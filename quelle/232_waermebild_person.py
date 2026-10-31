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
                            # adults are 1.45 m and taller. Small children (< ~5 years) and a crouching person also stay under
                            # 1.1 m - they become «animal in the thermal picture» (logged, relays / MQTT «animal»), not ignored.
FOOT = {"h": None, "t": 0.0, "busy": False}


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
    if CFG.get("thermal_person_day"):
        return True
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


def _foot_cam_h():
    """height of the camera above the ground in m: the simulator's pole (twin info «mast», fetched in the background at most
    every 60 s - never in the camera loop), else FOOT_CAM_H_M"""
    sim = bool(CFG.get("sim_on")) and str(CFG.get("source") or "").startswith("sim:")
    if not sim:
        return FOOT_CAM_H_M
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
    return FOOT["h"] or FOOT_CAM_H_M


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


def thermal_classify(box):
    """-> ("person", distance m) / ("animal", foot distance m, height m, distance at 1.7 m) / None for a warm body
    (x, y, w, h 0..1 of the main picture). A person by shape, size at 1.7 m and temperature (as before) that the foot point
    shows to be a low animal (real-reh-fusspunkt) becomes «animal». Feet hidden (grass, tent) put the foot point higher =
    farther = taller: that errs on the side of «person»."""
    d = thermal_person_check(box)
    if d is None:
        return None
    try:
        fe = foot_estimate(box)
    except Exception:
        fe = None
    TPERS["last"] = {"d_size": round(d, 2), "d_foot": round(fe[0], 2) if fe else None, "h_foot": round(fe[1], 2) if fe else None}
    if fe is not None:
        d_foot, h_foot = fe
        if d / max(0.1, d_foot) >= FOOT_RATIO_MIN and h_foot <= FOOT_ANIMAL_MAX_H_M:
            return ("animal", d_foot, max(0.0, h_foot), d)
    return ("person", d)


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


def thermal_person_feed(warm_boxes, person_boxes, present, frame, pw, ph, W, H, t0):
    """called by the camera loop (410) when the normal camera found nobody: the warm bodies that are persons become person
    boxes (in the working picture), drawn as «PERSON (THERMAL)». Returns the warm bodies that stay «warm»."""
    rest = []
    found = []
    ThermalCam.main_aspect = H / float(W)                      # (the overlay sets it too - only when the thermal picture is shown)
    animals = []
    for b in warm_boxes:
        c = thermal_classify(b)
        if c is None:
            rest.append(b); continue
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
            log_event("ai", f"Animal in the thermal picture, about {dist_round(a_[1])} m, about {a_[2]:.1f} m high - no person "
                            f"(foot point; as a 1.7 m person it would be {dist_round(a_[3])} m away)")
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
