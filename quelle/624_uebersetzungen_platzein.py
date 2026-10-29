#@ MoveEye – Teil 624: Übersetzungen und Anleitung «Platz einrichten» (317, 537, 582) und «Blickwinkel der Kamera» (318). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_PLATZEIN = {
    'Set up the place': ('Platz einrichten', 'Configurer l’emplacement', 'Configurare il posto', 'Endrizzar il plaz'),
    '1 Look around': ('1 Umschauen', '1 Regarder autour', '1 Guardarsi intorno', '1 Guardar enturn'),
    '2 Mark': ('2 Markieren', '2 Marquer', '2 Segnare', '2 Marcar'),
    '3 Done': ('3 Fertig', '3 Terminé', '3 Fatto', '3 Fatg'),
    'Put MoveEye where it will guard. The head looks around once: it takes a photo in every direction and watches for about 10 seconds what moves and what the AI recognises. Then you only mark your tent, the access, your valuables and what to ignore.': (
        'Stell MoveEye dorthin, wo es bewachen soll. Der Kopf schaut sich einmal um: in jeder Richtung ein Foto und etwa 10 Sekunden beobachten, was sich bewegt und was die KI erkennt. Danach markierst du nur noch dein Zelt, den Zugang, deine Wertsachen und was ignoriert werden soll.',
        'Place MoveEye là où il doit surveiller. La tête regarde une fois autour : une photo dans chaque direction et environ 10 secondes pour voir ce qui bouge et ce que l’IA reconnaît. Ensuite tu marques seulement ta tente, l’accès, tes objets de valeur et ce qu’il faut ignorer.',
        'Metti MoveEye dove deve sorvegliare. La testa si guarda intorno una volta: una foto in ogni direzione e circa 10 secondi per osservare cosa si muove e cosa riconosce l’IA. Poi segni solo la tua tenda, l’accesso, gli oggetti di valore e cosa ignorare.',
        'Metta MoveEye là nua ch’el duai survegliar. Il chau guarda ina giada enturn: en mintga direcziun ina foto ed observar var 10 secundas tge che sa mova e tge che la IA enconuscha. Lura marcas ti mo anc tia tenda, l’access, tias chaussas da valur e tge ch’ins duai ignorar.'),
    'Pan range of the servo {servo}°, with the lens it sees {cover} (camera {hf}°).': (
        'Schwenkbereich des Servos {servo}°, mit dem Objektiv sieht MoveEye {cover} (Kamera {hf}°).',
        'Rotation du servo {servo}°, avec l’objectif MoveEye voit {cover} (caméra {hf}°).',
        'Rotazione del servo {servo}°, con l’obiettivo MoveEye vede {cover} (telecamera {hf}°).',
        'Rotaziun dal servo {servo}°, cun l’objectiv vesa MoveEye {cover} (camera {hf}°).'),
    'the whole circle (360°)': ('den ganzen Kreis (360°)', 'tout le cercle (360°)', 'tutto il cerchio (360°)', 'l’entir circul (360°)'),
    'No full turn: the head turns only as far as its servo goes.': (
        'Keine volle Drehung: der Kopf dreht nur so weit, wie sein Servo kann.', 'Pas de tour complet : la tête tourne seulement aussi loin que son servo.',
        'Nessun giro completo: la testa gira solo fin dove arriva il servo.', 'Nagina rotaziun cumplaina: il chau sa volva mo uschè lunsch sco ses servo po.'),
    '{n} directions in {rows} rows - about {min} minutes.': (
        '{n} Richtungen in {rows} Reihen – etwa {min} Minuten.', '{n} directions en {rows} rangées – environ {min} minutes.',
        '{n} direzioni in {rows} file – circa {min} minuti.', '{n} direcziuns en {rows} lingias – var {min} minutas.'),
    'Use the wide-angle camera ({cam}, {deg}°): {n} directions, about {min} min': (
        'Weitwinkel-Kamera nutzen ({cam}, {deg}°): {n} Richtungen, etwa {min} min', 'Utiliser la caméra grand angle ({cam}, {deg}°) : {n} directions, environ {min} min',
        'Usare la telecamera grandangolare ({cam}, {deg}°): {n} direzioni, circa {min} min', 'Duvrar la camera cun grond angul ({cam}, {deg}°): {n} direcziuns, var {min} min'),
    'Thorough: 3 rows instead of 2 (takes longer)': ('Gründlich: 3 Reihen statt 2 (dauert länger)', 'Minutieux : 3 rangées au lieu de 2 (plus long)',
                                                     'Accurato: 3 file invece di 2 (dura di più)', 'Precis: 3 lingias empè da 2 (dura pli ditg)'),
    'It is dark: the night reference is made now.': ('Es ist dunkel: jetzt entsteht die Nacht-Referenz.', 'Il fait nuit : la référence de nuit est faite maintenant.',
                                                     'È buio: ora si crea il riferimento notturno.', 'Igl è stgir: ussa vegn fatga la referenza da notg.'),
    'with the infrared light': ('mit dem Infrarot-Licht', 'avec la lumière infrarouge', 'con la luce infrarossa', 'cun la glisch infracotschna'),
    'with the thermal camera too': ('auch mit der Wärmebild-Kamera', 'aussi avec la caméra thermique', 'anche con la termocamera', 'er cun la camera termica'),
    'Start looking around': ('Umschauen starten', 'Commencer à regarder autour', 'Iniziare a guardarsi intorno', 'Cumenzar a guardar enturn'),
    'Show the last look-around': ('Letzten Rundblick zeigen', 'Montrer le dernier tour d’horizon', 'Mostrare l’ultimo giro', 'Mussar l’ultim sguard enturn'),
    'Place set up on {when}: {n} things marked': ('Platz eingerichtet am {when}: {n} Sachen markiert', 'Emplacement configuré le {when} : {n} éléments marqués',
                                                  'Posto configurato il {when}: {n} cose segnate', 'Plaz endrizzà ils {when}: {n} chaussas marcadas'),
    'Forget the place': ('Platz vergessen', 'Oublier l’emplacement', 'Dimenticare il posto', 'Emblidar il plaz'),
    'Forget the place? Its zones, waypoints and guarded things are removed.': (
        'Platz vergessen? Seine Zonen, Wegpunkte und bewachten Sachen werden entfernt.', 'Oublier l’emplacement ? Ses zones, points de passage et objets surveillés sont supprimés.',
        'Dimenticare il posto? Le sue zone, i punti di passaggio e gli oggetti sorvegliati vengono rimossi.', 'Emblidar il plaz? Sias zonas, ses puncts da via e las chaussas survegliadas vegnan allontanadas.'),
    'The head turns by itself - please do not stand in front of it.': ('Der Kopf dreht sich von selbst – bitte nicht davor stehen.', 'La tête tourne toute seule – ne reste pas devant.',
                                                                       'La testa gira da sola – per favore non stare davanti.', 'Il chau sa volva sez – per plaschair betg star davant.'),
    'taking the photo': ('Foto', 'photo', 'foto', 'foto'),
    'watching what moves': ('beobachtet, was sich bewegt', 'observe ce qui bouge', 'osserva cosa si muove', 'observa tge che sa mova'),
    'making the panorama': ('Panorama wird zusammengesetzt', 'assemblage du panorama', 'composizione del panorama', 'il panorama vegn cumponì'),
    'Direction {i} of {n}': ('Richtung {i} von {n}', 'Direction {i} sur {n}', 'Direzione {i} di {n}', 'Direcziun {i} da {n}'),
    'Tap a suggestion to take it, or choose a button and draw a box on the panorama with your finger. Swipe sideways with ✋.': (
        'Tipp einen Vorschlag an, um ihn zu übernehmen, oder wähle eine Taste und zieh mit dem Finger ein Rechteck auf dem Panorama. Mit ✋ seitwärts schieben.',
        'Touche une suggestion pour la prendre, ou choisis un bouton et dessine un rectangle sur le panorama avec le doigt. Avec ✋ faire défiler.',
        'Tocca un suggerimento per prenderlo, oppure scegli un pulsante e disegna un rettangolo sul panorama con il dito. Con ✋ scorrere di lato.',
        'Tutga ina proposta per la prender, u tscherna in buttun e dissegna cun il det in rectangul sin il panorama. Cun ✋ stuschar da la vart.'),
    'My tent / camper': ('Mein Zelt / Wohnmobil', 'Ma tente / camping-car', 'La mia tenda / camper', 'Mia tenda / auto da campadi'),
    'Access / path': ('Zugang / Weg', 'Accès / chemin', 'Accesso / sentiero', 'Access / via'),
    'Public path': ('Öffentlicher Weg', 'Chemin public', 'Sentiero pubblico', 'Via publica'),
    'Valuables': ('Wertsachen', 'Objets de valeur', 'Oggetti di valore', 'Chaussas da valur'),
    'Ignore': ('Ignorieren', 'Ignorer', 'Ignorare', 'Ignorar'),
    'Move / select': ('Schieben / wählen', 'Déplacer / choisir', 'Spostare / scegliere', 'Stuschar / tscherner'),
    'Show the thermal picture': ('Wärmebild zeigen', 'Montrer l’image thermique', 'Mostrare l’immagine termica', 'Mussar il maletg termic'),
    'suggestion - tap to take it': ('Vorschlag – antippen zum Übernehmen', 'suggestion – toucher pour la prendre', 'suggerimento – toccare per prenderlo', 'proposta – tutgar per la prender'),
    'marked': ('markiert', 'marqué', 'segnato', 'marcà'),
    'the picture goes on after the seam (360°)': ('das Bild geht nach der Naht weiter (360°)', 'l’image continue après la couture (360°)',
                                                  'l’immagine continua dopo la cucitura (360°)', 'il maletg cuntinuescha suenter la cusadira (360°)'),
    'Take all suggestions': ('Alle Vorschläge übernehmen', 'Prendre toutes les suggestions', 'Prendere tutti i suggerimenti', 'Prender tut las propostas'),
    'Nothing marked yet.': ('Noch nichts markiert.', 'Rien de marqué pour l’instant.', 'Ancora niente segnato.', 'Anc nagut marcà.'),
    'Remove': ('Entfernen', 'Supprimer', 'Rimuovere', 'Allontanar'),
    'public path = only report': ('öffentlicher Weg = nur melden', 'chemin public = seulement signaler', 'sentiero pubblico = solo segnalare', 'via publica = mo annunziar'),
    'Patrol: the head looks at the accesses now and then': ('Patrouille: der Kopf schaut ab und zu zu den Zugängen', 'Patrouille : la tête regarde de temps en temps les accès',
                                                            'Pattuglia: la testa guarda ogni tanto gli accessi', 'Patrulla: il chau guarda da temp en temp vers ils access'),
    'Apply': ('Übernehmen', 'Appliquer', 'Applicare', 'Applitgar'),
    'Look around again': ('Nochmals umschauen', 'Regarder autour à nouveau', 'Guardarsi intorno di nuovo', 'Guardar danovamain enturn'),
    'protection zone, lights / siren aim here, a person close by counts more': ('Schutzzone, Licht / Sirene zielen hierhin, eine Person in der Nähe zählt mehr',
                                                                               'zone de protection, lumière / sirène visent ici, une personne proche compte plus',
                                                                               'zona di protezione, luce / sirena puntano qui, una persona vicina conta di più',
                                                                               'zona da protecziun, glisch / sirena mirian qua, ina persuna datiers dumbra dapli'),
    'line: a person crossing it is reported + patrol point': ('Linie: wer sie überquert, wird gemeldet + Patrouillen-Punkt', 'ligne : qui la traverse est signalé + point de patrouille',
                                                              'linea: chi la attraversa viene segnalato + punto di pattuglia', 'lingia: tgi che la traversa vegn annunzià + punct da patrulla'),
    'persons there: only a note, no alarm': ('Personen dort: nur ein Hinweis, kein Alarm', 'personnes là : seulement une note, pas d’alarme',
                                             'persone lì: solo una nota, nessun allarme', 'persunas là: mo in avis, nagin alarm'),
    'guarded: in the morning «Bike missing»': ('bewacht: am Morgen «Velo fehlt»', 'surveillé : le matin « vélo manquant »', 'sorvegliato: al mattino «bici mancante»',
                                               'surveglià: la damaun «velo manca»'),
    'mask: movement there is ignored': ('Maske: Bewegung dort wird ignoriert', 'masque : le mouvement là est ignoré', 'maschera: il movimento lì viene ignorato',
                                        'mascra: moviment là vegn ignorà'),
    'The place is set up': ('Der Platz ist eingerichtet', 'L’emplacement est configuré', 'Il posto è configurato', 'Il plaz è endrizzà'),
    '{n} protection zone(s) at the tent': ('{n} Schutzzone(n) beim Zelt', '{n} zone(s) de protection à la tente', '{n} zona/e di protezione alla tenda', '{n} zona(s) da protecziun tar la tenda'),
    '{n} line(s) at the accesses': ('{n} Linie(n) bei den Zugängen', '{n} ligne(s) aux accès', '{n} linea/e agli accessi', '{n} lingia(s) tar ils access'),
    '{n} public path(s): only reported': ('{n} öffentliche(r) Weg(e): nur gemeldet', '{n} chemin(s) public(s) : seulement signalé', '{n} sentiero/i pubblico/i: solo segnalato',
                                          '{n} via(s) publica(s): mo annunzià'),
    '{n} mask(s): ignored': ('{n} Maske(n): ignoriert', '{n} masque(s) : ignoré', '{n} maschera/e: ignorata', '{n} mascra(s): ignorà'),
    '{n} patrol point(s)': ('{n} Patrouillen-Punkt(e)', '{n} point(s) de patrouille', '{n} punto/i di pattuglia', '{n} punct(s) da patrulla'),
    '{n} guarded thing(s) - reported in the morning when missing': ('{n} bewachte Sache(n) – am Morgen gemeldet, wenn sie fehlen',
                                                                    '{n} objet(s) surveillé(s) – signalé(s) le matin s’ils manquent',
                                                                    '{n} oggetto/i sorvegliato/i – segnalato al mattino se manca',
                                                                    '{n} chaussa(s) survegliada(s) – annunziada la damaun sch’ella manca'),
    'The guarded things follow after the reference scan of the main camera.': ('Die bewachten Sachen folgen nach dem Referenz-Scan der Hauptkamera.',
                                                                               'Les objets surveillés suivent après le scan de référence de la caméra principale.',
                                                                               'Gli oggetti sorvegliati seguono dopo la scansione di riferimento della telecamera principale.',
                                                                               'Las chaussas survegliadas suondan suenter il scan da referenza da la camera principala.'),
    '{n} zone(s) not made: at most 12 zones': ('{n} Zone(n) nicht erstellt: höchstens 12 Zonen', '{n} zone(s) non créée(s) : 12 zones au maximum',
                                               '{n} zona/e non creata/e: al massimo 12 zone', '{n} zona(s) betg fatga: maximalmain 12 zonas'),
    'Nothing marked - nothing changed.': ('Nichts markiert – nichts geändert.', 'Rien de marqué – rien changé.', 'Niente segnato – niente cambiato.', 'Nagut marcà – nagut midà.'),
    'Now test it: walk past like a visitor would. MoveEye beeps at every detection.': (
        'Jetzt testen: geh vorbei, wie es ein Besucher tun würde. MoveEye piepst bei jeder Erkennung.',
        'Maintenant teste : passe comme le ferait un visiteur. MoveEye bipe à chaque détection.',
        'Ora prova: passa come farebbe un visitatore. MoveEye emette un bip a ogni rilevamento.',
        'Ussa testar: va speravi sco in visitader. MoveEye fa bip tar mintga identificaziun.'),
    'Start the walk test': ('Gehtest starten', 'Démarrer le test de marche', 'Avviare il test di camminata', 'Cumenzar il test da chaminar'),
    'Look at the zones': ('Zonen ansehen', 'Voir les zones', 'Vedere le zone', 'Guardar las zonas'),
    'Back to Schutz': ('Zurück zu Schutz', 'Retour à Protection', 'Torna a Protezione', 'Enavos tar Protecziun'),
    'Bike': ('Velo', 'Vélo', 'Bici', 'Velo'), 'Motorbike': ('Motorrad', 'Moto', 'Moto', 'Moto'), 'Car': ('Auto', 'Voiture', 'Auto', 'Auto'),
    'Camper?': ('Wohnmobil?', 'Camping-car ?', 'Camper?', 'Auto da campadi?'), 'Chair': ('Stuhl', 'Chaise', 'Sedia', 'Sutga'), 'Bench': ('Bank', 'Banc', 'Panchina', 'Banc'),
    'Backpack': ('Rucksack', 'Sac à dos', 'Zaino', 'Satgados'), 'Suitcase': ('Koffer', 'Valise', 'Valigia', 'Valisch'), 'Bag': ('Tasche', 'Sac', 'Borsa', 'Tastga'),
    'Umbrella': ('Schirm', 'Parapluie', 'Ombrello', 'Umbrella'), 'Table': ('Tisch', 'Table', 'Tavolo', 'Maisa'), 'Path?': ('Weg?', 'Chemin ?', 'Sentiero?', 'Via?'),
    'Road?': ('Strasse?', 'Route ?', 'Strada?', 'Via?'), 'Moves by itself': ('Bewegt sich von selbst', 'Bouge tout seul', 'Si muove da solo', 'Sa mova sez'),
    'Place set up': ('Platz eingerichtet', 'Emplacement configuré', 'Posto configurato', 'Plaz endrizzà'),
    'things marked': ('Sachen markiert', 'éléments marqués', 'cose segnate', 'chaussas marcadas'),
    'MoveEye put up? Let it look around once: tent, access, valuables, what to ignore.': (
        'MoveEye hingestellt? Lass es sich einmal umschauen: Zelt, Zugang, Wertsachen, was ignoriert werden soll.',
        'MoveEye installé ? Laisse-le regarder une fois autour : tente, accès, objets de valeur, ce qu’il faut ignorer.',
        'MoveEye posizionato? Lascialo guardare intorno una volta: tenda, accesso, oggetti di valore, cosa ignorare.',
        'MoveEye plazzà? Al laschar guardar ina giada enturn: tenda, access, chaussas da valur, tge ignorar.'),
    'New place? Set it up again': ('Neuer Platz? Nochmals einrichten', 'Nouvel emplacement ? Le configurer à nouveau', 'Nuovo posto? Configurarlo di nuovo', 'Nov plaz? L’endrizzar danovamain'),
    'MoveEye put up? Set up the place': ('MoveEye hingestellt? Platz einrichten', 'MoveEye installé ? Configurer l’emplacement', 'MoveEye posizionato? Configurare il posto',
                                         'MoveEye plazzà? Endrizzar il plaz'),
    '2-3 minutes: the head looks around, you only tap tent, access, valuables.': ('2–3 Minuten: der Kopf schaut sich um, du tippst nur Zelt, Zugang, Wertsachen an.',
                                                                                 '2–3 minutes : la tête regarde autour, tu touches seulement tente, accès, objets de valeur.',
                                                                                 '2–3 minuti: la testa si guarda intorno, tu tocchi solo tenda, accesso, oggetti di valore.',
                                                                                 '2–3 minutas: il chau guarda enturn, ti tutgas mo tenda, access, chaussas da valur.'),
    'Later': ('Später', 'Plus tard', 'Più tardi', 'Pli tard'),
    'Field of view of the camera': ('Blickwinkel der Kamera', 'Angle de vue de la caméra', 'Angolo di visione della telecamera', 'Angul da vista da la camera'),
    'Main camera': ('Hauptkamera', 'Caméra principale', 'Telecamera principale', 'Camera principala'),
    'Extra camera': ('Zusatzkamera', 'Caméra supplémentaire', 'Telecamera aggiuntiva', 'Camera supplementara'),
    'from the simulator': ('aus dem Simulator', 'du simulateur', 'dal simulatore', 'dal simulatur'),
    'detected': ('erkannt', 'détecté', 'rilevato', 'identifitgà'),
    'not detected - Camera Module 3 assumed': ('nicht erkannt – Camera Module 3 angenommen', 'non détecté – Camera Module 3 supposé', 'non rilevato – si assume Camera Module 3',
                                               'betg identifitgà – Camera Module 3 supponì'),
    'chosen': ('gewählt', 'choisi', 'scelto', 'tschernì'), 'own value': ('eigener Wert', 'valeur propre', 'valore proprio', 'agen valur'),
    'standard': ('Standard', 'standard', 'standard', 'standard'),
    'sits on the head (turns with it) - for the panorama': ('sitzt auf dem Kopf (dreht mit) – für das Panorama', 'est sur la tête (tourne avec) – pour le panorama',
                                                             'è sulla testa (gira con essa) – per il panorama', 'è sin il chau (sa volva cun el) – per il panorama'),
    'Automatic': ('Automatisch', 'Automatique', 'Automatico', 'Automatic'),
    'HQ / other camera: own value': ('HQ / andere Kamera: eigener Wert', 'HQ / autre caméra : valeur propre', 'HQ / altra telecamera: valore proprio', 'HQ / autra camera: agen valur'),
    'Name': ('Name', 'Nom', 'Nome', 'Num'),
    'the place setup is already running': ('«Platz einrichten» läuft schon', '« Configurer l’emplacement » est déjà en cours', '«Configurare il posto» è già in corso',
                                           '«Endrizzar il plaz» è gia en funcziun'),
    'the walk test is running': ('der Gehtest läuft', 'le test de marche est en cours', 'il test di camminata è in corso', 'il test da chaminar è en funcziun'),
    'a scan is already running': ('ein Scan läuft schon', 'un scan est déjà en cours', 'una scansione è già in corso', 'in scan è gia en funcziun'),
    'no camera': ('keine Kamera', 'pas de caméra', 'nessuna telecamera', 'nagina camera'),
    'no picture from the camera': ('kein Bild von der Kamera', 'pas d’image de la caméra', 'nessuna immagine dalla telecamera', 'nagin maletg da la camera'),
    'stopped': ('abgebrochen', 'interrompu', 'interrotto', 'interrut'),
    'done': ('fertig', 'terminé', 'fatto', 'fatg'),
    'place setup': ('Platz einrichten', 'configuration de l’emplacement', 'configurazione del posto', 'endrizzar il plaz'),
    'Person on the public path (only reported, no alarm)': ('Person auf dem öffentlichen Weg (nur gemeldet, kein Alarm)', 'Personne sur le chemin public (seulement signalée, pas d’alarme)',
                                                            'Persona sul sentiero pubblico (solo segnalata, nessun allarme)', 'Persuna sin la via publica (mo annunziada, nagin alarm)'),
    'Cancel': ('Abbrechen', 'Annuler', 'Annulla', 'Interrumper'),
    'about': ('etwa', 'environ', 'circa', 'var'),
    'left': ('übrig', 'restant', 'rimanente', 'restant'),
}
for _k, _v in _HX_PLATZEIN.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

WEB_PAGE = WEB_PAGE.replace("<!--PLACEJS-->", _place_main_js(), 1)     # the script of 537 with the German texts

# ---- the manual: one chapter «Platz einrichten» in every language (before «Tipps») ------------------------------------
_HELP_PLATZEIN = {
    "de": '<section id="place" data-icon="📍"><h2>Platz einrichten</h2><ul>'
          '<li><b>Wann:</b> nach dem Hinstellen (beim ersten Start und wenn MoveEye an einem neuen Ort steht, schlägt es das selbst vor). Schutz → «📍 Platz einrichten» (Web und Fenster).</li>'
          '<li><b>1 Umschauen:</b> der Kopf fährt seinen ganzen Schwenkbereich in 2 (gründlich: 3) Reihen ab. Wie weit, hängt vom Servo und vom Objektiv ab: MG90S rund 180°, mit dem Objektiv der Camera Module 3 (66°) rund 240° – keine volle Drehung; ein 360°-Servo sieht den ganzen Kreis. In jeder Richtung ein Foto und etwa 10 Sekunden beobachten: was sich bewegt (Äste, Strasse, Licht) und was die KI sieht (Auto, Velo, Stuhl, Bank, Person …). 2–3 Minuten, «Abbrechen» jederzeit.</li>'
          '<li><b>Nachts:</b> mit Infrarot-Licht und Wärmebild – so passt die Nacht-Referenz. <b>Weitwinkel:</b> sitzt eine Zusatzkamera mit grösserem Blickwinkel auf dem Kopf, braucht der Rundblick weniger Schritte.</li>'
          '<li><b>2 Markieren:</b> auf dem Panorama die Vorschläge antippen oder mit einer Taste ein Rechteck ziehen: <b>⛺ Mein Zelt / Wohnmobil</b> (Schutzzone: wer dort länger bleibt, wird gemeldet; eine Person beim Zelt braucht keine zweite Bestätigung), <b>🚶 Zugang / Weg</b> (Linie + Patrouillen-Punkt; «öffentlicher Weg = nur melden»: Passanten lösen keinen Alarm aus, nur einen Hinweis), <b>🚲 Wertsachen</b> (bewacht vom Referenz-Scan: am Morgen «Velo fehlt»), <b>🌿 Ignorieren</b> (Maske).</li>'
          '<li><b>3 Fertig:</b> Zonen, Masken, Wegpunkte und bewachte Sachen entstehen von selbst; die Zonen bleiben an ihrem Platz, auch wenn der Kopf dreht. Danach gleich den <b>Gehtest</b> machen. Ändern: Schutz → Zonen, oder nochmals «Platz einrichten».</li>'
          '<li><b>📐 Blickwinkel der Kamera</b> (Einstellungen → Kamera / Servos): pro Kamera Camera Module 3 (66°), Module 3 Wide (102°), Module 2 (62°) oder ein eigener Wert; am Pi wird das Modell meist selbst erkannt, im Simulator kommt der Wert vom Simulator.</li></ul></section>\n\n',
    "en": '<section id="place" data-icon="📍"><h2>Set up the place</h2><ul>'
          '<li><b>When:</b> after putting MoveEye up (it suggests it itself on the first start and when it stands at a new place). Schutz → «📍 Set up the place» (web and window).</li>'
          '<li><b>1 Look around:</b> the head drives its whole pan range in 2 (thorough: 3) rows. How far depends on the servo and the lens: MG90S about 180°, with the lens of the Camera Module 3 (66°) about 240° – no full turn; a 360° servo sees the whole circle. In every direction a photo and about 10 seconds of watching: what moves (branches, road, lights) and what the AI sees (car, bike, chair, bench, person …). 2–3 minutes, «Cancel» at any time.</li>'
          '<li><b>At night:</b> with the infrared light and the thermal camera – so the night reference fits. <b>Wide angle:</b> when an extra camera with a wider view sits on the head, the look-around needs fewer steps.</li>'
          '<li><b>2 Mark:</b> tap the suggestions on the panorama or draw a box with a button: <b>⛺ My tent / camper</b> (protection zone: who stays there is reported; a person at the tent needs no second confirmation), <b>🚶 Access / path</b> (line + patrol point; «public path = only report»: passers-by raise no alarm, only a note), <b>🚲 Valuables</b> (guarded by the reference scan: «Bike missing» in the morning), <b>🌿 Ignore</b> (mask).</li>'
          '<li><b>3 Done:</b> zones, masks, waypoints and guarded things are made by themselves; the zones stay on their place when the head turns. Then do the <b>walk test</b>. To change: Schutz → zones, or «Set up the place» again.</li>'
          '<li><b>📐 Field of view of the camera</b> (Settings → Camera / Servos): per camera Camera Module 3 (66°), Module 3 Wide (102°), Module 2 (62°) or an own value; on the Pi the model is usually detected, in the simulator the value comes from the simulator.</li></ul></section>\n\n',
    "fr": '<section id="place" data-icon="📍"><h2>Configurer l’emplacement</h2><ul>'
          '<li><b>Quand :</b> après avoir installé MoveEye (il le propose lui-même au premier démarrage et à un nouvel endroit). Protection → « 📍 Configurer l’emplacement » (web et fenêtre).</li>'
          '<li><b>1 Regarder autour :</b> la tête parcourt toute sa rotation en 2 (minutieux : 3) rangées. MG90S environ 180°, avec l’objectif de la Camera Module 3 (66°) environ 240° – pas de tour complet ; un servo 360° voit tout le cercle. Dans chaque direction une photo et environ 10 secondes d’observation : ce qui bouge (branches, route, lumières) et ce que l’IA voit (voiture, vélo, chaise, banc, personne …). 2–3 minutes, « Annuler » à tout moment.</li>'
          '<li><b>La nuit :</b> avec la lumière infrarouge et la caméra thermique. <b>Grand angle :</b> une caméra supplémentaire plus large sur la tête demande moins d’étapes.</li>'
          '<li><b>2 Marquer :</b> toucher les suggestions sur le panorama ou dessiner un rectangle : <b>⛺ Ma tente / camping-car</b> (zone de protection), <b>🚶 Accès / chemin</b> (ligne + point de patrouille ; « chemin public = seulement signaler »), <b>🚲 Objets de valeur</b> (surveillés par le scan de référence : « vélo manquant » le matin), <b>🌿 Ignorer</b> (masque).</li>'
          '<li><b>3 Terminé :</b> zones, masques, points de passage et objets surveillés sont créés tout seuls ; les zones restent à leur place quand la tête tourne. Ensuite faire le <b>test de marche</b>.</li>'
          '<li><b>📐 Angle de vue de la caméra</b> (Réglages → Caméra / Servos) : par caméra Camera Module 3 (66°), Module 3 Wide (102°), Module 2 (62°) ou une valeur propre.</li></ul></section>\n\n',
    "it": '<section id="place" data-icon="📍"><h2>Configurare il posto</h2><ul>'
          '<li><b>Quando:</b> dopo aver posizionato MoveEye (lo propone da solo al primo avvio e in un posto nuovo). Protezione → «📍 Configurare il posto» (web e finestra).</li>'
          '<li><b>1 Guardarsi intorno:</b> la testa percorre tutta la sua rotazione in 2 (accurato: 3) file. MG90S circa 180°, con l’obiettivo della Camera Module 3 (66°) circa 240° – nessun giro completo; un servo a 360° vede tutto il cerchio. In ogni direzione una foto e circa 10 secondi di osservazione: cosa si muove (rami, strada, luci) e cosa vede l’IA (auto, bici, sedia, panchina, persona …). 2–3 minuti, «Annulla» in ogni momento.</li>'
          '<li><b>Di notte:</b> con la luce infrarossa e la termocamera. <b>Grandangolo:</b> una telecamera aggiuntiva più larga sulla testa richiede meno passi.</li>'
          '<li><b>2 Segnare:</b> toccare i suggerimenti sul panorama o disegnare un rettangolo: <b>⛺ La mia tenda / camper</b> (zona di protezione), <b>🚶 Accesso / sentiero</b> (linea + punto di pattuglia; «sentiero pubblico = solo segnalare»), <b>🚲 Oggetti di valore</b> (sorvegliati dalla scansione di riferimento: «bici mancante» al mattino), <b>🌿 Ignorare</b> (maschera).</li>'
          '<li><b>3 Fatto:</b> zone, maschere, punti di passaggio e oggetti sorvegliati nascono da soli; le zone restano al loro posto quando la testa gira. Poi fare il <b>test di camminata</b>.</li>'
          '<li><b>📐 Angolo di visione della telecamera</b> (Impostazioni → Telecamera / Servo): per telecamera Camera Module 3 (66°), Module 3 Wide (102°), Module 2 (62°) o un valore proprio.</li></ul></section>\n\n',
    "rm": '<section id="place" data-icon="📍"><h2>Endrizzar il plaz</h2><ul>'
          '<li><b>Cura:</b> suenter avair plazzà MoveEye (el propona quai sez tar l’emprima partenza e sin in nov lieu). Protecziun → «📍 Endrizzar il plaz» (web e fanestra).</li>'
          '<li><b>1 Guardar enturn:</b> il chau percurra tut sia rotaziun en 2 (precis: 3) lingias. MG90S var 180°, cun l’objectiv da la Camera Module 3 (66°) var 240° – nagina rotaziun cumplaina; in servo da 360° vesa l’entir circul. En mintga direcziun ina foto ed observar var 10 secundas: tge che sa mova (roma, via, glischs) e tge che la IA vesa (auto, velo, sutga, banc, persuna …). 2–3 minutas, «Interrumper» adina.</li>'
          '<li><b>La notg:</b> cun la glisch infracotschna e la camera termica. <b>Grond angul:</b> ina camera supplementara pli largia sin il chau basegna damain pass.</li>'
          '<li><b>2 Marcar:</b> tutgar las propostas sin il panorama u dissegnar in rectangul: <b>⛺ Mia tenda / auto da campadi</b> (zona da protecziun), <b>🚶 Access / via</b> (lingia + punct da patrulla; «via publica = mo annunziar»), <b>🚲 Chaussas da valur</b> (survegliadas dal scan da referenza: «velo manca» la damaun), <b>🌿 Ignorar</b> (mascra).</li>'
          '<li><b>3 Fatg:</b> zonas, mascras, puncts da via e chaussas survegliadas vegnan fatgas sezzas; las zonas restan en lur plaz, er sch’il chau sa volva. Lura far il <b>test da chaminar</b>.</li>'
          '<li><b>📐 Angul da vista da la camera</b> (Parameters → Camera / Servos): per camera Camera Module 3 (66°), Module 3 Wide (102°), Module 2 (62°) u in agen valur.</li></ul></section>\n\n',
}


def _help_platzein(doc, lang):
    if '<section id="place"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    if i < 0:
        i = doc.find('<section id="privacy"')
    return doc[:i] + _HELP_PLATZEIN[lang] + doc[i:] if i >= 0 else doc


_hp_en = HELP_PAGE.find('<div lang="en">')
if _hp_en > 0:
    HELP_PAGE = _help_platzein(HELP_PAGE[:_hp_en], "de") + _help_platzein(HELP_PAGE[_hp_en:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_platzein(HELP_X[_L], _L)
