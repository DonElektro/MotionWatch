#!/usr/bin/env python3
"""MoveEye: Test «2D / 3D» auf der Schweizer Karte (Teil 639zzzzzz, Idee 42 des Besitzers, 28.11.2026).

  python3 werkzeuge/karte_3d_test.py [--datei X.py] [--web karte-web-2.zip] [--bilder ORDNER] [--ohne-browser]
  python3 werkzeuge/karte_3d_test.py --echt hoehe-ch-1.bin [--bilder ORDNER]   # nur lokal: echte Höhendaten (Zeit pro Kachel, Bilder Alpen)

A) im Prozess, mit einer kleinen erfundenen Höhendatei (Gitter 25 m wie DHM25, «Alpen» um Seon, eine Ecke ohne Daten):
   * Kodierung terrarium hin und zurück (bekannte Höhen, auf 0.1 m), 0 m = 128 / 0 / 0, PNG lesbar
   * Kachel = die Höhen der Datei an den Pixeln (bilinear, auf 1 m), ausserhalb der Datei und in der leeren Ecke 0 m
   * Zwischenspeicher: zweiter Abruf aus dem Speicher, Grenze hält (die am längsten nicht gebrauchten gehen zuerst),
     alte Schlüssel weg, Entfernen der Höhendaten löscht ihn mit
   * Zustand für die Seite: ohne Höhendaten aus, auf dem Host aus (kein Schalter), Texte in 5 Sprachen, Selbsttest
B) MoveEye als eigener Prozess (Test-Karte von karten_test.py, Höhendaten über HTTP), Browser 390 × 844 (DPR 2) und
   1366 × 768: Schalter «2D | 3D» unter «Standard | Topo»; ohne Höhen der Hinweis «Höhendaten Schweiz laden» mit Link;
   mit Höhendaten (Topo-Relief weggenommen) Gelände aus /karte/dem, geneigt, Relief, 2D zurück; mit dem Topo-Relief das
   Gelände aus «relief», gemerkt über Neuladen, Wechsel Standard / Topo behält 3D; im Vollbild; keine JS-Fehler, keine
   Anfrage nach aussen; Rechte (ohne Anmeldung 401, falscher Schlüssel / Zoom 404).
"""
import argparse
import base64
import glob
import hashlib
import json
import math
import os
import re
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "karten"))
FEHLER = []
# erfundene «Alpen» um Seon (dort liegen die Test-Kacheln der Karte): Ebene 450 m, drei Gipfel, ein Grat
E0, N0, COLS, ROWS, GRID = 2642000.0, 1234000.0, 960, 800, 25.0
GIPFEL = ((2655000.0, 1245000.0, 2900.0, 1800.0), (2650500.0, 1241000.0, 2300.0, 1500.0), (2659000.0, 1249000.0, 2000.0, 1300.0))
FAKE_KQ = ("(() => { let v; Object.defineProperty(window, 'KQ', {configurable: true, get: () => v,"
           " set: x => { if (x && x.layers) { delete x.layers.relief; delete x.layers.topo; x.topo = false; } v = x; }}); })();")   # wie ohne Topo-Karte (nur karten-1)


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def hoehe_fn(E, N):
    import numpy as np
    h = 450.0 + 0.004 * (N - N0)
    for e, n, a, s in GIPFEL:
        h = h + a * np.exp(-(((E - e) / s) ** 2 + ((N - n) / s) ** 2))
    return h + 300.0 * np.exp(-(((E - 2653000.0) * 0.8 + (N - 1243000.0) * 0.6) / 600.0) ** 2) * np.exp(-((N - 1243000.0) / 4000.0) ** 2)


def hoehe_datei(path):
    import numpy as np
    import hoehe
    E, N = np.meshgrid(E0 + np.arange(COLS) * GRID, N0 + np.arange(ROWS) * GRID)
    h = hoehe_fn(E, N).astype("float32")
    h[:80, :100] = float("nan")                              # die Ecke im Südwesten ohne Daten (wie ausserhalb der Grenze)
    return hoehe.schreibe(path, h, GRID, E0, N0, 0.5, "Test")


def neueste_datei():
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return c[-1]


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_karte3d_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    return ns


def einsetzen(ns, path):
    """the height file as if loaded (marker .ok with the pinned checksum)"""
    d = os.path.dirname(ns["kh_path"]())
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(path, ns["kh_path"]())
    ns["KH_FILE"].update(name="hoehe-ch-1.bin", size=os.path.getsize(path), sha256=hashlib.sha256(open(path, "rb").read()).hexdigest())
    json.dump({"tag": ns["KH_TAG"], "sha256": ns["KH_FILE"]["sha256"]}, open(ns["kh_path"]() + ".ok", "w"))
    ns["kh_close"]()


def kachel_von(lat, lon, z):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)


def png_hoehen(ns, b):
    import cv2
    import numpy as np
    a = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
    return ns["kd_decode"](a[..., ::-1]) if a is not None else None


def pixel_lagen(z, x, y, n=256):
    import numpy as np
    p = (np.arange(n) + 0.5) / n
    lon = (x + p) / 2 ** z * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (y + p) / 2 ** z))))
    return np.meshgrid(lon, lat)


# ---- A --------------------------------------------------------------------------------------------------------------------------------
def teil_a(datei):
    import numpy as np
    print("A) im Prozess (kleine Höhendatei)", flush=True)
    home = tempfile.mkdtemp(prefix="mw_k3d_home_")
    tmp = tempfile.mkdtemp(prefix="mw_k3d_a_")
    try:
        ns = lade(datei, home)
        ok(str(ns["karte3d_selftest"]()).startswith("3D map"), "Selbsttest 639zzzzzz")
        enc, dec = ns["kd_encode"], ns["kd_decode"]
        h = np.array([-430.25, 0.0, 0.04, 372.1, 1234.5678, 4478.0, 4634.0, 8848.86, -11034.0])
        ok(float(np.abs(dec(enc(h)) - h).max()) < 0.1, "terrarium: bekannte Höhen hin und zurück auf 0.1 m genau")
        q = np.rint(h * ns["KD_STEP"]) / ns["KD_STEP"]
        ok(float(np.abs(dec(enc(q)) - h).max()) < 0.1, "terrarium mit 1/%d m (so in den Kacheln): auf 0.1 m genau" % ns["KD_STEP"])
        ok(enc(np.zeros((1, 1)))[0, 0].tolist() == [128, 0, 0], "0 m = terrarium 128 / 0 / 0 (Wert von MapLibre)")
        st = ns["kd_state"]()
        ok(st["on"] is False and not st["host"] and re.fullmatch(r"[0-9a-f]{12}v\d+", st["key"]), "ohne Höhendaten: 3D-Kacheln aus")
        hp = os.path.join(tmp, "hoehe-ch-1.bin")
        r = hoehe_datei(hp)
        einsetzen(ns, hp)
        st = ns["kd_state"]()
        b_ = st.get("bounds") or [0, 0, 0, 0]
        ok(st["on"] and b_[0] < 8.0 < 8.3 < b_[2] and b_[1] < 47.25 < 47.42 < b_[3], f"Höhendatei ({r['bytes'] // 1024} KB) eingesetzt: an, Rahmen {b_}")
        f = ns["kh_file"]()
        # one tile over the «Alps» at z13 and z12: the heights of the file at every pixel
        for z in (12, 13, 10):
            x, y = kachel_von(47.3475, 8.1602, z)
            t0 = time.time(); b = ns["kd_tile"](z, x, y); ms = (time.time() - t0) * 1000
            H = png_hoehen(ns, b)
            LO, LA = pixel_lagen(z, x, y)
            E, N = ns["kh_lv95"](LA, LO)
            soll = hoehe_fn(E, N)
            inn = ((E - E0) / GRID > 100.5) & ((N - N0) / GRID > 80.5) & ((E - E0) / GRID < COLS - 1.5) & ((N - N0) / GRID < ROWS - 1.5)
            fehl = float(np.abs(H - soll)[inn].max()) if inn.any() else 99
            ok(H is not None and H.shape == (256, 256) and inn.sum() > 1000 and fehl < 1.5,
               f"Kachel z{z}/{x}/{y}: {len(b) // 1024} KB, {ms:.0f} ms, Höhen = Datei (grösste Abweichung {fehl:.2f} m, {int(H.max())} m hoch)")
        # outside: far away (Genf) and the empty corner
        x, y = kachel_von(46.2, 6.14, 12)
        H = png_hoehen(ns, ns["kd_tile"](12, x, y))
        ok(H is not None and float(np.abs(H).max()) == 0.0 and ns["kd_heights"](f, 12, x, y) is None, "ausserhalb der Datei (Genf): 0 m")
        la, lo = ns["kd_wgs84"](E0 + 40 * GRID, N0 + 30 * GRID)            # in the corner without data
        x, y = kachel_von(la, lo, 13)
        H = png_hoehen(ns, ns["kd_tile"](13, x, y))
        LO, LA = pixel_lagen(13, x, y)
        E, N = ns["kh_lv95"](LA, LO)
        leer = ((E - E0) / GRID < 98) & ((N - N0) / GRID < 78) & ((E - E0) / GRID > -1) & ((N - N0) / GRID > -1)
        ok(leer.sum() > 100 and float(np.abs(H[leer]).max()) == 0.0 and float(H[~leer].max()) > 400, "Ecke ohne Daten: 0 m, daneben die Höhen")
        ok(ns["kd_tile"](7, 66, 44) is None and ns["kd_tile"](14, 8580, 5745) is None and ns["kd_tile"](12, 9999, 1) is None, "Zoom ausserhalb 8–13 / Kachel ausserhalb: keine Antwort")
        # cache: hit, limit (oldest out, a used one stays), old key, removal
        d = ns["kd_cache_dir"]()
        n0 = len(os.listdir(d))
        hits = ns["KD_RT"]["hits"]; ns["kd_tile"](13, *kachel_von(47.3475, 8.1602, 13))
        ok(n0 >= 4 and ns["KD_RT"]["hits"] == hits + 1, f"Zwischenspeicher: {n0} Kacheln in {os.path.relpath(d, home)}, zweiter Abruf aus dem Speicher")
        x0, y0 = kachel_von(47.3475, 8.1602, 13)
        alle = [(13, x0 + dx, y0 + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
        for k in alle:
            ns["kd_tile"](*k)
        gr = sorted(os.path.getsize(os.path.join(d, x_)) for x_ in os.listdir(d))
        erst = os.path.join(d, "%d-%d-%d.png" % alle[0])
        alt = time.time() - 3600
        for i, x_ in enumerate(sorted(os.listdir(d))):
            os.utime(os.path.join(d, x_), (alt + i, alt + i))
        ns["kd_tile"](*alle[0])                                          # used again: young
        ns["KD_CACHE_MAX"] = int(sum(gr[-4:]) * 1.05)
        neu = (12, *kachel_von(47.30, 8.10, 12))
        ns["kd_tile"](*neu)
        tot = sum(os.path.getsize(os.path.join(d, x_)) for x_ in os.listdir(d))
        ok(tot <= ns["KD_CACHE_MAX"] and os.path.isfile(erst) and os.path.isfile(os.path.join(d, "%d-%d-%d.png" % neu)) and ns["KD_RT"]["bytes"] == tot,
           f"Grenze {ns['KD_CACHE_MAX'] // 1024} KB hält ({len(os.listdir(d))} Kacheln, {tot // 1024} KB), gerade gebrauchte bleiben")
        ns["KD_CACHE_MAX"] = 256 << 20
        os.makedirs(os.path.join(os.path.dirname(d), "0123456789abv0"))
        ns["KD_RT"]["bytes"] = None
        ns["kd_tile"](13, x0 + 2, y0)
        ok(not os.path.exists(os.path.join(os.path.dirname(d), "0123456789abv0")), "Ordner eines alten Schlüssels wird weggeräumt")
        ok(ns["kh_delete"]()[0] and not os.path.exists(d) and not ns["kd_state"]()["on"], "«Entfernen» der Höhendaten löscht auch die Kacheln")
        # host: nothing
        ns["HOST"] = {"on": True}
        st = ns["kd_state"]()
        pg = ns["kq_page"]()
        ok(st == {"on": False, "host": True} and '"host": true' in pg and not ns["kd_on"](), "Host: keine 3D-Kacheln, die Seite weiss es (kein Schalter)")
        ns["HOST"] = {"on": False}
        tx = ns["k3_tx"]()
        ok(set(tx) == {"de", "fr", "it", "rm", "en"} and all(all(tx[L].values()) and len(tx[L]) == len(tx["en"]) for L in tx)
           and tx["de"]["Load height data of Switzerland"] == "Höhendaten Schweiz laden", "Texte in 5 Sprachen («Höhendaten Schweiz laden»)")
        ok(all(ns["_HELP_K3"][L][0] in (ns["HELP_X"].get(L, "") if L in ("fr", "it", "rm") else ns["HELP_PAGE"]) for L in ("de", "en", "fr", "it", "rm")), "Anleitung in 5 Sprachen")
    finally:
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


# ---- B --------------------------------------------------------------------------------------------------------------------------------
def teil_b(datei, web, bilder):
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    import karten_test as KA
    import bergkarte_test as BG
    print("B) im Browser (390 × 844 DPR 2 und 1366 × 768)", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_k3d_b_")
    p = None
    try:
        web = BG.web_zip(web, tmp)
        P, rel, pins, _t = KA.dateien_bauen(tmp, web)
        hp = os.path.join(tmp, "hoehe-ch-1.bin")
        hoehe_datei(hp)
        hdata = open(hp, "rb").read()
        srv = Srv()
        for f in pins.values():
            srv.files["/" + f["tag"] + "/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
        srv.files["/hoehen-1/hoehe-ch-1.bin"] = hdata
        t1 = os.path.join(tmp, "run"); os.makedirs(t1)
        d2 = KA.gepatcht(datei, t1, pins, srv.url)
        src = open(d2, encoding="utf-8").read()
        alt = '"https://github.com/DonElektro/MotionWatch/releases/download/" + KH_TAG + "/"'
        src, n1 = re.subn(r'^KH_FILE = \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*"\}',
                          'KH_FILE = {"name": "hoehe-ch-1.bin", "size": %d, "sha256": "%s"}' % (len(hdata), hashlib.sha256(hdata).hexdigest()), src, flags=re.M)
        assert n1 == 1 and src.count(alt) == 1
        open(d2, "w", encoding="utf-8").write(src.replace(alt, json.dumps(srv.url + "hoehen-1/"), 1))
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
        PW = "Drei-" + os.urandom(4).hex()
        p, _cfg = KA.starte(d2, t1, port, PW)
        base = f"http://127.0.0.1:{port}"
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def req(path, d=None, user=("admin", PW), raw=False):
            hd = {"Content-Type": "application/json", "Origin": base}
            if user:
                hd["Authorization"] = "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode()
            r = urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None, headers=hd)
            try:
                with op.open(r, timeout=120) as x:
                    b = x.read()
                    return x.status, (b if raw else json.loads(b or b"{}"))
            except urllib.error.HTTPError as e:
                return e.code, (b"" if raw else {})
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(t1, "log.txt")).read()[-3000:])
            try:
                if req("/api/karte")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        req("/api/karte", {"action": "install"})
        for _i in range(240):
            if req("/api/karte")[1].get("on"):
                break
            time.sleep(0.5)
        ok(req("/api/karte")[1].get("on") and req("/api/karte")[1].get("topo"), "Test-Karte mit Topo-Relief installiert")
        time.sleep(2.5)
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        lage = "/karte?welt=ch&lat=47.335&lon=8.17&z=12.4"
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []
            for name, mob, vp in (("390", True, {"width": 390, "height": 844}), ("pc", False, {"width": 1366, "height": 768})):
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                     http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','light');localStorage.setItem('mw-sheet','page');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                dem = []
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.on("response", lambda r: dem.append(r.status) if "/karte/dem/" in r.url else None)
                konsole = []
                pg.on("console", lambda m: konsole.append(m.text[:200]) if m.type in ("warning", "error") else None)
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                bereit = "() => window.KQMAP && KQMAP.loaded() && window.K3 && document.getElementById('kq-3d')"

                def laden(fake):
                    pg.goto("about:blank")
                    if fake:
                        pg.add_init_script(FAKE_KQ)
                    pg.goto(base + lage)
                    pg.wait_for_function(bereit, timeout=90000)
                    pg.wait_for_timeout(800)
                if name == "390":                        # no height data yet: the hint (only once, then the data are loaded)
                    pg.add_init_script(FAKE_KQ)
                    pg.goto(base + lage)
                    pg.wait_for_function(bereit, timeout=90000)
                    pos = pg.evaluate("() => { const a = document.getElementById('kq-map').getBoundingClientRect(), b = document.querySelector('.kq-3d').getBoundingClientRect(); return [a.left, a.top, b.left, b.top]; }")
                    ok(6 <= pos[2] - pos[0] <= 12 and 6 <= pos[3] - pos[1] <= 12 and pg.locator("#kq-map .kq-sw").count() == 1 and pg.locator("#kq-3d").inner_text() == "3D" and pg.locator("#kq-2d.on").count() == 1,
                       f"{name}: ohne Topo-Karte Schalter «2D | 3D» oben links (wie im Bergtal), 2D an")
                    tap("#kq-3d")
                    pg.wait_for_selector("#kq-3dhint:not([hidden])", timeout=5000)
                    tx = pg.inner_text("#kq-3dhint")
                    ok("3D braucht die Höhendaten Schweiz" in tx and "Höhendaten Schweiz laden" in tx and not pg.evaluate("() => !!KQMAP.getTerrain() || K3.d3")
                       and pg.locator("#kq-2d.on").count() == 1, f"{name}: ohne Höhendaten Hinweis «Höhendaten Schweiz laden», 2D bleibt")
                    if bilder:
                        pg.screenshot(path=os.path.join(bilder, f"karte3d_hinweis_{name}.png"))
                    tap("#kq-3dload")
                    pg.wait_for_timeout(1200)
                    ok(pg.evaluate("() => { const r = document.getElementById('kt-hbox').getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight; }")
                       and pg.locator("#kq-3dhint").is_hidden(), f"{name}: der Link führt zum Feld «⛰ Höhendaten Schweiz»")
                    req("/api/touren", {"action": "hoehe_install"})
                    for _i in range(120):
                        if req("/api/touren")[1].get("hoehe", {}).get("on"):
                            break
                        time.sleep(0.5)
                    ok(req("/api/touren")[1]["hoehe"]["on"], "Höhendaten (Testdatei) über HTTP geladen")
                    time.sleep(2.2)
                    pg.close(); pg = ctx.new_page()
                    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                    pg.on("response", lambda r: dem.append(r.status) if "/karte/dem/" in r.url else None)
                    tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                # with height data, without the relief of the topo map: the terrain from /karte/dem
                laden(True)
                ok(pg.evaluate("() => K3.from()") == "dem", f"{name}: ohne Topo-Relief kommen die Höhen aus /karte/dem")
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"karte3d_2d_{name}.png"))
                tap("#kq-3d")
                try:
                    pg.wait_for_function("() => KQMAP.getPitch() > 40 && KQMAP.getTerrain() && KQMAP.getTerrain().source === 'kq-dem'", timeout=90000)
                except Exception:
                    print("  Zustand:", pg.evaluate("() => JSON.stringify({d3: K3.d3, from: K3.from(), pitch: KQMAP.getPitch(), terrain: KQMAP.getTerrain(), style: KQMAP.isStyleLoaded(), loaded: KQMAP.loaded(), on: document.querySelector('#kq-3d').className})"), "Konsole:", konsole[-5:], flush=True)
                    raise
                try:
                    pg.wait_for_function("() => (() => { try { return KQMAP.queryTerrainElevation(KQMAP.getCenter()) > 500; } catch (e) { return false; } })()", timeout=60000)
                except Exception:
                    pass
                pg.wait_for_timeout(3000)
                el = pg.evaluate("() => { try { return KQMAP.queryTerrainElevation(KQMAP.getCenter()) || 0; } catch (e) { return -1; } }")
                ok(pg.evaluate("() => !!KQMAP.getLayer('kq-hill') && K3.d3 && document.querySelector('#kq-3d').classList.contains('on') && KQMAP.dragRotate.isEnabled()")
                   and dem and all(s == 200 for s in dem) and el > 500,
                   f"{name}: 3D aus /karte/dem – geneigt {pg.evaluate('() => Math.round(KQMAP.getPitch())')}°, Relief, {len(dem)} Kacheln (200), Gelände {el:.0f} m")
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"karte3d_3d_dem_{name}.png"), timeout=90000)
                tap("#kq-2d")
                pg.wait_for_function("() => KQMAP.getPitch() < 0.01 && Math.abs(KQMAP.getBearing()) < 0.01 && !KQMAP.getTerrain() && !KQMAP.isMoving()", timeout=60000)
                ok(not pg.evaluate("() => !!KQMAP.getLayer('kq-hill') || KQMAP.dragRotate.isEnabled() || KQMAP.getMaxPitch() !== 0"), f"{name}: 2D wieder von oben, ohne Drehen und Neigen")
                # with the relief of the topo map: remembered over a reload, terrain from «relief»
                tap("#kq-3d")
                pg.wait_for_function("() => K3.d3", timeout=10000)
                pg.goto("about:blank"); pg.close(); pg = ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                n_dem = len(dem)
                pg.on("response", lambda r: dem.append(r.status) if "/karte/dem/" in r.url else None)
                pg.goto(base + lage)
                pg.wait_for_function(bereit, timeout=90000)
                pg.wait_for_function("() => KQMAP.getPitch() > 40 && KQMAP.getTerrain() && KQMAP.getTerrain().source === 'relief'", timeout=90000)
                pos = pg.evaluate("() => { const a = document.querySelector('#kq-map .kq-sw:not(.kq-3d)').getBoundingClientRect(), b = document.querySelector('.kq-3d').getBoundingClientRect(); return [a.left, a.bottom, b.left, b.top]; }")
                ok(abs(pos[0] - pos[2]) < 1 and pos[3] >= pos[1] + 2, f"{name}: mit Topo-Karte «2D | 3D» direkt unter «Standard | Topo»")
                ok(pg.evaluate("() => K3.from()") == "relief" and not pg.evaluate("() => !!KQMAP.getLayer('kq-hill')"), f"{name}: mit Topo-Relief: 3D gemerkt, Gelände aus «relief» (kein zweites Relief)")
                pg.wait_for_timeout(2500)
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"karte3d_3d_relief_{name}.png"), timeout=90000)
                pg.evaluate("() => document.querySelector('#kq-map .kq-sw:not(.kq-3d) button[data-v=std]').click()")
                pg.wait_for_function("() => KQMAP.getTerrain() && KQMAP.getTerrain().source === 'kq-dem' && !!KQMAP.getLayer('kq-hill') && !KQMAP.getStyle().sources.topo", timeout=60000)
                ok(len(dem) == n_dem and pg.evaluate("() => /\\/relief\\//.test(KQMAP.getStyle().sources['kq-dem'].tiles[0]) && document.querySelector('#kq-map .kq-attr').textContent.includes('swisstopo')"),
                   f"{name}: «Standard»: 3D bleibt (Relief der Topo-Karte als eigene Quelle, eigene Schattierung, Quelle © swisstopo)")
                pg.evaluate("() => document.querySelector('#kq-map .kq-sw:not(.kq-3d) button[data-v=topo]').click()")
                pg.wait_for_function("() => KQMAP.getTerrain() && KQMAP.getTerrain().source === 'relief' && !KQMAP.getLayer('kq-hill')", timeout=60000)
                ok(True, f"{name}: zurück auf «Topo»: Gelände wieder aus «relief»")
                # full screen: under CI load (software WebGL, 3D terrain) the page is busy drawing, so wait until the map
                # is quiet before the tap and give the full-screen change as long as the other 3D steps (was 10 s: red twice in CI)
                def vollbild(an):
                    try:
                        pg.wait_for_function("() => KQMAP.loaded() && !KQMAP.isMoving() && KQMAP.areTilesLoaded()", timeout=60000)
                    except Exception:
                        pass
                    tap("#kq-full")
                    soll = "" if an else "!"
                    try:
                        pg.wait_for_function(f"() => {soll}document.getElementById('kq-map').classList.contains('kq-fs')", timeout=60000)
                    except Exception:
                        zu = pg.evaluate("() => ({cls: document.getElementById('kq-map').className, fs: !!document.fullscreenElement, btn: (document.getElementById('kq-full') || {}).textContent})")
                        raise AssertionError(f"{name}: Vollbild {'an' if an else 'aus'} kam nicht – {zu}")
                vollbild(True)
                pg.wait_for_timeout(600)
                vis = pg.evaluate("() => { const r = document.querySelector('.kq-3d').getBoundingClientRect(); return r.top >= 0 && r.bottom < innerHeight && r.width > 40; }")
                tap("#kq-2d")
                pg.wait_for_function("() => KQMAP.getPitch() < 1 && !KQMAP.getTerrain()", timeout=60000)
                tap("#kq-3d")
                pg.wait_for_function("() => KQMAP.getPitch() > 40 && !!KQMAP.getTerrain()", timeout=90000)
                pg.wait_for_timeout(2000)
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"karte3d_vollbild_{name}.png"), timeout=90000)
                ok(vis, f"{name}: im Vollbild «⛶» ist «2D | 3D» da und schaltet")
                vollbild(False)
                tap("#kq-2d")
                ok(not errs, f"{name}: keine JS-Fehler" + (" – " + "; ".join(errs[:3]) if errs else ""))
                ctx.close()
            ok(not aussen, "keine Anfrage nach aussen" + (" – " + ", ".join(aussen[:3]) if aussen else ""))
            br.close()
        # rights and addresses
        key = req("/api/karte")[1] and None
        html = req("/karte", raw=True)[1].decode("utf-8", "replace")
        m = re.search(r'"key": "([0-9a-f]{12}v\d+)"', html)
        key = m.group(1) if m else "x"
        x, y = kachel_von(47.3475, 8.1602, 12)
        c1, b1 = req(f"/karte/dem/{key}/12/{x}/{y}.png", raw=True)
        c2, _ = req(f"/karte/dem/{key}/12/{x}/{y}.png", raw=True, user=None)
        c3, _ = req(f"/karte/dem/{key}/12/{x}/{y}.png", raw=True, user=("Anna", "anna-pass-1"))
        c4, _ = req(f"/karte/dem/0123456789abv1/12/{x}/{y}.png", raw=True)
        c5, _ = req(f"/karte/dem/{key}/14/{x * 4}/{y * 4}.png", raw=True)
        ok(c1 == 200 and b1[:8] == b"\x89PNG\r\n\x1a\n" and c2 == 401 and c3 == 200 and c4 == 404 and c5 == 404,
           f"Rechte: Admin {c1}, ohne Anmeldung {c2}, Familie {c3}; falscher Schlüssel {c4}, Zoom 14 {c5}")
    finally:
        if p is not None:
            p.terminate()
            try:
                p.wait(20)
            except Exception:
                p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


# ---- echt (nur lokal) ----------------------------------------------------------------------------------------------------------------
def teil_echt(datei, hb):
    import numpy as np
    print("Echte Höhendaten (DHM25): Zeit pro Kachel", flush=True)
    home = tempfile.mkdtemp(prefix="mw_k3d_echt_")
    try:
        ns = lade(datei, home)
        d = os.path.dirname(ns["kh_path"]()); os.makedirs(d)
        os.symlink(os.path.abspath(hb), ns["kh_path"]())
        json.dump({"tag": ns["KH_TAG"], "sha256": ns["KH_FILE"]["sha256"]}, open(ns["kh_path"]() + ".ok", "w"))
        ok(ns["kd_on"](), "echte Höhendaten an (Prüfsumme wie gepinnt)")
        f = ns["kh_file"]()
        for (wo, la, lo) in (("Matterhorn", 45.9763, 7.6586), ("Mitte", 46.8, 8.2), ("Bern", 46.948, 7.4474)):
            row = []
            for z in range(8, 14):
                x, y = kachel_von(la, lo, z)
                f.cache.clear()
                t0 = time.time(); b = ns["kd_tile"](z, x, y); ms = (time.time() - t0) * 1000
                row.append(f"z{z} {ms:.0f} ms {len(b) // 1024} KB")
            print(f"  {wo}: " + " · ".join(row), flush=True)
        H = png_hoehen(ns, ns["kd_tile"](13, *kachel_von(45.9763, 7.6586, 13)))
        ok(4300 < H.max() < 4500, f"Matterhorn-Kachel: höchster Punkt {H.max():.0f} m (DHM25 25 m, Gipfel 4478 m)")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei", default="")
    ap.add_argument("--web", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    ap.add_argument("--echt", default="", help="echte hoehe-ch-1.bin (nur lokal)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste_datei())
    print(f"Karte 3D · {os.path.basename(datei)}", flush=True)
    if a.echt:
        teil_echt(datei, a.echt)
    else:
        teil_a(datei)
        if not a.ohne_browser:
            teil_b(datei, a.web, a.bilder)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Karte-3D-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
