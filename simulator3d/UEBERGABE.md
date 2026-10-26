# Übergabe: Motion Watch 3D-Simulator

Stand: 26.10.2026 · Simulator-Version **3D-1.4** · passende Motion-Watch-Version **2.89.0**

Diese Datei ist der Startpunkt für einen neuen Chat, der den 3D-Simulator weiter ausbaut.

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

Seit 3D-1.4 sendet der Simulator nach dem Start **nichts**. Erst der Schalter «An Motion Watch senden» oben rechts (oder die Option `--stream`) öffnet den Port und schickt die Meldungen ins Netz.

## Wo liegt was (Repository DonElektro/MotionWatch)

- `simulator3d/`: Godot-Projekt
  - `project.godot`, `main.tscn`, `export_presets.cfg`
  - `scripts/main.gd`: Welt, Kameras, Wärmebild, Steuerung, PC-Fenster
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
- `GET/POST /control`: CONTROL-Protokoll 1. Das Steuerfeld der Motion-Watch-Webseite wird daraus automatisch gebaut. Neue Regler meldet man in `main.gd` mit `add_control(...)` an; sie erscheinen dann im PC-Fenster und auf der Webseite.
- UDP-Meldung alle 2 s an Port 8764: `{"mwsim":1,"name","port","version"}`.

## Wichtige technische Kniffe

- Jedes sichtbare Teil hat einen Wärmebild-Zwilling auf Ebene 2 (`thermal.gdshader`, Temperatur kodiert als (T+40)/120).
- Der Himmel im Wärmebild ist eine grosse Kuppel. Die Umrechnungstabelle wird beim Start kalibriert (Kompatibilitäts-Renderer: linear; Forward+: sRGB).
- SubViewports werden mit UPDATE_ONCE nur bei Bedarf gerendert. Das IR-Licht ist nur während der Aufnahme von Kamera 0 an.
- GDScript: Keine Methoden wie `c.get`/`c.set` an Dictionaries aufrufen, sondern `c["get"]`. Gepackte Arrays in Dictionaries zuerst kopieren, ändern und wieder zuweisen.
- `phone.gd`: `/json/list` über rohes StreamPeerTCP holen (HTTPRequest wurde nicht fertig). WebSocket mit 8-MB-Puffer. Bilder per `Page.captureScreenshot` (Screencast hatte die falsche Grösse).

## Bauen

- Godot 4.3 stable plus Export-Templates 4.3.
- Windows-Version: `godot --headless --path . --export-release "Windows Desktop" ../mwsim3d_build/MotionWatch3D.exe`
- Linux-Version zum Testen: Preset «Linux». Starten mit `--rendering-driver opengl3` auf einem virtuellen Bildschirm (Xvfb), damit es auch ohne echte Grafikkarte läuft.
- Nach jedem neuen Bau: die Datei `simulator3d/MotionWatch3D_Simulator.zip` im Repository ersetzen, dann in Motion Watch (`work.py`) in `SIM3D` die neue `version`, `size` und `sha256` eintragen und eine neue Motion-Watch-Version veröffentlichen. Sonst liefert der Pi-Download die alte Fassung.

## Geplante nächste Etappen (noch nicht gebaut)

Daniel möchte den Simulator weiter ausbauen. Besprochen sind:

- **Weitere Szenen** neben dem Camping-Platz: Wald, Parkplatz, Garten/Haus. Umschaltbar.
- **Eine lustige Szene**, in der der Besucher zum Verweilen eingeladen ist und witzige Dinge beobachten kann.
- **Wildbeobachtung** mit einem Gewehr, mit dem man ein Tier «treffen» kann – ausdrücklich **unblutig**, nur die Tiere, keine Gewalt gegen Menschen.

Als Reihenfolge wurde «zuerst eine schnelle Version» vereinbart, dann Ausbau.

## Was in dieser Umgebung nicht getestet werden konnte

- Die Windows-.exe auf echter Hardware (hier nur Linux mit llvmpipe über Xvfb).
- Die Erkennung des Edge-Pfads unter Windows.
- Nebel im Forward+-Renderer.
- Die echte Netzsuche zwischen PC und Pi.

## Testwerkzeuge in dieser Umgebung (nur als Hinweis, liegen nicht im Repo)

- Godot 4.3 unter `/tmp/.../godot/`, Projekt unter `/home/claude/mwsim3d`.
- Start auf virtuellem Bildschirm und HTTP-Abfragen über kleine Hilfsskripte.