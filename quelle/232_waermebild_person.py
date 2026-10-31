#@ MoveEye – Teil 232: Personen im Wärmebild (nachts, wenn die normale Kamera nichts sieht). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Wunsch Daniel): at night the normal camera often sees nobody (too dark, too far for the IR light). The thermal
# camera still sees the warm body. A warm body (ThermalCam.detect: warmer than the scene by thermal_delta, moving unless
# thermal_need_motion is off, in the zones, seen in 3 of 5 pictures) counts as a PERSON when it also
#   - stands upright (taller than wide, as a person),
#   - has the size of a person at its distance (1.7 m tall, 0.2 … 1.3 m wide - from the field of view of the camera),
#   - is warmer than the background but not hot like a fire or an engine (only with a camera that gives °C).
# It then goes into the same person / alarm logic (push, recording, siren, zones of the recording) as «Person (Wärmebild)».
# Option thermal_person (default on) - only at night (or by day too: thermal_person_day). Needs a thermal camera.
# 2.98.22 (Wunsch Daniel: «das Wärmebild soll mitlaufen»): by day too is now the default, so the thermal camera always
# runs along as soon as one is chosen - also with the overlay and the warm alarm off. Older settings are switched once
# (thermal_migrate, called by 040); who switches «… by day too» off again keeps it off.
# real-reh-fusspunkt (31.10.2026, Fehlalarm Daniel): a roe deer or a fox coming straight at the camera at night is narrow and
# looks «upright» in the thermal picture; with the 1.7 m of a person it seemed far away and so of person size -> push «Person».
# Now the distance is estimated a second time from the FOOT POINT (lower edge of the box, flat ground): the camera height
# (simulator: its pole «mast» from the twin info, else FOOT_CAM_H_M) and the tilt of the head (servo; simulator: the real
# head angle head_deg minus its fixed 6° down, main.gd want_tilt) give the distance of the feet, and with it the real height
# of the thing. Do both distances disagree strongly (FOOT_RATIO_MIN) and is the thing clearly lower than a standing person
# (FOOT_ANIMAL_MAX_H_M), it is reported as an animal («ANIMAL (THERMAL)», present «animal») and not as a person. Feet near
# the horizon or cut off at the picture edge: no foot estimate, everything as before. Self-test: 417 (foot_selftest).
# Decision Daniel (31.10.2026, third round): «animal» ONLY for a really FLAT warm body, everything upright stays as before:
#   - upright boxes (h/w >= 1.3, thermal_person_check) are persons exactly as before - also a roe deer straight from the
#     front, a child, a crouching person («im Zweifel Person»),
#   - a flat warm body (failed the upright check, before only «warm») becomes «animal» when: it is night / low light, the
#     foot point works (FOOT_RATIO_MIN, FOOT_ANIMAL_MAX_H_M), real height / real width <= FLAT_MAX_ASP, it did not stand
#     up in the last FOOT_HIST_S seconds, and 3 such pictures over >= 1 s (until then «warm» only),
#   - «Person?» (weak_person_feed): a flat box at the ground (w/h > WEAK_FLAT) that the AI of MoveEye calls a person with at
#     least WEAK_AI_MIN (the normal AI threshold stays) AND a movement track or a warm body confirms it -> a person (alarm,
#     «PERSON?»). It wins over «animal»: a warm body under a «Person?» never becomes an animal.
# Camera height: CFG «cam_height» («Höhe der Kamera (m)» in «Platz einrichten», 537 / 582, default 1.6 m). Connected to the
# simulator, its pole («Höhe der Kamera», 3D-4.x) has priority (the simulated camera really is that high); the field is for
# the real device.
# ----------------------------------------------------------------------------
for _k, _v in {"thermal_person": True, "thermal_person_day": True, "thermal_mig22": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TPERS = {"t": 0.0, "seen": 0.0, "n": 0, "animal_seen": 0.0, "animals": 0, "last": None}
# ---- foot point (real-reh-fusspunkt) - the limits and why ----------------------------------------------------------------
FOOT_CAM_H_M = 1.6          # camera height when nothing is known: the simulator's head (main.gd HEAD_H 1.6 m); a camping tripod
                            # is about 1.2 … 1.8 m. Too high a guess makes things look taller (= the safe side, more «person»).
FOOT_MIN_DEP_DEG = 4.0      # the feet must be at least 4° below the horizon. Thermal-90 (MI0802, 80 x 62 px, 90° x 67°,
                            # datasheet Waveshare / Meridian) = about 1.1° per pixel; with ±1° servo play the foot distance is
                            # then good to about ±30 %, enough to tell 1.7 m from 0.9 m (factor 1.9). Above it: as before.
FOOT_RATIO_MIN = 1.5        # «strongly different»: the 1.7 m estimate is at least 1.5 x the foot distance (a person stays near
                            # 1.0; ±30 % error of height / tilt keeps a real person below 1.5)
FOOT_ANIMAL_MAX_H_M = 1.1   # «clearly lower than a person»: roe deer shoulder height 0.6 … 0.9 m (head up to about 1.1 m), fox
                            # 0.35 … 0.4 m (about 0.5 m with the head) - Wildtier Schweiz / Hespeler «Rehwild heute»; standing
                            # adults are 1.45 m and taller. Small children and a crouching person are lower too - they stay
                            # persons: upright (thermal_person_check) or not flat (FLAT_MAX_ASP).
FLAT_MAX_ASP = 0.8          # «really flat» (Daniel: wider than high): real height / real width from the side. Roe deer: shoulder
                            # 0.6 … 0.9 m, head-body 0.95 … 1.35 m (Wildtier Schweiz) -> 0.5 … 0.8 (head held high up to ~0.9:
                            # then «warm», not animal); fox: shoulder 0.35 … 0.4 m, head-body 0.6 … 0.9 m (+ tail 0.35 … 0.45)
                            # -> 0.3 … 0.6. A crouching person (1.0 / 0.55 m = 1.8) and any child standing (> 3) are far above.
WEAK_AI_MIN = 0.15          # «Person?»: the raw person score of the AI (crawling figures of the simulator reach 0.18 at most,
                            # REAL_KRIECHENDE.md; the normal threshold ai_conf stays for everything else)
WEAK_FLAT = 1.5             # «flat box at the ground»: AI box width / height above 1.5 (crawling / lying, a standing person ~0.4)
WEAK_AGE_S = 2.5            # the AI runs only now and then: its weak boxes count for 2.5 s
FOOT_HIST_S = 4.0           # «does not stand up over the last pictures»: what was seen of it in the last 4 s
FOOT_NEED_N, FOOT_NEED_S = 3, 1.0   # an animal needs 3 animal-like pictures over at least 1 s (the thermal camera: 3 of 5 anyway)
FOOT = {"h": None, "t": 0.0, "busy": False, "hist": deque(maxlen=200)}
# ---- real-erk-e1 (Erkennungstest: a car on 20 m gave a push «Person (Wärmebild)» by day) - the limits and why --------------
# A moving car in the thermal picture: the movement mask cuts its hot parts (bonnet, grille, tyres, exhaust) into narrow
# pieces that look «upright». Now a warm body is NO thermal person when
#   - it is followed over the thermal pictures (TVEH chains) and as a 1.7 m person it would run faster than TV_PERSON_MAX_MS, or
#   - it is a wide (real width / height >= TV_WIDE), very warm body that drives faster than TV_CAR_MS (as a 1.5 m high car),
#     and the pieces near it (same height band) for TV_HOLD_S,
#   - the normal camera / the AI sees a vehicle or an animal on it (418 fixp_veto: vehicle track, car / truck …, animal of
#     the AI or an animal track = «Tier vor Person»).
# Only while the head stands still (a turning head makes everything «drive»).
TV_PERSON_MAX_MS = 10.0     # m/s: a sprinter reaches 9 - 10, a person running away 4 - 6; a half hidden person (only the upper
                            # half warm: 2 x too far as 1.7 m) running 5 m/s stays below. A car piece at 20 m (0.6 m tyre seen as
                            # 1.7 m = 57 m away) at 30 km/h is about 23 m/s.
TV_WIDE = 1.6               # «breit»: a car from the side 4.5 x 1.5 m = 3; a person, also two side by side walking, is below
TV_CAR_MS = 4.0             # m/s (14 km/h) for a wide body seen as 1.5 m high: faster than walking / jogging persons in a group
TV_HOT_C = 8.0              # «sehr warm» with a camera in °C: at least 8 °C over the scene (a body 3 - 6 °C through clothes);
                            # without °C (8-bit picture) only the shape and the speed count
TV_HOLD_S = 2.0
TVEH = {"chains": [], "veh": [], "ts": 0.0}
for _k, _v in {"cam_height": FOOT_CAM_H_M}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)


def thermal_migrate(cfg_in):
    """once per settings file: the thermal camera runs along by day too (2.98.22)"""
    if not isinstance(cfg_in, dict) or cfg_in.get("thermal_mig22"):
        return []
    CFG["thermal_mig22"] = True
    if cfg_in.get("thermal_person_day") is False:
        CFG["thermal_person_day"] = True
        return ["thermal camera runs along by day too"]
    return []


def thermal_person_active():
    """thermal persons are looked for now: the option is on, a thermal camera is chosen, and it is night (or by day too)"""
    if not CFG.get("thermal_person") or not CFG.get("thermal_source") or not CFG.get("detection_on"):
        return False
    if CFG.get("thermal_person_day") or STATE.get("fog"):
        return True                                       # 411: in fog the camera sees little - the thermal camera by day too
    try:
        return bool(is_dark() or STATE.get("lowlight"))
    except Exception:
        return bool(STATE.get("lowlight"))


def _thermal_temps(box):
    """(warm body, background) in °C when the thermal camera gives temperatures (float picture), else None"""
    th = THERMAL
    fr = th.frame if th is not None else None
    if fr is None or fr.dtype == np.uint8:
        return None
    try:
        f = th.crop(fr).astype(np.float32)
        if f.ndim == 3:
            f = f.mean(axis=2)
        H, W = f.shape[:2]
        x, y, w, h = box
        x0, y0 = max(0, int(x * W)), max(0, int(y * H))
        x1, y1 = min(W, int(math.ceil((x + w) * W))), min(H, int(math.ceil((y + h) * H)))
        reg = f[y0:y1, x0:x1]
        if reg.size < 2:
            return None
        return float(np.percentile(reg, 80)), float(np.median(f))
    except (ValueError, TypeError, cv2.error):
        return None


def cam_height_cfg():
    """the field «Höhe der Kamera (m)» of «Platz einrichten» (0.2 … 10 m, else the default 1.6 m)"""
    try:
        v = float(CFG.get("cam_height") or FOOT_CAM_H_M)
    except (TypeError, ValueError):
        return FOOT_CAM_H_M
    return v if 0.2 <= v <= 10.0 else FOOT_CAM_H_M


def cam_height_info():
    """for the pages: {"m": field, "sim": pole of the simulator or None, "used": what the foot point uses}"""
    h = _foot_cam_h()
    sim = FOOT["h"] if bool(CFG.get("sim_on")) and str(CFG.get("source") or "").startswith("sim:") else None
    return {"m": round(cam_height_cfg(), 2), "sim": round(sim, 2) if sim else None, "used": round(h, 2)}


def _foot_cam_h():
    """height of the camera above the ground in m: connected to the simulator its pole (twin info «mast», fetched in the
    background at most every 60 s - never in the camera loop) has priority, else the field «Höhe der Kamera» (cam_height)"""
    sim = bool(CFG.get("sim_on")) and str(CFG.get("source") or "").startswith("sim:")
    if not sim:
        return cam_height_cfg()
    now = time.time()
    if now - FOOT["t"] > 60.0 and not FOOT["busy"]:
        FOOT["t"] = now; FOOT["busy"] = True

        def _get():
            try:
                m = (sim_twin_info() or {}).get("mast")
                FOOT["h"] = float(m) if m is not None and 0.2 <= float(m) <= 10.0 else None
            except Exception:
                pass
            finally:
                FOOT["busy"] = False
        threading.Thread(target=_get, daemon=True).start()
    return FOOT["h"] or cam_height_cfg()


def _foot_pitch_deg():
    """where the main camera looks up (+) / down (-) in degrees: the wide camera of the simulator its mount (tilt_deg, + the
    head with tilt_follow), the head camera the servo; in the simulator the real head (head_deg) and its fixed 6° down"""
    src = str(CFG.get("source") or "")
    sim = bool(CFG.get("sim_on")) and src.startswith("sim:")
    head = servo_pos_deg()[1]
    if sim and isinstance(SIM.get("head"), list) and len(SIM["head"]) >= 2:
        try:
            head = float(SIM["head"][1])
        except (TypeError, ValueError):
            pass
    if sim and src != "sim:0":
        cam = next((c for c in (SIM.get("info") or {}).get("cameras") or [] if str(c.get("id")) == src[4:]), None)
        if cam and cam.get("tilt_deg") is not None:
            return float(cam["tilt_deg"]) + ((head - 6.0) if cam.get("tilt_follow") else 0.0)
    return head - 6.0 if sim else head


def foot_estimate(box, cam_h=None, pitch=None, vf=None):
    """(distance of the feet in m, real height in m) of a thing standing on flat ground, from the lower / upper edge of its
    box (x, y, w, h 0..1 of the main picture) - or None when the feet are cut off or too near the horizon"""
    x, y, w, h = box
    if h <= 0 or y + h > 0.985 or y < 0.01:
        return None                                           # cut off at the picture edge: feet / head unknown
    cam_h = _foot_cam_h() if cam_h is None else float(cam_h)
    pitch = _foot_pitch_deg() if pitch is None else float(pitch)
    vf = erk_vfov() if vf is None else float(vf)
    k = math.tan(math.radians(vf) / 2.0)
    dep_b = math.atan((y + h - 0.5) * 2.0 * k) - math.radians(pitch)   # how far below the horizon the feet are
    if dep_b < math.radians(FOOT_MIN_DEP_DEG):
        return None
    dist = cam_h / math.tan(dep_b)
    dep_t = math.atan((y - 0.5) * 2.0 * k) - math.radians(pitch)
    return dist, cam_h - dist * math.tan(dep_t)


def _foot_night():
    try:
        return bool(is_dark() or STATE.get("lowlight"))
    except Exception:
        return bool(STATE.get("lowlight"))


def foot_shape(box, fe):
    """real height / real width of a box (both from the foot distance) - small = flat like an animal from the side"""
    hf = cam_fov()[0]
    width_m = box[2] * 2.0 * fe[0] * math.tan(math.radians(hf) / 2.0)
    return max(0.0, fe[1]) / max(0.05, width_m)


def foot_decide(box, d, fe, night, t0, hist, maybe=False, vf=None):
    """the decision of thermal_classify, without the camera (self-test 417): -> ("person", d) / ("animal", foot m, height m,
    distance at 1.7 m) / ("wait", None) / None (only warm, as before). d = thermal_person_check (upright person) or None;
    maybe = a «Person?» of the AI lies on it. hist = deque of the last observations {t, cx, fy, low, person}."""
    x, y, w, h = box
    cx, fy = x + w / 2.0, y + h
    same = [o for o in hist if t0 - o["t"] <= FOOT_HIST_S and abs(o["cx"] - cx) < 0.12 and abs(o["fy"] - fy) < 0.15]
    if d is not None:                                           # upright: a person, as before
        hist.append({"t": t0, "cx": cx, "fy": fy, "low": False, "person": True})
        return ("person", d)
    low = False
    if fe is not None and night and not maybe:
        vf = erk_vfov() if vf is None else vf
        d_size = PERSON_H_M / (2.0 * max(1e-3, h) * math.tan(math.radians(vf) / 2.0))
        low = (d_size / max(0.1, fe[0]) >= FOOT_RATIO_MIN and fe[1] <= FOOT_ANIMAL_MAX_H_M and foot_shape(box, fe) <= FLAT_MAX_ASP)
    stood = any(o["person"] for o in same)                     # it stood up in the last seconds: no animal
    hist.append({"t": t0, "cx": cx, "fy": fy, "low": low, "person": False})
    if not low or stood:
        return None
    lows = [o for o in same if o["low"]] + [hist[-1]]
    if len(lows) >= FOOT_NEED_N and t0 - min(o["t"] for o in lows) >= FOOT_NEED_S:
        vf = erk_vfov() if vf is None else vf
        return ("animal", fe[0], max(0.0, fe[1]), PERSON_H_M / (2.0 * max(1e-3, h) * math.tan(math.radians(vf) / 2.0)))
    return ("wait", None)


def thermal_classify(box, t0=None, maybe=False):
    """-> ("person", distance m) / ("animal", …) / ("wait", None) / None for a warm body (x, y, w, h 0..1 of the main picture):
    upright as before (thermal_person_check), flat at night with the foot point = animal (real-reh-fusspunkt)"""
    d = thermal_person_check(box)
    fe = None
    if d is None:
        try:
            fe = foot_estimate(box)
        except Exception:
            fe = None
    TPERS["last"] = {"d_size": round(d, 2) if d else None, "d_foot": round(fe[0], 2) if fe else None, "h_foot": round(fe[1], 2) if fe else None}
    return foot_decide(box, d, fe, _foot_night(), time.time() if t0 is None else t0, FOOT["hist"], maybe)


def _ov(a, b):
    """two boxes (x, y, w, h, same units) overlap: intersection / smaller area"""
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])); iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return ix * iy / max(1e-9, min(a[2] * a[3], b[2] * b[3]))


def weak_person_check(ab, tracks_n, warm_n, fe):
    """«Person?» for one weak AI box ab = (x, y, w, h, conf) 0..1: flat, at the ground, confirmed by movement or warmth"""
    x, y, w, h, cf = ab
    if cf < WEAK_AI_MIN or h <= 0 or (w / h) * (1.0 / max(1e-3, float(ThermalCam.main_aspect))) <= WEAK_FLAT:
        return False                                            # (w / h in real pixels of the picture)
    if fe is not None and fe[1] > FOOT_ANIMAL_MAX_H_M + 0.3:
        return False                                            # not at the ground (a flat thing high up)
    return any(_ov(ab[:4], b) > 0.3 for b in list(tracks_n) + list(warm_n))


def weak_person_feed(ai, tracks, warm_boxes, person_boxes, present, frame, pw, ph, W, H, t0, veto=()):
    """410, when nobody was found: the weak person boxes of the AI (180, below ai_conf) that are flat at the ground and confirmed
    by a movement track or the thermal picture become «PERSON?» (person boxes = the normal person / alarm logic).
    Returns the «Person?» boxes 0..1 (a warm body under one never becomes an animal).
    real-erk-e1: not where the AI sees an animal (or an animal track is) - «Tier vor Person» (418 fixp_veto)."""
    wk = getattr(ai, "weak", None) or []
    STATE["person_maybe"] = 0                                   # /api/state: how many «Person?» in this picture
    if not wk or t0 - float(getattr(ai, "weak_t", 0.0)) > WEAK_AGE_S:
        return []
    ThermalCam.main_aspect = H / float(W)
    tn = [(t.box[0] / pw, t.box[1] / ph, t.box[2] / pw, t.box[3] / ph) for t in tracks if getattr(t, "box", None)]
    out = []
    for ab in wk:
        try:
            fe = foot_estimate(ab[:4])
        except Exception:
            fe = None
        if weak_person_check(ab, tn, warm_boxes or [], fe) and not any(_ov(ab[:4], v[:4]) > 0.3 for v in veto if v[4] == "animal"):
            out.append(ab)
    for bx, by, bw, bh, cf in out:
        person_boxes.append((int(bx * pw), int(by * ph), max(1, int(bw * pw)), max(1, int(bh * ph))))
        p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
        cv2.rectangle(frame, p1, p2, (60, 0, 255), 3)
        cv2.putText(frame, f"PERSON? (AI {cf:.2f})", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 0, 255), 2)
    STATE["person_maybe"] = len(out)
    if out:
        present.add("person")
        if t0 - TPERS.get("weak_seen", 0.0) > 10.0:
            TPERS["weak_n"] = TPERS.get("weak_n", 0) + 1
            log_event("person", f"Person? lying / crawling - AI {max(o[4] for o in out):.2f} (below the normal threshold) + "
                                f"movement / warmth at the same place")
        TPERS["weak_seen"] = t0
    return [o[:4] for o in out]


def thermal_person_check(box):
    """-> distance in m when the warm body (x, y, w, h 0..1 of the main picture) looks like a person by shape, size at 1.7 m and
    temperature, else None (the foot point comes after it: thermal_classify)"""
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return None
    asp = (h / w) * float(ThermalCam.main_aspect)             # height / width in real pixels of the main picture
    if not (1.3 <= asp <= 5.5):
        return None                                           # lying, round or a long thin thing: no standing person
    hf, vf = cam_fov()
    vf = erk_vfov()
    d = PERSON_H_M / (2.0 * h * math.tan(math.radians(vf) / 2.0))
    if not (1.0 <= d <= 80.0):
        return None
    width_m = w * 2.0 * d * math.tan(math.radians(hf) / 2.0)
    if not (0.2 <= width_m <= 1.3):
        return None                                           # too broad for a person at that distance (cow, car bonnet)
    tt = _thermal_temps(box)
    if tt is not None:
        body, bg = tt
        if body - bg < 3.0 or body > 45.0:
            return None                                       # hardly warmer than the ground / hot like a fire or an engine
    return d


def _tv_speed(ch, now):
    """(picture widths per second, mean height, mean width) of a chain over its last 2 s - or None (too short)"""
    pts = [p for p in ch["pts"] if now - p[0] <= 2.0]
    if len(pts) < 3 or pts[-1][0] - pts[0][0] < 0.4:
        return None
    return ((pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0]), sum(p[4] for p in pts) / len(pts), sum(p[3] for p in pts) / len(pts))


def thermal_vehicle_step(boxes, ts, hf, vf, asp, temps=None):
    """follow the warm bodies over the thermal pictures (ts = time of the thermal picture) -> the boxes that are a vehicle.
    asp = picture height / width (main picture), temps(box) -> (body, scene) °C or None. Without the camera (self-test)."""
    if ts != TVEH["ts"]:
        TVEH["ts"] = ts
        for b in boxes:
            cx, cy = b[0] + b[2] / 2.0, b[1] + b[3] / 2.0
            near = [c for c in TVEH["chains"] if ts - c["pts"][-1][0] <= 1.0 and abs(c["pts"][-1][2] - cy) < 0.15
                    and abs(c["pts"][-1][1] - cx) < 0.25 + b[2]]
            ch = min(near, key=lambda c: abs(c["pts"][-1][1] - cx), default=None) if near else None
            if ch is None or ch["pts"][-1][0] == ts:
                ch = {"pts": deque(maxlen=20), "veh": 0.0}; TVEH["chains"].append(ch)
            ch["pts"].append((ts, cx, cy, b[2], b[3]))
            sp = _tv_speed(ch, ts)
            if sp is None:
                continue
            vx, mh, mw = sp
            k = 2.0 * math.tan(math.radians(hf) / 2.0)
            v_person = abs(vx) * k * PERSON_H_M / (2.0 * max(1e-3, mh) * math.tan(math.radians(vf) / 2.0))
            v_car = abs(vx) * k * 1.5 / (2.0 * max(1e-3, mh) * math.tan(math.radians(vf) / 2.0))
            wide = (mw / max(1e-3, mh)) / max(1e-3, asp) >= TV_WIDE
            tt = temps(b) if temps else None
            hot = tt is None or tt[0] - tt[1] >= TV_HOT_C
            if (mh / max(1e-3, mw)) * asp >= 1.0 and v_person >= TV_PERSON_MAX_MS:
                ch["veh"] = ts                                  # upright piece far too fast for a person
            elif wide and hot and v_car >= TV_CAR_MS:
                ch["veh"] = ts; TVEH["veh"].append((ts, cx, cy))    # a wide hot body that drives: the pieces near it too
        TVEH["chains"] = [c for c in TVEH["chains"] if ts - c["pts"][-1][0] <= 1.5][-8:]
        TVEH["veh"] = [v for v in TVEH["veh"] if ts - v[0] <= TV_HOLD_S]
    out = []
    for b in boxes:
        cx, cy = b[0] + b[2] / 2.0, b[1] + b[3] / 2.0
        ch = next((c for c in TVEH["chains"] if c["pts"][-1][0] == TVEH["ts"] and abs(c["pts"][-1][1] - cx) < 1e-6 and abs(c["pts"][-1][2] - cy) < 1e-6), None)
        if (ch and TVEH["ts"] - ch["veh"] <= TV_HOLD_S) or any(abs(v[2] - cy) < 0.15 and abs(v[1] - cx) < 0.25 for v in TVEH["veh"]):
            out.append(b)
    return out


def thermal_person_feed(warm_boxes, person_boxes, present, frame, pw, ph, W, H, t0, maybe_boxes=(), veto=()):
    """called by the camera loop (410) when the normal camera found nobody: the warm bodies that are persons become person
    boxes (in the working picture), drawn as «PERSON (THERMAL)». Returns the warm bodies that stay «warm».
    real-erk-e1: a vehicle (fast / wide and hot in the thermal picture, or the camera / AI sees one there) or an animal of the
    AI on it is no person (veto from 418 fixp_veto)."""
    rest = []
    found = []
    ThermalCam.main_aspect = H / float(W)                      # (the overlay sets it too - only when the thermal picture is shown)
    animals = []
    vehicles = []
    try:
        if fixp_head_still(t0) >= 1.5:
            hf, vf = cam_fov()
            vehicles = thermal_vehicle_step(warm_boxes, float(getattr(THERMAL, "t", t0) or t0), hf, erk_vfov(), ThermalCam.main_aspect, _thermal_temps)
        else:
            TVEH["chains"] = []; TVEH["veh"] = []
    except Exception:
        vehicles = []
    for b in warm_boxes:
        if b in vehicles or any(_ov(b, v[:4]) > 0.3 for v in veto if v[4] == "vehicle"):
            rest.append(b)                                    # a vehicle: only warm (the warm alarm, if on, as before)
            p1 = (int(b[0] * W), int(b[1] * H)); p2 = (int((b[0] + b[2]) * W), int((b[1] + b[3]) * H))
            cv2.rectangle(frame, p1, p2, (200, 200, 200), 2)
            cv2.putText(frame, "VEHICLE (THERMAL)", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
            if t0 - TPERS.get("veh_seen", 0.0) > 10.0:
                log_event("ai", "Vehicle in the thermal picture (fast / wide and hot, or the camera sees one) - no person")
            TPERS["veh_seen"] = t0
            continue
        if any(_ov(b, v[:4]) > 0.3 for v in veto if v[4] == "animal"):
            rest.append(b); present.add("animal"); continue   # Tier vor Person: the AI sees an animal there
        c = thermal_classify(b, t0, any(_ov(b, m) > 0.3 for m in maybe_boxes))
        if c is None or c[0] == "wait":
            rest.append(b); continue                          # «wait»: maybe an animal - a few more pictures (only warm meanwhile)
        if c[0] == "animal":
            animals.append((b, c[1], c[2], c[3])); rest.append(b); continue   # still a warm body (the warm alarm, if on, as for any animal)
        found.append((b, c[1]))
    if animals:
        for (bx, by, bw, bh), d_, h_, _ds in animals:
            p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
            cv2.rectangle(frame, p1, p2, (0, 200, 255), 2)
            cv2.putText(frame, f"ANIMAL (THERMAL) ~{dist_round(d_)}m {h_:.1f}m high", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)
        present.add("animal")
        if t0 - TPERS["animal_seen"] > 10.0:                  # a new appearance (not every picture)
            TPERS["animals"] += 1
            a_ = min(animals, key=lambda a: a[1])
            try:                                              # for tuning FLAT_MAX_ASP with real nights (shape, box)
                shp = f", shape h/w {foot_shape(a_[0], (a_[1], a_[2])):.2f}, box {tuple(round(float(q), 3) for q in a_[0])}"
            except Exception:
                shp = ""
            log_event("ai", f"Animal in the thermal picture, about {dist_round(a_[1])} m, about {a_[2]:.1f} m high - no person "
                            f"(foot point; as a 1.7 m person it would be {dist_round(a_[3])} m away{shp})")
        TPERS["animal_seen"] = t0
    if not found:
        return rest
    for (bx, by, bw, bh), d in found:
        pb = (int(bx * pw), int(by * ph), max(1, int(bw * pw)), max(1, int(bh * ph)))
        person_boxes.append(pb)
        p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
        cv2.rectangle(frame, p1, p2, (60, 0, 255), 3)
        cv2.putText(frame, f"PERSON (THERMAL) ~{dist_round(d)}m", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 0, 255), 2)
        try:
            walktest_hit(bx + bw / 2.0, by + bh, d, "thermal", "th", t0)
        except Exception:
            pass
    present.add("person")
    best = min(found, key=lambda x: x[1])
    erk_note_thermal(best[1], t0)
    if t0 - TPERS["seen"] > 10.0:                             # a new appearance (not every picture)
        STATE["detections_total"] = STATE.get("detections_total", 0) + 1
        log_event("person", f"Person in the thermal picture, about {dist_round(best[1])} m (the normal camera sees nobody)")
    TPERS["seen"] = t0; TPERS["n"] = len(found)
    return rest
