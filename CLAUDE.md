# Motion Watch – Hinweise für Claude

Raspberry-Pi-5-Gerät zur Wildtier- und Personenwarnung beim Camping (Schwenk-/Neigekopf, KI-Erkennung, Wärmebild,
Push-Nachrichten). Besitzer: Daniel (Schweiz). Eventuell später als Produkt vermarkten.
Ausführlicher Stand: `docs/Projekt_MotionWatch_Uebersicht.md`, Einrichtung: `docs/Einrichtung_Raspberry_Pi.md`, Gehäuse: `docs/Uebergabe_Gehaeuse_Licht_Audio.md`.

## Zusammenarbeit

- Deutsch (Schweiz, «ss» statt «ß»), kurz und verständlich. Daniel ist kein Programmierer, aber technisch interessiert.
- Rückfragen nur bei echten Entscheidungen; sonst umsetzen und am Schluss kurz erklären (was neu ist, was getestet ist, was nicht).
- Ehrlich sagen, was nicht getestet werden konnte (echte Hardware, iPhone usw.).
- Keine Passwörter, privaten ntfy-Themen oder Zugangsdaten in Dateien, Commits oder geteilte Pakete.

## Software

- **Eine einzige Datei** `webcam_bewegung_X_Y_Z.py` (Python 3, ca. 14'000 Zeilen). Jede Änderung = **neue Version und neue Datei**
  (alte Dateien bleiben im Repository, die Update-Funktion bietet sie zur Auswahl an).
- Versionsnummer an vier Stellen ändern: `APP_VERSION = "X"`, `Motion Watch X` (Fenstertitel / Startmeldung),
  `{tr('Build')} X ·`, `webcam_bewegung_X.py` (Hilfe) – und eine Zeile `  * X: …` in der Änderungsliste oben in der Datei.
- **Sprachen** (ab 2.28.0): Deutsch, Französisch, Italienisch, Rätoromanisch (Rumantsch Grischun), Englisch. Schlüssel ist immer der
  englische Text. Deutsch: `DE` (Python) bzw. `I18N.de` / `TX` / `ALT` / `WZ` (Web). Französisch / Italienisch / Romanisch: Tabellen
  `TRX["fr"|"it"|"rm"]` und die Anleitung `HELP_X` am Dateiende (das Web lädt sie über `/i18n/<sprache>.js`). Neue Texte in
  allen Sprachen ergänzen; fehlt ein romanischer Text, erscheint Deutsch, bei Französisch / Italienisch Englisch.
- Danach im Repository: `python3 webcam_bewegung_X_Y_Z.py --make-manifest . --sign-key SCHLUESSELDATEI` (schreibt und **signiert**
  `versions.json`), committen, pushen. Ab 2.4.0 installieren die Geräte nur signierte Versionen. Den geheimen Schlüssel
  (`MotionWatch_Signierschluessel.txt`, 64 Hex-Zeichen) hat nur Daniel – bei Bedarf danach fragen; **nie ins Repository** legen.
  Ohne Schlüssel: Version trotzdem hochladen, Daniel signiert später (oder vorübergehend «Auch nicht signierte Versionen annehmen»).
  Der Pi holt Updates von `https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json`.
- **Nur die Hauptversionen** im Repository behalten: pro Hauptversion X.Y nur die neueste Datei (z. B. 2.58.2 statt 2.58.0/2.58.1),
  höchstens die letzten 10 Hauptversionen (Wunsch von Daniel, 25.10.2026). Danach Manifest neu signieren. Ältere Versionen bleiben
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

## Testen (vor jeder Auslieferung)

- `python3 webcam_bewegung_X_Y_Z.py --self-test .` (im Repository: prüft auch alle Signaturen in versions.json). Läuft zusätzlich
  automatisch auf GitHub (Actions → «Selbsttest») bei jedem Push.

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

- Der Ordner `simulator/` ist ein eigenes Programm (motionwatch_simulator.py + motionwatch_sim_interface.py + Anleitung).
- Ab 2.70.0 steckt er auch gepackt in der Motion-Watch-Datei (`SIM_ZIP_B64`, ZIP als base64). **Wer die Simulator-Dateien ändert, muss `SIM_ZIP_B64` neu erzeugen**, sonst installiert Motion Watch die alte Fassung.

## Rückmeldungen aus den Testläufen (ab 2.95.28)

- Daniel lädt Testlauf-Berichte (ZIP aus Motion Watch) nach `feedback/` hoch oder hängt sie im Chat an.
- Vor Arbeiten an der Erkennung: neue Berichte in `feedback/` lesen (JSON und Bilder), daraus Verbesserungen ableiten,
  danach nach `feedback/erledigt/` verschieben. Siehe `feedback/README.md`.
