#!/usr/bin/env python3
"""Test «Sprachen-Rundgang» (Teil 639zzm): Französisch, Italienisch und Romanisch am Handy.

Hintergrund (Prüfung Punkt 7): rund 300 Texte pro Sprache fehlten und sind jetzt übersetzt. Übersetzungen sind oft länger
als das Deutsche - dieser Test geht mit iPhone-Breite durch die Hauptreiter und die Einstellungen und prüft pro Sprache:

  1. Kein Platzhalter steht wörtlich da («{0}», «{n}», «%s», «%d»; ausser den erklärten der eigenen Push-Texte, «{name}» …)
     und kein Schlüssel-Name («usb-note», «dev-law»).
  2. Kein Text ragt deutlich aus seinem Knopf / Reiter (scrollWidth gegen clientWidth), wo er es auf Deutsch nicht tut.
  3. Die Seite wird nicht breiter als das Handy (kein seitliches Scrollen), wo sie es auf Deutsch nicht ist.
  4. Stichproben: einige der neu übersetzten Texte erscheinen in der Sprache (nicht englisch / deutsch).
  5. Keine JavaScript-Fehler.

  python3 werkzeuge/sprachen_tour_test.py [--datei X.py] [--bilder ORDNER] [--sprachen fr,it,rm]
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
PASSWORT = "Sprachen-" + base64.b16encode(os.urandom(5)).decode().lower()
SEITEN = ["/", "/protect", "/recordings", "/timeline", "/diary", "/messages", "/log", "/settings", "/cams", "/zones", "/sim", "/more",
          "/play", "/party", "/tools", "/build", "/help", "/quick"]
BILDER = ["/", "/protect", "/settings", "/tools", "/more", "/sim"]
TOLERANZ = 6                        # px, die ein Text aus seinem Knopf ragen darf

# was ein Knopf / Reiter ist; sichtbar, mit Text; ragt der Text heraus? (auch in aufgeklappten Karten)
MESSEN = r"""(tol) => {
  const out = [];
  const sel = 'button, a.btn, nav a, .tabs a, .tabs button, .dtabs button, .seg button, summary, .chip, label.opt > span, th';
  for (const e of document.querySelectorAll(sel)) {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const tx = (e.textContent || '').trim().replace(/\s+/g, ' ');
    if (!tx) continue;
    const dx = e.scrollWidth - e.clientWidth;
    if (dx > tol && cs.overflowX !== 'auto' && cs.overflowX !== 'scroll')
      out.push({k: (e.id ? '#' + e.id : e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '')) + '|' + (e.dataset.i18n || ''), t: tx.slice(0, 60), dx: dx, w: e.clientWidth});
  }
  const de = document.documentElement;
  return {over: out, seite: de.scrollWidth - de.clientWidth};
}"""

# sichtbarer Text mit einem wörtlichen Platzhalter oder einem Schlüssel-Namen
WOERTLICH = r"""() => {
  const out = [], w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const erkl = /\{(name|time|date|count|camera|link|db)\}/g;     // die erklärten Platzhalter der eigenen Push-Texte (Anleitung, Einstellungen)
  const ph = /\{\d+\}|\{[a-z_]{1,12}\}|%[sd]\b|%\([a-z_]+\)[sd]/, key = /^[a-z0-9]{2,8}(-[a-z0-9]{2,10}){1,2}$/;
  while (w.nextNode()) {
    const n = w.currentNode, p = n.parentElement;
    if (!p || /^(SCRIPT|STYLE|TEXTAREA|CODE|PRE|KBD)$/.test(p.tagName) || p.closest('code, pre, kbd, textarea')) continue;
    const t = n.nodeValue.trim();
    if (!t) continue;
    if (ph.test(t.replace(erkl, ''))) out.push('Platzhalter: ' + t.slice(0, 70));
    else if (key.test(t) && p.dataset && p.dataset.i18n === t) out.push('Schlüssel: ' + t);
  }
  for (const e of document.querySelectorAll('input[placeholder], textarea[placeholder]')) if (ph.test(e.placeholder.replace(erkl, ''))) out.push('Platzhalter: ' + e.placeholder.slice(0, 70));
  return [...new Set(out)];
}"""

# Stichproben der neu übersetzten Texte: (Seite, englischer Schlüssel)
PROBEN = [("/tools", "bt-note"), ("/tools", "Scan (10 s)"), ("/tools", "usb-note"), ("/tools", "Game collection"), ("/tools", "Network and internet"),
          ("/settings", "Trusted devices")]


def main():
    ap = argparse.ArgumentParser(description="Französisch / Italienisch / Romanisch am Handy: nichts ragt heraus, kein Platzhalter")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5146)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (sprache_<lang>_<seite>.png)")
    ap.add_argument("--sprachen", default="fr,it,rm")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_sprachen_")
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
        for _i in range(300):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        tx = {}
        for L in a.sprachen.split(","):
            js = op.open(base + "/i18n/%s.js" % L, timeout=30).read().decode("utf-8", "replace")
            tx[L] = json.loads(js.split("window.I18NX=", 1)[1].split(";window.", 1)[0].replace("<\\/", "</"))
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            lauf(br, a, pruef, base, tx)
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
    print("Sprachen-Rundgang " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def lauf(br, a, pruef, base, tx):
    jsf = []

    def seite(lang):
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                             http_credentials={"username": "admin", "password": PASSWORT})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: jsf.append(lang + ": " + str(e)[:300]))
        pg.goto(base + "/more", wait_until="domcontentloaded")      # die Sprache wie der Bediener wählen (langSet)
        pg.wait_for_timeout(1500)
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            pg.evaluate("k => { langSet(k); }", lang)
        pg.wait_for_timeout(800)
        return ctx, pg

    def gehe(pg, pfad):
        pg.goto(base + pfad, wait_until="domcontentloaded")
        pg.wait_for_timeout(3500 if pfad in ("/", "/settings", "/sim", "/protect", "/tools") else 1800)
        # der Rundgang für Neue würde Knöpfe verdecken; in den Einstellungen und Werkzeugen alle Karten aufklappen
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
        if pfad in ("/settings", "/tools", "/sim", "/protect", "/more"):
            pg.evaluate("() => { document.querySelectorAll('details').forEach(d => { d.open = true; }); }")
            pg.wait_for_timeout(900)

    def messen(pg):
        m = pg.evaluate(MESSEN, TOLERANZ)
        return {x["k"]: x for x in m["over"]}, m["seite"]

    # ---- Deutsch als Vergleich: was dort schon herausragt, ist keine Frage der Übersetzung ------------------------------------
    ctx, pg = seite("de")
    de = {}
    for pfad in SEITEN:
        gehe(pg, pfad)
        de[pfad] = messen(pg)
    ctx.close()
    print("  Deutsch als Vergleich: %d Seiten, %d Stellen ragen dort schon heraus" % (len(de), sum(len(v[0]) for v in de.values())), flush=True)

    for L in a.sprachen.split(","):
        ctx, pg = seite(L)
        ragt, breit, wort = [], [], []
        for pfad in SEITEN:
            gehe(pg, pfad)
            over, sw = messen(pg)
            for k, x in over.items():
                alt = de[pfad][0].get(k)
                if not alt or x["dx"] > alt["dx"] + TOLERANZ:
                    ragt.append("%s  «%s»  +%d px (Breite %d)" % (pfad, x["t"], x["dx"], x["w"]))
            if sw > max(de[pfad][1], 0) + TOLERANZ:
                breit.append("%s (+%d px)" % (pfad, sw))
            wort += [pfad + "  " + w for w in pg.evaluate(WOERTLICH)]
            if a.bilder and pfad in BILDER:
                pg.screenshot(path=os.path.join(a.bilder, "sprache_%s_%s.png" % (L, pfad.strip("/") or "live")))
                if pfad in ("/settings", "/tools"):
                    pg.screenshot(path=os.path.join(a.bilder, "sprache_%s_%s_ganz.png" % (L, pfad.strip("/"))), full_page=True)
        for z in ragt[:40]:
            print("    ragt heraus: " + z, flush=True)
        for z in wort[:40]:
            print("    wörtlich: " + z, flush=True)
        pruef(not wort, "%s: kein Platzhalter und kein Schlüssel-Name wörtlich (%d)" % (L, len(wort)))
        pruef(not ragt, "%s: kein Text ragt aus Knopf / Reiter, wo er es auf Deutsch nicht tut (%d)" % (L, len(ragt)))
        pruef(not breit, "%s: keine Seite breiter als das Handy (%s)" % (L, ", ".join(breit) or "–"))
        # Stichproben: der Text der Sprache steht da
        for pfad, key in PROBEN:
            gehe(pg, pfad)
            soll = tx[L].get(key, "")
            hat = pg.evaluate("s => document.body.textContent.includes(s)", soll) if soll else False
            pruef(bool(soll) and hat, "%s %s: «%s» in der Sprache (%s)" % (L, pfad, key, soll[:50]))
        ctx.close()
    pruef(not jsf, "keine JavaScript-Fehler" + (": " + " | ".join(jsf[:3]) if jsf else ""))


if __name__ == "__main__":
    sys.exit(main())
