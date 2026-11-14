# Morse mit Infrarot zwischen zwei MoveEye: gemessen (synthetische Kamera) und gerechnet

Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen-ir --tabelle docs/Morse_Messung_IR.md`. Text «PARIS QTH BERN 59», 2 Läufe pro Feld.
Nacht, das eigene IR-Licht ist an (Hintergrund 45 statt 25, Rauschen σ 5), die Gegenstelle ist ein Punkt, der überstrahlt.
Zahl = Zeichenfehler in %.

**Nicht gemessen: zwei echte Geräte, echte IR-LEDs, echte Entfernung, Regen / Nebel, die Bildrate der Pi-Kamera in der Nacht.**

## Gegenstelle: Punkt (weit weg, Radius 0.4 Pixel)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 20 WPM | Anzeige 0.4 × Bilder/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 36 | 57 | 54 | 100 | 100 | 100 | 100 | 100 | 3 |
| 10 | 0 | 0 | 29 | 0 | 100 | 100 | 100 | 100 | 100 | 4 |
| 15 | 0 | 0 | 0 | 0 | 14 | 100 | 50 | 100 | 100 | 6 |
| 20 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 100 | 100 | 8 |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 100 | 12 |

## Gegenstelle: klein (Radius 1.5 Pixel)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 20 WPM | Anzeige 0.4 × Bilder/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 21 | 93 | 100 | 100 | 100 | 100 | 100 | 3 |
| 10 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | 100 | 4 |
| 15 | 0 | 0 | 0 | 0 | 0 | 4 | 50 | 100 | 100 | 6 |
| 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 79 | 100 | 8 |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |

## Gegenstelle: nah, überstrahlt (Radius 6 Pixel)

| Bilder/s | 3 WPM | 4 WPM | 5 WPM | 6 WPM | 8 WPM | 10 WPM | 12 WPM | 15 WPM | 20 WPM | Anzeige 0.4 × Bilder/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 7 | 100 | 100 | 100 | 100 | 100 | 100 | 3 |
| 10 | 0 | 0 | 0 | 0 | 100 | 100 | 100 | 100 | 100 | 4 |
| 15 | 0 | 0 | 0 | 0 | 0 | 7 | 50 | 100 | 100 | 6 |
| 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 79 | 100 | 8 |
| 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 12 |

## Entfernung (gerechnet, nicht gemessen)

Das IR-Licht der Gegenstelle direkt zu sehen ist viel heller als eine davon beleuchtete Szene: sein Licht fällt auf einen
Bildpunkt (Winkel eines Bildpunkts bei 66° Bildwinkel und 1280 Bildpunkten: 0.9 mrad, Raumwinkel 8 × 10⁻⁷ sr), während eine
matte Fläche (30 % Rückstrahlung) das Licht in den ganzen Halbraum streut. Verhältnis direkt (Abstand D) zu beleuchteter
Fläche (Abstand d): (d / D)² × π / (0.3 × 8 × 10⁻⁷) ≈ (d / D)² × 1.3 × 10⁷.
Reicht das IR-Licht, um eine Szene in d = 5 m gut auszuleuchten, ist es als Punkt rechnerisch noch in mehreren Kilometern
so hell - die Helligkeit begrenzt die Strecke also nicht. Es begrenzen: die freie Sicht, der Abstrahlwinkel der LEDs
(beide müssen im Lichtkegel UND im Bild des anderen sein), Dunst, und dass der Punkt mindestens ~50 Graustufen über dem
Hintergrund liegt (nachts erfüllt, am Tag nicht). Ehrliche Erwartung ohne Messung: einige zehn bis wenige hundert Meter.

## Tempo

Senden kann das IR-Licht bis 20 WPM; lesen kann die Gegenstelle bis etwa 0.4 × ihre Bilder pro Sekunde:
bei 15 Bildern/s 6 WPM, bei 30 Bildern/s 12 WPM. Massgebend ist die Zahl auf der Seite der Gegenstelle.
