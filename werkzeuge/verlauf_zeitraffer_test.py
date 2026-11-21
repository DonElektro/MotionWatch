#!/usr/bin/env python3
"""Test «Verlauf: Zeitraffer-Videos getrennt» (4.17.1, Wunsch des Besitzers): im Filter «Zeitraffer» standen die Videos
(tlv_*.mp4) zwischen ~1640 einzelnen Fotos. Jetzt: «Zeitraffer» = die Videos (Standard), darunter die Wahl «Videos / Fotos».

Lädt die gebaute Datei in einem eigenen Prozess (Daten im Temp-Ordner), legt Zeitraffer-Fotos, ein Zeitraffer-Video und eine
normale Aufnahme an und ruft list_recordings (die Antwort von /api/recordings) mit jeder Art auf:
  kind=timelapse_video -> nur die Videos · kind=timelapse_photo -> nur die Fotos · kind=timelapse (alte Adresse) = die Videos
  «Alle» / «Videos» wie bisher (Zeitraffer-Videos dabei, Fotos nicht) · «Bilder» ohne Zeitraffer-Fotos (wie bisher)
  Antwort «tl» {videos, photos, last_day}; ohne Video: videos = 0 (die Seite zeigt den Hinweis und «Video erstellen»)
Dazu die Seite: zweite Wahl #f-tlk, der Hinweis, ?kind= in der Adresse, Texte in fr / it / rm.

  python3 werkzeuge/verlauf_zeitraffer_test.py [--datei X.py]
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

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
HINWEIS = "No timelapse video yet – one is made every night at about 00:20 from yesterday's photos (Settings → Timelapse)"

LAUF = r'''
import json, os, sys
ns = {"__name__": "mw_verlauf_tl_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
rec = sys.argv[2]; hinweis = sys.argv[3]
C = ns["CFG"]; C.update(record_dir=rec)
ns["log_event"] = lambda *a, **k: None
erg = []
def ok(b, t):
    erg.append([bool(b), t])
tld = ns["tl_dir"](); os.makedirs(tld, exist_ok=True)
for i in range(30):
    open(os.path.join(tld, "tl_20261120_%02d%02d00.jpg" % (8 + i // 60, i % 60)), "wb").write(b"\xff\xd8x" * 10)
for i in range(5):
    open(os.path.join(tld, "tl_20261121_09%02d00.jpg" % i), "wb").write(b"\xff\xd8x" * 10)
def liste(kind):
    r = ns["list_recordings"]({"kind": kind, "limit": "500"} if kind is not None else {"limit": "500"})
    return r, sorted(x["name"] for x in r["items"])
r, n = liste("timelapse_video")
ok(r["total"] == 0 and r["tl"]["videos"] == 0 and r["tl"]["photos"] == 35 and r["tl"]["last_day"] == "20261121",
   "ohne Video: «Zeitraffer → Videos» leer, tl = %s (die Seite zeigt den Hinweis + «Video erstellen»)" % r["tl"])
open(os.path.join(tld, "tlv_20261120_auto.mp4"), "wb").write(b"\x00" * 2000)
open(os.path.join(rec, "person_20261121_101500.jpg"), "wb").write(b"\xff\xd8x" * 10)
r, n = liste("timelapse_video")
ok(n == ["timelapse/tlv_20261120_auto.mp4"], "«Zeitraffer → Videos»: nur das Video (%s)" % n[:5])
r, n = liste("timelapse")
ok(n == ["timelapse/tlv_20261120_auto.mp4"], "alte Adresse kind=timelapse = die Videos (%s)" % n[:5])
r, n = liste("timelapse_photo")
ok(len(n) == 35 and all(x.startswith("timelapse/tl_") for x in n), "«Zeitraffer → Fotos»: die 35 Fotos (%d)" % len(n))
r, n = liste(None)
ok("timelapse/tlv_20261120_auto.mp4" in n and not any(x.startswith("timelapse/tl_") for x in n) and "person_20261121_101500.jpg" in n,
   "«Alle» wie bisher: Video ja, Zeitraffer-Fotos nein (%s)" % n[:5])
r, n = liste("video")
ok(n == ["timelapse/tlv_20261120_auto.mp4"], "«Videos» wie bisher (mit Zeitraffer-Videos) (%s)" % n)
r, n = liste("image")
ok(n == ["person_20261121_101500.jpg"], "«Bilder» wie bisher (ohne Zeitraffer-Fotos) (%s)" % n)
r, n = liste("timelapse_video")
ok(r["tl"]["videos"] == 1 and r["tl"]["photos"] == 35, "mit Video: tl = %s (kein Hinweis mehr)" % r["tl"])
page = ns["REC_PAGE"] if "REC_PAGE" in ns else ""
ok('id="f-tlk"' in page and 'data-tlk="timelapse_video"' in page and 'data-tlk="timelapse_photo"' in page and 'data-kind="timelapse"' in page,
   "Seite: zweite Wahl «Videos / Fotos» unter «Zeitraffer», Typ-Knöpfe unverändert")
ok(hinweis in page and "empty-tlmk" in page and 'q_.get("kind")' in page, "Seite: Hinweis, «Video erstellen», ?kind= in der Adresse")
ok(all(ns["TRX"][L].get(hinweis) for L in ("fr", "it", "rm")) and ns["DE"].get(hinweis, "").startswith("Noch kein Zeitraffer-Video"),
   "Hinweis in 5 Sprachen")
ok(all(ns["TRX"][L].get(k) for L in ("fr", "it", "rm") for k in ("Photos", "Videos", "Create video")), "«Fotos», «Videos», «Video erstellen» in fr / it / rm")
print("ERG " + json.dumps(erg))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Verlauf-Zeitraffer-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_vtl_")
    try:
        rec = os.path.join(tmp, "aufnahmen"); os.makedirs(rec)
        env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "daten"))
        r = subprocess.run([sys.executable, "-c", LAUF, datei, rec, HINWEIS], capture_output=True, text=True, timeout=600, env=env,
                           cwd=os.path.dirname(datei))
        erg = None
        for ln in (r.stdout + r.stderr).splitlines():
            if ln.startswith("ERG "):
                erg = json.loads(ln[4:])
        if erg is None:
            print((r.stdout + r.stderr)[-3000:])
            print("FEHLER: der Lauf brach ab")
            return 1
        for b, t in erg:
            print(("  ok   " if b else "  FEHLER  ") + t)
        bad = [t for b, t in erg if not b]
        print("Verlauf-Zeitraffer-Test OK" if not bad else "FEHLER: " + "; ".join(bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
