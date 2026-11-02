# Erkennung 4 – Stand 02.11.2026 02:15

- Test 3 (72 Vergleichsfälle, Sim 3.8.0): Personen vorher (main) 15/36 = 42 %, nachher (Zweig) 25/36 = 69 %;
  Tier/Auto als Person 4 -> 6 von 24; falsche Personen-Pushes 12/h -> 16/h. Bericht: bericht3.md.
- Ursache (16 verlorene Fälle, je 2×): main 9/32 = 28 %, Fix 26/32 = 81 %. Gründe: min_area nach Kalibrierung ~3150,
  Wind-Regel 10 Min. scharf und 2 KI-Treffer nötig, Kinder als «horse/animal».
- Schwach bleibt: Kriechen am Tag (4/12), verdeckte Wege im Camping-Platz.
- Nicht gemessen: Einzel-Schalter (t1, alle, wind, tier) – Zeit; plan2.sh macht sie am Schluss.
