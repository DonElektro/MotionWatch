#@ Motion Watch – Teil 135: Schutz (Schutz-Stufe, Assistent, Diebstahlschutz, Ampel, Abwesenheit, Eskalation, PIN, Schutz testen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.95.105: one place for everything that protects: a level instead of many switches
#   off   - no alarms
#   watch - «Wachsam»: armed, push messages, sabotage check; no siren
#   full  - «Voller Schutz»: + guarded things (reference scan), GPS theft tracking, siren after a while (escalation)
# Plus: the traffic light (what is missing, with a fix), presence of the owner's phone (armed when it is gone), a PIN
# for disarming (a wrong PIN 3 times = theft alarm); presence (presence_auto, 150) is shown here too, and «Schutz testen» (with the simulator: sabotage, a person).
# ----------------------------------------------------------------------------
PROTECT = {"esc_t": 0.0, "esc_id": 0, "pin_fails": [], "test": {"busy": False, "steps": [], "t": 0.0}}
PROTECT_LEVELS = ("off", "watch", "full")


def protect_level():
    """the level now: off when disarmed, else the chosen one (armed by other means = «watch»)"""
    if not CFG["armed"]:
        return "off"
    lv = CFG.get("protect_level") or "watch"
    return lv if lv in PROTECT_LEVELS and lv != "off" else "watch"


def protect_label(arm_state, left=0, lang=None):
    """2.98.0: one name for the state everywhere (web, window, alarm window): Aus / Wachsam / Voll"""
    lv = tr("Full protection", lang) if (CFG.get("protect_level") == "full") else tr("Watchful", lang)
    if arm_state in ("armed", "arming") and walktest_on():    # 2.98.15: during the walk test no alarms - say so (415)
        return tr("Walk test", lang)
    if arm_state == "armed":
        return lv
    if arm_state == "arming":
        return f"{lv} {tr('in', lang)} {int(left)} s"
    return tr("Off", lang)


def protect_set(level, who="web", answers=None):
    """switch the level; answers of the assistant (what, when, how) adjust what is switched on"""
    if level not in PROTECT_LEVELS:
        return False, "unknown level"
    A = answers or {}
    if level == "off":
        CFG["protect_level"] = "off"
        protect_siren_sync()                             # fix 3: «Aus» takes back what «Voll» switched on (disarm saves)
        disarm()
        return True, ""
    CFG["protect_level"] = level
    CFG["notify_on"] = True
    CFG["tamper_on"] = True
    if level == "full" or A.get("device"):
        if CFG.get("gpsmod_on"):
            CFG["gps_theft"] = True
    if level == "full" or A.get("things"):
        CFG["refscan_on_arm"] = True                     # compare with the reference when armed (guarded things)
    react = A.get("react") or ("siren" if level == "full" else "push")
    if react in ("light", "siren"):
        CFG["light_white_auto"] = "alarm_dark" if CFG.get("light_white_auto") in ("", "dark") else CFG["light_white_auto"]
    protect_siren_sync(level, react)                     # fix 3: the siren and the escalation follow the level (also back to off)
    for k in ("protect_level", "notify_on", "tamper_on", "gps_theft", "refscan_on_arm", "escalate_on", "siren_on"):
        sched_user_changed(k)
    save_settings()
    when = A.get("when") or "now"
    if when == "night":
        night_guard()
    else:
        arm()
    if (level == "full" or A.get("things")) and not refscan_meta() and not REFSCAN["busy"]:
        refscan_start("scan", "protection assistant")     # no reference yet: take it now (before the countdown ends)
    log_event("sys", f"Protection: {level} ({who})")
    return True, ""


# ---- fix 3 (Prüfung 10.11.2026): the level decides about the siren - in ONE place --------------------------------------------
# Before: «Voll» switched the siren on («Sirene bei Alarm» = Person, «Sirene nach 30 s») and nothing ever switched it off again.
# «Voll» -> «Wachsam» left the siren on (it even sounded at once), «Voll» -> «Aus» -> switching on again (button, shortcut,
# schedule, mode) showed «Wachsam» while the siren after 30 s was still active - «Wachsam» is described as «nur Meldungen».
# Now: what a level switched on is remembered in CFG["protect_auto"] and taken back when the level no longer wants it:
#   «Voll»     siren after the wait ON, «Sirene bei Alarm» from «aus» to «Person»
#   «Wachsam»  siren after the wait OFF; «Sirene bei Alarm» back to «aus» IF the level had switched it on
#   armed in another way after «Aus» (= «Wachsam»): the same as «Wachsam», for what the level had switched on
# What the user chose himself stays: «Sirene bei Alarm» in the settings of the loudspeaker (set_text, 030) and the switch
# «Sirene nach … s» on the page «Schutz» (protect_auto_user) - also in «Wachsam», the page shows it («🚨 Sirene»).
# An older settings file does not know who switched what (["?"]): a siren after the wait that is on counts as switched on by
# «Voll» (with «Sirene bei Alarm» = Person, exactly what «Voll» sets) - it is the left-over this fix is about.
PROTECT_AUTO_KEYS = ("escalate_on", "siren_on")


def _protect_auto():
    a = CFG.get("protect_auto")
    if not isinstance(a, list) or "?" in a:              # older settings file: see above
        a = ["escalate_on"] + (["siren_on"] if CFG.get("siren_on") == "person" else []) if CFG.get("escalate_on") else []
    return [k for k in PROTECT_AUTO_KEYS if k in a]


def protect_auto_user(key):
    """the user chose this himself (loudspeaker setting, switch on the page «Schutz»): the level no longer takes it back"""
    a = _protect_auto()
    CFG["protect_auto"] = [k for k in a if k != key]


def protect_siren_sync(level=None, react=None):
    """ONE function for every way of switching on: protect_set (level = the chosen one, react = answer of the assistant) and
    arm() / the schedule / the camping profile / the start of the program (level None = no level chosen now). Returns True
    when a setting changed (the caller saves)."""
    auto = _protect_auto()
    was = (CFG.get("escalate_on"), CFG.get("siren_on"), CFG.get("protect_auto"))
    if level is None:
        # no level chosen now: «Voll» / «Wachsam» chosen before stay as they were set then; after «Aus» the state is
        # «Wachsam» (protect_level) - what «Voll» had switched on goes off
        if (CFG.get("protect_level") or "off") == "off":
            if "escalate_on" in auto:
                CFG["escalate_on"] = False
            if "siren_on" in auto and CFG.get("siren_on") == "person":
                CFG["siren_on"] = "off"
            auto = []
    elif (react or ("siren" if level == "full" else "push")) == "siren":
        if not CFG.get("escalate_on"):
            CFG["escalate_on"] = True; auto.append("escalate_on")
        if CFG.get("siren_on") == "off":
            CFG["siren_on"] = "person"; auto.append("siren_on")
    else:
        CFG["escalate_on"] = False                       # a level chosen now always decides about the wait (as before)
        if "siren_on" in auto and CFG.get("siren_on") == "person":
            CFG["siren_on"] = "off"
        auto = []
    CFG["protect_auto"] = [k for k in PROTECT_AUTO_KEYS if k in auto]
    changed = was != (CFG.get("escalate_on"), CFG.get("siren_on"), CFG.get("protect_auto"))
    if was[:2] != (CFG.get("escalate_on"), CFG.get("siren_on")):
        if not CFG.get("escalate_on"):
            protect_cancel_escalation()
        log_event("sys", "Protection: siren " + ("on" if CFG.get("siren_on") != "off" else "off") + ", siren after the wait "
                  + ("on" if CFG.get("escalate_on") else "off") + (" (follows the level)" if level is None else f" (level {level})"))
    return changed


# ---- the traffic light ---------------------------------------------------------------------------------------------------
_PROT_CACHE = {"t": 0.0, "k": "", "v": None}


def protect_status(lang=None, force=False):
    """the state for the page (cached 3 s - the page asks every second)"""
    L = norm_lang(lang) if lang else cur_lang()
    k = L + str(CFG["armed"]) + str(CFG.get("protect_level")) + str(PROTECT["test"]["busy"]) + str(len(PROTECT["test"]["steps"]))
    if not force and _PROT_CACHE["v"] is not None and _PROT_CACHE["k"] == k and time.time() - _PROT_CACHE["t"] < 3.0:
        v = dict(_PROT_CACHE["v"]); v["arm"] = STATE.get("arm_state"); v["left"] = STATE.get("arm_left", 0)
        v["walk"] = walktest_on()
        return v
    v = _protect_status(L)
    _PROT_CACHE.update(t=time.time(), k=k, v=v)
    return dict(v, walk=walktest_on())                     # 2.98.15: walk test running = the state shows «Gehtest»


def _protect_status(L):
    T = lambda x: tr(x, L)
    lv = protect_level()
    items = []                                           # {"id", "ok", "text", "fix"}
    try:
        h = health_check(L)
        for x in h["items"]:
            if x["level"] == "bad":
                items.append({"id": "h_" + str(x["id"]), "ok": False, "text": x["title"] + ": " + x["text"], "fix": ""})
    except Exception:
        pass
    if not CFG.get("notify_on"):
        items.append({"id": "push", "ok": False, "text": T("Push messages are off"), "fix": "push"})
    if lv == "full" or CFG.get("protect_level") == "full":
        if not refscan_meta():
            items.append({"id": "ref", "ok": False, "text": T("No reference scan yet - guarded things cannot be checked"), "fix": "refscan"})
        if CFG.get("gpsmod_on") and GPSMOD.get("status") != "fix":
            items.append({"id": "gps", "ok": False, "text": T("GPS has no position yet"), "fix": ""})
        if CFG.get("escalate_on") and not out_selected():
            items.append({"id": "spk", "ok": False, "text": T("No loudspeaker for the siren"), "fix": "speaker"})
        if not CFG.get("protect_pin"):
            items.append({"id": "pin", "ok": False, "text": T("No PIN for disarming - a thief could switch it off"), "fix": "pin"})
    if CFG.get("backup_type", "off") == "off":
        items.append({"id": "backup", "ok": False, "text": T("Recordings are not copied away (backup off)"), "fix": "backup", "minor": True})
    tam = STATE.get("tamper") or {}
    tl = str(tam.get("last") or "")
    recent = False
    if re.match(r"\d\d:\d\d ", tl):
        try:
            hm = datetime.now().replace(hour=int(tl[:2]), minute=int(tl[3:5]), second=0)
            recent = 0 <= (datetime.now() - hm).total_seconds() < 600
        except ValueError:
            pass
    if recent:
        items.append({"id": "tamper", "ok": False, "text": T("Sabotage") + ": " + str(tam.get("last")), "fix": ""})
    bad = [x for x in items if not x.get("minor")]
    colour = "green" if not bad else ("red" if any(x["id"].startswith("h_") or x["id"] == "tamper" for x in bad) else "orange")
    # device protection in one line
    dev = []
    dev.append(("✓ " if CFG.get("tamper_on") else "– ") + T("sabotage check"))
    if CFG.get("gpsmod_on"):
        dev.append(("✓ " if GPSMOD.get("status") == "fix" else "⚠ ") + "GPS")
    dev.append(("✓ " if CFG.get("backup_type", "off") != "off" else "– ") + T("backup"))
    if CFG.get("protect_pin"):
        dev.append("✓ PIN")
    # the guarded things of the reference scan
    things = []
    meta = refscan_meta()
    if meta:
        miss = set()
        reps = refscan_reports()
        if reps:
            for n in (reps[0].get("gone") or []):
                miss.add(str(n))
        for it in (meta.get("watch") or [])[:12]:
            things.append({"name": it["name"], "pos": it["pos"], "box": [it["x"], it["y"], it["w"], it["h"]], "dir": REFSCAN_KINDS[meta["_kind"]],
                           "missing": it["name"] in miss})
    return {"level": lv, "chosen": CFG.get("protect_level") or "off", "arm": STATE.get("arm_state"), "left": STATE.get("arm_left", 0),
            "colour": colour, "items": items, "device": "  ·  ".join(dev), "things": things, "pin": bool(CFG.get("protect_pin")),
            "presence": {"on": bool(CFG.get("presence_auto")), "back": presence_back_mode(), "devices": len(CFG.get("presence_macs") or []) + len(CFG.get("presence_bt") or []),
                         "here": (TOOLS.get("presence") or {}).get("here")},
            "escalate": {"on": bool(CFG.get("escalate_on")), "s": int(CFG.get("escalate_siren_s", 30)), "pending": max(0, int(PROTECT["esc_t"] - time.time())) if PROTECT["esc_t"] else 0},
            "test": PROTECT["test"], "forecast": arm_forecast_text(L)}      # 2.98.13 (066)


# ---- escalation: light at once, push, the siren after a while unless somebody disarms --------------------------------------
def protect_on_alert(kind):
    if kind != "person" or not is_armed() or not CFG.get("escalate_on"):
        return
    light_alarm()
    if PROTECT["esc_t"] and time.time() < PROTECT["esc_t"]:
        return                                           # already counting
    s = max(0, int(CFG.get("escalate_siren_s", 30)))
    PROTECT["esc_t"] = time.time() + s
    PROTECT["esc_id"] += 1
    my = PROTECT["esc_id"]

    def later():
        time.sleep(s)
        if PROTECT["esc_id"] != my:
            return
        PROTECT["esc_t"] = 0.0
        if CFG.get("siren_on") == "off":                 # 2.97.0: «siren off» (e.g. mode wildlife) counts here too
            log_event("sys", "Escalation: the siren is switched off - only light and push")
            return
        if siren_quiet() and not sim_speaker():
            log_event("sys", "Escalation: siren held back (simulation / game / drill)")
            return                                       # 554: with the simulator connected it plays there (never for real)
        if time.time() - SOUND["last_alarm"] < float(CFG["siren_pause"]):
            return
        if is_armed() and speaker_ok() and not SOUND["playing"]:
            SOUND["last_alarm"] = time.time()
            log_event("sys", f"Escalation: siren after {s} s (nobody disarmed)")
            sound_play(None, None, None, reason="escalation")
    threading.Thread(target=later, daemon=True, name="escalate").start()


def protect_cancel_escalation():
    PROTECT["esc_id"] += 1
    PROTECT["esc_t"] = 0.0


# ---- PIN for disarming ---------------------------------------------------------------------------------------------------
def protect_pin_set(new_pin, old_pin=""):
    new_pin = str(new_pin or "").strip()
    if CFG.get("protect_pin") and not protect_pin_ok(old_pin):
        return False, "wrong PIN"
    if new_pin and not re.fullmatch(r"\d{4,8}", new_pin):
        return False, "the PIN must have 4 to 8 digits"
    CFG["protect_pin"] = _pin_hash(new_pin) if new_pin else ""
    save_settings()
    log_event("sys", "Protection: PIN " + ("set" if new_pin else "removed"))
    return True, ""


def protect_pin_ok(pin):
    h = CFG.get("protect_pin") or ""
    if not h:
        return True
    try:
        return hmac.compare_digest(_pin_hash(str(pin or "").strip(), h.split("$", 1)[0]), h)
    except Exception:
        return False


def protect_pin_check(pin, source="web"):
    """the PIN for switching off (if one is set): (ok, error). 3 wrong PINs within 10 minutes: theft alarm (push with
    picture), 5: blocked for 10 minutes. No PIN given: «PIN needed» - not counted (the page then asks for it)."""
    if not CFG.get("protect_pin"):
        return True, ""
    now = time.time()
    PROTECT["pin_fails"] = [t for t in PROTECT["pin_fails"] if now - t < 600]
    if len(PROTECT["pin_fails"]) >= 5:
        return False, "too many wrong PINs - try again in 10 minutes"
    if not str(pin or "").strip():
        return False, "PIN needed"
    if not protect_pin_ok(pin):
        PROTECT["pin_fails"].append(now)
        log_event("sys", f"Protection: wrong PIN for disarming ({source})")
        if len(PROTECT["pin_fails"]) >= 3:
            w = WATCH_REF.get("w")
            try:
                if w is not None:
                    w.notifier.tamper(tr("Somebody tries to disarm with a wrong PIN"), w.frame_out)
            except Exception:
                pass
            siren_alarm("tamper")
        return False, "wrong PIN"
    PROTECT["pin_fails"] = []
    return True, ""


def protect_disarm(pin, source="web"):
    """disarm with the PIN (if one is set), see protect_pin_check"""
    ok, err = protect_pin_check(pin, source)
    if not ok:
        return False, err
    protect_cancel_escalation()
    protect_set("off", source)
    return True, ""


# ---- fix 4 (Entscheid des Besitzers «Überall im Browser», 10.11.2026): the PIN for everything the browser / the web API
# switches off. Before, only «Aus» (POST /api/arm, /api/protect) asked for it - the mode «Transport», the shortcut address
# /k/<key>/disarm, «all off» of several devices, «Camping off» or «simulation on» switched the protection off without it.
# web_disarms() is the ONE list of these requests; the web server asks it before every POST (pin_guard, 550) and answers
# 403 {"need_pin": true} - the page then shows the PIN question (639zzk) and sends the request again with the header X-MW-PIN.
# A new address that switches off belongs into this list.
# WITHOUT the PIN on purpose (not the browser; Besitzer): the button «Aus» in a push message (/na/, 066 - the secret link
# of this one alarm), MQTT (270 - own user and password), the clap switch (250 - with a PIN it only arms), the buttons on
# the device (163a - own switch «btn_allow_disarm»), a command of another MoveEye (260: it calls /api/arm there - with a
# PIN on that device the answer is «PIN needed», as before) and everything automatic: schedules (030 arm_by_schedule),
# presence (150), «Heute Nacht bewachen» in the morning (130), the modes that end by themselves (mode_tick).
# Not locked out: the administrator knows the PIN; a forgotten PIN: «Reset to factory settings» with the web password
# (586), or the settings file - as before.
def mode_disarms(m, gamer_watch=None):
    """would switching to this mode switch the protection off? (mode_set, 130)"""
    m = str(m or ""); old = CFG.get("mode") or ""
    if m == old or not CFG.get("armed"):
        return False
    if m == "transport":
        return True
    prev = CFG.get("mode_prev") if isinstance(CFG.get("mode_prev"), dict) else {}
    cprev = CFG.get("camping_prev") if isinstance(CFG.get("camping_prev"), dict) else {}
    if m == "":                                          # back to the own settings: armed as it was before the mode
        return not prev.get("armed", True)
    if m == "gamer" and old == "camping" and CFG.get("camping"):   # leaving the camping profile gives its old state back,
        watch = CFG.get("mode_gamer_watch") if gamer_watch is None else gamer_watch    # the gamer mode only arms with «watch on»
        return not watch and not cprev.get("armed", True)
    return False


def web_disarms(path, d):
    """would this POST of the web API switch the protection off? (only asked while armed / arming and with a PIN)"""
    if not CFG.get("armed") or not isinstance(d, dict):
        return False
    if path == "/api/mode":
        return "mode" in d and mode_disarms(d.get("mode"), bool(d["mode_gamer_watch"]) if "mode_gamer_watch" in d else None)
    if path == "/api/camping":
        if d.get("on"):
            return False
        if (CFG.get("mode") or "") == "camping":
            return mode_disarms("")
        cprev = CFG.get("camping_prev") if isinstance(CFG.get("camping_prev"), dict) else {}
        return bool(CFG.get("camping")) and not cprev.get("armed", True)
    if path == "/api/set":
        return d.get("key") == "armed" and not d.get("value")
    if path == "/api/fleet":
        return d.get("action") == "disarm" and d.get("id") in ("all", "me")
    if path == "/api/sim":                               # «disarm and simulate?» (sim_set with confirm, 340)
        return bool(d.get("on")) and bool(d.get("confirm")) and not CFG.get("sim_on")
    if path == "/api/simintern":                         # the same for the simulator on the Pi (639zx)
        return d.get("action") == "start" and bool(d.get("confirm")) and not CFG.get("sim_on")
    return False


def web_pin_guard(path, method, d, pin):
    """None = go on; else the error text for the answer 403 {"need_pin": true}. Called by the web server before a POST."""
    if method != "POST" or not CFG.get("protect_pin") or not web_disarms(path, d):
        return None
    ok, err = protect_pin_check(pin, "web " + path)
    if ok:
        protect_cancel_escalation()
        return None
    return err


# ---- «Schutz testen» ---------------------------------------------------------------------------------------------------
def protect_test(lang=None):
    if PROTECT["test"]["busy"]:
        return False, "a test is already running"
    if CFG.get("sim_on") and simtask_busy("protection test"):
        return False, simtask_refuse("protection test")
    L = norm_lang(lang) if lang else cur_lang()
    PROTECT["test"] = {"busy": True, "steps": [], "t": time.time()}
    threading.Thread(target=_protect_test_run, args=(L,), daemon=True, name="protect-test").start()
    return True, ""


def _protect_test_run(L):
    T = lambda x: tr(x, L)
    S = PROTECT["test"]["steps"]

    def step(name, ok, text=""):
        S.append({"name": name, "ok": ok, "text": text})

    sim = bool(CFG.get("sim_on")) and SIM.get("ok") and time.time() - SIM.get("t", 0) < 5
    try:
        w = WATCH_REF.get("w")
        fresh = w is not None and time.time() - float(getattr(w, "last_frame_t", time.time())) < 5
        step(T("Camera picture"), bool(w is not None), "" if fresh else T("no recent picture"))
        step(T("Push messages"), bool(CFG.get("notify_on")), "" if CFG.get("notify_on") else T("off"))
        step(T("Loudspeaker / siren"), bool(out_selected()), "" if out_selected() else T("no loudspeaker"))
        meta = refscan_meta()
        step(T("Reference scan"), bool(meta), (trf("{n} guarded things", L, n=len(meta.get("watch") or [])) if meta else T("not yet")))
        if not sim:
            step(T("Sabotage and person"), None, T("only automatic with the simulator - test by hand: cover the camera, walk past"))
        else:
            t0 = (STATE.get("tamper") or {}).get("last", "")
            sim_control({"action": "sabotage", "cover": True})
            hit = False
            for _ in range(25):
                time.sleep(1)
                if (STATE.get("tamper") or {}).get("last", "") != t0:
                    hit = True
                    break
            sim_control({"action": "sabotage", "cover": False})
            step(T("Sabotage (camera covered)"), hit, "" if hit else T("not noticed within 25 s"))
            time.sleep(4)
            sim_control({"action": "press", "id": "spawn_person"})
            seen = False
            for _ in range(60):
                time.sleep(1)
                if int(STATE.get("persons") or 0) > 0:
                    seen = True
                    break
            step(T("Person walks past"), seen, "" if seen else T("no person detected within 60 s"))
    except Exception as e:
        step(T("Test"), False, str(e)[:120])
    PROTECT["test"]["busy"] = False
    ok = sum(1 for x in S if x["ok"])
    log_event("sys", f"Protection test: {ok} of {len(S)} ok")


