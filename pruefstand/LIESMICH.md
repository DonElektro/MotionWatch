# Prüfstand – die Erkennung messen

Der Prüfstand beantwortet bei jeder neuen Version die Frage: **Erkennt MoveEye besser oder schlechter als vorher?**

## So funktioniert es

1. `pruefstand.py` startet den 3D-Simulator und Motion Watch ohne Bildschirm (eigener, leerer Einstellungs-Ordner,
   Simulation an, keine Updates).
2. Im Simulator läuft ein fester **Testlauf** (`simulator3d/scripts/testrun.gd`): Phasen mit Tag, Nacht, Wind, Regen,
   Infrarot … und immer **dieselben Besucher auf denselben Wegen** (fester Zufallsstart). Der Simulator weiss, wer wann für eine
   Kamera sichtbar war (frei, gross genug, genug Licht) und vergleicht das mit dem, was Motion Watch meldet.
3. Die Zahlen kommen als JSON nach `ergebnisse/` und in die Tabelle **`VERLAUF.md`**:
   **Pushes richtig / falsch**, Personen erkannt (%), davon nur im Wärmebild, Reaktionszeit, Tiere gemeldet, Flackern,
   Bilder pro Sekunde, ob die KI lief.
4. Der Lauf wird mit dem letzten **vergleichbaren** Lauf verglichen (gleicher Testlauf, gleicher Rechner, gleicher KI-Stand):
   15 Prozentpunkte weniger Personen oder **ein falscher Push mehr pro Lauf** = «SCHLECHTER» (bei alten Läufen ohne Pushes:
   ein Flackern mehr pro Lauf) – Personen erst, wenn beide Läufe mindestens 8 Personen hatten.

## Prüfstand 2 (Wunsch Daniel, 29.10.2026)

- **Pushes statt Flackern.** Früher zählte jedes Aufflackern der Personen-Erkennung (0 → 1 Person) als Fehlalarm – ein Dachs
  gab so 3–5 «Fehlalarme» in Sekunden. Jetzt zählt, was auf dem Handy ankäme: MoveEye läuft im Prüfstand mit dem
  **Test-Postfach** (`notify_sandbox`), und schickt dem Simulator mit jedem Zustand die letzten Nachrichten seiner Liste
  «Nachrichten» (Teil `quelle/068_pruefstand_pushes.py`, Feld `det.pushes`). Der Simulator ordnet jeden Alarm-Push
  (Person, Wärme, Voralarm) zu: **richtig**, wenn bis 6 s vorher eine Person sichtbar oder wenigstens im Bild war, sonst
  **falsch** (mit vermuteter Ursache). Derselbe Besuch nochmals innert 10 s zählt einmal (ebenso ein zweiter falscher Push
  innert 10 s). Die alte Zahl heisst jetzt **Flackern** und steht weiter in der Tabelle. Die Pause zwischen zwei Pushes
  (Einstellung «Pause zwischen Meldungen», 60 s) gilt auch hier – wie am echten Gerät.
- **Nacht ohne Licht mit Wärmebild.** Die Wärmebildkamera von MoveEye ist im Prüfstand an (`--waermebild an`, Standard).
  Nachts zählt eine Person auch als sichtbar, wenn die Wärmebildkamera (Simulator `cams[2]`, auf dem Kopf) sie frei, gross
  genug (mindestens 8 der 62 Zeilen, bei Regen / Schnee mehr, bei Nebel noch mehr) und wärmer als die Nacht sieht. Damit
  messen auch «Nacht, ohne Licht» und «Nacht, Regen» etwas. Spalte **Wärmebild** = Personen, die nur das Wärmebild sah
  (erkannt / sichtbar).
- **Ganze Nacht** (`nacht`): 20–6 Uhr im Zeitraffer in etwa 11 Minuten (die Uhr des Simulators läuft schneller), etwa
  20 Tiere, Windböen, ein Regenschauer, ruhige Abschnitte ohne Besuch und 2 Personen. Hauptzahl: **Pushes pro Nacht**
  (richtig / falsch). `--mal` vervielfacht diese Nacht nicht (realistische Zahlen).
  **Später (Daniel 31.10.2026):** «Ganze Nacht» auf den Nacht-Ablauf `simulator3d/scripts/nachtlauf.gd` des
  Nacht-Testlaufs (MoveEye 579b, Seite /nacht) umstellen – ein Nacht-Ablauf für beide.
- **Zufallsstarts** (`--seeds 3`): Zufall 1 = die festen Besucher von früher (4711), 2, 3 … dieselben Besucher auf anderen
  Wegen. In `VERLAUF.md` steht dann die Streuung (kleinster–grösster Wert pro Lauf). Mehr Personen: `--mal 1` … `--mal 5`.
- **Schleichwege automatisch:** `pruefstand.py` übernimmt bei jedem Lauf die Schleichwege aus `feedback/` (Spielberichte als
  ZIP oder `schleichweg_*.json`) nach `simulator3d/spielwege/` – derselbe Weg nur einmal. Im Simulator geht es auch direkt:
  Prüfstand → **«Schleichwege an GitHub senden»** (GitHub-Schlüssel des Prüfstands; ohne Schlüssel in einen Ordner auf
  dem Schreibtisch, die Dateien im Chat anhängen).
- **Echte Nächte nachspielen** (`echtenaechte`): siehe unten.

## Übersicht → Kopf findet Ziel (Weitwinkel-Kamera, ab Simulator 3D-4.17)

`--weitwinkel case,base,head_front,head_rear` (`case` = im Gehäuse v5.2, Standard ab P9; auch `scene` als Vergleich ohne
Übersicht am Gerät) misst pro Montage der
Weitwinkel-Kamera: ein Besucher kommt **ausserhalb des Bildes der Kopfkamera** ins Weitwinkel-Bild (vorne: 42° neben der Mitte,
von 14 m auf 6 m auf das Gerät zu – im Weitwinkel-Bild ±51°, nicht im Kopfbild ±33°; hinten: quer hinter dem Kopf, 150° → 215°,
9 m), langsam (0,3 m/s). Gemessen wird die Zeit, bis die **Kopfkamera ihn im
Bild hat** (der Kopf drehte hin; der Simulator weiss es, Steuerbefehl `weit` / `probe`) und bis MoveEye eine Person meldet.
`--ww-versuche 3` Besucher pro Montage. Nur diese Messung: `--plaene "" --ohne-extras --weitwinkel …` – das Ergebnis kommt nach
`ergebnisse/weitwinkel_*.json` (nicht in `VERLAUF.md`). MoveEye läuft dafür mit `sim:1` als Zusatzkamera, Schwenk-Servo 360°
und Drehgrenze ± 170° (Kabel). Lokal nur aussagekräftig, wenn der Rechner frei ist (das Weitwinkel-Bild kommt sonst mit unter
1 Bild/s, die Bewegung braucht dann Sekunden, bis sie zählt).

## Plan «folgen»: Verfolgungs-Parcours (ab Simulator 3D-4.18, MoveEye 2.98.47 Entwurf)

`--plaene folgen` (oder `--folgen 1,3,4,5,6,7`) lässt die Lektionen des Verfolgungs-Parcours laufen (Szene «parcours», feste Wege,
Zufall 1 … `--seeds`): MoveEye folgt, der Simulator misst Zielfehler, Zeit im Bild, Verluste und Wiederfinde-Zeit, Pendeln /
Überschwingen, Servo-Weg und Verwechslungen → Note 1–6. `8` in der Liste = dieselben Lektionen nochmals nachts mit Infrarot.
`--folgen-weitwinkel base,head_rear` vergleicht pro Montage **mit und ohne Weitwinkel-Übergabe** («Übersicht lenkt den Kopf»,
MoveEye mit `sim:1`, Schutz an). Läuft nach den anderen Plänen (wechselt die Szene); Ergebnis in `ergebnisse/folgen_*.json`
(nicht in `VERLAUF.md`), auf GitHub in der Zusammenfassung. Dauer etwa 3 Min. pro Durchgang – **nicht im «quick»-Budget**:
auf GitHub nur sonntags (oder von Hand mit «folgen» in den Testläufen). Lokal nur aussagekräftig mit mindestens ~3 Bildern/s
bei MoveEye und einem KI-Modell (ohne Modell folgt MoveEye nur der Bewegung).

## Wann läuft was auf GitHub?

| Anlass | Testläufe | Dauer |
|---|---|---|
| neue Version (versions.json) | quick, night, standard, ganze Nacht; quick auch ohne Kamera-Effekte; Zufall 1 | etwa 40 Min. |
| jeden Sonntag in der Nacht | dazu **hard** (Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten) und **folgen** (Verfolgungs-Parcours), 3 Zufallsstarts | etwa 2½ Std. |
| von Hand (Run workflow) | frei wählbar: Testläufe, «hard» ankreuzen, Zufallsstarts, Besucher ×1–5, Kamera-Effekte | |

## Verlässlichere Zahlen (ab MoveEye 2.98.13 / Simulator 3D-4.0)

- **Besucher gehen gezielt durchs Bild der Kopfkamera** (nah / mittel / weit gemischt, quer durch das Bild). Vorher liefen
  sie quer über den ganzen Platz: viele kamen nie ins Bild, nachts nie ins Infrarotlicht → «0 / 0».
- Nachts nur so weit, wie das Licht reicht (Infrarot etwa 14 m). Ohne Licht sieht die Kamera niemanden – das zählt nicht.
- **Sichtbar** heisst: Kopf **und** Körper frei (vorher reichte der Kopf über einem Zelt).
- **Mehr Besucher**: `--mal 2` (Standard) schickt jede Besucherliste zweimal.
- **Mit und ohne Kamera-Effekte** (`--realismus an,aus`): jede Zeile «· ohne Kamera-Effekte» zeigt, ob ein Rückgang am
  realistischeren Bild des Simulators oder an MoveEye liegt.
- Szene **Stellplatz** (freie Sicht wie auf einem Camping-Platz; der Camping-Platz der Simulation verdeckt sehr viel).
- 15 s Eingewöhnen pro Phase (die Belichtung der Kamera braucht Zeit).

## Testläufe

| Name | Inhalt | Dauer |
|---|---|---|
| `quick` | Tag mit Wind, Nacht mit Infrarot | ca. 2½ Min. |
| `standard` | Tag, Wind und Wolken, Nacht mit Insekten, Nacht mit Regen | ca. 5 Min. |
| `night` | Nacht ohne Licht, mit Infrarot, mit Regen | ca. 4 Min. |
| `hard` | Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten | ca. 9 Min. |
| `nacht` | Ganze Nacht 20–6 Uhr im Zeitraffer: Tiere, Wind, Regenschauer, 2 Personen | ca. 11 Min. |
| `camping_voll` | **Voller Campingplatz** (eigene Szene): Nachbarn bewegen sich dauernd im Bild, Fremde kommen vom Weg an deinen Platz; Nachmittag und Nacht | ca. 3 Min. (×1) |
| `tarnen` | **Tarnen und Kriechen** (eigene Szene): Tarnkleidung + Robben, Schirm, Karton – nah (5–10 m); Tag, Dämmerung, Nacht | ca. 4½ Min. (×1) |
| `velodieb` | **Velodieb** (eigene Szene): rennt hin, greift das Velo (Velo-Sensor), rennt weg; Tag, Dämmerung, Nacht | ca. 4 Min. (×1) |
| `spielwege` | Schleichwege aus dem Spiel (läuft automatisch mit, wenn es welche gibt) | je Weg |
| `echtenaechte` | Alarm-Spuren echter Nächte, wie aufgenommen und mit anderem Wetter (automatisch, wenn es welche gibt) | je Fall ca. 2 Min. |

### Neue Szenen (Simulator 3D-4.x, `szenenplus.gd`)

Die drei Pläne `camping_voll`, `tarnen`, `velodieb` laden ihre **eigene Szene** (`--szene` gilt für sie nicht) und stellen
danach die alte wieder her. Sie sind **nicht** im kurzen Lauf «quick» (Wunsch Daniel: Prüfstand sparsam) – sie laufen
sonntags mit den grossen Läufen oder von Hand: `--plaene camping_voll,tarnen,velodieb`. Feste Zufallszahlen wie alle Pläne.
Hauptzahlen sind die echten **Pushes richtig / falsch** und die Reaktionszeit; dazu im Bericht `szene`:
- `camping_voll`: wie viele Fremde an deinen Platz kamen, mit / ohne Push, **Reaktion ab Betreten des Platzes**, und
  **falsche Pushes wegen Nachbarn** (ein Push, während nur Nachbarn im Bild waren). Die Quote «Personen erkannt» ist hier
  wenig aussagekräftig, weil fast immer Nachbarn im Bild sind.
- `tarnen`: pro Art (robben, schirm, karton) sichtbar / erkannt / mit Push.
- `velodieb`: Griffe, Push vor / nach dem Griff, ohne Push, **Reaktion ab Griff** (negativ = schon vorher gemeldet).

## Starten

Auf GitHub: **Actions → Prüfstand → Run workflow** (läuft auch jeden Sonntag in der Nacht). Dort mit echtem KI-Modell;
das Ergebnis wird ins Repository geschrieben.

Auf einem Linux-PC (braucht Godot 4.3, Python mit opencv, numpy, flask, pillow, cryptography; ohne Bildschirm Xvfb):

```
python3 pruefstand/pruefstand.py --godot /pfad/Godot_v4.3-stable_linux.x86_64 --plaene quick,night
python3 pruefstand/pruefstand.py --sim-bin /pfad/MotionWatch3D.x86_64 --plaene standard --wiederholungen 3
python3 pruefstand/pruefstand.py --nur-verlauf          # nur VERLAUF.md neu schreiben
```

`--streng` gibt den Rückgabewert 3, wenn die Erkennung schlechter geworden ist (für automatische Prüfungen).
Weitere Schalter: `--seeds 3`, `--mal 5`, `--realismus an,aus --roh-plaene quick`, `--waermebild aus`, `--ohne-extras`
(ohne Schleichwege und echte Nächte), `--wege-einlesen`, `--fall-aus-spur DATEI`.

## Grenzen

- Der Simulator ist nicht die Wirklichkeit: Die Zahlen zeigen, ob eine Version **besser oder schlechter als die vorherige**
  ist, nicht wie gut Motion Watch in einer echten Nacht ist. Dafür braucht es weiterhin Testnächte mit dem echten Gerät.
- Ein langsamer Rechner liefert weniger Bilder pro Sekunde und damit schlechtere Zahlen: nur Zeilen vom gleichen Rechner vergleichen.
- Auf GitHub (ohne Grafikkarte) liefert der Simulator nur etwa **2 Bilder pro Sekunde**; die Kamera am echten Pi 10–15.
  Die Zahlen sind dort also eher zu streng.
- Pro Lauf sind nur wenige Personen gut sichtbar (3–6). Für verlässlichere Zahlen `--wiederholungen 3` oder den Testlauf `standard`
  nehmen; ein Unterschied von einer Person ist noch kein Beweis.
- Ohne KI-Modell (z. B. ohne Internet) erkennt Motion Watch Personen nur über Bewegung und Gehmuster – die Spalte «KI» zeigt das.

## Auf dem eigenen PC (ab Simulator 3D-3.49)

Im 3D-Simulator: Werkzeuge → «Prüfstand: Erkennung messen». Motion Watch wählen (das verbundene oder eine Datei
`webcam_bewegung_X.py` einlesen), Testläufe ankreuzen, «Messung starten». Am Schluss erscheint das Ergebnis.
«Ergebnis senden» legt die Datei mit einem GitHub-Schlüssel (fein abgestuft, nur dieses Repository, «Contents: Read and write»)
direkt in `pruefstand/ergebnisse/`; der Ablauf «Prüfstand-Verlauf» schreibt dann `VERLAUF.md` neu. Ohne Schlüssel landet die
Datei auf dem Schreibtisch und kann im Chat angehängt werden.

## Schleichwege aus dem Spiel (ab Simulator 3D-3.53)

Liegen in `simulator3d/spielwege/` Dateien `schleichweg_*.json` (aus den Spielberichten in `feedback/spiel/`), läuft
der Plan «spielwege» bei jedem Prüfstand automatisch mit: eine Figur geht genau die Wege, auf denen Spieler unerkannt
ins Ziel kamen.

## Echte Nächte nachspielen (Prüfstand 2)

MoveEye merkt sich bei jedem Alarm, wo im Bild die Personen und Tiere waren (15 s vorher bis 20 s nachher, etwa zweimal pro
Sekunde; Teil 180 `alarm_track_sample`, Datei `alarm_tracks.json` im Einstellungs-Ordner von MoveEye; im Simulator als
«Alarm-Rückblick in 3D»). So eine Spur wird zum **Prüfstand-Fall**:

- im Simulator: den Alarm-Rückblick abspielen, dann Prüfstand → **«Letzten Alarm-Rückblick als Prüfstand-Fall»** (mit
  GitHub-Schlüssel direkt nach `simulator3d/pruefnaechte/`, sonst nur auf diesem PC), oder
- auf dem PC: `python3 pruefstand/pruefstand.py --fall-aus-spur alarm_tracks.json [--spur-id KENNUNG] [--spur-wetter rain]`
  (Beispiel zum Ausprobieren: `pruefstand/beispiel_alarmspur.json`, eine simulierte Spur).

Der Testlauf `echtenaechte` spielt jeden Fall (höchstens 4, die neusten) viermal: **wie aufgenommen**, **Nacht mit Regen**,
**Nacht ohne Licht**, **Tag mit Wind**. Jede Figur der Spur geht ihren Weg nach (aus der Lage im Bild und der Grösse des
Rahmens: Person 1,7 m, Tier 0,6 m). So zeigt sich, ob MoveEye denselben Besuch auch bei anderem Wetter gemeldet hätte.

Format einer Datei in `simulator3d/pruefnaechte/` (JSON):

```
{"v": 1, "title": "Alarm 02.11. 23:41", "date": "2026-11-02 23:41", "hour": 23.7, "weather": "clear", "wind": 10,
 "quelle": "MoveEye-Alarm 20261102_234100 (echt)",
 "variants": [{"name": "Nebel", "hour": 2.0, "weather": "fog", "wind": 5, "cond": ["ir"]}],      ← freiwillig
 "samples": [{"t": 1793659260.1, "pan": 12.0, "tilt": -3.0,
              "objs": [{"k": "person", "x": 0.41, "y": 0.62, "h": 0.22}, {"k": "cat", "x": 0.7, "y": 0.8, "h": 0.05}]}, …]}
```

- `samples` = genau die Punkte der Alarm-Spur von MoveEye: Zeit (Unix-Sekunden), Schwenk / Neigung des Kopfes in Grad,
  pro Figur Art (`k`), Mitte des Rahmens `x`, `y` und Höhe `h` (0…1 des Bildes der Kopfkamera).
- `hour` / `weather` / `wind`: wie es in der Nacht war (ohne Angabe: klar, Wind 10).
- `variants` (freiwillig): andere Bedingungen statt der drei Standard-Varianten; `cond` wie in den anderen Testläufen
  (`ir`, `glare`, `drops`, `web`, `headlights`, `shadows`).
- Kartengebunden (Wunsch Daniel): die Wege gelten nur von MoveEye aus gesehen; Hindernisse der Szene können anders stehen
  als in der echten Nacht.
