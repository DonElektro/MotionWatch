# Übergabe: Motion Watch 3D-Simulator

Stand: 31.10.2026 · Version **3.15.0** · MoveEye **3.15.0** (ab 3.0.0 eine gemeinsame Nummer; vorher Simulator 3D-4.85 / MoveEye 2.98.116)

Diese Datei ist der Startpunkt für einen neuen Chat, der den 3D-Simulator weiter ausbaut.

## NEU in 3.15.0 (MoveEye 3.15.0): Maggie sieht aus wie Daniels Hund

- `maggie_hund.gd` `_maggie_koerper()`: baut Maggie nach der Grundform «dog» neu (andere Hunde unverändert): schlank,
  hochbeinig (Schulter ≈ 31 cm), Beine mit Gelenk (`legs[i][2]`), feste Kippohren, Schwanz aus 3 Teilen nach oben gebogen,
  Farben fest (Liste im Kopf der Datei: WEISS, BRAUN, NASENR, NASE, AUGE, GLANZ; 6 Materialien über `m.mat()`).
  Schnittstelle bleibt: `body_root` (scale 0.6, innen Knoten `maggie_koerper` in Metern), `head`, `tail`, `legs`.
  `freuen(sek)`: wedelt kräftig (Rätsel gelöst/Fund, Graben-Erfolg, Kristall); sonst läuft der Schwanz leicht mit.
  `_schwanz()` senkt beim Laufen den Körper um die Höhe der tiefsten Pfote (Pfoten bleiben am Boden).
- `actor.gd`: neues Feld `tail_wag` (≥ 0 = Ausschlag von aussen, −1 = wie bisher; nur Maggie setzt es).
- `zwei_bausteine.gd`: die übrigen Emoji (📸 🙌 💎) durch Text ersetzt.

## NEU in 3.14.0 (MoveEye 3.14.0): Geheimnisse und Action im Grossvater-Abenteuer

- `abenteuer_geheim.gd` (neu, `bergtal_abenteuer.gd` `geheim`): Steinmännchen mit Geheimwort, doppelter Boden, Licht auf der
  Nachtaufnahme, Nacht-Geräusche mit «Wer war es?»; `abenteuer_action.gd` (neu): ein Action-Teil pro Kapitel. Steht neben den
  Team-Bausteinen von 3.13 (Kapitelseite und Lager: beide). `devtool.gd`, `devtool_kontakt.gd`.
- `zwei_bausteine.gd`: Kategorie-Emoji (💎 🐾 🗿 👣 📖 📸 🤝) durch übersetzten Text ersetzt (Godot-Standardschrift ohne Emoji).

## NEU in 3.13.0 (MoveEye 3.13.0): Team-Bausteine zu zweit (`zwei_bausteine.gd`)

- `zwei_bausteine.gd` (neu, zehn Bausteine), `abenteuer_zwei_team.gd` (Karte des Grossvaters), `maggie_zwei_team.gd` (Maggie);
  eingehängt in `abenteuer_zweit.gd`, `bergtal_abenteuer.gd`, `maggie_zwei.gd`, `maggie_story.gd`.
- Konzept-Check: 🎮 in `abenteuer_zwei_team.gd` durch Text «(Controller)» ersetzt; die Kategorie-Zeichen 💎 🐾 🗿 👣 📖 in
  `zwei_bausteine.gd` sind noch Emoji (ob die Schrift sie hat, offen).

## NEU in 3.12.0 (MoveEye 3.12.0): Blinki ohne Sichtfächer

- Simulator `mehr_icons.gd`, `tour.gd`, `gamemore.gd`: Blinki ohne orangen Kegel, Stimmungszeichen (Ecken, Pfeil, Herz, Punkte)
  kurz in einer Sprechblase; MoveEye 589_blinki.py und 635_uebersetzungen_blinki.py ebenso. Logo und Fensterkopf unverändert.

## NEU in 3.11.1 (MoveEye 3.11.1): OSM-Kacheln wieder sichtbar (nur MoveEye)

- Simulator-Code unverändert. MoveEye 530 / 540: Kachel-Bilder mit `referrerPolicy = "origin"` (die Seiten bleiben
  `Referrer-Policy: no-referrer`, 550) – OSM blockiert Kacheln ohne Referer («Access blocked … 403»).

## NEU in 3.11.0 (MoveEye 3.11.0): Maggie zu zweit (`maggie_zwei.gd`, `zweit_bild.gd`)

- `maggie_zwei.gd` (neu): 1 oder 2 Spieler, Rolle (zwei Wanderer / Spieler 2 ist Maggie), Teamrätsel je Region, Partner rettet;
  `zweit_bild.gd` (neu): Bildschirm geteilt / gemeinsam; `maggie_story.gd`, `maggie_hund.gd`, `geschichten.gd`, `padmap.gd`
  (Controller von maggie_zwei, ausserhalb des mit MoveEye 542 verglichenen JS-Blocks).
- Konzept-Check: `abenteuer_zweit.gd` ohne die Emoji 🎮 / ⌨ (Text «Controller» / «Tastatur», wie maggie_zwei).

## NEU in 3.10.1 (MoveEye 3.10.1): Vorführung – «Spiel-Knöpfe zeigen»

- `maggie_vorfuehrung.gd`, `devtool_vorfuehrung.gd`: Schalter «Spiel-Knöpfe zeigen» (ab Werk aus), die Knöpfe bleiben sichtbar
  und leuchten beim Druck des Autopiloten auf; `maggie_story.gd`, `schnittstelle.json`.

## NEU in 3.10.0 (MoveEye 3.10.0): Vorführmodus «Maggie»

- Simulator: Vorführung (Entwickler) – Maggie spielt sich selbst (ganz ≈ 2 h / Kurzfassung ≈ 15 Min.), Kamerawechsel,
  Untertitel, Erzählerstimme, eigener Spielstand, Autopilot meldet Hänger; neue /control-Aktion (schnittstelle.json 34).
  MoveEye: Teil `639m_vorfuehrung.py` (Vollbild /sim/vorfuehrung im Browser, Steuerung Pause/Kapitel).
- Erste zweistellige Mittelzahl: 3.10.0 > 3.9.x überall numerisch geprüft (versionen.py/gd, sim_vkey, Web vnum, sort -V).

## NEU in 3.9.2 (MoveEye 3.9.2): Start-Absturz behoben (Foto-Inhalte)

- `inhalte.gd`: Foto-Inhalte erst anwenden, wenn die Welt steht (vorher während der Update-Suche → Absturz unter Windows);
  Absturz-Schutz beim Einlesen (nächster Start ohne Fotos, Hinweis in der Statuszeile); `main.gd` Startoption `--no-inhalte`;
  `fauna.gd`.

## NEU in 3.9.1 (MoveEye 3.9.1): Diebstahl-Kartenlink, überall «Mover»

- MoveEye: Kartenlink vollständig in jeder Diebstahl-Meldung, Sabotage mit letzter GPS-Position (635b, 579a), «Mover» in
  Web/Fenster/Übersetzungen (538, 542, 549, 597, 600, 623, 628). Simulator: `padmap.gd`; Spielart «Verstecken mit dem Mover»
  (`gamewiz.gd`, `main.gd`, `game.gd`, Übersetzungen) – interne Schlüssel (`seek`, `rover`) unverändert.

## NEU in 3.9.0 (MoveEye 3.9.0): Hospiz – Knopf «Ohne Passwort starten», eine Regel für alle Wege

- `bergtal_horror.gd`: eine Prüfung für Passwort / Knopf am Simulator (auch «Weiterspielen» über /control, Kapitel-Sprung),
  Knopf «Ohne Passwort starten» (nicht im Kinder-Modus, Warnung und Widmung bleiben); `geschichten.gd`, `net.gd`,
  `devtool_kapitel.gd`. Tests: `werkzeuge/hospiz_test.gd` (headless, in der Release-Kette), `werkzeuge/hospiz_test.py` (live).

## NEU in 3.8.0 (MoveEye 3.8.0): MoveEye-Datei verkleinert (Zusatzdatei)

- MoveEye: grosse Literale in `moveeye_daten_X_Y_Z.zip` (bauen.py, Teile 012 / 397), Brücke 3.0.2 dauerhaft (`"bridge": true`),
  versions.json mit signiertem `"data"`-Eintrag. Simulator: `mwpc.gd` – der Prüfstand kopiert die ZIP neben der .py mit.

## NEU in 3.7.1 (MoveEye 3.7.1): Maggie – Pfeil und Dauer

- `maggie_story.gd`, `maggie_hund.gd`, `maggie_welt.gd`, `maggie_helfer.gd`, `maggie_gefahr.gd`: Pfeil zeigt auf die Stationen,
  pro Region 3 Rastplätze und 4 Rätsel (≈ 25–28 Min.), Rastplatz-Anzeige, Tipps verschwinden wieder. Spieltest-Haken erhalten.

## NEU in 3.7.0 (MoveEye 3.7.0): Simulator-Menüs aufgeräumt (Menü A)

- `main.gd` (Bedienfeld): «Einfach» 61 statt 101 Einträge, Besuch → Menschen / Tiere mit Unterkarten, doppelte Regler
  zusammengelegt (Tropfen, Scheinwerfer, Jahreszeit, Tagesablauf), Prüfstand und Rückmeldung nur an einem Ort, «Mover» /
  «Patrouille» einheitlich, ein Testen-Symbol, Foto-Regler grau ohne Foto; alte Steuerbefehle bleiben. Dazu `toolbar.gd`,
  `quick.gd`, `mehr.gd`, `kids.gd`, `fotomodus.gd` u. a.; MoveEye 139, 470, 540.

## NEU in 3.6.2 (MoveEye 3.6.2): Fehlerkorrekturen MoveEye (nur MoveEye)

- Simulator-Code unverändert. MoveEye: 060, 130, 139, 180, 232 (`thermal_ai_checked`, Signatur `veto=(), ai=None` neben
  E1 `thermal_vehicle_step`), 410, 417, 635a, 635b, 639i; `bauen.py` bricht über 8 MiB ab und warnt ab 7,5 MiB.

## NEU in 3.6.1 (MoveEye 3.6.1): Sicherheit und Fehler im Simulator

- `net.gd`: gefährliche /control-Befehle (werk reset, spieltest clear, set_password) und /dev/… nur von diesem PC oder vom
  verbundenen MoveEye (sonst `--fernsteuerung-offen` / `MWSIM_FERNSTEUERUNG_OFFEN=1`). Hospiz-Rätsel und Maggie-Bild pro
  Spielstand (`spielstand.gd`, `horror_raetsel.gd`, `geschichten.gd`), Kapitel-Sprung ohne echten Spielstand
  (`devtool_kapitel.gd`). `werk.gd`: sicherer Neustart, `KEEP_COPIES` 3, `parcours/lernbilder/` in KEEP.

## NEU in 3.6.0 (MoveEye 3.6.0): Feste Fehl-Personen (nur MoveEye)

- Simulator-Code unverändert. MoveEye: neue Teile `418_feste_fehlperson.py` (Personen-Kasten, der sich nie bewegt → Karte
  «ignorieren?», Kopf folgt nicht; warme Motoren keine Person; KI-Tier bleibt Tier), `599f_fenster_fehlperson.py`,
  `639l_uebersetzungen_fehlperson.py`; 232, 410 (`veto_` neben dem Kriech-Block von 418k), 550.

## NEU in 3.5.0 (MoveEye 3.5.0): Kriechende nachts, KI-Lupe weit (nur MoveEye)

- Simulator-Code unverändert. MoveEye: neue Teile `418k_kriechende_nacht.py` (Voralarm «⚠ Etwas Grosses am Boden», nach 6 s
  «Person? (kriecht)»; Fuchs/Igel nicht), `418z_ki_zoom_weit.py` (KI-Lupe auch für kleine, weite Bewegungen, nicht bei
  starkem Wind), `639x_uebersetzungen_kriechende.py`; 180, 410.

## NEU in 3.4.0 (MoveEye 3.4.0): Nebel-Modus und Dämmerung/Wind (nur MoveEye)

- Simulator-Code unverändert. MoveEye: neuer Teil `411_nebel_daemmerung.py` (Nebel erkennen, Kontrast, mehr Wärmebild,
  Hinweis «🌫 Nebel», kein «Kamera verdreht» im Nebel; Dämmerung/Wind: 2–3 Treffer in Folge), `639k_uebersetzungen_nebel.py`;
  060, 066, 180, 232, 410, 530, 540, 570.

## NEU in 3.3.0 (MoveEye 3.3.0): Roter Faden (`geschichten_faden.gd`)

- `geschichten_faden.gd` (neu): die beiden Geschichten kennen sich (Ruedi, Anna, Sepp, Vrenis Käse, Wanderbuch im Finale,
  Kapelle auf der alten Karte), Abzeichen «Beide Geschichten geschafft». Stand pro Spielstand in
  `user://spielstand/<n>/faden.json`, dazu Maggies eigene Datei dieses Platzes (`spielstand.gd path_maggie`).

## NEU in 3.2.0 (MoveEye 3.2.0): Statisten (`statisten.gd`)

- `statisten.gd` (neu): Hintergrund-Leute mit Zielen (Bank, Brunnen, Hütte, Aussicht), Tätigkeiten, Gruppen, grüssen,
  weichen aus, gehen abends heim (bei Regen schneller), halten in Spielmodi Abstand zu Rätseln und Gefahren
  (`bergtal_abenteuer.gd`); Menge wenig / normal / belebt. `actor.gd`, `figur_paket.gd`, `main.gd` angepasst.

## NEU in 3.1.0 (MoveEye 3.1.0): Kurze Push-Nachrichten (nur MoveEye)

- Simulator-Code unverändert. MoveEye: neuer Teil `635b_push_kurz.py` (ein Aufbau für alle Meldungen: Titel mit Symbol,
  eine Zeile, Bild; «🛡 Schutz ein»; im Simulator nur Alarme, Info per Schalter unter Push → Erweitert), 060, 130, 531a, 571a.

## NEU in 3.0.2 (MoveEye 3.0.2): Angleichungen

- `main.gd`: «Nur Gruppen» wie in MoveEye (Gruppen offen, Themen zu). `abenteuer_figuren_daten.gd`: Anna ist Betreuerin der
  Hütte, Sepp spricht passend zur gewählten Jahreszeit.

## NEU in 3.0.1 (MoveEye 3.0.1): Lektorat der Geschichten-Texte

- Texte in `maggie_*.gd`, `bergtal_abenteuer*.gd`, `abenteuer_figuren_daten.gd`, `bergtal_erleben_b.gd`, `entdecken.gd`,
  `spielbereich.gd` und `i18n/texte.json` überarbeitet; Titel überall «Die Karte des Grossvaters».

## NEU in 3.0.0 (MoveEye 3.0.0): Gemeinsame Versionsnummer

- MoveEye und MoveEye Sim haben ab jetzt dieselbe Nummer X.Y.Z (neue Funktion = Y+1, Fehlerkorrektur = Z+1). `version.json`
  mit Brücke `"version": "3D-5.0.0"` + `"ver": "3.0.0"` (geschrieben mit `werkzeuge/versionen.py --sim-json`).

## Versionsnummern (Paket «Versionierung 3.0.0», umgestellt mit dem Release 3.0.0)

Ab **3.0.0** haben MoveEye und der Simulator **dieselbe Nummer** («MoveEye 3.0.0» / «MoveEye Sim 3.0.0») und werden immer
zusammen veröffentlicht; `VERSION` in `scripts/main.gd` ist dann `"X.Y.Z"` (vorher `"3D-A.B"`). Vergleich und Anzeige nur
über `scripts/versionen.gd` (`key`, `newer`, `label`, `legacy`). **Brücke:** alte Simulatoren (bis 3D-4.8x) lesen in
`version.json` nur `version` – dort steht darum `3D-(X+2).Y.Z` (3.0.0 → `3D-5.0.0`), die echte Nummer in `ver`.
`version.json` nur mit `python3 werkzeuge/versionen.py --sim-json X.Y.Z "Notiz"` schreiben, danach `--pruefen`.
Regeln und Ablauf: CLAUDE.md, Abschnitt «Versionierung».

## NEU in 3D-4.85 (MoveEye 2.98.116): Fenster «Spielen» mit Geschichten (`geschichten.gd`)

- `geschichten.gd` (neu): Regal mit Geschichten-Karten (Die Karte des Grossvaters = Bergtal-Abenteuer, Maggie, Hospiz nur
  Besitzer mit Schloss, Teil 2 gesperrt), gleicher Start (Spielstand → Figur → Schwierigkeit/Jahreszeit); `spielbereich.gd`
  mit Kopfzeile Stufe/Spielstand/Weiterspielen und «Entdecken»; Abzeichen im Entdeckungsbuch (`entdecken.gd`).
- MoveEye: Reiter «Spielen» gleich aufgebaut (639i, 139; Bild `/sim/story_pic`), `net.gd`/`schnittstelle.json` angepasst.

## NEU in 3D-4.84 (MoveEye 2.98.115): «Beim Start: Nur Gruppen» (MoveEye und Simulator)

- `main.gd`: Einstellungen öffnen beim Start in «Nur Gruppen», Schalter «Beim Start: Nur Gruppen» (ab Werk ein); aus =
  die eigenen auf-/zugeklappten Menüs kommen zurück.
- MoveEye: Schalter `ui_start_groups` (020, 530, 470, 550, 570), neuer Teil `639j_nurgruppen.py` (Übersetzungen,
  Anleitung); Pi-Fenster: drei Aufklapp-Knöpfe in Reihenfolge und Symbolen wie im Web.

## NEU in 3D-4.83 (MoveEye 2.98.114): Werkseinstellungen (`werk.gd`)

- `werk.gd` (neu): Mehr → «⚠ Auf Werkseinstellungen zurücksetzen …» (nur Besitzer, Wort wie MoveEye FACTORY_WORDS), Kopie
  nach `user://werk_kopie/`, Löschen beim nächsten Start in `main._ready` (apply_pending). `KEEP` behält u. a.
  Horror-Passwort (nur Hash), `simulator_sprache.json` (wie MoveEye), heruntergeladene Inhalte, Entwickler-/Prüfdaten.

## NEU in 3D-4.82 (MoveEye 2.98.113): Abenteuer A6 (`spielstand.gd`, `abenteuer_stimme.gd`, `abenteuer_blinki.gd`)

- `spielstand.gd` (neu): 3 Familien-Spielstände, Autosave an Hütte und Lager, «Weiterspielen»; gemeinsames Level für
  Abenteuer, Spielbereich und Entdecken (`entdecken.gd`, `spielbereich.gd`).
- `abenteuer_stimme.gd` (neu): Tagebuch vorlesen (TTS) – `project.godot` `[audio] general/text_to_speech=true`.
- `abenteuer_blinki.gd` (neu): Blinki-Tipps. `bergtal_abenteuer.gd`: Kamerafahrt beim Kapitelstart, Jahreszeit wählbar,
  Kinder-Modus (Leicht, keine Gefahren, kein Hunger), Seite zu Teil 2 nach Kapitel 5.

## NEU in 3D-4.81 (MoveEye 2.98.112): Kleidung nach Jahreszeit (`kleidung.gd`)

- `kleidung.gd` (neu, `stufe(main)`): Winter / Nacht / Berg / Regen → lang mit Jacke, Sommer gemischt. `waerme.gd`
  `cloth_level(amb, variant, stufe)` und Haut wärmer als Stoff; `figur_paket.gd` ohne durchscheinende Beine; `actor.gd`,
  `figur.gd`, `menschen.gd`, `simreal.gd` angepasst.

## NEU in 3D-4.80 (MoveEye 2.98.111): Ein «Entwickler» (`devtool_schalter.gd`)

- `devtool_schalter.gd` (neu): Reiter «Schalter» im Fenster Mehr → Entwickler (Prüfstand, Störungen testen, Diagnose-Paket).
  Die Bedienfeld-Karte «Entwickler» (`main.gd`) öffnet nur noch dieses Fenster; Spieltest-Schalter nur noch einmal
  (`spieltest.gd`, `devtool_extra.gd`, `mehr.gd`).

## NEU in 3D-4.79 (MoveEye 2.98.110): «Maggie und der Bergkristall» (`maggie_*.gd`)

- `maggie_story.gd` (Rahmen, `main.maggie`), `maggie_welt.gd` (4 Regionen), `maggie_hund.gd` (S2: Maggie, Rätsel),
  `maggie_gefahr.gd` (S3: böse Tiere, Gruppe `maggie_boese`), `maggie_helfer.gd` (Eule, Steinbock, Murmeltier, Fuchs).
- `main.gd`: `spieltest` und `maggie` werden nebeneinander angelegt.
- Spieltest-Haken (`Spieltest.ereignis("maggie", …)`): `start` + `ort` (Region gestartet), `ende` (Region fertig),
  `erwischt`, `fortschritt` (Rätsel gelöst, maggie_hund), `hilfe` (Eule). Kein `tipp`: Maggie hat keinen Tipp-Knopf, und
  `story.tipp()` zeigt alle Hinweise (auch Erfolgsmeldungen) – das würde falsch zählen.

## NEU in 3D-4.78 (MoveEye 2.98.109): Kamera für Sprung und Kontaktbogen (`devtool_kamera.gd`)

- `devtool_kamera.gd` (neu): sucht freie Sicht (eigene Strahlen gegen Gelände, Wasser, Dinge), Augenhöhe, bevorzugte
  Blickrichtung der Aussichtspunkte; Lite über `Quality.lite()` (keine eigene Abfrage mehr). Eingebunden in `devtool.gd`
  und `devtool_kontakt.gd`. 38 von 55 Problem-Orten gut, Schluchten bleiben schwierig.
- `i18n/texte.json`: Suchwort «höhle» aus `DEEP` (kein sichtbarer Text) mit Übersetzung, damit sim_texte 0 Lücken meldet.

## NEU in 3D-4.77 (MoveEye 2.98.108): Spieltest-Assistent (`spieltest.gd`, `devtool_spieltest.gd`)

- `spieltest.gd` (neu): beobachtet alle Spielmodi, Smiley-Frage nach jeder Runde, Vorschläge, «ZIP für Claude»;
  Entwickler → Spieltest (`devtool_spieltest.gd`, `devtool_extra.gd`). world_reply «spieltest» (schnittstelle.json, 37 Felder).
- MoveEye `quelle/635a_spieltest.py` (neu, 350): Spieltest-Meldungen über den Haupt-Push, nur mit Schalter (Standard aus).

## NEU in 3D-4.76 (MoveEye 2.98.107): Weltfehler Bergtal, Rest (K3)

- `bergtal.gd`, `bergtal_orte.gd`, `bergtal_erleben_a/b.gd`, `bib_berg.gd`, `bib_objekte.gd`, `scenes.gd`, `kompakt_dorf.gd`,
  `shaders/bergtal_boden.gdshader`: Innenräume ohne Gras/Bäume, Sennerei mit Dach, keine Geländelöcher, Steinbrücke, runde
  Tarnwiese, Arvenhain, Herbstblumen, Gletscherspalten und Felsen auf dem Boden. K2 (`_roads_and_trails`, `_road_flatten`)
  unverändert.

## NEU in 3D-4.75 (MoveEye 2.98.106): Abenteuer-Pakete verbunden (A1–A5)

- `abenteuer_bestenliste.gd` mit A1 verbunden (Wertung, Sammlung, Wildkamera – keine Stubs mehr), A4-Tausch nach den
  A2-Wunschlisten, Wildhüter-Aufträge erkennen A1-Fotos.
- Entscheid Daniel: nur Grossvaters Feldstecher; Seil / Ersatzteil je ein Fundort (zweiter nur auf Leicht); Hilfe-Stufe (A3)
  = Schwierigkeit (eine Wahl), auf Mittel «Tipp jetzt».

## NEU in 3D-4.74 (MoveEye 2.98.105): Weltfehler Bergtal / Pfadilager (`bergtal.gd`, `kompakt_pfadi.gd`)

- `bergtal.gd`: Passstrasse auf dem Gelände (runde Kehren, nichts schwebt), Bergdorf auf Strassenhöhe, ebene Parkplätze.
- `kompakt_pfadi.gd`: keine Tanne mehr vor MoveEye beim Standort Zelte.

## NEU in 3D-4.73 (MoveEye 2.98.104): MoveEye im Abenteuer (`abenteuer_moveeye.gd`, Paket A1)

- `abenteuer_moveeye.gd` (neu, `bergtal_abenteuer.gd` `a1`): Lager bewachen / Wildkamera am Wildwechsel, Fuchs am Proviant,
  Hinweis-Aufnahme (Licht am Berg), Aufnahmen auswerten, Sammlung 7 seltener Tiere, `foto_wertung()`; Luchs in `bergtal.gd`,
  Murmeltier/Steinadler/Bartgeier in `waerme.gd`. Steht neben A2 `a2`.
- MoveEye 579b `NACHT_CAUSES` + 599e: neue Ursachen lynx/ibex/marmot/eagle/vulture/light und die älteren chamois/cow/hare/
  stoat/deer/rockfall/storm mit Übersetzungen (vorher roh angezeigt).
- Offen: `abenteuer_bestenliste.gd` (A5) nutzt für Tiere, Foto-Wertung und Wildkamera noch die Stubs (TODO A1).

## NEU in 3D-4.72 (MoveEye 2.98.103): Leben im Ferienpark (`ferienpark_leben.gd`)

- `ferienpark_leben.gd` (neu): Tagesablauf nach Uhrzeit (Grillabend mit Glut im Wärmebild, WC-Gänge, Jogger, Bäcker) und
  3 Aufgaben mit MoveEye (Kind finden, Velo-Dieb, Zeltwache) unter Spiel → Entdecken (Experte).
- `erlebniswelt.gd`: der Rahmen-Abgleich ist jetzt gemeinsam (Erlebnisse und Ferienpark-Aufgaben); `ferienpark.gd`,
  `szenenplus.gd`, `waerme.gd`, `main.gd` angepasst.

## NEU in 3D-4.71 (MoveEye 2.98.102): Tiere im Schlafzimmer (`zimmertiere.gd`)

- `zimmertiere.gd` (neu): Hamster im Laufrad, Wellensittich im Käfig, Hauswinkelspinne (Wand/Decke, seilt sich nachts vor
  die Linse ab); `lens.gdshader` neuer Block `spider` (Uniform `spider`, 0 = Block übersprungen); Wärme in `waerme.gd`.

## NEU in 3D-4.70 (MoveEye 2.98.101): Figuren, Gespräche, Nebenaufgaben (`abenteuer_figuren.gd`, `_daten`)

- `abenteuer_figuren.gd` / `abenteuer_figuren_daten.gd` (neu, `bergtal_abenteuer.gd` `a2`): Leute im Tal, Gespräche mit
  Antwortwahl und Gedächtnis, mit dem Hut mehr; Nebenaufgaben. Steht neben A3 `raetsel` und A5 `zweit`.
- Schalter «Test: Hut des Grossvaters tragen» auf der Kapitelseite entfernt (A3 liefert den Hut); für Tests bleibt
  `/control abenteuer a2 {sub: hut}`.

## NEU in 3D-4.69 (MoveEye 2.98.100): Abenteuer-Rätsel (`abenteuer_raetsel.gd`)

- `abenteuer_raetsel.gd` (neu, `bergtal_abenteuer.gd` `raetsel`): Peilung, Polarstern, 10 Tagebuchseiten, Gegenstände des
  Grossvaters, Wege freischalten, 6 Abzeichen, Hilfe-Stufen. Steht neben A5 `zweit` (Variable, Malen, `state()` → `a3`).
- MoveEye 2.98.100: erste dreistellige Patch-Nummer – bauen.py, `_vkey`, Manifest, Web-`vnum`, `sort -V` vergleichen numerisch.

## NEU in 3D-4.68 (MoveEye 2.98.99): Rätsel im Hospiz (`horror_raetsel.gd`)

- `horror_raetsel.gd` (neu, über `bergtal_horror.gd` `raetsel`): pro Kapitel ein Rätsel (Schlüssel, Zahlenschloss, Uhrzeit),
  Lösung nur auf den MoveEye-Aufnahmen, Hinweis-Knopf, unter 25 % Schreck keine Schreckmomente; Befehle `r_*`.
  Passwortschutz, Widmung und Warnung unverändert.

## NEU in 3D-4.67 (MoveEye 2.98.98): Entwicklertool Teil 3 (`devtool_extra.gd`, `_notizen`, `_kontakt`, `_kapitel`)

- Notizen an Claude (mit Bild, ZIP-Export), Kontaktbogen (alle Orte einer Welt), Kapitel-Sprung in einem Test-Spielstand.
- `devtool.gd`: Teil 2 (`eb()`, Ebenen) und Teil 3 (`extra`) hängen nebeneinander in `_build`, `control` und `_draw`.

## NEU in 3D-4.66 (MoveEye 2.98.97): Abenteuer zu zweit (`abenteuer_zweit.gd`, `abenteuer_bestenliste.gd`)

- `abenteuer_zweit.gd` (neu): Spielarten gemeinsam / Rollen / Wettrennen, geteilter Bildschirm (wird eins, wenn beide nah
  sind), Handy-Begleiter per QR.
- `abenteuer_bestenliste.gd` (neu): Familien-Bestenliste (`user://bergtal_abenteuer/familie.json`). `hat()` nutzt jetzt
  `preload` von `abenteuer_inventar.gd` (A4) statt Laden zur Laufzeit. Offen (TODO A1): seltene Tiere, Foto-Wertung,
  Wildkamera – kommen mit dem MoveEye-Lager-Paket.

## NEU in 3D-4.65 (MoveEye 2.98.96): Entwicklertool Teil 2 «Regler + Ebenen» (`devtool_ebenen.gd`)

- `devtool_ebenen.gd` (neu): Schnellregler als Spiegel der Bedienfeld-Regler (Uhrzeit, Wetter, Jahreszeit, Grafik), Ebenen
  Sichtfeld / Wege / Startpunkte / Auslöser / Lampen in 3D und auf der Karte; `/control dev layer|set|regler|parts`.
- `i18n/texte.json`: Eintrag «klar» (Wetter-Auswahl, main.gd `options`) von Hand ergänzt – sim_texte findet ihn nicht im Code
  (Zeile «nicht mehr im Code»), `--aufraeumen` würde ihn entfernen.

## NEU in 3D-4.64 (MoveEye 2.98.95): Wärmebild-Tier, «Person?», «Höhe der Kamera»

- MoveEye (232, 180, 410, Selbsttest 417): Wärmebild-Tier nur bei flacher Form (h/b ≤ 0.8); «Person?» bei flacher Box +
  KI ≥ 0.15 + Bewegung/Wärme (`weak_person_feed`, Zähler `person_maybe`). Feld «Höhe der Kamera (m)» in Platz einrichten
  (317, 537, 582); die Simulator-Stange hat Vorrang, solange verbunden.
- Simulator: «Stange» heisst «Höhe der Kamera» (toolbar, explore, fotomodus, padmap, tour; T.t-Übersetzungen).

## NEU in 3D-4.63 (MoveEye 2.98.94): Abenteuer-Rucksack (`abenteuer_inventar.gd`, `abenteuer_rucksack.gd`)

- `abenteuer_inventar.gd` (neu): gemeinsames Inventar (hat / gib / nimm / anzahl / gewicht), mit dem Rucksack verbunden.
- `abenteuer_rucksack.gd` (neu): Essen und Trinken mild (nur langsamer, nie Spielende), Quellen, Kochen in der Hütte,
  Ausrüstung finden (Kompass, Stirnlampe als Licht, Feldstecher, Seil), Tausch-Fenster ohne Geld; eingebunden in
  `bergtal_abenteuer.gd`. Texte in `i18n/texte.json` (sim_texte nach dem Merge neu gelaufen, 0 Lücken).
- Nicht live geprüft: Kochen, Quelle, Stirnlampe als Licht, Lite.

## NEU in 3D-4.62 (MoveEye 2.98.93): Entwicklertool Teil 1 (`devtool.gd`)

- `devtool.gd` (neu): Fenster Mehr → Entwickler (nur Besitzer) mit Übersichtskarte aller Welten und Orte (`explore.gd`
  `alle_orte()`), Klick = hinspringen, Flugkamera (W A S D, Esc zurück); `/control dev`. Anpassungen in `mehr.gd`,
  `padmap.gd`, `main.gd`; Texte in `i18n/texte.json` (sim_texte nach dem Merge neu gelaufen, 0 Lücken).

## NEU in 3D-4.61 (MoveEye 2.98.92): Kriechende Paket-Figuren (`figur_paket.gd`)

- `figur_paket.gd`: die Bezugshaltung (Grundpose) der Paket-Figuren wird gerade gerichtet – kriechende und liegende Figuren
  liegen flach (Kopf nicht mehr im Boden, Fuss nicht in der Luft), Arme bei Winken / Handy unverändert.

## NEU in 3D-4.60 (MoveEye 2.98.91): Simulator-Sprachen Schritt 2 (`i18n/texte.json`)

- Die 231 fehlenden Übersetzungen (en/fr/it/rm) ergänzt, nur `simulator3d/i18n/` (texte.json, abdeckung.txt).
  `werkzeuge/sim_texte.py --pruefen` meldet jetzt 0 Lücken (neue Basis 0 statt 231). Rätoromanisch noch nicht von
  Muttersprachlern geprüft.

## NEU in 3D-4.59 (MoveEye 2.98.90): Schwachlicht-Hysterese in MoveEye, nur noch eine Exe im ZIP

- Simulator-Code unverändert. MoveEye (Teil 410 `_lowlight_decide`): Helligkeit 10 s Median, Aus erst über Schwelle +
  `lowlight_gap`, Wartezeit `lowlight_hold` (Regler in der Gruppe Schwachlicht).
- ZIP ohne die Übergangs-Kopie `MotionWatch3D.exe` (simpack.sh TRANSITION=0 ist jetzt Vorgabe). `update.gd`
  `old_name_forward` / `remove_old_name_files` bleiben für Installationen, die die alte Datei noch haben.

## NEU in 3D-4.58 (MoveEye 2.98.89): Foto-Modus (`fotomodus.gd`)

- `fotomodus.gd` (neu, über `zwilling.gd`): Foto als Kugel um die Kamera, Horizont/Höhe/Neigung, Farbanpassung der Figuren
  (camfx.gdshader `foto_*`, eigene Teile getrennt vom Weitwinkel und camphys), Maske «Vorne malen» (fotomaske/fotowelt, foto.gdshaderinc).
  `before_capture` vor wetter und camphys.

## NEU in 3D-4.57 (MoveEye 2.98.88): Echte Oberflächen und Himmel (`inhalte.gd`, CC0-Paket)

- `inhalte.gd` (neu): lädt `inhalte/katalog.json` (Paket `pakete/MoveEye_Inhalte_F2.zip` von raw.githubusercontent.com mit
  SHA-256, sonst Einzeldateien) nach `user://inhalte/`; Shader grass/sky/flecken. Aus in Lite und im Prüfstand (`--quality`).
  Quellen: `CREDITS.md`. Das Paket enthält 6 der 11 Inhalte; die übrigen lädt der Simulator einzeln von den Quellen.

## NEU in 3D-4.56 (MoveEye 2.98.87): Figuren-Paket und Wind (`figur_paket.gd`, `wind_fx.gd`)

- `figur_paket.gd` (gleiche Schnittstelle wie figur.gd; Paket `pakete/figuren_v1.zip` mit `.gdignore` → nicht im Export,
  Download von raw.githubusercontent.com/…/main/simulator3d/pakete/figuren_v1.zip mit SHA-256), `werkzeuge/figuren_paket.py`.
  Lizenz: LIZENZEN.md (Quaternius, CC0). `wind_fx.gd` + Shader grass_wind / tent_wind / foliage (`gust_amt`).
- Bekannt: Kriechen mit Paket-Figuren 1/4 erkannt (Ringfiguren 4/4).

## NEU in 3D-4.55 (MoveEye 2.98.86): Grafikstufe «Hoch» (`grafik_hoch.gd`, `quality.gd`)

- `grafik_hoch.gd` (neu, Forward+/Vulkan, nur Godot-Bordmittel); `quality.gd` MODES (auto, lite, normal, hoch), eine Wahl
  `grafik_mode`, Einzelheiten Experte. Rückfall auf Normal, wenn Vulkan fehlt oder Hoch zu langsam ist.

## NEU in 3D-4.54 (MoveEye 2.98.85): Spielbereich «Spielen» (`spielbereich.gd`, MoveEye 639i)

- `spielbereich.gd` (neu): Startbildschirm «Spielen» (Kapitel, Entdeckungen, Abzeichen, Stufe, Blinki), Kachel ⭐ in `quick.gd`,
  Steuerung `{"action":"spielbereich"}`. MoveEye 639i: Web `/play` unter Mehr (bis Daniel über einen 7. Reiter entscheidet),
  im Fenster Knopf «⭐ Spielen» in der Leiste von Mehr (572).

## NEU in 3D-4.53 (MoveEye 2.98.84): Servo-Mechanik MG90S (`servo.gd`)

- `servo.gd` (neu): MG90S-Modell pro Achse (Tempo, Spiel, Nachschwingen, Strom, 5-V-Einbruch), Kopfbewegung in `main._process`,
  Störungen über `simint.gd`. Steuerung `{"action":"servo","do":"info|set|sim"}`. Lite: nichts abzuschalten.

## NEU in 3D-4.52 (MoveEye 2.98.83): PIR AS312, Mikrofon und Umgebungsgeräusche (`pir.gd`, `mikrofon.gd`)

- `pir.gd` (AS312: Fächer, Reichweite nach Temperatur, Fehlauslösung), `mikrofon.gd` + `mikrofon_*.gd` (Pegel, Umgebungsgeräusche),
  `simint.gd`; Feld `mic` (schnittstelle.json). MoveEye 558p (Mithören im Simulator), 250/350/530/550/570.
  `mikrofon._lite()` = `Quality.lite()`.

## NEU in 3D-4.51 (MoveEye 2.98.82): Wetter physikalisch (`wetter.gd`, `linse.gd`)

- `wetter.gd` (Regenstärke, Sicht, Bodennebel, Schnee, Linsenklima, Blitze; `sky_tick`, `before_capture` vor camphys) und
  `linse.gd` + Shader (Tropfen/Beschlag, Vierecke vor der Kamera: expo → camfx → Bodennebel → Linse → lens). Steuerung
  `{"action":"wetter"}`. Testlauf «wetter» (testrun.gd, pruefstand.py, von Hand). Lite: weniger Teilchen.

## NEU in 3D-4.50 (MoveEye 2.98.81): Kamera wie Camera Module 3 NoIR (`camphys.gd`)

- `camphys.gd` (neu): Belichtung, Verstärkung, Rauschen, NoIR-Farben, Unschärfe, Rolling Shutter; läuft in `_capture` nach
  `weit.before_capture` und setzt `distort` nicht für die Weitwinkel-Kamera (deren Fischauge bleibt). camfx.gdshader: eigene
  Uniforms getrennt von den Weitwinkel-Teilen. `ir_range` 10 m (vorher 14). Lite: Farbrauschen statt Flecken, kein Leuchten.

## NEU in 3D-4.49 (MoveEye 2.98.80): Gelände und Pflanzen (`gelaende.gd`, `vegetation.gd`)

- `gelaende.gd` (Relief, Wege, Sichtlinien `los`, Wolkenschatten), `vegetation.gd` (Bäume, Hecken, Gras/Blumen als MultiMesh);
  `main.hilly()` (statt nur `terrain`), `ground_y()`: zuerst `ground_fn`, dann Ort, dann Hügel. foliage.gdshader: Jahreszeit
  (`bare`, `blossom`) + Wolkenschatten (`cloud_amt`). Steuerung `{"action":"gelaende"}`. Lite: Gras/Blumen ausgedünnt.

## NEU in 3D-4.48 (MoveEye 2.98.79): Jahreszeiten (`jahreszeiten.gd`)

- `jahreszeiten.gd` (neu): Laub, Blüten, Blätter, Schnee, Bodennebel, Tageslauf, Belegung (`accept_visit`, `visit_factor`);
  `main.jahreszeit()`, Feld `season` in world_reply. Regler `jz_*`. Bergtal behält seine Berg-Jahreszeit (Juni = Frühling)
  über denselben Monat (`main.season`); eigener Schnee, der Winterschnee dieses Pakets ist dort aus.

## NEU in 3D-4.47 (MoveEye 2.98.78): Licht & Nacht (`licht.gd`)

- `licht.gd` (neu): Sonne, Dämmerung, Mond, Sterne, Lichtverschmutzung, Lampen, Blendung; `main.licht.lux_at(p)`, `main.licht.sky`,
  `night_level()` für `main.light_level`. sky.gdshader `star_vis` / `star_lim` (+ `milky` vom Bergtal). Feld `sky` in
  world_reply (schnittstelle.json; MoveEye liest es noch nicht). Teil «Licht & Nacht» in der Karte Szene. Lite: höchstens 4 Lampen, keine Schatten.

## NEU in 3D-4.46 (MoveEye 2.98.77): Fahrzeuge wie echt (`fahrzeuge.gd`)

- `fahrzeuge.gd` (neu): Tempo, Licht, Blendung (`_glare_tick`), Türen, Parkieren; Motorwärme aus `Waerme.engine()` (nur die
  Lampe mit eigenem Wert), läuft `waerme_welt`, macht diese die Motorwärme. Steuerung `{"action":"fahrzeuge"}`.
  Testlauf «Fahrzeuge in der Nacht» (testrun.gd, pruefstand.py, Workflow sonntags).

## NEU in 3D-4.45 (MoveEye 2.98.76): Tiere wie echt (`tiere.gd`, `fauna.gd`)

- `tiere.gd` (neu): Verhalten pro Art (auf actor.gd / simreal.gd / life.gd), Steuerung `{"action":"tiere","do":"info|spawn|threat|curl|pounce|car"}`.
  `fauna.gd`: Bodenvögel (Krähe, Elster, Möwe), Wärme über `Waerme.animal("bird")`. `actor.gd`: echte Grössen, Fell über
  `Waerme.animal()` (eigene Werte nur noch Rückfall). Lite: weniger Vögel, keine segelnden Möwen.

## NEU in 3D-4.44 (MoveEye 2.98.75): Wärmebild wie Thermal-90, Wärmetabelle (`thermsensor.gd`, `waerme.gd`)

- `thermsensor.gd` (Sensor-Modell Thermal-90), `waerme.gd` (Wärmetabelle: `Waerme.…` für Menschen, Tiere, Motoren, Feuer, Sonne),
  `waerme_welt.gd` (Oberflächen nach Sonne/Wetter, Auto-Motor); Shader `thermal*.gdshader` + `thermal_inc.gdshaderinc`.
  Neue Pakete mit eigenen Wärmewerten sollen `Waerme` nutzen. Lite: ohne Unschärfe, höchstens 8 Wärmebilder/s.

## NEU in 3D-4.43 (MoveEye 2.98.74): Einbruch-Abläufe (`einbruch.gd`)

- `einbruch.gd` (neu): 7 Abläufe mit Bewertung, Steuerung `{"action":"einbruch","do":"info|start|serie|stop|state|result"}`;
  im Nacht-Testlauf als Vorfall (`nachtlauf.register_kind`). `menschen._testing()` kennt `main.einbruch`. Lite: halb so oft prüfen.

## NEU in 3D-4.42 (MoveEye 2.98.73): Menschen-Verhalten (`menschen.gd`)

- `menschen.gd` (neu): Gangarten, Vielfalt, Gruppen, Tagesablauf, Schnittstelle für Szenarien (`main.menschen.spawn_kind`);
  Knöpfe `m_send_*` unter Besuch → Menschen schicken. `actor.gd`: Feld `hold_post`. Lite: `Quality.lite()`.

## NEU in 3D-4.41 (MoveEye 2.98.72): Pfadilager, Bergdorf, Hofladen, Festival (`kompakt*.gd`)

- `kompakt.gd` + `kompakt_pfadi.gd`, `kompakt_dorf.gd`, `kompakt_hof.gd`, `kompakt_festival.gd`, Shader `kompakt_ort.gdshader`;
  `worlds.gd` (Orte/Welt Festival), `bergtal.gd` (`place_c`: Mitte des Orts, MoveEye kann daneben stehen), `ferienpark.gd`.
  Regler `szene_spot` nur in diesen Orten («only»). Lite: `Bib.lite()` = `Quality.lite()` (`nl()` ≈ 35 %).

## NEU in 3D-4.40 (MoveEye 2.98.71): Horror-Modus «Das Hospiz» (`bergtal_horror.gd`)

- `bergtal_horror.gd` (neu): Passwort nur als gesalzener Hash (PBKDF2) in `user://bergtal_horror.json`, nie im Repo/Log;
  `{"action":"horror"}` (start nur entsperrt), Bilder `/horror_pic/<i>.jpg` (net.gd), Feld `horror` (schnittstelle.json),
  MoveEye 539a (Verlauf), 350.
- Einstieg nur über den 5. Platz der Stimmungswahl im Abenteuer (`mood_slot()` / `open_from_mood()`); Knopf unter «Szene» entfernt.

## NEU in 3D-4.39 (MoveEye 2.98.70): Bergtal-Abenteuer (`bergtal_abenteuer.gd`)

- `bergtal_abenteuer.gd` (Ablauf + Fenster) und `bergtal_abenteuer_daten.gd` (Stimmungen, Rucksack, Kapitel); Steuerung
  `{"action":"abenteuer","do":…}`, `busy_with`; Nacht über `nachtlauf.gd` (eigener Plan).
- Start als Schnellstart-Karte im Spiel-Assistenten (`gamewiz.gd`, `v` «abenteuer») statt Knopf in der Karte «Spiel».

## NEU in 3D-4.38 (MoveEye 2.98.69): Orte zum Erkunden im Bergtal (`bergtal_orte.gd`)

- `bergtal_orte.gd` (neu): Innenräume, Wasser, Grat, Geschichte; ersetzt in `bergtal.gd` die einfachen Gebäude (`REPLACES`,
  `orte.replaces()`), Steuerung `{"action":"bergtal","do":"orte"}`, Hooks `hospiz_door` / `hospiz_light` (für den Horror-Modus).
  Lite: `Bib.lite()` = `Quality.lite()`.
- Vignette 31 (Sennerei) nutzt den Käse im Gestell der Sennerei (`s.data["bt_dairy_cheese"]`), kein zweiter Käse mehr.

## NEU in 3D-4.37 (MoveEye 2.98.68): Erlebnisse im Bergtal 18–34, gemeinsame Basis (`bergtal_erleben_b.gd`, `bergtal_erleben_base.gd`)

- `bergtal_erleben_b.gd` (neu, Vignetten 18–34), Steuerung `{"action":"bergtal","do":"erleben_b"}`.
- Neu `bergtal_erleben_base.gd`: gemeinsame Hilfen, `_process`, Klasse `Vig` für Teil A und B (vorher doppelt, ~500 Zeilen);
  jeder Teil: `extends` Basis, `_part()`, `_make_vigs()`, `_register()`. Meta «be_y». Lite: `_lite()` = `Bib.lite()` = `Quality.lite()`.

## NEU in 3D-4.36 (MoveEye 2.98.67): Aussichtspunkte im Bergtal, Teil «Bergtal» in Szene (`bergtal_aussicht.gd`)

- `bergtal_aussicht.gd` (neu): Fernrohr, Panorama, Beobachten, MoveEye-Reichweite, Stimmungen (sky.gdshader `milky`),
  Karte aufdecken (minimap.gd), Wetter von weitem; Regler über `add_controls(main)`, Steuerung `{"action":"bergtal","do":"aussicht"}`.
  `_lite()` = `Quality.lite()`.
- main.gd: alle `bt_*`-Regler der Karte Szene im Teil «Bergtal» (GROUPS Szene), mit «only» nur im Bergtal (Fenster und MoveEye).

## NEU in 3D-4.35 (MoveEye 2.98.66): Erlebnisse im Bergtal 1–17 (`bergtal_erleben_a.gd`)

- `bergtal_erleben_a.gd` (neu): 17 Abläufe an den VIGNETTES-Plätzen von `bergtal.gd` (Hook `_erleben()`,
  `s.data["bt_erleben_a"]`), aktiv unter 60 m, versteckt über 220 m, bei Tests weg. Entdeckungen `berg.*` (18).
  Steuerung `{"action":"bergtal","do":"erleben","what":"info|where|go|state"}`. `_lite()` = `Bib.lite()` = `Quality.lite()`.

## NEU in 3D-4.34 (MoveEye 2.98.65): Welt «Bergtal» und Szenen zusammengefasst (`bergtal.gd`, `worlds.gd`)

- `bergtal.gd` + `bib_berg.gd` (erbt von Bib → `Quality.lite()`), Bodenshader `bergtal_boden.gdshader`, Karte mit Höhenlinien
  (`minimap.gd`). Regler `bt_*` mit `controls[…]["only"]`: nur im Bergtal (Jahreszeit, Schnellreise, Ereignisse auch in seinen Orten).
- `worlds.gd` (neu): alte Szenen sind Orte in Welten (`Worlds.world_of`, `is_place`, `solo`); `main.scene` bleibt die alte
  Kennung. Steuerung `{"action":"welt"}`, `{"action":"scenario","solo":true}`, Schalter `welt_solo`, Start `--solo`
  (Prüfstand). MoveEye 141 (Trainingsnacht allein), 551 (Name «Zuhause»). Details: REAL_BERGTAL, REAL_KONSOL.

## NEU in 3D-4.33 (MoveEye 2.98.64): Weitwinkel wie Gehäuse v5.2 (`weitwinkel.gd`, `camfx.gdshader`)

- `weitwinkel.gd`: Montage «case» (neuer Standard, Masse aus Gehäuse v5.2) und «none» (Blindstopfen); äquidistantes Fischauge
  und Vignette in `camfx.gdshader` (`fe_*`, Kamera 1: `distort` = 0), IR-LED Kanal 4 (ca. 4 m). Lite: `Quality.lite()`.
- MoveEye 163/591/568: «Im Gehäuse» zählt als Montage am Gerät, Kachel 🔭 mit den neuen Knöpfen. Prüfstand `--weitwinkel case`.

## NEU in 3D-4.32 (MoveEye 2.98.63): Gameplay ausfeilen (12 Punkte, `gamemore.gd` u. a.)

- Neu: `gamemission.gd`, `gamenacht.gd`, `gamesneak.gd`, `gameschwitzen.gd`, `gameturm.gd`, `gameturnier.gd`, `gameziele.gd`,
  gemeinsamer Teil `gamemore.gd` (Probe, Wiederholung, Höhepunkte, Werkzeuge). Geändert: game.gd, gamewiz.gd, gamerules.gd,
  gametools.gd, localplay.gd. MoveEye 548/596: Rangliste KI-Turm. Plan: `docs/Gameplay_Ausfeilen_Plan.md`.
- `gamemore._lite()` = `Quality.lite()` (keine Leucht-Materialien, kein Kies-Schmuck, Film 4 statt 8 Bilder).

## NEU in 3D-4.31 (MoveEye 2.98.62): Nacht-Testlauf (`nachtlauf.gd`, MoveEye /nacht)

- `nachtlauf.gd` (neu): Ablauf einer Nacht mit festem Zufall, schreibt die Wahrheit (Ereignisse, Abstand, Sichtbarkeit);
  Steuerung `{"action":"nacht",…}` (schnittstelle.json), `busy_with` «Nacht-Testlauf». Eigene Arten:
  `main.nacht.register_kind(kind, f, cat, cause)`. MoveEye: 579b (Abgleich, /nacht), 599d (Fenster), 599e (Texte).
- Abbrechen im Simulator-Fenster bleibt erlaubt (Daniel 31.10.); Start nur in MoveEye durch den Besitzer.
- MoveEye: «Trainings-Nacht» 🏋 und «Nacht-Generalprobe» 🎭 statt 🌙 (🌙 nur noch Nacht-Testlauf).

## NEU in 3D-4.30 (MoveEye 2.98.61): Erlebniswelt im Ferienpark (`erlebniswelt.gd`, 19 Vignetten)

- `erlebniswelt.gd` (neu): 18 Abläufe (innere Klassen) an den reservierten Orten von `ferienpark.gd`, nur aktiv unter 60 m
  (Ansicht oder MoveEye), unsichtbar über 180 m, bei Testlauf / Prüfstand weg. Figuren aus `actor.gd` («puppet», neue Geste
  «wave»). Steuerung `{"action":"ferienpark","do":"erleben","what":…}`. Entdeckungen über `main.entdecken.register()`.
- `_lite()` = `Quality.lite()`. Knopf `disc_seek` mit `controls[-1]["only"]` nur in der Szene «ferienpark» (Fenster und MoveEye).
- `overlay3d.gd`: MoveEye-Boxen auf Erlebniswelt-Figuren = «✓ erkannt». Details: Zweig `erlebniswelt`, REAL_ERLEBEN.

## NEU in 3D-4.29 (MoveEye 2.98.60): «Neu in dieser Version» scrollt, Esc schliesst (`news.gd`)

- `news.gd`: Liste in einem `ScrollContainer` (`_scroll`/`_list`), Knöpfe ausserhalb – nie höher als der Bildschirm;
  `_unhandled_input`: Esc = `close(false)`.

## NEU in 3D-4.28 (MoveEye 2.98.59): Szenen-Bibliothek `bib_objekte.gd` + Szene «Ferienpark am See» (`ferienpark.gd`)

- **Bibliothek** (~90 Dinge mit Parametern, echte Grösse, Hindernis, Wärme, Sichtweite): `var bib = Bib.new(main, scenes, knoten,
  transform)`, `bib.add(art, pos, drehung, {…})`, `bib.many(art, liste)`, `bib.line(art, a, b, n)`, `bib.finish()`. Teile gleicher
  Oberfläche pro 48-m-Zelle in einem Netz (+ Wärmebild-Zwilling), viele gleiche Dinge als MultiMesh (128-m-Gruppen).
  **Lite:** `Bib.lite()` = `Quality.lite()` (zusätzlich Grafik «simple»): 6 statt 10 Ecken, kleine Teile weg, Sichtweiten
  320/110/45 m, halber Wald, 4 Lampenlichter, 1 Rauchfahne.
- **Ferienpark** (~500 × 500 m): See, Terrassen (`main.ground_fn` = Höhe in Weltkoordinaten), Wald, Dorf; Boden-Shader
  `shaders/ferienpark_boden.gdshader`; Ortsschilder nur im Fenster (HELPER_LAYER), nicht im MoveEye-Bild.
  5 MoveEye-Standorte (`ferienpark.gd SPOTS`, Einstellung `fp_spot`, gespeichert in KEEP): zelt, wohnmobil, bungalow, steg, rezeption.
- **Neu: Regler nur in ihrer Szene.** `add_control(…)` danach `controls[-1]["only"] = func(): return scene == "…"`: der Regler
  fehlt dann im Fenster (`_dev_hidden` / `_apply_simple`, nach `set_scene` → `_only_refresh`) und in `control_info()` – MoveEye
  baut seine Simulator-Steuerung bei geänderter Liste von selbst neu (kein MoveEye-Code nötig). Erster Fall: «Standort im
  Ferienpark am See».
- MoveEye 551: Szenen-Name in allen Sprachen.

## NEU in 3D-4.27 (MoveEye 2.98.58): Entdecken (`entdecken.gd`, Erlebniswelt 20–23)

- **API** `main.entdecken`: `register(id, info)` während des Szenenbaus (main `_build_scene` ruft vorher `begin_scene`, danach
  `on_scene`), `mark_found`, `is_found`, `count`, `total`, `possible_now`, `list`, `reset`, `forget`, `take_photo`, `show_hint`,
  `open_book`; Signal `found(id)`. `info`: title, short_text, hint, icon, position/node, size, radius, when (night/day/morning/
  evening/rain/dry/snow/fog, Array = alle), kind (ort/szene/tier/mensch), photo_required, active (Callable), los, demo.
  **ids szenenübergreifend eindeutig** (`<szene>.<name>`). Ganze Tabelle: Zweig-Doku REAL_ENTDECKEN.md (Kopf von entdecken.gd).
- Gefunden per Ansicht (näher als radius, im Bild, Sichtlinie, 0.5 s) oder Foto der Kopfkamera (ganze Kiste im Bild, ≥ 22 px).
  Gespeichert `user://entdecken.json`, Bilder `user://entdecken/<szene>/<id>.jpg`. /control `entdecken` (info/open/photo/mark/
  reset/hint/set/where/register/unregister/forget), Bild `GET /disc_pic/<i>.jpg`.
- Buch = «Mehr»-Fenster (Symbol `book`, neu gezeichnet in `ui_style.gd group_icon`, Kachel «Entdeckungen» unter Spielen mit Buch
  statt Stern – wie 📖 in MoveEye). **Blinki-Hinweis im Fensterrahmen** (`entdecken.join_fenster(fenster)`, id «blinki»):
  Häkchen in «Fenster» = Einstellung «Blinki-Hinweise» (kein zweiter Schalter), ✕ des Rahmens schaltet sie aus.
- Lite: `entdecken._lite()` = `Quality.lite()` (Bilder 128 × 72, Prüfung 2× statt 4× pro Sekunde).
- MoveEye (139, 550, 639g): Kachel 📖 Entdeckungen in der Simulator-Zentrale (Blatt, Foto, im Simulator öffnen, Blinki-Hinweis).

## NEU in 3D-4.26 (MoveEye 2.98.57): Fenster im gemeinsamen Rahmen (`fenster.gd`)

- `scripts/fenster.gd`: ein Rahmen für alle schwebenden Fenster (Kompass, Karte, Livebild, SmallTV, Gerät, Mover-Stick,
  Kopf steuern, Kameras bei zugeklapptem Bedienfeld, CPU-Anzeige): Titelleiste ziehen (Doppelklick = Standardplatz),
  Grösse über die Ecke (Bilder mit festem Seitenverhältnis; Kompass/CPU/Mover fest), ✕ blendet aus, Schnappen 12 px an
  Rand (14 px), Bedienfeld, Leiste, «Bedienfeld zeigen» und andere Fenster (6 px oder bündig).
- Dock-Knopf **«Fenster»** (zwischen «Ansicht» und «Menü»): Liste mit Häkchen + «Anordnung zurücksetzen». Fenster mit eigener
  Taste/Einstellung schalten darüber (Karte = M, Livebild = L, Kameras = «Kamerabilder», SmallTV/Gerät = ihre Einstellung).
- Gemerkt pro PC in `user://fenster.json` (Ort relativ zum freien Platz, Grösse, ausgeblendet). Nie verschobene Fenster bleiben
  am alten Platz und rücken wie bisher mit.
- **Für andere Pakete:** eigenes Panel mit einer Zeile anmelden: `main.fenster.add("id", "Titel", panel)` (Optionen im Kopf von
  `fenster.gd`); Skripte, die sich selbst platzieren, prüfen `has_meta("fenster")`. Test-Aktion `/control {"action":"fenster",
  "do": info|drag|resize|close|list|check|reset}`. `cam_fx`/`cam_fy` werden nicht mehr gelesen.
- Lite: kostet nur ein paar Vergleiche pro Bild, keine eigene Lite-Abfrage nötig. Ungetestet: echter Touch, Windows, Controller in der Liste.

## NEU in 3D-4.25 (MoveEye 2.98.55): Grafik-Stufe «Lite» für den Raspberry Pi 5 (`quality.gd`)

- **Zentrale Abfrage (für alle Pakete, auch parallele Zweige):** `const Quality = preload("res://scripts/quality.gd")` →
  `Quality.lite() -> bool`; ohne preload: `Engine.has_meta("lite") and Engine.get_meta("lite")`. Gesetzt nur von
  `main.gd lite_update()` (beim Start und bei jedem Wechsel) über `Quality.set_lite()`. Wer etwas Teures baut (Partikel,
  Gras, Effekte, Schatten), fragt das ab; `Quality.n(anzahl)` gibt in Lite ~35 % zurück.
- **Einstellung** «Grafik-Modus» (`grafik_mode`, System → Grafik, auch in «Einfach»; gespeichert in user://, KEEP):
  `auto` (Standard) / `lite` / `normal`. Stufen-Liste `Quality.MODES` – **erweiterbar**: Lite < Normal (= Grafik bis 3D-4.24)
  < Hoch (Zweig «foto-hoch», `scripts/grafik_hoch.gd`, hängt dort `["hoch", "Hoch …"]` an MODES an; `mode_id()` /
  `mode_name()` nehmen neue Stufen von selbst). Test-Option `--grafik auto|lite|normal` (alt «voll»/«full» = normal).
- **Automatisch → Lite**, wenn `Quality.weak_reason()` etwas findet: `/proc/device-tree/model` enthält «Raspberry Pi»,
  Linux auf arm64/arm32, oder Grafik «V3D/VideoCore»; sonst nach 6–40 s im Mittel unter 12 Bilder/s (`_lite_tick`, einmal pro
  Start, nicht mit `--quality` = Prüfstand).
- **Was Lite macht** (`_lite_apply`, `_lite_scene`): Grafik «einfach» (keine Schatten, kein Glow, kein SSAO/SSR/SDFGI/Volumen-
  nebel, kein MSAA), `scaling_3d_scale` ≤ 0.6, höchstens 25 Bilder/s (auch `_check_active`), Regen/Schnee/Spritzer und alle
  Partikel der Szene ×0.35, Wiese `visible_instance_count` ×0.35, kleine Dinge (< 1.5 m) mit `visibility_range_end` 70 m,
  `max_visitors` ≤ 6, `/view.jpg` / `/view.mjpg` ≤ 640 px, JPEG 55 %, ≤ 4 Bilder/s. **Unverändert:** die Kamerabilder für
  MoveEye (960 × 540 / 640 × 360) – die Erkennung bekommt dieselben Bildgrössen (nur ohne Schatten). Die eigenen Werte
  (Grafik, Schärfe, Bilder/s, Besucher) liegen in `_perf_orig`, werden so gespeichert und mit «Normal» zurückgesetzt.
- **Renderer:** das ganze Projekt läuft schon mit Compatibility (OpenGL); `project.godot` hat neu zusätzlich
  `renderer/rendering_method.arm64="gl_compatibility"`, damit das arm64-Paket (Preset «Linux Pi») auch dann Compatibility
  bleibt, wenn ein anderer Zweig den Standard auf Forward+ stellt. Zur Laufzeit lässt sich der Renderer nicht wechseln: Lite
  von Hand am PC mit Vulkan (`.bat`) schaltet nur die Effekte ab.
- **«🩺 Leistung»** in Mehr → Selbstdiagnose (Zeile «Leistung», vorher «Grafik und Bilder pro Sekunde»): Bilder/s, Lite an/aus
  (mit Grund), Renderer, 3D-Auflösung (%), Kamerabild für MoveEye; dazu Kurzform auf der Karte und in «Über» (`main.perf_info()`).
- Gemessen hier (Xvfb, llvmpipe, 2 Kerne, PC-CPU 100 % durch andere Helfer): Normal 1 Bild/s, Lite 1–3 Bilder/s (3D 864 × 516
  statt 1440 × 860) – **nicht aussagekräftig**, keine Pi-Zahlen. MoveEye am Lite-Simulator: verbunden, Kamerabilder kommen
  (0.9 Bilder/s), Bewegungsrahmen um die Person. arm64-Export baut; auf echtem Pi 5 **ungetestet**.

## NEU in 3D-4.24 (MoveEye 2.98.53): Datei heisst MoveEyeSim3D.exe, frischer Start; Schriftzug mit echtem Gang

- **Neuer Dateiname:** export_presets `MoveEyeSim3D.exe` / `MoveEyeSim3D.x86_64` / `MoveEyeSim3D.arm64`, Datei-Eigenschaften
  «MoveEye Sim 3D» / Firma «MoveEye» (wirken erst mit `application/modify_resources=true` + rcedit – ist aus, also noch
  Godot-Standardangaben in der .exe). project.godot `config/name="MoveEye Sim 3D"` → **neuer Ordner der Benutzerdaten** (user://),
  die alten Einstellungen bleiben unbenutzt liegen (Entscheid Daniel: frischer Start, keine Übernahme).
- **Alte Installationen (bis 3D-4.23, MotionWatch3D.exe):** ihr Updater sucht im ZIP `MotionWatch3D.exe`. Darum enthält das
  ZIP (Ordner `MoveEyeSim3D/`) **übergangsweise dieselbe Datei zweimal**: `MoveEyeSim3D.exe` und `MotionWatch3D.exe`
  (ZIP ~64 MB statt ~32 MB; `simpack.sh` mit `TRANSITION=0` lässt die Kopie weg). Ablauf: alter Updater legt beide hin,
  ersetzt die laufende Datei durch die neue `MotionWatch3D.exe` und startet sie mit `--updated`; die merkt am alten Namen
  (`update.gd old_name_forward()`, ganz am Anfang von `main._ready`), dass `MoveEyeSim3D.exe` daneben liegt, startet diese mit
  denselben Argumenten + `--renamed` und beendet sich. `MoveEyeSim3D.exe` biegt den Autostart um (`autostart.gd repair()`:
  alter Wert «MotionWatch3D» / `motionwatch3d.desktop` → neuer «MoveEyeSim3D» / `moveeyesim3d.desktop`, alter entfernt) und
  löscht nach 4 / 20 / 90 s `MotionWatch3D.exe` und `MotionWatch3D.exe.old*` (`remove_old_name_files()`, nur wenn kein
  Autostart mehr auf den alten Namen zeigt). Der neue Updater überspringt die Kopie im ZIP. Unter Linux mit der echten
  3D-4.23-Datei geprüft, unter Windows ungetestet.
- Bleibt (Kennungen für Entferntes): ZIP-Pfad `simulator3d/MotionWatch3D_Simulator.zip` (alte Simulatoren und ältere
  MoveEye-Versionen holen ihn dort), User-Agent «MotionWatch3D…», Repo-URLs. MoveEye 100 erkennt den Simulator-Prozess an
  «moveeyesim3d» oder «motionwatch3d». Firewall-Regel «MoveEye Simulator» gilt pro Datei: Windows fragt für die neue nochmals.
- `wordmark.gd`: echter Gang wie im Web (MoveEye 144): Bein 1 + Arm 2 im Takt, Bein 2 + Arm 1 einen halben Schritt
  (0.35 s von 0.7 s) später.

## NEU in 3D-4.23 (MoveEye 2.98.52): Schriftzug bewegt wie im Web (`wordmark.gd`)

- `scripts/wordmark.gd` ist jetzt ein Control: `build(height)` zeichnet die Ebenen einmal (Sichtfächer, Person+Ecken,
  4 Glieder, Buchstaben, Ring, Pupille; je 2× fein, auf den benutzten Bereich zugeschnitten), `_draw()` verschiebt / dreht nur.
  Zeiten wie die Keyframes von MoveEye 144 (`WORDMARK_CSS`): Gehen 7 s ease-in-out (cubic-bezier .42,0,.58,1), Schritte 0.7 s
  ±18°, Fächer ±14.1° ums Auge, Pupille x −2.96…4.6 / y −2 auf derselben Kurve, Blinzeln 23 s (bei 39.6 % und 95.6 %, auf 10 %).
  Höchstens 30 Bilder/s, nichts, wenn unsichtbar oder minimiert. `texture(h)` (ganzes Logo still) bleibt.
- Die Ebenen sind aus `WORDMARK_W6` von quelle/144 geschnitten (rote Person wie im Web, vorher noch die alte orange Figur).
  Ändert sich das Logo im Web, die Konstanten in wordmark.gd neu daraus erzeugen.
- Nur main.gd (Kopf des Bedienfelds) zeigt den Schriftzug; mehr.gd, mini.gd, gamewiz.gd zeigen das Symbol (`mw_logo.gd`).

## NEU in 3D-4.22 (MoveEye 2.98.51): Namen «MoveEye» statt «MW», Lautsprecher in «Licht & Ton», Hinweis Tasten-Regeln

- Sichtbare Namen: «MoveEye Sim · 3D %s» (main.gd `beacon_name` / `control_info`, net.gd, update.gd, device.gd «· Gerät 2»),
  Autostart-Eintrag Linux `Name=MoveEye Sim 3D` (autostart.gd; Kennung «MotionWatch3D» / Datei `motionwatch3d.desktop` bleiben,
  `repair()` schreibt einen alten Eintrag mit «Name=MW Sim» neu), mini.gd «MoveEye-CPU %d %%», data.yaml-Kommentar (dataset.gd).
  MoveEye erkennt den Simulator weiter an «3D-x.y» im Namen (300 `sim_versions`), nicht an «MW».
- Trainingspakete: `MoveEye-Trainingsbilder_<Zeit>.zip`; kidaten.gd `ZIP_PREFIXES` erkennt auch die alten `MW-Trainingsbilder_…`.
- simint.gd: «Lautsprecher» (spk_vol, spk_mute) in der Gruppe «Licht & Ton» (GROUPS: «", Status-LED & Tasten, Lautsprecher» wie
  MoveEye «Lichter, Status-LED, Lautsprecher»), vorher «Sensoren».
- statusled.gd `add_info`: Hinweis «Regeln der Tasten … stellt man in MoveEye ein» + Knopf «Regeln der Tasten → in MoveEye»
  (nur sichtbar, solange MoveEye verbunden ist; öffnet `/settings?open=sec:Status LED`).
- Nicht umbenannt (technisch): project.godot `config/name` (= Ordner der Benutzerdaten), export_presets (Exe-Name
  MotionWatch3D.exe, Firmenname), ZIP `simulator3d/MotionWatch3D_Simulator.zip` und Ordner im ZIP, User-Agent, Repo-URLs.
  (3D-4.24: Exe-Name, config/name, Ordner im ZIP und Autostart doch umbenannt, siehe oben.)

## NEU in 3D-4.21 (MoveEye 2.98.50): Status-LED & Tasten, Gruppe «Licht & Ton», Sprachen Schritt 1, Karte «Mehr», Angleichen

- `scripts/statusled.gd`: LED-Kuppel in Blinkis Augen-Ring (state `led` von MoveEye 599c), Fenster «Gerät» mit LED-Punkt und den
  Knöpfen «Schutz» / «Alarm quittieren» (world_reply `buttons`, wie ein GPIO). Einstellung: **Licht & Ton → Status-LED & Tasten**
  (neue Gruppe in `GROUPS`, gid `lightsound`, Symbol `sun` in ui_style.gd – wie MoveEye «Licht & Ton»). Die Regeln der Tasten
  (dürfen alles, einzeln abschaltbar, Push bei Ausschalten / Sirene-Stopp) sind MoveEye-Einstellungen, nicht im Simulator.
- Sprachen Schritt 1: `scripts/i18n.gd` (T.t), `i18n/texte.json` (gesammelt mit `werkzeuge/sim_texte.py`), Zustandsfeld `lang`
  von MoveEye (292). Noch nichts sichtbar übersetzt; Texte aus wt-angl / wt-simmehr / wt-led haben noch Lücken (`--pruefen`).
- Karte «Mehr» (wt-simmehr) und Angleichen (wt-angl): siehe Commits 2b68263 / 543271d.

## NEU in 3D-4.21 (MoveEye 2.98.50): Gegenstände und Umgebung wie echt (`objekte_neu.gd`, `objekte_plus.gd`, `umgebung.gd`)

- **`scripts/objekte_neu.gd`** (nur Daten, Format wie objects.gd): 57 neue Dinge in 5 neuen Katalog-Reitern (Wertsachen, Camping,
  Garten & Haus, Lockt Tiere an, Fehlalarm-Quellen) + neues Obst / Essen im Reiter «Essen» und die Strassenlampe in «Draussen».
  Neu im Format: Teil «f» = Stoff mit `flap.gdshader` (flattert im Wind), Farbe «*…» = leuchtet, 12. Feld = Rolle (bewegliches Teil:
  «fruit» oder ein Drehpunkt aus «piv»), «w» als Zahl = °C, «steal» / «wind» / «lure» / «fx». `coco` "" = die KI kennt es nicht.
  objects.gd: `Obj.def(kind)`, `Obj.kinds()`, `Obj.cats()`; inventar.gd nimmt diese statt `Obj.OBJ` / `Obj.CATS` (Kachel «KI: –»).
- **`scripts/objekte_plus.gd`** (Knoten `main.objplus`, `user://objekte_plus.json`): `on_placed(n, kind)` (aus inventar.add_object) gibt
  jedem Ding sein Verhalten: Wind (`main.wind * gust()`): Früchte fallen (ab 22 km/h, liegen dann und locken Reh / Wildschwein / Igel),
  Hängematte, Windspiel, Ballon, Tonnendeckel, Gartentor, Plastiksack (wandert), Stoff über `main.cloth_mats`. Licht: Strassenlampe /
  Laterne / Solarleuchten über `main.lamps` / `main.lamp_mats` (nachts an), Lampe mit Bewegungsmelder (45 s nach der letzten Bewegung
  in 8 m), Fernseher flackert (18:30–0:40), Kerze / Lagerfeuer flackern (+ Funken). Rauch / Dampf / Bienen (CPUParticles, Gruppe «smoke»).
  Hühner am Hühnerstall (picken, nachts im Stall). **Wertsachen** kommen in `main.test_props` (Name wie die Kachel, z. B. «Kamera»,
  zweite «Kamera 2») → «Bewachte Sachen», Referenz-Scan, Spielziel «Diebstahl». Handy, Handtasche, Laptop (objects.gd) auch (`STEAL_OLD`).
  **Lockmittel:** Futternapf, Abfallsack, offene Kühlbox, Obst auf dem Tisch, Mülltonne, Chipstüte → `send_lure()`: passendes Tier
  (nachts Fuchs / Wildschwein / Marder / Dachs / Igel, tags Katze / Eichhörnchen / Reh) kommt, schnüffelt / wühlt 14–30 s, geht.
  Von selbst nur mit «Besucher von selbst» (Schalter Besuch → Verhalten «Tiere kommen absichtlich …», Knopf in «Tiere schicken»).
- **Spiel «Diebstahl»** (gameplus.gd / gamewiz.gd): Auswahl «was wird geklaut?» + alle Wertsachen (`gamewiz.theft_opts()`); fehlt die
  gewählte Wertsache, stellt `objplus.ensure_valuable()` sie neben das Zelt. «zufällig» nimmt auch hingestellte Wertsachen.
  `gameplus.theft_info(nm)` statt `THEFT_OBJ[nm]`. MoveEye merkt das Fehlen wie bisher über Referenz-Scan / Vergleich.
- **`scripts/umgebung.gd`** (Knoten `main.umgebung`, `user://umgebung.json`, `on_scene()` nach simreal): Schalter in
  Kamerabild → Schwierige Bedingungen (u_lamps Lampe mit Bewegungsmelder + Fenster mit Fernseher, u_reflect Pfützen spiegeln +
  Spritzer, u_smoke Rauch / Dampf / Funken / Nebelschwaden, u_insects Mücken-Schwarm, u_doors Gartentor + Mülltonne im Bild),
  Wetter → Natur und Wind (u_plants fallende Blätter Sep–Nov, Schnee fällt in Böen von den Ästen; u_tracks Spuren im Schnee / Matsch
  bleiben, MultiMesh 600; u_steps Schritte auf Kies / Laub / Schnee → `add_sound`), Besuch → Von selbst (u_vehicles).
  Was ins Bild stellt (u_lamps, u_doors, u_insects, u_vehicles) ist **aus**, damit der Prüfstand vergleichbar bleibt.
  Neue Besucher (main.spawn → `umgebung.spawn_kind`): `e_trotti`, `rollstuhl` (Personen: actor.gd-Varianten «escooter» /
  «wheelchair»), `delivery_bot`, `robomower` (keine Personen, eigene Fahrer), `cat_fence` (Zaun + Katze, simreal-Track «roof»),
  `chickens` (Hühnerstall), `hedgehog_bowl` (Futternapf + Igel). Grafik «einfach»: keine Partikel, keine kleinen Lichter.
- **Prüfstand-Plan «gegenstaende»** (testrun.gd, «props»: true): `objplus.test_place()` stellt TEST_SET (18 Dinge, 2 mit COCO-Namen: Futternapf, Campingstuhl)
  vor die Kopfkamera, Phasen Tag mit Böen / Dämmerung / Nacht IR, Besuche «lure» (Tier zum Lockmittel) und Roboter (zählen nicht als
  Wahrheit). Bericht `szene` = `{art: gegenstaende, dinge, ki_kennt, ki_kennt_nicht, lockmittel_tiere, lockmittel_angekommen,
  push_falsch, push_richtig}`. pruefstand.py kennt den Plan; GitHub nur sonntags (pruefstand.yml), nicht in «quick».
- Test-Aktionen: `{"action": "objekte", "do": info | lure | test_place | test_clear | set}`, `{"action": "umgebung", "do": info |
  set (key, value) | spawn (kind) | snow_puff | clear_tracks}` (nicht in schnittstelle.json: MoveEye braucht sie nicht).
- main.gd: nur Knoten, `on_scene`, `spawn`-Haken, `add_controls`, zwei Aktionen. actor.gd: zwei Personen-Varianten + `_animate_ride`.

## NEU in 3D-4.20 (MoveEye 2.98.49): Simulator «wie echt» – Lautsprecher, Servo-Störungen, Thermal-90 (`simint.gd`)

- `scripts/simint.gd` (Knoten `simint` in main.gd, eigene Datei `user://simint.json`), Antwort an MoveEye über net.gd (`rep.merge(simint.reply())`, nicht in world_reply):
  - **Lautsprecher:** `mw.sound` (MoveEye 554 schickt jetzt die echte Art: siren / two-tone / beeps / horn / whistle / bangs / chime / birds / marmot / tts / talk, dazu `sound_vol`) wird am PC als einfacher Ton gespielt (Licht & Ton → Lautsprecher, bis 3D-4.21 Sensoren: Lautstärke, «Am PC stumm»; Schalter «Geräusche» gilt auch). Das simulierte Mikrofon hört ihn am Gerät (`add_sound`, -2 dB bei 100 %), Pieps / Knall zusätzlich als `sound_ev` «clap» (n = 3, alle 2 s) – MoveEye muss das ignorieren. Fliehen bei Sirene: unverändert (on_state, _update_visitors).
  - **Störungen** (Karte Testen → «Störungen», Gruppe Testlauf / Teil «Störungen», auch in der Simulator-Steuerung von MoveEye): `stoer_uv` (5 V erzwingen), `stoer_pca` (PCA9685-Reset: Kopf steht, bis `mw.servo.reinit` steigt), `stoer_i2c` (5 s), `stoer_block` (pan / tilt klemmt), `stoer_off`. 5-V-Schiene aus `simwerte.volts` (unter 6.8 V sackt sie ab, Servo-Strom -0.18 V), Unterspannung unter 4.63 V: Servos 35 % Tempo und kurze Stopps (`servo_k`, `hold` in der Kopf-Nachführung von main.gd). Antwort `servo_sim` {v5, uv, i2c, pca_reset, pca_hold, blocked, head_mw}.
  - **Wärmebild-Modell** (Kamerabild → Wärmebild): «Thermal-90 (Waveshare)» Standard (80 × 62, 90° × 67°, 15 Bilder/s, NETD 125 mK; Datenblatt Waveshare / Core Electronics: 90° H × 67° V, bis 25 fps, 125–150 mK) oder «45°-Modell (alt)» (45° × 35°, 8 Bilder/s). Gerendert 160 × 106 (nicht quadratische Pixel), `decode_thermal_img` tastet nach Bildgrösse ab, Rauschen `randfn(0, th_noise)`; /info `thermal` = `simint.thermal_info()` (mit model / name / netd_mk), jede Antwort `thermal_model`. testrun.gd nimmt fov_v des Modells.
  - **Warme Hand** (`warm_hand`): Hand + Unterarm (34 / 33 / 32.5 °C) 2 m vor der Kopfkamera, langsame Acht – für MoveEye «Wärmebild ausrichten» (557), schaltet MoveEye selbst ein und aus.
  - Test-Aktion `{"action": "simint", "do": info | uv (on) | pca | i2c (s) | block (axis) | off | model (m) | hand (on)}`.
- main.gd: nur kleine Stellen (TH_FOV jetzt var + th_fps / th_noise, Knoten, Kopf-Nachführung, info(), GROUPS-Teile, Testen-Unterkarte, Aktion «simint»).
**NEU (Entwurf, Zweig wt-aufr, Aufräumen 2):** eine Feldliste `simulator3d/schnittstelle.json` (world_reply, state, info,
control) für beide Seiten – neue `scripts/schnittstelle.gd` prüft sie 2 s nach dem Start (Log «Schnittstelle: OK …» oder
«SCRIPT ERROR: Schnittstelle: …»), MoveEye im Selbsttest (Teil 558). Neues Feld = eine Zeile in der Liste. world_reply sendet
nicht mehr `sim_time` (= clock), `active` (bei Verbindung immer an), `weather` (= forecast.weather); `humidity` geht in den
Klima-Sensor von MoveEye, `sim_cpu_own` in die Kachel «CPU des PCs», `leader` in die Meldung «schaut nur zu». Von MoveEye
neu `ups_mah` (power.gd: «Kapazität einer Zelle» bei Verbindung nur lesbar, `controls[i]["ro"]`), nicht mehr `picture_mode`
und `simtask`; `armed` und `relays` stehen in der Statuszeile (schnittstelle.gd `mw_extra`). `smalltv.gd game_live()` ist
die eine Quelle für SmallTV, TV-Anzeige (MoveEye 150) und den TV-Modus (`tv.gd`); dazu Farbe, Ziel, Adresse, Verlauf,
Rangliste, Aufgabe, Sieger, «als Nächstes». Kommentare zu Einfach/Experte (MoveEye speichert es jetzt für die Seite «sim»).

## NEU in 3D-4.19 (MoveEye 2.98.48): virtueller SmallTV (`smalltv.gd`, Plan `docs/SmallTV_Anzeige_Plan.md`) – gleiche HTTP-Schnittstelle wie das Gerät auf dem Simulator-Port, Kachel, Macken-Schalter, Zähler im Prüfstand.

## NEU in 3D-4.18 (MoveEye 2.98.47): Neue Szenen (szenenplus.gd, Branch wt-szenen)

- `scripts/szenenplus.gd` (Knoten `szenen` in main.gd) baut drei Szenen (statisch `build_scene`, aus scenes.gd): **Voller
  Campingplatz** (`camping_voll`: dein Platz mit Pfosten und Seil vorne, Weg, Nachbarreihe, WC-Haus, Spielwiese),
  **Tarnen und Kriechen** (`tarnen`: trockene Wiese in den Farben der Tarnkleidung, hohes Gras, Büsche), **Velodieb**
  (`velodieb`: Veloständer im Bild, Hecke mit Lücke zur Strasse). Liste `Scenes.LIST`, `AUTO`, `EXTRA_HIDE`, `Scenes.EN`
  (englische Namen, MoveEye übersetzt sie, Teil 551), templates.gd (grün = neu).
- Nachbarn (`camping_voll`): Figuren von actor.gd / figur.gd **unter dem Szenen-Knoten** (nicht in `visitors`): bleiben bei
  Testläufen und Spielrunden, sind nie «Wahrheit»; 22:30–6:30 schlafen sie, nur die WC-Gänge (mit Lampe) gehen weiter.
- Besuch-Arten (`main.spawn`, Knöpfe unter «Besuch → Abläufe»): `platz_besuch`, `tarn_robben` (Tarnkleidung über
  `Actor.npc_camo`), `tarn_schirm` / `tarn_karton` (dieselben Dinge wie im Spiel, `gameplus.dress`), `velodieb` (löst
  `add_event("Velo", "tag")` aus, schiebt eine Kopie des Velos weg, das echte ist so lange versteckt).
- Testläufe (testrun.gd): Pläne mit `"scene"` (laden die Szene, danach zurück) und `"dists"`; `_cause` meldet «Nachbar»;
  Bericht `szene` (Reaktion ab Platz / ab Griff, Pushes wegen Nachbarn, pro Tarn-Art). CONTROL `{"action": "szenen"}`.
- Spiel: Ziel pro Szene (`szenen.goal_key`), im Assistenten eine Karte «Spiel zur Szene» (Presets `szene_voll`,
  `szene_tarnen`, `szene_velo`); Tarnkleidung wirkt in «Tarnen» stärker (0.6 statt 0.8), Bots nehmen dort immer ein Ding;
  in «Velodieb» immer das Velo, beim Greifen meldet der Velo-Sensor.

## NEU in 3D-4.18 (MoveEye 2.98.47): Simulator-Werte für MoveEye (power.gd, Branch wt-simwerte)

- `scripts/power.gd` (Knoten `simwerte` in main.gd): simulierter USV-HAT (2 × 18650, Kapazität pro Zelle, Ladung jetzt,
  Netzteil, Solarpanel-Watt; Verbrauch aus Pi + CPU von MoveEye + Servos + Licht + Ton, Laden mit `solar_reading()`, Kälte senkt
  die nutzbare Kapazität), Pi-Temperatur im Gehäuse (Aussentemperatur + Last + Sonne, Test «Lüftung blockiert»), Test
  «WLAN weg» / «Internet weg», Tageszähler über Mitternacht (Zeitraffer). Einstellungen in `user://simwerte.json`.
- `world_reply()` hängt `simwerte.reply()` an: `battery`, `pi_temp`, `net`, `clock` (date, hour, speed, tz_h), `place`
  (lat, lon, name wie `sun_pos`), `forecast` (gust_kmh, weather, storm, tmax, tmin). MoveEye: Teil 285.
- Regler: Karte Sensoren → «Akku und Strom» (mit Statuszeile) und «Netz-Ausfall testen» (auch in der Simulator-Steuerung von MoveEye).
## NEU in 3D-4.18 (MoveEye 2.98.47): Verfolgungs-Parcours (`parcours.gd`, Plan `docs/Verfolgungs_Parcours.md`)

- Szene `parcours` (Wiese, Distanzmarken 5/10/20/40 m, Busch, Zelt, Auto, Baum, Ring 8 m schaltbar), gebaut von
  `parcours.build_scene` (Aufruf in `scenes.gd`). Lektionen 1–7 als Puppen-Besucher (`actor.puppet`) mit festen Wegen, 8 = nachts mit IR.
- Wahrheit pro Lektion (20 Hz, Echtzeit über `main.now()`): Zielfehler, Zeit im Bild, Verluste / Wiederfinden, Pendeln /
  Überschwingen, Servo-Weg, Verwechslungen → Note 1–6, Ergebniskarte, Einblendung (Weg, Blickstrahl `laser.gd`, Fehlerkurve).
- Steuerbefehl `{"action": "parcours", "do": info | start (lessons, night, seed, prep_s) | stop | state | result | overlay | ring |
  pics | card | game (name, bot, secs) | steer (x, z, run) | game_stop}`. `busy_with()` meldet «Verfolgungs-Parcours».
- Spiel «Entkomme der Kamera» (Punkte in `game.board_add_extra`), Lernbilder unter `user://parcours/lernbilder/` →
  `dataset.gd` (`add_to_pack`). Fenster: Karte «Testlauf» → Teil «Verfolgungs-Parcours».
- Texte «feste Kamera» für die zweite Wächter-Ansicht heissen jetzt «Weitwinkel-Kamera» (game, gamerules, gameshutter,
  planner, testrun).

## NEU in 3D-4.17 (MoveEye 2.98.46): Balance-Paket 30.10.2026 + KI-Wächter, Stange-Regler, nacktes /sim-Bild

Spiel-Balance nach dem Code-Review (von Daniel freigegeben, Punkte 1, 3–11 und 12 teilweise):
- **Eine Punkte-Regel für alle Wächter** (`gameshutter.score_catch`, `game.guard_score`): jeder Fang zählt sofort so, wie er
  angezeigt wird (Auslöser 100–300, sonst 150), derselbe Schleicher nochmals in der Runde 50 % / 25 % / 0 %, jeder Fehlalarm
  einmal −50, am Schluss + 200 × Anteil «nicht im Ziel». Die Endzeile rechnet es vor («… = N Punkte»). Kein doppelter Abzug mehr.
- **Schuss auf Geschützte** (gerade erwischt, Startschutz) ist neutral: keine Punkte, keine Energie, Hinweis «schon erwischt» /
  «Startschutz». Der KI-Autopilot zielt nicht auf Geschützte (Rahmen-Feld 5 in `gamekihilfe.boxes`).
- **Startschutz** (`spawn_protect`): nach Start/Neustart geschützt, bis 6 m vom Start weg oder 6 s um.
- **Zwei Stufen:** Schleicher-Stufe = `game_level`, Wächter-Stufe = `game_glevel` (gamerules, «auto» = wie Schleicher-Stufe).
  Leichter Wächter = grosser Kreis **und** 130 ⚡ (0.5/s), schwer = kleiner Kreis **und** 70 ⚡ (0.3/s); normal unverändert.
- **Verzögerung Handy-Wächter:** Treffer werden gegen Kopf und Schleicher von vor 0.25 s geprüft (`_hist`). Der Wächter bekam
  nie das kleine 320×180-Bild (das gilt nur für Schleicher-Ansichten), jetzt im Code vermerkt.
- **Busch-Hüpfen:** Verstecken hat eine Wartezeit pro Person (4 s nach früh raus, 10 s nach «zu lange»), für alle Büsche.
- **Ein Text** für Stufen und Wächter (`gamerules.LEVEL_TXT`, `GLEVEL_TXT`, `GUARD_TXT`) im Assistenten und in den Einstellungen.
- **Profil «Wie echte Hardware»** (`game_real`, Standard aus): nur die eine feste Kamera zählt – kein Drehen, keine feste
  zweite Kamera, keine Wärmebild-Kamera, kein Mikrofon, kein Licht/IR, keine Sirene; im Assistenten «nur Simulator».
  `gamelearn` schreibt `"profil": "echt" | "simulator"` in Bericht, verpasste Bilder, Schleichwege und blinde Flecken.
- **Sieger pro Rolle:** Endbild mit bestem Wächter und bestem Schleicher plus Team-Ergebnis (`win.roles`, `win.team`);
  «Rollen reihum – wer am wenigsten erwischt wurde» vergleicht jetzt per Platz (nicht Name) und nennt die Anzahl.
- **«Team gegen Team» entfernt**; gespeichertes `teamguard` wird beim Laden zu `guard`.
- Beim Rundenstart werden auch die Sperr-Ringe und das Schuss-Protokoll für MoveEye geleert.

## Wer und wie

- Daniel aus der Schweiz, kein Programmierer.
- Immer **auf Deutsch** antworten, mit **«ss» statt «ß»**.
- Kurz und verständlich bleiben. Ehrlich sagen, was **nicht getestet** ist.
- Ausgeliefert wird eine **fertige Windows-.exe als ZIP**, kein Quellcode zum Selberbauen.
- Der Ziel-PC: älterer Intel i5, 16 GB RAM, Windows, NVIDIA- oder AMD-Grafikkarte.
- Bedienung über das PC-Fenster **und** über die Motion-Watch-Webseite (CONTROL-Protokoll).

## Was es ist

Ein 3D-Simulator (Godot 4.3) auf einem Windows-PC. Er spielt für Motion Watch (Raspberry Pi 5) die Hardware nach:

- Kopfkamera auf Schwenk-/Neige-Servos, feste zweite Kamera, Wärmebildkamera (80×62);
- weisses Licht und Infrarot, Tag/Nacht, Wetter, Wind, Sensoren;
- Besucher: Menschen, Tiere, Auto, Dieb;
- ein Handy-/Tablet-Simulator (Taste P), der die echte Motion-Watch-Webseite über ein unsichtbares Edge/Chrome anzeigt.

Seit 3D-1.9 gibt es **«Motion Watch auf diesem PC»** (`scripts/mwpc.gd`): Damit das Handy ohne Pi etwas zeigt, läuft das echte
Motion Watch unsichtbar neben dem Simulator. Beim ersten Mal: Python 3.12.7 für Windows aus python-build-standalone (GitHub,
`PY_URL`/`PY_SHA`), ausgepackt mit `tar.exe` von Windows; `pip install` von `PKGS` (PyPI); dann jeweils die neuste Datei aus
`versions.json` (geprüft mit deren SHA-256, **nicht** mit der Signatur). Start: `python.exe <datei> --headless --config <…>/config
--port 5000 --bind 127.0.0.1`; die Einstellungen `sim_on`, `sim_url`, `sim_auto=False` schreibt Python selbst (Godots JSON
macht aus ganzen Zahlen Kommazahlen). Alles unter `user://motionwatch_pc`. Unter Linux nimmt es das System-Python
(`--mw-python`), `--mw-base http://…/` ersetzt GitHub (Test: `python3 -m http.server` im Repository).
Grosse Downloads unter Windows mit **curl.exe** (Teil von Windows 10/11: Windows-Zertifikate und -Proxy, folgt der Weiterleitung von
github.com zu release-assets.githubusercontent.com); Godots HTTPRequest ist nur Ersatz – in 3D-1.9 scheiterte damit der
Python-Download bei Daniel («Fehler 0» = keine Verbindung). Fehlertexte nennen jetzt den Grund (`RESULTS`).
`--mw-test-python` lädt und entpackt das Windows-Python auch unter Linux (mit curl über den Proxy getestet: Download,
SHA-256 und tar gehen). Die Webseiten-Prüfung fragt mit HEAD (die Startseite ist ~400 KB), Wartezeit bis 5 Minuten.
Nur `sim_on` reicht nicht: Motion Watch suchte dann weiter eine USB-Kamera («NO CAMERA FOUND», schwarzes Handy-Bild). `_settings()`
setzt darum wie der Schalter «Simulation» auch `source = sim:0`, `thermal_source = sim:thermal` und `sim:1` in `extra_cams`.
Das Handy startet ab 3D-1.11 mit der normalen Startseite (Knopf «Vollbild» = nur Live-Bild).
**Handy-Eingaben (3D-1.13):** `Input.dispatchTouchEvent` erzeugte keinen Klick (Schalter wie «Marks» reagierten nicht, der
Joystick bewegte sich nicht). Jetzt `Input.dispatchMouseEvent` (mousePressed / mouseMoved mit `buttons: 1` / mouseReleased) –
die Seite bekommt Pointer-Ereignisse und Klicks. **Wichtig:** In der Sitzung mit `setDeviceMetricsOverride` teilt Chrome die
Eingabe-Koordinaten durch den deviceScaleFactor, darum CSS-Punkte × `DSF`. `DSF` ist jetzt 1 (ein Viertel der Bildpunkte, das
Handy wird ohnehin kleiner als 390 px gezeichnet), Screenshot JPEG 65 mit `optimizeForSpeed`, alle 150 ms.
Läuft noch ein Browser eines früheren Laufs auf Port 9333 (Profil gesperrt), wird er weiter benutzt (`_browser_running`).
Getestet mit dem Chromium von Playwright (`/opt/pw-browsers/...`, Option `--browser`) und Klicks per XTest: Marks ein/aus,
Joystick Pan 35 % → 99 %. Das PID von Motion Watch auf dem PC steht in `motionwatch_pc/mw.pid` (zum Stoppen nach Wiederverwenden).

**Bedienfeld (3D-1.13)** im Stil der Motion-Watch-Webseite: `scripts/ui_style.gd` (Farben `--bg #0a0e14`, Karten `#151e2b`,
Rand `#1f2b3a`, Akzent `#3b8cff`, gesperrte Grossbuchstaben als Überschrift, ▸/▾ grün). Karten: Verbindung, Kameras,
Werkzeuge, dann je Gruppe der Regler (Knöpfe nebeneinander), Tasten. **Virtuelle Maschine** (`main._in_vm()`, auch llvmpipe):
Grafik «einfach» und weniger Vorschaubilder. Motion Watch auf dem PC: `sim_fps` 4 (wenn noch 6), `sim_eco` an.
Gewehr geht beim Verlassen der Wildbeobachtung von selbst aus.
Unter Linux getestet bis «verbunden mit Motion Watch» und Webseite auf 127.0.0.1:5000; **unter Windows nicht getestet**
(Python-Download, tar, pip, Motion Watch selbst unter Windows).

**Daniel testet in einer VMware-Maschine** (Log: «VMware, Inc. – SVGA3D», Mesa 24.1). Deren OpenGL lehnt die Godot-Shader ab
(«declarations for uniform `world_transform` have mismatching invariant qualifiers»), sichtbar ist nur der Himmel; Vulkan geht
dort gar nicht. Ab 3D-1.8 erkennt `main._vm_needs_angle()` die virtuelle Grafik am Namen und startet einmal neu mit
`--rendering-driver opengl3_angle` (Kennzeichen `--angle-tried`, abschalten mit `--no-angle`). Godot 4.3 gibt Grafik-Optionen
beim Neustart nicht weiter (`OS.get_cmdline_args()` ist dann leer) und kennt `get_current_rendering_driver_name()` noch nicht.
Unter ANGLE **nicht getestet** – falls es auch so nicht geht: in VMware die 3D-Beschleunigung prüfen, sonst echte Hardware.

Seit 3D-1.7 **aktualisiert sich der Simulator selbst** (`scripts/update.gd`): Vor dem Bau der Welt lädt er
`simulator3d/version.json` von GitHub (`{"version", "file", "size", "sha256", "notes"}`). Ist die Version neuer, zeigt er
«Jetzt aktualisieren» / «Ohne Update starten». Beim Aktualisieren: ZIP nach `user://update.zip`, Grösse + SHA-256 prüfen,
Dateien neben die .exe legen, die laufende .exe in `.old` umbenennen, neue hinlegen, mit denselben Optionen plus `--updated`
neu starten (die `.old` wird beim nächsten Start gelöscht). Ohne Antwort nach 6 s startet er normal. `--no-update` schaltet es ab,
`--update-url http://…/` nimmt eine andere Quelle (zum Testen mit einem lokalen `python3 -m http.server`).
Der Programmpfad wird **vor** dem Umbenennen gemerkt (unter Linux zeigt er danach auf die `.old`).
Ab 3D-1.12 gibt es den Knopf **«Nach Updates suchen»** (`main.check_updates()`, `Updater.manual = true`: meldet auch
«schon die neuste Version» / «GitHub antwortet nicht»). Das Update-ZIP lädt unter Windows **curl.exe**; Godots HTTPRequest
nur als Ersatz, mit `download_chunk_size` 1 MB (mit 64 KB pro Bild dauerte es bei laufender Simulation viele Minuten).
**3D-3.16 bis 3D-3.36** wurden in einem anderen Chat gemacht (siehe Git-Geschichte und «Lies mich.txt», Abschnitte «NEU IN …»).

**NEU (Entwurf für 3D-4.17, Zweig wt-weit):** neue `weitwinkel.gd` – die frühere feste Kamera (cams[1]) ist die **Weitwinkel-Kamera**
(Camera Module 3 Wide NoIR, 102° × 67°, 640×360 / 8 Bilder/s, nur gerechnet wenn abgerufen) mit Montage `scene` (Mast, wie bisher,
Standard) · `base` (Unterteil vorne, fest, Neigung −12°) · `head_front` · `head_rear` (dreht mit, Versatz 180°), auf dem Kopf nur
mitschwenken oder auch mitneigen; Fischauge (camfx `distort`), NoIR-Look, eigenes IR-Bild nachts, zweites IR-Licht 120°
(`lights.ir_wide`, PCA9685 Kanal 4 bei MoveEye) an der Montagestelle. Kopf-Montage: Drehgrenze ± 170° (Kabel, Schleifring für
360°-Servos) und etwas trägerer Kopf (`servo_k`). `/info` cameras[1] meldet `mount`, `tilt_deg`, `yaw_offset`, `pan_follow`,
`tilt_follow`, `fov_h/fov_v`, `on_head`; die Antwort auf POST /state hat `wide` (MoveEye 163 sieht Wechsel sofort). Einstellungen:
Kamerabild → «Weitwinkel-Kamera» (`wide_mount`, `wide_tilt`, `wide_tilt_follow`, `wide_fisheye`, `wide_pan_limit`, `wide_heavy`;
`cam1_yaw` = Richtung am Mast). Steuerbefehl `weit` (mount …, `do: probe | spawn` für den Prüfstand). Der zweite Gerät-Simulator
(`device.gd`) hat weiterhin seine feste Kamera.

**3D-4.16:** neue `gamekihilfe.gd` (KI-Hilfe: Rahmen, zielen, Autopilot; `ki_hilfe` im Spielbericht, Runde ohne Wertung), Steuerbefehl «ki». **3D-4.15:** neue `figur.gd` (Skelett 15 Knochen, Körper aus Ringen, im Code gebaut, keine fremde Lizenz – `LIZENZEN.md`), `thermal_vc.gdshader`, `actor.gd` treibt die Knochen, `vielfalt.vary_person`, Steuerbefehl `figuren` (Test). **3D-4.14:** neue `padmap.gd` (eine Controller-Belegung, Kopie in MoveEye 542 `window.MWPad`, Selbsttest vergleicht), `padhud.gd` (Fadenkreuz, Mini-Karte), `padroles.gd` (mehrere Controller), `toolbar.gd` als Symbol-Dock. **3D-4.13:** `gamelearn.gd` Wahrheit 3 s gepuffert, Rahmen aus Meshes, `fa_box` mit Personen in der Nähe / erwarteter Höhe / Kopf ruhig, `fa_pruefung` im Spielbericht (MoveEye 2.98.42 Teil 148 sortiert nach `fa_learn/zweifel/`). **3D-4.12:** neue `gamerules.gd` (Rollen reihum, Fairness, Infos für Schleicher, Siegerbild), `gametools.gd` (Wächter-Energie), `gamecompare.gd` (Mensch gegen KI, Steuerbefehl `game_compare`); `tunnel.gd` lässt 8770/8771 (Spiel-Ports) durch; `_fold_all("groups")` öffnet nur «Kameras». **3D-4.11:** neues `gameshutter.gd` (Auslöser: Trefferkreis nach Schwierigkeit, `shut` in `world_reply` → Test-Postfach von MoveEye, Steuerbefehl `game_shut` für Tests); Kopf fährt mit gesendeter Geschwindigkeit weiter, `head_deg` in `world_reply`. **3D-4.10:** neues `padview.gd` (nacktes Bild für die Controller-Ansicht von MoveEye 2.98.32, Ansichtswechsel). **3D-4.9:** `main._mw_lead()` (ein MoveEye führt: `uid` aus dem Zustand, `helper` gibt nach, 4 s Stille = Wechsel; andere bekommen `follower`/`leader` und kein `mw_cmd`, `mw_watchers()` in der Verbindungs-Zeile); Controller in `localplay.gd` (über `explore.stick()`), Gamepad-API auf der Spielerseite in `game.gd`, `pad` {hold} nur für Tests. **3D-4.8:** `tunnel.gd` `inst` = «Startzeit-PID» in der Anmeldung «MWTUN1 code inst»; MoveEye 2.98.26 nimmt nur Leitungen des neuesten Fensters (`_tun_instance_ok`). **3D-4.7:** Karte «Spiel» nur Assistent/Start/Stopp (Einstellungen im Assistenten, Gruppen-Kennung `gid` für MoveEye), «Bewachte Sachen» = alle `test_props` in «Dein Platz» (über `set_prop`), Unsichtbar-Trank (früher Tarnkappe). **3D-4.6:** `zwilling.gd` + `inventar.gd` = ein Fenster «Dein Platz» (interne Namen bleiben), Zelt als Gegenstand, `game_teams` folgt dem Spielziel (nur «Fahne erobern»), Spielart «Team gegen Team» aus der Auswahl; neues `kidaten.gd` (Pakete aufräumen: 3 neueste, 30 Tage). **3D-4.5:** neues `gameplus.gd` (Wetterwechsel, Tarn-Sachen, Ziel Diebstahl mit refscan/refcompare über `mw_request`, Lern-Punkte; `user://spiel/extras.json`), Steuerbefehl `gameplus`. **3D-4.4:** neue `simreal.gd` (Pi-5-Modus, Objektiv, IR, Wärme; `user://simreal.json`), `zwilling.gd` (Dein Platz, `user://zwilling.json`), `flap.gdshader`, `kitrain.gd` (KI trainieren, Token über `pruef._token()`, braucht Actions: Read/Write), `dataset.gd` Vielfalt normal/hoch + `labels_meta/`; neue Besucherarten hooded, backpacker, phoner, group2–4, edge_sneak, deer_bedded, dog_leash, boar_herd, cat_roof; `camfx` Nachzieh-Bild nie heller als das neue. **3D-4.3:** neues `gamejaeger.gd` (Spielart Fehlalarm-Jäger, `fa_box` mit `info`); `testrun.gd` Pushes richtig/falsch aus `mw_det.pushes` (MoveEye 2.98.19 Teil 068), Wärmebild-Wahrheit (cams[2]), Pläne `nacht` und `echtenaechte` (`res://pruefnaechte/`), Seeds; `pruefstand.gd` Knöpfe Schleichwege senden / Alarm-Rückblick als Fall; `replay.gd` merkt die letzte Spur. **3D-4.2:** Unterteil «Diebstahlschutz prüfen» in «Testen» (vorher «Schutz testen»). **3D-4.1:** neue `gamexp.gd` (Stufen, `user://spiel/stufen.json`), `gamebots.gd` (Bots, Bot-Wächter `game_botguard`), `gamewatch.gd` (Zuschauer-Tipps, Köder); `gamewiz.apply_preset()` (Schnellstarts, auch für kids.gd und explore.set_invite); Ziel «Sprint»; Steuerbefehle `game_debug`, `busy` (eine Sperre mit MoveEye 2.98.14, `busy_with` kennt Aufgaben von MoveEye). Karte «Testlauf» in «Testen». `main.ir_ex` (eigene Belichtung des Infrarotbilds in `_auto_exposure`), `camfx` Nachzieh-Bild nie heller als jetzt, `colors.gd` Bodennebel 0.04, `dataset.gd` wartet auf ruhige Belichtung. **3D-4.0:** `testrun.gd`: `mult` (Steuerbefehl `test_start` {mult}), `_route()` (Wege quer durch das Bild von `cams[0]`, Abstände nach Tag / Nacht mit Licht), `visible()` verlangt auch freien Körper, `SETTLE` 15 s, Bericht hat `mult` und `realism`. `pruefstand/pruefstand.py`: `--mal`, `--realismus an,aus` (Schlüssel `<plan>~roh`), Szene `stellplatz`, Vergleich erst ab 8 Personen. `quick.gd` ohne Kacheln patrol / head, `toolbar.gd` «Rover-Route» / «Folgen». `main.no_emoji()`. **3D-3.99:** `net.start()` tut nichts, wenn schon auf diesem Port gelauscht wird (vorher: zweiter Aufruf aus `tunnel.set_on` → `call_deferred(set_stream)` → «already in use», `listening` false, Simulator stumm). `realism.ae_target()` am Tag ≥ 0.28, `noise_scale()` am Tag ≤ 1.8. **3D-3.98:** `release_ports()` schaltet den Tunnel ab (`_released_t`; `_stream_watch` schaltet ihn nach 20 s wieder ein, falls das Update abbricht). `emit_sound(kind, n, pos)` / `sound_events()` → `sound_ev` + `sound_ev_last` in `world_reply` (MoveEye 2.98.11 `sim_sound_events()`), Steuerbefehl `sound`. `solar_reading()` / `gps_reading()` / `gps_steal()` → `solar`, `gps` in `world_reply`, Steuerbefehl `gps`. `device.gd`: eigene Wärmekamera (`cams[2]`, `_capture_thermal`, `main.decode_thermal_img(img, false)`), `world_reply` ohne `mw_cmd` / `sound_ev`. `moon_auto` / `moon_phase()` (Sky-Uniform `moon_phase`), `CITY_SCENES` (Lichtglocke), `colors._ground_tick()` (wetness, puddle → Shader-Uniform `puddle` in grass / terrain, Bodennebel über `env.fog_height_density`), neues `scripts/tracks.gd` (Spuren im Schnee), `realism.thermal_fx()`. `no_emoji()` für Knopftexte im Fenster. **3D-3.97:** neues `scripts/colors.gd` (`main.colors`, `colors_on` / `seasons_on`): `add_mesh` nimmt `colors.material_for(albedo, kind)` (natürliche Farbe `natural()`, Oberfläche aus `KIND` nach Wärme-Schlüssel), `update()` aus `_update_sky` setzt Gras / Laub nach `month()` (`GRASS`, `LEAF`; `scenes.foliage()` Meta «broad» = Laubbaum), Nässe bei Regen, blaue Stunde, Dunst. `realism.gd`: engere Grenzen, Dämmerungs-Entsättigung, `cnoise` / `seed` in `camfx.gdshader`, warmer Weissabgleich bei Lampen. `explore._axis()` → `stick(st)` (runde Totzone um `pad_center`, ohne Controller null), `_learn_rest()` (3 s ruhig → neue Mitte, `main.pad_auto`), neues `scripts/padtest.gd` (Steuerbefehl `pad_test`), `main._no_pad_ui_nav()`; `_head_tick` (L1 + rechter Stick / Steuerkreuz → `mw_look`). MoveEye 2.98.10 schickt die rohen Achsen. **3D-3.96:** Szene `schlafzimmer` (`scenes._schlafzimmer()`, `data.bed`), neues `scripts/sleeper.gd` (Figur im Bett: sleep / wave / sit / up / turn / gone, `auto` reagiert auf `mw.wake` {state, snoozes, t0} von MoveEye 2.98.9 – jede neue `t0` = neues Klingeln; Steuerbefehl `sleeper`), keine Insekten im Schlafzimmer. Neues `scripts/laser.gd` (`main.show_laser`, KEEP, Leiste Ansicht «laser»; Strahl + Bildränder aus `cams[0]`, HELPER_LAYER). `explore._axis()` zieht `main.pad_center` ab und nimmt `main.pad_dead` (KEEP), `explore.calibrate()` misst 2 s die Ruhelage (Knopf `pad_cal`). Slider-Extra `tip`. **3D-3.95:** `game.MAX_P` = 16 Plätze, `main.game_max` (2–12, KEEP) = Läufer; Rolle «watch» (Zuschauer: Kopfkamera-Bild wie der Wächter, keine Figur, keine Wertung), `runners_n()`, `qual()` (ab 5 Läufern «small»), `_promote_watchers()` (alle 0.5 s in der Lobby). `spectator_info()` hat `url`, `max`, `runners` (MoveEye 2.98.7 «Spiele freigeben»). Slider-Extra `tip` = Tooltip. **3D-3.94:** neues `shaders/camfx.gdshader` (Quad zwischen Belichtung und Linse, liest die Bildschirm-Textur: trail = Anteil des letzten Bilds `prev_tex`, `pan_blur`, soft, sat, con, tint, noir) und `scripts/realism.gd` (`before_capture` / `after_capture`, `stats()` = gleiches Mass wie `quelle/146_echt_abgleich.py`, Anpassung alle 8 s an `mw.real_look` {day, night}, `user://echt_abgleich.json`; `ae_target()` in `_auto_exposure`, `noise_scale()`, `jpg_q`). Servo: Totband 0.6°, Nachschwingen (`_srv`), `pan_vel` / `tilt_vel`. Neues `scripts/fauna.gd` (Vögel / Fledermäuse, ruhen bei `measuring()`, `fauna_on` in KEEP). `actor.gd`: elderly, Shorts, Mantel, Schirm, Velolampen (`bike_lamp`), Lampen schwenken, Idle «stare», Augenleuchten × Blickrichtung. `kids_ask`. **3D-3.93:** Leiste «Ansicht» hat `zones3d` / `det3d` (schalten `show_zones3d` / `show_det3d`); die Kacheln dafür in der Simulator-Zentrale von MoveEye sind weg (Steuerbefehl `overlay` bleibt). **3D-3.92:** `game.BADGE_FILE` (`user://spiel/abzeichen.json` {name: {badge: n}}), `badges_all()`, `_badges_save()`; Abzeichen `spotter` (`learn.blind_s` ≥ 10 s). `gamelearn` setzt bei jedem `mw_false` `mw_cmd` op «fa_box» {box} → MoveEye 2.98.2 `fa_game_box()` schneidet den Ausschnitt nach `fa_learn/`. Steuerbefehl `blindmap` {do: game} liefert auch `badges`. **3D-3.91:** `main.mw_follow_on()` / `mw_following()` (aus `mw.servo.track` / `tracking`, MoveEye 2.98.1), `mw_track(on)` = `mw_cmd` op «track»; der Kopf folgt MoveEye statt der Patrouille, solange `mw_following()`. Leiste: «follow» = «Verfolgen» in `MAIN_ROW`, inventar / templates nur noch als Kacheln. **3D-3.90:** `_simple_ok(c)` / `SIMPLE_GROUPS` / `SIMPLE_HIDE_SUBS` in `_order_controls()` setzen «expert» (Einfach ≈ 60 Einstellungen); `extra.hide` = nur für die Webseite (dev_updates, auto_update, update_now → `update_mode`). `_mode_row` (oben) mit Einfach/Experte und Kinder/Erwachsene. Karte «Testen» (früher Werkzeuge), `night_test`-Knopf entfernt. `testrun.DAUER` = einzige Quelle für Plan-Dauern; `pruefstand.gd` liest Namen über `preload(testrun.gd)`. `_thumbs_tick` zeichnet nur Sichtbares, animiert nur unter der Maus (`_thumb_drawn`). `gamewiz.MODES` 5. Feld = alt (nur Experte). `gamelearn.blind_pts` (az° wie blindmap, d m; `user://spiel/blinde_flecken.json`), Steuerbefehl `blindmap` {do: game}; Zonen-Check-Hinweise im Modus free. `dataset._add_game_misses()` nimmt die verpassten Spielbilder ins YOLO-Paket. **3D-3.89:** `main.measuring()` (Test / Messung → `patrol.command()` gibt ZERO, der Kopf folgt der Patrouille nicht), `main.typing()` (LineEdit/TextEdit hat den Fokus → Pfeile, WASD, Flug ruhen), `main.head_owner()` (für `headpad.gd`). Erkunden ↔ Patrouille schliessen sich aus. `game.gd`: `_patrol_was`, `_mover_was` / `_rig_was` (seek), `scene_saved` (Tagesaufgabe) werden in `end_round()` zurückgestellt. `_perf_orig` / `_perf_auto`: «automatisch leichter» wird nicht gespeichert (`_save_settings` schreibt die eigene Wahl). **3D-3.88:** `main.busy_with(except_)` = wer die Welt gerade hat (Testlauf, Prüfstand, Trainingsbilder, Blinde Flecken, Fehlalarm nachstellen, Spielrunde, Wiedergabe). Solange belegt: `life.gd` echte Zeit / echtes Wetter, `_night_weather_tick`, `surprise`, Scheinwerfer (ausser Test), `_dev_check` / `auto_update`, `_perf_tick` ruhen; `testrun.start`, `blindmap.start`, `dataset.start`, `game.start_round`, `whatif`, `farecreate` lehnen ab. `visitlog` hat `src` (normal | game | replay), Testbesucher werden nicht eingetragen, ohne MoveEye (`mw_t` > 10 s) wird nichts gemessen. **3D-3.87:** neues `scripts/wordmark.gd` (Schriftzug W6 als SVG-Text, `texture(height)` über `Image.load_svg_from_string` – keine Import-Datei nötig; im Kopf des Bedienfelds statt Logo + «3D-Simulator Live»). **3D-3.86:** neues `scripts/objects.gd` (`OBJ`: alle COCO-Klassen, die nicht Besucher sind, als Grundformen-Daten [Form, Masse, Lage, Farbe, Drehung], `build(main, kind)`, `CATS`, `COCO_VISITORS`), neues `scripts/inventar.gd` (Fenster mit Reitern, Kacheln mit Bildern – Besucher aus `main.thumbs`, Dinge einmal in einem SubViewport gerendert –, `place_kind = "obj:<kind>"` → `_place_at` → `place_at_screen`; `user://objekte.json` {szene: [{k, x, z, r}]}, `rebuild()` nach jedem `set_scene`; Steuerbefehl `inventar` {do: info | open (tab) | close | add (kind, x, z, r) | clear}), neues `scripts/quick.gd` (Schnellzugriff oben im Bedienfeld, Kachel-Menüs mit `PopupMenu`), `toolbar.gd` eine Zeile `MAIN_ROW` (Text = Knopf, Liste = Menü), neue gezeichnete Symbole in `ui_style.gd` (clock, box, map, head, puzzle, phone, meter, route, plan), `mini.gd` zeigt `mw_logo.gd` statt «3D». **3D-3.85:** Makeover 21–25: neues `scripts/blindmap.gd` (Steuerbefehl `blindmap` {do: start (az, dist, hour, walk) | info | stop}; Person an jedem Punkt, `found` = `mw_det.persons` > 0, `inview` = `testrun.visible` mit Kopfkamera; `auto_visitors` aus solange); `main.farecreate()` (Steuerbefehl `farecreate` {cause: animal | wind | light | rain | car | other | end, hour, pan_deg, rain}). **3D-3.84:** Makeover 16–20: `device.gd` Plätze `door` / `bike` / `car` (`NAMED`, `_named_target()`, `set_scene` ruft `dev2._put()`); `patrol.gd` `goto_point(p, why)` (Mission alarm | dock | goto: hin, umschauen, zurück zu `home_pos`, dann alte Route), `batt` (−0.05 %/s, < 20 % → dock, lädt 1 %/s an der Station), `_dock_tick()` (Ladeplatte in `scene_parent`), `alarm_point()` (erster Rahmen von MoveEye auf den Boden, sonst 8 m geradeaus), `rover_info()`; Steuerbefehl `rover` {do: info | patrol (on) | alarm | dock | goto (x, z)}. **3D-3.83:** Makeover 8–11: neues `scripts/overlay3d.gd` (auf `HELPER_LAYER`; Zonen aus `mw.zones` – Punkte 0..1 der Kopfkamera, mit `project_ray_*` von `cams[0]` auf den Boden; Patrouillen-Punkte `mw.waypoints` [pan°, tilt°]; Rahmen `mw_det.boxes` → Besucher in 3 m = grün, sonst rot, Personen gut im Bild ohne Rahmen = orange; `main.show_zones3d` / `show_det3d` in `KEEP`), Steuerbefehle `whatif` {hour, weather, kind, n, pan_deg, dist} (`main.whatif()`), `twin` {name, lat, lon | op: info} (`twin_info()`), `overlay`. MoveEye 2.96.5 schickt `zones` / `waypoints` im Zustand und schreibt `situ` in die Aufnahme-Info. **3D-3.82:** neues `scripts/templates.gd` (Fenster «Vorlagen», `main.templates`, Werkzeugleiste `templates`): Reiter Szenen / Orte / Bausätze / Eigene Datei; `import_file()` kopiert .glb (bzw. wandelt .gltf um) nach `user://vorlagen/`, Liste `vorlagen.json` {file, x, z, rot, scale, auto}; `place_into(root)` (aus `scenes._vorlage()`) stellt die Modelle auf den Boden, `auto` = Einheit geraten (>300 m → cm), Hindernisse aus den Mesh-AABBs (max. 250, nicht flach / nicht hoch oben); `get_window().files_dropped` → Szene «vorlage». Steuerbefehl `templates` {do: info | open | import | drop | remove | adjust}. Neue Szenen `bauernhof`, `seeufer`, `baustelle` (`test_props["Werkzeugkiste"]`), `stellplatz`, `vorlage` mit `_fence()`. **3D-3.81:** `dev_updates` (in `KEEP`, Standard an) + `_dev_check()`: jede Minute GitHub-API «commits?path=simulator3d/version.json» mit ETag (304 zählt nicht ans Limit), neuer Commit → `run_update(true, false)`; `update.gd` hängt `?t=` an die version.json (am Cache vorbei). MoveEye 2.96.2 schaltet `update_fast` einmalig ein (`dev_phase_done`). **3D-3.80:** neues `scripts/visitlog.gd` (`main.spawn()` meldet jeden Besucher, Auswertung alle 0.5 s mit `testrun.visible` nur Kopfkamera und `mw_det`), Steuerbefehl `visits` {since} → MoveEye 2.96.1 holt alle 30 s (`355_simulator_tagebuch.py`, `sim_diary.jsonl`, `/api/sim_diary`). **3D-3.79:** Name MoveEye (früher Motion Watch) in allen Texten; `mw_logo.gd` zeichnet das neue Logo (Sichtfeld, gehende Person mit Erkennungs-Ecken), `icon_sim3d.png` neu. Interne Namen (`mw_*`, Dateien, Ports, `mwsim`) bleiben. **3D-3.78:** `gamewiz.gd` im Fenster neu (`_draw_prog`, `_card`, `_group`, `_option_row`, Gleiten über `_slide`-Ränder); Modell unverändert (4 Schritte, Motion Watch zeigt sie gleich), Schritt 3 hat `PLAYER_OPTS` (Bots usw.); `wizpics.gd` hat Bilder `seek`, `patrol`, `free`. **3D-3.77:** Spieler haben `kind` (phone | local | bot); `game.state_for(p)` (früher in `_send_state`), `add_local()` / `remove_local()` / `set_bots(n)`, `_bots_tick()`; neues `scripts/localplay.gd` (eigene CanvasLayer 30, Ansicht = `p.vp` bzw. Kopfkamera, Tasten, Herzschlag, Wiederholung `_draw_replay`), Steuerbefehl `localplay` {do: start | stop | key, role}. Wiederholung: `rec` / `rec_ev` → `replay` (Nachricht `rp`, Handy fragt mit `replay`). Abzeichen `BADGES` / `_badges_of()`. Geister `user://spiel/geister.json` (Ebene 16, nur Spieler), Tagesaufgabe `daily_plan()` / `user://spiel/tagesaufgabe.json`, Übungsrunde `TUT` / `_tut_tick()`. Spielart `seek` (`_seek_start`, `seek_drive` → `rover_pad.command()`, `seek_hiding()`). Neues `scripts/headpad.gd` («Kopf steuern» → `main.mw_look()` / `mw_light()` über `mw_cmd` op look | light, Motion Watch 2.95.103). Einstellungen `game_bots`, `game_tutorial`, `game_daily`, `game_ghost`, `game_heart` (in `KEEP`). `mini.gd` kompakt (330 × 84). **3D-3.76:** `patrol.ask()` (Frage «Was soll überwacht werden?», `places()`, Klick-Modus `edit = "pick"`), `guard_start()` / `plan_round()` (Ring um den Ort, Punkte ≥ 1.2 m von Hindernissen über `main.blocked()`, Umwege bei `_way_blocked`), Kopf zielt auf `guard.c`; Steuerbefehl `patrol` {guard: [x, z, r, name] | ask}. Uhrzeit: `hour_now` / `hour_at` / `speed_now` in den Einstellungen (alle 20 s und in `release_ports()` gespeichert). Spiel: Nachricht `leave` (Handy-Knopf 🚪, `lvBox`), Pakete werden vor dem Schliessen gelesen. `main.tree_spots` (Kronen aus `scenes.tree()`), `main.view_free()`, `game.clear_start()` und kürzere Kamera in `_steer`. `main.restart_args()` gibt `--old-pid` mit; `_stream_watch()` (3D-3.75) stoppt den alten Prozess. **3D-3.75:** neues `scripts/surprise.gd` (Überraschungsnacht: `start(kind)` power | fogbank | distract | glare | still, `_watch()` vergleicht `mw_det.persons`, Licht und Sirene mit der Wahrheit `_truth_person()`, `morning()` → Bericht + `user://ueberraschung/*.json`; `main.surprise_on` in `KEEP`, `main.power_off` schaltet `lamps` / Fenster / Türlicht aus; Steuerbefehl `surprise` {op: get | on | off | start, kind | morning}). Grafik: `view_scale` (`scaling_3d_scale` nur der grossen Ansicht), `win_fps` (Engine.max_fps bei offenem Fenster), `auto_perf` + `_perf_tick()` (< 14 Bilder/s während 20 s → eine Stufe leichter). `tunnel.gd`: `_fail()` mit wachsender Wartezeit (3–15 s), Leerlauf-Leitungen leben 40–55 s (`RECYCLE`), Pipe ohne Verkehr 180 s → zu; Motion Watch 2.95.101 nimmt die neuste Leitung und verwirft Leitungen älter als 100 s (`TUN_MAX_AGE`). `pruefstand.gd`: `auto` (`user://pruefstand/auto.json` {on, last}), `_auto_tick()` startet `start(["quick"], 1)` bei neuer `mw_version` (90 s nach dem Auftauchen, 180 s ohne Klick, kein Spiel / Testlauf / Überraschung), sendet mit Schlüssel; Steuerbefehl `pruefstand` {do: auto, on, last, touch_ago}. **3D-3.74:** `cond` hat neu `fogged` / `dirt` (Uniforms in `lens.gdshader`), `shake` (dreht `cams[0]`) und `net` (`_net_hold`: JPEGs bleiben stehen). Besucher `sneaker` (`events.sneaker()`, Meta `sneak`; Route-Haltung `crouch` ≥ 1.5 = kriechen in `actor.gd`; Licht → erstarren, Lampe aus; Sirene → `fled`). `night_weather` + `_night_weather_tick()` (Plan pro Nacht, Tau setzt `cond.fogged` 4–8 h). `kids.gd`: Missionen (`_mission`, `_mission_check` auch bei verstecktem Feld, `_won` → `main.kids_stars` in `KEEP`; `main._say(..., lay)` mit `HELPER_LAYER`). **3D-3.73:** Szene `zuhause` (`scenes._zuhause()`, `home_item()` mit `HOME_KINDS`/`HOME_LINES`/`HOME_DEFAULT`) aus `main.home_items` (`user://zuhause.json`, `home_load/save/rebuild`); Baukasten `scripts/home_editor.gd` (Klick = setzen, `_unhandled_input` → `home_editor.handle_input`), Steuerbefehl `home` {op: get | set | edit}. `dataset.export_pack(n)` schreibt ein YOLO-Paket nach `user://trainingsbilder/<zeit>/` und ein ZIP auf den Schreibtisch (`EXPORT_CLASSES`, mehrere Besucher pro Bild, Haltungen, leere Bilder, Szenenwechsel alle 60 Bilder); Steuerbefehl `dataset` {op: export, n}. **3D-3.72:** `test_props` (Name → Knoten, von `scenes.gd` im Camping-Platz gesetzt: Velo, Zelt, Tisch, Kühlboxen, Grill) + `set_prop()`; `set_sabotage(cover, turn)` (schwarzes Tuch 0.36 m vor dem Kopf – hinter der Near-Plane – bzw. `sabotage_turn` auf den Schwenk); `ref_night_test()` mit `_night_test_tick()` (day0 → day: refscan → night0 → night: `refcompare_day`); Planer-Knopf «Hierhin stellen + Referenz-Scan»; Steuerbefehle `prop`, `sabotage`, `ref_night_test`. **3D-3.71:** Anfragen an Motion Watch: `mw_request(op)` legt `mw_cmd` {id = Unix-ms, op: refscan | refcompare | refstop} in die Antwort auf `/state` (`world_reply`); Motion Watch führt sie einmal aus (`SIM.cmd_seen`) und meldet den Stand in `mw.refscan` (busy, step, n, ref_n, last, cmd_seen) → `refscan_text()` in den Werkzeugen. `set_bike()` / `bike_node` (Testhilfe), Steuerbefehle `mw_request` {op} und `bike` {on}. Neue Anfragen an Motion Watch immer über `mw_cmd`. **3D-3.70:** Steuerbefehl `shoot` {x, y, who} → `main.mw_shot()`: in einer Runde `game.mw_catch` (mwhand) bzw. `game.shot_at` (alle anderen Spielarten), sonst Strahl aus `cams[0]` durch (x, y) gegen `hit_spheres()` der Besucher; Treffer: Menschen `scare()`, Tiere `hit()`; daneben: `mw_shots.false` + Fehlalarm. **3D-3.69:** neues `scripts/kids.gd` (Kinder-Bedienfeld: Kacheln mit `thumbs` bzw. gezeichneten Symbolen, Murmli in `_draw_marmot`, Töne als erzeugtes `AudioStreamWAV`, Konfetti als ColorRects mit Tween auf eigenem CanvasLayer). `main.kids_on` / `kids_scary` / `kids_thief` / `kids_laser` / `kids_sound` (in `KEEP`), `_apply_kids()` blendet alle Kinder von `ui_box` ausser `kids` und `kids_seg` aus, `ask_adult()` (Rechenaufgabe), `spawn()` ersetzt Wildtiere / Diebe nach Einstellung, `game.hit_fx` ohne Laser nach Einstellung, `UI.segment` legt `meta "paint"` ab. **3D-3.68:** `main.release_ports()` (net.stop, Spiel-Server zu) vor jedem `OS.create_process` des Simulators selbst (Update, ANGLE-Neustart): Windows vererbt sonst den Lausch-Port, der neue Simulator meldet «Port 8765 is busy». `_stream_retry(60)` nimmt nach 8 Versuchen `ALT_PORTS` (8775/8785/8795); Tunnel leitet «GO 8765» auf `net.port`; Beacon meldet den Port. Kinder wie `mwpc` (Python) können den Port weiterhin erben – darum der Ausweichport. **3D-3.67:** `/view.jpg?clean=1` setzt `view_clean_t`; 3 s lang zeichnet `rover_pad.gd` nichts (`modulate.a = 0`, Maus durch, `_over_hud` überspringt unsichtbare Boxen) – `visible` bleibt, sonst stünde `command()` (Patrouille, Erkunden, Browser-Controller) still. **3D-3.66:** `patrol.handle_input()` im Modus «points» gibt Klicks an die Ansicht weiter (Punkt nur bei Klick < 8 px Bewegung, `_click_at`), Rechtsklick nur auf einem Punkt; Esc setzt `patrol.edit = ""`; `toolbar.gd` zeigt dann `_hint` mit «✓ Fertig (Esc)». Getestet mit XTest (`/tmp/claude-0/menu/xin.py`). **3D-3.65:** `stream_last` (in `KEEP`, nur vom Schalter gesetzt) startet das Senden wieder; `_stream_retry(30)` versucht `net.start()` jede Sekunde, solange der Port nach einem Update noch besetzt ist. **3D-3.64:** `HELPER_LAYER` (128) in `main.gd`: Hilfsmarken nur für den Bediener (`view_cam.cull_mask = 1 | HELPER_LAYER`), die Kameras für Motion Watch (Maske 1 | Linse) sehen sie nicht – Patrouillen-Pfosten/-Linien/-Nummern und die Empfangskarte. Neue Hilfsmarken immer auf diese Ebene legen. **3D-3.63:** `mw_logo.gd` bewegt nur noch die Pupille (±4.5 von 100). Motion Watch 2.95.88 legt das Wärmebild in der Simulation nach `fov_h` / `w` / `h` aus `/info` passend ins Kopfkamera-Bild (`ThermalCam.sim_geom()` / `fit()`) – `TH_FOV` oder die Auflösung ändern ist also unkritisch, solange `/info` stimmt. **3D-3.62:** neues `scripts/mw_logo.gd` (oranges Motion-Watch-Symbol im Kopf des Bedienfelds, gezeichnet in `_draw()`, die Pupille wandert in 6 s links/rechts; gleiche Bewegung wie `APP_ICONS_ANIM["classic"]` in Motion Watch). **3D-3.61:** neues `scripts/patrol.gd` (Route Punkte/Bereich, `command()` geht über `rover_pad.command()`, `head_yaw` überschreibt den Kopf, `user://patrouille.json` je Szene, Steuerbefehl `patrol`), neues `scripts/toolbar.gd` (Werkzeugleiste unten, alles per Maus), Spielart `patrol` (`mw_decides()` mit `patrol_judge`). **3D-3.60:** `place_rover_at()` / `place_kind = "rover"`; Spielart `free` (kein Schiedsrichter, 6 h, startet von selbst sobald jemand da ist); `explore.set_invite()` (QR), `explore.spectator()`; `_spectate_explore()` (Ziele Rover + freie Spieler) und `_spec_free()` (freie Sichtlinie, sonst von oben), Spiel-Einstellung «group»; Steuerbefehl `explore` {invite, spectate, place}. **3D-3.59:** Steuerbefehl `pad` {ax[4], bt[17] (Standard-Belegung, Trigger als Wert), name} → `explore.remote_pad()`; gilt 0.6 s, `_axis()` nimmt das Grössere von Browser und eigenem Joypad. **3D-3.58:** `/view.jpg?w=&q=&fmt=webp` → `main.view_request()` (Breite 320–2560, Qualität, WebP; `view_mime`); solange ein `/view.mjpg`-Strom offen ist, bleibt es JPEG. **3D-3.57:** `mast_h` / `set_mast()` (Stange, gespeichert; `HEAD_H` bleibt der Standard). **3D-3.56:** `explore._blocked()` (Hindernis ≥ 1 m Höhe nahe der Linie Rover–Ansicht) → `auto_top` nach 0.3 s, zurück nach 1.5 s frei. **3D-3.55:** neues `scripts/explore.gd` (Erkunden mit dem Rover: setzt Mover an, Panel weg, eigene Kamera hinterher / Fahrer / oben; Eingabe-Gerät aus `_input`; Joypad über `Input.get_joy_axis`; `rover_pad.command()` nimmt `explore.command()` dazu; `_fly` ruht; Steuerbefehl `explore` {on, view, drive}). **3D-3.54:** `testrun.ways()` nur Wege der aktuellen Szene (Leitlinie: Daten kartenunabhängig, Kartengebundenes nur auf seiner Karte). **3D-3.53:** `mw_det.boxes` (0..1, Kopfkamera) von Motion Watch: `gamelearn.reported_for(p)` ordnet Meldungen Spielern zu (`overlap`), `mw_false` = Rahmen ohne Spieler/Besucher; `_mw_referee` mit `MW_HOLD` / `MW_PAUSE` je `game_level` (easy: Kriechen sicher); `sneak_list()` / `records.blind`; `dataset.load_game()` (Steuerbefehl `dataset` op `game`) für die KI-Prüfung in Motion Watch. **3D-3.52:** Treffer-Sequenz in `game.gd` (`hit_fx`: Laser / Farbe / Blitz nach `game_fx_*`, Handy `hitFx()`; der Spieler bleibt 0.9 s stehen, dann `_to_start`), `mw_catch(who, x, y)` = Antippen im Livebild (Box aus `gamelearn.box()`), neues `scripts/gamelearn.gd` (verpasste Bilder, Spielbericht, Schleichwege in `user://spiel/<runde>/`, Bonus `blind`, Senden nach `feedback/spiel/`), Testlauf-Plan «spielwege» (`testrun.gd`, Wege aus `res://spielwege/` und `user://spiel/`). Steuerbefehl `game_test` nur für Tests. **3D-3.51:** die Karte «Kameras» liegt jetzt in der Liste direkt unter «Verbindung» (nicht mehr im festen Kopf; bleibt beim Suchen sichtbar, weil sie nicht in `top_cards` ist). **3D-3.50:** `UI.fold_active(body, st)` färbt Symbol und Pfeil einer Karte (0 grau, 1 grün, 2 orange) – der Pfeil zeigt den Zustand der Funktion, nicht mehr «offen»; Namen bleiben weiss. Gruppen über `group_active()`, dazu Kameras (verbunden) und Werkzeuge (Motion Watch / Prüfstand / Trainingsbilder läuft). **3D-3.49:** neues Fenster `scripts/pruefstand.gd` (Werkzeuge → Prüfstand, Steuerbefehl `{"action":"pruefstand","do":"get|open|start|send"}`): misst ein Motion Watch auf dem PC mit den Plänen von `testrun.gd` (nur Kopfkamera), schreibt `user://pruefstand/<datum>_<version>.json` im Format von `pruefstand/ergebnisse/` und sendet per GitHub-API (PUT contents, Schlüssel in `user://pruefstand/schluessel.txt`) oder legt die Datei auf den Schreibtisch. Datei-Modus: `mwpc.gd` `override_file` startet eine gewählte webcam_bewegung_X.py statt der eingebauten. **3D-3.48:** `test_start` nimmt `cams` ([0] = nur Kopfkamera zählt für die Wahrheit); der Bericht hat `visitors` (Art, Grösse px, Licht, Erkennungszeit) für `pruefstand/pruefstand.py` im Repository. **3D-3.47:** Tunnel-Zeile zeigt «Ziel: host:8766». **3D-3.46:** Unterteile (`UI.sub_fold`) ohne Einträge aus `ui_items` brauchen `set_meta("always", true)`, sonst blendet `_apply_simple()` sie aus – so war das Tunnel-Feld unsichtbar.

**3D-3.45 – Tunnel:** `tunnel.gd` hält ~10 Verbindungen zu MW:8766 offen (Hallo `MWTUN1 <code>` → `OK`); auf `GO <port>`
(8765 Simulator, 5057 KI-Rechenhilfe) verbindet es sich zu 127.0.0.1:<port> und reicht die Bytes durch (Rest nach der GO-Zeile
nicht verlieren!). MW: Türen 127.0.0.1:18765 / 15057, stellt `sim_url` von selbst um. KEEP: tunnel_host/code/on; CONTROL `tunnel`.

**3D-3.44 – Helfer für Motion Watch:** `mwpc.gd` startet MW mit `--helper` und fragt `/helper/hello` (Port 5057); `info()`
gibt `helper` {port, code} an den Pi. `tv.gd` (CanvasLayer 5, blendet `ui_layer` aus, CONTROL `tv`, Taste T). `planner.gd`
(Abdeckung mit `line_free`, `set_home`/`home_pos`, CONTROL `planner`). `replay.gd` (CONTROL `replay`, Geisterfigur, Kopf über
`replay.servo`). `show_netmap` (CONTROL `netmap`). `dataset.gd` (CONTROL `dataset`, `/dataset/<i>.jpg` in net.gd; Bilder über
die normale Bildschleife mit `snap_want` – nie selbst `_capture` aufrufen; Besucher mit fernem Ziel, sonst geben sie sich frei
→ Absturz). Gruppensymbol-Zustände gehen als `groups_on` an die Seite.

**3D-3.43 – Rand, schwebende Kamerabilder, grüne Symbole, Pi-Build:** `_palette_item` mit Zeilenumbruch, Panel
`grow_horizontal = BEGIN` (Test-Aktion `ui_wide` listet zu breite Teile). `show_panel(false)` hängt die Karte «Kameras» in
`cam_float` (Griff-Leiste, `cam_fx`/`cam_fy` in KEEP). `group_active()` / `_paint_groups()` färben die Gruppen-Symbole.
`apply_visit_preset` räumt auf, setzt `PRESET_HOUR` und schickt sofort Besuch. Export-Vorlage «Linux Pi» (arm64, ETC2),
ZIP `MotionWatch3D_Pi.zip` mit «Start auf dem Pi.sh»; `version.json` hat dazu `pi`. `update.gd` sucht auf Linux-ARM nicht
selbst (Motion Watch bringt die Pi-Version). Auf echter Pi-Hardware ungetestet.

**3D-3.42 – Bilder im Spiel-Assistenten:** `wizpics.gd` (SVG-Zeichnungen pro Karte, `texture()` über `Image.load_svg_from_string`);
das Modell schickt sie als `pic` / `pics` mit, Motion Watch zeigt sie als `data:image/svg+xml`. Text in den SVG zeigt nur der Browser.

**3D-3.41 – Spiel-Assistent im Simulator:** `gamewiz.gd` (Fenster-Teil + Modell `model()` / `op()`); CONTROL-Aktion
`{"action":"gamewiz","op":"get|open|close|pick|set|extras|next|back|last", "key", "value"}`. `main.control_set(id, value)` setzt eine
Einstellung wie «set». Motion Watch (2.95.48) rendert das Modell im Reiter Simulator (`gwOp`, `gwPaint`, Abfrage alle 1.5 s).
«Wie letztes Mal»: `user://gamewiz_last.json`. Im Fenster ohne Emoji (`plain()`), Motion Watch zeigt sie.

**3D-3.40 – Abläufe und Stimmungen:** `events.gd` (in main als `stories`): burglar, bbq, homecoming(parcel), fox_trash, boar_group,
kids_tag, mowing, night_lapse; Helfer `_later` (Zeitgeber, nur gleiche Szene) und `_watch` (wartet auf eine Bedingung über `main.anims`).
Besucher mit Meta «shy» fliehen vor weissem Licht / Sirene (`_life`). `VISIT_PRESETS` Feld 7 = eigene Besucherliste (`preset_kinds`).
`life.calendar()` (Wochenende, Jahreszeit; Schalter `calendar_on`). Neue Teile «Fahrzeuge» und «Abläufe» in der Karte Besuch.

**3D-3.39 – Mehr Besucher:** `actor.gd`: `PERSON_VARIANTS` (cyclist, stroller, drunk, courier, police → kind «person» + variant,
`_person_extras`, `_animate_cyclist`), `CAR_VARIANTS` (tractor, moto, van → kind «car», `_build_tractor`, `_build_moto`), neue Tiere in
`_build_animal` (cow, sheep, horse, chamois, ibex, lynx). `main.visit()`: couple, horse_walk, cows, sheep_flock, courier, police, drunk,
cyclist, bats / owl (`_night_flyers`, keine Besucher, nur Bewegung). `life.activity()` und `Scenes.AUTO` kennen alle.

**3D-3.38 – Besuch neu gegliedert:** Teile in `GROUPS` («Vorlagen», «Besucher hinsetzen», «Menschen schicken», «Tiere schicken»,
«Fahrzeuge und Abläufe», «Von selbst», «Verhalten»); `VISIT_PRESETS` + `apply_visit_preset()` (Auswahl `visit_preset`);
`VISIT_EMOJI` → `extra.emoji` (Seite von Motion Watch zeigt es vor dem Knopftext); Knöpfe im Fenster mit Bildchen (`thumb_btns`).
Test-Befehl `ui_scroll` kennt `open` (eine Karte mit allen Teilen öffnen).

**3D-3.37 – Verbindung:** `fold_card` merkt sich `head` und `icon` (Meta); `_draw_group_icon` nimmt die Farbe aus `get_meta("col")`.
`_update_status()` färbt Symbol und Titel der Karte `conn_body` (aus / wartet / verbunden).

**3D-3.15 – Mover-Stick im Simulator:** `rover_pad.gd` (Control unten rechts, nur bei `mover_on`; Ziehen oder Pfeiltasten →
`main.pad_drive` (vor, rechts) + `main.pad_on`; überstimmt in `_drive()` die Befehle von Motion Watch; «Hinterher» = Verfolgerkamera).
Achtung: `pad_on` ist ein Bool pro Bild (keine Zeitschwelle – mit langsamer Grafik dauert ein Bild > 0.3 s).
3D-Gebäude-Diagnose: `b3d.diag` → `geo.b3d_diag`, Datei `user://orte/3d_gebaeude_bericht.txt`, Anzeige in Schritt 2; gzip ohne
Kopfzeile wird entpackt (`_unzip`). Motion Watch 2.94.4: `mover_sim_show` = Stick in der Simulation auch ohne Mover (nur Anzeige).

**3D-3.14 – Orts-Assistent:** `karte.gd` Schritte 1–3 (`step`, `_show_step`, `_page_env`, `_page_objects`, `_build`); lädt mit
`geo.load_place(..., rebuild=false)` und baut erst bei «Szene bauen» (`main.place_loaded()`). `geo.detect_env()` (Häuser im
Umkreis 150 m, Anteil Wald / Wasser / Wiesen / Siedlung im 10-m-Raster, Fluss, Höhe) → `geo.env`, `env_why`.
`geo._env_props(env)`: `ENV_PROPS` pro Umgebung, Autos entlang kleiner Strassen (`park_segs`), Boote / Schilf am Ufer (`water_polys`).
Einstellungen `ort_env` / `ort_hide` / `ort_cars` / `ort_forest` / `ort_camp` (KEEP). Test-Befehl `{"action":"wizard","op":"pick|next|set"}`.

**3D-3.13 – Verstecke:** `scenes.gd`: `prop(kind, p, rot)` (15 Arten, jede mit Hindernis + `set_obstacle_height`),
`hide_props(n, dmin, dmax, kinds, keep_clear)` (Abstand ≥ 3 m zu Hindernissen, nicht auf Strasse / `data["clear"]` z. B. Teich),
Szene `verstecken` (`_verstecken`), `EXTRA_HIDE` = zusätzliche Verstecke pro Szene nach dem Bau.

**3D-3.12 – Übersichtskarte:** `minimap.gd` (Control im UI-Layer, zeichnet `obstacles`, Kamerakegel, Besucher, Spieler, Ziel, Luftbild),
`map_on` / `map_size` / `map_span` (KEEP), `set_map()`, Taste M, Knopf «Karte».

**3D-3.11 – Mover und Mini-Kästchen:** `rig` (Basis von Motion Watch, Elternknoten von `head`) + `chassis` (Kettenfahrzeug);
`mover_on` / `mover_max` (KEEP), `_drive()` liest `mw.drive.l/r` (−1 … 1, von Motion Watch 2.94.0), echte Zeit seit dem letzten Aufruf
(Bilder werden zum Sparen ausgelassen), Hindernisse wie Besucher, Gelände `ground_y`; Antwort an Motion Watch: `"mover": true`.
Test-Aktion `mover`. mini.gd: eigene CPU (Windows: PowerShell-Schleife über `OS.execute_with_pipe`, nur solange das Kästchen da ist;
Linux /proc), `set_tiny()` = Symbol 64 × 64 (Test: MWSIM_MINI_TEST=2). Windows-Messung nicht getestet (kein Windows hier).
Motion Watch 2.94.0: `MOVER`, `MoverControl` (PCA9685 als Motor HAT, 1600 Hz, Adafruit- oder Waveshare-Belegung, 0,6-s-Wächter,
sanftes Anfahren), `/api/mover`, `st.mover`, zweiter Stick im Web (`#mstick`, `body.mover`, Vollbild `#vo-mctl`) und im Fenster (`MoverPad`).

**3D-3.10 – 3D-Gebäude:** `b3d.gd`: `tileset.json` von 3d.geo.admin.ch (`geo.url("b3d")`), Baum ablaufen (region / box / sphere,
verschachtelte tileset.json, höchstens 40 Kacheln), b3dm (RTC_CENTER) oder glb mit `GLTFDocument` laden, glTF y-oben → z-oben →
Kachel-Transform → minus `ecef0` → Ost/Oben/Süd (Doppelgenauigkeit für die grossen Zahlen), flache Normalen passend zur Godot-Wicklung,
Haus um den Kopf weg (`keep_out`), Höhe an das Gelände angepasst (`_align`, 30-%-Wert). Shader `b3d.gdshader` (Dach/Wand nach Normale,
Fenster aus der Weltposition, nachts einzelne hell, `geo._b3d_night`). OSM-Häuser dann nur noch als Hindernisse. Nicht mit echten
swisstopo-Daten getestet (Ersatz-Server mit eigener b3dm-Datei); Draco-komprimierte Kacheln kann Godot 4.3 nicht → Rückfall auf OSM.

**3D-3.9 – Karte und Bedienung im Web:** Control-Typ `map` (`ort_map`; Wert «lat, lon», Setzen «lat, lon[, Name]» → `set_place_text`),
im Fenster ein Knopf auf `open_map`. `extra.iconk` = Name des gezeichneten Symbols. Motion Watch 2.93.16: `SIMMAP_JS` (`simMap` =
Kachelkarte swisstopo im Browser, Suche über api3 SearchServer direkt vom Handy; `simCtlBuild` = Bedienung wie im Simulator, SVG-Symbole
`SC_ICON`) – eingesetzt in SIM_PAGE und WEB_PAGE über `/*SIMMAP*/`. Achtung: `window.simCtl` gibt es dort schon (Abfrage).

**3D-3.8 – Sonne und Spiel im Gelände:** `sun_pos()` (NOAA, Ort `ort_lat/lon` sonst 46.8/8.2, `season` «today» oder Monat,
MEZ/MESZ grob nach Tag im Jahr), `sun_el()` nutzt sie, `_update_sky` dreht die Sonne nach dem Azimut (Rotation y = 180° − Azimut).
`horizon_el(az)` (Geländewinkel in 2°-Schritten, Cache `_horizon`), `sun_behind_hills()` dämpft Sonnenlicht und Wärme, `sky_mode`
LIGHT_ONLY dahinter (sonst dunkle Sonnenscheibe). game.gd: `_g()` setzt Ziel, Starts, Kristalle, Zelle, Basen auf `ground_y`.

**3D-3.7 – Kamerabilder fest:** Bedienfeld = `outer` VBox: `top_box` (Kopf, Werkzeugleiste, Karte «Kameras») + ScrollContainer mit `ui_box`.

**3D-3.6 – Maus-Steuerung:** `_unhandled_input` neu: `m_btn`, `m_grab` (Bodenpunkt), `_pan_to`, `_orbit` (Drehen um den Punkt),
`_zoom_at`, `fly_to` (Tween), `_visitor_at` (Bildschirm-Abstand), `selected` / `follow` / `_sel_action`; `_build_view_bar()` (Knöpfe,
Kompass, `sel_box`, `sel_ring`, `thermal_full` = Ansicht 3); `_view_overlays()` jedes Bild. Test-Aktion `visitors` liefert `sx/sy`.
Hinweis Xvfb-Tests: das Loslassen eines Knopfs kommt erst mit dem nächsten Ereignis an.

**3D-3.5 – Bedienfeld:** `GROUPS` (Gruppe, gezeichnetes Symbol `UI.group_icon`, Emoji fürs Web, Teile) und `PLACE` (id → Gruppe,
Teil) in main.gd; `_order_controls()` sortiert `controls` und setzt `extra.sub` / `extra.icon` (extra wird kopiert – mehrere
Controls teilen sich `ex`). Fenster: `UI.fold_card(..., icon)`, `UI.sub_fold()`, `sub_bodies`, `ui_items[4]` = Teil. Motion Watch
(ab 2.93.12) zeigt `icon` vor dem Gruppennamen und `sub` als Zwischentitel. Test-Aktion `ui_scroll` (fold, simple, y).

**3D-3.4 – Ort von der Karte:** `geo.gd` (Download mit Cache `user://orte/cache/<md5>.bin`, Kacheln WMTS 3857 swisstopo,
Terrarium-PNG, Overpass `out geom`, swisstopo profile.json 81 × 81 Punkte = swissALTI3D; lokale Koordinaten: Mercator × cos(lat),
Norden = -z; `height()`, Gebäude extrudiert mit Satteldach über dem kleinsten Rechteck, Fassaden-Shader `facade.gdshader`,
Bäume: nahe echte `tree()` (max. 380), sonst MultiMesh, Wald aus dem Luftbild bis 1.1 km), `karte.gd` (Kartenfenster, Suche über
SearchServer), Szene «ort» in scenes.gd, `main.terrain` / `ground_y()` / `ground_hit()` (Besucher, Platzieren, Sichtlinie mit
Gelände). Testen ohne Internet: `MW3D_GEO_BASE=http://127.0.0.1:8899` + Ersatz-Server (Host = erster Ordner). Test-Aktionen `geo`,
`map`. Nicht getestet: echte Server (aus der Testumgebung nicht erreichbar). Update: `_download_check` mit bis zu 3 Versuchen,
`.old2` usw. wenn `.old` gesperrt. Jogger: längere Schritte statt schnellerer Beine.

**3D-3.3 – Schatten:** `env.ambient_light_source` = COLOR (statt SKY: im Compatibility-Renderer lieferte der Himmel auf manchen
Grafikkarten kein Umgebungslicht → schwarze Schatten), Farbe/Stärke in `_update_sky()`; `sun.shadow_blur`, soft_shadow_filter_quality 3.
Test-Aktion `view` (pos, look, panel) für Bildschirmfotos.

**3D-3.2 – Fahne erobern:** `game_goal` «flag» (`flag_mode()`, nicht mit «teamguard»), `bases`, `flags` (Fahne mit
`scenes.cloth`, folgt dem Träger in `_flags_follow`), `_flag_rules()` (holen, heimbringen +500, abklatschen +100), `captures`.
Start an der eigenen Basis (`start_point`). Handy: `caps`, `flag`, Pfeil zum jeweiligen Ziel.

**3D-3.1 – Räuber/Wächter, Zelle, Team-Ziel:** `game_mode` «teamguard» (`team_mode()`, `guard_team`, `match_round`,
`match_scores`; Rollen über `_assign()`), erster Wächter = Kopf (`guard_player()`), weitere = feste Kamera (`guard_cam()`,
`guard2_watching()`, `main._wanted_fps(1)`). `game_rescue`: Zustand «jail» bei `jail` (`_build_jail`), Befreien im Referee
(1,6 m, +100 `bonus`). `game_teamgoal`: `goal_open()`, Strahl rot/grün (`_paint_goal`). Ablenkung `distract` / `_check_distract()`.

**3D-3.0 – Teams:** `main.game_teams`; Spieler `team`, `look` (`_clean_look`, `actor.look`), `cone` (Teamfarbe `_paint_cone`),
`_rebuild()` (neues Aussehen = neue Figur), `_make_actor()`. Nachrichten `team`, `look`, `sig` (`_signal`: Label3D über dem Kopf,
Ebene 16, an Teamkollegen `{"t":"sig", n, c, k, txt, ga, d}`). `team_results` in `st` als `tres`. Tarnung: KI-Erkennung × 0,8
bei Tag (nicht Parkplatz). Handy: `ov()` zeichnet nur bei Änderung neu (vorher 5×/s → Knöpfe konnten Klicks verlieren).

**3D-2.9 – Welt:** `scenes.cloth()` (Shader `cloth.gdshader`, Wind über `main.cloth_mats`), `flag()`, `laundry()`, `smoke()`
(CPUParticles, Gruppe «smoke»), `main._build_fireflies()`. Schalter `world_cloth`, `world_smoke`, `world_fireflies`.
**Wichtig:** Der Linsen-Shader las in 3D-2.6 das Bild über `hint_screen_texture` – diese Kopie enthält nur Undurchsichtiges, darum
fehlten Regen, Rauch usw. im Kamerabild. Jetzt: Belichtung über ein eigenes Quad mit `blend_mul` (`expo.gdshader`, `expo_mats`),
Farbe nachts über Kopien der Umgebung mit `adjustment_saturation` (`night_envs`: 0 = Infrarot, 0,4 = wenig Licht), Körnung/Tropfen
wieder als durchsichtige Überlagerung. Test-Abfrage `world`.

**3D-2.8 – Tiere:** `_build_animal()` mit Brust/Hinterteil (`bulk`), dunklerem Rücken, Oberschenkeln, Hals, Fuchs-Kinn und
Ohrspitzen, Schlappohren (Hund 50 %), runden Ohren (Wildschwein, Dachs). Menschen an der Tür: `_at_door()` → Arm zur Klinke.

**3D-2.7 – Figuren:** `actor._build_person()` mit Gelenken `hips` und `torso` (gegengleiches Schwingen in `_animate_person`),
Gesicht, Statur (`body_root.scale` nicht gleichmässig), Kapuze/Handschuhe, Lampe (`lamp`, `lamp_mat`, Anteil `main.lamp_share`).
Leerlauf-Arten pro Tier (`idle_kind`: graze, root, sniff, sit_up, sit, look, phone, bend), `startle()` beim Licht,
`play_emote()` für Spieler (caught, goal, throw). Reh springt auf der Flucht (`leap`), Hase hoppelt.
Zwischenversionen: `/tmp`-Skript `release.sh` (nicht im Repo): Version setzen, exportieren, ZIP, version.json, MW-Version, signieren.

**3D-2.6 – Nacht, Testlauf, Geräusche:**
- **Belichtung im Linsen-Shader:** Der Kompatibilitäts-Renderer ignoriert `CameraAttributesPractical.exposure_multiplier`
  (gemessen: Nachtbild gleich hell bei Verstärkung 1 und 8). Darum liest `lens.gdshader` das Bild (`hint_screen_texture`)
  und multipliziert nachts mit `expo = NIGHT_SCALE (0,15) × gain` (gain ≤ `night_gain`), `grey` = 1 bei IR, 0,6 nachts.
  Tags `expo = 1` (Bild unverändert, gemessen). IR-Licht `spot_range = ir_range`, `main.ir_on()` (MW oder Spiel-Wächter).
- **Motion Watch 2.93.3** schickt in `sim_state()["det"]` `persons`, `present`, `armed`, `noise`; der Simulator speichert
  `main.mw_det`. Der Simulator schickt in der `/state`-Antwort `sound_db` (`main.sound_db()`: Grundpegel, Regen, Wind,
  `sounds` aus `_update_sounds()` und `add_sound()`); Motion Watch füttert damit `AudioMonitor.feed_sim()` (nur ohne
  echtes Mikrofon) → normaler Geräuschalarm.
- **Testlauf** `scripts/testrun.gd`: `PHASES`, Wahrheit `visible()` (Kopf- oder feste Kamera, frei, ≥ 30 px Person /
  18 px Tier, Licht ≥ 0,25 über `game.light_at`), lockerer `present()` für Fehlalarme. Bericht JSON + HTML in
  `user://testlauf/`, CONTROL `test_report`. Geprüft mit einem nachgebauten Motion-Watch-Client (bekannte Meldungen):
  Erkennungen, Reaktionszeit, Fehlalarme und Ursachen stimmen. Mit dem echten Motion Watch hier: Tiere als Bewegung
  gemeldet, Personen 0 (KI-Modell in dieser Umgebung nicht ladbar).
- **Spiel:** `game_mode` «mw» (`_mw_referee`: Personenmeldung → sichtbarster Spieler), `game_goal` «return» (Beute).
- **Wolkenschatten** `cloud_shade()`, **Böen** `gust()`, Menschen schauen zum Licht (`look_at_light`).
- **Bedienfeld:** Schalter = Label (Umbruch) + CheckButton, Knöpfe `autowrap_mode`, Auswahl mit Label darüber und
  `fit_to_longest_item = false`. Test-Abfrage `ui_width` (Mindestbreite des Inhalts vs. Platz; jetzt 341 von 376 px).

**3D-2.5 – Realismus und Spiel:** Kamerabild: `shaders/lens.gdshader` auf einem Quad 12 cm vor Kamera 0/1 (eigene Ebenen 32/64,
`cull_mask` der Kameras), Rauschen aus `gain[i]` (Belichtung), Vignette, Regentropfen; Insekten = `CPUParticles3D` am
`head_pitch` (nachts, wenn Licht an). Einstellungen Gruppe «Kamerabild» (`lens_noise`, `lens_vignette`, `lens_drops`, `insects_on`).
Schiedsrichter `game.cam_sees()`: Personenhöhe in Pixeln (`VFOV`, Bildzeilen) → KI `smoothstep(18, 70 px)` × Haltung × Licht;
Bewegung = Pixel pro Sekunde × Grösse (ab 20 px); Wärmebild = Fleck ab 2,5–9 px × Temperaturunterschied; Licht `light_at()`
(Lampen `main.lamps`, weisses Licht/IR im Bildausschnitt des Kopfes, Mond). Unter 0,1 zählt nichts. Mikrofon `hearing()`.
Start bei z = −46 (dort sieht keine Kamera genug). Spielart `game_mode` «guard»: Wächter-Handy bekommt `main.latest_jpg(0)`
(`_send_guard_view`, `main._wanted_fps(0)` ≥ 8), steuert `guard_yaw/guard_tilt`, Nachrichten `light`, `catch`, `role`;
`stone` für Steine (Aufmerksamkeit `attention`), Kristalle `items`, Leben `game_lives` (Zustand «out» = Zuschauer),
Sichtkegel `cones` (Ebene 16), zufälliger Start/Ziel. Rangliste mit Wächter-Punkten (150 je Fang, −50 Fehlalarm, +100 je
Schleicher nicht im Ziel). Test-Abfrage `game` liefert auch `cams` (pro Kamera Abstand, im Bild, Verdecker, Sicherheit), `items`.

**3D-2.4 – Spiel «Unentdeckt ans Ziel»** (`scripts/game.gd`, `scripts/qr.gd`): bis 4 Handys. HTTP-Seite (`PAGE`, in game.gd
eingebettet) auf Port `stream_port + 5` (8770), WebSocket auf `+ 6` (8771, `WebSocketPeer.accept_stream`). Nachrichten: Handy →
`join {name, token}` (token in localStorage: gleicher Platz nach Neuladen), `in {mx, my, look, pitch, run, pos}` (alle 50 ms),
`frame` (nächstes Bild, Flusskontrolle), `start`. Simulator → `hello`, `st` (5×/s: Entdeckt-Wert, Ziel-Richtung, Runde, Liste,
Rangliste), `ev caught`, Bilder als binäre JPEG. Jeder Spieler hat eine eigene SubViewport-Kamera hinter seiner Figur
(`cull_mask 1|16`; Ebene 16 = nur für Spieler: Zielstrahl, farbige Kegel), Belichtung wie ein Handy (`_exposure`).
Figur = `actor.gd` mit `controlled` (`_player()`: Joystick, Rennen, Ducken, Kriechen = `prone`). **Schiedsrichter**
(`visibility()`, alle 0,2 s): pro Kamera (Kopf, fest, Wärmebild) Reichweite, Bildausschnitt (`is_position_in_frustum`), Sicht
(`main.line_free()` zum Scheitel; Hindernisse haben Höhen `ht`, `set_obstacle_height()` in scenes.gd, Zaun/Hecke 1,2 m, dünne
Kreise < 0,45 m zählen nicht), × Abstand × Haltung × Bewegung × Licht (Nacht: 0,12; IR nur Kopf 0,75; weisses Licht) × Wetter;
Wärmebild × Temperaturunterschied. Wert × 55/s × Stufe → 100 = erwischt (Blitzlicht, zurück zum Start, 3 s Schutz).
Ohne Motion Watch (`guard_auto`) dreht `game.guard_yaw` den Kopf. Test-Abfragen `{"action":"game"}`, `{"action":"game_put"}`.
Gemessen unter Xvfb/llvmpipe: Handybilder nur ~2/s (CPU-Grafik); auf echter Grafikkarte nicht getestet.

**3D-2.3 – Strom sparen:** `main._check_active()` (alle 0,5 s): `win_open` = nicht Kästchen (`mini.gd`) und nicht minimiert;
`connected()` = senden an und Motion Watch hat in den letzten 10 s `/state` geschickt oder Bilder/Wärmebild geholt. Weder noch
(und `eco_idle` an) → `sim_active = false`: `_process` endet nach dem langsamen Teil (Status, Speichern, Updates), Besucher
`PROCESS_MODE_DISABLED`, keine Aufnahmen, `Engine.max_fps = 5` (net.gd antwortet weiter und weckt ihn so). Kästchen mit Motion
Watch: `get_viewport().disable_3d = true` (grosse Ansicht aus), `max_fps = 30`, Vorschaubilder nur bei offenem Fenster.
**CPU im Kästchen:** Motion Watch misst mit psutil (`SysMonitor._shares`: eigener Prozess und – wenn der Simulator auf demselben
Rechner läuft – dessen Prozess über `pid` aus der `/state`-Antwort, Name muss «motionwatch3d» enthalten), Werte in % des ganzen
Rechners, und schickt sie in `sim_state()["cpu"] = {"total", "mw", "sim"}`. `sim` = None → Motion Watch läuft woanders (Pi).
Gemessen unter Linux/llvmpipe: Fenster 170 %, Kästchen mit MW 135 %, Pause 7 % eines Kerns.

**3D-2.2 – Start mit dem PC** (Simulator-Chat; baut auf 3D-2.1 des Haupt-Chats mit `mini.gd` auf) (`scripts/autostart.gd`): Windows-Wert `MotionWatch3D` unter
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (über `reg.exe`, kein Admin), Linux `~/.config/autostart/motionwatch3d.desktop`.
Startet mit `--autostart`: senden an, Szene vom letzten Mal (`last_scene`), kein Update-Dialog (ausser `auto_update`),
optional minimiert (`autostart_min` → `mini.gd` macht daraus das Kästchen), Motion Watch auf dem PC (`autostart_mwpc`), Bildschirm sperren (`autostart_lock`,
`rundll32 user32.dll,LockWorkStation`). **Minimiert zeichnet Godot nichts mehr** (`can_any_window_draw`) – die Kamerabilder
blieben stehen (getestet). Darum ruft `_process` dann 15× pro Sekunde `RenderingServer.force_draw(false)` (getestet mit einem
kleinen Fenstermanager unter Xvfb: Bilder laufen weiter) – Sicherheitsnetz neben dem Kästchen von `mini.gd`. «Ohne Anmelden»: echter Start vor der Anmeldung geht mit 3D nicht
(Sitzung 0 ohne Desktop/GPU), darum Sysinternals **Autologon** (Download mit curl.exe, `OS.shell_open` → UAC; Passwort
nur dort, LSA-verschlüsselt) + Sperren nach dem Start. Test-Abfrage `{"action":"window"}` (Fenstermodus, Autostart).

**Neue Einstellungen kommen von selbst in Motion Watch:** Jede Einstellung, die mit `add_control()` in `_register_controls()`
angemeldet wird, liefert der Simulator über `GET /control` mit. Die Webseite von Motion Watch fragt alle 4 s nach und baut die
Steuerung neu auf, sobald sich die Liste ändert (ab 2.92.3 bleiben offene Gruppen dabei offen). **In Motion Watch muss für neue
Simulator-Einstellungen nichts geändert werden** – nur die Typen `toggle`, `slider`, `select`, `button` (sonst Textfeld) benutzen.
`"expert": true` blendet nur im Simulator-Fenster aus. Das Desktop-Fenster von Motion Watch hat keine Simulator-Steuerung.

**3D-2.0 (grosses Update):**
- **Hindernisse** (`main.gd`, Abschnitt «obstacles»): Kreise (`add_obstacle`) und gedrehte Rechtecke (`add_obstacle_box`,
  `add_obstacle_node` im Rahmen eines Szenen-Knotens) in einem 4-m-Raster (`ob_grid`). `people_only` = Zäune/Hecke im Garten
  (Tiere schlüpfen durch). Jede Szene meldet ihre Objekte an (Bäume über `scenes.tree()`). `avoid()` biegt die Richtung um
  Hindernisse und gibt die gewählte Seite zurück (der Besucher hält sie 2,5 s, sonst pendelt er an Ecken), `keep_out()`
  schiebt nach jedem Schritt aus allen Objekten heraus. Getestet: Besucher quer durch Wohnwagen und Zelt geschickt –
  tiefste Annäherung 0,0 m, alle kamen ans Ziel.
- **Besucher** (`actor.gd` neu): Trägheit (`cur_speed`, `heading`, `_turn()`), Grasen/Umschauen (`idle_until`), Kopf- und
  Schwanz-Gelenke, Kniegelenke bei Menschen, festhängen → Umweg (`detour_until`). Neue Arten: child, jogger (Varianten von
  person), hare, hedgehog; Spaziergang mit Hund (`leader`), Rudel (`visit("herd")`), Garten-Besuch durchs Tor
  (`scenes.garden_route`). Vorschau-Modus `preview` für die Bildchen.
- **Szenen**: feinere Objekte (Wohnwagen mit Markise/Deichsel/Gasflasche, Zelt mit Aussenzelt, Velo mit Speichen, Hütte mit
  Brettern/Kamin/Holzstapel, Haus mit Fensterrahmen/Kamin, Autos mit Scheiben, Teich mit Schilf, Farne, Heu), Gras und Blumen
  als MultiMesh (`scenes.meadow()`, abschaltbar), **6 gemeinsame Laub-Materialien** statt eines pro Baum (schneller).
- **Bedienfeld**: Werkzeugleiste wie Motion Watch (`UI.icon_button` mit gezeichneten Symbolen, `UI.search_field`),
  Suche (`_search`), «nur Gruppen / alle auf / alle zu» (`_fold_all`), «Einfach | Experte» (`UI.segment`, `ui_simple`;
  Regler mit `"expert": true` im extra), Karte «Besucher hinsetzen» mit gerenderten Bildchen (`_make_thumbs` in eigener
  kleiner Welt) – anklicken oder ziehen (`set_drag_forwarding`, abgelegt über `NOTIFICATION_DRAG_END`). Schalter als
  CheckButton. Einstellungen in `KEEP` werden gespeichert (`simulator_settings.json`).
- **Neue Regler** (Gruppe Besuch): Wer kommt (`mix`), Wie oft (`visit_rate`), Höchstens (`max_visitors`), Tempo
  (`visitor_speed`), Flucht vor Licht/Sirene, Ausweichen; «Alle Besucher weg»; Grafik: Gras und Blumen.
- **Servos** drehen mit `SERVO_DEG_S` (200 °/s) statt zu springen; ab und zu ein Vogelschwarm (`_birds`).
- **Test-Abfragen** im CONTROL-Protokoll (nur für Tests, von der Webseite nicht benutzt): `{"action":"visitors"}` (Ort und
  Abstand zum nächsten Objekt jedes Besuchers), `{"action":"spawn_at","kind","from":[x,z],"to":[x,z],"wait":s}`.

Ab 3D-1.13 **Updates aus der Ferne**: Schalter `auto_update` (gespeichert in `user://simulator_settings.json`, auch als
CONTROL-Regler auf der Motion-Watch-Webseite) prüft alle 10 Minuten still (`Updater.quiet`) und installiert nach 15 s Countdown
(`Updater.auto`, «Abbrechen» möglich; bei Fehlern geht es nach 20 s von selbst weiter). Knopf `update_now` (CONTROL) löst das
sofort aus. Neustart-Optionen aus `main.restart_args()`: bisherige Optionen plus `--stream`, `--scene <aktuell>`, `--mwpc`
(startet «Motion Watch auf diesem PC» wieder). Der Status zeigt «Update: …».
Schutz nur über die Prüfsumme aus derselben Quelle (GitHub), **nicht signiert** wie Motion Watch.

Seit 3D-1.6 startet der Simulator mit dem **Kompatibilitäts-Renderer (OpenGL)**: Auf Daniels PC schloss sich die .exe mit
Forward+ (Vulkan) sofort wieder, mit OpenGL lief sie. Forward+ gibt es nur noch über «Start mit Vulkan-Grafik (schoener).bat».

Seit 3D-1.5 gibt es **sechs Szenen** (Camping-Platz, Wald, Parkplatz, Garten/Haus, Lustiger Platz, Wildbeobachtung) und ein
**unblutiges Gewehr** für die Wildbeobachtung (Taste G). Beides ist eine schnelle erste Fassung.

Seit 3D-1.4 sendet der Simulator nach dem Start **nichts**. Erst der Schalter «An Motion Watch senden» oben rechts (oder die Option `--stream`) öffnet den Port und schickt die Meldungen ins Netz.

## Wo liegt was (Repository DonElektro/MotionWatch)

- `simulator3d/`: Godot-Projekt
  - `project.godot`, `main.tscn`, `export_presets.cfg`
  - `scripts/main.gd`: Welt (Boden, Himmel, Hügel), Kameras, Wärmebild, Steuerung, PC-Fenster, Gewehr
  - `scripts/scenes.gd`: die sechs Szenen (`LIST`), welche Besucher von selbst kommen (`AUTO`), Bausteine (Baum, Hütte, Wohnwagen, Laterne …)
  - `scripts/net.gd`: HTTP-Server mit dem Simulator-Protokoll und UDP-Meldung
  - `scripts/actor.gd`: Besucher
  - `scripts/phone.gd`: Handy-/Tablet-Simulator
  - `shaders/`: Wärmebild, Gras, Laub, Boden
- `simulator3d/Lies mich.txt`: Anleitung für Daniel, liegt im ZIP.
- `simulator3d/MotionWatch3D_Simulator.zip`: die fertige Windows-Version. **Nicht löschen:** Motion Watch holt sie von hier und bietet sie unter `http://<Pi>:5000/sim/simulator3d.zip` an.
- `simulator/Simulator_Schnittstelle.md`: das Protokoll zwischen Motion Watch und Simulator.
- `simulator/motionwatch_sim_interface.py`: die Python-Vorlage des Protokolls.

## Protokoll (Kurzfassung, Details in Simulator_Schnittstelle.md)

- Port 8765 (Option `--port`).
- `POST /state`: Motion Watch schickt Servos, Lichter, Ton, Gerät.
- `GET /info`, `/events?since=`, `/cam/<n>/video.mjpg?fps=`, `/cam/<n>/snapshot.jpg`, `/thermal.bin` (float32 °C, Header X-Width/X-Height).
- Alle ausgetauschten Felder: `simulator3d/schnittstelle.json` (eine Liste, geprüft von MoveEye-Selbsttest und `schnittstelle.gd`).
- `GET/POST /control`: CONTROL-Protokoll 1. Das Steuerfeld der Motion-Watch-Webseite wird daraus automatisch gebaut. Neue Regler meldet man in `main.gd` mit `add_control(...)` an; sie erscheinen dann im PC-Fenster und auf der Webseite.
- UDP-Meldung alle 2 s an Port 8764: `{"mwsim":1,"name","port","version"}`.

## Szenen und Gewehr (ab 3D-1.5)

- Eine Szene baut alles unter einem eigenen Knoten; Umschalten löscht ihn und baut die nächste (`set_scene`). Die Szenen stehen
  als CONTROL-Szenarien in `/control` – die Motion-Watch-Webseite zeigt sie ohne Änderung an Motion Watch zur Auswahl.
- Jede Szene muss liefern: `door_node`, `door_light`, `window_mat` (Türsensor) und `obj["door"]`, `obj["pir"]`, `obj["bike"]`
  (Dieb, PIR). Die Sensornamen bleiben in allen Szenen gleich («Wohnwagen-Tür», «PIR Zelt», «Velo»), weil Motion Watch sie so kennt.
- Bewegte Dinge (Karussell, Enten, Vogelscheuche, Zwerg, Feuer) sind Funktionen in `anims`, Nachtlichter in `lamps` / `lamp_mats`.
- Besondere Besucher: `visit("car_park")` (Auto parkiert), `visit("bench")` (setzt sich auf die Bank), `visit("feed_deer")` usw.
  (Tier frisst an der Futterstelle). Ein Routenpunkt `[Punkt, Sekunden warten, kauern, schaut zu Punkt]`.
- Gewehr: Strahl von der Ansichtskamera (Maus) oder aus Kamera 0 (Knopf «Schuss aus der Kopfkamera», also mit dem Joystick von
  Motion Watch zielbar). Treffer-Kugeln pro Besucher in `actor.hit_spheres()`. Menschen und Autos blocken den Schuss
  («Nicht auf Menschen!»). Ein Tier hüpft, dreht sich, sieht Sterne und flieht (`actor.hit()` / `_dizzy()`). Töne werden aus
  Zahlen erzeugt (`_make_sound`).

## Wichtige technische Kniffe

- Jedes sichtbare Teil hat einen Wärmebild-Zwilling auf Ebene 2 (`thermal.gdshader`, Temperatur kodiert als (T+40)/120).
- Der Himmel im Wärmebild ist eine grosse Kuppel. Die Umrechnungstabelle wird beim Start kalibriert (Kompatibilitäts-Renderer: linear; Forward+: sRGB).
- SubViewports werden mit UPDATE_ONCE nur bei Bedarf gerendert. Das IR-Licht ist nur während der Aufnahme von Kamera 0 an.
- GDScript: Keine Methoden wie `c.get`/`c.set` an Dictionaries aufrufen, sondern `c["get"]`. Gepackte Arrays in Dictionaries zuerst kopieren, ändern und wieder zuweisen.
- `phone.gd`: `/json/list` über rohes StreamPeerTCP holen (HTTPRequest wurde nicht fertig). WebSocket mit 8-MB-Puffer. Bilder per `Page.captureScreenshot` (Screencast hatte die falsche Grösse).

## Bauen

- Godot 4.3 stable plus Export-Templates 4.3.
- Windows-Version: `godot --headless --path . --export-release "Windows Desktop" /tmp/…/MoveEyeSim3D.exe` (ab 3D-4.24; vorher MotionWatch3D.exe)
  (Zielordner **ausserhalb** des Repositorys wählen; `../mwsim3d_build` liegt sonst im Repository).
- ZIP: das alte ZIP entpacken, Ordner `MoveEyeSim3D/`, `MoveEyeSim3D.exe` (und übergangsweise dieselbe Datei als `MotionWatch3D.exe`) und `Lies mich.txt` ersetzen (die .bat-Dateien bleiben, rufen `MoveEyeSim3D.exe` auf), mit `zip -9 -r` packen.
- **Danach `simulator3d/version.json` mit neuer Version, Grösse und sha256 des ZIP schreiben** – sonst erfahren die Simulatoren
  nichts vom Update. (`VERSION` in main.gd, version.json und `SIM3D` in Motion Watch müssen zusammenpassen.)
- Linux-Version zum Testen: Preset «Linux». Starten mit `--rendering-driver opengl3` auf einem virtuellen Bildschirm (Xvfb), damit es auch ohne echte Grafikkarte läuft.
- Nach jedem neuen Bau: die Datei `simulator3d/MotionWatch3D_Simulator.zip` im Repository ersetzen, dann in Motion Watch (`work.py`) in `SIM3D` die neue `version`, `size` und `sha256` eintragen und eine neue Motion-Watch-Version veröffentlichen. Sonst liefert der Pi-Download die alte Fassung.

## Etappen

Gebaut in 3D-1.5 (schnelle erste Fassung, vereinbart war «zuerst schnell, dann Ausbau»):

- **Weitere Szenen**: Wald, Parkplatz, Garten/Haus, umschaltbar im Fenster und auf der Webseite.
- **Lustige Szene**: zwei Bänke, Besucher setzen sich und schauen zu: Karussell (nachts Disco), Entenfamilie um den Teich,
  winkende Vogelscheuche, Gartenzwerg hinter dem Stein, Lichterkette, Schild «Bitte lächeln!».
- **Wildbeobachtung** mit Hochsitz, Futterstelle, Salzlecke und einem **unblutigen** Gewehr: nur Tiere, Menschen nie.

Mögliche Ausbauten: Gelände mit Hügeln in der Nähe, schönere Tiere und Menschen (Modelle statt Grundformen), eigene Sensoren pro
Szene (bräuchte eine Anpassung in Motion Watch), Wasser im Wald, mehr Witz im Lustigen Platz, Punkteliste für die Wildbeobachtung.

## Fahrplan: Online-Dienst für Hersteller (Idee von Daniel, 26.10.2026)

Ziel: Später online gehen, damit Hersteller von Überwachungssystemen ihre Systeme an dieser Simulation testen können.
Noch nichts davon ist gebaut. Reihenfolge nach Wichtigkeit:

1. **Standard-Schnittstellen** statt nur Motion-Watch-Protokoll: **RTSP** für die Kamerabilder, **ONVIF** (Erkennung,
   Profil S, PTZ für den Schwenkkopf), **MQTT** / Webhooks für die Sensoren. Erst dann lässt sich ein fremdes System einfach
   «an eine Kamera» anschliessen. Das bestehende Protokoll bleibt für Motion Watch.
2. **Realistischere Bilder**: lizenzierte 3D-Modelle von Menschen und Tieren mit Animation statt Grundformen (KI-Erkenner
   erkennen die heutigen Figuren kaum), Kamerafehler (Rauschen, Unschärfe, Kompression, Infrarot-Look, Blendung).
3. **Wiederholbare Tests mit Ground Truth**: Der Simulator schreibt auf, wer wann wo im Bild war; Szenarien mit festem Zufall
   (Seed) und Zeitplan, exakt wiederholbar; Bericht am Ende («18 von 20 Personen erkannt, 2 Fehlalarme, Reaktionszeit»).
   Das ist der eigentliche Kern des Angebots.
4. **Betrieb im Internet**: Server mit Grafikkarte, eine Instanz pro Kunde, Steuerung über eine Webseite statt Windows-Fenster
   (das CONTROL-Protokoll ist ein guter Anfang), Kosten pro Stunde, Bildstrom mit wenig Verzögerung.
5. **Sicherheit**: heute offene Ports ohne Passwort und ein unsigniertes Selbst-Update – für einen Dienst braucht es Konten,
   HTTPS, Trennung der Kunden, signierte Updates. Das Repository ist öffentlich: für ein Produkt privat machen und eine Lizenz
   wählen. **Den Signierschlüssel erneuern** (er stand am 26.10.2026 im Chat); danach brauchen alle Pis einmal eine Version
   mit dem neuen öffentlichen Schlüssel (`UPDATE_PUBKEY`).
6. **Rechtliches und Geschäftliches** (fachlich prüfen lassen): AGB, Haftung, Datenschutz (nDSG, bei EU-Kunden DSGVO),
   Lizenzen aller Teile (Godot MIT; gekaufte 3D-Modelle oft eingeschränkt), Preismodell. Die Gewehr-Szene für ein
   Profi-Produkt eher weglassen.

**Vorgeschlagener erster Schritt:** zwei, drei mögliche Kunden fragen, was sie wirklich testen wollen. Technisch zuerst lokal:
der Simulator erscheint auf dem PC als **RTSP- / ONVIF-Kamera** (z. B. Bilder per ffmpeg an MediaMTX, ein kleiner
ONVIF-Dienst für Erkennung und PTZ) – ohne Server, mit einer gängigen Videoüberwachungs-Software testbar.

## Was in dieser Umgebung nicht getestet werden konnte

- Die Windows-.exe auf echter Hardware (hier nur Linux mit llvmpipe über Xvfb).
- Die Erkennung des Edge-Pfads unter Windows.
- Nebel im Forward+-Renderer (Forward+ ist ab 3D-1.6 nur noch über die Vulkan-.bat erreichbar).
- Die echte Netzsuche zwischen PC und Pi.
- Ton (Schuss «Plopp», Treffer «Boing») – hier ohne Lautsprecher.
- Die Bildrate der neuen Szenen auf dem alten i5 (Wald hat rund 300 Bäume; ab 3D-2.0 mit gemeinsamen Materialien).
- Ziehen der Besucher-Bildchen mit der echten Maus unter Windows (hier mit XTest getestet).
- Die echte Erkennungsquote von Motion Watch im Testlauf (hier ohne KI-Modell) und der Geräuschalarm mit simuliertem Pegel
  auf dem Pi.
- Das Spiel mit echten Handys im WLAN und unter Windows (hier nur mit Chromium-Handy-Nachbildung und Tastatur),
  die Bildrate der Handybilder auf einer echten Grafikkarte, Vibration, Vollbild/Querformat-Sperre auf iPhone.
- Autostart unter Windows (Registry-Eintrag, minimiert weiterzeichnen mit Direct3D/ANGLE, Sperren, Autologon) – nur unter Linux
  getestet (Autostart-Datei, minimiert weiterzeichnen).
- Das Selbst-Update unter Windows (Umbenennen der laufenden .exe, HTTPS zu GitHub) – hier nur unter Linux mit lokalem Server.
- Das Zielen mit der echten Maus (hier nur mit dem Knopf «Schuss aus der Kopfkamera» getestet).

## Testwerkzeuge in dieser Umgebung (nur als Hinweis, liegen nicht im Repo)

- Godot 4.3 von GitHub (Releases 4.3-stable, Linux-Programm + Export-Templates nach `~/.local/share/godot/export_templates/4.3.stable`).
- Projekt direkt im geklonten Repository (`simulator3d/`); `.godot/` ist in .gitignore.
- Start auf virtuellem Bildschirm und HTTP-Abfragen über kleine Hilfsskripte.
## Achtung: Zwei Chats ändern Motion Watch (Stand 26.10.2026, 19:30)

Neben dem Simulator-Chat ändert auch der Haupt-Chat `webcam_bewegung_*.py`. Am 26.10. haben beide eine eigene «2.91.0» gebaut,
und Änderungen gingen verloren (Push-Fehler wurden nicht bemerkt). Der Haupt-Chat hat das in **2.92.0** zusammengeführt:
Stand 2.91.0 dieses Chats + WLAN-Stick-Korrektur + Reiter «Simulator» (Seite `/sim`, `SIM_PAGE`).

Darum vor **jeder** Änderung an Motion Watch:
1. `git pull` und von der neuesten `webcam_bewegung_*.py` auf GitHub ausgehen.
2. Eine Versionsnummer wählen, die höher ist als die neueste auf GitHub.
3. Nach `git push` prüfen, dass er geklappt hat (`git status -sb` darf kein «ahead» zeigen). Bei Fehler: zuerst holen und zusammenführen, nie überschreiben.
