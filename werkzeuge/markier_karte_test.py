#!/usr/bin/env python3
"""Test «📍 Markier-Karte» (MoveEye Teil 639zzzzm) – ohne echte Kamera:

  A) im eigenen Prozess: Selbsttest mk_selftest (nur eigene Marker-Nummern, nur bei Schutz Aus, Folgen, Punkt merken nach
     1,2 s umdrehen, kein Punkt bei 0,4 s Abdecken, Umbenennen nimmt den Abstand mit, verloren / Ende, Rechte, Seiten-Haken).
     Danach dasselbe mit einem OpenCV OHNE cv2.aruco (pip opencv-python-headless < 4.7, wie im CI): die Funktion schaltet sich
     sauber ab (Pause «OpenCV without ArUco», Karten-Bild ohne Marker, keine Ausnahme).
     --py46 PYTHON: Teil A zusätzlich mit einem anderen Python (z. B. einer venv mit opencv-contrib-python-headless 4.6.0.66 =
     Raspberry Pi OS Bookworm python3-opencv: alte API detectMarkers); ohne die Option wird eine vorhandene venv
     $MW_PY46 genommen, sonst übersprungen (Meldung).
  B) MoveEye ohne Fenster mit der Demo-Kamera; der Marker einer Karte (PNG aus der Werkstatt) liegt in der Bildmitte, solange
     die Datei MW_MK_KARTE existiert: Rechte (Familie: keine Werkstatt, keine API), aus = nichts; ein: Sitzung startet (Zustand
     «folgt»), Karte 1,3 s weg und wieder da = «Punkt 1» im Teach-in mit Abstand und in der Runde; kurz weg (0,3 s) = kein Punkt;
     Schutz ein = Sitzung zu Ende, Karte ignoriert (Zeile im Protokoll); Druckseite / SVG; Werkstatt mit Abschnitt.
     --bilder ORDNER: Werkstatt und Teach-in in Handy-Breite (390 px, Playwright).

  python3 werkzeuge/markier_karte_test.py [--datei X.py] [--py46 PYTHON] [--nur-a] [--bilder ORDNER]
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
import types
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}
PW = "Markier-" + base64.b16encode(os.urandom(5)).decode().lower()


def ok(cond, what):
    N["ok"] += 1 if cond else 0
    (FEHLER.append(what) if not cond else None)
    print(("  ✓ " if cond else "  ✗ ") + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_mk_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


def ohne_aruco(cv2mod):
    """the cv2 module without the attribute «aruco» (like pip opencv-python-headless 4.6)"""
    m = types.ModuleType("cv2_ohne_aruco")
    for k in dir(cv2mod):
        if k != "aruco":
            try:
                setattr(m, k, getattr(cv2mod, k))
            except AttributeError:
                pass
    return m


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    import cv2
    home = tempfile.mkdtemp(prefix="mw_mk_a_")
    try:
        ns = lade(datei, home)
        det = ns["mk_detector"]()
        print(f"A) im eigenen Prozess (OpenCV {cv2.__version__}, ArUco: {det.api or det.why})", flush=True)
        r = ns["mk_selftest"]()
        if det.ok:
            ok(r.startswith("ArUco"), "Selbsttest mk_selftest: " + r)
        else:
            ok("switched off cleanly" in r, "Selbsttest ohne ArUco: " + r)
        # without aruco (the CI's pip OpenCV)
        ns["cv2"] = ohne_aruco(cv2)
        ns["MK"]["det"] = None
        CFG = ns["CFG"]
        ns["save_settings"] = lambda *a, **k: None
        ns["log_event"] = lambda *a, **k: None
        CFG.update(mk_on=True, armed=False, kopf_parked=False, mk_cards=[])
        c, err = ns["mk_create"]("Ohne", "a5", "test")
        ok(c is not None and not ns["mk_detector"]().ok, "ohne cv2.aruco: Karte trotzdem erstellbar, Detektor aus")
        ok(ns["mk_pause_reason"]() == "OpenCV without ArUco" and ns["mk_tick"]() == 30.0, "ohne cv2.aruco: Pause «OpenCV without ArUco», kein Lesen")
        ok("<svg" in ns["mk_card_svg"](c), "ohne cv2.aruco: Karten-Bild (SVG) ohne Ausnahme")
        st = ns["mk_state"]("de")
        ok(st["aruco"] is False and st["pause_t"] == "OpenCV ohne ArUco", "Zustand für die Werkstatt: " + st["pause_t"])
        ok(ns["mk_selftest"]().startswith("no ArUco"), "Selbsttest ohne ArUco: sauber abgeschaltet")
        ns["cv2"] = cv2
        ns["MK"]["det"] = None
    finally:
        shutil.rmtree(home, ignore_errors=True)


WRAP = r'''
import json, os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
_mk_read = DemoSource.read
_MKT = {"m": None, "img": None}
def _mk_read_card(self):                 # the test holds a marker card in the middle of the demo picture while the file exists
    ok_, img_ = _mk_read(self)
    p_ = os.environ.get("MW_MK_KARTE", "")
    if ok_ and p_ and os.path.exists(p_):
        try:
            m_ = os.path.getmtime(p_)
            if _MKT["m"] != m_:
                _MKT["img"] = cv2.imread(p_, cv2.IMREAD_COLOR); _MKT["m"] = m_
            c_ = _MKT["img"]
            if c_ is not None:
                h_, w_ = c_.shape[:2]; H_, W_ = img_.shape[:2]; x_, y_ = (W_ - w_) // 2, (H_ - h_) // 2
                img_ = img_.copy(); img_[y_:y_ + h_, x_:x_ + w_] = c_
        except Exception:
            pass
    return ok_, img_
DemoSource.read = _mk_read_card
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
'''


def teil_b(datei, bilder):
    print("B) MoveEye mit Demo-Kamera und einer Markier-Karte im Bild", flush=True)
    import cv2
    import numpy as np
    if not hasattr(cv2, "aruco"):
        print("  (übersprungen: dieses OpenCV hat kein cv2.aruco - Teil A prüft das Abschalten)", flush=True)
        return
    tmp = tempfile.mkdtemp(prefix="mw_mk_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    karte = os.path.join(tmp, "karte.png")
    st = {"source": "demo", "thermal_source": "", "thermal_on": False, "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "news_popup": False, "tours_auto": False, "armed": False, "kopf_park": False,
          "track_person": True, "patrol": False, "detection_on": False, "record_dir": os.path.join(tmp, "rec")}
    json.dump({"cfg": st, "waypoints": [[30.0, 45.0, "Zelt"]]}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=dict(os.environ, MW_MK_KARTE=karte))
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

    def state():
        return req("/api/mk?lang=de")[1]

    def warten(f, limit=30.0):
        t0 = time.time()
        while time.time() - t0 < limit:
            s = state()
            if f(s):
                return s
            time.sleep(0.25)
        return state()

    def zeigen(mid, px=150):
        a_ = cv2.aruco
        d_ = a_.getPredefinedDictionary(a_.DICT_4X4_50)
        m = (a_.generateImageMarker if hasattr(a_, "generateImageMarker") else a_.drawMarker)(d_, int(mid), 600)
        m = cv2.copyMakeBorder(m, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)          # the white paper around the marker
        m = cv2.cvtColor(cv2.resize(m, (px, px), interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2BGR)
        cv2.imwrite(karte + ".tmp.png", m); os.replace(karte + ".tmp.png", karte)

    def weg():
        try:
            os.remove(karte)
        except OSError:
            pass

    def punkte():
        return req("/api/servo")[1].get("points", [])

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        Fa = ("Anna", "anna-pass-1")
        ok(req("/api/mk", user=Fa)[0] == 403 and req("/api/mk", {"action": "create", "name": "x"}, user=Fa)[0] in (401, 403),
           "Familie: keine Markier-Karten (403)")
        code, page = req("/karten")
        ok(code == 200 and b"639zzzzm" in page and "Markier-Karten".encode() in page, "Werkstatt mit Abschnitt «📍 Markier-Karten» (Skript)")
        c, j = req("/api/mk", {"action": "create", "name": "Zeltplatz", "size": "a4"})
        card = j.get("card") or {}
        ok(c == 200 and card.get("mid") == 40, f"Karte erstellt: Marker {card.get('mid')}")
        c1, pg = req(f"/karten/markier?id={card.get('id')}&size=a5")
        c3, svg = req(f"/karten/markier?id={card.get('id')}&svg=1")
        ok(c1 == 200 and b"<svg" in pg and b"A5" in pg and c3 == 200 and svg[:4] == b"<svg" and req("/karten/markier?id=XXXXX")[0] == 404,
           "Druckseite (A5), SVG, unbekannte Karte 404")
        ok(req(f"/karten/markier?id={card.get('id')}", user=Fa)[0] in (401, 403), "Familie: keine Druckseite")
        mid = card.get("mid", 40)
        zeigen(mid)
        time.sleep(3)
        ok(state()["state"]["ses"] is None, "aus: die Karte im Bild startet nichts")
        ok(req("/api/set", {"key": "mk_on", "value": True})[0] == 200, "Markier-Karten einschalten")
        s = warten(lambda s: s["state"]["ses"] is not None)
        ok(s["state"]["ses"] is not None and s["state"]["ses"]["state"] == "follow", "Karte erkannt: Sitzung «folgt» "
           f"({s['state'].get('api')}, {s['state'].get('ms')} ms)")
        time.sleep(2.5)
        n0 = len(punkte())
        weg(); time.sleep(1.3); zeigen(mid)
        s = warten(lambda s: s["state"]["ses"] and s["state"]["ses"]["marks"] >= 1, 15)
        pts = punkte()
        neu = [x for x in pts if x.get("mk_m")]
        ok(len(pts) == n0 + 1 and neu and neu[-1]["name"] == "Punkt 1" and neu[-1]["patrol"], "1,3 s umgedreht: «Punkt 1» im Teach-in, in der Runde "
           + json.dumps(neu[-1:] , ensure_ascii=False))
        ok(bool(neu) and 0.3 < float(neu[-1]["mk_m"]) < 30.0, f"Abstand geschätzt: ~{neu[-1]['mk_m'] if neu else '?'} m")
        time.sleep(3.5)
        weg(); time.sleep(0.25); zeigen(mid); time.sleep(3)
        ok(len(punkte()) == n0 + 1, "0,25 s weg (jemand geht durchs Bild): kein Punkt")
        req("/api/arm", {"action": "arm_now"})
        s = warten(lambda s: s["state"]["ses"] is None, 10)
        ok(s["state"]["ses"] is None and s["state"]["armed"], "Schutz ein: Sitzung zu Ende, Karte ignoriert")
        time.sleep(2.5)
        lines = json.dumps(req("/api/log?limit=500&q=Markier")[1], ensure_ascii=False)
        ok("Schutz Aus" in lines or "protection is off" in lines, "Protokoll: «Markier-Karte … nur bei Schutz Aus»")
        req("/api/arm", {"action": "disarm"})
        if bilder:
            os.makedirs(bilder, exist_ok=True)
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as pw_:
                    b = pw_.chromium.launch()
                    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, http_credentials={"username": "admin", "password": PW},
                                        color_scheme="dark")
                    errs = []
                    for path, name in (("/karten", "werkstatt"), ("/servo", "teachin"), (f"/karten/markier?id={card.get('id')}", "druck")):
                        pg_ = ctx.new_page(); pg_.on("pageerror", lambda e: errs.append(str(e)))
                        pg_.goto(base + path); pg_.wait_for_timeout(2500)
                        w = pg_.evaluate("document.documentElement.scrollWidth")
                        pg_.screenshot(path=os.path.join(bilder, f"markier_{name}.png"), full_page=True)
                        ok(w <= 391, f"{path}: Breite {w} px (390)")
                    ok(not errs, "keine JavaScript-Fehler " + "; ".join(errs)[:200])
                    b.close()
            except ImportError:
                print("  (Bilder übersprungen: kein Playwright)")
    finally:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
        if FEHLER:
            print(open(os.path.join(tmp, "log.txt"), errors="replace").read()[-2500:])
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--py46", default=os.environ.get("MW_PY46", ""))
    ap.add_argument("--nur-a", action="store_true")
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste())
    teil_a(datei)
    if a.py46:
        print("A) noch einmal mit " + a.py46, flush=True)
        r = subprocess.run([a.py46, os.path.abspath(__file__), "--datei", datei, "--nur-a"], capture_output=True, text=True, timeout=600)
        print(r.stdout[-3000:] + r.stderr[-1500:])
        ok(r.returncode == 0 and "detectMarkers" in r.stdout, "Teil A mit OpenCV 4.6 contrib (alte API detectMarkers)")
    elif not a.nur_a:
        print("  (OpenCV 4.6 contrib übersprungen: --py46 / MW_PY46 fehlt)")
    if not a.nur_a:
        teil_b(datei, a.bilder)
    print(f"\n{N['ok']} ok, {len(FEHLER)} Fehler", flush=True)
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
