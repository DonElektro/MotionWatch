extends RefCounted
## Gehäuse v5.1 für die Werkstatt (werkstatt.gd) – erzeugt von werkzeuge/gehaeuse_bauen.py aus
## hardware/gehaeuse/bau.json. NICHT VON HAND ÄNDERN (Texte dort ändern, dann «gehaeuse_bauen.py --texte»).
## Texte deutsch (T.t übersetzt sie, Übersetzungen kommen aus bau.json in i18n/texte.json).

const QUELLE_SHA := "2d4be5503fbda254ae1dca9426eab2eec8ea5db9b75866ba9eacb0fe9ce9e2cf"
const VERSION := "5.1"
const KOPF_FARBE := "#f59a4a"   # Kopfteil (dreht / neigt) in MoveEye-Orange
const KOPF_TEILE := ["turntable", "yoke", "arm2", "head", "side", "lamp1", "lamp2", "head52"]
const GRAU := "#9a9ea3"   # Unterteil, Deckel, Zwischenboden, Füsse, Stopfen
const GRAU_TEILE := ["tub", "tub52", "lid", "shelf", "feet", "plug", "plug52", "sdplug", "resplug", "wplug", "sockel", "irplug"]
const MASSE := "Unterteil 183 × 97 × 71,5 mm (mit Füssen 77,5 mm), Gesamthöhe ca. 161 mm, Kopf 58 × 58 mm"
# Materialliste: id -> [Menge, Bezeichnung, Teilenummer, Gruppe]
const BOM := {
	"pi5": ["1×", "Raspberry Pi 5", "SC1112 (8 GB), SC1111 (4 GB)", "Rechner & Kameras"],
	"cooler": ["1×", "Raspberry Pi Active Cooler (Lüfter)", "SC1148", "Rechner & Kameras"],
	"sd": ["1×", "microSD 64 GB, A2", "SanDisk Extreme SDSQXAH-064G-GN6MA", "Rechner & Kameras"],
	"cam": ["1×", "Camera Module 3 NoIR", "SC0873", "Rechner & Kameras"],
	"camcable": ["1×", "Kamerakabel Pi 5, 500 mm (22→15-polig)", "SC1130", "Rechner & Kameras"],
	"therm": ["1×", "Waveshare Thermal-90 Camera Module", "Waveshare SKU 31941", "Rechner & Kameras"],
	"servo": ["2×", "Servo MG90S (Metallgetriebe)", "TowerPro MG90S", "Schwenk-/Neigekopf"],
	"pca": ["1×", "PCA9685 16-Kanal-PWM-Modul", "Adafruit 815", "Schwenk-/Neigekopf"],
	"elko": ["1×", "Elko 470 µF / 10 V", "470 µF ≥10 V", "Schwenk-/Neigekopf"],
	"bbs": ["~30×", "Softair-Kugeln 6 mm (0,20 g)", "BB 6 mm 0,20 g", "Schwenk-/Neigekopf"],
	"fett": ["1×", "Silikon- oder Lagerfett", "", "Schwenk-/Neigekopf"],
	"ups": ["1×", "Waveshare UPS HAT (E)", "Waveshare SKU 27966", "Strom"],
	"cells": ["4×", "Li-Ion-Akku 21700, Flat Top", "Samsung INR21700-50E", "Strom"],
	"charger": ["1×", "Pololu D36V50F5 (Laden 12–40 V → 5 V)", "Pololu #4091", "Strom"],
	"buck": ["1×", "Step-Down 6–36 V → 5 V 4 A (Servos, Licht, Verstärker)", "Bastelgarage 424274", "Strom"],
	"gx16": ["1×", "GX16 4-polig: Einbaubuchse + Stecker (Ladebuchse)", "Bastelgarage 420241", "Strom"],
	"fuse": ["1×", "Sicherungshalter fliegend + Sicherung 5 A", "Mini-Kfz (ATM) 5 A", "Strom"],
	"fuse2": ["1×", "Flachsicherung 5 A mit Halter (Akku-Leitung B+ → Step-Down)", "Mini-Kfz (ATM) 5 A", "Strom"],
	"usbc": ["1×", "USB-C-Stecker zum Anlöten (D36V50F5 → UPS HAT)", "USB-C Plug Breakout", "Strom"],
	"chled": ["1×", "Lade-LED 3 mm + 330 Ω + Lichtleiter", "LED 3 mm grün, 330 Ω, PMMA 3 mm", "Strom"],
	"ledw": ["1×", "Scheinwerfer-Modul weiss, Ø 18,8 × 14 mm", "Ø 18,8 mm", "Licht an der Gabel"],
	"ledir": ["1×", "Scheinwerfer-Modul Infrarot 850 nm", "Ø 18,8 mm, 850 nm", "Licht an der Gabel"],
	"mosfet": ["2×", "MOSFET-Modul 1-Kanal (2 × AOD4184 parallel), Logic-Level", "Bastelgarage 420985", "Licht an der Gabel"],
	"res": ["2×", "Vorwiderstand 2 W für die LEDs", "", "Licht an der Gabel"],
	"spk": ["1×", "Lautsprecher 41 mm, 4 Ω", "Visaton SC 4.7 ND", "Audio"],
	"pam": ["1×", "Verstärkermodul PAM8403", "PAM8403", "Audio"],
	"sound": ["1×", "USB-Soundkarte", "C-Media CM108", "Audio"],
	"mic": ["1×", "USB-Mikrofon (Mini)", "", "Audio"],
	"usbext": ["1×", "USB-A-Verlängerung, ca. 15 cm", "", "Audio"],
	"foam": ["1×", "Schaumstoff für das Mikrofon", "", "Audio"],
	"pir": ["1×", "Mini-PIR AS312", "Bastelgarage 420448", "Sensoren"],
	"mpu": ["1×", "Lagesensor MPU-6050", "GY-521", "Sensoren"],
	"petg": ["~1 kg", "PETG-Filament", "Bambu PETG HF", "Kabel, Druck, Notfall"],
	"litze": ["1×", "Litze 0,5 mm², Dupont-/JST-Kabel, Schrumpfschlauch", "20 AWG", "Kabel, Druck, Notfall"],
	"hdmi": ["1×", "Micro-HDMI-auf-HDMI-Kabel", "", "Kabel, Druck, Notfall"],
	"hub": ["1×", "USB-Hub, 4 Anschlüsse, kompakt", "max. 56 × 22 × 14 mm", "Neu in v5.1"],
	"ds18": ["1×", "Temperaturfühler DS18B20 wasserdicht", "DS18B20 Ø 6 mm", "Neu in v5.1"],
	"bme": ["1×", "Luftdrucksensor BME280", "0x76 / 0x77", "Neu in v5.1"],
	"relay": ["1×", "Relaismodul 1-Kanal, 5 V", "", "Neu in v5.1"],
	"m12": ["1×", "Kabelverschraubung M12 (Relais-Ausgang)", "Bastelgarage 420032", "Neu in v5.1"],
	"ina": ["1×", "Strommesser INA219 (optional, Solar)", "0x44", "Neu in v5.1"],
	"lte": ["1×", "USB-Stick LTE/GPS", "", "Später"],
	"camwide": ["1×", "Camera Module 3 Wide NoIR", "SC0874", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"irmod": ["1×", "IR-LED-Modul 850 nm mit 120°-Linse (Ø ca. 18,8 mm, nachmessen)", "850 nm, 120°", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"m2": ["4×", "Schraube M2 × 6, selbstschneidend (Weitwinkel-Kamera)", "M2 × 6", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"sdext": ["1×", "microSD-Verlängerung 15 cm mit Einbau-Kartenhalter (Platine ca. 22 × 15 mm, 2 Löcher M2,5 im Abstand 18 mm)", "15 cm", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"mosfet3": ["1×", "3. MOSFET-Modul (AOD4184) für das IR-Modul 120° (bzw. die IR-LED 5 mm), Kanal 4", "Bastelgarage 420985", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"irled5": ["1×", "IR-LED 5 mm, 850 nm", "", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"res_ir": ["1×", "Vorwiderstand 2 W für das IR-Modul 120°", "", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"taster": ["2×", "Taster 12 mm, IP67", "", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"sled": ["1×", "RGB-LED 5 mm mit Diffusor «Blinki-Auge»", "", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"camcable2": ["1×", "Kamerakabel Pi 5, 200 mm (CAM1)", "SC1129", "Variante v5.2 (Weitwinkel-Kamera, eigenes Unterteil)"],
	"psu12": ["1×", "Netzteil 12 V, mind. 3 A, mit GX16-Stecker verlötet", "", "Strom"],
	"psu12_dev": ["1×", "Netzteil 12 V, mind. 3 A, mit GX16-Stecker verlötet – Entwicklung", "", "Strom"],
	"lader12": ["1×", "Ladequelle: Netzteil 12 V, mind. 3 A, mit GX16-Stecker verlötet (lädt die Akkus über den D36V50F5)", "", "Strom"],
	"solar": ["1×", "Solarpanel 30 W, 18 V (Leerlauf unter 25 V), Kabel an GX16-Stecker", "", "Strom"],
	"solarreg": ["1×", "Solar-Regler (MPPT) zwischen Panel und GX16: Eingang 18 V, Ausgang 12–24 V konstant, mind. 2 A", "", "Strom"],
	"motorhat": ["1×", "Motor-HAT (Adafruit DC & Stepper Motor HAT, I2C 0x60)", "Adafruit 2348", "Mover"],
	"chassis": ["1×", "Kettenfahrwerk mit 2 DC-Motoren", "", "Mover"],
	"schrauben": ["1 Set", "Schraubensatz M2 / M2,5 / M3 mit Muttern und Scheiben", "", "Kabel, Druck, Notfall"],
	"psu_pi": ["1×", "Raspberry Pi 27-W-USB-C-Netzteil (Entwicklung)", "SC1153", "Strom"],
}
# Teile: [id, Art (druck | teil | kabel | v52), Name, Materialliste-id, Montageschritt (0 = keiner), Druckdatei,
#         ersetzt (v5.2: dieses Teil von v5.1, sonst "")]
const TEILE := [
	["tub", "druck", "01 Unterteil", "petg", 2, "01_Unterteil", ""],
	["feet", "druck", "11 Füsse (4×)", "petg", 2, "11_Fuss_4x", ""],
	["tripod", "teil", "Stativmutter 1/4\"", "", 2, "", ""],
	["speaker", "teil", "Lautsprecher 41 mm, 4 Ω", "spk", 2, "", ""],
	["pca", "teil", "PCA9685 16-Kanal-PWM-Modul", "pca", 3, "", ""],
	["elko", "teil", "Elko 470 µF / 10 V", "elko", 3, "", ""],
	["pir", "teil", "Mini-PIR AS312", "pir", 3, "", ""],
	["mic", "teil", "USB-Mikrofon (Mini)", "mic", 3, "", ""],
	["ups", "teil", "UPS HAT (E) mit 4 Akkus 21700", "ups", 4, "", ""],
	["pi", "teil", "Raspberry Pi 5", "pi5", 4, "", ""],
	["cooler", "teil", "Raspberry Pi Active Cooler (Lüfter)", "cooler", 4, "", ""],
	["shelf", "druck", "09 Zwischenboden", "petg", 5, "09_Zwischenboden", ""],
	["charger", "teil", "Pololu D36V50F5 (Laden 12–40 V → 5 V)", "charger", 5, "", ""],
	["pam", "teil", "Verstärkermodul PAM8403", "pam", 5, "", ""],
	["ina", "teil", "Strommesser INA219 (optional, Solar)", "ina", 5, "", ""],
	["mosfet", "teil", "MOSFET-Modul 1-Kanal (2 × AOD4184 parallel), Logic-Level", "mosfet", 6, "", ""],
	["buck", "teil", "Step-Down 6–36 V → 5 V 4 A (Servos, Licht, Verstärker)", "buck", 6, "", ""],
	["relay", "teil", "Relaismodul 1-Kanal, 5 V", "relay", 6, "", ""],
	["hub", "teil", "USB-Hub, 4 Anschlüsse, kompakt", "hub", 6, "", ""],
	["soundcard", "teil", "USB-Soundkarte", "sound", 6, "", ""],
	["mpu", "teil", "Lagesensor MPU-6050", "mpu", 6, "", ""],
	["bme", "teil", "Luftdrucksensor BME280", "bme", 6, "", ""],
	["cable_usb", "kabel", "USB-Kabel Pi → Hub", "hub", 6, "", ""],
	["cable_power", "kabel", "Stromkabel", "litze", 6, "", ""],
	["jacks", "teil", "GX16 4-polig: Einbaubuchse + Stecker (Ladebuchse)", "gx16", 7, "", ""],
	["fuse", "teil", "Sicherungshalter fliegend + Sicherung 5 A", "fuse", 7, "", ""],
	["ledlight", "teil", "Lade-LED 3 mm + 330 Ω + Lichtleiter", "chled", 7, "", ""],
	["relayjack", "teil", "Kabelverschraubung M12 (Relais-Ausgang)", "m12", 7, "", ""],
	["probe", "teil", "Temperaturfühler DS18B20 wasserdicht", "ds18", 7, "", ""],
	["lid", "druck", "02 Deckel mit Laufring", "petg", 8, "02_Deckel_mit_Laufring", ""],
	["servo1", "teil", "Pan-Servo MG90S", "servo", 8, "", ""],
	["balls", "teil", "Softair-Kugeln 6 mm (0,20 g)", "bbs", 8, "", ""],
	["horn1", "teil", "Servohorn Pan (im Drehteller)", "servo", 8, "", ""],
	["turntable", "druck", "03 Drehteller", "petg", 8, "03_Drehteller", ""],
	["yoke", "druck", "04 Gabel mit Arm 1", "petg", 9, "04_Gabel_mit_Arm1", ""],
	["horn2", "teil", "Servohorn Tilt (in Arm 1)", "servo", 9, "", ""],
	["therm", "teil", "Waveshare Thermal-90 Camera Module", "therm", 10, "", ""],
	["cam3", "teil", "Camera Module 3 NoIR", "cam", 10, "", ""],
	["servo2", "teil", "Tilt-Servo MG90S", "servo", 10, "", ""],
	["head", "druck", "06 Kamerakopf", "petg", 10, "06_Kamerakopf", ""],
	["side", "druck", "07 Seitendeckel", "petg", 10, "07_Seitendeckel", ""],
	["arm2", "druck", "05 Arm 2 (Lagerseite)", "petg", 11, "05_Arm2_Lagerseite", ""],
	["lamp1", "druck", "08 Lampenhalter Arm 1 (weiss)", "petg", 12, "08_Lampenhalter_2x", ""],
	["lamp2", "druck", "08 Lampenhalter Arm 2 (IR)", "petg", 12, "08_Lampenhalter_2x", ""],
	["alu", "teil", "LED-Platinen der Scheinwerfer", "res", 12, "", ""],
	["lens_w", "teil", "Scheinwerfer-Modul weiss, Ø 18,8 × 14 mm", "ledw", 12, "", ""],
	["lens_ir", "teil", "Scheinwerfer-Modul Infrarot 850 nm", "ledir", 12, "", ""],
	["cable_cam", "kabel", "Kamerakabel (Flachkabel)", "camcable", 13, "", ""],
	["cable_servo", "kabel", "Servokabel", "servo", 13, "", ""],
	["plug", "druck", "10 HDMI-Stopfen", "petg", 13, "10_HDMI_Stopfen", ""],
	["wide", "v52", "Weitwinkel-Kamera (Stirnwand, 12° nach unten)", "camwide", 3, "", ""],
	["irled", "v52", "IR-LED-Modul 120° (Stirnwand)", "irmod", 3, "", ""],
	["buttons", "v52", "Taster 12 mm, IP67", "taster", 7, "", ""],
	["sled", "v52", "RGB-LED 5 mm mit Diffusor «Blinki-Auge»", "sled", 10, "", ""],
	["tub52", "v52", "01 Unterteil v5.2 (Fenster Weitwinkel, IR-Modul, Kabelkamm, Tasten)", "petg", 2, "01_Unterteil_v52", "tub"],
	["mosfet52", "v52", "MOSFET-Modul (v5.2: Lüftungswand unter dem PCA9685)", "mosfet", 6, "", "mosfet"],
	["cable_cam1", "v52", "Kamerakabel CAM1 (Weitwinkel → Kabelkamm → Pi)", "camcable2", 13, "", ""],
	["cable_cam0_52", "v52", "Kamerakabel CAM0 (v5.2: Kamin → Kabelkamm → Pi)", "camcable", 13, "", "cable_cam"],
	["plug52", "v52", "10 Stopfen Service-Fenster v5.2 (HDMI + USB-C)", "petg", 13, "10_Stopfen_HDMI_USB_v52", "plug"],
	["sdplug", "v52", "16 Stopfen SD-Schlitz v5.2", "petg", 13, "16_Stopfen_SD_v52", ""],
	["head52", "v52", "06 Kamerakopf v5.2 (Status-LED oben)", "petg", 10, "06_Kamerakopf_v52", "head"],
	["diff52", "v52", "14 Diffusor «Blinki-Auge» + 15 Pupillenring", "sled", 10, "14_Diffusor_Status_LED", ""],
	["sockel", "dev", "13 Entwicklungs-Sockel (statt UPS HAT + Akkus)", "petg", 4, "13_Entwicklungs_Sockel", "ups"],
	["wplug", "v52", "12 Blindstopfen Weitwinkel-Fenster (ohne Weitwinkel-Kamera)", "petg", 3, "12_Blindstopfen_Weitwinkel", ""],
	["irplug", "v52", "19 Stopfen IR-Modul-Loch (ohne IR-Modul)", "petg", 3, "19_Stopfen_IR_Modul", ""],
	["resplug", "v52", "17 Blindstopfen Reserve-Öffnung hinten (GX12)", "petg", 7, "17_Blindstopfen_Reserve", ""],
	["lampdrv", "v52", "PLATZHALTER Lampentreiber (Feld 30 × 20, 2 × M2,5)", "", 6, "", ""],
	["fuseh", "v52", "Sicherungshalter 5 A (Akku B+) in der Klammer am Boden", "fuse2", 7, "", ""],
]
# Montage: [Titel v5.2, Text v5.2, Titel v5.1, Text v5.1] (v5.2 = Standard; v5.1 für die Auswahl v5.1)
const SCHRITTE := [
	["Teile drucken", "Die Druckteile v5.2 in PETG ohne Stützen drucken: Platte A (Unterteil v5.2 mit Weitwinkel-Fenster, Zwischenboden, Stopfen, Füsse) und Platte B (Deckel, Drehteller, Gabel, Arm 2, Kopf 06 v5.2 mit Status-LED, Seitendeckel, Lampenhalter, Diffusor 14, Pupillenring 15). Kopf, Gabel und Seitendeckel mit 5 mm Brim. Stopfen 10 (Service-Fenster) und 16 (SD-Schlitz) braucht jedes Gerät, 17 auch; 12 und 18–24 nur für Teile, die dein Paket nicht hat. Sockel 13 nur für die Entwicklungs-Variante.", "Teile drucken", "Alle 11 Druckteile in PETG ohne Stützen drucken: Platte A (Unterteil, Zwischenboden, Stopfen, Füsse) und Platte B (Deckel und alles für den Kopf). Kopf, Gabel und Seitendeckel mit 5 mm Brim."],
	["Unterteil vorbereiten", "Füsse unter das Unterteil v5.2 kleben und die Stativmutter 1/4\" von innen in die Sechskanttasche drücken. Den Lautsprecher mit 3–4 Tupfen Heisskleber in den Ring über dem Bodengitter kleben.", "Unterteil vorbereiten", "Füsse einkleben und die Stativmutter 1/4\" von innen in die Sechskanttasche drücken. Den Lautsprecher mit 3–4 Tupfen Heisskleber in den Ring über dem Bodengitter kleben."],
	["Vorne: Weitwinkel, IR-Modul, PCA9685, PIR, Mikrofon", "Weitwinkel-Kamera (Camera Module 3 Wide) mit 4 × M2 × 6 an die Rippen hinter dem Fenster der Stirnwand schrauben (12° nach unten). Das IR-Modul 120° von innen in die Hülse daneben schieben und mit der Madenschraube M3 sichern. PCA9685 an die 4 Dome der Lüftungswand schrauben (M2,5, Lötbrücke A0 → 0x41), Elko an V+. PIR von innen in die Hülse schieben, das Mikrofon mit Schaumstoff zwischen die Rippen klemmen. Ohne Weitwinkel-Kamera den Blindstopfen 12 von aussen ins Fenster drücken, ohne IR-Modul den Stopfen 19 in die Hülse.", "Vorne: PCA9685, PIR, Mikrofon", "PCA9685 an die 4 Dome der Lüftungswand schrauben (M2,5, Lötbrücke A0 → 0x41), Elko an V+. PIR von innen in die Hülse schieben, das Mikrofon mit Schaumstoff zwischen die Rippen klemmen."],
	["Akku, Pi und SD-Verlängerung", "Das UPS HAT (E) mit den 4 Akkus 21700 und dem Pi 5 darauf in den Zaun stellen und mit Klettband fixieren. HDMI und USB-C des Pi zeigen zum Service-Fenster, der Lüfter sitzt auf dem Pi. Die microSD-Verlängerung in den Kartenschlitz des Pi stecken und den Einbau-Kartenhalter mit 2 × M2,5 × 6 an die zwei Dome über dem PCA9685 schrauben.", "Akku und Pi", "Das UPS HAT (E) mit den 4 Akkus und dem Pi 5 darauf in den Zaun stellen und mit Klettband fixieren. HDMI zeigt zum Fenster, der Lüfter sitzt auf dem Pi."],
	["Zwischenboden", "Den Zwischenboden mit 2 × M3 einschrauben. Darauf mit Schaumklebeband: D36V50F5 (Laden), PAM8403 und optional INA219 (Solar, I2C 0x44, Shunt 0,01 Ω).", "Zwischenboden", "Den Zwischenboden mit 2 × M3 einschrauben. Darauf mit Schaumklebeband: D36V50F5 (Laden), PAM8403 und optional INA219."],
	["Module an den Wänden", "MOSFET-Module (Licht weiss, IR, IR-Modul 120°) an die Lüftungswand unter dem PCA9685 kleben, den Step-Down an die Stirnwand links vom PIR, den Lampentreiber auf das Feld darunter (2 × M2,5). Das Relais über die Hub-Ablage kleben. USB-Hub mit 2 Kabelbindern auf die Ablage, Soundkarte in den Hub, MPU-6050 flach auf den Boden.", "Module an den Wänden", "MOSFET-Modul und Step-Down an die Stirnwand links vom PIR, das Relais über die Hub-Ablage kleben. USB-Hub mit 2 Kabelbindern auf die Ablage, Soundkarte in den Hub, MPU-6050 flach auf den Boden."],
	["Hinten und unten: Buchsen, Tasten", "GX16-4P-Ladebuchse (Sicherung 5 A dahinter) und die Kabelverschraubung M12 für das Relais einschrauben, Lichtleiter der Lade-LED einsetzen. Die 2 Tasten (12 mm, IP67) in die Rückwand, Mutter innen. Die Reserve-Öffnung mit dem Blindstopfen 17 schliessen. Den Sicherungshalter 5 A (Akku B+) in die Klammer am Boden drücken. Den DS18B20 von unten durch das Bodenloch führen und abdichten.", "Hinten und unten", "GX16-4P-Ladebuchse (Sicherung 5 A dahinter) und die Kabelverschraubung M12 für das Relais einschrauben, Lichtleiter der Lade-LED einsetzen. Den DS18B20 von unten durch das Bodenloch führen und abdichten."],
	["Deckel und Drehlager", "Pan-Servo von unten in den Deckel (2 × M2 × 8). Kugeln in die Rille legen, Servo auf Mitte (1500 µs) und den Drehteller mit Horn so aufstecken, dass der Kopf später zur PIR-Seite schaut.", "Deckel und Drehlager", "Pan-Servo von unten in den Deckel (2 × M2 × 8). Kugeln in die Rille legen, Servo auf Mitte (1500 µs) und den Drehteller mit Horn so aufstecken, dass der Kopf später zur PIR-Seite schaut."],
	["Gabel montieren", "Die Gabel mit 4 × M3 × 8 (nicht länger: die Spitze darf nicht in den Laufring ragen) auf den Drehteller schrauben. Das Tilt-Horn senkrecht in die Vertiefung innen in Arm 1 legen und festschrauben.", "Gabel montieren", "Die Gabel mit 4 × M3 × 8 (nicht länger: die Spitze darf nicht in den Laufring ragen) auf den Drehteller schrauben. Das Tilt-Horn senkrecht in die Vertiefung innen in Arm 1 legen und festschrauben."],
	["Kamerakopf v5.2 mit Status-LED", "Die RGB-Status-LED von innen ins Loch im Dach des Kopfs 06 v5.2 schieben (Heisskleber), den Diffusor 14 aussen in die Vertiefung drücken und den Pupillenring 15 oben einsetzen. Thermal-90 (Linse links) und Camera Module 3 NoIR durch die offene Seite einschrauben (Camera Module 3: 4 × M2 × 4, Thermal-90: 2 × M2 × 6). Tilt-Servo auf Mitte einsetzen, alle Kabel (auch die 4 Adern der LED) durch den Schlitz hinten, Seitendeckel mit 3 × M3 × 10 Linsenkopf ISO 7380 zuschrauben (kein Zylinderkopf: der stösst beim Kippen an Arm 2).", "Kamerakopf", "Thermal-90 (Linse links) und Camera Module 3 durch die offene Seite einschrauben (Camera Module 3: 4 × M2 × 4, Thermal-90: 2 × M2 × 6). Tilt-Servo auf Mitte einsetzen, Kabel durch den Schlitz hinten, Seitendeckel mit 3 × M3 × 10 Linsenkopf ISO 7380 zuschrauben (kein Zylinderkopf: der stösst beim Kippen an Arm 2)."],
	["Kopf einsetzen, Arm 2", "Servowelle auf das Horn in Arm 1 stecken (Kopf schaut geradeaus). Arm 2 mit Mutter in die Nut setzen, 2 × M3 von oben, 2–3 Unterlegscheiben, M3 × 12 als Achse nur bis zum Anliegen.", "Kopf einsetzen, Arm 2", "Servowelle auf das Horn in Arm 1 stecken (Kopf schaut geradeaus). Arm 2 mit Mutter in die Nut setzen, 2 × M3 von oben, 2–3 Unterlegscheiben, M3 × 12 als Achse nur bis zum Anliegen."],
	["Lampen", "Die zwei Lampenhalter mit je 2 × M3 × 8 mit Unterlegscheibe aussen an die Arme schrauben: weiss an Arm 1, IR 850 nm an Arm 2. Module einsetzen und mit Heisskleber oder Madenschraube sichern.", "Lampen", "Die zwei Lampenhalter mit je 2 × M3 × 8 mit Unterlegscheibe aussen an die Arme schrauben: weiss an Arm 1, IR 850 nm an Arm 2. Module einsetzen und mit Heisskleber oder Madenschraube sichern."],
	["Kabel, Deckel zu, Stopfen", "Kabel von Kopf, Status-LED und Lampen in einer Schlaufe hinter dem Kopf durch den Kabelkamin führen. Die Kamerakabel in den Kabelkamm an der Lüftungswand legen: Schlitz 1 = CAM1 (Weitwinkel), Schlitz 2 = CAM0 (Kopfkamera). Deckel mit 6 × M3 × 10 zuschrauben (Moosgummi-Dichtband), den Stopfen 10 ins Service-Fenster (HDMI, USB-C) und den Stopfen 16 in den SD-Schlitz drücken.", "Kabel und Deckel zu", "Kabel von Kopf und Lampen in einer Schlaufe hinter dem Kopf durch den Kabelkamin führen. Deckel mit 6 × M3 × 10 zuschrauben (Moosgummi-Dichtband), HDMI-Stopfen einsetzen."],
	["Fertig", "In MoveEye Tilt auf ±60° und Pan auf ±90° begrenzen. Weitwinkel-Kamera, Tasten und Status-LED im Selbsttest prüfen. Vor dem Druck die Masse «Nachmessen» prüfen (IR-Modul, Linse der Weitwinkel-Kamera, CAM-Buchsen am Pi, UPS HAT (E) mit Akkus).", "Fertig", "In MoveEye Tilt auf ±60° und Pan auf ±90° begrenzen. Vor dem Druck des Unterteils die Masse des UPS HAT (E) mit Akkus nachmessen (siehe Anleitung)."],
]
# Bauen (real-bauen): Varianten, Einkauf, Drucken, Werkzeug, Sicherheit, Verkabeln, Software, Inbetriebnahme, Fehlersuche, Wartung
const BAU := {
	"varianten": [
		{
			"id": "gehaeuse",
			"titel": "Gehäuse",
			"werte": [
				{
					"id": "v51",
					"name": "v5.1 (ohne Weitwinkel)"
				},
				{
					"id": "v52",
					"name": "v5.2 (Standard): + Weitwinkel, IR-LED, Tasten, Status-LED"
				}
			]
		},
		{
			"id": "akku",
			"titel": "Strom",
			"werte": [
				{
					"id": "ups",
					"name": "mit Akku (UPS HAT (E), 4 × 21700)"
				},
				{
					"id": "netz",
					"name": "ohne Akku (12-V-Netzteil)"
				},
				{
					"id": "entwicklung",
					"name": "Entwicklung: Sockel statt Akku, Pi-Netzteil"
				}
			]
		},
		{
			"id": "mover",
			"titel": "Mover",
			"werte": [
				{
					"id": "ohne",
					"name": "ohne Mover"
				},
				{
					"id": "mover",
					"name": "mit Mover (Kettenfahrzeug) – folgt später"
				}
			]
		}
	],
	"variante_standard": {
		"gehaeuse": "v52",
		"akku": "ups",
		"mover": "ohne"
	},
	"haendler": {
		"bastelgarage": {
			"name": "Bastelgarage.ch",
			"suche": "https://www.bastelgarage.ch/search?sSearch={q}"
		},
		"berrybase": {
			"name": "BerryBase",
			"suche": "https://www.berrybase.ch/search?search={q}"
		},
		"pishop": {
			"name": "Pi-Shop.ch",
			"suche": "https://www.pi-shop.ch/search?sSearch={q}"
		},
		"galaxus": {
			"name": "Galaxus / Digitec",
			"suche": "https://www.galaxus.ch/de/search?q={q}"
		},
		"conrad": {
			"name": "Conrad.ch",
			"suche": "https://www.conrad.ch/de/search.html?search={q}"
		}
	},
	"druck": {
		"teile": [
			{
				"datei": "01_Unterteil",
				"stueck": 1,
				"fuellung": 15,
				"waende": 4,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 8.0,
				"liegt": "Boden",
				"wenn": "v51"
			},
			{
				"datei": "01_Unterteil_v52",
				"stueck": 1,
				"fuellung": 15,
				"waende": 4,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 8.5,
				"liegt": "Boden – Kamera-Rippen und Kabelkamm mit 45°-Unterseiten, ohne Stützen",
				"wenn": "v52"
			},
			{
				"datei": "02_Deckel_mit_Laufring",
				"stueck": 1,
				"fuellung": 15,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.12–0.16",
				"brim": 0,
				"zeit_h": 3.0,
				"liegt": "Unterseite – Rille fein drucken"
			},
			{
				"datei": "03_Drehteller",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.16",
				"brim": 0,
				"zeit_h": 1.2,
				"liegt": "Oberseite"
			},
			{
				"datei": "04_Gabel_mit_Arm1",
				"stueck": 1,
				"fuellung": 25,
				"waende": 4,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 5,
				"zeit_h": 2.2,
				"liegt": "Gabelboden"
			},
			{
				"datei": "05_Arm2_Lagerseite",
				"stueck": 1,
				"fuellung": 25,
				"waende": 4,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 0.8,
				"liegt": "Innenseite"
			},
			{
				"datei": "06_Kamerakopf",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 5,
				"zeit_h": 2.8,
				"liegt": "rechte Seitenwand",
				"wenn": "v51"
			},
			{
				"datei": "07_Seitendeckel",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 5,
				"zeit_h": 0.9,
				"liegt": "Aussenseite"
			},
			{
				"datei": "08_Lampenhalter_2x",
				"stueck": 2,
				"fuellung": 25,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 1.0,
				"liegt": "Rückseite"
			},
			{
				"datei": "09_Zwischenboden",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 0.4,
				"liegt": "flach"
			},
			{
				"datei": "10_HDMI_Stopfen",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.16",
				"brim": 0,
				"zeit_h": 0.3,
				"liegt": "Flansch",
				"wenn": "v51"
			},
			{
				"datei": "11_Fuss_4x",
				"stueck": 4,
				"fuellung": 30,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.16",
				"brim": 0,
				"zeit_h": 0.4,
				"liegt": "Fuss, Zapfen nach oben"
			},
			{
				"datei": "12_Blindstopfen_Weitwinkel",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.3,
				"wenn": "v52",
				"liegt": "Flansch unten (nur ohne Weitwinkel-Kamera)"
			},
			{
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"wenn": "v52",
				"datei": "10_Stopfen_HDMI_USB_v52",
				"zeit_h": 0.4,
				"liegt": "Flansch unten"
			},
			{
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"wenn": "v52",
				"datei": "16_Stopfen_SD_v52",
				"zeit_h": 0.2,
				"liegt": "Flansch unten"
			},
			{
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"wenn": "v52",
				"datei": "14_Diffusor_Status_LED",
				"zeit_h": 0.3,
				"liegt": "Zapfen unten, PETG natur/weiss"
			},
			{
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"wenn": "v52",
				"datei": "15_Pupillenring",
				"zeit_h": 0.1,
				"liegt": "flach, PETG schwarz"
			},
			{
				"datei": "06_Kamerakopf_v52",
				"stueck": 1,
				"fuellung": 20,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 5,
				"zeit_h": 2.8,
				"liegt": "rechte Seitenwand",
				"wenn": "v52"
			},
			{
				"datei": "13_Entwicklungs_Sockel",
				"stueck": 1,
				"fuellung": 15,
				"waende": 3,
				"stuetzen": false,
				"schicht": "0.20",
				"brim": 0,
				"zeit_h": 2.0,
				"wenn": "entwicklung",
				"liegt": "Rahmen unten (Bolzen oben)"
			},
			{
				"datei": "17_Blindstopfen_Reserve",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.2,
				"wenn": "v52",
				"liegt": "Flansch unten"
			},
			{
				"datei": "18_Stopfen_Waermebild",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.3,
				"wenn": "v52",
				"liegt": "Flansch unten (nur Kopf ohne Wärmebild)"
			},
			{
				"datei": "19_Stopfen_IR_Modul",
				"stueck": 1,
				"fuellung": 20,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.4,
				"wenn": "v52",
				"liegt": "Rückseite unten (nur ohne IR-Modul; die Madenschraube M3 hält ihn)"
			},
			{
				"datei": "20_Stopfen_DS18B20",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.1,
				"wenn": "v52",
				"liegt": "Flansch unten (nur ohne Temperaturfühler; Flansch aussen am Boden)"
			},
			{
				"datei": "21_Stopfen_Relais",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.2,
				"wenn": "v52",
				"liegt": "Flansch unten (nur ohne Relais; gleiche Form wie 17)"
			},
			{
				"datei": "23_Stopfen_Mikrofon",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.1,
				"wenn": "v52",
				"liegt": "Flansch unten (nur ohne Mikrofon; 5 Stifte im Presssitz)"
			},
			{
				"datei": "24_Stopfen_Lichtleiter",
				"stueck": 1,
				"fuellung": 100,
				"waende": 2,
				"stuetzen": false,
				"schicht": "0.12",
				"brim": 0,
				"zeit_h": 0.1,
				"wenn": "v52",
				"liegt": "Flansch unten (nur ohne Lade-LED; Presssitz mit Quetschrippen)"
			}
		],
		"hinweise": [
			"Material PETG (z. B. Bambu PETG HF), vorher 6–8 h bei 65 °C trocknen.",
			"Bambu Studio: Drucker «Bambu Lab X2D», Profil «Bambu PETG HF», 0,20 mm Standard; die 3MF-Dateien öffnen und die Werte dieser Tabelle setzen.",
			"Alle Teile sind schon richtig gedreht und brauchen keine Stützen.",
			"Glatte PEI-Platte: dünn Klebestift als Trennmittel (PETG haftet sonst zu stark); strukturierte PEI-Platte ohne.",
			"Für den Deckel die Rille des Laufrings fein drucken (variable Schichthöhe 0,12–0,16 mm).",
			"Ein fertiges Slicer-Profil liegt nicht bei: es müsste in Bambu Studio erstellt und am X2D getestet werden."
		],
		"zeit_hinweis": "Druckzeit: Schätzung, im Slicer nachsehen."
	},
	"werkzeug": [
		"3D-Drucker (Bambu Lab X2D) und Filament-Trockner",
		"Lötkolben mit Temperaturregler, Lötzinn (bleifrei), Ablage",
		"Multimeter (Spannung, Durchgang)",
		"Seitenschneider, Abisolierzange, Pinzette",
		"Schraubendreher Kreuz PH0 / PH1 und Innensechskant 1,5 / 2 / 2,5 mm",
		"Heissklebepistole, Schrumpfschlauch und Heissluft (oder Feuerzeug)",
		"Kabelbinder, Klettband, doppelseitiges Schaumklebeband, Moosgummi-Dichtband",
		"Schutzbrille, gut gelüfteter Platz"
	],
	"schrauben": [
		{
			"menge": "4×",
			"was": "M2,5 × 6",
			"schritt": 3
		},
		{
			"menge": "2×",
			"was": "M3 × 8",
			"schritt": 5
		},
		{
			"menge": "2×",
			"was": "M2 × 8",
			"schritt": 8
		},
		{
			"menge": "4×",
			"was": "M3 × 8 (Gabel → Drehteller)",
			"schritt": 9
		},
		{
			"menge": "4× + 2×",
			"was": "M2 × 4 (Camera Module 3) + M2 × 6 (Thermal-90)",
			"schritt": 10
		},
		{
			"menge": "3×",
			"was": "M3 × 10 Linsenkopf ISO 7380 (Seitendeckel)",
			"schritt": 10
		},
		{
			"menge": "2× + 1×",
			"was": "M3 × 10 + Mutter, M3 × 12 (Achse), 2–3 Scheiben",
			"schritt": 11
		},
		{
			"menge": "4×",
			"was": "M3 × 8 + Unterlegscheibe M3 (Lampenhalter)",
			"schritt": 12
		},
		{
			"menge": "6×",
			"was": "M3 × 10",
			"schritt": 13
		},
		{
			"menge": "4×",
			"was": "M2,5 × 6 (Pi auf Sockel 13)",
			"schritt": 4,
			"wenn": "entwicklung"
		}
	],
	"sicherheit": [
		{
			"thema": "akku",
			"text": "Akkus 21700 sind ungeschützt: nie kurzschliessen, Polung prüfen, 4 gleiche Zellen gleicher Ladung, beschädigte Zellen nicht verwenden, nicht unbeaufsichtigt laden.",
			"wenn": "ups"
		},
		{
			"thema": "strom",
			"text": "Die Ladebuchse GX16 hat keinen Verpolungsschutz: Polung des Steckers vor dem ersten Einstecken mit dem Multimeter messen. Die Sicherung 5 A direkt hinter die Buchse."
		},
		{
			"thema": "strom",
			"text": "Den Ausgang jedes Step-Down-Wandlers zuerst ohne Last messen (5,0–5,2 V), erst dann Pi, Servos oder Verstärker anschliessen. Nie unter Strom verkabeln."
		},
		{
			"thema": "loeten",
			"text": "Löten: Schutzbrille, Rauch nicht einatmen (lüften), heissen Kolben immer in die Ablage, danach Hände waschen."
		},
		{
			"thema": "servo",
			"text": "Servos: beim ersten Einschalten Finger weg vom Drehteller und vom Kopf; zuerst die Grenzen setzen (Pan ±90°, Tilt ±60°). Der Not-Aus steht auf der Seite Servos."
		},
		{
			"thema": "licht",
			"text": "IR-Licht 850 nm ist fast unsichtbar, aber hell: nicht aus der Nähe in die Lampe schauen."
		}
	],
	"verkabelung": {
		"knoten": {
			"gx16": {
				"name": "Ladebuchse GX16",
				"x": 4,
				"y": 12
			},
			"fuse": {
				"name": "Sicherung 5 A",
				"x": 4,
				"y": 30
			},
			"d36": {
				"name": "D36V50F5 (5 V)",
				"x": 4,
				"y": 48
			},
			"ups": {
				"name": "UPS HAT (E)",
				"x": 4,
				"y": 68,
				"wenn": "ups"
			},
			"buck": {
				"name": "Step-Down 5 V 4 A",
				"x": 4,
				"y": 88
			},
			"pi": {
				"name": "Raspberry Pi 5",
				"x": 40,
				"y": 50
			},
			"fan": {
				"name": "Lüfter (Active Cooler)",
				"x": 40,
				"y": 12
			},
			"cam0": {
				"name": "Camera Module 3 NoIR",
				"x": 22,
				"y": 4
			},
			"cam1": {
				"name": "Weitwinkel-Kamera",
				"x": 58,
				"y": 4,
				"wenn": "v52"
			},
			"therm": {
				"name": "Thermal-90",
				"x": 22,
				"y": 24
			},
			"pca": {
				"name": "PCA9685 (0x41)",
				"x": 74,
				"y": 40
			},
			"pan": {
				"name": "Servo Pan",
				"x": 96,
				"y": 10
			},
			"tilt": {
				"name": "Servo Tilt",
				"x": 96,
				"y": 24
			},
			"mosfet": {
				"name": "MOSFET-Modul",
				"x": 96,
				"y": 40
			},
			"lampw": {
				"name": "Lampe weiss",
				"x": 96,
				"y": 52
			},
			"lampir": {
				"name": "Lampe IR 850 nm",
				"x": 96,
				"y": 62
			},
			"irled": {
				"name": "IR-Modul 120°",
				"x": 96,
				"y": 72,
				"wenn": "v52"
			},
			"sled": {
				"name": "Status-LED RGB",
				"x": 96,
				"y": 84,
				"wenn": "v52"
			},
			"tasten": {
				"name": "2 Tasten",
				"x": 74,
				"y": 92,
				"wenn": "v52"
			},
			"pir": {
				"name": "PIR AS312",
				"x": 58,
				"y": 92
			},
			"ds18": {
				"name": "DS18B20",
				"x": 40,
				"y": 92
			},
			"relay": {
				"name": "Relais",
				"x": 22,
				"y": 92
			},
			"i2c": {
				"name": "I2C: BME280, MPU-6050, INA219",
				"x": 74,
				"y": 70
			},
			"hub": {
				"name": "USB-Hub",
				"x": 58,
				"y": 26
			},
			"sound": {
				"name": "USB-Soundkarte",
				"x": 74,
				"y": 14
			},
			"mic": {
				"name": "USB-Mikrofon",
				"x": 58,
				"y": 14
			},
			"pam": {
				"name": "PAM8403",
				"x": 22,
				"y": 70
			},
			"spk": {
				"name": "Lautsprecher 4 Ω",
				"x": 22,
				"y": 82
			},
			"motor": {
				"name": "Motor-HAT (0x60) + Fahrwerk",
				"x": 58,
				"y": 70,
				"wenn": "mover"
			},
			"fuse2": {
				"name": "Sicherung 5 A (Akku)",
				"x": 14,
				"y": 78,
				"wenn": "ups"
			}
		},
		"verbindungen": [
			{
				"id": "pca_i2c",
				"von": "pi",
				"nach": "pca",
				"art": "i2c",
				"pins": "3,3 V Pin 1 · GND Pin 6 · SDA Pin 3 (GPIO 2) · SCL Pin 5 (GPIO 3) · I2C 0x41 (Lötbrücke A0)",
				"code": "pca_address",
				"wert": "0x41"
			},
			{
				"id": "pan",
				"von": "pca",
				"nach": "pan",
				"art": "pwm",
				"pins": "Kanal 0 · Signal orange, + rot (V+), − braun",
				"code": "pca_pan_ch",
				"wert": "0"
			},
			{
				"id": "tilt",
				"von": "pca",
				"nach": "tilt",
				"art": "pwm",
				"pins": "Kanal 1 · Signal orange, + rot (V+), − braun",
				"code": "pca_tilt_ch",
				"wert": "1"
			},
			{
				"id": "akku_buck",
				"von": "ups",
				"nach": "fuse2",
				"art": "strom",
				"pins": "Akku-Lötpunkte B+ / B− des UPS HAT (E) (12–16,8 V) → Flachsicherung 5 A in B+ (fliegender Halter, nahe am HAT). Ersatz: USB-A-5-V-Buchse des HAT",
				"wenn": "ups"
			},
			{
				"id": "akku_buck2",
				"von": "fuse2",
				"nach": "buck",
				"art": "strom",
				"wenn": "ups",
				"pins": "nach der Sicherung → eigener Step-Down 6–36 V → 5 V (VIN / GND)"
			},
			{
				"id": "servo_strom",
				"von": "buck",
				"nach": "pca",
				"art": "strom",
				"pins": "5 V → Klemme V+ / GND des PCA9685, Elko 470 µF an V+",
				"wenn": "ups"
			},
			{
				"id": "servo_strom_netz",
				"von": "fuse",
				"nach": "buck",
				"art": "strom",
				"pins": "12 V nach der Sicherung → Step-Down → 5 V an V+ des PCA9685",
				"wenn": "netz",
				"unklar": "Variante ohne Akku ist im Gehäuse v5.1 nicht beschrieben (Vorschlag)"
			},
			{
				"id": "licht_w",
				"von": "pca",
				"nach": "mosfet",
				"art": "pwm",
				"pins": "Kanal 2 → MOSFET 1 → Lampe weiss (Einstellung «Licht weiss: PCA9685 Kanal 2»)",
				"code": "doku_licht_weiss",
				"wert": "2"
			},
			{
				"id": "licht_ir",
				"von": "pca",
				"nach": "mosfet",
				"art": "pwm",
				"pins": "Kanal 3 → MOSFET 2 → Lampe IR 850 nm (Einstellung «Infrarotlicht: PCA9685 Kanal 3»)",
				"code": "doku_licht_ir",
				"wert": "3"
			},
			{
				"id": "lampen",
				"von": "mosfet",
				"nach": "lampw",
				"art": "strom",
				"pins": "5 V über Vorwiderstand 2 W",
				"unklar": "Wert der Vorwiderstände noch offen (je nach LED)"
			},
			{
				"id": "lampen_ir",
				"von": "mosfet",
				"nach": "lampir",
				"art": "strom",
				"pins": "5 V über Vorwiderstand 2 W"
			},
			{
				"id": "ir_breit",
				"von": "pca",
				"nach": "irled",
				"art": "pwm",
				"pins": "Kanal 4 → 3. MOSFET-Modul (AOD4184, 1 Kanal) → 5 V über Vorwiderstand 2 W → IR-Modul 120° 850 nm («IR-Licht breit»); nur bei IR_TYP «5mm» (v52.py): 47 Ω / 0,5 W → IR-LED 5 mm (ca. 70 mA)",
				"code": "weit_ir_ch",
				"wert": "4",
				"wenn": "v52",
				"unklar": "Wert des Vorwiderstands je nach Modul (wie bei den Scheinwerfern)"
			},
			{
				"id": "led_rgb",
				"von": "pca",
				"nach": "sled",
				"art": "pwm",
				"pins": "Kanal 5 rot · 6 grün · 7 blau, gemeinsame Kathode (Einstellung «LED-Typ»); keine eigenen Vorwiderstände: 220 Ω sind auf dem PCA9685-Board",
				"code": "led_ch_rgb",
				"wert": "5/6/7",
				"wenn": "v52",
				"unklar": "gilt nur mit 220 Ω auf dem PCA9685-Board (Adafruit 815 oder Klon?) – klärt Daniel"
			},
			{
				"id": "tasten",
				"von": "pi",
				"nach": "tasten",
				"art": "gpio",
				"pins": "«Schutz» GPIO 16 (Pin 36) · «Alarm quittieren» GPIO 26 (Pin 37) · je gegen GND, interner Pull-up",
				"code": "btn_gpio",
				"wert": "16/26",
				"wenn": "v52"
			},
			{
				"id": "pir",
				"von": "pi",
				"nach": "pir",
				"art": "gpio",
				"pins": "3,3 V · GND · Ausgang GPIO 5 (Pin 29); in MoveEye unter Zusatzgeräte als Bewegungsmelder eintragen",
				"code": "doku_pir",
				"wert": "5"
			},
			{
				"id": "ds18",
				"von": "pi",
				"nach": "ds18",
				"art": "gpio",
				"pins": "3,3 V · GND · Daten GPIO 4 (Pin 7) + 4,7 kΩ nach 3,3 V; config.txt: dtoverlay=w1-gpio",
				"code": "doku_ds18",
				"wert": "4"
			},
			{
				"id": "relay",
				"von": "pi",
				"nach": "relay",
				"art": "gpio",
				"pins": "IN GPIO 22 (Pin 15) · VCC 5 V · GND",
				"code": "gpio_relay",
				"wert": "22"
			},
			{
				"id": "i2c_sens",
				"von": "pi",
				"nach": "i2c",
				"art": "i2c",
				"pins": "am selben I2C wie der PCA9685: BME280 0x76 / 0x77 · MPU-6050 0x68 · INA219 0x44 (optional, Solar)",
				"code": "solar_addr",
				"wert": "0x44"
			},
			{
				"id": "therm",
				"von": "pi",
				"nach": "therm",
				"art": "spi",
				"pins": "SPI0 + I2C 0x40, GPIO 7 / 23 / 24 (Kabel MX1.25 10-polig)",
				"unklar": "genaue Belegung des 10-poligen Kabels: Waveshare-Wiki, nicht mit dem echten Modul geprüft"
			},
			{
				"id": "cam0",
				"von": "pi",
				"nach": "cam0",
				"art": "csi",
				"pins": "CAM0, Kabel 22→15-polig 500 mm, Kontakte zur Platine",
				"unklar": "Anschluss CAM0 nur aus der Doku v5.2 abgeleitet (Weitwinkel = CAM1)"
			},
			{
				"id": "cam1",
				"von": "pi",
				"nach": "cam1",
				"art": "csi",
				"pins": "CAM1, Kabel 22→15-polig 200 mm, in MoveEye «Raspberry Pi camera 1»",
				"wenn": "v52"
			},
			{
				"id": "fan",
				"von": "pi",
				"nach": "fan",
				"art": "strom",
				"pins": "FAN-Anschluss des Pi 5 (4-polig JST)"
			},
			{
				"id": "hub",
				"von": "pi",
				"nach": "hub",
				"art": "usb",
				"pins": "USB-A des Pi → Hub (Kabel ≥ 15 cm)"
			},
			{
				"id": "sound",
				"von": "hub",
				"nach": "sound",
				"art": "usb",
				"pins": "USB-Soundkarte im Hub"
			},
			{
				"id": "mic",
				"von": "hub",
				"nach": "mic",
				"art": "usb",
				"pins": "USB-Mikrofon über Verlängerung 15 cm (vorne oben)"
			},
			{
				"id": "pam_in",
				"von": "sound",
				"nach": "pam",
				"art": "audio",
				"pins": "Klinke 3,5 mm → Eingang L / GND des PAM8403"
			},
			{
				"id": "pam_strom",
				"von": "buck",
				"nach": "pam",
				"art": "strom",
				"pins": "5 V / GND"
			},
			{
				"id": "spk",
				"von": "pam",
				"nach": "spk",
				"art": "audio",
				"pins": "Ausgang L+ / L− → Lautsprecher 4 Ω"
			},
			{
				"id": "laden",
				"von": "gx16",
				"nach": "fuse",
				"art": "strom",
				"pins": "12–40 V, je 2 Kontakte parallel für + und −"
			},
			{
				"id": "laden2",
				"von": "fuse",
				"nach": "d36",
				"art": "strom",
				"pins": "Sicherung 5 A → VIN / GND des D36V50F5"
			},
			{
				"id": "laden3",
				"von": "d36",
				"nach": "ups",
				"art": "strom",
				"pins": "5 V → USB-C-Stecker (56 kΩ auf CC) → USB-C des UPS HAT (E)",
				"wenn": "ups"
			},
			{
				"id": "ups_pi",
				"von": "ups",
				"nach": "pi",
				"art": "strom",
				"pins": "5 V / 6 A über Pogo-Pins, Akku-Chip I2C 0x2D",
				"code": "ups_e_addr",
				"wert": "0x2D",
				"wenn": "ups"
			},
			{
				"id": "netz_pi",
				"von": "d36",
				"nach": "pi",
				"art": "strom",
				"pins": "5 V → USB-C des Pi 5 direkt; im EEPROM PSU_MAX_CURRENT=5000 setzen (Schritt «Netzteil-Grenze»), sonst USB nur 600 mA",
				"wenn": "netz"
			},
			{
				"id": "ladeled",
				"von": "pi",
				"nach": "gx16",
				"art": "gpio",
				"pins": "GPIO 6 (Pin 31) → 330 Ω → Lade-LED 3 mm grün → GND (Pin 34); Lichtleiter hinten. MoveEye schaltet sie nach dem Lade-Zustand des UPS HAT (E)",
				"code": "charge_led_gpio",
				"wert": "6"
			},
			{
				"id": "mover",
				"von": "pi",
				"nach": "motor",
				"art": "i2c",
				"pins": "I2C 0x60 · Motor M1 = links, M2 = rechts",
				"code": "mover_addr",
				"wert": "0x60",
				"wenn": "mover",
				"unklar": "folgt später: Fahrwerk, Motorstrom und Befestigung (Stativmutter 1/4\")"
			}
		]
	},
	"software": [
		{
			"titel": "Pi OS auf die Karte",
			"text": "Mit dem Raspberry Pi Imager «Raspberry Pi OS (64-bit)», Bookworm, auf die microSD schreiben. Im Imager Hostname, Benutzer, WLAN und SSH einstellen."
		},
		{
			"titel": "MoveEye holen und einrichten",
			"text": "Auf dem Pi im Terminal (ohne sudo). Das Skript installiert die Pakete, schaltet I2C, SPI und Kamera ein, richtet den Dienst ein, lädt das KI-Modell und macht den Selbsttest. Zuerst mit --trocken ansehen.",
			"befehl": "git clone https://github.com/DonElektro/MotionWatch.git\ncd MotionWatch\nbash werkzeuge/einrichten.sh --trocken\nbash werkzeuge/einrichten.sh"
		},
		{
			"titel": "Wärmebild-Treiber",
			"text": "Für die Thermal-90: im Waveshare-Wiki «Thermal_Camera_Hat.zip» laden, im Ordner pysenxor-master installieren.",
			"befehl": "pip install --break-system-packages -e ./"
		},
		{
			"titel": "Netzteil-Grenze des Pi 5",
			"text": "Der UPS HAT (E) und der 5-V-Wandler melden kein USB-PD. Ohne diese Zeile drosselt der Pi 5 USB auf 600 mA und meldet «schwaches Netzteil». Im Editor die Zeile PSU_MAX_CURRENT=5000 ergänzen, speichern, neu starten (schaltet auch usb_max_current_enable ein).",
			"befehl": "sudo rpi-eeprom-config --edit"
		},
		{
			"titel": "Neu starten und prüfen",
			"text": "Nach dem Neustart: I2C-Geräte und Kamera prüfen. Erwartet: 40 Thermal-90, 41 PCA9685, 2d UPS HAT (E), dazu 68 / 76 / 77 / 44 je nach Sensoren.",
			"befehl": "sudo i2cdetect -y 1\nrpicam-hello --list-cameras"
		},
		{
			"titel": "Webseite öffnen, Passwort",
			"text": "Im Browser http://<IP-des-Pi>:5000/ öffnen (eigenes WLAN des Pi: http://10.42.0.1:5000/) und gleich ein Web-Passwort festlegen. Der QR-Code unten führt auf diese Seite.",
			"link": "qr"
		},
		{
			"titel": "Erster Start: Einrichtungs-Assistent",
			"text": "Beim ersten Öffnen führt der Assistent durch Sprache, Name, Push und Schutz. Später: Live → «🧭 Einrichtungs-Assistent».",
			"link": "/?guide=1"
		},
		{
			"titel": "Updates",
			"text": "MoveEye holt neue, signierte Versionen selbst (Einstellungen → System → Updates).",
			"link": "/settings"
		}
	],
	"inbetriebnahme": [
		{
			"titel": "Servos kalibrieren",
			"text": "Seite Servos: Mitte prüfen, Grenzen Pan ±90° und Tilt ±60° setzen, Richtung umkehren falls nötig, Nachschwingen ansehen.",
			"link": "/servo"
		},
		{
			"titel": "Kamera ausrichten",
			"text": "Im Live-Bild prüfen, ob der Kopf geradeaus schaut und das Bild nicht gedreht ist; Fokus der Camera Module 3 ist automatisch.",
			"link": "/cams"
		},
		{
			"titel": "Wärmebild ausrichten",
			"text": "Wärmebild über das Kamerabild legen (Zoom, Verschiebung).",
			"link": "/thermal_align"
		},
		{
			"titel": "Licht und Ton",
			"text": "Einstellungen → Licht & Ton: Licht weiss auf PCA9685 Kanal 2, Infrarot auf Kanal 3 stellen, dann Licht und Sirene kurz testen.",
			"link": "/settings"
		},
		{
			"titel": "Selbsttest und Diagnose",
			"text": "Werkzeuge: Selbstdiagnose und Hardware-Prüfung – alles grün? Sonst Reiter «Fehlersuche».",
			"link": "/tools"
		},
		{
			"titel": "Erste Testnacht",
			"text": "Schutz «Wachsam», eine Nacht laufen lassen, morgens Verlauf ansehen; den Bericht nach feedback/ hochladen.",
			"link": "/recordings"
		}
	],
	"fehlersuche": [
		"HW_PCA9685",
		"SERVO_NONE",
		"HW_SERVO_JITTER",
		"CAM_NONE",
		"THERMAL",
		"HW_I2C",
		"HW_UPS",
		"POWER_LOW",
		"BATT_LOW",
		"HW_LIGHT",
		"HW_SOUND",
		"MIC",
		"CPU_HOT"
	],
	"wartung": [
		{
			"teil": "Drehlager (Kugeln)",
			"wann": "alle 6 Monate",
			"was": "leichtgängig? Wenig Silikonfett nachgeben."
		},
		{
			"teil": "Servos MG90S",
			"wann": "monatlich (Servo-Diagnose)",
			"was": "Zittern, Brummen, Spiel? Verschleissteil – Ersatz-Servo bereithalten."
		},
		{
			"teil": "Akkus 21700",
			"wann": "alle 3 Monate, jährlich ersetzen prüfen",
			"was": "Zellspannungen in MoveEye gleich? Aufgebläht oder warm = sofort raus.",
			"wenn": "ups"
		},
		{
			"teil": "Dichtungen, Deckel, Stopfen",
			"wann": "vor jeder Saison",
			"was": "Moosgummi, Kabelverschraubung und Stopfen (Service-Fenster, SD-Schlitz, Reserve) dicht? Innen trocken?"
		},
		{
			"teil": "Linsen und Fenster",
			"wann": "monatlich",
			"was": "Kamera, Wärmebild und PIR mit weichem Tuch reinigen (Tau, Spinnweben)."
		},
		{
			"teil": "Lüfter und Lüftungsschlitze",
			"wann": "alle 6 Monate",
			"was": "Staub entfernen; CPU-Temperatur in MoveEye unter 80 °C?"
		},
		{
			"teil": "microSD-Karte",
			"wann": "wenn MoveEye warnt",
			"was": "Abnutzung der Karte (Selbstdiagnose); Sicherung machen, Ersatzkarte bereithalten."
		},
		{
			"teil": "Schrauben und Kabel",
			"wann": "alle 6 Monate",
			"was": "Kabelschlaufe hinter dem Kopf scheuert nicht? Achse von Arm 2 nicht zu fest?"
		}
	],
	"extra_schritte": [
		{
			"wenn": "netz",
			"titel": "Ohne Akku",
			"text": "Schritt 4 ohne UPS HAT und Akkus: den Pi direkt in den Zaun stellen (Klettband). Der D36V50F5 speist den Pi über USB-C, das 12-V-Netzteil kommt an die GX16-Buchse."
		},
		{
			"wenn": "v52",
			"titel": "Variante v5.2",
			"text": "Weitwinkel-Kamera in die Stirnwand (CAM1), IR-Modul 120° rechts neben die Kamera (Madenschraube M3), 2 Tasten in die Rückwand, Status-LED oben in den Kopf. Druckdateien: Druckdateien/v5-2/. Fehlt ein Teil im Paket, kommt der passende Stopfen hinein (12, 18–24).",
			"unklar": "Masse «Nachmessen» vor dem Druck prüfen"
		},
		{
			"wenn": "mover",
			"titel": "Mover",
			"text": "Motor-HAT auf den Pi bzw. an I2C (0x60), Motoren M1 links und M2 rechts, das Gehäuse mit der Stativmutter 1/4\" auf das Fahrwerk schrauben. In MoveEye erscheint der zweite Stick von selbst.",
			"unklar": "folgt später: Fahrwerk, Motorstrom und Befestigung (Stativmutter 1/4\")"
		},
		{
			"wenn": "entwicklung",
			"titel": "Entwicklungs-Variante ohne Akku",
			"text": "Statt UPS HAT (E) und Akkus den Sockel 13 in den Akku-Zaun drücken (Klemmrippen), den Pi mit 4 × M2,5 × 6 auf die Bolzen schrauben – gleiche Lage und Höhe wie mit Akku, HDMI-/USB-C-Fenster und Kamerakabel passen. Der Pi bekommt Strom über sein eigenes USB-C-Netzteil (5,1 V / 5 A) durch das Service-Fenster. Servos, Lampen und Verstärker: das 12-V-Netzteil (mind. 3 A) an die GX16-Ladebuchse (Pins wie beim Laden: 2 Kontakte +, 2 Kontakte −); die 5-A-Sicherung bleibt in der Leitung, dahinter auf den Eingang des Step-down (6–36 V → 5 V). Nur 12 V verwenden, Polung prüfen – es gibt keinen Verpolungsschutz. In dieser Variante zeigen Akku-%, INA219 und Lade-LED nichts."
		},
		{
			"wenn": "v52",
			"titel": "SD-Karte (v5.2)",
			"text": "Die microSD-Karte steckt nicht im Pi, sondern im Einbau-Kartenhalter der Verlängerung (15 cm) hinter dem SD-Schlitz der Stirnwand: Karte wechseln ohne das Gehäuse zu öffnen. Stopfen 16 abziehen, Karte herausnehmen bzw. einschieben, Stopfen wieder eindrücken. Vorher MoveEye herunterfahren."
		}
	],
	"druckdateien_einzeln": [
		"MoveEye_v5-1_01_Unterteil.3mf",
		"MoveEye_v5-1_02_Deckel_mit_Laufring.3mf",
		"MoveEye_v5-1_03_Drehteller.3mf",
		"MoveEye_v5-1_04_Gabel_mit_Arm1.3mf",
		"MoveEye_v5-1_05_Arm2_Lagerseite.3mf",
		"MoveEye_v5-1_06_Kamerakopf.3mf",
		"MoveEye_v5-1_07_Seitendeckel.3mf",
		"MoveEye_v5-1_08_Lampenhalter_2x.3mf",
		"MoveEye_v5-1_09_Zwischenboden.3mf",
		"MoveEye_v5-1_10_HDMI_Stopfen.3mf",
		"MoveEye_v5-1_11_Fuss_4x.3mf",
		"v5-2/MoveEye_v5-2_01_Unterteil_v52.3mf",
		"v5-2/MoveEye_v5-2_02_Deckel_mit_Laufring.3mf",
		"v5-2/MoveEye_v5-2_03_Drehteller.3mf",
		"v5-2/MoveEye_v5-2_04_Gabel_mit_Arm1.3mf",
		"v5-2/MoveEye_v5-2_05_Arm2_Lagerseite.3mf",
		"v5-2/MoveEye_v5-2_06_Kamerakopf_v52.3mf",
		"v5-2/MoveEye_v5-2_07_Seitendeckel.3mf",
		"v5-2/MoveEye_v5-2_08_Lampenhalter_2x.3mf",
		"v5-2/MoveEye_v5-2_09_Zwischenboden.3mf",
		"v5-2/MoveEye_v5-2_10_Stopfen_HDMI_USB_v52.3mf",
		"v5-2/MoveEye_v5-2_11_Fuss_4x.3mf",
		"v5-2/MoveEye_v5-2_12_Blindstopfen_Weitwinkel.3mf",
		"v5-2/MoveEye_v5-2_13_Entwicklungs_Sockel.3mf",
		"v5-2/MoveEye_v5-2_14_Diffusor_Status_LED.3mf",
		"v5-2/MoveEye_v5-2_15_Pupillenring.3mf",
		"v5-2/MoveEye_v5-2_16_Stopfen_SD_v52.3mf",
		"v5-2/MoveEye_v5-2_17_Blindstopfen_Reserve.3mf",
		"v5-2/MoveEye_v5-2_18_Stopfen_Waermebild.3mf",
		"v5-2/MoveEye_v5-2_19_Stopfen_IR_Modul.3mf",
		"v5-2/MoveEye_v5-2_20_Stopfen_DS18B20.3mf",
		"v5-2/MoveEye_v5-2_21_Stopfen_Relais.3mf",
		"v5-2/MoveEye_v5-2_23_Stopfen_Mikrofon.3mf",
		"v5-2/MoveEye_v5-2_24_Stopfen_Lichtleiter.3mf"
	],
	"farben": {
		"kopf": "#f59a4a",
		"kopf_teile": [
			"turntable",
			"yoke",
			"arm2",
			"head",
			"side",
			"lamp1",
			"lamp2",
			"head52"
		],
		"grau": "#9a9ea3",
		"grau_teile": [
			"tub",
			"tub52",
			"lid",
			"shelf",
			"feet",
			"plug",
			"plug52",
			"sdplug",
			"resplug",
			"wplug",
			"sockel",
			"irplug"
		],
		"turntable": "#f59a4a",
		"yoke": "#f59a4a",
		"arm2": "#f59a4a",
		"head": "#f59a4a",
		"side": "#f59a4a",
		"lamp1": "#f59a4a",
		"lamp2": "#f59a4a",
		"head52": "#f59a4a"
	},
	"bom_extra": {
		"pi5": {
			"preis": 85,
			"haendler": "pishop",
			"suche": "Raspberry Pi 5 8GB",
			"alt": "4 GB (SC1111) reicht auch",
			"gruppe": "rechner"
		},
		"cooler": {
			"preis": 10.9,
			"haendler": "bastelgarage",
			"suche": "Raspberry Pi 5 Aktiv Kühler",
			"alt": "DFRobot-Kühler (Bastelgarage 423487) passt",
			"gruppe": "rechner"
		},
		"sd": {
			"preis": 15,
			"haendler": "galaxus",
			"suche": "microSD 64GB A2",
			"alt": "jede A2-Karte einer Markenfirma",
			"gruppe": "rechner"
		},
		"cam": {
			"preis": 30,
			"haendler": "pishop",
			"suche": "Camera Module 3 NoIR",
			"gruppe": "rechner"
		},
		"camcable": {
			"preis": 5,
			"haendler": "pishop",
			"suche": "Raspberry Pi 5 Kamerakabel 500mm",
			"gruppe": "rechner"
		},
		"therm": {
			"preis": 70,
			"haendler": "pishop",
			"suche": "Waveshare Thermal Camera",
			"alt": "SKU 31941 ausgelaufen – Nachfolger bei Pi-Shop.ch",
			"gruppe": "rechner"
		},
		"servo": {
			"preis": 15.8,
			"haendler": "bastelgarage",
			"suche": "MG90S",
			"gruppe": "kopf"
		},
		"pca": {
			"preis": 12,
			"haendler": "bastelgarage",
			"suche": "PCA9685",
			"alt": "Klon «PCA9685 16 Kanal»",
			"gruppe": "kopf"
		},
		"elko": {
			"preis": 0.95,
			"haendler": "bastelgarage",
			"suche": "Elko 1000uF 25V",
			"alt": "1000 µF / 25 V geht auch",
			"gruppe": "kopf"
		},
		"bbs": {
			"preis": 5,
			"haendler": "galaxus",
			"suche": "Softair BB 6mm 0.20g",
			"gruppe": "kopf"
		},
		"fett": {
			"preis": 5,
			"haendler": "galaxus",
			"suche": "Silikonfett",
			"gruppe": "kopf"
		},
		"ups": {
			"preis": 36.9,
			"haendler": "bastelgarage",
			"suche": "USV HAT (E) 21700",
			"alt": "Waveshare 27966",
			"wenn": "ups",
			"gruppe": "strom"
		},
		"cells": {
			"preis": 132.92,
			"haendler": "galaxus",
			"suche": "Samsung INR21700-50E",
			"alt": "Molicel P45B; 4 gleiche Zellen aus einer Lieferung",
			"wenn": "ups",
			"gruppe": "strom"
		},
		"charger": {
			"preis": 34,
			"haendler": "berrybase",
			"suche": "Pololu D36V50F5",
			"alt": "nur bei BerryBase (de) gefunden",
			"gruppe": "strom"
		},
		"buck": {
			"preis": 6.9,
			"haendler": "bastelgarage",
			"suche": "Step-Down 6-36V 5V 4A",
			"alt": "Pololu #3782",
			"gruppe": "strom"
		},
		"gx16": {
			"preis": 8.9,
			"haendler": "bastelgarage",
			"suche": "GX16-4P",
			"gruppe": "strom"
		},
		"fuse": {
			"preis": 5,
			"haendler": "galaxus",
			"suche": "Sicherungshalter fliegend ATM",
			"gruppe": "strom"
		},
		"fuse2": {
			"preis": 5,
			"haendler": "galaxus",
			"suche": "Sicherungshalter fliegend ATM",
			"wenn": "ups",
			"gruppe": "strom"
		},
		"usbc": {
			"preis": 1.7,
			"haendler": "berrybase",
			"suche": "USB-C Kabel offenes Ende",
			"alt": "USB-C-Kabel mit offenem Ende (BerryBase 125190)",
			"gruppe": "strom"
		},
		"chled": {
			"preis": 2,
			"haendler": "bastelgarage",
			"suche": "LED 3mm grün",
			"gruppe": "strom"
		},
		"ledw": {
			"preis": 8,
			"haendler": "galaxus",
			"suche": "LED Modul 18mm weiss",
			"gruppe": "licht"
		},
		"ledir": {
			"preis": 8,
			"haendler": "galaxus",
			"suche": "IR LED Modul 850nm",
			"alt": "850 nm statt 940 nm (NoIR sieht es besser)",
			"gruppe": "licht"
		},
		"mosfet": {
			"preis": 9.8,
			"haendler": "bastelgarage",
			"suche": "MOSFET AOD4184",
			"alt": "je ein Modul für weiss (Kanal 2) und IR (Kanal 3); kein IRF520",
			"gruppe": "licht"
		},
		"res": {
			"preis": 1,
			"haendler": "bastelgarage",
			"suche": "Widerstand 2W",
			"gruppe": "licht"
		},
		"spk": {
			"preis": 8.9,
			"haendler": "bastelgarage",
			"suche": "Lautsprecher 4 Ohm 40mm",
			"gruppe": "audio"
		},
		"pam": {
			"preis": 9.9,
			"haendler": "bastelgarage",
			"suche": "PAM8403",
			"alt": "Fermion 3W (Bastelgarage 421925)",
			"gruppe": "audio"
		},
		"sound": {
			"preis": 8,
			"haendler": "galaxus",
			"suche": "USB Soundkarte",
			"gruppe": "audio"
		},
		"mic": {
			"preis": 10,
			"haendler": "galaxus",
			"suche": "USB Mini Mikrofon",
			"gruppe": "audio"
		},
		"usbext": {
			"preis": 5,
			"haendler": "galaxus",
			"suche": "USB-A Verlängerung 15cm",
			"gruppe": "audio"
		},
		"foam": {
			"preis": 3,
			"haendler": "galaxus",
			"suche": "Akustikschaum",
			"gruppe": "audio"
		},
		"pir": {
			"preis": 5.9,
			"haendler": "bastelgarage",
			"suche": "Micro PIR AS312",
			"gruppe": "sensor"
		},
		"mpu": {
			"preis": 10.9,
			"haendler": "bastelgarage",
			"suche": "MPU-6050",
			"gruppe": "sensor"
		},
		"petg": {
			"preis": 20,
			"haendler": "galaxus",
			"suche": "Bambu PETG HF",
			"alt": "eSun PETG (Bastelgarage 421203)",
			"gruppe": "kabel"
		},
		"litze": {
			"preis": 15,
			"haendler": "conrad",
			"suche": "Silikonlitze 20 AWG",
			"gruppe": "kabel"
		},
		"hdmi": {
			"preis": 5,
			"haendler": "berrybase",
			"suche": "Micro-HDMI Kabel",
			"gruppe": "kabel"
		},
		"hub": {
			"preis": 12,
			"haendler": "galaxus",
			"suche": "USB Hub 4 Port kompakt",
			"gruppe": "neu51"
		},
		"ds18": {
			"preis": 5.9,
			"haendler": "bastelgarage",
			"suche": "DS18B20 wasserdicht",
			"alt": "+ Widerstand 4,7 kΩ",
			"gruppe": "neu51"
		},
		"bme": {
			"preis": 17.9,
			"haendler": "bastelgarage",
			"suche": "Gravity BME280",
			"gruppe": "neu51"
		},
		"relay": {
			"preis": 5.5,
			"haendler": "bastelgarage",
			"suche": "1-Kanal Relais Modul",
			"gruppe": "neu51"
		},
		"m12": {
			"preis": 1.5,
			"haendler": "bastelgarage",
			"suche": "Kabelverschraubung M12",
			"alt": "GX12-3P",
			"gruppe": "neu51"
		},
		"ina": {
			"preis": 12.9,
			"haendler": "bastelgarage",
			"suche": "Gravity INA219",
			"optional": true,
			"gruppe": "neu51"
		},
		"lte": {
			"preis": 50,
			"haendler": "galaxus",
			"suche": "LTE USB Stick",
			"optional": true,
			"gruppe": "spaeter"
		},
		"camwide": {
			"preis": 35,
			"haendler": "pishop",
			"suche": "Camera Module 3 Wide NoIR",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"irmod": {
			"preis": 8,
			"haendler": "bastelgarage",
			"suche": "IR LED 850nm 3W Linse 120",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"m2": {
			"preis": 3,
			"haendler": "bastelgarage",
			"suche": "Schraube M2x6 Kunststoff selbstschneidend",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"sdext": {
			"preis": 8,
			"haendler": "galaxus",
			"suche": "microSD Verlängerungskabel 15cm Einbau",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"mosfet3": {
			"preis": 4.9,
			"haendler": "bastelgarage",
			"suche": "MOSFET AOD4184",
			"alt": "dazu Vorwiderstand 47 Ω / 0,5 W; oder ein kleiner Logic-Level-MOSFET (AO3400)",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"irled5": {
			"preis": 1,
			"haendler": "bastelgarage",
			"suche": "IR LED 5mm 850nm",
			"alt": "nur für IR_TYP = «5mm» in v52.py – Standard ist das IR-Modul 120° (irmod), nicht zusätzlich kaufen (+ 47 Ω / 0,5 W)",
			"wenn": "v52",
			"optional": true,
			"gruppe": "v52"
		},
		"res_ir": {
			"preis": 0.5,
			"haendler": "bastelgarage",
			"suche": "Widerstand 2W",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"taster": {
			"preis": 12,
			"haendler": "bastelgarage",
			"suche": "Taster 12mm IP67",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"sled": {
			"preis": 1,
			"haendler": "bastelgarage",
			"suche": "RGB LED 5mm",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"camcable2": {
			"preis": 4,
			"haendler": "pishop",
			"suche": "Raspberry Pi 5 Kamerakabel 200mm",
			"wenn": "v52",
			"gruppe": "v52"
		},
		"psu12": {
			"preis": 20,
			"haendler": "galaxus",
			"suche": "Netzteil 12V 3A",
			"wenn": "netz",
			"gruppe": "strom"
		},
		"psu12_dev": {
			"preis": 20,
			"haendler": "galaxus",
			"suche": "Netzteil 12V 3A",
			"wenn": "entwicklung",
			"gruppe": "strom"
		},
		"lader12": {
			"preis": 20,
			"haendler": "galaxus",
			"suche": "Netzteil 12V 3A",
			"alt": "oder Solar (solar + solarreg, optional); an der GX16 dürfen 12–40 V anliegen",
			"wenn": "ups",
			"gruppe": "strom"
		},
		"solar": {
			"preis": 45,
			"haendler": "galaxus",
			"suche": "Solarpanel 30W 18V",
			"alt": "Strom messen: INA219 (ina, 0x44)",
			"wenn": "ups",
			"optional": true,
			"gruppe": "strom"
		},
		"solarreg": {
			"preis": 15,
			"haendler": "galaxus",
			"suche": "MPPT Solar Laderegler Modul",
			"alt": "der D36V50F5 hat keine MPPT-Regelung: ohne Regler bricht die Spannung bei wenig Sonne ein",
			"wenn": "ups",
			"optional": true,
			"gruppe": "strom"
		},
		"motorhat": {
			"preis": 25,
			"haendler": "pishop",
			"suche": "Motor HAT",
			"alt": "Waveshare Motor Driver HAT",
			"wenn": "mover",
			"gruppe": "mover"
		},
		"chassis": {
			"preis": 60,
			"haendler": "galaxus",
			"suche": "Kettenfahrwerk Roboter",
			"wenn": "mover",
			"gruppe": "mover"
		},
		"schrauben": {
			"preis": 12,
			"haendler": "galaxus",
			"suche": "Schraubensortiment M2 M2.5 M3",
			"gruppe": "kabel"
		},
		"psu_pi": {
			"preis": 15,
			"haendler": "pishop",
			"suche": "Raspberry Pi 27W USB-C Netzteil",
			"wenn": "entwicklung",
			"gruppe": "strom"
		}
	}
}
# Gehäuse-Varianten: id -> {name, teile, ersetzt, druckdateien, anleitung, hinweis, nachmessen (deutsch, T.t übersetzt)}
const GEHAEUSE_VARIANTEN := {
	"v52": {"name": "Variante v5.2: Weitwinkel-Kamera im Unterteil", "teile": ["tub52", "wide", "irled", "mosfet52", "cable_cam1", "cable_cam0_52", "buttons", "sled", "plug52", "sdplug", "head52", "diff52", "resplug", "lampdrv", "fuseh"], "ersetzt": {"tub52": "tub", "mosfet52": "mosfet", "cable_cam0_52": "cable_cam", "plug52": "plug", "head52": "head"}, "druckdateien": ["v5-2/MotionWatch_v5-2_Platte_A_Unterteil.3mf", "v5-2/MotionWatch_v5-2_Platte_B_Deckel_Kopf.3mf"], "anleitung": "Dokumente/LIESMICH_Montage_v5-2.md", "hinweis": "Platte A und B v5.2 ersetzen die Platten v5.1 (Unterteil mit Weitwinkel-Fenster, Service-Fenster HDMI/USB-C, SD-Schlitz; Kopf mit Status-LED). Vor dem Druck die Liste «Nachmessen» prüfen.", "nachmessen": ["IR-Modul: Ø 18,8 mm, Länge 14 mm, Linse vorne Ø 17 mm (IRW_MOD_D, IRW_MOD_L, IRW_LENS_D)", "Weitwinkel-Kamera: Linsenhöhe 11,4 mm ab Platine, Linsenmitte 9,5 mm unter der Platinen-Oberkante, Frontlinse Ø 6 mm (WC_LENS_H, WC_LENS_FROM_TOP, WC_R0)", "Lage der Buchsen CAM/DISP 0 und 1 am Pi 5 (Kabelkamm FPC_X0, PI_CAM0_XY, PI_CAM1_XY)", "Abstände: IR-Modul–Kamera-Fenster (Steg 3,2 mm, Trennsteg 2 mm vor der Wand), IR-Modul–Lautsprecher 11 mm, Kabel–Lüfter 4 mm / Ansaugung 8 mm, Kabel–Lüftungsschlitze 9 mm", "UPS HAT (E) mit Akkus (wie v5.1: angenommen 90 × 80 × 26 mm)", "Service-Fenster: Lage USB-C (x 85) und HDMI am Pi 5; SD: microSD-Verlängerung mit Einbau-Kartenhalter (Lochabstand 18 mm, Platine ca. 22 × 15 mm)", "Lampentreiber: noch unbekannt – Feld 30 × 20 mit 2 Domen M2,5 ist ein Platzhalter (DRV_HOLES); Sicherungshalter 30 × 13 × 10 (FUSE_*)"]},
}
