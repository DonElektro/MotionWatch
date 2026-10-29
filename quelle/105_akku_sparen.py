#@ MoveEye – Teil 105: Akku-Sparen automatisch (unter einer Schwelle weniger Bilder, die KI seltener). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Wunsch Daniel): the battery gets low (below batt_save_pct, default 25 %) - MoveEye saves by itself:
#   - the power saving (eco_on, part 410 _eco) is switched on, if it was off (and off again afterwards),
#   - at most batt_save_fps pictures per second also while something moves (twice that while a person is seen),
#   - the AI looks only half as often (ai_every x 2, the pause between two AI runs x 2).
# Back to normal when the battery charges (UPS HAT) or the charge is 5 % above the threshold again. One line in the log
# and one info push. Shown on the Schutz page (beside «Power saving») and in the battery display (web and window).
# ----------------------------------------------------------------------------
for _k, _v in {"batt_save_on": True, "batt_save_pct": 25, "batt_save_fps": 3, "batt_save_eco": False, "cam_vfov": 41.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
BATT_SAVE = {"on": False, "since": 0.0, "pct": None, "push_t": 0.0, "why": ""}


def batt_save_active():
    return bool(BATT_SAVE["on"])


def batt_save_ai_k():
    """factor for the AI: 2 while the battery saver runs (ai_every and the pause between two AI runs)"""
    return 2 if BATT_SAVE["on"] else 1


def batt_save_state():
    b = STATE.get("battery") or {}
    return {"on": bool(BATT_SAVE["on"]), "enabled": bool(CFG.get("batt_save_on")), "pct": b.get("pct"), "thr": int(CFG.get("batt_save_pct") or 25),
            "fps": int(CFG.get("batt_save_fps") or 3), "since": int(BATT_SAVE["since"]) if BATT_SAVE["on"] else 0,
            "eco_by_us": bool(CFG.get("batt_save_eco"))}


def batt_save_text(lang=None):
    """one line for the Schutz page / the battery display"""
    s = batt_save_state()
    if not s["enabled"]:
        return tr("Battery saver off", lang)
    if s["on"]:
        return trf("Battery saver active: {pct} % (below {thr} %) - at most {fps} pictures per second, the AI less often", lang,
                   pct=s["pct"] if s["pct"] is not None else "?", thr=s["thr"], fps=s["fps"])
    return trf("Battery saver: below {thr} % fewer pictures and the AI less often", lang, thr=s["thr"])


def _batt_save_set(on, pct, why):
    if on == BATT_SAVE["on"]:
        return
    BATT_SAVE.update(on=on, since=time.time() if on else 0.0, pct=pct, why=why)
    STATE["batt_save"] = batt_save_state()
    if on:
        if not CFG.get("eco_on"):
            CFG["eco_on"] = True; CFG["batt_save_eco"] = True       # switched on by the battery saver - and off again later
        save_settings()
        log_event("sys", f"Battery saver ON: battery {pct} % (below {CFG['batt_save_pct']} %) - fewer pictures, AI less often")
        w = WATCH_REF.get("w")
        if w is not None and time.time() - BATT_SAVE["push_t"] > 6 * 3600:
            BATT_SAVE["push_t"] = time.time()
            try:
                w.notifier.info(trf("Battery {pct} %: the battery saver is on - fewer pictures per second, the AI less often. Back to normal when charging.", pct=pct),
                                title="{name}: " + tr("battery saver"))
            except Exception:
                pass
    else:
        if CFG.get("batt_save_eco"):
            CFG["batt_save_eco"] = False
            CFG["eco_on"] = False
        save_settings()
        log_event("sys", f"Battery saver OFF ({why}) - normal speed again")


def batt_save_tick():
    b = STATE.get("battery") or {}
    pct = b.get("pct")
    if not CFG.get("batt_save_on") or not b.get("on") or pct is None:
        _batt_save_set(False, pct, "switched off" if not CFG.get("batt_save_on") else "no battery value")
    else:
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            return
        thr = float(CFG.get("batt_save_pct") or 25)
        charging = bool(b.get("charging")) or (b.get("src") == "ups" and b.get("on_battery") is False)
        if not BATT_SAVE["on"] and not charging and pct < thr:
            _batt_save_set(True, int(round(pct)), "low")
        elif BATT_SAVE["on"] and (charging or pct >= thr + 5):
            _batt_save_set(False, int(round(pct)), "charging" if charging else f"battery {int(round(pct))} %")
    if not BATT_SAVE["on"] and CFG.get("batt_save_eco"):      # restarted while the saver had switched on power saving
        CFG["batt_save_eco"] = False; CFG["eco_on"] = False; save_settings()
    STATE["batt_save"] = batt_save_state()


def batt_save_loop():
    time.sleep(15)
    while True:
        try:
            batt_save_tick()
        except Exception as e:
            log_event("sys", f"Battery saver: {e}"[:160])
        time.sleep(10)


def batt_save_pace(watch, t0, present):
    """called once per picture by the camera loop: keep the frame rate at most at batt_save_fps (x 2 while a person is seen).
    The power saving of part 410 (eco) slows down further while all is quiet."""
    if not BATT_SAVE.get("loop"):
        BATT_SAVE["loop"] = True                                # the check runs once the camera loop runs (not in the self-test)
        threading.Thread(target=batt_save_loop, daemon=True, name="battsave").start()
    if not BATT_SAVE["on"] or watch.eco_slow:
        return
    f = max(1.0, float(CFG.get("batt_save_fps") or 3)) * (2.0 if "person" in present else 1.0)
    end = t0 + 1.0 / f
    while time.time() < end:
        if manual_active():
            break                                               # somebody steers the camera by hand: answer at once
        time.sleep(0.03)


STATE["batt_save"] = batt_save_state()
