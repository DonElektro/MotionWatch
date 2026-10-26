#!/usr/bin/env python3
"""
Motion Watch simulator - the world only
=======================================
Simulates what Motion Watch's hardware would see and do, on a normal PC:

  * camera on a pan / tilt head + a fixed camera, as MJPEG streams
  * two servos - they turn only as far and as fast as real servos (180 / 270 / 360 degrees)
  * Waveshare Thermal-90 thermal camera (degrees C), a PIR sensor, door / gas sensors
  * people, animals, cars, planes, weather, day / night, faults, many maps + your own maps (3D map editor)
  * a scoreboard (what is really there vs. what Motion Watch reports) and automatic tests

Motion Watch is NOT part of the simulator. It runs as its own program - on the Pi or on any PC - and talks to the
simulator over the network (simulator protocol 1, port 8767 - the 3D simulator has 8765):
  the simulator announces itself in the network (UDP port 8764) once «Send to Motion Watch» is on;
  Motion Watch reads the camera / thermal pictures and sends its servo, light and relay positions (POST /state);
  Motion Watch's web page remote-controls the simulator (GET / POST /control);
  the simulator reads Motion Watch's web page (/api/state) for the scoreboard and the tests.
Details: simulator/hardware/EIGENEN_SIMULATOR_ANBINDEN.md

  python motion_sim.py                          start the simulator window (silent until «Send to Motion Watch»)
  python motion_sim.py --stream                 announce to Motion Watch at once
  python motion_sim.py --map forest             start on another map
  python motion_sim.py --mw 192.168.1.50:5000   Motion Watch's web page (default: found by itself)
"""
import argparse
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MAPS_DIR = os.path.join(HERE, "my_maps")             # maps saved in the map editor
DATA_DIR = os.path.join(HERE, "data")                # what the simulator remembers (start window choices)


def quit_all(code=0):
    os._exit(code)


def main():
    ap = argparse.ArgumentParser(description="Motion Watch simulator (the world only - Motion Watch connects over the network)")
    ap.add_argument("--map", default=None, help="region (default) | valley | camp | garden | parking | forest | lake | winter | my_<own map>")
    ap.add_argument("--protocol-port", type=int, default=8767,
                    help="port of the simulator protocol (Motion Watch connects here; 8765 belongs to the 3D simulator)")
    ap.add_argument("--stream", action="store_true", help="«Send to Motion Watch» on at once: announce this simulator in the network")
    ap.add_argument("--name", default="", help="the name Motion Watch shows for this simulator (must be unique in the network)")
    ap.add_argument("--mw", default="", metavar="ADDRESS", help="Motion Watch's web page, e.g. 192.168.1.50:5000 (default: the device that connects)")
    ap.add_argument("--mw-password", default=os.environ.get("MOTIONWATCH_PASSWORD", ""), help="Motion Watch's web password, if it has one")
    ap.add_argument("--hour", type=float, default=None, help="start with this time of day (slider mode)")
    ap.add_argument("--people", type=int, default=None, help="how many people keep walking through")
    ap.add_argument("--run-tests", default="", metavar="all|walker,car,…", help="run test scenarios as soon as Motion Watch is connected")
    ap.add_argument("--report", default="", metavar="FILE", help="write the test results to this file (text)")
    ap.add_argument("--exit-after-tests", action="store_true", help="quit when the tests are done (exit code 1 if one failed)")
    ap.add_argument("--no-panel", action="store_true", help="no simulator window")
    ap.add_argument("--no-start-window", action="store_true", help="start at once, without the start window")
    ap.add_argument("--start-window", action="store_true", help="show the start window even if it was switched off")
    a = ap.parse_args()

    from simulator import bridge
    from simulator.scene import maps
    from simulator.config import SIM
    from simulator.engine import Engine
    from simulator.checks.scenarios import Runner
    from simulator.checks.scoreboard import Scoreboard

    maps.load_custom(MAPS_DIR)
    # ---- start window: map, places, what is drawn (remembered in data/start_choices.json) ----
    from simulator.ui import start as startwin
    choices = os.path.join(DATA_DIR, "start_choices.json")
    saved = startwin.load(choices)
    startwin.apply(saved)
    map_name = a.map or saved.get("map") or "region"
    if map_name not in maps.MAPS:
        map_name = "region"
    show = (a.start_window or SIM["start_window"]) and not (a.no_start_window or a.no_panel or a.run_tests)
    if show:
        chosen = startwin.ask(choices, map_name)
        if chosen is None:
            print("[SIM] start window closed - nothing started")
            return
        map_name = chosen
    if a.hour is not None:
        SIM.update(time_mode="manual", hour=a.hour)
    if a.people is not None:
        SIM.want("person", a.people)

    eng = Engine()
    eng.scoreboard = Scoreboard()
    m = maps.get(map_name)
    p0 = maps.pois(m)[0]                                 # the first place of the map = where the camera starts
    SIM.update(cam_x=p0["x"], cam_y=p0["y"], mount_height=p0["h"], mount_yaw=p0["yaw"], mount_pitch=p0["pitch"])
    if m.ambient is not None:
        SIM["ambient_c"] = m.ambient
    eng.world.set_map(m.name)
    eng.renderer.map = m
    eng.renderer.pano_pos = (SIM["cam_x"], SIM["cam_y"])
    from simulator.graphics import render
    render.set_quality(SIM["quality"])
    print(f"[SIM] map: {m.label} - building the picture …")
    eng.renderer.ensure(SIM["cam_width"], SIM["cam_height"], SIM["cam_hfov"], SIM["mount_height"])
    eng.start()
    runner = Runner(eng)

    from simulator import NAME
    from simulator.hardware.protocol import ProtocolServer, lan_ip
    SIM["stream"] = bool(a.stream or a.run_tests)        # tests need Motion Watch: announce at once
    proto = ProtocolServer(eng, a.protocol_port, name=a.name or NAME).start()
    bridge.configure(a.mw, a.mw_password)
    bridge.start()
    ip = lan_ip()
    print(f"[SIM] «{proto.name}» ready on http://{ip}:{a.protocol_port}/")
    print("[SIM]   " + ("announced in the network - in Motion Watch: tab «Simulator» - «Simulatoren im Netz» - «Verwenden»"
                        if SIM["stream"] else "silent until you switch «Send to Motion Watch» on (or start with --stream)"))
    print("[SIM]   waiting for Motion Watch " + (f"at {bridge.address()}" if bridge.address() else "(it connects by itself)"))

    if a.run_tests:
        threading.Thread(target=auto_tests, args=(a, runner), daemon=True, name="sim-autotest").start()

    if a.no_panel:
        while True:
            time.sleep(1.0)
    import tkinter as tk
    from simulator.ui.panel import Panel
    root = tk.Tk()
    Panel(root, eng, runner, proto, a, own_root=True)
    root.protocol("WM_DELETE_WINDOW", lambda: quit_all(0))
    root.mainloop()
    quit_all(0)


def auto_tests(a, runner):
    """--run-tests: wait for Motion Watch, run the scenarios, write / print the results."""
    from simulator import bridge
    from simulator.checks.scenarios import SCENARIOS
    t0 = time.time()
    while not bridge.ready():
        if time.time() - t0 > 600:
            print("[SIM] no Motion Watch connected within 10 minutes - tests not run:", bridge.status())
            if a.exit_after_tests:
                quit_all(2)
            return
        time.sleep(0.5)
    print(f"[SIM] Motion Watch connected ({bridge.address()}) - letting it settle …")
    time.sleep(15.0)                                  # camera opened, background learnt, auto-tune done
    keys = [s[0] for s in SCENARIOS] if a.run_tests == "all" else [k.strip() for k in a.run_tests.split(",") if k.strip()]
    print(f"[SIM] running tests: {', '.join(keys)}")
    runner.run(keys)
    time.sleep(1.0)
    while runner.busy():
        time.sleep(1.0)
    lines, failed = [], 0
    for _k, label, res, status in runner.history:
        failed += status in ("FAIL", "ERROR")
        lines.append(f"{status:7} {label}")
        for r in res:
            lines.append(f"          {r['status']:5} {r['label']}" + (f"  ({r['detail'].strip()})" if r["detail"] else ""))
    text = "\n".join(lines) + f"\n\n{len(runner.history) - failed} of {len(runner.history)} tests passed\n"
    print(text)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(text)
    if a.exit_after_tests:
        quit_all(1 if failed else 0)


if __name__ == "__main__":
    main()
