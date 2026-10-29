#@ MoveEye – Teil 141: Makeover – Trainings-Nacht, A/B-Vergleich, Test-Posteingang und Alarm-Kette, Störfall-Übungen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.6 (Makeover-Punkte 12–15), alles mit dem Simulator:
#  12  Trainings-Nacht: zur eingestellten Stunde mehrere Testläufe in verschiedenen Szenen (Tag- und Nacht-Plan), dann die
#      automatische Optimierung am schwächsten Plan, dann Trainingsbilder (YOLO-Paket auf dem PC des Simulators); am
#      Schluss ein Bericht als Push und unter «Simulator-Zentrale». Nur wenn nicht Schutz eingeschaltet und kein Spiel läuft.
#  13  A/B-Vergleich: zweimal derselbe Testlauf - A mit den jetzigen Einstellungen, B mit einer Änderung. B bleibt nur,
#      wenn es klar besser ist (Punktzahl +3), sonst kommt A zurück.
#  14  Test-Posteingang: im Simulator landen die Meldungen auf Wunsch hier statt auf dem Handy (niemand wird gestört);
#      «Alarm-Kette testen» spielt Push, Licht und Sirene durch und sagt, was ging.
#  15  Störfall-Übungen: Akku leer, WLAN / Internet weg, Hitze, Kälte - MoveEye erlebt es wie echt (nur ohne echtes
#      Herunterfahren) und am Schluss steht, wie es reagiert hat.
# ----------------------------------------------------------------------------
SANDBOX = {"items": [], "force": 0}
DRILL = {"kind": "", "t0": 0.0, "until": 0.0, "seen": [], "busy": False, "last": None, "restore": {}}
TRAIN = {"busy": False, "step": "", "last": None, "stop": False, "day": ""}
ABT = {"busy": False, "step": "", "last": None}
DRILL_KINDS = {"battery": 90, "net": 100, "heat": 70, "cold": 70}
AB_PRESETS = {
    "more_sens": ("More sensitive", {"sensitivity": +10}), "less_sens": ("Less sensitive", {"sensitivity": -10}),
    "ai_strict": ("AI stricter", {"ai_conf": +0.1}), "ai_loose": ("AI more generous", {"ai_conf": -0.1}),
    "small": ("Also small objects", {"min_area": -0.3}), "walk": ("Faster decision", {"walk_frames": -2}),
}


def simtask_busy(except_=""):
    """2.97.0: one lock for everything that uses the simulator to measure or to train: who is busy now ('' = free).
    Every start asks here first, so two of them never mix (a person of the blind spots in a test run, a game round
    in the training night ...). A game round in the simulator counts too."""
    def g(n, d, k="busy"):
        try:
            return n if d.get(k) else ""
        except Exception:
            return ""
    for name, busy in (("test run", TESTOPT.get("busy")), ("training night", TRAIN.get("busy")), ("A/B comparison", ABT.get("busy")),
                       ("drill", DRILL.get("busy"))):
        if busy and name != except_:
            return name
    for name, ref in (("blind spots", "BLIND"), ("false alarm learning", "FALEARN"), ("automatic thresholds", "AUTOTH"), ("demo", "DEMO_RUN")):
        d = globals().get(ref)
        if isinstance(d, dict) and d.get("busy") and name != except_:
            return name
    try:
        if PROTECT["test"]["busy"] and except_ != "protection test":
            return "protection test"
    except (NameError, KeyError):
        pass
    if except_ != "game" and sim_game_running():
        return "game"
    try:
        return sim_busy_remote()                           # 2.98.13: started in the simulator window (147_simsperre.py)
    except NameError:
        return ""


def simtask_refuse(me):
    """'' when free, else the reason for the page"""
    b = simtask_busy(me)
    return "" if not b else trf("The simulator is busy: {what}", what=tr(b))


def sim_ready():
    return bool(CFG.get("sim_on")) and SIM.get("ok") and time.time() - SIM.get("t", 0) < 6


# ---- 14: the test inbox ---------------------------------------------------------------------------------------------
def sim_game_running():
    """2.97.0: a round in the simulator (countdown / play) - the players are not burglars"""
    if not CFG.get("sim_on"):
        return False
    try:
        g = sim_game()                                     # fetches it fresh in the background now and then
    except Exception:
        g = SIMGAME.get("g")
    return bool(g) and g.get("round") in ("play", "countdown")


def event_origin():
    """2.97.0: real | sim | game | drill | demo - recordings, the diary and the reports can tell them apart"""
    if not CFG.get("sim_on"):
        return "real"
    if DRILL.get("kind") and time.time() < DRILL.get("until", 0):
        return "drill"
    try:
        if DEMO_RUN.get("busy"):
            return "demo"
    except NameError:
        pass
    return "game" if sim_game_running() else "sim"


def sandbox_active():
    """the test inbox instead of the phone: drills / demo (force), simulation with the switch, and always while a game runs"""
    if SANDBOX["force"] > 0:
        return True
    if not CFG.get("sim_on"):
        return False
    return bool(CFG.get("notify_sandbox")) or sim_game_running()


def sandbox_add(title, text, jpg=None, ev=""):
    it = {"t": datetime.now().strftime("%H:%M:%S"), "title": title, "text": text, "ev": ev, "icon": ev_icon(ev),
          "held": bool(DRILL["kind"] == "net" and time.time() < DRILL["until"])}
    if jpg:
        try:
            d = os.path.join(DATA_DIR, "testinbox")
            os.makedirs(d, exist_ok=True)
            n = "%d.jpg" % int(time.time() * 1000)
            with open(os.path.join(d, n), "wb") as f:
                f.write(jpg)
            it["img"] = n
            fs = sorted(os.listdir(d))
            for x in fs[:-20]:
                os.remove(os.path.join(d, x))
        except OSError:
            pass
    SANDBOX["items"].insert(0, it)
    del SANDBOX["items"][30:]
    if DRILL["kind"] and time.time() < DRILL["until"]:
        DRILL["seen"].append({"t": it["t"], "kind": "push", "text": title + ": " + text})
    log_event("web", f"Test inbox: {title}"[:160])


def alarmchain_test():
    """Push, light, siren - one after the other, into the test inbox (nobody is disturbed)"""
    out = []
    try:
        w = WATCH_REF.get("w")
        n0 = len(SANDBOX["items"])
        if w is not None:
            p = {"event": "person", "persons": 1, "time": datetime.now().isoformat(timespec="seconds"), "snapshot": None, "rain": False,
                 "wind": "", "source": STATE.get("source_label", ""), "link": "", "more": 0, "_test": True}
            jpg = None
            f = getattr(w, "frame_out", None)
            if f is not None:
                ok_, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 70])
                jpg = buf.tobytes() if ok_ else None
            w.notifier._dispatch(p, jpg, "test.jpg")
        got = len(SANDBOX["items"]) > n0
        out.append({"name": "Push message", "ok": got, "text": SANDBOX["items"][0]["title"] if got else "no message"})
        was = bool((STATE.get("lights") or {}).get("white"))
        light_alarm()
        lit = False
        for _ in range(12):
            time.sleep(0.25)
            if (STATE.get("lights") or {}).get("white"):
                lit = True
                break
        out.append({"name": "Light", "ok": lit or was, "text": "" if lit or was else "the white light is not set to «on alarm» (Light & sound)"})
        ok_s, err_s = sound_play(None, 3, None, reason="test")
        time.sleep(0.6)
        out.append({"name": "Siren", "ok": bool(ok_s and SOUND.get("playing")), "text": err_s or ""})
        time.sleep(2.5)
        try:
            sound_stop()
        except Exception:
            pass
        esc = bool(CFG.get("escalate_on"))
        out.append({"name": "Siren after a while (escalation)", "ok": esc, "text": trf("after {s} s", s=int(CFG.get("escalate_siren_s", 30))) if esc else "off"})
    except Exception as e:
        out.append({"name": "Error", "ok": False, "text": str(e)[:100]})
    log_event("sys", "Alarm chain test: " + ", ".join(f"{x['name']} {'ok' if x['ok'] else 'no'}" for x in out))
    return out


# ---- 15: drills ------------------------------------------------------------------------------------------------------
def drill_active(kind):
    return DRILL["kind"] == kind and time.time() < DRILL["until"]


def drill_note(kind, text):
    """called from log_event: what MoveEye did during a drill"""
    if DRILL["kind"] and time.time() < DRILL["until"] + 3 and len(DRILL["seen"]) < 40:
        DRILL["seen"].append({"t": datetime.now().strftime("%H:%M:%S"), "kind": kind, "text": str(text)[:160]})


def drill_start(kind):
    if kind not in DRILL_KINDS:
        return False, "unknown drill"
    if DRILL["busy"]:
        return False, "a drill is already running"
    if simtask_busy():
        return False, simtask_refuse("drill")
    if not sim_ready():
        return False, "only with the simulator"
    DRILL.update(kind=kind, t0=time.time(), until=time.time() + DRILL_KINDS[kind], seen=[], busy=True, restore={})
    SANDBOX["force"] += 1
    if kind in ("heat", "cold"):
        DRILL["restore"] = {"temp_alarm_on": CFG.get("temp_alarm_on")}
        CFG["temp_alarm_on"] = True                        # for the drill: the temperature alarm listens
        try:
            DRILL["restore"]["ambient"] = float(SIM.get("ambient", 15.0))
            sim_control({"action": "set", "id": "ambient", "value": 38.0 if kind == "heat" else -12.0})
        except Exception:
            pass
    if kind == "battery":
        DRILL["restore"] = {"batt_warned": CFG.get("batt_warned")}
        CFG["batt_warned"] = False
        bm = getattr(WATCH_REF.get("w"), "battmon", None)
        if bm is not None:
            bm._on_batt = False                            # so the first drill tick tells «power cut»
    if kind == "net":
        w = WATCH_REF.get("w")
        try:
            w.netmon.recheck = True
        except Exception:
            pass
    log_event("sys", f"Drill started: {kind}")
    threading.Thread(target=_drill_end_later, daemon=True, name="drill").start()
    return True, ""


def _drill_end_later():
    while time.time() < DRILL["until"]:
        time.sleep(1)
    kind = DRILL["kind"]
    try:
        rs = DRILL.get("restore") or {}
        if "temp_alarm_on" in rs:
            CFG["temp_alarm_on"] = rs["temp_alarm_on"]
        if "ambient" in rs:
            sim_control({"action": "set", "id": "ambient", "value": rs["ambient"]})
        if "batt_warned" in rs:
            CFG["batt_warned"] = bool(rs["batt_warned"])
            bm = getattr(WATCH_REF.get("w"), "battmon", None)
            if bm is not None and getattr(bm, "_on_batt", None):
                bm.ups_events(7.6, 60, None, False, False)  # the «mains power back» of the drill
                bm._on_batt = None
        if kind == "net":
            w = WATCH_REF.get("w")
            try:
                w.netmon.recheck = True
            except Exception:
                pass
            time.sleep(4)
    except Exception as e:
        DRILL["seen"].append({"t": "", "kind": "sys", "text": str(e)[:100]})
    time.sleep(2)
    seen = [x for x in DRILL["seen"] if x.get("kind") not in ("auto", "servo", "patrol", "relay")
            and not str(x["text"]).startswith(("Drill started", "Test inbox"))]
    DRILL["last"] = {"kind": kind, "t": DRILL["t0"], "s": DRILL_KINDS.get(kind, 0), "reactions": seen[:30]}
    DRILL.update(kind="", busy=False)
    SANDBOX["force"] = max(0, SANDBOX["force"] - 1)
    log_event("sys", f"Drill finished: {kind}, {len(seen)} reactions")
    try:
        if seen:
            points_add(50, f"Drill done: {kind}")
    except NameError:
        pass


def drill_battery_tick(bm):
    """BatteryMonitor.tick during the battery drill: the charge falls from 60 to 4 % - like real, but never shuts down"""
    el = time.time() - DRILL["t0"]
    pct = max(4, int(60 - el / DRILL_KINDS["battery"] * 60))
    hours = round(pct / 100.0 * 4.0, 1)
    STATE["battery"] = {"on": True, "src": "drill", "pct": pct, "hours": hours, "on_battery": True, "charging": False, "watts": 4.2,
                        "use_w": 4.2, "volt": round(6.0 + pct / 100.0 * 2.4, 2), "drill": True}
    bm.ups_events(6.0 + pct / 100.0 * 2.4, pct, hours, True, False)   # volt_ok False: never the real shutdown


# ---- 12: the training night ------------------------------------------------------------------------------------------
TRAIN_SCENES = ["camping", "wald", "garten", "parkplatz", "stellplatz"]


def train_run(manual=False):
    if TRAIN["busy"] or simtask_busy():
        return False, simtask_refuse("training night") or "already running"
    if not sim_ready():
        return False, "only with the simulator"
    TRAIN.update(busy=True, stop=False, step="")
    threading.Thread(target=_train_thread, args=(manual,), daemon=True, name="training").start()
    return True, ""


def _train_thread(manual):
    t0 = time.time()
    res, kept, export = [], [], None
    scenes = [s for s in (CFG.get("train_scenes") or TRAIN_SCENES) if isinstance(s, str)][:5] or TRAIN_SCENES
    try:
        TESTOPT["busy"] = "training"
        for sc in scenes:
            for plan in ("quick", "night"):
                if TRAIN["stop"]:
                    break
                TRAIN["step"] = f"{sc} · {plan}"
                try:
                    sim_control({"action": "scenario", "id": sc})
                except Exception:
                    pass
                time.sleep(4)
                run = _run_free(plan)
                if run is not None:
                    rp = run["report"]
                    res.append({"scene": sc, "plan": plan, "score": run["score"], "rate": rp.get("rate"), "fa": rp.get("false_alarms"),
                                "persons": rp.get("persons"), "found": rp.get("persons_detected")})
        TESTOPT["busy"] = ""
        if CFG.get("train_optimize", True) and res and not TRAIN["stop"]:
            worst = min(res, key=lambda x: x["score"] if x["score"] is not None else 999)
            TRAIN["step"] = "optimizing: " + worst["scene"] + " · " + worst["plan"]
            try:
                sim_control({"action": "scenario", "id": worst["scene"]})
            except Exception:
                pass
            time.sleep(4)
            _testopt_thread("auto", worst["plan"], 3)
            A = TESTOPT.get("auto") or {}
            kept = list(A.get("kept") or [])
            res.append({"scene": worst["scene"], "plan": "optimized", "score": A.get("best"), "base": A.get("base")})
        if CFG.get("train_pics", True) and not TRAIN["stop"]:
            TRAIN["step"] = "training pictures"
            try:
                export = sim_control({"action": "dataset", "op": "export", "n": 300})
            except Exception:
                export = None
    except Exception as e:
        log_event("sys", f"Training night: {e}"[:150])
    finally:
        TESTOPT["busy"] = ""
    rep = {"t": t0, "min": round((time.time() - t0) / 60.0, 1), "results": res, "kept": kept, "manual": manual, "stopped": TRAIN["stop"],
           "pics": (export or {}).get("n") if isinstance(export, dict) else None, "path": (export or {}).get("zip") if isinstance(export, dict) else None}
    TRAIN.update(busy=False, step="", last=rep)
    try:
        d = os.path.join(DATA_DIR, "training")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, datetime.now().strftime("%Y%m%d_%H%M") + ".json"), "w", encoding="utf-8") as f:
            json.dump(rep, f)
    except OSError:
        pass
    sc = [r["score"] for r in res if r.get("score") is not None and r["plan"] != "optimized"]
    txt = trf("Training night: {n} test runs, average score {s}, kept changes: {k}", n=len(sc), s=round(sum(sc) / len(sc)) if sc else "–",
              k=", ".join(kept) or tr("none"))
    log_event("sys", txt)
    w = WATCH_REF.get("w")
    if w is not None and not manual:
        w.notifier.info(txt, title="{name}: " + tr("Training night"))


def train_loop():
    while True:
        time.sleep(60)
        try:
            if not CFG.get("train_night_on") or TRAIN["busy"]:
                continue
            now = datetime.now(); day = now.strftime("%Y-%m-%d")
            if now.hour != int(CFG.get("train_hour", 1)) or TRAIN["day"] == day or CFG.get("train_day") == day:
                continue
            if not sim_ready() or is_armed() or simtask_busy():
                continue
            TRAIN["day"] = day
            CFG["train_day"] = day
            save_settings()
            train_run(False)
        except Exception as e:
            log_event("sys", f"Training night: {e}"[:150])


threading.Thread(target=train_loop, daemon=True, name="training-night").start()


# ---- 13: A/B -----------------------------------------------------------------------------------------------------------
def ab_run(preset, plan="quick"):
    if ABT["busy"] or simtask_busy():
        return False, simtask_refuse("A/B comparison") or "already running"
    if preset not in AB_PRESETS:
        return False, "unknown"
    if not sim_ready():
        return False, "only with the simulator"
    ABT.update(busy=True, step="A")
    threading.Thread(target=_ab_thread, args=(preset, plan), daemon=True, name="ab").start()
    return True, ""


def _sim_free(max_s=420):
    """wait until no test run is going on in the simulator (its test bench may have started one by itself)"""
    t_end = time.time() + max_s
    while time.time() < t_end and not TRAIN["stop"]:
        st = _simtest("test_report")
        if not st.get("running"):
            return True
        time.sleep(5)
    return False


def _run_free(plan):
    _sim_free()
    return testopt_run(plan)


def _ab_changes(preset):
    out = []
    for k, d in AB_PRESETS[preset][1].items():
        if k not in CFG:
            continue
        v = CFG[k]
        nv = v * (1 + d) if k == "min_area" else v + d
        out.append([k, v, _clampv(k, nv)])
    return out


def _ab_thread(preset, plan):
    res = {"preset": preset, "title": AB_PRESETS[preset][0], "plan": plan, "a": None, "b": None, "winner": "", "changes": {}}
    try:
        TESTOPT["busy"] = "ab"
        a = _run_free(plan)
        res["a"] = a["score"] if a else None
        ch = _ab_changes(preset)
        res["changes"] = {k: n for k, _o, n in ch}
        if res["a"] is None:
            raise RuntimeError(TESTOPT.get("msg") or "test run A failed")
        ABT["step"] = "B"
        before = opt_apply(ch, "A/B test " + preset)
        b = _run_free(plan)
        res["b"] = b["score"] if b else None
        if res["a"] is not None and res["b"] is not None and res["b"] >= res["a"] + 3.0:
            res["winner"] = "B"
            TESTOPT["undo"] = {"cfg": before, "t": time.time(), "what": "ab"}
            testopt_save()
        else:
            res["winner"] = "A"
            opt_restore(before, "A/B test: A stays")
    except Exception as e:
        res["error"] = str(e)[:100]
    finally:
        TESTOPT["busy"] = ""
        ABT.update(busy=False, step="", last=res)
        log_event("sys", f"A/B test {preset}: A {res['a']} / B {res['b']} -> {res['winner'] or '?'}")


def lab_state():
    return {"sandbox": bool(CFG.get("notify_sandbox")), "inbox": SANDBOX["items"][:12], "drill": {"kind": DRILL["kind"], "busy": DRILL["busy"],
            "left": max(0, int(DRILL["until"] - time.time())) if DRILL["busy"] else 0, "last": DRILL["last"]},
            "train": {"on": bool(CFG.get("train_night_on")), "hour": int(CFG.get("train_hour", 1)), "busy": TRAIN["busy"], "step": TRAIN["step"],
                      "last": TRAIN["last"]}, "ab": {"busy": ABT["busy"], "step": ABT["step"], "last": ABT["last"],
                      "presets": [[k, v[0]] for k, v in AB_PRESETS.items()]}, "ready": bool(sim_ready())}
