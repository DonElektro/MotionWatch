# Zusatz-Bildschirm GeekMagic SmallTV Ultra (Entscheide Daniel, 30.10.2026 10:25)

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
