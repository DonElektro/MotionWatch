#!/usr/bin/env python3
"""Test «Simulator verbinden ist kein Stromausfall» (4.17.1, Teil 639zzzzq + 100 BatteryMonitor.tick).

Lädt die gebaute Datei in einem eigenen Prozess und spielt mit dem echten BatteryMonitor.tick, dem echten ups_events und
dem echten Push-Weg (Notifier.info / tamper / person -> _dispatch, nur das Versenden selbst ist ersetzt):
  echter Akku am Netz -> Simulator verbindet (simulierter Akku «auf Batterie»): keine Push «Stromausfall», kein Sabotage-Alarm
  (Schutz an), eine Zeile im Protokoll · Simulator trennt: keine Push «Strom wieder da» · 2 Minuten später ein ECHTER
  Stromausfall: Push (Schutz aus) bzw. Sabotage-Alarm (Schutz an) · 60 s Ruhe: Gerätemeldung nur im Protokoll, Person-Alarm
  geht · Schalter «keine Push»: verbunden nichts, echte Sabotage und SOS trotzdem.

  python3 werkzeuge/sim_push_ruhe_test.py [--datei X.py]
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

LAUF = r'''
import json, os, sys, time, threading
from collections import deque
ns = {"__name__": "mw_simq_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
C, S, SIM = ns["CFG"], ns["STATE"], ns["SIM"]
erg = []; logs = []; sent = []; tamper = []
def ok(b, t):
    erg.append([bool(b), t])
ns["log_event"] = lambda kind, msg, *a, **k: logs.append(str(msg))
ns["save_settings"] = lambda *a, **k: None
ns["_simq_dispatch_before"] = lambda self, p, jpg, fname: sent.append(dict(p))     # the real sending (ntfy, …) is not done here
N = ns["Notifier"]
N.configured = staticmethod(lambda: True)
notifier = N()
W = type("W", (), {})(); W.notifier = notifier; W.frame_out = None; W.cap = object()
ns["WATCH_REF"]["w"] = W
armed = {"on": False}
ns["is_armed"] = lambda: armed["on"]
ns["TAMPER"] = type("T", (), {"alarm": lambda self, what, looked=None: tamper.append(what)})()
C.update(notify_on=True, ups_push=True, ups_on=True, tamper_power=True, sim_on=False, sim_push_off=False, lang="de", batt_warned=False)
SB = {"v": None}; REAL = {"on_batt": False}
ns["sim_sensor"] = lambda k: SB["v"] if k == "battery" else None
ns["drill_active"] = lambda *a: False
BM = ns["BatteryMonitor"]
bm = BM.__new__(BM); bm._t = time.time(); bm.hist = deque(maxlen=60); bm.uhist = deque(maxlen=6)
bm.ups_tick = lambda: bm.ups_events(7.8, 80, None, REAL["on_batt"], True)       # the real UPS HAT: mains or battery
def tick():
    sent.clear(); tamper.clear(); bm.tick(); time.sleep(0.4)                      # (Notifier sends in its own thread)
def pushes():
    return [str(p.get("text") or p.get("event")) for p in sent]
def sim_connect(now):
    C["sim_on"] = True; SIM.update(ok=True, t=now, since=now)
    SB["v"] = {"v": 15.2, "a": -0.6, "pct": 61, "on_battery": True, "charging": False, "cap_wh": 40.0, "load_w": 7.0}
def sim_leave(now):
    C["sim_on"] = False; SIM.update(ok=False, t=now, since=0.0, off_t=now); SB["v"] = None

for arm in (False, True):
    armed["on"] = arm; lab = "Schutz an" if arm else "Schutz aus"
    bm._on_batt = None; bm._val_src = None; SIM.update(ok=False, t=0.0, since=0.0, off_t=0.0); C["sim_on"] = False; SB["v"] = None
    REAL["on_batt"] = False; tick(); tick()
    ok(not sent and not tamper, f"{lab}: echter Akku am Netz, nichts")
    sim_connect(time.time()); tick()
    ok(not any("Strom" in x or "Power" in x for x in pushes()) and not tamper,
       f"{lab}: Simulator verbindet (sein Akku «auf Batterie»): keine Push «Stromausfall», kein Sabotage-Alarm ({pushes()}, {tamper})")
    ok(any("from the simulator - no power event" in l for l in logs), f"{lab}: eine Zeile im Protokoll")
    tick()
    ok(not sent and not tamper, f"{lab}: verbunden, nichts mehr")
    sim_leave(time.time()); tick()
    ok(not any("Strom" in x or "Power" in x for x in pushes()) and not tamper, f"{lab}: Simulator trennt: keine Push «Strom wieder da» ({pushes()})")
    ok(any("from the device - no power event" in l for l in logs), f"{lab}: Protokoll beim Trennen")
    SIM.update(t=time.time() - 120, off_t=time.time() - 120)                       # 2 minutes later
    REAL["on_batt"] = True; tick()
    if arm:
        ok(tamper == ["power"], f"Schutz an: ECHTER Stromausfall 2 min später -> Sabotage-Alarm ({tamper})")
    else:
        ok(any("Stromausfall" in x or "Power cut" in x for x in pushes()), f"Schutz aus: ECHTER Stromausfall 2 min später -> Push ({pushes()})")
    REAL["on_batt"] = False; tick()
    ok(any("Strom wieder da" in x or "Power back" in x for x in pushes()), f"{lab}: echter Strom wieder da -> Push ({pushes()})")

# the 60 s quiet time and the switch
armed["on"] = True
sim_connect(time.time()); sent.clear()
notifier.info("WLAN: verbunden", title="{name}: Netz"); time.sleep(0.3)
ok(not sent, "60 s nach dem Verbinden: Gerätemeldung nur ins Protokoll")
ok(any(l.startswith("No push (simulator just connected") for l in logs), "… mit einer Zeile im Protokoll")
p = {"event": "person", "persons": 1, "time": "", "snapshot": None, "rain": False, "wind": "", "source": "x", "link": ""}
notifier._dispatch(dict(p), None, "");
ok(any(x.get("event") == "person" for x in sent), "60 s nach dem Verbinden: Person-Alarm geht wie immer")
SIM.update(since=time.time() - 300); sent.clear()
notifier.info("WLAN: verbunden", title="{name}: Netz"); time.sleep(0.3)
ok(len(sent) == 1, "nach 60 s: Gerätemeldungen wieder als Push")
C["sim_push_off"] = True; sent.clear()
notifier._dispatch(dict(p), None, ""); notifier.info("WLAN: verbunden", title="{name}: Netz"); time.sleep(0.3)
ok(not sent, "Schalter «keine Push» + verbunden: weder Alarm noch Gerätemeldung")
notifier.tamper(ns["tr"]("device moved")); notifier.info("SOS", title="{name}: 🆘 SOS"); time.sleep(0.4)
ok(sorted(x.get("event") for x in sent) == ["info", "tamper"], f"Schalter an: echte Sabotage und SOS trotzdem ({[x.get('event') for x in sent]})")
S["source_id"] = "sim:0"; sent.clear()
notifier.tamper(ns["tr"]("camera covered")); time.sleep(0.4)
ok(not sent, "Schalter an: «Kamera abgedeckt» aus dem Simulator-Bild zurückgehalten")
sim_leave(time.time()); SIM.update(t=time.time() - 300, off_t=time.time() - 300); sent.clear()
notifier._dispatch(dict(p), None, ""); time.sleep(0.2)
ok(len(sent) == 1, "Simulator lange weg: Schalter wirkt nicht mehr")
ok("sim_push_off" in ns["USER_SETTINGS_DENY"] and any(x[1] == "sim_push_off" for x in ns["TOGGLES"]), "Schalter: nur Administrator, im Abschnitt Simulator")
k = "While the simulator is connected: no push"
ok(ns["DE"].get(k, "").startswith("Während") and all(ns["TRX"][L].get(k) for L in ("fr", "it", "rm")), "Schalter in 5 Sprachen")
print("ERG " + json.dumps(erg))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Sim-Push-Ruhe-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_simq_")
    try:
        env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "daten"))
        r = subprocess.run([sys.executable, "-c", LAUF, datei], capture_output=True, text=True, timeout=600, env=env,
                           cwd=os.path.dirname(datei))
        erg = None
        for ln in (r.stdout + r.stderr).splitlines():
            if ln.startswith("ERG "):
                erg = json.loads(ln[4:])
        if erg is None:
            print((r.stdout + r.stderr)[-3000:])
            print("FEHLER: der Lauf brach ab")
            return 1
        for b, t in erg:
            print(("  ok   " if b else "  FEHLER  ") + t)
        bad = [t for b, t in erg if not b]
        print("Sim-Push-Ruhe-Test OK" if not bad else "FEHLER: " + "; ".join(bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
