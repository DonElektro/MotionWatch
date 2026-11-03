"""Erkennungstest – die Fälle (aus den Erkennungstests 2–5 übernommen und bereinigt).
Nur die Steuer-API des Simulators (/control) und die Web-API von MoveEye (/api/state, /api/messages, /api/frame.jpg, /api/set);
am Simulator und an MoveEye wird nichts geändert. Gestartet wird über erkennungstest.py (setzt konfig()).

Ein Fall: Ort (Welt des Simulators) | Bedingung (Tageszeit, Wetter, Infrarot) | Ereignis (leer, gehen, kriechen, kind, tier,
fahrzeug). Ergebnis pro Fall eine Zeile in results.jsonl (fortsetzbar: Fälle, die schon drinstehen, werden übersprungen).
"""
import json
import math
import os
import threading
import time
import urllib.request

K = {"sim": "http://127.0.0.1:8796", "mw": "http://127.0.0.1:5096", "out": ".", "shots": "./bilder", "variant": "x",
     "fpsmin": 2.4, "fpswait": 180.0, "loadmax": 99.0}


def konfig(**kw):
    K.update(kw)
    os.makedirs(K["out"], exist_ok=True)
    os.makedirs(K["shots"], exist_ok=True)


def res_path():
    return os.path.join(K["out"], "results.jsonl")


# ------------------------------------------------------------------ Hilfen
def http_json(url, data=None, timeout=8):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def ctl(**d):
    return http_json(K["sim"] + "/control", d, timeout=20)


def mw_state():
    return http_json(K["mw"] + "/api/state", timeout=6).get("state", {})


def mw_messages():
    try:
        return http_json(K["mw"] + "/api/messages?src=local", timeout=6)
    except Exception as e:
        return {"err": str(e)}


def mw_set(key, value):
    try:
        return http_json(K["mw"] + "/api/set", {"key": key, "value": value}, timeout=8)
    except Exception as e:
        return {"err": str(e)}


def frame(name):
    try:
        with urllib.request.urlopen(K["mw"] + "/api/frame.jpg", timeout=6) as r:
            b = r.read()
        with open(os.path.join(K["shots"], name), "wb") as f:
            f.write(b)
        return True
    except Exception:
        return False


def load():
    try:
        return float(open("/proc/loadavg").read().split()[0])
    except Exception:
        return 0.0


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(os.path.join(K["out"], "ablauf.log"), "a") as f:
        f.write(s + "\n")


def mw_fps(n=4):
    """MoveEye-Bilder/s, Mittel über n Abfragen"""
    v = []
    for _ in range(n):
        try:
            v.append(float(mw_state().get("fps") or 0))
        except Exception:
            v.append(0.0)
        time.sleep(0.5)
    return sum(v) / len(v)


def wait_ok():
    """vor einem Fall: warten, bis MoveEye mindestens fpsmin Bilder/s hat (und die Last unter loadmax ist), höchstens fpswait s.
    Danach geht es trotzdem weiter – die Bilder/s stehen in jedem Fall im Ergebnis."""
    t0 = time.time()
    while time.time() - t0 < K["fpswait"]:
        if load() < K["loadmax"] and (K["fpsmin"] <= 0 or mw_fps() >= K["fpsmin"]):
            break
        time.sleep(10)
    return round(time.time() - t0)


ANIMAL_LABELS = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "teddy bear", "animal"}
VEH_LABELS = {"car", "truck", "bus", "motorcycle", "bicycle", "train", "boat", "airplane"}
SPAN = 48.0          # Grad zur Seite, wo ein Besucher (nicht Person) beginnt / endet (Kopfkamera ±33°)

# Bedingung: Name, Stunde, Wetter, Infrarot, Abstände (gehen, kriechen, Kind)
COND = {
    "tag":        ("Tag, klar", 12.0, "clear", False, (10.0, 7.0, 8.0)),
    "daemmerung": ("Dämmerung, klar", 17.5, "clear", False, (9.0, 6.0, 7.0)),
    "nacht":      ("Nacht, klar, Infrarot", 23.0, "clear", True, (7.0, 5.0, 6.0)),
    "regen":      ("Tag, Regen", 14.0, "rain", False, (10.0, 7.0, 8.0)),
    "nebel":      ("Tag, Nebel", 9.5, "fog", False, (10.0, 7.0, 8.0)),
    "schnee":     ("Tag, Schnee", 15.0, "snow", False, (10.0, 7.0, 8.0)),
    "nachtregen": ("Nacht, Regen, Infrarot", 23.5, "rain", True, (7.0, 5.0, 6.0)),
    "dunkel":     ("Nacht ohne Licht (nur Wärmebild)", 23.0, "clear", False, (7.0, 5.0, 6.0)),
}
ANIMALS = [("deer", 12.0), ("fox", 8.0), ("cat", 6.0), ("dog", 8.0), ("crows", 8.0), ("boar", 10.0), ("hedgehog", 4.0),
           ("magpies", 7.0), ("hare", 8.0), ("badger", 6.0)]
# Ort -> (Welt, Bedingungen)
PLAN = {
    "camping":    ("camping", ["tag", "daemmerung", "nacht", "regen"]),
    "wald":       ("bergtal", ["tag", "daemmerung", "nacht", "nebel"]),
    "stellplatz": ("ferienpark", ["tag", "daemmerung", "nacht", "schnee"]),
    "garten":     ("daheim", ["tag", "nacht", "nachtregen"]),
    "festival":   ("festival", ["tag", "nacht"]),
    "wild":       ("bergtal", ["tag", "nacht"]),
    "parkplatz":  ("ferienpark", ["tag", "daemmerung", "nacht", "nebel"]),
    "baustelle":  ("daheim", ["tag", "nacht"]),
    "schlafzimmer": ("daheim", []),
}
EVENTS = ["leer", "gehen", "kriechen", "kind", "tier", "fahrzeug"]
PERSON_EVENTS = ("gehen", "kriechen", "kind")
ST = {"ani_i": 0, "cur_key": "", "fall": ""}   # fall: woran gerade gerechnet wird (erkennungstest.py: Absturz -> welcher Fall)
UEBERSPRUNGEN = "uebersprungen.jsonl"          # Fälle, bei denen der Simulator / MoveEye immer wieder abstürzt (gelten als erledigt)


def done_keys():
    k = set()
    for pfad in (res_path(), os.path.join(K["out"], UEBERSPRUNGEN)):
        if os.path.exists(pfad):
            for ln in open(pfad):
                try:
                    k.add(json.loads(ln)["key"])
                except Exception:
                    pass
    return k


def ueberspringen(key, grund):
    """den Fall (oder «ort|…» bzw. «ort|bedingung|*») nicht mehr rechnen - steht im Bericht"""
    with open(os.path.join(K["out"], UEBERSPRUNGEN), "a") as f:
        f.write(json.dumps({"key": key, "grund": grund, "t": time.strftime("%H:%M:%S")}, ensure_ascii=False) + "\n")


def uebersprungene(ordner=None):
    out = []
    p = os.path.join(ordner or K["out"], UEBERSPRUNGEN)
    if os.path.exists(p):
        for ln in open(p):
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def save(rec):
    rec.setdefault("variant", K["variant"])
    with open(res_path(), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def pan_deg():
    try:
        return float(ctl(action="servo")["info"]["pan"]["head"])
    except Exception:
        return 0.0


def in_view(dist, off):
    """Bodenpunkt dist m vor MoveEye (bei 0/0, schaut nach -z) in Richtung des Kopfes + off Grad (+ = rechts)"""
    a = math.radians(-pan_deg() + off)
    return [round(math.sin(a) * dist, 2), round(-math.cos(a) * dist, 2)]


def cross(dist):
    r = dist / math.cos(math.radians(SPAN))
    s = 1 if (sum(map(ord, ST["cur_key"])) % 2) else -1      # feste Richtung je Fall (gleich in allen Läufen)
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
    """was MoveEye meldet, wenn niemand da ist (feste Fehl-Personen, Gegenstände der Szene)"""
    labs, boxes = set(), []
    t_end = time.time() + secs
    while time.time() < t_end:
        try:
            s = mw_state()
            labs |= set(s.get("present") or [])
            if int(s.get("persons") or 0) > 0:
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
    """MoveEye abfragen; want = person | animal | vehicle | none. base = (Labels, Personen-Rahmen) ohne Besucher."""
    base_labs, base_boxes = base
    seen = {}
    first_person = None
    person_eps = 0
    prev_p = 0
    warm = None
    fps = []
    extra = {}
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
        p = len(new_boxes(s, base_boxes))
        fps.append(float(s.get("fps") or 0))
        for lab in s.get("present") or []:
            if lab not in base_labs:
                seen.setdefault(lab, t)
        if p > 0 and prev_p == 0:
            person_eps += 1
        if p > 0 and first_person is None:
            first_person = t
            fn = "%s_erkannt.jpg" % tag
            if frame(fn):
                shot_first = fn
        for _k in ("crawl", "person_maybe"):
            try:
                if int(s.get(_k) or 0) > 0:
                    extra.setdefault(_k + "_s", t)
                    extra[_k + "_max"] = max(extra.get(_k + "_max", 0), int(s.get(_k) or 0))
            except Exception:
                pass
        if s.get("fog"):
            extra.setdefault("fog_s", t)
        try:
            _st = s.get("strict") or {}
            if int(_st.get("n") or 1) > 1:
                extra.setdefault("strict_s", t)
                extra["strict_why"] = _st.get("why", "")
                extra["strict_n"] = max(extra.get("strict_n", 0), int(_st.get("n")))
        except Exception:
            pass
        if int(s.get("warm") or 0) > 0 and warm is None:
            warm = t
        if not shot_mid and t >= secs * 0.45:
            fn = "%s_mitte.jpg" % tag
            if frame(fn):
                shot_mid = fn
        prev_p = p
        time.sleep(0.5)
    new = [m for i, m in msg_ids().items() if i not in msgs0]
    labs = sorted(seen)
    animal_l = sorted(set(labs) & ANIMAL_LABELS)
    veh_l = sorted(set(labs) & (VEH_LABELS - {"bicycle"}))
    motion = "motion" in seen or "prealarm" in seen
    rec = {"seen": {k: seen[k] for k in labs}, "base_labels": sorted(base_labs), "static_person_boxes": len(base_boxes) > 0,
           "first_person_s": first_person, "person_eps": person_eps, "warm_s": warm,
           "pushes": [[m.get("ev"), round(float(m.get("t", 0)) - t_spawn, 1), (m.get("text") or "")[:80]] for m in new],
           "fps": round(sum(fps) / len(fps), 1) if fps else 0, "shot_first": shot_first, "shot_mid": shot_mid, "extra": extra}
    if want == "person":
        rec["detected"] = first_person is not None
        rec["t_detect"] = first_person
        rec["as"] = "Person" if first_person is not None else (
            ", ".join(animal_l + veh_l) or ("Wärme" if warm is not None else ("nur Bewegung" if motion else "–")))
    elif want in ("animal", "vehicle"):
        lab = animal_l if want == "animal" else veh_l
        ts = [seen[x] for x in lab]
        rec["detected"] = bool(ts)
        rec["t_detect"] = min(ts) if ts else None
        rec["as"] = ", ".join(lab) if lab else ("Person" if first_person is not None else ("nur Bewegung" if motion else "–"))
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
    for _c in ("cond_glare", "cond_web"):
        try:
            ctl(action="set", id=_c, value=False)
        except Exception:
            pass


def clear():
    try:
        ctl(action="press", id="clear")
    except Exception:
        pass


def run_case(place, ck, ev, done, rep=1, leerwind=55):
    """Personenfälle rep-mal (der Simulator wählt die Richtung der Probe zufällig) – Schlüssel …#2, #3"""
    for r in range(rep if ev in PERSON_EVENTS else 1):
        _run_case(place, ck, ev, done, "" if r == 0 else "#%d" % (r + 1), leerwind)


def _run_case(place, ck, ev, done, sfx="", leerwind=55):
    key = "%s|%s|%s" % (place, ck, ev) + sfx
    if key in done:
        return
    world = PLAN[place][0]
    name, hour, weather, ir, (dw, dc, dk) = COND[ck]
    ST["cur_key"] = key.split("#")[0]
    ST["fall"] = key
    waited = wait_ok()
    if waited > 15:
        log("  gewartet %d s (Bilder/s %.1f, Last %.1f)" % (waited, mw_fps(), load()))
    tag = "%s_%s_%s%s" % (place, ck, ev, sfx.replace("#", "_"))
    clear()
    time.sleep(2)
    base = baseline(3.0)
    if base[1]:
        frame("%s_%s_statisch.jpg" % (place, ck))
    want, secs, info, ev_kind = "person", 18.0, "", ""
    r = {"ok": True}
    if ev == "gehen":
        r = ctl(action="menschen", do="probe", gait="walk", dist=dw)
        info = "geht quer, %.0f m" % dw
    elif ev == "kriechen":
        r = ctl(action="menschen", do="probe", gait="crawl", dist=dc, dark=True)
        info = "kriecht, dunkle Kleidung, %.0f m" % dc
        secs = 22.0
    elif ev == "kind":
        a, b = cross(dk)
        r = ctl(action="spawn_at", kind="child", **{"from": a, "to": b})
        info = "Kind, %.0f m" % dk
    elif ev == "tier":
        ev_kind, d = ANIMALS[ST["ani_i"] % len(ANIMALS)]
        ST["ani_i"] += 1
        if ck in ("nacht", "nachtregen", "dunkel"):
            d = min(d, 7.0)
        a, b = cross(d)
        r = ctl(action="spawn_at", kind=ev_kind, **{"from": a, "to": b})
        want, info = "animal", "%s, %.0f m" % (ev_kind, d)
    elif ev == "fahrzeug":
        if ir:
            ctl(action="set", id="cond_headlights", value=True)
        a, b = cross(20.0)
        r = ctl(action="spawn_at", kind="car", **{"from": a, "to": b})
        want, secs, info = "vehicle", 14.0, "Auto, 20 m" + (" + Scheinwerfer" if ir else "")
    elif ev == "leer":
        # Böen ab 39 km/h machen MoveEye 10 Min. strenger (Wind-Regel): die neuen Orte ohne Sturm (leerwind 12)
        ctl(action="set", id="wind", value=leerwind)
        want, secs, info = "none", 45.0, "nichts, Wind %d km/h%s" % (leerwind, " (Äste)" if leerwind >= 39 else "")
    t_spawn = time.time()
    load_at_start = load()
    rec = observe(secs, tag, want, t_spawn, base)
    rec.update({"key": key, "place": place, "world": world, "cond": ck, "cond_name": name, "event": ev, "info": info,
                "spawn_ok": bool(r.get("ok", False)), "secs": secs, "t": time.strftime("%H:%M:%S"), "load": load(),
                "load_start": round(load_at_start, 2), "waited": waited})
    if ev == "tier":
        rec["animal"] = ev_kind
    ctl(action="set", id="wind", value=12)
    ctl(action="set", id="cond_headlights", value=False)
    save(rec)
    log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("t_detect", ""),
        "fps", rec["fps"], "pushes", len(rec["pushes"]))


def blind(place, ck, done):
    """blinde Flecken: Gitter aus Richtungen und Abständen (blindmap des Simulators)"""
    key = "%s|%s|blindmap" % (place, ck)
    if key in done:
        return
    ST["fall"] = key
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
           "static_person_boxes": len(base[1]) > 0, "result": res, "start": r, "secs": round(time.time() - t0),
           "t": time.strftime("%H:%M:%S")}
    set_cond(ck)
    save(rec)
    log(key, "->", res.get("found"), "/", res.get("inview"), "im Bild, von", res.get("n"), "max", res.get("max_found"))


def goto_place(place):
    world = PLAN[place][0]
    ST["fall"] = "ort|" + place
    t0 = time.time()
    r = ctl(action="scenario", id=place)
    for _ in range(90):
        time.sleep(2)
        try:
            st = ctl(action="get")["status"]
            s = mw_state()
            if "verbunden" in st and "nicht verbunden" not in st and float(s.get("fps") or 0) > 0.5:
                break
        except Exception:
            pass
    ctl(action="set", id="auto", value=False)
    ctl(action="set", id="season", value="today")
    clear()
    log("Ort", place, "Welt", world, "geladen in %.0f s" % (time.time() - t0), r.get("ok", r))


def zimmer(done):
    """Schlafzimmer (Welt Zuhause): Hamster im Laufrad (Nacht), Spinne vor der Linse (Nacht, Infrarot), Wellensittich (Tag),
    Leerlauf"""
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
        rec.update({"key": key, "place": place, "world": "daheim", "cond": ck, "cond_name": COND[ck][0],
                    "event": "tier" if f else "leer", "animal": ev if f else "", "info": ev, "spawn_ok": bool(r.get("ok", False)),
                    "secs": 40.0 if f else 45.0, "t": time.strftime("%H:%M:%S"), "load": load()})
        save(rec)
        log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("false_person", ""))
        try:
            ctl(action="zimmertiere", do="state", who="hamster", hold=False)
        except Exception:
            pass


def orte(spec, done, rep=1, leerwind=55, sel=None, sel_leer=False, blindmap=False):
    """spec «camping,wald» oder «camping:tag+nacht» (nur diese Bedingungen); sel = nur diese Schlüssel (Ort|Bedingung|Ereignis),
    sel_leer = dazu immer den Leerlauf"""
    places, only = [], {}
    for p in [x for x in spec.split(",") if x]:
        if ":" in p:
            a, b = p.split(":", 1)
            only[a] = b.split("+")
            p = a
        places.append(p)
    for place in places:
        if place == "schlafzimmer":
            zimmer(done)
            continue
        if place not in PLAN:
            log("unbekannter Ort", place)
            continue
        conds = only.get(place, PLAN[place][1])

        def wanted(c, e):
            k = "%s|%s|%s" % (place, c, e)
            return sel is None or k in sel or (e == "leer" and sel_leer)
        conds = [c for c in conds if any(wanted(c, e) for e in EVENTS)]
        todo = ["%s|%s|%s" % (place, c, e) + ("" if r == 0 else "#%d" % (r + 1))
                for c in conds for e in EVENTS if wanted(c, e) for r in range(rep if e in PERSON_EVENTS else 1)]
        if all(k in done for k in todo):          # schon gemessen (Fortsetzen) oder nichts zu tun
            continue
        if "ort|" + place in done:                # Ort lädt nicht (Simulator stürzt dort immer ab): übersprungen
            log("Ort", place, "übersprungen (stürzt beim Laden ab)")
            continue
        wait_ok()
        goto_place(place)
        for ck in conds:
            if "%s|%s|*" % (place, ck) in done:    # Bedingung lässt sich nicht setzen (Absturz): übersprungen
                log("Bedingung", place, ck, "übersprungen (stürzt beim Setzen ab)")
                continue
            ST["fall"] = "%s|%s|*" % (place, ck)
            set_cond(ck)
            time.sleep(15)                      # Belichtung / MoveEye eingewöhnen
            for ev in EVENTS:
                if wanted(ck, ev):
                    run_case(place, ck, ev, done, rep, leerwind)
            if blindmap and ck in ("tag", "nacht"):
                blind(place, ck, done)


# ------------------------------------------------------------------ Sonderfälle (früher extra.py / diag4.py)
NAMES = {"nacht_blend": "Nacht, Scheinwerfer direkt in die Kamera", "tag_blend": "Tag, Sonne blendet in die Linse",
         "linse": "Tag, Wind 55 km/h, etwas direkt vor der Linse", "tag_ruhig": "Tag, klar, ohne Sturm in den 10 Min. davor",
         "kopf": "Tag, klar, Kopf-Verfolgung AN", "nachtregen": "Nacht, Regen, Infrarot", "nacht": "Nacht, klar, Infrarot",
         "daemmerung": "Dämmerung, klar", "tag": "Tag, klar"}


def case(place, ck, ev, want, secs, act, info, done, wind=12, before=None):
    key = "%s|%s|%s" % (place, ck, ev)
    if key in done:
        return
    ST["fall"] = key
    wait_ok()
    clear()
    time.sleep(2)
    if before:
        before()
    ctl(action="set", id="wind", value=wind)
    base = baseline(3.0)
    r = act() if act else {"ok": True}
    t_spawn = time.time()
    rec = observe(secs, "%s_%s_%s" % (place, ck, ev), want, t_spawn, base)
    rec.update({"key": key, "place": place, "world": PLAN[place][0], "cond": ck, "cond_name": NAMES.get(ck, ck), "event": ev,
                "info": info, "spawn_ok": bool((r or {}).get("ok", False)), "secs": secs, "t": time.strftime("%H:%M:%S"),
                "load": load(), "sonderfall": True})
    ctl(action="set", id="wind", value=12)
    save(rec)
    log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("t_detect", ""), "fps", rec["fps"],
        "pushes", len(rec["pushes"]))


def _later(dt, f):
    t = threading.Timer(dt, f)
    t.daemon = True
    t.start()


def toward():
    return ctl(action="fahrzeuge", do="toward")


def walk(dist):
    return lambda: ctl(action="menschen", do="probe", gait="walk", dist=dist)


def blend(done):
    """Stellplatz Nacht: Auto mit Scheinwerfern direkt auf die Kamera zu (leer, mit Person); Tag: Sonne blendet"""
    goto_place("stellplatz")
    set_cond("nacht")
    time.sleep(15)

    def leer_toward():
        r = toward()
        _later(22.0, toward)
        return r
    case("stellplatz", "nacht_blend", "leer", "none", 45.0, leer_toward, "2 Autos mit Scheinwerfern direkt auf die Kamera zu, niemand da", done)

    def walk_toward():
        toward()
        time.sleep(3)
        return ctl(action="menschen", do="probe", gait="walk", dist=7.0)
    case("stellplatz", "nacht_blend", "gehen", "person", 22.0, walk_toward, "Auto blendet, dabei geht eine Person quer, 7 m", done)
    set_cond("tag")
    ctl(action="set", id="cond_glare", value=True)
    time.sleep(15)
    case("stellplatz", "tag_blend", "leer", "none", 45.0, None, "Sonne blendet (cond_glare), niemand da", done,
         before=lambda: ctl(action="set", id="cond_glare", value=True))
    case("stellplatz", "tag_blend", "gehen", "person", 18.0, walk(10.0), "Sonne blendet, Person geht quer, 10 m", done,
         before=lambda: ctl(action="set", id="cond_glare", value=True))
    ctl(action="set", id="cond_glare", value=False)


def linse(done):
    """Camping Tag, Wind 55: Spinnennetz vor der Linse, Vogel fliegt vor der Linse durch"""
    goto_place("camping")
    set_cond("tag")
    time.sleep(15)
    case("camping", "linse", "netz", "none", 45.0, None, "Spinnennetz vor der Linse (cond_web), Wind 55 km/h, niemand da", done,
         wind=55, before=lambda: ctl(action="set", id="cond_web", value=True))
    case("camping", "linse", "netz_gehen", "person", 18.0, walk(10.0), "Spinnennetz vor der Linse, Person geht quer, 10 m", done,
         before=lambda: ctl(action="set", id="cond_web", value=True))
    ctl(action="set", id="cond_web", value=False)

    def birds():
        r = ctl(action="press", id="bird_now")
        for dt in (12.0, 24.0, 36.0):
            _later(dt, lambda: ctl(action="press", id="bird_now"))
        return r
    case("camping", "linse", "vogel", "none", 45.0, birds, "Vogel fliegt 4× direkt vor der Linse durch, niemand da", done)


def _observe_pan(secs, tag, want, base):
    pans, res = [], {}
    t0 = time.time()
    th = threading.Thread(target=lambda: res.update(observe(secs, tag, want, t0, base)))
    th.start()
    while th.is_alive():
        pans.append([round(time.time() - t0, 1), round(pan_deg(), 1)])
        time.sleep(2)
    return dict(res), pans


def kopf(done):
    """Camping Tag, Kopf-Verfolgung AN: Schwenk 150 s im leeren Bild, dann geht eine Person"""
    goto_place("camping")
    set_cond("tag")
    a, b = mw_set("track_person", True), mw_set("kopf_on", True)
    log("Kopf-Verfolgung an:", a, b)
    time.sleep(5)
    try:
        key = "camping|kopf|leer"
        if key not in done:
            wait_ok()
            base = baseline(3.0)
            rec, pans = _observe_pan(150.0, "camping_kopf_leer", "none", base)
            st = mw_state()
            rec.update({"key": key, "place": "camping", "world": "camping", "cond": "kopf", "cond_name": NAMES["kopf"], "event": "leer",
                        "info": "Kopf-Verfolgung AN, niemand da, 150 s", "pan": pans, "kopf": st.get("kopf"),
                        "track_what": st.get("track_what"), "secs": 150.0, "t": time.strftime("%H:%M:%S"), "load": load(),
                        "sonderfall": True})
            frame("camping_kopf_leer_ende.jpg")
            save(rec)
            log(key, "-> Schwenk", pans[0][1] if pans else "?", "->", pans[-1][1] if pans else "?", "Personen",
                rec.get("false_person_eps"), "Pushes", rec.get("false_pushes"))
        key = "camping|kopf|gehen"
        if key not in done:
            clear()
            time.sleep(2)
            base = baseline(3.0)
            r = ctl(action="menschen", do="probe", gait="walk", dist=10.0)
            rec, pans = _observe_pan(25.0, "camping_kopf_gehen", "person", base)
            rec.update({"key": key, "place": "camping", "world": "camping", "cond": "kopf", "cond_name": NAMES["kopf"], "event": "gehen",
                        "info": "Kopf-Verfolgung AN, Person geht quer, 10 m", "pan": pans, "spawn_ok": bool(r.get("ok")), "secs": 25.0,
                        "t": time.strftime("%H:%M:%S"), "load": load(), "sonderfall": True})
            save(rec)
            log(key, "->", rec.get("detected"), rec.get("t_detect"))
    finally:
        log("Kopf-Verfolgung aus:", mw_set("track_person", False), mw_set("kopf_on", False))


def ruhig(done):
    """Gegenprobe: wie camping|tag, aber vorher ruhig (keine Böe über 39 km/h in den 10 Min. davor)"""
    goto_place("camping")
    set_cond("tag")
    ctl(action="set", id="wind", value=12)
    t0 = time.time()
    while time.time() - t0 < 700:
        try:
            st = mw_state()
            if float((st.get("storm") or {}).get("gust") or 0) < 39 and int((st.get("strict") or {}).get("n") or 1) == 1:
                break
        except Exception:
            pass
        time.sleep(10)
    log("ruhig nach %.0f s" % (time.time() - t0))
    case("camping", "tag_ruhig", "gehen", "person", 18.0, walk(10.0), "wie camping|tag|gehen, aber ohne Sturm davor", done)
    case("camping", "tag_ruhig", "kriechen", "person", 22.0, lambda: ctl(action="menschen", do="probe", gait="crawl", dist=7.0, dark=True),
         "wie camping|tag|kriechen, aber ohne Sturm davor", done)
    case("camping", "tag_ruhig", "kind", "person", 18.0,
         lambda: ctl(action="spawn_at", kind="child", **dict(zip(("from", "to"), cross(8.0)))), "wie camping|tag|kind, aber ohne Sturm davor", done)
    case("camping", "tag_ruhig", "fahrzeug", "vehicle", 14.0,
         lambda: ctl(action="spawn_at", kind="car", **dict(zip(("from", "to"), cross(20.0)))), "wie camping|tag|fahrzeug, aber ohne Sturm davor", done)


def nebenfunde(done):
    """Scheinwerfer und Wind im leeren Bild (früher diag4.py)"""
    def car_lights():
        ctl(action="set", id="cond_headlights", value=True)
        return ctl(action="spawn_at", kind="car", **dict(zip(("from", "to"), cross(20.0))))

    def toward2():
        r = toward()
        _later(22.0, toward)
        return r
    for place, ck, ev, want, secs, act, info, wind in (
            ("stellplatz", "nacht_blend", "leer", "none", 45.0, toward2, "2 Autos mit Scheinwerfern auf die Kamera zu, niemand da", 12),
            ("garten", "nachtregen", "fahrzeug", "vehicle", 16.0, car_lights, "Auto 20 m + Scheinwerfer", 12),
            ("wild", "nacht", "fahrzeug", "vehicle", 16.0, car_lights, "Auto 20 m + Scheinwerfer", 12),
            ("camping", "daemmerung", "leer", "none", 45.0, None, "nichts, Wind 55 km/h", 55),
            ("garten", "tag", "leer", "none", 45.0, None, "nichts, Wind 12 km/h", 12)):
        key = "%s|%s|%s" % (place, ck, ev)
        if key in done:
            continue
        ST["cur_key"] = key
        wait_ok()
        goto_place(place)
        set_cond("nacht" if ck == "nacht_blend" else ck)
        time.sleep(15)
        case(place, ck, ev, want, secs, act, info, done, wind=wind)
        ctl(action="set", id="cond_headlights", value=False)


EXTRAS = {"blend": blend, "linse": linse, "kopf": kopf, "ruhig": ruhig, "nebenfunde": nebenfunde}
