# Prüfstand – die Erkennung messen

Der Prüfstand beantwortet bei jeder neuen Version die Frage: **Erkennt Motion Watch besser oder schlechter als vorher?**

## So funktioniert es

1. `pruefstand.py` startet den 3D-Simulator und Motion Watch ohne Bildschirm (eigener, leerer Einstellungs-Ordner,
   Simulation an, keine Updates).
2. Im Simulator läuft ein fester **Testlauf** (`simulator3d/scripts/testrun.gd`): Phasen mit Tag, Nacht, Wind, Regen,
   Infrarot … und immer **dieselben Besucher auf denselben Wegen** (fester Zufallsstart). Der Simulator weiss, wer wann für eine
   Kamera sichtbar war (frei, gross genug, genug Licht) und vergleicht das mit dem, was Motion Watch meldet.
3. Die Zahlen kommen als JSON nach `ergebnisse/` und in die Tabelle **`VERLAUF.md`**:
   Personen erkannt (%), Reaktionszeit, Tiere gemeldet, Fehlalarme, Bilder pro Sekunde, ob die KI lief.
4. Der Lauf wird mit dem letzten **vergleichbaren** Lauf verglichen (gleicher Testlauf, gleicher Rechner, gleicher KI-Stand):
   10 Prozentpunkte weniger Personen oder ein Fehlalarm mehr pro Lauf = «SCHLECHTER».

## Testläufe

| Name | Inhalt | Dauer |
|---|---|---|
| `quick` | Tag mit Wind, Nacht mit Infrarot | ca. 2½ Min. |
| `standard` | Tag, Wind und Wolken, Nacht mit Insekten, Nacht mit Regen | ca. 5 Min. |
| `night` | Nacht ohne Licht, mit Infrarot, mit Regen | ca. 4 Min. |
| `hard` | Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten | ca. 9 Min. |

## Starten

Auf GitHub: **Actions → Prüfstand → Run workflow** (läuft auch jeden Sonntag in der Nacht). Dort mit echtem KI-Modell;
das Ergebnis wird ins Repository geschrieben.

Auf einem Linux-PC (braucht Godot 4.3, Python mit opencv, numpy, flask, pillow, cryptography; ohne Bildschirm Xvfb):

```
python3 pruefstand/pruefstand.py --godot /pfad/Godot_v4.3-stable_linux.x86_64 --plaene quick,night
python3 pruefstand/pruefstand.py --sim-bin /pfad/MotionWatch3D.x86_64 --plaene standard --wiederholungen 3
python3 pruefstand/pruefstand.py --nur-verlauf          # nur VERLAUF.md neu schreiben
```

`--streng` gibt den Rückgabewert 3, wenn die Erkennung schlechter geworden ist (für automatische Prüfungen).

## Grenzen

- Der Simulator ist nicht die Wirklichkeit: Die Zahlen zeigen, ob eine Version **besser oder schlechter als die vorherige**
  ist, nicht wie gut Motion Watch in einer echten Nacht ist. Dafür braucht es weiterhin Testnächte mit dem echten Gerät.
- Ein langsamer Rechner liefert weniger Bilder pro Sekunde und damit schlechtere Zahlen: nur Zeilen vom gleichen Rechner vergleichen.
- Auf GitHub (ohne Grafikkarte) liefert der Simulator nur etwa **2 Bilder pro Sekunde**; die Kamera am echten Pi 10–15.
  Die Zahlen sind dort also eher zu streng.
- Pro Lauf sind nur wenige Personen gut sichtbar (3–6). Für verlässlichere Zahlen `--wiederholungen 3` oder den Testlauf `standard`
  nehmen; ein Unterschied von einer Person ist noch kein Beweis.
- Ohne KI-Modell (z. B. ohne Internet) erkennt Motion Watch Personen nur über Bewegung und Gehmuster – die Spalte «KI» zeigt das.

## Auf dem eigenen PC (ab Simulator 3D-3.49)

Im 3D-Simulator: Werkzeuge → «Prüfstand: Erkennung messen». Motion Watch wählen (das verbundene oder eine Datei
`webcam_bewegung_X.py` einlesen), Testläufe ankreuzen, «Messung starten». Am Schluss erscheint das Ergebnis.
«Ergebnis senden» legt die Datei mit einem GitHub-Schlüssel (fein abgestuft, nur dieses Repository, «Contents: Read and write»)
direkt in `pruefstand/ergebnisse/`; der Ablauf «Prüfstand-Verlauf» schreibt dann `VERLAUF.md` neu. Ohne Schlüssel landet die
Datei auf dem Schreibtisch und kann im Chat angehängt werden.
