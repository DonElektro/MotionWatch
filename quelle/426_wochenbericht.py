#@ MoveEye – Teil 426: Wochenbericht der Erkennung – einmal pro Woche ein Push mit dem Trend und einem Tipp. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Wunsch Daniel): einmal pro Woche (Einstellung Tag + Stunde, Standard Sonntag 18:00) eine Push-Nachricht: wie gut
# erkennt MoveEye – mit dem, was MoveEye selber hat (pruefstand/VERLAUF.md gibt es nur im Repository, nicht auf dem Pi):
#   · die eigenen Testläufe im Simulator (310, TESTOPT["runs"]): Punkte, gefundene Personen, Fehlalarme – diese / letzte Woche
#   · die echten Aufnahmen: wie viele, wie viele als «Fehlalarm» markiert (mit Ursache) – diese / letzte Woche
#   · die Alarm-Nachrichten (065)
#   · im Simulator-Tagebuch (355) verpasste Personen (im Bild, aber nicht erkannt)
#   · dazu ein Tipp, der zur Woche passt.
# Auch zu sehen: Verlauf → Zeitleiste (Karte «Wochenbericht») und im Fenster (Zeitleiste).
# 2.98.15: der frühere Montags-Push «Woche im Simulator» (142) ist hier drin (Besuche, Tiere) – eine Nachricht pro Woche;
# Einstellung weekrep_sim («mit der Woche im Simulator», übernommen aus simweek_on, 577).
# ----------------------------------------------------------------------------
WEEKREP = {"last": None}
WEEKDAYS_EN = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_WR_ALARM_EV = ("person", "tamper", "warm", "noise")
WR_CAUSES = {"animal": "Animal", "wind": "Wind / branches", "light": "Light / shadow", "rain": "Rain", "car": "Car", "other": "Other"}  # as in 540


def _wr_recs(a, b):
    """recordings between a and b: (count, false alarms, causes)"""
    n, nf, causes = 0, 0, {}
    try:
        names = os.listdir(rec_dir())
    except OSError:
        names = []
    stems = {}
    for nm in names:
        st_, ext = os.path.splitext(nm)
        if ext.lower() in (".mp4", ".jpg") and REC_NAME_RE.match(nm):
            stems.setdefault(st_, nm if ext.lower() == ".mp4" else stems.get(st_, nm))
    for st_, nm in stems.items():
        dt = parse_stamp(nm)
        if dt is None or not (a <= dt < b):
            continue
        n += 1
        c = _read_sidecar(nm).get("false")
        if c:
            nf += 1; causes[c] = causes.get(c, 0) + 1
    return n, nf, causes


def _wr_tests(a, b):
    runs = [r for r in (TESTOPT.get("runs") or []) if a.timestamp() <= float(r.get("t") or 0) < b.timestamp() and r.get("score") is not None]
    if not runs:
        return {"n": 0}
    rep = [r.get("report") or {} for r in runs]
    pers = sum(int(x.get("persons") or 0) for x in rep); found = sum(int(x.get("persons_detected") or 0) for x in rep)
    return {"n": len(runs), "score": round(sum(float(r["score"]) for r in runs) / len(runs), 1),
            "found": found, "persons": pers, "rate": round(100.0 * found / pers) if pers else None,
            "fa": sum(int(x.get("false_alarms") or 0) for x in rep), "last": runs[-1].get("score"), "mw": runs[-1].get("mw")}


def _wr_sim(a, b):
    try:
        vs = simdiary_read(None, max(1, (datetime.now() - a).days + 2))
    except Exception:
        vs = []
    seen = rec = 0
    miss_kinds = {}
    for v in vs:
        try:
            t = float(v.get("t_in") or 0)
        except (TypeError, ValueError):
            continue
        if not (a.timestamp() <= t < b.timestamp()) or str(v.get("kind")) not in SIM_PERSON_KINDS or float(v.get("vis_s") or 0) < 2:
            continue
        seen += 1
        if v.get("detected"):
            rec += 1
        else:
            k = str(v.get("kind")); miss_kinds[k] = miss_kinds.get(k, 0) + 1
    return {"seen": seen, "rec": rec, "missed": seen - rec, "rate": round(100.0 * rec / seen) if seen else None,
            "miss_kinds": sorted(miss_kinds.items(), key=lambda kv: -kv[1])[:3]}


def _wr_msgs(a, b):
    ta, tb = a.timestamp(), b.timestamp()
    return sum(1 for m in msglog_list(MSGLOG_MAX) if ta <= float(m.get("t") or 0) < tb and m.get("ev") in _WR_ALARM_EV and m.get("status") != "test")


def _wr_trend(cur, prev, better_up=True):
    """↑ / ↓ = the number went up / down, ✓ = that is good, ⚠ = that is worse"""
    if cur is None or prev is None:
        return ""
    d = cur - prev
    if abs(d) < 1e-9:
        return "→"
    return ("↑" if d > 0 else "↓") + (" ✓" if (d > 0) == better_up else " ⚠")


def weekrep_build(lang=None, now=None):
    """the weekly report: numbers of this week and the week before, a trend per line, one tip, the text for the push"""
    L = norm_lang(lang) if lang else cur_lang()
    now = now or datetime.now()
    a = now - timedelta(days=7); p = a - timedelta(days=7)
    T, Tp = _wr_tests(a, now), _wr_tests(p, a)
    R, Rp = _wr_recs(a, now), _wr_recs(p, a)
    S, Sp = _wr_sim(a, now), _wr_sim(p, a)
    M, Mp = _wr_msgs(a, now), _wr_msgs(p, a)
    weeks = []                                                  # test points per week, the last 6 weeks (for a small curve)
    for i in range(5, -1, -1):
        e = now - timedelta(days=7 * i); s = e - timedelta(days=7)
        w = _wr_tests(s, e)
        weeks.append({"wk": s.strftime("%d.%m."), "score": w.get("score"), "n": w.get("n", 0)})
    lines = []
    if T["n"]:
        lines.append(trf("Test runs: {n}, score {s} {tr} (week before {p}), persons found {f} of {a}, false alarms {fa}", L,
                         n=T["n"], s=T["score"], tr=_wr_trend(T["score"], Tp.get("score")), p=Tp.get("score", "–"),
                         f=T["found"], a=T["persons"], fa=T["fa"]))
    else:
        lines.append(tr("Test runs: none this week", L))
    lines.append(trf("Recordings: {n} (week before {p}), marked as false alarm: {f} {tr}", L,
                     n=R[0], p=Rp[0], f=R[1], tr=_wr_trend(R[1], Rp[1], better_up=False)) +
                 ((" (" + ", ".join(f"{tr(WR_CAUSES.get(k, k), L)} {v}" for k, v in sorted(R[2].items(), key=lambda kv: -kv[1])) + ")") if R[2] else ""))
    lines.append(trf("Alarm messages: {n} (week before {p})", L, n=M, p=Mp))
    sim_on = bool(CFG.get("weekrep_sim", True))             # «Wochenbericht: mit der Woche im Simulator» (577, was simweek_on)
    SW = weekrep_simweek(a, now, L) if sim_on else None        # 2.98.15: the former Monday push «week in the simulator» is part of it
    if SW and SW["visits"]:
        lines.append(trf("Week in the simulator: {v} visits. Animals: {an}", L, v=SW["visits"], an=SW["animals"] or "–"))
    if sim_on and S["seen"]:
        lines.append(trf("Simulator diary: persons recognised {r} % ({a} of {b}) {tr}, missed {m}", L,
                         r=S["rate"], a=S["rec"], b=S["seen"], tr=_wr_trend(S["rate"], Sp.get("rate")), m=S["missed"]) +
                     ((" – " + ", ".join(f"{tr_trigger(k, L)} {v}" for k, v in S["miss_kinds"])) if S["miss_kinds"] else ""))
    tip, link = weekrep_tip(L, T, Tp, R, S, now)
    text = "\n".join(lines) + "\n💡 " + tip
    return {"t": now.isoformat(timespec="seconds"), "from": a.strftime("%d.%m."), "to": now.strftime("%d.%m."),
            "tests": T, "tests_prev": Tp, "recs": {"n": R[0], "false": R[1], "causes": R[2]}, "recs_prev": {"n": Rp[0], "false": Rp[1]},
            "msgs": M, "msgs_prev": Mp, "sim": S, "sim_prev": Sp, "simweek": SW, "with_sim": sim_on, "weeks": weeks, "lines": lines, "tip": tip, "link": link, "text": text,
            "on": bool(CFG.get("weekrep_on")), "day": CFG.get("weekrep_day"), "hour": int(CFG.get("weekrep_hour", 18)),
            "last": WEEKREP["last"]}


def weekrep_simweek(a, b, L=None):
    """2.98.15: what the Monday push «Woche im Simulator» (142) said - visits and animals of the simulator diary"""
    try:
        st = simdiary_stats(max(1, (b - a).days))
    except Exception:
        return None
    vis = sum(int(x.get("visits") or 0) for x in st.get("days") or [])
    an = ", ".join(f"{tr_trigger(k['k'], L)} {k['n']}" for k in st.get("kinds") or [] if k.get("animal"))[:120]
    return {"visits": vis, "animals": an}


def weekrep_tip(L, T, Tp, R, S, now):
    """one tip that fits the week (text, address of the page that helps)"""
    if R[1] >= 2:
        try:
            sg = fa_suggestions(L, 7)["suggestions"]
        except Exception:
            sg = []
        if sg:
            return trf("{n} false alarms this week. Suggestion: {s} (History → Recordings → false alarms)", L, n=R[1], s=sg[0]["text"]), "/recordings"
        return trf("{n} false alarms this week. Draw an ignore zone over what moves (trees, road) – tab Protection → Zones.", L, n=R[1]), "/zones"
    if S["missed"] >= 2 and CFG.get("weekrep_sim", True):
        return trf("In the simulator {n} persons were in the picture but not recognised. Run the test «Night» and the automatic optimization (Simulator → Testing).", L, n=S["missed"]), "/sim"
    if T["n"] and Tp.get("score") is not None and T["score"] <= Tp["score"] - 5:
        return tr("The test score went down. Look at what changed in the settings (Simulator → Test runs, «undo»).", L), "/sim"
    if not T["n"]:
        return tr("No test run this week: switch on the nightly test run (Simulator → Testing) – then you see the trend here.", L), "/sim"
    if not R[0]:
        return tr("A quiet week. Check now and then that the camera still looks at the right place (Live).", L), "/"
    tips = ["Mark wrong alarms with «Was nothing» – MoveEye learns from them and suggests better settings.",
            "Star (★) important recordings: they are never deleted automatically.",
            "«Guard tonight» on the tab Protection sets everything for the night in one tap.",
            "The timeline (History → Timeline) shows a whole night at a glance."]
    return tr(tips[int(now.strftime("%V")) % len(tips)], L), "/timeline"


def weekrep_send(manual=False):
    r = weekrep_build()
    w = WATCH_REF.get("w")
    ok = False
    if w is not None and Notifier.configured() and CFG["notify_on"]:
        pub = CFG["public_url"].strip().rstrip("/")
        ok = bool(w.notifier.info(r["text"], pub + "/timeline" if pub else "", title="{name}: " + tr("Weekly detection report")))
    WEEKREP["last"] = {"t": datetime.now().isoformat(timespec="seconds"), "sent": ok, "manual": manual}
    log_event("sys", ("Weekly detection report sent" if ok else "Weekly detection report not sent (no push channel)") + (" (by hand)" if manual else ""))
    return r, ok


def weekrep_due(now):
    if not CFG.get("weekrep_on"):
        return False
    day = CFG.get("weekrep_day") if CFG.get("weekrep_day") in WEEKDAYS_EN else "Sunday"
    if now.weekday() != WEEKDAYS_EN.index(day) or now.hour < int(CFG.get("weekrep_hour", 18)) or now.hour > int(CFG.get("weekrep_hour", 18)) + 3:
        return False                                       # also up to 3 h late (the Pi was off at the hour)
    return CFG.get("weekrep_last") != now.strftime("%G-W%V")


def weekrep_loop():
    while True:
        time.sleep(60)
        try:
            now = datetime.now()
            if weekrep_due(now):
                CFG["weekrep_last"] = now.strftime("%G-W%V")
                save_settings()
                weekrep_send()
        except Exception as e:
            log_event("sys", f"Weekly detection report: {e}"[:150])


threading.Thread(target=weekrep_loop, daemon=True, name="weekrep").start()


def verlauf_selftest():
    """--self-test: night window, timeline and weekly report build (with whatever data there is), face pixelation"""
    a, b = timeline_window("2026-03-05", "night")
    assert (a.hour, b.hour, (b - a).total_seconds()) == (18, 9, 15 * 3600), "night 18:00-09:00"
    a, b = timeline_window("2026-03-29", "day")
    assert a.day == 29 and b.day == 30
    tl = timeline_build(None, "night", "de")
    assert tl["ok"] and isinstance(tl["items"], list)
    timeline_text(tl, "fr")
    wr = weekrep_build("it")
    assert wr["tip"] and wr["text"] and len(wr["weeks"]) == 6
    return faceblur_selftest()
