# Auftrag für Claude: Python-Weltsimulator fertig an Motion Watch anbinden

Diese Datei ist für die Claude-Instanz, die am **Python-Weltsimulator** (`simulator_python/`) arbeitet.
Geschrieben vom Claude, der Motion Watch (`webcam_bewegung_*.py`) betreut, nach einem echten Test am 27.10.2026.

## 1. Stand: Was schon funktioniert (getestet mit Motion Watch 2.95.0 und PY-1.0)

Der Simulator lief ohne Fenster (`python3 motion_sim.py --no-panel --stream`, Port 8767).
Motion Watch war damit verbunden, und jeder Regler wurde über die Webseite bedient:

- **Einstellungen (CONTROL-Protokoll 1): alles in Ordnung.** Alle 17 Regler kommen richtig im Simulator an:
  - Auswahl: Kamera-Platz, Wetter, Bildqualität
  - Schieber: Uhrzeit, Wind, Temperatur, Personen, Hunde usw.
  - Schalter: Pause, Echte Uhrzeit, Linse zugehalten usw.
  - Knöpfe: «Person schicken», «Gas-Alarm», «Tür auf», «Alle wegschicken»
  - Szenario wechseln: «Lake», danach erscheinen die neuen Kamera-Plätze.

  Die Gruppen Szene, Wetter, Besuch, Störungen, Sensoren und Bild erscheinen als aufklappbare Abschnitte im Reiter «Simulator».
- `/info`, `/state`, beide Kameras, `/thermal.bin`, `/events` (PIR, Tür, Gas) und die UDP-Meldung auf Port 8764 funktionieren.
- `?fps=` beim MJPEG-Strom wird beachtet. Das braucht Motion Watch für «CPU schonen».
- **Download:** Motion Watch 2.95.0 hat einen Knopf «Python-Weltsimulator (ZIP)» im Reiter Simulator unter «Programme und Downloads».
  - Adresse: `/sim/simulator_py.zip`
  - Der Pi holt dafür `simulator_python/MotionWatchSimulator.zip` aus dem Projekt und prüft Grösse und Prüfsumme.
    Diese Werte stehen fest in Motion Watch (Version PY-1.0).

## 2. Regeln (wichtig, weil zwei weitere Claude-Chats im selben Projekt arbeiten)

- Arbeite **nur im Ordner `simulator_python/`**.
- Nicht ändern:
  - `webcam_bewegung_*.py`
  - `versions.json`
  - `simulator3d/`
  - `simulator/`
  - andere Ordner

  Wenn Motion Watch etwas Neues braucht, schreib es unten in Abschnitt 5. Daniel gibt es dann an den Motion-Watch-Chat weiter.
- Vor jeder Arbeit `git pull`. Nie `git push --force`. Nie fremde Dateien überschreiben.
- Keine Passwörter, keine privaten Daten und keine Ordner `data/` mit persönlichen Einstellungen ins Projekt (das Projekt ist öffentlich).

## 3. Was du noch korrigieren sollst

### 3.1 Absturz ohne Fenster (wichtig für den Raspberry Pi)
`motion_sim.py` lädt `simulator.ui.start` immer. Diese Datei macht gleich am Anfang `import tkinter`.
Auf einem Pi ohne `python3-tk` stürzt der Simulator deshalb auch mit `--no-panel` ab:
`ModuleNotFoundError: No module named 'tkinter'`

So korrigieren:
- `start.py` erst laden, wenn das Startfenster wirklich gezeigt wird.
- `load()` und `apply()` so machen, dass sie ohne tkinter gehen, zum Beispiel in eine eigene kleine Datei ohne tkinter auslagern.

Test: `python3 -c "import sys; sys.modules['tkinter']=None; ..."` oder einfach auf einem Rechner ohne tkinter mit `--no-panel` starten.

### 3.2 Webseite von Motion Watch: Port und https aus `/state` nehmen
`bridge.py` nimmt immer `http://<IP>:5000`. Motion Watch schickt aber bei jedem `POST /state` mit, wo seine Webseite ist:

```json
"mw_scheme": "https",   // oder "http"
"mw_port": 5000
```

So korrigieren:
- Diese zwei Felder in `bridge.note_client` übernehmen.
- Achtung: `MWState.from_dict` wirft unbekannte Felder weg. Lies sie also aus dem rohen JSON, bevor es zu `MWState` wird.

Bei `https` hat Motion Watch ein **selbst unterschriebenes Zertifikat**:
- Die Zertifikatsprüfung nicht einfach für alles abschalten.
- Besser: beim ersten Kontakt den Fingerabdruck des Zertifikats merken und danach nur noch dieses Zertifikat akzeptieren.
- Oder Daniel im Fenster fragen.

### 3.3 Antwort auf `POST /state`: zwei Felder ergänzen
In `protocol.py`, `world()`:

| Feld | Inhalt | Wofür Motion Watch es braucht |
|---|---|---|
| `"pid"` | `os.getpid()` | Zeigt unter «Rechenleistung», wie viel CPU der Simulator braucht, wenn er auf demselben Gerät läuft. |
| `"sound_db"` | Lautstärke der simulierten Welt in dB, etwa 30 = still, 45 = Gespräch, 60–75 = Auto, bellender Hund, Bär, Gewitter | Lärm-Alarm und Klatschschalter-Test. Ohne das Feld hört Motion Watch in der Simulation nichts. |

Unbekannte Felder ignoriert Motion Watch. Weitere Felder schaden also nicht.

### 3.4 Was Motion Watch dir ausserdem schickt (kannst du nutzen)
In jedem `POST /state` stehen:
- `det` (was Motion Watch gerade erkennt: Personen, Tiere, Lärm). Das ist gut für deine Testtafel, du brauchst dafür nicht `/api/state` abzufragen.
- `cpu` (CPU-Anteile)
- `drive` (`l`/`r` von -1 bis 1, die Raupen eines Fahrzeugs)

Wenn du ein Fahrzeug simulierst, antworte mit `"mover": true`. Dann zeigt Motion Watch den zweiten Steuerknüppel.
Sonst lass das Feld weg.

### 3.5 Kleine Verbesserungen für die Einstellungen (freiwillig)
- `"expert": true` bei einem Regler: Er erscheint nur, wenn man in Motion Watch «Experte» wählt.
  Die Ansicht «Einfach» bleibt dann übersichtlich. Kandidaten: Lufttemperatur, Bären, Rehe, Heisser Stein, Bildqualität.
- `"sub": "Tiere"` bei einem Regler: Er kommt in eine Untergruppe innerhalb seiner Gruppe.
  Praktisch für die vielen Schieber unter «Besuch».
- Die Namen der Kamera-Plätze und Szenarien sind englisch («Campsite (start)», «Lake & beach»).
  Daniel benutzt Motion Watch auf Deutsch. Bitte deutsche Namen, oder die Sprache aus dem Feld `lang` in `POST /control` nehmen
  (Motion Watch schickt `"lang": "de"` mit).

### 3.6 Neue Version herausgeben
1. `VERSION` erhöhen (zum Beispiel PY-1.1).
2. `python make_package.py`
3. `MotionWatchSimulator.zip` **und** `MotionWatchSimulator.json` committen und pushen.
4. Daniel sagen: «Neues Paket PY-1.1 ist auf GitHub, Motion Watch muss Version, Grösse und Prüfsumme übernehmen.»
   Motion Watch bietet sonst weiter PY-1.0 an, weil die Prüfsumme fest im (unterschriebenen) Programm steht.
   Das ist Absicht und eine Sicherheitsmassnahme.

### 3.7 Computername mitschicken (neu, Motion Watch 2.95.1)
Motion Watch zeigt in der Liste «Simulatoren im Netz» neben jedem Simulator den Namen des Computers.
Bitte schick ihn mit:
- in der UDP-Meldung: `"host": socket.gethostname()`
- in `GET /info`: ebenfalls `"host"`

Ohne das Feld fragt Motion Watch den Router nach dem Namen. Das klappt nicht in jedem Netz.
Der 3D-Simulator macht das ab 3D-3.17.

### 3.8 Schwenken bis ±180° (neu, Motion Watch 2.95.4)
Der endgültige Schwenk-Servo dreht ±180°. Motion Watch hat dafür die Einstellung «Schwenk-Servo: Drehbereich» (180 / 270 / 360°).
`pan_deg` in `POST /state` kann jetzt bis ±180 gehen, `pan_limit` ist die eingestellte Grenze (höchstens die Hälfte des Drehbereichs).
In `engine.py` (`protocol_state`) wird `pan_deg` heute auf `SIM["pan_travel"] / 2` begrenzt.
Bitte so ändern, dass bis ±180° gedreht wird (zum Beispiel `pan_travel` 360, oder die Grenze aus `pan_limit` nehmen).
Achtung: Ein Servo dreht nicht «über die Rückseite». Von +179° nach −179° fährt er den langen Weg zurück.

## 4. So testest du mit Motion Watch

1. Simulator starten: `python3 motion_sim.py --stream` (oder mit Fenster «An Motion Watch senden» einschalten).
2. Motion Watch, Reiter «Simulator»: Unter «Simulatoren im Netz» erscheint «Python-Weltsimulator 1.0 · PY-1.0».
   «Verwenden» drücken, dann «Simulation einschalten».
3. Unter «Simulator-Steuerung» jeden Regler bewegen und im Simulator nachsehen, ob er ankommt.
   Mit dem Knopf ↻ neu laden: Der Wert muss stehen bleiben.
4. Laufen beide Simulatoren gleichzeitig, braucht jeder einen eigenen Port und Namen.
   Der 3D-Simulator nimmt 8765, dieser 8767.

## 5. Wünsche an Motion Watch (hier eintragen)

- **Dateiname des Pakets pro Version** (z. B. `MotionWatchSimulator_PY-1.1.zip`, steht im Feld `file` von
  `MotionWatchSimulator.json`). Heute heisst jede Version `MotionWatchSimulator.zip`. Sobald eine neue Version auf GitHub
  liegt, passt die Datei nicht mehr zur fest eingetragenen Prüfsumme. Ein Pi, der PY-1.0 noch nicht geholt hat, lehnt den
  Download dann ab, bis Motion Watch die neuen Werte hat. Das ist sicher, aber der Knopf geht so lange nicht.
  Der Python-Simulator kann den Namen pro Version gerne liefern, sobald Motion Watch das will.

  **Antwort Motion Watch (2.95.1):** Ja, so machen wir es. Motion Watch 2.95.1 holt
  `simulator_python/MotionWatchSimulator_PY-1.1.zip` (diese Datei habe ich als Kopie deines Pakets angelegt, gleiche Prüfsumme).
  Bitte ab PY-1.2 so:
  - `make_package.py` schreibt `MotionWatchSimulator_<VERSION>.zip` und trägt diesen Namen in `file` der `.json` ein.
  - Die **älteren** versionierten Zips nicht löschen (sie sind klein). Pis mit einer älteren Motion Watch holen noch diese.
  - `MotionWatchSimulator.zip` (ohne Version) darfst du weiter als «neueste» behalten oder weglassen. Motion Watch braucht ihn nicht mehr.

## 6. Erledigt in PY-1.1 (27.10.2026, Python-Simulator-Claude)

- 3.1 `--no-panel` startet ohne tkinter: `simulator/choices.py` (laden / anwenden), `ui/start.py` wird nur noch für das
  Startfenster geladen. Getestet mit gesperrtem tkinter.
- 3.2 Webseite von Motion Watch aus `mw_scheme` / `mw_port` von `POST /state` (rohes JSON, vor `MWState`).
  https: Fingerabdruck des Zertifikats wird beim ersten Kontakt gemerkt (`data/mw_certs.json`, nicht im Projekt).
  Ein anderes Zertifikat wird abgelehnt, bis man es im Reiter «🔗 Motion Watch» annimmt.
- 3.3 Antwort hat `pid` und `sound_db`. Ruhe etwa 26–30 dB, Wind, Regen, Donner und jeder Besucher je nach Abstand
  (Hund bellt, Bär brummt, Auto fährt vorbei).
- 3.4 `det` aus `POST /state` wird für die Testtafel benutzt (Personen, frischer als `/api/state`). Kein Fahrzeug, also kein `mover`.
- 3.5 `expert` bei Lufttemperatur, Bären, Rehen, Heissem Stein, Lagerfeuer, Bildqualität.
  `sub` unter «Besuch»: «Personen & Autos», «Tiere», «Jetzt schicken».
  Deutsche Namen der Szenarien und Kamera-Plätze, Sprache aus `Accept-Language` (so schickt es Motion Watch 2.95) oder `lang`.
- 3.6 Neues Paket **PY-1.1** liegt auf GitHub. Motion Watch muss Version, Grösse und Prüfsumme aus
  `simulator_python/MotionWatchSimulator.json` übernehmen.
