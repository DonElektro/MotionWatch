#!/usr/bin/env python3
"""Test für sim_web_speicher.py (Grafikspeicher iPhone / iPad, Besitzer 23.11.2026: iPad Pro 12.9" «WebGL context lost»):
  1. jede Godot-Stelle wird genau einmal ersetzt, zweiter Lauf ändert nichts, fehlt eine Stelle -> Abbruch
  2. Node: window.mwPixelRatio - PC unverändert, iPhone / iPad (iPadOS meldet sich als «MacIntel» mit Touch) höchstens 1.5 und
     3.2 Mio. Bildpunkte, ?lite=1 überall 1.0; nie unter 1 (ausser das Gerät selbst)
  3. --browser (Chromium, Playwright): eine Seite mit dem Block aus index.html, einer WebGL-Leinwand und genau dem gepatchten
     Godot-Listener; WEBGL_lose_context -> Meldung in der Seite statt alert(), 5 Sprachen, «Im Spar-Modus neu laden» lädt mit
     lite=1 (andere Angaben der Adresse bleiben), mit lite=1 nur «Neu laden»; Bilder mit --bilder ORDNER (390 px, DPR 2)
  4. --ordner EXPORT (fertiger Godot-Web-Export oder entpacktes sim-web.zip): echtes index.js; als iPad (Safari-Kennung,
     Touch) ist die Leinwand höchstens 1.5-fach, und ein Verlust des WebGL-Kontexts zeigt die Meldung, kein alert()

    python3 werkzeuge/sim_web_speicher_test.py [--browser] [--bilder ORDNER] [--ordner EXPORT]   # Ende: «… OK» (Exit 0)
WebKit hat Playwright hier nicht - Chromium mit der Kennung eines iPad ersetzt kein echtes iPad.
"""
import argparse
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_web_speicher as sp  # noqa: E402

FEHLER = []
IPAD_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 "
           "Safari/605.1.15")


def ok(bed, was):
    print(("  ok: " if bed else "  FEHLER: ") + was)
    if not bed:
        FEHLER.append(was)


def wirft(fn, *a):
    try:
        fn(*a)
    except SystemExit:
        return True
    return False


def teil1():
    print("1. Ersetzen")
    js = "var x={" + sp.JS_ERSATZ[0][0] + "};function f(canvas){" + sp.JS_ERSATZ[1][0] + ";}"
    j1 = sp.patch_js(js)
    ok(j1 != js and sp.MARKE_JS in j1 and all(n in j1 for _, n in sp.JS_ERSATZ), "index.js gepatcht (2 Stellen)")
    ok("alert(" in j1 and j1.index("mwContextLost") < j1.index("alert("), "alert nur noch als Rückfall nach mwContextLost")
    ok(sp.patch_js(j1) == j1, "zweiter Lauf ändert nichts")
    for i, (alt, _) in enumerate(sp.JS_ERSATZ):
        ok(wirft(sp.patch_js, js.replace(alt, "")), "Stelle %d fehlt -> Abbruch" % i)
    html = "<body><canvas id=canvas></canvas>" + sp.SCRIPT_TAG + "<script>x</script></body>"
    h1 = sp.patch_html(html)
    ok(sp.MARKE_HTML in h1 and h1.count(sp.SCRIPT_TAG) == 1 and h1.index("mw-gpu") < h1.index(sp.SCRIPT_TAG),
       "index.html: Block vor index.js")
    ok(sp.patch_html(h1) == h1, "index.html: zweiter Lauf ändert nichts")
    ok(wirft(sp.patch_html, html.replace(sp.SCRIPT_TAG, "")), "index.html ohne index.js -> Abbruch")
    ok(all(set(t) == set(sp.TEXTE["de"]) for t in sp.TEXTE.values()) and sorted(sp.TEXTE) == ["de", "en", "fr", "it", "rm"],
       "Texte: 5 Sprachen, alle Schlüssel")
    ok(sp.TEXTE["de"]["t"] == "Grafikspeicher voll – im Spar-Modus neu laden?" and "ß" not in json.dumps(sp.TEXTE, ensure_ascii=False),
       "deutscher Titel, «ss» statt «ß»")
    return j1


def script_aus_block():
    b = sp._block()
    return b[b.index("<script>") + 8:b.index("</script>")]


def teil2():
    node = shutil.which("node")
    print("2. Node" + ("" if node else " (nicht vorhanden - übersprungen)"))
    if not node:
        return
    fall = [  # (Name, userAgent, platform, maxTouchPoints, Suche, innerW, innerH, dpr, erwartet höchstens, erwartet mindestens)
        ("PC 2x", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130", "Win32", 0, "", 1920, 1080, 2.0, 2.0, 2.0),
        ("Mac 2x (ohne Touch)", IPAD_UA, "MacIntel", 0, "", 1512, 945, 2.0, 2.0, 2.0),
        ("iPad Pro 12.9 quer", IPAD_UA, "MacIntel", 5, "", 1366, 1024, 2.0, 1.5, 1.27),
        ("iPad Pro 12.9 hoch", IPAD_UA, "MacIntel", 5, "?grossvater=1", 1024, 1366, 2.0, 1.5, 1.27),
        ("iPhone 3x", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) Safari", "iPhone", 5, "", 430, 932, 3.0, 1.5, 1.5),
        ("iPad lite", IPAD_UA, "MacIntel", 5, "?lite=1", 1366, 1024, 2.0, 1.0, 1.0),
        ("PC lite", "Mozilla/5.0 (X11; Linux x86_64) Chrome/130", "Linux x86_64", 0, "?roboter=1&lite=1", 2560, 1440, 1.0, 1.0, 1.0),
        ("altes Gerät 0.75", "x", "x", 0, "?lite=1", 800, 600, 0.75, 0.75, 0.75),
    ]
    prog = "const S = " + json.dumps(script_aus_block()) + ";\nconst F = " + json.dumps(fall) + ";\nconst out = [];\n" + r"""
for (const [n, ua, pf, tp, search, w, h, dpr] of F) {
	const win = { innerWidth: w, innerHeight: h, devicePixelRatio: dpr };
	const nav = { userAgent: ua, platform: pf, maxTouchPoints: tp, language: 'de-CH' };
	const loc = { search: search, pathname: '/sim/index.html', hash: '' };
	new Function('window', 'navigator', 'location', 'document', 'console', S)(win, nav, loc, {}, { warn() {} });
	const r = win.mwPixelRatio(dpr);
	out.push([n, r, win.mwGpu.ios, win.mwGpu.lite, w * h * r * r]);
}
console.log(JSON.stringify(out));
"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.js")
        with open(p, "w", encoding="utf-8") as f:
            f.write(prog)
        r = subprocess.run([node, p], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        ok(False, "Node: " + r.stderr[-300:])
        return
    res = {x[0]: x for x in json.loads(r.stdout)}
    for n, *_, hi, lo in fall:
        x = res[n]
        ok(lo - 0.01 <= x[1] <= hi + 0.001, "%s: Pixeldichte %.2f (erwartet %.2f…%.2f), %.1f Mio. Bildpunkte, iOS %s"
           % (n, x[1], lo, hi, x[4] / 1e6, x[2]))
    ok(res["iPad Pro 12.9 quer"][4] <= 3.21e6, "iPad Pro: Leinwand höchstens 3.2 Mio. Bildpunkte (vorher 5.6)")


def _server(ordner):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ordner)
    h.log_message = lambda *a: None
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def teil3(j1, bilder):
    print("3. Chromium: Meldung statt alert()")
    from playwright.sync_api import sync_playwright
    d = tempfile.mkdtemp(prefix="mw_gpu_")
    lis = j1[j1.index("GodotEventListeners.add("):j1.index("},false)") + 8]
    page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<style>html,body{margin:0;background:#000}#canvas{display:block;width:100vw;height:100vh}</style></head><body>"
            "<canvas id='canvas'></canvas>" + sp.patch_html(sp.SCRIPT_TAG) + "<script>\n"
            "const GodotEventListeners = { add: (t, e, f, c) => t.addEventListener(e, f, c) };\n"
            "const canvas = document.getElementById('canvas');\nwindow.gl = canvas.getContext('webgl2') || canvas.getContext('webgl');\n"
            + lis + ";\n</script></body></html>")
    with open(os.path.join(d, "index.js"), "w") as f:
        f.write("window.indexJs = 1;")
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    s = _server(d)
    url = "http://127.0.0.1:%d/index.html" % s.server_address[1]
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
            for name, such, lang, lite in [("de", "?roboter=1", "de-CH", False), ("fr", "?sprache=fr", "de-CH", False),
                                           ("it", "", "it-IT", False), ("rm", "?sprache=rm", "en-US", False),
                                           ("en", "", "en-GB", False), ("de-lite", "?lite=1&grossvater=1", "de-CH", True)]:
                ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                    locale=lang, user_agent=IPAD_UA)
                pg = ctx.new_page()
                alerts = []
                pg.on("dialog", lambda dlg: (alerts.append(dlg.message), dlg.dismiss()))
                pg.goto(url + such)
                ok(pg.evaluate("() => !!window.gl && document.getElementById('mw-gpu').offsetParent === null"),
                   "%s: WebGL da, keine Meldung vor dem Verlust" % name)
                pg.evaluate("() => window.gl.getExtension('WEBGL_lose_context').loseContext()")
                pg.wait_for_function("() => document.getElementById('mw-gpu').classList.contains('on')", timeout=10000)
                tx = sp.TEXTE[name.split("-")[0]]
                got = pg.evaluate("() => ({t: document.getElementById('mw-gpu-t').textContent, p: document.getElementById('mw-gpu-p').textContent,"
                                  " a: document.getElementById('mw-gpu-a').textContent, b: document.getElementById('mw-gpu-b').offsetParent !== null,"
                                  " lost: window.mwGpu.lost, w: document.documentElement.scrollWidth})")
                ok(not alerts, "%s: kein alert() (%s)" % (name, alerts))
                ok(got["t"] == tx["t"] and got["lost"] == 1, "%s: Titel «%s»" % (name, got["t"]))
                ok(got["p"] == (tx["pl"] if lite else tx["p"]) and got["a"] == (tx["bl"] if lite else tx["a"])
                   and got["b"] == (not lite), "%s: Text und Knöpfe passen (%s)" % (name, got["a"]))
                ok(got["w"] <= 390, "%s: nichts ragt seitlich hinaus (%d px)" % (name, got["w"]))
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, "gpu_meldung_%s.png" % name))
                with pg.expect_navigation():
                    pg.click("#mw-gpu-a")
                q = pg.evaluate("() => location.search")
                ok("lite=1" in q and (such.replace("?", "").split("&")[0] in q), "%s: Knopf lädt neu mit lite=1 (%s)" % (name, q))
                if not lite:
                    pg.goto(url + such + ("&" if such else "?") + "lite=1")
                    pg.evaluate("() => window.gl.getExtension('WEBGL_lose_context').loseContext()")
                    pg.wait_for_function("() => document.getElementById('mw-gpu').classList.contains('on')", timeout=10000)
                    with pg.expect_navigation():
                        pg.click("#mw-gpu-a")
                    ok(pg.evaluate("() => (location.search.match(/lite=/g) || []).length") == 1, "%s: lite=1 nicht doppelt" % name)
                ctx.close()
            b.close()
    finally:
        s.shutdown()
        shutil.rmtree(d, ignore_errors=True)


def teil4(ordner, bilder):
    print("4. echter Export: " + ordner)
    from playwright.sync_api import sync_playwright
    js = open(os.path.join(ordner, "index.js"), encoding="utf-8").read()
    html = open(os.path.join(ordner, "index.html"), encoding="utf-8").read()
    ok(sp.MARKE_JS in js and sp.MARKE_HTML in html, "Export ist gepatcht (sim_web_paket.py packen / sim_web_speicher.py ORDNER)")
    s = _server(ordner)
    url = "http://127.0.0.1:%d/index.html" % s.server_address[1]
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
            for name, such, vw, vh, maxdpr in [("iPad Pro quer", "?test=1", 1366, 1024, 1.5), ("iPad lite", "?test=1&lite=1", 1366, 1024, 1.0)]:
                ctx = b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                    user_agent=IPAD_UA, locale="de-CH")
                pg = ctx.new_page()
                pg.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});")
                alerts, logs = [], []
                pg.on("dialog", lambda dlg: (alerts.append(dlg.message), dlg.dismiss()))
                pg.on("console", lambda m: logs.append(m.text))
                pg.set_default_timeout(300000)
                pg.goto(url + such, wait_until="domcontentloaded")
                pg.wait_for_function("() => typeof window.mwControl === 'function'", timeout=300000)
                pg.wait_for_timeout(15000)
                c = pg.evaluate("() => { const c = document.getElementById('canvas'); return {w: c.width, h: c.height, iw: innerWidth, ih: innerHeight, gpu: window.mwGpu}; }")
                r = c["w"] / max(1, c["iw"])
                ok(r <= maxdpr + 0.01 and c["gpu"]["ios"], "%s: Leinwand %d × %d (Faktor %.2f, höchstens %.1f)" % (name, c["w"], c["h"], r, maxdpr))
                pg.evaluate("(s) => window.mwControl(s)", json.dumps({"action": "webdiag"}))
                pg.wait_for_timeout(1000)
                dg = json.loads(pg.evaluate("() => window.mwLast"))
                px = dg["window"][0] * dg["window"][1] * dg["scale3d"] ** 2
                lim = 1.0e6 if "lite" in such else 1.8e6
                ok(dg.get("spar") == ("lite" if "lite" in such else "ios") and dg.get("msaa") == 0 and px <= lim * 1.02,
                   "%s: Spiel im Spar-Modus «%s», MSAA %s, 3D %.2f = %.1f Mio. Bildpunkte, Schatten %s"
                   % (name, dg.get("spar"), dg.get("msaa"), dg["scale3d"], px / 1e6, dg.get("shadow")))
                if "lite" in such:
                    ok(dg.get("shadow") is False, "%s: ohne Sonnenschatten" % name)
                print("   ", [x for x in logs if "Spar-Modus" in x or "Fenster" in x][:3])
                pg.evaluate("() => { const gl = document.getElementById('canvas').getContext('webgl2'); gl.getExtension('WEBGL_lose_context').loseContext(); }")
                pg.wait_for_function("() => document.getElementById('mw-gpu').classList.contains('on')", timeout=20000)
                ok(not alerts, "%s: Kontext verloren -> Meldung, kein alert() (%s)" % (name, alerts))
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, "gpu_export_%s.png" % name.replace(" ", "_")))
                ctx.close()
            b.close()
    finally:
        s.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ordner", default="")
    a = ap.parse_args()
    j1 = teil1()
    teil2()
    if a.browser or a.ordner:
        if a.bilder:
            os.makedirs(a.bilder, exist_ok=True)
        teil3(j1, a.bilder)
    if a.ordner:
        teil4(os.path.abspath(a.ordner), a.bilder)
    print("Sim-Web-Speicher-Test " + ("OK" if not FEHLER else "FEHLER: %d" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
