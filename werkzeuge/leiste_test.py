#!/usr/bin/env python3
"""Test «eine Zeile weniger» (Teil 639o, 4.x): keine Leiste mehr unter den Reitern.

Startet MoveEye ohne Fenster mit der Demo und prüft mit Playwright (iPhone 13 und PC):
  1. auf jeder Seite mit Reitern: keine Zeile «Einfach | Experte · Darstellung» mehr (#mwbar ist ein kleiner Werkzeug-Teil in der
     Unterreiter-Zeile – ohne Unterreiter rechts in der Statuszeile), kein waagrechtes Scrollen, alles in 390 px
  2. Einstellungen: der Knopf «🎓 Experte» / «Einfach» neben 🔍, aria-pressed, ein Tipp schaltet (dieselbe Speicherung /api/ui_simple)
  3. Seiten mit nur einer Ansicht (Live, Mehr): kein Knopf
  4. Live: «⇕» öffnet Alle zuklappen · Meine Ansicht · Alle aufklappen (Nur Gruppen nicht als Zeile; langes Drücken auf
     «Meine Ansicht» klappt nur die Gruppen auf)
  5. Einstellungen → Darstellung & Sprache → «Symbole»: Zustand farbig / schlicht, die eigene Seite schaltet (body.icplain)
  6. Anleitung «Tipps & Tricks»: der neue Absatz in Deutsch, Englisch (/help) und Französisch, Italienisch, Rätoromanisch (/i18n/<L>.js?h=1)
  7. Pi-Fenster (Ersatz-tkinter): der Knopf Einfach / Experte statt der Leiste, «Symbole» im Menü ☰
  8. keine JavaScript-Fehler

  python3 werkzeuge/leiste_test.py [--datei X.py] [--bilder ORDNER]
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
PASSWORT = "Leiste-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


LAGE = """() => { const b = document.getElementById('mwbar'), m = document.getElementById('mwb-mode'), f = document.getElementById('mwb-fold');
  const vis = e => !!(e && e.getClientRects().length && !e.hidden && getComputedStyle(e).display !== 'none');
  const r = b && b.getBoundingClientRect();
  return {host: b ? (b.parentNode.matches('nav.subnav') ? 'subnav' : b.parentNode.matches('.chips') ? 'status' : b.classList.contains('inctl') ? 'kopf' : b.parentNode.tagName) : null,
          row: !!document.querySelector('header + #mwbar, main > #mwbar, body > #mwbar'), mode: vis(m) ? m.innerText.trim() : null, mlabel: m ? m.getAttribute('aria-label') : null, pressed: m ? m.getAttribute('aria-pressed') : null,
          fold: vis(f), find: !!(document.getElementById('ms-find') && document.getElementById('ms-find').parentNode === b),
          inside: !!(r && r.right <= innerWidth + 1 && r.left >= 0), doc: document.documentElement.scrollWidth, oldseg: !!document.querySelector('#mwbar .mwb-mode, #mwb-view')}; }"""


def teil_fenster(datei):
    print("Pi-Fenster (Ersatz-tkinter)", flush=True)
    src = open(os.path.join(HIER, "lupe_test.py"), encoding="utf-8").read()
    exec(re.search(r'FAKE_TK = r"""(.*?)"""', src, re.S).group(1), {})
    home = tempfile.mkdtemp(prefix="mw_leiste_tk_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_leiste_tk", "__file__": os.path.abspath(datei)}
    try:
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        App, CFG, tkm = ns["App"], ns["CFG"], sys.modules["tkinter"]
        a = object.__new__(App)
        a.root = tkm.Frame(); a._lay = (True, False)
        called = []
        a._set_simple = lambda v: called.append(v)
        b = a._mwbar(tkm.Frame(), "settings")
        CFG["ui_simple"] = False
        pruef(b is not None and ("Expert" in b.cget("text") or "Experte" in b.cget("text") or "Einfach" in b.cget("text") or "Simple" in b.cget("text")),
              "Fenster: ein Knopf Einfach / Experte statt der Leiste («%s»)" % (b.cget("text") if b else None))
        for fn in b.binds.get("<Button-1>", []):
            fn(None)
        pruef(len(called) == 1, "Fenster: ein Klick schaltet die Ansicht (%s)" % called)
        pruef(a._mwbar(tkm.Frame(), "sim") is None, "Fenster: Simulator (nur eine Ansicht) ohne Knopf")
        src570 = open(datei, encoding="utf-8").read()
        pruef('add_cascade(label=tr("Symbols")' in src570, "Fenster: «Symbole» im Menü ☰")
    except Exception as e:
        import traceback
        traceback.print_exc()
        pruef(False, "Fenster: %s" % e)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Eine Zeile weniger")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5211)
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
    tmp = tempfile.mkdtemp(prefix="mw_leiste_")
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
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode(), "Content-Type": "application/json"}
        get = lambda path: op.open(urllib.request.Request(base + path, headers=H), timeout=15).read().decode("utf-8", "replace")
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        # 6. the manual in five languages
        h = get("/help")
        pruef(h.count("🎓 Experte") == 1 and "🎓 Expert»" in h and "Darstellung &amp; Sprache → Symbole" in h, "Anleitung Deutsch / Englisch: der neue Absatz")
        pruef("Menü «Darstellung» mit Symbole" not in h, "Anleitung: der alte Absatz («Menü Darstellung») ist weg")
        for L, w in (("fr", "Ma vue"), ("it", "La mia vista"), ("rm", "Mia vista")):
            js = get("/i18n/%s.js?h=1" % L)
            pruef("🎓" in js and "⇕" in js and w in js, "Anleitung %s: der neue Absatz in «Tipps & Tricks»" % L)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            for name, kw in (("handy", dict(dev)), ("pc", {"viewport": {"width": 1280, "height": 800}})):
                ctx = br.new_context(http_credentials={"username": "admin", "password": PASSWORT}, **kw)
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-icons','color')}catch(e){}")
                pg = ctx.new_page(); jsf = []
                pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                # 1. every page: no row
                for path in ("/settings", "/protect", "/", "/more", "/recordings", "/sim", "/fav"):
                    pg.goto(base + path, wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
                    l = pg.evaluate(LAGE)
                    pruef(l["host"] in ("subnav", "status", "kopf") and not l["row"] and not l["oldseg"] and l["inside"] and l["doc"] <= (391 if name == "handy" else 1281),
                          "%s %s: keine Leiste unter den Reitern, Werkzeuge in der %s-Zeile (%s)" % (name, path, l["host"], l))
                    if path in ("/", "/more"):
                        pruef(l["mode"] is None, "%s %s: nur eine Ansicht = kein Knopf Einfach / Experte" % (name, path))
                    if path == "/settings" and a.bilder:
                        pg.screenshot(path=os.path.join(a.bilder, "leiste_%s_einstellungen.png" % name))
                # 2. the toggle
                pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
                l = pg.evaluate(LAGE)
                pruef(l["host"] == "subnav" and l["find"] and l["mode"] and "Experte" in l["mode"] and l["pressed"] == "true",
                      "%s Einstellungen: «🎓 Experte» neben 🔍, aria-pressed=true (%s)" % (name, l))
                with pg.expect_navigation(timeout=20000):
                    pg.click("#mwb-mode")
                pg.wait_for_timeout(2500)
                l = pg.evaluate(LAGE)
                sv = json.loads(get("/api/ui_simple?page=settings")).get("on")
                pruef(l["mode"] == "Einfach" and l["pressed"] == "false" and sv is True, "%s: ein Tipp = «Einfach» (gespeichert: %s)" % (name, sv))
                with pg.expect_navigation(timeout=20000):
                    pg.click("#mwb-mode")
                pg.wait_for_timeout(2500)
                pruef(pg.evaluate(LAGE)["pressed"] == "true", "%s: noch ein Tipp = wieder «🎓 Experte»" % name)
                # 5. the symbols row
                pg.wait_for_selector("#ms-list .mi[data-ms='#mwb-icons-card']", timeout=15000)
                st = pg.evaluate("() => { const r = document.querySelector('#ms-list .mi[data-ms=\"#mwb-icons-card\"]'); return [r.closest('.mg').querySelector('.mgh').textContent, r.querySelector('.ms-st').textContent]; }")
                pruef(st == ["Darstellung & Sprache", "farbig"], "%s: Zeile «Symbole» unter Darstellung & Sprache, Zustand farbig (%s)" % (name, st))
                pg.locator("#ms-list .mi[data-ms='#mwb-icons-card']").click(); pg.wait_for_timeout(600)
                pg.locator("#mwb-icons-card .mwb-seg button").last.click(); pg.wait_for_timeout(400)
                pruef(pg.evaluate("() => document.body.classList.contains('icplain')"), "%s: «schlicht» gewählt (body.icplain)" % name)
                pg.locator("#ms-back").click(); pg.wait_for_timeout(1500)
                st = pg.evaluate("() => document.querySelector('#ms-list .mi[data-ms=\"#mwb-icons-card\"] .ms-st').textContent")
                pruef(st == "schlicht", "%s: die Zeile zeigt «schlicht»" % name)
                pg.evaluate("() => MWB.setIcons('color')")
                # 4. Live: ⇕
                pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(3500)
                pg.evaluate("() => ['g2-ov','g2-spot','g2-bub','gd-card'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); })")
                l = pg.evaluate(LAGE)
                pruef(l["fold"], "%s Live: «⇕» da (%s)" % (name, l))
                pg.click("#mwb-fold"); pg.wait_for_timeout(400)
                m = pg.evaluate("() => [...document.querySelectorAll('#mwb-vpop button')].filter(b => !b.hidden).map(b => b.id)")
                pruef(m == ["all-close", "all-mine", "all-open"], "%s Live: Alle zuklappen · Meine Ansicht · Alle aufklappen (%s)" % (name, m))
                if a.bilder:
                    pg.screenshot(path=os.path.join(a.bilder, "leiste_%s_live.png" % name))
                pg.click("#all-close"); pg.wait_for_timeout(500)
                op_ = pg.evaluate("() => [...document.querySelectorAll('main details:not(#g2-tt)')].filter(d => d.getClientRects().length).map(d => d.open)")
                pruef(op_ and not any(op_), "%s Live: «Alle zuklappen» klappt zu (%s)" % (name, op_))
                pg.click("#mwb-fold"); pg.wait_for_timeout(300)
                b = pg.locator("#all-mine").bounding_box()
                pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(900); pg.mouse.up(); pg.wait_for_timeout(500)
                tops = pg.evaluate("""() => [...document.querySelectorAll('main details:not(#g2-tt)')].filter(d => d.getClientRects().length && !d.parentElement.closest('details')).map(d => d.open)""")
                pruef(tops and all(tops), "%s Live: langes Drücken auf «Meine Ansicht» = die Gruppen offen (%s)" % (name, tops))
                pruef(not jsf, "%s: keine JavaScript-Fehler %s" % (name, jsf[:3]))
                ctx.close()
            br.close()
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
    teil_fenster(datei)
    print("Leiste-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
