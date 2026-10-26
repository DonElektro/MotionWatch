# Einen eigenen Simulator an Motion Watch anbinden

Stand: Motion Watch 2.93.0 · Simulator-Protokoll 1 · 26.10.2026

Diese Datei ist für alle, die einen **weiteren Simulator** für Motion Watch bauen, zum Beispiel einen zweiten neben dem
3D-Simulator. Wer mit Claude arbeitet, gibt ihm diese Datei als Erstes.

---

## 1. Das Wichtigste in Kürze

- Motion Watch läuft auf einem Raspberry Pi 5 und überwacht mit Kameras auf einem Schwenkkopf.
- Ein **Simulator** spielt diese Hardware nach: Er liefert Kamerabilder, ein Wärmebild und Sensor-Meldungen. Motion Watch
  schickt ihm dafür laufend, wohin die Servos zeigen und welche Lichter brennen.
- Verbindung: **einfaches HTTP**, Standard-Port **8765**. Programmiersprache, Grafik und Engine sind frei (Python, Godot,
  Unity …). Motion Watch kennt nur die Adressen unten.
- **In Motion Watch muss für einen neuen Simulator nichts geändert werden.** Er wird im Netz gefunden, seine Regler
  erscheinen von selbst auf der Webseite (Reiter «Simulator»).
- Eine fertige Vorlage in Python: `simulator/motionwatch_sim_interface.py`. Starten mit
  `python3 motionwatch_sim_interface.py --night`, dann siehst du einen kleinen, funktionierenden Demo-Simulator.
- Alle Einzelheiten: `simulator/Simulator_Schnittstelle.md`. Ein grosses Beispiel in Godot: `simulator3d/`.

---

## 2. Was dein Simulator können muss

### Pflicht

| Adresse | Was | Format |
|---|---|---|
| `GET /info` | Was der Simulator anbietet | JSON, siehe unten |
| `POST /state` | Motion Watch schickt Servos, Licht usw. (etwa 10× pro Sekunde) | JSON rein, JSON-Antwort raus |
| `GET /cam/0/video.mjpg` | Kamera 0 (auf dem Schwenkkopf) als Video | MJPEG: `multipart/x-mixed-replace; boundary=...` |
| `GET /cam/0/snapshot.jpg` | Ein Einzelbild von Kamera 0 | JPEG |

Mit `?fps=6` fragt Motion Watch nach weniger Bildern pro Sekunde. Bitte beachten, das spart Rechenleistung.

### Empfohlen

| Adresse | Was |
|---|---|
| `GET /cam/1/video.mjpg`, `/cam/1/snapshot.jpg` | Kamera 1 (fest montiert) |
| `GET /thermal.bin` | Wärmebild: `float32` in °C, Zeile für Zeile, Kopfzeilen `X-Width`, `X-Height`, `X-Unit: C` (Motion Watch rechnet mit 80 × 62) |
| `GET /events?since=<nr>` | Sensor-Meldungen: `{"v": 1, "events": [{"id": 7, "t": 1793050000.5, "sensor": "Wohnwagen-Tür", "kind": "door", "active": true}]}` |
| `GET /control`, `POST /control` | Fernsteuerung von der Webseite (Szenarien, Regler, Schalter, Knöpfe), siehe Abschnitt 4 |
| UDP-Meldung | «Hier ist ein Simulator», damit Motion Watch ihn selbst findet, siehe Abschnitt 3 |

### `GET /info` – Beispiel

```json
{"v": 1, "name": "Simulator von Max 1.0",
 "cameras": [{"id": 0, "name": "Kopf", "w": 960, "h": 540, "fps": 15, "fov_h": 66, "fov_v": 41, "on_head": true, "noir": true},
             {"id": 1, "name": "Fest", "w": 640, "h": 360, "fps": 10, "fov_h": 70, "fov_v": 40, "on_head": false, "noir": false}],
 "thermal": {"w": 80, "h": 62, "fps": 8, "fov_h": 45, "fov_v": 35, "unit": "C", "on_head": true},
 "sensors": [{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"}]}
```

### `POST /state` – was Motion Watch schickt (Auszug)

```json
{"v": 1, "t": 1793050000.2, "device": "Motion Watch",
 "servo": {"pan": 50, "tilt": 50, "pan_deg": 0.0, "tilt_deg": 0.0, "pan_limit": 90, "tilt_limit": 60, "moving": false},
 "lights": {"white": false, "ir": true},
 "relays": [{"name": "Relay 1", "on": false}],
 "sound": "", "armed": true, "picture_mode": "night_grey"}
```

- **Schwenken/Neigen:** `pan`/`tilt` in Prozent (0–100, 50 = Mitte, pan 100 = rechts, tilt 100 = oben) und zusätzlich in
  Grad ab der Mitte (`pan_deg`, `tilt_deg`). Am einfachsten die Grad-Werte nehmen.
- `sound`: was gerade aus dem Lautsprecher kommt (`"siren"`, `"tts"` …). Tiere sollen davor flüchten, das testet die Abschreckung.
- **Unbekannte Felder ignorieren.** Es kommen mit der Zeit neue dazu.

### Antwort auf `POST /state`

```json
{"v": 1, "ok": true, "sim_time": 1793050000.2, "dark": true, "ambient_c": 9.5, "pressure_hpa": 1012, "wind_kmh": 8,
 "humidity": 80, "weather": "clear", "last_event": 7}
```

`last_event` = Nummer der neuesten Sensor-Meldung. Ist sie höher als beim letzten Mal, holt Motion Watch `/events`.

### Regeln für die Bilder

- Kamera 0 dreht sich mit dem Schwenkkopf, Kamera 1 nicht. Das Wärmebild sitzt neben Kamera 0.
- Infrarot-Licht (`lights.ir`) sieht nur eine NoIR-Kamera. Nachts wird das Bild damit grau-hell.
- Die Servos sollen **nicht springen**, sondern mit begrenzter Geschwindigkeit nachfahren, wie echte (etwa 60–120 °/s).
- Bitte kein Text im Bild (ausser bewusst als Test). Motion Watch zeichnet seine eigenen Markierungen.

---

## 3. Gefunden werden

- Alle **2 Sekunden** eine UDP-Nachricht an **Port 8764**, an `255.255.255.255` (und `127.0.0.1`):
  `{"mwsim": 1, "name": "Simulator von Max 1.0", "port": 8765, "version": "M-1.0"}`
- Motion Watch zeigt ihn dann im Reiter **«Simulator» → «Simulatoren im Netz»** an. Mit «Verwenden» wird er genommen.
- **Wichtig:** Ein **eindeutiger Name** (nicht «Motion Watch 3D-Simulator»), damit man die Simulatoren unterscheiden kann.
- **Laufen zwei Simulatoren auf demselben PC**, braucht jeder einen eigenen Port. Der 3D-Simulator hat 8765, also deiner zum
  Beispiel **8767**. Die Windows-Firewall muss den Port erlauben («Private Netzwerke»).
- **Erst senden, wenn der Benutzer es will:** Der 3D-Simulator startet still und meldet sich erst, wenn man im Fenster den
  Schalter «An Motion Watch senden» einschaltet. Bitte genauso machen (Start-Option `--stream` für «sofort senden»).

---

## 4. Fernsteuerung von der Webseite (CONTROL-Protokoll)

Dein Simulator **beschreibt seine Bedienelemente selbst**. Motion Watch zeichnet sie im Reiter «Simulator» unter
«Simulator-Steuerung», ohne sie zu kennen.

`GET /control` antwortet zum Beispiel so:

```json
{"ok": true, "v": 1, "name": "Simulator von Max 1.0",
 "scenarios": [{"id": "stadt", "name": "Stadt bei Nacht", "kind": "world", "deletable": false}],
 "scenario": "stadt",
 "status": "22:10 · Nacht · 3 Personen unterwegs",
 "controls": [
   {"type": "slider", "id": "hour", "label": "Uhrzeit", "group": "Szene", "min": 0, "max": 24, "step": 0.25, "unit": "h", "value": 22.2},
   {"type": "select", "id": "weather", "label": "Wetter", "group": "Wetter", "options": [["clear", "klar"], ["rain", "Regen"]], "value": "clear"},
   {"type": "toggle", "id": "auto", "label": "Besuch von selbst", "group": "Besuch", "value": true},
   {"type": "button", "id": "spawn_person", "label": "Person", "group": "Besuch"}],
 "upload": null}
```

`POST /control` mit `{"action": "get" | "scenario" | "delete" | "set" | "press", "id": "...", "value": ...}`. Die Antwort
ist immer wieder dasselbe wie `GET /control`. Bei einem Fehler: `{"ok": false, "error": "warum"}`.

---

## 5. So testest du

1. Simulator starten (Senden einschalten).
2. Im Browser: `http://<PC>:<Port>/info` und `http://<PC>:<Port>/cam/0/snapshot.jpg` müssen etwas liefern.
3. Mit curl:
   ```
   curl -X POST -H "Content-Type: application/json" -d '{"servo":{"pan_deg":30,"tilt_deg":0},"lights":{"white":true}}' http://127.0.0.1:8767/state
   ```
   Danach muss Kamera 0 nach rechts schauen und das weisse Licht brennen.
4. In Motion Watch: Reiter **«Simulator»** → dein Simulator erscheint unter «Simulatoren im Netz» → **«Verwenden»** →
   **«Simulation einschalten»**. Oben erscheint das Live-Bild, darunter deine Regler.
5. Prüfen: Joystick bewegt deine Kamera, Licht-Knöpfe wirken, eine Person in deinem Bild löst die Erkennung aus.

Wenn nur «CONNECTING…» erscheint, liefert `/cam/0/video.mjpg` keine Bilder. Häufige Ursache: Das Fenster ist minimiert und
die Engine zeichnet nicht mehr.

---

## 6. Zusammenarbeit im GitHub-Projekt (bitte genau einhalten)

Im Projekt `DonElektro/MotionWatch` arbeiten schon **zwei Claude-Chats** (Motion Watch und 3D-Simulator). Am 26.10. sind
dabei einmal Änderungen verloren gegangen. Darum:

- **Am besten ein eigenes Repository** für deinen Simulator, zum Beispiel `DonElektro/MotionWatch-Sim2`. Dann kann
  niemand aus Versehen deine Dateien überschreiben, und du keine von Motion Watch.
- Falls doch im selben Projekt: nur in **deinem eigenen Ordner** arbeiten, zum Beispiel `simulator_max/`.
- **Nie ändern:** `webcam_bewegung_*.py`, `versions.json`, `simulator3d/`, `simulator/`. Wünsche an Motion Watch bitte
  über Daniel (Papa) an den Motion-Watch-Chat.
- **Vor jedem Hochladen** `git pull`. **Nach** `git push` prüfen, dass es geklappt hat (`git status -sb` darf kein «ahead»
  zeigen). **Nie** `git push --force`.
- **Keine Passwörter, Schlüssel oder privaten Daten** ins Repository. Der Signier-Schlüssel von Motion Watch gehört
  nur Daniel.
- **Eigene Versionsnummern** mit Vorsilbe, damit sie sich nicht mit den anderen Simulatoren verwechseln lassen, zum
  Beispiel `M-1.0`, `M-1.1` …

### Wenn Motion Watch deinen Simulator später zum Herunterladen anbieten soll

Das kann Motion Watch, wie beim 3D-Simulator (`/sim/simulator3d.zip`). Dafür braucht es von dir:
- ein fertiges ZIP an einer festen Stelle, zum Beispiel `simulator_max/MeinSimulator.zip`,
- eine Datei daneben mit Version, Grösse und Prüfsumme:
  `{"version": "M-1.0", "file": "simulator_max/MeinSimulator.zip", "size": 12345678, "sha256": "…"}`.

Den Knopf in Motion Watch baut dann der Motion-Watch-Chat ein.

---

## 7. Was Motion Watch für dich schon erledigt

- Kamerabilder ansehen, Bewegungs- und KI-Erkennung, Alarme, Aufnahmen: alles wie mit echter Hardware.
- Simulation ein/aus mit einem Knopf; dabei schaltet Motion Watch zwischen echter Hardware und Simulator um.
- Live-Bild, Statistik (Antwortzeit, Bilder pro Sekunde, Fehler) und deine Regler im Reiter «Simulator».
- In der Simulation werden keine Aufnahmen und keine Zeitraffer gespeichert, damit nichts mit echten Aufnahmen vermischt wird.

Viel Spass beim Bauen!
