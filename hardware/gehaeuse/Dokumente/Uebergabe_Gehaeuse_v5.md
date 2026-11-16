# Übergabe Gehäuse v5.1 → Software (MotionWatch)

*Stand 27.10.2026, passend zu Software 2.95.32. Ersetzt die früheren Gehäuse-Angaben (v4). Das Wetterhäuschen und der UPS HAT mit 2 × 18650 sind nicht mehr aktuell.*

## Aufbau

- **Unterteil:** 183 × 97 × 71,5 mm, mit Füssen 77,5 mm.
- **Gesamthöhe:** ca. 161 mm.
- **Kopf:** Er hängt in der Gabel zwischen zwei Armen, der Tilt-Servo sitzt im Kopf. Darin sitzen Camera Module 3 NoIR und Thermal-90.
- **Grundstellung:** Der Kopf schaut **zur Stirnseite mit PIR und Mikrofon** («vorne»), die Ladebuchse ist hinten. Bei der Montage den Pan-Servo auf Mitte (1500 µs) stellen und den Kopf nach vorne ausrichten.
- **Schwenkbereich:**
  - Mechanisch ist rundum alles kollisionsfrei (geprüft bei Tilt ±70°).
  - Mit dem MG90S (180°) gilt Pan ±90°.
  - Für «Pan-Servo: Drehbereich 270/360°» (ab 2.95.4) braucht es einen anderen Servo und eine längere Kabelschlaufe (ca. 25 cm, Spiralschlauch). Die Kabel laufen vom Kopf durch den Kabelkamin im Deckel.

## Strom

| Teil | Angabe |
|---|---|
| Akku | **Geekworm X1206 V2.0** (Entscheid 16.11.2026), 4 × 21700 **parallel** (3,0–4,2 V), unter dem Pi, 5,1 V / 6 A gesamt über Pogo-Pins, Akku-Chip MAX17043 **I2C 0x36**, GPIO 6 = Strom am Eingang, GPIO 16 = Laden ein/aus (beide nur lesen). Früher: Waveshare UPS HAT (E), 4 × 21700 in Serie, I2C 0x2D – bleibt in MoveEye unterstützt |
| Laden | GX16-4P hinten (je 2 Kontakte parallel), Sicherung 5 A → DC-Stecker 5,5/2,1 → **DC-Eingang des X1206, 9–18 V** (12 V empfohlen, mind. 3 A). **24-V-Quellen und Solarpanels direkt (Leerlauf über 18 V) passen nicht mehr.** Kein Verpolungsschutz an der GX16. Ohne Akku wie bisher: 12–40 V → Pololu D36V50F5 → USB-C des Pi |
| Servos, Licht, Verstärker | 5,1-V-Ausgang **XH2.54 des X1206** → **Flachsicherung 5 A** → PCA9685 V+ (Elko 470 µF), Lampen-MOSFETs, PAM8403. Der X1206 liefert zusammen 6 A (Pi und alles hier). Step-Down und Sicherung in B+ entfallen (nur noch ohne Akku: Step-Down am 12-V-Netzteil) |
| Solar (optional) | Panel an dieselbe GX16-Ladebuchse. **INA219 auf 0x44** (0x40 Thermal, 0x41 PCA9685). Nur mit 12-V-Panel, der INA219 misst bis 26 V |

## Anschlüsse und Adressen

| Was | Anschluss |
|---|---|
| PCA9685 | I2C **0x41**: Kanal 0 Pan, 1 Tilt, 2 Licht weiss, 3 Licht IR (über MOSFET) |
| Thermal-90 | SPI + I2C 0x40, GPIO 7/23/24 |
| Geekworm X1206 | I2C 0x36, GPIO 6 (Pin 31) und GPIO 16 (Pin 36) gehören der Platine (ältere Geräte: UPS HAT (E) auf 0x2D) |
| Ein/Aus (PSW) | Taster 12 mm in der Reserve-Öffnung hinten statt Blindstopfen 17 an der Buchse PSW des X1206 – **provisorisch** |
| Lade-LED, Taste «Schutz» | Neu GPIO 13 (Pin 33) und GPIO 12 (Pin 32); ältere Geräte GPIO 6 / 16 (Einstellungen) |
| BME280 (innen, nur Luftdruck / Sturmwarnung) | I2C 0x76 oder 0x77 (Gravity-Modul von DFRobot: 0x77) |
| MPU-6050 (Bewegt-/Umgefallen-Alarm) | I2C 0x68, flach auf dem Boden kleben |
| DS18B20 (Temperaturalarm) | 1-Wire GPIO 4, 4,7 kΩ nach 3,3 V. Sonde hängt **unter** dem Gehäuse (Loch Ø 6,5 im Boden) |
| PIR AS312 (Micro-PIR) | 3,3 V, Ausgang GPIO 5. Linse in der Stirnwand |
| Relais (Warnlampe / Sirene) | 1-Kanal-Modul, GPIO 22 (Relais 1). Kabel hinten durch eine **Kabelverschraubung M12** (alternativ GX12-3P) |
| Audio | USB-Mikrofon vorne oben, USB-Soundkarte + PAM8403 + Lautsprecher Ø 41 mm, strahlt nach unten durch den Boden |
| USB | Kompakter **4-Port-Hub** auf einer Ablage vorne (höchstens 56 × 22 × 14 mm). Daran: Soundkarte, GPS, LTE, 2. WLAN-Stick, optional SDR, Zigbee, USB-SSD |
| HDMI 0 | Notfallfenster mit Stopfen an der Seite mit den Lüftungsschlitzen |

## Lichter

- Je ein Scheinwerfer-Modul Ø 18,8 × 14 mm in einem Halter aussen an den Armen: Arm 1 weiss, Arm 2 IR 850 nm.
- Die Lichter schwenken mit, kippen aber nicht mit.
- An beiden Armen ist ein Kabelbügel.

## Für die Software zu prüfen

- Den Geekworm X1206 auf 0x36 mit `i2cdetect -y 1` bestätigen (ältere Geräte: UPS HAT (E) auf 0x2D).
- In den Texten der Software «Powerbank» oder «UPS HAT 2 × 18650» durch den UPS HAT (E) ersetzen, wo das noch vorkommt.
- In der Hardware-Prüfung (System → Hilfe) neu auftauchende Teile: Relais-Ausgang, DS18B20 unter dem Gehäuse, INA219 auf 0x44.
