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
# Translations: part 557.
# ----------------------------------------------------------------------------
SRV.setdefault("sim_uv", False)
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
    # the diagnosis: does the head follow?
    _simservo_block_check(s, now)


def _simservo_block_check(s, now):
    h = SIM.get("head")
    H = SRVSIM["hist"]
    if (not isinstance(h, list) or len(h) < 2 or not s.get("head_mw", True) or s.get("pca_hold") or s.get("i2c") or s.get("uv")
            or servo_blocked() or SIM.get("follower")):
        H.clear(); return
    try:
        cp, ct = servo_pos_deg()
        H.append((now, cp, float(h[0]), ct, float(h[1])))
    except (TypeError, ValueError):
        return
    while H and now - H[0][0] > 4.0:
        H.popleft()
    if len(H) < 4 or now - H[0][0] < 2.0 or now - SRVSIM["blk_t"] < 10.0:     # a busy PC answers maybe twice a second
        return
    for axis, ci, hi in (("pan", 1, 2), ("tilt", 3, 4)):
        cr = max(x[ci] for x in H) - min(x[ci] for x in H)
        hr = max(x[hi] for x in H) - min(x[hi] for x in H)
        if cr > 6.0 and hr < 1.0:
            SRVSIM["blk_t"] = now
            servo_fault("blocked", f"{axis}: {tr('Pan' if axis == 'pan' else 'Tilt', 'en')} {H[0][ci]:.0f}° → {H[-1][ci]:.0f}°, "
                                   f"head stays at {H[-1][hi]:.0f}°")
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
    keep = {k: CFG.get(k) for k in ("sim_on", "servo_estop", "servo_uv_stop")}
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
        # blocked: the planned position moves 10°, the head stays
        SRVSIM["hist"].clear(); SRVSIM["blk_t"] = 0.0
        t0 = time.time()
        for i in range(12):
            SRV["pos"] = [50.0 + i * 0.5, 50.0]
            SIM["head"] = [0.0, 0.0]
            _simservo_block_check(base, t0 + i * 0.25)
        assert SRV["fault"] == "blocked", SRV["fault"]
        servo_release("selftest")
    finally:
        G.update(keep_fn); HW_REINIT.update(keep_hw)
        CFG.update(keep); SIM.update(keep_sim); SRV.update(keep_srv); SRVSIM.update(pca_seen=None, pca_due=0.0); SRVSIM["hist"].clear()
    return True


SELFTEST_EXTRA.append(("Servo faults of the simulator: under-voltage, PCA9685 reset, I2C, blocked (555)", simservo_selftest))
