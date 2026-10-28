#@ Motion Watch – Teil 310: Testläufe mit Auswertung und Optimierung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- test runs with evaluation and optimization (2.95.22) ----------------------------------------------------------
# The 3D simulator (from 3D-3.27) plays a fixed test (the same visitors on the same ways every time) and knows the truth.
# MoveEye starts it, fetches the report, judges it (score) and proposes changes of its own settings. They can be
# taken over one by one or all at once (with «undo»), and the automatic optimization tries them out one after the
# other: a change stays only if the next test run is really better.
OPT_KEYS = ["sensitivity", "min_area", "ai_conf", "ai_every", "ai_require", "wind_auto", "wind_threshold", "wind_boost_max",
            "rain_auto", "rain_threshold", "lowlight_auto", "lowlight_threshold", "walk_frames", "speed_consistency",
            "shadow_filter", "car_filter", "object_conf", "auto_tune"]
TESTOPT = {"busy": "", "msg": "", "plan": "standard", "sim": {}, "runs": [], "undo": None, "sugg": [], "auto": None, "stop": False}
_TESTOPT_LOCK = threading.Lock()


def _clean_report(rep):
    """2.95.33: the simulator is network input - numbers checked, nothing that could break the scoring"""
    if not isinstance(rep, dict):
        return {}
    def n(x, hi=1000000):
        try:
            v = float(x)
        except (TypeError, ValueError):
            return 0
        return int(max(0, min(hi, v))) if math.isfinite(v) else 0
    out = dict(rep); ph = []
    for p in (rep.get("phases") if isinstance(rep.get("phases"), list) else [])[:60]:
        if not isinstance(p, dict):
            continue
        q = dict(p)
        for k in ("persons", "persons_detected", "false_alarms", "animals_as_person"):
            q[k] = n(p.get(k, 0))
        q["persons_detected"] = min(q["persons_detected"], q["persons"])
        q["name"] = str(p.get("name", ""))[:80]; q["dark"] = bool(p.get("dark"))
        mw_ = p.get("missed_why") if isinstance(p.get("missed_why"), dict) else {}
        q["missed_why"] = {str(k)[:20]: n(v) for k, v in list(mw_.items())[:20]}
        ph.append(q)
    out["phases"] = ph
    for k in ("persons", "persons_detected", "false_alarms"):
        out[k] = n(rep.get(k, 0))
    try:
        r_ = float(rep.get("rate") or 0); out["rate"] = max(0.0, min(100.0, r_)) if math.isfinite(r_) else 0.0
    except (TypeError, ValueError):
        out["rate"] = 0.0
    try:
        l_ = rep.get("latency_s"); out["latency_s"] = max(0.0, min(600.0, float(l_))) if l_ is not None and math.isfinite(float(l_)) else None
    except (TypeError, ValueError):
        out["latency_s"] = None
    for k in ("false_list", "missed_list"):
        out[k] = [x for x in (rep.get(k) if isinstance(rep.get(k), list) else []) if isinstance(x, dict)][:500]
    return out


def _opt_trial_file():
    return os.path.join(DATA_DIR, "opt_trial.json")


def _opt_trial_mark(cfg):
    """the last known good detection settings while the automatic optimization tries something"""
    try:
        with open(_opt_trial_file(), "w") as f:
            json.dump({"cfg": cfg, "t": time.time(), "sim": bool(CFG.get("sim_on"))}, f)
    except OSError:
        pass


def _opt_trial_end():
    try:
        os.remove(_opt_trial_file())
    except OSError:
        pass


def testopt_recover():
    """at the start: the program stopped during a trial of the automatic optimization -> the good settings come back"""
    try:
        with open(_opt_trial_file()) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return
    if isinstance(d, dict) and isinstance(d.get("cfg"), dict):
        if bool(d.get("sim", False)) != bool(CFG.get("sim_on")):   # 2.97.0: measured in the other profile - do not mix
            log_event("sys", "Automatic optimization was interrupted (restart) - other profile, nothing restored")
            _opt_trial_end()
            return
        opt_restore(d["cfg"], "automatic optimization was interrupted")
        log_event("sys", "Automatic optimization was interrupted (restart) - the settings from before the trial are back")
    _opt_trial_end()


def testopt_load():
    try:
        with open(os.path.join(DATA_DIR, "testruns.json")) as f:
            d = json.load(f)
        TESTOPT["runs"] = [r for r in d.get("runs", []) if isinstance(r, dict)][-30:]
        TESTOPT["undo"] = d.get("undo") if isinstance(d.get("undo"), dict) else None
        if TESTOPT["runs"]:
            TESTOPT["sugg"] = opt_suggest(_clean_report(TESTOPT["runs"][-1].get("report") or {}))
    except Exception:                                   # a damaged file must not stop the program
        pass
    try:
        testopt_recover()
    except Exception:
        pass


def testopt_save():
    try:                                                # picture folders of runs that are no longer kept
        keep = {str(int(r["t"])) for r in TESTOPT["runs"][-30:]}
        if os.path.isdir(_testopt_dir()):
            for n_ in os.listdir(_testopt_dir()):
                if n_.isdigit() and n_ not in keep:
                    shutil.rmtree(os.path.join(_testopt_dir(), n_), ignore_errors=True)
    except OSError:
        pass
    try:
        dst = os.path.join(DATA_DIR, "testruns.json"); tmp = dst + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"runs": TESTOPT["runs"][-30:], "undo": TESTOPT["undo"]}, f)
        os.replace(tmp, dst)
    except OSError:
        pass


def opt_snapshot():
    return {k: CFG[k] for k in OPT_KEYS if k in CFG}


def opt_score(rep):
    """one number for a test run (higher = better): persons found (0-100), minus false alarms, slow reactions and
    animals taken for persons"""
    if not rep or not rep.get("persons"):
        return None
    lat = float(rep.get("latency_s") if rep.get("latency_s") is not None else -1)
    asp = sum(int(p.get("animals_as_person", 0)) for p in rep.get("phases", []))
    sc = float(rep.get("rate", 0)) - 12.0 * int(rep.get("false_alarms", 0)) - 4.0 * max(0.0, lat - 1.5) - 4.0 * asp
    return round(sc, 1)


def _clampv(k, v):
    sp = web_specs().get(k) or {}
    if sp.get("type") == "bool":
        return bool(v)
    v = max(sp.get("min", v), min(sp.get("max", v), v))
    st = sp.get("step") or 1
    v = round(round(v / st) * st, 2)
    return int(round(v)) if isinstance(CFG.get(k), int) and not isinstance(CFG.get(k), bool) else float(v)


def opt_suggest(rep):
    """What would make it better? Every proposal: id, title, why (English keys, the page translates them), the changes
    [key, old, new] and how much it should help (prio)."""
    if not rep or not rep.get("phases"):
        return []
    C = CFG; out = []
    def add(id_, title, why, changes, prio, n=0):
        ch = []
        for k, v in changes:
            if k not in C:
                continue
            nv = _clampv(k, v)
            if nv != C[k]:
                ch.append([k, C[k], nv])
        if ch:
            out.append({"id": id_, "title": title, "why": why, "n": n, "changes": ch, "prio": prio})
    causes = {}
    for f in rep.get("false_list", []):
        c = str(f.get("cause", ""))
        key = ("animal" if c.startswith("Tier") else {"Insekten am Licht": "insects", "Wind (Bäume, Büsche)": "wind", "Regen": "rain",
               "Spinnennetz": "web", "Gegenlicht": "glare", "Scheinwerfer": "headlights", "Tropfen auf der Linse": "drops",
               "Wolkenschatten": "shadows", "Schnee": "snow", "Nebel": "fog"}.get(c, "other"))
        causes[key] = causes.get(key, 0) + 1
    fa = int(rep.get("false_alarms", 0))
    ph = rep.get("phases", [])
    miss_day = sum(p["persons"] - p["persons_detected"] for p in ph if not p.get("dark"))
    miss_night = sum(p["persons"] - p["persons_detected"] for p in ph if p.get("dark"))
    why = {k: sum(int((p.get("missed_why") or {}).get(k, 0)) for p in ph) for k in ("dark", "small", "fast", "crouch")}
    asp = sum(int(p.get("animals_as_person", 0)) for p in ph)
    lat = float(rep.get("latency_s") if rep.get("latency_s") is not None else -1)
    tune_off = []      # 2.97.0: the auto-tuner rests during test runs instead of being switched off for good by a suggestion
    # ---- false alarms ----
    if causes.get("wind", 0) + causes.get("shadows", 0):
        n = causes.get("wind", 0) + causes.get("shadows", 0)
        add("wind", "Calm down wind and cloud shadows",
            "{n} false alarms from moving branches or cloud shadows: the wind filter reacts earlier and moving areas must be bigger.",
            [("wind_auto", True), ("wind_threshold", C["wind_threshold"] - 0.1), ("wind_boost_max", C["wind_boost_max"] + 1.5),
             ("min_area", C["min_area"] * 1.25)] + tune_off, 30 + 8 * n, n)
    if causes.get("insects", 0) + causes.get("web", 0):
        n = causes.get("insects", 0) + causes.get("web", 0)
        add("insects", "AI confirms every person",
            "{n} false alarms from insects or a spider web in the light: a person only counts when the AI sees it.",
            [("ai_require", True), ("ai_conf", max(C["ai_conf"], 0.55))], 35 + 8 * n, n)
    if causes.get("rain", 0) + causes.get("drops", 0) + causes.get("snow", 0):
        n = causes.get("rain", 0) + causes.get("drops", 0) + causes.get("snow", 0)
        add("rain", "Stronger rain and snow filter",
            "{n} false alarms from rain, snow or drops on the lens: the rain filter switches on earlier.",
            [("rain_auto", True), ("rain_threshold", C["rain_threshold"] - 0.1), ("min_area", C["min_area"] * 1.15)] + tune_off, 28 + 8 * n, n)
    if causes.get("glare", 0) + causes.get("headlights", 0) + causes.get("fog", 0):
        n = causes.get("glare", 0) + causes.get("headlights", 0) + causes.get("fog", 0)
        add("light", "Ignore changes of the light",
            "{n} false alarms from low sun, headlights or fog: the shadow filter and the AI check what moves.",
            [("shadow_filter", True), ("ai_require", True), ("car_filter", True), ("sensitivity", C["sensitivity"] - 8)] + tune_off, 26 + 8 * n, n)
    if causes.get("animal", 0) or asp:
        n = causes.get("animal", 0) + asp
        add("animals", "Do not take animals for persons",
            "{n} times an animal was reported as a person: the AI must be surer and small moving things count less.",
            [("ai_require", True), ("ai_conf", C["ai_conf"] + 0.1), ("min_area", C["min_area"] * 1.2)] + tune_off, 30 + 8 * n, n)
    if causes.get("other", 0) >= 2:
        n = causes.get("other", 0)
        add("calm", "Less sensitive",
            "{n} false alarms without a clear cause: a bit less sensitive.",
            [("sensitivity", C["sensitivity"] - 10), ("ai_conf", C["ai_conf"] + 0.05)] + tune_off, 18 + 5 * n, n)
    # ---- missed persons ----
    if miss_night and why["dark"]:
        add("night", "See better in the dark",
            "{n} persons were missed at night: brighten the picture earlier and let the AI accept less sure persons.",
            [("lowlight_auto", True), ("lowlight_threshold", C["lowlight_threshold"] + 20), ("ai_conf", C["ai_conf"] - 0.1),
             ("ai_require", False if not causes.get("insects") else C["ai_require"])], 40 + 10 * miss_night, miss_night)
    if why["small"] or why["crouch"]:
        n = why["small"] + why["crouch"]
        add("small", "Find small and crouching persons",
            "{n} persons were far away, small or crouching and were missed: smaller moving areas count too.",
            [("min_area", C["min_area"] * 0.7), ("sensitivity", C["sensitivity"] + 8), ("ai_conf", C["ai_conf"] - 0.05)] + tune_off, 38 + 10 * n, n)
    if why["fast"]:
        add("fast", "Catch fast persons",
            "{n} fast persons (joggers) were missed: fewer pictures needed to recognise walking, the AI looks at every picture.",
            [("walk_frames", C["walk_frames"] - 2), ("ai_every", 1), ("speed_consistency", C["speed_consistency"] - 0.05)] + tune_off,
            32 + 10 * why["fast"], why["fast"])
    unexplained = miss_day - min(miss_day, why["small"] + why["crouch"] + why["fast"])
    if unexplained > 0:
        miss_day = unexplained
        add("day", "More sensitive by day",
            "{n} persons were missed by day: more sensitive and the AI accepts less sure persons.",
            [("sensitivity", C["sensitivity"] + 10), ("ai_conf", C["ai_conf"] - 0.1)] + tune_off, 36 + 10 * miss_day, miss_day)
    # ---- reaction time ----
    if lat > 2.0:
        add("speed", "React faster",
            "MoveEye needed {n} s on average: the AI looks at every picture and walking is recognised sooner.",
            [("ai_every", 1), ("walk_frames", C["walk_frames"] - 1)], 20 + int(6 * (lat - 2.0)), round(lat, 1))
    # ---- conflicts: what makes it less sensitive does not go together with what makes it more sensitive ----
    ids = {x["id"] for x in out}
    if ids & {"night", "small", "day"} and ids & {"wind", "calm", "animals"}:
        for x in out:                                   # keep both, but say it: the test after taking over decides
            x["conflict"] = True
    return sorted(out, key=lambda x: -x["prio"])


def opt_apply(changes, why="test run"):
    """take over changes [[key, old, new], ...]; returns the snapshot before (for «undo»)"""
    before = opt_snapshot()
    for k, _old, new in changes:
        if k in CFG:
            CFG[k] = _clampv(k, new); sched_user_changed(k)
    if CFG.get("sim_on"):                                  # 2.97.0: found in the simulation - asked «also real?» when it ends
        so = dict(CFG.get("simprof_opt") or {})
        for k, _old, _new in changes:
            if k in CFG:
                so[k] = CFG[k]
        CFG["simprof_opt"] = so
    save_settings()
    log_event("sys", "Optimization (" + why + "): " + ", ".join(f"{k} {o} -> {CFG[k]}" for k, o, _n in changes))
    return before


def opt_restore(snap, why="undo"):
    for k, v in (snap or {}).items():
        if k in CFG and isinstance(v, type(CFG[k])) or (k in CFG and isinstance(CFG[k], float) and isinstance(v, int)):
            CFG[k] = v; sched_user_changed(k)
    save_settings()
    log_event("sys", f"Optimization: settings restored ({why})")


def _simtest(action, **kw):
    try:
        r = sim_control(dict(action=action, **kw))
        return r if isinstance(r, dict) else {}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def _testopt_dir(run_id=None):
    d = os.path.join(DATA_DIR, "testruns")
    return os.path.join(d, str(int(run_id))) if run_id is not None else d


def _testopt_frames(stop, frames, t0):
    """during a test run: every 1.5 s a small picture of what MoveEye sees (with its marks) - for the report"""
    while not stop.is_set():
        w = WATCH_REF.get("w")
        f = getattr(w, "frame_out", None) if w is not None else None
        if f is not None:
            try:
                h, wd = f.shape[:2]; sc = 360.0 / max(1, wd)
                ok, buf = cv2.imencode(".jpg", cv2.resize(f, (360, int(h * sc))), [cv2.IMWRITE_JPEG_QUALITY, 62])
                if ok:
                    frames.append((time.time() - t0, buf.tobytes()))
            except Exception:
                pass
        stop.wait(1.5)


def _testopt_pics(run, frames):
    """the moments of the false alarms and of the missed persons: MoveEye's own picture of that moment"""
    rep_ = run["report"]; out = []
    want = [("false", f) for f in rep_.get("false_list", [])] + [("missed", m) for m in rep_.get("missed_list", [])]
    if not want or not frames:
        return out
    d = _testopt_dir(run["t"]); os.makedirs(d, exist_ok=True)
    for i, (kind, e) in enumerate(want[:24]):
        t = float(e.get("t", 0))
        best = min(frames, key=lambda x: abs(x[0] - t))
        if abs(best[0] - t) > 6:
            continue
        name = f"{kind[0]}{i:02d}.jpg"
        try:
            with open(os.path.join(d, name), "wb") as f_:
                f_.write(best[1])
        except OSError:
            continue
        ph = rep_.get("phases", [])
        pn = ph[int(e.get("phase", 0))]["name"] if 0 <= int(e.get("phase", 0)) < len(ph) else ""
        out.append({"kind": kind, "t": round(t, 1), "phase": pn, "why": e.get("cause") if kind == "false" else ", ".join(e.get("why") or []) or "?",
                    "what": e.get("kind", ""), "file": name})
    return out


def testopt_run(plan):
    """one test run, waits until it is finished (or stopped); returns the run (dict) or None"""
    r = _simtest("test_start", plan=plan)
    if not r.get("ok"):
        TESTOPT["msg"] = str(r.get("error") or "the simulator does not answer (3D-3.27 or newer needed)")
        return None
    TESTOPT["sim"] = r
    frames = []; stop_ = threading.Event()
    threading.Thread(target=_testopt_frames, args=(stop_, frames, time.time()), daemon=True).start()
    try:
        return _testopt_wait(plan, r, frames)
    finally:
        stop_.set()


def _testopt_wait(plan, r, frames):
    t_end = time.time() + max(120, int(r.get("total_s") or 600) * 2)
    seen_running = True
    while time.time() < t_end:
        if TESTOPT["stop"]:
            _simtest("test_stop")
            TESTOPT["msg"] = "stopped"
            return None
        time.sleep(2.0)
        st = _simtest("test_report")
        if not st:
            continue
        TESTOPT["sim"] = st
        if st.get("running"):
            continue
        rep = _clean_report(st.get("report") or {})
        if not rep or rep.get("plan") != plan:
            TESTOPT["msg"] = str(st.get("info") or "test run ended without report")
            return None
        run = {"t": time.time(), "plan": plan, "report": rep, "score": opt_score(rep), "cfg": opt_snapshot(),
               "mw": APP_VERSION, "sim": str(rep.get("simulator") or "")}
        try:
            run["pics"] = _testopt_pics(run, frames)
        except Exception as e:
            run["pics"] = []; log_event("sys", f"Test run pictures: {e}"[:150])
        with _TESTOPT_LOCK:
            TESTOPT["runs"].append(run); TESTOPT["runs"] = TESTOPT["runs"][-30:]
            TESTOPT["sugg"] = opt_suggest(rep)
            testopt_save()
        log_event("sys", f"Test run «{plan}» finished: persons {rep.get('persons_detected')}/{rep.get('persons')}, "
                         f"false alarms {rep.get('false_alarms')}, score {run['score']}")
        return run
    TESTOPT["msg"] = "the test run takes too long - stopped"
    _simtest("test_stop")
    return None


def _testopt_thread(kind, plan, tries=4):
    try:
        TESTOPT["stop"] = False; TESTOPT["msg"] = ""
        if kind == "run":
            TESTOPT["busy"] = "run"
            testopt_run(plan)
            return
        # automatic optimization: base run, then try the proposals one by one; keep a change only if the score rises
        TESTOPT["busy"] = "auto"
        A = {"plan": plan, "step": 0, "tries": tries, "log": [], "start_cfg": opt_snapshot(), "base": None, "best": None, "kept": []}
        TESTOPT["auto"] = A
        base = testopt_run(plan)
        if base is None or base["score"] is None:
            A["log"].append({"what": "base", "ok": False}); return
        A["base"] = A["best"] = base["score"]
        tried = set()
        _opt_trial_mark(A["start_cfg"])
        while A["step"] < tries and not TESTOPT["stop"]:
            sug = [x for x in opt_suggest(base["report"] if not A["kept"] else TESTOPT["runs"][-1]["report"]) if x["id"] not in tried]
            if not sug:
                break
            x = sug[0]; tried.add(x["id"]); A["step"] += 1
            A["now"] = x["title"]
            before = opt_apply(x["changes"], "automatic, try " + x["id"])
            run = testopt_run(plan)
            if run is None or run["score"] is None:
                opt_restore(before, "automatic, no result"); break
            better = run["score"] >= A["best"] + 3.0
            A["log"].append({"id": x["id"], "title": x["title"], "changes": x["changes"], "score": run["score"], "kept": better})
            if better:
                A["best"] = run["score"]; A["kept"].append(x["id"]); _opt_trial_mark(opt_snapshot())
            else:
                opt_restore(before, "automatic, not better")
        A["now"] = ""
        if A["kept"]:
            TESTOPT["undo"] = {"cfg": A["start_cfg"], "t": time.time(), "what": "auto"}
            testopt_save()
        log_event("sys", f"Automatic optimization finished: score {A['base']} -> {A['best']}, kept: {', '.join(A['kept']) or 'nothing'}")
        _opt_trial_end()
    except Exception as e:                              # 2.95.33: an error in the middle of a trial -> the good settings back
        log_event("sys", f"Optimization stopped by an error: {type(e).__name__}: {e}"[:200])
        try:
            testopt_recover()
        except Exception:
            pass
    finally:
        TESTOPT["busy"] = ""


def testopt_compare():
    """the last run against the last run of the same test with another MoveEye version: what got better / worse"""
    runs = TESTOPT["runs"]
    if not runs:
        return None
    L = runs[-1]
    prev = next((r for r in reversed(runs[:-1]) if r.get("plan") == L.get("plan") and r.get("mw") and r.get("mw") != L.get("mw")), None)
    if prev is None or L.get("score") is None or prev.get("score") is None:
        return None
    ph = []
    pp = {p["name"]: p for p in prev["report"].get("phases", [])}
    for p in L["report"].get("phases", []):
        q = pp.get(p["name"])
        if not q:
            continue
        d_found = p["persons_detected"] - q["persons_detected"]; d_fa = p["false_alarms"] - q["false_alarms"]
        if d_found or d_fa:
            ph.append({"name": p["name"], "found": d_found, "fa": d_fa})
    return {"from": prev.get("mw"), "to": L.get("mw"), "score": round(L["score"] - prev["score"], 1), "phases": ph}


def testopt_nightly_loop():
    """2.95.28: every night at the chosen hour one test run (when the simulator is connected and nothing else runs);
    a message only when the score is clearly lower than at the last night run of the same test"""
    done = ""
    while True:
        time.sleep(60)
        try:
            if not CFG.get("testopt_nightly"):
                continue
            now = datetime.now(); day = now.strftime("%Y-%m-%d")
            if now.hour != int(CFG.get("testopt_hour", 3)) or done == day or simtask_busy() or is_armed():
                continue
            if not (CFG["sim_on"] and SIM["ok"] and time.time() - SIM["t"] < 5):
                continue
            if now.weekday() == 6 and CFG.get("weekcheck_on"):
                continue                                   # 2.97.0: Sunday at this hour the weekly check runs (same plan family)
            done = day
            plan = CFG.get("testopt_plan") if CFG.get("testopt_plan") in ("standard", "quick", "hard", "night", "spielwege") else "quick"
            prev = next((r for r in reversed(TESTOPT["runs"]) if r.get("plan") == plan and r.get("night")), None)
            TESTOPT["busy"] = "night"; TESTOPT["stop"] = False
            try:
                run = testopt_run(plan)
            finally:
                TESTOPT["busy"] = ""
            if run is None:
                continue
            run["night"] = True; testopt_save()
            if prev and prev.get("score") is not None and run.get("score") is not None and run["score"] <= prev["score"] - 10:
                w = WATCH_REF.get("w")
                if w is not None:
                    w.notifier.info(trf("Night test run: score {a} instead of {b} - the recognition got worse. Details: tab Simulator.",
                                        a=run["score"], b=prev["score"]), title="{name}: " + tr("Test run"))
        except Exception as e:
            log_event("sys", f"Night test run: {e}"[:150])


def testopt_state():
    runs = TESTOPT["runs"]
    small = [{"t": r["t"], "plan": r["plan"], "score": r["score"], "rate": r["report"].get("rate"), "fa": r["report"].get("false_alarms"),
              "lat": r["report"].get("latency_s"), "persons": r["report"].get("persons"), "found": r["report"].get("persons_detected"),
              "cfg": r.get("cfg"), "mw": r.get("mw", ""), "night": bool(r.get("night"))} for r in runs[-12:]]
    return {"busy": TESTOPT["busy"], "msg": TESTOPT["msg"], "sim": TESTOPT["sim"], "runs": small,
            "last": runs[-1] if runs else None, "sugg": TESTOPT["sugg"], "undo": bool(TESTOPT["undo"]),
            "auto": TESTOPT["auto"], "connected": bool(CFG["sim_on"] and SIM["ok"] and time.time() - SIM["t"] < 5),
            "keys": {k: CFG[k] for k in OPT_KEYS if k in CFG}, "compare": testopt_compare(),
            "nightly": {"on": bool(CFG.get("testopt_nightly")), "hour": int(CFG.get("testopt_hour", 3)), "plan": CFG.get("testopt_plan", "quick")}}


