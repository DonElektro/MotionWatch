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
