#@ MoveEye – Teil 551: Namen der Simulator-Szenen in allen Sprachen (der Simulator schickt ab 3D-4.x zu jeder Szene «en» mit; Teile 139 / 470 / 549 zeigen damit den Namen in der Sprache der Seite) und die Anleitung der neuen Szenen «Voller Campingplatz», «Tarnen und Kriechen», «Velodieb». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_szenen = {
    'Campsite': ('Camping-Platz', 'Camping', 'Campeggio', 'Plaz da campadi'),
    'Forest': ('Wald', 'Forêt', 'Bosco', 'Guaud'),
    'Car park': ('Parkplatz', 'Parking', 'Parcheggio', 'Plaz da parcar'),
    'Garden / house': ('Garten / Haus', 'Jardin / maison', 'Giardino / casa', 'Curtin / chasa'),
    'Funny place': ('Lustiger Platz', 'Endroit amusant', 'Posto divertente', 'Plaz legher'),
    'Hide and seek (many hiding places)': ('Versteckspiel (viele Verstecke)', 'Cache-cache (beaucoup de cachettes)', 'Nascondino (molti nascondigli)', 'Giu da zuppar (bleras zuppadas)'),
    'Place from the map (Switzerland)': ('Ort von der Karte (Schweiz)', 'Lieu de la carte (Suisse)', 'Luogo dalla mappa (Svizzera)', 'Lieu da la charta (Svizra)'),
    'My home (self-built)': ('Mein Zuhause (selbst gebaut)', 'Ma maison (construite moi-même)', 'La mia casa (costruita da me)', 'Mia chasa (construida sez)'),
    'Farm': ('Bauernhof', 'Ferme', 'Fattoria', 'Bain puril'),
    'Lake shore with jetty': ('Seeufer mit Steg', 'Rive du lac avec ponton', 'Riva del lago con pontile', 'Riva dal lai cun punt'),
    'Building site': ('Baustelle', 'Chantier', 'Cantiere', 'Plazza da construcziun'),
    'Camper van site': ('Wohnmobil-Stellplatz', 'Aire de camping-cars', 'Area camper', 'Plaz per autos da campadi'),
    'My template (3D file)': ('Meine Vorlage (3D-Datei)', 'Mon modèle (fichier 3D)', 'Il mio modello (file 3D)', 'Mes model (datoteca 3D)'),
    'Bedroom (wake-up alarm)': ('Schlafzimmer (Wecker)', 'Chambre (réveil)', 'Camera da letto (sveglia)', 'Stanza da durmir (svegliarin)'),
    'Full campsite': ('Voller Campingplatz', 'Camping plein', 'Campeggio pieno', 'Plaz da campadi plain'),
    'Camouflage and crawling': ('Tarnen und Kriechen', 'Camouflage et ramper', 'Mimetizzarsi e strisciare', 'Camuflar e sa trair'),
    'Bike thief': ('Velodieb', 'Voleur de vélo', 'Ladro di bici', 'Lader da velo'),
    'Tracking course': ('Verfolgungs-Parcours', 'Parcours de suivi', 'Percorso di inseguimento', 'Parcours da persequitar'),
    'Holiday park by the lake': ('Ferienpark am See', 'Parc de vacances au bord du lac', 'Parco vacanze sul lago', 'Parc da vacanzas al lai'),
}
# German comes from the simulator itself (and DE is only made in part 560, after this part) - here only fr / it / rm
for _k, _v in _HX_szenen.items():
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (DE / EN): the three new scenes of the simulator, in the section «Erkennung» / «Detection»
for _a, _b in (('<section id="detect" data-icon="🎯"><h2>Erkennung</h2>',
                "<p><b>🏕 Neue Simulator-Szenen (Simulator 3D-4.x):</b> Drei Szenen üben gezielt Schwächen der Erkennung. "
                "<i>Voller Campingplatz</i>: viele harmlose Nachbarn kochen, gehen zum WC, Kinder spielen, jemand führt den Hund aus – nur "
                "wer an <i>deinen</i> Platz kommt, zählt (gut zum Einstellen der Zonen und von «Dein Platz»). <i>Tarnen und Kriechen</i>: "
                "Tarnkleidung in der Farbe des Bodens, Robben, Schirm und Karton. <i>Velodieb</i>: schnell hin, Velo greifen (der Velo-Sensor "
                "meldet sich), weg – gemessen wird die Reaktionszeit. Jede Szene hat einen festen Prüfstand-Lauf (camping_voll, tarnen, "
                "velodieb; nicht im kurzen Lauf, sondern sonntags oder von Hand) und im Spiel-Assistenten ein passendes Spiel.</p>"),
               ('<section id="detect" data-icon="🎯"><h2>Detection</h2>',
                "<p><b>🏕 New simulator scenes (simulator 3D-4.x):</b> three scenes train weak points of the detection. "
                "<i>Full campsite</i>: many harmless neighbours cook, walk to the toilets, children play, someone walks the dog – only who "
                "comes to <i>your</i> pitch counts (good for setting up zones and «Your place»). <i>Camouflage and crawling</i>: camouflage "
                "clothes in the colour of the ground, crawling, umbrella and cardboard box. <i>Bike thief</i>: fast in, grab the bike (the "
                "bike sensor reports), away – the reaction time is measured. Every scene has a fixed test-bench run (camping_voll, tarnen, "
                "velodieb; not in the short run but on Sundays or by hand) and a matching game in the game assistant.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
