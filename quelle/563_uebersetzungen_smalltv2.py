#@ MoveEye – Teil 563: Übersetzungen (DE / FR / IT / RM) zu «Live-Bild und Wechsel» und der Alarm-Animation des SmallTV (Teil 553). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_STV2 = {
    'Live picture and rotation': ('Live-Bild und Wechsel', 'Image en direct et alternance', 'Immagine dal vivo e alternanza', 'Maletg live e midada'),
    'stv-rot-hint': ('Tagsüber wechseln alle 30 s Live-Bild und «Akku und Strom», ein Alarm erscheint als Animation (60 s) und danach 5 min als Standbild. Nachts nur die rote Statusseite. Aus = nur die Statusseite.',
                     'Le jour, l’image en direct et «Batterie et courant» alternent toutes les 30 s, une alarme apparaît en animation (60 s) puis 5 min en image fixe. La nuit seulement la page d’état rouge. Désactivé = seulement la page d’état.',
                     'Di giorno ogni 30 s si alternano immagine dal vivo e «Batteria e corrente», un allarme appare come animazione (60 s) e poi 5 min come immagine fissa. Di notte solo la pagina di stato rossa. Spento = solo la pagina di stato.',
                     'Di sa midan mintga 30 s maletg live ed «Accu e current», in alarm cumpara sco animaziun (60 s) e lura 5 min sco maletg fix. La notg mo la pagina da status cotschna. Deactivà = mo la pagina da status.'),
    'Live picture': ('Live-Bild', 'Image en direct', 'Immagine dal vivo', 'Maletg live'),
    'Battery and power': ('Akku und Strom', 'Batterie et courant', 'Batteria e corrente', 'Accu e current'),
    'Alarm animation': ('Alarm-Animation', 'Animation d’alarme', 'Animazione d’allarme', 'Animaziun d’alarm'),
    'about {n} pictures/day': ('ca. {n} Bilder/Tag', 'env. {n} images/jour', 'ca. {n} immagini/giorno', 'ca. {n} maletgs/di'),
    'No camera picture': ('Kein Kamerabild', 'Pas d’image de la caméra', 'Nessuna immagine della telecamera', 'Nagin maletg da la camera'),
    'Charging': ('Laden', 'Charge', 'Carica', 'Chargiar'),
    'Solar': ('Solar', 'Solaire', 'Solare', 'Solar'),
    'Consumption': ('Verbrauch', 'Consommation', 'Consumo', 'Consum'),
    'Runtime left': ('Restlaufzeit', 'Autonomie restante', 'Autonomia residua', 'Temp restant'),
    'full in {n} min': ('voll in {n} min', 'pleine dans {n} min', 'piena tra {n} min', 'plain en {n} min'),
    'yes': ('ja', 'oui', 'sì', 'gea'),
    'simulator': ('Simulator', 'simulateur', 'simulatore', 'simulatur'),
    'After the animation the alarm picture stays (min)': ('Nach der Animation bleibt das Alarmbild (min)', 'Après l’animation, l’image d’alarme reste (min)',
                                                          'Dopo l’animazione l’immagine d’allarme resta (min)', 'Suenter l’animaziun resta il maletg d’alarm (min)'),
}
for _k, _v in _HX_STV2.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
