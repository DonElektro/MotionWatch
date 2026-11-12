#!/usr/bin/env python3
"""Test «Akku bis Sonnenaufgang?» (Teil 280 night_warn_reason, Teil 100 BATT_N) - die Abend-Meldung nach einem Neustart
und die Anzeige dazu (Selbst-Check: am Netz «Netzbetrieb» / «lädt», in der Einschwingzeit noch nichts - gleiche Regel night_hold).

Hintergrund (Besitzer 13.11.2026): nach jedem Update-Neustart kam «🪫 Akku bis Sonnenaufgang? – Noch 5.2 h, nötig 10.7 h»,
am Netz und mit 99 % Akku. Ursachen: (1) die Prognose fragte nicht, ob das Gerät überhaupt vom Akku läuft, (2) am Netz ist
der Verbrauch ein einzelner Augenblickswert, direkt nach dem Start bei voller Rechenlast, (3) «heute schon gewarnt» stand
nur im Speicher.

  python3 werkzeuge/akku_nacht_test.py [--datei X.py]

Jeder «Neustart» ist ein eigener Python-Prozess mit demselben Daten-Ordner. Die USV ist die echte Auswertung des UPS HAT (E)
(BatteryMonitor.ups_e) mit erfundenen Messwerten; Uhr (20:46), Dunkelheit und Push-Empfänger sind ersetzt. Ohne Netz, ohne
Hardware.
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
from datetime import datetime
ns = {"__name__": "mw_akku_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
fall = json.loads(sys.argv[2])
pushes = []
class N:
    def info(self, text, *a, **k):
        pushes.append(text)
class W:
    notifier = N()
ns["WATCH_REF"]["w"] = W()
ns["sim_now"] = lambda: datetime(*fall["zeit"])
ns["is_dark"] = lambda *a, **k: True
ns["sim_sensor"] = lambda *a, **k: None
ns["_pmic_watts"] = lambda: None
C = ns["CFG"]
C.update(night_warn=True, solar_on=False, ups_push=True, ups_on=True, ups_shutdown_pct=0, lang="de", latitude=47.37, longitude=8.54)
ns["STATE"]["cpu"] = fall.get("cpu", 20.0)
bm = ns["BatteryMonitor"].__new__(ns["BatteryMonitor"])
from collections import deque
bm.hist = deque(maxlen=60); bm.uhist = deque(maxlen=6)
if "BATT_N" in ns:
    ns["BATT_N"].update(n=0, ups=6, bank=60)
sol = ns["SolarMonitor"].__new__(ns["SolarMonitor"])
out = []
for i in range(fall["ticks"]):
    if fall.get("bank"):                                   # powerbank without UPS: the state as BatteryMonitor.tick writes it
        ns["STATE"]["battery"] = {"on": True, "watts": fall["w"], "use_w": fall["w"], "src": "estimate", "pct": fall["pct"],
                                  "hours": 1.0, "since": 1.0, "cap_wh": fall["cap"]}
    else:
        netz = fall["netz"]; pct = fall["pct"]
        a = 0.2 if netz else -fall["w"] / 8.0
        r = {"state": (0x20 | 5) if netz else 0x00, "a": a, "v": 8.0, "pct": pct, "mah": int(fall["cap"] * pct / 100.0 / 8.0 / 0.9 * 1000),
             "min_left": 0xFFFF, "min_full": 0xFFFF, "cells": [4.0, 4.0], "vbus": 5.1 if netz else 0.0}
        bm.ups_e(r)
    if "BATT_N" in ns:
        ns["BATT_N"]["n"] += 1
    sol.tick()
    out.append(len([p for p in pushes if "sunrise" in p or "Sonnenaufgang" in p]))
b = ns["STATE"]["battery"]; nf = ns["STATE"].get("night") or {}
try:
    hc = ns["health_check"]("de")
    it = [x for x in (hc.get("items") if isinstance(hc, dict) else hc) if isinstance(x, dict) and x.get("id") == "batt"]
except Exception as e:
    it = [{"text": "health_check: %r" % e, "level": "?"}]
print("ERG " + json.dumps({"n": out, "use_w": b.get("use_w"), "cap": b.get("cap_wh"), "on_batt": b.get("on_battery"), "have": nf.get("have_h"),
                           "need": nf.get("need_h"), "enough": nf.get("enough"), "hold": nf.get("hold"), "batt": (it or [{}])[0].get("text"), "lvl": (it or [{}])[0].get("level"), "text": [p for p in pushes if "sunrise" in p or "Sonnenaufgang" in p][:1],
                           "datei": os.path.isfile(os.path.join(ns["DATA_DIR"], "night_warned.json"))}, ensure_ascii=False))
os._exit(0)
'''


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


def lauf(datei, home, **fall):
    fall.setdefault("zeit", [2026, 11, 13, 20, 46])
    r = subprocess.run([sys.executable, "-c", LAUF, datei, json.dumps(fall)], capture_output=True, text=True, timeout=300,
                       env=dict(os.environ, MOTIONWATCH_HOME=home), cwd=os.path.dirname(datei))
    for ln in (r.stdout + r.stderr).splitlines():
        if ln.startswith("ERG "):
            return json.loads(ln[4:])
    print((r.stdout + r.stderr)[-1500:])
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--zeigen", action="store_true", help="nur den Fall des Besitzers zeigen (zum Vergleich mit einer älteren Datei)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Akku-Nacht-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_akku_")
    try:
        h = lambda n: os.path.join(tmp, n)
        if a.zeigen:
            print(json.dumps(lauf(datei, h("z"), netz=True, pct=99, cap=40.0, w=3.0, cpu=100.0, ticks=2), ensure_ascii=False))
            return 0
        print("1  Neustart am Netz, Akku 99 %, volle Rechenlast (der Fall des Besitzers)")
        r = lauf(datei, h("a"), netz=True, pct=99, cap=40.0, w=3.0, cpu=100.0, ticks=12)
        ok(r.get("enough") is False and r.get("on_batt") is False, "die Prognose selbst sagt «reicht nicht» (%s h von %s h bei %s W Augenblickswert) - am Netz"
           % (r.get("have"), r.get("need"), r.get("use_w")))
        ok(r.get("n") == [0] * 12 and r.get("datei") is False, "keine Meldung, auch nach der Einschwingzeit nicht (%s)" % r.get("n"))
        ok(r.get("hold") == "mains" and "Sonnenaufgang" not in str(r.get("batt")) and "99 %" in str(r.get("batt")) and "Netzbetrieb" in str(r.get("batt"))
           and r.get("lvl") == "ok", "Selbst-Check zeigt den Netzbetrieb statt «zu wenig bis Sonnenaufgang» (%s, %s)" % (r.get("batt"), r.get("lvl")))
        print("2  Neustart am Akku, genug Ladung")
        r = lauf(datei, h("b"), netz=False, pct=99, cap=60.0, w=3.0, ticks=12)
        ok(r.get("enough") is True and r.get("n") == [0] * 12, "keine Meldung (%s h von %s h)" % (r.get("have"), r.get("need")))
        print("3  Neustart am Akku, wirklich zu wenig")
        r = lauf(datei, h("c"), netz=False, pct=50, cap=40.0, w=4.0, ticks=10)
        ok(r.get("enough") is False and r.get("on_batt") is True, "Prognose: %s h von %s h" % (r.get("have"), r.get("need")))
        ok(r.get("n") == [0] * 5 + [1] * 5, "erst nach der Einschwingzeit (6 Messungen = 1 Minute bei der USV), dann genau einmal (%s)" % r.get("n"))
        ok(bool(r.get("text")) and str(r.get("have")) in r["text"][0] and r.get("datei") is True, "Text mit den Stunden, der Abend ist gemerkt")
        ok(r.get("hold") == "" and "zu knapp bis Sonnenaufgang" in str(r.get("batt")) and r.get("lvl") == "warn",
           "Selbst-Check sagt dasselbe wie die Meldung (%s, %s)" % (r.get("batt"), r.get("lvl")))
        r = lauf(datei, h("c2"), netz=False, pct=50, cap=40.0, w=4.0, ticks=3)
        ok(r.get("hold") == "settling" and r.get("n") == [0] * 3 and "Sonnenaufgang" not in str(r.get("batt")) and "50 %" in str(r.get("batt")),
           "in der Einschwingzeit: weder Meldung noch «zu knapp» in der Anzeige (%s)" % r.get("batt"))
        r = lauf(datei, h("c"), netz=False, pct=48, cap=40.0, w=4.0, ticks=10)
        ok(r.get("n") == [0] * 10, "zweiter Neustart am selben Abend: keine zweite Meldung (%s)" % r.get("n"))
        r = lauf(datei, h("c"), netz=False, pct=48, cap=40.0, w=4.0, ticks=3, zeit=[2026, 11, 14, 1, 30])
        ok(r.get("n") == [0] * 3, "nach Mitternacht nicht noch einmal")
        r = lauf(datei, h("c"), netz=False, pct=40, cap=40.0, w=4.0, ticks=8, zeit=[2026, 11, 14, 20, 0])
        ok(r.get("n") == [0] * 5 + [1] * 3, "am nächsten Abend wieder (%s)" % r.get("n"))
        print("4  Neustart am Akku, kritisch (unter der Grenze «fast leer»)")
        r = lauf(datei, h("d"), netz=False, pct=15, cap=40.0, w=4.0, ticks=3)
        ok(r.get("n") == [1, 1, 1] and r.get("hold") == "" and "zu knapp bis Sonnenaufgang" in str(r.get("batt")),
           "sofort, ohne Einschwingzeit, einmal; die Anzeige ebenso (%s · %s)" % (r.get("n"), r.get("batt")))
        print("5  Powerbank ohne USV (kein Netz-Signal)")
        r = lauf(datei, h("e"), bank=True, pct=50, cap=40.0, w=4.0, ticks=62)
        n = r.get("n") or []
        ok(n[:59] == [0] * 59 and n[59:] == [1] * 3, "nach der Einschwingzeit (60 Messungen = 10 Minuten, das Fenster der Schätzung), einmal")
        r = lauf(datei, h("f"), bank=True, pct=10, cap=40.0, w=4.0, ticks=2)
        ok(r.get("n") == [1, 1], "kritisch: sofort")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + ("Akku-Nacht-Test OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
