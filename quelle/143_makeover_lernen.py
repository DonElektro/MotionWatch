#@ MoveEye – Teil 143: Makeover – Fehlalarm-Lernen, blinde Flecken, Nacht-Generalprobe, Schwellen automatisch, Wochen-Check. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.8 (Makeover-Punkte 21–25), für die echte Überwachung, mit dem Simulator:
#  21  Fehlalarm-Lernen: eine Aufnahme mit 👎 (und Ursache) wird im Simulator nachgestellt (Tier, Wind, Licht, Regen, Auto)
#      und 60 s beobachtet. Meldet MoveEye dabei wieder eine Person, kommen die Bilder als «keine Person»-Beispiele nach
#      fa_learn/ (für das Training) und die passenden Vorschläge (Fehlalarme) werden gezeigt; sonst: «gelernt, bleibt ruhig».
#  22  Blinde Flecken: der Simulator stellt eine Person nacheinander an Punkte rund um MoveEye (Richtungen × Abstände) und
#      schaut, ob MoveEye sie erkennt - Karte grün / rot / grau (ausser Sicht) und ein Tipp.
#  23  Nacht-Generalprobe: wie 22, aber nur geradeaus, zur Uhrzeit von heute Nacht: «Heute Nacht erkennst du Personen bis
#      18 m». Auf Wunsch von selbst beim Einschalten des Schutzes in der Simulation.
#  24  Schwellen automatisch: die automatische Optimierung für Tag (quick) und Nacht (night) nacheinander.
#  25  Erkennungs-Check jede Woche: sonntags zur Stunde des Nacht-Tests der Plan «standard»; Push, wenn es schlechter wurde.
# ----------------------------------------------------------------------------
FALEARN = {"busy": False, "last": [], "cur": ""}
BLIND = {"busy": False, "kind": "", "last": None, "rehearsal": None}
AUTOTH = {"busy": False, "step": "", "last": None}


# ---- 21 -------------------------------------------------------------------------------------------------------------------
def falearn_start(name, cause):
    if FALEARN["busy"]:
        return False, "already running"
    if simtask_busy():
        return False, simtask_refuse("false alarm learning")
    if not sim_ready():
        return False, "only with the simulator"
    if not rec_path(name):
        return False, "not found"
    FALEARN.update(busy=True, cur=name)
    threading.Thread(target=_falearn_thread, args=(name, str(cause or "other")), daemon=True, name="falearn").start()
    return True, ""


def _falearn_thread(name, cause):
    res = {"name": name, "cause": cause, "t": time.time(), "alarms": 0, "pics": 0, "ok": False}
    try:
        meta = _read_sidecar(name)
        situ = meta.get("situ") or {}
        try:
            dt = datetime.fromisoformat(meta["start"]) if meta.get("start") else (parse_stamp(os.path.basename(name)) or datetime.now())
        except ValueError:
            dt = datetime.now()
        sim_control({"action": "farecreate", "cause": cause, "hour": round(dt.hour + dt.minute / 60.0, 2),
                     "pan_deg": float(situ.get("pan_deg") or 0.0), "rain": bool(situ.get("rain"))})
        d = os.path.join(DATA_DIR, "fa_learn", datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + re.sub(r"[^a-z]", "", cause))
        was = 0
        t_end = time.time() + 60
        w0 = WATCH_REF.get("w")
        if w0 is not None:
            w0.raw_until = t_end + 1                        # the picture without marks, for the training
        last_pic = 0.0
        while time.time() < t_end:
            p = int(STATE.get("persons") or 0)
            if p > 0 and was == 0:
                res["alarms"] += 1
            if p > 0 and time.time() - last_pic > 2.0 and res["pics"] < 10:
                w = WATCH_REF.get("w")
                f = getattr(w, "frame_raw", None) if w is not None else None
                if f is not None:
                    os.makedirs(d, exist_ok=True)
                    cv2.imwrite(os.path.join(d, "%02d.jpg" % res["pics"]), f, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    res["pics"] += 1
                    last_pic = time.time()
            was = p
            time.sleep(0.5)
        res["ok"] = res["alarms"] == 0
        if res["pics"]:
            with open(os.path.join(d, "info.json"), "w") as f_:
                json.dump({"label": "no_person", "cause": cause, "from": name}, f_)
        sim_control({"action": "farecreate", "cause": "end"})
    except Exception as e:
        res["error"] = str(e)[:100]
    FALEARN["last"].insert(0, res)
    del FALEARN["last"][10:]
    FALEARN.update(busy=False, cur="")
    log_event("sys", f"False alarm learning ({cause}): {res['alarms']} alarm(s) in 60 s, {res['pics']} picture(s) kept as «no person»")


# ---- 22 / 23 --------------------------------------------------------------------------------------------------------------
def blind_start(kind="map", hour=None):
    if BLIND["busy"]:
        return False, "already running"
    if simtask_busy():
        return False, simtask_refuse("blind spots")
    if not sim_ready():
        return False, "only with the simulator"
    q = {"action": "blindmap", "do": "start"}
    if kind == "rehearsal":
        q.update(az=[0], dist=[6, 10, 14, 18, 22, 26, 30], hour=hour if hour is not None else 22.5, walk=True)
    else:
        q.update(az=[-60, -40, -20, 0, 20, 40, 60], dist=[5, 10, 15, 20, 25])
    try:
        r = sim_control(q)
    except Exception:
        return False, "simulator not reachable"
    if not r.get("ok"):
        return False, str(r.get("error") or "not supported - update the simulator")
    BLIND.update(busy=True, kind=kind)
    threading.Thread(target=_blind_wait, daemon=True, name="blindmap").start()
    return True, ""


def _blind_wait():
    t_end = time.time() + 900
    res = None
    while time.time() < t_end:
        time.sleep(3)
        try:
            r = sim_control({"action": "blindmap", "do": "info"})
        except Exception:
            continue
        BLIND["prog"] = r.get("prog")
        if not r.get("busy"):
            res = r.get("result")
            break
    kind = BLIND["kind"]
    if res:
        res["tip"] = blind_tip(res)
        if kind == "rehearsal":
            BLIND["rehearsal"] = res
            far = res.get("max_found")
            txt = trf("Night rehearsal: tonight persons are recognised up to {d} m", d=far) if far else tr("Night rehearsal: no person recognised - check the night settings (IR light, night mode)")
            log_event("sys", txt)
            res["text"] = txt
        else:
            BLIND["last"] = res
            log_event("sys", f"Blind spots: {res.get('found', 0)} of {res.get('inview', 0)} places recognised")
    BLIND.update(busy=False, kind="")


def blind_tip(res):
    """a short tip from the map: where are the blind spots?"""
    pts = res.get("points") or []
    miss = [p for p in pts if p.get("inview") and not p.get("found")]
    if not pts:
        return ""
    if not any(p.get("inview") for p in pts):
        return tr("The person was never in the picture – check where the head looks (patrol, pan).")
    if not miss:
        return tr("No blind spot in view - well placed.")
    far = [p for p in miss if p["d"] >= 15]
    left = [p for p in miss if p["az"] < -10]
    right = [p for p in miss if p["az"] > 10]
    out = ""
    if len(far) >= len(miss) * 0.6:
        out = tr("Mostly far away: put MoveEye higher or tilt it a little up; at night more IR light helps.")
    elif len(left) > len(right) * 2:
        out = tr("Mostly on the left: turn MoveEye a little to the left or add a patrol point there.")
    elif len(right) > len(left) * 2:
        out = tr("Mostly on the right: turn MoveEye a little to the right or add a patrol point there.")
    else:
        out = tr("Spread over the picture: check the sensitivity (A/B comparison) and the zones.")
    nv = [p for p in pts if not p.get("inview")]
    if len(nv) > len(pts) * 0.3:
        out += " " + tr("Many places are outside the picture: a patrol or a second device covers them.")
    return out


def rehearsal_on_arm():
    """armed in the simulation: the night rehearsal by itself (when switched on)"""
    if CFG.get("rehearsal_on_arm") and sim_ready() and not BLIND["busy"] and not simtask_busy():
        now = datetime.now()
        h = now.hour + now.minute / 60.0
        blind_start("rehearsal", h if (h >= 20 or h < 6) else 22.5)


# ---- 24 --------------------------------------------------------------------------------------------------------------------
def autoth_start():
    if AUTOTH["busy"] or simtask_busy():
        return False, simtask_refuse("automatic thresholds") or "already running"
    if not sim_ready():
        return False, "only with the simulator"
    AUTOTH.update(busy=True, step="day")
    threading.Thread(target=_autoth_thread, daemon=True, name="autoth").start()
    return True, ""


def _autoth_thread():
    res = []
    try:
        for plan in ("quick", "night"):
            AUTOTH["step"] = plan
            _sim_free()
            _testopt_thread("auto", plan, 4)
            A = TESTOPT.get("auto") or {}
            res.append({"plan": plan, "base": A.get("base"), "best": A.get("best"), "kept": list(A.get("kept") or [])})
    finally:
        AUTOTH.update(busy=False, step="", last={"t": time.time(), "res": res})
        log_event("sys", "Automatic thresholds: " + "; ".join(f"{r['plan']} {r['base']} -> {r['best']}" for r in res))


# ---- 25 --------------------------------------------------------------------------------------------------------------------
def weekcheck_loop():
    while True:
        time.sleep(120)
        try:
            if not CFG.get("weekcheck_on"):
                continue
            now = datetime.now()
            wk = now.strftime("%G-W%V")
            if now.weekday() != 6 or now.hour != int(CFG.get("testopt_hour", 3)) or CFG.get("weekcheck_last") == wk:
                continue
            if not sim_ready() or simtask_busy() or is_armed():
                continue
            prev = next((r for r in reversed(TESTOPT["runs"]) if r.get("week")), None)
            TESTOPT["busy"] = "week"
            try:
                _sim_free()
                run = testopt_run("standard")
            finally:
                TESTOPT["busy"] = ""
            if run is None:
                continue                                   # 2.97.0: refused / stopped - try again in 2 min (the week is not lost)
            CFG["weekcheck_last"] = wk
            save_settings()
            run["week"] = True
            testopt_save()
            log_event("sys", f"Weekly recognition check: score {run['score']}")
            if prev and prev.get("score") is not None and run.get("score") is not None and run["score"] <= prev["score"] - 8:
                w = WATCH_REF.get("w")
                if w is not None:
                    w.notifier.info(trf("Weekly check: score {a} instead of {b} – the recognition got worse. Details: tab Simulator.",
                                        a=run["score"], b=prev["score"]), title="{name}: " + tr("Weekly check"))
        except Exception as e:
            log_event("sys", f"Weekly check: {e}"[:150])


threading.Thread(target=weekcheck_loop, daemon=True, name="weekcheck").start()


def blind_game_pts():
    """2.98.0: where players in the simulator games were visible but not reported - a layer of the blind spot map (30 s cache)"""
    if time.time() - BLIND.get("game_t", 0) > 30 and sim_ready():
        BLIND["game_t"] = time.time()
        try:
            r = sim_control({"action": "blindmap", "do": "game"})
            BLIND["game"] = [p for p in (r.get("pts") or []) if isinstance(p, dict)][-400:] if r.get("ok") else BLIND.get("game", [])
        except Exception:
            pass
    return BLIND.get("game") or []


def learn_state():
    return {"falearn": {"busy": FALEARN["busy"], "cur": FALEARN["cur"], "last": FALEARN["last"][:5]},
            "blind": {"busy": BLIND["busy"], "kind": BLIND["kind"], "prog": BLIND.get("prog"), "last": BLIND["last"], "rehearsal": BLIND["rehearsal"],
                      "game": blind_game_pts()},
            "autoth": {"busy": AUTOTH["busy"], "step": AUTOTH["step"], "last": AUTOTH["last"]},
            "week": {"on": bool(CFG.get("weekcheck_on")), "runs": [{"t": r["t"], "score": r["score"], "mw": r.get("mw")} for r in TESTOPT["runs"] if r.get("week")][-8:]},
            "rehearsal_on_arm": bool(CFG.get("rehearsal_on_arm")), "fa_learn_auto": bool(CFG.get("fa_learn_auto"))}
