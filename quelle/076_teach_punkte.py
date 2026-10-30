#@ MoveEye – Teil 076: Teach-in: Positionen mit dem Joystick anfahren und mit Namen speichern («Zelt», «Eingang» …) – die Wegpunkte der Patrouille, erweitert um Name und «in der Runde». Genau anfahren, umbenennen, löschen, ordnen, als Park- / Grundstellung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.35 (Wunsch Daniel): no new list - the taught points ARE the waypoints (WAYPOINTS, part 020, saved with the
#   settings). An entry is [pan %, tilt %] (as before, also «📍＋ Wegpunkt», Platz einrichten 317, Aufstell-Planer) or
#   [pan %, tilt %, "name"] or [pan %, tilt %, "name", 0] (0 = not in the round). Everything that reads w[0] / w[1] works
#   unchanged (patrol, smart round 162, simulator twin 290, the stick drawing on the web page and in the window).
#   Teach = the REAL position of the head (servo_pos, 072) - drive there with the joystick, then «save as …».
#   Go = servo_goto (072): the planner lands exactly on the stored value (as exact as the PWM: 4096 steps).
#   Coordinator (162): «Parking position» and «Home position» may be a taught point (kopf_park_point / kopf_home_point).
#   «Platz einrichten» (317): its directions can be taken over as named points (teach_from_place).
# ----------------------------------------------------------------------------
for _k, _v in {"kopf_park_point": "", "kopf_home_point": ""}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TEACH_MAX = 50


def wp_name(w):
    return str(w[2]) if isinstance(w, (list, tuple)) and len(w) >= 3 and w[2] else ""


def wp_patrol(w):
    """is this point part of the round (patrol)?"""
    return not (isinstance(w, (list, tuple)) and len(w) >= 4 and not w[3])


def _wp_make(pan, tilt, name="", patrol=True):
    pan = round(max(0.0, min(100.0, float(pan))), 2); tilt = round(max(0.0, min(100.0, float(tilt))), 2)
    name = re.sub(r"[\x00-\x1f<>\"]", "", str(name or "")).strip()[:30]
    if not name and patrol:
        return [pan, tilt]
    return [pan, tilt, name] if patrol else [pan, tilt, name, 0]


def wp_clean(w):
    """an entry of a settings file -> a valid entry or None (040 loads them with this)"""
    if isinstance(w, (int, float)) and not isinstance(w, bool):
        return None
    if not isinstance(w, (list, tuple)) or not 2 <= len(w) <= 4:
        return None
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x)) for x in w[:2]):
        return None
    name = w[2] if len(w) >= 3 and isinstance(w[2], str) else ""
    return _wp_make(w[0], w[1], name, not (len(w) >= 4 and not w[3]))


def teach_list(lang=None):
    hp, ht = servo_half("pan"), servo_half("tilt")
    out = []
    for i, w in enumerate(WAYPOINTS):
        out.append({"i": i, "name": wp_name(w), "pan": float(w[0]), "tilt": float(w[1]), "patrol": wp_patrol(w),
                    "deg": [round((float(w[0]) - 50) / 50 * hp, 1), round((float(w[1]) - 50) / 50 * ht, 1)],
                    "park": bool(wp_name(w)) and wp_name(w) == CFG.get("kopf_park_point"),
                    "home": bool(wp_name(w)) and wp_name(w) == CFG.get("kopf_home_point")})
    return out


def teach_point_by_name(name):
    if not name:
        return None
    for w in WAYPOINTS:
        if wp_name(w) == name:
            return float(w[0]), float(w[1])
    return None


def _teach_i(i):
    try:
        i = int(i)
    except (TypeError, ValueError):
        return None
    return i if 0 <= i < len(WAYPOINTS) else None


def _teach_unique(name, skip=None):
    base = name; n = 2
    while any(wp_name(w) == name for j, w in enumerate(WAYPOINTS) if j != skip):
        name = f"{base} {n}"; n += 1
    return name


def teach_add(name="", who="web", pan=None, tilt=None, patrol=True):
    """save the position where the head stands now (or pan / tilt) under a name"""
    if len(WAYPOINTS) >= TEACH_MAX:
        return False, "at most 50 points", None
    if pan is None or tilt is None:
        pan, tilt = servo_pos()
    w = _wp_make(pan, tilt, name, patrol)
    if len(w) >= 3 and w[2]:
        w[2] = _teach_unique(w[2])
    WAYPOINTS.append(w)
    save_settings()
    log_event("patrol", f"Point taught ({who}): «{wp_name(w) or len(WAYPOINTS)}» pan {w[0]:.1f} % / tilt {w[1]:.1f} %")
    return True, "", len(WAYPOINTS) - 1


def teach_edit(op, i, value=None, who="web"):
    """op: rename | delete | up | down | patrol | update (store the position of now) | park | home"""
    i = _teach_i(i)
    if i is None:
        return False, "no such point"
    w = list(WAYPOINTS[i])
    if op == "rename":
        nm = re.sub(r"[\x00-\x1f<>\"]", "", str(value or "")).strip()[:30]
        old = wp_name(w)
        nm = _teach_unique(nm, i) if nm else ""
        WAYPOINTS[i] = _wp_make(w[0], w[1], nm, wp_patrol(w))
        for k in ("kopf_park_point", "kopf_home_point"):
            if old and CFG.get(k) == old:
                CFG[k] = nm
    elif op == "delete":
        nm = wp_name(w)
        WAYPOINTS.pop(i)
        for k in ("kopf_park_point", "kopf_home_point"):
            if nm and CFG.get(k) == nm:
                CFG[k] = ""
    elif op in ("up", "down"):
        j = i - 1 if op == "up" else i + 1
        if not 0 <= j < len(WAYPOINTS):
            return False, "already at the end"
        WAYPOINTS[i], WAYPOINTS[j] = WAYPOINTS[j], WAYPOINTS[i]
    elif op == "patrol":
        WAYPOINTS[i] = _wp_make(w[0], w[1], wp_name(w) or (tr("Point") + f" {i + 1}" if not value else ""), bool(value))
    elif op == "update":
        p, t = servo_pos()
        WAYPOINTS[i] = _wp_make(p, t, wp_name(w), wp_patrol(w))
    elif op in ("park", "home"):
        k = "kopf_park_point" if op == "park" else "kopf_home_point"
        nm = wp_name(w)
        if not nm:
            nm = _teach_unique(tr("Parking position") if op == "park" else tr("Home position"))
            WAYPOINTS[i] = _wp_make(w[0], w[1], nm, wp_patrol(w))
        CFG[k] = "" if CFG.get(k) == nm and value is not True else nm
    else:
        return False, "unknown"
    save_settings()
    log_event("patrol", f"Taught point {op} ({who}): «{wp_name(w) or i + 1}»")
    return True, ""


def teach_goto(i, who="web", wait=False):
    """drive exactly to a taught point (the planner, 072). A manual command: pauses the automatic moves like the joystick."""
    i = _teach_i(i)
    if i is None:
        return False, "no such point"
    if servo_blocked():
        return False, servo_blocked_text() or "stopped"
    w = WAYPOINTS[i]
    MANUAL["until"] = time.time() + max(10.0, float(CFG.get("manual_hold") or 10))
    servo_driver_note(who, "goto")
    ok = servo_goto(float(w[0]), float(w[1]), "teach", wait=wait)
    log_event("servo", f"To the taught point «{wp_name(w) or i + 1}» (pan {float(w[0]):.1f} % / tilt {float(w[1]):.1f} %)")
    return ok, "" if ok else "interrupted"


def teach_from_place(who="web"):
    """the directions of «Platz einrichten» (tent, access, valuables) as named points - those not there yet"""
    try:
        items = kopf_items()
    except Exception:
        items = []
    n = 0
    for it in items:
        if it["kind"] == "ignore" or len(WAYPOINTS) >= TEACH_MAX:
            continue
        nm = str(it.get("name") or "")[:30]
        if any(wp_name(w) == nm for w in WAYPOINTS):
            continue
        p, t = round(float(it["pan"]), 1), round(float(it["tilt"]), 1)
        same = next((j for j, w in enumerate(WAYPOINTS) if abs(float(w[0]) - p) < 0.15 and abs(float(w[1]) - t) < 0.15), None)
        if same is not None:                               # the place already put this point (unnamed): give it the name
            if not wp_name(WAYPOINTS[same]):
                WAYPOINTS[same] = _wp_make(p, t, nm, wp_patrol(WAYPOINTS[same])); n += 1
            continue
        WAYPOINTS.append(_wp_make(p, t, nm, it["kind"] in ("tent", "access", "public_path"))); n += 1
    if n:
        save_settings()
        log_event("patrol", f"{n} points taken over from «Platz einrichten» ({who})")
    return n


def teach_choice_pairs():
    return [("", "– " + tr("none") + " –")] + [(wp_name(w), wp_name(w)) for w in WAYPOINTS if wp_name(w)]


def teach_selftest():
    keep = [list(w) for w in WAYPOINTS]; kc = {k: CFG.get(k) for k in ("kopf_park_point", "kopf_home_point")}
    sv = save_settings
    try:
        globals()["save_settings"] = lambda *a, **k: None
        WAYPOINTS[:] = [[10.0, 50.0]]
        assert wp_clean([1, 2, "x", 0]) == [1.0, 2.0, "x", 0] and wp_clean([1, 2]) == [1.0, 2.0] and wp_clean([1, "a"]) is None
        ok, _e, i = teach_add("Zelt", "test", 30.0, 40.0)
        ok2, _e, j = teach_add("Zelt", "test", 70.0, 45.0, patrol=False)
        assert ok and ok2 and wp_name(WAYPOINTS[j]) == "Zelt 2" and not wp_patrol(WAYPOINTS[j]) and teach_point_by_name("Zelt") == (30.0, 40.0)
        teach_edit("rename", j, "Eingang"); teach_edit("up", j); teach_edit("park", 1)
        assert wp_name(WAYPOINTS[1]) == "Eingang" and CFG["kopf_park_point"] == "Eingang"
        teach_edit("delete", 1)
        assert CFG["kopf_park_point"] == "" and len(WAYPOINTS) == 2
        assert [w[0] for w in WAYPOINTS if wp_patrol(w)] == [10.0, 30.0]
        assert [s[3] for s in kopf_stops() if s[3]] in (["Zelt"], [])
    finally:
        globals()["save_settings"] = sv
        WAYPOINTS[:] = keep; CFG.update(kc)
    return "taught points: add, unique names, rename, order, park, delete, in the round"
