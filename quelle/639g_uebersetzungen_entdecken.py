#@ MoveEye – Teil 639g: Übersetzungen der Kachel «Entdeckungen» der Simulator-Zentrale (139, Erlebniswelt 20–23 – Entdeckungsbuch des 3D-Simulators). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_DISC = {
    'Discoveries': ('Entdeckungen', 'Découvertes', 'Scoperte', 'Scuvertas'),
    '{f} of {n} discovered': ('{f} von {n} entdeckt', '{f} sur {n} découverts', '{f} di {n} scoperti', '{f} da {n} scuvrids'),
    'Photo for the discovery book': ('Foto für Entdeckungsbuch', 'Photo pour le carnet de découvertes', 'Foto per il diario delle scoperte', 'Foto per il cudesch da scuvertas'),
    'Open in the simulator': ('Im Simulator öffnen', 'Ouvrir dans le simulateur', 'Apri nel simulatore', 'Avrir en il simulatur'),
    'Blinki hint': ('Blinki-Hinweis', 'Indice de Blinki', 'Suggerimento di Blinki', 'Indicaziun da Blinki'),
    'a place': ('ein Ort', 'un lieu', 'un luogo', 'in lieu'),
    'a scene': ('eine Szene', 'une scène', 'una scena', 'ina scena'),
    'an animal': ('ein Tier', 'un animal', 'un animale', 'in animal'),
    'a person': ('ein Mensch', 'une personne', 'una persona', 'ina persuna'),
    'Found!': ('Entdeckt!', 'Découvert !', 'Scoperto!', 'Scuvrì!'),
    'Something special is in the picture – take the photo now!': ('Etwas Besonderes ist im Bild – jetzt fotografieren!',
        'Quelque chose de spécial est dans l’image – prends la photo maintenant !', 'C’è qualcosa di speciale nell’immagine – scatta la foto ora!',
        'Insatge spezial è en il maletg – fa ussa la foto!'),
    'Come close enough in the 3D view to discover places, animals and funny scenes. 📷 = take a photo with MoveEye’s camera: aim the head, then «Photo for the discovery book». 🌙 🌧 🌅 = only at night, in the rain, in the morning.': ('Wer in der 3D-Ansicht nahe genug kommt, entdeckt Orte, Tiere und lustige Szenen. 📷 = mit MoveEyes Kamera fotografieren: Kopf hinrichten, dann «Foto für Entdeckungsbuch». 🌙 🌧 🌅 = nur nachts, bei Regen, am Morgen.',
        'En s’approchant assez dans la vue 3D, on découvre des lieux, des animaux et des scènes drôles. 📷 = photographier avec la caméra de MoveEye : orienter la tête, puis « Photo pour le carnet de découvertes ». 🌙 🌧 🌅 = seulement la nuit, sous la pluie, le matin.',
        'Avvicinandosi abbastanza nella vista 3D si scoprono luoghi, animali e scene buffe. 📷 = fotografare con la camera di MoveEye: puntare la testa, poi «Foto per il diario delle scoperte». 🌙 🌧 🌅 = solo di notte, con la pioggia, al mattino.',
        'Tgi che vegn avunda datiers en la vista 3D, scuvra lieus, animals e scenas legras. 📷 = fotografar cun la camera da MoveEye: drizzar il chau, lura «Foto per il cudesch da scuvertas». 🌙 🌧 🌅 = mo la notg, cun plievgia, la damaun.'),
    'nothing special in the picture of the camera': ('nichts Besonderes im Bild der Kamera', 'rien de spécial dans l’image de la caméra',
        'niente di speciale nell’immagine della camera', 'nagut spezial en il maletg da la camera'),
    'nothing more to find here right now': ('gerade gibt es hier nichts mehr zu finden', 'plus rien à trouver ici pour l’instant',
        'per ora qui non c’è più niente da trovare', 'per il mument na datti qua nagut pli da chattar'),
}
for _k, _v in _HX_DISC.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
