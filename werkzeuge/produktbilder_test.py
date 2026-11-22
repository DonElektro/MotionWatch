#!/usr/bin/env python3
"""Test «🖼 Produktseite: Bilder» (MoveEye Teil 639zzzze) – eigene Fotos statt der Beispielbilder der Gäste-Seite /info/.

MoveEye (gebaute Datei, --demo --headless, eigener Daten-Ordner, Passwort, ein Benutzer «Nur ansehen») läuft auf 127.0.0.1:
  * Hochladen (JPEG mit EXIF: Kamera, GPS) → 16:9 1280 × 720 WebP, EXIF / GPS weg, Ausschnitt-Regler (pos 0 = linker Rand),
    Markierung + Text; PNG mit Transparenz; kaputte Datei → 400 mit deutschem Text.
  * /info/ zeigt das neue Bild (/info/bild/<platz>.webp, ohne Anmeldung), window.PB mit Markierung; «Zurück zum Beispiel»:
    /info/ wieder mit dem Beispiel, /info/bild/… → 404.
  * Rechte: Benutzer «Nur ansehen» → 403 (Seite, Zustand, Hochladen, Vorschau); Administrator → 200.
  * --browser: Knopf in der Karte «Homepage» neben dem Upload-Schlüssel, Seite /produktbilder bei 390 px (keine waagrechte Bildlaufleiste, keine JS-Fehler) und /info/ mit dem eigenen
    Bild und der Markierung; --bilder ORDNER: Bildschirmfotos vorher / nachher.

  python3 werkzeuge/produktbilder_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--foto BILD]
"""
import argparse
import base64
import glob
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
PW = "pb-test-pw-1"


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def pwhash(pw):
    salt = os.urandom(16)
    return "pbkdf2$200000$%s$%s" % (salt.hex(), hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200000).hex())


def foto_jpeg(w=2000, h=1000):
    """left half red, right half blue, with EXIF (camera name and GPS) - like a phone photo"""
    from PIL import Image
    im = Image.new("RGB", (w, h), (200, 30, 30))
    im.paste((30, 40, 200), (w // 2, 0, w, h))
    ex = Image.Exif(); ex[0x010F] = "TestCamFirma"; ex[0x0110] = "TestCamModell"
    ex[0x8825] = {1: "N", 2: (47.0, 3.0, 12.5), 3: "E", 4: (8.0, 18.0, 30.0)}
    b = io.BytesIO(); im.save(b, "JPEG", quality=90, exif=ex.tobytes())
    return b.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--foto", default="", help="ein eigenes Foto für die Bilder «nachher» (sonst ein erzeugtes)")
    a = ap.parse_args()
    ver = lambda f: tuple(int(x) for x in re.findall(r"(\d+)_(\d+)_(\d+)\.py$", f)[0])
    datei = os.path.abspath(a.datei or max(glob.glob(os.path.join(REPO, "webcam_bewegung_*_*_*.py")), key=ver))             # MoveEye starts with cwd = tmp
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix="mw_pbtest_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "detection_on": False, "info_page": True,
          "users": [{"name": "gast", "hash": pwhash("gast-pw-123"), "role": "view"}]}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "home"), NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        env[k] = "http://127.0.0.1:9"
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", PW],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user="admin", pw=PW, ctype="application/json", auth=True):
        h = {"Content-Type": ctype}
        if auth:
            h["Authorization"] = "Basic " + base64.b64encode((user + ":" + pw).encode()).decode()
        r = urllib.request.Request(base + path, data=data, headers=h, method="POST" if data is not None else "GET")
        try:
            with op.open(r, timeout=60) as x:
                return x.status, x.headers.get("Content-Type", ""), x.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", ""), e.read()

    def js(c_t_b):
        try:
            return json.loads(c_t_b[2] or b"{}")
        except ValueError:
            return {}
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        shots = a.bilder and a.browser
        if shots:
            browser(base, a.bilder, "vorher", None, a.foto)
        c, _t, b = req("/api/produktbilder")
        st0 = json.loads(b) if c == 200 else {}
        ok(c == 200 and [s["id"] for s in st0.get("slots", [])] == ["live", "tag", "nacht", "damals", "jetzt", "app_kamera", "app_live", "app_tagebuch", "zelt"] and not any(s["custom"] for s in st0["slots"]),
           "Zustand: neun Bildplätze (4.22.x: dazu die vier der App-Galerie), alle «Beispiel» (%d)" % c)
        ok([s["ratio"] for s in st0.get("slots", [])][5:] == ["1280/720", "520/1125", "520/1125", "1280/592"], "Form der neuen Plätze (Handy hochkant, Film-Karte)")
        for s in ["live", "tag", "nacht", "damals", "jetzt", "app_kamera", "app_live", "app_tagebuch", "zelt"]:
            c, t, b = req("/api/produktbilder/bild/" + s)
            ok(c == 200 and t.startswith("image/") and b[:4] == b"RIFF", "Vorschau Beispiel «%s» (%d, %s)" % (s, c, t))
        # rights
        g = [req("/produktbilder", user="gast", pw="gast-pw-123")[0], req("/api/produktbilder", user="gast", pw="gast-pw-123")[0],
             req("/api/produktbilder?action=set&slot=jetzt&pos=50", foto_jpeg(), user="gast", pw="gast-pw-123", ctype="application/octet-stream")[0],
             req("/api/produktbilder/bild/jetzt", user="gast", pw="gast-pw-123")[0],
             req("/api/produktbilder?action=reset", json.dumps({"slot": "jetzt"}).encode(), user="gast", pw="gast-pw-123")[0]]
        ok(g == [403] * 5, "Benutzer «Nur ansehen»: Seite / Zustand / Hochladen / Vorschau / zurück → 403 (%s)" % g)
        ok(req("/produktbilder")[0] == 200, "Administrator: Seite /produktbilder 200")
        c, _t, hp = req("/homepage"); c2, _t, tl = req("/tools")
        ok(c == 200 and b'id="hp-pbild" href="/produktbilder"' in hp, "Einstieg in der Karte «Homepage» (/homepage)")
        ok(c2 == 200 and b"/produktbilder" not in tl, "nicht mehr unter Mehr → Werkzeuge")
        ok(req("/homepage", user="gast", pw="gast-pw-123")[0] == 403, "Benutzer «Nur ansehen»: /homepage 403")
        ok(req("/api/produktbilder", auth=False)[0] == 401, "ohne Anmeldung: 401")
        # upload: JPEG with EXIF / GPS, cut at the left edge, with a mark
        raw = foto_jpeg()
        ok(b"TestCamFirma" in raw, "Testfoto mit EXIF (%d KB)" % (len(raw) // 1024))
        c, _t, b = req("/api/produktbilder?action=set&slot=jetzt&pos=0&box=10,20,30,40&label=" + urllib.request.quote("neu: Bank"), raw,
                       ctype="application/octet-stream")
        j = json.loads(b or b"{}")
        sj = next((s for s in j.get("slots", []) if s["id"] == "jetzt"), {})
        ok(c == 200 and j.get("ok") and sj.get("custom") and sj.get("box") == [10.0, 20.0, 30.0, 40.0] and sj.get("label") == "neu: Bank",
           "hochladen «Zeitfenster: jetzt» mit Markierung (%d %s)" % (c, sj))
        files = os.listdir(os.path.join(cfg, "produktseite"))
        ok(sorted(files) == ["bilder.json", "jetzt.webp"], "gespeichert im Daten-Ordner: %s" % files)
        c, t, img = req("/info/bild/jetzt.webp?v=1", auth=False)
        ok(c == 200 and t == "image/webp", "/info/bild/jetzt.webp ohne Anmeldung (%d, %s, %d KB)" % (c, t, len(img) // 1024))
        im = Image.open(io.BytesIO(img))
        ok(im.size == (1280, 720), "16:9, 1280 × 720 (%s)" % (im.size,))
        ok(b"TestCam" not in img and b"Exif" not in img and b"EXIF" not in img and b"XMP" not in img and not im.getexif(), "EXIF / GPS / Kamera entfernt")
        px = im.convert("RGB").getpixel((20, 360)), im.convert("RGB").getpixel((1260, 360))
        ok(px[0][0] > 150 and px[1][2] > 150, "Ausschnitt pos=0: links rot, rechts blau (%s, %s)" % px)
        c, _t, h = req("/info/", auth=False); h = h.decode()
        ok(c == 200 and '<img src="/info/bild/jetzt.webp?v=' in h and "window.PB=" in h and "neu: Bank" in h,
           "/info/ zeigt das eigene Bild und die Markierung")
        # PNG with transparency, a wrong file
        b2 = io.BytesIO(); Image.new("RGBA", (1000, 1000), (20, 160, 60, 120)).save(b2, "PNG")
        c, _t, b = req("/api/produktbilder?action=set&slot=tag&pos=50", b2.getvalue(), ctype="application/octet-stream")
        ok(c == 200, "PNG mit Transparenz (Hochformat → Mitte 16:9) %d" % c)
        c, _t, b = req("/api/produktbilder?action=set&slot=nacht&pos=50", b"kein Bild", ctype="application/octet-stream")
        ok(c == 400 and "kann nicht gelesen werden" in json.loads(b).get("error", ""), "kaputte Datei: 400 «%s»" % json.loads(b or b"{}").get("error"))
        c, _t, b = req("/api/produktbilder?action=set&slot=nacht&pos=50", foto_jpeg(400, 300), ctype="application/octet-stream")
        ok(c == 400 and "zu klein" in json.loads(b).get("error", ""), "zu kleines Bild: 400")
        c, _t, b = req("/api/produktbilder?action=set&slot=hacker&pos=50", foto_jpeg(), ctype="application/octet-stream")
        ok(c == 400, "unbekannter Bildplatz: 400")
        # 4.22.x: the gallery slots - a phone screenshot (portrait) and the film card
        b3 = io.BytesIO(); Image.new("RGB", (1170, 2532), (30, 40, 60)).save(b3, "PNG")
        c, _t, b = req("/api/produktbilder?action=set&slot=app_tagebuch&pos=50", b3.getvalue(), ctype="application/octet-stream")
        c2, t2, img2 = req("/info/bild/app_tagebuch.webp?v=1", auth=False)
        ok(c == 200 and c2 == 200 and Image.open(io.BytesIO(img2)).size == (520, 1125), "«App: Tagebuch» hochkant 520 × 1125 (%d, %d)" % (c, c2))
        c, _t, b = req("/api/produktbilder?action=set&slot=zelt&pos=50", foto_jpeg(500, 200), ctype="application/octet-stream")
        ok(c == 400 and "mindestens 640 × 296" in json.loads(b).get("error", ""), "Film-Karte: zu kleines Bild «%s»" % json.loads(b or b"{}").get("error"))
        c, _t, h = req("/info/", auth=False); h = h.decode()
        ok('src="/info/bild/app_tagebuch.webp?v=' in h and 'id="app-tagebuch"' in h and '<video' in h, "/info/: eigenes «Tagebuch», der Film bleibt")
        req("/api/produktbilder?action=reset", json.dumps({"slot": "app_tagebuch"}).encode())
        c, _t, b = req("/api/produktbilder?action=box", json.dumps({"slot": "jetzt", "box": [5, 5, 50, 50], "label": "neu: Holz"}).encode())
        ok(c == 200 and next(s for s in json.loads(b)["slots"] if s["id"] == "jetzt")["label"] == "neu: Holz", "Markierung ändern")
        if shots:
            if a.foto:
                for s in ("live", "tag", "jetzt"):
                    req("/api/produktbilder?action=set&slot=%s&pos=50" % s, open(a.foto, "rb").read(), ctype="application/octet-stream")
                req("/api/produktbilder?action=box", json.dumps({"slot": "jetzt", "box": [40, 55, 25, 30], "label": "neu: Tisch"}).encode())
            browser(base, a.bilder, "nachher", "jetzt", a.foto)
        elif a.browser:
            for s in ("live", "tag", "app_kamera", "zelt"):   # 4.19.1 + 4.22.x: own pictures also in the gallery cards
                req("/api/produktbilder?action=set&slot=%s&pos=50" % s, raw, ctype="application/octet-stream")
            browser(base, "", "", "jetzt", "")
            for s in ("live", "tag", "app_kamera", "zelt"):
                req("/api/produktbilder?action=reset", json.dumps({"slot": s}).encode())
        # back to the example
        c, _t, b = req("/api/produktbilder?action=reset", json.dumps({"slot": "jetzt"}).encode())
        ok(c == 200 and not next(s for s in json.loads(b)["slots"] if s["id"] == "jetzt")["custom"], "«Zurück zum Beispiel» (%d)" % c)
        c, _t, h = req("/info/", auth=False)
        ok("/info/bild/jetzt.webp" not in h.decode() and req("/info/bild/jetzt.webp", auth=False)[0] == 404, "/info/ wieder mit dem Beispiel, /info/bild/jetzt.webp → 404")
        log = open(os.path.join(cfg, "motionwatch.log"), errors="replace").read() if os.path.isfile(os.path.join(cfg, "motionwatch.log")) else ""
        ok("TestCam" not in log and "47.0" not in log, "nichts aus dem EXIF im Protokoll")
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("ALLES OK" if not FEHLER else "%d FEHLER:\n  " % len(FEHLER) + "\n  ".join(FEHLER)))
    sys.exit(1 if FEHLER else 0)


def browser(base, bilder, tag, slot, foto=""):
    from playwright.sync_api import sync_playwright
    if bilder:
        os.makedirs(bilder, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme="dark",
                             http_credentials={"username": "admin", "password": PW}, locale="de-CH")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        # the entry: card «Homepage», next to the upload key
        pg.goto(base + "/homepage", wait_until="domcontentloaded")
        pg.wait_for_selector("#hp-pbild", timeout=30000); pg.wait_for_timeout(800)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov','g2-spot','g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
        hp = pg.evaluate("() => { const a = document.getElementById('hp-pbild'), k = document.getElementById('hp-key-b'); "
                         "return [a.textContent.trim(), a.parentElement === k.parentElement, a.getBoundingClientRect().width > 100]; }")
        ok(hp == ["🖼 Produktseite: Bilder", True, True], "Homepage-Karte: Knopf neben dem Upload-Schlüssel %s" % hp)
        ok(pg.evaluate("() => document.documentElement.scrollWidth") <= 390, "/homepage: keine waagrechte Bildlaufleiste")
        if bilder:
            pg.locator("section.card", has=pg.locator("#hp-key-b")).screenshot(path=os.path.join(bilder, "homepage_karte_%s.png" % tag))
        pg.locator("#hp-pbild").click(); pg.wait_for_url("**/produktbilder", timeout=20000)
        ok(pg.url.endswith("/produktbilder"), "Knopf öffnet /produktbilder")
        pg.goto(base + "/produktbilder", wait_until="domcontentloaded")
        pg.wait_for_function("() => document.querySelectorAll('#pb-list .pb-c').length === 9", timeout=30000)
        pg.wait_for_function("() => [...document.querySelectorAll('#pb-list img')].every(i => i.complete && i.naturalWidth > 0)", timeout=30000)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov','g2-spot','g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
        names = pg.evaluate("() => [...document.querySelectorAll('#pb-list .pb-b b')].map(b => b.textContent)")
        ok(names == ["Live-Bild (Handy)", "Sieh selbst: Tag", "Sieh selbst: Nacht", "Zeitfenster: damals", "Zeitfenster: jetzt",
                     "App: Kamerabild im Handy", "App: ganzer Bildschirm Live", "App: Tagebuch", "Nachts am Zelt"], "Seite: %s" % names)
        ar = pg.evaluate("() => ['app_live', 'zelt'].map(k => { const r = document.querySelector('#pb-' + k + ' .pb-pv').getBoundingClientRect(); return Math.round(r.width / r.height * 100) / 100; })")
        ok(abs(ar[0] - 0.46) < 0.03 and abs(ar[1] - 2.16) < 0.05, "Vorschau in der Form des Platzes (Handy hochkant, Film-Karte) %s" % ar)
        ok("Keine Personen, Kennzeichen oder Hausnummern." in pg.locator("#pb-h2").inner_text(), "Hinweis «Keine Personen, Kennzeichen oder Hausnummern»")
        bk = pg.evaluate("() => { const b = document.getElementById('pb-back'); return [b.textContent.trim(), b.getAttribute('href')]; }")
        ok(bk == ["‹ Homepage", "/homepage"], "Zurück-Link «‹ Homepage» → /homepage %s" % bk)
        ok(pg.evaluate("() => document.documentElement.scrollWidth") <= 390, "keine waagrechte Bildlaufleiste")
        if bilder:
            pg.screenshot(path=os.path.join(bilder, "produktbilder_%s.png" % tag), full_page=True)
        if slot:                                               # the editor: choose a file, slider, draw a box
            pg.locator("#pb-%s input[type=file]" % slot).set_input_files(foto or {"name": "foto.jpg", "mimeType": "image/jpeg", "buffer": foto_jpeg()})
            pg.wait_for_selector("#pb-%s .pb-ed" % slot)
            ed = pg.locator("#pb-%s .pb-ed .pb-pv" % slot); bb = ed.bounding_box()
            pg.mouse.move(bb["x"] + bb["width"] * .3, bb["y"] + bb["height"] * .3); pg.mouse.down()
            pg.mouse.move(bb["x"] + bb["width"] * .6, bb["y"] + bb["height"] * .7, steps=5); pg.mouse.up()
            pg.locator("#pb-%s .pb-ed input[type=text]" % slot).fill("neu: Tisch")
            ok(pg.locator("#pb-%s .pb-ed .pb-mk" % slot).count() == 1, "Editor: Rechteck gezogen")
            if bilder:
                pg.locator("#pb-%s" % slot).screenshot(path=os.path.join(bilder, "produktbilder_editor.png"))
            pg.locator("#pb-%s .pb-ed .pb-a button" % slot).first.click()
            pg.wait_for_function("(s) => { const c = document.getElementById('pb-' + s); return c && c.querySelector('.pb-st.own'); }", arg=slot, timeout=30000)
            ok(True, "Editor: «Bild speichern» → «Eigenes Bild»")
        ok(not errs, "keine JS-Fehler auf /produktbilder %s" % errs[:2])
        ctx2 = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="de-CH")
        p2 = ctx2.new_page(); e2 = []
        p2.on("pageerror", lambda e: e2.append(str(e)))
        p2.goto(base + "/info/", wait_until="load"); p2.wait_for_timeout(1500)
        for sel in ("#sehen", "#app"):           # 4.19.1: the Zeitfenster is part of «Sieh selbst» (#sehen, #zf)
            p2.locator(sel).scroll_into_view_if_needed(); p2.wait_for_timeout(1800)
            p2.add_style_tag(content=".bar,.prog{visibility:hidden!important}")
            if bilder:
                p2.locator(sel).screenshot(path=os.path.join(bilder, "info_%s_%s.png" % (sel[1:], tag)))
        if slot:
            st = p2.evaluate("() => { const i = document.getElementById('zf-now'), m = document.getElementById('zf-mark'); "
                             "return [i.getAttribute('src'), i.naturalWidth, m.hidden || getComputedStyle(m).display === 'none', (m.querySelector('span') || m).textContent]; }")
            ok(st[0].startswith("/info/bild/jetzt.webp") and st[1] > 0 and not st[2] and st[3].startswith("neu:"), "/info/: eigenes Bild und Markierung im Zeitfenster %s" % st)
            ov = p2.evaluate("() => [...document.querySelectorAll('img[data-pb]')].map(i => [i.dataset.pb, (i.getAttribute('src') || '').slice(0, 24)])")
            own = {k: v for k, v in ov}
            ok(sorted(own) == ["app_kamera", "app_live", "app_tagebuch", "damals", "jetzt", "live", "nacht", "tag", "zelt"], "/info/: neun Bildplätze data-pb (%s)" % sorted(own))
            gal = p2.evaluate("() => { const c = document.getElementById('app-cam'), l = document.getElementById('app-cam-live'), z = document.querySelector('[data-pb=zelt]'); "
                              "return [(c.getAttribute('src') || '').slice(0, 21), c.naturalWidth, !c.hidden, !l.hidden, z.tagName, (z.getAttribute('src') || '').slice(0, 17), !!document.getElementById('clip'), "
                              "(document.getElementById('app-live').getAttribute('src') || '').slice(0, 10)]; }")
            ok(gal[0] == "/info/bild/app_kamera" and gal[1] > 0 and gal[2] and gal[3] and gal[4] == "IMG" and gal[5] == "/info/bild/zelt.w" and not gal[6] and gal[7] == "data:image",
               "/info/: eigenes Kamerabild im Live-Bild-Handy (mit «LIVE»), eigenes Bild statt des Films, die App rundherum bleibt %s" % gal)
            if not foto:
                ok(own["live"].startswith("/info/bild/live.webp") and own["tag"].startswith("/info/bild/tag.webp") and own["nacht"].startswith("data:"),
                   "/info/: eigene Bilder ersetzen «Live-Bild Handy» und «Sieh selbst: Tag», die anderen bleiben Beispiele (%s)" % ov)
        wide = p2.evaluate("() => document.documentElement.scrollWidth")
        ok(wide <= 390, "/info/ bei 390 px ohne waagrechtes Scrollen (%d px)" % wide)
        ok(p2.evaluate("() => !!document.querySelector('[data-mw-exit]') && !!document.getElementById('ask') && document.querySelectorAll('.langs button[data-lang]').length >= 4"),
           "/info/: Knopf data-mw-exit, Formular, Sprachwahl")
        ok(not e2, "keine JS-Fehler auf /info/ (390 px) %s" % e2[:2])
        ctx3 = br.new_context(viewport={"width": 1440, "height": 900}, locale="de-CH")
        p3 = ctx3.new_page(); e3 = []
        p3.on("pageerror", lambda e: e3.append(str(e)))
        p3.goto(base + "/info/", wait_until="load"); p3.wait_for_timeout(1500)
        for sel in ("#nacht", "#sehen", "#app", "#technik", "#kontakt"):
            p3.locator(sel).scroll_into_view_if_needed(); p3.wait_for_timeout(700)
        p3.evaluate("() => { const b = document.querySelector('.langs button[data-lang=fr]'); if (b) b.click(); }"); p3.wait_for_timeout(500)
        ok(p3.evaluate("() => document.documentElement.lang") == "fr", "/info/ am PC: Sprachwahl fr")
        # 4.21.0: «Alle Funktionen» with search, tile with the number, footnote with this MoveEye's number (window.MW_VER)
        p3.evaluate("() => document.getElementById('af-tile').click()"); p3.wait_for_timeout(600)
        p3.fill("#af-q", "batterie"); p3.wait_for_timeout(400)
        af = p3.evaluate("() => [document.querySelectorAll('.afs li').length, document.querySelectorAll('.afs li:not([hidden])').length, "
                         "document.getElementById('af-cnt').textContent, document.getElementById('af-qn').textContent, "
                         "document.querySelector('.af-fine').textContent, (window.MW_VER || {}).app || '', (window.MW_VER || {}).sim || '']")
        ok(af[0] > 300 and 0 < af[1] < af[0] and af[2] == str(af[0]) and af[3].startswith(str(af[1]) + " sur "),
           "/info/: Suche in «Alle Funktionen» (%d von %d, Kachel %s, %r)" % (af[1], af[0], af[2], af[3]))
        ok(bool(re.match(r"^\d+\.\d+\.\d+$", af[5])) and ("MoveEye %s " % af[5]) in af[4] and bool(re.search(r"simulateur \d+\.\d+\.\d+\.", af[4])),
           "/info/: Fussnote mit der Nummer dieser MoveEye (window.MW_VER) und des Simulators (%r)" % af[4])
        p3.keyboard.press("Escape"); p3.keyboard.press("Escape"); p3.wait_for_timeout(300)
        ok(p3.evaluate("() => document.getElementById('af-ov').hidden"), "/info/: Esc leert die Suche, zweites Esc schliesst")
        p3.evaluate("() => { document.getElementById('f-name').value = 'Test'; document.getElementById('f-msg').value = 'Frage aus dem Test'; }")
        p3.evaluate("() => document.getElementById('ask').requestSubmit()"); p3.wait_for_timeout(2500)
        nt = p3.evaluate("() => document.getElementById('note').textContent")
        ok(nt.startswith("✓"), "/info/: Formular geht als Mitteilung an MoveEye (%r)" % nt)
        ok(not e3, "keine JS-Fehler auf /info/ (PC, 1440 px) %s" % e3[:2])
        br.close()


if __name__ == "__main__":
    main()
