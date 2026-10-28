#@ MoveEye – Teil 355: Simulator-Tagebuch (alle Besuche im Simulator, Auswertung). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.1: the simulator (3D-3.80) logs every visitor from coming to going; MoveEye fetches the finished visits every 30 s
# (control action «visits») and keeps them in sim_diary.jsonl (the last 5000). The diary page has a tab «Simulator»:
# visits, recognised in %, time until recognised, missed ones - by kind, light, posture.
# ----------------------------------------------------------------------------
SIMDIARY = {"seen": 0, "t": 0.0, "lock": threading.Lock(), "n": 0}
def simdiary_file():
    return os.path.join(DATA_DIR, "sim_diary.jsonl")     # DATA_DIR may change at the start (--config)


def simdiary_poll():
    """called by the simulator link loop; quietly does nothing with an older simulator"""
    if not SIM.get("ok"):
        return
    SIMDIARY["t"] = time.time()
    try:
        r = sim_control({"action": "visits", "since": SIMDIARY["seen"]})
    except Exception:
        return
    if not isinstance(r, dict) or "visits" not in r:
        return
    if int(r.get("seq") or 0) < SIMDIARY["seen"]:          # the simulator started again: its numbers start at 1
        SIMDIARY["seen"] = 0
        return
    vs = [v for v in (r.get("visits") or []) if isinstance(v, dict)]
    if not vs:
        return
    with SIMDIARY["lock"]:
        with open(simdiary_file(), "a", encoding="utf-8") as f:
            for v in vs:
                v["mw_version"] = APP_VERSION
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
        SIMDIARY["seen"] = max(int(v.get("id", 0)) for v in vs)
        SIMDIARY["n"] += len(vs)
        if SIMDIARY["n"] > 500:                            # now and then: keep the last 5000
            SIMDIARY["n"] = 0
            try:
                with open(simdiary_file(), encoding="utf-8") as f:
                    lines = f.readlines()
                if len(lines) > 5000:
                    with open(simdiary_file(), "w", encoding="utf-8") as f:
                        f.writelines(lines[-5000:])
            except OSError:
                pass


def simdiary_read(day=None, days=1):
    """the visits of a day (YYYY-MM-DD, local time) and the days before it"""
    out = []
    try:
        end = datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1) if day else datetime.now() + timedelta(days=1)
    except ValueError:
        end = datetime.now() + timedelta(days=1)
    end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=max(1, min(31, int(days))))
    a, b = start.timestamp(), end.timestamp()
    try:
        with SIMDIARY["lock"], open(simdiary_file(), encoding="utf-8") as f:
            for line in f:
                try:
                    v = json.loads(line)
                except ValueError:
                    continue
                if a <= float(v.get("t_in", 0)) < b:
                    out.append(v)
    except OSError:
        pass
    return out


def simdiary_days():
    """the days with visits (for the date picker): {day: count}"""
    d = {}
    try:
        with open(simdiary_file(), encoding="utf-8") as f:
            for line in f:
                try:
                    t = float(json.loads(line).get("t_in", 0))
                except (ValueError, AttributeError):
                    continue
                k = datetime.fromtimestamp(t).strftime("%Y-%m-%d")
                d[k] = d.get(k, 0) + 1
    except OSError:
        pass
    return d
