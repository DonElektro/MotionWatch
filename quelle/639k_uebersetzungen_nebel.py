#@ MoveEye – Teil 639k: Übersetzungen des Nebel-Modus (411): Hinweis im Licht-Chip der Seite und des Fensters. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_NEBEL = {
    'Fog – view limited': ('Nebel – Sicht eingeschränkt', 'Brouillard – visibilité réduite', 'Nebbia – visibilità ridotta', 'Tschajera – vista limitada'),
}
for _k, _v in _HX_NEBEL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
