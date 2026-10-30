# Zusatz-Bildschirm GeekMagic SmallTV Ultra (Entscheide Daniel, 30.10.2026 10:25) – umgesetzt (Branch wt-smalltv)

Gerät: GeekMagic SmallTV Ultra, Firmware **Ultra-V9.0.40** (Daniel hat eines, läuft im Heimnetz). 1,5" IPS 240×240, ESP8266, WLAN 2,4 GHz,
5 V / 1 A, ca. 1 MB frei. HTTP ohne Passwort: `POST /doUpload?dir=/image/` (JPEG 240×240), `/set?theme=3` (Fotoalbum),
`/set?img=/image//name.jpg`, `/set?brt=0..100`, `/filelist`, `/delete`, `/v.json`, `/app.json`, `/space.json`. Ein Bild ≈ 2–3 s,
eine Anfrage nach der anderen (100–500 ms Pause), keine Selbst-Erkennung im Netz (Adresse eintragen), Flash schonen (nur bei Änderung
hochladen, immer dieselben 1–2 Dateinamen überschreiben). Quelle: geekmagic-stats device-protocol.md.

## Gewählt
- **Status + Alarmbild:** Zustand Aus / Wachsam / Voll, Akku, letzte Meldung, Uhrzeit; bei Meldung Bildausschnitt mit «Fuchs · 91 % · 6 m».
- **Spiel-Anzeige:** Punkte, Countdown, «Erwischt!» während einer Simulator-Runde.
- **Personen:** einstellbar, **Standard nur Symbol + Text** (kein Personenbild).
- **Nacht dunkel + Rotlicht:** nachts gedimmt, rote Bilder (passend zur Rotlicht-Ansicht), bei Alarm kurz hell.
- **Virtueller SmallTV im Simulator:** testen ohne Gerät (gleiche HTTP-Schnittstelle nachgebildet), auch im Prüfstand.
- **Mehrere Bildschirme:** z. B. Zelt und Wohnwagen, jeder mit eigener Auswahl.
- **Einrichtung per QR-Code:** geführt – Bildschirm ins MoveEye-WLAN holen (Hotspot «GIFTV», 192.168.4.1), Adresse finden / prüfen.

## Nicht gewählt
Blinki als Gesicht, Nachtbericht am Morgen.

## Hinweise
- Kein Passwort am Gerät → am besten im eigenen MoveEye-WLAN betreiben; im Konzept-Check erwähnen.
- Einstellungen unter Einstellungen (Gruppe Meldungen / Geräte), Status in «Mehr» bzw. Geräte-Liste; Desktop-Fenster ebenfalls.

Reihenfolge: **nach den neuen Szenen** (`docs/Neue_Szenen_Plan.md`).

## Umgesetzt (30.10.2026, Branch wt-smalltv, auf MoveEye 2.98.47 / Simulator 3D-4.18)
- MoveEye Teil `552_smalltv.py` (Logik, Bilder, Web), `599b_fenster_smalltv.py` (Einstellungen, Fenster, Selbsttest), `562_uebersetzungen_smalltv.py`
  (DE/FR/IT/RM/EN, Anleitungs-Kapitel «Zusatz-Bildschirm (SmallTV)»). Einstellungen → Geräte & Sensoren → «Zusatz-Bildschirm (SmallTV)».
- Status (Aus / Wachsam / Voll, Akku mit «SIM», letzte Meldung, «Stand» Uhrzeit alle 10 min), Alarmbild (Tier: Ausschnitt «Hund · 91 % · 3 m»;
  Person: Symbol + Abstand, Schalter «Bild auch bei Personen»), Spiel (Countdown / Restzeit, Punkte, «Erwischt!», Endstand 60 s).
  Während einer Spielrunde zeigt der Bildschirm das Spiel, Personen-Alarme der Spieler nicht.
- Nachts (is_dark) rot wie die Rotlicht-Ansicht und Helligkeit nachts (Standard 10 %), bei Alarm 20 s hell (nur Bildschirme mit Alarmbild).
- Mehrere Bildschirme (bis 6): Name, Adresse, Ein / Status / Alarmbild / Spiel, Helligkeit; Testbild, Prüfen, Entfernen; Gesundheit (erreichbar,
  Firmware aus /v.json, freier Speicher aus /space.json, Anzahl Bilder, letzter Fehler).
- Einrichtung: Schritte mit QR-Codes (WLAN «GIFTV», Seite 192.168.4.1), «Im Netz suchen» (/24, /v.json, 0,8 s, nur auf Knopfdruck), Hinweis
  «kein Passwort – eigenes WLAN von MoveEye».
- Schonung: ein Faden pro Gerät, eine Anfrage nach der anderen (0,3 s Pause), nur bei Änderung (Hash), höchstens alle 5 s (Alarm sofort),
  abwechselnd me_a.jpg / me_b.jpg (~10–25 KB je Bild), Fotoalbum (theme=3, autoplay=0) alle 10 min neu gesetzt; HTTP 400 → Dateiliste prüfen.
- Simulator `simulator3d/scripts/smalltv.gd`: virtueller SmallTV mit derselben Schnittstelle auf dem Simulator-Port, Kachel unter Karte / Livebild
  (Sensoren → Zusatz-Bildschirm: Kachel zeigen, Macken wie das echte Gerät, Bilder löschen), CONTROL `smalltv` (Zähler, letztes Bild), GET
  `/smalltv.jpg`, `game_live` in der Antwort auf /state. Prüfstand schreibt die Zähler in sein Ergebnis (`smalltv`), Test `werkzeuge/smalltv_test.py`.
