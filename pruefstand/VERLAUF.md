# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).

Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).

| Datum | Motion Watch | Simulator | Testlauf | Personen erkannt | nah / mittel / weit | Reaktion | Tiere gemeldet | Fehlalarme | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Kurz (Tag + Nacht) | 2 / 3 (**67 %**) | – / 1/2 / 1/1 | 4.2 s | 0 / 1 | 0 | 1.9 | running · 62 ms | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Nacht | 1 / 1 (**100 %**) | 1/1 / – / – | 0.0 s | 0 / 0 | 0 | 2.0 | running · 62 ms | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Standard (Tag, Wind, Nacht, Regen) | 4 / 5 (**80 %**) | 2/2 / 2/2 / 0/1 | 2.6 s | 2 / 2 | 0 | 2.0 | running · 62 ms | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:07 | 2.95.63 | 3D-3.47 | Kurz (Tag + Nacht) | 0 / 4 (**0 %**) | – | – | 0 / 1 | 0 | 29.0 | running · 77 ms | GitHub (ubuntu, 4 Kerne) |

## Einzelheiten pro Phase (letzter Lauf)

**Kurz (Tag + Nacht)** – 2026-10-28 00:54, Motion Watch 2.95.64

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Tag, Wind | 2 / 3 | 4.2 s | 0 / 1 | 0 | – |
| Nacht mit Infrarot | 0 / 0 | – | 0 / 0 | 0 | – |

**Nacht** – 2026-10-28 00:54, Motion Watch 2.95.64

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Nacht, ohne Licht | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Infrarot an | 1 / 1 | 0.0 s | 0 / 0 | 0 | – |
| Nacht, Regen | 0 / 0 | – | 0 / 0 | 0 | – |

**Standard (Tag, Wind, Nacht, Regen)** – 2026-10-28 00:54, Motion Watch 2.95.64

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Tag, klar | 3 / 3 | 2.6 s | 2 / 2 | 0 | – |
| Tag, Wind und Wolken | 1 / 2 | 2.4 s | 0 / 0 | 0 | 1× zu klein / weit weg |
| Nacht, klar (Insekten am Licht) | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Regen | 0 / 0 | – | 0 / 0 | 0 | – |

