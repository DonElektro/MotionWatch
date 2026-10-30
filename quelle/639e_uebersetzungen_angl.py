#@ MoveEye – Teil 639e: Übersetzungen «Angleichen MoveEye ↔ Simulator» (639d, 470, 530, 549). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_ANGL = {
    'Switch off, restart, pause': ('Ausschalten, neu starten, pausieren', 'Éteindre, redémarrer, pause', 'Spegnere, riavviare, pausa', 'Stizzar, reaviar, pausa'),
    'Faults (servos, under-voltage)': ('Störungen (Servos, Unterspannung)', 'Pannes (servos, sous-tension)', 'Guasti (servo, sottotensione)', 'Disfunctions (servos, tensiun memia bassa)'),
    'Photo of the place': ('Foto des Platzes', 'Photo de l’emplacement', 'Foto del posto', 'Foto da la plazza'),
}
for _k, _v in _HX_ANGL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the main page has its own dictionary: German of the new link (devExtras) and of the tile of Sim-Kompakt (549)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({_k: _v[0] for _k, _v in _HX_ANGL.items()}, ensure_ascii=False)
                            + ");</script></body>", 1)
