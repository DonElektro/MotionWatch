#!/usr/bin/env python3
"""Test «Unterseiten als Fenster» (Teil 639zzzzx, Besitzer 15.11.2026).

Startet MoveEye ohne Fenster mit der Demo und prüft mit Playwright (iPhone 13, dunkel; dazu kurz PC und «Bewegung reduzieren»):
  1. ab Werk «Mitte»: Einstellungen → eine Zeile öffnet ein Fenster über der Liste (dialog, aria-modal, Fokus auf ✕, die Liste
     bleibt dahinter sichtbar, #s=… in der Adresse); Tab bleibt im Fenster; Esc schliesst, Fokus zurück auf die Zeile
  2. schliessen mit ✕, Tipp auf den Hintergrund, Zurück des Browsers (vorwärts öffnet wieder)
  3. Wischen: «Von unten» Titelzeile nach unten = zu, im Inhalt nicht; «Von der Seite» nach rechts = zu; «Mitte» am Titel nach unten
  4. tabOpen bei offenem Fenster: der Inhalt wechselt, kein zweites Fenster (kein neuer Eintrag im Verlauf, Zurück = zu)
  5. die Wahl: Einstellungen → Darstellung & Sprache → «Unterseiten» (Zustand, vier Knöpfe, gemerkt pro Gerät, das offene Fenster
     wechselt sofort); «Ganze Seite» = wie bisher
  6. Schutz und Verlauf: Fenster; Live: unverändert (ganze Seite)
  7. Mehr → Radio: Rahmen mit ?fenster=1, ohne Kopf / «‹ Mehr» / doppelten Titel, #f=…; ✕, Zurück; ein Link, der die Seite verlässt,
     öffnet in der Hauptseite; /radio direkt = ganze Seite; /more#f=/radio öffnet das Fenster; spielt Ton, bleibt der Rahmen beim
     Schliessen stehen und kommt unverändert zurück; window.mwAudio der Hauptseite
  8. Anleitung «Tipps & Tricks» in fünf Sprachen; keine JavaScript-Fehler

  python3 werkzeuge/fenster_test.py [--datei X.py] [--bilder ORDNER]
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
PASSWORT = "Fenster-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


WIN = """() => { const p = document.getElementById('ms-page'), d = document.getElementById('fx-dim'), L = document.getElementById('ms-list');
  const a = document.activeElement;
  return {win: !!(p && p.classList.contains('fx-win')), cls: p ? [...p.classList].filter(c => /^fx-(bottom|mid|side|full)$/.test(c)).join('') : '',
          dim: !!(d && d.isConnected), sub: document.body.classList.contains('ms-sub'), pg: !!document.querySelector('.ms-pg'),
          modal: p ? p.getAttribute('aria-modal') : null, role: p ? p.getAttribute('role') : null, hash: location.hash,
          title: (document.querySelector('#ms-bar b') || {}).textContent || '', focus: a ? (a.id || a.dataset.ms || a.tagName) : '',
          inside: !!(p && a && p.contains(a)), list: !!(L && L.getClientRects().length && getComputedStyle(L).display !== 'none'),
          lock: document.documentElement.classList.contains('fx-lock'), x: (document.getElementById('ms-back') || {}).textContent || ''}; }"""
FR = """() => { const w = document.getElementById('fx-frame'), f = w && w.querySelector('iframe');
  let i = null; try { const d = f.contentDocument, v = e => !!(e && e.getClientRects().length && getComputedStyle(e).display !== 'none');
    i = {src: f.contentWindow.location.pathname + f.contentWindow.location.search, cls: d.documentElement.classList.contains('mw-fenster'),
         header: v(d.querySelector('header')), back: v(d.querySelector('main a[href="/more"]')), h2: v(d.querySelector('main h2'))}; } catch (e) {}
  return {open: !!(w && w.classList.contains('fx-win')), cls: w ? [...w.classList].filter(c => /^fx-(bottom|mid|side|full)$/.test(c)).join('') : '',
          title: w ? (w.querySelector('.fx-bar b') || {}).textContent : '', hash: location.hash, path: location.pathname, inner: i,
          parked: !!document.querySelector('.fx-park'), dim: !!document.getElementById('fx-dim')}; }"""


def main():
    ap = argparse.ArgumentParser(description="Unterseiten als Fenster")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5223)
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
    tmp = tempfile.mkdtemp(prefix="mw_fenster_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    bild = lambda pg, n: pg.screenshot(path=os.path.join(a.bilder, n + ".png")) if a.bilder else None
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()}
        get = lambda path: op.open(urllib.request.Request(base + path, headers=H), timeout=15).read().decode("utf-8", "replace")
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        # 8. the manual
        h = get("/help")
        pruef(h.count("🪟 Unterseiten als Fenster") == 1 and h.count("🪟 Sub-pages as a window") == 1, "Anleitung Deutsch / Englisch: der Absatz")
        for L, w in (("fr", "Sous-pages en fenêtre"), ("it", "Sottopagine in una finestra"), ("rm", "Sutpaginas sco fanestra")):
            pruef(w in get("/i18n/%s.js?h=1" % L), "Anleitung %s: der Absatz in «Tipps & Tricks»" % L)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            ctx = br.new_context(http_credentials={"username": "admin", "password": PASSWORT}, color_scheme="dark", **dev)
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');"
                                "localStorage.setItem('mw-tours-seen','[\"live\",\"protect\",\"history\",\"settings\",\"sim\",\"more\",\"cams\"]')}catch(e){}"
                                "document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');"
                                "s.textContent='#g2-ov,#g2-spot,#g2-bub,#gd-card{display:none!important}';document.head.appendChild(s);});")
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            W = lambda: pg.evaluate(WIN)

            def laden(path, sel="#ms-list .mi"):
                pg.goto(base + path, wait_until="domcontentloaded"); pg.wait_for_selector(sel, timeout=20000); pg.wait_for_timeout(1200)

            def zeile(ms):
                pg.locator('#ms-list .mi[data-ms="%s"]' % ms).click(); pg.wait_for_timeout(700)

            def setze(v):
                pg.evaluate("v => MWFX.set(v)", v)

            # 1. default «Middle»
            laden("/settings")
            pruef(pg.evaluate("() => MWFX.mode()") == "mid", "ab Werk: «Mitte»")
            zeile("sec:Updates"); w = W()
            pruef(w["win"] and w["cls"] == "fx-mid" and w["dim"] and w["modal"] == "true" and w["role"] == "dialog" and w["list"] and w["hash"].startswith("#s=")
                  and w["title"] == "Updates" and w["x"] == "✕" and w["lock"], "Einstellungen → Updates: Fenster «Mitte» über der Liste (%s)" % w)
            pruef(w["focus"] == "ms-back", "Fokus auf ✕ (%s)" % w["focus"])
            bild(pg, "einstellungen_mitte")
            for _ in range(25):
                pg.keyboard.press("Tab")
            pruef(W()["inside"], "Tab bleibt im Fenster")
            pg.keyboard.press("Shift+Tab"); pruef(W()["inside"], "Shift+Tab bleibt im Fenster")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(600); w = W()
            pruef(not w["win"] and not w["sub"] and not w["dim"] and not w["hash"] and not w["lock"] and w["x"].startswith("‹"), "Esc schliesst (%s)" % w)
            pruef(w["focus"] == "sec:Updates", "Fokus zurück auf die Zeile (%s)" % w["focus"])
            # 2. ✕, background, back / forward
            zeile("sec:Updates"); pg.locator("#ms-back").click(); pg.wait_for_timeout(600)
            pruef(not W()["win"] and not W()["hash"], "✕ schliesst")
            zeile("sec:Updates"); pg.mouse.click(4, 420); pg.wait_for_timeout(600)
            pruef(not W()["win"], "Tipp auf den Hintergrund schliesst")
            zeile("sec:Updates"); pg.go_back(); pg.wait_for_timeout(700)
            pruef(not W()["win"] and pg.evaluate("() => location.pathname") == "/settings", "Zurück des Browsers schliesst (bleibt auf Einstellungen)")
            pg.go_forward(); pg.wait_for_timeout(700)
            pruef(W()["win"] and W()["title"] == "Updates", "Vorwärts öffnet das Fenster wieder")
            pg.locator("#ms-back").click(); pg.wait_for_timeout(600)

            def zieh(dx, dy, sel="#ms-bar", at=None):
                b = pg.locator(sel).first.bounding_box()
                x0, y0 = (b["x"] + b["width"] * 0.4, b["y"] + b["height"] / 2) if at is None else at
                pg.mouse.move(x0, y0); pg.mouse.down()
                for i in range(1, 9):
                    pg.mouse.move(x0 + dx * i / 8, y0 + dy * i / 8); pg.wait_for_timeout(16)
                pg.mouse.up(); pg.wait_for_timeout(700)
            # 3. swipe
            zeile("sec:Updates"); zieh(0, 220)
            pruef(not W()["win"], "«Mitte»: Titel nach unten ziehen schliesst")
            setze("bottom"); zeile("sec:Updates"); pruef(W()["cls"] == "fx-bottom", "«Von unten» gewählt")
            bild(pg, "einstellungen_von_unten")
            b = pg.locator("#ms-page .ms-body").bounding_box()
            zieh(0, 200, at=(b["x"] + 40, b["y"] + 60)); pruef(W()["win"], "«Von unten»: im Inhalt ziehen schliesst nicht")
            zieh(0, 30); pruef(W()["win"], "«Von unten»: kurz ziehen = federt zurück")
            zieh(0, 220); pruef(not W()["win"], "«Von unten»: Titelzeile nach unten ziehen schliesst")
            setze("side"); zeile("sec:Updates"); pruef(W()["cls"] == "fx-side", "«Von der Seite» gewählt")
            bild(pg, "einstellungen_von_der_seite")
            zieh(0, 220); pruef(W()["win"], "«Von der Seite»: nach unten ziehen schliesst nicht")
            zieh(200, 0); pruef(not W()["win"], "«Von der Seite»: nach rechts ziehen schliesst")
            setze("mid")
            # 4. tabOpen while open: the content changes, one window, no new history entry
            zeile("sec:Updates"); n0 = pg.evaluate("() => history.length")
            pg.evaluate("() => tabOpen('sec:Patrol')"); pg.wait_for_timeout(700); w = W()
            pruef(w["win"] and w["title"] != "Updates" and pg.locator("#ms-page").count() == 1 and pg.evaluate("() => history.length") == n0
                  and pg.locator("#ms-page [data-view='sec:Patrol']").count() == 1, "tabOpen: der Inhalt wechselt, kein zweites Fenster (%s)" % w["title"])
            pg.go_back(); pg.wait_for_timeout(700)
            pruef(not W()["win"], "danach: Zurück schliesst das eine Fenster")
            # 4b. a dialog opened from the window lies above it and takes the tap (Web-Passwort #pwd-ov of the card «Sicherheit»)
            pg.evaluate("() => msOpen('grp:security')"); pg.wait_for_timeout(900)
            pruef(W()["win"] and pg.locator("#ms-page #secpanel").count() == 1, "Sicherheit im Fenster")
            # (this MoveEye has --web-password: the button only shows a toast - that toast must be above the window too)
            pg.locator("#ms-page #secpanel button", has_text="Web-Passwort").first.click(); pg.wait_for_timeout(500)
            t = pg.evaluate("() => { const o = document.getElementById('toast'); return o && o.getClientRects().length ? +getComputedStyle(o).zIndex : null; }")
            pruef(t is None or t > 237, "Meldung (#toast) aus dem Fenster liegt über dem Fenster (z %s)" % t)
            # a dialog like #pwd-ov (fixed, z-index 200, appended to <body>) opened by a button inside the window
            pg.evaluate("""() => { const b = document.createElement('button'); b.id = 't-open'; b.type = 'button'; b.textContent = 'Dialog';
                b.onclick = () => { const o = document.createElement('div'); o.id = 't-ov'; o.style.cssText = 'position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center';
                  o.innerHTML = '<div class="card"><input id="t-in" type="password"><button id="t-save" type="button">Speichern</button></div>';
                  o.querySelector('#t-save').onclick = () => { window.__saved = (window.__saved || 0) + 1; o.remove(); };
                  o.addEventListener('keydown', e => { if (e.key === 'Escape') o.remove(); }); document.body.appendChild(o); o.querySelector('#t-in').focus(); };
                document.querySelector('#ms-page #secpanel').prepend(b); }""")
            pg.locator("#t-open").click(); pg.wait_for_timeout(400)
            d = pg.evaluate("""() => { const o = document.getElementById('t-ov'), w = document.getElementById('ms-page'), b = document.getElementById('t-save'), r = b.getBoundingClientRect();
                const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return {zo: +getComputedStyle(o).zIndex, zw: +getComputedStyle(w).zIndex, hit: hit === b, win: w.classList.contains('fx-win'), focus: document.activeElement && document.activeElement.id}; }""")
            pruef(d["win"] and d["zo"] > d["zw"] and d["hit"] and d["focus"] == "t-in", "Dialog aus dem Fenster liegt oben, ist klickbar und hat den Fokus (%s)" % d)
            bild(pg, "dialog_ueber_fenster")
            pg.keyboard.press("Tab"); pg.keyboard.press("Shift+Tab")
            pruef(pg.evaluate("() => !!(document.activeElement && document.activeElement.closest('#t-ov'))"), "Tab im Dialog: die Fokusfalle des Fensters lässt ihn")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
            pruef(W()["win"] and not pg.evaluate("() => !!document.getElementById('t-ov')"), "Esc schliesst den Dialog, nicht das Fenster darunter")
            pg.locator("#t-open").click(); pg.wait_for_timeout(400); pg.locator("#t-save").click(); pg.wait_for_timeout(300)
            pruef(pg.evaluate("() => window.__saved") == 1 and W()["win"], "Tipp auf «Speichern» im Dialog kommt an")
            pg.locator("#ms-back").click(); pg.wait_for_timeout(700)
            z = pg.evaluate("() => { const o = document.getElementById('toast'); return o ? o.style.zIndex : ''; }")
            pruef(not W()["win"] and z == "", "Fenster zu, gehobene Ebenen wieder wie vorher (%r)" % z)
            # 5. the choice
            st = pg.evaluate("""() => { const r = document.querySelector('#ms-list .mi[data-ms="#fx-card"]');
                return r ? [r.closest('.mg').querySelector('.mgh').textContent, r.querySelector('b').textContent, r.querySelector('.ms-st').textContent] : null; }""")
            pruef(st == ["Darstellung & Sprache", "Unterseiten", "Mitte"], "Zeile «Unterseiten» unter Darstellung & Sprache, Zustand «Mitte» (%s)" % st)
            zeile("#fx-card")
            k = pg.evaluate("() => [...document.querySelectorAll('#fx-card .fx-pick button')].map(b => b.textContent + (b.getAttribute('aria-checked') === 'true' ? '*' : ''))")
            pruef(k == ["Ganze Seite", "Von unten", "Mitte*", "Von der Seite"], "vier Knöpfe, «Mitte» gewählt (%s)" % k)
            bild(pg, "unterseiten_wahl")
            pg.locator('#fx-card .fx-pick button[data-v="bottom"]').click(); pg.wait_for_timeout(400)
            pruef(W()["cls"] == "fx-bottom" and pg.evaluate("() => localStorage.getItem('mw-sheet')") == "bottom", "«Von unten» gewählt: das offene Fenster wechselt sofort, gemerkt")
            bild(pg, "unterseiten_wahl_von_unten")
            laden("/settings")
            st = pg.evaluate("() => document.querySelector('#ms-list .mi[data-ms=\"#fx-card\"] .ms-st').textContent")
            pruef(st == "Von unten" and pg.evaluate("() => MWFX.mode()") == "bottom", "nach dem Neuladen: «Von unten» (%s)" % st)
            pruef('"mw-sheet"' in get("/settings"), "pro Gerät: mw-sheet in der Liste der Geräte-Schlüssel (wird nicht auf den Pi kopiert)")
            setze("full"); zeile("sec:Updates"); w = W()
            pruef(not w["win"] and w["pg"] and w["sub"] and not w["dim"] and w["x"].startswith("‹"), "«Ganze Seite»: wie bisher (%s)" % w)
            pg.locator("#ms-back").click(); pg.wait_for_timeout(600)
            setze("mid")
            # 6. Schutz, Verlauf: window; Live: as before
            for path, name in (("/protect", "Schutz"), ("/recordings", "Verlauf")):
                laden(path)
                pg.evaluate("() => { const r = [...document.querySelectorAll('#ms-list .mi')].find(m => !m.hidden && m.tagName === 'BUTTON'); r.scrollIntoView({block: 'center'}); r.click(); }")
                pg.wait_for_timeout(800); w = W()
                pruef(w["win"] and w["cls"] == "fx-mid" and w["list"], "%s: Unterseite als Fenster (%s)" % (name, w["title"]))
                bild(pg, "%s_mitte" % name.lower())
                pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
            laden("/")
            pg.locator('#ms-list .mi[data-ms="#wt-card"]').click(); pg.wait_for_timeout(700); w = W()
            pruef(not w["win"] and w["pg"] and not w["dim"], "Live: unverändert, ganze Seite (%s)" % w)
            # 7. Mehr → Radio
            laden("/more", "main a.mi[href='/radio']")
            pg.evaluate("() => document.querySelector('main a.mi[href=\"/radio\"]').scrollIntoView({block: 'center'})")
            n0 = pg.evaluate("() => history.length")
            pg.locator("main a.mi[href='/radio']").click(); pg.wait_for_timeout(2500); f = pg.evaluate(FR)
            pruef(f["open"] and f["cls"] == "fx-mid" and f["path"] == "/more" and f["hash"] == "#f=%2Fradio" and f["title"] == "📻 Radio",
                  "Mehr → Radio: Fenster über Mehr, #f=/radio (%s)" % {k: f[k] for k in ("open", "cls", "path", "hash", "title")})
            i = f["inner"] or {}
            pruef(i.get("src") == "/radio?fenster=1" and i.get("cls") and not i.get("header") and not i.get("back") and not i.get("h2"),
                  "im Rahmen: /radio?fenster=1 ohne Kopf, «‹ Mehr» und doppelten Titel (%s)" % i)
            bild(pg, "radio_mitte")
            pg.locator("#fx-frame .fx-x").click(); pg.wait_for_timeout(600); f = pg.evaluate(FR)
            pruef(not f["open"] and not f["dim"] and not f["hash"] and pg.evaluate("() => history.length") == n0 + 1, "✕ schliesst das Radio-Fenster")
            for v, n in (("bottom", "radio_von_unten"), ("side", "radio_von_der_seite")):
                setze(v); pg.locator("main a.mi[href='/radio']").click(); pg.wait_for_timeout(2200)
                pruef(pg.evaluate(FR)["cls"] == "fx-" + v, "Radio-Fenster «%s»" % v)
                bild(pg, n)
                pg.go_back(); pg.wait_for_timeout(700)
                pruef(not pg.evaluate(FR)["open"], "Zurück schliesst das Radio-Fenster («%s»)" % v)
            setze("mid")
            pg.locator("main a.mi[href='/radio']").click(); pg.wait_for_timeout(2200)
            fl = pg.frame_locator("#fx-frame iframe")
            fl.locator("body").evaluate("b => { const a = document.createElement('a'); a.id = 'fx-t-link'; a.href = '/settings?open=sec:Updates'; a.textContent = 'x'; b.prepend(a); }")
            fl.locator("#fx-t-link").click(); pg.wait_for_timeout(3000)
            pruef(pg.evaluate("() => location.pathname") == "/settings" and not pg.evaluate(FR)["open"], "Link im Rahmen, der die Seite verlässt: öffnet in der Hauptseite")
            for _ in range(4):                                  # (the settings page put its own sub-page into the history)
                if pg.evaluate("() => location.pathname") == "/more":
                    break
                pg.go_back(); pg.wait_for_timeout(2500)
            f = pg.evaluate(FR)
            pruef(f["path"] == "/more", "Zurück: wieder Mehr (Fenster: %s)" % f["open"])
            if not f["open"]:
                pg.locator("main a.mi[href='/radio']").click(); pg.wait_for_timeout(2200)
            # sound keeps playing in the frame (<audio> of the page): the frame stays (out of sight) and comes back unchanged
            pg.frame_locator("#fx-frame iframe").locator("body").evaluate("b => { window.__fxMark = 42; const m = document.createElement('audio'); m.id = 'fx-t-au';"
                                                                          " Object.defineProperty(m, 'paused', {get: () => !!window.__fxStop}); b.appendChild(m); }")
            pg.locator("#fx-frame .fx-x").click(); pg.wait_for_timeout(700); f = pg.evaluate(FR)
            pruef(not f["open"] and f["parked"], "spielt Ton: der Rahmen bleibt beim Schliessen unsichtbar stehen")
            pg.locator("main a.mi[href='/radio']").click(); pg.wait_for_timeout(800)
            mk = pg.frame_locator("#fx-frame iframe").locator("body").evaluate("() => window.__fxMark")
            pruef(pg.evaluate(FR)["open"] and mk == 42, "wieder geöffnet: dieselbe Seite, nicht neu geladen")
            pg.frame_locator("#fx-frame iframe").locator("body").evaluate("() => { window.__fxStop = true; }")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(700)
            pruef(not pg.evaluate(FR)["open"] and not pg.evaluate(FR)["parked"], "Esc schliesst das Radio-Fenster (ohne Ton: entladen)")
            # the radio plays (player of the main page, 639zzzzd mwRadioP): a tab opens over the page, no reload
            pg.evaluate("() => { window.__fxMark = 7; window.mwRadioP = {S: {on: true, st: 'playing', name: 'Test'}, tx: {}, A: new Audio(), cb: null, play() {}, stop() {}, vol() {}, sleep() {}, ms() {}}; }")
            pg.locator("header nav.nav a[href='/protect']").click(); pg.wait_for_timeout(3000)
            f = pg.evaluate(FR); i = pg.evaluate("""() => { const f = document.querySelector('#fx-frame.fx-page iframe'); try { return [f.contentWindow.location.pathname,
                !!f.contentDocument.querySelector('header').getClientRects().length]; } catch (e) { return null; } }""")
            pruef(f["open"] and f["cls"] == "fx-full" and f["path"] == "/more" and f["hash"].startswith("#p=") and i == ["/protect", True]
                  and pg.evaluate("() => window.__fxMark") == 7, "Radio spielt: Reiter «Schutz» öffnet über der Seite (ganzer Bildschirm, eigener Kopf), kein Neuladen (%s %s)" % (f["hash"], i))
            bild(pg, "radio_spielt_schutz_darueber")
            # 📻 in the header of that page: the radio window of the main page
            pg.frame_locator("#fx-frame iframe").locator("body").evaluate("b => { const a = document.createElement('a'); a.id = 'fx-t-r'; a.href = '/radio'; a.textContent = 'R'; b.prepend(a); }")
            pg.frame_locator("#fx-frame iframe").locator("#fx-t-r").click(); pg.wait_for_timeout(2200); f = pg.evaluate(FR)
            pruef(f["open"] and f["title"] == "📻 Radio" and f["cls"] == "fx-mid" and pg.evaluate("() => window.__fxMark") == 7, "📻 in einer Seite darüber: das Radio-Fenster der Hauptseite")
            pg.go_back(); pg.wait_for_timeout(800)
            pg.evaluate("() => { delete window.mwRadioP; }")
            pg.goto(base + "/more", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
            # 📻 / a link to /radio on Live: the radio window over Live (Live itself stays as it is)
            laden("/")
            pg.evaluate("() => { let a = document.getElementById('mwk-radio'); if (a) a.hidden = false; else { a = document.createElement('a'); a.id = 'mwk-radio'; a.href = '/radio'; a.textContent = '📻'; document.querySelector('header').appendChild(a); } }")
            pg.locator("#mwk-radio").click(); pg.wait_for_timeout(2200); f = pg.evaluate(FR)
            pruef(f["open"] and f["path"] == "/" and f["title"] == "📻 Radio" and f["hash"] == "#f=%2Fradio", "Live: 📻 öffnet das Radio-Fenster über Live (%s)" % {k: f[k] for k in ("open", "path", "hash")})
            bild(pg, "live_radio_mitte")
            pg.go_back(); pg.wait_for_timeout(700)
            pruef(not pg.evaluate(FR)["open"] and not W()["win"], "Live: Zurück schliesst, Live unverändert")
            setze("full")
            pg.evaluate("() => { const a = document.getElementById('mwk-radio'); a.hidden = false; a.click(); }"); pg.wait_for_timeout(2200)
            pruef(pg.evaluate(FR)["cls"] == "fx-full", "«Ganze Seite»: das Radio über den ganzen Bildschirm (die Hauptseite lädt nicht neu)")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
            setze("mid")
            pg.goto(base + "/radio", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
            pruef(pg.evaluate("() => !document.documentElement.classList.contains('mw-fenster') && !!document.querySelector('header').getClientRects().length && !document.getElementById('fx-frame')"),
                  "/radio direkt: die ganze Seite wie bisher")
            pg.goto(base + "/more#f=%2Fradio", wait_until="domcontentloaded"); pg.wait_for_timeout(3000)
            pruef(pg.evaluate(FR)["open"], "/more#f=/radio öffnet das Radio-Fenster")
            pruef(not jsf, "Handy: keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close()
            # PC and «reduce motion»
            ctx = br.new_context(http_credentials={"username": "admin", "password": PASSWORT}, viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-tours-seen','[\"settings\",\"more\"]')}catch(e){}")
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            laden("/settings")
            zeile("sec:Updates")
            r = pg.evaluate("() => { const r = document.getElementById('ms-page').getBoundingClientRect(); return [r.width, getComputedStyle(document.getElementById('ms-page')).animationName]; }")
            pruef(W()["win"] and r[0] <= 762 and r[1] in ("none", ""), "PC: Fenster höchstens 760 px breit, ohne Bewegung (%s)" % r)
            bild(pg, "pc_einstellungen_mitte")
            pg.locator("#ms-back").click(); pg.wait_for_timeout(80)
            pruef(not W()["win"], "Bewegung reduziert: sofort zu")
            pruef(not jsf, "PC: keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close(); br.close()
        if p.poll() is not None:
            FEHLER.append("MoveEye ist während des Tests abgestürzt")
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
    print("Fenster-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
