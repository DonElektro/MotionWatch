#!/usr/bin/env python3
"""Test «Simulator aus – die echte Kamera kommt zurück» (Teile 340 sim_set, 440 Zusatzkameras, 210 open_source).

Fehler des Besitzers (MoveEye 3.92.0, echter Pi 5): nach Simulator ein / aus stand unter Einstellungen → Kameras die
Hauptkamera (Pi camera 0) rot «fehlgeschlagen Camera __init__ sequence did not complete», daneben ein NEUER Eintrag
«Pi camera 0» grün mit Bild. Die beiden stritten um denselben Sensor, der neue gewann.

Der Test startet MoveEye ohne Fenster in einem Temp-Ordner mit
  * einem falschen picamera2 (PYTHONPATH): ein Sensor (Nummer 0), pro Nummer nur EIN offenes Picamera2 – das zweite wirft
    wie libcamera «Camera __init__ sequence did not complete.»; der Zustand (wer hält den Sensor) steht in einer Datei,
  * einem falschen Simulator (HTTP, /info, /state, /cam/<n>/video.mjpg, /thermal.bin),
  * einer Netzwerk-Kamera, die nie antwortet (wie Karte 3 beim Besitzer),
und prüft in mehreren Läufen (Hauptkamera «pi:0» und «auto»):
  1. vor dem Simulator: Hauptkamera Pi camera 0 verbunden, Zusatzkameras = genau die Netzwerk-Kamera;
  2. Simulator ein, dabei «Pi camera 0» als Zusatzkamera hinzufügen (die Auswahl bietet sie im Simulator an) –
     MoveEye lehnt das ab (der Sensor gehört der Hauptkamera);
  3. Simulator aus: dieselbe Liste wie vorher (gleiche Reihenfolge, gleiche Hauptkamera), keine Simulator-Kamera mehr,
     die Hauptkamera verbunden, der Sensor genau einmal offen (vom Hauptprogramm), keine Zusatzkamera auf dem Pi-Sensor;
  4. Selbstheilung beim Start (Zustand nach 3.92.0): «pi:0» als Hauptkamera UND als Zusatzkamera – ohne eigene
     Einstellungen ist die Doppelung nach dem Start weg, mit eigener Rolle (Übersicht, kopf_ov) nur ausgeschaltet (Karte
     «aus: …», Rolle bleibt); genau eine Zeile im Protokoll, die Hauptkamera verbunden, der Sensor einmal offen.
Auf 3.92.0 schlägt der Test fehl: Lauf 2 («auto») verliert schon beim Start die offene Kamera (zweiter Öffnungs-Versuch
ersetzt das Ergebnis), Lauf 1 nimmt «Pi camera 0» im Simulator als Zusatzkamera an, die Selbstheilung fehlt.

  python3 werkzeuge/sim_kamera_zurueck_test.py [--datei X.py] [--nur lauf1,heil1]
"""
import argparse
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "SimKam-" + os.urandom(4).hex()
NETZ_ID = "c0ffee77"

# ---- falsches picamera2: ein Sensor, nur ein Öffnen pro Nummer (wie libcamera) -----------------------------------------
FAKE_PICAM = r'''
import json, os, threading, time
import numpy as np
_STATE = os.environ["MW_FAKE_PICAM_STATE"]
_LOCK = threading.Lock()
_HELD = {}
_LOG = []


def _write():
    try:
        with open(_STATE + ".tmp", "w") as f:
            json.dump({"held": {str(k): v for k, v in _HELD.items()}, "log": _LOG[-60:]}, f)
        os.replace(_STATE + ".tmp", _STATE)
    except OSError:
        pass


class Picamera2:
    @staticmethod
    def global_camera_info():
        return [{"Num": 0, "Id": "/base/axi/pcie@120000/rp1/i2c@88000/imx708@1a", "Model": "imx708_noir", "Location": 2}]

    def __init__(self, camera_num=0):
        import traceback
        who = ">".join(f.name for f in traceback.extract_stack()[-7:-1])
        with _LOCK:
            if camera_num not in (0,):
                raise IndexError("list index out of range")
            if camera_num in _HELD:
                _LOG.append(["refused", camera_num, time.time()]); _write()
                raise RuntimeError("Camera __init__ sequence did not complete.")
            _HELD[camera_num] = who
            _LOG.append(["open", camera_num, time.time()]); _write()
        self.num = camera_num; self.closed = False; self.n = 0

    def create_video_configuration(self, main=None, **kw):
        return {"main": main or {"size": (1280, 720)}}

    def create_still_configuration(self, main=None, **kw):
        return {"main": main or {"size": (4608, 2592)}}

    def configure(self, cfg):
        self.size = tuple((cfg.get("main") or {}).get("size") or (1280, 720))

    def start(self):
        pass

    def set_controls(self, c):
        pass

    def capture_array(self, name="main"):
        if self.closed:
            raise RuntimeError("camera closed")
        time.sleep(1 / 30.0)
        self.n += 1
        w, h = getattr(self, "size", (1280, 720))
        a = np.full((h, w, 3), 90, np.uint8)
        a[:, (self.n * 7) % w:(self.n * 7) % w + 4] = 200
        return a

    def stop(self):
        pass

    def close(self):
        with _LOCK:
            if not self.closed and _HELD.get(self.num) is not None:
                _HELD.pop(self.num, None)
                _LOG.append(["close", self.num, time.time()]); _write()
            self.closed = True
'''


# ---- falscher Simulator ---------------------------------------------------------------------------------------------------
def _jpeg():
    try:
        import cv2
        import numpy as np
        a = np.full((360, 640, 3), 60, np.uint8)
        cv2.putText(a, "SIM", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 4)
        return cv2.imencode(".jpg", a)[1].tobytes()
    except Exception:
        return b""


JPG = None


class Sim(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, d):
        b = json.dumps(d).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/cam/") and "video.mjpg" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame"); self.end_headers()
            try:
                while True:
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(JPG)).encode() + b"\r\n\r\n" + JPG + b"\r\n")
                    time.sleep(0.15)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return
        if self.path.startswith("/thermal.bin"):
            import struct
            b = struct.pack("<%df" % (80 * 62), *([20.0] * (80 * 62)))
            self.send_response(200); self.send_header("X-Width", "80"); self.send_header("X-Height", "62")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if self.path.startswith("/info"):
            return self._json({"name": "Testsim", "version": "3D-5.69.0", "ver": "3.69.0",
                               "cameras": [{"id": "0"}, {"id": "1", "mount": "scene"}]})
        return self._json({})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        return self._json({"ok": True})


def frei_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Lauf:
    def __init__(self, datei, name, st, pruef, tmp_root):
        self.name, self.pruef = name, pruef
        self.tmp = tempfile.mkdtemp(prefix="mw_simkam_" + name + "_", dir=tmp_root)
        self.cfg = os.path.join(self.tmp, "mw"); os.makedirs(self.cfg)
        fake = os.path.join(self.tmp, "fake"); os.makedirs(fake)
        with open(os.path.join(fake, "picamera2.py"), "w") as f:
            f.write(FAKE_PICAM)
        self.state = os.path.join(self.tmp, "picam.json")
        with open(os.path.join(self.cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        self.port = frei_port()
        self.logf = open(os.path.join(self.tmp, "log.txt"), "w")
        env = dict(os.environ, MW_FAKE_PICAM_STATE=self.state, PYTHONPATH=fake, MW_TEST_V4L="")
        self.p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(self.port), "--bind", "127.0.0.1",
                                   "--config", self.cfg, "--web-password", PASSWORT],
                                  stdout=self.logf, stderr=subprocess.STDOUT, cwd=self.tmp, env=env)
        self.base = "http://127.0.0.1:%d" % self.port
        pm = urllib.request.HTTPPasswordMgrWithDefaultRealm(); pm.add_password(None, self.base, "admin", PASSWORT)
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPBasicAuthHandler(pm))
        for _ in range(240):
            if self.p.poll() is not None:
                raise SystemExit("MoveEye hat sich beendet:\n" + self.log()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)

    def get(self, path):
        with self.op.open(self.base + path, timeout=15) as r:
            return json.loads(r.read().decode())

    def post(self, path, d):
        rq = urllib.request.Request(self.base + path, data=json.dumps(d).encode(), method="POST",
                                    headers={"Content-Type": "application/json", "Origin": self.base, "X-Requested-With": "test"})
        try:
            with self.op.open(rq, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode())
            except Exception:
                return {"ok": False, "error": "HTTP %d" % e.code}

    def cams(self):
        return self.get("/api/cams")["cams"]

    def picam(self):
        try:
            with open(self.state) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"held": {}, "log": []}

    def warte(self, fn, s=60.0):
        end = time.time() + s
        v = None
        while time.time() < end:
            try:
                v = fn()
            except Exception:
                v = None
            if v:
                return v
            time.sleep(1.0)
        return v

    def settings(self):
        with open(os.path.join(self.cfg, "motionwatch_settings.json")) as f:
            return json.load(f).get("cfg", {})

    def log(self):
        t = open(os.path.join(self.tmp, "log.txt"), errors="replace").read()
        for x in glob.glob(os.path.join(self.cfg, "**", "*.log"), recursive=True) + glob.glob(os.path.join(self.cfg, "**", "events*"), recursive=True):
            try:
                t += open(x, errors="replace").read()
            except OSError:
                pass
        return t

    def ende(self):
        self.p.terminate()
        try:
            self.p.wait(20)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.logf.close()


def grund(sim_url):
    return {"source": "pi:0", "extra_cams": ["url:" + NETZ_ID], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
            "ip_sources": [{"id": NETZ_ID, "name": "Einfahrt", "url": "rtsp://192.0.2.7:554/stream1"}],
            "sim_on": False, "sim_url": sim_url, "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
            "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False}


def main_ok(L, spec="pi:0"):
    c = L.cams()
    return c and c[0]["status"] == "connected" and c[0]["id"] == spec and c


def pi_auf_zusatz(cams):
    """Zusatzkameras (n > 0), die den Pi-Sensor halten (Bild «Pi camera …» oder Quelle pi:/usb: verbunden)"""
    return [c for c in cams[1:] if not c.get("off") and str(c["id"]).startswith("pi:") or (str(c.get("label", "")).startswith("Pi camera") and c["status"] == "connected")]


def lauf_sim(datei, pruef, tmp_root, sim_url, main_spec, name):
    st = grund(sim_url); st["source"] = main_spec
    L = Lauf(datei, name, st, pruef, tmp_root)
    try:
        c0 = L.warte(lambda: main_ok(L, "pi:0"), 90)
        pruef(bool(c0), f"{name}: vor dem Simulator Hauptkamera Pi camera 0 verbunden ({(c0 or L.cams())[0]})")
        vorher = [c["id"] for c in L.cams()]
        pruef(vorher == ["pi:0", "url:" + NETZ_ID], f"{name}: Liste vorher {vorher}")
        r = L.post("/api/sim", {"on": True, "confirm": True})
        pruef(r.get("ok") is not False, f"{name}: Simulator ein ({r})")
        cs = L.warte(lambda: (lambda c: c and c[0]["status"] == "connected" and str(c[0]["id"]).startswith("sim:") and c)(L.cams()), 90)
        pruef(bool(cs), f"{name}: im Simulator Hauptkamera = Simulator ({(cs or L.cams())[0]})")
        time.sleep(3)
        held = L.picam()["held"]
        pruef(not held, f"{name}: im Simulator ist der Pi-Sensor zu ({held})")
        # die Auswahl bietet die echte Pi-Kamera im Simulator an – dazunehmen darf sie MoveEye nicht (sie ist die echte Hauptkamera)
        r = L.post("/api/cams", {"action": "add", "id": "pi:0", "lang": "en"})
        pruef(r.get("ok") is False, f"{name}: Pi camera 0 im Simulator nicht als Zusatzkamera ({r})")
        time.sleep(4)
        r = L.post("/api/sim", {"on": False})
        pruef(r.get("ok") is not False, f"{name}: Simulator aus ({r})")
        c1 = L.warte(lambda: main_ok(L, "pi:0"), 60)
        time.sleep(12)                                  # Zusatzkameras versuchen es alle 6 s nochmals
        c1 = L.cams()
        ids = [c["id"] for c in c1]
        pruef(c1[0]["status"] == "connected" and c1[0]["id"] == "pi:0", f"{name}: nach dem Simulator Hauptkamera wieder verbunden ({c1[0]})")
        pruef(ids == vorher, f"{name}: dieselbe Liste wie vorher {ids} (vorher {vorher})")
        pruef(not pi_auf_zusatz(c1), f"{name}: keine Zusatzkamera auf dem Pi-Sensor {pi_auf_zusatz(c1)}")
        # die Datei wird gesammelt gespeichert (save_settings: höchstens alle 15 s) - bis zu 20 s auf sie warten
        L.warte(lambda: L.settings().get("source") == main_spec and L.settings().get("extra_cams") == ["url:" + NETZ_ID], 20)
        s = L.settings()
        pruef(s.get("source") == main_spec and s.get("extra_cams") == ["url:" + NETZ_ID],
              f"{name}: Einstellungen wie vorher (source {s.get('source')}, extra_cams {s.get('extra_cams')})")
        pc = L.picam()
        pruef(list(pc["held"]) == ["0"] and ">loop>" not in str(pc["held"].get("0", "")),
              f"{name}: der Sensor ist genau einmal offen ({str(pc['held'])[:200]})")
        ref = [x for x in pc["log"] if x[0] == "refused"]
        print(f"  info  {name}: {len(ref)} abgewiesene Öffnungen")
    finally:
        L.ende()
        tb = "Traceback (most recent call last)" in L.log()
        pruef(not tb, f"{name}: kein Traceback im Protokoll")
        if tb:
            print(L.log()[-2500:])
        shutil.rmtree(L.tmp, ignore_errors=True)


def lauf_heil(datei, pruef, tmp_root, sim_url, name, doppel, eigene):
    """Zustand des Besitzers nach 3.92.0: die Pi-Kamera ist Haupt- und Zusatzkamera. eigene = die Zusatzkamera hat eigene
    Einstellungen (Blickwinkel) -> nur ausschalten, sonst entfernen."""
    st = grund(sim_url)
    st["extra_cams"] = [doppel, "url:" + NETZ_ID]
    if eigene:
        st["kopf_ov"] = doppel                           # a role of its own: the overview camera of the head
    L = Lauf(datei, name, st, pruef, tmp_root)
    try:
        c = L.warte(lambda: main_ok(L, "pi:0"), 90)
        time.sleep(10)
        c = L.cams()
        pruef(c[0]["status"] == "connected" and c[0]["id"] == "pi:0", f"{name}: Hauptkamera verbunden ({c[0]})")
        pruef(not pi_auf_zusatz(c), f"{name}: keine Zusatzkamera auf dem Pi-Sensor {pi_auf_zusatz(c)}")
        s = L.settings()
        if eigene:
            pruef(doppel in (s.get("extra_cams_off") or []) and s.get("extra_cams") == [doppel, "url:" + NETZ_ID],
                  f"{name}: mit eigenen Einstellungen nur ausgeschaltet (extra_cams {s.get('extra_cams')}, aus {s.get('extra_cams_off')})")
            pruef(s.get("kopf_ov") == doppel, f"{name}: ihre Rolle bleibt (kopf_ov {s.get('kopf_ov')})")
            c = L.cams()
            pruef(any(x["id"] == doppel and x.get("off") and x["status"].startswith("off:") for x in c[1:]),
                  f"{name}: die Karte sagt «aus» {[(x['id'], x['status']) for x in c[1:]]}")
        else:
            pruef(s.get("extra_cams") == ["url:" + NETZ_ID], f"{name}: die Doppelung ist weg (extra_cams {s.get('extra_cams')})")
        lg = L.log()
        n = len(re.findall(r"Duplicate camera", lg))
        pruef(n == 1, f"{name}: genau eine Zeile im Protokoll ({n})")
        pc = L.picam()
        pruef(list(pc["held"]) == ["0"], f"{name}: der Sensor ist genau einmal offen ({str(pc['held'])[:160]})")
    finally:
        L.ende()
        tb = "Traceback (most recent call last)" in L.log()
        pruef(not tb, f"{name}: kein Traceback im Protokoll")
        if tb:
            print(L.log()[-2500:])
        shutil.rmtree(L.tmp, ignore_errors=True)


def main():
    global JPG
    ap = argparse.ArgumentParser(description="Simulator aus: die echte Kamera kommt zurück")
    ap.add_argument("--datei", default="")
    ap.add_argument("--nur", default="", help="nur diese Läufe: lauf1,lauf2,heil1,heil2")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    print("Datei:", os.path.basename(datei), flush=True)
    JPG = _jpeg()
    sp = frei_port()
    srv = ThreadingHTTPServer(("127.0.0.1", sp), Sim); srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    sim_url = "http://127.0.0.1:%d" % sp
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    nur = {x.strip() for x in a.nur.split(",") if x.strip()}
    tmp_root = tempfile.mkdtemp(prefix="mw_simkam_")
    try:
        laeufe = [("lauf1", lambda: lauf_sim(datei, pruef, tmp_root, sim_url, "pi:0", "lauf1")),
                  ("lauf2", lambda: lauf_sim(datei, pruef, tmp_root, sim_url, "auto", "lauf2")),
                  ("heil1", lambda: lauf_heil(datei, pruef, tmp_root, sim_url, "heil1", "pi:0", False)),
                  ("heil2", lambda: lauf_heil(datei, pruef, tmp_root, sim_url, "heil2", "pi:0", True))]
        for n, fn in laeufe:
            if nur and n not in nur:
                continue
            print("==", n, flush=True)
            fn()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp_root, ignore_errors=True)
    print("Sim-Kamera-zurück-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
