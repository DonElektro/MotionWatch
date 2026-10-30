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

## Ergänzung 30.10. Abend (Entscheide Daniel 19:20) – umgesetzt (Branch wt-stv2, auf MoveEye 2.98.48 / 3D-4.19)
- **Schalter «Live-Bild und Wechsel»** pro Bildschirm (Feld `rot` in `stv_list`, blauer Schalter wie die anderen, auch im Fenster mit
  kurzer Erklärung darunter). Schon eingetragene Bildschirme: **aus** (keine Überraschung), neu hinzugefügte: **ein**; der virtuelle
  SmallTV des Simulators: ein bei frischen Einstellungen, aus, wenn `stv_sim` schon gespeichert ist. Aus = genau wie bisher (Statusseite,
  Alarmbild 60 s als JPEG).
- **Ein, tagsüber:** alle 30 s (feste Zeitscheiben der echten Uhr) abwechselnd
  - *Live-Bild*: Standbild der Hauptkamera (`frame_out`, Privatzonen schon schwarz), Mitte quadratisch auf 240 × 240, «● LIVE» oben,
    Leiste unten Uhrzeit · Aus/Wachsam/Voll · Akku %. Erkannte Personen werden ohne «Bild auch bei Personen» grob verpixelt
    (`faces_pixelate` aus 375 auf `STATE.person_boxes`). Neu bei jeder Live-Zeitscheibe → höchstens ein Hochladen je 30 s.
  - *Akku und Strom*: grosser gezeichneter Akku mit %, Blitz beim Laden, Laden (voll in N min) / Netzstrom, Solar W, Verbrauch W,
    Restlaufzeit, «SIM» bei Simulator-Werten. Unverändert liegt das Bild noch auf dem Gerät und wird **nur wieder gezeigt** (`/set?img`,
    kein Schreiben in den Flash). Ohne Akku-Werte ist die zweite Seite die Statusseite.
- **Vorrang:** Alarm und Spielrunde wie bisher vor dem Wechsel. **Nachts** (Schalter «Nachts dunkel und rot» + dunkel) kein Wechsel, nur die
  rote, gedimmte Statusseite; ein Alarm wird trotzdem kurz hell.
- **Alarm-Animation:** GIF 240 × 240, 8 Bilder à 160 ms, pulsierender roter Rahmen (4–12 px), blinkendes gezeichnetes ⚠ + «Fuchs · 91 % · 6 m»
  bzw. Personensymbol; eine gemeinsame Palette, ab Bild 2 nur die geänderten Punkte (Rest durchsichtig) → 15–25 KB (Rauschen als
  schlimmster Fall 66 KB). Läuft «Alarmbild bleibt» (60 s), danach JPEG-Standbild mit ⚠ «Nach der Animation bleibt das Alarmbild» (5 min,
  neuer Regler 0–30 min), dann wieder der Wechsel. Nachts rot.
- **Gerät:** GIF über dieselbe Schnittstelle `POST /doUpload?dir=/image/` + `/set?img=/image//me_a.gif` (Handbuch Ultra V9.0.18
  «Picture Display»: Fotoalbum spielt JPG und GIF, GIFs laufen dauernd). Namen me_a / me_b bleiben; nach dem Hochladen wird die Datei mit
  der anderen Endung am gleichen Platz gelöscht (`/delete?file=/image//me_a.jpg`) → nie mehr als zwei Bilder. **Am echten Gerät nicht
  getestet** (ob die Firmware Teilbilder mit Transparenz richtig abspielt, ob /delete so heisst).
- **Bilder pro Tag** (`stv_per_day`, in der Liste «ca. N Bilder/Tag» und im Protokoll, wenn sich die Zahl ändert): ohne Wechsel
  24 × (60/10 + 1) ≈ 170; mit Wechsel tagsüber 60 Live-Bilder + ca. 20 Akku-Seiten pro Stunde, nachts wie ohne Wechsel → bei 12 h Tag
  ≈ 1040, je nach Tageslänge ≈ 750–1350 (Nacht-Schalter aus: ≈ 1900). Bei ~20 KB je Bild ≈ 20 MB pro Tag auf ~1 MB Flash.
- **Simulator** (`smalltv.gd`): eigener kleiner GIF-Leser (Godot 4.3 lädt kein GIF): LZW, Palette, Transparenz, Entsorgung, Zeilensprung;
  die Kachel spielt das GIF mit seinen Pausen ab; CONTROL `smalltv` meldet `gif_frames` / `anim_frames`, `/smalltv.jpg` gibt das GIF zurück.
- **Teile:** `553_smalltv_wechsel.py` (neu), `563_uebersetzungen_smalltv2.py` (neu), kleine Änderungen in 552 / 562 / 599b,
  `werkzeuge/smalltv_test.py` (GIF, Löschen der anderen Endung, nur wieder zeigen), Selbsttest «SmallTV live picture and rotation …».
