#!/usr/bin/env python3
"""Test des Zusatz-Bildschirms SmallTV (MoveEye Teil 552) gegen den virtuellen SmallTV des 3D-Simulators (ab 3D-4.19).

Lädt die gebaute MoveEye-Datei (ohne sie zu starten) und schickt mit genau dem Code, der auch zum echten Gerät geht,
Bilder an den Simulator: einmal normal, einmal mit «Macken wie das echte Gerät» (Upload antwortet 400, Antworten 1,2 s
später). Prüft Zähler, Dateinamen, Bildgrösse, Helligkeit und das gezeigte Bild (GET /smalltv.jpg).

  python3 werkzeuge/smalltv_test.py --sim http://127.0.0.1:8941 [--bilder ORDNER]

Ab MoveEye 553 (Live-Bild und Wechsel) zusätzlich: Alarm-Animation als GIF (me_a.gif), der Simulator liest alle Bilder
(«gif_frames»), die Kachel spielt sie ab («anim_frames»); danach JPEG am gleichen Platz -> das GIF wird gelöscht; ein
unverändertes Bild wird nur wieder gezeigt (kein neues Hochladen). --bilder speichert GIF, Bildstreifen und die Seiten.
"""
import argparse
import glob
import io
import json
import os
import runpy
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ctl(sim, d):
    req = urllib.request.Request(sim + "/control", json.dumps(d).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="http://127.0.0.1:8765")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    mw = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")), key=os.path.getmtime)[-1]
    g = runpy.run_path(mw, run_name="smalltv_test")
    from PIL import Image
    fails = 0

    def ok(cond, text):
        nonlocal fails
        print(("✓ " if cond else "✗ ") + text)
        fails += 0 if cond else 1
    v = g["_stv_json"](a.sim, "/v.json", 5)
    ok(g["stv_is_geekmagic"](v) and v.get("sim"), f"/v.json: {v}")
    for quirks in (False, True):
        ctl(a.sim, {"action": "smalltv", "reset": True, "all": True, "quirks": quirks})
        dv = g["StvDev"].__new__(g["StvDev"])
        dv.id = "t"; dv.shown = ""; dv.theme_t = 0.0; dv.ups = dv.bytes = dv.errs = 0; dv.h = {"ok": None, "t": 0.0}; dv.jpg = None; dv.kind = ""
        t0 = time.time()
        s1 = dv.send(a.sim, {"jpg": g["stv_render_test"]("Prüfung"), "sig": 1, "kind": "test", "brt": 40})
        s2 = dv.send(a.sim, {"jpg": g["stv_render_status"]("de"), "sig": 2, "kind": "status", "brt": 40})
        code, _b = g["_stv_req"](a.sim, "/set?brt=35", timeout=10)
        st = ctl(a.sim, {"action": "smalltv"})
        tag = "mit Macken" if quirks else "normal"
        ok(s1 and s2, f"{tag}: zwei Bilder gesendet ({time.time() - t0:.1f} s, Hinweis: {dv.h.get('note') or '-'})")
        ok(st["uploads"] == 2 and sorted(st["files"]) == ["me_a.jpg", "me_b.jpg"], f"{tag}: Zähler {st['uploads']}, Dateien {st['files']}")
        ok(st["theme"] == 3 and st["img"] == "/image/me_b.jpg" and st["bad_size"] == 0 and (st["last_w"], st["last_h"]) == (240, 240), f"{tag}: Fotoalbum, gezeigt {st['img']}, {st['last_w']}×{st['last_h']}")
        ok(code == 200 and st["brt"] == 35, f"{tag}: Helligkeit {st['brt']} %")
        with urllib.request.urlopen(a.sim + "/smalltv.jpg", timeout=10) as r:
            im = Image.open(io.BytesIO(r.read()))
        ok(im.size == (240, 240), f"{tag}: /smalltv.jpg {im.size}")
        ok(st["used"] < 120000, f"{tag}: Speicher {st['used']} Bytes")
        dv.check(a.sim, force=True)
        ok(dv.h.get("ok") and dv.h.get("free") is not None, f"{tag}: Gesundheit {dv.h.get('fw')} · {dv.h.get('free')} Bytes frei")
    # 553: alarm animation (GIF), the JPEG at its place removes it, unchanged pictures only shown again
    ctl(a.sim, {"action": "smalltv", "reset": True, "all": True, "quirks": False, "show": True})
    dv = g["StvDev"].__new__(g["StvDev"])
    dv.id = "t"; dv.shown = ""; dv.theme_t = 0.0; dv.ups = dv.bytes = dv.errs = 0; dv.h = {"ok": None, "t": 0.0}; dv.jpg = None; dv.kind = ""
    import numpy as np
    yy, xx = np.mgrid[0:120, 0:160]
    crop = np.dstack([(xx * 1.4) % 255, 60 + yy, 200 - yy]).astype("uint8")
    gif = g["stv_render_alarm_gif"]({"kind": "animal", "label": "fox", "conf": 0.91, "dist": 6, "crop": crop, "n": 1, "clock": "14:02"}, "de")
    n = Image.open(io.BytesIO(gif)).n_frames
    t0 = time.time()
    s1 = dv.send(a.sim, {"jpg": gif, "sig": 11, "kind": "gif", "brt": 60, "ext": "gif"})
    dt = time.time() - t0
    time.sleep(1.0)
    st = ctl(a.sim, {"action": "smalltv"})
    ok(s1 and st["img"] == "/image/me_a.gif" and st["gif_frames"] == n and (st["last_w"], st["last_h"]) == (240, 240) and st["bad_size"] == 0,
       f"GIF: {len(gif)} Bytes, {n} Bilder, Simulator liest {st['gif_frames']} ({dt:.1f} s), gezeigt {st['img']}")
    ok(st["anim_frames"] == n or not st["tile"], f"GIF: Kachel spielt {st['anim_frames']} Bilder ab (Kachel sichtbar: {st['tile']})")
    with urllib.request.urlopen(a.sim + "/smalltv.jpg", timeout=10) as r:
        back = r.read()
    ok(back == gif, "GIF: /smalltv.jpg liefert dasselbe GIF zurück")
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
        open(os.path.join(a.bilder, "alarm.gif"), "wb").write(back)
        im = Image.open(io.BytesIO(back))
        strip = Image.new("RGB", (240 * n, 240))
        for k in range(n):
            im.seek(k); strip.paste(im.convert("RGB"), (240 * k, 0))
        strip.save(os.path.join(a.bilder, "alarm_gif_bilder.png"))
    g["STATE"]["battery"] = {"on": True, "pct": 72, "sim": True, "charging": False, "on_battery": True, "use_w": 4.6, "solar_w": 3.2, "hours": 9.4}
    batt = g["stv_render_batt"]("de")
    s2 = dv.send(a.sim, {"jpg": batt, "sig": 12, "kind": "batt", "brt": 60})
    s3 = dv.send(a.sim, {"jpg": g["stv_render_live"]("de", crop), "sig": 13, "kind": "live", "brt": 60})
    st = ctl(a.sim, {"action": "smalltv"})
    ok(s2 and s3 and sorted(st["files"]) == ["me_a.jpg", "me_b.jpg"] and st["img"] == "/image/me_a.jpg",
       f"JPEG am Platz des GIF: Dateien {st['files']} (das GIF ist weg), gezeigt {st['img']}")
    up = st["uploads"]
    s4 = dv.send(a.sim, {"jpg": batt, "sig": 12, "kind": "batt", "brt": 60})
    st = ctl(a.sim, {"action": "smalltv"})
    ok(s4 and st["uploads"] == up and st["img"] == "/image/me_b.jpg", f"unverändertes Bild nur wieder gezeigt: {st['uploads']} Uploads, gezeigt {st['img']}")
    ctl(a.sim, {"action": "smalltv", "quirks": False})
    print("OK" if not fails else f"{fails} Fehler")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
