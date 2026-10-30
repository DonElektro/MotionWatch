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

## Umgesetzt (Entwurf, Branch wt-parcours, 30.10.2026 – Simulator 3D-4.18 / MoveEye 2.98.47, Nummern setzt der Lead)
- **Szene «Verfolgungs-Parcours»** (`simulator3d/scripts/parcours.gd`, in `scenes.gd` angemeldet): Wiese, Distanzmarken 5 / 10 / 20 / 40 m
  (Bögen ±60° mit Schild), Busch 2 m, Familienzelt 2,2 m, Auto, Baum; Ring 8 m ums Gerät schaltbar. Auch in `GREEN_SCENES`
  (Tarnung), `EXPORT_SCENES` (Trainingsbilder) und den Vorlagen.
- **Lektionen 1–7** mit festen Wegen (Figuren = Besucher aus `actor.gd` als Puppen, Aussehen fest pro Zufallszahl), **Lektion 8** =
  die gewählten Lektionen nachts (23:20) mit Infrarot. Vor jeder Lektion fährt der Kopf zur Mitte (MoveEye «center»).
- **Messung** (Wahrheit aus dem Simulator): Zielfehler (Grad, Mitte der Figur gegen Bildmitte der Kopfkamera), Zeit im Bild,
  Verdeckt-Anteil, Verluste (≥ 0,3 s draussen) und Wiederfinde-Zeit, Pendeln (kleine Hin-und-her-Bewegungen) und Überschwingen
  (im Stand), Servo-Weg, Verwechslungen (Lektion 6, nur solange MoveEye folgt) → **Note 1–6** und **Ergebniskarte** im Fenster.
  **Einblendung** (nur für den Bediener): geplanter Weg (blau), echter Weg (gelb), Blickstrahl + Bildränder (`laser.gd`),
  Fehlerkurve der letzten 30 s.
- **Prüfstand-Plan «folgen»** (`--plaene folgen`, `--folgen 1,3,…,8`, `--folgen-weitwinkel base,head_rear` = mit / ohne
  Weitwinkel-Übergabe); auf GitHub nur sonntags.
- **MoveEye** (Teile 416 / 569 / 599): Kachel 🎯 in der Simulator-Zentrale (Gruppe «Testen»): Lektionen, Start / Nacht / Stopp,
  Regler live (Tempo `servo_vmax_pan`, Verstärkung `track_gain`, Totzone `track_deadzone`, **neu Vorausschauen `track_lead`**,
  0 = wie bisher), letzter Lauf mit Fehlerkurven, **A/B** (Lauf A = jetzt, B = eine Änderung, oder zwei gespeicherte Läufe),
  **Auto-Tuning** (probiert Sätze, schlägt nur vor, Knopf «Vorschlag übernehmen»), **mit / ohne Weitwinkel-Übergabe**
  (braucht Schutz an). Fenster: Regler «Vorausschauen» und eine Karte im Reiter Simulator.
- **Spiel «Entkomme der Kamera»** (60 s): Figur mit dem Mover-Stick von MoveEye, dem Stick im Simulator oder per Steuerbefehl;
  10 Punkte/s ausserhalb des Bilds, 5 verdeckt, 100 pro Verlust, nur 4–25 m vom Gerät; Bot zum Ausprobieren; zählt in der
  Rangliste des Abends (`game.board_add_extra`, eigener Rekord «escape»), die Punkte-Regeln der Runden bleiben unverändert.
- **Lernbilder**: schnelle (> 2,5 m/s oder Kopf > 40°/s) oder weite (> 18 m) Figuren, höchstens 40 pro Lauf, nur Bild + Rahmen,
  Abstand, Tempo, geschätzte Unschärfe – keine Kartendaten; kommen ins Trainingsbilder-Paket (`dataset.gd`).
- **Realismus**: während eines Laufs «Servos wie echt» an (MG90S 200°/s, Spiel, Nachschwingen), Drehgrenze der Kopf-Montage der
  Weitwinkel-Kamera, Bildverzögerung von `simreal.gd`; die Ergebniskarte nennt es.
- Offen / nicht getestet: echte Hardware; Windows-Export; aussagekräftige Noten erst auf einem freien Rechner mit KI-Modell (hier
  2 Bilder/s, ohne Modell).
