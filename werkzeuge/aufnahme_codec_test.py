#!/usr/bin/env python3
"""Test: Aufnahme mit Ersatz-Encoder (MoveEye 4.14.1, Teil 420 open_writer) – nie ohne Aufnahme, wenn ein Encoder fehlt.

  Ein erfundenes «ffmpeg» vorne im PATH scheitert für die genannten Encoder genau wie auf einem Server ohne Pi-Hardware
  («[h264_v4l2m2m] Could not find a valid device»), sonst ruft es das echte ffmpeg. Geprüft wird in je einem eigenen Prozess:
    A. Hardware-Encoder und libx264 fehlen: OpenCV (avc1 / mp4v) nimmt auf, die Datei hat Bilder; genau EINE Zeile im
       Protokoll nennt, was fehlt und womit aufgenommen wird; ein zweites Öffnen schreibt keine weitere Zeile.
    B. nur der Hardware-Encoder fehlt (das echte ffmpeg mit libx264 da): ffmpeg x264, H.264 in der Datei, keine Zeile.
    C. gar kein ffmpeg: OpenCV nimmt auf.

  python3 werkzeuge/aufnahme_codec_test.py [--datei webcam_bewegung_X_Y_Z.py]
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
FEHLER = []

FAKE_FFMPEG = r'''#!/bin/sh
# erfundenes ffmpeg: scheitert für die Encoder in FAKE_FFMPEG_FAIL, sonst das echte ffmpeg (REAL_FFMPEG)
for a in "$@"; do
  case ",$FAKE_FFMPEG_FAIL," in *",$a,"*) echo "[$a @ 0x0] Could not find a valid device" >&2; echo "Error while opening encoder" >&2; exit 1;; esac
done
[ -n "$REAL_FFMPEG" ] && exec "$REAL_FFMPEG" "$@"
exit 1
'''

LAUF = r'''
import json, os, sys, shutil as _sh
fall = sys.argv[2]
if fall == "C":                                      # no ffmpeg on this computer
    _w = _sh.which
    _sh.which = lambda c, *a, **k: None if os.path.basename(str(c)) == "ffmpeg" else _w(c, *a, **k)
ns = {"__name__": "mw_codec_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
LOG = []
_log0 = ns["log_event"]
def _log(kind, text, *a, **k):
    LOG.append(str(text))
    return _log0(kind, text, *a, **k)
ns["log_event"] = _log
import numpy as np
R = {"files": []}
for n in range(2):
    p = os.path.join(sys.argv[3], f"rec{n}.mp4")
    w, codec = ns["open_writer"](p, 4.0, (320, 240))
    R.setdefault("codec", []).append(codec); R.setdefault("enc", []).append(ns["STATE"].get("recording_enc"))
    if w is None:
        R["files"].append(0); continue
    for i in range(12):
        f = np.zeros((240, 320, 3), np.uint8); f[:, i * 20:(i + 1) * 20] = 255
        w.write(f)
    w.release()
    R["files"].append(os.path.getsize(p) if os.path.exists(p) else 0)
    R.setdefault("paths", []).append(p)
R["log"] = [l for l in LOG if l.startswith("Video encoder:")]
print("ERGEBNIS " + json.dumps(R))
'''


def ok(cond, text):
    print(("  ok     " if cond else "  FEHLER ") + text, flush=True)
    if not cond:
        FEHLER.append(text)


def lauf(datei, fall, fail, tmp):
    fake = os.path.join(tmp, "bin_" + fall)
    os.makedirs(fake, exist_ok=True)
    p = os.path.join(fake, "ffmpeg")
    with open(p, "w") as f:
        f.write(FAKE_FFMPEG)
    os.chmod(p, 0o755)
    out = os.path.join(tmp, "out_" + fall)
    os.makedirs(out, exist_ok=True)
    real = shutil.which("ffmpeg") or ""
    env = dict(os.environ, PATH=fake + os.pathsep + os.environ.get("PATH", ""), FAKE_FFMPEG_FAIL=fail, REAL_FFMPEG=real,
               MOTIONWATCH_HOME=os.path.join(tmp, "home_" + fall))
    r = subprocess.run([sys.executable, "-c", LAUF, datei, fall, out], capture_output=True, text=True, timeout=300, env=env,
                       cwd=os.path.dirname(datei))
    m = re.search(r"^ERGEBNIS (.*)$", r.stdout, re.M)
    if not m:
        print(r.stdout[-1500:], r.stderr[-2500:])
        ok(False, f"{fall}: Lauf ohne Ergebnis (Exit {r.returncode})")
        return None
    return json.loads(m.group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(
        glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
        key=lambda p: tuple(int(x) for x in re.findall(r"(\d+)_(\d+)_(\d+)\.py$", p)[0]))[-1]
    print(f"Aufnahme mit Ersatz-Encoder: {os.path.basename(datei)}")
    tmp = tempfile.mkdtemp(prefix="mw_codec_")
    try:
        print("A. Hardware-Encoder und libx264 fehlen (Server ohne Pi, ffmpeg ohne x264)")
        r = lauf(datei, "A", "h264_v4l2m2m,libx264", tmp)
        if r:
            ok(all(c in ("avc1", "mp4v") for c in r["codec"]), f"OpenCV nimmt auf ({r['codec']}, {r['enc']})")
            ok(all(s > 1000 for s in r["files"]), f"die Dateien haben Bilder ({r['files']} Bytes)")
            ok(len(r["log"]) == 1 and "ffmpeg x264" in r["log"][0] and "OpenCV" in r["log"][0],
               f"genau eine Zeile im Protokoll, auch beim zweiten Öffnen ({r['log']})")
        if shutil.which("ffmpeg") and "libx264" in subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True,
                                                                     text=True).stdout:
            print("B. nur der Hardware-Encoder fehlt (das echte ffmpeg mit libx264)")
            r = lauf(datei, "B", "h264_v4l2m2m", tmp)
            if r:
                ok(r["codec"] == ["h264", "h264"] and r["enc"][0] == "ffmpeg x264", f"ffmpeg x264 ({r['codec']}, {r['enc']})")
                ok(all(s > 1000 for s in r["files"]), f"die Dateien haben Bilder ({r['files']} Bytes)")
                ok(r["log"] == [], f"keine Zeile im Protokoll - nichts ist ausgefallen ({r['log']})")
                if shutil.which("ffprobe") and r.get("paths"):
                    v = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,nb_read_frames",
                                        "-count_frames", "-of", "csv=p=0", r["paths"][0]], capture_output=True, text=True).stdout.strip()
                    ok(v.startswith("h264"), f"ffprobe: {v}")
        else:
            print("B. übersprungen: kein ffmpeg mit libx264 auf diesem Rechner")
        print("C. gar kein ffmpeg")
        r = lauf(datei, "C", "", tmp)
        if r:
            ok(all(c in ("avc1", "mp4v") for c in r["codec"]) and all(s > 1000 for s in r["files"]),
               f"OpenCV nimmt auf ({r['codec']}, {r['files']} Bytes)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"Aufnahme-Encoder: {len(FEHLER)} Fehler")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
