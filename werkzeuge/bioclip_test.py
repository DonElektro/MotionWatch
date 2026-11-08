#!/usr/bin/env python3
"""Test «🌿 Bestimmen» im Datentausch (MoveEye Teil 639zzd) – ohne Internet und ohne echtes Modell (für CI):

  A) im eigenen Prozess mit der gebauten Datei und dem Flask-Testclient:
     * ein kleines Ersatz-Modell (ONNX von Hand gebaut, dieselbe Schnittstelle wie BioCLIP: image [n,3,224,224] -> emb [n,D])
       mit einer Ersatz-Artenliste (Farben = Arten), geladen von einem lokalen Testserver mit festen Prüfsummen:
       verändert / zu gross -> abgelehnt, richtig -> geladen und geprüft; zu wenig freier Platz -> nicht geladen
     * Adresse /api/tausch/bio (GET / POST) und /g/<token>/tausch/bio/<id>: Rechte je Rolle (Kind nein, Freund / «Nur ansehen»
       ja), private Bilder nur für Besitzer + Admin, Gäste nur «Für alle», keine SVG / PDF, Gäste laden nie das Modell
     * der Rechen-Prozess (nice 10, onnxruntime): Ergebnis «Gemeiner Löwenzahn – Taraxacum officinale – … %», Pflanze / Tier /
       Pilz / Insekt, Zwischenspeicher pro Datei-Inhalt (zweites Mal und gleicher Inhalt unter anderem Namen ohne Rechnen),
       besetzt (ein Bild auf einmal), Zeitlimit (Prozess wird beendet, danach geht es wieder), Leerlauf beendet den Prozess,
       Ratenbremse, Schalter tausch_bio aus, Laufzeit fehlt (nur der Admin darf installieren), Löschen nur durch den Admin
  B) --browser: dieselbe App mit einem echten Server im Prozess, Playwright: Seite /tausch (Handy 390 × 844 und PC), 🌿 auf der
     Karte und «🌿 Bestimmen» in der Vorschau, Laden mit Fortschritt, Ergebnis, Gast-Seite; keine JavaScript-Fehler;
     --bilder ORDNER: Bildschirmfotos bioclip_*.png
  --echt ORDNER: dazu die echten Dateien aus dem Workflow «BioCLIP» (Modell wie in BIO_FILES, -arten.npy, -arten.json)
     über denselben Weg laden und rechnen; --fotos ORDNER (Gattung_art_N.jpg) misst Treffer und Zeit.

  python3 werkzeuge/bioclip_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--echt ORDNER [--fotos ORDNER]]
"""
import argparse
import base64
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
from piper_test import Srv, _f, _node, _s, _tensor, _valinfo   # noqa: E402  (tiny ONNX by hand + a test server with Range)

FEHLER = []
# schon vor 639zzd: ein Benutzer «Familie» bekommt auf jeder Seite 403 für /sx/ui.js und /fbx/ui.js (role_allows) - nicht von hier
KNOWN_403 = re.compile(r"status of 403|/(sx|fbx)/ui\.js")
N = {"ok": 0}
D = 16


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


# ---- the fake model: mean colour of the picture -> a fixed matrix -> D numbers (the interface of the real image encoder) -------
def fake_W():
    import numpy as np
    return np.random.RandomState(7).normal(size=(3, D)).astype(np.float32)


def fake_model():
    W = fake_W()
    ax = _f(5, 2, _s(1, "axes") + _f(20, 0, 7) + _f(8, 0, 2) + _f(8, 0, 3))
    kd = _f(5, 2, _s(1, "keepdims") + _f(20, 0, 2) + _f(3, 0, 0))
    nodes = [_node("ReduceMean", ["image"], ["m"], ax + kd), _node("MatMul", ["m", "W"], ["emb"])]
    inits = [_tensor("W", 1, [3, D], W.tobytes())]
    g = b"".join(_f(1, 2, n) for n in nodes) + _s(2, "fakebioclip") + b"".join(_f(5, 2, t) for t in inits)
    g += _f(11, 2, _valinfo("image", 1, ["n", 3, 224, 224])) + _f(12, 2, _valinfo("emb", 1, ["n", D]))
    return _f(1, 0, 8) + _s(2, "bioclip_test") + _f(7, 2, g) + _f(8, 2, _s(1, "") + _f(2, 0, 13))


MEAN, STD = (0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)
# colour (RGB 0..1) = species
ARTEN = [
    ((0.98, 0.84, 0.10), ["Plantae", "Tracheophyta", "Magnoliopsida", "Asterales", "Asteraceae", "Taraxacum", "officinale"]),
    ((0.95, 0.75, 0.15), ["Plantae", "Tracheophyta", "Magnoliopsida", "Asterales", "Asteraceae", "Taraxacum", "erythrospermum"]),
    ((0.95, 0.90, 0.20), ["Plantae", "Tracheophyta", "Magnoliopsida", "Ranunculales", "Ranunculaceae", "Ranunculus", "acris"]),
    ((0.25, 0.65, 0.20), ["Plantae", "Tracheophyta", "Magnoliopsida", "Rosales", "Urticaceae", "Urtica", "dioica"]),
    ((0.85, 0.40, 0.12), ["Animalia", "Chordata", "Mammalia", "Carnivora", "Canidae", "Vulpes", "vulpes"]),
    ((0.88, 0.10, 0.08), ["Animalia", "Arthropoda", "Insecta", "Coleoptera", "Coccinellidae", "Coccinella", "septempunctata"]),
    ((0.50, 0.33, 0.18), ["Fungi", "Basidiomycota", "Agaricomycetes", "Boletales", "Boletaceae", "Boletus", "edulis"]),
    ((0.20, 0.35, 0.90), ["Animalia", "Chordata", "Aves", "Passeriformes", "Paridae", "Cyanistes", "caeruleus"]),
]
NAMEN = {"Taraxacum officinale": {"de": "Gemeiner Löwenzahn", "en": "Common dandelion", "fr": "Pissenlit"},
         "Taraxacum erythrospermum": {"de": "Rotfrüchtiger Löwenzahn"}, "Ranunculus acris": {"de": "Scharfer Hahnenfuss"},
         "Urtica dioica": {"de": "Grosse Brennnessel"}, "Vulpes vulpes": {"de": "Rotfuchs", "en": "Red fox"},
         "Coccinella septempunctata": {"de": "Siebenpunkt-Marienkäfer"}, "Boletus edulis": {"de": "Steinpilz"},
         "Cyanistes caeruleus": {"de": "Blaumeise"}, "Taraxacum": {"de": "Löwenzahn"}, "Asteraceae": {"de": "Korbblütler"},
         "Canidae": {"de": "Hunde"}, "Boletaceae": {"de": "Dickröhrlingsverwandte"}}


def fake_tables():
    import io
    import numpy as np
    W = fake_W()
    E = []
    for c, _t in ARTEN:
        v = ((np.array(c, np.float32) - np.array(MEAN, np.float32)) / np.array(STD, np.float32)) @ W
        E.append(v / np.linalg.norm(v))
    b = io.BytesIO(); np.save(b, np.array(E, np.float16))
    lab = {"format": 1, "model": "test", "logit_scale": 9.0, "ranks": ["kingdom", "phylum", "class", "order", "family", "genus", "species"],
           "size": 224, "mean": list(MEAN), "std": list(STD), "n": len(ARTEN), "taxa": [t for _c, t in ARTEN], "names": NAMEN}
    return b.getvalue(), json.dumps(lab, ensure_ascii=False).encode()


def bild(rgb, w=640, h=480, muster=True):
    import cv2
    import numpy as np
    im = np.zeros((h, w, 3), np.uint8); im[:] = [int(255 * x) for x in rgb[::-1]]
    if muster:                                       # a little structure (the mean colour stays the same)
        for i in range(12):
            cv2.circle(im, (40 + i * 50, 240 + int(60 * np.sin(i))), 14, [min(255, int(255 * x) + 18) for x in rgb[::-1]], -1)
            cv2.circle(im, (60 + i * 50, 300 + int(60 * np.cos(i))), 14, [max(0, int(255 * x) - 18) for x in rgb[::-1]], -1)
    return cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()


def blume():
    """a picture for the screenshots: a yellow flower head on green (the mean colour is still «dandelion-like»)"""
    import cv2
    import numpy as np
    h, w = 900, 1200
    im = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    im[..., 1] = (120 + 60 * np.sin(xx / 37.0) * np.cos(yy / 53.0)).astype(np.uint8); im[..., 0] = 40; im[..., 2] = 60
    for r, col in ((380, (20, 200, 250)), (300, (10, 215, 255)), (200, (0, 190, 240)), (60, (0, 140, 200))):
        cv2.circle(im, (600, 450), r, col, -1)
    for a in range(0, 360, 9):
        x2, y2 = int(600 + 395 * np.cos(np.radians(a))), int(450 + 395 * np.sin(np.radians(a)))
        cv2.line(im, (600, 450), (x2, y2), (0, 175, 235), 7)
    return cv2.imencode(".jpg", cv2.GaussianBlur(im, (5, 5), 0), [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()


def laden(datei):
    home = tempfile.mkdtemp(prefix="mw_bio_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_bioclip_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *a, **k: None
    return ns, home


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei, echt="", fotos="", browser=False, bilder="", pins=False):
    ns, home = laden(datei)
    real = {w: dict(f) for w, f in ns["BIO_FILES"].items()}          # the pins of the program (before the test pins)
    CFG, TZ, BIO, BIO_DL = ns["CFG"], ns["TZ"], ns["BIO"], ns["BIO_DL"]
    GB = ns["TZ_GB"]
    root = tempfile.mkdtemp(prefix="mw_bio_root_")
    TZ["root_test"] = root
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_guest=True, tausch_push=False, tausch_bio=True, quiet_on=False,
               tausch_free_gb=0.1)                                # this test needs little room (the rule itself: below)
    ns["tausch_disk_free"] = lambda p: 100 * GB
    ns["BIO_IDLE_TICK"] = 0.3
    ADMIN_PW = "Admin-Pass-123"
    assert ns["web_pw_set"](ADMIN_PW)[0]
    users = {"Anna": "family", "Bob": "friend", "Vera": "view", "Kim": "kid", "Cus": "custom"}
    for n, r in users.items():
        okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live"]})          # own rights without file rights
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)
    H = {n: basic(n, n.lower() + "-pass-1") for n in users}
    H["admin"] = basic("admin", ADMIN_PW)
    PW = {n: n.lower() + "-pass-1" for n in users}

    def api(who, d, code=None):
        r = c.post("/api/tausch", json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def upload(who, name, data, area="all"):
        code, j = api(who, {"action": "start", "name": name, "size": len(data), "area": area, "folder": "", "lastmod": 1})
        if code != 200:
            return code, j
        uid, off = j["id"], 0
        while off < len(data):
            r = c.post(f"/api/tausch/chunk?id={uid}&off={off}", data=data[off:off + j["chunk"]], headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
            off = r.get_json()["have"]
        code, j = api(who, {"action": "finish", "id": uid})
        fid = j.get("file", {}).get("id", "")
        for _i in range(80):
            if TZ["files"].get(fid, {}).get("thumb") is not None:
                break
            time.sleep(0.05)
        return code, j

    def bio(who, fid, action="state", code=None, guest=None):
        if guest:
            r = c.post(f"/g/{guest}/tausch/bio/{fid}", json={"action": action}) if action != "state" else c.get(f"/g/{guest}/tausch/bio/{fid}")
        elif action == "state":
            r = c.get(f"/api/tausch/bio?id={fid}&lang=de", headers=H[who])
        else:
            r = c.post("/api/tausch/bio", json={"action": action, "id": fid, "lang": "de"}, headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def warten(who, fid, guest=None, limit=60.0):
        t0 = time.time()
        code, j = bio(who, fid, "start", guest=guest)
        while j.get("st") in ("run", "wait", "loading") and time.time() - t0 < limit:
            time.sleep(0.2)
            code, j = bio(who, fid, "state" if j.get("st") != "wait" else "start", guest=guest)
        return code, j

    srv = Srv()
    emb, lab = fake_tables()
    model = fake_model()
    pin = lambda name, b: {"name": name, "size": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    files = {"model": (ns["BIO_FILES"]["model"]["name"], model), "emb": ("bioclip-1-arten.npy", emb), "labels": ("bioclip-1-arten.json", lab)}
    for w, (n_, b_) in files.items():
        ns["BIO_FILES"][w] = pin(n_, b_)
        srv.files["/bioclip-1/" + n_] = b_
    ns["BIO_BASE"]["url"] = srv.url + "bioclip-1/"

    gelb, rot, braun = (0.98, 0.84, 0.10), (0.88, 0.10, 0.08), (0.50, 0.33, 0.18)
    _c, j = upload("Anna", "Wiese.jpg", bild(gelb)); fid = j["file"]["id"]
    _c, j = upload("Anna", "Kaefer.jpg", bild(rot)); rid = j["file"]["id"]
    _c, j = upload("Anna", "Pilz.jpg", bild(braun)); bid = j["file"]["id"]
    _c, j = upload("Anna", "Geheim.jpg", bild(gelb, muster=False), area="mine"); pid = j["file"]["id"]
    _c, j = upload("Anna", "Plan.svg", b'<svg xmlns="http://www.w3.org/2000/svg"/>'); sid = j["file"]["id"]
    _c, j = upload("Anna", "Notiz.txt", b"hallo"); tid = j["file"]["id"]
    ok(TZ["files"][fid].get("thumb") is True, "Vorschaubild des Testbilds gerechnet")
    ns["guest_set"]("create", 1)
    tok = CFG["guest_token"]

    print("A) vor dem Laden: Zustand, Rechte, Gäste", flush=True)
    code, j = bio("Anna", fid)
    ok(code == 200 and j.get("st") == "load" and j.get("can_dl") and not j.get("can_install") and "einmal BioCLIP" in j.get("msg", ""),
       f"Familie: «einmal laden» mit Grösse ({code} {j.get('st')} {j.get('msg', '')[:60]})")
    code, j = bio("admin", fid)
    ok(j.get("can_install") and j.get("can_delete"), "Admin darf installieren / löschen")
    code, j = bio(None, fid, guest=tok)
    ok(code == 200 and j.get("st") == "load" and not j.get("can_dl") and "noch nicht eingerichtet" in j.get("msg", ""), f"Gast: nicht eingerichtet ({j})")
    code, j = c.post(f"/g/{tok}/tausch/bio/{fid}", json={"action": "download"}).status_code, None
    ok(not BIO_DL["running"] and not os.path.isdir(os.path.join(home, "bioclip", "x")), "Gast löst nie das Laden aus")
    for who, want in (("Kim", 403), ("Cus", 403), ("Bob", 200), ("Vera", 200), ("admin", 200)):
        code, j = bio(who, fid)
        ok(code == want, f"{who}: /api/tausch/bio {code} statt {want}")
        code, j = bio(who, fid, "start")
        ok(code == want, f"{who}: start {code} statt {want}")
    ok(c.get(f"/api/tausch/bio?id={fid}").status_code == 401, "ohne Anmeldung -> 401")
    ok(bio("Bob", pid)[0] == 404 and bio("Vera", pid)[0] == 404, "privates Bild: Freund / «Nur ansehen» sehen es nicht")
    ok(bio("Anna", pid)[0] == 200 and bio("admin", pid)[0] == 200, "privates Bild: Besitzerin und Admin")
    ok(bio(None, pid, guest=tok)[0] == 404, "Gast: kein privates Bild")
    ok(bio(None, sid, guest=tok)[0] == 404, "Gast: kein SVG")
    code, j = bio("Anna", sid)
    ok(code == 400 and "Nur Bilder" in j.get("msg", ""), f"SVG: nur Bilder ({code})")
    ok(bio("Anna", tid)[0] == 400, "Text: nur Bilder")
    ok(bio("Anna", "0123456789abcdef")[0] == 404 and bio("Anna", "../../x")[0] == 404, "unbekannte / falsche Nummer -> 404")
    r = c.post("/api/tausch/bio", json={"action": "start", "id": fid}, headers=dict(H["Anna"], Origin="https://evil.example"))
    ok(r.status_code == 403, f"fremde Origin abgewiesen ({r.status_code})")
    lst = c.get("/api/tausch?area=all", headers=H["Bob"]).get_json()
    ok(lst.get("bio") is True, "Liste meldet «bio» (Knopf zeigen)")
    gl = c.get(f"/g/{tok}/tausch/list").get_json()
    ok(gl.get("bio") is True, "Gast-Liste meldet «bio»")

    print("A) Laden: Prüfsumme, Grösse, freier Platz", flush=True)
    srv.tamper.add("/bioclip-1/bioclip-1-arten.npy")
    BIO_DL.update(msg="")
    r_ = ns["bio_download"](wait=True)
    ok(not r_[0] and "checksum" in r_[1] and not ns["bio_installed"]() and not os.path.exists(ns["bio_path"]("emb") + ".part"),
       f"verändertes Modell abgelehnt, .part gelöscht ({r_[1]})")
    srv.tamper.clear()
    srv.extra = b"x" * 50
    r_ = ns["bio_download"](wait=True)
    ok(not r_[0] and ("too large" in r_[1] or "size" in r_[1]), f"zu grosse Datei abgelehnt ({r_[1]})")
    srv.extra = b""
    du = shutil.disk_usage
    shutil.disk_usage = lambda p: du(p)._replace(free=ns["bio_total"]() + 100)
    r_ = ns["bio_download"]()
    ok(not r_[0] and "free space" in r_[1], f"zu wenig Platz: nicht geladen ({r_[1]})")
    code, j = bio("Anna", fid, "download")
    ok(code == 400 and "Platz" in j.get("msg", ""), f"zu wenig Platz in der Seite ({j.get('msg')})")
    shutil.disk_usage = du
    if echt:
        for w, n_ in (("model", ns["BIO_FILES"]["model"]["name"]), ("emb", "bioclip-1-arten.npy"), ("labels", "bioclip-1-arten.json")):
            b_ = open(os.path.join(echt, n_), "rb").read()
            ns["BIO_FILES"][w] = pin(n_, b_)
            srv.files["/bioclip-1/" + n_] = b_
    if echt and pins:
        ok(all(ns["BIO_FILES"][w] == real[w] for w in real), "echt: Dateien = feste Werte in BIO_FILES (Grösse + sha256)")
    code, j = bio("Anna", fid, "download")
    ok(code == 200 and j.get("st") == "loading", f"Laden startet ({j.get('st')})")
    t0 = time.time()
    seen = set()
    while time.time() - t0 < 120:
        seen.add(bio("Anna", fid)[1].get("st"))
        if ns["bio_installed"]():
            break
        time.sleep(0.05)
    ok(ns["bio_installed"](), f"geladen und geprüft ({time.time() - t0:.1f} s, Zustände {sorted(x for x in seen if x)})")

    print("A) Rechnen, Ergebnis, Zwischenspeicher", flush=True)
    calls = {"n": 0}
    real_infer = ns["bio_infer"]

    def counting(img):
        calls["n"] += 1
        return real_infer(img)
    ns["bio_infer"] = counting
    if not echt:
        t0 = time.time()
        code, j = warten("Anna", fid)
        res = j.get("res") or {}
        top = res.get("top") or [{}]
        ok(j.get("st") == "done" and top[0].get("sci") == "Taraxacum officinale" and top[0].get("name") == "Gemeiner Löwenzahn",
           f"Ergebnis: {res.get('line')} ({time.time() - t0:.1f} s)")
        ok(re.fullmatch(r"\d{1,3}\u00a0%", top[0].get("pct", "")) and top[0].get("group_t") == "Pflanze" and top[0].get("rank_t") == "Art"
           and top[0].get("family_name") == "Korbblütler" and len(top) == 3, f"Prozent, Pflanze, Art, Familie ({top[0]})")
        ok(re.match(r"Gemeiner Löwenzahn – Taraxacum officinale – \d+\u00a0%", res.get("line", "")), "Zeile «Gemeiner Löwenzahn – Taraxacum officinale – NN %»")
        p_ = BIO.get("proc")
        ok(p_ is not None and p_.poll() is None, "Rechen-Prozess läuft (warm)")
        if p_ is not None and hasattr(os, "getpriority"):
            try:
                ok(os.getpriority(os.PRIO_PROCESS, p_.pid) >= 10 or not shutil.which("nice"), "Rechen-Prozess mit nice 10")
            except OSError:
                pass
        n0 = calls["n"]
        code, j = warten("Bob", fid)
        ok(j.get("st") == "done" and j["res"].get("cached") and calls["n"] == n0, "zweites Mal (anderer Benutzer): aus dem Zwischenspeicher")
        _c, j2 = upload("Anna", "Wiese_Kopie.jpg", bild(gelb))
        code, j = warten("Anna", j2["file"]["id"])
        ok(j.get("st") == "done" and j["res"].get("cached") and calls["n"] == n0, "gleicher Inhalt unter anderem Namen: nicht nochmals gerechnet")
        ok(len(glob.glob(os.path.join(home, "bioclip", "cache", "*.json"))) >= 1, "Zwischenspeicher auf der Karte")
        code, j = warten(None, rid, guest=tok)
        top = (j.get("res") or {}).get("top") or [{}]
        ok(j.get("st") == "done" and top[0].get("sci") == "Coccinella septempunctata" and top[0].get("group_t") == "Insekt",
           f"Gast bestimmt ein Bild «Für alle»: {(j.get('res') or {}).get('line')}")
        ok("by" not in json.dumps(j) and "owner" not in json.dumps(j), "Gast: keine Namen der Hochlader")
        code, j = bio("admin", rid)
        ok(j.get("st") == "done", "Ergebnis des Gasts danach für alle da")
        code, j = bio(None, rid, "download", guest=tok)
        ok(j.get("st") == "done", "Gast: «download» = nur ansehen")

        print("A) besetzt, Zeitlimit, Leerlauf, Ratenbremse, Schalter", flush=True)
        BIO["job"] = "ffffffffffffffff"
        code, j = bio("Anna", bid, "start")
        ok(j.get("st") == "wait" and "anderes Bild" in j.get("msg", ""), f"besetzt: «gleich weiter» ({j.get('st')})")
        BIO["job"] = ""
        ns["BIO_TIMEOUT_S"] = 0.0
        code, j = warten("Anna", bid)
        ok(j.get("st") == "err" and "Zeitüberschreitung" in j.get("msg", "") and BIO.get("proc") is None,
           f"Zeitlimit: Fehler, Prozess beendet ({j.get('msg')})")
        ns["BIO_TIMEOUT_S"] = 60.0
        code, j = warten("Anna", bid)
        top = (j.get("res") or {}).get("top") or [{}]
        ok(j.get("st") == "done" and top[0].get("sci") == "Boletus edulis" and top[0].get("group_t") == "Pilz", f"danach wieder: {(j.get('res') or {}).get('line')}")
        ns["BIO_IDLE_S"] = 0.5
        BIO["last"] = 0.0
        t0 = time.time()
        while BIO.get("proc") is not None and time.time() - t0 < 25:
            time.sleep(0.2)
        ok(BIO.get("proc") is None, f"Leerlauf: Prozess beendet, Modell frei ({time.time() - t0:.1f} s)")
        ns["BIO_IDLE_S"] = 600
        ns["BIO_RATE"] = (1, 1)
        TZ["rate"].clear()
        _c, ja = upload("Anna", "Blau.jpg", bild((0.20, 0.35, 0.90)))
        _c, jb = upload("Anna", "Gruen.jpg", bild((0.25, 0.65, 0.20)))
        code1, j1 = warten(None, ja["file"]["id"], guest=tok)
        code2, j2 = bio(None, jb["file"]["id"], "start", guest=tok)
        ok(j1.get("st") == "done" and code2 == 429, f"Ratenbremse Gast ({code2})")
        code3, j3 = bio(None, ja["file"]["id"], "start", guest=tok)
        ok(j3.get("st") == "done", "fertiges Ergebnis zählt nicht zur Bremse")
        ns["BIO_RATE"] = (30, 90)
        CFG["tausch_bio"] = False
        ok(bio("Anna", fid)[1].get("st") == "off" and c.get("/api/tausch?area=all", headers=H["Anna"]).get_json().get("bio") is False,
           "Schalter aus: kein Bestimmen, kein Knopf")
        CFG["tausch_bio"] = True
        rt = ns["bio_runtime"]
        ns["bio_runtime"] = lambda: False
        code, j = bio("Anna", bid)
        ok(j.get("st") == "runtime" and not j.get("can_install") and "Administrator" in j.get("msg", ""), "Laufzeit fehlt: Benutzer sieht den Hinweis")
        ok(bio("admin", bid)[1].get("can_install"), "Laufzeit fehlt: Admin darf installieren")
        ns["bio_runtime"] = rt
        u_ = ns["BIO_BASE"]["url"]; ns["BIO_BASE"]["url"] = "https://github.com/DonElektro/MotionWatch/releases/download/" + ns["BIO_TAG"] + "/"
        ok(ns["bio_selftest"]().startswith("pins"), "Selbsttest bio_selftest")
        ns["BIO_BASE"]["url"] = u_
    else:
        print("A) echtes Modell", flush=True)
        echt_pruefen(ns, warten, upload, fotos)

    if browser:
        teil_b(ns, app, home, PW, bilder, tok, echt)
    if not browser and not echt:
        code, j = bio("Bob", bid, "delete")
        ok(ns["bio_installed"](), "Benutzer kann das Modell nicht löschen")
        code, j = bio("admin", bid, "delete")
        ok(code == 200 and not ns["bio_installed"]() and not os.path.exists(ns["bio_path"]("model")), "Admin löscht das Modell")
    with BIO["lock"]:
        ns["bio_worker_stop"]()
    shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(home, ignore_errors=True)


def echt_pruefen(ns, warten, upload, fotos):
    BIO = ns["BIO"]
    ps = sorted(glob.glob(os.path.join(fotos, "*.jpg"))) if fotos else []
    if not ps:                                           # without photos: timing on a synthetic picture
        ps = [None]
    hit1 = hit3 = n = 0
    ms, zeilen = [], []
    for p in ps:
        data = open(p, "rb").read() if p else blume()
        art = re.sub(r"_\d+$", "", os.path.basename(p)[:-4]).replace("_", " ") if p else ""
        code, j = upload("Anna", (art.replace(" ", "_") or "blume") + ".jpg", data)
        if code != 200:
            print("  (nicht hochgeladen: %s %s)" % (p, j.get("error"))); continue
        t0 = time.time()
        code, j = warten("Anna", j["file"]["id"], limit=180)
        if j.get("st") != "done":
            ok(False, f"echt: {art} -> {j.get('st')} {j.get('msg')}"); continue
        res = j["res"]
        top = [t["sci"] for t in res["top"]]
        n += 1
        hit1 += int(bool(art) and top[0] == art); hit3 += int(bool(art) and art in top)
        ms.append(res.get("ms") or 0)
        zeilen.append("%-28s %5.1f s  %s%s" % (art or "(Testbild)", time.time() - t0, res.get("line"), "  · sicher: %s %s %s" % (
            res["sure"]["rank_t"], res["sure"]["sci"], res["sure"]["pct"]) if res.get("sure") else ""))
    print("\n".join(zeilen))
    ok(n > 0, f"echt: {n} Bilder bestimmt, Modell laden {BIO.get('load_ms')} ms, rechnen im Mittel {sum(ms) / max(1, len(ms)):.0f} ms (2 Threads)")
    if n and fotos:
        print(f"  Treffer: top-1 {hit1}/{n} ({100.0 * hit1 / n:.0f} %), top-3 {hit3}/{n} ({100.0 * hit3 / n:.0f} %)")
        ok(hit3 >= 0.6 * n, f"echt: top-3 mindestens 60 % ({hit3}/{n})")


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns, app, home, PW, bilder, tok, echt):
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    import socket
    TZ, BIO = ns["TZ"], ns["BIO"]
    os.makedirs(bilder, exist_ok=True)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("Anna", PW["Anna"]), raw=None, ctype="application/json"):
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None),
                                   headers=dict(basic(*user), **{"Content-Type": ctype}))
        with op.open(r, timeout=30) as x:
            return json.loads(x.read())
    # a nice picture for the screenshots + an uncached one for the guest
    j = req("/api/tausch", {"action": "start", "name": "Loewenzahn_Wiese.jpg", "size": len(blume()), "area": "all"})
    req(f"/api/tausch/chunk?id={j['id']}&off=0", raw=blume(), ctype="application/octet-stream")
    fl = req("/api/tausch", {"action": "finish", "id": j["id"]})["file"]["id"]
    for _i in range(80):
        if TZ["files"].get(fl, {}).get("thumb") is not None:
            break
        time.sleep(0.05)
    # the model is loaded already (part A); for the screenshot of «load» a second, not yet loaded state is shown first
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name, vp_, mob in (("handy", {"width": 390, "height": 844}, True), ("desktop", {"width": 1366, "height": 860}, False)):
            ctx = br.new_context(viewport=vp_, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                 http_credentials={"username": "Anna", "password": PW["Anna"]}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('tausch-view','grid')}catch(e){}")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" and not KNOWN_403.search(m.text) else None)
            pg.goto(base + "/tausch"); pg.wait_for_selector(".tz-it img", timeout=15000); pg.wait_for_timeout(800)
            card = pg.locator(".tz-it", has_text="Loewenzahn_Wiese.jpg")
            ok(card.locator("button[title='Bestimmen']").count() == 1, f"{name}: 🌿 auf der Bild-Karte")
            ok(pg.locator(".tz-it", has_text="Plan.svg").locator("button[title='Bestimmen']").count() == 0, f"{name}: kein 🌿 bei SVG")
            ok(pg.locator(".tz-it", has_text="Notiz.txt").locator("button[title='Bestimmen']").count() == 0, f"{name}: kein 🌿 bei Text")
            pg.screenshot(path=os.path.join(bilder, f"bioclip_liste_{name}.png"), full_page=True)
            if name == "handy":
                card.locator("button[title='Bestimmen']").click()       # from the card: opens the picture and starts
            else:
                card.locator(".th").click(); pg.wait_for_selector(".tz-lb .tz-biob"); pg.click(".tz-lb .tz-biob")
            pg.wait_for_selector(".tz-bio .row.first", timeout=60000); pg.wait_for_timeout(500)
            txt = pg.inner_text(".tz-bio")
            ok(("Gemeiner Löwenzahn" in txt or echt) and "%" in txt and "das Bild verlässt das Gerät nie" in txt, f"{name}: Ergebnis im Panel ({txt[:120]!r})")
            ok(pg.locator(".tz-bio .row").count() == 3, f"{name}: drei Arten")
            pg.screenshot(path=os.path.join(bilder, f"bioclip_ergebnis_{name}.png"))
            box = pg.locator(".tz-bio").bounding_box()
            ok(box and box["x"] >= 0 and box["x"] + box["width"] <= vp_["width"] + 1, f"{name}: Panel passt in die Breite")
            pg.click(".tz-bio .hd button"); pg.wait_for_timeout(200)
            ok(pg.locator(".tz-bio").count() == 0 and pg.locator(".tz-lb").count() == 1, f"{name}: Panel schliessen, Vorschau bleibt")
            ok(not errs, f"{name}: keine JavaScript-Fehler {errs}")
            ctx.close()
        # «load» state: pretend the model is missing (only the marker), then load with progress through the page
        okf = os.path.join(home, "bioclip", "bioclip.ok")
        os.remove(okf)
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                             http_credentials={"username": "Anna", "password": PW["Anna"]}, locale="de-CH")
        ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark')}catch(e){}")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + "/tausch"); pg.wait_for_selector(".tz-it img", timeout=15000)
        pg.locator(".tz-it", has_text="Kaefer.jpg").locator(".th").click()
        pg.wait_for_selector(".tz-lb .tz-biob"); pg.click(".tz-lb .tz-biob")
        pg.wait_for_selector(".tz-bio .act button", timeout=10000); pg.wait_for_timeout(300)
        ok("einmal BioCLIP" in pg.inner_text(".tz-bio"), "Handy: Frage «einmal laden» mit Grösse")
        pg.screenshot(path=os.path.join(bilder, "bioclip_laden_handy.png"))
        pg.click(".tz-bio .act button")
        pg.wait_for_selector(".tz-bio .row.first", timeout=60000); pg.wait_for_timeout(300)
        ok(ns["bio_installed"](), "Handy: über die Seite geladen, danach bestimmt")
        ok(not errs, f"Handy (laden): keine JavaScript-Fehler {errs}")
        ctx.close()
        # guest page (phone)
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + f"/g/{tok}/tausch"); pg.wait_for_selector(".it img", timeout=15000); pg.wait_for_timeout(500)
        pg.locator(".it", has_text="Pilz.jpg").click()
        pg.wait_for_selector(".lb .tz-biob"); pg.click(".lb .tz-biob")
        pg.wait_for_selector(".tz-bio .row.first", timeout=60000); pg.wait_for_timeout(400)
        t_ = pg.inner_text(".tz-bio")
        ok(("Steinpilz" in t_ or echt) and "%" in t_, f"Gast: Ergebnis ({t_[:80]!r})")
        pg.screenshot(path=os.path.join(bilder, "bioclip_gast_handy.png"))
        ok(pg.locator(".it", has_text="Notiz.txt").count() == 1, "Gast sieht die Liste")
        pg.click(".lb .bar button:last-child"); pg.locator(".it", has_text="Notiz.txt").click(); pg.wait_for_timeout(300)
        ok(pg.locator(".lb .tz-biob").count() == 0, "Gast: kein 🌿 bei Text")
        ok(not errs, f"Gast: keine JavaScript-Fehler {errs}")
        ctx.close()
        br.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description="Test «🌿 Bestimmen» (639zzd)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "bioclip_bilder"))
    ap.add_argument("--echt", default="", help="Ordner mit den echten Dateien aus dem Workflow «BioCLIP»")
    ap.add_argument("--fotos", default="", help="mit --echt: Fotos Gattung_art_N.jpg für Treffer und Zeit")
    ap.add_argument("--pins", action="store_true", help="mit --echt: die Dateien müssen genau den festen Werten in BIO_FILES entsprechen")
    a = ap.parse_args()
    t0 = time.time()
    teil_a(a.datei or neueste(), a.echt, a.fotos, a.browser, a.bilder, a.pins)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
