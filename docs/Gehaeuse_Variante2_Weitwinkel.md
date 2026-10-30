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
und «Alarm quittieren» – Platz und Kabel (GPIO) im Gehäuse vorsehen.

## Blindabdeckung für die Weitwinkel-Öffnung (Wunsch Daniel, 30.10.2026 22:05)

Solange die Weitwinkel-Kamera nicht eingebaut ist: **einrastender Stopfen** (kleine Rastnasen, ohne Werkzeug lösbar) für die
Kamera-Öffnung und ein zweiter kleiner Stopfen für das Loch der breiten IR-LED. Lieferung: **STL + parametrisches Python-Skript**.
Wartet auf Daniels Gehäuse-Modell (Upload), damit die Masse der Öffnung stimmen.
