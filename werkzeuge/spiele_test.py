#!/usr/bin/env python3
"""Test der Spielesammlung (games/MotionWatch_Spiele.zip, ab GS-1.4):

  1. Paket: games.json (jedes Spiel mit Ordner, Startdatei, Gruppe touch / buttons / keys, Bild-Symbol vorhanden,
     neue Spiele mit Namen und Beschreibung in de/en/fr/it/rm), LIZENZEN.txt nennt jeden Ordner, keine Adresse nach
     aussen in neuen Spielen (nur die eigenen Dateien), GAMES_PKG in quelle/320 passt zu Grösse und SHA-256 der ZIP.
  2. Browser (Playwright, ohne Internet - jede Anfrage nach aussen ist ein Fehler): jedes Spiel am Handy (390 × 844,
     Touch) und am PC (1280 × 800) laden, Start-Knopf antippen bzw. klicken, ein paar Eingaben; keine JavaScript-Fehler.
     Touch-Spiele: das Antippen muss im Spiel ankommen. Der eigene Zurück-Link führt zur Spielesammlung von MoveEye.

  python3 werkzeuge/spiele_test.py                    # Paket + Browser, nur die Spiele mit 5 Sprachen (ab GS-1.4)
  python3 werkzeuge/spiele_test.py --alle             # dazu die älteren Spiele (2048, Tetris …)
  python3 werkzeuge/spiele_test.py --ohne-browser     # nur das Paket
  python3 werkzeuge/spiele_test.py --bilder ORDNER    # Bildschirmfotos (Handy und PC) jedes Spiels

Die Spiele laufen hier wie am Spiele-Port von MoveEye unter /g/<ordner>/ und bekommen einen «✕ Zurück»-Knopf (#mw-back).
"""
import argparse
import hashlib
import http.server
import json
import os
import re
import shutil
import socketserver
import sys
import tempfile
import threading
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
SPRACHEN = ("de", "en", "fr", "it", "rm")
GRUPPEN = ("touch", "buttons", "keys")
ZURUECK = '<div id="mw-back"><a href="/zurueck-zur-sammlung">✕ Zurück</a></div>'
START = ["#bPlay", "#playBtn", "#btnPlay", "#startBtn", "#play", "button.play", "[data-t=play]",
         ".q-shade[data-card=ready] .play"]


def paket_pruefen(zp, fehler, warn):
    with zipfile.ZipFile(zp) as z:
        namen = set(z.namelist())
        gj = json.loads(z.read("games.json"))
        lic = z.read("LIZENZEN.txt").decode("utf-8")
        for g in gj.get("games", []):
            d, st = g.get("dir", ""), g.get("start", "index.html")
            if not re.fullmatch(r"[A-Za-z0-9_\-]{1,40}", d):
                fehler.append(f"{d}: Ordnername passt nicht zum Spiele-Port (/g/<ordner>/)")
            if f"{d}/{st}" not in namen:
                fehler.append(f"{d}: Startdatei {st} fehlt")
            if g.get("input", "touch") not in GRUPPEN:
                fehler.append(f"{d}: unbekannte Gruppe {g.get('input')!r}")
            ic = g.get("icon", "")
            if "." in ic and f"{d}/{ic}" not in namen:
                fehler.append(f"{d}: Bild-Symbol {ic} fehlt")
            if f"({d}/)" not in lic and not any(f"({p}" in lic and d.startswith(p.rstrip("*/")) for p in ("kv-*/", "qg-*/")):
                fehler.append(f"{d}: fehlt in LIZENZEN.txt")
            if "names" in g or "descs" in g:
                for L in SPRACHEN:
                    if not (g.get("names") or {}).get(L) or not (g.get("descs") or {}).get(L):
                        fehler.append(f"{d}: Name oder Beschreibung auf {L} fehlt")
                if g.get("desc") != (g.get("descs") or {}).get("de"):
                    fehler.append(f"{d}: desc ist nicht die deutsche Beschreibung")
                for n in namen:                   # new games: nothing from outside (fonts, scripts, statistics)
                    if n.startswith(d + "/") and n.endswith((".html", ".js", ".css")):
                        t = z.read(n).decode("utf-8", "replace")
                        for u in re.findall(r"(?:https?:)?//[A-Za-z0-9.-]+\.[a-z]{2,}[^\s\"')]*", t):
                            if "w3.org/" not in u and not u.startswith("//"):
                                fehler.append(f"{n}: Adresse nach aussen {u[:80]}")
        if "keys" in {g.get("input") for g in gj["games"]} and "keys" not in (gj.get("groups") or {}):
            warn.append("games.json: Gruppe «keys» ohne Titel in groups")
    q = os.path.join(REPO, "quelle", "320_spielecke.py")
    if os.path.isfile(q) and os.path.abspath(zp) == os.path.abspath(os.path.join(REPO, "games", "MotionWatch_Spiele.zip")):
        m = re.search(r'GAMES_PKG = \{"version": "([^"]+)", "file": "[^"]+", "size": (\d+), "sha256": "([0-9a-f]+)"\}', open(q, encoding="utf-8").read())
        b = open(zp, "rb").read()
        if not m:
            fehler.append("quelle/320: GAMES_PKG nicht gefunden")
        else:
            if int(m.group(2)) != len(b) or m.group(3) != hashlib.sha256(b).hexdigest():
                fehler.append(f"quelle/320: GAMES_PKG passt nicht zur ZIP (size {len(b)}, sha256 {hashlib.sha256(b).hexdigest()})")
            if m.group(1) != gj.get("version"):
                fehler.append(f"quelle/320: GAMES_PKG version {m.group(1)} ≠ games.json {gj.get('version')}")
    return gj


def server(root):
    """wie der Spiele-Port von MoveEye: /g/<ordner>/<datei>, HTML mit «✕ Zurück» (#mw-back)"""
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=root, **k)

        def log_message(self, *a):
            pass

        def do_GET(self):
            from urllib.parse import unquote, urlsplit
            p = unquote(urlsplit(self.path).path)
            if p == "/zurueck-zur-sammlung":
                b = b"<!doctype html><title>Sammlung</title><h1>Spielesammlung</h1>"
            else:
                m = re.fullmatch(r"/g/([A-Za-z0-9_\-]{1,40})/(.*)", p)
                f = os.path.realpath(os.path.join(root, m.group(1), m.group(2) or "index.html")) if m else ""
                if not f.startswith(os.path.realpath(root) + os.sep) or not os.path.isfile(f):
                    self.send_error(404); return
                if not f.endswith((".html", ".htm")):
                    self.path = "/" + os.path.relpath(f, root); return super().do_GET()
                t = open(f, encoding="utf-8", errors="replace").read()
                i = t.lower().rfind("</body>")
                b = (t[:i] + ZURUECK + t[i:] if i >= 0 else t + ZURUECK).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
    s = S(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


ZAEHLER = """() => { window.__mwT = {pd: 0, md: 0, ts: 0, kd: 0};
  addEventListener('pointerdown', () => __mwT.pd++, true); addEventListener('mousedown', () => __mwT.md++, true);
  addEventListener('touchstart', () => __mwT.ts++, true); addEventListener('keydown', () => __mwT.kd++, true); }"""
ZUSTAND = """() => {
  const q = window.quantumGame, ov = document.querySelector('#ovStart, #startOv, .q-shade[data-card=ready]');
  const vis = e => { const c = getComputedStyle(e); return c.display !== 'none' && c.visibility !== 'hidden' && +c.opacity > 0.05
    && !e.classList.contains('hidden') && !e.classList.contains('hide') && e.getBoundingClientRect().width > 0; };
  return {q: q ? q.state : null, start: ov ? vis(ov) : null, T: window.__mwT || null}; }"""


def spiel_pruefen(br, base, g, fehler, warn, bilder, zeile):
    d = g["dir"]
    url = f"{base}/g/{d}/{g.get('start', 'index.html')}"
    for name, vp, mobil in (("Handy", {"width": 390, "height": 844}, True), ("PC", {"width": 1280, "height": 800}, False)):
        ctx = br.new_context(viewport=vp, is_mobile=mobil, has_touch=mobil, device_scale_factor=2 if mobil else 1)
        aussen = []
        ctx.route("**/*", lambda r, a=aussen: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:"))
                  else (a.append(r.request.url[:100]), r.abort()))
        pg = ctx.new_page()
        fe = []
        pg.on("pageerror", lambda e, fe=fe: fe.append(str(e)[:300]))
        pg.on("console", lambda m, fe=fe: fe.append("console.error: " + m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text else None)
        info = {"start": "-", "eingabe": "-"}
        try:
            pg.goto(url, wait_until="load", timeout=30000)
            pg.evaluate(ZAEHLER)
            pg.wait_for_timeout(1200)
            vor = pg.evaluate(ZUSTAND)
            knopf = None
            for s in START:
                loc = pg.locator(s)
                for i in range(loc.count()):
                    if loc.nth(i).is_visible():
                        knopf = loc.nth(i); break
                if knopf:
                    break
            if knopf is None:
                loc = pg.get_by_role("button", name=re.compile(r"^\s*(▶\s*)?(play|spielen|start|jouer)\b", re.I))
                if loc.count() and loc.first.is_visible():
                    knopf = loc.first
            if knopf is not None:
                knopf.tap() if mobil else knopf.click()
            else:
                (pg.touchscreen.tap(vp["width"] / 2, vp["height"] / 2) if mobil else pg.mouse.click(vp["width"] / 2, vp["height"] / 2))
            pg.wait_for_timeout(700)
            nach = pg.evaluate(ZUSTAND)
            gestartet = (nach["q"] in ("playing", "over")) if nach["q"] is not None else (vor["start"] is True and nach["start"] is False) if vor["start"] is not None else None
            info["start"] = {True: "ok", False: "NEIN", None: "?"}[gestartet] if (vor["start"] is not None or vor["q"] is not None or knopf is not None) else "direkt"   # no start screen
            if gestartet is False and (g.get("input", "touch") == "touch" or not mobil):
                fehler.append(f"{d} {name}: startet nicht (Start-Knopf {'gefunden' if knopf is not None else 'nicht gefunden'})")
            # a few inputs
            cv = pg.locator("canvas").first
            box = cv.bounding_box() if pg.locator("canvas").count() else None
            cx, cy = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2) if box else (vp["width"] / 2, vp["height"] / 2)
            t0 = pg.evaluate("() => JSON.stringify(window.__mwT)")
            if mobil:
                for dx in (0, -60, 60):
                    pg.touchscreen.tap(cx + dx, cy); pg.wait_for_timeout(250)
            else:
                for k in ("ArrowLeft", "ArrowRight", "ArrowUp", "Space", "KeyW", "KeyD"):
                    pg.keyboard.press(k); pg.wait_for_timeout(120)
                pg.mouse.click(cx, cy); pg.wait_for_timeout(300)
            pg.wait_for_timeout(600)
            T = pg.evaluate("() => window.__mwT")
            st = pg.evaluate(ZUSTAND)
            if mobil:
                ok = (T["pd"] + T["md"] + T["ts"]) > 0
                info["eingabe"] = "Tippen ok" if ok else "Tippen kommt nicht an"
                if g.get("input", "touch") == "touch" and not ok:
                    fehler.append(f"{d} Handy: Antippen kommt im Spiel nicht an")
            else:
                info["eingabe"] = "ok"
            if st["q"] not in (None, "playing", "over", "paused"):
                warn.append(f"{d} {name}: nach der Eingabe Zustand {st['q']}")
            if bilder:
                pg.screenshot(path=os.path.join(bilder, f"spiel_{d}_{'handy' if mobil else 'pc'}.png"))
            # the game's own back link («../» or «index.html») must lead to the game list of MoveEye
            if "names" in g:
                if pg.locator('a[href="../"], a[href="index.html"]').count():
                    href_ok = pg.evaluate("""() => { const a = document.querySelector('a[href="../"], a[href="index.html"]');
                      let to = null; const b = document.querySelector('#mw-back a'); if (!b) return 'kein #mw-back';
                      b.addEventListener('click', e => { to = b.getAttribute('href'); e.preventDefault(); }, {once: true});
                      a.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true})); return to || 'nicht umgeleitet'; }""")
                    if href_ok != "/zurueck-zur-sammlung":
                        fehler.append(f"{d} {name}: eigener Zurück-Link führt nicht zur Sammlung ({href_ok})")
        except Exception as e:
            fehler.append(f"{d} {name}: {e.__class__.__name__}: {str(e)[:200]}")
        for x in fe:
            fehler.append(f"{d} {name}: JavaScript: {x}")
        for u in sorted(set(aussen)):
            fehler.append(f"{d} {name}: Anfrage nach aussen {u}")
        zeile[name] = info
        ctx.close()


def main():
    ap = argparse.ArgumentParser(description="Test der Spielesammlung (Paket und Browser)")
    ap.add_argument("--zip", default=os.path.join(REPO, "games", "MotionWatch_Spiele.zip"))
    ap.add_argument("--alle", action="store_true", help="auch die älteren Spiele im Browser prüfen")
    ap.add_argument("--nur", default="", help="nur diese Ordner (Komma-Liste)")
    ap.add_argument("--ohne-browser", action="store_true")
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos")
    a = ap.parse_args()
    fehler, warn = [], []
    gj = paket_pruefen(a.zip, fehler, warn)
    print(f"Paket {gj.get('version')}: {len(gj['games'])} Spiele", flush=True)
    if not a.ohne_browser:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit("Playwright fehlt (pip install playwright && python3 -m playwright install chromium)")
        tmp = tempfile.mkdtemp(prefix="mw_spiele_")
        try:
            with zipfile.ZipFile(a.zip) as z:
                z.extractall(tmp)
            s = server(tmp)
            base = f"http://127.0.0.1:{s.server_address[1]}"
            if a.bilder:
                os.makedirs(a.bilder, exist_ok=True)
            nur = {x.strip() for x in a.nur.split(",") if x.strip()}
            spiele = [g for g in gj["games"] if (g["dir"] in nur) if nur] or [g for g in gj["games"] if a.alle or "names" in g]
            with sync_playwright() as pw:
                br = pw.chromium.launch()
                print(f"{'Spiel':<20} {'Gruppe':<8} {'Handy: Start / Eingabe':<34} PC: Start", flush=True)
                for g in spiele:
                    zeile = {}
                    n0 = len(fehler)
                    spiel_pruefen(br, base, g, fehler, warn, a.bilder, zeile)
                    h, p = zeile.get("Handy", {}), zeile.get("PC", {})
                    print(f"{g['dir']:<20} {g.get('input', 'touch'):<8} {h.get('start', '-') + ' / ' + h.get('eingabe', '-'):<34} {p.get('start', '-')}"
                          + ("" if len(fehler) == n0 else f"   ✗ {len(fehler) - n0} Fehler"), flush=True)
                br.close()
            s.shutdown()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    for w in warn:
        print("Warnung:", w)
    for f in fehler:
        print("FEHLER:", f)
    print("Spiele-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
