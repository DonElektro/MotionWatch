#@ MoveEye – Teil 639p: Schalter aufräumen (Daniel 01.11.2026, review_schalter): Test-Postfach in der Simulation immer an, Simulation immer mit eigenen Einstellungen, Anmelden immer verschlüsselt (vom Gerät selbst weiter ohne https), «Auch nicht signierte Versionen annehmen» nur im Entwickler-Bereich und nach 24 h von selbst aus. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entfernt (nur diese Schalter, die Funktion bleibt immer an):
#   * notify_sandbox  -> sandbox_active() (141) ist in der Simulation immer wahr; Info-Meldungen gehen mit sim_info_push
#                        oder bei echten Pi-Warnungen weiter aufs Handy (sandbox_lets_through, 141 / 060)
#   * sim_separate    -> simprof_on / simprof_off (340) immer
#   * login_https_only-> seclogin_mode (574) immer «on» (oder «fallback» ohne https-Seite, nie ausgesperrt)
# Ein gespeicherter alter Wert dieser Schlüssel wird beim Laden still übergangen (apply_settings kennt sie nicht mehr).
# update_unsigned: Abschnitt «Developer» (639c _MENU_MOVES), Ablauf in update_unsigned_ok (380), Zeit update_unsigned_t (020).
# ----------------------------------------------------------------------------
_HX_SCHALTER = {
    "Only for your own builds: MoveEye also installs versions without the developer's signature. Switches itself off after 24 hours.":
        ("Nur für eigene Fassungen: MoveEye installiert auch Versionen ohne die Signatur des Entwicklers. Schaltet sich nach 24 Stunden selbst aus.",
         "Uniquement pour vos propres versions : MoveEye installe aussi des versions sans la signature du développeur. Se désactive tout seul après 24 heures.",
         "Solo per versioni proprie: MoveEye installa anche versioni senza la firma dello sviluppatore. Si spegne da solo dopo 24 ore.",
         "Mo per atgnas versiuns: MoveEye installescha er versiuns senza la signatura dal sviluppader. Sa stizza sez suenter 24 uras."),
    "Off.": ("Aus.", "Désactivé.", "Spento.", "Stizzà."),
    "Unsigned versions: switched off by itself after 24 hours":
        ("Nicht signierte Versionen: nach 24 Stunden von selbst ausgeschaltet",
         "Versions non signées : désactivé tout seul après 24 heures",
         "Versioni non firmate: spento da solo dopo 24 ore",
         "Versiuns betg signadas: stizzà sez suenter 24 uras"),
}
for _k, _v in _HX_SCHALTER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

SET_HELP["update_unsigned"] = ("Only for your own builds: MoveEye also installs versions without the developer's signature. Switches itself off after 24 hours.",
                               "Off.")


def schalter_selftest():
    """the removed switches stay removed, the functions are always on, unsigned versions expire after 24 hours"""
    lists = {x[1] for x in TOGGLES + SLIDERS + TEXTS}
    for k in ("notify_sandbox", "sim_separate", "login_https_only"):
        assert k not in CFG and k not in lists, f"{k} is back"
    assert any(x[1] == "update_unsigned" and x[0] == "Developer" for x in TOGGLES), "update_unsigned not in the developer section"
    keep = {k: CFG.get(k) for k in ("sim_on", "update_unsigned", "update_unsigned_t")}
    G = globals(); keep_save = G["save_settings"]; keep_log = G["log_event"]
    try:
        G["save_settings"] = lambda *a, **k: None; G["log_event"] = lambda *a, **k: None
        CFG["sim_on"] = True
        assert sandbox_active(), "test inbox not on in the simulation"
        CFG.update(update_unsigned=True, update_unsigned_t=0.0)
        assert update_unsigned_ok() and CFG["update_unsigned_t"] > 0, "time not started"
        CFG["update_unsigned_t"] = time.time() - 25 * 3600
        assert not update_unsigned_ok() and not CFG["update_unsigned"], "not switched off after 24 h"
    finally:
        G["save_settings"] = keep_save; G["log_event"] = keep_log
        CFG.update(keep)
    return "test inbox always on in the simulation, login always encrypted, unsigned versions 24 h"


SELFTEST_EXTRA.append(("Switches tidied up (639p)", schalter_selftest))
