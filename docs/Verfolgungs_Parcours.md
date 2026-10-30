# Simulator-Szene «Verfolgungs-Parcours» (Entscheide Daniel, 30.10.2026 09:50)

Zweck: den Verfolgungsmodus des Kopfs (Folgen) trainieren, einstellen und überwachen. Die echten Positionen der Figuren sind im Simulator bekannt → genaue Messung.
Umsetzung: **nach der Weitwinkel-Runde** (`docs/Gehaeuse_Variante2_Weitwinkel.md`), baut auf dem neuen Kamera-Modell auf.

## Ort
Offene Wiese mit Distanzmarken 5 / 10 / 20 / 40 m, Hindernisse (Busch, Zelt, Auto, Baum) für Verdeckungen, optional Ring rund ums Gerät.

## Lektionen (alle gewählt)
1. Langsam quer durchs Bild
2. Auf die Kamera zu / weg (Grössenänderung)
3. Zickzack und Tempowechsel (gehen → joggen → rennen → Velo)
4. Stopp und Weiterlaufen (kein Nachpendeln)
5. Verdeckung: hinter Hindernis verschwinden und wieder auftauchen
6. Zwei Personen kreuzen sich (Verwechslung)
7. Tier: Fuchs / Reh, schnell und unregelmässig
8. Nacht-Durchgang: alle gewählten Lektionen mit IR

## Messen und Anzeigen (alle gewählt)
- Messwerte pro Lektion: Zielfehler in Grad, Zeit im Bild (%), Verluste und Wiederfinde-Zeit, Überschwingen / Pendeln, Servo-Weg, Verwechslungen → Note und Ergebniskarte
- Live-Einblendung im Simulator-Fenster: Weg der Figur, Blickstrahl des Kopfs, Fehlerkurve
- Prüfstand-Plan **«folgen»** (feste Zufallszahlen; auf GitHub nur, wenn es ins «quick»-Budget passt, sonst sonntags)
- **Vergleich mit / ohne Weitwinkel-Übergabe** (pro Montage-Variante)

## Werkzeuge (alle gewählt)
- Regler für die Verfolgung in MoveEye (Tempo, Totzone, Vorausschauen) live verstellen + **A/B-Vergleich** zweier Läufe
- **Auto-Tuning**: Reglerwerte durchprobieren, beste vorschlagen (nicht automatisch übernehmen)
- Spiel **«Entkomme der Kamera»**: Figur mit dem Stick steuern, Punkte (passt in die Spiel-Karte, Rangliste)
- **Lernbilder sammeln**: bewegte / weit entfernte Figuren, nur Bilddaten (Regel «Daten aus dem Simulator»)

## Realismus
MG90S-Tempo, 180°-Grenze (bzw. Drehgrenze bei Kamera auf dem Kopf), Verzögerung und Nachschwingen wie «realistische Servos».
