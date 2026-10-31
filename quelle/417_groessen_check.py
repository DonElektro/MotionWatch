#@ MoveEye – Teil 417: Grössen-Prüfung – ist das Ding für seinen Platz im Bild gross genug für eine Person? Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.16 (Fehlalarme durch Tiere, Prüfstand): auf ebenem Boden steht eine Person weiter unten im Bild (näher) grösser da
# als weiter oben (weiter weg) – die Höhe im Bild wächst fast linear mit dem Abstand der Füsse vom Horizont. MoveEye lernt
# diese Gerade aus den Personen, die die KI sicher bestätigt hat (pro Neigung des Kopfes). Ein Ding, das nur durch seine
# Bewegung als «Person» gälte, aber viel kleiner ist, als eine Person an dieser Stelle wäre (Dachs, Katze, Fuchs), wird
# keine Person. Ohne genug gelernte Personen (die ersten Abende) prüft es nichts.
# ----------------------------------------------------------------------------
SIZEFIT = {"b": {}, "fit": {}, "t": 0.0, "rejects": 0}
SIZE_MIN_SAMPLES = 12


def _size_bucket():
    try:
        return int(round(float(CFG.get("tilt", 50)) / 3.0))     # the tilt of the head: another tilt = another line
    except (TypeError, ValueError):
        return 0


def size_learn(tracks, ai_boxes, pw, ph):
    """the AI-confirmed, upright persons of this picture: (feet row, height) both 0..1"""
    if not ai_boxes or ph <= 0:
        return
    b = SIZEFIT["b"].setdefault(_size_bucket(), deque(maxlen=120))
    for (x, y, w, h, *_r) in ai_boxes:
        if h < 0.04 * ph or w > 0.9 * h or y + h > 0.985 * ph or y < 0.01 * ph:
            continue                                     # not upright, or cut off at the edge: the size is not reliable
        b.append(((y + h) / ph, h / ph))
    now = time.time()
    if now - SIZEFIT["t"] > 5.0:
        SIZEFIT["t"] = now
        for k, d in SIZEFIT["b"].items():
            if len(d) >= SIZE_MIN_SAMPLES:
                a = np.array(d, dtype=np.float32)
                if float(a[:, 0].max() - a[:, 0].min()) < 0.12:
                    continue                             # all at the same distance: no line yet
                m, c = np.polyfit(a[:, 0], a[:, 1], 1)
                res = a[:, 1] - (m * a[:, 0] + c)
                ok = np.abs(res) < 2.5 * (np.std(res) + 1e-3)
                if ok.sum() >= SIZE_MIN_SAMPLES * 0.7:
                    m, c = np.polyfit(a[ok, 0], a[ok, 1], 1)
                if m > 0.05:                             # lower in the picture = bigger: a sensible line
                    SIZEFIT["fit"][k] = (float(m), float(c), len(d))


def size_expected(box, ph):
    f = SIZEFIT["fit"].get(_size_bucket())
    if not f or ph <= 0:
        return None
    yb = (box[1] + box[3]) / ph
    e = f[0] * yb + f[1]
    return e if e > 0.02 else None


def size_ok(t, ph):
    """False when the thing is much smaller than a person standing at that place would be (crouching persons are about half
    as high, crawling ones a third - so only clearly smaller things are refused, and never one the AI calls a person)"""
    if not CFG.get("size_check", True) or getattr(t, "ai_confirmed", False):
        return True
    e = size_expected(t.box, ph)
    if e is None:
        return True
    h = t.box[3] / ph
    small = h < 0.28 * e
    if small and not getattr(t, "_size_rej", False):
        t._size_rej = True; SIZEFIT["rejects"] += 1
    return not small


def size_state():
    f = SIZEFIT["fit"].get(_size_bucket())
    return {"learned": bool(f), "persons": int(f[2]) if f else len(SIZEFIT["b"].get(_size_bucket(), [])), "rejects": SIZEFIT["rejects"]}


def foot_selftest():
    """real-reh-fusspunkt (232, third round): at night a roe deer / fox from the SIDE (flat) is an animal; a child 1.0 m, a
    crouching person (also one that never stands up), a roe deer straight from the front and a standing person stay persons;
    a crawling person is an animal without an AI hint and «Person?» with AI >= 0.15 + movement / warmth; by day no animal.
    Camera 1.6 m high, 6° down - boxes from the flat-ground geometry with the field of view of this camera."""
    vf, cam_h, pitch = erk_vfov(), 1.6, -6.0
    hf = cam_fov()[0]
    k = math.tan(math.radians(vf) / 2.0)
    ThermalCam.main_aspect = 9 / 16.0

    def box(dist, height, width=0.4, cx=0.5, ch=None):
        ch = cam_h if ch is None else ch                     # ch = the real camera height (the estimate below uses cam_h)

        def row(z):                                          # picture row 0..1 of a point z m above the ground at dist m
            return 0.5 + math.tan(math.atan((ch - z) / dist) + math.radians(pitch)) / (2.0 * k)
        y0, y1 = row(height), row(0.0)
        w = width / (2.0 * dist * math.tan(math.radians(hf) / 2.0))
        return (cx - w / 2.0, y0, w, y1 - y0)

    def run(seq, night=True, maybe=False, ch=None):
        """seq = [(dist, height, width)] one picture each 0.5 s -> the last decision (like thermal_classify); ch = real
        camera height (the foot point always assumes cam_h = 1.6 m)"""
        hist = deque(maxlen=50); c = None
        for n, (dist, height, width) in enumerate(seq):
            b = box(dist, height, width, ch=ch)
            d = thermal_person_check(b)
            c = foot_decide(b, d, foot_estimate(b, cam_h, pitch, vf) if d is None else None, night, 100.0 + 0.5 * n, hist, maybe, vf)
        return c[0] if c else None
    for dist, height in ((6.0, 1.75), (12.0, 1.6), (9.0, 0.85), (5.0, 0.45)):
        fe = foot_estimate(box(dist, height), cam_h, pitch, vf)
        assert fe is not None and abs(fe[0] - dist) < 0.05 * dist and abs(fe[1] - height) < 0.05, (dist, height, fe)
    assert foot_estimate(box(40.0, 1.7), cam_h, 6.0, vf) is None          # feet near the horizon: no estimate
    assert foot_estimate((0.5, 0.3, 0.05, 0.7), cam_h, pitch, vf) is None  # cut off at the lower edge
    deer_side = [(10.0 - 0.6 * i, 0.9, 1.3) for i in range(5)]            # h/w 0.69
    fox_side = [(9.0 - 0.8 * i, 0.45, 0.8) for i in range(5)]             # h/w 0.56
    crawl = [(7.0 - 0.2 * i, 0.45, 1.5) for i in range(5)]
    assert run(deer_side) == "animal" and run(fox_side) == "animal", (run(deer_side), run(fox_side))
    assert run(fox_side[:2]) == "wait"                                    # 2 pictures in 0.5 s: not decided yet
    assert run(fox_side, night=False) is None                             # by day: no animal (only warm, as before)
    assert run([(9.0, 1.05, 1.2)] * 5) is None                            # deer with the head high (0.88): only warm
    assert run([(9.0, 1.0, 0.35)] * 5) == "person"                        # roe deer straight from the front: person («im Zweifel»)
    assert run([(7.0, 1.0, 0.3)] * 5) == "person"                         # child 1.0 m
    assert run([(6.0, 1.0, 0.55)] * 8) == "person"                        # crouching, never stands up
    assert run([(6.0, 1.75, 0.5)] * 5) == "person"
    assert run([(6.0, 1.75, 0.5)] * 2 + crawl) is None                    # stood, then lies down: never an animal
    assert run(crawl) == "animal" and run(crawl, maybe=True) is None      # crawling: animal without AI, «Person?» wins
    tr_ = [(0.40, 0.70, 0.22, 0.10)]                                      # a movement track at the same place
    assert weak_person_check((0.41, 0.71, 0.20, 0.08, 0.17), tr_, [], None)
    assert not weak_person_check((0.41, 0.71, 0.20, 0.08, 0.10), tr_, [], None)     # AI below 0.15
    assert not weak_person_check((0.41, 0.71, 0.20, 0.08, 0.17), [], [], None)      # nothing confirms it
    assert not weak_person_check((0.45, 0.50, 0.05, 0.30, 0.20), [(0.45, 0.5, 0.05, 0.3)], [], None)   # upright: not flat
    # camera 30 % higher than thought (really 2.1 m, the foot point assumes 1.6 m): the boxes are made with 2.1 m, judged with
    # 1.6 m (Code-Prüfung K8: before, the test gave fe=None with an upright box - the foot point was never used)
    fe_hi = foot_estimate(box(8.0, 0.5, 0.9, ch=2.1), cam_h, pitch, vf)
    assert fe_hi is not None and fe_hi[0] < 8.0 * 0.85, ("the wrong height must change the foot distance", fe_hi)
    assert run([(8.0, 1.65, 0.5)] * 5, ch=2.1) == "person"                # standing
    assert run([(7.0, 1.0, 0.3)] * 5, ch=2.1) == "person"                 # child 1.0 m
    assert run([(6.0, 1.0, 0.55)] * 8, ch=2.1) == "person"                # crouching, never stands up
    assert run([(9.0, 1.0, 0.35)] * 5, ch=2.1) == "person"                # roe deer straight from the front
    wide = box(6.0, 1.0, 0.8, ch=2.1)                                    # crouching wide (h/w 1.25): not upright -> foot point
    assert thermal_person_check(wide) is None and foot_estimate(wide, cam_h, pitch, vf) is not None
    assert run([(6.0, 1.0, 0.8)] * 8, ch=2.1) is None                     # ... and still no animal (only warm)
    crawl_hi = [(7.0 - 0.2 * i, 0.45, 1.5) for i in range(5)]
    assert run(crawl_hi, maybe=True, ch=2.1) is None                      # crawling + AI hint («Person?»): never an animal
    assert run(crawl_hi, ch=2.1) == "animal"                              # without AI hint: thermal_person_feed decides (M3)
    return True


def thermal_maybe_selftest():
    """Code-Prüfung M3: a flat warm body that the foot point calls «animal» is only an animal when the AI really looked for
    weak persons (own run or PC helper with the standard model) - AI off / helper without weak boxes: «Person?» (alarm)"""
    class _AI:
        weak_ok_t = 0.0
    keep = (globals()["thermal_classify"], CFG.get("ai_enabled"), DEMO.get("on"), dict(TPERS), STATE.get("person_maybe"))
    _le = globals()["log_event"]
    try:
        globals()["thermal_classify"] = lambda b, t0=None, maybe=False: ("animal", 6.0, 0.45, 14.0)
        globals()["log_event"] = lambda *a, **k: None
        CFG["ai_enabled"] = True; DEMO["on"] = False
        fr = np.zeros((90, 160, 3), np.uint8)
        wb = [(0.40, 0.70, 0.22, 0.08)]

        def feed(ai, t0=100.0):
            pb, pres = [], set()
            rest = thermal_person_feed(list(wb), pb, pres, fr, 160, 90, 160, 90, t0, (), ai=ai)
            return pres, pb, rest
        ai = _AI(); ai.weak_ok_t = 99.0                     # the AI looked 1 s ago: an animal, no person
        pres, pb, rest = feed(ai)
        assert "animal" in pres and "person" not in pres and not pb and rest == wb, (pres, pb)
        ai.weak_ok_t = 0.0                                   # helper without weak boxes / AI not running: «Person?»
        pres, pb, rest = feed(ai)
        assert "person" in pres and "animal" not in pres and len(pb) == 1 and not rest, ("no «Person?» without the AI", pres)
        ai.weak_ok_t = 99.0; CFG["ai_enabled"] = False       # AI switched off: «Person?»
        pres, pb, rest = feed(ai)
        assert "person" in pres and "animal" not in pres, ("AI off: animal", pres)
        CFG["ai_enabled"] = True
        assert not thermal_ai_checked(100.0, None) or WATCH_REF.get("w") is not None
        assert thermal_ai_checked(100.0, ai) and not thermal_ai_checked(100.0 + WEAK_OK_S + 1, ai)
    finally:
        globals()["thermal_classify"] = keep[0]; globals()["log_event"] = _le
        CFG["ai_enabled"] = keep[1]; DEMO["on"] = keep[2]; TPERS.clear(); TPERS.update(keep[3]); STATE["person_maybe"] = keep[4]
    return "flat warm body: animal only after an AI check, else «Person?» (AI off, PC helper without weak boxes)"

SELFTEST_EXTRA.append(("Thermal picture: animal or person from the foot point (232)", foot_selftest))
SELFTEST_EXTRA.append(("Thermal picture: no «animal» without an AI check, «Person?» instead (232, M3)", thermal_maybe_selftest))
