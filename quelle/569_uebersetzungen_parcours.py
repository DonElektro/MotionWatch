#@ MoveEye – Teil 569: Übersetzungen und Anleitung des Verfolgungs-Parcours (Teile 416 / 599). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_parc = {
    'Tracking parcours': ('Verfolgungs-Parcours', 'Parcours de suivi', 'Percorso di inseguimento', 'Parcours da persequitar'),
    'tracking parcours': ('Verfolgungs-Parcours', 'parcours de suivi', 'percorso di inseguimento', 'parcours da persequitar'),
    'Train the following': ('Folgen üben', 'Entraîner le suivi', 'Allenare l’inseguimento', 'Exercitar il suandar'),
    'Tracking: look ahead (seconds, 0 = off)': ('Folgen: vorausschauen (Sekunden, 0 = aus)', 'Suivi : anticiper (secondes, 0 = désactivé)',
                                                'Inseguimento: anticipare (secondi, 0 = spento)', 'Suandar: guardar ordavant (secundas, 0 = ora)'),
    'not supported - update the simulator': ('nicht unterstützt – Simulator aktualisieren', 'non pris en charge – mets à jour le simulateur',
                                             'non supportato – aggiorna il simulatore', 'betg sustegnì – actualisescha il simulatur'),
    'Night (lesson 8)': ('Nacht (Lektion 8)', 'Nuit (leçon 8)', 'Notte (lezione 8)', 'Notg (lecziun 8)'),
    'Start': ('Starten', 'Démarrer', 'Avvia', 'Cumenzar'),
    'Stop': ('Stopp', 'Stop', 'Stop', 'Stop'),
    'lesson': ('Lektion', 'leçon', 'lezione', 'lecziun'),
    'Lesson': ('Lektion', 'Leçon', 'Lezione', 'Lecziun'),
    'Regulators of the following (live)': ('Regler der Verfolgung (live)', 'Réglages du suivi (en direct)', 'Regolazioni dell’inseguimento (dal vivo)', 'Reguladers dal suandar (live)'),
    'Speed (°/s)': ('Tempo (°/s)', 'Vitesse (°/s)', 'Velocità (°/s)', 'Sveltezza (°/s)'),
    'Gain': ('Verstärkung', 'Gain', 'Guadagno', 'Rinforz'),
    'Dead zone': ('Totzone', 'Zone morte', 'Zona morta', 'Zona morta'),
    'Look ahead (s)': ('Vorausschauen (s)', 'Anticiper (s)', 'Anticipare (s)', 'Guardar ordavant (s)'),
    'parc-reg-note': ('Dieselben Einstellungen wie unter Einstellungen → Kamera / Servos und «Servo-Bewegung & Sicherheit». Vorausschauen 0 = wie bisher.',
                      'Les mêmes réglages que sous Réglages → Caméra / servos et «Mouvement des servos & sécurité». Anticiper 0 = comme avant.',
                      'Le stesse impostazioni di Impostazioni → Telecamera / servo e «Movimento servo & sicurezza». Anticipare 0 = come prima.',
                      'Ils medems parameters sco sut Parameters → Camera / servos e «Moviment dals servos & segirezza». Guardar ordavant 0 = sco fin ussa.'),
    'Last run': ('Letzter Lauf', 'Dernier essai', 'Ultima prova', 'Ultima prova'),
    'grade': ('Note', 'note', 'voto', 'nota'),
    'aim error': ('Zielfehler', 'erreur de visée', 'errore di mira', 'sbagl da mira'),
    'in the picture': ('im Bild', 'dans l’image', 'nell’immagine', 'en il maletg'),
    'losses': ('Verluste', 'pertes', 'perdite', 'perditas'),
    'swinging': ('Pendeln', 'oscillation', 'oscillazione', 'pendular'),
    'servo travel': ('Servo-Weg', 'course des servos', 'corsa dei servo', 'via dals servos'),
    'switches': ('Verwechslungen', 'confusions', 'scambi', 'confusiuns'),
    'learning pictures (picture data only)': ('Lernbilder (nur Bilddaten)', 'images d’apprentissage (données d’image seulement)',
                                              'immagini di apprendimento (solo dati d’immagine)', 'maletgs d’emprender (mo datas da maletg)'),
    'A/B comparison': ('A/B-Vergleich', 'Comparaison A/B', 'Confronto A/B', 'Cumparegliaziun A/B'),
    'A/B run': ('A/B-Lauf', 'Essai A/B', 'Prova A/B', 'Prova A/B'),
    'Compare': ('Vergleichen', 'Comparer', 'Confronta', 'Cumparegliar'),
    'No clear difference.': ('Kein klarer Unterschied.', 'Pas de différence nette.', 'Nessuna differenza chiara.', 'Nagina differenza clera.'),
    'B is better.': ('B ist besser.', 'B est meilleur.', 'B è migliore.', 'B è meglier.'),
    'A is better.': ('A ist besser.', 'A est meilleur.', 'A è migliore.', 'A è meglier.'),
    'Nothing is changed by itself.': ('Es wird nichts von selbst geändert.', 'Rien n’est modifié tout seul.', 'Niente viene cambiato da solo.', 'Nagut na vegn midà da sasez.'),
    'Auto-tuning': ('Auto-Tuning', 'Réglage automatique', 'Taratura automatica', 'Reglaziun automatica'),
    'Try values (short, lessons as chosen)': ('Werte durchprobieren (kurz, gewählte Lektionen)', 'Essayer des valeurs (court, leçons choisies)',
                                              'Provare valori (breve, lezioni scelte)', 'Empruvar valurs (curt, lecziuns tschernidas)'),
    'Values': ('Werte', 'Valeurs', 'Valori', 'Valurs'),
    'now': ('jetzt', 'maintenant', 'ora', 'ussa'),
    'take over proposal ★': ('Vorschlag ★ übernehmen', 'reprendre la proposition ★', 'adottare la proposta ★', 'surpigliar la proposta ★'),
    'taken over': ('übernommen', 'repris', 'adottato', 'surpiglià'),
    'The values now are the best - nothing to change.': ('Die jetzigen Werte sind die besten – nichts zu ändern.', 'Les valeurs actuelles sont les meilleures – rien à changer.',
                                                         'I valori attuali sono i migliori – niente da cambiare.', 'Las valurs actualas èn las meglras – nagut da midar.'),
    'Only a proposal - nothing was changed.': ('Nur ein Vorschlag – es wurde nichts geändert.', 'Seulement une proposition – rien n’a été modifié.',
                                               'Solo una proposta – niente è stato cambiato.', 'Mo ina proposta – nagut n’è vegnì midà.'),
    'With / without wide-angle hand-over': ('Mit / ohne Weitwinkel-Übergabe', 'Avec / sans relais grand-angle', 'Con / senza passaggio grandangolo', 'Cun / senza surdada grond angul'),
    'Compare (mount now)': ('Vergleichen (jetzige Montage)', 'Comparer (montage actuel)', 'Confronta (montaggio attuale)', 'Cumparegliar (montascha actuala)'),
    'the overview steers the head only when the protection is on (Wachsam / Voll)': (
        'die Übersicht lenkt den Kopf nur bei eingeschaltetem Schutz (Wachsam / Voll)', 'la vue d’ensemble ne dirige la tête que si la protection est active (Wachsam / Voll)',
        'la panoramica guida la testa solo con la protezione attiva (Wachsam / Voll)', 'la survista maina il chau mo cun la protecziun activa (Wachsam / Voll)'),
    'the wide camera is not an extra camera of MoveEye': ('die Weitwinkel-Kamera ist keine Zusatzkamera von MoveEye', 'la caméra grand-angle n’est pas une caméra supplémentaire de MoveEye',
                                                          'la telecamera grandangolare non è una telecamera aggiuntiva di MoveEye', 'la camera da grond angul n’è nagina camera supplementara da MoveEye'),
    'with hand-over': ('mit Übergabe', 'avec relais', 'con passaggio', 'cun surdada'),
    'without hand-over': ('ohne Übergabe', 'sans relais', 'senza passaggio', 'senza surdada'),
    'Game «Escape the camera»': ('Spiel «Entkomme der Kamera»', 'Jeu «Échappe à la caméra»', 'Gioco «Sfuggi alla telecamera»', 'Gieu «Fugia da la camera»'),
    'Name': ('Name', 'Nom', 'Nome', 'Num'),
    'Play (60 s)': ('Spielen (60 s)', 'Jouer (60 s)', 'Gioca (60 s)', 'Giugar (60 s)'),
    'Bot': ('Bot', 'Bot', 'Bot', 'Bot'),
    'parc-game-note': ('Steuere die Figur mit dem Mover-Stick (Live-Seite; ohne Mover «Stick zum Testen» einschalten) oder im Simulator mit dem Stick. 10 Punkte pro Sekunde ausserhalb des Bilds, 5 verdeckt, 100 pro Verlust – nur 4 bis 25 m vom Gerät. Zählt in der Rangliste des Abends.',
                       'Dirige la silhouette avec le stick du Mover (page Live ; sans Mover, active «stick pour tester») ou avec le stick du simulateur. 10 points par seconde hors de l’image, 5 caché, 100 par perte – seulement de 4 à 25 m de l’appareil. Compte dans le classement de la soirée.',
                       'Guida la figura con lo stick del Mover (pagina Live; senza Mover attiva «stick per provare») o con lo stick nel simulatore. 10 punti al secondo fuori dall’immagine, 5 nascosto, 100 per perdita – solo da 4 a 25 m dall’apparecchio. Conta nella classifica della serata.',
                       'Maina la figura cun il stick dal Mover (pagina Live; senza Mover activar «stick per empruvar») u cun il stick en il simulatur. 10 puncts per secunda ordaifer il maletg, 5 zuppà, 100 per perdita – mo 4 fin 25 m da l’apparat. Quinta en la glista da rang da la saira.'),
    'points': ('Punkte', 'points', 'punti', 'puncts'),
    'out of the picture': ('aus dem Bild', 'hors de l’image', 'fuori dall’immagine', 'ordaifer il maletg'),
    'lost': ('verloren', 'perdu', 'perso', 'pers'),
    'Overlay in the simulator': ('Einblendung im Simulator', 'Superposition dans le simulateur', 'Sovrapposizione nel simulatore', 'Surposiziun en il simulatur'),
    'Ring round the device': ('Ring rund ums Gerät', 'Anneau autour de l’appareil', 'Anello intorno all’apparecchio', 'Rintg enturn l’apparat'),
    'Collect learning pictures': ('Lernbilder sammeln', 'Collecter des images d’apprentissage', 'Raccogliere immagini di apprendimento', 'Rimnar maletgs d’emprender'),
    'parc-note': ('Der Simulator kennt die echten Wege der Figuren und misst genau: Zielfehler (Mitte der Figur gegen Bildmitte der Kopfkamera), Zeit im Bild, Verluste und Wiederfinde-Zeit, Pendeln / Überschwingen, Servo-Weg, Verwechslungen → Note 1–6. Während eines Laufs: Folgen ein, schlaue Runde aus – danach wie vorher.',
                  'Le simulateur connaît les vrais chemins des silhouettes et mesure exactement : erreur de visée, temps dans l’image, pertes et temps pour retrouver, oscillation / dépassement, course des servos, confusions → note 1–6. Pendant un essai : suivi activé, ronde intelligente désactivée – ensuite comme avant.',
                  'Il simulatore conosce i veri percorsi delle figure e misura con precisione: errore di mira, tempo nell’immagine, perdite e tempo per ritrovare, oscillazione / superamento, corsa dei servo, scambi → voto 1–6. Durante una prova: inseguimento attivo, giro intelligente spento – poi come prima.',
                  'Il simulatur enconuscha las vias veras da las figuras e mesira exactamain: sbagl da mira, temp en il maletg, perditas e temp per chattar puspè, pendular / surpassar, via dals servos, confusiuns → nota 1–6. Durant ina prova: suandar en, runda intelligenta ora – suenter sco avant.'),
    'Look ahead 0.3 s': ('Vorausschauen 0,3 s', 'Anticiper 0,3 s', 'Anticipare 0,3 s', 'Guardar ordavant 0,3 s'),
    'Gain +40 %': ('Verstärkung +40 %', 'Gain +40 %', 'Guadagno +40 %', 'Rinforz +40 %'),
    'Dead zone 0.05': ('Totzone 0,05', 'Zone morte 0,05', 'Zona morta 0,05', 'Zona morta 0,05'),
    'Speed 200 °/s': ('Tempo 200 °/s', 'Vitesse 200 °/s', 'Velocità 200 °/s', 'Sveltezza 200 °/s'),
    'Slowly across the picture': ('Langsam quer durchs Bild', 'Lentement à travers l’image', 'Lentamente attraverso l’immagine', 'Plaun traversond il maletg'),
    'Towards the camera / away': ('Auf die Kamera zu / weg', 'Vers la caméra / s’éloigner', 'Verso la telecamera / via', 'Vers la camera / davent'),
    'Zigzag and changes of speed': ('Zickzack und Tempowechsel', 'Zigzag et changements de vitesse', 'Zigzag e cambi di velocità', 'Zigzag e midadas da sveltezza'),
    'Stop and go on': ('Stopp und Weiterlaufen', 'Arrêt et reprise', 'Stop e ripartenza', 'Fermar e cuntinuar'),
    'Hidden behind obstacles': ('Verdeckung hinter Hindernissen', 'Caché derrière des obstacles', 'Nascosto dietro ostacoli', 'Zuppà davos impediments'),
    'Two persons cross': ('Zwei Personen kreuzen sich', 'Deux personnes se croisent', 'Due persone si incrociano', 'Duas persunas sa cruschan'),
    'Animal: fox / deer, fast and irregular': ('Tier: Fuchs / Reh, schnell und unregelmässig', 'Animal : renard / chevreuil, rapide et irrégulier',
                                               'Animale: volpe / capriolo, veloce e irregolare', 'Animal: vulp / chaura, svelt e irregular'),
    'Night run with infrared': ('Nacht-Durchgang mit Infrarot', 'Passage de nuit avec infrarouge', 'Passaggio notturno con infrarossi', 'Passadi da notg cun infracotschen'),
    'stopped': ('abgebrochen', 'interrompu', 'interrotto', 'interrut'),
    'the tracking parcours is running': ('der Verfolgungs-Parcours läuft', 'le parcours de suivi est en cours', 'il percorso di inseguimento è in corso', 'il parcours da persequitar è en funcziun'),
    'no result from the simulator': ('kein Ergebnis vom Simulator', 'pas de résultat du simulateur', 'nessun risultato dal simulatore', 'nagin resultat dal simulatur'),
    'no proposal': ('kein Vorschlag', 'pas de proposition', 'nessuna proposta', 'nagina proposta'),
    'the simulator did not start the parcours': ('der Simulator hat den Parcours nicht gestartet', 'le simulateur n’a pas démarré le parcours',
                                                 'il simulatore non ha avviato il percorso', 'il simulatur n’ha betg cumenzà il parcours'),
    'Train following in the simulator: lessons, A/B comparison, auto-tuning (proposal only).': (
        'Folgen im Simulator üben: Lektionen, A/B-Vergleich, Auto-Tuning (nur Vorschlag).', 'Entraîner le suivi dans le simulateur : leçons, comparaison A/B, réglage automatique (proposition seulement).',
        'Allenare l’inseguimento nel simulatore: lezioni, confronto A/B, taratura automatica (solo proposta).', 'Exercitar il suandar en il simulatur: lecziuns, cumparegliaziun A/B, reglaziun automatica (mo proposta).'),
    'browser': ('Browser', 'navigateur', 'browser', 'navigatur'),
}
for _k, _v in _HX_parc.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (HELP_PAGE of 540): one paragraph in the section «Kamera & Servos», German and English
for _a, _b in (('<section id="camera" data-icon="📷"><h2>Kamera &amp; Servos</h2>',
                "<p><b>🎯 Verfolgungs-Parcours (Simulator):</b> In der Simulator-Zentrale (Gruppe «Testen», Kachel 🎯) oder im Simulator-Fenster "
                "(Karte «Testlauf» → «Verfolgungs-Parcours») übst du das Folgen des Kopfs: Lektionen 1–7 (langsam quer, zu / weg, Zickzack mit "
                "Tempowechsel bis Velo, Stopp und Weiterlaufen, Verdeckung hinter Busch und Zelt, zwei Personen kreuzen, Fuchs / Reh) und Lektion 8 "
                "= dieselben nachts mit Infrarot. Der Simulator kennt die echten Wege und misst Zielfehler, Zeit im Bild, Verluste, Pendeln, "
                "Servo-Weg und Verwechslungen → Note 1–6. Die Regler (Tempo, Verstärkung, Totzone, Vorausschauen) sind dieselben wie unter "
                "Kamera / Servos; <i>Vorausschauen 0</i> = wie bisher. Der A/B-Vergleich zeigt zwei Läufe nebeneinander, das Auto-Tuning probiert "
                "Werte durch und <b>schlägt nur vor</b> («übernehmen»). Spiel «Entkomme der Kamera»: mit dem Stick raus aus dem Bild – Punkte in der "
                "Rangliste des Abends.</p>"),
               ('<section id="camera" data-icon="📷"><h2>Camera &amp; servos</h2>',
                "<p><b>🎯 Tracking parcours (simulator):</b> in the Simulator centre (group «Testen», tile 🎯) or in the simulator window (card "
                "«Testlauf» → «Verfolgungs-Parcours») you train the following of the head: lessons 1–7 (slowly across, towards / away, zigzag with "
                "changes of speed up to the bike, stop and go, hidden behind bush and tent, two persons crossing, fox / deer) and lesson 8 = the same "
                "at night with infrared. The simulator knows the real paths and measures aim error, time in the picture, losses, swinging, servo "
                "travel and identity switches → grade 1–6. The regulators (speed, gain, dead zone, look ahead) are the same as under Camera / servos; "
                "<i>look ahead 0</i> = as before. The A/B comparison shows two runs side by side, the auto-tuning tries values and <b>only "
                "proposes</b> («take over»). Game «Escape the camera»: get out of the picture with the stick – points in the ranking of the evening.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
