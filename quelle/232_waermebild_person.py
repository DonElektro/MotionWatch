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
# ----------------------------------------------------------------------------
for _k, _v in {"thermal_person": True, "thermal_person_day": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TPERS = {"t": 0.0, "seen": 0.0, "n": 0}


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


def thermal_person_check(box):
    """-> distance in m when the warm body (x, y, w, h 0..1 of the main picture) looks like a person, else None"""
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
    for b in warm_boxes:
        d = thermal_person_check(b)
        if d is None:
            rest.append(b); continue
        found.append((b, d))
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
