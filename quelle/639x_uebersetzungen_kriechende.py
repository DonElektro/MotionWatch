#@ MoveEye – Teil 639x: Übersetzungen für Kriechende nachts (418k) und den KI-Zoom (418z). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# real-erk-e3 (31.10.2026): die Push-Nachricht «Etwas Grosses am Boden» (Titel und Text) in de / fr / it / rm.
# ----------------------------------------------------------------------------
_HX_E3 = {
    "Something big at the ground": ("Etwas Grosses am Boden", "Quelque chose de grand au sol", "Qualcosa di grande a terra",
                                    "Insatge grond per terra"),
    "about {d} m, about {l} m long - a crawling person?": ("ca. {d} m, ca. {l} m lang – eine kriechende Person?",
                                                          "env. {d} m, env. {l} m de long – une personne qui rampe ?",
                                                          "circa {d} m, lungo circa {l} m – una persona che striscia?",
                                                          "ca. {d} m, ca. {l} m lung – ina persuna che sa splattira?"),
}
for _k, _v in _HX_E3.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
