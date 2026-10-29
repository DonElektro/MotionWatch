#@ MoveEye – Teil 145: Selbstheilung: Wächter für Kamera-Schleife, KI und Webseite, Neustart mit Bremse; Ampeln Speicherkarte und Selbstheilung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Self-healing (Daniel, 29.10.2026). A watchdog thread looks every 15 s:
#  * camera loop: no sign of life (HEART) for 90 s - the loop hangs inside a camera call. Or the source says «connected»,
#    the loop runs, but no new frame came for 150 s. The reconnect of the camera loop (410: read_failures / _good_t) acts
#    after ~6 s; the watchdog only steps in when that did not help for minutes, so the two never fight.
#  * AI: switched on, model loaded, frames come, but the AI has not run for 5 minutes (status stuck) -> the AI is loaded
#    again (only that part); 3 times in an hour -> MoveEye restarts.
#  * web page: http(s)://127.0.0.1:<port>/sw.js does not answer 4 times in a row (2 minutes) -> MoveEye restarts.
# A restart uses the same path as the update / pause (save settings, finish the recording, os.execv, same PID - the
# autostart and the systemd watchdog stay happy). Brake: at least 5 minutes running (doubled after each restart, at most
# 1 hour), at most 2 restarts per hour and 6 per day (kept in <data>/selfheal.json, written only when it restarts). When
# the brake holds, it is logged and one push says so. After a restart the new run logs it and sends one info push.
# Never in tool mode, while paused, during an update or another restart. MOTIONWATCH_NO_SELFHEAL=1 switches it off.
# ----------------------------------------------------------------------------
SELFHEAL = {"on": os.environ.get("MOTIONWATCH_NO_SELFHEAL", "") != "1", "t0": time.time(), "web_fail": 0, "last": [], "ai_fix": deque(maxlen=10),
            "held": {}, "file": None, "started": False, "web_t": 0.0}
SELFHEAL_LOOP_S = 90.0                 # camera loop without a sign of life
SELFHEAL_FRAME_S = 150.0               # «connected», loop alive, but no new frame
SELFHEAL_AI_S = 300.0                  # the AI has not run although it should
SELFHEAL_WEB_FAILS = 4                 # probes in a row without an answer (every 30 s)
SELFHEAL_GRACE_S = 180.0               # after a start: the camera / simulator may take a while
SELFHEAL_PER_HOUR, SELFHEAL_PER_DAY = 2, 6
_SH_TEST = os.environ.get("MOTIONWATCH_SELFHEAL_TEST", "")   # tests only: «web» / «loop» pretend that part hangs
if _SH_TEST:
    SELFHEAL_GRACE_S = float(os.environ.get("MOTIONWATCH_SELFHEAL_GRACE", "20"))


def _sh_file():
    return os.path.join(DATA_DIR, "selfheal.json")


def _sh_load():
    if SELFHEAL["file"] is None:
        try:
            with open(_sh_file()) as f:
                d = json.load(f)
            SELFHEAL["file"] = d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            SELFHEAL["file"] = {}
    return SELFHEAL["file"]


def _sh_save(d):
    SELFHEAL["file"] = d
    try:
        tmp = _sh_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(d, f)
        os.replace(tmp, _sh_file())
    except OSError:
        pass


def selfheal_allowed(now=None):
    """(allowed, reason) - the brake: uptime, per hour, per day"""
    now = now or time.time()
    d = _sh_load()
    ts = [float(t) for t in (d.get("restarts") or []) if isinstance(t, (int, float)) and now - float(t) < 86400]
    hour = [t for t in ts if now - t < 3600]
    six = [t for t in ts if now - t < 6 * 3600]
    need = min(3600.0, 300.0 * (2 ** len(six)))          # 5 min, 10, 20, 40, 60 - a hang right after the start waits longer
    if _SH_TEST:
        need = SELFHEAL_GRACE_S
    up = now - SELFHEAL["t0"]
    if len(hour) >= SELFHEAL_PER_HOUR:
        return False, "max. %d restarts per hour" % SELFHEAL_PER_HOUR
    if len(ts) >= SELFHEAL_PER_DAY:
        return False, "max. %d restarts per day" % SELFHEAL_PER_DAY
    if up < need:
        return False, "running only %d s (needs %d s before a restart)" % (up, need)
    return True, ""


def _sh_note(part, what, held=False):
    SELFHEAL["last"].insert(0, {"t": time.time(), "part": part, "what": what, "held": held})
    del SELFHEAL["last"][10:]


def _sh_push(text):
    w = WATCH_REF.get("w")
    if w is None:
        return
    try:
        w.notifier.info(text, title="{name}: " + tr("Self-healing"))
    except Exception:
        pass


def _sh_hold(part, why, reason):
    """a restart was needed but the brake holds: log it, one push per part and day"""
    k = part
    if time.time() - SELFHEAL["held"].get(k, 0) < 86400 and SELFHEAL["held"].get(k + "_r") == reason:
        return
    SELFHEAL["held"][k] = time.time(); SELFHEAL["held"][k + "_r"] = reason
    log_event("sys", f"Self-healing: {why} - no restart now ({reason})")
    _sh_note(part, why + " · " + "no restart now (limit)", True)
    if "per hour" in reason or "per day" in reason:
        _sh_push(tr(why) + " – " + tr("MoveEye did not restart again (limit reached). Please look at it."))


def selfheal_restart(part, why):
    """restart MoveEye (same process, same options) - only when the brake allows it"""
    ok, reason = selfheal_allowed()
    if not ok:
        _sh_hold(part, why, reason)
        return False
    if RESTART.get("pending"):
        return False
    RESTART["pending"] = "selfheal"
    now = time.time()
    d = dict(_sh_load())
    d["restarts"] = [t for t in (d.get("restarts") or []) if isinstance(t, (int, float)) and now - t < 86400] + [now]
    d["pending"] = {"t": now, "part": part, "why": why}
    _sh_save(d)
    log_event("sys", f"Self-healing: {why} - restarting MoveEye")

    def work():
        try:
            w = WATCH_REF.get("w")
            end = time.time() + 8.0
            while w is not None and getattr(w, "writer", None) is not None and time.time() < end and part != "loop":
                time.sleep(0.2)
            try:
                sound_stop(); talk_stop()
            except Exception:
                pass
            save_settings_now()
            _close_fds_on_exec()
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + _base_args())
        except Exception as e:
            RESTART["pending"] = ""
            log_event("sys", f"Self-healing: restart failed: {e}"[:200])
    threading.Thread(target=work, daemon=True, name="selfheal-restart").start()
    return True


def _sh_after_start():
    """the run after a restart by the watchdog: log it and send one info push (when the messages work again)"""
    d = _sh_load()
    p = d.get("pending")
    if not isinstance(p, dict):
        return
    d = dict(d); d.pop("pending", None); _sh_save(d)
    why = str(p.get("why") or "")
    _sh_note(str(p.get("part") or ""), why + " · " + "restarted")
    log_event("sys", f"Self-healing: started again after «{why}»")
    time.sleep(45)
    _sh_push(tr("MoveEye restarted itself") + ": " + tr(why) + ". " + tr("Everything runs again."))


def _sh_busy():
    """moments in which nothing is judged"""
    try:
        if toolmode_on() or RESTART.get("pending") or PAUSING.get("on") or UPD_PROG.get("phase") or POWER.get("pending"):
            return True
    except NameError:
        pass
    return False


def _sh_web_probe():
    """does the own web page answer? any HTTP answer counts (also 401 / 404)"""
    import http.client
    web = globals().get("WEB")
    if web is None or not getattr(web, "serving", False):
        return None
    host = WEB_OPTS.get("bind") or "127.0.0.1"
    if host in ("0.0.0.0", "", "::"):
        host = "127.0.0.1"
    port = int(CFG["web_port"])
    if _SH_TEST == "web":
        port = 1                                          # tests: nobody answers there
    try:
        if WEB_OPTS.get("https"):
            import ssl
            con = http.client.HTTPSConnection(host, port, timeout=8, context=ssl._create_unverified_context())
        else:
            con = http.client.HTTPConnection(host, port, timeout=8)
        con.request("GET", "/sw.js", headers={"User-Agent": "MoveEye-selfheal"})
        con.getresponse().read(64)
        con.close()
        return True
    except Exception:
        return False


def selfheal_check():
    """one round of the watchdog; returns what it found (for tests)"""
    w = WATCH_REF.get("w")
    now = time.time()
    if w is None or not SELFHEAL["on"] or now - SELFHEAL["t0"] < SELFHEAL_GRACE_S or _sh_busy():
        SELFHEAL["web_fail"] = 0
        return ""
    # --- the camera loop
    hb = now - HEART["t"] + (1000 if _SH_TEST == "loop" else 0)
    if hb > SELFHEAL_LOOP_S:
        selfheal_restart("loop", "The camera loop hung")
        return "loop"
    src = str(STATE.get("source_status") or "")
    good = float(getattr(w, "_good_t", 0.0) or 0.0)
    if src == "connected" and w.cap is not None and good and now - good > SELFHEAL_FRAME_S:
        selfheal_restart("frames", "No new pictures although the camera is connected")
        return "frames"
    # --- the AI (only the part)
    ai = getattr(w, "ai", None)
    if (ai is not None and getattr(ai, "net", None) is not None and CFG.get("ai_enabled") and CFG.get("detection_on", True)
            and not DEMO.get("on") and not helper_ready() and good and now - good < 10):
        last = float(getattr(ai, "_last_run", 0.0) or 0.0)
        since = SELFHEAL.get("ai_since") or now
        SELFHEAL["ai_since"] = since
        if now - max(last, since) > SELFHEAL_AI_S:
            recent = [t for t in SELFHEAL["ai_fix"] if now - t < 3600]
            if len(recent) >= 3:
                selfheal_restart("ai", "The AI got stuck again and again")
                return "ai_restart"
            SELFHEAL["ai_fix"].append(now); SELFHEAL["ai_since"] = now
            log_event("ai", "Self-healing: the AI was stuck - loading it again")
            _sh_note("ai", "The AI was stuck · loaded again")
            try:
                w.ai = AIDetector()
            except Exception as e:
                log_event("ai", f"Self-healing: AI could not be loaded again: {e}"[:200])
            if len(recent) == 0:
                _sh_push(tr("The AI was stuck and was loaded again."))
            return "ai"
    else:
        SELFHEAL["ai_since"] = None
    # --- the web page (every 30 s)
    if now - SELFHEAL["web_t"] >= 30:
        SELFHEAL["web_t"] = now
        ok = _sh_web_probe()
        if ok is False:
            SELFHEAL["web_fail"] += 1
            if SELFHEAL["web_fail"] >= SELFHEAL_WEB_FAILS:
                SELFHEAL["web_fail"] = 0
                selfheal_restart("web", "The web page did not answer")
                return "web"
        else:
            SELFHEAL["web_fail"] = 0
    return ""


def selfheal_loop():
    threading.Thread(target=_sh_after_start, daemon=True, name="selfheal-note").start()
    while True:
        time.sleep(15 if not _SH_TEST else 5)
        try:
            sdcard_tick()
            selfheal_check()
        except Exception as e:
            print(f"self-healing: {e}")


def selfheal_start():
    """started once the camera loop object exists (from the health wrapper or the first look)"""
    if SELFHEAL["started"]:
        return
    SELFHEAL["started"] = True
    threading.Thread(target=selfheal_loop, daemon=True, name="selfheal").start()


def _selfheal_waiter():
    """the program starts its parts in 640; this waits until the camera loop object exists (never in the self-test)"""
    for _ in range(600):
        time.sleep(1.0)
        if WATCH_REF.get("w") is not None:
            selfheal_start()
            return


threading.Thread(target=_selfheal_waiter, daemon=True, name="selfheal-wait").start()


def selfheal_health_item(L):
    T = lambda x: tr(x, L)
    if not SELFHEAL["on"]:
        return {"id": "selfheal", "icon": "🩹", "title": T("Self-healing"), "level": "off", "text": T("off"), "tip": ""}
    day = [x for x in SELFHEAL["last"] if time.time() - x["t"] < 86400]
    if not day:
        return {"id": "selfheal", "icon": "🩹", "title": T("Self-healing"), "level": "ok", "text": T("watching camera, AI and web page"), "tip": ""}
    x = day[0]
    held = bool(x.get("held"))
    return {"id": "selfheal", "icon": "🩹", "title": T("Self-healing"), "level": "bad" if held else "warn",
            "text": datetime.fromtimestamp(x["t"]).strftime("%H:%M") + " " + " · ".join(T(p) for p in x["what"].split(" · ")) + (f" (+{len(day) - 1})" if len(day) > 1 else ""),
            "tip": T("If it happens again: send the diagnosis package (Settings → Help).")}


# ---- the self-check gets the two traffic lights (web and window use health_check) ----------------------------------------
_health_check_base = health_check


def health_check(lang=None):
    h = _health_check_base(lang)
    L = norm_lang(lang) if lang else cur_lang()
    for fn in (sdcard_health_item, selfheal_health_item):
        try:
            h["items"].append(fn(L))
        except Exception as e:
            print(f"health item: {e}")
    h["items"].sort(key=lambda x: HEALTH_ORDER.index(x["level"]))
    h["count"] = {k: sum(1 for x in h["items"] if x["level"] == k) for k in HEALTH_ORDER}
    return h
