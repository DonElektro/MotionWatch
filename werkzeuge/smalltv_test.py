#!/usr/bin/env python3
"""Test des Zusatz-Bildschirms SmallTV (MoveEye Teil 552) gegen den virtuellen SmallTV des 3D-Simulators (ab 3D-4.19).

Lädt die gebaute MoveEye-Datei (ohne sie zu starten) und schickt mit genau dem Code, der auch zum echten Gerät geht,
Bilder an den Simulator: einmal normal, einmal mit «Macken wie das echte Gerät» (Upload antwortet 400, Antworten 1,2 s
später). Prüft Zähler, Dateinamen, Bildgrösse, Helligkeit und das gezeigte Bild (GET /smalltv.jpg).

  python3 werkzeuge/smalltv_test.py --sim http://127.0.0.1:8941
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
    ctl(a.sim, {"action": "smalltv", "quirks": False})
    print("OK" if not fails else f"{fails} Fehler")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
