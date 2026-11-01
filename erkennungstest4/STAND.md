# Erkennung 4 – Zwischenstand (pausiert 01.11.2026 ~17:05)

- Code-Fix im Zweig (5042c16, CI grün): Auto-Tune min_area ≤ 0.9 % des Bildes, Stetigkeit ≤ 0.5, kein Start mit Extremwerten;
  Wind nur letzte 2 Min. und mind. 2 Böen; KI-Person bei Dämmerung/Wind sofort («Person?»); aufrechte KI-Person nie «Tier».
- Gemessen (main 3.35, Sim 3.8.0, 14 verlorene + 2 weitere Personenfälle, je 2×): **9/32 = 28 %**. Ursache aus Spuren:
  min_area nach Kalibrierung ~3150 auch bei sauberem Start (Rauschen beim Ortswechsel) → keine Bewegungsspur; und
  Wind-Regel (n=2) nach 45 s Wind 55 → KI-Personen (1 KI-Treffer) nie bestätigt; einzelne Kinder als «horse/animal».
- Noch NICHT gemessen: Fix (fix2), t1, alle, Einzel-Schalter, Scheinwerfer/Wind-leer-Diagnose (diag4.py), Test 3.
  Grund: Rechner durch andere Helfer belegt (Last 7–11, MoveEye 1.3–2.3 Bilder/s).
- Weiter: Sim starten (start_sim.sh, Sim 3.8.0 in /tmp/claude-0/erkt4/sim38), dann `bash plan2.sh` (a fertig wird übersprungen).
  Test-Schalter-Bau: /tmp/claude-0/wt_erk4t (main 3.35 + testschalter + wind/dusk/reh/start/nup/size).
