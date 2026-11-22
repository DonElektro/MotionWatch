#!/usr/bin/env python3
"""Handwerkzeug (kein CI-Test): startet werkzeuge/aussicht_bilder.gd unter Xvfb (Bilder der 8 Bergtal-Aussichtspunkte).
Für den HP-Testweg (hp_test.txt: «python3 werkzeuge/aussicht_bilder.py», davor eine godot-Zeile, damit Godot geholt und
importiert ist). Godot aus $GODOT, Bilder nach $TMPDIR/aussicht/ (der HP sammelt sie als Artefakt ein).

  python3 werkzeuge/aussicht_bilder.py [--nur-tag] [--godot BIN] [--aus ORDNER]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(os.path.dirname(HIER), "simulator3d")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--godot", default=os.environ.get("GODOT", "godot"))
    p.add_argument("--aus", default=os.path.join(os.environ.get("TMPDIR", tempfile.gettempdir()), "aussicht"))
    p.add_argument("--nur-tag", action="store_true")
    a = p.parse_args()
    if not shutil.which("xvfb-run"):
        print("FEHLER: xvfb-run fehlt")
        return 1
    os.makedirs(a.aus, exist_ok=True)
    home = tempfile.mkdtemp(prefix="aussicht_home_")
    env = dict(os.environ, HOME=home)
    cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24", a.godot, "--path", ".", "-s",
           os.path.join(HIER, "aussicht_bilder.gd"), "--", "--no-update", "--no-tour", "--grafik", "normal",
           "--quality", "nice", "--aus", os.path.join(a.aus, "")]
    if a.nur_tag:
        cmd.append("--nur-tag")
    print(" ".join(cmd), flush=True)
    try:
        r = subprocess.run(cmd, cwd=SIM, env=env, timeout=40 * 60)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        print("FEHLER: Zeit abgelaufen")
        rc = 1
    finally:
        shutil.rmtree(home, ignore_errors=True)
    bilder = sorted(x for x in os.listdir(a.aus) if x.endswith(".jpg"))
    print("AUSSICHT %d Bilder in %s" % (len(bilder), a.aus))
    return 0 if rc == 0 and len(bilder) >= 8 else 1


if __name__ == "__main__":
    sys.exit(main())
