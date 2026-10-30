#@ MoveEye – Teil 632: Übersetzungen der Aufräum-Runde (Servos an einem Ort, Kurzbefehl-Schlüssel = App-Schlüssel, Zonen «nur melden» / «bleibt am Platz», Abschrecken mit Ziel, Tierart-Gruppe …). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# English key: (Deutsch, Français, Italiano, Rumantsch). At the end the German texts go into the pages that have their own
# dictionary (main page 530: /*AUFRDE*/ and /*AUFREN*/ for the code keys, zone editor 520: /*ZAUFRDE*/).
# ----------------------------------------------------------------------------
_HX_AUFR = {
    # 1: Servos - one entry (positions, test, diagnosis)
    'Positions, test, diagnosis, Not-Aus': ('Positionen, Test, Diagnose, Not-Aus', 'Positions, test, diagnostic, arrêt d’urgence', 'Posizioni, test, diagnosi, arresto d’emergenza', 'Posiziuns, test, diagnosa, stop d’urgenza'),
    'Test': ('Test', 'Test', 'Test', 'Test'),
    'Servos: safety, positions, test, diagnosis': ('Servos: Sicherheit, Positionen, Test, Diagnose', 'Servos : sécurité, positions, test, diagnostic', 'Servo: sicurezza, posizioni, test, diagnosi', 'Servos: segirezza, posiziuns, test, diagnosa'),
    'servo-note': ('Fährt Schwenken und Neigen langsam über den ganzen Bereich und prüft, ob sich das Bild jedes Mal bewegt. Danach zurück an die alte Stelle.',
                   'Fait pivoter et incliner lentement sur toute la plage et vérifie que l’image bouge à chaque fois. Puis retour à la position d’avant.',
                   'Ruota e inclina lentamente su tutto il campo e controlla che l’immagine si muova ogni volta. Poi torna alla posizione di prima.',
                   'Volva e sbassa plaun sur l’entir intervall e controllescha, sch’il maletg sa mova mintga giada. Lura enavos al lieu da pli baud.'),
    'Start the servo test': ('Servo-Test starten', 'Lancer le test des servos', 'Avvia il test dei servo', 'Cumenzar il test dals servos'),
    'Axis': ('Achse', 'Axe', 'Asse', 'Axa'),
    'Picture change': ('Bildänderung', 'Changement d’image', 'Cambio immagine', 'Midada dal maletg'),
    'no change': ('keine Änderung', 'aucun changement', 'nessun cambio', 'nagina midada'),
    'steps without a change of the picture - blocked, at the end or camera not on the head?': (
        'Schritte ohne Bildänderung – blockiert, am Anschlag oder Kamera nicht auf dem Kopf?',
        'étapes sans changement d’image – bloqué, en butée ou caméra pas sur la tête ?',
        'passi senza cambio d’immagine – bloccato, a fine corsa o telecamera non sulla testa?',
        'pass senza midada dal maletg – blocà, a la fin u camera betg sin il chau?'),
    '🛠 Servos: test and positions': ('🛠 Servos: Test und Positionen', '🛠 Servos : test et positions', '🛠 Servo: test e posizioni', '🛠 Servos: test e posiziuns'),
    'Network test, servos, diagnosis and more.': ('Netztest, Servos, Diagnose und mehr.', 'Test réseau, servos, diagnostic et plus.', 'Test di rete, servo, diagnosi e altro.', 'Test da rait, servos, diagnosa e dapli.'),
    # 2: the shortcut key is an app key
    'only the shortcut addresses /k/': ('nur die Kurzbefehl-Adressen /k/', 'seulement les adresses de raccourci /k/', 'solo gli indirizzi delle scorciatoie /k/', 'mo las adressas da scursanidas /k/'),
    'Copy the addresses now - the key is shown only this one time.': ('Adressen jetzt kopieren – der Schlüssel wird nur dieses eine Mal gezeigt.',
        'Copie les adresses maintenant – la clé n’est montrée que cette fois.', 'Copia ora gli indirizzi – la chiave viene mostrata solo questa volta.',
        'Copiar ussa las adressas – la clav vegn mussada mo questa giada.'),
    'app key': ('App-Schlüssel', 'clé d’app', 'chiave app', 'clav d’app'),
    'sc-key-note2': ('Der Schlüssel ist ein App-Schlüssel, der nur diese Adressen öffnet (nicht den Rest von MoveEye). MoveEye speichert nur seinen Fingerabdruck – darum steht er nur direkt nach dem Erstellen hier. Jeder App-Schlüssel (Einstellungen → Sicherheit) geht hier auch. Von unterwegs über die Tailscale-Adresse.',
                     'La clé est une clé d’app qui n’ouvre que ces adresses (pas le reste de MoveEye). MoveEye ne garde que son empreinte – elle n’apparaît donc ici que juste après sa création. Toute clé d’app (Réglages → Sécurité) fonctionne aussi. En déplacement : par l’adresse Tailscale.',
                     'La chiave è una chiave app che apre solo questi indirizzi (non il resto di MoveEye). MoveEye ne conserva solo l’impronta – per questo appare qui solo subito dopo la creazione. Funziona anche ogni chiave app (Impostazioni → Sicurezza). In viaggio: tramite l’indirizzo Tailscale.',
                     'La clav è ina clav d’app che avra mo questas adressas (betg il rest da MoveEye). MoveEye memorisescha mo ses stampun – perquai stat ella qua mo directamain suenter l’avair fatg. Mintga clav d’app (Parameters → Segirezza) va er. Da viadi: sur l’adressa Tailscale.'),
    'These app keys work here too:': ('Diese App-Schlüssel gehen hier auch:', 'Ces clés d’app fonctionnent aussi ici :', 'Anche queste chiavi app funzionano qui:', 'Questas clavs d’app van er qua:'),
    'One more shortcut key': ('Noch ein Kurzbefehl-Schlüssel', 'Une clé de raccourci de plus', 'Un’altra chiave per scorciatoie', 'Anc ina clav da scursanida'),
    'Make a shortcut key': ('Kurzbefehl-Schlüssel erstellen', 'Créer une clé de raccourci', 'Crea una chiave per scorciatoie', 'Far ina clav da scursanida'),
    'All app keys': ('Alle App-Schlüssel', 'Toutes les clés d’app', 'Tutte le chiavi app', 'Tut las clavs d’app'),
    # 5: the ☰ menu is per device
    'vm-device': ('Ein- und Ausblenden gilt nur für dieses Gerät – wie «◫ Ansicht» auf der Live-Seite.', 'Afficher / masquer ne vaut que pour cet appareil – comme «◫ Vue» de la page en direct.',
                  'Mostrare / nascondere vale solo per questo dispositivo – come «◫ Vista» della pagina live.', 'Mussar / zuppentar vala mo per quest apparat – sco «◫ Vista» da la pagina live.'),
    # 6: zones «only report» and «stays on its place»
    '+ Only report': ('+ Nur melden', '+ Signaler seulement', '+ Solo segnalare', '+ Mo annunziar'),
    'Only report': ('Nur melden', 'Signaler seulement', 'Solo segnalare', 'Mo annunziar'),
    'z-report': ('Steht eine Person mit den Füssen darin, gibt es keinen Alarm – nur eine Zeile im Protokoll und ab und zu eine Info-Nachricht (öffentlicher Weg, Weg der Nachbarn). «Platz einrichten» macht seinen öffentlichen Weg zu so einer Zone.',
                 'Une personne qui a les pieds dedans ne déclenche pas d’alarme – seulement une ligne dans le journal et de temps en temps un message d’info (chemin public, chemin des voisins). «Aménager le lieu» fait de son chemin public une telle zone.',
                 'Una persona con i piedi dentro non fa scattare l’allarme – solo una riga nel registro e ogni tanto un messaggio informativo (sentiero pubblico, passaggio dei vicini). «Allestire il posto» rende il suo sentiero pubblico una tale zona.',
                 'Ina persuna cun ils pes lien na fa nagin alarm – mo ina lingia en il protocol e da temp en temp in avis d’info (via publica, via dals vischins). «Endrizzar il lieu» fa da sia via publica ina tala zona.'),
    'Stays on its place': ('Bleibt am Platz', 'Reste à sa place', 'Resta al suo posto', 'Resta al ses lieu'),
    'z-anchor': ('Die Zone bleibt auf dem Boden, wenn sich der Kopf dreht (Ecken als Richtungen gespeichert) – sonst klebt sie am Bild. Einzeichnen, während die Kamera dorthin schaut. Privatsphäre-Zonen und der Schlafplatz bleiben immer am Platz.',
                 'La zone reste au sol quand la tête tourne (coins gardés comme directions) – sinon elle est fixée à l’image. La dessiner pendant que la caméra regarde là. Les zones de confidentialité et le lieu de sommeil restent toujours en place.',
                 'La zona resta a terra quando la testa gira (angoli salvati come direzioni) – altrimenti è fissata all’immagine. Disegnarla mentre la telecamera guarda lì. Le zone privacy e il posto letto restano sempre al loro posto.',
                 'La zona resta sin il terren, cur ch’il chau sa volva (cantuns memorisads sco direcziuns) – uschiglio stat ella fixa al maletg. Dissegnar, entant che la camera guarda là. Zonas da sfera privata ed il lieu da durmir restan adina al lieu.'),
    'from «Set up the place»': ('aus «Platz einrichten»', 'de «Aménager le lieu»', 'da «Allestire il posto»', 'da «Endrizzar il lieu»'),
    # 7 / 8: head
    'Deterrence: turn the light and the siren to the person (otherwise to the tent of «Platz einrichten»)': (
        'Abschrecken: Licht und Sirene zur Person drehen (sonst zum Zelt aus «Platz einrichten»)',
        'Dissuasion : tourner la lumière et la sirène vers la personne (sinon vers la tente de «Aménager le lieu»)',
        'Dissuasione: girare luce e sirena verso la persona (altrimenti verso la tenda di «Allestire il posto»)',
        'Spaventar: volver la glisch e la sirena vers la persuna (uschiglio vers la tenda da «Endrizzar il lieu»)'),
    'Smart round (when «Patrol» is on): longer at the tent and the access, hardly at ignored directions (places from «Platz einrichten», otherwise the waypoints)': (
        'Kluge Runde (wenn «Patrouille» an ist): länger beim Zelt und beim Zugang, kaum bei ignorierten Richtungen (Orte aus «Platz einrichten», sonst die Wegpunkte)',
        'Ronde intelligente (quand «Patrouille» est activée) : plus longtemps à la tente et à l’accès, à peine vers les directions ignorées (lieux de «Aménager le lieu», sinon les points de passage)',
        'Giro intelligente (quando «Pattuglia» è attiva): più a lungo alla tenda e all’accesso, appena verso le direzioni ignorate (posti da «Allestire il posto», altrimenti i punti di passaggio)',
        'Ronda intelligenta (cur che «Patruglia» è activa): pli ditg tar la tenda e tar l’access, strusch tar direcziuns ignoradas (lieus da «Endrizzar il lieu», uschiglio ils puncts da via)'),
    'game round: the players steer the head - following paused': ('Spielrunde: die Spieler steuern den Kopf – Folgen pausiert', 'manche de jeu : les joueurs dirigent la tête – suivi en pause',
        'turno di gioco: i giocatori guidano la testa – inseguimento in pausa', 'runda da gieu: ils giugaders manischan il chau – suandar en pausa'),
    # 12: two settings with the same name «Ton»
    'Wake-up sound': ('Weckton', 'Son du réveil', 'Suono della sveglia', 'Tun da la sveglia'),
    'Siren sound': ('Sirenenton', 'Son de la sirène', 'Suono della sirena', 'Tun da la sirena'),
    # 9: animal species as one group
    'Animal species': ('Tierart', 'Espèce animale', 'Specie animale', 'Spezia d’animal'),
    'Install the model: web page, Settings → AI detection → «Animal species» (address of an .onnx or .zip)': (
        'Modell installieren: Webseite, Einstellungen → KI-Erkennung → «Tierart» (Adresse einer .onnx- oder .zip-Datei)',
        'Installer le modèle : page web, Réglages → Détection IA → «Espèce animale» (adresse d’un .onnx ou .zip)',
        'Installare il modello: pagina web, Impostazioni → Rilevamento IA → «Specie animale» (indirizzo di un .onnx o .zip)',
        'Installar il model: pagina web, Parameters → Identificaziun IA → «Spezia d’animal» (adressa d’in .onnx u .zip)'),
}
for _k, _v in _HX_AUFR.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the pages with their own German dictionary
_AUFR_MAIN = ["Positions, test, diagnosis, Not-Aus", "only the shortcut addresses /k/", "Copy the addresses now - the key is shown only this one time.", "app key",
              "sc-key-note2", "These app keys work here too:", "One more shortcut key", "Make a shortcut key", "All app keys", "vm-device", "Animal species"]
_AUFR_EN = {k: k for k in _AUFR_MAIN}
_AUFR_EN.update({"sc-key-note2": "The key is an app key that opens only these addresses (not the rest of MoveEye). MoveEye keeps only its fingerprint - so it stands here only right after it is made. Every app key (Settings → Security) works here too. On the road: through the Tailscale address.",
                 "vm-device": "Showing and hiding is for this device only - like «◫ View» of the live page."})
WEB_PAGE = WEB_PAGE.replace("/*AUFRDE*/{}", json.dumps({k: DE[k] for k in _AUFR_MAIN}, ensure_ascii=False), 1).replace(
    "/*AUFREN*/{}", json.dumps({k: v for k, v in _AUFR_EN.items() if v != k}, ensure_ascii=False), 1)
ZONES_PAGE = ZONES_PAGE.replace("/*ZAUFRDE*/{}", json.dumps({k: DE[k] for k in ("+ Only report", "Only report", "z-report", "Stays on its place", "z-anchor",
                                                                                "from «Set up the place»")}, ensure_ascii=False), 1)


def aufr_selftest():
    """the clean-up round: one servo entry, the texts are filled in, the zone kinds"""
    assert "/*AUFRDE*/" not in WEB_PAGE and "/*AUFREN*/" not in WEB_PAGE and "/*ZAUFRDE*/" not in ZONES_PAGE
    assert "startZone('report')" in ZONES_PAGE and "Stays on its place" in ZONES_PAGE
    assert 'id="m-fbtest"' not in MORE_PAGE, "Test-Feedback is in Mehr → System (516)"
    assert "function simExtras" not in WEB_PAGE and "simExtras(d)" not in WEB_PAGE, "dead code (aufr)"
    assert "mw-hidden" in WEB_UI_LOCAL and "b-night" not in ALM_PAGE
    assert not any(k == "controls" for _g, k, _l in VIEW_ITEMS), "camera control only in ◫ Ansicht"
    for k in _HX_AUFR:
        assert tr(k, "de") != k or k in ("Test",), k
    return f"{len(_HX_AUFR)} texts, servo entry, zone kinds, ☰ per device, almanac theme"


SELFTEST_EXTRA.append(("Clean-up round (aufr): one place per thing", aufr_selftest))
