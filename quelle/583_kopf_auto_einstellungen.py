#@ MoveEye – Teil 582: Einstellungen «Automatische Kopfbewegung» (Teil 162) für Web und Fenster, Servo-Art (positionell / 360° endlos), Übersichtskamera. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30: one section «Automatic head movement» in the group «Cameras & head» (web GROUPS in 530, window TK_GROUPS here).
# Web and window read the same lists (TOGGLES / SLIDERS / TEXTS). Here instead of 570 so the big lists there stay as they are.
# ----------------------------------------------------------------------------
_KS = "Automatic head movement"
TOGGLES.extend([
    (_KS, "kopf_on", "Automatic head movement (the head turns by itself - one mover at a time: hand > alarm > walk test > valuables > round > parking)"),
    (_KS, "kopf_round", "Watchful / Full: smart round - longer at the tent and the access, hardly at ignored directions (places from «Platz einrichten», otherwise the waypoints)"),
    (_KS, "kopf_alarm", "Full: turn to the alarm - movement at the edge of the picture, a warm spot of the thermal camera, a noise (only with an access as direction)"),
    (_KS, "kopf_return", "Back to the home position when the person or the alarm is gone"),
    (_KS, "kopf_park", "Off: park the camera looking away (visible privacy), back home when switched on"),
    (_KS, "kopf_glance", "Quick look at the valuables now and then, compared with the reference (missing = push)"),
    (_KS, "kopf_save", "Battery low or deep night: move less, stay at the most important direction"),
    (_KS, "kopf_walk", "Walk test: the head follows you and shows afterwards where it lost you"),
    (_KS, "kopf_tamper_look", "Sabotage: the head looks around briefly - covered or turned? (in the push text)"),
    (_KS, "kopf_ov_on", "The overview camera steers the head (a fixed wide-angle extra camera)"),
    (_KS, "kopf_ov_calib", "Calibrate the overview now: the head looks at the thing that moves in the overview (switches itself off)"),
    ("Camera / Servos", "cont_set_mid", "Continuous servo: the head looks straight ahead now - set as the middle (switches itself off)"),
])
SLIDERS.extend([
    (_KS, "kopf_round_dwell", "Smart round: stay at the tent / the access (s)", 2, 30, 1),
    (_KS, "kopf_return_s", "Back home after (s without a person)", 5, 120, 5),
    (_KS, "kopf_park_pan", "Parking position: pan (%)", 0, 100, 1),
    (_KS, "kopf_park_tilt", "Parking position: tilt (%, low = looks down)", 0, 100, 1),
    (_KS, "kopf_glance_min", "Quick look at the valuables every (minutes)", 10, 30, 1),
    (_KS, "kopf_night_from", "Deep night from (hour)", 0, 23, 1),
    (_KS, "kopf_night_to", "Deep night until (hour)", 0, 23, 1),
    (_KS, "kopf_wild_photo_s", "Wildlife: a photo of the followed animal every (s)", 5, 120, 5),
    (_KS, "kopf_ov_offset", "Overview: where it looks (degrees from the middle of the head, + = right)", -180, 180, 1),
    (_KS, "kopf_ov_fov", "Overview: field of view (degrees, if not known)", 40, 200, 1),
    ("Camera / Servos", "cont_dps", "Continuous servo: degrees per second at full speed (measure once)", 20, 600, 10),
])
TEXTS.extend([
    (_KS, "kopf_wild", "Wildlife mode: follow animals slowly, no alarm, no light, photos", "enum", "kopf_wild"),
    (_KS, "kopf_ov", "Overview camera (fixed, wide angle)", "enum", "kopf_ov"),
    ("Camera / Servos", "servo_kind", "Pan servo: kind", "enum", "servo_kind"),
])
for _k in ("kopf_wild", "kopf_ov", "servo_kind"):
    TEXT_SPECS[_k] = ("enum", _k)
SECTIONS.append(_KS)
for _g in TK_GROUPS:
    if _g[0] == "camera" and _KS not in _g[2]:
        _g[2].insert(_g[2].index("Patrol") + 1 if "Patrol" in _g[2] else 1, _KS)
TK_SUB_ICONS[_KS] = "⟲"
SIMPLE_IN_USE[_KS] = lambda: live_has_head()             # «Simple»: shown when there is a pan / tilt head
KOPF_CHOICES = {"kopf_wild": (("auto", "automatic: on with the use case or mode «Wildlife watching»"), ("on", "on"), ("off", "off")),
                "servo_kind": (("positional", "positional servo (normal, 180 / 270 / 360°)"),
                               ("continuous", "continuous rotation (360° endless) - the position is only estimated"))}

_text_choice_pairs_kopf = text_choice_pairs


def text_choice_pairs(key):                                 # + 2.98.30: automatic head movement (162)
    if key in KOPF_CHOICES:
        return [(k, tr(l)) for k, l in KOPF_CHOICES[key]]
    if key == "kopf_ov":
        out = [("", tr("none"))]
        for i, sp in enumerate(CFG.get("extra_cams") or []):
            try:
                lab = source_label(sp)
            except Exception:
                lab = str(sp)
            out.append((str(sp), f"{tr('Extra camera')} {i + 1}: {lab}"))
        cur = str(CFG.get("kopf_ov") or "")
        if cur and cur not in [p[0] for p in out]:
            out.append((cur, cur))
        return out
    return _text_choice_pairs_kopf(key)


def kopf_selftest():
    """2.98.30: angles of 180 / 360° servos, the stops of the smart round, the rank of the movers"""
    keep = {k: CFG.get(k) for k in ("pan_servo_range", "pan_limit", "kopf_on", "kopf_round", "patrol", "armed", "protect_level")}
    keep_st = STATE.get("arm_state"); keep_items = KOPF.get("_items")
    try:
        CFG.update(pan_servo_range=180, pan_limit=90)
        assert abs(kopf_pan_add(50, 45) - 75) < 0.01 and kopf_pan_add(90, 45) == 100.0
        CFG.update(pan_servo_range=360, pan_limit=180)
        assert abs(kopf_pan_add(50, 90) - 75) < 0.01 and 0.0 <= kopf_pan_add(95, 45) <= 100.0
        KOPF["_items"] = (time.time() + 60, [{"kind": "tent", "pan": 30.0, "tilt": 50.0, "w_pan": 0, "h_tilt": 0, "name": "T"},
                                            {"kind": "ignore", "pan": 80.0, "tilt": 50.0, "w_pan": 10, "h_tilt": 10, "name": "I"}])
        CFG.update(kopf_on=True, kopf_round=True, patrol=False, armed=True, protect_level="watch"); STATE["arm_state"] = "armed"
        st = kopf_stops()
        assert [s[3] for s in st] == ["T", "I"] and st[0][2] > st[1][2] * 10, st
        assert kopf_patrol_plan()[0] and kopf_ignored(80, 50) and not kopf_ignored(30, 50)
        assert kopf_may("manual") and KOPF_PRIO.index("alarm") < KOPF_PRIO.index("round")
    finally:
        CFG.update(keep); STATE["arm_state"] = keep_st; KOPF["_items"] = keep_items


SELFTEST_EXTRA.append(("Automatic head movement (180 / 360° servos, smart round, one mover)", kopf_selftest))
