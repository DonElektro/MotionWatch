# quelle/ – Motion Watch in Teilen

Hier wird Motion Watch bearbeitet. Die Teile werden von `werkzeuge/bauen.py` Byte für Byte zu der einen Datei
`webcam_bewegung_X_Y_Z.py` zusammengesetzt, die der Pi, die Update-Funktion und die Signatur kennen. Die grosse Datei
nie von Hand ändern: GitHub prüft bei jedem Hochladen, dass sie genau zu `quelle/` passt.

Alle Teile zusammen sind **ein** Python-Programm (gemeinsame Namen, keine Importe zwischen den Teilen). Die Reihenfolge
der Nummern ist die Reihenfolge in der Datei – ein Name muss weiter oben stehen als dort, wo er beim Start gebraucht wird.
Die erste Zeile jedes Teils (`#@ …`) ist nur eine Beschreibung und fällt beim Bauen weg.

## Ablauf

```
python3 werkzeuge/bauen.py --neue-version "Was neu ist"            # Nummer +1, Zeile in der Änderungsliste, bauen
python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI               # versions.json signieren + Selbsttest (Schlüssel nie ins Repository)
python3 werkzeuge/bauen.py --pruefen                                # passt die Datei zu quelle/?
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
| `070_hardware_servos_licht.py` | Servos, PCA9685, Mover, Licht, Disco-Licht | 398 |
| `080_waermebild_modul.py` | Treiber Wärmebild-Modul, Klasse Hardware | 281 |
| `090_system_fern_sichtungen.py` | System, Fernzugriff, Sichtungen, Nachtbericht, Gast-Zugang | 465 |
| `100_akku.py` | Akku / USV, Systemüberwachung | 417 |
| `110_netz_wlan.py` | Netz, WLAN suchen und verbinden, QR-Codes | 813 |
| `120_eigenes_wlan_uhr_ort.py` | eigenes WLAN, Uhr vom Handy, Ort (GPS) vom Handy | 720 |
| `130_scharf_profile_modi.py` | Scharf / unscharf, Camping-Profil, einfache Einstellungen, Modi | 368 |
| `140_autostart.py` | Autostart | 422 |
| `150_zweites_wlan_tv_netzcheck.py` | zweites WLAN, USB-Tethering, TV-Anzeige, Netz-Check, WLAN-Wächter | 1059 |
| `160_netzautomatik_patrouille.py` | Netz-Automatik, Patrouille | 160 |
| `170_ki_personen.py` | KI-Modell laden und herunterladen | 110 |
| `180_ki_tierarten_helfer_tunnel.py` | Tierarten, Alarm-Rückblick, KI-Rechenhilfe, KI-Prüfung, Tunnel, AIDetector | 841 |
| `190_relais_wetter_tracker.py` | Relais, Wetter-Analyse, Auto-Tuner, Tracker | 422 |
| `200_erkennung_videoquellen.py` | Video-Quellen (USB, Pi-Kamera, Netz) | 166 |
| `210_demo.py` | Demo-Modus | 255 |
| `220_zeitraffer.py` | Zeitraffer | 195 |
| `230_waermebild.py` | Wärmebild-Überlagerung, Nachtsicht, Easter Egg (Herz) | 349 |
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
| `315_referenz_scan.py` | Referenz-Scan: Raster abfahren, Referenz-Fotos, Vergleich, Bericht (2.95.97) | 347 |
| `320_spielecke.py` | Extras: Spielecke und Spieleabend | 743 |
| `330_usb_geraete.py` | USB-Geräte, Spielesammlung, Seite verlassen (✕ Zurück) | 172 |
| `340_spiele_seiten.py` | Extras: Seiten der Spielecke und des Spieleabends | 655 |
| `350_simulator_link.py` | Verbindung zum Simulator (Schleife) | 87 |
| `360_daten_simulator_python.py` | Daten: der Python-Simulator als ZIP | 897 |
| `370_rueckmeldung_teilen_abschreckung.py` | Rückmeldung, Teilen, Abschreckung, Gegensprechen | 405 |
| `380_updates.py` | Updates | 216 |
| `390_protokoll_bedienermodus.py` | Protokoll, Bedienermodus, Pause, Update-Wächter | 1065 |
| `400_ausschalten.py` | Pi ausschalten / neu starten | 53 |
| `410_motionwatch_kern.py` | KERN: die Erkennungs-Schleife (Bewegung, Personen, Alarm) | 969 |
| `420_webzugang_aufnahmen.py` | Web-Zugang, Aufnahmen, Speicher, Bild für andere Programme | 630 |
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
| `525_web_mehr_seite.py` | Web: Seite «Mehr» (6. Reiter) und `main_tab_page()` für Live / Schutz / Einstellungen | 70 |
| `530_web_hauptseite.py` | Web: Hauptseite | 4459 |
| `540_web_anleitung_aufnahmen.py` | Web: Anleitung, Aufnahmen | 1187 |
| `550_web_server.py` | Web: der Server (alle Adressen) | 2562 |
| `560_uebersetzungen_de.py` | Übersetzungen Deutsch | 498 |
| `570_fenster.py` | Fenster auf dem Pi / PC (Tkinter) | 3322 |
| `580_uebersetzungen_fr.py` | Übersetzungen Französisch | 1396 |
| `590_uebersetzungen_it.py` | Übersetzungen Italienisch | 1392 |
| `600_uebersetzungen_rm.py` | Übersetzungen Rätoromanisch, Anleitungen | 1763 |
| `610_anleitung_ergaenzungen.py` | Anleitung: Ergänzungen in allen Sprachen | 167 |
| `620_daten_produktseite.py` | Daten: Produktseite für Gäste (/info/) | 2651 |
| `630_almanach.py` | Extras: Überlebens-Almanach | 270 |
| `640_start.py` | Start: Befehlszeile, Selbsttest, Programmstart | 152 |

Grob gruppiert: **Kern** (Erkennung, Alarm: 170–230, 410), **Geräte** (Hardware, Audio, Sensoren: 070–100, 240–280),
**Netz** (110–160), **Simulator und Prüfungen** (290–360), **Webseiten** (450–550), **Fenster** (570),
**Extras** (Spiele, Almanach, Produktseite: 320, 340, 620, 630), **Übersetzungen** (560–610), **Daten** (Bilder, ZIPs: 360, 480, 490, 620).
