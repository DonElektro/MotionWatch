#@ MoveEye – Teil 596: Übersetzungen für «MoveEye als KI-Wächter» (Teil 548) und den Schalter auf der Seite Simulator. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Key = English text: (Deutsch, Français, Italiano, Rumantsch). German also into I18N.de of the page Simulator (/*KIGDE*/ of 548).
# ----------------------------------------------------------------------------

_HX_VIER = {
    'MoveEye as AI guard': ('MoveEye als KI-Wächter', 'MoveEye comme gardien IA', 'MoveEye come guardiano IA', 'MoveEye sco guardian IA'),
    "In rounds with a guard role (guard, team against team, team against MoveEye, online rounds) MoveEye itself is the guard: everybody sneaks, MoveEye's real detection watches, the head follows and the shutter fires by itself. Such rounds go into their own list «against the AI», not into the ranking.": (
        'In Runden mit Wächter (Wächter, Team gegen Team, Team gegen MoveEye, Online-Runden) ist MoveEye selbst der Wächter: alle schleichen, die echte Erkennung von MoveEye passt auf, der Kopf folgt und der Auslöser löst selbst aus. Solche Runden kommen in eine eigene Liste «gegen die KI», nicht in die Rangliste.',
        'Dans les manches avec un gardien (gardien, équipe contre équipe, équipe contre MoveEye, manches en ligne), MoveEye est lui-même le gardien : tout le monde se faufile, la vraie détection de MoveEye surveille, la tête suit et le déclencheur se déclenche tout seul. Ces manches vont dans leur propre liste «contre l’IA», pas dans le classement.',
        'Nei turni con un guardiano (guardiano, squadra contro squadra, squadra contro MoveEye, turni online) MoveEye stesso fa il guardiano: tutti si intrufolano, il vero rilevamento di MoveEye sorveglia, la testa segue e lo scatto parte da solo. Questi turni finiscono in una lista propria «contro l’IA», non nella classifica.',
        'En rundas cun in guardian (guardian, team cunter team, team cunter MoveEye, rundas online) è MoveEye sez il guardian: tuts sa stgaffan, la vaira identificaziun da MoveEye fa attenziun, il chau suonda ed il declenchader declegna sez. Talas rundas vegnan en ina glista atgna «cunter la IA», betg en la classificaziun.'),
    'On: MoveEye guards rounds with a guard role itself': ('Ein: MoveEye bewacht Runden mit Wächter selbst', 'Activé : MoveEye garde lui-même les manches avec gardien', 'Attivo: MoveEye sorveglia da sé i turni con guardiano', 'En: MoveEye survegl sez rundas cun guardian'),
    'This round: MoveEye guards (AI)': ('Diese Runde: MoveEye bewacht (KI)', 'Cette manche : MoveEye garde (IA)', 'Questo turno: MoveEye sorveglia (IA)', 'Questa runda: MoveEye survegl (IA)'),
    'MoveEye is not connected to the simulator game': ('MoveEye ist nicht mit dem Spiel des Simulators verbunden', 'MoveEye n’est pas connecté au jeu du simulateur', 'MoveEye non è collegato al gioco del simulatore', 'MoveEye n’è betg collià cun il gieu dal simulatur'),
    'Against the AI': ('Gegen die KI', 'Contre l’IA', 'Contro l’IA', 'Cunter la IA'),
    'caught': ('erwischt', 'attrapé', 'preso', 'tschiffà'),
    'at the goal': ('am Ziel', 'au but', 'al traguardo', 'a la mira'),
    'The AI': ('Die KI', 'L’IA', 'L’IA', 'La IA'),
    'catches': ('erwischt', 'prises', 'catture', 'tschiffads'),
    'false alarms': ('Fehlalarme', 'fausses alarmes', 'falsi allarmi', 'fals alarms'),
    'shots': ('Auslösungen', 'déclenchements', 'scatti', 'declenchaments'),
    'Reset the list «against the AI»': ('Liste «gegen die KI» zurücksetzen', 'Réinitialiser la liste «contre l’IA»', 'Azzerare la lista «contro l’IA»', 'Reinizialisar la glista «cunter la IA»'),
    'Reset the list «against the AI»?': ('Liste «gegen die KI» zurücksetzen?', 'Réinitialiser la liste «contre l’IA» ?', 'Azzerare la lista «contro l’IA»?', 'Reinizialisar la glista «cunter la IA»?'),
    'no rounds against the AI yet': ('noch keine Runden gegen die KI', 'encore aucune manche contre l’IA', 'ancora nessun turno contro l’IA', 'anc naginas rundas cunter la IA'),
    # Gameplay ausfeilen (31.10.2026): the AI tower of the simulator (gameturm.gd)
    'AI tower': ('KI-Turm', 'Tour de l’IA', 'Torre dell’IA', 'Tur da la IA'),
    'floor': ('Stufe', 'étage', 'livello', 'stgalim'),
    'highest floor': ('höchste Stufe', 'étage le plus haut', 'livello più alto', 'il stgalim il pli aut'),
    'towers': ('Türme', 'tours', 'torri', 'turs'),
    'AI tower now: floor': ('KI-Turm läuft: Stufe', 'Tour de l’IA en cours : étage', 'Torre dell’IA in corso: livello', 'Tur da la IA en curs: stgalim'),
    'Start the AI tower: quick start «KI-Turm» in the game wizard': ('KI-Turm starten: Schnellstart «KI-Turm» im Spiel-Assistenten', 'Lancer la tour de l’IA : départ rapide «KI-Turm» dans l’assistant de jeu', 'Avviare la torre dell’IA: avvio rapido «KI-Turm» nell’assistente di gioco', 'Lantschar la tur da la IA: start svelt «KI-Turm» en l’assistent da gieu'),
}
for _k, _v in _HX_VIER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

SIM_PAGE = SIM_PAGE.replace("<!--KIGJS-->", KIG_JS.replace("/*KIGDE*/{}", json.dumps({k: DE[k] for k in KIG_KEYS if k in DE and DE[k] != k}, ensure_ascii=False)), 1)
