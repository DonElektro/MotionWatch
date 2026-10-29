#@ MoveEye – Teil 577: Nachlauf zum Konzept-Check – ein Wochenbericht, Rückkehr des Handys, Akku-Schwellen zusammen, Auto-Tuner begrenzt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.15 (Wunsch Daniel, Vorschläge aus dem Konzept-Check von 2.98.14):
#   1 Eine Nachricht pro Woche: der Montags-Push «Woche im Simulator» (142, simweek_on) steckt jetzt im Wochenbericht (426).
#     Einstellung weekrep_sim («mit der Woche im Simulator»), übernommen aus simweek_on.
#   4 Akku: die Schwelle des Akku-Sparens (batt_save_pct, 105) und die der Lagerfeuer-Spiele (mode_fire_min_pct, 130) stehen
#     zusammen im Abschnitt «Akku» (Web und Fenster lesen dieselben Listen).
#   5 Rückkehr des Handys: EINE Wahl presence_back = off (Schutz ausschalten) / ask («Bist du's?», 066) / none (nichts) statt
#     zwei Schaltern (presence_auto schaltete beim Zurückkommen aus, back_ask fragte). presence_auto heisst jetzt nur noch
#     «automatisch an, wenn mein Handy weg ist». Übernahme der alten Werte: presence_auto → off, sonst back_ask → ask, sonst none.
#   6 Auto-Tuner (190): min_area / sensitivity / speed_consistency höchstens ±20 % um die gemessenen Werte (Kalibrierung oder
#     Assistent «Erkennung verbessern», 312). Der Optimierer schaltet den Tuner nicht mehr (OPT_KEYS, 310).
# Hier statt in den grossen Listen von 570, damit dort nichts verschoben wird.
# ----------------------------------------------------------------------------
for _k, _v in {"weekrep_sim": True, "presence_back": "ask", "auto_tune_base": {}}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

PRESENCE_BACK = (("off", "switch the protection off"), ("ask", "ask «Is it you?» (person alarms wait)"), ("none", "nothing (the protection stays on)"))
PRESENCE_BACK_KEYS = tuple(k for k, _l in PRESENCE_BACK)
AUTOTUNE_KEYS = ("min_area", "sensitivity", "speed_consistency")
AUTOTUNE_SPAN = 0.20
AUTOTUNE_LAST = {}                                          # the value the tuner set last (to see a change by hand)


def presence_back_mode():
    v = CFG.get("presence_back")
    return v if v in PRESENCE_BACK_KEYS else "ask"


def _nl_put_after(lst, after_key, item, idx=1):
    """item into a settings list right after the entry with this key (else at the end); an entry with the same key is replaced"""
    lst[:] = [x for x in lst if x[idx] != item[idx]]
    for i, x in enumerate(lst):
        if x[idx] == after_key:
            lst.insert(i + 1, item)
            return
    lst.append(item)


# ---- the settings lists (web and window) ---------------------------------------------------------------------------------
_nl_put_after(TOGGLES, "weekrep_on", ("Night report", "weekrep_sim", "Weekly report: with the week in the simulator (visits, animals, recognised persons)"))
_nl_put_after(TOGGLES, "back_ask", ("Camping / protection", "presence_auto", "Protection on automatically when my phone is gone (choose the phone: Tools → Am I at home?)"))
TOGGLES[:] = [x for x in TOGGLES if x[1] not in ("simweek_on", "back_ask")]
for _i, _x in enumerate(SLIDERS):
    if _x[1] == "batt_save_pct":
        SLIDERS[_i] = ("Battery", "batt_save_pct", "🐢 Battery saver below (% battery): fewer pictures, the AI less often - normal again at +5 % or when charging", _x[3], _x[4], _x[5])
_nl_put_after(SLIDERS, "batt_save_pct", ("Battery", "mode_fire_min_pct", "🔥 Campfire games end below (% battery): back to the camping guard (0 = never)", 0, 50, 10))
_nl_put_after(TEXTS, "", ("Camping / protection", "presence_back", "When my phone comes back", "enum", "presence_back"))
TEXT_SPECS["presence_back"] = ("enum", "presence_back")
SIMPLE_KEYS.update({"weekrep_sim", "mode_fire_min_pct", "presence_back", "presence_auto"})

_text_choice_pairs_before_nl = text_choice_pairs


def text_choice_pairs(key):                                 # 2.98.15: + the choice at the return of the phone
    if TEXT_SPECS.get(key, (None, None))[1] == "presence_back":
        return [(k, tr(l)) for k, l in PRESENCE_BACK]
    return _text_choice_pairs_before_nl(key)


# ---- tools page «Am I at home?» (300) ---------------------------------------------------------------------------------------
_tools_state_before_nl = tools_state
_tools_cfg_before_nl = tools_cfg


def tools_state():
    r = _tools_state_before_nl()
    try:
        r["cfg"]["presence_back"] = presence_back_mode()
    except (KeyError, TypeError):
        pass
    return r


def tools_cfg(key, value, mac=None):
    if key == "presence_back":
        if value not in PRESENCE_BACK_KEYS:
            return False, "invalid value"
        CFG["presence_back"] = value
        save_settings()
        return True, ""
    return _tools_cfg_before_nl(key, value, mac)


# ---- the auto-tuner: ±20 % around the measured values -----------------------------------------------------------------------
def autotune_base_set(src):
    """src = «calibration» (the tuner itself, 190) or «assistant» (312): the values now are the middle of the allowed range.
    The calibration does not replace values measured by the assistant."""
    b = CFG.get("auto_tune_base") if isinstance(CFG.get("auto_tune_base"), dict) else {}
    if src == "calibration" and str(b.get("src", "")).startswith("assistant") and all(k in b for k in AUTOTUNE_KEYS):
        return b
    nb = {k: float(CFG[k]) for k in AUTOTUNE_KEYS if k in CFG}
    nb.update(src=src, t=int(time.time()))
    CFG["auto_tune_base"] = nb
    AUTOTUNE_LAST.clear()
    log_event("auto", f"Auto-tune: base from the {src} - " + ", ".join(f"{k} {nb[k]:g}" for k in AUTOTUNE_KEYS if k in nb) + " (±20 %)")
    return nb


def autotune_base_reset():
    """the tuner starts again (190, reset): a new calibration measures freely - values of the assistant stay the middle"""
    b = CFG.get("auto_tune_base") if isinstance(CFG.get("auto_tune_base"), dict) else {}
    if not str(b.get("src", "")).startswith("assistant"):
        CFG["auto_tune_base"] = {}
    AUTOTUNE_LAST.clear()


def autotune_clamp(key, value):
    """the value the tuner may set: at most ±20 % around the base. Changed by hand outside the band = that is the new base."""
    if key not in AUTOTUNE_KEYS:
        return value
    b = CFG.get("auto_tune_base") if isinstance(CFG.get("auto_tune_base"), dict) else {}
    try:
        mid = float(b[key])
    except (KeyError, TypeError, ValueError):
        return value
    cur = float(CFG.get(key, mid))
    lo, hi = mid * (1 - AUTOTUNE_SPAN), mid * (1 + AUTOTUNE_SPAN)
    if not (lo - 1e-6 <= cur <= hi + 1e-6) and AUTOTUNE_LAST.get(key) != CFG.get(key):
        b = dict(b, **{key: cur, "src": b.get("src", "") + "+hand"}); CFG["auto_tune_base"] = b      # set by hand / by a test
        mid = cur; lo, hi = mid * (1 - AUTOTUNE_SPAN), mid * (1 + AUTOTUNE_SPAN)
    v = max(lo, min(hi, float(value)))
    AUTOTUNE_LAST[key] = round(v, 2) if isinstance(CFG.get(key), float) else int(v)
    return v


_tunea_autotune_base_before_nl = _tunea_autotune_base


def _tunea_autotune_base():                                # 312: after «Erkennung verbessern» (and its «undo») = the new middle
    _tunea_autotune_base_before_nl()
    try:
        autotune_base_set("assistant")
    except Exception as e:
        log_event("sys", f"Auto-tune base: {e}"[:120])


# ---- taking over the settings of 2.98.14 and older ----------------------------------------------------------------------------
def nachlauf_migrate(cfg_in):
    """cfg_in = the «cfg» of the loaded / imported file; returns the list of what was taken over"""
    did = []
    if not isinstance(cfg_in, dict):
        return did
    if "weekrep_sim" not in cfg_in and isinstance(cfg_in.get("simweek_on"), bool):
        CFG["weekrep_sim"] = cfg_in["simweek_on"]
        did.append(f"simulator week push -> weekly report ({'with' if CFG['weekrep_sim'] else 'without'} simulator)")
    if "presence_back" not in cfg_in and ("presence_auto" in cfg_in or "back_ask" in cfg_in):
        CFG["presence_back"] = "off" if cfg_in.get("presence_auto") is True else ("ask" if cfg_in.get("back_ask") is True else "none")
        did.append(f"return of the phone -> {CFG['presence_back']}")
    if CFG.get("presence_back") not in PRESENCE_BACK_KEYS:
        CFG["presence_back"] = "ask"
    if not isinstance(CFG.get("auto_tune_base"), dict):
        CFG["auto_tune_base"] = {}
    return did


_apply_settings_before_nl = apply_settings


def apply_settings(data):                                   # 2.98.15: the same as before, then the migration above
    r = _apply_settings_before_nl(data)
    try:
        did = nachlauf_migrate(data.get("cfg") if isinstance(data, dict) else None)
        if did:
            log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
    except Exception as e:
        log_event("sys", f"Settings migration (577): {e}"[:150])
    return r


def nachlauf_selftest():
    """--self-test: the migrations, the ±20 % of the auto-tuner, the one weekly report"""
    keep = {k: CFG.get(k) for k in ("weekrep_sim", "presence_back", "auto_tune_base", "min_area", "sensitivity", "speed_consistency")}
    try:
        for old, want in (({"presence_auto": True, "back_ask": True}, "off"), ({"presence_auto": False, "back_ask": True}, "ask"),
                          ({"presence_auto": False, "back_ask": False}, "none"), ({"presence_auto": False}, "none")):
            CFG["presence_back"] = "ask"
            nachlauf_migrate(old)
            assert CFG["presence_back"] == want, f"presence {old} -> {CFG['presence_back']}"
        CFG["presence_back"] = "none"; nachlauf_migrate({"presence_back": "none", "presence_auto": True})
        assert CFG["presence_back"] == "none", "a new file is not migrated again"
        CFG["weekrep_sim"] = True; nachlauf_migrate({"simweek_on": False}); assert CFG["weekrep_sim"] is False
        CFG["weekrep_sim"] = True; nachlauf_migrate({"simweek_on": False, "weekrep_sim": True}); assert CFG["weekrep_sim"] is True
        assert dict(text_choice_pairs("presence_back")).keys() == set(PRESENCE_BACK_KEYS)
        assert not any(x[1] in ("simweek_on", "back_ask") for x in TOGGLES) and "auto_tune" not in OPT_KEYS
        ks = [x[1] for x in SLIDERS if x[0] == "Battery"]
        assert ks.index("mode_fire_min_pct") == ks.index("batt_save_pct") + 1, "battery thresholds together"
        CFG.update(min_area=1000, sensitivity=50, speed_consistency=0.5)
        autotune_base_set("assistant")
        assert autotune_clamp("min_area", 5000) == 1200 and autotune_clamp("min_area", 100) == 800
        assert abs(autotune_clamp("speed_consistency", 0.3) - 0.4) < 1e-9 and autotune_clamp("sensitivity", 70) == 60
        assert autotune_clamp("walk_frames", 99) == 99
        CFG["min_area"] = 1100; autotune_base_set("calibration"); assert CFG["auto_tune_base"]["min_area"] == 1000, "assistant wins"
        CFG["min_area"] = 3000; AUTOTUNE_LAST.clear()          # changed by hand far outside: that is the new middle
        assert abs(autotune_clamp("min_area", 4000) - 3600) < 1e-6
        wr = weekrep_build("de")
        assert "with_sim" in wr and wr["text"]
    finally:
        CFG.update(keep); AUTOTUNE_LAST.clear()
    return True
