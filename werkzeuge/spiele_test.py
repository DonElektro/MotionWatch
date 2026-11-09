#!/usr/bin/env python3
"""Test der Spielesammlung (games/MotionWatch_Spiele.zip, ab GS-1.4):

  1. Paket: games.json (jedes Spiel mit Ordner, Startdatei, Gruppe touch / buttons / keys, Bild-Symbol vorhanden,
     neue Spiele mit Namen und Beschreibung in de/en/fr/it/rm), LIZENZEN.txt nennt jeden Ordner, keine Adresse nach
     aussen in neuen Spielen (nur die eigenen Dateien), GAMES_PKG in quelle/320 passt zu Grösse und SHA-256 der ZIP.
  2. Browser (Playwright, ohne Internet - jede Anfrage nach aussen ist ein Fehler): jedes Spiel am Handy (390 × 844,
     Touch) und am PC (1280 × 800) laden, Start-Knopf antippen bzw. klicken, ein paar Eingaben; keine JavaScript-Fehler.
     Ab 3.66.1 mit dem echten «✕ Zurück» aus quelle/340 (GAME_BACK): er darf keinen Knopf, Link und kein Feld überdecken.
     Touch-Spiele: das Antippen muss im Spiel ankommen. Der eigene Zurück-Link führt zur Spielesammlung von MoveEye.
  3. Wobbly Truck (ab GS-1.5, mit ?test=1): Truck und Motorrad auf beiden Strecken, ein Salto und ein Wheelie werden erkannt,
     der Looping gelingt auf «Normal» und ist keine Falle, Einstellungen werden gespeichert, Rekord je Strecke und Fahrzeug.
     GS-1.6: auf «Einfach» landet ein schiefer Sprung ohne Eingabe gerade, ein Salto wird trotzdem erkannt, kein Abwurf mit ★;
     der schwebende «✕ Zurück» von MoveEye ist ausgeblendet (eigener Link oben, sonst über der Bremse).

  python3 werkzeuge/spiele_test.py                    # Paket + Browser, nur die Spiele mit 5 Sprachen (ab GS-1.4)
  python3 werkzeuge/spiele_test.py --alle             # dazu die älteren Spiele (2048, Tetris …)
  python3 werkzeuge/spiele_test.py --ohne-browser     # nur das Paket
  python3 werkzeuge/spiele_test.py --bilder ORDNER    # Bildschirmfotos (Handy und PC) jedes Spiels
  python3 werkzeuge/spiele_test.py --nur-fotaq [--fotaq ORDNER]   # nur «Flight of the Amazon Queen» (ScummVM, 639zzg)
  python3 werkzeuge/spiele_test.py --fotaq-moveeye [--datei X.py] [--bilder ORDNER] [--fotaq-release URL]
      # FOTAQ in MoveEye: Laden nur durch den Admin, Pins, freier Platz, veränderte / zu grosse Datei, Entpacken, Kachel,
      # Spiele-Port (wasm-Typ, 304, keine Pfade nach aussen), Entfernen; mit --fotaq-release die echten Assets + das Spiel

FOTAQ (ab MoveEye 639zzg): ist das Paket da (--fotaq, MW_FOTAQ oder ~/.config/motionwatch/fotaq), lädt es am Handy (quer),
iPad und PC die Startseite (Sprachwahl, Copyright, «✕ Zurück» überdeckt nichts), startet Deutsch und Englisch (ScummVM wählt
das Spiel, die Spielfläche zeigt ein Bild, keine JavaScript-Fehler), prüft die Knöpfe neben dem Spiel, Rechtsklick per Touch
(lange drücken, «🖱 Rechts»), «☰ Menü» und am PC Schnellspeichern (F11) mit Spielstand in IndexedDB nach dem Neuladen.
Fehlt das Paket, wird der Teil übersprungen.

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
try:    # 3.66.1: the real button of MoveEye (quelle/340 GAME_BACK) with its placement script
    _q = open(os.path.join(REPO, "quelle", "340_spiele_seiten.py"), encoding="utf-8").read()
    ZURUECK = re.search(r'GAME_BACK = """(.*?)"""', _q, re.S).group(1).replace("__BACK__", "/zurueck-zur-sammlung")
except (OSError, AttributeError):
    pass
# the floating «✕ Zurück» must never lie on a button, link or form field of the game (or it is hidden: own back link)
UEBERDECKT = """() => { const b = document.getElementById('mw-back'); if (!b || getComputedStyle(b).display === 'none') return null;
  const r = b.firstElementChild.getBoundingClientRect(), out = new Set();
  if (r.left < 0 || r.top < 0 || r.right > innerWidth || r.bottom > innerHeight) out.add('ausserhalb');
  for (let i = 0; i <= 4; i++) for (let j = 0; j <= 2; j++)
    for (const e of document.elementsFromPoint(Math.min(innerWidth - 1, r.left + 2 + (r.width - 4) * i / 4), Math.min(innerHeight - 1, r.top + 2 + (r.height - 4) * j / 2))) {
      if (b.contains(e) || e === document.body || e === document.documentElement) continue;
      const c = e.closest('a,button,input,select,textarea,label,[role=button],[onclick]');
      if (c) out.add(c.tagName.toLowerCase() + (c.id ? '#' + c.id : '') + ' ' + (c.textContent || '').trim().slice(0, 16)); }
  return [...out]; }"""
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
            for zeit in (0, 2800):                     # after the inputs and once more after the next re-check of the button
                pg.wait_for_timeout(zeit)
                ue = pg.evaluate(UEBERDECKT)
                if ue:
                    fehler.append(f"{d} {name}: «✕ Zurück» überdeckt {', '.join(ue)}")
                    break
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
                      b.removeAttribute('onclick');   // the real button goes back in the history: here only where it leads
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


# Wobbly Truck (GS-1.5): ?test=1 gives a fixed seed and window.__wt (deterministic simulation with fixed time steps)
WT_BOT = """window.__bot = (W, I) => { const a = W.B.a, w = W.B.w, sl = Math.atan((W.H(W.B.x + .04) - W.H(W.B.x - .04)) / .08);
  if (W.air.on && W.air.t > 0.12) { const tgt = Math.round((a - sl) / 6.283) * 6.283 + sl, e = a + w * 0.3 - tgt; I.gas = e < -0.12; I.brake = e > 0.12; }
  else { const d = a - sl, dw = d - Math.round(d / 6.283) * 6.283; I.brake = false; I.gas = dw < 0.35; } };"""
WT_RUN = """([veh, trk, scen, diff]) => { const W = window.__wt, I = W.inp; W.freeze(true); W.SET.diff = diff == null ? 1 : diff; W.select(veh, trk); W.start();
  const r = {state0: W.state}; I.gas = I.brake = I.trick = false;
  if (scen === 'fahren') { W.place(5, 0, 0, 0, 0, 0); W.sim(1.5, () => { __bot(W, I); }); r.dx = W.B.x - 5; }
  if (scen === 'salto') { W.place(8, 9, 9, 6, 0, 0);          // in the air: lean back until one turn, then land level
    W.sim(3.5, () => { const a = W.B.a, w = W.B.w; I.gas = W.air.on && a + w * 0.3 < 5.98; I.brake = W.air.on && !I.gas && w > 2.5; }); }
  if (scen === 'wheelie') { W.place(5, 0, 0, 0, 0, 0); W.sim(3, () => { I.gas = W.B.a < 0.45; }); I.gas = false; W.sim(1.5); }
  if (scen === 'looping') { const L = W.loops[0]; W.place(L.cx - 60, 0, 6, 0, 0, 0); W.sim(10, () => { __bot(W, I); }); r.x = W.B.x - L.cx; }
  if (scen === 'langsam') { const L = W.loops[0]; W.place(L.cx - 12, 0, 8, 0, 0, 0); W.sim(25, () => { __bot(W, I); }); r.x = W.B.x - L.cx; }
  if (scen === 'sturz') { W.place(8, 6, 6, 0, Math.PI, 0); W.sim(4); }
  if (scen === 'schief') { W.place(8, 8, 9, 6, 0.9, 2.5); W.sim(5); }     // Einfach: crooked jump, no input -> lands level by itself
  if (scen === 'halbsalto') { W.place(8, 9, 9, 6, 0, 0); W.sim(5, () => { I.gas = W.air.on && W.B.a < 4.0; }); }   // tilt, let go, assist finishes
  if (scen === 'superman') { W.place(8, 8, 9, 6, 0, 0); W.sim(5, () => { I.trick = true; }); }                      // ★ held into the landing
  I.gas = I.brake = I.trick = false; r.state = W.state; r.ids = W.log.map(e => e.id); return r; }"""


def wobbly_pruefen(br, base, fehler, bilder):
    """Wobbly Truck: both vehicles on both tracks, a flip and a wheelie are detected, the loop works on Normal and is no trap,
    settings are saved (and «Standard» resets them), the best score is kept per track and vehicle"""
    d = "kv-wobbly-truck"
    for name, vp, mobil in (("Handy", {"width": 390, "height": 844}, True), ("PC", {"width": 1280, "height": 800}, False)):
        ctx = br.new_context(viewport=vp, is_mobile=mobil, has_touch=mobil, device_scale_factor=1)
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else r.abort())
        pg = ctx.new_page()
        fe = []
        pg.on("pageerror", lambda e, fe=fe: fe.append(str(e)[:300]))
        ok = []
        try:
            pg.goto(f"{base}/g/{d}/index.html?test=1", wait_until="load", timeout=30000)
            pg.wait_for_timeout(400)
            pg.evaluate("() => {" + WT_BOT + "}")
            for veh in ("truck", "bike"):
                for trk in ("hills", "stunt"):
                    r = pg.evaluate(WT_RUN, [veh, trk, "fahren"])
                    if r["state0"] != "play" or r["state"] != "play" or r["dx"] < 5:
                        fehler.append(f"{d} {name}: {veh}/{trk} startet oder fährt nicht ({r})")
            for veh, trk, scen, want in (("truck", "hills", "salto", "backflip"), ("bike", "stunt", "salto", "backflip"),
                                         ("bike", "stunt", "wheelie", "wheelie"), ("truck", "stunt", "looping", "loop"),
                                         ("bike", "stunt", "looping", "loop")):
                r = pg.evaluate(WT_RUN, [veh, trk, scen])
                if want not in r["ids"] or r["state"] != "play":
                    fehler.append(f"{d} {name}: {veh}/{trk} {scen}: «{want}» nicht erkannt ({r['state']}, {r['ids']})")
                else:
                    ok.append(f"{scen}-{veh}")
            for veh, trk, scen, want in (("truck", "hills", "schief", "bigair"), ("bike", "stunt", "schief", "bigair"),
                                         ("truck", "stunt", "halbsalto", "backflip"), ("bike", "hills", "halbsalto", "backflip"),
                                         ("bike", "stunt", "superman", "superman")):
                r = pg.evaluate(WT_RUN, [veh, trk, scen, 0])          # difficulty «Einfach»: automatic air control
                if want not in r["ids"] or r["state"] != "play":
                    fehler.append(f"{d} {name}: Einfach {veh}/{trk} {scen}: «{want}» / Landung ohne Sturz fehlt ({r['state']}, {r['ids']})")
                else:
                    ok.append(f"einfach-{scen}-{veh}")
            # MoveEye's floating «✕ Zurück» (#mw-back) would cover the Brake pedal: the game hides it (own header link)
            if pg.evaluate("() => { const b = document.getElementById('mw-back'); return !b || getComputedStyle(b).display !== 'none'; }"):
                fehler.append(f"{d} {name}: schwebender Zurück-Knopf nicht ausgeblendet (überdeckt die Bremse)")
            for veh in ("truck", "bike"):           # too slow for the loop: fall off or pass behind it, never stuck in it
                r = pg.evaluate(WT_RUN, [veh, "stunt", "langsam"])
                if r["state"] == "play" and r["x"] < 15:
                    fehler.append(f"{d} {name}: {veh} bleibt beim Looping hängen ({r})")
            r = pg.evaluate(WT_RUN, ["bike", "stunt", "sturz"])  # upside down onto the head: crash, then game over with a best score
            best = pg.evaluate("() => localStorage.getItem('kv-game-wobbly-truck-best-stunt-bike')")
            if r["state"] != "over" or not best:
                fehler.append(f"{d} {name}: Sturz / Rekord je Strecke und Fahrzeug fehlt ({r['state']}, {best})")
            if mobil:   # the trick button is there for the motorbike while playing
                pg.evaluate("() => { __wt.select('bike', 'stunt'); __wt.start(); }")
                if not pg.locator("#trickP").is_visible():
                    fehler.append(f"{d} Handy: Trick-Knopf fehlt beim Motorrad")
            # settings: saved in localStorage, «Standard» resets
            pg.evaluate("() => { __wt.freeze(false); __wt.showSettings(); }")
            pg.locator("[data-diff='2']").click()
            pg.locator("#s_real").fill("80")
            s = pg.evaluate("() => JSON.parse(localStorage.getItem('kv-game-wobbly-truck-settings') || '{}')")
            if s.get("diff") != 2 or s.get("real") != 80:
                fehler.append(f"{d} {name}: Einstellungen nicht gespeichert ({s})")
            pg.locator("#resetBtn").click()
            s = pg.evaluate("() => JSON.parse(localStorage.getItem('kv-game-wobbly-truck-settings') || '{}')")
            if s.get("diff") != 1 or s.get("real") != 40:
                fehler.append(f"{d} {name}: «Standard» setzt nicht zurück ({s})")
            if bilder:
                pg.screenshot(path=os.path.join(bilder, f"spiel_{d}_einstellungen_{'handy' if mobil else 'pc'}.png"))
        except Exception as e:
            fehler.append(f"{d} {name}: {e.__class__.__name__}: {str(e)[:200]}")
        for x in fe:
            fehler.append(f"{d} {name}: JavaScript: {x}")
        print(f"{d:<20} {name:<6} Stunts/Looping: {', '.join(ok) or '-'}", flush=True)
        ctx.close()


# ---- «Flight of the Amazon Queen» (ScummVM, WebAssembly; MoveEye 639zzg): only when the package is there ------------------------
FOTAQ_GERAETE = (("handy", {"width": 844, "height": 390}, True),        # the phone sideways (the page asks for it)
                 ("ipad", {"width": 1180, "height": 820}, True),
                 ("pc", {"width": 1280, "height": 800}, False))
FOTAQ_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]
FOTAQ_SCHLECHT = ("failed to instantiate engine", "Couldn't identify game", "could not find any game", "Unrecognized game",
                  "Aborted(", "RuntimeError", "unreachable")
# IndexedDB of ScummVM (IDBFS, database = mount point HOME, store FILE_DATA): the keys (paths) of the files
FOTAQ_IDB = """() => new Promise(res => { const q = indexedDB.open('/home/web_user'); q.onerror = () => res(null);
  q.onsuccess = () => { const db = q.result; if (!db.objectStoreNames.contains('FILE_DATA')) { res([]); return; }
    const r = db.transaction('FILE_DATA').objectStore('FILE_DATA').getAllKeys(); r.onsuccess = () => res(r.result.map(String)); r.onerror = () => res(null); }; })"""


def fotaq_ordner(pfad=""):
    """the unpacked package (index.html, scummvm.wasm, data/games/de|en); '' = not installed"""
    home = os.environ.get("MOTIONWATCH_HOME", "") or os.path.expanduser("~/.config/motionwatch")
    for p in ([pfad] if pfad else []) + [os.environ.get("MW_FOTAQ", ""), os.path.join(home, "fotaq")]:
        if p and all(os.path.isfile(os.path.join(p, f)) for f in ("index.html", "scummvm.js", "scummvm.wasm")) \
                and all(os.path.isdir(os.path.join(p, "data", "games", L)) for L in ("de", "en")):
            return os.path.abspath(p)
    return ""


def _hell(png):
    """share of the picture that is not (nearly) black"""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("L").resize((160, 100))
    h = im.histogram()
    return sum(h[25:]) / (160 * 100)


def _diff(a, b):
    """share of pixels that changed clearly between two screenshots"""
    import io
    from PIL import Image, ImageChops
    x = Image.open(io.BytesIO(a)).convert("L").resize((160, 100)); y = Image.open(io.BytesIO(b)).convert("L").resize((160, 100))
    d = ImageChops.difference(x, y).point(lambda v: 255 if v > 30 else 0)
    return d.histogram()[255] / (160 * 100)


def _ueber(a, b):
    return a["x"] < b["x"] + b["width"] - 1 and a["x"] + a["width"] > b["x"] + 1 and a["y"] < b["y"] + b["height"] - 1 and a["y"] + a["height"] > b["y"] + 1


def fotaq_pruefen(br, base, fehler, warn, bilder, nur=None):
    import time

    def bild(pg, name):
        if bilder:
            pg.screenshot(path=os.path.join(bilder, f"fotaq_{name}.png"))

    for gname, vp, touch in FOTAQ_GERAETE:
        if nur and gname not in nur:
            continue
        for L in ("de", "en"):
            ctx = br.new_context(viewport=vp, is_mobile=touch, has_touch=touch, device_scale_factor=2 if touch else 1)
            aussen = []
            ctx.route("**/*", lambda r, a=aussen: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:"))
                      else (a.append(r.request.url[:100]), r.abort()))
            pg = ctx.new_page()
            fe = []
            pg.on("pageerror", lambda e, fe=fe: fe.append(str(e)[:300]))
            pg.on("console", lambda m, fe=fe: fe.append("console.error: " + m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text else None)
            tag = f"FOTAQ {gname} {L}"
            info = []
            try:
                if L == "de" and touch:                 # the language choice upright (as it opens on the phone / iPad)
                    pg.set_viewport_size({"width": min(vp["width"], vp["height"]), "height": max(vp["width"], vp["height"])})
                pg.goto(f"{base}/g/fotaq/index.html", wait_until="load", timeout=30000)
                pg.wait_for_timeout(500)
                for s in ("#btn-de", "#btn-en", "#backPick", "a[href='LIZENZEN.txt']"):
                    if not pg.locator(s).is_visible():
                        fehler.append(f"{tag}: {s} fehlt auf der Startseite")
                cred = pg.locator(".cred").inner_text()
                if "Passfield" not in cred or "ScummVM" not in cred:
                    fehler.append(f"{tag}: Copyright-Zeile fehlt ({cred[:80]})")
                ue = pg.evaluate(UEBERDECKT)
                if ue:
                    fehler.append(f"{tag}: «✕ Zurück» überdeckt {', '.join(ue)}")
                if L == "de" and touch:
                    bild(pg, f"auswahl_{gname}")
                    pg.set_viewport_size(vp)
                b = pg.locator(f"#btn-{L}")
                b.tap() if touch else b.click()
                t0 = time.time()
                ok = False
                while time.time() - t0 < 150:
                    pg.wait_for_timeout(2000)
                    log = pg.evaluate("() => (window.FOTAQ && FOTAQ.log || []).join('\\n')")
                    if any(x in log for x in FOTAQ_SCHLECHT) or any("ExitStatus" in x for x in fe):
                        fehler.append(f"{tag}: ScummVM meldet einen Fehler: " + " | ".join(z for z in log.splitlines() if any(x in z for x in FOTAQ_SCHLECHT))[:300])
                        break
                    if "User picked target" in log and pg.locator("#load").is_hidden() and _hell(pg.locator("#stage").screenshot()) > 0.03:
                        ok = True
                        break
                dt = round(time.time() - t0)
                if not ok:
                    log = pg.evaluate("() => (window.FOTAQ && FOTAQ.log || []).slice(-12).join(' | ')")
                    fehler.append(f"{tag}: das Spiel startet nicht (kein Bild nach {dt} s; {pg.locator('#loadTxt').inner_text()[:60]}; Log: {log[:400]})")
                    bild(pg, f"{L}_{gname}_fehler")
                else:
                    info.append(f"läuft nach {dt} s")
                    pg.wait_for_timeout(9000 if L == "de" else 6000)       # into the intro (pictures, speech)
                    bild(pg, f"{L}_{gname}")
                    if not pg.evaluate("() => { const r = document.querySelector('#canvas').getBoundingClientRect(); return r.width > 200 && r.height > 120; }"):
                        fehler.append(f"{tag}: Spielfläche zu klein")
                    st = pg.locator("#stage").bounding_box()
                    for s in ("#kMenu", "#kSkip", "#kRight", "#backGame"):    # the toolbar sits beside the game, never over it
                        r1 = pg.locator(s).bounding_box()
                        if not r1:
                            fehler.append(f"{tag}: Knopf {s} fehlt")
                        elif _ueber(r1, st):
                            fehler.append(f"{tag}: Knopf {s} liegt über dem Spiel")
                    if touch:                           # right click by touch: long press, and «🖱 Right» + tap -> mouse button 2 on the canvas
                        pg.evaluate("() => { window.__r = 0; document.querySelector('#canvas').addEventListener('mousedown', e => { if (e.button === 2) __r++; }); }")
                        x, y = st["x"] + st["width"] * .5, st["y"] + st["height"] * .45
                        cdp = ctx.new_cdp_session(pg)
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
                        pg.wait_for_timeout(750)
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                        pg.wait_for_timeout(300)
                        n1 = pg.evaluate("() => __r")
                        pg.locator("#kRight").tap(); pg.wait_for_timeout(200); pg.touchscreen.tap(x, y); pg.wait_for_timeout(300)
                        n2 = pg.evaluate("() => __r")
                        if n1 < 1 or n2 < 2:
                            fehler.append(f"{tag}: Rechtsklick per Touch kommt nicht an (lange drücken {n1}, Knopf {n2 - n1})")
                        else:
                            info.append("Rechtsklick ok")
                    # «⏭ Skip» (Esc from the page) through the intro into the first room: then the room stands still
                    sk = pg.locator("#kSkip")
                    for _ in range(8):
                        sk.tap() if touch else sk.click()
                        pg.wait_for_timeout(2500)
                    r1 = pg.locator("#stage").screenshot(); pg.wait_for_timeout(1500); r2 = pg.locator("#stage").screenshot()
                    still = _diff(r1, r2)
                    bild(pg, f"{L}_raum_{gname}")
                    if still > 0.12:
                        fehler.append(f"{tag}: «⏭ Weiter» führt nicht durch das Intro (Bild ändert noch {still:.0%})")
                    else:
                        info.append("Weiter ok")
                    # «☰ Menu» (F1 from the page = journal of the game: save, load, options): the picture changes a lot
                    m = pg.locator("#kMenu")
                    m.tap() if touch else m.click()
                    pg.wait_for_timeout(2500)
                    nach = pg.locator("#stage").screenshot()
                    bild(pg, f"{L}_menue_{gname}")
                    if _diff(r2, nach) < 0.3:
                        fehler.append(f"{tag}: «☰ Menü» öffnet das Tagebuch nicht (Änderung {_diff(r2, nach):.0%})")
                    else:
                        info.append("Menü ok")
                    sk.tap() if touch else sk.click()                       # Esc closes the journal again
                    pg.wait_for_timeout(1500)
                    if gname == "pc" and L == "de":     # quick save (F11) in the room, then it must be in IndexedDB, also after reload
                        pg.keyboard.press("F11"); pg.wait_for_timeout(3000)
                        bild(pg, f"{L}_gespeichert_{gname}")
                        keys = pg.evaluate(FOTAQ_IDB) or []
                        sv = [k for k in keys if "/saves/de/" in k and not k.endswith("/de")]
                        if not sv:
                            fehler.append(f"{tag}: Schnellspeichern (F11) ergab keinen Spielstand in IndexedDB ({len(keys)} Einträge: {', '.join(keys[:6])})")
                        else:
                            pg.reload(wait_until="load"); pg.wait_for_timeout(800)
                            keys2 = pg.evaluate(FOTAQ_IDB) or []
                            if not all(k in keys2 for k in sv):
                                fehler.append(f"{tag}: Spielstand nach dem Neuladen weg")
                            else:
                                info.append("Spielstand bleibt (" + ", ".join(os.path.basename(k) for k in sv) + ")")
            except Exception as e:
                fehler.append(f"{tag}: {e.__class__.__name__}: {str(e)[:200]}")
            for x in fe:
                fehler.append(f"{tag}: JavaScript: {x}")
            for u in sorted(set(aussen)):
                fehler.append(f"{tag}: Anfrage nach aussen {u}")
            print(f"{tag:<18} " + (" · ".join(info) or "-"), flush=True)
            ctx.close()


def fotaq_lauf(pfad, fehler, warn, bilder):
    d = fotaq_ordner(pfad)
    if not d:
        print("FOTAQ: Paket nicht installiert – übersprungen (--fotaq ORDNER oder MW_FOTAQ)", flush=True)
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright fehlt (pip install playwright && python3 -m playwright install chromium)")
    import mimetypes
    mimetypes.add_type("application/wasm", ".wasm")
    if os.path.basename(d) != "fotaq":                 # served like on the device: /g/fotaq/ (the folder must be called «fotaq»)
        fehler.append(f"FOTAQ: der Ordner muss «fotaq» heissen ({d})")
        return
    s = server(os.path.dirname(d))
    try:
        base = f"http://127.0.0.1:{s.server_address[1]}"
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=FOTAQ_ARGS)
            fotaq_pruefen(br, base, fehler, warn, bilder)
            br.close()
    finally:
        s.shutdown()


# ---- MoveEye side of FOTAQ (639zzg): load (pins, free space, wrong checksum), unpack, games port, tile, admin tab ------------------
def _neueste_datei():
    import glob
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def _fake_fotaq(tag):
    """three tiny ZIP like the real package (engine, de, en) -> {name: bytes}"""
    import io
    n = tag.split("-")[1]
    eng = {"index.html": open(os.path.join(HIER, "fotaq", "index.html"), "rb").read(), "thumb.svg": open(os.path.join(HIER, "fotaq", "thumb.svg"), "rb").read(),
           "scummvm.js": b"/* test */", "scummvm.wasm": b"\0asm\1\0\0\0", "LIZENZEN.txt": "Test-Paket".encode(),
           "fotaq.json": json.dumps({"tag": tag}).encode(), "data/index.json": b'{"games":{},"queen.tbl":4}', "data/queen.tbl": b"QTBL"}
    out = {}
    for k, files in (("engine", eng), ("de", {"data/games/de/queen.1c": os.urandom(300000), "data/games/de/readme.txt": b"FOTAQ Freeware"}),
                     ("en", {"data/games/en/queen.1c": os.urandom(200000), "data/games/en/readme.txt": b"FOTAQ Freeware"})):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            for p, d in files.items():
                z.writestr(p, d)
        out[f"fotaq-{k}-{n}.zip"] = (k, b.getvalue(), sum(len(d) for d in files.values()))
    return out


def fotaq_moveeye(datei, fehler, warn, bilder, release="", pins=""):
    import base64
    import time
    import urllib.request
    sys.path.insert(0, HIER)
    from piper_test import Srv
    home = tempfile.mkdtemp(prefix="mw_fotaq_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_fotaq_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    ns["lan_guest_ip"] = lambda ip, fwd="": not fwd          # test: 127.0.0.1 counts as own Wi-Fi (on the device: tunnel = outside)
    CFG, F, DL = ns["CFG"], ns["FOTAQ_FILES"], ns["FOTAQ_DL"]

    def ok(c, what):
        print(("  ✓ " if c else "  ✗ ") + what, flush=True)
        if not c:
            fehler.append("FOTAQ MoveEye: " + what)
    ok(not ns["fotaq_pinned"]() or all(f["size"] for f in F.values()), "Pins im Programm: alle oder keine")
    ok(ns["fotaq_selftest"](), "Selbsttest 639zzg")
    srv = Srv()
    tag = ns["FOTAQ_TAG"]
    if release:                                    # the real assets of a (probe) release: pins from its pins.txt
        tx = open(pins, encoding="utf-8").read() if os.path.isfile(pins) else urllib.request.urlopen(release.rstrip("/") + "/pins.txt", timeout=60).read().decode()
        tag = re.search(r"fotaq(?:probe)?-\d+", release.rstrip("/").rsplit("/", 1)[-1]).group(0)
        ns["FOTAQ_TAG"] = tag
        for m in re.finditer(r"^PIN (fotaq-([a-z]+)-\d+\.zip) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+)", tx, re.M):
            F[m.group(2)] = {"name": m.group(1), "size": int(m.group(3)), "sha256": m.group(4), "unpacked": int(m.group(5))}
        ns["FOTAQ_BASE"]["url"] = release.rstrip("/") + "/"
    else:
        for name, (k, b, unz) in _fake_fotaq(tag).items():
            F[k] = {"name": name, "size": len(b), "sha256": hashlib.sha256(b).hexdigest(), "unpacked": unz}
            srv.files["/" + tag + "/" + name] = b
        ns["FOTAQ_BASE"]["url"] = srv.url + tag + "/"
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.1)
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)
    H = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode()}
    HA = {"Authorization": "Basic " + base64.b64encode(b"Anna:anna-pass-1").decode()}

    def party(d=None, h=H):
        r = c.post("/api/party", json=d, headers=h) if d else c.get("/api/party", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def warten(limit=900):
        t0 = time.time()
        while DL["running"] and time.time() - t0 < limit:
            time.sleep(0.2)
    code, j = party()
    fs = j.get("fotaq") or {}
    ok(code == 200 and fs.get("pinned") and not fs.get("installed"), f"/api/party: fotaq gepinnt, nicht installiert ({fs.get('size')} Bytes)")
    ok(all(x.get("dir") != "fotaq" for x in j.get("games", [])), "nicht installiert: keine Kachel")
    code, j = party({"action": "fotaq_install"}, HA)
    ok(code == 403, f"Familie darf nicht laden ({code})")
    CFG["tausch_free_gb"] = 1e6                     # rule: always tausch_free_gb free
    code, j = party({"action": "fotaq_install"})
    ok(code == 400 and "Platz" in str(j.get("error")) and not DL["running"], f"zu wenig Platz: nicht geladen ({code} {j.get('error')})")
    CFG["tausch_free_gb"] = 0.1
    if not release:
        de = "/" + tag + "/" + F["de"]["name"]
        srv.tamper.add(de)
        party({"action": "fotaq_install"}); warten()
        ok(not ns["fotaq_installed"]() and "checksum" in DL["msg"], f"veränderte Datei abgelehnt ({DL['msg']})")
        srv.tamper.discard(de)
        srv.extra = b"x" * 10
        party({"action": "fotaq_install"}); warten()
        ok(not ns["fotaq_installed"]() and ("large" in DL["msg"] or "size" in DL["msg"] or "checksum" in DL["msg"]), f"zu grosse Datei abgelehnt ({DL['msg']})")
        srv.extra = b""
    t0 = time.time()
    code, j = party({"action": "fotaq_install"})
    seen = 0
    while DL["running"] and time.time() - t0 < 1800:
        seen = max(seen, DL["got"]); time.sleep(0.3)
    ok(code == 200 and ns["fotaq_installed"](), f"geladen und entpackt in {time.time() - t0:.0f} s ({DL['msg'] or 'ok'})")
    ok(not os.path.exists(ns["fotaq_dl_dir"]()), "ZIP danach gelöscht")
    gl = ns["games_list"]()
    g = next((x for x in gl if x.get("dir") == "fotaq"), None)
    ok(g is not None and g["input"] == "touch" and g["icon"] == "thumb.svg", "Kachel in der Gruppe «👆 Touch»")
    ok(ns["games_list"](extra=False) == [], "games_list(extra=False): die Sammlung allein (leer)")
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and "Flight of the Amazon Queen" in t and "fotaq/thumb.svg" in t and "👆" in t, "/spiele zeigt die Kachel mit Bild")
    # the games port (own origin), like the phones use it
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); wp = sk.getsockname()[1]
    CFG["web_port"] = wp - 2
    ns["games_server_start"]()
    gp = ns["GAMESRV"]["port"]
    ok(gp == wp, f"Spiele-Port läuft ({gp})")
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path, hdr=None):
        try:
            with op.open(urllib.request.Request(f"http://127.0.0.1:{gp}{path}", headers=hdr or {}), timeout=60) as x:
                return x.status, dict(x.headers), x.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), b""
    s_, h_, b_ = get("/g/fotaq/")
    ok(s_ == 200 and b'id="mw-back"' in b_ and b"Flight of the Amazon Queen" in b_, "Port: Startseite mit «✕ Zurück» von MoveEye")
    s_, h_, b_ = get("/g/fotaq/scummvm.wasm")
    ok(s_ == 200 and h_.get("Content-Type", "").startswith("application/wasm") and "Last-Modified" in h_, f"Port: scummvm.wasm als application/wasm ({h_.get('Content-Type')}, {len(b_)} Bytes)")
    s2, _h, b2 = get("/g/fotaq/scummvm.wasm", {"If-Modified-Since": h_.get("Last-Modified", "")})
    ok(s2 == 304 and not b2, f"Port: unverändert -> 304 ({s2})")
    for bad in ("/g/fotaq/fotaq.ok", "/g/fotaq/../settings.json", "/g/fotaq/%2e%2e/settings.json", "/g/fotaq/data/../../fotaq_dl/x"):
        s_, _h, _b = get(bad)
        ok(s_ == 404, f"Port: {bad} -> 404 ({s_})")
    q = os.path.join(ns["fotaq_dir"](), "data", "games", "de")
    big = max((os.path.join(q, x) for x in os.listdir(q)), key=os.path.getsize)
    s_, h_, b_ = get("/g/fotaq/data/games/de/" + os.path.basename(big))
    ok(s_ == 200 and len(b_) == os.path.getsize(big), f"Port: Spieldaten gestreamt ({len(b_)} Bytes)")
    if bilder:
        fotaq_mw_bilder(ns, app, PW, bilder, fehler)
    if release:                                     # the real game from the real games port of MoveEye
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=FOTAQ_ARGS)
            fotaq_pruefen(br, f"http://127.0.0.1:{gp}", fehler, warn, bilder)
            br.close()
    code, j = party({"action": "fotaq_delete"})
    ok(code == 200 and not ns["fotaq_installed"]() and not os.path.exists(ns["fotaq_dir"]()), "Entfernen")
    shutil.rmtree(home, ignore_errors=True)


def fotaq_mw_bilder(ns, app, PW, bilder, fehler):
    """screenshots: the tile on /spiele (phone) and the admin tab «Spielecke» (phone, PC)"""
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    os.makedirs(bilder, exist_ok=True)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for name, vp, mob in (("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)):
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                     http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark')}catch(e){}")
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:200]))
                pg.goto(base + "/spiele"); pg.wait_for_timeout(800)
                tile = pg.locator("a.c", has_text="Flight of the Amazon Queen")
                if not tile.count():
                    fehler.append(f"FOTAQ MoveEye {name}: keine Kachel auf /spiele")
                else:
                    tile.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                    pg.screenshot(path=os.path.join(bilder, f"fotaq_kachel_{name}.png"))
                pg.goto(base + "/party"); pg.wait_for_timeout(2500)
                fb = pg.locator("#fotaq-box")
                if not fb.count():
                    fehler.append(f"FOTAQ MoveEye {name}: Abschnitt im Reiter Spielecke fehlt")
                else:
                    fb.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                    pg.screenshot(path=os.path.join(bilder, f"fotaq_admin_{name}.png"))
                for e in errs:
                    fehler.append(f"FOTAQ MoveEye {name}: JavaScript: {e}")
                ctx.close()
            br.close()
    finally:
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description="Test der Spielesammlung (Paket und Browser)")
    ap.add_argument("--zip", default=os.path.join(REPO, "games", "MotionWatch_Spiele.zip"))
    ap.add_argument("--alle", action="store_true", help="auch die älteren Spiele im Browser prüfen")
    ap.add_argument("--nur", default="", help="nur diese Ordner (Komma-Liste)")
    ap.add_argument("--ohne-browser", action="store_true")
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos")
    ap.add_argument("--fotaq", default="", help="Ordner des FOTAQ-Pakets (sonst MW_FOTAQ oder ~/.config/motionwatch/fotaq; fehlt es: übersprungen)")
    ap.add_argument("--nur-fotaq", action="store_true", help="nur «Flight of the Amazon Queen» prüfen")
    ap.add_argument("--fotaq-moveeye", action="store_true", help="FOTAQ in MoveEye: Laden, Prüfsumme, Platz, Spiele-Port, Kachel (gebaute Datei)")
    ap.add_argument("--datei", default="", help="mit --fotaq-moveeye: die gebaute MoveEye-Datei (sonst die neueste)")
    ap.add_argument("--fotaq-release", default="", help="mit --fotaq-moveeye: echte Assets dieses Releases (…/releases/download/<tag>) statt Test-ZIP")
    ap.add_argument("--fotaq-pins", default="", help="mit --fotaq-release: pins.txt (sonst aus dem Release)")
    a = ap.parse_args()
    fehler, warn = [], []
    if a.fotaq_moveeye:
        fotaq_moveeye(a.datei or _neueste_datei(), fehler, warn, a.bilder, a.fotaq_release, a.fotaq_pins)
        for w in warn:
            print("Warnung:", w)
        for f in fehler:
            print("FEHLER:", f)
        print("FOTAQ-MoveEye-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
        sys.exit(1 if fehler else 0)
    if a.nur_fotaq:
        fotaq_lauf(a.fotaq, fehler, warn, a.bilder)
        for w in warn:
            print("Warnung:", w)
        for f in fehler:
            print("FEHLER:", f)
        print("FOTAQ-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
        sys.exit(1 if fehler else 0)
    gj = paket_pruefen(a.zip, fehler, warn)
    print(f"Paket {gj.get('version')}: {len(gj['games'])} Spiele", flush=True)
    if not a.ohne_browser:
        fotaq_lauf(a.fotaq, fehler, warn, a.bilder)
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
                if any(g["dir"] == "kv-wobbly-truck" for g in spiele):
                    wobbly_pruefen(br, base, fehler, a.bilder)
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
