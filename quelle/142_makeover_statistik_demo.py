#@ MoveEye – Teil 142: Makeover – mehrere Geräte, Rover, Statistik aus dem Simulator, Versionen-Kurve, Ein-Klick-Demo. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.7 (Makeover-Punkte 16–20):
#  16  Mehrere Geräte: das zweite Gerät im Simulator bewacht Zelt / Velo / Auto; Übergabe zwischen Geräten (260).
#  17  Rover: Patrouille, Ladestation mit Akku, «zum Alarm fahren» - von Hand oder von selbst bei einem Personen-Alarm.
#  18  Statistik: die Besuche im Simulator über 4 Wochen - pro Tag, pro Art, Erkennungsrate; Wochenbericht als Push.
#  19  Versionen vergleichen: Erkennungsrate (Simulator-Tagebuch) und Testlauf-Punkte pro MoveEye-Version als Kurve.
#  20  Ein-Klick-Demo: «Zeig mir MoveEye» - 3 Minuten Vorführung im Kino-Modus (Tag, Person, Nacht, Fuchs, Dieb, Alarm).
# ----------------------------------------------------------------------------
SIM_PERSON_KINDS = {"person", "child", "jogger", "burglar", "thief", "drunk", "courier", "police", "cyclist", "couple", "dogwalk",
                    "sneaker", "stroller", "garden_person", "homecoming", "parcel", "bbq", "kids_tag"}
SIM_ANIMAL_KINDS = {"fox", "deer", "boar", "cat", "dog", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "cow", "sheep",
                    "horse", "chamois", "ibex", "lynx", "herd", "owl", "bats", "cows", "sheep_flock", "horse_walk", "boar_group"}


# ---- 17: the rover ---------------------------------------------------------------------------------------------------
_ROVER = {"t": 0.0}


def rover_on_alarm(kind):
    """a person alarm (armed, simulator): the rover drives there by itself (when switched on)"""
    if kind != "person" or not CFG.get("rover_alarm") or not CFG.get("sim_on") or not is_armed():
        return
    if time.time() - _ROVER["t"] < 60:
        return
    _ROVER["t"] = time.time()
    def go():
        try:
            sim_control({"action": "rover", "do": "alarm"})
            log_event("sys", "Rover drives to the alarm")
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()


# ---- 18 / 19: statistics -----------------------------------------------------------------------------------------------
def simdiary_stats(days=28):
    vs = simdiary_read(None, days)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    D = {}
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        D[d] = {"d": d, "visits": 0, "persons": 0, "seen": 0, "rec": 0, "animals": 0}
    kinds, vers = {}, {}
    for v in vs:
        try:
            d = datetime.fromtimestamp(float(v.get("t_in") or 0)).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            continue
        k = str(v.get("kind") or "?")
        x = D.get(d)
        if x is None:
            continue
        x["visits"] += 1
        kinds[k] = kinds.get(k, 0) + 1
        if k in SIM_ANIMAL_KINDS:
            x["animals"] += 1
        if k in SIM_PERSON_KINDS:
            x["persons"] += 1
            good = float(v.get("vis_s") or 0) >= 2.0
            if good:
                x["seen"] += 1
                if v.get("detected"):
                    x["rec"] += 1
                ver = str(v.get("mw_version") or "?")
                y = vers.setdefault(ver, {"v": ver, "seen": 0, "rec": 0, "lat": []})
                y["seen"] += 1
                if v.get("detected"):
                    y["rec"] += 1
                    if float(v.get("detect_s") or -1) >= 0:
                        y["lat"].append(float(v["detect_s"]))
    for x in D.values():
        x["rate"] = round(100.0 * x["rec"] / x["seen"]) if x["seen"] else None
    tests = {}
    for r in TESTOPT.get("runs") or []:
        if r.get("score") is None:
            continue
        t_ = tests.setdefault(str(r.get("mw") or "?"), {"sum": 0.0, "n": 0})
        t_["sum"] += float(r["score"]); t_["n"] += 1
    allv = set(vers) | set(tests)
    out_v = []
    for ver in sorted(allv, key=lambda s: tuple(int(p) if p.isdigit() else 0 for p in s.split("."))):
        y = vers.get(ver, {"seen": 0, "rec": 0, "lat": []})
        t_ = tests.get(ver)
        out_v.append({"v": ver, "seen": y["seen"], "rate": round(100.0 * y["rec"] / y["seen"]) if y["seen"] else None,
                      "lat": round(sum(y["lat"]) / len(y["lat"]), 1) if y["lat"] else None,
                      "score": round(t_["sum"] / t_["n"]) if t_ else None, "tests": t_["n"] if t_ else 0})
    top = sorted(kinds.items(), key=lambda kv: -kv[1])[:12]
    return {"days": list(D.values()), "kinds": [{"k": k, "n": n, "animal": k in SIM_ANIMAL_KINDS, "person": k in SIM_PERSON_KINDS} for k, n in top],
            "versions": out_v[-10:], "total": len(vs)}


def simweek_loop():
    """Monday, at the hour of the night report: the week in the simulator as a push (when switched on)"""
    while True:
        time.sleep(60)                                     # 2.98.1: every minute (it must be ready before the night report)
        try:
            if not CFG.get("simweek_on"):
                continue
            now = datetime.now()
            wk = now.strftime("%G-W%V")
            if now.weekday() != 0 or now.hour < int(CFG.get("report_hour", 7)) or CFG.get("simweek_last") == wk:
                continue
            CFG["simweek_last"] = wk
            save_settings()
            st = simdiary_stats(7)
            vis = sum(x["visits"] for x in st["days"])
            if not vis:
                continue
            seen = sum(x["seen"] for x in st["days"]); rec = sum(x["rec"] for x in st["days"])
            an = ", ".join(f"{k['k']} {k['n']}" for k in st["kinds"] if k["animal"])[:120]
            txt = trf("Week in the simulator: {v} visits, persons recognised {r} % ({a} of {b}). Animals: {an}",
                      v=vis, r=round(100 * rec / seen) if seen else "–", a=rec, b=seen, an=an or "–")
            w = WATCH_REF.get("w")
            if w is not None and not morning_add("🧪 " + txt):   # 2.98.1: with the night report when it is on
                w.notifier.info(txt, title="{name}: " + tr("Simulator diary"))
        except Exception as e:
            log_event("sys", f"Week report: {e}"[:120])


threading.Thread(target=simweek_loop, daemon=True, name="simweek").start()


# ---- 20: the one-click demo ------------------------------------------------------------------------------------------
DEMO_RUN = {"busy": False, "step": "", "i": 0, "n": 0, "t": 0.0, "stop": False}
DEMO_STEPS = [
    (12, "Welcome to MoveEye – a camera that watches and thinks", [{"action": "scenario", "id": "camping"}, {"action": "set", "id": "hour", "value": 15}, {"action": "set", "id": "weather", "value": "clear"}]),
    (18, "Day: a person walks past – MoveEye notices it", [{"action": "press", "id": "spawn_person"}]),
    (25, "Animals are not a person: a fox comes by", [{"action": "press", "id": "spawn_fox"}]),
    (25, "Evening falls – MoveEye switches to night vision", [{"action": "set", "id": "hour", "value": 21.5}]),
    (20, "At night: somebody creeps to the bike", [{"action": "press", "id": "thief"}]),
    (30, "Alarm: light, push message – and the siren if nobody switches off", []),
    (25, "Rain: the filters keep false alarms away", [{"action": "set", "id": "weather", "value": "rain"}, {"action": "press", "id": "spawn_deer"}]),
    (25, "Morning: the night report and the diary say what happened", [{"action": "set", "id": "hour", "value": 7}, {"action": "set", "id": "weather", "value": "clear"}]),
    (12, "That was MoveEye. Thank you!", []),
]


def demo_start():
    if DEMO_RUN["busy"]:
        return False, "the demo is already running"
    if simtask_busy("demo"):
        return False, simtask_refuse("demo")
    if CFG["armed"] and not CFG.get("sim_on"):
        return False, "MoveEye is armed - disarm it first (the demo uses the simulator instead of the real camera)"
    if not CFG.get("sim_on") or not SIM.get("ok"):
        try:
            if not SIM.get("ok") and simpi_possible() and sim3d_ready("pi"):
                simpi_start("demo")                        # on the Pi: start the simulator first
                sim_set(True, "demo")
        except Exception:
            pass
        if not CFG.get("sim_on"):
            return False, "start the simulator first (tab Simulator)"
    DEMO_RUN.update(busy=True, step="", i=0, n=len(DEMO_STEPS), t=time.time(), stop=False)
    threading.Thread(target=_demo_thread, daemon=True, name="demo").start()
    return True, ""


def _demo_thread():
    SANDBOX["force"] += 1                                # nobody's phone rings during the demo
    try:
        for _ in range(60):                               # the simulator must answer (it may just have started)
            if SIM.get("ok") or DEMO_RUN["stop"]:
                break
            time.sleep(1)
        for i, (wait, text, acts) in enumerate(DEMO_STEPS):
            if DEMO_RUN["stop"]:
                break
            DEMO_RUN.update(i=i + 1, step=text)
            for a in acts:
                try:
                    sim_control(a)
                except Exception:
                    pass
            if i == 5:
                light_alarm()
            t_end = time.time() + wait
            while time.time() < t_end and not DEMO_RUN["stop"]:
                time.sleep(0.5)
    finally:
        SANDBOX["force"] = max(0, SANDBOX["force"] - 1)
        DEMO_RUN.update(busy=False, step="", i=0)
        log_event("sys", "Demo finished")
