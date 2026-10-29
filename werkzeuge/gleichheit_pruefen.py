#!/usr/bin/env python3
"""Vorher/nachher-Vergleich beim Zusammenführen von Wrappern (2.98.18): schreibt das Ergebnis der zusammengeführten Funktionen
(apply_settings, health_check, set_cfg, text_choice_pairs, tools_state / tools_cfg, _tunea_autotune_base) und die Listen
TOGGLES / SLIDERS / TEXTS / SECTIONS / TK_GROUPS / CFG als JSON. Zwei Dateien müssen Byte für Byte gleich sein:

  python3 werkzeuge/gleichheit_pruefen.py ALTE_DATEI.py vorher.json
  python3 werkzeuge/gleichheit_pruefen.py webcam_bewegung_X_Y_Z.py nachher.json
  cmp vorher.json nachher.json

Startet nichts (kein Fenster, keine Kamera); Einstellungen in /tmp/claude-0/code_cmp_home bzw. MW_CMP_HOME."""
import copy, json, os, sys, tempfile
path, out = sys.argv[1], sys.argv[2]
import shutil
H = os.environ.get("MW_CMP_HOME") or os.path.join(tempfile.gettempdir(), "mw_cmp_home"); shutil.rmtree(H, ignore_errors=True); os.makedirs(H)
os.environ["MOTIONWATCH_HOME"] = H
ns = {"__name__": "mw_check", "__file__": os.path.abspath(path)}
exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
LOG = []
ns["log_event"] = lambda kind, msg, *a, **k: LOG.append([kind, msg])
PUSH = []
ns["simupd_push"] = lambda on: PUSH.append(on)
R = {}
R["TOGGLES"] = list(ns["TOGGLES"]); R["SLIDERS"] = list(ns["SLIDERS"]); R["TEXTS"] = list(ns["TEXTS"]); R["SECTIONS"] = list(ns["SECTIONS"])
R["TK_GROUPS"] = ns["TK_GROUPS"]; R["TEXT_SPECS"] = ns["TEXT_SPECS"]; R["SIMPLE_KEYS"] = sorted(ns["SIMPLE_KEYS"])
R["CFG"] = copy.deepcopy(ns["CFG"]); R["DEFAULTS"] = copy.deepcopy(ns["DEFAULTS"])
R["web_specs"] = ns["web_specs"]()
R["enum"] = {k: ns["text_choice_pairs"](k) for _s, k, _l, kind, _e in ns["TEXTS"] if kind == "enum"}
CFG = ns["CFG"]; base = copy.deepcopy(CFG)
def reset():
    CFG.clear(); CFG.update(copy.deepcopy(base))
for lang in ("de", "en", "fr"):
    h = ns["health_check"](lang)
    for x in h["items"]:
        if x["id"] == "clock":
            x["text"] = "<time>"                     # the clock only
    R["health_" + lang] = h
sc = []
for sim_on in (False, True):
    ns["sim_ready"] = lambda: True
    for key, val in (("patrol", True), ("patrol", False), ("sim_autoupd", False), ("sim_autoupd", True), ("sensitivity", 33.3),
                     ("sensitivity", "x"), ("min_area", 1e12), ("nokey", 1), ("record", 1)):
        reset(); CFG["sim_on"] = sim_on; PUSH.clear()
        import threading, time
        r = ns["set_cfg"](key, val); time.sleep(0.05)
        sc.append([sim_on, key, repr(val), list(r), repr(CFG.get(key)), list(PUSH)])
R["set_cfg"] = sc
reset()
R["tools_state"] = {k: v for k, v in ns["tools_state"]().items() if k not in ("power",)}
R["tools_state_cfg_keys"] = list(ns["tools_state"]()["cfg"].keys())
tc = []
for key, val, mac in (("presence_back", "off", None), ("presence_back", "bad", None), ("presence_back", "none", None), ("presence_auto", 1, None),
                      ("presence_gone_min", 999, None), ("presence_macs", True, "AA:bb:cc:dd:ee:ff"), ("presence_macs", True, "zz"), ("x", 1, None),
                      ("bt_tracker_min", "q", None)):
    reset()
    r = ns["tools_cfg"](key, val, mac)
    tc.append([key, repr(val), list(r), repr(CFG.get(key))])
R["tools_cfg"] = tc
ap = []
for data in ({"cfg": {"presence_auto": True, "back_ask": True, "simweek_on": False, "mode": "night", "sensitivity": 70}},
             {"cfg": {"back_ask": True, "camping": True, "camping_prev": {"armed": True, "_seq": 5.0}, "light_white_auto": False, "light_white": "auto"}},
             {"cfg": {"presence_back": "none", "weekrep_sim": False, "simweek_on": True}}, {"cfg": {}}, ["not", "a", "dict"], {"cfg": "x"}):
    reset(); LOG.clear()
    try:
        r = ns["apply_settings"](data); err = None
    except Exception as e:
        r = None; err = repr(e)
    c = {k: v for k, v in CFG.items() if k not in ("mode_since",)}
    ap.append({"ret": r, "err": err, "cfg_changed": {k: v for k, v in c.items() if base.get(k) != v}, "log": [l for l in LOG]})
R["apply_settings"] = ap
reset(); LOG.clear()
CFG.update(min_area=1000, sensitivity=50, speed_consistency=0.5)
ns["_tunea_autotune_base"]()
R["tunea"] = {k: v for k, v in CFG["auto_tune_base"].items() if k != "t"}
R["tunea_log"] = LOG[:]
json.dump(R, open(out, "w"), indent=1, sort_keys=False, default=repr, ensure_ascii=False)
print("written", out)
