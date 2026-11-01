# MoveEye (früher Motion Watch) – Hinweise für Claude

**Interne Regeln und Notizen des Besitzers: zuerst die private Seite claude.ai/artifact/<WIRD_ERSETZT> mit dem Artifact-Tool lesen (action read).**

**Name ab 2.96.0: MoveEye** (Logo E6a-4: Sichtfeld, Auge unten, gehende Person in Erkennungs-Ecken). In allen sichtbaren Texten «MoveEye»; interne Namen bleiben (Dateien `webcam_bewegung_*.py`, Ordner `~/.config/motionwatch/`, Repository, `"app": "Motion Watch"` in Protokollen wie versions.json und der Geräte-Suche, Basic-Realm ab 2.98.19 «MoveEye»).

Raspberry-Pi-5-Gerät zur Wildtier- und Personenwarnung beim Camping (Schwenk-/Neigekopf, KI-Erkennung, Wärmebild,
Push-Nachrichten). Einrichtung: `docs/Einrichtung_Raspberry_Pi.md`, Gehäuse: `hardware/gehaeuse/LIESMICH.md`.

## Grundregeln

- Deutsch (Schweiz, «ss» statt «ß»), kurz und verständlich.
- Keine Passwörter, privaten ntfy-Themen oder Zugangsdaten in Dateien, Commits oder geteilte Pakete.
- **Nichts entfernen ohne Nachfrage:** Funktionen, Schalter, Menüpunkte, Dateien oder Inhalte werden nur nach
  ausdrücklicher Zustimmung des Besitzers entfernt. Vorher immer fragen.
- **Bau-Infos nachziehen:** Ändern sich Hardware oder Software so, dass die Bau-Infos betroffen sind (hardware/gehaeuse,
  Teile-, Einkaufs- oder Verkabelungsplan, Montage, Inbetriebnahme), jedes Mal fragen, ob die Bau-Infos nachgezogen werden
  sollen. Nicht automatisch nachziehen (Prüfung: `werkzeuge/bau_pruefen.py`).
- **Gleiches Aussehen MoveEye ↔ Simulator:** Bedienelemente, die es in beiden gibt (z. B. die drei Aufklapp-Knöpfe
  «Alle zuklappen · Nur Gruppen · Alle aufklappen», Suchfeld, Schalter Einfach/Experte, Symbole, Farben, aktive Zustände blau),
  in beiden gleich oder möglichst ähnlich bauen; ebenso die **Menüstruktur** (Gruppen, Reihenfolge, Namen, Einfach/Experte,
  Karten). Bei jeder optischen Änderung im einen Projekt das andere prüfen und mitziehen; Abweichungen melden.

## Software

- **Bearbeitet wird in `quelle/`** (ab 2.95.63): das Programm in rund 65 Teilen nach Thema (Übersicht in `quelle/LIESMICH.md`).
  `python3 werkzeuge/bauen.py` setzt sie Byte für Byte zur **einen Datei** `webcam_bewegung_X_Y_Z.py` zusammen (ca. 51'000 Zeilen),
  die der Pi, die Update-Funktion und die Signatur kennen. **Die grosse Datei nie von Hand ändern** – GitHub prüft bei jedem Push
  (`bauen.py --pruefen`), dass sie zu `quelle/` passt. Alle Teile sind zusammen *ein* Programm (gemeinsame Namen, keine Importe).
- Jede Änderung = **neue Version und neue Datei** (Nummern-Regeln ab 3.0.0: Abschnitt «Versionierung»): `python3 werkzeuge/bauen.py --neue-version "Was neu ist"` erhöht die Nummer an
  allen Stellen (`APP_VERSION`, Fenstertitel, `{tr('Build')}`, Dateiname in der Hilfe), schreibt die Zeile in die Änderungsliste
  (`quelle/000_kopf_aenderungen.py`), übernimmt die Simulator-Version aus `simulator3d/version.json`, baut die Datei und entfernt
  die ältere Datei derselben Hauptversion. `--version X.Y.Z` für eine bestimmte Nummer.
- **Prüfstand** (`pruefstand/`): misst die Erkennung mit dem 3D-Simulator (feste Testläufe) und schreibt `pruefstand/VERLAUF.md`.
  Vor Änderungen an der Erkennung und danach laufen lassen und vergleichen; auf GitHub: Actions → «Prüfstand».
  Ab 2.98.13: Szene «stellplatz», Besucher gehen durchs Bild der Kopfkamera, `--mal 2`, `--realismus an,aus` (Zeilen
  «· ohne Kamera-Effekte» zeigen, ob ein Rückgang am Simulator-Bild oder an MoveEye liegt). Lokal nur aussagekräftig, wenn der
  Rechner frei ist (unter ~3 Bilder/s erkennt MoveEye kaum etwas). Fehlersuche: Umgebungsvariable `MW_DEBUG_TRACKS=<datei>`
  schreibt pro Bild Bewegungsflächen und Spuren (410).
  Prüfstand 2: Hauptzahl sind die echten **Pushes richtig / falsch** (Test-Postfach, Teil 068 → `det.pushes`), das alte
  «Fehlalarme» heisst «Flackern»; nachts zählt das Wärmebild als Wahrheit und Sensor; Plan `nacht` (ganze Nacht im Zeitraffer),
  `--seeds 3` (Streuung), Schleichwege aus `feedback/` automatisch, echte Nächte in `simulator3d/pruefnaechte/` (pruefstand/LIESMICH.md).
- **Prüfstand sparsam:** pro Version läuft auf GitHub nur «quick»; die grossen Läufe sonntags oder von Hand
  (Actions → Prüfstand → Run workflow).
- **Sprachen** (ab 2.28.0): Deutsch, Französisch, Italienisch, Rätoromanisch (Rumantsch Grischun), Englisch. Schlüssel ist immer der
  englische Text. Deutsch: `DE` (Python) bzw. `I18N.de` / `TX` / `ALT` / `WZ` (Web). Französisch / Italienisch / Romanisch: Tabellen
  `TRX["fr"|"it"|"rm"]` und die Anleitung `HELP_X` am Dateiende (das Web lädt sie über `/i18n/<sprache>.js`). Neue Texte in
  allen Sprachen ergänzen; fehlt ein romanischer Text, erscheint Deutsch, bei Französisch / Italienisch Englisch.
- Danach im Repository: `python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI` (schreibt und **signiert** `versions.json`,
  dann Selbsttest), committen, pushen. Ab 2.4.0 installieren die Geräte nur signierte Versionen. Den geheimen Schlüssel
  (`MotionWatch_Signierschluessel.txt`, 64 Hex-Zeichen) hat nur der Besitzer – bei Bedarf danach fragen; **nie ins Repository** legen.
  Ohne Schlüssel: Version trotzdem hochladen, der Besitzer signiert später (oder vorübergehend «Auch nicht signierte Versionen annehmen»).
  Der Pi holt Updates von `https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json`.
- **Nur die Hauptversionen** im Repository behalten: pro Hauptversion X.Y nur die neueste Datei (z. B. 2.58.2 statt 2.58.0/2.58.1),
  höchstens die letzten 10 Hauptversionen. Danach Manifest neu signieren. Ältere Versionen bleiben
  in der Git-Geschichte.
- **Webseite und Desktop-Fenster immer beide anpassen**, zweisprachig DE/EN:
  - Web (Flask, Handy zuerst): Seiten-Vorlagen `WEB_PAGE`, `CAMS_PAGE`, `ZONES_PAGE`, `REC_PAGE`, `DIARY_PAGE`, `HELP_PAGE`, `GUEST_PAGE`;
    gemeinsame Teile `/*BASECSS*/`, `/*COMMON*/` (COMMON_JS), `<!--NAV-->`, `/*ALERTS*/` (HEADER_JS + ALERT_JS) über `render_page()`.
    Die Hauptseite hat ein eigenes `I18N.de`-Wörterbuch (kein COMMON_JS).
  - Desktop (Tkinter): Klasse `App`, Gruppen `TK_GROUPS`, Abschnitte in `_build_section`, Status über `self._status(...)`.
  - Einstellungen sind schema-basiert: `CFG` (Standardwerte) + `TOGGLES` / `SLIDERS` / `TEXTS` + Abschnitt in `SECTIONS`,
    Web-Gruppen in `GROUPS` (JS), Fenster-Gruppen in `TK_GROUPS`. Übersetzungen im Python-Wörterbuch `DE` (Fenster + Server).
  - Einstellungen bleiben bei neuen Versionen erhalten (`~/.config/motionwatch/`); `VOLATILE` wird nie geladen.
- Anleitung (`HELP_PAGE`, Abschnitte `<section id=…>` DE und EN) bei neuen Funktionen ergänzen.

## Versionierung (gilt ab dem Release 3.0.0)

- **Eine gemeinsame Nummer X.Y.Z:** «MoveEye 3.0.0» und «MoveEye Sim 3.0.0» haben immer dieselbe Nummer und werden **immer
  zusammen** veröffentlicht (auch wenn sich nur eines geändert hat). Start bei **3.0.0** (davor MoveEye 2.98.x / Simulator 3D-4.8x).
- **Zählen:** neue Funktion = zweite Zahl +1 (3.0.4 → 3.1.0), reine Fehlerkorrektur = dritte Zahl +1 (3.1.0 → 3.1.1),
  grosser Sprung (z. B. Hardware) = erste Zahl +1 (→ 4.0.0). Jede Zahl höchstens 3 Ziffern (Update-Muster der Geräte).
- **Dateiname bleibt** `webcam_bewegung_X_Y_Z.py` (z. B. `webcam_bewegung_3_0_0.py`): alte Geräte suchen genau dieses Muster
  (`VFILE_RE`, Signatur über Version + Dateiname). Pro Hauptversion X.Y nur die neueste Datei, höchstens 10 Hauptversionen.
- **Brücke für alte Simulatoren:** sie lesen in `simulator3d/version.json` nur `version` und vergleichen «3D-A.B» als Zahlen
  («3.0.0» wäre für sie älter als «3D-4.82»). Darum steht dort immer `"version": "3D-(X+2).Y.Z"` (3.0.0 → `3D-5.0.0`,
  3.1.0 → `3D-5.1.0`, 4.0.0 → `3D-6.0.0`) und die echte Nummer in `"ver": "X.Y.Z"`. Neue Simulatoren und MoveEye lesen `ver`
  und rechnen «3D-A.B» als (A−2).B (`simulator3d/scripts/versionen.gd`, `sim_vkey()` in Teil 300, `vnum` im Web-JS, Teil 470).
  Dieses Feld nie weglassen, auch nicht in späteren Versionen.
- **Grösse:** Geräte bis 2.98.x nehmen nur Programmdateien bis 8 MiB an (3.0.0 hat rund 7.6 MB) – 3.0.0 muss darunter
  bleiben. Ab 3.0.0 gilt 32 MiB (`UPD_MAX_BYTES`, Teil 390).
- **Zusatzdatei**: `bauen.py` lagert grosse Literale
  (Web-Seiten, JavaScript, Bilder als base64, Übersetzungen fr/it/rm, ältere Einträge der Änderungsliste) in
  `moveeye_daten_X_Y_Z.zip` neben `webcam_bewegung_X_Y_Z.py` aus; `quelle/` bleibt unverändert. Die Hauptdatei kennt die
  SHA-256 der ZIP (`ZD_SHA256`, Teil 012) – die Signatur der Hauptdatei bürgt so auch für die ZIP; zusätzlich steht sie mit
  eigener Signatur unter `"data"` in versions.json. **Beide Dateien gehören zusammen ins Repository** (`git add` beider).
  Ohne ZIP startet MoveEye im Kern (Kamera, Erkennung, Alarm, Push, Fenster; Web-Seiten zeigen «Zusatzdaten fehlen – Update»)
  und holt sie über dieselbe Update-Quelle (Teil 397), dann ein Neustart. Ziel Hauptdatei unter 5 MiB, Pflicht unter 8 MiB
  (`versionen.py --pruefen`) – so gehen auch Geräte bis 2.98.x direkt auf die neueste Version.
- **Brücke**: `webcam_bewegung_3_0_2.py` (eine Datei unter 8 MiB, ohne Zusatzdatei) bleibt
  **für immer** im Repository und in versions.json (`"bridge": true`, `BRUECKE` in `versionen.py`, `UPD_BRIDGE` in Teil 397).
  Beim Aufräumen («höchstens 10») nie löschen – `python3 werkzeuge/versionen.py --aufraeumen` lässt sie stehen (sie zählt mit).
  Wäre eine Hauptdatei je über 8 MiB, schreibt `--make-manifest` `"needs": "3.0.0"` in ihren Eintrag: Geräte ab dieser Fassung
  nehmen dann zuerst die Brücke und danach die neueste (`update_pick`, Teil 397). Ältere Geräte (2.98.x bis zur letzten Version ohne Zusatzdatei) wählen immer die
  neueste – für sie ist die 8-MiB-Grenze der Hauptdatei die eigentliche Sicherung, 3.0.2 von Hand in der Liste der Rückweg.
- **Release-Ablauf ab 3.0.0** (nur der Koordinator, Schlüssel nur beim Besitzer):
  1. Nummer wählen (Regeln oben); `VERSION := "X.Y.Z"` in `simulator3d/scripts/main.gd`, Block `NEU IN X.Y.Z` in
     `simulator3d/Lies mich.txt`, Kopf von `simulator3d/UEBERGABE.md`.
  2. Simulator exportieren und ZIP packen, dann `python3 werkzeuge/versionen.py --neu-data` (vor dem Export) und
     `python3 werkzeuge/versionen.py --sim-json X.Y.Z "Notiz"` (schreibt `version.json` mit `version` + `ver`).
  3. `python3 werkzeuge/bauen.py --version X.Y.Z --neue-version "Was neu ist"` (oder `--stufe funktion|fehler|gross` statt
     `--version`); übernimmt `ver` aus `version.json` in `SIM3D` (Teil 300).
  4. `python3 werkzeuge/versionen.py --pruefen` (eine Nummer überall, Brücke stimmt, Hauptdatei unter 8 MiB, Zusatzdatei und
     Brücken-Datei da), dann `bauen.py --signieren …`
     (Selbsttest prüft dasselbe noch einmal: «Version numbers …»), Rauchtest, committen, pushen.
  5. **Projektschalter «Projekt veröffentlicht»:** Beim Veröffentlichen `projekt_veroeffentlicht` auf `true` setzen
     (`simulator3d/ui_gemeinsam.json`, oberste Ebene; gilt für MoveEye und Simulator, danach `bauen.py` bettet sie ein).
     `false` = Entwicklung: die Links zu Neuerungen im Fenster «Neu in …» sind standardmässig an; `true` = standardmässig aus.
     Eine eigene Wahl im Entwickler-Bereich («Links zu Neuerungen», auto / an / aus) überschreibt den Standard. Neue Ziele
     für die Links: `neu_ziele` in derselben Datei (Version -> Seite / Einstellung / Simulator-Menü / -Aktion).

## Testen (vor jeder Auslieferung)

- `python3 webcam_bewegung_X_Y_Z.py --self-test .` (im Repository: prüft auch alle Signaturen in versions.json). Läuft zusätzlich
  automatisch auf GitHub (Actions → «CI», ohne Signaturen) bei jedem Push auf `real-*`, `integration`, `main`.

- **Bildtests nur bei Bedarf**: Live- bzw. Bild-Läufe (Playwright-Bildschirmfotos, allp, Live-Läufe des
  Simulators) nur bei sichtbaren Änderungen, sonst nur Tests ohne Bild. Gilt auch für die Release-Kette.
- **Tests auf GitHub**: Export, Godot-Tests und Prüfstand laufen in GitHub Actions (ab 3.28.1: «CI»,
  ersetzt «Selbsttest»; «Prüfstand» bleibt eigener Workflow). Nach jedem Push mit `werkzeuge/ci_status.sh <commit> --warten
  --fehler` auf das CI warten statt dieselben schweren Tests lokal zu wiederholen. Lokal bleiben: Signieren, Selbsttest mit
  Signatur, Simulator-Export und ZIP.
- **CI statt lokal rechnen** (Workflow `.github/workflows/ci.yml`, Name «CI»): bei Push auf `real-*` laufen parallel
  `bauen.py --pruefen`, Selbsttest (ohne Signaturen), Web-Rauchtest mit Browser (`web_rauchtest.py --browser`, Playwright),
  Godot-4.3-Parse-Check («Schnittstelle: OK»), jeder `werkzeuge/*_test.gd` und `sim_texte.py --pruefen`; auf `integration` /
  `main` (oder von Hand, oder «[export]» in der Commit-Nachricht) dazu der Export Linux + Windows ohne Signatur als Artefakt. Helfer und Integrator pushen und warten:
  `werkzeuge/ci_status.sh [zweig|commit] --warten --fehler` (Exit 0 = grün; ohne `--warten` nur die letzten Läufe;
  `--start` startet von Hand, geht erst wenn ci.yml auf main ist). Signieren bleibt lokal, der Schlüssel kommt nie ins CI.
- `python3 -m py_compile` und JavaScript-Prüfung (`node --check` der gerenderten Seiten).
- Programm mit simulierter Kamera starten (`open_source` ersetzen) und mit Playwright prüfen:
  Handy hoch (390 × 844) und quer, PC; keine JS-Fehler; Bildschirmfotos ansehen.
- Echte Prozess-Tests für Neustart/Pause/Update (`os.execv`, gleiche PID).
- Fenster ohne Bildschirm: Xvfb, oder notfalls ein Tkinter-Ersatz (nur Rauchtest).

## Hardware

Pi 5, Camera Module 3 NoIR, Waveshare Thermal-90 (SPI, I2C 0x40, GPIO 7/23/24, Treiber pysenxor – noch nicht mit echtem Modul getestet),
2 × MG90S an PCA9685 (0x41; Kanal 0 Pan, 1 Tilt), Licht weiss + IR an PCA9685 Kanal 2/3 (nur ein/aus), USB-Mikrofon,
USB-Soundkarte + PAM8403 + Lautsprecher oder Bluetooth, Powerbank oder Waveshare UPS HAT (INA219 0x42, 2 × 18650). Gehäuse: parametrisches Python-Modell (`Gehaeuse/`).
Push über ntfy (App «NTFY me», Server ntfy-me.com). Fernzugriff über Tailscale.

## Simulator

- Der Simulator ist **MoveEye Sim** (3D, Godot) im Ordner `simulator3d/`. Der alte Python-Basis-Simulator
  (`simulator/motionwatch_simulator.py`, `SIM_ZIP_B64`) ist ab 3.27.0 entfernt; Teil 360 kennt nur
  noch den Ordner `sim_dir`. In `simulator/` bleiben die Schnittstelle für eigene Simulatoren (`motionwatch_sim_interface.py`,
  `Simulator_Schnittstelle.md`, `EIGENEN_SIMULATOR_ANBINDEN.md`).

- **Daten aus dem Simulator:** nur bildbezogene, kartenunabhängige Daten für die Erkennung sammeln (Bilder mit
  Rahmen, Reaktionszeit nach Abstand/Haltung/Licht). Kartengebundenes (Schleichwege) immer mit Szene speichern und nur dort
  abspielen.

## Rückmeldungen aus den Testläufen (ab 2.95.28)

- Testlauf-Berichte (ZIP aus MoveEye) liegen in `feedback/` oder kommen als Anhang.
- Vor Arbeiten an der Erkennung: neue Berichte in `feedback/` lesen (JSON und Bilder), daraus Verbesserungen ableiten,
  danach nach `feedback/erledigt/` verschieben. Siehe `feedback/README.md`.
