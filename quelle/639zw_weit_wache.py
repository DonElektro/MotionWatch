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
for _k, _v in {"kopf_ov_ki": True, "kopf_ov_ki_animal": False, "kopf_ov_ki_vehicle": False, "kopf_ov_ki_dark": True,
               "kopf_ov_ki_fps": 1.0, "kopf_ov_zones": [], "alarm_heat_fusion": True, "fusion_heat_c": 3.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

WK = {"runs": 0, "ms": 0.0, "last_run": 0.0, "ran_t": 0.0, "hits": [], "calls": 0, "no_class": 0, "out_zone": 0, "busy": 0,
      "nc_t": 0.0, "oz_t": 0.0, "call_log": 0.0, "head_log": False, "since": time.time()}
FUS = {"vetoed": 0, "confirmed": 0, "latch": 0.0, "veto_t": 0.0, "ok_log": 0.0, "miss_log": 0.0, "since": time.time()}
WK_MAX_ZONES = 8
WK_HIT_S = 4.0                       # a hit of the light AI counts this long for the head (it walks on meanwhile)
WK_DARK_BRIGHT = 30                  # mean brightness of the wide picture below this = infrared night (like AI_FULL_MIN_BRIGHT, 418z)
WK_VEHICLES = set(VEHICLE_LABELS) | {"bicycle", "vehicle"}
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


# ---- (b) trigger zones --------------------------------------------------------------------------------------------------
def wk_zones_clean(lst):
    out = []
    for z in (lst if isinstance(lst, list) else [])[:WK_MAX_ZONES]:
        if not isinstance(z, dict):
            continue
        mode = "trigger" if z.get("mode") == "trigger" else "ignore"
        c = _clean_zone(dict(z, mode="only" if mode == "trigger" else "ignore", anchor=False, src=None), len(out))
        if c:
            out.append({"id": c["id"], "name": c["name"], "mode": mode, "points": c["points"]})
    return out


def wk_zone_ok(nx, ny, zones=None):
    """may movement whose foot point is (nx, ny) of the wide picture call the head? (pure: zones given, else the setting)"""
    zs = wk_zones_clean(CFG.get("kopf_ov_zones")) if zones is None else zones
    if not zs:
        return True
    if any(z["mode"] == "ignore" and point_in_poly(nx, ny, z["points"]) for z in zs):
        return False
    trig = [z for z in zs if z["mode"] == "trigger"]
    return (not trig) or any(point_in_poly(nx, ny, z["points"]) for z in trig)


def wk_zones_active(c):
    """the zones count only for a fixed wide camera (on the head they would wander with the picture)"""
    zs = wk_zones_clean(CFG.get("kopf_ov_zones"))
    if not zs:
        return []
    try:
        head = cam_on_head(getattr(c, "spec", ""))
    except Exception:
        head = False
    if head:
        if not WK["head_log"]:
            WK["head_log"] = True
            log_event("servo", "Overview: the wide camera turns with the head - its trigger zones do not count")
        return []
    WK["head_log"] = False
    return zs


def wk_foot(b, W, H):
    return (b[0] + b[2] / 2.0) / float(W), (b[1] + b[3] * 0.92) / float(H)


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
    for t_, kind, conf, nb in WK["hits"]:                    # the last hits in the picture (green), for the live view
        if now - t_ < 1.5:
            p1 = (int(nb[0] * W), int(nb[1] * H)); p2 = (int((nb[0] + nb[2]) * W), int((nb[1] + nb[3]) * H))
            cv2.rectangle(frame, p1, p2, (60, 220, 60), 2)
            cv2.putText(frame, f"{kind} {conf:.2f}", (p1[0], max(40, p1[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 220, 60), 1, cv2.LINE_AA)
    if not c.motion or not c.boxes or wk_mode(c) != "ai" or now - WK["last_run"] < wk_gap():
        return
    zs = wk_zones_active(c)
    cand = [b for b in c.boxes if b[2] * b[3] <= 0.3 * W * H and wk_zone_ok(*wk_foot(b, W, H), zones=zs)]
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
    hits = [(now, k, cf, ((x0 + b[0]) / W, (y0 + b[1]) / H, b[2] / W, b[3] / H)) for k, cf, b in found if k != "other"]
    WK["hits"] = (hits + [h for h in WK["hits"] if now - h[0] < WK_HIT_S])[:12]


def weit_pick(c, now, mode=None):
    """162 _kopf_ov_tick: (cx, size) of what may call the head now, or None. Zones first (outside = only noted), then the
    light AI (a hit of a wanted kind; movement without one = the head stays). mode None = wk_mode(c)."""
    raw = kopf_ov_target(c)                                   # moving, 2+ pictures, not half the picture (light, wind)
    if raw is None:
        return None
    W, H = c.wh
    zs = wk_zones_active(c)
    inz = [b for b in c.boxes if b[2] * b[3] <= 0.3 * W * H and wk_zone_ok(*wk_foot(b, W, H), zones=zs)]
    if not inz:
        if now - WK["oz_t"] > 10.0:
            WK["out_zone"] += 1
            if now - WK["oz_t"] > 60.0:
                log_event("servo", "Overview: movement outside the trigger zones - only noted")
        WK["oz_t"] = now
        return None
    mode = mode or wk_mode(c)
    if mode != "ai":
        x, y, w, h = max(inz, key=lambda b: b[2] * b[3])
        return ((x + w / 2.0) / W, w * h / float(W * H))
    want = wk_classes()
    hits = [h for h in WK["hits"] if now - h[0] < WK_HIT_S and h[1] in want
            and wk_zone_ok(h[3][0] + h[3][2] / 2.0, h[3][1] + h[3][3] * 0.92, zones=zs)]
    if hits:
        t_, kind, conf, nb = max(hits, key=lambda h: (h[0], h[2]))
        WK["calls"] += 1
        if now - WK["call_log"] > 20.0:
            WK["call_log"] = now
            log_event("servo", f"Overview AI: {kind} seen ({conf:.2f}) - the head looks")
        return (nb[0] + nb[2] / 2.0, nb[2] * nb[3])
    if now - WK["ran_t"] < 3.0:                               # the AI looked at this movement: nothing that may call the head
        if now - WK["nc_t"] > 10.0:
            WK["no_class"] += 1
            if now - WK["nc_t"] > 60.0:
                log_event("servo", "Overview: movement without a person - the head stays (light AI)")
        WK["nc_t"] = now
    return None


# ---- (c) thermal fusion at night -----------------------------------------------------------------------------------------
def fus_thermal_ok():
    """a thermal source is chosen and gives pictures right now"""
    th = THERMAL
    return (bool(CFG.get("thermal_source")) and th is not None and getattr(th, "frame", None) is not None
            and time.time() - float(getattr(th, "t", 0.0) or 0.0) < 3.0 and STATE.get("thermal") == "connected")


def fus_night():
    try:
        return bool(is_dark() or STATE.get("lowlight"))
    except Exception:
        return bool(STATE.get("lowlight"))


def fus_heat_in(f, nb, temps, boxes=(), dc=3.0):
    """pure: is there heat at the normalised box nb in the (already aligned) thermal picture f? temps = f is in °C.
    True / False, None = cannot tell (empty region)"""
    for b in boxes or ():                                    # a warm moving body of THERMAL.detect inside the (bigger) box
        cx, cy = b[0] + b[2] / 2.0, b[1] + b[3] / 2.0
        if nb[0] - 0.1 * nb[2] <= cx <= nb[0] + 1.1 * nb[2] and nb[1] - 0.1 * nb[3] <= cy <= nb[1] + 1.1 * nb[3]:
            return True
    if f is None:
        return None
    g = f.astype(np.float32) if temps else ThermalCam.to_gray8(f).astype(np.float32)
    if g.ndim == 3:
        g = g.mean(axis=2)
    H, W = g.shape[:2]
    x0 = max(0, int((nb[0] - 0.1 * nb[2]) * W)); y0 = max(0, int((nb[1] - 0.1 * nb[3]) * H))
    x1 = min(W, max(x0 + 1, int(math.ceil((nb[0] + 1.1 * nb[2]) * W)))); y1 = min(H, max(y0 + 1, int(math.ceil((nb[1] + 1.1 * nb[3]) * H))))
    reg = g[y0:y1, x0:x1]
    if reg.size < 1:
        return None
    hot, med = float(np.percentile(reg, 95)), float(np.median(g))
    need = float(dc) if temps else max(25.0, 0.2 * (255.0 - med))
    return hot >= med + need


def fus_heat(nb):
    th = THERMAL
    try:
        fr = th.frame
        f = th.crop(fr)
        boxes = th.boxes if time.time() - float(getattr(th, "det_t", 0.0) or 0.0) < 2.0 else ()
        return fus_heat_in(f, nb, fr.dtype != np.uint8, boxes, float(CFG.get("fusion_heat_c") or 3.0))
    except Exception:
        return None


def fus_decide(on, thermal_ok, night, heats):
    """the decision table: "pass" (as before) / "confirmed" (heat at the person) / "veto" (night, thermal ok, no heat)"""
    if not on or not thermal_ok or not night:
        return "pass"
    if any(h is True for h in heats):
        return "confirmed"
    if not heats or all(h is None for h in heats):
        return "pass"
    return "veto"


_alarm_gate_639zw = alarm_gate


def alarm_gate(w, frame, persons, now):                   # + 639zw: at night a person alarm needs heat (thermal fusion)
    res = _alarm_gate_639zw(w, frame, persons, now)
    if not res or not CFG.get("alarm_heat_fusion") or now < FUS["latch"]:
        return res
    ok, night = fus_thermal_ok(), fus_night()
    if not ok:
        if night and CFG.get("thermal_source") and now - FUS["miss_log"] > 600:
            FUS["miss_log"] = now
            log_event("person", "Thermal check: the thermal camera gives no picture - person alarms as before (without heat)")
        return res
    if not night:
        return res
    pw, ph = getattr(w, "_proc_size", None) or (frame.shape[1], frame.shape[0])
    heats = [fus_heat((b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph)) for b in res[:6]]
    d = fus_decide(True, ok, night, heats)
    if d == "pass":
        return res
    if d == "confirmed":
        FUS["confirmed"] += 1; FUS["latch"] = now + 10.0
        if now - FUS["ok_log"] > 30:
            FUS["ok_log"] = now
            log_event("person", "Thermal check: person with heat - alarm")
        return res
    if now - FUS["veto_t"] > 10.0:
        FUS["vetoed"] += 1
        log_event("person", "Person without heat - no alarm (night, thermal camera)")
    FUS["veto_t"] = now
    return []


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


def wache_state():
    """/api/wache: what the overview and the night thermal check did since the start (measurable)"""
    c = kopf_ov_cam()
    ai, why = wk_ai()
    return {"ov": bool(c), "mode": wk_mode(c) if c else "", "ai": not why, "why": why, "classes": sorted(wk_classes()),
            "zones": len(wk_zones_clean(CFG.get("kopf_ov_zones"))), "zones_on": bool(c is not None and wk_zones_active(c)),
            "runs": WK["runs"], "ms": round(WK["ms"], 1), "calls": WK["calls"], "no_class": WK["no_class"],
            "out_zone": WK["out_zone"], "busy": WK["busy"], "since": int(WK["since"]),
            "fusion": {"on": bool(CFG.get("alarm_heat_fusion")), "thermal": fus_thermal_ok(), "night": fus_night(),
                       "confirmed": FUS["confirmed"], "vetoed": FUS["vetoed"]}}


# ---- web: /api/wache, /api/weit/zones, /api/weit/frame.jpg ------------------------------------------------------------
def wk_cam():
    c = kopf_ov_cam()
    if c is None:
        try:
            c = view3_wide_cam()
        except Exception:
            c = None
    return c


_smalltv_routes_639zw = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zw
    _smalltv_routes_639zw(app, reply, body)
    from flask import Response, request

    @app.route("/api/wache")
    def wk_api_state():
        return reply(wache_state())

    @app.route("/api/weit/zones", methods=["GET", "POST"])
    def wk_api_zones():
        c = wk_cam()
        if request.method == "POST":
            d = body()
            if not isinstance(d.get("zones"), list):
                return reply({"ok": False, "error": tr_err("invalid zones", norm_lang(d.get("lang")))}, 400)
            CFG["kopf_ov_zones"] = wk_zones_clean(d.get("zones"))
            save_settings(); log_event("sys", f"Trigger zones of the overview updated ({len(CFG['kopf_ov_zones'])})")
            return reply({"ok": True, "error": None})
        try:
            head = bool(c is not None and cam_on_head(c.spec))
        except Exception:
            head = False
        return reply({"zones": wk_zones_clean(CFG.get("kopf_ov_zones")), "avail": c is not None, "n": getattr(c, "idx", None),
                      "on_head": head, "ov": bool(kopf_ov_cam())})

    @app.route("/api/weit/frame.jpg")
    def wk_api_frame():
        c = wk_cam()
        if c is None:
            return Response("no wide camera", 404)
        if time.time() > c.raw_until:
            c.raw = None
        c.raw_until = time.time() + 15
        for _ in range(25):
            if c.raw is not None:
                break
            time.sleep(0.1)
        f = c.raw
        if f is None:
            return Response("no frame yet", 503)
        if f.shape[1] > 960:
            f = cv2.resize(f, (960, int(f.shape[0] * 960 / f.shape[1])), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


# ---- settings (web + window: the same lists) ------------------------------------------------------------------------------
_WK_TG = [
    ("kopf_ov_ki", "Overview: light AI on the wide picture - only a person calls the head (animals / vehicles: switches below)"),
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
                           "At night with a thermal camera: a person alarm only with heat (AI + thermal camera) - no heat source = no alarm, only a log line"))

# ---- translations (English key: Deutsch, Français, Italiano, Rumantsch) ----------------------------------------------------
_HX_WK = {
    "Overview: light AI on the wide picture - only a person calls the head (animals / vehicles: switches below)": (
        "Übersicht: leichte KI im Weitwinkelbild – nur eine Person ruft den Kopf (Tiere / Fahrzeuge: Schalter darunter)",
        "Vue d’ensemble : IA légère sur l’image grand-angle – seule une personne appelle la tête (animaux / véhicules : interrupteurs ci-dessous)",
        "Panoramica: IA leggera sull’immagine grandangolare – solo una persona chiama la testa (animali / veicoli: interruttori sotto)",
        "Survista: IA levgia en il maletg da grond angul – mo ina persuna clama il chau (animals / vehichels: interruptuors sutvart)"),
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
    "At night with a thermal camera: a person alarm only with heat (AI + thermal camera) - no heat source = no alarm, only a log line": (
        "Nachts mit Wärmebild: Personen-Alarm nur mit Wärme (KI + Wärmebild) – ohne Wärmequelle kein Alarm, nur ein Eintrag im Protokoll",
        "La nuit avec caméra thermique : alarme personne seulement avec chaleur (IA + image thermique) – sans source de chaleur pas d’alarme, seulement une ligne au journal",
        "Di notte con termocamera: allarme persona solo con calore (IA + immagine termica) – senza fonte di calore nessun allarme, solo una riga nel registro",
        "La notg cun maletg termic: alarm da persuna mo cun chalur (IA + maletg termic) – senza funtauna da chalur nagin alarm, mo ina lingia en il protocol"),
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
        "Nur Bewegung, deren Füsse darin stehen, darf den Kopf rufen (was es ist, entscheidet die leichte KI). Ausserhalb: nur im Protokoll notiert. Keine Auslösezone = das ganze Bild.",
        "Seul un mouvement dont les pieds sont dedans peut appeler la tête (l’IA légère décide de quoi il s’agit). Dehors : seulement noté au journal. Aucune zone = toute l’image.",
        "Solo un movimento con i piedi dentro può chiamare la testa (l’IA leggera decide che cos’è). Fuori: solo annotato nel registro. Nessuna zona = tutta l’immagine.",
        "Mo in moviment cun ils pes en la zona dastga clamar il chau (tge ch’i è, decida l’IA levgia). Ordaifer: mo notà en il protocol. Nagina zona = l’entir maletg."),
    "z-wign": (
        "Bewegung, deren Füsse darin stehen, ruft den Kopf nie (Strasse, Äste).",
        "Un mouvement dont les pieds sont dedans n’appelle jamais la tête (route, branches).",
        "Un movimento con i piedi dentro non chiama mai la testa (strada, rami).",
        "In moviment cun ils pes en la zona na clama mai il chau (via, roms)."),
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
    ('zones = (await (await fetch("/api/zones")).json()).zones || [];', 'zones = (await (await fetch(ZAPI)).json()).zones || [];'),
    ('post("/api/zones", {zones: zones, lang: LANG})', 'post(ZAPI, {zones: zones, lang: LANG})'),
    ('img.src = "/api/frame.jpg?" + Date.now();', 'img.src = ZFRAME + Date.now();'),
    ('(z.mode === "line" ? [["line", t("Line")]] : [["ignore", t("Ignore zone")]',
     '(z.mode === "line" ? [["line", t("Line")]] : WEIT ? [["trigger", tt("Trigger zone")], ["ignore", t("Ignore zone")]] : [["ignore", t("Ignore zone")]'),
    ('if (z.mode === "ignore" || z.mode === "only") { const k = el("select");', 'if (!WEIT && (z.mode === "ignore" || z.mode === "only")) { const k = el("select");'),
    ('    {                                                    // aufr: «stays on its place» (anchor, 030 / 317) for every zone',
     '    if (!WEIT) {                                         // aufr: «stays on its place» (anchor, 030 / 317) for every zone'),
]
WK_ZONES_JS = r"""
Object.assign(I18N.de, /*WKDE*/{});
Object.assign(I18N, {en: Object.assign(I18N.en || {}, {"z-trig": "Only movement whose feet are inside may call the head (the light AI decides what it is). Outside: only noted in the log. No trigger zone = the whole picture.",
  "z-wign": "Movement whose feet are inside never calls the head (road, branches).",
  "z-whead": "The wide camera turns with the head: zones fixed to its picture would move - they count only with a fixed wide camera (case, base, mast)."})});
(function () {                                             // 639zw: switch head camera / wide camera, the two kinds on the wide picture
  COL.trigger = "255,96,96"; ZNAME.trigger = "Trigger zone";
  const aside = document.querySelector("aside .card"); if (!aside) return;
  const bar = el("div", "btns"); bar.id = "wk-bar"; bar.style.cssText = "margin:0 0 10px"; bar.hidden = !WEIT;
  const lab = (tag, cls, ic, key) => { const e = el(tag, cls, ic); const sp = el("span", "", tt(key)); sp.dataset.i18n = key; e.appendChild(sp); return e; };
  const a1 = lab("a", "btn" + (WEIT ? " sec" : ""), "🎯 ", "Head camera"); a1.href = "/zones";
  const a2 = lab("a", "btn" + (WEIT ? "" : " sec"), "🔭 ", "Wide camera"); a2.href = "/zones?cam=weit";
  bar.append(a1, a2); aside.insertBefore(bar, aside.firstChild);
  fetch("/api/weit/zones").then(r => r.json()).then(j => { if (j.avail || WEIT) bar.hidden = false;
    if (WEIT && !j.avail) $("#hint").textContent = tt("No wide camera - choose «Overview camera» under Automatic head movement first.");
    if (WEIT && j.on_head) { const n = el("div", "err", "⚠ " + tt("z-whead")); aside.appendChild(n); } }).catch(() => {});
  if (!WEIT) return;
  const _wkA = applyI18n;                                 // LANG is known only after initAppearance: translate then
  applyI18n = function () { _wkA(); document.title = "MoveEye - " + tt("Trigger zones in the wide picture"); };
  const bs = [...aside.querySelectorAll(".btns")].find(d => d.querySelector('button[onclick^="startZone"]'));
  if (bs) { bs.querySelectorAll("button").forEach(b => { if (!/'ignore'/.test(b.getAttribute("onclick") || "")) b.hidden = true; });
    const nb = el("button", "", tt("+ Trigger zone")); nb.dataset.i18n = "+ Trigger zone"; nb.onclick = () => startZone("trigger"); bs.insertBefore(nb, bs.firstChild); }
  const lg = document.querySelector(".legend"); if (lg) { [...lg.children].forEach((d, i) => { if (i) d.hidden = true; });
    const d = el("div"); d.style.marginTop = "4px"; d.innerHTML = '<i style="background:#ff6060"></i>'; const s1 = el("span", "", tt("Trigger zone")); s1.dataset.i18n = "Trigger zone"; const s2 = el("span", "", tt("z-trig")); s2.dataset.i18n = "z-trig"; d.append(s1, ": ", s2); lg.insertBefore(d, lg.firstChild);
    const ig = lg.children[1]; if (ig) { const s = ig.querySelector("span[data-i18n=z-ign]"); if (s) { s.dataset.i18n = "z-wign"; s.textContent = tt("z-wign"); } } }
  const how = document.querySelector('[data-i18n="z-how"]'); if (how) how.hidden = true;
  const h = lab("h3", "", "🔭 ", "Trigger zones in the wide picture"); h.style.margin = "0 0 6px"; aside.insertBefore(h, aside.firstChild);
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
    fetch("/api/wache").then(r => r.json()).then(j => { busy = false;
      const f = j.fusion || {};
      s.textContent = "🔭 " + t("Guard") + ": " + (j.mode === "motion" ? t("movement alone") + " · " : "") + j.runs + " " + t("AI runs") + (j.runs ? " (Ø " + j.ms + " ms)" : "")
        + " · " + t("head called") + " " + j.calls + "× · " + t("without a person") + " " + j.no_class + "× · " + t("outside the zones") + " " + j.out_zone + "×"
        + (f.on ? " · 🌡 " + t("night with heat") + " " + f.confirmed + "× · " + t("without heat - no alarm") + " " + f.vetoed + "×" : "");
    }).catch(() => { busy = false; });
  }
  function put() {
    if (busy || document.hidden) return;
    const old = document.getElementById("wk-stat");
    if (old) { if (old.offsetParent && Date.now() - last > 6000) stat(old); return; }
    const row = document.querySelector('#settings [data-key="kopf_ov_on"]');
    if (!row) return;
    const box = el("div", "mut"); box.id = "wk-link"; box.style.cssText = "margin:4px 0 8px";
    const a = el("a", "btn sec", "🗺 " + t("Trigger zones in the wide picture") + " ›"); a.href = "/zones?cam=weit"; a.style.cssText = "display:block;margin:4px 0";
    const s = el("div", "mut"); s.id = "wk-stat"; s.style.fontSize = "13px"; box.append(a, s); row.after(box);
    if (row.offsetParent) stat(s);
  }
  setInterval(put, 1500);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", WK_WEB_JS.replace("/*WKDE2*/{}", json.dumps(_WK_DE, ensure_ascii=False), 1) + "</body>", 1)


# ---- the window (Tk): a button to the editor in «Automatic head movement» ---------------------------------------------------
def _wk_tk_build_section(self, sec, sbody, settings_parent=None):
    _wk_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != "Automatic head movement":
        return
    try:
        from tkinter import ttk as _ttk
        _ttk.Button(sbody, text="🗺 " + tr("Trigger zones in the wide picture (browser)"),
                    command=lambda: self._open_page("/zones?cam=weit")).pack(fill="x", pady=(8, 0))
    except Exception:
        pass


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
           '(«person with heat»). Ein kaltes Objekt bewegen, das die KI für eine Person hält (Plakat, Puppe) → kein Alarm, Protokoll '
           '«Person without heat - no alarm». Ohne Wärmebild bleibt alles wie bisher.</li>'
           '<li><b>Leistung:</b> Unter «Gesundheit» die CPU-Last mit und ohne Bewegung im Weitwinkel vergleichen; bei Bedarf '
           '«Übersichts-KI: höchstens Läufe pro Sekunde» senken. Im Akku-Sparen läuft die Übersichts-KI nicht (Bewegung allein ruft den Kopf).</li>'
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
           'alarm («person with heat»). Move a cold object the AI takes for a person (poster, doll) → no alarm, log «Person without heat - '
           'no alarm». Without a thermal camera everything stays as before.</li>'
           '<li><b>Load:</b> compare the CPU load under «Health» with and without movement in the wide picture; if needed lower «Overview '
           'AI: at most runs per second». In the battery saver the overview AI does not run (movement alone calls the head).</li>'
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
           'alarme. Bouger un objet froid que l’IA prend pour une personne (affiche, poupée) → pas d’alarme, journal «Person without heat - '
           'no alarm». Sans caméra thermique, tout reste comme avant.</li>'
           '<li><b>Charge :</b> comparer la charge CPU sous «Santé» avec et sans mouvement dans le grand-angle ; au besoin réduire «IA de la '
           'vue d’ensemble : au plus passages par seconde». En économie de batterie, l’IA de la vue d’ensemble ne tourne pas.</li>'
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
           'Muovere un oggetto freddo che l’IA scambia per una persona (poster, bambola) → nessun allarme, registro «Person without heat - '
           'no alarm». Senza termocamera tutto resta come prima.</li>'
           '<li><b>Carico:</b> confrontare il carico CPU in «Salute» con e senza movimento nel grandangolo; se serve ridurre «IA panoramica: '
           'al massimo esecuzioni al secondo». Nel risparmio batteria l’IA panoramica non funziona.</li>'
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
           'Mover in object fraid che l’IA tegna per ina persuna (placat, poppa) → nagin alarm, protocol «Person without heat - no alarm». '
           'Senza maletg termic resta tut sco fin ussa.</li>'
           '<li><b>Chargia:</b> cumparegliar la chargia CPU sut «Sanadad» cun e senza moviment en il grond angul; sche necessari '
           'reducir «IA da la survista: al pli passadas per secunda». Cun spargnar accu na funcziuna l’IA da la survista betg.</li>'
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
    keep = {k: CFG.get(k) for k in ("kopf_ov_ki_animal", "kopf_ov_ki_vehicle", "kopf_ov_zones", "kopf_wild", "use_case", "mode",
                                    "cam_head", "alarm_heat_fusion")}
    keep_wk = dict(WK); keep_fus = dict(FUS)
    _ls = log_event
    try:
        globals()["log_event"] = lambda *a, **k: None
        # (a) classes: person always, animal / vehicle by switch, wildlife = animals
        assert wk_kind(1) == "person" and wk_kind(18) == "animal" and wk_kind(OWN_AI_ANIMAL_ID) == "animal"
        assert wk_kind(3) == "vehicle" and wk_kind(8) == "vehicle" and wk_kind(2) == "vehicle" and wk_kind(62) == "other"
        CFG.update(kopf_ov_ki_animal=False, kopf_ov_ki_vehicle=False, kopf_wild="off", cam_head={}, kopf_ov_zones=[])
        assert wk_classes() == {"person"}
        CFG["kopf_ov_ki_vehicle"] = True; assert wk_classes() == {"person", "vehicle"}
        CFG.update(kopf_ov_ki_vehicle=False, kopf_wild="on"); assert "animal" in wk_classes()
        CFG["kopf_wild"] = "off"
        now = time.time()
        c = _WkCam([(400, 150, 40, 100)])                                  # one moving box right of the middle
        WK.update(hits=[], ran_t=now)
        assert weit_pick(c, now, "motion") is not None, "movement alone (AI off / dark): as before"
        assert weit_pick(c, now, "ai") is None, "AI looked, nothing found: the head stays"
        WK["hits"] = [(now, "animal", 0.8, (0.62, 0.37, 0.07, 0.25))]
        assert weit_pick(c, now, "ai") is None, "an animal does not call the head (switch off)"
        CFG["kopf_ov_ki_animal"] = True
        assert weit_pick(c, now, "ai") is not None, "animal with the switch on"
        CFG["kopf_ov_ki_animal"] = False
        WK["hits"] = [(now, "person", 0.7, (0.62, 0.37, 0.07, 0.25))]
        t = weit_pick(c, now, "ai")
        assert t is not None and abs(t[0] - 0.655) < 0.01, t
        WK["hits"] = [(now - 10.0, "person", 0.7, (0.62, 0.37, 0.07, 0.25))]
        assert weit_pick(c, now, "ai") is None, "an old hit does not count"
        # (b) zones: foot point, trigger = only there, ignore = never there, none = all
        zs = wk_zones_clean([{"mode": "trigger", "points": [[0.0, 0.5], [0.5, 0.5], [0.5, 1.0], [0.0, 1.0]]},
                             {"mode": "ignore", "points": [[0.0, 0.8], [0.2, 0.8], [0.2, 1.0], [0.0, 1.0]]},
                             {"mode": "privacy", "points": [[0.9, 0.9], [1, 0.9], [1, 1]]}])
        assert [z["mode"] for z in zs] == ["trigger", "ignore", "ignore"], zs
        zs = zs[:2]
        assert wk_zone_ok(0.3, 0.7, zs) and not wk_zone_ok(0.8, 0.7, zs) and not wk_zone_ok(0.1, 0.9, zs) and wk_zone_ok(0.8, 0.7, [])
        CFG["kopf_ov_zones"] = zs
        WK["hits"] = []
        assert weit_pick(_WkCam([(400, 150, 40, 100)]), now, "motion") is None, "foot outside the trigger zone: only noted"
        assert weit_pick(_WkCam([(100, 150, 40, 140)]), now, "motion") is not None, "foot inside the trigger zone"
        CFG["cam_head"] = {"usb:9": True}
        assert weit_pick(_WkCam([(400, 150, 40, 100)]), now, "motion") is not None, "on the head the zones do not count"
        CFG.update(cam_head={}, kopf_ov_zones=[])
        assert wk_crop((600, 380, 40, 20), 640, 400)[0] + wk_crop((600, 380, 40, 20), 640, 400)[2] <= 640
        # (c) the decision table: day / night x thermal yes / no x heat yes / no
        for night in (False, True):
            for th in (False, True):
                for heat in (False, True):
                    d = fus_decide(True, th, night, [heat])
                    want = "pass" if not (night and th) else ("confirmed" if heat else "veto")
                    assert d == want, (night, th, heat, d)
        assert fus_decide(False, True, True, [False]) == "pass", "switch off: as before"
        assert fus_decide(True, True, True, [None]) == "pass", "cannot tell: as before"
        f = np.full((62, 80), 10.0, np.float32); f[20:40, 30:40] = 31.0          # °C: a warm body
        assert fus_heat_in(f, (0.35, 0.3, 0.15, 0.35), True) is True and fus_heat_in(f, (0.0, 0.0, 0.2, 0.2), True) is False
        g = np.full((62, 80), 60, np.uint8); g[20:40, 30:40] = 230                 # 8 bit: bright = warm
        assert fus_heat_in(g, (0.35, 0.3, 0.15, 0.35), False) is True and fus_heat_in(g, (0.8, 0.7, 0.15, 0.2), False) is False
        assert fus_heat_in(None, (0.1, 0.1, 0.2, 0.2), True, [(0.12, 0.15, 0.05, 0.1)]) is True, "a warm moving body in the box"
        # (c) the wrapper: night, thermal ok, no heat -> no alarm; without a thermal picture -> as before
        class _W:
            _proc_size = (480, 270)
        fr_ = np.zeros((270, 480, 3), np.uint8); P = [(100, 50, 40, 120, 0.9)]
        sv = {k: globals()[k] for k in ("_alarm_gate_639zw", "fus_thermal_ok", "fus_night", "fus_heat")}
        try:
            globals()["_alarm_gate_639zw"] = lambda w, frame, persons, now: persons
            CFG["alarm_heat_fusion"] = True; FUS.update(latch=0.0, veto_t=0.0)
            globals().update(fus_thermal_ok=lambda: True, fus_night=lambda: True, fus_heat=lambda nb: False)
            v0 = FUS["vetoed"]
            assert alarm_gate(_W(), fr_, P, now) == [] and FUS["vetoed"] == v0 + 1, "night without heat: no alarm"
            globals()["fus_heat"] = lambda nb: True
            assert alarm_gate(_W(), fr_, P, now) == P and FUS["latch"] > now, "night with heat: alarm"
            FUS["latch"] = 0.0; globals()["fus_heat"] = lambda nb: False; globals()["fus_night"] = lambda: False
            assert alarm_gate(_W(), fr_, P, now) == P, "day: as before"
            globals()["fus_night"] = lambda: True; globals()["fus_thermal_ok"] = lambda: False
            assert alarm_gate(_W(), fr_, P, now) == P, "no thermal picture: as before"
        finally:
            globals().update(sv)
        # pages: the zone editor knows the wide picture, translations in all languages
        for need in ("const WEIT = ", "fetch(ZAPI)", "post(ZAPI,", "ZFRAME + Date.now()", 'startZone("trigger")', '"Auslösezone"'):
            assert need in ZONES_PAGE, "zone editor: missing " + need
        assert 'id="wk-link"' in WEB_PAGE or "wk-link" in WEB_PAGE
        for k, v in _HX_WK.items():
            assert len(v) == 4 and all(v) and k in DE and all(k in TRX[L] for L in ("fr", "it", "rm")), k
        assert HELP_PAGE.count('<section id="wide-setup"') == 2 and all('id="wide-setup"' in (HELP_X.get(L) or 'id="wide-setup"') for L in ("fr", "it", "rm"))
        assert any(x[1] == "alarm_heat_fusion" for x in TOGGLES) and any(x[1] == "kopf_ov_ki_fps" for x in SLIDERS)
        assert DEFAULTS["alarm_heat_fusion"] is True and DEFAULTS["kopf_ov_ki"] is True and DEFAULTS["kopf_ov_ki_animal"] is False
    finally:
        globals()["log_event"] = _ls
        CFG.update(keep); WK.clear(); WK.update(keep_wk); FUS.clear(); FUS.update(keep_fus)
    return "Weitwinkel-Wache: classes, trigger zones, thermal fusion table (8 cases), zone editor, manual"


SELFTEST_EXTRA.append(("Wide camera as guard: light AI classes, trigger zones, night thermal fusion (639zw)", weit_wache_selftest))
