#@ MoveEye – Teil 579a: Push-Nachrichten neu geordnet (Logik): Kanäle als Karten, Stufen «Nur Personen · Personen + Tiere · Alles», Ruhezeiten, Bilder mit / klein / ohne, Stichwort als ein Feld, kurze Beschriftungen, Übernahme alter Einstellungen, /api/push. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026, menu review «Push-Nachrichten»): the section was 31 settings one below the other. Now:
#   Kopf      «Push senden» (notify_on), a status line («2 Kanäle · Test ✓»), «Alle testen»
#   Wohin     one card per channel: ntfy · Web-Push · Telegram · Pushover · E-Mail · Webhook · SMS. ntfy, Telegram and
#             Webhook are the «main channel» (only one of them: CFG notify_type, they share the retries and the outbox);
#             the select «Art der Benachrichtigung» is gone - the type follows the card that is switched on. New key
#             main_push_on (False = none of the three). ntfy and Webhook share notify_url: switching keeps the address of
#             the other one in push_url_<type> and brings it back (nothing is ever lost).
#   Was       push_level: persons (only person alarms) · animals (+ warm bodies of the thermal camera) · all (+ noise,
#             default = the behaviour up to now; the switches «Voralarm» and «Geräusch: Push» still apply on top).
#             Sabotage, theft, sensor / system alarms and notes always pass (they are no detection class).
#             push_pics: with · small (about 640 px) · text (without) - merges «Voralarm mit kleinem Bild».
#   Wann      the two pauses, quiet hours (quiet_on, quiet_windows, quiet_persons): no alarm push in the windows (the alarm
#             is still logged / recorded), on the clock of the simulator while it is connected (sim_now, 285).
#   Erweitert keyword (one field: empty = off), buttons, symbols, page address, info messages, shortcuts, message texts.
# The web page (531a) and the window (571a) build the same structure; translations + «?» texts in 639a.
# ----------------------------------------------------------------------------

# ---- defaults ------------------------------------------------------------------------------------------------------------
_PX_DEF = {"main_push_on": True, "push_level": "all", "quiet_on": False, "quiet_persons": False,
           "quiet_windows": [{"from": "08:00", "to": "18:00", "days": [0, 1, 2, 3, 4, 5, 6]}],
           "push_url_ntfy": "", "push_url_webhook": "", "push_cards": []}
for _k, _v in _PX_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
# 6.: new installations start with ntfy (before: webhook). Old settings files always contain notify_type; a file without
# it (very old export) gets «webhook» back in push_migrate() when it has an address.
if DEFAULTS.get("notify_type") == "webhook" and CFG.get("notify_type") == "webhook":
    CFG["notify_type"] = "ntfy"
DEFAULTS["notify_type"] = "ntfy"
try:
    USER_SETTINGS_DENY.update({"main_push_on", "push_url_ntfy", "push_url_webhook", "quiet_windows"})
except NameError:
    pass

PUSH_LEVELS = (("persons", "Only persons"), ("animals", "Persons + animals"), ("all", "Everything"))
PUSH_CHANNELS = ("ntfy", "webpush", "telegram", "pushover", "email", "webhook", "sms")
PUSH_MAIN = ("ntfy", "telegram", "webhook")
# which detection class an event belongs to (the level decides); None = always (sabotage, sensors, notes, tests)
PUSH_CLASS = {"person": "person", "warm": "animal", "noise": "other", "prealarm": None, "tamper": None, "info": None, "test": None}
_PX_LEVEL_HAS = {"persons": {"person"}, "animals": {"person", "animal"}, "all": {"person", "animal", "other"}}

# ---- the schema: new entries, shorter labels (≤ ~40 characters; the examples went into the «?», 639a) -----------------------
TOGGLES.extend([
    ("Notifications", "quiet_on", "Quiet hours (no alarm push)"),
    ("Notifications", "quiet_persons", "Report persons anyway"),
])
_sx_put_after(TEXTS, "push_pics", ("Notifications", "push_level", "What is reported", "enum", "push_levels"))
TEXT_SPECS["push_level"] = ("enum", "push_levels")
SIMPLE_KEYS.update({"push_level", "quiet_on", "quiet_persons", "push_pics"})
SX_PUSH_PICS = (("with", "with picture"), ("small", "small picture"), ("text", "without picture"))     # 578 reads it when the choices are asked

_PX_LABELS = {   # key: short English label (the old long one is in the «?» now)
    "notify_on": "Send push messages", "notify_prealarm": "Pre-alarm at the first movement",
    "browser_alarm": "Alarm sound in open browsers", "notify_network": "Message when the Pi joins a network",
    "notify_remote": "Message when somebody watches remotely", "webpush_on": "Web push (this device)", "pushover_on": "Pushover",
    "msg_icons": "Symbols in messages (🚶 🦊 🛑)", "msg_keyword_on": "Keyword at the start", "email_on": "E-mail",
    "pushover_emergency": "Emergency alarm (repeats until confirmed)", "push_actions": "Buttons: False alarm · Siren · Off",
    "alarm_confirm2": "Double confirmation of person alarms",
    "notify_url": "Address (server/topic)", "telegram_token": "Bot token", "telegram_chat": "Chat ID",
    "pushover_user": "User key", "pushover_token": "App token", "msg_keyword_prefix": "Keyword (empty = off)",
    "email_to": "To (your address)", "email_host": "SMTP server", "email_port": "Port", "email_user": "User name",
    "email_password": "Password", "email_events": "Which messages", "public_url": "Address of this page for links",
    "push_pics": "Pictures", "notify_cooldown": "Pause between alarms (s)", "prealarm_cooldown": "Pause between pre-alarms (s)",
}


def _px_relabel():
    for lst in (TOGGLES, TEXTS, SLIDERS):
        for i, x in enumerate(lst):
            if x[1] in _PX_LABELS and x[0] in ("Notifications", "Detection"):
                lst[i] = (x[0], x[1], _PX_LABELS[x[1]]) + tuple(x[3:])


_px_relabel()
# 5.: moved out - «Double confirmation» belongs to the detection, the device name to the system (Setup)
for _i, _x in enumerate(TOGGLES):
    if _x[1] == "alarm_confirm2":
        TOGGLES[_i] = ("Detection",) + tuple(_x[1:])
for _i, _x in enumerate(TEXTS):
    if _x[1] == "device_name":
        TEXTS[_i] = ("Setup",) + tuple(_x[1:])
# merged: the select «notification type» (the cards decide), «pre-alarm with a small picture» (Pictures: small)
TOGGLES[:] = [x for x in TOGGLES if x[1] != "prealarm_photo"]
TEXTS[:] = [x for x in TEXTS if x[1] != "notify_type"]          # TEXT_SPECS keeps it: set_text("notify_type") still works (guide)

_text_choice_pairs_before_px = text_choice_pairs


def text_choice_pairs(key):                                   # + push_level
    if TEXT_SPECS.get(key, (None, None))[1] == "push_levels":
        return [(k, tr(l)) for k, l in PUSH_LEVELS]
    return _text_choice_pairs_before_px(key)


_set_text_before_px = set_text


def set_text(key, value):
    """+ the push cards: the guide sets notify_url, then notify_type (main channel on again, no address swap - the
    address it just set is the one of the new type); «Pictures» covers the pre-alarm picture too"""
    ok, err = _set_text_before_px(key, value)
    if ok and key == "notify_type":
        CFG["main_push_on"] = True; save_settings()
    if ok and key == "push_pics":
        CFG["prealarm_photo"] = True; save_settings()
    return ok, err


# ---- pictures: with / small / without ------------------------------------------------------------------------------------
_sx_push_jpg_before_px = sx_push_jpg


def sx_push_jpg(jpg):
    jpg = _sx_push_jpg_before_px(jpg)
    if not jpg or CFG.get("push_pics") != "small":
        return jpg
    try:
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return jpg
        h, w = img.shape[:2]
        if w > 640:
            img = cv2.resize(img, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buf.tobytes() if ok else jpg
    except Exception:
        return jpg


# ---- level and quiet hours -------------------------------------------------------------------------------------------------
_PX_HM = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _px_min(s):
    m = _PX_HM.match(str(s or "").strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def quiet_clean(lst):
    """at most 4 windows {from, to, days[0=Mon..6=Sun]}; broken entries are dropped"""
    out = []
    for w in (lst if isinstance(lst, list) else [])[:4]:
        if not isinstance(w, dict):
            continue
        a, b = _px_min(w.get("from")), _px_min(w.get("to"))
        if a is None or b is None or a == b:
            continue
        days = sorted({int(d) for d in (w.get("days") or []) if str(d).lstrip("-").isdigit() and 0 <= int(d) <= 6})
        out.append({"from": "%02d:%02d" % divmod(a, 60), "to": "%02d:%02d" % divmod(b, 60), "days": days or [0, 1, 2, 3, 4, 5, 6]})
    return out


def push_clock():
    """the clock for the quiet hours: the simulated one while the simulator is connected (285), otherwise the real one"""
    try:
        return sim_now()
    except Exception:
        return datetime.now()


def quiet_now(dt=None):
    """True while a quiet window is running. A window over midnight (22:00 → 06:00) belongs to the day it starts on
    (like the schedules)."""
    if not CFG.get("quiet_on"):
        return False
    dt = dt or push_clock()
    m, wd = dt.hour * 60 + dt.minute, dt.weekday()
    for w in quiet_clean(CFG.get("quiet_windows")):
        a, b = _px_min(w["from"]), _px_min(w["to"])
        if a < b:
            if wd in w["days"] and a <= m < b:
                return True
        elif (wd in w["days"] and m >= a) or (((wd - 1) % 7) in w["days"] and m < b):
            return True
    return False


def push_allowed(ev, dt=None):
    """(ok, why) - may this event go out as a push? why: "" / "level" / "quiet"."""
    cls = PUSH_CLASS.get(ev)
    if cls is None:
        return True, ""
    lv = CFG.get("push_level") if CFG.get("push_level") in _PX_LEVEL_HAS else "all"
    if cls not in _PX_LEVEL_HAS[lv]:
        return False, "level"
    if quiet_now(dt) and not (cls == "person" and CFG.get("quiet_persons")):
        return False, "quiet"
    return True, ""


_PX_HELD = {}


def _px_held(ev, why):
    STATE["notify_status"] = "quiet hours" if why == "quiet" else "not reported (level)"
    now = time.time()
    if now - _PX_HELD.get((ev, why), 0) > 60:                # the log once a minute per kind, the alarm itself is logged anyway
        _PX_HELD[(ev, why)] = now
        log_event("web", f"No push message ({'quiet hours' if why == 'quiet' else 'level ' + str(CFG.get('push_level'))}): {ev}")


_px_person_before = Notifier.person
_px_prealarm_before = Notifier.prealarm
_px_main_conf_before = Notifier.main_configured
_px_test_all_before = Notifier.test_all


def _px_person(self, count, snapshot_path=None, frame=None):
    if count and is_armed() and CFG["notify_on"]:
        ok, why = push_allowed("person")
        if not ok:
            return _px_held("person", why)
    return _px_person_before(self, count, snapshot_path, frame)


def _px_prealarm(self, frame, event="prealarm"):
    if is_armed() and CFG["notify_on"]:
        ok, why = push_allowed(event if event in ("warm", "noise") else "prealarm")
        if not ok:
            _px_held(event, why)
            return False
    return _px_prealarm_before(self, frame, event)


def _px_main_configured():
    if not CFG.get("main_push_on", True):
        return False
    return _px_main_conf_before()


def _px_test_all(self, frame=None):
    res = _px_test_all_before(self, frame)
    STATE["push_test"] = {"t": time.time(), "n": len(res), "ok": sum(1 for r in res if r.get("ok")), "res": res}
    return res


# wraps: Notifier.person
Notifier.person = _px_person
# wraps: Notifier.prealarm
Notifier.prealarm = _px_prealarm
# wraps: Notifier.main_configured
Notifier.main_configured = staticmethod(_px_main_configured)
# wraps: Notifier.test_all
Notifier.test_all = _px_test_all


# ---- channels -------------------------------------------------------------------------------------------------------------
def _px_url_swap(old, new):
    """ntfy and Webhook share notify_url: keep the address of the old one, bring back the one of the new one"""
    if old == new:
        return
    if old in ("ntfy", "webhook"):
        CFG["push_url_" + old] = str(CFG.get("notify_url") or "")
    if new in ("ntfy", "webhook"):
        back = str(CFG.get("push_url_" + new) or "")
        if old in ("ntfy", "webhook") or back:           # Telegram → ntfy without a kept address: notify_url stays
            CFG["notify_url"] = back


def push_channels():
    """the cards: on (switched on), ready (can send), used (has data - shown without «+ add channel»)"""
    t_, main_on = CFG.get("notify_type"), bool(CFG.get("main_push_on", True))
    url = str(CFG.get("notify_url") or "").strip()
    try:
        subs = len(webpush_subs())
    except Exception:
        subs = 0
    try:
        nums = bool(sms_numbers())
    except Exception:
        nums = False
    keep = set(CFG.get("push_cards") or [])
    def one(id_, on, ready, used, info=""):
        return {"id": id_, "on": bool(on), "ready": bool(on and ready), "used": bool(on or used or id_ in keep), "info": info}
    out = [
        one("ntfy", main_on and t_ == "ntfy", bool(url), (t_ == "ntfy" and url) or CFG.get("push_url_ntfy"), _url_host(url) if t_ == "ntfy" and url else ""),
        one("webpush", CFG.get("webpush_on"), subs > 0, subs > 0, str(subs)),
        one("telegram", main_on and t_ == "telegram", CFG.get("telegram_token") and CFG.get("telegram_chat"), CFG.get("telegram_token") or CFG.get("telegram_chat")),
        one("pushover", CFG.get("pushover_on"), pushover_ready(), CFG.get("pushover_user") or CFG.get("pushover_token")),
        one("email", CFG.get("email_on"), email_ready(), CFG.get("email_to") or CFG.get("email_host"), str(CFG.get("email_to") or "")),
        one("webhook", main_on and t_ == "webhook", bool(url), (t_ == "webhook" and url) or CFG.get("push_url_webhook"), _url_host(url) if t_ == "webhook" and url else ""),
        one("sms", CFG.get("sms_on"), nums, nums),
    ]
    return out


def push_set_channel(ch, on):
    """switch one card on / off. ntfy, Telegram, Webhook: only one (switching one on switches the other two off)."""
    if ch not in PUSH_CHANNELS:
        return False, "unknown channel"
    on = bool(on)
    if ch in PUSH_MAIN:
        if on:
            _px_url_swap(CFG.get("notify_type"), ch)
            CFG["notify_type"] = ch; CFG["main_push_on"] = True
        elif CFG.get("notify_type") == ch:
            CFG["main_push_on"] = False
    else:
        CFG[{"webpush": "webpush_on", "pushover": "pushover_on", "email": "email_on", "sms": "sms_on"}[ch]] = on
    cards = [c for c in (CFG.get("push_cards") or []) if c in PUSH_CHANNELS]
    if on and ch not in cards:
        cards.append(ch)
    CFG["push_cards"] = cards
    save_settings()
    log_event("web", f"Push channel {ch}: {'on' if on else 'off'}")
    return True, ""


def push_add_card(ch):
    """«+ Kanal hinzufügen»: the card is shown (also while it is still off)"""
    if ch in PUSH_CHANNELS and ch not in (CFG.get("push_cards") or []):
        CFG["push_cards"] = [c for c in (CFG.get("push_cards") or []) if c in PUSH_CHANNELS] + [ch]
        save_settings()


def push_keyword():
    return str(CFG.get("msg_keyword_prefix") or "") if CFG.get("msg_keyword_on", True) else ""


def push_keyword_set(v):
    """one field: empty = off; otherwise the word (letters and digits, at most 12)"""
    v = re.sub(r"[^A-Za-z0-9]", "", str(v or ""))[:12]
    if not v:
        CFG["msg_keyword_on"] = False
    else:
        CFG["msg_keyword_on"] = True; CFG["msg_keyword_prefix"] = v
    save_settings()
    return True, ""


def push_test_one(w, ch):
    """▶ Test of one card - the same as «Test all channels», only this one; [{ch, ok, msg}]"""
    if ch == "all":
        return w.notifier.test_all(getattr(w, "frame_out", None))
    n = w.notifier
    jpg = None
    fr = getattr(w, "frame_out", None)
    if fr is not None:
        ok_, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 80]); jpg = buf.tobytes() if ok_ else None
    pub = CFG["public_url"].strip().rstrip("/")
    p = {"event": "test", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "snapshot": None, "rain": False, "wind": "",
         "source": STATE["source_label"], "link": pub + "/recordings" if pub else ""}
    name = {"ntfy": "ntfy", "webpush": "Web-Push", "telegram": "Telegram", "pushover": "Pushover", "email": "E-Mail", "webhook": "Webhook", "sms": "SMS"}.get(ch, ch)
    def go():
        if ch in PUSH_MAIN:
            if CFG.get("notify_type") != ch or not n.main_configured():
                return False, tr("not set up")
            code, where = n._send_main(p, jpg, "test.jpg"); return True, f"{where} · HTTP {code}"
        if ch == "pushover":
            return n._pushover(p, jpg, "test.jpg") if pushover_ready() else (False, tr("not set up"))
        if ch == "email":
            return email_send(n._title(p), n._text(p), jpg, "test.jpg") if email_ready() else (False, tr("not set up"))
        if ch == "sms":
            return sms_send(n._title(p) + ": " + n._text(p), force=True) if (CFG["sms_on"] and sms_numbers()) else (False, tr("not set up"))
        if ch == "webpush":
            k = webpush_all(n._title(p), n._text(p), "/", tag="mw-test", urgent=True) if CFG["webpush_on"] else 0
            return k > 0, f"{k} device(s)"
        return False, "unknown channel"
    try:
        ok, msg = go()
    except Exception as e:
        ok, msg = False, str(e)
    msg = str(msg)
    for sec_ in (CFG["telegram_token"], CFG["pushover_token"], CFG["pushover_user"], CFG.get("email_password", ""), CFG["notify_url"].strip()):
        if sec_:
            msg = msg.replace(sec_, "***")
    res = [{"ch": name, "ok": bool(ok), "msg": msg[:160]}]
    log_event("web", f"Test of {name}: {'ok' if ok else 'FAILED'}")
    STATE["push_test"] = {"t": time.time(), "n": 1, "ok": 1 if ok else 0, "res": res}
    return res


def push_info(lang=None):
    """everything the cards need (web 531a, window 571a)"""
    L = cur_lang(lang)
    ch = push_channels()
    n_ready = sum(1 for c in ch if c["ready"])
    te = STATE.get("push_test") or {}
    return {"on": bool(CFG.get("notify_on")), "channels": ch, "ready": n_ready, "main": CFG.get("notify_type"),
            "main_on": bool(CFG.get("main_push_on", True)), "url": str(CFG.get("notify_url") or ""),
            "level": CFG.get("push_level") or "all", "pics": CFG.get("push_pics") or "with",
            "quiet": {"on": bool(CFG.get("quiet_on")), "persons": bool(CFG.get("quiet_persons")), "windows": quiet_clean(CFG.get("quiet_windows")),
                      "now": quiet_now(), "clock": push_clock().strftime("%H:%M"), "sim": bool(CFG.get("sim_on"))},
            "keyword": push_keyword(), "night_from": int(CFG.get("report_from") or 20),
            "test": {"t": te.get("t", 0), "n": te.get("n", 0), "ok": te.get("ok", 0), "res": te.get("res", [])},
            "status_line": push_status_line(L, ch, te)}


def push_status_line(lang=None, ch=None, te=None):
    """«2 Kanäle · Test ✓» (or «aus», «kein Kanal», «Ruhezeit»)"""
    L = cur_lang(lang)
    if not CFG.get("notify_on"):
        return tr("switched off", L)
    ch = ch if ch is not None else push_channels()
    te = te if te is not None else (STATE.get("push_test") or {})
    n = sum(1 for c in ch if c["ready"])
    parts = [trf("{n} channels", L, n=n) if n != 1 else tr("1 channel", L)] if n else [tr("no channel set up", L)]
    if te.get("n"):
        parts.append(tr("Test", L) + " " + ("✓" if te.get("ok") == te.get("n") else f"{te.get('ok')}/{te.get('n')} ✓"))
    if quiet_now():
        parts.append("🌙 " + tr("quiet hours", L))
    return " · ".join(parts)


# ---- migration of older settings -------------------------------------------------------------------------------------------
def push_migrate(cfg_in):
    """older settings files: nothing is lost - the type, the address, Telegram, Pushover, e-mail stay as they were.
    Only: a file without notify_type (very old export) keeps the old default «webhook» when it has an address;
    broken quiet windows are cleaned; an unknown level becomes «all»."""
    did = []
    if isinstance(cfg_in, dict):
        if "notify_type" not in cfg_in and str(CFG.get("notify_url") or "").strip():
            CFG["notify_type"] = "webhook"; did.append("push: notification type webhook (old default)")
        if "main_push_on" not in cfg_in:
            CFG["main_push_on"] = True
            if CFG.get("notify_type") == "webhook" and not str(CFG.get("notify_url") or "").strip():
                CFG["notify_type"] = "ntfy"; did.append("push: nothing set up yet - main channel ntfy (new default)")
    if CFG.get("push_level") not in _PX_LEVEL_HAS:
        CFG["push_level"] = "all"
    if CFG.get("push_pics") not in ("with", "small", "text"):
        CFG["push_pics"] = "with"
    CFG["quiet_windows"] = quiet_clean(CFG.get("quiet_windows")) or json.loads(json.dumps(_PX_DEF["quiet_windows"]))
    if not isinstance(CFG.get("push_cards"), list):
        CFG["push_cards"] = []
    return did


def rename_migrate(cfg_in):
    """2.98.51 (MoveEye instead of «MW» / «MotionWatch»), once per settings file (a file without «names_v»):
    the push keyword: exactly the old default «MW» becomes «MoveEye» (an own word stays; the iPhone shortcuts must then look
    for «MoveEye-» - in the release notes); the own Wi-Fi: devices from before keep «MotionWatch» (phones know that network),
    only new setups get «MoveEye»."""
    did = []
    if not isinstance(cfg_in, dict) or "names_v" in cfg_in:
        return did
    if "msg_keyword_prefix" in cfg_in and str(CFG.get("msg_keyword_prefix") or "") == "MW":
        CFG["msg_keyword_prefix"] = "MoveEye"; did.append("push: keyword MW -> MoveEye (iPhone shortcuts: «MoveEye-ALARM» …)")
    if not str(cfg_in.get("hotspot_ssid") or "").strip():
        CFG["hotspot_ssid"] = "MotionWatch"; did.append("own Wi-Fi keeps the name MotionWatch")
    CFG["names_v"] = 1
    return did


_settings_migrations_before_px = _settings_migrations


def _settings_migrations(cfg_in):
    _settings_migrations_before_px(cfg_in)
    try:
        did = push_migrate(cfg_in)
        if did:
            log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
    except Exception as e:
        log_event("sys", f"Settings migration (579a): {e}"[:150])
    try:
        did = rename_migrate(cfg_in)
        if did:
            log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
            save_settings()                             # once: the file gets «names_v», the next start does not migrate again
    except Exception as e:
        log_event("sys", f"Settings migration (579a names): {e}"[:150])


# ---- web: /api/push (only the administrator: the path is in no role's list, 040) -------------------------------------------
def push_routes(app, watch, reply, body):
    from flask import request

    @app.route("/api/push", methods=["GET", "POST"])
    def api_push():
        if request.method == "GET":
            return reply(push_info(request.args.get("lang")))
        d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
        if a == "channel":
            ok, err = push_set_channel(str(d.get("ch") or ""), d.get("on"))
        elif a == "add":
            push_add_card(str(d.get("ch") or "")); ok, err = True, ""
        elif a == "test":
            if not CFG.get("notify_on"):
                return reply({"ok": False, "error": tr("Push messages are switched off", lang)}, 400)
            res = push_test_one(watch, str(d.get("ch") or "all"))
            return reply(dict(push_info(lang), ok=True, results=res))
        elif a == "quiet":
            CFG["quiet_windows"] = quiet_clean(d.get("windows")) or CFG["quiet_windows"]; save_settings(); ok, err = True, ""
        elif a == "keyword":
            ok, err = push_keyword_set(d.get("value"))
        else:
            ok, err = False, "unknown action"
        if not ok:
            return reply({"ok": False, "error": tr_err(err, lang)}, 400)
        return reply(dict(push_info(lang), ok=True))


_sx_routes_before_px = sx_routes


def sx_routes(app, watch, reply, body):                    # + /api/push (called once by 550)
    _sx_routes_before_px(app, watch, reply, body)
    push_routes(app, watch, reply, body)


# ---- --self-test: levels, quiet hours (also on the simulator clock), migration of old settings, channels, pictures ----------
def push_selftest():
    g_ = globals()
    keys = ("notify_type", "notify_url", "main_push_on", "push_level", "quiet_on", "quiet_persons", "quiet_windows", "push_url_ntfy",
            "push_url_webhook", "push_cards", "telegram_token", "telegram_chat", "pushover_on", "pushover_user", "pushover_token",
            "email_on", "email_to", "email_host", "webpush_on", "sms_on", "push_pics", "sim_on", "msg_keyword_on", "msg_keyword_prefix", "prealarm_photo")
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in keys}
    sim_keep = {k: SIM.get(k) for k in ("t", "clock")}
    save_keep = g_["save_settings"]
    g_["save_settings"] = lambda *a, **k: None
    try:
        CFG["sim_on"] = False; CFG["quiet_on"] = False
        # levels: «all» = as before (person, warm body, noise); sabotage / notes always
        CFG["push_level"] = "all"
        assert all(push_allowed(e)[0] for e in ("person", "warm", "noise", "prealarm", "tamper", "info", "test"))
        CFG["push_level"] = "animals"
        assert push_allowed("warm")[0] and push_allowed("person")[0] and push_allowed("noise") == (False, "level")
        CFG["push_level"] = "persons"
        assert push_allowed("person")[0] and push_allowed("warm") == (False, "level") and push_allowed("noise") == (False, "level")
        assert push_allowed("tamper")[0] and push_allowed("info")[0] and push_allowed("prealarm")[0]
        CFG["push_level"] = "nonsense"; assert push_allowed("noise")[0], "an unknown level counts as «all»"
        CFG["push_level"] = "all"
        # quiet hours: a window over midnight belongs to the day it starts on; «report persons anyway»
        CFG["quiet_on"] = True; CFG["quiet_windows"] = [{"from": "22:00", "to": "06:00", "days": [3]}]       # Thursday night
        thu23, fri05, fri07, wed23 = datetime(2026, 10, 29, 23, 0), datetime(2026, 10, 30, 5, 0), datetime(2026, 10, 30, 7, 0), datetime(2026, 10, 28, 23, 0)
        assert quiet_now(thu23) and quiet_now(fri05) and not quiet_now(fri07) and not quiet_now(wed23)
        CFG["quiet_persons"] = False
        assert push_allowed("person", thu23) == (False, "quiet") and push_allowed("warm", thu23) == (False, "quiet")
        assert push_allowed("tamper", thu23)[0] and push_allowed("info", thu23)[0], "sabotage and notes come in the quiet hours"
        CFG["quiet_persons"] = True
        assert push_allowed("person", thu23)[0] and push_allowed("warm", thu23) == (False, "quiet")
        CFG["quiet_windows"] = [{"from": "08:00", "to": "18:00", "days": [0, 1, 2, 3, 4]}]
        assert quiet_now(datetime(2026, 10, 30, 12, 0)) and not quiet_now(datetime(2026, 10, 31, 12, 0)) and not quiet_now(datetime(2026, 10, 30, 18, 0))
        CFG["quiet_on"] = False; assert not quiet_now(datetime(2026, 10, 30, 12, 0))
        assert quiet_clean([{"from": "25:00", "to": "06:00"}, {"from": "7:05", "to": "09:00", "days": [9, 1]}, "x"]) == [{"from": "07:05", "to": "09:00", "days": [1]}]
        # the simulator clock counts while it is connected (285 sim_now)
        CFG["quiet_on"] = True; CFG["quiet_persons"] = False; CFG["quiet_windows"] = [{"from": "02:00", "to": "04:00", "days": [0, 1, 2, 3, 4, 5, 6]}]
        CFG["sim_on"] = True; SIM["t"] = time.time(); SIM["clock"] = {"date": "2026-10-30", "hour": 3.0, "speed": 1.0}
        assert push_clock().hour == 3 and quiet_now() and push_allowed("person") == (False, "quiet")
        SIM["clock"] = {"date": "2026-10-30", "hour": 13.0, "speed": 1.0}
        assert not quiet_now()
        CFG["sim_on"] = False; CFG["quiet_on"] = False
        # migration: old settings with Telegram, Pushover, e-mail, webhook - nothing changes, nothing is lost
        old = {"notify_type": "telegram", "telegram_token": "123456:ABCdef", "telegram_chat": "4242", "notify_url": "https://hook.example.ch/x",
               "pushover_on": True, "pushover_user": "u" * 30, "pushover_token": "t" * 30, "email_on": True, "email_to": "a@b.ch",
               "email_host": "smtp.b.ch", "webpush_on": False, "sms_on": False}
        CFG.update(json.loads(json.dumps(old))); CFG["main_push_on"] = True; CFG["push_cards"] = []; CFG["push_url_ntfy"] = CFG["push_url_webhook"] = ""
        push_migrate(dict(old))
        assert all(CFG[k] == v for k, v in old.items()), "migration must not change channel settings"
        ch = {c["id"]: c for c in push_channels()}
        assert ch["telegram"]["on"] and ch["telegram"]["ready"] and ch["pushover"]["ready"] and ch["email"]["ready"]
        assert not ch["ntfy"]["on"] and not ch["webhook"]["on"] and Notifier.main_configured()
        # switching the main channel keeps every address and token
        push_set_channel("webhook", True)
        assert CFG["notify_type"] == "webhook" and CFG["notify_url"] == "https://hook.example.ch/x" and CFG["telegram_token"] == "123456:ABCdef"
        push_set_channel("ntfy", True)
        assert CFG["notify_type"] == "ntfy" and CFG["notify_url"] == "" and CFG["push_url_webhook"] == "https://hook.example.ch/x"
        CFG["notify_url"] = "https://ntfy.sh/mw-test-topic"
        push_set_channel("webhook", True)
        assert CFG["notify_url"] == "https://hook.example.ch/x" and CFG["push_url_ntfy"] == "https://ntfy.sh/mw-test-topic"
        push_set_channel("telegram", True); push_set_channel("ntfy", True)
        assert CFG["notify_url"] == "https://ntfy.sh/mw-test-topic" and CFG["telegram_token"] == "123456:ABCdef"
        push_set_channel("ntfy", False)
        assert not CFG["main_push_on"] and not Notifier.main_configured() and CFG["notify_url"] == "https://ntfy.sh/mw-test-topic"
        push_set_channel("email", False); assert not CFG["email_on"] and CFG["email_to"] == "a@b.ch"
        # a very old file without notify_type: the old default «webhook» when it has an address; an old webhook stays webhook
        CFG["notify_type"] = "ntfy"; CFG["notify_url"] = "https://ha.local/api/webhook/x"; CFG["main_push_on"] = True
        push_migrate({"notify_url": "https://ha.local/api/webhook/x"}); assert CFG["notify_type"] == "webhook"
        CFG["notify_type"] = "webhook"; push_migrate({"notify_type": "webhook", "notify_url": "https://ha.local/api/webhook/x"})
        assert CFG["notify_type"] == "webhook" and CFG["main_push_on"] and {c["id"]: c for c in push_channels()}["webhook"]["ready"]
        assert DEFAULTS["notify_type"] == "ntfy", "new installations start with ntfy"
        CFG["notify_type"] = "webhook"; CFG["notify_url"] = ""; push_migrate({"notify_type": "webhook", "notify_url": ""})
        assert CFG["notify_type"] == "ntfy", "an untouched old default (webhook without address) becomes ntfy"
        # keyword: one field, empty = off (the word is kept)
        assert DEFAULTS["msg_keyword_prefix"] == "MoveEye" and DEFAULTS["hotspot_ssid"] == "MoveEye", "2.98.51: new names ab Werk"
        push_keyword_set("MoveEye"); assert push_keyword() == "MoveEye" and msg_keyword("person") == "MoveEye-ALARM"
        push_keyword_set(""); assert push_keyword() == "" and msg_keyword("person") == "" and CFG["msg_keyword_prefix"] == "MoveEye"
        # 2.98.51: an old file - exactly «MW» becomes «MoveEye» once, an own word stays, the own Wi-Fi keeps «MotionWatch»
        CFG.update(msg_keyword_on=True, msg_keyword_prefix="MW", hotspot_ssid="MotionWatch")
        assert rename_migrate({"msg_keyword_prefix": "MW", "hotspot_ssid": "MotionWatch"}) and CFG["msg_keyword_prefix"] == "MoveEye"
        assert CFG["hotspot_ssid"] == "MotionWatch" and msg_keyword("warm") == "MoveEye-WAERME"
        CFG["msg_keyword_prefix"] = "Camp"; assert rename_migrate({"msg_keyword_prefix": "Camp", "hotspot_ssid": "x"}) == [] and CFG["msg_keyword_prefix"] == "Camp"
        CFG["msg_keyword_prefix"] = "MW"; assert rename_migrate({"msg_keyword_prefix": "MW", "names_v": 1}) == [] and CFG["msg_keyword_prefix"] == "MW", "only once"
        CFG["hotspot_ssid"] = "MoveEye"; rename_migrate({"msg_keyword_prefix": "Camp"}); assert CFG["hotspot_ssid"] == "MotionWatch", "old file without a name"
        push_keyword_set("Cam-1!"); assert push_keyword() == "Cam1"
        # pictures: small = about 640 px, without = none
        ok_, buf = cv2.imencode(".jpg", np.zeros((720, 1280, 3), np.uint8)); big = buf.tobytes()
        CFG["push_pics"] = "small"; sm = sx_push_jpg(big)
        assert cv2.imdecode(np.frombuffer(sm, np.uint8), cv2.IMREAD_COLOR).shape[1] == 640
        CFG["push_pics"] = "text"; assert sx_push_jpg(big) is None
        CFG["push_pics"] = "with"; assert sx_push_jpg(big) == big
        assert set(dict(text_choice_pairs("push_level"))) == {"persons", "animals", "all"}
        assert all(len(tr(l, "de")) <= 42 for k, l in _PX_LABELS.items()), "labels at most about 40 characters"
        assert not any(x[1] == "notify_type" for x in TEXTS) and any(x[1] == "alarm_confirm2" and x[0] == "Detection" for x in TOGGLES)
        assert "push_status_line" and push_status_line("de")
    finally:
        g_["save_settings"] = save_keep
        CFG.update(keep)
        for k, v in sim_keep.items():
            if v is None:
                SIM.pop(k, None)
            else:
                SIM[k] = v
    return "levels, quiet hours (sim clock), migration, channels, keyword, pictures"


SELFTEST_EXTRA.append(("Push messages as cards: levels, quiet hours, old settings (579a)", push_selftest))
