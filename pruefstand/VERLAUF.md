# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).

Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).

| Datum | Motion Watch | Simulator | Testlauf | Personen erkannt | nah / mittel / weit | Reaktion | Tiere gemeldet | Fehlalarme | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Kurz (Tag + Nacht) | 0 / 2 (**0 %**) | 0/1 / 0/1 / – | – | 0 / 1 | 0 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Nacht | 0 / 0 (**0 %**) | – | – | 0 / 0 | 0 | 3.2 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Standard (Tag, Wind, Nacht, Regen) | 2 / 6 (**33 %**) | 1/1 / 1/3 / 0/2 | 6.4 s | 1 / 2 | 0 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Kurz (Tag + Nacht) | 0 / 3 (**0 %**) | 0/2 / 0/1 / – | – | 0 / 1 | 0 | 4.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Nacht | 0 / 1 (**0 %**) | – / 0/1 / – | – | 0 / 0 | 0 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Standard (Tag, Wind, Nacht, Regen) | 6 / 6 (**100 %**) | 4/4 / – / 2/2 | 5.1 s | 2 / 2 | 0 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Kurz (Tag + Nacht) ×3 | 8 / 8 (**100 %**) | 4/4 / – / 4/4 | 3.4 s | 2 / 3 | 0 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Nacht ×3 | 1 / 1 (**100 %**) | 1/1 / – / – | 3.7 s | 0 / 0 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Standard (Tag, Wind, Nacht, Regen) ×3 | 4 / 15 (**27 %**) | 2/2 / 1/9 / 1/4 | 6.8 s | 3 / 4 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Kurz (Tag + Nacht) | 2 / 3 (**67 %**) | – / 1/2 / 1/1 | 4.2 s | 0 / 1 | 0 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Nacht | 1 / 1 (**100 %**) | 1/1 / – / – | 0.0 s | 0 / 0 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Standard (Tag, Wind, Nacht, Regen) | 4 / 5 (**80 %**) | 2/2 / 2/2 / 0/1 | 2.6 s | 2 / 2 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:07 | 2.95.63 | 3D-3.47 | Kurz (Tag + Nacht) – *vor der Korrektur der Bildrate (Bilder/s falsch gemessen), Wahrheit: Kopf- und feste Kamera* | 0 / 4 (**0 %**) | – | – | 0 / 1 | 0 | 29.0 | mit KI | GitHub (ubuntu, 4 Kerne) |

## Einzelheiten pro Phase (letzter Lauf)

**Kurz (Tag + Nacht)** – 2026-10-29 01:49, Motion Watch 2.98.10

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Tag, Wind | 0 / 2 | – | 0 / 1 | 0 | 1× zu schnell, 1× zu klein / weit weg |
| Nacht mit Infrarot | 0 / 0 | – | 0 / 0 | 0 | – |

**Nacht** – 2026-10-29 01:49, Motion Watch 2.98.10

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Nacht, ohne Licht | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Infrarot an | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Regen | 0 / 0 | – | 0 / 0 | 0 | – |

**Standard (Tag, Wind, Nacht, Regen)** – 2026-10-29 01:49, Motion Watch 2.98.10

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Tag, klar | 2 / 4 | 6.4 s | 1 / 2 | 0 | 2× zu klein / weit weg |
| Tag, Wind und Wolken | 0 / 2 | – | 0 / 0 | 0 | 1× zu schnell, 1× zu klein / weit weg |
| Nacht, klar (Insekten am Licht) | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Regen | 0 / 0 | – | 0 / 0 | 0 | – |

