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

# the manual (chapter «Platz einrichten», the camera height / foot point of 624): one sentence about crawling at night (418k)
_HELP_E3 = {
    "de": ("(Reh / Fuchs = Tier statt Person)", "(Reh / Fuchs = Tier statt Person; etwas Grosses, Warmes, das sich nachts nah am Boden "
           "bewegt, gibt den Voralarm «Etwas Grosses am Boden» und nach 6 s «Person?» – eine kriechende Person)"),
    "en": ("(roe deer / fox = animal instead of person)", "(roe deer / fox = animal instead of person; something big and warm that moves "
           "near the ground at night gives the pre-alarm «Something big at the ground» and after 6 s «Person?» – a crawling person)"),
    "fr": ("(chevreuil / renard = animal au lieu de personne)", "(chevreuil / renard = animal au lieu de personne ; quelque chose de grand et "
           "chaud qui bouge la nuit près du sol donne la pré-alarme « Quelque chose de grand au sol » et après 6 s « Personne ? » – une "
           "personne qui rampe)"),
    "it": ("(capriolo / volpe = animale invece di persona)", "(capriolo / volpe = animale invece di persona; qualcosa di grande e caldo che "
           "di notte si muove vicino a terra dà il preallarme «Qualcosa di grande a terra» e dopo 6 s «Persona?» – una persona che striscia)"),
    "rm": ("(chavriel / vulp = animal empè da persuna)", "(chavriel / vulp = animal empè da persuna; insatge grond e chaud che sa mova la "
           "notg datiers dal terren dat il preallarm «Insatge grond per terra» e suenter 6 s «Persuna?» – ina persuna che sa splattira)"),
}
_hp_en = HELP_PAGE.find('<div lang="en">')
if _hp_en > 0:
    HELP_PAGE = HELP_PAGE[:_hp_en].replace(*_HELP_E3["de"], 1) + HELP_PAGE[_hp_en:].replace(*_HELP_E3["en"], 1)
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = HELP_X[_L].replace(*_HELP_E3[_L], 1)
