#!/usr/bin/env python3
"""Test «systemctl stop = Exit-Code 0» (4.20.1, Teil 010 / 640): MoveEye endet auf SIGTERM sauber mit 0 – auch während es
noch lädt (vorher beendete Python das Programm durch das Signal, systemd zeigte «failed») und nachdem die Seite läuft
(Aufnahme beenden, Einstellungen speichern).

Startet die gebaute Datei ohne Fenster in einem Temp-Ordner:
  1. SIGTERM während MoveEye lädt (nach dem Übersetzen der Datei, bevor die Seite antwortet) -> Exit-Code 0
     (ganz am Anfang, solange Python die Datei noch übersetzt, endet sie durch das Signal: systemd zählt das als sauber)
  2. SIGTERM wenn die Seite antwortet -> Exit-Code 0 in höchstens 30 s, Einstellungen gespeichert
  3. zwei SIGTERM kurz nacheinander -> Exit-Code 0

  python3 werkzeuge/sigterm_test.py [--datei X.py]
"""
import argparse
import glob
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
erg = []


def ok(b, t):
    erg.append((bool(b), t))
    print(("  ok   " if b else "  FEHLER  ") + t, flush=True)


def frei_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def starten(datei, tmp, name):
    d = os.path.join(tmp, name); os.makedirs(d)
    json.dump({"cfg": {"setup_done": True, "dev_phase_done": True}}, open(os.path.join(d, "motionwatch_settings.json"), "w"))
    port = frei_port()
    p = subprocess.Popen([sys.executable, datei, "--headless", "--bind", "127.0.0.1", "--port", str(port), "--config", d],
                         stdout=open(os.path.join(tmp, name + ".log"), "w"), stderr=subprocess.STDOUT, cwd=tmp,
                         env=dict(os.environ, MOTIONWATCH_HOME=d))
    return p, port, d


def seite_da(port, limit=180):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            op.open("http://127.0.0.1:%d/" % port, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def warten(p, limit):
    try:
        return p.wait(limit)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait(10)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("SIGTERM-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_sigterm_")
    try:
        p, port, _d = starten(datei, tmp, "laden")
        log = os.path.join(tmp, "laden.log"); t0 = time.time()
        while time.time() - t0 < 60 and "VIDEOIO" not in open(log, errors="replace").read() and p.poll() is None:
            time.sleep(0.05)                                    # the program runs (camera search) - the web page is not up yet
        up = seite_da(port, 0.1)
        p.send_signal(signal.SIGTERM)
        rc = warten(p, 60)
        ok(rc == 0, "SIGTERM während des Ladens (Seite noch nicht da: %s): Exit-Code %s (0 erwartet, nicht -15)" % (not up, rc))

        p, port, d = starten(datei, tmp, "laeuft")
        ok(seite_da(port), "Seite antwortet")
        f = os.path.join(d, "motionwatch_settings.json"); m0 = os.path.getmtime(f)
        time.sleep(1.5)
        t0 = time.time(); p.send_signal(signal.SIGTERM)
        rc = warten(p, 60)
        ok(rc == 0 and time.time() - t0 < 30, "SIGTERM wenn die Seite läuft: Exit-Code %s in %.1f s" % (rc, time.time() - t0))
        ok(os.path.getmtime(f) > m0, "Einstellungen beim Beenden gespeichert")

        p, port, _d = starten(datei, tmp, "zweimal")
        ok(seite_da(port), "Seite antwortet (3)")
        p.send_signal(signal.SIGTERM); time.sleep(0.05); p.send_signal(signal.SIGTERM)
        rc = warten(p, 60)
        ok(rc == 0, "zwei SIGTERM kurz nacheinander: Exit-Code %s" % rc)
        bad = [t for b, t in erg if not b]
        if bad:
            for n in ("laden", "laeuft", "zweimal"):
                try:
                    print("--- %s.log (Ende)\n" % n + open(os.path.join(tmp, n + ".log"), errors="replace").read()[-1500:])
                except OSError:
                    pass
        print("SIGTERM-Test OK" if not bad else "FEHLER: " + "; ".join(bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
