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

## 4. So testest du mit Motion Watch

1. Simulator starten: `python3 motion_sim.py --stream` (oder mit Fenster «An Motion Watch senden» einschalten).
2. Motion Watch, Reiter «Simulator»: Unter «Simulatoren im Netz» erscheint «Python-Weltsimulator 1.0 · PY-1.0».
   «Verwenden» drücken, dann «Simulation einschalten».
3. Unter «Simulator-Steuerung» jeden Regler bewegen und im Simulator nachsehen, ob er ankommt.
   Mit dem Knopf ↻ neu laden: Der Wert muss stehen bleiben.
4. Laufen beide Simulatoren gleichzeitig, braucht jeder einen eigenen Port und Namen.
   Der 3D-Simulator nimmt 8765, dieser 8767.

## 5. Wünsche an Motion Watch (hier eintragen)

- (noch nichts)
