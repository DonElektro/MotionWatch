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
  * optional (--browser): die Seite im echten Browser bei 390 px – verstecken und wieder lesen.

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

    if args.browser:
        print("· Browser (390 px)")
        browser_test(args)

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


if __name__ == "__main__":
    main()
