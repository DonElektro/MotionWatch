#@ MoveEye – Teil 617: Übersetzungen «Dein Platz» (früher «Zwilling deines Platzes», Aufräumen 29.10.2026). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_PLATZ = {
    'Your place': ('Dein Platz', 'Ton emplacement', 'Il tuo posto', 'Tes plaz'),
}
for _k, _v in _HX_PLATZ.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
