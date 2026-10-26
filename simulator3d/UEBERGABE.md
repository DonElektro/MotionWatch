# Übergabe: Motion Watch 3D-Simulator

Stand: 26.10.2026 · Simulator-Version **3D-1.12** · passende Motion-Watch-Version **2.90.7**

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

Seit 3D-1.9 gibt es **«Motion Watch auf diesem PC»** (`scripts/mwpc.gd`): Damit das Handy ohne Pi etwas zeigt, läuft das echte
Motion Watch unsichtbar neben dem Simulator. Beim ersten Mal: Python 3.12.7 für Windows aus python-build-standalone (GitHub,
`PY_URL`/`PY_SHA`), ausgepackt mit `tar.exe` von Windows; `pip install` von `PKGS` (PyPI); dann jeweils die neuste Datei aus
`versions.json` (geprüft mit deren SHA-256, **nicht** mit der Signatur). Start: `python.exe <datei> --headless --config <…>/config
--port 5000 --bind 127.0.0.1`; die Einstellungen `sim_on`, `sim_url`, `sim_auto=False` schreibt Python selbst (Godots JSON
macht aus ganzen Zahlen Kommazahlen). Alles unter `user://motionwatch_pc`. Unter Linux nimmt es das System-Python
(`--mw-python`), `--mw-base http://…/` ersetzt GitHub (Test: `python3 -m http.server` im Repository).
Grosse Downloads unter Windows mit **curl.exe** (Teil von Windows 10/11: Windows-Zertifikate und -Proxy, folgt der Weiterleitung von
github.com zu release-assets.githubusercontent.com); Godots HTTPRequest ist nur Ersatz – in 3D-1.9 scheiterte damit der
Python-Download bei Daniel («Fehler 0» = keine Verbindung). Fehlertexte nennen jetzt den Grund (`RESULTS`).
`--mw-test-python` lädt und entpackt das Windows-Python auch unter Linux (mit curl über den Proxy getestet: Download,
SHA-256 und tar gehen). Die Webseiten-Prüfung fragt mit HEAD (die Startseite ist ~400 KB), Wartezeit bis 5 Minuten.
Nur `sim_on` reicht nicht: Motion Watch suchte dann weiter eine USB-Kamera («NO CAMERA FOUND», schwarzes Handy-Bild). `_settings()`
setzt darum wie der Schalter «Simulation» auch `source = sim:0`, `thermal_source = sim:thermal` und `sim:1` in `extra_cams`.
Das Handy startet ab 3D-1.11 mit der normalen Startseite (Knopf «Vollbild» = nur Live-Bild).
Unter Linux getestet bis «verbunden mit Motion Watch» und Webseite auf 127.0.0.1:5000; **unter Windows nicht getestet**
(Python-Download, tar, pip, Motion Watch selbst unter Windows).

**Daniel testet in einer VMware-Maschine** (Log: «VMware, Inc. – SVGA3D», Mesa 24.1). Deren OpenGL lehnt die Godot-Shader ab
(«declarations for uniform `world_transform` have mismatching invariant qualifiers»), sichtbar ist nur der Himmel; Vulkan geht
dort gar nicht. Ab 3D-1.8 erkennt `main._vm_needs_angle()` die virtuelle Grafik am Namen und startet einmal neu mit
`--rendering-driver opengl3_angle` (Kennzeichen `--angle-tried`, abschalten mit `--no-angle`). Godot 4.3 gibt Grafik-Optionen
beim Neustart nicht weiter (`OS.get_cmdline_args()` ist dann leer) und kennt `get_current_rendering_driver_name()` noch nicht.
Unter ANGLE **nicht getestet** – falls es auch so nicht geht: in VMware die 3D-Beschleunigung prüfen, sonst echte Hardware.

Seit 3D-1.7 **aktualisiert sich der Simulator selbst** (`scripts/update.gd`): Vor dem Bau der Welt lädt er
`simulator3d/version.json` von GitHub (`{"version", "file", "size", "sha256", "notes"}`). Ist die Version neuer, zeigt er
«Jetzt aktualisieren» / «Ohne Update starten». Beim Aktualisieren: ZIP nach `user://update.zip`, Grösse + SHA-256 prüfen,
Dateien neben die .exe legen, die laufende .exe in `.old` umbenennen, neue hinlegen, mit denselben Optionen plus `--updated`
neu starten (die `.old` wird beim nächsten Start gelöscht). Ohne Antwort nach 6 s startet er normal. `--no-update` schaltet es ab,
`--update-url http://…/` nimmt eine andere Quelle (zum Testen mit einem lokalen `python3 -m http.server`).
Der Programmpfad wird **vor** dem Umbenennen gemerkt (unter Linux zeigt er danach auf die `.old`).
Ab 3D-1.12 gibt es den Knopf **«Nach Updates suchen»** (`main.check_updates()`, `Updater.manual = true`: meldet auch
«schon die neuste Version» / «GitHub antwortet nicht»). Das Update-ZIP lädt unter Windows **curl.exe**; Godots HTTPRequest
nur als Ersatz, mit `download_chunk_size` 1 MB (mit 64 KB pro Bild dauerte es bei laufender Simulation viele Minuten).
Schutz nur über die Prüfsumme aus derselben Quelle (GitHub), **nicht signiert** wie Motion Watch.

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
- **Danach `simulator3d/version.json` mit neuer Version, Grösse und sha256 des ZIP schreiben** – sonst erfahren die Simulatoren
  nichts vom Update. (`VERSION` in main.gd, version.json und `SIM3D` in Motion Watch müssen zusammenpassen.)
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

## Fahrplan: Online-Dienst für Hersteller (Idee von Daniel, 26.10.2026)

Ziel: Später online gehen, damit Hersteller von Überwachungssystemen ihre Systeme an dieser Simulation testen können.
Noch nichts davon ist gebaut. Reihenfolge nach Wichtigkeit:

1. **Standard-Schnittstellen** statt nur Motion-Watch-Protokoll: **RTSP** für die Kamerabilder, **ONVIF** (Erkennung,
   Profil S, PTZ für den Schwenkkopf), **MQTT** / Webhooks für die Sensoren. Erst dann lässt sich ein fremdes System einfach
   «an eine Kamera» anschliessen. Das bestehende Protokoll bleibt für Motion Watch.
2. **Realistischere Bilder**: lizenzierte 3D-Modelle von Menschen und Tieren mit Animation statt Grundformen (KI-Erkenner
   erkennen die heutigen Figuren kaum), Kamerafehler (Rauschen, Unschärfe, Kompression, Infrarot-Look, Blendung).
3. **Wiederholbare Tests mit Ground Truth**: Der Simulator schreibt auf, wer wann wo im Bild war; Szenarien mit festem Zufall
   (Seed) und Zeitplan, exakt wiederholbar; Bericht am Ende («18 von 20 Personen erkannt, 2 Fehlalarme, Reaktionszeit»).
   Das ist der eigentliche Kern des Angebots.
4. **Betrieb im Internet**: Server mit Grafikkarte, eine Instanz pro Kunde, Steuerung über eine Webseite statt Windows-Fenster
   (das CONTROL-Protokoll ist ein guter Anfang), Kosten pro Stunde, Bildstrom mit wenig Verzögerung.
5. **Sicherheit**: heute offene Ports ohne Passwort und ein unsigniertes Selbst-Update – für einen Dienst braucht es Konten,
   HTTPS, Trennung der Kunden, signierte Updates. Das Repository ist öffentlich: für ein Produkt privat machen und eine Lizenz
   wählen. **Den Signierschlüssel erneuern** (er stand am 26.10.2026 im Chat); danach brauchen alle Pis einmal eine Version
   mit dem neuen öffentlichen Schlüssel (`UPDATE_PUBKEY`).
6. **Rechtliches und Geschäftliches** (fachlich prüfen lassen): AGB, Haftung, Datenschutz (nDSG, bei EU-Kunden DSGVO),
   Lizenzen aller Teile (Godot MIT; gekaufte 3D-Modelle oft eingeschränkt), Preismodell. Die Gewehr-Szene für ein
   Profi-Produkt eher weglassen.

**Vorgeschlagener erster Schritt:** zwei, drei mögliche Kunden fragen, was sie wirklich testen wollen. Technisch zuerst lokal:
der Simulator erscheint auf dem PC als **RTSP- / ONVIF-Kamera** (z. B. Bilder per ffmpeg an MediaMTX, ein kleiner
ONVIF-Dienst für Erkennung und PTZ) – ohne Server, mit einer gängigen Videoüberwachungs-Software testbar.

## Was in dieser Umgebung nicht getestet werden konnte

- Die Windows-.exe auf echter Hardware (hier nur Linux mit llvmpipe über Xvfb).
- Die Erkennung des Edge-Pfads unter Windows.
- Nebel im Forward+-Renderer (Forward+ ist ab 3D-1.6 nur noch über die Vulkan-.bat erreichbar).
- Die echte Netzsuche zwischen PC und Pi.
- Ton (Schuss «Plopp», Treffer «Boing») – hier ohne Lautsprecher.
- Die Bildrate der neuen Szenen auf dem alten i5 (Wald hat rund 300 Bäume).
- Das Selbst-Update unter Windows (Umbenennen der laufenden .exe, HTTPS zu GitHub) – hier nur unter Linux mit lokalem Server.
- Das Zielen mit der echten Maus (hier nur mit dem Knopf «Schuss aus der Kopfkamera» getestet).

## Testwerkzeuge in dieser Umgebung (nur als Hinweis, liegen nicht im Repo)

- Godot 4.3 von GitHub (Releases 4.3-stable, Linux-Programm + Export-Templates nach `~/.local/share/godot/export_templates/4.3.stable`).
- Projekt direkt im geklonten Repository (`simulator3d/`); `.godot/` ist in .gitignore.
- Start auf virtuellem Bildschirm und HTTP-Abfragen über kleine Hilfsskripte.