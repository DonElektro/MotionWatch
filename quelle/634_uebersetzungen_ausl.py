#@ MoveEye – Teil 634: Übersetzungen für den «Auslöser» (Teil 539: Fadenkreuz, runder Knopf, R2, Test-Postfach). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Key = English text: (Deutsch, Français, Italiano, Rumantsch). German also into I18N.de of the live page (/*AUSLDE*/).
# ----------------------------------------------------------------------------

_HX_AUSL = {
    'Shutter locked': ('Auslöser gesperrt', 'Déclencheur bloqué', 'Scatto bloccato', 'Sbrinzlader bloccà'),
    'caught!': ('erwischt!', 'attrapé !', 'preso!', 'tschiffà!'),
    'points': ('Punkte', 'points', 'punti', 'puncts'),
    'alarm into the test inbox': ('Alarm ins Test-Postfach', 'alarme dans la boîte de test', 'allarme nella casella di prova', 'alarm en la chascha da test'),
    'Missed - false alarm': ('Daneben – Fehlalarm', 'Raté – fausse alarme', 'Mancato – falso allarme', 'Fallà – fauss alarm'),
    'shutter locked 3 s': ('Auslöser 3 s gesperrt', 'déclencheur bloqué 3 s', 'scatto bloccato 3 s', 'sbrinzlader bloccà 3 s'),
    'Hit area': ('Trefferkreis', 'Zone de tir', 'Area di tiro', 'Cirquel da tour'),
    'easy': ('leicht', 'facile', 'facile', 'levet'),
    'hard': ('schwer', 'difficile', 'difficile', 'difficil'),
    'normal': ('normal', 'normal', 'normale', 'normal'),
    'Shutter: a shot at the middle of the picture (R2 on the controller)': (
        'Auslöser: Schuss auf die Bildmitte (R2 am Controller)', 'Déclencheur : un tir au milieu de l’image (R2 sur la manette)',
        'Scatto: un colpo al centro dell’immagine (R2 sul controller)', 'Sbrinzlader: in tir en il center dal maletg (R2 al controller)'),
    'You are the guard: aim the middle of the picture (circle) at a player and press 🎯': (
        'Du bist Wächter: Bildmitte (Kreis) auf einen Spieler richten und 🎯 drücken',
        'Tu es le gardien : vise un joueur avec le milieu de l’image (cercle) et appuie sur 🎯',
        'Sei la guardia: punta il centro dell’immagine (cerchio) su un giocatore e premi 🎯',
        'Ti es il guardian: drizza il center dal maletg (cirquel) sin in giugader e smatga 🎯'),
    'Shutter: a shot at the middle of the picture (with the simulator; in «Team gegen MoveEye» a catch)': (
        'Auslöser: Schuss auf die Bildmitte (mit dem Simulator; bei «Team gegen MoveEye» ein Fang)',
        'Déclencheur : un tir au milieu de l’image (avec le simulateur ; dans «Team gegen MoveEye» une capture)',
        'Scatto: un colpo al centro dell’immagine (con il simulatore; in «Team gegen MoveEye» una cattura)',
        'Sbrinzlader: in tir en il center dal maletg (cun il simulatur; en «Team gegen MoveEye» ina tschiffada)'),
    'Shutter: {name} caught': ('Auslöser: {name} erwischt', 'Déclencheur : {name} attrapé', 'Scatto: {name} preso', 'Sbrinzlader: {name} tschiffà'),
    'Photo by {by} · {m}:{s} in the round · {d} m · +{pts} points': (
        'Foto von {by} · {m}:{s} in der Runde · {d} m · +{pts} Punkte', 'Photo de {by} · {m}:{s} dans la manche · {d} m · +{pts} points',
        'Foto di {by} · {m}:{s} nel turno · {d} m · +{pts} punti', 'Foto da {by} · {m}:{s} en la runda · {d} m · +{pts} puncts'),
}
for _k, _v in _HX_AUSL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("/*AUSLDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_AUSL.items()}, ensure_ascii=False), 1)
