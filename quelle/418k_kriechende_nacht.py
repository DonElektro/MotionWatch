#@ MoveEye – Teil 418k: Kriechende nachts – Voralarm «etwas Grosses am Boden», dann «Person?». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# real-erk-e3 (31.10.2026, grosser Erkennungstest REAL_ERKENNUNG.md, Schwachstelle 3): nachts wurde nur 1 von 3 kriechenden /
# geduckten Personen erkannt; auf dem Stellplatz robbte jemand auf 5 m gut sichtbar durchs Infrarot-Licht und MoveEye meldete
# nur «Bewegung». Die KI kennt kaum liegende Menschen (COCO), das Wärmebild sah einen flachen warmen Körper - und die Reh-Regel
# (232, real-reh-fusspunkt) nennt einen flachen warmen Körper am Boden nachts «Tier».
# Neu (erweitert 232, ohne die Reh-Regel zu ändern): nachts ein warmer Körper (Wärmebild) an derselben Stelle wie Bewegung
# (Kamera), NAH (Fusspunkt unter CRAWL_NEAR_M), am Boden (oberer Rand unter CRAWL_TOP_M) und GROSS (CRAWL_MIN_LEN_M lang, oder
# kommt er gerade auf die Kamera zu: CRAWL_HEADON_W_M breit) gibt
#   1. sofort den Voralarm «etwas Grosses am Boden» (Info): Eintrag im Protokoll, Browser-Voralarm, eine kurze Push-Nachricht
#      mit Bild (Titel «Etwas Grosses am Boden», eigene Abkühlzeit prealarm_cooldown) - nur wenn der Schutz an ist,
#   2. hält es CRAWL_ESC_S an (dieselbe Stelle, kurze Lücken erlaubt), war es dabei einmal LANG (CRAWL_MIN_LEN_M - von vorne
#      sehen eine kriechende Person und ein schräg kommender Fuchs gleich breit aus), ist es niedrig (oberer Rand unter
#      CRAWL_ESC_TOP_M) und hat die KI dort kein Tier gesehen: «PERSON? (KRIECHT)» = eine Person für die normale Alarm-Logik (Push, Aufnahme,
#      Sirene). Die «Person?»-Regel von 2.98.95 (232 weak_person_feed: schwache KI + flach + Bewegung / Wärme) bleibt und
#      greift oft schon früher - dann ist es sofort eine Person.
# Kurzer Push-Text: Notifier.info mit Titel «{name}: Something big at the ground»; das neue Push-Format (635b push_short, 3.1.0)
# kennt den Titel über PK_TITLES, sobald es auf main ist (crawl_push trägt ihn dort ein, wenn es PK_TITLES gibt).
# Abgrenzung zu Tieren (Daniel: Igel und Fuchs sind kleiner und wärmer):
#   - KLEINER ist das sichere Merkmal, darum die Länge: Igel 0.2-0.3 m, Katze ~0.45 m, Marder ~0.5 m, Feldhase ~0.55 m,
#     Dachs ~0.75 m, Fuchs Kopf-Rumpf 0.6-0.9 m (Wildtier Schweiz; Körperlängen auch in simulator3d/scripts/waerme.gd ANIMALS);
#     eine kriechende / robbende Person ist 1.2 m (auf Knien) bis 1.9 m (flach mit Armen vorne) lang -> CRAWL_MIN_LEN_M 1.0.
#     Der Fuchsschwanz (0.35-0.45 m) ist im Wärmebild kühl (Fell, kaum durchblutet) und zählt kaum zur warmen Fläche.
#   - WÄRMER ist im Wärmebild kein sicheres Merkmal: Fell-Oberfläche Fuchs bei 8 °C Luft ~17 °C, Igel ~19 °C, Kleider einer
#     Person mit Jacke ~19 °C, Daunenjacke ~15 °C, das Gesicht 33 °C (waerme.gd nach McCafferty 2007 / ISO 9920). Ein kleines
#     Tier ist zwar als GANZES warm (kein kalter Stoff), eine Person hat kühle Kleider und heisse Stellen - bei 80 x 62 Pixeln
#     (Thermal-90, ~1.1° pro Pixel: ein Fuchs auf 5 m sind ~7 x 4 Pixel) lässt sich das nicht verlässlich messen. Darum keine
#     Temperatur-Grenze; zu heiss (Motor, Feuer) fällt schon in 232 heraus (thermal_person_check: über 45 °C kein Mensch).
#   - Reh / Wildschwein (0.95-1.35 m) sind so lang wie eine kriechende Person: sie bekommen den Voralarm («im Zweifel
#     Person», es ist nur eine Info), aber KEIN «Person?»: ein stehendes Reh ist mit Kopf 0.9-1.1 m hoch, ein Wildschwein
#     0.8-0.95 m (Schulter 0.55-1.0 m) - über CRAWL_ESC_TOP_M 0.85; eine robbende Person ist 0.3-0.5 m hoch, auf Knien ~0.75 m.
#     Rest-Risiko: ein äsendes Reh (Kopf unten, Rücken ~0.75 m) 6 s nahe am Zelt - dann «Person?» (Daniel: im Zweifel Person).
#   - sieht die KI dort ein Tier (dog, sheep, cat, horse, cow, bird, animal), gibt es kein «Person?» (nur den Voralarm).
# Gegenprobe Wind (leerer Wald): ohne warmen Körper nichts (Äste sind im Wärmebild Lufttemperatur) - ohne Wärmebild-Kamera
# ist die Regel aus. Tags gilt sie nicht (Tags sieht die KI liegende Menschen besser, und Sonne wärmt den Boden).
# Selbsttest: crawl_selftest (Fuchs, Igel, Reh, Wildschwein, kriechende Person seitlich und von vorne, Tag, zu weit, ohne Bewegung).
# ----------------------------------------------------------------------------
CRAWL_NEAR_M = 8.0       # «nah»: unter 8 m (Erkennungstest: Kriechende auf 5-7 m; das Infrarot-Licht reicht ~8-10 m, dahinter
                         # sieht die Kamera keine Bewegung mehr am Boden)
CRAWL_MIN_LEN_M = 1.0    # «gross»: mindestens 1.0 m lang (Fuchs höchstens 0.9 m ohne Schwanz, Person kriechend 1.2-1.9 m)
CRAWL_HEADON_W_M = 0.4   # von vorne (kommt näher): Schulterbreite einer Person 0.4-0.5 m (mit Armen mehr); Fuchs / Reh von vorne
                         # 0.15-0.35 m - nur zusammen mit «kommt näher» (CRAWL_COMING_M), sonst ist ein seitlicher Fuchs 0.6 m auch breit
CRAWL_COMING_M = 0.5     # «kommt auf die Kamera zu»: der Fusspunkt ist seit dem ersten Bild mindestens 0.5 m näher gekommen
CRAWL_TOP_M = 1.1        # «am Boden»: der obere Rand liegt unter 1.1 m (wie FOOT_ANIMAL_MAX_H_M der Reh-Regel; stehend > 1.45 m)
CRAWL_FLAT = 1.0         # und es ist nicht aufrecht: echte Höhe / echte Länge höchstens 1.0 (Aufrechte prüft 232 als Person)
CRAWL_ESC_S = 6.0        # «hält an»: 6 s an derselben Stelle (kriechend 0.2-0.5 m/s = 1-3 m; ein Tier, das vorbeiläuft, ist weg)
CRAWL_GAP_S = 2.0        # Lücken bis 2 s gehören dazu (das Wärmebild meldet 3 von 5 Bildern, die KI / Bewegung setzt aus)
CRAWL_SAME = 0.2         # «dieselbe Stelle»: Mitte / Fusspunkt höchstens 0.2 Bildbreite / -höhe vom letzten Bild entfernt
CRAWL_ESC_TOP_M = 0.85   # «Person?» nur niedrig: robbend 0.3-0.5 m, auf Knien ~0.75 m; Reh mit Kopf 0.9-1.1 m, Wildschwein 0.8-0.95 m
CRAWL_REPEAT_S = 30.0    # ein neuer Voralarm (Protokoll / Push) frühestens nach 30 s Ruhe - nicht in jedem Bild
CRAWL = {"since": 0.0, "last": 0.0, "pos": None, "d0": None, "esc": False, "long": False, "said": 0.0, "push_t": 0.0, "n_pre": 0, "n_esc": 0, "info": None}
CRAWL_PK_TITLE = ("⚠", "Something big at the ground", "info", True)    # (symbol, short title, class, picture) for 635b PK_TITLES


def crawl_measure(box, cam_h=None, pitch=None, vf=None, hf=None):
    """{"d": foot distance m, "len": real length m, "top": height of the upper edge m or None, "cut": feet cut off} of a warm
    body (x, y, w, h 0..1 of the main picture) on flat ground - or None (feet at the horizon / too far up)"""
    x, y, w, h = box
    hf = cam_fov()[0] if hf is None else float(hf)
    cut = y + h > 0.985
    fe = foot_estimate((x, y, w, (0.98 - y) if cut else h), cam_h, pitch, vf)
    if fe is None:
        return None
    d = fe[0]                                            # cut off at the lower edge: it is NEARER than the lowest row - an upper
    ln = w * 2.0 * d * math.tan(math.radians(hf) / 2.0)  # bound for the distance and the length (the safe side: more «big»)
    return {"d": d, "len": ln, "top": None if cut else max(0.0, fe[1]), "cut": cut}


def crawl_decide(m, box, night, moving, t0, st=None, animal=False):
    """the decision without the camera (self-test): None / "pre" (Voralarm «something big at the ground») / "person" («Person?»).
    m = crawl_measure, box = (x, y, w, h) 0..1, moving = movement of the camera at the same place, animal = the AI sees an
    animal there. st = the state (CRAWL)."""
    st = CRAWL if st is None else st
    if not night or not moving or m is None or m["d"] > CRAWL_NEAR_M:
        return None
    top = m["top"]
    if top is not None and (top > CRAWL_TOP_M or top / max(0.05, m["len"]) > CRAWL_FLAT):
        return None                                      # not at the ground / upright (upright warm bodies: 232)
    cx, fy = box[0] + box[2] / 2.0, box[1] + box[3]
    same = st["pos"] is not None and t0 - st["last"] <= CRAWL_GAP_S and abs(cx - st["pos"][0]) <= CRAWL_SAME and abs(fy - st["pos"][1]) <= CRAWL_SAME
    if not same:                                         # a new thing (or after a gap): start again
        st.update(since=t0, d0=m["d"], esc=False, long=False)
    st.update(pos=(cx, fy), last=t0)
    long_ = m["len"] >= CRAWL_MIN_LEN_M
    st["long"] = bool(st.get("long")) or long_
    if not (long_ or (m["len"] >= CRAWL_HEADON_W_M and st["d0"] - m["d"] >= CRAWL_COMING_M)):
        return None                                      # small (fox, hedgehog, cat) - or turned for a moment: no alarm now
    low = top is None or top <= CRAWL_ESC_TOP_M
    # «Person?» only when it was LONG at least once (from the front a crawling person and a fox coming diagonally look alike:
    # 0.55 vs 0.6-0.7 m wide - then only the Voralarm; the «Person?» rule of 232 / turning sideways decides)
    if (st["esc"] or (t0 - st["since"] >= CRAWL_ESC_S and low and st["long"])) and not animal:
        st["esc"] = True
        return "person"
    return "pre"


def crawl_push(notifier, frame, d, ln):
    """the short push «Something big at the ground» (info, with a small picture) - only with the protection on, own cool-down"""
    pk = globals().get("PK_TITLES")
    if isinstance(pk, dict):
        pk.setdefault(CRAWL_PK_TITLE[1], CRAWL_PK_TITLE)    # 3.1.0 push format (635b): symbol + short title, one line
    now = time.time()
    if notifier is None or not is_armed() or not CFG.get("notify_on") or now - CRAWL["push_t"] < float(CFG.get("prealarm_cooldown", 120.0)):
        return False
    jpg = None
    if frame is not None and CFG.get("prealarm_photo", True):
        h_, w_ = frame.shape[:2]
        sm = cv2.resize(frame, (640, int(h_ * 640 / w_)), interpolation=cv2.INTER_AREA) if w_ > 640 else frame
        ok, buf = cv2.imencode(".jpg", sm, [cv2.IMWRITE_JPEG_QUALITY, 70])
        jpg = buf.tobytes() if ok else None
    txt = trf("about {d} m, about {l} m long - a crawling person?", d=dist_round(d), l=f"{ln:.1f}")
    if notifier.info(txt, title="{name}: " + tr("Something big at the ground"), jpg=jpg, fname="prealarm.jpg"):
        CRAWL["push_t"] = now
        return True
    return False


def crawl_feed(warm_boxes, tracks, animals, person_boxes, present, frame, pw, ph, W, H, t0, notifier=None):
    """410, at night: warm bodies (0..1) that are not under a person box already at the same place as movement (tracks / candidates, working
    picture) -> Voralarm or «Person?» (person_boxes). Returns the boxes that became «Person?» (0..1)."""
    STATE["crawl"] = 0
    if not warm_boxes:
        return []
    night = _foot_night()
    if not night:
        return []
    if person_boxes:                                     # a person elsewhere (maybe a fixed false one): only the warm bodies beside it
        pb = [(b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph) for b in person_boxes]
        warm_boxes = [b for b in warm_boxes if not any(_ov(b, q) > 0.3 for q in pb)]
    mv = [(t.box[0] / pw, t.box[1] / ph, t.box[2] / pw, t.box[3] / ph) for t in tracks if getattr(t, "box", None) and not getattr(t, "lost", 0)]
    an = [(o[0] / pw, o[1] / ph, o[2] / pw, o[3] / ph) for o in animals or []]
    best = None
    for b in warm_boxes:
        moving = any(_ov(b, q) > 0.3 for q in mv)
        if not moving:
            continue
        try:
            m = crawl_measure(b)
        except Exception:
            m = None
        if m is None:
            continue
        if best is None or m["len"] > best[1]["len"]:
            best = (b, m, any(_ov(b, q) > 0.3 for q in an))
    if best is None:
        return []
    b, m, animal = best
    c = crawl_decide(m, b, night, True, t0, CRAWL, animal)
    if c is None:
        return []
    CRAWL["info"] = {"d": round(m["d"], 1), "len": round(m["len"], 2), "top": None if m["top"] is None else round(m["top"], 2), "cut": m["cut"], "what": c}
    bx, by, bw, bh = b
    p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
    near = f"~{dist_round(m['d'])}m" if not m["cut"] else f"<{dist_round(m['d'])}m"
    if c == "pre":
        STATE["crawl"] = 1
        present.add("prealarm")
        cv2.rectangle(frame, p1, p2, (0, 165, 255), 2)
        cv2.putText(frame, f"BIG AT THE GROUND? {near} {m['len']:.1f}m", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
        if t0 - CRAWL["said"] > CRAWL_REPEAT_S:
            CRAWL["said"] = t0; CRAWL["n_pre"] += 1
            log_event("person", f"Something big at the ground, {near.lstrip('~')}, about {m['len']:.1f} m long - warm and moving "
                                f"(night): a crawling person? (pre-alarm)")
            push_alert("prealarm", "crawl", source=STATE.get("source_label", ""))
            try:
                crawl_push(notifier, frame, m["d"], m["len"])
            except Exception as e:
                log_event("sys", f"Push «something big at the ground»: {e}"[:160])
        return []
    STATE["crawl"] = 2
    person_boxes.append((int(bx * pw), int(by * ph), max(1, int(bw * pw)), max(1, int(bh * ph))))
    present.add("person")
    cv2.rectangle(frame, p1, p2, (60, 0, 255), 3)
    cv2.putText(frame, f"PERSON? (CRAWLING) {near}", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 0, 255), 2)
    if not CRAWL.get("esc_said") or t0 - CRAWL.get("esc_said", 0.0) > CRAWL_REPEAT_S:
        CRAWL["n_esc"] += 1
        log_event("person", f"Person? crawling - something big, warm and moving at the ground for {CRAWL_ESC_S:.0f} s, "
                            f"{near.lstrip('~')}, about {m['len']:.1f} m long")
    CRAWL["esc_said"] = t0
    return [b]


def crawl_selftest():
    """fox, hedgehog, roe deer, wild boar, crawling person from the side and from the front, by day, too far, without movement.
    Camera 1.6 m high, 6° down, head camera of the simulator (field of view of this camera) - boxes from the flat-ground geometry."""
    vf, cam_h, pitch = erk_vfov(), 1.6, -6.0
    hf = cam_fov()[0]
    k = math.tan(math.radians(vf) / 2.0)

    def box(dist, height, length, cx=0.5):
        def row(z):
            return 0.5 + math.tan(math.atan((cam_h - z) / dist) + math.radians(pitch)) / (2.0 * k)
        y0, y1 = row(height), row(0.0)
        w = length / (2.0 * dist * math.tan(math.radians(hf) / 2.0))
        return (cx - w / 2.0, y0, w, y1 - y0)

    def run(seq, night=True, moving=True, animal=False, dt=0.5):
        """seq = [(dist, height, length)], one picture each dt s -> the decisions"""
        st = {"since": 0.0, "last": 0.0, "pos": None, "d0": None, "esc": False, "long": False}
        out = []
        for n, (dist, height, length) in enumerate(seq):
            b = box(dist, height, length)
            out.append(crawl_decide(crawl_measure(b, cam_h, pitch, vf, hf), b, night, moving, 100.0 + dt * n, st, animal))
        return out
    m = crawl_measure(box(5.0, 0.4, 1.7), cam_h, pitch, vf, hf)
    assert m and abs(m["d"] - 5.0) < 0.3 and abs(m["len"] - 1.7) < 0.15 and abs(m["top"] - 0.4) < 0.1, m
    crawl = [(5.5 - 0.1 * i, 0.4, 1.7) for i in range(16)]               # robbing from the side, 0.2 m/s, 8 s
    r = run(crawl)
    assert r[0] == "pre" and r[-1] == "person" and r.index("person") == 12, r      # Voralarm at once, «Person?» after 6 s
    assert run(crawl, night=False) == [None] * 16                          # by day: not this rule
    assert run(crawl, moving=False) == [None] * 16                         # warm but nothing moves (a warm stone, a sleeper)
    assert set(run(crawl, animal=True)) == {"pre"}                         # the AI sees an animal there: only the Voralarm
    knees = [(6.0 - 0.1 * i, 0.75, 1.2) for i in range(16)]                # on hands and knees, 0.75 m high
    assert run(knees)[-1] == "person"
    assert run([(10.0, 0.4, 1.7)] * 16) == [None] * 16                     # 10 m: too far for this rule
    fox = [(5.0, 0.45, 0.8)] * 16                                         # fox from the side 0.8 m, 0.45 m high, walks across
    hedgehog = [(3.0 - 0.05 * i, 0.15, 0.25) for i in range(16)]
    assert set(run(fox)) == {None} and set(run(hedgehog)) == {None}, (run(fox), run(hedgehog))
    fox_front = [(7.0 - 0.3 * i, 0.45, 0.2) for i in range(16)]           # fox straight at the camera: 0.2 m wide
    assert set(run(fox_front)) == {None}
    fox_diag = [(7.0 - 0.3 * i, 0.45, 0.65) for i in range(16)]           # fox coming diagonally (0.65 m wide): never «Person?»
    assert "person" not in run(fox_diag)
    front = [(7.5 - 0.15 * i, 0.4, 0.55) for i in range(16)]              # a person crawling straight at the camera, 0.55 m wide
    rf = run(front)
    assert rf[0] is None and "pre" in rf and "person" not in rf, rf       # Voralarm once it came 0.5 m nearer …
    rt = run(front + [(5.0, 0.4, 1.6)] * 2)                               # … «Person?» once it is seen long (turns sideways)
    assert rt[-1] == "person", rt
    deer = [(6.0 - 0.1 * i, 1.0, 1.3) for i in range(16)]                  # roe deer, head up 1.0 m: Voralarm, never «Person?»
    boar = [(6.0 - 0.1 * i, 0.9, 1.3) for i in range(16)]
    assert set(run(deer)) == {"pre"} and set(run(boar)) == {"pre"}, (run(deer), run(boar))
    assert run([(6.0, 1.75, 0.5)] * 4) == [None] * 4                       # standing person: upright - 232 does it
    gap = [(5.5, 0.4, 1.7)] * 6 + [(5.5, 0.4, 1.7)] * 10                  # 3 s gap after the 6th picture: starts again
    st = {"since": 0.0, "last": 0.0, "pos": None, "d0": None, "esc": False, "long": False}
    b = box(5.5, 0.4, 1.7); mm = crawl_measure(b, cam_h, pitch, vf, hf)
    seq = [crawl_decide(mm, b, True, True, t, st) for t in (0.0, 1.0, 2.0, 5.0, 6.0, 7.0, 8.0, 10.0, 11.5)]
    assert seq[:7] == ["pre"] * 7 and seq[-1] == "person", seq             # after the gap the 6 s count from 5.0
    cut = crawl_measure((0.1, 0.8, 0.45, 0.2), cam_h, pitch, vf, hf)      # cut off at the lower edge: near, length an upper bound
    assert cut and cut["cut"] and cut["top"] is None and cut["d"] < 4.0 and cut["len"] > 1.0, cut
    return True


SELFTEST_EXTRA.append(("Crawling at night: «something big at the ground», then «Person?» (418k)", crawl_selftest))
