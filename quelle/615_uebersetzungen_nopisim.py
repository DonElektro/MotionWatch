#@ MoveEye – Teil 615: Übersetzungen «kluge Runde» als Unterschalter von «Patrouille» (2.98.41). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_NOPISIM = {
    'smart: look longer at the important directions': ('klug: wichtige Richtungen länger anschauen', 'intelligente : regarder plus longtemps les directions importantes',
                                                       'intelligente: guardare più a lungo le direzioni importanti', 'intelligent: guardar pli ditg las direcziuns impurtantas'),
}
for _k, _v in _HX_NOPISIM.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
