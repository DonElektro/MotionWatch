# MotionWatch Gehäuse v5.2: was gegenüber v5.1 neu ist

> **Stand im Repository (01.11.2026, Zweig real-gehaeuse-v52):** echtes Unterteil **01_Unterteil_v52** aus `Quellcode/v52.py`
> mit diesen Änderungen gegenüber dem Paket vom 30.10.2026 (weiter unten beschrieben):
>
> **Runde v5.2b (01.11.2026):**
>
> - **Service-Fenster** (HDMI + USB-C des Pi) hinten links in der Lüftungswand, ein Stopfen (10 v5.2, Spiel 0,2).
> - **SD-Karte:** microSD-Verlängerung (15 cm, Halter-Platine ca. 22 × 15 mm, Löcher M2,5 im Abstand 18 mm) in den Pi stecken, den Einbau-Kartenhalter mit 2 × M2,5 × 6 an die zwei
>   Dome über dem PCA9685 schrauben; Schlitz aussen mit Stopfen 16. Masse des Halters nachmessen (`SD_*`).
> - **Kopf 06 v5.2** mit Loch und Sockel für die RGB-LED, Diffusor 14 (PETG natur/weiss), Pupillenring 15 (PETG schwarz).
> - **Lampentreiber:** Feld an der Stirnwand innen unter dem Step-down (30 × 20, 2 Dome M2,5 – Platzhalter, Löcher nach dem Kauf
>   anpassen). **Sicherung B+ 5 A:** Inline-Halter in die Klammer am Boden (x 28–58) drücken.
> - **Reserve-Öffnung** hinten zwischen den Tasten (GX12, Ø 12,3, Nut oben, Regendach), sonst Blindstopfen 17 einstecken.
> - **Entwicklungs-Sockel 13** statt UPS HAT + Akkus: in den Akku-Zaun drücken (Klemmrippen), Pi mit 4 × M2,5 × 6 darauf.
>   Strom: Pi über sein USB-C-Netzteil (Service-Fenster); Servos/Lampen: **nur 12 V** (Netzteil `psu12`, mind. 3 A) an
>   die GX16-Buchse, über die 5-A-Sicherung auf den Step-down. Akku-%, INA219 und Lade-LED zeigen dann nichts.
> - Alle Druckdateien v5.2 (Platten A, B und jedes Teil einzeln): `Druckdateien/v5-2/`.

> - **Breite IR-LED = Modul 850 nm mit 120°-Linse** (statt 5-mm-LED): Hülse innen an der Stirnwand (y 20, z 49), Modul von innen
>   einschieben, liegt vorne am Lochrand (Ø 17) an, Madenschraube M3 oben oder Heisskleber. Aussen 45°-Fase für den Lichtkegel.
>   Die 5-mm-LED geht weiter mit `IR_TYP = "5mm"` in `v52.py` (dann auch Stopfen 13).
> - **Trennsteg** aussen zwischen IR-Loch und Kamera-Fenster (1,4 mm dick, 2 mm tief; Sichtfeld-Reserve 6 %); in der Wand bleiben 3,2 mm Steg.
> - **Kabelkamm** an der Lüftungswand (x 121–128,5, vor den Lüftungsschlitzen): Schlitz 1 = **CAM1** (Weitwinkel), Schlitz 2 =
>   **CAM0** (Kopfkamera). Kabel von oben einlegen, der Deckel hält sie. Weg CAM1: Stecker unten an der Kamera → über den PIR →
>   unter dem Pan-Servo → über den Pi zur Lüftungswand → Kamm → CAM/DISP 1. CAM0: Kabelkamin → vor dem Lüfter entlang → Kamm.
>   Der Lüfter bleibt frei (Kabel 8 mm über bzw. neben der Ansaugung).
> - **Druck:** `Druckdateien/v5-2/MotionWatch_v5-2_Platte_A_Unterteil.3mf` = Unterteil v5.2, Zwischenboden, HDMI-Stopfen,
>   4 Füsse, Blindstopfen Weitwinkel (12). **Platte B bleibt v5.1** (Kopf mit Status-LED 06/14/15 ist hier noch nicht erzeugt).
> - **Nachmessen vor dem Druck:** IR-Modul (Ø 18,8, Länge 14, Linse Ø 17), Linsenhöhe der CM3 Wide (11,4) und Linsenmitte
>   (9,5 unter der Oberkante), Lage der CAM-Buchsen am Pi 5 (Kamm), UPS HAT (E) mit Akkus. Parameter mit «NACHMESSEN» in `v52.py`.
> - **Prüfung:** `check52.py` (Kollisionen fest, Sichtfeld, Stegbreiten, Abstände). Nicht gedruckt, nicht mit echten Teilen probiert.

Diese Anleitung beschreibt **nur die Änderungen**. Alles andere (Druck, Montage, Masse zum Nachmessen) steht weiter in `LIESMICH_Montage_v5-1.md`.

Neu in v5.2:

1. Weitwinkel-Kamera vorne im Unterteil
2. Loch für eine breite IR-LED daneben
3. Status-LED (RGB) oben auf dem Kopf, mit Diffusor «Blinki-Auge»
4. Zwei Tasten hinten
5. Zwei Blindstopfen für Geräte ohne Weitwinkel-Kamera

Geändert haben sich nur **01_Unterteil** und **06_Kamerakopf**. Neu sind die Kleinteile **12 bis 15**. Alle anderen Teile aus v5.1 bleiben gültig.

## 1. Weitwinkel-Kamera (Camera Module 3 Wide)

- **Ort:** Stirnwand (PIR-Seite), mittig über dem PIR. Die Kamera ist fest eingebaut und dreht nicht mit.
- **Neigung:** 12° nach unten.
- **Linse:** Mitte 56 mm über der Unterseite des Bodens. Die Linse sitzt 0,5 mm hinter der Wand-Innenseite und ragt also nicht in die Wand.
- **Halter:** zwei Rippen an der Wand-Innenseite, mit schräger Unterseite (ohne Stützen druckbar).
  - Je ein Kernloch Ø 1,7 mm pro Kamera-Loch.
  - Befestigung mit **4 × M2 × 6**, selbstschneidend für Kunststoff (oder normale M2-Schrauben vorsichtig eindrehen).
  - Die Platine liegt nur auf 4 Polstern (Ø 5, 1 mm hoch) auf.
- **Fenster:** aus dem Sichtfeld berechnet, damit die Wand nichts vom Bild abschneidet (120° diagonal, 102° × 67°).
  - Form: Trapez, aussen unten ca. 26 mm breit, oben ca. 15 mm, Höhe ca. 16 mm. Die Decke ist flach und wird als kurze Brücke gedruckt.
  - Darüber sitzt ein kleines **Regendach**: 5 mm tief, 30 mm breit, mit 45° Unterseite.
  - Geprüft mit Sichtstrahlen: Nichts ragt ins Bild, weder Gehäuse noch Kopf, Arme oder Lampen, in allen geprüften Kopf-Stellungen.
  - Reserve: Das Bild dürfte noch ca. 10 % grösser sein, bevor der Fensterrand stört.
- **Kabel:** Pi-5-Kamerakabel 22 → 15 polig an **CAM1**.
  - Der Stecker sitzt unten auf der Rückseite der Kamera. Das Kabel über den PIR nach hinten zum Pi führen.
  - Empfohlene Länge **200 mm**. Der Weg ist ca. 90–150 mm, je nachdem, wo der Anschluss liegt (geschätzt, nicht verlegt).
- **Wenn die Linse nicht passt:** Die Linsenhöhe ist geschätzt (11,4 mm ab Platine).
  - Ist die Linse **kürzer**: Unterlegscheiben M2 zwischen Platine und Polster legen. Das Fenster hat 1 mm Reserve.
  - Ist sie **länger**: die Polster etwas abschleifen.

## 2. Breite IR-LED (5 mm, 850 nm)

- **Ort:** Stirnwand, links vom PIR, aussen gesehen rechts (y 26, z 40). Loch Ø 5,2 mm.
- **Hülse:** Innen sitzt eine Hülse (Ø 9, bis 5,1 mm tief). Die LED wird von innen eingeschoben, bis der Kragen an der Hülse anliegt. Die Spitze ist dann bündig mit der Aussenwand.
  - Mit einem Tropfen Heisskleber oder Silikon von innen sichern.
- **Ansteuerung:** PCA9685 **Kanal 4** über einen dritten MOSFET-Kanal, wie das IR-Licht am Kopf.
  - Vorwiderstand bei 5 V: ca. **68 Ω / 0,25 W** (ca. 50 mA). Das ist geschätzt, bitte mit dem Datenblatt der LED prüfen.
- **Abstand:** Die LED liegt 20 mm neben und 16 mm unter dem Kamera-Fenster und ist durch die Wand getrennt. Sie blendet also nicht ins Fenster.

## 3. MOSFET-Modul an neuem Platz

Vorne ist der alte Platz jetzt von der Weitwinkel-Kamera belegt.

- **Neuer Platz:** Das MOSFET-Modul klebt an der **Wand mit den Lüftungsschlitzen, unten unter dem PCA9685**.
  - Bereich ca. 28 × 20 mm, 10–38 mm ab der Stirnwand, 3–23 mm über dem Boden.
  - Vorteil: kurze Kabel zum PCA9685.
- Der Spannungswandler D36V28F5 bleibt vorne links vom PIR, unter der IR-LED.

## 4. Status-LED auf dem Kopf

- **Ort:** Kopfdach, 3 mm vor der Kippachse, 8 mm zur Servo-Seite hin (Seite Arm 1).
  - Sie liegt zwischen den Seitendeckel-Schrauben und weit weg von der Hauptkamera.
- **Loch und Sockel:** Loch Ø 5,2 mm. Darum herum eine Vertiefung **Ø 14,4 × 1,2 mm** als Sockel für den Diffusor.
- **LED einbauen:** Die 5-mm-RGB-LED von innen einschieben, der Kragen liegt innen am Dach. Mit Heisskleber sichern.
- **Diffusor «Blinki-Auge»** (Teil 14, PETG natur oder weiss):
  - Runde Kuppel Ø 14, 7,5 mm hoch über dem Dach.
  - Wird mit 6 kleinen Rippen in die Vertiefung gedrückt, bei Bedarf mit einem Tupfen Silikon.
  - Oben hinein kommt der **Pupillenring** (Teil 15, PETG schwarz, Ø 6 / Ø 2,6). Er steht 0,3 mm vor, die Mitte leuchtet.
  - Gesamthöhe 7,8 mm.
- **Geprüft:** Kippen bis ±70° und alle Schwenk-Stellungen ohne Berührung.
- **Kabel:** 4 Adern innen nach hinten zum Kabelschlitz unten in der Rückwand, dann mit dem Bündel durch den Kabelkamin.
  - Das Kabel zählt zur Kabelschlaufe bzw. zur Drehgrenze.
- **Ansteuerung:** PCA9685 **Kanäle 5 / 6 / 7** (rot / grün / blau).
  - **Gemeinsame Kathode (empfohlen):** Kathode an GND, Ausgänge nicht invertiert.
  - Das Adafruit-PCA9685-Board hat schon 220 Ω vor jedem Ausgang und arbeitet mit 3,3 V. Darum keine weiteren Widerstände.
  - Strom: rot ca. 6 mA, grün und blau nur ca. 1–2 mA. Das reicht für eine Statusanzeige, bei direkter Sonne ist es aber schwach.
  - **Gemeinsame Anode** geht auch: Anode an 3,3 V, Ausgänge in der Software **invertieren**, gleiche Helligkeit.
    - Die Anode **nicht an 5 V** anschliessen: Die Servo-Ausgänge brauchen den Gegentakt-Modus, und dann glimmt Rot, wenn die LED aus sein sollte.
  - Diese Werte sind gerechnet, nicht gemessen. Für den Software-Chat: R/G/B = Kanal 5/6/7, Anode oder Kathode wie gewählt.

## 5. Zwei Tasten hinten

- **Ort:** Rückwand (Ladebuchsen-Seite), 33 mm über dem Boden. Zwischen Relais-Buchse und Pi, unterhalb der Pi-USB-Buchsen.
  - **Taste 1 (y 10,5):** neben der Relais-Verschraubung, aussen gesehen links.
  - **Taste 2 (y 50,5):** zwischen Relais-Dach und GX16-Dach.
- **Loch Ø 12,2 mm** für 12-mm-Einbautaster IP67. Die Mutter kommt innen hin.
- **Schutz:** Jede Taste hat ein **Dach mit Seitenwangen**, 7 mm tief. Die Kappe liegt ca. 4 mm zurück, das verhindert versehentliches Drücken. Unten ist es offen, damit Wasser abläuft.
  - Innere Breite: Taste 1 15 mm, Taste 2 17 mm.
- **Einbautiefe innen:** **12 mm** sind geprüft und frei. Bis zum Akkupaket (Zaun bei x 163) sind es ca. 15 mm, bis zu den Pi-USB-Buchsen ca. 17 mm.
  - Die Mutter darf höchstens Ø 17 mm haben.
- **Anschluss:** je eine Taste zwischen einem freien GPIO und GND, mit internem Pull-up. Welche GPIO, legt der Software-Chat fest.
  - Belegt sind schon: GPIO 4 (DS18B20), 5 (PIR) und 22 (Relais).
  - «Schutz» = Taste 1, «Alarm quittieren» = Taste 2 (Vorschlag).

## 6. Blindstopfen (Geräte ohne Weitwinkel-Kamera)

- **12_Blindstopfen_Weitwinkel:**
  - Von aussen ins Fenster drücken, bis die zwei Rastnasen oben und unten hinter der Wand einrasten.
  - Der Flansch deckt das Fenster ganz ab und liegt unter dem Regendach.
  - Zum Lösen den Fingernagel unter den Flansch-Rand (Stufe) schieben und abziehen. Die Rastflächen sind 45° schräg, darum geht das ohne Werkzeug.
- **13_Stopfen_IR_LED:** Geschlitzter Zapfen mit Rastnasen. Er rastet hinter dem Ende der LED-Hülse ein. Flansch Ø 9.
- **Spiel:** 0,2 mm pro Seite für PETG. Wenn es zu stramm oder zu locker ist, `BLIND_TOL` oder `BLIND_NOSE` in `v52.py` ändern und `python3 kleinteile52.py 12 13` laufen lassen.

## Druckteile v5.2 (Bambu Lab X2D, PETG, alle ohne Stützen)

| Datei | Anzahl | Platte | Hinweis |
|---|---|---|---|
| 01_Unterteil | 1 | A | **geändert**: Weitwinkel-Halter, Fenster, Regendach, IR-Hülse, Tastenlöcher mit Dächern |
| 06_Kamerakopf | 1 | B | **geändert**: Loch und Sockel für die Status-LED |
| 12_Blindstopfen_Weitwinkel | 1 | A | **neu**, liegt auf dem Flansch, nur ohne Weitwinkel-Kamera nötig |
| 13_Stopfen_IR_LED | 1 | A | **neu**, liegt auf dem Flansch, nur ohne IR-LED nötig |
| 14_Diffusor_Status_LED | 1 | B | **neu**, PETG natur oder weiss (durchscheinend) |
| 15_Pupillenring | 1 | B | **neu**, PETG schwarz |
| alle anderen | | | wie v5.1 |

**Platten:**
- **Platte A:** Unterteil, Zwischenboden, HDMI-Stopfen, 4 Füsse und die beiden Blindstopfen.
- **Platte B:** Deckel, Drehteller, Gabel, Arm 2, Kopf, Seitendeckel, 2 Lampenhalter, Diffusor und Pupillenring.

In Bambu Studio dem Diffusor das helle und dem Pupillenring das schwarze Filament zuweisen. Oder die beiden separat drucken.

**Kleinteile fein drucken:** Schichthöhe 0,12 mm, Rastnasen und Rippen sind klein.

## Neue Teile zum Bestellen

| Teil | Anzahl | Hinweis |
|---|---|---|
| Raspberry Pi **Camera Module 3 Wide** (NoIR Wide empfohlen, für Nacht mit IR) | 1 | Platine 25 × 24 mm, Löcher 21 × 12,5 mm (M2) |
| Pi-5-Kamerakabel **22 → 15 polig, 200 mm** | 1 | für CAM1; 300 mm nur, wenn 200 nicht reicht |
| IR-LED **5 mm, 850 nm**, möglichst breiter Winkel (ca. 120°) | 1 | plus Vorwiderstand ca. 68 Ω / 0,25 W |
| MOSFET-Modul (wie bei den Scheinwerfern) | 1 | für PCA-Kanal 4 (breite IR-LED), falls das vorhandene Modul keinen dritten Kanal hat |
| RGB-LED **5 mm, diffus**, gemeinsame **Kathode** (empfohlen) oder Anode | 1 | siehe Abschnitt 4 |
| Einbautaster **12 mm IP67**, Schliesser (tastend) | 2 | Loch 12 mm, Frontring höchstens Ø 14, Einbautiefe höchstens 12 mm, Mutter höchstens Ø 17 |
| Schrauben **M2 × 6** (selbstschneidend für Kunststoff) | 4 | Weitwinkel-Kamera |
| Litze 4-adrig, dünn (ca. 0,14 mm²), ca. 40 cm | 1 | Status-LED, durch die Kabelschlaufe |

## Was noch nicht geprüft ist

- **Weitwinkel-Kamera:**
  - Die Linsenhöhe (11,4 mm) und der Durchmesser der Frontlinse (Ø 6) sind **geschätzt**, nicht gemessen.
  - Das Fenster hat Reserve: Die Linse darf 1 mm kürzer sein, und das Bild dürfte ca. 10 % grösser sein.
  - Das Sichtfeld ist mit einem Fischauge-Modell gerechnet (Ecke ca. 120°) und noch nicht mit einem echten Bild geprüft.
- **Tasten:** Frontring Ø 14 und Einbautiefe 12 mm sind angenommen. Bitte vor dem Druck die gekauften Taster nachmessen.
- **Kamerakabel:** Weg und Länge sind geschätzt und nicht verlegt.
- **Status-LED:** Ströme und Helligkeit sind gerechnet, nicht gemessen. Die Haltekraft der Presssitze von Diffusor und Stopfen ist nicht getestet: zuerst die kleinen Teile drucken und probieren.
- **Ungeprüft wie in v5.1:** Akkumasse, PI_Z_ABOVE_FLOOR, HORN_TOP und MG90S (siehe v5.1).

## Quellcode v5.2 (`Quellcode_parametrisch_v5-2.zip`)

- `v52.py`: alle Ergänzungen. Die Parameter stehen oben. `v5.py` ist unverändert und wird importiert.
- `export52.py`: geänderte und neue Teile exportieren, z. B. `python3 export52.py 01 06`. Das Unterteil braucht ca. 30 Minuten.
- `kleinteile52.py`: nur die Teile 12–15 erzeugen (Stopfen, Diffusor, Pupillenring).
- `plates52.py`: die beiden 3MF-Platten.
- `printcheck52.py 1 6 C D E F`: Schicht-Prüfung.
- `check52.py`: Kollisionen und Sichtfeld-Test der Weitwinkel-Kamera.
- `prev52.py`: Vorschaubilder.
