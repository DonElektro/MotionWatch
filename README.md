# Motion Watch

Kamera-Überwachung für den Raspberry Pi 5 (Schwenk-/Neigekopf, KI-Personenerkennung, Wärmebild, Geräusch-Alarm,
Licht, Sirene, Push-Nachrichten, eigenes WLAN) – gebaut als mobile Wildtier-Warnung fürs Camping.

**Alles läuft auf dem Gerät – keine Cloud, kein Abo, deine Bilder gehören dir.**

Seit Version 2.0: Tier-Tagebuch (bestes Bild jedes Tier-Besuchs), Nachtbericht am Morgen per Push, Privatsphäre-Zonen
(Bereiche schwarz abdecken), Gast-Zugang (Link nur zum Zuschauen), App-Symbol für den Handy-Startbildschirm,
Akku-Laufzeit der Powerbank.

## Dateien

| Datei | Inhalt |
|---|---|
| `webcam_bewegung_X_Y_Z.py` | das Programm, eine Datei pro Version (die neuste ist oben in `versions.json`) |
| `versions.json` | Liste der Versionen für die Update-Funktion (die letzten etwa 20; Prüfsumme, Datum, Änderungen) |
| `Anleitung.html` | Bedienungsanleitung (auch im Programm unter «Anleitung») |

## Updates auf dem Pi

Auf der Webseite des Pi unter **System & Netz → Updates** als Quelle eintragen:

```
https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json
```

Dann «Nach Versionen suchen» und die gewünschte Version wählen. Ältere Versionen bleiben auf dem Pi und können jederzeit
wieder gewählt werden.

## Neue Version veröffentlichen

1. Neue Datei `webcam_bewegung_X_Y_Z.py` in diesen Ordner legen.
2. `python3 webcam_bewegung_X_Y_Z.py --make-manifest .` ausführen (aktualisiert `versions.json`).
3. Beide Dateien hochladen.

Das Repository enthält keine Passwörter oder Zugangsdaten – diese liegen nur in den Einstellungen auf dem Pi
(`~/.config/motionwatch/`).
