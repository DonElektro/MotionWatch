# Test-Runner: der Simulator-PC rechnet die langen Tests

Der HP (EliteDesk 800 G1 DM, Ubuntu-Kiosk mit MoveEye Sim) wird ein **eigener GitHub-Actions-Runner** mit dem Label
`moveeye-hp`. Er rechnet auf Abruf oder nach Zeitplan:

- **Erkennung (HP)** (`.github/workflows/erkennung_hp.yml`): der lange Erkennungstest (`werkzeuge/erkennungstest/`), Fall
  für Fall an mehreren Orten und bei mehreren Bedingungen. Von Hand oder jeden Samstag um 22:41 Uhr (Winterzeit) mit Plan «test3».
- **Prüfstand** (`.github/workflows/pruefstand.yml`): von Hand mit «rechner: hp» (sonst wie bisher auf GitHub).
- **Dauerrechnen (HP)** (`.github/workflows/dauer_hp.yml`, ab 3.55.0): rund um die Uhr, solange niemand spielt (Abschnitt unten).

Ergebnisse kommen als **Actions-Artefakt** (JSON und kurzer Bericht) und stehen in der Zusammenfassung des Laufs. Die
Erkennung schreibt nichts ins Repository.

## So arbeiten Kiosk und Tests zusammen

Während eines Jobs **pausiert der Kiosk-Simulator**: der Runner legt vor dem Job die Datei `/run/moveeye-test/kiosk_pause`
an, die Kiosk-Schleife (`kiosk_sitzung.sh`) beendet den Simulator und startet ihn erst nach dem Job wieder (die Datei gilt
höchstens 7 Std., falls etwas hängen bleibt). Der Test startet einen **eigenen** Simulator vom getesteten Stand (Linux-Paket
aus dem Repository, Lite-Grafik, eigener virtueller Bildschirm Xvfb) mit eigenen Einstellungen.

Warum nicht den laufenden Kiosk-Simulator (Port 8765) benutzen? Dort liefe die installierte Version statt des getesteten
Stands, seine Einstellungen und das Bild würden verändert, ein Update oder ein Neustart der Kiosk-Schleife mitten im Test
verdürbe den Lauf, und 4 GB RAM reichen nicht für zwei Simulatoren. Mit Pause ist der Lauf wiederholbar und der Kiosk
bleibt unberührt.

**Testbild (ab 3.53.0):** statt eines dunklen Bildschirms zeigt der Kiosk während des Tests ein Dashboard: «Test läuft –
bitte nicht ausschalten», das Bild, das MoveEye gerade auswertet (mit MoveEyes Rahmen: Personen rot, KI-Objekte farbig mit
Prozent, Bewegung weiss), «Soll / Ist» des laufenden Falls, Fall N/M mit Balken, Start, Dauer und Rest, dazu die Bilanz
bisher (Personen erkannt, Tiere / Autos ignoriert, Leerlauf ruhig, Pushes). Nach dem Test bleibt 2 Min. die
Zusammenfassung stehen, dann startet der Simulator wieder. Die Daten schreibt der Test nach `/run/moveeye-test/`
(`fortschritt.json`, `bild.png`; `erkennungstest.py --fortschritt`, Teil `werkzeuge/erkennungstest/fortschritt.py`); das
Testbild (`simulator3d/beilagen_linux/testbild.py`, braucht `python3-tk`) liest sie nur als Daten. Andere Tests (Prüfstand)
zeigen Logo, Text und Dauer.

## Dauerrechnen (ab 3.55.0)

Der HP rechnet **rund um die Uhr**; der Kiosk ist nicht mehr die Hauptsache. Ohne besonderen Auftrag reihum
(`werkzeuge/test_runner/dauer.py`):

1. **Erkennung messen** – main gegen die Version davor (Tag) und aktive `real-erkennung*`-Zweige (letzte 14 Tage), Pläne
   ursache, kriechen, nacht, tier, wind, je **3 Läufe pro Fall**; ist ein Plan für zwei Stände fertig, steht `vergleich.md` im Artefakt.
   Sind alle Stände gemessen, misst es main zusätzlich mit jeder **Variante** (ab 3.60: `bestaetigung2` = doppelte Bestätigung an;
   Pläne ursache, nacht, wind; `erkennungstest.py --variante`, `dauer.py waehlen --varianten keine` schaltet ab, Umgebung
   `MW_DAUER_VARIANTEN`) und schreibt `varianten.md`: Erkennung, Pushes pro Stunde und falsche Pushes pro Stunde nebeneinander.
   Von Hand: Actions → «Erkennung (HP)» → Variante; `bericht.py --varianten standard=A/results.jsonl bestaetigung2=B/results.jsonl`.
   Stürzt der Simulator oder MoveEye ab, sichert der Test das Protokoll (`simulator_absturz_N.log` bzw.
   `motionwatch_absturz_N.log` im Artefakt), startet neu und rechnet beim selben Fall weiter; stürzt es beim selben Fall
   zweimal ab, wird der Fall übersprungen (`uebersprungen.jsonl`, im Bericht). Code 3 = 8 Abstürze in einem Lauf bzw.
   Neustart gescheitert (Grund mit Code/Signal und Ende von `simulator.log` im Job-Protokoll). Code 7 = Stand nicht brauchbar
   (MoveEye-Datei oder Simulator-Paket `simulator3d/MoveEyeSim3D_Linux.zip` fehlt, alte MoveEye-Fassung kennt die
   Start-Optionen nicht): das Paket wird sofort abgeschlossen, nicht dreimal versucht.
2. **KI-Trainingsbilder** – der Simulator macht Bildpakete (YOLO, Vielfalt hoch, alle Szenen), 6 × 150 Bilder pro Paket,
   höchstens 2 Pakete pro Stand von main. Die ZIPs kommen ins Artefakt; fürs Training von Hand ins Release «ki-daten»
   ziehen (`ki_training/README.md`). Unter Xvfb (ohne Grafikkarte) braucht ein Szenenwechsel bis rund 1 Min. – so lange
   wartet das Werkzeug (`MW_KI_ANTWORT_S`, `MW_KI_STILL_S`); stürzt der Simulator ab, werden die schon fertigen Bilder
   (ab 10) als Teilpaket gesichert und er wird neu gestartet (Protokoll `simulator_absturz_N.log` im Artefakt; 3-mal
   hintereinander ohne gesicherte Bilder = Schluss). Geht es nicht weiter,
   steht der Grund im Job-Protokoll (`::error::`, dazu das Ende von `dauer.log`) und in `fehler.txt` – nicht mehr nur
   «Code 1». Grafik: normal (`MW_KI_GRAFIK=lite` zum Ausprobieren).
3. **Langzeittest** – MoveEye und Simulator 3 Std. im Leerlauf (Nacht, Tag, Nacht mit Regen, Dämmerung je 30 Min.):
   Abstürze, Speicher (und wie er wächst), Fehlalarme pro Nacht, Bilder/s; einmal pro Tag.

Ein Lauf rechnet höchstens 3 Std. (`stunden`) und startet dann selbst den nächsten; der Zeitplan (alle 30 Min.) springt ein,
wenn nichts läuft. Wartet ein Auftrag von Hand (Erkennung (HP), Prüfstand), beginnt kein neues Paket – er kommt zuerst dran.
Gesichert wird pro Fall (Erkennung), pro Bildpaket (KI) bzw. pro Minute (Langzeittest); ein unterbrochener Fall wird beim
nächsten Mal neu gerechnet, nichts anderes geht verloren. Zustand: `/var/lib/mwrunner/dauer/` (die letzten 12 Pakete bleiben).

**Spielen:** Am HP eine Taste drücken oder die Maus bewegen – das Testbild zeigt gross «Spielen?» (Enter oder Klick = ja,
Esc = weiter rechnen); unten rechts steht immer der Knopf «Spielen». Auch Spielen ist: in **MoveEye** im Simulator-Betrieb
den Reiter **Live** bzw. die Sim-Ansicht offen und sichtbar haben (Browser, ebenso das Fenster am Pi: Reiter Live, nicht verkleinert) –
MoveEye meldet das dem HP alle 20 s (`POST /zuschauer` an Port 8761, nur eine Zeitmarke) –, oder ein Handy öffnet die
Spiel-Seite (Port 8770). **Eine Verbindung MoveEye ↔ Simulator allein zählt nicht** (Entscheid Besitzer 03.11.2026: der Pi
bleibt im Simulator-Betrieb dauernd verbunden), die Karte / Seite «HP rechnet» auch nicht. Dann hält der Test in wenigen
Sekunden an, der Test-Simulator ist zu, und der Kiosk-Simulator startet (nie beide zugleich – 4 GB RAM). **15 Min. ohne
Maus, Taste, Controller, Zuschauer und Spieler am Handy** rechnet der nächste Lauf genau dort weiter. Ein Controller
(Gamepad) am HP zählt als Spielen – auch während gerechnet wird (Abschnitt «Controller»).

**Bildschirm:** während des Rechnens schaltet er nach 10 Min. ohne Maus / Taste ab (DPMS), das Testbild zeichnet dann nicht
mehr; Maus oder Taste weckt ihn sofort. Beim Simulator bleibt er an wie bisher.

**Vom Handy zuschauen:** MoveEye → Reiter Simulator → Karte «HP rechnet» (Tipp = ganze Ansicht `/hp`), oder Einstellungen →
Entwickler → «HP rechnet». Nur zuschauen. MoveEye holt die Angaben im eigenen Netz vom HP (`hp_wache.py`, Port 8761, nur
GET, nur private Adressen; mit ufw nur fürs eigene Netz freigegeben) – das Handy redet nie direkt mit dem HP, unterwegs geht
es über den gewohnten Zugang zu MoveEye.

```bash
gh workflow run dauer_hp.yml -R DonElektro/MotionWatch -f arbeit=ki      # eine bestimmte Arbeit jetzt
gh run list -R DonElektro/MotionWatch -w "Dauerrechnen (HP)" -L 5
```

## Controller (PS5 DualSense) am HP

- **Per Kabel (geht immer):** Controller mit USB-C anstecken – Linux kennt ihn von selbst (Treiber `hid-playstation`).
- **Per Bluetooth, ohne Tippen:** im Testbild den Knopf **«Controller koppeln»** (oder Taste **K**), im Kiosk (Simulator
  läuft) **Ctrl+Alt+B**. Dann am Controller **PS-Taste und Create-Taste** gleichzeitig halten, bis das Licht schnell blinkt.
  Ein Fenster zeigt den Fortschritt (Suche bis 60 s → gekoppelt → verbunden). Danach genügt die PS-Taste.
  Ohne Bluetooth-Adapter steht dort «Kein Bluetooth – USB-Stick nötig oder Controller per USB-C-Kabel» (ein USB-Bluetooth-Stick
  genügt, einstecken und noch einmal).
- **Spielen:** jede Taste und jeder deutliche Stick-Ausschlag zählt als Spielen (`hp_wache.py` liest nur `/dev/input/js*`
  bzw. die Joystick-Geräte, die die Kiosk-Sitzung ohnehin lesen darf); das Rechnen hält an, der Simulator startet. Der
  Simulator kennt den DualSense über die eingebaute SDL-Liste von Godot 4.3 (USB und Bluetooth), Tasten wie beim Xbox-Controller
  (Kreuz = A, Kreis = B, Viereck = X, Dreieck = Y, Create = Select, Options = Start).
- **Sicherheit:** der Kiosk-Benutzer bekommt kein root, kein sudo, keine polkit-Regel. Er legt nur die leere Datei
  `/run/moveeye-spiel/controller_koppeln` an; die Pfad-Einheit `moveeye-controller-koppeln.path` startet dann den Dienst
  `moveeye-controller-koppeln.service` (root, `controller_koppeln.sh`), der immer dasselbe tut: Bluetooth an, 60 s suchen,
  nur einen Sony-DualSense koppeln (Hersteller-Kennung 054C), vertrauen, verbinden, Kopplung wieder aus. Der HP selbst wird
  nicht sichtbar gemacht. Fortschritt: `/run/moveeye-controller/status.json` (feste Texte, keine Adressen).
- **Von Hand / prüfen:** `sudo /usr/local/lib/moveeye-kiosk/controller_koppeln.sh`, Protokoll `journalctl -u
  moveeye-controller-koppeln`; aus der Ferne Actions → «HP-Diagnose» (Zeile «Bluetooth: Adapter ja/nein, Controller verbunden …»).
  Eingerichtet wird alles von `moveeye-hp-update` (bluez, rfkill, fehlt der Treiber: `linux-modules-extra` des Kerns).

## 0. Automatisches Update (einmal eintippen)

Am HP (Text-Konsole **Ctrl+Alt+F3** oder SSH), eine Zeile:

```bash
curl -sL github.com/DonElektro/MotionWatch/raw/main/hp | sudo bash
```

Das richtet `moveeye-hp-update` ein und lässt es gleich einmal laufen. Danach schaut der HP **alle 15 Min.** nach, ob gerade
eine **Pause** ist (kein Test, niemand spielt), und prüft dann – höchstens alle 6 Std. und **8 Min. nach jedem Start** – die
neueste **signierte** Version; ist die letzte Prüfung über 20 Std. her, lässt das Dauerrechnen den HP frei, bis sie gelaufen
ist (so mindestens einmal am Tag). Es spielt ein, was sich geändert hat:
Kiosk (`kiosk_sitzung.sh`, Testbild), Haken und Dienst-Einstellungen des Runners, fehlende Pakete, den Simulator im
Kiosk-Ordner und sich selbst (ab 3.55.0 auch `hp_wache.py` und den Ordner `/run/moveeye-spiel`, mit HP_FASSUNG 4 auch
«Controller koppeln»: bluez, Dienst, Ctrl+Alt+B). Die Anmeldung des Runners
(Token) fasst es nie an. Läuft ein Test oder wird gespielt, wird verschoben (nächster Blick in 15 Min.).

Geprüft wird wie beim Pi: Signatur (Ed25519, öffentlicher Schlüssel im Skript) des Eintrags in `versions.json` →
Prüfsumme der Programmdatei → darin die Prüfsumme des Linux-Pakets (`SIM3D_LINUX`) → `MoveEyeSim3D_Linux.zip`, das den
Kiosk und den HP-Teil (`hp/`) enthält. Stimmt etwas nicht, wird nichts eingespielt; ältere Versionen werden abgelehnt.

```bash
sudo moveeye-hp-update --status      # eingespielte Version, nächster Termin, letzte Zeilen des Protokolls
sudo moveeye-hp-update               # jetzt sofort
moveeye-hp-update --pruefen          # nur laden und prüfen, nichts einspielen
sudo moveeye-hp-update --entfernen   # Zeitplan aus (eingespielte Dateien bleiben)
```

Protokoll: `/var/log/moveeye-hp-update.log`. Den Simulator nicht ersetzen: `SIMULATOR=nein` in
`/etc/moveeye-hp-update.conf`. `runner_einrichten.sh` und der USB-Installer richten das Update von selbst mit ein.

## 1. Einrichten (am HP, einmal, etwa 10 Min.)

Am HP eine Text-Konsole öffnen: **Ctrl+Alt+F3**, anmelden als `don`. (Zurück zum Kiosk: Ctrl+Alt+F1 bzw. F7.)
Einfacher ist SSH von einem anderen PC, dann lässt sich der Token einfügen: `ssh don@moveeye-sim`.
Tastatur falsch? `sudo loadkeys ch`. Das Zeichen `~` braucht es nirgends.

```bash
cd /home/don
curl -fLo runner_einrichten.sh https://raw.githubusercontent.com/DonElektro/MotionWatch/main/werkzeuge/test_runner/runner_einrichten.sh
sudo bash runner_einrichten.sh
```

(Vor dem Zusammenführen in main: in der Adresse `main` durch `real-test-runner` ersetzen und
`sudo bash runner_einrichten.sh --zweig real-test-runner` starten.)

Das Skript zeigt, was es tut, und fragt «Fortfahren? (j/n)». Danach fragt es nach dem **Token**:

1. Im Browser: <https://github.com/DonElektro/MotionWatch> → **Settings** → **Actions** → **Runners** →
   **New self-hosted runner**.
2. **Linux** und **x64** wählen. Im Abschnitt «Configure» steht eine Zeile `./config.sh --url … --token XXXX`.
   Nur **XXXX** kopieren (gilt 1 Stunde). Die Befehle «Download» und «Configure» dort **nicht** ausführen – das macht das Skript.
3. Token einfügen bzw. abtippen, Enter. Die Eingabe bleibt unsichtbar und wird nirgends gespeichert.

Danach einmal neu starten, damit der Kiosk die Pause-Funktion kennt: `sudo reboot`.

Optionen: `--bildschirm` erlaubt den Tests, den echten Bildschirm (Grafikkarte HD 4600) statt Xvfb zu benutzen
(Workflow-Eingabe «anzeige: bildschirm»). Das ist schneller, gibt dem Runner-Benutzer aber Zugriff auf die Anzeige –
nur einschalten, wenn am HP nichts anderes als der Kiosk läuft. `--name NAME` für einen anderen Runner-Namen.

## 2. Prüfen, ob der Runner online ist

- GitHub → Settings → Actions → **Runners**: `moveeye-hp` steht dort mit **Idle** (grün) bzw. **Active** während eines Jobs.
  «Offline» = HP aus, kein Netz oder Dienst gestoppt.
- Am HP: `systemctl status 'actions.runner.*'` (läuft = «active (running)»), Protokoll:
  `journalctl -u 'actions.runner.*' -n 50`.
- Von einem PC mit `gh`: `gh api repos/DonElektro/MotionWatch/actions/runners --jq '.runners[] | [.name, .status, .busy] | @tsv'`
  (braucht Admin-Rechte am Repository).
- Erster Test: Lauf mit Plan **kurz** (etwa 5 Min., siehe unten).

## 3. Einen Lauf starten und die Ergebnisse holen

Auf GitHub: **Actions → Erkennung (HP) → Run workflow**. Eingaben:

| Eingabe | Bedeutung |
|---|---|
| `stand` | Zweig oder Commit dieses Repositorys (MoveEye und Simulator von diesem Stand), Standard `main` |
| `plan` | `test3` (Test 3, etwa 2–3 Std.), `alle`, `wind`, `tier`, `kriechen`, `nacht`, `ursache`, `real` (echte Situationen: Dieb ums Zelt, Velo-Diebstahl; 6 Fälle à 2–5 Min.), `kurz` (etwa 5 Min.) |
| `laeufe` | Läufe pro Personenfall, 1–5 (der Simulator wählt die Richtung jedes Mal neu) |
| `simulator` | `paket` (Linux-Paket des Stands, Standard) oder `godot` (aus dem Quelltext – für noch nicht veröffentlichte Simulator-Änderungen; lädt Godot 4.3 einmal) |
| `anzeige` | `xvfb` (Standard) oder `bildschirm` (nur mit `--bildschirm` eingerichtet) |
| `warten` | so viele Minuten auf den HP warten, dann abbrechen (Standard 15) |

Mit `gh` (Besitzer oder Claude):

```bash
gh workflow run erkennung_hp.yml -R DonElektro/MotionWatch -f stand=real-mein-zweig -f plan=test3 -f laeufe=2
gh run list -R DonElektro/MotionWatch -w "Erkennung (HP)" -L 3          # Lauf-Nummer (ID) ablesen
gh run watch -R DonElektro/MotionWatch <ID>                             # zuschauen (optional)
gh run download -R DonElektro/MotionWatch <ID> -D erkennung_<ID>        # Artefakt holen
python3 werkzeuge/erkennungstest/bericht.py erkennung_<ID>/*/results.jsonl --vergleich ALT/results.jsonl
```

Prüfstand auf dem HP: `gh workflow run pruefstand.yml -R DonElektro/MotionWatch -f rechner=hp -f plaene=quick,night`.
Seine Zeilen in `VERLAUF.md` heissen «HP EliteDesk 800 G1 …» und werden nur mit Läufen vom selben Rechner verglichen.

Im Artefakt `erkennung-<plan>-<nr>`: `results.jsonl` (ein Fall pro Zeile), `ergebnis.json` (Kennzahlen und Angaben zum
Lauf), `bericht.md` (kurzer Bericht, steht auch in der Zusammenfassung), `ablauf.log`, `motionwatch.log`,
`simulator.log`, `bilder/` (Bild beim Erkennen und in der Mitte jedes Falls). Aufbewahrt 30 Tage.

Ist der HP aus, bricht der **Wächter** den Lauf nach `warten` Minuten mit einem Hinweis ab (sonst bliebe er bis zu 24 Std.
in der Warteschlange). Rechnet der HP gerade etwas anderes, wartet der Wächter weiter. Es läuft immer nur ein Job
gleichzeitig; ein dritter Lauf ersetzt einen noch wartenden zweiten.

## 4. Entfernen

```bash
sudo bash /usr/local/lib/moveeye-runner/runner_entfernen.sh
```

Für das Abmelden bei GitHub fragt es nach einem **Entfernen-Token**: GitHub → Settings → Actions → Runners → `moveeye-hp`
→ **Remove** → Token aus der angezeigten Zeile kopieren. Ohne Token (Enter) wird nur am HP entfernt; den Runner danach auf
GitHub von Hand löschen. Entfernt werden Dienst, Haken, Pause-Einstellung, Benutzer `mwrunner` und `/var/lib/mwrunner`.
Pakete bleiben, der Kiosk läuft wie vorher.

## 5. Sicherheit (öffentliches Repository)

Ein eigener Runner an einem öffentlichen Repository führt Code aus GitHub auf dem HP aus. Darum:

- **Einstellung auf GitHub (bitte einmal setzen):** Settings → Actions → General → «Fork pull request workflows from outside
  collaborators» → **Require approval for all outside collaborators** (je nach Stand von GitHub auch «Approval for running
  fork pull request workflows from contributors» → «Require approval for all external contributors»). So startet ein Pull-Request von Fremden nie von
  selbst einen Workflow.
- Die Workflows für den HP laufen **nur** von Hand (`workflow_dispatch`), nach Zeitplan oder bei Push auf `main` – **nie**
  bei `pull_request` oder `pull_request_target`. Jeder Job hat `if: github.repository_owner == 'DonElektro'` (in Forks läuft nichts).
- Der Haken vor jedem Job lehnt zusätzlich alles ab, was nicht von Hand, nach Zeitplan oder per Push kommt, und Workflows,
  die nicht vom Stand `main` stammen (`/etc/moveeye-runner.conf`, `ERLAUBTE_REFS`). Welcher Code getestet wird, wählt die
  Eingabe `stand` – nur Zweige und Commits dieses Repositorys, keine Commits aus Forks oder Pull-Requests.
- Der Runner läuft als eigener Systembenutzer **`mwrunner`** ohne sudo, ohne Passwort und ohne Anmeldung, im Dienst mit
  `NoNewPrivileges`, ohne Zugriff auf `/home` (`ProtectHome`), `/usr` und `/etc` nur lesend, höchstens etwa 3,4 GB RAM.
- Nach jedem Job wird der Arbeitsordner geleert; der Token wird nie gespeichert (nur der Runner selbst hält seine eigenen
  Zugangsdaten in `/var/lib/mwrunner/runner`, lesbar nur für `mwrunner`).
- Keine Geheimnisse in diesen Workflows: der Signierschlüssel kommt nie auf den HP.
- Nicht mehr gebraucht? Entfernen (Abschnitt 4) oder auf GitHub den Runner löschen – dann läuft dort nichts mehr.
