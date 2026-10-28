# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).

Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).

| Datum | Motion Watch | Simulator | Testlauf | Personen erkannt | nah / mittel / weit | Reaktion | Tiere gemeldet | Fehlalarme | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-28 01:49 | 2.95.64 | 3D-3.48 | Nacht | 0 / 1 (**0 %**) | 0/1 / – / – | – | 0 / 0 | 0 | 1.8 | no model files | Testumgebung Claude (2 Kerne) |
| 2026-10-28 00:07 | 2.95.63 | 3D-3.47 | Kurz (Tag + Nacht) | 0 / 4 (**0 %**) | – | – | 0 / 1 | 0 | 29.0 | running · 77 ms | GitHub (ubuntu, 4 Kerne) |

## Einzelheiten pro Phase (letzter Lauf)

**Nacht** – 2026-10-28 01:49, Motion Watch 2.95.64

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Nacht, ohne Licht | 0 / 0 | – | 0 / 0 | 0 | – |
| Nacht, Infrarot an | 0 / 1 | – | 0 / 0 | 0 | 1× zu dunkel |
| Nacht, Regen | 0 / 0 | – | 0 / 0 | 0 | – |

