#@ MoveEye – Teil 623: Übersetzungen für die «KI-Hilfe» am Auslöser (Teil 542: KI-Rahmen, KI zielt, KI-Autopilot). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Key = English text: (Deutsch, Français, Italiano, Rumantsch). German also into I18N.de of the live page (/*KIHDE*/).
# ----------------------------------------------------------------------------

_HX_KIHILFE = {
    'AI help off': ('KI-Hilfe aus', 'Aide IA désactivée', 'Aiuto IA spento', 'Agid IA deactivà'),
    'AI frames': ('KI-Rahmen', 'Cadres IA', 'Riquadri IA', 'Rom IA'),
    'AI aims': ('KI zielt', 'L’IA vise', 'L’IA mira', 'L’IA mira'),
    'AI autopilot': ('KI-Autopilot', 'Pilote automatique IA', 'Pilota automatico IA', 'Autopilot IA'),
    'paused': ('pausiert', 'en pause', 'in pausa', 'en pausa'),
    'you steer': ('du steuerst', 'tu diriges', 'guidi tu', 'ti manegias'),
    'round with AI help': ('Runde mit KI-Hilfe', 'manche avec aide IA', 'turno con aiuto IA', 'runda cun agid IA'),
    'this round does not count for the leaderboard': (
        'diese Runde zählt nicht für die Rangliste', 'cette manche ne compte pas pour le classement',
        'questo turno non conta per la classifica', 'questa runda na quinta betg per la ranglista'),
    'AI help for this round: off → AI frames → AI aims → AI autopilot (L2 on the controller). With AI help the round does not count for the leaderboard.': (
        'KI-Hilfe für diese Runde: aus → KI-Rahmen → KI zielt → KI-Autopilot (L2 am Controller). Mit KI-Hilfe zählt die Runde nicht für die Rangliste.',
        'Aide IA pour cette manche : désactivée → cadres IA → l’IA vise → pilote automatique IA (L2 sur la manette). Avec l’aide IA, la manche ne compte pas pour le classement.',
        'Aiuto IA per questo turno: spento → riquadri IA → l’IA mira → pilota automatico IA (L2 sul controller). Con l’aiuto IA il turno non conta per la classifica.',
        'Agid IA per questa runda: deactivà → rom IA → l’IA mira → autopilot IA (L2 al controller). Cun agid IA na quinta la runda betg per la ranglista.'),
    'error': ('Fehler', 'erreur', 'errore', 'errur'),
}
for _k, _v in _HX_KIHILFE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("/*KIHDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_KIHILFE.items()}, ensure_ascii=False), 1)
