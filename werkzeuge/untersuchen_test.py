#!/usr/bin/env python3
"""Test «🔍 Untersuchen» (MoveEye Teil 639zze) – ohne Kamera, ohne echte Modelle:

  A) im eigenen Prozess: Bereich / Antippen, Ergebnis-JSON, Speichern im Datentausch-Ordner «Funde», besetzt (nur eine
     Untersuchung zugleich), Zeitlimit (die Seite bekommt eine Antwort, «besetzt» wird frei).
  B) MoveEye ohne Fenster mit der Demo-Kamera (Kopf = Demo, Weitwinkel «usb:0», Wärmebild «usb:1» - in der Demo ist jede Quelle
     das Demo-Bild), BioCLIP + Artinfos als Ersatz von einem lokalen Testserver (feste Prüfsummen wie echt): /api/untersuchen
     (ganzes Bild, Bereich, Kopf drehen), Rechte (Kind ohne Kopf, «Eigene Rechte» ohne Live, Familie mit Kopf), Gast (nie den
     Kopf, kein Hochladen), Hochladen eines Fotos (auch kein Foto / zu gross), Wärmebild (keine Arten, Hinweis), Weitwinkel,
     besetzt, Modell laden nur Admin, Funde (Bild + JSON mit Zeit, Ort, Objekten, Arten).
  C) --browser: Live-Seite (Handy 390 × 844 und PC): 🔍, Rahmen ziehen, Ergebnis über dem Bild, Beschriftung antippen =
     Artinfo-Karte, 📷 Foto untersuchen, Gast-Seite; keine JavaScript-Fehler. --bilder ORDNER: untersuchen_*.png

  python3 werkzeuge/untersuchen_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import hashlib
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
sys.path.insert(0, HIER)
from bioclip_test import Srv, bild, fake_info, fake_model, fake_tables   # noqa: E402

# Pixelbomben (3.68.1): nur der Dateikopf, er nennt riesige Masse - wie _bk_bomb() in quelle/639zzf
PNG_BOMB = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR" + (65000).to_bytes(4, "big") * 2 + b"\x08\x02\x00\x00\x00" + b"\0" * 4
JPG_HEAD = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xc0\x00\x11\x08"
JPG_BOMB = JPG_HEAD + (9000).to_bytes(2, "big") * 2 + b"\x03" + b"\0" * 9
JPG_LANG = JPG_HEAD + (100).to_bytes(2, "big") + (30000).to_bytes(2, "big") + b"\x03" + b"\0" * 9
WEBP_BOMB = b"RIFF\0\0\0\0WEBPVP8X\x0a\0\0\0\0\0\0\0" + (16383).to_bytes(3, "little") * 2

FEHLER = []
N = {"ok": 0}
PW = "Unters-" + base64.b16encode(os.urandom(5)).decode().lower()


def ok(cond, what):
    if cond:
        N["ok"] += 1
        print("  ✓ " + what, flush=True)
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    print("A) im eigenen Prozess", flush=True)
    home = tempfile.mkdtemp(prefix="mw_unt_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_unt_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    CFG, TZ, UNT = ns["CFG"], ns["TZ"], ns["UNT"]
    root = tempfile.mkdtemp(prefix="mw_unt_root_")
    TZ["root_test"] = root
    CFG.update(tausch_on=True, tausch_free_gb=0.1, lang="de")
    ns["tausch_disk_free"] = lambda p: 100 * ns["TZ_GB"]
    ns["tausch_thumb_queue"] = lambda fid: None
    ok(ns["unt_selftest"]().startswith("region"), "Selbsttest unt_selftest")
    ok(ns["unt_box"]([0.02, 0.02]) == [0.0, 0.0, 0.3, 0.3], "Antippen am Rand: Bereich bleibt im Bild")
    import numpy as np
    import cv2
    img = np.full((240, 320, 3), 120, np.uint8)
    ns["unt_frame"] = lambda cam: (time.sleep(0.4), (img.copy(), ""))[1]   # slow enough for the «busy» check
    ns["unt_detect"] = lambda im, thermal=False, warm=True: [{"kind": "animal", "lab": "dog", "conf": 0.9, "box": [0.1, 0.1, 0.2, 0.2]}]
    ns["bio_installed"] = lambda: False
    who = {"admin": False, "live": True, "head": False, "key": "anna", "name": "Anna"}
    okk, err, jid = ns["unt_start"](who, "head", [0.5, 0.5, 0.4, 0.4], True, "de")
    ok(okk and jid, "Untersuchung startet")
    okk2, err2, _j = ns["unt_start"](who, "head", None, False, "de")
    ok(not okk2 and err2 == "busy", "zweite Untersuchung zugleich: besetzt")
    for _i in range(100):
        if UNT["jobs"][jid]["st"] != "run":
            break
        time.sleep(0.05)
    st = ns["unt_state"](jid, who, "de")
    ok(st["st"] == "done" and not st["aimed"] and st["items"][0]["label"] == "Hund" and st["nobio"] and "Administrator" in st["note"],
       f"Ergebnis: Hund, ohne Kopf (kein Recht), BioCLIP fehlt ({st.get('note')})")
    ok(st["items"][0]["box"] == [0.54, 0.54, 0.08, 0.08], f"Rahmen im Bereich -> Koordinaten des ganzen Bildes {st['items'][0]['box']}")
    fs = [m for m in TZ["files"].values() if m.get("folder") == "Funde"]
    ok(len(fs) == 2 and any(x["name"] == "Funde" for x in TZ["folders"]) and st["saved"]["msg"].startswith("Gespeichert"), "Bild + JSON im Ordner «Funde»")
    js = [m for m in fs if m["name"].endswith(".json")]
    r = json.load(open(os.path.join(root, "f", js[0]["id"] + ".bin"), encoding="utf-8")) if js else {}
    ok(r.get("objects", [{}])[0].get("label") == "dog" and r.get("region") == [0.5, 0.5, 0.4, 0.4] and "time" in r and r.get("species") == [],
       f"JSON: Objekte, Bereich, Zeit ({str(r)[:120]})")
    ok(not UNT["busy"], "danach wieder frei")
    ok("Hund" in ns["unt_text"](st, "de"), "Ergebnis als Text (Fenster)")
    # time limit: a hanging camera - the page still gets an answer, «busy» clears
    ns["UNT_TIMEOUT_S"] = 0.3
    ns["unt_frame"] = lambda cam: (time.sleep(3), (img, ""))[1]
    okk, err, jid = ns["unt_start"](who, "head", None, False, "de")
    t0 = time.time()
    while UNT["jobs"][jid]["st"] == "run" and time.time() - t0 < 30:
        time.sleep(0.1)
    st = ns["unt_state"](jid, who, "de")
    ok(st["st"] == "err" and "Zeitüberschreitung" in st["msg"] and not UNT["busy"], f"Zeitlimit: Fehler, wieder frei ({st.get('msg')}, {time.time() - t0:.1f} s)")
    shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
WRAP = r'''
import json, os, sys
D = sys.argv[1]; P = json.loads(os.environ["MW_UNT_PATCH"])
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
for _w, _p in MW_P["files"].items():
    BIO_FILES[_w].update(_p)
BIO_BASE["url"] = MW_P["base"]
BIO_INFO.update(MW_P["info"]); BIO_INFO_BASE["url"] = MW_P["info_base"]
_dr = DemoSource.read
def _dr_fix(self):                       # the demo clock stands in the second 16 of its cycle: the person walks past the tent
    self.t0 = time.time() - 16.0
    return _dr(self)
DemoSource.read = _dr_fix
"""
src = src[:i] + "\nMW_P = json.loads(os.environ['MW_UNT_PATCH'])\n" + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
'''


def teil_b(datei, browser, bilder):
    print("B) MoveEye mit Demo-Kamera, Ersatz-Modellen", flush=True)
    srv = Srv()
    emb, lab = fake_tables()
    model, info = fake_model(), fake_info()
    pin = lambda n, b: {"name": n, "size": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    files = {"model": ("bioclip-1-bild-fp32.onnx", model), "emb": ("bioclip-1-arten.npy", emb), "labels": ("bioclip-1-arten.json", lab)}
    patch = {"files": {w: pin(n, b) for w, (n, b) in files.items()}, "base": srv.url + "m/",
             "info": {"size": len(info), "sha256": hashlib.sha256(info).hexdigest()}, "info_base": srv.url + "i/"}
    for w, (n, b) in files.items():
        srv.files["/m/" + n] = b
    srv.files["/i/bioclip-info-1.sqlite"] = info
    tmp = tempfile.mkdtemp(prefix="mw_unt_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": ["usb:0"], "kopf_ov": "usb:0", "thermal_source": "usb:1", "thermal_on": False,
          "cam_fov": {"usb:0": {"model": "own", "deg": 102}}, "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "tausch_free_gb": 0.1, "news_popup": False, "latitude": 46.95, "longitude": 7.45}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_UNT_PATCH=json.dumps(patch))
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW), raw=None, ctype="application/json"):
        h = dict(basic(*user)) if user else {}
        h["Content-Type"] = ctype
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None), headers=h)
        try:
            with op.open(r, timeout=60) as x:
                b = x.read()
                return x.status, (json.loads(b) if x.headers.get_content_type() == "application/json" else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b)
            except ValueError:
                return e.code, b

    def warten(jid, user=("admin", PW), g=None, limit=90):
        t0 = time.time()
        while time.time() - t0 < limit:
            c, j = req((g or "/api/untersuchen") + f"?id={jid}&lang=de", user=user)
            if j.get("st") != "run":
                return j
            time.sleep(0.3)
        return {"st": "timeout"}

    def unters(d, user=("admin", PW), g=None):
        for _i in range(60):
            c, j = req(g or "/api/untersuchen", dict(d, lang="de"), user)
            if c != 409:
                break
            time.sleep(0.5)
        return c, j

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        for n, r in {"Anna": "family", "Kim": "kid", "Cus": "custom"}.items():
            req("/api/users", {"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        req("/api/users", {"action": "update", "name": "Cus", "perms": ["rec"]})
        A, K, C = ("Anna", "anna-pass-1"), ("Kim", "kim-pass-1"), ("Cus", "cus-pass-1")
        c, j = req("/api/untersuchen?lang=de")
        ok(c == 200 and j["cams"]["head"] and j["head"] and not j["bio"], f"Zustand: Kopf-Kamera, Recht Kopf, BioCLIP noch nicht da ({j})")
        print("B) ohne BioCLIP, Rechte", flush=True)
        c, j = unters({"cam": "head", "box": None})
        r = warten(j.get("id"))
        ok(r.get("st") == "done" and r.get("nobio") and r.get("can_load") and r["saved"]["msg"].startswith("Gespeichert"),
           f"ganzes Bild ohne BioCLIP: Ergebnis, Hinweis, gespeichert ({r.get('note')}, {len(r.get('items') or [])} Funde)")
        ok(any(i["kind"] == "person" for i in r.get("items") or []), "Demo: Person gefunden (KI)")
        ok(req("/api/untersuchen", {"cam": "head", "box": [0.2, 0.2, 0.3, 0.3], "aim": True}, K)[0] == 403, "Kind: Kopf drehen verboten")
        c, j = unters({"cam": "head", "box": [0.2, 0.2, 0.3, 0.3]}, K)
        ok(c == 200 and warten(j["id"], K).get("st") == "done", "Kind: ohne Kopf erlaubt")
        ok(req("/api/untersuchen", {"cam": "head"}, C)[0] == 403 and req("/api/untersuchen?lang=de", user=C)[0] == 403, "Eigene Rechte ohne Live: nein")
        ok(req("/api/untersuchen", {"action": "bio_load"}, A)[0] == 403, "Modell laden: nur Admin")
        ok(req("/api/untersuchen?lang=de", user=None)[0] == 401, "ohne Anmeldung: 401")
        c, j = req("/api/untersuchen", {"action": "bio_load"})
        t0 = time.time()
        while time.time() - t0 < 60 and not req("/api/untersuchen?lang=de")[1].get("bio"):
            time.sleep(0.3)
        ok(req("/api/untersuchen?lang=de")[1].get("bio"), f"Admin lädt BioCLIP (+ Artinfos) ({time.time() - t0:.1f} s)")
        print("B) mit BioCLIP: Bereich, Kopf, Wärmebild, Weitwinkel, Hochladen, Gast", flush=True)
        c, j = unters({"cam": "head", "box": [0.3, 0.3, 0.4, 0.4], "aim": True}, A)
        r = warten(j["id"], A)
        sp = [i for i in r.get("items") or [] if i["kind"] == "species"]
        ok(r.get("st") == "done" and r.get("aimed") and sp and sp[0]["res"]["top"] and r["box"], f"Familie: Bereich, Kopf gedreht, Art bestimmt ({sp[0]['label'] if sp else '-'})")
        ok(sp and sp[0]["res"].get("foot", "").startswith("Nur zur Orientierung") and sp[0]["res"]["top"][0].get("info") is not None, "Art: Artinfo-Karte + Hinweis wie im Datentausch")
        req("/api/set", {"key": "thermal_on", "value": True})
        time.sleep(2)
        c, j = unters({"cam": "thermal", "box": None})
        r = warten(j["id"])
        ok(r.get("st") == "done" and not [i for i in r.get("items") or [] if i["kind"] == "species"] and "Wärmebild" in (r.get("note") or ""),
           f"Wärmebild: keine Arten, Hinweis ({r.get('st')} {r.get('note') or r.get('msg')})")
        req("/api/set", {"key": "thermal_on", "value": False})
        c, j = unters({"cam": "wide", "box": None})
        r = warten(j["id"])
        ok(r.get("st") == "done" and r.get("cam") == "wide", f"Weitwinkel ({r.get('st')} {r.get('msg') or ''})")
        jpg = bild((0.98, 0.84, 0.10), 800, 600)
        c, j = req("/api/untersuchen/upload?lang=de", raw=jpg, user=A, ctype="application/octet-stream")
        r = warten(j.get("id"), A)
        sp = [i for i in r.get("items") or [] if i["kind"] == "species"]
        ok(r.get("st") == "done" and r.get("src") == "upload" and sp and "Löwenzahn" in sp[0]["label"], f"Foto hochladen: Art ({sp[0]['label'] if sp else r})")
        c, b = req(f"/api/untersuchen/img/{j.get('id')}.jpg", user=A)
        ok(c == 200 and bytes(b[:2]) == b"\xff\xd8", "Bild des Ergebnisses abrufbar")
        ok(req("/api/untersuchen/upload?lang=de", raw=b"kein bild", user=A, ctype="application/octet-stream")[0] == 400, "kein Foto: abgewiesen")
        ok(req("/api/untersuchen/upload?lang=de", raw=b"\xff\xd8" + b"0" * (16 * 1024 * 1024), user=A, ctype="application/octet-stream")[0] == 413, "zu gross: vor dem Lesen abgewiesen")
        # 3.68.1: winzige Dateien mit riesigen Massen im Kopf - abgewiesen, ohne zu dekodieren (639zzf; Speicher bleibt klein)
        for name, bomb in (("PNG 65000²", PNG_BOMB), ("JPEG 9000²", JPG_BOMB), ("WebP VP8X 16384²", WEBP_BOMB), ("JPEG 30000×100", JPG_LANG)):
            t0 = time.time()
            c, j = req("/api/untersuchen/upload?lang=de", raw=bomb, user=A, ctype="application/octet-stream")
            ok(c == 400 and time.time() - t0 < 3.0, f"Pixelbombe {name} ({len(bomb)} Bytes): abgewiesen ({c}, {time.time() - t0:.1f} s)")
        c, j = req("/api/guest", {"action": "create", "hours": 2})
        gp = req("/api/guest")[1]["path"]
        c, j = unters({"cam": "head", "box": [0.3, 0.3, 0.3, 0.3], "aim": True}, None, gp + "/untersuchen")
        r = warten(j.get("id"), None, gp + "/untersuchen")
        ok(r.get("st") == "done" and not r.get("aimed"), "Gast: Ausschnitt ja, Kopf nie")
        ok(req(gp + "/untersuchen/upload", raw=jpg, user=None, ctype="application/octet-stream")[0] in (404, 405), "Gast: kein Hochladen")
        c, j = req("/api/untersuchen", {"cam": "head", "lang": "de"})
        c2, j2 = req("/api/untersuchen", {"cam": "head", "lang": "de"})
        ok(c == 200 and c2 == 409 and j2.get("st") == "wait", "nur eine Untersuchung zugleich (zweite: «gleich weiter»)")
        warten(j.get("id"))
        c, j = req("/api/tausch?area=all&folder=Funde&lang=de")
        fs = j.get("files") or []
        js = [f for f in fs if f["name"].endswith(".json")]
        ok(len([f for f in fs if f["name"].endswith(".jpg")]) >= 5 and len(js) >= 5, f"Datentausch «Funde»: {len(fs)} Dateien")
        c, b = req(f"/tausch/dl/{js[0]['id']}") if js else (0, b"{}")
        r = json.loads(b) if c == 200 else {}
        ok(r.get("location", {}).get("lat") == 46.95 and "objects" in r and "time" in r, f"JSON mit Ort, Zeit, Objekten ({str(r)[:100]})")
        if browser:
            teil_c(base, gp, bilder, tmp)
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        if "Traceback" in log:
            print(log[-2500:])
            ok(False, "Fehler im Protokoll von MoveEye")
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- C
def teil_c(base, gp, bilder, tmp):
    from playwright.sync_api import sync_playwright
    print("C) Browser", flush=True)
    os.makedirs(bilder, exist_ok=True)
    up = os.path.join(tmp, "Wiese.jpg")   # wird mit tmp weggeräumt
    open(up, "wb").write(bild((0.98, 0.84, 0.10), 1200, 900))
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for name, vp, mob in (("handy", {"width": 390, "height": 844}, True), ("desktop", {"width": 1366, "height": 860}, False)):
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                 http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.removeItem('mw-view3');localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\"]')}catch(e){}")
            ctx.add_init_script("try{localStorage.setItem('mw-lv-knoepfe','1')}catch(e){}")   # 639zzj: buttons / tiles always shown (tested in live_sauber_test.py)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + "/", wait_until="domcontentloaded")
            pg.wait_for_function("() => { const v = document.getElementById('video'); return v && v.naturalWidth > 0 && document.getElementById('lv-b-unt'); }", timeout=30000)
            pg.wait_for_timeout(800)
            pg.click("#lv-b-unt")
            pg.wait_for_selector("#unt-ov.sel", timeout=5000)
            r = pg.locator("#unt-ov").bounding_box()
            pg.mouse.move(r["x"] + r["width"] * 0.12, r["y"] + r["height"] * 0.35); pg.mouse.down()       # around the person at the tent
            pg.mouse.move(r["x"] + r["width"] * 0.62, r["y"] + r["height"] * 0.97, steps=6); pg.mouse.up()
            pg.wait_for_timeout(300)
            ok("Diesen Bereich untersuchen?" in pg.inner_text("#unt-bar") and pg.locator("#unt-ov .ub.region").count() == 1, f"{name}: Rahmen gezogen, Frage")
            ok(pg.locator("#unt-aim").count() == 1, f"{name}: «Zuerst den Kopf dorthin drehen» (Admin)")
            pg.screenshot(path=os.path.join(bilder, f"untersuchen_auswahl_{name}.png"))
            pg.locator("#unt-bar button", has_text="Untersuchen").click()
            pg.wait_for_selector("#unt-ov .ub .ul", timeout=60000); pg.wait_for_timeout(600)
            txt = pg.inner_text("#unt-bar")
            ok("Fund" in txt and "Gespeichert im Datentausch" in txt and "Tox Info Suisse 145" in txt, f"{name}: Ergebnis-Leiste ({txt[:90]!r})")
            pg.screenshot(path=os.path.join(bilder, f"untersuchen_ergebnis_{name}.png"))
            pb = pg.evaluate("() => { const b = document.querySelector('#unt-ov .ub.person'); return b ? [parseFloat(b.style.left), parseFloat(b.style.top), parseFloat(b.style.width), parseFloat(b.style.height)] : null; }")
            ok(pb and 10 < pb[0] < 40 and pb[2] > 1.5 and pb[3] > 10, f"{name}: Person-Rahmen dort, wo die Person steht ({pb})")
            sl = pg.locator("#unt-ov .ub.species .ul")
            ok(sl.count() >= 1, f"{name}: Art-Beschriftung über dem Bild")
            if sl.count():
                sl.first.click()
                pg.wait_for_selector("#unt-host .tz-bio .row.first", timeout=5000)
                d = pg.locator("#unt-host .tz-bio .row.first details.info summary")
                if d.count():
                    d.click()
                pg.wait_for_timeout(400)
                ok(pg.locator("#unt-host .tz-bio .row").count() >= 1 and "Tox Info Suisse 145" in pg.inner_text("#unt-host .tz-bio"),
                   f"{name}: Artinfo-Karte aus dem Overlay")
                pg.screenshot(path=os.path.join(bilder, f"untersuchen_karte_{name}.png"))
                pg.click("#unt-host .tz-bio .hd button")
            pg.locator("#unt-bar button", has_text="Schliessen").click(); pg.wait_for_timeout(200)
            ok(pg.locator("#unt-ov").count() == 0, f"{name}: Schliessen räumt das Bild")
            with pg.expect_file_chooser() as fc:
                pg.click("#lv-b-unt-up")
            fc.value.set_files(up)
            pg.wait_for_selector("#unt-up:not([hidden]) .ub .ul", timeout=60000); pg.wait_for_timeout(700)
            ok("Löwenzahn" in pg.inner_text("#unt-up"), f"{name}: Foto hochgeladen, Art erkannt")
            pg.screenshot(path=os.path.join(bilder, f"untersuchen_upload_{name}.png"))
            ok(not errs, f"{name}: keine JavaScript-Fehler {errs}")
            ctx.close()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
        ctx.add_init_script("try{localStorage.setItem('mw-tours-seen','[\"live\",\"guest\"]')}catch(e){}")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + gp, wait_until="domcontentloaded")
        pg.wait_for_function("() => { const v = document.getElementById('v'); return v && v.naturalWidth > 0 && document.getElementById('g-unt'); }", timeout=30000)
        pg.click("#g-unt"); pg.wait_for_selector("#unt-bar")
        ok(pg.locator("#unt-aim").count() == 0, "Gast: kein «Kopf drehen»")
        pg.locator("#unt-bar button", has_text="Ganzes Bild").click()
        pg.wait_for_selector("#unt-ov .ub .ul", timeout=60000); pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(bilder, "untersuchen_gast_handy.png"))
        ok(not errs, f"Gast: keine JavaScript-Fehler {errs}")
        ctx.close()
        br.close()


def main():
    ap = argparse.ArgumentParser(description="Test «🔍 Untersuchen» (639zze)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "untersuchen_bilder"))
    a = ap.parse_args()
    datei = a.datei or neueste()
    t0 = time.time()
    teil_a(datei)
    teil_b(datei, a.browser, a.bilder)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
