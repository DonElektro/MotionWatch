#!/usr/bin/env python3
"""Echtbild-Prüfsatz (2.98.18): ein fester Satz Bilder mit der richtigen Antwort, gegen den MoveEyes KI gemessen wird -
ohne Simulator und ohne Godot. Siehe ki_training/pruefsatz/LIESMICH.md.

  # 1. auf dem Pi: die mit «Was war das?» beantworteten Alarmbilder als Prüfsatz (Ordner + ZIP) herausschreiben
  python3 pruefsatz.py exportieren --nach ~/MoveEye_Pruefsatz
  python3 pruefsatz.py exportieren --nach ki_training/pruefsatz --ohne-personen     # nur Tiere / leere Fehlalarme (öffentlich ok)

  # 2. ein paar Bilder aus dem 3D-Simulator (zum Ausprobieren, solange es keine echten gibt)
  python3 pruefsatz.py aus-simulator --sim http://127.0.0.1:8765 --n 16 --nach ki_training/pruefsatz

  # 3. messen: jede KI (SSD aus --ki, das eigene ONNX-Modell, falls dort) gegen alle Bilder - gefunden / verpasst / falsch
  python3 pruefsatz.py messen --satz ki_training/pruefsatz --ki ki --datei webcam_bewegung_X_Y_Z.py

Format (dasselbe wie für das Training, ki_training/README.md): ein Ordner (oder ZIP) mit Bildern und labels.json
{"format": "moveeye-labels-1", "items": [{"file": "x.jpg", "label": "person|animal|vehicle|nothing", "boxes": [[x, y, w, h]],
"sim": false}]} - Rahmen 0..1, x, y = linke obere Ecke.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
LABELS = {"person": "person", "animal": "animal", "vehicle": "vehicle", "nothing": "nothing",
          "Person": "person", "Tier": "animal", "Fahrzeug": "vehicle", "Nichts": "nothing"}


# ---- 1. export from MoveEye's «What was it?» pictures -------------------------------------------------------------------
def daten_ordner():
    env = os.environ.get("MOTIONWATCH_HOME", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "motionwatch")


def im_repository(path):
    path = os.path.abspath(os.path.expanduser(path))
    while not os.path.isdir(path) and os.path.dirname(path) != path:     # the folder may not exist yet
        path = os.path.dirname(path)
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        return r.returncode == 0
    except OSError:
        return False


def lesen_satz(path):
    """[(item, image bytes)] from a folder or a ZIP with labels.json"""
    out = []
    if os.path.isfile(path) and path.lower().endswith(".zip"):
        z = zipfile.ZipFile(path)
        names = z.namelist()
        lj = next((n for n in names if n.endswith("labels.json")), None)
        if not lj:
            return out
        base = lj[:-len("labels.json")]
        for it in _items(json.loads(z.read(lj).decode("utf-8"))):
            fn = base + it["file"]
            if fn in names:
                out.append((it, z.read(fn)))
        return out
    lj = os.path.join(path, "labels.json")
    if not os.path.isfile(lj):
        return out
    with open(lj, encoding="utf-8") as f:
        d = json.load(f)
    for it in _items(d):
        p = os.path.join(path, it["file"])
        if os.path.isfile(p):
            with open(p, "rb") as f:
                out.append((it, f.read()))
    return out


def _items(d):
    if isinstance(d, dict) and isinstance(d.get("items"), list):
        raw = d["items"]
    elif isinstance(d, dict):                                  # short form {"x.jpg": "Person"}
        raw = [{"file": k, "label": v} for k, v in d.items() if isinstance(v, str)]
    else:
        raw = d if isinstance(d, list) else []
    out = []
    for x in raw:
        if not isinstance(x, dict):
            continue
        fn = x.get("file") or x.get("image") or x.get("jpg")
        lab = LABELS.get(str(x.get("label") or x.get("answer") or x.get("kind") or ""))
        if not fn or not lab or "/" in fn or "\\" in fn or fn.startswith("."):
            continue
        out.append(dict(x, file=fn, label=lab, boxes=[b for b in (x.get("boxes") or []) if isinstance(b, list) and len(b) == 4]))
    return out


def schreiben_satz(nach, items, mit_zip=True):
    """items = [(item, jpg bytes)]: into the folder (labels.json merged with what is there) and as <folder>.zip"""
    os.makedirs(nach, exist_ok=True)
    alt = {it["file"]: it for it, _b in lesen_satz(nach)}
    for it, b in items:
        with open(os.path.join(nach, it["file"]), "wb") as f:
            f.write(b)
        alt[it["file"]] = it
    d = {"format": "moveeye-labels-1", "items": [alt[k] for k in sorted(alt)]}
    with open(os.path.join(nach, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    if mit_zip:
        zp = nach.rstrip("/") + ".zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(os.path.join(nach, "labels.json"), "labels.json")
            for k in sorted(alt):
                z.write(os.path.join(nach, k), k)
        print("ZIP: %s" % zp)
    return d


def cmd_exportieren(a):
    von = a.von or os.path.join(daten_ordner(), "alarm_labels")
    if not os.path.isdir(von):
        print("Kein Ordner %s – noch keine Alarmbilder mit «Was war das?»" % von)
        return 1
    items, n_pers, n_weg = [], 0, 0
    for jp in sorted(glob.glob(os.path.join(von, "*.json"))):
        try:
            with open(jp, encoding="utf-8") as f:
                x = json.load(f)
        except (OSError, ValueError):
            continue
        lab = LABELS.get(str(x.get("label") or ""))
        img = jp[:-5] + ".jpg"
        if not lab or not os.path.isfile(img):
            continue                                            # not answered yet
        if lab == "person" and not x.get("sim"):
            if a.ohne_personen:
                n_weg += 1
                continue
            n_pers += 1
        it = {"file": os.path.basename(img), "label": lab, "boxes": (x.get("boxes") or []) if lab == "person" else [],
              "sim": bool(x.get("sim")), "t": x.get("t"), "src": x.get("src", "")}
        with open(img, "rb") as f:
            items.append((it, f.read()))
    if n_pers and im_repository(a.nach) and not a.oeffentlich_ok:
        print("HALT: %d Bilder mit echten Personen und das Ziel liegt in einem Git-Repository.\n"
              "Fremde Personen gehören nicht in ein (öffentliches) Repository – lieber einen eigenen Ordner wählen und die ZIP\n"
              "privat ablegen (Secret PRUEFSATZ_URL, siehe ki_training/pruefsatz/LIESMICH.md), oder --ohne-personen.\n"
              "Wer sicher ist (privates Repository, nur eigene Leute im Bild): --oeffentlich-ok" % n_pers)
        return 2
    if not items:
        print("Keine beantworteten Bilder in %s" % von)
        return 1
    schreiben_satz(a.nach, items)
    by = {}
    for it, _b in items:
        by[it["label"]] = by.get(it["label"], 0) + 1
    print("%d Bilder nach %s: %s%s" % (len(items), a.nach, ", ".join("%s %d" % kv for kv in sorted(by.items())),
                                       (" (%d mit Personen weggelassen)" % n_weg) if n_weg else ""))
    return 0


# ---- 2. a few pictures from the 3D simulator --------------------------------------------------------------------------
def cmd_aus_simulator(a):
    import time
    import urllib.request

    def ctl(d):
        r = urllib.request.Request(a.sim.rstrip("/") + "/control", data=json.dumps(d).encode(), method="POST",
                                   headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode())
    st = ctl({"action": "dataset", "op": "start", "n": a.n})
    t_end = time.time() + 60 + 15 * a.n
    while st.get("busy") and time.time() < t_end:
        time.sleep(3)
        st = ctl({"action": "dataset", "op": "get"})
    lst = ctl({"action": "dataset", "op": "list"}).get("items", [])
    items = []
    stamp = time.strftime("%Y%m%d_%H%M%S")
    for x in lst:
        b = urllib.request.urlopen(a.sim.rstrip("/") + "/dataset/%d.jpg" % int(x["i"]), timeout=20).read()
        kind = str(x.get("kind") or "")
        lab = "person" if kind == "person" else "animal"
        it = {"file": "sim_%s_%02d.jpg" % (stamp, int(x["i"])), "label": lab, "boxes": [x["box"]] if lab == "person" and x.get("box") else [],
              "sim": True, "src": "3D-Simulator: %s, %s, %.0f m" % (kind, x.get("cond", ""), float(x.get("dist") or 0))}
        items.append((it, b))
    if not items:
        print("Der Simulator hat keine Bilder geliefert: %s" % st)
        return 1
    schreiben_satz(a.nach, items, mit_zip=False)
    print("%d Simulator-Bilder nach %s" % (len(items), a.nach))
    return 0


# ---- 3. measure MoveEye's AI ----------------------------------------------------------------------------------------------
def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw, ih = max(0.0, min(ax2, bx2) - max(a[0], b[0])), max(0.0, min(ay2, by2) - max(a[1], b[1]))
    u = a[2] * a[3] + b[2] * b[3] - iw * ih
    return iw * ih / u if u > 0 else 0.0


def treffer(bb, gg):
    """the AI box belongs to the true person: overlap (IoU) at least 0.3, or its middle lies in the true box"""
    cx, cy = bb[0] + bb[2] / 2, bb[1] + bb[3] / 2
    return iou(bb, gg) >= 0.3 or (gg[0] <= cx <= gg[0] + gg[2] and gg[1] <= cy <= gg[1] + gg[3])


def moveeye_laden(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_pruefsatz", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def cmd_messen(a):
    datei = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    satz = []
    for s in a.satz.split(","):
        if s.strip():
            satz += lesen_satz(s.strip())
    if not satz:
        print("Kein Bild im Prüfsatz %s" % a.satz)
        return 1
    home = tempfile.mkdtemp(prefix="mw_pruefsatz_")
    md = os.path.join(home, "models")
    os.makedirs(md)
    for fn in os.listdir(a.ki) if a.ki and os.path.isdir(a.ki) else []:
        os.symlink(os.path.abspath(os.path.join(a.ki, fn)), os.path.join(md, fn))
    ns = moveeye_laden(datei, home)
    cv2, np, CFG = ns["cv2"], ns["np"], ns["CFG"]
    modelle = []
    for kind in ("ssd", "own"):
        CFG["ai_model"] = kind
        det = ns["AIDetector"]()
        if det.net is None or (kind == "own" and det.kind != "yolo"):
            print("Modell %s: nicht vorhanden (%s)" % (kind, ns["STATE"].get("ai_model_note") or ns["STATE"].get("ai_status")))
            continue
        modelle.append((ns["STATE"].get("ai_model") or kind, det))
    if not modelle:
        print("Keine KI gefunden – --ki Ordner mit frozen_inference_graph.pb + ssd_mobilenet_v2_coco.pbtxt "
              "und/oder moveeye_model.onnx + moveeye_model.json")
        return 1
    pw = int(CFG["proc_width"])
    erg = {"datei": os.path.basename(datei), "bilder": len(satz), "modelle": []}
    for name, det in modelle:
        z = {"modell": name, "echt": {}, "sim": {}, "falsch_liste": [], "verpasst_liste": []}
        for it, b in satz:
            img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                continue
            h0, w0 = img.shape[:2]
            ph = int(h0 * pw / max(1, w0))
            small = cv2.resize(img, (pw, ph))                     # like the camera loop (410): the AI sees the small picture
            pers = det.infer(small, CFG["ai_conf"], CFG["object_conf"])[0]
            boxes = [(x / pw, y / ph, w / pw, h / ph) for x, y, w, h, _c in pers]
            g = z["sim" if it.get("sim") else "echt"]
            for k in ("personen", "gefunden", "verpasst", "ohne_person", "falsch"):
                g.setdefault(k, 0)
            if it["label"] == "person":
                g["personen"] += 1
                gt = it.get("boxes") or []
                hit = bool(boxes) and (not gt or any(treffer(bb, gg) for bb in boxes for gg in gt))
                g["gefunden" if hit else "verpasst"] += 1
                if not hit:
                    z["verpasst_liste"].append(it["file"])
            else:
                g["ohne_person"] += 1
                if boxes:
                    g["falsch"] += 1
                    z["falsch_liste"].append(it["file"])
        erg["modelle"].append(z)
    zeilen = ["## Echtbild-Prüfsatz – %s, %d Bilder" % (erg["datei"], len(satz)), "",
              "| Modell | Bilder | Personen gefunden | verpasst | Fehlalarme (Bilder ohne Person) |", "|---|---|---|---|---|"]
    for z in erg["modelle"]:
        for herkunft, lab in (("echt", "echt"), ("sim", "Simulator")):
            g = z[herkunft]
            if not g:
                continue
            zeilen.append("| %s | %s | %d von %d | %d | %d von %d |" % (z["modell"], lab, g["gefunden"], g["personen"], g["verpasst"],
                                                                         g["falsch"], g["ohne_person"]))
    for z in erg["modelle"]:
        if z["verpasst_liste"] or z["falsch_liste"]:
            zeilen.append("")
            zeilen.append("%s – verpasst: %s · falsch: %s" % (z["modell"], ", ".join(z["verpasst_liste"][:20]) or "–",
                                                              ", ".join(z["falsch_liste"][:20]) or "–"))
    text = "\n".join(zeilen)
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(erg, f, ensure_ascii=False, indent=1)
    shutil.rmtree(home, ignore_errors=True)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Echtbild-Prüfsatz für MoveEyes KI")
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("exportieren", help="die beantworteten Alarmbilder («Was war das?») als Prüfsatz")
    e.add_argument("--von", default="", help="Ordner alarm_labels (Standard: ~/.config/motionwatch/alarm_labels)")
    e.add_argument("--nach", default="MoveEye_Pruefsatz")
    e.add_argument("--ohne-personen", action="store_true", help="echte Bilder mit Personen weglassen (für ein öffentliches Repository)")
    e.add_argument("--oeffentlich-ok", action="store_true", help="Personen-Bilder auch in ein Git-Repository (nur privat!)")
    s = sp.add_parser("aus-simulator", help="Bilder aus dem 3D-Simulator (Person / Tier mit Rahmen)")
    s.add_argument("--sim", default="http://127.0.0.1:8765")
    s.add_argument("--n", type=int, default=16)
    s.add_argument("--nach", default=os.path.join(HIER, "pruefsatz"))
    m = sp.add_parser("messen", help="MoveEyes KI gegen den Prüfsatz")
    m.add_argument("--satz", default=os.path.join(HIER, "pruefsatz"), help="Ordner oder ZIP (mehrere mit Komma)")
    m.add_argument("--ki", default="", help="Ordner mit den Modell-Dateien (SSD und / oder eigenes ONNX-Modell)")
    m.add_argument("--datei", default="", help="gebaute MoveEye-Datei (Standard: die neuste im Repository)")
    m.add_argument("--json", default="", help="Ergebnis zusätzlich als JSON")
    a = ap.parse_args()
    return {"exportieren": cmd_exportieren, "aus-simulator": cmd_aus_simulator, "messen": cmd_messen}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
