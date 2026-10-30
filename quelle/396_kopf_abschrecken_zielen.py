#@ MoveEye – Teil 396: Abschrecken mit Ziel – beim Abschrecken (Licht, Blitzlicht, Sirene) dreht der Kopf Licht und Sirene zur Person oder zum Zelt (über den Kopf-Koordinator 162). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# aufr (Konzept-Check, Teil 317 / 162): light and siren sit on the head. When MoveEye deters (alarm light, the flashing
#   white light of «Abschreckung» 370, the siren 250), the head turns them to where it matters:
#     1. the person seen in the last 3 s (biggest box of the picture, kopf_frame of 162) - if «Folgen» already holds the
#        person in the middle, nothing to do;
#     2. otherwise the tent of «Platz einrichten» (place_info()["tent"], 317).
#   Only through the one mover of the head (KOPF["turn_req"] = the same way as «zum Alarm drehen», rank «alarm»): the hand,
#   Not-Aus, a game round and the parking keep their rank; afterwards the head goes home by itself (kopf_return).
#   Switch: «Automatic head movement» → kopf_deter_aim (583). At most once every 20 s.
# ----------------------------------------------------------------------------
CFG.setdefault("kopf_deter_aim", True)
DEFAULTS.setdefault("kopf_deter_aim", True)


def kopf_deter_target(now=None):
    """(pan %, tilt %, what) where light and siren should point now, or None"""
    now = time.time() if now is None else now
    pd = KOPF.get("pers_dir")
    if pd and now - pd[2] < 3.0:
        return (pd[0], pd[1], "person")
    try:
        pi = place_info()
    except Exception:
        return None
    tent = pi.get("tent") if pi.get("done") else None
    if tent:
        return (float(tent["pan"]), float(tent["tilt"]), "tent")
    return None


def kopf_deter_aim(why):
    """turn the head (light / siren) to the person or the tent - one request to the coordinator (162)"""
    try:
        if not (CFG.get("kopf_on") and CFG.get("kopf_deter_aim", True)) or STATE.get("tracking"):
            return False                                 # «Folgen» already looks at the person
        now = time.time()
        if now - float(KOPF.get("aim_t") or 0.0) < 20.0 or KOPF.get("turn_req") or not kopf_may("alarm"):
            return False
        tg = kopf_deter_target(now)
        if tg is None:
            return False
        p0, t0 = servo_pos()
        if abs(tg[0] - p0) < 2.0 and abs(tg[1] - t0) < 2.0:
            return False                                 # it looks there already
        KOPF["aim_t"] = now
        KOPF["turn_req"] = (tg[0], tg[1], f"{why}: light / siren to the {tg[2]}")
        return True
    except Exception as e:
        log_event("servo", f"Deterrence aim: {e}"[:160])
        return False


_kopf_frame_aim_base = kopf_frame


# wraps: kopf_frame
def kopf_frame(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0):
    if person_boxes and CFG.get("kopf_on"):              # where the biggest person is (for the aim of the deterrence)
        try:
            b = max(person_boxes, key=lambda x: float(x[2]) * float(x[3]))
            pan, tilt = kopf_pic_to_pan((b[0] + b[2] / 2.0) / pw, (b[1] + b[3] / 2.0) / ph)
            KOPF["pers_dir"] = (pan, tilt, t0)
        except Exception:
            pass
    return _kopf_frame_aim_base(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0)


_light_alarm_aim_base = light_alarm


# wraps: light_alarm
def light_alarm():
    kopf_deter_aim("alarm light")
    _light_alarm_aim_base()


_siren_alarm_aim_base = siren_alarm


# wraps: siren_alarm
def siren_alarm(kind):
    if is_armed() and CFG.get("siren_on") != "off" and kind in ("person", "warm", "sensor"):
        kopf_deter_aim("siren")
    return _siren_alarm_aim_base(kind)


_deter_react_aim_base = Deterrence.react


def _deter_react_aim(self, group, label):
    if group != "small":
        kopf_deter_aim("deterrence")
    return _deter_react_aim_base(self, group, label)


# wraps: Deterrence.react
Deterrence.react = _deter_react_aim


def kopf_deter_selftest():
    keep = {k: CFG.get(k) for k in ("kopf_on", "kopf_deter_aim")}
    kk = {k: KOPF.get(k) for k in ("pers_dir", "aim_t", "turn_req")}
    st = STATE.get("tracking")
    try:
        CFG.update(kopf_on=True, kopf_deter_aim=True); STATE["tracking"] = False
        p0, t0 = servo_pos()
        KOPF.update(pers_dir=(min(100.0, p0 + 30.0), t0, time.time()), aim_t=0.0, turn_req=None)
        ok = kopf_deter_aim("test")
        if kopf_may("alarm"):
            assert ok and KOPF["turn_req"] and "person" in KOPF["turn_req"][2], KOPF["turn_req"]
            KOPF["turn_req"] = None
            assert not kopf_deter_aim("test"), "at most once in 20 s"
        STATE["tracking"] = True; KOPF["aim_t"] = 0.0
        assert not kopf_deter_aim("test"), "following holds the person already"
        # aufr (decision Daniel): a round «Team gegen MoveEye» - no following, no automatic move; afterwards everything again
        sg, sim0, gw = globals()["sim_game"], CFG.get("sim_on"), KOPF.get("game_was", False)
        try:
            CFG["sim_on"] = True
            globals()["sim_game"] = lambda: {"mode": "mwhand", "round": "play"}
            assert kopf_game_hand() and kopf_track_blocked() and not kopf_may("round") and not kopf_may("alarm") and kopf_may("manual")
            globals()["sim_game"] = lambda: {"mode": "mwhand", "round": "end"}
            assert not kopf_game_hand() and not KOPF["game_was"]
        finally:
            globals()["sim_game"] = sg; CFG["sim_on"] = sim0; KOPF["game_was"] = gw
    finally:
        CFG.update(keep); KOPF.update(kk); STATE["tracking"] = st
    return "aim at the person (else the tent), once in 20 s, not while following; game round: following paused"


SELFTEST_EXTRA.append(("Deterrence turns light / siren to the person or the tent (162)", kopf_deter_selftest))
