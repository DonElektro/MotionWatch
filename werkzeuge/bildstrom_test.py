#!/usr/bin/env python3
"""Test der Kamerabilder im Browser (3.55.2, Fehler «Bilder oft schwarz – noch kein Bild» am iPhone / iPad).

Startet MoveEye ohne Fenster mit der Demo-Kamera (Hauptkamera + eine Zusatzkamera, beide Demo) und prüft mit Playwright
(Chromium, Handy 390 × 844):

  1. Live → Einstellungen → Kameras → zurück zu Live: zählt die offenen Verbindungen zum Server (TCP, alle 0.25 s, nach
     dem Laden) – höchstens 4 gleichzeitig, höchstens 2 lange offene (Safari erlaubt pro Gerät rund 6). Unter Einstellungen ist der versteckte Live-Strom zu,
     unter Kameras kommen Einzelbilder (keine Dauer-Ströme), zurück auf Live kommt das Bild wieder.
  2. Seite im Hintergrund (visibilitychange) und verdecktes Bild (data-hold, wie die Sim-Ansicht): der Strom ist zu.
  3. Hängender Strom (das erste Bild kommt nie – wie eine wartende Verbindung): nach 5 s verbindet das Bild neu, ohne Neuladen.
  4. Stehende Bildquelle (Demo-Kamera angehalten über MW_TEST_HOLD): das Bild verbindet still neu und läuft danach weiter.
  5. ↻ (Neu laden) bleibt im Reiter (Einstellungen), springt nicht mehr zu Live.

  python3 werkzeuge/bildstrom_test.py                        # neuste webcam_bewegung_*.py
  python3 werkzeuge/bildstrom_test.py --datei X.py --bilder ORDNER   # dazu Bildschirmfotos bildfix_*.png
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Bildtest-" + base64.b16encode(os.urandom(5)).decode().lower()
MAX_VERB = 4                                 # Safari: rund 6 pro Gerät - deutlich darunter bleiben (nach dem Laden der Seite)
MAX_LANG = 2                                 # lange offene Verbindungen (Bildstrom, Meldungen): höchstens 2


def verbindungen(port):
    """die offenen TCP-Verbindungen zum Server (ESTABLISHED, Server-Seite, IPv4 und IPv6): Menge der Gegenstellen"""
    out = set()
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            zeilen = open(f).read().splitlines()[1:]
        except OSError:
            continue
        for z in zeilen:
            t = z.split()
            if len(t) > 3 and t[3] == "01" and int(t[1].rsplit(":", 1)[1], 16) == port:
                out.add(t[2])
    return out


def main():
    ap = argparse.ArgumentParser(description="Kamerabilder im Browser: Verbindungen, Selbstheilung, Neu laden")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5131)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (bildfix_*.png)")
    a = ap.parse_args()
    datei = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_bild_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    halt = os.path.join(tmp, "halt")
    st = {"source": "demo", "extra_cams": ["usb:0"], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de",
          "desktop_notice": False, "setup_done": True, "https_extra": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_TEST_HOLD=halt)
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = "http://127.0.0.1:%d" % a.port
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": PASSWORT})
            pg = ctx.new_page()
            jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            feeds = []
            pg.on("request", lambda r: feeds.append(r.url) if "/video_feed" in r.url else None)

            def k(sel):
                return pg.evaluate("s => { const i = document.querySelector(s); return i && i.mwKeep ? Object.assign({w: i.naturalWidth}, i.mwKeep) : null; }", sel)

            def warte(sel, bed, ms=12000):
                t_ = time.time() + ms / 1000.0
                while time.time() < t_:
                    v = k(sel)
                    if v and bed(v):
                        return v
                    pg.wait_for_timeout(200)
                return k(sel)

            def messen(ms, ruhe=2500):
                """(höchstens gleichzeitig, davon lange offen >= 2 s) - nach dem Laden der Seite (ruhe ms)"""
                pg.wait_for_timeout(ruhe)
                seit, m, lang = {}, 0, 0
                for _ in range(int(ms / 250)):
                    now_ = time.time(); vs = verbindungen(a.port)
                    seit = {c: seit.get(c, now_) for c in vs}
                    m = max(m, len(vs)); lang = max(lang, sum(1 for c in vs if now_ - seit[c] >= 2.0))
                    pg.wait_for_timeout(250)
                return m, lang

            def weg():                              # news window / tips / tour: away for the pictures
                for _ in range(3):
                    pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
                    pg.wait_for_timeout(300)

            def foto(name):
                if a.bilder:
                    weg(); pg.wait_for_timeout(600)
                    pg.screenshot(path=os.path.join(a.bilder, "bildfix_%s.png" % name))

            print("1. Live → Einstellungen → Kameras → Live", flush=True)
            pg.goto(base + "/", wait_until="domcontentloaded")
            v = warte("#video", lambda v: v["frames"] > 0 and v["w"] > 0)
            pruef(bool(v and v["frames"] > 0), "Live: Bild kommt (%s)" % v)
            m, ml = messen(3000); pruef(m <= MAX_VERB and ml <= MAX_LANG, "Live: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, m, ml))
            foto("live")
            pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
            v = k("#video"); pruef(bool(v) and not v["on"], "Einstellungen: versteckter Live-Strom ist zu (%s)" % v)
            m, ml = messen(3000); pruef(m <= MAX_VERB and ml <= MAX_LANG, "Einstellungen: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, m, ml))
            pg.goto(base + "/cams", wait_until="domcontentloaded")
            pg.wait_for_timeout(1500)
            ts = []
            for _ in range(40):
                ts = pg.evaluate("() => [...document.querySelectorAll('#grid .tile img')].map(i => i.mwKeep ? Object.assign({w: i.naturalWidth}, i.mwKeep) : null)")
                if len(ts) >= 2 and all(t and t["frames"] >= 2 for t in ts):
                    break
                pg.wait_for_timeout(250)
            pruef(len(ts) >= 2 and all(t and t["mode"] == "snap" and t["frames"] >= 2 and t["w"] > 0 for t in ts),
                  "Kameras: beide Vorschauen zeigen Einzelbilder (%s)" % ts)
            m, ml = messen(6000); pruef(m <= MAX_VERB and ml <= MAX_LANG, "Kameras: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, m, ml))
            n0 = pg.evaluate("() => [...document.querySelectorAll('#grid .tile img')].map(i => i.mwKeep.frames)")
            pg.wait_for_timeout(2000)
            n1 = pg.evaluate("() => [...document.querySelectorAll('#grid .tile img')].map(i => i.mwKeep.frames)")
            pruef(all(b - a_ >= 2 for a_, b in zip(n0, n1)), "Kameras: etwa 2 Bilder pro Sekunde (%s → %s in 2 s)" % (n0, n1))
            foto("kameras")
            pg.go_back(wait_until="domcontentloaded")
            pg.goto(base + "/", wait_until="domcontentloaded")
            v = warte("#video", lambda v: v["frames"] > 0 and v["w"] > 0)
            pruef(bool(v and v["frames"] > 0), "zurück auf Live: Bild kommt wieder (%s)" % v)

            print("2. Hintergrund und verdeckt", flush=True)
            pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); }")
            pg.wait_for_timeout(1500)
            v = k("#video"); m, ml = messen(3000, 0)
            pruef(bool(v) and not v["on"] and ml == 0, "Seite im Hintergrund: Strom zu (%s, %d lange Verbindungen)" % (v, ml))
            pg.evaluate("() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }")
            f0 = (k("#video") or {}).get("conns", 0)
            v = warte("#video", lambda v: v["on"] and v["conns"] > f0 and v["frames"] > 0)
            pruef(bool(v and v["on"]), "wieder sichtbar: Strom wieder offen (%s)" % v)
            pg.evaluate("() => { document.getElementById('video').dataset.hold = '1'; }")
            pg.wait_for_timeout(1500); v = k("#video")
            pruef(bool(v) and not v["on"], "verdeckt (data-hold, Sim-Ansicht): Strom zu (%s)" % v)
            pg.evaluate("() => { delete document.getElementById('video').dataset.hold; }")
            v = warte("#video", lambda v: v["on"])
            pruef(bool(v and v["on"]), "nicht mehr verdeckt: Strom wieder offen")

            print("3. Hängender Strom (erstes Bild kommt nie)", flush=True)
            pg.evaluate("() => { window.__mwNav = 1; }")
            gehalten = []

            def route(rt):
                if not gehalten:
                    gehalten.append(rt)             # never answered: like a connection that waits behind others
                else:
                    rt.continue_()
            pg.route(re.compile(r".*/video_feed\?.*"), route)
            pg.evaluate("() => document.getElementById('video').mwRestart()")
            t0 = time.time()
            v = warte("#video", lambda v: len(gehalten) > 0 and v["stalls"] >= 1 and v["frames"] > 0 and v["w"] > 0 and not v["lost"], 20000)
            dt = time.time() - t0
            pruef(bool(v and v["stalls"] >= 1 and v["w"] > 0) and len(gehalten) == 1 and 4.5 <= dt <= 12,
                  "hängender Strom: nach %.1f s selbst neu verbunden, Bild da (%s)" % (dt, v))
            for rt in gehalten:
                try:
                    rt.abort()
                except Exception:
                    pass
            pg.unroute(re.compile(r".*/video_feed\?.*"))

            print("4. Bildquelle angehalten", flush=True)
            v0 = k("#video")
            open(halt, "w").close()
            v = warte("#video", lambda v: v["stalls"] > v0["stalls"], 15000)
            pruef(bool(v) and v["stalls"] > v0["stalls"], "stehendes Bild: still neu verbunden (%s)" % v)
            os.remove(halt)
            fr = v["frames"]
            v = warte("#video", lambda v: v["frames"] >= fr + 3 and not v["lost"], 15000)
            nav = pg.evaluate("() => window.__mwNav === 1")
            pruef(bool(v and v["frames"] >= fr + 3) and nav, "Bildquelle läuft wieder: Bild läuft weiter, ohne Neuladen (%s)" % v)

            print("5. ↻ bleibt im Reiter", flush=True)
            pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
            weg()
            with pg.expect_navigation(timeout=20000):
                pg.evaluate("() => document.getElementById('btn-reload').click()")      # (a tip may lie above it)
            pg.wait_for_timeout(500)
            pruef(pg.evaluate("() => location.pathname") == "/settings", "↻ unter Einstellungen: bleibt unter Einstellungen (%s)" % pg.url)
            if a.bilder:
                pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(2000); foto("einstellungen")
            pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
            br.close()
        if p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
    finally:
        try:
            os.remove(halt)
        except OSError:
            pass
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
    print("Bildstrom-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
