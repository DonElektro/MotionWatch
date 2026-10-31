# MoveEye (früher Motion Watch) – Hinweise für Claude

**Name ab 2.96.0: MoveEye** (Logo E6a-4: Sichtfeld, Auge unten, gehende Person in Erkennungs-Ecken). In allen sichtbaren Texten «MoveEye»; interne Namen bleiben (Dateien `webcam_bewegung_*.py`, Ordner `~/.config/motionwatch/`, Repository, `"app": "Motion Watch"` in Protokollen wie versions.json und der Geräte-Suche, Basic-Realm ab 2.98.19 «MoveEye»).

Raspberry-Pi-5-Gerät zur Wildtier- und Personenwarnung beim Camping (Schwenk-/Neigekopf, KI-Erkennung, Wärmebild,
Push-Nachrichten). Besitzer: Daniel (Schweiz). Eventuell später als Produkt vermarkten – Zielgruppen (Daniel, 29.10.2026):
Camper (Zelt, Wohnmobil), Haus und Garten, Wildtier-Beobachter, allgemeine Bewachungsaufgaben; Vertriebsform noch offen.
Ausführlicher Stand: `docs/Projekt_MotionWatch_Uebersicht.md`, Einrichtung: `docs/Einrichtung_Raspberry_Pi.md`, Gehäuse: `docs/Uebergabe_Gehaeuse_Licht_Audio.md`.

## Zusammenarbeit

- Deutsch (Schweiz, «ss» statt «ß»), kurz und verständlich. Daniel ist Robotik-Entwickler (programmiert selbst) – trotzdem kurz und verständlich erklären.
- Rückfragen nur bei echten Entscheidungen; sonst umsetzen und am Schluss kurz erklären (was neu ist, was getestet ist, was nicht).
- Ehrlich sagen, was nicht getestet werden konnte (echte Hardware, iPhone usw.).
- Keine Passwörter, privaten ntfy-Themen oder Zugangsdaten in Dateien, Commits oder geteilte Pakete.
- **Konzept-Prüfung bei jeder Änderung (Wunsch Daniel, 28.10.2026):** Jede neue Funktion vor dem Einbau auf Doppelbelegungen
  prüfen (gibt es das schon an einer anderen Stelle, im Web, im Fenster, im Simulator?) und ob sie optisch und funktional ins
  Konzept passt (6 Reiter Live · Schutz · Verlauf · Einstellungen · Simulator · Mehr; Simulator: Leiste = Bewegen/Ansicht,
  Kacheln = Inhalte, Karte «Testen»; Zustand heisst Aus / Wachsam / Voll; eine Sperre für Simulator-Aufgaben). Passt etwas nicht
  oder gibt es eine Doppelung, das Daniel im Schlussbericht ausdrücklich melden (Abschnitt «Konzept-Check»), mit Vorschlag.
- **Gleiches Aussehen MoveEye ↔ Simulator (Wunsch Daniel, 30.10.2026):** Bedienelemente, die es in beiden gibt (z. B. die drei
  Aufklapp-Knöpfe «Alle zuklappen · Nur Gruppen · Alle aufklappen», Suchfeld, Schalter Einfach/Experte, Symbole, Farben, aktive
  Zustände blau), in beiden gleich oder möglichst ähnlich bauen. Bei jeder optischen Änderung im einen Projekt das andere
  prüfen und mitziehen; im Konzept-Check melden, wenn es (noch) abweicht.
  **Verschärft (Daniel, 30.10.2026 20:00):** auch die **Menüstruktur** (Gruppen, Reihenfolge, Namen, Einfach/Experte,
  Karten) soll in beiden Projekten grosse Ähnlichkeit haben. Daniel **aktiv erinnern**, sobald etwas abweicht oder nicht ins
  gemeinsame Schema passt (in jedem Bericht und bei jedem Vorschlag), mit Vorschlag zum Angleichen.
- **Zwischenberichte (Wunsch Daniel, bis 2.11.2026 24:00):** bei jeder Aufgabe, die länger als 3–4 Minuten dauert, jede Minute
  eine kurze Checkliste senden (✅ erledigt / ⏳ offen).
  **Pausiert (Daniel, 30.10.2026 10:58):** vorerst keine Zwischenberichte, nur melden, wenn es News gibt (fertig, Problem, Frage).
- **Vor jeder Änderung bestätigen lassen (Wunsch Daniel, 30.10.2026 11:18):** bevor eine Änderung gebaut wird (auch kleine,
  auch Helfer starten), zuerst einen kurzen Fragekatalog (AskUserQuestion) mit dem geplanten Vorgehen und den Optionen stellen
  und erst nach Daniels Antwort umsetzen. Ausnahme: reine Lese-/Prüfarbeit (Analyse, Status, Tests ohne Änderung).
- **Kritisch hinterfragen (Wunsch Daniel, 30.10.2026 22:00):** passt ein Wunsch oder Vorschlag nicht zum Konzept oder zum
  jetzigen Projektstand (z. B. Hardware noch nicht da, Menüs werden wieder länger, Doppelung, Nebenschauplatz), das **vor dem Bau
  offen sagen** und begründen, damit Daniel den Weg stoppen kann – nicht einfach umsetzen.
- **Fragen immer als Fragekatalog (Wunsch Daniel, 29.10.2026):** wenn Daniel nichts anderes wünscht, jede Rückfrage als
  Auswahl-Katalog stellen (AskUserQuestion: bis 4 Fragen à 4 Antworten, Mehrfachauswahl wo sinnvoll), nicht als Fliesstext.
  **Ergänzung (Daniel, 31.10.2026 03:02):** für ALLE Entscheide den Fragebogen verwenden, aber **zuerst ankündigen**
  («Fragebogen zu X kommt – sag "weiter", wenn du bereit bist») und den Turn beenden; erst nach Daniels «weiter» den Fragebogen
  zeigen, damit er sich vorher Notizen machen kann. Erklärungen/Vorschläge allein schicken, nie zusammen mit dem Popup.
  **Ergänzung (Daniel, 31.10.2026 11:40):** statt auf «weiter» zu warten, ganz am Schluss einen kleinen «Button» zeigen:
  Mini-Frage «Fragebogen … starten?» mit «Los» / «Noch nicht»; erst nach «Los» den eigentlichen Fragebogen.
- **Zusammenfassung / Stand (Daniel, 31.10.2026 11:52):** wenn Daniel nach Stand, Übersicht oder Zusammenfassung fragt,
  immer als kleine Tabelle «Teil | Stand» mit Prozenten pro Paket (geschätzt, kurz sagen woraus) und Zeile «Gesamt»,
  darunter höchstens 1–2 Sätze. Knapp und klein.
- **Kurzzeichen «st» (Daniel, 31.10.2026 13:18):** schickt Daniel nur «st», sofort den Kurzbericht: Tabelle «Teil | Stand»
  (Prozent je Paket + «Gesamt»), darunter eine Zeile «Zuletzt veröffentlicht: …» und eine Zeile «Wartet auf dich: …»
  (offene Entscheide, sonst «nichts»). Kein weiterer Text.
- **Kurzzeichen (Daniel, 31.10.2026 22:14):**
  - st: Stand
  - neu: seit der letzten Frage veröffentlicht, mit «So testest du»
  - ot: offene To-dos und Notizen
  - nt: Sammelliste «nicht getestet»
  - ok: weiter wie empfohlen
  - halt: alles anhalten, nichts veröffentlichen
  - los: nach halt weiter
  - bild: aktuelle Bilder vom letzten Paket
  - lang: nächste Antwort ausführlich
  - x: die Liste der Kurzzeichen kurz anzeigen (ohne Nachfrage)

  Ausser bei st und x kurz nachfragen, was genau gemeint ist, bevor gehandelt wird.
- **Arbeit verteilen (Daniel, 31.10.2026 04:24):** grössere Aufträge in möglichst viele unabhängige Pakete aufteilen und
  parallel an Helfer geben – bevorzugt Helfer auf eigenen Cloud-Rechnern (Agent mit isolation "remote"), damit der lokale
  Rechner nicht überlastet. Jeder Helfer: eigener Zweig, kein Release, keine Rückfragen bei bestätigten Paketen; zusammengeführt
  und veröffentlicht wird nur im Haupt-Chat, ein Paket nach dem anderen.
- **Kurz schreiben (Daniel, 31.10.2026 04:36):** Text, den Daniel lesen muss, möglichst knapp halten – nur Ergebnis,
  Entscheid, nicht getestet; keine langen Aufzählungen.
- **Kurz fürs Handy (Daniel, 31.10.2026 21:08):** Nachrichten so kurz halten, dass Daniel auf dem Handy nicht scrollen muss:
  wenige Zeilen, Tabellen oder kurze Listen, Details nur auf Nachfrage.
- **Pause für Realismus aufgehoben (Daniel, 31.10.2026 00:53):** bis die Hardware da ist, Realismus/Szenen in kleinen Paketen,
  je Paket eine Version mit «So testest du». Danach Pause und Hardware-Aufbau.

## Offene Erinnerungen an Daniel

- **Hardware-Test (Wunsch Daniel, 29.10.2026):** sobald die Hardware zusammengebaut ist, daran erinnern und testen: Wärmebild
  (Thermal-90), Servos (Schwenken / Neigen, Richtung, Nachschwingen), Lautsprecher (Wecker-Melodie, Sirene), Licht, Mikrofon,
  Gesten des Weckers mit echter Kamera (Tag und Infrarot), Klatschschalter, Akku-Anzeige. Danach echte Testnächte als Bericht
  in `feedback/` hochladen lassen. Bei jeder grösseren Antwort kurz nachfragen, ob die Hardware inzwischen bereit ist.
  Stand 29.10.2026 17:40: **Camera Module 3 NoIR ist da und läuft** am Pi 5 (192.168.1.56, Videoquelle «Raspberry Pi camera»,
  ab 2.98.24). Noch fehlend: Wärmebild, Servos, Licht, Ton, Akku.

- **Gehäuse-Erinnerung (Daniel, 30.10.2026 21:49):** sobald Daniel am Gehäuse arbeitet, daran erinnern: **Aussparung für eine
  Farb-LED oben auf dem Kopf** (zeigt den Schutzzustand in Farbe: grün / orange / rot). Siehe `docs/Gehaeuse_Variante2_Weitwinkel.md`.

## Schwerpunkte (Antworten Daniel, 30.10.2026 11:12)

- MoveEye im Alltag: keine besonderen Störungen genannt.
- Nächste Wochen: vor allem **Entwicklung und Tests mit dem Simulator** (Hardware folgt).
- Simulator: **Realismus, Spielspass und Bedienung** gleich wichtig (Tempo nicht erste Priorität).

## Offene Aufträge (Stand 30.10.2026 14:00, MoveEye 2.98.48 / Simulator 3D-4.19)

- Wartet auf Daniel: Hardware-Tests; Gehäuse Variante 2 (Modell-ZIP); Tailscale Funnel (eingebaut 2.98.47) im Tailnet freischalten und echt testen;
  SmallTV (2.98.48) am echten Gerät testen (Testbild, Album-Weiterblättern, Suche, Lesbarkeit); KI-Wächter bei normalem Tempo; Parcours-Noten;
  Rückmeldung schwarzes Live-Bild / Seiten-Tempo; vor KI-Training «🔍 Lernbilder prüfen».
- **Entscheid Daniel 30.10.2026 22:00:** nach der laufenden Runde (Angleichen, Mehr-Bereich Simulator, Sprachen Schritt 1,
  LED/Tasten) **Pause bei neuen Funktionen** → Hardware-Aufbau mit geführter Inbetriebnahme (sobald Teile da sind).
  Gameplay-Plan und Sprachen Schritt 2 danach.
- Als Nächstes (nach wt-objekte): Angleichungen MoveEye ↔ Simulator (Entwickler-Schalter teilen, «Dein Platz» klären, /sim
  zuklappen statt ausblenden, Fenster «Strom»/System-Knöpfe, gezeichnete Symbole statt fehlender Emoji), dann Gameplay
  (`docs/Gameplay_Ausfeilen_Plan.md`).
- **Erinnern (Daniel 30.10.2026 21:45):** Simulator in den Sprachen FR/IT/RM/EN wie MoveEye – Daniel wartet noch, später daran erinnern.
- Vorgemerkt (nicht bauen, Daniel 30.10.): BME280-Erweiterungen (Taupunkt-/Frost-Warnung, Anzeige wenn Sensor fehlt, Akku-Kälte) –
  erst wenn die Grund-Hardware läuft.
- Vorgemerkt (nicht bauen, Daniel 30.10. 23:14): **Zwei MoveEye koppeln** für mehr Reichweite/Überwachungsbereich – erst nach
  Hardware-Aufbau, wenn ein zweites echtes Gerät läuft. Basis ist Teil 260 «mehrere Geräte» (Übersicht, alle ein/aus, Suche,
  Übergabe; braucht gleiches Netz). Stufen: 1) Koppeln per Code/QR, Gerät B verbindet sich selbst mit Hotspot von A, gemeinsamer
  Schutz/Alarmübersicht, Push mit Gerätename (klein, ~30–80 m); 2) USB-WLAN mit externer Antenne (~100–200 m, braucht
  Antennen-Durchführung im Gehäuse); 3) Kette A↔B↔C mit Weiterleitung (mittel); 4) LoRa nur für Alarme (gross, neue Hardware).
  Empfehlung: mit Stufe 1 beginnen.
- Notiz: Live-Chips verdichtet in 2.98.54 (Handy: Status-Chips in einer Zeile zum Wischen, Sticks wieder 140 px).
- Später: Prüfstand-Plan «funktionen» (Kurzproben Sabotage, Wecker, Klatschen, Diebstahl, Sensoren, Akku, Sirene – Daniel 30.10.: später); Prüfstand-Rückgang ab 2.98.23; KI-Training (Token Actions-Rechte, Trainingspaket); «Vertrauenswürdige Geräte» nur
  Admin; Controller-Einstellungen als MoveEye-Einstellung statt pro Browser; Produkt-Seite (Lizenzen, Datenschutz, Kundendoku);
  mobiler MoveEye (Laufroboter, nur Notiz); Tiere mit der neuen Figur-Technik (figur.gd).

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
- **Prüfstand sparsam (Wunsch Daniel, 29.10.2026):** pro Version läuft auf GitHub nur «quick»; die grossen Läufe sonntags
  oder von Hand (Actions → Prüfstand → Run workflow). Offen: Rückgang ab 2.98.23 (Bilder/s 4.6 → 2.8, Nacht schlechter) –
  Zwischenstand der Suche in `pruefstand/RUECKGANG_2_98_23.md`, später weitermachen.
- **Sprachen** (ab 2.28.0): Deutsch, Französisch, Italienisch, Rätoromanisch (Rumantsch Grischun), Englisch. Schlüssel ist immer der
  englische Text. Deutsch: `DE` (Python) bzw. `I18N.de` / `TX` / `ALT` / `WZ` (Web). Französisch / Italienisch / Romanisch: Tabellen
  `TRX["fr"|"it"|"rm"]` und die Anleitung `HELP_X` am Dateiende (das Web lädt sie über `/i18n/<sprache>.js`). Neue Texte in
  allen Sprachen ergänzen; fehlt ein romanischer Text, erscheint Deutsch, bei Französisch / Italienisch Englisch.
- Danach im Repository: `python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI` (schreibt und **signiert** `versions.json`,
  dann Selbsttest), committen, pushen. Ab 2.4.0 installieren die Geräte nur signierte Versionen. Den geheimen Schlüssel
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

## Versionierung (Entscheid Daniel, 31.10.2026 – gilt ab dem Release 3.0.0)

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
- **Zusatzdatei** (Entscheid Daniel 31.10.2026, Paket «MoveEye-Datei verkleinern»): `bauen.py` lagert grosse Literale
  (Web-Seiten, JavaScript, Bilder als base64, Übersetzungen fr/it/rm, ältere Einträge der Änderungsliste) in
  `moveeye_daten_X_Y_Z.zip` neben `webcam_bewegung_X_Y_Z.py` aus; `quelle/` bleibt unverändert. Die Hauptdatei kennt die
  SHA-256 der ZIP (`ZD_SHA256`, Teil 012) – die Signatur der Hauptdatei bürgt so auch für die ZIP; zusätzlich steht sie mit
  eigener Signatur unter `"data"` in versions.json. **Beide Dateien gehören zusammen ins Repository** (`git add` beider).
  Ohne ZIP startet MoveEye im Kern (Kamera, Erkennung, Alarm, Push, Fenster; Web-Seiten zeigen «Zusatzdaten fehlen – Update»)
  und holt sie über dieselbe Update-Quelle (Teil 397), dann ein Neustart. Ziel Hauptdatei unter 5 MiB, Pflicht unter 8 MiB
  (`versionen.py --pruefen`) – so gehen auch Geräte bis 2.98.x direkt auf die neueste Version.
- **Brücke** (Entscheid Daniel 31.10.2026): `webcam_bewegung_3_0_2.py` (eine Datei unter 8 MiB, ohne Zusatzdatei) bleibt
  **für immer** im Repository und in versions.json (`"bridge": true`, `BRUECKE` in `versionen.py`, `UPD_BRIDGE` in Teil 397).
  Beim Aufräumen («höchstens 10») nie löschen – `python3 werkzeuge/versionen.py --aufraeumen` lässt sie stehen (sie zählt mit).
  Wäre eine Hauptdatei je über 8 MiB, schreibt `--make-manifest` `"needs": "3.0.0"` in ihren Eintrag: Geräte ab dieser Fassung
  nehmen dann zuerst die Brücke und danach die neueste (`update_pick`, Teil 397). Ältere Geräte (2.98.x bis zur letzten Version ohne Zusatzdatei) wählen immer die
  neueste – für sie ist die 8-MiB-Grenze der Hauptdatei die eigentliche Sicherung, 3.0.2 von Hand in der Liste der Rückweg.
- **Release-Ablauf ab 3.0.0** (nur der Koordinator, Schlüssel nur bei Daniel):
  1. Nummer wählen (Regeln oben); `VERSION := "X.Y.Z"` in `simulator3d/scripts/main.gd`, Block `NEU IN X.Y.Z` in
     `simulator3d/Lies mich.txt`, Kopf von `simulator3d/UEBERGABE.md`.
  2. Simulator exportieren und ZIP packen, dann `python3 werkzeuge/versionen.py --neu-data` (vor dem Export) und
     `python3 werkzeuge/versionen.py --sim-json X.Y.Z "Notiz"` (schreibt `version.json` mit `version` + `ver`).
  3. `python3 werkzeuge/bauen.py --version X.Y.Z --neue-version "Was neu ist"` (oder `--stufe funktion|fehler|gross` statt
     `--version`); übernimmt `ver` aus `version.json` in `SIM3D` (Teil 300).
  4. `python3 werkzeuge/versionen.py --pruefen` (eine Nummer überall, Brücke stimmt, Hauptdatei unter 8 MiB, Zusatzdatei und
     Brücken-Datei da), dann `bauen.py --signieren …`
     (Selbsttest prüft dasselbe noch einmal: «Version numbers …»), Rauchtest, committen, pushen.

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
- Ab 2.70.0 steckt er auch gepackt in der Motion-Watch-Datei (`SIM_ZIP_B64`, ZIP als base64). **Wer die Simulator-Dateien ändert, muss `SIM_ZIP_B64` (in `quelle/360_daten_simulator_python.py`) neu erzeugen**, sonst installiert Motion Watch die alte Fassung.

- **Daten aus dem Simulator** (Wunsch Daniel): nur bildbezogene, kartenunabhängige Daten für die Erkennung sammeln (Bilder mit
  Rahmen, Reaktionszeit nach Abstand/Haltung/Licht). Kartengebundenes (Schleichwege) immer mit Szene speichern und nur dort
  abspielen. Später geplant: Bediener baut sein Zuhause im Simulator nach und trainiert Motion Watch darauf.

## Rückmeldungen aus den Testläufen (ab 2.95.28)

- Daniel lädt Testlauf-Berichte (ZIP aus Motion Watch) nach `feedback/` hoch oder hängt sie im Chat an.
- Vor Arbeiten an der Erkennung: neue Berichte in `feedback/` lesen (JSON und Bilder), daraus Verbesserungen ableiten,
  danach nach `feedback/erledigt/` verschieben. Siehe `feedback/README.md`.
