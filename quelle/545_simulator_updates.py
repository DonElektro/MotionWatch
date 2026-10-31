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

# set_cfg (540) passes «sim_autoupd» changed on the web page to the simulator (_set_cfg_sim -> simupd_push)


# ---- Versionierung 3.0.0 (Daniel 31.10.2026): MoveEye and the simulator share one number X.Y.Z from 3.0.0 («MoveEye 3.0.0» /
# «MoveEye Sim 3.0.0»). simulator3d/version.json keeps «version» = «3D-(X+2).Y.Z» for old simulators (they only compare that
# field: 3.0.0 would be older than 3D-4.82 for them) and has the real number in «ver». The self-test checks the order of the
# numbers and - in the repository (GitHub) - that version.json, SIM3D and APP_VERSION fit together.
def versionen_selftest():
    order = ["2.98.113", "2.98.114", "3.0.0", "3.0.1", "3.1.0", "3.1.1", "3.10.0", "4.0.0"]
    for a, b in zip(order, order[1:]):
        assert _vkey(a) < _vkey(b), f"MoveEye {a} < {b}"
        assert VFILE_RE.match("webcam_bewegung_%s.py" % b.replace(".", "_")) and VER_RE.match(b), f"file name / number {b}"
    sims = ["3D-4.82", "3D-4.83", "3.0.0", "3.0.1", "3.1.0", "3.10.0", "4.0.0"]
    for a, b in zip(sims, sims[1:]):
        assert sim_vkey(a) < sim_vkey(b), f"simulator {a} < {b}"
    assert sim_vkey("3D-5.0.0") == sim_vkey("3.0.0") == sim_vkey("MoveEye Sim 3.0.0") == (3, 0, 0), "bridge 3D-5.0.0 = 3.0.0"
    assert sim_vlegacy("3.0.0") == "3D-5.0.0" and sim_vlegacy("3.10.2") == "3D-5.10.2" and sim_vlegacy("3D-4.82") == "3D-4.82"
    p = os.path.join(HERE, "simulator3d", "version.json")
    if not os.path.isfile(p):
        return None                                               # on the Pi: no repository next to the program
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    ver, old = str(d.get("ver") or ""), str(d.get("version") or "")
    assert old.startswith("3D-"), f"version.json «version» must stay «3D-…» for old simulators (is {old!r})"
    if ver:
        assert old == sim_vlegacy(ver), f"version.json: «version» {old} must be {sim_vlegacy(ver)} (= {ver} for old simulators)"
        assert SIM3D["version"] in (ver, old), f"SIM3D {SIM3D['version']} does not fit version.json {ver}"
    if _vkey(APP_VERSION) >= (3, 0, 0):
        assert ver == APP_VERSION == SIM3D["version"], f"from 3.0.0 one number: MoveEye {APP_VERSION}, SIM3D {SIM3D['version']}, version.json {ver or old}"
    return f"simulator {ver or old} (old simulators read {old})"


SELFTEST_EXTRA.append(("Version numbers: order, file names, bridge for old simulators (3.0.0)", versionen_selftest))
