# Übergabe: Motion Watch 3D-Simulator

Stand: 28.10.2026 · Simulator-Version **3D-3.86** · passende MoveEye-Version (früher Motion Watch) **2.96.2**

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
**Handy-Eingaben (3D-1.13):** `Input.dispatchTouchEvent` erzeugte keinen Klick (Schalter wie «Marks» reagierten nicht, der
Joystick bewegte sich nicht). Jetzt `Input.dispatchMouseEvent` (mousePressed / mouseMoved mit `buttons: 1` / mouseReleased) –
die Seite bekommt Pointer-Ereignisse und Klicks. **Wichtig:** In der Sitzung mit `setDeviceMetricsOverride` teilt Chrome die
Eingabe-Koordinaten durch den deviceScaleFactor, darum CSS-Punkte × `DSF`. `DSF` ist jetzt 1 (ein Viertel der Bildpunkte, das
Handy wird ohnehin kleiner als 390 px gezeichnet), Screenshot JPEG 65 mit `optimizeForSpeed`, alle 150 ms.
Läuft noch ein Browser eines früheren Laufs auf Port 9333 (Profil gesperrt), wird er weiter benutzt (`_browser_running`).
Getestet mit dem Chromium von Playwright (`/opt/pw-browsers/...`, Option `--browser`) und Klicks per XTest: Marks ein/aus,
Joystick Pan 35 % → 99 %. Das PID von Motion Watch auf dem PC steht in `motionwatch_pc/mw.pid` (zum Stoppen nach Wiederverwenden).

**Bedienfeld (3D-1.13)** im Stil der Motion-Watch-Webseite: `scripts/ui_style.gd` (Farben `--bg #0a0e14`, Karten `#151e2b`,
Rand `#1f2b3a`, Akzent `#3b8cff`, gesperrte Grossbuchstaben als Überschrift, ▸/▾ grün). Karten: Verbindung, Kameras,
Werkzeuge, dann je Gruppe der Regler (Knöpfe nebeneinander), Tasten. **Virtuelle Maschine** (`main._in_vm()`, auch llvmpipe):
Grafik «einfach» und weniger Vorschaubilder. Motion Watch auf dem PC: `sim_fps` 4 (wenn noch 6), `sim_eco` an.
Gewehr geht beim Verlassen der Wildbeobachtung von selbst aus.
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
**3D-3.16 bis 3D-3.36** wurden in einem anderen Chat gemacht (siehe Git-Geschichte und «Lies mich.txt», Abschnitte «NEU IN …»).

**3D-3.86:** neues `scripts/objects.gd` (`OBJ`: alle COCO-Klassen, die nicht Besucher sind, als Grundformen-Daten [Form, Masse, Lage, Farbe, Drehung], `build(main, kind)`, `CATS`, `COCO_VISITORS`), neues `scripts/inventar.gd` (Fenster mit Reitern, Kacheln mit Bildern – Besucher aus `main.thumbs`, Dinge einmal in einem SubViewport gerendert –, `place_kind = "obj:<kind>"` → `_place_at` → `place_at_screen`; `user://objekte.json` {szene: [{k, x, z, r}]}, `rebuild()` nach jedem `set_scene`; Steuerbefehl `inventar` {do: info | open (tab) | close | add (kind, x, z, r) | clear}), neues `scripts/quick.gd` (Schnellzugriff oben im Bedienfeld, Kachel-Menüs mit `PopupMenu`), `toolbar.gd` eine Zeile `MAIN_ROW` (Text = Knopf, Liste = Menü), neue gezeichnete Symbole in `ui_style.gd` (clock, box, map, head, puzzle, phone, meter, route, plan), `mini.gd` zeigt `mw_logo.gd` statt «3D». **3D-3.85:** Makeover 21–25: neues `scripts/blindmap.gd` (Steuerbefehl `blindmap` {do: start (az, dist, hour, walk) | info | stop}; Person an jedem Punkt, `found` = `mw_det.persons` > 0, `inview` = `testrun.visible` mit Kopfkamera; `auto_visitors` aus solange); `main.farecreate()` (Steuerbefehl `farecreate` {cause: animal | wind | light | rain | car | other | end, hour, pan_deg, rain}). **3D-3.84:** Makeover 16–20: `device.gd` Plätze `door` / `bike` / `car` (`NAMED`, `_named_target()`, `set_scene` ruft `dev2._put()`); `patrol.gd` `goto_point(p, why)` (Mission alarm | dock | goto: hin, umschauen, zurück zu `home_pos`, dann alte Route), `batt` (−0.05 %/s, < 20 % → dock, lädt 1 %/s an der Station), `_dock_tick()` (Ladeplatte in `scene_parent`), `alarm_point()` (erster Rahmen von MoveEye auf den Boden, sonst 8 m geradeaus), `rover_info()`; Steuerbefehl `rover` {do: info | patrol (on) | alarm | dock | goto (x, z)}. **3D-3.83:** Makeover 8–11: neues `scripts/overlay3d.gd` (auf `HELPER_LAYER`; Zonen aus `mw.zones` – Punkte 0..1 der Kopfkamera, mit `project_ray_*` von `cams[0]` auf den Boden; Patrouillen-Punkte `mw.waypoints` [pan°, tilt°]; Rahmen `mw_det.boxes` → Besucher in 3 m = grün, sonst rot, Personen gut im Bild ohne Rahmen = orange; `main.show_zones3d` / `show_det3d` in `KEEP`), Steuerbefehle `whatif` {hour, weather, kind, n, pan_deg, dist} (`main.whatif()`), `twin` {name, lat, lon | op: info} (`twin_info()`), `overlay`. MoveEye 2.96.5 schickt `zones` / `waypoints` im Zustand und schreibt `situ` in die Aufnahme-Info. **3D-3.82:** neues `scripts/templates.gd` (Fenster «Vorlagen», `main.templates`, Werkzeugleiste `templates`): Reiter Szenen / Orte / Bausätze / Eigene Datei; `import_file()` kopiert .glb (bzw. wandelt .gltf um) nach `user://vorlagen/`, Liste `vorlagen.json` {file, x, z, rot, scale, auto}; `place_into(root)` (aus `scenes._vorlage()`) stellt die Modelle auf den Boden, `auto` = Einheit geraten (>300 m → cm), Hindernisse aus den Mesh-AABBs (max. 250, nicht flach / nicht hoch oben); `get_window().files_dropped` → Szene «vorlage». Steuerbefehl `templates` {do: info | open | import | drop | remove | adjust}. Neue Szenen `bauernhof`, `seeufer`, `baustelle` (`test_props["Werkzeugkiste"]`), `stellplatz`, `vorlage` mit `_fence()`. **3D-3.81:** `dev_updates` (in `KEEP`, Standard an) + `_dev_check()`: jede Minute GitHub-API «commits?path=simulator3d/version.json» mit ETag (304 zählt nicht ans Limit), neuer Commit → `run_update(true, false)`; `update.gd` hängt `?t=` an die version.json (am Cache vorbei). MoveEye 2.96.2 schaltet `update_fast` einmalig ein (`dev_phase_done`). **3D-3.80:** neues `scripts/visitlog.gd` (`main.spawn()` meldet jeden Besucher, Auswertung alle 0.5 s mit `testrun.visible` nur Kopfkamera und `mw_det`), Steuerbefehl `visits` {since} → MoveEye 2.96.1 holt alle 30 s (`355_simulator_tagebuch.py`, `sim_diary.jsonl`, `/api/sim_diary`). **3D-3.79:** Name MoveEye (früher Motion Watch) in allen Texten; `mw_logo.gd` zeichnet das neue Logo (Sichtfeld, gehende Person mit Erkennungs-Ecken), `icon_sim3d.png` neu. Interne Namen (`mw_*`, Dateien, Ports, `mwsim`) bleiben. **3D-3.78:** `gamewiz.gd` im Fenster neu (`_draw_prog`, `_card`, `_group`, `_option_row`, Gleiten über `_slide`-Ränder); Modell unverändert (4 Schritte, Motion Watch zeigt sie gleich), Schritt 3 hat `PLAYER_OPTS` (Bots usw.); `wizpics.gd` hat Bilder `seek`, `patrol`, `free`. **3D-3.77:** Spieler haben `kind` (phone | local | bot); `game.state_for(p)` (früher in `_send_state`), `add_local()` / `remove_local()` / `set_bots(n)`, `_bots_tick()`; neues `scripts/localplay.gd` (eigene CanvasLayer 30, Ansicht = `p.vp` bzw. Kopfkamera, Tasten, Herzschlag, Wiederholung `_draw_replay`), Steuerbefehl `localplay` {do: start | stop | key, role}. Wiederholung: `rec` / `rec_ev` → `replay` (Nachricht `rp`, Handy fragt mit `replay`). Abzeichen `BADGES` / `_badges_of()`. Geister `user://spiel/geister.json` (Ebene 16, nur Spieler), Tagesaufgabe `daily_plan()` / `user://spiel/tagesaufgabe.json`, Übungsrunde `TUT` / `_tut_tick()`. Spielart `seek` (`_seek_start`, `seek_drive` → `rover_pad.command()`, `seek_hiding()`). Neues `scripts/headpad.gd` («Kopf steuern» → `main.mw_look()` / `mw_light()` über `mw_cmd` op look | light, Motion Watch 2.95.103). Einstellungen `game_bots`, `game_tutorial`, `game_daily`, `game_ghost`, `game_heart` (in `KEEP`). `mini.gd` kompakt (330 × 84). **3D-3.76:** `patrol.ask()` (Frage «Was soll überwacht werden?», `places()`, Klick-Modus `edit = "pick"`), `guard_start()` / `plan_round()` (Ring um den Ort, Punkte ≥ 1.2 m von Hindernissen über `main.blocked()`, Umwege bei `_way_blocked`), Kopf zielt auf `guard.c`; Steuerbefehl `patrol` {guard: [x, z, r, name] | ask}. Uhrzeit: `hour_now` / `hour_at` / `speed_now` in den Einstellungen (alle 20 s und in `release_ports()` gespeichert). Spiel: Nachricht `leave` (Handy-Knopf 🚪, `lvBox`), Pakete werden vor dem Schliessen gelesen. `main.tree_spots` (Kronen aus `scenes.tree()`), `main.view_free()`, `game.clear_start()` und kürzere Kamera in `_steer`. `main.restart_args()` gibt `--old-pid` mit; `_stream_watch()` (3D-3.75) stoppt den alten Prozess. **3D-3.75:** neues `scripts/surprise.gd` (Überraschungsnacht: `start(kind)` power | fogbank | distract | glare | still, `_watch()` vergleicht `mw_det.persons`, Licht und Sirene mit der Wahrheit `_truth_person()`, `morning()` → Bericht + `user://ueberraschung/*.json`; `main.surprise_on` in `KEEP`, `main.power_off` schaltet `lamps` / Fenster / Türlicht aus; Steuerbefehl `surprise` {op: get | on | off | start, kind | morning}). Grafik: `view_scale` (`scaling_3d_scale` nur der grossen Ansicht), `win_fps` (Engine.max_fps bei offenem Fenster), `auto_perf` + `_perf_tick()` (< 14 Bilder/s während 20 s → eine Stufe leichter). `tunnel.gd`: `_fail()` mit wachsender Wartezeit (3–15 s), Leerlauf-Leitungen leben 40–55 s (`RECYCLE`), Pipe ohne Verkehr 180 s → zu; Motion Watch 2.95.101 nimmt die neuste Leitung und verwirft Leitungen älter als 100 s (`TUN_MAX_AGE`). `pruefstand.gd`: `auto` (`user://pruefstand/auto.json` {on, last}), `_auto_tick()` startet `start(["quick"], 1)` bei neuer `mw_version` (90 s nach dem Auftauchen, 180 s ohne Klick, kein Spiel / Testlauf / Überraschung), sendet mit Schlüssel; Steuerbefehl `pruefstand` {do: auto, on, last, touch_ago}. **3D-3.74:** `cond` hat neu `fogged` / `dirt` (Uniforms in `lens.gdshader`), `shake` (dreht `cams[0]`) und `net` (`_net_hold`: JPEGs bleiben stehen). Besucher `sneaker` (`events.sneaker()`, Meta `sneak`; Route-Haltung `crouch` ≥ 1.5 = kriechen in `actor.gd`; Licht → erstarren, Lampe aus; Sirene → `fled`). `night_weather` + `_night_weather_tick()` (Plan pro Nacht, Tau setzt `cond.fogged` 4–8 h). `kids.gd`: Missionen (`_mission`, `_mission_check` auch bei verstecktem Feld, `_won` → `main.kids_stars` in `KEEP`; `main._say(..., lay)` mit `HELPER_LAYER`). **3D-3.73:** Szene `zuhause` (`scenes._zuhause()`, `home_item()` mit `HOME_KINDS`/`HOME_LINES`/`HOME_DEFAULT`) aus `main.home_items` (`user://zuhause.json`, `home_load/save/rebuild`); Baukasten `scripts/home_editor.gd` (Klick = setzen, `_unhandled_input` → `home_editor.handle_input`), Steuerbefehl `home` {op: get | set | edit}. `dataset.export_pack(n)` schreibt ein YOLO-Paket nach `user://trainingsbilder/<zeit>/` und ein ZIP auf den Schreibtisch (`EXPORT_CLASSES`, mehrere Besucher pro Bild, Haltungen, leere Bilder, Szenenwechsel alle 60 Bilder); Steuerbefehl `dataset` {op: export, n}. **3D-3.72:** `test_props` (Name → Knoten, von `scenes.gd` im Camping-Platz gesetzt: Velo, Zelt, Tisch, Kühlboxen, Grill) + `set_prop()`; `set_sabotage(cover, turn)` (schwarzes Tuch 0.36 m vor dem Kopf – hinter der Near-Plane – bzw. `sabotage_turn` auf den Schwenk); `ref_night_test()` mit `_night_test_tick()` (day0 → day: refscan → night0 → night: `refcompare_day`); Planer-Knopf «Hierhin stellen + Referenz-Scan»; Steuerbefehle `prop`, `sabotage`, `ref_night_test`. **3D-3.71:** Anfragen an Motion Watch: `mw_request(op)` legt `mw_cmd` {id = Unix-ms, op: refscan | refcompare | refstop} in die Antwort auf `/state` (`world_reply`); Motion Watch führt sie einmal aus (`SIM.cmd_seen`) und meldet den Stand in `mw.refscan` (busy, step, n, ref_n, last, cmd_seen) → `refscan_text()` in den Werkzeugen. `set_bike()` / `bike_node` (Testhilfe), Steuerbefehle `mw_request` {op} und `bike` {on}. Neue Anfragen an Motion Watch immer über `mw_cmd`. **3D-3.70:** Steuerbefehl `shoot` {x, y, who} → `main.mw_shot()`: in einer Runde `game.mw_catch` (mwhand) bzw. `game.shot_at` (alle anderen Spielarten), sonst Strahl aus `cams[0]` durch (x, y) gegen `hit_spheres()` der Besucher; Treffer: Menschen `scare()`, Tiere `hit()`; daneben: `mw_shots.false` + Fehlalarm. **3D-3.69:** neues `scripts/kids.gd` (Kinder-Bedienfeld: Kacheln mit `thumbs` bzw. gezeichneten Symbolen, Murmli in `_draw_marmot`, Töne als erzeugtes `AudioStreamWAV`, Konfetti als ColorRects mit Tween auf eigenem CanvasLayer). `main.kids_on` / `kids_scary` / `kids_thief` / `kids_laser` / `kids_sound` (in `KEEP`), `_apply_kids()` blendet alle Kinder von `ui_box` ausser `kids` und `kids_seg` aus, `ask_adult()` (Rechenaufgabe), `spawn()` ersetzt Wildtiere / Diebe nach Einstellung, `game.hit_fx` ohne Laser nach Einstellung, `UI.segment` legt `meta "paint"` ab. **3D-3.68:** `main.release_ports()` (net.stop, Spiel-Server zu) vor jedem `OS.create_process` des Simulators selbst (Update, ANGLE-Neustart): Windows vererbt sonst den Lausch-Port, der neue Simulator meldet «Port 8765 is busy». `_stream_retry(60)` nimmt nach 8 Versuchen `ALT_PORTS` (8775/8785/8795); Tunnel leitet «GO 8765» auf `net.port`; Beacon meldet den Port. Kinder wie `mwpc` (Python) können den Port weiterhin erben – darum der Ausweichport. **3D-3.67:** `/view.jpg?clean=1` setzt `view_clean_t`; 3 s lang zeichnet `rover_pad.gd` nichts (`modulate.a = 0`, Maus durch, `_over_hud` überspringt unsichtbare Boxen) – `visible` bleibt, sonst stünde `command()` (Patrouille, Erkunden, Browser-Controller) still. **3D-3.66:** `patrol.handle_input()` im Modus «points» gibt Klicks an die Ansicht weiter (Punkt nur bei Klick < 8 px Bewegung, `_click_at`), Rechtsklick nur auf einem Punkt; Esc setzt `patrol.edit = ""`; `toolbar.gd` zeigt dann `_hint` mit «✓ Fertig (Esc)». Getestet mit XTest (`/tmp/claude-0/menu/xin.py`). **3D-3.65:** `stream_last` (in `KEEP`, nur vom Schalter gesetzt) startet das Senden wieder; `_stream_retry(30)` versucht `net.start()` jede Sekunde, solange der Port nach einem Update noch besetzt ist. **3D-3.64:** `HELPER_LAYER` (128) in `main.gd`: Hilfsmarken nur für den Bediener (`view_cam.cull_mask = 1 | HELPER_LAYER`), die Kameras für Motion Watch (Maske 1 | Linse) sehen sie nicht – Patrouillen-Pfosten/-Linien/-Nummern und die Empfangskarte. Neue Hilfsmarken immer auf diese Ebene legen. **3D-3.63:** `mw_logo.gd` bewegt nur noch die Pupille (±4.5 von 100). Motion Watch 2.95.88 legt das Wärmebild in der Simulation nach `fov_h` / `w` / `h` aus `/info` passend ins Kopfkamera-Bild (`ThermalCam.sim_geom()` / `fit()`) – `TH_FOV` oder die Auflösung ändern ist also unkritisch, solange `/info` stimmt. **3D-3.62:** neues `scripts/mw_logo.gd` (oranges Motion-Watch-Symbol im Kopf des Bedienfelds, gezeichnet in `_draw()`, die Pupille wandert in 6 s links/rechts; gleiche Bewegung wie `APP_ICONS_ANIM["classic"]` in Motion Watch). **3D-3.61:** neues `scripts/patrol.gd` (Route Punkte/Bereich, `command()` geht über `rover_pad.command()`, `head_yaw` überschreibt den Kopf, `user://patrouille.json` je Szene, Steuerbefehl `patrol`), neues `scripts/toolbar.gd` (Werkzeugleiste unten, alles per Maus), Spielart `patrol` (`mw_decides()` mit `patrol_judge`). **3D-3.60:** `place_rover_at()` / `place_kind = "rover"`; Spielart `free` (kein Schiedsrichter, 6 h, startet von selbst sobald jemand da ist); `explore.set_invite()` (QR), `explore.spectator()`; `_spectate_explore()` (Ziele Rover + freie Spieler) und `_spec_free()` (freie Sichtlinie, sonst von oben), Spiel-Einstellung «group»; Steuerbefehl `explore` {invite, spectate, place}. **3D-3.59:** Steuerbefehl `pad` {ax[4], bt[17] (Standard-Belegung, Trigger als Wert), name} → `explore.remote_pad()`; gilt 0.6 s, `_axis()` nimmt das Grössere von Browser und eigenem Joypad. **3D-3.58:** `/view.jpg?w=&q=&fmt=webp` → `main.view_request()` (Breite 320–2560, Qualität, WebP; `view_mime`); solange ein `/view.mjpg`-Strom offen ist, bleibt es JPEG. **3D-3.57:** `mast_h` / `set_mast()` (Stange, gespeichert; `HEAD_H` bleibt der Standard). **3D-3.56:** `explore._blocked()` (Hindernis ≥ 1 m Höhe nahe der Linie Rover–Ansicht) → `auto_top` nach 0.3 s, zurück nach 1.5 s frei. **3D-3.55:** neues `scripts/explore.gd` (Erkunden mit dem Rover: setzt Mover an, Panel weg, eigene Kamera hinterher / Fahrer / oben; Eingabe-Gerät aus `_input`; Joypad über `Input.get_joy_axis`; `rover_pad.command()` nimmt `explore.command()` dazu; `_fly` ruht; Steuerbefehl `explore` {on, view, drive}). **3D-3.54:** `testrun.ways()` nur Wege der aktuellen Szene (Leitlinie: Daten kartenunabhängig, Kartengebundenes nur auf seiner Karte). **3D-3.53:** `mw_det.boxes` (0..1, Kopfkamera) von Motion Watch: `gamelearn.reported_for(p)` ordnet Meldungen Spielern zu (`overlap`), `mw_false` = Rahmen ohne Spieler/Besucher; `_mw_referee` mit `MW_HOLD` / `MW_PAUSE` je `game_level` (easy: Kriechen sicher); `sneak_list()` / `records.blind`; `dataset.load_game()` (Steuerbefehl `dataset` op `game`) für die KI-Prüfung in Motion Watch. **3D-3.52:** Treffer-Sequenz in `game.gd` (`hit_fx`: Laser / Farbe / Blitz nach `game_fx_*`, Handy `hitFx()`; der Spieler bleibt 0.9 s stehen, dann `_to_start`), `mw_catch(who, x, y)` = Antippen im Livebild (Box aus `gamelearn.box()`), neues `scripts/gamelearn.gd` (verpasste Bilder, Spielbericht, Schleichwege in `user://spiel/<runde>/`, Bonus `blind`, Senden nach `feedback/spiel/`), Testlauf-Plan «spielwege» (`testrun.gd`, Wege aus `res://spielwege/` und `user://spiel/`). Steuerbefehl `game_test` nur für Tests. **3D-3.51:** die Karte «Kameras» liegt jetzt in der Liste direkt unter «Verbindung» (nicht mehr im festen Kopf; bleibt beim Suchen sichtbar, weil sie nicht in `top_cards` ist). **3D-3.50:** `UI.fold_active(body, st)` färbt Symbol und Pfeil einer Karte (0 grau, 1 grün, 2 orange) – der Pfeil zeigt den Zustand der Funktion, nicht mehr «offen»; Namen bleiben weiss. Gruppen über `group_active()`, dazu Kameras (verbunden) und Werkzeuge (Motion Watch / Prüfstand / Trainingsbilder läuft). **3D-3.49:** neues Fenster `scripts/pruefstand.gd` (Werkzeuge → Prüfstand, Steuerbefehl `{"action":"pruefstand","do":"get|open|start|send"}`): misst ein Motion Watch auf dem PC mit den Plänen von `testrun.gd` (nur Kopfkamera), schreibt `user://pruefstand/<datum>_<version>.json` im Format von `pruefstand/ergebnisse/` und sendet per GitHub-API (PUT contents, Schlüssel in `user://pruefstand/schluessel.txt`) oder legt die Datei auf den Schreibtisch. Datei-Modus: `mwpc.gd` `override_file` startet eine gewählte webcam_bewegung_X.py statt der eingebauten. **3D-3.48:** `test_start` nimmt `cams` ([0] = nur Kopfkamera zählt für die Wahrheit); der Bericht hat `visitors` (Art, Grösse px, Licht, Erkennungszeit) für `pruefstand/pruefstand.py` im Repository. **3D-3.47:** Tunnel-Zeile zeigt «Ziel: host:8766». **3D-3.46:** Unterteile (`UI.sub_fold`) ohne Einträge aus `ui_items` brauchen `set_meta("always", true)`, sonst blendet `_apply_simple()` sie aus – so war das Tunnel-Feld unsichtbar.

**3D-3.45 – Tunnel:** `tunnel.gd` hält ~10 Verbindungen zu MW:8766 offen (Hallo `MWTUN1 <code>` → `OK`); auf `GO <port>`
(8765 Simulator, 5057 KI-Rechenhilfe) verbindet es sich zu 127.0.0.1:<port> und reicht die Bytes durch (Rest nach der GO-Zeile
nicht verlieren!). MW: Türen 127.0.0.1:18765 / 15057, stellt `sim_url` von selbst um. KEEP: tunnel_host/code/on; CONTROL `tunnel`.

**3D-3.44 – Helfer für Motion Watch:** `mwpc.gd` startet MW mit `--helper` und fragt `/helper/hello` (Port 5057); `info()`
gibt `helper` {port, code} an den Pi. `tv.gd` (CanvasLayer 5, blendet `ui_layer` aus, CONTROL `tv`, Taste T). `planner.gd`
(Abdeckung mit `line_free`, `set_home`/`home_pos`, CONTROL `planner`). `replay.gd` (CONTROL `replay`, Geisterfigur, Kopf über
`replay.servo`). `show_netmap` (CONTROL `netmap`). `dataset.gd` (CONTROL `dataset`, `/dataset/<i>.jpg` in net.gd; Bilder über
die normale Bildschleife mit `snap_want` – nie selbst `_capture` aufrufen; Besucher mit fernem Ziel, sonst geben sie sich frei
→ Absturz). Gruppensymbol-Zustände gehen als `groups_on` an die Seite.

**3D-3.43 – Rand, schwebende Kamerabilder, grüne Symbole, Pi-Build:** `_palette_item` mit Zeilenumbruch, Panel
`grow_horizontal = BEGIN` (Test-Aktion `ui_wide` listet zu breite Teile). `show_panel(false)` hängt die Karte «Kameras» in
`cam_float` (Griff-Leiste, `cam_fx`/`cam_fy` in KEEP). `group_active()` / `_paint_groups()` färben die Gruppen-Symbole.
`apply_visit_preset` räumt auf, setzt `PRESET_HOUR` und schickt sofort Besuch. Export-Vorlage «Linux Pi» (arm64, ETC2),
ZIP `MotionWatch3D_Pi.zip` mit «Start auf dem Pi.sh»; `version.json` hat dazu `pi`. `update.gd` sucht auf Linux-ARM nicht
selbst (Motion Watch bringt die Pi-Version). Auf echter Pi-Hardware ungetestet.

**3D-3.42 – Bilder im Spiel-Assistenten:** `wizpics.gd` (SVG-Zeichnungen pro Karte, `texture()` über `Image.load_svg_from_string`);
das Modell schickt sie als `pic` / `pics` mit, Motion Watch zeigt sie als `data:image/svg+xml`. Text in den SVG zeigt nur der Browser.

**3D-3.41 – Spiel-Assistent im Simulator:** `gamewiz.gd` (Fenster-Teil + Modell `model()` / `op()`); CONTROL-Aktion
`{"action":"gamewiz","op":"get|open|close|pick|set|extras|next|back|last", "key", "value"}`. `main.control_set(id, value)` setzt eine
Einstellung wie «set». Motion Watch (2.95.48) rendert das Modell im Reiter Simulator (`gwOp`, `gwPaint`, Abfrage alle 1.5 s).
«Wie letztes Mal»: `user://gamewiz_last.json`. Im Fenster ohne Emoji (`plain()`), Motion Watch zeigt sie.

**3D-3.40 – Abläufe und Stimmungen:** `events.gd` (in main als `stories`): burglar, bbq, homecoming(parcel), fox_trash, boar_group,
kids_tag, mowing, night_lapse; Helfer `_later` (Zeitgeber, nur gleiche Szene) und `_watch` (wartet auf eine Bedingung über `main.anims`).
Besucher mit Meta «shy» fliehen vor weissem Licht / Sirene (`_life`). `VISIT_PRESETS` Feld 7 = eigene Besucherliste (`preset_kinds`).
`life.calendar()` (Wochenende, Jahreszeit; Schalter `calendar_on`). Neue Teile «Fahrzeuge» und «Abläufe» in der Karte Besuch.

**3D-3.39 – Mehr Besucher:** `actor.gd`: `PERSON_VARIANTS` (cyclist, stroller, drunk, courier, police → kind «person» + variant,
`_person_extras`, `_animate_cyclist`), `CAR_VARIANTS` (tractor, moto, van → kind «car», `_build_tractor`, `_build_moto`), neue Tiere in
`_build_animal` (cow, sheep, horse, chamois, ibex, lynx). `main.visit()`: couple, horse_walk, cows, sheep_flock, courier, police, drunk,
cyclist, bats / owl (`_night_flyers`, keine Besucher, nur Bewegung). `life.activity()` und `Scenes.AUTO` kennen alle.

**3D-3.38 – Besuch neu gegliedert:** Teile in `GROUPS` («Vorlagen», «Besucher hinsetzen», «Menschen schicken», «Tiere schicken»,
«Fahrzeuge und Abläufe», «Von selbst», «Verhalten»); `VISIT_PRESETS` + `apply_visit_preset()` (Auswahl `visit_preset`);
`VISIT_EMOJI` → `extra.emoji` (Seite von Motion Watch zeigt es vor dem Knopftext); Knöpfe im Fenster mit Bildchen (`thumb_btns`).
Test-Befehl `ui_scroll` kennt `open` (eine Karte mit allen Teilen öffnen).

**3D-3.37 – Verbindung:** `fold_card` merkt sich `head` und `icon` (Meta); `_draw_group_icon` nimmt die Farbe aus `get_meta("col")`.
`_update_status()` färbt Symbol und Titel der Karte `conn_body` (aus / wartet / verbunden).

**3D-3.15 – Mover-Stick im Simulator:** `rover_pad.gd` (Control unten rechts, nur bei `mover_on`; Ziehen oder Pfeiltasten →
`main.pad_drive` (vor, rechts) + `main.pad_on`; überstimmt in `_drive()` die Befehle von Motion Watch; «Hinterher» = Verfolgerkamera).
Achtung: `pad_on` ist ein Bool pro Bild (keine Zeitschwelle – mit langsamer Grafik dauert ein Bild > 0.3 s).
3D-Gebäude-Diagnose: `b3d.diag` → `geo.b3d_diag`, Datei `user://orte/3d_gebaeude_bericht.txt`, Anzeige in Schritt 2; gzip ohne
Kopfzeile wird entpackt (`_unzip`). Motion Watch 2.94.4: `mover_sim_show` = Stick in der Simulation auch ohne Mover (nur Anzeige).

**3D-3.14 – Orts-Assistent:** `karte.gd` Schritte 1–3 (`step`, `_show_step`, `_page_env`, `_page_objects`, `_build`); lädt mit
`geo.load_place(..., rebuild=false)` und baut erst bei «Szene bauen» (`main.place_loaded()`). `geo.detect_env()` (Häuser im
Umkreis 150 m, Anteil Wald / Wasser / Wiesen / Siedlung im 10-m-Raster, Fluss, Höhe) → `geo.env`, `env_why`.
`geo._env_props(env)`: `ENV_PROPS` pro Umgebung, Autos entlang kleiner Strassen (`park_segs`), Boote / Schilf am Ufer (`water_polys`).
Einstellungen `ort_env` / `ort_hide` / `ort_cars` / `ort_forest` / `ort_camp` (KEEP). Test-Befehl `{"action":"wizard","op":"pick|next|set"}`.

**3D-3.13 – Verstecke:** `scenes.gd`: `prop(kind, p, rot)` (15 Arten, jede mit Hindernis + `set_obstacle_height`),
`hide_props(n, dmin, dmax, kinds, keep_clear)` (Abstand ≥ 3 m zu Hindernissen, nicht auf Strasse / `data["clear"]` z. B. Teich),
Szene `verstecken` (`_verstecken`), `EXTRA_HIDE` = zusätzliche Verstecke pro Szene nach dem Bau.

**3D-3.12 – Übersichtskarte:** `minimap.gd` (Control im UI-Layer, zeichnet `obstacles`, Kamerakegel, Besucher, Spieler, Ziel, Luftbild),
`map_on` / `map_size` / `map_span` (KEEP), `set_map()`, Taste M, Knopf «Karte».

**3D-3.11 – Mover und Mini-Kästchen:** `rig` (Basis von Motion Watch, Elternknoten von `head`) + `chassis` (Kettenfahrzeug);
`mover_on` / `mover_max` (KEEP), `_drive()` liest `mw.drive.l/r` (−1 … 1, von Motion Watch 2.94.0), echte Zeit seit dem letzten Aufruf
(Bilder werden zum Sparen ausgelassen), Hindernisse wie Besucher, Gelände `ground_y`; Antwort an Motion Watch: `"mover": true`.
Test-Aktion `mover`. mini.gd: eigene CPU (Windows: PowerShell-Schleife über `OS.execute_with_pipe`, nur solange das Kästchen da ist;
Linux /proc), `set_tiny()` = Symbol 64 × 64 (Test: MWSIM_MINI_TEST=2). Windows-Messung nicht getestet (kein Windows hier).
Motion Watch 2.94.0: `MOVER`, `MoverControl` (PCA9685 als Motor HAT, 1600 Hz, Adafruit- oder Waveshare-Belegung, 0,6-s-Wächter,
sanftes Anfahren), `/api/mover`, `st.mover`, zweiter Stick im Web (`#mstick`, `body.mover`, Vollbild `#vo-mctl`) und im Fenster (`MoverPad`).

**3D-3.10 – 3D-Gebäude:** `b3d.gd`: `tileset.json` von 3d.geo.admin.ch (`geo.url("b3d")`), Baum ablaufen (region / box / sphere,
verschachtelte tileset.json, höchstens 40 Kacheln), b3dm (RTC_CENTER) oder glb mit `GLTFDocument` laden, glTF y-oben → z-oben →
Kachel-Transform → minus `ecef0` → Ost/Oben/Süd (Doppelgenauigkeit für die grossen Zahlen), flache Normalen passend zur Godot-Wicklung,
Haus um den Kopf weg (`keep_out`), Höhe an das Gelände angepasst (`_align`, 30-%-Wert). Shader `b3d.gdshader` (Dach/Wand nach Normale,
Fenster aus der Weltposition, nachts einzelne hell, `geo._b3d_night`). OSM-Häuser dann nur noch als Hindernisse. Nicht mit echten
swisstopo-Daten getestet (Ersatz-Server mit eigener b3dm-Datei); Draco-komprimierte Kacheln kann Godot 4.3 nicht → Rückfall auf OSM.

**3D-3.9 – Karte und Bedienung im Web:** Control-Typ `map` (`ort_map`; Wert «lat, lon», Setzen «lat, lon[, Name]» → `set_place_text`),
im Fenster ein Knopf auf `open_map`. `extra.iconk` = Name des gezeichneten Symbols. Motion Watch 2.93.16: `SIMMAP_JS` (`simMap` =
Kachelkarte swisstopo im Browser, Suche über api3 SearchServer direkt vom Handy; `simCtlBuild` = Bedienung wie im Simulator, SVG-Symbole
`SC_ICON`) – eingesetzt in SIM_PAGE und WEB_PAGE über `/*SIMMAP*/`. Achtung: `window.simCtl` gibt es dort schon (Abfrage).

**3D-3.8 – Sonne und Spiel im Gelände:** `sun_pos()` (NOAA, Ort `ort_lat/lon` sonst 46.8/8.2, `season` «today» oder Monat,
MEZ/MESZ grob nach Tag im Jahr), `sun_el()` nutzt sie, `_update_sky` dreht die Sonne nach dem Azimut (Rotation y = 180° − Azimut).
`horizon_el(az)` (Geländewinkel in 2°-Schritten, Cache `_horizon`), `sun_behind_hills()` dämpft Sonnenlicht und Wärme, `sky_mode`
LIGHT_ONLY dahinter (sonst dunkle Sonnenscheibe). game.gd: `_g()` setzt Ziel, Starts, Kristalle, Zelle, Basen auf `ground_y`.

**3D-3.7 – Kamerabilder fest:** Bedienfeld = `outer` VBox: `top_box` (Kopf, Werkzeugleiste, Karte «Kameras») + ScrollContainer mit `ui_box`.

**3D-3.6 – Maus-Steuerung:** `_unhandled_input` neu: `m_btn`, `m_grab` (Bodenpunkt), `_pan_to`, `_orbit` (Drehen um den Punkt),
`_zoom_at`, `fly_to` (Tween), `_visitor_at` (Bildschirm-Abstand), `selected` / `follow` / `_sel_action`; `_build_view_bar()` (Knöpfe,
Kompass, `sel_box`, `sel_ring`, `thermal_full` = Ansicht 3); `_view_overlays()` jedes Bild. Test-Aktion `visitors` liefert `sx/sy`.
Hinweis Xvfb-Tests: das Loslassen eines Knopfs kommt erst mit dem nächsten Ereignis an.

**3D-3.5 – Bedienfeld:** `GROUPS` (Gruppe, gezeichnetes Symbol `UI.group_icon`, Emoji fürs Web, Teile) und `PLACE` (id → Gruppe,
Teil) in main.gd; `_order_controls()` sortiert `controls` und setzt `extra.sub` / `extra.icon` (extra wird kopiert – mehrere
Controls teilen sich `ex`). Fenster: `UI.fold_card(..., icon)`, `UI.sub_fold()`, `sub_bodies`, `ui_items[4]` = Teil. Motion Watch
(ab 2.93.12) zeigt `icon` vor dem Gruppennamen und `sub` als Zwischentitel. Test-Aktion `ui_scroll` (fold, simple, y).

**3D-3.4 – Ort von der Karte:** `geo.gd` (Download mit Cache `user://orte/cache/<md5>.bin`, Kacheln WMTS 3857 swisstopo,
Terrarium-PNG, Overpass `out geom`, swisstopo profile.json 81 × 81 Punkte = swissALTI3D; lokale Koordinaten: Mercator × cos(lat),
Norden = -z; `height()`, Gebäude extrudiert mit Satteldach über dem kleinsten Rechteck, Fassaden-Shader `facade.gdshader`,
Bäume: nahe echte `tree()` (max. 380), sonst MultiMesh, Wald aus dem Luftbild bis 1.1 km), `karte.gd` (Kartenfenster, Suche über
SearchServer), Szene «ort» in scenes.gd, `main.terrain` / `ground_y()` / `ground_hit()` (Besucher, Platzieren, Sichtlinie mit
Gelände). Testen ohne Internet: `MW3D_GEO_BASE=http://127.0.0.1:8899` + Ersatz-Server (Host = erster Ordner). Test-Aktionen `geo`,
`map`. Nicht getestet: echte Server (aus der Testumgebung nicht erreichbar). Update: `_download_check` mit bis zu 3 Versuchen,
`.old2` usw. wenn `.old` gesperrt. Jogger: längere Schritte statt schnellerer Beine.

**3D-3.3 – Schatten:** `env.ambient_light_source` = COLOR (statt SKY: im Compatibility-Renderer lieferte der Himmel auf manchen
Grafikkarten kein Umgebungslicht → schwarze Schatten), Farbe/Stärke in `_update_sky()`; `sun.shadow_blur`, soft_shadow_filter_quality 3.
Test-Aktion `view` (pos, look, panel) für Bildschirmfotos.

**3D-3.2 – Fahne erobern:** `game_goal` «flag» (`flag_mode()`, nicht mit «teamguard»), `bases`, `flags` (Fahne mit
`scenes.cloth`, folgt dem Träger in `_flags_follow`), `_flag_rules()` (holen, heimbringen +500, abklatschen +100), `captures`.
Start an der eigenen Basis (`start_point`). Handy: `caps`, `flag`, Pfeil zum jeweiligen Ziel.

**3D-3.1 – Räuber/Wächter, Zelle, Team-Ziel:** `game_mode` «teamguard» (`team_mode()`, `guard_team`, `match_round`,
`match_scores`; Rollen über `_assign()`), erster Wächter = Kopf (`guard_player()`), weitere = feste Kamera (`guard_cam()`,
`guard2_watching()`, `main._wanted_fps(1)`). `game_rescue`: Zustand «jail» bei `jail` (`_build_jail`), Befreien im Referee
(1,6 m, +100 `bonus`). `game_teamgoal`: `goal_open()`, Strahl rot/grün (`_paint_goal`). Ablenkung `distract` / `_check_distract()`.

**3D-3.0 – Teams:** `main.game_teams`; Spieler `team`, `look` (`_clean_look`, `actor.look`), `cone` (Teamfarbe `_paint_cone`),
`_rebuild()` (neues Aussehen = neue Figur), `_make_actor()`. Nachrichten `team`, `look`, `sig` (`_signal`: Label3D über dem Kopf,
Ebene 16, an Teamkollegen `{"t":"sig", n, c, k, txt, ga, d}`). `team_results` in `st` als `tres`. Tarnung: KI-Erkennung × 0,8
bei Tag (nicht Parkplatz). Handy: `ov()` zeichnet nur bei Änderung neu (vorher 5×/s → Knöpfe konnten Klicks verlieren).

**3D-2.9 – Welt:** `scenes.cloth()` (Shader `cloth.gdshader`, Wind über `main.cloth_mats`), `flag()`, `laundry()`, `smoke()`
(CPUParticles, Gruppe «smoke»), `main._build_fireflies()`. Schalter `world_cloth`, `world_smoke`, `world_fireflies`.
**Wichtig:** Der Linsen-Shader las in 3D-2.6 das Bild über `hint_screen_texture` – diese Kopie enthält nur Undurchsichtiges, darum
fehlten Regen, Rauch usw. im Kamerabild. Jetzt: Belichtung über ein eigenes Quad mit `blend_mul` (`expo.gdshader`, `expo_mats`),
Farbe nachts über Kopien der Umgebung mit `adjustment_saturation` (`night_envs`: 0 = Infrarot, 0,4 = wenig Licht), Körnung/Tropfen
wieder als durchsichtige Überlagerung. Test-Abfrage `world`.

**3D-2.8 – Tiere:** `_build_animal()` mit Brust/Hinterteil (`bulk`), dunklerem Rücken, Oberschenkeln, Hals, Fuchs-Kinn und
Ohrspitzen, Schlappohren (Hund 50 %), runden Ohren (Wildschwein, Dachs). Menschen an der Tür: `_at_door()` → Arm zur Klinke.

**3D-2.7 – Figuren:** `actor._build_person()` mit Gelenken `hips` und `torso` (gegengleiches Schwingen in `_animate_person`),
Gesicht, Statur (`body_root.scale` nicht gleichmässig), Kapuze/Handschuhe, Lampe (`lamp`, `lamp_mat`, Anteil `main.lamp_share`).
Leerlauf-Arten pro Tier (`idle_kind`: graze, root, sniff, sit_up, sit, look, phone, bend), `startle()` beim Licht,
`play_emote()` für Spieler (caught, goal, throw). Reh springt auf der Flucht (`leap`), Hase hoppelt.
Zwischenversionen: `/tmp`-Skript `release.sh` (nicht im Repo): Version setzen, exportieren, ZIP, version.json, MW-Version, signieren.

**3D-2.6 – Nacht, Testlauf, Geräusche:**
- **Belichtung im Linsen-Shader:** Der Kompatibilitäts-Renderer ignoriert `CameraAttributesPractical.exposure_multiplier`
  (gemessen: Nachtbild gleich hell bei Verstärkung 1 und 8). Darum liest `lens.gdshader` das Bild (`hint_screen_texture`)
  und multipliziert nachts mit `expo = NIGHT_SCALE (0,15) × gain` (gain ≤ `night_gain`), `grey` = 1 bei IR, 0,6 nachts.
  Tags `expo = 1` (Bild unverändert, gemessen). IR-Licht `spot_range = ir_range`, `main.ir_on()` (MW oder Spiel-Wächter).
- **Motion Watch 2.93.3** schickt in `sim_state()["det"]` `persons`, `present`, `armed`, `noise`; der Simulator speichert
  `main.mw_det`. Der Simulator schickt in der `/state`-Antwort `sound_db` (`main.sound_db()`: Grundpegel, Regen, Wind,
  `sounds` aus `_update_sounds()` und `add_sound()`); Motion Watch füttert damit `AudioMonitor.feed_sim()` (nur ohne
  echtes Mikrofon) → normaler Geräuschalarm.
- **Testlauf** `scripts/testrun.gd`: `PHASES`, Wahrheit `visible()` (Kopf- oder feste Kamera, frei, ≥ 30 px Person /
  18 px Tier, Licht ≥ 0,25 über `game.light_at`), lockerer `present()` für Fehlalarme. Bericht JSON + HTML in
  `user://testlauf/`, CONTROL `test_report`. Geprüft mit einem nachgebauten Motion-Watch-Client (bekannte Meldungen):
  Erkennungen, Reaktionszeit, Fehlalarme und Ursachen stimmen. Mit dem echten Motion Watch hier: Tiere als Bewegung
  gemeldet, Personen 0 (KI-Modell in dieser Umgebung nicht ladbar).
- **Spiel:** `game_mode` «mw» (`_mw_referee`: Personenmeldung → sichtbarster Spieler), `game_goal` «return» (Beute).
- **Wolkenschatten** `cloud_shade()`, **Böen** `gust()`, Menschen schauen zum Licht (`look_at_light`).
- **Bedienfeld:** Schalter = Label (Umbruch) + CheckButton, Knöpfe `autowrap_mode`, Auswahl mit Label darüber und
  `fit_to_longest_item = false`. Test-Abfrage `ui_width` (Mindestbreite des Inhalts vs. Platz; jetzt 341 von 376 px).

**3D-2.5 – Realismus und Spiel:** Kamerabild: `shaders/lens.gdshader` auf einem Quad 12 cm vor Kamera 0/1 (eigene Ebenen 32/64,
`cull_mask` der Kameras), Rauschen aus `gain[i]` (Belichtung), Vignette, Regentropfen; Insekten = `CPUParticles3D` am
`head_pitch` (nachts, wenn Licht an). Einstellungen Gruppe «Kamerabild» (`lens_noise`, `lens_vignette`, `lens_drops`, `insects_on`).
Schiedsrichter `game.cam_sees()`: Personenhöhe in Pixeln (`VFOV`, Bildzeilen) → KI `smoothstep(18, 70 px)` × Haltung × Licht;
Bewegung = Pixel pro Sekunde × Grösse (ab 20 px); Wärmebild = Fleck ab 2,5–9 px × Temperaturunterschied; Licht `light_at()`
(Lampen `main.lamps`, weisses Licht/IR im Bildausschnitt des Kopfes, Mond). Unter 0,1 zählt nichts. Mikrofon `hearing()`.
Start bei z = −46 (dort sieht keine Kamera genug). Spielart `game_mode` «guard»: Wächter-Handy bekommt `main.latest_jpg(0)`
(`_send_guard_view`, `main._wanted_fps(0)` ≥ 8), steuert `guard_yaw/guard_tilt`, Nachrichten `light`, `catch`, `role`;
`stone` für Steine (Aufmerksamkeit `attention`), Kristalle `items`, Leben `game_lives` (Zustand «out» = Zuschauer),
Sichtkegel `cones` (Ebene 16), zufälliger Start/Ziel. Rangliste mit Wächter-Punkten (150 je Fang, −50 Fehlalarm, +100 je
Schleicher nicht im Ziel). Test-Abfrage `game` liefert auch `cams` (pro Kamera Abstand, im Bild, Verdecker, Sicherheit), `items`.

**3D-2.4 – Spiel «Unentdeckt ans Ziel»** (`scripts/game.gd`, `scripts/qr.gd`): bis 4 Handys. HTTP-Seite (`PAGE`, in game.gd
eingebettet) auf Port `stream_port + 5` (8770), WebSocket auf `+ 6` (8771, `WebSocketPeer.accept_stream`). Nachrichten: Handy →
`join {name, token}` (token in localStorage: gleicher Platz nach Neuladen), `in {mx, my, look, pitch, run, pos}` (alle 50 ms),
`frame` (nächstes Bild, Flusskontrolle), `start`. Simulator → `hello`, `st` (5×/s: Entdeckt-Wert, Ziel-Richtung, Runde, Liste,
Rangliste), `ev caught`, Bilder als binäre JPEG. Jeder Spieler hat eine eigene SubViewport-Kamera hinter seiner Figur
(`cull_mask 1|16`; Ebene 16 = nur für Spieler: Zielstrahl, farbige Kegel), Belichtung wie ein Handy (`_exposure`).
Figur = `actor.gd` mit `controlled` (`_player()`: Joystick, Rennen, Ducken, Kriechen = `prone`). **Schiedsrichter**
(`visibility()`, alle 0,2 s): pro Kamera (Kopf, fest, Wärmebild) Reichweite, Bildausschnitt (`is_position_in_frustum`), Sicht
(`main.line_free()` zum Scheitel; Hindernisse haben Höhen `ht`, `set_obstacle_height()` in scenes.gd, Zaun/Hecke 1,2 m, dünne
Kreise < 0,45 m zählen nicht), × Abstand × Haltung × Bewegung × Licht (Nacht: 0,12; IR nur Kopf 0,75; weisses Licht) × Wetter;
Wärmebild × Temperaturunterschied. Wert × 55/s × Stufe → 100 = erwischt (Blitzlicht, zurück zum Start, 3 s Schutz).
Ohne Motion Watch (`guard_auto`) dreht `game.guard_yaw` den Kopf. Test-Abfragen `{"action":"game"}`, `{"action":"game_put"}`.
Gemessen unter Xvfb/llvmpipe: Handybilder nur ~2/s (CPU-Grafik); auf echter Grafikkarte nicht getestet.

**3D-2.3 – Strom sparen:** `main._check_active()` (alle 0,5 s): `win_open` = nicht Kästchen (`mini.gd`) und nicht minimiert;
`connected()` = senden an und Motion Watch hat in den letzten 10 s `/state` geschickt oder Bilder/Wärmebild geholt. Weder noch
(und `eco_idle` an) → `sim_active = false`: `_process` endet nach dem langsamen Teil (Status, Speichern, Updates), Besucher
`PROCESS_MODE_DISABLED`, keine Aufnahmen, `Engine.max_fps = 5` (net.gd antwortet weiter und weckt ihn so). Kästchen mit Motion
Watch: `get_viewport().disable_3d = true` (grosse Ansicht aus), `max_fps = 30`, Vorschaubilder nur bei offenem Fenster.
**CPU im Kästchen:** Motion Watch misst mit psutil (`SysMonitor._shares`: eigener Prozess und – wenn der Simulator auf demselben
Rechner läuft – dessen Prozess über `pid` aus der `/state`-Antwort, Name muss «motionwatch3d» enthalten), Werte in % des ganzen
Rechners, und schickt sie in `sim_state()["cpu"] = {"total", "mw", "sim"}`. `sim` = None → Motion Watch läuft woanders (Pi).
Gemessen unter Linux/llvmpipe: Fenster 170 %, Kästchen mit MW 135 %, Pause 7 % eines Kerns.

**3D-2.2 – Start mit dem PC** (Simulator-Chat; baut auf 3D-2.1 des Haupt-Chats mit `mini.gd` auf) (`scripts/autostart.gd`): Windows-Wert `MotionWatch3D` unter
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (über `reg.exe`, kein Admin), Linux `~/.config/autostart/motionwatch3d.desktop`.
Startet mit `--autostart`: senden an, Szene vom letzten Mal (`last_scene`), kein Update-Dialog (ausser `auto_update`),
optional minimiert (`autostart_min` → `mini.gd` macht daraus das Kästchen), Motion Watch auf dem PC (`autostart_mwpc`), Bildschirm sperren (`autostart_lock`,
`rundll32 user32.dll,LockWorkStation`). **Minimiert zeichnet Godot nichts mehr** (`can_any_window_draw`) – die Kamerabilder
blieben stehen (getestet). Darum ruft `_process` dann 15× pro Sekunde `RenderingServer.force_draw(false)` (getestet mit einem
kleinen Fenstermanager unter Xvfb: Bilder laufen weiter) – Sicherheitsnetz neben dem Kästchen von `mini.gd`. «Ohne Anmelden»: echter Start vor der Anmeldung geht mit 3D nicht
(Sitzung 0 ohne Desktop/GPU), darum Sysinternals **Autologon** (Download mit curl.exe, `OS.shell_open` → UAC; Passwort
nur dort, LSA-verschlüsselt) + Sperren nach dem Start. Test-Abfrage `{"action":"window"}` (Fenstermodus, Autostart).

**Neue Einstellungen kommen von selbst in Motion Watch:** Jede Einstellung, die mit `add_control()` in `_register_controls()`
angemeldet wird, liefert der Simulator über `GET /control` mit. Die Webseite von Motion Watch fragt alle 4 s nach und baut die
Steuerung neu auf, sobald sich die Liste ändert (ab 2.92.3 bleiben offene Gruppen dabei offen). **In Motion Watch muss für neue
Simulator-Einstellungen nichts geändert werden** – nur die Typen `toggle`, `slider`, `select`, `button` (sonst Textfeld) benutzen.
`"expert": true` blendet nur im Simulator-Fenster aus. Das Desktop-Fenster von Motion Watch hat keine Simulator-Steuerung.

**3D-2.0 (grosses Update):**
- **Hindernisse** (`main.gd`, Abschnitt «obstacles»): Kreise (`add_obstacle`) und gedrehte Rechtecke (`add_obstacle_box`,
  `add_obstacle_node` im Rahmen eines Szenen-Knotens) in einem 4-m-Raster (`ob_grid`). `people_only` = Zäune/Hecke im Garten
  (Tiere schlüpfen durch). Jede Szene meldet ihre Objekte an (Bäume über `scenes.tree()`). `avoid()` biegt die Richtung um
  Hindernisse und gibt die gewählte Seite zurück (der Besucher hält sie 2,5 s, sonst pendelt er an Ecken), `keep_out()`
  schiebt nach jedem Schritt aus allen Objekten heraus. Getestet: Besucher quer durch Wohnwagen und Zelt geschickt –
  tiefste Annäherung 0,0 m, alle kamen ans Ziel.
- **Besucher** (`actor.gd` neu): Trägheit (`cur_speed`, `heading`, `_turn()`), Grasen/Umschauen (`idle_until`), Kopf- und
  Schwanz-Gelenke, Kniegelenke bei Menschen, festhängen → Umweg (`detour_until`). Neue Arten: child, jogger (Varianten von
  person), hare, hedgehog; Spaziergang mit Hund (`leader`), Rudel (`visit("herd")`), Garten-Besuch durchs Tor
  (`scenes.garden_route`). Vorschau-Modus `preview` für die Bildchen.
- **Szenen**: feinere Objekte (Wohnwagen mit Markise/Deichsel/Gasflasche, Zelt mit Aussenzelt, Velo mit Speichen, Hütte mit
  Brettern/Kamin/Holzstapel, Haus mit Fensterrahmen/Kamin, Autos mit Scheiben, Teich mit Schilf, Farne, Heu), Gras und Blumen
  als MultiMesh (`scenes.meadow()`, abschaltbar), **6 gemeinsame Laub-Materialien** statt eines pro Baum (schneller).
- **Bedienfeld**: Werkzeugleiste wie Motion Watch (`UI.icon_button` mit gezeichneten Symbolen, `UI.search_field`),
  Suche (`_search`), «nur Gruppen / alle auf / alle zu» (`_fold_all`), «Einfach | Experte» (`UI.segment`, `ui_simple`;
  Regler mit `"expert": true` im extra), Karte «Besucher hinsetzen» mit gerenderten Bildchen (`_make_thumbs` in eigener
  kleiner Welt) – anklicken oder ziehen (`set_drag_forwarding`, abgelegt über `NOTIFICATION_DRAG_END`). Schalter als
  CheckButton. Einstellungen in `KEEP` werden gespeichert (`simulator_settings.json`).
- **Neue Regler** (Gruppe Besuch): Wer kommt (`mix`), Wie oft (`visit_rate`), Höchstens (`max_visitors`), Tempo
  (`visitor_speed`), Flucht vor Licht/Sirene, Ausweichen; «Alle Besucher weg»; Grafik: Gras und Blumen.
- **Servos** drehen mit `SERVO_DEG_S` (200 °/s) statt zu springen; ab und zu ein Vogelschwarm (`_birds`).
- **Test-Abfragen** im CONTROL-Protokoll (nur für Tests, von der Webseite nicht benutzt): `{"action":"visitors"}` (Ort und
  Abstand zum nächsten Objekt jedes Besuchers), `{"action":"spawn_at","kind","from":[x,z],"to":[x,z],"wait":s}`.

Ab 3D-1.13 **Updates aus der Ferne**: Schalter `auto_update` (gespeichert in `user://simulator_settings.json`, auch als
CONTROL-Regler auf der Motion-Watch-Webseite) prüft alle 10 Minuten still (`Updater.quiet`) und installiert nach 15 s Countdown
(`Updater.auto`, «Abbrechen» möglich; bei Fehlern geht es nach 20 s von selbst weiter). Knopf `update_now` (CONTROL) löst das
sofort aus. Neustart-Optionen aus `main.restart_args()`: bisherige Optionen plus `--stream`, `--scene <aktuell>`, `--mwpc`
(startet «Motion Watch auf diesem PC» wieder). Der Status zeigt «Update: …».
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
- Die Bildrate der neuen Szenen auf dem alten i5 (Wald hat rund 300 Bäume; ab 3D-2.0 mit gemeinsamen Materialien).
- Ziehen der Besucher-Bildchen mit der echten Maus unter Windows (hier mit XTest getestet).
- Die echte Erkennungsquote von Motion Watch im Testlauf (hier ohne KI-Modell) und der Geräuschalarm mit simuliertem Pegel
  auf dem Pi.
- Das Spiel mit echten Handys im WLAN und unter Windows (hier nur mit Chromium-Handy-Nachbildung und Tastatur),
  die Bildrate der Handybilder auf einer echten Grafikkarte, Vibration, Vollbild/Querformat-Sperre auf iPhone.
- Autostart unter Windows (Registry-Eintrag, minimiert weiterzeichnen mit Direct3D/ANGLE, Sperren, Autologon) – nur unter Linux
  getestet (Autostart-Datei, minimiert weiterzeichnen).
- Das Selbst-Update unter Windows (Umbenennen der laufenden .exe, HTTPS zu GitHub) – hier nur unter Linux mit lokalem Server.
- Das Zielen mit der echten Maus (hier nur mit dem Knopf «Schuss aus der Kopfkamera» getestet).

## Testwerkzeuge in dieser Umgebung (nur als Hinweis, liegen nicht im Repo)

- Godot 4.3 von GitHub (Releases 4.3-stable, Linux-Programm + Export-Templates nach `~/.local/share/godot/export_templates/4.3.stable`).
- Projekt direkt im geklonten Repository (`simulator3d/`); `.godot/` ist in .gitignore.
- Start auf virtuellem Bildschirm und HTTP-Abfragen über kleine Hilfsskripte.
## Achtung: Zwei Chats ändern Motion Watch (Stand 26.10.2026, 19:30)

Neben dem Simulator-Chat ändert auch der Haupt-Chat `webcam_bewegung_*.py`. Am 26.10. haben beide eine eigene «2.91.0» gebaut,
und Änderungen gingen verloren (Push-Fehler wurden nicht bemerkt). Der Haupt-Chat hat das in **2.92.0** zusammengeführt:
Stand 2.91.0 dieses Chats + WLAN-Stick-Korrektur + Reiter «Simulator» (Seite `/sim`, `SIM_PAGE`).

Darum vor **jeder** Änderung an Motion Watch:
1. `git pull` und von der neuesten `webcam_bewegung_*.py` auf GitHub ausgehen.
2. Eine Versionsnummer wählen, die höher ist als die neueste auf GitHub.
3. Nach `git push` prüfen, dass er geklappt hat (`git status -sb` darf kein «ahead» zeigen). Bei Fehler: zuerst holen und zusammenführen, nie überschreiben.
