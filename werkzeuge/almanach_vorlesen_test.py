#!/usr/bin/env python3
"""Test «🔊 im Almanach mit der Piper-Stimme» (Teil 639zzzzv_vorlesen_almanach) – ohne echte Stimme (Piper wird durch einen
kurzen Sinuston ersetzt, wie in vorlesen_test.py):

  A) Flask-Testclient: /almanach/vorlesen (Sätze eines Artikels, Piper bereit?) und /almanach/vorlesen/ton (WAV) auch für Gäste
     ohne Anmeldung; ohne Piper: piper=false + Hinweis, Ton 503 mit «fallback»; Stimme mit Fehler: 503; falscher Artikel: 400;
     der Ton kommt nur von Piper (nie die alte Stimme), zweimal derselbe Satz = einmal gerechnet.
  B) --browser (390 px Handy): 🔊 holt den Ton über /almanach/vorlesen/ton, Leiste unten mit ⏸ und ⏹ Stopp, Stopp hält an;
     ohne Piper liest die Browser-Stimme mit Hinweis; antwortet Piper nicht, liest die Browser-Stimme weiter; keine JS-Fehler.
     --bilder ORDNER: Bildschirmfotos.

  python3 werkzeuge/almanach_vorlesen_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import os
import re
import sys
import tempfile
import threading
import time

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


SYNTH = r'''
def _avt_synth(text, lang, speed, out):
    import wave as _w, math as _m, struct as _s
    n = int(22050 * min(0.5, 0.15 + 0.003 * len(text)))
    with _w.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        w.writeframes(b"".join(_s.pack("<h", int(6000 * _m.sin(k * 2 * _m.pi * 440 / 22050))) for k in range(n)))
    _AVT_SAID.append((text, lang))
    return True, ""
def _avt_bad(text, lang, speed, out):
    _AVT_SAID.append(("BAD", lang))
    return False, "Piper stopped"
_AVT_SAID = []
'''


def teil_a(datei):
    print("A) Adressen", flush=True)
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_almvl_home_")
    ns = {"__name__": "mw_almanach_vorlesen_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    exec(SYNTH, ns)
    CFG, VL = ns["CFG"], ns["VL"]
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de")
    ns["piper_ready"] = lambda lang=None: False             # this machine: no Piper voice
    old = []
    ns["_tts_make_639zzb"] = lambda *a, **k: (old.append(a), (True, ""))[1]
    assert ns["web_pw_set"]("Admin-Pass-123")[0]
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)               # a guest: no login

    VL["synth"] = None
    r = c.get("/almanach/vorlesen?i=0&lang=de")
    j = r.get_json() or {}
    ok(r.status_code == 200 and j.get("ok") and j.get("piper") is False and "Browser" in (j.get("hint") or ""), f"ohne Piper: piper=false + Hinweis ({r.status_code} {j.get('hint')})")
    ok(j.get("n") and j["n"][0] == sum(len(p) for p in j["ch"][0]["p"]) and j["ch"][0]["p"][0][0] == ns["ALMANAC"][0][3][0][0], "Sätze: Titel zuerst, n passt")
    ok(all(not x.startswith("- ") for p in j["ch"][0]["p"] for x in p), "Listenpunkte ohne «- »")
    ok(j.get("tx", {}).get("My AI voice") == "Meine KI-Stimme", "Texte auf Deutsch dabei")
    r = c.get("/almanach/vorlesen/ton?i=0&s=0&lang=de")
    ok(r.status_code == 503 and (r.get_json() or {}).get("fallback") is True, f"ohne Piper: Ton 503 + fallback ({r.status_code})")
    ok(not old, "nie die alte Stimme (pico2wave / espeak-ng) – Rückfall ist die Browser-Stimme")
    r = c.get("/almanach/vorlesen")
    ok(r.status_code == 200 and (r.get_json() or {}).get("tx"), "ohne i: nur die Texte")
    ok(c.get("/almanach/vorlesen?i=99999").status_code == 400 and c.get("/almanach/vorlesen?i=x").status_code == 400, "falscher Artikel: 400")

    VL["synth"] = ns["_avt_synth"]
    j = c.get("/almanach/vorlesen?i=0&lang=de").get_json() or {}
    ok(j.get("piper") is True and not j.get("hint"), "mit Stimme: piper=true")
    r = c.get("/almanach/vorlesen/ton?i=0&s=1&lang=de")
    ok(r.status_code == 200 and r.mimetype == "audio/wav" and r.data[:4] == b"RIFF", f"Ton eines Satzes als WAV ({r.status_code})")
    said = ns["_AVT_SAID"]
    flat = [x for p in j["ch"][0]["p"] for x in p]
    ok(said and said[0] == (flat[1], "de"), f"richtiger Satz, Sprache der Seite ({said[:1]})")
    time.sleep(1.0)                                        # the worker computes the next sentences
    n0 = len(said)
    r = c.get("/almanach/vorlesen/ton?i=0&s=1&lang=de")
    ok(r.status_code == 200 and len(said) <= n0 + 2 and ("BAD", "de") not in said, "derselbe Satz kommt aus dem Zwischenspeicher")
    ok(n0 >= 2, f"die nächsten Sätze werden vorausgerechnet ({n0})")
    ok(c.get("/almanach/vorlesen/ton?i=0&s=99999").status_code == 503, "unbekannter Satz: kein Ton")
    VL["synth"] = ns["_avt_bad"]
    r = c.get("/almanach/vorlesen/ton?i=1&s=0&lang=de")
    ok(r.status_code == 503 and "antwortet nicht" in ((r.get_json() or {}).get("error") or ""), f"Piper mit Fehler: 503 + Hinweis ({r.status_code})")
    ok(not old, "auch bei einem Fehler nie die alte Stimme")
    page = c.get("/almanach/").get_data(as_text=True)
    ok("window.mwReadP = " in page and "window.almRead" in page and 'id="alm-rd"' in page and "/*VLPLAYER*/" not in page, "Seite: Spieler des Rucksacks + Leiste")
    return ns, app


INIT = r"""
window.__said = [];
try { const ss = window.speechSynthesis; if (ss) { let sp = false;
  ss.speak = u => { window.__said.push(u.text); sp = true; setTimeout(() => { sp = false; }, 4000); };
  Object.defineProperty(ss, "speaking", {get: () => sp}); ss.cancel = () => { sp = false; }; } } catch (e) {}
"""


def teil_b(ns, app, bilder):
    print("B) Browser 390 px", flush=True)
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    VL = ns["VL"]
    if bilder:
        os.makedirs(bilder, exist_ok=True)

    def foto(pg, name):
        if bilder:
            pg.wait_for_timeout(150)
            pg.screenshot(path=os.path.join(bilder, name + ".png"))

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx.add_init_script(INIT)
        pg = ctx.new_page()
        errs, tons = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "503" not in m.text else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: tons.append(r.url) if "/almanach/vorlesen/ton" in r.url else None)

        # 1) with the voice: Piper reads
        VL["synth"] = ns["_avt_synth"]
        pg.goto(base + "/almanach/#a2")
        pg.wait_for_selector("article h2")
        pg.wait_for_timeout(500)
        pg.click("#b-read")
        try:
            pg.wait_for_function("() => window.mwReadP && window.mwReadP.S.on && document.getElementById('rd-st').textContent.includes('KI-Stimme')", timeout=8000)
        except Exception:
            pass
        ok(any("i=2&s=0" in u for u in tons), f"🔊 holt den Ton über /almanach/vorlesen/ton ({tons[:2]})")
        ok(pg.is_visible("#alm-rd") and pg.is_visible("#rd-x") and pg.is_visible("#rd-go"), "Leiste unten mit ⏸ und ⏹ Stopp")
        ok(pg.evaluate("document.getElementById('b-read').classList.contains('on')"), "🔊 ist aktiv (Farbe)")
        ok(not pg.evaluate("window.__said.length"), "mit Piper keine Browser-Stimme")
        foto(pg, "almanach_piper_390")
        w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        ok(w[0] <= w[1], f"nicht zu breit {w}")
        try:
            pg.wait_for_function("() => window.mwReadP.S.s >= 1", timeout=8000)
            ok(True, "")
        except Exception:
            ok(False, "liest den nächsten Satz")
        pg.click("#rd-x")
        pg.wait_for_timeout(300)
        ok(not pg.is_visible("#alm-rd") and not pg.evaluate("window.mwReadP.S.on"), "⏹ Stopp hält an, Leiste weg")

        # 2) loading indicator: a slow voice
        def slow(text, lang, speed, out):
            time.sleep(1.5)
            return ns["_avt_synth"](text, lang, speed, out)
        VL["synth"] = slow
        pg.goto(base + "/almanach/#a5")
        pg.wait_for_selector("article h2"); pg.wait_for_timeout(400)
        pg.click("#b-read")
        pg.wait_for_timeout(300)
        ok(pg.locator("#rd-st .rd-sp").count() == 1 and "lad" in pg.inner_text("#rd-st"), f"Laden-Anzeige ({pg.inner_text('#rd-st')})")
        foto(pg, "almanach_piper_laedt_390")
        pg.click("#b-read")                                 # second tap = stop
        pg.wait_for_timeout(300)
        ok(not pg.is_visible("#alm-rd"), "zweiter Tipp auf 🔊 hält an")

        # 3) without Piper: the browser voice with a hint
        VL["synth"] = None
        pg.goto(base + "/almanach/#a3")
        pg.wait_for_selector("article h2"); pg.wait_for_timeout(500)
        n_ton = len(tons)
        pg.click("#b-read")
        pg.wait_for_timeout(600)
        said = pg.evaluate("window.__said")
        ok(len(said) == 1 and said[0].startswith(ns["alm_vl_arts"]()[3][0]), f"ohne Piper: Browser-Stimme liest den Artikel ({said[:1]})")
        ok(pg.is_visible("#x-tip") and "Browser" in pg.inner_text("#x-tip"), "ohne Piper: kurzer Hinweis")
        ok(pg.is_visible("#alm-rd") and "Browser" in pg.inner_text("#rd-st"), "Leiste zeigt «Browser-Stimme»")
        ok(len(tons) == n_ton, "ohne Piper kein Ton-Abruf")
        foto(pg, "almanach_browser_390")
        pg.click("#rd-x"); pg.wait_for_timeout(200)

        # 4) Piper fails: the browser voice reads on
        VL["synth"] = ns["_avt_bad"]
        pg.goto(base + "/almanach/#a4")
        pg.wait_for_selector("article h2"); pg.wait_for_timeout(500)
        pg.evaluate("window.__said = []")
        pg.click("#b-read")
        try:
            pg.wait_for_function("() => window.__said.length > 0", timeout=10000)
        except Exception:
            pass
        ok(pg.evaluate("window.__said.length") == 1 and "antwortet nicht" in pg.inner_text("#x-tip"), "Piper mit Fehler: Browser-Stimme + Hinweis")
        ok(not errs, f"keine JS-Fehler {errs[:3]}")
        b.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei"); ap.add_argument("--browser", action="store_true"); ap.add_argument("--bilder")
    a = ap.parse_args()
    datei = a.datei or neueste()
    print("Almanach-Vorlesen-Test mit", os.path.basename(datei), flush=True)
    ns, app = teil_a(datei)
    if a.browser or a.bilder:
        teil_b(ns, app, a.bilder)
    print(f"{N['ok']} Prüfungen, {len(FEHLER)} Fehler")
    for f in FEHLER:
        print("  ✗ " + f)
    sys.stdout.flush()
    os._exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
