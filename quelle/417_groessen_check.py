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
    """real-reh-fusspunkt (232): at night a roe deer / fox is an animal; a child 1.0 m upright, a crouching person who stands
    up and a standing person stay persons; by day nothing becomes an animal; crawling (wide box) is no thermal person at all
    (documented limit). Camera 1.6 m high, 6° down, Camera Module 3 (41° vertical) - boxes from the flat-ground geometry."""
    vf, cam_h, pitch = 41.0, 1.6, -6.0
    hf = cam_fov()[0]
    k = math.tan(math.radians(vf) / 2.0)

    def box(dist, height, width=0.4, cx=0.5):
        def row(z):                                          # picture row 0..1 of a point z m above the ground at dist m
            return 0.5 + math.tan(math.atan((cam_h - z) / dist) + math.radians(pitch)) / (2.0 * k)
        y0, y1 = row(height), row(0.0)
        w = width / (2.0 * dist * math.tan(math.radians(hf) / 2.0))
        return (cx - w / 2.0, y0, w, y1 - y0)

    def run(seq, night=True):
        """seq = [(dist, height, width)] one picture each 0.5 s -> the last decision"""
        hist = deque(maxlen=50); c = None
        for n, (dist, height, width) in enumerate(seq):
            b = box(dist, height, width)
            fe = foot_estimate(b, cam_h, pitch, vf)
            d = PERSON_H_M / (2.0 * b[3] * k)
            c = foot_decide(b, d, fe, night, 100.0 + 0.5 * n, hist)
        return c[0]
    for dist, height in ((6.0, 1.75), (12.0, 1.6), (9.0, 0.85), (5.0, 0.45)):
        fe = foot_estimate(box(dist, height), cam_h, pitch, vf)
        assert fe is not None and abs(fe[0] - dist) < 0.05 * dist and abs(fe[1] - height) < 0.05, (dist, height, fe)
    assert foot_estimate(box(40.0, 1.7), cam_h, 6.0, vf) is None          # feet near the horizon: no estimate
    assert foot_estimate((0.5, 0.3, 0.05, 0.7), cam_h, pitch, vf) is None  # cut off at the lower edge
    fox = [(9.0 - 0.8 * i, 0.45, 0.24) for i in range(5)]                 # fox from the front, coming closer
    deer = [(10.0 - 0.6 * i, 0.95, 0.55) for i in range(5)]               # roe deer at an angle
    assert run(fox) == "animal" and run(deer) == "animal", (run(fox), run(deer))
    assert run(fox[:2]) == "wait"                                         # 2 pictures in 0.5 s: not yet decided
    assert run(fox, night=False) == "person"                              # by day: no animal from the thermal picture
    assert run([(7.0, 1.0, 0.3)] * 5) == "person"                         # child 1.0 m, upright and narrow
    assert run([(7.0, 1.0, 0.45)] * 5) == "person"                        # ... with 1 pixel of thermal blur
    assert run([(6.0, 1.75, 0.5)] * 5) == "person"                        # standing adult
    assert run([(6.0, 1.75, 0.5)] * 2 + [(6.0, 0.95, 0.6)] * 6) == "person"   # stands, then crouches: stays a person
    assert run([(6.0, 0.95, 0.6)] * 3 + [(6.0, 1.7, 0.5)]) == "person"    # crouching, then stands up: person at once
    ThermalCam.main_aspect = 9 / 16.0
    assert thermal_person_check(box(6.0, 0.45, 1.6)) is None              # crawling (wide): never a thermal person (limit)
    hist = deque(maxlen=50)                                               # camera 30 % higher than thought: still a person
    b = box(8.0, 1.65, 0.5)
    assert foot_decide(b, PERSON_H_M / (2.0 * b[3] * k), foot_estimate(b, cam_h * 0.7, pitch, vf), True, 1.0, hist)[0] == "person"
    return True


SELFTEST_EXTRA.append(("Thermal picture: animal or person from the foot point (232)", foot_selftest))
