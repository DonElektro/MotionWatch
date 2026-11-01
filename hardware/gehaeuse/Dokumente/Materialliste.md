# MotionWatch – Materialliste (Stand 30.10.2026)

Status aus der abhakbaren Liste: ✅ vorhanden · 🚚 bestellt · ☐ fehlt. Ohne Schrauben (Schrauben: bau.json «schrauben» bzw. Bauen; wichtig ab 01.11.2026: Gabel → Drehteller **M3 × 8**, Seitendeckel **M3 × 10 Linsenkopf ISO 7380**, Camera Module 3 **M2 × 4**, Lampenhalter M3 × 8 **mit Unterlegscheibe**).

## Rechner & Kameras

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ✅ | 1× | Raspberry Pi 5 | SC1112 (8 GB), SC1111 (4 GB) | [Link](https://www.raspberrypi.com/products/raspberry-pi-5/) |
| ☐ | 1× | Raspberry Pi Active Cooler | SC1148 |  |
| ✅ | 1× | microSD 64 GB, A2 | SanDisk Extreme SDSQXAH-064G-GN6MA | Jede A2-Karte von einer Markenfirma geht. |
| ✅ | 1× | Camera Module 3 NoIR | SC0873 | Standard-Blickwinkel. Weitwinkel-Variante wäre SC0874. [Link](https://www.raspberrypi.com/products/camera-module-3/) |
| ✅ | 1× | Kamerakabel Pi 5, 500 mm (22→15-polig) | SC1130 | Lang genug für die Schlaufe hinter dem Kopf durch den Kabelkamin. [Link](https://www.digikey.fi/en/products/detail/raspberry-pi/SC1130/21658263) |
| ☐ | 1× | Waveshare Thermal-90 Camera Module | Waveshare SKU 31941 | Bei Waveshare inzwischen als «discontinued» gelistet. Inkl. MX1.25-10-pol-Kabel. [Link](https://www.waveshare.com/thermal-44-camera-module.htm?sku=31941) |

## Schwenk-/Neigekopf

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 2× | Servo MG90S (Metallgetriebe) | TowerPro MG90S | Doppelarm-Horn und Hornschrauben liegen bei. [Link](https://waveshare.com/MG90S-Servo.htm) |
| ✅ | 1× | PCA9685 16-Kanal-PWM-Modul | Adafruit 815, oder Klon «PCA9685 16 Kanal» | Lötbrücke A0 schliessen → I2C 0x41. [Link](https://www.adafruit.com/product/815) |
| ☐ | 1× | Elko 470 µF / 10 V | 470 µF ≥10 V radial | An V+ des PCA9685 gegen Servo-Stromspitzen. |
| ☐ | ~30× | Softair-Kugeln 6 mm (0,20 g) | BB 6 mm 0,20 g | Für das Drehlager. Glatte, nahtfreie Kugeln nehmen. |
| ☐ | 1× | Silikon- oder Lagerfett | Silikonfett |  |

## Strom

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | Waveshare UPS HAT (E) | Waveshare SKU 27966 | 56 × 88 mm, 5 V / 6 A über Pogo-Pins, USB-C-Laden bis 40 W. Ohne Akkus geliefert. [Link](https://www.waveshare.com/ups-hat-e.htm) |
| ☐ | 4× | Li-Ion-Akku 21700, Flat Top | Samsung INR21700-50E, Digitec 12822871 | 4 gleiche Zellen aus derselben Lieferung. Bei Digitec ca. CHF 33/Stk; bei akkuteile.de deutlich günstiger. Alternative: Molicel P45B. [Link](https://www.digitec.ch/en/s1/product/samsung-battery-inr21700-50e-max-15a-1-pcs-21700-5000-mah-batteries-12822871) |
| ☐ | 1× | Pololu D36V50F5 (Laden: 12–40 V → 5 V / 5,5 A) | Pololu #4091 | [Link](https://www.pololu.com/product/4091/specs) |
| ☐ | 1× | Step-Down 6–36 V → 5 V 4 A (Akku → Servos, Licht, Verstärker) | Bastelgarage 424274, oder Pololu #3782 | Akku liefert 12–16,8 V, passt. |
| ☐ | 1 Paar | GX16 4-polig: Einbaubuchse + Kabelstecker | Bastelgarage 420241 | Ladebuchse hinten (je 2 Kontakte parallel für Plus und Minus). |
| ☐ | 1× | Sicherungshalter fliegend + Sicherung 5 A | Mini-Kfz (ATM) 5 A | Direkt hinter der GX12-Buchse. |
| ☐ | 1× | USB-C-Stecker (male) zum Anlöten | USB-C Plug Breakout | Verbindet den D36V50F5 mit dem UPS HAT. Eine Variante mit 56-kΩ-Widerstand auf CC nehmen. |
| ☐ | 1× | Lade-LED 3 mm + Vorwiderstand + Lichtleiter | LED 3 mm grün, PMMA-Rundstab 3 mm | Lichtleiter hinten neben der Ladebuchse. |

## Licht an der Gabel

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | Scheinwerfer-Modul weiss, Ø 18,8 × 14 mm | Modul Ø18,8 mm | Masse von dir gemessen; der Lampenhalter v5.1 ist darauf ausgelegt (Bohrung 19,2 mm). |
| ☐ | 1× | Scheinwerfer-Modul Infrarot 850 nm, gleiche Grösse | Modul Ø18,8 mm, 850 nm | 850 nm (leichtes Rotglimmen), sieht die NoIR-Kamera viel besser als 940 nm. |
| ☐ | 1× | MOSFET-Modul 2-Kanal, Logic-Level (3,3 V) | Dual MOSFET D4184 / AOD4184 | Schaltet weiss und IR über PCA9685 Kanal 2/3. IRF520-Module schalten bei 3,3 V nicht sauber. |
| ☐ | 2× | Vorwiderstand 2 W für die LEDs | 2 W, Wert je nach LED | Wert rechne ich aus, sobald die genauen LEDs feststehen (ca. 0,5 W Betrieb). |

## Audio

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | Lautsprecher 41 mm, 4 Ω, 2 W | Visaton SC 4.7 ND 4 Ω, RS 431-8715 | 27 mm tief. Strahlt nach unten durch das Bodengitter. [Link](https://de.rs-online.com/web/p/einbau-lautsprecher/4318715) |
| ☐ | 1× | Verstärkermodul PAM8403 (5 V, 2 × 3 W) | PAM8403 Modul |  |
| ☐ | 1× | USB-Soundkarte | C-Media CM108 |  |
| ☐ | 1× | USB-Mikrofon (Mini) | Mini-USB-Mikrofon |  |
| ☐ | 1× | USB-A-Verlängerung kurz, ca. 15 cm | USB-A Stecker → Buchse, 15 cm | Neu wegen Kopf 180°: Mikrofon sitzt jetzt vorne oben in der Ecke. |
| ☐ | 1× | Schaumstoff für Mikrofon | Akustikschaum / Windschutz | Gegen Echo vom Lautsprecher und Servo-Geräusche. |

## Sensoren

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | Mini-PIR AS312 (Micro PIR Modul) | Bastelgarage 420448 | Linse Ø12,2 in der Stirnwand vorne (Gehäuse v5.1 angepasst). |
| ☐ | 1× | Lagesensor MPU-6050 | GY-521 |  |

## Kabel, Druck, Notfall

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | ~1 kg | PETG-Filament | z. B. Bambu PETG HF | Vor dem Druck trocknen. |
| ☐ | 1 Set | Litze 0,5 mm², Dupont-/JST-Kabel, Schrumpfschlauch | Silikonlitze 20 AWG |  |
| ☐ | 1× | Micro-HDMI-auf-HDMI-Kabel | Micro-HDMI → HDMI | Für den Notfallzugang HDMI 0. |

## Neu in v5.1

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | USB-Hub, 4 Anschlüsse, kompakt | höchstens 56 × 22 × 14 mm | Liegt auf der neuen Ablage vorne. Anschlüsse auf einer Längsseite, kurzes Kabel (≥ 15 cm) zum Pi. Für Soundkarte, GPS, LTE, 2. WLAN. |
| ☐ | 1× | Temperaturfühler DS18B20 wasserdicht, Ø 6 mm | DS18B20 Edelstahl Ø6, + Widerstand 4,7 kΩ | Für den Temperaturalarm. Kabel durch das neue Loch im Boden, Sonde hängt frei darunter. |
| ☐ | 1× | Luftdrucksensor BME280 (I2C) | BME280 Breakout 0x76 | Innen montiert, nur für die Sturmwarnung (Luftdruck). |
| ☐ | 1× | Relaismodul 1-Kanal, 5 V, 3,3-V-tauglich | 1-Kanal Relais mit Optokoppler | Für Warnlampe oder Sirene (auch Klatschschalter). |
| ☐ | 1× | Kabelverschraubung M12 (Relais-Ausgang) | Bastelgarage 420032 | Kabel zur Warnlampe fest durchgeführt. Alternativ passt eine GX12-3P-Buchse ins selbe Loch. |
| ☐ | 1× | Strommesser INA219 (optional, Solar) | INA219 Modul | Nur mit 12-V-Panel (misst bis 26 V). Adresse auf 0x44 löten. |

## Später

| | Menge | Teil | Teilenummer / Bestellnummer | Hinweis |
|---|---|---|---|---|
| ☐ | 1× | USB-Stick LTE/GPS | noch offen | Fach ist im Gehäuse reserviert. Modell wählen wir später. |

## Bestellliste (Stand 27.10.2026, Preise inkl. MwSt.)

### 1 · Bastelgarage.ch CHF 164.65

| Art.-Nr. | Artikel | Menge | CHF | Hinweis |
|---|---|---|---|---|
| 424020 | USV HAT (E) 6A 4x21700 Akkuboard | 1 | 36.90 | Waveshare 27966 |
| 420309 | TowerPro Micro Servo MG90S | 2 | 15.80 | nur falls nicht vorhanden |
| 423487 | Raspberry Pi 5 Aktiv Kühler mit Lüfter | 1 | 10.90 | DFRobot, nicht der offizielle; passt |
| 420448 | Micro PIR Bewegungsmelder (AS312) | 1 | 5.90 | Gehäuse v5.1 darauf angepasst (Linse Ø12,2) |
| 420100 | Temperatursensor wasserdicht DS18B20, 1 m | 1 | 5.90 | Sonde Ø6 |
| 420350 | MPU-6050 Beschleunigungssensor | 1 | 10.90 |  |
| 421909 | Gravity BME280 (Druck/Feuchte/Temperatur) | 1 | 17.90 | für die Sturmwarnung |
| 421023 | Gravity INA219 Wattmeter | 1 | 12.90 | optional (Solar), DIP auf 0x44 |
| 420842 | 1-Kanal Relais Modul | 1 | 5.50 | 3,3-V-Ansteuerung |
| 421925 | Fermion 3W Mini Audio Stereo Verstärker | 1 | 9.90 | ist ein PAM8403 |
| 420241 | GX16-4P Stecker mit Einbaustecker | 1 | 8.90 | Ladebuchse (Gehäuse v5.1 auf GX16 umgestellt) |
| 420032 | Kabelverschraubung M12 / IP68 | 1 | 1.50 | Relais-Ausgang hinten |
| 424274 | 6-36V → 5V 4A DC-DC Step-Down | 1 | 6.90 | ersetzt D36V28F5 (Servos/Licht) |
| 421203 | PETG Grau 1,75 mm 1 kg eSun | 1 | 13.90 |  |
| 420416 | Elko 1000 µF 25 V | 1 | 0.95 | statt 470 µF |
| 420548 | Lautsprecher 4 Ohm 3 W 40 mm | 1 | 8.90 | ausverkauft – vormerken |
| 420985 | 15A MOSFET Treiber (AOD4184) | 2 | 9.80 | ausverkauft – vormerken |

### 2 · BerryBase (berrybase.de) ca. € 35 + CHF 6.70

| Art.-Nr. | Artikel | Menge | Preis | Hinweis |
|---|---|---|---|---|
| POL4091 | Pololu D36V50F5 5V 5.5A Step-Down (berrybase.de) | 1 | € 34.95 | Ladewandler bis 40 V; in der Schweiz nicht gefunden |
| 125190 | USB-C Kabel mit offenem Ende, 0,2 m (berrybase.ch) | 1 | 1.70 | Wandler → UPS HAT |
| RPI4-HDMI2 | Offizielles Micro-HDMI-Kabel 1 m (berrybase.ch) | 1 | 5.00 | Notfall |

### 3 · Digitec / Galaxus CHF 132.92

| Art.-Nr. | Artikel | Menge | CHF | Hinweis |
|---|---|---|---|---|
| 12822871 | Samsung INR21700-50E, Flat Top | 4 | 132.92 | ungeschützt (passt in die Halter); günstiger bei akkuteile.de |

### Noch ohne festen Shop

Bei Bastelgarage und BerryBase nicht (lieferbar) gefunden: kompakter USB-Hub (max. 56 × 22 × 14 mm), USB-Soundkarte, USB-Mini-Mikrofon, USB-Verlängerung 15 cm + 2 USB-Winkeladapter, fliegender Sicherungshalter + 5-A-Sicherung, Softair-Kugeln 6 mm, Schaumstoff. Das sind Standardartikel, z. B. bei Digitec/Galaxus, Conrad oder im Sportgeschäft (Kugeln). Thermal-90: Waveshare listet die SKU 31941 als ausgelaufen; falls du sie nicht hast, bietet Pi-Shop.ch die Nachfolge-Varianten an.
