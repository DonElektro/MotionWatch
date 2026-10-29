#@ MoveEye – Teil 162: Automatische Kopfbewegung (wer bewegt den Kopf: Hand > Alarm/Folgen > Gehtest > Wertsachen-Blick > Runde > Parken), kluge Runde, zum Alarm drehen, Parken bei «Aus», Wertsachen-Blick, sparsam bei Akku / tiefer Nacht, Wildtier-Modus, Abdeckung / Verdrehen prüfen, 360°-Servos. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30 (Wunsch Daniel): the pan / tilt head moves by itself - but always only ONE mover at a time. Who may move it:
#   1. by hand (joystick, buttons, reference scan, timelapse, wake-up alarm - servo_hold())
#   2. alarm / follow (410 follows a person or movement; «turn to the alarm» in Voll; the sabotage look-around)
#   3. walk test (the head follows the walker, 415)
#   4. quick look at the valuables (every 10-30 min)
#   5. the round (patrol / «kluge Runde» in Wachsam and Voll, part 160)
#   6. parking (Aus: the camera looks away)
# kopf_may(who) says whether nobody with a higher rank holds the head. The automatic moves (4-6, alarm turn) also wait
# while the simulator is busy with a task (simtask_busy, one lock - 141 / 147).
# The places come from «Platz einrichten» (place_items(), part 3XX) when it exists, otherwise from the waypoints.
# Angles: always via servo_half("pan") - the pan servo may turn 180 / 270 / 360°. A positional servo never passes its
# end stop (cable): with 360° every direction has exactly one place in 0 … 100 %, the head goes the allowed way there.
# Continuous rotation servos («360° endless», servo_kind = continuous): the position is only ESTIMATED from speed x time
# (Hardware.loop, part 080) - «set the middle» once the head looks straight ahead; shown as «estimated» everywhere.
# ----------------------------------------------------------------------------
for _k, _v in {"kopf_on": True, "kopf_round": True, "kopf_round_dwell": 8.0, "kopf_alarm": True, "kopf_return": True, "kopf_return_s": 20.0,
               "kopf_park": True, "kopf_park_pan": 50.0, "kopf_park_tilt": 5.0, "kopf_parked": False, "kopf_unpark": [],
               "kopf_glance": True, "kopf_glance_min": 15.0, "kopf_save": True, "kopf_night_from": 1.0, "kopf_night_to": 5.0,
               "kopf_walk": True, "kopf_wild": "auto", "kopf_wild_photo_s": 15.0, "kopf_tamper_look": True,
               "servo_kind": "positional", "cont_dps": 120.0, "cont_set_mid": False, "cont_est": 50.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
KOPF = {"started": False, "home": None, "home_t": 0.0, "home_pos": None, "back": None, "alarm": None, "turn_req": None,
        "turn_t": 0.0, "glance": "", "glance_next": 0.0, "glance_last": None, "round_on": False, "tamper": False,
        "armed_was": None, "noise_was": False, "noise_log": 0.0, "track_was": False, "wl_n": 0, "wild_photo_t": 0.0,
        "wild_photos": 0, "status": "", "val_cool": {}, "save_why": ""}
KOPF_PRIO = ("manual", "alarm", "walktest", "glance", "round", "park")
KOPF_WEIGHT = {"tent": 3.0, "access": 3.0, "valuable": 2.0, "public_path": 1.0, "ignore": 0.05}


# ---- angles (180 / 270 / 360° pan servos) ----------------------------------------------------------------------------
def kopf_pct_per_deg(axis="pan"):
    return 100.0 / (2.0 * servo_half(axis))


def kopf_pan_add(cur, ddeg):
    """the pan in % after turning ddeg degrees (+ = right) from cur %. A 360° servo: wrapped into its one turn (the allowed way,
    never over the end stop); smaller servos: up to their limit."""
    half = servo_half("pan")
    deg = (float(cur) - 50.0) / 50.0 * half + float(ddeg)
    if half >= 180.0:
        deg = (deg + 180.0) % 360.0 - 180.0
    (lo, hi), _t = Hardware.limits()
    return max(lo, min(hi, 50.0 + deg / half * 50.0))


def kopf_tilt_add(cur, ddeg):
    _p, (lo, hi) = Hardware.limits()
    return max(lo, min(hi, float(cur) + float(ddeg) * kopf_pct_per_deg("tilt")))


def kopf_pic_to_pan(cx, cy):
    """a point of the picture (0..1) -> (pan, tilt) in % where the head must look to have it in the middle"""
    hf, vf = cam_fov()
    return kopf_pan_add(CFG["pan"], (cx - 0.5) * hf), kopf_tilt_add(CFG["tilt"], -(cy - 0.5) * vf)


def servo_estimated():
    """continuous rotation servo: the pan position is only an estimate"""
    return CFG.get("servo_kind") == "continuous" and not CFG.get("sim_on")


# ---- the places (Platz einrichten) or the waypoints ------------------------------------------------------------------
def kopf_items():
    """[{kind, pan, tilt, w_pan, h_tilt, name}] from place_items() (part 3XX «Platz einrichten») - [] while it does not exist"""
    c = KOPF.get("_items")
    if c and time.time() - c[0] < 2.0:
        return list(c[1])
    f = globals().get("place_items")
    if not callable(f):
        return []
    out = []
    try:
        for it in (f() or [])[:60]:
            if not isinstance(it, dict) or it.get("kind") not in KOPF_WEIGHT:
                continue
            out.append({"kind": it["kind"], "pan": max(0.0, min(100.0, float(it.get("pan", 50)))), "tilt": max(0.0, min(100.0, float(it.get("tilt", 50)))),
                        "w_pan": max(0.0, float(it.get("w_pan") or 0)), "h_tilt": max(0.0, float(it.get("h_tilt") or 0)),
                        "name": str(it.get("name") or tr(it["kind"]))[:40]})
    except Exception:
        return []
    KOPF["_items"] = (time.time(), out)
    return list(out)


def kopf_stops():
    """the directions of the round: [(pan, tilt, dwell s, name, weight)] sorted left -> right"""
    its = [i for i in kopf_items()]
    if its and CFG.get("kopf_on") and CFG.get("kopf_round"):
        base = max(1.0, float(CFG.get("kopf_round_dwell") or 8.0))
        st = [(i["pan"], i["tilt"], round(max(0.3, base * KOPF_WEIGHT[i["kind"]] / 3.0), 1), i["name"], KOPF_WEIGHT[i["kind"]]) for i in its]
        return sorted(st, key=lambda s: s[0])
    return [(w[0], w[1], float(CFG["patrol_dwell"]), "", 1.0) for w in WAYPOINTS]


def kopf_best():
    """the most important direction (tent / access first, then valuables …) - None without places"""
    its = [i for i in kopf_items() if i["kind"] != "ignore"]
    if its:
        b = max(its, key=lambda i: KOPF_WEIGHT[i["kind"]])
        return (b["pan"], b["tilt"], b["name"])
    return None


def kopf_ignored(pan, tilt):
    """does this direction lie in an «ignore» place (branches, road)?"""
    for i in kopf_items():
        if i["kind"] == "ignore" and abs(pan - i["pan"]) <= max(3.0, i["w_pan"] / 2.0) and abs(tilt - i["tilt"]) <= max(3.0, i["h_tilt"] / 2.0 or 50.0):
            return True
    return False


# ---- saving: battery low or deep night -------------------------------------------------------------------------------
def kopf_save_active():
    if not (CFG.get("kopf_on") and CFG.get("kopf_save")):
        return ""
    try:
        if batt_save_active():
            return "battery low"
    except NameError:
        pass
    a, b = float(CFG.get("kopf_night_from", 1)), float(CFG.get("kopf_night_to", 5))
    now = datetime.now(); h = now.hour + now.minute / 60.0
    if a != b and ((a < b and a <= h < b) or (a > b and (h >= a or h < b))):
        return "deep night"
    return ""


# ---- wildlife --------------------------------------------------------------------------------------------------------
def kopf_wild_active():
    if not CFG.get("kopf_on"):
        return False
    m = CFG.get("kopf_wild") or "auto"
    if m == "auto":
        return CFG.get("use_case") == "wild" or CFG.get("mode") == "wild"
    return m == "on"


def kopf_motion_gain():
    """410: following movement - slowly in the wildlife mode (the animal is not scared, the picture stays calm)"""
    return 0.45 if kopf_wild_active() else 1.0


def kopf_wild_quiet():
    """the wildlife mode: movement without a person (an animal) gives no pre-alarm, no siren and no light; persons still do"""
    if not kopf_wild_active() or STATE.get("persons"):
        return False
    return True                                          # wildlife watching: movement without a person is no alarm


_light_alarm_base = light_alarm


def light_alarm():                                   # wildlife: the light stays off while an animal is followed
    if kopf_wild_quiet():
        return
    _light_alarm_base()


def kopf_track_blocked():
    """410 track(): parked (Aus, privacy) - the head does not follow"""
    return bool(CFG.get("kopf_parked")) and bool(CFG.get("kopf_park")) and bool(CFG.get("kopf_on"))


# ---- who holds the head ----------------------------------------------------------------------------------------------
def kopf_claims():
    c = set()
    try:
        if servo_hold() or REFSCAN.get("busy"):
            c.add("manual")
    except NameError:
        pass
    if (STATE.get("tracking") and not kopf_track_blocked()) or KOPF["alarm"] or KOPF["tamper"] or KOPF["back"]:
        c.add("alarm")                                   # (parked: following is blocked, it does not count)
    if walktest_on():
        c.add("walktest")
    if KOPF["glance"]:
        c.add("glance")
    if KOPF["round_on"]:
        c.add("round")
    if CFG.get("kopf_parked"):
        c.add("park")
    return c


def kopf_owner():
    c = kopf_claims()
    return next((p for p in KOPF_PRIO if p in c), "")


def kopf_may(who, sim_lock=True):
    """True when nobody with a higher rank holds the head (and, for the automatic moves, the simulator task lock is free)"""
    c = kopf_claims()
    for p in KOPF_PRIO:
        if p == who:
            break
        if p in c:
            return False
    if sim_lock and who not in ("manual",):
        try:
            if simtask_busy("protection test"):
                return False
        except NameError:
            pass
    return True


def kopf_move(pan, tilt, who, speed=None, stop=None):
    """drive smoothly to pan / tilt (%) at speed %/s; False when someone with a higher rank comes or stop() says so"""
    sp = float(speed or CFG.get("patrol_speed") or 30.0)
    (plo, phi), (tlo, thi) = Hardware.limits()
    pan = max(plo, min(phi, float(pan))); tilt = max(tlo, min(thi, float(tilt)))
    while True:
        dp, dt = pan - CFG["pan"], tilt - CFG["tilt"]
        dist = math.hypot(dp, dt)
        if dist <= 0.5:
            break
        if not kopf_may(who, sim_lock=who not in ("alarm",)) or (stop is not None and stop()):
            return False
        f = min(1.0, sp * 0.02 / dist)
        CFG["pan"] = CFG["pan"] + dp * f; CFG["tilt"] = CFG["tilt"] + dt * f
        time.sleep(0.02)
    CFG["pan"], CFG["tilt"] = float(pan), float(tilt)
    return True


# ---- the round (called by the patrol, part 160) ----------------------------------------------------------------------
def kopf_patrol_plan():
    """(stops, why): what the patrol drives now. [] = it does not run (why = the status)"""
    auto = (CFG.get("kopf_on") and CFG.get("kopf_round") and CFG.get("armed") and STATE.get("arm_state") == "armed"
            and protect_level() in ("watch", "full"))
    if not CFG["patrol"] and not auto:
        return [], "off"
    stops = kopf_stops()
    sv = kopf_save_active()
    if sv and stops:
        b = kopf_best()
        st = (b[0], b[1], 30.0, b[2], 3.0) if b else max(stops, key=lambda s: s[4])
        KOPF["save_why"] = sv
        return [st], "saving: stays at the most important direction"
    KOPF["save_why"] = ""
    if len(stops) < 2:
        return [], "need 2+ waypoints" if CFG["patrol"] else "off"
    return stops, ""


# ---- the camera loop gives each picture (410) ------------------------------------------------------------------------
def kopf_frame(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0):
    if not KOPF["started"]:
        KOPF["started"] = True
        threading.Thread(target=_kopf_loop, daemon=True, name="kopf").start()
    if not CFG.get("kopf_on"):
        return
    if kopf_wild_active() and STATE.get("track_what") == "motion":
        KOPF["wild_t"] = time.time()
    # wildlife: a photo now and then while an animal is followed (not in the simulation: nothing goes into the recordings)
    if kopf_wild_active() and STATE.get("track_what") == "motion" and t0 - KOPF["wild_photo_t"] >= max(3.0, float(CFG.get("kopf_wild_photo_s") or 15)):
        KOPF["wild_photo_t"] = t0
        if CFG.get("sim_on"):
            KOPF["wild_photos"] += 1
            log_event("rec", "Wildlife: photo of the animal (simulation - not saved)")
        else:
            try:
                os.makedirs(CFG["record_dir"], exist_ok=True)
                name = f"wild_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(os.path.join(CFG["record_dir"], name), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                gps_tag_jpg(os.path.join(CFG["record_dir"], name))
                KOPF["wild_photos"] += 1
                log_event("rec", f"Wildlife: photo of the animal saved: {name}")
            except Exception as e:
                log_event("rec", f"Wildlife photo: {e}"[:160])
    # Voll: turn to the alarm (movement at the edge of the picture, a warm spot of the thermal camera)
    if not (CFG.get("kopf_alarm") and CFG.get("armed") and STATE.get("arm_state") == "armed" and protect_level() == "full"):
        return
    if (STATE.get("tracking") or KOPF["turn_req"] or t0 - KOPF["turn_t"] < 4.0 or t0 - KOPF.get("tamper_t", 0.0) < 15.0
            or t0 - float(w.mt.get("bg_reset", 0.0) or 0.0) < 3.0 or not kopf_may("alarm")):
        return
    req = None
    for bx, by, bw, bh in (warm_boxes or []):
        cx, cy = bx + bw / 2.0, by + bh / 2.0
        if abs(cx - 0.5) > 0.12 or abs(cy - 0.5) > 0.15:
            req = (cx, cy, "warm spot of the thermal camera"); break
    if req is None and "prealarm" in present:
        best = None
        for t in candidates or []:
            if (t.lost or t.is_vehicle or len(t.speeds) < 3 or t0 - t.born < 1.5 or t.box[2] * t.box[3] < 0.002 * pw * ph
                    or t.box[2] * t.box[3] > 0.15 * pw * ph):
                continue
            cx = (t.box[0] + t.box[2] / 2.0) / pw; cy = (t.box[1] + t.box[3] / 2.0) / ph
            if cx < 0.18 or cx > 0.82:
                if best is None or abs(cx - 0.5) > abs(best[0] - 0.5):
                    best = (cx, cy)
        if best:
            req = (best[0], best[1], "movement at the edge of the picture")
    if req is None:
        return
    pan, tilt = kopf_pic_to_pan(req[0], req[1])
    if kopf_ignored(pan, tilt):
        return                                            # branches / road: no turn
    KOPF["turn_req"] = (pan, tilt, req[2]); KOPF["turn_t"] = t0


# ---- the background loop ---------------------------------------------------------------------------------------------
def _kopf_loop():
    while True:
        time.sleep(0.25)
        try:
            _kopf_tick()
            STATE["kopf"] = dict(kopf_state(), text=kopf_text())
        except Exception as e:
            log_event("servo", f"Automatic head movement: {type(e).__name__}: {e}"[:200])
            time.sleep(2)


def _kopf_status(s):
    KOPF["status"] = s


def _kopf_tick():
    now = time.time()
    armed = bool(CFG.get("armed"))
    pos = (round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1))
    on = bool(CFG.get("kopf_on"))
    # ---- Aus: park / back home when switched on ----
    if KOPF["armed_was"] is None:
        KOPF["armed_was"] = armed
    if armed != KOPF["armed_was"]:
        KOPF["armed_was"] = armed
        if not armed and on and CFG.get("kopf_park") and not walktest_on():
            CFG["kopf_unpark"] = list(KOPF["home"] or pos)
            CFG["kopf_parked"] = True; KOPF["back"] = None; KOPF["alarm"] = None
            log_event("servo", "Protection off: the camera looks away (privacy)")
            save_settings()
        elif armed:
            _kopf_val_reset()
            KOPF["glance_next"] = now + 120.0
            if CFG.get("kopf_parked"):
                CFG["kopf_parked"] = False
                u = CFG.get("kopf_unpark") or []
                if len(u) == 2:
                    KOPF["back"] = {"pos": (float(u[0]), float(u[1])), "since": 0.0, "why": "protection on"}
                log_event("servo", "Protection on: the camera looks back to its home position")
                save_settings()
    if CFG.get("kopf_parked"):
        if not (on and CFG.get("kopf_park")):
            CFG["kopf_parked"] = False
        elif manual_active() and not REFSCAN.get("busy"):
            CFG["kopf_parked"] = False
            log_event("servo", "Privacy ended: the camera was moved by hand")
        else:
            tgt = (float(CFG["kopf_park_pan"]), float(CFG["kopf_park_tilt"]))
            (plo, phi), (tlo, thi) = Hardware.limits()
            tgt = (max(plo, min(phi, tgt[0])), max(tlo, min(thi, tgt[1])))
            if abs(pos[0] - tgt[0]) > 0.6 or abs(pos[1] - tgt[1]) > 0.6:
                if kopf_may("park"):
                    _kopf_status("parking - the camera looks away (privacy)")
                    kopf_move(tgt[0], tgt[1], "park")
            _kopf_status("parked - the camera looks away (privacy)")
            return
    if KOPF["status"].startswith("park"):
        _kopf_status("")
    if not on:
        KOPF.update(back=None, alarm=None, turn_req=None); _kopf_status("")
        return
    tracking = bool(STATE.get("tracking"))
    if manual_active() and (KOPF["back"] or KOPF["alarm"]):
        KOPF["back"] = None; KOPF["alarm"] = None          # moved by hand: the hand decides where home is
    # ---- home: where the head stands still when nobody moves it ----
    if KOPF["home"] is None:
        KOPF["home"] = pos
    if KOPF["home_pos"] != pos:
        KOPF["home_pos"] = pos; KOPF["home_t"] = now
    if not kopf_claims() and now - KOPF["home_t"] > 8.0:
        KOPF["home"] = pos
    # ---- following started (410): remember where to come back ----
    if tracking and not KOPF["track_was"] and not KOPF["back"] and KOPF["home"] and not KOPF["round_on"]:
        KOPF["back"] = {"pos": KOPF["home"], "since": 0.0, "why": "after following"}
    KOPF["track_was"] = tracking
    # ---- walk test: where the walker was lost ----
    _kopf_walk_tick(now)
    # ---- Voll: noise (one microphone has no direction: only with an access place) ----
    _kopf_noise_tick(now)
    # ---- the overview camera steers the head (same rank as the alarm) ----
    _kopf_ov_tick(now)
    # ---- Voll: the turn the camera loop asked for ----
    rq = KOPF["turn_req"]
    if rq:
        KOPF["turn_req"] = None
        if not tracking and kopf_may("alarm"):
            home = KOPF["home"] or pos
            KOPF["alarm"] = {"t": now, "why": rq[2]}
            if not KOPF["back"]:
                KOPF["back"] = {"pos": home, "since": 0.0, "why": "after the alarm"}
            log_event("servo", f"Turning to the alarm ({rq[2]}) - pan {rq[0]:.0f} % / tilt {rq[1]:.0f} %")
            _kopf_status("turned to the alarm")
            kopf_move(rq[0], rq[1], "alarm", speed=max(60.0, float(CFG.get("patrol_speed") or 30) * 2))
            KOPF["alarm"]["t"] = time.time()
    al = KOPF["alarm"]
    if al and not tracking and time.time() - al["t"] > 6.0:          # then «back» waits kopf_return_s
        KOPF["alarm"] = None
    elif al and tracking:
        al["t"] = time.time()
    # ---- back home after following / the alarm ----
    bk = KOPF["back"]
    if bk:
        if tracking or KOPF["alarm"]:
            bk["since"] = time.time()
        elif KOPF["round_on"] or not CFG.get("kopf_return"):
            KOPF["back"] = None                          # the round goes on by itself / not wanted
        elif time.time() - bk["since"] > (2.0 if bk["why"] == "protection on" else float(CFG.get("kopf_return_s") or 20)):
            if servo_hold() or REFSCAN.get("busy"):
                KOPF["back"] = None                      # somebody took the head by hand
            else:
                _kopf_status("back to the home position")
                p = bk["pos"]
                KOPF["back"] = None
                log_event("servo", f"Back to the home position ({bk['why']}): pan {p[0]:.0f} % / tilt {p[1]:.0f} %")
                KOPF["alarm"] = {"t": time.time(), "why": "back"}       # holds the rank while driving
                try:
                    kopf_move(p[0], p[1], "alarm")
                finally:
                    KOPF["alarm"] = None
                KOPF["home"] = (round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1)); KOPF["home_t"] = time.time()
    # ---- quick look at the valuables ----
    _kopf_glance_tick(now)
    own = kopf_owner()
    if KOPF["glance"]:
        _kopf_status("quick look at the valuables")
    elif KOPF["alarm"] and KOPF["alarm"].get("why") != "back":
        _kopf_status("turned to the alarm")
    elif own == "round" and KOPF["save_why"]:
        _kopf_status("saving: stays at the most important direction")
    else:
        _kopf_status("")


def _kopf_noise_tick(now):
    a = globals().get("AUDIO")
    noisy = bool(a is not None and getattr(a, "noise_alerted", False))
    rise = noisy and not KOPF["noise_was"]
    KOPF["noise_was"] = noisy
    if not rise or not (CFG.get("kopf_alarm") and is_armed() and protect_level() == "full") or STATE.get("tracking"):
        return
    acc = [i for i in kopf_items() if i["kind"] == "access"]
    if not acc:
        if now - KOPF["noise_log"] > 600:
            KOPF["noise_log"] = now
            log_event("servo", "Noise: no direction known (one microphone, no access in «Platz einrichten») - the head stays")
        return
    i = min(acc, key=lambda i: abs(i["pan"] - CFG["pan"]))
    if abs(i["pan"] - CFG["pan"]) > 2 or abs(i["tilt"] - CFG["tilt"]) > 2:
        KOPF["turn_req"] = (i["pan"], i["tilt"], "noise - looking at the access «%s»" % i["name"])


# ---- walk test: the head follows, where it lost the walker (415) -----------------------------------------------------
def kopf_walk_follow():
    try:
        head = live_has_head()
    except Exception:
        head = False
    return bool(CFG.get("kopf_on") and CFG.get("kopf_walk") and head)


def _kopf_walk_tick(now):
    if not WALK.get("on") or not WALK.get("follow"):
        KOPF["wl_n"] = 0
        return
    hits = WALK["hits"]
    n = len(hits)
    if not n:
        return
    rel = now - WALK["t0"]
    seen = n - KOPF["wl_n"]
    if seen >= 3 and rel - hits[-1][0] > 3.0:
        hp = (WALK.get("hp") or [(CFG["pan"], CFG["tilt"])])[-1]
        lost = {"t": hits[-1][0], "nx": hits[-1][1], "ny": hits[-1][2], "m": hits[-1][3], "pan": hp[0], "tilt": hp[1]}
        WALK.setdefault("lost", []).append(lost)
        KOPF["wl_n"] = n
        log_event("sys", "Walk test: the head lost you" + (f" at about {dist_round(lost['m'])} m" if lost["m"] else "")
                  + f" (pan {lost['pan']:.0f} %)")


def kopf_walk_where(nx, pan, ref_pan):
    """a point of a picture taken at pan -> the same direction in the picture taken at ref_pan (0..1, may lie outside)"""
    hf, _vf = cam_fov()
    return nx + (float(pan) - float(ref_pan)) / kopf_pct_per_deg("pan") / max(1.0, hf)


def kopf_walk_lost_text(res, lang=None):
    L = res.get("lost") or []
    if not L:
        return []
    parts = []
    for x in L[:5]:
        side = tr("left", lang) if x["pan"] < 45 else (tr("right", lang) if x["pan"] > 55 else tr("in the middle", lang))
        parts.append((trf("about {m} m", lang, m=dist_round(x["m"])) + ", " if x.get("m") else "") + side + f" ({x['pan']:.0f} %)")
    return [trf("The head lost you {n}x: {where}. There the camera hardly sees you - try a better place or more light.", lang,
                n=len(L), where="; ".join(parts))]


# ---- quick look at the valuables -------------------------------------------------------------------------------------
def _kopf_val_dir():
    return os.path.join(DATA_DIR, "kopfauto")


def _kopf_val_reset():
    """armed now: the own references are taken anew at the first look («as you left it»)"""
    shutil.rmtree(_kopf_val_dir(), ignore_errors=True)


def kopf_valuables():
    """[{name, pan, tilt, box (x, y, w, h of the picture), src: place | refscan, pos (refscan position)}]"""
    out = []
    hf, vf = cam_fov()
    for i in kopf_items():
        if i["kind"] != "valuable":
            continue
        bw = min(0.9, max(0.08, (i["w_pan"] / kopf_pct_per_deg("pan")) / max(1.0, hf))) if i["w_pan"] else 0.3
        bh = min(0.9, max(0.08, (i["h_tilt"] / kopf_pct_per_deg("tilt")) / max(1.0, vf))) if i["h_tilt"] else 0.3
        out.append({"name": i["name"], "pan": i["pan"], "tilt": i["tilt"], "box": (0.5 - bw / 2, 0.5 - bh / 2, bw, bh), "src": "place"})
    if out:
        return out
    try:
        meta = refscan_meta() or {}
    except NameError:
        meta = {}
    pos = {int(p["i"]): p for p in meta.get("positions") or []}
    for it in meta.get("watch") or []:
        p = pos.get(int(it.get("pos", -1)))
        if p:
            out.append({"name": it["name"], "pan": p["pan"], "tilt": p["tilt"], "box": (it["x"], it["y"], it["w"], it["h"]),
                        "src": "refscan", "pos": int(p["i"]), "file": p["file"], "kind": meta.get("_kind", "day")})
    return out


def _kopf_glance_tick(now):
    if not (CFG.get("kopf_glance") and CFG.get("armed") and STATE.get("arm_state") == "armed") or KOPF["glance"]:
        if not CFG.get("armed"):
            KOPF["glance_next"] = 0.0
        return
    every = max(5.0, min(120.0, float(CFG.get("kopf_glance_min") or 15))) * 60.0 * (2.0 if kopf_save_active() else 1.0)
    if not KOPF["glance_next"]:
        KOPF["glance_next"] = now + every
    if now < KOPF["glance_next"]:
        return
    if STATE.get("tracking") or STATE.get("persons") or not kopf_may("glance") or WATCH_REF.get("w") is None:
        KOPF["glance_next"] = now + 30.0
        return
    vals = kopf_valuables()
    KOPF["glance_next"] = now + every
    if not vals:
        return
    KOPF["glance"] = "starting"
    threading.Thread(target=_kopf_glance_run, args=(vals,), daemon=True, name="kopf-glance").start()


def kopf_glance_now():
    """for tests and the button: look at the valuables now"""
    if KOPF["glance"]:
        return False, "already looking"
    vals = kopf_valuables()
    if not vals:
        return False, "no valuables (Platz einrichten or reference scan)"
    KOPF["glance"] = "starting"
    threading.Thread(target=_kopf_glance_run, args=(vals,), daemon=True, name="kopf-glance").start()
    return True, ""


def _kopf_glance_abort():
    return bool(STATE.get("tracking") or KOPF["turn_req"] or servo_hold() or REFSCAN.get("busy"))


def _kopf_glance_run(vals):
    w = WATCH_REF.get("w")
    old = (float(CFG["pan"]), float(CFG["tilt"]))
    res = {"t": time.time(), "items": [], "gone": []}
    end = time.time() + 20.0                             # started by hand: wait a moment until the head is free
    while time.time() < end and (_kopf_glance_abort() or not kopf_may("glance")):
        time.sleep(0.3)
    old = (float(CFG["pan"]), float(CFG["tilt"]))
    try:
        _kopf_status("quick look at the valuables")
        log_event("servo", "Quick look at the valuables: " + ", ".join(v["name"] for v in vals))
        groups = {}
        for v in vals:
            groups.setdefault((round(v["pan"], 1), round(v["tilt"], 1)), []).append(v)
        for (pn, tl), items in groups.items():
            KOPF["glance"] = items[0]["name"]
            if _kopf_glance_abort() or not kopf_move(pn, tl, "glance", speed=max(40.0, float(CFG.get("patrol_speed") or 30)), stop=_kopf_glance_abort):
                res["aborted"] = True; break
            for v in items:
                g = _kopf_val_check(w, v)
                if g is None:
                    continue
                res["items"].append({"name": v["name"], "gone": g[0], "score": g[1], "ref": g[2]})
                if g[0]:
                    time.sleep(1.5)                     # a second look: somebody walking past is no theft
                    g2 = _kopf_val_check(w, v)
                    if g2 is not None and g2[0]:
                        res["gone"].append(v["name"]); _kopf_val_alarm(w, v, g2[3])
    finally:
        KOPF["glance_last"] = res
        if not _kopf_glance_abort():
            kopf_move(old[0], old[1], "glance", stop=_kopf_glance_abort)
        KOPF["glance"] = ""
        log_event("servo", "Quick look at the valuables done: " + (", ".join(f"{x['name']} {'MISSING' if x['gone'] else 'ok'}" for x in res["items"]) or "no picture")
                  + (" (interrupted)" if res.get("aborted") else ""))


def _kopf_val_check(w, v):
    """(gone, score, which reference, marked picture) or None (no picture). Reuses the comparison of the reference scan."""
    cur = _refscan_grab(w, _refscan_settle(), 2)
    if cur is None:
        return None
    kind = "night" if refscan_is_dark() else "day"
    ref = None; which = "own"
    if v["src"] == "refscan":
        ref = cv2.imread(refscan_dir(REFSCAN_KINDS.get(v.get("kind", "day"), "ref"), v["file"])); which = "reference scan"
    else:
        os.makedirs(_kopf_val_dir(), exist_ok=True)
        fn = os.path.join(_kopf_val_dir(), "val_%s_%s.jpg" % (re.sub(r"[^A-Za-z0-9]+", "_", v["name"])[:30] or "x", kind))
        ref = cv2.imread(fn)
        if ref is None:
            cv2.imwrite(fn, cur, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return (False, 0.0, "reference taken now", cur)
    if ref is None:
        return None
    if cur.shape != ref.shape:
        cur = cv2.resize(cur, (ref.shape[1], ref.shape[0]))
    ch, _sh, dmap = refscan_compare_images(ref, cur)
    x, y, bw, bh = v["box"]
    gone, sc = _refscan_watch_check({"x": x, "y": y, "w": bw, "h": bh}, dmap, ch)
    img = _refscan_mark_watch(_refscan_mark(cur, ch), [{"x": x, "y": y, "w": bw, "h": bh, "name": v["name"], "gone": gone}])
    return (gone, sc, which, img)


def _kopf_val_alarm(w, v, img):
    now = time.time()
    if now - KOPF["val_cool"].get(v["name"], 0.0) < 1800 or not is_armed():
        return
    KOPF["val_cool"][v["name"]] = now
    txt = trf("Guarded thing missing: {names}", names=v["name"]) + " (" + tr("quick look of the head") + ")"
    log_event("alarm", "Quick look: guarded thing missing: " + v["name"])
    push_alert("refscan", txt)
    try:
        w.notifier.alert("{name}: " + tr("Quick look at the valuables"), txt, img)
    except Exception:
        pass


# ---- sabotage: covered or turned? (060 TamperGuard.alarm) ------------------------------------------------------------
def kopf_tamper_wanted():
    try:
        head = live_has_head()
    except Exception:
        head = False
    return bool(CFG.get("kopf_on") and CFG.get("kopf_tamper_look") and head and not KOPF["tamper"] and not servo_hold())


def _kopf_gray(w, settle):
    time.sleep(settle)
    end = time.time() + 8.0; t_ = time.time()
    while time.time() < end:
        w.raw_until = time.time() + 10
        fr = w.frame_raw
        if fr is not None and float(getattr(w, "_last_t0", 0) or 0) > t_:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY) if fr.ndim == 3 else fr
            return cv2.resize(g, (80, 60), interpolation=cv2.INTER_AREA).astype(np.float32)
        time.sleep(0.05)
    return None


def kopf_tamper_look(what, ref):
    """the head looks left and right: dark everywhere = covered; the old view found elsewhere = turned (by how much).
    Returns a short text for the push (already translated) or ''."""
    w = WATCH_REF.get("w")
    if w is None or ref is None:
        return ""
    KOPF["tamper"] = True
    p0, q0 = float(CFG["pan"]), float(CFG["tilt"])
    hf, _vf = cam_fov()
    looks = []
    ref_e = cv2.magnitude(cv2.Sobel(ref, cv2.CV_32F, 1, 0), cv2.Sobel(ref, cv2.CV_32F, 0, 1))
    try:
        settle = 1.0 + (1.5 if CFG.get("sim_on") else 0.0)
        for f in (-1.0, -0.5, 0.5, 1.0):
            ddeg = f * hf * 0.9
            p = kopf_pan_add(p0, ddeg)
            if abs(p - p0) < 1.0:
                continue
            CFG["pan"] = p
            g = _kopf_gray(w, settle)
            if g is None:
                continue
            tpl = ref[12:48, 16:64].astype(np.float32)
            sc, sh = 0.0, 0.0
            try:
                r = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
                _a, sc, _b, loc = cv2.minMaxLoc(r)
                sh = (loc[0] - 16) / 80.0 * hf             # where the old middle is in this picture
            except cv2.error:
                pass
            e = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
            flat = float(g.std()) < 7 and float(e.mean()) < 0.25 * max(1e-3, float(ref_e.mean())) if ref_e is not None else False
            looks.append({"ddeg": (p - p0) / kopf_pct_per_deg("pan"), "dark": (float(g.mean()) < 18 and float(g.std()) < 7) or flat, "sc": float(sc), "sh": sh})
    finally:
        CFG["pan"], CFG["tilt"] = p0, q0
        time.sleep(0.3)
        KOPF["tamper"] = False; KOPF["tamper_t"] = time.time()
    if not looks:
        return ""
    if all(x["dark"] for x in looks):
        return tr("the head looked left and right: dark everywhere - the lens is covered")
    best = max(looks, key=lambda x: x["sc"])
    if best["sc"] > 0.55:
        deg = best["ddeg"] + best["sh"]
        side = tr("right") if deg > 0 else tr("left")
        return trf("the head looked around: the old view is now about {deg}° to the {side} - the device was turned", deg=int(round(abs(deg))), side=side)
    if what == "covered":
        return tr("the head looked left and right: the other directions are visible - something stands right in front of the camera")
    return tr("the head looked left and right: the old view was not found - turned a lot, or the place changed")


# ---- state for the pages ---------------------------------------------------------------------------------------------
def kopf_state(lang=None):
    gl = KOPF["glance_last"]
    return {"on": bool(CFG.get("kopf_on")), "owner": kopf_owner(), "status": tr(KOPF["status"], lang) if KOPF["status"] else "",
            "parked": bool(CFG.get("kopf_parked")), "save": kopf_save_active(), "wild": kopf_wild_active(), "wild_photos": KOPF["wild_photos"],
            "glance": KOPF["glance"], "glance_next": int(KOPF["glance_next"]) if KOPF["glance_next"] else 0,
            "glance_last": gl, "estimated": servo_estimated(), "cont_est": round(float(CFG.get("cont_est", 50)), 1),
            "items": len(kopf_items()), "home": KOPF["home"]}


def kopf_text(lang=None):
    """one line for the live page / the window (empty when nothing special)"""
    s = kopf_state(lang)
    out = []
    if s["status"]:
        out.append(s["status"])
    if s["save"]:
        out.append(tr("saving: " + s["save"], lang))
    if s["wild"]:
        out.append(tr("wildlife mode", lang))
    if s["estimated"]:
        out.append(tr("position only estimated (continuous servo)", lang))
    return " · ".join(out)


# ---- «Übersicht lenkt den Kopf»: a fixed wide-angle extra camera (440) steers the head ------------------------------
# Its motion boxes -> a direction: box centre x -> angle in the overview (its field of view, cam_fov_h(spec) of the other
# part or kopf_ov_fov) + where the overview looks (kopf_ov_offset, degrees from the head's middle = pan 50 %). When that
# direction is outside the picture of the head, the head turns there (same rank as «turn to the alarm») and the AI of the
# main camera checks what it is. «Kalibrieren»: point the head at something that moves in the overview, then switch
# «kopf_ov_calib» on (or POST /api/kopf {"do": "ov_calib", "x": 0..1} for a tap on the overview picture).
for _k, _v in {"kopf_ov": "", "kopf_ov_on": True, "kopf_ov_offset": 0.0, "kopf_ov_fov": 102.0, "kopf_ov_calib": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)


def kopf_ov_cam():
    sp = str(CFG.get("kopf_ov") or "")
    if not sp:
        return None
    return next((c for c in CAMS if str(c.spec) == sp), None)


def kopf_ov_fov():
    f = globals().get("cam_fov_h")
    if callable(f):
        try:
            v = float(f(CFG.get("kopf_ov")))
            if 10.0 <= v <= 360.0:
                return v
        except Exception:
            pass
    return max(10.0, min(360.0, float(CFG.get("kopf_ov_fov") or 102.0)))


def kopf_ov_deg(cx):
    """x of the overview picture (0..1) -> degrees from the head's middle (pan 50 %), + = right"""
    return float(CFG.get("kopf_ov_offset") or 0.0) + (float(cx) - 0.5) * kopf_ov_fov()


def kopf_ov_target(c):
    """(cx, size) of the biggest moving box of the overview, or None"""
    wh = getattr(c, "wh", None)
    if not wh or not c.motion or c.streak < 2 or not c.boxes:
        return None
    x, y, w, h = max(c.boxes, key=lambda b: b[2] * b[3])
    if w * h > 0.3 * wh[0] * wh[1]:
        return None                                       # half the picture «moves»: light, wind
    return ((x + w / 2.0) / wh[0], w * h / float(wh[0] * wh[1]))


def kopf_ov_calibrate(cx=None, who="web"):
    """the head looks at the thing; cx = where it is in the overview (None: the one moving box there)"""
    c = kopf_ov_cam()
    if c is None:
        return False, "no overview camera chosen"
    if cx is None:
        t = kopf_ov_target(c)
        if t is None:
            return False, "the overview sees no movement right now"
        cx = t[0]
    head = (float(CFG["pan"]) - 50.0) / 50.0 * servo_half("pan")
    CFG["kopf_ov_offset"] = round(head - (float(cx) - 0.5) * kopf_ov_fov(), 1)
    save_settings()
    log_event("servo", f"Overview calibrated ({who}): it looks {CFG['kopf_ov_offset']:+.0f}° from the middle of the head")
    return True, ""


def _kopf_ov_tick(now):
    if CFG.get("kopf_ov_calib"):
        CFG["kopf_ov_calib"] = False
        ok, err = kopf_ov_calibrate(None, "switch")
        if not ok:
            log_event("servo", "Overview: calibration not possible - " + err)
        save_settings()
    if not (CFG.get("kopf_on") and CFG.get("kopf_ov_on") and CFG.get("armed") and STATE.get("arm_state") == "armed"):
        return
    c = kopf_ov_cam()
    if c is None or STATE.get("tracking") or KOPF["turn_req"] or now - KOPF.get("ov_t", 0.0) < 6.0 or not kopf_may("alarm"):
        return
    t = kopf_ov_target(c)
    if t is None:
        return
    pan = kopf_pan_add(50.0, kopf_ov_deg(t[0]))
    hf, _vf = cam_fov()
    if abs(pan - CFG["pan"]) < hf * 0.35 * kopf_pct_per_deg("pan") or kopf_ignored(pan, CFG["tilt"]):
        return                                            # already in the picture of the head / an ignored direction
    KOPF["ov_t"] = now
    KOPF["turn_req"] = (pan, float(CFG["tilt"]), "movement seen by the overview camera")
