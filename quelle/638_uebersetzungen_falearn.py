#@ MoveEye – Teil 638: Übersetzungen «Lernbilder prüfen» (Fehlalarme aus den Spielen, 148). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_FALEARN = {
    'Check learning pictures': ('Lernbilder prüfen', 'Vérifier les images d’apprentissage', 'Controlla le immagini di apprendimento', 'Controllar ils maletgs d’emprender'),
    'Learning pictures checked': ('Lernbilder geprüft', 'Images d’apprentissage vérifiées', 'Immagini di apprendimento controllate', 'Maletgs d’emprender controllads'),
    'Game pictures for the training': ('Spielbilder fürs Training', 'Images de jeu pour l’entraînement', 'Immagini di gioco per l’addestramento', 'Maletgs da gieu per il trenament'),
    'doubtful (not used)': ('zweifelhaft (nicht verwendet)', 'douteuses (non utilisées)', 'dubbie (non usate)', 'dubitaivels (betg utilisads)'),
    'moved to «doubtful»': ('nach «zweifel» verschoben', 'déplacées vers «douteux»', 'spostate in «dubbi»', 'spustads en «dubis»'),
    'kept': ('übernommen', 'conservées', 'tenute', 'tegnids'),
}
for _k, _v in _HX_FALEARN.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
