#!/usr/bin/env python3
"""Test «🔏 Botschaft im Bild» (Steganographie, Teil 639zzzzc + Modul funk/stego.js).

Geprüft wird, dass Python und JavaScript bitgleich rechnen und die versprochenen Eigenschaften halten:
  * fester Test-Vektor: Python und node (funk/stego.js) entschlüsseln denselben Container zum selben Text.
  * Python versteckt → node liest, und umgekehrt (AES-256-GCM und der HMAC-Ersatz).
  * Rundläufe mit mehreren Bildgrössen.
  * die Kapazitäts-Grenze (genau voll geht, ein Zeichen mehr nicht).
  * falscher Schlüssel → nichts; ein geänderter Pixel-Bereich → der Prüf-Tag schlägt fehl → nichts.
  * JPEG rein → PNG raus; das Original bleibt unverändert.
  * nichts Geheimes (Text, Schlüssel) steht im Modul in der Konsole / im Protokoll.
  * die Seite «Handy-Funkgerät» (funk/): Reiter «🔏 Bild», stego.js im Service Worker, MoveEye / Einzeldatei mit
    eingebettetem Modul, Texte in 5 Sprachen, keine Anfrage nach aussen.
  * optional (--browser): das Modul im echten Browser bei 390 px, und auf der Funk-Seite (390 px, dunkel): ein Bild
    wählen, verstecken, herunterladen, wieder lesen, falscher Schlüssel, ein Bild aus Python lesen, 5 Sprachen.

Die Python-Seite wird direkt aus quelle/639zzzzc_bild_stego.py geladen (dieselben Funktionen, die MoveEye
benutzt), damit der Test wirklich die ausgelieferte Rechnung prüft. node bekommt funk/stego.js.

  python3 werkzeuge/stego_test.py            # ohne Browser
  python3 werkzeuge/stego_test.py --browser  # mit Playwright (Chromium), Bildschirmfotos nach --bilder
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PART = os.path.join(REPO, "quelle", "639zzzzc_bild_stego.py")
STEGO_JS = os.path.join(REPO, "funk", "stego.js")
# fester gemeinsamer Vektor (reiner Krypto-Container, ohne Bild): Python und node müssen ihn gleich lesen
VEC_KEY = "MoveEye-Vektor-1"
VEC_TEXT = "Treffen 06:30 am Brunnen. Schlüssel: grün-7. 🏔"
VEC_HEX = ("000102030405060708090a0b0c0d0e0f6465666768696a6b6c6d6e6f78e90763b1ef059fb32e046820d562"
           "15b87d9864e68804b21dc36c8371f3a1ddfccc58fc35921671a6856f08b9ff62bb75d7c0f83c5007ad7cc"
           "b12098c4a16baee220f213b8a31336144f2c90e24ecc4ba28efcf32b27a9e")

FAIL = []


def check(name, cond):
    print(("  ok  " if cond else "FAIL  ") + name)
    if not cond:
        FAIL.append(name)


# ---- die Python-Seite laden (die Funktionen aus dem Teil, mit Platzhaltern für die MoveEye-Globalen) ----------
def load_bild():
    g = {"__name__": "bild_part", "os": os, "json": json, "DE": {}, "TRX": {"fr": {}, "it": {}, "rm": {}},
         "SELFTEST_EXTRA": [],
         "TAUSCH_PAGE": ('<div class="tz-h"><h2>\U0001F4C1 <span data-i18n="File exchange">x</span></h2></div>'
                         '<span style="font-size:28px">\U0001F392</span><span style="flex:1;min-width:0">'
                         '<b data-i18n="Packing lists">x</b></span><script>/*x*/</script>\n</body></html>')}
    exec(compile(open(PART, encoding="utf-8").read(), PART, "exec"), g)
    return g


def png_bytes(w, h, seed=1):
    from PIL import Image
    data = bytearray()
    for i in range(w * h):
        data += bytes([(i * 7 + seed) % 256, (i * 13 + seed) % 256, (i * 29 + seed) % 256, 255])
    buf = io.BytesIO()
    Image.frombytes("RGBA", (w, h), bytes(data)).save(buf, "PNG")
    return buf.getvalue()


# ---- node-Treiber: funk/stego.js, Befehle über stdin (hex rein, hex/text raus) --------------------------------
NODE_DRIVER = r"""
const S = require(process.argv[2]);
const fs = require("fs");
const h2b = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));
const b2h = b => Buffer.from(b).toString("hex");
(async () => {
  const req = JSON.parse(fs.readFileSync(0, "utf8"));
  let out = {};
  if (req.op === "decode_vector") {
    const c = h2b(req.hex), rd = (o, n) => c.subarray(o, o + n);
    out.text = await S._internal.unpack(req.key, rd, 1e9);
  } else if (req.op === "reveal") {
    out.text = await S.reveal(h2b(req.png), req.key);
  } else if (req.op === "hide") {
    out.png = b2h(await S.hide(h2b(req.png), req.text, req.key));
  } else if (req.op === "capacity") {
    out.cap = S.capacity(req.w, req.h);
  }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { process.stdout.write(JSON.stringify({error: String(e && e.message || e)})); });
"""


def node(req):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(NODE_DRIVER)
        drv = f.name
    try:
        p = subprocess.run(["node", drv, STEGO_JS], input=json.dumps(req), capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            return {"error": p.stderr.strip()[:200] or "node failed"}
        return json.loads(p.stdout)
    finally:
        os.unlink(drv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.environ.get("STEGO_BILDER", tempfile.gettempdir()))
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()

    B = load_bild()
    have_node = subprocess.run(["node", "--version"], capture_output=True).returncode == 0
    if not have_node:
        print("node fehlt – die Python↔JS-Prüfungen werden übersprungen")

    print("· fester Vektor (Python ↔ node)")
    rd = lambda o, n: bytes.fromhex(VEC_HEX)[o:o + n]
    check("Python entschlüsselt den Vektor", B["_bild_unpack"](VEC_KEY, rd, 10 ** 9) == VEC_TEXT)
    if have_node:
        r = node({"op": "decode_vector", "hex": VEC_HEX, "key": VEC_KEY})
        check("node entschlüsselt den Vektor gleich", r.get("text") == VEC_TEXT)

    print("· Rundläufe mit mehreren Grössen (Python ↔ node, AES und HMAC-Ersatz)")
    for (w, h) in [(16, 16), (31, 29), (64, 48), (200, 150), (320, 240)]:
        base = png_bytes(w, h)
        cap = B["bild_capacity"](w, h)
        full = "Grösse %dx%d – Grüße 😀 an den Besitzer. Punkt." % (w, h)
        txt = ""                                             # auf die Kapazität dieses (kleinen) Bildes kürzen
        for ch in full:
            if len((txt + ch).encode("utf-8")) > cap:
                break
            txt += ch
        png = B["bild_hide_image"](base, txt, "pw-size")
        check("Python Rundlauf %dx%d" % (w, h), B["bild_reveal_image"](png, "pw-size") == txt)
        check("Python Ausgabe ist PNG %dx%d" % (w, h), png[:8] == b"\x89PNG\r\n\x1a\n")
        if have_node:
            r = node({"op": "reveal", "png": png.hex(), "key": "pw-size"})
            check("node liest Python-Bild %dx%d" % (w, h), r.get("text") == txt)
            r2 = node({"op": "hide", "png": base.hex(), "text": txt, "key": "pw-size"})
            check("Python liest node-Bild %dx%d" % (w, h), not r2.get("error") and B["bild_reveal_image"](bytes.fromhex(r2["png"]), "pw-size") == txt)
    # HMAC-Ersatz: Python erzwingt den Fallback, node (mit AES) liest trotzdem (es probiert beide Wege)
    base = png_bytes(80, 60)
    ph = B["bild_hide_image"](base, "Fallback ohne AES ✅", "k-hmac", force_hmac=True)
    check("Python HMAC-Fallback Rundlauf", B["bild_reveal_image"](ph, "k-hmac") == "Fallback ohne AES ✅")
    if have_node:
        r = node({"op": "reveal", "png": ph.hex(), "key": "k-hmac"})
        check("node liest Python-HMAC-Bild", r.get("text") == "Fallback ohne AES ✅")

    print("· Kapazitäts-Grenze")
    w, h = 64, 48
    cap = B["bild_capacity"](w, h)
    base = png_bytes(w, h)
    full = "A" * cap
    check("genau voll geht", B["bild_reveal_image"](B["bild_hide_image"](base, full, "k"), "k") == full)
    over = "A" * (cap + 1)
    try:
        B["bild_hide_image"](base, over, "k")
        check("ein Zeichen zu viel wird abgelehnt", False)
    except B["BildCapacity"] as e:
        check("ein Zeichen zu viel wird abgelehnt (Kapazität genannt)", e.capacity == cap and e.need == cap + 1)
    if have_node:
        check("node meldet dieselbe Kapazität", node({"op": "capacity", "w": w, "h": h}).get("cap") == cap)

    print("· falscher Schlüssel und ein geänderter Bereich")
    png = B["bild_hide_image"](png_bytes(120, 90), "Nur mit dem richtigen Schlüssel.", "richtig")
    check("falscher Schlüssel → nichts", B["bild_reveal_image"](png, "falsch") is None)
    check("richtiger Schlüssel → Text", B["bild_reveal_image"](png, "richtig") == "Nur mit dem richtigen Schlüssel.")
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    px = bytearray(im.tobytes())
    for i in range(0, 4000, 1):                              # einen Bereich verändern (die untersten Bits kippen)
        if i % 4 != 3:
            px[i] ^= 1
    b2 = io.BytesIO(); Image.frombytes("RGBA", im.size, bytes(px)).save(b2, "PNG")
    check("geänderter Bereich → Prüf-Tag schlägt fehl → nichts", B["bild_reveal_image"](b2.getvalue(), "richtig") is None)

    print("· JPEG rein → PNG raus; das Original bleibt unverändert")
    from PIL import Image as Im2
    jb = io.BytesIO(); Im2.new("RGB", (160, 120), (120, 60, 30)).save(jb, "JPEG", quality=90)
    jpeg = jb.getvalue()
    before = bytes(jpeg)                                     # Kopie zum Vergleich
    out = B["bild_hide_image"](jpeg, "JPEG wird dekodiert, Ausgabe ist PNG.", "jk")
    check("JPEG-Eingabe → PNG-Ausgabe", out[:8] == b"\x89PNG\r\n\x1a\n")
    check("die JPEG-Eingabe wurde nicht verändert", jpeg == before)
    check("JPEG-Rundlauf (Text zurück)", B["bild_reveal_image"](out, "jk") == "JPEG wird dekodiert, Ausgabe ist PNG.")
    # das «Original bleibt unverändert»: verstecken gibt neue Bytes zurück, die Eingabe ist unberührt
    src = png_bytes(100, 100); src_copy = bytes(src)
    _ = B["bild_hide_image"](src, "x", "k")
    check("das Original-Bild bleibt unverändert", src == src_copy)

    print("· nichts Geheimes im Protokoll")
    js = open(STEGO_JS, encoding="utf-8").read()
    part = open(PART, encoding="utf-8").read()
    check("funk/stego.js schreibt nie in die Konsole", "console.log" not in js and "console.error" not in js)
    # die Oberfläche (STEGO_UI) protokolliert weder Text noch Schlüssel
    ui = re.search(r'STEGO_UI = r"""(.*?)"""', part, re.S)
    check("die Oberfläche protokolliert nicht", ui and "console.log" not in ui.group(1))
    check("der Server bekommt Text/Schlüssel nie (kein /api für stego)", "/api/stego" not in part and "action\": \"hide" not in part)
    # funk/stego.js und das eingebettete Modul laufen nicht auseinander
    emb = re.search(r'STEGO_JS = r"""(.*?)"""', part, re.S)
    check("funk/stego.js == eingebettetes Modul", emb and emb.group(1) == js)

    funk_static(js)

    if args.browser:
        print("· Browser (390 px)")
        browser_test(args)
        funk_browser(args, B)

    print()
    if FAIL:
        print("FEHLER: %d Prüfung(en) rot: %s" % (len(FAIL), " · ".join(FAIL)))
        sys.exit(1)
    print("alle Prüfungen grün")


def browser_test(args):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        check("Playwright vorhanden", False)
        return
    os.makedirs(args.bilder, exist_ok=True)
    js = open(STEGO_JS, encoding="utf-8").read()
    # eine eigenständige Seite mit dem echten Modul: ein Bild wählen, verstecken, wieder lesen – wie offline auf dem Funkgerät
    harness = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
               "<body style='background:#0b0f14;color:#e6edf3;font:15px system-ui;margin:0;padding:12px'>"
               "<h2 id=t>🔏 Botschaft im Bild</h2><canvas id=c width=200 height=150 hidden></canvas>"
               "<div id=r>…</div><script>" + js + "</script><script>"
               "(async()=>{const cv=document.getElementById('c');const x=cv.getContext('2d');"
               "const im=x.createImageData(200,150);for(let i=0;i<im.data.length;i++)im.data[i]=i%4===3?255:(i*37)%256;"
               "x.putImageData(im,0,0);const blob=await new Promise(r=>cv.toBlob(r,'image/png'));"
               "const png=new Uint8Array(await blob.arrayBuffer());const msg='Browser 390px: Grüße 😀 Besitzer';"
               "const out=await MWStego.hide(png,msg,'bpw');const back=await MWStego.reveal(out,'bpw');"
               "document.getElementById('r').textContent=(back===msg?'OK ':'FAIL ')+JSON.stringify(back);"
               "})();</script>")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(harness)
        page_file = f.name
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            pg = br.new_page(viewport={"width": 390, "height": 740}, color_scheme="dark")
            pg.goto("file://" + page_file)
            pg.wait_for_function("document.getElementById('r').textContent.startsWith('OK')||document.getElementById('r').textContent.startsWith('FAIL')", timeout=20000)
            res = pg.inner_text("#r")
            pg.screenshot(path=os.path.join(args.bilder, "stego_390_modul.png"))
            check("Browser (390 px): verstecken und wieder lesen", res.startswith("OK"))
            br.close()
    finally:
        os.unlink(page_file)


# ---- die Seite «Handy-Funkgerät» (funk/, Teil 639zzzf): Reiter «🔏 Bild» -------------------------------------------
FUNK = os.path.join(REPO, "funk")
TITEL_BILD = {"de": "Botschaft im Bild", "en": "Message in a picture", "fr": "Message dans une image", "it": "Messaggio nell’immagine",
              "rm": "Messadi en ina maletg"}


def funk_page_fn(js):
    """funk_page() aus 639zzzf (mit Platzhaltern für die MoveEye-Globalen) - die drei Fassungen mw / file / pwa"""
    import ast
    src = open(os.path.join(REPO, "quelle", "639zzzf_funk.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    page = next(st.value.value for st in tree.body if isinstance(st, ast.Assign) and any(getattr(t, "id", "") == "FUNK_PAGE" for t in st.targets))
    fn = next(st for st in tree.body if isinstance(st, ast.FunctionDef) and st.name == "funk_page")
    g = {"FUNK_PAGE": page, "STEGO_JS": js, "json": json, "CFG": {"lang": "de"}, "norm_lang": lambda x: x or "de"}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "funk_page", "exec"), g)
    return g["funk_page"], page


def funk_static(js):
    print("· Seite «Handy-Funkgerät»: Reiter «🔏 Bild»")
    fp, page = funk_page_fn(js)
    idx = open(os.path.join(FUNK, "index.html"), encoding="utf-8").read()
    sw = open(os.path.join(FUNK, "sw.js"), encoding="utf-8").read()
    check("funk/index.html hat den Reiter «🔏 Bild» und lädt stego.js daneben",
          'id="imgBtn"' in idx and 'id="shImg"' in idx and '<script src="stego.js"></script>' in idx and idx == page)
    check("der Service Worker hält stego.js (ohne Netz)", '"stego.js"' in sw)
    check("funk/stego.js == STEGO_JS (aus funk_pwa.py, --pruefen)", open(os.path.join(FUNK, "stego.js"), encoding="utf-8").read() == js)
    for v in ("mw", "file"):
        p = fp(v, "de", 5001)
        check("Fassung «%s»: Modul eingebettet, keine zweite Datei nötig" % v, "root.MWStego = mod" in p and 'src="stego.js"' not in p)
    check("Fassung «pwa»: stego.js neben der Seite", '<script src="stego.js"></script>' in fp("pwa", "de"))
    ui = idx[idx.index("/*STEGO-UI-START*/"):idx.index("/*STEGO-UI-END*/")]
    check("die Oberfläche: kein fetch / innerHTML / console, Schlüssel nur mit «merken»",
          not re.search(r"fetch\s*\(|innerHTML|console\.|eval\(", ui) and "store.set('imgkey',k)" in ui and "store.del('imgkey')" in ui)
    r = subprocess.run(["node", "-e", "const s=require('fs').readFileSync(process.argv[1],'utf8');const i=s.indexOf('const TXT='),j=s.indexOf('};',i);"
                        "const TXT=eval('('+s.slice(i+10,j+1)+')');const ks=Object.keys(TXT.de).filter(k=>k.startsWith('img'));"
                        "console.log(JSON.stringify({n:ks.length,miss:Object.keys(TXT).map(l=>ks.filter(k=>!TXT[l][k]).map(k=>l+':'+k)).flat()}))",
                        os.path.join(FUNK, "index.html")], capture_output=True, text=True, timeout=60)
    t = json.loads(r.stdout or "{}")
    check("Texte des Reiters in 5 Sprachen (%s Schlüssel)" % t.get("n"), t.get("n", 0) >= 15 and not t.get("miss"))


def funk_browser(args, B):
    import http.server
    import threading
    from playwright.sync_api import sync_playwright
    print("· Browser: Seite «Handy-Funkgerät» (funk/, 390 px, dunkel)")
    tmp = tempfile.mkdtemp()
    src_png = os.path.join(tmp, "zelt.png")
    open(src_png, "wb").write(png_bytes(240, 180, seed=5))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lambda *a: http.server.SimpleHTTPRequestHandler(*a, directory=FUNK))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/" % srv.server_address[1]
    msg = "Treffpunkt 06:30 am grünen Zelt – Schlüssel bitte nicht verlieren 😀"
    shot = lambda pg, n: pg.screenshot(path=os.path.join(args.bilder, n), full_page=False)
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-proxy-server"])

        def ctx_page(lang):
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 color_scheme="dark", locale="de-CH", accept_downloads=True)
            ctx.add_init_script("try{localStorage.setItem('morsefunk.lang',JSON.stringify('%s'))}catch(e){}" % lang)
            pg = ctx.new_page()
            errs, fremd = [], []
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.on("request", lambda r: fremd.append(r.url) if not r.url.startswith(base) and not r.url.startswith(("blob:", "data:")) else None)
            pg.goto(base, wait_until="load")
            return ctx, pg, errs, fremd

        ctx, pg, errs, fremd = ctx_page("de")
        shot(pg, "funk_390_start.png")
        pg.locator("#imgBtn").click()
        pg.wait_for_selector("#shImg.open", timeout=5000)
        pg.set_input_files("#imgIn", src_png)
        pg.wait_for_function("() => /passt noch ca\\. \\d+ Zeichen/.test(document.getElementById('imgCap').textContent)", timeout=10000)
        pg.fill("#imgTxt", msg)
        pg.fill("#imgKey", "grün-7")
        cap_txt = pg.inner_text("#imgCap")
        shot(pg, "funk_390_bild_verstecken.png")
        pg.locator("#imgGo").click()
        pg.wait_for_selector("#imgDl:not([hidden])", timeout=60000)
        pg.locator("#imgDl").scroll_into_view_if_needed()
        shot(pg, "funk_390_bild_versteckt.png")
        check("verstecken auf der Seite: «%s», neue Datei «zelt_b.png»" % cap_txt,
              pg.get_attribute("#imgDl", "download") == "zelt_b.png" and "zelt_b.png" in pg.inner_text("#imgOut"))
        with pg.expect_download() as dl:
            pg.locator("#imgDl").click()
        out = os.path.join(tmp, "zelt_b.png")
        dl.value.save_as(out)
        made = open(out, "rb").read()
        check("Herunterladen: PNG, Python liest die Botschaft der Seite", made[:8] == b"\x89PNG\r\n\x1a\n" and B["bild_reveal_image"](made, "grün-7") == msg)
        check("das gewählte Original bleibt unverändert", open(src_png, "rb").read() == png_bytes(240, 180, seed=5))
        sw_ = pg.evaluate("() => document.documentElement.scrollWidth")
        check("390 px: kein waagrechtes Scrollen (%d px)" % sw_, sw_ <= 391)
        # lesen: falscher Schlüssel, richtiger Schlüssel, ein Bild aus Python (JPEG → PNG)
        pg.locator("#imgMRead").click()
        pg.set_input_files("#imgIn", out)
        pg.fill("#imgKey", "falsch")
        pg.locator("#imgGo").click()
        pg.wait_for_function("() => document.getElementById('imgOut').textContent.includes('keine Botschaft gefunden oder falscher Schlüssel')", timeout=60000)
        check("falscher Schlüssel → «keine Botschaft gefunden oder falscher Schlüssel», kein Text", pg.locator("#imgRes").is_hidden())
        pg.fill("#imgKey", "grün-7")
        pg.locator("#imgGo").click()
        pg.wait_for_selector("#imgRes:not([hidden])", timeout=60000)
        shot(pg, "funk_390_bild_gelesen.png")
        check("lesen auf der Seite: der Text erscheint", pg.inner_text("#imgRes") == msg)
        from PIL import Image
        jb = io.BytesIO(); Image.new("RGB", (200, 150), (40, 90, 140)).save(jb, "JPEG", quality=88)
        pyimg = os.path.join(tmp, "python_b.png")
        open(pyimg, "wb").write(B["bild_hide_image"](jb.getvalue(), "Aus Python für das Handy ✓", "py-key"))
        pg.set_input_files("#imgIn", pyimg)
        pg.fill("#imgKey", "py-key")
        pg.locator("#imgGo").click()
        pg.wait_for_function("() => document.getElementById('imgRes').textContent === 'Aus Python für das Handy ✓'", timeout=60000)
        check("die Seite liest ein Bild aus Python (JPEG → PNG)", True)
        hist = pg.evaluate("() => { try { return localStorage.getItem('morsefunk.hist') || '' } catch (e) { return '' } }")
        keys = pg.evaluate("() => Object.keys(localStorage).join(',')")
        check("Text nie im Verlauf / Speicher, Schlüssel ohne «merken» nicht gespeichert",
              msg not in hist and "imgkey" not in keys and "grün-7" not in pg.evaluate("() => JSON.stringify(localStorage)"))
        check("keine Anfrage nach aussen, keine JavaScript-Fehler", not fremd and not errs)
        if fremd or errs:
            print("      ", fremd[:3], errs[:3])
        ctx.close()
        for lang in ("en", "fr", "it", "rm", "de"):
            ctx, pg, errs, fremd = ctx_page(lang)
            pg.locator("#imgBtn").click()
            pg.wait_for_selector("#shImg.open", timeout=5000)
            pg.wait_for_timeout(250)
            tt = pg.inner_text('#shImg [data-t="imgTitle"]')
            sw_ = pg.evaluate("() => document.documentElement.scrollWidth")
            raus = pg.evaluate("""() => Array.from(document.querySelectorAll('#shImg button, #shImg a, #shImg label, .bottom button'))
              .filter(e => e.offsetParent && (e.getBoundingClientRect().right > innerWidth + 1 || e.scrollWidth > e.clientWidth + 2)).map(e => e.id || e.textContent.slice(0, 20))""")
            if lang in ("fr", "rm"):
                shot(pg, "funk_390_bild_%s.png" % lang)
            check("Reiter «🔏 Bild» %s: «%s», 390 px passt" % (lang, tt), tt == TITEL_BILD[lang] and sw_ <= 391 and not raus and not errs)
            ctx.close()
        br.close()
    srv.shutdown()

if __name__ == "__main__":
    main()
