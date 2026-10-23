# Projektstand: Pan-Tilt-Kamera mit Raspberry Pi 5 (Version 4)

*Stand: 22.10.2026. Übergabedokument für einen neuen Chat: Bitte diese Datei zusammen mit `Quellcode_parametrisch_v4.zip` hochladen, dann kann direkt am Modell weitergearbeitet werden.*

---

## 1. Ziel

Ein 3D-gedrucktes Gerät mit zwei parallel montierten Kameras (normal + Wärmebild), die von zwei Servos geschwenkt (Pan) und geneigt (Tilt) werden. Version 1 hat keinen eigenen Akku und wird von einer Powerbank versorgt. Gedruckt wird auf einem **Bambu Lab X2D** (Bauraum 256 × 256 × 260 mm, mit zwei Düsen 235,5 × 256 mm).

Optisch orientiert sich das Gerät an einer Waveshare-PTZ-Kamera: unten eine Box, darauf ein Drehteller mit Kugellager, darauf eine Gabel, in der der Kamerakopf hängt.

## 2. Hardware (festgelegt)

| Bauteil | Modell / Details |
|---|---|
| Rechner | Raspberry Pi 5 (85 × 56 mm, Löcher 58 × 49 mm) |
| Normale Kamera | Raspberry Pi Camera Module 3 (25 × 24 mm, Löcher 21 × 12,5 mm, Linse 9,5 mm unter Oberkante) |
| Wärmebildkamera | Waveshare Thermal-90 Camera Module, **SKU 31941 / WS-31941**: 80 × 62 px, 90° FOV, 8–14 µm, bis 25 fps, SPI + I2C, Stecker MX1.25 10-polig |
| Servos | 2× **MG90S** (SG90-Format, Micro-Servo). Anfangs MG996R, auf Wunsch verkleinert |
| Servotreiber | PCA9685 (Adafruit-Format 62,5 × 25,4 mm, Löcher 55,9 × 19 mm) |
| Strom | Powerbank, kein Akku im Gerät |
| Pan-Lager | gedruckter Laufring + ca. 28 Softair-Kugeln 6 mm |

### Thermal-90: Maße aus dem Produktfoto
- Platine 45 × 22 mm. **Alle Bauteile sitzen auf der Vorderseite** (Linsenblock, Stecker, Reset-Taster).
- Die Linse liegt **nicht mittig**: Linsenmitte 7,4 mm vom linken und 10,5 mm vom oberen Rand (von vorne gesehen).
- Linsenblock ca. 13,4 × 13,4 mm, Mitte bei (8,45 / 10,7) mm.
- Befestigungslöcher **nur links**: (1,75 / 1,75) und (1,75 / 20,25) mm, für M2.
- MX1.25-Stecker am rechten Rand auf der Vorderseite, ca. 4,5 mm hoch, Kabel geht nach rechts weg.
- **I2C-Adresse per Lötbrücke 0x40 oder 0x41, ab Werk 0x40. Das kollidiert mit dem PCA9685 (0x40)!**

## 3. Verlauf der Entscheidungen

1. **v1:** Kastengehäuse, MG996R, Pan-Servo im Deckel, U-Gabel, Kamerakopf. Mit Kollisionsprüfung, aber verworfen.
2. **v2:** Servos auf MG90S verkleinert, Platz für PCA9685 im Unterteil (längs unter dem Pan-Servo).
3. **v3:** Aufbau wie Waveshare-PTZ: Deckel mit Kugel-Laufring, Drehteller auf dem Pan-Servo, einseitiger Arm mit Tilt-Servo, Kameragehäuse mit Blende. Abgefragte Entscheidungen: MG90S behalten, gedrucktes BB-Lager, Unterteil geschlossen.
4. **v4 (aktuell):** Vom Nutzer gewünscht: **Tilt-Servo im Kamerakopf** und **Kopf zwischen zwei Armen**. Thermal-90 nach dem Produktfoto neu platziert (Linse aussermittig). Der Nutzer hat bestätigt, dass Unterteil, Deckel und Drehteller so passen.
5. Drucker korrigiert: X2D statt H2D. Das 3MF wurde neu angeordnet, alle STLs neu exportiert und wasserdicht geprüft.

## 4. Aktueller Aufbau (v4)

**Gesamt:** Unterteil 122 × 71 × 47,5 mm, Höhe bis Kippachse 101,8 mm, Gesamthöhe ca. 131 mm. Der Kamerakopf misst 58 × 58 mm, ist 29,5 mm tief und hat zusätzlich 12 mm Blende.

### Druckteile (7 Stück, alle ohne Stützen, schon in Druckrichtung gedreht)
| # | Datei | Funktion | liegt auf |
|---|---|---|---|
| 1 | 1_Gehaeuse_Unterteil.stl | Box mit Pi 5 (Abstandshalter 6,5 mm) und PCA9685 (Dome 4 mm). Öffnungen für USB-C, 2× micro-HDMI, USB/Ethernet, Lüftungsschlitze, 7-mm-Kabeldurchführung (Servo-Strom), Tasche für 1/4"-Stativmutter, 4 Schraubdome M3 für den Deckel | Boden |
| 2 | 2_Deckel_mit_Laufring.stl | Flacher Deckel. Pan-Servo hängt von unten darin (Welle bei x = 33 / y = 33). Laufring Ø 46–66 mm, 6,8 mm hoch, mit Kugelrille (Laufkreis R 28). Kabeldurchlass, Lüftung | Unterseite (Rille fein drucken) |
| 3 | 3_Drehteller.stl | Ø 68 × 6 mm, Kugelrille unten, Tasche für das Doppelarm-Horn, **4 Schraublöcher** für die Gabel (±11 / ±20,5 mm) | Oberseite |
| 4 | 4_Gabel_mit_Arm1.stl | Gabelboden (4 mm) und Arm 1 (Servo-Seite, +y) in einem Teil. Horn-Vertiefung innen in Arm 1, Loch für die Hornschraube von aussen, Nut für Arm 2 | Gabelboden |
| 5 | 5_Arm2_Lagerseite.stl | Abschraubbarer Arm 2 (−y), Sechskanttasche für eine M3-Mutter, die M3-Schraube dient als Kippachse | Innenseite |
| 6 | 6_Kamerakopf.stl | Geschlossener Kopf mit Blende. Innen: Schlitzhalter für den Tilt-Servo (von hinten einschiebbar), Kanal für das Getriebe-Türmchen, Wellenloch Ø 13 rechts, Lagerdom mit Bohrung Ø 3,3 links, Dome für Camera Module 3 und Thermal-90 | rechte Seitenwand |
| 7 | 7_Rueckdeckel.stl | Rückdeckel mit Stempel, der den Servo nach vorne drückt. Kabelschlitz, Lüftung, 4× M3 | Aussenseite |

`PanTilt_v4_X2D_alle_Teile.3mf`: alle 7 Teile auf einer Platte (230 × 249 mm), passt auch in den Zwei-Düsen-Bereich des X2D.

### Funktionsprinzip
- **Pan:** Der MG90S hängt im Deckel. Sein Horn ist von unten in den Drehteller geschraubt. Der Drehteller läuft auf ca. 28 BBs (6 mm) im Laufring, die Kugeln nehmen die Kippkräfte auf. Das Spiel lässt sich mit dünnen Scheiben zwischen den Servolaschen und dem Deckel einstellen.
- **Tilt:** Der MG90S sitzt **im Kopf**: Welle oben, Welle zeigt nach +y. Die Laschen stecken in Schlitzhaltern, die nach hinten offen sind. Das Horn ist in Arm 1 eingelassen und verschraubt, deshalb dreht sich der Kopf samt Servo um das feste Horn. Gegenüber läuft der Kopf auf einer M3×12, die in Arm 2 gekontert ist. Alle Kabel kommen hinten aus dem Kopf.
- **Kameras im Kopf:** Camera Module 3 oben (Linse bei y −13,5 / z +13,5), 2 mm Abstand zur Front, rundes Fenster Ø 12,5. Thermal-90 unten, Platine 5 mm hinter der Frontwand (wegen des Steckers), quadratisches Fenster 14,4 mm, Linse bei y −18,6 / z −12,5. Links 2× M2, rechts 2 Auflage-Nasen, rechts Platz für den Stecker.
- **Kollisionsprüfung:** Kippen bis ±70° und Schwenken bei 0 / ±90 / 180° ohne Kollision (gerechnet mit Platzhaltern für Servos, Platinen und Hörner).

### Koordinaten im Modell
- Unterteil: Ursprung an der inneren Ecke, z = 0 an der Bodenunterseite, x lang (117 innen), y tief (66 innen).
- Pan-Koordinaten: Ursprung auf der Pan-Achse, z = 0 auf der Oberseite des Drehtellers (absolut z = 61,8), Blickrichtung +x.
- Kipp-Koordinaten (Kopf): Ursprung auf der Kippachse (AXZ = 40 über dem Drehteller), x nach vorne, y nach rechts (von vorne gesehen), z nach oben.

## 5. Kleinteile / Einkauf

- ca. 28 Softair-Kugeln 6 mm (glatt) + Silikon- oder Lithiumfett
- M3: 4× 10 mm (Deckel), 4× 10 mm (Gabel → Drehteller), 2× 10 mm (Arm 2), 4× 8 mm (Rückdeckel), 1× 12 mm + Mutter (Kippachse)
- M2,5×6: 4× Pi 5, 4× PCA9685. M2×6: 4× Camera Module 3, 2× Thermal-90. 2× M2×8 + Muttern (Pan-Servo-Laschen)
- 2 Doppelarm-Hörner + Hornschrauben (liegen den Servos bei)
- Pi-5-Kamerakabel 22→15-polig, **mind. 500 mm**
- optional: 1/4"-Stativmutter, 470-µF-Elko für die Servo-Versorgung

## 6. Elektrik

- PCA9685 → Pi 5: VCC an 3,3 V (Pin 1), GND (Pin 6), SDA (Pin 3), SCL (Pin 5). Pan = Kanal 0, Tilt = Kanal 1.
- **Servo-Strom (V+) nicht vom Pi nehmen:** eigener 5-V-Ausgang der Powerbank an die V+-Klemme des PCA9685, Kabel durch die 7-mm-Durchführung, Masse gemeinsam.
- Pi 5 an der Powerbank: ideal sind 5 V / 5 A (USB-PD). Mit 3 A läuft er, begrenzt aber die USB-Leistung.
- **I2C-Konflikt 0x40 noch offen.** Optionen: Thermal-90 über SPI betreiben (empfohlen, wegen 25 fps) oder eine Lötbrücke umsetzen (PCA9685 A0 → 0x41 oder Thermal-90 → 0x41).
- Software-Grenzen: Pan ±90° (wegen der Kabel), Tilt ±60°.

## 7. Druck

- Material **PETG**, X2D im Cool Mode (ohne Kammerheizung). Für den Einsatz draussen in der Sonne wären ASA oder ABS im Heat Mode besser.
- Deckel und Drehteller (Laufrillen) mit feiner Schicht drucken (0,12–0,16 mm), den Rest mit 0,2 mm. Gabel mit 4 Wänden und 40 % Füllung.

## 8. Offene Punkte / noch nicht verifiziert

1. **HORN_TOP = 13,5 mm** (Laschen-Oberseite bis Aussenfläche des aufgesteckten Horns) am echten MG90S nachmessen. Davon hängen ab: das Spiel des Kugellagers, die Höhe des Drehtellers und die Lage des Servos im Kopf.
2. **Getriebe-Türmchen des MG90S:** Im Modell ragt es max. 8,3 mm über die Laschen-Oberseite (`SV_BODY_H` = 26,7). Nachmessen.
3. **Horn-Maße:** Arm 35 × 6,4 mm, Nabe Ø 7,8, Stärke ≤ 2 mm (je nach Hersteller verschieden).
4. **Thermal-90:** Die Masse stammen aus dem Foto. Höhe des Linsenblocks (angenommen ca. 6,5 mm) und Lochdurchmesser nachmessen, gegebenenfalls `THERM_STAND` anpassen.
5. Lochbild des PCA9685 prüfen, falls es kein Adafruit-Original ist.
6. I2C-Adresskonflikt lösen (siehe oben).
7. Kabelführung Kopf → Unterteil: Das Kabel läuft aussen hinter dem Kopf über den Drehteller in den Kabeldurchlass im Deckel. Eventuell später eine Kabelführung an der Gabel ergänzen.
8. Noch nicht gedruckt bzw. nicht getestet.

Mögliche nächste Schritte: Testdruck des Kamerakopfs und der Gabel, um die Servo- und Hornpassung zu prüfen. Danach Maße nachziehen, Python-Code für PCA9685 und Thermal-90 (SPI), später Akku für Version 2.

## 9. Werkzeugkette / Quellcode (`Quellcode_parametrisch_v4.zip`)

In der Arbeitsumgebung war weder OpenSCAD noch pip/PyPI verfügbar. Deshalb ist das Modell in **reinem Python mit numpy, scikit-image und matplotlib** gebaut, als eigene CSG-Bibliothek auf Basis von Distanzfeldern (SDF).

| Datei | Inhalt |
|---|---|
| `csg.py` | SDF-CSG: Cube/box, Cyl (auch Konus und Sechskant mit fn = 6), RBox, Prism, Torus, rx_box, Union/Difference/Intersection (`U`, `D`, `I`), `T` (Verschiebung), `R` (Drehung, OpenSCAD-Reihenfolge), `RM` (Matrix), Helfer `cyl_x/y/z`, `rib_yz` |
| `pantilt.py` | **Alle Parameter oben**, Teile `part_tub`, `part_lid`, `part_turntable`, `part_yoke`, `part_arm2`, `part_head`, `part_backcover`, Platzhalter für Servos/Platinen/Hörner, `placed(tilt, pan)` = Zusammenbau |
| `export.py` | Marching Cubes (Raster 0,2–0,25 mm) → wasserdichte QEM-Vereinfachung (`decimate.py`) → STL + 3MF. Aufruf `python3 export.py` (alle Teile) oder z. B. `python3 export.py 4 6` (nur Teil 4 und 6). Ausgabe nach `out4/` |
| `decimate.py` | `cluster_qem_manifold`: vereinfacht das Netz, ohne offene Kanten zu erzeugen (auch nach float32/STL) |
| `check4.py` | Kollisionsprüfung über mehrere Pan/Tilt-Stellungen |
| `render.py` | Vorschau-Renderer, z. B. `python3 render.py 1.3,-1.1,0.7 <tilt> <pan> "<ausblenden>" bild.png` |
| `section4.py` | Schnittbilder |

Ein Export dauert ca. 10 Minuten (das Unterteil am längsten, ca. 5 Minuten). Die Abweichung vom idealen Modell liegt bei max. ca. 0,1 mm.
