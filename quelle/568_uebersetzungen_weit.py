#@ MoveEye – Teil 568: Übersetzungen und Anleitung der Weitwinkel-Kamera im Simulator (Teile 163 / 591). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_weit = {
    'Wide infrared light (channel 4): second IR LED 120° on PCA9685 channel 4, on / off with the infrared light':
        ('IR-Licht breit (Kanal 4): zweite IR-LED 120° an PCA9685 Kanal 4, ein / aus mit dem Infrarotlicht',
         'Lumière IR large (canal 4) : deuxième LED IR 120° sur le canal 4 du PCA9685, allumée / éteinte avec la lumière infrarouge',
         'Luce IR ampia (canale 4): seconda LED IR 120° sul canale 4 del PCA9685, accesa / spenta con la luce infrarossa',
         'Glisch IR largia (chanal 4): segunda LED IR 120° sin il chanal 4 dal PCA9685, en / ora cun la glisch infraritga'),
    'Simulator wide camera': ('Simulator-Weitwinkel', 'Grand-angle du simulateur', 'Grandangolo del simulatore', 'Grond angul dal simulatur'),
    'Wide camera': ('Weitwinkel-Kamera', 'Caméra grand-angle', 'Telecamera grandangolare', 'Camera da grond angul'),
    'In the case (v5.2)': ('Im Gehäuse (v5.2)', 'Dans le boîtier (v5.2)', 'Nella custodia (v5.2)', 'En la chaschetta (v5.2)'),
    'Not installed (blind cover)': ('Nicht verbaut (Blindstopfen)', 'Non montée (cache)', 'Non montata (tappo cieco)', 'Betg montada (zaffer)'),
    'Not installed (blind cover) - no wide picture': ('Nicht verbaut (Blindstopfen) – kein Weitwinkel-Bild',
        'Non montée (cache) – pas d’image grand-angle', 'Non montata (tappo cieco) – nessuna immagine grandangolare',
        'Betg montada (zaffer) – nagin maletg da grond angul'),
    'Mast (scene)': ('Mast (Szene)', 'Mât (scène)', 'Palo (scena)', 'Pal (scena)'),
    'Base front, fixed': ('Unterteil vorne, fest', 'Socle avant, fixe', 'Base davanti, fissa', 'Part sut davant, fixa'),
    'Head front': ('Kopf vorne', 'Tête avant', 'Testa davanti', 'Chau davant'),
    'Head rear': ('Kopf hinten', 'Tête arrière', 'Testa dietro', 'Chau davos'),
    'The wide camera is not an extra camera of MoveEye': ('Die Weitwinkel-Kamera ist keine Zusatzkamera von MoveEye',
        'La caméra grand-angle n’est pas une caméra supplémentaire de MoveEye', 'La telecamera grandangolare non è una telecamera aggiuntiva di MoveEye',
        'La camera da grond angul n’è betg ina camera supplementara da MoveEye'),
    'On the mast: not part of the device - it does not steer the head by itself.': ('Am Mast: nicht Teil des Geräts – lenkt den Kopf nicht von selbst.',
        'Sur le mât : ne fait pas partie de l’appareil – ne dirige pas la tête d’elle-même.', 'Sul palo: non fa parte dell’apparecchio – non guida la testa da sola.',
        'Al pal: na fa betg part da l’apparat – na maina betg il chau da sasez.'),
    'Steers the head as overview («The overview camera steers the head»)': ('Lenkt den Kopf als Übersicht («Übersicht lenkt den Kopf»)',
        'Dirige la tête comme vue d’ensemble (« La vue d’ensemble dirige la tête »)', 'Guida la testa come panoramica («La panoramica guida la testa»)',
        'Maina il chau sco survista («La survista maina il chau»)'),
    'Overview chosen by hand - not changed.': ('Übersicht von Hand gewählt – bleibt so.', 'Vue d’ensemble choisie à la main – reste ainsi.',
        'Panoramica scelta a mano – resta così.', 'Survista tschernida a maun – resta uschia.'),
}
for _k, _v in _HX_weit.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (HELP_PAGE of 540): one paragraph in the section «Kamera & Servos», German and English
for _a, _b in (('<section id="camera" data-icon="📷"><h2>Kamera &amp; Servos</h2>',
                "<p><b>🔭 Weitwinkel-Kamera im Simulator (Simulator 3D-4.17):</b> Die frühere «feste Kamera» des Simulators ist jetzt die "
                "Weitwinkel-Kamera (Camera Module 3 Wide NoIR, 102° × 67°). Unter Simulator → Kamerabild → «Weitwinkel-Kamera» oder in der "
                "Kachel 🔭 wählst du die Montage: <i>Mast (Szene)</i> wie bisher, <i>Unterteil vorne, fest</i> (10–15° nach unten), "
                "<i>Kopf vorne</i> oder <i>Kopf hinten</i> (dreht mit). Sitzt sie am Gerät, stellt MoveEye «Übersicht lenkt den Kopf» selbst "
                "ein: Bewegung im Weitwinkel-Bild dreht den Kopf dorthin, dann prüft die KI der Hauptkamera; solange der Kopf dreht, zählt "
                "die Bewegung im Weitwinkel-Bild nicht. Auf dem Kopf gilt eine Drehgrenze (Kabel; 360°-Servos bräuchten einen Schleifring). "
                "Die zweite IR-LED 120° schaltest du mit «IR-Licht breit (Kanal 4)» unter Licht.</p>"
                "<p><b>Im Gehäuse (v5.2):</b> Standard-Montage im Simulator – wie das echte Gehäuse v5.2: fest in der Stirnwand über "
                "dem PIR, 12° nach unten, der Kopf dreht darüber. Das Bild ist ein Fischauge (120° diagonal, gebogene Linien am Rand, "
                "dunklere Ecken); nachts beleuchtet die kleine 5-mm-IR-LED (Kanal 4) nur die Nähe (ca. 4 m). "
                "<i>Nicht verbaut (Blindstopfen)</i>: kein Weitwinkel-Bild, die Zusatzkamera meldet «nicht verbaut».</p>"),
               ('<section id="camera" data-icon="📷"><h2>Camera &amp; servos</h2>',
                "<p><b>🔭 Wide camera in the simulator (simulator 3D-4.17):</b> the former «fixed camera» of the simulator is now the wide "
                "camera (Camera Module 3 Wide NoIR, 102° × 67°). In Simulator → camera picture → «Weitwinkel-Kamera» or with the tile 🔭 "
                "you choose its mount: <i>mast (scene)</i> as before, <i>base front, fixed</i> (10–15° down), <i>head front</i> or "
                "<i>head rear</i> (turns with the head). On the device MoveEye sets «The overview camera steers the head» by itself: "
                "movement in the wide picture turns the head there, then the AI of the main camera checks; while the head turns, movement "
                "in the wide picture does not count. On the head a pan limit applies (cable; 360° servos would need a slip ring). The "
                "second IR LED 120° is switched with «Wide infrared light (channel 4)» under Lights.</p>"
                "<p><b>In the case (v5.2):</b> the default mount in the simulator - like the real case v5.2: fixed in the front wall "
                "above the PIR, 12° down, the head turns above it. The picture is a fisheye (120° diagonal, bent lines at the edges, "
                "darker corners); at night the small 5 mm IR LED (channel 4) lights only the near field (about 4 m). "
                "<i>Not installed (blind cover)</i>: no wide picture, the extra camera says «not installed».</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
