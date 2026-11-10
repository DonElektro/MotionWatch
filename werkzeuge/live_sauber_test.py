#!/usr/bin/env python3
"""Test «Live-Bild sauber» (Teil 639zzj): Knöpfe und Kamera-Kacheln auf dem Live-Bild erst nach einem Tipp, 4 s.

Startet MoveEye ohne Fenster mit der Demo wie werkzeuge/kamerawahl_test.py (eine USB-Kamera über MW_TEST_V4L, eine
Netzwerk-Kamera, kein Weitwinkel / Wärmebild = Kacheln wie auf dem Bildschirmfoto des Besitzers) und prüft mit Playwright
(iPhone 13 mit Touch, PC mit Maus):

  1. Start: Knöpfe (#lv-tools) und Kacheln (#kw-row) unsichtbar und ohne Berührung, «LIVE» sichtbar; versteckte Kacheln holen
     keine Bilder (data-hold).
  2. Tipp genau auf die Stelle des versteckten Vollbild-Knopfs: zeigt nur (kein Vollbild); der zweite Tipp dort wirkt.
  3. Gezeigt 4 s; ein Tipp auf eine Kachel nach 3 s startet die 4 s neu; nach 5 s Ruhe weg (weich).
  4. «⋯ Kameras» offen bzw. «🔍 Untersuchen» offen: bleiben sichtbar; der Tipp ins Bild beim Untersuchen wählt den Bereich.
  5. Vollbild: ✕ oben rechts erst nach einem Tipp. Kachel-Name «USB-Kamera: …» auf Deutsch.
  6. PC: Maus über dem Bild zeigt sie, 4 s nach der letzten Bewegung weg; Tab auf einen Knopf zeigt sie.
  7. Schalter «Knöpfe im Live-Bild immer zeigen» (Einstellungen → Web-Stream, pro Browser): an = immer sichtbar wie bisher.
  8. Keine JavaScript-Fehler.

  python3 werkzeuge/live_sauber_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos live_sauber_*.png
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
PASSWORT = "Sauber-" + base64.b16encode(os.urandom(5)).decode().lower()


def main():
    ap = argparse.ArgumentParser(description="Live-Bild sauber")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5139)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (live_sauber_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_livesauber_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
          "ip_sources": [{"id": "c0ffee43", "name": "Einfahrt", "url": "rtsp://192.0.2.7:554/stream1"}],
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "ui_simple": False, "tours_auto": False}
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
            cred = {"username": "admin", "password": PASSWORT}
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            ctx = br.new_context(**dev, http_credentials=cred)
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            handy(pg, base, a, pruef)
            pruef(not jsf, "iPhone: keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close()
            ctx = br.new_context(viewport={"width": 1280, "height": 800}, http_credentials=cred)
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pc(pg, base, a, pruef)
            pruef(not jsf, "PC: keine JavaScript-Fehler %s" % jsf[:3])
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
    print("Live-Bild-sauber-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


ST = "() => window.mwLiveKnoepfe ? window.mwLiveKnoepfe.state() : null"
SICHT = """() => { const o = s => { const e = document.querySelector(s); if (!e || !e.getClientRects().length) return null; const c = getComputedStyle(e);
  return {op: +c.opacity, pe: c.pointerEvents}; };
  return {tools: o('#lv-tools'), row: o('#kw-row'), tile: o('#kw-row .kw-t'), live: o('.vtag'), exit: o('#vo-exit'),
    hold: [...document.querySelectorAll('#kw-row img')].map(i => i.dataset.hold === '1'),
    keep: [...document.querySelectorAll('#kw-row img')].filter(i => i.mwKeep && i.mwKeep.on).length}; }"""


def helfer(pg, a, name_pre):
    def warte(fn, ms=12000):
        t_ = time.time() + ms / 1000.0
        v = None
        while time.time() < t_:
            v = fn()
            if v:
                return v
            pg.wait_for_timeout(150)
        return v

    def weg():
        pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); document.querySelectorAll('.nws').forEach(e => e.remove()); }")

    def foto(name):
        if a.bilder:
            pg.screenshot(path=os.path.join(a.bilder, "live_sauber_%s_%s.png" % (name_pre, name)))
    return warte, weg, foto


def mitte(pg, sel):
    r = pg.evaluate("s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2, b.width]; }", sel)
    return r


def laden(pg, base, warte, weg, immer=False):
    pg.goto(base + "/", wait_until="domcontentloaded")
    pg.evaluate("i => { try { ['mw-kamwahl', 'mw-view3', 'mw-lv-knoepfe'].forEach(k => localStorage.removeItem(k)); if (i) localStorage.setItem('mw-lv-knoepfe', '1'); } catch (e) {} }", immer)
    pg.evaluate("() => fetch('/api/news', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({seen: true})})")
    pg.reload(wait_until="domcontentloaded")
    warte(lambda: pg.evaluate("() => { const v = document.getElementById('video'); return !!(v && v.naturalWidth > 0 && window.mwKamWahl && mwKamWahl.state().on && mwKamWahl.state().tiles.length >= 3); }"), 30000)
    weg(); pg.wait_for_timeout(400); weg()


def handy(pg, base, a, pruef):
    warte, weg, foto = helfer(pg, a, "iphone")
    laden(pg, base, warte, weg)
    pg.evaluate("() => scrollTo(0, 0)")
    pg.wait_for_timeout(1200)
    s, v = pg.evaluate(ST), pg.evaluate(SICHT)
    pruef(bool(s) and s["auto"] and not s["shown"], "Start: sauber (%s)" % s)
    pruef(v["tools"] and v["tools"]["op"] == 0 and v["tools"]["pe"] == "none" and v["row"] and v["row"]["op"] == 0 and v["tile"]["pe"] == "none",
          "Start: Knöpfe und Kacheln unsichtbar, keine Berührung (%s)" % {k: v[k] for k in ("tools", "row", "tile")})
    pruef(v["live"] and v["live"]["op"] == 1, "«LIVE» bleibt sichtbar (%s)" % v["live"])
    pg.wait_for_timeout(1500)
    v = pg.evaluate(SICHT)
    pruef(v["hold"] and all(v["hold"]) and v["keep"] == 0, "versteckte Kacheln holen keine Bilder (hold %s, offen %d)" % (v["hold"], v["keep"]))
    foto("1_vorher")
    # the first tap exactly where the hidden «full screen» button is: only shows
    fs = mitte(pg, "#lv-b-fs")
    pg.touchscreen.tap(fs[0], fs[1]); pg.wait_for_timeout(450)
    s, v = pg.evaluate(ST), pg.evaluate(SICHT)
    vo = pg.evaluate("() => document.body.classList.contains('videoonly')")
    pruef(s["shown"] and not vo and v["tools"]["op"] == 1 and v["tools"]["pe"] != "none", "Tipp auf den versteckten Vollbild-Knopf: zeigt nur, kein Vollbild (%s, Vollbild %s)" % (s, vo))
    pg.wait_for_timeout(1300)
    v = pg.evaluate(SICHT)
    pruef(not any(v["hold"]) and v["keep"] >= 1, "gezeigt: Kacheln holen wieder Bilder (%s, offen %d)" % (v["hold"], v["keep"]))
    foto("2_nach_tippen")
    # shown 4 s; a tile at 3 s starts them again
    pg.wait_for_timeout(1300)                              # ~3 s after the tap
    t = mitte(pg, "#kw-row .kw-t[data-k='usb:4']")
    pg.touchscreen.tap(t[0], t[1])
    big = warte(lambda: (pg.evaluate(KWS) or {}).get("big") == "usb:4", 4000)
    pruef(bool(big), "Kachel antippen (gezeigt): wirkt (USB gross)")
    pg.wait_for_timeout(3000)
    s = pg.evaluate(ST)
    pruef(s["shown"], "3 s nach dem Tipp auf die Kachel (6 s nach dem Bild): noch sichtbar (%s)" % s)
    pg.wait_for_timeout(1800)
    s, v = pg.evaluate(ST), pg.evaluate(SICHT)
    pruef(not s["shown"] and v["tools"]["op"] < 0.5, "danach weich weg (%s, opacity %s)" % (s, v["tools"]["op"]))
    pg.wait_for_timeout(1000)
    foto("3_nach_5s")
    v = pg.evaluate(SICHT)
    pruef(v["tools"]["op"] == 0 and v["live"]["op"] == 1, "5 s Ruhe: Knöpfe weg, «LIVE» da")
    # the German name of the USB camera (the label on the picture while it is big)
    tag = pg.evaluate("() => { const x = document.getElementById('v3-tag'); return x && !x.hidden ? x.textContent : ''; }")
    pruef("USB-Kamera: Fake USB Cam" in tag and "USB camera" not in tag, "Name der USB-Kamera auf Deutsch: %s" % tag)
    # back to the head
    vc = mitte(pg, "#video"); pg.touchscreen.tap(vc[0], vc[1]); pg.wait_for_timeout(400)
    t = mitte(pg, "#kw-row .kw-t[data-k='head']"); pg.touchscreen.tap(t[0], t[1])
    pruef(bool(warte(lambda: (pg.evaluate(KWS) or {}).get("big") == "head", 4000)), "Kopf-Kachel: zurück auf den Kopf")
    nm = pg.evaluate("() => [...document.querySelectorAll('#kw-row .kw-t')].map(b => b.textContent).join(' | ')")
    pruef("USB-Kamera: Fake USB Cam" in nm and "USB camera" not in nm, "Kachel-Name auf Deutsch: %s" % nm)
    # «⋯ Kameras» open: they stay
    m = mitte(pg, "#kw-more"); pg.touchscreen.tap(m[0], m[1]); pg.wait_for_timeout(400)
    pruef(pg.evaluate("() => !document.getElementById('kw-menu').hidden"), "⋯ Kameras: Liste offen")
    pg.wait_for_timeout(5000)
    s = pg.evaluate(ST)
    pruef(s["shown"] and s["pinned"] == "kw-menu", "Liste offen: bleibt nach 5 s sichtbar (%s)" % s)
    pg.touchscreen.tap(vc[0], vc[1] + 40); pg.wait_for_timeout(300)
    pruef(pg.evaluate("() => document.getElementById('kw-menu').hidden"), "Tipp daneben: Liste zu")
    pg.wait_for_timeout(4400)
    s = pg.evaluate(ST)
    pruef(not s["shown"], "Liste zu: 4 s später weg (%s)" % s)
    # «🔍 Untersuchen»: stays while choosing, the tap in the picture chooses the region
    pg.touchscreen.tap(vc[0], vc[1]); pg.wait_for_timeout(400)
    u = mitte(pg, "#lv-b-unt"); pg.touchscreen.tap(u[0], u[1])
    sel = warte(lambda: pg.evaluate("() => { const o = document.getElementById('unt-ov'); return !!(o && o.classList.contains('sel')); }"), 8000)
    pruef(bool(sel), "Untersuchen: Bereich wählen offen")
    pg.wait_for_timeout(5000)
    s = pg.evaluate(ST)
    pruef(s["shown"] and s["pinned"] == "unt-bar", "Untersuchen offen: Knöpfe bleiben (%s)" % s)
    vc = mitte(pg, "#video"); pg.touchscreen.tap(vc[0], vc[1]); pg.wait_for_timeout(500)
    box = pg.evaluate("() => !!document.querySelector('#unt-ov .ub.region')")
    pruef(box, "Untersuchen: der Tipp ins Bild wählt den Bereich (nicht nur zeigen)")
    foto("4_untersuchen")
    pg.evaluate("() => window.mwUntersuchen && mwUntersuchen.close()"); pg.wait_for_timeout(4600)
    pruef(not pg.evaluate(ST)["shown"], "Untersuchen zu: 4 s später weg")
    # full screen: ✕ only after a tap
    pg.evaluate("() => setVideoOnly(true)"); pg.wait_for_timeout(5000)
    v = pg.evaluate(SICHT)
    pruef(v["exit"] and v["exit"]["op"] == 0, "Vollbild: ✕ zuerst versteckt (%s)" % v["exit"])
    foto("5_vollbild_sauber")
    vc = mitte(pg, "#video"); pg.touchscreen.tap(vc[0], vc[1]); pg.wait_for_timeout(450)
    v = pg.evaluate(SICHT)
    pruef(v["exit"] and v["exit"]["op"] == 1 and v["row"]["op"] == 1, "Vollbild: Tipp zeigt ✕ und Kacheln (%s)" % v["exit"])
    foto("6_vollbild_tipp")
    ex = mitte(pg, "#vo-exit"); pg.touchscreen.tap(ex[0], ex[1]); pg.wait_for_timeout(500)
    pruef(not pg.evaluate("() => document.body.classList.contains('videoonly')"), "Vollbild: ✕ beendet es")
    # the switch in the settings (Expert: Network & access → Web stream)
    pg.goto(base + "/settings", wait_until="domcontentloaded")
    cb = warte(lambda: pg.evaluate("() => !!document.getElementById('lvk-cb')"), 20000)
    pruef(bool(cb), "Einstellungen → Web-Stream: Schalter «Knöpfe im Live-Bild immer zeigen» da")
    if cb:
        weg()
        info = pg.evaluate("""() => { const r = document.getElementById('lvk-row'), s = r.closest('[data-view]');
            return {txt: r.textContent, sec: s && s.dataset.view, on: document.getElementById('lvk-cb').checked}; }""")
        pruef("Knöpfe im Live-Bild immer zeigen" in info["txt"] and info["sec"] == "sec:Web stream" and not info["on"],
              "Schalter: Text DE, im Abschnitt Web-Stream, Standard aus (%s)" % info)
        pg.wait_for_timeout(3000)                          # «Meine Ansicht» (639r) folds the page first
        for _ in range(3):
            if pg.evaluate("() => !!document.getElementById('lvk-row').offsetParent && document.getElementById('lvk-row').getClientRects().length > 0 && !!document.getElementById('lvk-row').closest('details[open]') && !document.getElementById('lvk-row').closest('details:not([open])')"):
                break
            pg.evaluate("() => { const r = document.getElementById('lvk-row'); const ds = []; let d = r.closest('details'); while (d) { ds.unshift(d); d = d.parentElement && d.parentElement.closest('details'); } ds.forEach(x => { if (!x.open) x.querySelector(':scope > summary').click(); }); }")
            pg.wait_for_timeout(600)
        pg.evaluate("() => document.getElementById('lvk-row').scrollIntoView({block: 'center'})")
        pg.wait_for_timeout(300)
        pg.click("#lvk-row")
        pg.wait_for_timeout(400)
        foto("7_schalter")
        val = pg.evaluate("() => localStorage.getItem('mw-lv-knoepfe')")
        pruef(val == "1", "Schalter an: pro Browser gespeichert (%s)" % val)
        ui = pg.evaluate("() => fetch('/api/ui').then(r => r.json())")
        pg.wait_for_timeout(1200)
        ui = pg.evaluate("() => fetch('/api/ui').then(r => r.json())")
        pruef("mw-lv-knoepfe" not in ui, "nicht auf den Pi kopiert (WEB_UI_LOCAL)")
    pg.goto(base + "/", wait_until="domcontentloaded")
    warte(lambda: pg.evaluate("() => !!(window.mwKamWahl && mwKamWahl.state().on)"), 20000)
    weg(); pg.evaluate("() => scrollTo(0, 0)"); pg.wait_for_timeout(5500)
    s, v = pg.evaluate(ST), pg.evaluate(SICHT)
    pruef(s and not s["auto"] and v["tools"]["op"] == 1 and v["row"]["op"] == 1 and not any(v["hold"]), "Schalter an: Knöpfe und Kacheln immer sichtbar (%s)" % s)
    foto("8_schalter_an")
    pg.evaluate("() => localStorage.removeItem('mw-lv-knoepfe')")


KWS = "() => window.mwKamWahl ? window.mwKamWahl.state() : null"


def pc(pg, base, a, pruef):
    warte, weg, foto = helfer(pg, a, "pc")
    laden(pg, base, warte, weg)
    pg.mouse.move(5, 5); pg.wait_for_timeout(5000)
    pruef(not pg.evaluate(ST)["shown"], "PC: Start sauber")
    vc = mitte(pg, "#video")
    pg.mouse.move(vc[0], vc[1]); pg.mouse.move(vc[0] + 20, vc[1] + 10); pg.wait_for_timeout(400)
    s = pg.evaluate(ST)
    pruef(s["shown"] and s["why"] == "hover", "PC: Maus über dem Bild zeigt sie (%s)" % s)
    foto("1_maus")
    fs = mitte(pg, "#lv-b-view")
    pg.mouse.move(fs[0], fs[1]); pg.wait_for_timeout(5000)
    s = pg.evaluate(ST)
    pruef(s["shown"] and s["pinned"] == "mouse", "PC: Maus auf einem Knopf: bleiben (%s)" % s)
    pg.mouse.move(vc[0], vc[1] + 40); pg.wait_for_timeout(4700)
    pruef(not pg.evaluate(ST)["shown"], "PC: 4 s nach der letzten Bewegung weg")
    pg.mouse.move(2, 2); pg.wait_for_timeout(300)
    hit = None
    for _ in range(80):
        pg.keyboard.press("Tab")
        hit = pg.evaluate("() => { const a = document.activeElement; return a && a.closest && a.closest('#lv-tools, #kw-row') ? a.id || a.dataset.k : null; }")
        if hit:
            break
    pg.wait_for_timeout(300)
    s = pg.evaluate(ST)
    pruef(bool(hit) and s["shown"], "Tastatur: Tab auf «%s» zeigt sie (%s)" % (hit, s))
    pg.wait_for_timeout(5000)
    pruef(pg.evaluate(ST)["shown"], "Tastatur: solange der Knopf den Fokus hat, bleiben sie")
    foto("2_tab")


if __name__ == "__main__":
    sys.exit(main())
