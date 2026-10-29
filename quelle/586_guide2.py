#@ MoveEye – Teil 586: Guide 2 – ein System für Einrichtung (schnell / ausgiebig), Rundgänge, Einfach/Experte pro Seite, Tipps & Tricks, «?» bei Einstellungen, Tipp des Tages und «Auf Werkseinstellungen zurücksetzen». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (29.10.2026, Konzept-Check «one system»): the setup assistant (/api/setup, before: 4 steps), the first-open
# explanations (515), Simple / Expert, «Platz einrichten» (317), the walk test (415), the protection assistant (135) and
# the push test are ONE guide now:
#   * guide after (re)install: «Quick (about 5 min) or thorough?» - quick = basics, push, camera + place, protection +
#     walk test; thorough adds the other steps. Every step can be skipped, the state is kept on the Pi (CFG guide2), so
#     «Continue later» works from every device and from the window. Hardware steps are skipped when the part is missing.
#   * tours (coach marks) per page: web 516, window 584. Seen = web_ui «mw-tours-seen» (same on every device).
#   * Simple / Expert per page: web_ui «mw-page-mode» {page: "simple"|"expert"}; without an entry the default CFG ui_simple
#     (the choice in the guide). /api/schema?simple=0|1 uses it (simple_hidden, 130).
#   * «?» next to a setting: g2_help(key) from the hand-written texts below, the label and the topic explanation (515).
#   * tip of the day: a function that was never used (g2_tip_today), once a day, switch tip_of_day.
#   * factory reset (Mehr → System): everything back to the defaults and setup_done False, BUT Wi-Fi / own Wi-Fi / remote
#     access, the ntfy push channel and the own AI model + learning data stay. Recordings, diary and log are deleted. A
#     copy of the old settings is kept first (motionwatch_settings.before_reset_<time>.json, downloadable).
# ----------------------------------------------------------------------------
G2_DEF = {"mode": "", "step": "", "done": [], "skipped": [], "paused": False, "finished": False, "t": 0.0}
for _k, _v in (("guide2", G2_DEF), ("tours_auto", True), ("tip_of_day", True), ("tip_day_last", "")):
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
TOGGLES.extend([
    ("Setup", "tours_auto", "Tour of a page on its first visit (dims the screen and shows the controls one after another)"),
    ("Setup", "tip_of_day", "Tip of the day (a function you have not used yet)"),
])
SIMPLE_KEYS.update({"tours_auto", "tip_of_day"})
VIEW_GET = VIEW_GET + ("/g2/",)                       # the script of the tours / tips also for viewers (only texts)

# ---- the steps of the guide ------------------------------------------------------------------------------------------
G2_QUICK = ["basics", "push", "camera", "protect"]
G2_FULL = ["basics", "push", "camera", "view", "zones", "protect", "schedules", "lightsiren", "servos", "ai", "thermal", "battery", "sim", "tours"]
G2_STEPS = {   # id: (icon, English title, needs hardware (any of))
    "basics": ("🌐", "Basics", ()), "push": ("🔔", "Push messages to the phone", ()), "camera": ("📷", "Camera test and place", ()),
    "view": ("🧭", "Simple or Expert", ()), "zones": ("✏", "Fine-tune the zones", ()), "protect": ("🛡", "Protection and walk test", ()),
    "schedules": ("🕘", "Night time and schedules", ()), "lightsiren": ("💡", "Light and siren test", ("light", "speaker")),
    "servos": ("🎯", "Head and calibration", ("head",)), "ai": ("🤖", "AI model", ()), "thermal": ("🌡", "Thermal camera", ("thermal",)),
    "battery": ("🔋", "Battery", ()),      # a powerbank cannot be detected: the step asks for it
    "sim": ("🎮", "3D simulator", ()), "tours": ("💡", "Tours and tips", ()),
}
G2_HW_NAMES = {"light": "light", "speaker": "loudspeaker", "head": "pan / tilt head", "thermal": "thermal camera", "battery": "battery (UPS)"}


def g2_hw():
    """which hardware is there (the guide skips the steps of missing parts). The simulator counts as hardware."""
    sim = False
    try:
        sim = bool(CFG.get("sim_on") and sim_live())
    except Exception:
        pass
    try:
        head = bool(live_has_head())
    except Exception:
        head = False
    try:
        spk = bool(out_selected())
    except Exception:
        spk = False
    b = STATE.get("battery") or {}
    return {"head": head, "light": bool(CFG.get("light_white_out") or CFG.get("light_ir_out") or sim
                                        or str(STATE.get("servo_backend") or "").startswith("pca9685")),
            "speaker": spk or sim, "thermal": bool(CFG.get("thermal_source")) or STATE.get("thermal") == "connected",
            "battery": bool(CFG.get("ups_on") or b.get("on")), "sim": sim}


def g2_steps(mode=None, lang=None):
    mode = mode or CFG["guide2"].get("mode") or "quick"
    hw = g2_hw()
    out = []
    for sid in (G2_FULL if mode == "full" else G2_QUICK):
        ic, title, needs = G2_STEPS[sid]
        miss = [n for n in needs if not hw.get(n)]
        auto = len(miss) == len(needs) and bool(needs)      # skipped only when ALL of its parts are missing
        out.append({"id": sid, "icon": ic, "title": tr(title, lang),
                    "auto_skip": (tr("not connected", lang) + ": " + ", ".join(tr(G2_HW_NAMES[n], lang) for n in miss)) if auto else ""})
    return out


def g2_state(lang=None):
    g = dict(G2_DEF); g.update(CFG.get("guide2") or {})
    steps = g2_steps(g.get("mode") or "quick", lang)
    ids = [s["id"] for s in steps]
    left = [i for i in ids if i not in g["done"] and i not in g["skipped"] and not next(s for s in steps if s["id"] == i)["auto_skip"]]
    return dict(g, steps=steps, hw=g2_hw(), left=left, setup_done=bool(CFG["setup_done"]), update_fast=bool(CFG.get("update_fast")),
                open=bool(g.get("mode")) and not g.get("finished"), default_simple=bool(CFG.get("ui_simple")),
                use_case=CFG.get("use_case") or "", tours_auto=bool(CFG.get("tours_auto", True)), tip_of_day=bool(CFG.get("tip_of_day", True)))


def g2_action(d, who="web"):
    """the guide: start / step / done / skip / pause / resume / finish / again / view / place_time / tours_reset (POST /api/setup step=guide)"""
    a = str(d.get("action") or "")
    g = dict(G2_DEF); g.update(CFG.get("guide2") or {})
    sid = str(d.get("id") or "")
    if a == "start":
        mode = "full" if d.get("mode") == "full" else "quick"
        keep = g.get("mode") == mode and not g.get("finished")
        g = dict(G2_DEF, mode=mode, done=g["done"] if keep else [], skipped=g["skipped"] if keep else [], t=time.time())
        log_event("sys", f"Setup guide started ({mode}, {who})")
    elif a in ("done", "skip"):
        if sid not in G2_STEPS:
            return False, "unknown step"
        lst = g["done"] if a == "done" else g["skipped"]
        other = g["skipped"] if a == "done" else g["done"]
        if sid not in lst:
            lst.append(sid)
        if sid in other:
            other.remove(sid)
        g["step"] = sid
    elif a == "step":
        if sid not in G2_STEPS:
            return False, "unknown step"
        g["step"] = sid; g["paused"] = False
    elif a == "pause":
        g["paused"] = True
        CFG["setup_done"] = True                     # the start page does not ask again by itself - «continue» under Mehr
        log_event("sys", f"Setup guide paused - continue later ({who})")
    elif a == "resume":
        g["paused"] = False
    elif a == "finish":
        g["finished"] = True; g["paused"] = False
        CFG["setup_done"] = True
        log_event("sys", f"Setup guide finished ({g.get('mode') or 'quick'}, {len(g['done'])} steps done, {who})")
    elif a == "again":
        g = dict(G2_DEF)
        CFG["setup_done"] = False
    elif a == "view":                                # «Simple» or «Expert» as the default of every page + what it is for
        if "use" in d:
            ok, err = use_case_set(str(d.get("use") or ""), who)
            if not ok:
                return ok, err
        if "simple" in d:
            CFG["ui_simple"] = bool(d.get("simple"))
            web_ui_update({}, ["mw-page-mode"])      # the choice is the new default of every page
    elif a == "place_time":
        try:
            lat, lon = d.get("lat"), d.get("lon")
            if lat is not None and lon is not None and str(lat) != "" and str(lon) != "":
                lat, lon = float(lat), float(lon)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180 and math.isfinite(lat) and math.isfinite(lon)):
                    return False, "invalid value"
                CFG["latitude"], CFG["longitude"] = round(lat, 4), round(lon, 4)
                log_event("sys", f"Location set in the setup guide: {lat:.4f}, {lon:.4f}")
        except (TypeError, ValueError):
            return False, "invalid value"
        if d.get("t"):
            try:
                sync_time_from_client(d.get("t"), str(d.get("tz") or "")[:60], True)
            except Exception:
                pass
    elif a == "tours_reset":
        web_ui_update({}, ["mw-tours-seen"])
        log_event("sys", f"All tours reset ({who})")
    else:
        return False, "unknown action"
    g["t"] = time.time()
    CFG["guide2"] = g
    save_settings()
    return True, ""


# ---- Simple / Expert per page ------------------------------------------------------------------------------------------
_G2_SIMPLE = threading.local()


def page_modes():
    try:
        v = json.loads((CFG.get("web_ui") or {}).get("mw-page-mode") or "{}")
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


def page_simple(page):
    """Simple (True) or Expert (False) on this page: its own choice, otherwise the default (the guide / Settings)"""
    v = page_modes().get(str(page or ""))
    return bool(CFG.get("ui_simple")) if v not in ("simple", "expert") else v == "simple"


def ui_simple_now():
    """what simple_hidden() uses: during /api/schema?simple= the choice of the page, otherwise the default"""
    v = getattr(_G2_SIMPLE, "v", None)
    return bool(CFG.get("ui_simple")) if v is None else v


# ---- «?» next to a setting --------------------------------------------------------------------------------------------
# (explanation, recommendation) - English; the other languages in 633
SET_HELP = {
    "detection_on": ("Motion detection is the base of everything: without it MoveEye sees nothing.", "Leave it on."),
    "sensitivity": ("How small a change in the picture may be to count as movement. Higher = also small and far things, but more false alarms (grass, insects).", "Start in the middle, raise it only if the walk test misses you."),
    "ai_enabled": ("The AI checks every movement: person, animal, car - or nothing. Without it every movement could give an alarm.", "Leave it on."),
    "record": ("A video of every alarm, with a few seconds before.", "On - you see later what really happened."),
    "snapshot_on_person": ("A photo as soon as a person is recognised (smaller than a video, also in the push message).", "On."),
    "record_max_gb": ("How much of the memory card the recordings may use. The oldest are deleted first (⭐ stay).", "About half of the free memory."),
    "notify_on": ("Push messages to your phone at an alarm. Without them you only see the alarms on this page.", "On - set up the app ntfy in the guide."),
    "notify_prealarm": ("A first short message as soon as something moves, before the AI is sure.", "Off if you get too many messages."),
    "webpush_on": ("Messages directly in this browser (without the app ntfy). Only works on https pages.", "Additional to ntfy, not instead."),
    "notify_type": ("How the messages reach you: ntfy (app), Telegram, Pushover or a web address of your own.", "ntfy - free and simple."),
    "notify_url": ("The address of your ntfy channel (server + topic). Like a secret channel name: who knows it gets your alarms.", "Use a long random topic (the guide makes one)."),
    "arm_delay": ("The countdown after «arm» - time to leave the picture without an alarm.", "30 to 60 seconds."),
    "siren_on": ("The siren at an alarm (only in the protection level «Full»).", "On for theft protection, off at the campsite at night (neighbours)."),
    "siren_volume": ("How loud the siren is.", "Test it once with the light and siren test."),
    "light_white_auto": ("When the white light goes on by itself: at an alarm, at night or never.", "At an alarm - it scares and gives a good picture."),
    "light_ir_auto": ("Infrared light: invisible for people and animals, the camera sees in the dark with it.", "Automatic at night."),
    "track_person": ("The head follows a recognised person.", "On if you have a pan / tilt head."),
    "track_motion": ("The head follows everything that moves (also animals, branches).", "Off - «follow persons» is calmer."),
    "patrol": ("The head drives through the saved points and looks round the place by itself.", "On when the place is bigger than the picture."),
    "report_on": ("A short message in the morning: what happened in the night, with the best pictures.", "On."),
    "report_hour": ("The end of the night time: the report comes then, «Guard tonight» ends then.", "The time you usually get up."),
    "diary_on": ("Collects the best picture of every animal visit by itself.", "On - it costs little memory."),
    "eco_on": ("Fewer pictures while all is quiet: the battery lasts longer, the reaction is a little slower.", "On with a battery, off with a power supply."),
    "update_auto": ("New versions are installed by themselves (only signed ones).", "On."),
    "thermal_on": ("The thermal camera finds warm bodies, also in the dark and behind grass.", "On if a thermal camera is connected."),
    "thermal_alarm": ("An alarm from the thermal picture alone (warm body without movement in the normal picture).", "On at night without light."),
    "noise_alarm": ("An alarm when it is loud (the microphone).", "Off at a busy campsite."),
    "nightvision_auto": ("The brighter night picture, switched on by itself when it gets dark.", "On."),
    "lowlight_auto": ("Brightens the picture at dusk.", "On."),
    "device_name": ("The name in the push messages and on the page - helpful with several devices.", "Short, e.g. «Camper» or «Garden»."),
    "net_mode": ("Which network MoveEye uses: home Wi-Fi, its own Wi-Fi or automatic.", "Automatic."),
    "hotspot_ssid": ("The name of the own Wi-Fi of MoveEye (when there is no other network).", "Leave it as it is."),
    "tips_level": ("How many explanations appear the first time something is opened.", "«Normal»; «Off» when you know MoveEye."),
    "use_case": ("What MoveEye is for - «Simple» then shows only the settings that fit.", "Choose it in the guide."),
    "tours_auto": ("Every page shows its tour once on the first visit. The «?» at the top starts it again.", "On while you get to know MoveEye."),
    "tip_of_day": ("Once a day a tip about a function you have not used yet.", "On."),
    "tamper_on": ("Alarm when the camera is covered, turned away or the device is moved.", "On."),
    "rec_keep_days": ("Recordings older than this are deleted by themselves (0 = keep until the memory is full).", "14 to 30 days."),
    "push_pics": ("A picture in the push message.", "On - you see at once what it is."),
    "batt_save_on": ("Below a battery level MoveEye saves power by itself (fewer pictures, the AI less often).", "On with a battery."),
    "login_https_only": ("The password is only accepted over a secure connection (https, the device itself or Tailscale).", "On when you use MoveEye from outside."),
    "lens_check": ("Warns when the lens is dirty, wet or covered.", "On."),
    "weather_on": ("Weather forecast and warnings for the place (needs the location).", "On."),
    "gps_tag": ("Writes the location into the photos.", "Off if you share pictures."),
    "audio_out": ("Which loudspeaker plays the siren and the sounds.", "Test it with the light and siren test."),
    "cam_rotate": ("Turns the picture when the camera is mounted upside down or on its side.", "Look at the live picture and choose what is upright."),
}


def _g2_default_txt(key, lang):
    if key not in DEFAULTS:
        return ""
    v = DEFAULTS[key]
    if isinstance(v, bool):
        return tr("Default", lang) + ": " + tr("on" if v else "off", lang)
    if isinstance(v, (int, float)):
        return tr("Default", lang) + ": " + (str(int(v)) if float(v).is_integer() else str(v))
    if isinstance(v, str) and v:
        try:
            lab = dict(text_choice_pairs(key)).get(v)
        except Exception:
            lab = None
        if lab:
            return tr("Default", lang) + ": " + tr(lab, lang)
    return ""


def g2_help(lang=None):
    """{key: {"x": explanation, "r": recommendation}} for every setting with something to say (all of «Simple»)"""
    L = cur_lang(lang)
    tips = {k[4:]: (xe, xd) for k, _lv, _v, _te, xe, _td, xd in GUIDE_TIPS if k.startswith("sec:")}
    out = {}
    specs = [(s, k, l) for s, k, l in TOGGLES] + [(x[0], x[1], x[2]) for x in SLIDERS] + [(x[0], x[1], x[2]) for x in TEXTS]
    for sec, key, label in specs:
        if key in out:
            continue
        hand = SET_HELP.get(key)
        m_ = re.search(r"\(([^()]{8,})\)\s*$", label or "")
        if not (hand or key in SIMPLE_KEYS or m_):
            continue
        parts = []                                   # the label is the title of the box - the text says more
        sec_txt = tips.get(sec)
        if hand:
            parts.append(tr(hand[0], L))
        elif sec_txt:
            parts.append(sec_txt[1] if L == "de" else tr(sec_txt[0], L))
        else:
            m2 = re.search(r"\(([^()]{8,})\)\s*$", tr(label, L) or "")
            parts.append(m2.group(1) if m2 else tr(label, L))
        rec = tr(hand[1], L) if hand else ""
        dft = _g2_default_txt(key, L)
        out[key] = {"x": " ".join(parts), "r": rec, "d": dft}
    return out


# ---- tip of the day: a function that was never used ------------------------------------------------------------------
def _g2_seen(k):
    try:
        return k in guide_seen()
    except Exception:
        return False


def _g2_place_done():
    try:
        return _place_load() is not None
    except Exception:
        return False


def _g2_walk_done():
    try:
        _walk_load()
        return bool(WALK.get("result"))
    except Exception:
        return False


def _g2_refscan():
    try:
        return bool(refscan_meta())
    except Exception:
        return False


G2_FEATURES = [   # (id, icon, English title, English text, link, used?)
    ("place", "📐", "Set up the place", "MoveEye looks round once and suggests zones, paths and the things to guard.", "/place", _g2_place_done),
    ("walk", "🚶", "Walk test", "Walk past the camera like a visitor: MoveEye beeps at every detection and shows how far it sees.", "/protect", _g2_walk_done),
    ("zones", "✏", "Zones", "Draw areas into the picture: ignore the road, privacy, the sleeping place for the wake-up alarm.", "/zones", lambda: bool(ZONES)),
    ("diary", "📔", "Animal diary", "The best picture of every animal visit, collected by itself - every day on one page.", "/diary", lambda: _g2_seen("page:diary")),
    ("party", "🎲", "Game corner", "Quiz, werewolf and connect four for the phones in the same Wi-Fi - for the campfire.", "/party", lambda: _g2_seen("page:party")),
    ("schedule", "🕘", "Schedules", "Switch features on and off by themselves, e.g. the protection every night from 22:00.", "/settings#sec:Schedule", lambda: bool(SCHEDULES)),
    ("timelapse", "🎞", "Timelapse", "A photo every few minutes - a film of the whole day.", "/settings#sec:Timelapse", lambda: bool(CFG.get("timelapse_on"))),
    ("guest", "👀", "Guest access", "A link for others: only watching, for a limited time.", "/settings#sec:Guest access", lambda: bool(CFG.get("guest_token"))),
    ("backup", "☁", "Backup", "Copy the recordings away from the device (cloud, USB stick) - a thief cannot delete them then.", "/settings#sec:Backup", lambda: CFG.get("backup_type", "off") != "off"),
    ("wake", "⏰", "Wake-up alarm", "Wakes you with a melody and light; wave = snooze, sit up = off.", "/settings#sec:Wake-up alarm", lambda: bool(CFG.get("wake_on"))),
    ("refscan", "🔎", "Reference scan", "The head photographs the place and later sees what is missing or new.", "/protect", _g2_refscan),
    ("sim", "🎮", "3D simulator", "Test MoveEye on the PC without the real place: day, night, weather, animals, people.", "/sim", lambda: bool(CFG.get("sim_on") or CFG.get("sim_url"))),
    ("pin", "🔢", "PIN for disarming", "A thief cannot simply switch MoveEye off - and three wrong PINs give an alarm.", "/protect", lambda: bool(CFG.get("protect_pin"))),
    ("webpush", "🌐", "Messages in the browser", "Alarm messages directly in this browser, without the app.", "/settings#sec:Notifications", lambda: bool(CFG.get("webpush_on"))),
    ("quick", "📄", "Quick guide to print", "One page with the QR codes - for the camper or the neighbours.", "/quick", lambda: _g2_seen("page:help")),
]


def g2_tip_today(lang=None, peek=False):
    """the tip of the day: once a day, a function not used yet (rotating), or None"""
    if not CFG.get("tip_of_day", True) or not CFG["setup_done"]:
        return None
    today = datetime.now().strftime("%Y-%m-%d")
    if not peek and str(CFG.get("tip_day_last") or "").startswith(today):
        return None
    unused = []
    for fid, ic, title, text, href, used in G2_FEATURES:
        try:
            u = used()
        except Exception:
            u = False
        if not u:
            unused.append((fid, ic, title, text, href))
    if not unused:
        return None
    fid, ic, title, text, href = unused[datetime.now().toordinal() % len(unused)]
    return {"id": fid, "icon": ic, "title": tr(title, lang), "text": tr(text, lang), "href": href, "day": today}


def g2_tip_seen(fid=""):
    CFG["tip_day_last"] = datetime.now().strftime("%Y-%m-%d") + " " + str(fid)[:20]
    save_settings()


# ---- factory reset ------------------------------------------------------------------------------------------------------
FACTORY_KEEP = {
    # Wi-Fi, own Wi-Fi (hotspot), network
    "hotspot_on", "hotspot_password", "hotspot_ssid", "net_mode", "net_known", "net_watch", "net_noinet", "net_inet_notify",
    "wifi_count", "wifi_guard", "wifi_guard_thr", "wifi_presence", "wifi_repeater", "wifi_swap",
    # remote access (Tailscale / tunnel / address of the page)
    "web_port", "https_extra", "public_url", "tunnel_on", "tunnel_code", "tunnel_prev_url",
    # the ntfy push channel
    "notify_type", "notify_url", "notify_on",
    # the own AI model and its learning (the AI helper PC belongs to it)
    "ai_model", "ai_own_url", "ai_own_auto", "ai_own_check_day", "fa_learn_auto", "species_model", "helper_use", "helper_url", "helper_code",
    # paths, the language of the page and internal markers (otherwise old migrations / news would run again)
    "record_dir", "storage_path", "lang", "sim_autostart_v2", "dev_phase_done", "app_icon_moveeye_done", "app_icon_orange_done",
    "news_seen_web", "news_seen_tk", "weekcheck_last", "weekrep_last", "report_last_day",
    # updates (Daniel, development phase: the fast test updates must keep working after a reset)
    "update_fast", "update_auto", "update_url", "update_token", "update_unsigned", "update_hour", "update_install",
    "update_install_armed", "update_push", "update_notified",
}
FACTORY_WORD = "ZURÜCKSETZEN"
FACTORY_WORDS = {"ZURÜCKSETZEN", "ZURUECKSETZEN", "RESET", "RÉINITIALISER", "REINITIALISER", "RIPRISTINA", "RESETTAR"}
FACTORY_DATA = ["sightings.json", "sim_diary.jsonl", "alarm_tracks.json", "places.json", "place", "refscan", "gehtest", "logs", "motionwatch.log"]
_BACKUP_RE = re.compile(r"^motionwatch_settings\.before_reset_\d{8}-\d{6}\.json$")


def factory_word(lang=None):
    """the word to type: German «ZURÜCKSETZEN», the other languages «RESET» (both are always accepted)"""
    return FACTORY_WORD if cur_lang(lang) == "de" else "RESET"


def factory_backups():
    try:
        names = sorted((n for n in os.listdir(DATA_DIR) if _BACKUP_RE.match(n)), reverse=True)
    except OSError:
        names = []
    out = []
    for n in names[:10]:
        try:
            out.append({"name": n, "kb": max(1, os.path.getsize(os.path.join(DATA_DIR, n)) // 1024),
                        "when": datetime.strptime(n[33:48], "%Y%m%d-%H%M%S").strftime("%d.%m.%Y %H:%M")})
        except (OSError, ValueError):
            pass
    return out


def factory_backup_path(name):
    n = os.path.basename(str(name or ""))
    p = os.path.join(DATA_DIR, n)
    return p if _BACKUP_RE.match(n) and os.path.isfile(p) else None


def factory_info(lang=None):
    return {"need_pw": web_pw_active(), "need_pin": bool(CFG.get("protect_pin")) and not web_pw_active(),
            "word": factory_word(lang), "backups": factory_backups(), "locked": bool(CFG.get("lock_on")),
            "rec_dir": rec_dir(), "pw_cli": bool(CFG.get("web_password"))}


def factory_check(pw, pin, word):
    if CFG.get("lock_on"):
        return False, "not possible in operator mode"
    if str(word or "").strip().upper() not in FACTORY_WORDS:
        return False, "type the word to confirm"
    if web_pw_active():
        p = str(pw or "")
        ok = (CFG["web_password"] and hmac.compare_digest(p, CFG["web_password"])) or (CFG.get("web_pw_hash") and pw_check(p))
        if not ok:
            return False, "wrong password"
    elif CFG.get("protect_pin") and not protect_pin_ok(pin):
        return False, "wrong PIN"
    return True, ""


def _g2_rm_tree_files(d):
    """deletes the files below the folder d (recordings), not d itself; counts them"""
    n = 0
    d = os.path.abspath(d)
    bad = {os.path.abspath(os.sep), os.path.abspath(os.path.expanduser("~")), os.path.abspath(DATA_DIR), os.path.abspath(HERE)}
    if d in bad or len([p for p in d.split(os.sep) if p]) < 2 or not os.path.isdir(d):
        return 0
    for root, dirs, files in os.walk(d, topdown=False):
        for f in files:
            try:
                os.remove(os.path.join(root, f)); n += 1
            except OSError:
                pass
        for x in dirs:
            try:
                os.rmdir(os.path.join(root, x))
            except OSError:
                pass
    return n


def factory_reset(who="web"):
    """everything back to the defaults (see FACTORY_KEEP), recordings / diary / log deleted. Returns (ok, err, backup name)."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"motionwatch_settings.before_reset_{stamp}.json"
    try:
        with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
            json.dump(settings_data(), f, ensure_ascii=False, indent=1)
        os.chmod(os.path.join(DATA_DIR, name), 0o600)
    except OSError as e:
        return False, f"could not write the backup copy: {e}", ""
    try:
        if CFG.get("armed"):
            disarm()
    except Exception:
        pass
    try:
        if walktest_on():
            walktest_stop("reset")
    except Exception:
        pass
    base = globals().get("FACTORY_CFG") or DEFAULTS
    for k in list(CFG.keys()):
        if k in VOLATILE or k in FACTORY_KEEP or k.startswith("update_") or k not in base:
            continue
        CFG[k] = __import__("copy").deepcopy(base[k])
    CFG["setup_done"] = False
    CFG["dev_phase_done"] = True                     # never again «fast updates on once» - the kept value of update_fast counts
    CFG["guide2"] = json.loads(json.dumps(G2_DEF))
    WAYPOINTS[:] = []; ZONES[:] = []; SCHEDULES[:] = []
    try:
        RELAYS[:] = default_relays()
    except Exception:
        RELAYS[:] = []
    SCHED["base"].clear(); SCHED["manual"].clear()
    _PW_OK.clear()
    # what is deleted: recordings (with diary pictures and timelapse), the diary list, the log, place / reference scan
    n_rec = _g2_rm_tree_files(rec_dir())
    for nm in FACTORY_DATA:
        p = os.path.join(DATA_DIR, nm)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass
    for fn in ("SIGHT", "PLACE", "PLACES", "_ATR"):
        try:
            v = globals().get(fn)
            if fn == "SIGHT":
                v["list"] = []; v["loaded"] = True
            elif fn == "PLACE":
                v["rec"] = None; v["loaded"] = True
            elif fn == "PLACES":
                v["names"] = None
            elif fn == "_ATR":
                ALARM_TRACKS.clear(); v["loaded"] = True
        except Exception:
            pass
    try:
        WALK["result"] = None
    except Exception:
        pass
    with LOCK:
        STATE["events"].clear()
    save_settings_now()
    HW_REINIT["want"] = True; SETTINGS_GEN["n"] += 1
    log_event("sys", f"Factory reset ({who}): settings back to the defaults, {n_rec} recordings deleted. Kept: Wi-Fi, remote access, push channel, own AI model. Old settings: {name}")
    return True, "", name


# ---- the window and the web page: data for the script /g2/ui.js -----------------------------------------------------
def g2_routes(app, watch, reply, body):
    from flask import request, Response, send_file
    for p in ("/api/factory",):
        LOCK_DENY_PATHS.add(p); APPKEY_DENY_PATHS.add(p)

    @app.route("/g2/ui.js")
    def g2_ui_js():
        L = norm_lang(request.args.get("lang") or CFG["lang"])
        return Response(g2_js(L), mimetype="application/javascript", headers={"Cache-Control": "no-cache"})

    @app.route("/api/g2", methods=["GET", "POST"])
    def api_g2():
        """for every page (also viewers: read only): tours seen, tip of the day"""
        lang = norm_lang(request.args.get("lang") or CFG["lang"])
        if request.method == "POST":
            d = body()
            if d.get("action") == "tip_seen":
                g2_tip_seen(d.get("id")); return reply({"ok": True})
            return reply({"ok": False, "error": "unknown action"}, 400)
        return reply({"ok": True, "tip": g2_tip_today(lang), "guide": g2_state(lang), "modes": page_modes(),
                      "default_simple": bool(CFG.get("ui_simple"))})

    @app.route("/api/factory", methods=["GET", "POST"])
    def api_factory():
        lang = norm_lang(request.args.get("lang") or CFG["lang"])
        if request.method == "GET":
            return reply(dict(factory_info(lang), ok=True))
        d = body(); lang = norm_lang(d.get("lang") or lang)
        ok, err = factory_check(d.get("password"), d.get("pin"), d.get("word"))
        if not ok:
            return reply({"ok": False, "error": tr_err(err, lang)}, 400)
        ok, err, name = factory_reset("web " + (request.remote_addr or "?"))
        return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "backup": name}, 200 if ok else 500)

    @app.route("/api/factory/backup/<name>")
    def api_factory_backup(name):
        p = factory_backup_path(name)
        if not p:
            return Response("not found", 404)
        return send_file(p, mimetype="application/json", as_attachment=True, download_name=os.path.basename(p), max_age=0)
