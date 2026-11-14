#!/usr/bin/env python3
"""Test «🔍 Lupe» im Live-Bild (MoveEye Teil 639zzzl) – mit der Demo-Kamera, ohne echte Kamera und ohne echte Servos:

  A) im eigenen Prozess: Bereich prüfen (Zahlen, Grenzen), Ort in der Welt bei gedrehtem Kopf, Eimer pro Benutzer, wann der Kopf
     nicht folgt (Not-Aus, «Aus», Folgen, Gehtest, Simulator-Aufgabe), wann das Scharfbild pausiert (Alarm, Kopf fährt).
  B) MoveEye ohne Fenster (--demo; die Demo hat für den Test einen Kopf: live_has_head = an), /api/lupe/crop.jpg:
     Rechte (Admin, Familie mit Kopf, Kind / «nur ansehen» ohne Kopf, «Eigene Rechte» ohne Live, ohne Anmeldung, Gast-Link),
     Grenzen (keine Zahl, NaN, ausserhalb, zu breit), Eimer (429), Privatsphäre-Zone bleibt schwarz im Ausschnitt, schärfer als
     derselbe Ausschnitt aus dem Live-Strom (Laplace-Varianz), Scharfbild pausiert bei Person im Bild, Kopf zielen erlaubt / nicht
     (Kind 403, Not-Aus 409), der Ausschnitt folgt dem Ort, wenn der Kopf dreht, Gast nie den Kopf.
  D) Fenster (Tk) mit einem Ersatz-tkinter (hier gibt es kein tkinter, kein echtes Fenster): Knopf «🔍 Lupe», Rahmen ziehen, Mausrad,
     verschieben, Doppelklick, Esc; Scharfbild über dieselbe lupe_crop() und denselben Eimer lupe_rate(), Kopf über lupe_aim() (Not-Aus).
  C) --browser (Playwright, Chromium): Handy 390 × 844 mit Berührung (echte Touch-Ereignisse über CDP): Knopf «Lupe», Rahmen
     ziehen, scharfes Bild, zwei Finger zoomen (die Seite zoomt nicht, scrollt nicht), ein Finger verschiebt, Doppeltipp = 1:1,
     nochmals = zu; zwei Finger auf dem normalen Bild öffnen die Lupe; quer 844 × 390; Vollbild (#vo-lupe); PC: Maus ziehen,
     Rad, Doppelklick, Esc; Kopf folgt (Admin) / kein 🎯 (Kind); Leiste passt bei 390 px in allen 5 Sprachen; keine JS-Fehler.
     --bilder ORDNER: lupe_*.png

  python3 werkzeuge/lupe_test.py [--datei X.py] [--browser] [--bilder ORDNER]
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
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}
PW = "Lupe-" + base64.b16encode(os.urandom(5)).decode().lower()


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


def schaerfe(jpg_or_img, size=None):
    """Laplace-Varianz (je höher, desto mehr feine Einzelheiten); size = auf diese Grösse bringen (gleicher Massstab)"""
    import cv2
    import numpy as np
    im = cv2.imdecode(np.frombuffer(jpg_or_img, np.uint8), cv2.IMREAD_GRAYSCALE) if isinstance(jpg_or_img, (bytes, bytearray)) else jpg_or_img
    if size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_CUBIC if im.shape[1] < size[0] else cv2.INTER_AREA)
    return float(cv2.Laplacian(im, cv2.CV_64F).var())


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    print("A) im eigenen Prozess", flush=True)
    home = tempfile.mkdtemp(prefix="mw_lupe_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_lupe_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["log_event"] = lambda *a, **k: None
    ok(ns["lupe_selftest"]().startswith("region"), "Selbsttest lupe_selftest")
    box = ns["lupe_box"]
    ok(box("1e9", "-1e9", "0.5", "0.5") == [0.5, 0.0, 0.5, 0.5], "riesige Zahlen: in das Bild geklemmt")
    ok(box(None, 0, 1, 1) is None and box("inf", 0, 1, 1) is None and box([1], 0, 1, 1) is None, "keine / unendliche / falsche Zahl: abgewiesen")
    sh = ns["lupe_shift"]
    b, out = sh([0.45, 0.45, 0.1, 0.1], (-20.0, 0.0), (0.0, 0.0), (66.0, 41.0))
    ok(abs(b[0] - (0.45 - 20 / 66)) < 1e-9 and out == 0.0, f"Kopf 20° nach rechts gedreht: der Ort steht weiter links im Bild ({b[0]:.3f})")
    b, out = sh([0.45, 0.45, 0.1, 0.1], (179.0, 0.0), (-179.0, 0.0), (66.0, 41.0))
    ok(abs(b[0] - (0.45 - 2 / 66)) < 1e-9, "360°-Servo: über ±180° gerechnet (2°, nicht 358°)")
    b, out = sh([0.45, 0.45, 0.1, 0.1], (60.0, 0.0), (0.0, 0.0), (66.0, 41.0))
    ok(b[0] == 0.9 and out > 0.5, f"weit weg gedreht: am Rand, «nicht mehr im Bild» ({out:.1f})")
    CFG, STATE, KOPF = ns["CFG"], ns["STATE"], ns["KOPF"]
    hb = ns["lupe_head_block"]
    ok(hb() == "", "Kopf frei: die Lupe darf drehen")
    CFG["servo_estop"] = True
    ok("emergency" in hb(), "Not-Aus: der Kopf folgt nicht")
    CFG["servo_estop"] = False
    CFG.update(kopf_parked=True, kopf_park=True, kopf_on=True)
    ok("looks away" in hb(), "«Aus»: die Kamera schaut weg (Privatsphäre) – die Lupe dreht nicht zurück")
    CFG["kopf_parked"] = False
    STATE["tracking"] = True
    ok("follows" in hb(), "Folgen / Alarm hat Vorrang vor der Lupe")
    STATE["tracking"] = False
    ns["REFSCAN"]["busy"] = "scan"
    ok("reference" in hb(), "Referenz-Scan hat Vorrang")
    ns["REFSCAN"]["busy"] = ""
    ns["TESTOPT"]["busy"] = "x"
    ok("simulator task" in hb(), "Simulator-Aufgabe (Testlauf, Platz einrichten …) hat Vorrang")
    ns["TESTOPT"]["busy"] = ""
    sb = ns["lupe_still_block"]
    ok(sb() == "", "Scharfbild erlaubt")
    STATE["persons"] = 1
    ok(sb() == "alarm", "Person im Bild: Scharfbild pausiert (die Erkennung geht vor)")
    STATE["persons"] = 0
    ns["SRV"]["pos"] = [10.0, 50.0]; ns["SRV"]["vel"] = [3.0, 0.0]
    ok(sb() == "moving", "Kopf fährt: Scharfbild pausiert")
    ns["SRV"]["pos"] = None; ns["SRV"]["vel"] = [0.0, 0.0]
    # aim: the target in % from the middle of the region (kopf_pic_to_pan), «by hand» like the joystick
    ns["live_has_head"] = lambda: True
    CFG.update(pan=50.0, tilt=50.0)
    good, code, res = ns["lupe_aim"]([0.7, 0.4, 0.2, 0.2], ("k", "Test"), "de")
    ok(good and code == 200 and CFG["pan"] > 50.0 and ns["manual_active"](), f"Zielen: Kopf dreht nach rechts, «Hand» wie der Joystick ({res})")
    CFG["servo_estop"] = True
    good, code, res = ns["lupe_aim"]([0.1, 0.1, 0.2, 0.2], ("k", "Test"), "de")
    ok(not good and code == 409 and "Not-Aus" in res["msg"], f"Zielen bei Not-Aus: nein, mit Grund auf Deutsch ({res['msg']})")
    CFG["servo_estop"] = False
    shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
WRAP = r'''
import json, os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
_lt_clock = os.environ.get("MW_LUPE_CLOCK", "")
_lt_dr = DemoSource.read
def _lt_read(self):                      # the demo clock from a file: 40 = quiet meadow, 16 = a person walks past the tent
    try:
        self.t0 = time.time() - float(open(_lt_clock).read().strip() or 40)
    except Exception:
        self.t0 = time.time() - 40.0
    return _lt_dr(self)
DemoSource.read = _lt_read
live_has_head = lambda: True             # the test: the demo has a pan / tilt head
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
'''


def mjpeg_frame(op, url, headers, timeout=15):
    """one picture of the live stream (/video_feed) - what the page shows"""
    r = urllib.request.Request(url, headers=headers)
    with op.open(r, timeout=timeout) as x:
        buf = b""
        t0 = time.time()
        while time.time() - t0 < timeout:
            buf += x.read(4096)
            a = buf.find(b"\xff\xd8")
            e = buf.find(b"\xff\xd9", a + 2) if a >= 0 else -1
            if a >= 0 and e > a:
                # skip the first picture (may be older), take the second
                rest = buf[e + 2:]
                a2 = rest.find(b"\xff\xd8")
                e2 = rest.find(b"\xff\xd9", a2 + 2) if a2 >= 0 else -1
                if a2 >= 0 and e2 > a2:
                    return rest[a2:e2 + 2]
    return None


def teil_b(datei, browser, bilder):
    import cv2
    import numpy as np
    print("B) MoveEye mit Demo-Kamera", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_lupe_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    clock = os.path.join(tmp, "clock.txt"); open(clock, "w").write("40")
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "web_width": 960, "web_quality": 75, "cam_hfov": 66.0, "cam_vfov": 41.0,
          "kopf_park": False,   # «Aus» without the privacy look-away (that one blocks the magnifier on purpose, part A)
          "extra_cams": ["usb:0"], "kopf_ov": "usb:0", "cam_fov": {"usb:0": {"model": "own", "deg": 102}}}   # the small picture #v3-mini (639zv) and the tiles
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_LUPE_CLOCK=clock)
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW)):
        h = dict(basic(*user)) if user else {}
        h["Content-Type"] = "application/json"
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with op.open(r, timeout=60) as x:
                b = x.read()
                return x.status, (json.loads(b) if x.headers.get_content_type() == "application/json" else b), dict(x.headers)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b), dict(e.headers)
            except ValueError:
                return e.code, b, dict(e.headers)

    def crop(q, user=("admin", PW), g=None, tries=8):
        for _i in range(tries):                          # 429 = the bucket: wait a moment (only where the test does not want it)
            c, b, h = req((g or "/api/lupe") + "/crop.jpg?" + q, user=user)
            if c != 429:
                return c, b, h
            time.sleep(0.8)
        return c, b, h

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(3)
        req("/api/arm", {"action": "disarm"})                   # the demo starts in «Wachsam»: the guard rule is tested below on its own
        for n, r in {"Anna": "family", "Kim": "kid", "Vera": "view", "Cus": "custom"}.items():
            req("/api/users", {"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        req("/api/users", {"action": "update", "name": "Cus", "perms": ["rec"]})
        A, K, V, C = ("Anna", "anna-pass-1"), ("Kim", "kim-pass-1"), ("Vera", "vera-pass-1"), ("Cus", "cus-pass-1")
        c, j, _h = req("/api/lupe?lang=de")
        ok(c == 200 and j.get("head_right") and j.get("has_head") and j.get("sharp") == "sensor" and j.get("fov") == [66.0, 41.0] and not j.get("armed"),
           f"Zustand (Admin): Kopf-Recht, Kopf, Scharfbild vom «Sensor», Blickwinkel ({j})")
        print("B) Rechte", flush=True)
        q = "cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=800"
        c, b, h = crop(q)
        ok(c == 200 and bytes(b[:2]) == b"\xff\xd8" and h.get("X-Lupe-Src") == "sensor", f"Admin: Ausschnitt als JPEG, scharf vom Sensor ({c} {h.get('X-Lupe-Src')})")
        for who, nm in ((A, "Familie"), (K, "Kind"), (V, "nur ansehen")):
            c, b, h = crop(q, who)
            ok(c == 200 and bytes(b[:2]) == b"\xff\xd8", f"{nm} (Recht Live): Ausschnitt ja ({c})")
        ok(crop(q, C)[0] == 403 and req("/api/lupe?lang=de", user=C)[0] == 403, "Eigene Rechte ohne Live: kein Ausschnitt, kein Zustand (403)")
        ok(req("/api/lupe/crop.jpg?" + q, user=None)[0] == 401, "ohne Anmeldung: 401")
        c, j, _h = req("/api/lupe?lang=de", user=K)
        ok(c == 200 and not j.get("head_right"), "Kind: kein Kopf-Recht im Zustand")
        print("B) Grenzen", flush=True)
        for bad, why in (("x=abc&y=0&w=0.5&h=0.5", "keine Zahl"), ("x=nan&y=0&w=0.5&h=0.5", "NaN"), ("x=0&y=0&w=inf&h=0.5", "unendlich"),
                         ("x=0.1&y=0.1&w=0.2", "h fehlt"), ("x=0.1&y=0.1&w=0.2&h=0.2&ref=1,abc", "ref keine Zahl"), ("x=0.1&y=0.1&w=0.2&h=0.2&ref=9999,0", "ref zu gross")):
            ok(crop("cam=head&" + bad)[0] == 400, f"Grenzen: {why} -> 400")
        c, b, h = crop("cam=head&x=-5&y=7&w=0.3&h=0.3&ow=600")
        bx = [float(v) for v in h.get("X-Lupe-Box", "0,0,0,0").split(",")]
        ok(c == 200 and abs(bx[0]) < 1e-6 and abs(bx[1] + bx[3] - 1.0) < 0.01, f"ausserhalb: in das Bild geklemmt ({bx})")
        c, b, h = crop("cam=head&x=0&y=0&w=1&h=1&ow=99999")
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR) if c == 200 else None
        ok(im is not None and im.shape[1] <= 2048, f"Ausgabe höchstens 2048 px breit ({None if im is None else im.shape[1]})")
        c, b, h = crop("cam=head&x=0.4&y=0.4&w=0.0001&h=0.0001&ow=400")
        bx = [float(v) for v in h.get("X-Lupe-Box", "0,0,0,0").split(",")]
        ok(c == 200 and bx[2] >= 0.0199, f"kleinster Bereich 1/50 ({bx[2]:.4f})")
        print("B) Eimer (Rate)", flush=True)
        time.sleep(3)
        codes = [req("/api/lupe/crop.jpg?cam=head&x=0.1&y=0.1&w=0.2&h=0.2&ow=200", user=V)[0] for _i in range(14)]
        ok(429 in codes and codes[0] == 200, f"zu viele Anfragen hintereinander: 429 ({codes})")
        time.sleep(3)
        ok(crop("cam=head&x=0.1&y=0.1&w=0.2&h=0.2&ow=200", V, tries=1)[0] == 200, "nach einer Pause wieder 200")
        print("B) schärfer als der Live-Strom", flush=True)
        time.sleep(1)
        region = (0.78, 0.62, 0.12, 0.12)                       # the sign next to the tent (fine writing, 1-px stripes)
        c, b, h = crop("cam=head&x=%s&y=%s&w=%s&h=%s&ow=1200" % region)
        frame = mjpeg_frame(op, base + "/video_feed", basic("admin", PW))
        if c == 200 and frame:
            sf = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_GRAYSCALE)
            H_, W_ = sf.shape
            bx = [float(v) for v in h.get("X-Lupe-Box").split(",")]
            part = sf[int(bx[1] * H_):int((bx[1] + bx[3]) * H_), int(bx[0] * W_):int((bx[0] + bx[2]) * W_)]
            hi = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_GRAYSCALE)
            s_hi, s_lo = schaerfe(hi), schaerfe(part, (hi.shape[1], hi.shape[0]))
            ok(hi.shape[1] >= 2.5 * part.shape[1] and s_hi > 2.0 * s_lo,
               f"Lupe {hi.shape[1]} px statt {part.shape[1]} px aus dem Strom; feine Einzelheiten {s_hi:.0f} > 2 × {s_lo:.0f} (Laplace)")
            if bilder:
                os.makedirs(bilder, exist_ok=True)
                cv2.imwrite(os.path.join(bilder, "lupe_scharf_vergleich.png"),
                            np.hstack([cv2.resize(part, (hi.shape[1], hi.shape[0]), interpolation=cv2.INTER_CUBIC), hi]))
        else:
            ok(False, f"Vergleich: Ausschnitt {c}, Strom {bool(frame)}")
        print("B) Privatsphäre-Zone", flush=True)
        z = {"name": "Nachbar", "mode": "privacy", "points": [[0.0, 0.0], [0.4, 0.0], [0.4, 0.5], [0.0, 0.5]]}
        c, j, _h = req("/api/zones", {"zones": [z], "lang": "de"})
        ok(c == 200 and j.get("ok"), f"Privatsphäre-Zone links oben gesetzt ({j})")
        time.sleep(3.5)                                             # a new still after the zone (the old one is older than the gap)
        c, b, h = crop("cam=head&x=0.05&y=0.05&w=0.3&h=0.3&ow=600")
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_GRAYSCALE) if c == 200 else None
        ok(im is not None and h.get("X-Lupe-Src") == "sensor" and float(im.mean()) < 4.0,
           f"Ausschnitt ganz in der Zone: schwarz, auch vom Sensor-Standbild (Mittel {None if im is None else round(float(im.mean()), 1)})")
        c, b, h = crop("cam=head&x=0.2&y=0.1&w=0.4&h=0.4&ow=800")
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_GRAYSCALE) if c == 200 else None
        if im is not None:
            Hh, Ww = im.shape
            left, right = float(im[: int(Hh * 0.9), : int(Ww * 0.45)].mean()), float(im[:, int(Ww * 0.6):].mean())
            ok(left < 4.0 and right > 40.0, f"halb in der Zone: links schwarz ({left:.1f}), rechts Bild ({right:.1f})")
        else:
            ok(False, "halb in der Zone: kein Bild")
        c, b, h = crop("cam=head&x=0.05&y=0.05&w=0.3&h=0.3&ow=600&ref=-25,8")
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_GRAYSCALE) if c == 200 else None
        ok(im is not None, "auch mit verschobener Richtung (ref) nur Bildinhalt, die Zone bleibt geschwärzt im Bild")
        gp = None
        req("/api/guest", {"action": "create", "hours": 2})
        gp = req("/api/guest")[1]["path"]
        c, b, h = crop("x=0.05&y=0.05&w=0.3&h=0.3&ow=600", None, gp + "/lupe")
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_GRAYSCALE) if c == 200 else None
        ok(im is not None and float(im.mean()) < 4.0, "Gast: Ausschnitt ja, Zone schwarz")
        req("/api/zones", {"zones": [], "lang": "de"})
        ok(req(gp + "/lupe", {"action": "aim", "box": [0.1, 0.1, 0.2, 0.2]}, None)[0] in (404, 405), "Gast: Kopf zielen gibt es nicht")
        c, j, _h = req(gp + "/lupe", user=None)
        ok(c == 200 and not j.get("head_right"), "Gast: Zustand ohne Kopf-Recht")
        ok(req("/g/falsch123/lupe/crop.jpg?x=0&y=0&w=1&h=1", user=None)[0] == 404, "falscher Gast-Link: 404")
        print("B) Kopf zielen, Ort folgt", flush=True)
        ok(req("/api/lupe", {"action": "aim", "box": [0.6, 0.3, 0.2, 0.2], "cam": "head"}, K)[0] == 403, "Kind (ohne Kopf-Recht): Zielen 403")
        ok(req("/api/lupe", {"action": "aim", "box": [0.6, 0.3, 0.2, 0.2], "cam": "head"}, V)[0] == 403, "«nur ansehen»: Zielen 403")
        ok(req("/api/lupe", {"action": "aim", "box": ["x"], "cam": "head"})[0] == 400, "Zielen: falscher Bereich 400")
        ok(req("/api/lupe", {"action": "aim", "box": [0.6, 0.3, 0.2, 0.2], "cam": "wide"})[0] == 400, "Zielen nur in der Kopf-Ansicht")
        c, j, _h = req("/api/lupe?lang=de")
        p0 = j["pose"]
        c, j, _h = req("/api/lupe", {"action": "aim", "box": [0.7, 0.3, 0.2, 0.2], "cam": "head", "lang": "de"}, A)
        ok(c == 200 and j.get("ok"), f"Familie (Kopf-Recht): Zielen ok ({j})")
        for _i in range(25):
            time.sleep(0.2)
            p1 = req("/api/lupe?lang=de")[1]["pose"]
            if abs((p1[0] - p0[0]) - 19.8) < 1.5:
                break
        ok(abs((p1[0] - p0[0]) - 0.3 * 66.0) < 1.5 and abs((p1[1] - p0[1]) - 0.1 * 41.0) < 1.5,
           f"Kopf dreht die Mitte des Bereichs in die Bildmitte: {p0} -> {p1} (soll +19.8° / +4.1°)")
        time.sleep(3)
        c, b, h = crop("cam=head&x=0.7&y=0.3&w=0.2&h=0.2&ow=400&ref=%s,%s" % (p0[0], p0[1]))
        bx = [float(v) for v in h.get("X-Lupe-Box", "0,0,0,0").split(",")]
        ok(c == 200 and abs(bx[0] - 0.4) < 0.02 and abs(bx[1] - 0.4) < 0.02,
           f"der Ausschnitt folgt dem Ort: Bereich jetzt in der Mitte ({bx[:2]}), Richtung im Kopf «X-Lupe-Pose» {h.get('X-Lupe-Pose')}")
        req("/api/servo", {"op": "estop"})
        c, j, _h = req("/api/lupe", {"action": "aim", "box": [0.1, 0.1, 0.2, 0.2], "cam": "head", "lang": "de"})
        ok(c == 409 and "Not-Aus" in (j.get("msg") or ""), f"Not-Aus: Kopf folgt nicht, Grund ({j.get('msg')})")
        c, j, _h = req("/api/lupe?lang=de")
        ok("Not-Aus" in (j.get("block") or ""), "Zustand nennt den Grund (für die Seite)")
        req("/api/servo", {"op": "release"})
        c, j, _h = req("/api/lupe", {"action": "aim", "box": [0.4, 0.4, 0.2, 0.2], "cam": "head", "lang": "de"})
        ok(c == 200, f"nach «Freigeben» wieder ({c})")
        print("B) Scharfbild pausiert bei Person im Bild", flush=True)
        open(clock, "w").write("16")
        t0 = time.time()
        while time.time() - t0 < 20 and not req("/api/lupe?lang=de")[1].get("pause"):
            time.sleep(0.5)
        time.sleep(9)                                               # older than LUPE_HI_MAX_AGE: the last still is not used any more
        c, b, h = crop("cam=head&x=0.3&y=0.5&w=0.3&h=0.3&ow=400")
        ok(c == 200 and h.get("X-Lupe-Src") == "frame" and h.get("X-Lupe-Note") == "alarm",
           f"Person im Bild: volles Kamerabild statt Sensor, Hinweis «alarm» ({h.get('X-Lupe-Src')}, {h.get('X-Lupe-Note')})")
        open(clock, "w").write("40")
        print("B) Wache an: Scharfbild nur auf Wunsch, höchstens alle 10 s", flush=True)
        t0 = time.time()
        while time.time() - t0 < 30 and req("/api/lupe?lang=de")[1].get("pause"):
            time.sleep(0.5)
        req("/api/arm", {"action": "arm_now"})

        def ruhig(limit=30):                                    # no person / recording / following: a still may be taken
            t1 = time.time()
            while time.time() - t1 < limit and req("/api/lupe?lang=de")[1].get("pause"):
                time.sleep(0.5)
        j = req("/api/lupe?lang=de")[1]
        ok(j.get("armed") and j.get("armed_gap") == 10.0, f"Schutz an: Zustand «armed» ({j.get('armed')})")
        time.sleep(16)                                              # older than LUPE_ARMED_KEEP: no still in use
        n0 = req("/api/lupe?lang=de")[1]["stills"]
        srcs = []
        for _i in range(5):
            c, b, h = crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400")
            srcs.append((h.get("X-Lupe-Src"), h.get("X-Lupe-Note"))); time.sleep(1.0)
        n1 = req("/api/lupe?lang=de")[1]["stills"]
        ok(n1 == n0 and all(x[0] == "frame" and x[1] in ("armed", "alarm") for x in srcs), f"Schutz an, ohne Wunsch: 5 s lang kein Standbild (Kamera-Frame, Hinweis «armed») {srcs}, Standbilder {n0} -> {n1}")
        ruhig()
        c, b, h = crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400&want=1")
        n2 = req("/api/lupe?lang=de")[1]["stills"]
        ok(h.get("X-Lupe-Src") == "sensor" and n2 == n1 + 1, f"Schutz an, auf Wunsch (neuer Rahmen / «◐ Scharf»): genau ein Standbild ({h.get('X-Lupe-Src')}, {n1} -> {n2})")
        c, b, h = crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400&want=1")
        n3 = req("/api/lupe?lang=de")[1]["stills"]
        ok(n3 == n2 and h.get("X-Lupe-Note") == "armed_wait" and h.get("X-Lupe-Src") == "sensor",
           f"gleich nochmals gewünscht: kein zweites (höchstens 1 pro 10 s), das letzte bleibt ({h.get('X-Lupe-Note')}, {n3})")
        for _i in range(4):
            crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400"); time.sleep(1.0)
        ok(req("/api/lupe?lang=de")[1]["stills"] == n3, "dazwischen ohne Wunsch: keines")
        time.sleep(6.5); ruhig()
        c, b, h = crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400&want=1")
        n4 = req("/api/lupe?lang=de")[1]["stills"]
        ok(n4 == n3 + 1, f"nach 10 s wieder eines auf Wunsch ({n3} -> {n4})")
        req("/api/arm", {"action": "disarm"}); time.sleep(0.5)
        for _i in range(4):
            crop("cam=head&x=0.78&y=0.62&w=0.12&h=0.12&ow=400"); time.sleep(0.8)
        n5 = req("/api/lupe?lang=de")[1]["stills"]
        ok(n5 >= n4 + 2, f"Schutz aus: wieder laufend (ohne Wunsch) ({n4} -> {n5})")
        if browser:
            teil_c(base, gp, bilder, (A, K))
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
def teil_c(base, gp, bilder, users):
    from playwright.sync_api import sync_playwright
    print("C) Browser", flush=True)
    os.makedirs(bilder, exist_ok=True)
    A, K = users
    init = ("try{localStorage.setItem('mw-lang','__L__');localStorage.setItem('mw-theme','dark');localStorage.removeItem('mw-view3');"
            "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\"]');localStorage.setItem('mw-lv-knoepfe','1');localStorage.removeItem('mw-lupe')}catch(e){}")

    def page(br, vp, mob, user=("admin", PW), lang="de"):
        ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=3 if mob else 1,
                             http_credentials={"username": user[0], "password": user[1]}, locale="de-CH")
        ctx.add_init_script(init.replace("__L__", lang))
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + "/", wait_until="domcontentloaded")
        if pg.evaluate("() => (typeof LANG !== 'undefined' && LANG) || ''") != lang:   # one language for all (639zb): set it, load again
            pg.evaluate("async l => { await fetch('/api/ui', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': l}})}); }", lang)
            pg.goto(base + "/", wait_until="domcontentloaded")
        pg.wait_for_function("() => { const v = document.getElementById('video'); return v && v.naturalWidth > 0 && document.getElementById('lv-b-lupe'); }", timeout=40000)
        pg.wait_for_timeout(700)
        return ctx, pg, errs

    def lupe_knopf(pg, warten=500):
        """«Lupe» antippen wie ein Mensch: sind die Knöpfe des Live-Bilds gerade versteckt (nur 4 s nach einem Tipp, 639zzj), holt der
        erste Tipp sie zurück - dann noch einmal (langsamer CI-Rechner: 14.11.2026 viermal rot nur deswegen)"""
        for _i in range(3):
            pg.locator("#lv-b-lupe").click()
            try:
                pg.wait_for_selector("#lupe-ov", timeout=2500)
                break
            except Exception:
                continue
        pg.wait_for_selector("#lupe-ov", timeout=5000); pg.wait_for_timeout(warten)

    def touch(cdp, kind, pts):
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [{"x": x, "y": y, "id": i, "radiusX": 4, "radiusY": 4, "force": 1}
                                                                          for i, (x, y) in enumerate(pts)]})

    def drag1(cdp, a, b, steps=8):
        touch(cdp, "touchStart", [a])
        for k in range(1, steps + 1):
            touch(cdp, "touchMove", [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)])
        touch(cdp, "touchEnd", [])

    def pinch(cdp, c, d0, d1, steps=8, vert=False):
        pp = (lambda d: [(c[0], c[1] - d), (c[0], c[1] + d)]) if vert else (lambda d: [(c[0] - d, c[1]), (c[0] + d, c[1])])
        touch(cdp, "touchStart", pp(d0))
        for k in range(1, steps + 1):
            touch(cdp, "touchMove", pp(d0 + (d1 - d0) * k / steps))
        touch(cdp, "touchEnd", [])

    def tap(cdp, a):
        touch(cdp, "touchStart", [a]); touch(cdp, "touchEnd", [])

    st = lambda pg: pg.evaluate("() => window.mwLupe.state()")
    LAY = """() => { const vis = e => e && !e.hidden && e.getClientRects().length && getComputedStyle(e).display !== 'none';
      const R = e => e.getBoundingClientRect(), hit = (a, b) => a.left < b.right - 0.5 && b.left < a.right - 0.5 && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5;
      const tb = [...document.querySelectorAll('#lv-tools > *')].filter(vis);
      const oth = [...document.querySelectorAll('#v3-mini, #kw-row .kw-t, #kw-row > button, #lv-joy > *, .vtag')].filter(vis);
      const bad = []; tb.forEach(b => oth.forEach(o => { if (hit(R(b), R(o))) bad.push((b.id || b.className) + '/' + (o.id || o.className)); }));
      const m = document.getElementById('v3-mini'); let mini = null;
      if (vis(m)) { const r = R(m), e = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2); mini = !!(e && m.contains(e)); }
      return {bad: bad, mini: mini, n: tb.length, wrap: document.getElementById('lv-tools').classList.contains('lvt-wrap'), lupe: !!document.getElementById('lv-b-lupe')}; }"""
    scale = lambda pg: pg.evaluate("() => window.visualViewport ? visualViewport.scale : 1")
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        # ---- phone (portrait), touch ----
        ctx, pg, errs = page(br, {"width": 390, "height": 844}, True)
        cdp = ctx.new_cdp_session(pg)
        pg.wait_for_function("() => { const m = document.getElementById('v3-mini'); return m && !m.hidden; }", timeout=20000)
        pg.wait_for_timeout(1500)
        lay = pg.evaluate(LAY)
        ok(lay["lupe"] and not lay["bad"] and lay["mini"], f"Handy hoch: Knopfleiste deckt das kleine Bild, die Kacheln, den Joystick nicht ({lay})")
        pg.evaluate("() => scrollTo(0, 0)")
        lupe_knopf(pg, 500)
        r = pg.locator("#lupe-ov").bounding_box()
        ok(r and r["width"] > 300 and pg.evaluate("() => document.body.classList.contains('lupe-on')"), f"Handy: Lupe offen über dem Bild ({r and round(r['width'])} px)")
        ok(pg.locator("#lupe-x").is_visible() and "Lupe" in pg.inner_text("#lupe-x"), "Handy: «✕ Lupe» sichtbar (der Weg zurück)")
        ok(pg.locator("#lupe-head").is_visible() and "on" in pg.get_attribute("#lupe-head", "class"), "Handy, Admin: «🎯 Kopf folgt» da und ab Werk an")
        pg.locator("#lupe-head").click(); pg.wait_for_timeout(150)
        ok(not st(pg)["follow"] and pg.evaluate("() => JSON.parse(localStorage.getItem('mw-lupe')).follow") == 0, "Handy: «🎯 Kopf folgt» aus (pro Browser gemerkt)")
        pg.screenshot(path=os.path.join(bilder, "lupe_handy_offen.png"))
        y0 = pg.evaluate("() => scrollY")
        drag1(cdp, (r["x"] + r["width"] * 0.74, r["y"] + r["height"] * 0.58), (r["x"] + r["width"] * 0.94, r["y"] + r["height"] * 0.80))
        pg.wait_for_timeout(400)
        s = st(pg)
        ok(s["on"] and s["view"][2] < 0.3, f"Handy: Rahmen gezogen = Bereich gross (×{1 / s['view'][2]:.1f})")
        ok(pg.evaluate("() => scrollY") == y0 and scale(pg) == 1, "Handy: Ziehen im Bild scrollt / zoomt die Seite nicht")
        pg.wait_for_function("() => { const h = document.querySelector('#lupe-ov .lupe-hi'); return h && !h.hidden && h.naturalWidth > 0; }", timeout=15000)
        s = st(pg)
        ok(s["hi"] and s["hi"]["src"] == "sensor", f"Handy: scharfes Bild über dem Bereich ({s['hi'] and s['hi']['src']}, {s['hi'] and s['hi']['size']})")
        ok("scharf" in s["msg"] and "×" in s["msg"], f"Handy: Anzeige «×… · scharf …» ({s['msg'][:80]!r})")
        tr_ = pg.evaluate("() => document.getElementById('video').style.transform")
        ok("scale(" in tr_, "Handy: das Live-Bild selbst ist vergrössert (darunter, live)")
        pg.screenshot(path=os.path.join(bilder, "lupe_handy_rahmen.png"))
        v0 = s["view"]
        pinch(cdp, (r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.5), 40, 90)
        pg.wait_for_timeout(300)
        s = st(pg)
        ok(s["view"][2] < v0[2] * 0.75, f"Handy: zwei Finger auseinander = mehr Zoom ({1 / v0[2]:.1f} -> {1 / s['view'][2]:.1f})")
        ok(scale(pg) == 1, "Handy: die Seite zoomt beim Zwei-Finger-Zoom nicht (visualViewport.scale = 1)")
        v1 = s["view"]
        drag1(cdp, (r["x"] + r["width"] * 0.3, r["y"] + r["height"] * 0.5), (r["x"] + r["width"] * 0.6, r["y"] + r["height"] * 0.5))
        pg.wait_for_timeout(300)
        s = st(pg)
        ok(s["view"][0] < v1[0] - 0.005 and abs(s["view"][2] - v1[2]) < 1e-6, f"Handy: ein Finger verschiebt ({v1[0]:.3f} -> {s['view'][0]:.3f})")
        ok(pg.evaluate("() => scrollY") == y0, "Handy: Verschieben scrollt die Seite nicht")
        pg.wait_for_timeout(1200)
        pg.screenshot(path=os.path.join(bilder, "lupe_handy_zoom.png"))
        c = (r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.6)
        tap(cdp, c); pg.wait_for_timeout(120); tap(cdp, c); pg.wait_for_timeout(300)
        s = st(pg)
        ok(s["on"] and s["view"][2] == 1, "Handy: Doppeltipp = ganzes Bild (1:1)")
        ok(pg.evaluate("() => document.getElementById('video').style.transform") == "", "Handy: Live-Bild wieder normal")
        tap(cdp, c); pg.wait_for_timeout(120); tap(cdp, c); pg.wait_for_timeout(300)
        ok(not st(pg)["on"] and pg.locator("#lupe-ov").count() == 0 and not pg.evaluate("() => document.body.classList.contains('lupe-on')"),
           "Handy: Doppeltipp im ganzen Bild = Lupe zu")
        ok(pg.evaluate("() => document.body.classList.contains('videoonly')") is False, "Handy: der Doppeltipp der Lupe schaltet nicht ins Vollbild")
        # two fingers on the normal picture: the magnifier opens and zooms (the page stays)
        pg.wait_for_timeout(500)
        vb = pg.locator("#video").bounding_box()
        cc = (vb["x"] + vb["width"] * 0.4, vb["y"] + vb["height"] * 0.78)          # (top: the camera tiles 639zzi, right below: the joystick)
        hit = pg.evaluate("([y, a, b]) => [a, b].map(x => { const e = document.elementFromPoint(x, y); return e ? (e.id || e.className || e.tagName) : '-'; })",
                          [cc[1], cc[0] - 55, cc[0] + 55])
        ok(hit == ["video", "video"], f"Handy: an diesen Stellen liegt nur das Bild (kein Knopf, keine Kachel) {hit} {vb}")
        pinch(cdp, cc, 20, 55)
        pg.wait_for_timeout(400)
        s = st(pg)
        ok(s["on"] and s["view"][2] < 0.8 and scale(pg) == 1, f"Handy: zwei Finger auf dem normalen Bild öffnen die Lupe (×{1 / s['view'][2]:.1f}), Seite bleibt")
        pg.locator("#lupe-x").click(); pg.wait_for_timeout(200)
        ok(not st(pg)["on"], "Handy: «✕ Lupe» schliesst")
        # one finger on the normal picture: still the page (scroll / tap shows the buttons) - nothing changed there
        drag1(cdp, (vb["x"] + vb["width"] * 0.5, vb["y"] + vb["height"] * 0.8), (vb["x"] + vb["width"] * 0.5, vb["y"] + vb["height"] * 0.2))
        pg.wait_for_timeout(300)
        ok(not st(pg)["on"], "Handy: ein Finger auf dem normalen Bild öffnet keine Lupe")
        # full screen: the round button next to ✕
        pg.evaluate("() => setVideoOnly(true)"); pg.wait_for_timeout(700)
        ok(pg.locator("#vo-lupe").is_visible(), "Vollbild: Knopf «Lupe» oben rechts")
        pg.locator("#vo-lupe").click(); pg.wait_for_timeout(400)
        r2 = pg.locator("#lupe-ov").bounding_box()
        drag1(cdp, (r2["x"] + r2["width"] * 0.3, r2["y"] + r2["height"] * 0.3), (r2["x"] + r2["width"] * 0.6, r2["y"] + r2["height"] * 0.5))
        pg.wait_for_timeout(1500)
        s = st(pg)
        ok(s["on"] and s["view"][2] < 0.5 and pg.locator("#vo-exit").is_visible() and not pg.locator("#vo-side").is_visible(),
           "Vollbild: Lupe zoomt, ✕ des Vollbilds bleibt, ⇆ ausgeblendet")
        ok(pg.evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1"), "Vollbild: nichts ragt seitlich hinaus")
        pg.screenshot(path=os.path.join(bilder, "lupe_vollbild_handy.png"))
        pg.locator("#lupe-x").click(); pg.evaluate("() => setVideoOnly(false)"); pg.wait_for_timeout(400)
        ok(not errs, f"Handy: keine JavaScript-Fehler {errs}")
        ctx.close()
        # ---- phone (landscape) ----
        ctx, pg, errs = page(br, {"width": 844, "height": 390}, True)
        cdp = ctx.new_cdp_session(pg)
        pg.wait_for_timeout(1500)
        lay = pg.evaluate(LAY)
        ok(lay["lupe"] and not lay["bad"] and lay["mini"] is not False, f"Handy quer: Knopfleiste deckt nichts ({lay})")
        lupe_knopf(pg, 300)
        r = pg.locator("#lupe-ov").bounding_box()
        drag1(cdp, (r["x"] + r["width"] * 0.2, r["y"] + r["height"] * 0.3), (r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.7))
        pg.wait_for_timeout(1500)
        s = st(pg)
        ok(s["on"] and s["view"][2] < 0.5 and scale(pg) == 1, f"Handy quer: Rahmen = Zoom ×{1 / s['view'][2]:.1f}")
        pg.screenshot(path=os.path.join(bilder, "lupe_handy_quer.png"))
        ok(not errs, f"Handy quer: keine JavaScript-Fehler {errs}")
        ctx.close()
        # ---- PC: mouse ----
        ctx, pg, errs = page(br, {"width": 1366, "height": 860}, False)
        lupe_knopf(pg, 500)
        r = pg.locator("#lupe-ov").bounding_box()
        pa = pg.evaluate("async () => (await fetch('/api/lupe?lang=de')).json()")["pose"]
        pg.mouse.move(r["x"] + r["width"] * 0.7, r["y"] + r["height"] * 0.3); pg.mouse.down()
        pg.mouse.move(r["x"] + r["width"] * 0.9, r["y"] + r["height"] * 0.5, steps=6); pg.mouse.up()
        pg.wait_for_timeout(400)
        s = st(pg)
        ok(s["on"] and s["view"][2] < 0.3, f"PC: Maus zieht Rahmen (×{1 / s['view'][2]:.1f})")
        for _i in range(25):
            j_ = pg.evaluate("async () => (await fetch('/api/lupe?lang=de')).json()")
            if j_["pose"][0] - pa[0] > 5:
                break
            pg.wait_for_timeout(200)
        ok(j_["pose"][0] - pa[0] > 5, f"PC, Admin: «Kopf folgt» – der Kopf dreht zum Bereich (Schwenk {pa[0]:.1f}° -> {j_['pose'][0]:.1f}°)")
        pg.wait_for_timeout(1500)
        s = st(pg)
        cx = s["view"][0] + s["view"][2] / 2
        want = 0.8 + (s["ref"][0] - s["pose"][0]) / 66.0 if s["ref"] else 0.8      # the place in the world (the patrol may turn on)
        ok(abs(cx - want) < 0.03 and abs(want - 0.5) < 0.3,
           f"PC: der Bereich bleibt auf dem Ort, der Kopf bringt ihn zur Mitte (Mitte {cx:.2f}, soll {want:.2f}, Kopf {s['pose'][0]:.1f}°)")
        v0 = s["view"][2]
        pg.mouse.move(r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.5); pg.mouse.wheel(0, -300); pg.wait_for_timeout(300)
        ok(st(pg)["view"][2] < v0 * 0.9, "PC: Mausrad zoomt hinein")
        pg.mouse.wheel(0, 300); pg.wait_for_timeout(200)
        sy = pg.evaluate("() => scrollY")
        pg.mouse.wheel(0, 300); pg.wait_for_timeout(200)
        ok(pg.evaluate("() => scrollY") == sy, "PC: das Rad über der Lupe scrollt die Seite nicht")
        pg.mouse.dblclick(r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.5); pg.wait_for_timeout(300)
        ok(st(pg)["view"][2] == 1 and not pg.evaluate("() => document.body.classList.contains('videoonly')"), "PC: Doppelklick = ganzes Bild, kein Vollbild")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
        ok(not st(pg)["on"], "PC: Esc schliesst die Lupe")
        pg.mouse.move(r["x"] + r["width"] * 0.5, r["y"] + r["height"] * 0.5)
        pg.keyboard.down("Control"); pg.mouse.wheel(0, -120); pg.keyboard.up("Control"); pg.wait_for_timeout(300)
        ok(st(pg)["on"] and st(pg)["view"][2] < 1, "PC: Strg + Rad (Trackpad-Zoom) über dem Bild öffnet die Lupe")
        pg.screenshot(path=os.path.join(bilder, "lupe_pc.png"))
        pg.keyboard.press("Escape")
        ok(not errs, f"PC: keine JavaScript-Fehler {errs}")
        ctx.close()
        # ---- a user without the right «head»: zoom yes, no 🎯 ----
        ctx, pg, errs = page(br, {"width": 390, "height": 844}, True, K)
        lupe_knopf(pg, 800)
        ok(not pg.locator("#lupe-head").is_visible() and "nicht bewegen" in pg.inner_text("#lupe-ov .lupe-msg"),
           f"Kind: zoomen ja, kein «🎯 Kopf folgt», Hinweis ({pg.inner_text('#lupe-ov .lupe-msg')[:60]!r})")
        pg.evaluate("() => window.mwLupe.zoomTo([0.6, 0.5, 0.2, 0.2])"); pg.wait_for_timeout(1500)
        ok(st(pg)["hi"] is not None, "Kind: scharfes Bild kommt")
        ok(not errs, f"Kind: keine JavaScript-Fehler {errs}")
        ctx.close()
        # ---- protection on: «◐ Scharf» asks for one still, a second one within 10 s waits ----
        ctx, pg, errs = page(br, {"width": 390, "height": 844}, True)
        pg.evaluate("async () => { await fetch('/api/arm', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'arm_now'})}); }")
        lupe_knopf(pg, 800)
        n0 = pg.evaluate("async () => (await (await fetch('/api/lupe?lang=de')).json()).stills")
        pg.evaluate("() => window.mwLupe.zoomTo([0.7, 0.55, 0.2, 0.2])"); pg.wait_for_timeout(2500)
        n1 = pg.evaluate("async () => (await (await fetch('/api/lupe?lang=de')).json()).stills")
        pg.wait_for_timeout(2500)
        n2 = pg.evaluate("async () => (await (await fetch('/api/lupe?lang=de')).json()).stills")
        ok(n1 == n0 + 1 and n2 == n1 and st(pg)["info"].get("armed"), f"Schutz an, Seite: ein Standbild für den Rahmen, dann keines mehr ({n0} -> {n1} -> {n2})")
        pg.locator("#lupe-sharp").click(); pg.wait_for_timeout(1500)
        ok("nächste Scharfbild" in st(pg)["msg"], f"Schutz an: «◐ Scharf» innert 10 s = Hinweis «nächste Scharfbild …» ({st(pg)['msg'][:90]!r})")
        pg.screenshot(path=os.path.join(bilder, "lupe_wache_an.png"))
        pg.evaluate("async () => { await fetch('/api/arm', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'disarm'})}); }")
        ok(not errs, f"Schutz an: keine JavaScript-Fehler {errs}")
        ctx.close()
        # ---- 390 px, all languages, the font of the CI: the bar fits, nothing sticks out ----
        for lang in ("de", "en", "fr", "it", "rm"):
            ctx, pg, errs = page(br, {"width": 390, "height": 844}, True, lang=lang)
            for vp_ in ({"width": 390, "height": 844}, {"width": 844, "height": 390}):
                pg.set_viewport_size(vp_); pg.wait_for_timeout(1200)
                lay = pg.evaluate(LAY)
                ok(not lay["bad"] and lay["mini"] is not False, f"{vp_['width']} × {vp_['height']}, {lang}: Knopfleiste deckt nichts ({lay})")
            pg.set_viewport_size({"width": 390, "height": 844}); pg.wait_for_timeout(800)
            lupe_knopf(pg, 600)
            pg.evaluate("() => window.mwLupe.zoomTo([0.6, 0.5, 0.2, 0.2])"); pg.wait_for_timeout(1500)
            m = pg.evaluate("""() => { const o = document.getElementById('lupe-ov').getBoundingClientRect(), b = document.querySelector('#lupe-ov .lupe-bar');
                const bs = [...b.querySelectorAll('button')].filter(x => !x.hidden).map(x => x.getBoundingClientRect());
                return {inside: bs.every(x => x.left >= o.left - 1 && x.right <= o.right + 1), rows: new Set(bs.map(x => Math.round(x.top))).size,
                        sw: document.documentElement.scrollWidth, iw: innerWidth, msg: document.querySelector('#lupe-ov .lupe-msg').getBoundingClientRect().right <= o.right + 1,
                        txt: b.innerText}; }""")
            ok(pg.evaluate("() => LANG") == lang, f"390 px: Sprache {lang} aktiv")
            ok(m["inside"] and m["msg"] and m["sw"] <= m["iw"] + 1 and m["rows"] <= 2,
               f"390 px, {lang}: Leiste im Bild ({m['rows']} Zeile(n)), nichts ragt hinaus ({m['txt']!r})")
            pg.screenshot(path=os.path.join(bilder, f"lupe_390_{lang}.png"))
            ok(not errs, f"390 px, {lang}: keine JavaScript-Fehler {errs}")
            if lang == "rm":
                pg.evaluate("async () => { await fetch('/api/ui', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': 'de'}})}); }")
            ctx.close()
        # ---- guest page ----
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="de-CH")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(base + gp, wait_until="domcontentloaded")
        pg.wait_for_function("() => { const v = document.getElementById('v'); return v && v.naturalWidth > 0 && document.getElementById('g-lupe'); }", timeout=30000)
        pg.click("#g-lupe"); pg.wait_for_selector("#lupe-ov"); pg.wait_for_timeout(500)
        pg.evaluate("() => window.mwLupe.zoomTo([0.6, 0.5, 0.25, 0.25])"); pg.wait_for_timeout(1800)
        s = st(pg)
        ok(s["on"] and s["hi"] is not None and not s["canAim"] and not pg.locator("#lupe-head").is_visible(), "Gast-Seite: Lupe mit Scharfbild, ohne Kopf")
        ok("Lupe" in pg.inner_text("#lupe-x"), "Gast-Seite: Texte in der Sprache des Browsers")
        pg.screenshot(path=os.path.join(bilder, "lupe_gast_handy.png"))
        ok(not errs, f"Gast-Seite: keine JavaScript-Fehler {errs}")
        ctx.close()
        br.close()



# ---------------------------------------------------------------------------------------------------------------------- D
FAKE_TK = r"""
import sys, types
class W:
    made = []
    def __init__(self, master=None, *a, **k):
        self.master = master; self.k = dict(k); self.binds = {}; self.placed = None; self.dead = False; W.made.append(self)
    def pack(self, *a, **k): pass
    def grid(self, *a, **k): pass
    def place(self, *a, **k): self.placed = k
    def place_forget(self): self.placed = None
    def config(self, **k): self.k.update(k)
    configure = config
    def cget(self, n): return self.k.get(n, "")
    def bind(self, seq, fn=None, add=None):
        if add and seq in self.binds: self.binds[seq].append(fn)
        else: self.binds[seq] = [fn]
    def unbind(self, seq): self.binds.pop(seq, None)
    def destroy(self): self.dead = True
    def winfo_exists(self): return not self.dead
    def winfo_width(self): return self.k.get("_w", 640)
    def winfo_height(self): return self.k.get("_h", 400)
    def after(self, ms, fn=None, *a): return "id"
    def __getattr__(self, n):
        if n.startswith("__"): raise AttributeError(n)
        return lambda *a, **k: None
tk = types.ModuleType("tkinter")
for n in ("Frame", "Button", "Label", "Toplevel", "Canvas", "Entry", "Text", "Tk", "Checkbutton", "Scale", "Menu", "Scrollbar", "Listbox", "PhotoImage", "Radiobutton", "Spinbox", "LabelFrame", "Message", "OptionMenu", "PanedWindow", "Event", "Misc", "Widget"):
    setattr(tk, n, type(n, (W,), {}))
class Var:
    def __init__(self, *a, value=None, **k): self.v = value
    def get(self): return self.v
    def set(self, v): self.v = v
    def trace_add(self, *a, **k): pass
tk.StringVar = tk.IntVar = tk.BooleanVar = tk.DoubleVar = Var
tk.TclError = Exception
for n in ("END", "LEFT", "RIGHT", "BOTH", "X", "Y", "W", "E", "N", "S", "NW", "NE", "HORIZONTAL", "VERTICAL", "DISABLED", "NORMAL"):
    setattr(tk, n, n.lower())
def _mod(name):
    m = types.ModuleType(name); m.__getattr__ = lambda n: (lambda *a, **k: None) if n[:1].islower() else type(n, (W,), {}); sys.modules[name] = m; return m
ttk = _mod("tkinter.ttk"); tk.ttk = ttk
for n in ("messagebox", "filedialog", "simpledialog", "colorchooser", "font"):
    setattr(tk, n, _mod("tkinter." + n))
sys.modules["tkinter"] = tk
pt = types.ModuleType("PIL.ImageTk")
class PhotoImage:
    def __init__(self, im, *a, **k): self.im = im
pt.PhotoImage = PhotoImage
sys.modules["PIL.ImageTk"] = pt
import PIL; PIL.ImageTk = pt
"""


def teil_d(datei):
    """the window (Tk) with a fake tkinter (no tkinter here): the same server functions, the mouse, the picture"""
    print("D) Fenster (Tk) mit Ersatz-tkinter – kein echtes Fenster", flush=True)
    import numpy as np
    exec(FAKE_TK, {})
    home = tempfile.mkdtemp(prefix="mw_lupe_tk_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_lupe_tk", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ok(ns["GUI_OK"], "Ersatz-tkinter geladen: GUI_OK, die Fenster-Teile sind gebaut")
    ns["log_event"] = lambda *a, **k: None
    App, CFG, tkm = ns["App"], ns["CFG"], sys.modules["tkinter"]
    ok(App._update_video is ns["_lupe_tk_update_video"] and App._build_left is ns["_lupe_tk_build_left"], "Fenster: Lupe hängt an _build_left / _update_video")
    ns["live_has_head"] = lambda: True
    ns["v3_cur"] = lambda: "head"
    CFG.update(pan=50.0, tilt=50.0, tk_night=False, servo_estop=False)
    calls = {"crop": [], "rate": [], "aim": []}
    frame = np.zeros((360, 640, 3), np.uint8); frame[:, 320:] = (0, 200, 0)          # the live picture: left black, right green
    sharp = np.full((200, 200, 3), (255, 0, 0), np.uint8)                         # the sharp part: blue
    rate0, aim0 = ns["lupe_rate"], ns["lupe_aim"]

    def crop_spy(cam, box, ref, ow, want=False):
        calls["crop"].append((cam, list(box), ref, ow, want))
        import cv2
        return cv2.imencode(".png", sharp)[1].tobytes(), {"X-Lupe-Box": ",".join("%.5f" % v for v in box), "X-Lupe-Src": "sensor",
                                                          "X-Lupe-Note": "", "X-Lupe-Age": "0.2", "X-Lupe-Pose": "%.3f,%.3f" % tuple(ns["servo_pos_deg"]())}
    ns["lupe_crop"] = crop_spy
    ns["lupe_rate"] = lambda key: (calls["rate"].append(key), rate0(key))[1]
    ns["lupe_aim"] = lambda box, who, lang=None: (calls["aim"].append((list(box), who)), aim0(box, who, lang))[1]

    class Watch:
        frame_out = frame
    a = object.__new__(App)
    a.root = tkm.Frame(); a.watch = Watch(); a.tab = "live"; a.video = None

    def base(self, left):
        vh = tkm.Frame(left); self.video = tkm.Label(vh); self.video.k.update(_w=640, _h=400)
    ns["_lupe_tk_build_left_base"] = base
    a.toggle_video_only = lambda: calls.setdefault("fs", []).append(1)
    a._build_left(tkm.Frame())
    ok(a.b_lupe is not None and "Lupe" in a.b_lupe.cget("text") and a.b_lupe.placed, f"Fenster: Knopf «{a.b_lupe.cget('text')}» oben rechts im Live-Bild")
    ok("<Escape>" in a.root.binds, "Fenster: Esc ist gebunden")
    a.b_lupe.cget("command")()
    L = a._lupe
    bar, st = a._lupe_w
    texts = [w.cget("text") for w in tkm.Button.__mro__[1].made if isinstance(w, tkm.Button) and w.master is bar]
    ok(L["on"] and "✕ Lupe" in texts and "1:1" in texts and "🎯 Kopf folgt" in texts and "◐ Scharf" in texts and a.b_lupe.placed is None,
       f"Fenster: Lupe offen, Leiste {texts}")
    a._update_video()
    g = L["geo"]
    ok(g == (0.0, 20.0, 640.0, 360.0) and a.photo.im.size == (640, 360), f"Fenster: Bild eingepasst ({g}, {a.photo.im.size})")

    class Ev:
        def __init__(self, x, y, **k): self.x = x; self.y = y; self.__dict__.update(k)
    fire = lambda seq, e: [fn(e) for fn in a.video.binds.get(seq, [])]
    # drag a box over the right half (green) -> zoom, the head turns there (the window = the administrator at the device)
    fire("<ButtonPress-1>", Ev(400, 120)); fire("<B1-Motion>", Ev(480, 200)); fire("<B1-Motion>", Ev(560, 260))
    ok(L["sel"] is not None, "Fenster: Rahmen wird gezeigt, während die Maus zieht")
    a._update_video()
    fire("<ButtonRelease-1>", Ev(560, 260))
    v = L["v"]
    ok(v[2] < 0.45 and calls["aim"] and calls["aim"][-1][1] == "window" and CFG["pan"] > 50.0,
       f"Fenster: Rahmen = Zoom ×{1 / v[2]:.1f}, Kopf dreht über lupe_aim (wer: Fenster), Schwenk {CFG['pan']:.1f} %")
    # the sharp part: same function (lupe_crop) and the same bucket (lupe_rate) as /api/lupe/crop.jpg
    L["next"] = 0.0
    a._update_video()
    for _i in range(50):
        if L["hi"] is not None:
            break
        time.sleep(0.05)
    ok(calls["crop"] and calls["crop"][-1][0] == "head" and calls["rate"][-1] == "tk|window" and calls["crop"][-1][2] is not None
       and calls["crop"][-1][4] is True,
       f"Fenster: Scharfbild über lupe_crop (Kopf, mit Richtung) und den Eimer «tk|window» ({calls['crop'][-1] if calls['crop'] else '-'})")
    a._update_video()
    im = np.array(a.photo.im)
    ok(im[180, 320].tolist() == [0, 0, 255], f"Fenster: das Scharfbild liegt über dem Bereich (Mitte {im[180, 320].tolist()})")
    ok("scharf: voller Kamera-Sensor" in st.cget("text"), f"Fenster: Anzeige «{st.cget('text')[:50]}»")
    # «Sharp» off: only the live picture
    L["sharp"] = False; a._update_video()
    ok(np.array(a.photo.im)[180, 320].tolist() != [0, 0, 255] and "Live-Bild, vergrössert" in st.cget("text"), "Fenster: «◐ Scharf» aus = nur das Live-Bild")
    L["sharp"] = True
    # wheel, drag = move, rate limit
    s0 = L["v"][2]
    fire("<Button-4>", Ev(320, 200, num=4)); ok(L["v"][2] < s0, "Fenster: Mausrad (Linux Button-4) zoomt hinein")
    fire("<MouseWheel>", Ev(320, 200, delta=-120)); ok(abs(L["v"][2] - s0) < 1e-9, "Fenster: Mausrad zurück")
    x0 = ns["lupe_tk_view"](L)[0][0]
    fire("<ButtonPress-1>", Ev(300, 200)); fire("<B1-Motion>", Ev(400, 200)); fire("<ButtonRelease-1>", Ev(400, 200))
    ok(ns["lupe_tk_view"](L)[0][0] < x0, "Fenster: Ziehen verschiebt (vergrössert)")
    ns["LUPE_RL"]["tk|window"] = (0.0, time.time())
    n = len(calls["crop"]); L["next"] = 0.0; L["busy"] = True; ns["lupe_tk_fetch"](L)
    ok(len(calls["crop"]) == n, "Fenster: Eimer leer = kein Ausschnitt (dieselbe Grenze wie im Web)")
    # head conflict: emergency stop -> no turning, the reason
    CFG["servo_estop"] = True
    ns["lupe_tk_box_done"](L, [0.1, 0.1, 0.2, 0.2], "de")
    ok("Not-Aus" in L["msg"], f"Fenster: Not-Aus – der Kopf folgt nicht ({L['msg']})")
    CFG["servo_estop"] = False
    # protection on: «◐ Scharf» in the window = one sharp still on request (the server keeps the 10 s), not a switch off
    L["hi"] = None; L["busy"] = False; L["next"] = 0.0; L["want"] = False; ns["LUPE_RL"].pop("tk|window", None)
    a._update_video(); time.sleep(0.4)
    ok(calls["crop"][-1][4] is False, "Fenster: laufendes Nachladen fragt kein Standbild an (want = nein)")
    CFG["armed"] = True
    bs = [w for w in tkm.Button.__mro__[1].made if isinstance(w, tkm.Button) and w.master is bar and "Scharf" in str(w.cget("text"))][0]
    bs.cget("command")()
    ok(L["sharp"] and L["want"], "Fenster, Schutz an: «◐ Scharf» = ein Scharfbild auf Wunsch (bleibt an)")
    L["busy"] = False; ns["lupe_tk_fetch"](L)
    ok(calls["crop"][-1][4] is True and not L["want"], "Fenster: der Wunsch geht einmal an lupe_crop (want = ja), dann nicht mehr")
    CFG["armed"] = False
    L["follow"] = False; n = len(calls["aim"])
    ns["lupe_tk_box_done"](L, [0.1, 0.1, 0.2, 0.2], "de")
    ok(len(calls["aim"]) == n, "Fenster: «🎯 Kopf folgt» aus = nur zoomen")
    # double click: 1:1, again: closed; afterwards double click = full screen as before
    fire("<Double-Button-1>", Ev(320, 200)); ok(L["on"] and L["v"][2] == 1.0, "Fenster: Doppelklick = ganzes Bild")
    fire("<Double-Button-1>", Ev(320, 200)); ok(not L["on"] and bar.dead and a.b_lupe.placed, "Fenster: nochmals Doppelklick = Lupe zu, Knopf wieder da")
    fire("<Double-Button-1>", Ev(320, 200)); ok(calls.get("fs"), "Fenster: danach Doppelklick = Vollbild wie bisher")
    a._lupe_open(); [fn(None) for fn in a.root.binds["<Escape>"]]
    ok(not L["on"], "Fenster: Esc schliesst die Lupe")
    a._lupe_open(); a._update_video(); a._build_left(tkm.Frame())
    ok(not L["on"], "Fenster: Live-Bereich neu gebaut (Reiter, Ansicht) = ohne Lupe, kein altes Fenster-Element")
    shutil.rmtree(home, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser(description="Test «🔍 Lupe» (639zzzl)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "lupe_bilder"))
    a = ap.parse_args()
    datei = a.datei or neueste()
    t0 = time.time()
    teil_a(datei)
    teil_b(datei, a.browser, a.bilder)
    teil_d(datei)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
