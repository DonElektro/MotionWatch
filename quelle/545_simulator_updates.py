#@ MoveEye – Teil 545: Simulator-Updates: ein Besitzer (die Einstellung «Neue Versionen» des Simulators), MoveEye zeigt und stellt sie. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- 2.98.13: simulator updates have one owner - the simulator's own setting «Neue Versionen» (update_mode) -----------------
# MoveEye's switch «Update the simulator by itself» (sim_autoupd, web and window) shows and sets that setting through
# /control when the connected simulator has it; MoveEye then no longer presses «update_now» itself (300). For the Python
# simulator on the Pi (installed from inside MoveEye) the switch keeps working as before.
SIMUPD = {"t": 0.0, "mode": None, "synced": None}


def simupd_mode():
    """'off' | 'auto' | 'dev' of the connected simulator, None = it has no such setting (or not reachable)"""
    try:
        d = sim_control(None)
    except Exception:
        return None
    for c in d.get("controls") or []:
        if isinstance(c, dict) and c.get("id") == "update_mode":
            return str(c.get("value") or "off")
    return None


def simupd_push(on):
    """MoveEye's switch was changed: set the simulator's setting (keeps «dev» when it is already on)"""
    m = SIMUPD["mode"] if SIMUPD["mode"] is not None else simupd_mode()
    if m is None:
        return False
    want = ("dev" if m == "dev" else "auto") if on else "off"
    if want != m:
        try:
            sim_control({"action": "set", "id": "update_mode", "value": want})
        except Exception:
            return False
        log_event("sys", f"Simulator updates: {want} (set in MoveEye)")
    SIMUPD.update(mode=want, synced=bool(on), t=time.time())
    return True


def simupd_sync():
    """every 15 s while connected: whoever changed last wins - MoveEye's switch (web / window) or the simulator window"""
    if not sim_ready() or time.time() - SIMUPD["t"] < 15:
        return
    SIMUPD["t"] = time.time()
    m = simupd_mode()
    SIMUPD["mode"] = m
    if m is None:
        SIMUPD["synced"] = None
        return
    sim_on_ = m != "off"
    mine = bool(CFG.get("sim_autoupd", True))
    if SIMUPD["synced"] is None:                               # just connected: the simulator owns the setting
        SIMUPD["synced"] = sim_on_
        if mine != sim_on_:
            CFG["sim_autoupd"] = sim_on_; save_settings()
        return
    if mine != SIMUPD["synced"]:                               # changed in MoveEye (window) since the last look
        simupd_push(mine)
    elif sim_on_ != SIMUPD["synced"]:                          # changed in the simulator window
        SIMUPD["synced"] = sim_on_
        CFG["sim_autoupd"] = sim_on_; save_settings()


def sim_owns_updates():
    return SIMUPD.get("mode") is not None


_set_cfg_base = set_cfg


def set_cfg(key, value):
    ok, msg = _set_cfg_base(key, value)
    if ok and key == "sim_autoupd" and CFG.get("sim_on") and sim_ready():
        threading.Thread(target=simupd_push, args=(bool(CFG["sim_autoupd"]),), daemon=True, name="simupd").start()
    return ok, msg
