# quelle/ – Motion Watch in Teilen

Hier wird Motion Watch bearbeitet. Die Teile werden von `werkzeuge/bauen.py` Byte für Byte zu der einen Datei
`webcam_bewegung_X_Y_Z.py` zusammengesetzt, die der Pi, die Update-Funktion und die Signatur kennen. Die grosse Datei
nie von Hand ändern: GitHub prüft bei jedem Hochladen, dass sie genau zu `quelle/` passt.

Alle Teile zusammen sind **ein** Python-Programm (gemeinsame Namen, keine Importe zwischen den Teilen). Die Reihenfolge
der Nummern ist die Reihenfolge in der Datei – ein Name muss weiter oben stehen als dort, wo er beim Start gebraucht wird.
Die erste Zeile jedes Teils (`#@ …`) ist nur eine Beschreibung und fällt beim Bauen weg.

**Keine Funktion / Klasse zweimal** (ab 2.98.18): definiert ein späterer Teil denselben Namen noch einmal, ersetzt er den
früheren still (so ging 2.98.16 die Lautsprecher-Suche `bt_scan` verloren). `bauen.py` und `bauen.py --pruefen` (GitHub)
brechen dann ab. Erlaubt ist nur ein **gewollter Wrapper**, im späteren Teil markiert mit
`_<name>_base = <name>` über dem neuen `def` oder mit dem Kommentar `# wraps: <name>` auf der Zeile davor. Besser: die
Logik direkt in die ursprüngliche Funktion schreiben (so wurden 2.98.18 apply_settings, health_check, set_cfg,
text_choice_pairs, tools_state / tools_cfg und _tunea_autotune_base zusammengeführt; Gleichheit geprüft mit
`werkzeuge/gleichheit_pruefen.py`). Einstellungs-Listen (TOGGLES, SLIDERS, TEXTS) nicht in späteren Teilen umbauen, sondern
den Eintrag dort ändern, wo er steht.

## Ablauf

```
python3 werkzeuge/bauen.py --neue-version "Was neu ist"            # Nummer +1, Zeile in der Änderungsliste, bauen
python3 werkzeuge/bauen.py --neue-version "Was neu ist" --stufe funktion   # ab 3.0.0: X.Y+1.0 (Regeln: CLAUDE.md «Versionierung»)
python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI               # versions.json signieren + Selbsttest (Schlüssel nie ins Repository)
python3 werkzeuge/bauen.py --pruefen                                # passt die Datei zu quelle/? keine Funktion doppelt?
python3 werkzeuge/web_rauchtest.py                                  # jede Web-Adresse ohne / mit Anmeldung (auch auf GitHub)
python3 pruefstand/pruefstand.py --godot GODOT                      # Erkennung messen (siehe pruefstand/LIESMICH.md)
```

## Die Teile

| Teil | Inhalt | Zeilen |
|---|---|---|
| `000_kopf_aenderungen.py` | Kopf: Beschreibung und die Liste aller Änderungen (neueste oben) | 735 |
| `010_grundlagen.py` | Importe, Version (APP_VERSION), Ordner für Einstellungen | 119 |
| `020_einstellungen.py` | CFG: alle Einstellungen mit Standardwerten | 435 |
| `030_zonen_anwesenheit_zeitplaene.py` | Zonen, Anwesenheit, Text-Einstellungen, Zeitpläne | 817 |
| `040_speichern_passwort.py` | Einstellungen speichern, Web-Passwort | 443 |
| `041_benutzer_zugang.py` | Benutzer: Zeitfenster / Ablaufdatum, Handy verknüpfen (QR-Einmal-Link /l/), Geräte und Push pro Benutzer | 380 |
| `050_meldungen_push.py` | Meldungen (ntfy, Telegram, Webhook), Web-Push | 289 |
| `060_sicherung_schutz_klima.py` | Sicherung, Diebstahlschutz, Linse, Klima, Wetter, Postausgang, Notifier | 1224 |
| `066_alarm_extras.py` | Alarm-Extras: Knöpfe in der Push-Nachricht (/na/), Akku-Prognose, Morgen-Bildstreifen, «Was war das?», doppelte Bestätigung, Ansage beim Einschalten, «Bist du's?» | 724 |
| `067_speicherkarte.py` | Speicherkarte schonen: Schreibmenge pro Tag, Dateisystem-Fehler, Schreibschutz (Overlay) | 267 |
| `068_pruefstand_pushes.py` | Prüfstand: die letzten Push-Nachrichten für den Simulator (echte Pushes zählen statt Flackern) | 17 |
| `070_hardware_servos_licht.py` | Servos, PCA9685, Mover, Licht, Disco-Licht | 398 |
| `072_servo_planer.py` | Ein Bewegungsplaner für die Servos (Rampen, beide Achsen gemeinsam), Not-Aus / Freigeben, Störung, Unterspannung, Watchdog, Grenzen, wer steuert | 595 |
| `074_servo_diagnose.py` | Servo-Diagnose: Fehlerspeicher, Betriebsstunden, Grad und Bewegungen pro Achse, Wartungshinweise, Export | 260 |
| `076_teach_punkte.py` | Teach-in: benannte Positionen (= Wegpunkte), genau anfahren, ordnen, Park- / Grundstellung | 205 |
| `080_waermebild_modul.py` | Treiber Wärmebild-Modul, Klasse Hardware | 281 |
| `090_system_fern_sichtungen.py` | System, Fernzugriff, Sichtungen, Nachtbericht, Gast-Zugang | 465 |
| `100_akku.py` | Akku / USV, Systemüberwachung | 417 |
| `105_akku_sparen.py` | Akku-Sparen automatisch (unter einer Schwelle weniger Bilder, die KI seltener) | 116 |
| `110_netz_wlan.py` | Netz, WLAN suchen und verbinden, QR-Codes | 813 |
| `120_eigenes_wlan_uhr_ort.py` | eigenes WLAN, Uhr vom Handy, Ort (GPS) vom Handy | 720 |
| `130_scharf_profile_modi.py` | Scharf / unscharf, Camping-Profil, einfache Einstellungen, Modi | 368 |
| `131_konzept_modi.py` | Modi und Profile zusammengeführt: alte Einstellungen beim Laden übernehmen (2.98.14) | 66 |
| `140_autostart.py` | Autostart | 422 |
| `145_selbstheilung.py` | Selbstheilung: Wächter für Kamera-Schleife, KI, Webseite (Neustart mit Bremse); Ampeln Speicherkarte / Selbstheilung | 303 |
| `147_simsperre.py` | Eine Sperre für Simulator-Aufgaben mit dem Simulator; blinde Flecken aus dem Simulator | 118 |
| `148_fehlalarm_pruefen.py` | Fehlalarme aus den Spielen prüfen (richtiges Bild, Wahrheit vom Simulator, Grösse), fa_learn/zweifel/, «Lernbilder prüfen» | 250 |
| `150_zweites_wlan_tv_netzcheck.py` | zweites WLAN, USB-Tethering, TV-Anzeige, Netz-Check, WLAN-Wächter | 1059 |
| `160_netzautomatik_patrouille.py` | Netz-Automatik, Patrouille | 160 |
| `162_kopf_auto.py` | Automatische Kopfbewegung: ein Koordinator (Hand > Alarm/Folgen > Gehtest > Wertsachen-Blick > Runde > Parken, Simulator-Sperre), kluge Runde (place_items / Wegpunkte), zum Alarm drehen (Bildrand, Wärmefleck, Geräusch mit Zugang, Übersichtskamera), Parken bei «Aus», Wertsachen-Blick, sparsam (Akku / tiefe Nacht), Wildtier-Modus, Sabotage umschauen, 180/270/360°- und Endlos-Servos | 834 |
| `163_weitwinkel.py` | Weitwinkel-Kamera des Simulators (sim:1, 3D-4.17): Montage aus /info und der Antwort auf /state, «Übersicht lenkt den Kopf» von selbst (nur bei Montage-Wechsel, Hand bleibt), Kopf-Montage = Richtung Kopf + Versatz, Eigenbewegung der Kopf-Kamera ausblenden (440), IR-Licht breit auf PCA9685 Kanal 4 | 196 |
| `163a_status_led.py` | Status-LED (RGB auf PCA9685 Kanal 5/6/7) oben auf dem Kopf: Farbe pro Zustand, Alarm blinkt rot bis quittiert, Störung violett, Erkennung kurz, Blinki-Zwinkern, Nacht gedimmt; zwei Tasten am Gerät (GPIO 16 / 26, entprellt, kurz / lang; dürfen alles, einzeln abschaltbar, Push bei Ausschalten / Sirene-Stopp am Gerät); im Simulator dessen LED und Tasten | 572 |
| `170_ki_personen.py` | KI-Modell laden und herunterladen | 110 |
| `180_ki_tierarten_helfer_tunnel.py` | Tierarten, Alarm-Rückblick, KI-Rechenhilfe, KI-Prüfung, Tunnel, AIDetector | 841 |
| `190_relais_wetter_tracker.py` | Relais, Wetter-Analyse, Auto-Tuner, Tracker | 422 |
| `195_ki_eigenes_modell.py` | Eigenes KI-Modell (YOLO als ONNX): laden, herunterladen (sha256), Ausgabe entschlüsseln, Selbsttest | 321 |
| `196_ki_modell_auto.py` | Eigenes KI-Modell von selbst aktualisieren: täglich prüfen, nur übernehmen, wenn die Auswertung nicht schlechter ist | 125 |
| `197_ki_daten.py` | KI-Daten aufräumen: Trainingspaket mit «Vielfalt», Liste der Pakete auf dem Simulator-PC, «Alte KI-Daten löschen» (Web und Fenster) | 100 |
| `200_erkennung_videoquellen.py` | Video-Quellen (USB, Pi-Kamera, Netz) | 166 |
| `210_demo.py` | Demo-Modus | 255 |
| `220_zeitraffer.py` | Zeitraffer | 195 |
| `230_waermebild.py` | Wärmebild-Überlagerung, Nachtsicht, Easter Egg (Herz) | 349 |
| `232_waermebild_person.py` | Personen im Wärmebild (nachts, wenn die Kamera nichts sieht); Fusspunkt-Prüfung: Reh / Fuchs frontal = Tier statt Person | 200 |
| `240_audio.py` | Mikrofon, Geräusch-Alarm | 81 |
| `250_klatschen_bluetooth_ton.py` | Klatschschalter, Bluetooth, Lautsprecher, Sprachausgabe | 1131 |
| `255_wecker.py` | Wecker mit Schlafplatz: wegschauen, wecken, Gesten (winken / aufstehen) | 330 |
| `258_entwickler.py` | Entwickler-Bereich: eigene Verbindungen, erreichte Namen, Datenmenge (nur lesen, PIN) | 330 |
| `260_mehrere_geraete.py` | mehrere Motion-Watch-Geräte | 164 |
| `270_mqtt.py` | MQTT / Home Assistant | 250 |
| `280_sms_sensoren_sturm_gps_solar.py` | SMS, Sensoren, Sturmwarnung, GPS, Solar | 870 |
| `285_simwerte.py` | Simulator-Werte: Akku (simulierter USV-HAT), Uhrzeit (sim_now), Ort, Wetter, Pi-Wärme, «WLAN weg»-Test aus dem 3D-Simulator | 230 |
| `290_simulator_verbindung.py` | Verbindung zum Simulator | 333 |
| `292_simulator_sprache.py` | Sprache von MoveEye an den 3D-Simulator (Zustandsfeld «lang», i18n.gd) | 8 |
| `300_werkzeuge_simulator3d.py` | Werkzeuge, 3D-Simulator für Windows und den Pi, Simulator-Suche | 1155 |
| `310_testlaeufe.py` | Testläufe mit Auswertung und Optimierung | 485 |
| `312_erkennung_assistent.py` | Assistent «Erkennung verbessern» (ein Ablauf statt sechs Funktionen), Pause des Auto-Tuners | 307 |
| `315_referenz_scan.py` | Referenz-Scan: Raster abfahren, Referenz-Fotos, Vergleich, Bericht (2.95.97) | 347 |
| `317_platz.py` | «Platz einrichten»: Rundblick mit Beobachtung, Vorschläge, Zonen / Masken / Wegpunkte / bewachte Sachen aus dem Panorama, Platz-Datensatz `place_items()` / `place_info()`, öffentlicher Weg und Zelt im Alarm | 750 |
| `318_blickwinkel.py` | «Blickwinkel der Kamera» pro Kamera (Modell-Liste, eigener Wert, picamera2 / Simulator), `cam_fov_h(spec)`, Zusatzkameras nach dem Start | 230 |
| `320_spielecke.py` | Extras: Spielecke und Spieleabend | 743 |
| `330_usb_geraete.py` | USB-Geräte, Spielesammlung, Seite verlassen (✕ Zurück) | 172 |
| `343_spiel_vergleich_online.py` | Spiel «Mensch gegen KI» (Start / Stand über /api/game_compare, Simulator gamecompare.gd) und «Online über das WLAN hinaus»: Einladungslink mit Ablauf, Proxy /game/<token>/ (nur das Spiel des Simulators, Seite + WebSocket, auch durch den Tunnel), Ratenbremse, Spielerzahl, Protokoll, /api/game_invite | 420 |
| `340_spiele_seiten.py` | Extras: Seiten der Spielecke und des Spieleabends | 655 |
| `350_simulator_link.py` | Verbindung zum Simulator (Schleife) | 87 |
| `360_daten_simulator_python.py` | Daten: der Python-Simulator als ZIP | 897 |
| `370_rueckmeldung_teilen_abschreckung.py` | Rückmeldung, Teilen, Abschreckung, Gegensprechen | 405 |
| `375_gesichter_verpixeln.py` | Gesichter verpixeln beim Teilen (nur die geteilte Kopie) | 250 |
| `380_updates.py` | Updates | 216 |
| `390_protokoll_bedienermodus.py` | Protokoll, Bedienermodus, Pause, Update-Wächter | 1065 |
| `395_code_pflege.py` | Code-Pflege im Selbsttest: fehlende Übersetzungen fr / it / rm (nur Warnung), MIGRATE_ONLY (alte Schlüssel nur zum Übernehmen), SELFTEST_EXTRA | 85 |
| `396_kopf_abschrecken_zielen.py` | Abschrecken mit Ziel: Licht / Sirene drehen zur Person (zuletzt gesehen) oder zum Zelt aus «Platz einrichten», über den Kopf-Koordinator 162 (Schalter kopf_deter_aim) | 125 |
| `400_ausschalten.py` | Pi ausschalten / neu starten | 53 |
| `410_motionwatch_kern.py` | KERN: die Erkennungs-Schleife (Bewegung, Personen, Alarm) | 969 |
| `415_entfernung_gehtest.py` | Entfernung und Richtung einer Person, Gehtest beim Einrichten | 376 |
| `416_verfolgung_parcours.py` | Verfolgungs-Parcours des Simulators (3D-4.18): Lektionen starten (Steuerbefehl `parcours`), Läufe mit den Werten der Verfolgung speichern (`parcours_runs.json`), A/B-Vergleich, Auto-Tuning (nur Vorschlag, «übernehmen»), mit / ohne Weitwinkel-Übergabe, Spiel «Entkomme der Kamera»; neuer Regler `track_lead` (Vorausschauen, 0 = wie bisher) als Wrapper um `MotionWatch.track`; Kachel 🎯 (139, Gruppe «Testen»); eine Sperre (147) | 600 |
| `418_feste_fehlperson.py` | Feste Fehl-Personen lernen (Personen-Kasten der KI, der sich über Minuten nicht bewegt und nie hingegangen ist = Gegenstand; kein Push, Kopf folgt nicht; Karte «ignorieren?» mit Bild → Maske, /api/fixp), Tier vor Person (Spur behält die Tier-Klasse), Veto Tier / Fahrzeug für «Person?» und Wärmebild-Person (232), Selbsttest | 470 |
| `420_webzugang_aufnahmen.py` | Web-Zugang, Aufnahmen, Speicher, Bild für andere Programme | 630 |
| `425_zeitleiste.py` | Zeitleiste der Nacht: Daten für /api/timeline | 230 |
| `426_wochenbericht.py` | Wochenbericht der Erkennung (Push + Karte) | 200 |
| `430_pdf_bericht.py` | PDF-Bericht | 757 |
| `440_zusatzkameras.py` | zusätzliche Kameras | 203 |
| `450_web_gemeinsam.py` | Web: gemeinsames Aussehen (CSS), Bluetooth-Teil | 240 |
| `460_web_werkzeugseite.py` | Web: Seite Werkzeuge | 875 |
| `470_web_simulatorseite.py` | Web: Seite Simulator | 1339 |
| `480_daten_app_symbole.py` | Daten: App-Symbole (PNG) | 4376 |
| `490_daten_simulator_symbole.py` | Daten: Symbole der Simulatoren | 99 |
| `500_web_seitenbau.py` | Web: App-Symbol, Seiten zusammensetzen | 80 |
| `510_web_kopf_alarm.py` | Web: Service Worker, Kopf, Alarm, gemeinsames JavaScript | 494 |
| `520_web_seiten_kameras_zonen_tagebuch.py` | Web: Kameras, Zonen, Tagebuch, Gast, Protokoll | 730 |
| `523_web_zeitleiste.py` | Web: Seite «Zeitleiste» (Verlauf), /api/timeline, /api/weekreport | 330 |
| `516_web_guide2.py` | Web: Guide 2 – Einrichtung schnell / ausgiebig, Rundgänge mit Sprechblasen, Einfach/Experte pro Seite, «Tipps & Tricks», «?» bei Einstellungen, Tipp des Tages, Werkseinstellungen (/g2/ui.js) | 560 |
| `585_fenster_guide2.py` | Fenster: Guide 2 – Einrichtung, Rundgang pro Reiter (Rahmen + Textfeld), «?» bei Einstellungen, Tipp des Tages, Werkseinstellungen | 420 |
| `586_guide2.py` | Guide 2: Zustand der Einrichtung (CFG guide2), Schritte und Hardware, Einfach/Experte pro Seite, Hilfetexte, Tipp des Tages, «Auf Werkseinstellungen zurücksetzen» (Kopie, was bleibt / gelöscht wird) | 480 |
| `631_uebersetzungen_spielB.py` | Übersetzungen und Anleitungs-Zeilen (Kapitel «Spiele freigeben») zu 343 / 543 / 592 | 120 |
| `633_uebersetzungen_guide2.py` | Übersetzungen und Anleitungs-Kapitel «Einrichtung, Rundgänge und Tipps» zu Guide 2 | 330 |
| `589_blinki.py` | «Blinki», die Figur aus dem Logo für Einrichtung und Rundgänge: SVG + CSS + Skript vor /g2/ui.js (Web), kleines Bild mit cv2 (Fenster), Schalter «blinki_on» | 260 |
| `591_web_weitwinkel.py` | Weitwinkel-Bild als Kachel 🔭 (Simulator-Zentrale 139 und Sim-Kompakt 549, über /cam_feed, antippen = gross), Montage wählen, Schalter «IR-Licht breit (Kanal 4)», Zustand an den Simulator (lights.ir_wide), Selbsttest zu 163 | 167 |
| `593_fenster_aufraeumen.py` | Fenster: Gruppe «Tierart» in der KI-Erkennung (wie «KI-Modell») | 37 |
| `635_uebersetzungen_blinki.py` | Übersetzungen und Anleitungs-Zeile zu Blinki | 60 |
| `635a_spieltest.py` | Spieltest-Meldungen: der Spieltest-Assistent des 3D-Simulators (spieltest.gd, world_reply «spieltest») meldet jede Runde kurz, MoveEye schickt sie über den Hauptkanal des Push – nur mit dem Schalter «Spieltest-Meldungen» (Entwickler, Standard aus); Zustand «spieltest» zurück, mw_cmd «spieltest_push», Selbsttest | 140 |
| `594_uebersetzungen_kihilfe.py` | Übersetzungen für die «KI-Hilfe» am Auslöser (542) | 25 |
| `595_fenster_simstopp.py` | Fenster: «⏹ Stopp» (Not-Aus) in der Simulation ausblenden | 75 |
| `596_uebersetzungen_vier.py` | Übersetzungen für «MoveEye als KI-Wächter» (548) | 32 |
| `597_uebersetzungen_simkompakt.py` | Übersetzungen für «Sim-Kompakt» (549) | 67 |
| `551_uebersetzungen_szenen.py` | Namen der Simulator-Szenen in FR / IT / RM / EN (der Simulator schickt «en» mit; 139 / 470 / 549 zeigen sie) und Anleitungs-Absatz zu den neuen Szenen (Erkennung) | 50 |
| `568_uebersetzungen_weit.py` | Übersetzungen und Anleitungs-Absatz (Kamera & Servos) zur Weitwinkel-Kamera (163 / 591) | 50 |
| `598_simwerte_anzeige.py` | «🧪 Simulator»-Hinweis bei Simulator-Werten (Web und Fenster), Anleitung (285) | 175 |
| `599_uebersetzungen_simwerte.py` | Übersetzungen der Simulator-Werte (285, 598) | 55 |
| `599b_fenster_smalltv.py` | Zusatz-Bildschirm (552): Einstellungen (Abschnitt «Extra display» in «Geräte & Sensoren»), Fenster-Abschnitt (Liste, Testbild, Suche, Einrichtung mit QR), deutsche Texte der Webseite, Selbsttest mit nachgebautem Gerät (HTTP 400, langsam) | 300 |
| `599c_fenster_led.py` | Status-LED und Tasten (163a): Einstellungen (Abschnitt «Status LED» in «Licht & Ton»), /api/led, Blinki in der Kopfzeile zwinkert mit der LED, Fenster-Abschnitt, Simulator (state «led», world_reply «buttons»), Anleitung, Selbsttest | 640 |
| `599a_fenster_parcours.py` | Fenster: Regler «Vorausschauen» bei Kamera / Servos (SLIDERS), Karte «Verfolgungs-Parcours» im Reiter Simulator (letzter Lauf, Start, Vorschlag übernehmen, Kachel im Browser) | 70 |
| `598_uebersetzungen_weit.py` | Übersetzungen und Anleitungs-Absatz (Kamera & Servos) zur Weitwinkel-Kamera (163 / 591) | 50 |
| `634_uebersetzungen_ausl.py` | Übersetzungen für den «Auslöser» (539) | 40 |
| `637_uebersetzungen_servo.py` | Übersetzungen Servo-Bewegung, Not-Aus, Teach-in, Diagnose | 156 |
| `623_uebersetzungen_pad2.py` | Übersetzungen des Controller-Konzepts (542, 538, 470) | 75 |
| `632_uebersetzungen_aufr.py` | Übersetzungen der Aufräum-Runde (Servos an einem Ort, Kurzbefehl-Schlüssel = App-Schlüssel, Zonen «nur melden» / «bleibt am Platz», Tierart) + Selbsttest | 150 |
| `639_uebersetzungen_falearn.py` | Übersetzungen «Lernbilder prüfen» | 13 |
| `531a_web_push_karten.py` | Web: «Push-Nachrichten» als Karten (Kopf · Wohin · Was · Wann · Erweitert), SMS und Nachrichtentexte hinein, Alarmton in die Glocke | 268 |
| `571a_fenster_push.py` | Fenster: «Push-Nachrichten» gleich aufgebaut wie im Web (Kanal-Karten, Stufen, Ruhezeiten, Erweitert) | 453 |
| `579a_push_logik.py` | Push-Logik: Kanäle (Hauptkanal ntfy/Telegram/Webhook), Stufen Nur Personen / + Tiere / Alles, Ruhezeiten (Simulator-Uhr), Bilder mit/klein/ohne, Übernahme alter Einstellungen, /api/push, Selbsttest | 577 |
| `579b_nacht_testlauf.py` | Nacht-Testlauf mit dem 3D-Simulator (Steuerbefehl `nacht`, nachtlauf.gd): Optionen, Schutz «Voll» nur in der Simulation (danach zurück, auch nach Neustart), Test-Postfach erzwungen, Relais aus; Alarme (Wrapper um Notifier.person / prealarm), Erkennungen, Akku / Pi-Temperatur / Bilder/s, Bilder; Abgleich `nacht_match` (Zeitfenster + Art, Sichtbarkeit) → Vorfall erkannt + Sekunden, Fehlalarme nach Ursache, Verpasstes; Bericht als Push (🧪), Verlauf der letzten 10 Läufe, JSON-Export; nur Besitzer (nicht im Bedienermodus); Zeitplan; Kachel 🌙 (139), Seite /nacht, /api/nacht; eine Sperre (147); Selbsttest | 900 |
| `599d_fenster_nacht.py` | Fenster: Karte «Nacht-Testlauf» im Reiter Simulator (Stand, letzter Bericht, Start / Abbrechen nur Besitzer, Bericht im Browser) | 60 |
| `599e_uebersetzungen_nacht.py` | Übersetzungen (DE/FR/IT/RM) und Anleitungs-Absatz (Erkennung, DE/EN) zum Nacht-Testlauf | 120 |
| `639a_uebersetzungen_push.py` | Übersetzungen und «?»-Texte der Push-Karten | 205 |
| `639b_uebersetzungen_menu.py` | Übersetzungen der Menü-Struktur 2: kurze Beschriftungen (die lange im «?»), neue Gruppen | 401 |
| `639c_menu_struktur.py` | Menü-Struktur 2: Gruppen Web = Fenster, Entwickler-Gruppe, Einfach mit «Feineinstellungen», Abschreckungs-Tabelle | 339 |
| `639d_angleichen.py` | Angleichen MoveEye ↔ Simulator: Entwickler-Schalter an den Simulator (dev_area), Fenster «Strom» und Teil «System» (Ausschalten / Neustart / Pause) | 75 |
| `639e_uebersetzungen_angl.py` | Übersetzungen zu 639d (Störungen-Link, Foto des Platzes) | 13 |
| `639f_uebersetzungen_led.py` | Übersetzungen der Status-LED und Tasten (163a / 599c), Platz im Fenster (Gruppe «Licht & Ton») | 136 |
| `639h_basis_simulator.py` | «MoveEye Sim · Basis» (alter Python-Simulator) nur mit Schalter «Basis-Simulator anzeigen» (Simulator, Experte, Standard aus): Download und Pi-Knöpfe (auch /api/sim gesperrt), Übersetzungen | 41 |
| `639g_uebersetzungen_entdecken.py` | Übersetzungen der Kachel «Entdeckungen» (Entdeckungsbuch des Simulators, 139) | 29 |
| `639i_spielbereich.py` | «Spielen» (Mehr → Spielen, Web /play, Fenster-Knopf unter Mehr): Kopfzeile (Stufe, Spielstand), Weiterspielen-Hinweis, Regal «Geschichten» (nur anschauen, Bild /sim/story_pic), «Entdecken», Blinki – Daten vom Simulator (spielbereich.gd / geschichten.gd); Abzeichen im Entdeckungsbuch (139) | 541 |
| `639j_nurgruppen.py` | «Beim Start: Nur Gruppen» (Schalter `ui_start_groups`, ab Werk ein; Logik in 530 / 470 / 570 / 550): Übersetzungen DE/FR/IT/RM, Anleitungs-Absatz (Tipps, DE/EN) | 35 |
| `639k_uebersetzungen_fehlperson.py` | Übersetzungen, Karte «Hier steht etwas, das wie eine Person aussieht – ignorieren?» auf der Hauptseite, Anleitungs-Absatz (Erkennung) zu 418 | 60 |
| `636_werkseinstellungen_stand.py` | Standardwerte aller Teile vor dem Laden der Einstellungen (für die Werkseinstellungen) | 4 |
| `525_web_mehr_seite.py` | Web: Seite «Mehr» (6. Reiter) und `main_tab_page()` für Live / Schutz / Einstellungen | 70 |
| `530_web_hauptseite.py` | Web: Hauptseite | 4459 |
| `535_web_erkennung.py` | Web: Gehtest (Live, Schutz), Akku-Sparen auf der Schutz-Seite | 119 |
| `536_web_live_ansicht.py` | Web: Live-Seite nach Format (Hoch / Quer / nur Bild), «Ansicht» (Vorlagen, Bildgrösse, Lieblingsknöpfe, Karten, Bearbeiten), Joystick nur mit Kopf (`live_has_head`) | 488 |
| `537_web_platz.py` | Web: Seite «Platz einrichten» (/place), Karte auf der Schutz-Seite, Angebot nach dem Hinstellen, Blickwinkel in Kamera / Servos | 420 |
| `541_web_servo.py` | Web: Seite «Servos» (/servo, /api/servo): Not-Aus / Freigeben, wer steuert, Teach-in, Diagnose mit Export; Not-Aus auf der Live-Seite | 368 |
| `538_web_controller_ansicht.py` | Web: «Controller-Ansicht» der Live-Seite für Handy / Tablet (Live- + Simulator-Bild, Game-Controller, Gesten, schmale Leiste) | 383 |
| `539_web_ausloeser.py` | «Auslöser»: ein Mensch steuert die Kamera – Fadenkreuz und runder 🎯-Knopf im Live-Bild, R2, Treffer als Alarm ins Test-Postfach | 170 |
| `539a_sim_horror.py` | Bergtal · Horror-Modus des 3D-Simulators: seine «Aufnahmen» (Bild + Text) als Test-Einträge in den Verlauf → Nachrichten | 50 |
| `542_web_padmap.py` | EIN Controller-Konzept (MWPad): Belegung für Controller-Ansicht, Simulator-Seite, Handy-Spiel und 3D-Simulator (gleicher Text wie simulator3d/scripts/padmap.gd, Selbsttest vergleicht), Vibration, Hilfe, Fadenkreuz, Mini-Karte | 230 |
| `546_web_ki_hilfe.py` | «KI-Hilfe» am Auslöser (KI-Rahmen, KI zielt, KI-Autopilot): Knopf und Erkennungsrahmen im Live-Bild, Kopf folgt in «Team gegen MoveEye», /api/sim kihilfe, Runde «mit KI-Hilfe» | 230 |
| `543_web_spiel_waechter.py` | Spiel des Simulators: Wächter-Werkzeuge der Wächter an MoveEye («Team gegen MoveEye») – Energie, Licht, Sirene, Scan, Zoom, Hinweis-Marken im Live-Bild | 75 |
| `540_web_anleitung_aufnahmen.py` | Web: Anleitung, Aufnahmen | 1187 |
| `544_web_spiel_online.py` | Web: Seite Simulator, Karte «Spiel» – «Mensch gegen KI» (beide Runden, Ergebnis) und «Online-Einladung» (QR-Code, Zurückziehen, Protokoll) | 110 |
| `545_simulator_updates.py` | Simulator-Updates: ein Besitzer («Neue Versionen» im Simulator) | 72 |
| `547_web_benutzer.py` | Web: Karte «Benutzer» (Rollen Kind / Freund / Familie / Eigene Rechte, Handy verknüpfen, Zugangszeit, Push) | 130 |
| `548_web_ki_waechter.py` | Web: «🤖 MoveEye als KI-Wächter» in der Karte «Spiel» (Schalter, Liste «gegen die KI»), Simulator-Fenster ohne Einblendungen | 80 |
| `549_web_sim_kompakt.py` | Live-Seite «Sim-Kompakt»: mit verbundenem Simulator zwei kleine Bilder, Kopf- und Rover-Stick am Rand, Simulator-Kacheln dazwischen («◫ Ansicht», pro Gerät) | 429 |
| `550_web_server.py` | Web: der Server (alle Adressen) | 2562 |
| `552_smalltv.py` | Zusatz-Bildschirm GeekMagic SmallTV Ultra: Liste der Bildschirme (+ virtueller 🧪 des Simulators), Status / Alarmbild (Tier mit Ausschnitt, Person nur Symbol; Alarm-GIF auf jedem Bildschirm) / Spiel-Anzeige (`game_live` des Simulators), nachts gedimmt und rot, ein Faden pro Gerät, nur bei Änderung, me_a/me_b.jpg, Firmware-Macken (400), Suche im /24, /api/smalltv, Web-Teil (stvPanel); Wrapper um species_update, alarm_ctx_note, simvals_take, msglog_add | 900 |
| `553_smalltv_wechsel.py` | SmallTV «Live-Bild und Wechsel» (Schalter `rot` pro Bildschirm): tagsüber alle 30 s Live-Bild (reines Kamerabild ohne OSD, 410 `frame_clean`; neu nur jede zweite Live-Zeitscheibe = alle 2 min; Personen verpixelt) ↔ «Akku und Strom», Alarm als animiertes GIF (me_a/me_b.gif) 60 s, dann Standbild 5 min, nachts nur Status; «ca. N Bilder/Tag» (stv_per_day); Wrapper um stv_tick, stv_state | 330 |
| `558_schnittstelle.py` | Aufräumen 2: Prüfung der einen Feldliste MoveEye ↔ 3D-Simulator (`simulator3d/schnittstelle.json`: world_reply, state, info, control) im Selbsttest – liest die GDScript-Quellen und `sim_state`, meldet unbenutzte / fehlende Felder | 150 |
| `558p_sim_mikrofon.py` | Mithören im 3D-Simulator (Paket real-pir-ton): aus dem Feld «mic» (Pegel, Hintergrund, lauteste Quellen) ein Geräusch in derselben Lautstärke für «🎧 Mithören» (sim_mic_pcm, von 250 feed_sim), Selbsttest | 75 |
| `559_nachspielen_3d.py` | Aufräumen 2: «⏪ In 3D nachspielen» (Alarm-Spur 180) auch in Zeitleiste und Aufnahmen, ein Knopf-Aussehen (`mwR3d`, Klasse r3d); Wrapper um timeline_build, list_recordings | 110 |
| `564_uebersetzungen_aufr2.py` | Übersetzungen und Anleitungs-Absatz (System & Netz) zum Aufräumen 2 | 50 |
| `565_uebungen_sim.py` | Aufräumen 2: Übungen «Akku leer» / «WLAN / Internet weg» (141) stellen bei verbundenem Simulator nur dessen Regler (ein Weg), sonst eigene Werte; Wrapper um drill_start, drill_battery_tick, _drill_end_later | 100 |
| `556_tailscale_funnel.py` | Online-Spiel über Tailscale Funnel: nur /game/ öffentlich (eigene Tür + Sperre bei Funnel-Anfragen), Auto-Aus, Aufräumen beim Neustart, Fehler mit Abhilfe, Fenster-Zeile | 605 |
| `554_sim_lautsprecher.py` | Lautsprecher im Simulator: Sirene, Wecker-Melodie, Ansage gehen auch im Test-Postfach-Betrieb (Spiel, Übung, Testlauf) an den 3D-Simulator, der echte Lautsprecher bleibt still (sim_speaker, sim_speaker_only, sim_sound_play); eigener Ton zählt nicht für Klatschschalter / Gesundheit (own_sound_now); Wrapper um sim_state, soundev_state; Texte in 557 | 140 |
| `555_sim_servo_stoerungen.py` | Servo-Störungen aus dem Simulator («servo_sim»): Unterspannung der 5-V-Schiene (SRV sim_uv → Sperre wie echt), PCA9685-Reset (nach dem 10-s-Check, Freigeben → Treiber neu, «reinit»), I2C-Fehler (servo_io_error), blockierter Servo (Kopf head_deg folgt nicht → Störung «blocked»); Wrapper um simvals_take, servo_release, sim_state | 190 |
| `557_waermebild_ausrichten.py` | Assistent «Wärmebild ausrichten (warme Hand)» (/thermal_align, /api/thermal_align, Fenster): Paare Bewegung im Kamerabild ↔ warmer, bewegter Fleck im Wärmebild, Verzögerung gesucht, Gerade → thermal_zoom / dx / dy, Rückgängig; Wärmebild-Modell des Simulators (thermal_model → SIM info), Knopf in Werkzeuge; alle Texte von 554 / 555 / 557 (DE nach Teil 560 über load_settings / self_test), Anleitung DE/EN; Wrapper um simvals_take, ThermalCam.wanted, servo_routes, load_settings, self_test | 800 |
| `560_uebersetzungen_de.py` | Übersetzungen Deutsch | 498 |
| `562_uebersetzungen_smalltv.py` | Übersetzungen und Anleitungs-Kapitel «Zusatz-Bildschirm (SmallTV)» zu 552 / 599b | 150 |
| `563_uebersetzungen_smalltv2.py` | Übersetzungen zu 553 (Live-Bild und Wechsel, Akku und Strom, Alarm-Animation) | 30 |
| `561_uebersetzungen_funnel.py` | Übersetzungen und Anleitung (DE/EN) zum Tailscale Funnel (556) | 128 |
| `569_uebersetzungen_parcours.py` | Übersetzungen und Anleitungs-Absatz (Kamera & Servos) zum Verfolgungs-Parcours (416 / 599) | 140 |
| `570_fenster.py` | Fenster auf dem Pi / PC (Tkinter) | 3322 |
| `576_fenster_zeitleiste.py` | Fenster: Zeitleiste als Liste, Wochenbericht | 130 |
| `577_nachlauf_konzept.py` | Nachlauf Konzept-Check: ein Wochenbericht, Rückkehr des Handys (ausschalten / fragen / nichts), Akku-Schwellen zusammen, Auto-Tuner ±20 %, Übernahme alter Einstellungen | 201 |
| `578_sicher.py` | «Sicher»: «Aus» in der Push nur mit PIN, Push nach Stromausfall, Fehlerseiten in der eigenen Sprache, Dunkle Ansicht, Namen für Bildschirmleser, Aufnahmen nach N Tagen löschen / «Ferien vorbei», Push ohne Bild | 743 |
| `579_ki_modell_auto_schalter.py` | Schalter «Eigenes Modell von selbst aktualisieren» (Web und Fenster) | 4 |
| `571_alarm_einstellungen.py` | Schalter und Regler der Alarm-Extras (Web und Fenster) | 16 |
| `573_app_schluessel.py` | «App-Schlüssel» für andere Programme (nur als Hash gespeichert, auch über http, nie Sicherheits-Funktionen) und «Sicherheit an einem Ort» (Passwort, Benutzer, App-Schlüssel, Sicherheits-Check unter Einstellungen → Sicherheit; Web und Fenster) | 380 |
| `574_anmelden_verschluesselt.py` | «Anmelden nur verschlüsselt»: das Web-Passwort nur über https, vom Gerät selbst oder Tailscale; Hinweis-Seite, Rückfall ohne https (Web und Fenster) | 235 |
| `583_kopf_auto_einstellungen.py` | Einstellungen «Automatische Kopfbewegung» (Web und Fenster), Servo-Art, Übersichtskamera, Selbsttest | 92 |
| `588_fenster_servo.py` | Einstellungen «Servo-Bewegung & Sicherheit», Fenster «Servos» (Not-Aus, Teach-in, Diagnose), Not-Aus in der Kamerasteuerung | 296 |
| `584_info_rueckmeldung.py` | Rückmeldung von überall (💬 auf jeder Seite /fbx/ui.js, Fenster, 3D-Simulator; Art, Sterne, Bildschirmfoto, wartende Nachrichten, Test-Feedback) und «Über MoveEye» (Geschichte, Zeitleiste, Zahlen) | 420 |
| `622_uebersetzungen_info.py` | Übersetzungen und Anleitung (fr / it / rm) zu 584 | 110 |
| `587_qr_codes.py` | QR-Codes neben Links (qrBtn / qrShow für alle Seiten, POST /api/qr), «QR-Codes» unter Mehr (/qr), Druckseite A4, Fenster-Dialog und -Galerie | 628 |
| `580_uebersetzungen_fr.py` | Übersetzungen Französisch | 1396 |
| `581_fenster_ansicht.py` | Fenster: «Ansicht» des Reiters Live wie im Web (Vorlagen, Anordnung, Bildgrösse, Grösse, Lieblingsknöpfe + «mehr», Karten, Joystick; «Für alle Geräte») | 355 |
| `582_fenster_platz.py` | Fenster: «Platz einrichten» und «Blickwinkel der Kamera» | 300 |
| `590_uebersetzungen_it.py` | Übersetzungen Italienisch | 1392 |
| `592_fenster_spiel_online.py` | Fenster: Reiter Simulator – Karte «Mensch gegen KI · Online-Einladung» (wie 543) | 130 |
| `600_uebersetzungen_rm.py` | Übersetzungen Rätoromanisch, Anleitungen | 1763 |
| `602_uebersetzungen_alarm.py` | Übersetzungen der Alarm-Extras | 130 |
| `603_uebersetzungen_nachlauf.py` | Übersetzungen zum Nachlauf des Konzept-Checks (577) | 27 |
| `607_uebersetzungen_modell.py` | Übersetzungen «Eigenes KI-Modell» | 37 |
| `575_fenster_erkennung.py` | Fenster + Einstellungen: Gehtest, Wärmebild-Personen, Akku-Sparen | 87 |
| `580_uebersetzungen_fr.py` | Übersetzungen Französisch | 1396 |
| `590_uebersetzungen_it.py` | Übersetzungen Italienisch | 1392 |
| `600_uebersetzungen_rm.py` | Übersetzungen Rätoromanisch, Anleitungen | 1763 |
| `604_uebersetzungen_erkennung.py` | Übersetzungen: Gehtest, Entfernung, Wärmebild-Personen, Akku-Sparen | 102 |
| `572_fenster_reiter.py` | Fenster: Reiter Verlauf / Mehr / Simulator, Assistent im Fenster | 144 |
| `580_uebersetzungen_fr.py` | Übersetzungen Französisch | 1396 |
| `590_uebersetzungen_it.py` | Übersetzungen Italienisch | 1392 |
| `600_uebersetzungen_rm.py` | Übersetzungen Rätoromanisch, Anleitungen | 1763 |
| `605_uebersetzungen_konzept.py` | Übersetzungen der Konzept-Bereinigung (Assistent, Modi, Fenster-Reiter) | 97 |
| `609_uebersetzungen_robust.py` | Übersetzungen und Anleitung: Speicherkarte, Selbstheilung, Simulator-Sperre | 142 |
| `610_anleitung_ergaenzungen.py` | Anleitung: Ergänzungen in allen Sprachen | 167 |
| `612_uebersetzungen_spielA.py` | Übersetzungen der Wächter-Werkzeuge (543) | 17 |
| `613_uebersetzungen_sicher.py` | Übersetzungen und Anleitung zu 578 | 165 |
| `614_uebersetzungen_training.py` | Übersetzungen «KI trainieren» / Modell von selbst aktualisieren | 27 |
| `615_uebersetzungen_nopisim.py` | Übersetzung «klug: wichtige Richtungen länger anschauen» (Unterschalter von «Patrouille») | 9 |
| `616_uebersetzungen_spiel2.py` | Übersetzungen der Spiel-Extras (Wetterwechsel, Tarn-Sachen, Diebstahl, Lern-Punkte) | 8 |
| `617_uebersetzungen_platz.py` | Übersetzungen «Dein Platz» (früher «Zwilling deines Platzes») | 8 |
| `618_uebersetzungen_kisicher.py` | Übersetzungen zu 197 (KI-Daten aufräumen) und 574 (Anmelden nur verschlüsselt) | 95 |
| `619_uebersetzungen_simdopp.py` | Übersetzungen der Aufräum-Punkte Spiel-Karte, Bewachte Sachen, Sim-Schalter, Unsichtbar-Trank | 12 |
| `621_uebersetzungen_sicher3.py` | Übersetzungen und Anleitung zu 573 (App-Schlüssel, Sicherheit an einem Ort) und zur Rotlicht-Ansicht (578) | 150 |
| `611_uebersetzungen_users.py` | Übersetzungen und Anleitung «Benutzer und Handys» | 190 |
| `624_uebersetzungen_platzein.py` | Übersetzungen und Anleitung «Platz einrichten» / «Blickwinkel der Kamera» | 200 |
| `625_uebersetzungen_qr.py` | Übersetzungen der QR-Codes (585) | 129 |
| `626_uebersetzungen_live.py` | Übersetzungen der neuen Live-Seite (536) und des Fensters (570) | 89 |
| `627_uebersetzungen_live2.py` | Übersetzungen zu 2.98.29: ein Bearbeiten-Modus, «Für alle Geräte», Grösse, Fenster-Ansicht | 79 |
| `628_uebersetzungen_padview.py` | Übersetzungen der Controller-Ansicht (538) | 76 |
| `629_uebersetzungen_kopfauto.py` | Übersetzungen «Automatische Kopfbewegung» (2.98.30) | 63 |
| `620_daten_produktseite.py` | Daten: Produktseite für Gäste (/info/) | 2651 |
| `630_almanach.py` | Extras: Überlebens-Almanach | 270 |
| `640_start.py` | Start: Befehlszeile, Selbsttest, Programmstart | 152 |

Grob gruppiert: **Kern** (Erkennung, Alarm: 170–230, 410), **Geräte** (Hardware, Audio, Sensoren: 070–100, 240–280),
**Netz** (110–160), **Simulator und Prüfungen** (290–360), **Webseiten** (450–550), **Fenster** (570),
**Extras** (Spiele, Almanach, Produktseite: 320, 340, 620, 630), **Übersetzungen** (560–610), **Daten** (Bilder, ZIPs: 360, 480, 490, 620).
| `608_uebersetzungen_verlauf.py` | Übersetzungen Zeitleiste / Wochenbericht / Gesichter verpixeln, Anleitung | 110 |
