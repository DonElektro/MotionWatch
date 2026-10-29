#@ MoveEye – Teil 415: Entfernung und Richtung einer Person, Gehtest beim Einrichten. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Wunsch Daniel)
# 1. Distance: a person is about 1.7 m tall - from the height of its box and the vertical field of view of the camera
#    (simulator: /info, otherwise the setting cam_vfov, Camera Module 3: 41°) MoveEye estimates how far away it is, and from
#    the last seconds of the track whether it comes closer or goes away. Shown on the live picture, in the push text
#    («Person, ca. 12 m, kommt näher») and so also in the list «Nachrichten» (065 keeps the push text).
# 2. Walk test («Gehtest») when setting up: for 3 minutes (or until «Stop») the camper walks past the camera. Every detection
#    beeps (loudspeaker of the Pi and the open page), and MoveEye notes where (picture, estimated distance) the person was
#    recognised and where only movement was seen. No alarms, no pushes, no siren meanwhile (is_armed() is False).
#    The result: the camera picture of the start with coloured marks + a short summary (range, blind parts).
# ----------------------------------------------------------------------------
PERSON_H_M = 1.7                                  # a person (standing / walking), metres
WALKTEST_S = 180                                  # the walk test ends by itself after 3 minutes
ERK = {"tracks": {}, "best": None, "t": 0.0}
WALK = {"on": False, "t0": 0.0, "until": 0.0, "by": "", "hits": [], "motion": [], "ref": None, "last": {}, "beep_t": 0.0,
        "n": 0, "seq": 0, "result": None, "loaded": False}


def erk_vfov():
    """vertical field of view of the main camera in degrees (simulator: its /info, else the setting / Camera Module 3)"""
    try:
        if CFG.get("sim_on") and str(CFG["source"]).startswith("sim:"):
            info = SIM.get("info") or {}
            cam = next((c for c in info.get("cameras") or [] if str(c.get("id")) == str(CFG["source"])[4:]), None)
            if cam and cam.get("fov_v"):
                return max(5.0, min(170.0, float(cam["fov_v"])))
    except (TypeError, ValueError, KeyError):
        pass
    try:
        return max(5.0, min(170.0, float(cam_fov()[1])))
    except Exception:
        return 41.0


def person_dist_m(h_px, ph):
    """distance in m of a person whose box is h_px pixels tall in a picture ph pixels tall"""
    if h_px < 3 or ph <= 0:
        return None
    f = (ph / 2.0) / math.tan(math.radians(erk_vfov()) / 2.0)
    return max(0.5, min(200.0, PERSON_H_M * f / float(h_px)))


def dist_round(d):
    """12.4 -> 12, 33 -> 35 (far away the estimate is rough anyway)"""
    d = float(d)
    if d < 30:
        return max(1, int(round(d)))
    return int(round(d / 5.0) * 5)


def _track_dist(t, ai_boxes, ph):
    x, y, w, h = t.box
    hh, src = float(h), "motion"
    if t.ai_confirmed and ai_boxes:
        b = max(ai_boxes, key=lambda a: iou(t.box, a[:4]))
        if iou(t.box, b[:4]) > 0.2:
            hh, src = float(b[3]), "ai"                        # the box of the AI fits the person best
    if src == "motion" and hh > 30:
        hh -= 12.0                                             # the movement boxes are made 12 px taller (dilate 7 x 13, part 410)
    return person_dist_m(hh, ph), src


def _trend(hist, now):
    """'closer' / 'away' / '' from the distances of the last 4 seconds (straight line through the logarithm)"""
    pts = [(t_, d_) for t_, d_ in hist if now - t_ <= 4.0]
    if len(pts) < 4 or pts[-1][0] - pts[0][0] < 1.5:
        return ""
    ts = np.array([p[0] for p in pts]); ds = np.log(np.array([p[1] for p in pts]))
    try:
        k = float(np.polyfit(ts - ts[0], ds, 1)[0])            # relative change per second
    except (ValueError, np.linalg.LinAlgError):
        return ""
    span = ts[-1] - ts[0]
    if k * span < -0.12 and k < -0.03:
        return "closer"
    if k * span > 0.12 and k > 0.03:
        return "away"
    return ""


def erk_frame(persons, candidates, ai_boxes, pw, ph, t0, small):
    """once per picture (camera loop 410): distance and direction of every person, then the walk test"""
    out = []
    tr_ = ERK["tracks"]
    for t in persons:
        d, src = _track_dist(t, ai_boxes, ph)
        if d is None:
            continue
        h_ = tr_.setdefault(t.id, deque(maxlen=40)); h_.append((t0, d))
        t.dist = d; t.trend = _trend(h_, t0); t.dist_src = src
        out.append({"id": t.id, "m": dist_round(d), "trend": t.trend, "src": src})
    for k in [k for k, h_ in tr_.items() if not h_ or t0 - h_[-1][0] > 10.0]:
        del tr_[k]
    if out:
        best = min(out, key=lambda o: o["m"])
        ERK["best"] = best; ERK["t"] = t0
    STATE["person_dist"] = sorted(out, key=lambda o: o["m"])[:6]
    walktest_feed(persons, candidates, pw, ph, t0, small)


def erk_note_thermal(d, t0):
    """a person found only in the thermal picture (232)"""
    h_ = ERK["tracks"].setdefault("th", deque(maxlen=40)); h_.append((t0, d))
    o = {"id": "th", "m": dist_round(d), "trend": _trend(h_, t0), "src": "thermal"}
    if not ERK["best"] or t0 - ERK["t"] > 1.0 or ERK["best"].get("src") == "thermal":
        ERK["best"] = o; ERK["t"] = t0
    STATE["person_dist"] = (STATE.get("person_dist") or []) + [o]


def dist_overlay(t):
    """the short text on the live picture beside «PERSON #3» (ASCII: the picture font has no umlauts)"""
    d = getattr(t, "dist", None)
    if d is None:
        return ""
    tr_ = {"closer": " closer", "away": " leaving"}.get(getattr(t, "trend", ""), "")
    return f"  ~{dist_round(d)}m{tr_}"


def person_dist_text(lang=None, max_age=6.0):
    """«Person, ca. 12 m, kommt näher» - for the push text (empty when no distance is known)"""
    b = ERK.get("best")
    if not b or time.time() - ERK["t"] > max_age:
        return ""
    head = tr("Person (thermal picture)", lang) if b.get("src") == "thermal" else tr("Person", lang)
    s = head + ", " + trf("about {m} m", lang, m=b["m"])
    if b.get("trend") == "closer":
        s += ", " + tr("coming closer", lang)
    elif b.get("trend") == "away":
        s += ", " + tr("moving away", lang)
    return s


# ---- walk test ---------------------------------------------------------------------------------------------------------
def _walk_dir():
    return os.path.join(DATA_DIR, "gehtest")


def walktest_on():
    return bool(WALK["on"])


def walktest_start(by="web"):
    if WALK["on"]:
        return True, ""
    if not CFG.get("detection_on"):
        return False, "the detection is switched off"
    now = time.time()
    keep = {k: CFG.get(k) for k in ("track_person", "track_motion", "patrol")}
    follow = kopf_walk_follow()                               # 2.98.30: the head follows the walker (162)
    WALK.update(on=True, t0=now, until=now + WALKTEST_S, by=by, hits=[], motion=[], ref=None, last={}, beep_t=0.0, n=0, seq=WALK["seq"] + 1,
                follow=follow, hp=[], mp=[], lost=[], ref_pt=(round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1)))
    if any(keep.values()) or follow:                          # without following the head must stand still - else the map is wrong
        CFG["walktest_keep"] = keep
        for k in keep:
            CFG[k] = False
        if follow:
            CFG["track_person"] = True                        # only persons, no patrol; the map is turned back to the start view
        save_settings()
    try:
        protect_cancel_escalation()
    except Exception:
        pass
    log_event("sys", f"Walk test started ({by}) - walk past the camera; no alarms for {WALKTEST_S // 60} minutes")
    return True, ""


def walktest_stop(why="button"):
    if not WALK["on"]:
        return False
    WALK["on"] = False
    if WALK.get("follow") and WALK.get("ref_pt"):            # 2.98.30: back to where the walk test started (162)
        KOPF["back"] = {"pos": tuple(WALK["ref_pt"]), "since": 0.0, "why": "after the walk test"}
    keep = CFG.get("walktest_keep") or {}
    if keep:
        for k, v in keep.items():
            if k in CFG:
                CFG[k] = bool(v)
        CFG["walktest_keep"] = {}
        save_settings()
    try:
        res = _walktest_result(why)
        WALK["result"] = res
        log_event("sys", f"Walk test ended ({why}): person recognised {res['n_det']}x"
                  + (f", up to about {res['max_m']} m" if res.get("max_m") else "") + f", movement without person {res['n_mot']}x")
    except Exception as e:
        log_event("sys", f"Walk test: {e}"[:160])
    return True


def walktest_restore():
    """started again while a walk test ran (restart, power cut): what the walk test switched off comes back"""
    keep = CFG.get("walktest_keep") or {}
    if keep and not WALK["on"]:
        for k, v in keep.items():
            if k in CFG:
                CFG[k] = bool(v)
        CFG["walktest_keep"] = {}


CFG.setdefault("walktest_keep", {}); DEFAULTS.setdefault("walktest_keep", {})


def _walk_beep():
    WALK["n"] += 1
    now = time.time()
    if now - WALK["beep_t"] < 1.0:
        return
    WALK["beep_t"] = now
    try:
        if out_selected() and not SOUND.get("playing"):
            sound_play("beep1", 0.25, CFG.get("clap_volume", 60), reason="walk test")
    except Exception:
        pass


def walktest_hit(nx, ny, d, src, tid, t0):
    """a person recognised at nx, ny (feet, 0..1 of the picture), d metres away"""
    if not WALK["on"]:
        return
    last = WALK["last"].get(("p", tid), 0.0)
    if t0 - last < 0.4:
        return
    WALK["last"][("p", tid)] = t0
    if len(WALK["hits"]) < 3000:
        WALK["hits"].append((round(t0 - WALK["t0"], 1), round(nx, 3), round(ny, 3), round(float(d), 1) if d else None, src))
        WALK.setdefault("hp", []).append((round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1)))   # where the head looked (162)
    if t0 - WALK["last"].get(("beep", tid), 0.0) > 1.2:
        WALK["last"][("beep", tid)] = t0
        _walk_beep()


def walktest_feed(persons, candidates, pw, ph, t0, small):
    if not WALK["on"]:
        if CFG.get("walktest_keep"):
            walktest_restore()
        return
    if t0 >= WALK["until"]:
        walktest_stop("time"); return
    if WALK["ref"] is None and small is not None:
        WALK["ref"] = small.copy()                            # the picture of the place (before boxes are drawn)
    for t in persons:
        x, y, w, h = t.box
        walktest_hit((x + w / 2.0) / pw, min(1.0, (y + h) / float(ph)), getattr(t, "dist", None),
                     getattr(t, "dist_src", "ai" if t.ai_confirmed else "motion"), t.id, t0)
    pb = [t.box for t in persons]
    for t in candidates:
        if t.lost or t.is_vehicle or len(t.speeds) < 2 or any(iou(t.box, b) > 0.0 for b in pb):
            continue
        if t.box[2] > 0.4 * pw or t.box[2] * t.box[3] > 0.15 * pw * ph:
            continue                                          # a box over half the picture (light, wind, a turn) is no visitor
        k = ("m", t.id)
        if t0 - WALK["last"].get(k, 0.0) < 0.5:
            continue
        WALK["last"][k] = t0
        x, y, w, h = t.box
        d = person_dist_m(max(3.0, h - 12.0 if h > 30 else h), ph)      # as far as a person of this height would be
        if len(WALK["motion"]) < 3000:
            WALK["motion"].append((round(t0 - WALK["t0"], 1), round((x + w / 2.0) / pw, 3), round(min(1.0, (y + h) / float(ph)), 3),
                                   round(d, 1) if d else None))
            WALK.setdefault("mp", []).append((round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1)))


_WT_BANDS = ((0, 5), (5, 10), (10, 15), (15, 25), (25, 40), (40, 999))
_WT_COL = {"ai": (60, 200, 60), "motion": (60, 200, 60), "thermal": (200, 60, 230), "mot": (0, 165, 255)}


def _walk_marks(img, hits, motion):
    H, W = img.shape[:2]
    r = max(3, W // 140)
    for _t, nx, ny, _d in motion:
        cv2.circle(img, (int(nx * W), int(ny * H)), r, _WT_COL["mot"], 2, cv2.LINE_AA)
    for _t, nx, ny, _d, src in hits:
        cv2.circle(img, (int(nx * W), int(ny * H)), r + 1, _WT_COL.get(src, (60, 200, 60)), -1, cv2.LINE_AA)
        cv2.circle(img, (int(nx * W), int(ny * H)), r + 1, (20, 20, 20), 1, cv2.LINE_AA)


def _walktest_result(why):
    hits, motion = list(WALK["hits"]), list(WALK["motion"])
    lost = [dict(x) for x in WALK.get("lost") or []]
    if WALK.get("follow") and WALK.get("ref_pt"):           # 2.98.30: the head followed - every mark into the picture of the start
        rp = WALK["ref_pt"][0]
        hp, mp = WALK.get("hp") or [], WALK.get("mp") or []
        hits = [(h[0], round(kopf_walk_where(h[1], hp[i][0], rp), 3)) + tuple(h[2:]) for i, h in enumerate(hits) if i < len(hp)]
        motion = [(m[0], round(kopf_walk_where(m[1], mp[i][0], rp), 3)) + tuple(m[2:]) for i, m in enumerate(motion) if i < len(mp)]
        for x in lost:
            x["nx"] = round(kopf_walk_where(x["nx"], x["pan"], rp), 3)
        # (marks outside the start view are counted, the picture simply does not show them)
    ds = [h[3] for h in hits if h[3]]
    res = {"t": time.time(), "t0": WALK["t0"], "s": int(time.time() - WALK["t0"]), "why": why, "by": WALK["by"],
           "n_det": len(hits), "n_mot": len(motion), "n_thermal": sum(1 for h in hits if h[4] == "thermal"),
           "max_m": dist_round(max(ds)) if ds else None, "min_m": dist_round(min(ds)) if ds else None,
           "bands": [], "thirds": [], "img": False, "follow": bool(WALK.get("follow")), "lost": lost}
    for lo, hi in _WT_BANDS:
        res["bands"].append({"lo": lo, "hi": hi, "det": sum(1 for h in hits if h[3] and lo <= h[3] < hi),
                             "mot": sum(1 for m in motion if m[3] and lo <= m[3] < hi)})
    for i in range(3):
        a, b = i / 3.0, (i + 1) / 3.0
        res["thirds"].append({"det": sum(1 for h in hits if a <= h[1] < b or (i == 2 and h[1] >= 1.0)),
                              "mot": sum(1 for m in motion if a <= m[1] < b or (i == 2 and m[1] >= 1.0))})
    ref = WALK["ref"]
    try:
        d = _walk_dir(); os.makedirs(d, exist_ok=True)
        if ref is not None:
            img = ref.copy()
            if img.shape[1] < 640:
                img = cv2.resize(img, (640, int(img.shape[0] * 640 / img.shape[1])), interpolation=cv2.INTER_LINEAR)
            img = cv2.addWeighted(img, 0.75, np.zeros_like(img), 0.25, 0)       # a little darker: the marks stand out
            H, W = img.shape[:2]
            for x_ in (W // 3, 2 * W // 3):
                cv2.line(img, (x_, 0), (x_, H), (200, 200, 200), 1, cv2.LINE_AA)
            _walk_marks(img, hits, motion)
            for x in lost:                                    # 2.98.30: where the head lost the walker: a red cross
                if 0.0 <= x["nx"] <= 1.0:
                    p = (int(x["nx"] * W), int(min(1.0, x["ny"]) * H))
                    cv2.drawMarker(img, p, (40, 40, 255), cv2.MARKER_TILTED_CROSS, max(14, W // 30), 3, cv2.LINE_AA)
            for _t, nx, ny, dd, _s in hits[::max(1, len(hits) // 12)][:14]:       # a few distances written beside the marks
                if dd:
                    p = (min(W - 40, int(nx * W) + 8), max(14, int(ny * H) - 6))
                    cv2.putText(img, f"{dist_round(dd)}m", p, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
                    cv2.putText(img, f"{dist_round(dd)}m", p, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imwrite(os.path.join(d, "gehtest.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
            res["img"] = True
        with open(os.path.join(d, "gehtest.json"), "w", encoding="utf-8") as f:
            json.dump(res, f)
    except (OSError, cv2.error) as e:
        log_event("sys", f"Walk test picture: {e}"[:160])
    return res


def _walk_load():
    if WALK["loaded"]:
        return
    WALK["loaded"] = True
    try:
        with open(os.path.join(_walk_dir(), "gehtest.json"), encoding="utf-8") as f:
            WALK["result"] = json.load(f)
    except (OSError, ValueError):
        pass


def walktest_img():
    p = os.path.join(_walk_dir(), "gehtest.jpg")
    return p if os.path.isfile(p) else None


def walktest_summary(res, lang=None):
    """the result in a few sentences"""
    T = lambda x: tr(x, lang)
    out = []
    if not res:
        return out
    if not res["n_det"]:
        out.append(T("No person was recognised. Walk upright across the picture, 3 to 15 m from the camera; check the light, the zones and the AI."))
    else:
        out.append(trf("Person recognised {n}x - from about {lo} m to about {hi} m.", lang, n=res["n_det"], lo=res.get("min_m") or "?", hi=res.get("max_m") or "?"))
    if res.get("n_thermal"):
        out.append(trf("{n}x only in the thermal picture.", lang, n=res["n_thermal"]))
    names = (T("Left part"), T("Middle part"), T("Right part"))
    for i, th in enumerate(res.get("thirds") or []):
        if th["mot"] >= 4 and th["det"] * 2 < th["mot"]:
            out.append(trf("{where}: movement seen {m}x, but a person only {d}x - you are hardly recognised there (too far, covered, too dark or outside the zones?).",
                           lang, where=names[i], m=th["mot"], d=th["det"]))
        elif th["det"] == 0 and th["mot"] == 0 and res["n_det"] + res["n_mot"] >= 10:
            out.append(trf("{where}: nothing seen - did you walk there?", lang, where=names[i]))
    out += kopf_walk_lost_text(res, lang)                    # 2.98.30: where the head lost you (162)
    far = [b for b in res.get("bands") or [] if b["lo"] >= 5 and b["mot"] >= 4 and b["det"] * 2 < b["mot"]]
    if far and res["n_det"]:
        b = far[0]
        out.append(trf("From about {lo} m on movement is seen more often than a person: the range for persons ends there.", lang, lo=b["lo"]))
    return out


def walktest_state(lang=None):
    _walk_load()
    if WALK["on"] and time.time() >= WALK["until"]:
        walktest_stop("time")                                   # also when no picture comes any more
    res = WALK["result"]
    hits = WALK["hits"]
    return {"on": WALK["on"], "left": max(0, int(WALK["until"] - time.time())) if WALK["on"] else 0, "total": WALKTEST_S,
            "n_det": len(hits) if WALK["on"] else 0, "n_mot": len(WALK["motion"]) if WALK["on"] else 0, "beeps": WALK["n"],
            "last_m": dist_round(hits[-1][3]) if WALK["on"] and hits and hits[-1][3] else None, "seq": WALK["seq"],
            "speaker": bool(out_selected()),
            "result": dict(res, text=walktest_summary(res, lang), when=datetime.fromtimestamp(res["t"]).strftime("%d.%m. %H:%M")) if res else None,
            "batt_save": dict(batt_save_state(), text=batt_save_text(lang))}


def walktest_draw(frame):
    """during the walk test: the marks so far and the time left on the live picture"""
    if not WALK["on"]:
        return
    try:
        _walk_marks(frame, WALK["hits"][-400:], WALK["motion"][-400:])
        left = max(0, int(WALK["until"] - time.time()))
        txt = f"WALK TEST {left // 60}:{left % 60:02d}  persons {len(WALK['hits'])}  motion {len(WALK['motion'])}"
        H, W = frame.shape[:2]
        cv2.rectangle(frame, (0, H - 30), (W, H), (0, 0, 0), -1)
        cv2.putText(frame, txt, (10, H - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 230, 80), 2, cv2.LINE_AA)
    except cv2.error:
        pass
