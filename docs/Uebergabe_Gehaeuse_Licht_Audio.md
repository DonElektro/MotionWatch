# Ergänzungen für das Gehäuse (aus dem Software-Chat «Motion Watch»)

*Stand 22.10.2026 (aktualisiert für Software 1.8.0). Bitte zusammen mit `Projektstand_PanTilt_Kamera.md` und `Quellcode_parametrisch_v4.zip` verwenden.*

## 1. Entscheidungen

| Thema | Entscheidung |
|---|---|
| Scheinwerfer | **zwei schwache Lampen: weiss + Infrarot (850 nm)**, 1-W-LEDs, mit Vorwiderstand auf ca. 0,5 W begrenzt (wenig Wärme). Nur ein / aus, kein Dimmen (PWM mit 50 Hz würde im Video flackern) |
| Ort der Lampen | **aussen an den Gabelarmen**: Arm 1 = weiss, Arm 2 = Infrarot (oder umgekehrt, wie es besser passt). Schwenken mit, kippen **nicht** mit |
| Lautsprecher | **über USB**: USB-Soundkarte + kleiner Verstärker + Lautsprecher, im **Unterteil** |
| Mikrofon | USB-Mikrofon (Mini-Stick) am Pi, Öffnung nach aussen, weit weg von Servos und Lüfter |
| Kamera | Wechsel auf **Camera Module 3 NoIR** (gleiche Masse wie Camera Module 3) |
| I2C | PCA9685 auf **0x41** (Lötbrücke A0), Thermal-90 bleibt 0x40 |

## 2. Lampen an den Armen

- Je eine **1-W-LED auf 20-mm-Alu-Sternplatine** (weiss, kaltweiss oder neutralweiss / IR 850 nm), davor eine **20-mm-Linse mit Halter** (Abstrahlwinkel ca. 60°, damit das Kippen ±60° abgedeckt ist).
- Halter aussen am Arm, Blickrichtung +x (wie die Kamera), Mitte ungefähr auf Höhe der Kippachse oder etwas darunter.
- Hinter dem Stern: **Luftspalt oder kleine Alu-Platte (ca. 25 × 25 × 2 mm)** als Kühlung. PETG wird ab ca. 70 °C weich, darum soll die Platine nicht flächig auf Kunststoff liegen.
- Masse von Stern, Linse und Linsenhalter sind von Hersteller zu Hersteller verschieden: **nachmessen**, als Parameter anlegen.
- Kabel: je 2 Adern vom Unterteil über den Drehteller den Arm hinauf (nur Pan-Bewegung, ±90°), mit Zugentlastung am Arm.
- Die Lampe darf nicht in die Kamerafenster blenden (Arme liegen seitlich neben dem Kopf, das sollte passen, bitte kurz prüfen).

## 3. Elektrik der Lampen

- Steuerung über freie Kanäle des **PCA9685: Kanal 2 = weiss, Kanal 3 = IR** (Kanal 0 = Pan, 1 = Tilt bleiben).
- Je ein **Logic-Level-MOSFET** (z. B. AO3400 oder IRLZ44N) mit Vorwiderstand an der **Servo-5-V-Versorgung** (nicht am Pi).
  Für ca. 0,5 W LED-Leistung: weiss (ca. 3 V, 150 mA) → ca. 13 Ω / 0,5 W, IR (ca. 1,5 V, 300 mA) → ca. 12 Ω / 2 W.
  Die Durchlassspannung der LED nachmessen, dann den Widerstand anpassen. Die Software schaltet nur ein / aus.
- Kleine Lochrasterplatine ca. **30 × 20 mm** im Unterteil (Platz vorsehen, 2 Schraubdome M2,5 oder Klebefläche).

## 4. Audio im Unterteil

- **USB-Soundkarte** (Stick ca. 50 × 20 × 10 mm, oft mit kurzem Kabel), steckt im Pi oder liegt im Gehäuse.
- **Verstärker PAM8403** (Modul ca. 22 × 18 mm, 5 V von der Servo-Versorgung).
- **Lautsprecher rund 40 mm, 3 W, 4 Ω** (Tiefe ca. 15–20 mm, nachmessen). Einbau in einer **Seiten- oder Frontwand** des Unterteils mit Lochgitter und 4 Klemmnasen oder Schrauben. Hinter dem Lautsprecher etwas geschlossenes Volumen lassen (klingt lauter).
- **USB-Mikrofon:** Mini-Stick direkt am Pi. Ein kleines Loch oder Schlitz nach aussen davor, nicht neben den Lüftungsschlitzen des Lüfters und nicht direkt unter dem Pan-Servo.
- Das Unterteil (122 × 71 × 47,5 mm) wird dafür vermutlich etwas grösser werden müssen: bitte Platz prüfen.

## 5. Weitere Wünsche ans Gehäuse

- **Fenster der Wärmebildkamera offen lassen.** Glas, Acryl und PETG lassen 8–14 µm nicht durch.
- Lüftung regenfest: Schlitze **seitlich mit Abdeckung nach unten** statt oben im Deckel.
- Platz für den **offiziellen Pi-5-Active-Cooler**.
- Clip oder Kanal an der Gabel für eine **Schlaufe des Kamera-Flachbandkabels** und die Lampenkabel.
- **Wetterhäuschen für den Temperaturfühler** (ab Software 2.31.0), siehe Abschnitt 7.

## 6. Pinbelegung / Adressen (für die Software)

| Was | Anschluss |
|---|---|
| PCA9685 | I2C, Adresse **0x41**, Kanal 0 Pan, 1 Tilt, 2 Licht weiss, 3 Licht IR |
| Thermal-90 | SPI (+ I2C 0x40) |
| Lautsprecher, Mikrofon | USB |
| Relais | weiterhin frei wählbare GPIOs (ausser GPIO 4, falls 1-Wire aktiv) |
| BME280 / BMP280 | I2C, Adresse **0x76** (oder 0x77) – Temperatur, Feuchte, Luftdruck |
| DS18B20 (Alternative) | 1-Wire an **GPIO 4** (Pin 7), 4,7 kΩ von Daten nach 3,3 V; `dtoverlay=w1-gpio` in `config.txt` |

## 7. Temperaturfühler (Wetterhäuschen)

Die Software erkennt beide Fühler selbst. Empfohlen ist der **BME280** (Temperatur, Luftfeuchtigkeit, Luftdruck), z. B. als kleines
Breakout-Board 13 × 10 mm mit 4 Pins (VIN 3,3 V, GND, SCL, SDA). Er hängt am gleichen I2C-Bus wie PCA9685 und UPS-HAT.

**Wichtig: ausserhalb des warmen Gehäuses messen.** Der Pi 5 heizt das Innere um 10–20 °C auf; ein Fühler innen misst Unsinn.

Vorschlag fürs Modell:
- **Wetterhäuschen** (Strahlungsschutz) seitlich am **Unterteil**, auf der Seite **ohne** Lüftungsschlitze des Pi (die warme Abluft darf
  nicht hineinziehen), möglichst im Schatten des Gehäuses.
- Aufbau: 3–4 übereinanderliegende, nach aussen und unten geneigte **Lamellen-Ringe** (Aussen-Ø ca. 34 mm, Innenraum ca. 18 × 14 mm,
  Lamellenabstand 4–5 mm), oben ein geschlossener Deckel – Luft kommt von der Seite herein, Regen und Sonne nicht.
- Hellgrau oder weiss drucken (heizt in der Sonne weniger auf); kein Schwarz.
- Halter für das Board: Schlitz oder zwei Stifte, Board hochkant, Sensor-Chip zur Luft.
- **Kabeldurchführung** ins Gehäuse mit kleiner Tülle oder Schräge nach unten (kein Wasser ins Gehäuse); 4 Adern, 10–20 cm.
- Abstand vom Gehäuse ca. **15–20 mm** (kleiner Steg), damit die Gehäusewand das Häuschen nicht wärmt.
- **DS18B20** (wasserdichte Edelstahl-Sonde am Kabel) als Alternative: nur eine Durchführung (Ø 6 mm) unten am Gehäuse, die Sonde hängt
  frei 5–10 cm unter dem Gehäuse im Schatten. Misst nur die Temperatur.

Abweichungen gleicht die Einstellung «Temperaturfühler: Korrektur (°C)» aus (mit einem Thermometer vergleichen).
