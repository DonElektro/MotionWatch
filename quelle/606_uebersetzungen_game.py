#@ MoveEye – Teil 606: Übersetzungen der Spiel-Verbesserungen (Schnellstart im Assistenten, Duell, Tipps der Zuschauer, Stufen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_GAME = {
    'Quick start': ('Schnellstart', 'Démarrage rapide', 'Avvio rapido', 'Start svelt'),
    'runners at most': ('Läufer höchstens', 'coureurs au plus', 'corridori al massimo', 'currids al pli'),
    'Duel': ('Duell', 'Duel', 'Duello', 'Duel'),
    'MoveEye against the guard': ('MoveEye gegen den Wächter', 'MoveEye contre le gardien', 'MoveEye contro il guardiano', 'MoveEye cunter il guardian'),
    'Guesses «Who gets through?»': ('Tipps «Wer kommt durch?»', 'Pronostics «Qui passe ?»', 'Pronostici «Chi passa?»', 'Pronostics «Tgi passa?»'),
    'Level': ('Stufe', 'Niveau', 'Livello', 'Nivel'),
}
for _k, _v in _HX_GAME.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
