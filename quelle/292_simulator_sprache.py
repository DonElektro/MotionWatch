#@ MoveEye – Teil 292: die Sprache von MoveEye an den 3D-Simulator (Sprachen im Simulator, Phase 1, 30.10.2026). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_sim_state_290_292 = sim_state


def sim_state():                                          # + 292: «lang» - the simulator shows its texts in the language of MoveEye (i18n.gd)
    d = _sim_state_290_292()
    d["lang"] = cur_lang()
    return d
