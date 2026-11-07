#!/usr/bin/env python3
"""Test «Drei Kamera-Ansichten» (Teil 639zv) im Browser.

Startet MoveEye ohne Fenster mit der Demo (Hauptkamera Demo, eine Zusatzkamera «usb:0» = die Übersicht «Übersicht lenkt
den Kopf», eine Wärmebildquelle «usb:1» – in der Demo ist jede Quelle das Demo-Bild) und prüft mit Playwright:

  1. «Ansicht» auf dem Bild schaltet 🎯 Kopf → 🌡 Wärmebild (thermal_on auf dem Gerät) → 🔭 Weitwinkel (/cam_feed/1, Rahmen
     «wohin der Kopf schaut») → 🎯 Kopf; das grosse Bild bleibt EIN Strom.
  2. Lang drücken = Menü mit drei Ansichten + «Kleines Übersichtsbild»; Wahl im Menü wirkt.
  3. Bild im Bild: Einzelbilder (/cam_snap/1, ~2 / s), antippen tauscht gross / klein, aus im Menü = zu, pro Gerät gemerkt.
  4. Verbindungen: höchstens 4 gleichzeitig, höchstens 2 lange (wie werkzeuge/bildstrom_test.py).
  5. Fehlende Kameras werden übersprungen (Antwort von /api/state ohne Wärmebildquelle / ohne Weitwinkel) und im Menü grau.
  6. Controller-Ansicht: das kleine Bild kommt mit, «⇅ Tauschen» tauscht ohne Simulator die Ansichten.
  7. Keine JavaScript-Fehler.

  python3 werkzeuge/ansichten_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos ansicht_*.png (iPhone + iPad)
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
from bildstrom_test import verbindungen, MAX_VERB, MAX_LANG     # noqa: E402  (the same counting of the connections)

PASSWORT = "Ansicht-" + base64.b16encode(os.urandom(5)).decode().lower()


def main():
    ap = argparse.ArgumentParser(description="Drei Kamera-Ansichten im Browser")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5133)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (ansicht_*.png)")
    a = ap.parse_args()
    datei = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_ansicht_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": ["usb:0"], "kopf_ov": "usb:0", "thermal_source": "usb:1", "thermal_on": False,
          "cam_fov": {"usb:0": {"model": "own", "deg": 102}},
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
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
            geraete = [("iphone", {"width": 390, "height": 844}, 3), ("ipad", {"width": 820, "height": 1180}, 2)]
            for gname, vp, dsf in geraete:
                print("== %s %dx%d" % (gname, vp["width"], vp["height"]), flush=True)
                ctx = br.new_context(viewport=vp, is_mobile=True, has_touch=True, device_scale_factor=dsf,
                                     http_credentials={"username": "admin", "password": PASSWORT})
                pg = ctx.new_page()
                jsf = []
                pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                lauf(pg, a, base, pruef, gname, gname == "iphone")
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
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Ansichten-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def lauf(pg, a, base, pruef, gname, voll):
    V3 = "() => window.mwView3 ? window.mwView3.state() : null"

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

    def cfg_th():
        return pg.evaluate("() => fetch('/api/state').then(r => r.json()).then(j => !!j.cfg.thermal_on)")

    def weg():
        for _ in range(3):
            pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
            pg.wait_for_timeout(300)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; }")
        # the coach-mark tour of the page (516, #g2-ov over everything) can start a little later: end it like Esc / «Fertig»
        pg.evaluate("() => { ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")

    def foto(name):
        if a.bilder:
            weg(); pg.wait_for_timeout(700)
            pg.screenshot(path=os.path.join(a.bilder, "ansicht_%s_%s.png" % (gname, name)))

    def messen(ms):
        pg.wait_for_timeout(1500)
        seit, m, lang = {}, 0, 0
        for _ in range(int(ms / 250)):
            now_ = time.time(); vs = verbindungen(a.port)
            seit = {c: seit.get(c, now_) for c in vs}
            m = max(m, len(vs)); lang = max(lang, sum(1 for c in vs if now_ - seit[c] >= 2.0))
            pg.wait_for_timeout(250)
        return m, lang

    def lang_druecken(sel):
        weg()                                             # the tour (#g2-ov) may come between two steps
        for _ in range(3):                                # cards above the picture (e.g. 639zy / 639zz) can push it down while
            b0 = pg.locator(sel).first.bounding_box()     # pressing: wait until the button stands still, retry if no menu
            for _ in range(10):
                pg.wait_for_timeout(300)
                b = pg.locator(sel).first.bounding_box()
                if b == b0:
                    break
                b0 = b
            pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(800); pg.mouse.up()
            pg.wait_for_timeout(300)
            if pg.evaluate("() => { const m = document.getElementById('v3-menu'); return !!(m && !m.hidden); }"):
                break
            print("  Hinweis: lang drücken ohne Menü (Knopf verschoben?), nochmals")
            weg()

    pg.goto(base + "/", wait_until="domcontentloaded")
    pg.evaluate("() => { try { localStorage.removeItem('mw-view3'); } catch (e) {} }")
    pg.reload(wait_until="domcontentloaded")
    v = warte(lambda: (k := keep("#video")) and k["frames"] > 0 and k["w"] > 0 and k)
    pruef(bool(v), "Live: Bild kommt (%s)" % v)
    weg()
    s = warte(lambda: (x := pg.evaluate(V3)) and len(x["order"]) == 3 and x)
    pruef(bool(s) and s["order"] == ["head", "thermal", "wide"] and s["cur"] == "head", "drei Ansichten verfügbar, Start = Kopf (%s)" % s)
    pruef(pg.evaluate("() => { const b = document.getElementById('lv-b-cam'); return !!(b && b.offsetParent && b.textContent === '🎯'); }"),
          "Knopf «Ansicht» auf dem Bild zeigt 🎯")
    # PiP (head view): single pictures of the overview
    m = warte(lambda: (k := keep("#v3-mimg")) and k["frames"] >= 2 and k)
    pruef(bool(m) and m["mode"] == "snap" and "/cam_snap/1" in m["src"] and m["w"] > 0, "Bild im Bild: Übersicht als Einzelbilder (%s)" % m)
    if m:
        f0 = m["frames"]; pg.wait_for_timeout(2000); f1 = keep("#v3-mimg")["frames"]
        pruef(f1 - f0 >= 2, "Bild im Bild: etwa 2 Bilder pro Sekunde (%d → %d in 2 s)" % (f0, f1))
    mx, ml = messen(3000)
    pruef(mx <= MAX_VERB and ml <= MAX_LANG, "Kopf + Bild im Bild: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, mx, ml))
    foto("1_kopf")
    # 1. cycle
    pg.evaluate("() => fetch('/api/move', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({dir: 'center'})})")
    weg()
    pg.click("#lv-b-cam"); pg.wait_for_timeout(400)
    s = pg.evaluate(V3); th = warte(cfg_th, 6000)
    pruef(s["cur"] == "thermal" and th, "1× Ansicht: Wärmebild, thermal_on auf dem Gerät (%s, %s)" % (s["cur"], th))
    pg.wait_for_timeout(1500); foto("2_waermebild")
    pg.click("#lv-b-cam"); pg.wait_for_timeout(400)
    s = pg.evaluate(V3)
    v = warte(lambda: (k := keep("#video")) and "/cam_feed/1" in k["src"] and k["on"] and k["w"] > 0 and k)
    pruef(s["cur"] == "wide" and bool(v), "2× Ansicht: Weitwinkel, grosses Bild = /cam_feed/1 (%s)" % v)
    fr = warte(lambda: pg.evaluate("() => { const o = document.querySelector('#vcard .vwrap > .v3ov'); const f = (((QSJ || {}).state || {}).extra || [{}])[0].view3; return o && !o.hidden && o.offsetWidth > 0 && f && f.frame; }"), 8000)
    pruef(bool(fr) and abs(fr["x"] - 0.5) < 0.25 and 0.5 < fr["w"] < 0.8, "Weitwinkel: Rahmen «wohin der Kopf schaut» sichtbar, Kopf Mitte, 66° von 102° (%s)" % fr)
    m = warte(lambda: (k := keep("#v3-mimg")) and "/cam_snap/0" in k["src"] and k["frames"] >= 1 and k, 8000)
    pruef(bool(m), "Weitwinkel: klein der Kopf (/cam_snap/0) (%s)" % m)
    mx, ml = messen(3000)
    pruef(mx <= MAX_VERB and ml <= MAX_LANG, "Weitwinkel + Bild im Bild: höchstens %d Verbindungen, %d lange (gemessen %d, %d)" % (MAX_VERB, MAX_LANG, mx, ml))
    foto("3_weitwinkel")
    pg.click("#lv-b-cam"); pg.wait_for_timeout(400)
    s = pg.evaluate(V3); th = warte(lambda: not cfg_th(), 6000)
    v = warte(lambda: (k := keep("#video")) and k["src"] == "/video_feed" and k["on"] and k)
    pruef(s["cur"] == "head" and bool(th) and bool(v), "3× Ansicht: wieder Kopf, Wärmebild aus, /video_feed (%s)" % s["cur"])
    # 2. long press = menu
    lang_druecken("#lv-b-cam")
    mn = pg.evaluate("() => { const m = document.getElementById('v3-menu'); return m && !m.hidden ? [...m.querySelectorAll('button')].map(b => [b.dataset.v, b.disabled, b.classList.contains('on')]) : null; }")
    pruef(bool(mn) and [x[0] for x in mn] == ["head", "thermal", "wide", "pip"] and not any(x[1] for x in mn) and mn[0][2],
          "lang drücken: Menü mit Kopf, Wärmebild, Weitwinkel, kleines Bild (%s)" % mn)
    pruef(pg.evaluate(V3)["cur"] == "head", "lang drücken schaltet nicht weiter")
    foto("4_menu")
    pg.click("#v3-menu button[data-v='wide']"); pg.wait_for_timeout(500)
    pruef(pg.evaluate(V3)["cur"] == "wide" and pg.evaluate("() => document.getElementById('v3-menu').hidden"), "Menü: Weitwinkel gewählt, Menü zu")
    # 3. swap with the small picture
    pg.wait_for_timeout(800)
    pg.click("#v3-mini"); pg.wait_for_timeout(500)
    s = pg.evaluate(V3)
    pruef(s["cur"] == "head", "kleines Bild antippen: Kopf gross (%s)" % s["cur"])
    m = warte(lambda: (k := keep("#v3-mimg")) and "/cam_snap/1" in k["src"] and k)
    pruef(bool(m), "… und die Übersicht klein (%s)" % m)
    pg.click("#v3-mini"); pg.wait_for_timeout(500)
    pruef(pg.evaluate(V3)["cur"] == "wide", "nochmals antippen: Weitwinkel gross")
    pg.click("#v3-mini"); pg.wait_for_timeout(500)
    # PiP off in the menu -> closed, kept per device
    lang_druecken("#lv-b-cam"); pg.click("#v3-menu button[data-v='pip']"); pg.wait_for_timeout(1500)
    k = keep("#v3-mimg")
    pruef(pg.evaluate("() => document.getElementById('v3-mini').hidden") and k and not k["on"], "kleines Bild aus: versteckt und zu (%s)" % k)
    pg.keyboard.press("Escape")
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
    s = pg.evaluate(V3)
    pruef(s and s["pip"] is False and pg.evaluate("() => document.getElementById('v3-mini').hidden"), "neu laden: kleines Bild bleibt aus (pro Gerät) (%s)" % s)
    lang_druecken("#lv-b-cam"); pg.click("#v3-menu button[data-v='pip']"); pg.wait_for_timeout(300); pg.keyboard.press("Escape")
    pruef(pg.evaluate(V3)["pip"] is True, "kleines Bild wieder ein")
    # 6. controller view: the small picture moves along, «Swap» without the simulator
    if pg.evaluate("() => typeof window.pvOpen === 'function'"):
        pg.evaluate("() => window.pvOpen(true)"); pg.wait_for_timeout(1500)
        inpv = warte(lambda: pg.evaluate("() => { const m = document.getElementById('v3-mini'); return !!(m && m.closest('#pv-live') && !m.hidden); }"), 5000)
        pruef(bool(inpv), "Controller-Ansicht: kleines Bild im Live-Bild")
        has = pg.evaluate("() => !!document.querySelector('#pv button.pvb[data-id=\"view\"]')")
        pruef(has, "Controller-Ansicht: Knopf «Ansicht» in der Leiste")
        c0 = pg.evaluate(V3)["cur"]
        pg.evaluate("() => { const b = document.querySelector('#pv button.pvb[data-id=\"swap\"]'); if (b) b.click(); }"); pg.wait_for_timeout(600)
        c1 = pg.evaluate(V3)["cur"]
        pruef(c0 != c1 and "wide" in (c0, c1), "Controller-Ansicht: «⇅ Tauschen» tauscht die Ansichten (%s → %s)" % (c0, c1))
        foto("5_controller")
        pg.evaluate("() => window.pvOpen(false)"); pg.wait_for_timeout(800)
        pruef(pg.evaluate("() => { const m = document.getElementById('v3-mini'); return !!(m && m.closest('#vcard')); }"), "Controller-Ansicht zu: kleines Bild wieder auf der Live-Seite")
    # 5. skip what is missing: /api/state without thermal source and without wide camera
    def ohne(route):
        try:
            r = route.fetch()
        except Exception:
            return
        try:
            j = r.json()
            j["cfg"]["thermal_source"] = ""
            if pg.evaluate("() => window.__ohneWeit === 1"):
                j["state"]["extra"][0]["view3"]["wide"] = None
            route.fulfill(response=r, body=json.dumps(j), headers=dict(r.headers, **{"content-type": "application/json"}))
        except Exception:
            try:
                route.fulfill(response=r)
            except Exception:
                pass
    pg.route(re.compile(r".*/api/state(\?.*)?$"), ohne)
    pg.evaluate("() => window.mwView3.set('head', true)")
    s = warte(lambda: (x := pg.evaluate(V3)) and x["order"] == ["head", "wide"] and x, 8000)
    pruef(bool(s), "ohne Wärmebildquelle: Kopf → Weitwinkel (Wärmebild übersprungen) (%s)" % s)
    pg.click("#lv-b-cam"); pg.wait_for_timeout(300)
    pruef(pg.evaluate(V3)["cur"] == "wide", "ohne Wärmebild: 1× Ansicht = Weitwinkel")
    lang_druecken("#lv-b-cam")
    dis = pg.evaluate("() => [...document.querySelectorAll('#v3-menu button')].map(b => [b.dataset.v, b.disabled])")
    pruef(dict(dis).get("thermal") is True and dict(dis).get("wide") is False, "Menü: Wärmebild grau (%s)" % dis)
    pg.keyboard.press("Escape")
    pg.evaluate("() => { window.__ohneWeit = 1; }")
    s = warte(lambda: (x := pg.evaluate(V3)) and x["order"] == ["head"] and x, 8000)
    pruef(bool(s) and s["cur"] == "head", "ohne Weitwinkel: nur Kopf, zurück auf Kopf (%s)" % s)
    pg.wait_for_timeout(1200)
    st_ = pg.evaluate("() => ({cam: !!document.getElementById('lv-b-cam') && document.getElementById('lv-b-cam').hidden, mini: document.getElementById('v3-mini').hidden, qs: (document.getElementById('qs-view') || {}).disabled})")
    pruef(st_["cam"] and st_["mini"] and st_["qs"] is not False, "nur eine Ansicht: Knopf und kleines Bild weg (%s)" % st_)
    k = keep("#video")
    pruef(k and k["src"] == "/video_feed", "ohne Weitwinkel: grosses Bild /video_feed")
    pg.unroute_all(behavior="ignoreErrors")


if __name__ == "__main__":
    sys.exit(main())
