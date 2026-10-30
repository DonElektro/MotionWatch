#@ MoveEye – Teil 638: Übersetzungen «Bild wird geladen» (Platzhalter ⏳ auf dem Live-Bild, 2.98.38). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_BILDLADE = {'Picture is loading – tap to reload': ('Bild wird geladen – tippen zum Neuladen', 'Image en cours de chargement – touchez pour recharger',
                                                      'Immagine in caricamento – tocca per ricaricare', 'Il maletg chargia – tutgar per chargiar danovamain')}
for _k, (_de, _fr, _it, _rm) in _HX_BILDLADE.items():
    DE.setdefault(_k, _de)
    for _l, _v in (("fr", _fr), ("it", _it), ("rm", _rm)):
        TRX[_l].setdefault(_k, _v)
