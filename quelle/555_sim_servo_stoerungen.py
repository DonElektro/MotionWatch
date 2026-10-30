#@ MoveEye – Teil 555: Servo-Störungen aus dem 3D-Simulator – Unterspannung vom simulierten Akku, PCA9685-Reset, I2C-Fehler und blockierter Servo (Kopf folgt nicht) wie bei echter Hardware erkennen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026, «Servo-Störungen»): in the simulation MoveEye ignored the under-voltage (072 servo_release /
#   servo_safety_tick: «and not sim_on» - the PC has no vcgencmd), the simulator only had play / overshoot («Servos wie
#   echt»). Now the simulator (simint.gd) sends with every answer «servo_sim»:
#     v5 / uv     the 5 V rail of the simulated UPS HAT (sags with a weak battery and the servo current, or «Unterspannung
#                 erzwingen») -> SRV["sim_uv"]: the same lock as the real under-voltage (072: head stops and holds, moves
#                 again by itself 30 s after it is over, fault memory, servo diagnosis counts the minutes)
#     pca_reset   a counter: a new reset is found at the next «MODE1 check» (every 10 s like Hardware._pca_check, 080) ->
#                 latched fault «pca_reset» (outputs off, «Freigeben» needed). After «Freigeben» the driver is set up again
#                 (HW_REINIT) - sim_state servo «reinit» counts it, then the simulated head follows again.
#     i2c         the bus does not answer: every write while the head moves fails (and the 10 s check) -> servo_io_error
#                 (072): 3 in 3 s = latched fault «i2c», like a real broken cable.
#     head_mw     the head of the simulator follows MoveEye right now (not the game guard / patrol of the simulator) - only
#                 then the servo diagnosis compares: MoveEye drives > 6° but the head (head_deg, 350 SIM["head"]) moves < 1°
#                 within 2-4 s = «blocked» (stuck at the end stop) -> fault (needs «Freigeben»). Real MG90S have no position
#                 feedback - on the real device this needs the picture (servo test «steps without a change of the picture»).
# 2.98.53 (Daniel: «Servo blockiert» all the time on 2.98.52 - false alarm): the check compared the range of the planned angle
#   with the range of the head over the last 2-4 s. After 2 s at rest, the first move of a new command (e.g. 7° in 0.3 s) was
#   already «> 6°», while the head angle came from the reply BEFORE (simvals_take runs before 350 stores head_deg, and the
#   simulator answers at most every few 100 ms, slower with «Sparen» / low FPS) -> «blocked» within about one second of any
#   move; the head followed a moment later. Now: setting «sim_servo_block_check» (off by default), the head angle of THIS
#   reply, only fresh replies, and «blocked» only when the planned angle is > 6° away from the head for >= 3 s over >= 4 fresh
#   replies and the head moved < 1° in that time - and not when the planned angle is at / over the end of the simulated head
#   (MoveEye's own limit or the cable limit «pan_limit» of a wide camera on the head).
# Translations: part 557.
# ----------------------------------------------------------------------------
SRV.setdefault("sim_uv", False)
CFG.setdefault("sim_servo_block_check", False)            # 2.98.53: «Blockierten Servo im Simulator melden» (588), off by default
DEFAULTS.setdefault("sim_servo_block_check", False)
SRVSIM = {"pca_seen": None, "pca_due": 0.0, "i2c": False, "reinit": 0, "hist": deque(maxlen=80), "blk_t": 0.0, "v5": None,
          "io_t": 0.0, "last": None}
SRV_FAULT_TEXT.setdefault("blocked", "a servo is blocked - the head does not follow (stuck at the end stop?)")


def simservo_take(rep):
    """350 SimLink.tick (through simvals_take): the faults of the simulated servo driver and power supply"""
    s = rep.get("servo_sim") if isinstance(rep, dict) else None
    if not isinstance(s, dict) or not CFG.get("sim_on"):
        SRV["sim_uv"] = False; SRVSIM["last"] = None
        return
    now = time.time()
    SRVSIM["last"] = s
    try:
        SRVSIM["v5"] = float(s.get("v5")) if s.get("v5") is not None else None
    except (TypeError, ValueError):
        SRVSIM["v5"] = None
    SRV["sim_uv"] = bool(s.get("uv"))
    # PCA9685 reset: found at the next check (every 10 s like the real driver loop)
    pca = int(s.get("pca_reset") or 0)
    if SRVSIM["pca_seen"] is None or pca < SRVSIM["pca_seen"]:
        SRVSIM["pca_seen"] = pca                         # a (re)connect: old resets do not count
    elif pca > SRVSIM["pca_seen"]:
        SRVSIM["pca_seen"] = pca
        SRVSIM["pca_due"] = now + (10.0 - now % 10.0)
    if SRVSIM["pca_due"] and now >= SRVSIM["pca_due"]:
        SRVSIM["pca_due"] = 0.0
        servo_fault("pca_reset", "simulator: MODE1 / prescaler lost (brown-out)")
    # I2C: every write fails while it moves (the real loop writes only changes), the 10 s check fails too
    SRVSIM["i2c"] = bool(s.get("i2c"))
    if SRVSIM["i2c"] and SRV["fault"] not in SRV_FAULT_LOCK:
        if SRV["moving"] or now - SRVSIM["io_t"] >= 10.0:
            SRVSIM["io_t"] = now
            servo_io_error(OSError(121, "Remote I/O error (simulator)"))
    elif not SRVSIM["i2c"] and SRV["io_err"] and now - SRV["io_t"] > 3.0:
        servo_io_ok()
    # the diagnosis: does the head follow? (the head angle of this reply - 350 stores it in SIM["head"] only afterwards)
    _simservo_block_check(s, now, rep.get("head_deg") if isinstance(rep, dict) else None)


SIMBLK_GAP, SIMBLK_STILL, SIMBLK_SECS, SIMBLK_N, SIMBLK_FRESH = 6.0, 1.0, 3.0, 4, 1.5


def _simservo_limit(axis):
    """how far the simulated head can turn on this axis (degrees from the middle)"""
    try:
        lim = min(servo_half(axis), float(CFG["pan_limit" if axis == "pan" else "tilt_limit"]))   # MoveEye's own end (072 limits_deg)
    except (KeyError, TypeError, ValueError):
        lim = servo_half(axis)
    if axis == "pan":
        try:
            pl = (weit_sim_cam() or {}).get("pan_limit") if "weit_sim_cam" in globals() else None
            if pl:
                lim = min(lim, float(pl))                  # a wide camera on the head: the cable stops the head earlier
        except (TypeError, ValueError):
            pass
    return lim


def _simservo_block_check(s, now, h=None, t_rep=None):
    """«blocked»: the planned angle stays > 6° away from the head of the simulator for >= 3 s (>= 4 fresh replies) and the
    head does not move (< 1°). Only with the setting «sim_servo_block_check» (off by default, 2.98.53)."""
    H = SRVSIM["hist"]
    if h is None:
        h = SIM.get("head")
    if (not CFG.get("sim_servo_block_check", False) or not isinstance(h, list) or len(h) < 2 or not s.get("head_mw", True)
            or s.get("pca_hold") or s.get("i2c") or s.get("uv") or servo_blocked() or SIM.get("follower")):
        H.clear(); return
    t_rep = now if t_rep is None else t_rep
    if now - t_rep > SIMBLK_FRESH:                        # an old answer (busy PC, «Sparen»): not a sample
        return
    try:
        cp, ct = servo_pos_deg()
        H.append((now, cp, float(h[0]), ct, float(h[1])))
    except (TypeError, ValueError):
        return
    while H and now - H[0][0] > 8.0:
        H.popleft()
    if now - SRVSIM["blk_t"] < 10.0:
        return
    for axis, ci, hi in (("pan", 1, 2), ("tilt", 3, 4)):
        run = []                                           # the newest replies in a row with a big gap (planned <-> head)
        for x in reversed(H):
            if abs(x[ci] - x[hi]) <= SIMBLK_GAP:
                break
            run.append(x)
        if len(run) < SIMBLK_N or run[0][0] - run[-1][0] < SIMBLK_SECS:
            continue
        if max(x[hi] for x in run) - min(x[hi] for x in run) >= SIMBLK_STILL:
            continue                                       # the head moves - only slower than planned
        lim = _simservo_limit(axis)
        if abs(run[0][ci]) >= lim - 1.0 or abs(run[0][hi]) >= lim - 1.0:
            continue                                       # at the end of the simulated head: not a fault of the servo
        SRVSIM["blk_t"] = now
        servo_fault("blocked", f"{axis}: {tr('Pan' if axis == 'pan' else 'Tilt', 'en')} {run[-1][ci]:.0f}° → {run[0][ci]:.0f}°, "
                               f"head stays at {run[0][hi]:.0f}°")
        H.clear()
        return


_simvals_take_552 = simvals_take


def simvals_take(rep):                                    # + 555: servo faults and the 5 V rail of the simulator
    _simvals_take_552(rep)
    try:
        simservo_take(rep)
    except Exception as e:
        log_event("servo", f"Simulator servo values: {type(e).__name__}: {e}"[:160])


_servo_release_072 = servo_release


def servo_release(by="web"):                              # + 555: count a new set-up of the driver (the simulator waits for it)
    fault = SRV["fault"]
    ok, err = _servo_release_072(by)
    if ok and fault in SRV_FAULT_LOCK:
        SRVSIM["reinit"] += 1
    return ok, err


_sim_state_554_555 = sim_state


def sim_state():                                          # + 555: the driver was set up again / the outputs are off
    d = _sim_state_554_555()
    try:
        d["servo"]["reinit"] = SRVSIM["reinit"]
        d["servo"]["out_off"] = bool(servo_outputs_off())
        d["servo"]["fault"] = SRV["fault"] or SRV["inhibit"] or ""
    except (KeyError, TypeError):
        pass
    return d


def simservo_info(lang=None):
    """one line for the servo page / window: what the simulator does to the servos right now ('' = nothing)"""
    s = SRVSIM.get("last")
    if not s or not CFG.get("sim_on"):
        return ""
    out = []
    if SRVSIM.get("v5") is not None:
        out.append(trf("5 V rail {v} V", lang, v=f"{SRVSIM['v5']:.2f}") + (" ⚠ " + tr("under-voltage", lang) if s.get("uv") else ""))
    if s.get("i2c"):
        out.append(tr("I2C error", lang))
    if s.get("pca_hold"):
        out.append(tr("PCA9685 reset", lang))
    if s.get("blocked"):
        out.append(tr("servo blocked", lang))
    return "🧪 " + tr("Simulator", lang) + ": " + " · ".join(out) if out else ""


def simservo_selftest():
    """under-voltage, PCA9685 reset, I2C errors and a blocked servo from the simulator values"""
    keep = {k: CFG.get(k) for k in ("sim_on", "servo_estop", "servo_uv_stop", "sim_servo_block_check")}
    keep_sim = {k: SIM.get(k) for k in ("head", "follower")}
    keep_srv = {k: SRV.get(k) for k in ("fault", "inhibit", "io_err", "io_t", "sim_uv", "pos", "moving", "push_t")}
    G = globals()
    keep_fn = {k: G[k] for k in ("save_settings", "servo_diag_fault", "log_event", "servo_diag_count_uv")}
    keep_hw = dict(HW_REINIT)
    try:
        G.update(save_settings=lambda *a, **k: None, servo_diag_fault=lambda *a, **k: None, log_event=lambda *a, **k: None,
                 servo_diag_count_uv=lambda *a, **k: None)
        SRV["push_t"] = time.time()
        CFG.update(sim_on=True, servo_estop=False, servo_uv_stop=True); SRV.update(fault="", inhibit="", io_err=0, pos=[50.0, 50.0], moving=False)
        SRVSIM.update(pca_seen=None, pca_due=0.0); SIM["follower"] = False
        base = {"v5": 5.1, "uv": False, "i2c": False, "pca_reset": 0, "pca_hold": False, "blocked": "", "head_mw": True}
        simservo_take({"servo_sim": dict(base, uv=True, v5=4.5)})
        assert SRV["sim_uv"]
        servo_safety_tick(time.time())
        assert SRV["inhibit"] == "uv", SRV["inhibit"]
        SRV.update(inhibit="", sim_uv=False)
        simservo_take({"servo_sim": dict(base, pca_reset=1)})
        assert SRVSIM["pca_due"] > 0
        SRVSIM["pca_due"] = time.time() - 1
        simservo_take({"servo_sim": dict(base, pca_reset=1)})
        assert SRV["fault"] == "pca_reset" and servo_outputs_off()
        r0 = SRVSIM["reinit"]
        ok, _ = servo_release("selftest")
        assert ok and SRVSIM["reinit"] == r0 + 1 and sim_state()["servo"]["reinit"] == r0 + 1
        SRV["moving"] = True
        for _ in range(3):
            simservo_take({"servo_sim": dict(base, i2c=True)})
        assert SRV["fault"] == "i2c", SRV["fault"]
        servo_release("selftest"); SRV["moving"] = False
        # blocked (2.98.53): a) off by default -> nothing; b) on + the head stays while MoveEye drives -> fault;
        # c) on + slow answers (the head follows one reply late, 0.8 s apart) -> nothing; d) on + stale answers -> nothing;
        # e) on + planned angle at the end of the head -> nothing
        def run_(pos_head, dt, on, t_rep_late=0.0):
            CFG["sim_servo_block_check"] = on
            SRVSIM["hist"].clear(); SRVSIM["blk_t"] = 0.0; SRV["fault"] = ""
            t0 = time.time()
            for i, (p_, h_) in enumerate(pos_head):
                SRV["pos"] = [p_, 50.0]
                _simservo_block_check(base, t0 + i * dt, [h_, 0.0], t0 + i * dt - t_rep_late)
            return SRV["fault"]
        stuck = [(50.0 + min(i, 6) * 2.0, 0.0) for i in range(20)]                  # 0° -> about 22° planned, head stays at 0°
        assert DEFAULTS.get("sim_servo_block_check") is False
        assert run_(stuck, 0.25, False) == "", "off by default"
        assert run_(stuck, 0.25, True) == "blocked", SRV["fault"]
        servo_release("selftest")
        hd = lambda p_: (p_ - 50.0) / 50.0 * servo_half("pan")
        slow = []
        for i in range(12):                                # a big jump, the answers 0.8 s apart and one step behind
            p_ = 50.0 + min(i, 3) * 6.0
            slow.append((p_, hd(50.0 + min(max(i - 1, 0), 3) * 6.0)))
        assert run_(slow, 0.8, True) == "", "slow answers: " + SRV["fault"]
        assert run_(stuck, 0.25, True, t_rep_late=2.0) == "", "stale answers"
        edge = [(100.0, servo_half("pan") - 3.0) for _ in range(20)]               # planned 90° (the end), head at 87°
        assert run_(edge, 0.25, True) == "", "at the end stop"
    finally:
        G.update(keep_fn); HW_REINIT.update(keep_hw)
        CFG.update(keep); SIM.update(keep_sim); SRV.update(keep_srv); SRVSIM.update(pca_seen=None, pca_due=0.0); SRVSIM["hist"].clear()
    return True


SELFTEST_EXTRA.append(("Servo faults of the simulator: under-voltage, PCA9685 reset, I2C, blocked (555)", simservo_selftest))
