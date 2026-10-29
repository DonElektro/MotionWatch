#@ MoveEye – Teil 147: Eine Sperre für Simulator-Aufgaben mit dem Simulator zusammen; blinde Flecken, die im Simulator gestartet wurden. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Daniel, 29.10.2026): MoveEye had simtask_busy (141), the simulator busy_with (main.gd). Now they know each other:
#  * MoveEye asks the simulator every 3 s ({"action": "busy"} -> busy_with("")). A test run, the test bench, training
#    pictures, blind spots … started in the simulator window lock MoveEye's own starts with the same message
#    «The simulator is busy: …» (simtask_busy in 141 asks sim_busy_remote()).
#  * MoveEye tells the simulator what it does itself (sim_state: "simtask", "simtask_de"); the simulator refuses its own
#    starts then (busy_with in main.gd: «Störfall-Übung (von MoveEye)»).
#  * Blind spots started in the simulator («Testen» card): MoveEye follows them like its own (BLIND / _blind_wait in 143),
#    so the map in MoveEye shows the result, whoever started it. Older simulators without «busy»: blindmap info is asked.
# ----------------------------------------------------------------------------
SIMBUSY = {"w": "", "t": 0.0, "ok": None, "seen_blind": 0, "poll_t": 0.0, "started": False}
SIM_BUSY_NAMES = {"Testlauf": "test run", "Prüfstand": "test bench", "Trainingsbilder": "training pictures", "Blinde Flecken": "blind spots",
                  "Fehlalarm nachstellen": "false alarm learning", "Wiedergabe": "playback of a recording"}


def simtask_local():
    """what MoveEye itself does with the simulator right now ('' = nothing) - without asking the simulator"""
    for name, busy in (("test run", TESTOPT.get("busy")), ("training night", TRAIN.get("busy")), ("A/B comparison", ABT.get("busy")),
                       ("drill", DRILL.get("busy"))):
        if busy:
            return name
    for name, ref in (("blind spots", "BLIND"), ("false alarm learning", "FALEARN"), ("automatic thresholds", "AUTOTH"), ("demo", "DEMO_RUN")):
        d = globals().get(ref)
        if isinstance(d, dict) and d.get("busy") and not (ref == "BLIND" and d.get("ext")):
            return name
    try:
        if PROTECT["test"]["busy"]:
            return "protection test"
    except (NameError, KeyError, TypeError):
        pass
    return ""


def sim_busy_remote():
    """'' or the name of what the simulator does that MoveEye did not start (for simtask_busy). While MoveEye runs a task
    itself, the simulator being busy is that task - not counted."""
    if not CFG.get("sim_on") or simtask_local():
        return ""
    if time.time() - SIMBUSY["t"] > 30:
        return ""
    w = str(SIMBUSY["w"] or "")
    if not w or w == "Spielrunde" or "MoveEye" in w:          # the game round: sim_game_running() in 141
        return ""
    if w == "Blinde Flecken" and BLIND.get("busy"):
        return "blind spots"
    return tr(SIM_BUSY_NAMES.get(w, w)) + " (" + tr("started in the simulator") + ")"


def _simbusy_adopt_blind():
    """blind spots run in the simulator, MoveEye does not follow them yet -> follow them (result in BLIND['last'])"""
    if BLIND.get("busy"):
        SIMBUSY["seen_blind"] = 0
        return
    SIMBUSY["seen_blind"] += 1
    if SIMBUSY["seen_blind"] < 2:                              # twice in a row: not a start of MoveEye that is just coming
        return
    SIMBUSY["seen_blind"] = 0
    BLIND.update(busy=True, kind="map", ext=True)
    log_event("sys", "Blind spots started in the simulator - MoveEye draws the map")

    def run():
        try:
            _blind_wait()
        finally:
            BLIND["ext"] = False
    threading.Thread(target=run, daemon=True, name="blindmap-ext").start()


def _sim_reachable():
    """looser than sim_ready(): a slow simulator PC may miss a few frames - the lock still counts (30 s)"""
    return bool(CFG.get("sim_on")) and SIM.get("ok") and time.time() - SIM.get("t", 0) < 30


def simbusy_poll():
    if not _sim_reachable():
        SIMBUSY["seen_blind"] = 0
        return
    if SIMBUSY["ok"] is not False:
        try:
            r = sim_control({"action": "busy"})
        except Exception:
            return
        if r.get("ok") and "busy" in r:
            SIMBUSY.update(w=str(r.get("busy") or ""), t=time.time(), ok=True)
        elif r.get("error") == "unknown action":
            SIMBUSY.update(ok=False, poll_t=time.time())
            return
        blind = SIMBUSY["w"] == "Blinde Flecken"
    else:                                                      # an older simulator: only the blind spots
        if time.time() - SIMBUSY["poll_t"] > 600:
            SIMBUSY["ok"] = None                               # updated meanwhile? ask again
        try:
            r = sim_control({"action": "blindmap", "do": "info"})
        except Exception:
            return
        blind = bool(r.get("busy"))
    if blind:
        _simbusy_adopt_blind()
    else:
        SIMBUSY["seen_blind"] = 0


def simbusy_loop():
    while True:
        time.sleep(3.0)
        try:
            simbusy_poll()
            simupd_sync()
        except Exception as e:
            print(f"simulator lock: {e}")


def _simbusy_waiter():
    for _ in range(600):
        time.sleep(1.0)
        if WATCH_REF.get("w") is not None:
            threading.Thread(target=simbusy_loop, daemon=True, name="simbusy").start()
            return


threading.Thread(target=_simbusy_waiter, daemon=True, name="simbusy-wait").start()

