# MoveEye Gehäuse v5.3 – Montage und Druck

Stand 02.11.2026 (Zweig real-gehaeuse-v53). **v5.3 baut auf v5.2 auf** und ist **noch nicht Standard**: v5.2 bleibt Standard
bis zur Freigabe durch Elektro, v5.1 und v5.2 bleiben wählbar. Quelle: `Quellcode/v53.py` (importiert `v52.py` und `v5.py`).
Alles, was hier nicht steht, gilt wie in [LIESMICH_Montage_v5-2.md](LIESMICH_Montage_v5-2.md).

## Was ist neu

| Neu | Wo | Teil |
|---|---|---|
| Gewindeeinsätze M3 × 5,7 (Messing, Heat-Set) statt selbstschneidender Schrauben | 6 Deckel-Dome, 2 Klötze des Zwischenbodens, 4 Dome der Akkuklappe | 01 Unterteil v5.3 |
| Akkuklappe unten: Zellen 21700 tauschen ohne Deckel und ohne den Pi auszubauen | Öffnung 88 × 72 mm im Boden unter den Zellen | 26 Akkuklappe |
| Halter für Wand und Baum (Gurt 25 mm, 4 Wandschrauben, Schraube 1/4" in die Stativmutter) | unter dem Gerät, Rückwand an der +y-Seite | 25 Halter Wand / Baum |
| Luftführung: Einlass mit Regendach über dem Service-Fenster, Kanal auf die Ansaugung des Active Cooler | Lüftungswand (−y) | 27 Luftkanal |
| Zugentlastung: Kabelbinder-Ösen | Kabelkamin (Deckel), über der GX16, neben der Relais-Buchse, neben dem Relais-Modul | 01, 02 |
| Füsse in die Ecken (sonst stünde ein Fuss auf der Klappe) | (6, 6) … (172, 86) | 11 (gleiches Teil) |

Der **Seitendeckel des Kopfs** bleibt selbstschneidend (M3 × 10 ISO 7380): seine Säulen (Ø 6) sind für einen Einsatz zu dünn
(Ø 4 + 2 × 1,6 Wand) und im Kopf ist kein Platz für dickere Säulen; er wird selten geöffnet. Der Kopf 06 v5.2 bleibt unverändert.

## Akkuklappe – warum unten

Die vier Zellen 21700 hängen unter der Platine des UPS HAT (E), der Pi sitzt darauf (Annahme wie in v5.1/v5.2). Von unten
liegen die Zellen also frei: eine Öffnung im Boden unter dem Akku-Zaun reicht, um jede Zelle zur Feder zu drücken und
herauszukippen – **Deckel, Kopf, Pi, Zwischenboden und Lautsprecher bleiben drin**. Eine seitliche Klappe ginge nicht: die
Zellen liegen quer, ihre Halter-Enden stehen vor der Wand. Der Stativdom (x 62) und der Lautsprecher (x 30) liegen ausserhalb
der Klappe; die Klappe hat eine Aussparung für den Kopf der Stativschraube.

Die **SD-Karte** steckt zwischen Pi und HAT und ist auch von unten nicht erreichbar. Sie bleibt wie in v5.2 über die
microSD-Verlängerung im Schlitz der Lüftungswand (Stopfen 16) erreichbar – ohne Werkzeug.

## Einsätze einschmelzen

1. Lötkolben mit Einschmelzspitze M3 (z. B. ruthex), 220–230 °C für PETG.
2. Einsatz senkrecht auf die Bohrung (Ø 4,0, Herstellerangabe ruthex M3 × 5,7) setzen, ohne Druck einsinken lassen, bis er
   0,2 mm unter der Fläche steht; Spitze herausziehen und sofort mit einer flachen kalten Fläche bündig drücken.
3. Reihenfolge: 6 von oben in die Deckel-Dome, 2 von oben in die Klötze des Zwischenbodens, dann das Unterteil auf den Kopf
   legen und 4 von unten in die Dome der Akkuklappe.

Schrauben: Deckel 6 × M3 × 10, Zwischenboden 2 × M3 × 8, Akkuklappe 4 × M3 × 8 Linsenkopf, Halter 1 × 1/4"-20 × 16 mm.

## Halter Wand / Baum

- **Wand:** 4 Schrauben 4–5 mm mit Dübeln (Löcher Ø 5 in der Rückwand), 6 mm Luft hinter dem Gerät für die Köpfe.
- **Baum:** Spanngurt 25 mm durch die zwei Schlitzpaare (4 × 28 mm) um den Stamm; die zwei Rippen hinten liegen am Stamm.
- **Gerät:** die vorderen Füsse in die Mulden drücken (3 Quetschrippen, rastet ein), von unten die Rändelschraube
  1/4"-20 × 16 mm in die Stativmutter. Lautsprecher, Akkuklappe und Temperaturfühler bleiben frei.
- Druck: Plattform unten, Rückwand steht; Schlitze und Löcher mit 45°-Spitze, ohne Stützen.

## Luftführung

Frische Luft: 3 Schlitze 2,5 × 6 mm (rechts vom Griff des Stopfens 10) mit Regendach über dem Service-Fenster → Luftkanal 27 (Haube, unten offen, liegt mit einem
Moosgummi-Streifen auf dem Active Cooler, 3 Finger zentrieren ihn) → Ansaugung des Lüfters. Die warme Luft aus den Kühlrippen
geht wie bisher durch die Lüftungsschlitze daneben hinaus. Die Kamerakabel CAM0 / CAM1 liegen flach auf dem Dach des Kanals
und gehen dann in den Kabelkamm (wie v5.2). Ein Moosgummi-Pad oben auf dem Kanal: der Deckel hält ihn.

## Druck

| Platte | Inhalt |
|---|---|
| [A](../Druckdateien/v5-3/MotionWatch_v5-3_Platte_A_Unterteil.3mf) | Unterteil v5.3, Zwischenboden, Stopfen, 4 Füsse, Luftkanal 27 |
| [B](../Druckdateien/v5-3/MotionWatch_v5-3_Platte_B_Deckel_Kopf.3mf) | Deckel v5.3, Drehteller, Gabel, Arm 2, Kopf v5.2, Seitendeckel, 2 Lampenhalter, Diffusor, Pupillenring, Stopfen 18 |
| [C](../Druckdateien/v5-3/MotionWatch_v5-3_Platte_C_Halter.3mf) | Halter 25, Akkuklappe 26 |

Jedes Teil auch einzeln: `Druckdateien/v5-3/MoveEye_v5-3_NN_*.3mf` (die unveränderten Teile mit gleichem Inhalt wie v5.2).
Neu bauen: `python3 werkzeuge/gehaeuse_bauen.py --druck53`. Prüfen im Ordner `Quellcode/`: `python3 check53.py`
(Kollisionen, Einsatz-Wände, Kabel, Klappe), `python3 druckcheck53.py` (Wandstärken), `python3 printcheck53.py` (Überhänge),
Bilder `python3 prev53.py`.

## NACHMESSEN vor dem Druck v5.3

| Was | Parameter (`Quellcode/v53.py`) | Annahme |
|---|---|---|
| UPS HAT (E): Zellen unter der Platine, von unten entnehmbar; Halter-Enden liegen auf dem Bodenrand | `OPEN_*`, `v5.BAT_*` | Zellen x 74–162, Länge 70 in y 4–76 |
| Gewindeeinsatz (Herstellerangabe) | `INS_D`, `INS_L`, `INS_HOLE_L` | Ø 4,0 / 5,7 / Bohrtiefe 6,7 |
| Active Cooler: Oberkante, Ansaugöffnung, Ausblasrichtung | `COOL_*`, `FAN_IN` | z 55,5, 23 × 24 mm, seitlich aus den Rippen |
| Füsse in den Ecken, Halter-Mulden | `FEET53` | (6, 6) … (172, 86) |
| Gurt und Wandschrauben | `STRAP_*`, `WALL_HOLES` | Gurt 25 mm, Schrauben Ø ≤ 5 |
| alles aus v5.2 (IR-Modul, Weitwinkel-Linse, CAM-Buchsen, SD-Halter …) | `v52.py` | siehe LIESMICH.md |

## Nicht getestet

Berechnet und am Modell geprüft (Kollisionen, Wandstärken, Überhänge), aber **nicht gedruckt** und nicht mit echten Teilen
zusammengebaut. Ob der Luftkanal die Temperatur des Pi senkt, ist nicht gemessen.
