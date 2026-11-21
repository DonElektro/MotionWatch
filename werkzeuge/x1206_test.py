#!/usr/bin/env python3
"""Test Geekworm X1206 (MoveEye Teil 100 «x12», 639zi, 163a, 080, 639zzzzu) – mit einem erfundenen I2C-Bus, nie mit echter Hardware.

  Der Bus kennt drei erfundene Chips: UPS HAT (E) auf 0x2D, Geekworm X1206 (MAX17043) auf 0x36, INA219 eines alten UPS HAT auf 0x42.
  os.open / os.read / os.write / os.close und fcntl.ioctl der geladenen Datei gehen für «/dev/i2c-1» an diesen Bus; GPIO 6 (PLD)
  und 16 (Laden) liefert ein Ersatz für pinctrl. Geprüft wird:
    1. Erkennung: automatisch 0x2D -> 0x36 -> 0x42; fest gewähltes Modell; ein unplausibler Chip auf 0x36 zählt nicht.
    2. Werte: % und Zellenspannung, «lädt» / «voll» / «Akkubetrieb», Restzeit aus 4 × mAh einer Zelle.
    3. UPS HAT (E) und INA219 geben genau dieselben Werte wie vorher.
    4. Stromausfall / Strom zurück (Push), Schutz-Alarm «power» (scharf), sauberes Abschalten bei leerem Akku.
    5. GPIO 6 / 16 mit dem X1206 nie geschaltet: Lade-LED (echter Faden mit erfundenem gpiozero), Tasten, Relais; Warnung im Protokoll.
    6. Einstellungen: neue Geräte GPIO 13 / 12, Einstellungen älterer Versionen behalten 6 / 16; Texte in 5 Sprachen; Anzeige.
    7. 639zzzzz Laden steuern über GPIO 16 (erfundenes pinctrl): Kälte mit Hysterese, Notfall unter 10 %, «Trotzdem laden» 1 h,
       ohne BME280 keine Sperre, «Akku schonen» 80 / 75 %, Pegel einstellbar.
    8. Lernen mit erfundener Uhr: Restzeit aus dem Abfall, «voll in …», Zyklen, Kapazität aus einer langen Entladung.
    9. Schlafen (RTC in eine Datei, Selbsttest), Licht in Prozent am PCA9685, Selbsttests der neuen Teile.

  python3 werkzeuge/x1206_test.py [--datei webcam_bewegung_X_Y_Z.py]
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []

LAUF = r'''
import json, os, sys, time, types, threading, fcntl as _rfcntl
from collections import deque
ns = {"__name__": "mw_x1206_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
R = {}
LOG = []
_log0 = ns["log_event"]
def _log(kind, text, *a, **k):
    LOG.append(str(text))
    return _log0(kind, text, *a, **k)
ns["log_event"] = _log

# ---- the made-up I2C bus ----
BUS = {"dev": {}, "fd": {}}
def be(v): return bytes([(v >> 8) & 255, v & 255])
def le(*vals): return b"".join(bytes([v & 255, (v >> 8) & 255]) for v in vals)
def chip_x12(v=3.95, soc=80.0):
    return {0x02: be(int(v / 0.00125) << 4), 0x04: be(int(soc * 256))}
def chip_e(v=15.6, pct=77, st=0x20 | 0x80):
    return {0x00: bytes([0x0A]), 0x02: bytes([st]), 0x10: le(5100, 2000, 0), 0x20: le(int(v * 1000), 500, pct, 3800, 0xFFFF, 90),
            0x30: le(3900, 3900, 3900, 3900)}
def chip_ina(v=7.6, a=-0.4):
    sh = int(a * 0.1 / 0.00001) & 0xFFFF
    return {0x02: be(int(v / 0.004) << 3), 0x01: be(sh)}
class FakeOS:
    def __getattr__(self, k): return getattr(os, k)
    def open(self, path, flags, *a):
        if str(path).startswith("/dev/i2c-"):
            fd = 90000 + len(BUS["fd"]); BUS["fd"][fd] = {"addr": None, "reg": None}; return fd
        return os.open(path, flags, *a)
    def write(self, fd, b):
        if fd in BUS["fd"]:
            st = BUS["fd"][fd]
            if st["addr"] not in BUS["dev"]: raise OSError(121, "Remote I/O error")
            st["reg"] = b[0]; return len(b)
        return os.write(fd, b)
    def read(self, fd, n):
        if fd in BUS["fd"]:
            st = BUS["fd"][fd]
            if st["addr"] not in BUS["dev"]: raise OSError(121, "Remote I/O error")
            return BUS["dev"][st["addr"]].get(st["reg"], b"\x00" * n)[:n]
        return os.read(fd, n)
    def close(self, fd):
        if fd in BUS["fd"]:
            BUS["fd"].pop(fd); return None
        return os.close(fd)
ns["os"] = FakeOS()
ff = types.ModuleType("fcntl"); ff.__dict__.update({k: getattr(_rfcntl, k) for k in dir(_rfcntl) if not k.startswith("__")})
def _ioctl(fd, req, arg=0, *a):
    if fd in BUS["fd"]:
        BUS["fd"][fd]["addr"] = arg; return 0
    return _rfcntl.ioctl(fd, req, arg, *a)
ff.ioctl = _ioctl
sys.modules["fcntl"] = ff
GP = {6: 1, 16: 0}
ns["ups_x12_gpio"] = lambda n: GP.get(n)
ns["_pmic_watts"] = lambda: None
ns["sim_sensor"] = lambda *a, **k: None
C = ns["CFG"]; S = ns["STATE"]; X = ns["UPS_X12"]
C.update(lang="en", ups_on=True, ups_push=True, ups_mah=5000, ups_addr="0x42", ups_shutdown_pct=8, tamper_power=False, batt_warned=False)
S["cpu"] = 20.0
pushes = []
class N:
    def info(self, text, *a, **k): pushes.append(text)
class W:
    notifier = N()
ns["WATCH_REF"]["w"] = W()
def bm_new():
    bm = ns["BatteryMonitor"].__new__(ns["BatteryMonitor"]); bm.hist = deque(maxlen=60); bm.uhist = deque(maxlen=6)
    return bm
def case(devs, model="auto", ticks=1):
    BUS["dev"] = devs; C["ups_model"] = model; S.pop("battery", None); X.update(seen=False, probed=False, warned=set())
    bm = bm_new()
    for _ in range(ticks): bm.ups_tick()
    b = S.get("battery") or {}
    return {k: b.get(k) for k in ("model", "pct", "volt", "on_battery", "charging", "full", "hours", "cap_wh", "amps", "cells", "fast")}

# 1 / 2 / 3 detection and values
R["only36"] = case({0x36: chip_x12()})
R["e_and_36"] = case({0x2D: chip_e(), 0x36: chip_x12()})
R["36_and_42"] = case({0x36: chip_x12(), 0x42: chip_ina()})
R["only42"] = case({0x42: chip_ina()})
R["bad36_42"] = case({0x36: chip_x12(v=0.0, soc=200), 0x42: chip_ina()})
R["bad36"] = case({0x36: chip_x12(v=5.2)})
R["e_model_36"] = case({0x36: chip_x12()}, "e")
R["x12_model_2d"] = case({0x2D: chip_e()}, "x12")
R["ina_model_36_42"] = case({0x36: chip_x12(), 0x42: chip_ina()}, "ina")
R["only2d"] = case({0x2D: chip_e()})
GP[6] = 0
R["x12_batt"] = case({0x36: chip_x12(v=3.7, soc=50)})
GP[6] = 1; GP[16] = 1
LOG.clear()
R["x12_chg_off"] = case({0x36: chip_x12(v=3.9, soc=60)})
R["x12_chg_off_log"] = [l for l in LOG if "GPIO 16" in l]
GP[16] = 0
R["x12_full"] = case({0x36: chip_x12(v=4.19, soc=99)})
GP[6] = None
R["x12_nopld"] = case({0x36: chip_x12()})
GP[6] = 1

# 4 events
BUS["dev"] = {0x36: chip_x12(v=3.9, soc=80)}; C["ups_model"] = "auto"; X.update(seen=False, probed=False, warned=set())
bm = bm_new(); pushes.clear()
for pld in (1, 0, 1):
    GP[6] = pld; bm.ups_tick()
R["push"] = list(pushes)
alarms = []
class T:
    def alarm(self, kind, *a, **k): alarms.append(kind)
ns["TAMPER"] = T(); ns["is_armed"] = lambda: True; C["tamper_power"] = True; pushes.clear()
GP[6] = 0; bm.ups_tick()
R["tamper"] = list(alarms); R["tamper_push"] = list(pushes)
C["tamper_power"] = False; ns["is_armed"] = lambda: False
GP[6] = 1; bm.ups_tick()
acts = []
ns["power_action"] = lambda what, source="": acts.append((what, source))
ns["RUNGUARD"]["t0"] = time.time() - 1000
BUS["dev"] = {0x36: chip_x12(v=3.3, soc=5)}; GP[6] = 0; pushes.clear()
n = []
for _ in range(4):
    bm.ups_tick(); n.append(len(acts))
R["shutdown"] = {"acts": acts, "after": n, "push": list(pushes)}
GP[6] = 1

# 5 GPIO 6 / 16 never driven with an X1206
made = []
class FakeLED:
    def __init__(self, pin, frequency=100): self.pin = pin; self.value = 0; made.append(("open", pin))
    def close(self): made.append(("close", self.pin))
gz = types.ModuleType("gpiozero"); gz.PWMLED = FakeLED; sys.modules["gpiozero"] = gz
ns["charge_led_is_pi"] = lambda: True; ns["led_sim_live"] = lambda: False
C.update(charge_led_on=True, charge_led_gpio="6", btn_on=False); X.update(seen=False, probed=True, warned=set()); LOG.clear()
threading.Thread(target=ns["_charge_led_loop"], daemon=True).start()
time.sleep(0.6); R["led_e_6"] = list(made)
X["seen"] = True; time.sleep(0.6)
R["led_x12_6"] = list(made); R["led_hw"] = ns["CHARGE_LED"]["hw"]; R["led_log"] = [l for l in LOG if "X1206" in l and "GPIO 6" in l]
C["charge_led_gpio"] = "13"; time.sleep(11.0)
R["led_x12_13"] = list(made)
C["btn_gpio_protect"] = "16"; C["btn_gpio_ack"] = "26"; LOG.clear()
R["btn_x12"] = ns["led_gpio_pins"](); R["btn_log"] = [l for l in LOG if "GPIO 16" in l]
X["seen"] = False
R["btn_e"] = ns["led_gpio_pins"]()
X["seen"] = True
outs = []
class FakeOut:
    def __init__(self, gpio, active_high=True, initial_value=False): outs.append(gpio)
    def on(self): pass
    def off(self): pass
    def close(self): pass
hw = ns["Hardware"].__new__(ns["Hardware"]); hw.io = "gpiozero"; hw.outs = {}; hw._OutputDevice = FakeOut
hw._write(16, True, False); hw._write(6, True, False); hw._write(22, True, False)
R["relay_x12"] = list(outs)
X["seen"] = False; hw._write(16, True, False)
R["relay_e"] = list(outs)
C["ups_model"] = "x12"; X.update(seen=False, probed=True)
R["pins_model_x12"] = sorted(ns["ups_x12_pins"]())
C["ups_model"] = "auto"

# 6 settings and texts
D = ns["DEFAULTS"]
R["defaults"] = [D.get("charge_led_gpio"), D.get("btn_gpio_protect"), ns["CHARGE_LED_GPIO"]]
ns["apply_settings"]({"cfg": {"lang": "en"}})
R["old_file"] = [C["charge_led_gpio"], C["btn_gpio_protect"]]
ns["apply_settings"]({"cfg": {"lang": "en", "charge_led_gpio": "13", "btn_gpio_protect": "12"}})
R["new_file"] = [C["charge_led_gpio"], C["btn_gpio_protect"]]
X["seen"] = True
R["choices"] = [p[0] for p in ns["text_choice_pairs"]("charge_led_gpio")]
R["ups_choices"] = [p[0] for p in ns["text_choice_pairs"]("ups_model")]
tr = ns["tr"]
R["tr"] = {L: tr("Charge LED: GPIO", L) for L in ("de", "fr", "it", "rm", "en")}
R["help"] = ["0x36" in ns["HELP_PAGE"], ns["HELP_PAGE"].count("X1206"), json.dumps(ns.get("HELP_X", {}), ensure_ascii=False).count("X1206")]
R["web"] = 'b.model === "x12" ? "Geekworm X1206"' in ns["WEB_PAGE"]
R["i2c"] = ns["i2c_conflicts"](dict(servo_driver="pca9685", pca_address="0x41", solar_on=True, solar_addr="0x42", mover_mode="off",
                                     ups_on=True, ups_model="x12", ups_addr="0x42", thermal_on=False))

# 7 charging control (639zzzzz): made-up pinctrl and clock, BME280 values in STATE["env"]
PINS = []
_run0 = ns["_run"]
def _frun(cmd, timeout=30, inp=None):
    c = [x for x in cmd if x not in ("sudo", "-n")]
    if c[:3] == ["pinctrl", "set", "16"]:
        PINS.append(" ".join(c[3:]))
        GP[16] = 1 if c[3:] == ["op", "dh"] else 0
        return 0, "", ""
    return _run0(cmd, timeout, inp)
ns["_run"] = _frun
A = ns["AKL"]; CLK = [1.9e9]; A["now"] = lambda: CLK[0]
C.update(chg_cold_on=True, chg_cold_c=0.0, chg_cold_hyst=3.0, chg_emerg_pct=10, chg_override_h=1.0, chg_care=False, chg_off_level="high")
BUS["dev"] = {0x36: chip_x12(v=3.9, soc=60)}; GP[6] = 1; GP[16] = 0; X.update(seen=False, probed=False, warned=set())
bm = bm_new(); pushes.clear(); LOG.clear()
def tick(t=None, soc=60, pld=1, src="BME280", dt=30.0):
    CLK[0] += dt
    S["env"] = None if t is None else {"t": t, "src": src}
    BUS["dev"] = {0x36: chip_x12(v=3.9, soc=soc)}; GP[6] = pld
    bm.ups_tick()
    b = S.get("battery") or {}
    return (b.get("chg_ctl") or {}).get("why"), b.get("charging"), list(PINS)
R["c_warm"] = tick(5.0)
R["c_cold"] = tick(-1.0)
R["c_cold_log"] = [l for l in LOG if "GPIO 16" in l]
R["c_hyst"] = [tick(1.0)[0], tick(2.9)[0], tick(3.0)[0]]
R["c_pins"] = list(PINS)
tick(-2.0); ns["akl_override"](True, "test"); R["c_ov"] = tick(-2.0)[0]; R["c_ov_push"] = [p for p in pushes if "1 h" in p]
CLK[0] += 3700; R["c_ov_end"] = tick(-2.0)[0]
R["c_emerg"] = [tick(-2.0, soc=9)[0], tick(-2.0, soc=12)[0], tick(-2.0, soc=13)[0]]
R["c_emerg_push"] = [p for p in pushes if "9 %" in p]
CLK[0] += 700; R["c_nobme"] = tick(-5.0, src="DS18B20")
R["c_nobme_state"] = dict((S["battery"].get("chg_ctl") or {}))
C["chg_care"] = True; PINS.clear()
R["c_care"] = [tick(20.0, soc=80)[0], tick(20.0, soc=77)[0], tick(20.0, soc=75)[0]]
R["c_care_pins"] = list(PINS)
C["chg_care"] = False; C["chg_off_level"] = "low"; PINS.clear()
R["c_low"] = tick(-3.0)[2]
GP[16] = 0
R["c_low_read"] = S["battery"].get("charging")
tick(5.0); C["chg_off_level"] = "high"; GP[16] = 0
R["c_file"] = json.load(open(os.path.join(ns["DATA_DIR"], "akku_lernen.json")))

# 8 learning: runtime from the SOC drop, «full in», cycles, capacity from a long discharge
A.update(dis=[], chg=[], rate_dis=None, rate_t=0.0, cyc_pct=0.0, last_pct=None, cap_wh=None, cap_n=0, span=None)
bm.watts = lambda: (5.0, "pmic")
soc = 80.0
for i in range(150):                                   # 2.5 h on the battery, 16 %/h
    tick(10.0, soc=int(round(soc)), pld=0, dt=60.0); soc -= 16.0 / 60.0
b = S["battery"]
R["l_run"] = {k: b.get(k) for k in ("use_src", "use_w", "hours", "pct", "cap_wh")}
R["l_rate"] = A["rate_dis"]
R["l_night"] = ns["night_forecast"]() is not None
tick(10.0, soc=int(round(soc)), pld=1, dt=60.0)          # mains back: the span ends
R["l_cap"] = [A["cap_wh"], A["cap_n"], (S["battery"].get("health") or {}).get("health"), (S["battery"].get("health") or {}).get("cycles")]
GP[16] = 0
for i in range(40):                                    # charging 30 %/h
    tick(10.0, soc=int(round(soc)), pld=1, dt=60.0); soc += 0.5
R["l_full"] = [S["battery"].get("charging"), S["battery"].get("full_min"), S["battery"].get("pct")]
R["l_lines"] = ns["akl_lines"](S["battery"], "de")
A["now"] = None

# 9 sleep (RTC to a file), lights dimmed, the self-tests of both parts
rtc = os.path.join(ns["DATA_DIR"], "wakealarm"); ns["SLP_RTC"] = rtc
R["s_rtc"] = [ns["slp_write_alarm"](1900000123), open(rtc).read()]
try:
    R["s_self"] = ns["slp_selftest"]()
except Exception as e:
    R["s_self"] = "FEHLER %s: %s" % (type(e).__name__, e)
try:
    R["a_self"] = ns["akl_selftest"]()
except Exception as e:
    R["a_self"] = "FEHLER %s: %s" % (type(e).__name__, e)
dims = []
class FakePCA:
    def dim(self, ch, pct): dims.append((ch, round(pct, 1)))
    def switch(self, ch, on): dims.append((ch, "sw", on))
hw2 = ns["Hardware"].__new__(ns["Hardware"]); hw2.pca = FakePCA(); hw2._pca_lights = {}
C.update(light_white_out="pca:2", light_ir_out="pca:3", light_white_pct=100, light_ir_pct=40)
ns["lights_tick"] = lambda: {"white": True, "ir": True}
hw2._lights({}); hw2._lights({})
C["light_white_pct"] = 30; hw2._lights({})
R["dims"] = [d for d in dims if d[0] in (2, 3)]          # channel 4 = the wide infrared light (163), on / off
R["pca_bits"] = []
class FakeFD:
    pass
P = ns["PCA9685"].__new__(ns["PCA9685"]); P._set = lambda ch, on, off: R["pca_bits"].append((ch, on, off))
P.dim(2, 100); P.dim(2, 0); P.dim(3, 50)
try:
    R["selftest"] = ns["x1206_selftest"]()
except Exception as e:
    R["selftest"] = "FEHLER %s: %s" % (type(e).__name__, e)
print("ERG " + json.dumps(R, ensure_ascii=False, default=str))
sys.stdout.flush()
os._exit(0)
'''


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("X1206-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_x1206_")
    try:
        r = subprocess.run([sys.executable, "-c", LAUF, datei], capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, MOTIONWATCH_HOME=tmp), cwd=os.path.dirname(datei))
        R = None
        for ln in (r.stdout + r.stderr).splitlines():
            if ln.startswith("ERG "):
                R = json.loads(ln[4:])
        if R is None:
            print((r.stdout + r.stderr)[-3000:])
            ok(False, "Lauf ohne Ergebnis")
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("1  Erkennung")
    ok(R["only36"]["model"] == "x12", "nur 0x36 -> X1206 (%s)" % R["only36"])
    ok(R["e_and_36"]["model"] == "e", "0x2D und 0x36 -> UPS HAT (E) zuerst")
    ok(R["36_and_42"]["model"] == "x12", "0x36 und 0x42 -> X1206 vor dem INA219")
    ok(R["only42"]["model"] == "ina", "nur 0x42 -> INA219")
    ok(R["bad36_42"]["model"] == "ina" and R["bad36"]["model"] is None, "unplausibler Chip auf 0x36 zählt nicht")
    ok(R["e_model_36"]["model"] is None and R["x12_model_2d"]["model"] is None and R["ina_model_36_42"]["model"] == "ina",
       "fest gewähltes Modell sucht nur seinen Chip")
    print("2  Werte X1206")
    x = R["only36"]
    ok(x["pct"] == 80 and abs(x["volt"] - 3.95) < 0.01 and x["on_battery"] is False and x["charging"] is True and x["full"] is False,
       "80 %%, 3.95 V, am Netz, lädt (%s)" % x)
    y = R["x12_batt"]
    ok(y["on_battery"] is True and y["charging"] is False and y["hours"] and abs(y["cap_wh"] - 64.8) < 0.1,
       "Akkubetrieb, Restzeit aus 4 × 5000 mAh = 64,8 Wh (%s)" % y)
    ok(R["x12_chg_off"]["charging"] is False and len(R["x12_chg_off_log"]) == 1, "GPIO 16 hoch = Laden aus, einmal im Protokoll")
    ok(R["x12_full"]["full"] is True and R["x12_full"]["charging"] is False, "voll am Netz")
    ok(R["x12_nopld"]["on_battery"] is False and R["x12_nopld"]["charging"] is False, "ohne pinctrl: kein Akkubetrieb gemeldet, kein «lädt»")
    print("3  UPS HAT (E) und INA219 unverändert")
    e = R["only2d"]
    ok(e["model"] == "e" and e["pct"] == 77 and e["volt"] == 15.6 and e["charging"] is True and e["cells"] == [3.9] * 4,
       "UPS HAT (E): %s" % e)
    i = R["only42"]
    ok(i["pct"] == 60 and abs(i["volt"] - 7.6) < 0.01 and i["on_battery"] is True and i["amps"] == -0.4, "INA219: %s" % i)
    print("4  Stromausfall, Schutz-Alarm, Abschalten")
    p = R["push"]
    ok(len(p) == 2 and "Power cut" in p[0] and "80 %" in p[0] and "Power back" in p[1], "Push bei Ausfall und zurück: %s" % p)
    ok(R["tamper"] == ["power"] and not R["tamper_push"], "scharf: Alarm «power» statt Push")
    sd = R["shutdown"]
    ok(sd["after"] == [0, 0, 1, 1] and sd["acts"][0] == ["poweroff", "battery"], "nach 3 Messungen unter 8 %% sauber aus (%s)" % sd["after"])
    print("5  GPIO 6 / 16")
    ok(R["led_e_6"] == [["open", 6]], "ohne X1206 (UPS HAT (E)): Lade-LED auf GPIO 6 wie bisher")
    ok(R["led_x12_6"] == [["open", 6], ["close", 6]] and R["led_hw"] == "X1206" and len(R["led_log"]) == 1,
       "X1206 erkannt: GPIO 6 sofort frei, nie wieder geöffnet, eine Warnung (%s, %s, %s)" % (R["led_x12_6"], R["led_hw"], R["led_log"]))
    ok(R["led_x12_13"][-1] == ["open", 13] and ["open", 6] not in R["led_x12_13"][2:], "Lade-LED auf GPIO 13 geht")
    ok("protect" not in R["btn_x12"] and R["btn_x12"].get("ack") == 26 and len(R["btn_log"]) == 1, "Taste auf GPIO 16 mit X1206: aus, Warnung")
    ok(R["btn_e"].get("protect") == 16, "Taste auf GPIO 16 ohne X1206: wie bisher")
    ok(R["relay_x12"] == [22] and R["relay_e"] == [22, 16], "Relais / Lampen: GPIO 6 / 16 nur ohne X1206 (%s)" % R["relay_e"])
    ok(R["pins_model_x12"] == [6, 16], "Modell «x12» fest gewählt: GPIO 6 / 16 gesperrt")
    print("6  Einstellungen und Texte")
    ok(R["defaults"] == ["13", "12", 13], "neue Geräte: GPIO 13 / 12")
    ok(R["old_file"] == ["6", "16"] and R["new_file"] == ["13", "12"], "ältere Einstellungen behalten 6 / 16 (%s / %s)" % (R["old_file"], R["new_file"]))
    ok("6" not in R["choices"] and "16" not in R["choices"] and "13" in R["choices"], "Auswahl ohne GPIO 6 / 16 mit X1206")
    ok(R["ups_choices"] == ["auto", "e", "x12", "ina"], "Modelle: %s" % R["ups_choices"])
    t = R["tr"]
    ok(t["de"] == "Lade-LED: GPIO" and len({t[L] for L in ("fr", "it", "rm", "en")}) == 4, "Texte in 5 Sprachen: %s" % t)
    ok(R["help"][0] and R["help"][1] >= 2 and R["help"][2] >= 6, "Anleitung de / en / fr / it / rm nennt den X1206 (%s)" % R["help"])
    ok(R["web"], "Anzeige oben: «Geekworm X1206»")
    ok(R["i2c"] == [], "INA219-Adresse zählt mit dem X1206 nicht als Konflikt")
    ok(str(R["selftest"]).startswith("model «x12»"), "Selbsttest des Teils: %s" % R["selftest"])
    print("7  Laden steuern (639zzzzz): Kälte, Notfall, «Trotzdem laden», «Akku schonen»")
    ok(R["c_warm"][0] == "" and R["c_warm"][2] == [], "warm: GPIO 16 nie angefasst (%s)" % (R["c_warm"],))
    ok(R["c_cold"][0] == "cold" and R["c_cold"][2] == ["op dh"] and R["c_cold"][1] is False, "unter 0 °C: GPIO 16 hoch, lädt nicht (%s)" % (R["c_cold"],))
    ok(len([l for l in R["c_cold_log"] if "owns" in l]) == 0 and any("switched off" in l for l in R["c_cold_log"]), "eigene Sperre: keine Warnung «GPIO 16 hoch» (%s)" % R["c_cold_log"])
    ok(R["c_hyst"] == ["cold", "cold", ""] and R["c_pins"] == ["op dh", "ip pd"], "Hysterese: frei erst ab 3 °C, dann Eingang mit Pull-down (%s %s)" % (R["c_hyst"], R["c_pins"]))
    ok(R["c_ov"] == "override" and R["c_ov_end"] == "cold" and len(R["c_ov_push"]) == 1, "«Trotzdem laden» 1 h mit Push, danach wieder gesperrt")
    ok(R["c_emerg"] == ["emergency", "emergency", "cold"] and len(R["c_emerg_push"]) == 1, "unter 10 %% lädt es trotzdem (frei bis 13 %%), ein Push (%s)" % R["c_emerg"])
    ok(R["c_nobme"][0] == "" and R["c_nobme_state"].get("no_bme") is True, "ohne BME280: keine Sperre, nur Hinweis")
    ok(R["c_care"] == ["care", "care", ""] and R["c_care_pins"] == ["op dh", "ip pd"], "«Akku schonen»: aus bei 80 %%, wieder ab 75 %% (%s)" % R["c_care"])
    ok(R["c_low"] == ["op dl"] and R["c_low_read"] is False, "Pegel «tief» einstellbar: GPIO 16 tief = Laden aus (%s)" % R["c_low"])
    ok(R["c_file"].get("we_blocked") is False and "cyc_pct" in R["c_file"], "akku_lernen.json im Datenordner")
    print("8  Lernen: Laufzeit, «voll in», Zyklen, Kapazität")
    lr = R["l_run"]
    ok(lr["use_src"] == "learned" and R["l_rate"] and abs(R["l_rate"] - 16.0) < 2.5 and lr["hours"] and abs(lr["hours"] - lr["pct"] / R["l_rate"]) < 0.2,
       "Restzeit aus dem Abfall %%/h (%s, %s)" % (lr, R["l_rate"]))
    ok(R["l_night"], "Nachtprognose rechnet mit dem gelernten Verbrauch")
    cap = R["l_cap"]
    ok(cap[0] and 25 < cap[0] < 38 and cap[1] == 1 and cap[2] and 38 < cap[2] < 60 and 0.35 < cap[3] < 0.45, "Kapazität aus 2.5 h / 40 %%: %s" % cap)
    lf = R["l_full"]
    ok(lf[0] is True and lf[1] and abs(lf[1] - (100 - lf[2]) / 30.0 * 60) < 25, "voll in … aus dem Anstieg (%s)" % lf)
    ok(any("Vollzyklen" in l for l in R["l_lines"]), "Zeilen der Akku-Karte deutsch: %s" % R["l_lines"])
    print("9  Schlafen, Licht dimmen, Selbsttests")
    ok(R["s_rtc"] == ["", "1900000123"], "Weckzeit in den RTC (%s)" % R["s_rtc"])
    ok(str(R["s_self"]).startswith("fixed times"), "Selbsttest Schlafen: %s" % R["s_self"])
    ok(str(R["a_self"]).startswith("cold block"), "Selbsttest Laden: %s" % R["a_self"])
    ok(R["dims"] == [[2, 100.0], [3, 40.0], [2, 30.0]], "Licht in %% am PCA9685, nur bei Änderung (%s)" % R["dims"])
    ok(R["pca_bits"] == [[2, 4096, 0], [2, 0, 4096], [3, 0, 2048]], "100 %% = ganz an wie bisher, 0 %% = aus, 50 %% = PWM (%s)" % R["pca_bits"])
    print("\n" + ("X1206-Test OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
