"""Grosser Erkennungstest - Treiber. Nur Steuer-API des Simulators und die Web-API von MoveEye (nichts geändert).
Fortsetzbar: Fälle, die schon in results.jsonl stehen, werden übersprungen.
Aufruf: python3 driver.py PLATZ[,PLATZ…]"""
import sys, json, math, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

RES = OUT + "/results.jsonl"
ANIMAL_LABELS = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "teddy bear", "animal"}
VEH_LABELS = {"car", "truck", "bus", "motorcycle", "bicycle", "train", "boat", "airplane"}
SPAN = 48.0          # degrees to the side where a non-person visitor starts / ends (head camera ±33°)

# condition: name, hour, weather, ir, dists (walk, crawl, child)
COND = {
    "tag":        ("Tag, klar", 12.0, "clear", False, (10.0, 7.0, 8.0)),
    "daemmerung": ("Dämmerung, klar", 17.5, "clear", False, (9.0, 6.0, 7.0)),
    "nacht":      ("Nacht, klar, Infrarot", 23.0, "clear", True, (7.0, 5.0, 6.0)),
    "regen":      ("Tag, Regen", 14.0, "rain", False, (10.0, 7.0, 8.0)),
    "nebel":      ("Tag, Nebel", 9.5, "fog", False, (10.0, 7.0, 8.0)),
    "schnee":     ("Tag, Schnee", 15.0, "snow", False, (10.0, 7.0, 8.0)),
    "nachtregen": ("Nacht, Regen, Infrarot", 23.5, "rain", True, (7.0, 5.0, 6.0)),
}
ANIMALS = [("deer", 12.0), ("fox", 8.0), ("cat", 6.0), ("dog", 8.0), ("crows", 8.0), ("boar", 10.0), ("hedgehog", 4.0),
           ("magpies", 7.0), ("hare", 8.0), ("badger", 6.0)]
# place id -> (world, conditions)
PLAN = {
    "camping":    ("camping", ["tag", "daemmerung", "nacht", "regen"]),
    "wald":       ("bergtal", ["tag", "daemmerung", "nacht", "nebel"]),
    "stellplatz": ("ferienpark", ["tag", "daemmerung", "nacht", "schnee"]),
    "garten":     ("daheim", ["tag", "daemmerung", "nacht", "nachtregen"]),
    "festival":   ("festival", ["tag", "daemmerung", "nacht", "regen"]),
    "wild":       ("bergtal", ["tag", "daemmerung", "nacht", "schnee"]),
    "parkplatz":  ("ferienpark", ["tag", "daemmerung", "nacht", "nebel"]),
    "baustelle":  ("daheim", ["tag", "daemmerung", "nacht", "nachtregen"]),
}


def done_keys():
    k = set()
    if os.path.exists(RES):
        for ln in open(RES):
            try:
                k.add(json.loads(ln)["key"])
            except Exception:
                pass
    return k


def save(rec):
    with open(RES, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def pan_deg():
    try:
        return float(ctl(action="servo")["info"]["pan"]["head"])
    except Exception:
        return 0.0


def in_view(dist, off):
    """ground point dist m from MoveEye (at 0/0, rig looks -z) in the direction of the head + off degrees (+ = right)"""
    a = math.radians(-pan_deg() + off)
    return [round(math.sin(a) * dist, 2), round(-math.cos(a) * dist, 2)]


def cross(dist):
    r = dist / math.cos(math.radians(SPAN))
    s = 1 if time.time() % 2 < 1 else -1
    return in_view(r, -s * SPAN), in_view(r, s * SPAN)


def msg_ids():
    m = mw_messages()
    return {str(x.get("id")): x for x in (m.get("items") or [])} if isinstance(m, dict) else {}


def _iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0.0, min(ay2, by2) - max(a[1], b[1]))
    i = iw * ih
    u = a[2] * a[3] + b[2] * b[3] - i
    return i / u if u > 0 else 0.0


def baseline(secs=3.0):
    """what MoveEye reports with nobody there (static false persons, objects of the scene)"""
    labs, boxes, pers = set(), [], 0
    t_end = time.time() + secs
    while time.time() < t_end:
        try:
            s = mw_state()
            labs |= set(s.get("present") or [])
            if int(s.get("persons") or 0) > 0:
                pers += 1
                boxes += [list(b)[:4] for b in (s.get("person_boxes") or [])]
        except Exception:
            pass
        time.sleep(0.5)
    return labs, boxes


def new_boxes(s, base_boxes):
    out = []
    if int(s.get("persons") or 0) <= 0:
        return out
    for b in s.get("person_boxes") or []:
        b = list(b)[:4]
        if all(_iou(b, q) < 0.3 for q in base_boxes):
            out.append(b)
    return out


def observe(secs, tag, want, t_spawn, base):
    """poll MoveEye; want = person | animal | vehicle | none. base = (labels, person boxes) seen before with nobody there."""
    base_labs, base_boxes = base
    seen = {}            # label -> first time (only labels that were not there before)
    first_person = None
    person_eps = 0
    prev_p = 0
    warm = None
    fps = []
    shot_first = shot_mid = ""
    msgs0 = msg_ids()
    t_end = t_spawn + secs
    while time.time() < t_end:
        try:
            s = mw_state()
        except Exception:
            time.sleep(0.5)
            continue
        t = round(time.time() - t_spawn, 1)
        nb = new_boxes(s, base_boxes)
        p = len(nb)
        fps.append(float(s.get("fps") or 0))
        for lab in s.get("present") or []:
            if lab not in base_labs:
                seen.setdefault(lab, t)
        if p > 0 and prev_p == 0:
            person_eps += 1
        if p > 0 and first_person is None:
            first_person = t
            fn = "%s_erkannt.jpg" % tag
            if frame(SHOTS + "/" + fn):
                shot_first = fn
        if int(s.get("warm") or 0) > 0 and warm is None:
            warm = t
        if not shot_mid and t >= secs * 0.45:
            fn = "%s_mitte.jpg" % tag
            if frame(SHOTS + "/" + fn):
                shot_mid = fn
        prev_p = p
        time.sleep(0.5)
    new = [m for i, m in msg_ids().items() if i not in msgs0]
    labs = sorted(seen)
    animal_l = sorted(set(labs) & ANIMAL_LABELS)
    veh_l = sorted(set(labs) & (VEH_LABELS - {"bicycle"}))
    rec = {"seen": {k: seen[k] for k in labs}, "base_labels": sorted(base_labs), "static_person_boxes": len(base_boxes) > 0,
           "first_person_s": first_person, "person_eps": person_eps, "warm_s": warm,
           "pushes": [[m.get("ev"), round(float(m.get("t", 0)) - t_spawn, 1), (m.get("text") or "")[:80]] for m in new],
           "fps": round(sum(fps) / len(fps), 1) if fps else 0, "shot_first": shot_first, "shot_mid": shot_mid}
    if want == "person":
        rec["detected"] = first_person is not None
        rec["t_detect"] = first_person
        rec["as"] = "Person" if first_person is not None else (", ".join(animal_l + veh_l) or ("Wärme" if warm is not None else ("nur Bewegung" if "motion" in seen or "prealarm" in seen else "–")))
    elif want == "animal":
        ts = [seen[l] for l in animal_l]
        rec["detected"] = bool(ts)
        rec["t_detect"] = min(ts) if ts else None
        rec["as"] = ", ".join(animal_l) if animal_l else ("Person" if first_person is not None else ("nur Bewegung" if "motion" in seen or "prealarm" in seen else "–"))
        rec["false_person"] = first_person is not None
    elif want == "vehicle":
        ts = [seen[l] for l in veh_l]
        rec["detected"] = bool(ts)
        rec["t_detect"] = min(ts) if ts else None
        rec["as"] = ", ".join(veh_l) if veh_l else ("Person" if first_person is not None else ("nur Bewegung" if "motion" in seen or "prealarm" in seen else "–"))
        rec["false_person"] = first_person is not None
    else:
        rec["false_person_eps"] = person_eps
        rec["false_pushes"] = len([m for m in new if m.get("ev") in ("person", "warm", "prealarm")])
        rec["false_animal"] = animal_l
    return rec


def set_cond(ck):
    name, hour, weather, ir, _ = COND[ck]
    ctl(action="set", id="hour", value=hour)
    ctl(action="set", id="weather", value=weather)
    ctl(action="set", id="wind", value=12)
    ctl(action="set", id="cond_ir", value=ir)
    ctl(action="set", id="cond_headlights", value=False)
    ctl(action="set", id="speed", value=1)


def clear():
    try:
        ctl(action="press", id="clear")
    except Exception:
        pass


def run_case(place, ck, ev, i, done):
    key = "%s|%s|%s" % (place, ck, ev)
    if key in done:
        return
    world = PLAN[place][0]
    name, hour, weather, ir, (dw, dc, dk) = COND[ck]
    if load() >= 5.0:
        lw = time.time()
        l = wait_load(5.0, 420)
        log("  Last-Pause %.0f s, Last jetzt %.1f" % (time.time() - lw, l))
    tag = "%s_%s_%s" % (place, ck, ev)
    clear()
    time.sleep(2)
    base = baseline(3.0)
    if base[1] and not os.path.exists(SHOTS + "/%s_%s_statisch.jpg" % (place, ck)):
        frame(SHOTS + "/%s_%s_statisch.jpg" % (place, ck))
    want, secs, info = "person", 18.0, ""
    t0 = time.time()
    if ev == "gehen":
        r = ctl(action="menschen", do="probe", gait="walk", dist=dw)
        info = "geht quer, %.0f m" % dw
    elif ev == "kriechen":
        g = "crawl" if i % 2 == 0 else "sneak"
        r = ctl(action="menschen", do="probe", gait=g, dist=dc, dark=True)
        info = "%s, dunkle Kleidung, %.0f m" % ("kriecht" if g == "crawl" else "geduckt", dc)
        secs = 22.0
    elif ev == "kind":
        a, b = cross(dk)
        r = ctl(action="spawn_at", kind="child", **{"from": a, "to": b})
        info = "Kind, %.0f m" % dk
    elif ev == "tier":
        global ANI_I
        kind, d = ANIMALS[ANI_I % len(ANIMALS)]
        ANI_I += 1
        if ck == "nacht" or ck == "nachtregen":
            d = min(d, 7.0)
        a, b = cross(d)
        r = ctl(action="spawn_at", kind=kind, **{"from": a, "to": b})
        want, info = "animal", "%s, %.0f m" % (kind, d)
        ev_kind = kind
    elif ev == "fahrzeug":
        if ir:
            ctl(action="set", id="cond_headlights", value=True)
        a, b = cross(20.0)
        r = ctl(action="spawn_at", kind="car", **{"from": a, "to": b})
        want, secs, info = "vehicle", 14.0, "Auto, 20 m" + (" + Scheinwerfer" if ir else "")
    elif ev == "leer":
        ctl(action="set", id="wind", value=55)
        want, secs, info = "none", 45.0, "nichts, Wind 55 km/h (Äste)"
        r = {"ok": True}
    t_spawn = time.time()
    rec = observe(secs, tag, want, t_spawn, base)
    rec.update({"key": key, "place": place, "world": world, "cond": ck, "cond_name": name, "event": ev, "info": info,
                "spawn_ok": bool(r.get("ok", False)), "secs": secs, "t": time.strftime("%H:%M:%S"), "load": load()})
    if ev == "tier":
        rec["animal"] = ev_kind
    ctl(action="set", id="wind", value=12)
    ctl(action="set", id="cond_headlights", value=False)
    save(rec)
    log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("t_detect", ""), "fps", rec["fps"], "pushes", len(rec["pushes"]))


def blind(place, ck, done):
    key = "%s|%s|blindmap" % (place, ck)
    if key in done:
        return
    night = COND[ck][3]
    clear()
    time.sleep(2)
    base = baseline(3.0)
    ds = [4, 7, 10, 14, 18] if night else [5, 10, 15, 20, 25]
    r = ctl(action="blindmap", do="start", az=[-25, 0, 25], dist=ds, walk=True)
    t0 = time.time()
    res = {}
    while time.time() - t0 < 200:
        time.sleep(3)
        try:
            b = ctl(action="blindmap", do="info")
        except Exception:
            continue
        if not b.get("busy"):
            res = b.get("result") or {}
            break
    rec = {"key": key, "place": place, "world": PLAN[place][0], "cond": ck, "cond_name": COND[ck][0], "event": "blindmap",
           "static_person_boxes": len(base[1]) > 0, "result": res, "start": r, "secs": round(time.time() - t0), "t": time.strftime("%H:%M:%S")}
    set_cond(ck)
    save(rec)
    log(key, "->", res.get("found"), "/", res.get("inview"), "im Bild, von", res.get("n"), "max", res.get("max_found"))


def goto_place(place):
    world = PLAN[place][0]
    t0 = time.time()
    r = ctl(action="scenario", id=place)
    for _ in range(90):
        time.sleep(2)
        try:
            st = ctl(action="get")["status"]
            s = mw_state()
            if "verbunden" in st and float(s.get("fps") or 0) > 0.5:
                break
        except Exception:
            pass
    ctl(action="set", id="auto", value=False)
    ctl(action="set", id="season", value="today")
    clear()
    log("Ort", place, "Welt", world, "geladen in %.0f s" % (time.time() - t0), r.get("ok", r))


def zimmer(done):
    """Schlafzimmer (Welt Zuhause): Hamster im Laufrad (Nacht), Spinne vor der Linse (Nacht, Infrarot), Wellensittich (Tag), Leerlauf"""
    place = "schlafzimmer"
    goto_place(place)
    ctl(action="zimmertiere", do="set", pets=True, spider=True)
    cases = [("nacht", "hamster", lambda: ctl(action="zimmertiere", do="state", who="hamster", state="wheel", dur=40, hold=True)),
             ("nacht", "spinne", lambda: ctl(action="zimmertiere", do="lens", dist=0.12, hold=True)),
             ("nacht", "leer", None),
             ("tag", "vogel", lambda: ctl(action="zimmertiere", do="state", who="vogel", state="fly", dur=30, hold=True)),
             ("tag", "leer", None)]
    last = ""
    for ck, ev, f in cases:
        key = "%s|%s|%s" % (place, ck, ev)
        if key in done:
            continue
        if ck != last:
            set_cond(ck)
            time.sleep(15)
            last = ck
        base = baseline(3.0)
        r = f() if f else {"ok": True}
        t_spawn = time.time()
        rec = observe(40.0 if f else 45.0, "%s_%s_%s" % (place, ck, ev), "animal" if f else "none", t_spawn, base)
        rec.update({"key": key, "place": place, "world": "daheim", "cond": ck, "cond_name": COND[ck][0], "event": "tier" if f else "leer",
                    "animal": ev if f else "", "info": ev, "spawn_ok": bool(r.get("ok", False)), "ctl": r, "secs": 40, "t": time.strftime("%H:%M:%S"), "load": load()})
        save(rec)
        log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("false_person", ""), r)
        try:
            ctl(action="zimmertiere", do="state", who="hamster", hold=False)
        except Exception:
            pass


ANI_I = 0
EVENTS = ["leer", "gehen", "kriechen", "kind", "tier", "fahrzeug"]

if __name__ == "__main__":
    places = sys.argv[1].split(",") if len(sys.argv) > 1 else list(PLAN)
    done = done_keys()
    n = 0
    for place in places:
        if place not in PLAN:
            continue
        conds = PLAN[place][1]
        if all("%s|%s|%s" % (place, c, e) in done for c in conds for e in EVENTS):
            continue
        l = wait_load(5.0, 900)
        log("Last", l)
        goto_place(place)
        for ci, ck in enumerate(conds):
            set_cond(ck)
            time.sleep(15)                      # exposure / MoveEye settle
            for ei, ev in enumerate(EVENTS):
                run_case(place, ck, ev, n, done)
                n += 1
            if ck in ("tag", "nacht"):
                blind(place, ck, done)
        os.system("cd /tmp/claude-0/erk2 && python3 sync.py >> out/sync.log 2>&1")
    if "schlafzimmer" in places:
        zimmer(done)
        os.system("cd /tmp/claude-0/erk2 && python3 sync.py >> out/sync.log 2>&1")
    log("fertig")
