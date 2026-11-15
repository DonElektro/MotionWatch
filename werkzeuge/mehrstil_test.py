#!/usr/bin/env python3
"""Test «Mehr-Stil» (Teil 639zzzg): Zeilen statt Karten, eine Unterseite pro Thema, richtige Zustände.

Startet MoveEye ohne Fenster mit der Demo (eigener Ordner, freier Port) und prüft mit Playwright (iPhone 13):
  1. Einstellungen / Schutz / Kameras / Sim / Verlauf: Gruppen-Titel ausserhalb, Zeilen mit Titel, Zeile darunter, ›;
     die Gruppen haben KEINEN Zustand (kein «an» / «aus» bei einem Gruppen-Titel, keine alten Zustandswörter sichtbar)
  2. ein Tipp öffnet die eigene Unterseite (Titel oben, «‹ Zurück»), Zurück und Browser-Zurück gehen zur Liste;
     alte Links ?open=sec:… und #s=… öffnen die Unterseite; 🔍 sucht in allen Zeilen
  3. ZUSTÄNDE: jede Einstellung wird umgeschaltet (/api/set, /api/text), die Seite neu geladen, und das Zustandswort
     der Zeile muss passen – und zu dem, was der Schalter der Seite zeigt (z. B. Updates «automatisch» / «von Hand» /
     «Entwickler», Kopf «folgt Personen» / «bereit», Push «nicht eingerichtet» statt «an»)
  4. Schutz: oben Aus / Wachsam / Voll mit Statuszeile, Modus-Karte (mit dem Glut-Wächter darin)
  5. Live: nur «Gehtest» und «Tipps & Tricks» als Zeilen unten, Unterseite und zurück; sonst bleibt Live wie es war
  6. Pi-Fenster (Ersatz-tkinter): Gruppen-Titel ohne Zustand, Zeilen mit Zustand, Klick = ein Thema mit «‹ Zurück»
  7. keine JavaScript-Fehler

  python3 werkzeuge/mehrstil_test.py [--datei X.py] [--bilder ORDNER]
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
PASSWORT = "Stil-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


# (page, row, how, key, [(value, expected label regex, what the switch of the page shows or None)])
FLIPS = [
    ("settings", "sec:Patrol", "set", "patrol", [(True, r"^an$"), (False, r"^aus$")]),
    ("settings", "sec:Timelapse", "set", "timelapse_on", [(True, r"^an$"), (False, r"^aus$")]),
    ("settings", "sec:Window to the past", "set", "zf_on", [(False, r"^aus$"), (True, r"^an$")]),
    ("settings", "sec:Detection", "set", "detection_on", [(False, r"^aus$"), (True, r"^an$")]),
    ("settings", "sec:Vehicle filter", "set", "car_filter", [(False, r"^aus$"), (True, r"^an$")]),
    ("settings", "sec:Rain", "set", "rain_auto", [(False, r"^aus$"), (True, r"^automatisch$")]),
    ("settings", "sec:Wind", "set", "wind_auto", [(False, r"^aus$"), (True, r"^automatisch$")]),
    ("settings", "sec:Auto-tune", "set", "auto_tune", [(False, r"^aus$"), (True, r"^an$")]),
    ("settings", "sec:Clap switch", "set", "clap_on", [(True, r"^an$"), (False, r"^aus$")]),
    ("settings", "sec:Wake-up alarm", "set", "wake_on", [(True, r"^an$"), (False, r"^aus$")]),
    ("settings", "sec:Power saving", "set", "eco_on", [(True, r"^(an|spart gerade)$"), (False, r"^aus$")]),
    ("settings", "sec:Bless you", "set", "sneeze_on", [(True, r"^an$"), (False, r"^aus$")]),
    ("settings", "sec:Camera / Servos", "set", "track_person", [(False, r"^bereit$"), (True, r"^folgt Personen$")]),
    ("settings", "sec:AI detection", "set", "ai_enabled", [(False, r"^aus$"), (True, r"^(an|Modell fehlt)$")]),
    ("settings", "sec:Storm warning", "set", "storm_on", [(False, r"^aus$"), (True, r"^(an|kein Fühler)$")]),
    ("settings", "sec:Updates", "text", "update_mode", [("auto", r"^automatisch( · keine Quelle)?$"), ("off", r"^von Hand( · keine Quelle)?$"),
                                                         ("dev", r"^Entwickler( · keine Quelle)?$")]),
    ("protect", "sec:Recording", "set", "record", [(False, r"^aus$"), (True, r"^an$")]),
    ("protect", "report", "set", "report_on", [(False, r"^aus$"), (True, r"^an$")]),
    ("protect", "sec:Theft protection", "set", "tamper_on", [(False, r"^aus$"), (True, r"^an$")]),
    ("protect", "sec:Notifications", "set", "notify_on", [(False, r"^aus$"), (True, r"^(an|nicht eingerichtet|pausiert|Ruhezeit)$")]),
]
# the rucksack key is put together (639zzy: the old name never as one text in the source)
FLIPS.append(("settings", "sec:File " + "ex" "change", "set", "tausch_on", [(False, r"^aus$"), (True, r"^an$")]))

ROWS = """() => { const L = document.getElementById('ms-list'); if (!L) return null;
  const vis = e => !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  return {groups: [...L.querySelectorAll('.mg')].filter(vis).map(g => ({h: g.querySelector('.mgh').textContent, hst: g.querySelector('.mgh .ms-st, .mgh .mst') ? 1 : 0,
            rows: [...g.querySelectorAll('.mi')].filter(vis).map(m => ({id: m.dataset.ms, b: m.querySelector('b').textContent, small: (m.querySelector('small') || {}).textContent || '',
                   st: (m.querySelector('.ms-st') || {}).textContent || '', ar: !!m.querySelector('.ar')}))})),
          oldst: [...document.querySelectorAll('.mst')].filter(vis).map(e => e.textContent)}; }"""
STATE_OF = """id => { const m = [...document.querySelectorAll('#ms-list .mi')].find(x => x.dataset.ms === id); return m && !m.hidden ? (m.querySelector('.ms-st') || {}).textContent : null; }"""
SWITCH_OF = """k => { try { const x = ctrl[k]; if (x && x.input) return x.type === 'bool' ? x.input.checked : x.input.value; } catch (e) {}
  const s = document.querySelector('select[data-key="' + k + '"]'); return s ? s.value : null; }"""


def warte(pg, sel, t=20):
    t_ = time.time() + t
    while time.time() < t_:
        if pg.evaluate("s => !!document.querySelector(s)", sel):
            return True
        pg.wait_for_timeout(300)
    return False


def laden(pg, url, sel="#ms-list .mi"):
    pg.goto(url, wait_until="domcontentloaded")
    ok = warte(pg, sel)
    pg.wait_for_timeout(1800)                              # one state paint (every 1 s) after the page values are there
    return ok


def teil_web(pg, base, a):
    # 1. the pages: rows, groups without state
    for path, page in (("/settings", "settings"), ("/protect", "protect"), ("/cams", "cams"), ("/sim", "sim"), ("/recordings", "history")):
        laden(pg, base + path)
        r = pg.evaluate(ROWS)
        n = sum(len(g["rows"]) for g in r["groups"]) if r else 0
        pruef(bool(r) and n >= (8 if page in ("settings", "protect") else 1) and all(x["b"] and x["ar"] for g in r["groups"] for x in g["rows"]),
              "%s: Zeilen mit Titel und › (%d Zeilen in %d Gruppen)" % (path, n, len(r["groups"]) if r else 0))
        pruef(bool(r) and not any(g["hst"] for g in r["groups"]) and not any(re.search(r"\b(an|aus)$", g["h"]) for g in r["groups"]) and not r["oldst"],
              "%s: Gruppen-Titel ohne Zustand, keine alten Zustandswörter (%s)" % (path, [g["h"] for g in r["groups"]][:9]))
        if a.bilder:
            pg.screenshot(path=os.path.join(a.bilder, "mehrstil_%s.png" % page), full_page=True)
    # 2. a subpage, back, the browser back, the old links, the search
    laden(pg, base + "/settings")
    pg.locator('#ms-list .mi[data-ms="sec:Updates"]').click(); pg.wait_for_timeout(700)
    s = pg.evaluate("() => [document.body.classList.contains('ms-sub'), document.querySelector('#ms-bar b').textContent, location.hash, "
                    "!!document.querySelector('#ms-page [data-view=\"sec:Updates\"]'), !!document.getElementById('ms-back').getClientRects().length]")
    pruef(s[0] and s[1] == "Updates" and s[2].startswith("#s=") and s[3] and s[4], "Tipp auf «Updates»: eigene Unterseite mit «‹ Zurück» (%s)" % s)
    if a.bilder:
        pg.screenshot(path=os.path.join(a.bilder, "mehrstil_unterseite.png"), full_page=True)
    pg.locator("#ms-back").click(); pg.wait_for_timeout(600)
    s = pg.evaluate("() => [document.body.classList.contains('ms-sub'), !!document.querySelector('#settings [data-view=\"sec:Updates\"]'), location.hash]")
    pruef(not s[0] and s[1] and not s[2], "«‹ Zurück»: wieder die Liste, das Thema an seinem Platz (%s)" % s)
    pg.locator('#ms-list .mi[data-ms="sec:Patrol"]').click(); pg.wait_for_timeout(500); pg.go_back(); pg.wait_for_timeout(700)
    pruef(not pg.evaluate("() => document.body.classList.contains('ms-sub')"), "Browser-Zurück: wieder die Liste")
    laden(pg, base + "/settings?open=sec:Updates"); pg.wait_for_timeout(1500)
    pruef(pg.evaluate("() => document.body.classList.contains('ms-sub') && document.querySelector('#ms-bar b').textContent === 'Updates'"),
          "alter Link ?open=sec:Updates öffnet die Unterseite")
    laden(pg, base + "/settings#s=" + "sec%3APatrol")
    for _w in range(10):
        if pg.evaluate("() => document.body.classList.contains('ms-sub')"):
            break
        pg.wait_for_timeout(400)
    pruef(pg.evaluate("() => document.body.classList.contains('ms-sub') && !!document.querySelector('#ms-page [data-view=\"sec:Patrol\"]')"),
          "Link #s=sec:Patrol öffnet die Unterseite")
    laden(pg, base + "/settings")
    pg.locator("#ms-find").click(); pg.locator("#ms-qi").fill("Zeitraffer"); pg.wait_for_timeout(500)
    hits = pg.evaluate("() => [...document.querySelectorAll('#ms-list .mi')].filter(m => !m.hidden).map(m => m.querySelector('b').textContent)")
    pruef("Zeitraffer" in hits and len(hits) <= 4, "🔍 «Zeitraffer»: nur die passenden Zeilen (%s)" % hits)
    pg.locator('#ms-list .mi[data-ms="sec:Timelapse"]').click(); pg.wait_for_timeout(500)
    pruef(pg.evaluate("() => document.body.classList.contains('ms-sub')"), "🔍 Treffer antippen öffnet die Unterseite")
    # 4. Schutz on top
    laden(pg, base + "/protect")
    s = pg.evaluate("""() => { const t = document.getElementById('sk-top'), m = document.getElementById('sk-mode'), l = document.getElementById('ms-list');
        return {btns: t ? t.querySelectorAll('.prt-b').length : 0, status: (document.getElementById('sk-status') || {}).textContent || '',
                order: !!(t && m && l && (t.compareDocumentPosition(m) & 4) && (m.compareDocumentPosition(l) & 4)),
                glut: !!document.querySelector('#sk-mode #glut-box'), tiles: m ? m.querySelectorAll('.mode-grid button').length : 0,
                old: !!document.querySelector('#pr-card') && getComputedStyle(document.querySelector('#pr-card')).display !== 'none'}; }""")
    pruef(s["btns"] == 3 and bool(s["status"]) and s["order"] and s["tiles"] >= 6 and not s["old"],
          "Schutz: oben Aus / Wachsam / Voll mit Statuszeile, dann Modus, dann die Zeilen (%s)" % s)
    pruef(s["glut"], "Schutz: der Glut-Wächter liegt in der Modus-Karte (sichtbar bei Camping / Lagerfeuer)")
    # 5. Live: two rows at the bottom
    laden(pg, base + "/", "#ms-list .mi")
    s = pg.evaluate("""() => { const L = document.getElementById('ms-list'), sec = document.querySelector('main>section');
        const sib = L ? [...L.parentNode.children].filter(c => c.getClientRects().length && c.id !== 'ms-page' && c.id !== 'ms-hide') : [];
        return {last: !!(L && sec && sec.contains(L) && sib[sib.length - 1] === L), rows: [...L.querySelectorAll('.mi')].filter(m => !m.hidden).map(m => m.querySelector('b').textContent),
                video: !!document.getElementById('video') && !!document.getElementById('video').getClientRects().length,
                wt: !!document.querySelector('#ms-hide #wt-card'), tt: !!document.querySelector('#ms-hide #g2-tt')}; }""")
    pruef(s["last"] and any("Gehtest" in x for x in s["rows"]) and any("Tipps" in x for x in s["rows"]) and len(s["rows"]) == 2 and s["video"] and s["wt"] and s["tt"],
          "Live: nur «Gehtest» und «Tipps & Tricks» als Zeilen unten, das Live-Bild bleibt (%s)" % s)
    if a.bilder:
        pg.screenshot(path=os.path.join(a.bilder, "mehrstil_live.png"), full_page=True)
    pg.locator('#ms-list .mi[data-ms="#wt-card"]').click(); pg.wait_for_timeout(600)
    s = pg.evaluate("() => [document.body.classList.contains('ms-sub'), !!document.querySelector('#ms-page #wt-card')]")
    pruef(s[0] and s[1], "Live: «Gehtest» öffnet seine Unterseite")
    pg.locator("#ms-back").click(); pg.wait_for_timeout(600)
    pruef(pg.evaluate("() => !document.body.classList.contains('ms-sub') && !!document.getElementById('video').getClientRects().length"), "Live: Zurück = das Live-Bild wieder da")


def teil_zustand(pg, base, req):
    """3. every setting flipped: the label of its row follows - and matches the switch of the page"""
    for step in range(3):
        todo = [(pg_, row, how, key, vals[step]) for pg_, row, how, key, vals in FLIPS if step < len(vals)]
        for pg_, row, how, key, (v, rx) in todo:
            try:
                r = req("/api/set" if how == "set" else "/api/text", {"key": key, "value": v, "lang": "de"})
            except Exception as e:
                r = {"ok": False, "error": "%s %s" % (e, getattr(e, "read", lambda: b"")()[:200])}
            if r.get("ok") is False:
                pruef(False, "%s = %s setzen (%s)" % (key, v, r))
        time.sleep(1.5)
        for page in ("settings", "protect"):
            mine = [x for x in todo if x[0] == page]
            if not mine:
                continue
            laden(pg, base + "/" + page)
            for _p, row, how, key, (v, rx) in mine:
                st = pg.evaluate(STATE_OF, row)
                sw = pg.evaluate(SWITCH_OF, key)
                same = sw is None or (bool(sw) == bool(v) if isinstance(v, bool) else sw == v)
                pruef(st is not None and bool(re.search(rx, st)) and same,
                      "Zustand %s: %s = %s -> «%s» (Schalter der Seite: %s)" % (row, key, v, st, sw))


FAKE_TK_FROM = os.path.join(HIER, "lupe_test.py")


def teil_fenster(datei):
    """6. the window with the fake tkinter of lupe_test: rows, states, one topic with «‹ Zurück»"""
    print("Pi-Fenster (Ersatz-tkinter)", flush=True)
    src = open(FAKE_TK_FROM, encoding="utf-8").read()
    fake = re.search(r'FAKE_TK = r"""(.*?)"""', src, re.S).group(1)
    exec(fake, {})
    home = tempfile.mkdtemp(prefix="mw_stil_tk_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_stil_tk", "__file__": os.path.abspath(datei)}
    try:
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        App, CFG, STATE, tkm = ns["App"], ns["CFG"], ns["STATE"], sys.modules["tkinter"]
        pruef(App._search is ns["_ms_tk_search"] and App._tab is ns["_ms_tk_tab"], "Fenster: Hüllen um _search und _tab")
        a = object.__new__(App)
        a.root = tkm.Frame(); a.tab = "settings"; a.search_var = tkm.StringVar(value=""); a.search_ph = tkm.Label()
        a.is_shown = lambda v: True
        a._panel = lambda parent: tkm.Frame(parent)
        built, rebuilt = [], []
        a._build_section = lambda sec, body: built.append(sec)
        a._rebuild = lambda: rebuilt.append(1)
        ns["simple_hidden"] = lambda *x: False
        groups = [list(g) for g in ns["TK_GROUPS"] if ns["TK_GROUP_TAB"].get(g[0], "settings") == "settings"]
        inner = tkm.Frame()
        pruef(a._ms_tk_rows(inner, "settings", groups) is True and len(a._ms_rows) >= 15, "Fenster: Einstellungen als Zeilen (%d)" % len(a._ms_rows))
        made = tkm.Button.__mro__[1].made
        heads = [w.cget("text") for w in made if isinstance(w, tkm.Label) and w.master is a._ms_box]
        pruef(heads and not any(re.search(r"\b(an|aus|on|off)$", h) for h in heads), "Fenster: Gruppen-Titel ohne Zustand (%s)" % heads[:6])
        CFG["patrol"] = True; CFG["update_mode"] = "auto"; CFG["update_url"] = "https://example.invalid/v.json"; CFG["track_person"] = False
        STATE["servo_backend"] = "pca9685"
        a._ms_paint()
        st = {sec: lb.cget("text") for sec, lb in a._ms_rows}
        pruef(st.get("Patrol") == ns["tr"]("on") and st.get("Updates") == ns["tr"]("automatic") and st.get("Camera / Servos") == ns["tr"]("ready"),
              "Fenster: Zustände aus der Einstellung (Patrouille %s, Updates %s, Kopf %s)" % (st.get("Patrol"), st.get("Updates"), st.get("Camera / Servos")))
        CFG["patrol"] = False; CFG["update_mode"] = "off"
        a._ms_paint()
        st = {sec: lb.cget("text") for sec, lb in a._ms_rows}
        pruef(st.get("Patrol") == ns["tr"]("off") and st.get("Updates") == ns["tr"]("by hand"), "Fenster: umgeschaltet, der Zustand folgt (%s / %s)" % (st.get("Patrol"), st.get("Updates")))
        a._ms_go("Patrol")
        pruef(a._ms_cur == "Patrol" and rebuilt, "Fenster: Klick auf eine Zeile = dieses Thema (neu aufgebaut)")
        a._ms_tk_rows(tkm.Frame(), "settings", groups)
        backs = [w for w in made if isinstance(w, ns["ttk"].Button) and w.k.get("text") == ns["tr"]("‹ Back")] if hasattr(ns["ttk"], "Button") else []
        pruef(built == ["Patrol"] and getattr(a, "_ms_back", None) is not None, "Fenster: nur dieses Thema, mit «‹ Zurück» (%s)" % built)
        a._ms_back.k.get("command", lambda: None)()
        pruef(a._ms_cur is None, "Fenster: «‹ Zurück» = wieder die Zeilen")
        a.search_var.set("Patrouille" if ns["cur_lang"]() == "de" else "Patrol"); a._ms_tk_rows(tkm.Frame(), "settings", groups); a._search()
        pruef(0 < len(a._ms_rows) <= 3, "Fenster: Suche zeigt nur passende Zeilen (%s)" % [s for s, _ in a._ms_rows])
    except Exception as e:
        import traceback
        traceback.print_exc()
        pruef(False, "Fenster: %s" % e)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Mehr-Stil")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5191)
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
    tmp = tempfile.mkdtemp(prefix="mw_stil_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "patrol": False, "tausch_on": True}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode(), "Content-Type": "application/json"}
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        req = lambda path, d=None: json.loads(op.open(urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None,
                                                                              headers=H), timeout=15).read() or b"{}")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            ctx = br.new_context(http_credentials={"username": "admin", "password": PASSWORT}, **dev)
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de')}catch(e){}")
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            teil_web(pg, base, a)
            teil_zustand(pg, base, req)
            pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
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
    print("Mehr-Stil-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
