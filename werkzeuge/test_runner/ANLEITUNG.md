# Test-Runner: der Simulator-PC rechnet die langen Tests

Der HP (EliteDesk 800 G1 DM, Ubuntu-Kiosk mit MoveEye Sim) wird ein **eigener GitHub-Actions-Runner** mit dem Label
`moveeye-hp`. Er rechnet auf Abruf oder nach Zeitplan:

- **Erkennung (HP)** (`.github/workflows/erkennung_hp.yml`): der lange Erkennungstest (`werkzeuge/erkennungstest/`), Fall
  für Fall an mehreren Orten und bei mehreren Bedingungen. Von Hand oder jeden Samstag um 22:41 Uhr (Winterzeit) mit Plan «test3».
- **Prüfstand** (`.github/workflows/pruefstand.yml`): von Hand mit «rechner: hp» (sonst wie bisher auf GitHub).

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
| `plan` | `test3` (Test 3, etwa 2–3 Std.), `alle`, `wind`, `tier`, `kriechen`, `nacht`, `ursache`, `kurz` (etwa 5 Min.) |
| `laeufe` | Läufe pro Personenfall, 1–5 (der Simulator wählt die Richtung jedes Mal neu) |
| `simulator` | `paket` (Linux-Paket des Stands, Standard) oder `godot` (aus dem Quelltext – für noch nicht veröffentlichte Simulator-Änderungen; lädt Godot 4.3 einmal) |
| `anzeige` | `xvfb` (Standard) oder `bildschirm` (nur mit `--bildschirm` eingerichtet) |
| `warten` | so viele Minuten auf den HP warten, dann abbrechen (Standard 15) |

Mit `gh` (Daniel oder Claude):

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
