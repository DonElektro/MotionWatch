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
| `050_meldungen_push.py` | Meldungen (ntfy, Telegram, Webhook), Web-Push | 289 |
| `060_sicherung_schutz_klima.py` | Sicherung, Diebstahlschutz, Linse, Klima, Wetter, Postausgang, Notifier | 1224 |
| `066_alarm_extras.py` | Alarm-Extras: Knöpfe in der Push-Nachricht (/na/), Akku-Prognose, Morgen-Bildstreifen, «Was war das?», doppelte Bestätigung, Ansage beim Einschalten, «Bist du's?» | 724 |
| `067_speicherkarte.py` | Speicherkarte schonen: Schreibmenge pro Tag, Dateisystem-Fehler, Schreibschutz (Overlay) | 267 |
| `068_pruefstand_pushes.py` | Prüfstand: die letzten Push-Nachrichten für den Simulator (echte Pushes zählen statt Flackern) | 17 |
| `070_hardware_servos_licht.py` | Servos, PCA9685, Mover, Licht, Disco-Licht | 398 |
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
| `150_zweites_wlan_tv_netzcheck.py` | zweites WLAN, USB-Tethering, TV-Anzeige, Netz-Check, WLAN-Wächter | 1059 |
| `160_netzautomatik_patrouille.py` | Netz-Automatik, Patrouille | 160 |
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
| `232_waermebild_person.py` | Personen im Wärmebild (nachts, wenn die Kamera nichts sieht) | 105 |
| `240_audio.py` | Mikrofon, Geräusch-Alarm | 81 |
| `250_klatschen_bluetooth_ton.py` | Klatschschalter, Bluetooth, Lautsprecher, Sprachausgabe | 1131 |
| `255_wecker.py` | Wecker mit Schlafplatz: wegschauen, wecken, Gesten (winken / aufstehen) | 330 |
| `258_entwickler.py` | Entwickler-Bereich: eigene Verbindungen, erreichte Namen, Datenmenge (nur lesen, PIN) | 330 |
| `260_mehrere_geraete.py` | mehrere Motion-Watch-Geräte | 164 |
| `270_mqtt.py` | MQTT / Home Assistant | 250 |
| `280_sms_sensoren_sturm_gps_solar.py` | SMS, Sensoren, Sturmwarnung, GPS, Solar | 870 |
| `290_simulator_verbindung.py` | Verbindung zum Simulator | 333 |
| `300_werkzeuge_simulator3d.py` | Werkzeuge, 3D-Simulator für Windows und den Pi, Simulator-Suche | 1155 |
| `310_testlaeufe.py` | Testläufe mit Auswertung und Optimierung | 485 |
| `312_erkennung_assistent.py` | Assistent «Erkennung verbessern» (ein Ablauf statt sechs Funktionen), Pause des Auto-Tuners | 307 |
| `315_referenz_scan.py` | Referenz-Scan: Raster abfahren, Referenz-Fotos, Vergleich, Bericht (2.95.97) | 347 |
| `320_spielecke.py` | Extras: Spielecke und Spieleabend | 743 |
| `330_usb_geraete.py` | USB-Geräte, Spielesammlung, Seite verlassen (✕ Zurück) | 172 |
| `340_spiele_seiten.py` | Extras: Seiten der Spielecke und des Spieleabends | 655 |
| `350_simulator_link.py` | Verbindung zum Simulator (Schleife) | 87 |
| `360_daten_simulator_python.py` | Daten: der Python-Simulator als ZIP | 897 |
| `370_rueckmeldung_teilen_abschreckung.py` | Rückmeldung, Teilen, Abschreckung, Gegensprechen | 405 |
| `375_gesichter_verpixeln.py` | Gesichter verpixeln beim Teilen (nur die geteilte Kopie) | 250 |
| `380_updates.py` | Updates | 216 |
| `390_protokoll_bedienermodus.py` | Protokoll, Bedienermodus, Pause, Update-Wächter | 1065 |
| `395_code_pflege.py` | Code-Pflege im Selbsttest: fehlende Übersetzungen fr / it / rm (nur Warnung), MIGRATE_ONLY (alte Schlüssel nur zum Übernehmen), SELFTEST_EXTRA | 85 |
| `400_ausschalten.py` | Pi ausschalten / neu starten | 53 |
| `410_motionwatch_kern.py` | KERN: die Erkennungs-Schleife (Bewegung, Personen, Alarm) | 969 |
| `415_entfernung_gehtest.py` | Entfernung und Richtung einer Person, Gehtest beim Einrichten | 376 |
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
| `525_web_mehr_seite.py` | Web: Seite «Mehr» (6. Reiter) und `main_tab_page()` für Live / Schutz / Einstellungen | 70 |
| `530_web_hauptseite.py` | Web: Hauptseite | 4459 |
| `535_web_erkennung.py` | Web: Gehtest (Live, Schutz), Akku-Sparen auf der Schutz-Seite | 119 |
| `540_web_anleitung_aufnahmen.py` | Web: Anleitung, Aufnahmen | 1187 |
| `545_simulator_updates.py` | Simulator-Updates: ein Besitzer («Neue Versionen» im Simulator) | 72 |
| `550_web_server.py` | Web: der Server (alle Adressen) | 2562 |
| `560_uebersetzungen_de.py` | Übersetzungen Deutsch | 498 |
| `570_fenster.py` | Fenster auf dem Pi / PC (Tkinter) | 3322 |
| `576_fenster_zeitleiste.py` | Fenster: Zeitleiste als Liste, Wochenbericht | 130 |
| `577_nachlauf_konzept.py` | Nachlauf Konzept-Check: ein Wochenbericht, Rückkehr des Handys (ausschalten / fragen / nichts), Akku-Schwellen zusammen, Auto-Tuner ±20 %, Übernahme alter Einstellungen | 201 |
| `578_sicher.py` | «Sicher»: «Aus» in der Push nur mit PIN, Push nach Stromausfall, Fehlerseiten in der eigenen Sprache, Dunkle Ansicht, Namen für Bildschirmleser, Aufnahmen nach N Tagen löschen / «Ferien vorbei», Push ohne Bild | 743 |
| `579_ki_modell_auto_schalter.py` | Schalter «Eigenes Modell von selbst aktualisieren» (Web und Fenster) | 4 |
| `571_alarm_einstellungen.py` | Schalter und Regler der Alarm-Extras (Web und Fenster) | 16 |
| `573_app_schluessel.py` | «App-Schlüssel» für andere Programme (nur als Hash gespeichert, auch über http, nie Sicherheits-Funktionen) und «Sicherheit an einem Ort» (Passwort, Benutzer, App-Schlüssel, Sicherheits-Check unter Einstellungen → Sicherheit; Web und Fenster) | 380 |
| `574_anmelden_verschluesselt.py` | «Anmelden nur verschlüsselt»: das Web-Passwort nur über https, vom Gerät selbst oder Tailscale; Hinweis-Seite, Rückfall ohne https (Web und Fenster) | 235 |
| `580_uebersetzungen_fr.py` | Übersetzungen Französisch | 1396 |
| `590_uebersetzungen_it.py` | Übersetzungen Italienisch | 1392 |
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
| `613_uebersetzungen_sicher.py` | Übersetzungen und Anleitung zu 578 | 165 |
| `614_uebersetzungen_training.py` | Übersetzungen «KI trainieren» / Modell von selbst aktualisieren | 27 |
| `616_uebersetzungen_spiel2.py` | Übersetzungen der Spiel-Extras (Wetterwechsel, Tarn-Sachen, Diebstahl, Lern-Punkte) | 8 |
| `617_uebersetzungen_platz.py` | Übersetzungen «Dein Platz» (früher «Zwilling deines Platzes») | 8 |
| `618_uebersetzungen_kisicher.py` | Übersetzungen zu 197 (KI-Daten aufräumen) und 574 (Anmelden nur verschlüsselt) | 95 |
| `619_uebersetzungen_sicher3.py` | Übersetzungen und Anleitung zu 573 (App-Schlüssel, Sicherheit an einem Ort) und zur Rotlicht-Ansicht (578) | 150 |
| `620_daten_produktseite.py` | Daten: Produktseite für Gäste (/info/) | 2651 |
| `630_almanach.py` | Extras: Überlebens-Almanach | 270 |
| `640_start.py` | Start: Befehlszeile, Selbsttest, Programmstart | 152 |

Grob gruppiert: **Kern** (Erkennung, Alarm: 170–230, 410), **Geräte** (Hardware, Audio, Sensoren: 070–100, 240–280),
**Netz** (110–160), **Simulator und Prüfungen** (290–360), **Webseiten** (450–550), **Fenster** (570),
**Extras** (Spiele, Almanach, Produktseite: 320, 340, 620, 630), **Übersetzungen** (560–610), **Daten** (Bilder, ZIPs: 360, 480, 490, 620).
| `608_uebersetzungen_verlauf.py` | Übersetzungen Zeitleiste / Wochenbericht / Gesichter verpixeln, Anleitung | 110 |
