#@ MoveEye – Teil 639l: Übersetzungen und Karte «Hier steht etwas, das wie eine Person aussieht – ignorieren?» (feste Fehl-Personen, 418) auf der Hauptseite, Anleitungs-Absatz. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
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
    'It has not moved for minutes. It still counts as a person (alarm, the head follows) until you tap «Ignore».':
        ('Es hat sich seit Minuten nicht bewegt. Es gilt weiter als Person (Alarm, der Kopf folgt), bis du «Ignorieren» drückst.',
         'Cela n’a pas bougé depuis des minutes. Cela compte toujours comme une personne (alarme, la tête suit) jusqu’à ce que tu touches «Ignorer».',
         'Non si muove da minuti. Conta ancora come una persona (allarme, la testa segue) finché non tocchi «Ignora».',
         'Igl na s’ha betg movì dapi minutas. Igl vala vinavant sco persuna (alarm, il chau suonda) fin che ti tutgas «Ignorar».'),
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

# the manual (HELP_PAGE of 540): one paragraph in the section «Erkennung», German and English
for _a, _b in (('<section id="detect" data-icon="🎯"><h2>Erkennung</h2>',
                "<p><b>🌲 Feste Fehl-Personen, Fahrzeuge und Tiere:</b> Sieht die KI an einer Stelle über Minuten eine «Person», die sich nicht "
                "bewegt und nie dorthin gegangen ist (eine kleine Fichte, ein Baumstamm im Infrarot-Licht), zeigt MoveEye nach etwa "
                "45 s (war sie schon beim Start da) bzw. 3 Min. einen Vorschlag. Nur wenn eine Wärmekamera bestätigt, dass sie nicht warm ist, "
                "wird sie von selbst zum Gegenstand (kein Alarm, der Kopf folgt nicht); ohne Wärmekamera bleibt sie eine Person, bis du "
                "«Ignorieren» drückst. Auf der Seite Live / Schutz (und im Fenster) erscheint ein Bild mit «Hier steht etwas, das wie eine Person aussieht – ignorieren?»: «Ignorieren» macht eine Maske "
                "(nur für Personen, bleibt beim Drehen des Kopfs am Platz), «Ist eine Person» lernt die Stelle nie mehr. Bewegt sich der Kasten "
                "deutlich oder kommt jemand dazu, gilt er sofort wieder als Person. Eine Person, die hingegangen ist und dann lange still steht, "
                "wird nie ignoriert. «Person (Wärmebild)» kommt nicht mehr bei einem fahrenden Auto (breiter, warmer Fleck, viel zu schnell für "
                "eine Person) oder wenn Kamera bzw. KI dort ein Fahrzeug oder Tier sehen. Hat die KI auf einer Spur einmal ein Tier gesehen (Hund, "
                "Katze, Schaf, Vogel …), bleibt die Spur ein Tier – keine Person aus Bewegung, «Person?» oder Wärmebild.</p>"),
               ('<section id="detect" data-icon="🎯"><h2>Detection</h2>',
                "<p><b>🌲 Still false persons, vehicles and animals:</b> when the AI sees a «person» at one place for minutes that does not move "
                "and never walked there (a small spruce, a tree trunk in the infrared light), MoveEye makes a suggestion after about 45 s (there "
                "at the start already) or 3 min. Only when a thermal camera confirms it is not warm does it become a thing by itself (no "
                "alarm, the head does not follow); without a thermal camera it stays a person until you tap «Ignore». The Live / Schutz "
                "page (and the window) shows a picture "
                "with «Something here looks like a person - ignore it?»: «Ignore» makes a mask (persons only, stays on its place when the head "
                "turns), «It is a person» never learns that place again. When the box moves clearly or somebody comes onto it, it is a person "
                "again at once. A person who walked there and then stands still for a long time is never ignored. «Person (thermal)» no longer "
                "comes for a driving car (wide warm body, far too fast for a person) or when the camera or the AI sees a vehicle or an animal "
                "there. Once the AI saw an animal on a track (dog, cat, sheep, bird …), the track stays an animal - no person from the "
                "movement, «Person?» or the thermal picture.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
