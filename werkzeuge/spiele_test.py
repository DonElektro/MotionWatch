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
     GS-1.7: jeder Abschnitt der neuen Stunt-Piste ist mit beiden Fahrzeugen auf «Einfach» und «Normal» befahrbar (ohne Rettung),
     ein Supersprung landet auf «Einfach» ohne Eingabe in der Luft, der alte Rekord der Stunt-Piste bleibt sichtbar.
     GS-1.8: Stunts füllen das Nitro, der Schub macht schneller und kostet keinen Sprit extra, unter der Mindestfüllung zündet
     er nicht; der Nitro-Knopf am Handy ist mindestens 44 px gross und überdeckt weder Pedale noch den Zurück-Link;
     «Bildwackeln» und «Effekte» werden gespeichert; die Partikelzahl bleibt begrenzt.
     GS-1.9: Geisterfahrer – die beste Fahrt je Strecke / Fahrzeug / Schwierigkeit wird gespeichert (klein, höchstens 18 kB),
     fährt bei der nächsten Fahrt an der aufgezeichneten Stelle mit, nur eine bessere Fahrt ersetzt sie; abschaltbar;
     kaputte Daten oder ein voller Speicher stören das Spiel nicht; die Wilden Hügel der Bestfahrt kommen (ohne ?test=1)
     mit demselben Startwert wieder, ohne Haken gibt es neue Hügel ohne Geist.
     GS-1.10: neue Abschnitte (Sprungbrett, Einsturzbrücke, Feuerringe, Steinschlag, Eis, Schlamm, Verfolgung) sind auf
     «Einfach» und «Normal» befahrbar; Feuerring gibt Bonus, die Brücke stürzt unter einem stehenden Fahrzeug ein (Rettung),
     Fels mit Nitro wird zertrümmert; Welten wechseln etwa alle 500 m, eine Verfolgung etwa alle 1000 m: auf «Einfach»
     wird man nur mitgerissen, auf «Normal» ist es ein Sturz; Hindernisse der Hügel kommen aus dem Startwert; neuer
     Rekord-Platz «stunt3», die älteren Rekorde bleiben sichtbar.

  python3 werkzeuge/spiele_test.py                    # Paket + Browser, nur die Spiele mit 5 Sprachen (ab GS-1.4)
  python3 werkzeuge/spiele_test.py --alle             # dazu die älteren Spiele (2048, Tetris …)
  python3 werkzeuge/spiele_test.py --ohne-browser     # nur das Paket
  python3 werkzeuge/spiele_test.py --bilder ORDNER    # Bildschirmfotos (Handy und PC) jedes Spiels
  python3 werkzeuge/spiele_test.py --nur-fotaq [--fotaq ORDNER]   # nur «Flight of the Amazon Queen» (ScummVM, 639zzg)
  python3 werkzeuge/spiele_test.py --fotaq-moveeye [--datei X.py] [--bilder ORDNER] [--fotaq-release URL]
      # FOTAQ in MoveEye: Laden nur durch den Admin, Pins, freier Platz, veränderte / zu grosse Datei, Entpacken, Kachel,
      # Spiele-Port (wasm-Typ, 304, keine Pfade nach aussen), Entfernen; mit --fotaq-release die echten Assets + das Spiel
      # 3.70.2: Kachel in der PC-Gruppe mit Hinweis (/spiele, Gästeseite, Reiter Spielecke), Warnseite start.html nur mit
      # iPhone / iPad / iPad als Mac (Touch), «Trotzdem starten» -> index.html, am PC (Windows, Mac) gleich weiter

FOTAQ (ab MoveEye 639zzg): ist das Paket da (--fotaq, MW_FOTAQ oder ~/.config/motionwatch/fotaq), lädt es am Handy (quer),
iPad und PC die Startseite (Sprachwahl, Copyright, «✕ Zurück» überdeckt nichts), startet Deutsch und Englisch (ScummVM wählt
das Spiel, die Spielfläche zeigt ein Bild, keine JavaScript-Fehler), prüft die Knöpfe neben dem Spiel, Rechtsklick per Touch
(lange drücken, «🖱 Rechts»), «☰ Menü» und am PC Schnellspeichern (F11) mit Spielstand in IndexedDB nach dem Neuladen.
Fehlt das Paket, wird der Teil übersprungen.

«Was nun?» (eigenes Bilder-Rätsel, Quelle games/wasnun/, mit ?test=1): jedes der 10 Bilder wird am Handy (hoch und quer)
und am PC bis zum Sternebild gelöst; lustige falsche Stellen kosten nichts, das Geheimnis zählt, eine Sackgasse spult genau
einen Schritt zurück, der Tipp zeigt die Gegend und gibt höchstens 1 Stern, Tipp-Flächen mindestens 44 px, Fortschritt
bleibt nach dem Neuladen und das Spiel läuft ohne Speicher. Ab Bild 6 (GS-1.12) dazu: Dinge wählen / abwählen, jede
falsche Kombination und jedes Ding am falschen Ort (kostet nichts, nichts geht verloren), Sackgassen mit Dingen in der
Leiste, jeder Lösungsweg samt Abzeichen «Meister-Lösung», Tipps für Dinge und Kombinationen, ein Spielstand aus 3.73.0
bleibt erhalten, und je Bild 150 zufällige Tipps, nach denen es noch lösbar sein muss. Ab GS-1.14: Versatz-Test – ein
Tipp auf die sichtbare Mitte einer Stelle (oben, Mitte, unten) und eines Platzes der Leiste muss genau dort ankommen, und
das Bild darf nach dem Tipp nicht rutschen (hochkant, auch gerollt / niedriges Fenster / Ränder / 320 px, und quer);
der versteckte Tipp-Test (?tipp=1 oder fünfmal auf den Titel) ist sonst aus. WN_VERSATZ_ALT=1 prüft auch eine alte ZIP. Für den Stand der Quelle
(solange die ZIP ihn nicht enthält):
python3 werkzeuge/spiel_einbauen.py games/wasnun --nach /tmp/t.zip && python3 werkzeuge/spiele_test.py --zip /tmp/t.zip --nur wasnun

Schach (Quelle games/schach/, mit ?test=1; Brett Chessground, Regeln chess.js, Motor Stockfish als WebAssembly, Ersatz in
JavaScript): am iPhone 13 (hoch), Handy quer und PC: Brett so breit wie der Bildschirm, Antippen zeigt die Zielfelder, Zug
bewegt und markiert, Antwort des Computers auf der untersten und obersten Stufe in der Bedenkzeit, Tipp-Pfeil, Lern-Modus
(Dame eingestellt, Matt erlaubt, Patt; beide Knöpfe), Zug zurück, Umwandlung, Rochade, en passant, Matt / Patt / Remis,
zu zweit mit automatischem Drehen, Aufgeben, Einstellungen, Speichern und «Weiterspielen», ohne Speicher, Ersatz-Motor bei
gesperrter .wasm-Datei und bei hängendem Motor, ganze Partien Motor gegen Motor über die Regeln, keine Anfrage nach
aussen, keine Fehler in der Konsole, alle Knöpfe mindestens 44 px. Solange es nicht in der ZIP ist:
python3 werkzeuge/spiel_einbauen.py games/schach --nach /tmp/t.zip && python3 werkzeuge/spiele_test.py --zip /tmp/t.zip --nur schach

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
                    if n.startswith(d + "/lib/") and d == "schach":
                        continue                  # unveränderte Bausteine: Adressen nur im Lizenzkopf; der Browser-Test beweist «keine Anfrage nach aussen»
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
                    m = re.fullmatch(r"bytes=(\d+)-(\d*)", self.headers.get("Range") or "")
                    if m:                               # one piece of a file (FOTAQ iPhone test: the game data in pieces), like the games port
                        n = os.path.getsize(f); a = int(m.group(1)); e = min(int(m.group(2)) if m.group(2) else n - 1, n - 1)
                        if a > e:
                            self.send_response(416); self.send_header("Content-Range", f"bytes */{n}"); self.end_headers(); return
                        self.send_response(206); self.send_header("Content-Type", self.guess_type(f))
                        self.send_header("Content-Range", f"bytes {a}-{e}/{n}"); self.send_header("Content-Length", str(e - a + 1)); self.end_headers()
                        with open(f, "rb") as fh:
                            fh.seek(a); self.wfile.write(fh.read(e - a + 1))
                        return
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
WT_BOT = """window.__bot = (W, I) => { const a = W.B.a, w = W.B.w, x = W.B.x, sl = Math.atan((W.H(x + .04) - W.H(x - .04)) / .08);
  const m = (W.mods || []).find(q => x >= q.x0 && x < q.x1) || {}, intun = m.tun && x > m.tun[0] - 10 && x < m.tun[1];   // a careful driver: no wheelie into the tunnel
  if (W.air.on && W.air.t > 0.12) { const tgt = Math.round((a - sl) / 6.283) * 6.283 + sl, e = a + w * 0.3 - tgt; I.gas = e < -0.12; I.brake = e > 0.12; }
  else { const d = a - sl, dw = d - Math.round(d / 6.283) * 6.283; I.brake = false; I.gas = dw < (intun ? 0.04 : 0.35); } };"""
# GS-1.7: drive through one section of the Stunt-Piste (the first of its kind), or a Supersprung without any input in the air
WT_MODUL = """([veh, diff, typ, frei]) => { const W = window.__wt, I = W.inp; W.freeze(true); W.SET.diff = diff; W.SET.real = 40; W.select(veh, 'stunt'); W.start();
  W.H(8000); const m = W.mods.find(q => q.t === typ); if (!m) return {fehlt: 1};
  W.place(m.x0 + 0.5, 0, 12, 0, 0, 0); const n0 = W.log.length;
  W.sim(45, () => { if (frei) { I.gas = W.B.x < m.sj.x; I.brake = false; } else __bot(W, I); return W.B.x > m.x1 + 3 || W.state !== 'play'; });
  I.gas = I.brake = false; return {state: W.state, durch: W.B.x > m.x1 + 3, rettung: W.nRescue, ids: W.log.slice(n0).map(e => e.id).join(',')}; }"""
WT_MODULE = ("wheelie", "kickers", "loop", "dloop", "wall", "halfpipe", "stairs", "gaps", "dropin", "whoops", "tunnel", "tramp", "coinarcs", "super",
             "spring", "crumble", "rings", "rocks", "ice", "mud", "boss")        # GS-1.10
WT_MUSS = {"spring": "spring", "crumble": "crumble", "rings": "ring", "boss": "boss"}   # the stunt a clean run through the section must bring
# GS-1.10: worlds, zones, rings, bridge, boulders, chase
WT_WELT = """() => { const W = window.__wt, I = W.inp, r = {}; W.freeze(true); W.SET.diff = 1; W.SET.real = 40; W.applyPhys(); I.gas = I.brake = false;
  W.select('truck', 'stunt'); W.start(); W.H(7000);
  r.welten = W.laps.map(l => l.th).slice(0, 6).join(''); r.weltLang = Math.max(...W.laps.slice(1, 8).map((l, i) => l.x0 - W.laps[i].x0));
  const b = W.bosses.map(q => q.x0); r.boss = b.length; r.bossAbst = b.slice(1).map((x, i) => Math.round(x - b[i]));
  r.zonen = [...new Set(W.zones.map(z => z.t))].sort().join(','); r.sortiert = W.zones.every((z, i) => !i || z.x0 >= W.zones[i - 1].x1); r.ringe = W.rings.length;
  const rg = W.rings[0]; W.place(rg.x - 2.5, 0, 14, 0, 0, 0); const y0 = W.B.y; W.place(rg.x - 2.5, rg.y - 0.4 - y0, 14, 2, 0, 0); W.sim(0.5); r.ring = W.log.some(e => e.id === 'ring');
  W.start(); W.H(7000); let m = W.mods.find(q => q.t === 'crumble'); W.place((m.br.r[0] + m.br.r[1]) / 2, 0, 0, 0, 0, 0); W.sim(4); r.bruecke = W.nRescue >= 1 && W.state === 'play';
  W.start(); W.H(7000); m = W.mods.find(q => q.t === 'rocks'); W.place(m.x0 + 12, 0, 12, 0, 0, 0); W.setNitro(100); W.sim(0.2); W.sim(6, () => { I.gas = true; if (!W.nitroOn && W.nitro >= 30) W.fireNitro(); if (!W.nitroOn) W.setNitro(100); return W.log.some(e => e.id === 'smash'); });
  I.gas = false; r.fels = W.log.some(e => e.id === 'smash') && W.state === 'play';
  for (const d of [0, 1]) { W.SET.diff = d; W.applyPhys(); W.start(); W.H(3000); m = W.mods.find(q => q.t === 'boss'); W.place(m.boss[0] + 4, 0, 0, 0, 0, 0); W.sim(9, () => W.state !== 'play');
    r['jagd' + d] = W.state + ':' + W.log.filter(e => /boss/.test(e.id)).map(e => e.id).join(','); }
  W.SET.diff = 1; W.applyPhys();
  const hf = () => { W.select('truck', 'hills'); W.start(); W.place(1900, 0, 0, 0, 0, 0); W.snap(); W.sim(0.6); return JSON.stringify([W.zones, W.rings.map(q => [q.x, q.y]), W.trig.map(q => q.x), W.bosses.map(q => [q.x0, q.x1, q.th])]); };
  const h1 = hf(), h2 = hf(); r.huegelGleich = h1 === h2; r.huegelZonen = W.zones.length; r.huegelBoss = W.bosses.length ? W.bosses[0].x0 : 0; r.huegelWelt = [0, 600, 1100, 1600, 2100, 2600].map(x => W.worldAt(x)).join('');
  localStorage.setItem('kv-game-wobbly-truck-best-stunt2-truck', '7777'); W.select('truck', 'stunt'); W.menu(); const e = document.querySelector('em[data-best=stunt]'); r.alt = e ? e.textContent : '';
  localStorage.removeItem('kv-game-wobbly-truck-best-stunt2-truck'); return r; }"""
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


# GS-1.8: nitro. Two identical runs on the flat start of the hills, one with a boost: faster, same fuel, the bar is used up
WT_NITRO = """() => { const W = window.__wt, I = W.inp, r = {}; W.freeze(true); W.SET.diff = 1; W.SET.real = 40;
  for (const mit of [0, 1]) { W.select('truck', 'hills'); W.start(); W.place(5, 0, 0, 0, 0, 0); I.gas = true; W.sim(1.0);
    if (mit) { W.setNitro(10); r.zuwenig = W.fireNitro(); W.setNitro(100); r.zuendet = W.fireNitro(); }
    W.sim(1.0); r['v' + mit] = Math.hypot(W.B.vx, W.B.vy); r['sprit' + mit] = W.fuel; r['x' + mit] = W.B.x; if (mit) { r.rest = W.nitro; W.sim(3, () => !W.nitroOn); r.leer = W.nitro; r.aus = !W.nitroOn; r.teile = W.parts; } }
  I.gas = false; r.log = W.log.some(e => e.id === 'nitro'); return r; }"""
# GS-1.9: ghost. A run of some seconds ends (crash), the next run has its ghost; a worse run does not replace it
WT_GEIST = """([veh, trk]) => { const W = window.__wt, I = W.inp, r = {}, K = 'kv-game-wobbly-truck-ghost-';
  const lauf = (sek) => { W.start(); W.place(5, 0, 0, 0, 0, 0); W.sim(sek, () => { __bot(W, I); }); const x = W.B.x; I.gas = I.brake = false; W.crash(); W.sim(4, () => W.state === 'over'); return x; };
  const keys = () => Object.keys(localStorage).filter(k => k.startsWith(K));
  W.freeze(true); W.SET.diff = 1; W.SET.real = 40; W.SET.ghost = 1; W.SET.ghostHills = 1; keys().forEach(k => localStorage.removeItem(k)); W.select(veh, trk);
  const a = []; for (let i = 0; i < 400; i++) a.push(Math.round(i * 31.3), Math.round(Math.sin(i) * 400), Math.round(i * 5 - 300)); const d = W.gDec(W.gEnc(a));
  r.codec = d.n === 400 && Math.abs(d.x[399] - a[1197] * .05) < .01 && Math.abs(d.y[200] - a[601] * .05) < .01 && Math.abs(d.a[399] - a[1199] * .02) < .01;
  W.start(); r.ohne = W.ghost === null; r.x1 = lauf(6); r.s1 = W.score(); r.over = W.state; r.seed1 = W.seed;
  r.keys = keys(); r.len = r.keys.length ? localStorage.getItem(r.keys[0]).length : 0;
  W.start(); r.g = W.ghost; r.seed2 = W.seed; const p = W.ghostAt(3), q = W.ghostAt(0); r.p = !!(p && p.x > 8 && p.x < r.x1 + 1 && q && Math.abs(q.x - 3) < 0.6);
  lauf(2); r.s2 = W.score(); W.start(); r.bleibt = !!(W.ghost && W.ghost.s === r.s1);                      // a worse run: the ghost stays
  lauf(9); r.s3 = W.score(); W.start(); r.besser = !!(W.ghost && W.ghost.s === r.s3 && r.s3 > r.s1);       // a better run replaces it
  W.SET.ghost = 0; W.start(); r.aus = W.ghost === null; W.SET.ghost = 1;
  W.SET.diff = 0; W.applyPhys(); W.start(); r.andere = W.ghost === null; W.SET.diff = 1; W.applyPhys();   // another difficulty has its own ghost
  localStorage.setItem(r.keys[0], '{"v":1,"s":5,"seed":7,"d":"###kaputt###"}'); W.start(); r.kaputt = W.ghost === null && W.state === 'play';
  localStorage.setItem(r.keys[0], 'x'); W.start(); r.kaputt = r.kaputt && W.ghost === null && W.state === 'play';
  const alt = Storage.prototype.setItem; Storage.prototype.setItem = () => { throw new Error('QuotaExceededError'); };    // storage full
  try { lauf(4); r.voll = W.state === 'over'; } catch (e) { r.voll = false; r.vollFehler = String(e); } Storage.prototype.setItem = alt;
  keys().forEach(k => localStorage.removeItem(k)); return r; }"""
WT_GEIST_HUEGEL = """() => { const W = window.__wt, I = W.inp, r = {}; W.freeze(true); W.SET.diff = 1; W.SET.ghost = 1; W.SET.ghostHills = 1; W.select('truck', 'hills');
  W.start(); W.place(5, 0, 0, 0, 0, 0); W.sim(6, () => { I.gas = W.B.a < 0.3; }); I.gas = false; W.crash(); W.sim(4, () => W.state === 'over'); r.seed1 = W.seed; r.h1 = W.H(300);
  W.start(); r.seed2 = W.seed; r.h2 = W.H(300); r.geist = !!W.ghost;
  W.SET.ghostHills = 0; const s = new Set(); for (let i = 0; i < 4; i++) { W.start(); s.add(W.seed); r.ohne = W.ghost === null; } r.neu = s.size > 1; W.SET.ghostHills = 1;
  W.menu(); r.zeile = !!document.getElementById('ghostHills'); return r; }"""
WT_KNOEPFE = """() => { const b = id => { const e = document.getElementById(id), r = e.getBoundingClientRect(); return getComputedStyle(e).display === 'none' ? null : [r.left, r.top, r.right, r.bottom]; };
  const n = b('nitroP'), out = []; if (!n) return ['fehlt']; if (n[2] - n[0] < 44 || n[3] - n[1] < 44) out.push('kleiner als 44 px');
  if (n[0] < 0 || n[1] < 0 || n[2] > innerWidth || n[3] > innerHeight) out.push('ausserhalb');
  for (const id of ['gasP', 'brakeP', 'trickP', 'backLink', 'setBtn', 'muteBtn', 'restartBtn']) { const o = b(id); if (o && n[0] < o[2] && o[0] < n[2] && n[1] < o[3] && o[1] < n[3]) out.push('überdeckt ' + id); }
  return out; }"""


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
            best = pg.evaluate("() => localStorage.getItem('kv-game-wobbly-truck-best-stunt3-bike')")
            if r["state"] != "over" or not best:
                fehler.append(f"{d} {name}: Sturz / Rekord je Strecke und Fahrzeug fehlt ({r['state']}, {best})")
            if mobil:   # GS-1.7: every section drivable (Einfach and Normal, both vehicles), Supersprung on Einfach without input
                nm = 0
                for veh in ("truck", "bike"):
                    for diff in (0, 1):
                        for typ in WT_MODULE:
                            r = pg.evaluate(WT_MODUL, [veh, diff, typ, False])
                            if r.get("fehlt") or r["state"] != "play" or not r["durch"] or r["rettung"] or (typ in WT_MUSS and WT_MUSS[typ] not in r["ids"].split(",")):
                                fehler.append(f"{d} {name}: Abschnitt {typ} mit {veh} auf {['Einfach', 'Normal'][diff]} nicht befahrbar ({r})")
                            else:
                                nm += 1
                    r = pg.evaluate(WT_MODUL, [veh, 0, "super", True])
                    if r.get("state") != "play" or "super" not in r.get("ids", ""):
                        fehler.append(f"{d} {name}: Supersprung mit {veh} auf Einfach ohne Eingabe nicht gelandet ({r})")
                    else:
                        ok.append(f"supersprung-frei-{veh}")
                ok.append(f"{nm}/{2 * 2 * len(WT_MODULE)} Abschnitte")
                # the old Stunt-Piste record stays visible («alte Strecke»), the new course has its own slot
                txt = pg.evaluate("""() => { localStorage.setItem('kv-game-wobbly-truck-best-stunt-bike', '8339'); __wt.select('bike', 'stunt'); __wt.menu();
                    const e = document.querySelector('em[data-best=stunt]'); return e ? e.textContent : ''; }""")
                if "8339" not in txt:
                    fehler.append(f"{d} Handy: alter Rekord der Stunt-Piste wird nicht gezeigt ({txt!r})")
            # GS-1.8 nitro: stunts fill it, the boost is faster, costs no extra fuel, does not fire below the minimum
            r = pg.evaluate(WT_RUN, ["truck", "hills", "salto"])
            if not pg.evaluate("() => __wt.nitro > 5"):
                fehler.append(f"{d} {name}: ein Salto füllt das Nitro nicht")
            r = pg.evaluate(WT_NITRO)
            if r["zuwenig"] or not r["zuendet"] or not r["log"] or r["v1"] < r["v0"] + 2 or abs(r["sprit1"] - r["sprit0"]) > 0.01 or r["leer"] > 0.5 or not r["aus"] or r["teile"] > 260:
                fehler.append(f"{d} {name}: Nitro (zündet, schneller, kein Sprit extra, leer, Partikel begrenzt) stimmt nicht ({r})")
            else:
                ok.append("nitro")
            r = pg.evaluate(WT_WELT)                 # GS-1.10 worlds, new elements, chase
            gut = (r["welten"].startswith("01234") and r["weltLang"] < 1000 and r["boss"] >= 4 and all(850 <= x <= 1500 for x in r["bossAbst"])
                   and r["zonen"] == "ice,mud,spring" and r["sortiert"] and r["ringe"] >= 6 and r["ring"] and r["bruecke"] and r["fels"]
                   and r["jagd0"].startswith("play:") and "bosspush" in r["jagd0"] and r["jagd1"].split(":")[0] in ("crash", "over")
                   and r["huegelGleich"] and r["huegelZonen"] >= 3 and r["huegelBoss"] == 1000 and r["huegelWelt"] == "523401" and "7777" in r["alt"])
            if not gut:
                fehler.append(f"{d} {name}: Welten / neue Elemente / Verfolgung stimmen nicht ({r})")
            else:
                ok.append("welten")
            for veh, trk in (("truck", "stunt"), ("bike", "hills")):      # GS-1.9 ghost of the best run
                r = pg.evaluate(WT_GEIST, [veh, trk])
                gut = (r["codec"] and r["ohne"] and r["over"] == "over" and len(r["keys"]) == 1 and 40 < r["len"] <= 18300 and r["g"] and r["seed1"] == r["seed2"]
                       and r["p"] and r["bleibt"] and r["besser"] and r["aus"] and r["andere"] and r["kaputt"] and r["voll"])
                if not gut:
                    fehler.append(f"{d} {name}: Geisterfahrer {veh}/{trk} stimmt nicht ({r})")
                else:
                    ok.append(f"geist-{veh}")
            if mobil:   # the hills of the best run come back with the same seed (only without ?test=1: there the seed is fixed anyway)
                pg2 = ctx.new_page()
                pg2.on("pageerror", lambda e, fe=fe: fe.append(str(e)[:300]))
                pg2.goto(f"{base}/g/{d}/index.html", wait_until="load", timeout=30000)
                pg2.wait_for_timeout(300)
                r = pg2.evaluate(WT_GEIST_HUEGEL)
                if r["seed1"] != r["seed2"] or abs(r["h1"] - r["h2"]) > 1e-9 or not r["geist"] or not r["ohne"] or not r["neu"] or not r["zeile"]:
                    fehler.append(f"{d} Handy: Hügel der Bestfahrt / neue Hügel ohne Geist stimmt nicht ({r})")
                else:
                    ok.append("geist-hügel")
                pg2.evaluate("() => Object.keys(localStorage).filter(k => k.includes('-ghost-')).forEach(k => localStorage.removeItem(k))")
                pg2.close()
            if mobil:   # the trick button is there for the motorbike while playing
                pg.evaluate("() => { __wt.select('bike', 'stunt'); __wt.start(); }")
                if not pg.locator("#trickP").is_visible():
                    fehler.append(f"{d} Handy: Trick-Knopf fehlt beim Motorrad")
                for quer in (False, True):      # GS-1.8: the nitro button (portrait and landscape) is big enough and covers nothing
                    pg.set_viewport_size({"width": 844, "height": 390} if quer else vp)
                    pg.wait_for_timeout(150)
                    kn = pg.evaluate(WT_KNOEPFE)
                    if kn:
                        fehler.append(f"{d} Handy{' quer' if quer else ''}: Nitro-Knopf: {', '.join(kn)}")
                pg.evaluate("() => { __wt.freeze(true); __wt.setNitro(100); }")
                pg.locator("#nitroP").tap()
                if not pg.evaluate("() => __wt.nitroOn"):
                    fehler.append(f"{d} Handy: Tipp auf den Nitro-Knopf zündet nicht")
                else:
                    ok.append("nitro-knopf")
            # settings: saved in localStorage, «Standard» resets
            pg.evaluate("() => { __wt.freeze(false); __wt.showSettings(); }")
            pg.locator("[data-diff='2']").click()
            pg.locator("#s_real").fill("80")
            pg.locator("#s_shake").uncheck()            # GS-1.8: «Bildwackeln» and «Effekte»
            pg.locator("[data-fx='0']").click()
            s = pg.evaluate("() => JSON.parse(localStorage.getItem('kv-game-wobbly-truck-settings') || '{}')")
            if s.get("shake") != 0 or s.get("fx") != 0:
                fehler.append(f"{d} {name}: «Bildwackeln» / «Effekte» nicht gespeichert ({s})")
            if s.get("diff") != 2 or s.get("real") != 80:
                fehler.append(f"{d} {name}: Einstellungen nicht gespeichert ({s})")
            pg.locator("#resetBtn").click()
            s = pg.evaluate("() => JSON.parse(localStorage.getItem('kv-game-wobbly-truck-settings') || '{}')")
            if s.get("diff") != 1 or s.get("real") != 40 or s.get("shake") != 1 or s.get("fx") != 1:
                fehler.append(f"{d} {name}: «Standard» setzt nicht zurück ({s})")
            if bilder:
                pg.screenshot(path=os.path.join(bilder, f"spiel_{d}_einstellungen_{'handy' if mobil else 'pc'}.png"))
        except Exception as e:
            fehler.append(f"{d} {name}: {e.__class__.__name__}: {str(e)[:200]}")
        for x in fe:
            fehler.append(f"{d} {name}: JavaScript: {x}")
        print(f"{d:<20} {name:<6} Stunts/Looping: {', '.join(ok) or '-'}", flush=True)
        ctx.close()


# «Was nun?» (eigenes Spiel, Bilder-Rätsel): mit ?test=1 gibt es window.__wn (Zustand, nächste richtige Stelle, Tipp-Flächen
# in Bildschirm-Pixeln, «richtiger Moment»); Bewegungen laufen 6-mal schneller. Getippt wird echt (Touch bzw. Maus).
# Je Bild: lustige falsche Stellen (kosten nichts), das Geheimnis, eine Sackgasse (spult genau einen Schritt zurück),
# ein falscher Moment, der Tipp-Knopf (Gegend pulsiert, höchstens 1 Stern) und die ganze Lösung bis zum Sternebild.
WN = {
    "garten": {"gags": ["hahn", "vogel", "apfel", "sonne", "wolke", "maulwurf", "igel", "sprenger", "krone"], "geheim": "busch", "sack": ["knoten", "hahn"]},
    "zeltplatz": {"gags": ["zelt", "tasse", "feuer", "fahne", "vogel", "rucksack", "tanne", "sonne", "kessel"], "geheim": "stiefel", "sack": ["holz", "zuendholz"], "zeit": "zuendholz"},
    "alp": {"gags": ["horn", "kuh", "kraehe", "tuer", "kamin", "kanne", "edelweiss", "sonne"], "geheim": "gipfel", "sack": ["kaese"]},
    "werkstatt": {"gags": ["schublade", "robo", "hebel", "radio", "stock", "werkzeug", "fenster", "lampe"], "geheim": "mausloch",
                  "sack": ["magnet", "schublade", "schublade", "robo", "hebel"], "zeit": "magnet"},
    "kueche": {"gags": ["maus", "katze", "glocke", "uhr", "mond", "toaster", "besen", "napf"], "geheim": "schrank", "sack": ["wecker"], "zeit": "maus"},
}
# ab Bild 6 (GS-1.12): Dinge mitnehmen, kombinieren, an einer Stelle benutzen; zwei Ansichten; zwei Lösungswege; Zeit.
# gags: lustige Stellen («!x» = neutrale Stelle wie die Tür zwischen zwei Ansichten); sack: je Sackgasse zuerst der Lösung
# folgen, bis «vor» (JavaScript über den Zustand s) stimmt, dann «tu» (["s", Stelle] oder ["p", Ding in der Leiste]) - der
# letzte Tipp davon muss genau einen Schritt zurückspulen, mit allem, was in der Leiste war.
WN2 = {
    "weiher": {"gags": ["mann", "axt", "haus", "tanne", "mond", "boot", "laterne", "schnee", "feuer"], "geheim": "loch",
               "sack": [{"vor": "s.tasche.includes('eimer_heiss')", "tu": [["p", "eimer_heiss"], ["s", "mann"]]}]},
    "dachboden": {"gags": ["schirm", "geist", "wanne", "luke", "affe", "lampe", "wimpel", "koffer", "pferd"], "geheim": "bildnis",
                  "sack": [{"vor": "true", "tu": [["s", "kissen"]]}]},
    "leuchtturm": {"gags": ["lampe", "tuer", "tuempel", "schiff", "glocke", "fahne", "klippen", "fenster", "moewe", "wolke"], "geheim": "krake",
                   "sack": [{"vor": "s.tuer", "tu": [["s", "rad"], ["s", "rad"], ["s", "tuer"]]}]},
    "museum": {"gags": ["krone", "sockel", "ruestung", "heizung", "bild1", "kamera", "fenster", "!tuer", "waechter", "schirm", "kaffee", "wuhr", "brett", "!tuer2"], "geheim": "helm",
               "sack": [{"vor": "true", "tu": [["s", "lichtsch"]]}, {"vor": "s.sicht === 'wache' && s.tasche.includes('oel')", "tu": [["s", "hebel"]]}]},
    "uhrturm": {"gags": ["kuckuck", "luecke", "ra", "trommel", "pendel", "riesen", "blatt", "luke", "gewicht"], "geheim": "spinne",
                "sack": [{"vor": "s.gewicht === 'oben' && s.rad === 'drin'", "tu": [["s", "pendel"]]}]},
}
WN_ALT = '{"sterne":{"garten":3,"zeltplatz":2,"alp":3,"werkstatt":1,"kueche":2},"geheim":{"garten":1,"alp":1},"stumm":false}'   # ein Spielstand aus 3.73.0 (GS-1.11)
WN_Z = "() => ({z: JSON.stringify(__wn.S.zustand), fehler: __wn.S.fehler, tipp: __wn.S.tipp, spul: __wn.S.spul, fertig: __wn.S.fertig, next: (__wn.next ? __wn.next() : __wn.naechster()), tasche: (__wn.S.zustand.tasche || []).join(','), wahl: __wn.S.wahl})"


def wasnun_pruefen(br, pw, base, fehler, bilder):
    d = "wasnun"
    url = f"{base}/g/{d}/index.html?test=1"

    def seite(ctx, name):
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else r.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: fehler.append(f"{d} {name}: JavaScript: {str(e)[:300]}"))
        pg.on("console", lambda m: fehler.append(f"{d} {name}: console.error: {m.text[:200]}") if m.type == "error" else None)
        pg.goto(url, wait_until="load", timeout=30000)
        pg.wait_for_function("() => window.__wn && document.querySelectorAll('#karten .karte').length > 0", timeout=10000)
        return pg

    def bild(pg, was, name):
        if bilder:
            pg.wait_for_timeout(250)
            pg.screenshot(path=os.path.join(bilder, f"wasnun_{was}_{name}.png"))

    def frei(pg):
        pg.wait_for_function("() => __wn.frei()", timeout=20000)

    def tippe(pg, touch, sid, wann="gut", name=""):
        """eine Stelle wirklich antippen (wann: 'gut' = richtiger Moment abwarten, 'schlecht' = falschen, '' = sofort)"""
        frei(pg)
        if wann:
            pg.wait_for_function(f"id => __wn.frei() && __wn.{wann}(id)", arg=sid, timeout=20000, polling=40)
        st = next((x for x in pg.evaluate("() => __wn.stellen()") if x["id"] == sid), None)
        if not st or st["x"] is None:
            fehler.append(f"{d} {name}: Stelle «{sid}» ist nicht antippbar"); return False
        (pg.touchscreen.tap if touch else pg.mouse.click)(st["x"], st["y"])
        pg.wait_for_timeout(30)
        frei(pg)
        return True

    def groessen(pg, name, sz):
        for x in pg.evaluate("() => __wn.stellen()"):
            if x["w"] < 43.9 or x["h"] < 43.9:
                fehler.append(f"{d} {name}: {sz} Stelle «{x['id']}» nur {x['w']:.0f} × {x['h']:.0f} px (mindestens 44)")
            if x["x"] is None:
                fehler.append(f"{d} {name}: {sz} Stelle «{x['id']}» ist ganz verdeckt")

    def loese(pg, touch, name, sz, mitte="", falsch=""):
        """der Lösung folgen bis zum Sternebild; falsch: bei dieser Stelle zuerst einmal im falschen Moment tippen"""
        n = 0
        while n < 14:
            z = pg.evaluate(WN_Z)
            if z["fertig"]:
                break
            if touch:
                groessen(pg, name, sz)
            if falsch and z["next"] == falsch:
                tippe(pg, touch, falsch, "schlecht", name)
                z2 = pg.evaluate(WN_Z)
                if z2["fehler"] != z["fehler"] + 1 or z2["z"] != z["z"]:
                    fehler.append(f"{d} {name}: {sz} falscher Moment bei «{falsch}» zählt nicht als ein Fehlversuch ohne Verlust ({z2})")
                falsch = ""
                continue
            if not tippe(pg, touch, z["next"], "gut", name):
                return False
            z2 = pg.evaluate(WN_Z)
            if z2["z"] == z["z"] and not z2["fertig"]:
                fehler.append(f"{d} {name}: {sz} Schritt «{z['next']}» bringt nichts ({pg.inner_text('#text')[:80]})"); return False
            if z2["fehler"] != z["fehler"]:
                fehler.append(f"{d} {name}: {sz} richtiger Schritt «{z['next']}» zählt als Fehlversuch")
            n += 1
            if mitte and n == 2:
                bild(pg, mitte, name)
        try:
            pg.wait_for_selector("#ende:not([hidden]) .gs", timeout=8000)
        except Exception:
            fehler.append(f"{d} {name}: {sz} nach {n} Schritten kein Sternebild (nicht lösbar?)"); return False
        if mitte and not 4 <= n <= 8:               # the clean run from the start
            fehler.append(f"{d} {name}: {sz} hat {n} Schritte (soll 4 bis 8)")
        return True

    def sterne(pg):
        return pg.locator("#ende .gs svg.an").count()

    # ---- ab Bild 6: Dinge in der Leiste -------------------------------------------------------------------------------------
    def platz(pg, touch, did, name=""):
        frei(pg)
        p = next((x for x in pg.evaluate("() => __wn.plaetze()") if x["id"] == did), None)
        if not p:
            fehler.append(f"{d} {name}: «{did}» liegt nicht in der Leiste"); return False
        if p["w"] < 43.9 or p["h"] < 43.9:
            fehler.append(f"{d} {name}: Platz von «{did}» nur {p['w']:.0f} × {p['h']:.0f} px")
        (pg.touchscreen.tap if touch else pg.mouse.click)(p["x"], p["y"])
        pg.wait_for_timeout(30)
        frei(pg)
        return True

    def abwaehlen(pg, touch, name):
        w = pg.evaluate("() => __wn.S.wahl")
        if w:
            platz(pg, touch, w, name)

    def schritt2(pg, touch, name, weg=""):
        """der nächste richtige Schritt (Stelle, Ding an Stelle, zwei Dinge kombinieren, oder warten); gibt ihn zurück"""
        n = pg.evaluate("w => __wn.naechster(w || undefined)", weg)
        if n.get("warte"):
            pg.wait_for_timeout(300); return n
        abwaehlen(pg, touch, name)
        if n.get("kombi"):
            platz(pg, touch, n["kombi"][0], name); platz(pg, touch, n["kombi"][1], name)
        else:
            if n.get("ding"):
                platz(pg, touch, n["ding"], name)
            tippe(pg, touch, n["stelle"], "gut", name)
        return n

    def unsinn(pg, touch, name, sz, getan):
        """alles ausprobieren, was nichts bringt: jedes neue Ding wählen / abwählen, am Geheimnis benutzen, falsch kombinieren"""
        z = pg.evaluate(WN_Z)
        for did in [x for x in z["tasche"].split(",") if x and ("d", x) not in getan]:
            getan.add(("d", did))
            platz(pg, touch, did, name)
            if pg.evaluate("() => __wn.S.wahl") != did or not pg.locator("#tasche .platz.wahl").count():
                fehler.append(f"{d} {name}: {sz} «{did}» lässt sich nicht wählen (hervorgehoben)")
            platz(pg, touch, did, name)
            if pg.evaluate("() => __wn.S.wahl"):
                fehler.append(f"{d} {name}: {sz} «{did}» lässt sich nicht abwählen")
            platz(pg, touch, did, name); tippe(pg, touch, WN2[sz]["geheim"], "", name)       # am falschen Ort benutzen
            z2 = pg.evaluate(WN_Z)
            if z2["z"] != z["z"] or z2["fehler"] != z["fehler"] or z2["wahl"]:
                fehler.append(f"{d} {name}: {sz} «{did}» an der falschen Stelle ändert oder kostet etwas ({z2})")
        for k in pg.evaluate("() => __wn.kombis()"):
            if k["gibt"] or ("k", k["a"], k["b"]) in getan:
                continue
            getan.add(("k", k["a"], k["b"]))
            platz(pg, touch, k["a"], name); platz(pg, touch, k["b"], name)
            z2 = pg.evaluate(WN_Z)
            if z2["z"] != z["z"] or z2["fehler"] != z["fehler"] or z2["wahl"] or not pg.inner_text("#text").strip():
                fehler.append(f"{d} {name}: {sz} falsche Kombination {k['a']} + {k['b']} ändert oder kostet etwas ({z2})")

    def loese2(pg, touch, name, sz, weg="", bis="", probieren=None, tipps=False, bilder_ab=""):
        """der Lösung folgen: bis zum Sternebild oder bis «bis» stimmt. probieren: Menge für unsinn(); tipps: vor jedem Schritt den Tipp prüfen"""
        n, gewartet, hatbild = 0, 0, set()
        while n < 40 and gewartet < 80:
            z = pg.evaluate(WN_Z)
            if z["fertig"] or (bis and pg.evaluate("() => { const s = __wn.S.zustand; return !!(" + bis + "); }")):
                break
            if touch:
                groessen(pg, name, sz)
            if len(z["tasche"].split(",")) > 4:
                fehler.append(f"{d} {name}: {sz} mehr als 4 Dinge in der Leiste ({z['tasche']})")
            if probieren is not None:
                unsinn(pg, touch, name, sz, probieren)
            if bilder_ab and "mitte" not in hatbild and z["tasche"].count(",") >= 1:
                hatbild.add("mitte"); bild(pg, f"{bilder_ab}_mitte", name)
            if tipps:
                tipp_pruefen(pg, touch, name, sz, weg, n)
            s_ = schritt2(pg, touch, name, weg)
            if s_.get("warte"):
                gewartet += 1; continue
            z2 = pg.evaluate(WN_Z)
            if z2["z"] == z["z"] and not z2["fertig"]:
                fehler.append(f"{d} {name}: {sz} Schritt {s_} bringt nichts ({pg.inner_text('#text')[:80]})"); return False
            if z2["fehler"] != z["fehler"]:
                fehler.append(f"{d} {name}: {sz} richtiger Schritt {s_} zählt als Fehlversuch")
            if bilder_ab and s_.get("kombi") and "kombi" not in hatbild:
                hatbild.add("kombi"); bild(pg, f"{bilder_ab}_kombi", name)
            n += 1
        if bis:
            return True
        try:
            pg.wait_for_selector("#ende:not([hidden]) .gs", timeout=8000)
        except Exception:
            fehler.append(f"{d} {name}: {sz} Weg «{weg}»: nach {n} Schritten kein Sternebild (nicht lösbar?)"); return False
        return True

    def tipp_pruefen(pg, touch, name, sz, weg, n):
        """Tipp-Knopf: beim ersten Mal nachfragen; Kreis über der Gegend, bei zwei Dingen pulsieren beide in der Leiste"""
        nx = pg.evaluate("() => __wn.naechster()")
        b = pg.locator("#bTipp"); (b.tap if touch else b.click)()
        if pg.locator("#tJa").count():
            j = pg.locator("#tJa"); (j.tap if touch else j.click)()
        pg.wait_for_timeout(120)
        txt = pg.inner_text("#text")
        if nx.get("kombi"):
            if pg.locator("#tasche .platz.puls").count() != 2 or "zusammen" not in txt:
                fehler.append(f"{d} {name}: {sz} Tipp für eine Kombination zeigt nicht beide Dinge ({txt[:60]})")
        else:
            c = pg.evaluate("""id => { const c = document.querySelector('#fx .tippkreis'); if (!c) return null; const b = document.getElementById('bild').getBoundingClientRect(),
              st = __wn.stellen().find(x => x.id === id), k = b.width / 800, x = b.left + c.cx.baseVal.value * k, y = b.top + c.cy.baseVal.value * k;
              return {r: c.r.baseVal.value * k, d: Math.hypot(x - st.x, y - st.y)}; }""", nx.get("stelle"))
            if not c or c["d"] > c["r"] or c["r"] < 38:
                fehler.append(f"{d} {name}: {sz} Tipp-Kreis zeigt nicht die Gegend von «{nx.get('stelle')}» ({c})")
            if nx.get("ding") and n > 0 and not pg.locator("#tasche .platz.puls").count():
                fehler.append(f"{d} {name}: {sz} genauerer Tipp zeigt das nötige Ding «{nx['ding']}» nicht")
        if not txt.strip():
            fehler.append(f"{d} {name}: {sz} Tipp ohne Text")

    def neu(pg, touch, name, i, sz):
        """ein Bild ab Nummer 6: am Handy alles (Unsinn, Geheimnis, Sackgassen, Tipps, jeder Lösungsweg), am PC jeder Weg sauber"""
        k = WN2[sz]
        wege = pg.evaluate("() => __wn.wege()")
        nochmal = lambda: (pg.locator("#eNochmal").tap if touch else pg.locator("#eNochmal").click)()
        if touch:
            groessen(pg, name, sz)
            for g in k["gags"]:
                frei_ = g.startswith("!")
                z = pg.evaluate(WN_Z); t0 = pg.inner_text("#text")
                tippe(pg, touch, g.lstrip("!"), "", name)
                z2 = pg.evaluate(WN_Z)
                if z2["fehler"] or (not frei_ and z2["next"] != z["next"]):
                    fehler.append(f"{d} {name}: {sz} lustige Stelle «{g}» kostet etwas oder ändert den Weg ({z2})")
                if pg.inner_text("#text") == t0:
                    fehler.append(f"{d} {name}: {sz} Stelle «{g}» sagt nichts Neues")
            tippe(pg, touch, k["geheim"], "", name)
            if not pg.evaluate("id => !!__wn.MERK.geheim[id]", sz) or "Geheimnis gefunden" not in pg.inner_text("#text") or pg.evaluate(WN_Z)["fehler"]:
                fehler.append(f"{d} {name}: {sz} Geheimnis «{k['geheim']}» nicht gezählt")
            getan = set()
            for nr, sk in enumerate(k["sack"]):
                loese2(pg, touch, name, sz, wege[0], bis=sk["vor"], probieren=getan)
                for j, (art, was) in enumerate(sk["tu"]):
                    z = pg.evaluate(WN_Z)
                    platz(pg, touch, was, name) if art == "p" else tippe(pg, touch, was, "gut", name)
                    if j == len(sk["tu"]) - 1:
                        z2 = pg.evaluate(WN_Z)
                        vorher = json.loads(z["z"]); nachher = json.loads(z2["z"])
                        if z2["spul"] != z["spul"] + 1 or z2["fehler"] != z["fehler"] + 1 or nachher != vorher:
                            fehler.append(f"{d} {name}: {sz} Sackgasse «{was}» spult nicht genau einen Schritt zurück ({z} -> {z2})")
                        if "Zurückgespult" not in pg.inner_text("#text"):
                            fehler.append(f"{d} {name}: {sz} Sackgasse ohne freundliche Meldung")
                        bild(pg, f"{i + 1}_nach_sackgasse{nr + 1}", name)
            if loese2(pg, touch, name, sz, wege[0], probieren=getan):
                if sterne(pg) != 2 or pg.evaluate("id => __wn.MERK.sterne[id]", sz) != 2:
                    fehler.append(f"{d} {name}: {sz} mit {len(k['sack'])} Fehlversuch(en) {sterne(pg)} Sterne statt 2")
            nochmal()
            if loese2(pg, touch, name, sz, wege[-1], tipps=True) and (sterne(pg) != 1 or pg.evaluate("id => __wn.MERK.sterne[id]", sz) != 2):
                fehler.append(f"{d} {name}: {sz} mit Tipp {sterne(pg)} Sterne (soll 1), gemerkt bleibt 2")
            nochmal()
        for nr, w in enumerate(wege):
            if nr:
                nochmal()
            if loese2(pg, touch, name, sz, w, bilder_ab=f"{i + 1}" if nr == 0 else f"{i + 1}_meister"):
                if sterne(pg) != 3:
                    fehler.append(f"{d} {name}: {sz} Weg «{w}» ohne Fehlversuch {sterne(pg)} Sterne statt 3")
                abz = pg.locator("#ende .abz").count() > 0
                if abz != (w == "meister"):
                    fehler.append(f"{d} {name}: {sz} Weg «{w}»: Abzeichen Meister-Lösung {'da' if abz else 'fehlt'}")
                if not pg.inner_text("#ende .gesch").strip():
                    fehler.append(f"{d} {name}: {sz} Sternebild ohne Schluss-Geschichte")
                pg.wait_for_timeout(700)
                bild(pg, f"{i + 1}_sterne" + ("" if nr == 0 else "_meister"), name)
        if len(wege) > 1 and not pg.evaluate("id => !!__wn.MERK.meister[id]", sz):
            fehler.append(f"{d} {name}: {sz} Meister-Lösung nicht gemerkt")

    for name, touch in (("Handy", True), ("PC", False)):
        ctx = br.new_context(**pw.devices["iPhone 13"]) if touch else br.new_context(viewport={"width": 1280, "height": 800})
        pg = seite(ctx, name)
        try:
            ids = pg.evaluate("() => __wn.SZ.map(s => s.id)")
            if ids == list(WN):                # eine ZIP mit der ersten Fassung (5 Bilder, bis GS-1.11): nur diese prüfen
                if touch:
                    print(f"{d}: diese ZIP enthält noch die Fassung mit 5 Bildern – die Bilder 6-10 (games/wasnun/) sind nicht geprüft", flush=True)
            elif ids != list(WN) + list(WN2):
                fehler.append(f"{d} {name}: Bilder {ids} statt {list(WN) + list(WN2)}")
            voll = f"{3 * len(ids)}/{3 * len(ids)}"; geh = f"{len(ids)}/{len(ids)}"; 
            if pg.locator("#karten .karte.zu").count() != len(ids) - 1:
                fehler.append(f"{d} {name}: am Anfang sollen alle Bilder ausser dem ersten gesperrt sein")
            if f"0/{3 * len(ids)}" not in pg.inner_text("#chipSterne") or f"0/{len(ids)}" not in pg.inner_text("#chipGeheim"):
                fehler.append(f"{d} {name}: Anzeige Sterne / Geheimnisse am Anfang falsch")
            (pg.locator("#karten .karte").nth(1).tap if touch else pg.locator("#karten .karte").nth(1).click)(force=True)
            pg.wait_for_timeout(200)
            if pg.evaluate("() => __wn.S.i") != -1:
                fehler.append(f"{d} {name}: ein gesperrtes Bild lässt sich öffnen")
            bild(pg, "wahl_anfang", name)
            for i, sz in enumerate(ids):
                k = WN.get(sz, {})
                karte = pg.locator("#karten .karte").nth(i)
                if "zu" in (karte.get_attribute("class") or ""):
                    fehler.append(f"{d} {name}: {sz} ist nach dem Lösen des Bildes davor nicht offen"); break
                (karte.tap if touch else karte.click)()
                pg.wait_for_function("i => __wn.S.i === i", arg=i)
                bild(pg, f"{i + 1}_start", name)
                if sz in WN2:
                    neu(pg, touch, name, i, sz)
                    b = pg.locator("#eAlle"); (b.tap if touch else b.click)()
                    continue
                if touch:
                    # 1. Durchgang: Ausprobieren, Geheimnis, Sackgasse, falscher Moment -> 2 Sterne
                    groessen(pg, name, sz)
                    z0 = pg.evaluate(WN_Z)
                    for g in k.get("gags", []):
                        t0 = pg.inner_text("#text")
                        tippe(pg, touch, g, "", name)
                        z = pg.evaluate(WN_Z)
                        if z["fehler"] or z["next"] != z0["next"]:
                            fehler.append(f"{d} {name}: {sz} lustige Stelle «{g}» kostet etwas oder ändert den Weg ({z})")
                        if pg.inner_text("#text") == t0:
                            fehler.append(f"{d} {name}: {sz} Stelle «{g}» sagt nichts Neues")
                    tippe(pg, touch, k["geheim"], "", name)
                    if not pg.evaluate("id => !!__wn.MERK.geheim[id]", sz) or "Geheimnis gefunden" not in pg.inner_text("#text") or pg.evaluate(WN_Z)["fehler"]:
                        fehler.append(f"{d} {name}: {sz} Geheimnis «{k['geheim']}» nicht gezählt")
                    for j, s_ in enumerate(k["sack"]):
                        z = pg.evaluate(WN_Z)
                        tippe(pg, touch, s_, "gut", name)
                        if j == len(k["sack"]) - 1:
                            pg.wait_for_function("() => __wn.frei()")
                            z2 = pg.evaluate(WN_Z)
                            if z2["spul"] != z["spul"] + 1 or z2["fehler"] != z["fehler"] + 1 or z2["z"] != z["z"]:
                                fehler.append(f"{d} {name}: {sz} Sackgasse «{s_}» spult nicht genau einen Schritt zurück ({z} -> {z2})")
                            if "Zurückgespult" not in pg.inner_text("#text"):
                                fehler.append(f"{d} {name}: {sz} Sackgasse ohne freundliche Meldung")
                            bild(pg, f"{i + 1}_nach_sackgasse", name)
                    ok = loese(pg, touch, name, sz, falsch=k.get("zeit", ""))
                    soll = 2
                    if ok and (sterne(pg) != soll or pg.evaluate("id => __wn.MERK.sterne[id]", sz) != soll):
                        fehler.append(f"{d} {name}: {sz} mit Fehlversuchen {sterne(pg)} Sterne statt {soll}")
                    # 2. Durchgang: mit Tipp -> 1 Stern, das bessere Ergebnis bleibt
                    pg.locator("#eNochmal").tap()
                    pg.locator("#bTipp").tap(); pg.locator("#tJa").tap()
                    pg.wait_for_selector("#fx .tippkreis", timeout=3000)
                    bild(pg, f"{i + 1}_tipp", name)
                    c = pg.evaluate("""() => { const c = document.querySelector('#fx .tippkreis'), id = (__wn.next ? __wn.next() : __wn.naechster()), b = document.getElementById('bild').getBoundingClientRect(),
                      st = __wn.stellen().find(x => x.id === id), k = b.width / 800, x = b.left + c.cx.baseVal.value * k, y = b.top + c.cy.baseVal.value * k;
                      return {r: c.r.baseVal.value * k, d: Math.hypot(x - st.x, y - st.y)}; }""")
                    if c["d"] > c["r"] or c["r"] < 50:
                        fehler.append(f"{d} {name}: {sz} Tipp-Kreis zeigt nicht die Gegend der nächsten Stelle ({c})")
                    if loese(pg, touch, name, sz) and (sterne(pg) != 1 or pg.evaluate("id => __wn.MERK.sterne[id]", sz) != soll):
                        fehler.append(f"{d} {name}: {sz} mit Tipp {sterne(pg)} Sterne (soll 1), gemerkt bleibt {soll}")
                    pg.locator("#eNochmal").tap()
                # sauberer Durchgang -> 3 Sterne
                if loese(pg, touch, name, sz, mitte=f"{i + 1}_mitte"):
                    if sterne(pg) != 3:
                        fehler.append(f"{d} {name}: {sz} ohne Fehlversuch {sterne(pg)} Sterne statt 3")
                    pg.wait_for_timeout(700)
                    bild(pg, f"{i + 1}_sterne", name)
                b = pg.locator("#eAlle")
                (b.tap if touch else b.click)()
            bild(pg, "wahl_fertig", name)
            if voll not in pg.inner_text("#chipSterne") or (touch and geh not in pg.inner_text("#chipGeheim")):
                fehler.append(f"{d} {name}: am Schluss {pg.inner_text('#chipSterne')} / {pg.inner_text('#chipGeheim')}")
            # Ton-Schalter und Fortschritt bleiben nach dem Neuladen
            (pg.locator("#bTon").tap if touch else pg.locator("#bTon").click)()
            pg.reload(wait_until="load"); pg.wait_for_function("() => window.__wn")
            if voll not in pg.inner_text("#chipSterne") or pg.locator("#karten .krone").count() != (2 if len(ids) > 5 else 0) or pg.locator("#bTon").get_attribute("aria-pressed") != "true" or pg.locator("#karten .karte.zu").count():
                fehler.append(f"{d} {name}: Fortschritt oder Ton-Schalter nach dem Neuladen weg")
            if pg.evaluate("() => { const b = document.getElementById('mw-back'); return !!b && getComputedStyle(b).display !== 'none'; }"):
                fehler.append(f"{d} {name}: schwebender Zurück-Knopf nicht ausgeblendet (das Spiel hat oben «‹ Spiele»)")
            if pg.evaluate("() => document.documentElement.scrollWidth > innerWidth + 1"):
                fehler.append(f"{d} {name}: Seite breiter als der Bildschirm")
        except Exception as e:
            fehler.append(f"{d} {name}: {e.__class__.__name__}: {str(e)[:300]}")
        ctx.close()

    # quer am Handy: Tipp-Flächen gross genug, nichts läuft über; und ganz ohne Speicher (localStorage wirft)
    ctx = br.new_context(**pw.devices["iPhone 13 landscape"])
    ctx.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('gesperrt'); }});")
    pg = seite(ctx, "Handy quer, ohne Speicher")
    try:
        ids = pg.evaluate("() => __wn.SZ.map(s => s.id)")
        for i, sz in enumerate(ids):
            pg.locator("#karten .karte").nth(i).tap()
            pg.wait_for_function("i => __wn.S.i === i", arg=i)
            if i in (0, 4, 5, 8):
                bild(pg, f"{i + 1}_start", "quer")
            if not (loese2(pg, True, "quer", sz) if sz in WN2 else loese(pg, True, "quer", sz)) or sterne(pg) != 3:
                fehler.append(f"{d} quer / ohne Speicher: {sz} nicht mit 3 Sternen gelöst")
            if pg.evaluate("() => document.documentElement.scrollWidth > innerWidth + 1 || document.documentElement.scrollHeight > innerHeight + 1"):
                fehler.append(f"{d} quer: {sz} läuft über den Bildschirm")
            pg.locator("#eAlle").tap()
        if f"{3 * len(ids)}/{3 * len(ids)}" not in pg.inner_text("#chipSterne"):
            fehler.append(f"{d} ohne Speicher: Fortschritt gilt nicht einmal bis zum Schliessen ({pg.inner_text('#chipSterne')})")
    except Exception as e:
        fehler.append(f"{d} quer: {e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()

    # ---- GS-1.14: liegt ein Tipp genau dort, wo der Finger ist? (Meldung vom echten iPhone: hochkant «etwas darunter») --------
    # Ursache war: hochkant wuchs / schrumpfte die Textleiste mit jeder Meldung, das mittig gesetzte Bild rutschte nach dem Tipp
    # um bis 21 px. Jetzt: feste Leiste, das Bild steht still; die Lage kommt im Augenblick des Tipps von der Fläche #tast.
    def versatz():
        V = lambda pg: pg.evaluate("() => (window.__wn && __wn.V) || 0")
        MITTE = """id => { const st = __wn.S.sz.stellen.find(x => x.id === id && (!x.wenn || x.wenn(__wn.S.zustand))), r = typeof st.r === 'function' ? st.r(__wn.S.zustand, 0) : st.r,
          m = document.getElementById('bild').getScreenCTM(), x = r[0] + r[2] / 2, y = r[1] + r[3] / 2;
          return {bx: x, by: y, x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f}; }"""      # Mitte der Fläche über die Zeichen-Matrix des SVG (nicht über die Rechnung des Spiels)
        RAHMEN = "() => { const r = document.getElementById('rahmen').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"
        LAGEN = [("hoch", "iPhone 13", ""), ("hoch, Seite gerollt", "iPhone 13", "roll"), ("hoch, niedriges Fenster", "iPhone 13", "niedrig"),
                 ("hoch, Ränder (Notch)", "iPhone 13", "rand"), ("hoch, schmal 320", "iPhone 13", "schmal"), ("quer", "iPhone 13 landscape", "")]
        proben = {0: ["sonne", "wolke", "apfel", "hahn", "igel", "maulwurf", "sprenger"], 5: ["mond", "mann", "axt", "boot", "haus", "schnee", "laterne"]}
        alt = False
        for name, geraet, lage in LAGEN:
            ctx = br.new_context(**pw.devices[geraet])
            pg = seite(ctx, "Versatz " + name)
            try:
                if V(pg) < 3:
                    alt = True
                    if not os.environ.get("WN_VERSATZ_ALT"):
                        ctx.close(); break
                pg.goto(url + "&alle=1", wait_until="load"); pg.wait_for_function("() => window.__wn")
                if lage == "niedrig":
                    pg.set_viewport_size({"width": 390, "height": 520})
                if lage == "schmal":
                    pg.set_viewport_size({"width": 320, "height": 568})
                if lage == "rand":
                    pg.add_style_tag(content="body{padding:47px 0 34px!important}")
                # Bildwahl: die Mitte jeder sichtbaren Kachel gehört dieser Kachel (Knöpfe sind echte Elemente der Seite)
                falsch = pg.evaluate("""() => [...document.querySelectorAll('#karten .karte')].filter(k => { const r = k.getBoundingClientRect(); if (r.top < 60 || r.bottom > innerHeight) return false;
                  const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !e || e.closest('.karte') !== k; }).map(k => k.dataset.i)""")
                if falsch:
                    fehler.append(f"{d} Versatz {name}: Bildwahl – Mitte der Kacheln {falsch} trifft nicht die Kachel")
                for lvl, ids_ in proben.items():
                    pg.evaluate("i => __wn.start(i)", lvl); pg.wait_for_timeout(250)
                    if lage == "roll":       # die Seite darf sich nicht rollen lassen: versuchen, dann muss sie bei 0 stehen
                        pg.evaluate("() => { window.scrollTo(0, 30); document.documentElement.scrollTop = 30; document.body.scrollTop = 30; }")
                        pg.mouse.wheel(0, 40); pg.wait_for_timeout(150)
                        sy = pg.evaluate("() => [window.scrollY, document.documentElement.scrollHeight - innerHeight]")
                        if sy[0] > 0.5 or sy[1] > 1:
                            fehler.append(f"{d} Versatz {name}: die Seite lässt sich unter dem Bild rollen (scrollY {sy[0]}, {sy[1]} px zu hoch)")
                    r0 = pg.evaluate(RAHMEN)
                    for sid in ids_:
                        frei(pg)
                        m = pg.evaluate(MITTE, sid)
                        pg.touchscreen.tap(m["x"], m["y"]); pg.wait_for_timeout(40); frei(pg); pg.wait_for_timeout(120)
                        r1 = pg.evaluate(RAHMEN)
                        if max(abs(a_ - b_) for a_, b_ in zip(r0, r1)) > 0.6:
                            fehler.append(f"{d} Versatz {name}: Bild {lvl + 1} rutscht nach dem Tipp auf «{sid}» um {r1[1] - r0[1]:+.1f} px (Kasten {r0} -> {r1})"); r0 = r1
                        if V(pg) >= 3:
                            L = pg.evaluate("() => __wn.S.letzte")
                            if L["id"] != sid or abs(L["x"] - m["bx"]) > 1.5 or abs(L["y"] - m["by"]) > 1.5 or L["diff"] > 1:
                                fehler.append(f"{d} Versatz {name}: Bild {lvl + 1} Tipp auf die Mitte von «{sid}» ({m['bx']:.0f}/{m['by']:.0f}) kommt an bei «{L['id']}» {L['x']:.1f}/{L['y']:.1f} (Messarten ±{L['diff']:.1f} px)")
                    if lvl == 5 and V(pg) >= 3:      # ein Ding in der Leiste: Mitte des Platzes antippen = gewählt, nochmals = abgewählt
                        m = pg.evaluate(MITTE, "eimer"); pg.touchscreen.tap(m["x"], m["y"]); pg.wait_for_timeout(40); frei(pg)
                        b = pg.locator('#tasche .platz[data-d="eimer"]').bounding_box()
                        e_ = pg.evaluate("p => { const e = document.elementFromPoint(p[0], p[1]); return e && e.closest('.platz') ? e.closest('.platz').dataset.d : ''; }", [b["x"] + b["width"] / 2, b["y"] + b["height"] / 2])
                        pg.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2); pg.wait_for_timeout(60)
                        if e_ != "eimer" or pg.evaluate("() => __wn.S.wahl") != "eimer":
                            fehler.append(f"{d} Versatz {name}: Tipp auf die Mitte des Platzes «eimer» wählt ihn nicht")
                        pg.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2); pg.wait_for_timeout(60)
                if V(pg) >= 3 and lage == "":
                    # Tipp-Test: aus; fünfmal auf den Titel = an (Punkt beim Finger, Kreuz im Bild), nochmals fünfmal = aus
                    if pg.locator("#tippdot, #tippinfo, #fx .tippkreuz").count():
                        fehler.append(f"{d} Versatz {name}: der Tipp-Test ist ohne Einschalten sichtbar")
                    tit = pg.locator("#titel2" if "landscape" not in geraet else "#titel")
                    for _ in range(5):
                        tit.tap()
                    m = pg.evaluate(MITTE, "mond"); pg.touchscreen.tap(m["x"], m["y"]); pg.wait_for_timeout(200); frei(pg)
                    p_ = pg.evaluate("""() => { const d = document.getElementById('tippdot'), k = document.querySelector('#fx .tippkreuz'); if (!d || !k) return null;
                      const a = d.getBoundingClientRect(), b = k.getBoundingClientRect(); return [a.left + a.width / 2, a.top + a.height / 2, b.left + b.width / 2, b.top + b.height / 2, document.getElementById('tippinfo').textContent]; }""")
                    if not p_ or max(abs(p_[0] - m["x"]), abs(p_[1] - m["y"]), abs(p_[2] - m["x"]), abs(p_[3] - m["y"])) > 1.5 or "Stelle mond" not in p_[4]:
                        fehler.append(f"{d} Versatz {name}: Tipp-Test zeigt Punkt / Kreuz nicht am Tipp ({p_}, Tipp {m})")
                    bild(pg, "tipptest", "hoch" if "landscape" not in geraet else "quer")
                    for _ in range(5):
                        tit.tap()
                    if pg.locator("#tippdot, #tippinfo, #fx .tippkreuz").count():
                        fehler.append(f"{d} Versatz {name}: der Tipp-Test lässt sich nicht ausschalten")
                    pg.goto(url + "&alle=1&tipp=1", wait_until="load"); pg.wait_for_function("() => window.__wn")
                    if not pg.locator("#tippinfo").count():
                        fehler.append(f"{d} Versatz {name}: «?tipp=1» schaltet den Tipp-Test nicht ein")
            except Exception as e:
                fehler.append(f"{d} Versatz {name}: {e.__class__.__name__}: {str(e)[:300]}")
            ctx.close()
        if alt and not os.environ.get("WN_VERSATZ_ALT"):
            print(f"{d}: diese ZIP hat noch die Fassung vor GS-1.14 – der Versatz-Test (Bild rutscht nach dem Tipp) ist nicht gelaufen", flush=True)
        else:
            print(f"{d}: Versatz geprüft – Tipp auf die Mitte von je 7 Stellen in 2 Bildern, hochkant (auch gerollt, niedrig, mit Rändern, 320 px) und quer; das Bild steht still", flush=True)

    versatz()
    if len(ids) <= 5:
        print(f"{d}: 5 Bilder gelöst (Handy hoch und quer, PC), Sackgassen, Tipps, Geheimnisse geprüft", flush=True)
        return

    # ein Spielstand aus 3.73.0 (nur Bilder 1-5) bleibt erhalten: Sterne, Geheimnisse, Bild 6 ist offen, neue Einträge kommen dazu
    ctx = br.new_context(viewport={"width": 1280, "height": 800})
    ctx.add_init_script("if (!localStorage.getItem('mw-wasnun-v1')) localStorage.setItem('mw-wasnun-v1', " + json.dumps(WN_ALT) + ");")
    pg = seite(ctx, "alter Spielstand")
    try:
        if "11/30" not in pg.inner_text("#chipSterne") or "2/10" not in pg.inner_text("#chipGeheim"):
            fehler.append(f"{d} alter Spielstand: {pg.inner_text('#chipSterne')} / {pg.inner_text('#chipGeheim')} statt 11/30 und 2/10")
        zu = [int(x) for x in pg.evaluate("() => [...document.querySelectorAll('#karten .karte.zu')].map(k => k.dataset.i)")]
        if zu != [6, 7, 8, 9]:
            fehler.append(f"{d} alter Spielstand: gesperrt sind {zu}, erwartet nur die Bilder 8-10 und 7 (Index 6-9)")
        pg.locator("#karten .karte").nth(5).click()
        pg.wait_for_function("() => __wn.S.i === 5")
        loese2(pg, False, "alter Spielstand", "weiher")
        pg.locator("#eAlle").click()
        m = json.loads(pg.evaluate("() => localStorage.getItem('mw-wasnun-v1')"))
        alt = json.loads(WN_ALT)
        if any(m["sterne"].get(k_) != v for k_, v in alt["sterne"].items()) or m["sterne"].get("weiher") != 3 or m["geheim"] != alt["geheim"]:
            fehler.append(f"{d} alter Spielstand: nach einem neuen Bild stimmt der Speicher nicht mehr ({m})")
    except Exception as e:
        fehler.append(f"{d} alter Spielstand: {e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()

    # Zufalls-Lauf: je neues Bild 150 zufällige Tipps (Stellen, Dinge, Kombinationen, daneben) - danach muss es noch lösbar sein
    import random
    ctx = br.new_context(viewport={"width": 1280, "height": 800})
    pg = seite(ctx, "Zufalls-Lauf")
    pg.goto(url + "&alle=1&tempo=40", wait_until="load"); pg.wait_for_function("() => window.__wn")
    try:
        for i, sz in enumerate(WN2, start=len(WN)):
            rnd = random.Random(20261110 + i)
            pg.evaluate("i => __wn.start(i)", i)
            geloest = zurueck = 0
            for n in range(150):
                frei(pg)
                if pg.evaluate("() => __wn.S.fertig"):
                    pg.wait_for_selector("#eNochmal", timeout=8000); pg.locator("#eNochmal").click(); geloest += 1; continue
                st = [x for x in pg.evaluate("() => __wn.stellen()") if x["x"] is not None]
                pl = pg.evaluate("() => __wn.plaetze()")
                w = rnd.random()
                if pl and w < 0.3:
                    x = rnd.choice(pl); pg.mouse.click(x["x"], x["y"])
                elif w < 0.95:
                    x = rnd.choice(st); pg.mouse.click(x["x"], x["y"])
                else:
                    b = pg.locator("#bild").bounding_box(); pg.mouse.click(b["x"] + rnd.random() * b["width"], b["y"] + rnd.random() * b["height"])
                pg.wait_for_timeout(15)
                frei(pg)
                z = pg.evaluate(WN_Z)
                if len([x for x in z["tasche"].split(",") if x]) > 4:
                    fehler.append(f"{d} Zufalls-Lauf: {sz} mehr als 4 Dinge in der Leiste ({z['tasche']})"); break
            zurueck = pg.evaluate("() => __wn.S.spul")
            frei(pg)
            if pg.evaluate("() => __wn.S.fertig"):
                geloest += 1
            elif not loese2(pg, False, "Zufalls-Lauf", sz):
                fehler.append(f"{d} Zufalls-Lauf: {sz} ist nach 150 zufälligen Tipps nicht mehr lösbar ({pg.evaluate(WN_Z)})")
            else:
                geloest += 1
            print(f"{d}: Zufalls-Lauf {sz}: 150 Tipps, {zurueck} Sackgassen, danach lösbar ({geloest}-mal gelöst)", flush=True)
    except Exception as e:
        fehler.append(f"{d} Zufalls-Lauf: {e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()
    print(f"{d}: 10 Bilder gelöst (Handy hoch und quer, PC), Dinge und Kombinationen, Sackgassen, Tipps, Geheimnisse, alter Spielstand geprüft", flush=True)


# ---- Schach (eigene Zusammenstellung, Quelle games/schach/, mit ?test=1 -> window.__schach) ---------------------------------------
SCHACH_KLEIN = """() => [...document.querySelectorAll('button, a.back, select')].filter(e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e);
  return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && !e.closest('#mw-back') && (r.width < 43.9 || r.height < 43.9); })
  .map(e => (e.id || e.textContent.trim().slice(0, 16)) + ' ' + Math.round(e.getBoundingClientRect().width) + '×' + Math.round(e.getBoundingClientRect().height))"""
SCHACH_FEN = {
    "dame": "r1b3k1/5ppp/5n2/8/8/7P/5PP1/3Q2K1 w - - 0 1",                       # Dd1-d7 stellt die Dame ein
    "narr": "rnbqkbnr/pppp1ppp/8/4p3/8/5P2/PPPPP1PP/RNBQKBNR w KQkq - 0 2",     # g2-g4 erlaubt Dh4 matt
    "matt1": "6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1",                               # Ta8 matt
    "umw": "8/P6k/8/8/8/8/7K/8 w - - 0 1",
    "patt": "7k/8/8/6Q1/8/8/8/6K1 w - - 0 1",                                   # Dg6 setzt patt
    "rochade": "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "ep": "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "50": "8/8/4k3/8/8/4K3/8/R7 w - - 99 80",
    "material": "8/8/4k3/8/8/8/4Kp2/8 w - - 0 1",                               # Kxf2: nur noch zwei Könige
    "mitte": "r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P1B2/2PBPN2/PP1N1PPP/R2QK2R w KQ - 0 8",
}


def schach_pruefen(br, pw, base, fehler, bilder):
    d = "schach"
    url = f"{base}/g/{d}/index.html?test=1"
    mess = {}

    def f(name, text):
        fehler.append(f"{d} {name}: {text}")

    def seite(name, geraet=None, ohne_wasm=False, ohne_speicher=False, **kw):
        ctx = br.new_context(**(dict(geraet) if geraet else {}), **kw)
        aussen = []

        def weg(r):
            u = r.request.url
            if not u.startswith(base) and not u.startswith(("data:", "blob:")):
                aussen.append(u[:100]); return r.abort()
            if ohne_wasm and u.split("?")[0].endswith(".wasm"):
                return r.abort()
            return r.continue_()
        ctx.route("**/*", weg)
        if ohne_speicher:
            ctx.add_init_script("for (const k of ['getItem', 'setItem', 'removeItem']) Storage.prototype[k] = () => { throw new Error('SecurityError'); };")
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: None if ohne_wasm and ("wasm" in str(e).lower() or "Failed to fetch" in str(e)) else f(name, f"JavaScript: {str(e)[:300]}"))
        pg.on("console", lambda m: f(name, f"console.error: {m.text[:200]}") if m.type == "error" and not (ohne_wasm and ("wasm" in m.text.lower() or "Failed to load resource" in m.text)) else None)
        pg.__aussen = aussen
        pg.goto(url, wait_until="load", timeout=30000)
        pg.wait_for_function("() => window.__schach && document.querySelectorAll('#brett piece').length >= 32", timeout=10000)
        pg.evaluate("""() => { window.__anim = 0; new MutationObserver(l => { for (const m of l) if (m.target.classList && m.target.classList.contains('anim')) __anim++; })
          .observe(document.getElementById('brett'), {subtree: true, attributes: true, attributeFilter: ['class']}); }""")
        return ctx, pg

    def z(pg):
        return pg.evaluate("() => __schach.zustand()")

    def bild(pg, was):
        if bilder:
            pg.wait_for_timeout(350)
            pg.screenshot(path=os.path.join(bilder, f"schach_{was}.png"))

    def tippe(pg, feld, touch=True):
        p = pg.evaluate("f => __schach.feld(f)", feld)
        (pg.touchscreen.tap if touch else pg.mouse.click)(p["x"], p["y"])
        pg.wait_for_timeout(120)

    def druecke(pg, sel, touch=True):
        (pg.locator(sel).tap if touch else pg.locator(sel).click)()
        pg.wait_for_timeout(120)

    def warte(pg, js, ms=15000, arg=None):
        pg.wait_for_function(js, arg=arg, timeout=ms, polling=40)

    def motor(pg, art="wasm", ms=20000):
        warte(pg, "a => __schach.zustand().bereit && __schach.zustand().motor === a", ms, art)

    def stelle(pg, fen, **o):
        pg.evaluate("([f, o]) => __schach.stelle(f, o)", [SCHACH_FEN.get(fen, fen) if fen else None, o])
        pg.wait_for_timeout(150)

    def klein(pg, name, wo):
        k = pg.evaluate(SCHACH_KLEIN)
        if k:
            f(name, f"{wo}: Knöpfe unter 44 px: {', '.join(k[:6])}")

    def passt(pg, name, wo):
        m = pg.evaluate("""() => { const h = document.getElementById('haupt'), b = document.getElementById('brett').getBoundingClientRect(), k = document.getElementById('mw-back');
          return {breit: document.documentElement.scrollWidth > innerWidth + 1 || h.scrollWidth > h.clientWidth + 1, hoch: h.scrollHeight > h.clientHeight + 1, b: b.width, bh: b.height,
                  aus: b.left < -0.5 || b.right > innerWidth + 0.5 || b.top < 0 || b.bottom > innerHeight + 0.5, zurueck: !!k && getComputedStyle(k).display !== 'none', w: innerWidth}; }""")
        if m["breit"]:
            f(name, f"{wo}: die Seite läuft seitlich über den Bildschirm")
        if m["hoch"]:
            f(name, f"{wo}: nicht alles hat Platz (senkrecht)")
        if m["aus"] or abs(m["b"] - m["bh"]) > 1:
            f(name, f"{wo}: Brett nicht ganz sichtbar oder nicht quadratisch ({m['b']:.0f} × {m['bh']:.0f})")
        if m["zurueck"]:
            f(name, f"{wo}: der schwebende «✕ Zurück» ist sichtbar (das Spiel hat den eigenen Link «‹ Spiele»)")
        return m

    # ---------- 1. iPhone 13 hochkant: der ganze Ablauf ----------
    name = "iPhone"
    ctx, pg = seite(name, pw.devices["iPhone 13"])
    try:
        if not pg.locator("#dNeu").is_visible():
            f(name, "beim ersten Start fehlt das Fenster «Neues Spiel»")
        klein(pg, name, "Start")
        bild(pg, "01_start")
        druecke(pg, "#bSpielen")
        m = passt(pg, name, "Brett")
        if m["b"] < m["w"] - 1.5:
            f(name, f"das Brett ist nicht so breit wie der Bildschirm ({m['b']:.0f} von {m['w']} px)")
        klein(pg, name, "Spiel")
        motor(pg)
        if "Stockfish" not in pg.inner_text("#info"):
            f(name, f"Info-Zeile nennt den Motor nicht: {pg.inner_text('#info')!r}")
        # Antippen zeigt die erlaubten Felder
        tippe(pg, "e2")
        n = pg.locator("#brett square.move-dest").count()
        if n != 2:
            f(name, f"e2 angetippt: {n} Zielfelder statt 2")
        bild(pg, "02_zielpunkte")
        tippe(pg, "g1")
        if pg.locator("#brett square.move-dest").count() != 2 or pg.locator("#brett square.selected").count() != 1:
            f(name, "Springer g1 angetippt: Zielfelder / Auswahl stimmen nicht")
        tippe(pg, "e2")
        t0 = pg.evaluate("() => performance.now()")
        tippe(pg, "e4")
        warte(pg, "() => __schach.zustand().zugNr >= 2 && __schach.zustand().menschDran", 8000)
        mess["erster Zug bis Antwort (Lern-Prüfung + Stufe 3) ms"] = round(pg.evaluate("() => performance.now()") - t0)
        st = z(pg)
        if st["zuege"][0] != "e2e4":
            f(name, f"Zug e2-e4 kam nicht an: {st['zuege']}")
        if pg.locator("#brett square.last-move").count() != 2:
            f(name, "der letzte Zug ist nicht markiert (2 Felder)")
        if pg.evaluate("() => __anim") < 1:
            f(name, "kein Zug wurde bewegt gezeigt (Klasse «anim» kam nie)")
        if mess["erster Zug bis Antwort (Lern-Prüfung + Stufe 3) ms"] > 5000:
            f(name, "die Antwort des Computers dauerte über 5 s")
        if "e4" not in pg.inner_text("#zuege") or "1." not in pg.inner_text("#zuege"):
            f(name, f"Zugliste: {pg.inner_text('#zuege')!r}")
        if not (st["toene"].get("zug", 0) + st["toene"].get("schlag", 0) >= 2) or st["tonLaeuft"] != "running":
            f(name, f"Töne: {st['toene']} / AudioContext {st['tonLaeuft']}")
        bild(pg, "03_letzter_zug")
        # Tipp
        druecke(pg, "#bTipp")
        warte(pg, "() => !!__schach.zustand().tippPfeil", 6000)
        pg.wait_for_timeout(200)
        if pg.locator("#brett svg.cg-shapes g > *").count() < 1 or "Tipp:" not in pg.inner_text("#status"):
            f(name, f"Tipp: kein Pfeil oder kein Text ({pg.inner_text('#status')!r})")
        bild(pg, "04_tipp")
        tp = z(pg)["tippPfeil"]
        tippe(pg, tp[0]); tippe(pg, tp[1])                           # der empfohlene Zug: keine Warnung
        warte(pg, "() => __schach.zustand().zugNr >= 4 && __schach.zustand().menschDran", 8000)
        if pg.locator("#dWarn").is_visible() or z(pg)["tippPfeil"]:
            f(name, "nach dem empfohlenen Zug: Warnung oder Pfeil noch da")
        # Zug zurück (eigener Zug und Antwort)
        druecke(pg, "#bZurueck")
        st = z(pg)
        if st["zugNr"] != 2 or not st["menschDran"]:
            f(name, f"Zug zurück: {st['zugNr']} Halbzüge statt 2")
        # Bedenkzeit: unterste und oberste Stufe
        stelle(pg, "mitte", stufe=1, lern=False)
        for stufe in (1, 8):
            ms = [pg.evaluate("s => __schach.motorZug(s, 1000)", stufe) for _ in range(4 if stufe == 1 else 2)]
            mess[f"Stufe {stufe} Antwort ms (Bedenkzeit 1000)"] = [x["ms"] for x in ms]
            if any(not x["zug"] for x in ms) or max(x["ms"] for x in ms) > 1600:
                f(name, f"Stufe {stufe}: Antwort fehlt oder zu spät: {ms}")
        ms = pg.evaluate("() => __schach.motorZug(8, 300)")
        mess["Stufe 8 Antwort ms (Bedenkzeit 300)"] = ms["ms"]
        if not ms["zug"] or ms["ms"] > 900:
            f(name, f"Stufe 8 mit 0,3 s: {ms}")
        # Lern-Modus: Dame einstellen
        stelle(pg, "dame", stufe=3, lern=True)
        tippe(pg, "d1"); tippe(pg, "d7")
        warte(pg, "() => !document.getElementById('dWarn').hidden", 6000)
        t = pg.inner_text("#warnText")
        if "Dame" not in t or "Trotzdem ziehen?" not in t:
            f(name, f"Lern-Modus: Warnung nennt die Dame nicht: {t!r}")
        klein(pg, name, "Warnung")
        bild(pg, "05_lern_warnung")
        druecke(pg, "#bNochmal")
        pg.wait_for_timeout(300)
        st = z(pg)
        if st["zugNr"] != 0 or st["fen"] != SCHACH_FEN["dame"] or not st["menschDran"] or pg.locator("#dWarn").is_visible():
            f(name, f"«Nochmal überlegen»: Zug nicht zurückgenommen ({st['fen']})")
        tippe(pg, "d1"); tippe(pg, "d7")
        warte(pg, "() => !document.getElementById('dWarn').hidden", 6000)
        druecke(pg, "#bTrotzdem")
        warte(pg, "() => __schach.zustand().zugNr >= 1", 3000)
        if z(pg)["zuege"][0] != "d1d7":
            f(name, "«Trotzdem ziehen»: der Zug gilt nicht")
        # ein guter Zug: keine Warnung (bester Zug des Motors)
        stelle(pg, "dame", stufe=3, lern=True)
        warte(pg, "() => !!__schach.zustand().analyse", 6000)
        a = z(pg)["analyse"]["zug"]
        tippe(pg, a[:2]); tippe(pg, a[2:4])
        warte(pg, "() => __schach.zustand().zugNr >= 1", 6000)
        if pg.locator("#dWarn").is_visible():
            f(name, "Lern-Modus warnt beim besten Zug")
        # Lern-Modus aus: kein Fenster
        stelle(pg, "dame", stufe=3, lern=False)
        tippe(pg, "d1"); tippe(pg, "d7")
        warte(pg, "() => __schach.zustand().zugNr >= 1", 3000)
        if pg.locator("#dWarn").is_visible():
            f(name, "Lern-Modus aus: trotzdem eine Warnung")
        # Narrenmatt: Warnung «matt», dann setzt der Computer (Stufe 8) matt
        stelle(pg, "narr", stufe=8, lern=True)
        tippe(pg, "g2"); tippe(pg, "g4")
        warte(pg, "() => !document.getElementById('dWarn').hidden", 6000)
        if "matt" not in pg.inner_text("#warnText"):
            f(name, f"Lern-Modus: Matt-Warnung fehlt: {pg.inner_text('#warnText')!r}")
        druecke(pg, "#bTrotzdem")
        warte(pg, "() => !!__schach.zustand().ende && !document.getElementById('dEnde').hidden", 8000)
        st = z(pg)
        if st["ende"] != {"art": "matt", "sieger": "b"} or "Schachmatt" not in pg.inner_text("#endeTitel") or "Schachmatt" not in pg.inner_text("#status"):
            f(name, f"Matt durch den Computer: {st['ende']} / {pg.inner_text('#endeTitel')!r}")
        if pg.locator("#brett square.check").count() != 1:
            f(name, "der König im Schach ist nicht hervorgehoben")
        druecke(pg, "#bEndeBrett")
        druecke(pg, "#bZurueck")
        st = z(pg)
        if st["ende"] or st["zugNr"] != 0 or not st["menschDran"]:
            f(name, f"Zug zurück nach dem Matt: {st['zugNr']} Halbzüge, Ende {st['ende']}")
        # selbst matt setzen
        stelle(pg, "matt1", stufe=1, lern=True)
        tippe(pg, "a1"); tippe(pg, "a8")
        warte(pg, "() => !!__schach.zustand().ende && !document.getElementById('dEnde').hidden", 6000)
        st = z(pg)
        if st["ende"] != {"art": "matt", "sieger": "w"} or "gewonnen" not in pg.inner_text("#endeTitel") or st["toene"].get("matt", 0) < 1:
            f(name, f"selbst matt gesetzt: {st['ende']} / {pg.inner_text('#endeTitel')!r}")
        if st["san"][-1] != "Ta8#":
            f(name, f"deutsche Notation: {st['san']}")
        bild(pg, "06_spielende")
        # Patt (mit Warnung, weil klar besser)
        stelle(pg, "patt", stufe=1, lern=True)
        tippe(pg, "g5"); tippe(pg, "g6")
        warte(pg, "() => !document.getElementById('dWarn').hidden", 6000)
        if "patt" not in pg.inner_text("#warnText"):
            f(name, f"Patt-Warnung: {pg.inner_text('#warnText')!r}")
        druecke(pg, "#bTrotzdem")
        warte(pg, "() => !!__schach.zustand().ende && !document.getElementById('dEnde').hidden", 4000)
        if z(pg)["ende"]["art"] != "patt" or "Patt" not in pg.inner_text("#endeTitel"):
            f(name, f"Patt: {z(pg)['ende']} / {pg.inner_text('#endeTitel')!r}")
        # Umwandlung: abbrechen, dann Springer
        stelle(pg, "umw", stufe=1, lern=False)
        tippe(pg, "a7"); tippe(pg, "a8")
        warte(pg, "() => !document.getElementById('dUmw').hidden", 3000)
        if pg.locator("#umw button").count() != 4:
            f(name, "Umwandlung: keine 4 Figuren zur Wahl")
        klein(pg, name, "Umwandlung")
        bild(pg, "07_umwandlung")
        druecke(pg, "#bUmwAbbr")
        pg.wait_for_timeout(250)
        if z(pg)["zugNr"] != 0 or z(pg)["fen"] != SCHACH_FEN["umw"]:
            f(name, "Umwandlung abgebrochen: der Bauer steht nicht wieder auf a7")
        tippe(pg, "a7"); tippe(pg, "a8")
        warte(pg, "() => !document.getElementById('dUmw').hidden", 3000)
        druecke(pg, "#umw button[data-u=n]")
        warte(pg, "() => __schach.zustand().zugNr >= 1", 3000)
        st = z(pg)
        if st["zuege"][0] != "a7a8n" or st["san"][0] != "a8S":
            f(name, f"Umwandlung in einen Springer: {st['zuege']} {st['san']}")
        # zu zweit: kein Computerzug, Rochade, en passant, automatisch drehen
        stelle(pg, "rochade", gegner="mensch", lern=False)
        tippe(pg, "e1"); tippe(pg, "g1")
        pg.wait_for_timeout(900)
        st = z(pg)
        if st["zugNr"] != 1 or st["san"] != ["0-0"] or not st["fen"].startswith("r3k2r/8/8/8/8/8/8/R4RK1 b") or not st["menschDran"]:
            f(name, f"zu zweit, kurze Rochade: {st['san']} {st['fen']}")
        tippe(pg, "e8"); tippe(pg, "c8")
        pg.wait_for_timeout(300)
        if z(pg)["san"] != ["0-0", "0-0-0"]:
            f(name, f"zu zweit, lange Rochade von Schwarz: {z(pg)['san']}")
        if "Weiss ist am Zug" not in pg.inner_text("#status"):
            f(name, f"zu zweit: Status {pg.inner_text('#status')!r}")
        stelle(pg, "ep", gegner="mensch", lern=False)
        tippe(pg, "e5"); tippe(pg, "d6")
        pg.wait_for_timeout(300)
        if not z(pg)["fen"].startswith("4k3/8/3P4/8/8/8/8/4K3 b"):
            f(name, f"en passant: {z(pg)['fen']}")
        pg.evaluate("() => __schach.setze('autodrehen', true)")
        stelle(pg, None, gegner="mensch", lern=False)
        tippe(pg, "e2"); tippe(pg, "e4")
        warte(pg, "() => __schach.zustand().drehung === 'b'", 3000)
        tippe(pg, "e7"); tippe(pg, "e5")
        warte(pg, "() => __schach.zustand().drehung === 'w' && __schach.zustand().zugNr === 2", 3000)
        pg.evaluate("() => __schach.setze('autodrehen', false)")
        druecke(pg, "#bDrehen")
        if z(pg)["drehung"] != "b" or pg.locator("#brett.orientation-black").count() != 1:
            f(name, "«Brett drehen» dreht nicht")
        # Remis: Wiederholung, 50 Züge, zu wenig Material
        stelle(pg, None, gegner="mensch", lern=False)
        for u in ("g1f3", "g8f6", "f3g1", "f6g8") * 2:
            pg.evaluate("u => __schach.ziehe(u)", u)
        if (z(pg)["ende"] or {}).get("art") != "wiederholung":
            f(name, f"dreimal dieselbe Stellung: {z(pg)['ende']}")
        stelle(pg, "50", gegner="mensch", lern=False)
        tippe(pg, "a1"); tippe(pg, "a2")
        pg.wait_for_timeout(250)
        if (z(pg)["ende"] or {}).get("art") != "50zuege":
            f(name, f"50-Züge-Regel: {z(pg)['ende']}")
        stelle(pg, "material", gegner="mensch", lern=False)
        tippe(pg, "e2"); tippe(pg, "f2")
        pg.wait_for_timeout(250)
        if (z(pg)["ende"] or {}).get("art") != "material" or "Remis" not in pg.inner_text("#status"):
            f(name, f"zu wenig Material: {z(pg)['ende']}")
        # Aufgeben (mit Rückfrage), geschlagene Figuren
        stelle(pg, "dame", stufe=1, lern=False)
        tippe(pg, "d1"); tippe(pg, "d7")
        warte(pg, "() => __schach.zustand().zugNr >= 2 && __schach.zustand().menschDran", 6000)
        druecke(pg, "#bAufgeben")
        if not pg.locator("#dFrage").is_visible():
            f(name, "Aufgeben ohne Rückfrage")
        druecke(pg, "#bFrageJa")
        warte(pg, "() => !!__schach.zustand().ende", 3000)
        if z(pg)["ende"] != {"art": "aufgabe", "sieger": "b"}:
            f(name, f"Aufgeben: {z(pg)['ende']}")
        # Einstellungen: Stufe, Bedenkzeit, Töne, Balken; Über
        druecke(pg, "#bEndeBrett") if pg.locator("#dEnde").is_visible() else pg.wait_for_timeout(700)
        if pg.locator("#dEnde").is_visible():
            druecke(pg, "#bEndeBrett")
        druecke(pg, "#bEinst")
        klein(pg, name, "Einstellungen")
        bild(pg, "08_einstellungen")
        pg.select_option("#selStufe2", "5"); pg.select_option("#selZeit", "500")
        druecke(pg, "#schTon"); druecke(pg, "#schBalken")
        druecke(pg, "#bEinstZu")
        st = z(pg)
        if st["einst"]["stufe"] != 5 or st["einst"]["zeit"] != 500 or st["einst"]["ton"] or st["einst"]["balken"] or pg.locator("#balken").is_visible():
            f(name, f"Einstellungen greifen nicht: {st['einst']}")
        passt(pg, name, "ohne Balken")
        druecke(pg, "#bUeber")
        t = pg.inner_text("#dUeber")
        for wort in ("Chessground", "Stockfish", "chess.js", "js-chess-engine", "cburnett", "General Public License"):
            if wort not in t:
                f(name, f"«Über»: {wort} fehlt")
        bild(pg, "09_ueber")
        druecke(pg, "#bUeberZu")
        # Speichern und Weiterspielen
        druecke(pg, "#bNeu"); druecke(pg, "#segFarbe button[data-w=b]"); pg.select_option("#selStufe", "2"); druecke(pg, "#bSpielen")
        warte(pg, "() => __schach.zustand().zugNr >= 1 && __schach.zustand().menschDran", 8000)        # der Computer (Weiss) hat begonnen
        st = z(pg)
        if st["mensch"] != "b" or st["drehung"] != "b" or st["stufe"] != 2:
            f(name, f"mit Schwarz spielen: {st['mensch']} / Brett {st['drehung']} / Stufe {st['stufe']}")
        tippe(pg, "e7"); tippe(pg, "e6")
        warte(pg, "() => __schach.zustand().zugNr >= 3 && __schach.zustand().menschDran", 8000)
        vor = z(pg)
        pg.reload(wait_until="load")
        pg.wait_for_function("() => window.__schach && document.querySelectorAll('#brett piece').length > 0", timeout=10000)
        if not pg.locator("#dWeiter").is_visible():
            f(name, "nach dem Neuladen fehlt «Weiterspielen»")
        bild(pg, "10_weiterspielen")
        druecke(pg, "#bWeiter")
        st = z(pg)
        if st["fen"] != vor["fen"] or st["zuege"] != vor["zuege"] or st["mensch"] != "b" or st["stufe"] != 2 or st["drehung"] != "b":
            f(name, f"Weiterspielen: Stand stimmt nicht ({st['zuege']} statt {vor['zuege']})")
        if st["einst"]["zeit"] != 500 or st["einst"]["ton"] or st["einst"]["balken"] or st["einst"]["stufe"] != 2 or st["einst"]["farbe"] != "b":
            f(name, f"Einstellungen nach dem Neuladen: {st['einst']}")
        motor(pg)
        tippe(pg, "d7"); tippe(pg, "d5")
        warte(pg, "() => __schach.zustand().zugNr >= 5", 8000)
        # Motor hängt: Wechsel auf den Ersatz, die Suche kommt trotzdem
        pg.evaluate("() => { const w = Motor._w, alt = w.postMessage.bind(w); w.postMessage = t => { if (!/^go/.test(t)) alt(t); }; }")
        r = pg.evaluate("() => __schach.motorZug(8, 300)")
        st = z(pg)
        mess["Motor hängt: Antwort vom Ersatz nach ms"] = r["ms"]
        if not r["zug"] or st["motor"] != "js" or "Ersatz" not in pg.inner_text("#info"):
            f(name, f"hängender Motor: kein Wechsel auf den Ersatz ({r}, Motor {st['motor']}, Info {pg.inner_text('#info')!r})")
        # Motor gegen Motor über die Regeln: kein unerlaubter Zug, kein Hängen
        pg.reload(wait_until="load")
        pg.wait_for_function("() => window.__schach", timeout=10000)
        motor(pg)
        for w, s, zeit in ((1, 1, 40), (1, 2, 40), (2, 3, 40), (3, 1, 40)):
            r = pg.evaluate("o => __schach.selbstspiel(o)", {"w": w, "s": s, "zeit": zeit, "max": 400})
            mess[f"Selbstspiel Stufe {w} gegen {s}"] = f"{r.get('halbzuege')} Halbzüge, Ende {(r.get('ende') or {}).get('art', 'Zuggrenze')}, längste Antwort {r.get('maxMs')} ms"
            if r.get("fehler") or r.get("zufall"):
                f(name, f"Selbstspiel {w} gegen {s}: {r}")
        if pg.__aussen:
            f(name, f"Anfragen nach aussen: {sorted(set(pg.__aussen))[:3]}")
    except Exception as e:
        f(name, f"{e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()

    # ---------- 2. WebAssembly gesperrt: der Ersatz-Motor übernimmt von selbst ----------
    name = "ohne wasm"
    ctx, pg = seite(name, pw.devices["iPhone 13"], ohne_wasm=True)
    try:
        druecke(pg, "#bSpielen")
        t0 = pg.evaluate("() => performance.now()")
        motor(pg, "js", 25000)
        mess["Ersatz-Motor bereit nach ms (wasm gesperrt)"] = round(pg.evaluate("() => performance.now()") - t0)
        if "Ersatz-Motor" not in pg.inner_text("#info"):
            f(name, f"Info-Zeile: {pg.inner_text('#info')!r}")
        tippe(pg, "e2"); tippe(pg, "e4")
        warte(pg, "() => __schach.zustand().zugNr >= 2 && __schach.zustand().menschDran", 10000)
        druecke(pg, "#bTipp")
        warte(pg, "() => !!__schach.zustand().tippPfeil", 8000)
        stelle(pg, "dame", stufe=3, lern=True)
        tippe(pg, "d1"); tippe(pg, "d7")
        warte(pg, "() => !document.getElementById('dWarn').hidden", 8000)
        if "Dame" not in pg.inner_text("#warnText"):
            f(name, f"Lern-Modus mit dem Ersatz-Motor: {pg.inner_text('#warnText')!r}")
        druecke(pg, "#bNochmal")
        stelle(pg, "mitte", stufe=8, lern=False)
        ms = [pg.evaluate("s => __schach.motorZug(s, 1000)", s) for s in (1, 4, 8, 8)]
        mess["Ersatz-Motor Antwort ms (Stufen 1, 4, 8, 8)"] = [x["ms"] for x in ms]
        if any(not x["zug"] for x in ms) or max(x["ms"] for x in ms) > 4000:
            f(name, f"Ersatz-Motor: Antwort fehlt oder über 4 s: {ms}")
        r = pg.evaluate("o => __schach.selbstspiel(o)", {"w": 3, "s": 2, "zeit": 40, "max": 160})
        mess["Selbstspiel Ersatz-Motor Stufe 3 gegen 2"] = f"{r.get('halbzuege')} Halbzüge, Ende {(r.get('ende') or {}).get('art', 'Zuggrenze')}, längste Antwort {r.get('maxMs')} ms"
        if r.get("fehler") or r.get("zufall"):
            f(name, f"Selbstspiel: {r}")
        if pg.__aussen:
            f(name, f"Anfragen nach aussen: {sorted(set(pg.__aussen))[:3]}")
    except Exception as e:
        f(name, f"{e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()

    # ---------- 3. ohne Speicher (privates Fenster): spielbar, kein Fehler ----------
    name = "ohne Speicher"
    ctx, pg = seite(name, pw.devices["iPhone 13"], ohne_speicher=True)
    try:
        druecke(pg, "#bSpielen")
        motor(pg)
        tippe(pg, "d2"); tippe(pg, "d4")
        warte(pg, "() => __schach.zustand().zugNr >= 2 && __schach.zustand().menschDran", 8000)
        druecke(pg, "#bLern")
        if z(pg)["einst"]["lern"]:
            f(name, "Lern-Modus lässt sich oben nicht ausschalten")
    except Exception as e:
        f(name, f"{e.__class__.__name__}: {str(e)[:300]}")
    ctx.close()

    # ---------- 4. Handy quer und PC (Maus: klicken und ziehen) ----------
    for name, vp, touch in (("quer", {"width": 844, "height": 390}, True), ("PC", {"width": 1280, "height": 800}, False)):
        ctx, pg = seite(name, None, viewport=vp, is_mobile=touch, has_touch=touch, device_scale_factor=2 if touch else 1)
        try:
            klein(pg, name, "Start")
            druecke(pg, "#bSpielen", touch)
            m = passt(pg, name, "Brett")
            if m["b"] < (280 if touch else 560):
                f(name, f"Brett nur {m['b']:.0f} px")
            klein(pg, name, "Spiel")
            motor(pg)
            if touch:
                tippe(pg, "e2"); tippe(pg, "e4")
            else:                                                     # ziehen mit der Maus
                a, b_ = pg.evaluate("() => [__schach.feld('e2'), __schach.feld('e4')]")
                pg.mouse.move(a["x"], a["y"]); pg.mouse.down(); pg.mouse.move((a["x"] + b_["x"]) / 2, (a["y"] + b_["y"]) / 2, steps=4)
                pg.mouse.move(b_["x"], b_["y"], steps=4); pg.mouse.up()
            warte(pg, "() => __schach.zustand().zugNr >= 2 && __schach.zustand().menschDran", 8000)
            if z(pg)["zuege"][0] != "e2e4":
                f(name, f"Zug kam nicht an: {z(pg)['zuege']}")
            if not touch:
                tippe(pg, "g1", False); tippe(pg, "f3", False)        # klicken – klicken
                warte(pg, "() => __schach.zustand().zugNr >= 4 && __schach.zustand().menschDran", 8000)
            druecke(pg, "#bTipp", touch)
            warte(pg, "() => !!__schach.zustand().tippPfeil", 6000)
            passt(pg, name, "nach Zügen")
            bild(pg, "11_quer" if touch else "12_pc")
            stelle(pg, "dame", stufe=3, lern=True)
            tippe(pg, "d1", touch); tippe(pg, "d7", touch)
            warte(pg, "() => !document.getElementById('dWarn').hidden", 6000)
            klein(pg, name, "Warnung")
            bild(pg, "11_quer_warnung" if touch else "12_pc_warnung")
            druecke(pg, "#bNochmal", touch)
            if pg.__aussen:
                f(name, f"Anfragen nach aussen: {sorted(set(pg.__aussen))[:3]}")
        except Exception as e:
            f(name, f"{e.__class__.__name__}: {str(e)[:300]}")
        ctx.close()
    for k, v in mess.items():
        print(f"  {d}: {k}: {v}", flush=True)
    print(f"{d}: Brett, Zielfelder, Tipp, Lern-Modus, Matt / Patt / Remis, Umwandlung, zu zweit, Speichern, Ersatz-Motor, Selbstspiele geprüft", flush=True)


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


def _renderer_mb():
    """the biggest renderer process of Chromium right now (resident memory in MB; Linux only, else 0)"""
    best = 0
    try:
        for d in os.listdir("/proc"):
            if d.isdigit():
                try:
                    with open(f"/proc/{d}/cmdline", "rb") as fh:
                        if b"--type=renderer" not in fh.read():
                            continue
                    with open(f"/proc/{d}/statm") as fh:
                        best = max(best, int(fh.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") // (1 << 20))
                except (OSError, ValueError, IndexError):
                    pass
    except OSError:
        pass
    return best


def fotaq_pruefen(br, base, fehler, warn, bilder, nur=None, seite="/g/fotaq/index.html", marke="", mess=None):
    """seite / marke / mess: the iPhone test page (werkzeuge/fotaq_iostest.py) runs the same checks on its variants;
    mess (a dict) gets «<device> <language>»: {start_s, mb (peak memory of the page's process), ...}"""
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
            tag = f"FOTAQ{marke} {gname} {L}"
            info = []
            mb = [0]
            try:
                if L == "de" and touch:                 # the language choice upright (as it opens on the phone / iPad)
                    pg.set_viewport_size({"width": min(vp["width"], vp["height"]), "height": max(vp["width"], vp["height"])})
                pg.goto(f"{base}{seite}", wait_until="load", timeout=30000)
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
                    mb[0] = max(mb[0], _renderer_mb())
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
                    mb[0] = max(mb[0], _renderer_mb())
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
                    mb[0] = max(mb[0], _renderer_mb())
                    if mb[0]:
                        info.append(f"Speicher der Seite bis {mb[0]} MB")
                    if mess is not None:
                        mess[f"{gname} {L}"] = {"start_s": dt, "mb": mb[0], "diag": pg.evaluate("() => window.FOTAQ_DIAG ? FOTAQ_DIAG() : null")}
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
            nur = [x for x in os.environ.get("MW_FOTAQ_NUR", "").split(",") if x] or None      # e.g. «handy»: only this device
            fotaq_pruefen(br, base, fehler, warn, bilder, nur=nur)
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
    if bilder:
        fotaq_mw_bilder(ns, app, PW, bilder, fehler, nur_admin="_auswahl")
    if not release:                                  # languages one by one (wish of the owner): DE only, EN later, DE away
        fotaq_sprachen(ns, c, party, warten, srv, tag, ok)
    t0 = time.time()
    code, j = party({"action": "fotaq_install", "langs": ["de", "en"]})
    seen = 0
    while DL["running"] and time.time() - t0 < 1800:
        seen = max(seen, DL["got"]); time.sleep(0.3)
    ok(code == 200 and ns["fotaq_installed"](), f"geladen und entpackt in {time.time() - t0:.0f} s ({DL['msg'] or 'ok'})")
    ok(not os.path.exists(ns["fotaq_dl_dir"]()), "ZIP danach gelöscht")
    gl = ns["games_list"]()
    g = next((x for x in gl if x.get("dir") == "fotaq"), None)
    ok(g is not None and g["input"] == "keys" and g["icon"] == "thumb.svg" and g["start"] == "start.html", "Kachel in der Gruppe «⌨️ Am PC mit Tastatur und Maus» (3.70.2)")
    ok(g is not None and g.get("note") == "Am PC spielen – auf iPad/iPhone stürzt es ab" and len(g.get("notes") or {}) == 5, "Kachel: Hinweis «Am PC spielen …» (5 Sprachen)")
    ok(ns["games_list"](extra=False) == [], "games_list(extra=False): die Sammlung allein (leer)")
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and "Flight of the Amazon Queen" in t and 'src="/spiele/thumb/fotaq"' in t and "⌨️ Am PC mit Tastatur und Maus" in t and "👆" not in t,
       "/spiele zeigt die Kachel mit Bild in der PC-Gruppe")
    ok("⚠️ Am PC spielen – auf iPad/iPhone stürzt es ab" in t and "/g/fotaq/start.html" in t, "/spiele: Hinweis auf der Kachel, Link auf die Warnseite")
    pv = ns["party_view"]("") if "party_view" in ns else {}
    ok(any(x.get("dir") == "fotaq" and x.get("note") and x.get("input") == "keys" for x in (pv.get("games") or [])), "Gästeseite /p/<key>/: Kachel mit Hinweis in der PC-Gruppe")
    ok("g.note ?" in ns["PARTY_PAGE"] and 'L(x)("note", "notes")' in ns["TOOLS_PAGE"] and 'id = "fotaq-note"' in ns["TOOLS_PAGE"], "Gästeseite und Reiter Spielecke zeigen den Hinweis")
    r = c.get("/spiele/thumb/fotaq", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    ok(r.status_code == 200 and r.mimetype == "image/svg+xml", f"Bild der Kachel vom gleichen Ursprung (3.69.2, {r.status_code} {r.mimetype})")
    r = c.get("/party/thumb/fotaq", headers=H)
    ok(r.status_code == 200 and r.mimetype == "image/svg+xml", f"Reiter Spielecke: Bild aus DATA_DIR/fotaq ({r.status_code})")
    # the games port (own origin), like the phones use it
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); wp = sk.getsockname()[1]
    if not ns["GAMESRV"]["port"]:
        CFG["web_port"] = wp - 2
        ns["games_server_start"]()
    gp = ns["GAMESRV"]["port"]
    ok(gp > 0, f"Spiele-Port läuft ({gp})")
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path, hdr=None):
        try:
            with op.open(urllib.request.Request(f"http://127.0.0.1:{gp}{path}", headers=hdr or {}), timeout=60) as x:
                return x.status, dict(x.headers), x.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), b""
    s_, h_, b_ = get("/g/fotaq/")
    ok(s_ == 200 and b'id="mw-back"' in b_ and b"Flight of the Amazon Queen" in b_ and "Trotzdem starten".encode() in b_, "Port: Warnseite (3.70.2) mit «✕ Zurück» von MoveEye")
    s2, _h, b2 = get("/g/fotaq/start.html")
    ok(s2 == 200 and b2 == b_, "Port: start.html = Warnseite")
    s_, h_, b_ = get("/g/fotaq/index.html")
    ok(s_ == 200 and b'id="mw-back"' in b_ and b'id="backPick"' in b_ and b"Trotzdem starten" not in b_, "Port: index.html = Startseite des Pakets (unverändert)")
    fotaq_ios_warnung(gp, ok)
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


FOTAQ_UA = {
    "iPhone": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "iPad": "Mozilla/5.0 (iPad; CPU OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "iPad als Mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}


def fotaq_ios_warnung(gp, ok):
    """3.70.2: iPhone / iPad (also as Mac with touch) see the warning with «Trotzdem starten», which goes on to index.html;
    a PC (Windows, Mac without touch) goes straight on; English browser -> English text"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (Playwright fehlt: Warnseite im Browser nicht geprüft)", flush=True)
        return
    url = f"http://127.0.0.1:{gp}/g/fotaq/"
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name, touch, lang in (("iPhone", True, "de-CH"), ("iPad", True, "de-CH"), ("iPad als Mac", True, "en-GB"), ("Mac", False, "de-CH"), ("Windows", False, "de-CH")):
            ios = name.startswith("i")
            cx = br.new_context(user_agent=FOTAQ_UA[name], has_touch=touch, is_mobile=name == "iPhone", locale=lang,
                                viewport={"width": 390, "height": 844} if name == "iPhone" else {"width": 1024, "height": 1366} if ios else {"width": 1280, "height": 800})
            pg = cx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url, wait_until="domcontentloaded")
            if ios:
                pg.wait_for_selector("#fotaq-warn:not([hidden])", timeout=8000)
                tx = pg.inner_text("#warn")
                want = ("On iPad/iPhone the game crashes after about a minute. Play on the PC." if lang.startswith("en")
                        else "Auf iPad/iPhone stürzt das Spiel nach etwa einer Minute ab. Am PC spielen.")
                ok(want in tx and "/g/fotaq/" in pg.url and "index.html" not in pg.url, f"{name}: Warnung vor dem Start ({tx.strip()[:60]} …)")
                bt = pg.inner_text("#go")
                ok(("Start anyway" if lang.startswith("en") else "Trotzdem starten") in bt, f"{name}: Knopf «{bt.strip()}»")
                pg.click("#go")
                pg.wait_for_url("**/g/fotaq/index.html", timeout=8000)
                ok(pg.url.endswith("/g/fotaq/index.html"), f"{name}: «Trotzdem starten» -> Startseite des Spiels")
            else:
                pg.wait_for_url("**/g/fotaq/index.html", timeout=8000)
                ok(pg.url.endswith("/g/fotaq/index.html") and pg.locator("#fotaq-warn").count() == 0, f"{name}: keine Warnung, gleich zur Startseite")
            ok(not [e for e in errs if "start" in e.lower() or "fotaq" in e.lower()], f"{name}: keine JS-Fehler der Warnseite")
            cx.close()
        br.close()


def _launcher_sprachen(ns):
    """the language buttons the start page shows (served by the games port of MoveEye, real index.html)"""
    from playwright.sync_api import sync_playwright
    ns["games_server_start"]() if not ns["GAMESRV"]["port"] else None
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        pg.goto(f"http://127.0.0.1:{ns['GAMESRV']['port']}/g/fotaq/index.html")
        pg.wait_for_function("() => window.FOTAQ_LANGS !== null && window.FOTAQ_LANGS !== undefined", timeout=10000)
        out = [L for L in ("de", "en") if pg.locator("#btn-" + L).is_visible()]
        br.close()
    return out


def fotaq_sprachen(ns, c, party, warten, srv, tag, ok):
    import socket
    F, DL = ns["FOTAQ_FILES"], ns["FOTAQ_DL"]
    if not ns["GAMESRV"]["port"]:
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); wp = sk.getsockname()[1]
        ns["CFG"]["web_port"] = wp - 2
        ns["games_server_start"]()
    gi = lambda: json.load(open(os.path.join(ns["fotaq_dir"](), "data", "games", "index.json")))
    eng = "/" + tag + "/" + F["engine"]["name"]
    code, j = party({"action": "fotaq_install", "langs": []})
    ok(code == 400 and not DL["running"], f"keine Sprache gewählt: nicht geladen ({code} {j.get('error')})")
    st = party()[1]["fotaq"]
    ok(st["parts"]["de"]["size"] == F["de"]["size"] and not st["engine"], "Zustand nennt die Grösse jeder Sprache")
    party({"action": "fotaq_install", "langs": ["de"]}); warten()
    n0 = sum(1 for h in srv.hits if h[0] == eng)
    st = party()[1]["fotaq"]
    ok(ns["fotaq_installed"]() and st["langs"] == ["de"] and not os.path.exists(os.path.join(ns["fotaq_dir"](), "data", "games", "en")),
       f"nur Deutsch installiert ({st['langs']}, {DL['msg'] or 'ok'})")
    ok(gi() == {"de": {}}, f"data/games/index.json nur de ({gi()})")
    ok(_launcher_sprachen(ns) == ["de"], "Startseite bietet nur Deutsch an")
    ok(ns["fotaq_need"](["de", "en"])[1] == F["en"]["size"], "Englisch dazu: nur die Englisch-ZIP (Engine schon da)")
    party({"action": "fotaq_install", "langs": ["en"]}); warten()
    st = party()[1]["fotaq"]
    ok(st["langs"] == ["de", "en"] and sum(1 for h in srv.hits if h[0] == eng) == n0, f"Englisch später dazu, Engine nicht nochmals geladen ({st['langs']})")
    ok(_launcher_sprachen(ns) == ["de", "en"], "Startseite bietet beide Sprachen an")
    code, j = party({"action": "fotaq_remove", "lang": "de"})
    st = party()[1]["fotaq"]
    ok(code == 200 and st["langs"] == ["en"] and not os.path.exists(os.path.join(ns["fotaq_dir"](), "data", "games", "de")) and gi() == {"en": {}},
       f"Deutsch entfernt, Englisch bleibt ({st['langs']})")
    ok(_launcher_sprachen(ns) == ["en"], "Startseite bietet nur Englisch an")
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    ok("Flight of the Amazon Queen" in r.get_data(as_text=True), "Kachel bleibt mit einer Sprache")
    code, j = party({"action": "fotaq_remove", "lang": "en"})
    ok(code == 200 and not ns["fotaq_installed"]() and not os.path.exists(ns["fotaq_dir"]()), "letzte Sprache entfernt: alles weg, keine Kachel")


def fotaq_mw_bilder(ns, app, PW, bilder, fehler, nur_admin=""):
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
                if nur_admin:
                    pass
                elif not tile.count():
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
                    pg.screenshot(path=os.path.join(bilder, f"fotaq_admin{nur_admin}_{name}.png"))
                    if nur_admin and fb.locator("#fotaq-l-en").count():          # the size follows the choice
                        b0 = fb.locator("#fotaq-install").inner_text(); fb.locator("#fotaq-l-en").click(); pg.wait_for_timeout(200)
                        b1 = fb.locator("#fotaq-install").inner_text(); fb.locator("#fotaq-l-de").click(); pg.wait_for_timeout(200)
                        dis = fb.locator("#fotaq-install").is_disabled(); fb.locator("#fotaq-l-de").click(); fb.locator("#fotaq-l-en").click()
                        if b0 == b1 or not dis:
                            fehler.append(f"FOTAQ MoveEye {name}: Grösse folgt der Sprachwahl nicht ({b0} / {b1}, ohne Sprache gesperrt: {dis})")
                        else:
                            print(f"  ✓ {name}: Knopf «{b0}» → nur Deutsch «{b1}», ohne Sprache gesperrt", flush=True)
                for e in errs:
                    fehler.append(f"FOTAQ MoveEye {name}: JavaScript: {e}")
                ctx.close()
            br.close()
    finally:
        srv.shutdown()


_PNG_1PX = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def kacheln_https(datei, fehler, ohne_browser=False):
    """3.69.2: the tile pictures (admin tab, /spiele, /p/<key>/) come from the same origin - over https no http:// picture
    (mixed content: Safari blocks it, the tile stays empty); the thumb routes give only thumb.svg / thumb.png of listed games"""
    import base64
    import ssl
    import subprocess
    import socket
    from werkzeug.serving import make_server
    home = tempfile.mkdtemp(prefix="mw_kachel_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_kachel_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    ns["lan_guest_ip"] = lambda ip, fwd="": not fwd          # test: 127.0.0.1 = own Wi-Fi, with X-Forwarded-For = outside

    def ok(c, what):
        print(("  ✓ " if c else "  ✗ ") + what, flush=True)
        if not c:
            fehler.append("Kacheln https: " + what)
    gd = os.path.join(home, "games")
    spiele = [("t-svg", "thumb.svg", b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#2a7"/></svg>'),
              ("t-png", "thumb.png", base64.b64decode(_PNG_1PX)), ("t-emoji", "🎲", None), ("t-html", "index.html", None)]
    for d, ic, data in spiele:
        os.makedirs(os.path.join(gd, d), exist_ok=True)
        open(os.path.join(gd, d, "index.html"), "w").write("<!doctype html><title>x</title>")
        if data:
            open(os.path.join(gd, d, ic), "wb").write(data)
    json.dump({"version": "GS-T", "games": [{"dir": d, "name": "Spiel " + d, "icon": ic, "input": "touch", "start": "index.html"} for d, ic, _ in spiele]},
              open(os.path.join(gd, "games.json"), "w"))
    ns["GAMESRV"]["port"] = 5999                    # the games port «runs»: before 3.69.2 the pictures pointed to http://<host>:5999
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    ns["party_open"](2)
    key = ns["PARTY"]["key"]
    c = app.test_client(use_cookies=False)
    H = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode()}
    B = "https://pi.local:5001"
    img_http = re.compile(r'<img[^>]+src="http://|\.src\s*=\s*"http://|<img src="\$\{[^}]*\}"[^>]*>|im\.src = "/games/')
    for B_ in (B, "http://pi.local:5000"):
        for path, h in (("/spiele", {}), ("/p/%s/" % key, {}), ("/party", H), ("/tools", H)):
            r = c.get(path, base_url=B_, headers=h)
            html = r.get_data(as_text=True)
            bad = [m.group(0)[:80] for m in img_http.finditer(html) if "/thumb/" not in m.group(0)]
            ok(r.status_code == 200 and not bad, f"{B_.split(':')[0]} {path}: keine http://-Bilder ({r.status_code} {bad[:2]})")
    html = c.get("/spiele", base_url=B).get_data(as_text=True)
    ok('src="/spiele/thumb/t-svg"' in html and 'src="/spiele/thumb/t-png"' in html and "http://pi.local:5999/g/t-svg/" in html,
       "/spiele: Bilder vom gleichen Ursprung, das Spiel selbst weiter auf dem Spiele-Port")
    for path, h, want, ct in (("/party/thumb/t-svg", H, 200, "image/svg+xml"), ("/party/thumb/t-png", H, 200, "image/png"),
                              ("/party/thumb/t-emoji", H, 404, ""), ("/party/thumb/t-html", H, 404, ""), ("/party/thumb/nix", H, 404, ""),
                              ("/party/thumb/t-svg", {}, 401, ""), ("/spiele/thumb/t-svg", {}, 200, "image/svg+xml"),
                              ("/spiele/thumb/t-svg", {"X-Forwarded-For": "203.0.113.9"}, 404, ""),
                              ("/p/%s/thumb/t-png" % key, {}, 200, "image/png"), ("/p/falsch/thumb/t-png", {}, 404, "")):
        r = c.get(path, base_url=B, headers=h)
        good = r.status_code == want and (not ct or (r.mimetype == ct and r.headers.get("X-Content-Type-Options") == "nosniff"
                                                      and "sandbox" in r.headers.get("Content-Security-Policy", "")))
        ok(good, f"{path} {'(angemeldet)' if h is H else '(außen)' if h else ''}: {r.status_code} {r.mimetype}")
    if ohne_browser:
        return
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="mw_kachel_tls_")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", os.path.join(tmp, "k.pem"), "-out", os.path.join(tmp, "c.pem"),
                    "-days", "1", "-subj", "/CN=localhost"], check=True, capture_output=True)
    ctx_ = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx_.load_cert_chain(os.path.join(tmp, "c.pem"), os.path.join(tmp, "k.pem"))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    srv = make_server("127.0.0.1", port, app, threaded=True, ssl_context=ctx_)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"https://localhost:{port}"
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for name, vp, mob in (("handy", {"width": 390, "height": 2400}, True), ("pc", {"width": 1280, "height": 2400}, False)):
                bctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, ignore_https_errors=True,
                                      http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                bctx.add_init_script("try{localStorage.setItem('mw-lang','de')}catch(e){}")
                for path in ("/spiele", "/p/%s/" % key, "/party"):
                    pg = bctx.new_page(); http_imgs = []
                    pg.on("request", lambda rq, l=http_imgs: l.append(rq.url) if rq.resource_type == "image" and rq.url.startswith("http://") else None)
                    pg.goto(base + path); pg.wait_for_timeout(1500)
                    if path.startswith("/p/") and pg.locator("#nm").is_visible():          # the game evening: join first
                        pg.fill("#nm", "Test-" + name); pg.click("#go"); pg.wait_for_timeout(2500)
                    pg.evaluate("document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; })")
                    pg.wait_for_timeout(800)
                    st = pg.evaluate("[...document.querySelectorAll('a.c img')].map(i => [i.getAttribute('src'), i.complete && i.naturalWidth > 0])")
                    srcs = {s for s, _ in st}
                    want = {s for s in srcs if s and ("t-svg" in s or "t-png" in s)}
                    ok(len(want) == 2 and all(g for s, g in st if s in want) and not http_imgs,
                       f"{name} {path.split('/')[1] or path}: {len(want)} Kachel-Bilder geladen über https, keine http://-Bilder ({st} {http_imgs[:2]})")
                    pg.close()
                bctx.close()
            br.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Test der Spielesammlung (Paket und Browser)")
    ap.add_argument("--kacheln-https", action="store_true", help="3.69.2: Kachel-Bilder über https vom gleichen Ursprung (gebaute Datei, Browser)")
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
    if a.kacheln_https:
        kacheln_https(a.datei or _neueste_datei(), fehler, a.ohne_browser)
        for f in fehler:
            print("FEHLER:", f)
        print("Kacheln-https-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
        sys.exit(1 if fehler else 0)
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
    if os.path.isfile(os.path.join(REPO, "games", "wasnun", "kachel.json")) and not any(g.get("dir") == "wasnun" for g in gj["games"]):
        warn.append("«Was nun?» liegt in games/wasnun/, ist aber noch nicht in dieser ZIP (python3 werkzeuge/spiel_einbauen.py games/wasnun)")
    if os.path.isfile(os.path.join(REPO, "games", "schach", "kachel.json")) and not any(g.get("dir") == "schach" for g in gj["games"]):
        warn.append("Das neue Schach liegt in games/schach/, ist aber noch nicht in dieser ZIP (python3 werkzeuge/spiel_einbauen.py games/schach --hinter adarkroom --entfernen chess)")
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
                if any(g["dir"] == "wasnun" for g in spiele):
                    wasnun_pruefen(br, pw, base, fehler, a.bilder)
                if any(g["dir"] == "schach" for g in spiele):
                    schach_pruefen(br, pw, base, fehler, a.bilder)
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
