# Projekt «Motion Watch» – mobile Wildtier-Warnung für das Camping

*Stand 23.10.2026, Software-Version 2.0.5. Dieses Dokument beschreibt den ganzen Stand des Projekts.*

## 1. Ziel

Ein Raspberry Pi 5 mit Schwenk-/Neigekopf (3D-gedruckt), normaler Kamera (NoIR) und Wärmebildkamera überwacht beim Camping
die Umgebung und warnt vor Wildtieren und Personen: Push-Nachricht aufs Handy, Alarmton im Browser, Sirene und Licht am Gerät.
Bedient wird es über eine Webseite auf dem Handy (eigenes WLAN des Pi, Handy-Hotspot, Heimnetz oder über Tailscale von unterwegs)
oder über das Fenster auf dem Pi. Später eventuell als Produkt vermarkten.

## 2. Dateien

| Datei | Inhalt |
|---|---|
| `webcam_bewegung_2_0_5.py` | das ganze Programm (eine Datei, Python 3, ca. 14'000 Zeilen): Erkennung, Webseite, Desktop-Fenster |
| `Projektstand_PanTilt_Kamera.md`, `Quellcode_parametrisch_v4.zip` | Gehäuse (v4) aus dem Gehäuse-Chat, parametrisches Python-Modell |
| `Uebergabe_Gehaeuse_Licht_Audio.md` | Ergänzungen ans Gehäuse: Lampen, Lautsprecher, Mikrofon, Pinbelegung |
| `Einrichtung_Raspberry_Pi.md` | Installation, config.txt, Start, Autostart, Updates, Tailscale |
| `Chatverlauf_MotionWatch.md` | Verlauf des Software-Chats (Wünsche und Entscheidungen) |
| `Anleitung_MotionWatch_2_0_5.html` | Bedienungsanleitung (auch im Programm unter «Anleitung») |
| GitHub `DonElektro/MotionWatch` | alle Versionen + `versions.json` für die Update-Funktion |

Jede neue Version bekommt einen neuen Dateinamen `webcam_bewegung_X_Y_Z.py`, die Änderungen stehen oben in der Datei
(Liste «* X.Y.Z: …»). Update auf dem Pi: System & Netz → Updates, Quelle
`https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json`.

## 3. Hardware

- Raspberry Pi 5, Camera Module 3 **NoIR**, Waveshare **Thermal-90** (80 × 62, SPI + I2C 0x40, GPIO 7/23/24)
- 2 × MG90S an **PCA9685** (I2C **0x41**, Lötbrücke A0), Kanal 0 Pan, 1 Tilt; Grenzen in Grad (Pan ±90°, Tilt ±60°)
- Licht weiss + Infrarot 850 nm (je 1-W-LED, ~0,5 W), PCA9685 Kanal 2 / 3 über MOSFET, an den Gabelarmen; nur ein/aus (kein PWM)
- Audio: USB-Mikrofon, USB-Soundkarte + PAM8403 + 40-mm-Lautsprecher im Unterteil, oder Bluetooth-Lautsprecher
- Strom: Powerbank oder Waveshare UPS HAT (2 × 18650 in Serie, INA219 auf I2C 0x42; für den Pi 5 die Version mit 5 A nötig); Relais / Warnlampe an freien GPIOs

## 4. Funktionen (2.0.5)

- **Erkennung:** Bewegung, Personen (Gehmuster + KI SSD MobileNet), Tiere/Objekte, Zonen (Ignorieren / Nur hier / **Privatsphäre**),
  Regen-/Wind-/Schatten-Filter, Voralarm, Wärmebild-Alarm, Geräusch-Alarm
- **Alarm:** scharf/unscharf mit Countdown, Push (ntfy über ntfy-me.com, Telegram, Webhook) mit eigenen Texten, Alarmton im Browser,
  Sirene / eigene Töne, Lichter, Relais mit Auslösern (auch «Fernzugriff» für eine Warnlampe)
- **Aufnahmen:** Video mit Ton und Vorlauf, Schnappschüsse, Zeitraffer, Aufnahmeseite mit Statistik
- **Tier-Tagebuch** (Reiter «Tagebuch»): bestes Bild jedes Tier-Besuchs, Filter, Favoriten, Teilen
- **Nachtbericht:** Push am Morgen (Standard 7 Uhr) mit Zusammenfassung der Nacht + bestem Bild
- **Kamera:** Joystick / Tasten, Verfolgung, Patrouille, mehrere Kameras, Wärmebild-Überlagerung
- **Audio:** Pegel, Mithören, Gegensprechen (https auf Port + 1), Bluetooth-Lautsprecher
- **Camping:** eigenes WLAN, Netzwerk-Automatik, Uhrzeit vom Handy, Autostart, Camping-Profil, Stromsparmodus, **Akku-Laufzeit-Schätzung**
- **Fernzugriff:** Tailscale; Anzeige «🌐 Fern: Gerät», Push bei Fernzugriff; **Gast-Zugang** (Link nur zum Zuschauen, befristet)
- **Betrieb:** Unterspannung, Speicherplatz, Watchdog, Einstellungen sichern/laden, Web-Passwort, Update-Funktion mit Versionswahl,
  Pi ausschalten / neu starten, **Programm pausieren** (startet nach 5 min … 12 h selbst wieder), Internet-Prüfung über Port 443
- **Bedienung:** Webseite (Handy zuerst) in 9 Gruppen + **Einstellungs-Suche**, Desktop-Fenster mit denselben Gruppen, DE/EN, hell/dunkel,
  Vollbild (auch iPhone), Live-Bild verbindet sich selbst neu, **App-Symbol** für den Home-Bildschirm (grün = Heimnetz, rot = Tailscale),
  ⟳-Knopf im App-Modus, Hinweis «Neue Version läuft»

## 5. Offene Punkte

1. Thermal-90-Treiber ist **nicht mit dem echten Modul getestet** (für die Prüfung `stream_spi.py` aus Waveshares `Thermal_Camera_Hat.zip` hochladen).
2. PCA9685, Lichter, Lautsprecher, Bluetooth, Akku-Messung (PMIC), Pause mit Autostart auf dem echten Pi nur teilweise getestet.
3. Desktop-Fenster: in der Testumgebung zuletzt nur mit einem Tkinter-Ersatz geprüft.
4. Gehäuse: Lampenhalter, Lautsprecher/Mikrofon im Unterteil, Lüftung (siehe Übergabe-Dokument).
5. Vermarktung: Name prüfen, Datenschutz (Ton ab Werk aus, Privatsphäre-Zonen), Lizenzen (pysenxor), SD-Karten-Abbild, signierte Updates,
   Diagnose-Paket, Aufteilen in mehrere Dateien, automatische Tests auf GitHub.

## 6. Arbeitsweise (bewährt)

- Jede Änderung = neue Versionsnummer + neue Datei + Eintrag in der Änderungsliste + kurze deutsche Zusammenfassung.
- Webseite und Desktop-Fenster immer beide anpassen, zweisprachig DE/EN; Einstellungen bleiben erhalten (`~/.config/motionwatch/`).
- Vor dem Ausliefern testen (Browser Handy hoch/quer + PC, simulierte Hardware) und ehrlich sagen, was nicht getestet ist.
- Neue Version auch auf GitHub ablegen (`--make-manifest .` aktualisiert `versions.json`).
- Keine Passwörter / privaten ntfy-Themen in geteilte Dateien.
