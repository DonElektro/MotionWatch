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
