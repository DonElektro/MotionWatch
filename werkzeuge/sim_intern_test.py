#!/usr/bin/env python3
"""Test «Simulator intern» (MoveEye Teil 639zx) mit einem gefälschten Pi-Paket - ohne echten Simulator, ohne Pi.

Lädt die gebaute MoveEye-Datei (ohne sie zu starten), ersetzt SIM3D_PI durch ein kleines Paket aus einem Testordner
(file://, derselbe Weg wie das Holen von GitHub) und prüft:
  1. holen + Prüfsumme: falsche SHA-256 -> abgelehnt, nichts ausgepackt; richtige -> geholt
  2. auspacken: nur MoveEyeSim3D/…, Programmdatei ausführbar, geprueft.json; ein Paket mit «../» wird abgelehnt
  3. veränderte Programmdatei -> wird vor dem Start aus der geprüften ZIP neu ausgepackt
  4. starten: der «Simulator» (ein kleines Python-Skript, antwortet auf /info) läuft mit nice, Lite-Optionen und --port,
     MoveEye zeigt auf http://127.0.0.1:<port>, «selbst finden» aus, Simulation ein; die vorherige Verbindung ist gemerkt
  5. beenden: Prozess weg, Adresse / selbst finden / Simulation wieder wie vorher (hier: ein «HP» mit Simulation aus)
  6. Fenster geschlossen (Prozess beendet sich selbst) -> der Wächter stellt die Verbindung zurück
  7. Wächter-Grenzen (zu wenig Speicher / zu heiss) und die Web-Adresse /api/simintern (GET, POST stop, Rolle)

  python3 werkzeuge/sim_intern_test.py [--datei webcam_bewegung_X_Y_Z.py]
Ende: «Simulator-intern-Test OK» (Exit 0) oder die Fehler (Exit 1).
"""
import argparse
import glob
import hashlib
import json
import os
import runpy
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAKE_SIM = r'''#!/usr/bin/env python3
# gefälschter MoveEye Sim für werkzeuge/sim_intern_test.py: antwortet auf /info, schreibt seine Befehlszeile
import http.server, json, os, sys
a = sys.argv
port = int(a[a.index("--port") + 1]) if "--port" in a else 8765
open(os.path.join(os.environ.get("XDG_DATA_HOME", "/tmp"), "fake_args.json"), "w").write(json.dumps(
    {"argv": a, "nice": os.nice(0), "env": {k: os.environ.get(k, "") for k in ("DISPLAY", "XDG_DATA_HOME", "HOME")}}))
if os.path.exists(os.path.join(os.environ.get("XDG_DATA_HOME", "/tmp"), "fake_quit")):
    sys.exit(0)                     # «Fenster geschlossen»
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        b = json.dumps({"name": "MoveEye Sim 9.9.9 (Test)", "version": "9.9.9", "cameras": []}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *x):
        pass
http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()
'''


def make_zip(path, evil=False):
    with zipfile.ZipFile(path, "w") as z:
        i = zipfile.ZipInfo("MoveEyeSim3D/MoveEyeSim3D.arm64"); i.external_attr = 0o100755 << 16
        z.writestr(i, FAKE_SIM)
        z.writestr("MoveEyeSim3D/Lies mich.txt", "NEU IN 9.9.9\nTest\n")
        z.writestr("MoveEyeSim3D/installieren.sh", "#!/bin/bash\n")
        if evil:
            z.writestr("MoveEyeSim3D/../../boese.txt", "x")
    data = open(path, "rb").read()
    return len(data), hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    mw = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")), key=os.path.getmtime)[-1]
    tmp = tempfile.mkdtemp(prefix="simintern_test_")
    os.environ["MW_SIMPI_TEST"] = "1"                      # kein Pi nötig, im Container auch als root
    os.environ["DISPLAY"] = ":0"                           # «Desktop» (der falsche Simulator braucht keinen)
    os.environ["MOTIONWATCH_HOME"] = os.path.join(tmp, "daten")
    g = runpy.run_path(mw, run_name="sim_intern_test")
    g = g["simpi_start"].__globals__                       # run_path gibt eine Kopie zurück - die Funktionen lesen dieses
    g["set_data_dir"](os.path.join(tmp, "daten"))
    fails = []

    def ok(cond, text):
        print(("✓ " if cond else "✗ ") + text)
        if not cond:
            fails.append(text)

    saved = []
    g["save_settings"] = lambda *x, **k: saved.append(1)  # die echte Einstellungsdatei nie anfassen
    for fn in ("sim_set",):                                 # die Simulation ein / aus nur merken (keine Kamera, kein Profil)
        def fake_sim_set(on, who="web", confirm=False, _g=g):
            _g["CFG"]["sim_on"] = bool(on); return True, ""
        g[fn] = fake_sim_set
    CFG, SIM3D_PI, SIMPI = g["CFG"], g["SIM3D_PI"], g["SIMPI"]
    CFG.update(update_url="", sim_url="http://192.168.1.60:8765", sim_on=False, sim_auto=True, armed=False)
    src = os.path.join(tmp, "quelle"); os.makedirs(os.path.join(src, "simulator3d"))
    zpath = os.path.join(src, "simulator3d", "MoveEyeSim3D_Pi.zip")
    size, sha = make_zip(zpath)
    g["SIM3D_BASE"] = "file://" + src + "/"
    g["_simpi_check_real"] = g["simpi_check"]
    g["simpi_check"] = lambda res=None: ("", [])            # die echten Grenzen weiter unten einzeln
    try:
        # 1. falsche Prüfsumme
        SIM3D_PI.update(version="9.9.9", size=size, sha256="0" * 64)
        r = g["simpi_start"]("test")
        ok(r[0], "Start angenommen (Paket wird geholt)")
        t0 = time.time()
        while SIMPI["want"] and time.time() - t0 < 20:
            time.sleep(0.2)
        ok(not g["simpi_running"]() and "checksum" in SIMPI["msg"], "falsche Prüfsumme abgelehnt: " + SIMPI["msg"])
        ok(not os.path.exists(g["simpi_inst_dir"]()) and not g["sim3d_ready"](SIM3D_PI), "nichts ausgepackt, nichts behalten")
        ok(CFG["sim_url"] == "http://192.168.1.60:8765" and not CFG["sim_on"], "Verbindung unverändert")
        # 2. Paket mit «../» wird nicht ausgepackt
        evil = os.path.join(tmp, "evil.zip"); es, eh = make_zip(evil, evil=True)
        os.makedirs(os.path.dirname(g["sim3d_path"](SIM3D_PI)), exist_ok=True)
        shutil.copy(evil, g["sim3d_path"](SIM3D_PI)); SIM3D_PI.update(size=es, sha256=eh)
        exe, err = g["simpi_install"]()
        ok(not exe and "bad file name" in err and not os.path.exists(os.path.join(tmp, "daten", "boese.txt")), "Paket mit ../ abgelehnt: " + err)
        os.remove(g["sim3d_path"](SIM3D_PI))
        # 3. richtiges Paket - so wie es auf dem Pi ankommt: signiert in versions.json «sim.pi» (Test-Schlüssel), Release-Asset
        if not g["_ED"]:
            g["_ED"].extend(g["_ed25519_impl"]())
        seed = hashlib.sha256(os.urandom(32)).digest()
        real_pub = g["UPDATE_PUBKEY"]; g["UPDATE_PUBKEY"] = g["_ED"][0](seed).hex()
        fn = "simulator3d/MoveEyeSim3D_Pi.zip"
        url = "https://github.com/DonElektro/MotionWatch/releases/download/sim-9.9.9/MoveEyeSim3D_Pi.zip"
        sig = lambda v, h: g["_ED"][1](seed, g["_sig_msg"](v, fn, h)).hex()
        good = {"ver": "9.9.9", "file": fn, "size": size, "sha256": sha, "sig": sig("9.9.9", sha), "url": url}
        SIM3D_PI.update(version="3.56.0", size=0, sha256="", url="")
        ok(not g["sim_manifest_take"]({"ver": "9.9.9", "pi": dict(good, url="https://example.com/MoveEyeSim3D_Pi.zip")}) and not SIM3D_PI["size"],
           "«sim.pi» mit fremder Adresse abgelehnt")
        ok(not g["sim_manifest_take"]({"ver": "9.9.9", "pi": dict(good, sha256="1" * 64)}) and not SIM3D_PI["size"], "«sim.pi» mit falscher Signatur abgelehnt")
        ok(not g["sim_manifest_take"]({"ver": "3.0.0", "pi": dict(good, ver="3.0.0", sig=sig("3.0.0", sha))}), "«sim.pi» älter als eingebettet abgelehnt")
        ok(g["sim_manifest_take"]({"ver": "9.9.9", "pi": good}) == ["pi"] and SIM3D_PI["size"] == size and SIM3D_PI["url"] == url,
           "«sim.pi» signiert angenommen: Grösse, Prüfsumme, Release-Adresse")
        ok(json.load(open(os.path.join(g["simpi_dir"](), "sim_manifest.json"))).get("pi", {}).get("url") == url, "gespeichert (sim_manifest.json)")
        g["SIMMAN"]["t"] = time.time()                       # nicht nochmals versions.json holen
        real_open = g["urllib"].request.urlopen

        def fake_open(req, timeout=None):                     # das Release-Asset kommt aus dem Testordner
            u = req.full_url if hasattr(req, "full_url") else str(req)
            if u == url:
                return open(zpath, "rb")
            return real_open(req, timeout=timeout)
        g["urllib"].request.urlopen = fake_open
        # make_manifest: «sim.pi» aus simulator3d/version.json + lokaler ZIP, signiert, mit url
        mf = os.path.join(tmp, "mf"); os.makedirs(os.path.join(mf, "simulator3d"))
        shutil.copy(zpath, os.path.join(mf, fn))
        wz = os.path.join(mf, "simulator3d", "MoveEyeSim3D_Linux.zip"); ls_, lh_ = make_zip(wz)
        json.dump({"ver": "9.9.9", "version": "3D-11.9.9", "file": "simulator3d/MoveEyeSim3D_Linux.zip", "size": 1, "sha256": "x",
                   "linux": {"file": "simulator3d/MoveEyeSim3D_Linux.zip", "ver": "9.9.9", "size": ls_, "sha256": lh_},
                   "pi": {"file": fn, "ver": "9.9.9", "size": size, "sha256": sha, "url": url}},
                  open(os.path.join(mf, "simulator3d", "version.json"), "w"))
        blk = g["sim_manifest_block"](mf, seed) or {}
        ok((blk.get("pi") or {}).get("url") == url and (blk.get("pi") or {}).get("sig") == good["sig"] and "linux" in blk,
           "make_manifest: «sim.pi» mit Signatur und Release-Adresse")
        os.remove(os.path.join(mf, fn))                      # im Repository liegt die Pi-ZIP nicht: nur die Signatur zählt
        ok(not g["sim_manifest_check"](mf, {"sim": blk})[0] or all("pi" not in b for b in g["sim_manifest_check"](mf, {"sim": blk})[0]),
           "Selbsttest: Pi-ZIP fehlt im Repository = ok (Release-Asset)")
        SIMPI["msg"] = ""
        r = g["simpi_start"]("test")
        t0 = time.time()
        while (SIMPI["want"] or not g["simpi_running"]()) and time.time() - t0 < 20:
            time.sleep(0.2)
        st = g["simpi_state"]()
        ok(st["on"] and st["port"] in (8765, 8775, 8785), "läuft (Port %s, Meldung %r)" % (st["port"], SIMPI["msg"]))
        exe = os.path.join(g["simpi_inst_dir"](), "MoveEyeSim3D", "MoveEyeSim3D.arm64")
        ok(os.access(exe, os.X_OK) and os.path.isfile(os.path.join(g["simpi_inst_dir"](), "geprueft.json")), "ausgepackt, ausführbar, geprueft.json")
        ok(CFG["sim_url"] == "http://127.0.0.1:%d" % st["port"] and CFG["sim_on"] and not CFG["sim_auto"],
           "MoveEye zeigt auf localhost, Simulation ein, selbst finden aus")
        ok(st["prev"] == {"url": "http://192.168.1.60:8765", "on": False}, "vorherige Verbindung gemerkt: %s" % st["prev"])
        info = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/info" % st["port"], timeout=1) as f:
                    info = json.loads(f.read()); break
            except OSError:
                time.sleep(0.2)
        ok(bool(info) and "Test" in info.get("name", ""), "der «Simulator» antwortet auf /info")
        fa = json.load(open(os.path.join(g["simpi_dir"](), "intern_daten", "fake_args.json")))
        av = fa["argv"]
        ok(fa["nice"] >= g["SIMPI_NICE"] or not shutil.which("nice"), "nice %s (MoveEye geht vor)" % fa["nice"])
        ok(all(x in av for x in ("--no-update", "--grafik", "lite", "--stream", "--moveeye-intern")) and "--" in av, "Lite-Optionen: " + " ".join(av[1:]))
        ok(fa["env"]["XDG_DATA_HOME"].endswith("intern_daten"), "eigener Daten-Ordner")
        # 4. beenden -> zurück
        g["simpi_stop"]("test")
        time.sleep(0.5)
        ok(not g["simpi_running"](), "beendet")
        ok(CFG["sim_url"] == "http://192.168.1.60:8765" and not CFG["sim_on"] and CFG["sim_auto"], "zurück zum «HP», Simulation aus, selbst finden ein")
        ok(not os.path.exists(g["simpi_state_file"]()), "intern.json weg")
        # 5. veränderte Programmdatei -> neu ausgepackt
        with open(exe, "a") as f:
            f.write("\n# verändert\n")
        exe2, err = g["simpi_install"]()
        ok(exe2 == exe and "verändert" not in open(exe).read(), "veränderte Programmdatei neu aus der geprüften ZIP")
        # 6. Simulation war ein (HP) -> nach dem Beenden wieder ein; Fenster geschlossen -> Wächter stellt zurück
        CFG.update(sim_on=True, sim_url="http://192.168.1.60:8765", sim_auto=True)
        quit_flag = os.path.join(g["simpi_dir"](), "intern_daten", "fake_quit")
        open(quit_flag, "w").close()                        # der «Simulator» beendet sich gleich wieder
        g["simpi_start"]("test")
        t0 = time.time()
        while SIMPI["want"] and time.time() - t0 < 20:
            time.sleep(0.2)
        os.remove(quit_flag)
        t0 = time.time()
        while os.path.exists(g["simpi_state_file"]()) and time.time() - t0 < 25:
            time.sleep(0.5)
        ok(not os.path.exists(g["simpi_state_file"]()) and CFG["sim_url"] == "http://192.168.1.60:8765" and CFG["sim_on"],
           "Fenster zu: der Wächter stellt zurück (HP, Simulation bleibt ein): %s" % SIMPI["msg"])
        # 7. Grenzen
        chk = g["_simpi_check_real"]
        ok(chk({"ram_free": 500, "ram_total": 4000, "temp": 50, "load": 0.2, "disk_free": 5000})[0].startswith("too little free memory"), "zu wenig Speicher: nicht starten")
        ok(chk({"ram_free": 3000, "ram_total": 4000, "temp": 82, "load": 0.2, "disk_free": 5000})[0].startswith("the Pi is too hot"), "zu heiss: nicht starten")
        b, w = chk({"ram_free": 1200, "ram_total": 4000, "temp": 72, "load": 0.95, "disk_free": 5000})
        ok(b == "" and len(w) == 3, "knapp: starten mit 3 Hinweisen %s" % w)
        ok(g["tr_err"]("the Pi is too hot (82 °C) - let it cool down first", "de") == "der Pi ist zu heiss (82 °C) – zuerst abkühlen lassen", "Übersetzung mit Zahl")
        g["CFG"]["armed"] = True; g["CFG"]["sim_on"] = False
        r = g["simpi_start"]("test")
        ok(not r[0] and r[2] == "armed", "scharf: erst nach Bestätigung")
        g["CFG"]["armed"] = False
        # 8. Web-Adresse
        try:
            from flask import Flask, g as fg
            app = Flask("t")
            role = {"r": "admin"}

            @app.before_request
            def _r():
                fg.role = role["r"]
            from flask import jsonify, request as rq
            g["simpi_routes"](app, lambda o, c=200: (jsonify(o), c), lambda: rq.get_json(force=True, silent=True) or {})
            c = app.test_client()
            rr = c.get("/api/simintern?lang=de")
            j = rr.get_json() or {}
            if not j:
                print(rr.status_code, rr.data[:300])
            ok(j.get("ok") and "possible" in j and "res" in j, "GET /api/simintern")
            ok(c.post("/api/simintern", json={"action": "stop"}).get_json().get("ok"), "POST stop")
            ok(c.post("/api/simintern", json={"action": "x"}).status_code == 400, "unbekannte Aktion 400")
            role["r"] = "guest"
            ok(c.get("/api/simintern").status_code == 403, "nur der Besitzer (Rolle admin)")
        except ImportError:
            print("(Flask fehlt - Web-Adresse nicht geprüft)")
    finally:
        if "real_pub" in locals():
            g["UPDATE_PUBKEY"] = real_pub
        try:
            g["simpi_stop"]("test-ende")
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print("Simulator-intern-Test: %d Fehler" % len(fails))
        return 1
    print("Simulator-intern-Test OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
