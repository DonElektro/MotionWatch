#@ MoveEye – Teil 639u: Fehler-QR – neben jeder Fehlermeldung ein QR-Code bzw. Knopf «Beheben»: gemeinsamer Fehler-Katalog (simulator3d/fehler_katalog.json), Seite /hilfe/fehler/<KENNUNG>, «Jetzt beheben» nur für den Besitzer (POST + CSRF), QR im Fenster, im Bild «NO CAMERA», auf SmallTV und TV, Link in Push-Meldungen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Besitzer (01.11.2026): neben jeder Fehlermeldung ein QR-Code bzw. Knopf, der das Problem löst.
#   Katalog: simulator3d/fehler_katalog.json (eine Datei für MoveEye und den Simulator, Ergänzung zu ui_gemeinsam.json), beim
#     Bauen hier als FEHLER_KATALOG eingebettet (werkzeuge/bauen.py fehler_katalog_einbetten; bleibt in der Hauptdatei, die Hilfe
#     geht auch ohne Zusatzdaten). Pro Fehler: id, titel, text, schritte, optional aktion – in de / en / fr / it / rm.
#   Zuordnung: Selbstdiagnose (health_check, 120) -> jedes Teil mit «bad» (bzw. «warn», wenn der Fehler «warn» ist) bekommt
#     «fehler»: {id, path, url, fix, tok}. Neu in der Selbstdiagnose (nur ergänzt): «Simulator» (Simulation an, aber keine
#     Bilder), «Update» (letztes Update fehlgeschlagen), «Zusatzdaten» (Datei fehlt).
#   Seite /hilfe/fehler/<ID>: Erklärung, Schritte, «Jetzt beheben» (Formular, POST /hilfe/fehler/<ID>/beheben mit CSRF-Schlüssel)
#     oder – ohne automatische Lösung – «folge den Schritten». /hilfe/fehler/ = alle Fehler (die aktiven zuerst).
#   Beheben: nur der Besitzer (Rolle admin, kein App-Schlüssel) nach Anmeldung (Passwort gesetzt; ohne Passwort nur am Pi
#     selbst), immer POST, CSRF-Schlüssel = HMAC(Geheimnis dieses Laufs, Benutzer + Kennung), dazu prüft 550 «Origin».
#     JSON: POST /api/fehler/fix {id, csrf}; GET /api/fehler = aktive Fehler (den Schlüssel bekommt nur der Besitzer).
#   Aktionen (bestehende Funktionen): kamera_neu (Kamera neu öffnen wie sim_auto_adopt), dienst_neu (selfheal_restart, 145 –
#     mit Bremse), ki_laden (ai_model_download), speicher (cleanup_recordings, tl_cleanup, rec_clean_tmp, zusatz_aufraeumen),
#     update (update_check + update_install), zusatzdaten (zusatz_holen + zusatz_restart, 397), wlan (wifi_scan + wifi_connect
#     zum stärksten gespeicherten Netz), push_test (push_test_one), sim_verbinden (sim_scan + sim_auto_adopt + Kamera neu),
#     sim_neustart / sim_notfall (an den Simulator: /control {"action": "fehler", "do": "fix"}).
#   QR-Inhalt: nur <Adresse von MoveEye>/hilfe/fehler/<ID> – keine Passwörter, keine Schlüssel (fx_url). Erzeugt mit qr_svg /
#     qr_png / qr_matrix (110, wie 587).
#   Anzeige: Web-Selbstdiagnose (530 healthLoad ruft fxDeco: Handy/Touch = Knopf «Beheben», PC = Knopf + kleiner QR-Knopf),
#     Fenster (Selbstdiagnose: «🛠 Hilfe & QR» öffnet fx_tk_dialog mit QR und «Jetzt beheben»), Bild «NO CAMERA FOUND» (QR oben
#     links, auch Web-Live und TV), SmallTV (bei einem aktiven Fehler alle 20 s abwechselnd mit der Statusseite), TV-Seite
#     (/tv/…: Kasten mit QR), Push (Link-Zeile in «Kamera weg», «Erkennung gestört», Selbstheilung …).
#   Simulator: scripts/fehler_hilfe.gd liest dieselbe Datei, zeichnet den QR selbst (eigener Encoder, gleiche Regeln) und zeigt
#     ohne Verbindung die Anleitung ohne QR.
# ----------------------------------------------------------------------------
import hmac as _fx_hmac

FEHLER_KATALOG = json.loads(r"""{
 "v": 1,
 "_hinweis": "Gemeinsamer Fehler-Katalog MoveEye ↔ MoveEye Sim (Paket «Fehler-QR», Elektro 01.11.2026), Ergänzung zu ui_gemeinsam.json. Pro Fehler: Kennung, Titel, Erklärung, Schritte und optional eine Aktion, alles in de / en / fr / it / rm. MoveEye bettet die Datei beim Bauen ein (werkzeuge/bauen.py → quelle/639u_fehler_hilfe.py, FEHLER_KATALOG, bleibt in der Hauptdatei – Hilfe geht auch ohne Zusatzdaten); der Simulator liest sie aus res:// (scripts/fehler_hilfe.gd, export_presets.cfg). Neue Fehler: zuerst hier, dann bauen.",
 "_felder": {
  "pfad": "Adresse der Hilfeseite in MoveEye: <MoveEye>/hilfe/fehler/<id>. Der QR-Code enthält nur diese Adresse (keine Passwörter, keine Schlüssel).",
  "fehler": "seite: mw | sim | beide. stufe: bad | warn. quelle.health: IDs der Selbstdiagnose von MoveEye (120 health_check), quelle.sim_diag: IDs der Selbstdiagnose des Simulators (diagnose.gd), quelle.meldung: englische Teile von Meldungen (Push, Bild «NO CAMERA FOUND»), quelle.wenn: Zusatzbedingung in MoveEye (639u). aktion: Schlüssel aus «aktionen». bau: Reiter der Seite «Bauen» mit der passenden Anleitung (real-bauen).",
  "aktionen": "Was «Jetzt beheben» tut. MoveEye-Aktionen laufen nur als POST des Besitzers (angemeldet, CSRF-Schlüssel); sim_* laufen im Simulator selbst (Knopf im Simulator) oder über /control von MoveEye.",
  "ui": "Texte der Hilfeseite, der Knöpfe und des Fensters im Simulator."
 },
 "pfad": "/hilfe/fehler/",
 "sprachen": [
  "de",
  "en",
  "fr",
  "it",
  "rm"
 ],
 "ui": {
  "error": {
   "de": "Fehler",
   "en": "Error",
   "fr": "Erreur",
   "it": "Errore",
   "rm": "Errur"
  },
  "what": {
   "de": "Was ist los?",
   "en": "What is wrong?",
   "fr": "Que se passe-t-il ?",
   "it": "Che cosa succede?",
   "rm": "Tge è capità?"
  },
  "steps": {
   "de": "So behebst du es",
   "en": "How to fix it",
   "fr": "Comment corriger",
   "it": "Come risolvere",
   "rm": "Uschia sligias ti il problem"
  },
  "fix": {
   "de": "Beheben",
   "en": "Fix",
   "fr": "Corriger",
   "it": "Risolvi",
   "rm": "Reparar"
  },
  "fix_now": {
   "de": "Jetzt beheben",
   "en": "Fix now",
   "fr": "Corriger maintenant",
   "it": "Risolvi ora",
   "rm": "Reparar ussa"
  },
  "help": {
   "de": "Hilfe",
   "en": "Help",
   "fr": "Aide",
   "it": "Aiuto",
   "rm": "Agid"
  },
  "owner": {
   "de": "Nur der Besitzer kann das beheben – bitte anmelden.",
   "en": "Only the owner can fix this – please log in.",
   "fr": "Seul le propriétaire peut corriger – veuillez vous connecter.",
   "it": "Solo il proprietario può risolvere – accedi.",
   "rm": "Mo il possessur po reparar quai – s'annunzia per plaschair."
  },
  "pw_first": {
   "de": "Zuerst ein Passwort setzen (Einstellungen → Sicherheit) – sonst könnte jeder im Netz das auslösen.",
   "en": "Set a password first (Settings → Security) – otherwise anybody in the network could do this.",
   "fr": "Définissez d'abord un mot de passe (Réglages → Sécurité) – sinon n'importe qui sur le réseau pourrait le faire.",
   "it": "Imposta prima una password (Impostazioni → Sicurezza) – altrimenti chiunque nella rete potrebbe farlo.",
   "rm": "Fixescha l'emprim in pled-clav (Parameters → Segirezza) – uschiglio pudess mintgin en la rait far quai."
  },
  "done": {
   "de": "Erledigt",
   "en": "Done",
   "fr": "Fait",
   "it": "Fatto",
   "rm": "Fatg"
  },
  "failed": {
   "de": "Hat nicht geklappt",
   "en": "Did not work",
   "fr": "N'a pas fonctionné",
   "it": "Non ha funzionato",
   "rm": "N'ha betg funcziunà"
  },
  "manual": {
   "de": "Dafür gibt es keine automatische Lösung – folge den Schritten oben.",
   "en": "There is no automatic fix for this – follow the steps above.",
   "fr": "Il n'y a pas de correction automatique – suivez les étapes ci-dessus.",
   "it": "Non c'è una soluzione automatica – segui i passi qui sopra.",
   "rm": "Per quai na datti nagina soluziun automatica – suonda ils pass survart."
  },
  "scan": {
   "de": "Mit dem Handy scannen: Hilfe und «Beheben» dort",
   "en": "Scan with the phone: help and «Fix» there",
   "fr": "Scanner avec le téléphone : aide et « Corriger »",
   "it": "Scansiona con il telefono: aiuto e «Risolvi»",
   "rm": "Scannar cun il telefonin: agid e «Reparar» là"
  },
  "back": {
   "de": "Zurück zu MoveEye",
   "en": "Back to MoveEye",
   "fr": "Retour à MoveEye",
   "it": "Torna a MoveEye",
   "rm": "Enavos tar MoveEye"
  },
  "unknown": {
   "de": "Unbekannte Fehler-Kennung",
   "en": "Unknown error code",
   "fr": "Code d'erreur inconnu",
   "it": "Codice di errore sconosciuto",
   "rm": "Code d'errur nunenconuschent"
  },
  "code": {
   "de": "Kennung",
   "en": "Code",
   "fr": "Code",
   "it": "Codice",
   "rm": "Code"
  },
  "all": {
   "de": "Alle Fehler",
   "en": "All errors",
   "fr": "Toutes les erreurs",
   "it": "Tutti gli errori",
   "rm": "Tut las errurs"
  },
  "active": {
   "de": "Jetzt aktiv",
   "en": "Active now",
   "fr": "Actif maintenant",
   "it": "Attivo ora",
   "rm": "Activ ussa"
  },
  "offline": {
   "de": "Keine Verbindung zu MoveEye – die Anleitung kommt aus dem Simulator (ohne QR-Code).",
   "en": "No connection to MoveEye – the steps come from the simulator (no QR code).",
   "fr": "Pas de connexion à MoveEye – les étapes viennent du simulateur (sans code QR).",
   "it": "Nessuna connessione a MoveEye – i passi vengono dal simulatore (senza codice QR).",
   "rm": "Nagina colliaziun cun MoveEye – ils pass vegnan dal simulatur (senza code QR)."
  },
  "close": {
   "de": "Schliessen",
   "en": "Close",
   "fr": "Fermer",
   "it": "Chiudi",
   "rm": "Serrar"
  },
  "busy": {
   "de": "Läuft …",
   "en": "Running …",
   "fr": "En cours …",
   "it": "In corso …",
   "rm": "En lavur …"
  }
 },
 "aktionen": {
  "kamera_neu": {
   "de": "Kamera neu verbinden",
   "en": "Reconnect the camera",
   "fr": "Reconnecter la caméra",
   "it": "Ricollega la telecamera",
   "rm": "Colliar danovamain la camera"
  },
  "dienst_neu": {
   "de": "MoveEye neu starten (Selbstheilung)",
   "en": "Restart MoveEye (self-healing)",
   "fr": "Redémarrer MoveEye (auto-réparation)",
   "it": "Riavvia MoveEye (autoriparazione)",
   "rm": "Reaviar MoveEye (autoguariziun)"
  },
  "ki_laden": {
   "de": "KI-Modell herunterladen",
   "en": "Download the AI model",
   "fr": "Télécharger le modèle IA",
   "it": "Scarica il modello IA",
   "rm": "Telechargiar il model IA"
  },
  "speicher": {
   "de": "Speicher aufräumen",
   "en": "Free up storage",
   "fr": "Libérer de l'espace",
   "it": "Libera spazio",
   "rm": "Far plazza en la memoria"
  },
  "update": {
   "de": "Update erneut versuchen",
   "en": "Try the update again",
   "fr": "Réessayer la mise à jour",
   "it": "Riprova l'aggiornamento",
   "rm": "Empruvar danovamain l'actualisaziun"
  },
  "zusatzdaten": {
   "de": "Zusatzdaten neu holen",
   "en": "Fetch the data file again",
   "fr": "Récupérer à nouveau les données",
   "it": "Scarica di nuovo i dati",
   "rm": "Prender danovamain las datas supplementaras"
  },
  "wlan": {
   "de": "WLAN suchen und neu verbinden",
   "en": "Search Wi-Fi and reconnect",
   "fr": "Chercher le Wi-Fi et reconnecter",
   "it": "Cerca il Wi-Fi e ricollega",
   "rm": "Tschertgar WLAN e colliar danovamain"
  },
  "push_test": {
   "de": "Testnachricht senden",
   "en": "Send a test message",
   "fr": "Envoyer un message test",
   "it": "Invia un messaggio di prova",
   "rm": "Trametter in messadi da test"
  },
  "sim_verbinden": {
   "de": "Simulator neu verbinden",
   "en": "Reconnect the simulator",
   "fr": "Reconnecter le simulateur",
   "it": "Ricollega il simulatore",
   "rm": "Colliar danovamain il simulatur"
  },
  "sim_neustart": {
   "de": "Simulator neu starten",
   "en": "Restart the simulator",
   "fr": "Redémarrer le simulateur",
   "it": "Riavvia il simulatore",
   "rm": "Reaviar il simulatur"
  },
  "sim_notfall": {
   "de": "Notfall-Start (Grafik Lite)",
   "en": "Emergency start (graphics Lite)",
   "fr": "Démarrage d'urgence (graphisme Lite)",
   "it": "Avvio d'emergenza (grafica Lite)",
   "rm": "Start d'urgenza (grafica Lite)"
  }
 },
 "fehler": [
  {
   "id": "CAM_NONE",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "cam"
    ],
    "meldung": [
     "NO CAMERA FOUND",
     "Camera lost"
    ]
   },
   "titel": {
    "de": "Kein Kamerabild",
    "en": "No camera picture",
    "fr": "Pas d'image de la caméra",
    "it": "Nessuna immagine della telecamera",
    "rm": "Nagin maletg da la camera"
   },
   "text": {
    "de": "MoveEye bekommt von der Kamera keine Bilder – es wird nichts überwacht.",
    "en": "MoveEye gets no pictures from the camera – nothing is being watched.",
    "fr": "MoveEye ne reçoit aucune image de la caméra – rien n'est surveillé.",
    "it": "MoveEye non riceve immagini dalla telecamera – niente è sorvegliato.",
    "rm": "MoveEye na survegn nagins maletgs da la camera – nagut na vegn surveglià."
   },
   "schritte": {
    "de": [
     "Auf «Kamera neu verbinden» tippen.",
     "Kabel der Kamera prüfen (Flachbandkabel richtig herum, fest eingesteckt).",
     "Unter Einstellungen → Videoquelle die richtige Kamera wählen.",
     "Hilft nichts: den Pi neu starten."
    ],
    "en": [
     "Tap «Reconnect the camera».",
     "Check the camera cable (ribbon the right way round, firmly in).",
     "Choose the right camera under Settings → Video source.",
     "Nothing helps: restart the Pi."
    ],
    "fr": [
     "Touchez « Reconnecter la caméra ».",
     "Vérifiez le câble (nappe dans le bon sens, bien enfoncée).",
     "Choisissez la bonne caméra dans Réglages → Source vidéo.",
     "Rien n'y fait : redémarrez le Pi."
    ],
    "it": [
     "Tocca «Ricollega la telecamera».",
     "Controlla il cavo (piatto nel verso giusto, ben inserito).",
     "Scegli la telecamera giusta in Impostazioni → Sorgente video.",
     "Non serve: riavvia il Pi."
    ],
    "rm": [
     "Smatga «Colliar danovamain la camera».",
     "Controllescha il cabel (cabel plat en la dretga direcziun, bain enfilà).",
     "Tscherna la dretga camera sut Parameters → Funtauna video.",
     "Na gida nagut: reaviar il Pi."
    ]
   },
   "aktion": "kamera_neu"
  },
  {
   "id": "CAM_LOOP",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "loop"
    ],
    "meldung": [
     "Camera loop disturbed"
    ]
   },
   "titel": {
    "de": "Erkennung gestört",
    "en": "Detection disturbed",
    "fr": "Détection perturbée",
    "it": "Rilevamento disturbato",
    "rm": "Identificaziun disturbada"
   },
   "text": {
    "de": "Die Erkennungs-Schleife hängt oder startet immer wieder neu.",
    "en": "The detection loop hangs or keeps restarting.",
    "fr": "La boucle de détection est bloquée ou redémarre sans cesse.",
    "it": "Il ciclo di rilevamento è bloccato o si riavvia di continuo.",
    "rm": "La sleppa d'identificaziun è bloccada u reaviescha adina puspè."
   },
   "schritte": {
    "de": [
     "Auf «MoveEye neu starten» tippen (die Selbstheilung startet MoveEye sauber neu).",
     "Kommt es wieder: Diagnose-Paket schicken (Mehr → Hilfe)."
    ],
    "en": [
     "Tap «Restart MoveEye» (self-healing restarts it cleanly).",
     "If it comes back: send the diagnosis package (More → Help)."
    ],
    "fr": [
     "Touchez « Redémarrer MoveEye » (l'auto-réparation redémarre proprement).",
     "Si cela revient : envoyez le paquet de diagnostic (Plus → Aide)."
    ],
    "it": [
     "Tocca «Riavvia MoveEye» (l'autoriparazione riavvia in modo pulito).",
     "Se si ripete: invia il pacchetto di diagnosi (Altro → Aiuto)."
    ],
    "rm": [
     "Smatga «Reaviar MoveEye» (l'autoguariziun reaviescha MoveEye en urden).",
     "Sch'i turna: trametter il pachet da diagnosa (Dapli → Agid)."
    ]
   },
   "aktion": "dienst_neu"
  },
  {
   "id": "AI_MODEL",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "ai"
    ]
   },
   "titel": {
    "de": "KI-Modell fehlt",
    "en": "AI model missing",
    "fr": "Modèle IA manquant",
    "it": "Modello IA mancante",
    "rm": "Il model IA manca"
   },
   "text": {
    "de": "Die Personen-Erkennung (KI) kann nicht laufen, weil das Modell fehlt oder der Download fehlschlug.",
    "en": "Person detection (AI) cannot run because the model is missing or the download failed.",
    "fr": "La détection de personnes (IA) ne peut pas fonctionner : le modèle manque ou le téléchargement a échoué.",
    "it": "Il rilevamento persone (IA) non può funzionare: il modello manca o il download è fallito.",
    "rm": "L'identificaziun da persunas (IA) na po betg funcziunar: il model manca u il telechargiament n'ha betg funcziunà."
   },
   "schritte": {
    "de": [
     "Internet prüfen (ca. 70 MB werden geladen).",
     "Auf «KI-Modell herunterladen» tippen und warten."
    ],
    "en": [
     "Check the internet (about 70 MB are downloaded).",
     "Tap «Download the AI model» and wait."
    ],
    "fr": [
     "Vérifiez Internet (environ 70 Mo).",
     "Touchez « Télécharger le modèle IA » et patientez."
    ],
    "it": [
     "Controlla Internet (circa 70 MB).",
     "Tocca «Scarica il modello IA» e attendi."
    ],
    "rm": [
     "Controllar l'internet (var 70 MB vegnan telechargiads).",
     "Smatga «Telechargiar il model IA» e spetga."
    ]
   },
   "aktion": "ki_laden"
  },
  {
   "id": "SERVO_NONE",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "servo"
    ]
   },
   "titel": {
    "de": "Servos nicht gefunden",
    "en": "Servos not found",
    "fr": "Servos introuvables",
    "it": "Servo non trovati",
    "rm": "Servos betg chattads"
   },
   "text": {
    "de": "Der Schwenk-/Neigekopf antwortet nicht – die Kamera bewegt sich nicht.",
    "en": "The pan/tilt head does not answer – the camera does not move.",
    "fr": "La tête panoramique ne répond pas – la caméra ne bouge pas.",
    "it": "La testa pan/tilt non risponde – la telecamera non si muove.",
    "rm": "Il chau da girar/stortar na respunda betg – la camera na sa mova betg."
   },
   "schritte": {
    "de": [
     "Strom und Kabel der Servos prüfen (PCA9685, Adresse 0x41).",
     "I2C einschalten: sudo raspi-config → Interface → I2C.",
     "Danach MoveEye neu starten."
    ],
    "en": [
     "Check power and wiring of the servos (PCA9685, address 0x41).",
     "Switch on I2C: sudo raspi-config → Interface → I2C.",
     "Then restart MoveEye."
    ],
    "fr": [
     "Vérifiez l'alimentation et le câblage des servos (PCA9685, adresse 0x41).",
     "Activez I2C : sudo raspi-config → Interface → I2C.",
     "Puis redémarrez MoveEye."
    ],
    "it": [
     "Controlla alimentazione e cavi dei servo (PCA9685, indirizzo 0x41).",
     "Attiva I2C: sudo raspi-config → Interface → I2C.",
     "Poi riavvia MoveEye."
    ],
    "rm": [
     "Controllar current e cablaschi dals servos (PCA9685, adressa 0x41).",
     "Activar I2C: sudo raspi-config → Interface → I2C.",
     "Lura reaviar MoveEye."
    ]
   }
  },
  {
   "id": "THERMAL",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "thermal"
    ]
   },
   "titel": {
    "de": "Wärmebild-Kamera stört",
    "en": "Thermal camera problem",
    "fr": "Problème de caméra thermique",
    "it": "Problema termocamera",
    "rm": "Problem cun la camera termica"
   },
   "text": {
    "de": "Die Wärmebild-Kamera liefert keine Werte.",
    "en": "The thermal camera delivers no values.",
    "fr": "La caméra thermique ne fournit aucune valeur.",
    "it": "La termocamera non fornisce valori.",
    "rm": "La camera termica na furnescha nagina valur."
   },
   "schritte": {
    "de": [
     "Kabel und Stecker der Wärmebild-Kamera prüfen.",
     "SPI und I2C eingeschaltet? (raspi-config)",
     "MoveEye neu starten."
    ],
    "en": [
     "Check cable and plug of the thermal camera.",
     "SPI and I2C switched on? (raspi-config)",
     "Restart MoveEye."
    ],
    "fr": [
     "Vérifiez câble et connecteur de la caméra thermique.",
     "SPI et I2C activés ? (raspi-config)",
     "Redémarrez MoveEye."
    ],
    "it": [
     "Controlla cavo e connettore della termocamera.",
     "SPI e I2C attivi? (raspi-config)",
     "Riavvia MoveEye."
    ],
    "rm": [
     "Controllar cabel e plug da la camera termica.",
     "SPI ed I2C activads? (raspi-config)",
     "Reaviar MoveEye."
    ]
   },
   "aktion": "dienst_neu"
  },
  {
   "id": "MIC",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "mic"
    ]
   },
   "titel": {
    "de": "Mikrofon stört",
    "en": "Microphone problem",
    "fr": "Problème de micro",
    "it": "Problema microfono",
    "rm": "Problem cun il microfon"
   },
   "text": {
    "de": "Das Mikrofon hört nichts oder meldet einen Fehler.",
    "en": "The microphone hears nothing or reports an error.",
    "fr": "Le micro n'entend rien ou signale une erreur.",
    "it": "Il microfono non sente nulla o segnala un errore.",
    "rm": "Il microfon na auda nagut u annunzia ina errur."
   },
   "schritte": {
    "de": [
     "USB-Mikrofon aus- und wieder einstecken.",
     "Einstellungen → Mikrofon → «Geräte suchen» und neu wählen."
    ],
    "en": [
     "Unplug the USB microphone and plug it in again.",
     "Settings → Microphone → «Search devices» and choose again."
    ],
    "fr": [
     "Débranchez puis rebranchez le micro USB.",
     "Réglages → Micro → « Chercher les appareils » et rechoisir."
    ],
    "it": [
     "Scollega e ricollega il microfono USB.",
     "Impostazioni → Microfono → «Cerca dispositivi» e riscegli."
    ],
    "rm": [
     "Trair or e tschentar puspè en il microfon USB.",
     "Parameters → Microfon → «Tschertgar apparats» e tscherner danovamain."
    ]
   }
  },
  {
   "id": "NET_OFFLINE",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "net"
    ]
   },
   "titel": {
    "de": "Kein Internet",
    "en": "No internet",
    "fr": "Pas d'Internet",
    "it": "Nessuna connessione Internet",
    "rm": "Nagin internet"
   },
   "text": {
    "de": "MoveEye ist offline. Alarme warten im Postausgang und gehen raus, sobald das Netz wieder da ist.",
    "en": "MoveEye is offline. Alarms wait in the outbox and go out as soon as the network is back.",
    "fr": "MoveEye est hors ligne. Les alarmes attendent et partent dès que le réseau revient.",
    "it": "MoveEye è offline. Gli allarmi attendono e partono appena torna la rete.",
    "rm": "MoveEye è offline. Ils alarms spetgan e partan uschespert che la rait è puspè avant maun."
   },
   "schritte": {
    "de": [
     "Handy-Hotspot bzw. WLAN-Router eingeschaltet?",
     "Auf «WLAN suchen und neu verbinden» tippen.",
     "Sonst: Einstellungen → Netzwerk → anderes WLAN wählen."
    ],
    "en": [
     "Phone hotspot or Wi-Fi router switched on?",
     "Tap «Search Wi-Fi and reconnect».",
     "Otherwise: Settings → Network → choose another Wi-Fi."
    ],
    "fr": [
     "Point d'accès du téléphone ou routeur allumé ?",
     "Touchez « Chercher le Wi-Fi et reconnecter ».",
     "Sinon : Réglages → Réseau → choisir un autre Wi-Fi."
    ],
    "it": [
     "Hotspot del telefono o router acceso?",
     "Tocca «Cerca il Wi-Fi e ricollega».",
     "Altrimenti: Impostazioni → Rete → scegli un altro Wi-Fi."
    ],
    "rm": [
     "Hotspot dal telefonin u router WLAN activà?",
     "Smatga «Tschertgar WLAN e colliar danovamain».",
     "Uschiglio: Parameters → Rait → tscherner in auter WLAN."
    ]
   },
   "aktion": "wlan"
  },
  {
   "id": "PUSH_NONE",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "push"
    ],
    "wenn": "push_fehlt"
   },
   "titel": {
    "de": "Push-Meldungen nicht eingerichtet",
    "en": "Push messages not set up",
    "fr": "Notifications non configurées",
    "it": "Notifiche non configurate",
    "rm": "Messadis push betg installads"
   },
   "text": {
    "de": "Bei einem Alarm bekommst du keine Nachricht aufs Handy.",
    "en": "On an alarm you get no message on the phone.",
    "fr": "En cas d'alarme, vous ne recevez aucun message.",
    "it": "In caso di allarme non ricevi alcun messaggio.",
    "rm": "Tar in alarm na survegns ti nagin messadi."
   },
   "schritte": {
    "de": [
     "App «ntfy» aufs Handy laden.",
     "Einstellungen → Benachrichtigungen: ntfy einrichten (QR-Code scannen).",
     "«Test» senden."
    ],
    "en": [
     "Install the app «ntfy» on the phone.",
     "Settings → Notifications: set up ntfy (scan the QR code).",
     "Send «Test»."
    ],
    "fr": [
     "Installez l'application « ntfy ».",
     "Réglages → Notifications : configurer ntfy (scanner le code QR).",
     "Envoyer « Test »."
    ],
    "it": [
     "Installa l'app «ntfy».",
     "Impostazioni → Notifiche: configura ntfy (scansiona il QR).",
     "Invia «Test»."
    ],
    "rm": [
     "Installar l'app «ntfy» sin il telefonin.",
     "Parameters → Avis: installar ntfy (scannar il code QR).",
     "Trametter «Test»."
    ]
   }
  },
  {
   "id": "PUSH_ERROR",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "push"
    ],
    "wenn": "push_fehler"
   },
   "titel": {
    "de": "Push-Meldung fehlgeschlagen",
    "en": "Push message failed",
    "fr": "Échec de la notification",
    "it": "Notifica non riuscita",
    "rm": "Il messadi push n'è betg reussì"
   },
   "text": {
    "de": "Die letzte Nachricht kam nicht an. Alarme warten im Postausgang.",
    "en": "The last message did not arrive. Alarms wait in the outbox.",
    "fr": "Le dernier message n'est pas arrivé. Les alarmes attendent.",
    "it": "L'ultimo messaggio non è arrivato. Gli allarmi attendono.",
    "rm": "L'ultim messadi n'è betg arrivà. Ils alarms spetgan."
   },
   "schritte": {
    "de": [
     "Internet prüfen.",
     "Auf «Testnachricht senden» tippen.",
     "Kommt nichts: Adresse / Thema unter Einstellungen → Benachrichtigungen prüfen."
    ],
    "en": [
     "Check the internet.",
     "Tap «Send a test message».",
     "Nothing comes: check address / topic under Settings → Notifications."
    ],
    "fr": [
     "Vérifiez Internet.",
     "Touchez « Envoyer un message test ».",
     "Rien n'arrive : vérifiez l'adresse / le sujet dans Réglages → Notifications."
    ],
    "it": [
     "Controlla Internet.",
     "Tocca «Invia un messaggio di prova».",
     "Non arriva nulla: controlla indirizzo / argomento in Impostazioni → Notifiche."
    ],
    "rm": [
     "Controllar l'internet.",
     "Smatga «Trametter in messadi da test».",
     "Na vegn nagut: controllar l'adressa / il tema sut Parameters → Avis."
    ]
   },
   "aktion": "push_test"
  },
  {
   "id": "DISK_LOW",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "disk"
    ]
   },
   "titel": {
    "de": "Speicher fast voll",
    "en": "Storage almost full",
    "fr": "Stockage presque plein",
    "it": "Memoria quasi piena",
    "rm": "Memoria bunamain plaina"
   },
   "text": {
    "de": "Auf der Speicherkarte ist wenig Platz – bald können keine Aufnahmen mehr gespeichert werden.",
    "en": "There is little room on the memory card – soon no recordings can be saved.",
    "fr": "Il reste peu de place sur la carte – bientôt plus d'enregistrements possibles.",
    "it": "C'è poco spazio sulla scheda – presto non si potranno più salvare registrazioni.",
    "rm": "I dat pauca plazza sin la carta da memoria – bainprest na pon nagins registraziuns pli vegnir memorisadas."
   },
   "schritte": {
    "de": [
     "Auf «Speicher aufräumen» tippen (löscht die ältesten Aufnahmen, Favoriten bleiben).",
     "«Max. Grösse der Aufnahmen» kleiner stellen (Einstellungen → Aufnahme).",
     "Besser: SSD oder USB-Stick für die Aufnahmen."
    ],
    "en": [
     "Tap «Free up storage» (deletes the oldest recordings, favourites stay).",
     "Lower «max. size of the recordings» (Settings → Recording).",
     "Better: an SSD or USB drive for the recordings."
    ],
    "fr": [
     "Touchez « Libérer de l'espace » (supprime les plus anciens, les favoris restent).",
     "Réduisez « taille max. des enregistrements » (Réglages → Enregistrement).",
     "Mieux : un SSD ou une clé USB."
    ],
    "it": [
     "Tocca «Libera spazio» (cancella le registrazioni più vecchie, i preferiti restano).",
     "Riduci «dimensione max. registrazioni» (Impostazioni → Registrazione).",
     "Meglio: un SSD o una chiavetta USB."
    ],
    "rm": [
     "Smatga «Far plazza» (stizza las registraziuns las pli veglias, ils favurits restan).",
     "Reducir «grondezza max. da las registraziuns» (Parameters → Registraziun).",
     "Meglier: in SSD u in stick USB."
    ]
   },
   "aktion": "speicher"
  },
  {
   "id": "SDCARD",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "sdwear"
    ]
   },
   "titel": {
    "de": "Speicherkarte meldet Fehler",
    "en": "Memory card reports errors",
    "fr": "La carte mémoire signale des erreurs",
    "it": "La scheda di memoria segnala errori",
    "rm": "La carta da memoria annunzia errurs"
   },
   "text": {
    "de": "Das Dateisystem hat Fehler oder ist schreibgeschützt geworden.",
    "en": "The file system has errors or became read-only.",
    "fr": "Le système de fichiers a des erreurs ou est passé en lecture seule.",
    "it": "Il file system ha errori o è diventato di sola lettura.",
    "rm": "Il sistem da datotecas ha errurs u è daventà mo legibel."
   },
   "schritte": {
    "de": [
     "Sicherung machen (Einstellungen → Sicherung).",
     "Pi sauber herunterfahren, Karte am PC prüfen oder ersetzen."
    ],
    "en": [
     "Make a backup (Settings → Backup).",
     "Shut the Pi down cleanly, check or replace the card on a PC."
    ],
    "fr": [
     "Faites une sauvegarde (Réglages → Sauvegarde).",
     "Arrêtez proprement le Pi, vérifiez ou remplacez la carte."
    ],
    "it": [
     "Fai un backup (Impostazioni → Backup).",
     "Spegni il Pi correttamente, controlla o sostituisci la scheda."
    ],
    "rm": [
     "Far ina copia da segirezza (Parameters → Segirezza).",
     "Stizzar il Pi en urden, controllar u remplazzar la carta."
    ]
   }
  },
  {
   "id": "CPU_HOT",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "temp"
    ]
   },
   "titel": {
    "de": "Pi zu heiss",
    "en": "Pi too hot",
    "fr": "Pi trop chaud",
    "it": "Pi troppo caldo",
    "rm": "Pi memia chaud"
   },
   "text": {
    "de": "Der Prozessor ist über 70 °C – er wird langsamer und kann abstürzen.",
    "en": "The processor is above 70 °C – it slows down and may crash.",
    "fr": "Le processeur dépasse 70 °C – il ralentit et peut planter.",
    "it": "Il processore supera i 70 °C – rallenta e può bloccarsi.",
    "rm": "Il processer è sur 70 °C – el daventa plaun e po crudar."
   },
   "schritte": {
    "de": [
     "Gehäuse in den Schatten stellen.",
     "Kühlkörper / Lüfter prüfen.",
     "Nachtsicht oder Wärmebild vorübergehend ausschalten."
    ],
    "en": [
     "Put the housing in the shade.",
     "Check heat sink / fan.",
     "Switch night vision or thermal off for a while."
    ],
    "fr": [
     "Mettez le boîtier à l'ombre.",
     "Vérifiez dissipateur / ventilateur.",
     "Désactivez un moment la vision nocturne ou thermique."
    ],
    "it": [
     "Metti l'involucro all'ombra.",
     "Controlla dissipatore / ventola.",
     "Spegni per un po' la visione notturna o termica."
    ],
    "rm": [
     "Metter la chaschetta en la sumbriva.",
     "Controllar refrigerader / ventilatur.",
     "Deactivar ina giada la vista da notg u la camera termica."
    ]
   }
  },
  {
   "id": "POWER_LOW",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "power"
    ]
   },
   "titel": {
    "de": "Unterspannung",
    "en": "Under-voltage",
    "fr": "Sous-tension",
    "it": "Sottotensione",
    "rm": "Tensiun memia bassa"
   },
   "text": {
    "de": "Das Netzteil liefert zu wenig Strom – der Pi kann abstürzen und die Karte beschädigen.",
    "en": "The power supply delivers too little – the Pi may crash and damage the card.",
    "fr": "L'alimentation est trop faible – le Pi peut planter et abîmer la carte.",
    "it": "L'alimentatore è troppo debole – il Pi può bloccarsi e danneggiare la scheda.",
    "rm": "L'alimentaziun furnescha memia pauc – il Pi po crudar e donnegiar la carta."
   },
   "schritte": {
    "de": [
     "Netzteil / Powerbank mit 5 V / 5 A verwenden.",
     "Kurzes, dickes USB-C-Kabel nehmen."
    ],
    "en": [
     "Use a 5 V / 5 A power supply / powerbank.",
     "Use a short, thick USB-C cable."
    ],
    "fr": [
     "Utilisez une alimentation 5 V / 5 A.",
     "Prenez un câble USB-C court et épais."
    ],
    "it": [
     "Usa un alimentatore 5 V / 5 A.",
     "Usa un cavo USB-C corto e spesso."
    ],
    "rm": [
     "Duvrar ina alimentaziun 5 V / 5 A.",
     "Duvrar in curt e gross cabel USB-C."
    ]
   }
  },
  {
   "id": "BATT_LOW",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "batt"
    ]
   },
   "titel": {
    "de": "Akku schwach",
    "en": "Battery low",
    "fr": "Batterie faible",
    "it": "Batteria scarica",
    "rm": "Accu flaivel"
   },
   "text": {
    "de": "Der Akku reicht vielleicht nicht bis zum Morgen.",
    "en": "The battery may not last until the morning.",
    "fr": "La batterie risque de ne pas tenir jusqu'au matin.",
    "it": "La batteria potrebbe non durare fino al mattino.",
    "rm": "L'accu na tanscha forsa betg fin la damaun."
   },
   "schritte": {
    "de": [
     "Powerbank bald laden oder tauschen.",
     "Akku sparen einschalten (Einstellungen → Akku)."
    ],
    "en": [
     "Charge or swap the powerbank soon.",
     "Switch on battery saving (Settings → Battery)."
    ],
    "fr": [
     "Rechargez ou changez bientôt la batterie.",
     "Activez l'économie (Réglages → Batterie)."
    ],
    "it": [
     "Ricarica o sostituisci presto la powerbank.",
     "Attiva il risparmio (Impostazioni → Batteria)."
    ],
    "rm": [
     "Chargiar u barattar bainprest la powerbank.",
     "Activar spargnar accu (Parameters → Accu)."
    ]
   }
  },
  {
   "id": "CLOCK",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "clock"
    ]
   },
   "titel": {
    "de": "Uhrzeit unbekannt",
    "en": "Time unknown",
    "fr": "Heure inconnue",
    "it": "Ora sconosciuta",
    "rm": "Ura nunenconuschenta"
   },
   "text": {
    "de": "Der Pi kennt die Uhrzeit nicht – Zeitpläne und Aufnahmen haben falsche Zeiten.",
    "en": "The Pi does not know the time – schedules and recordings get wrong times.",
    "fr": "Le Pi ne connaît pas l'heure – horaires et enregistrements sont faux.",
    "it": "Il Pi non conosce l'ora – orari e registrazioni sono sbagliati.",
    "rm": "Il Pi na enconuscha betg l'ura – ils plans e las registraziuns han uras faussas."
   },
   "schritte": {
    "de": [
     "Die MoveEye-Seite einmal auf dem Handy öffnen – der Pi übernimmt die Zeit.",
     "Oder Internet verbinden."
    ],
    "en": [
     "Open the MoveEye page on the phone once – the Pi takes the time from it.",
     "Or connect to the internet."
    ],
    "fr": [
     "Ouvrez une fois la page MoveEye sur le téléphone – le Pi reprend l'heure.",
     "Ou connectez Internet."
    ],
    "it": [
     "Apri una volta la pagina MoveEye sul telefono – il Pi prende l'ora.",
     "Oppure collega Internet."
    ],
    "rm": [
     "Avrir ina giada la pagina MoveEye sin il telefonin – il Pi prenda l'ura.",
     "U colliar l'internet."
    ]
   }
  },
  {
   "id": "PW_NONE",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "pw"
    ]
   },
   "titel": {
    "de": "Kein Passwort",
    "en": "No password",
    "fr": "Pas de mot de passe",
    "it": "Nessuna password",
    "rm": "Nagin pled-clav"
   },
   "text": {
    "de": "Ohne Passwort kann jeder im selben Netz alles sehen und steuern.",
    "en": "Without a password everyone in the same network can watch and control everything.",
    "fr": "Sans mot de passe, tout le monde sur le réseau peut tout voir et commander.",
    "it": "Senza password chiunque nella rete può vedere e comandare tutto.",
    "rm": "Senza pled-clav po mintgin en la medema rait vesair e controllar tut."
   },
   "schritte": {
    "de": [
     "Einstellungen → Sicherheit → Passwort setzen.",
     "Danach neu anmelden."
    ],
    "en": [
     "Settings → Security → set a password.",
     "Then log in again."
    ],
    "fr": [
     "Réglages → Sécurité → définir un mot de passe.",
     "Puis reconnectez-vous."
    ],
    "it": [
     "Impostazioni → Sicurezza → imposta una password.",
     "Poi accedi di nuovo."
    ],
    "rm": [
     "Parameters → Segirezza → fixar in pled-clav.",
     "Lura s'annunziar danovamain."
    ]
   }
  },
  {
   "id": "LASTRUN_CRASH",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "lastrun"
    ],
    "meldung": [
     "ended unexpectedly"
    ]
   },
   "titel": {
    "de": "Absturz beim letzten Lauf",
    "en": "Crash in the last run",
    "fr": "Plantage lors de la dernière exécution",
    "it": "Arresto anomalo nell'ultima esecuzione",
    "rm": "Crudada durant l'ultima giada"
   },
   "text": {
    "de": "MoveEye ist unerwartet beendet worden (Strom, Hitze oder zu schwaches Netzteil). Nach mehreren Abstürzen startet es im sicheren Modus.",
    "en": "MoveEye ended unexpectedly (power, heat or a weak power supply). After several crashes it starts in safe mode.",
    "fr": "MoveEye s'est arrêté de façon inattendue (courant, chaleur, alimentation faible). Après plusieurs plantages, il démarre en mode sûr.",
    "it": "MoveEye si è chiuso inaspettatamente (corrente, calore o alimentatore debole). Dopo più arresti parte in modalità sicura.",
    "rm": "MoveEye è vegnì terminà nunspetgadamain (current, chalur u alimentaziun flaivla). Suenter pliras crudadas startà el en il modus segir."
   },
   "schritte": {
    "de": [
     "Netzteil 5 V / 5 A und Kühlung prüfen.",
     "Im sicheren Modus: KI, Wärmebild, Nachtsicht einzeln wieder einschalten.",
     "Kommt es wieder: Diagnose-Paket schicken."
    ],
    "en": [
     "Check the 5 V / 5 A power supply and cooling.",
     "In safe mode: switch AI, thermal, night vision on again one by one.",
     "If it happens again: send the diagnosis package."
    ],
    "fr": [
     "Vérifiez l'alimentation 5 V / 5 A et le refroidissement.",
     "En mode sûr : réactivez IA, thermique, vision nocturne un par un.",
     "Si cela se reproduit : envoyez le diagnostic."
    ],
    "it": [
     "Controlla alimentatore 5 V / 5 A e raffreddamento.",
     "In modalità sicura: riattiva IA, termica, visione notturna uno alla volta.",
     "Se si ripete: invia il pacchetto di diagnosi."
    ],
    "rm": [
     "Controllar l'alimentaziun 5 V / 5 A e la refrigeraziun.",
     "En il modus segir: activar danovamain IA, termica, vista da notg ina suenter l'autra.",
     "Sch'i capita puspè: trametter il pachet da diagnosa."
    ]
   }
  },
  {
   "id": "SELFHEAL_HELD",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "selfheal"
    ],
    "meldung": [
     "MoveEye did not restart again (limit reached). Please look at it."
    ]
   },
   "titel": {
    "de": "Selbstheilung angehalten",
    "en": "Self-healing held back",
    "fr": "Auto-réparation suspendue",
    "it": "Autoriparazione sospesa",
    "rm": "Autoguariziun fermada"
   },
   "text": {
    "de": "Ein Teil hing mehrmals; MoveEye hat sich schon oft neu gestartet und wartet jetzt (Bremse).",
    "en": "A part hung several times; MoveEye already restarted often and now waits (brake).",
    "fr": "Une partie s'est bloquée plusieurs fois ; MoveEye a déjà souvent redémarré et attend (frein).",
    "it": "Una parte si è bloccata più volte; MoveEye si è già riavviato spesso e ora attende (freno).",
    "rm": "Ina part è sa bloccada pliras giadas; MoveEye è gia reaviada savens ed spetga ussa (fren)."
   },
   "schritte": {
    "de": [
     "Auf «MoveEye neu starten» tippen, wenn die Bremse es erlaubt.",
     "Protokoll ansehen (Mehr → Protokoll) und Diagnose-Paket schicken."
    ],
    "en": [
     "Tap «Restart MoveEye» when the brake allows it.",
     "Look at the log (More → Log) and send the diagnosis package."
    ],
    "fr": [
     "Touchez « Redémarrer MoveEye » si le frein le permet.",
     "Consultez le journal (Plus → Journal) et envoyez le diagnostic."
    ],
    "it": [
     "Tocca «Riavvia MoveEye» se il freno lo consente.",
     "Guarda il registro (Altro → Registro) e invia la diagnosi."
    ],
    "rm": [
     "Smatga «Reaviar MoveEye» sch'il fren lubescha quai.",
     "Guardar il protocol (Dapli → Protocol) e trametter il pachet da diagnosa."
    ]
   },
   "aktion": "dienst_neu"
  },
  {
   "id": "UPDATE_FAIL",
   "seite": "mw",
   "stufe": "warn",
   "quelle": {
    "health": [
     "update"
    ],
    "meldung": [
     "update failed",
     "download failed",
     "restart failed",
     "signature"
    ]
   },
   "titel": {
    "de": "Update fehlgeschlagen",
    "en": "Update failed",
    "fr": "Échec de la mise à jour",
    "it": "Aggiornamento non riuscito",
    "rm": "L'actualisaziun n'è betg reussida"
   },
   "text": {
    "de": "Die neue Version liess sich nicht laden oder installieren. Die bisherige Version läuft weiter.",
    "en": "The new version could not be downloaded or installed. The current version keeps running.",
    "fr": "La nouvelle version n'a pas pu être téléchargée ou installée. L'ancienne continue.",
    "it": "La nuova versione non è stata scaricata o installata. Quella attuale continua.",
    "rm": "La nova versiun n'ha betg pudì vegnir telechargiada u installada. La versiun actuala cuntinuescha."
   },
   "schritte": {
    "de": [
     "Internet prüfen.",
     "Auf «Update erneut versuchen» tippen.",
     "Meldet es «Signatur»: nur signierte Versionen installieren (Elektro signiert)."
    ],
    "en": [
     "Check the internet.",
     "Tap «Try the update again».",
     "If it says «signature»: only signed versions install (signed later)."
    ],
    "fr": [
     "Vérifiez Internet.",
     "Touchez « Réessayer la mise à jour ».",
     "Si « signature » : seules les versions signées s'installent."
    ],
    "it": [
     "Controlla Internet.",
     "Tocca «Riprova l'aggiornamento».",
     "Se dice «firma»: si installano solo versioni firmate."
    ],
    "rm": [
     "Controllar l'internet.",
     "Smatga «Empruvar danovamain l'actualisaziun».",
     "Sch'i stat «signatura»: mo versiuns signadas vegnan installadas."
    ]
   },
   "aktion": "update"
  },
  {
   "id": "DATA_MISSING",
   "seite": "mw",
   "stufe": "bad",
   "quelle": {
    "health": [
     "zusatz"
    ],
    "meldung": [
     "Additional data missing",
     "Zusatzdaten fehlen"
    ]
   },
   "titel": {
    "de": "Zusatzdaten fehlen",
    "en": "Data file missing",
    "fr": "Fichier de données manquant",
    "it": "File dati mancante",
    "rm": "Las datas supplementaras mancan"
   },
   "text": {
    "de": "Die Datei moveeye_daten_*.zip fehlt. MoveEye schützt weiter (Kern), aber Web-Seiten, Bilder und Übersetzungen fehlen.",
    "en": "The file moveeye_daten_*.zip is missing. MoveEye keeps protecting (core), but web pages, pictures and translations are missing.",
    "fr": "Le fichier moveeye_daten_*.zip manque. MoveEye protège toujours, mais pages, images et traductions manquent.",
    "it": "Manca il file moveeye_daten_*.zip. MoveEye protegge ancora, ma mancano pagine, immagini e traduzioni.",
    "rm": "La datoteca moveeye_daten_*.zip manca. MoveEye protegia vinavant, ma paginas, maletgs e translaziuns mancan."
   },
   "schritte": {
    "de": [
     "Auf «Zusatzdaten neu holen» tippen (braucht Internet).",
     "MoveEye startet danach einmal neu."
    ],
    "en": [
     "Tap «Fetch the data file again» (needs internet).",
     "MoveEye then restarts once."
    ],
    "fr": [
     "Touchez « Récupérer à nouveau les données » (Internet requis).",
     "MoveEye redémarre ensuite une fois."
    ],
    "it": [
     "Tocca «Scarica di nuovo i dati» (serve Internet).",
     "MoveEye poi si riavvia una volta."
    ],
    "rm": [
     "Smatga «Prender danovamain las datas» (basegna internet).",
     "MoveEye reaviescha lura ina giada."
    ]
   },
   "aktion": "zusatzdaten"
  },
  {
   "id": "SIM_UNREACHABLE",
   "seite": "beide",
   "stufe": "bad",
   "quelle": {
    "health": [
     "sim"
    ],
    "sim_diag": [
     "tunnel"
    ],
    "meldung": [
     "simulator not reachable"
    ]
   },
   "titel": {
    "de": "Simulator nicht erreichbar",
    "en": "Simulator not reachable",
    "fr": "Simulateur injoignable",
    "it": "Simulatore non raggiungibile",
    "rm": "Simulatur betg cuntanschibel"
   },
   "text": {
    "de": "Die Simulation ist eingeschaltet, aber vom Simulator kommen keine Bilder.",
    "en": "The simulation is on, but no pictures come from the simulator.",
    "fr": "La simulation est active, mais aucune image ne vient du simulateur.",
    "it": "La simulazione è attiva, ma dal simulatore non arrivano immagini.",
    "rm": "La simulaziun è activa, ma dal simulatur na vegnan nagins maletgs."
   },
   "schritte": {
    "de": [
     "Läuft der Simulator auf dem PC?",
     "Auf «Simulator neu verbinden» tippen.",
     "Hängt er: «Simulator neu starten» oder Notfall-Start."
    ],
    "en": [
     "Is the simulator running on the PC?",
     "Tap «Reconnect the simulator».",
     "If it hangs: «Restart the simulator» or emergency start."
    ],
    "fr": [
     "Le simulateur tourne-t-il sur le PC ?",
     "Touchez « Reconnecter le simulateur ».",
     "S'il est bloqué : « Redémarrer le simulateur » ou démarrage d'urgence."
    ],
    "it": [
     "Il simulatore è in esecuzione sul PC?",
     "Tocca «Ricollega il simulatore».",
     "Se è bloccato: «Riavvia il simulatore» o avvio d'emergenza."
    ],
    "rm": [
     "Gira il simulatur sin il PC?",
     "Smatga «Colliar danovamain il simulatur».",
     "Sch'el è bloccà: «Reaviar il simulatur» u start d'urgenza."
    ]
   },
   "aktion": "sim_verbinden"
  },
  {
   "id": "SIM_NO_MW",
   "seite": "sim",
   "stufe": "warn",
   "quelle": {
    "sim_diag": [
     "mw",
     "fw"
    ]
   },
   "titel": {
    "de": "MoveEye nicht verbunden",
    "en": "MoveEye not connected",
    "fr": "MoveEye non connecté",
    "it": "MoveEye non collegato",
    "rm": "MoveEye betg collià"
   },
   "text": {
    "de": "Der Simulator sendet, aber MoveEye holt keine Bilder ab.",
    "en": "The simulator is sending, but MoveEye does not fetch the pictures.",
    "fr": "Le simulateur envoie, mais MoveEye ne récupère pas les images.",
    "it": "Il simulatore invia, ma MoveEye non preleva le immagini.",
    "rm": "Il simulatur trametta, ma MoveEye na prenda betg ils maletgs."
   },
   "schritte": {
    "de": [
     "In MoveEye: Reiter Simulator → Verbindung: Adresse dieses PCs eintragen (gleiches Netz).",
     "Auf «Simulator neu verbinden» tippen (Senden aus und wieder ein).",
     "Firewall: den Simulator für private Netzwerke zulassen (TCP-Port 8765)."
    ],
    "en": [
     "In MoveEye: tab Simulator → Connection: enter the address of this PC (same network).",
     "Tap «Reconnect the simulator» (sending off and on again).",
     "Firewall: allow the simulator for private networks (TCP port 8765)."
    ],
    "fr": [
     "Dans MoveEye : onglet Simulateur → Connexion : saisir l'adresse de ce PC (même réseau).",
     "Touchez « Reconnecter le simulateur » (envoi arrêté puis relancé).",
     "Pare-feu : autorisez le simulateur pour les réseaux privés (port TCP 8765)."
    ],
    "it": [
     "In MoveEye: scheda Simulatore → Connessione: inserisci l'indirizzo di questo PC (stessa rete).",
     "Tocca «Ricollega il simulatore» (invio spento e riacceso).",
     "Firewall: consenti il simulatore per le reti private (porta TCP 8765)."
    ],
    "rm": [
     "En MoveEye: register Simulatur → Colliaziun: endatar l'adressa da quest PC (medema rait).",
     "Smatga «Colliar danovamain il simulatur» (trametter or ed en).",
     "Firewall: lubir il simulatur per raits privatas (port TCP 8765)."
    ]
   },
   "aktion": "sim_verbinden"
  },
  {
   "id": "SIM_SLOW",
   "seite": "sim",
   "stufe": "bad",
   "quelle": {
    "sim_diag": [
     "gfx"
    ]
   },
   "titel": {
    "de": "Simulator zu langsam",
    "en": "Simulator too slow",
    "fr": "Simulateur trop lent",
    "it": "Simulatore troppo lento",
    "rm": "Simulatur memia plaun"
   },
   "text": {
    "de": "Der Simulator schafft zu wenige Bilder pro Sekunde – MoveEye erkennt dann kaum etwas.",
    "en": "The simulator makes too few pictures per second – MoveEye then hardly detects anything.",
    "fr": "Le simulateur produit trop peu d'images par seconde – MoveEye ne détecte presque rien.",
    "it": "Il simulatore produce troppe poche immagini al secondo – MoveEye rileva poco.",
    "rm": "Il simulatur fa memia paucs maletgs per secunda – MoveEye na identifitgescha lura strusch nagut."
   },
   "schritte": {
    "de": [
     "Andere Programme schliessen.",
     "Auf «Notfall-Start (Grafik Lite)» tippen – nur für diesen Start, die eigene Wahl bleibt gespeichert.",
     "Dauerhaft: System → Grafik → «Lite»."
    ],
    "en": [
     "Close other programs.",
     "Tap «Emergency start (graphics Lite)» – only for this start, your own choice stays saved.",
     "Permanently: System → Graphics → «Lite»."
    ],
    "fr": [
     "Fermez les autres programmes.",
     "Touchez « Démarrage d'urgence (Lite) » – seulement pour ce démarrage.",
     "Durablement : Système → Graphisme → « Lite »."
    ],
    "it": [
     "Chiudi gli altri programmi.",
     "Tocca «Avvio d'emergenza (Lite)» – solo per questo avvio.",
     "Stabilmente: Sistema → Grafica → «Lite»."
    ],
    "rm": [
     "Serrar autras applicaziuns.",
     "Smatga «Start d'urgenza (Lite)» – mo per quest start.",
     "Permanent: Sistem → Grafica → «Lite»."
    ]
   },
   "aktion": "sim_notfall"
  },
  {
   "id": "SIM_RAM",
   "seite": "sim",
   "stufe": "bad",
   "quelle": {
    "sim_diag": [
     "ram",
     "cpu"
    ]
   },
   "titel": {
    "de": "PC ausgelastet",
    "en": "PC overloaded",
    "fr": "PC surchargé",
    "it": "PC sovraccarico",
    "rm": "PC surchargià"
   },
   "text": {
    "de": "Arbeitsspeicher oder Prozessor des PCs sind fast voll.",
    "en": "Memory or processor of the PC are almost full.",
    "fr": "La mémoire ou le processeur du PC sont presque saturés.",
    "it": "Memoria o processore del PC sono quasi pieni.",
    "rm": "La memoria u il processer dal PC èn bunamain plains."
   },
   "schritte": {
    "de": [
     "Browser-Tabs und andere Programme schliessen.",
     "Auf «Simulator neu starten» tippen."
    ],
    "en": [
     "Close browser tabs and other programs.",
     "Tap «Restart the simulator»."
    ],
    "fr": [
     "Fermez onglets et programmes.",
     "Touchez « Redémarrer le simulateur »."
    ],
    "it": [
     "Chiudi schede e programmi.",
     "Tocca «Riavvia il simulatore»."
    ],
    "rm": [
     "Serrar tabs dal navigatur ed autras applicaziuns.",
     "Smatga «Reaviar il simulatur»."
    ]
   },
   "aktion": "sim_neustart"
  },
  {
   "id": "SIM_DISK",
   "seite": "sim",
   "stufe": "warn",
   "quelle": {
    "sim_diag": [
     "disk"
    ]
   },
   "titel": {
    "de": "Wenig Platz auf dem PC",
    "en": "Little room on the PC",
    "fr": "Peu d'espace sur le PC",
    "it": "Poco spazio sul PC",
    "rm": "Pauca plazza sin il PC"
   },
   "text": {
    "de": "Für Aufnahmen und Trainingsbilder ist bald kein Platz mehr.",
    "en": "Soon there is no room for recordings and training pictures.",
    "fr": "Bientôt plus de place pour enregistrements et images d'entraînement.",
    "it": "Presto non ci sarà spazio per registrazioni e immagini di addestramento.",
    "rm": "Bainprest na datti nagina plazza pli per registraziuns e maletgs da trenament."
   },
   "schritte": {
    "de": [
     "Karte Testen → «Alte KI-Daten löschen».",
     "Alte Aufnahmen im Simulator-Ordner löschen."
    ],
    "en": [
     "Card Testing → «Delete old AI data».",
     "Delete old recordings in the simulator folder."
    ],
    "fr": [
     "Carte Tester → « Supprimer les anciennes données IA ».",
     "Supprimez les anciens enregistrements."
    ],
    "it": [
     "Scheda Test → «Elimina vecchi dati IA».",
     "Elimina le vecchie registrazioni."
    ],
    "rm": [
     "Carta Testar → «Stizzar veglias datas IA».",
     "Stizzar veglias registraziuns en l'ordinatur dal simulatur."
    ]
   }
  },
  {
   "id": "SIM_API",
   "seite": "beide",
   "stufe": "bad",
   "quelle": {
    "sim_diag": [
     "api",
     "upd",
     "godot"
    ]
   },
   "titel": {
    "de": "Simulator und MoveEye passen nicht zusammen",
    "en": "Simulator and MoveEye do not match",
    "fr": "Simulateur et MoveEye incompatibles",
    "it": "Simulatore e MoveEye non compatibili",
    "rm": "Simulatur e MoveEye na correspundan betg"
   },
   "text": {
    "de": "Die Schnittstelle zwischen Simulator und MoveEye stimmt nicht (unterschiedliche Versionen).",
    "en": "The interface between simulator and MoveEye does not match (different versions).",
    "fr": "L'interface entre simulateur et MoveEye ne correspond pas (versions différentes).",
    "it": "L'interfaccia tra simulatore e MoveEye non corrisponde (versioni diverse).",
    "rm": "L'interfatscha tranter simulatur e MoveEye na correspunda betg (versiuns differentas)."
   },
   "schritte": {
    "de": [
     "Beide auf die neueste Version bringen: MoveEye → Mehr → Updates, Simulator → Mehr → Updates.",
     "Die fertige Fassung (ZIP) verwenden – sie ist für Godot 4.3 gebaut."
    ],
    "en": [
     "Update both: MoveEye → More → Updates, simulator → More → Updates.",
     "Use the finished version (ZIP) – it is built for Godot 4.3."
    ],
    "fr": [
     "Mettez les deux à jour : MoveEye → Plus → Mises à jour, simulateur → Plus → Mises à jour.",
     "Utilisez la version prête (ZIP) – construite pour Godot 4.3."
    ],
    "it": [
     "Aggiorna entrambi: MoveEye → Altro → Aggiornamenti, simulatore → Altro → Aggiornamenti.",
     "Usa la versione pronta (ZIP) – fatta per Godot 4.3."
    ],
    "rm": [
     "Actualisar omadus: MoveEye → Dapli → Actualisaziuns, simulatur → Dapli → Actualisaziuns.",
     "Duvrar la versiun finida (ZIP) – ella è fatga per Godot 4.3."
    ]
   }
  },
  {
   "id": "SIM_GODOT_ERR",
   "seite": "sim",
   "stufe": "warn",
   "quelle": {
    "sim_diag": [
     "err"
    ]
   },
   "titel": {
    "de": "Fehler im Simulator",
    "en": "Errors in the simulator",
    "fr": "Erreurs dans le simulateur",
    "it": "Errori nel simulatore",
    "rm": "Errurs en il simulatur"
   },
   "text": {
    "de": "Godot hat seit dem Start Fehler gemeldet.",
    "en": "Godot reported errors since the start.",
    "fr": "Godot a signalé des erreurs depuis le démarrage.",
    "it": "Godot ha segnalato errori dall'avvio.",
    "rm": "Godot ha annunzià errurs dapi il start."
   },
   "schritte": {
    "de": [
     "Mehr → Protokoll → «Fehler» ansehen.",
     "Kopieren und mit einer Rückmeldung schicken.",
     "Hängt etwas: «Simulator neu starten»."
    ],
    "en": [
     "More → Log → look at «Errors».",
     "Copy and send with a feedback.",
     "If something hangs: «Restart the simulator»."
    ],
    "fr": [
     "Plus → Journal → « Erreurs ».",
     "Copiez et envoyez avec un retour.",
     "Si quelque chose bloque : « Redémarrer le simulateur »."
    ],
    "it": [
     "Altro → Registro → «Errori».",
     "Copia e invia con un feedback.",
     "Se qualcosa si blocca: «Riavvia il simulatore»."
    ],
    "rm": [
     "Dapli → Protocol → guardar «Errurs».",
     "Copiar e trametter cun ina resposta.",
     "Sch'insatge è bloccà: «Reaviar il simulatur»."
    ]
   },
   "aktion": "sim_neustart"
  },
  {
   "id": "HW_PCA9685",
   "seite": "mw",
   "stufe": "warn",
   "bau": "verkabeln",
   "titel": {
    "de": "Servo-Steuerung PCA9685 fehlt",
    "en": "Servo board PCA9685 missing",
    "fr": "Carte servo PCA9685 absente",
    "it": "Scheda servo PCA9685 assente",
    "rm": "Platina servo PCA9685 manca"
   },
   "text": {
    "de": "MoveEye findet den PCA9685 auf I2C 0x41 nicht – Kopf, Licht und Status-LED bewegen sich nicht.",
    "en": "MoveEye does not find the PCA9685 on I2C 0x41 – head, light and status LED do not work.",
    "fr": "MoveEye ne trouve pas le PCA9685 sur I2C 0x41 – tête, lumière et LED d'état ne marchent pas.",
    "it": "MoveEye non trova il PCA9685 su I2C 0x41 – testa, luce e LED di stato non funzionano.",
    "rm": "MoveEye na chatta betg il PCA9685 sin I2C 0x41 – chau, glisch e LED da status na funcziunan betg."
   },
   "schritte": {
    "de": [
     "Strom aus. Kabel prüfen: 3,3 V Pin 1, GND Pin 6, SDA Pin 3, SCL Pin 5.",
     "Lötbrücke A0 geschlossen? Sonst hat er 0x40 wie die Thermal-90.",
     "Auf dem Pi «sudo i2cdetect -y 1»: 41 muss erscheinen."
    ],
    "en": [
     "Power off. Check the cables: 3.3 V pin 1, GND pin 6, SDA pin 3, SCL pin 5.",
     "Solder bridge A0 closed? Otherwise it has 0x40 like the Thermal-90.",
     "On the Pi «sudo i2cdetect -y 1»: 41 must show up."
    ],
    "fr": [
     "Couper le courant. Vérifier : 3,3 V broche 1, GND broche 6, SDA broche 3, SCL broche 5.",
     "Pont A0 fermé ? Sinon il a 0x40 comme la Thermal-90.",
     "Sur le Pi «sudo i2cdetect -y 1» : 41 doit apparaître."
    ],
    "it": [
     "Togliere corrente. Controllare: 3,3 V pin 1, GND pin 6, SDA pin 3, SCL pin 5.",
     "Ponticello A0 chiuso? Altrimenti ha 0x40 come la Thermal-90.",
     "Sul Pi «sudo i2cdetect -y 1»: deve comparire 41."
    ],
    "rm": [
     "Current ora. Controllar: 3,3 V pin 1, GND pin 6, SDA pin 3, SCL pin 5.",
     "Punt A0 serrà? Uschiglio ha el 0x40 sco la Thermal-90.",
     "Sin il Pi «sudo i2cdetect -y 1»: 41 sto cumparair."
    ]
   }
  },
  {
   "id": "HW_SERVO_JITTER",
   "seite": "mw",
   "stufe": "warn",
   "bau": "inbetrieb",
   "titel": {
    "de": "Servo zittert oder brummt",
    "en": "Servo jitters or hums",
    "fr": "Le servo tremble ou bourdonne",
    "it": "Il servo trema o ronza",
    "rm": "Il servo tremblescha u zunzurescha"
   },
   "text": {
    "de": "Meist zu wenig Strom für die Servos oder ein mechanischer Anschlag.",
    "en": "Mostly too little power for the servos or a mechanical end stop.",
    "fr": "Le plus souvent trop peu de courant pour les servos ou une butée mécanique.",
    "it": "Di solito poca corrente per i servo o un fine corsa meccanico.",
    "rm": "Per il pli memia pauc current per ils servos u in tschep mecanic."
   },
   "schritte": {
    "de": [
     "Step-Down-Ausgang unter Last messen: 5,0–5,2 V?",
     "Elko 470 µF an V+ des PCA9685 vorhanden?",
     "Grenzen kleiner stellen (Seite Servos), Kopf darf nicht anschlagen."
    ],
    "en": [
     "Measure the step-down output under load: 5.0–5.2 V?",
     "Capacitor 470 µF at V+ of the PCA9685 fitted?",
     "Set smaller limits (page Servos), the head must not hit anything."
    ],
    "fr": [
     "Mesurer la sortie de l'abaisseur en charge : 5,0–5,2 V ?",
     "Condensateur 470 µF sur V+ du PCA9685 présent ?",
     "Réduire les limites (page Servos), la tête ne doit rien toucher."
    ],
    "it": [
     "Misurare l'uscita dello step-down sotto carico: 5,0–5,2 V?",
     "Condensatore 470 µF su V+ del PCA9685 presente?",
     "Ridurre i limiti (pagina Servo), la testa non deve urtare."
    ],
    "rm": [
     "Mesirar la sortida dal step-down sut chargia: 5,0–5,2 V?",
     "Condensatur 470 µF vi da V+ dal PCA9685 avant maun?",
     "Pli pitschens limits (pagina Servos), il chau na dastga betg tutgar."
    ]
   }
  },
  {
   "id": "HW_I2C",
   "seite": "mw",
   "stufe": "warn",
   "bau": "verkabeln",
   "titel": {
    "de": "I2C-Gerät fehlt oder doppelt",
    "en": "I2C device missing or twice",
    "fr": "Appareil I2C absent ou en double",
    "it": "Dispositivo I2C assente o doppio",
    "rm": "Apparat I2C manca u dubel"
   },
   "text": {
    "de": "Zwei Module mit derselben Adresse stören sich, ein lockeres Kabel versteckt ein Modul.",
    "en": "Two modules with the same address disturb each other, a loose cable hides a module.",
    "fr": "Deux modules à la même adresse se gênent, un câble lâche cache un module.",
    "it": "Due moduli con lo stesso indirizzo si disturbano, un cavo allentato nasconde un modulo.",
    "rm": "Dus moduls cun la medema adressa sa disturban, in cabel lom zuppenta in modul."
   },
   "schritte": {
    "de": [
     "«sudo i2cdetect -y 1» ausführen und mit dem Reiter Verkabeln vergleichen.",
     "Erwartet: 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), 68 MPU-6050, 76/77 BME280, 44 INA219.",
     "Fehlt eins: Module einzeln abstecken, bis es wieder geht."
    ],
    "en": [
     "Run «sudo i2cdetect -y 1» and compare it with the tab Wiring.",
     "Expected: 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), 68 MPU-6050, 76/77 BME280, 44 INA219.",
     "One missing: unplug the modules one by one until it works again."
    ],
    "fr": [
     "Lancer «sudo i2cdetect -y 1» et comparer avec l'onglet Câblage.",
     "Attendu : 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), 68 MPU-6050, 76/77 BME280, 44 INA219.",
     "S'il en manque un : débrancher les modules un par un."
    ],
    "it": [
     "Eseguire «sudo i2cdetect -y 1» e confrontare con la scheda Cablaggio.",
     "Atteso: 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), 68 MPU-6050, 76/77 BME280, 44 INA219.",
     "Ne manca uno: staccare i moduli uno alla volta."
    ],
    "rm": [
     "Exequir «sudo i2cdetect -y 1» e cumparegliar cun il tab Cablar.",
     "Spetgà: 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), 68 MPU-6050, 76/77 BME280, 44 INA219.",
     "Manca in: distatgar ils moduls in ad in."
    ]
   }
  },
  {
   "id": "HW_UPS",
   "seite": "mw",
   "stufe": "warn",
   "bau": "verkabeln",
   "titel": {
    "de": "Akku-Platine (UPS HAT) nicht gefunden",
    "en": "Battery board (UPS HAT) not found",
    "fr": "Carte batterie (UPS HAT) introuvable",
    "it": "Scheda batteria (UPS HAT) non trovata",
    "rm": "Platina d'accu (UPS HAT) betg chattada"
   },
   "text": {
    "de": "Ohne UPS HAT zeigt MoveEye keinen Akkustand und fährt bei leerem Akku nicht sauber herunter.",
    "en": "Without the UPS HAT MoveEye shows no battery level and does not shut down cleanly when empty.",
    "fr": "Sans UPS HAT, MoveEye n'affiche pas la batterie et ne s'éteint pas proprement à vide.",
    "it": "Senza UPS HAT MoveEye non mostra la batteria e non si spegne bene a batteria scarica.",
    "rm": "Senza UPS HAT na mussa MoveEye nagin stadi d'accu e na sa stizza betg endretg."
   },
   "schritte": {
    "de": [
     "Pogo-Pins sauber unter dem Pi? Akkus richtig herum und geladen?",
     "«sudo i2cdetect -y 1»: 2d muss erscheinen.",
     "Einstellungen → Stromversorgung: Modell «UPS HAT (E)» wählen."
    ],
    "en": [
     "Pogo pins clean under the Pi? Cells the right way round and charged?",
     "«sudo i2cdetect -y 1»: 2d must show up.",
     "Settings → Power supply: choose the model «UPS HAT (E)»."
    ],
    "fr": [
     "Broches pogo propres sous le Pi ? Cellules dans le bon sens et chargées ?",
     "«sudo i2cdetect -y 1» : 2d doit apparaître.",
     "Réglages → Alimentation : choisir le modèle «UPS HAT (E)»."
    ],
    "it": [
     "Pin pogo puliti sotto il Pi? Celle nel verso giusto e cariche?",
     "«sudo i2cdetect -y 1»: deve comparire 2d.",
     "Impostazioni → Alimentazione: scegliere il modello «UPS HAT (E)»."
    ],
    "rm": [
     "Pins pogo nets sut il Pi? Cellas endretg e chargiadas?",
     "«sudo i2cdetect -y 1»: 2d sto cumparair.",
     "Parameters → Alimentaziun: tscherner il model «UPS HAT (E)»."
    ]
   }
  },
  {
   "id": "HW_LIGHT",
   "seite": "mw",
   "stufe": "warn",
   "bau": "verkabeln",
   "quelle": {
    "meldung": [
     "Light error"
    ]
   },
   "titel": {
    "de": "Licht geht nicht",
    "en": "The light does not work",
    "fr": "La lumière ne marche pas",
    "it": "La luce non funziona",
    "rm": "La glisch na funcziuna betg"
   },
   "text": {
    "de": "Weisses oder IR-Licht bleibt dunkel.",
    "en": "White or IR light stays dark.",
    "fr": "La lumière blanche ou IR reste éteinte.",
    "it": "La luce bianca o IR resta spenta.",
    "rm": "La glisch alva u IR resta stgira."
   },
   "schritte": {
    "de": [
     "Einstellungen → Licht & Ton: Licht weiss = PCA9685 Kanal 2, Infrarot = Kanal 3?",
     "MOSFET-Modul (Logic-Level) richtig verdrahtet, 5 V an den Lampen?",
     "IR-Licht im Kamerabild prüfen – das Auge sieht 850 nm kaum."
    ],
    "en": [
     "Settings → Light & sound: white light = PCA9685 channel 2, infrared = channel 3?",
     "MOSFET module (logic level) wired correctly, 5 V at the lamps?",
     "Check the IR light in the camera picture – the eye hardly sees 850 nm."
    ],
    "fr": [
     "Réglages → Lumière et son : blanc = canal 2 du PCA9685, infrarouge = canal 3 ?",
     "Module MOSFET (niveau logique) bien câblé, 5 V aux lampes ?",
     "Vérifier l'IR dans l'image de la caméra – l'œil voit à peine 850 nm."
    ],
    "it": [
     "Impostazioni → Luce e suono: bianco = canale 2 del PCA9685, infrarosso = canale 3?",
     "Modulo MOSFET (livello logico) cablato bene, 5 V alle lampade?",
     "Controllare l'IR nell'immagine della fotocamera – l'occhio vede appena 850 nm."
    ],
    "rm": [
     "Parameters → Glisch e tun: alv = chanal 2 dal PCA9685, infracotschen = chanal 3?",
     "Modul MOSFET (logic level) cablà endretg, 5 V vi da las lampas?",
     "Controllar l'IR en il maletg da la camera – l'egl vesa strusch 850 nm."
    ]
   }
  },
  {
   "id": "HW_SOUND",
   "seite": "mw",
   "stufe": "warn",
   "bau": "verkabeln",
   "titel": {
    "de": "Kein Ton aus dem Lautsprecher",
    "en": "No sound from the loudspeaker",
    "fr": "Pas de son du haut-parleur",
    "it": "Nessun suono dall'altoparlante",
    "rm": "Nagin tun da l'autpledader"
   },
   "text": {
    "de": "Sirene, Wecker und Sprechen bleiben stumm.",
    "en": "Siren, alarm clock and talking stay silent.",
    "fr": "Sirène, réveil et parole restent muets.",
    "it": "Sirena, sveglia e parlato restano muti.",
    "rm": "Sirena, sveglia e discurrer restan muts."
   },
   "schritte": {
    "de": [
     "USB-Soundkarte im Hub? In MoveEye unter Licht & Ton als Ausgang gewählt?",
     "PAM8403 hat 5 V und Klinke L / GND, Lautsprecher an L+ / L−?",
     "Ton testen (Wecker-Melodie); Lautstärke nicht auf 0."
    ],
    "en": [
     "USB sound card in the hub? Chosen as output under Light & sound in MoveEye?",
     "PAM8403 has 5 V and jack L / GND, loudspeaker on L+ / L−?",
     "Test the sound (alarm melody); volume not at 0."
    ],
    "fr": [
     "Carte son USB dans le hub ? Choisie comme sortie sous Lumière et son ?",
     "PAM8403 a 5 V et jack L / GND, haut-parleur sur L+ / L− ?",
     "Tester le son (mélodie du réveil) ; volume pas à 0."
    ],
    "it": [
     "Scheda audio USB nell'hub? Scelta come uscita in Luce e suono?",
     "PAM8403 ha 5 V e jack L / GND, altoparlante su L+ / L−?",
     "Provare il suono (melodia sveglia); volume non a 0."
    ],
    "rm": [
     "Carta da tun USB en il hub? Tschernida sco sortida sut Glisch e tun?",
     "PAM8403 ha 5 V e jack L / GND, autpledader vi da L+ / L−?",
     "Testar il tun (melodia da sveglia); volumen betg sin 0."
    ]
   }
  }
 ]
}""")
FX = {"secret": secrets.token_bytes(32), "cache": (0.0, None, None), "upd_err": None, "last": {}}
FX_LANGS = ("de", "en", "fr", "it", "rm")


def fx_entries():
    return [e for e in (FEHLER_KATALOG.get("fehler") or []) if isinstance(e, dict) and e.get("id")]


def fx_entry(fid):
    fid = str(fid or "").strip().upper()
    return next((e for e in fx_entries() if e["id"] == fid), None)


def _fx_l(lang):
    L = norm_lang(lang) if lang else cur_lang()
    return L if L in FX_LANGS else "en"


def fx_t(d, lang=None):
    """a {de, en, fr, it, rm} value of the catalogue in the language (fallback: rm -> de, others -> en)"""
    if not isinstance(d, dict):
        return d if d is not None else ""
    L = _fx_l(lang)
    return d.get(L) or d.get("de" if L == "rm" else "en") or d.get("de") or ""


def fx_ui(key, lang=None):
    return fx_t((FEHLER_KATALOG.get("ui") or {}).get(key) or {"en": key}, lang)


def fx_act_name(act, lang=None):
    return fx_t((FEHLER_KATALOG.get("aktionen") or {}).get(act) or {"en": act}, lang)


def fx_base():
    """the address a phone in the same network opens (the QR code points there); public_url when it is set"""
    pu = str(CFG.get("public_url") or "").strip().rstrip("/")
    if pu.startswith(("http://", "https://")):
        return pu
    try:
        pa = page_address().rstrip("/")
    except Exception:
        pa = ""
    if pa:
        return pa
    try:
        a = setup_addresses()
        if a:
            return a[0]["url"].rstrip("/")
    except Exception:
        pass
    try:                                                    # no network address known: the address the browser uses now
        from flask import has_request_context, request
        if has_request_context():
            return request.host_url.rstrip("/")
    except Exception:
        pass
    return ""


def fx_path(fid):
    return str(FEHLER_KATALOG.get("pfad") or "/hilfe/fehler/") + str(fid)


def fx_url(fid, base=None):
    """the text of the QR code: only the address of the help page (no password, no key, no token)"""
    b = (fx_base() if base is None else str(base)).rstrip("/")
    return (b + fx_path(fid)) if b else ""


# ---- which errors are there now -------------------------------------------------------------------------------------------
def _fx_cond(cond):
    try:
        if cond == "push_fehlt":
            return not Notifier.configured()
        if cond == "push_fehler":
            return Notifier.configured()
    except Exception:
        return False
    return True


def fx_for_health(item):
    """the catalogue entry of one line of the self-check (or None)"""
    lv = item.get("level")
    if lv not in ("bad", "warn"):
        return None
    for e in fx_entries():
        q = e.get("quelle") or {}
        if item.get("id") in (q.get("health") or []) and e.get("seite") in ("mw", "beide") and _fx_cond(q.get("wenn")):
            if lv == "bad" or e.get("stufe") == "warn":
                return e
    return None


def fx_update_failed():
    """the last update failed (update_install / the source) - within a day and as long as no newer version runs"""
    u = FX.get("upd_err")
    if u and time.time() - u[0] < 86400 and u[2] == APP_VERSION:
        return u[1]
    m = str(UPD.get("msg") or "")
    if m.startswith(("update source not reachable", "restart failed")) and time.time() - float(UPD.get("time") or 0) < 86400:
        return m
    return ""


def _fx_extra_items(L):
    """three more lines of the self-check (only added; the rest stays as it is)"""
    T = lambda x: tr(x, L)
    out = []
    try:
        if CFG.get("sim_on") and time.time() - RUNGUARD["t0"] > 60:
            gone = (not SIM.get("ok")) or time.time() - float(SIM.get("t") or 0) > 15
            out.append({"id": "sim", "icon": "🧪", "title": T("Simulator"), "level": "bad" if gone else "ok",
                        "text": tr_err(str(SIM.get("msg") or "simulator not reachable"), L) if gone else T("connected"), "tip": ""})
    except Exception:
        pass
    um = fx_update_failed()
    if um:
        out.append({"id": "update", "icon": "⬆", "title": T("Updates"), "level": "warn", "text": tr_err(um, L)[:160], "tip": ""})
    try:
        if not ZD["ok"]:
            out.append({"id": "zusatz", "icon": "📦", "title": fx_t(fx_entry("DATA_MISSING")["titel"], L), "level": "bad",
                        "text": str(ZD_FILE or "moveeye_daten_*.zip") + (" · " + str(ZD.get("err") or "")[:80] if ZD.get("err") else ""), "tip": ""})
    except Exception:
        pass
    return out


_health_check_before_fx = health_check


# wraps: health_check
def health_check(lang=None):
    """+ 639u: every problem with a catalogue entry gets «fehler» (help page, QR address, fix) - the lines stay as they are"""
    h = _health_check_before_fx(lang)
    try:
        L = _fx_l(lang)
        extra = _fx_extra_items(L)
        if extra and isinstance(h, dict) and isinstance(h.get("items"), list):
            h["items"].extend(extra)
            try:
                h["items"].sort(key=lambda x: HEALTH_ORDER.index(x["level"]))
                h["count"] = {k: sum(1 for x in h["items"] if x["level"] == k) for k in HEALTH_ORDER}
            except (ValueError, KeyError, NameError):
                pass
        user = None
        try:                                                # a page of the owner asks: the button «Fix» gets its CSRF key
            from flask import has_request_context, request, g as g_
            if has_request_context():
                user = fx_owner(request, g_)[0]
        except Exception:
            user = None
        for x in h.get("items") or []:
            e = fx_for_health(x)
            if e is not None:
                x["fehler"] = fx_info(e, L, user)
    except Exception as ex:
        log_event("sys", f"Fehler-QR: {ex}"[:160])
    return h


def fx_info(e, L, user=None):
    """what a page / window needs for one error (the CSRF key only when fx_owner gives a user)"""
    d = {"id": e["id"], "path": fx_path(e["id"]), "url": fx_url(e["id"]), "title": fx_t(e.get("titel"), L), "stufe": e.get("stufe", "bad"),
         "fix": fx_act_name(e["aktion"], L) if e.get("aktion") else "", "help": fx_ui("help", L), "fix_word": fx_ui("fix", L)}
    if user is not None and e.get("aktion"):
        d["tok"] = fx_token(user, e["id"])
    return d


def fx_active(lang=None, only_bad=True):
    """[(item of the self-check, entry)] of now - cached 10 s (SmallTV, TV, window ask often)"""
    now = time.time()
    t0, L0, res = FX["cache"]
    L = _fx_l(lang)
    if res is None or now - t0 > 10 or L0 != L:
        res = []
        try:
            for x in health_check(L).get("items") or []:
                if x.get("fehler"):
                    e = fx_entry(x["fehler"]["id"])
                    if e is not None:
                        res.append((x, e))
        except Exception:
            res = []
        FX["cache"] = (now, L, res)
    return [r for r in res if r[0].get("level") == "bad"] if only_bad else list(res)


# ---- who may fix: the owner, logged in; CSRF key ----------------------------------------------------------------------------
def fx_token(user, fid):
    return _fx_hmac.new(FX["secret"], ("%s|%s" % (user or "", fid)).encode("utf-8"), "sha256").hexdigest()[:40]


def fx_token_ok(user, fid, tok):
    return bool(tok) and _fx_hmac.compare_digest(fx_token(user, fid), str(tok)[:80])


def _fx_local(request):
    return (request.remote_addr or "") in ("127.0.0.1", "::1") and not (request.headers.get("X-Forwarded-For") or request.headers.get("Forwarded")
                                                                      or request.headers.get("X-Forwarded-Host"))


def fx_owner(request, g_):
    """(user, error key) - user is None when this request may not fix anything"""
    if getattr(g_, "role", "admin") != "admin" or getattr(g_, "appkey", None):
        return None, "owner"
    if not web_pw_active() and not _fx_local(request):
        return None, "pw_first"
    return str(getattr(g_, "user", "") or ""), ""


# ---- the actions (existing functions only) ----------------------------------------------------------------------------------
def _fx_watch():
    return WATCH_REF.get("w")


def _fx_cam_reopen():
    w = _fx_watch()
    if w is None:
        return False, "MoveEye is not running"
    w._open_gen += 1
    w._start_opener(CFG["source"])
    return True, "connecting…"


def _fx_bg(name, fn):
    def work():
        try:
            fn()
        except Exception as ex:
            log_event("sys", f"Fehler-QR {name}: {ex}"[:160])
    threading.Thread(target=work, daemon=True, name="fx-" + name).start()


def fx_run(act, who="web"):
    """run one action -> (ok, message in English: tr_err() translates it)"""
    log_event("sys", f"Fix «{act}» by {who}")
    if act == "kamera_neu":
        return _fx_cam_reopen()
    if act == "dienst_neu":
        ok, reason = selfheal_allowed()
        if not ok:
            return False, "limit reached: " + str(reason)
        return (True, "MoveEye restarts …") if selfheal_restart("manual", "Restart by the owner (fix)") else (False, "a restart is already running")
    if act == "ki_laden":
        return ai_model_download()
    if act == "speicher":
        before = (STATE.get("disk") or {}).get("free_mb")
        w = _fx_watch()
        if w is not None:
            w.cleanup_recordings()
        for f in ("tl_cleanup", "rec_clean_tmp", "zusatz_aufraeumen", "log_purge"):
            try:
                globals()[f]()
            except Exception:
                pass
        try:
            free = int(shutil.disk_usage(CFG["record_dir"]).free / 1024 ** 2)
            STATE.setdefault("disk", {})["free_mb"] = free
        except (OSError, KeyError, TypeError):
            free = None
        FX["cache"] = (0.0, None, None)
        return True, ("%.1f GB free" % (free / 1024)) if free is not None else "cleaned up"
    if act == "update":
        if UPD.get("busy"):
            return False, "an update is already running"
        items, err = update_check()
        if err:
            return False, err
        new = sorted((x for x in items if x.get("available") and _installable(x) and _vkey(x["version"]) > _vkey(APP_VERSION)),
                     key=lambda x: _vkey(x["version"]))
        if not new:
            FX["upd_err"] = None
            return True, "this version is already running"
        return update_install(new[-1]["version"])
    if act == "zusatzdaten":
        if ZD["ok"]:
            return True, "the data file is there"
        err = zusatz_holen()
        if err:
            return False, err
        zusatz_restart()
        return True, "MoveEye restarts …"
    if act == "wlan":
        ok, err = wifi_scan()
        if not ok:
            return False, err
        st = wifi_status()
        if st.get("connected") and (STATE.get("net") or {}).get("online") is not False:
            return True, "connected"
        cand = [n for n in st.get("scan") or [] if n.get("saved") and not n.get("active")]
        if not cand:
            return False, "no saved network in range"
        return wifi_connect(cand[0]["ssid"], "", True)
    if act == "push_test":
        w = _fx_watch()
        if w is None:
            return False, "MoveEye is not running"
        res = push_test_one(w, "all") or []
        n_ok = sum(1 for r in res if r.get("ok"))
        return (n_ok > 0 or not res), "%d / %d" % (n_ok, len(res))
    if act == "sim_verbinden":
        def go():
            sim_scan()
            sim_auto_adopt()
            if CFG.get("sim_on") and str(CFG.get("source") or "").startswith("sim:"):
                _fx_cam_reopen()
        _fx_bg("sim", go)
        return True, "connecting…"
    if act in ("sim_neustart", "sim_notfall"):
        try:
            r = sim_control({"action": "fehler", "do": "fix", "aktion": act})
        except Exception:
            return False, "simulator not reachable"
        if not isinstance(r, dict) or not r.get("ok"):
            return False, str((r or {}).get("error") or "not supported - update the simulator")
        return True, "the simulator restarts …"
    return False, "unknown action"


_update_install_before_fx = update_install


# wraps: update_install
def update_install(version):
    """+ 639u: a failed update is remembered for the self-check line «Updates» (help page UPDATE_FAIL)"""
    ok, err = _update_install_before_fx(version)
    if not ok and err and "already running" not in err:
        FX["upd_err"] = (time.time(), err, APP_VERSION)
    elif ok:
        FX["upd_err"] = None
    return ok, err


# ---- the help page (self-contained: works without the data file, too) ------------------------------------------------------
_FX_CSS = ("body{margin:0;background:#0b0f14;color:#e8eef5;font:16px/1.5 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}"
           "@media(prefers-color-scheme:light){body{background:#f4f6f9;color:#111}.box{background:#fff!important;border-color:#d8dee6!important}.mut{color:#5b6878!important}}"
           "main{max-width:720px;margin:0 auto;padding:16px}a{color:#3b8cff}.top{display:flex;align-items:center;gap:10px;margin-bottom:10px}"
           ".top img{width:36px;height:36px;border-radius:9px}.top b{font-size:18px}.mut{color:#8a9bb0;font-size:13px}"
           ".box{background:#111822;border:1px solid #1f2b3a;border-radius:14px;padding:14px 16px;margin:10px 0}"
           "h1{font-size:22px;margin:4px 0 8px}h2{font-size:16px;margin:0 0 6px}ol{margin:0;padding-left:22px}li{margin:4px 0}"
           ".lv{display:inline-block;border-radius:99px;padding:1px 10px;font-size:12px;font-weight:700;color:#fff;background:#e5484d}.lv.warn{background:#f2a33a}"
           "button{font:700 16px system-ui;padding:12px 18px;border-radius:12px;border:0;background:#3b8cff;color:#fff;cursor:pointer;width:100%}"
           ".ok{border-color:#3fcf6b!important}.bad{border-color:#e5484d!important}.qr{display:flex;gap:14px;align-items:center}"
           ".qr .q{background:#fff;border-radius:10px;padding:6px;width:132px;height:132px;flex:none}.qr .q svg{width:100%;height:100%}"
           ".code{font-family:ui-monospace,Menlo,monospace;font-size:12px}.list a{display:block;padding:6px 0;border-bottom:1px solid #1f2b3a;text-decoration:none}"
           "@media(pointer:coarse){.qr{display:none}}")


def _fx_head(title, L):
    return ('<!doctype html><html lang="' + L + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="referrer" content="no-referrer"><title>MoveEye – ' + html_escape(title) + '</title><style>' + _FX_CSS + '</style></head><body><main>'
            '<div class="top"><img src="/icon-192.png" alt=""><div><b>MoveEye</b><div class="mut">' + html_escape(fx_ui("help", L)) + ' · ' + html_escape(fx_ui("error", L))
            + '</div></div></div>')


def fx_page(fid, lang=None, user=None, why="", result=None):
    """the page /hilfe/fehler/<ID>. user: the owner (fix button with CSRF key); why: why not («owner» / «pw_first»)"""
    L = _fx_l(lang)
    e = fx_entry(fid)
    if e is None:
        return (_fx_head(fx_ui("unknown", L), L) + '<div class="box bad"><h1>' + html_escape(fx_ui("unknown", L)) + '</h1><p class="code">'
                + html_escape(str(fid)[:40]) + '</p><a href="' + fx_path("") + '">' + html_escape(fx_ui("all", L)) + '</a></div></main></body></html>'), 404
    tl = fx_t(e.get("titel"), L)
    act = [x for x, _e in fx_active(L, only_bad=False) if _e["id"] == e["id"]]
    h = _fx_head(tl, L) + '<div class="box ' + ("bad" if e.get("stufe") == "bad" else "") + '">'
    h += ('<span class="lv ' + html_escape(e.get("stufe", "bad")) + '">' + html_escape(fx_ui("active", L) if act else fx_ui("error", L)) + '</span> '
          '<span class="mut code">' + html_escape(fx_ui("code", L)) + ': ' + html_escape(e["id"]) + '</span>')
    h += '<h1>' + html_escape(tl) + '</h1>'
    if act and act[0].get("text"):
        h += '<p class="mut">' + html_escape(str(act[0].get("text"))[:200]) + '</p>'
    h += '<h2>' + html_escape(fx_ui("what", L)) + '</h2><p>' + html_escape(fx_t(e.get("text"), L)) + '</p></div>'
    h += '<div class="box"><h2>' + html_escape(fx_ui("steps", L)) + '</h2><ol>' + "".join(
        '<li>' + html_escape(s) + '</li>' for s in (fx_t(e.get("schritte"), L) or [])) + '</ol></div>'
    if result is not None:
        ok_, msg_ = result
        h += ('<div class="box ' + ("ok" if ok_ else "bad") + '"><b>' + ("✓ " + html_escape(fx_ui("done", L)) if ok_ else "⚠ " + html_escape(fx_ui("failed", L)))
              + '</b>' + ((' – ' + html_escape(tr_err(str(msg_), L))) if msg_ else "") + '</div>')
    if e.get("aktion"):
        h += '<div class="box">'
        if user is not None:
            h += ('<form method="post" action="' + fx_path(e["id"]) + '/beheben">'
                  '<input type="hidden" name="csrf" value="' + fx_token(user, e["id"]) + '"><input type="hidden" name="lang" value="' + L + '">'
                  '<button type="submit">🛠 ' + html_escape(fx_ui("fix_now", L)) + ': ' + html_escape(fx_act_name(e["aktion"], L)) + '</button></form>')
        else:
            h += '<p>🔒 ' + html_escape(fx_ui("pw_first" if why == "pw_first" else "owner", L)) + '</p>'
        h += '</div>'
    else:
        h += '<p class="mut">' + html_escape(fx_ui("manual", L)) + '</p>'
    u = fx_url(e["id"])
    if u:
        try:
            h += ('<div class="box qr"><div class="q">' + qr_svg(u) + '</div><div><div class="mut">' + html_escape(fx_ui("scan", L))
                  + '</div><div class="code">' + html_escape(u) + '</div></div></div>')
        except ValueError:
            pass
    h += '<p><a href="/">← ' + html_escape(fx_ui("back", L)) + '</a> · <a href="' + fx_path("") + '?lang=' + L + '">' + html_escape(fx_ui("all", L)) + '</a></p></main></body></html>'
    return h, 200


def fx_list_page(lang=None):
    L = _fx_l(lang)
    act = {e["id"] for _x, e in fx_active(L, only_bad=False)}
    rows = sorted(fx_entries(), key=lambda e: (e["id"] not in act, e.get("seite") == "sim", e["id"]))
    h = _fx_head(fx_ui("all", L), L) + '<div class="box list"><h1>' + html_escape(fx_ui("all", L)) + '</h1>'
    for e in rows:
        h += ('<a href="' + fx_path(e["id"]) + '?lang=' + L + '">' + ("⚠ " if e["id"] in act else "") + html_escape(fx_t(e.get("titel"), L))
              + ' <span class="mut code">' + html_escape(e["id"]) + ('' if not e.get("aktion") else ' · 🛠') + '</span></a>')
    return h + '</div><p><a href="/">← ' + html_escape(fx_ui("back", L)) + '</a></p></main></body></html>'


def _fx_lang_of(request):
    return _fx_l(request.values.get("lang") or (request.accept_languages.best_match(FX_LANGS) if request.accept_languages else None) or CFG.get("lang"))


_qr_routes_before_fx = qr_routes


# wraps: qr_routes
def qr_routes(app, reply, body):
    """+ 639u: /hilfe/fehler/, /hilfe/fehler/<ID>, POST …/beheben, GET /api/fehler, POST /api/fehler/fix (550 calls qr_routes once)"""
    _qr_routes_before_fx(app, reply, body)
    from flask import request, Response, g as g_
    hdr = {"Cache-Control": "no-store"}

    @app.route("/hilfe/fehler/")
    def fx_list_route():
        return Response(fx_list_page(_fx_lang_of(request)), mimetype="text/html", headers=hdr)

    @app.route("/hilfe/fehler/<fid>")
    def fx_page_route(fid):
        user, why = fx_owner(request, g_)
        h, code = fx_page(fid, _fx_lang_of(request), user, why)
        return Response(h, code, mimetype="text/html", headers=hdr)

    @app.route("/hilfe/fehler/<fid>/beheben", methods=["POST"])
    def fx_fix_route(fid):
        L = _fx_lang_of(request)
        e = fx_entry(fid)
        user, why = fx_owner(request, g_)
        if e is None or not e.get("aktion"):
            h, code = fx_page(fid, L, user, why)
            return Response(h, 404 if e is None else 400, mimetype="text/html", headers=hdr)
        if user is None:
            h, _c = fx_page(fid, L, None, why)
            return Response(h, 403, mimetype="text/html", headers=hdr)
        if not fx_token_ok(user, e["id"], request.form.get("csrf")):
            log_event("web", f"Fix {e['id']} refused: wrong CSRF key from {request.remote_addr}")
            h, _c = fx_page(fid, L, user, why, (False, "refused"))
            return Response(h, 403, mimetype="text/html", headers=hdr)
        res = fx_run(e["aktion"], "web " + (request.remote_addr or "?"))
        FX["last"][e["id"]] = (time.time(), bool(res[0]))
        FX["cache"] = (0.0, None, None)
        h, _c = fx_page(fid, L, user, why, res)
        return Response(h, 200 if res[0] else 409, mimetype="text/html", headers=hdr)

    @app.route("/api/fehler")
    def fx_api_list():
        L = _fx_l(request.args.get("lang"))
        user, _why = fx_owner(request, g_)
        return reply({"ok": True, "items": [dict(fx_info(e, L, user), text=str(x.get("text") or "")[:160], level=x.get("level"))
                                            for x, e in fx_active(L, only_bad=False)], "owner": user is not None})

    @app.route("/api/fehler/fix", methods=["POST"])
    def fx_api_fix():
        d = body()
        L = _fx_l(d.get("lang"))
        e = fx_entry(d.get("id"))
        user, why = fx_owner(request, g_)
        if e is None or not e.get("aktion"):
            return reply({"ok": False, "error": fx_ui("manual", L)}, 400)
        if user is None:
            return reply({"ok": False, "error": fx_ui("pw_first" if why == "pw_first" else "owner", L)}, 403)
        if not fx_token_ok(user, e["id"], d.get("csrf")):
            return reply({"ok": False, "error": "refused (CSRF)"}, 403)
        ok, msg = fx_run(e["aktion"], "web " + (request.remote_addr or "?"))
        FX["last"][e["id"]] = (time.time(), bool(ok))
        FX["cache"] = (0.0, None, None)
        return reply({"ok": bool(ok), "msg": tr_err(str(msg), L) if msg else "", "error": None if ok else tr_err(str(msg), L)}, 200 if ok else 409)


# ---- web: the button / QR next to every problem of the self-check (530 healthLoad calls fxDeco) -----------------------------
FX_JS = r"""<script>
window.fxDeco = function (b, f) {
  if (!f || !b) return;
  const touch = window.matchMedia && matchMedia("(pointer: coarse)").matches;
  const row = document.createElement("div"); row.className = "fx-row"; row.style.cssText = "display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:6px";
  if (f.fix && f.tok) {
    const k = document.createElement("button"); k.type = "button"; k.textContent = "🛠 " + f.fix_word + ": " + f.fix; k.title = f.fix;
    k.onclick = async () => { k.disabled = true;
      let r = {}; try { r = await (await fetch("/api/fehler/fix", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: f.id, csrf: f.tok, lang: (typeof LANG !== "undefined" ? LANG : "")})})).json(); } catch (e) { r = {ok: false, error: String(e)}; }
      if (typeof toast === "function") toast((r.ok ? "✓ " : "⚠ ") + (r.msg || r.error || "")); k.disabled = false;
      if (typeof healthLoad === "function") setTimeout(healthLoad, 1500); };
    row.appendChild(k);
  }
  const a = document.createElement("a"); a.href = f.path + "?lang=" + (typeof LANG !== "undefined" ? LANG : ""); a.textContent = "ℹ " + f.help; a.style.cssText = "font-size:13px;color:var(--acc,#3b8cff);font-weight:600";
  row.appendChild(a);
  if (!touch && f.url && typeof qrBtn === "function") { try { row.appendChild(qrBtn(f.url, f.title, {note: f.id})); } catch (e) {} }
  b.appendChild(row);
};
</script>"""

_render_page_before_fx = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639u: fxDeco (button «Fix» / QR next to the problems of the self-check) on every page"""
    out = _render_page_before_fx(page, active)
    return out.replace("</head>", FX_JS + "</head>", 1) if "</head>" in out else out


# ---- picture «NO CAMERA FOUND»: the QR code at the top left (window, web live picture, TV) ----------------------------------
def fx_qr_gray(text, scale=3):
    """QR as a grey picture (numpy, white quiet zone of 4 modules)"""
    M = qr_matrix(text)
    n = len(M); q = 4
    a = np.full((n + 2 * q, n + 2 * q), 255, np.uint8)
    a[q:q + n, q:q + n][np.array(M, bool)] = 0
    return cv2.resize(a, ((n + 2 * q) * scale,) * 2, interpolation=cv2.INTER_NEAREST)


_no_camera_frame_before_fx = MotionWatch.no_camera_frame


def _fx_no_camera_frame(self):
    img = _no_camera_frame_before_fx(self)
    try:
        busy = str(STATE.get("source_status") or "").startswith(("connecting", "connection lost"))
        u = fx_url("SIM_UNREACHABLE" if str(CFG.get("source") or "").startswith("sim:") else "CAM_NONE")
        if u and not busy:
            g = fx_qr_gray(u, 3)
            s = g.shape[0]
            if s + 12 <= img.shape[0] and s + 12 < 150:
                img[8:8 + s, 8:8 + s] = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
                cv2.putText(img, "SCAN: HELP / FIX", (8, 8 + s + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (230, 230, 230), 1)
    except Exception:
        pass
    return img


# wraps: MotionWatch.no_camera_frame
MotionWatch.no_camera_frame = _fx_no_camera_frame


# ---- push messages: a link to the help page ---------------------------------------------------------------------------------
def fx_for_text(*texts):
    """the catalogue entry whose «meldung» (English, or in the language of the device) is in one of the texts"""
    s = " ".join(str(t or "") for t in texts).lower()
    if not s.strip():
        return None
    for e in fx_entries():
        for m in (e.get("quelle") or {}).get("meldung") or []:
            for v in {m, tr(m)}:
                if v and v.lower() in s:
                    return e
    return None


def fx_push_line(e):
    """the base for a push: public_url (from outside) or the address in the own network"""
    u = fx_url(e["id"])
    return ("\n🛠 " + fx_ui("help", None) + ": " + u) if u else ""


_alert_before_fx = Notifier.alert
_info_before_fx = Notifier.info


def _fx_alert(self, title, text, frame=None):
    try:
        e = fx_for_text(title, text)
        if e is not None:
            text = str(text or "") + fx_push_line(e)
    except Exception:
        pass
    return _alert_before_fx(self, title, text, frame)


def _fx_info(self, text, link="", title="", jpg=None, fname="info.jpg"):
    try:
        e = fx_for_text(title, text)
        if e is not None:
            text = str(text or "") + fx_push_line(e)
            link = link or fx_url(e["id"])
    except Exception:
        pass
    return _info_before_fx(self, text, link, title, jpg, fname)


# wraps: Notifier.alert
Notifier.alert = _fx_alert
# wraps: Notifier.info
Notifier.info = _fx_info


# ---- SmallTV: a page with the QR code (every other 20 s while an error is there) -------------------------------------------
def stv_render_fehler(x, e, lang=None, red=False):
    from PIL import Image
    im, d = _stv_canvas()
    _stv_head(im, d, "⚠")
    L = _fx_l(lang)
    d.rounded_rectangle((6, 34, STV_SIZE - 6, 62), radius=8, fill=(200, 50, 55) if e.get("stufe") == "bad" else (190, 130, 30))
    f = _font(17)
    d.text((12, 39), _stv_fit(d, _stv_txt(fx_t(e.get("titel"), L)), f, STV_SIZE - 24), font=f, fill=(255, 255, 255))
    u = fx_url(e["id"])
    if u:
        try:
            g = fx_qr_gray(u, 4)
            if g.shape[0] > 168:
                g = cv2.resize(g, (168, 168), interpolation=cv2.INTER_NEAREST)
            q = Image.fromarray(g).convert("RGB")
            im.paste(q, ((STV_SIZE - q.width) // 2, 66))
        except Exception:
            pass
    else:
        for i, ln in enumerate(_stv_wrap(d, _stv_txt(fx_t(e.get("text"), L)), _font(15, False), STV_SIZE - 20, 6)):
            d.text((10, 72 + i * 20), ln, font=_font(15, False), fill=(200, 210, 222))
    d.text((10, STV_SIZE - 20), _stv_fit(d, _stv_txt(fx_ui("scan", L)), _font(12, False), STV_SIZE - 20), font=_font(12, False), fill=(150, 165, 185))
    return _stv_jpg(im, red)


_stv_plan_before_fx = stv_plan


# wraps: stv_plan
def stv_plan(e, now=None):
    """+ 639u: an active error (bad) every other 20 s instead of the status page; alarm and game stay first"""
    r = _stv_plan_before_fx(e, now)
    try:
        if r[0] in ("gif", "alarm", "game") or FX.get("stv_pause"):
            return r
        now = now or time.time()
        if int(now // 20) % 2 == 1:
            act = fx_active(CFG.get("lang"))
            if act:
                x, en = act[0]
                lang = CFG.get("lang"); red = stv_night()
                key = ("fehler", en["id"], fx_url(en["id"]), red, lang)
                return "fehler", key, lambda: stv_render_fehler(x, en, lang, red), r[3], False
    except Exception:
        pass
    return r


# ---- TV page (/tv/…): a box with the QR code ----------------------------------------------------------------------------
_tv_data_before_fx = tv_data


# wraps: tv_data
def tv_data():
    d = _tv_data_before_fx()
    try:
        act = fx_active(CFG.get("lang"))
        if act:
            x, e = act[0]
            L = _fx_l(CFG.get("lang"))
            u = fx_url(e["id"])
            d["fehler"] = {"id": e["id"], "title": fx_t(e.get("titel"), L), "text": fx_t(e.get("text"), L), "url": u,
                           "qr": qr_svg(u) if u else "", "t_scan": fx_ui("scan", L), "n": len(act)}
    except Exception:
        pass
    return d


# ---- window (Tkinter): «🛠 Hilfe & QR» in the self-check, the dialog with QR and «Jetzt beheben» ----------------------------
def fx_tk_dialog(parent, fid):
    import base64
    e = fx_entry(fid)
    if e is None:
        return None
    L = _fx_l(None)
    w = tk.Toplevel(parent); w.title("MoveEye – " + fx_ui("help", L) + " · " + e["id"]); w.configure(bg=C["panel"])
    try:
        w.transient(parent)
    except tk.TclError:
        pass
    tk.Label(w, text="⚠ " + fx_t(e.get("titel"), L), bg=C["panel"], fg=C["red"] if e.get("stufe") == "bad" else C["yel"],
             font=("DejaVu Sans", 13, "bold"), wraplength=440, justify="left").pack(anchor="w", padx=14, pady=(12, 2))
    tk.Label(w, text=fx_t(e.get("text"), L), bg=C["panel"], fg=C["txt"], wraplength=440, justify="left").pack(anchor="w", padx=14)
    tk.Label(w, text=fx_ui("steps", L), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold")).pack(anchor="w", padx=14, pady=(8, 0))
    tk.Label(w, text="\n".join("%d. %s" % (i + 1, s) for i, s in enumerate(fx_t(e.get("schritte"), L) or [])), bg=C["panel"], fg=C["txt"],
             wraplength=440, justify="left").pack(anchor="w", padx=14)
    u = fx_url(e["id"])
    if u:
        row = tk.Frame(w, bg=C["panel"]); row.pack(fill="x", padx=14, pady=8)
        try:
            img = tk.PhotoImage(data=base64.b64encode(qr_png(u, 4)).decode())
            pic = tk.Label(row, image=img, bg="#ffffff"); pic.image = img; pic.pack(side="left")
        except Exception:
            pass
        tk.Label(row, text=fx_ui("scan", L) + "\n" + u, bg=C["panel"], fg=C["mut"], wraplength=260, justify="left").pack(side="left", padx=10)
    st = tk.Label(w, text="", bg=C["panel"], fg=C["mut"], wraplength=440, justify="left"); st.pack(anchor="w", padx=14)
    bf = tk.Frame(w, bg=C["panel"]); bf.pack(fill="x", padx=14, pady=(6, 12))
    if e.get("aktion") and not CFG.get("lock_on"):          # operator mode (390): nothing is changed from the window
        def go():
            st.configure(text=fx_ui("busy", L)); w.update_idletasks()
            ok, msg = fx_run(e["aktion"], "window")
            FX["cache"] = (0.0, None, None)
            st.configure(text=("✓ " + fx_ui("done", L) if ok else "⚠ " + fx_ui("failed", L)) + ((" – " + tr_err(str(msg), L)) if msg else ""))
        ttk.Button(bf, text="🛠 " + fx_ui("fix_now", L) + ": " + fx_act_name(e["aktion"], L), command=go).pack(side="left", expand=True, fill="x", padx=(0, 4))
    elif not e.get("aktion"):
        tk.Label(w, text=fx_ui("manual", L), bg=C["panel"], fg=C["mut"], wraplength=440, justify="left").pack(anchor="w", padx=14)
    ttk.Button(bf, text=fx_ui("close", L), command=w.destroy).pack(side="left", expand=True, fill="x")
    return w


def _fx_tk_update_health(self):
    """the self-check of the window (as before) + «🛠 Hilfe & QR» under every problem with a catalogue entry"""
    try:
        if not self.h_text.winfo_exists():
            self.h_text = None; return
        h = health_check()
    except tk.TclError:
        self.h_text = None; return
    sig = json.dumps(h["items"], sort_keys=True, default=str)
    if sig == self._h_sig:
        return
    self._h_sig = sig; y = self.h_text.yview()[0]
    tx = self.h_text; tx.config(state="normal"); tx.delete("1.0", "end")
    try:
        tx.tag_configure("fx", foreground=C.get("acc", "#3b8cff"), underline=True, lmargin1=26, lmargin2=26, font=("DejaVu Sans", 9, "bold"))
    except tk.TclError:
        pass
    for x in h["items"]:
        tx.insert("end", "●" if x["level"] != "off" else "○", x["level"])
        tx.insert("end", "  " + x["title"], "t"); tx.insert("end", ("  " + x["text"]) if x["text"] else "", "m")
        if x["tip"] and x["level"] != "ok":
            tx.insert("end", "\n→ " + x["tip"], "tip")
        f = x.get("fehler")
        if f:
            tg = "fx_" + f["id"]
            tx.insert("end", "\n🛠 " + f["help"] + " & QR" + ((" · " + f["fix"]) if f.get("fix") else ""), ("fx", tg))
            tx.tag_bind(tg, "<Button-1>", lambda _ev, i=f["id"]: fx_tk_dialog(self.root, i))
            tx.tag_bind(tg, "<Enter>", lambda _ev: tx.config(cursor="hand2"))
            tx.tag_bind(tg, "<Leave>", lambda _ev: tx.config(cursor="arrow"))
        tx.insert("end", "\n")
    tx.config(state="disabled"); tx.yview_moveto(y)


# wraps: App._update_health
App._update_health = _fx_tk_update_health


# ---- the simulator: the address for its QR codes (127.0.0.1 would not work on the phone) ---------------------------------
_sim_state_639u = sim_state


def sim_state():                                          # + 639u: «help_base» - only the address, never a key (fehler_hilfe.gd)
    d = _sim_state_639u()
    now = time.time()
    hb = FX.get("hb")
    if not hb or now - hb[0] > 30:
        try:
            hb = (now, fx_base())
        except Exception:
            hb = (now, "")
        FX["hb"] = hb
    d["help_base"] = hb[1]
    return d


# ---- self-test ----------------------------------------------------------------------------------------------------------------
def fx_check(base=None):
    """problems of the catalogue (and of the simulator side, when its folder is here) -> (list, numbers)"""
    probs = []
    es = fx_entries()
    acts = FEHLER_KATALOG.get("aktionen") or {}
    if not 20 <= len(es) <= 40:
        probs.append(f"{len(es)} errors (20 - 40 wanted)")
    ids = [e["id"] for e in es]
    if len(set(ids)) != len(ids):
        probs.append("an id twice")
    for e in es:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,31}", e["id"]):
            probs.append(f"{e['id']}: id")
        for k in ("titel", "text", "schritte"):
            v = e.get(k) or {}
            miss = [lg for lg in FX_LANGS if not v.get(lg)]
            if miss:
                probs.append(f"{e['id']}.{k}: no {','.join(miss)}")
        if len({len(v) for v in (e.get("schritte") or {}).values()}) > 1:
            probs.append(f"{e['id']}: not the same number of steps in every language")
        if e.get("aktion") and e["aktion"] not in acts:
            probs.append(f"{e['id']}: unknown action {e['aktion']}")
        if e.get("seite") not in ("mw", "sim", "beide"):
            probs.append(f"{e['id']}: seite")
    for k, v in (FEHLER_KATALOG.get("ui") or {}).items():
        if any(not v.get(lg) for lg in FX_LANGS):
            probs.append(f"ui.{k}: a language is missing")
    for k, v in acts.items():
        if any(not v.get(lg) for lg in FX_LANGS):
            probs.append(f"action {k}: a language is missing")
    n = {"err": len(es), "fix": sum(1 for e in es if e.get("aktion")), "sim": False}
    base = base or os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(base, "simulator3d", "fehler_katalog.json")
    if os.path.exists(p):
        n["sim"] = True
        with open(p, encoding="utf-8") as f:
            if json.load(f) != FEHLER_KATALOG:
                probs.append("simulator3d/fehler_katalog.json differs from the embedded catalogue (werkzeuge/bauen.py)")
        ep = os.path.join(base, "simulator3d", "export_presets.cfg")
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("include_filter=") and "fehler_katalog.json" not in line:
                        probs.append("simulator export_presets.cfg: fehler_katalog.json is not in the .exe")
    return probs, n


def fx_selftest():
    probs, n = fx_check()
    assert not probs, f"{len(probs)} problems: " + " | ".join(probs[:10])
    u = fx_url("CAM_NONE", "http://192.0.2.56:5000")
    assert u == "http://192.0.2.56:5000/hilfe/fehler/CAM_NONE", u
    for k in ("web_password", "notify_url", "hotspot_password", "tv_key"):     # never a secret in the QR text
        v = str(CFG.get(k) or "")
        assert len(v) < 6 or v not in u, k
    assert fx_token("a", "CAM_NONE") != fx_token("b", "CAM_NONE") and fx_token_ok("a", "CAM_NONE", fx_token("a", "CAM_NONE"))
    assert not fx_token_ok("a", "CAM_NONE", "") and not fx_token_ok("a", "DISK_LOW", fx_token("a", "CAM_NONE")), "CSRF key"
    assert fx_for_health({"id": "cam", "level": "bad"})["id"] == "CAM_NONE"
    assert fx_for_health({"id": "cam", "level": "ok"}) is None
    assert fx_for_text("MoveEye: Camera lost", "")["id"] == "CAM_NONE"
    M = qr_matrix(u)
    assert len(M) in (29, 33, 37), "QR size"
    h, code = fx_page("CAM_NONE", "de", None, "owner")
    assert code == 200 and "Kein Kamerabild" in h and "csrf" not in h, "page without owner: no fix form"
    h2, _c = fx_page("CAM_NONE", "fr", "admin", "")
    assert 'name="csrf"' in h2 and "Reconnecter la caméra" in h2, "page of the owner"
    assert fx_page("NOPE", "en")[1] == 404
    return (f"{n['err']} errors, {n['fix']} with «Fix now», 5 languages" + ("" if n["sim"] else " (simulator folder not here)"))


SELFTEST_EXTRA.append(("Error help with QR code (simulator3d/fehler_katalog.json, /hilfe/fehler/<ID>)", fx_selftest))
