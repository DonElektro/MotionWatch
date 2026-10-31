#@ MoveEye – Teil 579b: Nacht-Testlauf mit dem 3D-Simulator (eine ganze Nacht mit Wahrheit, Abgleich Treffer / verpasst / Fehlalarme mit Ursache, Bericht am Morgen mit Push, Verlauf der letzten 10 Läufe, JSON), Kachel 🌙 in der Simulator-Zentrale, Seite /nacht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «Nacht-Testlauf» (Daniel 31.10.2026). The simulator (nachtlauf.gd, control «nacht») plays a seeded night: toilet
# trips (some with a torch), cat / fox / hedgehog, a late car, one hour of rain, wind, fog in the morning and EXACTLY ONE
# real incident (somebody sneaks to the tent / bike / caravan). It writes down every event with start / end and place
# («Wahrheit»). MoveEye logs what it did: its alarms (Notifier.person / prealarm, before the push rules: quiet hours and
# the 60 s pause do not hide an alarm), the pushes (list «Nachrichten»), what it detected (persons / animals / motion),
# battery, Pi temperature and pictures per second, and small pictures of the key moments. At the end both are matched
# (nacht_match: time window + kind) -> incident detected yes / no + seconds, false alarms by cause, misses.
#  * Only the owner (role admin, not in operator mode 390) starts / stops it and sets the schedule; in operator mode the
#    page shows the reports only (nacht_may). The schedule (nacht_auto_on, default off) starts it once a night at
#    nacht_auto_hour (real clock), not in operator mode.
#  * Safety: only with the simulator connected. During the run protection «Voll» (protect_set, 135) - the previous state
#    and the touched settings come back afterwards (also after a restart: CFG «nacht_restore»). The test inbox is
#    forced (SANDBOX force, 141) -> no push reaches the phone as a real alarm and the siren plays only in the simulator
#    (siren_quiet / sim_speaker_only, 554); relays stay off (relays_on False). The report push at the end is an info
#    message, marked «[SIM]» / 🧪 (Notifier._title adds [SIM] in the simulation).
#  * One lock (147): «night test run» while it runs - the simulator refuses its own tests meanwhile and its automatics
#    (real weather, surprise night …) rest (busy_with «Nacht-Testlauf»).
# Window: part 599d. Translations and the manual: part 599e.
# ----------------------------------------------------------------------------
for _k, _v in {"nacht_auto_on": False, "nacht_auto_hour": 23, "nacht_auto_day": "", "nacht_restore": {},
               "nacht_opts": {"scene": "", "busy": "normal", "tempo": "schnell", "from": "20:00", "to": "07:00"}}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

NACHT = {"busy": False, "stop": False, "step": "", "err": "", "runs": None, "live": None, "prog": ""}
NACHT_FILE = "nacht_runs.json"
NACHT_KEEP_RUNS = 10
NACHT_BUSY = ("ruhig", "normal", "viel")
NACHT_TEMPO = {"echt": 1.0, "schnell": 8.0}
# the settings the run touches (protect_set «full» + relays) - put back afterwards
NACHT_KEYS = ("armed", "protect_level", "notify_on", "tamper_on", "gps_theft", "refscan_on_arm", "escalate_on", "siren_on",
              "light_white_auto", "relays_on")
NACHT_ALARM_EVS = ("person", "warm", "prealarm", "noise", "tamper")
NACHT_PRIO = {"incident": 0, "people": 1, "animal": 2, "vehicle": 3, "weather": 4}
# cause keys of the simulator (nachtlauf.gd KINDS) -> English text (translated in 599e)
NACHT_CAUSES = {"wc": "Toilet trip (own people)", "wc_torch": "Toilet trip with torch", "cat": "Cat", "fox": "Fox", "hedgehog": "Hedgehog",
                "car": "Headlights (late car)", "rain": "Rain", "wind": "Wind", "fog": "Fog", "unknown": "nothing in the plan (unknown)",
                "incident": "Incident",
                # Bergtal-Abenteuer A1 (Simulator abenteuer_moveeye.gd): seltene Tiere und das Licht am Berg (Hinweis)
                "lynx": "Lynx", "ibex": "Ibex", "marmot": "Marmot", "eagle": "Golden eagle", "vulture": "Bearded vulture",
                "light": "Light on the mountain",
                # 2.98.104: older causes of the Bergtal night (bergtal.gd night_log, abenteuer_moveeye.gd) - before shown raw
                "chamois": "Chamois", "cow": "Cow", "hare": "Hare", "stoat": "Stoat", "deer": "Deer", "rockfall": "Rockfall",
                "storm": "Thunderstorm"}
NACHT_TARGETS = {"tent": "Somebody sneaks to the tent", "bike": "Somebody sneaks to the bike", "door": "Somebody sneaks to the caravan / car"}


# ---- who may ----------------------------------------------------------------------------------------------------------
def nacht_may(role="admin", locked=None):
    """start / stop / schedule: only the owner (administrator), never in operator mode"""
    lk = bool(CFG.get("lock_on")) if locked is None else bool(locked)
    return role == "admin" and not lk


def _nacht_role():
    try:
        from flask import g as _g, has_request_context
        return getattr(_g, "role", "admin") if has_request_context() else "admin"
    except Exception:
        return "admin"


# ---- times ------------------------------------------------------------------------------------------------------------
def nacht_hm(s, dflt):
    """«20:00» / «7» / 20.5 -> hours (float)"""
    try:
        if isinstance(s, (int, float)):
            return max(0.0, min(23.99, float(s)))
        m = re.fullmatch(r"\s*(\d{1,2})(?::(\d{2}))?\s*", str(s))
        if not m or int(m.group(1)) > 23 or int(m.group(2) or 0) > 59:
            return dflt
        return int(m.group(1)) + int(m.group(2) or 0) / 60.0
    except (TypeError, ValueError):
        return dflt


def nacht_clock(h):
    if h is None:
        return "–"
    h = float(h) % 24.0
    return "%02d:%02d" % (int(h), int(round((h % 1) * 60)) % 60)


def nacht_opts(d=None):
    """the options of a run, checked (scene, liveliness, tempo, start / end)"""
    d = dict(CFG.get("nacht_opts") or {}, **(d or {}))
    busy = str(d.get("busy") or "normal")
    tempo = str(d.get("tempo") or "schnell")
    o = {"scene": re.sub(r"[^A-Za-z0-9_\-]", "", str(d.get("scene") or ""))[:40], "busy": busy if busy in NACHT_BUSY else "normal",
         "tempo": tempo if tempo in NACHT_TEMPO else "schnell", "from": nacht_clock(nacht_hm(d.get("from"), 20.0)), "to": nacht_clock(nacht_hm(d.get("to"), 7.0))}
    try:
        if d.get("speed") is not None:                     # tests: another clock speed (1 … 60)
            o["speed"] = max(1.0, min(60.0, float(d["speed"])))
        if d.get("seed") is not None:
            o["seed"] = max(1, min(999999, int(d["seed"])))
    except (TypeError, ValueError):
        pass
    return o


# ---- the matching (pure: tested in the self-test) ------------------------------------------------------------------------
def nacht_dedupe(alarms, same=10.0):
    """the alarms sorted; one within `same` s after the one before counts as a repeat (the same event, like the test bench)"""
    out, last = [], -1e9
    for a in sorted(alarms or [], key=lambda x: float(x.get("t", 0))):
        if str(a.get("ev")) not in NACHT_ALARM_EVS:
            continue
        a = dict(a, rep=float(a["t"]) - last < same)
        last = float(a["t"])
        out.append(a)
    return out


def _nacht_seen_near(e, t, pre=3.0, post=6.0):
    """0 = the event was visible for the camera just before the alarm (vis_iv of the simulator), 1 = it was not,
    0.5 = unknown (no intervals) - an alarm belongs first to what the camera could see"""
    iv = e.get("vis_iv")
    if not isinstance(iv, list):
        return 0.5
    return 0 if any(float(a) - pre <= t <= float(b) + post for a, b in iv) else 1


def nacht_match(truth, alarms, dets=None, pre=3.0, post=10.0, same=10.0):
    """truth = events of the simulator [{id, kind, cat, cause, t0, t1, first_vis, vis_s}], alarms = [{t, ev}] of MoveEye,
    dets = detection segments [{k: person|animal|motion, t0, t1}] (all in seconds since the start of the run).
    An alarm belongs to an event that runs at that time (t0 - pre … t1 + post); several: the most important one
    (incident > own people > animal > vehicle > weather), then the nearest. The incident with an alarm = detected; every
    other alarm (not a repeat within `same` s) is a false alarm with the cause of its event, without one «unknown»."""
    T = [dict(e) for e in truth or [] if isinstance(e, dict)]
    for e in T:
        e["t1"] = float(e["t1"]) if e.get("t1") is not None and float(e["t1"]) >= float(e.get("t0", 0)) else float(e.get("t0", 0))
    A = nacht_dedupe(alarms, same)
    hits, false_, reps = [], [], 0
    for a in A:
        t = float(a["t"])
        cand = [e for e in T if float(e["t0"]) - pre <= t <= float(e["t1"]) + post
                and not (a.get("ev") == "tamper" and e.get("cat") == "incident")]   # a sabotage alarm is never the detection of the incident
        cand.sort(key=lambda e: (_nacht_seen_near(e, t, pre), NACHT_PRIO.get(e.get("cat"), 5), 0 if float(e["t0"]) <= t <= float(e["t1"]) else 1,
                                 min(abs(t - float(e["t0"])), abs(t - float(e["t1"])))))
        e = cand[0] if cand else None
        if e is not None and e.get("cat") == "incident":
            hits.append({"t": round(t, 1), "ev": a.get("ev"), "id": e.get("id"), "rep": bool(a["rep"])})
            continue
        if a["rep"]:
            reps += 1
            continue
        false_.append({"t": round(t, 1), "ev": a.get("ev"), "cause": (e or {}).get("cause") or "unknown", "id": (e or {}).get("id"),
                       "img": a.get("img"), "h": a.get("h")})
    by = {}
    for f in false_:
        by[f["cause"]] = by.get(f["cause"], 0) + 1
    inc = next((e for e in T if e.get("cat") == "incident"), None)
    D = [dict(x) for x in dets or [] if isinstance(x, dict)]

    def det_in(e, kinds):
        """the first detection of these kinds while the event runs (seconds) or None"""
        s = [float(x["t0"]) for x in D if x.get("k") in kinds and float(x["t0"]) <= float(e["t1"]) + post
             and float(x.get("t1", x["t0"])) >= float(e["t0"]) - pre]
        return max(float(e["t0"]), min(s)) if s else None
    I = None
    if inc is not None:
        ref = float(inc["first_vis"]) if inc.get("first_vis") is not None and float(inc["first_vis"]) >= 0 else float(inc["t0"])
        first = min((h["t"] for h in hits), default=None)
        d0 = det_in(inc, ("person",))
        I = {"id": inc.get("id"), "target": inc.get("target") or "", "t0": inc["t0"], "t1": inc["t1"], "h0": inc.get("h0"),
             "first_vis": inc.get("first_vis"), "vis_s": inc.get("vis_s"), "detected": first is not None,
             "ttd_s": round(max(0.0, first - ref), 1) if first is not None else None,
             "alarm_after_start_s": round(first - float(inc["t0"]), 1) if first is not None else None,
             "det_s": round(max(0.0, d0 - ref), 1) if d0 is not None else None, "alarms": len(hits)}
    misses = []                                         # visible for the camera, but MoveEye detected nothing of it
    for e in T:
        if e.get("cat") in ("weather",) or float(e.get("vis_s") or 0) < 1.0:
            continue
        kinds = ("person",) if e.get("cat") in ("people", "incident") else (("person", "animal", "motion") if e.get("cat") == "animal" else ("person", "animal", "motion", "vehicle"))
        if e.get("cat") == "incident" and I and I["detected"]:
            continue
        if det_in(e, kinds) is None and not (e.get("cat") == "incident" and I and I["detected"]):
            misses.append({"id": e.get("id"), "kind": e.get("kind"), "cat": e.get("cat"), "cause": e.get("cause"), "t0": e["t0"],
                           "h0": e.get("h0"), "vis_s": e.get("vis_s"), "incident": e.get("cat") == "incident"})
    return {"incident": I, "false": len(false_), "false_by": by, "false_list": false_, "repeats": reps, "hits": hits,
            "alarms": len(A), "misses": misses, "missed_incident": bool(I and not I["detected"])}


def nacht_segments(samples, gap=1.5):
    """[(t, {person, animal, motion})] every ~0.5 s -> segments [{k, t0, t1}] (a gap below `gap` s joins them)"""
    out, cur = [], {}
    for t, ks in samples:
        for k in ("person", "animal", "motion"):
            if k in ks:
                if k in cur and t - cur[k]["t1"] <= gap:
                    cur[k]["t1"] = t
                else:
                    if k in cur:
                        out.append(cur[k])
                    cur[k] = {"k": k, "t0": t, "t1": t}
    out.extend(cur.values())
    return sorted(out, key=lambda x: x["t0"])


# ---- runs on disk -----------------------------------------------------------------------------------------------------
def _nacht_path():
    return os.path.join(DATA_DIR, NACHT_FILE)


def _nacht_pic_dir(rid=""):
    return os.path.join(DATA_DIR, "nacht", re.sub(r"[^0-9]", "", str(rid))) if rid else os.path.join(DATA_DIR, "nacht")


def nacht_runs():
    if NACHT["runs"] is None:
        try:
            with open(_nacht_path(), encoding="utf-8") as f:
                d = json.load(f)
            NACHT["runs"] = d.get("runs") if isinstance(d.get("runs"), list) else []
        except (OSError, ValueError):
            NACHT["runs"] = []
    return NACHT["runs"]


def _nacht_save():
    runs = nacht_runs()
    del runs[:-NACHT_KEEP_RUNS]
    try:
        tmp = _nacht_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"runs": runs}, f, ensure_ascii=False)
        os.replace(tmp, _nacht_path())
    except OSError:
        pass
    try:                                                # pictures of older runs away
        keep = {str(r.get("id")) for r in runs}
        base = _nacht_pic_dir()
        if os.path.isdir(base):
            for n in os.listdir(base):
                if n not in keep:
                    import shutil
                    shutil.rmtree(os.path.join(base, n), ignore_errors=True)
    except OSError:
        pass


def nacht_run_by(rid):
    for r in nacht_runs():
        if str(r.get("id")) == str(rid):
            return r
    return None


def nacht_summary(r):
    """one line of the comparison (last 10 runs, per MoveEye version)"""
    res = r.get("result") or {}
    I = res.get("incident") or {}
    return {"id": r.get("id"), "t": r.get("t"), "mw": r.get("mw_version"), "sim": r.get("sim_version"), "scene": (r.get("opts") or {}).get("scene"),
            "busy": (r.get("opts") or {}).get("busy"), "tempo": (r.get("opts") or {}).get("tempo"), "from": (r.get("opts") or {}).get("from"),
            "to": (r.get("opts") or {}).get("to"), "inc": bool(I.get("detected")), "ttd": I.get("ttd_s"), "fa": res.get("false", 0),
            "miss": len(res.get("misses") or []), "stopped": bool(r.get("stopped")), "auto": bool(r.get("auto")), "seed": r.get("seed")}


# ---- what MoveEye does during the run (alarms, pictures) -----------------------------------------------------------------
def _nacht_thumb(frame, rid, n):
    """a small picture of a key moment (320 px wide) -> the file name, or None"""
    if frame is None or n > 14:
        return None
    try:
        h, w = frame.shape[:2]
        img = cv2.resize(frame, (320, max(1, int(h * 320 / max(1, w)))), interpolation=cv2.INTER_AREA) if w > 320 else frame
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            return None
        d = _nacht_pic_dir(rid)
        os.makedirs(d, exist_ok=True)
        name = "m%02d.jpg" % n
        with open(os.path.join(d, name), "wb") as f:
            f.write(buf.tobytes())
        return name
    except Exception:
        return None


def _nacht_moment(label, kind, frame=None):
    L = NACHT.get("live")
    if not L:
        return
    if frame is None:
        try:
            frame = WATCH_REF["w"].frame_out
        except Exception:
            frame = None
    n = len(L["moments"]) + 1
    img = _nacht_thumb(frame, L["id"], n)
    L["moments"].append({"t": round(time.time() - L["T0"] - L["off"], 1), "h": L.get("hour"), "label": label, "kind": kind, "img": img})


def _nacht_alarm(ev, frame=None):
    """an alarm decision of MoveEye during the run (before the push rules)"""
    L = NACHT.get("live")
    if not L or not is_armed():
        return
    t = time.time() - L["T0"] - L["off"]
    if L["alarms"] and t - L["alarms"][-1]["t"] < 2.0 and L["alarms"][-1]["ev"] == ev:
        return                                          # the same decision twice in a frame or two
    a = {"t": round(t, 1), "ev": ev, "h": L.get("hour")}
    L["alarms"].append(a)
    if sum(1 for m in L["moments"] if m["kind"] == "alarm") < 8:
        _nacht_moment(ev, "alarm", frame)
        a["img"] = L["moments"][-1].get("img")


_nacht_person_before = Notifier.person
_nacht_prealarm_before = Notifier.prealarm


def _nacht_person(self, count, snapshot_path=None, frame=None):
    if count and NACHT.get("live"):
        _nacht_alarm("person", frame)
    return _nacht_person_before(self, count, snapshot_path, frame)


def _nacht_prealarm(self, frame, event="prealarm"):
    if NACHT.get("live"):
        _nacht_alarm(event if event in ("warm", "noise") else "prealarm", frame)
    return _nacht_prealarm_before(self, frame, event)


# wraps: Notifier.person
Notifier.person = _nacht_person
# wraps: Notifier.prealarm
Notifier.prealarm = _nacht_prealarm


# ---- the run ------------------------------------------------------------------------------------------------------------
def _nacht_restore(snap):
    """put back what the run changed (protection, its settings, relays)"""
    if not snap:
        return
    was = bool(snap.get("armed"))
    for k in NACHT_KEYS:
        if k in snap and k != "armed":
            CFG[k] = snap[k]
    if not was and CFG.get("armed"):
        disarm()
    elif was and not CFG.get("armed"):
        arm(0)
    CFG["nacht_restore"] = {}
    save_settings()


def nacht_start(o=None, auto=False, role="admin", locked=None):
    if not auto and not nacht_may(role, locked):
        return False, "only the owner (not in operator mode)"
    if NACHT["busy"]:
        return False, "a night test run is already running"
    if not _sim_reachable():                            # (147: a slow simulator PC may miss a few frames)
        return False, "only with the simulator"
    if simtask_busy():
        return False, simtask_refuse("night test run") or "already running"
    opts = nacht_opts(o)
    CFG["nacht_opts"] = {k: opts[k] for k in ("scene", "busy", "tempo", "from", "to")}
    save_settings()
    NACHT.update(busy=True, stop=False, step="…", err="", prog="")
    _SIMHUB["t"] = 0.0
    threading.Thread(target=_nacht_thread, args=(opts, auto), daemon=True, name="night-test").start()
    return True, ""


def nacht_stop(role="admin", locked=None):
    if not nacht_may(role, locked):
        return False, "only the owner (not in operator mode)"
    NACHT["stop"] = True
    try:
        sim_control({"action": "nacht", "do": "stop"})
    except Exception:
        pass
    return True, ""


def _nacht_thread(opts, auto):
    snap = {k: CFG.get(k) for k in NACHT_KEYS}
    run, stopped, err = None, False, ""
    L = None
    SANDBOX["force"] += 1                               # nothing reaches the phone as a real alarm, the siren only in the simulator
    try:
        CFG["nacht_restore"] = snap; CFG["relays_on"] = False; save_settings()
        q = {"action": "nacht", "do": "start", "scene": opts["scene"], "busy": opts["busy"], "tempo": opts["tempo"],
             "from": nacht_hm(opts["from"], 20.0), "to": nacht_hm(opts["to"], 7.0), "by": "MoveEye " + APP_VERSION}
        for k in ("speed", "seed"):
            if k in opts:
                q[k] = opts[k]
        r = sim_control(q)
        if not r.get("ok"):
            if r.get("error") == "unknown action":
                raise RuntimeError("the simulator does not know the night test run - update the simulator")
            raise RuntimeError(str(r.get("error") or "the simulator did not start the night test run"))
        ri = r.get("run") or {}
        rid = str(ri.get("id") or int(time.time() * 1000))
        L = {"id": rid, "T0": time.time(), "off": 0.0, "offs": [], "alarms": [], "moments": [], "samples": [], "batt": [], "temp": [],
             "fps": [], "hour": ri.get("from"), "msg0": None, "pushes": [], "inc_seen": False, "run": ri}
        try:
            with MSGLOG["lock"]:
                L["msg0"] = {str(x.get("id")) for x in _msglog_load()}
        except Exception:
            L["msg0"] = set()
        NACHT["live"] = L
        protect_set("full", who="night test run")      # protection «Voll» - in the simulation only
        arm(0)                                          # at once (no countdown): the night starts now
        log_event("sys", "Night test run started (simulation, protection Full; seed %s, %s, %s → %s)" % (ri.get("seed"), opts["tempo"], opts["from"], opts["to"]))
        est = float(ri.get("est_s") or 3600.0)
        t_end = time.time() + est + 600.0
        last_poll, last_res, done = 0.0, 0.0, False
        while time.time() < t_end:
            if NACHT["stop"]:
                stopped = True
                break
            if not CFG.get("sim_on"):
                raise RuntimeError("only with the simulator")
            now = time.time()
            p = STATE.get("present") or []
            ks = set(p) & {"animal", "motion"}
            if int(STATE.get("persons") or 0) > 0:
                ks.add("person")
            if ks:
                L["samples"].append((round(now - L["T0"] - L["off"], 1), sorted(ks)))
            if now - last_res >= max(5.0, est / 240.0):   # battery, Pi temperature, pictures/s - about 240 points a night
                last_res = now
                b = STATE.get("battery") or {}
                h = L.get("hour")
                if b.get("pct") is not None:
                    L["batt"].append([h, round(float(b["pct"]), 1)])
                if STATE.get("cpu_temp") is not None:
                    L["temp"].append([h, round(float(STATE["cpu_temp"]), 1)])
                L["fps"].append([h, round(float(STATE.get("fps") or 0.0), 1)])
            if now - last_poll >= 2.0:
                last_poll = now
                try:
                    st = sim_control({"action": "nacht", "do": "state"})
                except Exception:
                    st = None
                if st and st.get("ok"):
                    if st.get("running") and str(st.get("id")) == rid:
                        L["offs"].append((time.time() - L["T0"]) - float(st.get("t") or 0.0))
                        L["offs"] = L["offs"][-30:]
                        L["off"] = sorted(L["offs"])[len(L["offs"]) // 2]
                        L["hour"] = st.get("hour")
                        NACHT["prog"] = "%s · %d/%d · %d min" % (nacht_clock(st.get("hour")), int(st.get("n_done") or 0), int(st.get("n_plan") or 0),
                                                              int(round(float(st.get("left_s") or 0) / 60.0)))
                        NACHT["step"] = NACHT["prog"]
                        for a in st.get("active") or []:
                            if a.get("cat") == "incident" and a.get("vis") and not L["inc_seen"]:
                                L["inc_seen"] = True
                                _nacht_moment("Incident visible", "incident")
                    elif str(st.get("done_id") or "") == rid:
                        done = True
                        break
                    elif not st.get("running"):
                        done = True                     # stopped in the simulator window
                        break
            time.sleep(0.5)
        if not done and not stopped:
            err = "no result from the simulator"
        try:
            sim_control({"action": "nacht", "do": "stop"}) if not done else None
        except Exception:
            pass
        time.sleep(1.0)
        tr_ = {}
        for _ in range(5):
            try:
                tr_ = sim_control({"action": "nacht", "do": "truth", "id": rid}) or {}
            except Exception:
                tr_ = {}
            if tr_.get("ok") and str((tr_.get("run") or {}).get("id")) == rid:
                break
            time.sleep(1.0)
        sr = tr_.get("run") or {}
        truth = sr.get("truth") or []
        stopped = stopped or bool(sr.get("stopped"))
        dets = nacht_segments(L["samples"])
        try:
            with MSGLOG["lock"]:
                items = list(_msglog_load())
            L["pushes"] = [{"t": round(float(x.get("t", 0)) - L["T0"] - L["off"], 1), "ev": x.get("ev"), "status": x.get("status")}
                           for x in items if str(x.get("id")) not in L["msg0"] and float(x.get("t", 0)) >= L["T0"]]
        except Exception:
            pass
        # sabotage alarms do not go through Notifier.person / prealarm: from the message list
        sp_, h0_ = float(ri.get("speed") or 8.0), float(ri.get("from") or 0.0)
        L["alarms"].extend({"t": p_["t"], "ev": "tamper", "h": round((h0_ + p_["t"] * sp_ / 3600.0) % 24.0, 3)} for p_ in L["pushes"] if p_.get("ev") == "tamper")
        res = nacht_match(truth, L["alarms"], dets)
        meta = sr.get("meta") or {}
        run = {"id": rid, "t": time.strftime("%Y-%m-%d %H:%M"), "mw_version": APP_VERSION, "sim_version": meta.get("sim_version") or "",
               "opts": dict(opts, scene=meta.get("scene") or ri.get("scene") or opts.get("scene")), "seed": meta.get("seed", ri.get("seed")),
               "speed": meta.get("speed", ri.get("speed")), "real_min": round((time.time() - L["T0"]) / 60.0, 1), "auto": bool(auto),
               "stopped": stopped, "err": err, "result": res, "truth": truth, "alarms": L["alarms"], "pushes": L["pushes"], "dets": dets[:400],
               "batt": L["batt"], "temp": L["temp"], "fps": L["fps"], "moments": L["moments"],
               "quiet": bool(CFG.get("quiet_on")), "ai": str(STATE.get("ai_status") or "")}
        if stopped and not truth:
            run = None                                      # stopped before anything happened: nothing to keep
    except Exception as e:
        err = str(e)[:160]
        log_event("sys", "Night test run: " + err)
    finally:
        NACHT["live"] = None
        SANDBOX["force"] = max(0, SANDBOX["force"] - 1)
        try:
            _nacht_restore(snap)
        except Exception as e:
            log_event("sys", "Night test run: restore " + str(e)[:100])
        NACHT.update(busy=False, step="", prog="", err=err)
        _SIMHUB["t"] = 0.0
    if run is not None:
        nacht_runs().append(run)
        _nacht_save()
        log_event("sys", "Night test run finished: " + nacht_push_text(run, "en"))
        if not stopped:
            nacht_push(run)


def nacht_push_text(run, lang=None):
    res = run.get("result") or {}
    I = res.get("incident") or {}
    inc = (trf("detected after {s} s", lang, s=I.get("ttd_s")) if I.get("detected") else tr("NOT detected", lang)) if I else "–"
    by = ", ".join("%s %d" % (tr(NACHT_CAUSES.get(k, k), lang), n) for k, n in sorted((res.get("false_by") or {}).items(), key=lambda x: -x[1]))
    return "🧪 " + trf("Incident: {inc} · false alarms: {fa}{by} · misses: {mi}", lang, inc=inc, fa=res.get("false", 0),
                       by=(" (" + by + ")") if by else "", mi=len(res.get("misses") or []))


def nacht_push(run):
    """the morning report: an info message (marked simulation), with the link to the report page"""
    w = WATCH_REF.get("w")
    if w is None:
        return
    pub = (CFG.get("public_url") or "").strip().rstrip("/")
    try:
        w.notifier.info(nacht_push_text(run), pub + "/nacht?id=" + str(run["id"]) if pub else "", title="{name}: 🧪 " + tr("Night test run (simulation)"))
    except Exception as e:
        log_event("sys", "Night test run: push " + str(e)[:100])


def nacht_auto_loop():
    """the schedule: once a night at nacht_auto_hour (real clock), when the simulator is there and free"""
    while True:
        time.sleep(60)
        try:
            if not CFG.get("nacht_auto_on") or NACHT["busy"] or CFG.get("lock_on"):
                continue
            now = datetime.now(); day = now.strftime("%Y-%m-%d")
            if now.hour != int(CFG.get("nacht_auto_hour", 23)) or CFG.get("nacht_auto_day") == day:
                continue
            if not _sim_reachable() or simtask_busy():
                continue
            CFG["nacht_auto_day"] = day; save_settings()
            nacht_start(None, auto=True)
        except Exception as e:
            log_event("sys", "Night test run (schedule): " + str(e)[:150])


def _nacht_boot():
    """a run was cut by a restart of MoveEye: put the protection back as it was"""
    time.sleep(20)
    if CFG.get("nacht_restore") and not NACHT["busy"]:
        log_event("sys", "Night test run was interrupted (restart) - protection put back as before")
        _nacht_restore(CFG.get("nacht_restore"))


threading.Thread(target=nacht_auto_loop, daemon=True, name="night-test-auto").start()
threading.Thread(target=_nacht_boot, daemon=True, name="night-test-boot").start()


# ---- one lock (147) ----------------------------------------------------------------------------------------------------
_simtask_busy_nacht_base = simtask_busy


def simtask_busy(except_=""):                              # + 579b: one lock
    if NACHT["busy"] and except_ != "night test run":
        return "night test run"
    return _simtask_busy_nacht_base(except_)


_simtask_local_nacht_base = simtask_local


def simtask_local():                                       # + 579b: the simulator refuses its own starts meanwhile
    return "night test run" if NACHT["busy"] else _simtask_local_nacht_base()


SIM_BUSY_NAMES.setdefault("Nacht-Testlauf", "night test run")


# ---- the page data -----------------------------------------------------------------------------------------------------
def nacht_state(role="admin", rid=None):
    runs = nacht_runs()
    sel = nacht_run_by(rid) if rid else (runs[-1] if runs else None)
    o = nacht_opts()
    return {"ok": True, "owner": nacht_may(role), "locked": bool(CFG.get("lock_on")), "busy": NACHT["busy"], "step": NACHT["step"],
            "err": NACHT["err"], "sim": bool(_sim_reachable()), "opts": o, "busy_opts": list(NACHT_BUSY), "tempo_opts": list(NACHT_TEMPO),
            "auto": {"on": bool(CFG.get("nacht_auto_on")), "hour": int(CFG.get("nacht_auto_hour", 23))},
            "runs": [nacht_summary(r) for r in runs][::-1], "run": sel, "causes": NACHT_CAUSES, "targets": NACHT_TARGETS,
            "live": {"alarms": len((NACHT.get("live") or {}).get("alarms") or []), "hour": (NACHT.get("live") or {}).get("hour")} if NACHT.get("live") else None}


def nacht_api(d, role="admin", locked=None):
    """POST /api/nacht -> (reply, http code): start / stop / auto (schedule) - only the owner"""
    op = str(d.get("do") or "")
    if op not in ("start", "stop", "auto"):
        return {"ok": False, "error": "unknown action"}, 400
    if not nacht_may(role, locked):
        return {"ok": False, "error": "only the owner (not in operator mode)"}, 403
    if op == "start":
        ok, err = nacht_start(d, role=role, locked=locked)
    elif op == "stop":
        ok, err = nacht_stop(role, locked)
    else:
        if "on" in d:
            CFG["nacht_auto_on"] = bool(d.get("on"))
        if d.get("hour") is not None:
            try:
                CFG["nacht_auto_hour"] = max(0, min(23, int(d["hour"])))
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid value"}, 400
        save_settings(); ok, err = True, ""
    return {"ok": ok, "error": err}, 200 if ok else 409


_ginv_routes_nacht_base = ginv_routes


def ginv_routes(app, reply, body):                         # + 579b: /nacht, /api/nacht (550 calls ginv_routes)
    _ginv_routes_nacht_base(app, reply, body)
    from flask import request, Response, send_file

    @app.route("/api/nacht", methods=["GET", "POST"])
    def api_nacht():
        role = _nacht_role()
        if request.method == "POST":
            d = body()
            rep, code = nacht_api(d, role)
            if rep.get("error"):
                rep["error"] = tr_err(rep["error"], norm_lang(d.get("lang")))
            rep["state"] = nacht_state(role)
            _SIMHUB["t"] = 0.0
            return reply(rep, code)
        return reply(nacht_state(role, request.args.get("id")))

    @app.route("/api/nacht/img/<rid>/<name>")
    def api_nacht_img(rid, name):
        if not re.fullmatch(r"\d{1,16}", rid) or not re.fullmatch(r"m\d{2}\.jpg", name):
            return Response("no", 404)
        p = os.path.join(_nacht_pic_dir(rid), name)
        if not os.path.isfile(p):
            return Response("no", 404)
        return send_file(p, mimetype="image/jpeg", max_age=3600)

    @app.route("/api/nacht/export/<rid>")
    def api_nacht_export(rid):
        r = nacht_run_by(rid)
        if r is None:
            return Response("no", 404)
        return Response(json.dumps(dict(r, app="MoveEye", kind="night test run (simulation)"), ensure_ascii=False, indent=1),
                        mimetype="application/json", headers={"Content-Disposition": 'attachment; filename="nacht_testlauf_%s.json"' % re.sub(r"\D", "", rid)})

    @app.route("/nacht")
    def nacht_page_route():
        return Response(nacht_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})


# ---- tile 🌙 (Simulator centre, group «Testen») and the page /nacht -------------------------------------------------------
_sim_hub_nacht_base = sim_hub


def sim_hub(force=False):                                  # + 579b: the tile 🌙 «Nacht-Testlauf» (not per user: no owner flag here)
    d = _sim_hub_nacht_base(force)
    if d.get("ok"):
        runs = nacht_runs()
        s = nacht_summary(runs[-1]) if runs else None
        d = dict(d, nacht={"busy": NACHT["busy"], "prog": NACHT["prog"], "last": {"inc": s["inc"], "fa": s["fa"], "ttd": s["ttd"]} if s else None})
    return d


NACHT_JS = r"""
<style>
.mwnt{flex:1 1 100%;display:flex;flex-direction:column;gap:8px;min-width:0;max-width:100%;box-sizing:border-box}
.mwnt *{box-sizing:border-box;max-width:100%}
.mwnt .row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.mwnt .row>button{flex:1 1 auto;min-width:0}
.mwnt select,.mwnt input{min-width:0;flex:1 1 90px}
.mwnt label{display:flex;flex-direction:column;gap:2px;font-size:12px;color:var(--mut,#8a9bb0);flex:1 1 120px;min-width:0}
.mwnt .box{border:1px solid var(--line,#1f2b3a);border-radius:10px;padding:8px}
.mwnt h4{margin:0 0 4px;font-size:13px}
.mwnt .big{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}
.mwnt .big div{background:var(--panel2,#151e2b);border:1px solid var(--line,#1f2b3a);border-radius:12px;padding:8px 10px;font-size:12px;color:var(--mut,#8a9bb0)}
.mwnt .big b{display:block;font-size:20px;color:var(--txt,#e8eef5)}
.mwnt .g{color:#3fcf6b!important}.mwnt .r{color:#ff4d4d!important}.mwnt .o{color:#f59a4a!important}
.mwnt table{width:100%;border-collapse:collapse;font-size:12px}
.mwnt td,.mwnt th{padding:3px 4px;border-bottom:1px solid var(--line,#1f2b3a);text-align:left;vertical-align:top;overflow-wrap:anywhere}
.mwnt th{color:var(--mut,#8a9bb0);font-weight:600}
.mwnt tr.sel td{background:rgba(59,140,255,.12)}
.mwnt svg{width:100%;height:56px;background:var(--panel2,#0c121a);border-radius:6px}
.mwnt .pics{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px}
.mwnt .pics figure{margin:0;font-size:11px;color:var(--mut,#8a9bb0)}
.mwnt .pics img{width:100%;border-radius:8px;display:block;background:#000;aspect-ratio:16/9;object-fit:cover}
.mwnt .lock{padding:8px 10px;border-radius:10px;background:rgba(245,154,74,.12);font-size:13px}
</style>
<script>
(function () {
  const DE = /*NDE*/{};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  let merged = false;
  const merge = () => { if (merged) return; try { if (typeof I18N !== "undefined" && I18N.de) { for (const k in DE) if (!(k in I18N.de)) I18N.de[k] = DE[k]; merged = true; } } catch (e) {} };
  const tt = k => { merge(); try { if (typeof t === "function" && t(k) !== k) return t(k); } catch (e) {} return L() === "en" ? k : (DE[k] || k); };
  const tf = (k, o) => tt(k).replace(/\{(\w+)\}/g, (m, x) => (o && o[x] != null) ? o[x] : m);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const B = (txt, fn, cls) => { const b = E("button", cls == null ? "sec" : cls, txt); b.type = "button"; b.onclick = fn; return b; };
  const clk = h => h == null ? "–" : String(Math.floor(h % 24)).padStart(2, "0") + ":" + String(Math.round(h % 1 * 60) % 60).padStart(2, "0");
  const say = m => { if (typeof toast === "function") toast(m); };
  let D = null, DT = 0, O = null, SEL = null;
  const repaint = () => { if (window.mwSimHub) window.mwSimHub.paint(); if (window._ntPage) window._ntPage(); };
  async function load(id) { try { D = await (await fetch("/api/nacht" + (id ? "?id=" + encodeURIComponent(id) : ""))).json(); DT = Date.now(); } catch (e) {} return D; }
  async function post(d) { try { const r = await (await fetch("/api/nacht", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})).json();
      if (r.state) { D = r.state; DT = Date.now(); } if (!r.ok) say("⚠ " + (r.error || "")); repaint(); return r; } catch (e) { say("⚠ " + tt("Simulator not reachable")); } }
  const cause = k => tt((D && D.causes && D.causes[k]) || k);
  const EVN = {person: "Person alarm", warm: "Warmth alarm", prealarm: "Pre-alarm", noise: "Noise alarm", tamper: "Sabotage alarm", incident: "Incident visible"};
  const evn = k => tt(EVN[k] || k);
  const BN = {ruhig: "calm", normal: "normal (some going on)", viel: "lots going on"};
  function curve(pts, lo, hi, col, unit) {                // one small line chart over the night (x = order of the points)
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", "0 0 100 30"); s.setAttribute("preserveAspectRatio", "none");
    const P = (pts || []).filter(p => p && p[1] != null); if (P.length < 2) { const w = E("div", "mut", "–"); return w; }
    const vs = P.map(p => p[1]); lo = lo == null ? Math.min(...vs) - 1 : lo; hi = hi == null ? Math.max(...vs) + 1 : hi;
    const pl = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    pl.setAttribute("points", P.map((p, i) => (i / (P.length - 1) * 100).toFixed(2) + "," + (30 - (p[1] - lo) / Math.max(0.01, hi - lo) * 28 - 1).toFixed(2)).join(" "));
    pl.setAttribute("fill", "none"); pl.setAttribute("stroke", col); pl.setAttribute("stroke-width", "1.5"); pl.setAttribute("vector-effect", "non-scaling-stroke"); s.appendChild(pl);
    const w = E("div"); w.appendChild(s);
    w.appendChild(E("div", "mut", clk(P[0][0]) + " " + P[0][1] + unit + " → " + clk(P[P.length - 1][0]) + " " + P[P.length - 1][1] + unit + " · min " + Math.min(...vs) + unit + " · max " + Math.max(...vs) + unit));
    return w;
  }
  function report(w, R, full) {
    if (!R) { w.appendChild(E("div", "mut", tt("No night test run yet."))); return; }
    const res = R.result || {}, I = res.incident || {}, o = R.opts || {};
    w.appendChild(E("div", "mut", "🧪 " + R.t + " · MoveEye " + R.mw_version + " · " + tt("Simulator") + " " + (R.sim_version || "–") + " · " + (o.scene || "") + " · " + tt(BN[o.busy] || o.busy || "") + " · "
      + (o.tempo === "echt" ? "1×" : "8×") + " · " + o.from + "–" + o.to + " · seed " + R.seed + (R.stopped ? " · ⏹ " + tt("stopped") : "") + (R.auto ? " · ⏰" : "")));
    const big = E("div", "big");
    const tile = (lbl, val, cls) => { const d = E("div", "", lbl); d.appendChild(E("b", cls || "", val)); big.appendChild(d); };
    tile(tt("Incident detected"), I.id ? (I.detected ? "✅ " + tf("after {s} s", {s: I.ttd_s}) : "❌ " + tt("not detected")) : "–", I.detected ? "g" : "r");
    tile(tt("False alarms"), String(res.false || 0), (res.false || 0) ? "o" : "g");
    tile(tt("Misses"), String((res.misses || []).length), (res.misses || []).length ? "o" : "g");
    tile(tt("Alarms in all"), String(res.alarms || 0) + (res.repeats ? " (" + res.repeats + " " + tt("repeats") + ")" : ""));
    w.appendChild(big);
    if (I.id) { const b = E("div", "box"); b.appendChild(E("h4", "", "🥷 " + tt((D && D.targets && D.targets[I.target]) || "Incident") + " · " + clk(I.h0)));
      b.appendChild(E("div", "mut", (I.first_vis != null && I.first_vis >= 0 ? tf("visible for the camera after {s} s", {s: Math.round(I.first_vis - I.t0)}) + " · " + tf("{s} s visible", {s: I.vis_s}) : tt("never visible for the camera"))
        + " · " + (I.det_s != null ? tf("first detection after {s} s", {s: I.det_s}) : tt("no detection")) + " · " + (I.detected ? tf("first alarm after {s} s", {s: I.ttd_s}) : tt("no alarm"))));
      w.appendChild(b); }
    const fb = E("div", "box"); fb.appendChild(E("h4", "", "⚠ " + tt("False alarms by cause")));
    const by = Object.entries(res.false_by || {}).sort((a, b) => b[1] - a[1]);
    if (!by.length) fb.appendChild(E("div", "g", "✓ " + tt("none – fine")));
    by.forEach(([k, n]) => fb.appendChild(E("div", "", n + " × " + cause(k))));
    if (full) (res.false_list || []).slice(0, 30).forEach(f => fb.appendChild(E("div", "mut", clk(f.h) + " · " + evn(f.ev) + " · " + cause(f.cause))));
    w.appendChild(fb);
    const mb = E("div", "box"); mb.appendChild(E("h4", "", "👁 " + tt("Misses (visible, nothing detected)")));
    if (!(res.misses || []).length) mb.appendChild(E("div", "g", "✓ " + tt("none – fine")));
    (res.misses || []).slice(0, full ? 40 : 6).forEach(m => mb.appendChild(E("div", m.incident ? "r" : "", clk(m.h0) + " · " + cause(m.cause) + " · " + tf("{s} s visible", {s: m.vis_s}))));
    w.appendChild(mb);
    if (!full) return;
    const cb = E("div", "box"); cb.appendChild(E("h4", "", "🔋 " + tt("Battery"))); cb.appendChild(curve(R.batt, 0, 100, "#3fcf6b", " %"));
    cb.appendChild(E("h4", "", "🌡 " + tt("Pi temperature"))); cb.appendChild(curve(R.temp, null, null, "#f59a4a", " °C"));
    cb.appendChild(E("h4", "", "🎞 " + tt("Pictures per second"))); cb.appendChild(curve(R.fps, 0, null, "#3b8cff", "")); w.appendChild(cb);
    const pb = E("div", "box"); pb.appendChild(E("h4", "", "📷 " + tt("Key moments"))); const pics = E("div", "pics");
    (R.moments || []).forEach(m => { const f = E("figure"); if (m.img) { const im = E("img"); im.loading = "lazy"; im.alt = ""; im.src = "/api/nacht/img/" + R.id + "/" + m.img; f.appendChild(im); }
      f.appendChild(E("figcaption", "", clk(m.h) + " · " + evn(m.label))); pics.appendChild(f); });
    if (!(R.moments || []).length) pics.appendChild(E("div", "mut", "–")); pb.appendChild(pics); w.appendChild(pb);
    const ev = E("div", "box"); ev.appendChild(E("h4", "", "📋 " + tt("The night (truth of the simulator)")));
    const tb = E("table"), h = E("tr"); [tt("Time"), tt("Event"), tt("visible (s)"), tt("Alarms")].forEach(x => h.appendChild(E("th", "", x))); tb.appendChild(h);
    const al = (res.false_list || []).concat((res.hits || []).map(x => Object.assign({cause: "incident"}, x)));
    (R.truth || []).forEach(e => { const tr = E("tr"); const n = al.filter(a => a.id === e.id).length;
      tr.append(E("td", "", clk(e.h0) + (e.h1 >= 0 ? "–" + clk(e.h1) : "")), E("td", e.cat === "incident" ? "r" : "", cause(e.cause)), E("td", "", e.cat === "weather" ? "" : (e.vis_s ? String(e.vis_s) : "–")), E("td", n ? (e.cat === "incident" ? "g" : "o") : "", n ? String(n) : ""));
      tb.appendChild(tr); }); ev.appendChild(tb); w.appendChild(ev);
    const ex = E("div", "row"); const a = E("a", "btn sec", "⬇ " + tt("Export (JSON)")); a.href = "/api/nacht/export/" + R.id; a.setAttribute("download", ""); ex.appendChild(a); w.appendChild(ex);
  }
  function compare(w, cur) {
    const runs = (D && D.runs) || []; if (!runs.length) return;
    const b = E("div", "box"); b.appendChild(E("h4", "", "📊 " + tt("Comparison: last 10 runs")));
    const tb = E("table"), h = E("tr"); [tt("Date"), "MoveEye", tt("Incident"), tt("False alarms"), tt("Misses"), ""].forEach(x => h.appendChild(E("th", "", x))); tb.appendChild(h);
    runs.forEach(r => { const tr = E("tr", cur && cur.id === r.id ? "sel" : ""); tr.style.cursor = "pointer";
      tr.append(E("td", "", (r.t || "").slice(5)), E("td", "", r.mw || ""), E("td", r.inc ? "g" : "r", r.inc ? "✅ " + r.ttd + " s" : "❌"), E("td", r.fa ? "o" : "g", String(r.fa)), E("td", "", String(r.miss)),
        E("td", "mut", (r.tempo === "echt" ? "1×" : "8×") + " · " + tt(BN[r.busy] || r.busy || "") + (r.stopped ? " · ⏹" : "") + (r.auto ? " · ⏰" : "")));
      tr.onclick = () => { if (window._ntPage) { SEL = r.id; load(r.id).then(repaint); } else location.href = "/nacht?id=" + r.id; }; tb.appendChild(tr); });
    b.appendChild(tb); w.appendChild(b);
  }
  function controls(w) {
    if (!D.owner) { w.appendChild(E("div", "lock", "🔒 " + tt(D.locked ? "Operator mode: only the owner can start or stop the night test run – the reports can be viewed." : "Only the owner can start or stop the night test run – the reports can be viewed."))); return; }
    if (!O) O = Object.assign({}, D.opts);
    const sc = (window.mwSimHub && window.mwSimHub.H() && window.mwSimHub.H().scenes) || [];
    const lab = (n, el) => { const l = E("label", "", n); l.appendChild(el); return l; };
    const sel = (opts, key) => { const s = E("select"); opts.forEach(([v, n]) => { const o = E("option", "", n); o.value = v; if (String(O[key]) === String(v)) o.selected = true; s.appendChild(o); }); s.onchange = () => O[key] = s.value; return s; };
    const inp = key => { const i = E("input"); i.type = "time"; i.value = O[key]; i.onchange = () => O[key] = i.value; return i; };
    const r1 = E("div", "row");
    r1.append(lab(tt("Scene"), sel([["", tt("as now")]].concat(sc.map(x => [x.id, window.mwSimHub.scn(x)])), "scene")),
      lab(tt("Liveliness"), sel([["ruhig", tt("calm")], ["normal", tt("normal (some going on)")], ["viel", tt("lots going on")]], "busy")),
      lab(tt("Tempo"), sel([["echt", tt("real (1×)")], ["schnell", tt("fast (8 h in about 1 h)")]], "tempo")),
      lab(tt("Start time"), inp("from")), lab(tt("End time"), inp("to")));
    w.appendChild(r1);
    const r2 = E("div", "row");
    if (D.busy) r2.append(B("⏹ " + tt("Abort the night test run"), () => post({do: "stop"}), ""), E("span", "mut", "⏳ " + (D.step || "")));
    else r2.appendChild(B("🌙 " + tt("Start night test run"), () => post(Object.assign({do: "start"}, O)), ""));
    w.appendChild(r2);
    const A = D.auto || {}, r3 = E("div", "row"), hs = E("select");
    for (let i = 0; i < 24; i++) { const o = E("option", "", String(i).padStart(2, "0") + ":00"); o.value = i; if (i === A.hour) o.selected = true; hs.appendChild(o); }
    hs.onchange = () => post({do: "auto", hour: +hs.value});
    r3.append(B((A.on ? "✓ " : "") + tt("Every night by itself"), () => post({do: "auto", on: !A.on}), A.on ? "" : "sec"), hs);
    w.appendChild(r3);
    w.appendChild(E("div", "mut", tt("nacht-note")));
  }
  merge();
  window.mwNacht = {
    name: () => tt("Night test run"),
    sub: H => { const N = H && H.nacht; if (!N) return ""; if (N.busy) return "⏳ " + (N.prog || ""); if (N.last) return (N.last.inc ? "✅ " : "❌ ") + tt("false alarms") + " " + N.last.fa;
      return tt("whole night with truth"); },
    sheet: (s, H) => { const w = E("div", "mwnt"); s.appendChild(w);
      if (!D || Date.now() - DT > 5000) { load().then(() => { if (window.mwSimHub) window.mwSimHub.paint(); }); if (!D) { w.appendChild(E("div", "mut", "…")); return; } }
      if (D.err) w.appendChild(E("div", "r", "⚠ " + tt(D.err)));
      controls(w); report(w, D.run, false);
      if (D.run) { const a = E("a", "btn sec", "📄 " + tt("Open the report")); a.href = "/nacht?id=" + D.run.id; w.appendChild(a); } },
    page: el => { window._ntPage = () => { el.textContent = ""; const w = E("div", "mwnt"); el.appendChild(w); if (!D) { w.appendChild(E("div", "mut", "…")); return; }
        if (D.busy) w.appendChild(E("div", "o", "⏳ " + tt("Night test run is running") + " · " + (D.step || "")));
        report(w, D.run, true); compare(w, D.run); };
      const id = new URLSearchParams(location.search).get("id"); load(id).then(() => window._ntPage()); setInterval(() => { if (D && D.busy) load(SEL || id).then(() => window._ntPage()); }, 10000); }
  };
})();
</script>
"""
NACHT_KEYS_TXT = ("Night test run", "Night test run (simulation)", "whole night with truth", "Start night test run", "Abort the night test run",
                  "Scene", "as now", "Liveliness", "calm", "normal (some going on)", "lots going on", "Tempo", "real (1×)", "fast (8 h in about 1 h)",
                  "Start time", "End time", "Every night by itself", "nacht-note", "Open the report", "No night test run yet.", "Incident detected",
                  "after {s} s", "not detected", "False alarms", "false alarms", "Misses", "Alarms in all", "repeats", "Incident",
                  "visible for the camera after {s} s", "{s} s visible", "never visible for the camera", "first detection after {s} s", "no detection",
                  "first alarm after {s} s", "no alarm", "False alarms by cause", "none – fine", "Misses (visible, nothing detected)", "Battery",
                  "Pi temperature", "Pictures per second", "Key moments", "The night (truth of the simulator)", "Time", "Event", "visible (s)", "Alarms",
                  "Export (JSON)", "Comparison: last 10 runs", "Date", "stopped", "Night test run is running", "Simulator", "Incident visible",
                  "Person alarm", "Warmth alarm", "Pre-alarm", "Noise alarm", "Sabotage alarm", "Simulator not reachable",
                  "Operator mode: only the owner can start or stop the night test run – the reports can be viewed.",
                  "Only the owner can start or stop the night test run – the reports can be viewed.",
                  "only the owner (not in operator mode)", "a night test run is already running", "only with the simulator",
                  "the simulator does not know the night test run - update the simulator", "no result from the simulator",
                  "the simulator did not start the night test run", "night test run", "Night test run: report") + tuple(NACHT_CAUSES.values()) + tuple(NACHT_TARGETS.values())


def nacht_js():
    return NACHT_JS.replace("/*NDE*/{}", json.dumps({k: DE[k] for k in NACHT_KEYS_TXT if k in DE}, ensure_ascii=False), 1)


_simhub_head_nacht_base = simhub_head


def simhub_head():                                        # + 579b: the tile 🌙 «Nacht-Testlauf»
    return _simhub_head_nacht_base() + nacht_js()


NACHT_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Night test run</title>
<style>
/*BASECSS*/
main{padding:14px 16px 90px;max-width:980px;margin:0 auto}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <h2 style="margin:0 0 8px">🌙 <span data-i18n="Night test run: report">Night test run: report</span></h2>
  <div class="mut" style="margin:0 0 10px">🧪 <span data-i18n="SIMULATION – alarms are not real">SIMULATION – alarms are not real</span> · <a href="/sim" data-i18n="Simulator centre">Simulator centre</a></div>
  <div id="nt-page"></div>
</main>
<script>
/*COMMON*/
</script>
<!--NTJS-->
<script>(async () => { try { await initAppearance(); } catch (e) {} window.mwNacht.page(document.getElementById("nt-page")); })();</script>
</body></html>"""
NAV_OF["nacht"] = "sim"


def nacht_page():
    js = "<script>Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in ("Night test run: report", "Simulator centre", "SIMULATION – alarms are not real")},
                                                        ensure_ascii=False) + ");</script>"
    return render_page(NACHT_PAGE, "nacht").replace("<!--NTJS-->", js + nacht_js(), 1)


# ---- self-test: the matching, the owner lock, the options -----------------------------------------------------------
def nacht_selftest():
    truth = [{"id": 1, "kind": "wc", "cat": "people", "cause": "wc_torch", "t0": 10.0, "t1": 60.0, "first_vis": 12.0, "vis_s": 8.0},
             {"id": 2, "kind": "fox", "cat": "animal", "cause": "fox", "t0": 100.0, "t1": 120.0, "first_vis": 104.0, "vis_s": 6.0},
             {"id": 3, "kind": "rain", "cat": "weather", "cause": "rain", "t0": 90.0, "t1": 300.0, "first_vis": -1, "vis_s": 0},
             {"id": 4, "kind": "incident", "cat": "incident", "cause": "incident", "target": "bike", "t0": 200.0, "t1": 260.0, "first_vis": 210.0, "vis_s": 20.0},
             {"id": 5, "kind": "cat", "cat": "animal", "cause": "cat", "t0": 400.0, "t1": 420.0, "first_vis": 405.0, "vis_s": 5.0}]
    alarms = [{"t": 20.0, "ev": "person"}, {"t": 24.0, "ev": "person"},          # toilet trip + a repeat within 10 s
              {"t": 110.0, "ev": "prealarm"},                                     # fox during the rain: the fox (animal > weather)
              {"t": 150.0, "ev": "person"},                                       # only the rain runs: rain
              {"t": 214.5, "ev": "person"}, {"t": 218.0, "ev": "person"},         # the incident (and a repeat - still the incident)
              {"t": 500.0, "ev": "noise"}, {"t": 600.0, "ev": "info"}]            # nothing in the plan: unknown; info is no alarm
    dets = nacht_segments([(12.5, ["person"]), (13.0, ["person"]), (212.0, ["person"]), (212.5, ["person"]), (106.0, ["animal"])])
    r = nacht_match(truth, alarms, dets)
    I = r["incident"]
    assert I["detected"] and I["ttd_s"] == 4.5 and I["det_s"] == 2.0 and I["alarms"] == 2, I
    assert r["false"] == 4 and r["repeats"] == 1, r
    assert r["false_by"] == {"wc_torch": 1, "fox": 1, "rain": 1, "unknown": 1}, r["false_by"]
    assert [m["kind"] for m in r["misses"]] == ["cat"], r["misses"]          # the cat was visible, nothing detected
    r2 = nacht_match(truth, [{"t": 20.0, "ev": "person"}], [])
    assert r2["missed_incident"] and not r2["incident"]["detected"] and r2["incident"]["ttd_s"] is None
    assert any(m["incident"] for m in r2["misses"])
    r3 = nacht_match(truth, [{"t": 199.0, "ev": "person"}, {"t": 268.0, "ev": "person"}, {"t": 285.0, "ev": "person"}], [])
    assert r3["incident"]["detected"] and r3["incident"]["ttd_s"] == 0.0 and r3["false"] == 1 and r3["false_by"] == {"rain": 1}, r3
    # two events at the same time: the alarm belongs to the one the camera saw (vis_iv), not simply to the incident
    tv = [dict(truth[0], t0=150.0, t1=300.0, vis_iv=[[160.0, 175.0]]), dict(truth[3], t0=100.0, t1=300.0, vis_iv=[])]
    r4 = nacht_match(tv, [{"t": 170.0, "ev": "person"}], [])
    assert r4["false_by"] == {"wc_torch": 1} and not r4["incident"]["detected"], r4
    r5 = nacht_match(tv, [{"t": 250.0, "ev": "person"}], [])
    assert r5["incident"]["detected"], r5                  # nobody seen at 250: the most important running event
    r6 = nacht_match(tv, [{"t": 250.0, "ev": "tamper"}], [])
    assert not r6["incident"]["detected"] and r6["false_by"] == {"wc_torch": 1}, r6   # sabotage: not the incident
    # segments: a gap of more than 1.5 s splits
    sg = nacht_segments([(1.0, ["person"]), (1.5, ["person", "animal"]), (5.0, ["person"])])
    assert [(x["k"], x["t0"], x["t1"]) for x in sg] == [("person", 1.0, 1.5), ("animal", 1.5, 1.5), ("person", 5.0, 5.0)], sg
    # only the owner, never in operator mode
    assert nacht_may("admin", False) and not nacht_may("admin", True) and not nacht_may("family", False) and not nacht_may("kid", False)
    rep, code = nacht_api({"do": "start"}, "admin", True)
    assert code == 403 and not rep["ok"], rep
    rep, code = nacht_api({"do": "auto", "on": True}, "friend", False)
    assert code == 403, rep
    rep, code = nacht_api({"do": "stop"}, "admin", True)
    assert code == 403, rep
    keep = (CFG.get("nacht_auto_on"), CFG.get("nacht_auto_hour"), CFG.get("lock_on"))
    try:
        CFG["lock_on"] = True
        assert not nacht_state("admin")["owner"] and nacht_state("admin")["locked"]
        CFG["lock_on"] = False
        assert nacht_state("admin")["owner"] and not nacht_state("family")["owner"]
        rep, code = nacht_api({"do": "auto", "hour": 2}, "admin", False)
        assert code == 200 and CFG["nacht_auto_hour"] == 2
    finally:
        CFG["nacht_auto_on"], CFG["nacht_auto_hour"], CFG["lock_on"] = keep
    o = nacht_opts({"from": "23:30", "to": "6", "busy": "x", "tempo": "echt", "scene": "camping;rm"})
    assert o["from"] == "23:30" and o["to"] == "06:00" and o["busy"] == "normal" and o["tempo"] == "echt" and o["scene"] == "campingrm", o
    assert nacht_hm("25:00", 7.0) == 7.0 and nacht_clock(7.5) == "07:30"
    assert "mwNacht" in simhub_head() and "nt-page" in nacht_page()
    assert "🧪" in nacht_push_text({"result": r}, "en") and "4.5" in nacht_push_text({"result": r}, "en")


SELFTEST_EXTRA.append(("Night test run: matching, owner only, options (579b)", nacht_selftest))
