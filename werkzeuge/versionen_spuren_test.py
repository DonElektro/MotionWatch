#!/usr/bin/env python3
"""Drei Spuren: «versionen.py --pruefen» in einem kleinen Ersatz-Repository (git, nur die Dateien mit Nummern, falsche ZIPs).

Fälle: nur MoveEye erhöht · nur Sim erhöht (mit Ersatz-ZIP und --sim-json) · nur Gehäuse erhöht · etwas geändert, Nummer
vergessen (nur Warnung) · Brücke oder Sim-Nummer kleiner, Minimum der anderen Spur nicht erfüllt (Problem, Exit 1).

    python3 werkzeuge/versionen_spuren_test.py          # Ende: «Spuren-Test OK» (Exit 0)
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
FEHLER = []


def ok(bed, was, out=""):
    print(("  ok: " if bed else "  FEHLER: ") + was)
    if not bed:
        FEHLER.append(was)
        print("    " + out.strip().replace("\n", "\n    "))


def schreib(T, rel, text):
    p = os.path.join(T, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w" if isinstance(text, str) else "wb") as f:
        f.write(text)


def linux_zip(T, v):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("MoveEyeSim3D/Lies mich.txt", "NEU IN %s\nTest\n" % v)
        zf.writestr("MoveEyeSim3D/installieren.sh", "#!/bin/sh\n")
        zi = zipfile.ZipInfo("MoveEyeSim3D/MoveEyeSim3D.x86_64"); zi.external_attr = 0o755 << 16
        zf.writestr(zi, b"ELF" + v.encode())
    schreib(T, "simulator3d/MoveEyeSim3D_Linux.zip", buf.getvalue())
    schreib(T, "simulator3d/MotionWatch3D_Simulator.zip", b"PK-win-" + v.encode())


def main():
    W = tempfile.mkdtemp(prefix="spuren_test_")
    T = os.path.join(W, "repo")
    env = dict(os.environ, MW_VERSIONEN_REPO=T, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")

    def git(*a):
        return subprocess.run(["git"] + list(a), cwd=T, env=env, capture_output=True, text=True)

    def lauf(*a):
        r = subprocess.run([sys.executable, os.path.join(HIER, "versionen.py")] + list(a), env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def setz(rel, alt, neu):
        p = os.path.join(T, rel)
        s = open(p, encoding="utf-8").read()
        assert alt in s, (rel, alt)
        schreib(T, rel, s.replace(alt, neu, 1))

    def commit(msg):
        git("add", "-A"); git("commit", "-q", "-m", msg)
    try:
        os.makedirs(T)
        schreib(T, "quelle/010_grundlagen.py", 'APP_VERSION = "3.56.0"\n')
        schreib(T, "quelle/300_werkzeuge_simulator3d.py", 'SIM3D = {"version": "3.55.2", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": 1,\n'
                '         "sha256": "00"}\nSIM3D_LINUX = {"version": "3.55.2", "file": "simulator3d/MoveEyeSim3D_Linux.zip", "size": 1,\n'
                '               "sha256": "00", "stem": "MoveEyeSim3D_Linux"}\n')
        schreib(T, "quelle/545_simulator_updates.py", 'SIM_MIN = "3.55.0"\n')
        schreib(T, "quelle/500_web.py", "# web\n")
        schreib(T, "simulator3d/scripts/main.gd", 'extends Node\nconst VERSION := "3.55.2"\n')
        schreib(T, "simulator3d/scripts/abgleich.gd", 'extends Node\nconst MW_MIN := "3.55.0"\n')
        schreib(T, "simulator3d/scripts/welt.gd", "extends Node\n")
        schreib(T, "simulator3d/Lies mich.txt", "MoveEye Sim\n\nNEU IN 3.55.2\nalt\n")
        schreib(T, "hardware/gehaeuse/bau.json", json.dumps({"version": "5.3.0", "teile": []}, indent=1) + "\n")
        schreib(T, "hardware/gehaeuse/Dokumente/Montage.md", "Montage\n")
        schreib(T, "webcam_bewegung_3_56_0.py", 'APP_VERSION = "3.56.0"\n')
        schreib(T, "webcam_bewegung_3_0_2.py", 'APP_VERSION = "3.0.2"\n')
        schreib(T, "versions.json", json.dumps({"versions": [{"version": "3.56.0", "file": "webcam_bewegung_3_56_0.py"},
                                                            {"version": "3.0.2", "file": "webcam_bewegung_3_0_2.py", "bridge": True}]}, indent=1) + "\n")
        linux_zip(T, "3.55.2")
        rc, out = lauf("--sim-json", "3.55.2", "Start")
        ok(rc == 0, "Ausgangslage: version.json mit --sim-json", out)
        vj0 = json.load(open(os.path.join(T, "simulator3d", "version.json")))
        schreib(T, "quelle/300_werkzeuge_simulator3d.py",            # wie sim3d_sync.py / bauen.py --neue-version
                'SIM3D = {"version": "3.55.2", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": %d,\n         "sha256": "%s"}\n'
                'SIM3D_LINUX = {"version": "3.55.2", "file": "simulator3d/MoveEyeSim3D_Linux.zip", "size": %d,\n'
                '               "sha256": "%s", "stem": "MoveEyeSim3D_Linux"}\n' % (vj0["size"], vj0["sha256"], vj0["linux"]["size"], vj0["linux"]["sha256"]))
        git("init", "-q"); commit("Start")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Simulator" not in out and "WARNUNG: Gehäuse" not in out and "WARNUNG: MoveEye geändert" not in out
           and "MoveEye 3.56.0 · Sim 3.55.2 · Gehäuse 5.3.0" in out, "Ausgangslage: drei verschiedene Nummern sind ok", out)

        print("--- nur MoveEye")
        setz("quelle/500_web.py", "# web", "# web neu")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: MoveEye geändert seit 3.56.0" in out and "WARNUNG: Simulator" not in out, "MoveEye geändert, Nummer vergessen: Warnung", out)
        setz("quelle/010_grundlagen.py", "3.56.0", "3.56.1")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "MoveEye 3.56.1 steht noch nicht in versions.json" in out and "WARNUNG: Simulator" not in out
           and "WARNUNG: Gehäuse" not in out, "MoveEye erhöht (Sim, Gehäuse unberührt): nur der Hinweis «noch nicht signiert»", out)
        git("checkout", "-q", "--", "."); git("clean", "-qfd")

        print("--- nur Sim")
        setz("simulator3d/scripts/welt.gd", "extends Node", "extends Node3D")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Simulator geändert seit Sim 3.55.2" in out and "WARNUNG: MoveEye" not in out, "Sim geändert, Nummer vergessen: Warnung", out)
        setz("simulator3d/scripts/main.gd", '"3.55.2"', '"3.55.3"')
        setz("simulator3d/Lies mich.txt", "NEU IN 3.55.2", "NEU IN 3.55.3\nneu\n\nNEU IN 3.55.2")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "Sim 3.55.3 gesetzt, version.json hat noch 3.55.2" in out, "Sim-Nummer gesetzt, noch nicht gepackt: Warnung", out)
        linux_zip(T, "3.55.3")                                    # «Export» (Ersatz-ZIPs)
        rc, out = lauf("--sim-json", "3.55.3", "Test")
        vj = json.load(open(os.path.join(T, "simulator3d", "version.json")))
        ok(rc == 0 and vj["ver"] == "3.55.3" and vj["version"] == "3D-5.55.3" and vj["linux"]["ver"] == "3.55.3" and vj.get("mw_min") == "3.55.0",
           "--sim-json 3.55.3: Brücke 3D-5.55.3, Linux-Block, mw_min", out)
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Simulator geändert" not in out and "WARNUNG: MoveEye" not in out and "WARNUNG: Gehäuse" not in out
           and "Sim 3.55.3 steht nicht signiert in versions.json" in out, "nur Sim erhöht: ok, Hinweis «noch signieren» (MoveEye bleibt 3.56.0)", out)
        man = json.load(open(os.path.join(T, "versions.json")))
        man["sim"] = {"ver": "3.55.3", "win": {"ver": "3.55.3", "file": vj["file"], "size": vj["size"], "sha256": vj["sha256"], "sig": "x"},
                      "linux": dict(vj["linux"], sig="x")}
        schreib(T, "versions.json", json.dumps(man))
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "steht nicht signiert" not in out and "passt nicht zu version.json" not in out, "Block «sim» passt zu version.json", out)
        commit("Sim 3.55.3")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Simulator" not in out, "nach dem Commit: keine Warnung", out)
        v2 = dict(vj, version="3D-5.55.1", ver="3.55.1")
        schreib(T, "simulator3d/version.json", json.dumps(v2))
        rc, out = lauf("--pruefen")
        ok(rc == 1 and "Brücke kleiner geworden" in out and "Sim-Nummer kleiner geworden" in out, "Brücke / Sim-Nummer kleiner: Problem", out)
        git("checkout", "-q", "--", ".")
        setz("simulator3d/scripts/abgleich.gd", '"3.55.0"', '"3.57.0"')
        rc, out = lauf("--pruefen")
        ok(rc == 1 and "der Simulator braucht MoveEye ≥ 3.57.0" in out, "Sim braucht neuere MoveEye (MW_MIN): Problem", out)
        git("checkout", "-q", "--", ".")
        setz("quelle/545_simulator_updates.py", '"3.55.0"', '"3.56.0"')
        rc, out = lauf("--pruefen")
        ok(rc == 1 and "MoveEye braucht Sim ≥ 3.56.0" in out, "MoveEye braucht neueren Sim (SIM_MIN): Problem", out)
        git("checkout", "-q", "--", ".")

        print("--- nur Gehäuse")
        setz("hardware/gehaeuse/Dokumente/Montage.md", "Montage", "Montage neu")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Gehäuse geändert seit v5.3.0" in out and "WARNUNG: Simulator" not in out and "WARNUNG: MoveEye" not in out,
           "Gehäuse geändert, Nummer vergessen: Warnung", out)
        setz("hardware/gehaeuse/bau.json", '"5.3.0"', '"5.3.1"')
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Gehäuse" not in out and "Gehäuse 5.3.1" in out and "WARNUNG: Simulator" not in out,
           "nur Gehäuse erhöht: ok (MoveEye, Sim unberührt)", out)
        commit("Gehäuse 5.3.1")
        rc, out = lauf("--pruefen")
        ok(rc == 0 and "WARNUNG: Gehäuse" not in out, "nach dem Commit: keine Warnung", out)
        setz("hardware/gehaeuse/bau.json", '"5.3.1"', '"5.3"')
        rc, out = lauf("--pruefen")
        ok(rc == 0, "Gehäuse-Nummer X.Y ist erlaubt", out)
        setz("hardware/gehaeuse/bau.json", '"5.3"', '"v5.3"')
        rc, out = lauf("--pruefen")
        ok(rc == 1 and "passt nicht zum Schema" in out, "Gehäuse-Nummer «v5.3»: Problem", out)
        rc, out = lauf("--spuren")
        ok(rc == 0 and out.strip() == "MoveEye 3.56.0 · Sim 3.55.3 · Gehäuse v5.3", "--spuren: eine Zeile mit Vorsilben", out)
    finally:
        shutil.rmtree(W, ignore_errors=True)
    print("Spuren-Test " + ("OK" if not FEHLER else "FEHLER: %d" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
