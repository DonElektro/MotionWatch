#@ MoveEye – Teil 317: «Platz einrichten» – ein Assistent nach dem Hinstellen: Rundblick, Vorschläge, Zelt / Zugang / Wertsachen / Ignorieren, Platz-Datensatz (place_items / place_info). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30 (Wunsch Daniel, 29.10.2026): «MoveEye hinstellen → Platz einrichten». One assistant that only DRIVES the parts that
# exist already - it duplicates none of them:
#   * the scan: the head drives its whole pan range in 2-3 tilt rows (the grid of the reference scan 315, its grab
#     function), per direction a photo + ~10 s observation (what moves, what the AI sees) -> suggestions
#   * the photos become the reference of the reference scan (315, day or night) - so «Velo fehlt» in the morning works
#   * the result screen: the panorama of 316 (pano_canvas) with the suggestions; the operator marks
#     «Mein Zelt / Wohnmobil», «Zugang / Weg», «Wertsachen», «Ignorieren»
#   * apply: zones (030; anchored by direction, they stay on their place when the head turns), patrol waypoints (020 / 160),
#     guarded things of the reference scan (315), then the walk test (415)
#   * the result is kept as the «place» record: place_items() / place_info() below - read by other parts (head automation).
# Directions: pan / tilt in percent of the servos like CFG["pan"] / CFG["tilt"] (0 … 100, 50 = middle); a box on the panorama
# is kept as its middle (pan, tilt) and its size (w_pan, h_tilt) in the same percent.
# ----------------------------------------------------------------------------
PLACE_KINDS = ("tent", "access", "public_path", "valuable", "ignore")
PLACE = {"busy": "", "step": 0, "n": 0, "phase": "", "msg": "", "stop": False, "t0": 0.0, "eta": 0.0, "night": False,
         "scan": None, "rec": None, "loaded": False}
_PLACE_LOCK = threading.Lock()


def place_dir(*p):
    return os.path.join(DATA_DIR, "place", *p)


def _place_load():
    """the place record from the data folder (once; later from memory)"""
    if PLACE["loaded"]:
        return PLACE["rec"]
    PLACE["loaded"] = True
    try:
        with open(place_dir("place.json"), encoding="utf-8") as f:
            d = json.load(f)
        PLACE["rec"] = d if isinstance(d, dict) else None
    except (OSError, ValueError):
        PLACE["rec"] = None
    return PLACE["rec"]


def _place_save(rec):
    os.makedirs(place_dir(), exist_ok=True)
    tmp = place_dir("place.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False)
    os.replace(tmp, place_dir("place.json"))
    PLACE["rec"] = rec; PLACE["loaded"] = True


def place_items():
    """the marked things of the place: [{"kind": "tent"|"access"|"public_path"|"valuable"|"ignore", "pan": %, "tilt": %,
    "w_pan": %, "h_tilt": %, "name": str}] - pan / tilt = the middle of the box in servo percent (like CFG["pan"]),
    w_pan / h_tilt = its size in the same percent. [] when the place was never set up. A copy: changing it changes nothing."""
    rec = _place_load() or {}
    out = []
    for it in rec.get("items") or []:
        try:
            out.append({"kind": str(it["kind"]), "pan": float(it["pan"]), "tilt": float(it["tilt"]), "w_pan": float(it["w_pan"]),
                        "h_tilt": float(it["h_tilt"]), "name": str(it.get("name") or "")})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def place_info():
    """a summary of the place for other parts: {"done": bool, "t": time it was set up (or None), "n": number of items,
    "kinds": {kind: count}, "tent": the first tent item or None, "home": {"pan", "tilt"} (where the head should rest:
    towards the tent, else the middle of the scan), "pan_range_deg": what the head can see (servo + lens), "servo_deg",
    "fov": [h, v] degrees, "lat", "lon" (when known), "public_path_report_only": bool, "night_ref": bool,
    "new_position": True when MoveEye stands somewhere else than when the place was set up (GPS ~1 km)}"""
    rec = _place_load() or {}
    items = place_items()
    kinds = {}
    for it in items:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    tent = next((dict(it) for it in items if it["kind"] == "tent"), None)
    home = {"pan": tent["pan"], "tilt": tent["tilt"]} if tent else dict(rec.get("home") or {"pan": 50.0, "tilt": float(CFG.get("refscan_tilt_mid", 50))})
    try:
        hf, vf = cam_fov()
    except Exception:
        hf, vf = 66.0, 41.0
    sd = 2.0 * min(servo_half("pan"), max(5.0, float(CFG.get("pan_limit") or 180)))
    return {"done": bool(rec.get("t")), "t": rec.get("t"), "n": len(items), "kinds": kinds, "tent": tent, "home": home,
            "pan_range_deg": round(min(360.0, sd + hf)), "servo_deg": round(sd), "fov": [round(hf, 1), round(vf, 1)],
            "lat": rec.get("lat"), "lon": rec.get("lon"), "public_path_report_only": bool(rec.get("public_report", True)),
            "night_ref": bool(rec.get("night_ref")), "new_position": place_new_position()}


def place_new_position():
    """the device stands somewhere else than when the place was set up (GPS / the location from the phone, ~1 km)"""
    rec = _place_load() or {}
    try:
        lat, lon = float(rec.get("lat")), float(rec.get("lon"))
        if not (lat or lon):
            return False
        return abs(lat - float(CFG["latitude"])) > 0.01 or abs(lon - float(CFG["longitude"])) > 0.01
    except (TypeError, ValueError, KeyError):
        return False


# ---- settings (inside the assistant, no own section) ------------------------------------------------------------------
for _k, _v in {"place_observe_s": 10, "place_rows": 2, "place_tent_secs": 15, "place_public_push": True, "place_offer_off": "",
               "place_patrol": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

PLACE_OBJ = {                                        # what the AI sees -> what it suggests (static / moving)
    "bicycle": ("valuable", "Bike", "access"), "motorcycle": ("valuable", "Motorbike", "ignore"), "car": ("valuable", "Car", "ignore"),
    "truck": ("tent", "Camper?", "ignore"), "bus": ("tent", "Camper?", "ignore"), "chair": ("valuable", "Chair", None),
    "bench": ("valuable", "Bench", None), "backpack": ("valuable", "Backpack", None), "suitcase": ("valuable", "Suitcase", None),
    "handbag": ("valuable", "Bag", None), "umbrella": ("valuable", "Umbrella", None), "dining table": ("valuable", "Table", None),
    "person": (None, "", "access"),
}
PLACE_MOVING_NAME = {"access": "Path?", "ignore": "Road?"}


# ---- directions: a picture point <-> degrees (right +, up +) ------------------------------------------------------------
def place_pic_to_ang(x, y, pan, tilt, hf, vf):
    a0, e0 = _cam_deg(pan, tilt)
    return (a0 + math.degrees(math.atan((x - 0.5) * 2.0 * math.tan(math.radians(hf / 2.0)))),
            e0 + math.degrees(math.atan((0.5 - y) * 2.0 * math.tan(math.radians(vf / 2.0)))))


def place_ang_to_pic(a, e, pan, tilt, hf, vf):
    a0, e0 = _cam_deg(pan, tilt)
    da = a - a0
    if servo_half("pan") >= 179.0:
        da = (da + 180.0) % 360.0 - 180.0
    da = max(-85.0, min(85.0, da)); de = max(-85.0, min(85.0, e - e0))
    return (0.5 + math.tan(math.radians(da)) / (2.0 * math.tan(math.radians(hf / 2.0))),
            0.5 - math.tan(math.radians(de)) / (2.0 * math.tan(math.radians(vf / 2.0))))


def _box_ang(b, pan, tilt, hf, vf):
    """(x, y, w, h) 0..1 of a picture -> {"a0", "a1", "e0" (bottom), "e1" (top)} in degrees"""
    x, y, w_, h_ = b
    a0, e1 = place_pic_to_ang(x, y, pan, tilt, hf, vf)
    a1, e0 = place_pic_to_ang(x + w_, y + h_, pan, tilt, hf, vf)
    return {"a0": round(a0, 2), "a1": round(a1, 2), "e0": round(e0, 2), "e1": round(e1, 2)}


def _ang_iou(p, q):
    ix = max(0.0, min(p["a1"], q["a1"]) - max(p["a0"], q["a0"])); iy = max(0.0, min(p["e1"], q["e1"]) - max(p["e0"], q["e0"]))
    u = (p["a1"] - p["a0"]) * (p["e1"] - p["e0"]) + (q["a1"] - q["a0"]) * (q["e1"] - q["e0"]) - ix * iy
    return ix * iy / u if u > 0 else 0.0


def _ang_union(p, q):
    return {"a0": min(p["a0"], q["a0"]), "a1": max(p["a1"], q["a1"]), "e0": min(p["e0"], q["e0"]), "e1": max(p["e1"], q["e1"])}


def place_ang_to_item(b, kind, name):
    """a box in degrees -> an item of place_items() (servo percent; a 360° head: the middle between 0 and 100)"""
    hp, ht = servo_half("pan"), servo_half("tilt")
    ca = (b["a0"] + b["a1"]) / 2.0
    if hp >= 179.0:
        ca = (ca + 180.0) % 360.0 - 180.0
    pan = 50.0 + ca / hp * 50.0
    pan = pan % 100.0 if hp >= 179.0 else max(0.0, min(100.0, pan))
    return {"kind": kind, "pan": round(pan, 2), "tilt": round(max(0.0, min(100.0, 50.0 + (b["e0"] + b["e1"]) / 2.0 / ht * 50.0)), 2),
            "w_pan": round(abs(b["a1"] - b["a0"]) / hp * 50.0, 2), "h_tilt": round(abs(b["e1"] - b["e0"]) / ht * 50.0, 2), "name": name}


# ---- the plan of the scan --------------------------------------------------------------------------------------------
def place_plan(rows=None, wide=False):
    """the directions of the scan: the whole pan range of the servo (180 / 270 / 360° - pan_servo_range), 1-3 tilt rows.
    The number of steps follows the field of view of the camera that takes the photos (a wide-angle one: fewer)."""
    spec = cam_wide_spec() if wide else ""
    hf, vf = cam_fov_hv(spec)[:2] if spec else cam_fov()
    hp, ht = servo_half("pan"), servo_half("tilt")
    eh = min(hp, max(5.0, float(CFG.get("pan_limit", hp) or hp)))      # the pan limit (Camera / Servos) counts too
    et = min(ht, max(5.0, float(CFG.get("tilt_limit", ht) or ht)))
    wrap = eh >= 179.0
    lo, hi = 50.0 - eh / hp * 50.0, 50.0 + eh / hp * 50.0
    if wrap:
        n = max(2, min(12, int(math.ceil(360.0 / (0.8 * hf)))))
        pans = [round(100.0 * i / n, 1) for i in range(n)]
    else:
        n = max(2, min(12, int(math.ceil(2.0 * eh / (0.8 * hf))) + 1))
        pans = [round(lo + (hi - lo) * i / (n - 1), 1) for i in range(n)]
    m = max(1, min(3, int(rows or CFG.get("place_rows", 2))))
    mid = float(CFG.get("refscan_tilt_mid", 50))
    dt = min(30.0, 0.8 * vf / ht * 50.0)
    sp = dt * (m - 1)
    tlo, thi = 50.0 - et / ht * 50.0, 50.0 + et / ht * 50.0
    sp = min(sp, thi - tlo)
    mid = max(tlo + sp / 2.0, min(thi - sp / 2.0, mid))
    tilts = [round(mid, 1)] if m == 1 else [round(mid - sp / 2.0 + sp * j / (m - 1), 1) for j in range(m)]
    pos = []
    for j, t in enumerate(tilts):                       # a snake like the reference scan (315): short ways
        row = pans if j % 2 == 0 else list(reversed(pans))
        pos += [(p, t) for p in row]
    obs = max(3.0, min(30.0, float(CFG.get("place_observe_s", 10))))
    per = obs + _refscan_settle() + 1.5
    cover = min(360.0, 2.0 * eh + hf)
    return {"spec": spec, "wide": bool(spec), "hf": round(hf, 1), "vf": round(vf, 1), "hp": hp, "ht": ht, "wrap": wrap, "pans": pans,
            "tilts": tilts, "positions": pos, "n": len(pos), "observe": obs, "eta": round(len(pos) * per), "cover": round(cover),
            "servo": round(2.0 * hp), "limit": round(2.0 * eh), "cover_v": round(min(180.0, sp / 50.0 * ht + vf)), "tilt_span": round(sp, 1), "tilt_mid": mid}


def place_busy_reason():
    """'' when the assistant may start, else why not (one lock with the simulator tasks, the reference scan, the walk test)"""
    if PLACE["busy"]:
        return "the place setup is already running"
    if REFSCAN["busy"]:
        return "a scan is already running"
    if WATCH_REF.get("w") is None:
        return "no camera"
    try:
        if walktest_on():
            return "the walk test is running"
    except NameError:
        pass
    if CFG.get("sim_on"):
        b = simtask_busy("place setup")
        if b:
            return trf("The simulator is busy: {what}", what=tr(b))
    return ""


def place_start(night_ir=True, thermal=True, wide=False, rows=None, by="web"):
    with _PLACE_LOCK:
        why = place_busy_reason()
        if why:
            return False, why
        plan = place_plan(rows, wide)
        dark = refscan_is_dark()
        PLACE.update(busy="scan", step=0, n=plan["n"], phase="", msg="", stop=False, t0=time.time(), eta=float(plan["eta"]), night=dark,
                     plan=plan)
    threading.Thread(target=_place_run, args=(plan, dark and night_ir, dark and thermal, by), daemon=True, name="placescan").start()
    log_event("sys", f"Place setup: scan started ({plan['n']} directions, {plan['cover']}° wide, {by})")
    return True, ""


def place_stop():
    PLACE["stop"] = True


def _place_grab_cam(cam, settle):
    """a clean picture of an extra camera (440) after the head stood still a moment"""
    time.sleep(settle)
    t_ask = time.time()
    cam.raw_until = t_ask + 20
    end = t_ask + 12
    while time.time() < end and not PLACE["stop"]:
        if cam.raw is not None and cam.raw_t > t_ask + 0.3:
            return cam.raw.copy()
        time.sleep(0.05)
    return None


def _place_frame(w, cam):
    w.raw_until = time.time() + 20                      # the main camera too: its AI boxes are mapped to the picture size
    if cam is not None:
        cam.raw_until = time.time() + 20
        return (cam.raw, cam.raw_t) if cam.raw is not None else (None, 0.0)
    w.raw_until = time.time() + 20
    return w.frame_raw, float(getattr(w, "_last_t0", 0) or 0)


def _place_observe(w, cam, secs, pan, tilt, hf, vf):
    """~secs seconds looking in one direction: what moves (a map of changes) and what the AI sees (main camera)"""
    end = time.time() + secs
    prev = None; acc = None; n = 0; last_t = 0.0; ai = []; seen_run = None
    mh, mv = cam_fov()
    while time.time() < end and not PLACE["stop"]:
        fr, t_ = _place_frame(w, cam)
        if fr is not None and t_ > last_t:
            last_t = t_
            H, W_ = fr.shape[:2]
            sw = 160; sh = max(8, int(round(160 * H / float(W_))))
            g = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(fr, (sw, sh), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY), (5, 5), 0)
            if prev is not None and prev.shape == g.shape:
                m = (cv2.absdiff(g, prev) > 14).astype(np.float32)
                if float(m.mean()) < 0.5:                  # half the picture changed: light switched / the camera moved - not counted
                    acc = m if acc is None else acc + m
                    n += 1
            prev = g
        ai_ = getattr(w, "ai", None)
        mf = w.frame_raw
        if ai_ is not None and mf is not None:
            run = (getattr(ai_, "_last_run", None), len(ai_.objects or []), len(ai_.boxes or []))
            if run != seen_run:
                seen_run = run
                pw = float(CFG.get("proc_width") or 480); ph = pw * mf.shape[0] / float(mf.shape[1])
                for b in list(ai_.boxes or []):
                    ai.append(("person", b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph, float(b[4]) if len(b) > 4 else 0.5))
                for o in list(ai_.objects or []):
                    ai.append((COCO_LABELS.get(o[5], "object"), o[0] / pw, o[1] / ph, o[2] / pw, o[3] / ph, float(o[4])))
        time.sleep(0.2)
    motion = []
    if acc is not None and n >= 3:
        frac = acc / float(n)
        mk = (frac > 0.12).astype(np.uint8) * 255
        mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sh, sw = mk.shape
        for c in cnts:
            if cv2.contourArea(c) < sw * sh * 0.004:
                continue
            x, y, w_, h_ = cv2.boundingRect(c)
            b = _box_ang((x / sw, y / sh, w_ / sw, h_ / sh), pan, tilt, hf, vf)
            b["score"] = round(float(frac[y:y + h_, x:x + w_].mean()), 3)
            motion.append(b)
    objs = []
    for lab, x, y, w_, h_, cf in ai:                    # the AI looks with the main camera
        b = _box_ang((x, y, w_, h_), pan, tilt, mh, mv)
        b.update(label=lab, conf=round(cf, 2))
        objs.append(b)
    return {"motion": motion[:20], "ai": objs[:200], "frames": n}


def place_suggest(positions, night=False):
    """the suggestions of the scan (in degrees): moving things -> «Ignorieren» / «Zugang», standing things -> «Wertsachen»,
    a camper (truck / bus) -> «Mein Zelt / Wohnmobil»"""
    clusters = []
    for p in positions:
        for o in (p.get("obs") or {}).get("ai") or []:
            for c in clusters:
                if c["label"] == o["label"] and (_ang_iou(c["last"], o) > 0.25 or (abs((c["last"]["a0"] + c["last"]["a1"]) - (o["a0"] + o["a1"])) / 2 < 4.0
                                                                              and abs((c["last"]["e0"] + c["last"]["e1"]) - (o["e0"] + o["e1"])) / 2 < 4.0)):
                    c["box"] = _ang_union(c["box"], o); c["n"] += 1; c["conf"] = max(c["conf"], o["conf"])
                    ca = ((o["a0"] + o["a1"]) / 2.0, (o["e0"] + o["e1"]) / 2.0)
                    c["move"] = max(c["move"], math.hypot(ca[0] - c["c0"][0], ca[1] - c["c0"][1]))
                    c["last"] = o
                    break
            else:
                clusters.append({"label": o["label"], "box": dict(o), "last": o, "n": 1, "conf": o["conf"], "move": 0.0,
                                 "c0": ((o["a0"] + o["a1"]) / 2.0, (o["e0"] + o["e1"]) / 2.0)})
    out = []
    for c in clusters:
        rule = PLACE_OBJ.get(c["label"])
        if not rule:
            continue
        b = c["box"]
        size = max(2.0, b["a1"] - b["a0"])
        moving = c["move"] > max(3.0, 0.5 * size)
        if moving and rule[2]:
            kind, name, why = rule[2], PLACE_MOVING_NAME.get(rule[2], ""), "moving " + c["label"]
        elif not moving and rule[0] and c["n"] >= 1:
            kind, name, why = rule[0], rule[1], c["label"]
        else:
            continue
        out.append({"kind": kind, "name": name, "why": why, "a0": b["a0"], "a1": b["a1"], "e0": b["e0"], "e1": b["e1"], "conf": c["conf"]})
    persons = [o for p in positions for o in (p.get("obs") or {}).get("ai") or [] if o["label"] == "person"]
    mot = []
    for p in positions:                                  # things that move by themselves (branches, flags, lights)
        for m in (p.get("obs") or {}).get("motion") or []:
            if m.get("score", 0) < (0.2 if night else 0.12):
                continue                                 # at night the picture is noisy (infrared, insects)
            if any(_ang_iou(m, s_) > 0.1 for s_ in out if s_["why"].startswith("moving")) or any(_ang_iou(m, o) > 0.05 for o in persons):
                continue                                 # a person walking, a car driving: already a suggestion
            mot.append(m)
    mot.sort(key=lambda m: -m.get("score", 0) * (m["a1"] - m["a0"]) * (m["e1"] - m["e0"]))
    for m in mot[:4]:                                    # only the strongest few - the operator decides
        out.append({"kind": "ignore", "name": "Moves by itself", "why": "motion", "a0": m["a0"], "a1": m["a1"], "e0": m["e0"], "e1": m["e1"],
                    "conf": m.get("score", 0.2)})
    merged = []
    for s in out:                                        # the same thing seen from two directions: one suggestion
        for t in merged:
            if t["kind"] == s["kind"] and t["name"] == s["name"] and _ang_iou(t, s) > 0.2:
                t.update(_ang_union(t, s)); t["conf"] = max(t["conf"], s["conf"])
                break
        else:
            merged.append(dict(s))
    order = {"tent": 0, "valuable": 1, "access": 2, "ignore": 3}
    merged.sort(key=lambda s: (order.get(s["kind"], 9), -s["conf"]))
    for i, s in enumerate(merged[:14]):
        s["id"] = "s%d" % (i + 1)
        for k in ("a0", "a1", "e0", "e1"):
            s[k] = round(s[k], 2)
    return merged[:14]


def _place_run(plan, use_ir, use_thermal, by):
    w = WATCH_REF.get("w")
    old = (CFG["pan"], CFG["tilt"])
    old_ir = CFG.get("light_ir")
    tmp = place_dir("scan_new")
    try:
        shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp, exist_ok=True)
        cam = next((c for c in list(CAMS) if c.spec == plan["spec"]), None) if plan["wide"] else None
        if plan["wide"] and cam is None:
            plan = place_plan(len(plan["tilts"]), False)
            PLACE["n"] = plan["n"]
        if use_ir and old_ir != "on":
            CFG["light_ir"] = "on"                       # the night reference with the infrared light (070)
        hf, vf = plan["hf"], plan["vf"]
        meta = {"t": time.time(), "night": PLACE["night"], "ir": bool(use_ir), "wide": plan["wide"], "spec": plan["spec"], "hf": hf, "vf": vf,
                "hp": plan["hp"], "ht": plan["ht"], "wrap": plan["wrap"], "positions": [], "by": by, "sim": bool(CFG.get("sim_on")),
                "main_fov": list(cam_fov())}
        for i, (p, t) in enumerate(plan["positions"]):
            if PLACE["stop"]:
                PLACE["msg"] = "stopped"; return
            PLACE.update(step=i + 1, phase="photo")
            _refscan_move(p, t)
            settle = _refscan_settle() + (1.0 if i == 0 else 0.0)
            img = _place_grab_cam(cam, settle) if cam is not None else _refscan_grab(w, settle, max(1, min(5, int(CFG.get("refscan_photos", 2)))))
            if img is None:
                PLACE["msg"] = "stopped" if PLACE["stop"] else "no picture from the camera"; return
            fn = f"pos_{i:02d}.jpg"
            cv2.imwrite(os.path.join(tmp, fn), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
            entry = {"i": i, "pan": p, "tilt": t, "file": fn}
            if use_thermal and THERMAL is not None and THERMAL.frame is not None and time.time() - THERMAL.t < 5:
                try:
                    cv2.imwrite(os.path.join(tmp, f"th_{i:02d}.jpg"), THERMAL.color(THERMAL.frame)[0], [cv2.IMWRITE_JPEG_QUALITY, 88])
                    entry["th"] = f"th_{i:02d}.jpg"
                except Exception:
                    pass
            PLACE["phase"] = "watch"
            MANUAL["until"] = time.time() + 60
            entry["obs"] = _place_observe(w, cam, plan["observe"], p, t, hf, vf)
            meta["positions"].append(entry)
        PLACE["phase"] = "panorama"
        meta["suggest"] = place_suggest(meta["positions"], PLACE["night"])
        _place_pano(tmp, meta)
        if not plan["wide"]:                             # the photos are the reference of the reference scan (315) too
            _place_to_refscan(tmp, meta, plan)
        with open(os.path.join(tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
        shutil.rmtree(place_dir("scan"), ignore_errors=True)
        os.replace(tmp, place_dir("scan"))
        PLACE["scan"] = None
        PLACE["msg"] = "done"
        log_event("sys", f"Place setup: scan done - {len(meta['suggest'])} suggestions")
    except Exception as e:
        PLACE["msg"] = "error: " + str(e)[:120]
        log_event("sys", f"Place setup failed: {e}"[:200])
    finally:
        if CFG.get("light_ir") != old_ir:
            CFG["light_ir"] = old_ir
        _refscan_move(*old)
        MANUAL["until"] = time.time() + 2
        shutil.rmtree(tmp, ignore_errors=True)
        PLACE.update(busy="", stop=False, phase="")


def _place_pano(d, meta):
    geo = {"hf": meta["hf"], "vf": meta["vf"], "hp": meta["hp"], "ht": meta["ht"], "wrap": meta["wrap"]}
    pos = meta["positions"]
    can, cells = pano_canvas(pos, lambda p: cv2.imread(os.path.join(d, p["file"])), tw=420, geo=geo)
    if can is None:
        raise RuntimeError("no panorama")
    g = cells.pop("_geo")
    cv2.imwrite(os.path.join(d, "pano.jpg"), can, [cv2.IMWRITE_JPEG_QUALITY, 85])
    meta["geo"] = g
    if any(p.get("th") for p in pos):                   # the thermal pictures on the same degrees (own field of view)
        thf, thv = cam_fov_hv("thermal")[:2]
        tg = dict(geo, hf=thf, vf=thv, a0=g["a0"], a1=g["a1"], e0=g["e_top"], e1=g["e_bot"])
        tk = g["k"]
        tcan, _c = pano_canvas([p for p in pos if p.get("th")], lambda p: cv2.imread(os.path.join(d, p["th"])), tw=int(round(tk * thf)), geo=tg)
        if tcan is not None:
            if tcan.shape[:2] != can.shape[:2]:
                tcan = cv2.resize(tcan, (can.shape[1], can.shape[0]))
            cv2.imwrite(os.path.join(d, "pano_th.jpg"), tcan, [cv2.IMWRITE_JPEG_QUALITY, 85])
            meta["thermal"] = True


def _place_to_refscan(d, meta, plan):
    """the scan becomes the reference of the reference scan (day or night) - and the grid of the reference scan the grid
    of the place, so «compare» drives the same directions (refscan_positions)"""
    CFG.update(refscan_pan_from=plan["pans"][0], refscan_pan_to=plan["pans"][-1], refscan_pan_steps=len(plan["pans"]),
               refscan_tilt_steps=len(plan["tilts"]), refscan_tilt_mid=plan["tilt_mid"], refscan_tilt_span=max(1.0, plan["tilt_span"]))
    kind = "night" if meta["night"] else "day"
    old = refscan_meta(kind) or {}
    rd = refscan_dir(REFSCAN_KINDS[kind] + "_new")
    shutil.rmtree(rd, ignore_errors=True); os.makedirs(rd, exist_ok=True)
    rm = {"t": meta["t"], "positions": [], "source": STATE.get("source_label", ""), "sim": bool(CFG.get("sim_on")), "dark": kind == "night",
          "photos": int(CFG.get("refscan_photos", 2)), "kind": kind, "place": True,
          "watch": [x for x in old.get("watch") or [] if x.get("src") != "place"] if len(old.get("positions") or []) == len(meta["positions"]) else []}
    for p in meta["positions"]:
        shutil.copy(os.path.join(d, p["file"]), os.path.join(rd, p["file"]))
        rm["positions"].append({"i": p["i"], "pan": p["pan"], "tilt": p["tilt"], "file": p["file"]})
    with open(os.path.join(rd, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(rm, f)
    shutil.rmtree(refscan_dir(REFSCAN_KINDS[kind]), ignore_errors=True)
    os.replace(rd, refscan_dir(REFSCAN_KINDS[kind]))
    save_settings()
    meta["refscan"] = kind


def place_scan():
    """the last scan (scan.json) or None"""
    if PLACE.get("scan") is not None:
        return PLACE["scan"]
    try:
        with open(place_dir("scan", "scan.json"), encoding="utf-8") as f:
            PLACE["scan"] = json.load(f)
    except (OSError, ValueError):
        PLACE["scan"] = None
    return PLACE["scan"]


# ---- apply: zones, masks, waypoints, guarded things, the place record --------------------------------------------------
def _clean_items(items):
    out = []
    for it in (items or [])[:30]:
        if not isinstance(it, dict) or it.get("kind") not in PLACE_KINDS:
            continue
        try:
            a0, a1, e0, e1 = (float(it[k]) for k in ("a0", "a1", "e0", "e1"))
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(v) for v in (a0, a1, e0, e1)):
            continue
        a0, a1 = min(a0, a1), max(a0, a1); e0, e1 = min(e0, e1), max(e0, e1)
        if a1 - a0 < 0.3 or e1 - e0 < 0.3 or a1 - a0 > 200 or e1 - e0 > 120:
            continue
        nm = re.sub(r"[\x00-\x1f<>]", "", str(it.get("name") or ""))[:40].strip()
        out.append({"kind": it["kind"], "a0": round(a0, 2), "a1": round(a1, 2), "e0": round(e0, 2), "e1": round(e1, 2), "name": nm})
    return out


PLACE_DEFAULT_NAMES = {"tent": "My tent / camper", "access": "Access / path", "public_path": "Public path", "valuable": "Valuables", "ignore": "Ignore"}


def _zone_points(ang, line=False):
    pp = sleep_project(ang)
    pts = [pp[0], pp[8]] if line else pp[::8]
    return [[round(min(1.0, max(0.0, x)), 4), round(min(1.0, max(0.0, y)), 4)] for x, y in pts]


def place_apply(items, public_report=True, patrol=None, by="web"):
    """make the zones / masks / waypoints / guarded things of the marked items and keep the place record"""
    its = _clean_items(items)
    scan = place_scan() or {}
    old = _place_load() or {}
    for it in its:
        it["name"] = it["name"] or tr(PLACE_DEFAULT_NAMES[it["kind"]])
        if it["kind"] == "public_path" and not public_report:
            it["kind"] = "access"
    keep = [dict(z) for z in ZONES if z.get("src") != "place"]
    new, skipped = [], 0
    room = MAX_ZONES - len(keep)
    for it in its:
        k = it["kind"]
        if k not in ("tent", "access", "ignore", "public_path"):
            continue
        if len(new) >= room:
            skipped += 1; continue
        if k == "access":
            em = round((it["e0"] + it["e1"]) / 2.0, 2)
            ang = [[it["a0"], em], [it["a1"], em]]
            z = {"mode": "line", "name": "🚶 " + it["name"], "points": _zone_points(ang, True), "ang": ang, "dir": "both"}
        else:
            ang = [[it["a0"], it["e1"]], [it["a1"], it["e1"]], [it["a1"], it["e0"]], [it["a0"], it["e0"]]]
            z = {"mode": {"tent": "loiter", "public_path": "report"}.get(k, "ignore"), "name": {"tent": "⛺ ", "public_path": "🛣 "}.get(k, "🌿 ") + it["name"],
                 "points": _zone_points(ang), "ang": ang}            # aufr: the public path = a zone «nur melden» (030), editable in the zone editor
            if k == "tent":
                z["secs"] = int(CFG.get("place_tent_secs", 15))
        z.update(id=uuid.uuid4().hex[:8], anchor=True, src="place")
        new.append(z)
    ok, err = zones_set(keep + new)
    if not ok:
        return False, err, {}
    # waypoints: the accesses (and the tent) - the patrol (160) looks there
    wps_old = [list(x) for x in old.get("wps") or []]
    for wp in wps_old:
        if wp in WAYPOINTS:
            WAYPOINTS.remove(wp)
    wps = []
    for it in its:
        if it["kind"] in ("access", "public_path", "tent"):
            pi = place_ang_to_item(it, it["kind"], it["name"])
            wp = [round(pi["pan"], 1), round(pi["tilt"], 1)]
            if wp not in WAYPOINTS and len(WAYPOINTS) < 50:
                WAYPOINTS.append(wp); wps.append(wp)
    if patrol is not None:
        CFG["place_patrol"] = bool(patrol)
        if patrol and len(WAYPOINTS) >= 2:
            CFG["patrol"] = True
    # guarded things of the reference scan (315): the box in the picture of the direction that sees it best
    vals = [it for it in its if it["kind"] == "valuable"]
    watched = place_set_watch(vals)
    if vals and not watched and scan.get("wide"):
        threading.Thread(target=_place_ref_then_watch, args=(vals,), daemon=True, name="placeref").start()
    if vals:
        CFG["refscan_on_arm"] = True                     # compare when armed + the morning panorama: «Velo fehlt»
        CFG["refscan_pano_on"] = True
    home = place_ang_to_item(next((it for it in its if it["kind"] == "tent"), None) or {"a0": -1, "a1": 1, "e0": -1, "e1": 1}, "home", "")
    rec = {"v": 1, "t": time.time(), "by": by, "scan_t": scan.get("t"), "night_ref": bool(scan.get("night")),
           "items": [dict(place_ang_to_item(it, it["kind"], it["name"]), a0=it["a0"], a1=it["a1"], e0=it["e0"], e1=it["e1"]) for it in its],
           "zones": [z["id"] for z in new], "wps": wps, "watched": watched, "public_report": bool(public_report),
           "home": {"pan": home["pan"], "tilt": home["tilt"]}, "lat": CFG.get("latitude"), "lon": CFG.get("longitude")}
    _place_save(rec)
    CFG["place_offer_off"] = ""
    save_settings()
    res = {"zones": len(new), "skipped": skipped, "waypoints": len(wps), "watched": watched,
           "public": sum(1 for it in its if it["kind"] == "public_path"), "masks": sum(1 for z in new if z["mode"] == "ignore"),
           "tent": sum(1 for z in new if z["mode"] == "loiter"), "lines": sum(1 for z in new if z["mode"] == "line"), "items": len(its)}
    log_event("sys", f"Place set up ({by}): {res['items']} things, {res['zones']} zones, {res['waypoints']} waypoints, {watched} guarded things")
    return True, "", res


def place_set_watch(vals):
    """the valuables as guarded things of the reference scan (day and night reference, when there is one) - returns how many"""
    n = 0
    mh, mv = cam_fov()
    for kind in ("day", "night"):
        meta = refscan_meta(kind)
        if not meta or meta.get("_kind") != kind or not meta.get("positions"):
            continue
        out = [x for x in meta.get("watch") or [] if x.get("src") != "place"]
        for it in vals:
            ca, ce = (it["a0"] + it["a1"]) / 2.0, (it["e0"] + it["e1"]) / 2.0
            best = min(meta["positions"], key=lambda p: math.hypot(*(np.subtract(place_ang_to_pic(ca, ce, p["pan"], p["tilt"], mh, mv), 0.5))))
            x0, y0 = place_ang_to_pic(it["a0"], it["e1"], best["pan"], best["tilt"], mh, mv)
            x1, y1 = place_ang_to_pic(it["a1"], it["e0"], best["pan"], best["tilt"], mh, mv)
            x0, x1 = max(0.0, min(1.0, x0)), max(0.0, min(1.0, x1)); y0, y1 = max(0.0, min(1.0, y0)), max(0.0, min(1.0, y1))
            if x1 - x0 < 0.01 or y1 - y0 < 0.01:
                continue
            out.append({"pos": int(best["i"]), "x": round(x0, 4), "y": round(y0, 4), "w": round(x1 - x0, 4), "h": round(y1 - y0, 4),
                        "name": it["name"][:40], "src": "place"})
        meta["watch"] = out[:30]
        refscan_save_meta(meta)
        n = max(n, sum(1 for x in out if x.get("src") == "place"))
    return n


def _place_ref_then_watch(vals):
    """the scan was made with the wide-angle camera: the reference scan of the main camera first, then the guarded things"""
    for _ in range(60):
        if not REFSCAN["busy"]:
            break
        time.sleep(2)
    ok, _e = refscan_start("scan", "place setup")
    if not ok:
        return
    time.sleep(3)
    while REFSCAN["busy"]:
        time.sleep(2)
    n = place_set_watch(vals)
    rec = _place_load()
    if rec:
        rec["watched"] = n
        _place_save(rec)


def place_clear(by="web"):
    """forget the place: its zones, waypoints and guarded things (the photos of the reference scan stay)"""
    rec = _place_load() or {}
    zones_set([dict(z) for z in ZONES if z.get("src") != "place"])
    for wp in rec.get("wps") or []:
        if list(wp) in WAYPOINTS:
            WAYPOINTS.remove(list(wp))
    place_set_watch([])
    try:
        os.remove(place_dir("place.json"))
    except OSError:
        pass
    PLACE["rec"] = None
    save_settings()
    log_event("sys", f"Place forgotten ({by})")
    return True


# ---- the offer: on the first start and after a new position -------------------------------------------------------------
def place_offer():
    """'' = nothing to offer, "first" = never set up, "moved" = the device stands somewhere else now"""
    rec = _place_load()
    off = str(CFG.get("place_offer_off") or "")
    if not rec or not rec.get("t"):
        return "" if off == "first" else "first"
    if place_new_position() and off != "moved:%s,%s" % (CFG.get("latitude"), CFG.get("longitude")):
        return "moved"
    return ""


def place_offer_dismiss():
    o = place_offer()
    CFG["place_offer_off"] = "first" if o == "first" else "moved:%s,%s" % (CFG.get("latitude"), CFG.get("longitude"))
    save_settings()


def place_state(lang=None):
    plan = place_plan()
    wide = cam_wide_spec()
    pw = place_plan(wide=True) if wide else None
    scan = place_scan()
    rec = _place_load()
    sc = None
    if scan:
        sc = {"t": scan.get("t"), "geo": scan.get("geo"), "suggest": scan.get("suggest") or [], "night": scan.get("night"),
              "thermal": bool(scan.get("thermal")), "wide": scan.get("wide"), "n": len(scan.get("positions") or []), "refscan": scan.get("refscan"),
              "v": int(scan.get("t") or 0)}
    left = 0
    if PLACE["busy"]:
        left = max(0, int(PLACE["eta"] - (time.time() - PLACE["t0"])))
    th_ok = THERMAL is not None and THERMAL.frame is not None and time.time() - THERMAL.t < 10
    return {"busy": PLACE["busy"], "step": PLACE["step"], "n": PLACE["n"], "phase": PLACE["phase"], "msg": tr(PLACE["msg"], lang) if PLACE["msg"] else "",
            "done_msg": PLACE["msg"] == "done", "left": left, "dark": refscan_is_dark(), "thermal_ok": th_ok,
            "ir_ok": bool(CFG.get("light_ir_out")) or bool(CFG.get("sim_on")),
            "plan": {"n": plan["n"], "eta": plan["eta"], "cover": plan["cover"], "servo": plan["servo"], "hf": plan["hf"], "vf": plan["vf"],
                     "rows": len(plan["tilts"]), "wrap": plan["wrap"], "cover_v": plan["cover_v"]},
            "wide": {"spec": wide, "label": source_label(wide), "hf": pw["hf"], "n": pw["n"], "eta": pw["eta"], "cover": pw["cover"]} if pw else None,
            "scan": sc, "record": {"t": rec.get("t"), "items": rec.get("items") or [], "public_report": rec.get("public_report", True),
                                   "watched": rec.get("watched", 0), "zones": len(rec.get("zones") or []), "wps": len(rec.get("wps") or [])} if rec else None,
            "offer": place_offer(), "why_not": tr(place_busy_reason(), lang) if not PLACE["busy"] else "",
            "info": place_info()}


# ---- the alarm: a person on the public path is only reported, a person at the tent counts more ---------------------------
PLACE_GATE = {"pub_t": 0.0, "tent_t": 0.0}


def place_report_migrate():
    """aufr: the «public path» of a place set up with 2.98.36 or older was only an item of the place record (alarm_gate looked
    at it). Now it is a zone «nur melden» (mode report, stays on its place) - made once from the record, so it shows up
    and can be changed in the zone editor. Returns the list of what was taken over."""
    rec = _place_load() or {}
    pubs = [it for it in (rec.get("items") or []) if isinstance(it, dict) and it.get("kind") == "public_path" and "a0" in it]
    if not pubs or not rec.get("public_report", True) or any(z["mode"] == "report" and z.get("src") == "place" for z in ZONES):
        return []
    new = []
    for it in pubs:
        if len(ZONES) + len(new) >= MAX_ZONES:
            break
        try:
            ang = [[float(it["a0"]), float(it["e1"])], [float(it["a1"]), float(it["e1"])], [float(it["a1"]), float(it["e0"])], [float(it["a0"]), float(it["e0"])]]
        except (KeyError, TypeError, ValueError):
            continue
        new.append({"id": uuid.uuid4().hex[:8], "mode": "report", "name": "🛣 " + (str(it.get("name") or "") or tr(PLACE_DEFAULT_NAMES["public_path"])),
                    "points": _zone_points(ang), "ang": ang, "anchor": True, "src": "place"})
    if not new:
        return []
    ok, _e = zones_set([dict(z) for z in ZONES] + new)
    if ok:
        rec["zones"] = list(rec.get("zones") or []) + [z["id"] for z in ZONES if z.get("src") == "place" and z["mode"] == "report"]
        try:
            _place_save(rec)
        except OSError:
            pass
    return [f"public path of the place -> {len(new)} zone(s) «only report»"] if ok else []


def _place_in(it, a, e, grow=0.0):
    a0, a1 = it["a0"] - grow, it["a1"] + grow
    if servo_half("pan") >= 179.0:
        c = (a0 + a1) / 2.0
        a = c + ((a - c + 180.0) % 360.0 - 180.0)
    return a0 <= a <= a1 and it["e0"] - grow <= e <= it["e1"] + grow


_alarm_gate_base = alarm_gate


def alarm_gate(w, frame, persons, now):
    """2.98.30 (317): before the gate of 066: persons whose feet stand in a zone «nur melden» (aufr: zone mode report - the
    public path of «Platz einrichten» and every such zone of the zone editor) are no alarm - one log line / info push now and
    then. A person at the tent (or coming closer to it) needs no double confirmation."""
    rec = PLACE["rec"] if PLACE["loaded"] else _place_load()
    its = (rec or {}).get("items") or []
    reps = [z for z in ZONES if z["mode"] == "report" and zone_here(z) and len(z.get("points") or []) >= 3]
    tents = [it for it in its if it.get("kind") == "tent" and "a0" in it]
    if not persons or not (reps or tents):
        return _alarm_gate_base(w, frame, persons, now)
    pw = float(CFG.get("proc_width") or 480)
    ph = float(getattr(w, "_ph", 0) or 0) or (pw * frame.shape[0] / float(frame.shape[1]) if frame is not None else pw * 0.5625)
    hf, vf = cam_fov()
    keep, pub, near, where = [], 0, False, ""
    for b in persons:
        x, y, bw, bh = (float(v) for v in b[:4])
        fx, fy = (x + bw / 2.0) / pw, (y + bh * 0.95) / ph
        a, e = place_pic_to_ang(fx, fy, CFG["pan"], CFG["tilt"], hf, vf)
        at_tent = any(_place_in(t, a, e, 4.0) for t in tents)
        zr = None if at_tent else next((z for z in reps if point_in_poly(fx, fy, z["points"])), None)
        if zr is not None:
            pub += 1; where = where or zr["name"]; continue
        near = near or at_tent
        keep.append(b)
    if pub and now - PLACE_GATE["pub_t"] > 300:
        PLACE_GATE["pub_t"] = now
        log_event("person", f"Person in «{where}» - only reported (zone «only report»)")
        if is_armed() and CFG.get("place_public_push", True):
            try:
                w.notifier.info(tr("Person on the public path (only reported, no alarm)") + " · " + where, title="{name}: " + tr("Only report"))
            except Exception:
                pass
    res = _alarm_gate_base(w, frame, keep, now)
    if res or not keep or not near:
        return res
    closer = (ERK.get("best") or {}).get("trend") == "closer" and now - float(ERK.get("t") or 0) < 3.0
    if ALX["hold_until"] <= now and is_armed() and CFG.get("alarm_confirm2"):
        if now - PLACE_GATE["tent_t"] > 30:
            PLACE_GATE["tent_t"] = now
            log_event("person", "Person at the tent" + (" coming closer" if closer else "") + " - alarm without the second confirmation (place setup)")
        return keep
    return res


def place_selftest():
    sv = (CFG["pan"], CFG["tilt"], CFG.get("pan_servo_range"), CFG["pan_limit"])
    try:
        CFG["pan"], CFG["tilt"] = 50.0, 50.0
        hf, vf = 66.0, 41.0
        a, e = place_pic_to_ang(0.75, 0.25, 30.0, 60.0, hf, vf)
        x, y = place_ang_to_pic(a, e, 30.0, 60.0, hf, vf)
        assert abs(x - 0.75) < 1e-6 and abs(y - 0.25) < 1e-6
        it = place_ang_to_item({"a0": -10, "a1": 10, "e0": -5, "e1": 5}, "tent", "x")
        assert abs(it["pan"] - 50) < 1e-6 and it["w_pan"] > 0
        CFG["pan_servo_range"] = 360.0
        it = place_ang_to_item({"a0": 170, "a1": 190, "e0": -5, "e1": 5}, "access", "x")   # across the seam
        assert it["pan"] < 1.0 or it["pan"] > 99.0, it
        assert _place_in({"a0": 170, "a1": 190, "e0": -5, "e1": 5}, -175.0, 0.0)
        p = place_plan(2)
        CFG["pan_limit"] = 180
        p = place_plan(2)
        assert p["wrap"] and p["cover"] == 360 and p["n"] == len(p["pans"]) * 2 and max(p["pans"]) < 100
        CFG["pan_servo_range"] = 180.0; CFG["pan_limit"] = 90
        p = place_plan(2)
        assert not p["wrap"] and p["pans"][0] == 0 and p["pans"][-1] == 100
        assert _clean_items([{"kind": "tent", "a0": 5, "a1": -5, "e0": 1, "e1": -3}])[0]["a0"] == -5
        assert not _clean_items([{"kind": "x", "a0": 0, "a1": 5, "e0": 0, "e1": 5}])
        # the alarm gate: a person on the public path is no alarm, one beside it is
        CFG["pan"], CFG["tilt"] = 50.0, 50.0
        old = (PLACE["rec"], PLACE["loaded"], CFG.get("alarm_confirm2"), PLACE_GATE["pub_t"], ALX["hold_until"])
        try:
            PLACE.update(rec={"items": [{"kind": "public_path", "a0": -12, "a1": 12, "e0": -25, "e1": 25, "name": "p"}]}, loaded=True)
            CFG["alarm_confirm2"] = False; ALX["hold_until"] = 0.0
            zs_old = [dict(z) for z in ZONES]
            _ss, globals()["save_settings"] = globals()["save_settings"], lambda: None
            _ps, globals()["_place_save"] = globals()["_place_save"], lambda r: None
            try:
                ZONES[:] = []
                assert place_report_migrate() and [z["mode"] for z in ZONES] == ["report"] and ZONES[0].get("anchor") and ZONES[0].get("ang")
                assert place_report_migrate() == [], "taken over only once"
                sleep_update()

                class _W:
                    _ph = 270; ai = None; last_warm = 0.0; notifier = None
                pw = float(CFG.get("proc_width") or 480)
                on_path = (pw / 2 - 10, 100, 20, 60); beside = (pw * 0.9, 100, 20, 60)
                assert alarm_gate(_W(), None, [on_path], time.time()) == []
                assert alarm_gate(_W(), None, [on_path, beside], time.time()) == [beside]
                ZONES[:] = [dict(ZONES[0], anchor=False)]                       # a zone «only report» of the zone editor (not anchored)
                assert _clean_zone(ZONES[0], 0)["mode"] == "report"
                assert alarm_gate(_W(), None, [on_path], time.time()) == []
            finally:
                ZONES[:] = zs_old
                globals()["save_settings"] = _ss; globals()["_place_save"] = _ps
        finally:
            PLACE["rec"], PLACE["loaded"], CFG["alarm_confirm2"], PLACE_GATE["pub_t"], ALX["hold_until"] = old
        return "directions, 360° seam, plan, items, public path = zone «only report» (migration, alarm)"
    finally:
        CFG["pan"], CFG["tilt"], CFG["pan_servo_range"], CFG["pan_limit"] = sv
