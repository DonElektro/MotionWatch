#!/usr/bin/env python3
"""MoveEye – eigenes KI-Modell trainieren (läuft auf GitHub: Actions → «KI-Modell», siehe README.md in diesem Ordner).

Ablauf: Trainingspakete aus dem Simulator (YOLO-ZIPs) + beschriftete echte Alarmbilder («Was war das?») zu einem
Datensatz mit den Klassen person / animal / vehicle zusammenstellen, ein kleines YOLO-Modell (yolov8n / yolo11n) darauf
weitertrainieren, auf zurückgehaltenen Bildern messen (mAP), als ONNX mit 320 px Eingang exportieren, mit OpenCV
(cv2.dnn, wie auf dem Pi) prüfen und moveeye_model.onnx + moveeye_model.json (Manifest mit sha256) schreiben.

    python3 ki_training/trainieren.py --pakete ki_training/pakete --echt ki_training/echt --aus ausgabe
    python3 ki_training/trainieren.py ... --nur-daten        # nur den Datensatz bauen (ohne Training, ohne ultralytics)
    python3 ki_training/trainieren.py ... --probe-auswertung # Datensatz + Auswertung mit erfundenen Funden (Test ohne ultralytics)

Auswertung «wo versagt die KI» (auswertung.md, Kurzfassung im Manifest unter "eval"/"summary"): die Simulator-Pakete haben
pro Bild eine Datei labels_meta/<train|val>/<bild>.json (Abstand, Haltung, Licht, Verdeckung, Unschärfe, Art pro Objekt).
Nach dem Training sucht das Modell auf den zurückgehaltenen Bildern; jeder echte Rahmen gilt als gefunden, wenn ein Fund
derselben Klasse ihn mit IoU >= 0.5 trifft. Daraus: Trefferquote nach Abstand, Haltung, Licht, Verdeckung, Art …, und
Fehlalarme auf leeren Bildern (nach Art der Falle: Ast, Fahne, Licht, Insekt, Schatten).
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
        self.root = root; self.meta = {}; self.stats = {"pack_images": 0, "real_images": 0, "real_skipped": 0, "blank_skipped": 0, "background": 0,
                                        "boxes": {c: 0 for c in CLASSES}, "val_images": 0, "packs": [], "real_sets": []}
        for p in ("images/train", "images/val", "labels/train", "labels/val"):
            os.makedirs(os.path.join(root, p), exist_ok=True)

    def add(self, img_path, lines, name, val, meta=None):
        """meta: {"image": {...}, "objects": [one dict per line (same order) or None]} - kept in meta.json for the evaluation"""
        part = "val" if val else "train"
        ext = os.path.splitext(img_path)[1].lower()
        base = SAFE.sub("_", name)[:140]
        if meta is not None:
            self.meta[base] = dict(meta, part=part)
        shutil.copyfile(img_path, os.path.join(self.root, "images", part, base + ext))
        with open(os.path.join(self.root, "labels", part, base + ".txt"), "w") as f:
            f.write("".join(f"{c} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n" for c, x, y, w, h in lines))
        for c, *_r in lines:
            self.stats["boxes"][CLASSES[c]] += 1
        if not lines:
            self.stats["background"] += 1
        if val:
            self.stats["val_images"] += 1

    def write_meta(self):
        with open(os.path.join(self.root, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False)

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
                pm = read_pack_meta(os.path.join(root, "labels_meta", part, os.path.splitext(fn)[0] + ".json"))
                by_line = {int(o.get("line", -1)): o for o in (pm or {}).get("objects", []) if isinstance(o, dict)}
                lines, objs = [], []
                if os.path.isfile(lab):
                    for i, ln in enumerate(open(lab)):
                        v = ln.split()
                        if len(v) != 5:
                            continue
                        c = target_class(names.get(int(float(v[0])), ""))
                        if c is not None:
                            lines.append((c, *[min(1.0, max(0.0, float(x))) for x in v[1:]]))
                            objs.append(by_line.get(i))
                img_meta = {k: v for k, v in (pm or {}).items() if k not in ("objects", "dropped")}
                img_meta["source"] = "sim"
                ds.add(os.path.join(idir, fn), lines, f"sim_{tag}_{fn}", part == "val", {"image": img_meta, "objects": objs})
                ds.stats["pack_images"] += 1
        ds.stats["packs"].append({"name": tag, "images": ds.stats["pack_images"] - n0})
        print(f"  pack {tag}: {ds.stats['pack_images'] - n0} pictures")


def read_pack_meta(path):
    """labels_meta/<part>/<bild>.json of a simulator pack (3D-4.x) - None if missing or broken"""
    try:
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
        return m if isinstance(m, dict) else None
    except (OSError, ValueError):
        return None


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
            ds.add(p, lines, f"real_{tag}_{fn}", is_val(tag + "/" + fn),
                   {"image": {"source": "echt", "label": lab, "empty": not lines}, "objects": [{"kind": "echt"} for _l in lines]})
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


# ---- Auswertung «wo versagt die KI» ------------------------------------------------------------------------------------
# preds: {base name of the picture: [(class, x1, y1, x2, y2, conf), ...]} with coordinates 0..1 (from predict_val or a test)
WEATHER_DE = {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}
BANDS = [  # (key, title, function(object meta, image meta, box) -> band name or None, band order)
    ("dist", "Abstand", lambda o, im, b: None if not isinstance(o.get("dist"), (int, float)) or o["dist"] < 0 else
        "unter 5 m" if o["dist"] < 5 else "5–10 m" if o["dist"] < 10 else "10–20 m" if o["dist"] < 20 else "20–35 m" if o["dist"] < 35 else "über 35 m",
        ["unter 5 m", "5–10 m", "10–20 m", "20–35 m", "über 35 m"]),
    ("size", "Grösse im Bild (Höhe)", lambda o, im, b: "unter 3 %" if b[3] < 0.03 else "3–8 %" if b[3] < 0.08 else "8–20 %" if b[3] < 0.2 else "über 20 %",
        ["unter 3 %", "3–8 %", "8–20 %", "über 20 %"]),
    ("posture", "Haltung (Personen)", lambda o, im, b: o.get("posture") or None, ["stehend", "geduckt", "kriechend"]),
    ("light", "Licht", lambda o, im, b: None if not isinstance(o.get("light", im.get("light")), (int, float)) else
        ("dunkel" + (" (Infrarot)" if im.get("ir") else "") if o.get("light", im.get("light")) < 0.12 else "Dämmerung" if o.get("light", im.get("light")) < 0.5 else "hell"),
        ["hell", "Dämmerung", "dunkel", "dunkel (Infrarot)"]),
    ("lum", "Helligkeit im Rahmen", lambda o, im, b: None if not isinstance(o.get("box_lum"), (int, float)) or o["box_lum"] < 0 else
        "sehr dunkel" if o["box_lum"] < 0.08 else "dunkel" if o["box_lum"] < 0.2 else "mittel" if o["box_lum"] < 0.5 else "hell",
        ["sehr dunkel", "dunkel", "mittel", "hell"]),
    ("occ", "Verdeckung", lambda o, im, b: None if not isinstance(o.get("occlusion"), (int, float)) or o["occlusion"] < 0 else
        "frei (unter 10 %)" if o["occlusion"] < 0.1 else "teils (10–40 %)" if o["occlusion"] < 0.4 else "stark (40–80 %)",
        ["frei (unter 10 %)", "teils (10–40 %)", "stark (40–80 %)"]),
    ("cut", "Am Bildrand angeschnitten", lambda o, im, b: None if not isinstance(o.get("cut"), (int, float)) else "nein" if o["cut"] < 0.1 else "ja",
        ["nein", "ja"]),
    ("blur", "Unschärfe", lambda o, im, b: "scharf" if not (o.get("blur_px") or o.get("soft")) else
        "Bewegung stark" if (o.get("blur_px") or 0) >= 6 else "Bewegung leicht" if (o.get("blur_px") or 0) > 0 else "unscharf (Fokus)",
        ["scharf", "unscharf (Fokus)", "Bewegung leicht", "Bewegung stark"]),
    ("weather", "Wetter", lambda o, im, b: WEATHER_DE.get(im.get("weather"), im.get("weather")), ["klar", "bewölkt", "Regen", "Nebel", "Schnee"]),
    ("carry", "Trägt etwas", lambda o, im, b: None if o.get("class") not in (None, "person") or "carry" not in o else ("ja" if o.get("carry") else "nein"), ["nein", "ja"]),
    ("kind", "Art", lambda o, im, b: o.get("kind") or None, None),
    ("scene", "Szene", lambda o, im, b: im.get("scene"), None),
    ("source", "Quelle", lambda o, im, b: {"sim": "Simulator", "echt": "echte Bilder"}.get(im.get("source"), im.get("source")), None),
]


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy; u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def read_gt(ds_root, part="val"):
    """{base: [(class, x1, y1, x2, y2), ...]} of the YOLO labels of one part"""
    out = {}
    ldir = os.path.join(ds_root, "labels", part)
    for fn in sorted(os.listdir(ldir)) if os.path.isdir(ldir) else []:
        if not fn.endswith(".txt"):
            continue
        rows = []
        for ln in open(os.path.join(ldir, fn)):
            v = ln.split()
            if len(v) == 5:
                c, x, y, w, h = int(v[0]), *map(float, v[1:])
                rows.append((c, x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        out[fn[:-4]] = rows
    return out


def evaluate(gt, meta, preds, conf=None, iou_min=0.5):
    """match the finds to the true boxes per picture (greedy by IoU, same class, find >= threshold of its class).
    Returns {"objects": [...], "images": [...], "totals": {...}}"""
    conf = conf or {}
    objs, imgs = [], []
    for base, rows in gt.items():
        m = meta.get(base) or {}; im = m.get("image") or {}; om = m.get("objects") or []
        thr = lambda c: float(conf.get(CLASSES[c], 0.35)) if 0 <= c < len(CLASSES) else 0.35
        ps = sorted([p for p in preds.get(base, []) if p[5] >= thr(int(p[0]))], key=lambda p: -p[5])
        used = set(); hit = [False] * len(rows)
        pairs = sorted(((iou(r[1:], p[1:5]), i, j) for i, r in enumerate(rows) for j, p in enumerate(ps) if int(p[0]) == r[0]), reverse=True)
        for v, i, j in pairs:
            if v < iou_min or hit[i] or j in used:
                continue
            hit[i] = True; used.add(j)
        for i, r in enumerate(rows):
            o = om[i] if i < len(om) and isinstance(om[i], dict) else {}
            b = (r[1], r[2], r[3] - r[1], r[4] - r[2])
            objs.append({"class": CLASSES[r[0]] if 0 <= r[0] < len(CLASSES) else str(r[0]), "hit": hit[i], "o": o, "im": im, "box": b, "image": base})
        fp = [CLASSES[int(p[0])] for j, p in enumerate(ps) if j not in used and 0 <= int(p[0]) < len(CLASSES)]
        imgs.append({"image": base, "empty": not rows, "fp": fp, "negatives": list(im.get("negatives") or []), "im": im})
    n = len(objs); h = sum(o["hit"] for o in objs)
    per = {}
    for c in CLASSES:
        oc = [o for o in objs if o["class"] == c]
        if oc:
            per[c] = {"n": len(oc), "hit": sum(o["hit"] for o in oc), "recall": round(sum(o["hit"] for o in oc) / len(oc), 4)}
    empty = [i for i in imgs if i["empty"]]
    fpe = [i for i in empty if i["fp"]]
    tot = {"objects": n, "hits": h, "recall": round(h / n, 4) if n else None, "per_class": per,
           "images": len(imgs), "empty_images": len(empty), "empty_with_false_alarm": len(fpe),
           "false_finds": sum(len(i["fp"]) for i in imgs)}
    return {"objects": objs, "images": imgs, "totals": tot}


def band_table(res, key, classes=("person", "animal")):
    """[(band, {class: (hits, n)}, (hits, n) all)] in the order of the band"""
    spec = next(b for b in BANDS if b[0] == key)
    rows = {}
    for o in res["objects"]:
        try:
            band = spec[2](o["o"], o["im"], o["box"])
        except (TypeError, KeyError, ValueError):
            band = None
        if band is None:
            continue
        r = rows.setdefault(band, {"all": [0, 0]})
        r["all"][0] += o["hit"]; r["all"][1] += 1
        if o["class"] in classes:
            r.setdefault(o["class"], [0, 0]); r[o["class"]][0] += o["hit"]; r[o["class"]][1] += 1
    order = spec[3] or sorted(rows, key=lambda k: -rows[k]["all"][1])
    return [(k, rows[k]) for k in order if k in rows] + [(k, rows[k]) for k in rows if spec[3] and k not in spec[3]]


def _pct(hn):
    h, n = hn
    return f"{100 * h / n:.0f} % ({h}/{n})" if n else "–"


def weak_spots(res, min_n=5, top=5):
    """the bands with the lowest recall (at least min_n objects, clearly below the average)"""
    avg = res["totals"]["recall"] or 0.0
    out = []
    for key, title, _f, _o in BANDS:
        if key in ("source", "scene"):
            continue
        for band, r in band_table(res, key):
            h, n = r["all"]
            if n >= min_n and h / n < avg - 0.05:
                out.append((h / n, title, band, h, n))
    out.sort()
    return out[:top]


def neg_table(res):
    """false alarms on empty pictures by kind of trap"""
    rows = {}
    for i in res["images"]:
        if not i["empty"]:
            continue
        kinds = sorted(set(i["negatives"])) or (["echtes Bild «nichts»"] if i["im"].get("source") == "echt" else ["ohne Falle"])
        for k in kinds:
            r = rows.setdefault(k, [0, 0]); r[0] += bool(i["fp"]); r[1] += 1
    return sorted(rows.items(), key=lambda kv: -kv[1][1])


EN = {"Abstand": "distance", "Grösse im Bild (Höhe)": "size in the picture", "Haltung (Personen)": "posture", "Licht": "light",
      "Helligkeit im Rahmen": "brightness in the box", "Verdeckung": "occlusion", "Am Bildrand angeschnitten": "cut at the edge",
      "Unschärfe": "blur", "Wetter": "weather", "Trägt etwas": "carrying something", "Art": "kind", "unter 5 m": "under 5 m",
      "über 35 m": "over 35 m", "unter 3 %": "under 3 %", "über 20 %": "over 20 %", "stehend": "standing", "geduckt": "crouching",
      "kriechend": "crawling", "hell": "bright", "Dämmerung": "dusk", "dunkel": "dark", "dunkel (Infrarot)": "dark (infrared)",
      "sehr dunkel": "very dark", "mittel": "medium", "frei (unter 10 %)": "free (under 10 %)", "teils (10–40 %)": "partly (10–40 %)",
      "stark (40–80 %)": "mostly (40–80 %)", "nein": "no", "ja": "yes", "scharf": "sharp", "unscharf (Fokus)": "out of focus",
      "Bewegung leicht": "slight motion", "Bewegung stark": "strong motion", "klar": "clear", "bewölkt": "cloudy", "Regen": "rain",
      "Nebel": "fog", "Schnee": "snow", "ast": "branch", "fahne": "flag", "licht": "light", "insekt": "insect", "schatten": "shadow",
      "ohne Falle": "no trap", "echtes Bild «nichts»": "real picture «nothing»"}


def summary_text(res, lang="de"):
    """2-3 short lines (German, or English with lang="en") - in the manifest; MoveEye shows them in the model box"""
    t = res["totals"]; en = lang == "en"; T = (lambda x: EN.get(x, x)) if en else (lambda x: x)
    if not t["objects"]:
        return "No held-out pictures with persons or animals - no evaluation." if en else "Keine zurückgehaltenen Bilder mit Personen oder Tieren – keine Auswertung."
    s = (f"Found: {100 * t['recall']:.0f} % of {t['objects']} persons/animals" if en else f"Gefunden: {100 * t['recall']:.0f} % von {t['objects']} Personen/Tieren")
    if "person" in t["per_class"]:
        s += f" ({'persons' if en else 'Personen'} {100 * t['per_class']['person']['recall']:.0f} %)"
    s += "."
    ws = weak_spots(res, top=3)
    if ws:
        s += (" Weak: " if en else " Schwach bei: ") + ", ".join(f"{T(title).split(' (')[0].lower()} {T(band)} {100 * r:.0f} %" for r, title, band, _h, _n in ws) + "."
    if t["empty_images"]:
        s += (f" False alarms on {t['empty_with_false_alarm']} of {t['empty_images']} empty pictures" if en else
              f" Fehlalarme auf {t['empty_with_false_alarm']} von {t['empty_images']} leeren Bildern")
        nt = [(k, v) for k, v in neg_table(res) if v[0]]
        if nt:
            s += (" (mostly: " if en else " (meist: ") + T(max(nt, key=lambda kv: kv[1][0])[0]) + ")"
        s += "."
    return s


def eval_report(res, title="Auswertung: Wo versagt die KI?"):
    """the markdown report (auswertung.md, in the release)"""
    t = res["totals"]
    L = [f"## {title}", "", summary_text(res), "",
         f"- Zurückgehaltene Bilder: {t['images']} ({t['empty_images']} leer), Objekte: {t['objects']}, gefunden: {t['hits']}"
         + (f" (**Trefferquote {100 * t['recall']:.1f} %**)" if t["recall"] is not None else ""),
         "- " + ", ".join(f"{c}: {_pct((v['hit'], v['n']))}" for c, v in t["per_class"].items()),
         f"- Falsche Funde insgesamt: {t['false_finds']} · leere Bilder mit Fehlalarm: {t['empty_with_false_alarm']} von {t['empty_images']}",
         "- Ein Rahmen gilt als gefunden, wenn ein Fund derselben Klasse ihn mit IoU ≥ 0.5 trifft (Schwelle je Klasse wie in MoveEye).",
         "- Zahlen mit weniger als 5 Objekten sind Zufall – mit (wenig) markiert.", ""]
    ws = weak_spots(res)
    if ws:
        L += ["### Die grössten Schwächen", ""] + [f"{k + 1}. **{title_} {band}**: {100 * r:.0f} % gefunden ({h} von {n})"
                                                   for k, (r, title_, band, h, n) in enumerate(ws)] + [""]
    for key, title_, _f, _o in BANDS:
        tb = band_table(res, key)
        if not tb or (len(tb) == 1 and key in ("source", "scene", "carry", "cut")):
            continue
        L += [f"### Trefferquote nach {title_}", "", "| | alle | Personen | Tiere |", "|---|---|---|---|"]
        for band, r in tb[:25]:
            few = " (wenig)" if r["all"][1] < 5 else ""
            L.append(f"| {band}{few} | {_pct(r['all'])} | {_pct(r.get('person', (0, 0)))} | {_pct(r.get('animal', (0, 0)))} |")
        L.append("")
    nt = neg_table(res)
    if nt:
        L += ["### Fehlalarme auf leeren Bildern (nach Falle)", "", "| Falle | Bilder mit Fehlalarm |", "|---|---|"]
        L += [f"| {k} | {_pct(v)} |" for k, v in nt] + [""]
    return "\n".join(L) + "\n"


def eval_manifest(res):
    """the short form for moveeye_model.json (MoveEye compares it with the running model before an automatic update)"""
    t = res["totals"]
    bands = {}
    for key in ("dist", "posture", "light", "occ"):
        bands[key] = {band: round(r["all"][0] / r["all"][1], 3) for band, r in band_table(res, key) if r["all"][1]}
    return {"recall": t["recall"], "recall_person": (t["per_class"].get("person") or {}).get("recall"), "objects": t["objects"],
            "empty_images": t["empty_images"], "empty_false_alarm": round(t["empty_with_false_alarm"] / t["empty_images"], 4) if t["empty_images"] else None,
            "weak": [f"{title} {band}: {100 * r:.0f} %" for r, title, band, _h, _n in weak_spots(res)], "bands": bands, "summary": summary_text(res),
            "summary_en": summary_text(res, "en")}


def predict_val(model, ds_root, imgsz, batch=16):
    """the trained model on all val pictures: {base: [(class, x1, y1, x2, y2, conf)]} (0..1), low threshold - evaluate() cuts"""
    vdir = os.path.join(ds_root, "images", "val"); out = {}
    files = sorted(f for f in os.listdir(vdir) if f.lower().endswith(IMG_EXT))
    for k in range(0, len(files), batch):
        chunk = files[k:k + batch]
        for f, r in zip(chunk, model.predict([os.path.join(vdir, f) for f in chunk], imgsz=imgsz, conf=0.05, device="cpu", verbose=False)):
            out[os.path.splitext(f)[0]] = [(int(c), *map(float, b), float(cf)) for b, c, cf in zip(r.boxes.xyxyn.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
    return out


def fake_predictions(gt, meta, seed=7):
    """for --probe-auswertung: finds that miss more far away, crawling, in the dark and behind things (tests the report)"""
    import random
    rnd = random.Random(seed); out = {}
    for base, rows in gt.items():
        m = meta.get(base) or {}; om = m.get("objects") or []; im = m.get("image") or {}
        ps = []
        for i, r in enumerate(rows):
            o = om[i] if i < len(om) and isinstance(om[i], dict) else {}
            p = 0.95 - 0.012 * float(o.get("dist") or 8) - (0.25 if o.get("posture") == "kriechend" else 0.1 if o.get("posture") == "geduckt" else 0)
            p -= 0.5 * max(0.0, float(o.get("occlusion") or 0)) + (0.2 if float(o.get("light", im.get("light", 1)) or 0) < 0.12 else 0)
            if rnd.random() < p:
                j = 0.01
                ps.append((r[0], r[1] + j, r[2] + j, r[3] + j, r[4] + j, rnd.uniform(0.4, 0.95)))
        if not rows and im.get("negatives") and rnd.random() < 0.4:
            ps.append((0, 0.4, 0.3, 0.5, 0.7, 0.6))
        out[base] = ps
    return out


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
    ap.add_argument("--probe-auswertung", action="store_true", help="dataset + evaluation report with made-up finds (tests the report without ultralytics)")
    a = ap.parse_args()
    os.makedirs(a.aus, exist_ok=True); os.makedirs(a.arbeit, exist_ok=True)
    ds_root = os.path.join(a.arbeit, "datensatz")
    shutil.rmtree(ds_root, ignore_errors=True)
    ds = Dataset(ds_root)
    print("Trainingspakete:"); add_packs(ds, unpack_all(a.pakete, a.arbeit, "pakete"))
    print("Echte Bilder:"); add_real(ds, unpack_all(a.echt, a.arbeit, "echt"), (a.pseudo or None) if not (a.nur_daten or a.probe_auswertung) else None)
    data_yaml = ds.write_yaml(); ds.write_meta()
    st = ds.stats; n_all = st["pack_images"] + st["real_images"]
    print(json.dumps(st, indent=1))
    if n_all < 20:
        sys.exit(f"zu wenige Trainingsbilder ({n_all}) - mindestens 20 nötig (siehe ki_training/README.md)")
    if st["val_images"] == 0:
        sys.exit("keine zurückgehaltenen Bilder (val) - ein Simulator-Paket hat immer welche")
    if a.nur_daten:
        print("nur Daten: fertig ->", data_yaml); return
    if a.probe_auswertung:
        gt = read_gt(ds_root); res = evaluate(gt, ds.meta, fake_predictions(gt, ds.meta), {"person": 0.3, "animal": 0.3, "vehicle": 0.3})
        rep = eval_report(res, "Probe-Auswertung (erfundene Funde – nur zum Testen des Berichts)")
        with open(os.path.join(a.aus, "auswertung.md"), "w", encoding="utf-8") as f:
            f.write(rep)
        with open(os.path.join(a.aus, "auswertung.json"), "w", encoding="utf-8") as f:
            json.dump(eval_manifest(res), f, indent=1, ensure_ascii=False)
        print(rep); return

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
    conf = best_conf(m)
    try:                                                      # «wo versagt die KI»: the model on the held-out pictures
        res = evaluate(read_gt(ds_root), ds.meta, predict_val(best, ds_root, a.imgsz), conf)
        ev = eval_manifest(res); ev_md = eval_report(res)
    except Exception as e:                                    # the model itself is fine - the report must not stop it
        print("  ! Auswertung ging nicht:", e); ev = {"summary": f"Auswertung ging nicht: {e}"[:200]}; ev_md = "## Auswertung\n\n" + ev["summary"] + "\n"
    with open(os.path.join(a.aus, "auswertung.md"), "w", encoding="utf-8") as f:
        f.write(ev_md)
    version = a.version or datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")
    man = {"format": "moveeye-model-1", "version": str(version), "classes": CLASSES, "input": a.imgsz, "file": "moveeye_model.onnx",
           "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw), "conf": conf, "metrics": metrics,
           "eval": ev, "summary": ev.get("summary", ""), "summary_en": ev.get("summary_en", ""),
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
           f"- OpenCV-Prüfung ({check['opencv']}): Ausgabe {check['output']}, {check['with_detection']} von {check['pictures']} Bildern mit Fund\n"
           f"- **Wo versagt die KI?** {ev.get('summary', '')} (ganze Auswertung: auswertung.md)\n\n"
           "| Klasse | mAP50 | mAP50-95 |\n|---|---|---|\n" + pc +
           "\nIn MoveEye: Einstellungen → KI-Erkennung → «Eigenes Modell herunterladen», dann «KI-Modell: Eigenes».\n")
    with open(os.path.join(a.aus, "bericht.md"), "w", encoding="utf-8") as f:
        f.write(rep)
    print(rep)


if __name__ == "__main__":
    main()
