# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).

**Pushes richtig / falsch** (ab Prüfstand 2): die Push-Nachrichten, die MoveEye wirklich verschickt hat (Test-Postfach der
Simulation). Richtig = eine Person war sichtbar oder im Bild; derselbe Besuch nochmals innert 10 s zählt einmal.
Bei «Ganze Nacht» ist das die Zahl pro Nacht. **Flackern** = jede kurze Personen-Meldung ohne sichtbare Person (hiess
vorher «Fehlalarme»; ein Dachs gab so 3–5 «Fehlalarme» in Sekunden, aber höchstens einen Push).
**Wärmebild**: Personen, die nachts nur die Wärmebildkamera sah (ohne Licht, zu weit fürs Infrarot) – erkannt / sichtbar.
Mehrere Läufe (Zufall 1, 2, 3 … oder Wiederholungen): in Klammern die Streuung (kleinster–grösster Wert pro Lauf).

Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).

| Datum | Motion Watch | Simulator | Testlauf | Pushes richtig / falsch | Personen erkannt | Wärmebild | nah / mittel / weit | Reaktion | Tiere gemeldet | Flackern | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-30 03:24 | 2.98.39 | 3D-4.12 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.5 s | 3 / 3 | 11 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 03:10 | 2.98.37 | 3D-4.12 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 2/3 / – | 2.1 s | 2 / 3 | 2 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 02:15 | 2.98.36 | 3D-4.11 | Kurz (Tag + Nacht) | **4** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 2/2 / 0/1 | 1.6 s | 2 / 4 | 6 | 3.5 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-30 01:56 | 2.98.35 | 3D-4.10 | Kurz (Tag + Nacht) | **2** / **1** | 8 / 10 (**80 %**) | – | 7/8 / 1/1 / 0/1 | 0.6 s | 2 / 3 | 8 | 3.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-29 23:43 | 2.98.33 | 3D-4.10 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 8/8 / 1/1 / 1/1 | 2.0 s | 4 / 4 | 3 | 2.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-29 22:48 | 2.98.32 | 3D-4.10 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 4.9 s | 3 / 3 | 6 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-29 21:40 | 2.98.31 | 3D-4.9 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.8 s | 4 / 4 | 7 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-29 20:18 | 2.98.30 | 3D-4.9 | Kurz (Tag + Nacht) | **4** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 2/2 / 0/1 | 1.5 s | 3 / 3 | 8 | 2.9 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-29 19:16 | 2.98.29 | 3D-4.9 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 3/3 / – | 1.2 s | 4 / 4 | 4 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-29 17:50 | 2.98.27 | 3D-4.8 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 10 (**90 %**) | – | 6/7 / 3/3 / – | 1.2 s | 4 / 4 | 7 | 4.4 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 17:50 | 2.98.27 | 3D-4.8 | Nacht | **3** / **0** | 6 / 12 (**50 %**) | 2 / 8 | 3/3 / 1/1 / – | 1.1 s | 5 / 8 | 0 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 17:50 | 2.98.27 | 3D-4.8 | Standard (Tag, Wind, Nacht, Regen) | **6** / **1** | 19 / 22 (**86 %**) | 5 / 8 | 6/6 / 6/6 / 2/2 | 0.8 s | 7 / 10 | 2 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 17:50 | 2.98.27 | 3D-4.8 | Ganze Nacht (20–6 Uhr, Zeitraffer) | **1** / **1** pro Nacht | 1 / 2 (**50 %**) | 1 / 2 | – | 0.6 s | 2 / 15 | 1 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 17:50 | 2.98.27 | 3D-4.8 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.7 s | 4 / 4 | 2 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 16:37 | 2.98.23 | 3D-4.6 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 2.1 s | 4 / 4 | 0 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 16:37 | 2.98.23 | 3D-4.6 | Nacht | **4** / **0** | 9 / 12 (**75 %**) | 7 / 9 | 2/2 / 0/1 / – | 2.8 s | 3 / 7 | 2 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 16:37 | 2.98.23 | 3D-4.6 | Standard (Tag, Wind, Nacht, Regen) | **4** / **0** | 10 / 20 (**50 %**) | 2 / 8 | 4/5 / 2/4 / 2/3 | 2.0 s | 3 / 10 | 1 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 16:37 | 2.98.23 | 3D-4.6 | Ganze Nacht (20–6 Uhr, Zeitraffer) | **0** / **1** pro Nacht | 0 / 2 (**0 %**) | 0 / 2 | – | – | 0 / 15 | 1 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 16:37 | 2.98.23 | 3D-4.6 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | **1** / **1** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 2.4 s | 1 / 3 | 5 | 2.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 15:51 | 2.98.22 | 3D-4.5 | Kurz (Tag + Nacht) | **2** / **2** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.5 s | 4 / 4 | 13 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 15:51 | 2.98.22 | 3D-4.5 | Nacht | **2** / **1** | 6 / 12 (**50 %**) | 3 / 9 | 2/2 / 1/1 / – | 1.1 s | 6 / 8 | 16 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 15:51 | 2.98.22 | 3D-4.5 | Standard (Tag, Wind, Nacht, Regen) | **5** / **0** | 16 / 22 (**73 %**) | 2 / 8 | 5/5 / 7/7 / 2/2 | 1.3 s | 7 / 11 | 10 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 15:51 | 2.98.22 | 3D-4.5 | Ganze Nacht (20–6 Uhr, Zeitraffer) | **0** / **0** pro Nacht | 0 / 2 (**0 %**) | 0 / 2 | – | – | 5 / 15 | 0 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 15:51 | 2.98.22 | 3D-4.5 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | **2** / **0** | 9 / 9 (**100 %**) | – | 7/7 / 2/2 / – | 0.5 s | 4 / 4 | 10 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Kurz (Tag + Nacht) | – | 8 / 8 (**100 %**) | – | 7/7 / 1/1 / – | 0.8 s | 3 / 3 | 12 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Nacht | – | 3 / 4 (**75 %**) | – | 3/3 / 0/1 / – | 1.8 s | 4 / 4 | 0 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) | – | 6 / 6 (**100 %**) | – | 1/1 / 4/4 / 1/1 | 2.7 s | 3 / 3 | 3 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | – | 0 / 0 (**0 %**) | – | – | – | 0 / 0 | 0 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Nacht · ohne Kamera-Effekte | – | 1 / 1 (**100 %**) | – | 1/1 / – / – | 0.0 s | 1 / 1 | 3 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 14:34 | 2.98.18 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) · ohne Kamera-Effekte | – | 14 / 14 (**100 %**) | – | 4/4 / 8/8 / 2/2 | 0.8 s | 6 / 6 | 2 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Kurz (Tag + Nacht) | – | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.8 s | 3 / 3 | 6 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Nacht | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 1.1 s | 4 / 4 | 5 | 4.5 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) | – | 14 / 14 (**100 %**) | – | 6/6 / 5/5 / 3/3 | 1.8 s | 6 / 6 | 4 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | – | 8 / 8 (**100 %**) | – | 6/6 / 2/2 / – | 0.8 s | 4 / 4 | 7 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Nacht · ohne Kamera-Effekte | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 1.5 s | 4 / 4 | 13 | 4.5 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 13:14 | 2.98.16 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) · ohne Kamera-Effekte | – | 14 / 14 (**100 %**) | – | 6/6 / 4/4 / 4/4 | 1.0 s | 6 / 6 | 10 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Kurz (Tag + Nacht) | – | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.0 s | 4 / 4 | 11 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Nacht | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 1.1 s | 3 / 3 | 1 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) | – | 14 / 14 (**100 %**) | – | 6/6 / 6/6 / 2/2 | 1.3 s | 6 / 6 | 8 | 4.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | – | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 7 | 4.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Nacht · ohne Kamera-Effekte | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 0.6 s | 4 / 4 | 19 | 4.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 11:12 | 2.98.15 | 3D-4.2 | Standard (Tag, Wind, Nacht, Regen) · ohne Kamera-Effekte | – | 14 / 14 (**100 %**) | – | 6/6 / 4/4 / 4/4 | 0.8 s | 6 / 6 | 6 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Kurz (Tag + Nacht) | – | 7 / 8 (**88 %**) | – | 4/5 / 3/3 / – | 1.3 s | 2 / 2 | 4 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Nacht | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 4.0 s | 4 / 4 | 2 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Standard (Tag, Wind, Nacht, Regen) | – | 14 / 14 (**100 %**) | – | 6/6 / 7/7 / 1/1 | 2.0 s | 6 / 6 | 6 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | – | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.0 s | 4 / 4 | 7 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Nacht · ohne Kamera-Effekte | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 1.8 s | 4 / 4 | 8 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 09:55 | 2.98.14 | 3D-4.1 | Standard (Tag, Wind, Nacht, Regen) · ohne Kamera-Effekte | – | 14 / 14 (**100 %**) | – | 6/6 / 4/4 / 4/4 | 3.3 s | 6 / 6 | 5 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Kurz (Tag + Nacht) | – | 6 / 10 (**60 %**) | – | 3/7 / 2/2 / 1/1 | 1.7 s | 2 / 3 | 1 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Nacht | – | 2 / 4 (**50 %**) | – | 2/3 / 0/1 / – | 3.5 s | 3 / 5 | 2 | 3.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Standard (Tag, Wind, Nacht, Regen) | – | 12 / 14 (**86 %**) | – | 5/5 / 5/6 / 2/3 | 1.3 s | 6 / 6 | 5 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Kurz (Tag + Nacht) · ohne Kamera-Effekte | – | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.5 s | 3 / 3 | 5 | 3.7 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Nacht · ohne Kamera-Effekte | – | 3 / 3 (**100 %**) | – | 2/2 / 1/1 / – | 0.3 s | 4 / 4 | 10 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 04:37 | 2.98.13 | 3D-4.0 | Standard (Tag, Wind, Nacht, Regen) · ohne Kamera-Effekte | – | 14 / 14 (**100 %**) | – | 5/5 / 7/7 / 2/2 | 1.5 s | 6 / 6 | 1 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:39 | 2.98.12 | 3D-3.99 | Kurz (Tag + Nacht) | – | 0 / 4 (**0 %**) | – | 0/2 / 0/1 / 0/1 | – | 1 / 1 | 0 | 3.2 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:39 | 2.98.12 | 3D-3.99 | Nacht | – | 0 / 0 (**0 %**) | – | – | – | 0 / 0 | 1 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:39 | 2.98.12 | 3D-3.99 | Standard (Tag, Wind, Nacht, Regen) | – | 2 / 6 (**33 %**) | – | 0/2 / 2/4 / – | 6.7 s | 2 / 3 | 1 | 3.2 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:15 | 2.98.11 | 3D-3.98 | Kurz (Tag + Nacht) | – | 0 / 2 (**0 %**) | – | – / 0/2 / – | – | 0 / 1 | 0 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:15 | 2.98.11 | 3D-3.98 | Nacht | – | 0 / 0 (**0 %**) | – | – | – | 0 / 0 | 0 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 02:15 | 2.98.11 | 3D-3.98 | Standard (Tag, Wind, Nacht, Regen) | – | 4 / 6 (**67 %**) | – | 1/1 / 3/3 / 0/2 | 3.8 s | 1 / 1 | 0 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Kurz (Tag + Nacht) | – | 0 / 2 (**0 %**) | – | 0/1 / 0/1 / – | – | 0 / 1 | 0 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Nacht | – | 0 / 0 (**0 %**) | – | – | – | 0 / 0 | 0 | 3.2 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:49 | 2.98.10 | 3D-3.97 | Standard (Tag, Wind, Nacht, Regen) | – | 2 / 6 (**33 %**) | – | 1/1 / 1/3 / 0/2 | 6.4 s | 1 / 2 | 0 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Kurz (Tag + Nacht) | – | 0 / 3 (**0 %**) | – | 0/2 / 0/1 / – | – | 0 / 1 | 0 | 4.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Nacht | – | 0 / 1 (**0 %**) | – | – / 0/1 / – | – | 0 / 0 | 0 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-29 01:32 | 2.98.9 | 3D-3.96 | Standard (Tag, Wind, Nacht, Regen) | – | 6 / 6 (**100 %**) | – | 4/4 / – / 2/2 | 5.1 s | 2 / 2 | 0 | 4.8 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Kurz (Tag + Nacht) ×3 | – | 8 / 8 (**100 %**) (100 %) | – | 4/4 / – / 4/4 | 3.4 s | 2 / 3 | 0 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Nacht ×3 | – | 1 / 1 (**100 %**) | – | 1/1 / – / – | 3.7 s | 0 / 0 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 06:53 | 2.95.64 | 3D-3.48 | Standard (Tag, Wind, Nacht, Regen) ×3 | – | 4 / 15 (**27 %**) (0–50 %) | – | 2/2 / 1/9 / 1/4 | 6.8 s | 3 / 4 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Kurz (Tag + Nacht) | – | 2 / 3 (**67 %**) | – | – / 1/2 / 1/1 | 4.2 s | 0 / 1 | 0 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Nacht | – | 1 / 1 (**100 %**) | – | 1/1 / – / – | 0.0 s | 0 / 0 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:54 | 2.95.64 | 3D-3.48 | Standard (Tag, Wind, Nacht, Regen) | – | 4 / 5 (**80 %**) | – | 2/2 / 2/2 / 0/1 | 2.6 s | 2 / 2 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) |
| 2026-10-28 00:07 | 2.95.63 | 3D-3.47 | Kurz (Tag + Nacht) – *vor der Korrektur der Bildrate (Bilder/s falsch gemessen), Wahrheit: Kopf- und feste Kamera* | – | 0 / 4 (**0 %**) | – | – | – | 0 / 1 | 0 | 29.0 | mit KI | GitHub (ubuntu, 4 Kerne) |

## Einzelheiten pro Phase (letzter Lauf)

**Kurz (Tag + Nacht)** – 2026-10-30 03:24, Motion Watch 2.98.39

| Phase | Pushes richtig / falsch | Personen | Wärmebild | Reaktion | Tiere | Flackern | verpasst, weil … |
|---|---|---|---|---|---|---|---|
| Tag, Wind | 1 / 0 | 6 / 6 | – | 0.2 s | 2 / 2 | 5 | – |
| Nacht mit Infrarot | 1 / 0 | 4 / 4 | – | 1.0 s | 1 / 1 | 6 | – |

