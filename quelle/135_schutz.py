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


def protect_set(level, who="web", answers=None):
    """switch the level; answers of the assistant (what, when, how) adjust what is switched on"""
    if level not in PROTECT_LEVELS:
        return False, "unknown level"
    A = answers or {}
    if level == "off":
        CFG["protect_level"] = "off"
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
    CFG["escalate_on"] = react == "siren"
    if react in ("light", "siren"):
        CFG["light_white_auto"] = "alarm_dark" if CFG.get("light_white_auto") in ("", "dark") else CFG["light_white_auto"]
    if react == "siren" and CFG.get("siren_on") == "off":
        CFG["siren_on"] = "person"
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


# ---- the traffic light ---------------------------------------------------------------------------------------------------
_PROT_CACHE = {"t": 0.0, "k": "", "v": None}


def protect_status(lang=None, force=False):
    """the state for the page (cached 3 s - the page asks every second)"""
    L = norm_lang(lang) if lang else cur_lang()
    k = L + str(CFG["armed"]) + str(CFG.get("protect_level")) + str(PROTECT["test"]["busy"]) + str(len(PROTECT["test"]["steps"]))
    if not force and _PROT_CACHE["v"] is not None and _PROT_CACHE["k"] == k and time.time() - _PROT_CACHE["t"] < 3.0:
        v = dict(_PROT_CACHE["v"]); v["arm"] = STATE.get("arm_state"); v["left"] = STATE.get("arm_left", 0)
        return v
    v = _protect_status(L)
    _PROT_CACHE.update(t=time.time(), k=k, v=v)
    return v


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
            "presence": {"on": bool(CFG.get("presence_auto")), "devices": len(CFG.get("presence_macs") or []) + len(CFG.get("presence_bt") or []),
                         "here": (TOOLS.get("presence") or {}).get("here")},
            "escalate": {"on": bool(CFG.get("escalate_on")), "s": int(CFG.get("escalate_siren_s", 30)), "pending": max(0, int(PROTECT["esc_t"] - time.time())) if PROTECT["esc_t"] else 0},
            "test": PROTECT["test"]}


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
        if siren_quiet():
            log_event("sys", "Escalation: siren held back (simulation / game / drill)")
            return
        if time.time() - SOUND["last_alarm"] < float(CFG["siren_pause"]):
            return
        if is_armed() and out_selected() and not SOUND["playing"]:
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


def protect_disarm(pin, source="web"):
    """disarm with the PIN (if one is set). 3 wrong PINs within 10 minutes: theft alarm (push with picture)"""
    now = time.time()
    PROTECT["pin_fails"] = [t for t in PROTECT["pin_fails"] if now - t < 600]
    if len(PROTECT["pin_fails"]) >= 5:
        return False, "too many wrong PINs - try again in 10 minutes"
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
    protect_cancel_escalation()
    protect_set("off", source)
    return True, ""


# ---- «Schutz testen» ---------------------------------------------------------------------------------------------------
def protect_test(lang=None):
    if PROTECT["test"]["busy"]:
        return False, "a test is already running"
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


