#@ MoveEye – Teil 639k: Übersetzungen und Karte «Hier steht etwas, das wie eine Person aussieht – ignorieren?» (feste Fehl-Personen, 418) auf der Hauptseite, Anleitungs-Absatz. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_FIXP = {
    'Something here looks like a person - ignore it?': ('Hier steht etwas, das wie eine Person aussieht – ignorieren?',
                                                        'Quelque chose ici ressemble à une personne – l’ignorer ?',
                                                        'Qui c’è qualcosa che sembra una persona – ignorarlo?',
                                                        'Qua stat insatge che para ina persuna – ignorar?'),
    'It has not moved for minutes. MoveEye treats it as a thing for now (no alarm, the head does not follow); a mask keeps it so.':
        ('Es hat sich seit Minuten nicht bewegt. MoveEye behandelt es vorerst als Gegenstand (kein Alarm, der Kopf folgt nicht); eine Maske merkt es sich dauerhaft.',
         'Cela n’a pas bougé depuis des minutes. MoveEye le traite pour l’instant comme un objet (pas d’alarme, la tête ne suit pas) ; un masque le garde ainsi.',
         'Non si muove da minuti. MoveEye lo tratta per ora come un oggetto (nessun allarme, la testa non lo segue); una maschera lo ricorda per sempre.',
         'Igl na s’ha betg movì dapi minutas. MoveEye al tracta per ussa sco object (nagin alarm, il chau na suonda betg); ina mascra al tegna uschia.'),
    'Ignore (make a mask)': ('Ignorieren (Maske übernehmen)', 'Ignorer (créer un masque)', 'Ignora (crea una maschera)', 'Ignorar (far ina mascra)'),
    'It is a person': ('Ist eine Person', 'C’est une personne', 'È una persona', 'Igl è ina persuna'),
    'Mask made': ('Maske gemacht', 'Masque créé', 'Maschera creata', 'Mascra fatga'),
    'Looks like a person': ('Sieht aus wie eine Person', 'Ressemble à une personne', 'Sembra una persona', 'Para ina persuna'),
    'at most 12 zones': ('höchstens 12 Zonen', '12 zones au maximum', 'al massimo 12 zone', 'maximalmain 12 zonas'),
}
for _k, _v in _HX_FIXP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

WEB_PAGE = WEB_PAGE.replace("</body>", fixp_main_js() + "</body>", 1)     # the card of 418 with the German texts
