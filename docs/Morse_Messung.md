# Morse-Empfang: gemessene Grenzen (synthetische Kamera)

Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen --tabelle docs/Morse_Messung.md`. Text «PARIS QTH BERN 59», 2 Läufe pro Feld.
Kamera: 640 × 360 (Arbeitsbild von MoveEye), Rauschen σ 3, Belichtung = halbe Bildperiode, die Bildzeit kommt bis 10 % der
Bildperiode später an, die Kamera regelt die Helligkeit nach, die Optik verschmiert um 0.7 Pixel, der Fleck wandert ±3 Pixel.
Zahl = Zeichenfehler in % (0 = alles richtig, 100 = nichts gelesen).

**Nicht gemessen: echte Kamera, echte Lampe, echte Entfernung, echtes Tageslicht, die Bildrate von MoveEye auf dem Pi.**

## Bildrate × Tempo, Fleck Radius 0.6 Pixel, Nacht

(Radius im Arbeitsbild 640 breit; im Kamerabild 1280 das Doppelte)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 18 WPM | 20 WPM | liest bis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 0 | 100 | 100 | 100 | 93 | 100 | 100 | 86 | 100 | 100 | **3 WPM** |
| 8 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | 100 | 100 | **6 WPM** |
| 10 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | 89 | 100 | **6 WPM** |
| 15 | 0 | 0 | 0 | 0 | 100 | 0 | 100 | 100 | 100 | 100 | **6 WPM** |
| 20 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 7 | 100 | 100 | **8 WPM** |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | **12 WPM** |

## Bildrate × Tempo, Fleck Radius 1.5 Pixel, Nacht

(Radius im Arbeitsbild 640 breit; im Kamerabild 1280 das Doppelte)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 18 WPM | 20 WPM | liest bis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 0 | 100 | 100 | 100 | 100 | 100 | 100 | 93 | 100 | 100 | **3 WPM** |
| 8 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | 89 | 100 | **6 WPM** |
| 10 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 96 | 96 | 100 | **6 WPM** |
| 15 | 0 | 0 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | **10 WPM** |
| 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100 | 100 | **15 WPM** |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **20 WPM** |

## Bildrate × Tempo, Fleck Radius 4 Pixel, Nacht

(Radius im Arbeitsbild 640 breit; im Kamerabild 1280 das Doppelte)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 18 WPM | 20 WPM | liest bis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 0 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 96 | **3 WPM** |
| 8 | 0 | 0 | 4 | 0 | 100 | 100 | 96 | 100 | 100 | 100 | **4 WPM** |
| 10 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 96 | 100 | 100 | **6 WPM** |
| 15 | 0 | 0 | 0 | 0 | 0 | 50 | 100 | 100 | 100 | 100 | **8 WPM** |
| 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 | 100 | **12 WPM** |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **20 WPM** |

## Fleckgrösse × Licht (15 Bilder/s, 5 WPM)

| Licht | Radius 0.4 | Radius 0.6 | Radius 1 | Radius 1.5 | Radius 2.5 | Radius 4 | Radius 10 |
|---|---|---|---|---|---|---|---|
| Nacht (Hintergrund 25, Lampe +400) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dämmerung (Hintergrund 80, Lampe +200) | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tag (Hintergrund 140, Lampe +110) | 100 | 100 | 100 | 0 | 0 | 0 | 0 |
| Tag, schwache Lampe (Hintergrund 140, Lampe +60) | 100 | 100 | 100 | 100 | 100 | 100 | 89 |

Ein kleiner Fleck ist nach der Optik dunkler: entscheidend ist, dass sein hellster Bildpunkt rund 50 Graustufen
(von 255) über dem Hintergrund liegt. Nachts reicht dafür ein Punkt, am Tag braucht es eine helle oder nahe Lampe.

## Erschwerte Bedingungen (15 Bilder/s, Fleck 3 Pixel, Nacht)

| Bedingung | 3 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM |
|---|---|---|---|---|---|
| wie oben | 0 | 0 | 0 | 0 | 100 |
| Handtastung ±20 % | 0 | 0 | 0 | 33 | 36 |
| Handtastung ±30 % | 0 | 0 | 0 | 33 | 67 |
| Handtastung ±40 % | 26 | 7 | 21 | 55 | 100 |
| Hand wandert ±14 Pixel | 2 | 0 | 0 | 0 | 100 |
| Hand wandert ±40 Pixel | 79 | 86 | 74 | 57 | 98 |
| 5 % verlorene Bilder, Bildzeit bis 25 % später | 0 | 0 | 0 | 0 | 36 |
| 15 % verlorene Bilder, Bildzeit bis 50 % später | 0 | 0 | 2 | 21 | 74 |
| kurze Belichtung (1/10 Bildperiode) | 0 | 0 | 0 | 0 | 0 |
| lange Belichtung (ganze Bildperiode) | 0 | 0 | 0 | 0 | 0 |
| Dauerlicht + Blinker 1.5 Hz daneben | 0 | 0 | 0 | 0 | 100 |
| starkes Rauschen σ 10 | 0 | 0 | 0 | 0 | 100 |
| Farnsworth (Pausen wie 3 WPM) | 0 | 0 | 0 | 2 | 0 |

## Daraus: die Grenze für die Anzeige

| Bilder/s | Fleck 0.6 | Fleck 1.5 | Fleck 4 | Anzeige: 0.4 × Bilder/s |
|---|---|---|---|---|
| 5 | 3 | 3 | 3 | 2 |
| 8 | 6 | 6 | 4 | 3 |
| 10 | 6 | 6 | 6 | 4 |
| 15 | 6 | 10 | 8 | 6 |
| 20 | 8 | 15 | 12 | 8 |
| 30 | 12 | 20 | 20 | 12 |

In der Simulation liest der Empfänger, bis ein dit etwa 1.8 Bilder lang ist (rund 0.65 × Bilder pro Sekunde). Die Seite
verspricht weniger: «bis etwa **0.4 × Bilder pro Sekunde** WPM» - ein dit ist dann 3 Bilder lang. Die Reserve ist für das,
was die Simulation nicht kennt (echte Kamera, ungleichmässige Bildzeiten auf dem Pi). Die Messung hält die Grenze überall ein.
