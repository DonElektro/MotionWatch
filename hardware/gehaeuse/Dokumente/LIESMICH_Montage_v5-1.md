# MotionWatch Gehäuse v5.1: Druck und Montage

Raspberry Pi 5 · UPS HAT (E) mit 4 × 21700 · Camera Module 3 NoIR · Thermal-90 · 2 × MG90S · PCA9685 · Lampen weiss + IR · Lautsprecher · PIR · Mikrofon

- **Unterteil:** 183 × 97 × 71,5 mm (mit Füssen 77,5 mm)
- **Gesamthöhe:** ca. 161 mm
- **Grundstellung:** Der Kopf schaut zur Seite mit PIR und Mikrofon («vorne»). Die Ladebuchse ist hinten.

## Neu in v5.1

- **Scheinwerfer:** Der Halter ist jetzt für dein Modul Ø 18,8 × 14 mm gebaut.
  - Bohrung 19,2 mm, das Modul sitzt 1 mm zurückversetzt (Regen).
  - Dahinter bleiben 2,5 mm Platz für die Kabel.
  - Fixieren mit einem Tropfen Heisskleber oder Silikon, oder mit einer Madenschraube M3 von oben.
  - Der Halter ist kleiner und leichter als vorher.
- **Kabelbügel an beiden Armen:** Arm 1 hat jetzt auch einen, mit einer schrägen Stütze darunter (stützenfrei druckbar).
- **USB-Hub-Ablage vorne rechts**, über dem Lautsprecher, auf 4 Stegen mit Kabelbinder-Schlitzen.
  - Für einen kompakten 4-Port-Hub bis 56 × 22 × 14 mm, Anschlüsse zur Gehäusemitte.
  - Sticks dürfen bis ca. 40 mm herausragen. Die Anschlüsse ganz links (über dem PIR) nur für kurze Stecker verwenden.
- **Temperaturfühler:** Loch Ø 6,5 mm mit Kragen im Boden. Die DS18B20-Sonde hängt darunter.
- **Relais-Ausgang:** Loch Ø 12,3 hinten unten mit Regendach, für eine Kabelverschraubung M12 (Kabel zur Warnlampe oder Sirene). Wahlweise passt eine GX12-3P-Buchse ins selbe Loch.
- **Ladebuchse jetzt GX16-4P** (Loch 16 mm, Bastelgarage): je 2 Kontakte parallel für Plus und Minus. Dach und Lichtleiter entsprechend versetzt.
- **PIR-Loch Ø 12,4** für den Micro-PIR AS312 von Bastelgarage (Linse Ø 12,2).
- **INA219** (optional, Solar) liegt auf dem Zwischenboden neben dem PAM8403.
- **Längere Blende** am Kamerakopf (18 statt 12 mm) gegen Tau und Regen. Nachgerechnet: Sie ragt bei keiner der beiden Kameras ins Bild.
- **Lüftungsschlitze 3 mm verschoben.** Fehler aus v5.0: Der Rand des HDMI-Stopfens stiess an das Lüftungsdach.
- **Neue Plätze der Module:**
  - MOSFET-Modul und D36V28F5 kleben jetzt an der Stirnwand links vom PIR.
  - Das Relaismodul klebt an der Wand über der Hub-Ablage.

Kopf, Seitendeckel, Gabel, Lampenhalter und Unterteil haben sich geändert. Gleich geblieben sind Deckel, Drehteller, Arm 2, Zwischenboden, HDMI-Stopfen und Füsse.

## Vor dem Druck des Unterteils: bitte nachmessen

Einige Bauteile hatte ich nicht in der Hand. Die Werte unten sind geschätzt und stehen oben in `v5.py`. Schick mir die echten Masse, dann passe ich sie in wenigen Minuten an.

| Was | angenommen | Parameter |
|---|---|---|
| UPS HAT (E) mit Akkus: Länge × Breite × Höhe | 90 × 80 × 26 mm | `BAT_L, BAT_W, BAT_H` |
| Höhe der Pi-Unterseite über dem Gehäuseboden (Stapel UPS + Pi) | 37 mm | `PI_Z_ABOVE_FLOOR` |
| Lautsprecher Visaton SC 4.7 ND | Ø 41 mm | `SPK_D` |

Das Unterteil ist der grösste Druck (viele Stunden). Kopf, Seitendeckel, Drehteller, Gabel, Arm 2 und Lampenhalter hängen nicht von diesen Massen ab und können sofort gedruckt werden.

## Druckteile (Bambu Lab X2D): alle ohne Stützen und schon richtig gedreht

| Datei | Anzahl | liegt auf | Hinweis |
|---|---|---|---|
| 01_Unterteil | 1 | Boden | 4 Wände, 15 % Füllung |
| 02_Deckel_mit_Laufring | 1 | Unterseite | Rille fein drucken (0,12–0,16 mm) |
| 03_Drehteller | 1 | Oberseite | gleich wie v4.1 |
| 04_Gabel_mit_Arm1 | 1 | Gabelboden | 2 Löcher für den Lampenhalter, neuer Kabelbügel |
| 05_Arm2_Lagerseite | 1 | Innenseite | neu: 2 Löcher für den Lampenhalter, Kabelbügel |
| 06_Kamerakopf | 1 | rechte Seitenwand | längere Blende |
| 07_Seitendeckel | 1 | Aussenseite | längere Blende |
| 08_Lampenhalter | **2** | Rückseite | gleiches Teil für beide Seiten |
| 09_Zwischenboden | 1 | flach | |
| 10_HDMI_Stopfen | 1 | Flansch | |
| 11_Fuss | **4** | Fuss | Zapfen nach oben |

Hast du v4.1 schon gedruckt, bleibt der Drehteller gültig. Kopf und Seitendeckel funktionieren auch, haben aber die kürzere Blende. Die alte Gabel und den alten Arm 2 kannst du auch weiterverwenden: Bohr dann je zwei Löcher Ø 2,5 mm für die Lampenhalter (Lage siehe `LAMP_HOLES` in `v5.py`: 2 mm vor der Achse, 13,25 und 34,75 mm über dem Gabelboden).

**Platten:**
- **Platte A:** Unterteil mit den Kleinteilen (Füsse, Stopfen, Zwischenboden)
- **Platte B:** Deckel und alles für den Kopf

Material PETG (vorher trocknen). Für Kopf, Gabel und Seitendeckel 5 mm Brim.

## Neu gegenüber v4.1

**Unterteil**

- Akku-Zaun für das UPS-HAT-Paket. Fixiert wird es mit Klettband oder doppelseitigem Schaumklebeband auf dem Boden.
- **PCA9685** auf 4 Domen stehend an der Wand mit den Lüftungsschlitzen, Bauteile nach innen, M2,5.
- **Lautsprecher** in einem Zentrierring über dem Bodengitter. Mit 3–4 Tupfen Heisskleber oder Silikon festmachen.
- **Stativmutter 1/4"** im Boden: Mutter von innen in die Sechskanttasche drücken.
- **Vorne:**
  - PIR-Hülse: AM312 von innen einschieben, mit einem Tropfen Heisskleber sichern.
  - Mikrofon oben in der Ecke zwischen zwei Rippen, mit Schaumstoff eingeklemmt. Fünf kleine Schalllöcher.
- **Hinten:**
  - Loch Ø 16 für die GX16-4P-Einbaubuchse, mit Regendach.
  - Loch Ø 3,3 für den Lichtleiter der Lade-LED.
- **Lüftungsschlitze** mit Regendach auf der Seite neben dem HDMI-Fenster.
- **HDMI-Notfallfenster** 30 × 16 mm, mit Stopfen verschlossen. Der Stopfen hat unten eine Lasche zum Herausziehen.
- **Zwischenboden** (separates Teil) für Ladewandler, PAM8403 und Soundkarte. Er liegt auf Leisten an zwei Wänden und wird mit 2 × M3 geschraubt.
- 6 Deckelschrauben M3.
- 4 aufgesteckte Füsse (6 mm, Zapfen einkleben). Damit kommt der Ton vom Lautsprecher unten heraus.

**Deckel:** Laufring, Pan-Servo und Kabelkamin wie im Konzept.

**Lampen:** Die Halter sind jetzt eigene Teile und werden aussen an die Arme geschraubt (je 2 × M3 × 8). In jeden Halter kommt ein Scheinwerfer-Modul Ø 18,8 × 14 mm, die Kabel gehen hinten durch das Loch.

## Montage (Kurzfassung)

1. **Unterteil vorbereiten:**
   - Füsse einkleben und die Stativmutter einlegen.
   - Lautsprecher einkleben.
   - PCA9685 an die Dome schrauben (Lötbrücke A0 → 0x41).
   - PIR und Mikrofon einsetzen.
   - GX16-Buchse von innen verschrauben, dahinter die Sicherung.
2. **Akkupaket** mit dem Pi darauf in den Zaun stellen, mit Klettband fixieren. HDMI zeigt zum Fenster.
3. **Zwischenboden** einschrauben. Darauf kommen D36V50F5 (Laden), PAM8403 und Soundkarte, mit Schaumklebeband.
4. **Module mit Schaumklebeband:**
   - MOSFET-Modul und D36V28F5 an die Stirnwand links vom PIR.
   - Relaismodul an die Wand über der Hub-Ablage.
   - USB-Hub mit 2 Kabelbindern auf die Ablage.
   - MPU-6050 flach auf den Boden neben den Stativdom.
5. **Hinten:** GX16-4P-Ladebuchse und die Kabelverschraubung M12 für das Relais-Kabel einschrauben.
6. **DS18B20:** Kabel von unten durch das Bodenloch, mit Silikon abdichten. Die Sonde hängt ca. 5 cm unter dem Gehäuse.
7. **Deckel:**
   - Pan-Servo von unten einsetzen (2 × M2 × 8 mit Muttern).
   - Kugeln einlegen, Drehteller mit Horn aufsetzen.
   - **Servo auf Mitte (1500 µs) und den Drehteller so aufstecken, dass der Kopf später nach vorne zur PIR-Seite schaut.**
8. **Kopf, Gabel und Arm 2** wie in der v4.1-Anleitung. Danach die Lampenhalter an die Arme schrauben, weiss an Arm 1, IR an Arm 2.
9. Kabel von Kopf und Lampen hinter dem Kopf in einer Schlaufe durch den Kabelkamin führen. Deckel mit 6 × M3 × 10 zuschrauben.
   - Tipp: 10 × 3 mm Moosgummi-Dichtband auf den Wannenrand kleben.

## Schwenken über ±90°

Die Software kann ab 2.95.4 einen 270°- oder 360°-Servo nutzen. Mechanisch ist rundum alles frei (geprüft). Die Kabelschlaufe vom Kopf zum Kabelkamin muss dann länger sein, ca. 25 cm, am besten in einem Spiralschlauch. Mit dem MG90S (180°) bleibt es bei ±90°.

## Kurz zu beachten

- **Pi-USB-Anschlüsse:** Hinter den USB-Buchsen des Pi bleiben nur ca. 17 mm bis zur Wand. Für das Kabel zum Hub und die Mikrofon-Verlängerung kurze **USB-Winkeladapter (90°)** verwenden. Die Soundkarte steckt im Hub.
- **I2C-Adresse:** Das Waveshare-Wiki nennt für den UPS HAT (E) die Adresse **0x2D**. Bitte mit `i2cdetect -y 1` prüfen (Info für den Software-Chat).
- **Software-Grenzen:** Tilt auf ±60° und Pan auf ±90° um die Grundstellung begrenzen.
