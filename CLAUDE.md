# MoveEye (früher Motion Watch) – Hinweise für Claude

**Interne Regeln und Notizen des Besitzers: zuerst die private Seite claude.ai/artifact/WiCPgjkniA3TEhxwVwhHUU mit dem Artifact-Tool lesen (action read).**

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
- Jede Änderung = **neue Version und neue Datei** (Nummern-Regeln: Abschnitt «Versionierung», drei Spuren): `python3 werkzeuge/bauen.py --neue-version "Was neu ist"` erhöht die MoveEye-Nummer an
  allen Stellen (`APP_VERSION`, Fenstertitel, `{tr('Build')}`, Dateiname in der Hilfe), schreibt die Zeile in die Änderungsliste
  (`quelle/000_kopf_aenderungen.py`), übernimmt den Simulator aus `simulator3d/version.json` als eingebetteten Rückfall, baut die
  Datei und entfernt die ältere Datei derselben Hauptversion. `--version X.Y.Z` für eine bestimmte Nummer.
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
- Danach im Repository: `python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI` (schreibt und **signiert** `versions.json`
  samt Block `sim`, dann Selbsttest; nur Simulator: `--nur-signieren`, baut nichts), committen, pushen. Ab 2.4.0 installieren die Geräte nur signierte Versionen. Den geheimen Schlüssel
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

## Versionierung: drei Spuren (Entscheid des Besitzers 03.11.2026, gilt bis zum Zusammenführen)

- **Drei Spuren im selben Repository, jede mit eigener Nummer**, veröffentlicht wird nur die geänderte Spur (kein Sim-Export,
  kein Bausatz ohne Grund). Berichte immer mit Vorsilben: «MoveEye 3.56.0 · Sim 3.55.4 · Gehäuse 5.3.1»
  (`python3 werkzeuge/versionen.py --spuren`).
  - 📷 **MoveEye 3.x**: `APP_VERSION` (Teil 010) + Eintrag in `versions.json` (signiert).
  - 🎮 **Simulator** (eigene Nummer, weiter ab 3.55.x): `VERSION` in `simulator3d/scripts/main.gd`, `simulator3d/version.json`
    (`ver`, Brücke `version`, Block `linux`, optional `mw_min`), Block `NEU IN X.Y.Z` in `simulator3d/Lies mich.txt`; signiert
    als Block `"sim"` in `versions.json`.
  - 🧩 **Gehäuse v5.x**: `"version"` in `hardware/gehaeuse/bau.json` (X.Y oder X.Y.Z), Release `geh-X.Y.Z` mit dem Bausatz.
- **Pausiert bis zum Zusammenführen:** «eine Nummer für alles» (ab 3.0.0), MoveEye = Sim angleichen, Kamera/Gehäuse überall
  nachziehen, Bausatz und Homepage-Prüfung bei jedem Release. **Weiter gültig:** Sicherheit, Signatur (gleicher Schlüssel,
  gleiches Verfahren), «So testest du», Name «Elektro», Fragebogen-Regeln. Am Schluss (Zusammenführen): gemeinsame Nummer +
  grosser Konzept-Check; dann diesen Abschnitt zurück auf «eine Nummer» stellen.
- **Zählen** (jede Spur für sich): neue Funktion = zweite Zahl +1, reine Fehlerkorrektur = dritte Zahl +1, grosser Sprung = erste
  Zahl +1. Jede Zahl höchstens 3 Ziffern (Update-Muster der Geräte). Keine Nummer wird je kleiner.
- **Verträglichkeit statt gleicher Nummer:** `SIM_MIN` (Teil 545, geht als `sim_min` im Zustand an den Simulator) und `MW_MIN`
  (`simulator3d/scripts/abgleich.gd`, geht als `mw_min` in `/info` und in `version.json`) nennen die älteste Version der
  anderen Spur, mit der es geht. Das Versions-Paar (Teil 639zb / `abgleich.gd`) warnt nur darunter. Erhöhen, wenn sich die
  Schnittstelle (`simulator3d/schnittstelle.json`, Teil 558 / `schnittstelle.gd`) so ändert, dass die ältere Seite nicht mitkommt.
- **Simulator für /sim und den HP aus der signierten Liste:** `make_manifest` (Teil 390, `bauen.py --signieren` oder
  `--nur-signieren`) schreibt `"sim": {"ver", "win": {file, size, sha256, ver, sig}, "linux": {…}}` in `versions.json`;
  Signatur wie bei den Programmdateien (Ed25519 über `MotionWatch|ver|file|sha256`). MoveEye (Teil 300 `sim_manifest_take`)
  nimmt nur einen richtig signierten Eintrag für genau diese Datei und nie eine ältere Nummer, sonst die eingebettete
  `SIM3D` / `SIM3D_LINUX` (Rückfall = Simulator des eigenen Releases). `moveeye-hp-update` (HP_FASSUNG 3) holt die Sim-Nummer
  ebenso aus dem Block `sim` und merkt MoveEye- und Sim-Nummer getrennt. **Alt:** MoveEye vor diesem Umbau kennt nur die
  eingebettete Prüfsumme – nach einem Sim-Release allein liefert es /sim erst nach dem eigenen Update wieder.
- **Simulator-Anhang (Besitzer 12.11.2026, «Ablage entlasten»):** ab der Version **nach Sim 3.67.2** kommen Windows- und
  Linux-Paket nicht mehr ins Repository (103 MB pro Version, git kann sie nicht vergleichen), sondern wie das Pi-Paket als
  Assets an den Release `sim-X.Y.Z` (Workflow «Sim-Pakete», `sim_pi.yml`; nie «latest»). **Die Pakete von Sim 3.67.2 bleiben
  für immer** unter `simulator3d/MotionWatch3D_Simulator.zip` / `MoveEyeSim3D_Linux.zip` liegen (wie die Brücke 3.0.2) und
  in `version.json` (oberste Felder, `linux`) und `versions.json` (`sim.win`, `sim.linux`) **eingefroren**: alte Simulatoren,
  alte MoveEye und ein alter HP holen sie wie bisher und kommen von dort weiter (zwei Schritte). Die neuste Version steht in
  `version.json` unter `anhang` {ver, version, notes, mw_min, win / linux: {file `simulator3d/anhang/…`, ver, size, sha256,
  url}} und signiert in `versions.json` unter `sim.anhang`. Regeln überall gleich (Teil 300, `update.gd`, `hp_update.sh`):
  eigener Dateiname, die Adresse muss genau `…/releases/download/sim-<Nummer>/<Name>` sein, das neuere gültige Paket gewinnt,
  ein Anhang, der nicht stimmt, wird nie benutzt. Werkzeuge: `werkzeuge/sim_anhang.py holen X.Y.Z` (Assets holen, nachrechnen,
  nach `simulator3d/anhang/`, `.gitignore`), `versionen.py --anhang-json X.Y.Z "Notiz"`, `bauen.py --nur-signieren` (behält
  eine gültige Signatur, wenn die geholte Datei wieder weg ist); `sim_anhang.py pfad linux` gibt Workflows das neuste Linux-Paket.
  **Zurück ins Repository** (Asset-Weg gestört): eine **neuere** Sim-Nummer wie früher exportieren und packen,
  `MW_SIM_IM_REPO=1 versionen.py --sim-json …` (schreibt `version.json` ohne `anhang`), signieren, beide ZIP committen –
  kein Gerät braucht dafür ein Update. Tests: `werkzeuge/sim_anhang_test.py`, `sim_anhang_test.gd`, `hp_update_test.sh` Teil 6.
- **Gehäuse-Daten** in MoveEye (Teil 639v) und im Simulator (`werkstatt_daten.gd`, Modelle) kommen mit deren nächstem Release
  (`gehaeuse_bauen.py --sim`); der Selbsttest meldet abweichende Gehäuse-Daten bis dahin nur als Warnung.
- **In MoveEye eingebettet** (dann braucht es auch ein MoveEye-Release): `simulator3d/ui_gemeinsam.json`,
  `simulator3d/fehler_katalog.json` (`bauen.py --pruefen` schlägt sonst fehl).
- **Dateiname bleibt** `webcam_bewegung_X_Y_Z.py`: alte Geräte suchen genau dieses Muster (`VFILE_RE`, Signatur über Version +
  Dateiname). Pro Hauptversion X.Y nur die neueste Datei, höchstens 10 Hauptversionen.
- **Brücke für alte Simulatoren:** sie lesen in `simulator3d/version.json` nur `version` und vergleichen «3D-A.B» als Zahlen.
  Darum steht dort immer `"version": "3D-(X+2).Y.Z"` zur Sim-Nummer `"ver": "X.Y.Z"` (3.55.4 → `3D-5.55.4`). Neue Simulatoren und
  MoveEye lesen `ver` und rechnen «3D-A.B» als (A−2).B (`simulator3d/scripts/versionen.gd`, `sim_vkey()` in Teil 300, `vnum`
  im Web-JS, Teil 470). Dieses Feld nie weglassen und **nie kleiner** werden lassen (`versionen.py --pruefen` prüft es).
- **Grösse:** Geräte bis 2.98.x nehmen nur Programmdateien bis 8 MiB an. Ab 3.0.0 gilt 32 MiB (`UPD_MAX_BYTES`, Teil 390).
- **Zusatzdatei**: `bauen.py` lagert grosse Literale
  (Web-Seiten, JavaScript, Bilder als base64, Übersetzungen fr/it/rm, ältere Einträge der Änderungsliste) in
  `moveeye_daten_X_Y_Z.zip` neben `webcam_bewegung_X_Y_Z.py` aus; `quelle/` bleibt unverändert. Die Hauptdatei kennt die
  SHA-256 der ZIP (`ZD_SHA256`, Teil 012) – die Signatur der Hauptdatei bürgt so auch für die ZIP; zusätzlich steht sie mit
  eigener Signatur unter `"data"` in versions.json. **Beide Dateien gehören zusammen ins Repository** (`git add` beider).
  Ohne ZIP startet MoveEye im Kern (Kamera, Erkennung, Alarm, Push, Fenster; Web-Seiten zeigen «Zusatzdaten fehlen – Update»)
  und holt sie über dieselbe Update-Quelle (Teil 397), dann ein Neustart. **Schlank (ab 3.59.0):** statische Inhalte schon
  ab 1 KiB in die ZIP, `_HX…`-Tabellen behalten nur Deutsch, die gebaute Datei ohne Kommentare / Docstrings und mit Tabs
  (gleiche Zeilennummern; Originalzeilen in der ZIP, `zd_source()`). Hauptdatei: Warnung ab 4 MiB, Abbruch ab 5 MiB
  (`bauen.py`, `versionen.py --pruefen`), äussere Grenze 8 MiB für Geräte bis 2.98.x. Tests: `werkzeuge/zusatzdaten_test.py`,
  `werkzeuge/update_uebergang_test.py`. **Ablage entlasten (Nov. 2026):** `daten.json` steht **ungepackt** in der ZIP
  (`ZD_GEPACKT = False` in `bauen.py`, rund 10 MB statt 4.9 MB): git speichert so pro Version nur den Unterschied
  (rund 0.1 MB statt 4.9 MB; `werkzeuge/ablage_test.py` misst es). Nicht wieder packen, die ZIP nie von Hand neu packen.
  Die Geräte nehmen die Programmdatei von der Adresse `url` ihres Eintrags (seit 2.98.x) und suchen die ZIP **daneben**;
  `data.url` lesen sie nicht. Ab der nächsten Version findet eine MoveEye ohne ZIP sie auch über ihren eigenen Eintrag
  (`_zd_entry_urls`, Teil 397) – vorbereitet, **nicht in Gebrauch**: alles liegt weiter neben `versions.json`
  (`update_uebergang_test.py` Teil U stellt die andere Ablage mit lokalen Servern nach).
- **Brücke**: `webcam_bewegung_3_0_2.py` (eine Datei unter 8 MiB, ohne Zusatzdatei) bleibt
  **für immer** im Repository und in versions.json (`"bridge": true`, `BRUECKE` in `versionen.py`, `UPD_BRIDGE` in Teil 397).
  Beim Aufräumen («höchstens 10») nie löschen – `python3 werkzeuge/versionen.py --aufraeumen` lässt sie stehen (sie zählt mit).
  Wäre eine Hauptdatei je über 8 MiB, schreibt `--make-manifest` `"needs": "3.0.0"` in ihren Eintrag: Geräte ab dieser Fassung
  nehmen dann zuerst die Brücke und danach die neueste (`update_pick`, Teil 397). Ältere Geräte (2.98.x bis zur letzten Version ohne Zusatzdatei) wählen immer die
  neueste – für sie ist die 8-MiB-Grenze der Hauptdatei die eigentliche Sicherung, 3.0.2 von Hand in der Liste der Rückweg.
- **Prüfen:** `python3 werkzeuge/versionen.py --pruefen` prüft jede Spur für sich (Exit 1 nur bei Problemen: Brücke / Nummer
  kleiner, Minimum der anderen Spur nicht erfüllt, Grösse, Brücken-Datei) und **warnt**, wenn Dateien einer Spur seit ihrem
  letzten Release geändert sind, die Nummer aber nicht. Tests: `werkzeuge/versionen_spuren_test.py`, `werkzeuge/sim_manifest_test.py`.
- **Release-Ablauf** (nur der Integrator, Schlüssel nur beim Besitzer; Werkzeuge ausserhalb des Repositorys: `rel_mw.sh`,
  `rel_sim.sh`, `rel_geh.sh`, `pub.sh`; die alte `rel_kette.sh` nur noch mit `ALTE_KETTE=1`):
  - 📷 **MoveEye allein:** `bauen.py --version X.Y.Z --neue-version "Was neu ist"` (bettet den aktuellen Simulator als
    Rückfall ein), `versionen.py --pruefen`, `bauen.py --signieren …` (schreibt auch den Block `sim`), Selbsttest, Rauchtest,
    committen, pushen. Kein Sim-Export, kein Bausatz.
  - 🎮 **Simulator allein, ab der Version nach 3.67.2 (Simulator-Anhang):** Nummer in `main.gd`, `NEU IN X.Y.Z`, `UEBERGABE.md`,
    `versionen.py --neu-data`; committen, main pushen (kein Export, keine ZIP) → Workflow «Sim-Pakete» (`ver=X.Y.Z`, Probe aus)
    → `sim_anhang.py holen X.Y.Z`, `pi_asset.py holen X.Y.Z`, `versionen.py --anhang-json X.Y.Z "Notiz"`,
    `bauen.py --nur-signieren …`, Selbsttest; `version.json` + `versions.json` committen, pushen. Bis 3.67.2 wie folgt:
  - 🎮 **Simulator allein:** `VERSION := "X.Y.Z"` in `main.gd`, Block `NEU IN X.Y.Z` in «Lies mich», Kopf von `UEBERGABE.md`;
    exportieren (Windows + Linux), ZIP + Linux-Paket, `versionen.py --neu-data`, `versionen.py --sim-json X.Y.Z "Notiz"`,
    dann `bauen.py --nur-signieren …` (baut nichts, die MoveEye-Datei bleibt Byte für Byte; Block `sim` neu signiert),
    Selbsttest, committen, pushen. Der Prüfstand läuft auch bei einer neuen Sim-Nummer.
  - 🧩 **Gehäuse allein:** `"version"` in `bau.json` erhöhen, `bau_pruefen.py` (nach Freigabe `--festhalten`), committen,
    pushen: der Workflow «Bausatz» baut den Release `geh-X.Y.Z` mit der neusten signierten MoveEye
    (`releases/latest/download/MoveEye_Bausatz.zip` bleibt). Kein MoveEye-Bau, kein Signieren.
  - **Erstes Mal nach dem Umbau** (Reihenfolge zählt): zuerst MoveEye mit der neuen Prüfung (zusammen mit einem Sim-Paket, das
    das neue `hp_update.sh` enthält: `rel_sim.sh … SIGNIEREN=0`, dann `rel_mw.sh`), erst danach Releases einer Spur allein.
  - **Projektschalter «Projekt veröffentlicht»:** Beim Veröffentlichen `projekt_veroeffentlicht` auf `true` setzen
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
- **CI in Gruppen** (ab Nov. 2026): die Tests stehen in `werkzeuge/ci_tests.txt` – **neuer Test = eine Zeile dort**
  (`Gruppe | Limit | Nochmal | Befehl | Name`), `ci.yml` bleibt wie es ist. Jede `werkzeuge/*_test.py` muss dort stehen
  (in einer Gruppe oder in «hand» mit Grund), sonst ist `python3 werkzeuge/ci_lauf.py --pruefen` rot. Gruppen = parallele
  Jobs: `basis` (ohne Browser, läuft immer), `kern`, `rechte`, `live`, `daten`, `spiele-1`, `spiele-2`, `simlive` (gegen
  einen laufenden Simulator). Lokal eine Gruppe wie im CI: `python3 werkzeuge/ci_lauf.py --gruppe live`. Was läuft,
  entscheidet `werkzeuge/ci_auswahl.py` (Vergleich des ganzen Zweigs mit main; `--dateien …` / `--simulieren 20` zeigt es
  lokal): **auf main immer alles**; sonst alles ausser den Spiele-Tests (nur bei Änderungen an `games/`, den Spiele-Teilen
  in `quelle/` und den Spiele-Tests) und dem USB-Installer (nur bei `werkzeuge/usb_installer/`); nur Prüfstand-Ergebnisse /
  `feedback/` → nur die Grundprüfungen; Änderungen an den CI-Dateien → alles. Übersprungenes steht mit «übersprungen,
  weil …» in der Zusammenfassung des Laufs; der Job «Ergebnis» ist der eine Haken (auf main rot, sobald irgendetwas
  übersprungen wurde). «1x» in der Liste = genau ein zweiter Versuch für Tests, die unter Last wackeln (wird als Warnung gemeldet).
- `python3 -m py_compile` und JavaScript-Prüfung (`node --check` der gerenderten Seiten).
- Programm mit simulierter Kamera starten (`open_source` ersetzen) und mit Playwright prüfen:
  Handy hoch (390 × 844) und quer, PC; keine JS-Fehler; Bildschirmfotos ansehen.
- Echte Prozess-Tests für Neustart/Pause/Update (`os.execv`, gleiche PID).
- Fenster ohne Bildschirm: Xvfb, oder notfalls ein Tkinter-Ersatz (nur Rauchtest).

## Hardware

Pi 5, Camera Module 3 NoIR, Waveshare Thermal-90 (SPI, I2C 0x40, GPIO 7/23/24, Treiber pysenxor – noch nicht mit echtem Modul getestet),
2 × MG90S an PCA9685 (0x41; Kanal 0 Pan, 1 Tilt), Licht weiss + IR an PCA9685 Kanal 2/3 (nur ein/aus), USB-Mikrofon,
USB-Soundkarte + PAM8403 + Lautsprecher oder Bluetooth, Waveshare UPS HAT (E) mit 4 × 21700 (I2C 0x2D; ältere UPS HAT mit INA219 0x42 werden weiter erkannt), optional INA219 für Solar (0x44, Shunt 0,01 Ω), oder Powerbank / 12-V-Netzteil. Gehäuse: parametrisches Python-Modell (`Gehaeuse/`).
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
