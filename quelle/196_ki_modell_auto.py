#@ MoveEye – Teil 196: Eigenes KI-Modell von selbst aktualisieren (täglich, nur wenn die Auswertung nicht schlechter ist). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# «KI trainieren» im Simulator (kitrain.gd) legt ein Trainingspaket auf GitHub und startet das Training (ki_modell.yml).
# Das neue Modell erscheint im Release «ki-modell». Hier: einmal am Tag (und beim Knopf «Eigenes Modell aktualisieren»)
# das Manifest lesen und das Modell nur übernehmen, wenn es neu ist und seine Messung nicht schlechter als die des
# laufenden: mAP50, Trefferquote und «Personen gefunden» (eval.recall_person aus der Auswertung «wo versagt die KI»),
# je mit 0.02 Spielraum (jedes Training misst auf etwas anderen Bildern).
# Nur wenn schon ein eigenes Modell heruntergeladen ist - zum ersten Mal holt man es von Hand.
# ----------------------------------------------------------------------------
_OWNAUTO_CFG = {"ai_own_auto": True, "ai_own_check_day": ""}
for _k, _v in _OWNAUTO_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
OWN_AI_TOL = 0.02


def own_ai_current_meta():
    """the manifest of the downloaded own model, or None"""
    _o, js = own_ai_paths()
    if not js:
        return None
    try:
        with open(js, encoding="utf-8") as f:
            return own_ai_check_manifest(json.load(f))
    except (OSError, ValueError, TypeError):
        return None


def _own_ai_scores(m):
    """the comparable numbers of a manifest: {"mAP50": .., "recall": .., "persons found": ..} (only those it has)"""
    m = m or {}
    met = m.get("metrics") if isinstance(m.get("metrics"), dict) else {}
    ev = m.get("eval") if isinstance(m.get("eval"), dict) else {}
    out = {}
    for name, v in (("mAP50", met.get("map50")), ("recall", met.get("recall")), ("persons found", ev.get("recall_person"))):
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 <= float(v) <= 1.0:
            out[name] = float(v)
    return out


def own_ai_not_worse(new, cur):
    """(ok, reason in English for tr(), detail with numbers) - may the new model replace the running one?"""
    if not cur:
        return True, "", ""
    if str(new.get("sha256") or "") and str(new.get("sha256")) == str(cur.get("sha256") or ""):
        return False, "already the newest model", ""
    a, b = _own_ai_scores(new), _own_ai_scores(cur)
    common = [k for k in a if k in b]
    if not common:
        return (False, "the new model has no evaluation", "") if b else (True, "", "")
    worse = [f"{k} {a[k]:.2f} < {b[k]:.2f}" for k in common if a[k] < b[k] - OWN_AI_TOL]
    if worse:
        return False, "its evaluation is worse", ", ".join(worse)
    return True, "", ""


def own_ai_auto_check(force=False):
    """once a day (force: now): look for a new own model and install it only if it is not worse. Returns (started, reason)."""
    if not CFG.get("ai_own_auto", True) and not force:
        return False, "off"
    if not own_ai_paths()[0]:
        return False, "own model not downloaded yet"
    if DEMO["on"] or OWN_AI["busy"]:
        return False, "busy"
    day = datetime.now().strftime("%Y-%m-%d")
    if not force and CFG.get("ai_own_check_day") == day:
        return False, "checked today"
    CFG["ai_own_check_day"] = day
    save_settings()
    ok, err = own_ai_download(only_better=True)
    OWN_AI["check_msg"] = "" if ok else err
    if not ok:
        log_event("ai", f"Own AI model: daily check not possible ({err})"[:200])
    return ok, err


def _own_ai_auto_loop():
    time.sleep(600)                                      # not right at the start (network, camera first)
    while True:
        try:
            own_ai_auto_check()
        except Exception as e:
            log_event("ai", f"Own AI model check: {e}"[:200])
        time.sleep(1800)


def own_ai_long_text(lang=None):
    """own_ai_text + the summary of its evaluation («wo versagt die KI») + the automatic update (for the window)"""
    i = own_ai_info(lang)
    t = own_ai_text(lang)
    if i.get("summary"):
        t += "\n📊 " + i["summary"]
    if i["present"]:
        t += "\n🔄 " + (tr("updates by itself (daily, only if not worse)", lang) if i["auto"] else tr("automatic update off", lang))
        if CFG.get("ai_own_check_day"):
            t += f" · {tr('last check', lang)} {CFG['ai_own_check_day']}"
    if OWN_AI.get("msg") and OWN_AI["msg"] != "ready" and not OWN_AI["busy"]:
        t += "\n" + OWN_AI["msg"]
    return t


def own_ai_auto_selftest():
    """self-test: comparing two manifests"""
    cur = {"sha256": "a" * 64, "metrics": {"map50": 0.70, "recall": 0.60}, "eval": {"recall_person": 0.80}}
    assert own_ai_not_worse({"sha256": "a" * 64}, cur)[0] is False                                   # the same file
    assert own_ai_not_worse({"sha256": "b" * 64, "metrics": {"map50": 0.69, "recall": 0.61}, "eval": {"recall_person": 0.79}}, cur)[0]   # within 0.02
    ok, why, det = own_ai_not_worse({"sha256": "b" * 64, "metrics": {"map50": 0.72, "recall": 0.62}, "eval": {"recall_person": 0.70}}, cur)
    assert not ok and why == "its evaluation is worse" and "persons found" in det, (ok, why, det)
    assert own_ai_not_worse({"sha256": "b" * 64}, cur)[1] == "the new model has no evaluation"
    assert own_ai_not_worse({"sha256": "b" * 64, "metrics": {"map50": 0.5}}, None)[0]                 # nothing installed yet
    assert own_ai_not_worse({"sha256": "b" * 64, "metrics": {"map50": 0.5}}, {"sha256": "c" * 64})[0]   # old model without numbers


threading.Thread(target=_own_ai_auto_loop, daemon=True, name="own-ai-auto").start()
