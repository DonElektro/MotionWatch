# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).

| Datum | Motion Watch | Simulator | Testlauf | Personen erkannt | Reaktion | Tiere gemeldet | Fehlalarme | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-28 00:07 | 2.95.63 | 3D-3.47 | Kurz (Tag + Nacht) | 0 / 4 (**0 %**) | – | 0 / 1 | 0 | 29.0 | running · 77 ms | GitHub (ubuntu, 4 Kerne) |

## Einzelheiten pro Phase (letzter Lauf)

**Kurz (Tag + Nacht)** – 2026-10-28 00:07, Motion Watch 2.95.63

| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |
|---|---|---|---|---|---|
| Tag, Wind | 0 / 3 | – | 0 / 1 | 0 | 1× zu schnell, 1× zu klein / weit weg |
| Nacht mit Infrarot | 0 / 1 | – | 0 / 0 | 0 | 1× zu dunkel |

