#@ MoveEye – Teil 606: Übersetzungen der Spiel-Verbesserungen (Schnellstart im Assistenten, Duell, Tipps der Zuschauer, Stufen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_GAME = {
    'Quick start': ('Schnellstart', 'Démarrage rapide', 'Avvio rapido', 'Start svelt'),
    'runners at most': ('Läufer höchstens', 'coureurs au plus', 'corridori al massimo', 'currids al pli'),
    'Duel': ('Duell', 'Duel', 'Duello', 'Duel'),
    'MoveEye against the guard': ('MoveEye gegen den Wächter', 'MoveEye contre le gardien', 'MoveEye contro il guardiano', 'MoveEye cunter il guardian'),
    'Guesses «Who gets through?»': ('Tipps «Wer kommt durch?»', 'Pronostics «Qui passe ?»', 'Pronostici «Chi passa?»', 'Pronostics «Tgi passa?»'),
    'Level': ('Stufe', 'Niveau', 'Livello', 'Nivel'),
    # game collection: groups (GS-1.4)
    'Touch (phone, tablet)': ('Touch (Handy, Tablet)', 'Tactile (téléphone, tablette)', 'Touch (telefono, tablet)', 'Touch (telefonin, tablet)'),
    'With on-screen buttons': ('Mit Bildschirm-Tasten', 'Avec boutons à l\'écran', 'Con tasti sullo schermo', 'Cun buttuns sin il visur'),
    'With keyboard and mouse (PC)': ('Am PC mit Tastatur und Maus', 'Au PC avec clavier et souris', 'Al PC con tastiera e mouse', 'Al PC cun tastatura e mieur'),
    # Spieltab: admin tab «Mehr → Spielecke» with the tiles and headings of /spiele
    'games installed': ('Spiele installiert', 'jeux installés', 'giochi installati', 'gieus installads'),
    'For phone and tablet (touch)': ('Für Handy und Tablet (Touch)', 'Pour téléphone et tablette (tactile)', 'Per telefono e tablet (touch)', 'Per telefonin e tablet (touch)'),
    'With on-screen buttons (on the PC with the keyboard)': ('Mit Bildschirm-Tasten (am PC mit der Tastatur)', 'Avec boutons à l\'écran (au PC avec le clavier)', 'Con tasti sullo schermo (al PC con la tastiera)', 'Cun buttuns sin il visur (al PC cun la tastatura)'),
    'On the PC with keyboard and mouse': ('Am PC mit Tastatur und Maus', 'Au PC avec clavier et souris', 'Al PC con tastiera e mouse', 'Al PC cun tastatura e mieur'),
}
for _k, _v in _HX_GAME.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
