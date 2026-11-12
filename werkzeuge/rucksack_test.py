#!/usr/bin/env python3
"""Test «Digitaler Rucksack» (Teil 639zzy): der Bereich «Datentausch» heisst überall neu – in allen fünf Sprachen.

Auftrag des Besitzers (12.11.2026): nur die Anzeige ändert, Adressen (/tausch/…), Schlüssel und Rechte bleiben.

  A) ohne Browser: die Dokumente, die Benutzer lesen (README.md, Anleitung.html, docs/*.md), nennen den alten Namen nicht mehr.
  B) mit Playwright am Handy (390 px), Deutsch / Englisch / Französisch / Italienisch / Romanisch:
     1. Der neue Name steht an jeder Stelle: Kachel unter «Mehr», Überschrift und Titel von /tausch, «‹ …» auf den
        Packlisten, Abschnitt der Einstellungen, Abschnitt der Anleitung.
     2. Kein sichtbarer Text dieser Seiten nennt den alten Namen (auch nicht in einer anderen Sprache). In der Anleitung
        zählt die Liste der Änderungen nicht (Geschichte bleibt, wie sie geschrieben wurde).
     3. Der längere Name hat Platz: nichts ragt heraus, nichts ist abgeschnitten, die Seite ist nicht breiter als das Handy,
        Kachel und Rücklink bleiben in ihrer Zeile.
     4. Alte Lesezeichen gehen: /tausch und /tausch/packlisten antworten wie bisher.
     5. Keine JavaScript-Fehler.

  python3 werkzeuge/rucksack_test.py [--datei X.py] [--bilder ORDNER] [--port N]
  Mit den Schriften von GitHub: FONTCONFIG_FILE=…/fonts.conf python3 werkzeuge/rucksack_test.py
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
PASSWORT = "Rucksack-" + base64.b16encode(os.urandom(5)).decode().lower()
NAMEN = {"de": "Digitaler Rucksack", "en": "Digital backpack", "fr": "Sac à dos numérique", "it": "Zaino digitale", "rm": "Satgados digital"}
ALT = r"daten[- ]?tausch|file[- ]exchange|data[- ]exchange|[ée]change de (?:fichiers|données)|scambio (?:di )?(?:file|dati)|barat da (?:datotecas|datas)"
SEITEN = ["/more", "/tausch", "/tausch/packlisten", "/settings", "/help", "/"]

# sichtbarer Text mit dem alten Namen (ohne die Liste der Änderungen in der Anleitung)
SICHTBAR = r"""(alt) => {
  const rx = new RegExp(alt, 'i'), out = [], w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const n = w.currentNode, p = n.parentElement;
    if (!p || /^(SCRIPT|STYLE)$/.test(p.tagName) || p.closest('#changes, #aenderungen, #news, .changes, [data-history]')) continue;
    const t = n.nodeValue.trim();
    if (t && rx.test(t)) out.push(t.slice(0, 110));
  }
  for (const e of document.querySelectorAll('[title], [aria-label], [placeholder]'))
    for (const a of ['title', 'aria-label', 'placeholder']) { const v = e.getAttribute(a) || ''; if (rx.test(v)) out.push(a + ': ' + v.slice(0, 90)); }
  if (rx.test(document.title)) out.push('title: ' + document.title);
  return [...new Set(out)];
}"""

# die Stellen mit dem Namen: ragt etwas heraus, ist es abgeschnitten, bricht es um?
PLATZ = r"""(name) => {
  const out = [];
  for (const e of document.querySelectorAll('a, b, h1, h2, h3, summary, button, span, small, label, th, li')) {
    if (![...e.childNodes].some(n => n.nodeType === 3 && n.nodeValue.includes(name))) continue;
    const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    if (!r.width || !r.height || cs.visibility === 'hidden') continue;
    const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.3;
    out.push({k: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.split(' ')[0] : ''),
              dx: e.scrollWidth - e.clientWidth, re: Math.round(r.right - window.innerWidth), li: Math.round(-r.left), zeilen: Math.round(r.height / lh),
              cut: cs.textOverflow === 'ellipsis' && e.scrollWidth > e.clientWidth, block: cs.display !== 'inline'});
  }
  const de = document.documentElement;
  return {st: out, seite: de.scrollWidth - de.clientWidth};
}"""


def dokumente():
    """A) README, Anleitung.html, docs/*.md: [(Datei, Zeile, Text)] mit dem alten Namen"""
    out = []
    for f in [os.path.join(REPO, "README.md"), os.path.join(REPO, "Anleitung.html")] + sorted(glob.glob(os.path.join(REPO, "docs", "*.md"))):
        if not os.path.isfile(f):
            continue
        for i, ln in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
            m = re.search(ALT, ln, re.I)
            if m:
                out.append((os.path.relpath(f, REPO), i, ln[max(0, m.start() - 30):m.end() + 30].strip()))
    return out


def main():
    ap = argparse.ArgumentParser(description="«Digitaler Rucksack» statt «Datentausch» in fünf Sprachen, mit Platz am Handy")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5157)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (rucksack_<sprache>_<seite>.png)")
    ap.add_argument("--sprachen", default="de,en,fr,it,rm")
    a = ap.parse_args()
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    print("A) Dokumente", flush=True)
    dk = dokumente()
    for f, i, t in dk[:20]:
        print("    %s:%d  %s" % (f, i, t), flush=True)
    pruef(not dk, "README.md, Anleitung.html, docs/*.md ohne den alten Namen (%d)" % len(dk))

    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_rucksack_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "tausch_on": True}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(300):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        print("B) Browser, 390 px" + (" · Schriften: " + os.environ["FONTCONFIG_FILE"] if os.environ.get("FONTCONFIG_FILE") else ""), flush=True)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            lauf(br, a, pruef, base)
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
    print("Rucksack-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def lauf(br, a, pruef, base):
    jsf = []
    for L in a.sprachen.split(","):
        name = NAMEN[L]
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                             http_credentials={"username": "admin", "password": PASSWORT})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e, L=L: jsf.append(L + ": " + str(e)[:300]))
        pg.goto(base + "/more", wait_until="domcontentloaded")
        pg.wait_for_timeout(1500)
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            pg.evaluate("k => { langSet(k); }", L)
        pg.wait_for_timeout(800)
        alt, eng, breit, fehlt = [], [], [], []
        for pfad in SEITEN:
            r = pg.goto(base + pfad, wait_until="domcontentloaded")
            if pfad.startswith("/tausch"):
                pruef(r is not None and r.status == 200, "%s %s: die alte Adresse antwortet (%s)" % (L, pfad, r.status if r else None))
            pg.wait_for_timeout(3500 if pfad in ("/", "/settings") else 2000)
            pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            if pfad in ("/settings", "/help"):
                pg.evaluate("() => { document.querySelectorAll('details').forEach(d => { d.open = true; }); }")
                pg.wait_for_timeout(1200)
            alt += [pfad + "  " + t for t in pg.evaluate(SICHTBAR, ALT)]
            m = pg.evaluate(PLATZ, name)
            if pfad != "/" and not m["st"]:
                fehlt.append(pfad)
            for x in m["st"]:
                if x["dx"] > 3 and x["block"] or x["re"] > 2 or x["li"] > 2 or x["cut"]:
                    eng.append("%s %s: +%d px, rechts %d, links %d%s" % (pfad, x["k"], x["dx"], x["re"], x["li"], ", abgeschnitten" if x["cut"] else ""))
                if pfad in ("/more", "/tausch/packlisten", "/tausch") and x["k"].split(".")[0].split("#")[0] in ("b", "span", "h2", "a") and x["zeilen"] > 1:
                    eng.append("%s %s: «%s» bricht um (%d Zeilen)" % (pfad, x["k"], name, x["zeilen"]))
            if m["seite"] > 4:
                breit.append("%s (+%d px)" % (pfad, m["seite"]))
            if a.bilder and pfad != "/":
                if pfad == "/settings":
                    pg.evaluate("n => { const s = [...document.querySelectorAll('summary')].find(x => x.textContent.includes(n)); if (s) s.scrollIntoView({block: 'center'}); }", name)
                if pfad == "/help":
                    pg.evaluate("() => { const s = document.getElementById('tausch'); if (s) s.scrollIntoView(); }")
                pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(a.bilder, "rucksack_%s_%s.png" % (L, pfad.strip("/").replace("/", "_"))))
        for z in alt[:20]:
            print("    alter Name: " + z, flush=True)
        for z in eng[:20]:
            print("    eng: " + z, flush=True)
        pruef(not fehlt, "%s: «%s» steht auf Mehr, /tausch, Packlisten, Einstellungen, Anleitung (fehlt: %s)" % (L, name, ", ".join(fehlt) or "–"))
        pruef(not alt, "%s: kein sichtbarer Text mit dem alten Namen (%d)" % (L, len(alt)))
        pruef(not eng, "%s: der Name hat überall Platz (%d)" % (L, len(eng)))
        pruef(not breit, "%s: keine Seite breiter als das Handy (%s)" % (L, ", ".join(breit) or "–"))
        ctx.close()
    pruef(not jsf, "keine JavaScript-Fehler" + (": " + " | ".join(jsf[:3]) if jsf else ""))


if __name__ == "__main__":
    sys.exit(main())
