#!/usr/bin/env python3
"""Drei Spuren: MoveEye nimmt einen Simulator, dessen Prüfsumme NUR im signierten Block «sim» von versions.json steht.

Ohne Netz und ohne den echten Schlüssel (ein TEST-Schlüssel entsteht hier; nur in diesem Lauf ersetzt er den öffentlichen
Schlüssel im geladenen Programm). Ablauf in einem Arbeitsordner:
  1. Sim mit neuer Nummer (eingebettet + 1): Windows-ZIP und Linux-Paket (Lies mich, installieren.sh, ausführbar), dazu
     simulator3d/version.json über versionen.py --sim-json (Brücke «3D-…», «mw_min», Block «linux»).
  2. Programmdatei --make-manifest mit dem Test-Schlüssel: versions.json bekommt «sim» mit zwei Signaturen.
  3. Programm laden, Downloads aus dem Arbeitsordner (urlopen ersetzt): /sim holt Windows und Linux mit den Werten aus
     «sim» (nicht mit den eingebetteten), gespeicherter Block wird beim Neustart wieder geprüft.
  4. Abgelehnt: verändertes ZIP, Block ohne Signatur, verfälschte Signatur, anderer Schlüssel (echter öffentlicher Schlüssel),
     verfälschte gespeicherte Datei, ältere Nummer.

    python3 werkzeuge/sim_manifest_test.py [--datei webcam_bewegung_X_Y_Z.py]     # Ende: «Sim-Manifest-Test OK» (Exit 0)
"""
import argparse
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEHLER = []


def ok(bed, was):
    print(("  ok: " if bed else "  FEHLER: ") + was)
    if not bed:
        FEHLER.append(was)


def warte(dl, s=20.0):
    t0 = time.time()
    while dl["running"] and time.time() - t0 < s:
        time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    app = re.search(r'^APP_VERSION = "([^"]+)"', open(os.path.join(R, "quelle", "010_grundlagen.py"), encoding="utf-8").read(), re.M).group(1)
    prog = a.datei or os.path.join(R, "webcam_bewegung_%s.py" % app.replace(".", "_"))
    if not os.path.isfile(prog):
        sys.exit("fehlt: %s (zuerst werkzeuge/bauen.py)" % prog)
    if "def sim_manifest_take" not in open(prog, encoding="utf-8").read():
        sys.exit("%s kennt den Block «sim» noch nicht (vor den drei Spuren gebaut) - zuerst bauen" % os.path.basename(prog))
    W = tempfile.mkdtemp(prefix="sim_manifest_test_")
    try:
        T = os.path.join(W, "quelle_dl")                 # what the update source (GitHub) would serve
        os.makedirs(os.path.join(T, "simulator3d", "scripts"))
        shutil.copy(prog, T)
        zd = re.search(r'^ZD_FILE = "([^"]+)"', open(prog, encoding="utf-8").read(), re.M)
        if zd and os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(prog)), zd.group(1))):
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(prog)), zd.group(1)), T)
        shutil.copy(os.path.join(R, "simulator3d", "scripts", "abgleich.gd"), os.path.join(T, "simulator3d", "scripts"))
        emb = re.search(r'^SIM3D = \{"version": "([0-9.]+)"', open(prog, encoding="utf-8").read(), re.M).group(1)
        x, y, z = (int(v) for v in emb.split("."))
        nv = "%d.%d.%d" % (x, y, z + 1)
        print("--- 1. Sim %s (eingebettet: %s) packen" % (nv, emb))
        with open(os.path.join(T, "simulator3d", "MotionWatch3D_Simulator.zip"), "wb") as f:
            f.write(b"PK-test-windows-" + os.urandom(3000))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("MoveEyeSim3D/Lies mich.txt", "MoveEye Sim\n\nNEU IN %s\nTest.\n" % nv)
            zf.writestr("MoveEyeSim3D/installieren.sh", "#!/bin/sh\n")
            zi = zipfile.ZipInfo("MoveEyeSim3D/MoveEyeSim3D.x86_64"); zi.external_attr = 0o755 << 16
            zf.writestr(zi, b"\x7fELF-test" + os.urandom(2000))
        with open(os.path.join(T, "simulator3d", "MoveEyeSim3D_Linux.zip"), "wb") as f:
            f.write(buf.getvalue())
        env = dict(os.environ, MW_VERSIONEN_REPO=T)
        r = subprocess.run([sys.executable, os.path.join(R, "werkzeuge", "versionen.py"), "--sim-json", nv, "Test"], env=env,
                           capture_output=True, text=True)
        vj = json.load(open(os.path.join(T, "simulator3d", "version.json"), encoding="utf-8"))
        ok(r.returncode == 0 and vj.get("ver") == nv and vj.get("version") == "3D-%d.%d.%d" % (x + 2, y, z + 1)
           and isinstance(vj.get("linux"), dict) and vj.get("mw_min"), "version.json: ver, Brücke, mw_min, Block linux (%s)" % r.stdout.strip()[-80:])

        print("--- 2. versions.json mit Test-Schlüssel signieren")
        seed = hashlib.sha256(os.urandom(32)).digest()
        key = os.path.join(W, "test_schluessel.txt")
        with open(key, "w") as f:
            f.write(seed.hex())
        r = subprocess.run([sys.executable, os.path.join(T, os.path.basename(prog)), "--make-manifest", T, "--sign-key", key],
                           capture_output=True, text=True, cwd=W)
        os.remove(key)
        man = json.load(open(os.path.join(T, "versions.json"), encoding="utf-8"))
        sim = man.get("sim") or {}
        ok(r.returncode == 0 and sim.get("ver") == nv and (sim.get("win") or {}).get("sig") and (sim.get("linux") or {}).get("sig"),
           "Block «sim» %s mit Signaturen für Windows und Linux (%s)" % (sim.get("ver"), (r.stdout.strip().splitlines() or [""])[-1][-60:]))
        ok(not any(e.get("file", "").startswith("simulator3d/") for e in man.get("versions") or []),
           "«versions» unverändert (alte Geräte sehen keinen Simulator als MoveEye-Version)")

        print("--- 3. MoveEye holt den Simulator mit den Werten aus «sim»")
        os.environ["MOTIONWATCH_HOME"] = os.path.join(W, "daten")
        sys.argv = [prog]
        spec = importlib.util.spec_from_file_location("mw_sim_manifest_test", os.path.join(T, os.path.basename(prog)))
        mw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mw)
        real_pub = mw.UPDATE_PUBKEY
        if not mw._ED:
            mw._ED.extend(mw._ed25519_impl())
        test_pub = mw._ED[0](seed).hex()
        ok(test_pub != real_pub, "Test-Schlüssel ist nicht der echte")
        serve = {"dir": T}

        class Antwort(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *e):
                self.close()

        def urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            m = re.match(r"^https://test\.invalid/main/([^?]+)", url)
            if not m:
                raise OSError("kein Netz im Test: " + url)
            p = os.path.join(serve["dir"], m.group(1))
            if not os.path.isfile(p):
                raise OSError("404 " + m.group(1))
            with open(p, "rb") as f:
                return Antwort(f.read())
        mw.urllib.request.urlopen = urlopen
        mw.CFG["update_url"] = "https://test.invalid/main/versions.json"

        def frisch(pub):
            for k in ("SIM3D", "SIM3D_LINUX"):
                getattr(mw, k).update(getattr(mw, k + "_EMBED"))
            mw.SIMMAN.update(t=0.0, loaded=False, src="embedded")
            for d in (mw.SIM3D_DL, mw.SIM3D_LINUX_DL):
                d.update(running=False, got=0, msg="")
            mw.UPDATE_PUBKEY = pub
        frisch(test_pub)
        ok(not mw.sim3d_ready(), "vorher: kein Simulator im Zwischenspeicher")
        mw.sim3d_fetch(); warte(mw.SIM3D_DL)
        ok(mw.sim3d_ready() and mw.SIM3D["version"] == nv and mw.SIM3D["sha256"] == vj["sha256"],
           "Windows: Sim %s geholt, Prüfsumme aus «sim» (%s)" % (mw.SIM3D["version"], mw.SIM3D_DL["msg"] or "ohne Fehler"))
        mw.sim3d_fetch(mw.SIM3D_LINUX, mw.SIM3D_LINUX_DL); warte(mw.SIM3D_LINUX_DL)
        ok(mw.sim3d_ready(mw.SIM3D_LINUX) and mw.SIM3D_LINUX["version"] == nv,
           "Linux: Sim %s geholt (%s)" % (mw.SIM3D_LINUX["version"], mw.SIM3D_LINUX_DL["msg"] or "ohne Fehler"))
        gesp = os.path.join(os.environ["MOTIONWATCH_HOME"], "sim3d", mw.SIMMAN_FILE)
        ok(os.path.isfile(gesp), "geprüfter Block gespeichert (%s)" % mw.SIMMAN_FILE)
        frisch(test_pub)                                 # «Neustart»: ohne Netz gilt der gespeicherte, wieder geprüfte Block
        serve["dir"] = os.path.join(W, "leer")
        ok(mw.sim3d_ready() and mw.SIM3D["version"] == nv, "nach dem Neustart: gespeicherter Block wieder geprüft und genommen")
        d = json.load(open(gesp)); d["win"]["sha256"] = "0" * 64; json.dump(d, open(gesp, "w"))
        frisch(test_pub)
        ok(not mw.sim3d_ready() and mw.SIM3D["version"] == emb, "gespeicherter Block verfälscht: nicht genommen")
        os.remove(gesp)
        for p in glob.glob(os.path.join(os.environ["MOTIONWATCH_HOME"], "sim3d", "*.zip")):
            os.remove(p)

        frisch(test_pub)
        sb, stxt = mw.sim_manifest_check(T, man)
        ok(not sb and "win+linux" in stxt.replace("linux+win", "win+linux"), "Selbsttest-Prüfung des Blocks «sim» (%s)" % stxt.strip(", "))
        zp = os.path.join(T, "simulator3d", "MoveEyeSim3D_Linux.zip"); orig = open(zp, "rb").read()
        open(zp, "wb").write(orig[:-1] + bytes([orig[-1] ^ 1]))
        sb, _t = mw.sim_manifest_check(T, man)
        ok(sb == ["simulator linux " + nv], "Selbsttest-Prüfung: verändertes Linux-Paket gemeldet (%s)" % sb)
        open(zp, "wb").write(orig)
        sb, _t = mw.sim_manifest_check(T, dict(man, sim=dict(sim, ver="9.9.9")))
        ok(any("sign again" in x for x in sb), "Selbsttest-Prüfung: versions.json «sim» ≠ version.json gemeldet")
        mw.UPDATE_PUBKEY = real_pub
        sb, _t = mw.sim_manifest_check(T, man)
        ok(len(sb) == 2, "Selbsttest-Prüfung mit dem echten Schlüssel: Test-Signaturen abgelehnt (%s)" % sb)

        print("--- 4. Abgelehnt")
        serve["dir"] = T

        def versuch(was, aendern, pub=test_pub, zip_kaputt=False, erwartet="checksum"):
            for p in glob.glob(os.path.join(os.environ["MOTIONWATCH_HOME"], "sim3d", "*")):
                os.remove(p)                             # each attempt like a new device (no cache, no stored block)
            Q = os.path.join(W, "q_" + str(len(FEHLER)) + "_" + re.sub(r"\W", "", was)[:20])
            shutil.copytree(T, Q)
            m = json.load(open(os.path.join(Q, "versions.json")))
            aendern(m)
            json.dump(m, open(os.path.join(Q, "versions.json"), "w"))
            if zip_kaputt:
                zp = os.path.join(Q, "simulator3d", "MotionWatch3D_Simulator.zip")
                b = bytearray(open(zp, "rb").read()); b[-10] ^= 255; open(zp, "wb").write(bytes(b))
            serve["dir"] = Q
            frisch(pub)
            mw.sim3d_fetch(); warte(mw.SIM3D_DL)
            msg = mw.SIM3D_DL["msg"]
            ok(not mw.sim3d_ready() and erwartet in msg and not glob.glob(os.path.join(os.environ["MOTIONWATCH_HOME"], "sim3d", "*.zip")),
               "%s: abgelehnt (%s)" % (was, msg[:70]))
            shutil.rmtree(Q)
        versuch("ZIP verändert (1 Byte)", lambda m: None, zip_kaputt=True)
        versuch("Block ohne Signatur", lambda m: m["sim"]["win"].pop("sig"))
        versuch("Signatur verfälscht", lambda m: m["sim"]["win"].update(sig=("0" if m["sim"]["win"]["sig"][0] != "0" else "1") + m["sim"]["win"]["sig"][1:]))
        versuch("Prüfsumme im Block geändert", lambda m: m["sim"]["win"].update(sha256=hashlib.sha256(b"x").hexdigest()))
        versuch("Nummer im Block geändert", lambda m: m["sim"]["win"].update(ver="%d.%d.%d" % (x, y, z + 5)))
        versuch("anderer Schlüssel (echter öffentlicher Schlüssel)", lambda m: None, pub=real_pub)
        versuch("Block «sim» weggelassen", lambda m: m.pop("sim"))
        frisch(test_pub)
        if z > 0:
            o = "%d.%d.%d" % (x, y, z - 1)
            fn = sim["win"]["file"]; sh = sim["win"]["sha256"]
            alt = {"ver": o, "win": dict(sim["win"], ver=o, sig=mw._ED[1](seed, mw._sig_msg(o, fn, sh)).hex())}
            ok(not mw.sim_manifest_take(alt, save=False) and mw.SIM3D["version"] == emb, "ältere Nummer (%s, richtig signiert) abgelehnt" % o)
        mw.UPDATE_PUBKEY = real_pub
    finally:
        shutil.rmtree(W, ignore_errors=True)
    print("Sim-Manifest-Test " + ("OK" if not FEHLER else "FEHLER: %d" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
