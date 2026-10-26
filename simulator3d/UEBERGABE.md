# Übergabe: Motion Watch 3D-Simulator

Stand: 26.10.2026 · Simulator-Version **3D-1.6** · passende Motion-Watch-Version **2.90.1**

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

Seit 3D-1.6 startet der Simulator mit dem **Kompatibilitäts-Renderer (OpenGL)**: Auf Daniels PC schloss sich die .exe mit
Forward+ (Vulkan) sofort wieder, mit OpenGL lief sie. Forward+ gibt es nur noch über «Start mit Vulkan-Grafik (schoener).bat».

Seit 3D-1.5 gibt es **sechs Szenen** (Camping-Platz, Wald, Parkplatz, Garten/Haus, Lustiger Platz, Wildbeobachtung) und ein
**unblutiges Gewehr** für die Wildbeobachtung (Taste G). Beides ist eine schnelle erste Fassung.

Seit 3D-1.4 sendet der Simulator nach dem Start **nichts**. Erst der Schalter «An Motion Watch senden» oben rechts (oder die Option `--stream`) öffnet den Port und schickt die Meldungen ins Netz.

## Wo liegt was (Repository DonElektro/MotionWatch)

- `simulator3d/`: Godot-Projekt
  - `project.godot`, `main.tscn`, `export_presets.cfg`
  - `scripts/main.gd`: Welt (Boden, Himmel, Hügel), Kameras, Wärmebild, Steuerung, PC-Fenster, Gewehr
  - `scripts/scenes.gd`: die sechs Szenen (`LIST`), welche Besucher von selbst kommen (`AUTO`), Bausteine (Baum, Hütte, Wohnwagen, Laterne …)
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

## Szenen und Gewehr (ab 3D-1.5)

- Eine Szene baut alles unter einem eigenen Knoten; Umschalten löscht ihn und baut die nächste (`set_scene`). Die Szenen stehen
  als CONTROL-Szenarien in `/control` – die Motion-Watch-Webseite zeigt sie ohne Änderung an Motion Watch zur Auswahl.
- Jede Szene muss liefern: `door_node`, `door_light`, `window_mat` (Türsensor) und `obj["door"]`, `obj["pir"]`, `obj["bike"]`
  (Dieb, PIR). Die Sensornamen bleiben in allen Szenen gleich («Wohnwagen-Tür», «PIR Zelt», «Velo»), weil Motion Watch sie so kennt.
- Bewegte Dinge (Karussell, Enten, Vogelscheuche, Zwerg, Feuer) sind Funktionen in `anims`, Nachtlichter in `lamps` / `lamp_mats`.
- Besondere Besucher: `visit("car_park")` (Auto parkiert), `visit("bench")` (setzt sich auf die Bank), `visit("feed_deer")` usw.
  (Tier frisst an der Futterstelle). Ein Routenpunkt `[Punkt, Sekunden warten, kauern, schaut zu Punkt]`.
- Gewehr: Strahl von der Ansichtskamera (Maus) oder aus Kamera 0 (Knopf «Schuss aus der Kopfkamera», also mit dem Joystick von
  Motion Watch zielbar). Treffer-Kugeln pro Besucher in `actor.hit_spheres()`. Menschen und Autos blocken den Schuss
  («Nicht auf Menschen!»). Ein Tier hüpft, dreht sich, sieht Sterne und flieht (`actor.hit()` / `_dizzy()`). Töne werden aus
  Zahlen erzeugt (`_make_sound`).

## Wichtige technische Kniffe

- Jedes sichtbare Teil hat einen Wärmebild-Zwilling auf Ebene 2 (`thermal.gdshader`, Temperatur kodiert als (T+40)/120).
- Der Himmel im Wärmebild ist eine grosse Kuppel. Die Umrechnungstabelle wird beim Start kalibriert (Kompatibilitäts-Renderer: linear; Forward+: sRGB).
- SubViewports werden mit UPDATE_ONCE nur bei Bedarf gerendert. Das IR-Licht ist nur während der Aufnahme von Kamera 0 an.
- GDScript: Keine Methoden wie `c.get`/`c.set` an Dictionaries aufrufen, sondern `c["get"]`. Gepackte Arrays in Dictionaries zuerst kopieren, ändern und wieder zuweisen.
- `phone.gd`: `/json/list` über rohes StreamPeerTCP holen (HTTPRequest wurde nicht fertig). WebSocket mit 8-MB-Puffer. Bilder per `Page.captureScreenshot` (Screencast hatte die falsche Grösse).

## Bauen

- Godot 4.3 stable plus Export-Templates 4.3.
- Windows-Version: `godot --headless --path . --export-release "Windows Desktop" /tmp/…/MotionWatch3D.exe`
  (Zielordner **ausserhalb** des Repositorys wählen; `../mwsim3d_build` liegt sonst im Repository).
- ZIP: das alte ZIP entpacken, `MotionWatch3D.exe` und `Lies mich.txt` ersetzen (die .bat-Dateien bleiben), mit `zip -9 -r` packen.
- Linux-Version zum Testen: Preset «Linux». Starten mit `--rendering-driver opengl3` auf einem virtuellen Bildschirm (Xvfb), damit es auch ohne echte Grafikkarte läuft.
- Nach jedem neuen Bau: die Datei `simulator3d/MotionWatch3D_Simulator.zip` im Repository ersetzen, dann in Motion Watch (`work.py`) in `SIM3D` die neue `version`, `size` und `sha256` eintragen und eine neue Motion-Watch-Version veröffentlichen. Sonst liefert der Pi-Download die alte Fassung.

## Etappen

Gebaut in 3D-1.5 (schnelle erste Fassung, vereinbart war «zuerst schnell, dann Ausbau»):

- **Weitere Szenen**: Wald, Parkplatz, Garten/Haus, umschaltbar im Fenster und auf der Webseite.
- **Lustige Szene**: zwei Bänke, Besucher setzen sich und schauen zu: Karussell (nachts Disco), Entenfamilie um den Teich,
  winkende Vogelscheuche, Gartenzwerg hinter dem Stein, Lichterkette, Schild «Bitte lächeln!».
- **Wildbeobachtung** mit Hochsitz, Futterstelle, Salzlecke und einem **unblutigen** Gewehr: nur Tiere, Menschen nie.

Mögliche Ausbauten: Gelände mit Hügeln in der Nähe, schönere Tiere und Menschen (Modelle statt Grundformen), eigene Sensoren pro
Szene (bräuchte eine Anpassung in Motion Watch), Wasser im Wald, mehr Witz im Lustigen Platz, Punkteliste für die Wildbeobachtung.

## Was in dieser Umgebung nicht getestet werden konnte

- Die Windows-.exe auf echter Hardware (hier nur Linux mit llvmpipe über Xvfb).
- Die Erkennung des Edge-Pfads unter Windows.
- Nebel im Forward+-Renderer (Forward+ ist ab 3D-1.6 nur noch über die Vulkan-.bat erreichbar).
- Die echte Netzsuche zwischen PC und Pi.
- Ton (Schuss «Plopp», Treffer «Boing») – hier ohne Lautsprecher.
- Die Bildrate der neuen Szenen auf dem alten i5 (Wald hat rund 300 Bäume).
- Das Zielen mit der echten Maus (hier nur mit dem Knopf «Schuss aus der Kopfkamera» getestet).

## Testwerkzeuge in dieser Umgebung (nur als Hinweis, liegen nicht im Repo)

- Godot 4.3 von GitHub (Releases 4.3-stable, Linux-Programm + Export-Templates nach `~/.local/share/godot/export_templates/4.3.stable`).
- Projekt direkt im geklonten Repository (`simulator3d/`); `.godot/` ist in .gitignore.
- Start auf virtuellem Bildschirm und HTTP-Abfragen über kleine Hilfsskripte.