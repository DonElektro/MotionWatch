#@ Motion Watch – Teil 130: Scharf / unscharf, Camping-Profil, einfache Einstellungen, Modi. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Armed / disarmed: alarms (push, browser sound, relays, recordings) only while armed. Arming waits a moment first,
# so you can walk away without alarming yourself.
# ----------------------------------------------------------------------------
ARM = {"at": 0.0, "announced": True}


def is_armed():
    return bool(CFG["armed"]) and time.time() >= ARM["at"]


def arm(delay=None):
    try:
        d = float(CFG["arm_delay"] if delay is None else delay)
    except (TypeError, ValueError):
        d = 60.0
    d = max(0.0, min(600.0, d))
    CFG["armed"] = True; ARM["at"] = time.time() + d; ARM["announced"] = d <= 0
    sched_user_changed("armed"); save_settings()
    log_event("sys", f"Armed in {d:.0f} s" if d else "Armed")
    arm_tick()


def disarm():
    CFG["armed"] = False; ARM["at"] = 0.0; ARM["announced"] = True
    sched_user_changed("armed"); save_settings()
    log_event("sys", "Disarmed - no alarms")
    arm_tick()


def arm_tick():
    left = max(0, int(ARM["at"] - time.time() + 0.99)) if CFG["armed"] else 0
    STATE["arm_state"] = "disarmed" if not CFG["armed"] else ("arming" if left > 0 else "armed")
    STATE["arm_left"] = left
    if CFG["armed"] and left == 0 and not ARM["announced"]:
        ARM["announced"] = True
        log_event("sys", "Armed now - alarms are active")
        push_alert("armed", "armed")
        try:
            rehearsal_on_arm()                             # 2.96.8: night rehearsal in the simulation (makeover 23)
        except Exception:
            pass
        try:
            refscan_on_armed()                         # 2.95.97: compare with the reference scan (if wanted)
        except Exception:
            pass


# ----------------------------------------------------------------------------
# Camping profile: one switch for the field. Own Wi-Fi on, the camera stays where it is (zones are drawn on the picture,
# a moving camera would move them), alarms + recordings on, armed after the countdown. Ending it restores everything.
# ----------------------------------------------------------------------------
CAMPING_SET = {"detection_on": True, "record": True, "snapshot_on_person": True, "notify_on": True, "notify_prealarm": True,
               "browser_alarm": True, "relays_on": True, "patrol": False, "track_person": False, "timelapse_on": False,
               "lowlight_auto": True, "rain_auto": True, "wind_auto": True, "show_zones": True, "eco_on": True}


# ---- simple settings: what most people need; Expert shows everything ----
SIMPLE_SECTIONS = {"Camera / Servos", "Patrol", "AI detection", "Detection", "Recording", "Low light", "Setup", "Notifications",
                   "Camping / protection", "Thermal camera", "Microphone", "Loudspeaker", "Clap switch", "Bless you", "Lights", "Night report", "Battery",
                   "Power saving", "Messages", "Updates", "Extra sensors", "Storm warning", "GPS module", "Solar panel", "Mover"}
SIMPLE_KEYS = {"track_person", "track_motion", "patrol", "ai_enabled", "detection_on", "sensitivity", "record", "snapshot_on_person", "record_max_gb",
               "share_gps", "lowlight_auto", "nightvision", "nightvision_auto", "gps_tag", "env_on", "latitude", "longitude",
               "notify_on", "notify_prealarm", "webpush_on", "notify_type", "notify_url", "telegram_token", "telegram_chat",
               "pushover_on", "pushover_user", "pushover_token", "pushover_emergency", "msg_keyword_on", "email_on", "email_to",
               "arm_delay", "net_mode", "hotspot_ssid", "hotspot_password", "thermal_on", "thermal_alarm", "noise_alarm", "audio_in",
               "audio_out", "siren_on", "siren_volume", "siren_sound", "light_white_auto", "light_ir_auto", "report_on", "report_hour",
               "diary_on", "weather_on", "batt_mah", "eco_on", "device_name", "update_auto", "loop_on", "loop_hours",
               "cam_rotate", "cam_mirror", "sens_on", "rf433_on", "zigbee_on", "ble_on", "tag_missing", "eco_pir", "storm_on", "storm_drop", "storm_wind", "mover_mode", "mover_speed", "gpsmod_on", "gps_theft", "lens_check", "temp_alarm_on", "temp_hot", "temp_cold", "solar_on", "night_warn"}


def simple_hidden(key, sec=None):
    """True when Simple is on and this setting (or section) belongs to Expert only."""
    if not CFG.get("ui_simple"):
        return False
    return (sec is not None and sec not in SIMPLE_SECTIONS) or (key is not None and key not in SIMPLE_KEYS)


NIGHT_SET = {"detection_on": True, "ai_enabled": True, "record": True, "snapshot_on_person": True, "notify_on": True,
             "notify_prealarm": True, "lowlight_auto": True, "nightvision_auto": True, "report_on": True, "diary_on": True,
             "eco_on": True, "timelapse_on": False}


def night_guard(lang=None):
    """«Guard tonight»: what a night needs on, armed after the countdown; returns what was done and what is missing."""
    L = norm_lang(lang) if lang else cur_lang()
    done = []
    for k, v in NIGHT_SET.items():
        if k in CFG and CFG[k] != v:
            CFG[k] = v; sched_user_changed(k)
    if (STATE.get("audio") or {}).get("status") == "listening" and not CFG["noise_alarm"]:
        CFG["noise_alarm"] = True; done.append(tr("Noise alarm on", L))
    if STATE.get("thermal") == "connected" and not CFG["thermal_alarm"]:
        CFG["thermal_alarm"] = True; done.append(tr("Thermal alarm on", L))
    save_settings()
    done = [tr("Detection, AI and recordings on", L), tr("Push messages on", L), tr("Night vision and low light automatic", L),
            tr("Night report in the morning", L) + f" ({int(CFG['report_hour']):02d}:00)", tr("Power saving on", L)] + done
    arm()
    d = int(float(CFG["arm_delay"]))
    done.append(trf("Armed in {s} s - leave the area now", L, s=d) if d else tr("Armed", L))
    h = health_check(L)
    miss = [{"icon": x["icon"], "title": x["title"], "text": x["text"], "tip": x["tip"], "level": x["level"]}
            for x in h["items"] if x["level"] == "bad" or (x["level"] == "warn" and x["id"] in ("servo", "net", "power", "temp", "disk", "batt"))]
    log_event("sys", "Guard tonight: armed" + (f", {len(miss)} problem(s) open" if miss else ""))
    return {"ok": True, "done": done, "missing": miss}


# ---- power mode (2.95.19): the counterpart of power saving - every picture through the AI, bigger processing, best
# stream, the simulator at full speed, the processor at its highest clock. Switching it off restores everything. ----
TURBO_SET = {"eco_on": False, "ai_every": 1, "proc_width": 640, "web_quality": 88, "web_width": 1920, "sim_eco": False, "sim_fps": 15}
_GOV = "/sys/devices/system/cpu/cpu{}/cpufreq/scaling_governor"


def _governor(want=None):
    """read (want=None) or set the governor of all processor cores; returns the old one (or "" if not possible)"""
    old = ""
    try:
        with open(_GOV.format(0)) as f:
            old = f.read().strip()
    except OSError:
        return ""
    if want:
        for i in range(os.cpu_count() or 4):
            try:
                with open(_GOV.format(i), "w") as f:
                    f.write(want)
            except OSError:
                pass
    return old


def turbo_set(on, who="web"):
    on = bool(on)
    if on and not CFG["turbo_on"]:
        prev = {k: CFG[k] for k in TURBO_SET if k in CFG}
        prev["_governor"] = _governor()
        CFG["turbo_prev"] = prev
        for k, v in TURBO_SET.items():
            if k in CFG:
                CFG[k] = v; sched_user_changed(k)
        g_ = _governor("performance")
        CFG["turbo_on"] = True
        log_event("sys", f"Power mode ON ({who}): every picture through the AI, best quality" + ("" if g_ else " (processor clock: not allowed without root)"))
    elif not on and CFG["turbo_on"]:
        prev = CFG["turbo_prev"] if isinstance(CFG["turbo_prev"], dict) else {}
        for k, v in prev.items():
            if k in CFG and isinstance(v, type(CFG[k])):
                CFG[k] = v
        if prev.get("_governor"):
            _governor(prev["_governor"])
        CFG["turbo_on"] = False; CFG["turbo_prev"] = {}
        log_event("sys", f"Power mode OFF ({who}) - previous settings restored")
    save_settings()
    return True, ""


# ---- modes (2.95.47): one switch sets up the whole device. Camping guard, campfire games (battery, little power - the
# guard watches on sparingly), gamer (only with mains power - power mode, all games), home, wildlife, night guard,
# transport. «Own settings» (no mode) brings back what was set before the first mode. ----
MODES = [("camping", "⛺", "Camping guard"), ("fire", "🔥", "Campfire games"), ("gamer", "🎮", "Gamer"), ("home", "🏠", "Home / garden"),
         ("wild", "🦌", "Wildlife watching"), ("night", "🌙", "Night guard"), ("transport", "🔕", "Transport / rest")]
MODE_INFO = {
    "": "Your own settings, no mode.",
    "camping": "Full guard: alarms, recordings, own Wi-Fi, armed after the countdown. Power saving while all is quiet.",
    "fire": "The game corner is open for the phones (in the Wi-Fi MoveEye is in). The guard watches on sparingly: few pictures, the AI only at movement - an animal at the tent is still reported. Back to the camping guard at the set time or when the battery gets low.",
    "gamer": "Only with mains power: power mode, all games and the game collection, the best picture. The guard only if you want it. On battery MoveEye goes back to the campfire games by itself.",
    "home": "Guarding house and garden: alarms and recordings on, no own Wi-Fi, no camping profile.",
    "wild": "Animals: no siren, the light does not go on by itself (it would scare them), many pictures, the camera follows what moves.",
    "night": "The highest attention: more sensitive, thermal alarm, infrared light by itself, the pre-alarm too.",
    "transport": "Rest while travelling: no detection, no recordings, no alarms - only the battery, GPS theft and tamper protection stay on.",
}
MODE_SETS = {
    "fire": {"eco_on": True, "ai_every": 3, "proc_width": 416, "web_quality": 60, "web_width": 960, "patrol": False, "track_person": False,
             "track_motion": False, "timelapse_on": False, "notify_prealarm": False, "detection_on": True, "notify_on": True, "record": True},
    "home": {"detection_on": True, "record": True, "snapshot_on_person": True, "notify_on": True, "notify_prealarm": False, "eco_on": False},
    "wild": {"detection_on": True, "siren_on": "off", "light_white_auto": False, "record": True, "snapshot_on_person": True, "notify_prealarm": True,
             "track_motion": True, "track_person": True, "eco_on": False, "lowlight_auto": True},
    "night": {"detection_on": True, "sensitivity": 75, "notify_prealarm": True, "light_ir_auto": True, "nightvision_auto": True, "record": True,
              "snapshot_on_person": True, "notify_on": True, "eco_on": False},
    "transport": {"detection_on": False, "record": False, "timelapse_on": False, "patrol": False, "track_person": False, "track_motion": False,
                  "eco_on": True, "notify_prealarm": False},
}
MODE_RT = {"msg": "", "gov": "", "party": False, "hotspot": False, "turbo": False, "rest": False, "checked": 0.0}


def mode_power():
    """(mains power?, why not) - the gamer mode needs it. Unknown supply (no UPS HAT, no voltage reading) counts as mains."""
    b = STATE.get("battery") or {}
    sup = STATE.get("supply") or {}
    if b.get("on") and b.get("on_battery"):
        return False, "runs on the battery"
    if sup.get("uv_now"):
        return False, "under-voltage: the power supply is too weak"
    return True, ""


def _mode_keys():
    ks = set()
    for d in MODE_SETS.values():
        ks.update(d)
    return [k for k in ks if k in CFG] + ["armed", "thermal_alarm"]


def _mode_leave(m):
    """undo what the mode switched on (camping profile, power mode, game corner, rest, Wi-Fi, governor)"""
    if m == "camping" and CFG["camping"]:
        camping_set(False)
    if MODE_RT["turbo"] and CFG["turbo_on"]:
        turbo_set(False, "mode")
    MODE_RT["turbo"] = False
    if MODE_RT["rest"] and toolmode_on() and TOOLMODE.get("by") == "gamer mode":
        toolmode_set(0, "gamer mode")
    MODE_RT["rest"] = False
    if MODE_RT["party"] and party_on():
        party_close()
    MODE_RT["party"] = False
    if MODE_RT["gov"]:
        _governor(MODE_RT["gov"])
        MODE_RT["gov"] = ""
    if MODE_RT.get("tv"):
        tv_show(False, "mode")
        MODE_RT["tv"] = False


def mode_set(m, who="web"):
    """switch the device to a mode ("" = own settings again)"""
    m = str(m or "")
    if m and m not in dict((x[0], x) for x in MODES):
        return False, "unknown mode"
    if m == "gamer":
        ok, why = mode_power()
        if not ok:
            return False, "The gamer mode needs mains power: " + why
    old = CFG.get("mode") or ""
    if old == m:
        return True, ""
    _mode_leave(old)
    prev = CFG["mode_prev"] if isinstance(CFG["mode_prev"], dict) else {}
    if not old:                                             # first mode: keep the own settings
        prev = {k: CFG[k] for k in _mode_keys()}
        prev["hotspot_on"] = bool((STATE.get("hotspot") or {}).get("on"))
        CFG["mode_prev"] = prev
    for k, v in prev.items():                               # every mode starts from the own settings
        if k in CFG and k not in ("armed", "hotspot_on") and isinstance(v, type(CFG[k])):
            CFG[k] = v
    CFG["mode"] = m
    CFG["mode_since"] = time.time()
    if not m:                                               # own settings again
        if prev.get("armed", CFG["armed"]):
            arm()
        else:
            disarm()
        if not prev.get("hotspot_on", False) and (STATE.get("hotspot") or {}).get("on") and MODE_RT["hotspot"]:
            hotspot_switch_later(False, 2.0)
        MODE_RT["hotspot"] = False
        CFG["mode_prev"] = {}
        log_event("sys", f"Mode off ({who}): own settings again")
        save_settings()
        return True, ""
    for k, v in MODE_SETS.get(m, {}).items():
        if k in CFG:
            CFG[k] = v; sched_user_changed(k)
    hs_on = bool((STATE.get("hotspot") or {}).get("on"))
    if m == "camping":
        camping_set(True)
    elif m in ("fire", "gamer"):
        # 2.95.49: the Wi-Fi is NOT switched here - the own Wi-Fi would cut the phones off the network they are in (the
        # page froze). The game corner works in the network MoveEye is in; the own Wi-Fi is a switch of its own.
        if not party_on():
            party_open(float(CFG["mode_fire_hours"]) if m == "fire" else 8.0); MODE_RT["party"] = True
        if m == "fire":
            g = _governor("powersave")
            if g:
                MODE_RT["gov"] = g
            arm()                                           # the guard watches on, sparingly
        else:
            turbo_set(True, "gamer mode"); MODE_RT["turbo"] = True
            if CFG["mode_gamer_watch"]:
                arm()
            else:
                toolmode_set(720, "gamer mode"); MODE_RT["rest"] = True
    elif m in ("home", "wild", "night"):
        if CFG["thermal_source"] and m == "night":
            CFG["thermal_alarm"] = True
        arm()
    elif m == "transport":
        disarm()
        g = _governor("powersave")
        if g:
            MODE_RT["gov"] = g
    if m in ("fire", "gamer") and CFG.get("tv_auto") and (_tv_browser() or (SIMPI["proc"] is not None and SIMPI["proc"].poll() is None)):
        tv_show(True, "mode")                               # 2.95.51: the TV view on the HDMI (if a desktop is there)
        MODE_RT["tv"] = True
    MODE_RT["msg"] = ""
    log_event("sys", f"Mode «{dict((x[0], x[2]) for x in MODES)[m]}» on ({who})")
    save_settings()
    return True, ""


def mode_tick():
    """every 10 s: the campfire ends at its time or when the battery gets low; the gamer mode falls back without mains power"""
    m = CFG.get("mode") or ""
    w = WATCH_REF.get("w")
    def push(txt):
        MODE_RT["msg"] = txt
        log_event("sys", txt)
        if w is not None:
            try:
                w.notifier.info(tr(txt), title="{name}: " + tr("Mode"))
            except Exception:
                pass
    if m == "fire":
        b = STATE.get("battery") or {}
        until = str(CFG.get("mode_fire_until") or "")
        late = False
        if re.match(r"^\d{1,2}:\d{2}$", until):
            hh, mm = map(int, until.split(":"))
            now = datetime.now(); since = datetime.fromtimestamp(float(CFG.get("mode_since") or 0))
            end = now.replace(hour=hh % 24, minute=mm % 60, second=0, microsecond=0)
            late = since < end <= now or (end < since and now.date() > since.date() and now >= end)
        low = b.get("on") and b.get("on_battery") and b.get("pct") is not None and float(b["pct"]) < float(CFG["mode_fire_min_pct"])
        if late or low:
            mode_set("camping", "auto")
            push("Campfire games ended (" + ("battery low" if low else "time") + ") - camping guard on")
    elif m == "gamer":
        ok, why = mode_power()
        if not ok:
            mode_set("fire", "auto")
            push("Gamer mode: no mains power any more - campfire games on (" + why + ")")


def mode_state():
    ok, why = mode_power()
    m = CFG.get("mode") or ""
    return {"id": m, "since": CFG.get("mode_since") or 0, "msg": MODE_RT["msg"], "power_ok": ok, "power_why": why,
            "list": [{"id": i, "icon": ic, "name": n, "info": MODE_INFO[i]} for i, ic, n in MODES], "own_info": MODE_INFO[""],
            "fire_until": CFG["mode_fire_until"], "fire_min_pct": CFG["mode_fire_min_pct"], "gamer_watch": bool(CFG["mode_gamer_watch"]),
            "camping": bool(CFG["camping"])}


def turbo_state():
    return {"on": bool(CFG["turbo_on"]), "gov": _governor() if CFG["turbo_on"] else "", "temp": STATE.get("cpu_temp"), "cpu": STATE.get("cpu")}


def camping_set(on, hotspot_delay=2.0):
    netauto_pause()
    if on and not CFG["camping"]:
        prev = {k: CFG[k] for k in list(CAMPING_SET) + ["thermal_alarm", "armed", "hotspot_on"]}
        CFG["camping_prev"] = prev
        for k, v in CAMPING_SET.items():
            CFG[k] = v; sched_user_changed(k)
        if CFG["thermal_source"]:
            CFG["thermal_alarm"] = True
        CFG["camping"] = True
        log_event("sys", "Camping profile ON")
        arm()
        if wifi_backend() == "nm" and not STATE["hotspot"].get("on"):
            hotspot_switch_later(True, hotspot_delay)
    elif not on and CFG["camping"]:
        prev = CFG["camping_prev"] if isinstance(CFG["camping_prev"], dict) else {}
        for k, v in prev.items():
            if k in CFG and k not in ("armed", "hotspot_on") and isinstance(v, type(CFG[k])):
                CFG[k] = v
        CFG["camping"] = False; CFG["camping_prev"] = {}
        log_event("sys", "Camping profile OFF - previous settings restored")
        if prev.get("armed", True):
            CFG["armed"] = True; ARM["at"] = 0.0; ARM["announced"] = True; arm_tick()
        else:
            disarm()
        if not prev.get("hotspot_on", False) and STATE["hotspot"].get("on"):
            hotspot_switch_later(False, hotspot_delay)
    save_settings()
    return True, ""


