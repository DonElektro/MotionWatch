#@ MoveEye – Teil 072: Servo-Bewegung wie bei einem Industrieroboter: ein Bewegungsplaner (Rampen, beide Achsen gemeinsam), sichere Zustände (Not-Aus, Freigeben, Grenzen ganz unten, Störung, Unterspannung) und Watchdog. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.35 (Wunsch Daniel, «industriell»): ONE motion planner for pan / tilt. Everybody (joystick, buttons, coordinator 162,
#   patrol 160, reference scan 315, place scan 317, timelapse, wake-up alarm, tracking 410 …) still writes the WANTED
#   position into CFG["pan"] / CFG["tilt"] (0..100 %). The servo loop (Hardware.loop, part 080, 50 Hz) calls servo_plan_tick():
#   it drives the REAL position SRV["pos"] there with a trapezoid profile per axis (max. speed and acceleration in °/s and
#   °/s² per axis, settings «Servo motion & safety»): accelerate, cruise, brake, land exactly on the target - no jump, no
#   overshoot (a target that changes the direction while moving is braked first). A point-to-point move from rest is
#   synchronised: both axes start and arrive together (straight line). Only SRV["pos"] reaches the PWM and the simulator
#   (sim_state, part 290: pan_deg / tilt_deg + speed), so the simulator sees every intermediate position.
#   servo_goto(pan, tilt, who, speed, wait) = drive there (optionally slower) and wait until it stands - the old own
#   ramps of the patrol and the coordinator are gone (no second path). servo_pos() = where the head really looks (the
#   picture comes from there: tracking, «turn to the alarm»).
# Safe states:
#   * Not-Aus / Stopp (web, window, controller: hold Select 1.5 s, API POST /api/servo {"op": "estop"}): braking with twice
#     the acceleration, then hold (or park, setting); every new target is ignored, the mover stops. It stays after a
#     restart (CFG["servo_estop"]) until somebody presses «Freigeben» (release).
#   * Störung (latched, needs «Freigeben»): I2C errors in a row, the PCA9685 lost its settings (brown-out / reset). The
#     servo outputs stay off until the release (no jump to an old position by itself).
#   * Sperre (clears by itself): under-voltage (vcgencmd get_throttled, part 100, STATE["supply"]) and the watchdog of the
#     camera loop (HEART older than servo_wd_s): the head stops and holds; no push spam (one push per hour at most).
#   * Software limits (pan_limit / tilt_limit): the target is clamped here AND once more right before the PWM (080
#     Hardware._servos) - also after an error or a wrong value (NaN) nothing goes past them.
#   * Watchdog of the servo loop itself: a thread checks its heartbeat; when it hung (> 1.5 s) the old move is not
#     continued afterwards (the target becomes the position where it stopped).
# Fault memory, operating hours, degrees and moves per axis: part 074 (servo_diag_*).
# ----------------------------------------------------------------------------
for _k, _v in {"servo_vmax_pan": 120.0, "servo_vmax_tilt": 90.0, "servo_acc_pan": 360.0, "servo_acc_tilt": 300.0,
               "servo_estop": False, "servo_estop_by": "", "servo_stop_btn": True, "servo_estop_park": False, "servo_uv_stop": True,
               "servo_wd_s": 10.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
SRV = {"pos": None, "vel": [0.0, 0.0], "tgt": None, "scale": [(1.0, 1.0), (1.0, 1.0)], "cap": None, "moving": False, "arrive_t": 0.0,
       "start_t": 0.0, "beat": 0.0, "inhibit": "", "inhibit_t": 0.0, "inhibit_log": {}, "fault": "", "fault_t": 0.0,
       "io_err": 0, "io_t": 0.0, "wd_trip": False, "wd_log": 0.0, "limit_on": [False, False], "parked": False,
       "estop_t": 0.0, "push_t": 0.0, "safety_t": 0.0, "test_uv": False, "trace": deque(maxlen=1500), "started": False}
SERVO_AXES = ("pan", "tilt")
SRV_FAULT_LOCK = ("i2c", "pca_reset")          # latched faults that also keep the servo outputs off until the release


def _srv_k(axis):
    """% per degree of an axis (0..100 % = the whole turning range)"""
    return 100.0 / (2.0 * servo_half(axis))


def srv_limits_pct():
    """[(lo, hi), (lo, hi)] in % for pan and tilt (pan_limit / tilt_limit, middle = 50 %)"""
    try:
        return Hardware.limits()
    except Exception:
        return [(0.0, 100.0), (0.0, 100.0)]


def srv_clamp(pan, tilt):
    """the software limits - for every target and once more before the PWM. NaN / nonsense -> None (keep the old value)"""
    out = []
    for v, (lo, hi) in zip((pan, tilt), srv_limits_pct()):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(v):
            return None
        out.append(max(lo, min(hi, max(0.0, min(100.0, v)))))
    return out[0], out[1]


def srv_axis_limits(axis):
    """(max. speed %/s, max. acceleration %/s²) of an axis from the settings in degrees"""
    k = _srv_k(axis)
    try:
        vm = max(5.0, min(600.0, float(CFG.get("servo_vmax_" + axis) or 120.0)))
        am = max(20.0, min(5000.0, float(CFG.get("servo_acc_" + axis) or 300.0)))
    except (TypeError, ValueError):
        vm, am = 120.0, 300.0
    return vm * k, am * k


def srv_axis_step(p, v, tgt, vmax, amax, dt):
    """one step of the motion planner for one axis - an online trapezoid profile.
    p, tgt in %, v in %/s, vmax %/s, amax %/s², dt s -> (new p, new v).
    The speed is always the highest one from which it can still stop on the target (v² / 2a, in the discrete form of the
    step), at most vmax, and changes by at most amax * dt per step. Coming from rest it never passes the target and the
    last step lands exactly on it."""
    e = tgt - p
    h = amax * dt
    if abs(e) <= 1e-4 and abs(v) <= h:
        return tgt, 0.0
    s = 1.0 if e > 0 else -1.0
    d = abs(e); vt = v * s                                  # speed towards the target (negative = moving away)
    if 0.0 <= vt <= h * 1.0001 and d <= (vt + h * 0.5) * dt:
        return tgt, 0.0                                     # the last step: it stops exactly on the target
    q = h * h / 4.0 + 2.0 * amax * d - h * vt
    vs = -h / 2.0 + math.sqrt(q) if q > 0 else 0.0
    vd = s * min(vmax, vs)
    v2 = v + max(-h, min(h, vd - v))
    if vt > 0.0 and v2 * s < 0.0:
        v2 = 0.0                                            # still before the target: do not turn round
    p2 = p + (v + v2) * 0.5 * dt
    if (tgt - p2) * s < 0.0 and abs(v2) <= h * 1.0001:
        return tgt, 0.0
    return p2, v2


def srv_trap_time(d, vmax, amax):
    """time of a trapezoid move over d from rest to rest"""
    d = abs(d)
    if d <= 0:
        return 0.0
    if d >= vmax * vmax / amax:
        return d / vmax + vmax / amax
    return 2.0 * math.sqrt(d / amax)


def srv_sync_scale(dists, lims):
    """both axes start and arrive together: the axis with the longer time leads, the other one gets the leader's profile
    scaled by its distance / the distance of the leader (straight line). -> [(speed factor, acc. factor) pan, … tilt]
    relative to each axis' own limits (never above 1)"""
    ts = [srv_trap_time(d, vm, am) for d, (vm, am) in zip(dists, lims)]
    out = [(1.0, 1.0), (1.0, 1.0)]
    if max(ts) <= 0:
        return out
    li = 0 if ts[0] >= ts[1] else 1
    oi = 1 - li
    dl, do = abs(dists[li]), abs(dists[oi])
    if dl > 1e-6 and do > 1e-6:
        r = do / dl
        vm_l, am_l = lims[li]; vm_o, am_o = lims[oi]
        out[oi] = (max(0.01, min(1.0, vm_l * r / vm_o)), max(0.01, min(1.0, am_l * r / am_o)))
    return out


def servo_pos():
    """where the head really is (pan %, tilt %) - the planned position that went to the servos"""
    p = SRV["pos"]
    if p is None:
        return float(CFG["pan"]), float(CFG["tilt"])
    return p[0], p[1]


def servo_pos_deg():
    p, t = servo_pos()
    return (p - 50.0) / 50.0 * servo_half("pan"), (t - 50.0) / 50.0 * servo_half("tilt")


def servo_arrived(tol=0.15):
    """the head stands on the wanted position"""
    p = SRV["pos"]
    if p is None:
        return True
    return (abs(p[0] - float(CFG["pan"])) <= tol and abs(p[1] - float(CFG["tilt"])) <= tol
            and abs(SRV["vel"][0]) < 0.05 and abs(SRV["vel"][1]) < 0.05)


def servo_blocked():
    """'' = it may move; otherwise why not (Not-Aus, a latched fault, a lock that clears by itself)"""
    if CFG.get("servo_estop"):
        return "estop"
    if SRV["fault"]:
        return "fault"
    if SRV["inhibit"]:
        return "inhibit"
    return ""


def servo_blocked_text(lang=None):
    b = servo_blocked()
    if b == "estop":
        return tr("Emergency stop - press «Release» to move again", lang)
    if b == "fault":
        return tr("Servo fault", lang) + ": " + tr(SRV_FAULT_TEXT.get(SRV["fault"], SRV["fault"]), lang) + " - " + tr("press «Release» after checking", lang)
    if b == "inhibit":
        return tr("Servos stopped", lang) + ": " + tr(SRV_FAULT_TEXT.get(SRV["inhibit"], SRV["inhibit"]), lang) + " - " + tr("moves again by itself", lang)
    return ""


SRV_FAULT_TEXT = {"i2c": "I2C errors - the servo driver does not answer", "pca_reset": "the PCA9685 lost its settings (brown-out or reset)",
                  "uv": "under-voltage of the power supply", "wd_cam": "the camera loop hangs (watchdog)",
                  "wd_loop": "the servo loop hung (watchdog)", "estop": "emergency stop", "release": "released",
                  "limit": "software limit reached", "temp": "high temperature of the Pi", "throttle": "the Pi slows down (throttled)",
                  "no_driver": "no servo driver found"}


def servo_park_target():
    """the parking position: a taught point chosen as parking position (076), otherwise kopf_park_pan / kopf_park_tilt"""
    try:
        tp = teach_point_by_name(CFG.get("kopf_park_point") or "")
    except NameError:
        tp = None
    if tp:
        return srv_clamp(tp[0], tp[1])
    return srv_clamp(CFG.get("kopf_park_pan", 50.0), CFG.get("kopf_park_tilt", 5.0))


def servo_stop_point():
    """where both axes stand when braking now with the normal acceleration"""
    p = list(servo_pos())
    for i, ax in enumerate(SERVO_AXES):
        _vm, am = srv_axis_limits(ax)
        v = SRV["vel"][i]
        p[i] = p[i] + v * abs(v) / (2.0 * am)
    return srv_clamp(p[0], p[1]) or servo_pos()


def servo_goto(pan, tilt, who="", speed=None, wait=True, stop=None, timeout=60.0):
    """THE way to drive the head to a position: the target goes to the planner (optionally slower: speed = path speed
    in %/s, e.g. the patrol speed), wait = until it stands there. False: blocked (Not-Aus, fault), interrupted by stop() or
    by somebody else who set another target, or timeout."""
    if servo_blocked():
        return False
    c = srv_clamp(pan, tilt)
    if c is None:
        return False
    pan, tilt = c
    CFG["pan"], CFG["tilt"] = float(pan), float(tilt)
    SRV["cap"] = (float(speed), (round(pan, 3), round(tilt, 3))) if speed else None
    if not wait:
        return True
    if SRV["pos"] is None or not SRV.get("started"):
        return True                                       # no servo loop (tests, tools): the target counts as reached
    end = time.time() + timeout
    while time.time() < end:
        if servo_blocked():
            return False
        if abs(float(CFG["pan"]) - pan) > 0.01 or abs(float(CFG["tilt"]) - tilt) > 0.01:
            return False                                  # somebody else drives the head now
        if stop is not None:
            try:
                if stop():
                    sp = servo_stop_point()               # brake gently where it is (no jerk, no return)
                    CFG["pan"], CFG["tilt"] = sp[0], sp[1]; SRV["cap"] = None
                    return False
            except Exception:
                return False
        if servo_arrived():
            return True
        time.sleep(0.02)
    return False


def servo_wait(timeout=15.0, settle=0.0):
    """wait until the head stands on its target (then settle seconds more) - for tools that set CFG themselves"""
    end = time.time() + timeout
    while time.time() < end and SRV.get("started") and not servo_arrived():
        if servo_blocked():
            return False
        time.sleep(0.03)
    if settle > 0:
        time.sleep(settle)
    return servo_arrived()


# ---- the planner step, called by the servo loop (Hardware.loop, 080) ------------------------------------------------
def servo_plan_tick(dt):
    """-> (pan, tilt) in % for the servos now. Reads the targets CFG["pan"] / CFG["tilt"] (already clamped by the loop)."""
    now = time.time()
    SRV["beat"] = time.monotonic(); SRV["started"] = True
    dt = max(0.001, min(0.1, float(dt)))
    if SRV["pos"] is None:
        SRV["pos"] = [float(CFG["pan"]), float(CFG["tilt"])]; SRV["tgt"] = list(SRV["pos"])
    if now - SRV["safety_t"] >= 0.25:
        SRV["safety_t"] = now
        try:
            servo_safety_tick(now)
        except Exception as e:
            log_event("servo", f"Servo safety check: {type(e).__name__}: {e}"[:160])
    pos, vel = SRV["pos"], SRV["vel"]
    if SRV["wd_trip"]:                                   # the loop hung: do not go on with the old move
        SRV["wd_trip"] = False; vel[0] = vel[1] = 0.0
        CFG["pan"], CFG["tilt"] = pos[0], pos[1]
    blocked = servo_blocked()
    estop = blocked == "estop"
    if blocked:
        # stop: brake (Not-Aus: twice the acceleration), then hold; with «park» drive slowly to the parking position
        park = None
        if estop and CFG.get("servo_estop_park") and SRV["parked"] is not True:
            park = servo_park_target()
        if park is not None and SRV["parked"] == "go":
            for i, ax in enumerate(SERVO_AXES):          # stands: slowly (15 °/s) to the parking position
                vm, am = srv_axis_limits(ax)
                pos[i], vel[i] = srv_axis_step(pos[i], vel[i], park[i], min(vm, 15.0 * _srv_k(ax)), am, dt)
            if pos[0] == park[0] and pos[1] == park[1] and vel[0] == 0.0 and vel[1] == 0.0:
                SRV["parked"] = True
                log_event("servo", "Emergency stop: parked - holding")
        else:
            for i, ax in enumerate(SERVO_AXES):          # braking (Not-Aus: twice the acceleration) to a stand
                _vm, am = srv_axis_limits(ax)
                a2 = am * (2.0 if estop else 1.0) * dt
                v = vel[i]; v2 = v - math.copysign(min(abs(v), a2), v)
                pos[i] += (v + v2) * 0.5 * dt; vel[i] = v2
            if park is not None and vel[0] == 0.0 and vel[1] == 0.0:
                SRV["parked"] = "go"
        c = srv_clamp(pos[0], pos[1])
        if c:
            pos[0], pos[1] = c
        CFG["pan"], CFG["tilt"] = round(pos[0], 3), round(pos[1], 3)      # the pages show where it stands; no target waits
        SRV["cap"] = None; SRV["tgt"] = list(pos)
    else:
        SRV["parked"] = False
        tgt = [float(CFG["pan"]), float(CFG["tilt"])]
        lims = [srv_axis_limits(ax) for ax in SERVO_AXES]
        if SRV["tgt"] is None or abs(tgt[0] - SRV["tgt"][0]) > 1e-3 or abs(tgt[1] - SRV["tgt"][1]) > 1e-3:
            SRV["tgt"] = list(tgt)
            rest = abs(vel[0]) < 0.5 and abs(vel[1]) < 0.5
            SRV["scale"] = srv_sync_scale([tgt[0] - pos[0], tgt[1] - pos[1]], lims) if rest else [(1.0, 1.0), (1.0, 1.0)]
        cap = SRV["cap"]
        capv = None
        if cap and abs(cap[1][0] - tgt[0]) < 0.01 and abs(cap[1][1] - tgt[1]) < 0.01:
            capv = max(1.0, cap[0])
        elif cap:
            SRV["cap"] = None
        dist = math.hypot(tgt[0] - pos[0], tgt[1] - pos[1])
        for i, ax in enumerate(SERVO_AXES):
            vm, am = lims[i]
            kv, ka = SRV["scale"][i]
            vm, am = vm * kv, am * ka
            if capv is not None and dist > 1e-6:
                vm = min(vm, max(0.2, capv * abs(tgt[i] - pos[i]) / dist)) if abs(vel[i]) < vm else min(vm, capv)
            p0 = pos[i]
            pos[i], vel[i] = srv_axis_step(pos[i], vel[i], tgt[i], vm, am, dt)
            if not math.isfinite(pos[i]) or not math.isfinite(vel[i]):
                pos[i], vel[i] = p0, 0.0
    moving = abs(vel[0]) > 0.01 or abs(vel[1]) > 0.01
    if moving and not SRV["moving"]:
        SRV["start_t"] = now
        servo_diag_move_start()
    if SRV["moving"] and not moving:
        SRV["arrive_t"] = now
    SRV["moving"] = moving
    servo_diag_count(dt, vel)
    if moving or len(SRV["trace"]) == 0 or now - SRV["trace"][-1][0] > 1.0:
        hp, ht = servo_half("pan"), servo_half("tilt")
        SRV["trace"].append((round(now, 3), round((pos[0] - 50) / 50 * hp, 3), round((pos[1] - 50) / 50 * ht, 3)))
    return pos[0], pos[1]


def servo_speed_deg():
    """the speed now in °/s (pan, tilt) - for the simulator (it goes on between two packets)"""
    return SRV["vel"][0] / _srv_k("pan"), SRV["vel"][1] / _srv_k("tilt")


def servo_outputs_off():
    """a latched fault of the driver: the servo outputs stay off until the release"""
    return SRV["fault"] in SRV_FAULT_LOCK


# ---- who steers the head (several «panels»: phones, PCs, the window, the controller, the simulator) --------------------
# Lesson from robotics (Daniel): never start the wrong robot from the wrong panel. Every manual command notes its panel;
# all clients show «the head is steered by …» and a short notice when another panel takes it (state polling, no extra
# connection). key = an anonymous short id of the panel (address + browser), label = what people read.
def servo_driver_note(who, what=""):
    if isinstance(who, (tuple, list)) and len(who) == 2:
        key, label = str(who[0])[:24], str(who[1])[:60]
    else:
        key = label = str(who or "?")[:60]
        if key == "window":
            label = tr("Window") + " (" + tr("this computer") + ")"
    d = SRV.get("drv") or {}
    now = time.time()
    if d.get("key") != key or now - float(d.get("t", 0)) > 10.0:
        SRV["drv_n"] = int(SRV.get("drv_n", 0)) + 1      # a new «session» of a panel: the others get a notice
        if d.get("key") != key:
            log_event("servo", f"The head is steered by: {label}")
    SRV["drv"] = {"key": key, "label": label, "t": now, "what": str(what)[:20], "n": SRV.get("drv_n", 0)}


def servo_driver(lang=None):
    """who steers the head right now: a panel (manual, last 10 s) or the automatic (162) - for every client"""
    d = SRV.get("drv") or {}
    now = time.time()
    if d and now - float(d.get("t", 0)) <= 10.0:
        return {"kind": "manual", "key": d["key"], "label": d["label"], "ago": round(now - d["t"], 1), "n": d.get("n", 0)}
    try:
        own = kopf_owner()
    except Exception:
        own = ""
    names = {"manual": "by hand / tool", "alarm": "alarm / follow", "walktest": "walk test", "glance": "quick look at the valuables",
             "round": "round (patrol)", "park": "parking"}
    if STATE.get("tracking"):
        own = "alarm"
    return {"kind": "auto" if own else "idle", "key": "", "label": tr(names.get(own, ""), lang) if own else "", "ago": None,
            "n": d.get("n", 0) if d else 0}


# ---- Not-Aus / release -------------------------------------------------------------------------------------------------
def servo_estop(by="web"):
    """by = a label or (key, label) of the panel - every client shows who pressed it"""
    if isinstance(by, (tuple, list)) and len(by) == 2:
        servo_driver_note(by, "estop"); by = by[1]
    first = not CFG.get("servo_estop")
    CFG["servo_estop"] = True; CFG["servo_estop_by"] = str(by)[:60]
    SRV["estop_t"] = time.time(); SRV["cap"] = None
    try:
        MOVER.update(v=0.0, w=0.0, cmd_t=0.0)              # the mover stops too
        if MOVERCTL is not None:
            MOVERCTL.stop_now()
    except Exception:
        pass
    if first:
        log_event("servo", f"EMERGENCY STOP ({by}): all movement stopped - «Release» needed")
        servo_diag_fault("estop", "warn", f"Emergency stop ({by})")
        save_settings()
    return True


def servo_release(by="web"):
    """«Freigeben»: ends the Not-Aus and a latched fault. Not while the reason is still there (under-voltage …)."""
    if isinstance(by, (tuple, list)) and len(by) == 2:
        servo_driver_note(by, "release"); by = by[1]
    if SRV["inhibit"] == "uv":
        if SRV["test_uv"] or ((STATE.get("supply") or {}).get("uv_now") and not CFG.get("sim_on")):
            return False, "under-voltage is still there - check the power supply first"
        SRV["inhibit"] = ""; SRV["uv_last"] = 0.0           # it is over: «Freigeben» need not wait the 30 s
    was = servo_blocked()
    if not was:
        return True, ""
    p = servo_pos()
    CFG["pan"], CFG["tilt"] = p[0], p[1]                   # nothing jumps: the target is where it stands
    SRV["vel"] = [0.0, 0.0]; SRV["tgt"] = list(p); SRV["cap"] = None
    fault = SRV["fault"]
    CFG["servo_estop"] = False; CFG["servo_estop_by"] = ""
    SRV.update(fault="", fault_t=0.0, io_err=0, parked=False)
    if fault in SRV_FAULT_LOCK:
        HW_REINIT["want"] = True                           # the driver is set up again, then the outputs come back
    MANUAL["until"] = time.time() + 3.0                    # a short pause before the automatic moves start again
    log_event("servo", f"Servos released ({by})" + (f" after: {SRV_FAULT_TEXT.get(fault, fault)}" if fault else ""))
    servo_diag_fault("release", "info", f"Released ({by})" + (f" - {fault}" if fault else ""))
    save_settings()
    return True, ""


def servo_fault(code, text=""):
    """a latched fault (needs «Freigeben»)"""
    if SRV["fault"] == code:
        return
    SRV["fault"] = code; SRV["fault_t"] = time.time(); SRV["cap"] = None
    log_event("servo", f"SERVO FAULT: {SRV_FAULT_TEXT.get(code, code)}" + (f" - {text}" if text else "") + " - stopped, «Release» needed")
    servo_diag_fault(code, "error", text or SRV_FAULT_TEXT.get(code, code))
    _servo_push_once(tr("Servo fault") + ": " + tr(SRV_FAULT_TEXT.get(code, code)))


def _servo_push_once(text):
    """at most one push per hour for servo problems (no spam, never the siren)"""
    if time.time() - SRV["push_t"] < 3600:
        return
    SRV["push_t"] = time.time()
    w = WATCH_REF.get("w") if "WATCH_REF" in globals() else None
    if w is not None and not CFG.get("sim_on"):
        try:
            w.notifier.info(text, title="{name}: " + tr("Servos"))
        except Exception:
            pass


def servo_io_error(e):
    """a write to the servo driver failed (080). One error: noted; 3 in a row within 3 s: latched fault."""
    now = time.time()
    SRV["io_err"] = SRV["io_err"] + 1 if now - SRV["io_t"] < 3.0 else 1
    SRV["io_t"] = now
    servo_diag_fault("i2c", "warn", f"{type(e).__name__}: {e}"[:120])
    if SRV["io_err"] >= 3:
        servo_fault("i2c", f"{type(e).__name__}: {e}"[:120])


def servo_io_ok():
    SRV["io_err"] = 0


def _servo_inhibit(code, on, now):
    if on and SRV["inhibit"] != code and not SRV["inhibit"]:
        SRV["inhibit"] = code; SRV["inhibit_t"] = now
        if now - SRV["inhibit_log"].get(code, 0.0) > 300:
            SRV["inhibit_log"][code] = now
            log_event("servo", f"Servos stopped: {SRV_FAULT_TEXT.get(code, code)} - they move again by themselves")
            servo_diag_fault(code, "warn", SRV_FAULT_TEXT.get(code, code))
            if code == "uv":
                _servo_push_once(tr("Servos stopped") + ": " + tr(SRV_FAULT_TEXT["uv"]))
    elif not on and SRV["inhibit"] == code:
        SRV["inhibit"] = ""
        log_event("servo", f"Servos may move again ({SRV_FAULT_TEXT.get(code, code)} is over)")


def servo_safety_tick(now):
    """4 x per second: under-voltage, the camera loop watchdog, temperature (only noted)"""
    sup = STATE.get("supply") or {}
    uv = (bool(sup.get("uv_now")) and not CFG.get("sim_on")) or SRV["test_uv"]
    if uv:
        SRV["uv_last"] = now
    if CFG.get("servo_uv_stop", True):
        _servo_inhibit("uv", uv or (SRV["inhibit"] == "uv" and now - SRV.get("uv_last", 0.0) < 30.0), now)
    elif SRV["inhibit"] == "uv":
        _servo_inhibit("uv", False, now)
    # the camera loop hangs (HEART, 410): nothing should move on old information
    wd = max(3.0, float(CFG.get("servo_wd_s") or 10.0))
    hb = now - float(HEART.get("t", now)) if "HEART" in globals() else 0.0
    idle = PAUSING.get("on") or toolmode_on() if "PAUSING" in globals() else True
    hang = hb > wd and not idle and now - START > 60 and WATCH_REF.get("w") is not None
    if SRV["inhibit"] in ("", "wd_cam"):
        _servo_inhibit("wd_cam", hang, now)
    t = STATE.get("cpu_temp")
    if isinstance(t, (int, float)) and t >= 82.0 and now - SRV.get("temp_t", 0.0) > 600:
        SRV["temp_t"] = now
        servo_diag_fault("temp", "warn", f"{t:.0f} °C")
    if sup.get("throttled") and now - SRV.get("thr_t", 0.0) > 600:
        SRV["thr_t"] = now
        servo_diag_fault("throttle", "warn", "vcgencmd get_throttled")
    if uv and now - SRV.get("uvd_t", 0.0) > 60:
        SRV["uvd_t"] = now
        servo_diag_count_uv()


def servo_limit_note(axis_i, hit):
    """the loop (080) clamped a target at the software limit: one entry per episode"""
    if hit and not SRV["limit_on"][axis_i]:
        servo_diag_fault("limit", "info", ("pan" if axis_i == 0 else "tilt") + " " + tr("limit"))
    SRV["limit_on"][axis_i] = hit


def _servo_watchdog():
    """the servo loop itself: its heartbeat must be fresh - after a hang the old move is not continued"""
    while True:
        time.sleep(0.25)
        try:
            b = SRV["beat"]
            if b and time.monotonic() - b > 1.5 and not SRV["wd_trip"]:
                SRV["wd_trip"] = True
                if time.time() - SRV["wd_log"] > 300:
                    SRV["wd_log"] = time.time()
                    log_event("servo", "Watchdog: the servo loop hung - the move is not continued")
                    servo_diag_fault("wd_loop", "warn", f"{time.monotonic() - b:.1f} s")
        except Exception:
            pass


def servo_watchdog_start():
    if not SRV.get("wd_started"):
        SRV["wd_started"] = True
        threading.Thread(target=_servo_watchdog, daemon=True, name="servo-wd").start()


def servo_state(lang=None):
    """for the pages and the API"""
    p, t = servo_pos()
    pd, td = servo_pos_deg()
    vp, vt = servo_speed_deg()
    (plo, phi), (tlo, thi) = srv_limits_pct()
    return {"pos": [round(p, 2), round(t, 2)], "deg": [round(pd, 1), round(td, 1)], "dps": [round(vp, 1), round(vt, 1)],
            "target": [round(float(CFG["pan"]), 2), round(float(CFG["tilt"]), 2)], "moving": SRV["moving"],
            "blocked": servo_blocked(), "text": servo_blocked_text(lang), "estop": bool(CFG.get("servo_estop")),
            "estop_by": CFG.get("servo_estop_by") or "", "fault": SRV["fault"], "inhibit": SRV["inhibit"],
            # 2.98.43 (Daniel): «⏹ Stopp» on the live page only with a head and when not switched off
            "stop_btn": bool(CFG.get("servo_stop_btn", True)) and bool(globals().get("live_has_head", lambda: True)()),
            "limits": [[round(plo, 1), round(phi, 1)], [round(tlo, 1), round(thi, 1)]],
            "limits_deg": [float(CFG["pan_limit"]), float(CFG["tilt_limit"])],
            "vmax": [float(CFG["servo_vmax_pan"]), float(CFG["servo_vmax_tilt"])], "acc": [float(CFG["servo_acc_pan"]), float(CFG["servo_acc_tilt"])],
            "backend": str(STATE.get("servo_backend") or ""), "driver": servo_driver(lang)}


def servo_planner_selftest():
    """the planner: no overshoot from rest, acceleration and speed limited, exact landing, both axes together"""
    import random as _r
    for d in (0.05, 0.4, 3.0, 25.0, -60.0, 100.0):
        for jit in (False, True):
            p, v, n, t = 0.0, 0.0, 0, 0.0
            while n < 3000:
                dt = 0.02 * (_r.uniform(0.6, 1.8) if jit else 1.0)
                p2, v2 = srv_axis_step(p, v, d, 66.0, 220.0, dt)
                assert abs(v2) <= 66.0 + 1e-6, (d, v2)
                assert abs(v2 - v) <= 220.0 * dt + 1e-6, (d, v, v2)
                assert (p2 - d) * (1 if d > 0 else -1) <= 1e-9, ("overshoot", d, p2)
                assert (p2 - p) * (1 if d > 0 else -1) >= -1e-9, ("goes back", d, p, p2)
                p, v, n, t = p2, v2, n + 1, t + dt
                if p == d and v == 0.0:
                    break
            assert p == d and v == 0.0, ("not arrived", d, p, v)
            assert t <= srv_trap_time(d, 66.0, 220.0) + 0.2, (d, t)
    # a target behind it while moving: brakes (limited), turns, lands
    p, v = 0.0, 50.0
    for _ in range(400):
        p2, v2 = srv_axis_step(p, v, -5.0, 66.0, 220.0, 0.02)
        assert abs(v2 - v) <= 220.0 * 0.02 + 1e-6
        p, v = p2, v2
    assert p == -5.0 and v == 0.0
    # synchronised: the shorter axis gets slower limits, both take about the same time
    sc = srv_sync_scale([40.0, 10.0], [(60.0, 200.0), (50.0, 200.0)])
    t0 = srv_trap_time(40.0, 60.0, 200.0); t1 = srv_trap_time(10.0, 50.0 * sc[1][0], 200.0 * sc[1][1])
    assert sc[0] == (1.0, 1.0) and 0.0 < sc[1][0] < 1.0 and abs(t0 - t1) < 0.02, (sc, t0, t1)
    # the limits: clamped, NaN refused
    keep = (CFG["pan_limit"], CFG["tilt_limit"])
    try:
        CFG["pan_limit"] = 45; CFG["tilt_limit"] = 30
        c = srv_clamp(100.0, -5.0)
        assert c is not None and c[0] <= 50.0 + 45.0 / servo_half("pan") * 50.0 + 1e-9 and c[1] >= 50.0 - 30.0 / servo_half("tilt") * 50.0 - 1e-9
        assert srv_clamp(float("nan"), 50) is None and srv_clamp("x", 50) is None
    finally:
        CFG["pan_limit"], CFG["tilt_limit"] = keep
    return "trapezoid: no overshoot, limited, exact landing, synchronised, limits"
