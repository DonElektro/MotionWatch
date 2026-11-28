#!/usr/bin/env python3
"""Test «Wärmebild prüfen und reparieren» und robuster Start der Waveshare Thermal-90 / 44 (Teile 080, 230, 639zzzzzx).

Fehler des Besitzers (MoveEye 4.24.0, echter Pi 5, erstes echtes Modul): Live-Ansicht «Wärmebild» nur Spinner, Kopfzeile
«Wärme ⚠», kein Grund sichtbar. Der Test startet MoveEye ohne Fenster (Demo-Kamera als Kopfbild) in einem Temp-Ordner mit
einem nachgestellten Sensor auf PYTHONPATH (falsches senxor / spidev / smbus2 / gpiozero; Verhalten aus einer Datei, damit
der Test es im Lauf umschalten kann) und erfundenen Gerätedateien (MW_TEST_DEV_DIR). Der Reihe nach:
  1. Treiber fehlt        -> Status nennt «driver missing», die Prüfung zeigt pysenxor ✗;
  2. GPIO 7 belegt        -> Status nennt «dtoverlay=spi0-0cs»;
  3. I2C antwortet nicht  -> Status nennt «0x40»;
  4. kein DATA READY      -> Status nennt «DATA READY (GPIO 24)», danach sind ALLE Pins wieder frei (vor 4.24.x blieben sie
                             offen und jeder neue Versuch scheiterte mit «GPIO busy»);
  5. alles gut            -> «connected», die Prüfung zeigt Modul-ID und Bildrate > 0;
  6. anderer CS-Pin (8)   -> MoveEye öffnet das Modul neu mit GPIO 8.
Bei jedem Schritt liefert /video_feed weiter Bilder (das Kopfbild hält nie an) und die Live-Ansicht bekommt den Status.
Rechte (nur Admin) prüft der Test nicht (Benutzer mit Passwort-Hash wären nötig): role-Abfrage in thermal_check_routes.

  python3 werkzeuge/waermebild_pruefen_test.py [--datei X.py]
"""
import argparse
import glob
import json
import os
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
PASSWORT = "WaermeT-" + os.urandom(4).hex()

FAKE_COMMON = r'''
import json, os, threading
_MODE = os.environ["MW_FAKE_SENXOR_MODE"]
_PINS = os.environ["MW_FAKE_SENXOR_PINS"]
_LOCK = threading.Lock()
CLAIMED = {}


def mode():
    try:
        return open(_MODE).read().strip()
    except OSError:
        return "ok"


def write_pins():
    try:
        with open(_PINS + ".tmp", "w") as f:
            json.dump(sorted(CLAIMED), f)
        os.replace(_PINS + ".tmp", _PINS)
    except OSError:
        pass
'''
FAKE_GPIOZERO = r'''
import time
from _fake_common import CLAIMED, _LOCK, mode, write_pins


class _Dev:
    def __init__(self, pin, **kw):
        p = int(str(pin).replace("BCM", "").replace("GPIO", ""))
        with _LOCK:
            if mode() == "busy" and p == 7:
                raise RuntimeError("lgpio.error: 'GPIO busy'")
            if p in CLAIMED:
                raise RuntimeError("lgpio.error: 'GPIO busy'")
            CLAIMED[p] = type(self).__name__; write_pins()
        self.pin = p; self.closed = False; self.value = 0

    def on(self):
        self.value = 1

    def off(self):
        self.value = 0

    def close(self):
        with _LOCK:
            if not self.closed:
                self.closed = True; CLAIMED.pop(self.pin, None); write_pins()


class DigitalOutputDevice(_Dev):
    pass


class OutputDevice(_Dev):
    pass


class DigitalInputDevice(_Dev):
    def wait_for_active(self, timeout=None):
        if mode() == "nodrdy":
            time.sleep(min(1.0, timeout or 1.0)); return False
        time.sleep(1 / 15.0); return True


class Servo:
    def __init__(self, *a, **k):
        raise RuntimeError("no servo in the test")
'''
FAKE_SPIDEV = r'''
class SpiDev:
    def __init__(self, bus=0, dev=0):
        self.mode = 0; self.lsbfirst = False; self.bits_per_word = 8; self.max_speed_hz = 0; self.cshigh = False

    def close(self):
        pass
'''
FAKE_SMBUS2 = r'''
from _fake_common import mode


class SMBus:
    def __init__(self, n=1):
        pass

    def read_byte(self, a):
        if a == 0x40 and mode() != "noi2c":
            return 0
        raise OSError(121, "Remote I/O error")

    def close(self):
        pass
'''
FAKE_SENXOR_INIT = r'''
from _fake_common import mode
if mode() == "nodriver":
    raise ImportError("No module named 'senxor'")
'''
FAKE_SENXOR_IF = r'''
class SPI_Interface:
    def __init__(self, device, xfer_size=160):
        self.device = device


class I2C_Interface:
    def __init__(self, bus, addr):
        self.bus = bus; self.addr = addr
'''
FAKE_SENXOR_UTILS = r'''
import numpy as np


def data_to_frame(data, shape, hflip=False):
    return np.asarray(data).reshape(shape[1], shape[0])
'''
FAKE_SENXOR_MI48 = r'''
import numpy as np
from _fake_common import mode


class MI48:
    def __init__(self, ifaces, data_ready=None, reset_handler=None):
        if reset_handler:
            reset_handler()
        if mode() == "noi2c":
            raise OSError(121, "Remote I/O error")
        self.fw_version = (2, 1); self.fpa_shape = (80, 62); self.camera_id_hexsn = "TEST-SN-0001"; self.n = 0

    def set_fps(self, f):
        pass

    def enable_filter(self, **k):
        pass

    def set_offset_corr(self, v):
        pass

    def start(self, **k):
        pass

    def stop(self):
        pass

    def read(self):
        self.n += 1
        d = np.full(80 * 62, 2931, np.uint16)                   # 20 °C in deci-Kelvin
        d[62 * 40 + 20 + (self.n % 30)] = 3081                   # a warm spot that moves (35 °C)
        return d, None
'''


def frei_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class MW:
    def __init__(self, datei, tmp):
        self.tmp = tmp
        self.cfg = os.path.join(tmp, "mw"); os.makedirs(self.cfg)
        fake = os.path.join(tmp, "fake"); os.makedirs(os.path.join(fake, "senxor"))
        for n, t in (("_fake_common.py", FAKE_COMMON), ("gpiozero.py", FAKE_GPIOZERO), ("spidev.py", FAKE_SPIDEV),
                     ("smbus2.py", FAKE_SMBUS2), ("senxor/__init__.py", FAKE_SENXOR_INIT), ("senxor/interfaces.py", FAKE_SENXOR_IF),
                     ("senxor/utils.py", FAKE_SENXOR_UTILS), ("senxor/mi48.py", FAKE_SENXOR_MI48)):
            with open(os.path.join(fake, n), "w") as f:
                f.write(t)
        dev = os.path.join(tmp, "dev"); os.makedirs(dev)
        for n in ("spidev0.0", "i2c-1"):
            open(os.path.join(dev, n), "w").close()
        self.modef = os.path.join(tmp, "mode.txt"); self.pinsf = os.path.join(tmp, "pins.json")
        self.mode("nodriver")
        st = {"source": "demo", "extra_cams": [], "kopf_ov": "", "thermal_source": "senxor:0", "thermal_on": True,
              "thermal_alpha": 0.5, "thermal_hot": True, "thermal_hot_pct": 80, "thermal_zoom": 65, "thermal_dx": 0,
              "sim_on": False, "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False,
              "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False}
        with open(os.path.join(self.cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        self.port = frei_port()
        self.logf = open(os.path.join(tmp, "log.txt"), "w")
        env = dict(os.environ, PYTHONPATH=fake, MW_TEST_V4L="", MW_TEST_DEV_DIR=dev,
                   MW_FAKE_SENXOR_MODE=self.modef, MW_FAKE_SENXOR_PINS=self.pinsf)
        self.p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(self.port), "--bind", "127.0.0.1",
                                   "--config", self.cfg, "--web-password", PASSWORT],
                                  stdout=self.logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
        self.base = "http://127.0.0.1:%d" % self.port
        self.op = self._opener("admin", PASSWORT)
        for _ in range(240):
            if self.p.poll() is not None:
                raise SystemExit("MoveEye hat sich beendet:\n" + self.log()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)

    def _opener(self, user, pw):
        pm = urllib.request.HTTPPasswordMgrWithDefaultRealm(); pm.add_password(None, self.base, user, pw)
        return urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPBasicAuthHandler(pm))

    def mode(self, m):
        with open(self.modef, "w") as f:
            f.write(m)

    def pins(self):
        try:
            return json.load(open(self.pinsf))
        except (OSError, ValueError):
            return []

    def get(self, path, op=None, timeout=30):
        with (op or self.op).open(self.base + path, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def post(self, path, d):
        rq = urllib.request.Request(self.base + path, data=json.dumps(d).encode(), method="POST",
                                    headers={"Content-Type": "application/json", "Origin": self.base, "X-Requested-With": "test"})
        try:
            with self.op.open(rq, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": "HTTP %d" % e.code}

    def state(self):
        s = self.get("/api/state")
        return s.get("state", s)

    def frames(self):
        """how many pictures /video_feed sends in about 3 s (the head picture with the thermal overlay)"""
        r = self.op.open(self.base + "/video_feed", timeout=15)
        n, end, buf = 0, time.time() + 3.0, b""
        try:
            while time.time() < end:
                c = r.read1(65536) if hasattr(r, "read1") else r.read(4096)
                if not c:
                    break
                buf += c; n += buf.count(b"--frame"); buf = buf[-16:]
        finally:
            r.close()
        return n

    def warte(self, fn, s=60.0):
        end = time.time() + s; v = None
        while time.time() < end:
            try:
                v = fn()
            except Exception:
                v = None
            if v:
                return v
            time.sleep(1.0)
        return v

    def log(self):
        t = open(os.path.join(self.tmp, "log.txt"), errors="replace").read()
        for x in glob.glob(os.path.join(self.cfg, "**", "*.log"), recursive=True):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in os.path.basename(p)[16:-3].split("_")])[-1]
    tmp = tempfile.mkdtemp(prefix="mw_waerme_")
    fehler = []

    def pruef(ok, text):
        print(("OK    " if ok else "FEHLER") + "  " + text, flush=True)
        if not ok:
            fehler.append(text)
    M = None
    try:
        M = MW(datei, tmp)

        def th_has(*words):
            def f():
                s = str(M.state().get("thermal") or "")
                return s if all(w.lower() in s.lower() for w in words) else None
            return f

        def step_of(res, sid):
            return next((x for x in res.get("steps", []) if x["id"] == sid), {})
        s1 = M.warte(th_has("driver missing"), 60)
        pruef(bool(s1), f"1 Treiber fehlt: Status nennt es ({s1 or M.state().get('thermal')})")
        pruef(M.frames() >= 2, "1 Kopfbild läuft weiter (/video_feed)")
        r = M.get("/api/thermal_check?lang=de", timeout=90)
        pruef(r.get("ok") and step_of(r, "senxor").get("ok") is False, f"1 Prüfung: pysenxor ✗ ({step_of(r, 'senxor')})")
        pruef(step_of(r, "spidev").get("ok") is True and step_of(r, "head").get("ok") is True,
              f"1 Prüfung: SPI-Gerät ✓, Kopfkamera ✓ ({step_of(r, 'spidev')} / {step_of(r, 'head')})")
        pruef("MoveEye" in r.get("report", "") and PASSWORT not in r.get("report", "") and PASSWORT not in json.dumps(r),
              "1 Bericht ohne Passwort")
        M.mode("busy")
        s2 = M.warte(th_has("spi0-0cs"), 60)
        pruef(bool(s2), f"2 GPIO 7 belegt: Status nennt dtoverlay=spi0-0cs ({s2 or M.state().get('thermal')})")
        M.mode("noi2c")
        s3 = M.warte(th_has("0x40"), 60)
        pruef(bool(s3), f"3 I2C antwortet nicht: Status nennt 0x40 ({s3 or M.state().get('thermal')})")
        pruef(M.frames() >= 2, "3 Kopfbild läuft weiter (/video_feed)")
        M.mode("nodrdy")
        s4 = M.warte(th_has("data ready", "gpio 24"), 60)
        pruef(bool(s4), f"4 kein DATA READY: Status nennt GPIO 24 ({s4 or M.state().get('thermal')})")
        time.sleep(1.0)
        pruef(M.pins() == [], f"4 nach dem Fehler sind alle Pins wieder frei ({M.pins()})")
        M.mode("ok")
        s5 = M.warte(lambda: M.state().get("thermal") == "connected", 60)
        pruef(bool(s5), f"5 alles gut: verbunden ({M.state().get('thermal')})")
        pruef(sorted(M.pins()) == [7, 23, 24], f"5 Pins 7 / 23 / 24 belegt ({M.pins()})")
        pruef(M.frames() >= 2, "5 Kopfbild mit Wärmebild läuft (/video_feed)")
        r = M.get("/api/thermal_check?lang=de", timeout=90)
        fr = step_of(r, "frame"); mo = step_of(r, "module")
        pruef(fr.get("ok") is True and "Bilder/s" in fr.get("detail", ""), f"5 Prüfung: Wärmebild ✓ mit Bildrate ({fr})")
        pruef(mo.get("ok") is True and "TEST-SN-0001" in mo.get("detail", ""), f"5 Prüfung: Modul-ID ({mo})")
        pruef(step_of(r, "senxor").get("ok") is True, "5 Prüfung: pysenxor ✓")
        rs = M.post("/api/set", {"key": "senxor_cs", "value": "8"})
        pruef(rs.get("ok") is not False, f"6 CS auf GPIO 8 gestellt ({rs})")
        s6 = M.warte(lambda: 8 in M.pins() and 7 not in M.pins() and M.state().get("thermal") == "connected", 60)
        pruef(bool(s6), f"6 neu geöffnet mit GPIO 8 ({M.pins()}, {M.state().get('thermal')})")
        lg = M.log()
        pruef("Camera loop error" not in lg, "keine Fehler der Kamera-Schleife im Protokoll")
    finally:
        if M is not None:
            M.ende()
            if fehler:
                print("---- Protokoll (Ende) ----\n" + M.log()[-4000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("ERGEBNIS:", "OK" if not fehler else f"{len(fehler)} Fehler")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
