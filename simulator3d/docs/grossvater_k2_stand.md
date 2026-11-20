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
- Kit-Grundlage, Szenen 1–5 als Daten, eigene Schlucht westlich der Hütte (Mitte -40/-40, man geht bachaufwärts nach Süden).
- Erste Bilder an Koordinator gemeldet (alter Ort im Bach-Graben, 7d8757a).

## Als Nächstes
1. Kit-Test grün, Bilder 1280×720, 390×844, 820×1180, 1180×820 (Touch) ansehen und verbessern.
2. Szenen 6–12 bauen (Brücke über die Schlucht bei s 50–58, Steinmann, Rückblende, Funde, Lia, Nachtlager, Cliffhanger).
3. Texte in i18n/texte.json (sim_texte.py) + Übersetzungen.
4. Danach separat (eigener Commit): Bergtal `_carve_stream` vertieft bei jedem Schritt – alle Nutzer prüfen und melden.

## Hinweise
- tier_modell.gd «previously freed»-Fehler beim Simulator-Start gab es schon vorher (nicht angefasst).
- Xvfb-Bilder laufen mit 1–8 fps (Software-GL) – Zeiten in den Bild-Skripten grosszügig, auf Phase/fps warten.
