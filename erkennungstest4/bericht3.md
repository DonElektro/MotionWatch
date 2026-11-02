# Erkennungstest 3 (01.11.2026)

MoveEye vorher = main (Erkennung wie 3.45.0), nachher = Zweig `real-erkennung-fix`. Simulator 3.8.0 (wie Test 2), gleiche Fälle,
je Fall ein Lauf, bei Personen feste Bedingungen wie Test 2 (zuerst 45 s Wind 55 km/h). MoveEye mit Vorrang (nice -10),
weil andere Helfer den Rechner zeitweise belegten (Last bis 6); Bilder/s je Fall in results.jsonl.

## 72 Vergleichsfälle (Camping, Schattwald, Stellplatz)

| | Test 1 (2.98.110) | Test 2 (3.8.0) | vorher (main) | nachher (Fix) |
|---|---|---|---|---|
| Person geht | 10/12 (83 %) | 7/12 (58 %) | 7/12 (58 %) | 10/12 (83 %) |
| Person kriecht | 7/12 (58 %) | 4/12 (33 %) | 1/12 (8 %) | 4/12 (33 %) |
| Kind | 10/12 (83 %) | 5/12 (42 %) | 7/12 (58 %) | 11/12 (92 %) |
| **Personen gesamt** | **27/36 (75 %)** | **16/36 (44 %)** | **15/36 (42 %)** | **25/36 (69 %)** |
| Tier / Auto als Person | 8/24 (33 %) | 1/24 (4 %) | 4/24 (17 %) | 6/24 (25 %) |
| Tier / Auto: Personen-Pushes | 4 | 1 | 3 | 3 |
| Leerlauf: «Person» / falsche Pushes | 10 / 2 | 5 / 1 | 1 / 0 | 2 / 1 |
| Tier als Tier | 3/12 (25 %) | 3/12 (25 %) | 5/12 (42 %) | 4/12 (33 %) |
| Auto als Fahrzeug | 2/12 (17 %) | 1/12 (8 %) | 1/12 (8 %) | 1/12 (8 %) |

Falsche Personen-Pushes (Leerlauf + Tier/Auto, 15 Min.): vorher 3 (12/h), nachher 4 (16/h).

## Neue Orte und Sonderfälle

| Fall | vorher | nachher |
|---|---|---|
| baustelle|nacht|fahrzeug | nur Bewegung | nur Bewegung |
| baustelle|nacht|gehen | ✔ 5.7s | ✔ 7.8s |
| baustelle|nacht|kind | ✔ 3.1s | ✔ 3.1s |
| baustelle|nacht|kriechen | ✔ 17.9s | ✔ 11.7s |
| baustelle|nacht|leer | 0×P 0 Push | 0×P 0 Push |
| baustelle|nacht|tier | – | – |
| camping|dunkel|fahrzeug | nur Bewegung | nur Bewegung |
| camping|dunkel|gehen | ✔ 9.3s | ✔ 11.7s |
| camping|dunkel|kind | ✘ – | ✘ – |
| camping|dunkel|kriechen | ✔ 7.8s | ✘ – |
| camping|dunkel|leer | 0×P 0 Push | 0×P 0 Push |
| camping|dunkel|tier | – | – |
| camping|kopf|gehen | ✔ 6.4s · Schwenk -30.4→-0.8 | ✔ 15.4s · Schwenk -26.0→71.8 |
| camping|kopf|leer | 11×P 2 Push · Schwenk -31.0…-0.3 | 7×P 2 Push · Schwenk -30.9…-29.3 |
| festival|nacht|fahrzeug | truck | ⚠Person |
| festival|nacht|gehen | ✔ 4.7s | ✔ 4.8s |
| festival|nacht|kind | ✔ 4.2s | ✔ 4.2s |
| festival|nacht|kriechen | ✔ 2.7s | ✔ 4.8s |
| festival|nacht|leer | 1×P 0 Push | 1×P 1 Push |
| festival|nacht|tier | ⚠Person 1 Push | ⚠Person 1 Push |
| festival|tag|fahrzeug | airplane, boat | boat |
| festival|tag|gehen | ✔ 9.1s | ✔ 5.8s |
| festival|tag|kind | ✔ 6.3s | ✔ 4.2s |
| festival|tag|kriechen | ✔ 14.6s | ✔ 5.2s |
| festival|tag|leer | 0×P 0 Push | 4×P 1 Push |
| festival|tag|tier | – | ⚠Person 1 Push |
| garten|nachtregen|fahrzeug | ⚠Person | ⚠Person |
| garten|nachtregen|gehen | ✔ 0.6s | ✔ 1.6s |
| garten|nachtregen|kind | ✔ 0.0s | ✔ 3.2s |
| garten|nachtregen|kriechen | ✔ 3.1s | ✔ 5.2s |
| garten|nachtregen|leer | 4×P 1 Push | 8×P 1 Push |
| garten|nachtregen|tier | ⚠Person | ⚠Person |
| garten|tag|fahrzeug | ⚠Person | ⚠Person |
| garten|tag|gehen | ✔ 1.1s | ✔ 7.4s |
| garten|tag|kind | ✔ 3.2s | ✔ 3.7s |
| garten|tag|kriechen | ✔ 9.8s | ✔ 4.7s |
| garten|tag|leer | 1×P 1 Push | 6×P 1 Push |
| garten|tag|tier | – | ⚠Person |
| schlafzimmer|nacht|hamster | – | – |
| schlafzimmer|nacht|leer | 0×P 0 Push | 0×P 0 Push |
| schlafzimmer|nacht|spinne | – | nur Bewegung |
| schlafzimmer|tag|leer | 1×P 0 Push | 1×P 1 Push |
| schlafzimmer|tag|vogel | ⚠Person 1 Push | ⚠Person |
| stellplatz|nacht_blend|gehen | ✔ 0.6s | ✔ 1.1s |
| stellplatz|nacht_blend|leer | 6×P 0 Push | 12×P 0 Push |
| stellplatz|tag_blend|gehen | ✔ 7.3s | ✔ 0.6s |
| stellplatz|tag_blend|leer | 6×P 1 Push | 7×P 1 Push |
| wild|nacht|fahrzeug | nur Bewegung | ⚠Person |
| wild|nacht|gehen | ✔ 9.8s | ✔ 5.3s |
| wild|nacht|kind | ✔ 2.1s | ✔ 4.7s |
| wild|nacht|kriechen | ✔ 10.5s | ✔ 1.1s |
| wild|nacht|leer | 0×P 1 Push | 1×P 1 Push |
| wild|nacht|tier | – 1 Push | – |
| wild|tag|fahrzeug | – | nur Bewegung |
| wild|tag|gehen | ✔ 6.8s | ✔ 7.8s |
| wild|tag|kind | ✘ – | ✔ 3.7s |
| wild|tag|kriechen | ✔ 4.7s | ✔ 1.7s |
| wild|tag|leer | 2×P 0 Push | 0×P 0 Push |
| wild|tag|tier | ⚠Person 1 Push | ⚠Person 1 Push |

Neue Orte: Personen vorher 25/27 (93 %), nachher 25/27 (93 %); Tier/Auto als Person vorher 6/19 (32 %), nachher 10/19 (53 %); Leerlauf-Pushes vorher 6, nachher 9.

## Alle 72 Vergleichsfälle

| Fall | Test 2 | vorher | nachher |
|---|---|---|---|
| camping|daemmerung|fahrzeug | nur Bewegung | truck | – |
| camping|daemmerung|gehen | ✔ 11.1s | ✘ nur Bewegung | ✔ 13.8s |
| camping|daemmerung|kind | ✘ – | ✘ – | ✘ nur Bewegung |
| camping|daemmerung|kriechen | ✔ 4.1s | ✘ – | ✔ 12.7s |
| camping|daemmerung|leer | 2×P 0 Push | 1×P 0 Push | 0×P 0 Push |
| camping|daemmerung|tier | – | – | nur Bewegung |
| camping|nacht|fahrzeug | nur Bewegung | nur Bewegung | nur Bewegung |
| camping|nacht|gehen | ✘ nur Bewegung | ✔ 8.0s | ✔ 9.3s |
| camping|nacht|kind | ✘ – | ✘ animal, sheep | ✔ 3.2s |
| camping|nacht|kriechen | ✘ – | ✘ truck | ✘ animal, sheep |
| camping|nacht|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| camping|nacht|tier | – | animal, sheep | animal, sheep |
| camping|regen|fahrzeug | nur Bewegung | nur Bewegung | ⚠Person |
| camping|regen|gehen | ✘ – | ✘ – | ✘ – |
| camping|regen|kind | ✘ nur Bewegung | ✘ nur Bewegung | ✔ 7.3s |
| camping|regen|kriechen | ✘ nur Bewegung | ✘ – | ✘ – |
| camping|regen|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| camping|regen|tier | – | nur Bewegung | – |
| camping|tag|fahrzeug | nur Bewegung | nur Bewegung | – |
| camping|tag|gehen | ✘ – | ✘ – | ✘ nur Bewegung |
| camping|tag|kind | ✘ nur Bewegung | ✔ 15.4s | ✔ 0.6s |
| camping|tag|kriechen | ✘ nur Bewegung | ✘ – | ✘ – |
| camping|tag|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| camping|tag|tier | – | nur Bewegung | – |
| stellplatz|daemmerung|fahrzeug | nur Bewegung | nur Bewegung | nur Bewegung |
| stellplatz|daemmerung|gehen | ✔ 7.8s | ✔ 8.3s | ✔ 6.8s |
| stellplatz|daemmerung|kind | ✘ nur Bewegung | ✔ 5.7s | ✔ 4.2s |
| stellplatz|daemmerung|kriechen | ✔ 11.5s | ✘ truck | ✘ nur Bewegung |
| stellplatz|daemmerung|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| stellplatz|daemmerung|tier | nur Bewegung | – | – |
| stellplatz|nacht|fahrzeug | nur Bewegung | nur Bewegung | nur Bewegung |
| stellplatz|nacht|gehen | ✔ 5.1s | ✔ 4.8s | ✔ 2.1s |
| stellplatz|nacht|kind | ✔ 9.3s | ✔ 4.3s | ✔ 2.6s |
| stellplatz|nacht|kriechen | ✔ 10.8s | ✔ 15.6s | ✔ 12.7s |
| stellplatz|nacht|leer | 0×P 0 Push | 0×P 0 Push | 1×P 0 Push |
| stellplatz|nacht|tier | animal, bird | animal, bird | ⚠Person |
| stellplatz|schnee|fahrzeug | truck | – | nur Bewegung |
| stellplatz|schnee|gehen | ✔ 17.4s | ✔ 9.5s | ✔ 7.8s |
| stellplatz|schnee|kind | ✔ 6.1s | ✔ 6.8s | ✔ 4.2s |
| stellplatz|schnee|kriechen | ✘ nur Bewegung | ✘ – | ✘ animal, cow |
| stellplatz|schnee|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| stellplatz|schnee|tier | nur Bewegung | ⚠Person 1 Push | ⚠Person 1 Push |
| stellplatz|tag|fahrzeug | nur Bewegung | nur Bewegung | nur Bewegung |
| stellplatz|tag|gehen | ✔ 8.4s | ✔ 9.1s | ✔ 8.3s |
| stellplatz|tag|kind | ✔ 5.2s | ✔ 5.8s | ✔ 3.6s |
| stellplatz|tag|kriechen | ✘ airplane | ✘ nur Bewegung | ✔ 17.3s |
| stellplatz|tag|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| stellplatz|tag|tier | – | – | – |
| wald|daemmerung|fahrzeug | nur Bewegung | nur Bewegung | ⚠Person 1 Push |
| wald|daemmerung|gehen | ✔ 15.6s | ✘ nur Bewegung | ✔ 8.5s |
| wald|daemmerung|kind | ✘ – | ✔ 6.9s | ✔ 4.8s |
| wald|daemmerung|kriechen | ✘ – | ✘ – | ✘ nur Bewegung |
| wald|daemmerung|leer | 1×P 1 Push | 0×P 0 Push | 0×P 0 Push |
| wald|daemmerung|tier | – | – | – |
| wald|nacht|fahrzeug | nur Bewegung | ⚠Person 1 Push | ⚠Person 1 Push |
| wald|nacht|gehen | ✔ 3.2s | ✔ 0.6s | ✔ 8.5s |
| wald|nacht|kind | ✔ 9.3s | ✔ 1.4s | ✔ 1.1s |
| wald|nacht|kriechen | ✔ 4.1s | ✘ nur Bewegung | ✔ 5.8s |
| wald|nacht|leer | 2×P 0 Push | 0×P 0 Push | 1×P 1 Push |
| wald|nacht|tier | ⚠Person 1 Push | ⚠Person | ⚠Person |
| wald|nebel|fahrzeug | – | – | – |
| wald|nebel|gehen | ✘ nur Bewegung | ✘ nur Bewegung | ✔ 9.2s |
| wald|nebel|kind | ✔ 5.7s | ✘ – | ✔ 7.4s |
| wald|nebel|kriechen | ✘ nur Bewegung | ✘ – | ✘ – |
| wald|nebel|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| wald|nebel|tier | – | – | – |
| wald|tag|fahrzeug | nur Bewegung | – | nur Bewegung |
| wald|tag|gehen | ✘ animal, bird | ✔ 11.5s | ✔ 6.8s |
| wald|tag|kind | ✘ – | ✘ nur Bewegung | ✔ 4.7s |
| wald|tag|kriechen | ✘ nur Bewegung | ✘ teddy bear | ✘ teddy bear |
| wald|tag|leer | 0×P 0 Push | 0×P 0 Push | 0×P 0 Push |
| wald|tag|tier | animal, dog, teddy bear | ⚠Person 1 Push | animal, dog, teddy bear |
