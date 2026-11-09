#!/usr/bin/env python3
"""Test «Kamerawahl» (Teil 639zzi): kleine Bilder aller Videoquellen im Live-Bild, am echten Gerät.

Startet MoveEye ohne Fenster mit der Demo und falschen Quellen: Hauptkamera (Kopf) = Demo, eine USB-Kamera (MW_TEST_V4L,
in der Demo liefert jede Quelle das Demo-Bild), eine Netzwerk-Kamera mit Passwort in der Adresse, KEIN Weitwinkel und KEIN
Wärmebild. Prüft mit Playwright (iPhone und iPad):

  1. Kacheln: USB, Netzwerk (angeschlossen zuerst), Weitwinkel + Wärmebild grau «nicht angeschlossen» (iPad: alle 4;
     iPhone: 2 + «⋯ Kameras +2», im Menü grau). Ohne Netzwerk-Kamera hat das iPhone Platz für alle drei.
  2. Die Kacheln holen Einzelbilder /cam_thumb/<quelle> (etwa 1 / s), zu sobald die Reihe versteckt / die Seite verdeckt ist.
  3. Antippen = nur das grosse Bild wechselt (/cam_view/<quelle>, ein Strom); die Erkennung behält ihre Quelle, keine
     Einstellung ändert (cfg vor / nach gleich, source_id gleich). Kopf-Kachel = zurück auf /video_feed.
  4. Graue Kachel antippen: Hinweis, das grosse Bild bleibt.
  5. Die Adresse / das Passwort der Netzwerk-Kamera kommt nie in den Browser (Seite, /api/state, /api/cams) und nicht ins Protokoll.
  6. Verbindungen: höchstens 4 gleichzeitig, höchstens 2 lange (wie werkzeuge/bildstrom_test.py). Keine JavaScript-Fehler.

  python3 werkzeuge/kamerawahl_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos kamerawahl_*.png (iPhone + iPad)
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
sys.path.insert(0, HIER)
from bildstrom_test import verbindungen, MAX_VERB, MAX_LANG     # noqa: E402

PASSWORT = "Kamerawahl-" + base64.b16encode(os.urandom(5)).decode().lower()
GEHEIM = "NetzGeheim" + base64.b16encode(os.urandom(4)).decode().lower()
NETZ_ID = "c0ffee42"


def main():
    ap = argparse.ArgumentParser(description="Kamerawahl im Live-Bild")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5137)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (kamerawahl_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_kamerawahl_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
          "ip_sources": [{"id": NETZ_ID, "name": "Einfahrt", "url": "rtsp://admin:%s@192.0.2.7:554/stream1" % GEHEIM}],
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_TEST_V4L="4:Fake USB Cam")
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
            for gname, vp, dsf in [("iphone", {"width": 390, "height": 844}, 3), ("ipad", {"width": 820, "height": 1180}, 2)]:
                print("== %s %dx%d" % (gname, vp["width"], vp["height"]), flush=True)
                ctx = br.new_context(viewport=vp, is_mobile=True, has_touch=True, device_scale_factor=dsf,
                                     http_credentials={"username": "admin", "password": PASSWORT})
                pg = ctx.new_page()
                jsf = []
                pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                lauf(pg, a, pruef, gname)
                pruef(not jsf, "%s: keine JavaScript-Fehler %s" % (gname, jsf[:3]))
                ctx.close()
            br.close()
        if p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        log += "".join(open(x, errors="replace").read() for x in glob.glob(os.path.join(cfg, "**", "*.log"), recursive=True))
        pruef(GEHEIM not in log, "Protokoll: kein Passwort der Netzwerk-Kamera")
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Kamerawahl-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def lauf(pg, a, pruef, gname):
    KW = "() => window.mwKamWahl ? window.mwKamWahl.state() : null"
    NETZ = "url:" + NETZ_ID

    def keep(sel):
        return pg.evaluate("s => { const i = document.querySelector(s); return i && i.mwKeep ? Object.assign({w: i.naturalWidth, src: i.mwKeep.src}, i.mwKeep) : null; }", sel)

    def warte(fn, ms=12000):
        t_ = time.time() + ms / 1000.0
        v = None
        while time.time() < t_:
            v = fn()
            if v:
                return v
            pg.wait_for_timeout(200)
        return v

    def weg():
        for _ in range(3):
            pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
            pg.wait_for_timeout(300)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; }")
        pg.evaluate("() => { ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")

    def foto(name):
        if a.bilder:
            weg(); pg.wait_for_timeout(900)
            pg.screenshot(path=os.path.join(a.bilder, "kamerawahl_%s_%s.png" % (gname, name)))

    def messen(ms):
        pg.wait_for_timeout(1500)
        seit, m, lang = {}, 0, 0
        for _ in range(int(ms / 250)):
            now_ = time.time(); vs = verbindungen(a.port)
            seit = {c: seit.get(c, now_) for c in vs}
            m = max(m, len(vs)); lang = max(lang, sum(1 for c in vs if now_ - seit[c] >= 2.0))
            pg.wait_for_timeout(250)
        return m, lang

    def zustand():
        return pg.evaluate("""() => fetch('/api/state').then(r => r.json()).then(j => ({cfg: j.cfg, src: j.state.source_id,
            label: j.state.source_label}))""")

    KAM = ("source", "extra_cams", "kopf_ov", "kopf_ov_on", "thermal_source", "thermal_on", "thermal_alarm", "nightvision", "detection_on",
           "sim_on", "tk_live_view", "cam_rotate", "cam_mirror")      # pan / tilt / auto-tuner change on their own in the demo

    def unterschied(x, y):
        return sorted(k for k in KAM if x["cfg"].get(k) != y["cfg"].get(k))

    posts = []
    pg.on("request", lambda r: posts.append(r.url.split("?")[0].split("/", 3)[-1]) if r.method == "POST" else None)

    def tile(k):
        return "#kw-row .kw-t[data-k='%s']" % k

    def tippen(sel):
        weg()
        pg.locator(sel).first.click(timeout=5000)
        pg.wait_for_timeout(500)

    pg.goto(pg.url if pg.url.startswith("http") else "http://127.0.0.1:%d/" % a.port, wait_until="domcontentloaded")
    pg.evaluate("() => { try { localStorage.removeItem('mw-kamwahl'); localStorage.removeItem('mw-view3'); } catch (e) {} }")
    pg.reload(wait_until="domcontentloaded")
    v = warte(lambda: (k := keep("#video")) and k["frames"] > 0 and k["w"] > 0 and k)
    pruef(bool(v) and v["src"] == "/video_feed", "Live: Kopf-Bild kommt (%s)" % (v and v["src"]))
    weg()
    s = warte(lambda: (x := pg.evaluate(KW)) and x["on"] and len(x["tiles"]) >= 3 and x)
    want = ["usb:4", NETZ, "wide", "thermal"] if gname == "ipad" else ["usb:4", NETZ, "more"]
    pruef(bool(s) and s["list"][:3] == ["head", "wide", "thermal"] and "usb:4" in s["list"] and NETZ in s["list"],
          "Quellen: Kopf, Weitwinkel, Wärmebild, USB, Netzwerk (%s)" % (s and s["list"]))
    pruef(bool(s) and s["tiles"] == want and s["big"] == "head" and s["mini"] is None,
          "Kacheln %s, gross = Kopf (%s)" % (want, s and s["tiles"]))
    grau = pg.evaluate("""() => [...document.querySelectorAll('#kw-row .kw-t.na')].map(b => [b.dataset.k, !b.querySelector('img'),
        b.textContent.includes('nicht angeschlossen')])""")
    if gname == "ipad":
        pruef(grau == [["wide", True, True], ["thermal", True, True]], "graue Kacheln «nicht angeschlossen» für Weitwinkel und Wärmebild, ohne Bild (%s)" % grau)
    # pictures of the tiles: single pictures, about 1 per second
    m = warte(lambda: (k := keep(tile("usb:4") + " img")) and k["frames"] >= 2 and k["w"] > 0 and k)
    pruef(bool(m) and m["mode"] == "snap" and m["src"].startswith("/cam_thumb/usb") and m["w"] <= 256,
          "USB-Kachel: Einzelbilder /cam_thumb/, klein (%s)" % (m and {x: m[x] for x in ("src", "w", "frames")}))
    n = warte(lambda: (k := keep(tile(NETZ) + " img")) and k["frames"] >= 1 and k["w"] > 0 and k)
    pruef(bool(n), "Netzwerk-Kachel: Bild über MoveEye (%s)" % (n and n["src"]))
    if m:
        f0 = keep(tile("usb:4") + " img")["frames"]; pg.wait_for_timeout(3000); f1 = keep(tile("usb:4") + " img")["frames"]
        pruef(1 <= f1 - f0 <= 5, "Kachel: etwa 1 Bild pro Sekunde (%d → %d in 3 s)" % (f0, f1))
    mx, ml = messen(3000)
    pruef(mx <= MAX_VERB and ml <= MAX_LANG, "Kopf + Kacheln: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, mx, ml))
    foto("1_kacheln")
    # the network camera: never its address / password in the browser
    txt = pg.evaluate("() => Promise.all(['/api/state', '/api/cams', '/api/sources'].map(u => fetch(u).then(r => r.text()))).then(a => a.join('\\n'))")
    pruef(GEHEIM not in txt and GEHEIM not in pg.content(), "Netzwerk-Kamera: Passwort nie im Browser (Seite, /api/state, /api/cams)")
    # switching = only the view
    z0 = zustand()
    del posts[:]
    tippen(tile("usb:4"))
    v = warte(lambda: (k := keep("#video")) and k["src"] == "/cam_view/usb:4" and k["on"] and k["frames"] > 0 and k["w"] > 0 and k)
    s = pg.evaluate(KW)
    pruef(bool(v) and s["big"] == "usb:4" and "head" in s["tiles"] and "usb:4" not in s["tiles"],
          "USB antippen: gross = /cam_view/usb:4 (ein Strom), Kopf jetzt als Kachel (%s, %s)" % (v and v["src"], s["tiles"]))
    tag = pg.evaluate("() => { const x = document.getElementById('v3-tag'); return x && !x.hidden ? x.textContent : ''; }")
    pruef("Fake USB Cam" in tag, "Schild auf dem Bild: %s" % tag)
    pg.wait_for_timeout(1500)
    z1 = zustand()
    diff = unterschied(z0, z1)
    pruef(not diff and z0["src"] == z1["src"] == "demo", "Erkennung behält ihre Quelle (%s → %s), Kamera-Einstellungen gleich %s" % (z0["src"], z1["src"], diff))
    mx, ml = messen(3000)
    pruef(mx <= MAX_VERB and ml <= MAX_LANG, "USB gross + Kacheln: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, mx, ml))
    foto("2_usb_gross")
    # the network camera big (iPad: its tile; iPhone: through «⋯ Kameras»)
    if gname == "ipad":
        tippen(tile(NETZ))
    else:
        s = pg.evaluate(KW)
        pruef(s["tiles"][-1] == "more", "iPhone: «⋯ Kameras» als letzte Kachel (%s)" % s["tiles"])
        tippen("#kw-more")
        mn = pg.evaluate("""() => { const m = document.getElementById('kw-menu'); return m && !m.hidden ? [...m.querySelectorAll('button')]
            .map(b => [b.dataset.k, b.classList.contains('na'), b.classList.contains('on')]) : null; }""")
        pruef(bool(mn) and [x[0] for x in mn] == ["head", "wide", "thermal", "usb:4", NETZ] and mn[1][1] and mn[2][1] and mn[3][2],
              "⋯ Kameras: alle Quellen, Weitwinkel / Wärmebild grau, USB = gross (%s)" % mn)
        foto("3_menu")
        tippen("#kw-menu button[data-k='%s']" % NETZ)
    v = warte(lambda: (k := keep("#video")) and k["src"] == "/cam_view/" + NETZ and k["on"] and k["frames"] > 0 and k)
    pruef(bool(v), "Netzwerk-Kamera gross: /cam_view/%s (%s)" % (NETZ, v and v["src"]))
    pruef(GEHEIM not in pg.content(), "Netzwerk-Kamera gross: kein Passwort in der Seite")
    # a grey tile: hint, nothing changes
    vor = keep("#video")["src"]
    if gname == "ipad":
        tippen(tile("thermal"))
    else:
        tippen("#kw-more"); tippen("#kw-menu button[data-k='thermal']")
    msg = pg.evaluate("() => { const x = document.getElementById('toast'); return x ? x.textContent : ''; }")
    pruef("nicht angeschlossen" in msg and "Einstellungen" in msg and keep("#video")["src"] == vor,
          "graue Kachel antippen: Hinweis «%s», grosses Bild bleibt" % msg)
    foto("4_hinweis")
    # the head tile: back to the main camera
    tippen(tile("head"))
    v = warte(lambda: (k := keep("#video")) and k["src"] == "/video_feed" and k["on"] and k)
    s = pg.evaluate(KW)
    pruef(bool(v) and s["big"] == "head" and s["sel"] is None, "Kopf-Kachel: zurück auf /video_feed (%s)" % (v and v["src"]))
    z2 = zustand()
    diff = unterschied(z0, z2)
    bad = [u for u in posts if u.startswith(("api/set", "api/source", "api/cams", "api/text", "api/kopf"))]
    pruef(not diff and z2["src"] == "demo" and not bad, "nach allem: Kamera-Einstellungen gleich, Erkennung = demo, kein Einstell-Aufruf %s %s" % (diff, bad))
    # kept per device
    tippen(tile("usb:4")); pg.reload(wait_until="domcontentloaded")
    v = warte(lambda: (k := keep("#video")) and k["src"] == "/cam_view/usb:4" and k["on"] and k)
    pruef(bool(v), "neu laden: USB bleibt gross (pro Gerät)")
    weg(); tippen(tile("head"))
    # closed when not visible: row hidden, page hidden
    warte(lambda: (k := keep(tile("usb:4") + " img")) and k["on"] and k, 6000)
    pg.evaluate("() => { const r = document.getElementById('kw-row'); r.style.display = 'none'; }")
    pg.wait_for_timeout(1800)
    offen = pg.evaluate("() => [...document.querySelectorAll('#kw-row img')].filter(i => i.mwKeep && i.mwKeep.on).length")
    pruef(offen == 0, "Kacheln versteckt: alle Einzelbild-Abfragen zu (%d offen)" % offen)
    pg.evaluate("() => { document.getElementById('kw-row').style.display = ''; }")
    warte(lambda: (k := keep(tile("usb:4") + " img")) and k["on"] and k, 6000)
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); }")
    pg.wait_for_timeout(1800)
    offen = pg.evaluate("() => [...document.querySelectorAll('#kw-row img')].filter(i => i.mwKeep && i.mwKeep.on).length")
    pruef(offen == 0, "Seite verdeckt: alle Kachel-Abfragen zu (%d offen)" % offen)
    pg.evaluate("() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }")
    # the phone without the network camera: room for USB + the two grey tiles
    if gname == "iphone":
        def ohne_netz(route):
            try:
                r = route.fetch()
                j = r.json()
                j["state"]["extra"][0]["kw"] = [x for x in j["state"]["extra"][0]["kw"] if not x["k"].startswith("url:")]
                route.fulfill(response=r, body=json.dumps(j), headers=dict(r.headers, **{"content-type": "application/json"}))
            except Exception:
                try:
                    route.continue_()
                except Exception:
                    pass
        pg.route(re.compile(r".*/api/state(\?.*)?$"), ohne_netz)
        s = warte(lambda: (x := pg.evaluate(KW)) and x["tiles"] == ["usb:4", "wide", "thermal"] and x, 8000)
        pruef(bool(s), "iPhone ohne Netzwerk-Kamera: USB + Weitwinkel / Wärmebild grau, kein «⋯» (%s)" % (s and s["tiles"]))
        foto("5_grau")
        pg.unroute_all(behavior="ignoreErrors")


if __name__ == "__main__":
    sys.exit(main())
