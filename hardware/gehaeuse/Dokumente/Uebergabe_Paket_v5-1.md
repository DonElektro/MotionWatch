# MotionWatch – Übergabe Gehäuse-Chat (Stand 30.10.2026)

*Kopie von `00_LIES_MICH_ZUERST.md` aus dem Übergabe-Paket v5.1. Pfade wie `Druckdateien_v5-1/` beziehen sich auf das Paket; im Repository siehe `../LIESMICH.md`.*

Dieses Paket enthält den ganzen Stand des **3D-Gehäuses** für «MotionWatch»: Druckdateien, parametrischen Quellcode, Anleitungen, Materialliste mit Bestellliste und die wichtigsten Entscheidungen. Es ist für einen neuen Chat gedacht, der hier weitermacht.

## Hinweise für Claude (bitte zuerst lesen)

- **Besitzer:** Daniel, Schweiz. Antworten auf Deutsch mit «ss» statt «ß», kurz und verständlich. Daniel ist technisch interessiert, aber kein Programmierer.
- **Drucker:** Bambu Lab **X2D** (nicht H2D). Material PETG. Teile immer **ohne Stützen** druckbar machen und Schicht für Schicht prüfen (`printcheck5.py`).
- **Werkzeuge:**
  - OpenSCAD und pip-Pakete von PyPI waren in der alten Umgebung nicht verfügbar. Das Modell ist darum eine eigene kleine **SDF-CSG-Bibliothek in Python** (`csg.py`).
  - Daraus entstehen mit Marching Cubes (scikit-image), Vereinfachung und Reparatur STL- und 3MF-Dateien.
  - Gebraucht werden `numpy`, `scipy`, `scikit-image`, `matplotlib`.
- **Software:** Die Software läuft in einem anderen Chat («Motion Watch Software», Repository `github.com/DonElektro/MotionWatch`, Stand 2.95.x). Wenn sich Hardware oder Gehäuse ändern, gehört das dorthin (siehe `Dokumente/Uebergabe_Gehaeuse_v5.md`, gedacht für `docs/` im Repository).
- **Sicherheit:** Keine Passwörter, privaten ntfy-Themen oder Zugangsdaten in Dateien oder auf GitHub.
- **Materialliste online:** Die abhakbare Liste ist ein Artifact in Daniels claude.ai-Konto, Titel «MotionWatch Materialliste» (privater Link, im Repository weggelassen). Der Stand vom 30.10. liegt hier als `Dokumente/Materialliste.md`.

## Was das Gerät ist

Ein Raspberry Pi 5 mit **Schwenk-/Neigekopf** (2 × MG90S) warnt beim Camping vor Wildtieren und Personen.

- **Kameras im Kopf:** Camera Module 3 **NoIR** und Waveshare **Thermal-90** (80 × 62, Wärmebild).
- **Unterteil:**
  - Akku Waveshare **UPS HAT (E)** mit 4 × 21700.
  - PCA9685 für die Servos.
  - Lautsprecher, nach unten gerichtet.
  - PIR und Mikrofon an der Stirnseite.
  - USB-Hub.
  - Relais.
  - Sensoren.
- **Laden:** über eine Buchse hinten, 12–40 V.

## Stand der Mechanik: Version 5.1

- **Unterteil:**
  - 183 × 97 × 71,5 mm, mit aufgesteckten Füssen 77,5 mm.
  - Gesamthöhe ca. 161 mm.
- **Grundstellung:** Der Kopf schaut **zur Stirnseite mit PIR und Mikrofon** («vorne», Modell-Richtung −x). Die Ladebuchse ist hinten (+x).
- **Pan-Lager:** Ca. 28 Softair-Kugeln 6 mm laufen in einer gedruckten Rille zwischen Deckel und Drehteller. Der Pan-Servo hängt im Deckel.
- **Gabel:** Der Kopf hängt zwischen **zwei Armen**. Der Tilt-Servo sitzt **im Kopf**, sein Horn ist in Arm 1 eingelassen. Arm 2 ist das Lager (M3-Schraube als Achse).
- **Kopf:** Er ist zu einer Seite offen und wird mit einem Seitendeckel geschlossen. Das war die Lösung für den gescheiterten Druck von v4.
- **Lampen:**
  - Je ein Scheinwerfer-Modul **Ø 18,8 × 14 mm** (von Daniel gemessen) in einem Halter aussen an den Armen: weiss an Arm 1, IR 850 nm an Arm 2.
  - An beiden Armen ist ein Kabelbügel.
- **Unterteil innen:**
  - Zaun für den Akkublock, darüber der Pi.
  - PCA9685 auf Domen an der Wand mit den Lüftungsschlitzen.
  - Lautsprecher-Ring über einem Bodengitter.
  - Stativmutter 1/4".
  - Ablage für den USB-Hub (höchstens 56 × 22 × 14 mm).
  - Zwischenboden als eigenes Teil, für Ladewandler, PAM8403 und INA219.
  - PIR-Hülse (Ø 12,4) und Mikrofon-Rippen in der Stirnwand.
- **Öffnungen aussen:**
  - HDMI-Notfallfenster mit Stopfen.
  - Lüftungsschlitze mit Regendach.
  - GX16-4P-Ladebuchse mit Dach.
  - Relais-Ausgang (Loch Ø 12,3 für eine Kabelverschraubung M12) mit Dach.
  - Loch Ø 6,5 im Boden für den Temperaturfühler DS18B20.
- **Kopf-Blende:** 18 mm lang. Nachgerechnet: Sie ragt bei keiner der beiden Kameras ins Bild.
- **Geprüft:**
  - Kollisionen beim Kippen 0/±40/±70° und Schwenken 0/90/135/180/225/270°: alles frei.
  - Alle Teile ohne schwebende Inseln. Es gibt nur kurze Brücken (Kabelkamin-Dach 24 mm, Hub-Ablage ca. 17 mm).

### Druckteile v5.1 (`Druckdateien_v5-1/`)

| Datei | Anzahl | Hinweis |
|---|---|---|
| 01_Unterteil | 1 | Boden auf dem Bett; grösster Druck |
| 02_Deckel_mit_Laufring | 1 | Rille fein drucken (0,12–0,16 mm) |
| 03_Drehteller | 1 | |
| 04_Gabel_mit_Arm1 | 1 | Brim 5 mm |
| 05_Arm2_Lagerseite | 1 | |
| 06_Kamerakopf | 1 | Brim 5 mm |
| 07_Seitendeckel | 1 | |
| 08_Lampenhalter | 2 | gleiches Teil für beide Seiten |
| 09_Zwischenboden | 1 | |
| 10_HDMI_Stopfen | 1 | |
| 11_Fuss | 4 | Zapfen einkleben |

Die beiden 3MF-Dateien haben die Teile schon auf den Platten verteilt. Platte A: Unterteil und Kleinteile. Platte B: Deckel und alles für den Kopf.

## Offene Punkte

1. **Masse des UPS HAT (E) mit Akkus nachmessen**, bevor das Unterteil gedruckt wird.
   - Angenommen sind 90 × 80 × 26 mm (`BAT_L/BAT_W/BAT_H`).
   - Die Pi-Unterseite liegt angenommen 37 mm über dem Boden (`PI_Z_ABOVE_FLOOR`).
   - Waveshare gibt keine Masse an, und die 3D-Datei war aus der alten Umgebung nicht erreichbar.
2. **HORN_TOP (13,5 mm) und die Höhe des MG90S-Getriebeturms** (höchstens 8,3 mm über den Laschen) sind noch nicht am echten Teil geprüft. Die Werte stehen in `pantilt.py`.
3. **Lautsprecher:** Das Unterteil ist für Ø 41 mm ausgelegt (Visaton SC 4.7 ND, 27 tief). Der 40-mm-Lautsprecher von Bastelgarage passt auch, wird geklebt.
4. **Bastelgarage ausverkauft:** Lautsprecher und MOSFET-Module (AOD4184). Diese bitte vormerken.
5. **Thermal-90:** Waveshare listet die SKU 31941 als ausgelaufen. Ob Daniel sie schon hat, steht in der Liste noch nicht.
6. **Pan über ±90°:** Die Software kann ab 2.95.4 einen 270°-Servo nutzen. Die Mechanik ist frei, aber die Kabelschlaufe muss dann länger sein (ca. 25 cm, Spiralschlauch).
7. **Repository-Dokumente veraltet:** `CLAUDE.md` und `docs/Uebergabe_Gehaeuse_Licht_Audio.md` nennen noch den UPS HAT mit 2 × 18650 und das Wetterhäuschen. `Dokumente/Uebergabe_Gehaeuse_v5.md` ersetzt sie.
8. **Mover (Kettenfahrzeug):** Die Software unterstützt ihn ab 2.94.0. Ins Gehäuse kommt er **vorerst nicht** (Wunsch Daniel).
9. **Antennen-Durchführungen:** vorerst weggelassen (Wunsch Daniel).

## Entscheidungen im Verlauf (Kurzfassung)

- **v1–v2:** Kastengehäuse.
- **v3:** Aufbau wie ein Waveshare-PTZ mit Drehteller auf Kugellager.
- **v4:** Tilt-Servo im Kopf, Kopf zwischen zwei Armen. Die Thermal-90 ist nach dem Produktfoto platziert (Linse 7,4 / 10,5 mm vom linken / oberen Rand).
- **v4.1:** Der Druck von v4 scheiterte, weil Dome im Kopf in der Luft begannen. Lösung: Kopf seitlich offen mit Seitendeckel, und die Gabelrippen gehen bis aufs Bett.
- **Konzept v5 (neue Hardware aus dem Software-Chat):**
  - Lautsprecher nach unten.
  - Strom ganz aus dem Akku.
  - PIR im Unterteil.
  - HDMI für Notfälle frei.
  - Kein Wetterhäuschen.
  - Laden bis 40 V ohne Verpolungsschutz.
  - UPS HAT (E) mit 4 × 21700.
  - Kopf in Grundstellung um 180° gedreht.
- **v5.0:** druckbares Modell daraus.
- **v5.1:** Ergänzungen aus dem Software-Stand 2.95:
  - USB-Hub.
  - Temperaturfühler.
  - Relais-Ausgang.
  - INA219.
  - Längere Blende.
  - Scheinwerfer Ø 18,8.
  - Zweiter Kabelbügel.
  - Umstellung auf Teile von Bastelgarage: GX16 statt GX12, PIR AS312 mit Linse 12,2.
  - Behobener Fehler: Der HDMI-Stopfen stiess ans Lüftungsdach.

## Strom und Anschlüsse (Kurzfassung, Details in `Dokumente/Uebergabe_Gehaeuse_v5.md`)

- **Laden:** GX16-4P, 12–40 V → Sicherung 5 A → Pololu D36V50F5 → USB-C des UPS HAT (E). Der HAT liefert 5 V / 6 A über Pogo-Pins an den Pi und hat die I2C-Adresse 0x2D.
- **Servos, Licht, Verstärker:** Step-Down vom Akku auf 5 V (Bastelgarage 424274 oder Pololu D36V28F5).
- **I2C-Adressen:**

  | Teil | Adresse |
  |---|---|
  | PCA9685 | 0x41 |
  | Thermal-90 | 0x40 |
  | UPS HAT (E) | 0x2D |
  | BME280 | 0x76 / 0x77 |
  | MPU-6050 | 0x68 |
  | INA219 | 0x44 |

- **Weitere Anschlüsse:**
  - DS18B20 an GPIO 4.
  - PIR an GPIO 5.
  - Relais an GPIO 22.
  - Licht an PCA9685 Kanal 2 (weiss) und 3 (IR), über MOSFET.

## Modell ändern und neu erzeugen (`Quellcode/`)

```
cd Quellcode
python3 v5.py                       # Kennmasse ausgeben
python3 export5.py                  # alle Teile -> out51/*.stl (+ .npz); einzelne: python3 export5.py 01 08
python3 plates5.py                  # 3MF-Platten für den X2D (230 x 249)
python3 printcheck5.py 1 4 8        # Schicht-Prüfung (schwebende Inseln, Überhänge)
python3 check5.py                   # Kollisionen über mehrere Kopf-Stellungen
python3 prev51.py                   # Vorschaubilder
```

- **Dateien:**
  - `v5.py`: Gehäuse v5.1, alle Parameter oben.
  - `pantilt.py`: Kopf, Gabel, Drehteller, Lager (aus v4.1).
  - `csg.py`: die CSG-Bibliothek.
  - `decimate.py`: Netz vereinfachen und reparieren.
  - `export.py`: STL- und 3MF-Ausgabe.
  - `concept_render.py`: Renderer.
- **Laufzeit:** Das Unterteil braucht beim Export ca. 20–25 Minuten, die Schicht-Prüfung ca. 35 Minuten (2 CPU-Kerne).
- **Parameter für die Masse oben:** `BAT_L/BAT_W/BAT_H`, `PI_Z_ABOVE_FLOOR`, `SPK_D`, `PIR_D`, `GX12_D` (heisst historisch so, ist jetzt GX16 mit 16,2), `HUB_*`, `LAMP_MOD_D/L`.

## Inhalt des Pakets

| Ordner | Inhalt |
|---|---|
| `Druckdateien_v5-1/` | 2 × 3MF (Platten) und alle STL-Dateien |
| `Dokumente/` | Montageanleitung v5.1, Übergabe für den Software-Chat, Materialliste mit Bestellliste (MD) und als HTML-Kopie, Montageanleitung v4.1 (Kopf-Montage im Detail) |
| `Bilder/` | Vorschau v5.1, Konzeptskizze v5f |
| `Quellcode/` | Python-Modell v5.1 (direkt lauffähig) |
