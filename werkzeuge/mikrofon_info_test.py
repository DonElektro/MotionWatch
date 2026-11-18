#!/usr/bin/env python3
"""Test «Kein Mikrofon eingesteckt» (Teil 639zzzh): fehlt das Mikrofon, ist es ein grauer Hinweis, kein rotes Problem.

Startet MoveEye ohne Fenster mit der Demo und einem Ersatz für arecord, der wie ein fehlendes USB-Mikrofon antwortet
(«audio open error: No such device»). Geprüft über /api/health (Selbstdiagnose) und /api/state (Kopf-Zähler, Schutz-Ampel):
  1. kein Geräusch-Alarm / Klatschschalter / «Gesundheit!»: Mikrofon grau (Stufe «off»), Text «Kein Mikrofon eingesteckt
     (z. B. USB-Kamera)», zählt nicht als Problem (Kopf «N Probleme», Schutz-Ampel)
  2. Geräusch-Alarm an: rot, der Text nennt «Geräusch-Alarm», zählt als Problem
  3. wieder aus: wieder grau

  python3 werkzeuge/mikrofon_info_test.py [--datei X.py]
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Mikro-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def main():
    ap = argparse.ArgumentParser(description="Kein Mikrofon eingesteckt = Hinweis")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5181)
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_mikro_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    binx = os.path.join(tmp, "bin"); os.makedirs(binx)
    fake = os.path.join(binx, "arecord")                 # like arecord without the USB microphone
    with open(fake, "w") as f:
        f.write("#!/bin/sh\nif [ \"$1\" = \"-l\" ]; then echo '**** List of CAPTURE Hardware Devices ****'; exit 0; fi\n"
                "echo 'arecord: main:850: audio open error: No such device' >&2\nexit 1\n")
    os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "audio_in": "plughw:CARD=Device,DEV=0",
          "noise_alarm": False, "clap_on": False, "sneeze_on": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    env = dict(os.environ, PATH=binx + os.pathsep + os.environ.get("PATH", ""))
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = "http://127.0.0.1:%d" % a.port
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode(), "Content-Type": "application/json"}
        req = lambda path, d=None: json.loads(op.open(urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None,
                                                                              headers=H), timeout=15).read() or b"{}")
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)

        def lage(want_level, t_max=40, bad=None):          # bad: also wait until the head counts the problems of the list
            t_ = time.time() + t_max; mic = None; s = {}
            while time.time() < t_:
                h = req("/api/health?lang=de")
                mic = next((x for x in h.get("items") or [] if x.get("id") == "mic"), None)
                s = req("/api/state")
                rot_ = [x.get("id") for x in h.get("items") or [] if x.get("level") == "bad"]
                if mic and mic.get("level") == want_level and mic.get("mic_none") and (bad is None or (h.get("count") or {}).get("bad", 0) == len(rot_)):
                    break
                time.sleep(1)
            lage.rot = sorted(x.get("id") for x in h.get("items") or [] if x.get("level") == "bad")   # 4.16.1: from the same answer
            st_ = s.get("state") or {}
            prot = " ".join(x.get("text", "") for x in ((st_.get("protect") or {}).get("items") or []))
            return mic, h.get("count") or {}, (st_.get("health") or {}), prot

        mic, cnt, hs, prot = lage("off")
        print("    Mikrofon:", (st.get("audio_in"), mic))
        pruef(bool(mic) and mic["level"] == "off" and "Kein Mikrofon eingesteckt (z. B. USB-Kamera)" in mic["text"],
              "kein Mikrofon, nichts braucht es: grauer Hinweis «Kein Mikrofon eingesteckt (z. B. USB-Kamera)» (%s)" % mic)
        pruef(bool(mic) and "fehler" not in mic, "der Hinweis bietet kein «Mikrofon stört» / «Beheben» an")
        pruef(hs.get("bad") == cnt.get("bad") and "Mikrofon" not in prot and "No such device" not in prot,
              "zählt nicht als Problem (Kopf %s, Schutz-Ampel ohne Mikrofon)" % hs)
        bad0 = cnt.get("bad", 0)
        schlecht = lambda: sorted(x.get("id") for x in req("/api/health?lang=de").get("items") or [] if x.get("level") == "bad")
        bad0_ids = schlecht()
        r = req("/api/set", {"key": "noise_alarm", "value": True})
        pruef(r.get("ok", True) is not False, "Geräusch-Alarm einschalten (%s)" % r)
        mic, cnt, hs, prot = lage("bad")
        pruef(bool(mic) and mic["level"] == "bad" and "Geräusch-Alarm" in mic["text"], "Geräusch-Alarm an: rot, nennt die Funktion (%s)" % mic)
        # 4.16.1: «ai» / «cam» can still change by themselves right after the start (CI) - so the mic line is compared, and the
        # count with the list of the same answer
        pruef("mic" in lage.rot and cnt.get("bad", 0) == len(lage.rot), "zählt jetzt als Problem (%d -> %d, %s)" % (bad0, cnt.get("bad", 0), lage.rot))
        req("/api/set", {"key": "noise_alarm", "value": False})
        mic, cnt, hs, prot = lage("off", bad=True)              # the count follows a little later than the item (CI)
        pruef(bool(mic) and mic["level"] == "off" and "mic" not in lage.rot and cnt.get("bad", 0) == len(lage.rot),
              "wieder aus: wieder grau (%s; rot vorher %s, jetzt %s)" % (mic, bad0_ids, lage.rot))
        if p.poll() is not None:
            FEHLER.append("MoveEye ist während des Tests abgestürzt")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Mikrofon-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
