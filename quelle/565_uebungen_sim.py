#@ MoveEye – Teil 565: die Übungen «Akku leer» und «WLAN / Internet weg» (141) spielen mit den Werten des Simulators (Aufräumen 2, Daniel 30.10.2026). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der 3D-Simulator rechnet den USV-HAT, «WLAN weg / Internet weg» und die Hitze selbst (power.gd, «battery», «net»,
# «ambient_c»). Darum gibt es jetzt EINEN Weg: ist der Simulator verbunden und simuliert er den Wert, stellen die Übungen
# nur seine Regler (batt_level / batt_mains, net_internet_off; die Hitze / Kälte stellte schon immer «ambient»), MoveEye
# liest die Werte wie sonst auch (285 sim_battery_tick, sim_net_down) - gleiche Texte, gleiche Meldungen wie bisher.
# Ohne diese Werte (älterer Simulator, Akku nicht simuliert) bleiben die eigenen Übungswerte von 141 (Rückfall).
# Am Ende kommen die Regler zurück, wie sie waren; «Netzstrom zurück» meldet der Simulator selbst (Netzteil kurz an).
# ----------------------------------------------------------------------------
DRILL_SIM = {"batt": None, "net": None, "pct": None, "t": 0.0}


def _drill_sim_set(cid, value):
    try:
        r = sim_control({"action": "set", "id": cid, "value": value})
        return isinstance(r, dict) and r.get("ok", True) is not False
    except Exception:
        return False


_drill_start_141 = drill_start


# wraps: drill_start
def drill_start(kind):                                    # + 565: battery / net through the simulator values
    DRILL_SIM.update(batt=None, net=None, pct=None, t=0.0)
    sb = sim_sensor("battery") if kind == "battery" else None
    sn = sim_sensor("net") if kind == "net" else None
    ok, err = _drill_start_141(kind)
    if not ok:
        return ok, err
    if sb is not None:
        DRILL_SIM["batt"] = {"pct": int(sb.get("pct") or 60), "mains": bool(sb.get("mains"))}
        _drill_sim_set("batt_mains", False)               # the cable is pulled: the next tick tells «power cut» (141 sets _on_batt False)
        _drill_sim_set("batt_level", 60)
        DRILL_SIM["pct"] = 60; DRILL_SIM["t"] = time.time()
    if sn is not None and sn.get("wifi") is not False and sn.get("internet") is not False:
        if _drill_sim_set("net_internet_off", True):      # the simulator plays «Internet weg» (MoveEye: sim_net_down)
            DRILL_SIM["net"] = True
            time.sleep(0.5)
            try:
                WATCH_REF["w"].netmon.recheck = True        # check at once with the new simulator value
            except Exception:
                pass
    return ok, err


_drill_battery_tick_141 = drill_battery_tick


# wraps: drill_battery_tick
def drill_battery_tick(bm):                               # + 565: 60 -> 4 % in the simulator, MoveEye reads it as usual
    sb = sim_sensor("battery")
    if DRILL_SIM["batt"] is None or sb is None:
        return _drill_battery_tick_141(bm)                 # without simulator values: the own drill values (fallback)
    if DRILL_SIM["batt"].get("back"):
        return sim_battery_tick(bm, sb)                   # the last seconds: power back / the old values, as the simulator says
    el = time.time() - DRILL["t0"]
    pct = max(4, int(60 - el / DRILL_KINDS["battery"] * 60))
    if pct != DRILL_SIM["pct"]:
        _drill_sim_set("batt_level", pct)
        DRILL_SIM["pct"] = pct
    return sim_battery_tick(bm, sb)                       # (285: during the drill never «the Pi would shut down now»)


_drill_end_later_141 = _drill_end_later


# wraps: _drill_end_later
def _drill_end_later():                                   # + 565: the simulator controls back as they were
    # with the simulator «power back» comes 5 s before the end: its answer takes a moment and the message must still fall
    # into the drill (141 notes reactions until 3 s after the end), as with the own values before
    while time.time() < DRILL["until"] - (5.0 if DRILL_SIM["batt"] is not None and not DRILL_SIM["batt"]["mains"] else 0.0):
        time.sleep(0.5)
    B, N = DRILL_SIM["batt"], DRILL_SIM["net"]
    bm = getattr(WATCH_REF.get("w"), "battmon", None)
    if B is not None:
        B["back"] = True                                   # drill_battery_tick: no more drill values from now on
        if not B["mains"]:
            _drill_sim_set("batt_mains", True)              # «Mains power back» - from the simulator values, like at the end of the drill before
            for _ in range(30):                             # the new value in the answer of the simulator (10 × a second)
                time.sleep(0.1)
                if (sim_sensor("battery") or {}).get("mains"):
                    break
            if bm is not None:
                try:
                    bm.tick()                               # at once (the monitor itself looks only every 10 s): the message is part of the drill
                except Exception:
                    pass
        if bm is not None:
            bm._on_batt = None                              # the way back to the old values is no power cut
        _drill_sim_set("batt_level", B["pct"])
        _drill_sim_set("batt_mains", B["mains"])
        time.sleep(1.0)
        if bm is not None:
            bm._on_batt = None
        while time.time() < DRILL["until"]:
            time.sleep(0.2)
        DRILL_SIM["batt"] = None                           # the normal path again
        if "batt_warned" in (DRILL.get("restore") or {}):
            CFG["batt_warned"] = bool(DRILL["restore"]["batt_warned"])
            DRILL["restore"].pop("batt_warned", None)      # done here (141 would send its own «power back» otherwise)
    if N:
        DRILL_SIM["net"] = None
        _drill_sim_set("net_internet_off", False)
    return _drill_end_later_141()
