# Rückgang im Prüfstand ab 2.98.23 – Zwischenstand (29.10.2026, Suche pausiert)

- **Weniger Bilder/s (4.6 → 2.8):** nicht MoveEye. Alle vier Kombinationen (MoveEye 2.98.22 / 2.98.25 × Simulator 3D-4.5 / 3D-4.7)
  liefern auf demselben GitHub-Rechner 4.5–4.6 Bilder/s; MoveEye braucht ~26 % CPU, der Engpass ist Godot (~2.6 Kerne). Die Bildrate
  hängt am Prozessor des GitHub-Rechners (früher schon 3.0–4.9 ohne Codeänderung). `pruefstand.py` schreibt jetzt den Prozessor mit.
- **Wärmebild «Nacht, klar» 0/4:** echter Fehler (älter als 2.98.22): der kalte Himmel (≤ −17 °C) setzt das untere Skalenende, der
  Boden liegt bei ~210/255, die Schwelle «Median + 30 %» lag über 255. Behoben in `quelle/230_waermebild.py` (Schwelle nur auf der
  warmen Seite gemessen), ab 2.98.29. Offline geprüft (11 statt 1 Bild mit Person), Prüfstand-Zahlen fehlen noch.
- **Offen:** ob am Tag falsche Wärmebild-Pushes entstehen; kleine Personen im Wärmebild (12–15 Zeilen) werden verpasst (Mindestfläche?).
  «zu dunkel / zu klein» im Bericht ist nur die Beschriftung des Simulators. night_strict und Grössen-Check sind nicht beteiligt.
