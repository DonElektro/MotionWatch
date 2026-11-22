#!/usr/bin/env python3
"""MoveEye: Test «⛶ Vollbild» der Karten auf /karte (Teil 639zzq, Haken in 639zzzzzt; Besitzer 22.11.2026).

  python3 werkzeuge/karte_vollbild_test.py [--web karte-web-2.zip] [--bilder ORDNER] [--vorher] [--datei X.py]

Beide Karten (Schweiz mit den Test-Dateien von karten_test.py, Bergtal mit dem erfundenen Tal von bergkarte_test.py) in
einem MoveEye (eigener Prozess, Laden über HTTP), Browser 390 × 844 (Handy, DPR 2) und 1366 × 768 (PC):
  * Knopf «⛶» in der Knopf-Spalte oben rechts, unter Zoom / Kompass, Titel «Vollbild»; Texte in 5 Sprachen
  * antippen = Fullscreen API auf dem Kartenkasten (document.fullscreenElement), Karte = Bildschirm, «✕» «Vollbild beenden»
  * Esc und «✕» = zurück, Karte wieder so gross wie vorher
  * ohne Element-Vollbild (wie iPhone Safari): fest über der Seite (Klasse kq-fsp), Karte = Bildschirm, Drehen (quer) passt
    sich an, Esc / «✕» zurück
  * Texte des Knopfs im Browser in 5 Sprachen; keine JS-Fehler, keine Anfrage nach aussen
--vorher: nur Bildschirmfotos (für ein Programm ohne den Knopf).
"""
import argparse
import base64
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import karten_test as KA                                 # noqa: E402  (Test-Karte Schweiz)
import bergkarte_test as BG                              # noqa: E402  (erfundenes Tal)
FEHLER = []
OHNE_FS = ("Object.defineProperty(Document.prototype,'fullscreenEnabled',{get:()=>false});"
           "Object.defineProperty(Document.prototype,'webkitFullscreenEnabled',{get:()=>false});")


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def texte():
    src = open(os.path.join(ROOT, "quelle", "639zzq_offline_karten.py"), encoding="utf-8").read()
    m = re.search(r"const FT = \{(.*?)\};", src, re.S)
    ok(bool(m) and all(f"{L}: [" in m.group(1) for L in ("de", "fr", "it", "rm", "en")) and "ß" not in m.group(1), "Texte «Vollbild» / «Vollbild beenden» in de / fr / it / rm / en (KQ_PAGE)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei")
    ap.add_argument("--web")
    ap.add_argument("--bilder")
    ap.add_argument("--vorher", action="store_true")
    ap.add_argument("--nur-sprache", action="store_true", help="nur die Texte im Browser (schnell)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or KA.neueste_datei())
    print(f"Karte Vollbild · {os.path.basename(datei)}", flush=True)
    if not a.vorher:
        texte()
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    tmp = tempfile.mkdtemp(prefix="mw_kvoll_")
    p = None
    try:
        web = BG.web_zip(a.web, tmp)
        P, rel, pins, _tiles = KA.dateien_bauen(tmp, web)
        exp = BG.erfundenes_tal(os.path.join(tmp, "exp"))
        _zp, data, unp = BG.paket_bauen(exp, web, os.path.join(tmp, "out"))
        srv = Srv()
        for f in pins.values():
            srv.files["/" + f["tag"] + "/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
        srv.files["/%s/%s" % (BG.BP.TAG, BG.BP.NAME)] = data
        t1, t2 = os.path.join(tmp, "p1"), os.path.join(tmp, "run")
        os.makedirs(t1); os.makedirs(t2)
        d2 = BG.gepatcht(KA.gepatcht(datei, t1, pins, srv.url), t2, data, unp, srv.url)
        shutil.rmtree(t1, ignore_errors=True)
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
        PW = "Voll-" + os.urandom(4).hex()
        p, _cfg = KA.starte(d2, t2, port, PW)
        base = f"http://127.0.0.1:{port}"
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def req(path, d=None):
            hd = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode(), "Content-Type": "application/json", "Origin": base}
            r = urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None, headers=hd)
            try:
                with op.open(r, timeout=120) as x:
                    return x.status, json.loads(x.read() or b"{}")
            except urllib.error.HTTPError as e:
                return e.code, {}
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(t2, "log.txt")).read()[-3000:])
            try:
                if req("/api/karte")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        for api in ("/api/karte", "/api/karte/berg"):
            req(api, {"action": "install"})
            for _i in range(240):
                if req(api)[1].get("on"):
                    break
                time.sleep(0.5)
            ok(req(api)[1].get("on"), f"{api}: Test-Karte über HTTP geladen und installiert")
        time.sleep(2.5)
        bilder = a.bilder
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []
            groesse = ("() => { const r = document.getElementById('kq-map').getBoundingClientRect(), c = KQMAP.getCanvas();"
                       " return [r.width, r.height, c.clientWidth, c.clientHeight, innerWidth, innerHeight]; }")

            def voll(g):
                return abs(g[0] - g[4]) <= 1 and abs(g[1] - g[5]) <= 1 and abs(g[2] - g[4]) <= 2 and abs(g[3] - g[5]) <= 2
            for name, mob, vp in ((("390", True, {"width": 390, "height": 844}), ("pc", False, {"width": 1366, "height": 768})) if not a.nur_sprache else ()):
                for echt_fs in ((True, False) if not a.vorher else (True,)):
                    ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                         http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                    ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','light');localStorage.setItem('mw-sheet','page');"
                                        "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}"
                                        + ("" if echt_fs else OHNE_FS))
                    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                    pg = ctx.new_page(); errs = []
                    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                    tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                    art = "Fullscreen API" if echt_fs else "ohne Element-Vollbild (iPhone)"
                    for welt in ("ch", "berg"):
                        wo = f"{name} {welt} ({art})"
                        pg.set_viewport_size(vp)
                        pg.goto(base + ("/karte?welt=ch&lat=%s&lon=%s&z=13" % KA.SEON if welt == "ch" else "/karte?welt=berg"))
                        pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && window.BK && BK.mode === '%s'" % welt, timeout=90000)
                        pg.wait_for_timeout(1500)
                        pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'center'})")
                        pg.wait_for_timeout(300)
                        if bilder and echt_fs:
                            pg.screenshot(path=os.path.join(bilder, f"{'vorher' if a.vorher else 'nachher'}_{welt}_{name}.png"))
                        if a.vorher:
                            continue
                        lage = pg.evaluate("""() => { const b = document.getElementById('kq-full'); if (!b) return null;
                            const g = b.closest('.maplibregl-ctrl-group'), col = g.parentElement, gs = [...col.children], i = gs.indexOf(g), nav = gs[i - 1];
                            return {col: col.classList.contains('maplibregl-ctrl-top-right'), nav: !!(nav && nav.querySelector('.maplibregl-ctrl-zoom-in')),
                                    compass: !!(nav && nav.querySelector('.maplibregl-ctrl-compass')), txt: b.textContent, title: b.title, aria: b.getAttribute('aria-label'),
                                    w: b.getBoundingClientRect().width, nw: nav ? nav.querySelector('button').getBoundingClientRect().width : 0}; }""")
                        ok(bool(lage) and lage["col"] and lage["nav"] and lage["txt"] == "⛶" and lage["title"] == "Vollbild" and lage["aria"] == "Vollbild"
                           and abs(lage["w"] - lage["nw"]) < 1 and (lage["compass"] or welt == "ch"),
                           f"{wo}: Knopf «⛶» «Vollbild» oben rechts unter Zoom{' / Kompass' if welt == 'berg' else ''}, gleich breit ({lage})")
                        g0 = pg.evaluate(groesse)
                        tap("#kq-full")
                        pg.wait_for_function("() => document.getElementById('kq-map').classList.contains('kq-fs')", timeout=10000)
                        pg.wait_for_timeout(900)
                        st = pg.evaluate("() => ({fs: document.fullscreenElement && document.fullscreenElement.id, fsp: document.getElementById('kq-map').classList.contains('kq-fsp'),"
                                         " txt: document.getElementById('kq-full').textContent, t: document.getElementById('kq-full').title})")
                        g1 = pg.evaluate(groesse)
                        ok((st["fs"] == "kq-map" and not st["fsp"]) if echt_fs else (not st["fs"] and st["fsp"]),
                           f"{wo}: Vollbild an ({'document.fullscreenElement = #kq-map' if echt_fs else 'Klasse kq-fsp, fest über der Seite'}: {st})")
                        ok(voll(g1) and st["txt"] == "✕" and st["t"] == "Vollbild beenden", f"{wo}: Karte = Bildschirm {g1[:4]} bei {g1[4:]}, Knopf «✕» «Vollbild beenden»")
                        if bilder and mob == (not echt_fs) or bilder and not mob and echt_fs:
                            pg.screenshot(path=os.path.join(bilder, f"vollbild_{welt}_{name}.png"))
                        if mob and not echt_fs:                                   # turn the phone (landscape) in full screen
                            pg.set_viewport_size({"width": vp["height"], "height": vp["width"]}); pg.wait_for_timeout(900)
                            g2 = pg.evaluate(groesse)
                            ok(voll(g2), f"{wo}: gedreht (quer) wieder Bildschirm {g2[:4]} bei {g2[4:]}")
                            if bilder and welt == "berg":
                                pg.screenshot(path=os.path.join(bilder, f"vollbild_{welt}_{name}_quer.png"))
                            pg.set_viewport_size(vp); pg.wait_for_timeout(600)
                        pg.keyboard.press("Escape")
                        try:
                            pg.wait_for_function("() => !document.fullscreenElement && !document.getElementById('kq-map').classList.contains('kq-fs')", timeout=8000)
                        except Exception:
                            pass
                        pg.wait_for_timeout(700)
                        g3 = pg.evaluate(groesse)
                        st = pg.evaluate("() => ({fs: !!document.fullscreenElement, c: document.getElementById('kq-map').className, h: document.documentElement.className.includes('kq-fs-on'), txt: document.getElementById('kq-full').textContent})")
                        ok(not st["fs"] and "kq-fs" not in st["c"] and not st["h"] and st["txt"] == "⛶" and abs(g3[1] - g0[1]) <= 1 and abs(g3[3] - g0[3]) <= 2,
                           f"{wo}: Esc = zurück, Karte wie vorher ({g0[1]:.0f} → {g3[1]:.0f} px hoch)")
                        tap("#kq-full")
                        pg.wait_for_function("() => document.getElementById('kq-map').classList.contains('kq-fs')", timeout=10000); pg.wait_for_timeout(500)
                        tap("#kq-full")
                        pg.wait_for_function("() => !document.fullscreenElement && !document.getElementById('kq-map').classList.contains('kq-fs')", timeout=10000)
                        pg.wait_for_timeout(500)
                        g4 = pg.evaluate(groesse)
                        ok(abs(g4[1] - g0[1]) <= 1, f"{wo}: «✕» = zurück ({g4[1]:.0f} px hoch)")
                    ok(not errs, f"{name} ({art}): keine JS-Fehler" + (f" ({errs[:2]})" if errs else ""))
                    ctx.close()
            if not a.vorher:                                             # the texts of the button in all 5 languages (kqT of the page)
                ctx = br.new_context(viewport={"width": 390, "height": 844}, http_credentials={"username": "admin", "password": PW})
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                pg = ctx.new_page(); pg.goto(base + "/karte?welt=berg")
                pg.wait_for_function("() => window.KQMAP && document.getElementById('kq-full')", timeout=90000)
                sp = pg.evaluate("""() => { const o = LANG, r = {now: document.getElementById('kq-full').title === kqFullT('Full screen')};
                    for (const l of ['de', 'fr', 'it', 'rm', 'en']) { LANG = l; r[l] = [kqFullT('Full screen'), kqFullT('Exit full screen')]; } LANG = o; return r; }""")
                ok(sp["now"] and sp["de"] == ["Vollbild", "Vollbild beenden"] and sp["fr"] == ["Plein écran", "Quitter le plein écran"]
                   and sp["it"] == ["Schermo intero", "Esci dallo schermo intero"] and sp["rm"] == ["Maletg entir", "Terminar il maletg entir"]
                   and sp["en"] == ["Full screen", "Exit full screen"], f"Texte im Browser in 5 Sprachen ({sp})")
                ctx.close()
            ok(not aussen, "keine Anfrage nach aussen" + (f" ({aussen[:3]})" if aussen else ""))
            br.close()
    finally:
        if p:
            p.terminate()
            try:
                p.wait(20)
            except Exception:
                p.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    FEHLER.extend(BG.FEHLER + KA.FEHLER)
    print("\n%s: %d Fehler" % ("OK" if not FEHLER else "FEHLER", len(FEHLER)), flush=True)
    for f in FEHLER:
        print("  ✗", f)
    sys.exit(1 if FEHLER and not a.vorher else 0)


if __name__ == "__main__":
    main()
