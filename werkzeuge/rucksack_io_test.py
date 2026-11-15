#!/usr/bin/env python3
"""Test «🎒 Rucksack bei Import/Export» (Teil 639zzzzr):

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei (schnell, ohne Browser):
     feste Export-Liste (RK_EXPORTS: genau diese Muster, fremde Rechner / «..» / /tausch / unbekannte Parameter abgewiesen),
     Privates (Einstellungen, Diagnose, Nacht-Testlauf, Sicherungen) nur in «Meine Dateien» – auch wenn die Seite «Für alle»
     schickt –, Inhalt gleich wie der direkte Download, Rechte je Rolle (Admin, Familie, Freund, Kind; nur Admin-Exporte für
     den Admin), App-Schlüssel nie, Bedienermodus, fremde Origin (CSRF), Grenze pro Datei, Skript /rk/io.js und Einbau
     nur auf Seiten mit Reitern (nicht Gast, nicht die Funk-Seite).
  B) --browser: MoveEye ohne Fenster (eigener Datenordner), Playwright Handy 390 × 844 (Faktor 2) und PC:
     Einstellungen → «🎒 In den Rucksack» (Einstellungsdatei landet in «Meine Dateien»), «🎒 Aus dem Rucksack» lädt eine
     Einstellungsdatei, Touren: GPX aus dem Rucksack importieren, Tour als GPX in den Rucksack, ein Datei-Feld ohne Knopf
     fragt «Von diesem Gerät / Aus dem Rucksack», Live-Reiter ohne 🎒, keine JavaScript-Fehler. Bildschirmfotos mit --bilder.

  python3 werkzeuge/rucksack_io_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

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


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def gpx(name, n=25):
    seg = "".join('<trkpt lat="%.5f" lon="%.5f"><ele>%d</ele></trkpt>' % (46.61 + i * 0.002, 8.05 + i * 0.003, 1500 + i * 40) for i in range(n))
    return ('<?xml version="1.0"?><gpx version="1.1" creator="test"><trk><name>%s</name><trkseg>%s</trkseg></trk></gpx>' % (name, seg)).encode()


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    home = tempfile.mkdtemp(prefix="mw_rkio_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_rkio_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    CFG, TZ = ns["CFG"], ns["TZ"]
    root = tempfile.mkdtemp(prefix="mw_rkio_root_")
    try:
        TZ["root_test"] = root
        ns["GAMESRV"]["port"] = 1
        CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_push=False, quiet_on=False)
        ns["tausch_disk_free"] = lambda p: 100 * ns["TZ_GB"]
        TZ["push_manual"] = True
        ns["tausch_push_send"] = lambda *a: True
        ns["tausch_push_user"] = lambda *a: True
        PW = "Admin-Pass-123"
        assert ns["web_pw_set"](PW)[0]
        users = {"Anna": "family", "Bob": "friend", "Kim": "kid"}
        for n, r in users.items():
            okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
            assert okk, err
        ws = ns["WebStream"](None)
        ws._serve = lambda app, ctx: None
        ws.start()
        c = ws.app.test_client(use_cookies=False)
        H = {n: basic(n, n.lower() + "-pass-1") for n in users}
        H["admin"] = basic("admin", PW)

        def io(who, d, extra=None):
            r = c.post("/api/tausch/io", json=dict(d, lang="de"), headers=dict(H[who], **(extra or {})))
            return r.status_code, (r.get_json(silent=True) or {})

        def files(who, area):
            return {f["name"]: f for f in c.get(f"/api/tausch?area={area}", headers=H[who]).get_json().get("files", [])}

        print("A) feste Liste", flush=True)
        F = ns["rk_export_find"]
        want = {r"/api/settings/export": "private", r"/tools/diag\.zip": "private", r"/api/nacht/export/[A-Za-z0-9_.-]{1,80}": "private",
                r"/api/factory/backup/[A-Za-z0-9_.-]{1,120}": "private", r"/api/sim/sicherung/[A-Za-z0-9_.-]{1,120}": "private"}
        have = {p: m for p, q, m, k in ns["RK_EXPORTS"]}
        for p, m in want.items():
            ok(have.get(p) == m, f"privat in der Liste: {p} -> {have.get(p)}")
        ok(len(ns["RK_EXPORTS"]) == 17, f"Liste hat {len(ns['RK_EXPORTS'])} Einträge (neue nur mit Test)")
        ok(isinstance(ns["RK_EXPORTS"], tuple) and all(isinstance(e, tuple) for e in ns["RK_EXPORTS"]), "Liste ist fest (Tupel)")
        for u in ("http://127.0.0.1/api/settings/export", "//x/api/settings/export", "/api/settings/export?a=1", "/tausch/dl/0123456789abcdef",
                  "/api/tausch", "/build/datei/../x", "/build/datei/%2E%2E/x", "/rec/file/a.mp4?dl=1&z=1", "/api/settings/export#f",
                  "/x/api/settings/export", "/api/users", "/api/settings", "/rec/file/a%00.mp4"):
            ok(F(u) is None, f"abgewiesen: {u}")

        print("A) Speichern als Admin", flush=True)
        direct = c.get("/api/settings/export", headers=H["admin"]).data
        code, j = io("admin", {"action": "save", "url": "/api/settings/export", "area": "all", "folder": ""})
        ok(code == 200 and j.get("ok") and j.get("private") is True, f"Einstellungen gespeichert: {code} {j}")
        fid = (j.get("file") or {}).get("id", "")
        ok((j.get("file") or {}).get("area") == "mine", f"Einstellungen nur in «Meine Dateien» (Seite schickte «Für alle»): {j.get('file')}")
        ok(fid and c.get(f"/tausch/dl/{fid}", headers=H["admin"]).data == direct, "Inhalt gleich wie der Download")
        ok(re.match(r"moveeye_einstellungen.*\.json$", (j.get("file") or {}).get("name", "")) is not None, f"Name aus dem Download: {j.get('file', {}).get('name')}")
        ok(not any(n.startswith("moveeye_einstellungen") for n in files("admin", "all")), "nicht unter «Für alle»")
        code, j = io("admin", {"action": "save", "url": "/tools/diag.zip", "area": "all"})
        ok(code == 200 and (j.get("file") or {}).get("area") == "mine", f"Diagnose nur privat: {code} {str(j)[:200]}")
        code, j = io("admin", {"action": "save", "url": "/api/servo/export?fmt=csv", "area": "all", "name": "Servo.csv"})
        ok(code == 200 and (j.get("file") or {}).get("area") == "all" and j["file"]["name"] == "Servo.csv", f"Servo-Daten für alle mit eigenem Namen: {code} {j}")
        code, j = io("admin", {"action": "save", "url": "/api/servo/export?fmt=csv", "area": "all", "name": "Servo.csv"})
        ok(code == 200 and j.get("file", {}).get("name") == "Servo (2).csv", f"gleicher Name -> (2): {j.get('file', {}).get('name')}")
        c.post("/api/touren/import?lang=de&name=Weg.gpx", data=gpx("Weg"), headers=dict(H["admin"], **{"Content-Type": "application/octet-stream"}))
        code, j = io("admin", {"action": "save", "url": "/touren/x/alle.zip", "area": "all"})
        ok(code == 200 and j.get("file", {}).get("name") == "MoveEye_Touren.zip", f"alle Touren als ZIP: {code} {j}")
        code, j = io("admin", {"action": "save", "url": "/api/users", "area": "all"})
        ok(code == 400 and not j.get("ok"), f"Adresse nicht in der Liste: {code}")
        code, j = io("admin", {"action": "save", "url": "/api/nacht/export/gibtsnicht", "area": "all"})
        ok(code == 400 and "HTTP" in (j.get("error") or ""), f"Export mit Fehler -> nichts gespeichert: {code} {j}")
        code, j = io("admin", {"action": "nope"})
        ok(code == 400, "unbekannte Aktion")
        r = c.post("/api/tausch/io", json={"action": "save", "url": "/api/settings/export"}, headers=dict(H["admin"], Origin="https://evil.example"))
        ok(r.status_code == 403, f"fremde Origin abgewiesen: {r.status_code}")

        print("A) Grenzen, Bedienermodus", flush=True)
        CFG["tausch_file_mb"] = 0.0001
        code, j = io("admin", {"action": "save", "url": "/api/settings/export", "area": "mine"})
        ok(code == 400 and "gross" in (j.get("error") or ""), f"zu gross für den Rucksack: {code} {j}")
        CFG["tausch_file_mb"] = 200.0
        ok(not [x for x in os.listdir(os.path.join(root, "up")) if x.startswith("rk_")], "keine Zwischendatei übrig")
        CFG["lock_on"] = True
        code, j = io("admin", {"action": "save", "url": "/api/settings/export", "area": "mine"})
        ok(code == 400 and not j.get("ok"), f"Bedienermodus: Einstellungen nicht exportierbar: {code} {j}")
        CFG["lock_on"] = False
        CFG["tausch_on"] = False
        code, j = io("admin", {"action": "save", "url": "/api/servo/export?fmt=json", "area": "all"})
        ok(code == 400, "Rucksack aus -> nichts")
        r = c.get("/api/tausch/io", headers=H["admin"])
        ok(r.status_code == 200 and r.get_json().get("on") is False, "Probe: aus")
        CFG["tausch_on"] = True

        print("A) Rechte je Rolle", flush=True)
        r = c.get("/api/tausch/io?lang=de", headers=H["Anna"])
        pj = r.get_json() or {}
        ok(r.status_code == 200 and pj.get("up") and pj.get("down") and len(pj.get("exports", [])) == 17, f"Familie: Probe {r.status_code} {str(pj)[:120]}")
        code, j = io("Anna", {"action": "save", "url": "/api/settings/export", "area": "mine"})
        ok(code == 400 and not j.get("ok"), f"Familie: Einstellungen (nur Admin) abgewiesen: {code} {j}")
        code, j = io("Anna", {"action": "save", "url": "/touren/x/alle.zip", "area": "all"})
        ok(code == 200 and j.get("file", {}).get("area") == "all", f"Familie: Touren-ZIP: {code} {j}")
        code, j = io("Anna", {"action": "save", "url": "/tools/diag.zip", "area": "all"})
        ok(code == 400, f"Familie: Diagnose abgewiesen: {code}")
        r = c.get("/api/tausch/io", headers=H["Bob"])
        ok(r.status_code == 200 and r.get_json().get("up") is False and r.get_json().get("down") is True, "Freund: nur wählen")
        code, j = io("Bob", {"action": "save", "url": "/touren/x/alle.zip", "area": "all"})
        ok(code in (400, 403) and not j.get("ok"), f"Freund: speichern abgewiesen: {code}")
        r = c.get("/api/tausch/io", headers=H["Kim"])
        ok(r.status_code == 403, f"Kind: keine Rechte: {r.status_code}")
        okk, err, key = ns["appkey_create"]("Prog")
        ok(okk, f"App-Schlüssel angelegt: {err}")
        r = c.get("/api/tausch/io", headers={"X-MoveEye-Key": key})
        ok(r.status_code == 403, f"App-Schlüssel: keine Probe ({r.status_code})")
        r = c.post("/api/tausch/io", json={"action": "save", "url": "/touren/x/alle.zip", "lang": "de"}, headers={"X-MoveEye-Key": key})
        ok(r.status_code == 400 and not (r.get_json() or {}).get("ok"), f"App-Schlüssel: kein Speichern ({r.status_code})")

        print("A) Skript und Einbau", flush=True)
        r = c.get("/settings", headers=H["admin"])
        m = re.search(r'/rk/io\.js\?v=([0-9a-f]{12})', r.get_data(as_text=True))
        ok(m is not None, "Skript auf /settings")
        for pth in ("/karte", "/tausch/pack", "/more"):
            rr = c.get(pth, headers=H["admin"])
            ok(rr.status_code != 200 or rr.get_data(as_text=True).count("/rk/io.js") == 1, f"Skript genau einmal auf {pth}")
        r2 = c.get("/morse/funk", headers=H["admin"])
        ok("/rk/io.js" not in r2.get_data(as_text=True), "Funk-Seite unverändert (kein Skript)")
        js = c.get("/rk/io.js?v=" + (m.group(1) if m else ""), headers=H["Anna"])
        t = js.get_data(as_text=True)
        ok(js.status_code == 200 and "javascript" in js.content_type and "/*RKTX*/" not in t and "Aus dem Rucksack" in t,
           f"Skript für Benutzer mit Texten ({js.status_code})")
        ok(js.headers.get("Cache-Control", "").startswith("private, max-age"), "Skript mit Version wird zwischengespeichert")
        ns["rucksack_io_selftest"]()
        ok(True, "Selbsttest des Teils")
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(datei, bilder):
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    base = "http://127.0.0.1:%d" % port
    tmp = tempfile.mkdtemp(prefix="mw_rkio_b_")
    PW = "Rk-Test-2026!"
    auth = "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()
    cfg = os.path.join(tmp, "mw")
    os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "tausch_free_gb": 0.2}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    logf = open(os.path.join(tmp, "mw.log"), "w")
    p = subprocess.Popen([sys.executable, os.path.abspath(datei), "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=dict(os.environ, MOTIONWATCH_HOME=tmp))

    def req(path, data=None, ctype="application/json"):
        r = urllib.request.Request(base + path, data=data, method="POST" if data is not None else "GET")
        r.add_header("Authorization", auth)
        if data is not None:
            r.add_header("Content-Type", ctype)
        with urllib.request.urlopen(r, timeout=60) as f:
            return f.read()

    def up(name, b, area="all", folder=""):
        s = json.loads(req("/api/tausch", json.dumps({"action": "start", "name": name, "size": len(b), "area": area, "folder": folder, "lang": "de"}).encode()))
        req("/api/tausch/chunk?id=%s&off=0" % s["id"], b, "application/octet-stream")
        f = json.loads(req("/api/tausch", json.dumps({"action": "finish", "id": s["id"], "lang": "de"}).encode()))
        assert f.get("ok"), f

    def lst(area, folder=""):
        return json.loads(req("/api/tausch?area=%s&folder=%s" % (area, folder)))

    try:
        for _ in range(240):
            if p.poll() is not None:
                raise SystemExit("MoveEye beendet:\n" + open(os.path.join(tmp, "mw.log")).read()[-3000:])
            try:
                urllib.request.urlopen(base + "/manifest.webmanifest", timeout=2)
                break
            except Exception:
                time.sleep(1)
        req("/api/tausch", json.dumps({"action": "mkdir", "name": "Touren", "lang": "de"}).encode())
        up("Bergtal_Rundweg.gpx", gpx("Bergtal Rundweg"), folder="Touren")
        up("Gipfel_Ost.gpx", gpx("Gipfel Ost", 12), folder="Touren")
        up("Notizen.txt", "Wasserstelle 200 m".encode())
        exp = json.loads(req("/api/settings/export"))
        exp.setdefault("cfg", {})["lang"] = "de"
        up("moveeye_einstellungen_alt.json", json.dumps(exp).encode(), area="mine")
        req("/api/touren/import?lang=de&name=Weg.gpx", gpx("Weg am See", 10), "application/octet-stream")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for W, H, tag in ((390, 844, "handy"), (1280, 860, "pc")):
                print(f"B) Browser {tag}", flush=True)
                cx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2 if W < 500 else 1, locale="de-CH", color_scheme="dark",
                                    http_credentials={"username": "admin", "password": PW}, has_touch=W < 500, is_mobile=W < 500)
                pg = cx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))

                def shot(name):
                    if bilder:
                        pg.wait_for_timeout(400)
                        pg.screenshot(path=os.path.join(bilder, f"{name}_{tag}.png"))

                def clean():
                    pg.evaluate("document.querySelectorAll('#g2-ov,.g2m,#gw,#fx-dim').forEach(e => e.remove())")

                # Live: nothing of the backpack visible
                pg.goto(base + "/", wait_until="domcontentloaded")
                pg.wait_for_function("window.mwRucksack && document.querySelector('.rk-btn')", timeout=30000)
                vis = pg.evaluate("[...document.querySelectorAll('.rk-btn,.rk-mini')].filter(b => b.offsetParent !== null).length")
                ok(vis == 0, f"Live: kein 🎒 sichtbar ({vis})")
                # settings: save into the backpack
                pg.goto(base + "/settings", wait_until="domcontentloaded")
                pg.wait_for_timeout(2500)
                for _k in range(3):
                    try:
                        pg.get_by_role("button", name="Überspringen").first.click(timeout=1500)
                        pg.wait_for_timeout(300)
                    except Exception:
                        break
                clean()
                pg.evaluate("""() => { const a = document.querySelector('a[href="/api/settings/export"]'); const d = a.closest('details'); if (d) d.open = true;
                    let p = d && d.parentElement; while (p) { if (p.tagName === 'DETAILS') p.open = true; p = p.parentElement; }
                    a.scrollIntoView({block: 'center'}); }""")
                sb = pg.locator('a[href="/api/settings/export"] + button.rk-btn')
                ok(sb.count() == 1 and "In den Rucksack" in sb.inner_text(), "Einstellungen: Knopf «🎒 In den Rucksack»")
                pb = pg.locator('button.rk-btn[data-rk-for="imp-file"]')
                ok(pb.count() == 1 and "Aus dem Rucksack" in pb.inner_text(), "Einstellungen: Knopf «🎒 Aus dem Rucksack»")
                shot("1_einstellungen_knoepfe")
                sb.evaluate("b => b.click()")
                pg.wait_for_selector("#rk-ov .rk-form")
                ok(pg.locator("#rk-ov select").is_disabled() and "Meine Dateien" in pg.locator("#rk-ov select").inner_text(), "privat: nur «Meine Dateien»")
                shot("2_einstellungen_speichern")
                pg.locator("#rk-ov .rk-ft button:not(.sec)").click()
                pg.wait_for_selector("#rk-toast", timeout=30000)
                ok("gespeichert" in pg.locator("#rk-toast").inner_text(), "Toast «Im Rucksack gespeichert»")
                mine = [f["name"] for f in lst("mine")["files"]]
                ok(sum(n.startswith("moveeye_einstellungen") for n in mine) >= 2, f"Einstellungen in «Meine Dateien»: {mine}")
                # settings: load from the backpack (the page's own import runs)
                pg.evaluate("window.__imp = []; const o = window.importSettings; window.importSettings = f => window.__imp.push(f && f.name)")
                pb.evaluate("b => b.click()")
                pg.wait_for_selector("#rk-ov .rk-row")
                pg.locator(".rk-tabs button", has_text="Meine Dateien").click()
                pg.locator(".rk-row", has_text="moveeye_einstellungen_alt.json").click()
                shot("3_einstellungen_waehlen")
                pg.locator("#rk-ov .rk-ft button:not(.sec)").click()
                pg.wait_for_function("window.__imp.length > 0", timeout=15000)
                ok(pg.evaluate("window.__imp[0]") == "moveeye_einstellungen_alt.json", "Einstellungen aus dem Rucksack an importSettings")
                # a file field without a button next to it: the chooser
                pg.evaluate("""() => { const i = document.createElement('input'); i.type = 'file'; i.accept = 'image/*'; i.id = 'rk-test-f'; window.__ch = 0;
                    i.onchange = () => window.__ch++; document.body.appendChild(i); i.hidden = true; i.click(); }""")
                pg.wait_for_selector("#rk-ov .rk-ch")
                ok(pg.locator("#rk-ov .rk-ch button").count() == 2, "Feld ohne Knopf: «Von diesem Gerät / Aus dem Rucksack»")
                shot("4_auswahl")
                pg.keyboard.press("Escape")
                ok(pg.locator("#rk-ov").count() == 0, "Esc schliesst")
                # tours: import a GPX from the backpack, save a tour as GPX
                pg.goto(base + "/karte", wait_until="domcontentloaded")
                pg.wait_for_selector("#kt-imp", timeout=30000)
                clean()
                kb = pg.locator('button.rk-btn[data-rk-for="kt-file"]')
                ok(kb.count() == 1, "Touren: Knopf «🎒 Aus dem Rucksack»")
                n0 = len(json.loads(req("/api/touren")).get("tours", []))
                kb.evaluate("b => { b.scrollIntoView({block: 'center'}); b.click(); }")
                pg.wait_for_selector("#rk-ov .rk-row")
                ok(pg.locator("#rk-ov .rk-chips button.on", has_text="GPX").count() == 1, "Filter GPX · KML · ZIP aktiv")
                pg.locator(".rk-row", has_text="Touren").click()
                pg.wait_for_selector(".rk-row:has-text('Gipfel_Ost.gpx')")
                pg.locator(".rk-row", has_text="Gipfel_Ost.gpx").click()
                shot("5_touren_waehlen")
                pg.locator("#rk-ov .rk-ft button:not(.sec)").click()
                t0 = time.time()
                while time.time() - t0 < 15 and len(json.loads(req("/api/touren")).get("tours", [])) <= n0:
                    time.sleep(0.5)
                ok(len(json.loads(req("/api/touren")).get("tours", [])) == n0 + 1, "Tour aus dem Rucksack importiert")
                pg.wait_for_selector("a[href$='.gpx'] + .rk-mini, a[href$='.gpx'] + .rk-btn", timeout=15000)
                b = pg.locator("a[href$='.gpx'] + .rk-mini, a[href$='.gpx'] + .rk-btn").first
                b.evaluate("b => { b.scrollIntoView({block: 'center'}); b.click(); }")
                pg.wait_for_selector("#rk-ov .rk-form")
                pg.locator("#rk-ov select").select_option("all|Touren")
                shot("6_tour_speichern")
                pg.locator("#rk-ov .rk-ft button:not(.sec)").click()
                pg.wait_for_selector("#rk-toast", timeout=30000)
                ok(len(lst("all", "Touren")["files"]) >= 3, "Tour als GPX im Ordner «Touren»")
                ok(not errs, f"keine JS-Fehler: {errs[:3]}")
                cx.close()
                for f in lst("all", "Touren")["files"]:
                    if f["name"] not in ("Bergtal_Rundweg.gpx", "Gipfel_Ost.gpx"):
                        req("/api/tausch", json.dumps({"action": "delete", "id": f["id"], "lang": "de"}).encode())
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder")
    a = ap.parse_args()
    d = a.datei or neueste()
    teil_a(d)
    if a.browser:
        if a.bilder:
            os.makedirs(a.bilder, exist_ok=True)
        teil_b(d, a.bilder)
    print(f"{N['ok']} gut, {len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)
