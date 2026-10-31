# Gehäuse Variante 2: mit zweiter Weitwinkel-Kamera (Entscheidungen Daniel, 29.10.2026)

Grundlage: Modell v4 (`docs/Projektstand_PanTilt_Kamera.md`) bzw. die neuere Version, die Daniel hochlädt. Variante 1 bleibt unverändert.

| Thema | Entscheidung |
|---|---|
| Kamera | **Camera Module 3 Wide NoIR** (Platine 25 × 24 mm, Löcher 21 × 12,5 mm wie Camera Module 3), ca. 102° horizontal |
| Ort | **Front des Unterteils**, fest (dreht nicht mit), mittig unter dem Kopf, leicht nach unten geneigt (ca. 10–15°), möglichst nah an der Pan-Achse |
| Anschluss | Pi 5 **CAM1** (zweiter Kamera-Anschluss), Pi-5-Kamerakabel 22→15-polig; in der Software «Raspberry Pi camera 1», Rolle «Übersicht lenkt den Kopf» |
| Breites IR-Licht | zweite **IR-LED 850 nm mit 120°-Linse**, fest an der Front neben der Weitwinkel-Kamera (blendet nicht ins eigene Fenster); **PCA9685 Kanal 4** (MOSFET wie Kanal 3) |
| Kabel | Halter / Führung für **zwei Flachkabel** im Unterteil, Lüfter und Lüftungsschlitze frei |
| Grösse | Das **Unterteil darf grösser werden**, wenn es eng wird |
| Fenster | offen (kein Schutzfenster gewählt) |

Offen: Masse der 120°-Linse / des Halters nachmessen; Lage gegenüber der Lüftung und dem Lautsprecher prüfen; Neigung als Parameter.

## Simulator-Einbindung der Weitwinkel-Kamera (Entscheide Daniel, 30.10.2026 09:35)

Ziel: die Montage-Varianten im Simulator vergleichen, bevor gedruckt wird.

| Thema | Entscheid |
|---|---|
| Kamera im Simulator | Die heutige «Feste Kamera» (Simulator-Kamera 1, Mast 3 m neben dem Gerät) wird **zur Weitwinkel-Kamera zusammengelegt**: eine Kamera mit Montage-Wahl, 102° × 67°, NoIR-Look, ca. 640×360 / 8 Bilder/s, nur gerechnet wenn abgerufen |
| Montage-Wahl | **Mast (Szene)** wie bisher · **Unterteil vorne, fest** (10–15° nach unten) · **Kopf vorne** · **Kopf hinten** (dreht mit, Versatz 180°); auf dem Kopf wählbar: **nur mitschwenken oder auch mitneigen**; Neigung als Regler |
| Schnittstelle | `/info` → `cameras[1]` meldet `mount` (`scene`/`base`/`head_front`/`head_rear`), `tilt_deg`, `yaw_offset`, `pan_follow`, `tilt_follow`, `fov_h`/`fov_v`; MoveEye stellt daraus «Übersicht lenkt den Kopf» (162) selbst ein |
| Automatik (162) | Kamera auf dem Kopf: Richtung = Kopfstellung + Versatz (statt fest); Bewegung im Weitwinkel-Bild **unterdrücken, solange der Kopf dreht** (Eigenbewegung); hinten montiert: Bewegung hinten → **Kopf dreht hin** (Rang wie «Zum Alarm drehen»), dann prüft die KI der Hauptkamera |
| IR-Licht | zweite IR-LED 120° auf **PCA9685 Kanal 4**, im Simulator als breites IR-Licht an der Montagestelle, schaltbar wie die Hardware |
| Kabel / Servo-Last | Kamera auf dem Kopf: **Drehgrenze** (zweites Flachkabel, wichtig für spätere 360°-Servos → Schleifring nötig) und **trägerer Kopf** (Mehrlast MG90S) |
| Verzerrung | leichtes **Fischauge** am Bildrand (Shader), abschaltbar |
| Prüfstand | neue Messung «Übersicht → Kopf findet Ziel» (Zeit bis die Hauptkamera das Ziel sieht) **pro Montage-Variante** |
| Seiten / Spiel | Weitwinkel-Bild als Kachel auf /sim und in Sim-Kompakt; im Spiel als zweite Wächter-Sicht (gleiche Regeln für den KI-Wächter) |

Umsetzung: nach dem Zusammenführen von Sim-Kompakt und Spiel-Balance (gleiche Dateien), als eigene Runde.

### Umgesetzt (Zweig wt-weit, 30.10.2026 – Simulator-Entwurf 3D-4.17, MoveEye auf 2.98.45)

| Thema | Stand |
|---|---|
| Kamera / Montage | **umgesetzt** – `simulator3d/scripts/weitwinkel.gd`: cams[1] = Weitwinkel 102° × 67°, 640×360 / 8 Bilder/s (wie bisher nur gerechnet, wenn abgerufen), NoIR-Look, nachts eigenes IR-Bild; Montage Mast (Standard, alte Einstellungen bleiben) · Unterteil vorne (−12°, Regler) · Kopf vorne · Kopf hinten (180°); auf dem Kopf «auch mitneigen» wählbar. Einstellungen: Kamerabild → «Weitwinkel-Kamera» (die alte «Kamera 1: Richtung» heisst jetzt «Weitwinkel am Mast: Richtung») |
| Schnittstelle | **umgesetzt** – `/info` cameras[1]: name «Wide camera (NoIR Wide)», `mount`, `tilt_deg`, `yaw_offset`, `pan_follow`, `tilt_follow`, `fov_h`/`fov_v`, `on_head` (+ `fisheye`, `pan_limit`, `ir_wide`); jede Antwort auf POST /state hat `wide` (Wechsel sofort bei MoveEye) |
| Automatik (162) | **umgesetzt** – Teil `163_weitwinkel.py`: am Gerät stellt MoveEye `kopf_ov = sim:1` selbst ein (nur beim Montage-Wechsel – von Hand Gewähltes bleibt; Mast = nicht von selbst, war es automatisch, wird es wieder gelöscht); Kopf-Montage: Richtung = echte Kopfstellung + Versatz + Winkel im Bild; solange der Kopf dreht (+1,2 s im Simulator, 0,8 s echt) zählt Bewegung der Kopf-Kamera nicht (440, gleiche Signale wie die Hauptkamera); hinten: Kopf dreht hin (Rang «Zum Alarm drehen»), dann prüft die KI |
| IR-Licht | **umgesetzt** – Schalter «IR-Licht breit (Kanal 4)» (Licht, Web und Fenster): zweite IR-LED auf PCA9685 Kanal 4, ein / aus mit dem Infrarotlicht (nicht, wenn Kanal 4 schon belegt ist); Simulator: breites IR-Licht 120° an der Montagestelle (`lights.ir_wide`) |
| Kabel / Servo-Last | **umgesetzt im Simulator** – Kopf-Montage: Drehgrenze ± 170° (Regler, Hinweis Schleifring für 360°-Servos), Kopf 15 % träger mit «Servos wie echt». MoveEye selbst hat dafür keine eigene Grenze (die bestehende `pan_limit` gilt) |
| Verzerrung | **umgesetzt** – Fischauge (camfx `distort` 0,16) als Schalter «Weitwinkel: leichtes Fischauge», Standard ein |
| Prüfstand | **umgesetzt** – `--weitwinkel base,head_front,head_rear` (pruefstand/LIESMICH.md). Erster lokaler Lauf (langsamer 2-Kern-Rechner, fremde Last ~100 %, Weitwinkel-Bild < 1 Bild/s – Zahlen nur grob): Unterteil 2/3 gefunden (3,5 / 21,9 s), Kopf vorne 2/3 (2,4 / 3,8 s), Kopf hinten 3/3 (Median 4,3 s) |
| Seiten / Spiel | **Seiten umgesetzt** – Kachel 🔭 «Weitwinkel-Kamera» in der Simulator-Zentrale (/sim) und in Sim-Kompakt: Bild (über die vorhandene Zusatzkamera, /cam_feed – kein neuer Strom vom Simulator), antippen = gross, Montage-Knöpfe. **Spiel:** die zweite Wächter-Sicht nutzt cams[1] weiter (jetzt mit der gewählten Montage); Texte «feste Kamera» im Spiel nicht angepasst (Spiel-Dateien gehören der Runde «balance») |


## Status-LED oben auf dem Kopf (Wunsch Daniel, 30.10.2026 21:49)

Aussparung oben auf dem Kopf für eine **Farb-LED** (RGB), die den Schutzzustand zeigt (grün / orange / rot, Zuordnung zu
Aus / Wachsam / Voll noch festlegen). Lichtleiter/Diffusor einplanen, Kabel durch die Pan-Achse (zählt zur Drehgrenze /
Schleifring wie das zweite Flachkabel). Ansteuerung offen (WS2812 an GPIO oder RGB an 3 PCA9685-Kanälen).

Entscheide 30.10.2026 21:55: **RGB-LED an PCA9685 Kanälen 5/6/7** (gemeinsame Anode/Kathode noch wählen), Farben pro Zustand
einstellbar; Diffusor **in der Form von Blinkis Auge**. Dazu **zwei Tasten am Gerät**: «Schutz» (kurz Wachsam ↔ Aus, lang Voll)
und «Alarm quittieren» – Platz und Kabel (GPIO 16 / Pin 36 und GPIO 26 / Pin 37, je gegen Masse) im Gehäuse vorsehen.

### Software umgesetzt (Zweig wt-led, 30.10.2026 – MoveEye-Teile 163a / 599c / 639f, Simulator `statusled.gd`)

| Thema | Stand |
|---|---|
| LED-Ausgang | **umgesetzt** – RGB an PCA9685 der Servos, Kanäle 5 / 6 / 7 (einstellbar), gemeinsame Kathode oder Anode (Einstellung «LED-Typ»), Helligkeit per PWM mit Gamma 2,2; geschrieben nur bei Änderung (I2C teilt sich mit den Servos); Kanal belegt (Servo, Licht, IR breit) = Hinweis statt Ausgabe. **Nicht mit echter Hardware getestet** (nur mit nachgebautem PCA9685 im Selbsttest) |
| Farben / Vorrang | **umgesetzt** – Aus grün, Wachsam orange, Voll rot (einstellbar: grün, orange, rot, gelb, blau, türkis, violett, weiss, aus); Countdown = Farbe «atmet». Vorrang: LED-Test > Alarm (rot blinkend bis quittiert; Schutz aus quittiert auch) > Störung (violett pulsierend: Akku schwach, Unterspannung, Kamera weg, Servo-Störung) > Erkennung (kurz weiss, Standard aus) > Zustand > Blinki-Zwinkern |
| Nacht | **umgesetzt** – dunkel (im Simulator dessen Nacht): gedimmt (Standard 8 %), aus oder wie am Tag; Alarm bleibt hell; kein Zwinkern nachts |
| Blinki-Zwinkern | **umgesetzt** – alle 5 Minuten (einstellbar) kurz zweimal dunkel = «alles ok» (nicht nach einer Störung); Blinki (Mini-Figur mit LED-farbiger Iris) in der Kopfzeile der Webseite zwinkert im selben Moment |
| Tasten | **umgesetzt** – GPIO 16 «Schutz» (Pin 36), GPIO 26 «Alarm quittieren» (Pin 37) – einstellbar; GPIO 5 ist der PIR (Gehäuse-Übergabe). Interner Pull-up, Taste gegen Masse, Entprellen 50 ms, lang = 1,5 s (feuert beim Halten). Schutz kurz Wachsam ↔ Aus, lang Voll; Quittieren stoppt Sirene + Eskalation + rotes Blinken (dasselbe wie «Alarm quittieren» im Alarmfenster). Jeder Druck im Protokoll. **Ab 2.98.50 (Daniel): die Tasten dürfen alles**, auch mit PIN zum Ausschalten; einzeln abschaltbar: «Taste darf Schutz einschalten / ausschalten / Sirene stoppen / Alarm quittieren»; jedes Ausschalten und Sirene-Stoppen am Gerät steht im Protokoll und kommt als Push («Schutz am Gerät ausgeschaltet» / «Sirene am Gerät gestoppt», Schalter «Meldung bei Ausschalten am Gerät»). Standard «Tasten am Gerät» aus, bis sie verdrahtet sind. **Nicht mit echtem GPIO getestet** |
| Simulator | **umgesetzt** – LED als leuchtende Kuppel in Blinkis Augen-Ring oben auf dem Kopf (state `led`), Fenster «Gerät» unten rechts mit LED-Punkt, Statuszeile und den Knöpfen «Schutz» / «Alarm quittieren» (world_reply `buttons`, wie ein GPIO: gedrückt / Dauer / Zähler); MoveEye nimmt dann diese statt GPIO / PCA (🧪). Einstellung im Simulator: Licht & Ton → «Status-LED & Tasten» (ab 3D-4.21) |
| Seiten | **umgesetzt** – Einstellungen → Licht & Ton → «Status-LED & Tasten» (Web und Fenster), Statuszeile «LED: Wachsam (orange)», «LED testen», «Alarm quittieren», letzte Tastendrucke; Anleitung DE / EN; Sprachen DE / FR / IT / RM / EN |

## Blindabdeckung für die Weitwinkel-Öffnung (Wunsch Daniel, 30.10.2026 22:05)

Solange die Weitwinkel-Kamera nicht eingebaut ist: **einrastender Stopfen** (kleine Rastnasen, ohne Werkzeug lösbar) für die
Kamera-Öffnung und ein zweiter kleiner Stopfen für das Loch der breiten IR-LED. Lieferung: **STL + parametrisches Python-Skript**.
Wartet auf Daniels Gehäuse-Modell (Upload), damit die Masse der Öffnung stimmen.

## Umgesetzt in v5.2 (Gehäuse-Modell, 30.10.2026)

Grundlage: Gehäuse v5.1 (parametrisches Python-Modell). Unverändert bleiben alle Teile ausser **01_Unterteil** und **06_Kamerakopf**. Neu sind die Kleinteile 12–15. Details: `LIESMICH_Montage_v5-2.md` im Gehäuse-Paket v5.2.

| Thema | Umsetzung v5.2 |
|---|---|
| Weitwinkel-Kamera | CM3 Wide an der Stirnwand (PIR-Seite), mittig über dem PIR, Linse z 56 mm, **12° nach unten** (Parameter `WC_TILT`). 4 M2-Halter auf zwei Rippen mit 45°-Unterseite. Fenster aus dem Sichtfeld berechnet (Trapez ca. 26/15 × 16 mm, 120° diagonal frei, ca. 10 % Reserve), kleines Regendach. Sichtstrahlen-Test: frei bei allen Kopf-Stellungen |
| Kabel | Pi-5-Kabel 22 → 15 polig, 200 mm, an **CAM1** (Länge geschätzt) |
| Breite IR-LED | 5-mm-LED 850 nm, Loch Ø 5,2 links vom PIR (y 26, z 40), Spitze bündig, **PCA9685 Kanal 4** über MOSFET. Statt eines Moduls mit 120°-Linse vorerst eine 5-mm-LED (Masse der Linse waren offen) |
| MOSFET-Modul | neuer Platz unten an der Lüftungswand unter dem PCA9685 (vorne war es der Kamera im Weg) |
| Status-LED | 5-mm-RGB-LED auf dem Kopfdach (Kipp-Koordinaten x +3, y +8), Sockel Ø 14,4 für Diffusor **«Blinki-Auge»** (Kuppel Ø 14 + schwarzer Pupillenring, 7,8 mm hoch). Kippen ±70° frei. **Kanäle 5/6/7**, Empfehlung **gemeinsame Kathode** (Adafruit-Board hat 220 Ω, 3,3 V) |
| Tasten | 2 × 12-mm-Taster IP67 an der **Rückwand** (y 10,5 und 50,5, z 33), mit Dach und Seitenwangen gegen versehentliches Drücken; 12 mm Einbautiefe geprüft. GPIO noch festlegen (frei: nicht 4, 5, 22) |
| Blindabdeckung | **12_Blindstopfen_Weitwinkel** (2 Rastzungen, 45°-Rastfläche, ohne Werkzeug lösbar) und **13_Stopfen_IR_LED** (geschlitzter Rastzapfen); STL + Generator `kleinteile52.py` (Parameter `BLIND_TOL` 0,2 mm, `BLIND_NOSE`) |
| Offen | Linsenhöhe / Frontlinse der CM3 Wide, Taster-Masse und Kabelweg nachmessen; Helligkeit der RGB-LED am echten Board prüfen |

## Simulator wie Gehäuse v5.2 (Paket P9 «Weitwinkel-Kamera wie Gehäuse v5.2», 31.10.2026)

| Thema | Stand |
|---|---|
| Montage | neue Montage **«Im Gehäuse (v5.2)»** (`case`), Standard für neue Einrichtungen (gespeicherte Montagen bleiben): Stirnwand über dem PIR (Pan-0-Seite), fest, Linse 39,5 mm vor der Pan-Achse und 69,8 mm unter der Kippachse (Linse z 56 mm, Kippachse z 125,8 mm über der Bodenunterseite, aus `v52.py` / `v5.py` / `pantilt.py`), **12° nach unten** (fest, der Neigungs-Regler gilt hier nicht). Die anderen Montagen bleiben |
| Kamera-Typ | **NoIR Wide** – so steht es oben in diesem Dokument und in `LIESMICH_Montage_v5-2.md` («NoIR Wide empfohlen, für Nacht mit IR»); MoveEye-Teil 163 nennt sie ebenfalls «Camera Module 3 Wide NoIR». Simulator: NoIR-Look am Tag (rosa), nachts Graubild mit IR |
| Objektiv | **äquidistantes Fischauge** wie im Gehäuse-Prüfprotokoll (`check52.py fov_rays`): Winkel wächst linear mit dem Abstand von der Bildmitte, 51° bis zum Seitenrand, 33,5° bis oben/unten, Ecke ca. 61° (≈ 122° diagonal). Gerechnet als breiteres gerades Bild (121,8°, 1,5-fach überabgetastet, in Lite 1-fach), `camfx.gdshader` biegt es. Für MoveEye praktisch: `(cx − 0,5) × 102°` ist bei diesem Modell genau der Winkel |
| Vignettierung | dunklere Ecken (−22 % in der Ecke; Schätzung: ISP gleicht die Helligkeit nur zur Hälfte aus, `luminance_strength` 0,5 in den libcamera-Tuning-Dateien) |
| Fenster / Regendach | **nicht sichtbar**: laut Prüfprotokoll v5.2 frei bis 110 % des Sichtfelds (erst bei 114 % stossen 2 Strahlen ans Unterteil) – darum wird kein Fensterrand gezeichnet. Regentropfen auf der Linse viel seltener (Linse 3 mm tief hinter dem Fenster unter dem Regendach) |
| IR-LED | eine **5-mm-LED 850 nm** (Kanal 4) 20 mm neben und 16 mm unter der Linse: leuchtet nur die Nähe aus (ca. 4 m brauchbar, bei 7 m fertig; 1/d²; Schätzung, nicht gemessen). Ein / aus wie bisher mit dem Infrarotlicht (`light_ir_wide`) |
| Blindstopfen | Montage **«Nicht verbaut (Blindstopfen)»** (`none`): kein Bild (der Simulator rechnet die Kamera nicht, `/cam/1/…` antwortet 404 «not installed»), keine IR-LED; MoveEye meldet die Zusatzkamera als «wide camera not installed (blind cover)» statt «Simulator nicht erreichbar», «Übersicht lenkt den Kopf» wird (falls von selbst gesetzt) gelöscht |
| Kamera-Physik | Anschluss für `camphys.gd` (Zweig real-kamera): `weit.sensor_info()` liefert Blende f/2.2 (≈ 0,67 × Licht der Kopfkamera), NoIR, eingebaut ja/nein – das Sensor-Nachbearbeiten (Belichtung, Verstärkung, Rauschen) kann so für Kamera 1 dieselbe Funktion nutzen; die Optik (Fischauge, Ecken) bleibt in `weitwinkel.gd` |
