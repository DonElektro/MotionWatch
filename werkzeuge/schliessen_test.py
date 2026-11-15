#!/usr/bin/env python3
"""Test «jede Seite hat einen Weg zurück» (Besitzer 15.11.2026: «Fenster, das ich nicht mehr zukriege»).

Am Handy läuft MoveEye oft als App vom Home-Bildschirm (ohne Adresszeile, ohne Zurück-Knopf des Browsers). Geprüft wird mit
Playwright bei 390 px, dunkel, Touch, und «App-Modus» nachgemacht (navigator.standalone, matchMedia display-mode: standalone):
  1. Handy-Funkgerät (funk/, wie auf der Homepage «Funk/»): jedes Blatt (Senden, Schlüssel, Einstellungen, Verlauf, Bild) hat ein
     sichtbares «✕ Schliessen» (mindestens 44 × 44 px, aria-label); Esc, Tippen daneben und nach unten Wischen schliessen es.
  2. Handy-Funkgerät von einer anderen Seite her geöffnet (Homepage → Funk/): «‹ Zurück» ist da und führt zurück; direkt als
     eigene App geöffnet: keiner (es gibt nichts dahinter).
  3. MoveEye → Morse-Modus → «⬇ Als Datei für ein anderes Handy herunterladen» im App-Modus: die Datei geht ins Teilen-Blatt,
     die Seite bleibt; öffnet das iPhone die Datei trotzdem als Seite, hat sie «‹ Zurück» und das führt zum Morse-Modus.
  4. Jede Seite von MoveEye (alle festen Adressen, die eine HTML-Seite liefern): Reiter, «✕ Zurück» oder ein eigener Weg zurück.
  5. Fenster: Nachrichten-Bild gross, Update / Neustart des Pi (wartet auf den Pi) - je ein sichtbares «✕».
  6. keine JavaScript-Fehler

  python3 werkzeuge/schliessen_test.py [--datei X.py] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Zu-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []
# every fixed address of MoveEye that can be an HTML page (the test skips what is no page: 404, JSON, a file)
SEITEN = ("/more", "/settings", "/tools", "/sim", "/cams", "/zones", "/diary", "/recordings", "/timeline", "/messages", "/log", "/help",
          "/fav", "/protect", "/quick", "/place", "/servo", "/refscan", "/thermal_align", "/preview", "/play", "/party", "/spiele",
          "/almanach", "/almanach/bilder", "/almanach/plus", "/almanach/sos", "/almanach/live", "/karte", "/karten", "/tausch",
          "/tausch/packlisten", "/morse", "/morse/funk", "/radio", "/nacht", "/kino", "/info", "/dev", "/build", "/case", "/homepage",
          "/hp", "/hilfe/fehler/", "/qr", "/nt/", "/nt/walk/", "/sim/trailer", "/sim/vorfuehrung", "/setup-card", "/qr/print", "/karten/print")
# the app mode of the home screen (iPhone: navigator.standalone, others: display-mode standalone)
APP_MODUS = """(() => { try { Object.defineProperty(Navigator.prototype, 'standalone', {get: () => true, configurable: true}); } catch (e) {}
  const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? {matches: true, media: q, onchange: null, addListener() {}, removeListener() {},
    addEventListener() {}, removeEventListener() {}, dispatchEvent() { return false; }} : mm(q);
  try { localStorage.setItem('mw-lang', 'de'); } catch (e) {} })();"""
# a visible way back on the page: tabs, «✕ Zurück» of MoveEye, the own back link or a button / link «‹ / ✕ / Zurück / Schliessen»
WEG_ZURUECK = r"""(root) => { const R = root ? document.querySelector(root) : document;
  const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05 && r.bottom > 0 && r.right > 0 && r.left < innerWidth && r.top < innerHeight; };
  if (!root) { const n = document.querySelector('nav.nav'); if (vis(n)) return 'Reiter';
    for (const id of ['mw-exit', 'mw-back']) { const e = document.getElementById(id); if (vis(e) && vis(e.querySelector('a,button') || e)) return id; }
    for (const e of document.querySelectorAll('[data-mw-exit]')) if (vis(e)) return 'eigener Knopf «' + e.textContent.trim().slice(0, 24) + '»'; }
  const re = /^\s*(✕|×|‹|←)|(Zurück|Schliessen|Abbrechen|Fertig|\bBack\b|\bClose\b)/i;
  for (const e of R.querySelectorAll('a,button,[role=button]')) { const r = e.getBoundingClientRect();
    if (vis(e) && r.width >= 30 && r.height >= 30 && re.test((e.textContent || '') + ' ' + (e.getAttribute('aria-label') || ''))) return 'Knopf «' + e.textContent.trim().slice(0, 24) + '»'; }
  return ''; }"""


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def kontext(br, extra=""):
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme="dark",
                         locale="de-CH", http_credentials={"username": "admin", "password": PASSWORT})
    ctx.add_init_script(APP_MODUS + extra)
    return ctx


def teil_funk(br, hp, bilder):
    """1. + 2. the page «Handy-Funkgerät» as on the homepage (Funk/)"""
    print("Handy-Funkgerät (Funk/)", flush=True)
    ctx = kontext(br); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.evaluate("u => location.replace(u)", hp + "Funk/"); pg.wait_for_url("**/Funk/"); pg.wait_for_timeout(500)   # launched: nothing behind it
    pruef(not pg.locator("#mw-back").is_visible(), "direkt als eigene App geöffnet: kein «Zurück» (nichts dahinter)")
    for knopf, blatt in (("#sendBtn", "#shSend"), ("#keyBtn", "#shKey"), ("#setBtn", "#shSet"), ("#histBtn", "#shHist"), ("#imgBtn", "#shImg")):
        for wie in ("✕", "Esc", "daneben", "wischen"):
            pg.locator(knopf).click(); pg.wait_for_timeout(200)
            x = pg.locator(blatt + " [data-close]").first
            auf = pg.locator(blatt).is_visible()
            if wie == "✕":
                bb = x.bounding_box() or {"width": 0, "height": 0}
                txt, al = x.inner_text(), x.get_attribute("aria-label") or ""
                pruef(auf and x.is_visible() and bb["width"] >= 44 and bb["height"] >= 44 and "✕" in txt and "Schliessen" in txt and al == "Schliessen",
                      f"{blatt}: «{txt.strip()}» sichtbar, {bb['width']:.0f} × {bb['height']:.0f} px, aria-label «{al}»")
                if bilder and blatt == "#shImg":
                    pg.screenshot(path=os.path.join(bilder, "nachher_funk_blatt_bild.png"))
                x.click()
            elif wie == "Esc":
                pg.keyboard.press("Escape")
            elif wie == "daneben":
                pg.mouse.click(195, 12)
            else:                                            # a finger from the top of the sheet 200 px down
                pg.evaluate("""s => { const p = document.querySelector(s + ' .panel'), r = p.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + 12;
                  const t = yy => new Touch({identifier: 1, target: p, clientX: x, clientY: yy});
                  p.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true, touches: [t(y)], changedTouches: [t(y)]}));
                  for (let i = 1; i <= 5; i++) p.dispatchEvent(new TouchEvent('touchmove', {bubbles: true, cancelable: true, touches: [t(y + i * 40)], changedTouches: [t(y + i * 40)]}));
                  p.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true, touches: [], changedTouches: [t(y + 200)]})); }""", blatt)
            pg.wait_for_timeout(350)
            pruef(auf and not pg.locator(blatt).is_visible(), f"{blatt}: {wie} schliesst das Blatt")
            pg.evaluate("() => document.querySelectorAll('.sheet.open').forEach(s => s.classList.remove('open'))")
    # a little swipe (or scrolling inside) does not close it
    pg.locator("#setBtn").click(); pg.wait_for_timeout(200)
    pg.evaluate("""() => { const p = document.querySelector('#shSet .panel'), r = p.getBoundingClientRect(), x = r.left + 50, y = r.top + 12;
      const t = yy => new Touch({identifier: 1, target: p, clientX: x, clientY: yy});
      p.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, touches: [t(y)], changedTouches: [t(y)]}));
      p.dispatchEvent(new TouchEvent('touchmove', {bubbles: true, cancelable: true, touches: [t(y + 30)], changedTouches: [t(y + 30)]}));
      p.dispatchEvent(new TouchEvent('touchend', {bubbles: true, touches: [], changedTouches: [t(y + 30)]})); }""")
    pg.wait_for_timeout(350)
    pruef(pg.locator("#shSet").is_visible() and pg.evaluate("() => !document.querySelector('#shSet .panel').style.transform"),
          "kurzes Wischen (30 px): das Blatt bleibt offen und springt zurück")
    pg.keyboard.press("Escape")
    ctx.close()
    # from the start page of the homepage: «‹ Zurück» is there and leads back
    ctx = kontext(br); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(hp, wait_until="domcontentloaded"); pg.click("a[href='Funk/']"); pg.wait_for_url("**/Funk/"); pg.wait_for_timeout(500)
    b = pg.locator("#mw-back")
    bb = b.bounding_box() if b.is_visible() else None
    if bilder:
        pg.screenshot(path=os.path.join(bilder, "nachher_funk_von_homepage.png"))
    pruef(bool(bb) and bb["height"] >= 44 and "Zurück" in b.inner_text(), f"von der Homepage her geöffnet: «{b.inner_text() if bb else ''}» sichtbar ({bb})")
    if bb:
        b.click(); pg.wait_for_timeout(700)
        pruef(pg.url.rstrip("/") == hp.rstrip("/"), f"«‹ Zurück» führt zur Homepage ({pg.url})")
    pruef(not errs, f"Handy-Funkgerät: keine JavaScript-Fehler {errs[:2]}")
    ctx.close()


def teil_datei(br, base, bilder):
    """3. MoveEye → Morse-Modus → «⬇ Als Datei …» in the app mode"""
    print("Morse-Modus → Handy-Funkgerät als Datei (App-Modus)", flush=True)
    ctx = kontext(br, """window.__geteilt = []; navigator.canShare = () => true;
      navigator.share = d => { window.__geteilt.push((d.files || []).map(f => f.name + ':' + f.type + ':' + f.size)); return Promise.resolve(); };""")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(base + "/morse", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
    pg.evaluate("() => { const f = document.getElementById('mo-f-prot'); if (f) f.click(); }"); pg.wait_for_timeout(800)
    a = pg.locator("#mo-funk-dl")
    if not a.is_visible():
        pg.evaluate("() => { const p = document.getElementById('mo-prot'); if (p) p.hidden = false; }")
    a.scroll_into_view_if_needed(); a.click(); pg.wait_for_timeout(2500)
    g = pg.evaluate("() => window.__geteilt")
    pruef(pg.url.endswith("/morse") and g and g[0] and g[0][0].startswith("Handy-Funkgeraet.html:"),
          f"App-Modus: die Datei geht ins Teilen-Blatt (mit «Schliessen» des iPhones), die Seite bleibt ({g}, {pg.url})")
    # the iPhone opens the file anyway as a page (download in the app mode): it has a way back
    html = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(
        base + "/morse/funk.html", headers={"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()}), timeout=20).read()
    pg.route("**/__datei/Handy-Funkgeraet.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html))
    pg.evaluate("() => { location.href = '/__datei/Handy-Funkgeraet.html'; }"); pg.wait_for_url("**/Handy-Funkgeraet.html"); pg.wait_for_timeout(700)
    b = pg.locator("#mw-back")
    if bilder:
        pg.screenshot(path=os.path.join(bilder, "nachher_funk_datei.png"))
    pruef(b.is_visible() and "Zurück" in b.inner_text(), f"die Datei als Seite geöffnet: «{b.inner_text() if b.is_visible() else ''}» sichtbar")
    if b.is_visible():
        b.click(); pg.wait_for_timeout(1200)
        pruef(pg.url.endswith("/morse"), f"«‹ Zurück» führt zum Morse-Modus ({pg.url})")
    pruef(b"window.__mwExit" in html and html.count(b"mw-exit") == 0, "die Datei für ein anderes Handy: ohne das «✕ Zurück» von MoveEye (eigener Weg zurück)")
    pruef(not errs, f"Morse / Datei: keine JavaScript-Fehler {errs[:2]}")
    ctx.close()


def teil_seiten(br, base, bilder):
    """4. every page of MoveEye"""
    print("alle Seiten von MoveEye (App-Modus)", flush=True)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()}
    ctx = kontext(br); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(pg.url + ": " + str(e)[:160]))
    pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
    pruef(pg.evaluate(WEG_ZURUECK, None) == "Reiter", "Hauptseite: Reiter")
    n = 0
    for s in SEITEN:
        try:
            r = op.open(urllib.request.Request(base + s, headers=H), timeout=20)
            typ, cd = r.headers.get("Content-Type", ""), r.headers.get("Content-Disposition", "")
            r.read()
        except Exception:
            continue
        if "text/html" not in typ or "attachment" in cd:
            continue
        pg.goto(base + "/", wait_until="commit")            # with something behind (as when coming from MoveEye)
        try:
            pg.goto(base + s, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            pruef(False, f"{s}: lädt nicht ({str(e)[:80]})"); continue
        weg = ""
        for _i in range(8):
            pg.wait_for_timeout(400)
            weg = pg.evaluate(WEG_ZURUECK, None)
            if weg:
                break
        n += 1
        pruef(bool(weg), f"{s}: {weg or 'KEIN Weg zurück'}")
        if not weg and bilder:
            pg.screenshot(path=os.path.join(bilder, "ohne_weg_" + re.sub(r"\W+", "_", s).strip("_") + ".png"))
    pruef(n >= 30, f"{n} Seiten geprüft")
    # 5. windows
    pg.goto(base + "/messages", wait_until="domcontentloaded"); pg.wait_for_timeout(1200)
    pg.evaluate("() => big('/icon-192.png')"); pg.wait_for_timeout(300)
    w = pg.evaluate(WEG_ZURUECK, "#big")
    pruef(pg.locator("#big").is_visible() and "✕" in w, f"Nachrichten, Bild gross: {w or 'kein ✕'}")
    if bilder:
        pg.screenshot(path=os.path.join(bilder, "nachher_nachrichten_bild.png"))
    if "✕" in w:
        pg.locator("#big button").first.click()
    else:
        pg.evaluate("() => { document.getElementById('big').style.display = 'none'; }")
    pg.wait_for_timeout(300)
    pruef(not pg.locator("#big").is_visible(), "Nachrichten, Bild gross: ✕ schliesst")
    for wie, js in (("Update", "() => updWait('99.0.0')"), ("Neustart", "() => powerOverlay('reboot')")):
        pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
        pg.evaluate(js); pg.wait_for_timeout(400)
        w = pg.evaluate(WEG_ZURUECK, "#pw-ov")
        pruef("✕" in w, f"Fenster «{wie}» (wartet auf den Pi): {w or 'kein ✕'}")
        if bilder:
            pg.screenshot(path=os.path.join(bilder, "nachher_fenster_" + wie.lower() + ".png"))
        if "✕" in w:
            pg.locator("#pw-ov .mw-ovx").click(); pg.wait_for_timeout(300)
            pruef(pg.locator("#pw-ov").count() == 0, f"Fenster «{wie}»: ✕ schliesst, die Seite ist wieder da")
        pg.evaluate("() => { const o = document.getElementById('pw-ov'); if (o) o.remove(); }")
    pruef(not errs, f"Seiten: keine JavaScript-Fehler {errs[:3]}")
    ctx.close()


def main():
    ap = argparse.ArgumentParser(description="jede Seite hat einen Weg zurück")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5231)
    ap.add_argument("--bilder", default="")
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
    tmp = tempfile.mkdtemp(prefix="mw_zu_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "patrol": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    # the homepage as the owner has it: a start page with a link to Funk/ (the same files as funk/)
    hpdir = os.path.join(tmp, "hp"); shutil.copytree(os.path.join(REPO, "funk"), os.path.join(hpdir, "Funk"))
    with open(os.path.join(hpdir, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!doctype html><html lang="de"><meta name="viewport" content="width=device-width"><body style="background:#111;color:#eee">'
                '<a href="Funk/" style="display:block;padding:20px;color:#5af">📡 Handy-Funkgerät</a></body></html>')
    class Leise(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *x):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lambda *x: Leise(*x, directory=hpdir))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    hp = "http://127.0.0.1:%d/" % srv.server_address[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw_:
            br = pw_.chromium.launch(args=["--no-proxy-server"])
            teil_funk(br, hp, a.bilder)
            op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _i in range(240):
                if p.poll() is not None:
                    sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
                try:
                    op.open(base + "/manifest.webmanifest", timeout=2); break
                except Exception:
                    time.sleep(1)
            teil_datei(br, base, a.bilder)
            teil_seiten(br, base, a.bilder)
            br.close()
    finally:
        srv.shutdown()
        p.terminate()
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d Fehler" % len(FEHLER) if FEHLER else "\nalles ok")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
