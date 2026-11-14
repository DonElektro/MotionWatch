# Prüfstand – Verlauf der Erkennung

Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.

Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann
für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom
gleichen Rechner, mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde) und mit gleichem Aussehen:
in der Spalte Simulator steht ab 10.11.2026 «Aussehen neu» (Flora-Aussehen mit Grafik Normal, seither Standard) und
«Tiere Modelle» (Tiere mit Skelett) bzw. «Grundformen»; ohne Angabe = das alte Aussehen mit den Grundformen.

**Pushes richtig / falsch** (ab Prüfstand 2): die Push-Nachrichten, die MoveEye wirklich verschickt hat (Test-Postfach der
Simulation). Richtig = eine Person war sichtbar oder im Bild; derselbe Besuch nochmals innert 10 s zählt einmal.
Bei «Ganze Nacht» ist das die Zahl pro Nacht. **Flackern** = jede kurze Personen-Meldung ohne sichtbare Person (hiess
vorher «Fehlalarme»; ein Dachs gab so 3–5 «Fehlalarme» in Sekunden, aber höchstens einen Push).
**Wärmebild**: Personen, die nachts nur die Wärmebildkamera sah (ohne Licht, zu weit fürs Infrarot) – erkannt / sichtbar.
Mehrere Läufe (Zufall 1, 2, 3 … oder Wiederholungen): in Klammern die Streuung (kleinster–grösster Wert pro Lauf).

Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).

| Datum | Motion Watch | Simulator | Testlauf | Pushes richtig / falsch | Personen erkannt | Wärmebild | nah / mittel / weit | Reaktion | Tiere gemeldet | Flackern | Bilder/s | KI | Rechner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-14 05:43 | 3.89.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 4.8 s | 2 / 3 | 6 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-14 04:11 | 3.89.0 | 3.69.0 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 1/1 / 2/2 | 1.0 s | 3 / 3 | 0 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6975P-C |
| 2026-11-14 01:19 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Voller Campingplatz ×3 · Zufall 1,2,3 | **11** / **2** (falsch 0–1 pro Lauf) | 17 / 17 (**100 %**) (100 %) | – | 15/15 / – / 2/2 | 6.1 s | 0 / 0 | 7 | 0.5 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-14 01:19 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Tarnen und Kriechen ×3 · Zufall 1,2,3 | **15** / **0** (falsch 0 pro Lauf) | 50 / 51 (**98 %**) (95–100 %) | 16 / 17 | 34/34 / – / – | 2.5 s | 0 / 0 | 3 | 1.0 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-14 01:19 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Velodieb ×3 · Zufall 1,2,3 | **9** / **3** (falsch 0–2 pro Lauf) | 24 / 28 (**86 %**) (70–100 %) | 1 / 1 | 23/27 / – / – | 3.5 s | 0 / 0 | 18 | 0.7 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-14 01:19 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Gegenstände (Wind, Licht, Lockmittel) ×3 · Zufall 1,2,3 | **9** / **1** (falsch 0–1 pro Lauf) | 9 / 25 (**36 %**) (12–56 %) | 0 / 4 | 8/13 / 1/8 / – | 5.1 s | 7 / 11 | 5 | 0.7 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-14 01:19 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Fahrzeuge in der Nacht (Licht, Blendung, Parkieren) ×3 · Zufall 1,2,3 | **19** / **0** (falsch 0 pro Lauf) | 22 / 29 (**76 %**) (70–80 %) | 11 / 16 | 11/12 / – / 0/1 | 4.6 s | 0 / 0 | 2 | 0.8 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-14 00:06 | 3.87.1 | 3.69.0 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | 1 / 1 | 6/6 / 2/2 / – | 2.3 s | 3 / 3 | 2 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 8 / 10 (**80 %**) | 2 / 2 | 4/5 / 2/3 / – | 4.2 s | 3 / 3 | 2 | 1.0 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Nacht | **4** / **1** | 7 / 7 (**100 %**) | 5 / 5 | 2/2 / – / – | 3.2 s | 3 / 4 | 3 | 1.1 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Standard (Tag, Wind, Nacht, Regen) | **7** / **0** | 17 / 19 (**90 %**) | 5 / 5 | 5/5 / 4/6 / 3/3 | 3.3 s | 8 / 8 | 4 | 1.1 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Ganze Nacht (20–6 Uhr, Zeitraffer) | **1** / **1** pro Nacht | 1 / 1 (**100 %**) | 1 / 1 | – | 4.0 s | 1 / 3 | 1 | 1.1 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Schwierige Bedingungen | **5** / **3** | 16 / 23 (**70 %**) | 3 / 4 | 11/14 / 1/3 / 1/2 | 4.0 s | 8 / 8 | 10 | 1.1 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Voller Campingplatz | **0** / **2** | 0 / 2 (**0 %**) | 0 / 1 | 0/1 / – / – | – | 0 / 0 | 5 | 0.7 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Tarnen und Kriechen | **5** / **0** | 13 / 16 (**81 %**) | 5 / 5 | 8/10 / 0/1 / – | 10.4 s | 0 / 0 | 0 | 1.0 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Velodieb | **0** / **0** | 0 / 4 (**0 %**) | 0 / 4 | – | – | 0 / 0 | 0 | 0.8 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Gegenstände (Wind, Licht, Lockmittel) | **1** / **0** | 1 / 5 (**20 %**) | 0 / 1 | 1/4 / – / – | 8.7 s | 3 / 4 | 1 | 0.8 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 22:00 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Fahrzeuge in der Nacht (Licht, Blendung, Parkieren) | **3** / **1** | 3 / 9 (**33 %**) | 2 / 5 | 1/4 / – / – | 6.2 s | 0 / 0 | 0 | 0.8 | mit KI | HP EliteDesk 800 G1 (4 Kerne) · Intel(R) Core(TM) i5-4590T CPU @ 2.00GHz |
| 2026-11-13 19:39 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.8 s | 3 / 3 | 3 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-13 18:22 | 3.87.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 3.1 s | 3 / 3 | 1 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-13 14:23 | 3.86.1 | 3.68.0 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.6 s | 3 / 3 | 0 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-13 12:36 | 3.86.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.9 s | 3 / 3 | 2 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-12 22:50 | 3.86.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/2 / 0/1 | 1.7 s | 3 / 3 | 6 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 21:28 | 3.85.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/3 / – | 2.0 s | 3 / 3 | 0 | 1.2 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) Platinum 8370C CPU @ 2. |
| 2026-11-12 19:47 | 3.84.2 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 2.8 s | 3 / 3 | 2 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 18:37 | 3.84.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 3.0 s | 3 / 3 | 0 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 17:22 | 3.84.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **4** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.6 s | 3 / 3 | 17 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 15:52 | 3.83.4 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 3 / 3 | 4/4 / 3/3 / – | 2.3 s | 3 / 3 | 3 | 1.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 15:20 | 3.83.3 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/6 / 1/1 / 1/1 | 2.4 s | 3 / 3 | 2 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 14:02 | 3.83.2 | 3.67.2 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.3 s | 2 / 3 | 3 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-12 12:43 | 3.83.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 4/5 / 3/3 / – | 5.0 s | 3 / 3 | 2 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-12 09:33 | 3.83.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/3 / – | 2.7 s | 3 / 3 | 0 | 1.4 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-12 08:54 | 3.82.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 6 / 7 (**86 %**) | 1 / 1 | 4/5 / 1/1 / – | 2.9 s | 2 / 3 | 0 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6973P-C |
| 2026-11-12 08:15 | 3.81.3 | 3.67.2 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/2 / 0/1 | 1.8 s | 2 / 3 | 1 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 08:00 | 3.81.3 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 8 / 10 (**80 %**) | 1 / 2 | 5/5 / 2/3 / – | 1.5 s | 3 / 3 | 2 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 07:08 | 3.81.3 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 1/2 / 1/1 | 2.7 s | 3 / 3 | 2 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 06:51 | 3.81.2 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 8 / 10 (**80 %**) | 2 / 2 | 5/5 / 1/2 / 0/1 | 2.1 s | 3 / 3 | 1 | 1.4 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-12 06:32 | 3.81.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 8 / 10 (**80 %**) | 2 / 3 | 4/4 / 0/1 / 2/2 | 1.7 s | 3 / 3 | 1 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-12 06:12 | 3.81.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 2.9 s | 3 / 3 | 4 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-11 23:18 | 3.80.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 2/2 / – | 3.1 s | 3 / 3 | 2 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-11 22:57 | 3.79.0 | 3.67.1 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 3.1 s | 3 / 3 | 8 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-11 22:39 | 3.78.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/2 / 0/1 | 2.0 s | 3 / 3 | 0 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-11 21:08 | 3.77.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 2 | 1.4 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-11 18:24 | 3.76.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/2 / 0/1 | 4.4 s | 2 / 3 | 0 | 1.2 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) Platinum 8370C CPU @ 2. |
| 2026-11-10 23:17 | 3.76.0 | 3.67.1 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 6/6 / 1/1 / 0/1 | 2.5 s | 2 / 3 | 2 | 1.1 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) Platinum 8370C CPU @ 2. |
| 2026-11-10 22:26 | 3.75.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.5 s | 3 / 3 | 2 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6973P-C |
| 2026-11-10 21:34 | 3.74.0 | 3.67.1 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 2 | 5/5 / 1/1 / 2/2 | 1.0 s | 3 / 3 | 13 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-10 20:32 | 3.73.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 3.7 s | 3 / 3 | 1 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-10 19:49 | 3.72.0 | 3.67.1 · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 2.1 s | 3 / 3 | 2 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-10 16:51 | 3.71.1 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 3.2 s | 3 / 3 | 0 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6973P-C |
| 2026-11-10 08:33 | 3.71.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.3 s | 3 / 3 | 1 | 1.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-10 08:33 | 3.71.0 | ? · Aussehen neu · Tiere Modelle | Kurz (Tag + Nacht) · ohne Kamera-Effekte | **3** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 2.9 s | 3 / 3 | 4 | 1.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-09 21:57 | 3.71.0 | 3.67.1 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 0.9 s | 2 / 3 | 9 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-09 20:17 | 3.70.2 | 3.67.1 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 2.2 s | 3 / 3 | 17 | 3.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-09 19:45 | 3.70.1 | 3.67.1 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | – | 6/6 / 3/3 / – | 1.4 s | 2 / 3 | 6 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-09 19:01 | 3.70.0 | 3.67.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 1.5 s | 3 / 3 | 3 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-09 17:57 | 3.69.2 | 3.67.0 | Kurz (Tag + Nacht) | **1** / **2** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 1/1 / 2/2 | 2.1 s | 2 / 3 | 10 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-09 17:31 | 3.69.2 | 3.66.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 1.8 s | 3 / 3 | 7 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-09 16:50 | 3.69.1 | 3.66.0 | Kurz (Tag + Nacht) | **1** / **2** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 17 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-09 10:47 | 3.69.0 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 5 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-09 07:36 | 3.68.1 | 3.66.0 | Kurz (Tag + Nacht) | **2** / **0** | 9 / 10 (**90 %**) | 2 / 3 | 4/4 / 2/2 / 1/1 | 1.1 s | 3 / 3 | 4 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-09 06:34 | 3.68.0 | 3.66.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.2 s | 3 / 3 | 3 | 2.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-09 05:45 | 3.67.0 | 3.66.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 2.1 s | 3 / 3 | 7 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 23:22 | 3.66.1 | 3.66.0 | Kurz (Tag + Nacht) | **3** / **1** | 9 / 9 (**100 %**) | 2 / 2 | 5/5 / 1/1 / 1/1 | 1.3 s | 3 / 3 | 5 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 21:41 | 3.66.0 | 3.66.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 0.9 s | 3 / 3 | 3 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 20:22 | 3.65.0 | ? | Kurz (Tag + Nacht) | **1** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 4/5 / 2/2 / 1/1 | 1.0 s | 3 / 3 | 2 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 19:36 | 3.64.0 | 3.65.1 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 0.7 s | 3 / 3 | 11 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 18:43 | 3.64.0 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 3.0 s | 2 / 3 | 7 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 18:11 | 3.64.0 | 3.63.0 | Kurz (Tag + Nacht) | **4** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 1.6 s | 3 / 3 | 2 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 16:58 | 3.63.2 | 3.63.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 1.4 s | 2 / 3 | 6 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 16:20 | 3.63.2 | 3.62.1 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 2.4 s | 2 / 3 | 4 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 16:10 | 3.63.2 | 3.62.1 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 0.9 s | 3 / 3 | 7 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 15:34 | 3.63.2 | 3.62.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 1.1 s | 3 / 3 | 10 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-08 15:12 | 3.63.2 | ? | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 1/1 / 1/1 | 1.2 s | 2 / 3 | 4 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 08:59 | 3.63.2 | 3.60.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 1/1 / 1/1 | 1.6 s | 2 / 2 | 11 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Kurz (Tag + Nacht) ×3 · Zufall 1,2,3 | **7** / **2** (falsch 0–1 pro Lauf) | 29 / 29 (**100 %**) (100 %) | 5 / 5 | 16/16 / 5/5 / 3/3 | 1.5 s | 9 / 9 | 26 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Nacht ×3 · Zufall 1,2,3 | **10** / **3** (falsch 1 pro Lauf) | 21 / 21 (**100 %**) (100 %) | 15 / 15 | 6/6 / – / – | 2.0 s | 12 / 13 | 19 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Standard (Tag, Wind, Nacht, Regen) ×3 · Zufall 1,2,3 | **20** / **2** (falsch 0–1 pro Lauf) | 57 / 57 (**100 %**) (100 %) | 15 / 15 | 14/14 / 21/21 / 7/7 | 1.5 s | 23 / 24 | 26 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Ganze Nacht (20–6 Uhr, Zeitraffer) ×3 · Zufall 1,2,3 | **3** / **13** (falsch 4–5 pro Lauf) in 3 Nächten (Ø 1.0 / 4.3 pro Nacht) | 3 / 3 (**100 %**) (100 %) | 3 / 3 | – | 4.7 s | 9 / 13 | 37 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Schwierige Bedingungen ×3 · Zufall 1,2,3 | **26** / **4** (falsch 0–3 pro Lauf) | 70 / 78 (**90 %**) (88–92 %) | 12 / 12 | 37/39 / 19/23 / 2/4 | 2.8 s | 14 / 21 | 17 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Voller Campingplatz ×3 · Zufall 1,2,3 | **12** / **0** (falsch 0 pro Lauf) | 18 / 18 (**100 %**) (100 %) | – | 16/16 / 2/2 / – | 4.6 s | 0 / 0 | 10 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Tarnen und Kriechen ×3 · Zufall 1,2,3 | **13** / **1** (falsch 0–1 pro Lauf) | 51 / 53 (**96 %**) (94–100 %) | 16 / 18 | 34/34 / 1/1 / – | 2.6 s | 0 / 0 | 6 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Velodieb ×3 · Zufall 1,2,3 | **1** / **2** (falsch 0–1 pro Lauf) | 2 / 8 (**25 %**) (0–100 %) | 0 / 5 | – / 2/3 / – | 0.8 s | 0 / 0 | 24 | 2.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Gegenstände (Wind, Licht, Lockmittel) ×3 · Zufall 1,2,3 | **9** / **2** (falsch 0–1 pro Lauf) | 13 / 24 (**54 %**) (38–75 %) | 2 / 3 | 6/13 / 5/8 / – | 5.8 s | 11 / 16 | 2 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 02:58 | 3.63.2 | 3.59.0 | Fahrzeuge in der Nacht (Licht, Blendung, Parkieren) ×3 · Zufall 1,2,3 | **17** / **2** (falsch 0–1 pro Lauf) | 29 / 30 (**97 %**) (90–100 %) | 17 / 18 | 12/12 / – / – | 1.5 s | 0 / 0 | 11 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-08 00:04 | 3.63.2 | 3.59.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.3 s | 2 / 3 | 10 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-07 23:13 | 3.62.1 | 3.58.0 | Kurz (Tag + Nacht) ×3 · Zufall 1,2,3 | **8** / **1** (falsch 0–1 pro Lauf) | 29 / 30 (**97 %**) (90–100 %) | 3 / 3 | 18/18 / 7/7 / 1/2 | 1.1 s | 8 / 9 | 20 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-07 23:13 | 3.62.1 | 3.58.0 | Kurz (Tag + Nacht) · ohne Kamera-Effekte ×3 · Zufall 1,2,3 | **9** / **0** (falsch 0 pro Lauf) | 29 / 29 (**100 %**) (100 %) | 4 / 4 | 16/16 / 5/5 / 4/4 | 1.5 s | 9 / 9 | 13 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-07 22:42 | 3.62.1 | 3.58.0 | Kurz (Tag + Nacht) | **1** / **1** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 1/2 / 1/1 | 0.9 s | 2 / 3 | 10 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6973P-C |
| 2026-11-07 22:05 | 3.62.1 | 3.57.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / – / 2/2 | 1.0 s | 3 / 3 | 5 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-07 21:31 | 3.62.0 | 3.57.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.1 s | 3 / 3 | 9 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-07 20:41 | 3.61.0 | 3.57.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.5 s | 2 / 2 | 10 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-07 19:12 | 3.60.0 | 3.56.0 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/2 / 0/1 | 2.2 s | 2 / 3 | 3 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-07 18:02 | 3.59.0 | 3.56.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.8 s | 3 / 3 | 7 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-07 15:58 | 3.58.0 | 3.56.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 2/2 / – | 1.7 s | 3 / 3 | 8 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-07 11:54 | 3.57.0 | 3.56.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 2 | 5/5 / 2/2 / 1/1 | 1.6 s | 2 / 2 | 7 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-07 10:20 | 3.56.0 | 3.56.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 5/5 / 3/3 / 1/1 | 2.4 s | 2 / 3 | 8 | 2.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-03 20:34 | 3.55.2 | 3.55.2 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 9 (**100 %**) | – | 6/6 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 10 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6975P-C |
| 2026-11-03 14:38 | 3.55.1 | 3.55.1 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 2 | 5/5 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 0 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-03 00:13 | 3.55.0 | 3.55.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 2 | 5/5 / 1/1 / 2/2 | 1.1 s | 3 / 3 | 0 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6975P-C |
| 2026-11-02 22:48 | 3.54.0 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 4 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-02 21:47 | 3.53.0 | ? | Kurz (Tag + Nacht) | **1** / **2** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.6 s | 3 / 3 | 9 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-02 20:00 | 3.52.0 | ? | Kurz (Tag + Nacht) | **1** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 1.0 s | 3 / 3 | 6 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-02 16:57 | 3.51.0 | 3.51.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.0 s | 3 / 3 | 1 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-02 08:21 | 3.50.0 | 3.50.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 1/1 / 2/2 | 1.5 s | 3 / 3 | 11 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-02 05:34 | 3.49.0 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 1/1 / 2/2 | 1.4 s | 3 / 3 | 2 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 23:07 | 3.48.1 | 3.48.1 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/3 / – | 3.3 s | 3 / 3 | 0 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-11-01 22:43 | 3.48.0 | 3.48.0 | Kurz (Tag + Nacht) | **2** / **0** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 3/3 / – | 1.7 s | 3 / 3 | 2 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-01 22:23 | 3.47.0 | ? | Kurz (Tag + Nacht) | **2** / **0** | 9 / 10 (**90 %**) | 0 / 1 | 6/6 / 2/2 / 1/1 | 2.1 s | 3 / 3 | 7 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-01 20:42 | 3.46.0 | 3.46.0 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.1 s | 3 / 3 | 7 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 19:42 | 3.45.0 | ? | Kurz (Tag + Nacht) | **1** / **1** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 4 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 17:59 | 3.44.2 | ? | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 1/1 / 2/2 | 1.4 s | 3 / 3 | 11 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 17:33 | 3.44.0 | 3.44.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 0 / 1 | 6/6 / 3/3 / – | 2.7 s | 3 / 3 | 9 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 17:08 | 3.43.1 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 2/2 / – | 3.3 s | 2 / 3 | 6 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 16:54 | 3.43.0 | ? | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.9 s | 3 / 3 | 1 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 16:44 | 3.42.0 | ? | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 3.2 s | 3 / 3 | 7 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 13:18 | 3.41.0 | 3.41.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 1/2 / 1/1 | 3.3 s | 3 / 3 | 17 | 1.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 12:51 | 3.40.0 | 3.40.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 2.8 s | 2 / 2 | 2 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 12:30 | 3.39.2 | 3.39.2 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 1/1 / 2/2 | 1.3 s | 3 / 3 | 6 | 2.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 12:14 | 3.39.1 | ? | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / 2/2 / – | 1.6 s | 2 / 3 | 11 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 11:38 | 3.39.0 | 3.39.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 15 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 11:07 | 3.37.0 | 3.37.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 2.5 s | 2 / 3 | 6 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-11-01 10:49 | 3.33.0 | 3.33.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.8 s | 3 / 3 | 11 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 10:33 | 3.30.0 | 3.30.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/3 / – | 1.6 s | 2 / 3 | 4 | 3.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Kurz (Tag + Nacht) ×3 · Zufall 1,2,3 | **7** / **1** (falsch 0–1 pro Lauf) | 25 / 28 (**89 %**) (89–90 %) | 4 / 5 | 15/15 / 3/4 / 3/4 | 2.4 s | 5 / 9 | 13 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Nacht ×3 · Zufall 1,2,3 | **12** / **3** (falsch 0–2 pro Lauf) | 22 / 22 (**100 %**) (100 %) | 16 / 16 | 6/6 / – / – | 2.6 s | 12 / 14 | 19 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Standard (Tag, Wind, Nacht, Regen) ×3 · Zufall 1,2,3 | **19** / **3** (falsch 1 pro Lauf) | 53 / 56 (**95 %**) (94–95 %) | 15 / 15 | 15/15 / 17/20 / 6/6 | 3.6 s | 20 / 24 | 19 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Ganze Nacht (20–6 Uhr, Zeitraffer) ×3 · Zufall 1,2,3 | **2** / **14** (falsch 4–6 pro Lauf) in 3 Nächten (Ø 0.7 / 4.7 pro Nacht) | 3 / 3 (**100 %**) (100 %) | 3 / 3 | – | 1.6 s | 11 / 13 | 51 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Schwierige Bedingungen ×3 · Zufall 1,2,3 | **25** / **3** (falsch 0–2 pro Lauf) | 76 / 78 (**97 %**) (96–100 %) | 11 / 11 | 42/42 / 20/22 / 3/3 | 3.9 s | 23 / 25 | 25 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Voller Campingplatz ×3 · Zufall 1,2,3 | **10** / **2** (falsch 0–2 pro Lauf) | 18 / 18 (**100 %**) (100 %) | – | 17/17 / 1/1 / – | 4.8 s | 0 / 0 | 11 | 1.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Tarnen und Kriechen ×3 · Zufall 1,2,3 | **13** / **0** (falsch 0 pro Lauf) | 55 / 56 (**98 %**) (95–100 %) | 19 / 20 | 36/36 / – / – | 2.2 s | 0 / 0 | 1 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Velodieb ×3 · Zufall 1,2,3 | **11** / **2** (falsch 0–1 pro Lauf) | 30 / 30 (**100 %**) (100 %) | – | 30/30 / – / – | 2.8 s | 0 / 0 | 3 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Gegenstände (Wind, Licht, Lockmittel) ×3 · Zufall 1,2,3 | **7** / **0** (falsch 0 pro Lauf) | 11 / 24 (**46 %**) (25–62 %) | 1 / 3 | 5/15 / 5/6 / – | 5.8 s | 8 / 12 | 6 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:55 | 3.29.0 | 3.29.0 | Fahrzeuge in der Nacht (Licht, Blendung, Parkieren) ×3 · Zufall 1,2,3 | **12** / **7** (falsch 1–4 pro Lauf) | 28 / 32 (**88 %**) (83–90 %) | 17 / 18 | 11/12 / – / 0/2 | 1.4 s | 0 / 0 | 27 | 2.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 02:11 | 3.29.0 | 3.29.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 6/6 / – / 2/2 | 1.7 s | 3 / 3 | 2 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 01:55 | 3.28.1 | 3.28.1 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.0 s | 2 / 2 | 7 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 01:31 | 3.27.0 | 3.27.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.5 s | 2 / 3 | 6 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 01:00 | 3.26.0 | 3.26.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 00:41 | 3.25.0 | 3.25.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/2 / 0/1 | 4.2 s | 2 / 3 | 2 | 3.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-11-01 00:26 | 3.24.0 | 3.24.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/3 / – | 1.0 s | 2 / 3 | 8 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-11-01 00:11 | 3.23.1 | 3.23.1 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 1/1 / 1/2 | 3.2 s | 1 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 23:50 | 3.23.0 | 3.23.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.8 s | 2 / 3 | 4 | 2.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 23:22 | 3.22.0 | 3.22.0 | Kurz (Tag + Nacht) | **1** / **2** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 1.8 s | 2 / 3 | 7 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 23:02 | 3.21.0 | 3.21.0 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.1 s | 3 / 3 | 3 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 22:50 | 3.20.0 | 3.20.0 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.5 s | 2 / 3 | 1 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 22:29 | 3.19.3 | 3.19.3 | Kurz (Tag + Nacht) | **2** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 5/6 / 2/2 / 1/1 | 2.4 s | 1 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 21:59 | 3.19.2 | 3.19.2 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.0 s | 2 / 3 | 6 | 3.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 21:40 | 3.19.0 | 3.19.0 | Kurz (Tag + Nacht) | **2** / **1** | 8 / 9 (**89 %**) | 1 / 1 | 5/5 / 2/3 / – | 2.2 s | 2 / 3 | 4 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 21:29 | 3.18.0 | 3.18.0 | Kurz (Tag + Nacht) | **2** / **0** | 7 / 9 (**78 %**) | – | 5/6 / 2/3 / – | 4.8 s | 2 / 3 | 0 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 21:12 | 3.16.0 | 3.16.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/3 / – | 1.3 s | 1 / 3 | 1 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 20:54 | 3.15.1 | 3.15.1 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 10 (**90 %**) | 2 / 3 | 4/4 / 2/2 / 1/1 | 1.2 s | 2 / 3 | 7 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 20:13 | 3.15.0 | 3.15.0 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 1.6 s | 2 / 3 | 3 | 3.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 19:58 | 3.14.0 | 3.14.0 | Kurz (Tag + Nacht) | **1** / **1** | 9 / 10 (**90 %**) | 2 / 2 | 4/5 / 2/2 / 1/1 | 1.4 s | 2 / 3 | 5 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 19:35 | 3.12.0 | 3.12.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 5.2 s | 2 / 3 | 5 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 19:12 | 3.11.1 | 3.11.1 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.2 s | 3 / 3 | 2 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 18:54 | 3.11.0 | 3.11.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 5/5 / 2/2 / 0/1 | 1.2 s | 3 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 18:45 | 3.10.1 | 3.10.1 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.0 s | 2 / 3 | 2 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 18:27 | 3.9.2 | 3.9.2 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 0.8 s | 2 / 3 | 4 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 17:17 | 3.9.0 | 3.9.0 | Kurz (Tag + Nacht) | **1** / **1** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 0.9 s | 3 / 3 | 6 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 16:33 | 3.7.0 | 3.7.0 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.1 s | 3 / 3 | 5 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 16:16 | 3.6.1 | 3.6.1 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 3/3 / – | 1.4 s | 3 / 3 | 3 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 15:55 | 3.4.0 | 3.4.0 | Kurz (Tag + Nacht) | **4** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 1/1 / 2/2 | 2.3 s | 3 / 3 | 0 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 15:46 | 3.3.0 | 3.3.0 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 3/3 / – | 0.9 s | 3 / 3 | 4 | 3.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 15:38 | 3.2.0 | 3.2.0 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 0.7 s | 3 / 3 | 12 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 15:19 | 3.0.2 | 3.0.2 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 2.2 s | 3 / 3 | 5 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 15:10 | 3.0.1 | 3.0.1 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 1/2 / 1/1 | 1.6 s | 3 / 3 | 6 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 15:00 | 3.0.0 | 3.0.0 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | – | 6/6 / 2/2 / 1/1 | 1.7 s | 2 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 14:49 | 2.98.116 | 3D-4.85 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 1 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 14:35 | 2.98.115 | 3D-4.84 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/2 / 0/1 | 3.0 s | 3 / 3 | 2 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 14:17 | 2.98.114 | 3D-4.83 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 0.3 s | 3 / 3 | 8 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 13:57 | 2.98.113 | 3D-4.82 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 4/5 / 2/2 / 1/1 | 1.0 s | 3 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 13:39 | 2.98.111 | 3D-4.80 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.2 s | 3 / 3 | 10 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 13:19 | 2.98.110 | 3D-4.79 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 2 / 2 | 4/5 / 2/2 / 1/1 | 1.5 s | 2 / 3 | 4 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 13:02 | 2.98.108 | 3D-4.77 | Kurz (Tag + Nacht) | **1** / **2** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.0 s | 3 / 3 | 12 | 2.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 12:45 | 2.98.106 | 3D-4.75 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 3/3 / – | 1.1 s | 3 / 3 | 7 | 3.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 12:31 | 2.98.105 | 3D-4.74 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 4 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 12:13 | 2.98.103 | 3D-4.72 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 9 (**100 %**) | 1 / 1 | 5/5 / 2/2 / 1/1 | 2.2 s | 3 / 3 | 7 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 11:56 | 2.98.101 | 3D-4.70 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 3/3 / – | 0.6 s | 3 / 3 | 8 | 2.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 11:38 | 2.98.98 | 3D-4.67 | Kurz (Tag + Nacht) | **1** / **2** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 2/3 / – | 1.2 s | 3 / 3 | 7 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 11:22 | 2.98.96 | 3D-4.65 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.6 s | 3 / 3 | 2 | 2.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 11:05 | 2.98.94 | 3D-4.63 | Kurz (Tag + Nacht) | **2** / **0** | 9 / 10 (**90 %**) | 2 / 3 | 4/4 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 2 | 1.8 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) Platinum 8370C CPU @ 2. |
| 2026-10-31 10:46 | 2.98.92 | 3D-4.61 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 2.9 s | 2 / 3 | 5 | 3.4 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 10:31 | 2.98.90 | 3D-4.59 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.5 s | 3 / 3 | 3 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 07:59 | 2.98.88 | 3D-4.57 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.0 s | 2 / 3 | 3 | 3.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 07:45 | 2.98.86 | 3D-4.55 | Kurz (Tag + Nacht) | **3** / **1** | 10 / 10 (**100 %**) | 1 / 1 | 6/6 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 5 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 07:32 | 2.98.83 | 3D-4.52 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | 2 / 2 | 5/5 / 2/2 / 1/1 | 1.6 s | 2 / 3 | 4 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6975P-C |
| 2026-10-31 07:18 | 2.98.81 | 3D-4.50 | Kurz (Tag + Nacht) | **3** / **0** | 8 / 9 (**89 %**) | 1 / 1 | 5/5 / 1/2 / 1/1 | 0.9 s | 3 / 3 | 3 | 3.3 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 07:04 | 2.98.78 | ? | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 1/2 / 1/1 | 3.4 s | 4 / 4 | 2 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 06:50 | 2.98.76 | 3D-4.45 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 7 | 2.2 | mit KI | GitHub (ubuntu, 4 Kerne) · INTEL(R) XEON(R) PLATINUM 8573C |
| 2026-10-31 06:37 | 2.98.74 | 3D-4.43 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.4 s | 3 / 3 | 15 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 06:22 | 2.98.72 | 3D-4.41 | Kurz (Tag + Nacht) | **4** / **0** | 9 / 10 (**90 %**) | – | 6/7 / 2/2 / 1/1 | 1.4 s | 3 / 4 | 3 | 3.2 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 06:08 | 2.98.70 | 3D-4.39 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 8 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 05:50 | 2.98.68 | 3D-4.37 | Kurz (Tag + Nacht) | **2** / **2** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 4.5 s | 4 / 4 | 6 | 2.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 05:41 | 2.98.67 | 3D-4.36 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 2 | 5/5 / 2/2 / 1/1 | 4.2 s | 2 / 3 | 8 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 05:30 | 2.98.66 | 3D-4.35 | Kurz (Tag + Nacht) | **3** / **1** | 8 / 10 (**80 %**) | – | 6/7 / 1/1 / 1/2 | 2.0 s | 3 / 3 | 17 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 05:21 | 2.98.65 | 3D-4.34 | Kurz (Tag + Nacht) | **2** / **2** | 9 / 10 (**90 %**) | – | 6/7 / 3/3 / – | 2.3 s | 3 / 3 | 9 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 05:09 | 2.98.64 | 3D-4.33 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 2/2 / 0/1 | 1.3 s | 3 / 4 | 2 | 3.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-31 05:01 | 2.98.63 | 3D-4.32 | Kurz (Tag + Nacht) | **3** / **0** | 8 / 10 (**80 %**) | – | 7/8 / 0/1 / 1/1 | 4.4 s | 1 / 3 | 5 | 1.9 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) Platinum 8370C CPU @ 2. |
| 2026-10-31 04:47 | 2.98.61 | 3D-4.30 | Kurz (Tag + Nacht) | **1** / **3** | 10 / 10 (**100 %**) | – | 7/7 / 3/3 / – | 1.4 s | 3 / 3 | 10 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 04:29 | 2.98.60 | 3D-4.29 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 6/7 / 3/3 / – | 4.1 s | 2 / 3 | 4 | 2.1 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 03:48 | 2.98.59 | 3D-4.28 | Kurz (Tag + Nacht) | **1** / **1** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.1 s | 3 / 3 | 9 | 2.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 03:23 | 2.98.58 | 3D-4.27 | Kurz (Tag + Nacht) | **2** / **1** | 9 / 10 (**90 %**) | – | 6/7 / 2/2 / 1/1 | 2.0 s | 3 / 3 | 6 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 03:01 | 2.98.57 | 3D-4.26 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | 1 / 1 | 6/6 / 1/2 / 1/1 | 4.9 s | 2 / 3 | 2 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-31 02:53 | 2.98.56 | 3D-4.25 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 3/3 / – | 1.0 s | 3 / 3 | 8 | 2.6 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-31 02:41 | 2.98.55 | 3D-4.25 | Kurz (Tag + Nacht) | **3** / **0** | 8 / 10 (**80 %**) | – | 6/8 / 1/1 / 1/1 | 1.6 s | 3 / 3 | 11 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 23:49 | 2.98.54 | 3D-4.24 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | – | 7/7 / 3/3 / – | 2.8 s | 3 / 3 | 9 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 23:22 | 2.98.53 | 3D-4.24 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 6/7 / 3/3 / – | 2.4 s | 3 / 3 | 7 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-30 22:47 | 2.98.52 | 3D-4.23 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 7/7 / 1/2 / 1/1 | 4.6 s | 2 / 3 | 0 | 2.7 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V74 |
| 2026-10-30 22:26 | 2.98.51 | 3D-4.22 | Kurz (Tag + Nacht) | **3** / **0** | 9 / 10 (**90 %**) | – | 7/8 / 1/1 / 1/1 | 4.6 s | 2 / 3 | 1 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 22:02 | 2.98.50 | 3D-4.21 | Kurz (Tag + Nacht) | **4** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 4.1 s | 0 / 4 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 19:48 | 2.98.49 | 3D-4.20 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.9 s | 4 / 4 | 0 | 2.0 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 12:46 | 2.98.48 | 3D-4.19 | Kurz (Tag + Nacht) | **4** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 0.9 s | 3 / 3 | 4 | 3.7 | mit KI | GitHub (ubuntu, 4 Kerne) · Intel(R) Xeon(R) 6973P-C |
| 2026-10-30 11:47 | 2.98.47 | 3D-4.18 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 2.1 s | 3 / 3 | 7 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 09:02 | 2.98.46 | 3D-4.17 | Kurz (Tag + Nacht) | **2** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 1/1 / 2/2 | 0.4 s | 3 / 3 | 10 | 2.9 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 04:30 | 2.98.44 | 3D-4.15 | Kurz (Tag + Nacht) | **3** / **0** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 2.9 s | 3 / 3 | 5 | 2.8 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 7763 |
| 2026-10-30 04:06 | 2.98.43 | 3D-4.14 | Kurz (Tag + Nacht) | **3** / **0** | 8 / 8 (**100 %**) | – | 5/5 / 2/2 / 1/1 | 1.2 s | 3 / 3 | 10 | 4.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-30 03:52 | 2.98.42 | 3D-4.13 | Kurz (Tag + Nacht) | **2** / **1** | 10 / 10 (**100 %**) | – | 7/7 / 2/2 / 1/1 | 1.3 s | 3 / 3 | 13 | 4.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
| 2026-10-30 03:44 | 2.98.41 | 3D-4.12 | Kurz (Tag + Nacht) | **1** / **1** | 9 / 10 (**90 %**) | – | 6/7 / 2/2 / 1/1 | 0.7 s | 3 / 3 | 6 | 4.5 | mit KI | GitHub (ubuntu, 4 Kerne) · AMD EPYC 9V45 |
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

**Kurz (Tag + Nacht)** – 2026-11-14 05:43, Motion Watch 3.89.1

| Phase | Pushes richtig / falsch | Personen | Wärmebild | Reaktion | Tiere | Flackern | verpasst, weil … |
|---|---|---|---|---|---|---|---|
| Tag, Wind | 2 / 0 | 6 / 6 | – | 7.2 s | 2 / 2 | 6 | – |
| Nacht mit Infrarot | 1 / 0 | 4 / 4 | 2 / 2 | 1.3 s | 0 / 1 | 0 | – |

