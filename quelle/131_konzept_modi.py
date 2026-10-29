#@ MoveEye – Teil 131: Konzept – Modi und Profile zusammengeführt: alte Einstellungen sicher übernehmen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Konzept, Wunsch Daniel): EIN Ort entscheidet, was das Gerät tut - der Modus (130). Der Einsatzzweck (use_case)
# entscheidet nur, was angezeigt wird. Der Modus «Nachtwache» ist weg («Heute Nacht bewachen» macht das für eine Nacht),
# das Camping-Profil ist der Modus «Camping». Hier werden Einstellungen älterer Versionen beim Laden umgestellt, ohne dass
# sich am Verhalten des Geräts etwas ändert (Schutz bleibt, wie er ist; nichts wird ein- oder ausgeschaltet):
#  - Modus «night» aktiv -> kein Modus mehr, die jetzigen Werte bleiben die eigenen Einstellungen
#  - Camping-Profil ohne Modus -> Modus «Camping» (Ausschalten gibt wie bisher die alten Werte zurück)
#  - ungültige Licht-Werte aus den alten Modi (True / False statt einer Auswahl) -> gültige Auswahl mit gleicher Wirkung
#  - die Liste der gemerkten eigenen Einstellungen bekommt die neuen Schlüssel der Modi (z. B. das weisse Licht)
# ----------------------------------------------------------------------------
_LIGHT_AUTO_OK = ("alarm_dark", "alarm", "dark")


def _concept_fix_lights(d, live):
    """light_white_auto False (old mode wildlife) meant «never by itself»; light_ir_auto True (old mode night) never worked
    (no valid choice) - both become valid choices with the same effect"""
    if not isinstance(d, dict):
        return
    for n in ("white", "ir"):
        k = f"light_{n}_auto"
        if k in d and d[k] not in _LIGHT_AUTO_OK:
            if d[k] is False and live and d.get("light_" + n) == "auto":
                d["light_" + n] = "off"                       # same effect: the light does not go on by itself
            d[k] = "alarm_dark" if n == "white" else "dark"


def concept_migrate():
    """called after loading / importing the settings (see apply_settings below); returns the list of what was changed"""
    did = []
    m = str(CFG.get("mode") or "")
    if m == "night":
        CFG["mode"] = ""; CFG["mode_prev"] = {}; CFG["mode_since"] = 0.0
        did.append("mode night -> own settings (values kept)")
    elif m and m not in dict((x[0], x) for x in MODES):
        CFG["mode"] = ""; CFG["mode_prev"] = {}
        did.append(f"unknown mode {m} -> own settings")
    if CFG.get("camping") and (CFG.get("mode") or "") != "camping" and not CFG.get("mode"):
        cp = CFG.get("camping_prev") if isinstance(CFG.get("camping_prev"), dict) else {}
        CFG["mode"] = "camping"; CFG["mode_since"] = float(cp.get("_seq") or time.time())
        CFG["mode_prev"] = {"armed": bool(cp.get("armed", False)), "hotspot_on": bool(cp.get("hotspot_on", False)),
                            "_seq": float(cp.get("_seq") or time.time()) - 0.001}
        did.append("camping profile -> mode camping")
    _concept_fix_lights(CFG, True)
    for pk in ("mode_prev", "camping_prev", "turbo_prev"):
        _concept_fix_lights(CFG.get(pk), False)
    prev = CFG.get("mode_prev")
    if CFG.get("mode") and isinstance(prev, dict) and prev and CFG["mode"] != "camping":
        for k in _mode_keys():                               # keys the modes switch now, but not when this mode was chosen
            if k not in prev and k in CFG and k not in MODE_SETS.get(CFG["mode"], {}):
                prev[k] = CFG[k]
    if did:
        log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
    return did


_apply_settings_before_concept = apply_settings


def apply_settings(data):                                   # 2.98.14: the same as before, then the migration above
    r = _apply_settings_before_concept(data)
    try:
        concept_migrate()
    except Exception as e:
        log_event("sys", f"Settings migration: {e}"[:150])
    return r
