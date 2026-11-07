#@ MoveEye – Teil 639zz: Objekte und Profile – Erkennungsprofile (🏕️ Nacht am Zelt, 🌳 Garten tagsüber, 🏠 Hausüberwachung, 🔋 Akku sparen; von Hand, per Zeitplan oder bei tiefem Akku), Wildtiere mit Namen («🦊 Fuchs beim Zelt»), Fahrzeuge je Art (melden / nur protokollieren / ignorieren), Dinge (Paket vor der Tür, liegen gelassen, Gegenstand weg). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «Objekte und Profile» (vom Besitzer freigegeben). Ein Erkennungsprofil sagt, WAS gemeldet wird und WIE VIEL die KI
# rechnet - es schreibt keine Einstellungen um (kein Konflikt mit den Modi 130, den Zeitplänen 030 und dem Akku-Sparen 105):
#   * die Wirkung kommt über kleine Haken, die nur sparen können: prof_proc_width (kleineres Arbeitsbild, 410),
#     AIDetector.detect (KI nur bei Bewegung / seltener, Wrapper unten), wk_ai (keine leichte KI im Weitwinkel im Akku-Profil),
#     own_ai_paths (das grössere eigene Modell nur in Haus / Garten und nur mit ai_model_big - ab Werk aus, erst nach einer
#     Messung am Pi), die Dinge-Prüfung (einmal pro Minute) nur in Haus / Garten.
#   * welches Profil gilt: Akku unter prof_batt_pct (wenn prof_batt_on) > ein laufender Zeitplan mit «Erkennungsprofil» >
#     det_profile (von Hand: Knopf auf der Seite / im Fenster). Wählt man während eines Zeitplans von Hand, gilt die eigene Wahl
#     bis der Zeitplan wechselt (wie bei den Schaltern der Zeitpläne, sched_user_changed).
#   * ohne Profil (det_profile "", ab Werk) verhält sich MoveEye wie bisher: Tiere werden nur protokolliert (neu: mit Namen),
#     Fahrzeuge je nach veh_* (ab Werk «nur protokollieren»), keine Dinge-Prüfung, keine neue Push-Nachricht.
# Pushes: obj_push_text() baut die Wörter («🦊 Fuchs beim Zelt», «📦 Paket vor der Tür») - auch für andere Teile (Helfer F).
# Ehrlich: SSD MobileNet (COCO) kennt Fuchs, Reh, Dachs, Igel, Wildschwein nicht (ein Fuchs ist oft «dog»); Namen kommen vom
# Tierarten-Modell (180, ImageNet: red fox, badger, hedgehog, wild boar - kein Reh) oder vom eigenen Modell, wenn es mit den
# Wildtier-Klassen trainiert ist (ki_training/trainieren.py --klassen wildtiere). Ein Paket kennt COCO auch nicht: die
# Dinge-Prüfung findet es als «neuer Gegenstand» (Bildvergleich mit dem Hintergrund) - Selbsttest objprof_selftest.
# ----------------------------------------------------------------------------
_OP_DEF = {"det_profile": "", "prof_batt_on": False, "prof_batt_pct": 20,
           "veh_car": "log", "veh_moto": "log", "veh_bike": "log", "veh_truck": "log",
           "obj_pkg_on": True, "obj_pkg_min": 2, "obj_pkg_zone": "", "obj_left_on": True, "obj_left_min": 10,
           "obj_gone_on": True, "obj_remember_min": 30, "obj_remembered": [], "ai_model_big": False}
for _k, _v in _OP_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v)))
    DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))

_OPS = "Detection profile"
PROF_ORDER = ("night", "garden", "home", "battery")
# per profile: what is reported (animals: none / big / all; vehicles: the veh_* choice applies; things: which checks) and what
# the AI may cost (ai_k: the AI only every k-th time, motion_only: the AI only after movement, proc_max: the working picture at
# most this wide, big: the bigger own model allowed). Persons are always reported (the person alarm itself is unchanged).
PROFILES = {
    "night": {"icon": "🏕️", "name": "Night at the tent", "info": "Persons and large animals. The AI only looks when something moves - saves a lot.",
              "animals": "big", "vehicles": False, "things": (), "ai_k": 1, "motion_only": True, "proc_max": 0, "big": False},
    "garden": {"icon": "🌳", "name": "Garden by day", "info": "Persons and all animals with their names. Remembered things (bike, cool box) are watched.",
               "animals": "all", "vehicles": False, "things": ("gone",), "ai_k": 1, "motion_only": False, "proc_max": 0, "big": True},
    "home": {"icon": "🏠", "name": "House watch", "info": "Persons, vehicles and parcels: a parcel at the door, things left behind or gone.",
             "animals": "none", "vehicles": True, "things": ("package", "left", "gone"), "ai_k": 1, "motion_only": False, "proc_max": 0, "big": True},
    "battery": {"icon": "🔋", "name": "Save battery", "info": "Only persons. The AI looks seldom, small pictures - for long nights on the battery.",
                "animals": "none", "vehicles": False, "things": (), "ai_k": 4, "motion_only": False, "proc_max": 320, "big": False},
}
PROF_NONE = {"icon": "⚙️", "name": "Own settings", "info": "No profile: MoveEye works as set up (as before).",
             "animals": "none", "vehicles": True, "things": (), "ai_k": 1, "motion_only": False, "proc_max": 0, "big": False}
PROF = {"eff": "", "why": "manual", "batt": False, "over": None, "sched": None, "seen_manual": None, "tick_t": 0.0,
        "since": time.time(), "ai_skipped": 0, "ai_runs": 0, "checks": 0, "check_t": 0.0, "check_ms": 0, "last_events": deque(maxlen=12),
        "big_on": False, "paused": ""}
PROF_MOTION_HOLD = 3.0          # s: after movement the AI keeps looking this long (profile «Night»)
PROF_MOTION_FRAC = 0.0015       # share of moving pixels that counts as movement
OBJ_CHECK_S = 60.0              # the things check: about once a minute
OBJ_GONE_MISSES = 2             # a remembered thing is «gone» after two checks in a row without it
OBJ_PUSH_GAP = 600.0            # the same message (kind + name + place) at most every 10 minutes
VEH_POLICIES = ("report", "log", "ignore")
VEH_TYPES = {"car": ("veh_car", "🚗", "Car"), "moto": ("veh_moto", "🏍️", "Motorbike"), "bike": ("veh_bike", "🚲", "Bicycle"),
             "truck": ("veh_truck", "🚚", "Van / truck")}
VEH_OF_LABEL = {"car": "car", "motorcycle": "moto", "bicycle": "bike", "truck": "truck", "bus": "truck", "van": "truck"}


# ---- names of the animals --------------------------------------------------------------------------------------------------
# canonical key -> (symbol, English name = translation key). The five wildlife species of the package first.
WILD = {"fox": ("🦊", "Fox"), "roe deer": ("🦌", "Roe deer"), "badger": ("🦡", "Badger"), "hedgehog": ("🦔", "Hedgehog"),
        "wild boar": ("🐗", "Wild boar"), "red deer": ("🦌", "Red deer"), "hare": ("🐇", "Hare"), "marten": ("🐾", "Marten"),
        "wolf": ("🐺", "Wolf"), "lynx": ("🐈", "Lynx"), "squirrel": ("🐿️", "Squirrel"), "chamois": ("🐐", "Chamois"),
        "ibex": ("🐐", "Ibex"), "cat": ("🐈", "Cat"), "dog": ("🐕", "Dog"), "bird": ("🐦", "Bird"), "horse": ("🐎", "Horse"),
        "sheep": ("🐑", "Sheep"), "cow": ("🐄", "Cow"), "bear": ("🐻", "Bear"), "elephant": ("🐘", "Elephant"),
        "zebra": ("🦓", "Zebra"), "giraffe": ("🦒", "Giraffe"), "animal": ("🐾", "Animal")}
WILD_FIVE = ("fox", "roe deer", "badger", "hedgehog", "wild boar")
# large animals (profile «Night at the tent»): what matters at a tent at night. Fox and badger count too - they raid food at
# camp sites (decision to confirm with the owner); a generic «animal» counts when its box is big (WILD_BIG_H).
WILD_BIG = {"fox", "roe deer", "badger", "wild boar", "red deer", "wolf", "lynx", "bear", "horse", "cow", "sheep", "chamois", "ibex",
            "elephant", "zebra", "giraffe"}
WILD_BIG_H = 0.15
# own model (195): its class names get their own ids (before: all wildlife = 92 «animal»), so the name reaches the push
WILD_IDS = {"fox": 93, "roe deer": 94, "badger": 95, "hedgehog": 96, "wild boar": 97, "red deer": 98, "hare": 99, "marten": 100,
            "wolf": 101, "lynx": 102, "squirrel": 103, "chamois": 104, "ibex": 105}
WILD_ALIAS = {"deer": "roe deer", "roe": "roe deer", "reh": "roe deer", "boar": "wild boar", "rabbit": "hare", "fuchs": "fox",
              "dachs": "badger", "igel": "hedgehog", "wildschwein": "wild boar"}
for _n, _i in WILD_IDS.items():
    COCO_LABELS.setdefault(_i, _n)
    ANIMALS.add(_n)
# words in the label of the species model (180, «red fox;Fuchs», ImageNet «porcupine, hedgehog») -> canonical key; order counts
_WILD_WORDS = (("roe", "roe deer"), ("reh", "roe deer"), ("boar", "wild boar"), ("wildschwein", "wild boar"), ("wild pig", "wild boar"),
               ("badger", "badger"), ("dachs", "badger"), ("hedgehog", "hedgehog"), ("igel", "hedgehog"), ("fox", "fox"), ("fuchs", "fox"),
               ("red deer", "red deer"), ("stag", "red deer"), ("hirsch", "red deer"), ("deer", "roe deer"), ("hare", "hare"), ("rabbit", "hare"),
               ("marten", "marten"), ("marder", "marten"), ("wolf", "wolf"), ("lynx", "lynx"), ("luchs", "lynx"), ("squirrel", "squirrel"),
               ("chamois", "chamois"), ("gämse", "chamois"), ("ibex", "ibex"), ("steinbock", "ibex"), ("cat", "cat"), ("katze", "cat"),
               ("dog", "dog"), ("hund", "dog"), ("bird", "bird"), ("vogel", "bird"))


def wild_canon(label):
    """a label (COCO, own model, species model) -> canonical key of WILD (or "" if it is no animal we know)"""
    s = str(label or "").strip().lower()
    if not s:
        return ""
    s = WILD_ALIAS.get(s, s)
    if s in WILD:
        return s
    for w, k in _WILD_WORDS:
        if w in s:
            return k
    return "animal" if s in ANIMALS else ""


def wild_name(label, box=None, species=None, lang=None):
    """(key, symbol, name in the language) of an animal: the species model wins over the first AI (a fox is often «dog»)"""
    k = wild_canon(species[0]) if species else ""
    if not k or k == "animal":
        k = wild_canon(label) or "animal"
    ic, en = WILD.get(k, WILD["animal"])
    return k, ic, tr(en, lang)


_own_ai_classmap_op_base = own_ai_classmap


def own_ai_classmap(names):                               # + 639zz: wildlife classes of the own model keep their name
    out = list(_own_ai_classmap_op_base(names))
    for i, nm in enumerate(names):
        k = WILD_ALIAS.get(str(nm).strip().lower(), str(nm).strip().lower())
        if k in WILD_IDS and (out[i] is None or out[i][0] == OWN_AI_ANIMAL_ID):
            out[i] = (WILD_IDS[k], False)
    return out


# ---- the words of the messages (also for other parts: obj_push_text) ------------------------------------------------------
THING_NAMES = {"backpack": ("🎒", "Backpack"), "handbag": ("👜", "Bag"), "suitcase": ("🧳", "Suitcase"), "umbrella": ("☂️", "Umbrella"),
               "bicycle": ("🚲", "Bicycle"), "motorcycle": ("🏍️", "Motorbike"), "chair": ("🪑", "Chair"), "bench": ("🪑", "Bench"),
               "skateboard": ("🛹", "Skateboard"), "surfboard": ("🏄", "Surfboard"), "skis": ("🎿", "Skis"), "sports ball": ("⚽", "Ball"),
               "object": ("📦", "Object"), "package": ("📦", "Parcel")}
THING_LABELS = set(THING_NAMES) - {"object", "package"}
PKG_LABELS = {"object", "suitcase"}                        # what may be a parcel (COCO has no parcel: a new unknown object)
BAG_LABELS = {"backpack", "handbag", "suitcase", "umbrella"}
GONE_LABELS = {"bicycle", "motorcycle", "suitcase", "backpack", "handbag", "chair", "umbrella", "skateboard", "surfboard", "skis", "sports ball", "object"}
# German: the zone name with the right little word («beim Zelt», «vor der Tür»); unknown names: «bei «Name»»
_ZONE_DE = {"zelt": "beim Zelt", "vorzelt": "im Vorzelt", "tür": "vor der Tür", "haustür": "vor der Haustür", "türe": "vor der Türe",
            "eingang": "beim Eingang", "einfahrt": "bei der Einfahrt", "garage": "bei der Garage", "garten": "im Garten",
            "terrasse": "auf der Terrasse", "sitzplatz": "beim Sitzplatz", "weg": "auf dem Weg", "strasse": "auf der Strasse",
            "auto": "beim Auto", "velo": "beim Velo", "wohnmobil": "beim Wohnmobil", "wohnwagen": "beim Wohnwagen", "feuerstelle": "bei der Feuerstelle",
            "grill": "beim Grill", "hof": "im Hof", "parkplatz": "auf dem Parkplatz", "tor": "beim Tor", "briefkasten": "beim Briefkasten",
            "hecke": "bei der Hecke", "wiese": "auf der Wiese", "waldrand": "am Waldrand", "lager": "beim Lager", "biwak": "beim Biwak"}
_ZONE_PREP = {"de": ("beim ", "bei ", "vor ", "am ", "im ", "an ", "auf ", "hinter ", "neben ", "unter "),
              "en": ("at ", "near ", "by ", "in ", "on ", "behind ", "in front of "), "fr": ("près ", "devant ", "à ", "au ", "dans ", "sur "),
              "it": ("presso ", "davanti ", "vicino ", "al ", "alla ", "nel ", "sul "), "rm": ("tar ", "davant ", "en ", "sin ", "sper ")}
_ZONE_FMT = {"en": "at {z}", "fr": "près de {z}", "it": "presso {z}", "rm": "tar {z}"}


def obj_zone_phrase(zone, lang=None):
    """«beim Zelt» / «at Tent» - the name of a zone as a place in a sentence ("" without a zone)"""
    z = str(zone or "").strip()
    if not z:
        return ""
    L = norm_lang(lang) if lang else cur_lang()
    if z.lower().startswith(_ZONE_PREP.get(L, ()) or ("at ",)):
        return z                                          # the name is a place already («beim Zelt», «vor der Tür»)
    if L == "de":
        return _ZONE_DE.get(z.lower()) or ("bei «" + z + "»")
    return _ZONE_FMT.get(L, "at {z}").format(z=z)


def obj_push_text(kind, key="", zone="", lang=None):
    """(symbol, title, what) of a message of this package - kind: animal (key = canonical animal), vehicle (car / moto / bike /
    truck), package, left (key = thing label), gone (key = thing label). Other parts (e.g. 639zy, Helfer F) may call it."""
    L = norm_lang(lang) if lang else cur_lang()
    where = obj_zone_phrase(zone, L)
    if kind == "animal":
        _k, ic, nm = wild_name(key, lang=L)
        title = (nm + " " + where) if where else trf("{x} seen", L, x=nm)
    elif kind == "vehicle":
        _ck, ic, en = VEH_TYPES.get(key, VEH_TYPES["car"])
        nm = tr(en, L)
        title = (nm + " " + where) if where else trf("{x} seen", L, x=nm)
    elif kind == "package":
        ic, nm = "📦", tr("Parcel", L)
        title = (nm + " " + where) if where else tr("Parcel put down", L)
    else:
        ic, en = THING_NAMES.get(key, THING_NAMES["object"])
        nm = tr(en, L)
        if kind == "left":
            title = trf("{x} left behind {where}", L, x=nm, where=where).replace("  ", " ").strip() if where else trf("{x} left behind", L, x=nm)
        else:
            ic = ic if key != "object" else "❓"
            title = trf("{x} gone", L, x=nm) + ((" · " + where) if where else "")
    return ic, title.strip(), nm


PUSH_CLASS.update({"obj_animal": "animal", "obj_vehicle": "other", "obj_thing": "other", "obj_gone": None})   # level «Was» (579a)
_PROF_PUSH_T = {}


def obj_push(ev, ic, title, text, jpg=None, gap_key=None):
    """one message of this package (only while armed, with the push level and the quiet hours of 579a) - True if sent"""
    now = time.time()
    if gap_key is not None:
        if now - _PROF_PUSH_T.get(gap_key, 0.0) < OBJ_PUSH_GAP:
            return False
    w = WATCH_REF.get("w")
    n = getattr(w, "notifier", None) if w is not None else None
    if n is None or not is_armed() or not CFG.get("notify_on") or not n.configured():
        return False
    ok, why = push_allowed(ev)
    if not ok:
        _px_held(ev, why)
        return False
    if gap_key is not None:
        _PROF_PUSH_T[gap_key] = now
    if jpg is not None:
        jpg = sx_push_jpg(jpg)                              # «Pictures: small / without» of 579a
    pub = CFG["public_url"].strip().rstrip("/")
    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text, "info_title": "{name}: " + title,
         "obj_ic": ic, "obj_title": title, "obj_ev": ev, "snapshot": None, "rain": bool(STATE.get("rain_mode")), "wind": STATE.get("wind_level", ""),
         "source": STATE.get("source_label", ""), "link": pub + "/" if pub else ""}
    threading.Thread(target=n._dispatch, args=(p, jpg if CFG.get("push_pics") != "text" else None, "objekt.jpg"), daemon=True).start()
    return True


_push_kind_op_base = push_kind


def push_kind(p):                                         # + 639zz: the messages of this package keep their own symbol and title
    if p.get("obj_ic") and p.get("obj_title"):
        return {"ic": p["obj_ic"], "title": str(p["obj_title"]), "text": _pk_cut(_PK_SIM.sub(" ", str(p.get("text") or "")).strip()),
                "cls": "alarm", "pic": True, "test": False}
    return _push_kind_op_base(p)


def obj_zone_of(box, pw=1.0, ph=1.0):
    """the name of the first named zone (not ignore / privacy / sleep) at the foot point of a box - "" if none"""
    try:
        nx, ny = (box[0] + box[2] / 2.0) / pw, (box[1] + box[3] * 0.85) / ph
        for z in ZONES:
            if z.get("mode") in ("ignore", "privacy", "sleep", "line") or not zone_here(z):
                continue
            if point_in_poly(nx, ny, z["points"]) and str(z.get("name") or "").strip():
                return str(z["name"]).strip()[:24]
    except Exception:
        pass
    return ""


def _obj_jpg(frame, box=None, pw=1.0, ph=1.0):
    """the picture of a message: the clean camera picture, a thin orange frame around the thing"""
    if frame is None:
        return None
    try:
        img = frame.copy()
        if box is not None:
            H, W = img.shape[:2]; sx, sy = W / float(pw), H / float(ph)
            x, y, w_, h_ = [int(v) for v in (box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy)]
            cv2.rectangle(img, (x, y), (x + w_, y + h_), (0, 160, 255), 2)
        img = apply_privacy(img)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes() if ok else None
    except Exception:
        return None


# ---- which profile applies ------------------------------------------------------------------------------------------------
def prof_def(pid=None):
    pid = PROF["eff"] if pid is None else pid
    return PROFILES.get(pid, PROF_NONE)


def prof_energy(pid=None):
    """what the profile allows the AI to cost (the base values of today when there is no profile)"""
    d = prof_def(pid)
    things = tuple(t for t in d["things"] if CFG.get({"package": "obj_pkg_on", "left": "obj_left_on", "gone": "obj_gone_on"}[t], True))
    return {"ai_k": max(1, int(d["ai_k"])), "motion_only": bool(d["motion_only"]), "proc_max": int(d["proc_max"] or 0),
            "things": things, "big": bool(d["big"] and CFG.get("ai_model_big"))}


def _prof_sched(now=None):
    """(schedule name, profile) of the last running schedule that chooses a profile - (None, "") if none"""
    now = now or sim_now()
    with LOCK:
        plans = [dict(s) for s in SCHEDULES]
    got = (None, "")
    for s in plans:
        try:
            if s.get("profile") in PROFILES and schedule_active(s, now):
                got = (s["name"], s["profile"])
        except Exception:
            pass
    return got


def prof_effective(now=None, battery=None):
    """(profile, why) - battery low > schedule > own choice. Keeps the hysteresis of the battery (+5 %)."""
    b = STATE.get("battery") if battery is None else battery
    b = b or {}
    if CFG.get("prof_batt_on") and b.get("on") and b.get("pct") is not None:
        try:
            pct = float(b["pct"]); thr = float(CFG.get("prof_batt_pct") or 20)
        except (TypeError, ValueError):
            pct, thr = 100.0, 0.0
        charging = bool(b.get("charging")) or (b.get("src") == "ups" and b.get("on_battery") is False)
        if PROF["batt"]:
            if charging or pct >= thr + 5:
                PROF["batt"] = False
        elif not charging and pct < thr:
            PROF["batt"] = True
    else:
        PROF["batt"] = False
    if PROF["batt"]:
        return "battery", "battery"
    sn, sp = _prof_sched(now)
    if (sn, sp) != PROF["sched"]:
        PROF["sched"] = (sn, sp); PROF["over"] = None        # another schedule (or none): it takes over again
    if sp and PROF["over"] != (sn, sp):
        return sp, "schedule:" + str(sn)
    m = str(CFG.get("det_profile") or "")
    return (m if m in PROFILES else ""), "manual"


def prof_tick(force=False, now=None, battery=None):
    """every ~2 s (from the camera loop and the page): the profile that applies now; a change is logged once"""
    t = time.time()
    if not force and t - PROF["tick_t"] < 2.0:
        return PROF["eff"]
    PROF["tick_t"] = t
    m = str(CFG.get("det_profile") or "")
    if PROF["seen_manual"] is None:
        PROF["seen_manual"] = m
    elif m != PROF["seen_manual"]:                           # chosen by hand (page, window, settings import)
        PROF["seen_manual"] = m
        sn, sp = _prof_sched(now)
        PROF["sched"] = (sn, sp)
        PROF["over"] = (sn, sp) if sp else None
    pid, why = prof_effective(now, battery)
    if pid != PROF["eff"] or why != PROF["why"]:
        old = PROF["eff"]
        PROF.update(eff=pid, why=why, since=t)
        d = prof_def(pid)
        log_event("sys", f"Detection profile: {d['icon']} {d['name']} ({prof_why_text(why, 'en')})")
        if not prof_energy(pid)["things"]:
            THINGS.reset(keep_remembered=True); CHANGE.reset()
        if prof_def(old)["proc_max"] != d["proc_max"]:
            pass                                             # 410 notices the new working size itself (_reset_models)
    big = prof_energy(pid)["big"] and CFG.get("ai_model") == "own"
    if big != PROF["big_on"]:
        PROF["big_on"] = big
        if own_big_paths()[0]:
            try:
                own_ai_switched()                            # the other own model (195 loads it in the background)
            except Exception as e:
                log_event("ai", f"Bigger model: {e}"[:160])
    STATE["det_profile"] = {"id": pid, "why": why}
    return pid


def prof_set(pid, who="web"):
    pid = str(pid or "")
    if pid and pid not in PROFILES:
        return False, "unknown profile"
    CFG["det_profile"] = pid
    save_settings()
    log_event("sys", f"Detection profile chosen ({who}): {prof_def(pid)['name']}")
    prof_tick(force=True)
    return True, ""


def prof_why_text(why, lang=None):
    if why == "battery":
        return trf("battery below {p} %", lang, p=int(CFG.get("prof_batt_pct") or 20))
    if str(why).startswith("schedule:"):
        return trf("schedule «{n}»", lang, n=why.split(":", 1)[1])
    return tr("chosen by hand", lang)


# ---- energy: the hooks (they can only save) ---------------------------------------------------------------------------------
def prof_proc_width(pw):
    """410: the working width of the picture - the profile «Save battery» makes it smaller (never bigger)"""
    try:
        prof_tick()
    except Exception as e:
        log_event("sys", f"Detection profile: {e}"[:160])
    cap = prof_energy()["proc_max"]
    return min(int(pw), cap) if cap else pw


def prof_motion(ai, fg, t0):
    """410, before the AI: was there movement? (profile «Night»: the AI only looks then)"""
    try:
        if fg is not None and fg.size and cv2.countNonZero(fg) >= PROF_MOTION_FRAC * fg.size:
            ai.prof_motion_t = t0
        elif STATE.get("warm") or time.time() - float(SENS.get("pir_t") or 0) < 2.0:
            ai.prof_motion_t = t0                             # warm body / PIR also count
    except Exception:
        pass


_prof_detect_base = AIDetector.detect


def _prof_detect(self, frame):
    if DEMO.get("on"):
        return _prof_detect_base(self, frame)
    e = prof_energy()
    if e["motion_only"] and time.time() - float(getattr(self, "prof_motion_t", 0.0) or 0.0) > PROF_MOTION_HOLD:
        if self.boxes or self.objects:
            self.boxes = []; self.objects = []
        PROF["ai_skipped"] += 1
        if CFG.get("ai_enabled") and self.net is not None:
            STATE["ai_status"] = "waiting for movement (profile)"
        return self.boxes
    if e["ai_k"] > 1:
        self._prof_n = getattr(self, "_prof_n", 0) + 1
        if self._prof_n % e["ai_k"]:
            PROF["ai_skipped"] += 1
            return self.boxes
    PROF["ai_runs"] += 1
    return _prof_detect_base(self, frame)


# wraps: AIDetector.detect
AIDetector.detect = _prof_detect

_wk_ai_op_base = wk_ai


def wk_ai():                                              # + 639zz: no light AI on the wide picture in «Save battery»
    if PROF["eff"] == "battery":                          # (in «Night» the wide camera runs it only at movement anyway, 639zw)
        return None, "battery profile"
    return _wk_ai_op_base()


OWN_BIG_ONNX, OWN_BIG_JSON = "moveeye_model_gross.onnx", "moveeye_model_gross.json"


def own_big_paths():
    for d in ai_model_dirs():
        a, b = os.path.join(d, OWN_BIG_ONNX), os.path.join(d, OWN_BIG_JSON)
        if os.path.isfile(a) and os.path.isfile(b):
            return a, b
    return None, None


_own_ai_paths_op_base = own_ai_paths


def own_ai_paths():                                       # + 639zz: the bigger own model only in House / Garden with ai_model_big
    if PROF.get("big_on"):
        a, b = own_big_paths()
        if a:
            return a, b
    return _own_ai_paths_op_base()


# schedules (030) keep the field «profile» (the editor of the page and of the window send it)
_clean_schedule_op_base = _clean_schedule


def _clean_schedule(s, i):                                # + 639zz: «Erkennungsprofil» of a schedule
    out = _clean_schedule_op_base(s, i)
    if out is not None:
        out["profile"] = s.get("profile") if isinstance(s, dict) and s.get("profile") in PROFILES else ""
    return out


_schedule_save_op_base = schedule_save


def schedule_save(index, data):                           # + 639zz: an editor without the field keeps the chosen profile
    if isinstance(data, dict) and "profile" not in data and isinstance(index, int) and 0 <= index < len(SCHEDULES):
        data = dict(data, profile=SCHEDULES[index].get("profile", ""))
    r = _schedule_save_op_base(index, data)
    prof_tick(force=True)
    return r


# ---- arrivals: an animal / a vehicle is reported once when it comes (not every picture) -------------------------------------
class SeenWatch:
    """per key: seen for confirm_s -> one arrival; again only after gone_s without it. Things seen in the first grace_s
    after the start are already there (no arrival: a parked car at the start is no message)."""

    def __init__(self, confirm_s=1.5, gone_s=300.0, grace_s=0.0):
        self.confirm_s, self.gone_s, self.grace_s = confirm_s, gone_s, grace_s
        self.s = {}; self.t0 = None

    def feed(self, t, seen):
        """seen: {key: extra} at time t -> [(key, extra)] that arrived now"""
        if self.t0 is None:
            self.t0 = t
        out = []
        for k, ex in seen.items():
            st = self.s.get(k)
            if st is None or t - st["last"] > self.gone_s:
                st = self.s[k] = {"first": t, "last": t, "done": False, "base": t - self.t0 < self.grace_s}
            st["last"] = t
            if not st["done"] and t - st["first"] >= self.confirm_s:
                st["done"] = True
                if not st["base"]:
                    out.append((k, ex))
        for k in [k for k, st in self.s.items() if t - st["last"] > self.gone_s]:
            del self.s[k]
        return out


ANIMAL_WATCH = SeenWatch(confirm_s=1.5, gone_s=300.0)
VEHICLE_WATCH = SeenWatch(confirm_s=1.5, gone_s=120.0, grace_s=30.0)


def prof_animal_policy(key, box=None, ph=1.0, pid=None):
    """report / log for an animal in the profile (persons are not handled here)"""
    a = prof_def(pid)["animals"]
    if a == "all":
        return "report"
    if a == "big":
        if key in WILD_BIG or (key == "animal" and box is not None and box[3] >= WILD_BIG_H * ph):
            return "report"
    return "log"


def veh_policy(vtype, pid=None):
    """the choice of the vehicle type (veh_*); a profile without vehicles reports none (at most «log»)"""
    k = VEH_TYPES.get(vtype, VEH_TYPES["car"])[0]
    p = CFG.get(k) if CFG.get(k) in VEH_POLICIES else "log"
    if p == "report" and not prof_def(pid)["vehicles"]:
        return "log"
    return p


# ---- things: parcel at the door, left behind, gone -------------------------------------------------------------------------
class ThingsWatch:
    """state machine over the checks (about one a minute): items [(label, box 0..1, conf)], persons [box 0..1]."""

    def __init__(self):
        self.reset()

    def reset(self, keep_remembered=False):
        keep = [tr_ for tr_ in getattr(self, "tracks", []) if tr_["remembered"]] if keep_remembered else []
        for tr_ in keep:
            tr_["miss"] = 0; tr_["patch"] = None
        self.tracks = keep; self.n = 0; self.next_id = max([tr_["id"] for tr_ in keep] + [0]) + 1; self.ghosts = []

    @staticmethod
    def _same(a, b):
        return a == b or "object" in (a, b) and (a in PKG_LABELS or b in PKG_LABELS)

    def observe(self, t, items, persons, pkg_zone=lambda b: True, allowed=("package", "left", "gone"), cfg=None):
        """-> [(kind, track)] events. kinds: package, left, gone, remembered"""
        c = cfg or CFG
        ev = []
        used = set()
        for lab, box, conf in items:
            best, bi = None, 0.3
            for tr_ in self.tracks:
                if id(tr_) in used or not self._same(tr_["label"], lab):
                    continue
                v = iou(tr_["box"], box)
                if v > bi:
                    best, bi = tr_, v
            if best is None:
                best = {"id": self.next_id, "label": lab, "box": tuple(box), "first": t, "last": t, "seen": 0, "miss": 0,
                        "base": self.n == 0, "remembered": False, "rep": set(), "patch": None}
                self.next_id += 1
                self.tracks.append(best)
            else:
                best["box"] = tuple(0.7 * a + 0.3 * b for a, b in zip(best["box"], box))
                if best["label"] == "object" and lab != "object":
                    best["label"] = lab                     # the AI knows better
            best["last"] = t; best["seen"] += 1; best["miss"] = 0
            used.add(id(best))
        near = lambda b: any(iou(_grow(b, 0.25), p) > 0.0 for p in persons)
        for tr_ in list(self.tracks):
            if id(tr_) in used:
                age = t - tr_["first"]
                if tr_["base"] or near(tr_["box"]):
                    pass
                elif "package" in allowed and tr_["label"] in PKG_LABELS and pkg_zone(tr_["box"]) and "pkg" not in tr_["rep"] \
                        and age >= float(c.get("obj_pkg_min", 2)) * 60.0 - 1:
                    tr_["rep"].update(("pkg", "left")); ev.append(("package", tr_))
                elif "left" in allowed and tr_["label"] in BAG_LABELS and "left" not in tr_["rep"] and not (
                        "package" in allowed and tr_["label"] in PKG_LABELS and pkg_zone(tr_["box"])) \
                        and age >= float(c.get("obj_left_min", 10)) * 60.0 - 1:
                    tr_["rep"].add("left"); ev.append(("left", tr_))
                if "gone" in allowed and not tr_["remembered"] and tr_["label"] in GONE_LABELS \
                        and age >= float(c.get("obj_remember_min", 30)) * 60.0 - 1:
                    tr_["remembered"] = True; ev.append(("remembered", tr_))
                continue
            if near(tr_["box"]):
                continue                                    # somebody stands in front of it - no miss
            tr_["miss"] += 1
            if tr_["remembered"] and "gone" in allowed and tr_["miss"] >= OBJ_GONE_MISSES:
                ev.append(("gone", tr_)); self.tracks.remove(tr_); self.ghosts.append((t, tr_["box"]))
            elif not tr_["remembered"] and tr_["miss"] >= 3:
                self.tracks.remove(tr_)
        self.ghosts = [g for g in self.ghosts if t - g[0] < 3600]
        self.n += 1
        return ev

    def remember_now(self):
        n = 0
        for tr_ in self.tracks:
            if tr_["label"] in GONE_LABELS and not tr_["remembered"]:
                tr_["remembered"] = True; n += 1
        return n

    def forget(self):
        for tr_ in self.tracks:
            tr_["remembered"] = False
        self.ghosts = []


def _grow(b, k):
    return (b[0] - b[2] * k, b[1] - b[3] * k, b[2] * (1 + 2 * k), b[3] * (1 + 2 * k))


class StaticChange:
    """new things in the picture without a class (a parcel, a cool box): the picture of each check against a slowly learnt
    background. A blob counts when it is there at two checks in a row at the same place and did not change in between."""
    W = 160

    def __init__(self):
        self.reset()

    def reset(self):
        self.ref = None; self.prev = None; self.prev_blobs = []; self.age = {}

    def _gray(self, img):
        g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = g.shape[:2]
        g = cv2.resize(g, (self.W, max(8, int(h * self.W / float(w)))), interpolation=cv2.INTER_AREA)
        return cv2.GaussianBlur(g, (5, 5), 0)

    def patch(self, img, box):
        g = self._gray(img); H, W = g.shape[:2]
        x, y, w, h = int(box[0] * W), int(box[1] * H), max(2, int(box[2] * W)), max(2, int(box[3] * H))
        return g[max(0, y):y + h, max(0, x):x + w].copy()

    def same_patch(self, img, box, patch):
        """is the remembered thing still there? (normalised correlation of the picture part)"""
        if patch is None or patch.size < 4:
            return True
        cur = self.patch(img, box)
        if cur.shape != patch.shape or cur.size < 4:
            return True
        a = cur.astype(np.float32) - cur.mean(); b = patch.astype(np.float32) - patch.mean()
        den = float(np.sqrt((a * a).sum() * (b * b).sum()))
        if den < 1e-3:
            return abs(float(cur.mean()) - float(patch.mean())) < 25
        return float((a * b).sum()) / den >= 0.55 and abs(float(cur.mean()) - float(patch.mean())) < 45

    def update(self, img, persons=(), ghosts=(), keep=()):
        """-> [box 0..1] of new still things. persons: boxes 0..1 (left out), ghosts: places where a remembered thing
        disappeared (learnt at once), keep: boxes of remembered things (never learnt into the background)"""
        g = self._gray(img)
        H, W = g.shape[:2]
        if self.ref is None or self.ref.shape != g.shape:
            self.ref = g.astype(np.float32); self.prev = g; self.prev_blobs = []; return []
        if abs(float(g.mean()) - float(self.ref.mean())) > 25:
            self.ref = g.astype(np.float32); self.prev = g; self.prev_blobs = []; return []    # the light changed a lot
        ref8 = cv2.convertScaleAbs(self.ref)
        d = cv2.absdiff(g, ref8)
        m = (d > 28).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        if cv2.countNonZero(m) > 0.3 * m.size:
            self.ref = g.astype(np.float32); self.prev = g; self.prev_blobs = []; return []
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blobs = []
        for c_ in cnts:
            x, y, w, h = cv2.boundingRect(c_)
            a = w * h / float(W * H)
            if not 0.002 <= a <= 0.15:
                continue
            b = (x / float(W), y / float(H), w / float(W), h / float(H))
            if any(iou(_grow(b, 0.2), p) > 0.0 for p in persons):
                continue
            blobs.append((b, (x, y, w, h)))
        out, learn = [], np.ones_like(g, np.float32)
        for b, (x, y, w, h) in blobs:
            reg_now, reg_prev = g[y:y + h, x:x + w], self.prev[y:y + h, x:x + w]
            ghost = any(iou(b, gb) > 0.3 for _t, gb in ghosts)
            if not ghost:                                     # an emptier place than the background = a thing was taken away
                e_now = float(cv2.Canny(reg_now, 40, 120).mean()); e_ref = float(cv2.Canny(ref8[y:y + h, x:x + w], 40, 120).mean())
                ghost = e_ref > 4.0 and e_now < 0.6 * e_ref
            if ghost:
                self.ref[y:y + h, x:x + w] = g[y:y + h, x:x + w]; continue
            key = (round(b[0], 1), round(b[1], 1))
            stable = any(iou(b, pb) > 0.4 for pb in self.prev_blobs) and float(cv2.absdiff(reg_now, reg_prev).mean()) < 10
            self.age[key] = self.age.get(key, 0) + 1
            if any(iou(b, k) > 0.3 for k in keep) or self.age[key] < 20:
                learn[y:y + h, x:x + w] = 0.0                 # stays out of the background (about 20 checks, remembered: always)
            if stable:
                out.append(b)
        self.age = {k: v for k, v in self.age.items() if any((round(b[0], 1), round(b[1], 1)) == k for b, _r in blobs)}
        rate = 0.2 * learn
        self.ref = self.ref * (1.0 - rate) + g.astype(np.float32) * rate
        self.prev = g; self.prev_blobs = [b for b, _r in blobs]
        return out


THINGS = ThingsWatch()
CHANGE = StaticChange()


def _obj_pkg_zone(box):
    """is a box (0..1) in the zone for parcels? obj_pkg_zone = a zone name; empty = any named zone, without zones the picture"""
    want = str(CFG.get("obj_pkg_zone") or "").strip()
    zs = [z for z in ZONES if z.get("mode") not in ("ignore", "privacy", "sleep", "line")]
    if want:
        zs = [z for z in zs if str(z.get("name") or "").strip() == want]
        if not zs:
            return False
    if not zs:
        return True
    nx, ny = box[0] + box[2] / 2.0, box[1] + box[3] * 0.85
    return any(point_in_poly(nx, ny, z["points"]) for z in zs)


def _obj_remembered_save():
    CFG["obj_remembered"] = [{"label": tr_["label"], "box": [round(v, 3) for v in tr_["box"]]} for tr_ in THINGS.tracks if tr_["remembered"]][:20]
    save_settings()


def _obj_remembered_load():
    if THINGS.tracks or not isinstance(CFG.get("obj_remembered"), list):
        return
    for r in CFG["obj_remembered"][:20]:
        try:
            if r.get("label") in GONE_LABELS and len(r.get("box") or []) == 4:
                THINGS.tracks.append({"id": THINGS.next_id, "label": r["label"], "box": tuple(float(v) for v in r["box"]), "first": time.time(),
                                      "last": time.time(), "seen": 1, "miss": 0, "base": True, "remembered": True, "rep": set(), "patch": None})
                THINGS.next_id += 1
        except (AttributeError, TypeError, ValueError):
            pass


def things_check(w, small, full, persons_n, t0, objs=None):
    """one check of the things (called from prof_frame about once a minute, only in profiles with things)"""
    t1 = time.time()
    ph, pw = small.shape[:2]
    if objs is None:
        objs = list(getattr(w.ai, "objects", []) or [])
        try:
            if getattr(w.ai, "net", None) is not None and CFG.get("ai_enabled") and not DEMO.get("on"):
                _b, objs = w.ai.infer(small, 2.0, min(0.5, float(CFG.get("object_conf", 0.4))))    # one run for the things only
        except Exception as e:
            log_event("ai", f"Things check: {e}"[:160])
    items = [(COCO_LABELS.get(o[5]), (o[0] / pw, o[1] / ph, o[2] / pw, o[3] / ph), o[4]) for o in objs
             if COCO_LABELS.get(o[5]) in THING_LABELS and o[4] >= 0.35]
    _obj_remembered_load()
    keep = []
    for tr_ in THINGS.tracks:                                # a remembered thing without a class: still the same picture there?
        if tr_["remembered"] and tr_["label"] == "object":
            keep.append(tr_["box"])
            if tr_["patch"] is None:
                tr_["patch"] = CHANGE.patch(small, tr_["box"])
            elif CHANGE.same_patch(small, tr_["box"], tr_["patch"]):
                items.append(("object", tr_["box"], 0.5))
    for b in CHANGE.update(small, persons_n, THINGS.ghosts, keep):
        if not any(iou(b, it[1]) > 0.3 for it in items):
            items.append(("object", b, 0.5))
    allowed = prof_energy()["things"]
    evs = THINGS.observe(t0, items, persons_n, _obj_pkg_zone, allowed)
    for kind, tr_ in evs:
        for t_ in THINGS.tracks:
            if t_ is tr_ and tr_["remembered"] and tr_["label"] == "object" and tr_["patch"] is None:
                tr_["patch"] = CHANGE.patch(small, tr_["box"])
        obj_event(kind, tr_, full, pw, ph)
    if any(k in ("remembered", "gone") for k, _t in evs):
        _obj_remembered_save()
    PROF["checks"] += 1; PROF["check_t"] = t0; PROF["check_ms"] = int((time.time() - t1) * 1000)
    return evs


def obj_event(kind, tr_, full, pw=1.0, ph=1.0):
    """log + message of a things event"""
    box_n = tr_["box"]
    zone = obj_zone_of(box_n, 1.0, 1.0)
    if kind == "remembered":
        ic, en = THING_NAMES.get(tr_["label"], THING_NAMES["object"])
        log_event("ai", f"Thing remembered: {en} ({zone or 'picture'})")
        return
    ic, title, _nm = obj_push_text(kind, tr_["label"], zone)
    _ic, en_title, _n = obj_push_text(kind, tr_["label"], zone, "en")
    log_event("ai", f"{ic} {en_title}")
    PROF["last_events"].appendleft({"t": datetime.now().strftime("%H:%M"), "ic": ic, "kind": kind, "label": tr_["label"], "zone": zone})
    jpg = _obj_jpg(full, (box_n[0] * pw, box_n[1] * ph, box_n[2] * pw, box_n[3] * ph), pw, ph) if full is not None else None
    if jpg is None and full is not None:
        jpg = _obj_jpg(full)
    text = datetime.now().strftime("%H:%M") + " · " + tr("Things check")
    obj_push("obj_gone" if kind == "gone" else "obj_thing", ic, title, text, jpg, gap_key=(kind, tr_["label"], zone, round(box_n[0], 1)))


# ---- the hook of the camera loop -----------------------------------------------------------------------------------------
def prof_frame(w, small, full, ai_objs, person_boxes, pw, ph, t0):
    """410, once per picture after the AI: animals with names, vehicles by type, the things check (once a minute)"""
    sees = {}
    vs = {}
    for o in ai_objs:
        lab = COCO_LABELS.get(o[5], "")
        if lab in ANIMALS:
            sp = species_for(o[:4]) if CFG.get("species_on") and SPECIES["cache"] else None
            k, _ic, _nm = wild_name(lab, o, sp, "en")
            if k not in sees or o[2] * o[3] > sees[k][2] * sees[k][3]:
                sees[k] = o
        elif lab in VEH_OF_LABEL:
            vt = VEH_OF_LABEL[lab]
            if vt not in vs or o[2] * o[3] > vs[vt][2] * vs[vt][3]:
                vs[vt] = o
    for k, o in ANIMAL_WATCH.feed(t0, sees):
        zone = obj_zone_of(o, pw, ph)
        pol = prof_animal_policy(k, o, ph)
        ic, title, _nm = obj_push_text("animal", k, zone)
        _i, en_title, _n = obj_push_text("animal", k, zone, "en")
        log_event("ai", f"{ic} {en_title} (AI {int(o[4] * 100)} %)")
        PROF["last_events"].appendleft({"t": datetime.now().strftime("%H:%M"), "ic": ic, "kind": "animal", "label": k, "zone": zone})
        if pol == "report":
            obj_push("obj_animal", ic, title, datetime.now().strftime("%H:%M") + f" · {tr('AI')} {int(o[4] * 100)} %",
                     _obj_jpg(full, o, pw, ph), gap_key=("animal", k, zone))
    for vt, o in VEHICLE_WATCH.feed(t0, vs):
        pol = veh_policy(vt)
        if pol == "ignore":
            continue
        zone = obj_zone_of(o, pw, ph)
        ic, title, _nm = obj_push_text("vehicle", vt, zone)
        _i, en_title, _n = obj_push_text("vehicle", vt, zone, "en")
        log_event("car", f"{ic} {en_title}")
        PROF["last_events"].appendleft({"t": datetime.now().strftime("%H:%M"), "ic": ic, "kind": "vehicle", "label": vt, "zone": zone})
        if pol == "report":
            obj_push("obj_vehicle", ic, title, datetime.now().strftime("%H:%M"), _obj_jpg(full, o, pw, ph), gap_key=("vehicle", vt, zone))
    e = prof_energy()
    if not e["things"]:
        PROF["paused"] = ""
        return
    if t0 - PROF["check_t"] < OBJ_CHECK_S:
        return
    pos = (round(float(CFG.get("pan", 0)), 1), round(float(CFG.get("tilt", 0)), 1))
    if CFG.get("patrol") or STATE.get("tracking") or manual_active():
        PROF["check_t"] = t0
        if PROF["paused"] != "moves":
            PROF["paused"] = "moves"; log_event("ai", "Things check paused: the camera moves (patrol / following)")
        return
    if PROF.get("pos") != pos:
        PROF["pos"] = pos; CHANGE.reset()                        # another direction: learn the background again
    PROF["paused"] = ""
    persons_n = [(b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph) for b in person_boxes]
    try:
        things_check(w, small, full, persons_n, t0)
    except Exception as e_:
        PROF["check_t"] = t0
        log_event("ai", f"Things check: {type(e_).__name__}: {e_}"[:160])


# ---- state for the page and the window -------------------------------------------------------------------------------------
def prof_state(lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    prof_tick()
    pid = PROF["eff"]; d = prof_def(pid); e = prof_energy(pid)
    parts = []
    if e["motion_only"]:
        parts.append(tr("AI only at movement", L))
    if e["ai_k"] > 1:
        parts.append(trf("AI only every {k}th picture", L, k=e["ai_k"]))
    if e["proc_max"]:
        parts.append(trf("small pictures ({w} px)", L, w=e["proc_max"]))
    parts.append(tr("things check every minute", L) if e["things"] else tr("things check off", L))
    if e["big"]:
        parts.append(tr("bigger model allowed", L))
    things = []
    for tr_ in THINGS.tracks[:12]:
        ic, en = THING_NAMES.get(tr_["label"], THING_NAMES["object"])
        st = tr("remembered", L) if tr_["remembered"] else (tr("reported", L) if tr_["rep"] else tr("seen", L))
        things.append({"ic": ic, "name": tr(en, L), "state": st, "since": datetime.fromtimestamp(tr_["first"]).strftime("%H:%M"),
                       "zone": obj_zone_of(tr_["box"])})
    evs = [dict(x, name=(obj_push_text(x["kind"], x["label"], x["zone"], L)[1] if x["kind"] in ("animal", "vehicle", "package", "left", "gone") else x["label"]))
           for x in list(PROF["last_events"])[:6]]
    return {"ok": True, "id": pid, "chosen": str(CFG.get("det_profile") or ""), "why": PROF["why"], "why_text": prof_why_text(PROF["why"], L),
            "icon": d["icon"], "name": tr(d["name"], L), "energy": " · ".join(parts),
            "list": [{"id": "", "icon": PROF_NONE["icon"], "name": tr(PROF_NONE["name"], L), "info": tr(PROF_NONE["info"], L)}] +
                    [{"id": k, "icon": PROFILES[k]["icon"], "name": tr(PROFILES[k]["name"], L), "info": tr(PROFILES[k]["info"], L)} for k in PROF_ORDER],
            "things": things, "events": evs, "paused": tr("paused: the camera moves", L) if PROF["paused"] == "moves" else "",
            "batt_on": bool(CFG.get("prof_batt_on")), "batt_pct": int(CFG.get("prof_batt_pct") or 20),
            "checks": PROF["checks"], "ai_skipped": PROF["ai_skipped"], "ai_runs": PROF["ai_runs"]}


def prof_routes(app, reply, body):
    from flask import request

    @app.route("/api/profile", methods=["GET", "POST"])
    def api_profile():
        if request.method == "GET":
            return reply(prof_state(request.args.get("lang")))
        d = body(); a = d.get("action")
        if a == "set":
            ok, err = prof_set(d.get("id", ""), "web")
            if not ok:
                return reply({"ok": False, "error": err}, 400)
        elif a == "remember":
            n = THINGS.remember_now(); _obj_remembered_save(); log_event("ai", f"Things remembered by hand: {n}")
        elif a == "forget":
            THINGS.forget(); _obj_remembered_save(); log_event("ai", "Remembered things forgotten")
        else:
            return reply({"ok": False, "error": "unknown action"}, 400)
        return reply(prof_state(d.get("lang")))


_smalltv_routes_op_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zz: /api/profile (550 calls smalltv_routes once)
    _smalltv_routes_op_base(app, reply, body)
    prof_routes(app, reply, body)


# ---- settings (web and window read the same lists) ------------------------------------------------------------------------
TOGGLES.extend([
    (_OPS, "prof_batt_on", "Battery low: switch to «Save battery»"),
    (_OPS, "obj_pkg_on", "Parcel at the door (House watch)"),
    (_OPS, "obj_left_on", "Thing left behind (House watch)"),
    (_OPS, "obj_gone_on", "Remembered thing gone (House / Garden)"),
    ("AI detection", "ai_model_big", "Bigger own model in House / Garden (only after a measurement on the Pi)"),
])
SLIDERS.extend([
    (_OPS, "prof_batt_pct", "… below (%)", 5, 60, 1),
    (_OPS, "obj_pkg_min", "Parcel: lies there for (min)", 1, 30, 1),
    (_OPS, "obj_left_min", "Left behind after (min)", 2, 120, 1),
    (_OPS, "obj_remember_min", "Remember a thing after (min)", 5, 240, 5),
])
TEXTS.extend([
    (_OPS, "det_profile", "Profile", "enum", "det_profiles"),
    (_OPS, "obj_pkg_zone", "Zone for parcels", "enum", "obj_zones"),
    ("Vehicle filter", "veh_car", "🚗 Car", "enum", "veh_policy"),
    ("Vehicle filter", "veh_moto", "🏍️ Motorbike", "enum", "veh_policy"),
    ("Vehicle filter", "veh_bike", "🚲 Bicycle", "enum", "veh_policy"),
    ("Vehicle filter", "veh_truck", "🚚 Van / truck", "enum", "veh_policy"),
])
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS if k in _OP_DEF})
SECTIONS.append(_OPS)
TK_SUB_ICONS[_OPS] = "◈"
SIMPLE_SECTIONS.update({_OPS, "Vehicle filter"})        # «Einfach»: the four vehicle choices are main switches, the old filter stays folded
SIMPLE_KEYS.update({"det_profile", "prof_batt_on", "obj_pkg_on", "obj_left_on", "obj_gone_on", "veh_car", "veh_moto", "veh_bike", "veh_truck"})
MENU_MAIN.update({"veh_car", "veh_moto", "veh_bike", "veh_truck"})
MENU_TITLES.setdefault(_OPS, "Detection profile")
SET_HELP.update({
    "det_profile": ("One choice for what MoveEye reports and how much the AI computes: Night at the tent, Garden by day, House watch, "
                    "Save battery. A schedule can choose a profile (field «Detection profile»), the battery too. «Own settings» = as before.",
                    "Night at the tent for camping nights on the battery."),
    "prof_batt_on": ("Below the threshold MoveEye switches to «Save battery» by itself (only persons, the AI seldom) and back when "
                     "the battery charges or is 5 % above it.", "On for battery operation."),
    "obj_pkg_on": ("Only in «House watch»: a new thing that lies still in the zone for parcels for a few minutes (nobody next to "
                   "it) - one message with the picture.", "On."),
    "obj_left_on": ("Only in «House watch»: a backpack, bag or suitcase that stays where somebody put it down.", "On."),
    "obj_gone_on": ("In «House watch» and «Garden by day»: a bike, cool box or chair that was there for a while (or was remembered "
                    "with «Remember now») disappears.", "On."),
    "ai_model_big": ("A bigger own model (file moveeye_model_gross.onnx) only in the profiles House and Garden. Off until it has "
                     "been measured on the Pi (time per picture, temperature, battery).", "Off."),
    "veh_car": ("Per type of vehicle: report (push message, in the profile «House watch»), only log, or ignore.", "Only log."),
})
for _k in ("veh_moto", "veh_bike", "veh_truck"):
    SET_HELP[_k] = SET_HELP["veh_car"]

_text_choice_pairs_op_base = text_choice_pairs


def text_choice_pairs(key):                               # + 639zz: profiles, parcel zone, vehicle choices
    extra = (TEXT_SPECS.get(key) or (None, None))[1]
    if extra == "det_profiles":
        return [("", PROF_NONE["icon"] + " " + tr(PROF_NONE["name"]))] + [(k, PROFILES[k]["icon"] + " " + tr(PROFILES[k]["name"])) for k in PROF_ORDER]
    if extra == "veh_policy":
        return [("report", tr("report")), ("log", tr("only log")), ("ignore", tr("ignore"))]
    if extra == "obj_zones":
        names = [str(z.get("name") or "").strip() for z in ZONES if z.get("mode") not in ("ignore", "privacy", "sleep", "line")]
        cur = str(CFG.get("obj_pkg_zone") or "")
        return [("", tr("any zone (without zones: the picture)"))] + [(n, n) for n in dict.fromkeys(names + ([cur] if cur else [])) if n]
    return _text_choice_pairs_op_base(key)


_set_text_op_base = set_text


def set_text(key, value):                                 # + 639zz: a profile chosen in the settings counts like the button
    ok, err = _set_text_op_base(key, value)
    if ok and key == "det_profile":
        save_settings(); prof_tick(force=True)
    return ok, err


# the web group «Erkennung»: the profile first; the section gets its panel (buttons, state, things)
WEB_PAGE = WEB_PAGE.replace('{card: "tune", title: "Improve detection", ic: "🎯"}, ',
                            '{card: "tune", title: "Improve detection", ic: "🎯"}, {sec: "Detection profile", title: "Detection profile", ic: "🎛️"}, ', 1)
_OP_SEC_OLD = 'if (sec.id === "Extra display" && window.stvPanel) stvPanel(d);'
WEB_PAGE = WEB_PAGE.replace(_OP_SEC_OLD, _OP_SEC_OLD + '\n    if (sec.id === "Detection profile" && window.profPanel) profPanel(d);   // 639zz: detection profiles', 1)
# the schedule editor (530): «Detection profile» per schedule
_OP_SCHED_OLD = 'mk("Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)", skip));'
_OP_SCHED_NEW = ('mk("Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)", skip),\n'
                 '             mk("Detection profile", mkSel(window.profOpts ? profOpts() : [["", "–"]], cur.profile || "", v => { cur.profile = v; save(); })));   // 639zz')
WEB_PAGE = WEB_PAGE.replace(_OP_SCHED_OLD, _OP_SCHED_NEW, 1)

PROF_CSS = r"""
#profpanel .pfnow{font-weight:600;margin-bottom:2px}
#profpanel .pfgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:8px 0}
#profpanel .pfb{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-align:left;padding:9px 10px;border-radius:12px;
  border:1px solid var(--line,#2a3442);background:var(--card,transparent);color:inherit;font:inherit;cursor:pointer;min-height:84px}
#profpanel .pfb .pi{font-size:24px;line-height:1}
#profpanel .pfb .pn{font-weight:600;font-size:14px}
#profpanel .pfb .pd{font-size:12px;opacity:.75;line-height:1.3}
#profpanel .pfb.on{border-color:#2f7cf6;background:rgba(47,124,246,.14);box-shadow:inset 0 0 0 1px #2f7cf6}
#profpanel .pfb.auto{outline:2px dashed #2f7cf6;outline-offset:2px}
#profpanel .pfrow{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}#profpanel .pfrow button{flex:1 1 140px}
#profpanel .pfl{font-size:13px;white-space:pre-wrap;margin-top:6px}
"""

PROF_JS = r"""
<script>
(function () {
  try { const D = /*PROFDE*/{}; if (typeof I18N !== "undefined" && I18N.de) for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const st = document.createElement("style"); st.textContent = /*PROFCSS*/""; (document.head || document.documentElement).appendChild(st);
  let BOX = null, TM = null, LAST = null;
  const NAMES = [["", "⚙️", "Own settings"], ["night", "🏕️", "Night at the tent"], ["garden", "🌳", "Garden by day"], ["home", "🏠", "House watch"], ["battery", "🔋", "Save battery"]];
  window.profOpts = () => NAMES.map(([v, i, n]) => [v, v ? i + " " + T(n) : "– " + T("unchanged") + " –"]);
  const P = d => fetch("/api/profile", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))}).then(r => r.json());
  const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; };
  function show(j) {
    if (!BOX || !j || !j.ok) return;
    LAST = j;
    BOX.querySelector(".pfnow").textContent = T("Active") + ": " + j.icon + " " + j.name;
    BOX.querySelector(".pfwhy").textContent = j.why_text + (j.paused ? " · " + j.paused : "");
    const g = BOX.querySelector(".pfgrid");
    if (g.dataset.sig !== JSON.stringify([j.list, j.chosen, j.id])) {
      g.dataset.sig = JSON.stringify([j.list, j.chosen, j.id]); g.textContent = "";
      j.list.forEach(p => {
        const b = mk("button", "pfb" + (p.id === j.chosen ? " on" : "") + (p.id === j.id && p.id !== j.chosen ? " auto" : "")); b.type = "button";
        b.dataset.id = p.id; b.setAttribute("aria-pressed", p.id === j.chosen ? "true" : "false");
        b.append(mk("span", "pi", p.icon), mk("span", "pn", p.name), mk("span", "pd", p.info));
        b.onclick = async () => { b.disabled = true; show(await P({action: "set", id: p.id})); b.disabled = false; };
        g.appendChild(b);
      });
    }
    BOX.querySelector(".pfen").textContent = "⚡ " + j.energy;
    const th = j.things || [], ev = j.events || [];
    BOX.querySelector(".pfthings").textContent = th.length ? T("Things") + ":\n" + th.map(x => x.ic + " " + x.name + " · " + x.state + " · " + x.since + (x.zone ? " · " + x.zone : "")).join("\n") : "";
    BOX.querySelector(".pfev").textContent = ev.length ? T("Last reports") + ":\n" + ev.map(x => x.t + "  " + x.ic + " " + x.name).join("\n") : "";
  }
  const load = () => fetch("/api/profile?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(show).catch(() => {});
  window.profPanel = function (d) {
    if (d.querySelector("#profpanel")) return;
    BOX = mk("div", "auxbox"); BOX.id = "profpanel";
    BOX.append(mk("div", "pfnow", "…"), mk("div", "pfwhy mut", ""), mk("div", "pfgrid"), mk("div", "pfen mut", ""));
    const r = mk("div", "pfrow");
    const b1 = mk("button", "sec", "📌 " + T("Remember now")); b1.type = "button"; b1.title = T("Remember the things in view - a message when one is gone");
    b1.onclick = async () => show(await P({action: "remember"}));
    const b2 = mk("button", "sec", "✕ " + T("Forget")); b2.type = "button"; b2.onclick = async () => show(await P({action: "forget"}));
    r.append(b1, b2); BOX.appendChild(r);
    BOX.append(mk("div", "pfthings pfl", ""), mk("div", "pfev pfl mut", ""),
               mk("div", "pfl mut", T("Automatic: choose a profile in a schedule (Protection → Schedule), or below: battery low.")));
    const sm = d.querySelector("summary"); if (sm) sm.after(BOX); else d.prepend(BOX);
    const sel = d.querySelector('[data-key="det_profile"]:not(select)'); if (sel) sel.hidden = true;   // the buttons replace the list
    load();
    if (!TM) TM = setInterval(() => { if (BOX && BOX.offsetParent !== null && !document.hidden) load(); }, 3000);
  };
})();
</script>
"""
PROF_JS_KEYS = ["Active", "Own settings", "Night at the tent", "Garden by day", "House watch", "Save battery", "unchanged", "Remember now",
                "Remember the things in view - a message when one is gone", "Forget", "Things", "Last reports",
                "Automatic: choose a profile in a schedule (Protection → Schedule), or below: battery low.", "Detection profile"]


def prof_web_de_refresh():
    """the German texts of the web panel (after the translation table below is known)"""
    global WEB_PAGE
    m = re.search(r"/\*PROFDE\*/(\{.*?\});", WEB_PAGE)
    if m:
        WEB_PAGE = WEB_PAGE[:m.start(1)] + json.dumps({_k: DE.get(_k, _k) for _k in PROF_JS_KEYS}, ensure_ascii=False) + WEB_PAGE[m.end(1):]


WEB_PAGE = WEB_PAGE.replace("</body>", PROF_JS.replace('/*PROFCSS*/""', json.dumps(PROF_CSS), 1) + "</body>", 1)


# ---- window (Tkinter): the same in Settings → Detection → Detection profile --------------------------------------------
def _prof_tk_build_section(self, sec, sbody, settings_parent=None):
    _prof_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != _OPS:
        return
    try:
        _prof_tk_panel(self, sbody)
    except Exception as e:
        log_event("sys", f"Window: detection profile: {e}"[:160])


def _prof_tk_panel(app, sbody):
    box = ttk.Frame(sbody); box.pack(fill="x", pady=(6, 0))
    now = ttk.Label(box, text="", wraplength=340, justify="left"); now.pack(anchor="w")
    grid = ttk.Frame(box); grid.pack(fill="x", pady=(4, 0))
    btns = {}
    rows = [("", PROF_NONE)] + [(k, PROFILES[k]) for k in PROF_ORDER]
    for i, (pid, d) in enumerate(rows):
        b = ttk.Button(grid, text=d["icon"] + " " + tr(d["name"]), command=lambda p=pid: (prof_set(p, "window"), tick(once=True)))
        b.grid(row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2); btns[pid] = b
    grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
    en = ttk.Label(box, text="", style="Mut.TLabel", wraplength=340, justify="left"); en.pack(anchor="w", pady=(4, 0))
    bf = ttk.Frame(box); bf.pack(fill="x", pady=(4, 0))
    ttk.Button(bf, text="📌 " + tr("Remember now"), command=lambda: (THINGS.remember_now(), _obj_remembered_save())).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="✕ " + tr("Forget"), command=lambda: (THINGS.forget(), _obj_remembered_save())).pack(side="left", expand=True, fill="x")
    th = ttk.Label(box, text="", style="Mut.TLabel", wraplength=340, justify="left"); th.pack(anchor="w", pady=(4, 0))

    def tick(once=False):
        try:
            if not now.winfo_exists():
                return
            j = prof_state()
            now.config(text=tr("Active") + ": " + j["icon"] + " " + j["name"] + "\n" + j["why_text"] + (" · " + j["paused"] if j["paused"] else ""))
            for pid, b in btns.items():
                b.state(["pressed"] if pid == j["chosen"] else ["!pressed"])
            en.config(text="⚡ " + j["energy"])
            lines = [x["ic"] + " " + x["name"] + " · " + x["state"] + " · " + x["since"] for x in j["things"]]
            lines += [x["t"] + "  " + x["ic"] + " " + x["name"] for x in j["events"][:4]]
            th.config(text="\n".join(lines))
            if not once:
                app.root.after(3000, tick)
        except Exception:
            pass
    tick()


_prof_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _prof_tk_build_section
for _g in TK_GROUPS:
    if _g[0] == "detect" and _OPS not in _g[2]:
        _g[2].insert(_g[2].index("Improve detection") + 1 if "Improve detection" in _g[2] else 0, _OPS)


# ---- texts: (Deutsch, français, italiano, rumantsch) ---------------------------------------------------------------------
_HX_OBJPROF = {
    'Detection profile': ('Erkennungsprofil', 'Profil de détection', 'Profilo di rilevamento', 'Profil d’identificaziun'),
    'Profile': ('Profil', 'Profil', 'Profilo', 'Profil'),
    'Own settings': ('Eigene Einstellungen', 'Réglages propres', 'Impostazioni proprie', 'Atgnas configuraziuns'),
    'No profile: MoveEye works as set up (as before).': ('Kein Profil: MoveEye arbeitet wie eingestellt (wie bisher).', 'Pas de profil : MoveEye fonctionne comme réglé (comme avant).', 'Nessun profilo: MoveEye funziona come impostato (come finora).', 'Nagin profil: MoveEye lavura sco configurà (sco fin ussa).'),
    'Night at the tent': ('Nacht am Zelt', 'Nuit à la tente', 'Notte alla tenda', 'Notg tar la tenda'),
    'Persons and large animals. The AI only looks when something moves - saves a lot.': ('Personen und grosse Tiere. Die KI schaut nur, wenn sich etwas bewegt – spart viel.', 'Personnes et grands animaux. L’IA ne regarde que quand quelque chose bouge – économise beaucoup.', 'Persone e animali grandi. L’IA guarda solo quando qualcosa si muove – risparmia molto.', 'Persunas e animals gronds. La IA guarda mo cura che insatge sa mova – spargna bler.'),
    'Garden by day': ('Garten tagsüber', 'Jardin le jour', 'Giardino di giorno', 'Iert di'),
    'Persons and all animals with their names. Remembered things (bike, cool box) are watched.': ('Personen und alle Tiere mit Namen. Gemerkte Dinge (Velo, Kühlbox) werden bewacht.', 'Personnes et tous les animaux avec leur nom. Les objets mémorisés (vélo, glacière) sont surveillés.', 'Persone e tutti gli animali con il nome. Le cose memorizzate (bici, borsa frigo) sono sorvegliate.', 'Persunas e tut ils animals cun num. Chaussas memorisadas (velo, box da fraid) vegnan survegliadas.'),
    'House watch': ('Hausüberwachung', 'Surveillance de la maison', 'Sorveglianza casa', 'Survegliaziun da la chasa'),
    'Persons, vehicles and parcels: a parcel at the door, things left behind or gone.': ('Personen, Fahrzeuge und Pakete: Paket vor der Tür, liegen gelassene oder verschwundene Dinge.', 'Personnes, véhicules et colis : colis devant la porte, objets oubliés ou disparus.', 'Persone, veicoli e pacchi: pacco davanti alla porta, cose lasciate o sparite.', 'Persunas, vehichels e pachets: pachet davant l’isch, chaussas laschadas enavos u svanidas.'),
    'Save battery': ('Akku sparen', 'Économiser la batterie', 'Risparmiare batteria', 'Spargnar accu'),
    'Only persons. The AI looks seldom, small pictures - for long nights on the battery.': ('Nur Personen. Die KI schaut selten, kleine Bilder – für lange Nächte am Akku.', 'Seulement les personnes. L’IA regarde rarement, petites images – pour de longues nuits sur batterie.', 'Solo persone. L’IA guarda raramente, immagini piccole – per lunghe notti a batteria.', 'Mo persunas. La IA guarda darar, maletgs pitschens – per lungas notgs cun l’accu.'),
    'Active': ('Aktiv', 'Actif', 'Attivo', 'Activ'),
    'chosen by hand': ('von Hand gewählt', 'choisi à la main', 'scelto a mano', 'tschernì a maun'),
    'schedule «{n}»': ('Zeitplan «{n}»', 'horaire « {n} »', 'programma «{n}»', 'plan d’urari «{n}»'),
    'battery below {p} %': ('Akku unter {p} %', 'batterie sous {p} %', 'batteria sotto {p} %', 'accu sut {p} %'),
    'AI only at movement': ('KI nur bei Bewegung', 'IA seulement au mouvement', 'IA solo con movimento', 'IA mo tar moviment'),
    'AI only every {k}th picture': ('KI nur jedes {k}. Bild', 'IA seulement chaque {k}e image', 'IA solo ogni {k}ª immagine', 'IA mo mintga {k}avel maletg'),
    'small pictures ({w} px)': ('kleine Bilder ({w} px)', 'petites images ({w} px)', 'immagini piccole ({w} px)', 'maletgs pitschens ({w} px)'),
    'things check every minute': ('Dinge-Prüfung jede Minute', 'contrôle des objets chaque minute', 'controllo oggetti ogni minuto', 'controlla da chaussas mintga minuta'),
    'things check off': ('Dinge-Prüfung aus', 'contrôle des objets désactivé', 'controllo oggetti spento', 'controlla da chaussas stizzada'),
    'bigger model allowed': ('grösseres Modell erlaubt', 'modèle plus grand permis', 'modello più grande consentito', 'model pli grond permess'),
    'Things check': ('Dinge-Prüfung', 'Contrôle des objets', 'Controllo oggetti', 'Controlla da chaussas'),
    'Things': ('Dinge', 'Objets', 'Oggetti', 'Chaussas'),
    'Last reports': ('Letzte Meldungen', 'Derniers messages', 'Ultimi messaggi', 'Ultims messadis'),
    'remembered': ('gemerkt', 'mémorisé', 'memorizzato', 'memorisà'),
    'reported': ('gemeldet', 'signalé', 'segnalato', 'annunzià'),
    'seen': ('gesehen', 'vu', 'visto', 'vis'),
    'paused: the camera moves': ('Pause: die Kamera bewegt sich', 'pause : la caméra bouge', 'pausa: la camera si muove', 'pausa: la camera sa mova'),
    'Remember now': ('Jetzt merken', 'Mémoriser', 'Memorizza ora', 'Memorisar ussa'),
    'Remember the things in view - a message when one is gone': ('Die Dinge im Bild merken – Meldung, wenn eines fehlt', 'Mémoriser les objets visibles – message si l’un disparaît', 'Memorizza le cose visibili – messaggio se una sparisce', 'Memorisar las chaussas en il maletg – messadi sch’ina manca'),
    'Forget': ('Vergessen', 'Oublier', 'Dimentica', 'Emblidar'),
    'Automatic: choose a profile in a schedule (Protection → Schedule), or below: battery low.': ('Automatisch: im Zeitplan ein Profil wählen (Schutz → Zeitplan) oder unten: bei tiefem Akku.', 'Automatique : choisir un profil dans un horaire (Protection → Horaire) ou ci-dessous : batterie faible.', 'Automatico: scegliere un profilo in un programma (Protezione → Programma) o sotto: batteria bassa.', 'Automatic: tscherner in profil en il plan d’urari (Protecziun → Plan d’urari) u sutvart: accu bass.'),
    'Battery low: switch to «Save battery»': ('Akku tief: auf «Akku sparen» wechseln', 'Batterie faible : passer à « Économiser la batterie »', 'Batteria bassa: passare a «Risparmiare batteria»', 'Accu bass: midar a «Spargnar accu»'),
    '… below (%)': ('… unter (%)', '… sous (%)', '… sotto (%)', '… sut (%)'),
    'Parcel at the door (House watch)': ('Paket vor der Tür (Hausüberwachung)', 'Colis devant la porte (surveillance maison)', 'Pacco davanti alla porta (sorveglianza casa)', 'Pachet davant l’isch (survegliaziun chasa)'),
    'Thing left behind (House watch)': ('Gegenstand liegen gelassen (Hausüberwachung)', 'Objet oublié (surveillance maison)', 'Oggetto lasciato (sorveglianza casa)', 'Chaussa laschada enavos (survegliaziun chasa)'),
    'Remembered thing gone (House / Garden)': ('Gemerkter Gegenstand weg (Haus / Garten)', 'Objet mémorisé disparu (maison / jardin)', 'Oggetto memorizzato sparito (casa / giardino)', 'Chaussa memorisada davent (chasa / iert)'),
    'Bigger own model in House / Garden (only after a measurement on the Pi)': ('Grösseres eigenes Modell in Haus / Garten (erst nach Messung am Pi)', 'Modèle propre plus grand en maison / jardin (seulement après une mesure sur le Pi)', 'Modello proprio più grande in casa / giardino (solo dopo una misura sul Pi)', 'Agen model pli grond en chasa / iert (pir suenter ina mesiraziun sin il Pi)'),
    'Parcel: lies there for (min)': ('Paket: liegt dort seit (Min.)', 'Colis : posé depuis (min)', 'Pacco: lì da (min)', 'Pachet: è là dapi (min)'),
    'Left behind after (min)': ('Liegen gelassen nach (Min.)', 'Oublié après (min)', 'Lasciato dopo (min)', 'Laschà enavos suenter (min)'),
    'Remember a thing after (min)': ('Gegenstand merken nach (Min.)', 'Mémoriser un objet après (min)', 'Memorizzare un oggetto dopo (min)', 'Memorisar ina chaussa suenter (min)'),
    'Zone for parcels': ('Zone für Pakete', 'Zone pour les colis', 'Zona per i pacchi', 'Zona per pachets'),
    'any zone (without zones: the picture)': ('jede Zone (ohne Zonen: das ganze Bild)', 'toute zone (sans zones : l’image)', 'ogni zona (senza zone: l’immagine)', 'mintga zona (senza zonas: il maletg)'),
    'report': ('melden', 'signaler', 'segnalare', 'annunziar'),
    'only log': ('nur protokollieren', 'seulement journal', 'solo protocollo', 'mo protocollar'),
    'ignore': ('ignorieren', 'ignorer', 'ignorare', 'ignorar'),
    '🚗 Car': ('🚗 Auto', '🚗 Voiture', '🚗 Auto', '🚗 Auto'),
    '🏍️ Motorbike': ('🏍️ Motorrad', '🏍️ Moto', '🏍️ Moto', '🏍️ Moto'),
    '🚲 Bicycle': ('🚲 Velo', '🚲 Vélo', '🚲 Bicicletta', '🚲 Velo'),
    '🚚 Van / truck': ('🚚 Lieferwagen / Lastwagen', '🚚 Camionnette / camion', '🚚 Furgone / camion', '🚚 Furgun / camiun'),
    'Car': ('Auto', 'Voiture', 'Auto', 'Auto'),
    'Motorbike': ('Motorrad', 'Moto', 'Moto', 'Moto'),
    'Bicycle': ('Velo', 'Vélo', 'Bicicletta', 'Velo'),
    'Van / truck': ('Lieferwagen', 'Camionnette', 'Furgone', 'Furgun'),
    'Fox': ('Fuchs', 'Renard', 'Volpe', 'Vulp'),
    'Roe deer': ('Reh', 'Chevreuil', 'Capriolo', 'Chavriel'),
    'Badger': ('Dachs', 'Blaireau', 'Tasso', 'Tais'),
    'Hedgehog': ('Igel', 'Hérisson', 'Riccio', 'Ritsch'),
    'Wild boar': ('Wildschwein', 'Sanglier', 'Cinghiale', 'Portg selvadi'),
    'Red deer': ('Hirsch', 'Cerf', 'Cervo', 'Tschierv'),
    'Hare': ('Hase', 'Lièvre', 'Lepre', 'Lieur'),
    'Marten': ('Marder', 'Martre', 'Martora', 'Fiergna'),
    'Wolf': ('Wolf', 'Loup', 'Lupo', 'Luf'),
    'Lynx': ('Luchs', 'Lynx', 'Lince', 'Luf tschervé'),
    'Squirrel': ('Eichhörnchen', 'Écureuil', 'Scoiattolo', 'Squirel'),
    'Chamois': ('Gämse', 'Chamois', 'Camoscio', 'Chamutsch'),
    'Ibex': ('Steinbock', 'Bouquetin', 'Stambecco', 'Capricorn'),
    'Cat': ('Katze', 'Chat', 'Gatto', 'Giat'),
    'Dog': ('Hund', 'Chien', 'Cane', 'Chaun'),
    'Bird': ('Vogel', 'Oiseau', 'Uccello', 'Utschè'),
    'Horse': ('Pferd', 'Cheval', 'Cavallo', 'Chaval'),
    'Sheep': ('Schaf', 'Mouton', 'Pecora', 'Nuorsa'),
    'Cow': ('Kuh', 'Vache', 'Mucca', 'Vatga'),
    'Bear': ('Bär', 'Ours', 'Orso', 'Urs'),
    'Elephant': ('Elefant', 'Éléphant', 'Elefante', 'Elefant'),
    'Zebra': ('Zebra', 'Zèbre', 'Zebra', 'Zebra'),
    'Giraffe': ('Giraffe', 'Girafe', 'Giraffa', 'Giraffa'),
    'Animal': ('Tier', 'Animal', 'Animale', 'Animal'),
    'Backpack': ('Rucksack', 'Sac à dos', 'Zaino', 'Satgados'),
    'Bag': ('Tasche', 'Sac', 'Borsa', 'Tastga'),
    'Suitcase': ('Koffer', 'Valise', 'Valigia', 'Valischa'),
    'Umbrella': ('Schirm', 'Parapluie', 'Ombrello', 'Parasoli'),
    'Chair': ('Stuhl', 'Chaise', 'Sedia', 'Sutga'),
    'Bench': ('Bank', 'Banc', 'Panchina', 'Banc'),
    'Skateboard': ('Skateboard', 'Skateboard', 'Skateboard', 'Skateboard'),
    'Surfboard': ('Surfbrett', 'Planche de surf', 'Tavola da surf', 'Aissa da surf'),
    'Skis': ('Ski', 'Skis', 'Sci', 'Skis'),
    'Ball': ('Ball', 'Ballon', 'Palla', 'Balla'),
    'Object': ('Gegenstand', 'Objet', 'Oggetto', 'Object'),
    'Parcel': ('Paket', 'Colis', 'Pacco', 'Pachet'),
    'Parcel put down': ('Paket abgelegt', 'Colis déposé', 'Pacco depositato', 'Pachet deponì'),
    '{x} seen': ('{x} gesehen', '{x} vu', '{x} visto', '{x} vis'),
    '{x} left behind': ('{x} liegen gelassen', '{x} oublié', '{x} lasciato', '{x} laschà enavos'),
    '{x} left behind {where}': ('{x} {where} liegen gelassen', '{x} oublié {where}', '{x} lasciato {where}', '{x} laschà enavos {where}'),
    '{x} gone': ('{x} weg', '{x} disparu', '{x} sparito', '{x} davent'),
    'AI': ('KI', 'IA', 'IA', 'IA'),
    'waiting for movement (profile)': ('wartet auf Bewegung (Profil)', 'attend un mouvement (profil)', 'attende movimento (profilo)', 'spetga sin moviment (profil)'),
    'One choice for what MoveEye reports and how much the AI computes: Night at the tent, Garden by day, House watch, Save battery. A schedule can choose a profile (field «Detection profile»), the battery too. «Own settings» = as before.':
        ('Eine Wahl dafür, was MoveEye meldet und wie viel die KI rechnet: Nacht am Zelt, Garten tagsüber, Hausüberwachung, Akku sparen. Ein Zeitplan kann ein Profil wählen (Feld «Erkennungsprofil»), der Akku auch. «Eigene Einstellungen» = wie bisher.',
         'Un choix pour ce que MoveEye signale et combien l’IA calcule : Nuit à la tente, Jardin le jour, Surveillance de la maison, Économiser la batterie. Un horaire peut choisir un profil (champ « Profil de détection »), la batterie aussi. « Réglages propres » = comme avant.',
         'Una scelta per ciò che MoveEye segnala e quanto calcola l’IA: Notte alla tenda, Giardino di giorno, Sorveglianza casa, Risparmiare batteria. Un programma può scegliere un profilo (campo «Profilo di rilevamento»), anche la batteria. «Impostazioni proprie» = come finora.',
         'Ina tscherna per quai che MoveEye annunzia e quant che la IA quinta: Notg tar la tenda, Iert di, Survegliaziun da la chasa, Spargnar accu. In plan d’urari po tscherner in profil (champ «Profil d’identificaziun»), l’accu er. «Atgnas configuraziuns» = sco fin ussa.'),
    'Night at the tent for camping nights on the battery.': ('Nacht am Zelt für Camping-Nächte am Akku.', 'Nuit à la tente pour les nuits de camping sur batterie.', 'Notte alla tenda per le notti in campeggio a batteria.', 'Notg tar la tenda per notgs da campadi cun l’accu.'),
    'Below the threshold MoveEye switches to «Save battery» by itself (only persons, the AI seldom) and back when the battery charges or is 5 % above it.':
        ('Unter der Schwelle wechselt MoveEye selbst auf «Akku sparen» (nur Personen, die KI selten) und zurück, sobald der Akku lädt oder 5 % darüber ist.',
         'Sous le seuil, MoveEye passe de lui-même à « Économiser la batterie » (seulement les personnes, l’IA rarement) et revient dès que la batterie charge ou dépasse le seuil de 5 %.',
         'Sotto la soglia MoveEye passa da solo a «Risparmiare batteria» (solo persone, l’IA raramente) e torna quando la batteria si carica o è 5 % sopra.',
         'Sut il limit mida MoveEye sez a «Spargnar accu» (mo persunas, la IA darar) e turna, uschespert che l’accu chargia u è 5 % sur il limit.'),
    'On for battery operation.': ('Ein beim Betrieb mit Akku.', 'Activé sur batterie.', 'Acceso a batteria.', 'Envidà cun l’accu.'),
    'Only in «House watch»: a new thing that lies still in the zone for parcels for a few minutes (nobody next to it) - one message with the picture.':
        ('Nur in «Hausüberwachung»: ein neuer Gegenstand, der ein paar Minuten still in der Zone für Pakete liegt (niemand daneben) – eine Meldung mit Bild.',
         'Seulement en « Surveillance de la maison » : un nouvel objet immobile quelques minutes dans la zone des colis (personne à côté) – un message avec l’image.',
         'Solo in «Sorveglianza casa»: un oggetto nuovo fermo per qualche minuto nella zona dei pacchi (nessuno accanto) – un messaggio con l’immagine.',
         'Mo en «Survegliaziun da la chasa»: ina chaussa nova che resta in pèr minutas en la zona per pachets (nagin sper) – in messadi cun maletg.'),
    'On.': ('Ein.', 'Activé.', 'Acceso.', 'Envidà.'),
    'Off.': ('Aus.', 'Désactivé.', 'Spento.', 'Stizzà.'),
    'Only log.': ('Nur protokollieren.', 'Seulement journal.', 'Solo protocollo.', 'Mo protocollar.'),
    'Only in «House watch»: a backpack, bag or suitcase that stays where somebody put it down.':
        ('Nur in «Hausüberwachung»: ein Rucksack, eine Tasche oder ein Koffer, der liegen bleibt, wo ihn jemand abgestellt hat.',
         'Seulement en « Surveillance de la maison » : un sac à dos, un sac ou une valise qui reste là où quelqu’un l’a posé.',
         'Solo in «Sorveglianza casa»: uno zaino, una borsa o una valigia che resta dove qualcuno l’ha lasciato.',
         'Mo en «Survegliaziun da la chasa»: in satgados, ina tastga u ina valischa che resta, nua ch’insatgi l’ha deponì.'),
    'In «House watch» and «Garden by day»: a bike, cool box or chair that was there for a while (or was remembered with «Remember now») disappears.':
        ('In «Hausüberwachung» und «Garten tagsüber»: ein Velo, eine Kühlbox oder ein Stuhl, der eine Weile da war (oder mit «Jetzt merken» gemerkt wurde), verschwindet.',
         'En « Surveillance de la maison » et « Jardin le jour » : un vélo, une glacière ou une chaise présent depuis un moment (ou mémorisé avec « Mémoriser ») disparaît.',
         'In «Sorveglianza casa» e «Giardino di giorno»: una bici, una borsa frigo o una sedia che c’era da un po’ (o memorizzata con «Memorizza ora») sparisce.',
         'En «Survegliaziun da la chasa» ed «Iert di»: in velo, in box da fraid u ina sutga ch’è stada là in temp (u memorisada cun «Memorisar ussa») svanescha.'),
    'A bigger own model (file moveeye_model_gross.onnx) only in the profiles House and Garden. Off until it has been measured on the Pi (time per picture, temperature, battery).':
        ('Ein grösseres eigenes Modell (Datei moveeye_model_gross.onnx) nur in den Profilen Haus und Garten. Aus, bis es am Pi gemessen ist (Zeit pro Bild, Temperatur, Akku).',
         'Un modèle propre plus grand (fichier moveeye_model_gross.onnx) seulement dans les profils Maison et Jardin. Désactivé tant qu’il n’a pas été mesuré sur le Pi (temps par image, température, batterie).',
         'Un modello proprio più grande (file moveeye_model_gross.onnx) solo nei profili Casa e Giardino. Spento finché non è misurato sul Pi (tempo per immagine, temperatura, batteria).',
         'In agen model pli grond (datoteca moveeye_model_gross.onnx) mo en ils profils Chasa ed Iert. Stizzà fin ch’el è mesirà sin il Pi (temp per maletg, temperatura, accu).'),
    'Per type of vehicle: report (push message, in the profile «House watch»), only log, or ignore.':
        ('Je Fahrzeugart: melden (Push-Nachricht, im Profil «Hausüberwachung»), nur protokollieren oder ignorieren.',
         'Par type de véhicule : signaler (notification push, dans le profil « Surveillance de la maison »), seulement journal ou ignorer.',
         'Per tipo di veicolo: segnalare (notifica push, nel profilo «Sorveglianza casa»), solo protocollo o ignorare.',
         'Per tip da vehichel: annunziar (avis push, en il profil «Survegliaziun da la chasa»), mo protocollar u ignorar.'),
}
for _k, _v in _HX_OBJPROF.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
prof_web_de_refresh()

# ---- the manual (HELP_PAGE): Detection, German and English --------------------------------------------------------------------
_OP_HELP = (
    ('<section id="detect" data-icon="🎯"><h2>Erkennung</h2>',
     "<p><b>🎛️ Erkennungsprofil:</b> Eine Wahl dafür, was MoveEye meldet und wie viel die KI rechnet (Einstellungen → Erkennung). "
     "<i>🏕️ Nacht am Zelt</i>: Personen und grosse Tiere (Reh, Wildschwein, Fuchs, Dachs …), die KI schaut nur bei Bewegung – spart viel. "
     "<i>🌳 Garten tagsüber</i>: Personen und alle Tiere mit Namen («🦊 Fuchs beim Zelt»), gemerkte Dinge werden bewacht. "
     "<i>🏠 Hausüberwachung</i>: Personen, Fahrzeuge, «📦 Paket vor der Tür», liegen gelassene und verschwundene Dinge (Prüfung etwa jede Minute). "
     "<i>🔋 Akku sparen</i>: nur Personen, die KI selten, kleine Bilder. Wechsel von Hand, per Zeitplan (Feld «Erkennungsprofil») oder bei tiefem Akku. "
     "Ohne Profil bleibt alles wie bisher. Fahrzeuge je Art (Auto, Motorrad, Velo, Lieferwagen): melden, nur protokollieren oder ignorieren "
     "(Erkennung → Fahrzeugfilter). Namen der Wildtiere kommen vom Tierarten-Modell oder vom eigenen Modell mit Wildtier-Klassen – "
     "das Standard-Modell kennt Fuchs, Reh, Dachs, Igel und Wildschwein nicht. Ein Paket erkennt MoveEye als neuen Gegenstand, der still liegen bleibt.</p>"),
    ('<section id="detect" data-icon="🎯"><h2>Detection</h2>',
     "<p><b>🎛️ Detection profile:</b> One choice for what MoveEye reports and how much the AI computes (Settings → Detection). "
     "<i>🏕️ Night at the tent</i>: persons and large animals, the AI only looks at movement - saves a lot. <i>🌳 Garden by day</i>: persons "
     "and all animals with names («🦊 Fox at Tent»), remembered things are watched. <i>🏠 House watch</i>: persons, vehicles, «📦 parcel "
     "at the door», things left behind or gone (checked about once a minute). <i>🔋 Save battery</i>: only persons, the AI seldom, small "
     "pictures. Switch by hand, by a schedule (field «Detection profile») or when the battery is low. Without a profile all stays as before. "
     "Vehicles per type (car, motorbike, bicycle, van): report, only log or ignore (Detection → Vehicle filter). The names of wild animals "
     "come from the species model or from an own model with wildlife classes - the standard model does not know fox, roe deer, badger, "
     "hedgehog and wild boar. A parcel is found as a new object that stays still.</p>"),
)
for _h_old, _h_new in _OP_HELP:
    if _h_old in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_h_old, _h_old + _h_new, 1)


# ---- self-test --------------------------------------------------------------------------------------------------------------
def objprof_selftest():
    """profiles by time / battery, vehicle choices, the state machines of parcel / left behind / gone with made-up
    detections, the energy per profile, the words of the messages"""
    keep_cfg = {k: json.loads(json.dumps(CFG.get(k))) for k in list(_OP_DEF) + ["ai_model"]}
    keep_prof = {k: PROF[k] for k in ("eff", "why", "batt", "over", "sched", "seen_manual", "tick_t", "big_on")}
    with LOCK:
        keep_sched = [dict(s) for s in SCHEDULES]
    keep_zones = [dict(z) for z in ZONES]
    keep_things = (THINGS.tracks, THINGS.n, THINGS.ghosts)
    _save = globals().get("save_settings")
    try:
        globals()["save_settings"] = lambda *a, **k: None
        # 1. energy: no profile = today; every profile at most as costly; things / big model only in House / Garden
        e0 = prof_energy("")
        assert e0 == {"ai_k": 1, "motion_only": False, "proc_max": 0, "things": (), "big": False}, e0
        CFG["ai_model_big"] = True
        for pid in PROFILES:
            e = prof_energy(pid)
            assert e["ai_k"] >= 1 and (e["proc_max"] == 0 or e["proc_max"] <= 320)
            assert bool(e["things"]) == (pid in ("home", "garden")), (pid, e)
            assert e["big"] == (pid in ("home", "garden")), (pid, e)
        assert prof_energy("night")["motion_only"] and prof_energy("battery")["ai_k"] >= 4 and prof_energy("battery")["proc_max"] == 320
        CFG["ai_model_big"] = False
        assert not any(prof_energy(p)["big"] for p in PROFILES)               # ab Werk: never the bigger model
        CFG["obj_pkg_on"] = False
        assert prof_energy("home")["things"] == ("left", "gone")
        CFG["obj_pkg_on"] = True
        # 2. which profile: manual, schedule from 22:00, manual during the schedule, battery low with hysteresis
        CFG.update(det_profile="garden", prof_batt_on=False)
        PROF.update(batt=False, over=None, sched=None, seen_manual=None)
        with LOCK:
            SCHEDULES[:] = [_clean_schedule({"name": "Nacht", "days": list(range(7)), "start": "22:00", "end": "06:00", "profile": "night", "actions": {}}, 0)]
        assert SCHEDULES[0]["profile"] == "night"
        day, night = datetime(2026, 11, 9, 14, 0), datetime(2026, 11, 9, 23, 30)
        assert prof_tick(True, day, {}) == "garden" and PROF["why"] == "manual"
        assert prof_tick(True, night, {}) == "night" and PROF["why"] == "schedule:Nacht"
        assert prof_tick(True, datetime(2026, 11, 10, 5, 59), {}) == "night"          # over midnight
        CFG["det_profile"] = "home"                                                    # by hand during the schedule: wins
        assert prof_tick(True, night, {}) == "home"
        assert prof_tick(True, day, {}) == "home"
        assert prof_tick(True, night, {}) == "night"                                  # the next night: the schedule again
        CFG["prof_batt_on"] = True; CFG["prof_batt_pct"] = 20
        assert prof_tick(True, night, {"on": True, "pct": 19, "on_battery": True}) == "battery" and PROF["why"] == "battery"
        assert prof_tick(True, day, {"on": True, "pct": 23, "on_battery": True}) == "battery"     # hysteresis +5 %
        assert prof_tick(True, day, {"on": True, "pct": 26, "on_battery": True}) == "home"
        assert prof_tick(True, day, {"on": True, "pct": 10, "charging": True}) == "home"         # charging: no switch
        CFG["prof_batt_on"] = False
        assert prof_tick(True, day, {"on": True, "pct": 5, "on_battery": True}) == "home"
        # 3. vehicles per type, the profile caps «report»
        CFG.update(veh_car="report", veh_moto="ignore", veh_bike="log", veh_truck="report")
        assert veh_policy("car", "home") == "report" and veh_policy("car", "night") == "log" and veh_policy("car", "") == "report"
        assert veh_policy("moto", "home") == "ignore" and veh_policy("bike", "home") == "log" and veh_policy("truck", "battery") == "log"
        vw = SeenWatch(confirm_s=1.5, gone_s=120.0, grace_s=30.0)
        assert vw.feed(0.0, {"car": 1}) == [] and vw.feed(2.0, {"car": 1}) == []        # parked at the start: no message
        assert vw.feed(40.0, {"bike": 1}) == [] and vw.feed(42.0, {"bike": 1}) == [("bike", 1)]
        assert vw.feed(43.0, {"bike": 1}) == []                                            # once per arrival
        assert vw.feed(300.0, {"bike": 1}) == [] and vw.feed(302.0, {"bike": 1}) == [("bike", 1)]   # back after 2 min
        # 4. animals: names, large animals at night, all in the garden
        assert wild_canon("red fox;Fuchs") == "fox" and wild_canon("porcupine, hedgehog") == "hedgehog" and wild_canon("wild boar, boar") == "wild boar"
        assert wild_canon("deer") == "roe deer" and wild_canon("badger") == "badger" and wild_canon("dog") == "dog" and wild_canon("toaster") == ""
        assert wild_name("dog", species=("red fox", 0.8), lang="de")[2] == "Fuchs"
        cm = own_ai_classmap(["person", "animal", "fox", "roe deer", "badger", "hedgehog", "wild boar", "dog"])
        assert cm[1] == (OWN_AI_ANIMAL_ID, False) and [c[0] for c in cm[2:7]] == [WILD_IDS[k] for k in WILD_FIVE] and cm[7] == (18, False)
        assert all(COCO_LABELS[WILD_IDS[k]] in ANIMALS for k in WILD_FIVE)
        assert prof_animal_policy("fox", pid="night") == "report" and prof_animal_policy("hedgehog", pid="night") == "log"
        assert prof_animal_policy("hedgehog", pid="garden") == "report" and prof_animal_policy("fox", pid="battery") == "log"
        assert prof_animal_policy("animal", (0, 0, 10, 40), 100, "night") == "report" and prof_animal_policy("animal", (0, 0, 10, 5), 100, "night") == "log"
        # 5. words
        assert obj_push_text("animal", "fox", "Zelt", "de")[:2] == ("🦊", "Fuchs beim Zelt")
        assert obj_push_text("animal", "wild boar", "", "de")[1] == "Wildschwein gesehen"
        assert obj_push_text("package", "", "Tür", "de")[:2] == ("📦", "Paket vor der Tür")
        assert obj_push_text("package", "", "", "de")[1] == "Paket abgelegt"
        assert obj_push_text("left", "backpack", "Zelt", "de")[1] == "Rucksack beim Zelt liegen gelassen"
        assert obj_push_text("gone", "bicycle", "", "de")[1] == "Velo weg"
        assert obj_push_text("vehicle", "moto", "Einfahrt", "de")[1] == "Motorrad bei der Einfahrt"
        assert obj_push_text("animal", "fox", "Tent", "en")[1] == "Fox at Tent" and obj_push_text("animal", "fox", "Velo-Platz", "de")[1] == "Fuchs bei «Velo-Platz»"
        assert obj_push_text("animal", "roe deer", "", "fr")[1] == "Chevreuil vu"
        pk = push_kind({"event": "info", "text": "22:14 · KI 80 %", "info_title": "{name}: Fuchs beim Zelt", "obj_ic": "🦊", "obj_title": "Fuchs beim Zelt"})
        assert pk["ic"] == "🦊" and pk["title"] == "Fuchs beim Zelt" and pk["cls"] == "alarm"
        # 6. things: parcel (stays 2 min in the zone, courier gone), left behind (10 min), gone (remembered, 2 checks)
        ZONES[:] = [{"id": 1, "name": "Tür", "mode": "only", "points": [[0.0, 0.5], [0.5, 0.5], [0.5, 1.0], [0.0, 1.0]]}]
        tw = ThingsWatch(); ok_zone = _obj_pkg_zone
        tw.observe(0, [("bicycle", (0.7, 0.2, 0.2, 0.3), 0.8)], [], ok_zone)                 # there from the start
        box = (0.2, 0.7, 0.1, 0.1)
        assert tw.observe(60, [("object", box, 0.5)], [(0.15, 0.4, 0.2, 0.5)], ok_zone) == []   # the courier stands there
        assert tw.observe(120, [("object", box, 0.5)], [], ok_zone) == []
        ev = tw.observe(180, [("object", box, 0.5)], [], ok_zone)
        assert [k for k, _t in ev] == ["package"], ev
        assert tw.observe(240, [("object", box, 0.5)], [], ok_zone) == []                   # once
        bag = (0.7, 0.7, 0.08, 0.1)                                                           # outside the parcel zone
        tw.observe(300, [("object", box, 0.5), ("backpack", bag, 0.7)], [], ok_zone)
        evs = []
        for i in range(1, 12):
            evs += tw.observe(300 + 60 * i, [("object", box, 0.5), ("backpack", bag, 0.7)], [], ok_zone)
        assert [k for k, _t in evs] == ["left"], evs
        tw2 = ThingsWatch()
        tw2.observe(0, [("bicycle", (0.7, 0.2, 0.2, 0.3), 0.8)], [], ok_zone)
        assert tw2.remember_now() == 1
        assert tw2.observe(60, [], [(0.68, 0.15, 0.25, 0.4)], ok_zone) == []                # somebody in front: no miss
        assert tw2.observe(120, [], [], ok_zone) == []
        ev = tw2.observe(180, [], [], ok_zone)
        assert [k for k, _t in ev] == ["gone"] and not tw2.tracks, ev
        tw3 = ThingsWatch()                                                                    # auto-remember after 30 min
        evs = []
        for i in range(0, 33):
            evs += tw3.observe(60 * i, [("bicycle", (0.6, 0.3, 0.2, 0.3), 0.8)], [], ok_zone, ("gone",))
        assert [k for k, _t in evs] == ["remembered"], evs
        assert [k for k, _t in tw3.observe(33 * 60, [], [], ok_zone, ("gone",)) + tw3.observe(34 * 60, [], [], ok_zone, ("gone",))] == ["gone"]
        assert tw3.observe(0, [("backpack", bag, 0.7)], [], ok_zone, ()) == []               # no checks allowed: nothing
        # 7. the picture side of the things check: a new box appears and stays -> found; light change -> nothing
        rng = np.random.RandomState(3)
        bg = (rng.rand(270, 480) * 60 + 90).astype(np.uint8); bg = cv2.GaussianBlur(bg, (7, 7), 0)
        sc = StaticChange()
        assert sc.update(bg) == [] and sc.update(bg) == []
        fr = bg.copy(); cv2.rectangle(fr, (100, 180), (150, 230), 30, -1); cv2.rectangle(fr, (100, 180), (150, 230), 230, 2)
        assert sc.update(fr) == []                                                             # first time: not yet still
        got = sc.update(fr)
        assert len(got) == 1 and abs(got[0][0] - 100 / 480.0) < 0.03 and abs(got[0][1] - 180 / 270.0) < 0.03, got
        assert sc.update(cv2.add(fr, 60)) == []                                                # a lamp: learnt again, no thing
        sc2 = StaticChange(); sc2.update(bg); sc2.update(bg)
        assert sc2.update(fr, persons=[(0.18, 0.6, 0.15, 0.3)]) == [] and sc2.update(fr, persons=[(0.18, 0.6, 0.15, 0.3)]) == []
        p_ = sc.patch(fr, got[0])
        assert sc.same_patch(fr, got[0], p_) and not sc.same_patch(bg, got[0], p_)            # remembered thing: there / gone
        # 8. the AI gate: «Night» skips the AI without movement, «Save battery» every 4th time only
        class _A:
            boxes, objects, net, prof_motion_t = [], [], None, 0.0
        a_ = _A(); calls = []
        base = globals()["_prof_detect_base"]
        try:
            globals()["_prof_detect_base"] = lambda self, f: calls.append(1) or []
            dm = DEMO.get("on"); DEMO["on"] = False
            PROF["eff"] = "night"
            _prof_detect(a_, None); assert not calls
            a_.prof_motion_t = time.time(); _prof_detect(a_, None); assert len(calls) == 1
            PROF["eff"] = "battery"; calls.clear()
            for _i in range(8):
                _prof_detect(a_, None)
            assert len(calls) == 2, calls
            PROF["eff"] = ""; calls.clear()
            for _i in range(3):
                _prof_detect(a_, None)
            assert len(calls) == 3
            PROF["eff"] = "battery"; PROF["tick_t"] = time.time()
            assert prof_proc_width(640) == 320 and prof_proc_width(256) == 256
        finally:
            globals()["_prof_detect_base"] = base; DEMO["on"] = dm
    finally:
        globals()["save_settings"] = _save
        for k, v in keep_cfg.items():
            CFG[k] = v
        PROF.update(keep_prof)
        with LOCK:
            SCHEDULES[:] = keep_sched
        ZONES[:] = keep_zones
        THINGS.tracks, THINGS.n, THINGS.ghosts = keep_things
    return "profiles by time / battery, vehicles per type, parcel / left behind / gone, energy per profile, push words"


SELFTEST_EXTRA.append(("Objects and profiles: profiles by schedule / battery, vehicles per type, parcel / left / gone, energy (639zz)", objprof_selftest))
