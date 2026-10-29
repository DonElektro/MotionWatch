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
