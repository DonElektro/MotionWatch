#@ MoveEye – Teil 614: Übersetzungen «KI trainieren» / eigenes Modell von selbst aktualisieren (Teile 195, 196, 579). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_TRAINING = {
    'Own model: update by itself (checks daily, installs a new model only if its evaluation is not worse)': (
        'Eigenes Modell von selbst aktualisieren (prüft täglich, nimmt ein neues Modell nur, wenn seine Auswertung nicht schlechter ist)',
        'Modèle propre : mise à jour automatique (vérifie chaque jour, n’installe un nouveau modèle que si son évaluation n’est pas moins bonne)',
        'Modello proprio: aggiornamento automatico (controlla ogni giorno, installa un nuovo modello solo se la sua valutazione non è peggiore)',
        'Agen model: actualisar sez (controllescha mintga di, installescha in nov model mo sch’sia evaluaziun n’è betg mendra)'),
    'updates by itself (daily, only if not worse)': ('aktualisiert sich selbst (täglich, nur wenn nicht schlechter)', 'se met à jour tout seul (chaque jour, seulement s’il n’est pas moins bon)',
                                                   'si aggiorna da solo (ogni giorno, solo se non peggiore)', 's’actualisescha sez (mintga di, mo sche betg mender)'),
    'automatic update off': ('automatisches Aktualisieren aus', 'mise à jour automatique désactivée', 'aggiornamento automatico spento', 'actualisaziun automatica deactivada'),
    'last check': ('zuletzt geprüft', 'dernière vérification', 'ultimo controllo', 'ultima controlla'),
    'not installed': ('nicht übernommen', 'pas installé', 'non installato', 'betg installà'),
    'already the newest model': ('schon das neueste Modell', 'déjà le modèle le plus récent', 'già il modello più recente', 'gia il model il pli nov'),
    'its evaluation is worse': ('seine Auswertung ist schlechter', 'son évaluation est moins bonne', 'la sua valutazione è peggiore', 'sia evaluaziun è mendra'),
    'the new model has no evaluation': ('das neue Modell hat keine Auswertung', 'le nouveau modèle n’a pas d’évaluation', 'il nuovo modello non ha una valutazione', 'il nov model n’ha nagina evaluaziun'),
    'checked today': ('heute schon geprüft', 'déjà vérifié aujourd’hui', 'già controllato oggi', 'gia controllà oz'),
    'off': ('aus', 'désactivé', 'spento', 'deactivà'),
    'busy': ('beschäftigt', 'occupé', 'occupato', 'occupà'),
}
for _k, _v in _HX_TRAINING.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
