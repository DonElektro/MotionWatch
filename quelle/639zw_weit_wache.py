#@ MoveEye – Teil 639zw: «Weitwinkel = Wache, Kopf = Detektiv» – leichte KI auf dem Weitwinkelbild (nur Person, optional Tier / Fahrzeug ruft den Kopf), Auslösezonen im Weitwinkelbild (Zonen-Editor /zones?cam=weit), Wärmebild-Fusion nachts ab Werk an (ohne Wärme kein Personen-Alarm), Zähler /api/wache, Anleitung «Weitwinkel einrichten und testen». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Strategie des Besitzers (07.11.2026): die Weitwinkel-Kamera (Camera Module 3 Wide NoIR) ist die «Wache» (immer an, leichte KI),
# der Kopf der «Detektiv» (wird gerufen, verfolgt dann; das Wärmebild nimmt nachts die Fehlalarme weg).
#
# (a) Leichte KI auf dem Weitwinkelbild (weit_ki_frame, aus der Schleife der Zusatzkamera 440):
#     - nur für die Übersicht (CFG kopf_ov), nur scharf, nur wenn das Weitwinkelbild Bewegung hat (c.boxes, in einer Auslösezone);
#     - dasselbe Netz wie die Hauptkamera (SSD MobileNet COCO oder das eigene YOLO-Modell, Teil 195 - kein zweites Modell im
#       Speicher) auf einem Ausschnitt um die grösste Bewegung (Quadrat, das Netz verkleinert selbst auf 300 / 320-640 px);
#     - höchstens kopf_ov_ki_fps Läufe pro Sekunde (ab Werk 1), mindestens 3 x die letzte Laufzeit Pause, heiss / Sim-Sparen
#       doppelt so lang; die Hauptkamera hat Vorrang: ein Schloss um AIDetector.infer - die Übersicht nimmt es nur, wenn es
#       frei ist (sonst lässt sie den Lauf aus), die Hauptkamera wartet höchstens auf einen Übersichts-Lauf;
#     - aus im Akku-Sparen (BATT_SAVE), in der Demo, ohne Modell / KI aus, mit dem PC-Helfer ohne eigenes Netz: dann wie bisher
#       (Bewegung allein ruft den Kopf); im Dunkeln (is_dark oder Weitwinkelbild dunkel) ab Werk ebenfalls Bewegung allein
#       (kopf_ov_ki_dark: die KI sieht im Infrarot-Fischauge wenig - am Kopf prüft dann das Wärmebild, (c)).
#     - Klassen: Person immer; Tier (kopf_ov_ki_animal, im Wildtier-Modus immer) und Fahrzeug (kopf_ov_ki_vehicle) wahlweise.
#     _kopf_ov_tick (162) fragt weit_pick(c, now): Bewegung ausserhalb der Zonen = nur notiert, ohne passende Klasse = der Kopf
#     bleibt (notiert), mit Treffer = Richtung aus dem KI-Kasten.
#     Kosten (geschätzt, Pi 5, OpenCV-DNN, 4 Kerne): SSD 300 px ~60-90 ms, eigenes YOLO 320 px ~60-80 ms, 640 px ~200-250 ms
#     (418z). Bei 1 Lauf/s und nur bei Bewegung: SSD ~2 % der ganzen CPU (6-9 % eines Kerns), YOLO 640 ~6 % (25 % eines Kerns);
#     ohne Bewegung im Weitwinkel 0. Gemessen auf dem Entwicklungsrechner: siehe Bericht (werkzeuge-Lauf, nicht im Repository).
# (b) Auslösezonen im Weitwinkelbild (CFG kopf_ov_zones, normiert 0..1 auf das Bild der Übersicht): «trigger» = nur hier darf
#     der Weitwinkel den Kopf rufen (keine = das ganze Bild), «ignore» = hier nie. Gezählt wird der Fusspunkt (unten Mitte),
#     wie bei den Zonen der Hauptkamera (030). Zonen-Editor = die Seite /zones mit ?cam=weit (520 + Patch unten): eigenes Bild
#     (/api/weit/frame.jpg, ohne Kästen), eigene Liste (/api/weit/zones), nur die zwei Arten. Dreht die Weitwinkel-Kamera mit
#     dem Kopf (Montage head_*, cam_on_head), gelten die Zonen nicht (sie würden mitwandern) - einmal im Protokoll.
# (c) Wärmebild-Fusion (alarm_heat_fusion, ab Werk an): nachts (is_dark / lowlight) und nur wenn eine Wärmebildquelle gewählt ist
#     UND Bilder liefert (frisch < 3 s, «connected»), braucht ein Personen-Alarm Wärme am Ort der Person (Wärmebild-Ausschnitt
#     wie das Overlay, 230 crop: 95. Perzentil im Kasten deutlich über dem Median des Bilds - °C: + fusion_heat_c, 8 Bit: + max(25,
#     20 % des Rests); oder ein warmer Körper von THERMAL.detect im Kasten). Keine Wärme = kein Alarm, Protokoll «Person without
#     heat - no alarm» (DE «ohne Wärme – kein Alarm»), Zähler vetoed. Tag, kein Wärmebild, Wärmebild ohne Bild = genau wie
#     bisher (auch die doppelte Bestätigung alarm_confirm2 bleibt, wie sie ist). Bestätigt = 10 s offen (kein Flackern).
#     Damit das Wärmebild nachts läuft, will ThermalCam.wanted die Quelle auch dann (nur mit gewählter Quelle).
#     Messbar: /api/wache (Zähler seit dem Start) und die Protokollzeilen; Prüfstand 2 zählt die echten Pushes (068).
# Selbsttest: weit_wache_selftest (Klassen, Zonen, Entscheidungstabelle Tag/Nacht x Wärmebild ja/nein x Wärme ja/nein).
# ----------------------------------------------------------------------------
#
# Idee 1 des Besitzers (14.11.2026, Paket «Weitwinkel-KI»), was dazukam:
# (a) Ziele Person / Tier / Fahrzeug (Auto, Velo, Motorrad): ab Werk rufen alle drei den Kopf (kopf_ov_ki_animal / _vehicle an);
#     gespeicherte Einstellungen bleiben. Ein Treffer merkt sich seine Richtung (kopf_ov_deg zur Zeit des Treffers) und ob er
#     nach den Zonen zählt - dreht der Kopf mit der Kamera, stimmt die Richtung trotzdem.
# (b) Zonen: «Auslösezone» grün (Einschluss), «Ignorier-Zone» rot (Ausschluss), je Zone die Ziele («targets»). Ausschluss gewinnt;
#     ohne Auslösezone zählt das ganze Bild (für die Ziele der Schalter). Gespeichert pro Montage (kopf_ov_zone_sets: Montage
#     des Simulators, echt «fixed» / «head»; die alte Liste kopf_ov_zones gilt für feste Montagen ohne eigene Liste weiter).
#     Montagen auf dem Kopf: die Ecken stehen als Richtungen in Grad («ang»: Kopfstellung beim Zeichnen + Versatz + Winkel im
#     Bild, das Fischauge ist winkeltreu) - die Zone bleibt am Boden, wenn der Kopf dreht; was gerade ausserhalb des Bildes liegt,
#     zeigt der Editor nicht (die Ecken bleiben trotzdem).
# (c) Wärmebild-Bestätigung nachts mit Richtung und Zeitfenster: warme Stellen des ausgerichteten Wärmebilds (Kasten -> Richtung
#     mit der Kopfstellung zur Zeit des Wärmebilds) kommen in einen Ringspeicher (HEAT). Ein Personen-Alarm zählt, wenn eine
#     warme Stelle in fusion_window_s (ab Werk 4 s) vorher in seiner Richtung lag (± fusion_tol_deg, ab Werk 8°, senkrecht das
#     Doppelte), sonst wartet er höchstens das Zeitfenster und gilt dann als «ohne Wärme – nicht gewertet». Wärmebild gewählt,
#     aber gestört = der Alarm zählt (fail open, Protokoll). Nur Personen-Alarme gehen durch alarm_gate - Sabotage, SOS, Alarm
#     von Hand, Geräusch, Wärme-Alarm nie. Nach dem Update einmal auf allen Geräten an (heat_confirm_migrate) mit Hinweis.
# ----------------------------------------------------------------------------
for _k, _v in {"kopf_ov_ki": True, "kopf_ov_ki_animal": True, "kopf_ov_ki_vehicle": True, "kopf_ov_ki_dark": True,
               "kopf_ov_ki_fps": 1.0, "kopf_ov_zones": [], "kopf_ov_zone_sets": {}, "alarm_heat_fusion": True, "fusion_heat_c": 3.0,
               "fusion_window_s": 4.0, "fusion_tol_deg": 8.0, "heat_fus_mig": True, "heat_fus_note": "", "heat_fus_seen": []}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

WK = {"runs": 0, "ms": 0.0, "last_run": 0.0, "ran_t": 0.0, "hits": [], "calls": 0, "no_class": 0, "out_zone": 0, "busy": 0,
      "nc_t": 0.0, "oz_t": 0.0, "call_log": 0.0, "since": time.time(), "kinds": {}}
FUS = {"vetoed": 0, "confirmed": 0, "fault": 0, "latch": 0.0, "veto_t": 0.0, "ok_log": 0.0, "miss_log": 0.0, "fault_t": 0.0,
       "pend_t": 0.0, "pend_last": 0.0, "s_t": 0.0, "last": [], "since": time.time()}
HEAT = deque(maxlen=240)             # (thermal picture time, az0, az1, el0, el1) - warm spots as directions (degrees)
WZ_KINDS = ("person", "animal", "vehicle")
WK_MAX_ZONES = 8
WK_HIT_S = 4.0                       # a hit of the light AI counts this long for the head (it walks on meanwhile)
WK_DARK_BRIGHT = 30                  # mean brightness of the wide picture below this = infrared night (like AI_FULL_MIN_BRIGHT, 418z)
WK_VEHICLES = set(VEHICLE_LABELS) | {"bicycle", "vehicle", "motorbike"}
_WK_AI_LOCK = threading.Lock()
_wk_infer_base = AIDetector.infer


def _wk_infer_locked(self, img, conf_p, conf_o):          # the main camera (and its zoom) wait at most for one overview run
    with _WK_AI_LOCK:
        return _wk_infer_base(self, img, conf_p, conf_o)


# wraps: AIDetector.infer
AIDetector.infer = _wk_infer_locked


# ---- (a) classes -------------------------------------------------------------------------------------------------------
def wk_kind(cls_id):
    """COCO id (also the mapped ids of the own model, 195) -> "person" / "animal" / "vehicle" / "other\""""
    if int(cls_id) == 1:
        return "person"
    lab = COCO_LABELS.get(int(cls_id), "")
    if lab in ANIMALS:
        return "animal"
    if lab in WK_VEHICLES:
        return "vehicle"
    return "other"


def wk_classes():
    """which kinds may call the head: a person always, animals / vehicles by switch (animals always in the wildlife mode)"""
    s = {"person"}
    try:
        wild = kopf_wild_active()
    except Exception:
        wild = False
    if CFG.get("kopf_ov_ki_animal") or wild:
        s.add("animal")
    if CFG.get("kopf_ov_ki_vehicle"):
        s.add("vehicle")
    return s


def wk_ai():
    """(detector, "") when the light AI may run on the wide picture now, else (None, why)"""
    if not CFG.get("kopf_ov_ki"):
        return None, "off"
    try:
        if batt_save_active():
            return None, "battery saver"
    except NameError:
        pass
    if DEMO.get("on"):
        return None, "demo"
    w = WATCH_REF.get("w")
    ai = getattr(w, "ai", None)
    if ai is None or getattr(ai, "net", None) is None or not CFG.get("ai_enabled"):
        return None, "no AI"
    return ai, ""


def wk_dark(c=None):
    try:
        if is_dark():
            return True
    except Exception:
        pass
    b = getattr(c, "wk_bright", None) if c is not None else None
    return b is not None and b < WK_DARK_BRIGHT


def wk_mode(c=None):
    """"ai" = the light AI decides what calls the head, "motion" = movement alone (as before: AI off / not there / battery
    saver / dark with kopf_ov_ki_dark)"""
    ai, _why = wk_ai()
    if ai is None:
        return "motion"
    if CFG.get("kopf_ov_ki_dark") and wk_dark(c):
        return "motion"
    return "ai"


# ---- (b) geometry of the wide picture: picture point <-> direction (degrees, + = right / up) --------------------------------
def wz_spec(c=None):
    return str(getattr(c, "spec", "") or CFG.get("kopf_ov") or "")


def wz_on_head(c=None):
    try:
        return bool(cam_on_head(wz_spec(c)))
    except Exception:
        return False


def wz_geom(c=None):
    """{yaw, fh, fv, tilt, head, tf} of the overview camera: where its middle looks (yaw from the head's middle, or from the
    head itself when it sits on the head), its field of view, its tilt, whether it turns (and tilts) with the head"""
    sp = wz_spec(c)
    sc = weit_sim_cam() if sp == "sim:1" else None
    fh = kopf_ov_fov() if sp == str(CFG.get("kopf_ov") or "") else 0.0
    if not fh:
        try:
            fh = float(cam_fov_h(sp))
        except Exception:
            fh = 102.0
    if sc and str(sc.get("mount") or "") in WEIT_DEVICE_MOUNTS:
        try:
            fh = float(sc.get("fov_h") or fh)
            return {"yaw": float(sc.get("yaw_offset") or 0.0), "fh": fh, "fv": float(sc.get("fov_v") or fh * 67.0 / 102.0),
                    "tilt": float(sc.get("tilt_deg") or 0.0), "head": bool(sc.get("on_head")), "tf": bool(sc.get("tilt_follow"))}
        except (TypeError, ValueError):
            pass
    return {"yaw": float(CFG.get("kopf_ov_offset") or 0.0), "fh": fh, "fv": fh * 67.0 / 102.0, "tilt": 0.0,
            "head": wz_on_head(c), "tf": False}


def wz_head():
    """(pan °, tilt °) where the head really is (the simulated head, else the servo position)"""
    h = SIM.get("head") if CFG.get("sim_on") else None
    if isinstance(h, list) and len(h) >= 2:
        try:
            return float(h[0]), float(h[1])
        except (TypeError, ValueError):
            pass
    return servo_pos_deg()


def wz_dir(c, x, y, head=None, g=None):
    """picture point (0..1) of the overview -> (azimuth, elevation) in degrees; the fisheye is linear in the angle"""
    g = g or wz_geom(c)
    hp, ht = head if head is not None else (wz_head() if g["head"] else (0.0, 0.0))
    az = g["yaw"] + (float(x) - 0.5) * g["fh"] + (hp if g["head"] else 0.0)
    el = g["tilt"] + (0.5 - float(y)) * g["fv"] + (ht if g["head"] and g["tf"] else 0.0)
    return az, el


def wz_pic(c, az, el, head=None, g=None):
    """direction -> picture point of the overview now (may lie outside 0..1 = not in the picture)"""
    g = g or wz_geom(c)
    hp, ht = head if head is not None else (wz_head() if g["head"] else (0.0, 0.0))
    mid = g["yaw"] + (hp if g["head"] else 0.0)
    a = float(az) + 360.0 * round((mid - float(az)) / 360.0)
    x = 0.5 + (a - mid) / max(1.0, g["fh"])
    y = 0.5 - (float(el) - g["tilt"] - (ht if g["head"] and g["tf"] else 0.0)) / max(1.0, g["fv"])
    return x, y


# ---- (b) zones: include (trigger, green) / exclude (ignore, red), per zone the targets, per mount ----------------------------
def wz_key(c=None):
    """the mount the zones belong to: the simulator's mount of sim:1, else «head» / «fixed»"""
    if wz_spec(c) == "sim:1":
        try:
            m = weit_mount()
        except Exception:
            m = ""
        if m and m != "none":
            return m
    return "head" if wz_on_head(c) else "fixed"


WZ_KEY_NAMES = {"fixed": "Fixed (does not turn)", "head": "On the head (turns)", "case": "In the case (v5.2)", "scene": "Mast (scene)",
                "base": "Base front, fixed", "head_front": "Head front", "head_rear": "Head rear"}


def wz_key_name(key, lang=None):
    return tr(WZ_KEY_NAMES.get(str(key), str(key)), lang)


def wz_world(key):
    return str(key).startswith("head")


def wz_raw(key):
    sets = CFG.get("kopf_ov_zone_sets") if isinstance(CFG.get("kopf_ov_zone_sets"), dict) else {}
    if key in sets:
        return sets[key]
    return [] if wz_world(key) else (CFG.get("kopf_ov_zones") or [])


def wz_store(key, zones):
    sets = dict(CFG.get("kopf_ov_zone_sets") if isinstance(CFG.get("kopf_ov_zone_sets"), dict) else {})
    sets = {k: v for k, v in sets.items() if re.fullmatch(r"[a-z_]{1,20}", str(k))}
    sets[str(key)] = zones
    CFG["kopf_ov_zone_sets"] = dict(list(sets.items())[-8:])
    if key == "fixed":
        CFG["kopf_ov_zones"] = zones                          # the old list stays in step (older versions read it)


def wz_targets(z, mode):
    t = z.get("targets")
    if isinstance(t, list):
        out = [k for k in WZ_KINDS if k in t]
        if out:
            return out
    return list(WZ_KINDS)                                     # Besitzer 14.11.2026: new zones - all three


def wk_zones_clean(lst, world=False):
    """zones of the wide picture: fixed = picture points (0..1), world (head mounts) = corners as directions «ang»"""
    out = []
    for z in (lst if isinstance(lst, list) else [])[:WK_MAX_ZONES]:
        if not isinstance(z, dict):
            continue
        mode = "trigger" if z.get("mode") in ("trigger", "include") else "ignore"
        if world:
            ang = []
            for a in (z.get("ang") or [])[:40] if isinstance(z.get("ang"), list) else []:
                if isinstance(a, (list, tuple)) and len(a) == 2 and _num(a[0]) and _num(a[1]) and abs(a[0]) <= 720 and abs(a[1]) <= 90:
                    ang.append([round(float(a[0]), 2), round(float(a[1]), 2)])
            if len(ang) < 3:
                continue
            zid = str(z.get("id") or "")
            out.append({"id": zid if re.fullmatch(r"[0-9a-f]{8}", zid) else uuid.uuid4().hex[:8],
                        "name": str(z.get("name") or "").strip()[:40] or f"Zone {len(out) + 1}", "mode": mode,
                        "targets": wz_targets(z, mode), "ang": ang})
            continue
        c = _clean_zone(dict(z, mode="only" if mode == "trigger" else "ignore", anchor=False, src=None), len(out))
        if c:
            out.append({"id": c["id"], "name": c["name"], "mode": mode, "targets": wz_targets(z, mode), "points": c["points"]})
    return out


def wk_zones_active(c):
    """the zones of the mount the overview has now (head mounts: as directions - they stay on the ground when it turns)"""
    key = wz_key(c)
    return wk_zones_clean(wz_raw(key), wz_world(key))


def wk_zone_ok(nx, ny, zones=None, kind=None, c=None):
    """may this (foot point (nx, ny) of the wide picture, kind) call the head? kind None = movement alone (an exclude zone
    counts when it excludes persons), "any" = movement the AI shall look at (excluded only where all three are excluded).
    Exclude wins over include; without an include zone the whole picture counts (for the kinds of the switches)."""
    zs = wk_zones_active(c) if zones is None else zones
    if not zs:
        return kind in (None, "any") or kind in wk_classes()
    p = wz_dir(c, nx, ny) if any(z.get("ang") for z in zs) else None

    def inside(z):
        if z.get("ang"):
            pts = z["ang"]; ca = sum(a[0] for a in pts) / len(pts)
            return point_in_poly(p[0] + 360.0 * round((ca - p[0]) / 360.0), p[1], pts)
        return point_in_poly(nx, ny, z["points"])

    def acts(z):
        t = set(z.get("targets") or WZ_KINDS)
        if kind == "any":
            return z["mode"] == "trigger" or t >= set(WZ_KINDS)
        if kind is None:
            return z["mode"] == "trigger" or "person" in t
        return kind in t
    if any(z["mode"] == "ignore" and acts(z) and inside(z) for z in zs):
        return False
    trig = [z for z in zs if z["mode"] == "trigger"]
    if not trig:
        return kind in (None, "any") or kind in wk_classes()
    return any(acts(z) and inside(z) for z in trig)


def wk_foot(b, W, H):
    return (b[0] + b[2] / 2.0) / float(W), (b[1] + b[3] * 0.92) / float(H)


def wk_draw_zones(frame, c, zones=None):
    """the zones into a copy of the wide picture (window view, 599-like): green = include, red = exclude, P / A / V = targets"""
    out = frame.copy()
    H, W = out.shape[:2]
    zs = wk_zones_active(c) if zones is None else zones
    lay = out.copy()
    for z in zs:
        pts = [wz_pic(c, a[0], a[1]) for a in z["ang"]] if z.get("ang") else z["points"]
        P = np.array([[int(x * W), int(y * H)] for x, y in pts], np.int32)
        col = (107, 207, 63) if z["mode"] == "trigger" else (96, 96, 255)
        cv2.fillPoly(lay, [P], col)
        cv2.polylines(out, [P], True, col, 2, cv2.LINE_AA)
        lab = z["name"].encode("ascii", "replace").decode()[:24] + " [" + "".join(k[0].upper() for k in z.get("targets") or WZ_KINDS) + "]"
        x0, y0 = int(max(4, min(W - 120, P[:, 0].min()))), int(max(16, min(H - 6, P[:, 1].min() - 6)))
        cv2.putText(out, lab, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(out, lab, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    return cv2.addWeighted(lay, 0.25, out, 0.75, 0)


# ---- (a) the light AI on the wide picture (called by the extra camera, 440) ------------------------------------------
def wk_wanted(c):
    return (str(CFG.get("kopf_ov") or "") == str(getattr(c, "spec", "")) and CFG.get("kopf_on") and CFG.get("kopf_ov_on")
            and CFG.get("armed") and STATE.get("arm_state") == "armed")


def wk_gap():
    fps = max(0.1, min(5.0, float(CFG.get("kopf_ov_ki_fps") or 1.0)))
    gap = max(1.0 / fps, 3.0 * WK["ms"] / 1000.0)
    ct = STATE.get("cpu_temp") or 0
    gap *= 2.0 if ct >= 75 else 1.0
    try:
        if CFG.get("sim_on") and sim_eco_now():
            gap *= 2.0
    except NameError:
        pass
    return gap


def wk_crop(box, W, H):
    """a square around the movement (2.2 x its size, at least 30 % of the picture height), inside the picture"""
    x, y, w, h = box[:4]
    s = int(min(min(W, H), max(2.2 * max(w, h), 0.3 * min(W, H))))
    cx, cy = x + w / 2.0, y + h / 2.0
    x0 = int(max(0, min(W - s, cx - s / 2.0))); y0 = int(max(0, min(H - s, cy - s / 2.0)))
    return x0, y0, s


def weit_ki_frame(c, frame):
    """440, every picture of an extra camera: the overview runs the light AI on its movement (see the head of this part)"""
    if not wk_wanted(c):
        return
    now = time.time()
    H, W = frame.shape[:2]
    if now - getattr(c, "wk_bt", 0.0) > 2.0:
        c.wk_bt = now
        try:
            c.wk_bright = float(np.mean(cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)))
        except cv2.error:
            pass
    for h_ in WK["hits"]:                                    # the last hits in the picture (green), for the live view
        if now - h_[0] < 1.5:
            nb = h_[3]; col = (60, 220, 60) if h_[5] else (90, 90, 230)
            p1 = (int(nb[0] * W), int(nb[1] * H)); p2 = (int((nb[0] + nb[2]) * W), int((nb[1] + nb[3]) * H))
            cv2.rectangle(frame, p1, p2, col, 2)
            cv2.putText(frame, f"{h_[1]} {h_[2]:.2f}", (p1[0], max(40, p1[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    if not c.motion or not c.boxes or wk_mode(c) != "ai" or now - WK["last_run"] < wk_gap():
        return
    zs = wk_zones_active(c)
    cand = [b for b in c.boxes if b[2] * b[3] <= 0.3 * W * H and wk_zone_ok(*wk_foot(b, W, H), zones=zs, kind="any", c=c)]
    if not cand:
        return
    ai, _why = wk_ai()
    if ai is None:
        return
    if not _WK_AI_LOCK.acquire(blocking=False):
        WK["busy"] += 1                                      # the main camera runs its AI now: it has priority
        return
    try:
        WK["last_run"] = now
        x0, y0, s = wk_crop(max(cand, key=lambda b: b[2] * b[3]), W, H)
        img = np.ascontiguousarray(frame[y0:y0 + s, x0:x0 + s])
        t0 = time.time()
        persons, objs = _wk_infer_base(ai, img, float(CFG.get("ai_conf") or 0.5), float(CFG.get("object_conf") or 0.5))
        ms = (time.time() - t0) * 1000.0
    finally:
        _WK_AI_LOCK.release()
    WK["ms"] = ms if not WK["runs"] else 0.8 * WK["ms"] + 0.2 * ms
    WK["runs"] += 1; WK["ran_t"] = now
    found = [("person", float(b[4]), b) for b in persons] + [(wk_kind(o[5]), float(o[4]), o) for o in objs]
    hits = []
    for k, cf, b in found:
        if k == "other":
            continue
        nb = ((x0 + b[0]) / W, (y0 + b[1]) / H, b[2] / W, b[3] / H)
        ok = wk_zone_ok(nb[0] + nb[2] / 2.0, nb[1] + nb[3] * 0.92, zones=zs, kind=k, c=c)
        hits.append((now, k, cf, nb, kopf_ov_deg(nb[0] + nb[2] / 2.0), ok))  # direction now: right after the head turned too
        WK["kinds"][k] = WK["kinds"].get(k, 0) + 1
    WK["hits"] = (hits + [h for h in WK["hits"] if now - h[0] < WK_HIT_S])[:12]


def weit_pick(c, now, mode=None):
    """162 _kopf_ov_tick: (cx, size) of what may call the head now, or None. Zones first (outside = only noted), then the
    light AI (a hit of a wanted kind in its zones; movement without one = the head stays). mode None = wk_mode(c).
    A hit keeps its direction: cx is where it is in the picture of now (the camera may sit on the head)."""
    raw = kopf_ov_target(c)                                   # moving, 2+ pictures, not half the picture (light, wind)
    if raw is None:
        return None
    W, H = c.wh
    zs = wk_zones_active(c)
    mode = mode or wk_mode(c)
    inz = [b for b in c.boxes if b[2] * b[3] <= 0.3 * W * H
           and wk_zone_ok(*wk_foot(b, W, H), zones=zs, kind=None if mode != "ai" else "any", c=c)]
    if not inz:
        if now - WK["oz_t"] > 10.0:
            WK["out_zone"] += 1
            if now - WK["oz_t"] > 60.0:
                log_event("servo", "Overview: movement outside the trigger zones - only noted")
        WK["oz_t"] = now
        return None
    if mode != "ai":
        x, y, w, h = max(inz, key=lambda b: b[2] * b[3])
        return ((x + w / 2.0) / W, w * h / float(W * H))
    hits = [h for h in WK["hits"] if now - h[0] < WK_HIT_S and h[5]]
    if hits:
        t_, kind, conf, nb, az, _ok = max(hits, key=lambda h: (h[0], h[2]))
        WK["calls"] += 1
        if now - WK["call_log"] > 20.0:
            WK["call_log"] = now
            log_event("servo", f"Overview AI: {kind} seen ({conf:.2f}) - the head looks")
        d = (az - kopf_ov_deg(0.5) + 180.0) % 360.0 - 180.0
        cx = 0.5 + d / max(1.0, kopf_ov_fov())
        return (cx, nb[2] * nb[3])
    if now - WK["ran_t"] < 3.0:                               # the AI looked at this movement: nothing that may call the head
        if now - WK["nc_t"] > 10.0:
            WK["no_class"] += 1
            if now - WK["nc_t"] > 60.0:
                log_event("servo", "Overview: movement without a wanted target - the head stays (light AI)")
        WK["nc_t"] = now
    return None


# ---- (c) thermal confirmation at night: direction + time window ----------------------------------------------------------
def fus_thermal_ok():
    """a thermal source is chosen and gives pictures right now"""
    th = THERMAL
    return (bool(CFG.get("thermal_source")) and th is not None and getattr(th, "frame", None) is not None
            and time.time() - float(getattr(th, "t", 0.0) or 0.0) < 3.0 and STATE.get("thermal") == "connected")


def fus_night():
    """the day / night decision of MoveEye (is_dark, else the low light of the camera)"""
    try:
        return bool(is_dark() or STATE.get("lowlight"))
    except Exception:
        return bool(STATE.get("lowlight"))


def fus_spots(f, temps, dc=3.0, boxes=()):
    """pure: the warm spots of the aligned thermal picture f as boxes (0..1): clearly warmer than the median of the picture
    (°C: + dc, 8 bit: + max(25, 20 % of the rest)) + the warm moving bodies of THERMAL.detect"""
    out = [tuple(float(v) for v in b[:4]) for b in boxes or ()]
    if f is None:
        return out
    g = f.astype(np.float32) if temps else ThermalCam.to_gray8(f).astype(np.float32)
    if g.ndim == 3:
        g = g.mean(axis=2)
    H, W = g.shape[:2]
    if H < 2 or W < 2:
        return out
    med = float(np.median(g))
    need = float(dc) if temps else max(25.0, 0.2 * (255.0 - med))
    m = (g >= med + need).astype(np.uint8)
    n, _lab, st, _c = cv2.connectedComponentsWithStats(m, connectivity=8)
    for i in range(1, min(n, 24)):
        x, y, w, h, a = (int(v) for v in st[i])
        if a >= max(2, int(0.0004 * W * H)):
            out.append((x / W, y / H, w / float(W), h / float(H)))
    return out


def fus_box_dir(nb, pan, tilt, hf, vf):
    """a box (0..1) of the main picture with the head at pan / tilt (%) -> (az0, az1, el0, el1) degrees"""
    a0, e1 = place_pic_to_ang(nb[0], nb[1], pan, tilt, hf, vf)
    a1, e0 = place_pic_to_ang(nb[0] + nb[2], nb[1] + nb[3], pan, tilt, hf, vf)
    return min(a0, a1), max(a0, a1), min(e0, e1), max(e0, e1)


def fus_match(pd, heat, now, win, tol):
    """pure: is there a warm spot (t, az0, az1, el0, el1) within win seconds and tol degrees (vertical 2 x tol) of the
    person's direction pd (az0, az1, el0, el1)? -> the angle off (0 = overlap) or None"""
    a0, a1, e0, e1 = pd
    ca, best = (a0 + a1) / 2.0, None
    for t, h0, h1, g0, g1 in heat:
        if now - t > win or t - now > 1.0:
            continue
        sh = 360.0 * round((ca - (h0 + h1) / 2.0) / 360.0)
        h0, h1 = h0 + sh, h1 + sh
        da = max(0.0, h0 - a1, a0 - h1)
        de = max(0.0, g0 - e1, e0 - g1)
        if da <= tol and de <= 2.0 * tol and (best is None or da < best):
            best = da
    return best


def fus_cover():
    """(x0, x1) of the main picture that the thermal picture covers (simulator: a narrower thermal camera sits in the middle)"""
    try:
        g = ThermalCam.sim_geom()
    except Exception:
        g = None
    if g and g[0] < 1.0:
        return 0.5 - g[0] / 2.0, 0.5 + g[0] / 2.0
    return 0.0, 1.0


def fus_sample(now):
    """the warm spots of the newest thermal picture into HEAT (as directions, with the head of that moment)"""
    th = THERMAL
    try:
        t = float(getattr(th, "t", 0.0) or 0.0)
        if t <= FUS["s_t"] or now - FUS.get("s_wall", 0.0) < 0.2:
            return
        FUS["s_t"] = t; FUS["s_wall"] = now
        fr = th.frame
        if fr is None:
            return
        boxes = th.boxes if time.time() - float(getattr(th, "det_t", 0.0) or 0.0) < 2.0 else ()
        sp = fus_spots(th.crop(fr), fr.dtype != np.uint8, float(CFG.get("fusion_heat_c") or 3.0), boxes)
        pan, tilt = servo_pos()
        hf, vf = cam_fov()
        for b in sp[:16]:
            HEAT.append((t,) + fus_box_dir(b, pan, tilt, hf, vf))
    except Exception:
        pass


def fus_decide(on, thermal_ok, night, heats):
    """the decision table: "pass" (as before) / "confirmed" (heat at the person) / "veto" (night, thermal ok, no heat)"""
    if not on or not thermal_ok or not night:
        return "pass"
    if any(h is True for h in heats):
        return "confirmed"
    if not heats or all(h is None for h in heats):
        return "pass"
    return "veto"


FUS_TXT = {"confirmed": "Thermal camera confirmed", "veto": "Without heat - not counted",
           "fault": "Thermal camera faulty - alarm counts without heat check", "wait": "Waiting for heat"}


def fus_note(what, now, detail=""):
    FUS["last"] = ([{"t": round(now, 1), "what": what, "detail": detail}] + FUS["last"])[:6]


_alarm_gate_639zw = alarm_gate


def alarm_gate(w, frame, persons, now):                   # + 639zw: at night a person alarm needs heat in its direction
    """only person alarms come here (410 handle_recording) - sabotage, SOS, alarm by hand, noise and heat alarms never.
    Day, switch off, no thermal source: as before. Thermal source chosen but no fresh picture: fail open (alarm counts)."""
    res = _alarm_gate_639zw(w, frame, persons, now)
    if not CFG.get("alarm_heat_fusion") or not CFG.get("thermal_source") or not fus_night():
        FUS["pend_t"] = 0.0
        return res
    ok = fus_thermal_ok()
    if ok:
        fus_sample(now)
    if not res:
        if now - FUS["pend_last"] > 5.0:
            FUS["pend_t"] = 0.0
        return res
    if now < FUS["latch"]:
        return res
    if not ok:
        if now - FUS["fault_t"] > 10.0:
            FUS["fault"] += 1; fus_note("fault", now, str(STATE.get("thermal") or "")[:40])
            if now - FUS["miss_log"] > 60.0:
                FUS["miss_log"] = now
                log_event("person", f"{FUS_TXT['fault']} ({str(STATE.get('thermal') or 'no picture')[:40]})")
        FUS["fault_t"] = now; FUS["pend_t"] = 0.0
        return res
    pw, ph = getattr(w, "_proc_size", None) or (frame.shape[1], frame.shape[0])
    pan, tilt = servo_pos()
    hf, vf = cam_fov()
    win = max(1.0, min(15.0, float(CFG.get("fusion_window_s") or 4.0)))
    tol = max(1.0, min(30.0, float(CFG.get("fusion_tol_deg") or 8.0)))
    cx0, cx1 = fus_cover()
    best, seen = None, 0
    for b in res[:6]:
        nb = (b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph)
        if not (cx0 <= nb[0] + nb[2] / 2.0 <= cx1):
            continue                                          # outside the thermal picture: cannot tell
        seen += 1
        m = fus_match(fus_box_dir(nb, pan, tilt, hf, vf), HEAT, now, win, tol)
        if m is not None and (best is None or m < best):
            best = m
    if not seen:
        return res
    if best is not None:
        FUS["confirmed"] += 1; FUS["latch"] = now + 10.0
        wait = now - FUS["pend_t"] if FUS["pend_t"] else 0.0
        FUS["pend_t"] = 0.0
        det = f"{best:.0f}°" + (f", +{wait:.1f} s" if wait > 0.05 else "")
        fus_note("confirmed", now, det)
        log_event("person", f"{FUS_TXT['confirmed']} - alarm counts (heat {det})")
        return res
    if not FUS["pend_t"]:
        FUS["pend_t"] = now
    FUS["pend_last"] = now
    if now - FUS["pend_t"] < win:
        return []                                             # the thermal camera has a moment to see it
    if now - FUS["veto_t"] > 10.0:
        FUS["vetoed"] += 1
        fus_note("veto", now, f"{win:.0f} s, ±{tol:.0f}°")
        log_event("heat", f"{FUS_TXT['veto']} (night, no heat within {win:.0f} s and ±{tol:.0f}°)")
    FUS["veto_t"] = now
    return []


_IMP.setdefault("heat", re.compile(r"^Without heat"))      # the timeline (425) shows it (not as an alarm)


_th_wanted_639zw = ThermalCam.wanted


def _wk_th_wanted(self):                                   # the thermal camera runs at night for the fusion (only when chosen)
    s = _th_wanted_639zw(self)
    if s or not CFG.get("alarm_heat_fusion") or not CFG.get("thermal_source") or not CFG.get("detection_on"):
        return s
    if not (CFG.get("armed") and fus_night()):
        return s
    spec = CFG["thermal_source"]
    return "" if spec == STATE.get("source_id") else spec


# wraps: ThermalCam.wanted
ThermalCam.wanted = _wk_th_wanted


def heat_confirm_migrate(cfg_in):
    """once per settings file (Besitzer 14.11.2026): the night thermal confirmation on for existing devices too, with a
    one-time notice in «New in this version» (web and window). New devices have heat_fus_mig from the factory."""
    if not isinstance(cfg_in, dict) or cfg_in.get("heat_fus_mig"):
        return []
    CFG["heat_fus_mig"] = True
    CFG["heat_fus_note"] = "pending"; CFG["heat_fus_seen"] = []
    was = cfg_in.get("alarm_heat_fusion")
    CFG["alarm_heat_fusion"] = True
    return ["thermal confirmation at night switched on" + (" (was off)" if was is False else "")]


HEAT_NOTE = ("New: at night a person alarm counts only when the thermal camera confirms heat in the same direction - "
             "now on for all devices, yours too. By day and without a thermal camera nothing changes. Switch off: Settings → «At night with a thermal camera …».")
_news_state_639zw = news_state
_news_seen_639zw = news_seen


def news_state(who="web", lang=None):                     # + 639zw: the one-time notice of the thermal confirmation
    st = _news_state_639zw(who, lang)
    if CFG.get("heat_fus_note") == "pending" and who not in (CFG.get("heat_fus_seen") or []):
        it = {"v": APP_VERSION, "t": "🌡 " + tr(HEAT_NOTE, lang), "href": "/settings?setting=alarm_heat_fusion"}
        st = dict(st, items=[it] + list(st.get("items") or []), show=True)
    return st


def news_seen(who="web"):                                 # + 639zw
    if CFG.get("heat_fus_note") == "pending":
        CFG["heat_fus_seen"] = sorted(set(CFG.get("heat_fus_seen") or []) | {who})
    return _news_seen_639zw(who)


_timeline_build_639zw = timeline_build


def timeline_build(day=None, mode="night", lang=None):    # + 639zw: the thermal decisions in the language of the page
    tl = _timeline_build_639zw(day, mode, lang)
    try:
        for it in tl.get("items") or []:
            tx = str(it.get("text") or "") if it.get("type") == "log" else ""
            for k in ("confirmed", "veto", "fault"):
                if tx.startswith(FUS_TXT[k]):
                    it["text"] = ("🌡 " if k != "veto" else "❄ ") + tr(FUS_TXT[k], lang) + tx[len(FUS_TXT[k]):]
                    if k == "veto":
                        it["alarm"] = False
    except Exception:
        pass
    return tl


def wache_state(lang=None):
    """/api/wache: what the overview and the night thermal check did since the start (measurable)"""
    c = kopf_ov_cam()
    ai, why = wk_ai()
    key = wz_key(c) if c is not None else ""
    return {"ov": bool(c), "mode": wk_mode(c) if c else "", "ai": not why, "why": why, "classes": sorted(wk_classes()),
            "zones": len(wk_zones_active(c)) if c is not None else 0, "zones_on": bool(c is not None and wk_zones_active(c)),
            "mount": key, "world": wz_world(key) if key else False,
            "runs": WK["runs"], "ms": round(WK["ms"], 1), "calls": WK["calls"], "no_class": WK["no_class"], "kinds": dict(WK["kinds"]),
            "out_zone": WK["out_zone"], "busy": WK["busy"], "since": int(WK["since"]),
            "fusion": {"on": bool(CFG.get("alarm_heat_fusion")), "thermal": fus_thermal_ok(), "night": fus_night(),
                       "chosen": bool(CFG.get("thermal_source")), "window": CFG.get("fusion_window_s"), "tol": CFG.get("fusion_tol_deg"),
                       "confirmed": FUS["confirmed"], "vetoed": FUS["vetoed"], "fault": FUS["fault"],
                       "last": [dict(x, text=tr(FUS_TXT[x["what"]], lang)) for x in FUS["last"]]}}


# ---- web: /api/wache, /api/weit/zones, /api/weit/frame.jpg ------------------------------------------------------------
def wk_cam():
    c = kopf_ov_cam()
    if c is None:
        try:
            c = view3_wide_cam()
        except Exception:
            c = None
    return c


def wk_zones_view(c):
    """GET /api/weit/zones: the zones of the mount now, head mounts projected into the picture of now (+ the head)"""
    key = wz_key(c) if c is not None else "fixed"
    zs = wk_zones_clean(wz_raw(key), wz_world(key))
    head = list(wz_head()) if wz_world(key) else None
    out = []
    for z in zs:
        z = dict(z)
        if z.get("ang"):
            g = wz_geom(c)
            z["points"] = [[round(v, 4) for v in wz_pic(c, a[0], a[1], tuple(head), g)] for a in z.pop("ang")]
        out.append(z)
    return {"zones": out, "key": key, "key_name": wz_key_name(key, cur_lang()), "world": wz_world(key), "head": head}


def wk_zones_save(c, zones, head=None):
    """POST /api/weit/zones: picture points -> stored (head mounts: as directions with the head the editor had)"""
    key = wz_key(c) if c is not None else "fixed"
    if wz_world(key):
        try:
            hd = (float(head[0]), float(head[1])) if isinstance(head, list) and len(head) == 2 else wz_head()
            if not all(math.isfinite(v) for v in hd):
                hd = wz_head()
        except (TypeError, ValueError):
            hd = wz_head()
        g = wz_geom(c); conv = []
        for z in zones if isinstance(zones, list) else []:
            if not isinstance(z, dict):
                continue
            pts = [p for p in (z.get("points") or [])[:40] if isinstance(p, (list, tuple)) and len(p) == 2 and _num(p[0]) and _num(p[1])]
            conv.append(dict(z, ang=[list(wz_dir(c, max(-4.0, min(5.0, p[0])), max(-4.0, min(5.0, p[1])), hd, g)) for p in pts]))
        zones = conv
    zs = wk_zones_clean(zones, wz_world(key))
    wz_store(key, zs)
    return key, zs


_smalltv_routes_639zw = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zw
    _smalltv_routes_639zw(app, reply, body)
    from flask import Response, request

    @app.route("/api/wache")
    def wk_api_state():
        return reply(wache_state(norm_lang(request.args.get("lang"))))

    @app.route("/api/weit/zones", methods=["GET", "POST"])
    def wk_api_zones():
        c = wk_cam()
        if request.method == "POST":
            d = body()
            if not isinstance(d.get("zones"), list):
                return reply({"ok": False, "error": tr_err("invalid zones", norm_lang(d.get("lang")))}, 400)
            key, zs = wk_zones_save(c, d.get("zones"), d.get("head"))
            save_settings(); log_event("sys", f"Zones of the wide picture updated ({key}: {len(zs)})")
            return reply({"ok": True, "error": None})
        v = wk_zones_view(c)
        return reply(dict(v, avail=c is not None, n=getattr(c, "idx", None), on_head=wz_on_head(c) if c is not None else False,
                          ov=bool(kopf_ov_cam())))

    @app.route("/api/weit/frame.jpg")
    def wk_api_frame():
        c = wk_cam()
        if c is None:
            return Response("no wide camera", 404)
        f = wk_raw(c, 2.5)
        if f is None:
            return Response("no frame yet", 503)
        if f.shape[1] > 960:
            f = cv2.resize(f, (960, int(f.shape[0] * 960 / f.shape[1])), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


def wk_raw(c, wait=0.0):
    """the newest picture of the wide camera without boxes (440 keeps it while somebody asks), or None"""
    if time.time() > c.raw_until:
        c.raw = None
    c.raw_until = time.time() + 15
    t_end = time.time() + wait
    while c.raw is None and time.time() < t_end:
        time.sleep(0.1)
    return c.raw


# ---- settings (web + window: the same lists) ------------------------------------------------------------------------------
_WK_TG = [
    ("kopf_ov_ki", "Overview: light AI on the wide picture - only a person, an animal or a vehicle calls the head (which ones: switches below and per zone)"),
    ("kopf_ov_ki_animal", "Overview: animals call the head too (always in the wildlife mode)"),
    ("kopf_ov_ki_vehicle", "Overview: vehicles call the head too"),
    ("kopf_ov_ki_dark", "Overview in the dark: movement alone calls the head (the AI sees little in the infrared wide picture - the thermal camera checks at the head)"),
]
_wk_i = next((i for i, t_ in enumerate(TOGGLES) if t_[1] == "kopf_ov_on"), len(TOGGLES) - 1)
for _j, (_k, _l) in enumerate(_WK_TG):
    TOGGLES.insert(_wk_i + 1 + _j, ("Automatic head movement", _k, _l))
_wk_s = next((i for i, s_ in enumerate(SLIDERS) if s_[1] == "kopf_ov_fov"), len(SLIDERS) - 1)
SLIDERS.insert(_wk_s + 1, ("Automatic head movement", "kopf_ov_ki_fps", "Overview AI: at most runs per second", 0.2, 3.0, 0.1))
_wk_c = next((i for i, t_ in enumerate(TOGGLES) if t_[1] == "alarm_confirm2"), len(TOGGLES) - 1)
_wk_sec = TOGGLES[_wk_c][0] if 0 <= _wk_c < len(TOGGLES) and TOGGLES[_wk_c][1] == "alarm_confirm2" else "Detection"
TOGGLES.insert(_wk_c + 1, (_wk_sec, "alarm_heat_fusion",
                           "At night with a thermal camera: a person alarm counts only when the thermal camera sees heat in its direction (by day as before)"))
_wk_f = max([i for i, s_ in enumerate(SLIDERS) if s_[0] == _wk_sec] or [len(SLIDERS) - 1])
SLIDERS.insert(_wk_f + 1, (_wk_sec, "fusion_window_s", "Thermal confirmation at night: time window (seconds)", 1.0, 10.0, 0.5))
SLIDERS.insert(_wk_f + 2, (_wk_sec, "fusion_tol_deg", "Thermal confirmation at night: direction tolerance (degrees)", 2.0, 20.0, 1.0))

# ---- translations (English key: Deutsch, Français, Italiano, Rumantsch) ----------------------------------------------------
_HX_WK = {
    "Overview: light AI on the wide picture - only a person, an animal or a vehicle calls the head (which ones: switches below and per zone)": (
        "Übersicht: leichte KI im Weitwinkelbild – nur eine Person, ein Tier oder ein Fahrzeug ruft den Kopf (welche: Schalter darunter und pro Zone)",
        "Vue d’ensemble : IA légère sur l’image grand-angle – seule une personne, un animal ou un véhicule appelle la tête (lesquels : interrupteurs ci-dessous et par zone)",
        "Panoramica: IA leggera sull’immagine grandangolare – solo una persona, un animale o un veicolo chiama la testa (quali: interruttori sotto e per zona)",
        "Survista: IA levgia en il maletg da grond angul – mo ina persuna, in animal u in vehichel clama il chau (tgenins: interruptuors sutvart e per zona)"),
    "Overview: animals call the head too (always in the wildlife mode)": (
        "Übersicht: auch Tiere rufen den Kopf (im Wildtier-Modus immer)",
        "Vue d’ensemble : les animaux appellent aussi la tête (toujours en mode faune)",
        "Panoramica: anche gli animali chiamano la testa (sempre in modalità fauna)",
        "Survista: er animals claman il chau (adina en il modus da selvaschina)"),
    "Overview: vehicles call the head too": (
        "Übersicht: auch Fahrzeuge rufen den Kopf", "Vue d’ensemble : les véhicules appellent aussi la tête",
        "Panoramica: anche i veicoli chiamano la testa", "Survista: er vehichels claman il chau"),
    "Overview in the dark: movement alone calls the head (the AI sees little in the infrared wide picture - the thermal camera checks at the head)": (
        "Übersicht im Dunkeln: Bewegung allein ruft den Kopf (die KI sieht im Infrarot-Weitwinkelbild wenig – am Kopf prüft das Wärmebild)",
        "Vue d’ensemble dans l’obscurité : le mouvement seul appelle la tête (l’IA voit peu dans l’image grand-angle infrarouge – la caméra thermique vérifie à la tête)",
        "Panoramica al buio: basta il movimento per chiamare la testa (l’IA vede poco nell’immagine grandangolare a infrarossi – alla testa controlla la termocamera)",
        "Survista en il stgir: il moviment sulet clama il chau (l’IA vesa pauc en il maletg infracotschen da grond angul – al chau controllescha il maletg termic)"),
    "Overview AI: at most runs per second": (
        "Übersichts-KI: höchstens Läufe pro Sekunde", "IA de la vue d’ensemble : au plus passages par seconde",
        "IA panoramica: al massimo esecuzioni al secondo", "IA da la survista: al pli passadas per secunda"),
    "At night with a thermal camera: a person alarm counts only when the thermal camera sees heat in its direction (by day as before)": (
        "Nachts mit Wärmebild: ein Personen-Alarm zählt nur, wenn das Wärmebild in seiner Richtung Wärme sieht (tagsüber wie bisher)",
        "La nuit avec caméra thermique : une alarme personne ne compte que si l’image thermique voit de la chaleur dans sa direction (le jour comme avant)",
        "Di notte con termocamera: un allarme persona conta solo se l’immagine termica vede calore nella sua direzione (di giorno come prima)",
        "La notg cun maletg termic: in alarm da persuna quinta mo, sch’il maletg termic vesa chalur en sia direcziun (di sco fin ussa)"),
    "Thermal confirmation at night: time window (seconds)": (
        "Wärmebild-Bestätigung nachts: Zeitfenster (Sekunden)", "Confirmation thermique la nuit : fenêtre de temps (secondes)",
        "Conferma termica di notte: finestra di tempo (secondi)", "Confermaziun termica la notg: fanestra da temp (secundas)"),
    "Thermal confirmation at night: direction tolerance (degrees)": (
        "Wärmebild-Bestätigung nachts: Richtungs-Spielraum (Grad)", "Confirmation thermique la nuit : tolérance de direction (degrés)",
        "Conferma termica di notte: tolleranza di direzione (gradi)", "Confermaziun termica la notg: toleranza da direcziun (grads)"),
    HEAT_NOTE: (
        "Neu: Nachts zählt ein Personen-Alarm nur, wenn das Wärmebild in derselben Richtung Wärme bestätigt – ab jetzt auf allen Geräten an, auch auf deinem. Tagsüber und ohne Wärmebildkamera ändert sich nichts. Abschalten: Einstellungen → «Nachts mit Wärmebild …».",
        "Nouveau : la nuit, une alarme personne ne compte que si l’image thermique confirme de la chaleur dans la même direction – désormais activé sur tous les appareils, le tien aussi. Le jour et sans caméra thermique, rien ne change. Désactiver : Réglages → «La nuit avec caméra thermique …».",
        "Novità: di notte un allarme persona conta solo se l’immagine termica conferma calore nella stessa direzione – ora attivo su tutti i dispositivi, anche sul tuo. Di giorno e senza termocamera non cambia nulla. Disattivare: Impostazioni → «Di notte con termocamera …».",
        "Nov: La notg quinta in alarm da persuna mo, sch’il maletg termic conferma chalur en la medema direcziun – ussa activ sin tut ils apparats, er sin il tes. Di e senza camera termica na sa mida nagut. Deactivar: Parameters → «La notg cun maletg termic …»."),
    "Thermal camera confirmed": ("Wärmebild bestätigt", "Image thermique confirmée", "Immagine termica confermata", "Maletg termic confermà"),
    "Without heat - not counted": ("ohne Wärme – nicht gewertet", "sans chaleur – non compté", "senza calore – non conteggiato", "senza chalur – betg quintà"),
    "Thermal camera faulty - alarm counts without heat check": (
        "Wärmebild gestört – Alarm zählt ohne Wärme-Prüfung", "Caméra thermique en panne – l’alarme compte sans contrôle de chaleur",
        "Termocamera guasta – l’allarme conta senza controllo del calore", "Maletg termic disturbà – l’alarm quinta senza controlla da chalur"),
    "Waiting for heat": ("wartet auf Wärme", "attend la chaleur", "attende il calore", "spetga chalur"),
    "Zones in the wide picture": ("Zonen im Weitwinkelbild", "Zones dans l’image grand-angle", "Zone nell’immagine grandangolare", "Zonas en il maletg da grond angul"),
    "Zones in the wide picture (browser)": ("Zonen im Weitwinkelbild (Browser)", "Zones dans l’image grand-angle (navigateur)",
                                            "Zone nell’immagine grandangolare (browser)", "Zonas en il maletg da grond angul (navigatur)"),
    "Edit in the browser": ("Im Browser bearbeiten", "Modifier dans le navigateur", "Modifica nel browser", "Modifitgar en il navigatur"),
    "New picture": ("Neues Bild", "Nouvelle image", "Nuova immagine", "Nov maletg"),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
    "Person": ("Person", "Personne", "Persona", "Persuna"),
    "Animal": ("Tier", "Animal", "Animale", "Animal"),
    "Vehicle": ("Fahrzeug", "Véhicule", "Veicolo", "Vehichel"),
    "Targets": ("Ziele", "Cibles", "Obiettivi", "Finamiras"),
    "include": ("einschliessen", "inclure", "includere", "includer"),
    "exclude": ("ausschliessen", "exclure", "escludere", "excluder"),
    "No zones - the whole picture counts.": ("Keine Zonen – das ganze Bild zählt.", "Aucune zone – toute l’image compte.",
                                            "Nessuna zona – conta tutta l’immagine.", "Naginas zonas – l’entir maletg quinta."),
    "Mount": ("Montage", "Montage", "Montaggio", "Montascha"),
    "Fixed (does not turn)": ("Fest (dreht nicht)", "Fixe (ne tourne pas)", "Fissa (non gira)", "Fixa (na sa volva betg)"),
    "On the head (turns)": ("Auf dem Kopf (dreht mit)", "Sur la tête (tourne)", "Sulla testa (gira)", "Sin il chau (sa volva)"),
    "as directions (turns with the head)": ("als Richtungen (dreht mit dem Kopf)", "en directions (tourne avec la tête)",
                                            "come direzioni (gira con la testa)", "sco direcziuns (sa volva cun il chau)"),
    "No picture of the wide camera yet - try again in a moment.": (
        "Noch kein Bild der Weitwinkel-Kamera – gleich nochmals versuchen.", "Pas encore d’image de la caméra grand-angle – réessaie dans un instant.",
        "Ancora nessuna immagine della telecamera grandangolare – riprova tra poco.", "Anc nagin maletg da la camera da grond angul – emprova pli tard danovamain."),
    "without a target": ("ohne Ziel", "sans cible", "senza obiettivo", "senza finamira"),
    "thermal camera faulty": ("Wärmebild gestört", "caméra thermique en panne", "termocamera guasta", "maletg termic disturbà"),
    "z-wworld": (
        "Die Weitwinkel-Kamera dreht mit dem Kopf: die Zonen bleiben in ihrer Richtung (am Boden), auch wenn der Kopf dreht. Was gerade ausserhalb des Bildes liegt, ist nicht zu sehen, gilt aber weiter.",
        "La caméra grand-angle tourne avec la tête : les zones restent dans leur direction (au sol) quand la tête tourne. Ce qui est hors de l’image n’est pas visible mais reste valable.",
        "La telecamera grandangolare gira con la testa: le zone restano nella loro direzione (a terra) quando la testa gira. Ciò che è fuori dall’immagine non si vede ma resta valido.",
        "La camera da grond angul sa volva cun il chau: las zonas restan en lur direcziun (sin il terren), er sch’il chau sa volva. Quai che stat ordaifer il maletg na sa vesa betg, ma vala vinavant."),
    "Trigger zones in the wide picture": (
        "Auslösezonen im Weitwinkelbild", "Zones de déclenchement dans l’image grand-angle",
        "Zone di attivazione nell’immagine grandangolare", "Zonas da declegnida en il maletg da grond angul"),
    "Trigger zones in the wide picture (browser)": (
        "Auslösezonen im Weitwinkelbild (Browser)", "Zones de déclenchement dans l’image grand-angle (navigateur)",
        "Zone di attivazione nell’immagine grandangolare (browser)", "Zonas da declegnida en il maletg da grond angul (navigatur)"),
    "+ Trigger zone": ("+ Auslösezone", "+ Zone de déclenchement", "+ Zona di attivazione", "+ Zona da declegnida"),
    "Trigger zone": ("Auslösezone", "Zone de déclenchement", "Zona di attivazione", "Zona da declegnida"),
    "Head camera": ("Kopfkamera", "Caméra de la tête", "Telecamera della testa", "Camera dal chau"),
    "z-trig": (
        "Grün: nur was mit den Füssen darin steht, darf den Kopf rufen – nur die angekreuzten Ziele (die leichte KI erkennt Person, Tier, Fahrzeug). Ausserhalb: nur im Protokoll. Keine Auslösezone = das ganze Bild.",
        "Vert : seul ce qui a les pieds dedans peut appeler la tête – seulement les cibles cochées (l’IA légère reconnaît personne, animal, véhicule). Dehors : seulement au journal. Aucune zone = toute l’image.",
        "Verde: solo ciò che ha i piedi dentro può chiamare la testa – solo gli obiettivi selezionati (l’IA leggera riconosce persona, animale, veicolo). Fuori: solo nel registro. Nessuna zona = tutta l’immagine.",
        "Verd: mo quai che stat cun ils pes en la zona dastga clamar il chau – mo las finamiras marcadas (l’IA levgia enconuscha persuna, animal, vehichel). Ordaifer: mo en il protocol. Nagina zona = l’entir maletg."),
    "z-wign": (
        "Rot: die angekreuzten Ziele, deren Füsse darin stehen, rufen den Kopf nie (Strasse, Äste) – gewinnt gegen eine Auslösezone.",
        "Rouge : les cibles cochées dont les pieds sont dedans n’appellent jamais la tête (route, branches) – l’emporte sur une zone de déclenchement.",
        "Rosso: gli obiettivi selezionati con i piedi dentro non chiamano mai la testa (strada, rami) – vince su una zona di attivazione.",
        "Cotschen: las finamiras marcadas cun ils pes en la zona na claman mai il chau (via, roms) – gudogna cunter ina zona da declegnida."),
    "z-whead": (
        "Die Weitwinkel-Kamera dreht mit dem Kopf: Zonen im Bild würden mitwandern – sie gelten nur bei fester Weitwinkel-Kamera (Gehäuse, Unterteil, Mast).",
        "La caméra grand-angle tourne avec la tête : des zones fixées à son image se déplaceraient – elles ne valent qu’avec une caméra grand-angle fixe (boîtier, socle, mât).",
        "La telecamera grandangolare gira con la testa: zone fisse nella sua immagine si sposterebbero – valgono solo con una telecamera grandangolare fissa (custodia, base, palo).",
        "La camera da grond angul sa volva cun il chau: zonas fixadas en ses maletg sa movessan – ellas valan mo cun ina camera da grond angul fixa (chaschetta, part sut, pal)."),
    "No wide camera - choose «Overview camera» under Automatic head movement first.": (
        "Keine Weitwinkel-Kamera – zuerst unter «Automatische Kopfbewegung» die «Übersichtskamera» wählen.",
        "Pas de caméra grand-angle – choisis d’abord la «caméra d’ensemble» sous Mouvement automatique de la tête.",
        "Nessuna telecamera grandangolare – scegli prima la «telecamera panoramica» in Movimento automatico della testa.",
        "Nagina camera da grond angul – tscherna l’emprim la «camera da survista» sut Moviment automatic dal chau."),
    "Guard": ("Wache", "Garde", "Guardia", "Guardia"),
    "AI runs": ("KI-Läufe", "passages IA", "esecuzioni IA", "passadas IA"),
    "head called": ("Kopf gerufen", "tête appelée", "testa chiamata", "chau clamà"),
    "without a person": ("ohne Person", "sans personne", "senza persona", "senza persuna"),
    "outside the zones": ("ausserhalb der Zonen", "hors des zones", "fuori dalle zone", "ordaifer las zonas"),
    "night with heat": ("nachts mit Wärme", "nuit avec chaleur", "notte con calore", "notg cun chalur"),
    "without heat - no alarm": ("ohne Wärme – kein Alarm", "sans chaleur – pas d’alarme", "senza calore – nessun allarme", "senza chalur – nagin alarm"),
    "movement alone": ("Bewegung allein", "mouvement seul", "solo movimento", "mo moviment"),
}
for _k, _v in _HX_WK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_WK_DE = {_k: _v[0] for _k, _v in _HX_WK.items()}
for _k in ("Wide camera", "Ignore zone", "Delete", "Saved", "Save zones"):
    if _k in DE:
        _WK_DE.setdefault(_k, DE[_k])

# ---- the zone editor on the wide picture: /zones?cam=weit (520) ------------------------------------------------------------
_WK_ZP = [
    ('const cv = $("#cv"), g = cv.getContext("2d"), img = new Image();',
     'const WEIT = new URLSearchParams(location.search).get("cam") === "weit";       // 639zw: trigger zones of the wide picture\n'
     'const ZAPI = WEIT ? "/api/weit/zones" : "/api/zones", ZFRAME = WEIT ? "/api/weit/frame.jpg?" : "/api/frame.jpg?";\n'
     'const cv = $("#cv"), g = cv.getContext("2d"), img = new Image();'),
    ('zones = (await (await fetch("/api/zones")).json()).zones || [];',
     '{ const jz = await (await fetch(ZAPI)).json(); zones = jz.zones || []; window.WKHEAD = jz.head || null; }'),
    ('post("/api/zones", {zones: zones, lang: LANG})', 'post(ZAPI, {zones: zones, lang: LANG, head: window.WKHEAD || null})'),
    ('    L.appendChild(r);\n  });\n}\nasync function save()', '    if (WEIT && typeof wkTargets === "function") wkTargets(z, r);\n    L.appendChild(r);\n  });\n}\nasync function save()'),
    ('img.src = "/api/frame.jpg?" + Date.now();', 'img.src = ZFRAME + Date.now();'),
    ('(z.mode === "line" ? [["line", t("Line")]] : [["ignore", t("Ignore zone")]',
     '(z.mode === "line" ? [["line", t("Line")]] : WEIT ? [["trigger", tt("Trigger zone")], ["ignore", t("Ignore zone")]] : [["ignore", t("Ignore zone")]'),
    ('if (z.mode === "ignore" || z.mode === "only") { const k = el("select");', 'if (!WEIT && (z.mode === "ignore" || z.mode === "only")) { const k = el("select");'),
    ('    {                                                    // aufr: «stays on its place» (anchor, 030 / 317) for every zone',
     '    if (!WEIT) {                                         // aufr: «stays on its place» (anchor, 030 / 317) for every zone'),
]
WK_ZONES_JS = r"""
Object.assign(I18N.de, /*WKDE*/{});
Object.assign(I18N, {en: Object.assign(I18N.en || {}, {"z-trig": "Green: only what stands inside with its feet may call the head - only the ticked targets (the light AI knows person, animal, vehicle). Outside: only in the log. No trigger zone = the whole picture.",
  "z-wign": "Red: the ticked targets whose feet are inside never call the head (road, branches) - wins over a trigger zone.",
  "z-wworld": "The wide camera turns with the head: the zones keep their direction (on the ground) when the head turns. What lies outside the picture right now is not shown but still counts."})});
function wkTargets(z, r) {                                 // 639zw: per zone the targets person / animal / vehicle
  if (!Array.isArray(z.targets) || !z.targets.length) z.targets = ["person", "animal", "vehicle"];
  const w = el("div", "mut wk-tg"); w.style.cssText = "grid-column:1/-1;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center";
  w.appendChild(el("span", "", tt("Targets") + ":"));
  [["person", "👤", "Person"], ["animal", "🦌", "Animal"], ["vehicle", "🚗", "Vehicle"]].forEach(([k, ic, lab]) => {
    const l = el("label"), c = el("input"); c.type = "checkbox"; c.checked = z.targets.includes(k);
    c.onclick = e => e.stopPropagation();
    c.onchange = () => { const s = new Set(z.targets); if (c.checked) s.add(k); else if (s.size > 1) s.delete(k); else c.checked = true;
      z.targets = ["person", "animal", "vehicle"].filter(x => s.has(x)); draw(); };
    l.style.cssText = "display:inline-flex;gap:4px;align-items:center;min-height:32px"; l.append(c, ic + " " + tt(lab)); w.appendChild(l); });
  r.appendChild(w);
}
(function () {                                             // 639zw: switch head camera / wide camera, the two kinds on the wide picture
  if (WEIT) { COL.trigger = "63,207,107"; COL.ignore = "255,96,96"; } else COL.trigger = "63,207,107";
  ZNAME.trigger = "Trigger zone";
  const aside = document.querySelector("aside .card"); if (!aside) return;
  const bar = el("div", "btns"); bar.id = "wk-bar"; bar.style.cssText = "margin:0 0 10px"; bar.hidden = !WEIT;
  const lab = (tag, cls, ic, key) => { const e = el(tag, cls, ic); const sp = el("span", "", tt(key)); sp.dataset.i18n = key; e.appendChild(sp); return e; };
  const a1 = lab("a", "btn" + (WEIT ? " sec" : ""), "🎯 ", "Head camera"); a1.href = "/zones";
  const a2 = lab("a", "btn" + (WEIT ? "" : " sec"), "🔭 ", "Wide camera"); a2.href = "/zones?cam=weit";
  bar.append(a1, a2); aside.insertBefore(bar, aside.firstChild);
  fetch("/api/weit/zones").then(r => r.json()).then(j => { if (j.avail || WEIT) bar.hidden = false;
    if (WEIT && !j.avail) $("#hint").textContent = tt("No wide camera - choose «Overview camera» under Automatic head movement first.");
    if (WEIT && j.world) { const n = el("div", "mut", "🧭 " + tt("z-wworld")); n.id = "wk-world"; n.style.marginTop = "8px"; aside.appendChild(n); } }).catch(() => {});
  if (!WEIT) return;
  const _wkA = applyI18n;                                 // LANG is known only after initAppearance: translate then
  applyI18n = function () { _wkA(); document.title = "MoveEye - " + tt("Zones in the wide picture"); };
  const bs = [...aside.querySelectorAll(".btns")].find(d => d.querySelector('button[onclick^="startZone"]'));
  if (bs) { bs.querySelectorAll("button").forEach(b => { if (!/'ignore'/.test(b.getAttribute("onclick") || "")) b.hidden = true; });
    const nb = el("button", "", tt("+ Trigger zone")); nb.dataset.i18n = "+ Trigger zone"; nb.onclick = () => startZone("trigger"); bs.insertBefore(nb, bs.firstChild); }
  const lg = document.querySelector(".legend"); if (lg) { [...lg.children].forEach((d, i) => { if (i) d.hidden = true; });
    const d = el("div"); d.style.marginTop = "4px"; d.innerHTML = '<i style="background:#3fcf6b"></i>'; const s1 = el("span", "", tt("Trigger zone")); s1.dataset.i18n = "Trigger zone"; const s2 = el("span", "", tt("z-trig")); s2.dataset.i18n = "z-trig"; d.append(s1, ": ", s2); lg.insertBefore(d, lg.firstChild);
    const ig = lg.children[1]; if (ig) { const ii = ig.querySelector("i"); if (ii) ii.style.background = "#ff6060";
      const s = ig.querySelector("span[data-i18n=z-ign]"); if (s) { s.dataset.i18n = "z-wign"; s.textContent = tt("z-wign"); } } }
  const how = document.querySelector('[data-i18n="z-how"]'); if (how) how.hidden = true;
  const h = lab("h3", "", "🔭 ", "Zones in the wide picture"); h.style.margin = "0 0 6px"; aside.insertBefore(h, aside.firstChild);
})();
"""
for _a, _b in _WK_ZP:
    if _a in ZONES_PAGE:
        ZONES_PAGE = ZONES_PAGE.replace(_a, _b, 1)
ZONES_PAGE = ZONES_PAGE.replace("/*ALERTS*/\n</script>", WK_ZONES_JS.replace("/*WKDE*/{}", json.dumps(_WK_DE, ensure_ascii=False), 1)
                                + "/*ALERTS*/\n</script>", 1)

# ---- the settings page: a link to the editor and the counters below «The overview camera steers the head» ----------------
WK_WEB_JS = r"""
<script>
Object.assign(I18N.de, /*WKDE2*/{});
(function () {                                             // 639zw: link «Auslösezonen» + counters of the guard (/api/wache)
  let busy = false, last = 0;
  function stat(s) {
    busy = true; last = Date.now();
    fetch("/api/wache?lang=" + LANG).then(r => r.json()).then(j => { busy = false;
      const f = j.fusion || {};
      s.textContent = "🔭 " + t("Guard") + ": " + (j.mode === "motion" ? t("movement alone") + " · " : "") + j.runs + " " + t("AI runs") + (j.runs ? " (Ø " + j.ms + " ms)" : "")
        + " · " + t("head called") + " " + j.calls + "× · " + t("without a target") + " " + j.no_class + "× · " + t("outside the zones") + " " + j.out_zone + "×"
        + (f.on && f.chosen ? " · 🌡 " + t("Thermal camera confirmed") + " " + f.confirmed + "× · " + t("Without heat - not counted") + " " + f.vetoed + "×"
           + (f.fault ? " · " + t("thermal camera faulty") + " " + f.fault + "×" : "") : "");
    }).catch(() => { busy = false; });
  }
  function put() {
    if (busy || document.hidden) return;
    const old = document.getElementById("wk-stat");
    if (old) { if (old.offsetParent && Date.now() - last > 6000) stat(old); return; }
    const row = document.querySelector('#settings [data-key="kopf_ov_on"]');
    if (!row) return;
    const box = el("div", "mut"); box.id = "wk-link"; box.style.cssText = "margin:4px 0 8px";
    const a = el("a", "btn sec", "🗺 " + t("Zones in the wide picture") + " ›"); a.href = "/zones?cam=weit"; a.style.cssText = "display:block;margin:4px 0";
    const s = el("div", "mut"); s.id = "wk-stat"; s.style.fontSize = "13px"; box.append(a, s); row.after(box);
    if (row.offsetParent) stat(s);
  }
  setInterval(put, 1500);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", WK_WEB_JS.replace("/*WKDE2*/{}", json.dumps(_WK_DE, ensure_ascii=False), 1) + "</body>", 1)

# ---- the page «Kameras»: a card «Zonen im Weitwinkelbild» (only when there is a wide camera; self-contained for the redesign) ---
WK_CAMS_JS = r"""
<script>
Object.assign(I18N.de, /*WKDE3*/{});
(function () {                                             // 639zw: the zones of the wide picture from the page Kameras
  function go() {
    if (document.getElementById("wk-cams")) return;
    fetch("/api/weit/zones").then(r => r.ok ? r.json() : null).then(j => {
      if (!j || !j.avail || document.getElementById("wk-cams")) return;
      const main = document.querySelector("main"); if (!main) return;
      const c = el("section", "card"); c.id = "wk-cams"; c.style.marginTop = "16px";
      const h = el("h2", "", "🔭 " + t("Zones in the wide picture")); h.style.cssText = "margin:0 0 6px;font-size:17px";
      const zs = j.zones || [];
      const n = zs.filter(z => z.mode === "trigger").length, m = zs.length - n;
      const p = el("div", "mut", (j.key_name ? t("Mount") + ": " + j.key_name + " · " : "") + (zs.length ? "🟩 " + n + " · 🟥 " + m + (j.world ? " · 🧭 " + t("as directions (turns with the head)") : "") : t("No zones - the whole picture counts.")));
      const a = el("a", "btn sec", "🗺 " + t("Zones in the wide picture") + " ›"); a.href = "/zones?cam=weit"; a.style.cssText = "display:block;margin-top:8px";
      c.append(h, p, a);
      const g = document.getElementById("grid"); if (g && g.nextSibling) main.insertBefore(c, g.nextSibling); else main.appendChild(c);
    }).catch(() => {});
  }
  setTimeout(go, 600);
})();
</script>
"""
CAMS_PAGE = CAMS_PAGE.replace("</body>", WK_CAMS_JS.replace("/*WKDE3*/{}", json.dumps(_WK_DE, ensure_ascii=False), 1) + "</body>", 1)


# ---- the window (Tk): a button to the editor in «Automatic head movement» ---------------------------------------------------
def _wk_tk_build_section(self, sec, sbody, settings_parent=None):
    _wk_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != "Automatic head movement":
        return
    try:
        from tkinter import ttk as _ttk
        _ttk.Button(sbody, text="🔭 " + tr("Zones in the wide picture"), command=lambda: wk_tk_view(self)).pack(fill="x", pady=(8, 0))
        _ttk.Button(sbody, text="🗺 " + tr("Zones in the wide picture (browser)"),
                    command=lambda: self._open_page("/zones?cam=weit")).pack(fill="x", pady=(4, 0))
    except Exception:
        pass


def wk_zone_lines(zs, lang=None):
    """one line per zone: name · include / exclude · targets (window view and self-test)"""
    if not zs:
        return [tr("No zones - the whole picture counts.", lang)]
    nm = {"person": "Person", "animal": "Animal", "vehicle": "Vehicle"}
    return [("🟩 " if z["mode"] == "trigger" else "🟥 ") + z["name"] + " · " + tr("include" if z["mode"] == "trigger" else "exclude", lang)
            + " · " + ", ".join(tr(nm[k], lang) for k in z.get("targets") or WZ_KINDS) for z in zs]


def wk_tk_view(app):
    """the window: the wide picture with its zones (only to look at - editing in the browser), a way back («Close»)"""
    import base64
    win = tk.Toplevel(app.root); win.title("MoveEye – " + tr("Zones in the wide picture"))
    pic = ttk.Label(win); pic.pack(padx=12, pady=(12, 6))
    info = ttk.Label(win, wraplength=560, justify="left"); info.pack(anchor="w", padx=12)
    bf = ttk.Frame(win); bf.pack(fill="x", padx=12, pady=12)
    st = {"n": 0}

    def load():
        if not win.winfo_exists():
            return
        c = wk_cam()
        if c is None:
            info.config(text=tr("No wide camera - choose «Overview camera» under Automatic head movement first.")); return
        key = wz_key(c)
        f = wk_raw(c, 0.0)
        lines = [tr("Mount") + ": " + wz_key_name(key) + (" · " + tr("as directions (turns with the head)") if wz_world(key) else "")]
        lines += wk_zone_lines(wk_zones_active(c))
        if f is None:
            st["n"] += 1
            if st["n"] < 12:
                win.after(400, load)
            lines.insert(0, tr("No picture of the wide camera yet - try again in a moment."))
        else:
            st["n"] = 0
            try:
                im = wk_draw_zones(f, c)
                if im.shape[1] > 560:
                    im = cv2.resize(im, (560, int(im.shape[0] * 560 / im.shape[1])), interpolation=cv2.INTER_AREA)
                ok, buf = cv2.imencode(".png", im)
                if ok:
                    ph_ = tk.PhotoImage(data=base64.b64encode(buf.tobytes()).decode()); pic.config(image=ph_); pic.image = ph_
            except Exception as e:
                lines.insert(0, str(e)[:80])
        info.config(text="\n".join(lines))
    ttk.Button(bf, text="↻ " + tr("New picture"), command=lambda: (st.update(n=0), load())).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="🗺 " + tr("Edit in the browser"), command=lambda: app._open_page("/zones?cam=weit")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="✕ " + tr("Close"), command=win.destroy).pack(side="left", expand=True, fill="x")
    win.after(100, load)


_wk_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _wk_tk_build_section

# ---- the manual: «Weitwinkel einrichten und testen» (all 5 languages) -------------------------------------------------------
_HELP_WK = {
    "de": ('<section id="wide-setup" data-icon="🔭"><h2>Weitwinkel einrichten und testen</h2>'
           '<p>Die Weitwinkel-Kamera ist die <b>Wache</b> (immer an, leichte KI), der Kopf der <b>Detektiv</b> (wird gerufen, verfolgt, '
           'nachts prüft das Wärmebild).</p><ol>'
           '<li><b>Anschliessen:</b> Camera Module 3 Wide NoIR an den zweiten Kamera-Anschluss des Pi 5. Einstellungen → Kameras → '
           '«Zusatzkamera hinzufügen» → die zweite Pi-Kamera; dann unter «Automatische Kopfbewegung» die <i>Übersichtskamera</i> wählen '
           'und «Übersicht lenkt den Kopf» ein.</li>'
           '<li><b>Blickwinkel:</b> Blickwinkel der Zusatzkamera «eigener» 102°; sitzt sie fest im Gehäuse (nicht auf dem Kopf), '
           '«dreht mit dem Kopf» aus.</li>'
           '<li><b>Kalibrieren:</b> Kopf auf etwas richten, das sich im Weitwinkel bewegt (eine Person), dann «Übersicht jetzt '
           'kalibrieren». Prüfen: Ansicht 🔭 zeigt den gelben Rahmen dort, wohin der Kopf schaut.</li>'
           '<li><b>Auslösezonen:</b> Einstellungen → «Auslösezonen im Weitwinkelbild» (oder /zones → 🔭 Weitwinkel): den Bereich '
           'einzeichnen, aus dem der Kopf gerufen werden darf (Zelt, Zugang); Strasse und Äste als Ignorier-Zone. Keine Zone = ganzes Bild.</li>'
           '<li><b>Leichte KI testen (Tag):</b> Schutz «Voll», ausserhalb des Kopfbilds durchs Weitwinkelbild gehen → der Kopf dreht hin '
           '(Protokoll «Overview AI: person seen»). Einen Ast / Tuch im Wind bewegen → der Kopf bleibt («movement without a person»). '
           'Ausserhalb der Auslösezone gehen → nur notiert. Zähler unter dem Schalter (🔭 Wache) bzw. /api/wache.</li>'
           '<li><b>Nacht mit Wärmebild:</b> Wärmebildquelle gewählt und Bild da (🌡). Im Dunkeln vor dem Kopf gehen → Alarm '
           '(«Wärmebild bestätigt»). Ein kaltes Objekt bewegen, das die KI für eine Person hält (Plakat, Puppe) → kein Alarm, Protokoll '
           '«ohne Wärme – nicht gewertet». Ohne Wärmebild bleibt alles wie bisher.</li>'
           '<li><b>Leistung:</b> Unter «Gesundheit» die CPU-Last mit und ohne Bewegung im Weitwinkel vergleichen; bei Bedarf '
           '«Übersichts-KI: höchstens Läufe pro Sekunde» senken. Im Akku-Sparen läuft die Übersichts-KI nicht (Bewegung allein ruft den Kopf).</li>'
           '<li><b>Zonen und Ziele:</b> Grün = Auslösezone (nur hier darf etwas den Kopf rufen), rot = Ignorier-Zone (gewinnt). Pro Zone ankreuzen: 👤 Person, 🦌 Tier, 🚗 Fahrzeug. Die Zonen gelten pro Montage; sitzt die Weitwinkel-Kamera auf dem Kopf, bleiben sie in ihrer Richtung am Boden, auch wenn der Kopf dreht. Ansehen auch im Fenster: «Automatische Kopfbewegung» → «🔭 Zonen im Weitwinkelbild».</li><li><b>Wärmebild-Bestätigung (nur nachts):</b> ein Alarm zählt, wenn das Wärmebild höchstens 4 s vorher oder nachher in derselben Richtung (± 8°) Wärme sah – beides unter «Erkennung» einstellbar. Die Zeitleiste zeigt «Wärmebild bestätigt» oder «ohne Wärme – nicht gewertet». Ist das Wärmebild gestört, zählt der Alarm trotzdem («Wärmebild gestört»). Sabotage, SOS und Alarm von Hand prüft es nie.</li>'
           '</ol></section>\n'),
    "en": ('<section id="wide-setup" data-icon="🔭"><h2>Set up and test the wide camera</h2>'
           '<p>The wide camera is the <b>guard</b> (always on, light AI), the head the <b>detective</b> (called, follows, at night the '
           'thermal camera checks).</p><ol>'
           '<li><b>Connect:</b> Camera Module 3 Wide NoIR to the second camera port of the Pi 5. Settings → Cameras → «Add extra camera» '
           '→ the second Pi camera; then under «Automatic head movement» choose it as <i>overview camera</i> and switch «The overview '
           'camera steers the head» on.</li>'
           '<li><b>Field of view:</b> field of view of the extra camera «own» 102°; fixed in the case (not on the head): «turns with the head» off.</li>'
           '<li><b>Calibrate:</b> point the head at something that moves in the wide picture (a person), then «Calibrate the overview now». '
           'Check: view 🔭 shows the yellow frame where the head looks.</li>'
           '<li><b>Trigger zones:</b> Settings → «Trigger zones in the wide picture» (or /zones → 🔭 Wide camera): draw the area from where '
           'the head may be called (tent, access); road and branches as ignore zone. No zone = the whole picture.</li>'
           '<li><b>Test the light AI (day):</b> protection «Full», walk through the wide picture outside the head picture → the head turns '
           '(log «Overview AI: person seen»). Move a branch / cloth in the wind → the head stays («movement without a person»). Walk outside '
           'the trigger zone → only noted. Counters below the switch (🔭 Guard) or /api/wache.</li>'
           '<li><b>Night with thermal camera:</b> thermal source chosen and a picture there (🌡). Walk in front of the head in the dark → '
           'alarm («Thermal camera confirmed»). Move a cold object the AI takes for a person (poster, doll) → no alarm, log «Without heat - not counted». Without a thermal camera everything stays as before.</li>'
           '<li><b>Load:</b> compare the CPU load under «Health» with and without movement in the wide picture; if needed lower «Overview '
           'AI: at most runs per second». In the battery saver the overview AI does not run (movement alone calls the head).</li>'
           '<li><b>Zones and targets:</b> green = trigger zone (only here may something call the head), red = ignore zone (wins). Per zone tick: 👤 person, 🦌 animal, 🚗 vehicle. The zones count per mount; when the wide camera sits on the head they keep their direction on the ground while the head turns. Also in the window: «Automatic head movement» → «🔭 Zones in the wide picture».</li><li><b>Thermal confirmation (only at night):</b> an alarm counts when the thermal camera saw heat in the same direction (± 8°) at most 4 s before or after – both under «Detection». The timeline shows «Thermal camera confirmed» or «Without heat - not counted». A faulty thermal camera never blocks an alarm. Sabotage, SOS and alarms by hand are never checked.</li>'
           '</ol></section>\n'),
    "fr": ('<section id="wide-setup" data-icon="🔭"><h2>Installer et tester le grand-angle</h2>'
           '<p>La caméra grand-angle est la <b>garde</b> (toujours active, IA légère), la tête le <b>détective</b> (appelée, suit, la nuit '
           'la caméra thermique vérifie).</p><ol>'
           '<li><b>Brancher :</b> Camera Module 3 Wide NoIR sur le deuxième port caméra du Pi 5. Réglages → Caméras → «Ajouter une caméra» '
           '→ la deuxième caméra Pi ; puis sous «Mouvement automatique de la tête» la choisir comme <i>caméra d’ensemble</i> et activer '
           '«La vue d’ensemble dirige la tête».</li>'
           '<li><b>Champ de vision :</b> «propre» 102° ; fixe dans le boîtier (pas sur la tête) : «tourne avec la tête» désactivé.</li>'
           '<li><b>Calibrer :</b> diriger la tête vers quelque chose qui bouge dans le grand-angle (une personne), puis «Calibrer la vue '
           'd’ensemble maintenant». Contrôle : la vue 🔭 montre le cadre jaune là où regarde la tête.</li>'
           '<li><b>Zones de déclenchement :</b> Réglages → «Zones de déclenchement dans l’image grand-angle» (ou /zones → 🔭) : dessiner la '
           'zone d’où la tête peut être appelée (tente, accès) ; route et branches en zone ignorée. Aucune zone = toute l’image.</li>'
           '<li><b>Tester l’IA légère (jour) :</b> protection «Complet», traverser l’image grand-angle hors de l’image de la tête → la tête '
           'tourne. Bouger une branche / un tissu au vent → la tête reste. Hors de la zone → seulement noté. Compteurs sous l’interrupteur '
           '(🔭 Garde) ou /api/wache.</li>'
           '<li><b>Nuit avec caméra thermique :</b> source thermique choisie et image présente (🌡). Marcher devant la tête dans le noir → '
           'alarme. Bouger un objet froid que l’IA prend pour une personne (affiche, poupée) → pas d’alarme, journal «Without heat - not counted». Sans caméra thermique, tout reste comme avant.</li>'
           '<li><b>Charge :</b> comparer la charge CPU sous «Santé» avec et sans mouvement dans le grand-angle ; au besoin réduire «IA de la '
           'vue d’ensemble : au plus passages par seconde». En économie de batterie, l’IA de la vue d’ensemble ne tourne pas.</li>'
           '<li><b>Zones et cibles :</b> vert = zone de déclenchement, rouge = zone ignorée (l’emporte). Par zone cocher : 👤 personne, 🦌 animal, 🚗 véhicule. Les zones valent par montage ; sur la tête elles gardent leur direction au sol quand la tête tourne. Aussi dans la fenêtre : «🔭 Zones dans l’image grand-angle».</li><li><b>Confirmation thermique (la nuit seulement) :</b> une alarme compte si l’image thermique a vu de la chaleur dans la même direction (± 8°) au plus 4 s avant ou après – réglable sous «Détection». La chronologie montre «Image thermique confirmée» ou «sans chaleur – non compté». Une caméra thermique en panne ne bloque jamais une alarme ; sabotage, SOS et alarme manuelle jamais vérifiés.</li>'
           '</ol></section>\n'),
    "it": ('<section id="wide-setup" data-icon="🔭"><h2>Configurare e provare il grandangolo</h2>'
           '<p>La telecamera grandangolare è la <b>guardia</b> (sempre attiva, IA leggera), la testa il <b>detective</b> (chiamata, segue, '
           'di notte controlla la termocamera).</p><ol>'
           '<li><b>Collegare:</b> Camera Module 3 Wide NoIR alla seconda porta telecamera del Pi 5. Impostazioni → Telecamere → «Aggiungi '
           'telecamera» → la seconda telecamera Pi; poi in «Movimento automatico della testa» sceglierla come <i>telecamera panoramica</i> '
           'e attivare «La panoramica guida la testa».</li>'
           '<li><b>Campo visivo:</b> «proprio» 102°; fissa nella custodia (non sulla testa): «gira con la testa» disattivato.</li>'
           '<li><b>Calibrare:</b> puntare la testa su qualcosa che si muove nel grandangolo (una persona), poi «Calibra ora la panoramica». '
           'Verifica: la vista 🔭 mostra il riquadro giallo dove guarda la testa.</li>'
           '<li><b>Zone di attivazione:</b> Impostazioni → «Zone di attivazione nell’immagine grandangolare» (o /zones → 🔭): disegnare '
           'l’area da cui la testa può essere chiamata (tenda, accesso); strada e rami come zona ignorata. Nessuna zona = tutta l’immagine.</li>'
           '<li><b>Provare l’IA leggera (giorno):</b> protezione «Completa», attraversare il grandangolo fuori dall’immagine della testa → la '
           'testa gira. Muovere un ramo / un telo al vento → la testa resta. Fuori dalla zona → solo annotato. Contatori sotto '
           'l’interruttore (🔭 Guardia) o /api/wache.</li>'
           '<li><b>Notte con termocamera:</b> fonte termica scelta e immagine presente (🌡). Camminare davanti alla testa al buio → allarme. '
           'Muovere un oggetto freddo che l’IA scambia per una persona (poster, bambola) → nessun allarme, registro «Without heat - not counted». Senza termocamera tutto resta come prima.</li>'
           '<li><b>Carico:</b> confrontare il carico CPU in «Salute» con e senza movimento nel grandangolo; se serve ridurre «IA panoramica: '
           'al massimo esecuzioni al secondo». Nel risparmio batteria l’IA panoramica non funziona.</li>'
           '<li><b>Zone e obiettivi:</b> verde = zona di attivazione, rosso = zona ignorata (vince). Per zona selezionare: 👤 persona, 🦌 animale, 🚗 veicolo. Le zone valgono per montaggio; sulla testa mantengono la loro direzione a terra quando la testa gira. Anche nella finestra: «🔭 Zone nell’immagine grandangolare».</li><li><b>Conferma termica (solo di notte):</b> un allarme conta se l’immagine termica ha visto calore nella stessa direzione (± 8°) al massimo 4 s prima o dopo – regolabile in «Rilevamento». La cronologia mostra «Immagine termica confermata» o «senza calore – non conteggiato». Una termocamera guasta non blocca mai un allarme; sabotaggio, SOS e allarme manuale mai controllati.</li>'
           '</ol></section>\n'),
    "rm": ('<section id="wide-setup" data-icon="🔭"><h2>Installar e testar il grond angul</h2>'
           '<p>La camera da grond angul è la <b>guardia</b> (adina activa, IA levgia), il chau il <b>detectiv</b> (vegn clamà, suonda, la '
           'notg controllescha il maletg termic).</p><ol>'
           '<li><b>Colliar:</b> Camera Module 3 Wide NoIR vi dal segund attatg da camera dal Pi 5. Parameters → Cameras → «Agiuntar camera» '
           '→ la segunda camera Pi; lura sut «Moviment automatic dal chau» la tscherner sco <i>camera da survista</i> ed activar «La '
           'survista maina il chau».</li>'
           '<li><b>Champ da vista:</b> «agen» 102°; fixa en la chaschetta (betg sin il chau): «sa volva cun il chau» deactivà.</li>'
           '<li><b>Calibrar:</b> drizzar il chau sin insatge che sa mova en il grond angul (ina persuna), lura «Calibrar ussa la survista». '
           'Controlla: la vista 🔭 mussa il rom mellen là nua ch’il chau guarda.</li>'
           '<li><b>Zonas da declegnida:</b> Parameters → «Zonas da declegnida en il maletg da grond angul» (u /zones → 🔭): dissegnar il '
           'sectur dal qual il chau dastga vegnir clamà (tenda, access); via e roms sco zona ignorada. Nagina zona = l’entir maletg.</li>'
           '<li><b>Testar l’IA levgia (di):</b> protecziun «Cumplaina», ir tras il grond angul ordaifer il maletg dal chau → il chau sa '
           'volva. Mover in rom / ina tschiffa en il vent → il chau resta. Ordaifer la zona → mo notà. Dumbraders sut l’interruptur '
           '(🔭 Guardia) u /api/wache.</li>'
           '<li><b>Notg cun maletg termic:</b> funtauna termica tschernida e maletg avant maun (🌡). Ir en il stgir davant il chau → alarm. '
           'Mover in object fraid che l’IA tegna per ina persuna (placat, poppa) → nagin alarm, protocol «Without heat - not counted». '
           'Senza maletg termic resta tut sco fin ussa.</li>'
           '<li><b>Chargia:</b> cumparegliar la chargia CPU sut «Sanadad» cun e senza moviment en il grond angul; sche necessari '
           'reducir «IA da la survista: al pli passadas per secunda». Cun spargnar accu na funcziuna l’IA da la survista betg.</li>'
           '<li><b>Zonas e finamiras:</b> verd = zona da declegnida, cotschen = zona ignorada (gudogna). Per zona marcar: 👤 persuna, 🦌 animal, 🚗 vehichel. Las zonas valan per montascha; sin il chau mantegnan ellas lur direcziun sin il terren, er sch’il chau sa volva. Er en la fanestra: «🔭 Zonas en il maletg da grond angul».</li><li><b>Confermaziun termica (mo la notg):</b> in alarm quinta, sch’il maletg termic ha vis chalur en la medema direcziun (± 8°) al pli 4 s avant u suenter – reglabel sut «Identificaziun». La cronologia mussa «Maletg termic confermà» u «senza chalur – betg quintà». In maletg termic disturbà na bloccha mai in alarm; sabotascha, SOS ed alarm a maun mai controllads.</li>'
           '</ol></section>\n'),
}


def _help_wk(doc, lang):
    if 'id="wide-setup"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_WK[lang] + doc[i:] if i >= 0 else doc


_hp_en_wk = HELP_PAGE.find('<div lang="en">')
if _hp_en_wk > 0:
    HELP_PAGE = _help_wk(HELP_PAGE[:_hp_en_wk], "de") + _help_wk(HELP_PAGE[_hp_en_wk:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_wk(HELP_X[_L], _L)


# ---- self-test: (a) classes, (b) zones, (c) the decision table --------------------------------------------------------------
class _WkCam:
    def __init__(self, boxes, wh=(640, 400), spec="usb:9"):
        self.boxes, self.wh, self.spec = list(boxes), wh, spec
        self.motion, self.streak = bool(boxes), 3


def weit_wache_selftest():
    keep = {k: CFG.get(k) for k in ("kopf_ov_ki_animal", "kopf_ov_ki_vehicle", "kopf_ov_zones", "kopf_ov_zone_sets", "kopf_wild", "use_case",
                                    "mode", "cam_head", "alarm_heat_fusion", "kopf_ov", "kopf_ov_offset", "thermal_source", "fusion_window_s",
                                    "fusion_tol_deg", "heat_fus_mig", "heat_fus_note", "heat_fus_seen", "news_seen_web", "news_seen_tk", "sim_on")}
    keep_wk = dict(WK); keep_fus = dict(FUS); keep_heat = list(HEAT)
    sv = {k: globals()[k] for k in ("log_event", "_alarm_gate_639zw", "fus_thermal_ok", "fus_night", "fus_sample", "fus_cover", "servo_pos",
                                    "cam_fov", "wz_head", "_timeline_build_639zw", "save_settings")}
    try:
        globals().update(log_event=lambda *a, **k: None, save_settings=lambda *a, **k: None)
        CFG.update(kopf_ov="", kopf_ov_offset=0.0, sim_on=False)
        # (a) classes: all three from the factory (Besitzer 14.11.2026), switches, wildlife = animals
        assert DEFAULTS["kopf_ov_ki_animal"] is True and DEFAULTS["kopf_ov_ki_vehicle"] is True and DEFAULTS["kopf_ov_ki"] is True
        assert wk_kind(1) == "person" and wk_kind(18) == "animal" and wk_kind(OWN_AI_ANIMAL_ID) == "animal"
        assert wk_kind(3) == "vehicle" and wk_kind(4) == "vehicle" and wk_kind(2) == "vehicle" and wk_kind(62) == "other"
        CFG.update(kopf_ov_ki_animal=False, kopf_ov_ki_vehicle=False, kopf_wild="off", cam_head={}, kopf_ov_zones=[], kopf_ov_zone_sets={})
        assert wk_classes() == {"person"}
        CFG["kopf_ov_ki_vehicle"] = True; assert wk_classes() == {"person", "vehicle"}
        CFG.update(kopf_ov_ki_vehicle=False, kopf_wild="on"); assert "animal" in wk_classes()
        CFG["kopf_wild"] = "off"
        now = time.time()
        c = _WkCam([(400, 150, 40, 100)])                                  # one moving box right of the middle
        WK.update(hits=[], ran_t=now)
        assert weit_pick(c, now, "motion") is not None, "movement alone (AI off / dark): as before"
        assert weit_pick(c, now, "ai") is None, "AI looked, nothing found: the head stays"
        nb = (0.62, 0.37, 0.07, 0.25); az = kopf_ov_deg(0.655)
        WK["hits"] = [(now, "animal", 0.8, nb, az, wk_zone_ok(0.655, 0.6, [], "animal"))]
        assert weit_pick(c, now, "ai") is None, "an animal does not call the head (switch off)"
        CFG["kopf_ov_ki_animal"] = True
        WK["hits"] = [(now, "animal", 0.8, nb, az, wk_zone_ok(0.655, 0.6, [], "animal"))]
        assert weit_pick(c, now, "ai") is not None, "animal with the switch on"
        WK["hits"] = [(now, "person", 0.7, nb, az, True)]
        t = weit_pick(c, now, "ai")
        assert t is not None and abs(t[0] - 0.655) < 0.01, t
        WK["hits"] = [(now - 10.0, "person", 0.7, nb, az, True)]
        assert weit_pick(c, now, "ai") is None, "an old hit does not count"
        # (b) zones: foot point, include = only there (its targets), exclude = never there (its targets, wins), none = all
        zs = wk_zones_clean([{"mode": "trigger", "points": [[0.0, 0.5], [0.5, 0.5], [0.5, 1.0], [0.0, 1.0]]},
                             {"mode": "ignore", "points": [[0.0, 0.8], [0.2, 0.8], [0.2, 1.0], [0.0, 1.0]]},
                             {"mode": "privacy", "points": [[0.9, 0.9], [1, 0.9], [1, 1]]}])
        assert [z["mode"] for z in zs] == ["trigger", "ignore", "ignore"], zs
        assert all(z["targets"] == list(WZ_KINDS) for z in zs), "a zone without targets: all three"
        zs = zs[:2]
        assert wk_zone_ok(0.3, 0.7, zs) and not wk_zone_ok(0.8, 0.7, zs) and not wk_zone_ok(0.1, 0.9, zs) and wk_zone_ok(0.8, 0.7, [])
        zt = wk_zones_clean([{"mode": "trigger", "targets": ["vehicle"], "points": [[0, 0], [1, 0], [1, 1], [0, 1]]},
                             {"mode": "ignore", "targets": ["person"], "points": [[0, 0], [0.3, 0], [0.3, 1], [0, 1]]}])
        assert wk_zone_ok(0.5, 0.5, zt, "vehicle") and not wk_zone_ok(0.5, 0.5, zt, "person"), "include only vehicles"
        assert not wk_zone_ok(0.1, 0.5, zt, None) and wk_zone_ok(0.1, 0.5, zt, "vehicle") and wk_zone_ok(0.1, 0.5, zt, "any"), "exclude persons only"
        CFG["kopf_ov_zones"] = zs
        WK["hits"] = []
        assert weit_pick(_WkCam([(400, 150, 40, 100)]), now, "motion") is None, "foot outside the trigger zone: only noted"
        assert weit_pick(_WkCam([(100, 150, 40, 140)]), now, "motion") is not None, "foot inside the trigger zone"
        # (b) per mount: fixed keeps the old list, the head gets its own list as directions
        CFG.update(cam_head={"usb:9": True}, kopf_ov="usb:9")
        hc = _WkCam([(400, 150, 40, 100)])
        assert wz_key(hc) == "head" and wz_world("head") and wz_raw("head") == [], "head: no zones of the fixed mount"
        assert weit_pick(hc, now, "motion") is not None, "head mount without own zones: the whole picture"
        g = wz_geom(hc)
        for x, y in ((0.1, 0.2), (0.5, 0.5), (0.93, 0.8)):
            px_ = wz_pic(hc, *wz_dir(hc, x, y, (20.0, 5.0), g), (20.0, 5.0), g)
            assert abs(px_[0] - x) < 1e-6 and abs(px_[1] - y) < 1e-6, (x, y, px_)
        globals()["wz_head"] = lambda: (0.0, 0.0)
        key, saved = wk_zones_save(hc, [{"mode": "trigger", "points": [[0.6, 0.5], [0.8, 0.5], [0.8, 1.0], [0.6, 1.0]], "targets": ["person"]}], [0.0, 0.0])
        assert key == "head" and saved and saved[0].get("ang") and "points" not in saved[0], saved
        assert CFG["kopf_ov_zones"] == zs, "the fixed list stays"
        assert wk_zone_ok(0.7, 0.8, None, "person", hc) and not wk_zone_ok(0.3, 0.8, None, "person", hc)
        sh = 30.0 / g["fh"]
        globals()["wz_head"] = lambda: (30.0, 0.0)                    # the head turned 30° right: the zone stays on the ground
        assert wk_zone_ok(0.7 - sh, 0.8, None, "person", hc) and not wk_zone_ok(0.7, 0.8, None, "person", hc), "zone keeps its direction"
        v = wk_zones_view(hc)
        assert v["world"] and abs(v["zones"][0]["points"][0][0] - (0.6 - sh)) < 1e-3, v
        globals()["wz_head"] = lambda: (190.0, 0.0)                   # far round: wraps (rear mount / 360° servos)
        assert not wk_zone_ok(0.7, 0.8, None, "person", hc)
        CFG.update(cam_head={}, kopf_ov="", kopf_ov_zones=[], kopf_ov_zone_sets={})
        assert wk_crop((600, 380, 40, 20), 640, 400)[0] + wk_crop((600, 380, 40, 20), 640, 400)[2] <= 640
        im = wk_draw_zones(np.zeros((120, 200, 3), np.uint8), _WkCam([]), zs)
        assert im.shape == (120, 200, 3) and int(im[100, 70, 1]) > int(im[100, 70, 2]) and int(im[115, 8, 2]) > int(im[115, 8, 1]) and int(im[40, 150, 1]) == 0, "green include / red exclude"
        assert len(wk_zone_lines(zs, "de")) == 2 and wk_zone_lines([], "de")[0].startswith("Keine Zonen")
        # (c) pure parts: the decision table, warm spots, direction + time matching
        for night in (False, True):
            for th in (False, True):
                for heat in (False, True):
                    d = fus_decide(True, th, night, [heat])
                    want = "pass" if not (night and th) else ("confirmed" if heat else "veto")
                    assert d == want, (night, th, heat, d)
        f = np.full((62, 80), 10.0, np.float32); f[20:40, 30:40] = 31.0          # °C: a warm body
        sp = fus_spots(f, True, 3.0)
        assert len(sp) == 1 and abs(sp[0][0] - 30 / 80.0) < 0.02 and abs(sp[0][2] - 10 / 80.0) < 0.02, sp
        g8 = np.full((62, 80), 60, np.uint8); g8[20:40, 30:40] = 230
        assert len(fus_spots(g8, False)) == 1 and fus_spots(np.full((62, 80), 60, np.uint8), False) == []
        H_ = [(now - 2.0, 10.0, 14.0, -5.0, 5.0)]
        assert fus_match((11.0, 13.0, -3.0, 3.0), H_, now, 4.0, 8.0) == 0.0
        assert fus_match((20.0, 22.0, -3.0, 3.0), H_, now, 4.0, 8.0) == 6.0, "6° beside: inside the tolerance"
        assert fus_match((30.0, 33.0, -3.0, 3.0), H_, now, 4.0, 8.0) is None, "another direction"
        assert fus_match((11.0, 13.0, -3.0, 3.0), H_, now + 3.0, 4.0, 8.0) is None, "too old"
        assert fus_match((11.0, 13.0, 30.0, 40.0), H_, now, 4.0, 8.0) is None, "far above"
        assert fus_match((-179.0, -177.0, 0.0, 2.0), [(now, 178.0, 182.0, -1.0, 3.0)], now, 4.0, 8.0) == 0.0, "behind: wraps"
        # (c) the gate: day as before, faulty = fail open, heat = confirmed, no heat = waits, then «not counted»
        class _W:
            _proc_size = (480, 270)
        fr_ = np.zeros((270, 480, 3), np.uint8); P = [(220, 50, 40, 120, 0.9)]
        st = {"night": True, "ok": True}
        globals().update(_alarm_gate_639zw=lambda w, frame, persons, now: persons, fus_thermal_ok=lambda: st["ok"],
                         fus_night=lambda: st["night"], fus_sample=lambda now: None, fus_cover=lambda: (0.0, 1.0),
                         servo_pos=lambda: (50.0, 50.0), cam_fov=lambda: (66.0, 41.0))
        CFG.update(alarm_heat_fusion=True, thermal_source="sim:thermal", fusion_window_s=4.0, fusion_tol_deg=8.0)
        FUS.update(latch=0.0, veto_t=0.0, pend_t=0.0, pend_last=0.0, fault_t=0.0, last=[]); HEAT.clear()
        pd = fus_box_dir((220 / 480.0, 50 / 270.0, 40 / 480.0, 120 / 270.0), 50.0, 50.0, 66.0, 41.0)
        st["night"] = False
        assert alarm_gate(_W(), fr_, P, now) == P, "day: as before (no heat needed)"
        st["night"] = True; CFG["alarm_heat_fusion"] = False
        assert alarm_gate(_W(), fr_, P, now) == P, "switch off: as before"
        CFG.update(alarm_heat_fusion=True, thermal_source="")
        assert alarm_gate(_W(), fr_, P, now) == P, "no thermal camera: as before"
        CFG["thermal_source"] = "sim:thermal"; st["ok"] = False; f0 = FUS["fault"]
        assert alarm_gate(_W(), fr_, P, now) == P and FUS["fault"] == f0 + 1, "thermal camera faulty: fail open"
        st["ok"] = True
        HEAT.append((now - 1.0, pd[0] + 3.0, pd[1] + 3.0, pd[2], pd[3]))
        c0 = FUS["confirmed"]
        assert alarm_gate(_W(), fr_, P, now) == P and FUS["confirmed"] == c0 + 1 and FUS["latch"] > now, "heat in the direction: alarm"
        assert FUS["last"][0]["what"] == "confirmed"
        FUS.update(latch=0.0); HEAT.clear(); HEAT.append((now - 1.0, pd[0] + 40.0, pd[1] + 40.0, pd[2], pd[3]))
        v0 = FUS["vetoed"]
        assert alarm_gate(_W(), fr_, P, now) == [] and FUS["vetoed"] == v0, "no heat yet: waits (no veto at once)"
        assert alarm_gate(_W(), fr_, P, now + 2.0) == [] and FUS["vetoed"] == v0
        assert alarm_gate(_W(), fr_, P, now + 4.5) == [] and FUS["vetoed"] == v0 + 1, "no heat within the window: not counted"
        assert FUS["last"][0]["what"] == "veto"
        HEAT.append((now + 5.0, pd[0], pd[1], pd[2], pd[3]))
        assert alarm_gate(_W(), fr_, P, now + 5.2) == P, "heat comes later: the alarm counts then"
        FUS.update(latch=0.0, pend_t=0.0); HEAT.clear()
        assert alarm_gate(_W(), fr_, [], now + 30.0) == [], "nobody: nothing"
        import inspect
        assert "alarm_gate(self, frame, persons, now)" in inspect.getsource(MotionWatch.handle_recording), "only person alarms pass the gate"
        for fn in (push_alert, siren_alarm):
            assert "alarm_gate" not in inspect.getsource(fn), fn.__name__ + ": sabotage / SOS / by hand never pass the gate"
        # update: once on for existing devices, with a one-time notice (web and window)
        assert DEFAULTS["heat_fus_mig"] is True, "a new device needs no migration"
        assert heat_confirm_migrate({"alarm_heat_fusion": False, "armed": True}) and CFG["alarm_heat_fusion"] is True
        assert CFG["heat_fus_note"] == "pending" and heat_confirm_migrate({"heat_fus_mig": True}) == []
        CFG.update(news_seen_web=APP_VERSION, news_seen_tk=APP_VERSION)
        sw = news_state("web", "de")
        assert sw["show"] and "nachts" in sw["items"][0]["t"].lower() and sw["items"][0]["href"].endswith("alarm_heat_fusion"), sw["items"][:1]
        news_seen("web")
        assert not news_state("web", "de")["show"] and news_state("tk", "de")["show"], "web seen, the window not yet"
        # the timeline shows the decisions in the language of the page
        globals()["_timeline_build_639zw"] = lambda d, m, l: {"items": [{"type": "log", "kind": "heat", "text": FUS_TXT["veto"] + " (night)", "alarm": True},
                                                                       {"type": "log", "kind": "person", "text": FUS_TXT["confirmed"] + " - alarm counts", "alarm": True}]}
        it = timeline_build(None, "night", "de")["items"]
        assert it[0]["text"].startswith("❄ ohne Wärme – nicht gewertet") and it[0]["alarm"] is False and "Wärmebild bestätigt" in it[1]["text"], it
        assert log_important("heat", FUS_TXT["veto"] + " x")
        # pages: the zone editor knows the wide picture, translations in all languages
        for need in ("const WEIT = ", "fetch(ZAPI)", "post(ZAPI,", "ZFRAME + Date.now()", 'startZone("trigger")', '"Auslösezone"', "function wkTargets",
                     "wkTargets(z, r)", "window.WKHEAD", '"63,207,107"'):
            assert need in ZONES_PAGE, "zone editor: missing " + need
        assert "wk-link" in WEB_PAGE and 'id = "wk-cams"' in CAMS_PAGE
        for k, v in _HX_WK.items():
            assert len(v) == 4 and all(v) and k in DE and all(k in TRX[L] for L in ("fr", "it", "rm")), k
        for k in FUS_TXT.values():
            assert k in _HX_WK, k
        assert HELP_PAGE.count('<section id="wide-setup"') == 2 and all('id="wide-setup"' in (HELP_X.get(L) or 'id="wide-setup"') for L in ("fr", "it", "rm"))
        assert any(x[1] == "alarm_heat_fusion" for x in TOGGLES) and any(x[1] == "kopf_ov_ki_fps" for x in SLIDERS)
        assert any(x[1] == "fusion_window_s" for x in SLIDERS) and any(x[1] == "fusion_tol_deg" for x in SLIDERS)
        assert DEFAULTS["alarm_heat_fusion"] is True and DEFAULTS["fusion_window_s"] == 4.0 and DEFAULTS["fusion_tol_deg"] == 8.0
        assert not any(role_allows(r, "/api/weit/zones", "POST", {}) for r in ("view", "friend", "family", "kid")), "only the administrator (and «settings») edits"
        assert role_allows("custom", "/api/weit/zones", "POST", {}, ("settings",)) and role_allows("family", "/api/weit/zones", "GET", {})
        assert not role_allows("custom", "/api/weit/frame.jpg", "GET", {}, ("arm",)) and role_allows("custom", "/api/weit/frame.jpg", "GET", {}, ("live",)), "the wide picture needs «live» (3.89 review)"
    finally:
        globals().update(sv)
        CFG.update(keep); WK.clear(); WK.update(keep_wk); FUS.clear(); FUS.update(keep_fus); HEAT.clear(); HEAT.extend(keep_heat)
    return "Weitwinkel-Wache: classes, zones per mount (head = directions), thermal confirmation by direction + time window, update notice"


SELFTEST_EXTRA.append(("Wide camera as guard: light AI classes, trigger zones, night thermal fusion (639zw)", weit_wache_selftest))
