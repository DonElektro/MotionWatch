#!/usr/bin/env python3
"""Tests für «Queen – iPhone-Test» (MoveEye Teil 639zzv, werkzeuge/fotaq/ios/): Test-Varianten der Engine von
«Flight of the Amazon Queen» neben dem Spiel. Erweitert den FOTAQ-Test in werkzeuge/spiele_test.py (gleiche Prüfungen).

  python3 werkzeuge/fotaq_iostest.py                     # MoveEye-Seite (gebaute Datei): Laden nur Admin, Pins, veränderte Datei,
                                                         #   kein Eintrag ohne das Spiel, keine Kachel, Spiele-Port /g/fotaqtest/
                                                         #   (Daten des Spiels, Stücke per «Range»), Warnseite bleibt, Entfernen
  python3 werkzeuge/fotaq_iostest.py --paket ORDNER --daten ORDNER [--bilder ORDNER]
                                                         # das echte Testpaket im Browser (Chromium als Handy und PC): jede Variante
                                                         #   startet auf Deutsch und Englisch bis ins Spiel, Diagnose-Zeile, Spielstand,
                                                         #   keine Fehler, nichts von aussen; misst Start und Speicher der Seite
Echtes Safari gibt es hier nicht: ob der Absturz auf iPhone / iPad weg ist, zeigt nur das Gerät.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import time
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import spiele_test as ST          # noqa: E402


def _fake_test(tag):
    """a tiny test package like the real one -> bytes, unpacked size"""
    files = {"index.html": b"<!doctype html><title>Queen - iPhone-Test</title><body><div id='vars'></div></body>", "iostest.js": b"/* test */",
             "thumb.svg": open(os.path.join(HIER, "fotaq", "thumb.svg"), "rb").read(), "a/scummvm.js": b"/* a */", "a/scummvm.wasm": b"\0asm\1\0\0\0",
             "b/scummvm.js": b"/* b */", "b/scummvm.wasm": b"\0asm\1\0\0\0", "LIZENZEN.txt": b"Test", "data/index.json": b'{"games":{},"queen.tbl":4}',
             "data/queen.tbl": b"QTBL", "fotaqtest.json": json.dumps({"tag": tag, "varianten": [{"id": "a"}, {"id": "b"}]}).encode()}
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for p, d in files.items():
            z.writestr(p, d)
    return b.getvalue(), sum(len(d) for d in files.values())


def moveeye(datei, fehler):
    import urllib.error
    import urllib.request
    from piper_test import Srv
    home = tempfile.mkdtemp(prefix="mw_fqt_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_fqt_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    ns["lan_guest_ip"] = lambda ip, fwd="": not fwd
    CFG, F, T = ns["CFG"], ns["FOTAQ_FILES"], ns["FQT_FILE"]

    def ok(c, what):
        print(("  ✓ " if c else "  ✗ ") + what, flush=True)
        if not c:
            fehler.append("iPhone-Test MoveEye: " + what)
    ok(ns["fqt_selftest"]() and ns["fotaq_selftest"](), "Selbsttest 639zzv und 639zzg")
    ok(ns["fqt_pinned"]() or not T["size"], f"Pins im Programm: alle oder keine ({ns['FQT_TAG']}, {T['size']} Bytes)")
    srv = Srv()
    tag = ns["FOTAQ_TAG"]
    for name, (k, b, unz) in ST._fake_fotaq(tag).items():
        F[k] = {"name": name, "size": len(b), "sha256": hashlib.sha256(b).hexdigest(), "unpacked": unz}
        srv.files["/" + tag + "/" + name] = b
    ns["FOTAQ_BASE"]["url"] = srv.url + tag + "/"
    ttag = "fotaqios-7"
    tb, tunz = _fake_test(ttag)
    ns["FQT_TAG"] = ttag
    T.update(name="fotaq-iostest-7.zip", size=len(tb), sha256=hashlib.sha256(tb).hexdigest(), unpacked=tunz)
    srv.files["/" + ttag + "/" + T["name"]] = tb
    ns["FQT_BASE"]["url"] = srv.url + ttag + "/"
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.1)
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    c = ws.app.test_client(use_cookies=False)
    H = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode()}
    HA = {"Authorization": "Basic " + base64.b64encode(b"Anna:anna-pass-1").decode()}
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); wp = sk.getsockname()[1]
    if not ns["GAMESRV"]["port"]:
        CFG["web_port"] = wp - 2
        ns["games_server_start"]()
    gp = ns["GAMESRV"]["port"]
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path, hdr=None):
        try:
            with op.open(urllib.request.Request(f"http://127.0.0.1:{gp}{path}", headers=hdr or {}), timeout=60) as x:
                return x.status, dict(x.headers), x.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), b""

    def party(d=None, h=H):
        r = c.post("/api/party", json=d, headers=h) if d is not None else c.get("/api/party", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def warten(dl):
        t0 = time.time()
        while dl["running"] and time.time() - t0 < 60:
            time.sleep(0.1)
    code, j = party()
    S = (j.get("fotaq") or {}).get("iostest") or {}
    ok(code == 200 and S.get("pinned") and not S.get("installed") and not S.get("game"), "/api/party: Testpaket gepinnt, nicht installiert, Spiel fehlt")
    code, j = party({"action": "fotaq_install", "iostest": True})
    ok(code == 400 and not ns["fqt_installed"](), f"ohne das Spiel kein Test ({j.get('error')})")
    party({"action": "fotaq_install", "langs": ["de", "en"]}); warten(ns["FOTAQ_DL"])
    ok(ns["fotaq_installed"](), "das Spiel ist installiert (Test-ZIP)")
    code, j = party({"action": "fotaq_install", "iostest": True}, HA)
    ok(code in (401, 403) and not ns["fqt_installed"](), f"Familie darf den Test nicht laden ({code})")
    ok(get("/g/fotaqtest/")[0] == 404 and get("/g/fotaqtest/data/games/de/queen.1c")[0] == 404, "Port: vor dem Laden nichts unter /g/fotaqtest/")
    srv.files["/" + ttag + "/" + T["name"]] = tb[:-1] + bytes([tb[-1] ^ 1])
    party({"action": "fotaq_install", "iostest": True}); warten(ns["FQT_DL"])
    ok(not ns["fqt_installed"]() and "checksum" in ns["FQT_DL"]["msg"], f"veränderte Datei abgelehnt ({ns['FQT_DL']['msg']})")
    srv.files["/" + ttag + "/" + T["name"]] = tb
    code, j = party({"action": "fotaq_install", "iostest": True}); warten(ns["FQT_DL"])
    ok(code == 200 and ns["fqt_installed"]() and not ns["FQT_DL"]["msg"], f"Test geladen und entpackt ({ns['FQT_DL']['msg'] or 'ok'})")
    ok(not os.path.exists(os.path.join(home, T["name"])), "ZIP danach gelöscht")
    S = party()[1]["fotaq"]["iostest"]
    ok(S["installed"] and S["game"] and S["tag"] == ttag, "/api/party: Test installiert")
    gl = ns["games_list"]()
    ok(all(x.get("dir") != "fotaqtest" for x in gl) and any(x.get("dir") == "fotaq" for x in gl), "keine Kachel für den Test, die Kachel des Spiels bleibt")
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    ok(r.status_code == 200 and "fotaqtest" not in r.get_data(as_text=True), "/spiele: kein Hinweis auf den Test")
    s_, h_, b_ = get("/g/fotaqtest/")
    ok(s_ == 200 and b"iPhone-Test" in b_ and b'id="mw-back"' in b_, "Port: /g/fotaqtest/ = Seite des Tests mit «✕ Zurück»")
    s_, h_, b_ = get("/g/fotaqtest/b/scummvm.wasm")
    ok(s_ == 200 and h_.get("Content-Type") == "application/wasm" and b_[:4] == b"\0asm", "Port: Engine der Variante B (application/wasm)")
    q = open(os.path.join(ns["fotaq_dir"](), "data", "games", "de", "queen.1c"), "rb").read()
    s_, h_, b_ = get("/g/fotaqtest/data/games/de/queen.1c")
    ok(s_ == 200 and b_ == q and h_.get("Accept-Ranges") == "bytes", "Port: Spieldaten des Tests = die des Spiels (ganz)")
    s_, h_, b_ = get("/g/fotaqtest/data/games/de/queen.1c", {"Range": "bytes=1000-66535"})
    ok(s_ == 206 and b_ == q[1000:66536] and h_.get("Content-Range") == f"bytes 1000-66535/{len(q)}", f"Port: ein Stück per «Range» ({s_}, {len(b_)} Bytes)")
    s_, h_, b_ = get("/g/fotaqtest/data/games/de/queen.1c", {"Range": f"bytes={len(q) - 10}-{len(q) + 500}"})
    ok(s_ == 206 and b_ == q[-10:], "Port: letztes Stück wird am Dateiende gekürzt")
    s_, h_, b_ = get("/g/fotaqtest/data/games/de/queen.1c", {"Range": f"bytes={len(q)}-"})
    ok(s_ == 416, f"Port: Stück hinter dem Ende -> 416 ({s_})")
    s_, h_, b_ = get("/g/fotaq/data/games/en/queen.1c", {"Range": "bytes=0-9"})
    ok(s_ == 206 and len(b_) == 10, "Port: «Range» auch beim Spiel selbst")
    s_, h_, b_ = get("/g/fotaqtest/data/games/index.json")
    ok(s_ == 200 and sorted(json.loads(b_)) == ["de", "en"], "Port: Sprachen des Tests = die installierten des Spiels")
    for bad in ("/g/fotaqtest/fotaqtest.ok", "/g/fotaqtest/../settings.json", "/g/fotaqtest/%2e%2e/settings.json", "/g/fotaqtest/data/games/../../../settings.json",
                "/g/fotaqtest/data/games/de/../../../fotaq.ok"):
        ok(get(bad)[0] in (301, 400, 404), f"Port: {bad} gibt es nicht")
    s_, h_, b_ = get("/g/fotaq/")
    ok(s_ == 200 and "Trotzdem starten".encode() in b_, "die Warnseite des Spiels bleibt")
    # second round: the test page reports to MoveEye (games port), the administrator reads it in /api/party

    def post(path, body, hdr=None):
        try:
            with op.open(urllib.request.Request(f"http://127.0.0.1:{gp}{path}", data=body, headers=dict({"Content-Type": "text/plain"}, **(hdr or {})), method="POST"), timeout=30) as x:
                return x.status
        except urllib.error.HTTPError as e:
            return e.code
    rep = {"why": "error", "v": "b", "lang": "de", "dev": "iPhone iOS 18.7", "step": 3, "sec": 41, "wasm": 5358441, "heap": 67108864, "req": 30, "bytes": 6920000,
           "errors": 0, "retries": 0, "audio": "running 48000", "tag": ttag, "kind": "exit", "passwort": "geheim",
           "err": "CRITICAL: Missing variable: 'Globals.ShowSearchPic'! http://192.168.1.75:5002/g/fotaqtest/ <b>"}
    ok(post("/fotaqtest-diag/report", json.dumps(rep).encode()) == 204, "Port: Meldung der Testseite angenommen")
    R = party()[1]["fotaq"]["iostest"]["reports"]
    ok(len(R) == 1 and R[0]["v"] == "b" and R[0]["sec"] == 41 and R[0]["err"].startswith("CRITICAL: Missing variable: 'Globals.ShowSearchPic'!"), "/api/party: die Meldung steht beim Test")
    ok("192.168" not in json.dumps(R) and "passwort" not in R[0] and "geheim" not in json.dumps(R), "Meldung: keine Adresse, keine fremden Felder")
    ok(os.path.isfile(ns["fqt_reports_file"]()) and "192.168" not in open(ns["fqt_reports_file"]()).read(), "Meldung bleibt in einer Datei (ohne Adresse)")
    ok(post("/fotaqtest-diag/report", json.dumps(rep).encode(), {"Origin": "http://boese.example"}) == 403, "Port: Meldung von einer fremden Seite abgelehnt")
    ok(post("/fotaqtest-diag/report", b"x" * 5000) == 413 and post("/fotaqtest-diag/report", b"kein json") == 400, "Port: zu grosse / kaputte Meldung abgelehnt")
    ok(post("/fotaqtest-diag/anderes", b"{}") == 404 and get("/fotaqtest-diag/report")[0] == 404, "Port: nur POST /fotaqtest-diag/report")
    time.sleep(0.6)
    for i in range(14):
        ns["FQT_REPORTS"]["last"] = 0
        ns["fqt_report_add"](dict(rep, sec=i, err=""))
    R = party()[1]["fotaq"]["iostest"]["reports"]
    ok(len(R) == 12 and R[0]["sec"] == 13, "höchstens 12 Meldungen, die neueste zuerst")
    tp = ns["TOOLS_PAGE"]
    ok("fqtPaint((P.fotaq || {}).iostest);" in tp and 'pl.href = "/games/fotaqtest/"' in tp and "iostest: true" in tp, "Reiter Spielecke: Eintrag «Queen – iPhone-Test» mit «Test öffnen»")
    ok('rb.id = "fqt-reports"' in tp and "Meldungen vom Test" in tp, "Reiter Spielecke: «Meldungen vom Test» mit «Kopieren»")
    party({"action": "fotaq_remove", "lang": "de"})
    ok(get("/g/fotaqtest/data/games/de/queen.1c")[0] == 404 and get("/g/fotaqtest/data/games/en/queen.1c")[0] == 200, "eine Sprache des Spiels entfernt: im Test auch weg")
    code, j = party({"action": "fotaq_delete", "iostest": True})
    ok(code == 200 and not ns["fqt_installed"]() and not os.path.exists(ns["fqt_dir"]()) and ns["fotaq_installed"](), "Test entfernt, das Spiel bleibt")
    ok(party()[1]["fotaq"]["iostest"]["reports"] == [] and not os.path.exists(ns["fqt_reports_file"]()) and post("/fotaqtest-diag/report", json.dumps(rep).encode()) == 404,
       "Test entfernt: Meldungen weg, keine neuen angenommen")
    party({"action": "fotaq_install", "iostest": True}); warten(ns["FQT_DL"])
    party({"action": "fotaq_delete"})
    ok(not ns["fotaq_installed"]() and not ns["fqt_installed"]() and get("/g/fotaqtest/")[0] == 404, "Spiel entfernt: der Test ist nicht mehr erreichbar")
    srv.stop() if hasattr(srv, "stop") else None
    shutil.rmtree(home, ignore_errors=True)


def ende_pruefen(pw, br, base, v, fehler, bilder):
    """second round (first test on the iPhone, 12.11.2026: «Aufgeben» → «Ja» opened ScummVM's launcher, which stopped with
    «Missing variable: 'Globals.ShowSearchPic'»): giving up ends the game cleanly with «Spiel beendet», the quick save made
    before is in the browser store; and when the game data stop coming, a message stays (after retries), no black screen"""
    tag = f"iPhone-Test {v} Ende"

    def start(ctx):
        pg = ctx.new_page()
        pg.goto(f"{base}/g/fotaqtest/index.html?v={v}", wait_until="load"); pg.wait_for_selector(f"#var-{v}.on", timeout=10000)
        pg.locator("#btn-de").tap()
        pg.wait_for_function("() => window.FOTAQ_DIAG && FOTAQ_DIAG().step === 3", timeout=150000)
        return pg
    geraet = dict(viewport={"width": 844, "height": 390}, is_mobile=True, has_touch=True, user_agent=pw.devices["iPhone 13"]["user_agent"], locale="de-CH")
    ctx = br.new_context(**geraet)
    try:
        pg = start(ctx)
        fe = []
        pg.on("pageerror", lambda e: fe.append(str(e)[:200]))
        for _ in range(8):
            pg.locator("#kSkip").tap(); pg.wait_for_timeout(2500)
        pg.keyboard.press("F11"); pg.wait_for_timeout(2500)          # quick save in the first room
        pg.locator("#kMenu").tap(); pg.wait_for_timeout(2500)         # the journal: «Give Up» bottom left, then «Yes»
        c = pg.locator("#canvas").bounding_box()
        for fx, fy in ((0.27, 0.84), (0.27, 0.36)):
            pg.touchscreen.tap(c["x"] + c["width"] * fx, c["y"] + c["height"] * fy); pg.wait_for_timeout(2500)
        try:
            pg.wait_for_selector("#fqEnd", timeout=15000)
        except Exception:
            pass
        pg.wait_for_timeout(800)
        if bilder:
            pg.screenshot(path=os.path.join(bilder, f"test_ende_{v}.png"))
        dg = pg.evaluate("() => FOTAQ_DIAG()")
        tx = pg.locator("#fqEnd").inner_text() if pg.locator("#fqEnd").count() else ""
        log = pg.evaluate("() => FOTAQ.log.join(' | ')")
        if not dg.get("ended") or dg.get("err") or "Spiel beendet" not in tx or "gesichert" not in tx or "Missing variable" in log:
            fehler.append(f"{tag}: «Aufgeben» → «Ja» endet nicht sauber mit «Spiel beendet» (Tafel: {tx[:120]!r}; {json.dumps(dg)[:260]}; Log: {log[-300:]})")
        if pg.locator("#fqEnd.bad").count() or not pg.locator("#fqAgain").is_visible() or not pg.locator("#fqBack").is_visible():
            fehler.append(f"{tag}: Tafel «Spiel beendet» ohne «Nochmal» / «‹ Spiele» oder als Fehler")
        keys = pg.evaluate(ST.FOTAQ_IDB) or []
        if not [k for k in keys if "/saves/de/" in k and not k.endswith("/de")]:
            fehler.append(f"{tag}: der Spielstand von vorher ist nach dem Ende nicht im Browser-Speicher ({len(keys)} Einträge)")
        pg.locator("#fqAgain").tap(); pg.wait_for_selector(f"#var-{v}", timeout=10000)
        hist = pg.locator("#hist").inner_text()
        if "sauber beendet" not in hist or "NICHT" in hist or "FEHLER" in hist:
            fehler.append(f"{tag}: der Lauf steht nicht als sauber beendet in der Liste ({hist[:160]})")
        for x in fe:
            if "ExitStatus" not in x:
                fehler.append(f"{tag}: JavaScript: {x}")
        print(f"{tag}: Aufgeben ok ({tx.splitlines()[0] if tx else '-'})", flush=True)
    except Exception as e:
        fehler.append(f"{tag}: {e.__class__.__name__}: {str(e)[:200]}")
    ctx.close()
    ctx = br.new_context(**geraet)                          # the game data stop coming after the start
    try:
        aus = [False]
        ctx.route("**/data/games/**", lambda r: r.abort() if aus[0] and "queen.1c" in r.request.url else r.continue_())
        pg = start(ctx)
        pg.evaluate("() => { localStorage.removeItem('x'); }")
        aus[0] = True
        t0 = time.time()
        while time.time() - t0 < 60 and not pg.locator("#fqEnd.bad").count():
            pg.locator("#kSkip").tap(); pg.wait_for_timeout(2000)
        dg = pg.evaluate("() => FOTAQ_DIAG()")
        tx = pg.locator("#fqEnd").inner_text() if pg.locator("#fqEnd").count() else ""
        if bilder:
            pg.screenshot(path=os.path.join(bilder, f"test_daten_weg_{v}.png"))
        if dg.get("kind") != "data" or not dg.get("retries") or "Spieldaten konnten nicht geladen werden" not in tx or "queen.1c" not in pg.locator("#fqMsg").input_value():
            fehler.append(f"{tag}: fehlende Spieldaten geben keine klare Meldung nach Wiederholungen (Tafel: {tx[:120]!r}; {json.dumps(dg)[:260]})")
        elif not pg.locator("#fqCopy").is_visible():
            fehler.append(f"{tag}: «Fehler kopieren» fehlt")
        else:
            print(f"{tag}: Daten weg -> Meldung nach {dg['retries']} Wiederholungen ok", flush=True)
        pg.locator("#fqAgain").tap(); pg.wait_for_selector(f"#var-{v}", timeout=10000)
        hist = pg.locator("#hist").inner_text()
        if "FEHLER" not in hist or "queen.1c" not in hist:
            fehler.append(f"{tag}: der Fehler steht nach dem Neuladen nicht in der Liste ({hist[:200]})")
    except Exception as e:
        fehler.append(f"{tag} (Daten weg): {e.__class__.__name__}: {str(e)[:200]}")
    ctx.close()


def paket(pfad, daten, bilder, fehler, warn):
    """the real test package in the browser: every variant, German and English"""
    from playwright.sync_api import sync_playwright
    import mimetypes
    mimetypes.add_type("application/wasm", ".wasm")
    man = json.load(open(os.path.join(pfad, "fotaqtest.json"), encoding="utf-8"))
    root = tempfile.mkdtemp(prefix="mw_fqt_web_")
    d = os.path.join(root, "fotaqtest")
    shutil.copytree(pfad, d)
    if os.path.exists(os.path.join(d, "data", "games")):
        fehler.append("iPhone-Test: das Paket enthält Spieldaten (data/games)")
        return
    shutil.copytree(daten, os.path.join(d, "data", "games"), copy_function=lambda a, b: (os.link(a, b) if os.stat(a).st_dev == os.stat(os.path.dirname(b)).st_dev else shutil.copy2(a, b)))
    s = ST.server(root)
    mess = {}
    try:
        base = f"http://127.0.0.1:{s.server_address[1]}"
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=ST.FOTAQ_ARGS)
            vs = [v["id"] for v in man["varianten"]]
            for v in vs:
                m = mess.setdefault(v, {})
                ST.fotaq_pruefen(br, base, fehler, warn, bilder and os.path.join(bilder, v), nur=["handy"] + (["pc"] if v == vs[-1] else []),
                                 seite=f"/g/fotaqtest/index.html?v={v}", marke=f"-Test {v.upper()}", mess=m)
                for k, x in m.items():
                    dg = x.get("diag") or {}
                    if dg.get("v") != v or dg.get("step") != 3 or dg.get("errors") or not dg.get("req") or not dg.get("heap"):
                        fehler.append(f"iPhone-Test {v} {k}: Diagnose stimmt nicht ({json.dumps(dg)[:200]})")
                    elif dg["heap"] > 200 * 1048576:
                        fehler.append(f"iPhone-Test {v} {k}: WebAssembly-Speicher {dg['heap'] >> 20} MB (erwartet deutlich unter 200 MB)")
            # as an iPhone 13 (upright, like the owner opens it): choice of the variant, device line, a run in the list after reload
            ctx = br.new_context(**pw.devices["iPhone 13"])
            pg = ctx.new_page()
            fe = []
            pg.on("pageerror", lambda e: fe.append(str(e)[:200]))
            pg.goto(f"{base}/g/fotaqtest/index.html", wait_until="load")
            pg.wait_for_selector("#var-" + vs[-1], timeout=10000)
            hist = pg.locator("#hist").inner_text()
            if "iPhone iOS" not in hist or man["tag"] not in hist:
                fehler.append(f"iPhone-Test: Gerätezeile fehlt ({hist[:120]})")
            if "✓" not in pg.locator("#var-" + vs[0]).inner_text():
                fehler.append("iPhone-Test: ohne ?v= ist nicht die erste Variante gewählt")
            pg.locator("#var-" + vs[-1]).tap()
            pg.wait_for_url("**/index.html?v=" + vs[-1], timeout=8000)
            pg.wait_for_selector("#var-" + vs[-1] + ".on", timeout=8000)
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "test_auswahl_iphone.png"), full_page=True)
            pg.locator("#btn-de").tap()
            try:
                pg.wait_for_function("() => window.FOTAQ_DIAG && FOTAQ_DIAG().step === 3", timeout=150000)
            except Exception:
                fehler.append("iPhone-Test (iPhone 13): Schritt 3 nicht erreicht: " + str(pg.evaluate("() => JSON.stringify(window.FOTAQ_DIAG && FOTAQ_DIAG())"))[:300])
            pg.wait_for_timeout(2500)
            dz = pg.locator("#dz").inner_text()
            pg.wait_for_timeout(5500)                   # second round: the line hides itself after the start, «ⓘ» shows it again
            if pg.locator("#dz").is_visible():
                fehler.append("iPhone-Test: die Diagnose-Zeile bleibt über dem Spiel stehen")
            pg.locator("#kDiag").tap(); pg.wait_for_timeout(1300)
            if not pg.locator("#dz").is_visible():
                fehler.append("iPhone-Test: «ⓘ» zeigt die Diagnose-Zeile nicht")
            pg.locator("#kDiag").tap()
            if not all(x in dz for x in ("Test " + vs[-1].upper(), "iPhone iOS", "Schritt 3: gestartet", "Speicher", "Daten", "Ton")):
                fehler.append(f"iPhone-Test: Diagnose-Zeile unvollständig ({dz})")
            print("Diagnose-Zeile (iPhone 13): " + dz, flush=True)
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "test_spiel_iphone.png"))
            pg.evaluate("() => { const a = JSON.parse(localStorage.getItem('fotaq-iostest-runs')); window.__n = a.length; }")
            pg.reload(wait_until="load"); pg.wait_for_selector("#var-" + vs[-1], timeout=10000)
            hist = pg.locator("#hist").inner_text()
            if "Schritt 3: gestartet" not in hist or "sauber beendet" not in hist or "NICHT" in hist:
                fehler.append(f"iPhone-Test: der Lauf steht nach dem Neuladen nicht als sauber beendet in der Liste ({hist[:200]})")
            # a run that was cut off (crash): marked
            pg.evaluate("() => { const a = JSON.parse(localStorage.getItem('fotaq-iostest-runs')); a[a.length - 1].clean = false; localStorage.setItem('fotaq-iostest-runs', JSON.stringify(a)); }")
            pg.reload(wait_until="load"); pg.wait_for_selector("#var-" + vs[-1], timeout=10000)
            if "NICHT sauber beendet" not in pg.locator("#hist").inner_text():
                fehler.append("iPhone-Test: ein abgebrochener Lauf ist nicht markiert")
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "test_nach_absturz_iphone.png"), full_page=True)
            for x in fe:
                fehler.append("iPhone-Test (iPhone 13): JavaScript: " + x)
            ctx.close()
            for v in vs:
                ende_pruefen(pw, br, base, v, fehler, bilder)
            br.close()
    finally:
        s.shutdown()
        shutil.rmtree(root, ignore_errors=True)
    print("\nMESSUNG Testpaket " + man["tag"])
    for v in man["varianten"]:
        print(f"  Variante {v['id']}: wasm {v['wasm']} Bytes, grösste Funktion {v['largest']}, Funktionen 40–160 KB: {v['from_40000_to_160000']}, über 10 KB: {v['over_10000']}")
        for k, x in sorted(mess.get(v["id"], {}).items()):
            dg = x.get("diag") or {}
            print(f"    {k:<9} Start {x['start_s']:>3} s · Seite bis {x['mb']} MB · WebAssembly-Speicher {dg.get('heap', 0) >> 20} MB · Daten gelesen {dg.get('bytes', 0) >> 20} MB in {dg.get('req', 0)} Stücken")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paket", default="", help="Ordner fotaqtest/ des Testpakets (aus ios_paket.py)")
    ap.add_argument("--daten", default="", help="mit --paket: Ordner data/games des Spiels (de/, en/, index.json)")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--datei", default="", help="die gebaute MoveEye-Datei (sonst die neueste)")
    a = ap.parse_args()
    fehler, warn = [], []
    if a.paket:
        paket(a.paket, a.daten, a.bilder, fehler, warn)
    else:
        moveeye(a.datei or ST._neueste_datei(), fehler)
    for w in warn:
        print("Hinweis: " + w)
    if fehler:
        print("\nFEHLER:\n  " + "\n  ".join(fehler))
        sys.exit(1)
    print("\nOK")


if __name__ == "__main__":
    main()
