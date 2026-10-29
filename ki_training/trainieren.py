#!/usr/bin/env python3
"""MoveEye – eigenes KI-Modell trainieren (läuft auf GitHub: Actions → «KI-Modell», siehe README.md in diesem Ordner).

Ablauf: Trainingspakete aus dem Simulator (YOLO-ZIPs) + beschriftete echte Alarmbilder («Was war das?») zu einem
Datensatz mit den Klassen person / animal / vehicle zusammenstellen, ein kleines YOLO-Modell (yolov8n / yolo11n) darauf
weitertrainieren, auf zurückgehaltenen Bildern messen (mAP), als ONNX mit 320 px Eingang exportieren, mit OpenCV
(cv2.dnn, wie auf dem Pi) prüfen und moveeye_model.onnx + moveeye_model.json (Manifest mit sha256) schreiben.

    python3 ki_training/trainieren.py --pakete ki_training/pakete --echt ki_training/echt --aus ausgabe
    python3 ki_training/trainieren.py ... --nur-daten        # nur den Datensatz bauen (ohne Training, ohne ultralytics)
"""
import argparse, datetime, hashlib, json, os, re, shutil, sys, zipfile

CLASSES = ["person", "animal", "vehicle"]
ANIMAL_NAMES = {"animal", "dog", "cat", "horse", "sheep", "cow", "fox", "deer", "boar", "badger", "hare", "hedgehog", "wolf", "marten",
                "squirrel", "lynx", "chamois", "ibex", "bird", "bear", "elephant", "zebra", "giraffe", "roe deer", "wild boar", "rabbit"}
VEHICLE_NAMES = {"vehicle", "car", "truck", "bus", "motorcycle", "bicycle", "van", "tractor"}
# labels of «Was war das?» (German or English, any case) -> what was in the picture
REAL_LABELS = {"person": "person", "mensch": "person", "tier": "animal", "animal": "animal", "fahrzeug": "vehicle", "vehicle": "vehicle",
               "auto": "vehicle", "car": "vehicle", "nichts": "nothing", "nothing": "nothing", "none": "nothing", "fehlalarm": "nothing"}
# COCO-80 ids of the pre-trained model (for real pictures without boxes)
COCO_PERSON, COCO_ANIMALS, COCO_VEHICLES = {0}, set(range(14, 24)), {1, 2, 3, 5, 7}
IMG_EXT = (".jpg", ".jpeg", ".png")
SAFE = re.compile(r"[^A-Za-z0-9_.\-]")


def target_class(name):
    n = str(name).strip().lower()
    if n == "person":
        return 0
    if n in ANIMAL_NAMES:
        return 1
    if n in VEHICLE_NAMES:
        return 2
    return None


def is_val(key, every=5):
    """fixed split by name: the same picture is always in the same part (held-out pictures stay held out)"""
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % every == 0


def safe_extract(zpath, dst, limit=2 * 1024 ** 3):
    """only plain files, no absolute paths or «..», limited size (zip bombs)"""
    total = 0
    with zipfile.ZipFile(zpath) as z:
        for zi in z.infolist():
            if zi.is_dir():
                continue
            parts = [p for p in zi.filename.replace("\\", "/").split("/") if p not in ("", ".")]
            if not parts or any(p == ".." for p in parts) or zi.filename.startswith("/"):
                continue
            total += zi.file_size
            if total > limit:
                raise ValueError(f"{zpath}: too big")
            out = os.path.join(dst, *[SAFE.sub("_", p) for p in parts])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with z.open(zi) as s, open(out, "wb") as d:
                shutil.copyfileobj(s, d)


def unpack_all(srcs, work, kind):
    """ZIPs and folders below the given paths -> list of folders to read"""
    out = []
    for src in srcs:
        if not src or not os.path.exists(src):
            continue
        entries = [src] if src.lower().endswith(".zip") else [os.path.join(src, e) for e in sorted(os.listdir(src))]
        for e in entries:
            if e.lower().endswith(".zip"):
                d = os.path.join(work, kind, SAFE.sub("_", os.path.basename(e))[:-4])
                if not os.path.isdir(d):
                    safe_extract(e, d)
                out.append(d)
            elif os.path.isdir(e):
                out.append(e)
    return out


def find_root(d, marker):
    """the folder that holds data.yaml / labels.json (a ZIP may have one folder level in between)"""
    for root, _dirs, files in os.walk(d):
        if marker in files:
            return root
    return None


def read_names(yaml_path):
    """class names of a pack's data.yaml (simple form «names:» + «  0: person» or a list) - no PyYAML needed"""
    names, on = {}, False
    with open(yaml_path, encoding="utf-8") as f:
        for ln in f:
            if re.match(r"^names\s*:", ln):
                m = re.match(r"^names\s*:\s*\[(.*)\]", ln)
                if m:
                    return {i: n.strip().strip("'\"") for i, n in enumerate(m.group(1).split(","))}
                on = True; continue
            if on:
                m = re.match(r"^\s+(\d+)\s*:\s*(.+?)\s*$", ln)
                if m:
                    names[int(m.group(1))] = m.group(2).strip("'\""); continue
                m = re.match(r"^\s+-\s*(.+?)\s*$", ln)
                if m:
                    names[len(names)] = m.group(1).strip("'\""); continue
                if ln.strip() and not ln.startswith((" ", "\t")):
                    on = False
    return names


class Dataset:
    def __init__(self, root):
        self.root = root; self.stats = {"pack_images": 0, "real_images": 0, "real_skipped": 0, "blank_skipped": 0, "background": 0,
                                        "boxes": {c: 0 for c in CLASSES}, "val_images": 0, "packs": [], "real_sets": []}
        for p in ("images/train", "images/val", "labels/train", "labels/val"):
            os.makedirs(os.path.join(root, p), exist_ok=True)

    def add(self, img_path, lines, name, val):
        part = "val" if val else "train"
        ext = os.path.splitext(img_path)[1].lower()
        base = SAFE.sub("_", name)[:140]
        shutil.copyfile(img_path, os.path.join(self.root, "images", part, base + ext))
        with open(os.path.join(self.root, "labels", part, base + ".txt"), "w") as f:
            f.write("".join(f"{c} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n" for c, x, y, w, h in lines))
        for c, *_r in lines:
            self.stats["boxes"][CLASSES[c]] += 1
        if not lines:
            self.stats["background"] += 1
        if val:
            self.stats["val_images"] += 1

    def write_yaml(self):
        p = os.path.join(self.root, "data.yaml")
        with open(p, "w") as f:
            f.write(f"path: {os.path.abspath(self.root)}\ntrain: images/train\nval: images/val\nnames:\n")
            f.write("".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
        return p


def blank(path):
    """a picture that is (nearly) one colour - e.g. completely white from an over-exposed simulator camera: no use"""
    try:
        import cv2
    except ImportError:
        return False
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return img is None or float(img.std()) < 6.0


def add_packs(ds, folders):
    """simulator packs (YOLO format: data.yaml, images/{train,val}, labels/{train,val}); the pack's own val part stays val"""
    for d in folders:
        root = find_root(d, "data.yaml")
        if not root:
            print(f"  ! {d}: no data.yaml - skipped"); continue
        names = read_names(os.path.join(root, "data.yaml"))
        tag = SAFE.sub("_", os.path.basename(d.rstrip("/")))[:40]; n0 = ds.stats["pack_images"]
        for part in ("train", "val"):
            idir = os.path.join(root, "images", part)
            if not os.path.isdir(idir):
                continue
            for fn in sorted(os.listdir(idir)):
                if not fn.lower().endswith(IMG_EXT):
                    continue
                if blank(os.path.join(idir, fn)):
                    ds.stats["blank_skipped"] += 1; continue
                lab = os.path.join(root, "labels", part, os.path.splitext(fn)[0] + ".txt")
                lines = []
                if os.path.isfile(lab):
                    for ln in open(lab):
                        v = ln.split()
                        if len(v) != 5:
                            continue
                        c = target_class(names.get(int(float(v[0])), ""))
                        if c is not None:
                            lines.append((c, *[min(1.0, max(0.0, float(x))) for x in v[1:]]))
                ds.add(os.path.join(idir, fn), lines, f"sim_{tag}_{fn}", part == "val")
                ds.stats["pack_images"] += 1
        ds.stats["packs"].append({"name": tag, "images": ds.stats["pack_images"] - n0})
        print(f"  pack {tag}: {ds.stats['pack_images'] - n0} pictures")


def read_real_items(root):
    """labels.json of «Was war das?» (see README.md) - tolerant about the key names"""
    with open(os.path.join(root, "labels.json"), encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") if isinstance(data, dict) else data
    if isinstance(data, dict) and items is None:                # also {"bild.jpg": "Person", ...}
        items = [{"file": k, "label": v} for k, v in data.items() if isinstance(v, str)]
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        fn = it.get("file") or it.get("image") or it.get("jpg") or it.get("name")
        lab = REAL_LABELS.get(str(it.get("label") or it.get("answer") or it.get("kind") or "").strip().lower())
        if not fn or not lab:
            continue
        fn = os.path.basename(str(fn))
        boxes = it.get("boxes") if isinstance(it.get("boxes"), list) else ([it["box"]] if isinstance(it.get("box"), list) else None)
        out.append((fn, lab, boxes))
    return out


def add_real(ds, folders, pseudo_model=None, conf=0.25):
    """real alarm pictures. With boxes (x, y, w, h 0..1): used as they are. Without boxes: a pre-trained COCO model finds the
    person / animal (only the kind that was confirmed by the human answer); «nothing» = picture without person / animal
    (a former false alarm - the model learns not to see one there); vehicles are marked where the COCO model is sure."""
    det = None
    for d in folders:
        root = find_root(d, "labels.json")
        if not root:
            print(f"  ! {d}: no labels.json - skipped"); continue
        items = read_real_items(root); tag = SAFE.sub("_", os.path.basename(d.rstrip("/")))[:40]; n0 = ds.stats["real_images"]
        for fn, lab, boxes in items:
            p = os.path.join(root, fn)
            if not os.path.isfile(p):
                p = os.path.join(root, "images", fn)
            if not os.path.isfile(p) or not fn.lower().endswith(IMG_EXT):
                ds.stats["real_skipped"] += 1; continue
            lines = []
            if boxes:
                c = CLASSES.index(lab) if lab in CLASSES else None
                for b in boxes:
                    if c is not None and isinstance(b, (list, tuple)) and len(b) >= 4:
                        x, y, w, h = [min(1.0, max(0.0, float(v))) for v in b[:4]]
                        if w > 0 and h > 0:
                            lines.append((c, x + w / 2, y + h / 2, w, h))
            else:
                if pseudo_model is None:
                    if lab != "nothing":
                        ds.stats["real_skipped"] += 1; continue
                else:
                    if det is None:
                        from ultralytics import YOLO
                        det = YOLO(pseudo_model)
                    r = det.predict(p, conf=0.15, verbose=False)[0]
                    W, H = r.orig_shape[1], r.orig_shape[0]
                    for b, k, cf in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
                        k = int(k); x1, y1, x2, y2 = b
                        kind = 0 if k in COCO_PERSON else 1 if k in COCO_ANIMALS else 2 if k in COCO_VEHICLES else None
                        if kind is None or CLASSES[kind] != lab and not (kind == 2 and cf >= 0.5):
                            continue
                        if kind != 2 and cf < (conf if kind == 0 else 0.2):
                            continue
                        lines.append((kind, (x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H))
                    if lab in ("person", "animal") and not any(CLASSES[c] == lab for c, *_r in lines):
                        ds.stats["real_skipped"] += 1; continue          # the COCO model did not find it: no box, not used
            ds.add(p, lines, f"real_{tag}_{fn}", is_val(tag + "/" + fn))
            ds.stats["real_images"] += 1
        ds.stats["real_sets"].append({"name": tag, "images": ds.stats["real_images"] - n0})
        print(f"  real {tag}: {ds.stats['real_images'] - n0} pictures")


def best_conf(metrics):
    """confidence with the best F1 per class (from the validation curves) - MoveEye uses it as «0.5» of its sliders"""
    out = {}
    try:
        b = metrics.box
        f1, px = getattr(b, "f1_curve", None), getattr(b, "px", None)
        if f1 is not None and px is not None and len(f1):
            idx = getattr(b, "ap_class_index", list(range(len(f1))))
            for row, ci in zip(f1, idx):
                out[CLASSES[int(ci)]] = round(float(px[int(row.argmax())]), 3)
    except Exception as e:                                    # older / newer ultralytics: defaults in MoveEye (0.35)
        print("  (no F1 curve:", e, ")")
    return {k: min(0.8, max(0.1, v)) for k, v in out.items()}


def letterbox(img, n, cv2, np):
    h, w = img.shape[:2]; r = min(n / w, n / h); nw, nh = int(round(w * r)), int(round(h * r))
    sq = np.full((n, n, 3), 114, np.uint8); dx, dy = (n - nw) // 2, (n - nh) // 2
    sq[dy:dy + nh, dx:dx + nw] = cv2.resize(img, (nw, nh)); return sq, r, dx, dy


def opencv_check(onnx_path, n, val_dir, nc):
    """the exported file with OpenCV like on the Pi: loads, output 1 x (4 + nc) x A, finds something on the val pictures"""
    import cv2, numpy as np
    net = cv2.dnn.readNetFromONNX(onnx_path)
    imgs = sorted(f for f in os.listdir(val_dir) if f.lower().endswith(IMG_EXT))[:20]
    shape, found = None, 0
    for f in imgs:
        img = cv2.imread(os.path.join(val_dir, f))
        sq, *_ = letterbox(img, n, cv2, np)
        net.setInput(cv2.dnn.blobFromImage(sq, 1 / 255.0, (n, n), swapRB=True))
        o = net.forward(); shape = list(o.shape)
        a = o[0].T if o.shape[1] == 4 + nc else o[0]
        found += int((a[:, 4:].max(1) > 0.3).sum() > 0)
    assert shape and 4 + nc in shape[1:], f"unexpected output {shape}"
    return {"opencv": cv2.__version__, "output": shape, "pictures": len(imgs), "with_detection": found}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pakete", nargs="*", default=["ki_training/pakete"], help="folders or ZIPs with simulator packs")
    ap.add_argument("--echt", nargs="*", default=["ki_training/echt"], help="folders or ZIPs with labelled real pictures")
    ap.add_argument("--aus", default="ausgabe", help="output folder")
    ap.add_argument("--arbeit", default="arbeit", help="work folder (dataset, runs)")
    ap.add_argument("--basis", default="yolov8n.pt", help="starting model (yolov8n.pt or yolo11n.pt)")
    ap.add_argument("--pseudo", default="yolov8s.pt", help="COCO model for boxes on real pictures without boxes ('' = off)")
    ap.add_argument("--epochen", type=int, default=60)
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--version", default="")
    ap.add_argument("--nur-daten", action="store_true", help="only build the dataset (no training)")
    a = ap.parse_args()
    os.makedirs(a.aus, exist_ok=True); os.makedirs(a.arbeit, exist_ok=True)
    ds_root = os.path.join(a.arbeit, "datensatz")
    shutil.rmtree(ds_root, ignore_errors=True)
    ds = Dataset(ds_root)
    print("Trainingspakete:"); add_packs(ds, unpack_all(a.pakete, a.arbeit, "pakete"))
    print("Echte Bilder:"); add_real(ds, unpack_all(a.echt, a.arbeit, "echt"), (a.pseudo or None) if not a.nur_daten else None)
    data_yaml = ds.write_yaml()
    st = ds.stats; n_all = st["pack_images"] + st["real_images"]
    print(json.dumps(st, indent=1))
    if n_all < 20:
        sys.exit(f"zu wenige Trainingsbilder ({n_all}) - mindestens 20 nötig (siehe ki_training/README.md)")
    if st["val_images"] == 0:
        sys.exit("keine zurückgehaltenen Bilder (val) - ein Simulator-Paket hat immer welche")
    if a.nur_daten:
        print("nur Daten: fertig ->", data_yaml); return

    from ultralytics import YOLO, __version__ as ul_version
    model = YOLO(a.basis)
    model.train(data=data_yaml, epochs=a.epochen, imgsz=a.imgsz, batch=a.batch, device="cpu", workers=2, patience=20,
                project=os.path.abspath(os.path.join(a.arbeit, "runs")), name="moveeye", exist_ok=True, plots=False, verbose=False)
    best_pt = os.path.join(a.arbeit, "runs", "moveeye", "weights", "best.pt")
    best = YOLO(best_pt)
    m = best.val(data=data_yaml, split="val", imgsz=a.imgsz, batch=a.batch, device="cpu", plots=False, verbose=False)
    per = {}
    try:
        for i, ci in enumerate(m.box.ap_class_index):
            per[CLASSES[int(ci)]] = {"map50": round(float(m.box.ap50[i]), 4), "map50_95": round(float(m.box.ap[i]), 4)}
    except Exception:
        pass
    metrics = {"map50": round(float(m.box.map50), 4), "map50_95": round(float(m.box.map), 4), "precision": round(float(m.box.mp), 4),
               "recall": round(float(m.box.mr), 4), "per_class": per, "val_images": st["val_images"]}
    onnx_tmp = best.export(format="onnx", imgsz=a.imgsz, opset=12, simplify=True, dynamic=False)
    onnx = os.path.join(a.aus, "moveeye_model.onnx"); shutil.copyfile(onnx_tmp, onnx)
    check = opencv_check(onnx, a.imgsz, os.path.join(ds_root, "images", "val"), len(CLASSES))
    with open(onnx, "rb") as f:
        raw = f.read()
    version = a.version or datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")
    man = {"format": "moveeye-model-1", "version": str(version), "classes": CLASSES, "input": a.imgsz, "file": "moveeye_model.onnx",
           "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw), "conf": best_conf(m), "metrics": metrics,
           "made": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "base": a.basis, "epochs": a.epochen,
           "ultralytics": ul_version, "images": {k: st[k] for k in ("pack_images", "real_images", "real_skipped", "blank_skipped", "background", "val_images", "boxes")},
           "check": check}
    with open(os.path.join(a.aus, "moveeye_model.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1, ensure_ascii=False)
    pc = "".join(f"| {k} | {v['map50']:.3f} | {v['map50_95']:.3f} |\n" for k, v in per.items())
    rep = (f"## MoveEye-KI-Modell {version}\n\n"
           f"- Bilder: {st['pack_images']} aus dem Simulator, {st['real_images']} echte ({st['real_skipped']} ohne Rahmen übersprungen), "
           f"{st['background']} ohne Person/Tier, {st['blank_skipped']} einfarbige ausgelassen, {st['val_images']} zurückgehalten zum Messen\n"
           f"- Rahmen: " + ", ".join(f"{k} {v}" for k, v in st["boxes"].items()) + "\n"
           f"- **mAP50 {metrics['map50']:.3f}** · mAP50-95 {metrics['map50_95']:.3f} · Präzision {metrics['precision']:.3f} · Trefferquote {metrics['recall']:.3f}\n"
           f"- Grundmodell {a.basis}, {a.epochen} Epochen, Eingang {a.imgsz} px, ONNX {len(raw) // 1024} kB, sha256 `{man['sha256']}`\n"
           f"- OpenCV-Prüfung ({check['opencv']}): Ausgabe {check['output']}, {check['with_detection']} von {check['pictures']} Bildern mit Fund\n\n"
           "| Klasse | mAP50 | mAP50-95 |\n|---|---|---|\n" + pc +
           "\nIn MoveEye: Einstellungen → KI-Erkennung → «Eigenes Modell herunterladen», dann «KI-Modell: Eigenes».\n")
    with open(os.path.join(a.aus, "bericht.md"), "w", encoding="utf-8") as f:
        f.write(rep)
    print(rep)


if __name__ == "__main__":
    main()
