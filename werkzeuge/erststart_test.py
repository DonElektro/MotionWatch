#!/usr/bin/env python3
"""Test «Eins nach dem anderen» (Teil 639zzs): beim Öffnen der Startseite ist nie mehr als eines sichtbar.

Startet MoveEye ohne Fenster (Demo-Bild) mit verschiedenen Profilen und schaut mit Playwright in iPhone-Breite (390 × 844)
zu: ein Skript in der Seite merkt sich bei jeder Änderung, welche der sechs Dinge gerade sichtbar sind – Einrichtung (#g2w),
«Neu in dieser Version» (.nws), Rundgang mit Blinki (#g2-bub), Banner «Platz einrichten» (#pl-offer), «Was war das?»
(#alx-what .aw), Tipp des Tages (#g2-tip). Dazu: die kleine Erklär-Karte (#gd-card, 515) liegt nie über einem dieser Fenster.

  1  ganz neu (nichts eingerichtet): nur die Einrichtung, keine «Neu in dieser Version»; der Stand ist danach gemerkt.
  2  neu, eingerichtet (wie die Demo): zuerst der Rundgang, KEINE «Neu in dieser Version»; danach das Banner; die PIN-Frage
     (639zzk) liegt über dem Rundgang und geht; neu laden: kein Rundgang mehr, Banner; «Später» bleibt.
     Die Knöpfe im Live-Bild (639zzj) sind versteckt und kommen mit einem Tipp.
  3  nach einem Update (alte Version gemerkt): zuerst «Neu in dieser Version» allein, nach OK der Rundgang, danach das
     Banner, nach «Später» «Was war das?», kein Tipp des Tages obendrauf; neu laden: nichts davon nochmals, der Tipp des
     Tages kommt jetzt (ruhige Seite).
  4  nach einem Update, Rundgang schon gesehen: «Neu in dieser Version», dann das Banner; «Nicht mehr anzeigen» gilt.

  python3 werkzeuge/erststart_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos erststart_*.png
"""
import argparse
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
FEHLER = []

SEL = {"guide": "#g2w", "news": ".nws", "tour": "#g2-bub", "offer": "#pl-offer", "what": "#alx-what .aw", "tip": "#g2-tip"}
WAECHTER = """(() => {
  const SEL = %s, q = window.__eins = {max: 0, seq: [], both: [], last: null};
  const tick = () => { if (!document.body) return;
    const da = s => [...document.querySelectorAll(s)].some(e => e.getClientRects().length && getComputedStyle(e).visibility !== "hidden");
    const v = Object.keys(SEL).filter(k => da(SEL[k]));
    const karte = da("#gd-card") && v.some(k => k !== "offer" && k !== "what");      // the small card (515) never over a window
    const key = v.join("+"); if (v.length > q.max) q.max = v.length; if (karte) q.max = Math.max(q.max, 2);
    if (v.length > 1 || karte) q.both.push([Math.round(performance.now()), key + (karte ? "+karte" : "")]);
    if (key !== q.last) { q.last = key; q.seq.push([Math.round(performance.now()), key]); } };
  setInterval(tick, 40);
  const start = () => new MutationObserver(tick).observe(document.documentElement, {childList: true, subtree: true, attributes: true, attributeFilter: ["class", "style", "hidden"]});
  if (document.documentElement) start(); else document.addEventListener("readystatechange", start, {once: true});
})();""" % json.dumps(SEL)


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


class Geraet:
    """ein MoveEye ohne Fenster mit eigenem Einstellungs-Ordner"""

    def __init__(self, datei, cfg_extra):
        self.tmp = tempfile.mkdtemp(prefix="mw_erststart_")
        cfg = os.path.join(self.tmp, "mw"); os.makedirs(cfg)
        st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
              "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "https_extra": False}
        st.update(cfg_extra)
        with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); self.port = sk.getsockname()[1]
        self.logf = open(os.path.join(self.tmp, "log.txt"), "w")
        self.p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(self.port), "--bind", "127.0.0.1", "--config", cfg],
                                  stdout=self.logf, stderr=subprocess.STDOUT, cwd=self.tmp)
        self.base = "http://127.0.0.1:%d" % self.port
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(240):
            if self.p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(self.tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)

    def get(self, path):
        with self.op.open(self.base + path, timeout=15) as r:
            return json.loads(r.read())

    def zu(self):
        self.p.terminate()
        try:
            self.p.wait(15)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.logf.close()
        log = open(os.path.join(self.tmp, "log.txt"), errors="replace").read()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:]); FEHLER.append("Traceback im Protokoll von MoveEye")
        shutil.rmtree(self.tmp, ignore_errors=True)


def seite(br, tours_seen=False):
    ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
    ctx.add_init_script("try{localStorage.setItem('mw-lang','de')%s}catch(e){}" % (";localStorage.setItem('mw-tours-seen','[\"live\"]')" if tours_seen else ""))
    ctx.add_init_script(WAECHTER)
    pg = ctx.new_page()
    pg.jsf = []
    pg.on("pageerror", lambda e: pg.jsf.append(str(e)[:300]))
    return ctx, pg


def sicht(pg):
    return pg.evaluate("() => window.__eins.last || ''")


def warte(pg, was, ms=12000):
    """bis genau «was» sichtbar ist ('' = nichts)"""
    t_ = time.time() + ms / 1000.0
    while time.time() < t_:
        if sicht(pg) == was:
            return True
        pg.wait_for_timeout(100)
    return False


def folge(pg):
    return [k for _t, k in pg.evaluate("() => window.__eins.seq") if k]


def nie_zwei(pg, name):
    q = pg.evaluate("() => ({max: window.__eins.max, both: window.__eins.both.slice(0, 5)})")
    pruef(q["max"] <= 1, "%s: nie zwei gleichzeitig sichtbar %s" % (name, q["both"] if q["max"] > 1 else ""))


def bild(pg, a, name):
    if a.bilder:
        pg.screenshot(path=os.path.join(a.bilder, "erststart_%s.png" % name))


def klick(pg, wo, text):
    pg.evaluate("() => { const g = document.querySelector('#gd-card button.ok'); if (g) g.click(); }")   # an explanation card at the bottom (515)
    pg.locator(wo).locator("button, a", has_text=text).first.click()


# ---------------------------------------------------------------------------------------------------------------------- 1
def ganz_neu(datei, br, a):
    print("1) ganz neu: nichts eingerichtet", flush=True)
    g = Geraet(datei, {"setup_done": False})
    try:
        n0 = g.get("/api/news?lang=de")
        pruef(n0.get("fresh") is True and n0.get("show") is True, "neu: der Server meldet «fresh» (noch nie Neuigkeiten gesehen)")
        ctx, pg = seite(br)
        pg.goto(g.base + "/")
        pruef(warte(pg, "guide"), "neu: die Einrichtung erscheint (%s)" % folge(pg))
        pg.wait_for_timeout(5000)
        bild(pg, a, "1_ganz_neu")
        pruef(folge(pg) == ["guide"], "neu: nur die Einrichtung, keine «Neu in dieser Version» (%s)" % folge(pg))
        nie_zwei(pg, "neu")
        n1 = g.get("/api/news?lang=de")
        pruef(n1.get("fresh") is False and n1.get("show") is False, "neu: der Stand ist gemerkt – das nächste Update meldet sich wieder")
        pruef(not pg.jsf, "neu: keine JavaScript-Fehler %s" % pg.jsf[:3])
        ctx.close()
    finally:
        g.zu()


# ---------------------------------------------------------------------------------------------------------------------- 2
def neu_eingerichtet(datei, br, a):
    print("2) neu, eingerichtet (wie die Demo)", flush=True)
    g = Geraet(datei, {"setup_done": True})
    try:
        ctx, pg = seite(br)
        pg.goto(g.base + "/")
        pruef(warte(pg, "tour"), "eingerichtet: zuerst der Rundgang (%s)" % folge(pg))
        pg.wait_for_timeout(4000)
        bild(pg, a, "2_rundgang")
        pruef(folge(pg) == ["tour"], "eingerichtet: keine «Neu in dieser Version», kein Banner solange der Rundgang offen ist (%s)" % folge(pg))
        # the PIN question (639zzk) lies over the tour and works; the tour is still there afterwards
        pg.evaluate("() => { window.__pin = 'offen'; window.mwPinAsk('').then(v => { window.__pin = v; }); }")
        pg.wait_for_selector("#mw-pin-in", timeout=3000)
        oben = pg.evaluate("""() => { const r = document.getElementById('mw-pin-in').getBoundingClientRect();
            const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!e && e.id === 'mw-pin-in'; }""")
        pruef(oben, "PIN-Frage liegt über dem Rundgang")
        pg.fill("#mw-pin-in", "1234"); pg.click("#mw-pin-ok"); pg.wait_for_timeout(300)
        pruef(pg.evaluate("() => window.__pin") == "1234" and sicht(pg) == "tour", "PIN-Frage geht, der Rundgang ist danach noch da")
        klick(pg, "#g2-bub", "Überspringen")
        pruef(warte(pg, "offer"), "eingerichtet: nach dem Rundgang das Banner «Platz einrichten» (%s)" % folge(pg))
        pg.wait_for_timeout(1500)
        bild(pg, a, "2_banner")
        # the clean live picture (639zzj): buttons hidden, one tap shows them
        op = "() => { const e = document.querySelector('#lv-tools'); return e && e.getClientRects().length ? +getComputedStyle(e).opacity : -1; }"
        o0 = pg.evaluate(op)
        bx = pg.locator("#vcard img").first.bounding_box()
        if bx:
            pg.touchscreen.tap(bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] / 2)
        pg.wait_for_timeout(700)
        pruef(o0 == 0 and pg.evaluate(op) > 0.9, "Live-Bild sauber: Knöpfe versteckt (%s), nach einem Tipp da (%s)" % (o0, pg.evaluate(op)))
        nie_zwei(pg, "eingerichtet")
        n1 = g.get("/api/news?lang=de")
        pruef(n1.get("fresh") is False and n1.get("show") is False, "eingerichtet: Stand der Neuigkeiten gemerkt")
        pg.goto(g.base + "/")
        pruef(warte(pg, "offer"), "neu geladen: Banner wieder da")
        pg.wait_for_timeout(3000)
        pruef(folge(pg) == ["offer"], "neu geladen: kein Rundgang, keine Neuigkeiten mehr (%s)" % folge(pg))
        klick(pg, "#pl-offer", "Später")
        pg.wait_for_timeout(800)
        pg.goto(g.base + "/"); pg.wait_for_timeout(5000)
        pruef("offer" not in folge(pg), "«Später» des Banners bleibt (%s)" % folge(pg))
        nie_zwei(pg, "neu geladen")
        pruef(not pg.jsf, "eingerichtet: keine JavaScript-Fehler %s" % pg.jsf[:3])
        ctx.close()
    finally:
        g.zu()


# ---------------------------------------------------------------------------------------------------------------------- 3
def nach_update(datei, br, a):
    print("3) nach einem Update: alte Version gemerkt, Rundgang noch nie gesehen", flush=True)
    g = Geraet(datei, {"setup_done": True, "news_seen_web": "3.70.0"})
    try:
        ctx, pg = seite(br)
        offen = {"n": 1}                                  # one alarm waits for «Was war das?» until it is answered

        def alarm(route):
            if route.request.method == "POST":
                offen["n"] = 0
                return route.fulfill(status=200, content_type="application/json", body='{"ok": true}')
            if "/img/" in route.request.url:
                return route.fulfill(status=404, body="")
            items = [{"id": "t1", "t": time.time() - 60, "label": "", "boxes": [[0.3, 0.3, 0.2, 0.4]]}] * offen["n"]
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(
                {"ok": True, "items": items, "lang": "de", "tx": {"What was it?": "Was war das?", "Person": "Person", "Animal": "Tier", "Nothing": "Nichts"}}))
        pg.route("**/api/alarmlabel**", alarm)
        pg.goto(g.base + "/")
        pruef(warte(pg, "news"), "Update: zuerst «Neu in dieser Version» (%s)" % folge(pg))
        pg.wait_for_timeout(5000)
        bild(pg, a, "3_neu_in_dieser_version")
        pruef(folge(pg) == ["news"], "Update: solange sie offen ist, nichts anderes (%s)" % folge(pg))
        frei = pg.evaluate("""() => { const b = [...document.querySelectorAll('.nws button')].find(x => x.textContent.trim() === 'OK'); b.scrollIntoView({block: 'center'}); const r = b.getBoundingClientRect();
            const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return e === b; }""")
        pruef(frei, "Update: nichts liegt über dem Dialog (OK ist frei)")
        klick(pg, ".nws", "OK")
        pruef(warte(pg, "tour"), "Update: danach der Rundgang (noch nie gesehen) (%s)" % folge(pg))
        pg.wait_for_timeout(2500)
        bild(pg, a, "3_rundgang")
        klick(pg, "#g2-bub", "Überspringen")
        pruef(warte(pg, "offer"), "Update: danach das Banner (%s)" % folge(pg))
        pg.wait_for_timeout(2500)
        bild(pg, a, "3_banner")
        klick(pg, "#pl-offer", "Später")
        pruef(warte(pg, "what", 30000), "Update: danach «Was war das?» (%s)" % folge(pg))
        bild(pg, a, "3_was_war_das")
        klick(pg, "#alx-what", "Nichts")
        pruef(warte(pg, ""), "«Was war das?» beantwortet: weg")
        pg.wait_for_timeout(8000)
        pruef(folge(pg) == ["news", "tour", "offer", "what"], "Update: jedes kam einmal an die Reihe, kein Tipp des Tages obendrauf (%s)" % folge(pg))
        nie_zwei(pg, "Update")
        log = pg.evaluate("() => window.MWQ.log.map(x => x[1] + ':' + x[2])")
        pruef("later:tip" in log or "want:tip" not in log, "Tipp des Tages: auf den nächsten Besuch verschoben (%s)" % [x for x in log if "tip" in x])
        tip = g.get("/api/g2?lang=de").get("tip")
        pg.goto(g.base + "/")
        if tip:
            pruef(warte(pg, "tip", 15000), "nächster Besuch (ruhige Seite): der Tipp des Tages kommt (%s)" % folge(pg))
            bild(pg, a, "3_tipp_des_tages")
        else:
            print("  (kein Tipp des Tages vom Gerät – nicht geprüft)")
            pg.wait_for_timeout(8000)
        pruef(folge(pg) in (["tip"], []), "nächster Besuch: keine Neuigkeiten, kein Rundgang, kein Banner mehr (%s)" % folge(pg))
        nie_zwei(pg, "nächster Besuch")
        pruef(not pg.jsf, "Update: keine JavaScript-Fehler %s" % pg.jsf[:3])
        ctx.close()
    finally:
        g.zu()


# ---------------------------------------------------------------------------------------------------------------------- 4
def update_rundgang_gesehen(datei, br, a):
    print("4) nach einem Update, Rundgang schon gesehen; «Nicht mehr anzeigen»", flush=True)
    g = Geraet(datei, {"setup_done": True, "news_seen_web": "3.70.0"})
    try:
        ctx, pg = seite(br, tours_seen=True)
        pg.goto(g.base + "/")
        pruef(warte(pg, "news"), "Update (Rundgang gesehen): «Neu in dieser Version» (%s)" % folge(pg))
        pg.wait_for_timeout(3000)
        klick(pg, ".nws", "Nicht mehr anzeigen")
        pruef(warte(pg, "offer"), "danach das Banner, kein Rundgang (%s)" % folge(pg))
        pg.wait_for_timeout(2500)
        pruef(folge(pg) == ["news", "offer"], "Reihenfolge: Neuigkeiten, Banner (%s)" % folge(pg))
        nie_zwei(pg, "Update (Rundgang gesehen)")
        n = g.get("/api/news?lang=de")
        pruef(n.get("show") is False, "«Nicht mehr anzeigen» ist auf dem Gerät gemerkt")
        pruef(not pg.jsf, "keine JavaScript-Fehler %s" % pg.jsf[:3])
        ctx.close()
    finally:
        g.zu()


def main():
    ap = argparse.ArgumentParser(description="Eins nach dem anderen (639zzs)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (erststart_*.png)")
    ap.add_argument("--nur", default="", help="nur diese Abschnitte, z. B. 13")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for i, fn in enumerate((ganz_neu, neu_eingerichtet, nach_update, update_rundgang_gesehen), 1):
            if not a.nur or str(i) in a.nur:
                fn(datei, br, a)
        br.close()
    print("Erststart-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)) + " (%.0f s)" % (time.time() - t0))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
