#!/usr/bin/env python3
"""Rauchtest der Webseite (2.98.18, läuft auch auf GitHub im «Selbsttest»):

  1. sammelt ALLE Adressen (@app.route) aus der Flask-Tabelle (url_map) der gebauten Datei - ohne Server, ohne Kamera,
  2. startet MoveEye ohne Fenster (--headless) mit frischen Einstellungen und einem Web-Passwort,
  3. fragt jede Adresse OHNE Anmeldung ab: jede nicht öffentliche muss 401 / 403 / Umleitung antworten,
  4. fragt jede Adresse MIT Anmeldung ab (nur GET - nichts wird ausgelöst): keine darf mit 500 antworten.

  python3 werkzeuge/web_rauchtest.py                         # neuste webcam_bewegung_*.py, Port 5099
  python3 werkzeuge/web_rauchtest.py --datei X.py --port 5103 --zeigen

Die gewollt öffentlichen Adressen stehen unten in OEFFENTLICH (Gäste-Seiten mit eigenem Schlüssel, Teilen-Links, Knöpfe in
der Push-Nachricht, Übersetzungen, App-Symbole, Manifest, Service-Worker …). Wird eine neue Adresse öffentlich, muss sie
hier bewusst eingetragen werden - sonst schlägt der Test fehl.
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)

# gewollt ohne Anmeldung erreichbar (Anfang der Adresse bzw. genaue Adresse) - jede prüft ihren eigenen Schlüssel oder ist harmlos
OEFFENTLICH_ANFANG = {
    "/g/": "Gäste-Seite (Schlüssel im Link)",
    "/x/": "geteilte Aufnahme (Teilen-Link mit Schlüssel)",
    "/k/": "Kiosk / Anzeige (Schlüssel im Link)",
    "/p/": "Spielecke für Gäste (Schlüssel im Link)",
    "/na/": "Knöpfe in der Push-Nachricht (Einmal-Schlüssel)",
    "/spiele": "Spiele der Lagerfeuer-Ecke",
    "/tv/": "TV-Ansicht (Schlüssel im Link)",
    "/nt/": "Netz-Test fürs Handy (keine Daten)",
    "/info": "Info-Seite für Nachbarn (nur wenn eingeschaltet)",
    "/almanach": "Almanach (keine Daten)",
}
OEFFENTLICH_GENAU = {
    "/i18n/fr.js": "Übersetzung", "/i18n/it.js": "Übersetzung", "/i18n/rm.js": "Übersetzung",
    "/manifest.webmanifest": "App-Manifest", "/icon-192.png": "App-Symbol", "/icon-512.png": "App-Symbol",
    "/apple-touch-icon.png": "App-Symbol", "/apple-touch-icon-precomposed.png": "App-Symbol", "/favicon.ico": "App-Symbol",
    "/sw.js": "Service-Worker (Push)", "/sim/simulator.zip": "Simulator-Programm (öffentlich, ohne Geheimnisse)",
    "/static/<path:filename>": "Flask-Standard (kein Ordner)",
}
LANGSAM = ("/video", "/cam_feed", "/stream", "/mjpeg", "_feed")       # Bildströme: nur der Anfang wird gelesen
PASSWORT = "Rauchtest-" + base64.b16encode(os.urandom(6)).decode().lower()


def oeffentlich(rule):
    if rule in OEFFENTLICH_GENAU:
        return OEFFENTLICH_GENAU[rule]
    for a, why in OEFFENTLICH_ANFANG.items():
        if rule.startswith(a) or rule == a.rstrip("/"):
            return why
    return ""


def routen(datei):
    """alle Regeln der Flask-Tabelle: im eigenen Python-Prozess die Datei laden und die Seite bauen, ohne sie zu starten"""
    home = tempfile.mkdtemp(prefix="mw_routen_")
    code = r'''
import json, os, sys
ns = {"__name__": "mw_routen", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
ns["GAMESRV"]["port"] = 1                                  # no game server
ns["CFG"]["https_extra"] = False
ws = ns["WebStream"](None)
ws._serve = lambda app, ctx: None                          # build the page, do not serve it
ws.start()
out = [{"rule": r.rule, "methods": sorted(m for m in r.methods if m not in ("HEAD", "OPTIONS")), "endpoint": r.endpoint}
       for r in ws.app.url_map.iter_rules()]
print("ROUTEN " + json.dumps(out))
'''
    env = dict(os.environ, MOTIONWATCH_HOME=home)
    r = subprocess.run([sys.executable, "-c", code, datei], capture_output=True, text=True, env=env, timeout=180)
    shutil.rmtree(home, ignore_errors=True)
    for line in r.stdout.splitlines():
        if line.startswith("ROUTEN "):
            return json.loads(line[7:])
    sys.exit("Adressen nicht gefunden:\n" + (r.stdout + r.stderr)[-3000:])


def beispiel(rule):
    """eine Adresse mit Beispielwerten für die Platzhalter (<key>, <path:fn>, <int:n> …)"""
    def ers(m):
        conv = (m.group(1) or "").rstrip(":")
        return {"int": "1", "float": "1.0", "path": "rauchtest/x.txt"}.get(conv, "rauchtest0")
    return re.sub(r"<(?:([a-z]+):)?[A-Za-z_]+>", ers, rule)


def holen(url, auth=None, timeout=25):
    """(Status, Ort bei Umleitung) - Bildströme werden nach dem Anfang abgebrochen"""
    req = urllib.request.Request(url, method="GET")
    if auth:
        req.add_header("Authorization", "Basic " + base64.b64encode(("admin:" + auth).encode()).decode())

    class KeinUmleiten(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(KeinUmleiten)
    try:
        with op.open(req, timeout=timeout) as r:      # only the status line: streams / event lines never end
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "") or ""
    except Exception as e:                                   # timeout of a stream etc.
        return -1, e.__class__.__name__


def main():
    ap = argparse.ArgumentParser(description="Rauchtest aller Web-Adressen von MoveEye")
    ap.add_argument("--datei", default="", help="gebaute Datei (Standard: neuste webcam_bewegung_*.py im Repository)")
    ap.add_argument("--port", type=int, default=5099)
    ap.add_argument("--zeigen", action="store_true", help="jede Adresse mit Antwort ausgeben")
    a = ap.parse_args()
    datei = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    import socket
    with socket.socket() as sk:                              # the port is taken (another MoveEye): a free one
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); print("Port %d belegt – nehme %d" % (a.port, sk.getsockname()[1])); a.port = sk.getsockname()[1]
    rs = routen(datei)
    print("%d Adressen in %s" % (len(rs), os.path.basename(datei)))
    tmp = tempfile.mkdtemp(prefix="mw_rauch_")
    cfg = os.path.join(tmp, "mw")
    os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_auto": False, "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "motionwatch.log"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    fehler, warn = [], []
    try:
        for _i in range(240):                                    # a busy computer needs a while
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "motionwatch.log")).read()[-3000:])
            if holen(base + "/manifest.webmanifest", timeout=2)[0] == 200:
                break
            time.sleep(1)
        else:
            mlog = os.path.join(cfg, "motionwatch.log")
            sys.exit("Webseite nicht erreichbar:\n" + (open(mlog, errors="replace").read()[-3000:] if os.path.isfile(mlog) else ""))
        n_pub = n_zu = 0

        def eine(r):
            url = base + beispiel(r["rule"])
            langsam = any(x in r["rule"] for x in LANGSAM)
            t0 = time.time()
            c1, ort = holen(url, timeout=8 if langsam else 25)
            c2, ort2 = holen(url, auth=PASSWORT, timeout=8 if langsam else 25) if "GET" in r["methods"] else ("-", "")
            return r, langsam, c1, ort, c2, ort2, time.time() - t0

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(6) as ex:
            ergebnisse = list(ex.map(eine, sorted(rs, key=lambda x: x["rule"])))
        for r, langsam, c1, ort, c2, ort2, dt in ergebnisse:
            why = oeffentlich(r["rule"])
            if why:
                n_pub += 1
                if c1 >= 500 and c1 != 503:
                    fehler.append("ohne Anmeldung GET %s -> %d (öffentlich: %s)" % (r["rule"], c1, why))
            else:
                n_zu += 1
                if not (c1 in (401, 403) or 300 <= c1 < 400 and "login" in ort.lower()):
                    fehler.append("OFFEN ohne Anmeldung: %s -> %d %s (nicht in OEFFENTLICH)" % (r["rule"], c1, ort))
            if c2 != "-":
                if c2 >= 500 and c2 != 503:                   # 503 = «no camera picture yet» (on purpose, no camera here)
                    fehler.append("mit Anmeldung GET %s -> %d" % (r["rule"], c2))
                elif c2 == -1 and not langsam:
                    warn.append("mit Anmeldung GET %s: keine Antwort (%s)" % (r["rule"], ort2))
            if dt > 10 and not langsam:
                warn.append("langsam: %s (%.0f s)" % (r["rule"], dt))
            if a.zeigen:
                print("  %-48s ohne %4s  mit %4s  %5.1f s  %s" % (r["rule"], c1, c2, dt, ("öffentlich: " + why) if why else ""), flush=True)
        if p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
        print("%d geschützte Adressen, %d gewollt öffentliche" % (n_zu, n_pub))
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "motionwatch.log"), errors="replace").read()
        tb = log.count("Traceback (most recent call last)")
        if tb:
            warn.append("%d Python-Fehlermeldungen (Traceback) im Protokoll von MoveEye" % tb)
            print(log[-4000:])
        shutil.rmtree(tmp, ignore_errors=True)
    for w in warn:
        print("WARNUNG: " + w)
    for x in fehler:
        print("FEHLER: " + x)
    print("Web-Rauchtest " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
