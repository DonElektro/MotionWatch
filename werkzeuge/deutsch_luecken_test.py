#!/usr/bin/env python3
"""Test «deutsche Lücken» (Teil 639zzk): keine englischen Texte im deutschen Web, wo es den deutschen Text gibt.

Hintergrund (3.72): «Play area» (Mehr, zweite Zeile der Reiter), «Build yourself» mit Beschreibung (Mehr), «STATUS LED &
BUTTONS» und «FILE EXCHANGE» (Einstellungen), «Night timeline» (Verlauf) standen im deutschen Web englisch - das Deutsche
gab es in DE, aber nicht in der deutschen Liste der Seite. Jetzt bekommt jede Seite das Deutsche, das ihr fehlt (I18NDX).

Startet MoveEye ohne Fenster mit der Demo und prüft mit Playwright (iPhone, Deutsch):

  1. Die gemeldeten Stellen sind deutsch (Mehr, Einstellungen, Verlauf, Werkzeuge, Anleitung, Spielecke, Bauen).
  2. Alle Seiten: kein Element mit data-i18n zeigt noch seinen englischen Schlüssel, wenn es dafür eine französische
     Übersetzung gibt (dann ist es ein echter Text und kein Name wie «Simulator») - ausser den Wörtern in GLEICH,
     die deutsch und englisch gleich heissen.
  3. Englisch bleibt englisch (kein Deutsch rutscht in die englische Seite), Französisch bleibt französisch.
  4. Keine JavaScript-Fehler.

  python3 werkzeuge/deutsch_luecken_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos deutsch_*.png
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
PASSWORT = "Deutsch-" + base64.b16encode(os.urandom(5)).decode().lower()
SEITEN = ["/", "/protect", "/zones", "/recordings", "/timeline", "/diary", "/messages", "/log", "/settings", "/cams", "/sim", "/more",
          "/play", "/help", "/party", "/tools", "/build", "/quick"]
# deutsch = englisch (kein Fehler, wenn der Schlüssel stehen bleibt)
GLEICH = {"Live", "Simulator", "Sim", "Status", "Test", "Person", "Name", "Start", "Version", "Alarm", "Camping", "Download", "Demo", "Stop",
          "Standard", "Normal", "Info", "OK", "Server", "Position", "Text", "System", "Details", "Online", "Offline", "Turbo", "Disco", "Party",
          "Hotspot", "Feedback", "Trailer", "Software", "Videos", "Badges", "Level", "Port", "Material", "Material:", "Film", "Radio", "Timer", "Wind", "Tunnel", "Reset"}


def main():
    ap = argparse.ArgumentParser(description="keine englischen Texte im deutschen Web")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5145)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (deutsch_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_deutsch_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False}
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
        js = op.open(base + "/i18n/fr.js", timeout=15).read().decode("utf-8", "replace")
        fr = json.loads(js.split("window.I18NX=", 1)[1].split(";window.", 1)[0].replace("<\\/", "</"))
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            lauf(br, a, pruef, base, fr)
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
    print("Deutsch-Lücken-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


# alle Elemente mit data-i18n, die noch ihren Schlüssel zeigen (auch in zugeklappten Karten)
STEHEN = """() => [...new Set([...document.querySelectorAll('[data-i18n]')].filter(e => e.textContent.trim() === e.dataset.i18n && /[A-Za-z]{3}/.test(e.dataset.i18n)).map(e => e.dataset.i18n))]"""


def lauf(br, a, pruef, base, fr):
    jsf = []

    def seite(lang):
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                             http_credentials={"username": "admin", "password": PASSWORT})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
        pg.goto(base + "/more", wait_until="domcontentloaded")      # die Sprache wie der Bediener wählen (langSet merkt sie auch
        pg.wait_for_timeout(1500)                                   # auf dem Gerät; ein Wert nur im Browser würde überschrieben)
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=20000):
            pg.evaluate("k => { langSet(k); }", lang)
        pg.wait_for_timeout(800)
        return ctx, pg

    def gehe(pg, pfad, warte=2200):
        pg.goto(base + pfad, wait_until="domcontentloaded")
        pg.wait_for_timeout(warte)

    def text(pg, sel):
        return pg.evaluate("s => [...document.querySelectorAll(s)].map(e => e.textContent.trim())", sel)

    def foto(pg, name):
        if a.bilder:
            pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            pg.screenshot(path=os.path.join(a.bilder, "deutsch_%s.png" % name))

    # ---- 1. die gemeldeten Stellen --------------------------------------------------------------------------------------------
    ctx, pg = seite("de")
    for pfad in ("/more", "/help", "/party", "/tools", "/build"):
        gehe(pg, pfad)
        sub = text(pg, "nav.subnav a")
        pruef("Spielen" in sub and "Play area" not in sub, "%s: zweite Zeile der Reiter «Spielen» statt «Play area» (%s)" % (pfad, sub))
        if pfad == "/more":
            mi = pg.evaluate("() => { const m = document.getElementById('m-build'); return m ? [m.querySelector('b').textContent, m.querySelector('small').textContent] : null; }")
            pruef(bool(mi) and mi[0] == "Bauen" and "selber" in mi[1].lower() and "yourself" not in mi[1], "/more: «Bauen» mit deutscher Beschreibung (%s)" % mi)
            foto(pg, "mehr")
    for pfad in ("/recordings", "/diary", "/messages", "/log"):
        gehe(pg, pfad)
        sub = text(pg, "nav.subnav a")
        pruef("Zeitleiste" in sub and "Night timeline" not in sub, "%s: «Zeitleiste» statt «Night timeline» (%s)" % (pfad, sub))
    gehe(pg, "/settings", 5000)
    tit = pg.evaluate("() => [...document.querySelectorAll('#settings summary')].map(s => s.textContent.trim())")
    alle = " | ".join(tit)
    pruef("Status-LED & Tasten" in alle and "Status LED & buttons" not in alle, "/settings: «Status-LED & Tasten» statt «Status LED & buttons»")
    pruef("Datentausch" in alle and "File exchange" not in alle, "/settings: «Datentausch» statt «File exchange»")
    if a.bilder:
        pg.evaluate("""() => { const s = [...document.querySelectorAll('#settings summary')].find(x => x.textContent.includes('Status-LED')); if (s) { let d = s.parentElement.parentElement; while (d) { if (d.tagName === 'DETAILS') d.open = true; d = d.parentElement; } s.scrollIntoView({block: 'center'}); } }""")
        pg.wait_for_timeout(500); foto(pg, "einstellungen")
    gehe(pg, "/cams")
    ph = pg.evaluate("() => { const i = document.getElementById('fl-pw'); return i ? i.placeholder : null; }")
    pruef(ph in (None, "Passwort"), "/cams: Platzhalter «Passwort» (%s)" % ph)
    gehe(pg, "/sim", 4000)
    og = pg.evaluate("() => [...document.querySelectorAll('option')].filter(o => o.value === 'game').map(o => o.textContent)")
    pruef(all("verpasste Bilder" in x for x in og), "/sim: Auswahl «verpasste Bilder aus dem Spiel» deutsch (%s)" % og)
    # ---- 2. alle Seiten: kein übersetzbarer Schlüssel bleibt stehen -----------------------------------------------------------
    rest = {}
    for pfad in SEITEN:
        gehe(pg, pfad, 3000 if pfad in ("/", "/settings", "/sim", "/protect") else 1800)
        for k in pg.evaluate(STEHEN):
            if k not in GLEICH and fr.get(k) and fr[k] != k:
                rest.setdefault(k, []).append(pfad)
    for k, wo in sorted(rest.items()):
        print("    englisch geblieben: «%s» (%s)" % (k[:90], ", ".join(wo[:6])), flush=True)
    pruef(not rest, "alle %d Seiten: kein Text mit Übersetzung bleibt englisch stehen (%d)" % (len(SEITEN), len(rest)))
    ctx.close()
    # ---- 3. Englisch bleibt englisch, Französisch französisch --------------------------------------------------------------------
    ctx, pg = seite("en")
    gehe(pg, "/more")
    sub = text(pg, "nav.subnav a")
    mi = pg.evaluate("() => { const m = document.getElementById('m-build'); return m ? m.querySelector('b').textContent : null; }")
    pruef("Play area" in sub and "Spielen" not in sub and mi == "Build yourself", "Englisch: «Play area», «Build yourself» bleiben (%s, %s)" % (sub, mi))
    gehe(pg, "/settings", 5000)
    alle = " | ".join(pg.evaluate("() => [...document.querySelectorAll('#settings summary')].map(s => s.textContent.trim())"))
    pruef("Status LED & buttons" in alle and "Status-LED" not in alle and "Datentausch" not in alle, "Englisch: Einstellungen ohne deutsche Titel")
    ctx.close()
    ctx, pg = seite("fr")
    gehe(pg, "/more")
    sub = text(pg, "nav.subnav a")
    pruef("Jouer" in sub and "Spielen" not in sub, "Französisch: «Jouer» (%s)" % sub)
    ctx.close()
    pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])


if __name__ == "__main__":
    sys.exit(main())
