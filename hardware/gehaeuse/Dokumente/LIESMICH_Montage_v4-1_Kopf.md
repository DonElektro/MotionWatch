# Pan-Tilt-Kamera v4.1: druckbar korrigiert

Raspberry Pi 5 · Pi Camera Module 3 · Waveshare Thermal-90 · 2× MG90S/SG90 · PCA9685 · Powerbank

Unterteil 122 × 71 × 47,5 mm, Gesamthöhe ca. 131 mm, Kamerakopf 58 × 58 × 30 mm (+ 12 mm Blende).

## Was gegenüber v4 geändert ist (wegen des gescheiterten Drucks)

- **Kamerakopf:** In v4 begannen der Lagerdom und zwei Schraubdome **in ca. 50 mm Höhe frei in der Luft**, weil sie an der zuletzt gedruckten Seitenwand hingen. Das war sehr wahrscheinlich der Grund für den Fehldruck.
  - Neu ist der Kopf zur Lagerseite hin **offen** und wird mit einem **Seitendeckel** verschlossen.
  - Der Seitendeckel trägt den Lagerdom für die Kippachse und einen Stempel, der den Servo hält.
  - Die Rückwand ist jetzt fest und hat einen Kabelschlitz.
- **Gabel:** Die zwei äußeren Stützrippen an Arm 1 begannen 4 mm über dem Bett. Jetzt gehen sie bis aufs Bett.
- Alle 7 Teile wurden Schicht für Schicht in Druckrichtung geprüft: **keine schwebenden Bereiche mehr**, keine großen Überhänge.
- Unverändert gegenüber v4 und nicht neu zu drucken, falls sie schon gelungen sind: Unterteil, Deckel, Drehteller, Arm 2.

## Druckteile (Bambu Lab X2D): alle ohne Stützen, schon gedreht

| Datei | liegt auf | Höhe |
|---|---|---|
| 1_Gehaeuse_Unterteil | Boden | 44,5 mm |
| 2_Deckel_mit_Laufring | Unterseite (Rille fein drucken, 0,12–0,16 mm) | 9,8 mm |
| 3_Drehteller | Oberseite (Rille oben, fein drucken) | 6 mm |
| 4_Gabel_mit_Arm1 | Gabelboden, 4 Wände, 40 % Füllung | 52 mm |
| 5_Arm2_Lagerseite | Innenseite (Mutternfalle unten) | 14 mm |
| 6_Kamerakopf | rechte Seitenwand (Servo-Seite), offen nach oben | 55,5 mm |
| 7_Seitendeckel | Außenseite, Dom und Stempel zeigen nach oben | 28,8 mm |

`PanTilt_v4-1_X2D_alle_Teile.3mf`: alle 7 Teile auf einer Platte (230 × 249 mm).

**Empfehlung:** Nicht alles auf einmal drucken, sondern in zwei Platten:
- **Platte A:** Unterteil allein (größtes Teil, braucht die längste Zeit).
- **Platte B:** alle anderen Teile.

Für Kopf, Gabel und Seitendeckel einen **Brim** (5 mm) einschalten. Material PETG (vorher trocknen), Kammer im Cool Mode.

## Kleinteile

- ca. 28 Softair-Kugeln 6 mm + etwas Fett
- Unterteil: 4× M3×10 (Deckel), 4× M2,5×6 (Pi), 4× M2,5×6 (PCA9685), 2× M2×8 + Muttern (Pan-Servo)
- Gabel: 4× **M3×8** (Gabel → Drehteller; länger stösst in den Laufring, Druck-Check 01.11.2026), 2× M3×10 (Arm 2 → Gabelboden)
- Kippachse: 1× M3×12 + 1× M3-Mutter + **2–3 M3-Unterlegscheiben** (zwischen Seitendeckel und Arm 2)
- Kopf: 4× **M2×4** (Camera Module 3; M2×6 sticht durch die Front), 2× M2×6 (Thermal-90), **3× M3×10 Linsenkopf ISO 7380** (Seitendeckel; Zylinderkopf stösst beim Kippen an Arm 2)
- 2× Doppelarm-Horn mit Hornschrauben (liegen den Servos bei)
- Kamerakabel Pi 5 22→15-polig, mind. 500 mm

## Montage

1. **Unterteil, Deckel, Drehteller:** PCA9685 und Pi einschrauben, Pan-Servo in den Deckel, Kugeln einlegen, Drehteller mit Horn aufsetzen, Mittelschraube anziehen.
2. **Gabel** mit 4× M3 auf den Drehteller schrauben.
3. **Tilt-Horn** senkrecht in die Vertiefung innen in Arm 1 legen und mit 2–4 Hornschrauben festschrauben.
4. **Kameras in den Kopf** (durch die offene Seite):
   - Thermal-90: Bauteilseite nach vorne, Linse links (von vorne gesehen), Stecker rechts. Links 2× M2, rechts liegt sie auf zwei Nasen auf. Kabel vorher einstecken.
   - Camera Module 3 auf die 4 oberen Dome (M2).
5. **Servos auf Mitte stellen** (1500 µs).
6. **Tilt-Servo** von der offenen Seite her einsetzen:
   - Welle oben, Welle durch das Loch in der gegenüberliegenden Wand.
   - Die Laschen liegen in den kleinen Führungsrahmen auf den beiden Haltern.
7. Kabel durch den Schlitz in der **Rückwand** führen.
8. **Seitendeckel** aufsetzen und mit 3× M3 festschrauben. Der lange Stempel drückt den Servo in seine Halter.
9. **Kopf einsetzen** (Arm 2 noch nicht montiert):
   - Servowelle auf das Horn in Arm 1 stecken, Kopf schaut gerade nach vorne.
   - Hornschraube von außen durch Arm 1 in die Servowelle drehen.
10. **Arm 2** montieren:
    - M3-Mutter in die Sechskant-Tasche drücken.
    - Arm in die Nut des Gabelbodens setzen und 2× M3 von oben eindrehen.
    - 2–3 Unterlegscheiben zwischen Arm 2 und Seitendeckel legen.
    - M3×12 von außen durch Arm 2 in die Lagerbohrung drehen, nur bis sie anliegt.
11. Kabel mit Schlaufe hinter dem Kopf nach unten und durch den Kabeldurchlass im Deckel führen. In der Software Tilt auf ±60° und Pan auf ±90° begrenzen.

Kollisionsfrei geprüft: Kippen bis ±70°, Schwenken 0/±90/180°.

## Nachmessen (Werte oben in `pantilt.py`)

- **HORN_TOP = 13,5 mm** (Laschen-Oberseite → Außenfläche Horn).
- MG90S-Getriebe-Türmchen: höchstens 8,3 mm über der Laschen-Oberseite.
- Linsenblock Thermal-90: ca. 13,4 mm Kante (aus dem Foto). `THERM_STAND` stellt den Abstand zur Front ein.

## Verdrahtung & Strom

- PCA9685 → Pi 5: VCC an 3,3 V (Pin 1), GND (Pin 6), SDA (Pin 3), SCL (Pin 5). Pan = Kanal 0, Tilt = Kanal 1.
- **I2C-Adresskonflikt 0x40:** Thermal-90 über SPI betreiben (empfohlen) oder eine Lötbrücke auf 0x41 umsetzen.
- Servo-Versorgung V+ separat vom zweiten Powerbank-Ausgang (Kabel durch die 7-mm-Durchführung), 470 µF Elko empfohlen.
