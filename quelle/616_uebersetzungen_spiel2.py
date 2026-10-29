#@ MoveEye – Teil 616: Übersetzungen der Spiel-Extras (Wetterwechsel, Tarn-Sachen, Diebstahl, Lern-Punkte; Simulator 3D-4.x). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_SPIEL2 = {
    'Best teachers': ('Beste Lehrer', 'Meilleurs professeurs', 'Migliori insegnanti', 'Meglders magisters'),
}
for _k, _v in _HX_SPIEL2.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
