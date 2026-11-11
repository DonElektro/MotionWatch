#!/usr/bin/env python3
"""Test «▦ QR-Befehls-Karten» (MoveEye Teil 639zzp) – ohne echte Kamera:

  A) im eigenen Prozess: Selbsttest qrk_selftest (Prüfnummer eigen / verändert / anderes Gerät, Code lesen, Sperrzeit,
     sperren, neuer Schlüssel, keine Geheimnisse auf einer Karte), jeder Befehl in Demo-sicherer Form über qrk_exec
     (Ersatz-Funktionen zählen die Aufrufe), Pause-Gründe (aus, Simulation, Akku-Sparen, CPU), kein Schlüssel im Code.
  B) MoveEye ohne Fenster mit der Demo-Kamera; eine Karte (das PNG aus der Werkstatt, verkleinert wie in ~1 m) wird ins
     Demo-Bild gelegt, solange die Datei MW_QRK_KARTE existiert: aus = kein Lesen; ein = der Befehl läuft einmal; Sperrzeit
     (gehalten, kurz weg); fremde / veränderte / gesperrte Karte = nichts (Zeile «fremde Karte ignoriert»); jeder Befehl
     (Push an einen lokalen Webhook, Vorlesen, Notiz mit Foto, Aufnahme, Licht, Relais, Kopf, Erkennungsprofil, Modus);
     Weitwinkel allein; Foto + Notiz in Verlauf → Aufnahmen; Rahmen im Live-Bild; Rechte (Familie / Kind: keine Werkstatt,
     keine Karte, kein Schalter); keine Zugangsdaten im Code (das Bild der Karte gelesen).
  C) --browser: Werkstatt in iPhone-Breite (390 × 844) und am PC: Karte erstellen, Liste, Druckseite; Live-Seite mit dem
     Rahmen um die Karte; Einstellungen → Kameras & Kopf → Abschnitt mit Link; keine JavaScript-Fehler.
     --bilder ORDNER: qr_karten_*.png
  --messen: nur die Machbarkeits-Messung (Simulation: Postkarte 10 × 15 cm, QR 8 cm im Kamerabild 1280 × 720 mit
     Perspektive, Unschärfe, Rauschen, Dämmerung, IR-grau; Lesezeit und grösster Abstand) – dauert einige Minuten.

  python3 werkzeuge/qr_karten_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--messen]
"""
import argparse
import base64
import glob
import http.server
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}
PW = "Karten-" + base64.b16encode(os.urandom(5)).decode().lower()


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


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_qrk_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(ns):
    print("A) im eigenen Prozess", flush=True)
    CFG = ns["CFG"]
    ns["save_settings"] = lambda *a, **k: None
    logs = []
    ns["log_event"] = lambda k, t: logs.append(t)
    ok(ns["qrk_selftest"]().startswith("check number"), "Selbsttest qrk_selftest")
    CFG.update(qrk_cards=[], qrk_secret="", lang="de", record_dir=os.path.join(ns["DATA_DIR"], "recordings"))   # never into the repository
    calls = []
    ns["light_set"] = lambda n, m: (calls.append(("light", n, m)), (True, ""))[1]
    ns["relay_update"] = lambda i, f, v: (calls.append(("relay", i, f, v)), (True, ""))[1]
    ns["teach_goto"] = lambda i, who="", wait=False: (calls.append(("head", i)), (True, ""))[1]
    ns["prof_set"] = lambda p, who="": (calls.append(("prof", p)), (True, ""))[1]
    ns["mode_set"] = lambda m, who="": (calls.append(("mode", m)), (True, ""))[1]
    ns["tts_say"] = lambda txt, lang=None, save=False: (calls.append(("say", txt)), (True, ""))[1]
    ns["WAYPOINTS"][:] = [[40.0, 50.0, "Zelt"]]
    import numpy as np
    img = np.full((360, 640, 3), 128, np.uint8)
    mk = ns["qrk_create"]
    cards = {
        "light": mk({"cmd": "L", "name": "Licht", "light": "ir", "on": True}),
        "relay": mk({"cmd": "Y", "name": "Pumpe", "relay": 0, "on": False}),
        "head": mk({"cmd": "H", "name": "Zum Zelt", "point": "Zelt"}),
        "prof": mk({"cmd": "F", "name": "Nacht", "profile": "p:night"}),
        "mode": mk({"cmd": "F", "name": "Haus", "profile": "m:home"}),
        "say": mk({"cmd": "S", "name": "Hallo", "text": "Grüezi mitenand"}),
        "rec": mk({"cmd": "R", "name": "Film", "secs": 30}),
    }
    ok(all(c for c, _e in cards.values()), "sieben Karten erstellt: " + ", ".join(f"{k}={e or 'ok'}" for k, (c, e) in cards.items()))
    ex = ns["qrk_exec"]
    for k in ("light", "relay", "head", "prof", "mode", "say"):
        r = ex(cards[k][0], img)
        ok(r == (True, ""), f"Befehl {k}: {r} {calls[-1] if calls else ''}")
    ok(("light", "ir", "on") in calls and ("relay", 0, "mode", "off") in calls and ("head", 0) in calls and ("prof", "night") in calls
       and ("mode", "home") in calls and ("say", "Grüezi mitenand") in calls, "die vorhandenen Funktionen bekommen die richtigen Werte")
    CFG["sim_on"] = False
    q0 = ns["QUICK"]["rec_until"]
    ok(ex(cards["rec"][0], img)[0] and ns["QUICK"]["rec_until"] > time.time() + 25 and ns["QUICK"]["rec_until"] != q0, "Aufnahme 30 s: QUICK rec_until")
    CFG["armed"] = True
    bad = dict(cards["mode"][0], p="m:transport")
    ok(not ex(bad, img)[0] and ("mode", "transport") not in calls, "Modus «Transport / Ruhe» per Karte: abgelehnt (kein Ausschalten)")
    ns["mode_disarms"] = lambda m, gw=None: True
    ok(not ex(cards["mode"][0], img)[0], "ein Modus, der den Schutz ausschalten würde: abgelehnt")
    CFG["armed"] = False
    # pauses
    CFG.update(qrk_on=False)
    ok(ns["qrk_pause_reason"]() == "off", "aus: Pause «off»")
    CFG.update(qrk_on=True, sim_on=True)
    ok(ns["qrk_pause_reason"]() == "simulation", "Simulation: Pause")
    CFG["sim_on"] = False
    ns["batt_save_active"] = lambda: True
    ok(ns["qrk_pause_reason"]() == "battery saver", "Akku-Sparen: Pause")
    ns["batt_save_active"] = lambda: False
    ns["STATE"]["cpu"] = 97.0
    ok(ns["qrk_pause_reason"]() == "CPU busy", "CPU 97 %: Pause")
    ns["STATE"]["cpu"] = 80.0
    ok(ns["qrk_pause_reason"]() == "CPU busy", "CPU 80 % (unter 85, aber nicht 10 % darunter): weiter Pause")
    ns["STATE"]["cpu"] = 40.0
    ok(ns["qrk_pause_reason"]() == "", "CPU 40 %: liest")
    CFG.update(qrk_cam_head=False, qrk_cam_wide=False)
    ok(ns["qrk_pause_reason"]() == "no camera chosen", "keine Kamera gewählt: Pause")
    CFG.update(qrk_cam_head=True, qrk_cam_wide=True, qrk_on=False)
    # the code: no key, no password
    key = CFG["qrk_secret"]
    pls = [ns["qrk_payload"](c) for c, _e in cards.values()]
    ok(key and not any(key in p or key[:12] in p for p in pls), "der Schlüssel steht in keinem Code")
    ok(all(len(p.encode()) <= ns["QRK_HEAD"] + ns["QRK_TEXT_MAX"] for p in pls), "Codes klein (Kopf 18 Bytes + Werte)")
    for txt in ("WIFI:T:WPA;S:Camping;P:geheim;;", "mein passwort: x", "http://u:p@host/", "PIN: 4711"):
        c, e = mk({"cmd": "P", "name": "x", "text": txt})
        ok(c is None and "password" in e.lower(), f"Text mit Zugangsdaten abgelehnt: {txt!r}")
    CFG["hotspot_password"] = "Zelt-Geheim-77"
    ok(mk({"cmd": "N", "name": "x", "text": "Code ist zelt-geheim-77"})[0] is None, "das Passwort des eigenen WLAN abgelehnt")
    ns["STATE"]["wifi"] = {"ssid": "CampingSeeblick", "connected": True}
    ok(mk({"cmd": "P", "name": "Wir sind im CampingSeeblick", "text": "da"})[0] is None, "der Name des verbundenen WLAN abgelehnt")
    ns["STATE"]["wifi"] = None
    # every use: the log line, the counter
    c = cards["light"][0]
    ns["qrk_run"](c, img, "head", feedback=False)
    ok(ns["qrk_card"](c["id"])["n"] == 1 and any("QR card «Licht»" in x for x in logs), "Benutzung: Zähler + Protokollzeile")
    ns["QRK"]["log_t"].clear()
    ns["qrk_seen"]("head", "M1XXXXXP" + "A" * 10 + "1hallo", None, img)
    ns["qrk_seen"]("head", "https://example.org/wlan?pw=geheim", None, img)
    fl = [x for x in logs if "foreign" in x]
    ok(len(fl) == 1 and "geheim" not in " ".join(logs) and "hallo" not in " ".join(logs), "fremde Karten: eine Zeile pro Minute, nie der Inhalt")


# ---------------------------------------------------------------------------------------------------------------------- B
WRAP = r'''
import json, os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
_qk_read = DemoSource.read
_QK = {"m": None, "img": None}
def _qk_read_card(self):                 # the test holds a card in front of the demo camera while the file exists
    ok_, img_ = _qk_read(self)
    p_ = os.environ.get("MW_QRK_KARTE", "")
    if ok_ and p_ and os.path.exists(p_):
        try:
            m_ = os.path.getmtime(p_)
            if _QK["m"] != m_:
                _QK["img"] = cv2.imread(p_, cv2.IMREAD_COLOR); _QK["m"] = m_
            c_ = _QK["img"]
            if c_ is not None:
                h_, w_ = c_.shape[:2]; x_, y_ = 330, 60
                img_ = img_.copy(); img_[y_:y_ + h_, x_:x_ + w_] = c_
        except Exception:
            pass
    return ok_, img_
DemoSource.read = _qk_read_card
_qk_pr = qrk_pause_reason
def _qk_pr_test():                       # this computer is shared by other tests: the CPU pause is checked in part A
    r_ = _qk_pr()
    return "" if r_ in ("CPU busy", "detection is slow") else r_
qrk_pause_reason = _qk_pr_test
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
'''


class Hook(http.server.BaseHTTPRequestHandler):
    got = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        Hook.got.append(self.rfile.read(n))
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def teil_b(datei, ns, browser, bilder):
    print("B) MoveEye mit Demo-Kamera und einer Karte im Bild", flush=True)
    import cv2
    import numpy as np
    hook = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Hook)
    threading.Thread(target=hook.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp(prefix="mw_qrk_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    karte = os.path.join(tmp, "karte.png")
    st = {"source": "demo", "extra_cams": ["usb:0"], "kopf_ov": "usb:0", "thermal_source": "", "thermal_on": False,
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "news_popup": False, "tours_auto": False, "notify_type": "webhook", "notify_url": f"http://127.0.0.1:{hook.server_address[1]}/hook",
          "notify_on": True, "qrk_feedback": "beep"}
    json.dump({"cfg": st, "waypoints": [[30.0, 45.0, "Zelt"], [70.0, 50.0, "Velo"]]}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_QRK_KARTE=karte)
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    A = ("admin", PW)

    def req(path, data=None, user=A):
        h = dict(basic(*user)) if user else {}
        h["Content-Type"] = "application/json"
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
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

    def cards():
        return {c["name"]: c for c in req("/api/qrk?lang=de")[1].get("cards", [])}

    def zeigen(cid, px=170):
        """the PNG of the card from the workshop, as big as at about 1 m in front of the demo camera"""
        c, png = req(f"/api/qrk/card/{cid}.png")
        im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
        im = cv2.resize(im, (px, int(px * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA)
        cv2.imwrite(karte + ".tmp.png", im); os.replace(karte + ".tmp.png", karte)

    def zeigen_code(text, px=150):
        im = cv2.imdecode(np.frombuffer(ns["qr_png"](text, 6), np.uint8), cv2.IMREAD_COLOR)
        im = cv2.resize(im, (px, px), interpolation=cv2.INTER_AREA)
        cv2.imwrite(karte + ".tmp.png", im); os.replace(karte + ".tmp.png", karte)

    def weg():
        try:
            os.remove(karte)
        except OSError:
            pass

    def warten_n(name, n, limit=60.0):
        t0 = time.time()
        while time.time() - t0 < limit:
            c = cards().get(name)
            if c and c["n"] >= n:
                return c
            time.sleep(0.3)
        return cards().get(name)

    def log_text():
        return json.dumps(req("/api/log?limit=3000&q=qr")[1].get("lines", []), ensure_ascii=False)

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        for n_, r_ in {"Anna": "family", "Kim": "kid"}.items():
            req("/api/users", {"action": "add", "name": n_, "password": n_.lower() + "-pass-1", "role": r_})
        Fa, K = ("Anna", "anna-pass-1"), ("Kim", "kim-pass-1")
        print("B) Rechte", flush=True)
        for who, u in (("Familie", Fa), ("Kind", K)):
            ok(req("/karten", user=u)[0] == 403 and req("/api/qrk?lang=de", user=u)[0] == 403, f"{who}: keine Werkstatt")
            ok(req("/api/qrk", {"action": "create", "cmd": "L", "name": "x", "light": "white", "on": True}, u)[0] == 403, f"{who}: keine Karte erstellen")
            ok(req("/api/set", {"key": "qrk_on", "value": True}, u)[0] == 403, f"{who}: Schalter nicht")
        ok(req("/karten", user=None)[0] == 401, "ohne Anmeldung: 401")
        c, b = req("/karten")
        ok(c == 200 and b"Card workshop" in b, "Admin: Werkstatt")
        c, b = req("/more")
        ok(c == 200 and b'href="/karten"' in b, "Mehr: «Karten-Werkstatt» für den Admin")
        c, b = req("/more", user=Fa)
        ok(c == 200 and b'href="/karten"' not in b, "Mehr: nicht für die Familie")
        print("B) Karten erstellen", flush=True)
        mk = lambda d: req("/api/qrk", dict(d, action="create", lang="de"))
        specs = [{"cmd": "L", "name": "Licht an", "light": "white", "on": True, "desc": "Weisses Licht ein"},
                 {"cmd": "P", "name": "Essen fertig", "text": "Essen ist fertig – kommt zum Zelt!", "photo": True},
                 {"cmd": "S", "name": "Ansage", "text": "Willkommen auf dem Platz"},
                 {"cmd": "N", "name": "Notiz", "text": "Velo abgeschlossen"},
                 {"cmd": "R", "name": "Film 30 s", "secs": 30},
                 {"cmd": "Y", "name": "Relais ein", "relay": 0, "on": True},
                 {"cmd": "H", "name": "Kopf Velo", "point": "Velo"},
                 {"cmd": "F", "name": "Profil Nacht", "profile": "p:night"},
                 {"cmd": "F", "name": "Modus Haus", "profile": "m:home"}]
        for s_ in specs:
            c, j = mk(s_)
            ok(c == 200 and j.get("ok"), f"Karte «{s_['name']}» ({j.get('card', {}).get('what') or j.get('error')})")
        c, j = mk({"cmd": "P", "name": "WLAN", "text": "WIFI:T:WPA;S:Camping;P:geheim;;"})
        ok(c == 400 and "Passwort" in (j.get("error") or ""), f"WLAN-Code abgelehnt: {j.get('error')}")
        c, j = mk({"cmd": "F", "name": "Ruhe", "profile": "m:transport"})
        ok(c == 400, "Modus «Transport / Ruhe»: keine Karte")
        C = cards()
        c, j = req("/api/qrk", {"action": "check", "cmd": "P", "text": "x" * 40, "photo": True})
        ok(j.get("ok") and j["modules"] == 33 and 0.3 < j["range"]["card"] < 1.0 and j["range"]["a4"] > 1.2, f"Werkstatt: Grösse + Reichweite {j}")
        # no key, no password in what the camera reads
        key = ""
        for _i in range(40):                                            # the settings are written a few seconds later
            key = json.load(open(os.path.join(cfg, "motionwatch_settings.json"))).get("cfg", {}).get("qrk_secret", "")
            if key:
                break
            time.sleep(0.5)
        dets = [cv2.QRCodeDetectorAruco()] if hasattr(cv2, "QRCodeDetectorAruco") else []
        dets.append(cv2.QRCodeDetector())
        txts = []
        for nm, cc in C.items():
            c, png = req(f"/api/qrk/card/{cc['id']}.png")
            im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
            txts.append(next((t_ for t_ in (d_.detectAndDecode(im)[0] for d_ in dets) if t_), ""))
        ok(len(key) == 64 and all(t.startswith("M1") for t in txts) and not any(key[:16] in t for t in txts) and not any(PW in t for t in txts),
           f"{len(txts)} Karten-Bilder gelesen: Code «M1…», kein Schlüssel, kein Passwort ({txts[0][:24]}…)")
        c, svg = req(f"/api/qrk/card/{C['Licht an']['id']}.svg")
        ok(c == 200 and b"<svg" in svg and "Licht an".encode() in svg and b"Weisses Licht ein" in svg, "SVG mit Name und Beschreibung")
        c, pg = req(f"/karten/print?id={C['Licht an']['id']}&size=card&lang=de")
        ok(c == 200 and b"width=\"100mm\"" in pg and "Drucken".encode() in pg and b"@page" in pg, "Druckseite (Postkarte 100 × 150 mm)")
        print("B) aus = kein Lesen", flush=True)
        zeigen(C["Licht an"]["id"])
        time.sleep(4)
        s0 = req("/api/qrk?lang=de")[1]["state"]
        ok(s0["pause"] == "off" and s0["scans"] == 0 and cards()["Licht an"]["n"] == 0, f"aus: nichts gelesen ({s0['pause']}, {s0['scans']} Blicke)")
        print("B) ein: Befehl einmal, Sperrzeit", flush=True)
        req("/api/set", {"key": "qrk_on", "value": True})
        c1 = warten_n("Licht an", 1)
        ok(c1 and c1["n"] == 1, f"Karte gelesen, Befehl ausgeführt ({c1 and c1['n']}×)")
        j = req("/api/state?lang=de")[1]
        ok(j["state"]["light_cfg"]["white"] == "on", "weisses Licht: ein")
        time.sleep(1.2)
        c, snap = req("/snapshot.jpg")
        im = cv2.imdecode(np.frombuffer(snap, np.uint8), cv2.IMREAD_COLOR) if c == 200 else None
        green = 0
        if im is not None:
            roi = im[30:330, 300:530].astype(int)
            green = int(((abs(roi[:, :, 0] - 80) < 40) & (abs(roi[:, :, 1] - 220) < 40) & (abs(roi[:, :, 2] - 90) < 45)).sum())
        ok(green > 200, f"Live-Bild: grüner Rahmen + Schild um die Karte ({green} Pixel)")
        if bilder and im is not None:
            cv2.imwrite(os.path.join(bilder, "qr_karten_livebild_rahmen.png"), im)
        time.sleep(8)                                                   # held in front of the camera for 8 s more
        ok(cards()["Licht an"]["n"] == 1, "gehalten: nur einmal")
        weg(); time.sleep(4); zeigen(C["Licht an"]["id"])
        c2 = warten_n("Licht an", 2)
        ok(c2 and c2["n"] == 2, "weg und Sperrzeit vorbei: wieder")
        t_fire = time.time()
        weg(); time.sleep(3.6); zeigen(C["Licht an"]["id"]); time.sleep(2.5)
        ok(cards()["Licht an"]["n"] == 2 and time.time() - t_fire < 10, "kurz weg, aber die Sperrzeit (10 s) noch nicht vorbei: nicht noch einmal")
        weg(); time.sleep(max(4.0, 10.5 - (time.time() - t_fire))); zeigen(C["Licht an"]["id"])
        c3 = warten_n("Licht an", 3)
        ok(c3 and c3["n"] == 3, "danach wieder")
        weg(); time.sleep(3.5)
        print("B) fremd, verändert, gesperrt", flush=True)
        pl_ok = txts[list(C).index("Licht an")]
        def warten_log(rx, limit=30.0):                               # a busy computer reads later: wait for the line
            t0 = time.time()
            while time.time() - t0 < limit and not re.search(rx, log_text()):
                time.sleep(0.5)
        zeigen_code(pl_ok[:-1] + ("0" if pl_ok[-1] == "1" else "1")); warten_log("foreign card ignored|fremde Karte ignoriert"); time.sleep(2)
        zeigen_code("https://example.org/?pw=geheim"); time.sleep(4)
        weg()
        lt = log_text()
        ok(cards()["Licht an"]["n"] == 3 and req("/api/state?lang=de")[1]["state"]["light_cfg"]["white"] == "on", "veränderte Karte («Licht aus» mit alter Prüfnummer): nichts")
        ok("foreign card ignored" in lt or "fremde Karte ignoriert" in lt, "Protokoll: «fremde Karte ignoriert»")
        ok(lt.count("foreign card ignored") + lt.count("fremde Karte ignoriert") == 1 and "geheim" not in lt, "nur eine Zeile, ohne Inhalt")
        req("/api/qrk", {"action": "revoke", "id": C["Licht an"]["id"]})
        time.sleep(4); zeigen(C["Licht an"]["id"]); warten_log("is revoked|gesperrt"); time.sleep(2); weg()
        ok(cards()["Licht an"]["n"] == 3 and cards()["Licht an"]["off"], "gesperrte Karte: nichts")
        ok("is revoked" in log_text() or "gesperrt" in log_text(), "Protokoll: gesperrt")
        print("B) jeder Befehl mit der Kamera", flush=True)
        Hook.got.clear()
        for nm in ("Essen fertig", "Ansage", "Notiz", "Film 30 s", "Relais ein", "Kopf Velo", "Profil Nacht", "Modus Haus"):
            time.sleep(3.5)
            zeigen(C[nm]["id"])
            cc = warten_n(nm, 1)
            weg()
            ok(cc and cc["n"] == 1, f"«{nm}»: gelesen und ausgeführt")
            if nm == "Film 30 s":
                ok(req("/api/state?lang=de")[1]["state"]["quick_rec"], "Aufnahme läuft (Schnellschalter-Zustand)")
        time.sleep(2)
        st = req("/api/qrk?lang=de")[1]["state"]
        uses = {u["name"]: u for u in st["uses"]}
        ok(any(b"Essen ist fertig" in g for g in Hook.got), f"Push an den Webhook mit dem Text der Karte ({len(Hook.got)} Nachrichten)")
        ok(not any(key[:16].encode() in g or PW.encode() in g for g in Hook.got), "Push ohne Schlüssel / Passwort")
        ok(uses.get("Ansage") and (uses["Ansage"]["ok"] or re.search("Lautsprecher|Sprachprogramm", uses["Ansage"]["msg_t"] or "")),
           f"Vorlesen: über tts_say (Demo ohne Lautsprecher: {uses.get('Ansage', {}).get('msg_t')})")
        j = req("/api/state?lang=de")[1]
        ok(j["relays"][0]["mode"] == "on", "Relais 1: ein")
        ok(uses.get("Profil Nacht", {}).get("ok") and uses.get("Modus Haus", {}).get("ok"), "Profil und Modus: ausgeführt")
        ok(uses.get("Kopf Velo") is not None, f"Kopf: teach_goto ({uses.get('Kopf Velo', {}).get('ok')}, {uses.get('Kopf Velo', {}).get('msg_t')})")
        c, j = req("/api/recordings?kind=image&limit=100")
        recs = [x for x in j.get("items", []) if x["name"].startswith("qrcard_")]
        ok(len(recs) >= 5 and all(x.get("source") == "QR card" for x in recs), f"Verlauf → Aufnahmen: {len(recs)} Fotos (Quelle «QR card»)")
        ok(any("Velo abgeschlossen" in (x.get("note") or "") for x in recs), "Notiz mit Foto im Verlauf (Text der Karte)")
        print("B) nur Weitwinkel", flush=True)
        req("/api/set", {"key": "qrk_cam_head", "value": False})
        req("/api/qrk", {"action": "unrevoke", "id": C["Licht an"]["id"]})
        req("/api/light", {"light": "white", "mode": "off"})
        time.sleep(3.5); zeigen(C["Licht an"]["id"])
        c4 = warten_n("Licht an", 4)
        weg()
        lu = req("/api/qrk?lang=de")[1]["state"]["last"] or {}
        ok(c4 and c4["n"] == 4 and lu.get("cam") == "wide", f"Weitwinkel-Kamera allein liest ({lu.get('cam')})")
        req("/api/set", {"key": "qrk_cam_head", "value": True})
        c, j = req("/api/qrk", {"action": "try", "id": C["Ansage"]["id"], "lang": "de"})
        ok(c == 200 and "msg" in j, "Werkstatt «Ausprobieren»")
        c, j = req("/api/qrk", {"action": "rotate"})
        ok(c == 400, "neuer Schlüssel nur mit Bestätigung")
        if browser:
            teil_c(base, bilder, karte, C, zeigen, weg)
        n_vor = cards()["Licht an"]["n"]
        req("/api/qrk", {"action": "rotate", "confirm": True})
        ok(all(x["reprint"] for x in cards().values()), "neuer Schlüssel: alle Karten «neu drucken»")
        time.sleep(3.5); zeigen_code(pl_ok); time.sleep(4); weg()
        ok(cards()["Licht an"]["n"] == n_vor, "alte gedruckte Karte nach neuem Schlüssel: nichts")
        req("/api/set", {"key": "qrk_on", "value": False})
        if FEHLER:
            print("  Protokoll (QR):", "\n   ".join(f"{x['t']} {x['text']}" for x in req("/api/log?limit=3000&q=qr")[1].get("lines", [])[:40]))
    finally:
        weg()
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        hook.shutdown()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        if "Traceback" in log:
            print(log[-2500:])
            ok(False, "Fehler im Protokoll von MoveEye")
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- C
def teil_c(base, bilder, karte, C, zeigen, weg):
    from playwright.sync_api import sync_playwright
    print("C) Browser", flush=True)
    if bilder:
        os.makedirs(bilder, exist_ok=True)
    def shot(pg, n, **k):
        if not bilder:
            return
        pg.evaluate("() => document.querySelectorAll('#gd-card, .gd-card, #g2-ov').forEach(x => x.remove())")   # page tips cover the picture
        pg.screenshot(path=os.path.join(bilder, n), **k)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for name, vp, mob in (("iphone", {"width": 390, "height": 844}, True), ("pc", {"width": 1366, "height": 900}, False)):
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=3 if mob else 1,
                                 http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + "/karten", wait_until="domcontentloaded")
            pg.wait_for_selector("#qk-cmds button", timeout=20000)
            pg.wait_for_selector(".qk-c", timeout=10000)
            ok("Karten-Werkstatt" in pg.inner_text("h2") and pg.locator(".qk-c").count() >= 9, f"{name}: Werkstatt mit der Liste ({pg.locator('.qk-c').count()} Karten)")
            sw = pg.evaluate("() => document.documentElement.scrollWidth")
            ok(sw <= vp["width"] + 1, f"{name}: kein waagrechtes Scrollen ({sw} px)")
            pg.locator("#qk-cmds button", has_text="Push").click()
            pg.fill("#qk-name", "Bin gleich zurück")
            pg.fill("#qk-text", "Bin in 10 Minuten zurück")
            pg.fill("#qk-desc", "Vor die Kamera halten")
            pg.wait_for_timeout(700)
            ok("Leseabstand" in pg.inner_text("#qk-size"), f"{name}: Hinweis Grösse / Abstand ({pg.inner_text('#qk-size')[:70]!r})")
            pg.click("#qk-go")
            pg.wait_for_selector("#qk-new.on img", timeout=10000); pg.wait_for_timeout(600)
            ok("Bin gleich zurück" in pg.inner_text("#qk-new"), f"{name}: neue Karte mit Vorschau")
            shot(pg, f"qr_karten_werkstatt_{name}.png")
            shot(pg, f"qr_karten_werkstatt_{name}_ganz.png", full_page=True)
            with ctx.expect_page() as pp:
                pg.locator("#qk-new-b a", has_text="Drucken").click()
            pr = pp.value; pr.wait_for_load_state("domcontentloaded"); pr.wait_for_timeout(400)
            ok(pr.locator(".cv svg").count() == 1 and "Drucken" in pr.inner_text(".bar"), f"{name}: Druckseite")
            shot(pr, f"qr_karten_druckseite_{name}.png")
            pr.emulate_media(media="print")
            ok(not pr.locator(".bar").is_visible(), f"{name}: Druckansicht ohne Knöpfe")
            pr.close()
            ok(not errs, f"{name}: keine JavaScript-Fehler {errs}")
            ctx.close()
        # the live picture with the frame (iPhone width) and the section in the settings
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3,
                             http_credentials={"username": "admin", "password": PW}, locale="de-CH")
        ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + "/", wait_until="domcontentloaded")
        pg.wait_for_function("() => { const v = document.getElementById('video'); return v && v.naturalWidth > 0; }", timeout=30000)
        time.sleep(3.5)
        zeigen(C["Licht an"]["id"])
        pg.wait_for_timeout(3500)
        shot(pg, "qr_karten_livebild_iphone.png")
        try:
            pg.locator("#video").screenshot(path=os.path.join(bilder, "qr_karten_livebild_nah.png")) if bilder else None
        except Exception:
            pass
        weg()
        pg.goto(base + "/settings", wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)
        found = pg.evaluate("""() => { const d = [...document.querySelectorAll('details')].find(x => /QR-Befehls-Karten/.test(x.querySelector('summary') ? x.querySelector('summary').textContent : ''));
            if (!d) return false; d.open = true; d.dispatchEvent(new Event('toggle')); d.scrollIntoView(); return true; }""")
        pg.wait_for_timeout(1500)
        ok(found and pg.locator(".qrk-p a[href='/karten']").count() == 1, "Einstellungen → Kameras & Kopf: Abschnitt mit Link zur Werkstatt")
        shot(pg, "qr_karten_einstellungen_iphone.png")
        ok(not errs, f"Live / Einstellungen: keine JavaScript-Fehler {errs}")
        ctx.close()
        br.close()


# ---------------------------------------------------------------------------------------------------------------------- Messung
def messen(ns, n=10):
    """the feasibility check (simulation): postcard 10 × 15 cm, QR 8 cm, in a camera picture 1280 × 720"""
    import cv2
    import numpy as np
    rng = np.random.default_rng(7)
    qr_matrix = ns["qr_matrix"]

    def card_image(M, ppcm=60):
        W, H = 10 * ppcm, 15 * ppcm
        img = np.full((H, W), 245, np.uint8)
        q = cv2.resize(np.where(np.array(M, bool), 20, 245).astype(np.uint8), (8 * ppcm, 8 * ppcm), interpolation=cv2.INTER_NEAREST)
        img[ppcm:9 * ppcm, ppcm:9 * ppcm] = q
        cv2.putText(img, "Licht an", (int(1.5 * ppcm), int(11.5 * ppcm)), cv2.FONT_HERSHEY_SIMPLEX, 2.2, 30, 5)
        return img, ppcm

    def background(w=1280, h=720):
        yy, xx = np.mgrid[0:h, 0:w]
        bg = (90 + 60 * np.sin(xx / 210.0) * np.cos(yy / 160.0)).astype(np.float32)
        for _ in range(25):
            cv2.circle(bg, (int(rng.integers(0, w)), int(rng.integers(0, h))), int(rng.integers(10, 90)), float(rng.integers(30, 200)), -1)
        for _ in range(15):
            cv2.line(bg, (int(rng.integers(0, w)), int(rng.integers(0, h))), (int(rng.integers(0, w)), int(rng.integers(0, h))), float(rng.integers(20, 220)), int(rng.integers(1, 6)))
        return cv2.GaussianBlur(bg, (0, 0), 1.5)

    def render(card, ppcm, d, hfov, light, W=1280, H=720):
        f = (W / 2) / math.tan(math.radians(hfov / 2))
        ch, cw = card.shape
        yw, pt, rl = (math.radians(rng.uniform(-30, 30)), math.radians(rng.uniform(-15, 15)), math.radians(rng.uniform(-12, 12)))
        Ry = np.array([[math.cos(yw), 0, math.sin(yw)], [0, 1, 0], [-math.sin(yw), 0, math.cos(yw)]])
        Rx = np.array([[1, 0, 0], [0, math.cos(pt), -math.sin(pt)], [0, math.sin(pt), math.cos(pt)]])
        Rz = np.array([[math.cos(rl), -math.sin(rl), 0], [math.sin(rl), math.cos(rl), 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        off = np.array([rng.uniform(-0.15, 0.15) * d, rng.uniform(-0.08, 0.08) * d, d])
        pts = []
        for u, v in ((0, 0), (cw / ppcm, 0), (cw / ppcm, ch / ppcm), (0, ch / ppcm)):
            P = R @ np.array([(u - cw / ppcm / 2) / 100.0, (v - ch / ppcm / 2) / 100.0, 0.0]) + off
            pts.append([W / 2 + f * P[0] / P[2], H / 2 + f * P[1] / P[2]])
        Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]]), np.float32(pts))
        bg = background(W, H)
        warped = cv2.warpPerspective(card.astype(np.float32), Hm, (W, H), flags=cv2.INTER_AREA)
        mask = cv2.warpPerspective(np.ones_like(card, np.float32), Hm, (W, H), flags=cv2.INTER_LINEAR)
        img = cv2.GaussianBlur(bg * (1 - mask) + warped * mask, (0, 0), rng.uniform(0.6, 1.1))
        g, o, noise = {"day": (1.0, 0.0, 3.0), "dusk": (0.35, 10.0, 7.0), "ir": (0.30, 25.0, 9.0)}[light]
        if light == "ir":
            yy, xx = np.mgrid[0:H, 0:W]
            img = img * np.clip(1.0 - 0.5 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2), 0.4, 1.0)
        return cv2.cvtColor(np.clip(img * g + o + rng.normal(0, noise, img.shape), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)

    decs = [("QRCodeDetector", cv2.QRCodeDetector())] + ([("QRCodeDetectorAruco", cv2.QRCodeDetectorAruco())] if hasattr(cv2, "QRCodeDetectorAruco") else [])
    print(f"Messung (Simulation, OpenCV {cv2.__version__}, {os.cpu_count()} CPU) – {n} Versuche pro Abstand", flush=True)
    for nm, det in decs:
        ts = []
        for _i in range(6):
            im = cv2.cvtColor(background().astype(np.uint8), cv2.COLOR_GRAY2GRAY if False else cv2.COLOR_GRAY2BGR)
            t0 = time.perf_counter(); det.detectAndDecode(im); ts.append((time.perf_counter() - t0) * 1000)
        print(f"  leeres Bild 1280 × 720, {nm}: {sorted(ts)[len(ts) // 2]:.0f} ms", flush=True)
    for pname, txt in (("Licht an (20 B)", "M1K7QX2LABCDEFGHJKw1"), ("Push, 40 Zeichen (59 B)", "M1K7QX2PABCDEFGHJK1" + "Bitte zum Zelt kommen, Essen ist fertig!")):
        M = qr_matrix(txt)
        card, ppcm = card_image(M)
        print(f"  {pname}: {len(M)} × {len(M)} Module, Modul {80 / len(M):.1f} mm", flush=True)
        for cam, hfov in (("Kopf 66°", 66.0), ("Weitwinkel 102°", 102.0)):
            for light in ("day", "dusk", "ir"):
                best = {}
                for d in [x / 10 for x in range(3, 31)]:
                    hits = {k: 0 for k, _ in decs}; ms = {k: [] for k, _ in decs}
                    for _i in range(n):
                        im = render(card, ppcm, d, hfov, light)
                        for k, det in decs:
                            t0 = time.perf_counter(); got = det.detectAndDecode(im)[0]; ms[k].append((time.perf_counter() - t0) * 1000)
                            hits[k] += got == txt
                    for k in hits:
                        if hits[k] >= 0.8 * n:
                            best[k] = (d, sorted(ms[k])[n // 2])
                    if all(hits[k] < 0.3 * n for k in hits) and d > 0.5:
                        break
                print(f"    {cam:15s} {light:4s} " + " · ".join(f"{k}: {('bis %.1f m (%.0f ms)' % best[k]) if k in best else 'nie sicher'}" for k, _ in decs), flush=True)


def main():
    ap = argparse.ArgumentParser(description="Test «▦ QR-Befehls-Karten» (639zzp)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--messen", action="store_true")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    t0 = time.time()
    home = tempfile.mkdtemp(prefix="mw_qrk_home_")
    try:
        ns = lade(datei, home)
        if a.messen:
            messen(ns)
            return 0
        ns_b = lade(datei, tempfile.mkdtemp(prefix="mw_qrk_home2_"))     # a clean copy for the helpers of B (qr_png)
        teil_a(ns)
        teil_b(datei, ns_b, a.browser, a.bilder)
    finally:
        shutil.rmtree(home, ignore_errors=True)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
