#@ MoveEye – Teil 612: Übersetzungen der «Wächter-Werkzeuge» (Teil 543, Spielkonzept: Energie, Licht, Sirene, Scan, Zoom). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Key = English text: (Deutsch, Français, Italiano, Rumantsch). German also into I18N.de of the live page (/*WAECHTERDE*/).
_HX_SPIELA = {
    'Light': ('Licht', 'Lumière', 'Luce', 'Glisch'),
    'Siren': ('Sirene', 'Sirène', 'Sirena', 'Sirena'),
    'Scan': ('Scan', 'Scan', 'Scansione', 'Scan'),
    'Zoom': ('Zoom', 'Zoom', 'Zoom', 'Zoom'),
    'Energy': ('Energie', 'Énergie', 'Energia', 'Energia'),
    'energy': ('Energie', 'énergie', 'energia', 'energia'),
    'not enough energy': ('zu wenig Energie', 'pas assez d’énergie', 'energia insufficiente', 'memia pauca energia'),
}
for _k, _v in _HX_SPIELA.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("/*WAECHTERDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_SPIELA.items()}, ensure_ascii=False), 1)
