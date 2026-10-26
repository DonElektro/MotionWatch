# Motion Watch Simulator

A simulated world for Motion Watch: camera on a pan / tilt head, servos, Thermal-90 thermal camera, PIR / door / gas
sensors, people, animals, cars, planes, weather, day and night. Test Motion Watch before the hardware arrives.

**Motion Watch is not part of the simulator.** It runs as its own program – on the Pi or on any PC in the same network –
and talks to the simulator over the network (simulator protocol 1, port **8767** – the 3D simulator has 8765). The rules
for every Motion Watch simulator: `simulator/hardware/EIGENEN_SIMULATOR_ANBINDEN.md`.

Name in the network: **«Python-Weltsimulator 1.0»**, version **PY-1.0**.

| Motion Watch … | … the simulator |
|---|---|
| finds the simulator in the network | announces itself every 2 s (UDP port 8764) – only while **📡 Send to Motion Watch** is on |
| reads the camera picture `http://<PC>:8767/cam/0/video.mjpg` (`?fps=6` = fewer pictures; cam 1 = a fixed camera) | renders what the head camera sees right now |
| reads the thermal picture `/thermal.bin` | renders an 80 × 62 picture in °C: people ~30–34 °C, cool ground, cold sky |
| reads sensor events `/events` | sends «PIR» when somebody comes near the box, door / gas from the buttons |
| sends its servo, light and relay positions `POST /state` | turns the head – only as far and as fast as real servos (120 °/s) – and switches the lights; a siren makes animals run away |
| shows the simulator's controls on its web page (`GET` / `POST /control`) | scenario (map), place, time, weather, wind, visitors, faults, door / gas |
| shows what it sees on its web page `/api/state` | reads it for the scoreboard and the automatic tests |

## Start

1. Python 3.10 or newer must be installed (Windows: python.org, tick "Add python.exe to PATH").
2. Double-click **`START SIMULATOR.bat`** (the first start installs opencv-python, numpy and pillow by itself) – or:

```bash
python motion_sim.py
```

3. Switch **📡 Send to Motion Watch** on (top right) – the simulator starts silent.
4. In Motion Watch: tab **«Simulator» → «Simulatoren im Netz»** → «Python-Weltsimulator 1.0» → **«Verwenden»** →
   **«Simulation einschalten»**. The Windows firewall must allow port 8767 («Private Netzwerke»).
   The simulator finds Motion Watch's web page by itself (the device that sends its state, port 5000), or enter it in
   tab **🔗 Motion Watch**.

First a **start window** opens: pick the map, tick which places exist (Region map – a live preview shows how they fit
together) and what is drawn (trees, buildings, small things, the mountain behind the world, shadows, background
traffic), quality, light and how many people walk through. Everything can be changed later in the 🗺 World tab.

## The folder

| | |
|---|---|
| `START SIMULATOR.bat` | double-click to start |
| `INSTALL.bat`, `requirements.txt` | Python packages (START does it by itself too) |
| `motion_sim.py` | the launcher (options below) |
| `make_package.py` | builds `MotionWatchSimulator.zip` to send to somebody (without `data/`) + `MotionWatchSimulator.json` (version, size, checksum) |
| `my_maps/` | maps you saved in the map editor |
| `data/` | what the simulator remembers (start window choices) |
| `simulator/` | `hardware/` protocol server, `scene/` world and maps, `graphics/` pictures, `ui/` the window, `checks/` tests + scoreboard, `bridge.py` the link to Motion Watch's web page |

## The window

* **📍 Place** (top bar) – ready-made viewpoints on every map. **📷 Move camera** – click on the map where the camera
  should stand, drag to turn it. Box **③** under the map: arrow buttons (10 m steps, turn 15°, higher / lower).
* **Map (from above)** / **3D map editor** – box **①**: pick 🚶 🐕 🐈 🐻 🦌 🐑 🐦 🚗 🚚 🚲 🏍 and click a spot: it walks in
  from outside the picture, reaches the spot and walks away again. Box **②**: ✋ move, 🗑 delete, 🌳 🌿 🏠 place things,
  💾 save as own map.
* **▶ Live** – camera + thermal picture, Motion Watch's state, Arm / Disarm / web page, and the **scoreboard**: persons
  really in view vs. reported, detection rate and delay, false alarms (with cause), tracking error, recordings.
* **👥 People** – one slider per kind = how many keep coming through; behaviour, speed, pause, time speed.
* **🗺 World** – maps (Region with touching places, Valley, camp, garden, parking, forest, lakeside, winter + your own),
  places, what is drawn, time of day, clouds, rain, fog, wind, temperature.
* **📷 Camera** – resolution, fps, field of view, noise, exposure; where the head stands; servo travel (180° / 270° /
  360°), bracket stop, speed, jitter, reversed, stuck, power; faults: cable pulled, frozen picture, lens covered, dew.
* **🌡 Thermal** – thermal camera plugged in, hot stone, camp fire.
* **🔗 Motion Watch** – the simulator's addresses, Motion Watch's web page (address, password), what it sends.
* **✅ Tests** (18 automatic checks), **📜 Log**, **❓ Help**. **Quality** slider and **📡 Send to Motion Watch** top right.

## Options

```bash
python motion_sim.py --map valley --hour 22 --people 3
```

```bash
python motion_sim.py --mw 192.168.1.50:5000 --mw-password secret
```

```bash
python motion_sim.py --no-panel --run-tests all --report results.txt --exit-after-tests
```

```bash
python motion_sim.py --stream
```

`--stream` announces to Motion Watch at once. `--protocol-port` changes port 8767, `--name` the name Motion Watch shows
(must be unique). `--run-tests` announces at once, waits until Motion Watch is connected, then runs the tests.

## Good to know

* The picture starts at 13:00 (daylight). Real time: tab 🗺 World → "real clock".
* The servos only move where Motion Watch sends them, as fast as the speed allows, never past their travel or the
  bracket stop. Nobody connected = the head stays in the middle.
* Motion Watch's AI works on the simulated picture as on the Pi – it needs its model files.
* While the simulation is on, Motion Watch saves no recordings or timelapses (so nothing mixes with real clips) – the
  tests skip «recording started» then.
* GitHub project of Motion Watch: `DonElektro/MotionWatch`. Never change `webcam_bewegung_*.py`, `versions.json`,
  `simulator3d/` or `simulator/` there; wishes for Motion Watch go through Daniel. No passwords or keys in a repository.
* Moving the camera rebuilds the static scene in the background for a few seconds (big city: a bit longer).
