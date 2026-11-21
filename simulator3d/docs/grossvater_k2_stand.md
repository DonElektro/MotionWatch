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

## Als Nächstes
1. Separat (eigener Commit, NICHT mit dem Kapitel mischen): Bergtal `_carve_stream` vertieft bei jedem Schritt –
   Korrektur auf ~19 m, alle Nutzer des Bergtals prüfen und melden, was sich verschiebt.
2. Kunst: Figur mit mehr Silhouette (Mütze/Stirnband), Lia sichtbarer, Nacht am Lager etwas Licht (Stirnlampe / MoveEye-LED).
3. Feinschliff: Szenenübergänge ohne Sprünge (Lager: Weg aus der Schlucht), Sprecherstimmen (Piper) später.

## Hinweise
- tier_modell.gd «previously freed»-Fehler beim Simulator-Start gab es schon vorher (nicht angefasst).
- Xvfb-Bilder laufen mit 1–8 fps (Software-GL) – Zeiten in den Bild-Skripten grosszügig, auf Phase/fps warten.
