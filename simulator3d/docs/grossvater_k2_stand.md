# Grossvater K2 – Abenteuer-Kit: Stand

Zweig `sim-grossvater-k2` (von origin/main 9f14de1), Worktree /tmp/claude-0/wt_grossvater. Auftrag: Grundlage «Abenteuer-Kit»
(Figur, Kamera-Regie, Steuerung, schlanker Bildschirm, Maggie als Begleiterin, Musik-Zustände), danach Kapitel 2 in 12 Szenen
(Geschichte freigegeben 20.11. 23:45). Besitzer 21.11.: «Beides» – zuerst eigene Schlucht (gebaut), Bergtal-Fehler später separat.

## Dateien
- `scripts/kit_abenteuer.gd` – Rahmen: Start/Stopp, Szenen-Ablauf aus Daten, Eingabe (Tasten, Controller über padmap, Touch),
  Checkpoints, Funde, Abzeichen, Maggie-Hilfen, Steuerbefehl `{"action": "kit", …}` (Kopf der Datei).
- `scripts/kit_spaet.gd` – läuft nach den Figuren (Höhe, Kamera, HUD).
- `scripts/kit_figur.gd` – Spielfigur (Zustände boden/luft/klettern/leiter/balance/seil/haengen/heben/steuern/film/zurueck).
- `scripts/kit_regie.gd` – Folgekamera mit Federarm, Shots (establish/schulter/reveal/nah/fix/maggie), Wand-Ausweichen,
  Balken, Zeitlupe, Film-Zeitleiste (überspringbar).
- `scripts/kit_hud.gd` – Ziel, Kompass, Hinweis, Untertitel, Pause-Menü, Touch-Stick + Knöpfe, Sepia-Rückblende.
- `scripts/kit_maggie.gd` – Maggie (erbt maggie_hund.gd): folgen, riechen, warnen, heben, steuern.
- `scripts/kit_parcours.gd` – Parcours aus Daten (Steine, Blöcke, Wände mit Tor/Fenster, Leiter, Seil, Stamm, Wasser, Spalt, Fälle, Funde).
- `scripts/kit_schlucht.gd` – eigene Schlucht (Höhenfeld, Mesh, Ausschnitt im Bergtal-Boden, Steine versteckt).
- `scripts/kit_k2_daten.gd` – Kapitel 2: Texte, Schlucht, Parcours, Aktionen, Checkpoints, 12 Szenen (6–12 noch Stubs).
- Geändert: `anim_mensch.gd` (Posen balance/haengen/heben/schwingen/sprung/zeigen), `klang.gd` (Kontext «kit», musik_zustand,
  kit_ton), `bergtal.gd` (boden_fn in gy), `bergtal_abenteuer.gd` (Schalter «Neuer Spielmodus (Probe)»; HUD nur bei Änderung,
  höchstens 2×/s neu), `main.gd` (var kit, _fly, busy_with), `main_steuerung.gd` (action kit), `padmap.gd`, `tasten.gd`,
  `maggie_hund.gd` (tier_modell-Rest von Maggie entfernen – sonst SCRIPT ERROR bei jedem Bild, sobald Maggie gebaut wird).
- Test: `werkzeuge/kit_figur_test.gd` (Welt ohne Bild). Bilder: scratchpad/grossvater/bau/ (Skript /tmp/claude-0/gv_k2/shots.sh,
  Aufruf mit flock Slot 2; vorher einmal `godot --headless --import` im Worktree).

## Erledigt
- Kit-Grundlage, alle 12 Szenen von Kapitel 2 als Daten und spielbar (Kit-Test: 58 Prüfungen grün, 0 SCRIPT ERROR).
- Eigene Schlucht westlich der Hütte (Mitte -40/-40, man geht bachaufwärts nach Süden), Kunst-Durchgang 1 (Fels-Shader,
  Klettersteig, Gischt, warmes Licht). Nachtlager am Rand bei (-22, -9) (bergtal «frei», Biwak), Lias Zelt (-10, -16.5).
- Texte 5 Sprachen (rm mit «?» zum Korrekturlesen). Bilder PC / Handy / iPad hoch + quer in scratchpad/grossvater/bau.

## Polish + Probe-Paket (21.11. nachts)
- Film-Prüfung automatisch (kit_regie.gd pruef_shot, `{"action":"kit","do":"filmcheck"}`, im Kit-Test): jede Einstellung
  Motiv ≥ 15 % Bildhöhe, im Bild, kein Fels davor – alle 14 grün. Einstellungen neu gerahmt (Brücke von vorne tief,
  Rückblende beide am Steinmann mit Sepia/Vignette/Korn/Wischblende, Lia am Wasserfall, IR über MoveEye zum Felsen + Fuchs).
- Wand-Details (MultiMesh: Blöcke, Farn, Simse, Lärchen), IR-Lichtkegel, Startkarte (Rolle + Name, «Nina»), Ziel-Zeile nach
  Sprung (setzen mit sync), Laterne bei Lias Zelt, Brückenplanken ohne Lücke.
- Autostart: Datei `res://inhalte/grossvater_probe.json` ({"autostart": true}) NUR im Zweig `sim-grossvater-k2-probe`
  (nie zusammenführen), oder Startoption `--grossvater-neu`, Browser `?grossvater=1`. Tests mit --no-tour starten nie davon.
- Pakete: CI-Lauf 44848049125 auf sim-grossvater-k2-probe (Export Windows / Linux / Pi als Artefakte, Kit-Test grün);
  Web lokal exportiert: scratchpad/grossvater/paket/ (web-grossvater-k2-roh.zip = Godot-Export, sim-web-grossvater-k2.zip =
  Format des Webspace) – Stand 186039a (IR-Felsen noch am alten Ort).

## Test im normalen Simulator (Besitzer 21.11.)
- Kein Probe-Zweig mehr: der neue Modus ist im Zweig sim-grossvater-k2 Standard für Kapitel 2. Weg im Simulator:
  Schnellzugriff → SPIELEN → «Spielen» → Fenster «Spielen», Regal «Geschichten» → Karte «Die Karte des Grossvaters» →
  «▶ Kapitel 2 spielen (neu)» → Startkarte (Rolle, Name «Nina») → «Los geht's!». Alter Ablauf: «Weiterspielen» /
  «Neu beginnen» und der Schalter «Neuer Spielmodus (Probe)» auf der Kapitel-Seite.
- Windows lokal exportiert → scratchpad/grossvater/MoveEyeSim_Grossvater_Test.zip (nach jeder Runde neu, gleiche Datei).
- Führung (Besitzer blieb in Szene 3 hängen): Zielmarke an jedem Ziel, Kompass beim Maggie-Steuern Loch → Riegel,
  Hinweise nach 10/25 s, Loch mit dunklem Rand + Licht, Maggie läuft drüben selbst zum Riegel.

## Testkanal «sim-test» (Besitzer 21.11.)
- Knopf im Simulator: Mehr → Entwickler (nur Besitzer, Entwickler-Bereich an), ganz oben über den Reitern:
  «🧪 Neuste Testversion holen» und «⏪ Zur letzten Version zurück» (scripts/testkanal.gd). Holt sim-test.json, zeigt
  Commit / Datum / Grösse, fragt, lädt, prüft Grösse + SHA-256, sichert die laufende Datei als «<exe>.vorher» (eine
  Sicherung: die erste Nicht-Testversion bleibt), tauscht wie update.gd (_install) und startet neu. Titelleiste dann
  «Testversion: <commit>», das normale Update bietet nichts an (Hinweis «Testkanal aktiv»). Nie automatisch.
- Bauen: Workflow «Sim-Pakete» (sim_pi.yml) mit testkanal=true, Job «testkanal»:
  `gh workflow run sim_pi.yml --ref sim-grossvater-k2 -f testkanal=true -f ref=sim-grossvater-k2 -f label="Grossvater K2"`
  → Vorabversion https://github.com/DonElektro/MotionWatch/releases/tag/sim-test («Testversion (nicht signiert)»,
  prerelease, nie latest; Tag per GITHUB_TOKEN gesetzt / verschoben). Fasst versions.json / sim-X.Y.Z nie an.
- Auch ohne MoveEye (Besitzer fand das Entwickler-Fenster nicht – dev_area aus): dieselben Knöpfe unter Mehr → Updates
  (= Karte System → Updates), nur in «Experte» (in «Einfach» ein Hinweis), nie im Kinder-Modus.
- Test: werkzeuge/testkanal_test.gd (lokaler Server statt GitHub: Manifest, falsche Prüfsumme / Grösse, Sicherung, Zurück).
- Erste Runde: Lauf 44887699188, Commit a946844, Windows 54771814 B (sha256 1603b52b…), Linux 48822165 B; dieselbe
  Windows-ZIP liegt als scratchpad/grossvater/MoveEyeSim_Grossvater_Test.zip.

## Szene 6: Brückenkopf nicht erreichbar (Besitzer 21.11.)
- Ursache 1: die Führung (WEG) war EIN Weg für das ganze Kapitel und endete bei s 43 – ab Szene 5 zog sie die Figur
  überall zurück Richtung Wasserfallwand (am stärksten auf dem Weg zur Brücke). Jetzt: WEGE je Szene (kit_k2_daten.gd),
  das Lager am Rand ohne Führung.
- Ursache 2: Kompass und Marke zeigten auf die Brückenmitte – geradeaus steht man an der Kante des Wasserfall-Einschnitts.
  Jetzt: Schritt «ueber» (Plattenweg → Brückenkopf → Mitte), Hinweise nach 10/25 s; am Kopf eine breite Holzplattform,
  Trittsteine vom Seil-Ende her, zwei Laternen.
- «ort»-Ziele zählen nur auf ihrer Höhe (die Leiter-Stufe galt schon unten an der Wand).
- Nach 90 s ohne Fortschritt: Blinki-Hinweis + Pausenmenü «⏭ Zum nächsten Abschnitt springen».
- Test werkzeuge/kit_weg_test.gd: Raster-Modell (main.ground_y, keep_out, Wasser/Spalt, Stufe/Steilheit/Fallhöhe,
  Sprünge, Aktionen) sucht für JEDES Ziel aller 12 Szenen einen Weg; die echte Figur läuft die reinen Geh-Wege mit der
  Führung der Szene ab. Mit der alten Führung fällt Szene 6 durch.

## Kapitel 2 fertig für Sim 3.73.0 (Besitzer 21.11. nachmittags)
- [x] Bergtal-Fix sim-bergtal-bach (02f2b81) zusammengeführt.
- [x] Musik: 13 Kandidaten (CC BY) als 25-s-Vorschau → scratchpad/grossvater/musik/ – wartet auf Freigabe; Werkzeug
  werkzeuge/musik/ + Sim-Pakete auftrag=musik-vorschau|musik-ganz (läuft auf dem Runner, Ergebnis an sim-test).
- [x] Kamera: Federn statt lerp (Blickpunkt mit Vorlauf in Gehrichtung, Drehen hinter die Figur mit weich einsetzender
  Kraft, nicht bei Gehen auf die Kamera zu, Maus/Stick übersteuern, Federarm mit Hysterese, Höhe je Zustand).
- [x] Klettern: Hochziehen in Phasen (Hände an die Kante – Arm-Winkel aus der Kantenhöhe –, ziehen, Knie, stehen; Zeit nach
  Höhe), Stufen bis 0.6 m einfach hochsteigen (auch von selbst beim Gehen), Ausstieg oben an der Leiter gleich.
- [x] Grafik: Wände (gebogene Schichten, Kalkflächen, Risse, Moos in Fugen, AO aus der Form), Geröll, Brocken, Überhänge;
  Wasser-Shader (Fall mit Strähnen + Schaumfuss, Bach fliesst talwärts, Gumpen mit Wellen + Ringen), Nebel am Fallfuss;
  Licht ausgewogen (Filmic, Belichtung 0.95, kühleres Umgebungslicht, wärmere weichere Sonne); Figuren: Hut (Grossvater),
  Mütze (Toni), Zopf (Lia), runder Rucksack mit Trägern.
- [x] Stimmen: Piper/Thorsten (CC0) für Erzähler + Grossvater (tiefer), klang/stimmen/ (11 Dateien, 200 KB), nur Deutsch.
- [x] Musik gewählt (explore Lost Frontier, spannung Gathering Darkness, action Five Armies, entdeckung Epic loop);
  ganze Stücke 96 kbit/s → klang/sp_kit_<zustand>.ogg (klang.gd nimmt sie von selbst), Quellen in Über + LIZENZEN.
- [x] Web-Test Handy 390×844, iPad 820×1180 / 1180×820 (Playwright, Touch, Export «Web» lokal): läuft, Touch-Stick,
  Szene direkt per ?grossvater=1&name=Nina&k2szene=s06_bruecke; gefunden + behoben: das Demo-Fenster der Homepage lag über
  dem Spiel. Bildzeiten hier nicht aussagekräftig (Software-Grafik ~1 fps) → auf dem Gerät messen mit …&messen=1
  (Zeile oben links: fps, mittlere/längste Bildzeit, Lite).
- [x] Kamera am Brückenkopf (unteres halbes Bild verdeckt): Federarm mit mehr Luft unter der Sichtlinie + Felsbrocken als
  Hindernis + Nahgrenze; Test: Kamera am Start jeder Szene in 4 Richtungen frei (kit_weg_test).

## Übergabe an den Integrator – Sim 3.73.0 (Zweig sim-grossvater-k2)
- Inhalt: Kapitel 2 «Wo der Bach zweimal fällt» im neuen Modus (Standard für Kapitel 2; alter Ablauf über den Schalter
  «Neuer Spielmodus (Probe)»), Bergtal-Fix (sim-bergtal-bach zusammengeführt), Testkanal-Knöpfe (Mehr → Updates nur
  «Experte», Mehr → Entwickler) + Sim-Pakete testkanal/auftrag, Kamera, Klettern, Grafik, Stimmen, Musik.
- Neue Dateien im Paket: klang/sp_kit_*.ogg (4.7 MB Musik), klang/stimmen/ (0.2 MB), klang/kit_musik_quellen.json;
  export_presets.cfg: include_filter + klang/stimmen/*.ogg, klang/stimmen/*.json (alle Presets).
- Lizenzen: klang/LIZENZEN.txt (Musik CC BY mit Wortlaut, Stimmen CC0), «Lies mich.txt» Block MUSIK UND STIMMEN,
  Mehr › Über den Simulator › «Musik und Stimmen». «NEU IN 3.73.0» schreibt der Integrator (rel_sim.sh).
- Tests: kit_figur_test, kit_weg_test (neu: Erreichbarkeit aller 12 Szenen + Kamera), testkanal_test (neu),
  spielton_test (kit_* = Schleife), sim_texte --pruefen grün. CI-Lauf auf dem Zweig: siehe Bericht.
- Offen / bewusst nicht: Rumantsch der neuen Texte zum Korrekturlesen («?» in texte.json); Stimmen nur Deutsch;
  Figuren-Paket (Quaternius) wird im Kit nicht verlangt; die Testkanal-Vorabversion «sim-test» bleibt (nie latest).

## Als Nächstes
1. Separat (eigener Commit, NICHT mit dem Kapitel mischen): Bergtal `_carve_stream` vertieft bei jedem Schritt –
   Korrektur auf ~19 m, alle Nutzer des Bergtals prüfen und melden, was sich verschiebt.
2. Kunst: Figur mit mehr Silhouette (Mütze/Stirnband), Lia sichtbarer, Nacht am Lager etwas Licht (Stirnlampe / MoveEye-LED).
3. Feinschliff: Szenenübergänge ohne Sprünge (Lager: Weg aus der Schlucht), Sprecherstimmen (Piper) später.

## Hinweise
- tier_modell.gd «previously freed»-Fehler beim Simulator-Start gab es schon vorher (nicht angefasst).
- Xvfb-Bilder laufen mit 1–8 fps (Software-GL) – Zeiten in den Bild-Skripten grosszügig, auf Phase/fps warten.

## Phase 2 – Kapitel 1 «Die Karte» (Zweig sim-grossvater-k1, 21.11. abends)
- Daten: scripts/kit_k1_daten.gd (10 Szenen, Hütte Alp Tschuggen aus bergtal_orte.gd, Achse um die Hütte). Das Kit nimmt
  das Kapitel aus start({"kapitel": 1|2}); Knopf «▶ Kapitel 1» auf der Karte der Geschichte, Steuerung spielbereich
  story what=kapitel1.
- Neu (alles in kit_abenteuer.gd / kit_parcours.gd / kit_hud.gd, kit_figur.gd unverändert): Dachboden als Ebene (Böden
  nur oben, vor dem Hüttenboden), Decke für die Kamera (DECKEN) + Hauswände als Federarm-Hindernis, Stirnlampe (Funde nur
  im Lichtkegel), Ofen (Licht, Rauch), Rucksack 3 von 6 (Spielstand «k_rucksack»), Maggie holt (maggie_such), Murmeltier,
  Kartenbild halb/ganz, Abzeichen «Stöberer».
- Test werkzeuge/kit_k1_test.gd: das ganze Kapitel gespielt (Figur geht über Stick-Eingabe, Leiter, Lampe, Wahl, Maggie)
  + Kamera am Start jeder Szene und im Dachboden. Stimmen: Kapitel 1 dazu (22 Dateien); Lia (kerstin, CC0) im Werkzeug.

## Phase 2 – Kapitel 3 «Der Seeblock» (Zweig sim-grossvater-k3, 22.11.)
- Daten: scripts/kit_k3_daten.gd (11 Szenen). Ort: Südufer des Gumpisees (bergtal LAKE1), Achse am Ufer (s = −x, q = −z − 300).
  Szene 1 am leeren Zelt von Kapitel 2, dann Blende an den See. «top_see» / «h_see» / «blick_see» / «ziel_see» / «y_see» =
  Höhen über dem Seespiegel (Steine im Bachdelta, Kamera und Lia über dem Wasser).
- Neu in scripts/kit_k3.gd (eigene Datei; kit_abenteuer.gd hängt sie nur ein, kit_figur.gd unverändert):
  Duftspur (Wolken verblassen beim Trödeln, Aktion = Maggie schnüffelt neu, Abzeichen «Spürnase»), Floss aus drei Stämmen
  (Stick relativ zur Kamera, Bojen, Windböen mit Warnbalken – Aktion im richtigen Moment = gehalten; vom Kurs = zurück zur
  letzten Boje; Abzeichen «Kapitän»), Seeblock mit Steg, Riss (Zeichen aus Kapitel 2), drei Marken unter Moos, Kiste mit
  Zahlenschloss (drei Rädchen mit Zeichen; Tasten, Maus, Touch), Lias Fussspuren, Feuer am Ufer.
- Kamera: der Seeblock hält die Kamera fern (Kugeln wie die Felsen der Schlucht); pruef_shot prüft jetzt auch Wände (line_blocker).
- Test werkzeuge/kit_k3_test.gd: das ganze Kapitel wie ein Spieler (Stick + Springen über die Steine, Kante, Floss mit Stick
  relativ zur Kamera und Aktion bei den Böen, Schloss erst falsch, dann richtig), jede Filmeinstellung, die Kamera an allen
  Szenenstarts + Steinen + Steg (8 Richtungen), Duftspur verloren / neu, Floss vom Kurs.
- Lias Zelt (art «zelt», auch Kapitel 2): stehendes Firstzelt (Prisma), offen und leer; der Test prüft die Höhe.
- Für das Finale (Kapitel 5, Sonnenaufgang): Haken des Frei-erkunden-Helfers beim Abschluss aufrufen –
  main.explore.startpunkt_melden("grossvater_grat", T.t("Grat beim Sonnenaufgang"), "bergtal", welt_pos, heading).

## Phase 2 – Kapitel 4 «Nebel im Couloir» (Zweig sim-grossvater-k4, 22.11.)
- Daten: scripts/kit_k4_daten.gd (12 Szenen). Ort: ein Couloir am Osthang über dem Gumpisee (kit_schlucht.gd, SCHLUCHT),
  Achse s = x − 138 (hinauf nach Osten), oben auf der Schulter das alte Biwak (DECKEN: Kamera unter dem Dach).
- Neu in scripts/kit_k4.gd (kit_abenteuer.gd lädt je Kapitel kit_k<n>.gd mit denselben Haken; kit_figur.gd unverändert,
  verträglich mit explore_person.gd): Nebel (eigene Dichte nach dem Nebel-Tick von bergtal.gd), Wärmebild (Bildschirm in
  kalter Palette, warme Körper leuchten durch den Nebel), Peilung (nur Kompass, kein Leuchtpunkt, Kurs in Grad), Seilschaft
  (Haken einhängen vor dem Klettern, Lia sichert von Stand zu Stand, sichtbares Seil), Stahlseil-Querung (ohne Umhängen
  kein Weiterkommen), Steinschlag mit QTE, Maggie im Rucksack, das Biwak mit dem Buch; Abzeichen «Seilschaft».
- Test werkzeuge/kit_k4_test.gd: das ganze Kapitel wie ein Spieler, alle Filmeinstellungen, Kamera an allen Szenenstarts,
  auf den Stufen, am Stahlseil und im Biwak (unter dem Dach).
- Nach der Durchsicht (22.11.): im Biwak eine feste Eckkamera an der Türwand (Regal und Buch im Bild) statt der
  Folgekamera von oben; Szene 12 eine echte Nacht (der Himmel wird nachgeführt - main tut es während des Abenteuers nicht -,
  Sterne und Milchstrasse, ohne Tagesdunst, Kerze im neuen Fenster und in der Tür, zuerst ein Blick zu den Sternen);
  Steinschlag mit Lia und den Steinen im Bild; keine Filmeinstellung steiler als 22° (Test); Rollen-Test Biwakbuch und
  Rückblende (Tochter / Sohn: 2000 und «Vater», Enkelin / Enkel: 1974 und «Grossvater», auch die Stimme).

## Kapitel um Kapitel, Kapitelwähler, Startadresse (22.11.)
- kit_abenteuer.gd KAPITEL_FERTIG = [1, 2, 3, 4]: die fertigen Kapitel für den Wähler, die Kette und die Startseiten-Kachel.
- Am Ende eines Kapitels: «Kapitel N geschafft – weiter mit Kapitel N+1 …», 5 s Countdown, «Weiter ›», «Zurück zum Menü»;
  Held, Name, Rolle bleiben (der Held ist im Spielstand gespeichert: k_held), der Rucksack (k_rucksack) auch. Nach dem
  letzten fertigen Kapitel das Ende des Kapitels («Fortsetzung folgt»). Tests einzelner Kapitel: Start mit "kette": false.
- Geschichten-Karte: «▶ Ganzes Spiel ab Kapitel 1» und «Kapitel 1 … 4». Ohne gespeicherten Helden zuerst die Heldenwahl.
- Browser: ?grossvater=1 = der Kapitelwähler, ?grossvater=1&kapitel=N = gleich Kapitel N (die alte Adresse ?grossvater=k2 =
  Kapitel 2); Startoptionen --grossvater-neu und --grossvater-kapitel=N; Steuerbefehl {"action":"kit","do":"grossvater"}
  (ohne kapitel: der Wähler), {"do":"kapitel_liste"}.
- Test werkzeuge/kit_kette_test.gd.

## Die Bewegungen von «Frei erkunden» im Abenteuer (22.11.)
- scripts/figur_haltung.gd: EIN Ablauf für explore_person.gd und kit_abenteuer.gd - C / ✚ ↓ / grüner Knopf: stehen →
  geduckt → kriechen; X / ✚ ← sitzen, Z / ✚ → liegen; waten und schwimmen; V / R3 die Ansichten (hinter dir, aus den Augen,
  von oben); Rennen mit dem Schnelllauf des Erkundens (Entwickler-Schalter), im Abenteuer nie langsamer als normal.
- Überall erlaubt ausser im Film, beim Klettern / Hangeln / Balancieren, beim Steuern von Maggie, auf der Karte und auf dem
  Floss (kit_k3.gd haltung_erlaubt). Das Wasser eines Rätsels (Parcours «wasser»: Bach, der See um den Seeblock) bleibt
  wie es ist: zurück zum letzten Punkt - schwimmend wird kein Rätsel übersprungen. Die Folgekamera schaut bei tiefer
  Haltung tiefer (kit_regie.gd ziel_figur über kit.kopf_hoehe()).
- Test werkzeuge/kit_haltung_test.gd.
