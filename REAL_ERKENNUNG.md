# Grosser Erkennungstest – MoveEye 2.98.110 im 3D-Simulator 3D-4.79

Stand 31.10.2026, Zweig `real-erkennungstest` (nur Bericht und Messwerte, nichts an MoveEye oder am Simulator geändert).

## Kurz

- **72 Fälle** gemessen (3 Orte, 12 Bedingungen), dazu 6 Personen-Raster mit «blinden Flecken» (je 15 Stellen).
- **Personen** (gehen, kriechen/geduckt, Kind): **27 von 36 (75 %) erkannt**. Gehende Personen gut (10 von 12), kriechende/geduckte
  deutlich schlechter (7 von 12), bei Nebel **gar nichts**.
- **Fehlalarme:** im Leerlauf (45 s, Wind 55 km/h) 10× «Person» in 9 Min. (≈ 67 pro Stunde) und 2 falsche Pushes (≈ 13 pro Stunde); über alle Fälle ohne Person (Leerlauf, Tiere, Autos, 15 Min.) 6 falsche Personen-Pushes ≈ 23 pro Stunde. Dazu wurden Tiere und Autos 8 von 24 als **Person** gemeldet,
  zum Teil mit Push.
- **Tiere** werden selten richtig erkannt (3 von 12): das KI-Modell (COCO) kennt Reh, Fuchs, Wildschwein, Igel nicht.

## So wurde gemessen

- Rechner: 2 Kerne, Software-Grafik (llvmpipe), Xvfb :163. Simulator 3D-4.79 (`--stream --port 9263 --quality simple
  --mini-tiny`, eigenes HOME, **mit Welt**, nicht «allein»), MoveEye 2.98.110 (`--headless --port 5163`, eigener Ordner,
  Simulation, Test-Postfach, Wärmebild an). KI: eigenes Modell **test-coco640** (YOLO/ONNX, 640 px, Schwelle Person 0,30),
  wie in den früheren Berichten. MoveEye bekam **2–4 Bilder/s** (am Pi 10–15) – die Zahlen sind eher zu streng.
- Bewegungs-Verfolgung des Kopfs **aus** (`track_person`, `kopf_on` = aus, über `/api/set`), damit jeder Besuch sicher durchs
  Bild der Kopfkamera geht. Grund: im ersten Versuch folgte der Kopf einer *festen Fehl-Person* (siehe Schwachstelle 2) und
  drehte von −30° auf −71° weg.
- Pro Ort und Bedingung (Uhrzeit/Wetter über die Steuerbefehle `set hour/weather/wind/cond_ir/cond_headlights`, Jahreszeit «wie
  heute» = Ende Oktober, Dämmerung 17:30, Nacht 23:00 mit Infrarot) in dieser Reihenfolge:
  1. **Leerlauf** 45 s, niemand da, Wind 55 km/h (wehende Äste, Fahnen, Gras) → Fehlalarme,
  2. **Person geht** quer durchs Bild (`menschen probe walk`, Tag 10 m, Dämmerung 9 m, Nacht 7 m),
  3. **kriecht / geduckt** in dunkler Kleidung (`probe crawl` bzw. `sneak`, 5–7 m),
  4. **Kind** (6–8 m), 5. **Tier** (Reh, Fuchs, Katze, Hund, Krähen, Wildschwein, Igel, Elstern … reihum, 4–12 m),
  6. **Auto** quer auf 20 m (nachts mit Bedingung «Scheinwerfer»).
  Vor jedem Fall 3 s «leeres Bild» als Grundlinie: was MoveEye da schon meldet (feste Fehl-Personen, Gegenstände), zählt nicht
  als Erkennung. Danach MoveEye zweimal pro Sekunde abgefragt (`/api/state`: Personen-Kästchen, erkannte Klassen, Wärme) und
  die Pushes im Test-Postfach (`/api/messages`) gezählt.
- Bei **Tag** und **Nacht** zusätzlich das vorhandene Werkzeug **«blinde Flecken»** (`blindmap.gd`): eine Person steht an
  3 Richtungen × 5 Abständen, der Simulator prüft selbst, ob sie im Bild der Kopfkamera frei sichtbar ist (die «Wahrheit»).
- «Zeit bis erkannt» zählt **ab dem Start** des Besuchs am Bildrand ausserhalb des Bildes. Eine gehende Person ist bei 10 m
  nach etwa 5–6 s im Bild, bei 7 m nach etwa 4 s; Kind etwa 3–4 s. Ein Wert von 6 s bei «gehen» heisst also: knapp 1 s nach
  dem Eintritt ins Bild erkannt.
- Bilder: `/tmp/claude-0/real_shots/erkennung/` (`<ort>_<bedingung>_<fall>_mitte.jpg` = Bild nach etwa der halben Zeit,
  `…_erkannt.jpg` = Bild beim ersten Personen-Treffer, `…_statisch.jpg` = feste Fehl-Person im leeren Bild). Die 10 Bilder der
  Schwachstellen liegen auch im Zweig unter `erkennungstest/bilder/`.
- Werkzeuge und Rohdaten: `erkennungstest/` (Treiber `driver.py`, `lib.py`, Startskript, `results.jsonl` mit jedem Fall).

**Last:** Jeder Fall startete nur bei einer Last unter 5 (sonst bis 7 Min. gewartet, danach trotzdem, vermerkt in
`results.jsonl`). Ab etwa 15:15 lief parallel ein zweiter Simulator eines anderen Helfers (Port 9271); die Last blieb dann meist
über 5. Deshalb ist die Matrix kleiner geworden als geplant (siehe «Nicht getestet»).

## Tabelle: Ort / Zeit / Wetter × Ereignis

✔ = erkannt (Zeit ab Start des Besuchs, als was), ✘ = verpasst (was MoveEye stattdessen meldete: «nur Bewegung» = nur
Bewegung/Voralarm, «–» = gar nichts), ⚠Person = ein Tier oder Auto wurde als Person gemeldet. Leerlauf: «n× Person» = so oft
erschien eine Person, obwohl niemand da war (feste Fehl-Personen schon abgezogen), «Push» = ein Alarm-Push im Test-Postfach.

| Ort | Zeit / Wetter | Person geht | kriecht / geduckt | Kind | Tier | Auto | Leerlauf 45 s |
|---|---|---|---|---|---|---|---|
| Camping-Platz | Tag, klar | ✔ 6 s | ✘ – | ✔ 6 s | deer: ✘ – | ✘ Person | ruhig |
| Camping-Platz | Dämmerung, klar | ✔ 8 s | ✔ 21 s | ✔ 5 s | deer: ✘ Person | ✘ Person | 4× Person, 1 Push |
| Camping-Platz | Nacht, klar, Infrarot | ✔ 8 s | ✘ truck | ✘ nur Bewegung | fox: ✘ nur Bewegung | ✔ 12 s truck | ruhig |
| Camping-Platz | Tag, Regen | ✔ 16 s | ✘ – | ✔ 5 s | cat: ✘ – | ✘ Person | ruhig |
| Bergtal · Schattwald | Tag, klar | ✔ 7 s | ✔ 5 s | ✔ 7 s | dog: ✔ 8 s animal, dog ⚠Person | ✘ nur Bewegung | ruhig |
| Bergtal · Schattwald | Dämmerung, klar | ✔ 6 s | ✔ 6 s | ✔ 9 s | crows: ✘ – | ✘ nur Bewegung | 2× Person |
| Bergtal · Schattwald | Nacht, klar, Infrarot | ✘ nur Bewegung | ✔ 9 s | ✔ 4 s | boar: ✔ 11 s animal, sheep ⚠Person | ✔ 5 s car ⚠Person | 4× Person, 1 Push (animal,bird) |
| Bergtal · Schattwald | Tag, Nebel | ✘ – | ✘ – | ✘ – | hedgehog: ✘ – | ✘ – | ruhig |
| Ferienpark · Stellplatz | Tag, klar | ✔ 7 s | ✔ 6 s | ✔ 3 s | magpies: ✘ – | ✘ – | ruhig |
| Ferienpark · Stellplatz | Dämmerung, klar | ✔ 13 s | ✔ 17 s | ✔ 5 s | deer: ✘ nur Bewegung | ✘ nur Bewegung | ruhig |
| Ferienpark · Stellplatz | Nacht, klar, Infrarot | ✔ 5 s | ✘ nur Bewegung | ✔ 6 s | fox: ✔ 2 s animal, bird ⚠Person | ✘ nur Bewegung | ruhig (animal,bird) |
| Ferienpark · Stellplatz | Tag, Schnee | ✔ 10 s | ✔ 11 s | ✔ 4 s | deer: ✘ – | ✘ nur Bewegung | ruhig |

**Vorsicht beim Lesen:** Ein ✘ heisst nicht immer, dass MoveEye versagt hat. Auf dem **Camping-Platz** schaut die Kopfkamera
auf Zelt und Wohnwagen in 3–5 m; Tiere und Kriechende dahinter sind oft ganz verdeckt (Bilder geprüft: das Reh am Tag, das
Kind in der Nacht und die Katze im Regen waren nicht zu sehen). Im **Schattwald** steht direkt vor MoveEye eine grosse Fichte
und verdeckt die Bildmitte. Die verlässliche Wahrheit für Personen liefert das Raster «blinde Flecken» (Spalte «im Bild»).

## Die 10 grössten Schwachstellen

1. **Nebel: gar nichts erkannt.** Schattwald, Tag, Nebel: Person (10 m), Kriechender, Kind, Igel, Auto – alles ✘, nicht einmal
   «Bewegung». Die Person ist im Bild schwach zu sehen (rechts, etwa 10 m). Dafür kam im leeren Nebel-Bild ein
   **Sabotage-Push «Kamera verdreht / Bild verändert»** – ein Fehlalarm anderer Art.
   Bild: `erkennungstest/bilder/01_nebel_person_verpasst.jpg` (`real_shots/erkennung/wald_nebel_gehen_mitte.jpg`).
2. **Feste «Person» im leeren Bild.** Auf 5 von 12 Ort/Bedingungen meldete MoveEye ohne Besuch dauernd eine Person – auf dem
   Camping-Platz eine kleine Fichte auf einem Steinsockel (Kasten im Bild), nachts im Wald ein Baumstamm. Mit Kopf-Verfolgung
   (Standard) **dreht der Kopf dieser Fehl-Person nach** (von −30° auf −71°) und schaut dann am echten Geschehen vorbei.
   Bild: `02_feste_fehlperson_fichte.jpg` (`camping_tag_statisch_markiert.jpg`).
3. **Kriechen / geduckt in dunkler Kleidung, nachts.** Auf dem Stellplatz robbt jemand in 5 m durchs Infrarot-Licht – gut
   sichtbar, MoveEye meldet nur «Bewegung». Insgesamt nur 7 von 12 kriechende/geduckte Personen erkannt, nachts 1 von 3.
   Bild: `03_nacht_kriechen_verpasst.jpg` (`stellplatz_nacht_kriechen_mitte.jpg`).
4. **Fehlalarme in der Dämmerung.** Camping-Platz 17:30, niemand da, Wind: 4× Person und ein **Push «Person, ca. 22 m»**; kurz
   darauf ein zweiter Push «Person, ca. 19 m», bevor das Reh überhaupt ins Bild kam. Im Wald in der Dämmerung 2× Person.
   Bild: `04_daemmerung_fehlalarm_leer.jpg` (`camping_daemmerung_leer_erkannt.jpg`).
5. **Auto wird zur Person (Wärmebild).** Ein Auto auf 20 m gab auf dem Camping-Platz am Tag einen **Push «Person
   (Wärmebild)»** – der warme Motor zählt als warmer Körper. Autos wurden in 4 von 12 Fällen als Person gemeldet, nur 2× als Auto.
   Bild: `05_auto_waermebild_als_person.jpg` (`camping_tag_fahrzeug_erkannt.jpg`).
6. **Nachts Push durch einen Baumstamm.** Schattwald 23:00, niemand da: Push «Person, ca. 2 m» – der Stamm der Fichte direkt vor
   der Kamera im Infrarot-Licht. Bild: `06_nacht_baumstamm_push.jpg` (`wald_nacht_leer_erkannt.jpg`).
7. **Tiere als Person mit Push.** Hund am Tag (Wald): richtig «dog», aber 14 s später **Push «Person, ca. 10 m»**;
   Wildschwein nachts: «sheep» und **Push «Person»**; Fuchs nachts: «bird» und Person. Insgesamt 8 von 24 Tier-/Auto-Fälle
   mit Person-Meldung. Bild: `07_hund_als_person.jpg` (`wald_tag_tier_erkannt.jpg`).
8. **Kurze Reichweite im Wald.** Raster «blinde Flecken» im Schattwald: am Tag nur 5 von 15 Stellen erkannt (alle 15 frei im
   Bild), nichts über 10 m – auf dem offenen Stellplatz 13 von 14 bis 25 m. Hintergrund mit Stämmen und Schatten ist schwer.
   Bild: `08_wald_reichweite.jpg` (`wald_tag_leer_mitte.jpg`).
9. **Tierart fast nie richtig.** Nur 3 von 12 Tiere überhaupt als Tier erkannt; das COCO-Modell kennt Reh, Fuchs, Wildschwein,
   Igel, Dachs nicht – es sagt «sheep», «bird», «dog» oder nichts. Krähen und Elstern (am Boden) wurden nie erkannt.
   Bild: `09_fuchs_als_vogel_und_person.jpg` (`stellplatz_nacht_tier_erkannt.jpg`, der Fuchs ist schon fast aus dem Bild).
10. **Regen und Schnee machen langsam.** Gehende Person bei Regen erst nach 16 s (klar: 6 s), bei Schnee 10 s, kriechend bei
    Schnee 11 s. Nachts ohne Kriechen bleibt die Reichweite bei etwa 10 m (Camping, Wald) bis 18 m (Stellplatz).
    Bild: `10_regen_spaet.jpg` (`camping_regen_gehen_mitte.jpg`).

Gut lief: **gehende Personen** und **Kinder** am Tag, in der Dämmerung und nachts mit Infrarot meist in 1–2 s nach dem Eintritt
ins Bild; Schnee und Regen ohne Fehlalarm im Leerlauf; Autos nachts mit Scheinwerfern gaben keinen Push.

## Vorschläge für MoveEye (nur Vorschläge, nichts geändert)

1. **Feste Fehl-Personen lernen:** ein Personen-Kasten, der sich über Minuten nicht bewegt und schon beim «Einrichten» da war,
   als «Gegenstand» merken (Masken-Vorschlag «Hier steht etwas, das wie eine Person aussieht – ignorieren?») – und der Kopf
   folgt ihm nicht.
2. **Wärmebild-Person nur mit Bestätigung:** «Person (Wärmebild)» erst melden, wenn Form/Grösse passt (stehend höher als breit)
   oder die Kopfkamera / KI es bestätigt; ein breiter, sehr warmer Fleck, der schnell fährt = Fahrzeug.
3. **Tier vor Person:** wenn die KI im selben Bereich «dog/cat/sheep/bird» sieht, keine Person-Meldung aus der Bewegung
   oder dem Wärmebild für diese Spur (Spur-Klasse beibehalten).
4. **Nebel-Modus:** bei erkannter Nebel-Lage (wenig Kontrast) Kontrast-Anhebung (CLAHE) vor der KI und mehr Gewicht auf
   Wärmebild; Hinweis an den Benutzer «Nebel – Sicht eingeschränkt».
5. **Dämmerung strenger:** zwischen Tag- und Nacht-Belichtung (Rauschen, Verstärkung steigt) Personen nur nach 2–3 Treffern in
   Folge melden; Wind-Stärke (schon gemessen, Push «starker Wind») als Grund für strengere Prüfung nutzen.
6. **Kriechende nachts:** Bewegung am Boden in Nähe (< 8 m) im Infrarot-Licht mit Wärme = Voralarm «etwas Grosses am Boden»;
   ein Modell mit liegenden/kriechenden Personen trainieren (KI-Training `ki_training/`).
7. **Eigenes Tier-Modell:** Reh, Fuchs, Wildschwein, Dachs, Igel, Katze, Hund, Vogel als eigene Klassen (Wildtier-Zielgruppe).
8. **Reichweite im Wald:** KI-Zoom (Kachel um die Bewegung) auch bei weiter Bewegung ohne Kasten, grössere Eingabe (z. B. 960 px)
   am Pi 5 prüfen.

## Was nicht getestet werden konnte

- **Welten Festival und Zuhause (Garten, Baustelle) und der zweite Bergtal-Ort (Wildbeobachtung): nicht gemessen.** Ab etwa
  15:15 lief ein zweiter Simulator eines anderen Helfers; die Last lag dann bei 6–10 und jeder Fall wartete bis 7 Min.
  Getestet: 3 von 5 Welten (Camping-Platz, Bergtal · Schattwald, Ferienpark · Stellplatz).
- **Schlafzimmer (Hamster, Spinne vor der Linse, Wellensittich): nicht gemessen** (Last über 5).
- **Dämmerung** nur mit klarem Himmel; **Nebel** nur im Wald, **Schnee** nur auf dem Stellplatz, **Regen** nur auf dem
  Camping-Platz am Tag; **Nacht mit Regen** gar nicht.
- **Wehende Äste** nur als Wind 55 km/h im Leerlauf (kein eigener Fall «Ast direkt vor der Linse»).
- **Scheinwerfer** nur nachts mit Auto (Bedingung «Scheinwerfer»), nicht als Blendung direkt in die Kamera.
- Nacht nur **mit Infrarot**; «Nacht ohne Licht» (nur Wärmebild) nicht getrennt.
- Mit **Kopf-Verfolgung aus** gemessen (siehe oben); mit Verfolgung könnten Erkennung und Fehlalarme anders sein.
- Pushes: die «Pause zwischen Meldungen» (60 s) verschluckt Pushes kurz nacheinander – die Push-Zahlen sind eine Untergrenze;
  die Erkennung selbst wurde über den Zustand von MoveEye gemessen.
- Pro Fall **ein** Versuch – ein einzelnes ✘ ist kein Beweis. Kein Vergleich mit/ohne Kamera-Effekte.
- Nicht benutzt: `nachtlauf.gd` (ganze Nacht, 1 h im Schnell-Tempo – zu lang für das Zeitbudget) und der Kontaktbogen
  (devtool_kontakt) – statt dessen Einzelbilder aus MoveEye (`/api/frame.jpg`).
- Echte Hardware (Pi 5, Camera Module 3 NoIR, Thermal-90) – nur Simulator. Der Pi bekommt 10–15 Bilder/s statt 2–4.

## Zahlen

- Person geht: 10 / 12 erkannt, Median 8 s ab Start
- kriecht / geduckt: 7 / 12 erkannt, Median 9 s ab Start
- Kind: 10 / 12 erkannt, Median 5 s ab Start
- Tier: 3 / 12 erkannt, Median 8 s ab Start
- Auto: 2 / 12 erkannt, Median 12 s ab Start
- Leerlauf: 12 Abschnitte, 9.0 min, 10× Person ohne Person (67 / h), 2 falsche Pushes (13 / h)
- Tier / Auto als Person gemeldet: 8 von 24
- Feste «Person» im leeren Bild (vor dem Besuch schon da): 5 von 12 Orten/Bedingungen: camping/daemmerung, camping/regen, camping/tag, stellplatz/tag, wald/nacht

| Ort | Zeit | Personen-Raster (stehend, 3 Richtungen × 5 Abstände): erkannt / im Bild / Punkte | weitester Treffer |
|---|---|---|---|
| Camping-Platz | Tag, klar | 11 / 13 / 15 (feste Fehl-Person!) | 20 m |
| Camping-Platz | Nacht, klar, Infrarot | 7 / 11 / 15 | 10 m |
| Bergtal · Schattwald | Tag, klar | 5 / 15 / 15 | 10 m |
| Bergtal · Schattwald | Nacht, klar, Infrarot | 7 / 15 / 15 | 10 m |
| Ferienpark · Stellplatz | Tag, klar | 13 / 14 / 15 | 25 m |
| Ferienpark · Stellplatz | Nacht, klar, Infrarot | 10 / 15 / 15 | 18 m |


Rohdaten: `erkennungstest/results.jsonl` (ein Fall pro Zeile: gesehene Klassen mit Zeit, Pushes, Bilder/s, Last).
