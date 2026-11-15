#@ MoveEye – Teil 639zzzg: «Mehr-Stil» auf allen Seiten (Besitzer 2026-11) – Gruppen-Titel ausserhalb der Karten, Zeilen mit Symbol, Titel, einer kurzen Zeile darunter, dem Zustand und ›; ein Tipp öffnet die eigene Unterseite mit «‹ Zurück». Dazu «Schutz klar» (oben Aus / Wachsam / Voll mit einer Statuszeile, Modus-Kacheln). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Nichts wird entfernt: die Karten / Gruppen der Seite bleiben, wie sie sind (ids, Schalter, Hüllen anderer Teile). Diese Schicht
# zeigt sie im Browser als Liste; ein Tipp hängt die Karte in die Unterseite (#ms-page) und beim Zurück an ihren Platz zurück.
# Seiten: Einstellungen (#settings, Gruppen neu: Kamera & Kopf, Erkennung, Licht & Ton, Zusatzgeräte, Gerät & Akku, Netz & Zugang,
# Darstellung, Daten & Updates), Schutz (oben die grosse Karte, dann Zeilen), Sim (die Karten der Seite), Verlauf (Statistik, Filter
# … als Zeilen über den Aufnahmen). Der Zustand jeder Zeile kommt aus EINER Funktion (MS_ST) aus Einstellung und Laufzeit-Zustand.
# Alte Links (?open=…) öffnen die passende Unterseite; die Unterseite steht in der Adresse (#s=…), «Zurück» des Browsers geht.
# 🔍 oben rechts sucht in allen Zeilen (auch in den Texten der Unterseiten) und öffnet die gefundene.
# Pi-Fenster (Tk): kommt nach der Freigabe (Zeilen -> Unterseite mit Zurück).
# ----------------------------------------------------------------------------
# the texts and the rows (one JSON literal: werkzeuge/bauen.py puts it into the data zip - the main file stays small)
MS_TEXT_JS = r"""{
"hx": {
"Camera & head": [
"Kamera & Kopf",
"Caméra et tête",
"Camera e testa",
"Camera e chau"
],
"Detection": [
"Erkennung",
"Détection",
"Rilevamento",
"Identificaziun"
],
"Light & sound": [
"Licht & Ton",
"Lumière et son",
"Luce e suono",
"Glisch e tun"
],
"Extra devices": [
"Zusatzgeräte",
"Appareils supplémentaires",
"Dispositivi aggiuntivi",
"Apparats supplementars"
],
"Device & battery": [
"Gerät & Akku",
"Appareil et batterie",
"Dispositivo e batteria",
"Apparat ed accu"
],
"Network & access": [
"Netz & Zugang",
"Réseau et accès",
"Rete e accesso",
"Rait ed access"
],
"Display & language": [
"Darstellung & Sprache",
"Affichage et langue",
"Aspetto e lingua",
"Preschentaziun e lingua"
],
"Data & updates": [
"Daten & Updates",
"Données et mises à jour",
"Dati e aggiornamenti",
"Datas ed actualisaziuns"
],
"At an alarm": [
"Bei Alarm",
"En cas d’alarme",
"In caso di allarme",
"En cas d’alarm"
],
"Theft protection": [
"Diebstahlschutz",
"Protection contre le vol",
"Protezione furto",
"Protecziun cunter il fraud"
],
"Time & presence": [
"Zeit & Anwesenheit",
"Heure et présence",
"Orari e presenza",
"Temp e preschientscha"
],
"Protection tools": [
"Schutz-Werkzeuge",
"Outils de protection",
"Strumenti di protezione",
"Utensils da protecziun"
],
"Simulator": [
"Simulator",
"Simulateur",
"Simulatore",
"Simulatur"
],
"Link to the simulator": [
"Verbindung zum Simulator",
"Connexion au simulateur",
"Collegamento al simulatore",
"Colliaziun cun il simulatur"
],
"More topics": [
"Weitere",
"Autres sujets",
"Altri argomenti",
"Ulteriurs temas"
],
"Help & downloads": [
"Hilfe & Downloads",
"Aide et téléchargements",
"Aiuto e download",
"Agid e telechargiadas"
],
"Overview": [
"Übersicht",
"Vue d’ensemble",
"Panoramica",
"Survista"
],
"Cameras and devices": [
"Kameras und Geräte",
"Caméras et appareils",
"Telecamere e dispositivi",
"Cameras ed apparats"
],
"devices": [
"Geräte",
"appareils",
"dispositivi",
"apparats"
],
"on": [
"an",
"activé",
"attivo",
"en"
],
"off": [
"aus",
"désactivé",
"spento",
"ora"
],
"automatic": [
"automatisch",
"automatique",
"automatico",
"automatic"
],
"by hand": [
"von Hand",
"à la main",
"a mano",
"a maun"
],
"developer": [
"Entwickler",
"Développeur",
"Sviluppatore",
"Sviluppader"
],
"no source": [
"keine Quelle",
"pas de source",
"nessuna fonte",
"nagina funtauna"
],
"not set up": [
"nicht eingerichtet",
"pas configuré",
"non configurato",
"betg endrizzà"
],
"not connected": [
"nicht verbunden",
"non connecté",
"non collegato",
"betg collià"
],
"connected": [
"verbunden",
"connecté",
"collegato",
"collià"
],
"no head": [
"kein Kopf",
"pas de tête",
"nessuna testa",
"nagin chau"
],
"ready": [
"bereit",
"prêt",
"pronto",
"pront"
],
"follows persons": [
"folgt Personen",
"suit les personnes",
"segue le persone",
"suonda persunas"
],
"emergency stop": [
"Not-Aus",
"Arrêt d’urgence",
"Arresto d’emergenza",
"Stop d’urgenza"
],
"no motor driver": [
"kein Motortreiber",
"pas de pilote moteur",
"nessun driver motore",
"nagin driver da motor"
],
"model missing": [
"Modell fehlt",
"modèle manquant",
"modello mancante",
"model manca"
],
"no light connected": [
"kein Licht gewählt",
"pas de lumière choisie",
"nessuna luce scelta",
"nagina glisch tschernida"
],
"no loudspeaker": [
"kein Lautsprecher",
"pas de haut-parleur",
"nessun altoparlante",
"nagin autpledader"
],
"no microphone": [
"kein Mikrofon",
"pas de micro",
"nessun microfono",
"nagin microfon"
],
"no sensor": [
"kein Fühler",
"pas de capteur",
"nessun sensore",
"nagin sensur"
],
"no battery": [
"kein Akku",
"pas de batterie",
"nessuna batteria",
"nagin accu"
],
"saving now": [
"spart gerade",
"économise",
"sta risparmiando",
"spargna ussa"
],
"active": [
"aktiv",
"actif",
"attivo",
"activ"
],
"password set": [
"Passwort gesetzt",
"mot de passe défini",
"password impostata",
"pled-clav fixà"
],
"no password": [
"kein Passwort",
"pas de mot de passe",
"nessuna password",
"nagin pled-clav"
],
"hotspot on": [
"Hotspot an",
"hotspot activé",
"hotspot attivo",
"hotspot en"
],
"not available": [
"nicht verfügbar",
"non disponible",
"non disponibile",
"betg disponibel"
],
"camera": [
"Kamera",
"caméra",
"telecamera",
"camera"
],
"cameras": [
"Kameras",
"caméras",
"telecamere",
"cameras"
],
"relay": [
"Relais",
"relais",
"relè",
"relais"
],
"sensors": [
"Sensoren",
"capteurs",
"sensori",
"sensurs"
],
"schedules active": [
"Zeitpläne aktiv",
"horaires actifs",
"orari attivi",
"plans activs"
],
"here": [
"da",
"là",
"qui",
"qua"
],
"away": [
"weg",
"absent",
"via",
"davent"
],
"night vision": [
"Nachtsicht",
"vision nocturne",
"visione notturna",
"vista da notg"
],
"paused": [
"pausiert",
"en pause",
"in pausa",
"en pausa"
],
"quiet hours": [
"Ruhezeit",
"heures calmes",
"ore di quiete",
"uras da ruaus"
],
"time ok": [
"Uhrzeit stimmt",
"heure correcte",
"ora corretta",
"ura correcta"
],
"check the time": [
"Uhrzeit prüfen",
"vérifier l’heure",
"controlla l’ora",
"controllar l’ura"
],
"ready to install": [
"bereit zum Installieren",
"prête à installer",
"pronto da installare",
"pront per installar"
],
"‹ Back": [
"‹ Zurück",
"‹ Retour",
"‹ Indietro",
"‹ Enavos"
],
"Search all settings": [
"Alle Einstellungen durchsuchen",
"Chercher dans tous les réglages",
"Cerca in tutte le impostazioni",
"Tschertgar en tut las configuraziuns"
],
"Nothing found": [
"Nichts gefunden",
"Rien trouvé",
"Nessun risultato",
"Nagut chattà"
],
"all ok": [
"alles ok",
"tout est en ordre",
"tutto ok",
"tut en urden"
],
"on mains power": [
"am Strom",
"sur secteur",
"alla rete",
"a la rait"
],
"1 problem": [
"1 Problem",
"1 problème",
"1 problema",
"1 problem"
],
"problems": [
"Probleme",
"problèmes",
"problemi",
"problems"
],
"1 hint": [
"1 Hinweis",
"1 remarque",
"1 nota",
"1 indicaziun"
],
"hints": [
"Hinweise",
"remarques",
"note",
"indicaziuns"
],
"Fix": [
"Beheben",
"Corriger",
"Correggi",
"Curreger"
],
"Protection assistant, test and PIN": [
"Schutz-Assistent, Test und PIN",
"Assistant, test et PIN",
"Assistente, test e PIN",
"Assistent, test e PIN"
],
"Siren and absence": [
"Sirene und Abwesenheit",
"Sirène et absence",
"Sirena e assenza",
"Sirena ed absenza"
],
"Device: tamper and backup": [
"Gerät: Sabotage und Sicherung",
"Appareil : sabotage et sauvegarde",
"Dispositivo: sabotaggio e backup",
"Apparat: sabotascha e segirezza"
],
"Time, place, temperature": [
"Uhrzeit, Standort, Temperatur",
"Heure, lieu, température",
"Ora, luogo, temperatura",
"Ura, lieu, temperatura"
],
"Walk test": [
"Gehtest",
"Test de marche",
"Test di camminata",
"Test da chaminar"
],
"Set up the place": [
"Platz einrichten",
"Installer l’emplacement",
"Imposta il posto",
"Endrizzar il lieu"
],
"Zones": [
"Zonen",
"Zones",
"Zone",
"Zonas"
],
"Cameras": [
"Kameras",
"Caméras",
"Telecamere",
"Cameras"
],
"Gehtest and tips": [
"Gehtest & Tipps",
"Test de marche et astuces",
"Test di camminata e consigli",
"Test da chaminar e cussegls"
],
"Tips & tricks": [
"Tipps & Tricks",
"Astuces",
"Consigli e trucchi",
"Cussegls e tricks"
]
},
"dx": {
"d:source": [
"Woher das Bild kommt",
"D’où vient l’image",
"Da dove arriva l’immagine",
"Danunder che il maletg vegn"
],
"d:cams": [
"Alle Kameras, hinzufügen, andere MoveEye",
"Toutes les caméras, ajouter, autres MoveEye",
"Tutte le telecamere, aggiungere, altri MoveEye",
"Tut las cameras, agiuntar, auters MoveEye"
],
"d:servo": [
"Drehen, Grenzen, Grundstellung, folgen",
"Rotation, limites, position de base, suivre",
"Rotazione, limiti, posizione base, seguire",
"Volver, cunfins, posiziun da basa, suandar"
],
"d:patrol": [
"Der Kopf schaut reihum",
"La tête regarde à tour de rôle",
"La testa guarda a turno",
"Il chau guarda per rotaziun"
],
"d:mover": [
"Raupen-Fahrwerk",
"Châssis à chenilles",
"Telaio a cingoli",
"Chassis cun chadainas"
],
"d:timelapse": [
"Ein Bild alle paar Minuten",
"Une image toutes les quelques minutes",
"Un’immagine ogni pochi minuti",
"In maletg mintga paucs minuts"
],
"d:qr": [
"Befehle per QR-Karte",
"Commandes par carte QR",
"Comandi con scheda QR",
"Cumonds cun carta QR"
],
"d:camfine": [
"Alle Feineinstellungen von Kamera und Kopf",
"Tous les réglages fins caméra et tête",
"Tutte le regolazioni fini",
"Tut las configuraziuns finas"
],
"d:tune": [
"Geführt prüfen und verbessern",
"Vérifier et améliorer, guidé",
"Verificare e migliorare, guidato",
"Controllar e meglierar, guidà"
],
"d:profile": [
"Wie empfindlich MoveEye ist",
"Sensibilité de MoveEye",
"Quanto è sensibile MoveEye",
"Quant sensibel che MoveEye è"
],
"d:detection": [
"Bewegung und Personen im Bild",
"Mouvement et personnes",
"Movimento e persone",
"Moviment e persunas"
],
"d:ai": [
"Personen, Tiere, Fahrzeuge erkennen",
"Reconnaître personnes, animaux, véhicules",
"Riconoscere persone, animali, veicoli",
"Renconuscher persunas, animals, vehichels"
],
"d:thermal": [
"Wärmebild: Alarm, Bild, Kamera",
"Thermique : alarme, image, caméra",
"Termico: allarme, immagine, telecamera",
"Termic: alarm, maletg, camera"
],
"d:thalarm": [
"Alarm bei Wärme",
"Alarme à la chaleur",
"Allarme al calore",
"Alarm tar chalur"
],
"d:thview": [
"Farben und Darstellung",
"Couleurs et affichage",
"Colori e visualizzazione",
"Colurs e preschentaziun"
],
"d:thcam": [
"Anschluss und Ausrichtung",
"Connexion et orientation",
"Collegamento e orientamento",
"Colliaziun ed orientaziun"
],
"d:walk": [
"Gehen erkennen statt Wackeln",
"Reconnaître la marche",
"Riconoscere il camminare",
"Renconuscher il chaminar"
],
"d:car": [
"Vorbeifahrende Autos ignorieren",
"Ignorer les voitures",
"Ignorare le auto",
"Ignorar autos"
],
"d:rain": [
"Weniger Fehlalarme bei Regen",
"Moins de fausses alarmes sous la pluie",
"Meno falsi allarmi con la pioggia",
"Main faussas alarms cun plievgia"
],
"d:wind": [
"Weniger Fehlalarme bei Wind",
"Moins de fausses alarmes avec le vent",
"Meno falsi allarmi con il vento",
"Main faussas alarms cun vent"
],
"d:lowlight": [
"Dämmerung und Nacht",
"Crépuscule et nuit",
"Crepuscolo e notte",
"Crepuscul e notg"
],
"d:autotune": [
"Stellt sich selbst nach",
"Se règle tout seul",
"Si regola da solo",
"Sa regla sez"
],
"d:lights": [
"Weisses Licht und Infrarot",
"Lumière blanche et infrarouge",
"Luce bianca e infrarossi",
"Glisch alva ed infracotschen"
],
"d:led": [
"Farben der LED, Tasten",
"Couleurs de la LED, boutons",
"Colori del LED, tasti",
"Colurs da la LED, tastas"
],
"d:spk": [
"Sirene, Stimme, Klang",
"Sirène, voix, son",
"Sirena, voce, suono",
"Sirena, vusch, tun"
],
"d:mic": [
"Geräusch-Alarm und Hören",
"Alarme sonore et écoute",
"Allarme rumore e ascolto",
"Alarm da canera ed udir"
],
"d:clap": [
"Zweimal klatschen schaltet",
"Deux claquements commutent",
"Due battiti accendono",
"Dus clappads cumbinan"
],
"d:bless": [
"Antwortet aufs Niesen",
"Répond aux éternuements",
"Risponde agli starnuti",
"Respunda a starnidas"
],
"d:wake": [
"Weckt dich sanft",
"Te réveille en douceur",
"Ti sveglia dolcemente",
"Ta dasdescha plaun"
],
"d:relay": [
"Schaltet Geräte bei Alarm",
"Commute des appareils",
"Comanda dispositivi",
"Cumonda apparats"
],
"d:sensors": [
"Bewegungsmelder, Türkontakt …",
"Détecteur, contact de porte …",
"Rilevatore, contatto porta …",
"Detectur, contact da porta …"
],
"d:storm": [
"Luftdruck und Wind",
"Pression et vent",
"Pressione e vento",
"Pressiun e vent"
],
"d:gps": [
"Standort und Diebstahl",
"Position et vol",
"Posizione e furto",
"Posiziun e fraud"
],
"d:smalltv": [
"Kleiner Bildschirm (SmallTV)",
"Petit écran (SmallTV)",
"Piccolo schermo (SmallTV)",
"Pitschen visur (SmallTV)"
],
"d:batt": [
"Ladung, Laufzeit, Warnungen",
"Charge, autonomie, alertes",
"Carica, autonomia, avvisi",
"Chargia, durada, avertiments"
],
"d:eco": [
"Weniger Strom in ruhigen Zeiten",
"Moins de courant au calme",
"Meno corrente nei momenti calmi",
"Main current en temps quiets"
],
"d:solar": [
"Strom vom Panel messen",
"Mesurer le courant du panneau",
"Misurare la corrente del pannello",
"Mesirar il current dal panel"
],
"d:system": [
"Prozessor, Speicher, Neustart",
"Processeur, mémoire, redémarrage",
"Processore, memoria, riavvio",
"Processur, memoria, reaviar"
],
"d:warn": [
"Hitze, Spannung, Speicher",
"Chaleur, tension, mémoire",
"Calore, tensione, memoria",
"Chalur, tensiun, memoria"
],
"d:setup": [
"Ort, Uhrzeit, Zeitzone",
"Lieu, heure, fuseau",
"Luogo, ora, fuso",
"Lieu, ura, zona"
],
"d:wifi": [
"WLAN und eigener Hotspot",
"Wi-Fi et hotspot",
"Wi-Fi e hotspot",
"WLAN e hotspot"
],
"d:stream": [
"Live-Bild im Browser",
"Image en direct",
"Immagine dal vivo",
"Maletg live"
],
"d:guest": [
"Link nur zum Zuschauen",
"Lien pour regarder",
"Link solo per guardare",
"Colliaziun mo per guardar"
],
"d:mqtt": [
"Home Assistant, MQTT",
"Home Assistant, MQTT",
"Home Assistant, MQTT",
"Home Assistant, MQTT"
],
"d:security": [
"Passwort, Benutzer, https",
"Mot de passe, utilisateurs, https",
"Password, utenti, https",
"Pled-clav, utilisaders, https"
],
"d:devhelp": [
"Name, Symbol, Hilfe",
"Nom, icône, aide",
"Nome, icona, aiuto",
"Num, simbol, agid"
],
"d:appicon": [
"Symbol auf dem Handy",
"Icône sur le téléphone",
"Icona sul telefono",
"Simbol sin il telefonin"
],
"d:rucksack": [
"Fotos und Dateien teilen",
"Partager photos et fichiers",
"Condividere foto e file",
"Parter fotos e datotecas"
],
"d:updates": [
"Neue Versionen",
"Nouvelles versions",
"Nuove versioni",
"Novas versiuns"
],
"d:log": [
"Was wichtig war",
"Ce qui était important",
"Cosa è stato importante",
"Tge ch’era impurtant"
],
"d:factory": [
"Einrichtung, Werkseinstellungen",
"Configuration, réglages d’usine",
"Configurazione, impostazioni di fabbrica",
"Endrizzament, configuraziuns da fabrica"
],
"d:chain": [
"Person → Push → Licht → Aufnahme → Sirene",
"Personne → push → lumière → vidéo → sirène",
"Persona → push → luce → video → sirena",
"Persuna → push → glisch → video → sirena"
],
"d:push": [
"Nachrichten aufs Handy",
"Messages sur le téléphone",
"Messaggi sul telefono",
"Messadis sin il telefonin"
],
"d:deter": [
"Licht und Klang gegen Besucher",
"Lumière et son contre les visiteurs",
"Luce e suono contro i visitatori",
"Glisch e tun cunter visitaders"
],
"d:rec": [
"Videos bei Alarm",
"Vidéos en cas d’alarme",
"Video in caso di allarme",
"Videos en cas d’alarm"
],
"d:report": [
"Am Morgen eine Zusammenfassung",
"Un résumé le matin",
"Un riassunto al mattino",
"In resumaziun la damaun"
],
"d:theft": [
"Anheben, Kippen, Strom weg",
"Soulever, basculer, coupure",
"Sollevare, inclinare, corrente",
"Auzar, sbassar, current davent"
],
"d:refscan": [
"Fotos der bewachten Dinge",
"Photos des objets gardés",
"Foto degli oggetti sorvegliati",
"Fotos da las chaussas survegliadas"
],
"d:backup": [
"Bilder weg vom Gerät",
"Images hors de l’appareil",
"Immagini fuori dal dispositivo",
"Maletgs davent da l’apparat"
],
"d:zones": [
"Wo Alarm gilt, wo nicht",
"Où l’alarme compte",
"Dove vale l’allarme",
"Nua che l’alarm vala"
],
"d:sched": [
"Zu festen Zeiten an / aus",
"Marche / arrêt à heures fixes",
"Acceso / spento a orari fissi",
"En / ora a temps fixs"
],
"d:night": [
"Wann Nacht ist",
"Quand c’est la nuit",
"Quando è notte",
"Cura ch’igl è notg"
],
"d:presence": [
"Bist du da oder weg?",
"Es-tu là ou absent ?",
"Sei qui o via?",
"Es ti qua u davent?"
],
"d:camping": [
"Einschalten, eigenes WLAN",
"Mise en marche, Wi-Fi propre",
"Accensione, Wi-Fi proprio",
"Activar, agen WLAN"
],
"d:tools": [
"Assistent, Schutz testen, PIN",
"Assistant, tester, PIN",
"Assistente, test, PIN",
"Assistent, testar, PIN"
],
"d:siren": [
"Sirene nach … s, Handy weg = an",
"Sirène après … s, téléphone absent = marche",
"Sirena dopo … s, telefono via = acceso",
"Sirena suenter … s, telefonin davent = en"
],
"d:device": [
"Sabotage-Prüfung, Sicherung",
"Contrôle sabotage, sauvegarde",
"Controllo sabotaggio, backup",
"Controlla da sabotascha, segirezza"
],
"d:walktest": [
"Wie weit sieht MoveEye dich?",
"Jusqu’où MoveEye te voit ?",
"Fin dove ti vede MoveEye?",
"Fin nua che MoveEye ta vesa?"
],
"d:place": [
"Zelt, Weg, Feuer einzeichnen",
"Tente, chemin, feu",
"Tenda, sentiero, fuoco",
"Tenda, senda, fieu"
],
"d:where": [
"Uhrzeit, Standort, Fühler",
"Heure, lieu, capteur",
"Ora, luogo, sensore",
"Ura, lieu, sensur"
],
"d:health": [
"Alle Prüfungen auf einen Blick",
"Tous les contrôles d’un coup d’œil",
"Tutti i controlli a colpo d’occhio",
"Tut ils controls d’in sguard"
],
"d:simconn": [
"Adresse, selbst finden, Firewall",
"Adresse, recherche, pare-feu",
"Indirizzo, ricerca, firewall",
"Adressa, tschertgar, firewall"
],
"d:simstatus": [
"Bilder, Antwortzeit, Meldungen",
"Images, temps de réponse, messages",
"Immagini, tempo di risposta, messaggi",
"Maletgs, temp da resposta, messadis"
],
"d:simhub": [
"Welt, Wetter, Besucher",
"Monde, météo, visiteurs",
"Mondo, meteo, visitatori",
"Mund, aura, visitaders"
],
"d:simtools": [
"Werkzeuge des Simulators",
"Outils du simulateur",
"Strumenti del simulatore",
"Utensils dal simulatur"
],
"d:simperf": [
"Weniger Bilder, weniger CPU",
"Moins d’images, moins de CPU",
"Meno immagini, meno CPU",
"Main maletgs, main CPU"
],
"d:simset": [
"Was MoveEye in der Simulation tut",
"Ce que fait MoveEye en simulation",
"Cosa fa MoveEye nella simulazione",
"Tge che MoveEye fa en la simulaziun"
],
"d:simhelp": [
"So funktioniert es",
"Comment ça marche",
"Come funziona",
"Co che quai funcziuna"
],
"d:simhp": [
"Rechner für die Simulation",
"Ordinateur de la simulation",
"Computer della simulazione",
"Computer da la simulaziun"
],
"d:stats": [
"Wann etwas los war",
"Quand il y a eu du mouvement",
"Quando è successo qualcosa",
"Cura ch’i ha dà insatge"
],
"d:filter": [
"Datum, Art, Kamera",
"Date, type, caméra",
"Data, tipo, telecamera",
"Data, gener, camera"
],
"d:loop": [
"Daueraufnahme",
"Enregistrement continu",
"Registrazione continua",
"Registraziun cuntinuanta"
],
"d:addcam": [
"Suchen, USB, Netzwerk-Kamera",
"Chercher, USB, caméra réseau",
"Cerca, USB, telecamera di rete",
"Tschertgar, USB, camera da rait"
],
"d:fleet": [
"Alle Geräte zusammen ein / aus",
"Tous les appareils ensemble",
"Tutti i dispositivi insieme",
"Tut ils apparats ensemen"
],
"d:map": [
"Aufnahmen auf der Karte",
"Enregistrements sur la carte",
"Registrazioni sulla mappa",
"Registraziuns sin la charta"
],
"d:zf": [
"Bilder für «Damals / Jetzt» sammeln",
"Collecter des images «autrefois / maintenant»",
"Raccogliere immagini «allora / adesso»",
"Rimnar maletgs «lura / ussa»"
],
"d:tips": [
"Kurze Hilfen zu dieser Seite",
"Petites aides pour cette page",
"Brevi aiuti per questa pagina",
"Curts agids per questa pagina"
]
},
"en": {
"d:source": "Where the picture comes from",
"d:cams": "All cameras, add one, other MoveEye",
"d:servo": "Turning, limits, home position, follow",
"d:patrol": "The head looks around in turn",
"d:mover": "Tracked chassis",
"d:timelapse": "One picture every few minutes",
"d:qr": "Commands by QR card",
"d:camfine": "All fine settings of camera and head",
"d:tune": "Check and improve, guided",
"d:profile": "How sensitive MoveEye is",
"d:detection": "Movement and persons in the picture",
"d:ai": "Recognise persons, animals, vehicles",
"d:thermal": "Thermal: alarm, picture, camera",
"d:thalarm": "Alarm on warmth",
"d:thview": "Colours and view",
"d:thcam": "Connection and direction",
"d:walk": "Walking instead of swaying",
"d:car": "Ignore passing cars",
"d:rain": "Fewer false alarms in the rain",
"d:wind": "Fewer false alarms in the wind",
"d:lowlight": "Dusk and night",
"d:autotune": "Adjusts itself",
"d:lights": "White light and infrared",
"d:led": "LED colours, buttons",
"d:spk": "Siren, voice, sound",
"d:mic": "Noise alarm and listening",
"d:clap": "Two claps switch",
"d:bless": "Answers a sneeze",
"d:wake": "Wakes you gently",
"d:relay": "Switches devices at an alarm",
"d:sensors": "Motion detector, door contact …",
"d:storm": "Air pressure and wind",
"d:gps": "Position and theft",
"d:smalltv": "Small screen (SmallTV)",
"d:batt": "Charge, run time, warnings",
"d:eco": "Less power in quiet times",
"d:solar": "Measure the panel current",
"d:system": "Processor, memory, restart",
"d:warn": "Heat, voltage, memory",
"d:setup": "Place, time, time zone",
"d:wifi": "Wi-Fi and own hotspot",
"d:stream": "Live picture in the browser",
"d:guest": "A link only to watch",
"d:mqtt": "Home Assistant, MQTT",
"d:security": "Password, users, https",
"d:devhelp": "Name, icon, help",
"d:appicon": "Icon on the phone",
"d:rucksack": "Share photos and files",
"d:updates": "New versions",
"d:log": "What was important",
"d:factory": "Setup, factory settings",
"d:chain": "Person → push → light → recording → siren",
"d:push": "Messages to the phone",
"d:deter": "Light and sound against visitors",
"d:rec": "Videos at an alarm",
"d:report": "A summary in the morning",
"d:theft": "Lifted, tilted, power gone",
"d:refscan": "Photos of the guarded things",
"d:backup": "Pictures away from the device",
"d:zones": "Where an alarm counts",
"d:sched": "On / off at fixed times",
"d:night": "When it is night",
"d:presence": "Are you here or away?",
"d:camping": "Switching on, own Wi-Fi",
"d:tools": "Assistant, test the protection, PIN",
"d:siren": "Siren after … s, phone gone = on",
"d:device": "Tamper check, backup",
"d:walktest": "How far does MoveEye see you?",
"d:place": "Draw tent, path, fire",
"d:where": "Time, place, sensor",
"d:health": "All checks at a glance",
"d:simconn": "Address, find by itself, firewall",
"d:simstatus": "Pictures, response time, messages",
"d:simhub": "World, weather, visitors",
"d:simtools": "Tools of the simulator",
"d:simperf": "Fewer pictures, less CPU",
"d:simset": "What MoveEye does in the simulation",
"d:simhelp": "How it works",
"d:simhp": "Computer of the simulation",
"d:stats": "When something happened",
"d:filter": "Date, kind, camera",
"d:addcam": "Search, USB, network camera",
"d:fleet": "All devices on / off together",
"d:loop": "Continuous recording",
"d:map": "Recordings on the map",
"d:zf": "Collect pictures for «then / now»",
"d:tips": "Short help for this page"
},
"pages": {
"settings": [
[
"Camera & head",
[
[
"source",
"d:source",
"source"
],
[
"@cams",
"d:cams",
"cams",
"📷",
"Cameras",
"/cams"
],
[
"sec:Camera / Servos",
"d:servo",
"servo"
],
[
"sec:Patrol",
"d:patrol",
"patrol"
],
[
"grp:mover",
"d:mover",
"mover"
],
[
"sec:Timelapse",
"d:timelapse",
"timelapse"
],
[
"sec:Window to the past",
"d:zf",
"zf"
],
[
"sec:QR command cards",
"d:qr",
""
],
[
"~grp:camera",
"d:camfine",
""
]
]
],
[
"Detection",
[
[
"tune",
"d:tune",
""
],
[
"sec:Detection profile",
"d:profile",
"profile"
],
[
"sec:Detection",
"d:detection",
"detection"
],
[
"sec:AI detection",
"d:ai",
"ai"
],
[
"sec:Thermal camera",
"d:thermal",
"thermal"
],
[
"th:alarm",
"d:thalarm",
"thalarm"
],
[
"th:view",
"d:thview",
"thview"
],
[
"th:cam",
"d:thcam",
"thcam"
],
[
"sec:Walking recognition",
"d:walk",
""
],
[
"sec:Vehicle filter",
"d:car",
"car"
],
[
"sec:Rain",
"d:rain",
"rain"
],
[
"sec:Wind",
"d:wind",
"wind"
],
[
"sec:Low light",
"d:lowlight",
"lowlight"
],
[
"sec:Auto-tune",
"d:autotune",
"autotune"
]
]
],
[
"Light & sound",
[
[
"sec:Lights",
"d:lights",
"lights"
],
[
"sec:Status LED",
"d:led",
""
],
[
"sec:Loudspeaker",
"d:spk",
"spk"
],
[
"sec:Microphone",
"d:mic",
"mic"
],
[
"sec:Clap switch",
"d:clap",
"clap"
],
[
"sec:Bless you",
"d:bless",
"bless"
],
[
"sec:Wake-up alarm",
"d:wake",
"wake"
]
]
],
[
"Extra devices",
[
[
"relayset",
"d:relay",
"relay"
],
[
"sec:Extra sensors",
"d:sensors",
"sensors"
],
[
"sec:Storm warning",
"d:storm",
"storm"
],
[
"sec:GPS module",
"d:gps",
"gps"
],
[
"sec:Extra display",
"d:smalltv",
""
]
]
],
[
"Device & battery",
[
[
"batt",
"d:batt",
"batt"
],
[
"sec:Power saving",
"d:eco",
"eco"
],
[
"sec:Solar panel",
"d:solar",
"solar"
],
[
"system",
"d:system",
"system"
],
[
"sec:Device warnings",
"d:warn",
""
],
[
"sec:Setup",
"d:setup",
"setup"
]
]
],
[
"Network & access",
[
[
"wifi",
"d:wifi",
"wifi"
],
[
"sec:Web stream",
"d:stream",
"stream"
],
[
"guest",
"d:guest",
"guest"
],
[
"sec:MQTT / Home Assistant",
"d:mqtt",
"mqtt"
],
[
"grp:security",
"d:security",
"security"
]
]
],
[
"Display & language",
[
[
"sec:Device & help",
"d:devhelp",
""
],
[
"~grp:sys",
"d:appicon",
""
]
]
],
[
"Data & updates",
[
[
"sec:File @XC",
"d:rucksack",
"rucksack"
],
[
"sec:Updates",
"d:updates",
"updates"
],
[
"log",
"d:log",
""
],
[
"g2:setup",
"d:factory",
""
]
]
]
],
"protect": [
[
"At an alarm",
[
[
"#alarm-chain",
"d:chain",
"chain",
"🚨",
"What happens at an alarm?"
],
[
"sec:Notifications",
"d:push",
"push"
],
[
"sec:Deterrence",
"d:deter",
"deter"
],
[
"sec:Recording",
"d:rec",
"rec"
],
[
"report",
"d:report",
"report"
]
]
],
[
"Theft protection",
[
[
"sec:Theft protection",
"d:theft",
"theft"
],
[
"sec:Reference scan",
"d:refscan",
"refscan"
],
[
"sec:Backup",
"d:backup",
"backup"
]
]
],
[
"Time & presence",
[
[
"@zones",
"d:zones",
"",
"🗺",
"Zones",
"/zones"
],
[
"schedule",
"d:sched",
"sched"
],
[
"sec:Night time",
"d:night",
""
],
[
"sec:Presence",
"d:presence",
"presence"
]
]
],
[
"Protection tools",
[
[
"sec:Camping / protection",
"d:camping",
"camping"
],
[
"#sk-v-tools",
"d:tools",
"",
"🧭",
"Protection assistant, test and PIN"
],
[
"#sk-v-siren",
"d:siren",
"siren",
"⏱",
"Siren and absence"
],
[
"#sk-v-dev",
"d:device",
"",
"🔒",
"Device: tamper and backup"
],
[
"#pr-wt",
"d:walktest",
"",
"🚶",
"Walk test"
],
[
"#pl-card",
"d:place",
"",
"📍",
"Set up the place"
],
[
"#sk-v-where",
"d:where",
"",
"🕐",
"Time, place, temperature"
],
[
"#hcard",
"d:health",
"health"
]
]
]
],
"sim": [
[
"Link to the simulator",
[
[
"#c-conn",
"d:simconn",
"simconn"
],
[
"#c-status",
"d:simstatus",
""
],
[
"#c-hp",
"d:simhp",
""
]
]
],
[
"Simulator",
[
[
"#c-hub",
"d:simhub",
""
],
[
"#c-tools",
"d:simtools",
""
],
[
"#c-perf",
"d:simperf",
""
],
[
"#c-simset",
"d:simset",
"",
"⚙"
]
]
],
[
"Help & downloads",
[
[
"#c-help",
"d:simhelp",
"",
"❓"
]
]
]
],
"cams": [
[
"Cameras and devices",
[
[
"?section.card:has(#btn-scan)",
"d:addcam",
"cams",
"➕"
],
[
"#fleet-card",
"d:fleet",
"fleet",
"🛰"
]
]
]
],
"history": [
[
"Overview",
[
[
"#statcard",
"d:stats",
"",
"📊"
],
[
"#flt-d",
"d:filter",
"",
"🔎"
],
[
"#loopcard",
"d:loop",
"",
"🎞"
],
[
"#mapcard",
"d:map",
"",
"🗺"
],
[
"#fa-card",
"d:loop",
"",
"🎞"
]
]
]
],
"live": [
[
"Gehtest and tips",
[
[
"#wt-card",
"d:walktest",
"",
"🚶"
],
[
"#g2-tt",
"d:tips",
"",
"💡",
"Tips & tricks"
]
]
]
]
}
}"""
_MS_T = json.loads(MS_TEXT_JS.replace("@XC", "ex" "change"))
_HX_MS, _DX_MS, _DX_EN, MS_PAGES = ({k: tuple(v) for k, v in _MS_T["hx"].items()}, {k: tuple(v) for k, v in _MS_T["dx"].items()}, _MS_T["en"], _MS_T["pages"])
for _k, _v in list(_HX_MS.items()) + list(_DX_MS.items()):
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

MS_CSS = r"""<style id="ms-css">
/* 639zzzg: «Mehr-Stil» - group headings outside, rows, one subpage per topic */
.ms-list .mg{margin:20px 0 0}.ms-list .mg:first-child{margin-top:6px}.ms-list .mg[hidden]{display:none}
.ms-list .mgh{font-size:17px;font-weight:700;margin:0 4px 8px;letter-spacing:0;text-transform:none;color:var(--txt)}
.ms-list .mgl{border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden}
.ms-list .mi{display:flex;align-items:center;gap:12px;padding:10px 12px 10px 14px;margin:0;border:0;border-radius:0;background:transparent;color:var(--txt);
  text-decoration:none;cursor:pointer;font:inherit;width:100%;text-align:left;min-height:58px;box-shadow:none;box-sizing:border-box}
.ms-list .mi:not([hidden])~.mi:not([hidden]){border-top:1px solid var(--line)}.ms-list .mi[hidden]{display:none}
.ms-list .mi>i{font-style:normal;font-size:22px;width:30px;flex:none;text-align:center;display:flex;justify-content:center}.ms-list .mi>i svg{width:24px;height:24px}
.ms-list .mi>span:first-of-type{flex:1;min-width:0}.ms-list .mi b{display:block;font-size:15px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ms-list .mi small{display:block;color:var(--mut);font-size:12px;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ms-list .mi .ms-st{flex:none;max-width:40%;color:var(--mut);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ms-list .mi .ms-st.on{color:var(--grn)}.ms-list .mi .ms-st.warn{color:var(--yel)}.ms-list .mi .ms-st.bad{color:var(--red)}
.ms-list .mi .ar{color:var(--mut);font-size:20px;flex:none}.ms-list .mi:hover{background:rgba(127,140,160,.08)}
.ms-hidebox{position:absolute!important;left:-10000px!important;top:0!important;width:360px!important;visibility:hidden!important;pointer-events:none!important}
#ms-page{display:none}.ms-pg>#ms-page{display:block}.ms-pg>*:not(#ms-page){display:none!important}
#ms-bar{display:flex;align-items:center;gap:10px;margin:0 0 12px;padding:6px 0}
#ms-bar button{min-height:44px;padding:0 14px;flex:none}#ms-bar b{font-size:17px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#ms-page>.ms-body>details>summary,#ms-page>.ms-body>section>h3:first-child,#ms-page>.ms-body>.card>h3:first-child{display:none!important}#ms-page>.ms-body>*{margin-top:0}
#ms-page>.ms-body>details.sub,#ms-page>.ms-body>details.grp{display:block!important;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px 14px}
#ms-find{min-width:44px;min-height:40px;padding:0 10px;margin-left:auto;font-size:17px;line-height:1}
#ms-q{display:none;margin:4px 0 6px}#ms-q.on{display:block}#ms-q input{width:100%;box-sizing:border-box;padding:11px 14px;font-size:15px;border-radius:12px}
.ms-list .mg.ms-none{display:none}.ms-q-none{color:var(--mut);margin:12px 4px}
body.ms-on #srch{display:none!important}
/* Schutz: the big card on top */
body[data-tab="protect"] #pr-card,body[data-tab="protect"] #sk-top #protect-box>.row:first-child>b,body[data-tab="protect"] #mode-tv,
body[data-tab="protect"] #sk-probs .prt-amp>div:first-child,#ms-page #alarm-chain>h3{display:none!important}
#sk-top{padding:12px 14px 14px}#sk-top #protect-box{margin:0}#sk-top .prt-seg{margin-top:0}
#sk-top .prt-b{min-height:64px;font-size:14px}#sk-top .prt-b .ic{font-size:22px}
.sk-status{display:flex;align-items:center;gap:8px;margin-top:10px;min-height:44px;padding:0 4px 0 12px;border-radius:12px;background:rgba(127,140,160,.1);font-size:14px}
.sk-status .sk-s{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sk-status.bad{background:rgba(255,77,77,.12);cursor:pointer}.sk-status.bad b{color:var(--red,#ff6b6b)}.sk-status.hint{cursor:pointer}
.sk-status button{min-height:36px;padding:4px 12px;flex:none}
#sk-probs{margin-top:8px}#sk-probs[hidden]{display:none}#sk-probs .prt-amp{margin-top:0}#sk-top #pr-night{margin-top:12px}
#sk-mode{padding:12px 14px}#sk-mode #mode-box{margin:0!important}
#sk-mode .mode-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:6px!important}
#sk-mode .mode-grid button{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-height:58px;padding:6px 3px!important;
  font-size:11.5px!important;line-height:1.2;text-align:center;white-space:normal;overflow-wrap:anywhere}
#sk-mode .mode-grid button .mi{font-size:20px}
#sk-mode .mode-grid button.on{outline:2px solid var(--acc,#3b8cff);background:rgba(59,140,255,.2)!important;color:var(--txt)}
@media(min-width:700px){#sk-mode .mode-grid{grid-template-columns:repeat(7,minmax(0,1fr))!important}}
</style>"""

MS_JS = r"""<script>
(function () {                                             // 639zzzg: «Mehr-Stil»
  if (window.msInit || !document.body) return; window.msInit = 1;
  const PAGE = window.MS_PAGE, CONF = (window.MS_CONF || {})[PAGE]; if (!CONF) return;
  const TX = window.MS_TX || {}, $ = s => document.querySelector(s);
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  const tr = k => ((TX[L()] || {})[k]) || ((TX.en || {})[k]) || k;
  const tt = k => (typeof t === "function" ? t(k) : tr(k));
  const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const get = k => { try { return localStorage.getItem("mw-ms-" + k); } catch (e) { return null; } };
  const put = (k, v) => { try { localStorage.setItem("mw-ms-" + k, v); } catch (e) {} };
  // ---- the state of each row: ONE function each, from the setting (c), the state at run time (s) and the rest (j) -> [text, colour] or null
  const ON = v => v ? [tr("on"), "on"] : [tr("off"), ""];
  const ST = {
    source: (c, s) => s.source_label ? [s.source_label + (s.source_status && s.source_status !== "connected" ? " · " + tr("not connected") : ""), s.source_status === "connected" ? "" : "warn"] : null,
    cams: (c, s) => { const n = (s.extra || []).length; return n ? [n + " " + (n === 1 ? tr("camera") : tr("cameras")), ""] : null; },
    servo: (c, s) => !s.servo_backend || s.servo_backend === "none" ? [tr("no head"), ""] : (s.servo && s.servo.estop ? [tr("emergency stop"), "bad"]
             : (c.track_person ? [tr("follows persons"), "on"] : [tr("ready"), ""])),
    patrol: c => ON(c.patrol), timelapse: c => ON(c.timelapse_on), zf: c => ON(c.zf_on),
    mover: (c, s) => s.mover && (s.mover.hw || s.mover.sim) ? [tr("ready"), ""] : [tr("no motor driver"), ""],
    profile: (c, s) => s.det_profile && s.det_profile.id ? [s.det_profile.name || s.det_profile.id, ""] : [tr("by hand"), ""],
    detection: c => ON(c.detection_on),
    ai: (c, s) => !c.ai_enabled ? ON(false) : (/no model/.test(s.ai_status || "") ? [tr("model missing"), "warn"] : ON(true)),
    thermal: (c, s) => !(c.thermal_on || c.thermal_alarm) ? ON(false) : (s.thermal === "connected" ? ON(true) : [tr("not connected"), "warn"]),
    thalarm: c => ON(c.thermal_alarm), thview: c => ON(c.thermal_on),
    thcam: (c, s) => s.thermal === "connected" ? [tr("connected"), ""] : [tr("not connected"), ""],
    car: c => ON(c.car_filter), rain: c => c.rain_auto ? [tr("automatic"), "on"] : ON(false), wind: c => c.wind_auto ? [tr("automatic"), "on"] : ON(false),
    lowlight: c => c.nightvision ? [tr("night vision"), "on"] : (c.lowlight_auto || c.nightvision_auto ? [tr("automatic"), "on"] : ON(false)),
    autotune: c => ON(c.auto_tune),
    lights: (c, s) => { const l = s.light_cfg || {}; if (!l.white_out && !l.ir_out) return [tr("no light connected"), ""]; return ON(l.white !== "off" || l.ir !== "off"); },
    spk: (c, s) => !(s.audio && s.audio.spk) ? [tr("no loudspeaker"), ""] : ON(c.siren_on && c.siren_on !== "off"),
    mic: (c, s) => !c.audio_in ? ON(false) : (s.audio && s.audio.mic ? ON(true) : [tr("no microphone"), ""]),
    clap: c => ON(c.clap_on), bless: c => ON(c.sneeze_on), wake: c => ON(c.wake_on),
    relay: (c, s, j) => { const n = (j.relays || []).filter(r => r.mode && r.mode !== "off").length; return !c.relays_on || !n ? ON(false) : [n + " " + tr("relay"), "on"]; },
    sensors: c => { const n = (c.sensors || []).length; return c.sens_on && n ? [n + " " + tr("sensors"), "on"] : ON(false); },
    storm: (c, s) => !c.storm_on ? ON(false) : (s.storm && (s.storm.p != null || s.storm.meter_ok) ? ON(true) : [tr("no sensor"), ""]),
    gps: (c, s) => !c.gpsmod_on ? ON(false) : (s.gpsmod && s.gpsmod.status === "fix" ? ON(true) : [tr("not connected"), "warn"]),
    batt: (c, s) => { const b = s.battery || {}; if (!(b.on && typeof b.pct === "number")) return [tr("no battery"), ""];
      const plug = (b.src === "ups" && !b.on_battery) || !!b.charging; return [(plug ? "🔌 " : "🔋 ") + Math.round(b.pct) + " %", !plug && b.pct < 15 ? "bad" : (!plug && b.pct < 30 ? "warn" : "")]; },
    eco: (c, s) => !c.eco_on ? ON(false) : (s.eco === "saving" ? [tr("saving now"), "on"] : ON(true)),
    solar: (c, s) => ON(c.solar_on && s.solar && s.solar.on),
    system: (c, s) => typeof s.cpu === "number" ? ["CPU " + Math.round(s.cpu) + " %", s.cpu >= 85 ? "bad" : (s.cpu >= 70 ? "warn" : "")] : null,
    setup: (c, s) => s.time_status === "ok" ? [tr("time ok"), ""] : [tr("check the time"), "warn"],
    wifi: (c, s) => { const h = s.hotspot || {}; return h.on ? [tr("hotspot on"), "on"] : (h.available === false && !s.wifi ? [tr("not available"), ""] : ON(false)); },
    stream: c => ON(c.web_stream), guest: (c, s) => s.guest && s.guest.active ? [tr("active"), "on"] : ON(false),
    mqtt: (c, s) => !c.mqtt_on ? ON(false) : (s.mqtt && s.mqtt.status === "connected" ? [tr("connected"), "on"] : [tr("not connected"), "warn"]),
    security: (c, s) => s.pw_set ? [tr("password set"), ""] : [tr("no password"), "warn"],
    rucksack: c => ON(c.tausch_on),
    updates: (c, s) => { const n = s.update_new && s.update_new.version; if (n) return [n + " · " + tr("ready to install"), "on"];
      const m = {auto: [tr("automatic"), "on"], dev: [tr("developer"), "on"], off: [tr("by hand"), ""]}[c.update_mode || "off"] || [String(c.update_mode), ""];
      return (c.update_url || "").trim() ? m : [m[0] + " · " + tr("no source"), "warn"]; },
    push: (c, s) => !c.notify_on ? ON(false) : ({off: [tr("not set up"), "warn"], paused: [tr("paused"), "warn"], "quiet hours": [tr("quiet hours"), ""]}[s.notify_status] || ON(true)),
    deter: (c, s) => { const spk = !!(s.audio && s.audio.spk), lamp = !!(s.light_cfg && s.light_cfg.white_out);
      return ON(["person", "big", "small", "warm"].some(g => { const a = c["deter_" + g + "_act"]; return (a === "sound" && spk) || (a === "light" && lamp) || (a === "both" && (spk || lamp)); })); },
    rec: c => ON(c.record), report: c => ON(c.report_on), theft: c => ON(c.tamper_on),
    refscan: c => ON(c.refscan_on_arm || +c.refscan_every > 0), backup: c => ON(c.backup_type && c.backup_type !== "off"),
    sched: (c, s, j) => { const n = (j.schedules || []).filter(x => x.enabled).length; return n ? [n + " " + tr("schedules active"), "on"] : ON(false); },
    presence: (c, s) => s.presence === "here" ? [tr("here"), ""] : (s.presence === "away" ? [tr("away"), ""] : null),
    camping: (c, s) => ON(!!s.camping),
    chain: (c, s) => { const P = s.protect || {}; return P.level ? [{off: tt("Off"), watch: tt("Watchful"), full: tt("Full protection")}[P.level] || P.level, P.level === "off" ? "" : "on"] : null; },
    siren: c => c.escalate_on ? [(c.escalate_siren_s || 30) + " s", "on"] : ON(false),
    health: (c, s) => { const h = s.health || {}; return h.bad ? [h.bad + " " + (h.bad === 1 ? tr("1 problem").replace(/^1 /, "") : tr("problems")), "bad"] : [tr("all ok"), "on"]; },
    fleet: c => { const n = (c.fleet || []).length; return n ? [n + " " + tr("devices"), ""] : null; },
    simconn: (c, s) => { const m = s.sim || {}; return m.on ? (m.connected || m.ok ? [tr("connected"), "on"] : [tr("not connected"), "warn"]) : ON(false); },
  };
  window.MS_ST = ST;
  // the values as the page shows them right now: /api/state leaves some settings out (e.g. update_mode, update_url) - the switches,
  // selects and fields of the page have them (the old row state read only /api/state: «Updates: aus» although automatic)
  const data = () => { const j = (typeof MAINJ !== "undefined" && MAINJ) || window.__msJ || {}, c = Object.assign({}, j.cfg || {});
    try { Object.entries(typeof ctrl !== "undefined" ? ctrl : {}).forEach(([k, x]) => { if (x && x.input) c[k] = x.type === "bool" ? x.input.checked : +x.input.value; }); } catch (e) {}
    document.querySelectorAll("select[data-key]").forEach(x => { c[x.dataset.key] = x.value; });
    document.querySelectorAll(".sl[data-key] > input, .sl[data-key] input").forEach(x => { const k = x.closest("[data-key]").dataset.key;
      c[k] = x.value || (x.type === "password" && /^••/.test(x.placeholder || "") ? "(set)" : ""); });
    return [c, j.state || window.__lastState || {}, j]; };
  // ---- the rows -----------------------------------------------------------------------------------------------------------
  let host = null, list = null, page = null, hideBox = null, cur = null; const rows = [];
  function virtFine(gv) {                                  // the unnamed fine settings of a group (no data-view of their own)
    const g = document.querySelector('[data-view="' + gv + '"]'); if (!g) return null;
    return [...g.querySelectorAll(":scope > details.sub")].find(d => !d.dataset.view) || null;
  }
  const target = id => id.startsWith("?") ? $(id.slice(1)) : id.startsWith("[") ? $(id) : id.startsWith("#") ? $(id) : (id.startsWith("~") ? virtFine(id.slice(1)) : (id.startsWith("@") ? null : document.querySelector('[data-view="' + id + '"]')));
  function iconOf(el) {
    const sm = el && (el.querySelector(":scope > summary") || el.querySelector(":scope > h2, :scope > h3"));
    const ie = sm && sm.querySelector(".gi .ie, .ie, svg"); if (ie) return ie.cloneNode(true);
    const m = sm && /^\s*(\p{Extended_Pictographic}️?)/u.exec(sm.textContent); return document.createTextNode(m ? m[1] : "•");
  }
  function titleOf(el) {
    const sm = el && (el.querySelector(":scope > summary") || el.querySelector(":scope > h2, :scope > h3")); if (!sm) return el && el.id ? el.id : "";
    const cl = sm.cloneNode(true); cl.querySelectorAll(".mst, small, .gi").forEach(n => n.remove());
    const sn = cl.querySelector(".sn, b, h2, h3, span[data-i18n]"); let x = (sn || cl).textContent;
    x = x.replace(/^\s*(\p{Extended_Pictographic}️?\s*)+/u, "").replace(/\s*\(\d+\)\s*$/, "");
    return x.trim().split("\n")[0].trim().slice(0, 60);
  }
  function build() {
    // Live (owner: nothing else changes there): only «Gehtest» and «Tipps & Tricks» as rows at the bottom of the live part
    const anchor = PAGE === "settings" || PAGE === "protect" ? $("#settings") : (PAGE === "sim" ? $("#c-conn") : (PAGE === "cams" ? $("section.card:has(#btn-scan)")
                   : (PAGE === "live" ? ($("#wt-card") && $("main>section")) : $("#statcard"))));
    if (!anchor || !anchor.parentNode) return false;
    host = PAGE === "live" ? anchor : anchor.parentNode;
    list = E("div", "ms-list"); list.id = "ms-list";
    page = E("div"); page.id = "ms-page"; const bar = E("div"); bar.id = "ms-bar"; const back = E("button", "sec", tr("‹ Back")); back.type = "button"; back.id = "ms-back";
    back.onclick = () => (history.state && history.state.ms ? history.back() : close()); bar.append(back, E("b")); page.append(bar, E("div", "ms-body"));
    hideBox = E("div", "ms-hidebox"); hideBox.id = "ms-hide";
    if (PAGE === "live") host.appendChild(list); else anchor.before(list);
    if (PAGE === "settings" || PAGE === "protect") { anchor.classList.add("ms-hidebox"); document.body.classList.add("ms-on"); }
    host.append(page, hideBox);
    CONF.forEach(([gk, items]) => {
      const sec = E("section", "mg"); sec.append(E("h2", "mgh", tr(gk))); const box = E("div", "mgl"); sec.appendChild(box); list.appendChild(sec);
      items.forEach(([id, dk, sk, ic, ti, href]) => {
        const r = E(href ? "a" : "button", "mi"); if (href) r.href = href; else r.type = "button"; r.dataset.ms = id;
        const i = E("i"), sp = E("span"), b = E("b"); sp.append(b, E("small", "", dk ? tr(dk) : ""));
        const st = E("span", "ms-st"); r.append(i, sp, st, E("span", "ar", "›")); box.appendChild(r);
        const row = {id, dk, sk, ic, ti, href, r, i, b, st}; rows.push(row);
        if (!href) r.onclick = () => open(row, true);
      });
    });
    // nothing gets lost: every group / topic of this tab that no row shows gets a row under «More topics»
    if (PAGE === "settings" || PAGE === "protect") {
      const mine = el => ((el.closest(".grp") || el).dataset.tabOf || "settings") === PAGE;
      const covered = el => rows.some(x => { const t_ = x.href ? null : target(x.id); return t_ && (t_ === el || t_.contains(el) || el.contains(t_)); });
      const extra = [...document.querySelectorAll("#settings details.grp, #settings details.grp > details.sub")].filter(d => mine(d) && !covered(d)
        && !(d.classList.contains("grp") && d.querySelector(":scope > details.sub")) && d.id !== "pr-card");
      if (extra.length) { const sec = E("section", "mg"); sec.append(E("h2", "mgh", tr("More topics"))); const box = E("div", "mgl"); sec.appendChild(box); list.appendChild(sec);
        extra.forEach(d => { if (!d.dataset.view) d.dataset.msx = "x" + rows.length; const id = d.dataset.view || ("[data-msx=" + d.dataset.msx + "]");
          const r = E("button", "mi"); r.type = "button"; r.dataset.ms = id; const i = E("i"), sp = E("span"), b = E("b"); sp.append(b, E("small", "", ""));
          const st = E("span", "ms-st"); r.append(i, sp, st, E("span", "ar", "›")); box.appendChild(r);
          const row = {id, dk: "", sk: "", r, i, b, st}; rows.push(row); r.onclick = () => open(row, true); }); }
    }
    if (PAGE === "live") return true;
    // the 🔍 top right: searches all rows (also the texts inside their pages)
    const nav = $("header>nav.subnav");
    const find = E("button", "sec", "🔍"); find.type = "button"; find.id = "ms-find"; find.title = tr("Search all settings"); find.setAttribute("aria-label", find.title);
    const q = E("div"); q.id = "ms-q"; const qi = E("input"); qi.type = "search"; qi.id = "ms-qi"; qi.placeholder = tr("Search all settings") + " …"; q.appendChild(qi); list.before(q);
    find.onclick = () => { const o = !q.classList.contains("on"); q.classList.toggle("on", o); if (o) { if (cur) close(); qi.focus(); } else { qi.value = ""; filter(""); } };
    qi.oninput = () => filter(qi.value);
    if (nav) nav.appendChild(find); else { const rr = E("div"); rr.style.cssText = "display:flex;justify-content:flex-end"; rr.appendChild(find); list.before(rr); }
    return true;
  }
  let none = null;
  function filter(v) {
    const w = v.trim().toLowerCase();
    rows.forEach(x => { const el = x.href ? null : target(x.id);
      const txt = (x.b.textContent + " " + (x.dk ? tr(x.dk) : "") + " " + x.st.textContent + " " + (el ? el.textContent : "")).toLowerCase(); x.hit = !w || txt.includes(w); });
    paint(); let any = false;
    list.querySelectorAll(".mg").forEach(g => { const n = [...g.querySelectorAll(".mi")].some(m => !m.hidden); g.classList.toggle("ms-none", !n); if (n) any = true; });
    if (!none) { none = E("div", "ms-q-none", tr("Nothing found")); list.appendChild(none); } none.hidden = any || !w;
  }
  // a row is shown when its part exists and the page would show it (Simple / Expert, rights, data-need …)
  function shown(el) { if (!el || el.hidden) return false; return getComputedStyle(el).display !== "none"; }
  function paint() {
    if (!list) return;
    const [c, s, j] = data();
    rows.forEach(x => {
      const el = x.href ? null : target(x.id);
      const vis = (x.href ? true : (x === cur || shown(el))) && x.hit !== false;
      x.r.hidden = !vis; if (!vis) return;
      if (!x.i.firstChild) x.i.appendChild(x.ic ? document.createTextNode(x.ic) : iconOf(el));
      const ti = x.ti ? ((TX[L()] || {})[x.ti] ? tr(x.ti) : tt(x.ti)) : titleOf(el); if (ti && x.b.textContent !== ti) x.b.textContent = ti;
      let v = null; try { v = x.sk && ST[x.sk] ? ST[x.sk](c, s, j) : null; } catch (e) { v = null; }
      const tx = v ? v[0] : "", cl = "ms-st" + (v && v[1] ? " " + v[1] : ""); if (x.st.textContent !== tx) x.st.textContent = tx; if (x.st.className !== cl) x.st.className = cl;
    });
    list.querySelectorAll(".mg").forEach(g => { g.hidden = ![...g.querySelectorAll(".mi")].some(m => !m.hidden); });
  }
  // ---- one page per topic: the part moves into #ms-page and back to its place ---------------------------------------------
  let mark = null;
  function open(row, push) {
    const el = row.href ? null : target(row.id); if (!el) return;
    if (cur) close(true);
    const h = list.parentNode; if (h && h !== host) { host.classList.remove("ms-pg"); host = h; }      // Live moves its parts (536): the list's place counts
    if (page.parentNode !== host) host.appendChild(page); if (hideBox.parentNode !== host) host.appendChild(hideBox);
    cur = row; mark = document.createComment("ms"); el.before(mark);
    page.lastChild.appendChild(el); page.querySelector("#ms-bar b").textContent = row.b.textContent || titleOf(el);
    if (el.tagName === "DETAILS") { el.dataset.msWasOpen = el.open ? "1" : ""; el.open = true; }
    el.hidden = false; host.classList.add("ms-pg"); document.body.classList.add("ms-sub");
    if (push) { try { history.pushState({ms: row.id}, "", "#s=" + encodeURIComponent(row.id)); } catch (e) {} }
    window.scrollTo(0, 0);
  }
  function close(keep) {
    if (!cur) return; const el = page.lastChild.firstChild;
    if (el && mark && mark.parentNode) { mark.replaceWith(el); if (el.tagName === "DETAILS" && !el.dataset.msWasOpen) el.open = false; }
    else if (el) hideBox.appendChild(el);
    mark = null; const was = cur; cur = null;
    if (!keep) { host.classList.remove("ms-pg"); document.body.classList.remove("ms-sub"); paint(); setTimeout(() => was.r.scrollIntoView({block: "center"}), 0);
      if (location.hash.startsWith("#s=")) { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {} } }
  }
  window.addEventListener("popstate", e => { const id = e.state && e.state.ms; if (id) { const r = rows.find(x => x.id === id); if (r) open(r, false); } else close(); });
  // old links: ?open=<view> and #s=<id> open the subpage (also when the view sits inside a row's part)
  function openId(v, push) {
    let r = rows.find(x => x.id === v || x.id === "#" + v);
    if (!r) { const el = document.querySelector('[data-view="' + v + '"]');
      if (el) r = rows.find(x => { const t_ = x.href ? null : target(x.id); return t_ && (t_ === el || t_.contains(el)); }); }
    if (r) { open(r, push); return true; }
    return false;
  }
  window.msOpen = v => openId(v, true);
  if (typeof tabOpen === "function") { const o = tabOpen; tabOpen = function (v) {
    const d = document.querySelector('#settings [data-view="' + v + '"], #ms-page [data-view="' + v + '"]'), g = d && (d.closest(".grp") || d), tab = g && (g.dataset.tabOf || "settings");
    if (d && tab === document.body.dataset.tab && openId(v, true)) return; return o.apply(this, arguments); }; }
  // ---- Schutz: the big card (Off / Watchful / Full, one status line, the problems), the mode tiles ---------------------------
  let top = null, stl = null, probs = null, mode = null; const virt = {};
  function protectTop() {
    if (PAGE !== "protect" || !list) return;
    const pb = $("#protect-box"); if (!pb) return;
    if (!top) { top = E("div", "card sk-card"); top.id = "sk-top"; stl = E("div", "sk-status"); stl.id = "sk-status"; stl.setAttribute("role", "status");
      probs = E("div"); probs.id = "sk-probs"; probs.hidden = get("probs") !== "1";
      stl.onclick = () => { if (!/bad|hint/.test(stl.className)) return; probs.hidden = !probs.hidden; put("probs", probs.hidden ? "0" : "1"); stl.dataset.k = ""; skPaint(); };
      mode = E("div", "card sk-card"); mode.id = "sk-mode";
      ["tools", "siren", "dev", "where"].forEach(k => { const v = E("div", "card"); v.id = "sk-v-" + k; v.style.padding = "12px 14px"; hideBox.appendChild(v); virt[k] = v; });
      const q = $("#ms-q"); (q || list).before(top, mode); }
    const keep = (box, el) => { if (el && el.parentNode !== box) box.appendChild(el); };
    keep(top, pb); keep(top, stl); keep(top, probs); keep(top, $("#pr-night")); keep(top, $("#pr-err")); keep(mode, $("#mode-box"));
    const amp = pb.querySelector(":scope > .prt-amp"); if (amp) { probs.textContent = ""; probs.appendChild(amp); }
    const parts = {tools: [".btns", ".prt-test"], siren: ["details.more"], dev: [".prt-dev", ".prt-things"]};
    if ([".btns", ".prt-test", "details.more", ".prt-dev", ".prt-things"].some(q => pb.querySelector(":scope > " + q)))
      Object.entries(parts).forEach(([k, qs]) => { virt[k].textContent = "";
        qs.forEach(q => { const x = pb.querySelector(":scope > " + q); if (x) { virt[k].appendChild(x); if (x.tagName === "DETAILS") { x.open = true; x.firstChild.style.display = "none"; } } }); });
    const ps = $("#pr-state"); [ps && ps.parentNode, $("#pr-disarm") && $("#pr-disarm").parentNode, $("#pr-time"), $("#pr-gps"), $("#pr-env")]
      .forEach(x => { if (x && x.closest("#pr-card")) virt.where.appendChild(x); });
    [$("#pl-card"), $("#pr-wt"), $("#hcard"), $("#alarm-chain")].forEach(x => { if (x && !x.closest("#ms-hide, #ms-page")) hideBox.appendChild(x); });
    skPaint();
  }
  function skPaint() {
    if (!stl) return;
    const S = window.__lastState || {}, P = S.protect || {}, b = S.battery || {};
    const items = P.items || [], bad = items.filter(x => !x.minor).length, minor = items.length - bad, parts = [];
    if (b.on && typeof b.pct === "number") { const plug = (b.src === "ups" && !b.on_battery) || !!b.charging;
      parts.push((plug ? "🔌 " : "🔋 ") + Math.round(b.pct) + " %"); if (plug) parts.push(b.charging ? tt("charging") : tr("on mains power")); }
    const key = [parts.join("|"), bad, minor, probs.hidden, L()].join("~"); if (stl.dataset.k === key) return; stl.dataset.k = key;
    stl.textContent = ""; stl.className = "sk-status" + (bad ? " bad" : (minor ? " hint" : ""));
    const sp = E("span", "sk-s"); if (parts.length) sp.append(parts.join(" · ") + " · ");
    if (bad) sp.append(E("b", "", "🔴 " + (bad === 1 ? tr("1 problem") : bad + " " + tr("problems"))));
    else sp.append("✅ " + tr("all ok") + (minor ? " · " + (minor === 1 ? tr("1 hint") : minor + " " + tr("hints")) : ""));
    stl.appendChild(sp);
    if (bad || minor) { const f = E("button", bad ? "" : "sec", (bad ? tr("Fix") + " " : "") + (probs.hidden ? "›" : "⌄")); f.type = "button"; stl.appendChild(f); }
    if (!(bad || minor)) probs.hidden = true;
  }
  // ---- start: when the page has built its parts ----------------------------------------------------------------------------
  function tick() { if (!list && !build()) return; try { protectTop(); } catch (e) {}
    if (PAGE === "sim" || PAGE === "history" || PAGE === "cams" || PAGE === "live") rows.forEach(x => { const el = x.href ? null : target(x.id);   // the cards of the rows: out of sight, at hand for their page
      if (el && x !== cur && !el.closest("#ms-hide, #ms-page")) { const m = document.createComment("ms-home"); el.before(m); x.home = m; hideBox.appendChild(el); } });
    paint(); }
  let started = false;
  const go = () => { tick(); if (!list || started) return; started = true;
    const h = decodeURIComponent((location.hash.match(/^#s=(.+)$/) || [])[1] || ""); if (h) openId(h, false); };
  setTimeout(go, 700); setInterval(() => { if (!started) go(); else tick(); }, 1000);
  if (PAGE === "sim" || PAGE === "history" || PAGE === "cams") { const f = async () => { try { window.__msJ = await (await fetch("/api/state", {cache: "no-store"})).json(); } catch (e) {} };
    f(); setInterval(f, 3000); }
})();
</script>"""


def ms_tx():
    keys = list(_HX_MS) + list(_DX_MS)
    out = {"de": {k: DE.get(k, k) for k in keys}, "en": dict({k: k for k in _HX_MS}, **_DX_EN)}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or k for k in keys}
    return out


# ---- the TV view under «Mehr» (the same buttons as before in the card «Modus») -------------------------------------------
SK_TV_JS = r"""<script>
(function () {                                             // 639zzzg: «📺 TV-Anzeige» under «Mehr»
  const main = document.querySelector("main"); if (!main || document.getElementById("sk-tv")) return;
  const c = document.createElement("div"); c.id = "sk-tv"; c.className = "mi"; c.style.cssText = "display:block;cursor:default"; c.hidden = true;
  const ab = document.getElementById("m-about"); if (ab) ab.before(c); else main.appendChild(c);
  const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  let k0 = "";
  async function go() {
    let j = null; try { j = await (await fetch("/api/state", {cache: "no-store"})).json(); } catch (e) {}
    const T = j && j.state && j.state.tv; if (!T) { setTimeout(go, 15000); return; }
    const key = [T.on, T.browser, T.auto, T.url, T.msg, T.sim, T.sim_ok, typeof LANG !== "undefined" ? LANG : ""].join("|");
    if (key !== k0) { k0 = key; c.hidden = false; c.textContent = "";
      const h = E("div", "", ""); h.style.cssText = "display:flex;align-items:center;gap:12px"; h.append(E("i", "", "📺"), E("b", "", t("TV view"))); c.appendChild(h);
      const r = E("div", "row"); r.style.cssText = "margin-top:10px;flex-wrap:wrap;gap:6px;display:flex";
      const tv = async b => { const x = await post("/api/tv", b); if (!x || !x.ok) alert("⚠ " + ((x && x.error) || "error")); k0 = ""; go(); };
      if (T.browser) { const b = E("button", T.on ? "" : "sec", T.on ? t("Stop on the HDMI") : t("Show on the HDMI")); b.type = "button"; b.onclick = () => tv({on: !T.on}); r.append(b); }
      if (T.sim_ok) { const b = E("button", T.sim ? "" : "sec", T.sim ? t("Stop the TV mode of the simulator") : "🎮 " + t("TV mode in the 3D simulator")); b.type = "button"; b.onclick = () => tv({sim: !T.sim}); r.append(b); }
      const a = E("a", "btn sec", "🔗 " + t("Open the link")); a.href = T.url; a.target = "_blank"; r.append(a);
      const cp = E("button", "sec", "📋"); cp.type = "button"; cp.title = t("Copy the link");
      cp.onclick = () => { try { navigator.clipboard.writeText(location.origin + T.url); } catch (e) {} }; r.append(cp);
      if (typeof qrBtn === "function") r.append(qrBtn(location.origin + T.url, t("TV view"), {secret: true}));
      c.appendChild(r);
      const l = E("label", "row pr-sw"); l.style.cssText = "display:flex;gap:10px;align-items:center;margin-top:8px"; const cb = E("input", "sw"); cb.type = "checkbox"; cb.checked = !!T.auto;
      cb.onchange = () => post("/api/tv", {auto: cb.checked}); const sp = E("span", "mut", t("tv-auto")); sp.style.flex = "1"; l.append(sp, cb); c.appendChild(l);
      if (T.msg && T.msg !== "on" && T.msg !== "off") c.appendChild(E("div", "err", t(T.msg))); }
    setTimeout(go, 5000);
  }
  go();
})();
</script>"""


def _sk_tv_de():
    """the German TV texts of the main page (530) - the page «Mehr» has its own I18N.de"""
    m = re.search(r'Object\.assign\(I18N\.de, (\{"TV view".*?\})\);', WEB_PAGE)
    try:
        d = json.loads(m.group(1)) if m else {}
    except Exception:
        d = {}
    return {k: v for k, v in d.items() if k in ("TV view", "Stop on the HDMI", "Show on the HDMI", "Open the link", "Copy the link", "Link copied",
                                                  "Stop the TV mode of the simulator", "TV mode in the 3D simulator", "tv-auto")}


_MS_ACTIVE = {"settings": "settings", "protect": "protect", "sim": "sim", "rec": "history", "cams": "cams", "live": "live"}
_render_page_639zzzg = render_page


# wraps: render_page
def render_page(page, active):                                 # + 639zzzg: «Mehr-Stil» on Einstellungen, Schutz, Sim, Verlauf; the TV view under «Mehr»
    out = _render_page_639zzzg(page, active)
    pg = _MS_ACTIVE.get(active)
    if pg == "history" and 'id="statcard"' not in out:
        pg = None                                              # the other pages of «Verlauf» (timeline, diary …) stay as they are
    if pg in ("settings", "protect") and 'id="settings"' not in out:
        pg = None
    if pg and "</body>" in out and "</head>" in out:
        out = out.replace("</head>", MS_CSS + "</head>", 1)
        i = out.rfind("</body>")
        tag = ("<script>window.MS_PAGE=" + json.dumps(pg) + ";window.MS_CONF=" + json.dumps(MS_PAGES, ensure_ascii=False) + ";window.MS_TX="
               + json.dumps(ms_tx(), ensure_ascii=False).replace("</", "<\\/") + ";</script>")
        out = out[:i] + tag + MS_JS + out[i:]
    elif active == "more" and 'id="m-about"' in out and "</body>" in out:
        de = "<script>try{Object.assign(I18N.de," + json.dumps(_sk_tv_de(), ensure_ascii=False).replace("</", "<\\/") + ")}catch(e){}</script>"
        i = out.rfind("</body>")
        out = out[:i] + de + SK_TV_JS + out[i:]
    return out


def ms_selftest():
    for k in list(_HX_MS) + list(_DX_MS):
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzzg: text " + k
    assert set(_DX_EN) == set(_DX_MS), "639zzzg: English row lines"
    for pg, groups in MS_PAGES.items():
        for g, items in groups:
            assert g in _HX_MS, "639zzzg: group " + g
            for it in items:
                assert not it[1] or it[1] in _DX_MS, "639zzzg: line " + it[1]
                assert not it[2] or ("    " + it[2] + ": ") in MS_JS or (", " + it[2] + ": ") in MS_JS, "639zzzg: state function " + it[2]
    p = render_page(WEB_PAGE, "settings")
    assert "ms-css" in p and "msInit" in p and 'MS_PAGE="settings"' in p, "639zzzg: settings"
    m = render_page(MORE_PAGE, "more")
    assert "sk-tv" in m and '"TV view"' in m, "639zzzg: TV view under «Mehr»"
    return "rows with one state function each, one page per topic, 🔍 over all rows; Schutz on top; TV view under «Mehr»"


SELFTEST_EXTRA.append(("«Mehr» style on all pages (639zzzg)", ms_selftest))


# ---- the window (Tkinter): the same rows - a click shows ONE topic with «‹ Zurück» (570 _build_sidebar calls _ms_tk_rows) ----------
def _mst(on):
    return (tr("on"), "on") if on else (tr("off"), "")


def _ms_tk_servo():
    sb = str(STATE.get("servo_backend") or "")
    if not sb or sb == "none":
        return tr("no head"), ""
    if (STATE.get("servo") or {}).get("estop"):
        return tr("emergency stop"), "bad"
    return (tr("follows persons"), "on") if CFG.get("track_person") else (tr("ready"), "")


def _ms_tk_batt():
    b = STATE.get("battery") or {}
    if not (b.get("on") and isinstance(b.get("pct"), (int, float))):
        return tr("no battery"), ""
    plug = (b.get("src") == "ups" and not b.get("on_battery")) or bool(b.get("charging"))
    p = b["pct"]
    return ("🔌 " if plug else "🔋 ") + "%d %%" % round(p), "" if plug else ("bad" if p < 15 else ("warn" if p < 30 else ""))


def _ms_tk_updates():
    m = {"auto": (tr("automatic"), "on"), "dev": (tr("developer"), "on"), "off": (tr("by hand"), "")}.get(CFG.get("update_mode") or "off", (str(CFG.get("update_mode")), ""))
    return m if str(CFG.get("update_url") or "").strip() else (m[0] + " · " + tr("no source"), "warn")


def _ms_tk_push():
    if not CFG.get("notify_on"):
        return _mst(False)
    return {"off": (tr("not set up"), "warn"), "paused": (tr("paused"), "warn"), "quiet hours": (tr("quiet hours"), "")}.get(STATE.get("notify_status"), _mst(True))


# one function per topic (the same rules as MS_ST on the web page)
MS_TK_ST = {
    "Camera / Servos": _ms_tk_servo, "Patrol": lambda: _mst(CFG.get("patrol")), "Timelapse": lambda: _mst(CFG.get("timelapse_on")),
    "Window to the past": lambda: _mst(CFG.get("zf_on")), "Detection": lambda: _mst(CFG.get("detection_on")),
    "AI detection": lambda: _mst(False) if not CFG.get("ai_enabled") else ((tr("model missing"), "warn") if "no model" in str(STATE.get("ai_status") or "") else _mst(True)),
    "Thermal camera": lambda: _mst(False) if not (CFG.get("thermal_on") or CFG.get("thermal_alarm")) else (_mst(True) if STATE.get("thermal") == "connected" else (tr("not connected"), "warn")),
    "Vehicle filter": lambda: _mst(CFG.get("car_filter")), "Rain": lambda: (tr("automatic"), "on") if CFG.get("rain_auto") else _mst(False),
    "Wind": lambda: (tr("automatic"), "on") if CFG.get("wind_auto") else _mst(False),
    "Low light": lambda: (tr("night vision"), "on") if CFG.get("nightvision") else ((tr("automatic"), "on") if CFG.get("lowlight_auto") or CFG.get("nightvision_auto") else _mst(False)),
    "Auto-tune": lambda: _mst(CFG.get("auto_tune")),
    "Lights": lambda: (tr("no light connected"), "") if not ((STATE.get("light_cfg") or {}).get("white_out") or (STATE.get("light_cfg") or {}).get("ir_out"))
    else _mst((STATE.get("light_cfg") or {}).get("white") != "off" or (STATE.get("light_cfg") or {}).get("ir") != "off"),
    "Loudspeaker": lambda: (tr("no loudspeaker"), "") if not (STATE.get("audio") or {}).get("spk") else _mst(CFG.get("siren_on") and CFG.get("siren_on") != "off"),
    "Microphone": lambda: _mst(False) if not CFG.get("audio_in") else (_mst(True) if (STATE.get("audio") or {}).get("mic") else (tr("no microphone"), "")),
    "Clap switch": lambda: _mst(CFG.get("clap_on")), "Bless you": lambda: _mst(CFG.get("sneeze_on")), "Wake-up alarm": lambda: _mst(CFG.get("wake_on")),
    "Relays": lambda: _mst(CFG.get("relays_on") and any((r or {}).get("mode", "off") != "off" for r in (CFG.get("relays") or []))),
    "Extra sensors": lambda: _mst(CFG.get("sens_on") and CFG.get("sensors")),
    "Storm warning": lambda: _mst(False) if not CFG.get("storm_on") else (_mst(True) if (STATE.get("storm") or {}).get("p") is not None or (STATE.get("storm") or {}).get("meter_ok") else (tr("no sensor"), "")),
    "GPS module": lambda: _mst(CFG.get("gpsmod_on")), "Battery": _ms_tk_batt, "Power saving": lambda: _mst(CFG.get("eco_on")),
    "Solar panel": lambda: _mst(CFG.get("solar_on")), "Web stream": lambda: _mst(CFG.get("web_stream")),
    "Guest access": lambda: (tr("active"), "on") if (STATE.get("guest") or {}).get("active") else _mst(False),
    "MQTT / Home Assistant": lambda: _mst(CFG.get("mqtt_on")), "Updates": _ms_tk_updates, "Notifications": _ms_tk_push,
    "Recording": lambda: _mst(CFG.get("record")), "Night report": lambda: _mst(CFG.get("report_on")), "Theft protection": lambda: _mst(CFG.get("tamper_on")),
    "Reference scan": lambda: _mst(CFG.get("refscan_on_arm") or float(CFG.get("refscan_every") or 0) > 0),
    "Backup": lambda: _mst(CFG.get("backup_type") and CFG.get("backup_type") != "off"), "Camping / protection": lambda: _mst(STATE.get("camping")),
}


def ms_tk_state(sec):
    """(text, level) of a topic in the window, or ("", "") when it has no state; a group never has one"""
    f = MS_TK_ST.get(sec)
    try:
        return f() if f else ("", "")
    except Exception:
        return "", ""


def _ms_tk_rows(self, inner, tab, groups):
    """570 _build_sidebar: instead of the cards with the topics inside - the rows; one chosen topic = its page with «‹ Zurück»"""
    def secs(items):
        return [x for x in items if x and (x in TK_PSEUDO or (x in SECTIONS and self.is_shown("sec:" + x) and (tab == "sim" or not simple_hidden(None, x))))]
    allg = [(gid, name, secs(items)) for gid, name, items in groups]
    allg = [g for g in allg if g[2]]
    cur = getattr(self, "_ms_cur", None)
    if cur and any(cur in g[2] for g in allg):
        card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
        top = tk.Frame(card, bg=C["panel"]); top.pack(fill="x")
        b = ttk.Button(top, text=tr("‹ Back"), command=lambda: self._ms_go(None)); b.pack(side="left")
        self._ms_back = b
        tk.Label(top, text=tr(MENU_TITLES.get(cur, cur)), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), anchor="w").pack(side="left", padx=10)
        body = tk.Frame(card, bg=C["panel"]); body.pack(fill="x", pady=(8, 0))
        self._build_section(cur, body)
        self._ms_rows, self._ms_groups = [], []
        return True
    self._ms_cur = None
    self._ms_groups = allg
    self._ms_box = tk.Frame(inner, bg=C["bg"]); self._ms_box.pack(fill="x")
    self._ms_fill("")
    self._ms_tick()
    return True


def _ms_fill(self, q):
    """the rows (only those with the search word); a group heading above its card - no state on a group"""
    box = self._ms_box
    for w in list(box.winfo_children() or []):
        w.destroy()
    self._ms_rows = []
    q = (q or "").strip().lower()
    for gid, name, secs in self._ms_groups:
        hit = []
        for sec in secs:
            words = " ".join([tr(name), tr(MENU_TITLES.get(sec, sec)), tr(sec)] + [tr(t_[2]) for lst in (TOGGLES, SLIDERS, TEXTS) for t_ in lst if t_[0] == sec]).lower()
            if not q or q in words:
                hit.append(sec)
        if not hit:
            continue
        tk.Label(box, text=tr(name), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), anchor="w").pack(fill="x", pady=(10, 4))
        card = tk.Frame(box, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"]); card.pack(fill="x")
        for n, sec in enumerate(hit):
            if n:
                tk.Frame(card, bg=C["line"], height=1).pack(fill="x")
            r = tk.Frame(card, bg=C["panel"], cursor="hand2", padx=10, pady=8); r.pack(fill="x")
            ic = tk.Label(r, text=TK_SUB_ICONS.get(sec, "•"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 12), width=2, cursor="hand2")
            ar = tk.Label(r, text="›", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 13), cursor="hand2")
            st = tk.Label(r, text="", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), cursor="hand2")
            tl = tk.Label(r, text=tr(MENU_TITLES.get(sec, sec)), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w", cursor="hand2")
            ic.pack(side="left"); ar.pack(side="right"); st.pack(side="right", padx=(6, 6)); tl.pack(side="left", fill="x", expand=True, padx=(6, 0))
            for w_ in (r, ic, ar, st, tl):
                w_.bind("<Button-1>", lambda e, s=sec: self._ms_go(s))
            self._ms_rows.append((sec, st))
    if q and not self._ms_rows:
        tk.Label(box, text=tr("Nothing found"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w").pack(fill="x", pady=(8, 0))
    self._ms_paint()


def _ms_paint(self):
    for sec, st in getattr(self, "_ms_rows", []):
        try:
            if not st.winfo_exists():
                continue
            txt, lv = ms_tk_state(sec)
            col = {"on": C["grn"], "warn": C["yel"], "bad": C["red"]}.get(lv, C["mut"])
            if st.cget("text") != txt or st.cget("fg") != col:
                st.config(text=txt, fg=col)
        except Exception:
            pass


def _ms_tick(self):
    if getattr(self, "_ms_job", None):
        return
    def run():
        self._ms_job = None
        if getattr(self, "_ms_rows", None):
            self._ms_paint()
            self._ms_job = self.root.after(2000, run)
    self._ms_job = self.root.after(2000, run)


def _ms_go(self, sec):
    """open one topic (or back to the rows): the panel is built again"""
    self._ms_cur = sec
    self._rebuild()


_ms_tk_search_before = None


def _ms_tk_search(self):
    """the search field: in the rows view it filters the rows (a click opens the topic)"""
    if getattr(self, "_ms_box", None) is not None and getattr(self, "_ms_groups", None) and not getattr(self, "_ms_cur", None):
        try:
            q = self.search_var.get()
            try:
                self.search_ph.place_forget() if q.strip() else self.search_ph.place(in_=self.search_ph.master.winfo_children()[1], x=1, rely=0.5, anchor="w")
            except (tk.TclError, IndexError):
                pass
            self._ms_fill(q)
            return
        except Exception:
            pass
    return _ms_tk_search_before(self)


def _ms_tk_tab(self, tid):
    self._ms_cur = getattr(self, "_ms_next", None)             # another tab: the rows of that tab (a favourite may name its topic, 639zzzi)
    self._ms_next = None
    return _ms_tk_tab_before(self, tid)


if "App" in globals():
    _ms_tk_search_before = App._search
    # wraps: App._search
    _ms_tk_tab_before = App._tab
    # wraps: App._tab
    App._ms_tk_rows, App._ms_fill, App._ms_paint, App._ms_tick, App._ms_go = _ms_tk_rows, _ms_fill, _ms_paint, _ms_tick, _ms_go
    App._search, App._tab = _ms_tk_search, _ms_tk_tab
