#!/usr/bin/env python3
"""Test «🔦 Gäste erwartet» (MoveEye Teil 639zzzzzg) – Führungslicht, ohne Hardware.

  A) im eigenen Prozess (gebaute Datei geladen, Kopf ohne Servo-Schleife, Push / Sirene / Licht nachgemacht):
     Zielen (Bodenpunkt, 2 m voraus in Gehrichtung, Umdrehen, die Person bleibt im Bild der Kopf-Kamera, mit fester
     Weitwinkel-Kamera frei), Ziel erreicht -> Licht aus, Abschied -> wieder an, Zeiten (aus dem Bild / steht still /
     höchstens), kein neues Licht am selben Ort, kein Alarm für Personen / Wärme / Bewegung / Abschreckung / Relais, aber
     Sabotage, Diebstahl, SOS-Lampe und Sensor-Sirene wie immer, ohne Zusatz-ZIP alles wie früher, Schalter «auch Tiere»,
     Licht blendet weich auf (Rampe, ein / aus ohne Dimmen), der Kopf fährt (Beweger «guide», Folgen pausiert), «bis HH:MM»,
     Zeitplan, Zustand an den Simulator (guests, white_level), Texte in 5 Sprachen.
  B) --browser: MoveEye (Demo, eigener Daten-Ordner), Einstellungen → Schutz → «Gäste erwartet» 390 px dunkel: Karte,
     «bis», Ziel, 5 Sprachen, keine JS-Fehler; Bilder nach --bilder (gaeste_karte.png, gaeste_karte_pc.png).
  C) --sim GODOT: Simulator (Xvfb) + MoveEye verbunden, Nacht, «Gäste erwartet» mit dem Zelt als Ziel, Szenario «Gäste
     besuchen das Zelt»: Bilder des Simulator-Fensters (PC 1280 × 720, Handy hochkant 390 × 844) nach --bilder und als
     GLBILD-Zeilen ins Protokoll (--bilder-aus-log LOG setzt sie wieder zusammen; schwer: HP-Testweg).

  python3 werkzeuge/gaeste_licht_test.py [--datei X.py] [--browser] [--sim GODOT] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import json
import math
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []

TEIL_A = r'''
import json, math, os, sys, threading, time
ns = {"__name__": "mw_gaeste_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
C, S, K = ns["CFG"], ns["STATE"], ns["KOPF"]
out = {}
ns["save_settings"] = lambda *a, **k: None
ns["SRV"]["pos"] = None; ns["SRV"]["started"] = False
C.update(lang="de", pan=50.0, tilt=50.0, kopf_on=True, sim_on=False, light_white_out="pca:2", armed=True, notify_on=True,
         gl_on=False, gl_until="", gl_until_t=0.0, gl_target={}, gl_animals=True, gl_dark_only=False, gl_push=True, gl_pct=60,
         gl_fade_in_s=3.0, gl_fade_out_s=4.0, gl_lost_s=10, gl_still_s=30, gl_max_min=5, gl_target_r=2.0, cam_height=1.6, browser_alarm=True,
         push_bundle=False)
S.update(tracking=False, persons=0, warm=0, arm_state="armed")
GC = ns["GuideCore"]
aim_ang = ns["gl_aim_angles"]
# ---- 1. geometry ----------------------------------------------------------------------------------------------------------------
def walk(c, t0, p0, v, secs, step=0.1, target=None, **kw):
    ev = []
    for i in range(int(round(secs / step))):
        t = t0 + i * step
        ev += c.step(t, [(p0[0] + v[0] * i * step, p0[1] + v[1] * i * step, "person")], target, **kw)
    return ev, t0 + secs
c = GC()
ev, t = walk(c, 1000.0, (-4.0, 8.0), (1.0, 0.0), 4.0)
a = c.aim()
out["ahead"] = [round(c.p[0], 2), round(c.p[1], 2), round(a[0], 2), round(a[1], 2), ev]
ev2, t = walk(c, t, (c.p[0], 8.0), (-1.0, 0.0), 0.6)
out["flip_early"] = round(c.aim()[0] - c.p[0], 2)
ev2, t = walk(c, t, (c.p[0], 8.0), (-1.0, 0.0), 1.6)
out["flip"] = [round(c.p[0], 2), round(c.aim()[0], 2)]
c = GC()
ev, t = walk(c, 2000.0, (0.0, 14.0), (0.0, -1.0), 3.0)
a = c.aim()
out["towards"] = [round(c.p[1], 2), round(a[1], 2)]
# the person stays in the head picture: near person, walking towards the camera, light 2 m ahead
fov = (66.0, 41.0)
p = (0.0, 3.0); tg = (0.0, 1.0)
az, pitch = aim_ang(tg, p, 1.6, fov)
azf, pitchf = aim_ang(tg, p, 1.6, None)
e_head = math.degrees(math.atan2(1.7 - 1.6, 3.0)); e_feet = -math.degrees(math.atan2(1.6, 3.0))
out["clamp"] = [round(pitch, 2), round(pitchf, 2), round(e_head - (pitch + 41.0 / 2), 2), round(e_feet - (pitch - 41.0 / 2), 2)]
p = (0.0, 4.0); tg = (6.0, 4.0)                       # sideways, a big step ahead: stays inside the picture horizontally
az, _ = aim_ang(tg, p, 1.6, fov)
out["clamp_side"] = [round(az, 2), round(math.degrees(math.atan2(6.0, 4.0)), 2)]
# ---- 2. target, farewell, timeouts, block -------------------------------------------------------------------------------------------
c = GC()
ev, t = walk(c, 3000.0, (0.0, 14.0), (0.0, -1.0), 10.0, target=(0.0, 5.0), r=2.0)
out["arrive"] = [ev, c.phase, c.light_wanted()]
ev, t = walk(c, t, (c.p[0], c.p[1]), (0.0, 0.0), 60.0, step=0.5, target=(0.0, 5.0), r=2.0)
out["stay"] = [ev, c.phase, c.light_wanted()]
ev, t = walk(c, t, (0.0, 5.0), (1.0, 0.6), 6.0, target=(0.0, 5.0), r=2.0)
a = c.aim()
out["farewell"] = [ev, c.phase, c.light_wanted(), round(a[0] - c.p[0], 2)]
ev3 = c.step(t + 11.0, [], (0.0, 5.0), r=2.0, lost_s=10.0)
out["farewell_gone"] = [ev3, c.phase]
c = GC(); c.step(4000.0, [(2.0, 6.0, "person")])
out["lost"] = [c.step(4009.0, [], lost_s=10.0), c.step(4010.5, [], lost_s=10.0)]
c = GC()
ev = []
for i in range(80):
    ev += c.step(5000.0 + i * 0.5, [(3.0 + (0.1 if i % 2 else -0.1), 7.0, "person")], still_s=30.0)
out["still"] = [ev, c.last_end["why"] if c.last_end else None]
out["block"] = [c.step(5045.0, [(3.0, 7.0, "person")]), c.step(5046.0, [(9.0, 2.0, "person")])]
c = GC()
ev, t = walk(c, 6000.0, (-30.0, 10.0), (0.1, 0.0), 305.0, step=1.0, max_s=300.0)
out["max"] = ev[-1:]
c = GC()
out["at_target_start"] = [c.step(7000.0, [(0.5, 5.0, "person")], (0.0, 5.0), r=2.0), c.phase, c.light_wanted()]
# ---- 3. no alarm for guests, the rest as always ----------------------------------------------------------------------------------------
sent = []
class W:
    pass
w = W()
w.frame_out = None
w.notifier = ns["Notifier"]()
w.notifier._dispatch = lambda p, jpg, fn: sent.append((p.get("event"), p.get("info_title") or "", p.get("text") or ""))
ns["Notifier"].configured = staticmethod(lambda: True)
ns["WATCH_REF"]["w"] = w
sirens = []
ns["_gl_siren_alarm"] = lambda kind: sirens.append(kind)
ns["is_armed"] = lambda: True
def alerts():
    return [x["kind"] for x in ns["ALERTS"]["items"]]
def run_alarms(tag):
    sent.clear(); sirens.clear(); ns["ALERTS"]["items"].clear(); ns["GL_NOTE"]["t"] = 0.0
    w.notifier.last = 0.0; w.notifier.last_pre = 0.0; w.notifier.last_warm = 0.0
    def go(f):
        try:
            f()
        except Exception as e:
            out.setdefault("errs", []).append("%s: %s %s" % (tag, type(e).__name__, e))
    go(lambda: w.notifier.person(1, None, None))
    go(lambda: w.notifier.prealarm(None, "warm"))
    go(lambda: w.notifier.prealarm(None))
    go(lambda: ns["push_alert"]("person", "person", count=1))
    go(lambda: ns["push_alert"]("warm", "warm"))
    go(lambda: ns["push_alert"]("prealarm", "movement"))
    go(lambda: ns["siren_alarm"]("person"))
    go(lambda: ns["siren_alarm"]("warm"))
    # what must ALWAYS go through
    go(lambda: w.notifier.tamper("Sabotage: camera covered", None))
    go(lambda: w.notifier.alert("{name}: THEFT ALARM", "moved", None))
    go(lambda: ns["siren_alarm"]("tamper"))
    go(lambda: ns["siren_alarm"]("sensor"))
    go(lambda: ns["push_alert"]("noise", "noise"))
    time.sleep(0.3)
    return {"sent": [x[0] for x in sent], "titles": [x[1] for x in sent], "texts": [x[2] for x in sent], "sirens": list(sirens), "alerts": alerts()}
C["gl_on"] = False
out["alarm_off"] = run_alarms("off")
C["gl_on"] = True
out["alarm_on"] = run_alarms("on")
ns["GL_ZD"]["ok"] = False
out["alarm_nozip"] = run_alarms("nozip")
ns["GL_ZD"]["ok"] = True
# a motion detector (PIR) fired by the guest: no alarm; the door sensor still alarms (review 22.11.2026)
def sensor(kind, nm):
    sent.clear(); sirens.clear()
    x = {"id": nm, "name": nm, "kind": kind, "alarm": "always", "src": "sim:" + nm}
    ns["SENS"]["st"].pop(nm, None)
    try:
        ns["sens_fire"](x, "active")
    except Exception as e:
        out.setdefault("errs", []).append("sensor %s: %s" % (nm, e))
    time.sleep(0.3)
    return [list(sent and [y[0] for y in sent]), list(sirens)]
C["gl_on"] = True
out["pir_on"] = sensor("pir", "PIR Zelt")
out["door_on"] = sensor("door", "Tuer")
C["gl_on"] = False
out["pir_off"] = sensor("pir", "PIR Zelt 2")
C["gl_on"] = True
# deterrence and relays
reacted = []
d = ns["Deterrence"](); d.react = lambda g, l: reacted.append(g)
C.update(deter_person_act="light", deter_pause=0.0)
for tt in (1.0, 2.5, 4.0):
    d.check({"person"}, tt)
out["deter_on"] = list(reacted)
C["gl_on"] = False; reacted.clear()
d2 = ns["Deterrence"](); d2.react = lambda g, l: reacted.append(g)
for tt in (1.0, 2.5, 4.0):
    d2.check({"person"}, tt)
out["deter_off"] = list(reacted)
C["gl_on"] = True
seen = []
base = ns["_gl_relays_update"]
ns["_gl_relays_update"] = lambda self, present: seen.append(sorted(present))
ns["RelayManager"]().update({"person", "warm", "noise", "door"})
ns["_gl_relays_update"] = base
out["relays"] = seen[-1]
# the SOS lamp goes first, the guide light only adds
ns["GL"]["want"] = True; ns["GL"]["lv"] = 1.0; ns["GL"]["lv_t"] = time.time() - 10
ns["GL"]["core"].phase = "guide"; ns["GL"]["core"].seen_t = time.time()
C.update(light_white="off", light_ir="off")
r1 = ns["lights_tick"]()
out["light_guide"] = [bool(r1.get("white")), ns["GL_LIGHT"]["drive"], ns["GL_LIGHT"]["pct"], bool(ns["GL_DIM"])]
sos = ns.get("ALM_SOS")
if sos is not None:
    sos.update(on=True, t0=time.time(), until=time.time() + 60, by="test")
    vals = set()
    for i in range(30):
        vals.add(bool(ns["lights_tick"]().get("white"))); time.sleep(0.05)
    out["sos"] = [sorted(vals), ns["GL_LIGHT"]["drive"], bool(ns["_alm_sos_blocked"](time.time())) if "_alm_sos_blocked" in ns else False]
    sos.update(on=False)
# fade: from off, the light comes up softly
ns["GL"]["want"] = False; ns["GL"]["lv"] = 0.0; ns["GL"]["lv_t"] = time.time() - 10
now = time.time()
ns["gl_light_set"](True, now)
fr = [round(ns["gl_light_want"](now + s)[0], 3) for s in (0.0, 0.5, 1.5, 3.0, 4.0)]
out["fade_in"] = fr
ns["gl_light_set"](False, now + 4.0)
out["fade_out"] = [round(ns["gl_light_want"](now + 4.0 + s)[0], 3) for s in (0.0, 2.0, 4.0)]
ns["GL"]["want"] = False; ns["GL"]["lv"] = 0.0
ns["GL"]["core"].reset()
# ---- 4. the animal switch, the head, a picture ---------------------------------------------------------------------------------------
class AI:
    objects = [(300, 200, 60, 40, 0.9, 18)]        # COCO 18 = dog (pixel box in a 640 x 360 picture)
    boxes = []
class Wk:
    ai = AI()
ns["COCO_LABELS"].setdefault(18, "dog")
C["gl_animals"] = True
out["animals_on"] = [o[2] for o in ns["gl_obs"](Wk(), [], [], [], 640, 360)]
C["gl_animals"] = False
out["animals_off"] = [o[2] for o in ns["gl_obs"](Wk(), [], [], [], 640, 360)]
C["gl_animals"] = True
class NoAI:
    ai = None
pb = [(300, 120, 40, 200)]                          # a person in the picture
g = ns["gl_obs"](NoAI(), [], pb, [], 640, 360)
out["person_ground"] = [round(v, 2) for v in g[0][:2]] if g else None
C.update(pan=50.0, tilt=50.0, gl_on=True)
t0 = time.time()
for i in range(12):
    ns["GL"]["pan_t"] = 0.0
    x = 300 + i * 12
    ns["gl_frame"](NoAI(), [], [(x, 120, 40, 200)], [], 640, 360, time.time())
    time.sleep(0.03)
out["head"] = [ns["GL"]["core"].phase, round(C["pan"], 1), round(C["tilt"], 1), "guide" in ns["kopf_claims"](), ns["kopf_track_blocked"](), ns["kopf_may"]("guide"), ns["kopf_may"]("round")]
out["sim"] = ns["sim_state"]().get("guests")
ns["GL"]["core"].reset(); ns["gl_phase_watch"](time.time())
# ---- 5. switch, end time, schedule, target ---------------------------------------------------------------------------------------------
ok_, msg = ns["gl_set"](True, "7:61", "test")
out["until_bad"] = [ok_, msg]
ok_, msg = ns["gl_set"](True, "23:59", "test")
out["until_ok"] = [ok_, C["gl_until"], C["gl_until_t"] > time.time()]
C["gl_until_t"] = time.time() - 1
ns["GL"]["on_was"] = True
ns["gl_tick"](time.time())
out["until_end"] = [C["gl_on"], ns["gl_active"]()]
C.update(gl_on=False, gl_until="", gl_until_t=0.0)
out["sched"] = ["gl_on" in ns["SCHED_KEYS"], ("gl_on", "Guests expected (guide light)") in ns["SCHED_FEATURES"]]
ns["SCHEDULES"][:] = [ns["_clean_schedule"]({"name": "Gäste", "enabled": True, "days": [0, 1, 2, 3, 4, 5, 6], "start": "00:00", "end": "23:59",
                                              "actions": {"gl_on": True}}, 0)]
ns["schedule_tick"]()
out["sched_on"] = [C["gl_on"], ns["gl_active"]()]
ns["SCHEDULES"][:] = []
ns["schedule_tick"]()
out["sched_off"] = C["gl_on"]
ok_, msg = ns["gl_set_target"]({"kind": "point", "x": 1.5, "y": 6.0, "name": "Zelt"})
out["target"] = [ok_, C["gl_target"].get("x"), C["gl_target"].get("y")]
C.update(pan=50.0, tilt=50.0); ns["SRV"]["pos"] = None
ok_, msg = ns["gl_set_target"]({"kind": "here"})
out["target_here"] = [ok_, msg]
C["tilt"] = 40.0; ns["SRV"]["pos"] = None
ok_, msg = ns["gl_set_target"]({"kind": "here"})
out["target_here_low"] = [ok_, round(math.hypot(C["gl_target"]["x"], C["gl_target"]["y"]), 1) if ok_ else msg]
out["state"] = sorted(ns["gl_state"]("de").keys())
out["deny"] = all(k in ns["USER_SETTINGS_DENY"] and k in ns["APPKEY_DENY_KEYS"] for k in ns["GL_DEF"])
tr = ns["tr"]
out["txt"] = {L: [tr("Guests expected", L), tr("guiding a guest", L), tr("A guest is coming – no alarm (guests expected).", L)] for L in ("de", "fr", "it", "rm", "en")}
out["help"] = [ns["HELP_PAGE"].count('id="gl-help"')] + [('id="gl-help"' in (ns["HELP_X"].get(L) or "")) for L in ("fr", "it", "rm")]
out["selftest"] = ns["gl_selftest"]()
print("ERG " + json.dumps(out, ensure_ascii=False, default=str))
'''


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def teil_a(datei, tmp):
    print("A) Gäste erwartet im eigenen Prozess", flush=True)
    home = os.path.join(tmp, "a"); os.makedirs(home)
    r = subprocess.run([sys.executable, "-c", TEIL_A, datei], capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, MOTIONWATCH_HOME=home), cwd=tmp)
    e = next((json.loads(ln[4:]) for ln in r.stdout.splitlines() if ln.startswith("ERG ")), None)
    if e is None:
        print((r.stdout + r.stderr)[-4000:])
        ok(False, "Teil A lief nicht durch")
        return
    ok(not e.get("errs"), "keine Ausnahmen in den Alarm-Wegen %s" % e.get("errs", [])[:3])
    px, py, ax, ay, ev = e["ahead"]
    ok(ev[:1] == ["start"] and 1.7 <= ax - px <= 2.1 and abs(ay - py) < 0.3, "geht nach rechts: Licht 2 m vor den Füssen (Füsse %.1f / %.1f, Licht %.1f / %.1f)" % (px, py, ax, ay))
    ok(e["flip_early"] > 0, "kurz umgedreht (0.6 s): noch die alte Seite (+%.2f m), kein Flackern" % e["flip_early"])
    fp, fa = e["flip"]
    ok(fa < fp - 1.5, "umgedreht: Licht zeigt auf die andere Seite (Füsse %.1f, Licht %.1f)" % (fp, fa))
    ok(e["towards"][1] < e["towards"][0] - 1.6, "kommt auf die Kamera zu: Licht näher als die Füsse (%s)" % e["towards"])
    cl = e["clamp"]
    ok(cl[0] > cl[1] and cl[2] <= 0.01 and cl[3] >= -0.01, "nahe Person, Kopf-Kamera: das Licht zielt weniger weit, Kopf und Füsse bleiben im Bild (%s)" % cl)
    ok(abs(e["clamp_side"][0]) <= 66.0 * 0.38 + 0.01 and e["clamp_side"][1] > 50, "seitlich weit voraus: die Person bleibt im Bild (%s)" % e["clamp_side"])
    ok("arrived" in e["arrive"][0] and e["arrive"][1] == "arrived" and not e["arrive"][2], "Ziel erreicht: Licht aus (%s)" % e["arrive"][:2])
    ok(e["stay"][0] == [] and e["stay"][1] == "arrived" and not e["stay"][2], "am Ziel 60 s: bleibt aus, kein «steht still» (%s)" % e["stay"][:2])
    ok("farewell" in e["farewell"][0] and e["farewell"][2] and e["farewell"][3] > 0.5, "geht wieder weg: Licht wieder an, voraus (%s)" % e["farewell"])
    ok(e["farewell_gone"] == [["end:gone"], "idle"], "aus dem Bild: Ende (%s)" % e["farewell_gone"])
    ok(e["lost"] == [[], ["end:lost"]], "aus dem Bild 10 s: aus (%s)" % e["lost"])
    ok(e["still"][0][-1:] == ["end:still"] and e["still"][1] == "still", "steht still 30 s: aus (%s)" % e["still"][0][-2:])
    ok(e["block"] == [[], ["start"]], "am selben Ort kein neues Licht, eine andere Person schon (%s)" % e["block"])
    ok(e["max"] == ["end:max"], "höchstens 5 min (%s)" % e["max"])
    ok(e["at_target_start"] == [["start"], "arrived", False], "schon am Ziel beim Einschalten: Licht erst beim Gehen (%s)" % e["at_target_start"])
    a0, a1, an = e["alarm_off"], e["alarm_on"], e["alarm_nozip"]
    ok("person" in a0["sent"] and "warm" in a0["sent"] and "person" in a0["sirens"] and "person" in a0["alerts"], "aus: Alarme wie immer (%s)" % a0)
    ok(not {"person", "warm", "prealarm"} & set(a1["sent"]) and not {"person", "warm", "prealarm"} & set(a1["sirens"])
       and not {"person", "warm", "prealarm"} & set(a1["alerts"]), "an: kein Personen- / Wärme- / Vorwarn-Push, keine Sirene, kein Browser-Alarm (%s)" % a1)
    ok(a1["sent"].count("info") == 1 and any("Gast kommt" in x for x in a1["titles"]), "an: genau ein leiser Push «Gast kommt» (%s)" % a1["titles"])
    ok(a1["sent"].count("tamper") == 2 and {"tamper", "sensor"} <= set(a1["sirens"]) and "noise" in a1["alerts"],
       "an: Sabotage, Diebstahl, Sensor-Sirene und Geräusch wie immer (%s / %s)" % (a1["sent"], a1["sirens"]))
    ok("person" in an["sent"] and "person" in an["sirens"], "ohne Zusatz-ZIP: alter Schutz (Alarm wie immer)")
    ok(e["pir_on"][1] == [] and "tamper" not in e["pir_on"][0], "an: Bewegungsmelder (PIR) vom Gast = kein Alarm, keine Sirene (%s)" % e["pir_on"])
    ok("tamper" in e["door_on"][0] and "sensor" in e["door_on"][1], "an: Tür-Sensor alarmiert wie immer (%s)" % e["door_on"])
    ok("tamper" in e["pir_off"][0] and "sensor" in e["pir_off"][1], "aus: Bewegungsmelder alarmiert wie immer (%s)" % e["pir_off"])
    ok(e["deter_on"] == [] and e["deter_off"] == ["person"], "Abschreckung: an = keine, aus = wie immer (%s / %s)" % (e["deter_on"], e["deter_off"]))
    ok(e["relays"] == ["door", "noise"], "Relais: Person / Wärme fallen weg, Tür / Geräusch bleiben (%s)" % e["relays"])
    lg = e["light_guide"]
    ok(lg[0] and lg[1] and 5 <= lg[2] <= 60, "Führungslicht schaltet das weisse Licht dazu (%s)" % lg)
    if "sos" in e:
        ok(not e["sos"][1] and (e["sos"][0] == [False, True] or e["sos"][2]), "SOS-Lampe geht vor: das Führungslicht hält sich raus (%s)" % e["sos"])
    fi, fo = e["fade_in"], e["fade_out"]
    ok(fi[0] == 0.0 and 0 < fi[1] < 0.15 and fi[1] < fi[2] < fi[3] and fi[3] == 1.0 and fi[4] == 1.0, "weich auf in 3 s, kein Sprung (%s)" % fi)
    ok(fo[0] == 1.0 and 0 < fo[1] < 1 and fo[2] == 0.0, "weich aus in 4 s (%s)" % fo)
    ok(e["animals_on"] == ["animal"] and e["animals_off"] == [], "Schalter «auch Tiere» (%s / %s)" % (e["animals_on"], e["animals_off"]))
    ok(e["person_ground"] is not None and 2 < e["person_ground"][1] < 20, "Person im Bild -> Bodenpunkt %s m" % e["person_ground"])
    h = e["head"]
    ok(h[0] == "guide" and (h[1] != 50.0 or h[2] != 50.0) and h[3] and h[4] and h[5] and not h[6],
       "Kopf: Beweger «guide», Folgen pausiert, Runde wartet, der Kopf fährt (%s)" % h)
    s = e["sim"] or {}
    ok(s.get("on") is True and s.get("phase") == "guide" and "target" in s, "Zustand an den Simulator «guests» (%s)" % s)
    ok(e["until_bad"][0] is False and e["until_ok"][0] and e["until_ok"][1] == "23:59" and e["until_ok"][2], "«bis HH:MM» prüfen / setzen (%s)" % e["until_ok"])
    ok(e["until_end"] == [False, False], "Endzeit vorbei: aus (%s)" % e["until_end"])
    ok(e["sched"] == [True, True] and e["sched_on"] == [True, True] and e["sched_off"] is False, "Zeitplan schaltet «Gäste erwartet» ein und wieder aus")
    ok(e["target"] == [True, 1.5, 6.0], "Ziel als Punkt (%s)" % e["target"])
    ok(e["target_here"][0] is False and "horizon" in e["target_here"][1], "Ziel «wohin der Kopf schaut» am Horizont: abgelehnt (%s)" % e["target_here"][1])
    ok(e["target_here_low"][0] and 2 < e["target_here_low"][1] < 30, "Kopf schaut nach unten: Ziel am Boden (%s)" % e["target_here_low"])
    ok({"on", "active", "phase", "target", "targets", "until", "level", "light"} <= set(e["state"]), "Zustand für Seite und Fenster")
    ok(e["deny"], "nur der Administrator (USER_SETTINGS_DENY, APPKEY_DENY_KEYS)")
    for L, v in e["txt"].items():
        ok(all(v) and (L == "en" or v[0] != "Guests expected"), "%s: %s" % (L, " · ".join(v)))
    ok(e["help"] == [2, True, True, True], "Anleitung in 5 Sprachen (%s)" % e["help"])
    ok(bool(e["selftest"]), "Selbsttest-Funktion: " + str(e["selftest"]))


PW = "gaeste-test-pw-1"


def frei_port():
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        return sk.getsockname()[1]


def teil_b(datei, tmp, bilder):
    print("B) Seite 390 px dunkel (MoveEye Demo)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "light_white_out": "pca:2", "detection_on": False, "track_person": False, "track_motion": False, "patrol": False,
          "ui_simple": False}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    port = frei_port()
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    auth = {"Authorization": "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()}

    def api(path, data=None):
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None,
                                   headers=dict(auth, **{"Content-Type": "application/json"}))
        try:
            with op.open(r, timeout=60) as x:
                return json.loads(x.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read() or b"{}")
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(3)
        r = api("/api/gaeste", {"action": "set", "on": True, "until": "23:30"})
        ok(r.get("ok") and r["gl"]["on"] and r["gl"]["until"] == "23:30", "API: an, bis 23:30 (%s)" % {k: r.get("gl", {}).get(k) for k in ("on", "until", "text")})
        r = api("/api/gaeste", {"action": "target", "kind": "point", "x": 1.0, "y": 7.0, "name": "Zelt"})
        ok(r.get("ok") and r["gl"]["target"]["name"] == "Zelt", "API: Ziel «Zelt» (%s)" % r.get("msg"))
        r = api("/api/gaeste", {"action": "target", "kind": "tap", "cx": 2, "cy": 0.5})
        ok(not r.get("ok") and r.get("msg"), "API: falscher Punkt abgelehnt (%s)" % r.get("msg"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            for name, vp, mob in (("gaeste_karte_pc.png", {"width": 1280, "height": 900}, False), ("gaeste_karte.png", {"width": 390, "height": 844}, True)):
                ctx = br.new_context(viewport=vp, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob,
                                     color_scheme="dark", http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(base + "/protect?open=" + urllib.parse.quote("sec:Guests expected"), wait_until="domcontentloaded")
                pg.wait_for_timeout(2500)
                pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
                found = pg.evaluate("""() => { const s = document.querySelector('[data-view="sec:Guests expected"]'); if (!s) return false;
                    for (let e = s; e; e = e.parentElement) if (e.tagName === 'DETAILS') e.open = true; s.scrollIntoView(); return true; }""")
                ok(found, "%s: Abschnitt «Gäste erwartet» auf der Seite Schutz (?open=sec:Guests expected)" % name)
                try:
                    pg.wait_for_function("""() => { const s = document.querySelector('[data-view="sec:Guests expected"]');
                        if (s) for (let e = s; e; e = e.parentElement) if (e.tagName === 'DETAILS' && !e.open) e.open = true;
                        const g = document.querySelector('#gl-p .gl-st'); return !!(g && g.getClientRects().length); }""", timeout=45000, polling=700)
                    pg.wait_for_timeout(1200)
                    txt = pg.locator("#gl-p").inner_text()
                    ok(txt.startswith("🔦 ") and len(txt.splitlines()[0]) > 4, "%s: Zustand «%s»" % (name, txt.splitlines()[0]))
                    ok("Zelt" in txt, "%s: Ziel «Zelt» in der Liste" % name)
                    pg.evaluate("() => document.getElementById('gl-p').scrollIntoView({block: 'start'})")
                    pg.wait_for_timeout(500)
                    pg.screenshot(path=os.path.join(bilder, name))
                except Exception as ex:
                    ok(False, "%s: Karte fehlt (%s)" % (name, ex))
                if mob:
                    wsc = pg.evaluate("() => document.documentElement.scrollWidth")
                    ok(wsc <= 390, "keine waagrechte Bildlaufleiste bei 390 px (%d)" % wsc)
                    for L, word in (("fr", "Invités attendus"), ("it", "Ospiti attesi"), ("rm", "Giasts spetgads"), ("en", "Guests expected")):
                        pg.evaluate("async l => { try { localStorage.setItem('mw-lang', l); } catch (e) {} await fetch('/api/ui', {method: 'POST', "
                                    "headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': l}})}); }", L)
                        pg.goto(base + "/protect?open=" + urllib.parse.quote("sec:Guests expected"), wait_until="domcontentloaded")
                        try:
                            pg.wait_for_function("w => document.body.textContent.includes(w)", arg=word, timeout=30000)
                            ok(True, "%s: «%s»" % (L, word))
                        except Exception:
                            ok(False, "%s: «%s» fehlt" % (L, word))
                    pg.evaluate("async () => { try { localStorage.setItem('mw-lang', 'de'); } catch (e) {} await fetch('/api/ui', {method: 'POST', "
                                "headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': 'de'}})}); }")
                ok(not errs, "%s: keine JS-Fehler %s" % (name, errs[:3]))
                ctx.close()
            br.close()
        r = api("/api/gaeste", {"action": "set", "on": False})
        ok(r.get("ok") and not r["gl"]["on"] and not r["gl"]["until"], "API: aus (Endzeit weg)")
    finally:
        p.terminate()
        try:
            p.wait(10)
        except Exception:
            p.kill()


def http_json(url, data=None, timeout=10, auth=None):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    h = {"Content-Type": "application/json"}
    if auth:
        h.update(auth)
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=h)
    with op.open(r, timeout=timeout) as x:
        return json.loads(x.read())


def http_bytes(url, timeout=10, auth=None):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    r = urllib.request.Request(url, headers=auth or {})
    with op.open(r, timeout=timeout) as x:
        return x.read()


def bild_klein(pfad, breite=960):
    """smaller for the log: at most 960 px wide, JPEG 78 (cv2 is there wherever MoveEye runs)"""
    try:
        import cv2
        im = cv2.imread(pfad)
        if im is not None:
            if im.shape[1] > breite:
                im = cv2.resize(im, (breite, int(im.shape[0] * breite / im.shape[1])), interpolation=cv2.INTER_AREA)
            ok_, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 78])
            if ok_:
                return buf.tobytes()
    except Exception:
        pass
    return open(pfad, "rb").read()


def bild_ins_log(pfad):
    """the HP artifact cannot always be fetched: the picture also goes into the job log (base64, lines «GLBILD name i/n …»;
    werkzeuge/gaeste_licht_test.py --bilder-aus-log LOG puts them together again). Simulator pictures only - nothing private."""
    try:
        b = base64.b64encode(bild_klein(pfad)).decode()
    except OSError:
        return
    name, n = os.path.basename(pfad), (len(b) + 2999) // 3000
    for k in range(n):
        print("GLBILD %s %d/%d %s" % (name, k + 1, n, b[k * 3000:(k + 1) * 3000]), flush=True)


def bilder_aus_log(log, ziel):
    parts = {}
    for ln in open(log, encoding="utf-8", errors="replace"):
        m = re.search(r"GLBILD (\S+) (\d+)/(\d+) (\S+)", ln)
        if m:
            d = parts.setdefault(m.group(1), {})
            if int(m.group(2)) == 1 or (d and next(iter(d.values()))[0] != int(m.group(3))):
                d.clear()                                      # a new copy of the picture starts
            d[int(m.group(2))] = (int(m.group(3)), m.group(4))
    os.makedirs(ziel, exist_ok=True)
    for name, d in parts.items():
        n = next(iter(d.values()))[0]
        if len(d) == n:
            open(os.path.join(ziel, name), "wb").write(base64.b64decode("".join(d[k][1] for k in range(1, n + 1))))
            print("  %s (%d Teile)" % (name, n))
        else:
            print("  %s unvollständig (%d von %d)" % (name, len(d), n))


def _sim_start(godot, senv, sp, res, logp):
    return subprocess.Popen([godot, "--path", os.path.join(REPO, "simulator3d"), "--resolution", res, "--", "--no-update", "--no-tour", "--stream",
                             "--solo", "--scene", "camping", "--hour", "22.5", "--port", str(sp), "--quality", "lite"],
                            env=senv, stdout=open(logp, "a"), stderr=subprocess.STDOUT, start_new_session=True)


def _verbunden(web, auth, secs):
    t_end = time.time() + secs
    while time.time() < t_end:
        try:
            s = http_json(web + "/api/state", timeout=4, auth=auth)["state"]
            if str(s.get("source_status", "")).startswith("connected") and float(s.get("fps") or 0) > 0:
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def teil_c(datei, tmp, bilder, godot):
    """Simulator + MoveEye: night, «Gäste erwartet» with the tent as target, the scenario - pictures (heavy: HP route)"""
    print("C) Simulator-Nacht mit Gast zum Zelt (Godot %s)" % godot, flush=True)
    os.makedirs(bilder, exist_ok=True)
    procs = []
    env = dict(os.environ)
    sim_p = None
    try:
        if not env.get("DISPLAY"):
            disp = ":%d" % (70 + os.getpid() % 9)
            procs.append(subprocess.Popen(["Xvfb", disp, "-screen", "0", "1280x900x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                          start_new_session=True))
            env["DISPLAY"] = disp
            time.sleep(2)
        sp, mp = frei_port(), frei_port()
        senv = dict(env, HOME=os.path.join(tmp, "simhome")); os.makedirs(senv["HOME"])
        slog = os.path.join(tmp, "sim.log")
        sim_p = _sim_start(godot, senv, sp, "1280x720", slog)
        cfg = os.path.join(tmp, "mwc"); os.makedirs(cfg)
        st = {"sim_on": True, "source": "sim:0", "thermal_source": "sim:thermal", "sim_url": "http://127.0.0.1:%d" % sp, "sim_auto": False,
              "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
              "setup_done": True, "news_popup": False, "theme": "dark", "thermal_on": False, "patrol": False, "track_person": True,
              "gl_on": True, "gl_dark_only": True, "gl_pct": 70, "light_ir": "auto", "light_ir_auto": "dark"}   # IR as on a real night
        json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
        ki = os.path.join(env.get("CACHE", ""), "ki") if env.get("CACHE") else ""
        print("  KI-Modell: %s" % (ki if ki and os.path.isdir(ki) else "keins (Bewegung + Wärmebild)"), flush=True)
        if ki and os.path.isdir(ki):
            os.makedirs(os.path.join(cfg, "models"), exist_ok=True)
            for fn in os.listdir(ki):
                shutil.copy(os.path.join(ki, fn), os.path.join(cfg, "models", fn))
        mlog = open(os.path.join(tmp, "mw.log"), "w")
        procs.append(subprocess.Popen([sys.executable, datei, "--headless", "--port", str(mp), "--bind", "127.0.0.1", "--config", cfg,
                                       "--web-password", PW], env=env, stdout=mlog, stderr=subprocess.STDOUT, cwd=tmp, start_new_session=True))
        sim, web = "http://127.0.0.1:%d" % sp, "http://127.0.0.1:%d" % mp
        auth = {"Authorization": "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()}
        okc = _verbunden(web, auth, 420)
        ok(okc, "Simulator und MoveEye verbunden")
        if not okc:
            print(open(slog, errors="replace").read()[-2500:])
            print(open(os.path.join(tmp, "mw.log"), errors="replace").read()[-2500:])
            return
        info = {}
        for _i in range(20):                                   # MoveEye's state reaches the simulator: guests come by themselves
            info = http_json(sim + "/control", {"action": "gaeste", "do": "info"})
            if info.get("mw_on") and int(info.get("started") or 0) >= 1:
                break
            time.sleep(2)
        ok(info.get("ok") and info.get("mw_on"), "Simulator sieht «Gäste erwartet» von MoveEye (%s)" % info)
        ok(int(info.get("started") or 0) >= 1, "Gäste kommen von selbst, weil MoveEye «Gäste erwartet» an hat")
        tx, ty = info["tent_mw"]
        http_json(sim + "/control", {"action": "gaeste", "do": "look"})
        r = http_json(web + "/api/gaeste", {"action": "target", "kind": "point", "x": tx, "y": ty, "name": "Zelt"}, auth=auth)
        ok(r.get("ok"), "Ziel = Zelt des Simulators (%.1f / %.1f m)" % (tx, ty))
        shots, phases, t0, meas = [], [], time.time(), []
        want = {"guide": "gaeste_sim_fuehrt.jpg", "arrived": "gaeste_sim_am_zelt.jpg", "farewell": "gaeste_sim_abschied.jpg"}
        while time.time() - t0 < 480 and len(shots) < 3:
            try:
                g = http_json(web + "/api/gaeste", auth=auth)
            except Exception:
                time.sleep(1); continue
            ph = g.get("phase")
            phases.append((round(time.time() - t0), ph, g.get("light"), round(float(g.get("pct") or 0)), g.get("pos"), g.get("aim"), g.get("seen_s"),
                           (g.get("last_end") or {}).get("why")))
            if ph in want and want[ph] not in shots and (ph != "guide" or (g.get("light") and float(g.get("pct") or 0) > 40)):
                if ph in ("guide", "farewell"):                   # the markers: red = axis of the spot on the ground, green = MoveEye's aim
                    http_json(sim + "/control", {"action": "gaeste", "do": "look"})
                    http_json(sim + "/control", {"action": "gaeste", "do": "debug", "on": True})
                    for _k in range(5):
                        time.sleep(0.5)
                        d_ = http_json(sim + "/control", {"action": "gaeste", "do": "info"})
                        meas.append(dict(d_.get("dbg") or {}, phase=ph, spot_deg=d_.get("spot_deg")))
                    dn = "gaeste_sim_debug_%s.jpg" % ph
                    open(os.path.join(bilder, dn), "wb").write(http_bytes(sim + "/view.jpg", 20))
                    bild_ins_log(os.path.join(bilder, dn))
                    http_json(sim + "/control", {"action": "gaeste", "do": "debug", "on": False})
                time.sleep(1.5 if ph != "arrived" else 4.0)
                http_json(sim + "/control", {"action": "gaeste", "do": "look"})
                time.sleep(0.6)
                open(os.path.join(bilder, want[ph]), "wb").write(http_bytes(sim + "/view.jpg", 20))
                try:                                                   # MoveEye's head camera: the guest in the light
                    open(os.path.join(bilder, want[ph].replace(".jpg", "_kopf.jpg")), "wb").write(http_bytes(web + "/api/frame.jpg", 20, auth))
                except Exception as ex:
                    print("  Kopf-Bild: %s" % ex, flush=True)
                shots.append(want[ph])
                bild_ins_log(os.path.join(bilder, want[ph]))            # at once (the artifact cannot always be fetched)
                bild_ins_log(os.path.join(bilder, want[ph].replace(".jpg", "_kopf.jpg")))
            time.sleep(0.8)
        print("  Ziel %.1f / %.1f m · Verlauf (s, Phase, Licht, %%, Gast, Licht-Ziel, ungesehen s, Ende):" % (tx, ty), flush=True)
        idle = [x for x in phases if x[1] == "idle"]
        for x in [x for x in phases if x[1] != "idle" or x in idle[::15]][:120]:
            print("   ", x, flush=True)
        print("  Marken (Lichtachse am Boden / Zielpunkt MoveEye / Gast, m vom Gerät):", flush=True)
        for m_ in meas:
            print("   ", m_, flush=True)
        errs_ = sorted(float(m_["err_m"]) for m_ in meas if "err_m" in m_)
        ok(bool(errs_) and errs_[len(errs_) // 2] < 1.0, "Licht trifft den Zielpunkt von MoveEye am Boden (Abweichung Median %s m)" % (errs_[len(errs_) // 2] if errs_ else "–"))
        ahead = []
        for m_ in meas:
            if "aim_mw" in m_ and "guest_mw" in m_:
                ahead.append(math.hypot(m_["aim_mw"][0] - m_["guest_mw"][0], m_["aim_mw"][1] - m_["guest_mw"][1]))
        ok(bool(ahead), "Zielpunkt vor dem Gast: %s m (2 m, weniger wenn der Gast sonst aus dem Bild liefe)" % [round(x, 1) for x in ahead])
        ok(any(abs(float(m_.get("spot_deg") or 0) - 13.0) < 0.5 for m_ in meas), "Führungslicht als schmaler Lichtkegel (13°)")
        ok("gaeste_sim_fuehrt.jpg" in shots, "Bild: Gast wird zum Zelt geführt (Licht vor den Füssen)")
        ok("gaeste_sim_am_zelt.jpg" in shots, "Bild: Gast am Zelt, Licht aus")
        ok("gaeste_sim_abschied.jpg" in shots, "Bild: Abschied - Licht leuchtet wieder voraus")
        g = http_json(web + "/api/gaeste", auth=auth)
        ok(int(g.get("notes") or 0) >= 1 and any(p[2] for p in phases), "«Gast kommt» notiert, Führungslicht war an")
        try:
            # the phone: the simulator window upright (390 x 844, its phone layout) - the same night, a guest guided to the tent
            try:
                os.killpg(sim_p.pid, signal.SIGTERM); sim_p.wait(20)
            except Exception:
                pass
            time.sleep(3)
            sim_p = _sim_start(godot, senv, sp, "390x844", slog)
            up = False
            for _i in range(120):                                  # the simulator answers again, MoveEye is connected again
                try:
                    up = bool(http_json(sim + "/control", {"action": "gaeste", "do": "info"}, timeout=4).get("ok"))
                except Exception:
                    up = False
                if up:
                    break
                time.sleep(2)
            ok(up and _verbunden(web, auth, 300), "Simulator hochkant neu gestartet, wieder verbunden")
            time.sleep(10)
            http_json(sim + "/control", {"action": "gaeste", "do": "start", "n": 1, "stay": 25}, timeout=20)
            http_json(sim + "/control", {"action": "gaeste", "do": "look"}, timeout=20)
            t1, got = time.time(), False
            while time.time() - t1 < 240 and not got:
                try:
                    g = http_json(web + "/api/gaeste", auth=auth)
                except Exception:
                    time.sleep(1); continue
                if g.get("phase") in ("guide", "farewell") and g.get("light") and float(g.get("pct") or 0) > 40:
                    time.sleep(1.5)
                    open(os.path.join(bilder, "gaeste_sim_handy.jpg"), "wb").write(http_bytes(sim + "/view.jpg", 20))
                    bild_ins_log(os.path.join(bilder, "gaeste_sim_handy.jpg"))
                    got = True
                time.sleep(0.8)
            ok(got, "Bild: Handy (Simulator hochkant 390 × 844), Gast im Führungslicht")
        except Exception as ex:
            ok(False, "Handy-Bild: %s" % ex)
        hits = []
        for wurzel, _d, files in os.walk(cfg):
            for fn in files:
                if fn.endswith((".log", ".jsonl", ".txt")):
                    try:
                        for ln in open(os.path.join(wurzel, fn), errors="replace"):
                            if "Guide light" in ln or "Guests expected" in ln or "guest" in ln.lower():
                                hits.append(ln.strip()[:220])
                    except OSError:
                        pass
        for fn in sorted(os.listdir(bilder)):                    # once more at the end (a line of the log may get lost)
            if fn.startswith("gaeste_sim_") and fn.endswith(".jpg"):
                bild_ins_log(os.path.join(bilder, fn))
        print("  MoveEye-Protokoll (Führungslicht, letzte 40):", flush=True)
        for ln in hits[-40:]:
            print("   ", ln, flush=True)
    finally:
        for pr in [sim_p] + list(reversed(procs)):
            try:
                os.killpg(pr.pid, signal.SIGTERM)
            except (OSError, AttributeError):
                pass
        time.sleep(2)
        for pr in [sim_p] + procs:
            try:
                os.killpg(pr.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--sim", default="", help="Godot 4.3 (oder «env»: $GODOT) - Simulator-Bilder")
    ap.add_argument("--nur-sim", action="store_true", help="nur Teil C")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "gaeste_bilder"))
    ap.add_argument("--bilder-aus-log", default="", help="Job-Protokoll des HP: die Bilder (GLBILD-Zeilen) nach --bilder")
    a = ap.parse_args()
    if a.bilder_aus_log:
        bilder_aus_log(a.bilder_aus_log, a.bilder)
        return 0
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Gäste-erwartet-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_gaeste_")
    try:
        if not a.nur_sim:
            teil_a(datei, tmp)
            if a.browser:
                teil_b(datei, tmp, a.bilder)
        if a.sim:
            g = os.environ.get("GODOT", "") if a.sim == "env" else a.sim
            if not g:
                ok(False, "Godot fehlt ($GODOT)")
            else:
                teil_c(datei, tmp, a.bilder, g)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Gäste-erwartet-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
