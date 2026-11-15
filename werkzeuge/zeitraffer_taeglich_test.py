#!/usr/bin/env python3
"""Test «Jeden Tag automatisch ein Video» (MoveEye Teil 639zzzv, Zeitraffer Teil 220).

Wunsch des Besitzers (14.11.2026): kurz nach Mitternacht macht MoveEye aus den Zeitraffer-Fotos von gestern ein Video
(tlv_JJJJMMTT_auto.mp4), leise (nice / ionice), nie während Alarm / Aufnahme / Folgen, bei schwachem Akku erst in der
nächsten Nacht, verpasste Tage (höchstens 7) nachholen, die Fotos bleiben, die Grenze des Zeitraffer-Ordners gilt.

Der Test lädt die gebaute Datei in einem eigenen Python-Prozess (Daten-Ordner im Temp-Ordner), ersetzt die Uhr
(tld_now), legt falsche Fotos an (kleine JPG mit Nummer) und ruft den Nacht-Schritt tld_tick direkt auf. Video mit dem
echten ffmpeg, wenn es da ist (Bilder gezählt mit ffprobe), sonst mit einem Ersatz-ffmpeg (nur der Ablauf).
Geprüft: Schalter aus -> nichts; vor 00:20 / ab 06:00 nichts; gestern genau einmal; ein Tag mit Video (auch von Hand)
bleibt; wartet bei Alarm / Aufnahme / kurz nach dem Alarm und macht es später in derselben Nacht; Alarm mitten im Video
-> abgebrochen, keine halbe Datei, später neu; Akku schwach -> nächste Nacht; Nachholen nach einer Pause (genau die
letzten 7 Tage); Ordner-Grenze -> übersprungen mit Protokoll-Zeile, kein neuer Versuch; Umstellung alter Einstellungen
(einmal an + Hinweis), eigene Wahl «aus» bleibt; Liste der Zeitraffer-Seite.

  python3 werkzeuge/zeitraffer_taeglich_test.py [--datei X.py] [--ersatz]
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

LAUF = r'''
import json, os, shutil, subprocess, sys, time
from datetime import datetime
ns = {"__name__": "mw_tld_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
rec = sys.argv[2]
import cv2, numpy as np
C, S, TLD = ns["CFG"], ns["STATE"], ns["TLD"]
logs = []
ns["log_event"] = lambda kind, msg, *a, **k: logs.append(msg)
ns["save_settings"] = lambda *a, **k: None
uhr = {"t": datetime(2026, 11, 14, 0, 25)}
ns["tld_now"] = lambda: uhr["t"]
C.update(record_dir=rec, timelapse_fps=10.0, timelapse_max_gb=2.0, timelapse_daily=True, tld_skip=[])
S.update(recording=False, persons=0, tracking=False)
ns["BATT_SAVE"]["on"] = False
erg = []
echt = bool(os.environ.get("TLD_ECHT"))


def ok(bed, text):
    erg.append([bool(bed), text])


def tld():
    return ns["tl_dir"]()


def fotos(day, n, size=(320, 240)):
    os.makedirs(tld(), exist_ok=True)
    for i in range(n):
        img = np.full((size[1], size[0], 3), 40 + i * 10 % 200, np.uint8)
        cv2.putText(img, str(i), (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        cv2.imwrite(os.path.join(tld(), "tl_%s_%02d%02d00.jpg" % (day, 8 + i // 60, i % 60)), img)


def videos():
    return sorted(n for n in os.listdir(tld()) if n.startswith("tlv_"))


def reste():
    return sorted(n for n in os.listdir(tld()) if n.startswith(".tlv_"))


def nacht(y, m, d, hh=0, mm=25):
    uhr["t"] = datetime(y, m, d, hh, mm)


def bis_fertig(n=20):
    r = []
    for _ in range(n):
        x = ns["tld_tick"]()
        r.append(x)
        if x in ("nothing to do", "done tonight", "battery low", "off", "not now"):
            break
    return r


def frames(name):
    if not echt or not shutil.which("ffprobe"):
        return None
    p = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
                        "-of", "csv=p=0", os.path.join(tld(), name)], capture_output=True, text=True)
    try:
        return int(p.stdout.strip())
    except ValueError:
        return -1


# 1. setting off: nothing at all
fotos("20261113", 6); fotos("20261114", 3)
C["timelapse_daily"] = False
ok(ns["tld_tick"]() == "off" and videos() == [], "Schalter aus: kein Video")
C["timelapse_daily"] = True
# 2. outside the night window
nacht(2026, 11, 14, 0, 10); a = ns["tld_tick"]()
nacht(2026, 11, 14, 6, 0); b = ns["tld_tick"]()
ok(a == b == "not now" and videos() == [], "vor 00:20 und ab 06:00 nichts (%s, %s)" % (a, b))
# 3. yesterday once
nacht(2026, 11, 14, 0, 25)
r = ns["tld_tick"]()
ok(r == "made tlv_20261113_auto.mp4" and videos() == ["tlv_20261113_auto.mp4"], "00:25: gestern -> tlv_20261113_auto.mp4 (%s)" % r)
f = frames("tlv_20261113_auto.mp4")
ok(f in (None, 6), "das Video hat 6 Bilder (ffprobe: %s)" % ("kein echtes ffmpeg" if f is None else f))
ok(len(ns["tl_photos"]("20261113")) == 6 and reste() == [], "die Fotos bleiben, keine halbe Datei")
ok(any("Daily timelapse video made: tlv_20261113_auto.mp4 (6 photos" in x for x in logs), "Protokoll-Zeile «made»")
ok(S.get("timelapse_render") == "video ready: tlv_20261113_auto.mp4", "Zeitraffer-Seite: «Video fertig» (%s)" % S.get("timelapse_render"))
ov = ns["tl_overview"]()
ok("tlv_20261113_auto.mp4" in [v["name"] for v in ov["videos"]], "steht in der Liste der Zeitraffer-Seite (/api/timelapse)")
r = ns["tld_tick"]()
r2 = ns["tld_tick"]()
ok(r == "nothing to do" and r2 == "done tonight" and len(videos()) == 1, "dieselbe Nacht: nichts mehr (%s, %s)" % (r, r2))
# 4. next night: yesterday made, the day before (has a video) skipped; a day with a video made by hand too
open(os.path.join(tld(), "tlv_20261112_101010.mp4"), "wb").close(); fotos("20261112", 4)
nacht(2026, 11, 15, 0, 30)
r = bis_fertig()
ok(r == ["made tlv_20261114_auto.mp4", "nothing to do"], "nächste Nacht: nur der 14. (13. und 12. haben ein Video) (%s)" % r)
ok(not os.path.exists(os.path.join(tld(), "tlv_20261112_auto.mp4")), "Video von Hand (tlv_20261112_101010.mp4) zählt als vorhanden")
# 5. alarm: wait, retry in the same night; never after 06:00
fotos("20261115", 3)
nacht(2026, 11, 16, 0, 21); S["persons"] = 1
r1 = ns["tld_tick"]()
nacht(2026, 11, 16, 2, 0); S["persons"] = 0; S["recording"] = True
r2 = ns["tld_tick"]()
S["recording"] = False; S["tracking"] = True
r3 = ns["tld_tick"]()
S["tracking"] = False; TLD["alarm_t"] = time.time()
r4 = ns["tld_tick"]()
ok([r1, r2, r3, r4] == ["busy"] * 4 and not os.path.exists(os.path.join(tld(), "tlv_20261115_auto.mp4")),
   "wartet bei Person / Aufnahme / Folgen / kurz nach dem Alarm (%s)" % [r1, r2, r3, r4])
ok(sum("waits: alarm has priority" in x for x in logs) == 1, "eine Zeile «wartet» pro Nacht")
nacht(2026, 11, 16, 6, 5); TLD["alarm_t"] = 0.0
r5 = ns["tld_tick"]()
ok(r5 == "not now" and not os.path.exists(os.path.join(tld(), "tlv_20261115_auto.mp4")), "ab 06:00 nicht mehr (%s)" % r5)
nacht(2026, 11, 16, 3, 0)
r6 = ns["tld_tick"]()
ok(r6 == "made tlv_20261115_auto.mp4", "Alarm vorbei, noch vor 06:00 -> Video (%s)" % r6)
# 6. alarm starts while ffmpeg runs: stopped, nothing half, later again
fotos("20261116", 40, (640, 480))
nacht(2026, 11, 17, 0, 40)
echt_busy = ns["tld_busy"]; n = {"c": 0}


def busy_ab_2():
    n["c"] += 1
    return n["c"] >= 2


ns["tld_busy"] = busy_ab_2
r = ns["tld_tick"]()
ns["tld_busy"] = echt_busy
ok(r == "busy" and reste() == [] and not os.path.exists(os.path.join(tld(), "tlv_20261116_auto.mp4")),
   "Alarm mitten im Video: abgebrochen, keine halbe Datei (%s)" % r)
ok(S.get("timelapse_render") == "waiting: alarm has priority", "Zeitraffer-Seite: «wartet: Alarm hat Vorrang»")
r = ns["tld_tick"]()
ok(r == "made tlv_20261116_auto.mp4" and frames("tlv_20261116_auto.mp4") in (None, 40), "danach neu gemacht, ganz (%s)" % r)
# 7. catch-up after a pause: exactly the last 7 days, yesterday first
for d in range(20, 30):
    fotos("202611%02d" % d, 3)
nacht(2026, 11, 30, 0, 30)
r = bis_fertig()
gemacht = [x[len("made tlv_"):len("made tlv_") + 8] for x in r if x.startswith("made")]
ok(gemacht == ["202611%02d" % d for d in range(29, 22, -1)] and r[-1] == "nothing to do",
   "Nachholen: genau die letzten 7 Tage, gestern zuerst (%s)" % gemacht)
ok(not any(os.path.exists(os.path.join(tld(), "tlv_202611%02d_auto.mp4" % d)) for d in (20, 21, 22)), "ältere Tage nicht")
# 8. battery low: this night nothing, next night
fotos("20261201", 3)
ns["BATT_SAVE"]["on"] = True; nacht(2026, 12, 2, 0, 30)
r = bis_fertig()
ok(r == ["battery low"] and not os.path.exists(os.path.join(tld(), "tlv_20261201_auto.mp4")), "Akku schwach: diese Nacht nichts (%s)" % r)
ok(ns["tld_tick"]() == "done tonight", "auch später in derselben Nacht nicht")
ns["BATT_SAVE"]["on"] = False; nacht(2026, 12, 3, 0, 30)
r = bis_fertig()
ok(r == ["made tlv_20261201_auto.mp4", "nothing to do"], "nächste Nacht nachgeholt (%s)" % r)
# 9. the max. timelapse folder: skipped with a log line, no new try - independent of the encoder (own fake ffmpeg, fixed size)
fake = os.path.join(os.path.dirname(rec), "fakebin"); os.makedirs(fake, exist_ok=True)
marke = os.path.join(os.path.dirname(rec), "ffmpeg_lief")
with open(os.path.join(fake, "ffmpeg"), "w") as fh:
    fh.write("#!/bin/sh\nfor a; do last=$a; done\ntouch '%s'\necho frame=5\nhead -c 5000 /dev/zero > \"$last\"\necho progress=end\n" % marke)
os.chmod(os.path.join(fake, "ffmpeg"), 0o755)
pfad = os.environ.get("PATH", ""); os.environ["PATH"] = fake + os.pathsep + pfad
# 9a. clearly too little room (200 bytes): skipped before the encoder starts
fotos("20261203", 5)
voll = ns["tld_folder_bytes"]()
C["timelapse_max_gb"] = (voll + 200) / 1024 ** 3
nacht(2026, 12, 4, 0, 30)
r = ns["tld_tick"]()
ok(r == "skipped" and not os.path.exists(os.path.join(tld(), "tlv_20261203_auto.mp4")) and reste() == [], "Video wäre über der Grenze: übersprungen (%s)" % r)
ok(any("20261203 skipped: it would exceed the max. timelapse folder" in x for x in logs), "Protokoll-Zeile «would exceed»")
ok(len(ns["tl_photos"]("20261203")) == 5 and "20261203" in C["tld_skip"], "Fotos bleiben, der Tag ist gemerkt")
ok(not os.path.exists(marke), "Schätzung vorher: ffmpeg gar nicht gestartet")
# 9b. the estimate fits (2000 bytes), the real file (5000 bytes) does not: made, measured, deleted, skipped
fotos("20261204", 5)
voll = ns["tld_folder_bytes"]()
C["timelapse_max_gb"] = (voll + 2000) / 1024 ** 3
nacht(2026, 12, 5, 0, 30)
r = ns["tld_tick"]()
ok(r == "skipped" and os.path.exists(marke) and not os.path.exists(os.path.join(tld(), "tlv_20261204_auto.mp4")) and reste() == [],
   "echte Grösse nach dem Video über der Grenze: gelöscht, übersprungen (%s)" % r)
ok(any("20261204 skipped: it would exceed the max. timelapse folder" in x for x in logs) and "20261204" in C["tld_skip"],
   "Protokoll-Zeile, der Tag ist gemerkt")
nacht(2026, 12, 6, 0, 30)
ok(ns["tld_tick"]() == "nothing to do", "kein neuer Versuch in der nächsten Nacht")
os.environ["PATH"] = pfad
C["timelapse_max_gb"] = (voll - 10) / 1024 ** 3; fotos("20261206", 3); nacht(2026, 12, 7, 0, 30)
r = ns["tld_tick"]()
ok(r == "skipped" and any("20261206 skipped: the timelapse folder is full" in x for x in logs), "Ordner schon voll: ohne ffmpeg übersprungen (%s)" % r)
C["timelapse_max_gb"] = 2.0
# 10. setting off with waiting days
fotos("20261207", 3); C["timelapse_daily"] = False; nacht(2026, 12, 8, 0, 30)
ok(ns["tld_tick"]() == "off" and not os.path.exists(os.path.join(tld(), "tlv_20261207_auto.mp4")), "Schalter aus: wartende Tage bleiben ohne Video")
# 10b. photo cleanup leaves room for the daily videos: photos at most ~90 % of the max. folder, oldest first, videos never
shutil.rmtree(tld()); fotos("20261210", 20)
open(os.path.join(tld(), "tlv_20261209_auto.mp4"), "wb").write(b"v" * 1000)
open(os.path.join(tld(), "tlv_20261209_101010.mp4"), "wb").write(b"v" * 1000)
ph = lambda: sorted(ns["tl_photos"]())
psum = lambda: sum(os.path.getsize(os.path.join(tld(), n)) for n in ph())
alle, tot = ph(), psum()
C["timelapse_max_gb"] = tot * 1.02 / 1024 ** 3
C["timelapse_daily"] = False; ns["tl_cleanup"]()
ok(ph() == alle, "Schalter aus: Fotos bis 100 %% wie bisher (%d Fotos bleiben)" % len(alle))
C["timelapse_daily"] = True; ns["tl_cleanup"]()
rest = ph()
ok(rest and len(rest) < len(alle) and rest == alle[len(alle) - len(rest):] and psum() <= 0.9 * tot * 1.02,
   "Schalter an: Fotos höchstens 90 %% (%d von %d bleiben, die ältesten gelöscht)" % (len(rest), len(alle)))
ok(videos() == ["tlv_20261209_101010.mp4", "tlv_20261209_auto.mp4"], "Videos nie gelöscht (%s)" % videos())
ok(any("old photo(s) deleted" in x for x in logs), "Protokoll-Zeile der Aufräumung")
C["timelapse_max_gb"] = 2.0
# 11. settings of an older version: on once + notice; own choice «off» later stays
C.update(timelapse_daily=False, tld_mig=False, tld_note="", tld_seen=[])
ns["apply_settings"]({"cfg": {"timelapse_on": True, "timelapse_daily": False}})
ok(C["timelapse_daily"] is True and C["tld_note"] == "pending" and any("one video per day switched on" in x for x in logs),
   "altes Gerät: nach dem Update an, Protokoll-Zeile")
st = ns["news_state"]("web", "de")
ok(any("Jeden Tag automatisch ein Video" in it.get("t", "") for it in st.get("items") or []), "Hinweis in «Neu in dieser Version» (Deutsch)")
ns["news_seen"]("web")
ok(not any("⏱" in it.get("t", "") for it in ns["news_state"]("web", "de").get("items") or []), "Hinweis nur einmal")
ns["apply_settings"]({"cfg": {"tld_mig": True, "timelapse_daily": False}})
ok(C["timelapse_daily"] is False, "eigene Wahl «aus» bleibt nach dem nächsten Start")
lab = [t for t in ns["TOGGLES"] if t[1] == "timelapse_daily"]
ok(lab and lab[0][0] == "Timelapse" and all(ns["tr"](lab[0][2], L) != lab[0][2] for L in ("de", "fr", "it", "rm")),
   "Schalter unter Zeitraffer, 5 Sprachen (%s)" % [ns["tr"](lab[0][2], L) for L in ("de", "fr", "it", "rm")] if lab else "Schalter fehlt")
print("ERG " + json.dumps(erg, ensure_ascii=False))
os._exit(0)
'''

ERSATZ_FFMPEG = """#!/bin/sh
for a; do last=$a; done
echo "frame=2"
sleep 0.3
head -c 5000 /dev/zero > "$last"
echo "progress=end"
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--ersatz", action="store_true", help="Ersatz-ffmpeg auch wenn ffmpeg da ist (wie ein Rechner ohne ffmpeg)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Zeitraffer-täglich-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_tld_")
    try:
        env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "daten"))
        if shutil.which("ffmpeg") and not a.ersatz:
            env["TLD_ECHT"] = "1"
            print("  echtes ffmpeg: " + shutil.which("ffmpeg"))
        else:
            b = os.path.join(tmp, "bin"); os.makedirs(b)
            with open(os.path.join(b, "ffmpeg"), "w") as f:
                f.write(ERSATZ_FFMPEG)
            os.chmod(os.path.join(b, "ffmpeg"), 0o755)
            env["PATH"] = b + os.pathsep + env.get("PATH", "")
            print("  kein ffmpeg – Ersatz (nur der Ablauf, keine echten Videos)")
        r = subprocess.run([sys.executable, "-c", LAUF, datei, os.path.join(tmp, "aufnahmen")], capture_output=True, text=True,
                           timeout=600, env=env, cwd=os.path.dirname(datei))
        erg = None
        for ln in (r.stdout + r.stderr).splitlines():
            if ln.startswith("ERG "):
                erg = json.loads(ln[4:])
        if erg is None:
            print((r.stdout + r.stderr)[-3000:])
            print("FEHLER: der Lauf brach ab")
            return 1
        fehler = 0
        for bed, text in erg:
            print(("  ok   " if bed else "  FEHLER ") + text)
            fehler += 0 if bed else 1
        print("Ergebnis: %d Prüfungen, %s" % (len(erg), "alle ok" if not fehler else "%d FEHLER" % fehler))
        return 1 if fehler else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
