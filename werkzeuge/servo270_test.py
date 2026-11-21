#!/usr/bin/env python3
"""Test Schwenk-Servo 270° (MoveEye, Einstellung pan_servo_range = 270): alles rechnet mit ±135° statt ±90°.

  Ohne echte Hardware: die gebaute Datei wird geladen (Daten in einem Temp-Ordner) und geprüft:
    1. Grenzen: servo_half, Hardware.limits / srv_clamp mit pan_limit 135 (ganzer Bereich) und 90 (Teil davon).
    2. Teach-in: Grad der gespeicherten Punkte (0 % = -135°, 100 % = +135°), _wp_make klemmt auf 0 … 100 %.
    3. Runde / Patrouille: die Haltepunkte aus den Wegpunkten (auch ganz aussen), kopf_pan_add ohne Umlauf (nur 360° läuft rund).
    4. Zonen in Grad (feste / verankerte Zonen): Bildpunkt -> Richtung -> Bildpunkt bei +120°, Kamera ganz aussen.
    5. Simulator-Verbindung: sim_state «servo» (pan_range 270, pan_limit, pan_goal / pan_deg ±135°).
    6. Gegenprobe 180° und 360° (wie bisher).

  python3 werkzeuge/servo270_test.py [--datei webcam_bewegung_X_Y_Z.py]
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
import json, os, sys
ns = {"__name__": "mw_servo270_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
C = ns["CFG"]; R = {}
C.update(pan_servo_range=270, servo_range=180, pan_limit=135, tilt_limit=60, pan=50.0, tilt=50.0, patrol=True, kopf_on=True,
         kopf_round=False, kopf_save=False, servo_kind="positional")
R["half"] = ns["servo_half"]("pan")
R["lim135"] = ns["Hardware"].limits()[0]
R["clamp135"] = ns["srv_clamp"](100.0, 50.0)
C["pan_limit"] = 90
R["lim90"] = [round(x, 2) for x in ns["Hardware"].limits()[0]]
R["clamp90"] = [round(x, 2) for x in ns["srv_clamp"](100.0, 50.0)]
C["pan_limit"] = 180
R["lim180"] = ns["Hardware"].limits()[0]
C["pan_limit"] = 135
W = ns["WAYPOINTS"]; W[:] = [ns["_wp_make"](0, 50, "links"), ns["_wp_make"](100, 50, "rechts"), ns["_wp_make"](50, 50), ns["_wp_make"](120, 50, "zu weit")]
R["teach"] = [(p["name"], p["pan"], p["deg"][0]) for p in ns["teach_list"]("en")]
R["plan"] = [round(s[0], 2) for s in ns["kopf_patrol_plan"]()[0]]
pa = ns["kopf_pan_add"]
R["add"] = [round(pa(50, 120), 2), round(pa(round(pa(50, 120), 2), 30), 2), round(pa(50, -200), 2)]
p120 = 50 + 120 / 135 * 50
ang = ns["sleep_to_ang"]([(0.5, 0.5), (0.7, 0.4)], pan=p120, tilt=50)
R["ang"] = ang
R["proj"] = [[round(v, 3) for v in pt] for pt in ns["sleep_project"](ang, pan=p120, tilt=50)[::8]]
C["pan"] = 100.0
st = ns["sim_state"]()["servo"]
R["sim"] = {k: st.get(k) for k in ("pan_range", "pan_limit", "pan_goal")}
C["pan"] = 50.0
C.update(pan_servo_range=180, pan_limit=90)
R["half180"] = [ns["servo_half"]("pan"), round(pa(50, 120), 2), ns["sim_state"]()["servo"]["pan_range"]]
C.update(pan_servo_range=360, pan_limit=180)
R["half360"] = [ns["servo_half"]("pan"), round(pa(95, 30), 2)]
print("ERG " + json.dumps(R, default=str))
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
    print("Servo-270°-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_servo270_")
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
    print("1  Grenzen")
    ok(R["half"] == 135.0, "servo_half = 135° (%s)" % R["half"])
    ok(R["lim135"] == [0.0, 100.0] and R["clamp135"] == [100.0, 50.0], "pan_limit 135: ganzer Bereich 0 … 100 %")
    ok(R["lim90"] == [16.67, 83.33] and R["clamp90"] == [83.33, 50.0], "pan_limit 90 bei 270°: ±90° = 16,7 … 83,3 %% (%s)" % R["lim90"])
    ok(R["lim180"] == [0.0, 100.0], "pan_limit über 135 bleibt beim Ende des Servos")
    print("2  Teach-in")
    t = R["teach"]
    ok(t[0][2] == -135.0 and t[1][2] == 135.0 and t[2][2] == 0.0, "0 %% = -135°, 100 %% = +135°, Mitte 0° (%s)" % t)
    ok(t[3][1] == 100.0 and t[3][2] == 135.0, "zu weit wird auf 100 %% = +135° geklemmt (%s)" % (t[3],))
    print("3  Runde")
    ok(R["plan"] == [0.0, 100.0, 50.0, 100.0], "Haltepunkte bis ganz aussen (%s)" % R["plan"])
    ok(R["add"] == [94.44, 100.0, 0.0], "drehen um +120° = 94,4 %%, weiter +30° bleibt am Ende, -200° am anderen Ende (%s)" % R["add"])
    print("4  Zonen in Grad")
    a0 = R["ang"][0]
    ok(abs(a0[0] - 120.0) < 0.01 and abs(a0[1]) < 0.01, "Bildmitte bei +120° = Richtung +120° (%s)" % a0)
    pr = R["proj"]
    ok(abs(pr[0][0] - 0.5) < 0.01 and abs(pr[0][1] - 0.5) < 0.01, "zurück ins Bild: wieder die Mitte (%s)" % pr)
    print("5  Simulator-Verbindung")
    ok(R["sim"] == {"pan_range": 270.0, "pan_limit": 135.0, "pan_goal": 135.0}, "sim_state: %s" % R["sim"])
    print("6  Gegenprobe 180° / 360°")
    ok(R["half180"] == [90.0, 100.0, 180.0], "180°: wie bisher (%s)" % R["half180"])
    ok(R["half360"][0] == 180.0 and R["half360"][1] < 10, "360°: läuft rund (%s)" % R["half360"])
    print("\n" + ("Servo-270°-Test OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
