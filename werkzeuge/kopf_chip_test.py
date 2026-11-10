#!/usr/bin/env python3
"""Test «Kopf-Chip alles ok» (Teil 530, compactHeader): «✓ alles ok» nur, wenn kein Chip warnt.

Hintergrund (3.72): der Chip erschien, sobald EIN Wert normal war - auch neben «🩺 2» (Selbstdiagnose) und «Wind: stark».
Jetzt: kein Warn-Chip sichtbar -> «✓ alles ok» (grün); sonst «N Hinweis(e)» (neutral), Antippen zeigt weiter alle Werte.
Zustands-Chips (Aufnahme, Lampe, von Hand, Bedienermodus …) zählen nicht als Warnung.

Startet MoveEye ohne Fenster mit der Demo und prüft mit Playwright (iPhone). Die Chips werden in EINEM Schritt gesetzt und
compactHeader() direkt aufgerufen (kein Warten auf zufällige Zustände der Demo); dazu der echte Zustand der Demo.

  python3 werkzeuge/kopf_chip_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos kopfchip_*.png
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
PASSWORT = "Kopfchip-" + base64.b16encode(os.urandom(5)).decode().lower()

# setzt die Chips (id -> Klasse, "" = normal sichtbar, null = versteckt), ruft compactHeader und liest den Chip
SETZEN = """([chips, extra]) => {
  const s = Object.assign({}, window.__lastState || {}, {persons: 0, fog: false}, extra || {});
  document.querySelectorAll('header .chips .badge').forEach(b => { if (b.id !== 'b-ok' && b.id !== 'b-arm') { b.hidden = true; b.classList.remove('red', 'yel', 'org', 'vh'); } });
  Object.entries(chips).forEach(([id, cls]) => { const b = document.getElementById(id); b.hidden = false; if (cls) b.classList.add(cls);
    if (id === 'b-wind') b.textContent = 'Wind: stark'; if (id === 'b-health') b.textContent = '🩺 2'; });
  document.querySelector('header').classList.remove('hx');
  ['g2-ov', 'g2-spot', 'g2-bub', 'gd-card'].forEach(i => { const e = document.getElementById(i); if (e) e.style.display = 'none'; });
  compactHeader(s, {eco_fps: 2});
  const ok = document.getElementById('b-ok');
  return {text: ok.textContent, hidden: ok.hidden, grn: ok.classList.contains('grn'), warn: hdrWarnChips(s).map(b => b.id)};
}"""


def main():
    ap = argparse.ArgumentParser(description="Kopf-Chip «alles ok» / «N Hinweise»")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5141)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (kopfchip_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_kopfchip_")
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
        # die neuen Texte in allen Sprachen (fr / it / rm über /i18n/<sprache>.js, Deutsch in der Seite)
        for lang in ("fr", "it", "rm"):
            js = op.open(base + "/i18n/%s.js" % lang, timeout=10).read().decode("utf-8", "replace")
            pruef('"hint":' in js and '"hints":' in js, "Texte «hint» / «hints» in %s" % lang)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3,
                                 http_credentials={"username": "admin", "password": PASSWORT})
            pg = ctx.new_page()
            jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            lauf(pg, a, pruef, base)
            pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close(); br.close()
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
    print("Kopf-Chip-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def lauf(pg, a, pruef, base):
    def weg():
        for _ in range(3):
            pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
            pg.wait_for_timeout(300)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")

    def foto(name):
        if a.bilder:                                         # sofort (die nächste Abfrage der Seite setzt die Chips wieder echt)
            pg.screenshot(path=os.path.join(a.bilder, "kopfchip_%s.png" % name), clip={"x": 0, "y": 0, "width": 390, "height": 200})

    pg.goto(base + "/", wait_until="domcontentloaded")
    t_ = time.time() + 30
    while time.time() < t_ and not pg.evaluate("() => !!(window.__lastState && window.__lastState.health && typeof compactHeader === 'function' && typeof hdrWarnChips === 'function')"):
        pg.wait_for_timeout(300)
    weg()
    # ---- echter Zustand der Demo: nie «alles ok» neben einem Warn-Chip ----------------------------------------------------------
    for _ in range(12):
        r = pg.evaluate("""() => { const ok = document.getElementById('b-ok'), w = hdrWarnChips(window.__lastState || {});
            return {text: ok.textContent, hidden: ok.hidden, n: +ok.dataset.warn, warn: w.map(b => b.id + ':' + b.textContent.trim())}; }""")
        if r["warn"]:
            break
        pg.wait_for_timeout(1000)
    print("  Demo: Warn-Chips %s, Chip «%s»" % (r["warn"], r["text"]), flush=True)
    if r["warn"]:
        pg.wait_for_timeout(1200)
        r = pg.evaluate("""() => { const ok = document.getElementById('b-ok'), w = hdrWarnChips(window.__lastState || {}); return {text: ok.textContent, hidden: ok.hidden, n: w.length}; }""")
        pruef(r["hidden"] or "alles ok" not in r["text"], "Demo mit Warn-Chip: kein «alles ok» (Chip «%s», %d Warn-Chips)" % (r["text"], r["n"]))
        foto("demo_hinweise")

    def fall(name, chips, extra, text, grn, bild=""):
        r_ = pg.evaluate(SETZEN, [chips, extra])
        if bild:
            foto(bild)
        pruef(not r_["hidden"] and r_["text"] == text and r_["grn"] == grn, "%s -> «%s»%s (ist «%s», grün %s, Warn-Chips %s)"
              % (name, text, " grün" if grn else "", r_["text"], r_["grn"], r_["warn"]))

    N = {"b-cpu": "", "b-fps": ""}                               # zwei normale Werte: der Chip hat etwas zu verstecken
    fall("alles normal", N, None, "✓ alles ok", True, "alles_ok")
    fall("Selbstdiagnose rot", dict(N, **{"b-health": "red"}), None, "1 Hinweis", False)
    fall("Selbstdiagnose + Wind stark", dict(N, **{"b-health": "red", "b-wind": "yel"}), None, "2 Hinweise", False, "2_hinweise")
    fall("nur Wind", dict(N, **{"b-wind": "yel"}), None, "1 Hinweis", False)
    fall("kein Passwort / Unterspannung", dict(N, **{"b-sec": "yel", "b-pwr": "red"}), None, "2 Hinweise", False)
    fall("CPU rot (ein Wert ausserhalb)", {"b-cpu": "red", "b-fps": ""}, None, "1 Hinweis", False)
    fall("Person erkannt", dict(N, **{"b-person": "red"}), {"persons": 1}, "1 Hinweis", False)
    fall("Akku tief", dict(N, **{"b-batt": "yel"}), None, "1 Hinweis", False)
    fall("nur Zustände (Aufnahme, Lampe, von Hand, Bedienermodus, abwesend)", dict(N, **{"b-rec": "red", "b-lights": "yel", "b-pat": "yel", "b-lock": "yel", "b-pres": "org"}),
         None, "✓ alles ok", True)
    fall("wenig Licht (Zustand)", dict(N, **{"b-light": "yel"}), None, "✓ alles ok", True)
    fall("Nebel (Sicht eingeschränkt)", dict(N, **{"b-light": "yel"}), {"fog": True}, "1 Hinweis", False)
    # Antippen zeigt weiter alle Werte - auch mit Hinweisen
    pg.evaluate(SETZEN, [dict(N, **{"b-health": "red"}), None])
    r = pg.evaluate("""() => { const ok = document.getElementById('b-ok'), H = document.querySelector('header'); ok.click();
        const a = {text: ok.textContent, hx: H.classList.contains('hx'), cpu: getComputedStyle(document.getElementById('b-cpu')).display};
        ok.click(); return [a, {text: ok.textContent, hx: H.classList.contains('hx'), cpu: getComputedStyle(document.getElementById('b-cpu')).display}]; }""")
    pruef(r[0]["hx"] and r[0]["text"] == "✓ einklappen" and r[0]["cpu"] != "none", "Antippen mit Hinweis: Werte aufgeklappt, «✓ einklappen» (%s)" % r[0])
    pruef(not r[1]["hx"] and r[1]["text"] == "1 Hinweis" and r[1]["cpu"] == "none", "nochmals: zu, wieder «1 Hinweis» (%s)" % r[1])


if __name__ == "__main__":
    sys.exit(main())
