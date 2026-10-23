#!/usr/bin/env python3
"""
Motion Watch 1.4.0  -  Webcam motion / person detection with weather awareness,
                       pan/tilt servos, pendulum patrol, AI verification & relay
===============================================================================
Features
  * USB-webcam motion detection (OpenCV MOG2 + temporal filtering)
  * Person highlighting in RED (tinted silhouette + box + track line)
  * Rain detection  -> automatic "Rain Mode" (stronger filtering, sees through rain)
  * Wind detection  -> background vegetation motion raises the trigger threshold
  * Walking recognition: an object must move with a steady speed for N frames
  * Car / vehicle filter: wide, fast or huge objects are ignored
  * Auto-tune: calibrates thresholds on start and keeps adjusting them
  * AI person detection (SSD MobileNet V2 via OpenCV DNN) - optional, verifies
    motion detections and also finds standing persons
  * Pan/Tilt servos (GPIO 17 / 27, 500-2500 us) with manual sliders, automatic
    person tracking (keeps the person centred) and a pendulum patrol over
    waypoints (1-2-3-2-1 ...), all in background threads
  * Relays (GPIO 22 + any free GPIO): Off / On / Auto (person, motion, animal, cat, dog, car, ...)
  * Clip recording while a person is present
  * Object marking: every COCO object the AI network knows (cars, animals, bags, ...) gets a labelled box
  * Live CPU load (+ temperature) with 60 s history graph in the desktop app and the web page
  * Native desktop app (Tkinter) + web page (Flask, port 5000) with live stream, pan/tilt pad,
    all settings, snapshot, CPU graph and event log  ->  http://<pi-ip>:5000/
  * 1.2.2: settings + waypoints persist (motionwatch_settings.json), recordings at real FPS,
    automatic cleanup of old recordings (size limit), snapshot JPG per detection, camera
    auto-reconnect, low-light mode (CLAHE), webhook alarm (Home Assistant / ntfy / IFTTT),
    web JPEG only encoded while a viewer is connected, headless without Tkinter, log file
  * 1.2.2: fullscreen (F11 / Esc, double-click video = video only), light / dark theme,
    German / English language switch - desktop window and web page
  * 1.2.3: camera moves with the arrow keys and an on-screen direction pad (press and hold) in the
    desktop window, like on the web page; manual moves pause tracking / patrol for a few seconds
  * 1.2.3: every badge, statistic tile, panel and settings section can be shown / hidden one by one
    (right-click the video or the "View" button); the whole settings panel on the right collapses
    (Ctrl+B or the ▶ strip) so the picture can fill the screen
  * 1.2.3: up to 8 relays, each Off / On / Auto; Auto switches on a trigger: person, any motion, any
    animal or a single object type like "cat" (animal / object triggers use the AI model)
  * 1.2.3: web page: camera control + relays directly under the picture (before the event log),
    relay editor, show / hide fields, collapsible settings panel
  * 1.3.0: SCHEDULE - time plans (weekdays + start/end time, also over midnight) that force features ON / OFF:
    detection, recording, snapshots, person tracking, patrol, AI, auto relays, notifications.
    Desktop window + web page; a switch changed by hand wins until the schedule changes
  * 1.3.0: RECORDINGS PREVIEW page  http://<pi-ip>:5000/recordings : thumbnails, player, download, delete, filters
    (date, type, schedule, video source, search, sort). Recordings are H.264 when the encoder exists,
    otherwise they are converted for the browser on first play (needs ffmpeg)
  * 1.3.0: VIDEO SOURCE selection with camera scan: USB / V4L2 webcams, Raspberry Pi cameras (picamera2) and
    network cameras (RTSP / HTTP-MJPEG - IP and Wi-Fi cams) that you add by URL; switchable while running
  * 1.4.0: ZONES - draw ignore / only-here areas on the picture (web page /zones); they act on detection, recording, alarms, relays
  * 1.4.0: MORE CAMERAS - extra cameras record on motion, grid view at /cams (main camera keeps AI, tracking, relays)
  * 1.4.0: SCHEDULES learn sunset / sunrise, a shift in minutes, "only when nobody / somebody is home" (phones answer a ping)
    and skip dates (holidays, 2026-12-24..2026-12-26 or 12-24 every year)
  * 1.4.0: RECORDINGS - pre-roll (seconds before the detection), H.264 through ffmpeg (hardware encoder on Pi 3/4, x264 otherwise,
    crash-safe fragmented MP4), favourites that the automatic cleanup never deletes, ZIP download, statistics + day timeline
  * 1.4.0: ALARMS - ntfy push and Telegram with snapshot and a link to the recordings, besides the webhook
  * 1.4.0: SECURITY / OPERATION - --https (self-signed certificate is created), --bind, lock-out after wrong passwords,
    security headers, warning when the page is open without a password, settings file readable by the owner only,
    --print-service / --install-service for autostart (systemd), clean stop on SIGTERM
  * 1.4.0: new look of all web pages (header navigation, cards, live badges, light / dark)
  * 1.4.1: touch JOYSTICK on the live page: drag = pan/tilt, the further you pull the faster it moves, release = stop
    (speed slow / medium / fast; the old direction buttons are one tap away under "Control")
  * 1.4.2: "Expand all / Collapse all" at the very top of the settings panel; CPU temperature in the header badge and the video HUD
  * 1.5.0: TIMELAPSE - every N minutes the camera drives to a chosen position, waits until the picture is calm, saves a photo and
    drives back. An alarm (person, recording, tracking) always has priority: the photo is taken after the alarm.
    Photos in <recordings>/timelapse/, "Create video" turns a day (or all photos) into an MP4
  * 1.5.0: PRE-ALARM - new relay trigger "pre-alarm (any movement)": switches at the first movement in the picture
  * 1.5.0: THERMAL CAMERA - second camera (same view) that is laid over the picture: blend or "hot areas only"; choose it after the camera scan
  * 1.5.1: Wi-Fi signal (e.g. phone hotspot) in the header, the system card and the HUD + internet check (push messages need it)
  * 1.5.1: PRE-ALARM PUSH - short ntfy / Telegram / webhook message with a small picture at the first movement (own cooldown)
  * 1.5.2: ALARM SOUND IN THE BROWSER - bell at the top of every web page: pre-alarm = two beeps, person = siren, vibration on
    phones, volume, mute 30 min. Alarms arrive live over /api/alerts (Server-Sent Events), also in a background tab
  * 1.5.3: SETTINGS IN ONE FIXED FOLDER ~/.config/motionwatch (--config DIR to change): a new version, saved anywhere, keeps
    everything. On the first start the settings of an older version are found and taken over; a backup copy is kept.
    The layout (open / closed cards, hidden fields, theme, language, stick / buttons) is saved too - web page and desktop window
  * 1.6.0: WI-FI / HOTSPOT - search networks, connect (falls back to the previous network if it fails), save for automatic
    connection (preferred), forget. NetworkManager (nmcli) or wpa_supplicant. Push message with the new address of the page
    when the Pi joins a network. Without root once:  sudo python3 webcam_bewegung_1_7_4.py --allow-wifi
  * 1.6.1: Wi-Fi signal history (5 min) with average, weakest value and drop-outs - web page and desktop window;
    "Expand all / Collapse all" now works for every card of the web page
  * 1.6.2: FPS in the header; the whole header can be hidden with one button (per device); phone layout: the stick sits
    directly under the live picture (portrait) or right next to it (landscape)
  * 1.6.3: the web page / stream is ON from the start (--no-web switches it off); on phones "Expand all / Collapse all"
    sit directly under the stick
  * 1.6.4: phone: "Expand all / Collapse all" under the "Control: Stick | Buttons" switch; event log directly under the system card
  * 1.6.5: the current servo position is shown on the stick (orange ring + cross hair inside the dashed travel range)
  * 1.6.6: phone (portrait): "Expand all / Collapse all" between the picture card and the "Controls" card
  * 1.7.0: CAMPING - own Wi-Fi of the Pi (hotspot, works without mobile network) with one switch; ARMED / DISARMED with
    countdown (alarms, push, browser sound, relays, recordings only while armed); THERMAL ALARM (warm body moving in the
    zones: relay trigger, push, sound, recording); the clock of the Pi is taken from the phone when there is no internet
    time; CAMPING PROFILE: own Wi-Fi + camera stays still + alarms on + armed after the countdown (switching off restores)
  * 1.7.1: AUTOSTART switch: on = at boot Motion Watch starts by itself (systemd, no screen needed) and switches the own
    Wi-Fi on; off = nothing starts at boot and the Pi joins its known networks
  * 1.7.2: NETWORK AUTOMATIC: known networks first (phone hotspot = internet + push), otherwise the own Wi-Fi; when the
    phone hotspot disappears the own Wi-Fi comes on, and every 10 min (only if no device is connected) it looks again
  * 1.7.3: web page: the 26 menus are now 8 groups (Alarm & camping, Notifications, Detection, Camera & servos,
    Recordings & timelapse, Thermal camera, Relays & schedule, System & network); fine tuning under "Advanced"; more compact
  * 1.7.4: the desktop window uses the same 8 groups as the web page

Install:  sudo apt install python3-pil.imagetk python3-tk python3-gpiozero ffmpeg python3-picamera2
          pip install opencv-python numpy pillow flask psutil
AI model (optional, put next to the script):
          wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz
          tar xzf ssd_mobilenet_v2_coco_2018_03_29.tar.gz
          cp ssd_mobilenet_v2_coco_2018_03_29/frozen_inference_graph.pb .
          wget https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt -O ssd_mobilenet_v2_coco.pbtxt
Run:      python3 webcam_bewegung_1_7_4.py  [--source auto|usb:0|pi:0|rtsp://...] [--cam 0] [--no-web] [--headless] [--port 5000]
                                            [--web-password SECRET] [--bind 127.0.0.1] [--https [--cert F --key F]]
Autostart: python3 webcam_bewegung_1_7_4.py --headless --web-password SECRET --https --print-service   (shows the systemd unit)
           sudo python3 webcam_bewegung_1_7_4.py --headless --web-password SECRET --https --install-service
Web pages: /  live + settings   /cams  all cameras   /recordings  preview   /zones  zone editor
            --web        start the web page right away      --headless   no desktop window (web only)
            --web-password  protect the web page (user name: anything)

Servo backends: gpiozero (works on Raspberry Pi 5) -> pigpio (older Pis, needs
"sudo pigpiod") -> simulation (no hardware, everything else still works).
"""

import argparse, atexit, functools, glob, hmac, json, math, os, queue, re, shutil, signal, subprocess, sys, tempfile, threading, time, urllib.request, uuid, zipfile
from collections import deque
from datetime import datetime, timedelta

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def default_data_dir():
    """Settings, log and certificate live in ONE fixed folder, independent of where the script is saved:
    ~/.config/motionwatch  (with sudo: the folder of the user who called sudo). MOTIONWATCH_HOME or --config override it.
    So a new version, saved anywhere, keeps all settings."""
    env = os.environ.get("MOTIONWATCH_HOME", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    home = os.path.expanduser("~")
    if os.environ.get("SUDO_USER") and hasattr(os, "geteuid") and os.geteuid() == 0:
        try:
            import pwd
            home = pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir
        except (ImportError, KeyError):
            pass
        return os.path.join(home, ".config", "motionwatch")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config"), "motionwatch")


DATA_DIR = default_data_dir()
SETTINGS_NAME = "motionwatch_settings.json"
SETTINGS_FILE = os.path.join(DATA_DIR, SETTINGS_NAME)
LOG_FILE = os.path.join(DATA_DIR, "motionwatch.log")


def set_data_dir(path):
    """Use this folder for settings / log / certificate (creates it). Falls back to the script folder if it cannot be written."""
    global DATA_DIR, SETTINGS_FILE, LOG_FILE
    path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
    except OSError as e:
        print(f"Settings folder {path} is not writable ({e}) - using the script folder instead")
        path = HERE
    DATA_DIR = path
    SETTINGS_FILE = os.path.join(path, SETTINGS_NAME)
    LOG_FILE = os.path.join(path, "motionwatch.log")
    return path


def _settings_saved_time(p):
    try:
        with open(p) as f:
            d = json.load(f)
        if not isinstance(d, dict) or not isinstance(d.get("cfg"), dict):
            return None
        return d.get("saved") or datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")
    except (OSError, ValueError):
        return None


def find_old_settings():
    """Settings files of older versions (next to their script). Looks in the script folder, the current folder, the home
    folder and two levels below it (e.g. ~/Downloads/v1.4/), and in the folders next to the script folder. Newest first."""
    home = os.path.expanduser("~")
    if os.environ.get("SUDO_USER"):
        try:
            import pwd
            home = pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir
        except (ImportError, KeyError):
            pass
    pats = [os.path.join(HERE, SETTINGS_NAME), os.path.join(os.getcwd(), SETTINGS_NAME), os.path.join(home, SETTINGS_NAME),
            os.path.join(home, "*", SETTINGS_NAME), os.path.join(home, "*", "*", SETTINGS_NAME),
            os.path.join(os.path.dirname(HERE), "*", SETTINGS_NAME), "/home/*/" + SETTINGS_NAME, "/home/*/*/" + SETTINGS_NAME]
    found = {}
    for pat in pats:
        for p in glob.glob(pat)[:200]:
            p = os.path.abspath(p)
            if p == os.path.abspath(SETTINGS_FILE) or p in found:
                continue
            t = _settings_saved_time(p)
            if t:
                found[p] = t
    return sorted(found, key=lambda p: found[p], reverse=True)


def prepare_settings_file():
    """Called once at start: take over the settings of an older version (first start of 1.5.3 or newer), keep a backup copy
    of the last good settings, move the HTTPS certificate along. Returns a short message for the log."""
    msg = ""
    if not os.path.isfile(SETTINGS_FILE):
        old = find_old_settings()
        if old:
            try:
                shutil.copy2(old[0], SETTINGS_FILE)
                os.chmod(SETTINGS_FILE, 0o600)
                msg = f"Settings taken over from the older version: {old[0]}"
            except OSError as e:
                msg = f"Could not take over old settings from {old[0]}: {e}"
    if os.path.isfile(SETTINGS_FILE) and _settings_saved_time(SETTINGS_FILE):
        try:                                             # backup of the last good file (before this version changes it)
            shutil.copy2(SETTINGS_FILE, os.path.join(DATA_DIR, "motionwatch_settings.backup.json"))
        except OSError:
            pass
    for name in ("motionwatch_cert.pem", "motionwatch_key.pem"):
        src, dst = os.path.join(HERE, name), os.path.join(DATA_DIR, name)
        if os.path.isfile(src) and not os.path.isfile(dst) and DATA_DIR != HERE:
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass
    return msg

# ----------------------------------------------------------------------------
# Configuration (everything here is adjustable from the GUI)
# ----------------------------------------------------------------------------
CFG = {
    # master
    "detection_on": True, "highlight_red": True, "show_tracks": True,
    "show_mask": False, "show_hud": True,
    # sensitivity
    "sensitivity": 50, "min_area": 1500,
    # shadow filter (colour based: same hue/saturation, darker brightness = shadow)
    "shadow_filter": True, "shadow_ratio_max": 0.92, "shadow_ratio_min": 0.30,
    # walking recognition
    "walk_frames": 6, "walk_min_speed": 0.3, "walk_max_speed": 30.0, "speed_consistency": 0.4,
    "person_sticky": True,       # once confirmed, a person stays flagged while tracked (standing still is fine)
    # vehicle filter
    "car_filter": True, "car_aspect": 1.35, "car_speed": 14.0, "car_area_frac": 0.18,
    # rain / wind
    "rain_auto": True, "rain_mode": False, "rain_threshold": 0.35,
    "wind_auto": True, "wind_threshold": 0.30, "wind_boost_max": 4.0,
    # AI (SSD MobileNet V2)
    "ai_enabled": True,          # auto-disabled if model files are missing
    "ai_require": False,         # motion persons must be confirmed by the AI
    "ai_conf": 0.5,              # confidence threshold
    "ai_every": 3,               # run the network every N frames
    "show_objects": True,        # mark ALL objects the network finds (not just persons)
    "object_conf": 0.5,          # confidence threshold for non-person objects
    # recording
    "record": True, "record_dir": "recordings", "record_tail": 3.0,
    "record_max_gb": 2.0,        # oldest recordings are deleted above this size
    "snapshot_on_person": True,  # save a JPG the moment a person is detected
    # low light
    "lowlight_auto": True, "lowlight_threshold": 60,   # mean brightness (0-255) below which CLAHE is applied
    # notifications (POST JSON to this URL when a person is detected; leave empty to disable)
    "notify_url": "", "notify_cooldown": 60.0,
    # processing
    "proc_width": 480,
    # auto-tune
    "auto_tune": True, "calib_seconds": 6.0, "walk_seconds": 0.6,
    # servos  (positions in percent 0-100)
    "pan": 50.0, "tilt": 50.0,
    "servo_min_us": 500, "servo_max_us": 2500,
    "invert_pan": False, "invert_tilt": False,
    "track_person": True,        # keep the detected person centred
    "track_gain": 0.6,           # how aggressively the camera follows
    "track_deadzone": 0.08,      # fraction of the frame treated as "centred"
    # patrol
    "patrol": False, "patrol_dwell": 2.0, "patrol_speed": 30.0,   # %/second
    "patrol_tilt": 50.0,
    # manual camera control (pad / arrow keys / web) pauses tracking + patrol for this many seconds
    "manual_hold": 5.0,
    # appearance
    "theme": "dark", "lang": "en", "fullscreen": False,
    "ui_hidden": [],             # desktop fields the user has hidden (View menu)
    # web stream
    "web_stream": False, "web_port": 5000, "web_password": "",
    "web_quality": 75,           # JPEG quality of the stream (lower = less CPU / bandwidth)
    "web_width": 1280,           # max stream width in px (smaller = less CPU / bandwidth)
    # video source: auto | usb:<n> | pi:<n> | url:<id>   (network cameras are saved in ip_sources)
    "source": "auto", "ip_sources": [],
    # switches that only exist so a schedule can control them
    "notify_on": True,           # send notifications
    "notify_type": "webhook", "telegram_token": "", "telegram_chat": "", "public_url": "",
    "pre_roll": 2.0,             # seconds of video before the detection that are added to a recording
    "record_encoder": "auto",    # auto = ffmpeg (hardware H.264 when the Pi has it, else x264) | opencv
    "show_zones": True,
    "latitude": 47.37, "longitude": 8.54,   # for sunrise / sunset schedules
    "presence_hosts": [], "away_after": 10.0,
    "extra_cams": [],            # more cameras (motion recording only): list of source ids
    "relays_on": True,           # Auto relays may switch (On / Off relays are not affected)
    # timelapse: park the camera at a chosen position, take a photo every N minutes (an alarm always has priority)
    "timelapse_on": False, "timelapse_interval": 10.0,      # minutes
    "timelapse_pan": 50.0, "timelapse_tilt": 50.0,          # the position the photo is taken from (percent)
    "timelapse_settle": 4.0,     # seconds to wait after the move (servo travel + auto exposure)
    "timelapse_return": True,    # go back to the previous position afterwards
    "timelapse_fps": 25.0,       # frame rate of the video that is made from the photos
    "timelapse_max_gb": 2.0,     # oldest photos are deleted above this size
    # thermal camera: a second camera (same view) that is laid over the normal picture
    "thermal_on": False, "thermal_source": "", "thermal_alpha": 0.5, "thermal_map": "inferno",
    "thermal_hot": False, "thermal_hot_pct": 80.0,          # hot mode: only the warmest N percent are shown
    # pre-alarm push: a short message (small picture) to the phone at the first movement, before a person is confirmed
    "notify_prealarm": False, "prealarm_cooldown": 120.0, "prealarm_photo": True,
    "browser_alarm": True,       # open web pages get pre-alarm / person alarms live (sound in the browser)
    # layout: which cards are open / closed, hidden fields, theme, language, stick or buttons ... (web and desktop window)
    "web_ui": {}, "ui_open": ["grp:alarm"],
    "notify_network": True,      # push message with the page address when the Pi joins a network (e.g. the phone hotspot)
    # protection: alarms only while armed; arming waits arm_delay seconds
    "armed": True, "arm_delay": 60.0,
    # own Wi-Fi of the Pi (access point) + camping profile
    "hotspot_on": False, "hotspot_ssid": "MotionWatch", "hotspot_password": "", "camping": False, "camping_prev": {},
    # thermal camera alarm: a warm body that moves inside the zones
    "thermal_alarm": False, "thermal_need_motion": True, "thermal_delta": 30.0, "thermal_min_area": 0.5,
    "time_from_browser": True,   # set the clock of the Pi from the phone when it has no internet time
    "autostart": False,          # start at boot (systemd)
    # network: auto = known networks (phone hotspot) first, otherwise the own Wi-Fi | hotspot = own Wi-Fi at boot | client = known only
    "net_mode": "auto", "auto_wait": 60.0, "auto_retry": 10.0,
}

STATE = {
    "rain_score": 0.0, "rain_mode": False,
    "wind_score": 0.0, "wind_level": "calm", "wind_boost": 1.0,
    "persons": 0, "candidates": 0, "recording": False,
    "fps": 0.0, "events": [], "frames": 0, "uptime": 0,
    "ignored_vehicles": 0, "detections_total": 0,
    "auto_status": "idle", "auto_changes": 0,
    "ai_status": "off", "ai_persons": 0, "ai_ms": 0, "shadow_pct": 0,
    "servo_backend": "–", "relay": False, "patrol_status": "off", "tracking": False,
    "web_status": "off",
    "objects": 0, "object_summary": "",
    "cpu": 0.0, "cpu_temp": None, "cpu_hist": [], "cpu_count": 1,
    "lowlight": False, "brightness": 0, "rec_dir_mb": 0, "notify_status": "off", "web_viewers": 0,
    "settings_status": "defaults",
    "relay_states": [], "relay_out": [], "present": [], "manual": False,
    "source_id": "", "source_label": "", "source_status": "starting", "source_res": "", "rec_name": "",
    "sched_active": [], "sched_active_idx": [], "sched_forced": {}, "sched_manual": [],
    "presence": "unknown", "web_open": False, "extra": [], "recording_enc": "",
    "timelapse": "off", "timelapse_last": "", "timelapse_render": "", "thermal": "off", "thermal_res": "",
    "wifi": None, "net": {"online": None, "ms": None}, "wifi_hist": [],
    "arm_state": "armed", "arm_left": 0, "hotspot": {"on": False, "ssid": "", "clients": 0, "ip": "", "busy": False, "available": False, "msg": ""},
    "time_status": "", "warm": 0, "autostart": {"on": False, "mode": "", "msg": "", "path": ""}, "netauto": "off",
}
DEFAULTS = dict(CFG)
WAYPOINTS = []          # pan positions in percent
START = time.time()
LOCK = threading.Lock()
GPIO_PAN, GPIO_TILT, GPIO_RELAY = 17, 27, 22
GPIO_RESERVED = (GPIO_PAN, GPIO_TILT)          # servo pins can never be used as relays
MAX_RELAYS = 8
FREE_GPIOS = (23, 24, 25, 5, 6, 12, 13, 16, 26, 4, 22, 18, 19, 20, 21)


def default_relays():
    """Relay 1 = the original alarm relay on GPIO 22 (switches while a person is detected)."""
    return [{"name": "Relay 1", "gpio": GPIO_RELAY, "mode": "auto", "trigger": "person", "hold": 5.0, "active_low": False}]


RELAYS = default_relays()          # edited in the desktop window and on the web page, saved in the settings file
MANUAL = {"until": 0.0}            # manual camera moves pause tracking / patrol until this time


def manual_active():
    return time.time() < MANUAL["until"]


def move_camera(cmd, step=3.0):
    """Manual pan/tilt step (direction pad, arrow keys, web page). Pauses tracking/patrol for manual_hold seconds."""
    try:
        step = max(0.5, min(25.0, float(step)))
    except (TypeError, ValueError):
        step = 3.0
    if cmd == "left":
        CFG["pan"] = max(0.0, CFG["pan"] - step)
    elif cmd == "right":
        CFG["pan"] = min(100.0, CFG["pan"] + step)
    elif cmd == "up":
        CFG["tilt"] = min(100.0, CFG["tilt"] + step)
    elif cmd == "down":
        CFG["tilt"] = max(0.0, CFG["tilt"] - step)
    elif cmd == "center":
        CFG["pan"] = 50.0; CFG["tilt"] = 50.0
    else:
        return False
    MANUAL["until"] = time.time() + CFG["manual_hold"]
    return True


STICK = {"t": 0.0}                 # time of the last joystick sample (0 = stick released)


def stick_camera(x, y, speed=30.0):
    """Joystick: x/y = deflection -1..1 (right / up are positive), speed = full-deflection speed in % per second.
    The camera moves by deflection * speed * time since the last sample, so it can never run away: no sample, no movement.
    A small dead zone and a quadratic curve make slow, precise moves easy near the centre."""
    try:
        x, y = float(x), float(y)
        speed = max(5.0, min(100.0, float(speed)))
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(x) and math.isfinite(y)):
        return False
    now = time.time()
    last, STICK["t"] = STICK["t"], now
    mag = math.hypot(x, y)
    if mag < 0.08:
        STICK["t"] = 0.0
        return True
    dt = now - last if 0.0 < now - last < 0.5 else 0.1          # first sample after a pause counts as one 100 ms tick
    k = min(1.0, (mag - 0.08) / 0.92) ** 2 * speed * dt / mag
    CFG["pan"] = max(0.0, min(100.0, CFG["pan"] + x * k))
    CFG["tilt"] = max(0.0, min(100.0, CFG["tilt"] + y * k))
    MANUAL["until"] = now + CFG["manual_hold"]
    return True



ALERTS = {"seq": 0, "items": deque(maxlen=50)}      # live alarms for open web pages (sound in the browser)
ALERTS_COND = threading.Condition()


def push_alert(kind, text="", **extra):
    if not CFG.get("browser_alarm", True):
        return
    if kind in ("person", "prealarm", "warm") and not is_armed():
        return
    with ALERTS_COND:
        ALERTS["seq"] += 1
        ALERTS["items"].append(dict(seq=ALERTS["seq"], kind=kind, text=text, time=datetime.now().strftime("%H:%M:%S"), ts=time.time(), **extra))
        ALERTS_COND.notify_all()


def log_event(kind, text):
    with LOCK:
        STATE["events"].insert(0, {"t": datetime.now().strftime("%H:%M:%S"), "kind": kind, "text": text})
        del STATE["events"][60:]
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  [{kind}]  {text}\n")
    except OSError:
        pass


# ----------------------------------------------------------------------------
# Zones: polygons on the picture (normalised 0..1). "ignore" = detections whose feet are inside are dropped,
# "only" = when at least one such zone exists, only detections inside it count.
# ----------------------------------------------------------------------------
MAX_ZONES = 12
ZONES = []              # [{"id", "name", "mode": "ignore"|"only", "points": [[x, y], ...]}]


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _clean_zone(z, i):
    if not isinstance(z, dict):
        return None
    pts = []
    for p in (z.get("points") or [])[:40] if isinstance(z.get("points"), list) else []:
        if isinstance(p, (list, tuple)) and len(p) == 2 and _num(p[0]) and _num(p[1]):
            pts.append([round(min(1.0, max(0.0, float(p[0]))), 4), round(min(1.0, max(0.0, float(p[1]))), 4)])
    if len(pts) < 3:
        return None
    zid = str(z.get("id") or "")
    return {"id": zid if re.fullmatch(r"[0-9a-f]{8}", zid) else uuid.uuid4().hex[:8],
            "name": str(z.get("name") or "").strip()[:40] or f"Zone {i + 1}",
            "mode": "only" if z.get("mode") == "only" else "ignore", "points": pts}


def point_in_poly(x, y, pts):
    inside, j = False, len(pts) - 1
    for i in range(len(pts)):
        xi, yi, xj, yj = pts[i][0], pts[i][1], pts[j][0], pts[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def zone_allows(nx, ny):
    zs = ZONES
    if not zs:
        return True
    for z in zs:
        if z["mode"] == "ignore" and point_in_poly(nx, ny, z["points"]):
            return False
    only = [z for z in zs if z["mode"] == "only"]
    return (not only) or any(point_in_poly(nx, ny, z["points"]) for z in only)


def zone_box_ok(b, pw, ph):
    """Box (x, y, w, h, ...) in processing-frame pixels; the point that counts is the middle of the feet region."""
    if not ZONES:
        return True
    return zone_allows((b[0] + b[2] / 2.0) / pw, (b[1] + b[3] * 0.85) / ph)


def zones_set(lst):
    if not isinstance(lst, list):
        return False, "invalid zones"
    out = []
    for z in lst[:MAX_ZONES]:
        c = _clean_zone(z, len(out))
        if c:
            out.append(c)
    with LOCK:
        ZONES[:] = out
    save_settings(); log_event("sys", f"Zones updated ({len(out)})")
    return True, ""


# ----------------------------------------------------------------------------
# Presence: is somebody home? (ping the phones / devices from the settings)
# ----------------------------------------------------------------------------
PRESENCE = {"home": None, "seen": {}, "start": time.time()}
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]{0,79}$")


def _ping(host):
    try:
        return subprocess.run(["ping", "-c", "1", "-W", "1", host], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


class PresenceMonitor:
    """Every 20 s: ping the configured devices. 'home' = one of them answered within the last 'away_after' minutes
    (phones sleep their Wi-Fi, so a single missed ping means nothing)."""
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                self.check()
            except Exception as e:
                log_event("sys", f"Presence error: {e}")
            time.sleep(20.0)

    def check(self):
        hosts = [h for h in CFG["presence_hosts"] if isinstance(h, str) and _HOST_RE.match(h)]
        if not hosts or shutil.which("ping") is None:
            PRESENCE["home"] = None; STATE["presence"] = "unknown"; return
        ts = [threading.Thread(target=lambda h=h: PRESENCE["seen"].__setitem__(h, time.time()) if _ping(h) else None, daemon=True) for h in hosts]
        for t in ts:
            t.start()
        for t in ts:
            t.join(6.0)
        now, grace = time.time(), CFG["away_after"] * 60.0
        seen = [PRESENCE["seen"].get(h, 0.0) for h in hosts]
        if any(now - x < grace for x in seen):
            home = True
        elif not any(seen) and now - PRESENCE["start"] < grace:
            home = None                                    # just started, nothing answered yet -> unknown
        else:
            home = False
        if home != PRESENCE["home"]:
            log_event("sched", "Presence: " + {True: "somebody is home", False: "nobody home", None: "unknown"}[home])
        PRESENCE["home"] = home
        STATE["presence"] = {True: "home", False: "away", None: "unknown"}[home]


# ----------------------------------------------------------------------------
# Text settings (notifications, location, presence) - validated, shared by desktop window and web page
# ----------------------------------------------------------------------------
NOTIFY_TYPES = ("webhook", "ntfy", "telegram")
THERMAL_MAPS = {"inferno": cv2.COLORMAP_INFERNO, "jet": cv2.COLORMAP_JET, "hot": cv2.COLORMAP_HOT, "turbo": cv2.COLORMAP_TURBO,
                "grey": None}
TEXTS = [  # (section, key, label, kind, extra)
    ("Notifications", "notify_type", "Notification type", "enum", NOTIFY_TYPES),
    ("Notifications", "notify_url", "Webhook / ntfy URL", "str", None),
    ("Notifications", "telegram_token", "Telegram bot token", "secret", None),
    ("Notifications", "telegram_chat", "Telegram chat id", "str", None),
    ("Notifications", "public_url", "Address of this page for links (e.g. https://pi.local:5000)", "str", None),
    ("Thermal camera", "thermal_source", "Thermal camera (run the camera scan first)", "enum", "thermal_choices"),
    ("Thermal camera", "thermal_map", "Colours", "enum", tuple(THERMAL_MAPS)),
    ("Camping / protection", "net_mode", "Network", "enum", "net_modes"),
    ("Camping / protection", "hotspot_ssid", "Own Wi-Fi: name", "str", None),
    ("Camping / protection", "hotspot_password", "Own Wi-Fi: password (8-63 characters)", "str", None),
    ("Setup", "latitude", "Latitude (sunrise / sunset)", "float", (-66.0, 66.0)),
    ("Setup", "longitude", "Longitude (sunrise / sunset)", "float", (-180.0, 180.0)),
    ("Setup", "presence_hosts", "Phones / devices for presence (IP or name, comma separated)", "hosts", None),
]
TEXT_SPECS = {k: (kind, extra) for s, k, l, kind, extra in TEXTS}


def text_choice_pairs(key):
    """[(value, label)] of an enum setting. The thermal camera list changes with the camera scan, so it is computed."""
    kind, extra = TEXT_SPECS[key]
    if extra == "net_modes":
        return [("auto", tr("Automatic: known networks (e.g. phone hotspot), otherwise own Wi-Fi")),
                ("hotspot", tr("Own Wi-Fi at boot")), ("client", tr("Only known networks"))]
    if extra == "thermal_choices":
        act = STATE["source_id"]
        return [("", "– " + tr("none") + " –")] + [(i["id"], i["name"]) for i in list_sources() if i["id"] not in ("auto", act)]
    return [(c, tr(c)) for c in extra]


def _http_ok(u):
    return isinstance(u, str) and len(u) <= 500 and re.match(r"^https?://[^\s]+$", u, re.I) is not None


def text_value(key):
    v = CFG[key]
    return ", ".join(v) if isinstance(v, list) else v


def set_text(key, value):
    spec = TEXT_SPECS.get(key)
    if spec is None:
        return False, "unknown setting"
    kind, extra = spec
    if kind == "enum":
        if value not in [c for c, _l in text_choice_pairs(key)]:
            return False, "invalid value"
        CFG[key] = value
        if key == "net_mode":
            NETAUTO["paused"] = False
            log_event("sys", f"Network mode: {value}")
    elif kind == "float":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False, "not a number"
        if not math.isfinite(v) or not extra[0] <= v <= extra[1]:
            return False, "out of range"
        CFG[key] = round(v, 4)
    elif kind == "hosts":
        hosts = [h for h in re.split(r"[,; ]+", str(value or "")) if h]
        if len(hosts) > 8 or not all(_HOST_RE.match(h) for h in hosts):
            return False, "invalid device name or address"
        CFG[key] = hosts
    else:
        v = str(value or "").strip()
        if v:
            if key in ("notify_url", "public_url") and not _http_ok(v):
                return False, "invalid URL (http:// or https:// expected)"
            if key == "telegram_token" and not re.fullmatch(r"\d{5,12}:[A-Za-z0-9_\-]{20,60}", v):
                return False, "invalid Telegram bot token"
            if key == "telegram_chat" and not re.fullmatch(r"-?\d{1,20}|@[A-Za-z0-9_]{3,64}", v):
                return False, "invalid Telegram chat id"
        if key == "hotspot_ssid" and (not v or len(v.encode()) > 32 or any(ord(c) < 32 for c in v)):
            return False, "invalid network name"
        if key == "hotspot_password" and not (8 <= len(v) <= 63 and all(32 <= ord(c) < 127 for c in v)):
            return False, "the password must have 8 to 63 characters"
        CFG[key] = v
    save_settings()
    return True, ""


def web_texts(lang=None):
    """Schema + current values for the web page (secrets are never sent, only whether they are set)."""
    out = []
    for sec, key, label, kind, extra in TEXTS:
        v = text_value(key)
        out.append({"section": sec, "key": key, "label": tr(label, lang), "kind": kind, "choices": [c for c, _l in text_choice_pairs(key)] if kind == "enum" else None,
                    "labels": {c: l for c, l in text_choice_pairs(key)} if kind == "enum" else None,
                    "value": "" if kind == "secret" else v, "set": bool(v)})
    return out


# ----------------------------------------------------------------------------
# Schedules (time plans): switch features on / off at certain times
#   A schedule = name + weekdays + start/end time + a list of "feature -> ON / OFF".
#   While a schedule is active its features are forced; when it ends they go back to the value
#   the user had set.  Changing a forced switch by hand wins until the schedule changes.
#   Windows may cross midnight (22:00 -> 06:00 belongs to the day it starts on).
# ----------------------------------------------------------------------------
MAX_SCHEDULES = 12
MAX_EXTRA = 3
SCHEDULES = []          # [{"name", "enabled", "days": [0=Mon .. 6=Sun], "start": "HH:MM", "end": "HH:MM", "actions": {key: bool}}]
SCHED = {"base": {}, "manual": set(), "last": {}, "active": []}
SCHED_FEATURES = [      # (config key, label) - everything a schedule may switch
    ("detection_on", "Detection"), ("record", "Recording"), ("snapshot_on_person", "Snapshots"),
    ("track_person", "Person tracking"), ("patrol", "Patrol"), ("ai_enabled", "AI detection"),
    ("relays_on", "Auto relays"), ("notify_on", "Notifications"), ("timelapse_on", "Timelapse"), ("thermal_on", "Thermal overlay"),
    ("notify_prealarm", "Pre-alarm push"), ("browser_alarm", "Alarm sound in the browser"),
    ("armed", "Armed (alarms)"), ("thermal_alarm", "Thermal alarm"),
]
SCHED_KEYS = [k for k, _ in SCHED_FEATURES]
SCHED_NOTE = ("While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. "
              "Switching one by hand overrides the schedule until its next change.")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _clean_time(v, default):
    return v if isinstance(v, str) and _TIME_RE.match(v) else default


def _day_ok(d):
    return isinstance(d, (int, float)) and not isinstance(d, bool) and math.isfinite(d) and 0 <= d <= 6


def _clean_schedule(s, i):
    """Validate / normalise one schedule dict (from the settings file, web page or desktop dialog)."""
    if not isinstance(s, dict):
        return None
    name = str(s.get("name") or "").strip()[:40] or f"Schedule {i + 1}"
    days = s.get("days", list(range(7)))
    days = sorted({int(d) for d in days if _day_ok(d)}) if isinstance(days, list) else list(range(7))
    acts = s.get("actions") if isinstance(s.get("actions"), dict) else {}
    off = s.get("sun_offset", 0)
    off = 0 if isinstance(off, bool) or not isinstance(off, (int, float)) or not math.isfinite(off) else int(max(-180, min(180, off)))
    return {"name": name, "enabled": bool(s.get("enabled", True)), "days": days,
            "start": _clean_time(s.get("start"), "22:00"), "end": _clean_time(s.get("end"), "06:00"),
            "sun": s.get("sun") if s.get("sun") in ("dark", "light") else "",        # "dark" = sunset..sunrise, "light" = sunrise..sunset
            "sun_offset": off,                                                       # minutes added to sunrise and sunset
            "presence": s.get("presence") if s.get("presence") in ("away", "home") else "",
            "skip": re.sub(r"[^0-9.,; \-]", "", str(s.get("skip") or ""))[:200].strip(),   # dates on which the schedule does not run
            "actions": {k: acts[k] for k in SCHED_KEYS if isinstance(acts.get(k), bool)}}


def _mins(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def sun_times(d, lat, lon):
    """Sunrise / sunset as minutes after local midnight (NOAA formula, about +-2 min). 'dark' / 'light' for polar night / day."""
    n = d.timetuple().tm_yday
    g = 2 * math.pi / 365.0 * (n - 1)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
           + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    c = math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(dec)) - math.tan(la) * math.tan(dec)
    if c > 1:
        return "dark"
    if c < -1:
        return "light"
    ha = math.degrees(math.acos(c))
    try:
        tz = datetime(d.year, d.month, d.day, 12).astimezone().utcoffset().total_seconds() / 60.0
    except (OverflowError, OSError, ValueError):
        tz = 0.0
    return (720 - 4 * (lon + ha) - eq + tz, 720 - 4 * (lon - ha) - eq + tz)


@functools.lru_cache(maxsize=64)
def _parse_skip(text):
    """'2026-12-24..2026-12-26, 08-01' -> ranges. 'MM-DD' repeats every year."""
    def point(t):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", t)
        try:
            if m:
                return ("d", datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date())
            m = re.fullmatch(r"(\d{2})-(\d{2})", t)
            if m:
                datetime(2000, int(m.group(1)), int(m.group(2)))
                return ("y", (int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass
        return None
    out = []
    for tok in re.split(r"[,; ]+", text or ""):
        if not tok:
            continue
        a, _, b = tok.partition("..")
        pa, pb = point(a), point(b or a)
        if pa and pb and pa[0] == pb[0]:
            out.append((pa[0], pa[1], pb[1]))
    return tuple(out)


def _is_skipped(s, d):
    for kind, a, b in _parse_skip(s.get("skip", "")):
        if kind == "d" and a <= d <= b:
            return True
        if kind == "y" and a <= (d.month, d.day) <= b:
            return True
    return False


def _window_start(s, dt):
    """The calendar day on which the time window that contains `dt` started (None = outside). A window that crosses midnight
    belongs to the day it starts on."""
    today, cur = dt.date(), dt.hour * 60 + dt.minute
    if s.get("sun"):
        r = sun_times(today, CFG["latitude"], CFG["longitude"])
        light = s["sun"] == "light"
        if r in ("dark", "light"):
            return today if (r == "light") == light else None
        rise, sset = r[0] + s.get("sun_offset", 0), r[1] + s.get("sun_offset", 0)
        if light:
            return today if rise <= cur < sset else None
        if cur >= sset:
            return today
        return today - timedelta(days=1) if cur < rise else None
    a, b = _mins(s["start"]), _mins(s["end"])
    if a == b:                                   # same start and end = the whole day
        return today
    if a < b:
        return today if a <= cur < b else None
    if cur >= a:
        return today
    return today - timedelta(days=1) if cur < b else None


def schedule_window_contains(s, dt):
    """Is the moment `dt` inside the schedule's weekdays + time window? (ignores 'enabled' and presence)"""
    if not s["days"]:
        return False
    d = _window_start(s, dt)
    return d is not None and d.weekday() in s["days"] and not _is_skipped(s, d)


def presence_ok(s):
    p = s.get("presence")
    home = PRESENCE["home"]
    if not p or home is None:                    # no rule, or presence unknown -> stay armed
        return True
    return home if p == "home" else not home


def schedule_active(s, dt=None):
    return bool(s["enabled"]) and schedule_window_contains(s, dt or datetime.now()) and presence_ok(s)


def days_text(days, names=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
    days = sorted(days)
    if len(days) == 7:
        return "every day" if names[0] == "Mon" else "täglich"
    if days == [0, 1, 2, 3, 4]:
        return f"{names[0]}–{names[4]}"
    if days == [5, 6]:
        return f"{names[5]}, {names[6]}"
    return ", ".join(names[d] for d in days) or "–"


def schedule_tick():
    """Apply all schedules (called once per second by the Scheduler thread and after every edit)."""
    with LOCK:
        plans = [dict(s) for s in SCHEDULES]
    now = datetime.now()
    forced, active, active_idx = {}, [], []
    for i, s in enumerate(plans):
        if schedule_active(s, now):
            active.append(s["name"]); active_idx.append(i)
            forced.update(s["actions"])                  # later schedules win over earlier ones
    base, manual, last = SCHED["base"], SCHED["manual"], SCHED["last"]
    labels = dict(SCHED_FEATURES)
    prev = SCHED["active"]
    for n in active:
        if n not in prev:
            log_event("sched", f"Schedule started: {n}")
    for n in prev:
        if n not in active:
            log_event("sched", f"Schedule ended: {n}")
    SCHED["active"] = active
    for k, v in forced.items():
        if last.get(k) != v:
            manual.discard(k)                            # new window / new value -> the schedule takes over again
        if k in manual:
            continue
        if k not in base:
            base[k] = CFG[k]
        if CFG[k] != v:
            CFG[k] = v
            log_event("sched", f"Schedule: {labels.get(k, k)} {'ON' if v else 'OFF'}")
    for k in list(base):
        if k not in forced:                              # no schedule controls it any more -> give the user's value back
            CFG[k] = base.pop(k); manual.discard(k)
            log_event("sched", f"Schedule: {labels.get(k, k)} back to {'ON' if CFG[k] else 'OFF'}")
    SCHED["last"] = dict(forced)
    STATE["sched_active"] = list(active); STATE["sched_active_idx"] = active_idx
    STATE["sched_forced"] = dict(forced); STATE["sched_manual"] = sorted(manual)


def sched_user_changed(key):
    """A switch was changed by hand. If a schedule currently forces it, the user's choice wins until the schedule changes."""
    if key in SCHED["last"]:
        SCHED["manual"].add(key)
        SCHED["base"][key] = CFG[key]


def schedule_add():
    with LOCK:
        if len(SCHEDULES) >= MAX_SCHEDULES:
            return False, f"maximum {MAX_SCHEDULES} schedules"
        SCHEDULES.append(_clean_schedule({"name": f"Schedule {len(SCHEDULES) + 1}", "actions": {}}, len(SCHEDULES)))
    save_settings(); log_event("sched", "Schedule added")
    schedule_tick()
    return True, ""


def schedule_save(index, data):
    clean = _clean_schedule(data, index if isinstance(index, int) else 0)
    if clean is None:
        return False, "invalid schedule"
    with LOCK:
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(SCHEDULES):
            return False, "unknown schedule"
        SCHEDULES[index] = clean
    save_settings()
    schedule_tick()
    return True, ""


def schedule_remove(index):
    with LOCK:
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(SCHEDULES):
            return False, "unknown schedule"
        gone = SCHEDULES.pop(index)
    save_settings(); log_event("sched", f"Schedule removed: {gone['name']}")
    schedule_tick()
    return True, ""


class Scheduler:
    """Background thread: applies the time plans once per second."""
    def __init__(self):
        schedule_tick()
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                schedule_tick(); arm_tick()
            except Exception as e:                      # never let the scheduler thread die
                log_event("sys", f"Scheduler error: {e}")
            time.sleep(1.0)


# ----------------------------------------------------------------------------
# Settings persistence (autosaved 2 s after any change)
# ----------------------------------------------------------------------------
VOLATILE = {"web_stream", "web_password", "rain_mode", "fullscreen"}   # never restored from disk
_save_timer = None


WEB_UI_KEY = re.compile(r"^mw-[A-Za-z0-9_:\-./ ]{1,90}$")
WEB_UI_LOCAL = {"mw-sound", "mw-hdr"}                      # per device on purpose (sound on the phone, not on the PC)


def clean_web_ui(d):
    out = {}
    if isinstance(d, dict):
        for k, v in list(d.items())[:400]:
            if isinstance(k, str) and WEB_UI_KEY.match(k) and k not in WEB_UI_LOCAL and isinstance(v, str) and len(v) <= 4000:
                out[k] = v
    return out


def web_ui_update(changes, removes=()):
    if not isinstance(changes, dict):
        return False
    cur = dict(CFG["web_ui"])
    cur.update(clean_web_ui(changes))
    for k in (removes if isinstance(removes, list) else []):
        cur.pop(k, None)
    CFG["web_ui"] = clean_web_ui(cur)                # re-assign: DEFAULTS share the old dict
    save_settings()
    return True


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        STATE["settings_status"] = "defaults (no file yet)"
        return
    n = 0
    for k, v in data.get("cfg", {}).items():
        if k in CFG and k not in VOLATILE and isinstance(v, type(CFG[k])) or (k in CFG and isinstance(CFG[k], float) and isinstance(v, int)):
            CFG[k] = type(CFG[k])(v); n += 1
    WAYPOINTS[:] = [float(w) for w in data.get("waypoints", []) if isinstance(w, (int, float))]
    CFG["ui_hidden"] = [k for k in CFG["ui_hidden"] if isinstance(k, str)][:200]
    CFG["ui_open"] = [k for k in CFG["ui_open"] if isinstance(k, str)][:100]
    CFG["web_ui"] = clean_web_ui(CFG["web_ui"])
    rl = data.get("relays")
    if isinstance(rl, list):
        used, out = set(), []
        for r in rl[:MAX_RELAYS]:
            if isinstance(r, dict):
                c = _clean_relay(r, len(out), used)
                if c:
                    out.append(c); used.add(c["gpio"])
        RELAYS[:] = out
    else:                                    # settings file from 1.2.2 -> migrate the single relay
        old = data.get("cfg", {}); r0 = default_relays()[0]
        if old.get("relay_on_person") is False:
            r0["mode"] = "off"
        if isinstance(old.get("relay_hold"), (int, float)) and not isinstance(old.get("relay_hold"), bool):
            r0["hold"] = max(0.5, min(600.0, float(old["relay_hold"])))
        RELAYS[:] = [r0]
    sc = data.get("schedules")
    if isinstance(sc, list):
        out = []
        for x in sc[:MAX_SCHEDULES]:
            c = _clean_schedule(x, len(out))
            if c:
                out.append(c)
        SCHEDULES[:] = out
    zl = data.get("zones")
    if isinstance(zl, list):
        ZONES[:] = [z for z in (_clean_zone(x, i) for i, x in enumerate(zl[:MAX_ZONES])) if z]
    CFG["presence_hosts"] = [h for h in CFG["presence_hosts"] if isinstance(h, str) and _HOST_RE.match(h)][:8]
    CFG["extra_cams"] = [x for x in CFG["extra_cams"] if isinstance(x, str) and SRC_RE.match(x) and x != "auto"][:MAX_EXTRA]
    if CFG["notify_type"] not in NOTIFY_TYPES:
        CFG["notify_type"] = "webhook"
    CFG["ip_sources"] = _clean_ip_sources(CFG["ip_sources"])
    if not SRC_RE.match(str(CFG["source"])):
        CFG["source"] = "auto"
    STATE["settings_status"] = f"loaded {n} settings, {len(WAYPOINTS)} waypoints, {len(RELAYS)} relays, {len(SCHEDULES)} schedules"
    log_event("sys", f"Settings loaded from {SETTINGS_FILE} ({n} values, {len(WAYPOINTS)} waypoints, {len(RELAYS)} relays, {len(SCHEDULES)} schedules)")


def save_settings_now():
    try:
        tmp = SETTINGS_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"cfg": {k: SCHED["base"].get(k, v) for k, v in CFG.items() if k not in VOLATILE}, "waypoints": list(WAYPOINTS),
                       "relays": [dict(r) for r in RELAYS], "schedules": [dict(x) for x in SCHEDULES], "zones": [dict(z) for z in ZONES],
                       "saved": datetime.now().isoformat(timespec="seconds")}, f, indent=1)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, SETTINGS_FILE)
        STATE["settings_status"] = "saved " + datetime.now().strftime("%H:%M:%S")
    except OSError as e:
        STATE["settings_status"] = f"save failed: {e}"


def save_settings():
    """Debounced: many slider moves -> one write."""
    global _save_timer
    if _save_timer:
        _save_timer.cancel()
    _save_timer = threading.Timer(2.0, save_settings_now); _save_timer.daemon = True; _save_timer.start()


def reset_settings():
    for k, v in DEFAULTS.items():
        if k not in VOLATILE and k not in ("pan", "tilt", "source", "ip_sources", "extra_cams", "latitude", "longitude",
                                           "presence_hosts", "telegram_token", "telegram_chat", "public_url", "notify_url", "notify_type",
                                           "web_ui", "ui_open", "ui_hidden", "theme", "lang"):
            CFG[k] = v
    WAYPOINTS.clear()
    RELAYS[:] = default_relays()
    ZONES.clear(); SCHEDULES.clear(); SCHED["base"].clear(); SCHED["manual"].clear(); SCHED["last"] = {}; SCHED["active"] = []
    save_settings_now()
    log_event("sys", "Settings reset to defaults")


# ----------------------------------------------------------------------------
# Notifications: webhook / ntfy / Telegram when a person is detected (with cooldown)
# ----------------------------------------------------------------------------
TELEGRAM_API = "https://api.telegram.org"


class Notifier:
    """Alarm message when a person is detected (with cooldown). Three kinds:
         webhook   JSON POST to a URL (Home Assistant, IFTTT, ...)
         ntfy      push to the ntfy app: the snapshot is attached, a tap opens the recordings page
         telegram  photo + caption to a Telegram chat (bot token + chat id)"""
    def __init__(self):
        self.last = 0.0; self.last_pre = 0.0; self.last_warm = 0.0

    @staticmethod
    def configured():
        if CFG["notify_type"] == "telegram":
            return bool(CFG["telegram_token"] and CFG["telegram_chat"])
        return bool(CFG["notify_url"].strip())

    def person(self, count, snapshot_path=None, frame=None):
        if count and not is_armed():
            STATE["notify_status"] = "disarmed"; return
        if not self.configured():
            STATE["notify_status"] = "off"; return
        if not CFG["notify_on"]:
            STATE["notify_status"] = "paused"; return
        now = time.time()
        if now - self.last < CFG["notify_cooldown"]:
            return
        self.last = now
        jpg, fname = None, "snapshot.jpg"
        try:
            if snapshot_path and os.path.isfile(snapshot_path) and os.path.getsize(snapshot_path) < 8 * 1024 * 1024:
                with open(snapshot_path, "rb") as f:
                    jpg = f.read()
                fname = os.path.basename(snapshot_path)
            elif frame is not None:
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                jpg = buf.tobytes() if ok else None
        except OSError:
            jpg = None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": "person" if count else "test", "persons": int(count), "time": datetime.now().isoformat(timespec="seconds"),
                   "snapshot": snapshot_path, "rain": bool(STATE["rain_mode"]), "wind": STATE["wind_level"],
                   "source": STATE["source_label"], "link": pub + "/recordings" if pub else ""}
        threading.Thread(target=self._dispatch, args=(payload, jpg, fname), daemon=True).start()

    def test(self, frame):
        self.last = 0.0
        self.person(0, None, frame)

    def prealarm(self, frame, event="prealarm"):
        """Pre-alarm push: something moves in the picture. Own cooldown; skipped right after a person alarm (that one says more).
        The picture is small (640 px) so it costs little mobile data. event="warm": the thermal camera saw a warm body."""
        if not ((CFG["notify_prealarm"] or event == "warm") and CFG["notify_on"] and self.configured() and is_armed()):
            return False
        now = time.time()
        if event == "warm":
            if now - self.last_warm < CFG["notify_cooldown"]:
                return False
            self.last_warm = now
        else:
            if now - self.last_pre < CFG["prealarm_cooldown"] or now - self.last < CFG["prealarm_cooldown"]:
                return False
            self.last_pre = now
        jpg = None
        if CFG["prealarm_photo"] and frame is not None:
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA) if w > 640 else frame
            ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
            jpg = buf.tobytes() if ok else None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": event, "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "snapshot": None,
                   "rain": bool(STATE["rain_mode"]), "wind": STATE["wind_level"], "source": STATE["source_label"],
                   "link": pub + "/" if pub else ""}
        threading.Thread(target=self._dispatch, args=(payload, jpg, "prealarm.jpg"), daemon=True).start()
        return True

    def info(self, text, link=""):
        """Short information message (e.g. the new address of the page). Not limited by the alarm cooldown."""
        if not (self.configured() and CFG["notify_on"]):
            return False
        payload = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text,
                   "snapshot": None, "rain": False, "wind": "", "source": STATE["source_label"], "link": link}
        threading.Thread(target=self._dispatch, args=(payload, None, ""), daemon=True).start()
        return True

    @staticmethod
    def _event(p):
        return p.get("event") if p.get("event") in ("person", "prealarm", "info", "warm") else "test"

    @staticmethod
    def _title(p):
        de = CFG["lang"] == "de"
        return {"person": "Motion Watch: Person erkannt" if de else "Motion Watch: person detected",
                "prealarm": "Motion Watch: Bewegung (Voralarm)" if de else "Motion Watch: movement (pre-alarm)",
                "info": "Motion Watch: Netzwerk" if de else "Motion Watch: network",
                "warm": "Motion Watch: Waerme erkannt" if de else "Motion Watch: warm body detected",
                "test": "Motion Watch: Test"}[Notifier._event(p)]

    @staticmethod
    def _text(p):
        de, ev, tm = CFG["lang"] == "de", Notifier._event(p), p["time"][11:]
        if ev == "test":
            txt = "Motion Watch Testnachricht" if de else "Motion Watch test message"
        elif ev == "info":
            txt = p.get("text", "")
        elif ev == "warm":
            txt = (f"Waermebild: warmer Koerper in der Zone um {tm} - Kamera: {p['source']}" if de
                   else f"Thermal camera: warm body in the zone at {tm} - camera: {p['source']}")
        elif ev == "prealarm":
            txt = (f"Voralarm: Bewegung um {tm} - Kamera: {p['source']}" if de else f"Pre-alarm: movement at {tm} - camera: {p['source']}")
        else:
            txt = (f"{p['persons']} Person(en) erkannt um {tm} - Kamera: {p['source']}" if de
                   else f"{p['persons']} person(s) detected at {tm} - camera: {p['source']}")
        return txt.encode("ascii", "replace").decode()

    def _dispatch(self, p, jpg, fname):
        kind, secret = CFG["notify_type"], CFG["telegram_token"]
        try:
            if kind == "telegram":
                code = self._telegram(p, jpg, fname); where = "Telegram"
            elif kind == "ntfy":
                code = self._ntfy(p, jpg, fname); where = "ntfy " + CFG["notify_url"][:40]
            else:
                url = CFG["notify_url"].strip()
                req = urllib.request.Request(url, data=json.dumps(p).encode(),
                                             headers={"Content-Type": "application/json", "Title": self._title(p)})
                with urllib.request.urlopen(req, timeout=8) as r:
                    code = r.status
                where = url[:40]
            STATE["notify_status"] = f"sent {datetime.now().strftime('%H:%M:%S')} (HTTP {code})"
            log_event("web", f"Notification sent to {where}… (HTTP {code})")
        except Exception as e:
            msg = str(e).replace(secret, "***") if secret else str(e)
            STATE["notify_status"] = f"error: {msg}"[:200]
            log_event("web", f"Notification failed: {msg}"[:200])

    def _ntfy(self, p, jpg, fname):
        ev = self._event(p)
        h = {"Title": self._title(p), "Tags": {"person": "warning,camera", "prealarm": "eyes,camera", "info": "signal_strength", "warm": "fire,camera"}.get(ev, "camera"),
             "Priority": {"person": "high", "warm": "high", "prealarm": "default"}.get(ev, "default")}
        if p["link"]:
            h["Click"] = p["link"]
        text = self._text(p)
        if jpg:
            h["Filename"] = fname; h["Message"] = text; h["Content-Type"] = "image/jpeg"
            req = urllib.request.Request(CFG["notify_url"].strip(), data=jpg, headers=h, method="PUT")
        else:
            req = urllib.request.Request(CFG["notify_url"].strip(), data=text.encode(), headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status

    def _telegram(self, p, jpg, fname):
        base = f"{TELEGRAM_API}/bot{CFG['telegram_token']}"
        text = self._text(p) + (("\n" + p["link"]) if p["link"] else "")
        if jpg:
            b = uuid.uuid4().hex
            parts = []
            for k, v in (("chat_id", CFG["telegram_chat"]), ("caption", text)):
                parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
            parts.append((f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="{fname}"\r\n'
                          f'Content-Type: image/jpeg\r\n\r\n').encode() + jpg + b"\r\n")
            parts.append(f"--{b}--\r\n".encode())
            req = urllib.request.Request(base + "/sendPhoto", data=b"".join(parts), headers={"Content-Type": "multipart/form-data; boundary=" + b})
        else:
            req = urllib.request.Request(base + "/sendMessage", data=json.dumps({"chat_id": CFG["telegram_chat"], "text": text}).encode(),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status


# ----------------------------------------------------------------------------
# Hardware: servos + relays  (gpiozero -> pigpio -> simulation)
# ----------------------------------------------------------------------------
class Hardware:
    """Pan/tilt servos + any number of relay outputs. Backends: gpiozero -> pigpio -> simulation."""
    def __init__(self):
        self.backend = "simulation"
        self.pan = self.tilt = self.pi = None
        self.outs = {}              # gpio -> {"dev": gpiozero device or None, "on": bool, "al": bool}
        self.fail = {}              # gpio -> time of last error (retried after 5 s)
        self._last_servo = None
        try:
            from gpiozero import Servo, OutputDevice
            mn, mx = CFG["servo_min_us"] / 1e6, CFG["servo_max_us"] / 1e6
            self.pan = Servo(GPIO_PAN, min_pulse_width=mn, max_pulse_width=mx)
            self.tilt = Servo(GPIO_TILT, min_pulse_width=mn, max_pulse_width=mx)
            self._OutputDevice = OutputDevice
            self.backend = "gpiozero"
        except Exception as e1:
            try:
                import pigpio
                self.pi = pigpio.pi()
                if not self.pi.connected:
                    raise RuntimeError("pigpiod not running")
                self._pigpio = pigpio
                self.backend = "pigpio"
            except Exception:
                log_event("servo", f"No servo hardware ({type(e1).__name__}) - simulation mode")
        STATE["servo_backend"] = self.backend
        log_event("servo", f"Servo backend: {self.backend}  (pan GPIO{GPIO_PAN}, tilt GPIO{GPIO_TILT}, "
                           f"relays GPIO {', '.join(str(r['gpio']) for r in RELAYS) or '-'})")
        threading.Thread(target=self.loop, daemon=True).start()

    def _us(self, pct):
        return CFG["servo_min_us"] + (CFG["servo_max_us"] - CFG["servo_min_us"]) * pct / 100.0

    def _servos(self, pan, tilt):
        if CFG["invert_pan"]: pan = 100 - pan
        if CFG["invert_tilt"]: tilt = 100 - tilt
        if self.backend == "gpiozero":
            self.pan.value = pan / 50.0 - 1.0
            self.tilt.value = tilt / 50.0 - 1.0
        elif self.backend == "pigpio":
            self.pi.set_servo_pulsewidth(GPIO_PAN, self._us(pan))
            self.pi.set_servo_pulsewidth(GPIO_TILT, self._us(tilt))

    def _write(self, gpio, on, al):
        ent = self.outs.get(gpio)
        if self.backend == "gpiozero":
            if ent is None or ent["al"] != al:
                if ent is not None and ent["dev"] is not None:
                    ent["dev"].close()
                    self.outs.pop(gpio, None)
                ent = {"dev": self._OutputDevice(gpio, active_high=not al, initial_value=False), "on": False, "al": al}
                self.outs[gpio] = ent
            ent["dev"].on() if on else ent["dev"].off()
        else:
            if ent is None:
                if self.backend == "pigpio":
                    self.pi.set_mode(gpio, self._pigpio.OUTPUT)
                ent = {"dev": None, "on": False, "al": al}
                self.outs[gpio] = ent
            if self.backend == "pigpio":
                self.pi.write(gpio, int(bool(on)) ^ int(bool(al)))
        ent["on"], ent["al"] = on, al

    def _release(self, gpio):
        ent = self.outs.pop(gpio, None)
        if not ent:
            return
        try:
            if self.backend == "gpiozero" and ent["dev"] is not None:
                ent["dev"].off(); ent["dev"].close()
            elif self.backend == "pigpio":
                self.pi.write(gpio, 1 if ent["al"] else 0)          # inactive level
        except Exception:
            pass

    def loop(self):
        """50 Hz: push pan/tilt and all relay states to the hardware when they change."""
        while True:
            pan = max(0.0, min(100.0, float(CFG["pan"])))
            tilt = max(0.0, min(100.0, float(CFG["tilt"])))
            cur = (round(pan, 1), round(tilt, 1))
            if cur != self._last_servo:
                try:
                    self._servos(pan, tilt)
                except Exception as e:
                    log_event("servo", f"Servo error: {e}")
                self._last_servo = cur
            wanted = {g: (on, al) for g, on, al in STATE["relay_out"]}
            for g in [g for g in self.outs if g not in wanted]:
                self._release(g)
            now = time.time()
            for g, (on, al) in wanted.items():
                ent = self.outs.get(g)
                if ent is not None and ent["on"] == on and ent["al"] == al:
                    continue
                if now - self.fail.get(g, 0.0) < 5.0:
                    continue
                try:
                    self._write(g, on, al); self.fail.pop(g, None)
                except Exception as e:
                    self.fail[g] = now
                    log_event("servo", f"Relay GPIO{g} error: {e}")
            time.sleep(0.02)




# ----------------------------------------------------------------------------
# System monitor: CPU load (+ temperature) sampled once per second
# ----------------------------------------------------------------------------
class SysMonitor:
    def __init__(self):
        self.hist = deque(maxlen=60)          # last 60 seconds
        self._prev = None
        try:
            import psutil
            self.ps = psutil
            psutil.cpu_percent(percpu=True)   # first call only primes the counters
        except ImportError:
            self.ps = None
            log_event("sys", "psutil not installed - using /proc/stat (pip install psutil recommended)")
        STATE["cpu_count"] = os.cpu_count() or 1
        threading.Thread(target=self.loop, daemon=True).start()

    def _cpu(self):
        if self.ps:
            per = self.ps.cpu_percent(percpu=True)
            return sum(per) / len(per) if per else 0.0
        try:                                   # Linux fallback without psutil
            with open("/proc/stat") as f:
                vals = [int(v) for v in f.readline().split()[1:]]
        except Exception:
            return None
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals[:8])
        prev, self._prev = self._prev, (idle, total)
        if prev is None or total <= prev[1]:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (1.0 - (idle - prev[0]) / (total - prev[1]))))

    def _temp(self):
        try:                                   # Raspberry Pi / most Linux boards
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return int(f.read().strip()) / 1000.0
        except Exception:
            pass
        if self.ps and hasattr(self.ps, "sensors_temperatures"):
            try:
                for entries in self.ps.sensors_temperatures().values():
                    if entries:
                        return float(entries[0].current)
            except Exception:
                pass
        return None

    def loop(self):
        while True:
            time.sleep(1.0)
            cpu = self._cpu()
            temp = self._temp()
            if cpu is not None:
                self.hist.append(round(cpu, 1))
            STATE.update(cpu=None if cpu is None else round(cpu, 1),
                         cpu_temp=None if temp is None else round(temp, 1),
                         cpu_hist=list(self.hist))


# ----------------------------------------------------------------------------
# Network: Wi-Fi signal (e.g. a phone hotspot) and whether the internet can be reached (push messages need it)
#   /proc/net/wireless every 2 s (signal level), "iw dev <if> link" every 15 s (network name, speed), internet check every 30 s
# ----------------------------------------------------------------------------
def _proc_wireless():
    out = {}
    try:
        with open("/proc/net/wireless") as f:
            lines = f.read().splitlines()[2:]
    except OSError:
        return out
    for ln in lines:
        if ":" not in ln:
            continue
        iface, rest = ln.split(":", 1); parts = rest.split()
        try:
            link, level = float(parts[1].rstrip(".")), float(parts[2].rstrip("."))
        except (IndexError, ValueError):
            continue
        if level > 63:                                   # some drivers report an unsigned byte (200 = -56 dBm)
            level -= 256
        out[iface.strip()] = (link, level)
    return out


def _wifi_ifaces():
    names = sorted(set(_proc_wireless()) | {os.path.basename(os.path.dirname(p)) for p in glob.glob("/sys/class/net/*/wireless")})
    return names


def _iw_link(iface):
    """-> dict(ssid, dbm, rate, connected) from 'iw', or None when iw is missing."""
    if shutil.which("iw") is None:
        return None
    try:
        r = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return None
    txt = r.stdout
    if "Not connected" in txt or not txt.strip():
        return {"ssid": "", "dbm": None, "rate": "", "connected": False}
    m_ss = re.search(r"SSID:\s*(.+)", txt); m_sig = re.search(r"signal:\s*(-?\d+)", txt); m_rate = re.search(r"tx bitrate:\s*([\d.]+\s*\S+)", txt)
    return {"ssid": m_ss.group(1).strip()[:40] if m_ss else "", "dbm": int(m_sig.group(1)) if m_sig else None,
            "rate": m_rate.group(1) if m_rate else "", "connected": True}


def wifi_pct(dbm):
    return int(max(0, min(100, 2 * (dbm + 100)))) if dbm is not None else 0


class NetMonitor:
    def __init__(self):
        self.iw = {}; self.weak = False; self.was = None; self.ip = ""; self.announced = None; self.t_start = time.time()
        self.key = None; self.changed_at = 0.0; self.recheck = False
        self.hist = deque(maxlen=150)                    # one value every 2 s = the last 5 minutes (None = no connection)
        threading.Thread(target=self.loop, daemon=True).start()
        threading.Thread(target=self.online_loop, daemon=True).start()

    def sample(self, n):
        if n % 8 == 0 or WIFI.get("refresh") or WIFI.get("hs_busy"):
            try:
                hotspot_refresh()
            except Exception:
                pass
        if STATE["hotspot"].get("on"):                   # the Pi is the access point itself: no signal to measure
            STATE["wifi"] = {"iface": WIFI["iface"], "ssid": STATE["hotspot"]["ssid"], "dbm": None, "pct": 0, "rate": "", "connected": False,
                             "ip": STATE["hotspot"]["ip"], "ap": True}
            self.was = None; WIFI["refresh"] = False
            return
        ifaces = _wifi_ifaces()
        if not ifaces:
            STATE["wifi"] = None; return
        proc = _proc_wireless()
        iface = next((i for i in ifaces if i in proc and proc[i][1] < 0), ifaces[0])
        refresh = WIFI.get("refresh") or WIFI.get("busy")
        if refresh:
            WIFI["refresh"] = False
        if n % 8 == 0 or iface not in self.iw or refresh:
            info = _iw_link(iface)
            if info is not None:
                self.iw[iface] = info
        iw = self.iw.get(iface) or {}
        dbm = int(proc[iface][1]) if iface in proc and proc[iface][1] < 0 else iw.get("dbm")
        connected = (dbm is not None) if not iw else bool(iw.get("connected")) and dbm is not None
        if connected and (n % 8 == 0 or not self.ip or refresh):
            self.ip = wifi_ip(iface)
        elif not connected:
            self.ip = ""
        STATE["wifi"] = {"iface": iface, "ssid": iw.get("ssid", "") if connected else "", "dbm": dbm if connected else None,
                         "pct": wifi_pct(dbm) if connected else 0, "rate": iw.get("rate", "") if connected else "", "connected": connected,
                         "ip": self.ip}
        self.hist.append(dbm if connected else None)
        STATE["wifi_hist"] = list(self.hist)
        self.announce(connected, iw.get("ssid", ""))
        if connected != self.was:
            if self.was is not None:
                log_event("sys", f"Wi-Fi {iface}: " + (f"connected ({dbm} dBm)" if connected else "connection lost"))
            self.was = connected
        if connected:
            if not self.weak and dbm < -77:
                self.weak = True; log_event("sys", f"Wi-Fi signal weak: {dbm} dBm")
            elif self.weak and dbm > -72:
                self.weak = False; log_event("sys", f"Wi-Fi signal ok again: {dbm} dBm")

    def announce(self, connected, ssid):
        """Push message with the address of the page when the Pi is in a (new) network - on a phone hotspot nobody knows
        the address otherwise. Waits until the internet works, because the message needs it."""
        key = (ssid, self.ip)
        if key != self.key:                              # new network / address: check the internet again right away
            self.key = key; self.changed_at = time.time(); self.recheck = True
        net = STATE["net"]
        if not (connected and self.ip and CFG["notify_network"]) or net.get("online") is not True or net.get("t", 0) < self.changed_at:
            return
        if key == self.announced or time.time() - self.t_start < 8:
            return
        w = WATCH_REF.get("w")
        if w is None:
            return
        addr = page_address(self.ip)
        de = CFG["lang"] == "de"
        txt = (f"Motion Watch ist online im WLAN {ssid or '?'}: {addr}" if de else f"Motion Watch is online in Wi-Fi {ssid or '?'}: {addr}")
        if w.notifier.info(txt, addr):
            self.announced = key
            log_event("sys", f"Address sent as push message: {addr}")

    def loop(self):
        n = 0
        while True:
            try:
                self.sample(n)
            except Exception as e:
                STATE["wifi"] = None; log_event("sys", f"Wi-Fi monitor error: {e}"); time.sleep(30)
            n += 1
            time.sleep(2.0)

    def online_loop(self):
        import socket
        while True:
            res = {"online": False, "ms": None}
            for host in ("1.1.1.1", "8.8.8.8"):
                t0 = time.time()
                try:
                    socket.create_connection((host, 53), timeout=3).close()
                    res = {"online": True, "ms": int((time.time() - t0) * 1000)}
                    break
                except OSError:
                    pass
            if STATE["net"].get("online") is not None and res["online"] != STATE["net"]["online"]:
                log_event("sys", "Internet reachable again" if res["online"] else "Internet not reachable (push messages cannot be sent)")
            res["t"] = time.time()
            STATE["net"] = res
            self.recheck = False
            for _ in range(30 if res["online"] else 10):     # every 30 s (10 s while offline), at once after a network change
                if self.recheck:
                    break
                time.sleep(1.0)


# ----------------------------------------------------------------------------
# Wi-Fi management: search networks (phone hotspots), connect, save for automatic connection, forget.
#   NetworkManager (nmcli, Raspberry Pi OS Bookworm and newer) - or wpa_supplicant (wpa_cli, older systems).
#   "Connect now" falls back to the previous network when the new one does not work.
# ----------------------------------------------------------------------------
WIFI = {"backend": None, "iface": "", "scan": [], "scan_time": 0.0, "job": "", "job_ok": None, "busy": False, "refresh": False}
_WIFI_LOCK = threading.Lock()


def _run(cmd, timeout=30, inp=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=inp)
        return r.returncode, r.stdout, (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as e:
        return 127, "", str(e)


def _nm_split(line):
    """nmcli -t output: fields separated by ':', a literal ':' is written as '\\:'."""
    out, cur, esc = [], [], False
    for ch in line:
        if esc:
            cur.append(ch); esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def wifi_backend():
    if WIFI["backend"] is None:
        if shutil.which("nmcli"):
            code, out, _e = _run(["nmcli", "-t", "-f", "RUNNING", "general"], 8)
            if code == 0 and "running" in out:
                WIFI["backend"] = "nm"
        if WIFI["backend"] is None and shutil.which("wpa_cli"):
            WIFI["backend"] = "wpa"
        if WIFI["backend"] is None:
            WIFI["backend"] = ""
    if not WIFI["iface"]:
        ifs = _wifi_ifaces()
        WIFI["iface"] = ifs[0] if ifs else "wlan0"
    return WIFI["backend"]


def _perm_hint(err):
    e = (err or "").lower()
    if "not authorized" in e or "permission" in e or "insufficient privileges" in e or "access denied" in e:
        return ("no permission to change Wi-Fi - start the program with sudo, or allow it once with: "
                f"sudo python3 {os.path.basename(__file__)} --allow-wifi")
    return err or "error"


def _bars_from_pct(p):
    return 4 if p >= 75 else 3 if p >= 50 else 2 if p >= 25 else 1 if p > 0 else 0


def wifi_ip(iface=None):
    iface = iface or WIFI["iface"] or "wlan0"
    code, out, _e = _run(["ip", "-4", "-o", "addr", "show", "dev", iface], 5)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out or "")
    return m.group(1) if m else ""


def local_ip():
    """Address of this computer in the local network (no packet is sent)."""
    import socket
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sk.connect(("10.255.255.255", 1)); return sk.getsockname()[0]
        finally:
            sk.close()
    except OSError:
        return wifi_ip()


def page_address(ip=None):
    ip = ip or wifi_ip()
    scheme = "https" if WEB_OPTS.get("https") else "http"
    return f"{scheme}://{ip}:{CFG['web_port']}/" if ip else ""


# ---- NetworkManager ----------------------------------------------------------
def _nm_saved():
    code, out, err = _run(["nmcli", "-t", "-f", "NAME,UUID,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY,ACTIVE", "connection", "show"], 15)
    res = []
    if code != 0:
        return res
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) < 6 or f[2] not in ("802-11-wireless", "wifi"):
            continue
        c2, ss, _e = _run(["nmcli", "-t", "-g", "802-11-wireless.ssid,802-11-wireless.mode", "connection", "show", "uuid", f[1]], 10)
        lines = ss.splitlines() if c2 == 0 else []
        ssid = lines[0] if lines else f[0]
        mode = lines[1] if len(lines) > 1 else ""
        if mode == "ap":                                   # a hotspot the Pi itself offers - not a network to join
            continue
        try:
            prio = int(f[4])
        except ValueError:
            prio = 0
        res.append({"name": f[0], "id": f[1], "ssid": ssid, "auto": f[3] == "yes", "prio": prio, "active": f[5] == "yes"})
    return res


def _nm_scan():
    code, out, err = _run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,CHAN", "device", "wifi", "list", "--rescan", "yes"], 40)
    if code != 0:                                          # rescanning may need more rights: use the cached list
        code, out, err = _run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,CHAN", "device", "wifi", "list", "--rescan", "no"], 20)
    if code != 0:
        raise RuntimeError(_perm_hint(err))
    nets = {}
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) < 5 or not f[1]:
            continue
        try:
            sig = int(f[2])
        except ValueError:
            sig = 0
        sec = f[3].strip() if f[3].strip() not in ("", "--") else ""
        cur = nets.get(f[1]); act = f[0].strip() == "*"
        if cur is None or sig > cur["signal"]:            # 2.4 + 5 GHz of the same network: show the stronger one
            nets[f[1]] = {"ssid": f[1], "signal": sig, "secure": bool(sec), "security": sec, "chan": f[4],
                          "active": act or bool(cur and cur["active"])}
        elif act:
            cur["active"] = True
    return list(nets.values())


def _nm_connect_now(ssid, password):
    saved = next((s for s in _nm_saved() if s["ssid"] == ssid), None)
    if saved:
        if password:
            _run(["nmcli", "connection", "modify", "uuid", saved["id"], "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password], 15)
        code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", saved["id"]], 50)
    else:
        cmd = ["nmcli", "--wait", "40", "device", "wifi", "connect", ssid] + (["password", password] if password else []) + ["ifname", WIFI["iface"]]
        code, out, err = _run(cmd, 50)
    return code == 0, _perm_hint(err) if code else ""


def _nm_save(ssid, password, preferred):
    prio = "20" if preferred else "0"
    saved = next((s for s in _nm_saved() if s["ssid"] == ssid), None)
    if saved:
        cmd = ["nmcli", "connection", "modify", "uuid", saved["id"], "connection.autoconnect", "yes", "connection.autoconnect-priority", prio]
        if password:
            cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password]
    else:
        cmd = ["nmcli", "connection", "add", "type", "wifi", "ifname", WIFI["iface"], "con-name", ssid, "ssid", ssid,
               "connection.autoconnect", "yes", "connection.autoconnect-priority", prio]
        if password:
            cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password]
    code, out, err = _run(cmd, 20)
    return code == 0, _perm_hint(err) if code else ""


def _nm_forget(sid):
    code, out, err = _run(["nmcli", "connection", "delete", "uuid", sid], 20)
    return code == 0, _perm_hint(err) if code else ""


def _nm_up(sid):
    code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", sid], 50)
    return code == 0


# ---- wpa_supplicant (older Raspberry Pi OS) ------------------------------------
def _wpa(*args, timeout=15):
    return _run(["wpa_cli", "-i", WIFI["iface"]] + list(args), timeout)


def _wpa_saved():
    code, out, err = _wpa("list_networks")
    res = []
    for ln in out.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 2 and f[0].isdigit():
            res.append({"name": f[1], "id": f[0], "ssid": f[1], "auto": "[DISABLED]" not in (f[3] if len(f) > 3 else ""),
                        "prio": 0, "active": "[CURRENT]" in (f[3] if len(f) > 3 else "")})
    return res


def _wpa_scan():
    _wpa("scan"); time.sleep(4)
    code, out, err = _wpa("scan_results")
    if code != 0:
        raise RuntimeError(_perm_hint(err))
    cur = next((s["ssid"] for s in _wpa_saved() if s["active"]), "")
    nets = {}
    for ln in out.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) < 5 or not f[4]:
            continue
        try:
            pct = wifi_pct(int(f[2]))
        except ValueError:
            pct = 0
        if f[4] not in nets or pct > nets[f[4]]["signal"]:
            sec = "WPA" if ("WPA" in f[3] or "RSN" in f[3]) else ("WEP" if "WEP" in f[3] else "")
            nets[f[4]] = {"ssid": f[4], "signal": pct, "secure": bool(sec), "security": sec, "chan": f[1], "active": f[4] == cur}
    return list(nets.values())


def _wpa_q(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _wpa_save(ssid, password, preferred, select=False):
    saved = next((s for s in _wpa_saved() if s["ssid"] == ssid), None)
    if saved:
        nid = saved["id"]
    else:
        code, out, err = _wpa("add_network")
        nid = out.strip().splitlines()[-1] if out.strip() else ""
        if not nid.isdigit():
            return False, _perm_hint(err or out)
        _wpa("set_network", nid, "ssid", _wpa_q(ssid))
    if password:
        _wpa("set_network", nid, "psk", _wpa_q(password))
    elif not saved:
        _wpa("set_network", nid, "key_mgmt", "NONE")
    _wpa("set_network", nid, "priority", "20" if preferred else "0")
    code, out, err = _wpa("select_network" if select else "enable_network", nid)
    _wpa("save_config")
    return code == 0 and "FAIL" not in out, _perm_hint(err) if code else ("" if "FAIL" not in out else "wpa_supplicant refused it")


# ---- common entry points ---------------------------------------------------------
def wifi_status():
    b = wifi_backend()
    saved = []
    try:
        saved = _nm_saved() if b == "nm" else (_wpa_saved() if b == "wpa" else [])
    except Exception:
        saved = []
    w = STATE["wifi"] or {}
    ip = wifi_ip() if b else ""
    act = next((x for x in saved if x["active"]), None)            # the network manager knows best which network is in use
    import socket
    host = socket.gethostname()
    names = {x["ssid"] for x in saved}
    scan = [dict(n, active=(n["ssid"] == act["ssid"]) if act else n["active"], saved=n["ssid"] in names) for n in WIFI["scan"]]
    scan.sort(key=lambda n: (not n["active"], -n["signal"]))
    return {"backend": b, "iface": WIFI["iface"], "saved": saved, "scan": scan, "scan_time": WIFI["scan_time"],
            "job": WIFI["job"], "job_ok": WIFI["job_ok"], "busy": WIFI["busy"], "ssid": act["ssid"] if act else w.get("ssid", ""),
            "connected": bool(act) or w.get("connected", False),
            "ip": ip, "address": page_address(ip), "local_name": f"{host}.local", "port": CFG["web_port"],
            "https": bool(WEB_OPTS.get("https"))}


def wifi_scan():
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    if not _WIFI_LOCK.acquire(blocking=False):
        return False, "busy"
    try:
        nets = _nm_scan() if b == "nm" else _wpa_scan()
        saved = {s["ssid"] for s in (_nm_saved() if b == "nm" else _wpa_saved())}
        for n in nets:
            n["saved"] = n["ssid"] in saved; n["bars"] = _bars_from_pct(n["signal"])
        nets.sort(key=lambda n: (not n["active"], -n["signal"]))
        WIFI["scan"] = nets[:40]; WIFI["scan_time"] = time.time()
        log_event("sys", f"Wi-Fi scan: {len(nets)} network(s)")
        return True, ""
    except Exception as e:
        return False, str(e)[:200]
    finally:
        _WIFI_LOCK.release()


def _valid(ssid, password):
    if not isinstance(ssid, str) or not ssid or len(ssid.encode()) > 32 or any(ord(c) < 32 for c in ssid):
        return "invalid network name"
    if password and (not isinstance(password, str) or not 8 <= len(password) <= 63 or any(ord(c) < 32 for c in password)):
        return "the password must have 8 to 63 characters"
    return ""


def wifi_save(ssid, password="", preferred=True):
    err = _valid(ssid, password)
    if err:
        return False, err
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    with _WIFI_LOCK:
        ok, msg = _nm_save(ssid, password, preferred) if b == "nm" else _wpa_save(ssid, password, preferred)
    if ok:
        log_event("sys", f"Wi-Fi network saved: {ssid} (connects automatically{', preferred' if preferred else ''})")
    return ok, msg


def wifi_forget(sid):
    b = wifi_backend()
    if not b or not isinstance(sid, str) or not re.fullmatch(r"[0-9A-Za-z\-]{1,40}", sid):
        return False, "unknown network"
    with _WIFI_LOCK:
        if b == "nm":
            ok, msg = _nm_forget(sid)
        else:
            code, out, err = _wpa("remove_network", sid); _wpa("save_config")
            ok, msg = code == 0 and "FAIL" not in out, _perm_hint(err)
    if ok:
        log_event("sys", "Wi-Fi network removed")
    return ok, msg


def wifi_connect(ssid, password="", preferred=True):
    """Switch to another network in the background. If it does not work within ~45 s, go back to the previous one."""
    err = _valid(ssid, password)
    if err:
        return False, err
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    if WIFI["busy"]:
        return False, "busy"
    WIFI["busy"] = True; WIFI["job"] = f"connecting to {ssid}…"; WIFI["job_ok"] = None

    def work():
        try:
            with _WIFI_LOCK:
                prev = next((s for s in (_nm_saved() if b == "nm" else _wpa_saved()) if s["active"]), None)
                log_event("sys", f"Wi-Fi: switching to {ssid}" + (f" (from {prev['ssid']})" if prev else ""))
                if b == "nm":
                    ok, msg = _nm_connect_now(ssid, password)
                    if ok:
                        _nm_save(ssid, "", preferred)          # keep it for automatic connection later
                else:
                    ok, msg = _wpa_save(ssid, password, preferred, select=True)
                    if ok:                                   # wpa_cli returns at once: wait for the association
                        ok = False
                        for _ in range(30):
                            time.sleep(1.5)
                            st = _wpa("status")[1]
                            if f"ssid={ssid}" in st and "wpa_state=COMPLETED" in st:
                                ok = True; break
                        msg = "" if ok else "could not connect (wrong password or too far away?)"
                if ok:
                    for _ in range(10):                      # wait for an address
                        ip = wifi_ip()
                        if ip:
                            break
                        time.sleep(1)
                    WIFI["job"] = f"connected to {ssid}" + (f" · {page_address(ip)}" if ip else ""); WIFI["job_ok"] = True
                    log_event("sys", WIFI["job"])
                else:
                    back = ""
                    if prev and prev["ssid"] != ssid:
                        if b == "nm":
                            back = " - back on " + prev["ssid"] if _nm_up(prev["id"]) else " - previous network did not come back"
                        else:
                            _wpa("select_network", prev["id"]); [_wpa("enable_network", s["id"]) for s in _wpa_saved()]; _wpa("save_config")
                            back = " - back on " + prev["ssid"]
                    WIFI["job"] = f"failed: {msg or 'could not connect'}{back}"; WIFI["job_ok"] = False
                    log_event("sys", f"Wi-Fi: {ssid} failed ({msg}){back}")
        except Exception as e:
            WIFI["job"] = "failed: " + str(e)[:150]; WIFI["job_ok"] = False
        finally:
            WIFI["busy"] = False; WIFI["refresh"] = True
    threading.Thread(target=work, daemon=True).start()
    return True, ""


POLKIT_RULE = """// Motion Watch: allow user "{user}" to manage Wi-Fi / the own hotspot (NetworkManager) and the clock (timedated)
polkit.addRule(function(action, subject) {{
    if ((action.id.indexOf("org.freedesktop.NetworkManager.") == 0 || action.id.indexOf("org.freedesktop.timedate1.") == 0
         || action.id == "org.freedesktop.login1.set-self-linger") && subject.user == "{user}") {{
        return polkit.Result.YES;
    }}
}});
"""


def allow_wifi():
    """--allow-wifi: one-time permission so Motion Watch may change Wi-Fi without running as root."""
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "pi"
    path = "/etc/polkit-1/rules.d/50-motionwatch-wifi.rules"
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        print(f"Needs root. Run:  sudo {sys.executable} {os.path.abspath(__file__)} --allow-wifi"); return 1
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(POLKIT_RULE.format(user=user))
    except OSError as e:
        print(f"Could not write {path}: {e}"); return 1
    subprocess.run(["systemctl", "restart", "polkit"], capture_output=True)
    subprocess.run(["loginctl", "enable-linger", user], capture_output=True)       # autostart without login
    print(f"User '{user}' may now manage Wi-Fi, the own hotspot, the clock and the autostart ({path}).")
    return 0


# ----------------------------------------------------------------------------
# Own Wi-Fi of the Pi (access point / hotspot): the phone connects directly to the Pi - works without any mobile network.
#   NetworkManager connection "MotionWatch-Hotspot" (WPA2, 2.4 GHz for range). The page is then at http://10.42.0.1:<port>/
# ----------------------------------------------------------------------------
HOTSPOT_CON = "MotionWatch-Hotspot"
_PW_ALPHA = "abcdefghjkmnpqrstuvwxyz23456789"           # no 0/O, 1/l/i: easy to type on a phone


def hotspot_password():
    pw = CFG["hotspot_password"]
    if not (isinstance(pw, str) and 8 <= len(pw) <= 63):
        import secrets
        pw = "".join(secrets.choice(_PW_ALPHA) for _ in range(10))
        CFG["hotspot_password"] = pw; save_settings()
    return pw


def _nm_active_names():
    code, out, _e = _run(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"], 10)
    return [_nm_split(l)[0] for l in out.splitlines()] if code == 0 else []


def _hotspot_clients(iface):
    code, out, _e = _run(["iw", "dev", iface, "station", "dump"], 5)
    return sum(1 for l in out.splitlines() if l.startswith("Station")) if code == 0 else 0


def hotspot_refresh():
    b = wifi_backend()
    on = b == "nm" and HOTSPOT_CON in _nm_active_names()
    STATE["hotspot"] = {"on": on, "ssid": CFG["hotspot_ssid"] if on else "", "clients": _hotspot_clients(WIFI["iface"]) if on else 0,
                        "ip": wifi_ip() if on else "", "busy": WIFI.get("hs_busy", False), "available": b == "nm", "msg": WIFI.get("hs_msg", "")}
    return STATE["hotspot"]


def hotspot_set(on, persist=True):
    """Switch the own Wi-Fi on / off (blocking, a few seconds). Off = NetworkManager goes back to the known networks."""
    b = wifi_backend()
    if b != "nm":
        return False, "the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)"
    iface, ssid = WIFI["iface"], CFG["hotspot_ssid"] or "MotionWatch"
    with _WIFI_LOCK:
        if on:
            pw = hotspot_password()
            code, out, _e = _run(["nmcli", "-t", "-f", "NAME", "connection", "show"], 10)
            exists = HOTSPOT_CON in [_nm_split(l)[0] for l in out.splitlines()]
            sec = ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", pw, "wifi-sec.proto", "rsn", "wifi-sec.pairwise", "ccmp", "wifi-sec.group", "ccmp"]
            if exists:
                code, out, err = _run(["nmcli", "connection", "modify", "id", HOTSPOT_CON, "802-11-wireless.ssid", ssid] + sec, 20)
            else:
                code, out, err = _run(["nmcli", "connection", "add", "type", "wifi", "ifname", iface, "con-name", HOTSPOT_CON, "autoconnect", "no",
                                       "ssid", ssid, "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg", "ipv4.method", "shared"] + sec, 20)
            if code == 0:
                code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "id", HOTSPOT_CON], 50)
        else:
            code, out, err = _run(["nmcli", "connection", "down", "id", HOTSPOT_CON], 30)
            if code != 0 and "not an active connection" in (err or "").lower():
                code = 0
    ok = code == 0
    if ok:
        if persist:
            CFG["hotspot_on"] = on; save_settings()
        log_event("sys", f"Own Wi-Fi «{ssid}» switched ON (page: {page_address('10.42.0.1')})" if on else "Own Wi-Fi switched OFF - back to the known networks")
    else:
        log_event("sys", f"Own Wi-Fi could not be switched {'on' if on else 'off'}: {_perm_hint(err)}")
    WIFI["refresh"] = True
    return ok, "" if ok else _perm_hint(err)


def hotspot_switch_later(on, delay=1.5):
    """In the background, a little later: the web page that asked must still get its answer before the network changes."""
    WIFI["hs_busy"] = True; WIFI["hs_msg"] = ""
    def work():
        time.sleep(delay)
        try:
            ok, err = hotspot_set(on)
            WIFI["hs_msg"] = "" if ok else err
        finally:
            WIFI["hs_busy"] = False
            try:
                hotspot_refresh()
            except Exception:
                pass
    threading.Thread(target=work, daemon=True).start()


# ----------------------------------------------------------------------------
# Clock from the phone: the Pi has no clock with a battery (except Pi 5 with battery). Without internet it starts with a
# wrong time, then schedules, sunset and the names of recordings are wrong. Every page sends the time of the phone.
# ----------------------------------------------------------------------------
TIME = {"last": 0.0}


def _ntp_synced():
    code, out, _e = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], 5)
    return code == 0 and out.strip() == "yes"


def _set_timezone(tz):
    if not (isinstance(tz, str) and re.fullmatch(r"[A-Za-z_]+(/[A-Za-z0-9_+\-]+){0,2}", tz) and os.path.isfile(os.path.join("/usr/share/zoneinfo", tz))):
        return ""
    code, out, _e = _run(["timedatectl", "show", "-p", "Timezone", "--value"], 5)
    if code != 0 or out.strip() == tz:
        return ""
    code, out, err = _run(["timedatectl", "set-timezone", tz], 10)
    if code == 0:
        try:
            time.tzset()
        except AttributeError:
            pass
        log_event("sys", f"Time zone set from the phone: {tz}")
        return f"time zone {tz}"
    return ""


def _set_clock(epoch):
    stamp = datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(os, "geteuid") and os.geteuid() == 0 and shutil.which("date"):
        code, out, err = _run(["date", "-s", "@%d" % int(epoch)], 10)
        return code == 0, err
    code, out, err = _run(["timedatectl", "set-time", stamp], 10)
    if code != 0 and "automatic time synchronization" in (err or "").lower():
        _run(["timedatectl", "set-ntp", "false"], 10)              # allowed to set by hand only while NTP is off ...
        code, out, err = _run(["timedatectl", "set-time", stamp], 10)
        _run(["timedatectl", "set-ntp", "true"], 10)               # ... and it takes over again as soon as there is internet
    return code == 0, err


def sync_time_from_client(ms, tz=""):
    if not CFG["time_from_browser"]:
        return "off"
    try:
        client = float(ms) / 1000.0
    except (TypeError, ValueError):
        return "invalid"
    if not (1704067200 <= client <= 4102444800):             # 2024 .. 2100: anything else is not a real clock
        return "invalid"
    msgs = [m for m in [_set_timezone(tz)] if m]
    now = time.time(); diff = client - now
    if abs(diff) < 60:
        STATE["time_status"] = "ok" + (" · " + msgs[0] if msgs else ""); return STATE["time_status"]
    if _ntp_synced():
        STATE["time_status"] = "set by the internet (NTP)"; return STATE["time_status"]
    if now - TIME["last"] < 120:
        return "wait"
    TIME["last"] = now
    ok, err = _set_clock(client)
    if ok:
        log_event("sys", f"Clock set from the phone ({'+' if diff > 0 else '-'}{abs(diff) / 60:.0f} min): now {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        STATE["time_status"] = "taken from the phone " + datetime.now().strftime("%H:%M")
    else:
        STATE["time_status"] = "could not set the clock: " + _perm_hint(err)[:120]
    return STATE["time_status"]


# ----------------------------------------------------------------------------
# Armed / disarmed: alarms (push, browser sound, relays, recordings) only while armed. Arming waits a moment first,
# so you can walk away without alarming yourself.
# ----------------------------------------------------------------------------
ARM = {"at": 0.0, "announced": True}


def is_armed():
    return bool(CFG["armed"]) and time.time() >= ARM["at"]


def arm(delay=None):
    try:
        d = float(CFG["arm_delay"] if delay is None else delay)
    except (TypeError, ValueError):
        d = 60.0
    d = max(0.0, min(600.0, d))
    CFG["armed"] = True; ARM["at"] = time.time() + d; ARM["announced"] = d <= 0
    sched_user_changed("armed"); save_settings()
    log_event("sys", f"Armed in {d:.0f} s" if d else "Armed")
    arm_tick()


def disarm():
    CFG["armed"] = False; ARM["at"] = 0.0; ARM["announced"] = True
    sched_user_changed("armed"); save_settings()
    log_event("sys", "Disarmed - no alarms")
    arm_tick()


def arm_tick():
    left = max(0, int(ARM["at"] - time.time() + 0.99)) if CFG["armed"] else 0
    STATE["arm_state"] = "disarmed" if not CFG["armed"] else ("arming" if left > 0 else "armed")
    STATE["arm_left"] = left
    if CFG["armed"] and left == 0 and not ARM["announced"]:
        ARM["announced"] = True
        log_event("sys", "Armed now - alarms are active")
        push_alert("armed", "armed")


# ----------------------------------------------------------------------------
# Camping profile: one switch for the field. Own Wi-Fi on, the camera stays where it is (zones are drawn on the picture,
# a moving camera would move them), alarms + recordings on, armed after the countdown. Ending it restores everything.
# ----------------------------------------------------------------------------
CAMPING_SET = {"detection_on": True, "record": True, "snapshot_on_person": True, "notify_on": True, "notify_prealarm": True,
               "browser_alarm": True, "relays_on": True, "patrol": False, "track_person": False, "timelapse_on": False,
               "lowlight_auto": True, "rain_auto": True, "wind_auto": True, "show_zones": True}


def camping_set(on, hotspot_delay=2.0):
    netauto_pause()
    if on and not CFG["camping"]:
        prev = {k: CFG[k] for k in list(CAMPING_SET) + ["thermal_alarm", "armed", "hotspot_on"]}
        CFG["camping_prev"] = prev
        for k, v in CAMPING_SET.items():
            CFG[k] = v; sched_user_changed(k)
        if CFG["thermal_source"]:
            CFG["thermal_alarm"] = True
        CFG["camping"] = True
        log_event("sys", "Camping profile ON")
        arm()
        if wifi_backend() == "nm" and not STATE["hotspot"].get("on"):
            hotspot_switch_later(True, hotspot_delay)
    elif not on and CFG["camping"]:
        prev = CFG["camping_prev"] if isinstance(CFG["camping_prev"], dict) else {}
        for k, v in prev.items():
            if k in CFG and k not in ("armed", "hotspot_on") and isinstance(v, type(CFG[k])):
                CFG[k] = v
        CFG["camping"] = False; CFG["camping_prev"] = {}
        log_event("sys", "Camping profile OFF - previous settings restored")
        if prev.get("armed", True):
            CFG["armed"] = True; ARM["at"] = 0.0; ARM["announced"] = True; arm_tick()
        else:
            disarm()
        if not prev.get("hotspot_on", False) and STATE["hotspot"].get("on"):
            hotspot_switch_later(False, hotspot_delay)
    save_settings()
    return True, ""


# ----------------------------------------------------------------------------
# Autostart: when switched on, the Pi starts Motion Watch when it boots (no screen needed) and switches the own Wi-Fi on.
# When switched off, nothing starts at boot and the Pi joins its known networks as usual (the own Wi-Fi never starts by itself).
#   normal user: systemd USER service  ~/.config/systemd/user/motionwatch.service  (+ "linger" so it starts without login)
#   root (sudo): systemd system service /etc/systemd/system/motionwatch.service
# ----------------------------------------------------------------------------
SERVICE_NAME = "motionwatch.service"
AUTOSTART = {"on": False, "mode": "", "msg": "", "path": ""}


def _is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _run_user():
    import getpass
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or getpass.getuser()


def _unit_path(mode):
    if mode == "system":
        return "/etc/systemd/system/" + SERVICE_NAME
    return os.path.join(os.path.expanduser("~"), ".config", "systemd", "user", SERVICE_NAME)


def _autostart_mode():
    return "system" if (_is_root() or os.path.isfile(_unit_path("system"))) else "user"


def _systemctl(mode, *args, timeout=30):
    return _run(["systemctl"] + (["--user"] if mode == "user" else []) + list(args), timeout)


def autostart_args():
    """The options this program was started with, for the service (without one-time actions), plus --headless --boot."""
    drop = {"--print-service", "--install-service", "--allow-wifi", "--boot", "--headless", "--no-web", "--web"}
    return [x for x in sys.argv[1:] if x not in drop] + ["--headless", "--boot"]


def autostart_unit(mode):
    import shlex
    exe = " ".join(shlex.quote(x) for x in [sys.executable, os.path.abspath(__file__)] + autostart_args())
    if mode == "system":
        head = "[Unit]\nDescription=Motion Watch (camera surveillance)\nAfter=network.target NetworkManager.service\nWants=NetworkManager.service\n\n"
        install = "WantedBy=multi-user.target"
    else:
        head = "[Unit]\nDescription=Motion Watch (camera surveillance)\n\n"
        install = "WantedBy=default.target"
    return (head + "[Service]\nType=simple\n" + f"WorkingDirectory={HERE}\nExecStart={exe}\n"
            + f"Environment=PYTHONUNBUFFERED=1\nEnvironment=MOTIONWATCH_HOME={DATA_DIR}\n"
            + "Restart=on-failure\nRestartSec=5\n\n[Install]\n" + install + "\n")


def autostart_refresh():
    mode = _autostart_mode()
    path = _unit_path(mode)
    code, out, _e = _systemctl(mode, "is-enabled", SERVICE_NAME, timeout=10)
    AUTOSTART.update(on=out.strip() == "enabled", mode=mode, path=path if os.path.isfile(path) else "")
    STATE["autostart"] = dict(AUTOSTART)
    return STATE["autostart"]


def autostart_set(on):
    if shutil.which("systemctl") is None:
        return False, "autostart needs systemd (Raspberry Pi OS)"
    mode = _autostart_mode()
    path = _unit_path(mode)
    if mode == "system" and not _is_root():
        if on:
            return False, "a system service exists - change it with sudo, or remove it: sudo systemctl disable --now motionwatch"
        code, out, err = _systemctl(mode, "disable", SERVICE_NAME)
        ok = code == 0
        msg = "" if ok else "the system service can only be switched off with sudo: sudo systemctl disable motionwatch"
    elif on:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(autostart_unit(mode))
            os.chmod(path, 0o600)                         # the web password may be in the command line
        except OSError as e:
            return False, f"could not write {path}: {e}"
        _systemctl(mode, "daemon-reload")
        code, out, err = _systemctl(mode, "enable", SERVICE_NAME)
        ok, msg = code == 0, "" if code == 0 else (err or "systemctl enable failed")[:200]
        if ok and mode == "user":                         # start at boot even when nobody logs in
            c2, o2, e2 = _run(["loginctl", "enable-linger", _run_user()], 15)
            if c2 != 0:
                msg = ("autostart is on, but it only starts after a login until you run once: "
                       f"sudo loginctl enable-linger {_run_user()}   (or: sudo python3 {os.path.basename(__file__)} --allow-wifi)")
    else:
        code, out, err = _systemctl(mode, "disable", SERVICE_NAME)
        ok, msg = code == 0, "" if code == 0 else (err or "systemctl disable failed")[:200]
    if ok:
        CFG["autostart"] = on; save_settings()
        log_event("sys", "Autostart ON: starts at boot and switches the own Wi-Fi on" if on else
                         "Autostart OFF: nothing starts at boot, the Pi joins its known networks")
    AUTOSTART["msg"] = msg
    autostart_refresh()
    return ok, msg


def autostart_follow_version():
    """A new version was started by hand while autostart is on: let the service start this file from now on."""
    if not CFG["autostart"]:
        return
    mode = _autostart_mode()
    path = _unit_path(mode)
    if mode == "system" and not _is_root():
        return
    try:
        with open(path) as f:
            old = f.read()
    except OSError:
        return
    if os.path.abspath(__file__) not in old:
        try:
            with open(path, "w") as f:
                f.write(autostart_unit(mode))
            os.chmod(path, 0o600)
            _systemctl(mode, "daemon-reload")
            log_event("sys", f"Autostart now starts this version: {os.path.basename(__file__)}")
        except OSError:
            pass


def boot_hotspot():
    """Started at boot (--boot): switch the own Wi-Fi on. NetworkManager may still be starting, so try a few times."""
    def work():
        time.sleep(3.0)
        for attempt in range(8):
            ok, err = hotspot_set(True, persist=False)
            if ok:
                return
            WIFI["hs_msg"] = err
            time.sleep(10.0)
        log_event("sys", "Own Wi-Fi could not be switched on at boot")
    threading.Thread(target=work, daemon=True).start()


# ----------------------------------------------------------------------------
# Network automatic: known networks first (e.g. the phone hotspot = internet + push messages), otherwise the own Wi-Fi.
#   start / connection lost: wait auto_wait seconds for a known network, then switch the own Wi-Fi on
#   own Wi-Fi on: every auto_retry minutes look for known networks again - only when no device is connected to the Pi
#   switching by hand (hotspot switch, camping profile) pauses the automatic until the network mode is chosen again
# Timers use time.monotonic(): the clock may jump when it is taken from the phone.
# ----------------------------------------------------------------------------
NETAUTO = {"paused": False, "status": "off"}
NETAUTO_SEARCH = 45.0                                   # seconds the own Wi-Fi stays off while known networks are tried


def netauto_pause():
    if CFG["net_mode"] == "auto" and not NETAUTO["paused"]:
        NETAUTO["paused"] = True
        log_event("sys", "Network automatic paused (switched by hand) - choose the network mode again to resume")


class NetAuto:
    def __init__(self):
        self.lost_since = None; self.next_retry = None
        threading.Thread(target=self.loop, daemon=True).start()

    def _set(self, status):
        if status != NETAUTO["status"]:
            NETAUTO["status"] = status
        STATE["netauto"] = status

    def wait_connected(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            time.sleep(1.0)
            w = STATE["wifi"] or {}
            if w.get("connected") and not STATE["hotspot"].get("on"):
                return w.get("ssid") or "?"
        return ""

    def step(self):
        if CFG["net_mode"] != "auto":
            self.lost_since = None; self.next_retry = None; self._set("off"); return
        if wifi_backend() != "nm":
            self._set("needs NetworkManager"); return
        if NETAUTO["paused"]:
            self._set("paused (switched by hand)"); return
        if WIFI["busy"] or WIFI.get("hs_busy"):
            return
        now = time.monotonic()
        hs, w = STATE["hotspot"] or {}, STATE["wifi"] or {}
        retry = max(0.0, float(CFG["auto_retry"])) * 60.0
        if hs.get("on"):
            self.lost_since = None
            if retry <= 0:
                self._set("own Wi-Fi on"); return
            if self.next_retry is None:
                self.next_retry = now + retry
            if now < self.next_retry:
                self._set(f"own Wi-Fi on - next search in {max(1, int((self.next_retry - now) / 60 + 0.99))} min"); return
            if hs.get("clients", 0) > 0:
                self.next_retry = now + min(60.0, retry)
                self._set("own Wi-Fi on - search postponed (a device is connected)"); return
            self._set("searching known networks …")
            log_event("sys", "Network automatic: own Wi-Fi off for a moment, looking for known networks")
            hotspot_set(False, persist=False); hotspot_refresh()
            ssid = self.wait_connected(NETAUTO_SEARCH)
            if ssid:
                self.next_retry = None
                log_event("sys", f"Network automatic: connected with «{ssid}»")
                self._set(f"connected with «{ssid}»")
            else:
                hotspot_set(True, persist=False); hotspot_refresh()
                self.next_retry = time.monotonic() + retry
                log_event("sys", "Network automatic: no known network - own Wi-Fi on again")
            return
        if w.get("connected"):
            self.lost_since = None; self.next_retry = None
            self._set(f"connected with «{w.get('ssid') or '?'}»"); return
        if self.lost_since is None:
            self.lost_since = now
        left = float(CFG["auto_wait"]) - (now - self.lost_since)
        if left > 0:
            self._set(f"no known network - own Wi-Fi in {int(left + 0.99)} s"); return
        log_event("sys", "Network automatic: no known network - switching the own Wi-Fi on")
        ok, err = hotspot_set(True, persist=False); hotspot_refresh()       # state at once, not 2 s later
        self.lost_since = None; self.next_retry = time.monotonic() + retry
        self._set("own Wi-Fi on" if ok else "own Wi-Fi failed: " + err[:100])

    def loop(self):
        while True:
            time.sleep(2.0)
            try:
                self.step()
            except Exception as e:
                self._set("error: " + str(e)[:100])


# ----------------------------------------------------------------------------
# Patrol: pendulum over waypoints  (1-2-3-2-1-2-3 ...)
# ----------------------------------------------------------------------------
class Patrol:
    def __init__(self):
        self.paused_until = 0
        threading.Thread(target=self.loop, daemon=True).start()

    def move_to(self, target):
        """Smoothly move pan to target at patrol_speed %/s; returns False if interrupted."""
        while abs(CFG["pan"] - target) > 0.5:
            if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                return False
            step = CFG["patrol_speed"] * 0.02
            CFG["pan"] = CFG["pan"] + max(-step, min(step, target - CFG["pan"]))
            time.sleep(0.02)
        CFG["pan"] = float(target)
        return True

    def loop(self):
        announced = False
        while True:
            if not CFG["patrol"] or len(WAYPOINTS) < 2:
                STATE["patrol_status"] = "off" if not CFG["patrol"] else "need 2+ waypoints"
                announced = False
                time.sleep(0.3); continue
            if STATE["tracking"]:
                STATE["patrol_status"] = "paused (tracking person)"
                time.sleep(0.2); continue
            if servo_hold():
                STATE["patrol_status"] = "paused (manual control)"
                time.sleep(0.2); continue
            if not announced:
                log_event("patrol", f"Patrol started over {len(WAYPOINTS)} waypoints: {[round(w) for w in WAYPOINTS]}")
                announced = True
            wps = list(WAYPOINTS)
            path = wps + wps[-2:0:-1]            # pendulum, no doubled end points
            for i, wp in enumerate(path):
                STATE["patrol_status"] = f"moving to waypoint {i + 1}/{len(path)} ({wp:.0f}%)"
                CFG["tilt"] = float(CFG["patrol_tilt"])
                if not self.move_to(wp):
                    break
                STATE["patrol_status"] = f"dwelling at {wp:.0f}%"
                t_end = time.time() + CFG["patrol_dwell"]
                while time.time() < t_end:
                    if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                        break
                    time.sleep(0.05)
                if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                    break


# ----------------------------------------------------------------------------
# AI person detector (SSD MobileNet V2, COCO class 1 = person)
# ----------------------------------------------------------------------------
class AIDetector:
    PB, PBTXT = "frozen_inference_graph.pb", "ssd_mobilenet_v2_coco.pbtxt"

    def __init__(self):
        self.net = None
        self.boxes = []          # last persons, in processing-frame coordinates
        self.objects = []        # last non-person objects (x, y, w, h, conf, cls)
        self.frame_counter = 0
        here = os.path.dirname(os.path.abspath(__file__))
        pb, pbtxt = os.path.join(here, self.PB), os.path.join(here, self.PBTXT)
        if os.path.exists(pb) and os.path.exists(pbtxt):
            try:
                self.net = cv2.dnn.readNetFromTensorflow(pb, pbtxt)
                STATE["ai_status"] = "ready"
                log_event("ai", "AI model SSD MobileNet V2 loaded")
            except Exception as e:
                STATE["ai_status"] = "load error"
                log_event("ai", f"AI model could not be loaded: {e}")
        else:
            CFG["ai_enabled"] = False
            STATE["ai_status"] = "no model files"
            log_event("ai", "AI off: frozen_inference_graph.pb / ssd_mobilenet_v2_coco.pbtxt not found next to the script")

    def detect(self, frame):
        """Run every N frames; returns list of (x, y, w, h, conf) persons."""
        if self.net is None or not CFG["ai_enabled"]:
            STATE["ai_status"] = "off" if self.net else STATE["ai_status"]
            self.boxes = []; self.objects = []
            return self.boxes
        self.frame_counter += 1
        if self.frame_counter % max(1, int(CFG["ai_every"])) != 0:
            return self.boxes
        t0 = time.time()
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
        self.net.setInput(blob)
        det = self.net.forward()
        boxes, objects = [], []
        for i in range(det.shape[2]):
            cls, conf = int(det[0, 0, i, 1]), float(det[0, 0, i, 2])
            need = CFG["ai_conf"] if cls == 1 else CFG["object_conf"]
            if cls < 1 or conf < need:
                continue
            x1, y1, x2, y2 = (det[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
            x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(w - 1, x2), min(h - 1, y2)
            if x2 > x1 and y2 > y1:
                if cls == 1:
                    boxes.append((x1, y1, x2 - x1, y2 - y1, conf))
                else:
                    objects.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1), conf, cls))
        self.boxes = boxes; self.objects = objects
        STATE["ai_ms"] = int((time.time() - t0) * 1000)
        STATE["ai_status"] = f"running · {STATE['ai_ms']} ms"
        STATE["ai_persons"] = len(boxes)
        return boxes


# COCO class ids used by SSD MobileNet V2 (TensorFlow 91-id label map)
COCO_LABELS = {
    1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane", 6: "bus", 7: "train", 8: "truck",
    9: "boat", 10: "traffic light", 11: "fire hydrant", 13: "stop sign", 14: "parking meter", 15: "bench",
    16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow", 22: "elephant", 23: "bear",
    24: "zebra", 25: "giraffe", 27: "backpack", 28: "umbrella", 31: "handbag", 32: "tie", 33: "suitcase",
    34: "frisbee", 35: "skis", 36: "snowboard", 37: "sports ball", 38: "kite", 39: "baseball bat",
    40: "baseball glove", 41: "skateboard", 42: "surfboard", 43: "tennis racket", 44: "bottle",
    46: "wine glass", 47: "cup", 48: "fork", 49: "knife", 50: "spoon", 51: "bowl", 52: "banana",
    53: "apple", 54: "sandwich", 55: "orange", 56: "broccoli", 57: "carrot", 58: "hot dog", 59: "pizza",
    60: "donut", 61: "cake", 62: "chair", 63: "couch", 64: "potted plant", 65: "bed", 67: "dining table",
    70: "toilet", 72: "tv", 73: "laptop", 74: "mouse", 75: "remote", 76: "keyboard", 77: "cell phone",
    78: "microwave", 79: "oven", 80: "toaster", 81: "sink", 82: "refrigerator", 84: "book", 85: "clock",
    86: "vase", 87: "scissors", 88: "teddy bear", 89: "hair drier", 90: "toothbrush",
}


# ----------------------------------------------------------------------------
# Relays: each one Off / On / Auto. Auto = on while its trigger is in view (+ hold time)
# ----------------------------------------------------------------------------
TRIGGERS = (["person", "motion", "prealarm", "warm", "animal", "cat", "dog", "bird", "car", "truck", "bicycle", "motorcycle", "bus"]
            + sorted(set(COCO_LABELS.values()) - {"person", "cat", "dog", "bird", "car", "truck", "bicycle", "motorcycle", "bus"}))
ANIMALS = {COCO_LABELS[i] for i in range(16, 26)}
TRIGGER_EN = {"motion": "motion (anything)", "prealarm": "pre-alarm (any movement)", "warm": "warm body (thermal camera)", "animal": "animal (any)"}
RELAY_NOTE = ("Auto: the relay switches on while its trigger is in view and stays on for the hold time. "
              "Animal and object triggers (e.g. cat) need the AI model. "
              "Pre-alarm switches on at the first movement in the picture, long before a person is confirmed.")


def tr_trigger(key, lang=None):
    return tr(TRIGGER_EN.get(key, key), lang)


def _clean_relay(r, i, used):
    """Validate one relay loaded from the settings file. Returns None if no GPIO is left."""
    out = {"name": f"Relay {i + 1}", "gpio": None, "mode": "off", "trigger": "person", "hold": 5.0, "active_low": False}
    if isinstance(r.get("name"), str) and r["name"].strip():
        out["name"] = r["name"].strip()[:24]
    g = r.get("gpio")
    if isinstance(g, int) and 2 <= g <= 27 and g not in GPIO_RESERVED and g not in used:
        out["gpio"] = g
    else:
        out["gpio"] = next((x for x in FREE_GPIOS if x not in used and x not in GPIO_RESERVED), None)
    if out["gpio"] is None:
        return None
    if r.get("mode") in ("off", "on", "auto"):
        out["mode"] = r["mode"]
    if r.get("trigger") in TRIGGERS:
        out["trigger"] = r["trigger"]
    try:
        h = float(r.get("hold", 5.0))
        if math.isfinite(h):
            out["hold"] = max(0.5, min(600.0, h))
    except (TypeError, ValueError):
        pass
    out["active_low"] = bool(r.get("active_low", False))
    return out


def relay_update(idx, field, value):
    """Validated change of one relay setting (desktop + web). Returns (ok, error_message)."""
    if not (isinstance(idx, int) and 0 <= idx < len(RELAYS)):
        return False, "unknown relay"
    r = RELAYS[idx]
    if field == "name":
        v = str(value).strip()[:24] or f"Relay {idx + 1}"
    elif field == "gpio":
        try:
            v = int(float(value))
        except (TypeError, ValueError):
            return False, "GPIO must be a number"
        if not 2 <= v <= 27:
            return False, "GPIO must be between 2 and 27"
        if v in GPIO_RESERVED:
            return False, f"GPIO {v} is used by a servo"
        if any(i != idx and o["gpio"] == v for i, o in enumerate(RELAYS)):
            return False, f"GPIO {v} is already used by another relay"
    elif field == "mode":
        if value not in ("off", "on", "auto"):
            return False, "mode must be off / on / auto"
        v = value
    elif field == "trigger":
        if value not in TRIGGERS:
            return False, "unknown trigger"
        v = value
    elif field == "hold":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False, "hold time must be a number"
        if not math.isfinite(v):
            return False, "hold time must be a number"
        v = max(0.5, min(600.0, v))
    elif field == "active_low":
        v = bool(value)
    else:
        return False, "unknown field"
    if r.get(field) == v:
        return True, ""
    with LOCK:
        r[field] = v
    if field in ("mode", "trigger", "gpio"):
        log_event("servo", f"{r['name']}: {field} -> {v}")
    save_settings()
    return True, ""


def relay_add():
    if len(RELAYS) >= MAX_RELAYS:
        return False, f"maximum {MAX_RELAYS} relays"
    used = {r["gpio"] for r in RELAYS}
    gpio = next((g for g in FREE_GPIOS if g not in used and g not in GPIO_RESERVED), None)
    if gpio is None:
        return False, "no free GPIO left"
    new = {"name": f"Relay {len(RELAYS) + 1}", "gpio": gpio, "mode": "off", "trigger": "cat", "hold": 10.0, "active_low": False}
    with LOCK:
        RELAYS.append(new)
    log_event("servo", f"{new['name']} added on GPIO{gpio}")
    save_settings()
    return True, ""


def relay_remove(idx):
    if not (isinstance(idx, int) and 0 <= idx < len(RELAYS)):
        return False, "unknown relay"
    with LOCK:
        r = RELAYS.pop(idx)
    log_event("servo", f"{r['name']} (GPIO{r['gpio']}) removed")
    save_settings()
    return True, ""


class RelayManager:
    """Decides every frame which relay is on: mode On / Off, or Auto = trigger in view (+ hold time)."""
    def __init__(self):
        self.last_seen = {}; self.was_on = {}

    def update(self, present):
        now = time.time()
        with LOCK:
            relays = list(RELAYS)
        states, out = [], []
        for r in relays:
            k = id(r)
            if r["mode"] == "on":
                on = True
            elif r["mode"] == "auto":
                if not CFG["relays_on"] or not is_armed():
                    on = False
                else:
                    if r["trigger"] in present:
                        self.last_seen[k] = now
                    on = now - self.last_seen.get(k, 0.0) < r["hold"]
            else:
                on = False
            if on != self.was_on.get(k, False):
                why = tr_trigger(r["trigger"], "en") if r["mode"] == "auto" else r["mode"]
                log_event("servo", f"{r['name']} (GPIO{r['gpio']}) {'ON' if on else 'OFF'} ({why})")
            self.was_on[k] = on
            states.append(on); out.append((r["gpio"], on, bool(r["active_low"])))
        STATE["relay_states"] = states
        STATE["relay_out"] = out
        STATE["relay"] = bool(states and states[0])




def class_color(cls):
    """Stable BGR colour per class. Hues avoid red, which is reserved for persons."""
    hsv = np.uint8([[[30 + (int(cls) * 37) % 110, 210, 255]]])
    b, g, r = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(b), int(g), int(r)


def draw_object(frame, obj, sx, sy):
    """Box + label for a generic detected object. obj = (x, y, w, h, conf, cls) in processing coords."""
    x, y, w, h, conf, cls = obj
    X, Y, BW, BH = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
    col = class_color(cls)
    cv2.rectangle(frame, (X, Y), (X + BW, Y + BH), col, 2)
    label = f"{COCO_LABELS.get(cls, 'object')} {int(conf * 100)}%"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(0, Y - th - 8)
    cv2.rectangle(frame, (X, top), (X + tw + 6, top + th + 8), col, -1)
    cv2.putText(frame, label, (X + 3, top + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


def draw_outline(frame, contours, box, sx, sy, color, thickness):
    """Draw the silhouette contours that lie inside `box` (processing coords) onto the full frame."""
    x, y, w, h = box[:4]
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cx + cw / 2 >= x and cx + cw / 2 <= x + w and cy + ch / 2 >= y and cy + ch / 2 <= y + h:
            pts = (c.reshape(-1, 2) * np.array([sx, sy])).astype(np.int32)
            cv2.polylines(frame, [pts], True, color, thickness, cv2.LINE_AA)


def merge_boxes(boxes, gap_x=12, gap_y=30):
    """Union boxes that touch or nearly touch (a person often splits into head/torso/legs)."""
    boxes = [list(b[:4]) for b in boxes]
    merged = True
    while merged and len(boxes) > 1:
        merged = False
        out = []
        while boxes:
            a = boxes.pop(0)
            i = 0
            while i < len(boxes):
                b = boxes[i]
                if (a[0] - gap_x < b[0] + b[2] and b[0] - gap_x < a[0] + a[2] and
                        a[1] - gap_y < b[1] + b[3] and b[1] - gap_y < a[1] + a[3]):
                    x1, y1 = min(a[0], b[0]), min(a[1], b[1])
                    x2, y2 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
                    a = [x1, y1, x2 - x1, y2 - y1]; boxes.pop(i); merged = True
                else:
                    i += 1
            out.append(a)
        boxes = out
    return [tuple(int(v) for v in b) for b in boxes]


def iou(a, b):
    ax, ay, aw, ah = a[:4]; bx, by, bw, bh = b[:4]
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx)); iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    return inter / float(aw * ah + bw * bh - inter + 1e-6)


# ----------------------------------------------------------------------------
# Weather analysis
# ----------------------------------------------------------------------------
class WeatherAnalyzer:
    def __init__(self):
        self.prev_gray = None
        self.rain_hist = deque(maxlen=30)
        self.wind_hist = deque(maxlen=45)

    def rain(self, gray):
        if self.prev_gray is None:
            self.prev_gray = gray
            return 0.0
        diff = cv2.absdiff(gray, self.prev_gray)
        self.prev_gray = gray
        _, th = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        hk = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        streaks = cv2.subtract(cv2.morphologyEx(th, cv2.MORPH_OPEN, vk), cv2.morphologyEx(th, cv2.MORPH_OPEN, hk))
        n, _, stats, _ = cv2.connectedComponentsWithStats(streaks, 8)
        if n <= 1:
            score = 0.0
        else:
            areas = stats[1:, cv2.CC_STAT_AREA]
            tiny = np.sum((areas >= 3) & (areas <= 60))
            h, w = gray.shape
            cells = np.zeros((4, 4), np.uint8)
            cx = stats[1:, cv2.CC_STAT_LEFT] * 4 // w; cy = stats[1:, cv2.CC_STAT_TOP] * 4 // h
            cells[np.clip(cy, 0, 3), np.clip(cx, 0, 3)] = 1
            score = min(1.0, tiny / 160.0) * (0.4 + 0.6 * cells.mean())
        self.rain_hist.append(score)
        return float(np.mean(self.rain_hist))

    def wind(self, fg_mask, person_boxes):
        mask = fg_mask.copy()
        for (x, y, w, h) in person_boxes:
            mask[y:y + h, x:x + w] = 0
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if n <= 1:
            score = 0.0
        else:
            areas = stats[1:, cv2.CC_STAT_AREA]
            small = areas[(areas >= 8) & (areas <= 900)]
            score = min(1.0, small.sum() / float(mask.size) * 25.0 + len(small) / 220.0)
        self.wind_hist.append(score)
        return float(np.mean(self.wind_hist))


# ----------------------------------------------------------------------------
# Auto-tuner
# ----------------------------------------------------------------------------
class AutoTuner:
    def __init__(self):
        self.reset()

    def reset(self):
        self.t_start = time.time(); self.calibrated = False
        self.noise_areas, self.noise_frac = [], []
        self.last_eval = time.time()
        self.new_candidates = self.became_person = self.near_miss = 0
        self.seen_ids = set()
        STATE["auto_status"] = "calibrating…"
        log_event("auto", "Auto-tune: calibrating - keep the scene empty for a few seconds")

    @staticmethod
    def _set(key, value, why):
        value = round(value, 2) if isinstance(CFG[key], float) else int(value)
        if value != CFG[key]:
            old = CFG[key]; CFG[key] = value
            STATE["auto_changes"] += 1
            log_event("auto", f"Auto-tune: {key} {old} -> {value} ({why})")

    def observe(self, fg, tracks, persons, fps):
        if not CFG["auto_tune"]:
            STATE["auto_status"] = "off"; return
        now = time.time()
        if fps > 1:
            self._set("walk_frames", max(4, min(24, round(fps * CFG["walk_seconds"]))), "fps")
        if not self.calibrated:
            n, _, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
            if n > 1:
                self.noise_areas.extend(stats[1:, cv2.CC_STAT_AREA].tolist())
            self.noise_frac.append(np.count_nonzero(fg) / float(fg.size))
            left = CFG["calib_seconds"] - (now - self.t_start)
            STATE["auto_status"] = f"calibrating… {max(0, left):.0f}s"
            if left <= 0:
                self.calibrated = True
                if self.noise_areas:
                    self._set("min_area", max(600, min(4000, float(np.percentile(self.noise_areas, 95)) * 2.5)), "scene noise")
                frac = float(np.mean(self.noise_frac)) if self.noise_frac else 0.0
                if frac > 0.02:
                    self._set("sensitivity", max(10, CFG["sensitivity"] - 20), "noisy scene")
                elif frac < 0.001:
                    self._set("sensitivity", min(90, CFG["sensitivity"] + 10), "very quiet scene")
                STATE["auto_status"] = "tuned"
                log_event("auto", "Auto-tune: calibration done, now adjusting live")
            return
        for t in tracks:
            if t.id not in self.seen_ids:
                self.seen_ids.add(t.id); self.new_candidates += 1
            if t.is_person and not getattr(t, "_counted", False):
                t._counted = True; self.became_person += 1
            if (not t.is_person and not t.is_vehicle and t.age >= CFG["walk_frames"]
                    and CFG["walk_min_speed"] <= t.speed() <= CFG["walk_max_speed"]
                    and 0.3 <= t.steadiness() < CFG["speed_consistency"]):
                self.near_miss += 1
        if now - self.last_eval < 10:
            return
        minutes = (now - self.last_eval) / 60.0
        self.last_eval = now
        false_rate = (self.new_candidates - self.became_person) / minutes
        if not persons:
            if false_rate > 25:
                self._set("min_area", min(8000, CFG["min_area"] * 1.2), f"{false_rate:.0f} false blobs/min")
            elif false_rate > 12:
                self._set("sensitivity", max(10, CFG["sensitivity"] - 5), "many false blobs")
            elif false_rate < 2 and self.became_person == 0:
                self._set("min_area", max(500, CFG["min_area"] * 0.93), "scene calm, more sensitive")
        if self.near_miss > 20 and self.became_person == 0:
            self._set("speed_consistency", max(0.3, CFG["speed_consistency"] - 0.05), "steady walkers not passing")
        elif self.became_person > 0 and false_rate < 5:
            self._set("speed_consistency", min(0.7, CFG["speed_consistency"] + 0.02), "persons detected, tightening")
        STATE["auto_status"] = f"tuned · {false_rate:.0f} false/min"
        self.new_candidates = self.became_person = self.near_miss = 0


# ----------------------------------------------------------------------------
# Tracker
# ----------------------------------------------------------------------------
class Track:
    _next = 1

    def __init__(self, box):
        self.id = Track._next; Track._next += 1
        self.box = box
        self.hist = deque(maxlen=40); self.speeds = deque(maxlen=40)
        self.hist.append(self.center())
        self.lost = 0; self.age = 0
        self.is_person = self.is_vehicle = self.ai_confirmed = False

    def center(self):
        x, y, w, h = self.box
        return (x + w / 2.0, y + h / 2.0)

    def update(self, box):
        old = self.center(); self.box = box; c = self.center()
        self.hist.append(c); self.speeds.append(math.hypot(c[0] - old[0], c[1] - old[1]))
        self.lost = 0; self.age += 1

    def speed(self):
        return float(np.mean(self.speeds)) if self.speeds else 0.0

    def steadiness(self):
        if len(self.speeds) < 4:
            return 0.0
        sp = np.array(self.speeds)
        if sp.mean() < 1e-3:
            return 0.0
        cv = sp.std() / sp.mean()
        pts = np.array(self.hist)
        path = np.sum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))) + 1e-6
        net = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
        return float(max(0.0, 1.0 - cv * 0.6) * (0.3 + 0.7 * net / path))


class Tracker:
    def __init__(self):
        self.tracks = []

    def update(self, boxes, max_dist=60):
        unmatched = list(range(len(boxes)))
        for t in self.tracks:
            best, bd = None, max_dist
            tc = t.center()
            for i in unmatched:
                x, y, w, h = boxes[i]
                d = math.hypot(x + w / 2 - tc[0], y + h / 2 - tc[1])
                if d < bd:
                    best, bd = i, d
            if best is not None:
                t.update(boxes[best]); unmatched.remove(best)
            else:
                t.lost += 1
        for i in unmatched:
            self.tracks.append(Track(boxes[i]))
        self.tracks = [t for t in self.tracks if t.lost < 8]
        return self.tracks


# ----------------------------------------------------------------------------
# Main detector
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Video sources
#   usb:<n>   USB / V4L2 webcams (/dev/video<n>)        pi:<n>   Raspberry Pi CSI cameras (picamera2)
#   url:<id>  network cameras: RTSP / HTTP-MJPEG (IP cams, Wi-Fi cams) saved in the settings
#   auto      first working USB camera (the behaviour of the older versions)
# Every source object offers read() -> (ok, BGR frame) and release(), so the main loop does not care where the picture comes from.
# ----------------------------------------------------------------------------
SRC_RE = re.compile(r"^(auto|usb:\d{1,2}|pi:\d{1,2}|url:[0-9a-f]{8})$")
MAX_IP_SOURCES = 16
V4L_SKIP = ("bcm2835-codec", "bcm2835-isp", "rpivid", "pispbe", "rp1-cfe", "hevc", "-decoder", "-encoder")   # Pi internal nodes, no cameras
SOURCES = {"items": [], "time": 0.0, "scanning": False, "hints": []}      # result of the last scan
_SCAN_LOCK = threading.Lock()


def _url_ok(u):
    return isinstance(u, str) and len(u) <= 500 and re.match(r"^(rtsp|rtsps|http|https)://[^\s]+$", u, re.I) is not None


def mask_url(u):
    """rtsp://user:secret@host/x -> rtsp://user:***@host/x  (passwords are never shown or sent to the browser)."""
    return re.sub(r"(://[^/@:\s]+):[^/@\s]*@", r"\1:***@", u or "")


def _clean_ip_sources(lst):
    out, seen = [], set()
    for s in (lst if isinstance(lst, list) else [])[:MAX_IP_SOURCES]:
        if not isinstance(s, dict):
            continue
        sid, url = str(s.get("id", "")), str(s.get("url", "")).strip()
        if not re.fullmatch(r"[0-9a-f]{8}", sid) or sid in seen or not _url_ok(url):
            continue
        seen.add(sid)
        out.append({"id": sid, "name": str(s.get("name") or "").strip()[:40] or "Network camera", "url": url})
    return out


def find_ip_source(sid):
    for s in CFG["ip_sources"]:
        if s["id"] == sid:
            return s
    return None


class CvSource:
    """A camera read through OpenCV (USB webcam or network stream)."""
    def __init__(self, cap, size=None):
        self.cap = cap; self.size = size

    def read(self):
        return self.cap.read()

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass


class PiCamSource:
    """Raspberry Pi camera (CSI) through picamera2 / libcamera."""
    def __init__(self, index):
        from picamera2 import Picamera2                     # ImportError -> "not installed" message
        self.cam = Picamera2(index)
        self.cam.configure(self.cam.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"}))
        self.cam.start()
        self.size = (1280, 720)

    def read(self):
        try:
            return True, self.cam.capture_array("main")     # "RGB888" is delivered in B,G,R order = what OpenCV expects
        except Exception:
            return False, None

    def release(self):
        for fn in ("stop", "close"):
            try:
                getattr(self.cam, fn)()
            except Exception:
                pass


def _open_usb(idx, raw=False):
    """raw=True for thermal cameras: they have their own small resolution and formats, so nothing is forced on them."""
    for backend, name in ((cv2.CAP_V4L2, "V4L2"), (cv2.CAP_ANY, "default")):
        cap = cv2.VideoCapture(idx, backend)
        if cap.isOpened():
            if not raw:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, frame = cap.read()
            if ok:
                return CvSource(cap, (frame.shape[1], frame.shape[0]))
        cap.release()
    return None


def _open_url(url):
    if url.lower().startswith("rtsp"):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")     # TCP is far more reliable over Wi-Fi
    cap = None
    try:                                                    # connect / read time-outs (OpenCV >= 4.5.2)
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 8000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 8000])
    except Exception:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    ok, frame = cap.read() if cap.isOpened() else (False, None)
    if not ok:
        cap.release()
        return None
    return CvSource(cap, (frame.shape[1], frame.shape[0]))


def source_label(spec):
    kind, _, arg = spec.partition(":")
    if kind == "usb":
        return f"USB camera {arg}"
    if kind == "pi":
        return f"Pi camera {arg}"
    if kind == "url":
        s = find_ip_source(arg)
        return s["name"] if s else "Network camera"
    return "Automatic"


def open_source(spec, thermal=False):
    """Open a source (may block for seconds - always call from a background thread). thermal=True opens USB cameras unforced.
    Returns (source or None, resolved id, label, error text)."""
    label = source_label(spec)
    try:
        kind, _, arg = spec.partition(":")
        if spec == "auto":
            for idx in range(4):
                src = _open_usb(idx)
                if src:
                    return src, f"usb:{idx}", f"USB camera {idx}", ""
            return None, spec, label, "no working USB camera found (ls /dev/video*)"
        if kind == "usb":
            src = (_open_usb(int(arg), raw=True) or _open_usb(int(arg))) if thermal else _open_usb(int(arg))
            return (src, spec, label, "") if src else (None, spec, label, f"no picture from /dev/video{arg}")
        if kind == "pi":
            return PiCamSource(int(arg)), spec, label, ""
        if kind == "url":
            s = find_ip_source(arg)
            if not s:
                return None, spec, label, "unknown network camera"
            src = _open_url(s["url"])
            return (src, spec, label, "") if src else (None, spec, label, "no picture from " + mask_url(s["url"]))
        return None, spec, label, "unknown source"
    except ImportError:
        return None, spec, label, "picamera2 not installed (sudo apt install python3-picamera2)"
    except Exception as e:
        return None, spec, label, str(e)[:160]


def _v4l_name(idx):
    try:
        with open(f"/sys/class/video4linux/video{idx}/name") as f:
            return f.read().strip()
    except OSError:
        return ""


def _is_pi():
    try:
        with open("/proc/device-tree/model") as f:
            return "raspberry" in f.read().lower()
    except OSError:
        return False


def scan_sources(active_id=""):
    """Look for every camera that is connected right now (a few seconds). The camera that is in use cannot be opened a
    second time, so it is listed without probing."""
    if not _SCAN_LOCK.acquire(blocking=False):
        return SOURCES["items"]                             # a scan is already running
    SOURCES["scanning"] = True
    try:
        items, hints = [], []
        idxs = sorted({int(re.sub(r"\D", "", p)) for p in glob.glob("/dev/video*") if re.sub(r"\D", "", p)})
        if not idxs and not sys.platform.startswith("linux"):
            idxs = [0, 1, 2, 3]
        for idx in idxs:
            name = _v4l_name(idx)
            if any(b in name.lower() for b in V4L_SKIP):
                continue
            sid = f"usb:{idx}"
            entry = {"id": sid, "kind": "usb", "name": "USB camera: " + (name or f"video{idx}"),
                     "detail": f"/dev/video{idx}", "available": True}
            if sid == active_id:
                entry["detail"] += " · in use"
            else:
                src = _open_usb(idx) or _open_usb(idx, raw=True)     # thermal cameras do not like the forced format
                if src is None:
                    continue                                # metadata node or camera that is busy / not working
                entry["detail"] += f" · {src.size[0]}x{src.size[1]}"; src.release()
            items.append(entry)
        try:
            from picamera2 import Picamera2
            for n, info in enumerate(Picamera2.global_camera_info()):
                if "usb" in str(info.get("Id", "")).lower():
                    continue                                # USB cameras were found above
                num = int(info.get("Num", n))
                items.append({"id": f"pi:{num}", "kind": "pi", "name": "Raspberry Pi camera: " + str(info.get("Model", "camera")),
                              "detail": f"CSI port {num}", "available": True})
        except ImportError:
            if _is_pi():
                hints.append("Raspberry Pi cameras need picamera2:  sudo apt install python3-picamera2  "
                             "(in a virtual environment create it with --system-site-packages)")
        except Exception as e:
            hints.append(f"Pi camera scan failed: {e}")
        SOURCES.update(items=items, hints=hints, time=time.time())
        log_event("sys", f"Camera scan: {len(items)} camera(s) found")
        return items
    finally:
        SOURCES["scanning"] = False
        _SCAN_LOCK.release()


def list_sources():
    """Everything the user can pick: automatic + scanned cameras + saved network cameras."""
    items = [{"id": "auto", "kind": "auto", "name": "Automatic (first working USB camera)", "detail": "", "available": None}]
    items += [dict(i) for i in SOURCES["items"] if i["kind"] != "url"]
    items += [{"id": "url:" + s["id"], "kind": "url", "name": s["name"], "detail": mask_url(s["url"]), "available": None}
              for s in CFG["ip_sources"]]
    ids = {i["id"] for i in items}
    act = STATE["source_id"]
    if act and act not in ids:                              # the running camera is always in the list
        items.insert(1, {"id": act, "kind": act.split(":")[0], "name": STATE["source_label"], "detail": "in use", "available": True})
    return items


def source_info():
    return {"items": list_sources(), "selected": CFG["source"], "active": STATE["source_id"], "label": STATE["source_label"],
            "status": STATE["source_status"], "res": STATE["source_res"], "scanning": SOURCES["scanning"],
            "scanned": SOURCES["time"], "hints": list(SOURCES["hints"])}


def source_select(watch, sid):
    if not isinstance(sid, str) or not SRC_RE.match(sid):
        return False, "unknown source"
    if sid.startswith("url:") and not find_ip_source(sid[4:]):
        return False, "unknown network camera"
    watch.request_source(sid)
    return True, ""


def source_add(name, url):
    """Save a network camera. Returns (ok, error, new id)."""
    url = str(url or "").strip()
    if not _url_ok(url):
        return False, "invalid URL (rtsp:// or http:// expected)", ""
    if len(CFG["ip_sources"]) >= MAX_IP_SOURCES:
        return False, "too many network cameras", ""
    sid = uuid.uuid4().hex[:8]
    name = str(name or "").strip()[:40] or "Network camera"
    CFG["ip_sources"] = CFG["ip_sources"] + [{"id": sid, "name": name, "url": url}]     # re-assign, never mutate (DEFAULTS share the list)
    save_settings(); log_event("sys", f"Network camera added: {name} ({mask_url(url)})")
    return True, "", sid


def source_remove(watch, sid):
    s = find_ip_source(sid) if isinstance(sid, str) else None
    if not s:
        return False, "unknown network camera"
    CFG["ip_sources"] = [x for x in CFG["ip_sources"] if x["id"] != sid]
    save_settings(); log_event("sys", f"Network camera removed: {s['name']}")
    if CFG["source"] == "url:" + sid:
        watch.request_source("auto")
    return True, ""


# ----------------------------------------------------------------------------
# Timelapse: every N minutes the camera drives to a chosen position, waits until the picture is calm and saves a photo.
# An alarm (person seen, recording running, tracking) always has priority: then nothing moves, and the photo is taken
# only after the alarm is over. Photos: <recordings>/timelapse/tl_YYYYmmdd_HHMMSS.jpg   videos: tlv_*.mp4 in the same folder.
# ----------------------------------------------------------------------------
TL_HOLD = {"on": False}                          # True while the camera is parked for a photo: the patrol must not move it
TL_PHOTO_RE = re.compile(r"^tl_(\d{8})_(\d{6})\.jpg$")
TL_VIDEO_RE = re.compile(r"^tlv_[0-9A-Za-z_\-]{1,40}\.mp4$")
_TL_RENDER_LOCK = threading.Lock()


def servo_hold():
    """Something other than tracking is holding the servos (hand control, timelapse position)."""
    return manual_active() or TL_HOLD["on"]


def tl_dir():
    return os.path.join(os.path.abspath(CFG["record_dir"]), "timelapse")


def tl_photos(day=""):
    try:
        names = sorted(n for n in os.listdir(tl_dir()) if TL_PHOTO_RE.match(n) and (not day or n[3:11] == day))
    except OSError:
        names = []
    return names


def tl_overview():
    photos = tl_photos(); days = {}
    for n in photos:
        days[n[3:11]] = days.get(n[3:11], 0) + 1
    videos = []
    try:
        for n in sorted(os.listdir(tl_dir()), reverse=True):
            if TL_VIDEO_RE.match(n):
                st = os.stat(os.path.join(tl_dir(), n))
                videos.append({"name": n, "size": st.st_size, "time": int(st.st_mtime)})
    except OSError:
        pass
    return {"count": len(photos), "latest": photos[-1] if photos else "", "videos": videos[:30],
            "days": [{"day": d, "count": c} for d, c in sorted(days.items(), reverse=True)[:60]],
            "status": STATE["timelapse"], "render": STATE["timelapse_render"], "on": bool(CFG["timelapse_on"])}


def tl_path(name):
    """Absolute path of a timelapse photo / video (guards against path tricks), or None."""
    if not isinstance(name, str) or not (TL_PHOTO_RE.match(name) or TL_VIDEO_RE.match(name)):
        return None
    p = os.path.join(tl_dir(), name)
    return p if os.path.isfile(p) else None


def tl_cleanup():
    limit = CFG["timelapse_max_gb"] * 1024 ** 3
    try:
        files = [(n, os.path.getsize(os.path.join(tl_dir(), n))) for n in os.listdir(tl_dir()) if TL_PHOTO_RE.match(n)]
    except OSError:
        return
    files.sort()
    total = sum(sz for _n, sz in files); removed = 0
    while total > limit and len(files) > 1:
        n, sz = files.pop(0)
        try:
            os.remove(os.path.join(tl_dir(), n)); total -= sz; removed += 1
        except OSError:
            break
    if removed:
        log_event("servo", f"Cleanup: {removed} old photo(s) deleted")


class Timelapse:
    """State machine, called once per camera frame with the untouched picture.
       idle -> (interval over, no alarm) -> moving (camera driven to the position, settle time) -> photo -> idle."""
    def __init__(self):
        self.state = "idle"; self.t = 0.0; self.last_shot = 0.0; self.saved = None; self.target = None; self.pending_now = False

    def request_now(self):
        self.pending_now = True

    def _back(self):
        """Drive back to where the camera was - but only if nobody (tracking, hand control) has moved it since."""
        if CFG["timelapse_return"] and self.saved and self.target and abs(CFG["pan"] - self.target[0]) < 1 and abs(CFG["tilt"] - self.target[1]) < 1:
            CFG["pan"], CFG["tilt"] = self.saved

    def _abort(self, why):
        self._back()
        TL_HOLD["on"] = False; self.state = "idle"
        log_event("servo", f"Photo postponed: {why}")

    def update(self, frame, alarm):
        now = time.time()
        if not CFG["timelapse_on"] and not self.pending_now:
            if self.state != "idle":
                self._back(); TL_HOLD["on"] = False; self.state = "idle"
            STATE["timelapse"] = "off"
            return
        busy = alarm or manual_active()
        if self.state == "idle":
            due = self.pending_now or now - self.last_shot >= CFG["timelapse_interval"] * 60.0
            if not due:
                STATE["timelapse"] = f"next photo in {int(max(1, (self.last_shot + CFG['timelapse_interval'] * 60.0 - now) / 60.0 + 0.5))} min"
                return
            if busy:
                STATE["timelapse"] = "waiting: alarm has priority" if alarm else "waiting: manual control"
                return
            tp = float(max(0.0, min(100.0, CFG["timelapse_pan"]))); tt = float(max(0.0, min(100.0, CFG["timelapse_tilt"])))
            self.saved = (CFG["pan"], CFG["tilt"]); self.target = (tp, tt)
            TL_HOLD["on"] = True
            CFG["pan"], CFG["tilt"] = tp, tt
            self.state = "moving"; self.t = now
            log_event("servo", f"Driving to the photo position (pan {tp:.0f}%, tilt {tt:.0f}%)")
            STATE["timelapse"] = "moving to the photo position"
            return
        # state == "moving": the alarm may start at any time and wins immediately
        if busy:
            self._abort("alarm" if alarm else "manual control")
            STATE["timelapse"] = "waiting: alarm has priority" if alarm else "waiting: manual control"
            return
        if now - self.t < CFG["timelapse_settle"]:
            STATE["timelapse"] = "moving to the photo position"
            return
        self._shoot(frame, now)

    def _shoot(self, frame, now):
        try:
            os.makedirs(tl_dir(), exist_ok=True)
            name = datetime.now().strftime("tl_%Y%m%d_%H%M%S.jpg")
            ok = cv2.imwrite(os.path.join(tl_dir(), name), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        except (OSError, cv2.error) as e:
            ok, name = False, ""
            log_event("servo", f"Photo could not be saved: {e}")
        self.last_shot = now; self.pending_now = False
        if ok:
            STATE["timelapse_last"] = name
            log_event("servo", f"Photo saved: {name}")
            tl_cleanup()
        self._back()
        TL_HOLD["on"] = False; self.state = "idle"
        STATE["timelapse"] = "photo saved"


def timelapse_render(day="", fps=None):
    """Make a video from the photos of one day (or all). Runs in the background; progress is in STATE['timelapse_render']."""
    day = day if isinstance(day, str) and re.fullmatch(r"\d{8}", day) else ""
    try:
        fps = max(5.0, min(60.0, float(fps if fps is not None else CFG["timelapse_fps"])))
    except (TypeError, ValueError):
        fps = 25.0
    files = tl_photos(day)[-20000:]
    if len(files) < 2:
        return False, "need at least 2 photos"
    if not _TL_RENDER_LOCK.acquire(blocking=False):
        return False, "a video is already being made"

    def work():
        enc_before = STATE["recording_enc"]
        try:
            first = cv2.imread(os.path.join(tl_dir(), files[0]))
            if first is None:
                STATE["timelapse_render"] = "error: first photo unreadable"; return
            h, w = first.shape[:2]
            name = f"tlv_{day or 'all'}_{datetime.now().strftime('%H%M%S')}.mp4"
            path = os.path.join(tl_dir(), name)
            writer, _codec = open_writer(path, fps, (w, h))
            if writer is None:
                STATE["timelapse_render"] = "error: no video encoder available"; return
            for i, n in enumerate(files):
                img = cv2.imread(os.path.join(tl_dir(), n))
                if img is None:
                    continue
                if img.shape[:2] != (h, w):
                    img = cv2.resize(img, (w, h))
                writer.write(img)
                if hasattr(writer, "q"):
                    while writer.q.qsize() > 30:                 # the ffmpeg pipe drops frames when it is full: wait for it
                        time.sleep(0.01)
                STATE["timelapse_render"] = f"making video {i + 1}/{len(files)}"
            writer.release()
            STATE["timelapse_render"] = "video ready: " + name
            log_event("servo", f"Video made: {name} ({len(files)} photos, {fps:.0f} fps)")
        except Exception as e:
            STATE["timelapse_render"] = "error: " + str(e)[:100]
        finally:
            STATE["recording_enc"] = enc_before
            _TL_RENDER_LOCK.release()
    STATE["timelapse_render"] = "making video 0/" + str(len(files))
    threading.Thread(target=work, daemon=True).start()
    return True, ""


# ----------------------------------------------------------------------------
# Thermal camera: a second camera with the same view. Its picture is coloured and laid over the normal picture
# (blend, or "hot mode": only the warmest areas are shown). Detection always works on the normal picture.
# ----------------------------------------------------------------------------
class ThermalCam:
    """Keeps the chosen thermal source open in the background and always holds its newest picture."""
    def __init__(self):
        self.src = None; self.spec = ""; self.frame = None; self.t = 0.0; self.fails = 0
        self.retry_at = 0.0; self.opening = False; self.cache = (None, None)
        self.bgsub = None; self.bg_shape = None; self.hits = deque(maxlen=5); self.det_t = 0.0; self.boxes = []; self.lo = self.hi = None
        threading.Thread(target=self.loop, daemon=True).start()

    def wanted(self):
        spec = CFG["thermal_source"] if (CFG["thermal_on"] or CFG["thermal_alarm"]) else ""
        if spec and spec == STATE["source_id"]:
            return ""                                          # that camera is the main camera already
        return spec

    def _close(self):
        src, self.src, self.frame = self.src, None, None
        if src is not None:
            src.release()

    def _open(self, spec):
        self.opening = True
        try:
            res = open_source(spec, thermal=True)
            if res[0] is None:
                STATE["thermal"] = "no picture: " + res[3]
                log_event("sys", f"Thermal camera '{res[2]}' not available: {res[3]}")
                self.retry_at = time.time() + 5.0
            elif self.wanted() != spec:
                res[0].release()
            else:
                self.src = res[0]; self.spec = spec; self.fails = 0
                size = getattr(res[0], "size", None)
                STATE["thermal_res"] = f"{size[0]}x{size[1]}" if size else ""
                log_event("sys", f"Thermal camera: {res[2]}" + (f" ({STATE['thermal_res']})" if size else ""))
        finally:
            self.opening = False

    def loop(self):
        while True:
            try:
                want = self.wanted()
                if self.src is not None and (want != self.spec):
                    self._close()
                if self.src is None:
                    if not want:
                        STATE["thermal"] = "off" if not (CFG["thermal_on"] or CFG["thermal_alarm"]) else ("same camera as the main picture" if CFG["thermal_source"] else "no thermal camera selected")
                        time.sleep(0.5); continue
                    if time.time() >= self.retry_at and not self.opening:
                        STATE["thermal"] = "connecting…"
                        self._open(want)
                    else:
                        time.sleep(0.3)
                    continue
                ok, fr = self.src.read()
                if ok and fr is not None:
                    self.frame = fr; self.t = time.time(); self.fails = 0
                    STATE["thermal"] = "connected"
                else:
                    self.fails += 1
                    if self.fails >= 30:
                        STATE["thermal"] = "connection lost - reconnecting"
                        self._close(); self.retry_at = time.time() + 3.0
                    time.sleep(0.05)
            except Exception as e:
                STATE["thermal"] = "error: " + str(e)[:80]
                self._close(); self.retry_at = time.time() + 5.0; time.sleep(1.0)

    @staticmethod
    def to_gray8(fr):
        """Any thermal frame -> 8 bit intensity (hot = bright) with the contrast stretched to what is in the picture."""
        if fr.ndim == 3:
            if fr.shape[2] == 1:
                fr = fr[:, :, 0]
            else:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY) if fr.dtype == np.uint8 else fr.mean(axis=2)
        f = fr.astype(np.float32)
        small = f[::max(1, f.shape[0] // 60), ::max(1, f.shape[1] // 80)]
        lo, hi = np.percentile(small, (1, 99))
        if hi - lo < 1e-3:
            return np.zeros(f.shape, np.uint8)
        return np.clip((f - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)

    @staticmethod
    def is_plain_gray(fr):
        if fr.ndim == 2 or fr.shape[2] == 1:
            return True
        if fr.dtype != np.uint8:
            return True
        s = fr[::8, ::8].astype(np.int16)
        return int(np.abs(s[:, :, 0] - s[:, :, 1]).max()) < 6 and int(np.abs(s[:, :, 1] - s[:, :, 2]).max()) < 6

    def color(self, fr):
        """-> (colour picture, intensity). A camera that already delivers false colours keeps its own colours."""
        gray = self.to_gray8(fr)
        cmap = THERMAL_MAPS.get(CFG["thermal_map"], cv2.COLORMAP_INFERNO)
        if self.is_plain_gray(fr):
            col = cv2.applyColorMap(gray, cmap) if cmap is not None else cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            col = fr if fr.dtype == np.uint8 and fr.ndim == 3 and fr.shape[2] == 3 else cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return col, gray

    def detect(self):
        """Warm bodies in the thermal picture: clearly warmer than the scene (thermal_delta), moving (unless switched off,
        so sun-warmed stones or an engine do not alarm), big enough, inside the zones, seen in 3 of the last 5 pictures."""
        fr, t = self.frame, self.t
        if fr is None or time.time() - t > 3.0:
            self.hits.clear(); self.boxes = []; return []
        if t == self.det_t:
            return self.boxes
        self.det_t = t
        f = fr.astype(np.float32)
        if f.ndim == 3:
            f = f.mean(axis=2)
        if f.shape[1] > 160:
            f = cv2.resize(f, (160, max(1, int(f.shape[0] * 160 / f.shape[1]))), interpolation=cv2.INTER_AREA)
        lo, hi = np.percentile(f, (2, 99.5))
        if self.lo is None:
            self.lo, self.hi = float(lo), float(hi)
        else:                                            # slow: an animal walking in must not re-scale the whole picture
            self.lo += 0.05 * (lo - self.lo); self.hi += 0.05 * (max(hi, self.lo + 1e-3) - self.hi)
        g = np.clip((f - self.lo) * 255.0 / max(1e-3, self.hi - self.lo), 0, 255).astype(np.uint8)
        med = float(np.median(g))
        warm = ((g.astype(np.int16) > med + CFG["thermal_delta"] * 2.55).astype(np.uint8)) * 255
        if CFG["thermal_need_motion"]:
            if self.bgsub is None or self.bg_shape != g.shape:
                self.bgsub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=12, detectShadows=False); self.bg_shape = g.shape
            mov = cv2.dilate(self.bgsub.apply(g), np.ones((3, 3), np.uint8), iterations=2)
            warm = cv2.bitwise_and(warm, mov)
        warm = cv2.morphologyEx(warm, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        cnts, _ = cv2.findContours(warm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        H, W = g.shape
        min_a = max(2.0, CFG["thermal_min_area"] / 100.0 * W * H)
        boxes = []
        for c in cnts:
            if cv2.contourArea(c) < min_a:
                continue
            x, y, w, h = cv2.boundingRect(c)
            nb = (x / W, y / H, w / W, h / H)
            if zone_allows(nb[0] + nb[2] / 2.0, nb[1] + nb[3] * 0.85):
                boxes.append(nb)
        self.hits.append(bool(boxes))
        self.boxes = boxes if sum(self.hits) >= 3 else []
        return self.boxes

    def overlay(self, frame):
        fr = self.frame
        if fr is None or time.time() - self.t > 3.0:
            return frame
        try:
            col, gray = self.color(fr)
            H, W = frame.shape[:2]
            col = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC)
            a = float(max(0.05, min(1.0, CFG["thermal_alpha"])))
            if CFG["thermal_hot"]:
                gray = cv2.resize(gray, (W, H), interpolation=cv2.INTER_LINEAR)
                thr = float(np.percentile(gray[::4, ::4], CFG["thermal_hot_pct"]))
                m = cv2.GaussianBlur((gray > thr).astype(np.float32), (0, 0), max(2.0, W / 200.0))[:, :, None] * a
                return (frame * (1.0 - m) + col * m).astype(np.uint8)
            return cv2.addWeighted(frame, 1.0 - a, col, a, 0)
        except cv2.error:
            return frame


THERMAL = None            # created together with the camera loop


class MotionWatch:
    def __init__(self):
        self.cap = None                    # the video source (CvSource / PiCamSource), opened in a background thread
        self.bg = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=28, detectShadows=False)
        self.weather = WeatherAnalyzer(); self.tracker = Tracker(); self.tuner = AutoTuner()
        self.ai = AIDetector(); self.hw = Hardware(); self.patrol = Patrol(); self.relays = RelayManager()
        self.frame_out = None; self.jpeg = None; self.jpeg_seq = 0
        self.frame_raw = None; self.raw_until = 0.0
        self.sysmon = SysMonitor(); self.netmon = NetMonitor()
        self.mask_buf = deque(maxlen=5)
        self.color_bg = None               # slow colour background for the shadow filter
        self.writer = None; self.last_person_time = 0; self.last_relay_time = 0
        self.rec_name = ""; self.rec_info = None; self.rec_size = None; self._rec_retry = 0.0
        self.preroll = deque()
        self.frame_times = deque(maxlen=30)
        self.read_failures = 0; self.web_viewers = 0
        self.pre_since = 0.0; self.pre_last = 0.0; self.pre_alerted = False
        self.last_warm = 0.0; self.warm_alerted = False
        self.notifier = Notifier(); self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self.last_cleanup = 0
        self._open_lock = threading.Lock(); self._open_gen = 0; self._opened = None; self._opening = False; self._retry_at = 0.0
        os.makedirs(CFG["record_dir"], exist_ok=True); rec_clean_tmp()
        atexit.register(self.close)
        self.presence = PresenceMonitor()
        self.scheduler = Scheduler()
        global THERMAL
        self.timelapse = Timelapse(); THERMAL = ThermalCam()
        hotspot_password()                                 # the own Wi-Fi has its password from the start (shown on the page)
        WATCH_REF["w"] = self
        self.request_source(CFG["source"])

    def close(self):
        if self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
        save_settings_now()

    # ---- recordings folder housekeeping ---------------------------------
    def cleanup_recordings(self):
        """Delete the oldest recordings (video + snapshot + info file belong together) until below record_max_gb.
        Favourites (star in the preview page) are never deleted."""
        groups = {}
        for f in glob.glob(os.path.join(CFG["record_dir"], "*")):
            if os.path.isfile(f):
                groups.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(f)
        items = []
        for stem, fs in groups.items():
            try:
                items.append((max(os.path.getmtime(f) for f in fs), sum(os.path.getsize(f) for f in fs), stem, fs))
            except OSError:
                pass
        items.sort(key=lambda g: g[0])
        total = sum(g[1] for g in items)
        removable = [g for g in items if not _read_sidecar(g[2] + ".json").get("fav")]
        limit = CFG["record_max_gb"] * 1024 ** 3
        removed = 0
        while total > limit and removable and len(items) - removed > 1:
            _mt, size, stem, fs = removable.pop(0)
            if any(os.path.basename(f) in LIVE_RECS or os.path.basename(f) == self.rec_name for f in fs):
                continue                                          # never delete what is being recorded right now
            try:
                for f in fs:
                    os.remove(f)
            except OSError:
                break
            rec_purge_extras(stem)
            total -= size; removed += 1
        STATE["rec_dir_mb"] = int(total / 1024 ** 2)
        if removed:
            log_event("rec", f"Cleanup: {removed} old recording(s) deleted, folder now {STATE['rec_dir_mb']} MB")

    # ---- video source ----------------------------------------------------
    def request_source(self, spec):
        """Switch to another video source (any thread). The running camera keeps working until the new one delivers a picture."""
        CFG["source"] = spec; save_settings()
        active = STATE["source_id"]
        if self.cap is not None and (spec == active or (spec == "auto" and active.startswith("usb:"))):
            return                                                # that camera is already running
        self._open_gen += 1
        self._start_opener(spec)

    def _start_opener(self, spec):
        gen = self._open_gen
        self._opening = True
        STATE["source_status"] = "connecting…"

        def work():
            res = open_source(spec)
            with self._open_lock:
                if gen == self._open_gen:
                    self._opened = res; self._opening = False
                elif res[0] is not None:
                    res[0].release()                              # a newer request replaced this one
        threading.Thread(target=work, daemon=True).start()

    def _take_opened(self):
        with self._open_lock:
            res, self._opened = self._opened, None
        return res

    def _apply_opened(self, res):
        src, sid, label, err = res
        if src is None:
            log_event("sys", f"Video source '{label}' not available: {err}")
            if self.cap is not None:                              # a switch failed: keep the working camera
                STATE["source_status"] = f"failed: {err} (still using {STATE['source_label']})"
                CFG["source"] = STATE["source_id"]; save_settings()
            else:
                STATE["source_status"] = f"failed: {err}"
                self._retry_at = time.time() + 3.0
            return
        old, self.cap = self.cap, src
        if old is not None:
            old.release()
        self.reset_scene()
        size = getattr(src, "size", None)
        STATE.update(source_id=sid, source_label=label, source_status="connected",
                     source_res=f"{size[0]}x{size[1]}" if size else "")
        log_event("rec", f"Video source: {label}" + (f" ({STATE['source_res']})" if STATE["source_res"] else ""))

    def reset_scene(self):
        """New camera = new picture size and scene: forget everything that depends on the old picture."""
        if self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
        self.bg = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=28, detectShadows=False)
        self.weather = WeatherAnalyzer(); self.tracker = Tracker()
        self.mask_buf.clear(); self.color_bg = None; self.preroll.clear()
        self.tuner.reset()
        self.read_failures = 0

    def no_camera_frame(self):
        img = np.zeros((360, 640, 3), np.uint8)
        busy = STATE["source_status"].startswith(("connecting", "connection lost"))
        ascii_ = lambda s: str(s).encode("ascii", "replace").decode()
        cv2.putText(img, "CONNECTING..." if busy else "NO CAMERA FOUND", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                    (0, 200, 255) if busy else (0, 0, 255), 3)
        cv2.putText(img, ascii_(source_label(CFG["source"]))[:50], (150, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
        cv2.putText(img, ascii_(STATE["source_status"])[:60], (150, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        cv2.putText(img, "check the camera / network  |  ls /dev/video*", (150, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        return img

    # ---- processing ------------------------------------------------------
    def preprocess(self, gray, rain_mode):
        if rain_mode:
            g = cv2.medianBlur(cv2.GaussianBlur(gray, (9, 9), 0), 5)
            self.mask_buf.append(g)
            if len(self.mask_buf) >= 3:
                g = np.median(np.array(self.mask_buf), axis=0).astype(np.uint8)
            return g
        self.mask_buf.clear()
        return cv2.GaussianBlur(gray, (5, 5), 0)

    def remove_shadows(self, fg, small):
        """Drop moving pixels that are only a darker copy of the background (= shadows)."""
        if self.color_bg is None:
            self.color_bg = small.astype(np.float32)
            return fg
        cv2.accumulateWeighted(small, self.color_bg, 0.002)
        if not CFG["shadow_filter"] or not np.any(fg):
            return fg
        bg = self.color_bg.astype(np.uint8)
        hsv_c = cv2.cvtColor(small, cv2.COLOR_BGR2HSV); hsv_b = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
        vb = hsv_b[:, :, 2].astype(np.float32) + 1.0
        ratio = hsv_c[:, :, 2].astype(np.float32) / vb
        dh = np.abs(hsv_c[:, :, 0].astype(np.int16) - hsv_b[:, :, 0].astype(np.int16))
        dh = np.minimum(dh, 180 - dh)
        ds = np.abs(hsv_c[:, :, 1].astype(np.int16) - hsv_b[:, :, 1].astype(np.int16))
        # on grey / low-saturation ground (asphalt, concrete, dusk) the hue is numerically unstable,
        # so the hue test is skipped there and only brightness ratio + saturation decide
        low_sat = (hsv_b[:, :, 1] < 50) & (hsv_c[:, :, 1] < 70)
        hue_ok = (dh < 12) | low_sat
        shadow = ((ratio > CFG["shadow_ratio_min"]) & (ratio < CFG["shadow_ratio_max"])
                  & hue_ok & (ds < 45) & (fg > 0)).astype(np.uint8) * 255
        # smooth the shadow mask so single person pixels are not punched out
        shadow = cv2.morphologyEx(shadow, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        shadow = cv2.morphologyEx(shadow, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        total = np.count_nonzero(fg)
        STATE["shadow_pct"] = int(100 * np.count_nonzero(shadow) / max(1, total))
        return cv2.bitwise_and(fg, cv2.bitwise_not(shadow))

    def foreground(self, gray, small, rain_mode, wind_boost):
        sens = CFG["sensitivity"] / 100.0
        self.bg.setVarThreshold(16 + (1 - sens) * 40 + (12 if rain_mode else 0))
        fg = self.bg.apply(gray, learningRate=0.004 if rain_mode else 0.002)
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        fg = self.remove_shadows(fg, small)                      # colour based shadow removal
        k = 5 if rain_mode or wind_boost > 1.5 else 3
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        return cv2.dilate(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 13)), 1)

    def classify(self, t, frame_area, wind_boost, ai_boxes):
        x, y, w, h = t.box
        aspect = w / float(h + 1e-6); area = w * h; sp = t.speed()
        t.ai_confirmed = any(iou(t.box, b) > 0.2 for b in ai_boxes)
        if CFG["car_filter"] and not t.ai_confirmed:
            vehicle = (aspect > CFG["car_aspect"] and sp > 3.0) or sp > CFG["car_speed"] or \
                      (area > CFG["car_area_frac"] * frame_area and aspect > 1.2 and sp > 1.0)
            if vehicle:
                if not t.is_vehicle:
                    STATE["ignored_vehicles"] += 1
                    log_event("car", f"Vehicle-like object #{t.id} ignored (aspect {aspect:.2f}, speed {sp:.1f})")
                t.is_vehicle, t.is_person = True, False
                return
            t.is_vehicle = False                               # shape became person-like again -> re-evaluate
        need_frames = int(CFG["walk_frames"] * wind_boost)
        walking = (len(t.speeds) >= need_frames and CFG["walk_min_speed"] <= sp <= CFG["walk_max_speed"]
                   and t.steadiness() >= CFG["speed_consistency"] and aspect < CFG["car_aspect"])
        if t.ai_confirmed:
            walking = True                                  # AI says person -> person
        elif CFG["ai_require"] and self.ai.net is not None and CFG["ai_enabled"]:
            walking = False                                 # needs AI confirmation
        elif t.is_person and CFG["person_sticky"] and sp <= CFG["walk_max_speed"]:
            walking = True                                  # keep flag while tracked (may stand still)
        if walking and not t.is_person:
            STATE["detections_total"] += 1
            log_event("person", f"Person #{t.id} {'AI-confirmed' if t.ai_confirmed else 'walking'}, speed {sp:.1f} px/f")
        t.is_person = walking

    # ---- servo tracking --------------------------------------------------
    def track(self, target_box, pw, ph):
        x, y, w, h = target_box[:4]
        ex = (x + w / 2.0) / pw - 0.5          # -0.5 .. 0.5  (right = positive)
        ey = (y + h / 2.0) / ph - 0.5          # down  = positive
        dz = CFG["track_deadzone"]
        g = CFG["track_gain"] * 10.0
        if abs(ex) > dz:
            CFG["pan"] = max(0.0, min(100.0, CFG["pan"] + ex * g))
        if abs(ey) > dz:
            CFG["tilt"] = max(0.0, min(100.0, CFG["tilt"] - ey * g))

    # ---- recording ----------------------------------------------
    def handle_recording(self, frame, persons):
        now = time.time()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")          # video and snapshot of one event share the same name
        if not is_armed():
            persons = []                                  # disarmed: no snapshots, no notifications, no new recordings
        new_person = bool(persons) and (now - self.last_person_time) > CFG["record_tail"]
        if persons:
            self.last_person_time = now
        if new_person:
            snap = None
            if CFG["snapshot_on_person"]:
                snap = os.path.join(CFG["record_dir"], f"person_{stamp}.jpg")
                cv2.imwrite(snap, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            self.notifier.person(len(persons), snap, frame)
            push_alert("person", "person", count=len(persons), source=STATE["source_label"])
        want = CFG["record"] and ((self.last_person_time > 0 and (now - self.last_person_time) < CFG["record_tail"])
                                  or (CFG["thermal_alarm"] and is_armed() and now - self.last_warm < CFG["record_tail"]))
        h, w = frame.shape[:2]
        if self.writer is not None and (self.rec_size != (w, h) or getattr(self.writer, "failed", False)):
            self.writer.release(); self.writer = None          # picture size changed (camera switched) or the encoder died
            self._finish_recording()
        pre = float(CFG["pre_roll"])
        if self.writer is None and not want and pre > 0 and CFG["record"]:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])      # small ring buffer of recent frames
            if ok:
                self.preroll.append((now, buf.tobytes()))
        while self.preroll and (pre <= 0 or now - self.preroll[0][0] > pre + 0.5):
            self.preroll.popleft()
        if want and self.writer is None and now >= self._rec_retry:
            if now - self.last_cleanup > 60:
                self.cleanup_recordings(); self.last_cleanup = now
            name = os.path.join(CFG["record_dir"], f"person_{stamp}.mp4")
            fps = max(5.0, min(30.0, float(STATE["fps"]) or 15.0))     # real frame rate -> correct playback speed
            self.writer, codec = open_writer(name, fps, (w, h))
            if self.writer is None:
                self._rec_retry = now + 30.0
                log_event("rec", "Recording failed: no video encoder could be opened (retry in 30 s)")
            else:
                self.rec_name = os.path.basename(name); self.rec_size = (w, h); STATE["rec_name"] = self.rec_name
                self.rec_info = {"start": now - (now - self.preroll[0][0] if self.preroll else 0.0), "fps": fps, "frames": 0, "persons": 0,
                                 "codec": codec, "source": STATE["source_label"], "source_id": STATE["source_id"],
                                 "schedules": list(SCHED["active"])}
                n = 0
                for _t, jb in self.preroll:                            # the seconds before the detection come first
                    img = cv2.imdecode(np.frombuffer(jb, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None and img.shape[:2] == (h, w):
                        self.writer.write(img); n += 1
                self.preroll.clear(); self.rec_info["frames"] += n
                log_event("rec", f"Recording started: {self.rec_name} ({fps:.0f} fps, {STATE['recording_enc'] or codec}"
                                 + (f", {n} pre-roll frames" if n else "") + ")")
        elif not want and self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
            log_event("rec", "Recording stopped")
        if self.writer is not None:
            self.writer.write(frame)
            self.rec_info["frames"] += 1; self.rec_info["persons"] = max(self.rec_info["persons"], len(persons))
        STATE["recording"] = self.writer is not None

    def _finish_recording(self):
        """Write the small info file (<name>.json) next to a finished recording: source, schedules, duration, codec ..."""
        info, name = self.rec_info, self.rec_name
        self.rec_info = None; self.rec_name = ""; STATE["rec_name"] = ""
        if not info or not name:
            return
        meta = {"start": datetime.fromtimestamp(info["start"]).isoformat(timespec="seconds"),
                "end": datetime.now().isoformat(timespec="seconds"),
                "duration": round(info["frames"] / info["fps"], 1) if info["fps"] else 0.0,
                "frames": info["frames"], "fps": round(info["fps"], 1), "codec": info["codec"],
                "persons": info["persons"], "source": info["source"], "source_id": info["source_id"],
                "schedules": info["schedules"]}
        try:
            with open(os.path.join(CFG["record_dir"], os.path.splitext(name)[0] + ".json"), "w") as f:
                json.dump(meta, f)
        except OSError:
            pass

    # ---- main loop -------------------------------------------------------
    def run(self):
        while True:
            opened = self._take_opened()
            if opened is not None:
                self._apply_opened(opened)
            if self.cap is None:
                self.relays.update(set()); STATE["present"] = []
                self.frame_out = self.no_camera_frame(); time.sleep(0.5)
                if not self._opening and time.time() >= self._retry_at:
                    self._start_opener(CFG["source"])
                continue
            ok, frame = self.cap.read()
            if not ok:
                self.read_failures += 1
                if self.read_failures >= 60:            # ~3 s without a frame -> reconnect the source
                    log_event("sys", "Camera stopped delivering frames - reconnecting")
                    STATE["source_status"] = "connection lost - reconnecting"
                    self.cap.release()
                    self.cap = None; self.read_failures = 0; self._retry_at = time.time() + 2.0
                time.sleep(0.05); continue
            self.read_failures = 0
            t0 = time.time()
            # timelapse: an alarm (person seen, recording running, tracking) always has priority over the photo
            alarm = (self.writer is not None or STATE["persons"] > 0 or STATE["tracking"]
                     or (self.last_person_time > 0 and t0 - self.last_person_time < CFG["record_tail"] + 1.0))
            self.timelapse.update(frame, alarm)
            if t0 < self.raw_until:
                self.frame_raw = frame.copy()
            H, W = frame.shape[:2]
            pw = CFG["proc_width"]; ph = int(H * pw / W); sx = W / pw; sy = H / ph
            small = cv2.resize(frame, (pw, ph))
            if CFG["thermal_on"] and THERMAL is not None:
                frame = THERMAL.overlay(frame)             # detection keeps using `small` (the normal picture)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            bright = float(gray.mean()); STATE["brightness"] = int(bright)
            lowlight = CFG["lowlight_auto"] and bright < CFG["lowlight_threshold"]
            if lowlight != STATE["lowlight"]:
                log_event("auto", f"Low-light mode {'ON' if lowlight else 'OFF'} (brightness {bright:.0f})")
                STATE["lowlight"] = lowlight
            if lowlight:
                gray = self.clahe.apply(cv2.medianBlur(gray, 5))   # denoise, then boost contrast so dark figures separate

            rain_score = self.weather.rain(gray) if CFG["rain_auto"] else 0.0
            rain_mode = (rain_score > CFG["rain_threshold"]) if CFG["rain_auto"] else CFG["rain_mode"]
            if rain_mode != STATE["rain_mode"]:
                log_event("rain", "Rain mode ON - filtering rain" if rain_mode else "Rain mode OFF")
            wind_boost = STATE["wind_boost"]

            persons, candidates, person_boxes = [], [], []
            present = set()                      # what is in view right now -> relay triggers
            if CFG["detection_on"]:
                g = self.preprocess(gray, rain_mode)
                fg = self.foreground(g, small, rain_mode, wind_boost)
                ai_boxes = [b for b in self.ai.detect(small) if zone_box_ok(b, pw, ph)]
                ai_objs = [o for o in self.ai.objects if zone_box_ok(o, pw, ph)]
                objects = ai_objs if (CFG["show_objects"] and CFG["ai_enabled"]) else []
                counts = {}
                for o in objects:
                    nm = COCO_LABELS.get(o[5], "object"); counts[nm] = counts.get(nm, 0) + 1
                STATE["objects"] = len(objects)
                STATE["object_summary"] = ", ".join(f"{n} x{c}" for n, c in counts.items())
                min_area = CFG["min_area"] * (1.0 - CFG["sensitivity"] / 200.0) * wind_boost
                cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                boxes = [b for b in (cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) >= min_area) if zone_box_ok(b, pw, ph)]
                if boxes:
                    present.add("prealarm")              # pre-alarm: anything at all moves in the picture (before it is judged to be a person)
                boxes = merge_boxes(boxes + [b[:4] for b in ai_boxes])   # AI persons become tracks too
                tracks = self.tracker.update(boxes)
                for t in tracks:
                    if t.lost:
                        continue
                    self.classify(t, pw * ph, wind_boost, ai_boxes)
                    if t.is_person:
                        persons.append(t); person_boxes.append(t.box)
                    else:
                        candidates.append(t)            # anything else that moves -> white
                if person_boxes or ai_boxes:
                    present.add("person")
                if persons or candidates:
                    present.add("motion")
                present.update(COCO_LABELS.get(o[5], "object") for o in ai_objs)
                if present & ANIMALS:
                    present.add("animal")
                self.tuner.observe(fg, tracks, persons, STATE["fps"])
                if CFG["wind_auto"]:
                    ws = self.weather.wind(fg, person_boxes)
                    STATE["wind_score"] = ws
                    boost = 1.0 + max(0.0, ws - CFG["wind_threshold"]) / (1 - CFG["wind_threshold"]) * (CFG["wind_boost_max"] - 1)
                    STATE["wind_boost"] = round(min(CFG["wind_boost_max"], boost), 2)
                    lvl = "calm" if ws < CFG["wind_threshold"] else ("breezy" if ws < 0.55 else ("strong" if ws < 0.8 else "storm"))
                    if lvl != STATE["wind_level"]:
                        log_event("wind", f"Wind: {lvl} (score {ws:.2f}, threshold x{STATE['wind_boost']})")
                    STATE["wind_level"] = lvl
                else:
                    STATE["wind_boost"] = 1.0; STATE["wind_score"] = 0.0; STATE["wind_level"] = "off"

                # servo tracking: follow the largest person
                # (paused while the camera is moved by hand: pad, arrow keys, web page)
                manual = manual_active()
                if CFG["track_person"] and person_boxes and not manual:
                    target = max(person_boxes, key=lambda b: b[2] * b[3])
                    self.track(target, pw, ph)
                    if not STATE["tracking"]:
                        log_event("servo", "Tracking person - patrol paused")
                    STATE["tracking"] = True
                elif STATE["tracking"] and (manual or time.time() - self.last_person_time > 2.0):
                    STATE["tracking"] = False
                    log_event("servo", "Manual control - tracking paused" if manual else "Person lost - patrol may resume")

                # drawing
                if CFG["show_mask"]:
                    m = cv2.resize(fg, (W, H))
                    frame = cv2.addWeighted(frame, 0.6, cv2.cvtColor(m, cv2.COLOR_GRAY2BGR), 0.4, 0)
                for t in candidates:
                    x, y, w, h = [int(v) for v in (t.box[0] * sx, t.box[1] * sy, t.box[2] * sx, t.box[3] * sy)]
                    draw_outline(frame, cnts, t.box, sx, sy, (255, 255, 255), 1)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
                    cv2.putText(frame, "vehicle" if t.is_vehicle else "motion", (x, max(14, y - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                for obj in objects:
                    draw_object(frame, obj, sx, sy)
                for t in persons:
                    x, y, w, h = [int(v) for v in (t.box[0] * sx, t.box[1] * sy, t.box[2] * sx, t.box[3] * sy)]
                    if CFG["highlight_red"]:
                        roi = frame[max(0, y):y + h, max(0, x):x + w]
                        msrc = fg[t.box[1]:t.box[1] + t.box[3], t.box[0]:t.box[0] + t.box[2]]
                        mroi = cv2.resize(msrc, (roi.shape[1], roi.shape[0])) if roi.size and msrc.size else None
                        if mroi is not None:
                            red = np.zeros_like(roi); red[:, :, 2] = 255
                            tint = cv2.addWeighted(roi, 0.45, red, 0.55, 0)
                            roi[mroi > 0] = tint[mroi > 0]
                    draw_outline(frame, cnts, t.box, sx, sy, (0, 0, 255), 2)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(frame, f"PERSON #{t.id}{' AI' if t.ai_confirmed else ''}  {t.speed():.1f}px/f",
                                (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    if CFG["show_tracks"] and len(t.hist) > 1:
                        pts = np.array([(int(px * sx), int(py * sy)) for px, py in t.hist], np.int32)
                        cv2.polylines(frame, [pts], False, (0, 0, 255), 2)
                if person_boxes and CFG["track_person"]:
                    cv2.drawMarker(frame, (W // 2, H // 2), (0, 255, 255), cv2.MARKER_CROSS, 24, 1)
            else:
                STATE["objects"] = 0; STATE["object_summary"] = ""

            if CFG["show_zones"] and ZONES:
                for z in ZONES:
                    pts = np.array([(int(px * W), int(py * H)) for px, py in z["points"]], np.int32)
                    col = (0, 160, 255) if z["mode"] == "ignore" else (80, 200, 80)
                    cv2.polylines(frame, [pts], True, col, 1, cv2.LINE_AA)
                    cv2.putText(frame, z["name"][:24].encode("ascii", "replace").decode(), (int(pts[0][0]) + 4, int(pts[0][1]) + 14),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
            warm_boxes = []
            if CFG["thermal_alarm"] and CFG["detection_on"] and THERMAL is not None:
                warm_boxes = THERMAL.detect()                 # (x, y, w, h) 0..1 of the picture, already checked against the zones
                if warm_boxes:
                    present.add("warm"); self.last_warm = t0
                    for bx, by, bw, bh in warm_boxes:
                        p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
                        cv2.rectangle(frame, p1, p2, (0, 140, 255), 3)
                        cv2.putText(frame, "WARM", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
                    if not self.warm_alerted:
                        self.warm_alerted = True
                        push_alert("warm", "warm", count=len(warm_boxes), source=STATE["source_label"])
                        if self.notifier.prealarm(frame, "warm"):
                            log_event("person", "Thermal alarm: warm body in the zone - push message sent")
                        else:
                            log_event("person", "Thermal alarm: warm body in the zone" + ("" if is_armed() else " (disarmed - no alarm)"))
                elif self.warm_alerted and t0 - self.last_warm > 5.0:
                    self.warm_alerted = False
            STATE["warm"] = len(warm_boxes)
            self.handle_recording(frame, person_boxes)
            self.relays.update(present)
            STATE["present"] = sorted(present); STATE["manual"] = manual_active()
            if "prealarm" in present:
                self.pre_last = t0
                if not self.pre_since:
                    self.pre_since = t0
                elif t0 - self.pre_since >= 0.5:
                    if not self.pre_alerted:                # one browser alarm per movement phase (5 s of calm ends it)
                        self.pre_alerted = True
                        push_alert("prealarm", "movement", source=STATE["source_label"])
                    if CFG["notify_prealarm"] and self.notifier.prealarm(frame):
                        log_event("person", "Pre-alarm: movement - push message sent")
            else:
                self.pre_since = 0.0
                if self.pre_alerted and t0 - self.pre_last > 5.0:
                    self.pre_alerted = False

            if CFG["show_hud"]:
                hud = (f"{'RAIN MODE' if rain_mode else 'No rain'} | Wind: {STATE['wind_level']} x{STATE['wind_boost']} | "
                       f"Persons: {len(person_boxes)} | Pan {CFG['pan']:.0f}% Tilt {CFG['tilt']:.0f}% | {STATE['patrol_status']}"
                       + (f" | CPU {STATE['cpu']:.0f}%" if STATE["cpu"] is not None else "")
                       + (f" {STATE['cpu_temp']:.0f}C" if STATE["cpu"] is not None and STATE["cpu_temp"] is not None else "")
                       + (" | MANUAL" if STATE["manual"] else "")
                       + (" | IR" if CFG["thermal_on"] and STATE["thermal"] == "connected" else "")
                       + (f" | WiFi {STATE['wifi']['dbm']}dBm" if STATE["wifi"] and STATE["wifi"]["connected"] else "")
                       + (" | TIMELAPSE" if TL_HOLD["on"] else ""))
                cv2.rectangle(frame, (0, 0), (W, 34), (0, 0, 0), -1)
                cv2.putText(frame, hud, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 160, 255) if rain_mode else (230, 230, 230), 2)
                if STATE["recording"]:
                    cv2.circle(frame, (W - 24, 17), 8, (0, 0, 255), -1)

            self.frame_times.append(time.time() - t0)
            with LOCK:
                STATE.update(rain_score=round(rain_score, 2), rain_mode=rain_mode, persons=len(person_boxes),
                             candidates=len(candidates), fps=round(1.0 / max(1e-3, np.mean(self.frame_times)), 1),
                             frames=STATE["frames"] + 1, uptime=int(time.time() - START))
            self.frame_out = frame
            if CFG["web_stream"] and self.web_viewers > 0:
                out, ww = frame, int(CFG["web_width"])
                if W > ww:
                    out = cv2.resize(frame, (ww, int(H * ww / W)), interpolation=cv2.INTER_AREA)
                ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(CFG["web_quality"])])
                if ok:
                    self.jpeg = buf.tobytes(); self.jpeg_seq += 1


# ----------------------------------------------------------------------------
# Web access options (set on the command line) + self-signed certificate + systemd unit
# ----------------------------------------------------------------------------
WEB_OPTS = {"bind": "0.0.0.0", "https": False, "cert": "", "key": ""}


def ensure_cert():
    """Use the given certificate, or create (once) a self-signed one next to the script. Returns (cert, key) or (None, None)."""
    if WEB_OPTS["cert"] and WEB_OPTS["key"]:
        return WEB_OPTS["cert"], WEB_OPTS["key"]
    cert, key = os.path.join(DATA_DIR, "motionwatch_cert.pem"), os.path.join(DATA_DIR, "motionwatch_key.pem")
    if os.path.isfile(cert) and os.path.isfile(key):
        return cert, key
    if shutil.which("openssl") is None:
        return None, None
    import socket
    host = socket.gethostname()
    for san in (f"subjectAltName=DNS:localhost,DNS:{host},DNS:{host}.local,IP:127.0.0.1", None):
        cmd = ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "3650", "-subj", f"/CN={host}"]
        if san:
            cmd += ["-addext", san]
        try:
            if subprocess.run(cmd, capture_output=True, timeout=60).returncode == 0:
                os.chmod(key, 0o600)
                log_event("web", "Self-signed certificate created (browsers will show a warning once; import the .pem to remove it)")
                return cert, key
        except (OSError, subprocess.SubprocessError):
            pass
    return None, None


def service_text():
    import shlex
    args = [a for a in sys.argv[1:] if a not in ("--print-service", "--install-service")]
    if "--headless" not in args:
        args.append("--headless")
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "pi"
    exe = " ".join(shlex.quote(x) for x in [sys.executable, os.path.abspath(__file__)] + args)
    return f"""[Unit]
Description=Motion Watch (camera motion / person detection)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={HERE}
ExecStart={exe}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""


def install_service():
    path = "/etc/systemd/system/motionwatch.service"
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        print("Installing a system service needs root. Run the same command again with sudo, e.g.:\n"
              f"   sudo {sys.executable} {os.path.abspath(__file__)} --install-service {' '.join(a for a in sys.argv[1:] if a != '--install-service')}\n"
              "or print the unit file with --print-service and install it yourself."); return 1
    with open(path, "w") as f:
        f.write(service_text())
    for cmd in (["systemctl", "daemon-reload"], ["systemctl", "enable", "--now", "motionwatch.service"]):
        print("$", " ".join(cmd)); subprocess.run(cmd)
    print(f"Service installed ({path}). Status: systemctl status motionwatch   Log: journalctl -u motionwatch -f")
    return 0


# ----------------------------------------------------------------------------
# Recordings backend (used by the preview page /recordings)
#   person_YYYYmmdd_HHMMSS.mp4   video          person_YYYYmmdd_HHMMSS.jpg   snapshot of the same event
#   person_YYYYmmdd_HHMMSS.json  info file (source, schedules, duration, codec) written when a recording ends
#   snapshot_*.jpg               manual snapshots
# Thumbnails are cached in recordings/.thumbs, browser-playable copies in recordings/.cache
# ----------------------------------------------------------------------------
REC_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,120}$")
REC_EXTS = {".mp4": "video", ".jpg": "image"}
_STAMP_RE = re.compile(r"(\d{8})_(\d{6})")
BROWSER_CODECS = {"avc1", "h264", "x264"}                   # what <video> can play everywhere (MPEG-4 part 2 "mp4v" cannot)
_BAD_CODECS = set()                                         # encoders that failed once (avc1 is missing in many OpenCV builds)
_REC_META = {}                                              # name -> [mtime, size, meta, probed]
_TRANSCODE = {}                                             # name -> "running" | "done" | "error: ..."
_TRANSCODE_LOCK = threading.Lock()
_TRANSCODE_SEM = threading.Semaphore(1)                     # one conversion at a time, the detection must keep running


# ---- encoder: ffmpeg pipe (hardware H.264 on Pi 3/4, x264 elsewhere) ------------------------------------------
_ENC = {"hw": None}


def _ffmpeg_hw_ok():
    if _ENC["hw"] is None:
        try:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
                                "-frames:v", "5", "-c:v", "h264_v4l2m2m", "-pix_fmt", "yuv420p", "-f", "null", "-"],
                               capture_output=True, timeout=20)
            _ENC["hw"] = r.returncode == 0
        except Exception:
            _ENC["hw"] = False
    return _ENC["hw"]


class FfmpegWriter:
    """Looks like cv2.VideoWriter, but pipes the frames into ffmpeg from a background thread, so the detection never waits
    for the encoder. Fragmented MP4: a recording survives a power loss up to the last few seconds."""
    def __init__(self, path, fps, size, hw):
        w, h = size
        enc = ["-c:v", "h264_v4l2m2m", "-b:v", "4M"] if hw else ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "25"]
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-framerate", f"{fps:.2f}",
               "-i", "-", "-an", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"] + enc + \
              ["-movflags", "+frag_keyframe+empty_moov+default_base_moof", path]
        if shutil.which("nice"):
            cmd = ["nice", "-n", "5"] + cmd
        self.size = (w, h); self.failed = False; self.dropped = 0
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.q = queue.Queue(maxsize=60)
        self.th = threading.Thread(target=self._pump, daemon=True); self.th.start()

    def _pump(self):
        while True:
            item = self.q.get()
            if item is None:
                break
            try:
                self.proc.stdin.write(item)
            except (BrokenPipeError, OSError, ValueError):
                self.failed = True
                break
        try:
            self.proc.stdin.close()
        except Exception:
            pass

    def isOpened(self):
        return self.proc.poll() is None and not self.failed

    def write(self, frame):
        if self.failed or self.proc.poll() is not None:
            self.failed = True; return
        try:
            self.q.put_nowait(frame.tobytes())
        except queue.Full:
            self.dropped += 1                                   # encoder too slow: drop a frame instead of stalling the detection

    def release(self):
        try:
            self.q.put(None, timeout=5)
        except queue.Full:
            self.proc.kill()
        self.th.join(30)
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def open_writer(path, fps, size):
    """Open a video writer. H.264 plays in every browser. Order: ffmpeg (hardware, then x264) -> OpenCV 'avc1' -> OpenCV 'mp4v'
    (mp4v is the last resort; the preview page converts such files on first play). Returns (writer or None, codec)."""
    if CFG["record_encoder"] == "auto" and "ffmpeg" not in _BAD_CODECS and shutil.which("ffmpeg"):
        for hw in ((True, False) if _ffmpeg_hw_ok() else (False,)):
            try:
                w = FfmpegWriter(path, fps, size, hw)
                time.sleep(0.2)
                if w.isOpened():
                    STATE["recording_enc"] = "ffmpeg h264_v4l2m2m (hardware)" if hw else "ffmpeg x264"
                    return w, "h264"
                w.release()
            except Exception:
                pass
            try:
                os.remove(path)
            except OSError:
                pass
        _BAD_CODECS.add("ffmpeg")
    for cc in ("avc1", "mp4v"):
        if cc in _BAD_CODECS:
            continue
        try:
            w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*cc), fps, size)
        except Exception:
            w = None
        if w is not None and w.isOpened():
            STATE["recording_enc"] = "OpenCV " + cc
            return w, cc
        _BAD_CODECS.add(cc)
        if w is not None:
            w.release()
        try:
            os.remove(path)
        except OSError:
            pass
    return None, ""


def rec_dir():
    return os.path.abspath(CFG["record_dir"])


def rec_path(name):
    """Absolute path of a file in the recordings folder, or None (guards against path tricks like ../)."""
    if not isinstance(name, str) or not REC_NAME_RE.match(name) or ".." in name:
        return None
    p = os.path.join(rec_dir(), name)
    return p if os.path.isfile(p) else None


def parse_stamp(name):
    m = _STAMP_RE.search(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _read_sidecar(name):
    try:
        with open(os.path.join(rec_dir(), os.path.splitext(name)[0] + ".json")) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def rec_meta(name, st, probe=False):
    """Info about a video: the info file, completed by looking into the file itself (codec, duration) when asked."""
    e = _REC_META.get(name)
    if e is None or e[0] != st.st_mtime or e[1] != st.st_size:
        e = _REC_META[name] = [st.st_mtime, st.st_size, _read_sidecar(name), False]
        if len(_REC_META) > 5000:                           # keep the cache small
            for k in list(_REC_META)[:1000]:
                _REC_META.pop(k, None)
    meta = e[2]
    if probe and not e[3] and not (meta.get("codec") and meta.get("duration") is not None):
        e[3] = True
        cap = None
        try:
            cap = cv2.VideoCapture(os.path.join(rec_dir(), name))
            if cap.isOpened():
                v = int(cap.get(cv2.CAP_PROP_FOURCC))
                fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                meta.setdefault("codec", "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4)).strip().lower())
                if meta.get("duration") is None and fps > 0 and frames > 0:
                    meta["duration"] = round(frames / fps, 1)
        except Exception:
            pass
        finally:
            if cap is not None:
                cap.release()
    return meta


def _parse_day(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d")
    except ValueError:
        return None


def list_recordings(args, watch=None):
    """Filtered, sorted, paged list of recordings. Filters: kind, from, to, schedule, source, q, sort, offset, limit."""
    d = rec_dir()
    try:
        names = os.listdir(d)
    except OSError:
        names = []
    files, total_bytes = {}, 0
    for n in names:
        if n.startswith(".") or not REC_NAME_RE.match(n):
            continue
        stem, ext = os.path.splitext(n)
        try:
            st = os.stat(os.path.join(d, n))
        except OSError:
            continue
        total_bytes += st.st_size
        kind = REC_EXTS.get(ext.lower())
        if kind:
            files.setdefault(stem, {})[kind] = (n, st)
    with LOCK:
        plans = [dict(s) for s in SCHEDULES]
    live = watch.rec_name if watch is not None else ""
    live_set = set(LIVE_RECS) | ({live} if live else set())

    items = []
    for stem, kinds in files.items():
        if "video" in kinds:
            n, st = kinds["video"]; kind = "video"; snap = kinds.get("image")
        else:
            n, st = kinds["image"]; kind = "image"; snap = None
        dt = parse_stamp(n) or datetime.fromtimestamp(st.st_mtime)
        meta = rec_meta(n, st)
        items.append({"n": n, "st": st, "kind": kind, "dt": dt, "meta": meta, "snap": snap[0] if snap else None,
                      "sched": [i for i, s in enumerate(plans) if schedule_window_contains(s, dt)]})

    # filters that do not depend on the schedule
    kind_f, src_f, q = args.get("kind", ""), args.get("source", ""), (args.get("q", "") or "").strip().lower()
    d_from, d_to = _parse_day(args.get("from", "")), _parse_day(args.get("to", ""))
    sources = sorted({it["meta"].get("source") for it in items if it["meta"].get("source")})
    if kind_f in ("video", "image"):
        items = [it for it in items if it["kind"] == kind_f]
    if d_from:
        items = [it for it in items if it["dt"] >= d_from]
    if d_to:
        items = [it for it in items if it["dt"] < d_to.replace(hour=0) + timedelta(days=1)]
    if src_f:
        items = [it for it in items if it["meta"].get("source") == src_f]
    if q:
        items = [it for it in items if q in it["n"].lower()]

    if args.get("fav") == "1":
        items = [it for it in items if it["meta"].get("fav")]
    counts = {"all": len(items), "any": sum(1 for it in items if it["sched"]), "none": sum(1 for it in items if not it["sched"])}
    for i in range(len(plans)):
        counts[str(i)] = sum(1 for it in items if i in it["sched"])
    sch_f = args.get("schedule", "")
    if sch_f == "any":
        items = [it for it in items if it["sched"]]
    elif sch_f == "none":
        items = [it for it in items if not it["sched"]]
    elif sch_f.isdigit():
        items = [it for it in items if int(sch_f) in it["sched"]]

    sort = args.get("sort", "new")
    if sort == "old":
        items.sort(key=lambda it: it["dt"])
    elif sort == "size":
        items.sort(key=lambda it: it["st"].st_size, reverse=True)
    else:
        items.sort(key=lambda it: it["dt"], reverse=True)

    try:
        offset = max(0, int(args.get("offset", 0))); limit = max(1, min(200, int(args.get("limit", 48))))
    except (TypeError, ValueError):
        offset, limit = 0, 48
    page = []
    for it in items[offset:offset + limit]:
        meta = rec_meta(it["n"], it["st"], probe=True) if it["kind"] == "video" else it["meta"]
        codec = (meta.get("codec") or "").lower()
        page.append({"name": it["n"], "kind": it["kind"], "time": it["dt"].strftime("%Y-%m-%d %H:%M:%S"),
                     "size": it["st"].st_size, "duration": meta.get("duration"), "source": meta.get("source"),
                     "persons": meta.get("persons"), "schedules": [plans[i]["name"] for i in it["sched"]],
                     "playable": (codec in BROWSER_CODECS) if codec else None, "snap": it["snap"], "fav": bool(meta.get("fav")),
                     "recording": it["n"] in live_set})
    now = datetime.now()
    return {"total": len(items), "items": page, "counts": counts, "sources": sources, "recording": bool(live_set),
            "schedules": [{"index": i, "name": s["name"], "enabled": s["enabled"], "days": s["days"], "start": s["start"],
                           "end": s["end"], "active_now": schedule_active(s, now), "count": counts.get(str(i), 0)}
                          for i, s in enumerate(plans)],
            "disk": {"files": len(files), "mb": int(total_bytes / 1024 ** 2), "limit_gb": CFG["record_max_gb"]},
            "ffmpeg": shutil.which("ffmpeg") is not None}


def _write_sidecar(name, meta):
    stem = os.path.splitext(name)[0]
    p = os.path.join(rec_dir(), stem + ".json")
    tmp = p + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(meta, f)
        os.replace(tmp, p)
    except OSError:
        return False
    for k in (stem + ".mp4", stem + ".jpg"):
        _REC_META.pop(k, None)
    return True


def rec_set_fav(names, value, watch=None):
    """Star / un-star recordings. Starred recordings are never removed by the automatic cleanup."""
    n = 0
    for name in (names if isinstance(names, list) else [])[:500]:
        if not rec_path(name) or name.lower().endswith(".json") or _is_live(name, watch):
            continue
        meta = _read_sidecar(name)
        if value:
            meta["fav"] = True
        else:
            meta.pop("fav", None)
        if _write_sidecar(name, meta):
            n += 1
    return n


def rec_clean_tmp():
    tdir = os.path.join(rec_dir(), ".tmp")
    try:
        for f in os.listdir(tdir):
            p = os.path.join(tdir, f)
            if time.time() - os.path.getmtime(p) > 3600:
                os.remove(p)
    except OSError:
        pass


def rec_zip(names, watch=None):
    """Pack recordings (video + snapshot) into one ZIP in the temp folder. Returns the path or None."""
    tdir = os.path.join(rec_dir(), ".tmp")
    os.makedirs(tdir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".zip", dir=tdir); os.close(fd)
    count, seen = 0, set()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for name in (names if isinstance(names, list) else [])[:300]:
            if not rec_path(name) or _is_live(name, watch):
                continue
            stem, ext = os.path.splitext(name)
            for e in ((".mp4", ".jpg") if ext.lower() == ".mp4" else (ext.lower(),)):
                p = os.path.join(rec_dir(), stem + e)
                if os.path.isfile(p) and p not in seen:
                    seen.add(p); z.write(p, os.path.basename(p)); count += 1
    if not count:
        os.remove(tmp)
        return None
    return tmp


def _scan_events():
    """[(datetime, name, kind)] - one entry per recorded event (the video if there is one, else the picture)."""
    d = rec_dir()
    try:
        names = os.listdir(d)
    except OSError:
        return []
    files = {}
    for n in names:
        if n.startswith(".") or not REC_NAME_RE.match(n):
            continue
        stem, ext = os.path.splitext(n)
        kind = REC_EXTS.get(ext.lower())
        if kind:
            files.setdefault(stem, {})[kind] = n
    out = []
    for stem, k in files.items():
        n = k.get("video") or k["image"]
        dt = parse_stamp(n)
        if dt is None:
            try:
                dt = datetime.fromtimestamp(os.path.getmtime(os.path.join(d, n)))
            except OSError:
                continue
        out.append((dt, n, "video" if "video" in k else "image"))
    return out


_STATS = {"t": 0.0, "key": None, "val": None}


def rec_stats(days=14, day=None):
    """Events per day / hour for the statistics card of the preview page + the events of one day for the timeline."""
    try:
        days = max(1, min(90, int(days)))
    except (TypeError, ValueError):
        days = 14
    key = (days, day, len(os.listdir(rec_dir())) if os.path.isdir(rec_dir()) else 0)
    if _STATS["key"] == key and time.time() - _STATS["t"] < 10:
        return _STATS["val"]
    events = _scan_events()
    today = datetime.now().date(); start = today - timedelta(days=days - 1)
    per_day, heat = {}, [[0] * 24 for _ in range(7)]
    for dt, name, kind in events:
        dd = dt.date()
        if start <= dd <= today:
            per_day.setdefault(dd, [0] * 24)[dt.hour] += 1
            heat[dt.weekday()][dt.hour] += 1
    lst = []
    for i in range(days):
        dd = start + timedelta(days=i); hrs = per_day.get(dd, [0] * 24)
        lst.append({"date": dd.isoformat(), "hours": hrs, "count": sum(hrs)})
    ev = []
    dd = _parse_day(day) if day else None
    if dd:
        ev = sorted(({"m": dt.hour * 60 + dt.minute, "t": dt.strftime("%H:%M:%S"), "name": n, "kind": k}
                     for dt, n, k in events if dt.date() == dd.date()), key=lambda e: e["m"])
    val = {"days": lst, "heat": heat, "events": ev, "day": day, "total": len(events)}
    _STATS.update(t=time.time(), key=key, val=val)
    return val


def rec_thumb(name):
    """Path of a small cached JPEG thumbnail (320 px wide) for a video or snapshot, or None."""
    path = rec_path(name)
    if not path:
        return None
    tdir = os.path.join(rec_dir(), ".thumbs")
    tp = os.path.join(tdir, name + ".jpg")
    try:
        if os.path.isfile(tp) and os.path.getmtime(tp) >= os.path.getmtime(path):
            return tp
        os.makedirs(tdir, exist_ok=True)
        img = None
        if name.lower().endswith(".jpg"):
            img = cv2.imread(path)
        else:
            snap = path[:-4] + ".jpg"                          # the snapshot of the same event is the cheapest thumbnail
            if os.path.isfile(snap):
                img = cv2.imread(snap)
            if img is None:
                cap = cv2.VideoCapture(path)
                try:
                    ok, img = cap.read()
                    img = img if ok else None
                finally:
                    cap.release()
        if img is None:
            return None
        h, w = img.shape[:2]
        img = cv2.resize(img, (320, max(1, int(h * 320 / w))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(tp, img, [cv2.IMWRITE_JPEG_QUALITY, 72])
        return tp
    except Exception:
        return None


def _cache_path(name):
    return os.path.join(rec_dir(), ".cache", os.path.splitext(name)[0] + ".h264.mp4")


def _transcode(name, src, dst):
    tmp = dst + ".part.mp4"
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        cmd = (["nice", "-n", "10"] if shutil.which("nice") else []) + [
            "ffmpeg", "-y", "-loglevel", "error", "-i", src, "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
        with _TRANSCODE_SEM:
            r = subprocess.run(cmd, capture_output=True, timeout=1800)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode(errors="replace").strip()[-200:] or f"ffmpeg exit {r.returncode}")
        os.replace(tmp, dst)
        _TRANSCODE[name] = "done"
    except Exception as e:
        _TRANSCODE[name] = f"error: {e}"
        try:
            os.remove(tmp)
        except OSError:
            pass


def rec_play_state(name, watch=None):
    """What the browser can play for this video: ready (url) / converting / unsupported / error / missing."""
    path = rec_path(name)
    if not path or not name.lower().endswith(".mp4"):
        return {"state": "missing"}
    if _is_live(name, watch):
        return {"state": "live"}                                # still being written, the file is not complete yet
    try:
        meta = rec_meta(name, os.stat(path), probe=True)
    except OSError:
        return {"state": "missing"}
    if (meta.get("codec") or "").lower() in BROWSER_CODECS:
        return {"state": "ready", "url": "/rec/file/" + name}
    dst = _cache_path(name)
    if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(path):
        return {"state": "ready", "url": "/rec/play/" + name}
    if shutil.which("ffmpeg") is None:
        return {"state": "unsupported", "url": "/rec/file/" + name + "?dl=1"}
    with _TRANSCODE_LOCK:
        cur = _TRANSCODE.get(name, "")
        if cur == "running":
            return {"state": "converting"}
        if cur.startswith("error"):
            _TRANSCODE.pop(name, None)
            return {"state": "error", "error": cur[7:]}
        _TRANSCODE[name] = "running"
    threading.Thread(target=_transcode, args=(name, path, dst), daemon=True).start()
    return {"state": "converting"}


def rec_purge_extras(stem):
    """Remove cached thumbnails / converted copies that belong to a recording."""
    for p in (os.path.join(rec_dir(), ".thumbs", stem + ".mp4.jpg"), os.path.join(rec_dir(), ".thumbs", stem + ".jpg.jpg"),
              os.path.join(rec_dir(), ".cache", stem + ".h264.mp4")):
        try:
            os.remove(p)
        except OSError:
            pass
    for k in (stem + ".mp4", stem + ".jpg"):
        _REC_META.pop(k, None); _TRANSCODE.pop(k, None)


def rec_delete(names, watch=None):
    """Delete recordings (video + snapshot + info file of each). Returns how many were deleted."""
    n_ok = 0
    for name in (names if isinstance(names, list) else [])[:500]:
        path = rec_path(name)
        if not path or _is_live(name, watch):
            continue
        stem = os.path.splitext(name)[0]
        for ext in ((".mp4", ".jpg", ".json") if name.lower().endswith(".mp4") else (os.path.splitext(name)[1].lower(),)):
            try:
                os.remove(os.path.join(rec_dir(), stem + ext))
            except OSError:
                pass
        rec_purge_extras(stem)
        n_ok += 1
    if n_ok:
        log_event("rec", f"{n_ok} recording(s) deleted from the preview page")
    return n_ok


# ----------------------------------------------------------------------------
# More cameras at the same time (motion recording only: no AI, no servos)
#   The first camera (the "source") does the full job. Extra cameras watch for movement, record clips (cam<n>_<time>.mp4 + snapshot)
#   and can be viewed in the grid at /cams. They follow the same switches (detection, recording) and schedules.
# ----------------------------------------------------------------------------
CAMS = []
LIVE_RECS = set()                    # file names that are being written right now (never deleted / zipped)
WATCH_REF = {"w": None}


def _is_live(name, watch=None):
    return name in LIVE_RECS or (watch is not None and bool(watch.rec_name) and watch.rec_name == name)


class ExtraCam:
    def __init__(self, idx, spec):
        self.idx, self.spec = idx, spec
        self.stop = False
        self.jpeg = None; self.seq = 0; self.viewers = 0; self._enc_t = 0.0
        self.status = "connecting…"; self.label = source_label(spec); self.res = ""; self.fps = 0.0
        self.motion = False; self.recording = False
        self.writer = None; self.rec_name = ""; self.rec_info = None; self.last_motion = 0.0; self.streak = 0
        self.boxes = []; self.times = deque(maxlen=30); self.n = 0; self.last_cleanup = 0.0
        self.thread = threading.Thread(target=self.loop, daemon=True); self.thread.start()

    def info(self):
        return {"n": self.idx, "id": self.spec, "label": self.label, "status": self.status, "res": self.res,
                "fps": round(self.fps, 1), "motion": self.motion, "recording": self.recording}

    def close(self):
        self.stop = True
        self.thread.join(4.0)
        self._stop_rec()

    def _sleep(self, sec):
        end = time.time() + sec
        while not self.stop and time.time() < end:
            time.sleep(0.2)

    def loop(self):
        while not self.stop:
            src, sid, label, err = open_source(self.spec)
            if src is None:
                self.status = f"failed: {err}"; self._sleep(6.0); continue
            self.label = label; self.status = "connected"
            self.res = f"{src.size[0]}x{src.size[1]}" if getattr(src, "size", None) else ""
            bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=28, detectShadows=False)
            fails, self.n = 0, 0
            try:
                while not self.stop:
                    ok, frame = src.read()
                    if not ok:
                        fails += 1
                        if fails >= 60:
                            break
                        time.sleep(0.05); continue
                    fails = 0
                    self._process(frame, bg)
            except Exception as e:
                log_event("sys", f"Camera {self.label}: {e}")
            finally:
                src.release(); self._stop_rec()
            if not self.stop:
                self.status = "connection lost - reconnecting"; self.motion = False; self._sleep(2.0)

    def _process(self, frame, bg):
        t0 = time.time()
        self.n += 1
        H, W = frame.shape[:2]
        if self.n % 2 == 0 or not self.times:                  # detection on every 2nd frame is enough
            pw = 320; ph = max(1, int(H * pw / W)); sx = W / pw; sy = H / ph
            gray = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(frame, (pw, ph)), cv2.COLOR_BGR2GRAY), (5, 5), 0)
            fg = bg.apply(gray)
            fg = cv2.dilate(cv2.erode(cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)[1], None, iterations=1), None, iterations=2)
            cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            amin = CFG["min_area"] * (1.0 - CFG["sensitivity"] / 200.0) * (320.0 / 480.0) ** 2
            self.boxes = [(int(x * sx), int(y * sy), int(w * sx), int(h * sy)) for x, y, w, h in
                          (cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) >= amin)] if self.n > 30 else []
            self.motion = bool(self.boxes) and CFG["detection_on"]
            self.streak = self.streak + 1 if self.motion else 0
        now = time.time()
        if self.motion and self.streak >= 3:
            self.last_motion = now
        for x, y, w, h in self.boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
        cv2.rectangle(frame, (0, 0), (W, 26), (0, 0, 0), -1)
        cv2.putText(frame, self.label.encode("ascii", "replace").decode()[:40] + ("   MOTION" if self.motion else ""), (8, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 160, 255) if self.motion else (230, 230, 230), 1, cv2.LINE_AA)
        want = CFG["record"] and CFG["detection_on"] and self.last_motion > 0 and now - self.last_motion < CFG["record_tail"]
        if want and self.writer is None:
            self._start_rec(frame)
        elif not want and self.writer is not None:
            self._stop_rec()
        if self.writer is not None:
            self.writer.write(frame); self.rec_info["frames"] += 1
        self.recording = self.writer is not None
        self.times.append(time.time() - t0)
        if self.n % 15 == 0:
            self.fps = 1.0 / max(1e-3, np.mean(self.times)) if self.times else 0.0
        if self.viewers > 0 and now - self._enc_t >= 0.1:        # only encode while somebody watches
            self._enc_t = now
            out = frame if W <= 640 else cv2.resize(frame, (640, int(H * 640 / W)), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 65])
            if ok:
                self.jpeg = buf.tobytes(); self.seq += 1

    def _start_rec(self, frame):
        h, w = frame.shape[:2]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"cam{self.idx}_{stamp}"
        wr, codec = open_writer(os.path.join(CFG["record_dir"], base + ".mp4"), 12.0, (w, h))
        if wr is None:
            self.last_motion = 0.0; return
        if time.time() - self.last_cleanup > 60 and WATCH_REF["w"] is not None:
            WATCH_REF["w"].cleanup_recordings(); self.last_cleanup = time.time()
        if CFG["snapshot_on_person"]:
            cv2.imwrite(os.path.join(CFG["record_dir"], base + ".jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        self.writer = wr; self.rec_name = base + ".mp4"; LIVE_RECS.add(self.rec_name)
        fps = max(5.0, min(30.0, self.fps or 12.0))
        self.rec_info = {"start": time.time(), "fps": fps, "frames": 0, "codec": codec, "schedules": list(SCHED["active"])}
        log_event("rec", f"Recording started: {self.rec_name} ({self.label})")

    def _stop_rec(self):
        if self.writer is None:
            return
        wr, self.writer = self.writer, None
        wr.release()
        info, name = self.rec_info, self.rec_name
        self.rec_info = None; self.recording = False
        try:
            meta = {"start": datetime.fromtimestamp(info["start"]).isoformat(timespec="seconds"),
                    "end": datetime.now().isoformat(timespec="seconds"), "frames": info["frames"],
                    "duration": round(info["frames"] / max(1.0, info["fps"]), 1), "fps": round(info["fps"], 1), "codec": info["codec"],
                    "persons": 0, "motion": True, "source": self.label, "source_id": self.spec, "schedules": info["schedules"]}
            with open(os.path.join(CFG["record_dir"], os.path.splitext(name)[0] + ".json"), "w") as f:
                json.dump(meta, f)
        except OSError:
            pass
        LIVE_RECS.discard(name); self.rec_name = ""
        log_event("rec", f"Recording stopped: {name}")


def cams_apply():
    """Start / stop the extra camera threads so they match the settings."""
    want = list(CFG["extra_cams"])
    for c in list(CAMS):
        if c.spec not in want:
            CAMS.remove(c); threading.Thread(target=c.close, daemon=True).start()
    have = {c.spec for c in CAMS}
    used = {c.idx for c in CAMS}
    for spec in want:
        if spec not in have:
            idx = next(i for i in range(1, 99) if i not in used); used.add(idx)
            CAMS.append(ExtraCam(idx, spec))


def cams_status(watch=None):
    main = {"n": 0, "id": STATE["source_id"] or CFG["source"], "label": STATE["source_label"] or source_label(CFG["source"]),
            "status": STATE["source_status"], "res": STATE["source_res"], "fps": STATE["fps"],
            "motion": bool(STATE["persons"] or STATE["candidates"]), "recording": STATE["recording"]}
    return [main] + [c.info() for c in CAMS]


def cams_add(spec):
    if not isinstance(spec, str) or not SRC_RE.match(spec) or spec == "auto":
        return False, "unknown source"
    if spec.startswith("url:") and not find_ip_source(spec[4:]):
        return False, "unknown network camera"
    if spec in CFG["extra_cams"] or spec == STATE["source_id"]:
        return False, "this camera is already in use"
    if len(CFG["extra_cams"]) >= MAX_EXTRA:
        return False, f"maximum {MAX_EXTRA} extra cameras"
    CFG["extra_cams"] = CFG["extra_cams"] + [spec]
    save_settings(); cams_apply(); log_event("sys", f"Extra camera added: {source_label(spec)}")
    return True, ""


def cams_remove(spec):
    if spec not in CFG["extra_cams"]:
        return False, "unknown source"
    CFG["extra_cams"] = [x for x in CFG["extra_cams"] if x != spec]
    save_settings(); cams_apply(); log_event("sys", f"Extra camera removed: {source_label(spec)}")
    return True, ""


def cams_close_all():
    for c in list(CAMS):
        c.stop = True
    for c in list(CAMS):
        c.thread.join(3.0); c._stop_rec()


atexit.register(cams_close_all)


# ----------------------------------------------------------------------------
# Web stream + remote control (Flask) - http://<pi-ip>:5000/
#   /              control page (live video, pan/tilt pad, CPU, all settings)
#   /video_feed    raw MJPEG stream          /snapshot.jpg   current frame
#   /api/...       JSON API used by the page (state, set, move, action, relay, triggers)
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Shared look of all web pages (header, navigation, buttons, cards, forms)
# ----------------------------------------------------------------------------
BASE_CSS = r"""
:root{--bg:#0a0e14;--panel:#111822;--panel2:#151e2b;--line:#1f2b3a;--txt:#e8eef5;--mut:#8a9bb0;--acc:#3b8cff;--acc2:#6aa9ff;--red:#ff4d4d;--grn:#3fcf6b;--yel:#e0a526;--blu:#5aa9ff;--org:#f59a4a;--pur:#b794f6;--field:#0c121a;--btn2:#1a2433;--hdr:rgba(10,14,20,.8);--glow:rgba(59,140,255,.13);--shadow:0 1px 2px rgba(0,0,0,.45),0 10px 28px rgba(0,0,0,.22);--r:14px}
body.light{--bg:#eef2f7;--panel:#ffffff;--panel2:#f8fafc;--line:#d7dfea;--txt:#18212d;--mut:#5a6b80;--acc:#1f6feb;--acc2:#4d8ff5;--red:#d1242f;--grn:#1a8f3c;--yel:#9a6700;--blu:#0969da;--org:#bc4c00;--pur:#8250df;--field:#f2f5fa;--btn2:#e3e9f2;--hdr:rgba(238,242,247,.85);--glow:rgba(31,111,235,.10);--shadow:0 1px 2px rgba(20,30,50,.08),0 10px 28px rgba(20,30,50,.08)}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{scrollbar-width:thin;scrollbar-color:var(--line) transparent}
body{margin:0;color:var(--txt);font:14px/1.45 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh;
  background:radial-gradient(1100px 480px at 75% -8%,var(--glow),transparent 70%),var(--bg);background-attachment:fixed}
header{position:sticky;top:0;z-index:30;display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;padding:10px 16px;
  background:var(--hdr);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
header h1{font-size:17px;margin:0 8px 0 0;font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:9px}
header h1::before{content:"";width:11px;height:11px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 4px var(--glow),0 0 14px var(--acc)}
.nav{display:flex;gap:2px;background:var(--field);border:1px solid var(--line);border-radius:11px;padding:3px}
.nav a{padding:5px 13px;border-radius:8px;color:var(--mut);text-decoration:none;font-weight:600;font-size:13px;white-space:nowrap}
.nav a:hover{color:var(--txt)}.nav a.on{background:var(--acc);color:#fff;box-shadow:0 2px 10px var(--glow)}
.badge{display:inline-flex;align-items:center;gap:6px;padding:3px 11px;border:1px solid var(--line);border-radius:99px;font-size:12px;font-weight:600;color:var(--mut);background:var(--field);white-space:nowrap}
.badge.red{color:var(--red);border-color:var(--red)}.badge.blu{color:var(--blu);border-color:var(--blu)}
.badge.yel{color:var(--yel);border-color:var(--yel)}.badge.grn{color:var(--grn);border-color:var(--grn)}
.badge.org{color:var(--org);border-color:var(--org)}
.hdr-ctl{margin-left:auto;display:flex;gap:6px;align-items:center}
.hdr-ctl button,.hdr-ctl .btn{padding:5px 11px;font-size:13px}
button,.btn{background:var(--acc);color:#fff;border:0;border-radius:9px;padding:8px 14px;font:inherit;font-weight:600;cursor:pointer;text-decoration:none;text-align:center;display:inline-block;transition:filter .12s,transform .06s,background .15s}
button:hover,.btn:hover{filter:brightness(1.1)}
button:active,.btn:active{transform:translateY(1px);filter:brightness(1.2)}
button:focus-visible,.btn:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--acc2);outline-offset:2px}
button.sec,.btn.sec{background:var(--btn2);color:var(--txt);border:1px solid var(--line)}
button.red{background:var(--red)}
button:disabled{opacity:.5;cursor:default;filter:none;transform:none}
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:var(--r);padding:14px;margin-bottom:14px;box-shadow:var(--shadow)}
details.card>summary{margin:0;font-size:11px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;user-select:none}
details.card>summary::after{content:"▾";font-size:13px;transition:transform .15s}
details.card:not([open])>summary::after{transform:rotate(-90deg)}
details.card[open]>summary{margin-bottom:10px}
details.card>summary::-webkit-details-marker{display:none}
select,input[type=text],input[type=number],input[type=date],input[type=time],input[type=password]{background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:6px 9px;font:inherit;color-scheme:dark;max-width:100%}
body.light select,body.light input[type=date],body.light input[type=time]{color-scheme:light}
select:focus,input:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px var(--glow)}
input[type=range]{width:100%;accent-color:var(--acc);margin:4px 0 0}
input[type=checkbox],input[type=radio]{accent-color:var(--acc)}
input.sw{appearance:none;-webkit-appearance:none;width:42px;height:24px;border-radius:12px;background:#2a3542;position:relative;cursor:pointer;flex:none;outline:none;transition:background .15s;margin:0;border:0;padding:0}
input.sw::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:left .15s;box-shadow:0 1px 3px rgba(0,0,0,.4)}
input.sw:checked{background:var(--acc)}input.sw:checked::after{left:21px}
body.light input.sw{background:#c4ccd8}body.light input.sw:checked{background:var(--acc)}
.mut{color:var(--mut);font-size:12px}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px}
.err{color:var(--red);font-size:12px;min-height:16px}
.vh{display:none!important}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.btns>*{flex:1 1 auto}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border-radius:0;padding:5px 11px;font-size:12px;background:transparent;color:var(--mut)}
.seg button.sel-off{background:var(--mut);color:#fff}.seg button.sel-on{background:var(--grn);color:#fff}.seg button.sel-auto{background:var(--acc);color:#fff}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:6px}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--panel);border:1px solid var(--line);color:var(--txt);padding:9px 16px;border-radius:10px;box-shadow:var(--shadow);z-index:90;font-weight:600;opacity:0;pointer-events:none;transition:opacity .2s}
#toast.on{opacity:1}
#hdr-show{display:none;position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:70;padding:1px 22px 3px;opacity:.85;
  border-radius:0 0 10px 10px;border-top:0;box-shadow:var(--shadow);font-size:12px;line-height:1.2}
body.hdrhidden header{display:none}body.hdrhidden #hdr-show{display:block}body.videoonly #hdr-show{display:none!important}
body.hdrhidden .sndpop{top:44px}
.sndbtn{position:relative}.sndbtn.on{background:var(--acc);color:#fff;border-color:transparent}
.sndbtn.warn::after{content:"";position:absolute;top:3px;right:3px;width:8px;height:8px;border-radius:50%;background:var(--yel)}
.sndpop{position:fixed;top:58px;right:12px;z-index:80;width:300px;max-width:calc(100vw - 24px)}
.sndpop .row{margin:7px 0}.sndpop .sndhead{font-size:11px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;margin-bottom:6px}
@keyframes alarmflash{0%,60%{box-shadow:inset 0 0 0 4px var(--red)}100%{box-shadow:inset 0 0 0 0 transparent}}
body.alarmflash{animation:alarmflash 1.6s ease-out 2}
@media(max-width:700px){header{padding:8px 10px;gap:5px 6px}.nav a{padding:5px 9px}
  header h1{font-size:15px}.badge{font-size:11px;padding:2px 8px}.hdr-ctl button,.hdr-ctl .btn{padding:4px 9px;font-size:12px}}
"""

NAV_ITEMS = [("live", "/", "Live"), ("cams", "/cams", "Cameras"), ("rec", "/recordings", "Recordings"), ("zones", "/zones", "Zones")]


def nav_html(active):
    out = []
    for key, href, label in NAV_ITEMS:
        cls = ' class="on"' if key == active else ""
        out.append(f'<a href="{href}"{cls} data-i18n="{label}">{label}</a>')
    return '<nav class="nav">' + "".join(out) + "</nav>"


def ui_seed_script():
    """Runs first on every page: copies the saved layout into the browser storage (so the page code finds it there) and
    sends every later layout change back to the Pi, where it is kept in the settings file."""
    data = json.dumps(CFG["web_ui"]).replace("</", "<\\/")
    return ("<script>(function(){var S=" + data + ";try{for(var k in S)localStorage.setItem(k,S[k]);}catch(e){}"
            "var P={},T=null,L=" + json.dumps(sorted(WEB_UI_LOCAL)) + ";"
            "function send(){var b=P;P={};T=null;try{fetch('/api/ui',{method:'POST',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({set:b}),keepalive:true}).catch(function(){});}catch(e){}}"
            "try{var o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){o.call(this,k,v);"
            "try{if(this===window.localStorage&&/^mw-/.test(k)&&L.indexOf(k)<0&&S[k]!==String(v)){S[k]=String(v);P[k]=String(v);"
            "clearTimeout(T);T=setTimeout(send,700);}}catch(e){}};}catch(e){}"
            "addEventListener('pagehide',function(){if(T){clearTimeout(T);send();}});})();</script>")


def render_page(page, active):
    """Fill the shared pieces into a page template."""
    page = page.replace("<head>", "<head>" + ui_seed_script(), 1)
    return (page.replace("/*BASECSS*/", BASE_CSS).replace("/*COMMON*/", COMMON_JS).replace("<!--NAV-->", nav_html(active))
            .replace("/*ALERTS*/", HEADER_JS + ALERT_JS))


HEADER_JS = r"""
// ---- hide / show the whole header (remembered per device) ----
(function () {
  const H = document.querySelector("header"); if (!H) return;
  const TX = {"Hide header": "Kopfzeile ausblenden", "Show header": "Kopfzeile einblenden"};
  const tx = s => (LANG === "de" && TX[s]) || s;
  const hb = el("button", "sec", "▴"); hb.type = "button"; hb.id = "btn-hdr";
  const ctl = H.querySelector(".hdr-ctl"); (ctl || H).appendChild(hb);
  const sh = el("button", "sec", "▾"); sh.type = "button"; sh.id = "hdr-show"; document.body.appendChild(sh);
  function set(hidden, store) {
    document.body.classList.toggle("hdrhidden", hidden);
    hb.title = tx("Hide header"); sh.title = tx("Show header"); hb.setAttribute("aria-label", hb.title); sh.setAttribute("aria-label", sh.title);
    if (store) { try { localStorage.setItem("mw-hdr", hidden ? "0" : "1"); } catch (e) {} }
    window.dispatchEvent(new Event("resize"));
  }
  hb.onclick = () => set(true, true); sh.onclick = () => set(false, true);
  let v = null; try { v = localStorage.getItem("mw-hdr"); } catch (e) {}
  set(v === "0", false);
  setTimeout(() => set(document.body.classList.contains("hdrhidden"), false), 1500);   // titles in the right language
})();
// ---- clock: the Pi has no battery clock; without internet it takes the time of the phone ----
(function () {
  let tz = ""; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
  setTimeout(() => { try { fetch("/api/time", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({t: Date.now(), tz: tz})}).catch(() => {}); } catch (e) {} }, 800);
})();
"""


ALERT_JS = r"""
// ---- alarm sound in the browser (every page): the server sends alarms over a live connection (/api/alerts) ----
(function () {
  const ALT = {"Alarm sound": "Alarmton", "Sound on": "Ton ein", "Pre-alarm (first movement)": "Voralarm (erste Bewegung)",
    "Person detected": "Person erkannt", "Warm body (thermal camera)": "Wärme erkannt (Wärmebild)", "Armed - alarms are active": "Scharf - Alarme aktiv",
    "Person / warm body": "Person / Wärme erkannt", "Volume": "Lautstärke", "Test": "Test", "Vibrate (phones)": "Vibrieren (Handy)",
    "Pre-alarm: movement": "Voralarm: Bewegung", "Tap anywhere on the page to allow the sound": "Irgendwo auf die Seite tippen, um den Ton zu erlauben",
    "Mute 30 min": "30 Min. stumm", "Muted until": "Stumm bis", "Unmute": "Ton wieder an", "Pre-alarm": "Voralarm", "Person": "Person",
    "connection to the camera interrupted - reconnecting": "Verbindung zur Kamera unterbrochen - verbinde neu",
    "The page must stay open (also in the background). With the screen off or the browser closed only the push message (ntfy / Telegram) arrives.":
      "Die Seite muss offen bleiben (auch im Hintergrund geht es). Bei ausgeschaltetem Bildschirm oder geschlossenem Browser kommt nur die Push-Nachricht (ntfy / Telegram)."};
  const at = s => (LANG === "de" && ALT[s]) || s;
  const S = {on: false, pre: true, person: true, vol: 0.7, vib: true, mute: 0};
  try { Object.assign(S, JSON.parse(localStorage.getItem("mw-sound") || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem("mw-sound", JSON.stringify(S)); } catch (e) {} };
  let ctx = null, es = null, lastPre = 0, connOk = true, errTimer = null, titleTimer = null;
  const baseTitle = document.title;

  function audio() {
    if (!ctx) { const A = window.AudioContext || window.webkitAudioContext; if (!A) return null; try { ctx = new A(); } catch (e) { return null; } }
    if (ctx.state === "suspended") ctx.resume().then(paint).catch(() => {});
    return ctx;
  }
  function tone(c, f0, f1, t0, dur, type, vol) {
    const o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(f0, t0);
    if (f1 !== f0) o.frequency.linearRampToValueAtTime(f1, t0 + dur);
    const v = Math.max(0.002, vol);
    g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(v, t0 + 0.02);
    g.gain.setValueAtTime(v, t0 + dur - 0.04); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(c.destination); o.start(t0); o.stop(t0 + dur + 0.03);
  }
  function play(kind) {
    const c = audio(); if (!c) return;
    const v = S.vol * 0.45, t0 = c.currentTime + 0.05;
    if (kind === "prealarm") {                       // two short, friendly beeps
      tone(c, 880, 880, t0, 0.14, "sine", v); tone(c, 1175, 1175, t0 + 0.22, 0.2, "sine", v);
    } else {                                         // person: siren, about 2 seconds
      for (let i = 0; i < 4; i++) { tone(c, 620, 1180, t0 + i * 0.5, 0.25, "triangle", v); tone(c, 1180, 620, t0 + i * 0.5 + 0.25, 0.25, "triangle", v); }
    }
    if (S.vib && navigator.vibrate) { try { navigator.vibrate(kind === "prealarm" ? [120, 80, 120] : [300, 120, 300, 120, 300]); } catch (e) {} }
  }
  const muted = () => S.mute && Date.now() < S.mute;

  // ---- header button ----
  const btn = el("button", "sec sndbtn"); btn.type = "button"; btn.id = "btn-sound";
  const ctl = document.querySelector(".hdr-ctl"); if (ctl) ctl.insertBefore(btn, ctl.firstChild); else document.body.appendChild(btn);
  function paint() {
    const needTap = S.on && (!ctx || ctx.state !== "running");
    btn.textContent = (S.on && !muted()) ? "🔔" : "🔕";
    btn.classList.toggle("on", S.on && !muted() && !needTap && connOk);
    btn.classList.toggle("warn", S.on && (needTap || !connOk));
    btn.title = at("Alarm sound") + (needTap ? " · " + at("Tap anywhere on the page to allow the sound") : "")
      + (!connOk ? " · " + at("connection to the camera interrupted - reconnecting") : "")
      + (muted() ? " · " + at("Muted until") + " " + new Date(S.mute).toLocaleTimeString().slice(0, 5) : "");
  }
  // browsers only allow sound after a click / tap on the page: unlock on the first one
  ["pointerdown", "keydown", "touchstart"].forEach(ev => document.addEventListener(ev, () => { if (S.on) { audio(); setTimeout(paint, 200); } }, {passive: true}));

  // ---- settings panel ----
  let pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function sw(label, key, after) {
    const row = el("label", "row"); const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!S[key];
    cb.onchange = () => { S[key] = cb.checked; save(); if (after) after(); paint(); };
    row.append(el("span", "", at(label)), cb); return row;
  }
  function openPop() {
    closePop();
    pop = el("div", "sndpop card");
    pop.appendChild(el("div", "sndhead", at("Alarm sound")));
    pop.append(sw("Sound on", "on", () => { if (S.on) { audio(); play("prealarm"); } connect(); }),
               sw("Pre-alarm (first movement)", "pre"), sw("Person / warm body", "person"), sw("Vibrate (phones)", "vib"));
    const vr = el("div", "sl"); const top = el("div", "row"); const vv = el("span", "val", Math.round(S.vol * 100) + " %");
    top.append(el("span", "", at("Volume")), vv);
    const r = el("input"); r.type = "range"; r.min = 0.1; r.max = 1; r.step = 0.05; r.value = S.vol;
    r.oninput = () => { S.vol = parseFloat(r.value); vv.textContent = Math.round(S.vol * 100) + " %"; save(); };
    vr.append(top, r); pop.appendChild(vr);
    const b = el("div", "btns");
    const t1 = el("button", "sec", at("Test") + ": " + at("Pre-alarm")); t1.type = "button"; t1.onclick = () => play("prealarm");
    const t2 = el("button", "sec", at("Test") + ": " + at("Person")); t2.type = "button"; t2.onclick = () => play("person");
    const m = el("button", "sec", muted() ? at("Unmute") : at("Mute 30 min")); m.type = "button";
    m.onclick = () => { S.mute = muted() ? 0 : Date.now() + 30 * 60000; save(); paint(); openPop(); };
    b.append(t1, t2, m); pop.appendChild(b);
    const hint = el("div", "mut", at("The page must stay open (also in the background). With the screen off or the browser closed only the push message (ntfy / Telegram) arrives."));
    hint.style.marginTop = "8px"; pop.appendChild(hint);
    pop.addEventListener("pointerdown", e => e.stopPropagation());
    document.body.appendChild(pop);
  }
  btn.addEventListener("pointerdown", e => e.stopPropagation());
  btn.onclick = () => { audio(); pop ? closePop() : openPop(); paint(); };
  document.addEventListener("pointerdown", closePop);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closePop(); });

  // ---- alarms from the server ----
  function flash(label) {
    document.body.classList.remove("alarmflash"); void document.body.offsetWidth; document.body.classList.add("alarmflash");
    if (document.hidden) { document.title = "🔔 " + label; clearTimeout(titleTimer); titleTimer = setTimeout(() => { document.title = baseTitle; }, 15000); }
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) document.title = baseTitle; });
  function onAlert(a) {
    if (!S.on) return;
    if (a.kind === "armed") { try { toast("🛡 " + at("Armed - alarms are active")); } catch (e) {} return; }
    const label = a.kind === "person" ? at("Person detected") + (a.count ? " (" + a.count + ")" : "")
      : (a.kind === "warm" ? at("Warm body (thermal camera)") : at("Pre-alarm: movement"));
    flash(label);
    try { toast("🔔 " + label + " · " + a.time); } catch (e) {}
    if (muted()) return;
    if (a.kind === "prealarm") { if (!S.pre || Date.now() - lastPre < 8000) return; lastPre = Date.now(); }
    if ((a.kind === "person" || a.kind === "warm") && !S.person) return;
    play(a.kind);
  }
  function connect() {
    if (!S.on) { if (es) { es.close(); es = null; } connOk = true; paint(); return; }
    if (es || !window.EventSource) return;
    es = new EventSource("/api/alerts");
    es.addEventListener("alert", e => { try { onAlert(JSON.parse(e.data)); } catch (x) {} });
    es.onopen = () => { clearTimeout(errTimer); connOk = true; paint(); };
    es.onerror = () => { clearTimeout(errTimer); errTimer = setTimeout(() => { connOk = false; paint(); }, 8000); };   // it reconnects by itself
  }
  window.mwPlayAlarm = play;               // for testing in the browser console
  paint(); connect();
  setInterval(paint, 30000);
})();
"""


COMMON_JS = r"""
const $ = s => document.querySelector(s);
const post = (u, b) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b || {})})
    .then(r => r.json()).catch(() => ({ok: false, error: "connection"}));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
let LANG = "", THEME = "";
try { LANG = localStorage.getItem("mw-lang") || ""; THEME = localStorage.getItem("mw-theme") || ""; } catch (e) {}
const I18N = {de: {"Live": "Live", "Cameras": "Kameras", "Recordings": "Aufzeichnungen", "Zones": "Zonen"}};
const t = s => (LANG === "de" && I18N.de[s]) || (I18N.en && I18N.en[s]) || s;
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(e => e.textContent = t(e.dataset.i18n));
  const b = $("#btn-lang"); if (b) b.textContent = LANG === "de" ? "EN" : "DE";
  document.documentElement.lang = LANG;
}
function applyTheme() { document.body.classList.toggle("light", THEME === "light"); const b = $("#btn-theme"); if (b) b.innerHTML = THEME === "light" ? "&#9790;" : "&#9728;"; }
function toggleTheme() { THEME = THEME === "light" ? "dark" : "light"; try { localStorage.setItem("mw-theme", THEME); } catch (e) {} applyTheme(); }
function toggleLang() { LANG = LANG === "de" ? "en" : "de"; try { localStorage.setItem("mw-lang", LANG); } catch (e) {} location.reload(); }
let toastTimer = null;
function toast(msg) { let e = $("#toast"); if (!e) { e = el("div"); e.id = "toast"; document.body.appendChild(e); } e.textContent = msg; e.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("on"), 2600); }
async function initAppearance() {
  if (!LANG || !THEME) {
    try { const a = await (await fetch("/api/appearance")).json(); LANG = LANG || a.lang; THEME = THEME || a.theme; }
    catch (e) { LANG = LANG || "en"; THEME = THEME || "dark"; }
  }
  applyTheme(); applyI18n();
}
"""


CAMS_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch - Cameras</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1700px;margin:0 auto}
.camgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}
@media(max-width:520px){.camgrid{grid-template-columns:1fr}}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);overflow:hidden;box-shadow:var(--shadow)}
.tile.big{grid-column:1/-1}
.tile .vw{position:relative;background:#000;aspect-ratio:16/9;cursor:zoom-in}
.tile.big .vw{cursor:zoom-out}
.tile img{width:100%;height:100%;object-fit:contain;display:block}
.tile .vw .ov{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9fb0c6;font-weight:600;text-align:center;padding:12px;pointer-events:none}
.th2{display:flex;align-items:center;gap:8px;padding:9px 12px}
.th2 b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dot{font-size:14px;color:var(--mut)}.dot.on{color:var(--grn)}.dot.bad{color:var(--red)}
.chip{font-size:11px;font-weight:700;border-radius:6px;padding:1px 7px;color:#fff}
.chip.mo{background:var(--org)}.chip.rc{background:var(--red)}
.add{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center}
.add select{width:100%}
h3{margin:0 0 8px;font-size:11px;letter-spacing:.09em;color:var(--mut);text-transform:uppercase}
.note{margin-top:8px}
</style></head><body>
<header>
  <h1>Motion Watch</h1>
  <!--NAV-->
  <span class="badge" id="b-n">–</span>
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div class="camgrid" id="grid"></div>
  <section class="card" style="margin-top:16px">
    <h3 data-i18n="Add camera">Add camera</h3>
    <div class="add">
      <select id="pick"></select>
      <button class="sec" id="btn-scan" onclick="scan()" data-i18n="Scan for cameras">Scan for cameras</button>
      <button onclick="add()" data-i18n="Add">Add</button>
    </div>
    <div class="err" id="err"></div>
    <details style="margin-top:6px"><summary class="mut" style="cursor:pointer" data-i18n="Add network camera">Add network camera</summary>
      <div class="add" style="grid-template-columns:1fr 2fr auto;margin-top:8px">
        <input type="text" id="ip-name" placeholder="Name" maxlength="40">
        <input type="text" id="ip-url" placeholder="rtsp://user:pass@192.168.1.50:554/stream1  |  http://192.168.1.50:8080/video" maxlength="500">
        <button class="sec" onclick="addIp()" data-i18n="Add">Add</button>
      </div></details>
    <div class="mut note" id="note"></div>
  </section>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Add camera": "Kamera hinzufügen", "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …", "Add": "Hinzufügen",
  "Add network camera": "Netzwerk-Kamera hinzufügen", "Main camera": "Hauptkamera", "Remove": "Entfernen", "motion": "Bewegung", "REC": "AUFN",
  "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "starting": "startet", "connection lost - reconnecting": "Verbindung verloren - verbinde neu",
  "cameras": "Kameras", "Choose a camera…": "Kamera wählen …", "no picture yet": "noch kein Bild",
  "The main camera does the full detection (AI, tracking, relays). Extra cameras watch for movement and record clips; they follow the same switches and schedules. Every extra camera needs CPU - on a Raspberry Pi 2-3 cameras are realistic.":
    "Die Hauptkamera macht die volle Erkennung (KI, Verfolgung, Relais). Zusatzkameras erkennen Bewegung und nehmen Clips auf; sie folgen denselben Schaltern und Zeitplänen. Jede Zusatzkamera braucht CPU - auf einem Raspberry Pi sind 2-3 Kameras realistisch.",
  "Remove this camera?": "Diese Kamera entfernen?", "Name": "Name"});
let SIG = "", SRC = null;
const tStatus = s => s && s.startsWith("failed:") ? t("failed") + s.slice(7) : t(s || "");
function tile(c) {
  const box = el("div", "tile"); box.dataset.id = c.id;
  const vw = el("div", "vw"), img = el("img"); img.alt = ""; img.dataset.src = c.n === 0 ? "/video_feed" : "/cam_feed/" + c.n; img.src = img.dataset.src;
  const ov = el("div", "ov", t("no picture yet")); img.onload = () => ov.hidden = true;
  vw.append(img, ov); vw.onclick = () => box.classList.toggle("big");
  const hd = el("div", "th2"), dot = el("span", "dot", "●"), name = el("b", "", c.n === 0 ? t("Main camera") + " · " + c.label : c.label);
  const mo = el("span", "chip mo", t("motion")), rc = el("span", "chip rc", "● " + t("REC")), st = el("span", "mut");
  mo.hidden = rc.hidden = true; hd.append(dot, name, mo, rc, st);
  if (c.n !== 0) { const x = el("button", "sec", "✕"); x.title = t("Remove"); x.style.padding = "3px 9px";
    x.onclick = async () => { if (confirm(t("Remove this camera?"))) { await post("/api/cams", {action: "remove", id: c.id}); SIG = ""; poll(); } }; hd.appendChild(x); }
  box.append(vw, hd); box._u = c2 => {
    dot.className = "dot " + (c2.status === "connected" ? "on" : (c2.status.startsWith("failed") ? "bad" : ""));
    mo.hidden = !c2.motion; rc.hidden = !c2.recording;
    st.textContent = tStatus(c2.status) === t("connected") ? (c2.res || "") + (c2.fps ? " · " + c2.fps + " fps" : "") : tStatus(c2.status);
    ov.hidden = c2.status === "connected" && img.naturalWidth > 0;
  };
  return box;
}
async function poll() {
  let j; try { j = await (await fetch("/api/cams")).json(); } catch (e) { return; }
  const sig = j.cams.map(c => c.id + ":" + c.n).join("|") + LANG;
  const g = $("#grid");
  if (sig !== SIG) { SIG = sig; g.textContent = ""; j.cams.forEach(c => g.appendChild(tile(c))); }
  [...g.children].forEach((b, i) => j.cams[i] && b._u(j.cams[i]));
  $("#b-n").textContent = j.cams.length + " " + t("cameras");
  SRC = j.sources; fillPick(j);
}
function fillPick(j) {
  const sel = $("#pick"), cur = sel.value; if (sel.matches(":focus")) return;
  const used = new Set(j.cams.map(c => c.id)); sel.textContent = "";
  const o0 = el("option", "", t("Choose a camera…")); o0.value = ""; sel.appendChild(o0);
  (j.sources.items || []).filter(i => i.id !== "auto" && !used.has(i.id)).forEach(i => {
    const o = el("option", "", i.name + (i.detail ? " [" + i.detail.replace("in use", "") + "]" : "")); o.value = i.id; sel.appendChild(o); });
  sel.value = cur;
  $("#note").textContent = t("The main camera does the full detection (AI, tracking, relays). Extra cameras watch for movement and record clips; they follow the same switches and schedules. Every extra camera needs CPU - on a Raspberry Pi 2-3 cameras are realistic.");
}
function showErr(m) { $("#err").textContent = m ? "⚠ " + m : ""; if (m) setTimeout(() => $("#err").textContent = "", 6000); }
async function add() { const id = $("#pick").value; if (!id) return; const r = await post("/api/cams", {action: "add", id: id, lang: LANG}); showErr(r.ok ? "" : r.error); SIG = ""; poll(); }
async function scan() {
  const b = $("#btn-scan"); b.disabled = true; b.textContent = t("Scanning…");
  await post("/api/sources/scan", {}); b.disabled = false; b.textContent = t("Scan for cameras"); poll();
}
async function addIp() {
  const r = await post("/api/source", {action: "add", name: $("#ip-name").value, url: $("#ip-url").value, select: false, lang: LANG});
  if (!r.ok) { showErr(r.error); return; }
  $("#ip-name").value = $("#ip-url").value = "";
  const r2 = await post("/api/cams", {action: "add", id: r.id, lang: LANG}); showErr(r2.ok ? "" : r2.error); SIG = ""; poll();
}
document.addEventListener("visibilitychange", () => {      // no stream while the tab is hidden = no CPU
  document.querySelectorAll(".tile img").forEach(i => { i.src = document.hidden ? "" : i.dataset.src; });
});
(async () => { await initAppearance(); poll(); setInterval(poll, 2500); })();
/*ALERTS*/
</script></body></html>
"""

ZONES_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch - Zones</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1500px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}
@media(max-width:980px){main{grid-template-columns:1fr}}
#cv{width:100%;display:block;background:#000;border-radius:12px;touch-action:none;cursor:crosshair;box-shadow:0 0 0 1px var(--line)}
.zrow{border:1px solid var(--line);border-radius:10px;padding:8px;margin-top:8px;display:grid;grid-template-columns:1fr auto;gap:6px 8px;align-items:center;background:var(--field)}
.zrow.sel{border-color:var(--acc);box-shadow:0 0 0 3px var(--glow)}
.zrow input[type=text]{width:100%}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
ol{padding-left:18px;margin:6px 0}
</style></head><body>
<header>
  <h1>Motion Watch</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <section class="card" style="margin:0">
    <canvas id="cv" width="1280" height="720"></canvas>
    <div class="mut" id="hint" style="margin-top:8px"></div>
  </section>
  <aside>
    <div class="card" style="margin:0 0 14px">
      <div class="btns" style="margin-top:0">
        <button onclick="startZone('ignore')" data-i18n="+ Ignore zone">+ Ignore zone</button>
        <button onclick="startZone('only')" data-i18n="+ Only-here zone">+ Only-here zone</button>
      </div>
      <div class="btns"><button class="sec" id="b-fin" onclick="finish()" data-i18n="Finish shape" hidden>Finish shape</button>
        <button class="sec" onclick="loadFrame()" data-i18n="New picture">New picture</button></div>
      <div id="list"></div>
      <div class="btns"><button id="b-save" onclick="save()" data-i18n="Save zones">Save zones</button></div>
      <div class="err" id="err"></div>
    </div>
    <div class="card" style="margin:0">
      <div class="legend mut"><div><i style="background:#f59a4a"></i><span data-i18n="Ignore zone">Ignore zone</span>: <span data-i18n="z-ign">z-ign</span></div>
      <div style="margin-top:4px"><i style="background:#3fcf6b"></i><span data-i18n="Only-here zone">Only-here zone</span>: <span data-i18n="z-only">z-only</span></div></div>
      <div class="mut" style="margin-top:8px" data-i18n="z-how">z-how</div>
    </div>
  </aside>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"+ Ignore zone": "+ Ignorier-Zone", "+ Only-here zone": "+ Nur-hier-Zone", "Finish shape": "Form abschliessen", "New picture": "Neues Bild",
  "Save zones": "Zonen speichern", "Ignore zone": "Ignorier-Zone", "Only-here zone": "Nur-hier-Zone", "Delete": "Löschen", "Saved": "Gespeichert",
  "Click the corners of the area in the picture. Click the first point or press 'Finish shape' to close it.": "Klicke die Ecken des Bereichs im Bild an. Klicke den ersten Punkt oder 'Form abschliessen', um die Form zu schliessen.",
  "Drag a corner to move it. Select a zone in the list to edit it.": "Eine Ecke lässt sich verschieben. Wähle eine Zone in der Liste zum Bearbeiten.",
  "no zones": "keine Zonen", "no picture - is the camera running?": "kein Bild - läuft die Kamera?", "Name": "Name",
  "z-ign": "Personen und Objekte, deren Füsse darin stehen, werden ignoriert (Strasse, Baum, Nachbars Garten).",
  "z-only": "Wenn mindestens eine solche Zone existiert, zählt nur, was darin passiert (Eingang, Einfahrt).",
  "z-how": "Eine Zone wirkt auf die Erkennung, die Aufnahme, die Alarme und die Relais. Gezählt wird der Punkt unten in der Mitte des erkannten Objekts (die Füsse)."});
Object.assign(I18N, {en: {"z-ign": "Persons and objects whose feet are inside are ignored (street, tree, neighbour's garden).",
  "z-only": "If at least one such zone exists, only what happens inside it counts (entrance, driveway).",
  "z-how": "A zone affects detection, recording, alarms and relays. The point that counts is the bottom middle of the detected object (the feet)."}});
const tt = s => (LANG === "de" && I18N.de[s]) || (I18N.en && I18N.en[s]) || s;
const cv = $("#cv"), g = cv.getContext("2d"), img = new Image();
let zones = [], sel = -1, drawing = null, drawMode = "ignore", drag = null;
const COL = {ignore: "245,154,74", only: "63,207,107"};
function norm(e) { const r = cv.getBoundingClientRect(); return [Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), Math.min(1, Math.max(0, (e.clientY - r.top) / r.height))]; }
function px(p) { return [p[0] * cv.width, p[1] * cv.height]; }
function draw() {
  g.clearRect(0, 0, cv.width, cv.height);
  if (img.complete && img.naturalWidth) g.drawImage(img, 0, 0, cv.width, cv.height);
  else { g.fillStyle = "#0b0f14"; g.fillRect(0, 0, cv.width, cv.height); g.fillStyle = "#8a9bb0"; g.font = "28px sans-serif"; g.textAlign = "center"; g.fillText(t("no picture - is the camera running?"), cv.width / 2, cv.height / 2); g.textAlign = "left"; }
  const poly = (pts, mode, on, close) => {
    g.beginPath(); pts.forEach((p, i) => { const [x, y] = px(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); if (close) g.closePath();
    if (close) { g.fillStyle = "rgba(" + COL[mode] + "," + (on ? .34 : .22) + ")"; g.fill(); }
    g.strokeStyle = "rgb(" + COL[mode] + ")"; g.lineWidth = on ? 4 : 2.5; g.stroke();
    pts.forEach(p => { const [x, y] = px(p); g.beginPath(); g.arc(x, y, on || !close ? 8 : 5, 0, 7); g.fillStyle = "#fff"; g.fill(); g.strokeStyle = "rgb(" + COL[mode] + ")"; g.lineWidth = 2; g.stroke(); });
  };
  zones.forEach((z, i) => { poly(z.points, z.mode, i === sel, true); const [x, y] = px(z.points[0]); g.fillStyle = "#fff"; g.font = "bold 24px sans-serif"; g.fillText(z.name, x + 12, y - 10); });
  if (drawing) poly(drawing, drawMode, true, false);
}
function hit(n) {
  const r = cv.getBoundingClientRect(), tol = 14 / r.width;
  for (let zi = zones.length - 1; zi >= 0; zi--) for (let pi = 0; pi < zones[zi].points.length; pi++) {
    const p = zones[zi].points[pi]; if (Math.hypot((p[0] - n[0]), (p[1] - n[1]) * r.height / r.width) < tol) return [zi, pi]; }
  return null;
}
function inside(n, pts) { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
  if ((pts[i][1] > n[1]) !== (pts[j][1] > n[1]) && n[0] < (pts[j][0] - pts[i][0]) * (n[1] - pts[i][1]) / (pts[j][1] - pts[i][1]) + pts[i][0]) c = !c; } return c; }
cv.addEventListener("pointerdown", e => {
  const n = norm(e);
  if (drawing) {
    const r = cv.getBoundingClientRect();
    if (drawing.length >= 3 && Math.hypot(n[0] - drawing[0][0], (n[1] - drawing[0][1]) * r.height / r.width) < 14 / r.width) { finish(); return; }
    drawing.push(n); draw(); return;
  }
  const h = hit(n);
  if (h) { sel = h[0]; drag = h; cv.setPointerCapture(e.pointerId); renderList(); draw(); return; }
  const idx = zones.findIndex(z => inside(n, z.points)); sel = idx; renderList(); draw();
});
cv.addEventListener("pointermove", e => { if (drag) { zones[drag[0]].points[drag[1]] = norm(e); draw(); } });
cv.addEventListener("pointerup", () => { drag = null; });
cv.addEventListener("dblclick", () => { if (drawing && drawing.length >= 3) finish(); });
function startZone(mode) { drawMode = mode; drawing = []; sel = -1; $("#b-fin").hidden = false; setHint(); draw(); }
function finish() {
  if (drawing && drawing.length >= 3) { zones.push({name: (drawMode === "only" ? "Only " : "Ignore ") + (zones.length + 1), mode: drawMode, points: drawing}); sel = zones.length - 1; }
  drawing = null; $("#b-fin").hidden = true; setHint(); renderList(); draw();
}
function setHint() { $("#hint").textContent = drawing ? tt("Click the corners of the area in the picture. Click the first point or press 'Finish shape' to close it.") : tt("Drag a corner to move it. Select a zone in the list to edit it."); }
function renderList() {
  const L = $("#list"); L.textContent = "";
  if (!zones.length) L.appendChild(el("div", "mut", t("no zones"))).style.marginTop = "8px";
  zones.forEach((z, i) => {
    const r = el("div", "zrow" + (i === sel ? " sel" : "")); r.onclick = () => { sel = i; renderList(); draw(); };
    const nm = el("input"); nm.type = "text"; nm.value = z.name; nm.maxLength = 40; nm.oninput = () => { z.name = nm.value; draw(); }; nm.onclick = e => e.stopPropagation();
    const del = el("button", "sec", "✕"); del.title = t("Delete"); del.onclick = e => { e.stopPropagation(); zones.splice(i, 1); sel = -1; renderList(); draw(); };
    const md = el("select"); [["ignore", t("Ignore zone")], ["only", t("Only-here zone")]].forEach(([v, l]) => { const o = el("option", "", l); o.value = v; md.appendChild(o); });
    md.value = z.mode; md.onchange = () => { z.mode = md.value; draw(); }; md.onclick = e => e.stopPropagation();
    r.append(nm, del, md); L.appendChild(r);
  });
}
async function save() {
  const r = await post("/api/zones", {zones: zones, lang: LANG});
  $("#err").textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) toast(t("Saved"));
}
function loadFrame() { img.onload = draw; img.onerror = draw; img.src = "/api/frame.jpg?" + Date.now(); }
(async () => {
  await initAppearance(); setHint();
  try { zones = (await (await fetch("/api/zones")).json()).zones || []; } catch (e) { zones = []; }
  renderList(); loadFrame(); setTimeout(loadFrame, 1500); draw();
})();
/*ALERTS*/
</script></body></html>
"""


WEB_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch</title>
<style>
/*BASECSS*/
main{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:16px;padding:16px;align-items:start;max-width:1800px;margin:0 auto}
body.noside main{grid-template-columns:minmax(0,1fr)}
@media(max-width:960px){main{grid-template-columns:1fr;row-gap:0}}
.vwrap{position:relative;border-radius:12px;overflow:hidden;background:#000;box-shadow:0 0 0 1px var(--line)}
#video{width:100%;display:block;background:#000;min-height:160px}
.vtag{position:absolute;bottom:10px;left:10px;display:flex;gap:6px;flex-wrap:wrap;pointer-events:none}
.vtag span{background:rgba(0,0,0,.62);color:#fff;border-radius:7px;padding:2px 9px;font-size:11px;font-weight:700;letter-spacing:.05em;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.vtag .live::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#3fcf6b;margin-right:6px;animation:pulse 1.6s infinite}
.vtag .rec{background:var(--red)}
@keyframes pulse{50%{opacity:.3}}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:9px;margin-top:12px}
.stat{background:var(--field);border:1px solid var(--line);border-radius:11px;padding:9px 12px}
.stat small{display:block;color:var(--mut);font-size:10px;font-weight:700;letter-spacing:.07em}
.stat b{font-size:22px;font-variant-numeric:tabular-nums}
.tg{padding:7px 0;cursor:pointer}
.sl{margin-top:9px}
.val{color:var(--mut);font-size:12px}
.pad{display:grid;grid-template-columns:repeat(3,58px);grid-template-rows:repeat(3,58px);gap:6px;touch-action:none;user-select:none}
details.grp>summary{font-size:12px;letter-spacing:.07em}
details.grp>summary .gi{font-size:16px;margin-right:9px;letter-spacing:0;filter:saturate(.9)}
details.grp>summary .gn{flex:1}
details.sub{border-top:1px solid var(--line);margin-top:12px;padding-top:9px}
details.sub>summary{font-size:10.5px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;cursor:pointer;list-style:none;
  display:flex;justify-content:space-between;align-items:center;user-select:none}
details.sub>summary::-webkit-details-marker,details.adv>summary::-webkit-details-marker{display:none}
details.sub>summary::after{content:"▾";font-size:12px;transition:transform .15s}details.sub:not([open])>summary::after{transform:rotate(-90deg)}
details.sub[open]>summary{margin-bottom:7px}
details.sub.inline{border-top:0;margin-top:0;padding-top:0}details.sub.inline>summary{display:none}
details.grp>summary+details.sub,details.grp>summary+.blk{border-top:0;margin-top:0;padding-top:0}
.blk{border-top:1px solid var(--line);margin-top:12px;padding-top:7px}
.blk>h4{margin:0 0 2px;font-size:10.5px;letter-spacing:.09em;color:var(--mut);text-transform:uppercase;font-weight:700}
details.adv{margin-top:12px;border-top:1px dashed var(--line);padding-top:8px}
details.adv>summary{cursor:pointer;color:var(--acc2);font-size:12.5px;font-weight:600;list-style:none;user-select:none}
details.adv>summary::before{content:"▸";display:inline-block;width:1.1em}details.adv[open]>summary::before{content:"▾"}
details.adv>.blk:first-of-type{border-top:0}
#settings .tg{padding:4px 0}#settings .sl{margin-top:7px}
@media(max-width:760px){.card{padding:12px}details.card>summary{font-size:11.5px}}
.pr-sw{margin-top:12px;padding-top:10px;border-top:1px solid var(--line);align-items:flex-start;cursor:pointer}
.pr-sw input.sw{margin-top:2px}#b-arm{user-select:none}
.wf-item{border:1px solid var(--line);border-radius:10px;margin-top:6px;background:var(--field);overflow:hidden}
.wf-item.on{border-color:var(--grn)}
.wf-head{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:pointer}
.wf-head b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wf-tags{display:flex;gap:6px;align-items:center}
.wf-form,.wf-item>.mut{padding:0 10px 10px}.wf-item>input{margin:10px 10px 6px;width:calc(100% - 20px)!important}
.wf-saved{padding:6px 0;border-bottom:1px solid var(--line)}.wf-saved:last-child{border-bottom:0}
.wbars{display:inline-flex;align-items:flex-end;gap:1.5px;height:11px;margin-right:3px}
.wbars i{display:block;width:3px;background:currentColor;opacity:.25;border-radius:1px}
.wbars i:nth-child(1){height:3px}.wbars i:nth-child(2){height:5px}.wbars i:nth-child(3){height:8px}.wbars i:nth-child(4){height:11px}
.wbars i.on{opacity:1}
.stickbox{display:flex;flex-direction:column;align-items:center;gap:10px}
.stick{position:relative;width:184px;height:184px;border-radius:50%;touch-action:none;user-select:none;-webkit-user-select:none;cursor:grab;
  background:radial-gradient(circle at 50% 50%,var(--field) 0,var(--field) 38%,var(--panel2) 100%);border:1px solid var(--line);
  box-shadow:inset 0 2px 14px rgba(0,0,0,.35),0 0 0 5px var(--glow)}
.stick::before,.stick::after{content:"";position:absolute;background:var(--line);left:50%;top:50%;transform:translate(-50%,-50%);pointer-events:none}
.stick::before{width:1px;height:78%}.stick::after{height:1px;width:78%}
.stick .ar{position:absolute;color:var(--mut);font-size:11px;pointer-events:none;opacity:.8}
.stick .ar.u{top:7px;left:50%;transform:translateX(-50%)}.stick .ar.d{bottom:7px;left:50%;transform:translateX(-50%)}
.stick .ar.l{left:9px;top:50%;transform:translateY(-50%)}.stick .ar.r{right:9px;top:50%;transform:translateY(-50%)}
/* servo position shown on the stick: dashed frame = travel range, orange ring = where the camera points now */
.srange{position:absolute;left:14.65%;top:14.65%;width:70.7%;height:70.7%;border:1px dashed rgba(245,154,74,.45);
  border-radius:6px;pointer-events:none}
.sline{z-index:1;position:absolute;display:block;background:rgba(245,154,74,.38);pointer-events:none;transition:top .25s ease-out,left .25s ease-out}
.sline.h{left:0;right:0;height:1px;top:50%}.sline.v{top:0;bottom:0;width:1px;left:50%}
.spos{position:absolute;display:block;left:50%;top:50%;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;border:2.5px solid #f59a4a;
  box-shadow:0 0 0 3px rgba(245,154,74,.22),0 0 12px rgba(245,154,74,.65);z-index:3;pointer-events:none;transition:top .25s ease-out,left .25s ease-out}
.stick.on .spos,.stick.on .sline{transition:none}
#spos-txt{font-size:11px;letter-spacing:.02em;text-align:center;margin-top:-4px}
#spos-txt b{color:#f59a4a;font-weight:700}
.knob{position:absolute;z-index:2;left:50%;top:50%;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;pointer-events:none;will-change:transform;
  background:radial-gradient(circle at 36% 30%,var(--acc2),var(--acc) 62%);box-shadow:0 6px 16px rgba(0,0,0,.45),inset 0 1px 2px rgba(255,255,255,.35);transition:transform .16s ease-out}
.stick.on{cursor:grabbing}.stick.on .knob{transition:none;filter:brightness(1.12)}
.stickrow{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap}
.stickrow select{padding:4px 8px}
#mctl{display:none}
#mbtns{display:none}body.mobctl #mbtns{display:block;width:100%}
body.mobctl #mbtns #allbtns{margin:10px 0 0!important}
#mbtns2{display:none}body.mobctl:not(.mobland) #mbtns2{display:block;margin:0 0 14px}body.mobctl #mbtns2 #allbtns{margin:0!important}
body.mobland #mbtns .btns>*{padding:5px 8px;font-size:12px}
body.mobland .stickbox{gap:6px}body.mobland .stickrow select,body.mobland .stickrow button{padding:3px 7px!important;font-size:12px}
body.mobctl #mctl{display:block;margin-top:12px}
body.mobctl #mctl .pad{margin:0 auto}
body.mobctl #mctl>#ctl-left>.row{justify-content:center;gap:10px}
body.mobland main{padding:8px;row-gap:0}
body.mobland header{position:static}
body.mobland #vcard{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px 12px;align-items:center;padding:8px}
body.mobland #vcard>.vwrap{grid-column:1;grid-row:1}
body.mobland #mctl{grid-column:2;grid-row:1;margin:0;max-width:200px}
body.mobland #vcard>.stats,body.mobland #vcard>#obj-list{grid-column:1/-1}
body.mobland #video{max-height:calc(100vh - 20px);max-height:calc(100svh - 20px);object-fit:contain;min-height:0}
body.mobland .stick{width:136px;height:136px}
body.mobland .knob{width:54px;height:54px;margin:-27px 0 0 -27px}
body.mobland .pad{grid-template-columns:repeat(3,50px);grid-template-rows:repeat(3,50px)}
body.mobland #mctl .stickrow{gap:4px}body.mobland #mctl>#ctl-left>.row{flex-wrap:wrap;gap:4px 8px;margin-top:6px!important}
body.padmode .stickbox{display:none}body:not(.padmode) .padbox{display:none}
button.dp{font-size:22px;padding:0;background:var(--btn2);color:var(--txt);border:1px solid var(--line);border-radius:12px}
button.dp.mid{background:var(--acc);color:#fff;border-color:transparent}
canvas{width:100%;height:56px;display:block;background:var(--field);border-radius:8px}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden;margin:6px 0}
.bar>i{display:block;height:100%;width:0;background:var(--grn);transition:width .4s,background .4s}
#log{font:12px/1.55 ui-monospace,Menlo,Consolas,monospace;max-height:200px;overflow:auto;white-space:pre-wrap}
#log .t{color:var(--mut)}
body.videoonly header,body.videoonly aside,body.videoonly .stats,body.videoonly #obj-list,body.videoonly details.card,body.videoonly .vtag{display:none}
body.videoonly main{display:block;padding:0;max-width:none}body.videoonly .card{margin:0;padding:0;border:0;border-radius:0;box-shadow:none;background:none}
body.videoonly .vwrap{border-radius:0;box-shadow:none}
body.videoonly #video{border-radius:0;height:100vh;object-fit:contain}
.pop{position:fixed;top:58px;right:12px;z-index:40;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 14px 12px;box-shadow:var(--shadow);max-height:80vh;overflow:auto;min-width:250px}
.pop h3{margin:10px 0 4px;font-size:11px;color:var(--mut);letter-spacing:.08em;text-transform:uppercase}
.pop label{display:flex;gap:8px;align-items:center;padding:3px 0;cursor:pointer}
.ctl-grid{display:grid;grid-template-columns:auto minmax(0,1fr);gap:18px;align-items:start}
@media(max-width:640px){.ctl-grid{grid-template-columns:1fr}}
h4.sub{margin:14px 0 4px;font-size:11px;letter-spacing:.08em;color:var(--mut);text-transform:uppercase}
.rq{display:grid;grid-template-columns:auto auto auto minmax(0,1fr);gap:6px 10px;align-items:center}
.dot{font-size:15px;color:var(--mut)}.dot.on{color:var(--grn)}
.rel-ed{border:1px solid var(--line);border-radius:10px;padding:9px;margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;align-items:end;background:var(--field)}
.rel-ed input[type=text],.rel-ed input[type=number]{width:100%}
.warn{color:var(--yel);font-size:13px;cursor:help}
.srcrow{display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;border-radius:8px}
.srcrow:hover{background:var(--field)}
.srcrow input{margin:0}
.days{display:flex;gap:4px;flex-wrap:wrap}
.days button{padding:4px 9px;font-size:12px;background:var(--btn2);color:var(--mut);border:1px solid var(--line)}
.days button.on{background:var(--acc);color:#fff;border-color:transparent}
</style></head><body>
<header>
  <h1 data-view="title" data-vgroup="Header" data-vlabel="Title">Motion Watch</h1>
  <!--NAV-->
  <span class="badge" id="b-person" data-view="b-person" data-vgroup="Header" data-vlabel="Persons">No person</span>
  <span class="badge" id="b-obj" data-view="b-obj" data-vgroup="Header" data-vlabel="Objects">0 objects</span>
  <span class="badge" id="b-rain" data-view="b-rain" data-vgroup="Header" data-vlabel="Rain">No rain</span>
  <span class="badge" id="b-wind" data-view="b-wind" data-vgroup="Header" data-vlabel="Wind">Wind: calm</span>
  <span class="badge" id="b-rec" data-view="b-rec" data-vgroup="Header" data-vlabel="Recording">Idle</span>
  <span class="badge" id="b-src" data-view="b-src" data-vgroup="Header" data-vlabel="Video source">Source –</span>
  <span class="badge" id="b-sched" data-view="b-sched" data-vgroup="Header" data-vlabel="Schedule">Schedule –</span>
  <span class="badge" id="b-pres" data-view="b-pres" data-vgroup="Header" data-vlabel="Presence" hidden>Presence</span>
  <span class="badge yel" id="b-sec" data-view="b-sec" data-vgroup="Header" data-vlabel="Security warning" hidden title="Set a password: --web-password SECRET" data-i18n="⚠ no password">⚠ no password</span>
  <span class="badge" id="b-relay" data-view="b-relay" data-vgroup="Header" data-vlabel="Relays">Relays</span>
  <span class="badge" id="b-light" data-view="b-light" data-vgroup="Header" data-vlabel="Light level">Light –</span>
  <span class="badge" id="b-arm" data-view="b-arm" data-vgroup="Header" data-vlabel="Armed / disarmed" style="cursor:pointer">🛡</span>
  <span class="badge" id="b-fps" data-view="b-fps" data-vgroup="Header" data-vlabel="FPS">FPS –</span>
  <span class="badge" id="b-wifi" data-view="b-wifi" data-vgroup="Header" data-vlabel="Wi-Fi" hidden>Wi-Fi</span>
  <span class="badge" id="b-cpu" data-view="b-cpu" data-vgroup="Header" data-vlabel="CPU">CPU –</span>
  <span class="badge" id="b-conn" data-view="b-conn" data-vgroup="Header" data-vlabel="Connection">connecting…</span>
  <span class="hdr-ctl">
    <button class="sec" id="btn-view" onclick="toggleViewMenu(event)" title="View">&#9776;</button>
    <button class="sec" id="btn-side" onclick="toggleHidden('sidebar')" title="Settings panel">&#9654;</button>
    <button class="sec" id="btn-fs" onclick="toggleFullscreen()" title="F11">&#x26F6;</button>
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<div id="viewmenu" class="pop" hidden></div>
<main>
  <section>
    <div class="card" id="vcard">
      <div class="vwrap"><img id="video" src="/video_feed" alt="live stream">
        <div class="vtag"><span class="live">LIVE</span><span class="rec" id="v-rec" hidden>● REC</span><span id="v-src" hidden></span></div></div>
      <div id="mctl"></div>
      <div class="stats">
        <div class="stat" data-view="s-fps" data-vgroup="Statistics" data-vlabel="FPS"><small>FPS</small><b id="s-fps">–</b></div>
        <div class="stat" data-view="s-persons" data-vgroup="Statistics" data-vlabel="Persons now"><small>PERSONS NOW</small><b id="s-persons">–</b></div>
        <div class="stat" data-view="s-objects" data-vgroup="Statistics" data-vlabel="Objects"><small>OBJECTS</small><b id="s-objects">–</b></div>
        <div class="stat" data-view="s-det" data-vgroup="Statistics" data-vlabel="Detections"><small>DETECTIONS</small><b id="s-det">–</b></div>
      </div>
      <div class="mut" id="obj-list" data-view="obj-list" data-vgroup="Statistics" data-vlabel="Object list" style="margin-top:8px"></div>
    </div>
    <div id="mbtns2"></div>
    <details class="card" open data-view="controls" data-vgroup="Panels" data-vlabel="Controls">
      <summary data-i18n="Controls">Controls</summary>
      <div class="ctl-grid">
        <div id="ctl-left">
          <div class="stickbox">
            <div class="stick" id="stick" role="application" aria-label="camera joystick"><span class="ar u">&#9650;</span><span class="ar d">&#9660;</span><span class="ar l">&#9664;</span><span class="ar r">&#9654;</span><div class="srange" aria-hidden="true"><i class="sline h" id="sline-h"></i><i class="sline v" id="sline-v"></i><i class="spos" id="spos"></i></div><div class="knob" id="knob"></div></div>
            <div class="mut" id="spos-txt" aria-live="off"></div>
            <div class="stickrow"><span class="mut" data-i18n="Speed">Speed</span>
              <select id="stick-speed"><option value="12" data-i18n="slow">slow</option><option value="30" selected data-i18n="medium">medium</option><option value="60" data-i18n="fast">fast</option></select>
              <button class="sec" type="button" data-dir="center" id="stick-center" style="padding:4px 11px" data-i18n="Centre">Centre</button></div>
          </div>
          <div class="pad padbox">
            <span></span><button class="dp" data-dir="up" aria-label="tilt up">&#9650;</button><span></span>
            <button class="dp" data-dir="left" aria-label="pan left">&#9664;</button>
            <button class="dp mid" data-dir="center" aria-label="centre">&#9679;</button>
            <button class="dp" data-dir="right" aria-label="pan right">&#9654;</button>
            <span></span><button class="dp" data-dir="down" aria-label="tilt down">&#9660;</button><span></span>
          </div>
          <div class="row padbox" style="margin-top:8px"><span class="mut" data-i18n="Step per click">Step per click</span>
            <select id="step"><option>1</option><option selected>3</option><option>5</option><option>10</option><option>20</option></select></div>
          <div class="row" style="margin-top:10px"><span class="mut" data-i18n="Control">Control</span>
            <span class="seg"><button class="sel-auto" type="button" id="m-stick" data-i18n="Stick">Stick</button><button type="button" id="m-pad" data-i18n="Buttons">Buttons</button></span></div>
          <div id="mbtns"></div>
        </div>
        <div>
          <div style="font-weight:700">Pan <span id="v-pan">–</span>% · Tilt <span id="v-tilt">–</span>%</div>
          <div class="mut"><span data-i18n="arrow keys work too">arrow keys work too</span></div>
          <div class="mut" id="patrol-st"></div>
          <div class="btns">
            <button class="sec" onclick="act('wp_add')" data-i18n="+ Waypoint">+ Waypoint</button>
            <button class="sec" onclick="act('wp_clear')" data-i18n="Clear waypoints">Clear waypoints</button>
            <a class="btn sec" href="/snapshot.jpg" data-i18n="Snapshot">Snapshot</a>
          </div>
          <h4 class="sub" data-i18n="Relays">Relays</h4>
          <div class="rq" id="relay-quick"></div>
          <div class="err" id="relay-err"></div>
        </div>
      </div>
      <div class="btns">
        <button class="sec" onclick="act('recalibrate')" data-i18n="Recalibrate">Recalibrate</button>
        <button class="sec" onclick="act('reset_counter')" data-i18n="Reset counter">Reset counter</button>
        <button class="sec" onclick="if(confirm(t('Reset all settings to defaults?')))act('reset_settings')" data-i18n="Reset settings">Reset settings</button>
      </div>
      <div class="mut" id="sys-info" style="margin-top:6px"></div>
    </details>
  </section>
  <aside data-view="sidebar" data-vgroup="Panels" data-vlabel="Settings panel">
    <div class="btns" id="allbtns" style="margin:0 0 12px">
      <button class="sec" onclick="allSections(true)" data-i18n="Expand all">Expand all</button>
      <button class="sec" onclick="allSections(false)" data-i18n="Collapse all">Collapse all</button>
    </div>
    <details class="card" open data-view="protect" data-vgroup="Panels" data-vlabel="Camping / protection" id="pr-card">
      <summary data-i18n="Camping / protection">Camping / protection</summary>
      <div class="row"><b id="pr-state" style="font-size:18px">–</b><span class="mut" id="pr-left"></span></div>
      <div class="btns">
        <button type="button" id="pr-arm" data-i18n="🛡 Arm (countdown)">🛡 Arm (countdown)</button>
        <button type="button" class="sec" id="pr-armnow" data-i18n="Arm now">Arm now</button>
        <button type="button" class="sec" id="pr-disarm" data-i18n="Disarm">Disarm</button>
      </div>
      <label class="row pr-sw"><span><b>⛺ <span data-i18n="Camping profile">Camping profile</span></b><br>
        <span class="mut" data-i18n="cp-desc">Own Wi-Fi on, the camera stays where it is (no patrol / tracking / timelapse), alarms and recordings on, armed after the countdown. Switching it off restores your settings.</span></span>
        <input type="checkbox" class="sw" id="pr-camp"></label>
      <label class="row pr-sw"><span><b>📡 <span data-i18n="Own Wi-Fi (hotspot)">Own Wi-Fi (hotspot)</span></b><br><span class="mut" id="pr-hs-info"></span></span>
        <input type="checkbox" class="sw" id="pr-hs"></label>
      <div class="pr-sw" style="cursor:default"><b>🌐 <span data-i18n="Network">Network</span></b>
        <select id="pr-net" style="width:100%;margin-top:6px">
          <option value="auto" data-i18n="Automatic: phone hotspot / known networks, otherwise own Wi-Fi">Automatic: phone hotspot / known networks, otherwise own Wi-Fi</option>
          <option value="hotspot" data-i18n="Own Wi-Fi at boot">Own Wi-Fi at boot</option>
          <option value="client" data-i18n="Only known networks">Only known networks</option>
        </select>
        <div class="mut" id="pr-net-info" style="margin-top:4px"></div></div>
      <label class="row pr-sw"><span><b>🔁 <span data-i18n="Autostart at boot">Autostart at boot</span></b><br><span class="mut" id="pr-as-info"></span></span>
        <input type="checkbox" class="sw" id="pr-as"></label>
      <div class="mut" id="pr-time" style="margin-top:6px"></div>
      <div class="err" id="pr-err"></div>
    </details>
    <details class="card" open data-view="system" data-vgroup="Panels" data-vlabel="System">
      <summary data-i18n="System">System</summary>
      <div class="row"><b id="cpu-big" style="font-size:22px">–</b><span class="mut" id="cpu-info"></span></div>
      <div class="bar"><i id="cpu-bar"></i></div>
      <canvas id="cpu-spark" width="360" height="56"></canvas>
      <div class="mut" style="margin-top:4px" data-i18n="CPU load, last 60 seconds">CPU load, last 60 seconds</div>
      <div id="wifi-box" hidden style="margin-top:12px">
        <div class="row"><b id="wifi-big" style="font-size:18px">–</b><span class="mut" id="wifi-name"></span></div>
        <div class="bar"><i id="wifi-bar"></i></div>
        <canvas id="wifi-spark" width="360" height="64"></canvas>
        <div class="mut" id="wifi-stat" style="margin-top:4px"></div>
        <div class="mut" id="wifi-info"></div>
      </div>
    </details>
    <details class="card" open data-view="log" data-vgroup="Panels" data-vlabel="Event log"><summary data-i18n="Event log">Event log</summary><div id="log"></div></details>
    <details class="card" data-view="wifi" data-vgroup="Panels" data-vlabel="Wi-Fi / hotspot" id="wf-card">
      <summary data-i18n="Wi-Fi / hotspot">Wi-Fi / hotspot</summary>
      <div class="mut" id="wf-status">…</div>
      <div class="btns"><button type="button" id="wf-scan" data-i18n="Search networks">Search networks</button></div>
      <div class="err" id="wf-err"></div>
      <div id="wf-list"></div>
      <div class="mut" style="margin-top:12px;font-weight:700;letter-spacing:.06em;font-size:11px;text-transform:uppercase" data-i18n="Saved networks">Saved networks</div>
      <div id="wf-saved"></div>
    </details>
    <details class="card" open data-view="source" data-vgroup="Panels" data-vlabel="Video source">
      <summary data-i18n="Video source">Video source</summary>
      <div class="mut" id="src-status"></div>
      <div id="src-list"></div>
      <div class="err" id="src-err"></div>
      <div class="btns"><button class="sec" id="btn-scan" onclick="scanSources()" data-i18n="Scan for cameras">Scan for cameras</button></div>
      <div class="mut" id="src-hints"></div>
      <h4 class="sub" data-i18n="Add network camera">Add network camera</h4>
      <div class="rel-ed" style="grid-template-columns:1fr">
        <input type="text" id="ip-name" placeholder="Name" maxlength="40">
        <input type="text" id="ip-url" placeholder="rtsp://user:pass@192.168.1.50:554/stream1  |  http://192.168.1.50:8080/video" maxlength="500">
        <button class="sec" onclick="addIpSource()" data-i18n="Add">Add</button>
      </div>
    </details>
    <details class="card" open data-view="schedule" data-vgroup="Panels" data-vlabel="Schedule">
      <summary data-i18n="Schedule">Schedule</summary>
      <div class="mut" id="sched-note"></div>
      <div id="sched-list"></div>
      <div class="err" id="sched-err"></div>
      <div class="btns"><button class="sec" onclick="schedPost({action:'add'})" data-i18n="+ Add schedule">+ Add schedule</button></div>
    </details>
    <details class="card" data-view="relayset" data-vgroup="Panels" data-vlabel="Relay settings">
      <summary data-i18n="Relay settings">Relay settings</summary>
      <div class="mut" id="relay-note"></div>
      <div id="relay-editor"></div>
      <div class="btns"><button class="sec" onclick="relayPost({action:'add'})" data-i18n="+ Add relay">+ Add relay</button></div>
    </details>
    <div id="settings"></div>
  </aside>
</main>
<script>
const $ = s => document.querySelector(s);
const post = (u, b) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b || {})})
    .then(r => r.json()).catch(() => ({ok: false, error: "connection"}));
const ctrl = {};
let editing = null;
const I18N = {de: {
  "Controls": "Steuerung", "System": "System", "Event log": "Ereignisprotokoll", "Expand all": "Alle öffnen",
  "Collapse all": "Alle schließen", "+ Waypoint": "+ Wegpunkt", "Clear waypoints": "Wegpunkte löschen", "Snapshot": "Schnappschuss",
  "Recalibrate": "Neu kalibrieren", "Reset counter": "Zähler zurücksetzen", "Reset settings": "Einstellungen zurücksetzen",
  "CPU load, last 60 seconds": "CPU-Last, letzte 60 Sekunden", "Step per click": "Schritt pro Klick",
  "Pi connected": "Pi verbunden", "Pi not reachable": "Pi nicht erreichbar",
  "calm": "ruhig", "breezy": "böig", "strong": "stark", "storm": "Sturm", "⚠ no password": "⚠ kein Passwort",
  "Wi-Fi / hotspot": "WLAN / Hotspot", "Search networks": "Netze suchen", "Searching …": "Suche läuft …", "Saved networks": "Gespeicherte Netze",
  "Connected with": "Verbunden mit", "Page address": "Adresse dieser Seite", "or": "oder", "connecting to": "verbinde mit", "connected to": "verbunden mit",
  "failed": "fehlgeschlagen", "back on": "zurück im Netz", "Password": "Passwort", "Password (empty = keep the saved one)": "Passwort (leer = gespeichertes behalten)",
  "show password": "Passwort zeigen", "prefer this network (before other known networks)": "dieses Netz bevorzugen (vor anderen bekannten Netzen)",
  "Connect now": "Jetzt verbinden", "Only save (connects automatically)": "Nur speichern (verbindet automatisch)", "Forget network": "Netz vergessen",
  "Forget this network?": "Dieses Netz vergessen?", "no networks found": "keine Netze gefunden",
  "Press 'Search networks'. Switch on the hotspot of the phone first.": "Auf «Netze suchen» tippen. Vorher den Hotspot am Handy einschalten.",
  "saved": "gespeichert", "preferred": "bevorzugt", "no auto connect": "nicht automatisch", "Other / hidden network …": "Anderes / verstecktes Netz …",
  "Network name (SSID)": "Netzname (SSID)", "The Pi is connected with this network.": "Der Pi ist mit diesem Netz verbunden.",
  "The Pi now switches to the network": "Der Pi wechselt jetzt ins Netz",
  "This page will probably lose its connection. Afterwards open it in that network at": "Diese Seite verliert dabei vermutlich die Verbindung. Öffne sie danach in diesem Netz unter",
  "or with the address from the push message. If it does not work, the Pi returns to the previous network after about a minute.":
    "oder mit der Adresse aus der Push-Nachricht. Klappt es nicht, kehrt der Pi nach etwa einer Minute ins bisherige Netz zurück.",
  "The connection to this page was interrupted - normal while the Pi changes the network. Open the page in the new network:":
    "Die Verbindung zu dieser Seite ist unterbrochen - beim Netzwechsel normal. Öffne die Seite im neuen Netz:",
  "(or the address from the push message).": "(oder mit der Adresse aus der Push-Nachricht).",
  "The Pi is connected with it right now - the page may lose its connection.": "Der Pi ist gerade damit verbunden - die Seite kann die Verbindung verlieren.",
  "Wi-Fi management is not available on this system (NetworkManager or wpa_supplicant missing).": "WLAN-Verwaltung ist auf diesem System nicht verfügbar (NetworkManager oder wpa_supplicant fehlt).",
  "none": "keine",
  "Network": "Netzwerk", "Automatic: phone hotspot / known networks, otherwise own Wi-Fi": "Automatik: Handy-Hotspot / bekannte Netze, sonst eigenes WLAN",
  "Own Wi-Fi at boot": "Beim Hochfahren eigenes WLAN", "Only known networks": "Nur bekannte Netze", "Autostart at boot": "Autostart beim Hochfahren",
  "automatic paused (switched by hand) - choose «Automatic» again to resume": "Automatik pausiert (von Hand geschaltet) - «Automatik» erneut wählen zum Fortsetzen",
  "own Wi-Fi on": "eigenes WLAN an", "searching known networks …": "suche bekannte Netze …",
  "own Wi-Fi on - search postponed (a device is connected)": "eigenes WLAN an - Suche verschoben (ein Gerät ist verbunden)",
  "connected with": "verbunden mit", "no known network - own Wi-Fi in": "kein bekanntes Netz - eigenes WLAN in",
  "own Wi-Fi on - next search for known networks in": "eigenes WLAN an - nächste Suche nach bekannten Netzen in",
  "tries the known networks (phone hotspot), otherwise switches the own Wi-Fi on": "versucht die bekannten Netze (Handy-Hotspot), sonst schaltet es das eigene WLAN ein",
  "switches the own Wi-Fi on": "schaltet das eigene WLAN ein", "joins the known networks": "verbindet sich mit den bekannten Netzen",
  "on: when the Pi boots, Motion Watch starts by itself and": "an: beim Hochfahren startet Motion Watch von selbst und",
  "Autostart with own Wi-Fi": "Autostart mit eigenem WLAN", "Autostart on": "Autostart an", "Autostart off": "Autostart aus",
  "on: when the Pi boots, Motion Watch starts by itself and switches the own Wi-Fi on": "an: beim Hochfahren startet Motion Watch von selbst und schaltet das eigene WLAN ein",
  "off: nothing starts at boot, the Pi joins its known networks": "aus: beim Hochfahren startet nichts, der Pi verbindet sich mit den bekannten Netzen",
  "Alarm & camping": "Alarm & Camping", "Notifications": "Benachrichtigungen", "Detection": "Erkennung", "Camera & servos": "Kamera & Servos",
  "Recordings & timelapse": "Aufnahmen & Zeitraffer", "Thermal camera": "Wärmebild", "Relays & schedule": "Relais & Zeitplan",
  "System & network": "System & Netz", "Advanced": "Erweitert",
  "Camping / protection": "Camping / Schutz", "Armed": "Scharf", "Armed in": "Scharf in", "Disarmed": "Unscharf",
  "🛡 Arm (countdown)": "🛡 Scharf schalten (Countdown)", "Arm now": "Sofort scharf", "Disarm": "Unscharf schalten",
  "no alarms, no recordings": "keine Alarme, keine Aufnahmen", "leave the area now": "jetzt den Bereich verlassen", "alarms active": "Alarme aktiv",
  "tap: arm / disarm": "Antippen: scharf / unscharf", "Camping profile": "Camping-Profil",
  "cp-desc": "Eigenes WLAN an, die Kamera bleibt stehen (keine Patrouille / Verfolgung / Zeitraffer), Alarme und Aufnahmen an, scharf nach dem Countdown. Ausschalten stellt deine Einstellungen wieder her.",
  "Own Wi-Fi (hotspot)": "Eigenes WLAN (Hotspot)", "Own Wi-Fi": "Eigenes WLAN", "own Wi-Fi": "eigenes WLAN", "device": "Gerät", "devices": "Geräte",
  "switching …": "schaltet um …", "on": "an", "name": "Name", "password": "Passwort", "Clock": "Uhrzeit", "taken from the phone": "vom Handy übernommen",
  "correct": "stimmt", "time zone": "Zeitzone", "set by the internet (NTP)": "über das Internet gestellt (NTP)",
  "needs NetworkManager (Raspberry Pi OS Bookworm or newer)": "braucht NetworkManager (Raspberry Pi OS Bookworm oder neuer)",
  "The Pi now switches on its own Wi-Fi": "Der Pi schaltet jetzt sein eigenes WLAN ein",
  "This page loses its connection. Connect the phone to": "Diese Seite verliert die Verbindung. Verbinde das Handy mit",
  "and open": "und öffne", "the camera stays where it is (no patrol, tracking or timelapse)": "die Kamera bleibt stehen (keine Patrouille, Verfolgung oder Zeitraffer)",
  "alarms and recordings on": "Alarme und Aufnahmen an", "armed after the countdown": "scharf nach dem Countdown",
  "End camping? The own Wi-Fi is switched off again - this page loses its connection and the Pi goes back to the known networks.":
    "Camping beenden? Das eigene WLAN wird ausgeschaltet - diese Seite verliert die Verbindung und der Pi geht zurück in die bekannten Netze.",
  "Switch the own Wi-Fi off? This page loses its connection; the Pi goes back to the known networks.":
    "Eigenes WLAN ausschalten? Diese Seite verliert die Verbindung; der Pi geht zurück in die bekannten Netze.",
  "Camping profile ON": "Camping-Profil an", "Camping profile OFF": "Camping-Profil aus",
  "Wi-Fi signal, last": "WLAN-Signal, letzte", "min": "Min.", "weakest": "schwächster", "drop-out": "Aussetzer",
  "drop-outs": "Aussetzer", "no drop-outs": "keine Aussetzer",
  "no Wi-Fi": "kein WLAN", "no internet": "kein Internet", "Wi-Fi": "WLAN", "not connected": "nicht verbunden", "Internet": "Internet",
  "online": "online", "offline": "offline",
  "Use current position": "Aktuelle Position übernehmen", "Show position": "Position anzeigen", "Photo now": "Foto jetzt",
  "Create video": "Video erstellen", "All days": "Alle Tage", "photos": "Fotos", "Download": "Herunterladen", "Remove this video?": "Dieses Video löschen?",
  "Photo requested": "Foto angefordert", "off": "aus", "waiting: alarm has priority": "wartet: Alarm hat Vorrang",
  "waiting: manual control": "wartet: Handsteuerung", "moving to the photo position": "fährt zur Fotoposition", "photo saved": "Foto gespeichert",
  "next photo in": "nächstes Foto in", "making video": "Video wird erstellt", "video ready": "Video fertig", "connected": "verbunden",
  "connecting…": "verbinde …", "no thermal camera selected": "keine Wärmebildkamera gewählt",
  "same camera as the main picture": "gleiche Kamera wie das Hauptbild", "connection lost - reconnecting": "Verbindung verloren - verbinde neu",
  "The thermal camera must look in the same direction as the main camera. Choose it in the list after a camera scan (Video source).":
    "Die Wärmebildkamera muss in dieselbe Richtung blicken wie die Hauptkamera. Wähle sie nach einem Kamera-Scan (Videoquelle) in der Liste aus.",
  "Speed": "Tempo", "slow": "langsam", "medium": "mittel", "fast": "schnell", "Centre": "Mitte", "Control": "Steuerung", "Stick": "Stick", "Buttons": "Tasten",
  "No person": "Keine Person", "PERSON DETECTED": "PERSON ERKANNT", "PERSONS DETECTED": "PERSONEN ERKANNT",
  "object": "Objekt", "objects": "Objekte", "No rain": "Kein Regen", "RAIN MODE": "REGENMODUS", "Wind": "Wind",
  "Idle": "Bereit", "REC": "AUFN", "LOW LIGHT": "SCHWACHLICHT", "Light ok": "Licht ok", "Settings": "Einstellungen",
  "recordings": "Aufnahmen", "viewers": "Zuschauer", "notify": "Alarm", "Tracking person": "Person wird verfolgt",
  "Manual control - tracking / patrol paused": "Handsteuerung - Verfolgung / Patrouille pausiert",
  "Patrol": "Patrouille", "waypoints": "Wegpunkte", "Objects": "Objekte", "FPS": "FPS", "PERSONS NOW": "PERSONEN JETZT",
  "OBJECTS": "OBJEKTE", "DETECTIONS": "ERKENNUNGEN", "cores": "Kerne", "online": "online", "offline": "offline",
  "Reset all settings to defaults?": "Alle Einstellungen auf Standard zurücksetzen?", "arrow keys work too": "Pfeiltasten gehen auch",
  "Relays": "Relais", "Relay settings": "Relais-Einstellungen", "+ Add relay": "+ Relais hinzufügen", "Off": "Aus", "On": "Ein",
  "Auto": "Auto", "Name": "Name", "GPIO": "GPIO", "Hold (s)": "Halten (s)", "Active low": "Low-aktiv", "Remove": "Entfernen",
  "Remove this relay?": "Dieses Relais entfernen?", "needs AI model": "braucht das KI-Modell",
  "Header": "Kopfzeile", "Statistics": "Statistiken", "Panels": "Bereiche", "Title": "Titel", "Persons": "Personen",
  "Rain": "Regen", "Recording": "Aufnahme", "Light level": "Lichtverhältnisse", "CPU": "CPU", "Connection": "Verbindung",
  "Persons now": "Personen jetzt", "Detections": "Erkennungen", "Object list": "Objektliste", "Settings panel": "Einstellungsbereich",
  "Show all": "Alle einblenden", "View": "Ansicht", "no relays": "keine Relais",
  "Auto: the relay switches on while its trigger is in view and stays on for the hold time. Animal and object triggers (e.g. cat) need the AI model.":
    "Auto: Das Relais schaltet ein, solange sein Auslöser im Bild ist, und bleibt für die Haltezeit an. Tier- und Objekt-Auslöser (z. B. Katze) brauchen das KI-Modell."
}};
Object.assign(I18N.de, {
  "Live": "Live", "Cameras": "Kameras", "Zones": "Zonen", "Presence": "Anwesenheit", "Security warning": "Sicherheitswarnung",
  "⚠ no password": "⚠ kein Passwort", "Saved": "Gespeichert", "Clear": "Löschen", "set": "gesetzt", "Test notification": "Test-Nachricht senden",
  "Test sent": "Test gesendet", "Fixed times": "Feste Zeiten", "Sunset → sunrise": "Sonnenuntergang → Sonnenaufgang", "Sunrise → sunset": "Sonnenaufgang → Sonnenuntergang",
  "Shift (minutes)": "Versatz (Minuten)", "Time window": "Zeitfenster", "Applies": "Gilt", "Always": "Immer", "Only when nobody is home": "Nur wenn niemand zuhause ist",
  "Only when somebody is home": "Nur wenn jemand zuhause ist", "Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)": "Ausnahmedaten (JJJJ-MM-TT, Bereiche mit .., MM-TT jedes Jahr)",
  "home": "zuhause", "away": "abwesend", "unknown": "unbekannt",
  "Video source": "Videoquelle", "Source": "Quelle", "Schedule": "Zeitplan", "Recordings": "Aufzeichnungen",
  "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …",
  "Automatic (first working USB camera)": "Automatisch (erste funktionierende USB-Kamera)",
  "Add network camera": "Netzwerk-Kamera hinzufügen", "Add": "Hinzufügen", "Remove this network camera?": "Diese Netzwerk-Kamera entfernen?",
  "+ Add schedule": "+ Zeitplan hinzufügen", "no schedules": "keine Zeitpläne", "Remove this schedule?": "Diesen Zeitplan entfernen?",
  "active now": "aktiv", "From": "Von", "To": "Bis", "unchanged": "unverändert", "ON": "EIN", "OFF": "AUS", "Enabled": "Aktiv",
  "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "starting": "startet",
  "connection lost - reconnecting": "Verbindung verloren - verbinde neu", "no cameras found": "keine Kameras gefunden", "in use": "in Benutzung",
  "While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. Switching one by hand overrides the schedule until its next change.":
    "Solange ein Zeitplan aktiv ist, werden die gewählten Funktionen fest EIN oder AUS geschaltet. Danach gilt wieder deine eigene Einstellung. Wer von Hand schaltet, überstimmt den Zeitplan bis zu dessen nächster Änderung."
});
let LANG = "", THEME = "", videoOnly = false, TRIG = [], sigQ = "", sigE = "";
let HIDDEN = new Set();
try { LANG = localStorage.getItem("mw-lang") || ""; THEME = localStorage.getItem("mw-theme") || "";
      HIDDEN = new Set(JSON.parse(localStorage.getItem("mw-hidden") || "[]")); } catch (e) {}
function t(s) { return (LANG === "de" && I18N.de[s]) || s; }
let toastTimer = null;
function toast(msg) { let e = $("#toast"); if (!e) { e = el("div"); e.id = "toast"; document.body.appendChild(e); } e.textContent = msg; e.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("on"), 2600); }
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(e => e.textContent = t(e.dataset.i18n));
  document.querySelectorAll(".stat small").forEach(e => { if (!e.dataset.en) e.dataset.en = e.textContent; e.textContent = t(e.dataset.en); });
  $("#btn-lang").textContent = LANG === "de" ? "EN" : "DE";
  $("#relay-note").textContent = t("Auto: the relay switches on while its trigger is in view and stays on for the hold time. Animal and object triggers (e.g. cat) need the AI model.");
  $("#sched-note").textContent = t("While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. Switching one by hand overrides the schedule until its next change.");
  document.documentElement.lang = LANG;
}
function applyTheme() {
  document.body.classList.toggle("light", THEME === "light");
  $("#btn-theme").innerHTML = THEME === "light" ? "&#9790;" : "&#9728;";
}
function toggleTheme() { THEME = THEME === "light" ? "dark" : "light"; try { localStorage.setItem("mw-theme", THEME); } catch (e) {} applyTheme(); }
function toggleLang() { LANG = LANG === "de" ? "en" : "de"; try { localStorage.setItem("mw-lang", LANG); } catch (e) {} location.reload(); }
function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {});
}

// ---- show / hide every field individually (stored per browser) ----
function saveHidden() { try { localStorage.setItem("mw-hidden", JSON.stringify([...HIDDEN])); } catch (e) {} }
function applyHidden() {
  document.querySelectorAll("[data-view]").forEach(e => e.classList.toggle("vh", HIDDEN.has(e.dataset.view)));
  document.body.classList.toggle("noside", HIDDEN.has("sidebar"));
  $("#btn-side").innerHTML = HIDDEN.has("sidebar") ? "&#9664;" : "&#9654;";
}
function toggleHidden(k) { HIDDEN.has(k) ? HIDDEN.delete(k) : HIDDEN.add(k); saveHidden(); applyHidden(); }
function buildViewMenu() {
  const m = $("#viewmenu"); m.textContent = ""; const groups = {};
  document.querySelectorAll("[data-view]").forEach(e => (groups[e.dataset.vgroup] = groups[e.dataset.vgroup] || []).push(e));
  ["Header", "Statistics", "Panels", "Settings"].forEach(g => {
    if (!groups[g]) return;
    m.appendChild(el("h3", "", t(g)));
    groups[g].forEach(e => {
      const lab = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = !HIDDEN.has(e.dataset.view);
      cb.onchange = () => toggleHidden(e.dataset.view);
      lab.append(cb, el("span", "", t(e.dataset.vlabel))); m.appendChild(lab);
    });
  });
  const b = el("button", "sec", t("Show all")); b.style.cssText = "margin-top:10px;width:100%";
  b.onclick = () => { HIDDEN.clear(); saveHidden(); applyHidden(); buildViewMenu(); };
  m.appendChild(b);
}
function toggleViewMenu(ev) { ev.stopPropagation(); const m = $("#viewmenu"); m.hidden = !m.hidden; if (!m.hidden) buildViewMenu(); }
document.addEventListener("click", e => { const m = $("#viewmenu"); if (!m.hidden && !m.contains(e.target) && document.body.contains(e.target)) m.hidden = true; });

function badge(id, text, cls) { const b = $(id); b.textContent = text; b.className = "badge" + (cls ? " " + cls : "") + (HIDDEN.has(b.dataset.view) ? " vh" : ""); }
function act(a) { post("/api/action", {action: a}); }
function showPos(pan, tilt) {
  if (typeof pan !== "number" || typeof tilt !== "number") return;
  const x = Math.max(0, Math.min(100, pan)), y = 100 - Math.max(0, Math.min(100, tilt));     // tilt up = higher on the stick
  const p = $("#spos"); if (!p) return;
  p.style.left = x + "%"; p.style.top = y + "%";
  $("#sline-v").style.left = x + "%"; $("#sline-h").style.top = y + "%";
  const tx = $("#spos-txt"); tx.textContent = "";
  tx.append(el("b", "", "◎ "), document.createTextNode("Pan " + Math.round(pan) + " % · Tilt " + Math.round(tilt) + " %"));
}
function move(dir) { post("/api/move", {dir: dir, step: parseFloat($("#step").value)}).then(r => { if (r && r.ok) showPos(r.pan, r.tilt); }); }

// ---- relays ----
function relayPost(body) {
  body.lang = LANG;
  return post("/api/relay", body).then(r => {
    const e = $("#relay-err"); e.textContent = r.ok ? "" : "⚠ " + (r.error || "error");
    if (!r.ok) setTimeout(() => { e.textContent = ""; }, 5000);
    sigQ = sigE = "";            // force a rebuild with the new values
    return r;
  });
}
function renderRelays(relays, states, aiOk) {
  const q = $("#relay-quick");
  const sq = JSON.stringify([relays.map(r => [r.name, r.trigger]), aiOk]);
  if (sq !== sigQ && !q.contains(document.activeElement)) {
    sigQ = sq; q.textContent = "";
    if (!relays.length) q.appendChild(el("span", "mut", t("no relays")));
    relays.forEach((r, i) => {
      const dot = el("span", "dot", "●"); dot.id = "rq-dot-" + i;
      const seg = el("span", "seg"); seg.id = "rq-seg-" + i;
      ["off", "on", "auto"].forEach(m => {
        const b = el("button", "", t(m === "off" ? "Off" : m === "on" ? "On" : "Auto")); b.dataset.mode = m;
        b.onclick = () => relayPost({action: "set", index: i, field: "mode", value: m}); seg.appendChild(b);
      });
      const sel = el("select");
      TRIG.forEach(o => { const op = el("option", "", o.label); op.value = o.key; sel.appendChild(op); });
      sel.value = r.trigger;
      sel.onchange = () => relayPost({action: "set", index: i, field: "trigger", value: sel.value});
      const tw = el("span"); tw.appendChild(sel);
      if (!aiOk && r.trigger !== "person" && r.trigger !== "motion") { const w = el("span", "warn", " ⚠"); w.title = t("needs AI model"); tw.appendChild(w); }
      q.append(dot, el("span", "", r.name), seg, tw);
    });
  }
  relays.forEach((r, i) => {
    const d = $("#rq-dot-" + i); if (d) d.classList.toggle("on", !!states[i]);
    const s = $("#rq-seg-" + i); if (s) s.querySelectorAll("button").forEach(b => b.className = b.dataset.mode === r.mode ? "sel-" + r.mode : "");
  });
  const ed = $("#relay-editor"), se = JSON.stringify(relays);
  if (se !== sigE && !ed.contains(document.activeElement)) {
    sigE = se; ed.textContent = "";
    relays.forEach((r, i) => {
      const box = el("div", "rel-ed");
      const field = (label, input) => { const w = el("label", "mut"); w.append(el("div", "", t(label)), input); return w; };
      const send = (f, v) => relayPost({action: "set", index: i, field: f, value: v});
      const name = el("input"); name.type = "text"; name.value = r.name; name.onchange = () => send("name", name.value);
      const gpio = el("input"); gpio.type = "number"; gpio.min = 2; gpio.max = 27; gpio.value = r.gpio; gpio.onchange = () => send("gpio", gpio.value);
      const hold = el("input"); hold.type = "number"; hold.min = 0.5; hold.max = 600; hold.step = 0.5; hold.value = r.hold; hold.onchange = () => send("hold", hold.value);
      const al = el("input"); al.type = "checkbox"; al.className = "sw"; al.checked = r.active_low; al.onchange = () => send("active_low", al.checked);
      const alw = el("label", "row tg"); alw.append(el("span", "", t("Active low")), al);
      const del = el("button", "sec", t("Remove")); del.onclick = () => { if (confirm(t("Remove this relay?"))) relayPost({action: "remove", index: i}); };
      box.append(field("Name", name), field("GPIO", gpio), field("Hold (s)", hold), alw, del);
      ed.appendChild(box);
    });
  }
}

// ---- video source (scan, choose, network cameras) ----
let SRC = null, sigS = "", lastSrcId = null, autoScanned = false;
function srcErr(msg) {
  const e = $("#src-err"); e.textContent = msg ? "⚠ " + msg : "";
  if (msg) setTimeout(() => { e.textContent = ""; }, 6000);
}
function tStatus(s) {
  if (!s) return "";
  if (s.startsWith("failed:")) return t("failed") + s.slice(7);
  return t(s);
}
function srcName(it) { return it.id === "auto" ? t("Automatic (first working USB camera)") : it.name; }
function renderSourceStatus(s) {
  $("#src-status").textContent = (s.source_label || "–") + (s.source_res ? " · " + s.source_res : "") + " · " + tStatus(s.source_status);
}
async function loadSources(scan) {
  const btn = $("#btn-scan");
  if (scan) { btn.disabled = true; btn.textContent = t("Scanning…"); }
  let r = null;
  try { r = scan ? await post("/api/sources/scan", {}) : await (await fetch("/api/sources")).json(); } catch (e) { r = null; }
  if (scan) { btn.disabled = false; btn.textContent = t("Scan for cameras"); }
  if (r && r.items) SRC = r;
  sigS = ""; renderSources();
  if (!scan && SRC && !SRC.scanned && !SRC.scanning && !autoScanned) { autoScanned = true; loadSources(true); }   // first visit: look for cameras once
}
function scanSources() { loadSources(true); }
function srcPost(body) {
  body.lang = LANG;
  return post("/api/source", body).then(r => { srcErr(r.ok ? "" : (r.error || "error")); loadSources(false); return r; });
}
function selectSource(id) { srcPost({action: "select", id: id}); }
function addIpSource() {
  srcPost({action: "add", name: $("#ip-name").value, url: $("#ip-url").value, select: true})
    .then(r => { if (r.ok) { $("#ip-name").value = ""; $("#ip-url").value = ""; } });
}
function renderSources() {
  if (!SRC || !SRC.items) return;
  $("#src-hints").textContent = (SRC.hints || []).join(" ");
  const L = $("#src-list"), sig = JSON.stringify([SRC.items, SRC.selected, SRC.active, LANG]);
  if (sig === sigS) return;
  sigS = sig; L.textContent = "";
  SRC.items.forEach(it => {
    const row = el("label", "srcrow");
    const rb = el("input"); rb.type = "radio"; rb.name = "src"; rb.checked = it.id === SRC.selected;
    rb.onchange = () => selectSource(it.id);
    const dot = el("span", "dot" + (it.id === SRC.active ? " on" : ""), "●");
    const info = el("span"); info.style.flex = "1"; info.style.minWidth = "0";
    info.append(el("div", "", srcName(it)), el("div", "mut", (it.detail || "").replace("in use", t("in use"))));
    row.append(rb, dot, info);
    if (it.kind === "url") {
      const x = el("button", "sec", "✕"); x.style.padding = "2px 8px"; x.title = t("Remove");
      x.onclick = e => { e.preventDefault(); if (confirm(t("Remove this network camera?"))) srcPost({action: "remove", id: it.id.slice(4)}); };
      row.appendChild(x);
    }
    L.appendChild(row);
  });
  if (SRC.items.length <= 1) L.appendChild(el("div", "mut", t("no cameras found")));
}

// ---- schedule ----
let FEAT = [], sigC = "";
const DAYS = () => LANG === "de" ? ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"] : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
function schedPost(body) {
  body.lang = LANG;
  return post("/api/schedule", body).then(r => {
    const e = $("#sched-err"); e.textContent = r.ok ? "" : "⚠ " + (r.error || "error");
    if (!r.ok) setTimeout(() => { e.textContent = ""; }, 5000);
    sigC = "";                                        // rebuild with the values the server really stored
    return r;
  });
}
function textField(x) {
  const wrap = el("div", "sl"), top = el("div", "row"); top.appendChild(el("span", "", x.label)); wrap.appendChild(top);
  let inp;
  if (x.kind === "enum") { inp = el("select"); x.choices.forEach(c => { const o = el("option", "", (x.labels && x.labels[c]) || c); o.value = c; inp.appendChild(o); }); inp.value = x.value; }
  else { inp = el("input"); inp.type = x.kind === "secret" ? "password" : "text"; inp.value = x.value || ""; inp.autocomplete = "off";
         if (x.kind === "secret" && x.set) inp.placeholder = "•••••• (" + t("set") + ")"; }
  inp.style.width = "100%"; inp.style.marginTop = "4px";
  const err = el("div", "err");
  const send = v => post("/api/text", {key: x.key, value: v, lang: LANG}).then(r => { err.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) toast(t("Saved")); return r; });
  inp.onchange = () => { if (x.kind === "secret" && inp.value === "") return;
    send(inp.value).then(r => { if (r.ok && x.kind === "secret") { inp.value = ""; inp.placeholder = "•••••• (" + t("set") + ")"; } }); };
  wrap.append(inp, err);
  if (x.kind === "secret") { const c = el("button", "sec", t("Clear")); c.style.marginTop = "2px"; c.onclick = () => send(" ").then(r => { if (r.ok) inp.placeholder = ""; }); wrap.appendChild(c); }
  return wrap;
}
function schedBox(s, i) {
  const box = el("div", "rel-ed"); box.style.gridTemplateColumns = "1fr";
  const cur = JSON.parse(JSON.stringify(s));          // working copy that the controls edit and send
  const save = () => schedPost({action: "save", index: i, schedule: cur});
  const r1 = el("div", "row"); r1.style.gap = "6px";
  const name = el("input"); name.type = "text"; name.value = s.name; name.style.flex = "1"; name.style.minWidth = "0";
  name.onchange = () => { cur.name = name.value; save(); };
  const act = el("span", "badge grn", t("active now")); act.id = "sc-act-" + i; act.hidden = true;
  const en = el("input"); en.type = "checkbox"; en.className = "sw"; en.checked = s.enabled; en.title = t("Enabled");
  en.onchange = () => { cur.enabled = en.checked; save(); };
  const del = el("button", "sec", "✕"); del.title = t("Remove"); del.style.padding = "4px 9px";
  del.onclick = () => { if (confirm(t("Remove this schedule?"))) schedPost({action: "remove", index: i}); };
  r1.append(name, act, en, del);
  const days = el("div", "days");
  DAYS().forEach((d, k) => {
    const b = el("button", cur.days.includes(k) ? "on" : "", d);
    b.onclick = () => {
      const on = !cur.days.includes(k);
      cur.days = on ? cur.days.concat([k]).sort() : cur.days.filter(x => x !== k);
      b.classList.toggle("on", on); save();
    };
    days.appendChild(b);
  });
  const times = el("div", "row"); times.style.justifyContent = "flex-start"; times.style.gap = "14px";
  [["start", "From"], ["end", "To"]].forEach(([key, label]) => {
    const w = el("label", "mut"), inp = el("input"); inp.type = "time"; inp.value = s[key];
    inp.onchange = () => { if (inp.value) { cur[key] = inp.value; save(); } };
    w.append(el("span", "", t(label) + " "), inp); times.appendChild(w);
  });
  const feats = el("div");
  FEAT.forEach(f => {
    const row = el("label", "row"); row.style.padding = "2px 0"; row.appendChild(el("span", "", f.label));
    const sel = el("select"); sel.style.width = "auto";
    [["", t("unchanged")], ["on", t("ON")], ["off", t("OFF")]].forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sel.appendChild(o); });
    sel.value = f.key in cur.actions ? (cur.actions[f.key] ? "on" : "off") : "";
    sel.onchange = () => { if (sel.value === "") delete cur.actions[f.key]; else cur.actions[f.key] = sel.value === "on"; save(); };
    row.appendChild(sel); feats.appendChild(row);
  });
  const adv = el("div"); adv.style.cssText = "display:grid;gap:6px;margin:8px 0";
  const mk = (label, node) => { const w = el("label", "mut"); w.append(el("div", "", t(label)), node); return w; };
  const mkSel = (opts, val, fn) => { const sl = el("select"); sl.style.width = "100%"; opts.forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sl.appendChild(o); }); sl.value = val; sl.onchange = () => fn(sl.value); return sl; };
  const off = el("input"); off.type = "number"; off.min = -180; off.max = 180; off.step = 5; off.value = cur.sun_offset || 0; off.style.width = "100px";
  const offw = mk("Shift (minutes)", off);
  const sync = () => { times.querySelectorAll("input").forEach(x => { x.disabled = !!cur.sun; }); offw.style.display = cur.sun ? "" : "none"; };
  off.onchange = () => { cur.sun_offset = parseInt(off.value, 10) || 0; save(); };
  const skip = el("input"); skip.type = "text"; skip.placeholder = "2026-12-24..2026-12-26, 08-01"; skip.value = cur.skip || ""; skip.style.width = "100%";
  skip.onchange = () => { cur.skip = skip.value; save(); };
  adv.append(mk("Time window", mkSel([["", t("Fixed times")], ["dark", t("Sunset → sunrise")], ["light", t("Sunrise → sunset")]], cur.sun || "", v => { cur.sun = v; sync(); save(); })), offw,
             mk("Applies", mkSel([["", t("Always")], ["away", t("Only when nobody is home")], ["home", t("Only when somebody is home")]], cur.presence || "", v => { cur.presence = v; save(); })),
             mk("Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)", skip));
  sync();
  box.append(r1, days, times, adv, feats);
  return box;
}
function renderSchedules(list, st) {
  const L = $("#sched-list"), sig = JSON.stringify([list, FEAT.length, LANG]);
  if (sig !== sigC && !L.contains(document.activeElement)) {
    sigC = sig; L.textContent = "";
    if (!list.length) L.appendChild(el("span", "mut", t("no schedules")));
    list.forEach((s, i) => L.appendChild(schedBox(s, i)));
  }
  const act = st.sched_active_idx || [];
  list.forEach((s, i) => { const b = $("#sc-act-" + i); if (b) b.hidden = !act.includes(i); });
}

// ---- settings in 8 groups: existing cards become sub-sections, settings sections become compact blocks ----
const GROUPS = [
  {id: "alarm", icon: "🛡", name: "Alarm & camping", inline: ["protect"], adv: ["Camping / protection"], open: true},
  {id: "notify", icon: "🔔", name: "Notifications", sections: ["Notifications"]},
  {id: "detect", icon: "🎯", name: "Detection", sections: ["Detection", "AI detection"],
   adv: ["Walking recognition", "Vehicle filter", "Rain", "Wind", "Low light", "Auto-tune"]},
  {id: "camera", icon: "📷", name: "Camera & servos", sections: ["Camera / Servos", "Patrol"], cards: ["source"]},
  {id: "rec", icon: "🎬", name: "Recordings & timelapse", sections: ["Recording", "Timelapse"]},
  {id: "thermal", icon: "🌡", name: "Thermal camera", sections: ["Thermal camera"]},
  {id: "relay", icon: "⚡", name: "Relays & schedule", sections: ["Relays"], cards: ["relayset", "schedule"], adv: ["Schedule"]},
  {id: "sys", icon: "📶", name: "System & network", cards: ["system", "log", "wifi"], sections: ["Web stream", "Setup"], cardsFirst: true,
   adv: ["Wi-Fi / hotspot", "Video source"]},
];
function toBlock(d) {
  const b = el("div", "blk"), title = d.querySelector("summary").textContent;
  const kids = [...d.children].filter(c => c.tagName !== "SUMMARY");
  if (d.querySelectorAll("input,select,button").length > 1 && title.trim().toLowerCase() !== (toBlock.group || "").trim().toLowerCase()) b.appendChild(el("h4", "", title));
  kids.forEach(k => b.appendChild(k));
  d.remove();
  return kids.length ? b : null;
}
function toSub(d, inline) {
  d.classList.remove("card"); d.classList.add("sub");
  if (inline) { d.classList.add("inline"); d.open = true; }
  return d;
}
function regroup() {
  const box = $("#settings"), aside = box.parentNode, used = new Set();
  const byView = v => document.querySelector('details[data-view="' + v + '"]');
  const frag = document.createDocumentFragment();
  GROUPS.forEach(g => {
    const G = el("details", "card grp"); G.dataset.view = "grp:" + g.id; G.dataset.vgroup = "Panels"; G.dataset.vlabel = g.name;
    if (g.open) G.open = true;
    const sm = el("summary"); sm.append(el("span", "gi", g.icon), el("span", "gn", t(g.name))); G.appendChild(sm);
    toBlock.group = t(g.name);
    const sec = (id, into) => { const d = byView("sec:" + id); if (!d) return; used.add("sec:" + id); const b = toBlock(d); if (b) into.appendChild(b); };
    (g.inline || []).forEach(v => { const d = byView(v); if (d) { used.add(v); G.appendChild(toSub(d, true)); } });
    const cards = () => (g.cards || []).forEach(v => { const d = byView(v); if (d) { used.add(v); G.appendChild(toSub(d, false)); } });
    if (g.cardsFirst) cards();
    (g.sections || []).forEach(id => sec(id, G));
    if (!g.cardsFirst) cards();
    const A = el("details", "adv"); A.dataset.view = "adv:" + g.id; A.appendChild(el("summary", "", t("Advanced")));
    (g.adv || []).forEach(id => sec(id, A));
    if (A.children.length > 1) G.appendChild(A);
    if (G.children.length > 1) frag.appendChild(G);
  });
  // anything not listed (e.g. a section added in a later version) ends up under System > Advanced
  const rest = [...box.querySelectorAll(':scope > details[data-view^="sec:"]')].filter(d => !used.has(d.dataset.view));
  if (rest.length) {
    const sys = frag.querySelector('[data-view="grp:sys"]'), A = sys.querySelector(":scope > details.adv") || sys.appendChild(el("details", "adv"));
    if (!A.querySelector("summary")) { A.dataset.view = "adv:sys"; A.appendChild(el("summary", "", t("Advanced"))); }
    rest.forEach(d => { const b = toBlock(d); if (b) A.appendChild(b); });
  }
  box.textContent = ""; box.appendChild(frag);
  const ab = $("#allbtns");                                 // right under "expand / collapse all" (computer)
  aside.insertBefore(box, ab && ab.parentNode === aside ? ab.nextSibling : aside.firstChild);
}

async function build() {
  try { TRIG = await (await fetch("/api/triggers?lang=" + LANG)).json(); } catch (e) { TRIG = []; }
  try { FEAT = (await (await fetch("/api/schedule?lang=" + LANG)).json()).features || []; } catch (e) { FEAT = []; }
  const sch = await (await fetch("/api/schema?lang=" + LANG)).json();
  const box = $("#settings");
  sch.forEach(sec => {
    const d = el("details", "card");
    d.appendChild(el("summary", "", sec.name));
    d.dataset.view = "sec:" + sec.id; d.dataset.vgroup = "Settings"; d.dataset.vlabel = sec.name;
    sec.toggles.forEach(tg => {
      const row = el("label", "row tg");
      const cb = el("input"); cb.type = "checkbox"; cb.className = "sw";
      cb.onchange = () => post("/api/set", {key: tg.key, value: cb.checked});
      row.append(el("span", "", tg.label), cb);
      d.appendChild(row); ctrl[tg.key] = {type: "bool", input: cb};
    });
    (sec.texts || []).forEach(x => d.appendChild(textField(x)));
    if (sec.id === "Notifications") {
      const tb = el("button", "sec", t("Test notification")); tb.style.marginTop = "8px";
      tb.onclick = () => post("/api/notify_test", {lang: LANG}).then(r => toast(r.ok ? t("Test sent") : "⚠ " + (r.error || "error"))); d.appendChild(tb);
    }
    sec.sliders.forEach(s => {
      const wrap = el("div", "sl"), top = el("div", "row");
      const val = el("span", "val", "");
      top.append(el("span", "", s.label), val);
      const r = el("input"); r.type = "range"; r.min = s.min; r.max = s.max; r.step = s.step;
      let timer = null;
      const send = () => post("/api/set", {key: s.key, value: parseFloat(r.value)});
      r.oninput = () => {
        editing = s.key; val.textContent = r.value;
        if (!timer) timer = setTimeout(() => { timer = null; send(); }, 100);   // throttle while dragging
      };
      r.onchange = () => { clearTimeout(timer); timer = null; send(); editing = null; };
      wrap.append(top, r); d.appendChild(wrap);
      ctrl[s.key] = {type: "num", input: r, val: val};
    });
    if (sec.id === "Timelapse") tlExtras(d);
    if (sec.id === "Thermal camera") thExtras(d);
    box.appendChild(d);
  });
}

// ---- timelapse + thermal camera: status, buttons, latest photo, videos ----
const TLTXT = () => ({"off": t("off"), "waiting: alarm has priority": t("waiting: alarm has priority"), "waiting: manual control": t("waiting: manual control"),
  "moving to the photo position": t("moving to the photo position"), "photo saved": t("photo saved"), "connected": t("connected"),
  "connecting…": t("connecting…"), "no thermal camera selected": t("no thermal camera selected"),
  "same camera as the main picture": t("same camera as the main picture"), "connection lost - reconnecting": t("connection lost - reconnecting")});
function tlTxt(s) {
  if (!s) return "";
  let m = /^next photo in (\d+) min$/.exec(s); if (m) return t("next photo in") + " " + m[1] + " min";
  m = /^making video (\d+)\/(\d+)$/.exec(s); if (m) return t("making video") + " " + m[1] + "/" + m[2];
  if (s.startsWith("video ready: ")) return t("video ready") + ": " + s.slice(12);
  m = /^taken from the phone (.*)$/.exec(s); if (m) return t("taken from the phone") + " " + m[1];
  if (s === "ok") return t("correct");
  if (s.startsWith("ok · time zone ")) return t("correct") + " · " + t("time zone") + " " + s.slice(15);
  return TLTXT()[s] || s;
}
let tlSeen = null;
function fmtDay(d) { return d.slice(6, 8) + "." + d.slice(4, 6) + "." + d.slice(0, 4); }
async function tlLoad() {
  let j; try { j = await (await fetch("/api/timelapse")).json(); } catch (e) { return; }
  const img = $("#tl-img"); if (!img) return;
  if (j.latest) { img.src = "/timelapse/" + j.latest; img.hidden = false; $("#tl-open").href = "/timelapse/" + j.latest; } else { img.hidden = true; }
  const cnt = $("#tl-count"); cnt.textContent = j.count + " " + t("photos");
  const sel = $("#tl-day"), keep = sel.value; sel.textContent = "";
  const all = el("option", "", t("All days")); all.value = ""; sel.appendChild(all);
  j.days.forEach(x => { const o = el("option", "", fmtDay(x.day) + " (" + x.count + ")"); o.value = x.day; sel.appendChild(o); });
  sel.value = keep;
  const L = $("#tl-videos"); L.textContent = "";
  j.videos.forEach(v => {
    const row = el("div", "row"); row.style.marginTop = "4px";
    const a = el("a", "", v.name); a.href = "/timelapse/" + v.name; a.target = "_blank"; a.style.color = "var(--acc2)"; a.style.wordBreak = "break-all";
    const dl = el("a", "", "⬇"); dl.href = "/timelapse/" + v.name + "?dl=1"; dl.title = t("Download"); dl.style.color = "var(--acc2)";
    const x = el("button", "sec", "✕"); x.style.padding = "2px 8px"; x.title = t("Remove");
    x.onclick = async () => { if (confirm(t("Remove this video?"))) { await post("/api/timelapse", {action: "delete_video", name: v.name}); tlLoad(); } };
    row.append(a, dl, x); L.appendChild(row);
  });
}
function tlExtras(d) {
  const st = el("div", "mut", ""); st.id = "tl-status"; st.style.margin = "6px 0";
  const btns = el("div", "btns");
  const mk = (txt, fn, cls) => { const b = el("button", cls || "sec", t(txt)); b.type = "button"; b.onclick = fn; return b; };
  btns.append(
    mk("Use current position", async () => { await post("/api/timelapse", {action: "here"}); toast(t("Saved")); }),
    mk("Show position", () => post("/api/timelapse", {action: "goto"})),
    mk("Photo now", async () => { await post("/api/timelapse", {action: "now"}); toast(t("Photo requested")); }));
  const img = el("img"); img.id = "tl-img"; img.hidden = true; img.alt = "latest timelapse photo";
  img.style.cssText = "width:100%;border-radius:10px;margin-top:8px;border:1px solid var(--line)";
  const open = el("a", ""); open.id = "tl-open"; open.target = "_blank"; open.appendChild(img);
  const cnt = el("div", "mut", ""); cnt.id = "tl-count";
  const vrow = el("div", "row"); vrow.style.marginTop = "10px";
  const sel = el("select"); sel.id = "tl-day"; sel.style.flex = "1";
  const mkv = mk("Create video", async () => {
    const r = await post("/api/timelapse", {action: "render", day: sel.value, lang: LANG});
    if (!r.ok) toast("⚠ " + (r.error || "error"));
  }, "");
  vrow.append(sel, mkv);
  const rs = el("div", "mut", ""); rs.id = "tl-render"; rs.style.marginTop = "4px";
  const vl = el("div", ""); vl.id = "tl-videos";
  d.append(st, btns, open, cnt, vrow, rs, vl);
  tlLoad(); setInterval(tlLoad, 30000);
}
function thExtras(d) {
  const st = el("div", "mut", ""); st.id = "th-status"; st.style.margin = "6px 0";
  const hint = el("div", "mut", t("The thermal camera must look in the same direction as the main camera. Choose it in the list after a camera scan (Video source).")); hint.style.marginTop = "4px";
  d.append(st, hint);
}
// ---- Wi-Fi / hotspot card: search, connect, save, forget ----
let WF = null, wfOpenSsid = null, wfPoll = null, wfLost = false;
function wfBars(n) { const b = el("span", "wbars"); for (let i = 1; i <= 4; i++) b.appendChild(el("i", i <= n ? "on" : "")); return b; }
function wfErr(m) { const e = $("#wf-err"); e.textContent = m ? "⚠ " + m : ""; }
async function wfLoad() {
  let j;
  try { j = await (await fetch("/api/wifi")).json(); wfLost = false; }
  catch (e) {
    if (WF && WF.busy) { wfLost = true; wfRenderStatus(); }
    return;
  }
  WF = j; wfRender();
  if (!j.busy && wfPoll) { clearInterval(wfPoll); wfPoll = null; }
}
async function wfPost(body) {
  body.lang = LANG; wfErr("");
  let r;
  try { r = await post("/api/wifi", body); } catch (e) { r = {ok: false, error: "connection"}; }
  if (r && r.backend !== undefined) { WF = r; wfRender(); }
  if (!r.ok) wfErr(r.error || "error");
  return r;
}
function wfRenderStatus() {
  const st = $("#wf-status"); if (!st || !WF) return;
  st.textContent = "";
  if (!WF.backend) { st.textContent = t("Wi-Fi management is not available on this system (NetworkManager or wpa_supplicant missing)."); return; }
  const line1 = el("div", "", WF.connected ? t("Connected with") + " «" + (WF.ssid || "?") + "»" + (WF.ip ? " · IP " + WF.ip : "") : t("not connected"));
  line1.style.fontWeight = "600"; line1.style.color = "var(--txt)";
  st.appendChild(line1);
  if (WF.address) {
    const a = el("div", ""); a.append(document.createTextNode(t("Page address") + ": "));
    const l1 = el("a", "", WF.address); l1.href = WF.address; l1.style.color = "var(--acc2)";
    const alt = (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/";
    const l2 = el("a", "", alt); l2.href = alt; l2.style.color = "var(--acc2)";
    a.append(l1, document.createTextNode(" · " + t("or") + " "), l2); st.appendChild(a);
  }
  if (WF.job) {
    const j = el("div", WF.job_ok === false ? "err" : "", wfJobText(WF.job)); j.style.marginTop = "4px";
    if (WF.job_ok === true) j.style.color = "var(--grn)";
    st.appendChild(j);
  }
  if (wfLost) {
    const w = el("div", "err", t("The connection to this page was interrupted - normal while the Pi changes the network. Open the page in the new network:")
      + " " + (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/ " + t("(or the address from the push message)."));
    w.style.marginTop = "6px"; st.appendChild(w);
  }
}
function wfJobText(s) {
  let m = /^connecting to (.*)…$/.exec(s); if (m) return t("connecting to") + " " + m[1] + " …";
  m = /^connected to (.*)$/.exec(s); if (m) return "✓ " + t("connected to") + " " + m[1];
  m = /^failed: (.*)$/.exec(s); if (m) return t("failed") + ": " + m[1].replace(" - back on ", " - " + t("back on") + " ");
  return s;
}
function wfForm(ssid0, secure, savedId, nameInput) {
  const f = el("div", "wf-form");
  const name = () => nameInput ? nameInput.value.trim() : ssid0;
  let pw = null;
  if (secure) {
    const r = el("div", "row"); r.style.gap = "6px";
    pw = el("input"); pw.type = "password"; pw.placeholder = savedId ? t("Password (empty = keep the saved one)") : t("Password"); pw.autocomplete = "off";
    pw.style.flex = "1"; pw.style.minWidth = "0";
    const eye = el("button", "sec", "👁"); eye.type = "button"; eye.style.padding = "4px 9px"; eye.title = t("show password");
    eye.onclick = () => { pw.type = pw.type === "password" ? "text" : "password"; };
    r.append(pw, eye); f.appendChild(r);
  }
  const pr = el("label", "row"); pr.style.marginTop = "6px";
  const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = true;
  pr.append(el("span", "mut", t("prefer this network (before other known networks)")), cb); f.appendChild(pr);
  const b = el("div", "btns");
  const go = el("button", "", t("Connect now")); go.type = "button";
  go.onclick = async () => {
    const ssid = name(); if (!ssid) { wfErr(t("Network name (SSID)") + "?"); return; }
    const msg = t("The Pi now switches to the network") + " «" + ssid + "». " + t("This page will probably lose its connection. Afterwards open it in that network at") + " "
      + (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/ " + t("or with the address from the push message. If it does not work, the Pi returns to the previous network after about a minute.");
    if (!confirm(msg)) return;
    const r = await wfPost({action: "connect", ssid: ssid, password: pw ? pw.value : "", preferred: cb.checked});
    if (r.ok) { wfOpenSsid = null; if (!wfPoll) wfPoll = setInterval(wfLoad, 2000); }
  };
  const sv = el("button", "sec", t("Only save (connects automatically)")); sv.type = "button";
  sv.onclick = async () => { const ssid = name(); if (!ssid) { wfErr(t("Network name (SSID)") + "?"); return; }
    const r = await wfPost({action: "save", ssid: ssid, password: pw ? pw.value : "", preferred: cb.checked}); if (r.ok) { toast(t("Saved")); wfOpenSsid = null; wfRender(); } };
  b.append(go, sv); f.appendChild(b);
  if (savedId) {
    const fg = el("button", "sec", t("Forget network")); fg.type = "button"; fg.style.marginTop = "6px"; fg.style.width = "100%";
    fg.onclick = async () => { if (confirm(t("Forget this network?") + " «" + name() + "»")) { await wfPost({action: "forget", id: savedId}); wfOpenSsid = null; wfRender(); } };
    f.appendChild(fg);
  }
  return f;
}
function wfRender() {
  wfRenderStatus();
  if (!WF) return;
  const L = $("#wf-list"), S = $("#wf-saved");
  const ae = document.activeElement;
  if (ae && ae.tagName === "INPUT" && (L.contains(ae) || S.contains(ae))) return;     // do not disturb typing
  L.textContent = ""; S.textContent = "";
  const savedBy = {}; (WF.saved || []).forEach(s => savedBy[s.ssid] = s);
  if (!WF.scan.length) L.appendChild(el("div", "mut", WF.scan_time ? t("no networks found") : t("Press 'Search networks'. Switch on the hotspot of the phone first.")));
  WF.scan.forEach(n => {
    const it = el("div", "wf-item" + (n.active ? " on" : ""));
    const head = el("div", "wf-head");
    head.append(wfBars(n.bars), el("b", "", n.ssid));
    if (n.secure) head.appendChild(el("span", "mut", "🔒"));
    const tags = el("span", "wf-tags");
    if (n.active) tags.appendChild(el("span", "badge grn", t("connected")));
    else if (savedBy[n.ssid]) tags.appendChild(el("span", "badge", t("saved")));
    tags.appendChild(el("span", "mut", n.signal + " %"));
    head.appendChild(tags);
    head.onclick = () => { wfOpenSsid = wfOpenSsid === n.ssid ? null : n.ssid; wfRender(); };
    it.appendChild(head);
    if (wfOpenSsid === n.ssid && !n.active) it.appendChild(wfForm(n.ssid, n.secure, (savedBy[n.ssid] || {}).id));
    if (wfOpenSsid === n.ssid && n.active) it.appendChild(el("div", "mut", t("The Pi is connected with this network.")));
    L.appendChild(it);
  });
  const other = el("button", "sec", t("Other / hidden network …")); other.type = "button"; other.style.marginTop = "8px"; other.style.width = "100%";
  other.onclick = () => { wfOpenSsid = wfOpenSsid === "\u0000other" ? null : "\u0000other"; wfRender(); };
  L.appendChild(other);
  if (wfOpenSsid === "\u0000other") {
    const box = el("div", "wf-item"); const nm = el("input"); nm.type = "text"; nm.placeholder = t("Network name (SSID)"); nm.style.width = "100%";
    box.appendChild(nm);
    box.appendChild(wfForm("", true, null, nm)); L.appendChild(box);
  }
  if (!(WF.saved || []).length) S.appendChild(el("div", "mut", t("none")));
  (WF.saved || []).sort((a, b) => b.prio - a.prio).forEach(s => {
    const r = el("div", "row wf-saved");
    const left = el("span", ""); left.append(el("b", "", s.ssid), document.createTextNode(s.active ? " · " + t("connected") : ""), el("span", "mut", (s.prio > 0 ? " · " + t("preferred") : "") + (s.auto ? "" : " · " + t("no auto connect"))));
    const x = el("button", "sec", "✕"); x.type = "button"; x.title = t("Forget network"); x.style.padding = "3px 9px";
    x.onclick = async () => { if (confirm(t("Forget this network?") + " «" + s.ssid + "»" + (s.active ? "\n" + t("The Pi is connected with it right now - the page may lose its connection.") : ""))) await wfPost({action: "forget", id: s.id}); };
    r.append(left, x); S.appendChild(r);
  });
}

$("#wf-scan").onclick = async () => {
  const b = $("#wf-scan"); b.disabled = true; b.textContent = t("Searching …");
  await wfPost({action: "scan"});
  b.disabled = false; b.textContent = t("Search networks");
};
$("#wf-card").addEventListener("toggle", () => { if ($("#wf-card").open) wfLoad(); });
setInterval(() => { if ($("#wf-card").open && !document.hidden) wfLoad(); }, 10000);
setTimeout(() => { if ($("#wf-card").open) wfLoad(); }, 1500);

// ---- camping / protection card + header badge ----
let PR = {campUntil: 0, hsUntil: 0};
function prText(s) {
  if (s.arm_state === "armed") return ["🛡 " + t("Armed"), "grn"];
  if (s.arm_state === "arming") return ["🛡 " + t("Armed in") + " " + s.arm_left + " s", "yel"];
  return ["🛡 " + t("Disarmed"), ""];
}
async function prArm(action) {
  const r = await post("/api/arm", {action: action});
  if (r && r.ok) toast(action === "disarm" ? t("Disarmed") : (r.left ? t("Armed in") + " " + r.left + " s" : t("Armed")));
}
function prHotspotMsg(r) {
  return t("The Pi now switches on its own Wi-Fi") + " «" + r.ssid + "» (" + t("password") + ": " + r.password + "). "
    + t("This page loses its connection. Connect the phone to") + " «" + r.ssid + "» " + t("and open") + " " + r.address;
}
async function prCamp(on) {
  const s = window.__lastState || {};
  if (on) {
    const hc = s.hotspot_cfg || {};
    const msg = t("Camping profile") + ":\n- " + t("own Wi-Fi") + " «" + hc.ssid + "» (" + t("password") + ": " + hc.password + ")\n- "
      + t("the camera stays where it is (no patrol, tracking or timelapse)") + "\n- " + t("alarms and recordings on") + "\n- "
      + t("armed after the countdown") + "\n\n" + t("This page loses its connection. Connect the phone to") + " «" + hc.ssid + "» " + t("and open") + " " + hc.address;
    if (!confirm(msg)) { $("#pr-camp").checked = false; return; }
  } else if (s.hotspot && s.hotspot.on && !confirm(t("End camping? The own Wi-Fi is switched off again - this page loses its connection and the Pi goes back to the known networks."))) { $("#pr-camp").checked = true; return; }
  PR.campUntil = Date.now() + 2500; PR.hsUntil = Date.now() + 2500;
  const r = await post("/api/camping", {on: on, lang: LANG});
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); return; }
  toast(on ? "⛺ " + t("Camping profile ON") : t("Camping profile OFF"));
}
async function prHotspot(on) {
  const s = window.__lastState || {}, hc = s.hotspot_cfg || {};
  if (on && !confirm(prHotspotMsg(hc))) { $("#pr-hs").checked = false; return; }
  if (!on && !confirm(t("Switch the own Wi-Fi off? This page loses its connection; the Pi goes back to the known networks."))) { $("#pr-hs").checked = true; return; }
  PR.hsUntil = Date.now() + 2500;
  const r = await post("/api/hotspot", {on: on, lang: LANG});
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); $("#pr-hs").checked = !on; }
}
function updateProtect(s) {
  window.__lastState = s;
  const [txt, cls] = prText(s);
  const b = $("#b-arm"); if (b) { badge("#b-arm", txt, cls); b.title = t("tap: arm / disarm"); }
  const st = $("#pr-state"); if (!st) return;
  st.textContent = txt; st.style.color = cls === "grn" ? "var(--grn)" : (cls === "yel" ? "var(--yel)" : "var(--mut)");
  $("#pr-left").textContent = s.arm_state === "disarmed" ? t("no alarms, no recordings") : (s.arm_state === "arming" ? t("leave the area now") : t("alarms active"));
  $("#pr-arm").hidden = s.arm_state !== "disarmed"; $("#pr-armnow").hidden = s.arm_state === "armed"; $("#pr-disarm").hidden = s.arm_state === "disarmed";
  const hs = s.hotspot || {}, hc = s.hotspot_cfg || {};
  if (Date.now() > PR.campUntil) $("#pr-camp").checked = !!s.camping;
  if (Date.now() > PR.hsUntil && !hs.busy) $("#pr-hs").checked = !!hs.on;
  $("#pr-hs").disabled = hs.available === false;
  const info = $("#pr-hs-info");
  if (hs.available === false) info.textContent = t("needs NetworkManager (Raspberry Pi OS Bookworm or newer)");
  else if (hs.busy) info.textContent = t("switching …");
  else if (hs.on) info.textContent = t("on") + " · «" + hs.ssid + "» · " + t("password") + " " + (hc.password || "–") + " · " + hs.clients + " "
    + (hs.clients === 1 ? t("device") : t("devices")) + " · " + (hc.address || "");
  else info.textContent = t("off") + " · " + t("name") + " «" + (hc.ssid || "") + "» · " + t("password") + " " + (hc.password || "–");
  $("#pr-err").textContent = hs.msg ? "⚠ " + hs.msg : "";
  $("#pr-time").textContent = s.time_status ? t("Clock") + ": " + tlTxt(s.time_status) : "";
}
async function prAutostart(on) {
  PR.asUntil = Date.now() + 3000;
  const r = await post("/api/autostart", {on: on, lang: LANG});
  if (r && r.autostart) window.__autostart = r.autostart;
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); $("#pr-as").checked = !on; }
  else { $("#pr-err").textContent = r.autostart && r.autostart.msg ? "⚠ " + r.autostart.msg : ""; toast(on ? "🔁 " + t("Autostart on") : t("Autostart off")); }
}
const NETTXT = () => ({"off": "", "needs NetworkManager": t("needs NetworkManager (Raspberry Pi OS Bookworm or newer)"),
  "paused (switched by hand)": t("automatic paused (switched by hand) - choose «Automatic» again to resume"),
  "own Wi-Fi on": t("own Wi-Fi on"), "searching known networks …": t("searching known networks …"),
  "own Wi-Fi on - search postponed (a device is connected)": t("own Wi-Fi on - search postponed (a device is connected)")});
function netTxt(x) {
  if (!x) return "";
  let m = /^connected with «(.*)»$/.exec(x); if (m) return "✓ " + t("connected with") + " «" + m[1] + "»";
  m = /^no known network - own Wi-Fi in (\d+) s$/.exec(x); if (m) return t("no known network - own Wi-Fi in") + " " + m[1] + " s";
  m = /^own Wi-Fi on - next search in (\d+) min$/.exec(x); if (m) return t("own Wi-Fi on - next search for known networks in") + " " + m[1] + " min";
  return NETTXT()[x] !== undefined ? NETTXT()[x] : x;
}
function updateAutostart(s) {
  const a = s.autostart || {}, i = $("#pr-as-info"); if (!i) return;
  if (!(Date.now() < (PR.asUntil || 0))) $("#pr-as").checked = !!a.on;
  const mode = s.net_mode || "auto";
  if (document.activeElement !== $("#pr-net") && !(Date.now() < (PR.netUntil || 0))) $("#pr-net").value = mode;
  const what = {auto: t("tries the known networks (phone hotspot), otherwise switches the own Wi-Fi on"),
                hotspot: t("switches the own Wi-Fi on"), client: t("joins the known networks")}[mode];
  i.textContent = a.on ? t("on: when the Pi boots, Motion Watch starts by itself and") + " " + what
                       : t("off: nothing starts at boot, the Pi joins its known networks");
  $("#pr-net-info").textContent = netTxt(s.netauto);
}
$("#pr-net").onchange = async e => {
  PR.netUntil = Date.now() + 3000;
  const r = await post("/api/text", {key: "net_mode", value: e.target.value, lang: LANG});
  if (r.ok) toast(t("Saved")); else $("#pr-err").textContent = "⚠ " + (r.error || "error");
};
$("#pr-as").onchange = e => prAutostart(e.target.checked);
$("#pr-arm").onclick = () => prArm("arm");
$("#pr-armnow").onclick = () => prArm("arm_now");
$("#pr-disarm").onclick = () => prArm("disarm");
$("#pr-camp").onchange = e => prCamp(e.target.checked);
$("#pr-hs").onchange = e => prHotspot(e.target.checked);
$("#b-arm").addEventListener("click", () => { const s = window.__lastState || {}; prArm(s.arm_state === "disarmed" ? "arm" : "disarm"); });

function drawWifi(hist) {
  const c = $("#wifi-spark"); if (!c) return;
  const g = c.getContext("2d"), w = c.width, h = c.height, N = 150;
  const TOP = -35, BOT = -95, y = d => 2 + (h - 4) * (TOP - Math.max(BOT, Math.min(TOP, d))) / (TOP - BOT);
  const col = d => d >= -65 ? "#3fb950" : (d >= -75 ? "#d29922" : "#ff3b3b");
  g.clearRect(0, 0, w, h);
  g.font = "9px system-ui, sans-serif"; g.textAlign = "right";
  [[-65, "#3fb950", "bottom", -1], [-75, "#d29922", "top", 1]].forEach(([d, cl, base, dy]) => {
    g.strokeStyle = THEME === "light" ? "#d0d7e2" : "#1f2a38"; g.lineWidth = 1; g.setLineDash([3, 3]);
    g.beginPath(); g.moveTo(0, y(d)); g.lineTo(w, y(d)); g.stroke(); g.setLineDash([]);
    g.textBaseline = base; g.fillStyle = cl; g.globalAlpha = 0.8; g.fillText(d + " dBm", w - 3, y(d) + dy); g.globalAlpha = 1;
  });
  g.textAlign = "left";
  if (!hist || !hist.length) return;
  const x = i => w - (hist.length - 1 - i) * (w / (N - 1));
  g.lineWidth = 2;
  for (let i = 1; i < hist.length; i++) {
    const a = hist[i - 1], b = hist[i];
    if (a == null || b == null) continue;
    g.strokeStyle = col(Math.min(a, b)); g.beginPath(); g.moveTo(x(i - 1), y(a)); g.lineTo(x(i), y(b)); g.stroke();
  }
  hist.forEach((d, i) => {
    if (d == null) { g.fillStyle = "#ff3b3b"; g.fillRect(x(i) - 1, h - 6, 2.5, 6); }                 // no connection
    else if ((i === 0 || hist[i - 1] == null) && (i === hist.length - 1 || hist[i + 1] == null)) { g.fillStyle = col(d); g.beginPath(); g.arc(x(i), y(d), 2, 0, 7); g.fill(); }
  });
}
function wifiStats(hist) {
  const v = (hist || []).filter(d => d != null);
  let drops = 0; (hist || []).forEach((d, i) => { if (d == null && (i === 0 || hist[i - 1] != null)) drops++; });
  const mins = Math.max(1, Math.round((hist || []).length * 2 / 60));
  let txt = t("Wi-Fi signal, last") + " " + mins + " " + t("min");
  if (v.length) txt += " · Ø " + Math.round(v.reduce((a, b) => a + b, 0) / v.length) + " dBm · " + t("weakest") + " " + Math.min(...v) + " dBm";
  txt += " · " + (drops ? drops + " " + (drops === 1 ? t("drop-out") : t("drop-outs")) : t("no drop-outs"));
  return txt;
}
function updateWifi(s) {
  const w = s.wifi, n = s.net || {}, b = $("#b-wifi"), box = $("#wifi-box");
  if (!b) return;
  if (!w) { b.hidden = true; box.hidden = true; return; }
  if (w.ap) {                                        // the Pi is the access point: show that instead of a signal
    const hs = s.hotspot || {};
    b.hidden = HIDDEN.has("b-wifi"); box.hidden = true;
    b.textContent = "📡 " + t("Own Wi-Fi") + " · " + (hs.clients || 0) + " " + ((hs.clients === 1) ? t("device") : t("devices"));
    b.className = "badge grn" + (HIDDEN.has("b-wifi") ? " vh" : ""); b.title = "«" + (hs.ssid || "") + "» · " + (hs.ip || "");
    return;
  }
  b.hidden = HIDDEN.has("b-wifi"); box.hidden = false;
  drawWifi(s.wifi_hist); $("#wifi-stat").textContent = wifiStats(s.wifi_hist);
  const bars = !w.connected ? 0 : (w.pct >= 75 ? 4 : w.pct >= 50 ? 3 : w.pct >= 25 ? 2 : 1);
  const cls = !w.connected ? "red" : (w.dbm >= -65 ? "grn" : (w.dbm >= -75 ? "yel" : "red"));
  const wb = el("span", "wbars"); for (let i = 1; i <= 4; i++) wb.appendChild(el("i", i <= bars ? "on" : ""));
  b.textContent = ""; b.append(wb, document.createTextNode(w.connected ? w.dbm + " dBm" : t("no Wi-Fi")));
  if (n.online === false && w.connected) b.append(document.createTextNode(" · " + t("no internet")));
  b.className = "badge " + (n.online === false ? "red" : cls) + (HIDDEN.has("b-wifi") ? " vh" : "");
  b.title = (w.ssid ? w.ssid + " · " : "") + w.iface + (w.rate ? " · " + w.rate : "");
  $("#wifi-big").textContent = w.connected ? w.pct + " %" : t("no Wi-Fi");
  $("#wifi-name").textContent = t("Wi-Fi") + (w.ssid ? " «" + w.ssid + "»" : "") + " · " + w.iface;
  const bar = $("#wifi-bar"); bar.style.width = (w.connected ? w.pct : 0) + "%";
  bar.style.background = cls === "grn" ? "#3fb950" : (cls === "yel" ? "#d29922" : "#ff3b3b");
  $("#wifi-info").textContent = (w.connected ? w.dbm + " dBm" + (w.rate ? " · " + w.rate : "") : t("not connected")) + " · " + t("Internet") + ": "
    + (n.online === true ? t("online") + (n.ms != null ? " (" + n.ms + " ms)" : "") : (n.online === false ? t("offline") : "…"));
}
function updateExtras(s) {
  updateWifi(s);
  const a = $("#tl-status"); if (a) a.textContent = tlTxt(s.timelapse);
  const r = $("#tl-render"); if (r) r.textContent = tlTxt(s.timelapse_render);
  if (s.timelapse_last !== tlSeen) { if (tlSeen !== null) tlLoad(); tlSeen = s.timelapse_last; }
  if ((s.timelapse_render || "").startsWith("video ready") && r && !r.dataset.done) { r.dataset.done = "1"; tlLoad(); }
  if (!(s.timelapse_render || "").startsWith("video ready") && r) delete r.dataset.done;
  const h = $("#th-status"); if (h) h.textContent = tlTxt(s.thermal) + (s.thermal === "connected" && s.thermal_res ? " · " + s.thermal_res : "");
}

function drawSpark(hist) {
  const c = $("#cpu-spark"), g = c.getContext("2d"), w = c.width, h = c.height;
  g.clearRect(0, 0, w, h);
  g.strokeStyle = THEME === "light" ? "#d0d7e2" : "#1f2a38"; g.lineWidth = 1;
  [25, 50, 75].forEach(p => { const y = h - h * p / 100; g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); });
  if (!hist || hist.length < 2) return;
  const last = hist[hist.length - 1];
  g.strokeStyle = last < 60 ? "#3fb950" : (last < 85 ? "#d29922" : "#ff3b3b");
  g.lineWidth = 2; g.beginPath();
  hist.forEach((v, i) => {
    const x = w - (hist.length - 1 - i) * (w / 59), y = h - 2 - (h - 4) * v / 100;
    i ? g.lineTo(x, y) : g.moveTo(x, y);
  });
  g.stroke();
}

async function refresh() {
  let j;
  try { j = await (await fetch("/api/state")).json(); }
  catch (e) { badge("#b-conn", t("Pi not reachable"), "red"); return; }
  badge("#b-conn", t("Pi connected"), "grn");
  const s = j.state, c = j.cfg, rel = j.relays || [], rs = s.relay_states || [];
  badge("#b-person", s.persons ? s.persons + " " + (s.persons > 1 ? t("PERSONS DETECTED") : t("PERSON DETECTED")) : t("No person"), s.persons ? "red" : "");
  badge("#b-obj", s.objects + " " + (s.objects === 1 ? t("object") : t("objects")), s.objects ? "org" : "");
  badge("#b-rain", s.rain_mode ? t("RAIN MODE") : t("No rain"), s.rain_mode ? "blu" : "");
  badge("#b-wind", t("Wind") + ": " + t(s.wind_level), (s.wind_level !== "calm" && s.wind_level !== "off") ? "yel" : "");
  badge("#b-rec", s.recording ? "● " + t("REC") : t("Idle"), s.recording ? "red" : "");
  const on = rs.filter(Boolean).length;
  badge("#b-relay", t("Relays") + ": " + on + "/" + rel.length, on ? "grn" : "");
  badge("#b-light", s.lowlight ? t("LOW LIGHT") : t("Light ok") + " (" + s.brightness + ")", s.lowlight ? "yel" : "");
  $("#sys-info").textContent = t("Settings") + ": " + s.settings_status + " · " + t("recordings") + ": " + s.rec_dir_mb + " MB · " + t("viewers") + ": " + s.web_viewers
      + (s.notify_status !== "off" ? " · " + t("notify") + ": " + s.notify_status : "");
  $("#s-fps").textContent = s.fps; $("#s-persons").textContent = s.persons;
  $("#s-objects").textContent = s.objects; $("#s-det").textContent = s.detections_total;
  $("#obj-list").textContent = s.object_summary ? t("Objects") + ": " + s.object_summary : "";
  $("#v-pan").textContent = Math.round(c.pan); $("#v-tilt").textContent = Math.round(c.tilt);
  showPos(c.pan, c.tilt);
  $("#patrol-st").textContent = (s.manual ? t("Manual control - tracking / patrol paused") : s.tracking ? t("Tracking person")
      : (c.patrol ? t("Patrol") + ": " + s.patrol_status : "")) + (j.waypoints.length ? " · " + t("waypoints") + ": " + j.waypoints.map(Math.round).join(", ") : "");
  renderRelays(rel, rs, c.ai_enabled && !/no model|error/.test(s.ai_status));
  const ssrc = s.source_status || "";
  badge("#b-src", t("Source") + ": " + (s.source_label || "–").slice(0, 26), ssrc === "connected" ? "grn" : (ssrc.startsWith("failed") ? "red" : "yel"));
  badge("#b-sched", t("Schedule") + ": " + ((s.sched_active || []).length ? s.sched_active.join(", ") : "–"), (s.sched_active || []).length ? "blu" : "");
  renderSourceStatus(s);
  if (s.source_id !== lastSrcId) { lastSrcId = s.source_id; loadSources(false); }
  renderSchedules(j.schedules || [], s);
  $("#v-rec").hidden = !s.recording; $("#v-src").hidden = !s.source_label; $("#v-src").textContent = s.source_label || "";
  $("#b-sec").hidden = !s.web_open;
  updateExtras(s); updateProtect(s); updateAutostart(s);
  badge("#b-pres", t("Presence") + ": " + t(s.presence || "unknown"), s.presence === "home" ? "grn" : (s.presence === "away" ? "org" : ""));
  $("#b-pres").hidden = !(s.presence === "home" || s.presence === "away") || HIDDEN.has("b-pres");

  if (typeof s.fps === "number") badge("#b-fps", Math.round(s.fps) + " FPS", s.fps >= 12 ? "grn" : (s.fps >= 6 ? "yel" : "red"));
  if (s.cpu === null || s.cpu === undefined) {
    badge("#b-cpu", "CPU n/a", ""); $("#cpu-big").textContent = "n/a";
  } else {
    const cls = s.cpu < 60 ? "grn" : (s.cpu < 85 ? "yel" : "red");
    const tp = s.cpu_temp;
    const tcls = tp == null ? "" : (tp >= 80 ? "red" : (tp >= 70 ? "yel" : "grn"));
    const worst = [cls, tcls].includes("red") ? "red" : ([cls, tcls].includes("yel") ? "yel" : cls);
    badge("#b-cpu", "CPU " + Math.round(s.cpu) + "%" + (tp != null ? " · " + Math.round(tp) + " °C" : ""), worst);
    $("#cpu-big").textContent = s.cpu.toFixed(0) + " %";
    const bar = $("#cpu-bar"); bar.style.width = s.cpu + "%";
    bar.style.background = s.cpu < 60 ? "#3fb950" : (s.cpu < 85 ? "#d29922" : "#ff3b3b");
    $("#cpu-info").textContent = (s.cpu_temp != null ? s.cpu_temp.toFixed(1) + " °C · " : "") + s.cpu_count + " " + t("cores");
  }
  drawSpark(s.cpu_hist);

  for (const k in ctrl) {
    if (k === editing || !(k in c)) continue;
    const x = ctrl[k];
    if (x.type === "bool") x.input.checked = !!c[k];
    else if (document.activeElement !== x.input) { x.input.value = c[k]; x.val.textContent = Math.round(c[k] * 100) / 100; }
  }
  const log = $("#log"); log.textContent = "";
  j.events.forEach(e => { log.append(el("span", "t", e.t + "  "), document.createTextNode(e.text + "\n")); });
}

let hold = null;
document.querySelectorAll("button.dp").forEach(b => {
  const stop = () => { clearInterval(hold); hold = null; };
  b.addEventListener("pointerdown", e => {
    e.preventDefault(); move(b.dataset.dir);
    if (b.dataset.dir !== "center") hold = setInterval(() => move(b.dataset.dir), 160);
  });
  ["pointerup", "pointerleave", "pointercancel"].forEach(ev => b.addEventListener(ev, stop));
});
// ---- joystick: deflection is sent ~10x per second, the server moves the camera proportionally ----
(function () {
  const pad = $("#stick"), knob = $("#knob");
  let id = null, vx = 0, vy = 0, timer = null, busy = false;
  const radius = () => pad.clientWidth / 2 - knob.clientWidth / 2;
  function show(px, py) { knob.style.transform = "translate(" + px + "px," + py + "px)"; }
  function send() {
    if (busy) return;
    busy = true;
    post("/api/stick", {x: vx, y: vy, speed: parseFloat($("#stick-speed").value)}).then(r => { busy = false; if (r && r.ok) showPos(r.pan, r.tilt); });
  }
  function track(e) {
    const b = pad.getBoundingClientRect(), R = radius();
    let dx = e.clientX - (b.left + b.width / 2), dy = e.clientY - (b.top + b.height / 2);
    const m = Math.hypot(dx, dy);
    if (m > R) { dx *= R / m; dy *= R / m; }
    show(dx, dy);
    vx = Math.round(dx / R * 1000) / 1000; vy = Math.round(-dy / R * 1000) / 1000;      // up is positive
  }
  function release() {
    if (id === null) return;
    id = null; vx = vy = 0; clearInterval(timer); timer = null;
    pad.classList.remove("on"); show(0, 0);
    busy = false; send();                                       // tell the server the stick is back in the middle
  }
  pad.addEventListener("pointerdown", e => {
    if (id !== null) return;
    e.preventDefault(); id = e.pointerId; pad.setPointerCapture(id);
    pad.classList.add("on"); track(e); busy = false; send();
    timer = setInterval(send, 100);
  });
  pad.addEventListener("pointermove", e => { if (e.pointerId === id) { e.preventDefault(); track(e); } });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach(ev => pad.addEventListener(ev, e => { if (e.pointerId === id) release(); }));
  addEventListener("blur", release);
  document.addEventListener("visibilitychange", () => { if (document.hidden) release(); });
  pad.addEventListener("contextmenu", e => e.preventDefault());
  $("#stick-center").addEventListener("click", () => move("center"));
  try { const s = localStorage.getItem("mw-stick-speed"); if (s) $("#stick-speed").value = s; } catch (e) {}
  $("#stick-speed").addEventListener("change", e => { try { localStorage.setItem("mw-stick-speed", e.target.value); } catch (x) {} });
  function mode(padmode) {
    document.body.classList.toggle("padmode", padmode);
    $("#m-stick").className = padmode ? "" : "sel-auto"; $("#m-pad").className = padmode ? "sel-auto" : "";
    try { localStorage.setItem("mw-ctl", padmode ? "pad" : "stick"); } catch (e) {}
  }
  $("#m-stick").addEventListener("click", () => mode(false));
  $("#m-pad").addEventListener("click", () => mode(true));
  let saved = ""; try { saved = localStorage.getItem("mw-ctl") || ""; } catch (e) {}
  mode(saved === "pad");
})();

// ---- phone: stick directly under the picture (portrait) or right next to it (landscape) ----
(function () {
  const left = $("#ctl-left"), home = left.parentNode, slot = $("#mctl");
  const allb = $("#allbtns"), allHome = allb.parentNode, mb = $("#mbtns");
  const mqPhone = matchMedia("(max-width: 760px), (max-height: 520px) and (orientation: landscape)");
  const mqLand = matchMedia("(orientation: landscape) and (max-height: 520px)");
  let was = null;
  function place() {
    const phone = mqPhone.matches, land = phone && mqLand.matches;
    if (phone && left.parentNode !== slot) slot.appendChild(left);
    if (!phone && left.parentNode !== home) home.insertBefore(left, home.firstChild);
    const target = land ? mb : $("#mbtns2");                                        // portrait: between picture card and "Controls"
    if (phone && allb.parentNode !== target) target.appendChild(allb);
    if (!phone && allb.parentNode !== allHome) allHome.insertBefore(allb, allHome.firstChild);
    document.body.classList.toggle("mobctl", phone); document.body.classList.toggle("mobland", land);
    if (land && was !== "land") setTimeout(() => $("#vcard").scrollIntoView({block: "start"}), 50);   // picture + stick fill the screen
    was = land ? "land" : (phone ? "phone" : "desk");
  }
  [mqPhone, mqLand].forEach(m => m.addEventListener ? m.addEventListener("change", place) : m.addListener(place));
  place();
})();

const KEYS = {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Home: "center"};
addEventListener("keydown", e => {
  if (e.key === "F11") { e.preventDefault(); toggleFullscreen(); return; }
  if (KEYS[e.key] && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); move(KEYS[e.key]); }
});

// remember which cards are open (per browser)
function secKey(d) { return "mw-open:" + (d.dataset.view || d.querySelector("summary").textContent); }
function initSections() {
  document.querySelectorAll("details.card, details.sub:not(.inline), details.adv").forEach(d => {
    try { const v = localStorage.getItem(secKey(d)); if (v !== null) d.open = (v === "1"); } catch (e) {}
    d.addEventListener("toggle", () => { try { localStorage.setItem(secKey(d), d.open ? "1" : "0"); } catch (e) {} });
  });
}
function allSections(open) { document.querySelectorAll("details.card, details.sub:not(.inline)").forEach(d => { if (d.open !== open) d.open = open; }); }

$("#video").addEventListener("dblclick", () => {
  videoOnly = !videoOnly; document.body.classList.toggle("videoonly", videoOnly);
  if (videoOnly && !document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
  if (!videoOnly && document.fullscreenElement) document.exitFullscreen();
});
document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement && videoOnly) { videoOnly = false; document.body.classList.remove("videoonly"); }
});
(async () => {
  applyHidden();
  if (!LANG || !THEME) {
    try { const a = await (await fetch("/api/appearance")).json(); LANG = LANG || a.lang; THEME = THEME || a.theme; }
    catch (e) { LANG = LANG || "en"; THEME = THEME || "dark"; }
  }
  applyTheme(); applyI18n();
  await build(); regroup(); applyHidden(); initSections(); refresh(); setInterval(refresh, 700);
})();
/*ALERTS*/
</script></body></html>
"""


REC_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch - Recordings</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1600px;margin:0 auto}
.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px 16px;align-items:end}
.filters label,.flab{display:block;font-size:11px;font-weight:700;letter-spacing:.08em;color:var(--mut);text-transform:uppercase;margin-bottom:4px}
.filters select,.filters input[type=text],.filters input[type=date]{width:100%}
.dates{display:flex;gap:6px}
.quick{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.quick button{padding:3px 10px;font-size:12px}
.seg{width:100%}.seg button{flex:1;padding:6px 10px;font-size:13px}
.seg button.sel{background:var(--acc);color:#fff}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.bar .sp{flex:1}
button.favf.on{background:var(--yel);color:#fff;border-color:var(--yel)}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.rc{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;position:relative;box-shadow:var(--shadow);transition:transform .12s,border-color .12s}
.rc:hover{border-color:var(--acc);transform:translateY(-2px)}
.rc.sel{outline:2px solid var(--acc)}
.th{position:relative;aspect-ratio:16/9;background:#000;display:flex;align-items:center;justify-content:center;color:var(--mut);font-size:30px}
.th img{width:100%;height:100%;object-fit:cover;display:block}
.th .play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .15s;background:rgba(0,0,0,.28);color:#fff;font-size:38px}
.rc:hover .play{opacity:1}
.tag{position:absolute;left:8px;bottom:8px;background:rgba(0,0,0,.72);color:#fff;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:700}
.tag.live{background:var(--red)}
.star{position:absolute;right:8px;top:6px;font-size:22px;line-height:1;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8);cursor:pointer;background:none;border:0;padding:0}
.star.on{color:var(--yel)}
.chk{position:absolute;left:8px;top:8px;width:20px;height:20px;display:none}
body.selecting .chk{display:block}
.rb{padding:9px 11px}
.rb b{display:block;font-size:13px}
.chips{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}
.chip{font-size:11px;border:1px solid var(--blu);border-radius:99px;padding:0 8px;color:var(--blu)}
.empty{padding:40px;text-align:center;color:var(--mut)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:50;display:flex;align-items:center;justify-content:center;padding:12px}
.modal[hidden]{display:none}
.mbox{background:var(--panel);border:1px solid var(--line);border-radius:14px;max-width:1100px;width:100%;max-height:100%;display:flex;flex-direction:column;overflow:hidden}
.mhead{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:8px 12px;border-bottom:1px solid var(--line)}
.mhead .sp{flex:1}
#m-body{background:#000;display:flex;align-items:center;justify-content:center;min-height:200px;overflow:auto}
#m-body video,#m-body img{max-width:100%;max-height:72vh;display:block}
#m-note{padding:8px 12px;min-height:30px}
/* statistics */
.stats{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}
@media(max-width:900px){.stats{grid-template-columns:1fr}}
.stats h4{margin:0 0 8px;font-size:11px;letter-spacing:.08em;color:var(--mut);text-transform:uppercase}
.heat{display:grid;grid-template-columns:22px repeat(24,minmax(0,1fr));gap:2px;align-items:center}
.heat .hl{font-size:10px;color:var(--mut)}
.heat .c{aspect-ratio:1;border-radius:3px;background:var(--field);border:1px solid var(--line)}
.dbars{display:flex;align-items:flex-end;gap:5px;height:88px}
.dbars .d{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;cursor:pointer;min-width:0}
.dbars .d i{display:block;width:100%;background:var(--acc);border-radius:4px 4px 0 0;min-height:2px;opacity:.75}
.dbars .d.on i{opacity:1;background:var(--yel)}
.dbars .d small{font-size:10px;color:var(--mut);margin-top:3px}
.tl{position:relative;height:38px;background:var(--field);border:1px solid var(--line);border-radius:8px;margin-top:6px}
.tl .m{position:absolute;top:5px;bottom:5px;width:5px;margin-left:-2px;border-radius:3px;background:var(--acc);cursor:pointer}
.tl .m.image{background:var(--mut)}
.tl .m:hover{background:var(--yel)}
.tl .tk{position:absolute;top:100%;font-size:10px;color:var(--mut);transform:translateX(-50%);margin-top:2px}
</style></head><body>
<header>
  <h1>Motion Watch</h1>
  <!--NAV-->
  <span class="badge" id="b-count">–</span>
  <span class="badge" id="b-disk">–</span>
  <span class="badge red" id="b-live" hidden>● REC</span>
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <details class="card" id="statcard">
    <summary data-i18n="Statistics">Statistics</summary>
    <div class="stats">
      <div><h4 data-i18n="Events per weekday and hour">Events per weekday and hour</h4><div class="heat" id="heat"></div></div>
      <div><h4 data-i18n="Last 14 days (click a day)">Last 14 days (click a day)</h4><div class="dbars" id="dbars"></div>
        <h4 style="margin-top:16px" id="tl-title"></h4><div class="tl" id="tl"></div><div style="height:16px"></div></div>
    </div>
  </details>
  <section class="card filters">
    <div>
      <span class="flab" data-i18n="Date">Date</span>
      <div class="dates"><input type="date" id="f-from" aria-label="from"><input type="date" id="f-to" aria-label="to"></div>
      <div class="quick">
        <button class="sec" data-q="all" data-i18n="All time">All time</button>
        <button class="sec" data-q="today" data-i18n="Today">Today</button>
        <button class="sec" data-q="yday" data-i18n="Yesterday">Yesterday</button>
        <button class="sec" data-q="week" data-i18n="Last 7 days">Last 7 days</button>
      </div>
    </div>
    <div>
      <span class="flab" data-i18n="Type">Type</span>
      <div class="seg" id="f-kind">
        <button data-kind="" data-i18n="All">All</button><button data-kind="video" data-i18n="Videos">Videos</button><button data-kind="image" data-i18n="Images">Images</button>
      </div>
    </div>
    <div id="w-sched"><label for="f-sched" data-i18n="Schedule">Schedule</label><select id="f-sched"></select></div>
    <div id="w-src"><label for="f-src" data-i18n="Video source">Video source</label><select id="f-src"></select></div>
    <div><label for="f-q" data-i18n="Search">Search</label><input type="text" id="f-q" placeholder="person_2026…"></div>
    <div><label for="f-sort" data-i18n="Sort">Sort</label>
      <select id="f-sort"><option value="new" data-i18n="Newest first">Newest first</option><option value="old" data-i18n="Oldest first">Oldest first</option><option value="size" data-i18n="Largest first">Largest first</option></select></div>
  </section>
  <div class="bar">
    <span class="mut" id="result-info"></span><span class="sp"></span>
    <button class="sec favf" id="btn-fav">★ <span data-i18n="Favorites">Favorites</span></button>
    <button class="sec" id="btn-reset" data-i18n="Reset filters">Reset filters</button>
    <button class="sec" id="btn-refresh" data-i18n="Refresh">Refresh</button>
    <button class="sec" id="btn-select" data-i18n="Select">Select</button>
    <button class="sec" id="btn-starsel" hidden></button>
    <button class="sec" id="btn-zipsel" hidden></button>
    <button class="red" id="btn-delsel" hidden></button>
  </div>
  <div id="grid"></div>
  <div class="empty" id="empty" hidden data-i18n="No recordings match the filters">No recordings match the filters</div>
  <div style="text-align:center;margin:14px"><button class="sec" id="more" hidden data-i18n="Load more">Load more</button></div>
</main>
<div class="modal" id="modal" hidden>
  <div class="mbox">
    <div class="mhead">
      <b id="m-title"></b><span class="mut" id="m-meta"></span><span class="sp"></span>
      <button class="sec" id="m-prev" title="←">&#8249;</button><button class="sec" id="m-next" title="→">&#8250;</button>
      <button class="sec" id="m-fav" title="★">☆</button>
      <a class="btn sec" id="m-dl" download data-i18n="Download">Download</a>
      <button class="red" id="m-del" data-i18n="Delete">Delete</button>
      <button class="sec" id="m-close">&#10005;</button>
    </div>
    <div id="m-body"></div>
    <div class="mut" id="m-note"></div>
  </div>
</div>
<form id="zipform" method="post" action="/rec/zip" hidden><input type="hidden" name="names" id="zipnames"></form>
<script>
/*COMMON*/
Object.assign(I18N.de, {
  "Date": "Datum", "All time": "Gesamter Zeitraum", "Today": "Heute", "Yesterday": "Gestern", "Last 7 days": "Letzte 7 Tage", "Type": "Typ", "All": "Alle", "Videos": "Videos",
  "Images": "Bilder", "Schedule": "Zeitplan", "Video source": "Videoquelle", "Search": "Suche", "Sort": "Sortierung",
  "Newest first": "Neueste zuerst", "Oldest first": "Älteste zuerst", "Largest first": "Größte zuerst",
  "Reset filters": "Filter zurücksetzen", "Refresh": "Aktualisieren", "Select": "Auswählen", "Cancel selection": "Auswahl beenden",
  "Delete selected": "Auswahl löschen", "Load more": "Mehr laden", "No recordings match the filters": "Keine Aufnahmen passen zu den Filtern",
  "Download": "Herunterladen", "Delete": "Löschen", "Inside any schedule": "In irgendeinem Zeitplan",
  "Outside all schedules": "Außerhalb aller Zeitpläne", "All sources": "Alle Quellen", "off": "aus", "every day": "täglich",
  "recordings": "Aufnahmen", "shown": "angezeigt", "persons": "Personen", "Preparing video…": "Video wird vorbereitet …",
  "Converting for the browser (one time)…": "Wird für den Browser umgewandelt (einmalig) …",
  "This video uses a codec browsers cannot play. Install ffmpeg on the Pi (sudo apt install ffmpeg) or download the file.":
    "Dieses Video nutzt einen Codec, den Browser nicht abspielen. Installiere ffmpeg auf dem Pi (sudo apt install ffmpeg) oder lade die Datei herunter.",
  "Still recording - available when it ends.": "Aufnahme läuft noch - danach verfügbar.", "Error": "Fehler",
  "Delete this recording?": "Diese Aufnahme löschen?", "recordings?": "Aufnahmen löschen?", "Image": "Bild", "Video": "Video",
  "Statistics": "Statistik", "Events per weekday and hour": "Ereignisse pro Wochentag und Stunde", "Last 14 days (click a day)": "Letzte 14 Tage (Tag anklicken)",
  "Favorites": "Favoriten", "Protect selected": "Auswahl schützen", "Download ZIP": "ZIP laden", "events": "Ereignisse", "Timeline": "Zeitleiste",
  "Favorites are never deleted by the automatic cleanup": "Favoriten werden vom automatischen Aufräumen nie gelöscht"
});
const DAYN = () => LANG === "de" ? ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"] : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const pad = n => String(n).padStart(2, "0");
const ymd = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
function fmtSize(b) { return b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(0) + " KB" : b < 1073741824 ? (b / 1048576).toFixed(1) + " MB" : (b / 1073741824).toFixed(2) + " GB"; }
function fmtDur(s) { if (s === null || s === undefined) return ""; s = Math.round(s); return Math.floor(s / 60) + ":" + pad(s % 60); }
function fmtDays(days) {
  const N = DAYN();
  if (days.length === 7) return t("every day");
  if (days.join() === "0,1,2,3,4") return N[0] + "–" + N[4];
  return days.map(d => N[d]).join(", ") || "–";
}

const F = {from: "", to: "", kind: "", schedule: "", source: "", q: "", sort: "new", fav: ""};
let items = [], DATA = null, reqId = 0, selecting = false, modalIdx = -1, modalToken = 0, openAfter = null, tlDay = "";
const selected = new Set();

async function load(reset) {
  const my = ++reqId, p = new URLSearchParams();
  Object.entries(F).forEach(([k, v]) => { if (v) p.set(k, v); });
  p.set("offset", reset ? 0 : items.length); p.set("limit", 48);
  let j;
  try { j = await (await fetch("/api/recordings?" + p)).json(); } catch (e) { return; }
  if (my !== reqId) return;                           // a newer request is on its way
  DATA = j;
  const grid = $("#grid");
  if (reset) { items = []; grid.textContent = ""; selected.clear(); updateSelBtn(); }
  j.items.forEach(it => { items.push(it); grid.appendChild(card(it)); });
  $("#b-count").textContent = j.disk.files + " " + t("recordings");
  $("#b-disk").textContent = j.disk.mb + " MB / " + j.disk.limit_gb + " GB";
  $("#b-live").hidden = !j.recording;
  $("#result-info").textContent = items.length + " / " + j.total + " " + t("shown");
  $("#empty").hidden = items.length > 0; $("#more").hidden = items.length >= j.total;
  fillOptions(j);
  if (openAfter && items.length) { const n = openAfter; openAfter = null; const i = items.findIndex(x => x.name === n); openAt(i >= 0 ? i : 0); }
}

function fillOptions(j) {
  const ss = $("#f-sched"), cur = F.schedule;
  $("#w-sched").hidden = !j.schedules.length;
  ss.textContent = "";
  const add = (v, label) => { const o = el("option", "", label); o.value = v; ss.appendChild(o); };
  add("", t("All") + " (" + j.counts.all + ")");
  add("any", t("Inside any schedule") + " (" + j.counts.any + ")");
  add("none", t("Outside all schedules") + " (" + j.counts.none + ")");
  j.schedules.forEach(s => add(String(s.index), (s.active_now ? "● " : "") + s.name + " · " + s.start + "–" + s.end + " · " + fmtDays(s.days)
      + " (" + s.count + ")" + (s.enabled ? "" : " [" + t("off") + "]")));
  ss.value = cur; if (ss.value !== cur) { F.schedule = ""; ss.value = ""; }
  const sr = $("#f-src"), cs = F.source; sr.textContent = "";
  const a0 = el("option", "", t("All sources")); a0.value = ""; sr.appendChild(a0);
  j.sources.forEach(n => { const o = el("option", "", n); o.value = n; sr.appendChild(o); });
  sr.value = cs; if (sr.value !== cs) { F.source = ""; sr.value = ""; }
  $("#w-src").hidden = !j.sources.length;
}

function card(it) {
  const c = el("div", "rc"); c.dataset.name = it.name;
  const th = el("div", "th");
  const img = el("img"); img.loading = "lazy"; img.alt = "";
  img.src = "/rec/thumb/" + encodeURIComponent(it.name);
  img.onerror = () => { img.remove(); th.insertBefore(document.createTextNode(it.kind === "video" ? "▶" : "🖼"), th.firstChild); };
  th.appendChild(img);
  if (it.kind === "video") th.appendChild(el("div", "play", "▶"));
  th.appendChild(el("span", "tag" + (it.recording ? " live" : ""), it.recording ? "● REC" : it.kind === "video" ? "▶ " + fmtDur(it.duration) : t("Image")));
  const st = el("button", "star" + (it.fav ? " on" : ""), it.fav ? "★" : "☆"); st.title = t("Favorites are never deleted by the automatic cleanup");
  st.onclick = async e => { e.stopPropagation(); await setFav([it.name], !it.fav); it.fav = !it.fav; st.className = "star" + (it.fav ? " on" : ""); st.textContent = it.fav ? "★" : "☆"; };
  const cb = el("input", "chk"); cb.type = "checkbox"; cb.onclick = e => e.stopPropagation();
  cb.onchange = () => toggleSel(it.name, cb.checked, c);
  th.append(cb, st);
  const body = el("div", "rb");
  body.appendChild(el("b", "", it.time));
  body.appendChild(el("div", "mut", [fmtSize(it.size), it.persons ? it.persons + " " + t("persons") : "", it.source || ""].filter(Boolean).join(" · ")));
  if (it.schedules.length) { const ch = el("div", "chips"); it.schedules.forEach(n => ch.appendChild(el("span", "chip", n))); body.appendChild(ch); }
  c.append(th, body);
  c.onclick = () => { if (selecting) { cb.checked = !cb.checked; toggleSel(it.name, cb.checked, c); } else openAt(items.indexOf(it)); };
  return c;
}
async function setFav(names, value) { const r = await post("/api/rec/fav", {names: names, value: value}); return r; }

function toggleSel(name, on, c) { on ? selected.add(name) : selected.delete(name); c.classList.toggle("sel", on); updateSelBtn(); }
function updateSelBtn() {
  const n = selected.size;
  const d = $("#btn-delsel"), z = $("#btn-zipsel"), s = $("#btn-starsel");
  d.hidden = z.hidden = s.hidden = !selecting;
  d.textContent = t("Delete selected") + " (" + n + ")"; z.textContent = t("Download ZIP") + " (" + n + ")"; s.textContent = "★ " + t("Protect selected") + " (" + n + ")";
  d.disabled = z.disabled = s.disabled = !n;
}
function setSelecting(on) {
  selecting = on; document.body.classList.toggle("selecting", on);
  $("#btn-select").textContent = on ? t("Cancel selection") : t("Select");
  if (!on) { selected.clear(); document.querySelectorAll(".rc.sel").forEach(c => c.classList.remove("sel")); document.querySelectorAll(".chk").forEach(c => c.checked = false); }
  updateSelBtn();
}
async function remove(names) {
  const msg = names.length === 1 ? t("Delete this recording?") : names.length + " " + t("recordings?");
  if (!confirm(msg)) return false;
  await post("/api/rec/delete", {names});
  return true;
}
function zip(names) { $("#zipnames").value = JSON.stringify(names); $("#zipform").submit(); }

// ---- viewer ----
function openAt(i) {
  if (i < 0 || i >= items.length) return;
  modalIdx = i; const it = items[i], token = ++modalToken;
  $("#modal").hidden = false;
  $("#m-title").textContent = it.time; $("#m-meta").textContent = [fmtSize(it.size), it.source || "", it.schedules.join(", ")].filter(Boolean).join(" · ");
  $("#m-dl").href = "/rec/file/" + encodeURIComponent(it.name) + "?dl=1"; $("#m-dl").setAttribute("download", it.name);
  $("#m-fav").textContent = it.fav ? "★" : "☆"; $("#m-fav").style.color = it.fav ? "var(--yel)" : "";
  $("#m-prev").disabled = i === 0; $("#m-next").disabled = i === items.length - 1;
  const body = $("#m-body"), note = $("#m-note"); body.textContent = ""; note.textContent = "";
  if (it.kind === "image") { const im = el("img"); im.src = "/rec/file/" + encodeURIComponent(it.name); body.appendChild(im); }
  else showVideo(it, token);
}
async function showVideo(it, token) {
  const body = $("#m-body"), note = $("#m-note");
  note.textContent = t("Preparing video…");
  for (let n = 0; n < 1200; n++) {                    // converting a long clip can take a while: poll up to ~30 min
    const r = await post("/api/rec/prepare", {name: it.name});
    if (token !== modalToken) return;                 // the viewer was closed or moved on
    if (r.state === "ready") {
      const v = el("video"); v.controls = true; v.autoplay = true; v.playsInline = true; v.src = r.url; body.appendChild(v); note.textContent = ""; return;
    }
    if (r.state === "converting") { note.textContent = t("Converting for the browser (one time)…"); await sleep(1500); continue; }
    if (r.state === "live") { note.textContent = t("Still recording - available when it ends."); return; }
    if (r.state === "unsupported") {
      note.textContent = t("This video uses a codec browsers cannot play. Install ffmpeg on the Pi (sudo apt install ffmpeg) or download the file."); return;
    }
    note.textContent = t("Error") + ": " + (r.error || r.state); return;
  }
}
function closeModal() { modalToken++; $("#modal").hidden = true; $("#m-body").textContent = ""; modalIdx = -1; }
$("#m-close").onclick = closeModal;
$("#m-prev").onclick = () => openAt(modalIdx - 1);
$("#m-next").onclick = () => openAt(modalIdx + 1);
$("#m-fav").onclick = async () => { const it = items[modalIdx]; if (!it) return; await setFav([it.name], !it.fav); it.fav = !it.fav; openAtKeep(); load(true); };
function openAtKeep() { const it = items[modalIdx]; if (it) { $("#m-fav").textContent = it.fav ? "★" : "☆"; $("#m-fav").style.color = it.fav ? "var(--yel)" : ""; } }
$("#m-del").onclick = async () => { const it = items[modalIdx]; if (it && await remove([it.name])) { closeModal(); load(true); loadStats(); } };
$("#modal").addEventListener("click", e => { if (e.target.id === "modal") closeModal(); });
addEventListener("keydown", e => {
  if ($("#modal").hidden) return;
  if (e.key === "Escape") closeModal(); else if (e.key === "ArrowLeft") openAt(modalIdx - 1); else if (e.key === "ArrowRight") openAt(modalIdx + 1);
});

// ---- statistics ----
async function loadStats() {
  const p = new URLSearchParams({days: 14}); if (tlDay) p.set("day", tlDay);
  let j; try { j = await (await fetch("/api/recordings/stats?" + p)).json(); } catch (e) { return; }
  if (!tlDay) tlDay = ymd(new Date());
  if (!j.day) { const p2 = new URLSearchParams({days: 14, day: tlDay}); try { j = await (await fetch("/api/recordings/stats?" + p2)).json(); } catch (e) { return; } }
  const heat = $("#heat"); heat.textContent = "";
  const max = Math.max(1, ...j.heat.map(r => Math.max(...r)));
  heat.appendChild(el("span", "hl", ""));
  for (let h = 0; h < 24; h++) heat.appendChild(el("span", "hl", h % 6 === 0 ? String(h) : ""));
  j.heat.forEach((row, d) => {
    heat.appendChild(el("span", "hl", DAYN()[d]));
    row.forEach((n, h) => { const c = el("span", "c"); c.title = DAYN()[d] + " " + pad(h) + ":00 · " + n + " " + t("events");
      if (n) { c.style.background = "var(--acc)"; c.style.opacity = String(0.22 + 0.78 * n / max); c.style.borderColor = "transparent"; } heat.appendChild(c); });
  });
  const mx = Math.max(1, ...j.days.map(d => d.count)), db = $("#dbars"); db.textContent = "";
  j.days.forEach(d => {
    const b = el("div", "d" + (d.date === tlDay ? " on" : "")); b.title = d.date + " · " + d.count + " " + t("events");
    const i = el("i"); i.style.height = Math.max(2, 100 * d.count / mx * 0.8) + "%"; b.append(i, el("small", "", d.date.slice(8)));
    b.onclick = () => { tlDay = d.date; setDates(d.date, d.date); loadStats(); }; db.appendChild(b);
  });
  $("#tl-title").textContent = t("Timeline") + " · " + tlDay + " · " + j.events.length + " " + t("events");
  const tl = $("#tl"); tl.textContent = "";
  [0, 3, 6, 9, 12, 15, 18, 21, 24].forEach(h => { const k = el("span", "tk", pad(h)); k.style.left = (h / 24 * 100) + "%"; tl.appendChild(k); });
  j.events.forEach(ev => { const m = el("span", "m " + ev.kind); m.style.left = (ev.m / 1440 * 100) + "%"; m.title = ev.t;
    m.onclick = () => { openAfter = ev.name; setDates(tlDay, tlDay); }; tl.appendChild(m); });
}

// ---- filter controls ----
function setDates(a, b) { F.from = a; F.to = b; $("#f-from").value = a; $("#f-to").value = b; load(true); }
document.querySelectorAll(".quick button").forEach(b => b.onclick = () => {
  const now = new Date(), d1 = new Date(now), d7 = new Date(now);
  d1.setDate(d1.getDate() - 1); d7.setDate(d7.getDate() - 6);
  const q = b.dataset.q;
  if (q === "all") setDates("", ""); else if (q === "today") setDates(ymd(now), ymd(now));
  else if (q === "yday") setDates(ymd(d1), ymd(d1)); else setDates(ymd(d7), ymd(now));
});
$("#f-from").onchange = () => { F.from = $("#f-from").value; load(true); };
$("#f-to").onchange = () => { F.to = $("#f-to").value; load(true); };
document.querySelectorAll("#f-kind button").forEach(b => b.onclick = () => { F.kind = b.dataset.kind; markKind(); load(true); });
function markKind() { document.querySelectorAll("#f-kind button").forEach(b => b.classList.toggle("sel", b.dataset.kind === F.kind)); }
$("#f-sched").onchange = () => { F.schedule = $("#f-sched").value; load(true); };
$("#f-src").onchange = () => { F.source = $("#f-src").value; load(true); };
$("#f-sort").onchange = () => { F.sort = $("#f-sort").value; load(true); };
$("#btn-fav").onclick = () => { F.fav = F.fav ? "" : "1"; $("#btn-fav").classList.toggle("on", !!F.fav); load(true); };
let qTimer = null;
$("#f-q").oninput = () => { clearTimeout(qTimer); qTimer = setTimeout(() => { F.q = $("#f-q").value.trim(); load(true); }, 300); };
$("#btn-reset").onclick = () => {
  Object.assign(F, {from: "", to: "", kind: "", schedule: "", source: "", q: "", sort: "new", fav: ""});
  $("#f-from").value = $("#f-to").value = $("#f-q").value = ""; $("#f-sort").value = "new"; $("#btn-fav").classList.remove("on"); markKind(); load(true);
};
$("#btn-refresh").onclick = () => { load(true); loadStats(); };
$("#btn-select").onclick = () => setSelecting(!selecting);
$("#btn-delsel").onclick = async () => { if (selected.size && await remove([...selected])) { setSelecting(false); load(true); loadStats(); } };
$("#btn-zipsel").onclick = () => { if (selected.size) zip([...selected]); };
$("#btn-starsel").onclick = async () => { if (selected.size) { await setFav([...selected], true); toast("★ " + selected.size); setSelecting(false); load(true); } };
$("#more").onclick = () => load(false);

(async () => {
  await initAppearance(); markKind(); updateSelBtn(); load(true); loadStats();
})();
/*ALERTS*/
</script></body></html>
"""


def web_specs():
    """key -> spec for every setting that may be changed remotely (reuses the GUI definitions)."""
    specs = {}
    for sec, key, label in TOGGLES:
        if key != "web_stream":                  # the stream must not be switched off from the stream itself
            specs[key] = {"type": "bool"}
    for sec, key, label, lo, hi, step in SLIDERS:
        specs[key] = {"type": "num", "min": lo, "max": hi, "step": step}
    return specs


def web_schema(lang=None):
    out = []
    for sec in SECTIONS:
        toggles = [{"key": k, "label": tr(l, lang)} for s, k, l in TOGGLES if s == sec and k != "web_stream"]
        sliders = [{"key": k, "label": tr(l, lang), "min": lo, "max": hi, "step": st} for s, k, l, lo, hi, st in SLIDERS if s == sec]
        texts = [x for x in web_texts(lang) if x["section"] == sec]
        if toggles or sliders or texts:
            out.append({"id": sec, "name": tr(sec, lang), "toggles": toggles, "sliders": sliders, "texts": texts})
    return out


def set_cfg(key, value):
    """Validated setter for the web API. Returns (ok, error_message)."""
    spec = web_specs().get(key)
    if spec is None:
        return False, "unknown setting"
    if spec["type"] == "bool":
        CFG[key] = bool(value)
        sched_user_changed(key)
        save_settings()
        if key == "patrol":
            log_event("patrol", "Patrol switched ON (web)" if CFG[key] else "Patrol switched OFF (web)")
        return True, ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, "not a number"
    if not math.isfinite(v):
        return False, "not a number"
    v = max(spec["min"], min(spec["max"], v))
    v = round(round(v / spec["step"]) * spec["step"], 2)
    CFG[key] = int(round(v)) if isinstance(CFG[key], int) else float(v)
    save_settings()
    return True, ""


class WebStream:
    def __init__(self, watch):
        self.watch = watch; self.started = False

    def start(self):
        if self.started:
            return
        try:
            from flask import Flask, Response, request, send_file
        except ImportError:
            STATE["web_status"] = "flask not installed"
            log_event("web", "Web stream: pip install flask"); return
        app = Flask("motionwatch")
        watch = self.watch

        def reply(obj, code=200):
            return Response(json.dumps(obj, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                            status=code, mimetype="application/json")

        def body():
            return request.get_json(force=True, silent=True) or {}

        fails = {}                                  # ip -> times of wrong passwords (lock-out after 8 in 5 minutes)

        @app.before_request
        def auth():
            pw = CFG["web_password"]
            if not pw:
                return None
            ip = request.remote_addr or "?"
            now = time.time()
            recent = [x for x in fails.get(ip, []) if now - x < 300]
            if len(recent) >= 8:
                fails[ip] = recent
                return Response("Too many failed logins - try again in a few minutes", 429, {"Retry-After": "300"})
            a = request.authorization
            if a and hmac.compare_digest(str(a.password or "").encode(), str(pw).encode()):
                fails.pop(ip, None)
                return None
            if a:
                recent.append(now)
                if len(recent) == 8:
                    log_event("web", f"Login blocked for 5 minutes after 8 wrong passwords from {ip}")
            fails[ip] = recent
            if len(fails) > 500:
                for k in [k for k, v in fails.items() if not v or now - v[-1] > 300]:
                    fails.pop(k, None)
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Motion Watch"'})

        @app.after_request
        def secure_headers(resp):
            resp.headers.setdefault("X-Content-Type-Options", "nosniff")
            resp.headers.setdefault("X-Frame-Options", "DENY")
            resp.headers.setdefault("Referrer-Policy", "no-referrer")
            return resp

        @app.route("/")
        def index():
            return Response(render_page(WEB_PAGE, "live"), mimetype="text/html")

        @app.route("/cams")
        def cams_page():
            return Response(render_page(CAMS_PAGE, "cams"), mimetype="text/html")

        @app.route("/zones")
        def zones_page():
            return Response(render_page(ZONES_PAGE, "zones"), mimetype="text/html")

        @app.route("/video_feed")
        def video_feed():
            def gen():
                last = -1
                watch.web_viewers += 1; STATE["web_viewers"] = watch.web_viewers
                try:
                    while True:
                        jpg, seq = watch.jpeg, watch.jpeg_seq
                        if jpg and seq != last:
                            last = seq
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode()
                                   + b"\r\n\r\n" + jpg + b"\r\n")
                        else:
                            time.sleep(0.02)
                finally:
                    watch.web_viewers = max(0, watch.web_viewers - 1); STATE["web_viewers"] = watch.web_viewers
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

        @app.route("/snapshot.jpg")
        def snapshot():
            if watch.frame_out is None:
                return Response("no frame yet", 503)
            ok, buf = cv2.imencode(".jpg", watch.frame_out, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                return Response("encode error", 500)
            watch_jpeg = buf.tobytes()
            name = datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.jpg")
            return Response(watch_jpeg, mimetype="image/jpeg",
                            headers={"Content-Disposition": f'attachment; filename="{name}"'})

        @app.route("/api/schema")
        def api_schema():
            lang = request.args.get("lang") or CFG["lang"]
            return reply(web_schema("de" if lang == "de" else "en"))

        @app.route("/api/appearance")
        def api_appearance():
            return reply({"theme": CFG["theme"], "lang": CFG["lang"]})

        @app.route("/api/state")
        def api_state():
            with LOCK:
                st = {k: v for k, v in STATE.items() if k != "events"}
                events = [dict(e) for e in STATE["events"][:12]]
                relays = [dict(r) for r in RELAYS]
                schedules = [dict(x) for x in SCHEDULES]
                st["extra"] = cams_status()
                st["camping"] = bool(CFG["camping"]); st["net_mode"] = CFG["net_mode"]
                st["hotspot_cfg"] = {"ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"], "address": page_address("10.42.0.1")}
            cfg = {k: CFG[k] for k in web_specs()}
            return reply({"state": st, "cfg": cfg, "waypoints": list(WAYPOINTS), "events": events, "relays": relays,
                          "schedules": schedules})

        @app.route("/api/triggers")
        def api_triggers():
            lang = "de" if (request.args.get("lang") or CFG["lang"]) == "de" else "en"
            return reply([{"key": k, "label": tr_trigger(k, lang)} for k in TRIGGERS])

        @app.route("/api/relay", methods=["POST"])
        def api_relay():
            d = body(); a = d.get("action"); idx = d.get("index")
            lang = "de" if d.get("lang") == "de" else "en"
            if a == "set":
                ok, err = relay_update(idx, d.get("field"), d.get("value"))
            elif a == "add":
                ok, err = relay_add()
            elif a == "remove":
                ok, err = relay_remove(idx)
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/set", methods=["POST"])
        def api_set():
            d = body()
            ok, msg = set_cfg(d.get("key"), d.get("value"))
            return reply({"ok": ok, "error": msg or None}, 200 if ok else 400)

        @app.route("/api/move", methods=["POST"])
        def api_move():
            d = body()
            if not move_camera(d.get("dir"), d.get("step", 3)):
                return reply({"ok": False, "error": "unknown direction"}, 400)
            return reply({"ok": True, "pan": CFG["pan"], "tilt": CFG["tilt"]})

        @app.route("/api/stick", methods=["POST"])
        def api_stick():
            d = body()
            if not stick_camera(d.get("x", 0), d.get("y", 0), d.get("speed", 30)):
                return reply({"ok": False, "error": "invalid values"}, 400)
            return reply({"ok": True, "pan": CFG["pan"], "tilt": CFG["tilt"]})

        @app.route("/api/arm", methods=["POST"])
        def api_arm():
            a = body().get("action")
            if a == "arm":
                arm()
            elif a == "arm_now":
                arm(0)
            elif a == "disarm":
                disarm()
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True, "state": STATE["arm_state"], "left": STATE["arm_left"]})

        @app.route("/api/hotspot", methods=["POST"])
        def api_hotspot():
            d = body(); lang = "de" if d.get("lang") == "de" else "en"
            if wifi_backend() != "nm":
                return reply({"ok": False, "error": tr("the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)", lang)}, 400)
            hotspot_password()
            netauto_pause()
            hotspot_switch_later(bool(d.get("on")))
            return reply({"ok": True, "ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"], "address": page_address("10.42.0.1")})

        @app.route("/api/camping", methods=["POST"])
        def api_camping():
            d = body()
            hotspot_password()
            ok, err = camping_set(bool(d.get("on")))
            return reply({"ok": ok, "error": err or None, "ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"],
                          "address": page_address("10.42.0.1"), "hotspot": wifi_backend() == "nm"})

        @app.route("/api/autostart", methods=["GET", "POST"])
        def api_autostart():
            if request.method == "GET":
                return reply(autostart_refresh())
            d = body(); lang = "de" if d.get("lang") == "de" else "en"
            ok, err = autostart_set(bool(d.get("on")))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "autostart": STATE["autostart"]}, 200 if ok else 400)

        @app.route("/api/time", methods=["POST"])
        def api_time():
            d = body()
            return reply({"ok": True, "status": sync_time_from_client(d.get("t"), d.get("tz") or "")})

        @app.route("/api/wifi", methods=["GET", "POST"])
        def api_wifi():
            if request.method == "GET":
                return reply(wifi_status())
            d = body(); a = d.get("action"); lang = "de" if d.get("lang") == "de" else "en"
            if not CFG["web_password"] and (request.remote_addr or "") not in ("127.0.0.1", "::1"):
                return reply({"ok": False, "error": tr("set a web password first (--web-password) - otherwise anybody in the network could change the Wi-Fi", lang)}, 403)
            if a == "scan":
                ok, err = wifi_scan()
            elif a == "connect":
                ok, err = wifi_connect(d.get("ssid"), d.get("password") or "", bool(d.get("preferred", True)))
            elif a == "save":
                ok, err = wifi_save(d.get("ssid"), d.get("password") or "", bool(d.get("preferred", True)))
            elif a == "forget":
                ok, err = wifi_forget(d.get("id"))
            else:
                ok, err = False, "unknown action"
            out = wifi_status(); out.update(ok=ok, error=tr_err(err, lang) if err else None)
            return reply(out, 200 if ok else 400)

        @app.route("/api/ui", methods=["GET", "POST"])
        def api_ui():
            if request.method == "POST":
                d = body()
                if not web_ui_update(d.get("set", {}), d.get("del", [])):
                    return reply({"ok": False, "error": "invalid"}, 400)
                return reply({"ok": True})
            return reply(CFG["web_ui"])

        @app.route("/api/alerts")
        def api_alerts():
            """Server-Sent Events: open pages get every alarm at once (also in a background tab)."""
            try:
                last = int(request.headers.get("Last-Event-ID") or 0)
            except ValueError:
                last = 0
            now0 = time.time()
            with ALERTS_COND:
                if last <= 0 or last > ALERTS["seq"]:
                    last = ALERTS["seq"]

            def gen():
                nonlocal last
                yield "retry: 3000\n\n"
                while True:
                    with ALERTS_COND:
                        if ALERTS["seq"] <= last:
                            ALERTS_COND.wait(timeout=15.0)
                        items = [dict(a) for a in ALERTS["items"] if a["seq"] > last]
                    if items:
                        for a in items:
                            last = a["seq"]
                            if time.time() - a["ts"] < 60:     # after a reconnect: nothing older than a minute
                                yield f"id: {a['seq']}\nevent: alert\ndata: {json.dumps(a)}\n\n"
                    else:
                        yield ": ping\n\n"                  # keeps proxies / phones from closing the connection
            return Response(gen(), mimetype="text/event-stream",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

        @app.route("/api/timelapse")
        def api_timelapse():
            return reply(tl_overview())

        @app.route("/api/timelapse", methods=["POST"])
        def api_timelapse_post():
            d = body(); a = d.get("action"); lang = "de" if d.get("lang") == "de" else "en"
            if a == "now":
                watch.timelapse.request_now(); log_event("servo", "Timelapse photo requested (web)")
            elif a == "here":                                  # take the position the camera has right now
                CFG["timelapse_pan"] = round(float(CFG["pan"]), 1); CFG["timelapse_tilt"] = round(float(CFG["tilt"]), 1)
                save_settings(); log_event("servo", f"Timelapse position set to pan {CFG['timelapse_pan']:.0f}% / tilt {CFG['timelapse_tilt']:.0f}%")
            elif a == "goto":                                  # look at the picture of the chosen position
                CFG["pan"], CFG["tilt"] = float(CFG["timelapse_pan"]), float(CFG["timelapse_tilt"])
                MANUAL["until"] = time.time() + max(10.0, CFG["manual_hold"])
            elif a == "render":
                ok, err = timelapse_render(d.get("day", ""), d.get("fps"))
                return reply({"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 400)
            elif a == "delete_video":
                p = tl_path(d.get("name"))
                if not p or not TL_VIDEO_RE.match(d.get("name", "")):
                    return reply({"ok": False, "error": "not found"}, 404)
                os.remove(p)
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True})

        @app.route("/timelapse/<name>")
        def timelapse_file(name):
            p = tl_path(name)
            if not p:
                return Response("not found", 404)
            return send_file(p, mimetype="video/mp4" if name.endswith(".mp4") else "image/jpeg", conditional=True,
                             as_attachment=request.args.get("dl") == "1", download_name=name)

        @app.route("/api/action", methods=["POST"])
        def api_action():
            a = body().get("action")
            if a == "wp_add":
                WAYPOINTS.append(round(float(CFG["pan"]), 1)); save_settings()
                log_event("patrol", f"Waypoint added at pan {CFG['pan']:.0f}% (web)  ->  {[round(w) for w in WAYPOINTS]}")
            elif a == "wp_clear":
                WAYPOINTS.clear(); save_settings(); log_event("patrol", "Waypoints cleared (web)")
            elif a == "recalibrate":
                watch.tuner.reset()
            elif a == "reset_counter":
                STATE["detections_total"] = 0; STATE["ignored_vehicles"] = 0
                log_event("person", "Person counter reset (web)")
            elif a == "reset_settings":
                reset_settings()
            elif a == "save_settings":
                save_settings_now()
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True})

        # ---- video source ----
        @app.route("/api/sources")
        def api_sources():
            return reply(source_info())

        @app.route("/api/sources/scan", methods=["POST"])
        def api_sources_scan():
            scan_sources(STATE["source_id"])               # takes a few seconds; the server is threaded
            return reply(source_info())

        @app.route("/api/source", methods=["POST"])
        def api_source():
            d = body(); a = d.get("action")
            lang = "de" if d.get("lang") == "de" else "en"
            if a == "select":
                ok, err = source_select(watch, d.get("id"))
            elif a == "add":
                ok, err, sid = source_add(d.get("name"), d.get("url"))
                if ok and d.get("select"):
                    source_select(watch, "url:" + sid)
                if ok:
                    return reply({"ok": True, "error": None, "id": "url:" + sid})
            elif a == "remove":
                ok, err = source_remove(watch, d.get("id"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        # ---- schedule ----
        @app.route("/api/schedule")
        def api_schedule_get():
            lang = "de" if (request.args.get("lang") or CFG["lang"]) == "de" else "en"
            with LOCK:
                plans = [dict(x) for x in SCHEDULES]
            return reply({"features": [{"key": k, "label": tr(l, lang)} for k, l in SCHED_FEATURES], "schedules": plans})

        @app.route("/api/schedule", methods=["POST"])
        def api_schedule_post():
            d = body(); a = d.get("action")
            lang = "de" if d.get("lang") == "de" else "en"
            if a == "add":
                ok, err = schedule_add()
            elif a == "save":
                ok, err = schedule_save(d.get("index"), d.get("schedule"))
            elif a == "remove":
                ok, err = schedule_remove(d.get("index"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        # ---- recordings preview ----
        @app.route("/recordings")
        def recordings_page():
            return Response(render_page(REC_PAGE, "rec"), mimetype="text/html")

        @app.route("/api/recordings")
        def api_recordings():
            return reply(list_recordings(request.args, watch))

        @app.route("/rec/thumb/<name>")
        def rec_thumb_route(name):
            p = rec_thumb(name)
            if not p:
                return Response("no thumbnail", 404)
            return send_file(p, mimetype="image/jpeg", max_age=3600)

        @app.route("/rec/file/<name>")
        def rec_file(name):
            p = rec_path(name)
            ext = os.path.splitext(name)[1].lower()
            if not p or ext not in REC_EXTS:
                return Response("not found", 404)
            return send_file(p, mimetype="video/mp4" if ext == ".mp4" else "image/jpeg", conditional=True,
                             as_attachment=request.args.get("dl") == "1", download_name=name)

        @app.route("/rec/play/<name>")
        def rec_play(name):
            if rec_path(name) is None or not name.lower().endswith(".mp4") or not os.path.isfile(_cache_path(name)):
                return Response("not converted yet", 404)
            return send_file(_cache_path(name), mimetype="video/mp4", conditional=True)

        @app.route("/api/rec/prepare", methods=["POST"])
        def api_rec_prepare():
            return reply(rec_play_state(body().get("name"), watch))

        @app.route("/api/rec/delete", methods=["POST"])
        def api_rec_delete():
            return reply({"ok": True, "deleted": rec_delete(body().get("names"), watch)})

        # ---- more cameras ----
        @app.route("/api/cams")
        def api_cams():
            return reply({"cams": cams_status(), "sources": source_info()})

        @app.route("/api/cams", methods=["POST"])
        def api_cams_post():
            d = body(); a = d.get("action"); lang = "de" if d.get("lang") == "de" else "en"
            if a == "add":
                ok, err = cams_add(d.get("id"))
            elif a == "remove":
                ok, err = cams_remove(d.get("id"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/cam_feed/<int:n>")
        def cam_feed(n):
            cam = next((c for c in CAMS if c.idx == n), None)
            if cam is None:
                return Response("unknown camera", 404)

            def gen():
                last = -1
                cam.viewers += 1
                try:
                    while not cam.stop:
                        jpg, seq = cam.jpeg, cam.seq
                        if jpg and seq != last:
                            last = seq
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                        else:
                            time.sleep(0.03)
                finally:
                    cam.viewers = max(0, cam.viewers - 1)
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

        # ---- zones ----
        @app.route("/api/zones")
        def api_zones_get():
            return reply({"zones": [dict(z) for z in ZONES]})

        @app.route("/api/zones", methods=["POST"])
        def api_zones_post():
            d = body(); lang = "de" if d.get("lang") == "de" else "en"
            ok, err = zones_set(d.get("zones"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/frame.jpg")
        def api_frame():
            if time.time() > watch.raw_until:
                watch.frame_raw = None
            watch.raw_until = time.time() + 15
            for _ in range(25):
                if watch.frame_raw is not None:
                    break
                time.sleep(0.1)
            f = watch.frame_raw
            if f is None:
                return Response("no frame yet", 503)
            ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        # ---- text settings, test notification ----
        @app.route("/api/text", methods=["POST"])
        def api_text():
            d = body(); lang = "de" if d.get("lang") == "de" else "en"
            ok, err = set_text(d.get("key"), d.get("value"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/notify_test", methods=["POST"])
        def api_notify_test():
            lang = "de" if body().get("lang") == "de" else "en"
            if not Notifier.configured():
                return reply({"ok": False, "error": tr_err("notification is not configured", lang)}, 400)
            watch.notifier.test(watch.frame_out)
            return reply({"ok": True})

        # ---- recordings: favourites, zip, statistics ----
        @app.route("/api/rec/fav", methods=["POST"])
        def api_rec_fav():
            d = body()
            return reply({"ok": True, "changed": rec_set_fav(d.get("names"), bool(d.get("value")), watch)})

        @app.route("/api/recordings/stats")
        def api_rec_stats():
            return reply(rec_stats(request.args.get("days", 14), request.args.get("day")))

        @app.route("/rec/zip", methods=["GET", "POST"])
        def rec_zip_route():
            if request.method == "POST":
                try:
                    names = json.loads(request.form.get("names", "[]"))
                except ValueError:
                    names = []
            else:
                names = [n for n in (request.args.get("names") or "").split(",") if n]
            p = rec_zip(names, watch)
            if not p:
                return Response("nothing to download", 404)
            def gen():                                    # streamed, so the temporary file can be removed afterwards
                try:
                    with open(p, "rb") as f:
                        while True:
                            chunk = f.read(1 << 20)
                            if not chunk:
                                break
                            yield chunk
                finally:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            fname = "motionwatch_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
            return Response(gen(), mimetype="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="{fname}"', "Content-Length": str(os.path.getsize(p))})

        import logging; logging.getLogger("werkzeug").setLevel(logging.ERROR)
        ctx = None
        if WEB_OPTS["https"]:
            ctx = ensure_cert()
            if not ctx[0]:
                STATE["web_status"] = "https failed (no certificate; install openssl or pass --cert/--key)"
                log_event("web", "HTTPS requested but no certificate available - web page NOT started"); return
        threading.Thread(target=lambda: app.run(host=WEB_OPTS["bind"], port=int(CFG["web_port"]), threaded=True,
                                                use_reloader=False, ssl_context=ctx), daemon=True).start()
        self.started = True
        scheme = "https" if ctx else "http"
        STATE["web_open"] = not CFG["web_password"] and WEB_OPTS["bind"] not in ("127.0.0.1", "localhost", "::1")
        STATE["web_status"] = f"on · {scheme} · port {CFG['web_port']}" + (" · password" if CFG["web_password"] else " · NO PASSWORD")
        log_event("web", f"Web control started: {scheme}://<ip>:{CFG['web_port']}/  (raw stream: /video_feed)")
        if STATE["web_open"]:
            log_event("web", "WARNING: the web page has no password and is reachable from the network - use --web-password, --bind 127.0.0.1 or a VPN")
        self.app = app


# ----------------------------------------------------------------------------
# Translations (English text is the key; German below). tr() is used everywhere.
# ----------------------------------------------------------------------------
DE = {
    # sections
    "Camera / Servos": "Kamera / Servos", "Patrol": "Patrouille", "AI detection": "KI-Erkennung",
    "Relay / Alarm": "Relais / Alarm", "Notifications": "Benachrichtigungen", "Web stream": "Web-Stream",
    "Auto-tune": "Auto-Abstimmung", "Detection": "Erkennung", "Low light": "Schwachlicht",
    "Walking recognition": "Geh-Erkennung", "Vehicle filter": "Fahrzeugfilter", "Rain": "Regen", "Wind": "Wind",
    "Recording": "Aufnahme", "Appearance": "Darstellung",
    # sliders
    "Pan (%)": "Schwenken (%)", "Tilt (%)": "Neigen (%)", "Tracking gain": "Verfolgungsstärke",
    "Tracking dead zone": "Verfolgungs-Totzone", "Dwell at waypoint (s)": "Verweilzeit am Wegpunkt (s)",
    "Patrol speed (%/s)": "Patrouillen-Geschwindigkeit (%/s)", "Patrol tilt (%)": "Patrouillen-Neigung (%)",
    "Confidence threshold": "Konfidenz-Schwelle", "Run every N frames": "Alle N Bilder ausführen",
    "Object confidence": "Objekt-Konfidenz", "JPEG quality": "JPEG-Qualität", "Stream width (px)": "Stream-Breite (px)",
    "Hold after person (s)": "Halten nach Person (s)", "Walking time needed (s)": "Nötige Gehzeit (s)",
    "Sensitivity": "Empfindlichkeit", "Shadow: max brightness ratio": "Schatten: max. Helligkeitsverhältnis",
    "Shadow: min brightness ratio": "Schatten: min. Helligkeitsverhältnis", "Min object size (px²)": "Min. Objektgröße (px²)",
    "Frames of steady motion": "Bilder gleichmäßiger Bewegung", "Min speed (px/frame)": "Min. Geschwindigkeit (px/Bild)",
    "Max speed (px/frame)": "Max. Geschwindigkeit (px/Bild)", "Speed consistency": "Geschwindigkeits-Konstanz",
    "Vehicle aspect ratio": "Fahrzeug-Seitenverhältnis", "Vehicle speed (px/frame)": "Fahrzeug-Geschwindigkeit (px/Bild)",
    "Rain threshold": "Regen-Schwelle", "Wind threshold": "Wind-Schwelle", "Max trigger boost": "Max. Auslöse-Verstärkung",
    "Keep recording after (s)": "Nachlaufzeit Aufnahme (s)", "Max recordings folder (GB)": "Max. Aufnahmeordner (GB)",
    "Low-light threshold (brightness)": "Schwachlicht-Schwelle (Helligkeit)", "Cooldown between alarms (s)": "Pause zwischen Alarmen (s)",
    # toggles
    "Follow detected person (auto pan/tilt)": "Erkannter Person folgen (auto Schwenk/Neige)",
    "Invert pan direction": "Schwenkrichtung umkehren", "Invert tilt direction": "Neigerichtung umkehren",
    "Pendulum patrol active": "Pendel-Patrouille aktiv", "AI person detection (SSD MobileNet V2)": "KI-Personenerkennung (SSD MobileNet V2)",
    "Mark all detected objects (cars, animals, ...)": "Alle erkannten Objekte markieren (Autos, Tiere, ...)",
    "Motion persons need AI confirmation": "Bewegungs-Personen brauchen KI-Bestätigung",
    "Switch relay when person detected": "Relais bei Person schalten", "Relay ON (manual)": "Relais EIN (manuell)",
    "Web stream + remote control (port 5000)": "Web-Stream + Fernsteuerung (Port 5000)", "Automatic tuning": "Automatische Abstimmung",
    "Detection (master switch)": "Erkennung (Hauptschalter)", "Highlight persons red": "Personen rot hervorheben",
    "Show movement tracks": "Bewegungsspuren anzeigen", "Show motion mask": "Bewegungsmaske anzeigen",
    "Show HUD overlay": "HUD-Einblendung anzeigen", "Shadow filter (ignore person shadows)": "Schattenfilter (Schatten ignorieren)",
    "Keep person flagged while tracked": "Person markiert lassen solange verfolgt", "Ignore cars / vehicles": "Autos / Fahrzeuge ignorieren",
    "Auto rain detection": "Automatische Regenerkennung", "Rain mode (manual, if auto off)": "Regenmodus (manuell, wenn Auto aus)",
    "Auto wind detection": "Automatische Winderkennung", "Record when person seen": "Aufnehmen wenn Person erkannt",
    "Save snapshot JPG per detection": "Schnappschuss-JPG pro Erkennung", "Auto low-light mode (contrast boost)": "Auto-Schwachlichtmodus (Kontrast)",
    # badges / stats / buttons / misc
    "No person": "Keine Person", "PERSON DETECTED": "PERSON ERKANNT", "PERSONS DETECTED": "PERSONEN ERKANNT",
    "Persons total": "Personen gesamt", "No rain": "Kein Regen", "RAIN MODE": "REGENMODUS", "Wind": "Wind",
    "Idle": "Bereit", "REC": "AUFN", "Relay off": "Relais aus", "RELAY ON": "RELAIS EIN", "Patrol off": "Patrouille aus",
    "TRACKING": "VERFOLGT", "Light ok": "Licht ok", "LOW LIGHT": "SCHWACHLICHT", "Auto": "Auto",
    "FPS": "FPS", "PERSONS NOW": "PERSONEN JETZT", "DETECTIONS": "ERKENNUNGEN", "VEHICLES IGNORED": "FAHRZEUGE IGNORIERT",
    "SHADOW % REMOVED": "SCHATTEN % ENTFERNT", "SYSTEM · CPU": "SYSTEM · CPU", "WEATHER": "WETTER",
    "Rain score": "Regen-Wert", "Wind score": "Wind-Wert", "Trigger multiplier (wind)": "Auslöse-Faktor (Wind)",
    "EVENT LOG": "EREIGNISPROTOKOLL", "Expand all": "Alle öffnen", "Collapse all": "Alle schließen",
    "Centre camera": "Kamera zentrieren", "Snapshot": "Schnappschuss", "Add current pan as waypoint": "Aktuelle Position als Wegpunkt",
    "Clear": "Löschen", "Recalibrate (scene empty)": "Neu kalibrieren (Szene leer)", "Reset all settings": "Alle Einstellungen zurücksetzen",
    "Test notification": "Test-Benachrichtigung", "Webhook URL (POST JSON on person; e.g. https://ntfy.sh/my-topic)":
        "Webhook-URL (POST JSON bei Person; z. B. https://ntfy.sh/mein-thema)",
    "backend": "Backend", "pan": "Schwenk", "tilt": "Neigung", "waypoints": "Wegpunkte", "none": "keine",
    "AI persons": "KI-Personen", "objects": "Objekte", "automatic changes": "automatische Änderungen", "status": "Status",
    "Settings": "Einstellungen", "recordings": "Aufnahmen", "brightness": "Helligkeit", "cores": "Kerne", "last 60 s": "letzte 60 s",
    "no CPU data (pip install psutil)": "keine CPU-Daten (pip install psutil)",
    "Fullscreen (F11)": "Vollbild (F11)", "Exit fullscreen (Esc)": "Vollbild verlassen (Esc)",
    "Dark": "Dunkel", "Light": "Hell", "Theme": "Design", "Language": "Sprache",
    "Double-click video: video only · F11: fullscreen · Esc: back": "Doppelklick aufs Video: nur Video · F11: Vollbild · Esc: zurück",
    "Build": "Build", "Pan/Tilt surveillance with AI, patrol & relay": "Schwenk/Neige-Überwachung mit KI, Patrouille & Relais",
    "Motion Watch - desktop window opened": "Motion Watch - Desktop-Fenster geöffnet",
    # 1.2.3: relays, view menu, camera control
    "Relays": "Relais", "Off": "Aus", "On": "Ein", "on": "an", "View": "Ansicht", "Show all": "Alle einblenden",
    "Settings panel": "Einstellungsbereich", "Header": "Kopfzeile", "Statistics": "Statistiken", "Panels": "Bereiche",
    "Settings sections": "Einstellungsabschnitte", "Title": "Titel", "Header buttons": "Schaltflächen oben",
    "Persons": "Personen", "Objects": "Objekte", "Light level": "Lichtverhältnisse", "Persons now": "Personen jetzt",
    "Detections": "Erkennungen", "Vehicles ignored": "Fahrzeuge ignoriert", "Shadow % removed": "Schatten % entfernt",
    "Camera control": "Kamerasteuerung", "Weather": "Wetter", "System · CPU": "System · CPU", "Event log": "Ereignisprotokoll",
    "Settings status": "Einstellungs-Status", "OBJECTS": "OBJEKTE", "CAMERA CONTROL": "KAMERASTEUERUNG", "RELAYS": "RELAIS",
    "Step": "Schritt", "Arrow keys move the camera": "Pfeiltasten bewegen die Kamera", "MANUAL": "MANUELL",
    "Manual control - tracking / patrol paused": "Handsteuerung - Verfolgung / Patrouille pausiert",
    "Tracking person": "Person wird verfolgt", "Pan": "Schwenk", "Tilt": "Neigung", "+ Waypoint": "+ Wegpunkt",
    "Centre": "Mitte", "no relays": "keine Relais", "needs AI model": "braucht das KI-Modell", "Hold (s)": "Halten (s)",
    "Active low": "Low-aktiv", "Remove relay": "Relais entfernen", "Remove this relay?": "Dieses Relais entfernen?",
    "+ Add relay": "+ Relais hinzufügen", "Manual control pause (s)": "Pause nach Handsteuerung (s)",
    "Double-click video: video only · F11: fullscreen · Esc: back · Ctrl+B: settings panel · right-click video: show / hide fields":
        "Doppelklick aufs Video: nur Video · F11: Vollbild · Esc: zurück · Strg+B: Einstellungsbereich · Rechtsklick aufs Video: Felder ein-/ausblenden",
    RELAY_NOTE: "Auto: Das Relais schaltet ein, solange sein Auslöser im Bild ist, und bleibt für die Haltezeit an. "
                "Tier- und Objekt-Auslöser (z. B. Katze) brauchen das KI-Modell. "
                "Der Voralarm schaltet schon bei der ersten Bewegung im Bild ein, lange bevor eine Person bestätigt ist.",
    # relay triggers (COCO object names)
    "person": "Person", "motion (anything)": "Bewegung (alles)", "animal (any)": "Tier (alle)", "cat": "Katze", "dog": "Hund",
    "bird": "Vogel", "car": "Auto", "truck": "Lkw", "bicycle": "Fahrrad", "motorcycle": "Motorrad", "bus": "Bus",
    "horse": "Pferd", "sheep": "Schaf", "cow": "Kuh", "elephant": "Elefant", "bear": "Bär", "zebra": "Zebra",
    "giraffe": "Giraffe", "airplane": "Flugzeug", "train": "Zug", "boat": "Boot", "traffic light": "Ampel",
    "fire hydrant": "Hydrant", "stop sign": "Stoppschild", "parking meter": "Parkuhr", "bench": "Bank",
    "backpack": "Rucksack", "umbrella": "Regenschirm", "handbag": "Handtasche", "tie": "Krawatte", "suitcase": "Koffer",
    "frisbee": "Frisbee", "skis": "Ski", "snowboard": "Snowboard", "sports ball": "Ball", "kite": "Drachen",
    "skateboard": "Skateboard", "surfboard": "Surfbrett", "bottle": "Flasche", "cup": "Tasse", "chair": "Stuhl",
    "couch": "Sofa", "potted plant": "Topfpflanze", "bed": "Bett", "dining table": "Esstisch", "tv": "Fernseher",
    "laptop": "Laptop", "cell phone": "Handy", "book": "Buch", "clock": "Uhr", "vase": "Vase", "scissors": "Schere",
    "teddy bear": "Teddybär", "knife": "Messer", "bowl": "Schüssel", "banana": "Banane", "apple": "Apfel", "pizza": "Pizza",
    # relay errors
    "unknown relay": "unbekanntes Relais", "GPIO must be a number": "GPIO muss eine Zahl sein",
    "GPIO must be between 2 and 27": "GPIO muss zwischen 2 und 27 liegen", "mode must be off / on / auto": "Modus muss Aus / Ein / Auto sein",
    "unknown trigger": "unbekannter Auslöser", "hold time must be a number": "Haltezeit muss eine Zahl sein",
    "unknown field": "unbekanntes Feld", "no free GPIO left": "kein freier GPIO mehr", "unknown action": "unbekannte Aktion",
}


DE.update({
    "Fixed times": "Feste Zeiten", "Sunset → sunrise": "Sonnenuntergang → Sonnenaufgang", "Sunrise → sunset": "Sonnenaufgang → Sonnenuntergang",
    "Shift (minutes)": "Versatz (Minuten)", "Time window": "Zeitfenster", "Applies": "Gilt", "Always": "Immer",
    "Only when nobody is home": "Nur wenn niemand zuhause ist", "Only when somebody is home": "Nur wenn jemand zuhause ist",
    "Skip dates": "Ausnahmedaten", "Clear": "Löschen", "set": "gesetzt", "Test notification": "Test-Nachricht senden",
    "Open camera grid (browser)": "Kamera-Übersicht öffnen (Browser)", "Open zone editor (browser)": "Zonen-Editor öffnen (Browser)",
    "Notification type": "Art der Benachrichtigung", "Webhook / ntfy URL": "Webhook- / ntfy-URL", "Telegram bot token": "Telegram-Bot-Token",
    "Telegram chat id": "Telegram-Chat-ID", "Address of this page for links (e.g. https://pi.local:5000)": "Adresse dieser Seite für Links (z. B. https://pi.local:5000)",
    "Latitude (sunrise / sunset)": "Breitengrad (Sonnenauf-/untergang)", "Longitude (sunrise / sunset)": "Längengrad (Sonnenauf-/untergang)",
    "Phones / devices for presence (IP or name, comma separated)": "Handys / Geräte für Anwesenheit (IP oder Name, mit Komma getrennt)",
    "Setup": "Einrichtung", "Away after N minutes without answer": "Abwesend nach N Minuten ohne Antwort",
    "Pre-roll: video before the detection (s)": "Vorlauf: Video vor der Erkennung (s)", "Show zones in the picture": "Zonen im Bild zeigen",
    "Cameras": "Kameras", "Zones": "Zonen", "Live": "Live", "Recordings": "Aufzeichnungen",
    "invalid value": "ungültiger Wert", "out of range": "ausserhalb des erlaubten Bereichs", "invalid device name or address": "ungültiger Gerätename oder ungültige Adresse",
    "invalid URL (http:// or https:// expected)": "ungültige URL (http:// oder https:// erwartet)", "invalid Telegram bot token": "ungültiger Telegram-Bot-Token",
    "invalid Telegram chat id": "ungültige Telegram-Chat-ID", "this camera is already in use": "diese Kamera wird schon benutzt",
    "notification is not configured": "Benachrichtigung ist nicht eingerichtet", "invalid zones": "ungültige Zonen", "not a number": "keine Zahl",
    "Remove this network camera?": "Diese Netzwerk-Kamera entfernen?", "Remove this schedule?": "Diesen Zeitplan entfernen?",
    "off": "aus", "Video source": "Videoquelle", "Schedule": "Zeitplan", "Source": "Quelle", "Snapshots": "Schnappschüsse",
    "Person tracking": "Personenverfolgung", "Auto relays": "Auto-Relais", "Auto relays enabled": "Auto-Relais aktiv",
    "Send notifications": "Benachrichtigungen senden",
    "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …", "Remove network camera": "Netzwerk-Kamera entfernen",
    "Add network camera (RTSP / HTTP stream, Wi-Fi cams)": "Netzwerk-Kamera hinzufügen (RTSP / HTTP-Stream, WLAN-Kameras)",
    "Add": "Hinzufügen", "Automatic (first working USB camera)": "Automatisch (erste funktionierende USB-Kamera)",
    "+ Add schedule": "+ Zeitplan hinzufügen", "Edit schedule": "Zeitplan bearbeiten", "Edit": "Bearbeiten", "Days": "Tage",
    "From": "Von", "To": "Bis", "unchanged": "unverändert", "ON": "EIN", "OFF": "AUS", "Enabled": "Aktiv", "Save": "Speichern",
    "Cancel": "Abbrechen", "Features": "Funktionen", "no schedules": "keine Zeitpläne", "active now": "aktiv",
    "Open recordings preview (browser)": "Aufzeichnungs-Vorschau öffnen (Browser)",
    "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "starting": "startet",
    "connection lost - reconnecting": "Verbindung verloren - verbinde neu", "in use": "in Benutzung",
    "Name": "Name", "Network camera": "Netzwerk-Kamera", "every day": "täglich", "none": "keine",
    "Web stream could not start (is flask installed?)": "Web-Stream konnte nicht starten (ist flask installiert?)",
    "Time must look like 07:30": "Die Zeit muss so aussehen: 07:30",
    SCHED_NOTE: "Solange ein Zeitplan aktiv ist, werden die gewählten Funktionen fest EIN oder AUS geschaltet. Danach gilt wieder "
                "deine eigene Einstellung. Wer von Hand schaltet, überstimmt den Zeitplan bis zu dessen nächster Änderung.",
    "unknown source": "unbekannte Quelle", "unknown network camera": "unbekannte Netzwerk-Kamera",
    "invalid URL (rtsp:// or http:// expected)": "ungültige URL (rtsp:// oder http:// erwartet)",
    "too many network cameras": "zu viele Netzwerk-Kameras", "invalid schedule": "ungültiger Zeitplan",
    "unknown schedule": "unbekannter Zeitplan",
})
DE.update({
    "needs NetworkManager": "braucht NetworkManager", "paused (switched by hand)": "pausiert (von Hand geschaltet)",
    "own Wi-Fi on": "eigenes WLAN an", "searching known networks …": "suche bekannte Netze …",
    "Alarm & camping": "Alarm & Camping", "Detection": "Erkennung", "Camera & servos": "Kamera & Servos",
    "Recordings & timelapse": "Aufnahmen & Zeitraffer", "Thermal camera": "Wärmebild", "Relays & schedule": "Relais & Zeitplan",
    "System & network": "System & Netz", "Advanced": "Erweitert", "Notifications": "Benachrichtigungen",
    "Network": "Netzwerk", "Automatic: known networks (e.g. phone hotspot), otherwise own Wi-Fi": "Automatik: bekannte Netze (z. B. Handy-Hotspot), sonst eigenes WLAN",
    "Own Wi-Fi at boot": "Beim Hochfahren eigenes WLAN", "Only known networks": "Nur bekannte Netze",
    "Automatic: wait for a known network (s)": "Automatik: auf bekanntes Netz warten (s)",
    "Automatic: look for known networks every (min, 0 = never)": "Automatik: nach bekannten Netzen suchen alle (Min., 0 = nie)",
    "Autostart ON": "Autostart an", "Autostart OFF": "Autostart aus",
    "autostart needs systemd (Raspberry Pi OS)": "Autostart braucht systemd (Raspberry Pi OS)",
    "Camping / protection": "Camping / Schutz", "Armed (alarms)": "Scharf (Alarme)", "Thermal alarm": "Wärmebild-Alarm",
    "Take the clock from the phone (when the Pi has no internet time)": "Uhrzeit vom Handy übernehmen (wenn der Pi keine Internetzeit hat)",
    "Alarm when a warm body moves inside the zones": "Alarm, wenn sich ein warmer Körper in den Zonen bewegt",
    "Only warm bodies that move (ignore warm stones, engines)": "Nur bewegte warme Körper (warme Steine, Motoren ignorieren)",
    "Thermal alarm: warmer than the scene by (%)": "Wärmebild-Alarm: wärmer als die Umgebung um (%)",
    "Thermal alarm: minimum size (% of the picture)": "Wärmebild-Alarm: Mindestgrösse (% des Bildes)",
    "Arming countdown (s)": "Countdown bis scharf (s)", "Own Wi-Fi: name": "Eigenes WLAN: Name",
    "Own Wi-Fi: password (8-63 characters)": "Eigenes WLAN: Passwort (8-63 Zeichen)", "warm body (thermal camera)": "warmer Körper (Wärmebild)",
    "the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)": "das eigene WLAN braucht NetworkManager (Raspberry Pi OS Bookworm oder neuer)",
    "Armed": "Scharf", "Disarmed": "Unscharf", "Arm (countdown)": "Scharf (Countdown)", "Arm now": "Sofort scharf", "Disarm": "Unscharf schalten",
    "Camping profile": "Camping-Profil", "Camping ON": "Camping an", "Camping OFF": "Camping aus", "Own Wi-Fi ON": "Eigenes WLAN an",
    "Own Wi-Fi OFF": "Eigenes WLAN aus", "Armed in": "Scharf in", "devices": "Geräte", "Clock": "Uhrzeit",
    "Saved": "Gespeichert",
    "Wi-Fi / hotspot": "WLAN / Hotspot", "Search networks": "Netze suchen", "Connect now": "Jetzt verbinden",
    "Only save (connects automatically)": "Nur speichern (verbindet automatisch)", "Forget network": "Netz vergessen",
    "Password": "Passwort", "prefer this network": "dieses Netz bevorzugen", "Searching …": "Suche läuft …",
    "Push message with the address when the Pi joins a network": "Push-Nachricht mit der Adresse, wenn der Pi in ein Netz kommt",
    "set a web password first (--web-password) - otherwise anybody in the network could change the Wi-Fi":
        "zuerst ein Web-Passwort setzen (--web-password) - sonst könnte jeder im Netz das WLAN umstellen",
    "invalid network name": "ungültiger Netzname", "the password must have 8 to 63 characters": "das Passwort muss 8 bis 63 Zeichen haben",
    "busy": "beschäftigt - bitte kurz warten", "unknown network": "unbekanntes Netz",
    "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)": "WLAN-Verwaltung nicht verfügbar (NetworkManager / wpa_supplicant fehlt)",
    "could not connect (wrong password or too far away?)": "Verbindung nicht möglich (falsches Passwort oder zu weit weg?)",
    "calm": "ruhig", "breezy": "böig", "strong": "stark", "storm": "Sturm",
    "Alarm sound in the browser": "Alarmton im Browser",
    "Alarm sound in open browsers (switch on with the bell at the top)": "Alarmton in geöffneten Browsern (oben mit der Glocke einschalten)",
    "Wi-Fi": "WLAN", "not connected": "nicht verbunden", "Internet": "Internet", "online": "online", "offline": "offline",
    "Pre-alarm push": "Voralarm-Push", "Pre-alarm: min. time between messages (s)": "Voralarm: Mindestabstand zwischen Meldungen (s)",
    "Pre-alarm push: message at the first movement": "Voralarm-Push: Meldung bei der ersten Bewegung",
    "Pre-alarm push with a small picture": "Voralarm-Push mit kleinem Bild",
    "Timelapse": "Zeitraffer", "Thermal camera": "Wärmebildkamera", "Thermal overlay": "Wärmebild-Überlagerung",
    "Photo every N minutes": "Foto alle N Minuten", "Position: pan (%)": "Position: Schwenk (%)", "Position: tilt (%)": "Position: Neigung (%)",
    "Wait after moving (s)": "Wartezeit nach dem Fahren (s)", "Video: frames per second": "Video: Bilder pro Sekunde",
    "Max timelapse folder (GB)": "Max. Zeitraffer-Ordner (GB)", "Overlay strength": "Stärke der Überlagerung",
    "Hot areas only: warmest N percent": "Nur heisse Bereiche: wärmste N Prozent",
    "Timelapse active": "Zeitraffer aktiv", "Return to the previous position afterwards": "Danach zur vorherigen Position zurückfahren",
    "Overlay the thermal picture": "Wärmebild überlagern", "Show only the hot areas (people, animals, engines)": "Nur heisse Bereiche zeigen (Personen, Tiere, Motoren)",
    "Thermal camera (run the camera scan first)": "Wärmebildkamera (zuerst Kamera-Scan ausführen)", "Colours": "Farben",
    "inferno": "Inferno", "jet": "Jet", "hot": "Hot", "turbo": "Turbo", "grey": "Grau",
    "pre-alarm (any movement)": "Voralarm (jede Bewegung)",
    "Use current position": "Aktuelle Position übernehmen", "Photo now": "Foto jetzt", "Create video": "Video erstellen",
    "need at least 2 photos": "mindestens 2 Fotos nötig", "a video is already being made": "es wird schon ein Video erstellt",
    "next photo in": "nächstes Foto in", "making video": "Video wird erstellt", "off": "aus", "waiting: alarm has priority": "wartet: Alarm hat Vorrang", "waiting: manual control": "wartet: Handsteuerung",
    "moving to the photo position": "fährt zur Fotoposition", "photo saved": "Foto gespeichert",
    "no thermal camera selected": "keine Wärmebildkamera gewählt", "same camera as the main picture": "gleiche Kamera wie das Hauptbild",
    "connecting…": "verbinde …",
})


def tl_status_text(text):
    """Status strings with numbers (timelapse) for the desktop window."""
    m = re.fullmatch(r"next photo in (\d+) min", text or "")
    if m:
        return (tr("next photo in") + " " + m.group(1) + " min") if CFG["lang"] == "de" else text
    m = re.fullmatch(r"making video (\d+)/(\d+)", text or "")
    if m:
        return (tr("making video") + " " + m.group(1) + "/" + m.group(2)) if CFG["lang"] == "de" else text
    return tr(text)


def tr_err(msg, lang=None):
    """Translate a relay error message (some contain numbers)."""
    if (lang or CFG.get("lang", "en")) != "de":
        return msg
    if msg.startswith("autostart is on, but it only starts after a login"):
        return "Autostart ist an, startet aber erst nach einer Anmeldung, bis du einmal ausführst: " + msg.split("run once: ", 1)[-1].replace("(or: ", "(oder: ")
    if msg.startswith("a system service exists"):
        return "Es gibt einen System-Dienst - ändern mit sudo oder entfernen: sudo systemctl disable --now motionwatch"
    if msg.startswith("the system service can only be switched off with sudo"):
        return "Der System-Dienst lässt sich nur mit sudo ausschalten: sudo systemctl disable motionwatch"
    if msg.startswith("no permission to change Wi-Fi"):
        return "keine Berechtigung, das WLAN zu ändern - Programm mit sudo starten oder einmalig erlauben mit: " + msg.split("with: ", 1)[-1]
    for pat, de in ((r"GPIO (\d+) is used by a servo", r"GPIO \1 wird von einem Servo benutzt"),
                    (r"GPIO (\d+) is already used by another relay", r"GPIO \1 wird schon von einem anderen Relais benutzt"),
                    (r"maximum (\d+) relays", r"maximal \1 Relais"),
                    (r"maximum (\d+) schedules", r"maximal \1 Zeitpläne"),
                    (r"maximum (\d+) extra cameras", r"maximal \1 Zusatzkameras")):
        if re.fullmatch(pat, msg):
            return re.sub(pat, de, msg)
    return DE.get(msg, msg)


def tr(text, lang=None):
    """Translate an English UI string into the current language (falls back to English)."""
    if (lang or CFG.get("lang", "en")) == "de":
        return DE.get(text, text)
    return text


THEMES = {
    "dark": {"bg": "#0b0f14", "panel": "#121923", "line": "#1f2a38", "txt": "#e6edf3", "mut": "#8b9bb0",
             "acc": "#2f81f7", "red": "#ff3b3b", "grn": "#3fb950", "yel": "#d29922", "blu": "#58a6ff", "org": "#f0883e",
             "pur": "#bc8cff", "field": "#0f151d", "knob_off": "#2a3542", "badge_red_bg": "#1a1216"},
    "light": {"bg": "#eef1f5", "panel": "#ffffff", "line": "#d0d7e2", "txt": "#1b2430", "mut": "#5b6b7f",
              "acc": "#1f6feb", "red": "#d1242f", "grn": "#1a7f37", "yel": "#9a6700", "blu": "#0969da", "org": "#bc4c00",
              "pur": "#8250df", "field": "#f3f5f8", "knob_off": "#c4ccd8", "badge_red_bg": "#ffecec"},
}


# ----------------------------------------------------------------------------
# Desktop GUI (Tkinter) - optional, so --headless works without Tkinter/Pillow
# ----------------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from PIL import Image, ImageTk
    GUI_OK, GUI_ERR = True, ""
except ImportError as _e:
    GUI_OK, GUI_ERR = False, str(_e)

    class tk:                       # minimal stand-in so the class definitions below still load
        Frame = object

C = dict(THEMES["dark"])


def apply_theme():
    C.clear(); C.update(THEMES.get(CFG.get("theme", "dark"), THEMES["dark"]))


def kind_colors():
    return {"person": C["red"], "rain": C["blu"], "wind": C["yel"], "car": C["mut"], "rec": C["grn"],
            "auto": C["org"], "ai": C["pur"], "servo": C["acc"], "patrol": C["acc"], "web": C["mut"], "sys": C["mut"], "sched": C["pur"]}

DAYS_SHORT_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DAYS_SHORT_DE = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
SLIDERS = [  # (section, key, label, min, max, step)
    ("Camera / Servos", "pan", "Pan (%)", 0, 100, 1),
    ("Camera / Servos", "tilt", "Tilt (%)", 0, 100, 1),
    ("Camera / Servos", "track_gain", "Tracking gain", 0.1, 2.0, 0.1),
    ("Camera / Servos", "track_deadzone", "Tracking dead zone", 0.02, 0.3, 0.01),
    ("Camera / Servos", "manual_hold", "Manual control pause (s)", 0, 60, 1),
    ("Patrol", "patrol_dwell", "Dwell at waypoint (s)", 0, 15, 0.5),
    ("Patrol", "patrol_speed", "Patrol speed (%/s)", 5, 100, 5),
    ("Patrol", "patrol_tilt", "Patrol tilt (%)", 0, 100, 1),
    ("AI detection", "ai_conf", "Confidence threshold", 0.2, 0.95, 0.05),
    ("AI detection", "ai_every", "Run every N frames", 1, 10, 1),
    ("AI detection", "object_conf", "Object confidence", 0.2, 0.95, 0.05),
    ("Web stream", "web_quality", "JPEG quality", 30, 95, 5),
    ("Web stream", "web_width", "Stream width (px)", 320, 1920, 80),
    ("Auto-tune", "walk_seconds", "Walking time needed (s)", 0.3, 3.0, 0.1),
    ("Detection", "sensitivity", "Sensitivity", 0, 100, 1),
    ("Detection", "shadow_ratio_max", "Shadow: max brightness ratio", 0.6, 0.98, 0.01),
    ("Detection", "shadow_ratio_min", "Shadow: min brightness ratio", 0.1, 0.6, 0.01),
    ("Detection", "min_area", "Min object size (px²)", 300, 8000, 100),
    ("Walking recognition", "walk_frames", "Frames of steady motion", 3, 30, 1),
    ("Walking recognition", "walk_min_speed", "Min speed (px/frame)", 0.1, 5.0, 0.1),
    ("Walking recognition", "walk_max_speed", "Max speed (px/frame)", 5, 60, 1),
    ("Walking recognition", "speed_consistency", "Speed consistency", 0.0, 1.0, 0.05),
    ("Vehicle filter", "car_aspect", "Vehicle aspect ratio", 1.0, 3.0, 0.05),
    ("Vehicle filter", "car_speed", "Vehicle speed (px/frame)", 5, 40, 1),
    ("Rain", "rain_threshold", "Rain threshold", 0.05, 1.0, 0.05),
    ("Wind", "wind_threshold", "Wind threshold", 0.05, 1.0, 0.05),
    ("Wind", "wind_boost_max", "Max trigger boost", 1.0, 8.0, 0.5),
    ("Recording", "record_tail", "Keep recording after (s)", 0, 15, 0.5),
    ("Recording", "pre_roll", "Pre-roll: video before the detection (s)", 0, 10, 0.5),
    ("Setup", "away_after", "Away after N minutes without answer", 2, 60, 1),
    ("Recording", "record_max_gb", "Max recordings folder (GB)", 0.5, 64, 0.5),
    ("Low light", "lowlight_threshold", "Low-light threshold (brightness)", 10, 150, 5),
    ("Notifications", "notify_cooldown", "Cooldown between alarms (s)", 5, 600, 5),
    ("Notifications", "prealarm_cooldown", "Pre-alarm: min. time between messages (s)", 30, 1800, 30),
    ("Timelapse", "timelapse_interval", "Photo every N minutes", 1, 720, 1),
    ("Timelapse", "timelapse_pan", "Position: pan (%)", 0, 100, 1),
    ("Timelapse", "timelapse_tilt", "Position: tilt (%)", 0, 100, 1),
    ("Timelapse", "timelapse_settle", "Wait after moving (s)", 1, 15, 0.5),
    ("Timelapse", "timelapse_fps", "Video: frames per second", 5, 60, 1),
    ("Timelapse", "timelapse_max_gb", "Max timelapse folder (GB)", 0.5, 64, 0.5),
    ("Thermal camera", "thermal_alpha", "Overlay strength", 0.1, 1.0, 0.05),
    ("Thermal camera", "thermal_hot_pct", "Hot areas only: warmest N percent", 50, 99, 1),
    ("Thermal camera", "thermal_delta", "Thermal alarm: warmer than the scene by (%)", 10, 60, 1),
    ("Thermal camera", "thermal_min_area", "Thermal alarm: minimum size (% of the picture)", 0.1, 5, 0.1),
    ("Camping / protection", "arm_delay", "Arming countdown (s)", 0, 300, 5),
    ("Camping / protection", "auto_wait", "Automatic: wait for a known network (s)", 20, 300, 10),
    ("Camping / protection", "auto_retry", "Automatic: look for known networks every (min, 0 = never)", 0, 60, 1),
]
TOGGLES = [  # (section, key, label)
    ("Camera / Servos", "track_person", "Follow detected person (auto pan/tilt)"),
    ("Camera / Servos", "invert_pan", "Invert pan direction"),
    ("Camera / Servos", "invert_tilt", "Invert tilt direction"),
    ("Patrol", "patrol", "Pendulum patrol active"),
    ("AI detection", "ai_enabled", "AI person detection (SSD MobileNet V2)"),
    ("AI detection", "show_objects", "Mark all detected objects (cars, animals, ...)"),
    ("AI detection", "ai_require", "Motion persons need AI confirmation"),
    ("Web stream", "web_stream", "Web stream + remote control (port 5000)"),
    ("Auto-tune", "auto_tune", "Automatic tuning"),
    ("Detection", "detection_on", "Detection (master switch)"),
    ("Detection", "highlight_red", "Highlight persons red"),
    ("Detection", "show_tracks", "Show movement tracks"),
    ("Detection", "show_mask", "Show motion mask"),
    ("Detection", "show_hud", "Show HUD overlay"),
    ("Detection", "show_zones", "Show zones in the picture"),
    ("Detection", "shadow_filter", "Shadow filter (ignore person shadows)"),
    ("Walking recognition", "person_sticky", "Keep person flagged while tracked"),
    ("Vehicle filter", "car_filter", "Ignore cars / vehicles"),
    ("Rain", "rain_auto", "Auto rain detection"),
    ("Rain", "rain_mode", "Rain mode (manual, if auto off)"),
    ("Wind", "wind_auto", "Auto wind detection"),
    ("Recording", "record", "Record when person seen"),
    ("Recording", "snapshot_on_person", "Save snapshot JPG per detection"),
    ("Low light", "lowlight_auto", "Auto low-light mode (contrast boost)"),
    ("Relays", "relays_on", "Auto relays enabled"),
    ("Notifications", "notify_on", "Send notifications"),
    ("Notifications", "notify_prealarm", "Pre-alarm push: message at the first movement"),
    ("Notifications", "prealarm_photo", "Pre-alarm push with a small picture"),
    ("Notifications", "browser_alarm", "Alarm sound in open browsers (switch on with the bell at the top)"),
    ("Notifications", "notify_network", "Push message with the address when the Pi joins a network"),
    ("Camping / protection", "time_from_browser", "Take the clock from the phone (when the Pi has no internet time)"),
    ("Thermal camera", "thermal_alarm", "Alarm when a warm body moves inside the zones"),
    ("Thermal camera", "thermal_need_motion", "Only warm bodies that move (ignore warm stones, engines)"),
    ("Timelapse", "timelapse_on", "Timelapse active"),
    ("Timelapse", "timelapse_return", "Return to the previous position afterwards"),
    ("Thermal camera", "thermal_on", "Overlay the thermal picture"),
    ("Thermal camera", "thermal_hot", "Show only the hot areas (people, animals, engines)"),
]
TK_GROUPS = [  # (id, icon, name, sections, advanced sections) - the desktop window shows no icons (Tk 8.6 lacks colour emoji)
    ("alarm", "", "Alarm & camping", ["Camping / protection"], []),
    ("notify", "", "Notifications", ["Notifications"], []),
    ("detect", "", "Detection", ["Detection", "AI detection"], ["Walking recognition", "Vehicle filter", "Rain", "Wind", "Low light", "Auto-tune"]),
    ("camera", "", "Camera & servos", ["Camera / Servos", "Patrol", "Video source"], []),
    ("rec", "", "Recordings & timelapse", ["Recording", "Timelapse"], []),
    ("thermal", "", "Thermal camera", ["Thermal camera"], []),
    ("relay", "", "Relays & schedule", ["Relays", "Schedule"], []),
    ("sys", "", "System & network", ["Wi-Fi / hotspot", "Web stream", "Setup"], []),
]
SECTIONS = ["Camping / protection", "Camera / Servos", "Video source", "Wi-Fi / hotspot", "Schedule", "Relays", "Timelapse", "Thermal camera", "Patrol", "AI detection", "Notifications", "Web stream", "Auto-tune",
            "Detection", "Low light", "Walking recognition", "Vehicle filter", "Rain", "Wind", "Recording", "Setup"]


class Toggle(tk.Frame):
    """Clear on/off switch: blue pill with the knob on the right = ON, grey with knob left = OFF."""
    def __init__(self, parent, text, value, command):
        super().__init__(parent, bg=C["panel"])
        self.command = command; self.value = bool(value)
        self.cv = tk.Canvas(self, width=44, height=24, bg=C["panel"], bd=0, highlightthickness=0, cursor="hand2")
        self.cv.pack(side="right")
        self.lbl = tk.Label(self, text=text, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), anchor="w", cursor="hand2",
                            justify="left", wraplength=290)
        self.lbl.pack(side="left", fill="x", expand=True)
        for w in (self.cv, self.lbl):
            w.bind("<Button-1>", self._click)
        self._draw()

    def _draw(self):
        c = self.cv; c.delete("all")
        col = C["acc"] if self.value else C["knob_off"]
        c.create_oval(2, 2, 22, 22, fill=col, outline=col); c.create_oval(22, 2, 42, 22, fill=col, outline=col)
        c.create_rectangle(12, 2, 32, 22, fill=col, outline=col)
        x = 32 if self.value else 12
        c.create_oval(x - 8, 4, x + 8, 20, fill="#ffffff", outline="#ffffff")
        self.lbl.config(fg=C["txt"] if self.value else C["mut"])

    def _click(self, _e=None):
        self.set(not self.value); self.command(self.value)

    def set(self, value):
        value = bool(value)
        if value != self.value:
            self.value = value; self._draw()

    def get(self):
        return self.value


# every field of the desktop window can be shown / hidden individually (right-click the video or the ☰ button)
VIEW_GROUPS = ["Header", "Statistics", "Panels", "Settings sections"]
VIEW_ITEMS = [  # (group, key, label)
    ("Header", "title", "Title"), ("Header", "hdr_buttons", "Header buttons"),
    ("Header", "b_person", "Persons"), ("Header", "b_count", "Persons total"), ("Header", "b_objects", "Objects"),
    ("Header", "b_rain", "Rain"), ("Header", "b_wind", "Wind"), ("Header", "b_rec", "Recording"),
    ("Header", "b_relays", "Relays"), ("Header", "b_patrol", "Patrol"), ("Header", "b_light", "Light level"),
    ("Header", "b_auto", "Auto-tune"), ("Header", "b_fps", "FPS"), ("Header", "b_arm", "Armed / disarmed"),
    ("Statistics", "s_fps", "FPS"), ("Statistics", "s_persons", "Persons now"), ("Statistics", "s_objects", "Objects"),
    ("Statistics", "s_det", "Detections"), ("Statistics", "s_veh", "Vehicles ignored"),
    ("Statistics", "s_shadow", "Shadow % removed"),
    ("Panels", "controls", "Camera control"), ("Panels", "weather", "Weather"), ("Panels", "cpu", "System · CPU"),
    ("Panels", "log", "Event log"), ("Panels", "settings_line", "Settings status"),
] + [("Settings sections", "sec:" + s, s) for s in SECTIONS]
STAT_TILES = [("s_fps", "fps", "FPS"), ("s_persons", "persons", "PERSONS NOW"), ("s_objects", "objects", "OBJECTS"),
              ("s_det", "detections_total", "DETECTIONS"), ("s_veh", "ignored_vehicles", "VEHICLES IGNORED"),
              ("s_shadow", "shadow_pct", "SHADOW % REMOVED")]
TYPING = ("Entry", "TEntry", "Spinbox", "TSpinbox", "TCombobox", "TScale", "Listbox")


class Seg(tk.Frame):
    """Segmented Off / On / Auto switch for one relay."""
    MODES = ("off", "on", "auto")

    def __init__(self, parent, value, command, small=False):
        super().__init__(parent, bg=C["line"], padx=1, pady=1)
        self.command = command; self.value = None; self.btn = {}
        for m in self.MODES:
            l = tk.Label(self, text=tr(m.capitalize()), font=("DejaVu Sans", 8 if small else 9, "bold"),
                         padx=6 if small else 9, pady=1 if small else 3, cursor="hand2")
            l.pack(side="left", padx=(0 if m == "off" else 1, 0))
            l.bind("<Button-1>", lambda e, mm=m: self._click(mm))
            self.btn[m] = l
        self.set(value)

    def _click(self, m):
        if m != self.value:
            self.set(m); self.command(m)

    def set(self, value):
        if value == self.value:
            return
        self.value = value
        col = {"off": C["mut"], "on": C["grn"], "auto": C["acc"]}
        for m, l in self.btn.items():
            l.config(bg=col[m] if m == value else C["field"], fg="#ffffff" if m == value else C["mut"])


class App:
    def __init__(self, watch, web=None):
        self.watch = watch
        self.web = web or WebStream(watch)
        self.root = tk.Tk()
        self.root.title("Motion Watch 1.7.4")
        self.root.geometry("1360x820"); self.root.minsize(900, 560)
        self.video_only = False; self.is_fullscreen = False; self.photo = None
        self.open_secs = set(CFG["ui_open"])                    # open sidebar groups: kept in the settings file
        if not any(x.startswith("grp:") for x in self.open_secs):   # settings of an older version: start with "Alarm & camping" open
            self.open_secs = {"grp:alarm"}
        self.step_var = tk.StringVar(value="3")
        self.relay_err = ""; self._err_job = None; self._rb_pending = False; self._hold_job = None
        self.right_f = self.side_canvas = None
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        self.root.bind("<Control-t>", lambda e: self.toggle_theme())
        self.root.bind("<Control-l>", lambda e: self.toggle_lang())
        self.root.bind("<Control-b>", lambda e: self.toggle_sidebar())
        for key, cmd in (("<Left>", "left"), ("<Right>", "right"), ("<Up>", "up"), ("<Down>", "down"), ("<Home>", "center")):
            self.root.bind_all(key, lambda e, c=cmd: self._key_move(c))
        self.root.bind_all("<Button-4>", lambda e: self._wheel(e, -1))
        self.root.bind_all("<Button-5>", lambda e: self._wheel(e, 1))
        self.root.bind_all("<MouseWheel>", lambda e: self._wheel(e, -1 if e.delta > 0 else 1))
        self._rebuild()
        if CFG.get("fullscreen"):
            self.toggle_fullscreen()
        self.root.after(30, self._update_video); self.root.after(500, self._update_state)

    # ---- (re)building the window ----------------------------------------
    def _rebuild(self):
        """(Re)create the whole window content - theme, language, shown/hidden fields, relays."""
        apply_theme()
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=C["bg"])
        self.vars, self.value_labels, self.status_labels = {}, {}, {}
        self.sections = {}
        self.dragging = None; self._last_ev = None
        self._style(); self._build()

    def _schedule_rebuild(self):
        if not self._rb_pending:
            self._rb_pending = True
            self.root.after(10, self._do_rebuild)

    def _do_rebuild(self):
        self._rb_pending = False; self._rebuild()

    def is_shown(self, key):
        return key not in CFG["ui_hidden"]

    def set_hidden(self, key, hide):
        CFG["ui_hidden"] = [k for k in CFG["ui_hidden"] if k != key] + ([key] if hide else [])
        save_settings(); self._schedule_rebuild()

    def show_all(self):
        CFG["ui_hidden"] = []; save_settings(); self._schedule_rebuild()

    def toggle_sidebar(self):
        self.set_hidden("sidebar", self.is_shown("sidebar"))

    def toggle_theme(self):
        self._set("theme", "light" if CFG["theme"] == "dark" else "dark"); self._rebuild()

    def toggle_lang(self):
        self._set("lang", "de" if CFG["lang"] == "en" else "en"); self._rebuild()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen); CFG["fullscreen"] = self.is_fullscreen
        if self.b_fs is not None:
            self.b_fs.config(text="⛶ " + (tr("Exit fullscreen (Esc)") if self.is_fullscreen else tr("Fullscreen (F11)")))

    def exit_fullscreen(self):
        if self.video_only:
            self.toggle_video_only()
        if self.is_fullscreen:
            self.toggle_fullscreen()

    def toggle_video_only(self):
        """Double-click the video: only the live picture, nothing else."""
        self.video_only = not self.video_only; self._rebuild()

    def _view_menu(self, x=None, y=None):
        kw = dict(tearoff=0, bg=C["panel"], fg=C["txt"], activebackground=C["acc"], activeforeground="#ffffff",
                  selectcolor=C["acc"], bd=1, relief="solid", font=("DejaVu Sans", 10))
        m = tk.Menu(self.root, **kw)
        self.view_vars = {}
        for g in VIEW_GROUPS:
            sub = tk.Menu(m, **kw)
            for grp, key, label in VIEW_ITEMS:
                if grp == g:
                    v = tk.BooleanVar(value=self.is_shown(key)); self.view_vars[key] = v
                    sub.add_checkbutton(label=tr(label), variable=v, command=lambda k=key, vv=v: self.set_hidden(k, not vv.get()))
            m.add_cascade(label=tr(g), menu=sub)
        m.add_separator()
        sv = tk.BooleanVar(value=self.is_shown("sidebar")); self.view_vars["sidebar"] = sv
        m.add_checkbutton(label=tr("Settings panel") + "   (Ctrl+B)", variable=sv, command=self.toggle_sidebar)
        m.add_command(label=tr("Show all"), command=self.show_all)
        if x is None:
            x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()

    def _style(self):
        s = ttk.Style(self.root); s.theme_use("clam")
        s.configure(".", background=C["panel"], foreground=C["txt"], font=("DejaVu Sans", 10))
        s.configure("TFrame", background=C["panel"]); s.configure("Bg.TFrame", background=C["bg"])
        s.configure("TLabel", background=C["panel"], foreground=C["txt"])
        s.configure("Mut.TLabel", foreground=C["mut"], font=("DejaVu Sans", 8))
        s.configure("Head.TLabel", foreground=C["mut"], font=("DejaVu Sans", 8, "bold"))
        s.configure("Bold.TLabel", font=("DejaVu Sans", 11, "bold"))
        s.configure("Title.TLabel", background=C["bg"], foreground=C["txt"], font=("DejaVu Sans", 14, "bold"))
        s.configure("Sub.TLabel", background=C["bg"], foreground=C["mut"], font=("DejaVu Sans", 8))
        s.configure("Stat.TLabel", font=("DejaVu Sans", 16, "bold"))
        s.configure("Horizontal.TScale", background=C["panel"], troughcolor=C["line"], sliderlength=16)
        s.configure("TProgressbar", troughcolor=C["line"], background=C["blu"], thickness=6)
        s.configure("Wind.Horizontal.TProgressbar", troughcolor=C["line"], background=C["yel"], thickness=6)
        for nm, col in (("CpuG", C["grn"]), ("CpuY", C["yel"]), ("CpuR", C["red"])):
            s.configure(f"{nm}.Horizontal.TProgressbar", troughcolor=C["line"], background=col, thickness=8)
        s.configure("TButton", background=C["acc"], foreground="#fff", borderwidth=0, font=("DejaVu Sans", 9, "bold"))
        s.map("TButton", background=[("active", "#4a93ff")])
        s.configure("Sec.TButton", background=C["line"], foreground=C["txt"])
        s.map("Sec.TButton", background=[("active", C["knob_off"])])
        s.configure("Vertical.TScrollbar", background=C["line"], troughcolor=C["panel"], arrowcolor=C["mut"])
        s.configure("TCombobox", fieldbackground=C["field"], background=C["line"], foreground=C["txt"], arrowcolor=C["txt"])
        s.map("TCombobox", fieldbackground=[("readonly", C["field"])], foreground=[("readonly", C["txt"])],
              selectbackground=[("readonly", C["field"])], selectforeground=[("readonly", C["txt"])])
        for opt, val in (("background", C["field"]), ("foreground", C["txt"]),
                         ("selectBackground", C["acc"]), ("selectForeground", "#ffffff")):
            self.root.option_add(f"*TCombobox*Listbox.{opt}", val)

    def _badge(self, parent, text):
        return tk.Label(parent, text=text, bg=C["field"], fg=C["mut"], font=("DejaVu Sans", 9, "bold"),
                        padx=10, pady=4, highlightthickness=1, highlightbackground=C["line"])

    def _sb(self, key, text, color=None):
        lbl = self.badges.get(key)
        if lbl is not None:
            lbl.config(text=text, fg=color or C["mut"], highlightbackground=color or C["line"],
                       bg=(C["badge_red_bg"] if color == C["red"] else C["field"]))

    def _flow(self, _e=None):
        """Badges wrap onto a second line when the window is narrow."""
        f = self.badge_f
        if f is None or not f.winfo_exists():
            return
        W = max(f.winfo_width(), 200); x = y = rowh = 0
        for w in self.badges.values():
            ww, hh = w.winfo_reqwidth(), w.winfo_reqheight()
            if x and x + ww > W:
                x = 0; y += rowh + 6; rowh = 0
            w.place(x=x, y=y); x += ww + 8; rowh = max(rowh, hh)
        if int(f.cget("height")) != y + rowh:
            f.configure(height=y + rowh)

    def _panel(self, parent):
        return tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=10)

    def _build(self):
        r = self.root
        self.stat, self.badges = {}, {}
        self.badge_f = self.b_fs = self.video = None
        self.p_rain = self.p_wind = self.l_rain = self.l_wind = self.l_boost = None
        self.l_cpu = self.p_cpu = self.cpu_canvas = self.l_cpu_info = self.log = None
        self.l_wifi = None; self.wifi_canvas = None
        self.l_pt = self.l_ctl_status = self.l_settings = None
        self.right_f = self.side_canvas = None
        self.relay_segs, self.relay_dots, self.relay_err_labels = {}, {}, []
        self._built_sig = self._relay_sig()
        if self.video_only:
            self.video = tk.Label(r, bg="#000", bd=0, cursor="hand2"); self.video.pack(fill="both", expand=True)
            self.video.bind("<Double-Button-1>", lambda e: self.toggle_video_only())
            self.video.bind("<Button-3>", lambda e: self._view_menu(e.x_root, e.y_root))
            return
        self._build_header()
        body = ttk.Frame(r, style="Bg.TFrame"); body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        body.columnconfigure(0, weight=1); body.rowconfigure(0, weight=1)
        left = ttk.Frame(body, style="Bg.TFrame"); left.grid(row=0, column=0, sticky="nsew")
        side_open = self.is_shown("sidebar")
        strip = tk.Frame(body, bg=C["bg"]); strip.grid(row=0, column=1, sticky="ns", padx=6)
        for txt, cmd in (("▶" if side_open else "◀", self.toggle_sidebar), ("☰", self._view_menu)):
            l = tk.Label(strip, text=txt, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11, "bold"), width=2, pady=6,
                         cursor="hand2", highlightthickness=1, highlightbackground=C["line"])
            l.pack(pady=(0, 6)); l.bind("<Button-1>", lambda e, c=cmd: c())
        self._build_left(left)
        if side_open:
            self._build_sidebar(body)

    def _build_header(self):
        show = self.is_shown
        badge_keys = [k for g, k, l in VIEW_ITEMS if g == "Header" and k.startswith("b_")]
        if not (show("title") or show("hdr_buttons") or any(show(k) for k in badge_keys)):
            return
        head = ttk.Frame(self.root, style="Bg.TFrame"); head.pack(fill="x", padx=16, pady=(12, 6))
        top = ttk.Frame(head, style="Bg.TFrame"); top.pack(fill="x")
        if show("title"):
            t = ttk.Frame(top, style="Bg.TFrame"); t.pack(side="left")
            ttk.Label(t, text="Motion Watch", style="Title.TLabel").pack(anchor="w")
            ttk.Label(t, text=f"{tr('Build')} 1.7.4 · {tr('Pan/Tilt surveillance with AI, patrol & relay')}", style="Sub.TLabel").pack(anchor="w")
        if show("hdr_buttons"):
            ctl = ttk.Frame(top, style="Bg.TFrame"); ctl.pack(side="right", anchor="n")
            vb = ttk.Button(ctl, text="☰ " + tr("View"), style="Sec.TButton")
            vb.config(command=lambda: self._view_menu(vb.winfo_rootx(), vb.winfo_rooty() + vb.winfo_height()))
            vb.pack(side="left", padx=(0, 4))
            ttk.Button(ctl, text=("⇥ " if show("sidebar") else "⇤ ") + tr("Settings panel"), style="Sec.TButton",
                       command=self.toggle_sidebar).pack(side="left", padx=(0, 4))
            self.b_fs = ttk.Button(ctl, text="⛶ " + (tr("Exit fullscreen (Esc)") if self.is_fullscreen else tr("Fullscreen (F11)")),
                                   command=self.toggle_fullscreen); self.b_fs.pack(side="left", padx=(0, 4))
            ttk.Button(ctl, text=("☀ " + tr("Light")) if CFG["theme"] == "dark" else ("☾ " + tr("Dark")),
                       command=self.toggle_theme).pack(side="left", padx=(0, 4))
            ttk.Button(ctl, text="DE" if CFG["lang"] == "en" else "EN", command=self.toggle_lang).pack(side="left")
        keys = [k for k in badge_keys if show(k)]
        if keys:
            self.badge_f = tk.Frame(head, bg=C["bg"], height=30); self.badge_f.pack(fill="x", pady=(6, 0))
            texts = {"b_person": tr("No person"), "b_count": f"{tr('Persons total')}: 0", "b_objects": f"0 {tr('objects')}",
                     "b_rain": tr("No rain"), "b_wind": f"{tr('Wind')}: calm", "b_rec": tr("Idle"), "b_relays": tr("Relays"),
                     "b_patrol": tr("Patrol off"), "b_light": tr("Light ok"), "b_auto": tr("Auto-tune"), "b_fps": "– FPS", "b_arm": "🛡"}
            for k in keys:
                self.badges[k] = self._badge(self.badge_f, texts[k])
            if "b_count" in self.badges:
                self.badges["b_count"].bind("<Button-1>", lambda e: self._reset_count())
            self.badge_f.bind("<Configure>", self._flow)
            self.root.after(50, self._flow)

    def _build_left(self, left):
        show = self.is_shown
        left.columnconfigure(0, weight=1)
        self.video = tk.Label(left, bg="#000", bd=0, highlightthickness=1, highlightbackground=C["line"], cursor="hand2")
        self.video.grid(row=0, column=0, sticky="nsew"); left.rowconfigure(0, weight=1)    # the picture gets all spare room
        self.video.bind("<Double-Button-1>", lambda e: self.toggle_video_only())
        self.video.bind("<Button-3>", lambda e: self._view_menu(e.x_root, e.y_root))
        row = 1
        tiles = [t for t in STAT_TILES if show(t[0])]
        if tiles:
            stats = ttk.Frame(left, style="Bg.TFrame"); stats.grid(row=row, column=0, sticky="ew", pady=(8, 0)); row += 1
            for i, (vk, k, lab) in enumerate(tiles):
                f = tk.Frame(stats, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=8)
                f.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0)); stats.columnconfigure(i, weight=1)
                ttk.Label(f, text=tr(lab), style="Head.TLabel").pack(anchor="w")
                self.stat[k] = ttk.Label(f, text="–", style="Stat.TLabel"); self.stat[k].pack(anchor="w")
        if show("controls"):
            c = self._panel(left); c.grid(row=row, column=0, sticky="ew", pady=(8, 0)); row += 1
            self._build_controls(c)
        ws, cs = show("weather"), show("cpu")
        if ws or cs:
            mid = ttk.Frame(left, style="Bg.TFrame"); mid.grid(row=row, column=0, sticky="ew", pady=(8, 0)); row += 1
            col = 0
            if ws:
                wx = self._panel(mid); wx.grid(row=0, column=col, sticky="nsew"); wx.columnconfigure(1, weight=1)
                mid.columnconfigure(col, weight=3); col += 1
                ttk.Label(wx, text=tr("WEATHER"), style="Head.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
                ttk.Label(wx, text=tr("Rain score")).grid(row=1, column=0, sticky="w")
                self.p_rain = ttk.Progressbar(wx, maximum=1.0); self.p_rain.grid(row=1, column=1, sticky="ew", padx=10)
                self.l_rain = ttk.Label(wx, text="0.00", style="Mut.TLabel", width=6); self.l_rain.grid(row=1, column=2)
                ttk.Label(wx, text=tr("Wind score")).grid(row=2, column=0, sticky="w", pady=(4, 0))
                self.p_wind = ttk.Progressbar(wx, maximum=1.0, style="Wind.Horizontal.TProgressbar")
                self.p_wind.grid(row=2, column=1, sticky="ew", padx=10, pady=(4, 0))
                self.l_wind = ttk.Label(wx, text="0.00", style="Mut.TLabel", width=6); self.l_wind.grid(row=2, column=2, pady=(4, 0))
                ttk.Label(wx, text=tr("Trigger multiplier (wind)")).grid(row=3, column=0, sticky="w", pady=(4, 0))
                self.l_boost = ttk.Label(wx, text="x1.0", style="Mut.TLabel"); self.l_boost.grid(row=3, column=1, sticky="w", padx=10, pady=(4, 0))
            if cs:
                sysf = self._panel(mid); sysf.grid(row=0, column=col, sticky="nsew", padx=(8 if col else 0, 0))
                mid.columnconfigure(col, weight=2)
                ttk.Label(sysf, text=tr("SYSTEM · CPU"), style="Head.TLabel").pack(anchor="w")
                self.l_cpu = ttk.Label(sysf, text="–", style="Stat.TLabel"); self.l_cpu.pack(anchor="w")
                self.p_cpu = ttk.Progressbar(sysf, maximum=100, style="CpuG.Horizontal.TProgressbar"); self.p_cpu.pack(fill="x", pady=(2, 4))
                self.cpu_canvas = tk.Canvas(sysf, height=34, bg=C["field"], bd=0, highlightthickness=0); self.cpu_canvas.pack(fill="x")
                self.l_cpu_info = ttk.Label(sysf, text="", style="Mut.TLabel"); self.l_cpu_info.pack(anchor="w", pady=(4, 0))
                self.l_wifi = ttk.Label(sysf, text="", style="Mut.TLabel", wraplength=300, justify="left"); self.l_wifi.pack(anchor="w", pady=(4, 0))
                self.wifi_canvas = tk.Canvas(sysf, height=34, bg=C["field"], bd=0, highlightthickness=0); self.wifi_canvas.pack(fill="x", pady=(2, 0))
        if show("log"):
            logf = self._panel(left); logf.grid(row=row, column=0, sticky="nsew", pady=(8, 0)); row += 1
            ttk.Label(logf, text=tr("EVENT LOG"), style="Head.TLabel").pack(anchor="w")
            self.log = tk.Text(logf, bg=C["panel"], fg=C["txt"], bd=0, highlightthickness=0, height=6,
                               font=("DejaVu Sans Mono", 9), state="disabled", wrap="none", takefocus=0)
            self.log.config(height=5)
            self.log.pack(fill="both", expand=True, pady=(6, 0))
            for k, colr in kind_colors().items():
                self.log.tag_configure(k, foreground=colr)
            self.log.tag_configure("t", foreground=C["mut"])
        if show("settings_line"):
            self.l_settings = ttk.Label(left, text="", style="Sub.TLabel"); self.l_settings.grid(row=row, column=0, sticky="w", pady=(6, 0))

    # ---- camera control panel (directly under the picture) --------------
    def _build_controls(self, f):
        ttk.Label(f, text=tr("CAMERA CONTROL"), style="Head.TLabel").pack(anchor="w", pady=(0, 6))
        inner = tk.Frame(f, bg=C["panel"]); inner.pack(fill="x")
        pad = tk.Frame(inner, bg=C["panel"]); pad.pack(side="left", anchor="n")
        for rr, cc, txt, cmd in ((0, 1, "▲", "up"), (1, 0, "◀", "left"), (1, 1, "●", "center"), (1, 2, "▶", "right"), (2, 1, "▼", "down")):
            mid = cmd == "center"
            b = tk.Label(pad, text=txt, width=3, font=("DejaVu Sans", 13, "bold"), pady=3, cursor="hand2",
                         bg=C["acc"] if mid else C["field"], fg="#ffffff" if mid else C["txt"],
                         highlightthickness=1, highlightbackground=C["line"])
            b.grid(row=rr, column=cc, padx=2, pady=2)
            b.bind("<ButtonPress-1>", lambda e, c=cmd: self._pad_press(c))
            b.bind("<ButtonRelease-1>", self._pad_release); b.bind("<Leave>", self._pad_release)
        info = tk.Frame(inner, bg=C["panel"]); info.pack(side="left", anchor="n", padx=(14, 0))
        self.l_pt = ttk.Label(info, text="", style="Bold.TLabel", justify="left"); self.l_pt.pack(anchor="w")
        sr = tk.Frame(info, bg=C["panel"]); sr.pack(anchor="w", pady=(4, 2))
        ttk.Label(sr, text=tr("Step") + " (%)").pack(side="left")
        cb = ttk.Combobox(sr, values=("1", "3", "5", "10", "20"), width=4, state="readonly", textvariable=self.step_var)
        cb.pack(side="left", padx=(6, 0)); cb.bind("<<ComboboxSelected>>", lambda e: self.root.focus_set())
        ttk.Label(info, text=tr("Arrow keys move the camera"), style="Mut.TLabel", wraplength=170, justify="left").pack(anchor="w")
        self.l_ctl_status = ttk.Label(info, text="", style="Mut.TLabel", wraplength=170, justify="left")
        self.l_ctl_status.pack(anchor="w", pady=(2, 0))
        bf = tk.Frame(inner, bg=C["panel"]); bf.pack(side="left", anchor="n", padx=(14, 0))
        ttk.Button(bf, text=tr("Snapshot"), command=self._snapshot).pack(fill="x", pady=(0, 4))
        ttk.Button(bf, text=tr("+ Waypoint"), style="Sec.TButton", command=self._add_wp).pack(fill="x", pady=(0, 4))
        ttk.Button(bf, text=tr("Centre"), style="Sec.TButton", command=lambda: self._move("center")).pack(fill="x")
        rf = tk.Frame(inner, bg=C["panel"]); rf.pack(side="left", anchor="n", padx=(18, 0), fill="x", expand=True)
        ttk.Label(rf, text=tr("RELAYS"), style="Head.TLabel").grid(row=0, column=0, columnspan=5, sticky="w")
        labels = [tr_trigger(k) for k in TRIGGERS]; ai_ok = self._ai_ok()
        if not RELAYS:
            ttk.Label(rf, text=tr("no relays"), style="Mut.TLabel").grid(row=1, column=0, sticky="w")
        for i, rl in enumerate(RELAYS):
            col, row = (i // 4) * 5, i % 4 + 1
            dot = tk.Label(rf, text="●", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11))
            dot.grid(row=row, column=col, padx=(0 if col == 0 else 14, 2), pady=2); self.relay_dots.setdefault(i, []).append(dot)
            ttk.Label(rf, text=rl["name"]).grid(row=row, column=col + 1, sticky="w", padx=(0, 6))
            sg = Seg(rf, rl["mode"], lambda m, i=i: self._relay_set(i, "mode", m), small=True)
            sg.grid(row=row, column=col + 2, padx=(0, 6)); self.relay_segs.setdefault(i, []).append(sg)
            self._trigger_box(rf, i, rl, labels).grid(row=row, column=col + 3, sticky="w")
            if not ai_ok and rl["trigger"] not in ("person", "motion", "prealarm", "warm"):
                tk.Label(rf, text="⚠", bg=C["panel"], fg=C["yel"], font=("DejaVu Sans", 10)).grid(row=row, column=col + 4, padx=(2, 0))
        if not self.is_shown("sidebar"):           # sidebar closed -> show relay errors here
            el = ttk.Label(rf, text=self.relay_err, style="Mut.TLabel", foreground=C["red"], wraplength=360)
            el.grid(row=6, column=0, columnspan=10, sticky="w"); self.relay_err_labels.append(el)
        self._sync_modes()

    def _trigger_box(self, parent, i, rl, labels):
        cb = ttk.Combobox(parent, values=labels, width=11, state="readonly")
        cb.current(TRIGGERS.index(rl["trigger"]) if rl["trigger"] in TRIGGERS else 0)
        cb.bind("<<ComboboxSelected>>", lambda e, i=i, c=cb: (self.root.focus_set(), self._relay_set(i, "trigger", TRIGGERS[c.current()])))
        return cb

    # ---- settings sidebar (collapsible: ▶ strip button, header button or Ctrl+B) ----
    def _build_sidebar(self, body):
        right = tk.Frame(body, bg=C["bg"], width=380); right.grid(row=0, column=2, sticky="ns"); right.grid_propagate(False)
        self.right_f = right
        canvas = tk.Canvas(right, bg=C["bg"], bd=0, highlightthickness=0); self.side_canvas = canvas
        sb = ttk.Scrollbar(right, orient="vertical", command=canvas.yview); canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas, style="Bg.TFrame"); win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        bar = ttk.Frame(inner, style="Bg.TFrame"); bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text=tr("Expand all"), command=lambda: self._all_sections(True)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bar, text=tr("Collapse all"), command=lambda: self._all_sections(False)).pack(side="left", expand=True, fill="x")
        ttk.Label(inner, text=tr("Double-click video: video only · F11: fullscreen · Esc: back · Ctrl+B: settings panel · right-click video: show / hide fields"),
                  style="Sub.TLabel", wraplength=340, justify="left").pack(anchor="w", pady=(0, 8))
        # 8 groups (same as the web page); a group = one card, its sections are sub-blocks with a small title
        self.group_titles = {}; self.adv = {}
        listed = {x for g in TK_GROUPS for x in g[3] + g[4]}
        groups = [list(g) for g in TK_GROUPS]
        groups[-1][4] = groups[-1][4] + [x for x in SECTIONS if x not in listed]     # sections added later -> System > Advanced
        for gid, icon, name, secs, adv in groups:
            secs = [x for x in secs if x in SECTIONS and self.is_shown("sec:" + x)]
            adv = [x for x in adv if x in SECTIONS and self.is_shown("sec:" + x)]
            if not secs and not adv:
                continue
            key = "grp:" + gid
            card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
            head = tk.Label(card, text="", bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9, "bold"), anchor="w", cursor="hand2")
            head.pack(fill="x")
            gbody = tk.Frame(card, bg=C["panel"])
            self.sections[key] = (head, gbody); self.group_titles[key] = tr(name)
            head.bind("<Button-1>", lambda e, k=key: self._toggle_section(k))
            split = gid == "alarm"                         # buttons on top, its settings under "Advanced" (like the web page)
            adv_box = None
            for n_, sec in enumerate(secs):
                if split:
                    sb = tk.Frame(gbody, bg=C["panel"]); sb.pack(fill="x")
                    adv_box = tk.Frame(gbody, bg=C["panel"])
                    self._build_section(sec, sb, settings_parent=adv_box)
                else:
                    self._sub_block(gbody, sec, first=(n_ == 0), titled=len(secs) > 1 and tr(sec) != tr(name))
            if split and adv_box is not None:
                adv = [None] + adv
            if adv:
                tk.Frame(gbody, bg=C["line"], height=1).pack(fill="x", pady=(10, 6))
                ah = tk.Label(gbody, text="", bg=C["panel"], fg=C["acc"], font=("DejaVu Sans", 9, "bold"), anchor="w", cursor="hand2")
                ah.pack(fill="x")
                ab = tk.Frame(gbody, bg=C["panel"])
                self.adv[gid] = (ah, ab)
                ah.bind("<Button-1>", lambda e, g=gid: self._set_adv(g, "adv:" + g not in self.open_secs))
                for sec in adv:
                    if sec is None:
                        adv_box.pack(in_=ab, fill="x"); adv_box.lift(ab)   # the settings of the split section (drawn above ab)
                        continue
                    self._sub_block(ab, sec, first=False, titled=True)
                self._set_adv(gid, "adv:" + gid in self.open_secs, save=False)
        for sec in self.sections:
            self._set_section(sec, sec in self.open_secs)

    def _sub_block(self, parent, sec, first, titled):
        """One settings section inside a group: thin line + small title, then its controls."""
        if not first:
            tk.Frame(parent, bg=C["line"], height=1).pack(fill="x", pady=(10, 6))
        if titled:
            tk.Label(parent, text=tr(sec).upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x", pady=(0, 2))
        sbody = tk.Frame(parent, bg=C["panel"]); sbody.pack(fill="x")
        self._build_section(sec, sbody)

    def _build_section(self, sec, sbody, settings_parent=None):
        """Status line, switches, sliders, text fields and buttons of one section. settings_parent: put the switches /
        sliders / text fields there instead (the buttons stay in sbody)."""
        sp = settings_parent if settings_parent is not None else sbody
        if sec in ("Camera / Servos", "Video source", "Schedule", "Patrol", "AI detection", "Web stream", "Auto-tune", "Notifications", "Timelapse", "Thermal camera", "Wi-Fi / hotspot", "Camping / protection"):
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w")
        for s, key, label in TOGGLES:
            if s != sec: continue
            tg = Toggle(sp, tr(label), CFG[key], lambda val, k=key: self._set(k, val)); tg.pack(fill="x", pady=3)
            self.vars[key] = tg
        for s, key, label, lo, hi, step in SLIDERS:
            if s != sec: continue
            row = ttk.Frame(sp); row.pack(fill="x", pady=(6, 0))
            ttk.Label(row, text=tr(label)).pack(side="left")
            vl = ttk.Label(row, text=str(CFG[key]), style="Mut.TLabel"); vl.pack(side="right"); self.value_labels[key] = vl
            v = tk.DoubleVar(value=CFG[key]); self.vars[key] = v
            sc = ttk.Scale(sp, from_=lo, to=hi, variable=v, orient="horizontal",
                           command=lambda val, k=key, st=step: self._slide(k, float(val), st))
            sc.pack(fill="x")
            sc.bind("<ButtonPress-1>", lambda e, k=key: setattr(self, "dragging", k))
            sc.bind("<ButtonRelease-1>", lambda e: (setattr(self, "dragging", None), self.root.focus_set()))
        if sec == "Relays":
            self._build_relay_editor(sbody)
        if sec == "Video source":
            self._build_source_box(sbody)
        if sec == "Schedule":
            self._build_schedule_box(sbody)
        self._build_texts(sp, sec)
        if sec == "Notifications":
            ttk.Button(sbody, text=tr("Test notification"),
                       command=lambda: self.watch.notifier.test(self.watch.frame_out)).pack(fill="x", pady=(8, 0))
        if sec == "Wi-Fi / hotspot":
            self._build_wifi_box(sbody)
        if sec == "Camping / protection":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Arm (countdown)"), command=arm).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Arm now"), command=lambda: arm(0)).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Disarm"), command=disarm).pack(side="left", expand=True, fill="x")
            bf2 = ttk.Frame(sbody); bf2.pack(fill="x", pady=(6, 0))
            ttk.Button(bf2, text=tr("Camping ON"), command=lambda: camping_set(True)).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf2, text=tr("Camping OFF"), command=lambda: camping_set(False)).pack(side="left", expand=True, fill="x")
            bf3 = ttk.Frame(sbody); bf3.pack(fill="x", pady=(6, 0))
            ttk.Button(bf3, text=tr("Own Wi-Fi ON"), command=lambda: (netauto_pause(), hotspot_switch_later(True, 0.2))).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf3, text=tr("Own Wi-Fi OFF"), command=lambda: (netauto_pause(), hotspot_switch_later(False, 0.2))).pack(side="left", expand=True, fill="x")
            bf4 = ttk.Frame(sbody); bf4.pack(fill="x", pady=(6, 0))
            ttk.Button(bf4, text=tr("Autostart ON"), command=lambda: self._autostart(True)).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf4, text=tr("Autostart OFF"), command=lambda: self._autostart(False)).pack(side="left", expand=True, fill="x")
        if sec == "Timelapse":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Use current position"), command=self._tl_here).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Photo now"), command=self.watch.timelapse.request_now).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Create video"), command=self._tl_render).pack(side="left", expand=True, fill="x")
        if sec == "Patrol":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Add current pan as waypoint"), command=self._add_wp).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Clear"), command=self._clear_wp).pack(side="left", expand=True, fill="x")
        if sec == "Auto-tune":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Recalibrate (scene empty)"), command=self.watch.tuner.reset).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Reset all settings"), command=self._reset_settings).pack(side="left", expand=True, fill="x")

    def _set_adv(self, gid, open_, save=True):
        ah, ab = self.adv[gid]
        (self.open_secs.add if open_ else self.open_secs.discard)("adv:" + gid)
        if save and sorted(self.open_secs) != sorted(CFG["ui_open"]):
            CFG["ui_open"] = sorted(self.open_secs); save_settings()
        ah.config(text=("▾ " if open_ else "▸ ") + tr("Advanced"))
        if open_:
            ab.pack(fill="x", pady=(2, 0))
        else:
            ab.pack_forget()

    def _build_relay_editor(self, parent):
        ttk.Label(parent, text=tr(RELAY_NOTE), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(0, 2))
        labels = [tr_trigger(k) for k in TRIGGERS]; ai_ok = self._ai_ok()
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        for i, rl in enumerate(RELAYS):
            card = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
            card.pack(fill="x", pady=(6, 0))
            r1 = tk.Frame(card, bg=C["panel"]); r1.pack(fill="x")
            dot = tk.Label(r1, text="●", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11)); dot.pack(side="left")
            self.relay_dots.setdefault(i, []).append(dot)
            nv = tk.StringVar(value=rl["name"])
            ent = tk.Entry(r1, textvariable=nv, width=13, **ent_kw); ent.pack(side="left", padx=(4, 8))
            for ev in ("<Return>", "<FocusOut>"):
                ent.bind(ev, lambda e, i=i, v=nv: self._relay_set(i, "name", v.get()))
            ttk.Label(r1, text="GPIO", style="Mut.TLabel").pack(side="left")
            used = {o["gpio"] for j, o in enumerate(RELAYS) if j != i}
            free = [str(g) for g in range(2, 28) if g not in GPIO_RESERVED and g not in used]
            gcb = ttk.Combobox(r1, values=free, width=3, state="readonly"); gcb.set(str(rl["gpio"]))
            gcb.pack(side="left", padx=(4, 0))
            gcb.bind("<<ComboboxSelected>>", lambda e, i=i, c=gcb: (self.root.focus_set(), self._relay_set(i, "gpio", c.get())))
            x = tk.Label(r1, text="✕", bg=C["panel"], fg=C["red"], font=("DejaVu Sans", 11, "bold"), cursor="hand2")
            x.pack(side="right"); x.bind("<Button-1>", lambda e, i=i: self._relay_remove(i))
            r2 = tk.Frame(card, bg=C["panel"]); r2.pack(fill="x", pady=(6, 0))
            sg = Seg(r2, rl["mode"], lambda m, i=i: self._relay_set(i, "mode", m)); sg.pack(side="left")
            self.relay_segs.setdefault(i, []).append(sg)
            self._trigger_box(r2, i, rl, labels).pack(side="left", padx=(8, 0))
            if not ai_ok and rl["trigger"] not in ("person", "motion", "prealarm", "warm"):
                ttk.Label(card, text="⚠ " + tr("needs AI model"), foreground=C["yel"], style="Mut.TLabel").pack(anchor="w", pady=(4, 0))
            r3 = tk.Frame(card, bg=C["panel"]); r3.pack(fill="x", pady=(6, 0))
            ttk.Label(r3, text=tr("Hold (s)")).pack(side="left")
            hv = tk.StringVar(value=f"{rl['hold']:g}")
            sp = tk.Spinbox(r3, from_=0.5, to=600, increment=0.5, width=5, textvariable=hv, buttonbackground=C["line"],
                            command=lambda i=i, v=hv: self._relay_hold(i, v), **ent_kw)
            sp.pack(side="left", padx=(6, 12))
            for ev in ("<Return>", "<FocusOut>"):
                sp.bind(ev, lambda e, i=i, v=hv: self._relay_hold(i, v))
            Toggle(r3, tr("Active low"), rl["active_low"], lambda val, i=i: self._relay_set(i, "active_low", val)).pack(side="left", fill="x", expand=True)
        el = ttk.Label(parent, text=self.relay_err, style="Mut.TLabel", foreground=C["red"], wraplength=330)
        el.pack(anchor="w", pady=(4, 0)); self.relay_err_labels.append(el)
        ttk.Button(parent, text=tr("+ Add relay"), command=self._relay_add).pack(fill="x", pady=(4, 0))

    # ---- text settings (notifications, location, presence) ----------------
    def _build_texts(self, parent, sec):
        specs = [x for x in TEXTS if x[0] == sec]
        if not specs:
            return
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        err = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330, justify="left")
        for _s, key, label, kind, extra in specs:
            ttk.Label(parent, text=tr(label), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(8, 0))
            if kind == "enum":
                pairs = text_choice_pairs(key); lab = dict(pairs); back = {l: c for c, l in pairs}
                cb = ttk.Combobox(parent, values=[l for _c, l in pairs], state="readonly"); cb.set(lab.get(CFG[key], CFG[key])); cb.pack(fill="x", pady=(2, 0))
                cb.bind("<<ComboboxSelected>>", lambda e, k=key, c=cb, bk=back: (self.root.focus_set(), self._text_set(k, bk.get(c.get(), c.get()), err)))
                continue
            var = tk.StringVar(value="" if kind == "secret" else str(text_value(key)))
            row = ttk.Frame(parent); row.pack(fill="x", pady=(2, 0))
            ent = tk.Entry(row, textvariable=var, show="•" if kind == "secret" else "", **ent_kw)
            ent.pack(side="left", fill="x", expand=True)
            for ev in ("<Return>", "<FocusOut>"):
                ent.bind(ev, lambda e, k=key, v=var, kd=kind: self._text_set(k, v.get(), err) if (kd != "secret" or v.get()) else None)
            if kind == "secret":
                ttk.Label(row, text=("(" + tr("set") + ")") if CFG[key] else "", style="Mut.TLabel").pack(side="left", padx=4)
                ttk.Button(row, text=tr("Clear"), width=6, command=lambda k=key, v=var: (v.set(""), self._text_set(k, "", err))).pack(side="left")
        err.pack(anchor="w", pady=(4, 0))

    def _text_set(self, key, value, err_label):
        ok, msg = set_text(key, value)
        err_label.config(text="" if ok else "⚠ " + tr_err(msg))

    # ---- video source ----------------------------------------------------
    def _build_source_box(self, parent):
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        self.src_cb = ttk.Combobox(parent, state="readonly"); self.src_cb.pack(fill="x", pady=(4, 0))
        self.src_cb.bind("<<ComboboxSelected>>", self._src_pick)
        bf = ttk.Frame(parent); bf.pack(fill="x", pady=(6, 0))
        self.b_scan = ttk.Button(bf, text=tr("Scan for cameras"), command=self._scan)
        self.b_scan.pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text=tr("Remove network camera"), command=self._src_remove).pack(side="left", expand=True, fill="x")
        ttk.Label(parent, text=tr("Add network camera (RTSP / HTTP stream, Wi-Fi cams)"), style="Mut.TLabel",
                  wraplength=330, justify="left").pack(anchor="w", pady=(10, 0))
        self.ip_name = tk.StringVar(); self.ip_url = tk.StringVar()
        tk.Entry(parent, textvariable=self.ip_name, **ent_kw).pack(fill="x", pady=(2, 2))
        tk.Entry(parent, textvariable=self.ip_url, **ent_kw).pack(fill="x", pady=(0, 4))
        ttk.Label(parent, text="rtsp://user:pass@192.168.1.50:554/stream1  |  http://192.168.1.50:8080/video", style="Mut.TLabel",
                  wraplength=330, justify="left").pack(anchor="w")
        ttk.Button(parent, text=tr("Add"), command=self._src_add).pack(fill="x", pady=(4, 0))
        for txt, path in (("Open recordings preview (browser)", "/recordings"), ("Open camera grid (browser)", "/cams"), ("Open zone editor (browser)", "/zones")):
            ttk.Button(parent, text=tr(txt), command=lambda p=path: self._open_page(p)).pack(fill="x", pady=(6 if path != "/recordings" else 10, 0))
        self.src_msg = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330)
        self.src_msg.pack(anchor="w", pady=(4, 0))
        self._fill_sources()

    def _fill_sources(self):
        cb = getattr(self, "src_cb", None)
        if cb is None or not cb.winfo_exists():
            return
        self.src_items = list_sources()
        names = []
        for it in self.src_items:
            nm = tr("Automatic (first working USB camera)") if it["id"] == "auto" else it["name"]
            names.append(("● " if it["id"] == STATE["source_id"] else "") + nm + (f"  [{it['detail']}]" if it["detail"] else ""))
        cb.config(values=names)
        sel = next((i for i, it in enumerate(self.src_items) if it["id"] == CFG["source"]), 0)
        cb.current(sel)

    def _src_pick(self, _e=None):
        self.root.focus_set()
        i = self.src_cb.current()
        if 0 <= i < len(self.src_items):
            ok, err = source_select(self.watch, self.src_items[i]["id"])
            self.src_msg.config(text="" if ok else tr_err(err))

    def _scan(self):
        if self.b_scan["state"] == "disabled":
            return
        self.b_scan.config(state="disabled", text=tr("Scanning…")); self._scan_done = False

        def work():
            try:
                scan_sources(STATE["source_id"])
            finally:
                self._scan_done = True
        threading.Thread(target=work, daemon=True).start()

    def _src_add(self):
        ok, err, sid = source_add(self.ip_name.get(), self.ip_url.get())
        if not ok:
            self.src_msg.config(text=tr_err(err)); return
        self.ip_name.set(""); self.ip_url.set("")
        source_select(self.watch, "url:" + sid); self.src_msg.config(text=""); self._fill_sources()

    def _src_remove(self):
        i = self.src_cb.current()
        if 0 <= i < len(self.src_items) and self.src_items[i]["kind"] == "url":
            if messagebox.askyesno("Motion Watch", tr("Remove this network camera?")):
                source_remove(self.watch, self.src_items[i]["id"][4:]); self._fill_sources()

    def _open_page(self, path):
        import webbrowser
        self.web.start()
        webbrowser.open(f"{'https' if WEB_OPTS['https'] else 'http'}://127.0.0.1:{CFG['web_port']}{path}")

    # ---- schedule ----------------------------------------------------------
    def _build_schedule_box(self, parent):
        ttk.Label(parent, text=tr(SCHED_NOTE), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(0, 2))
        names = DAYS_SHORT_DE if CFG["lang"] == "de" else DAYS_SHORT_EN
        with LOCK:
            plans = [dict(x) for x in SCHEDULES]
        if not plans:
            ttk.Label(parent, text=tr("no schedules"), style="Mut.TLabel").pack(anchor="w")
        for i, sc in enumerate(plans):
            card = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
            card.pack(fill="x", pady=(6, 0))
            r1 = tk.Frame(card, bg=C["panel"]); r1.pack(fill="x")
            on = schedule_active(sc)
            tk.Label(r1, text="●", bg=C["panel"], fg=C["grn"] if on else C["mut"], font=("DejaVu Sans", 11)).pack(side="left")
            tk.Label(r1, text=" " + sc["name"], bg=C["panel"], fg=C["txt"] if sc["enabled"] else C["mut"],
                     font=("DejaVu Sans", 10, "bold")).pack(side="left")
            x = tk.Label(r1, text="✕", bg=C["panel"], fg=C["red"], font=("DejaVu Sans", 11, "bold"), cursor="hand2")
            x.pack(side="right"); x.bind("<Button-1>", lambda e, i=i: self._sched_remove(i))
            ttk.Button(r1, text=tr("Edit"), command=lambda i=i: self._sched_dialog(i)).pack(side="right", padx=(0, 6))
            lab = {k: lbl for k, lbl in SCHED_FEATURES}
            acts = ", ".join(f"{tr(lab[k])} {tr('ON') if v else tr('OFF')}" for k, v in sc["actions"].items()) or "–"
            when = {"dark": tr("Sunset → sunrise"), "light": tr("Sunrise → sunset")}.get(sc.get("sun"), f"{sc['start']}–{sc['end']}")
            extra = (" · " + tr({"away": "Only when nobody is home", "home": "Only when somebody is home"}[sc["presence"]])) if sc.get("presence") else ""
            tk.Label(card, text=f"{when} · {days_text(sc['days'], names)}" + extra + ("" if sc["enabled"] else f" · [{tr('off')}]")
                     + "\n" + acts, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), justify="left", wraplength=320,
                     anchor="w").pack(fill="x", pady=(4, 0))
        ttk.Button(parent, text=tr("+ Add schedule"), command=self._sched_add).pack(fill="x", pady=(8, 0))

    def _sched_add(self):
        schedule_add(); self._schedule_rebuild()

    def _sched_remove(self, i):
        if messagebox.askyesno("Motion Watch", tr("Remove this schedule?")):
            schedule_remove(i); self._schedule_rebuild()

    def _sched_dialog(self, i):
        with LOCK:
            if not 0 <= i < len(SCHEDULES):
                return
            sc = json.loads(json.dumps(SCHEDULES[i]))
        dlg = tk.Toplevel(self.root); dlg.title(tr("Edit schedule")); dlg.configure(bg=C["bg"]); dlg.transient(self.root)
        f = ttk.Frame(dlg, style="Bg.TFrame", padding=12); f.pack(fill="both", expand=True)
        ttk.Label(f, text=tr("Name")).grid(row=0, column=0, sticky="w")
        nv = tk.StringVar(value=sc["name"]); ttk.Entry(f, textvariable=nv, width=26).grid(row=0, column=1, columnspan=3, sticky="ew", pady=2)
        en = tk.BooleanVar(value=sc["enabled"]); ttk.Checkbutton(f, text=tr("Enabled"), variable=en).grid(row=1, column=0, columnspan=4, sticky="w")
        ttk.Label(f, text=tr("Days")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        dv = []
        df = ttk.Frame(f); df.grid(row=3, column=0, columnspan=4, sticky="w")
        for d, nm in enumerate(DAYS_SHORT_DE if CFG["lang"] == "de" else DAYS_SHORT_EN):
            v = tk.BooleanVar(value=d in sc["days"]); dv.append(v); ttk.Checkbutton(df, text=nm, variable=v).pack(side="left")
        ttk.Label(f, text=tr("From")).grid(row=4, column=0, sticky="w", pady=(8, 0))
        sv = tk.StringVar(value=sc["start"]); ttk.Entry(f, textvariable=sv, width=7).grid(row=4, column=1, sticky="w", pady=(8, 0))
        ttk.Label(f, text=tr("To")).grid(row=4, column=2, sticky="e", pady=(8, 0))
        ev = tk.StringVar(value=sc["end"]); ttk.Entry(f, textvariable=ev, width=7).grid(row=4, column=3, sticky="w", pady=(8, 0))
        sun_opts = [tr("Fixed times"), tr("Sunset → sunrise"), tr("Sunrise → sunset")]; sun_keys = ["", "dark", "light"]
        ttk.Label(f, text=tr("Time window")).grid(row=5, column=0, sticky="w", pady=(6, 0))
        sun_cb = ttk.Combobox(f, values=sun_opts, state="readonly", width=26); sun_cb.current(sun_keys.index(sc.get("sun", "")))
        sun_cb.grid(row=5, column=1, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Label(f, text=tr("Shift (minutes)")).grid(row=6, column=0, sticky="w")
        offv = tk.StringVar(value=str(sc.get("sun_offset", 0))); ttk.Entry(f, textvariable=offv, width=7).grid(row=6, column=1, sticky="w")
        pr_opts = [tr("Always"), tr("Only when nobody is home"), tr("Only when somebody is home")]; pr_keys = ["", "away", "home"]
        ttk.Label(f, text=tr("Applies")).grid(row=7, column=0, sticky="w")
        pr_cb = ttk.Combobox(f, values=pr_opts, state="readonly", width=26); pr_cb.current(pr_keys.index(sc.get("presence", "")))
        pr_cb.grid(row=7, column=1, columnspan=3, sticky="ew")
        ttk.Label(f, text=tr("Skip dates")).grid(row=8, column=0, sticky="w")
        skv = tk.StringVar(value=sc.get("skip", "")); ttk.Entry(f, textvariable=skv).grid(row=8, column=1, columnspan=3, sticky="ew")
        ttk.Label(f, text=tr("Features"), style="Mut.TLabel").grid(row=9, column=0, columnspan=4, sticky="w", pady=(10, 2))
        opts = [tr("unchanged"), tr("ON"), tr("OFF")]; fv = {}
        for r, (key, label) in enumerate(SCHED_FEATURES):
            ttk.Label(f, text=tr(label)).grid(row=10 + r, column=0, columnspan=2, sticky="w")
            cb = ttk.Combobox(f, values=opts, state="readonly", width=11)
            cb.set(opts[0] if key not in sc["actions"] else (opts[1] if sc["actions"][key] else opts[2]))
            cb.grid(row=10 + r, column=2, columnspan=2, sticky="e", pady=1); fv[key] = cb

        def save():
            for t_ in (sv.get().strip(), ev.get().strip()):
                if not _TIME_RE.match(t_):
                    messagebox.showerror("Motion Watch", tr("Time must look like 07:30"), parent=dlg); return
            acts = {}
            for key, cb in fv.items():
                if cb.get() == opts[1]: acts[key] = True
                elif cb.get() == opts[2]: acts[key] = False
            schedule_save(i, {"name": nv.get(), "enabled": en.get(), "days": [d for d, v in enumerate(dv) if v.get()],
                              "start": sv.get().strip(), "end": ev.get().strip(), "actions": acts,
                              "sun": sun_keys[max(0, sun_cb.current())], "sun_offset": int(offv.get()) if offv.get().strip().lstrip("-").isdigit() else 0,
                              "presence": pr_keys[max(0, pr_cb.current())], "skip": skv.get()})
            dlg.destroy(); self._schedule_rebuild()
        bf = ttk.Frame(f); bf.grid(row=11 + len(SCHED_FEATURES), column=0, columnspan=4, sticky="ew", pady=(12, 0))
        ttk.Button(bf, text=tr("Save"), command=save).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text=tr("Cancel"), command=dlg.destroy).pack(side="left", expand=True, fill="x")
        dlg.grab_set()

    # ---- relays ----------------------------------------------------------
    def _ai_ok(self):
        return self.watch.ai.net is not None and CFG["ai_enabled"]

    def _relay_sig(self):
        return json.dumps([{k: v for k, v in r.items() if k != "mode"} for r in RELAYS], sort_keys=True) + str(self._ai_ok())

    def _relay_msg(self, text):
        self.relay_err = ("⚠ " + tr_err(text)) if text else ""
        for el in self.relay_err_labels:
            if el.winfo_exists():
                el.config(text=self.relay_err)
        if self._err_job:
            self.root.after_cancel(self._err_job); self._err_job = None
        if text:
            self._err_job = self.root.after(6000, lambda: self._relay_msg(""))

    def _relay_set(self, i, field, value):
        before = json.dumps(RELAYS, sort_keys=True)
        ok, err = relay_update(i, field, value)
        self._relay_msg("" if ok else err)
        if ok and field in ("mode", "hold", "active_low"):      # the widget already shows it - no rebuild needed
            self._built_sig = self._relay_sig(); self._sync_modes()
        elif not ok or json.dumps(RELAYS, sort_keys=True) != before:
            self._schedule_rebuild()

    def _relay_hold(self, i, var):
        self._relay_set(i, "hold", var.get())
        if 0 <= i < len(RELAYS):
            var.set(f"{RELAYS[i]['hold']:g}")

    def _relay_add(self):
        ok, err = relay_add(); self._relay_msg("" if ok else err)
        self.open_secs.add("grp:relay"); self._schedule_rebuild()

    def _relay_remove(self, i):
        if not 0 <= i < len(RELAYS):
            return
        r = RELAYS[i]
        if messagebox.askyesno(tr("Remove relay"), f"{tr('Remove this relay?')}\n\n{r['name']} (GPIO {r['gpio']})", parent=self.root):
            ok, err = relay_remove(i); self._relay_msg("" if ok else err); self._schedule_rebuild()

    def _sync_modes(self):
        states = STATE.get("relay_states", [])
        for i, r in enumerate(RELAYS):
            for s in self.relay_segs.get(i, []):
                s.set(r["mode"])
            on = i < len(states) and states[i]
            for d in self.relay_dots.get(i, []):
                d.config(fg=C["grn"] if on else C["mut"])

    def _sync_relays(self):
        """Relays changed elsewhere (web page) -> rebuild, unless the user is typing in a field right now."""
        if self._relay_sig() != self._built_sig:
            try:
                w = self.root.focus_get()
                typing = w is not None and w.winfo_class() in TYPING
            except (KeyError, tk.TclError):
                typing = False
            if not typing and not self.dragging:
                self._schedule_rebuild()
            return
        self._sync_modes()

    # ---- manual camera control: pad, arrow keys -------------------------
    def _move(self, cmd):
        try:
            step = float(self.step_var.get())
        except ValueError:
            step = 3.0
        move_camera(cmd, step)
        if self.l_pt is not None:
            self.l_pt.config(text=f"{tr('Pan')} {CFG['pan']:.0f}%\n{tr('Tilt')} {CFG['tilt']:.0f}%")

    def _key_move(self, cmd):
        try:
            w = self.root.focus_get()
            if w is not None and w.winfo_class() in TYPING:
                return                                   # arrow keys belong to the text field / slider
        except (KeyError, tk.TclError):
            pass
        self._move(cmd)
        return "break"

    def _pad_press(self, cmd):
        self._pad_release()
        self._move(cmd)
        if cmd != "center":
            self._hold_job = self.root.after(350, lambda: self._pad_repeat(cmd))

    def _pad_repeat(self, cmd):
        self._move(cmd); self._hold_job = self.root.after(120, lambda: self._pad_repeat(cmd))

    def _pad_release(self, _e=None):
        if self._hold_job:
            self.root.after_cancel(self._hold_job); self._hold_job = None

    def _wheel(self, e, direction):
        c = self.side_canvas
        if c is None or self.right_f is None or not c.winfo_exists():
            return
        if str(e.widget).startswith(str(self.right_f)):
            c.yview_scroll(direction, "units")

    def _reset_settings(self):
        theme, lang, hidden = CFG["theme"], CFG["lang"], CFG["ui_hidden"]
        reset_settings()
        CFG["theme"], CFG["lang"], CFG["ui_hidden"] = theme, lang, hidden     # keep the chosen look, language and view
        save_settings(); self._schedule_rebuild()

    # ---- collapsible sections -------------------------------------------
    def _set_section(self, sec, open_):
        head, body = self.sections[sec]
        (self.open_secs.add if open_ else self.open_secs.discard)(sec)
        if sorted(self.open_secs) != sorted(CFG["ui_open"]):
            CFG["ui_open"] = sorted(self.open_secs); save_settings()
        head.config(text=("▾  " if open_ else "▸  ") + self.group_titles.get(sec, tr(sec)).upper())
        if open_:
            body.pack(fill="x", pady=(4, 0))
        else:
            body.pack_forget()

    def _toggle_section(self, sec):
        self._set_section(sec, sec not in self.open_secs)

    def _all_sections(self, open_):
        for sec in self.sections:
            self._set_section(sec, open_)

    # ---- callbacks -------------------------------------------------------
    def _set(self, key, value):
        with LOCK:
            CFG[key] = type(CFG[key])(value) if not isinstance(CFG[key], bool) else bool(value)
        save_settings()
        if key == "web_stream" and value:
            self.web.start()
        if key == "fullscreen":
            return
        if key == "patrol":
            log_event("patrol", "Patrol switched ON" if value else "Patrol switched OFF")

    def _slide(self, key, value, step):
        value = round(round(value / step) * step, 2)
        value = int(value) if isinstance(CFG[key], int) else value
        self.value_labels[key].config(text=str(value)); self._set(key, value)
        if key in ("pan", "tilt") and self.dragging == key:          # dragging the pan/tilt slider = manual control
            MANUAL["until"] = time.time() + CFG["manual_hold"]

    def _reset_count(self):
        STATE["detections_total"] = 0; STATE["ignored_vehicles"] = 0
        log_event("person", "Person counter reset (click on the counter badge resets it)")

    def _add_wp(self):
        WAYPOINTS.append(round(float(CFG["pan"]), 1)); save_settings()
        log_event("patrol", f"Waypoint added at pan {CFG['pan']:.0f}%  ->  {[round(w) for w in WAYPOINTS]}")

    def _clear_wp(self):
        WAYPOINTS.clear(); save_settings(); log_event("patrol", "Waypoints cleared")

    def _snapshot(self):
        if self.watch.frame_out is None:
            return
        os.makedirs(CFG["record_dir"], exist_ok=True)
        name = os.path.join(CFG["record_dir"], datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.jpg"))
        cv2.imwrite(name, self.watch.frame_out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        log_event("rec", f"Snapshot saved: {os.path.basename(name)}")

    # ---- periodic updates ------------------------------------------------
    def _update_video(self):
        try:
            frame = self.watch.frame_out
            if frame is not None and self.video is not None and self.video.winfo_exists():
                w = max(160, self.video.winfo_width()); h = max(90, self.video.winfo_height())
                fh, fw = frame.shape[:2]; scale = min(w / fw, h / fh)
                img = cv2.cvtColor(cv2.resize(frame, (max(1, int(fw * scale)), max(1, int(fh * scale)))), cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(Image.fromarray(img)); self.video.config(image=self.photo)
        finally:
            self.root.after(33, self._update_video)

    # ---- Wi-Fi / hotspot --------------------------------------------------
    def _build_wifi_box(self, parent):
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        self.wf_btn = ttk.Button(parent, text=tr("Search networks"), command=self._wf_scan); self.wf_btn.pack(fill="x", pady=(6, 0))
        self.wf_cb = ttk.Combobox(parent, state="readonly"); self.wf_cb.pack(fill="x", pady=(6, 0))
        self.wf_cb.bind("<<ComboboxSelected>>", lambda e: self.root.focus_set())
        ttk.Label(parent, text=tr("Password"), style="Mut.TLabel").pack(anchor="w", pady=(6, 0))
        self.wf_pw = tk.StringVar(); tk.Entry(parent, textvariable=self.wf_pw, show="•", **ent_kw).pack(fill="x")
        self.wf_pref = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text=tr("prefer this network"), variable=self.wf_pref).pack(anchor="w", pady=(4, 0))
        bf = ttk.Frame(parent); bf.pack(fill="x", pady=(6, 0))
        ttk.Button(bf, text=tr("Connect now"), command=lambda: self._wf_do("connect")).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text=tr("Only save (connects automatically)"), command=lambda: self._wf_do("save")).pack(side="left", expand=True, fill="x")
        ttk.Button(parent, text=tr("Forget network"), command=lambda: self._wf_do("forget")).pack(fill="x", pady=(4, 0))
        self.wf_msg = ttk.Label(parent, text="", style="Mut.TLabel", wraplength=330, justify="left"); self.wf_msg.pack(anchor="w", pady=(4, 0))
        self._wf_fill()

    def _wf_fill(self):
        nets = WIFI["scan"]
        self.wf_cb["values"] = [("▂▄▆█"[:max(1, n["bars"])] + "  " + n["ssid"] + ("  🔒" if n["secure"] else "") + f"  ({n['signal']} %)"
                                 + ("  ✓" if n["active"] else "")) for n in nets]
        if nets and not self.wf_cb.get():
            self.wf_cb.current(0)

    def _wf_selected(self):
        i = self.wf_cb.current()
        return WIFI["scan"][i] if 0 <= i < len(WIFI["scan"]) else None

    def _wf_scan(self):
        self.wf_btn.config(text=tr("Searching …"), state="disabled")
        def work():
            ok, err = wifi_scan()
            def done():
                if self.wf_btn.winfo_exists():
                    self.wf_btn.config(text=tr("Search networks"), state="normal"); self._wf_fill()
                    self.wf_msg.config(text="" if ok else "⚠ " + tr_err(err), foreground=C["red"])
            self.root.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    def _wf_do(self, action):
        n = self._wf_selected()
        if n is None:
            self.wf_msg.config(text="⚠ " + tr("Search networks"), foreground=C["red"]); return
        if action == "connect":
            ok, err = wifi_connect(n["ssid"], self.wf_pw.get(), self.wf_pref.get())
        elif action == "save":
            ok, err = wifi_save(n["ssid"], self.wf_pw.get(), self.wf_pref.get())
        else:
            sv = next((x for x in (_nm_saved() if wifi_backend() == "nm" else _wpa_saved()) if x["ssid"] == n["ssid"]), None)
            ok, err = wifi_forget(sv["id"]) if sv else (False, "unknown network")
        self.wf_pw.set("")
        self.wf_msg.config(text=(tr("Saved") if ok else "⚠ " + tr_err(err)), foreground=C["grn"] if ok else C["red"])

    def _autostart(self, on):
        ok, err = autostart_set(on)
        if not ok or err:
            self._status("Camping / protection", "⚠ " + tr_err(err))

    def _tl_here(self):
        CFG["timelapse_pan"] = round(float(CFG["pan"]), 1); CFG["timelapse_tilt"] = round(float(CFG["tilt"]), 1)
        save_settings(); log_event("servo", f"Timelapse position set to pan {CFG['timelapse_pan']:.0f}% / tilt {CFG['timelapse_tilt']:.0f}%")

    def _tl_render(self):
        ok, err = timelapse_render("")
        if not ok:
            self._status("Timelapse", "⚠ " + tr_err(err))

    def _status(self, sec, text):
        lbl = self.status_labels.get(sec)
        if lbl is not None:
            lbl.config(text=text)

    def _update_state(self):
        try:
            if not self.video_only:
                self._refresh()
        finally:
            self.root.after(500, self._update_state)

    def _refresh(self):
        st = STATE
        self._sync_relays()
        for k, lbl in self.stat.items():
            lbl.config(text=str(st[k]))
        if self.p_rain is not None:
            self.p_rain["value"] = st["rain_score"]; self.l_rain.config(text=f"{st['rain_score']:.2f}")
            self.p_wind["value"] = st["wind_score"]; self.l_wind.config(text=f"{st['wind_score']:.2f}")
            self.l_boost.config(text=f"x{st['wind_boost']}")
        n = st["persons"]; manual = manual_active()
        self._sb("b_person", f"{n} {tr('PERSONS DETECTED') if n > 1 else tr('PERSON DETECTED')}" if n else tr("No person"), C["red"] if n else None)
        self._sb("b_count", f"{tr('Persons total')}: {st['detections_total']}", C["red"] if st["detections_total"] else None)
        summ = st["object_summary"]
        self._sb("b_objects", f"{st['objects']} {tr('objects')}" + (f": {summ[:40]}" if summ else ""), C["org"] if st["objects"] else None)
        self._sb("b_rain", tr("RAIN MODE") if st["rain_mode"] else tr("No rain"), C["blu"] if st["rain_mode"] else None)
        wl = st["wind_level"]; self._sb("b_wind", f"{tr('Wind')}: {tr(wl)}", C["yel"] if wl not in ("calm", "off") else None)
        self._sb("b_rec", "● " + tr("REC") if st["recording"] else tr("Idle"), C["red"] if st["recording"] else None)
        on = sum(1 for s in st["relay_states"] if s)
        self._sb("b_relays", f"{tr('Relays')}: {on}/{len(RELAYS)} {tr('on')}", C["grn"] if on else None)
        self._sb("b_patrol", tr("MANUAL") if manual else (tr("TRACKING") if st["tracking"] else
                 (f"{tr('Patrol')}: {st['patrol_status']}" if CFG["patrol"] else tr("Patrol off"))),
                 C["yel"] if manual else (C["acc"] if (st["tracking"] or CFG["patrol"]) else None))
        self._sb("b_auto", f"{tr('Auto')}: {st['auto_status']}", C["org"])
        self._sb("b_light", tr("LOW LIGHT") if st["lowlight"] else tr("Light ok"), C["yel"] if st["lowlight"] else None)
        fps = float(st["fps"] or 0)
        self._sb("b_fps", f"{fps:.0f} FPS", C["grn"] if fps >= 12 else (C["yel"] if fps >= 6 else C["red"]))
        a_st = st["arm_state"]
        self._sb("b_arm", "🛡 " + (tr("Armed") if a_st == "armed" else (f"{tr('Armed in')} {st['arm_left']} s" if a_st == "arming" else tr("Disarmed"))),
                 C["grn"] if a_st == "armed" else (C["yel"] if a_st == "arming" else None))
        if self.badges:
            self._flow()
        if self.l_pt is not None:
            self.l_pt.config(text=f"{tr('Pan')} {CFG['pan']:.0f}%\n{tr('Tilt')} {CFG['tilt']:.0f}%")
            if manual:
                txt = f"{tr('Manual control - tracking / patrol paused')} ({MANUAL['until'] - time.time():.0f} s)"
            elif st["tracking"]:
                txt = tr("Tracking person")
            else:
                txt = f"{tr('Patrol')}: {st['patrol_status']}" if CFG["patrol"] else ""
            self.l_ctl_status.config(text=txt)
        self._status("Camera / Servos", f"{tr('backend')}: {st['servo_backend']} · {tr('pan')} {CFG['pan']:.0f}% · {tr('tilt')} {CFG['tilt']:.0f}%"
                                        + (" · " + tr("TRACKING") if st["tracking"] else "") + (" · " + tr("MANUAL") if manual else ""))
        self._status("Video source", f"{st['source_label'] or '–'}" + (f" · {st['source_res']}" if st["source_res"] else "") + f" · {tr(st['source_status'])}")
        self._status("Schedule", (tr("active now") + ": " + ", ".join(st["sched_active"])) if st["sched_active"] else "–")
        if getattr(self, "_scan_done", None) and getattr(self, "b_scan", None) is not None and self.b_scan.winfo_exists():
            self._scan_done = False; self.b_scan.config(state="normal", text=tr("Scan for cameras")); self._fill_sources()
        if st["source_id"] != getattr(self, "_src_seen", None):
            self._src_seen = st["source_id"]; self._fill_sources()
        sig = json.dumps([SCHEDULES, st["sched_active"]], sort_keys=True)
        if sig != getattr(self, "_sched_sig", sig) and not any(isinstance(w, tk.Toplevel) for w in self.root.winfo_children()):
            self._sched_sig = sig; self._schedule_rebuild()
        self._sched_sig = sig
        self._status("Patrol", f"{st['patrol_status']} · {tr('waypoints')}: {[round(w) for w in WAYPOINTS] or tr('none')}")
        self._status("AI detection", f"{st['ai_status']} · {st['ai_persons']} {tr('AI persons')}"
                                     + (f" · {tr('objects')}: {st['object_summary']}" if st["object_summary"] else ""))
        self._status("Web stream", f"{st['web_status']}  (http://<pi-ip>:{CFG['web_port']}/)")
        self._status("Auto-tune", f"{st['auto_status']} · {st['auto_changes']} {tr('automatic changes')}")
        self._status("Notifications", f"{tr('status')}: {st['notify_status']}")
        hs = st["hotspot"] or {}
        a_st = st["arm_state"]
        self._status("Camping / protection", "🛡 " + (tr("Armed") if a_st == "armed" else (f"{tr('Armed in')} {st['arm_left']} s" if a_st == "arming" else tr("Disarmed")))
                     + (" · ⛺ " + tr("Camping profile") if CFG["camping"] else "")
                     + (f" · 📡 «{hs.get('ssid')}» {hs.get('clients', 0)} {tr('devices')} · {page_address('10.42.0.1')}" if hs.get("on") else
                        f" · 📡 «{CFG['hotspot_ssid']}» / {CFG['hotspot_password'] or '–'}")
                     + (f" · {tr('Clock')}: {st['time_status']}" if st["time_status"] else "")
                     + f" · 🔁 {tr('Autostart ON') if (st['autostart'] or {}).get('on') else tr('Autostart OFF')}"
                     + (f" · {tr(st['netauto'])}" if CFG["net_mode"] == "auto" and st["netauto"] not in ("", "off") else ""))
        w = st["wifi"] or {}
        self._status("Wi-Fi / hotspot", (f"{tr('Wi-Fi')}: «{w.get('ssid') or '?'}» · {w.get('ip') or ''}" if w.get("connected") else f"{tr('Wi-Fi')}: {tr('not connected')}")
                     + (f" · {WIFI['job']}" if WIFI["job"] else ""))
        self._status("Timelapse", tl_status_text(st["timelapse"]) + (" · " + tl_status_text(st["timelapse_render"]) if st["timelapse_render"] else ""))
        self._status("Thermal camera", tl_status_text(st["thermal"]) + (f" · {st['thermal_res']}" if st["thermal"] == "connected" and st["thermal_res"] else ""))
        if self.l_settings is not None:
            self.l_settings.config(text=f"{tr('Settings')}: {st['settings_status']} · {tr('recordings')} {st['rec_dir_mb']} MB"
                                        + (" · " + tr("LOW LIGHT") if st["lowlight"] else f" · {tr('brightness')} {st['brightness']}"))
        if self.l_cpu is not None:
            self._update_cpu()
        for key, v in self.vars.items():
            if key == self.dragging: continue
            cur = CFG[key]
            if isinstance(v, Toggle):
                v.set(cur)
            elif abs(v.get() - cur) > 1e-9:
                v.set(cur); self.value_labels[key].config(text=str(round(cur, 2)))
        if self.log is not None:
            with LOCK:
                events = list(st["events"])
            if events and events[0] is not self._last_ev:
                self._last_ev = events[0]
                self.log.config(state="normal"); self.log.delete("1.0", "end")
                for e in events:
                    self.log.insert("end", e["t"] + "  ", "t"); self.log.insert("end", e["text"] + "\n", e["kind"])
                self.log.config(state="disabled")

    def _update_wifi(self):
        if self.l_wifi is None:
            return
        w, n = STATE["wifi"], STATE["net"]
        if not w:
            self.l_wifi.config(text=""); return
        if w["connected"]:
            bars = "▂▄▆█"[:(4 if w["pct"] >= 75 else 3 if w["pct"] >= 50 else 2 if w["pct"] >= 25 else 1)]
            txt = f"{tr('Wi-Fi')} {bars} {w['dbm']} dBm ({w['pct']} %)" + (f" · {w['ssid']}" if w["ssid"] else "")
            col = C["grn"] if w["dbm"] >= -65 else (C["yel"] if w["dbm"] >= -75 else C["red"])
        else:
            txt, col = f"{tr('Wi-Fi')}: {tr('not connected')}", C["red"]
        if n.get("online") is not None:
            txt += f" · {tr('Internet')}: " + (tr("online") + (f" ({n['ms']} ms)" if n.get("ms") is not None else "") if n["online"] else tr("offline"))
            if not n["online"]:
                col = C["red"]
        self.l_wifi.config(text=txt, foreground=col)
        self._draw_wifi(STATE["wifi_hist"])

    def _draw_wifi(self, hist):
        c = self.wifi_canvas
        if c is None or not c.winfo_exists():
            return
        c.delete("all")
        w = max(10, c.winfo_width()); h = max(10, c.winfo_height())
        y = lambda d: 2 + (h - 4) * (-35 - max(-95, min(-35, d))) / 60.0
        colr = lambda d: C["grn"] if d >= -65 else (C["yel"] if d >= -75 else C["red"])
        for d in (-65, -75):
            c.create_line(0, y(d), w, y(d), fill=C["line"], dash=(3, 3))
        n = len(hist)
        xs = lambda i: w - (n - 1 - i) * (w / 149.0)
        for i in range(1, n):
            a, b = hist[i - 1], hist[i]
            if a is not None and b is not None:
                c.create_line(xs(i - 1), y(a), xs(i), y(b), fill=colr(min(a, b)), width=2)
        for i, d in enumerate(hist):
            if d is None:
                c.create_rectangle(xs(i) - 1, h - 5, xs(i) + 1, h, fill=C["red"], outline="")

    def _update_cpu(self):
        self._update_wifi()
        cpu = STATE["cpu"]
        if cpu is None:
            self.l_cpu.config(text="n/a"); self.l_cpu_info.config(text=tr("no CPU data (pip install psutil)")); return
        self.l_cpu.config(text=f"{cpu:.0f} %")
        self.p_cpu["value"] = cpu
        self.p_cpu.configure(style="CpuG.Horizontal.TProgressbar" if cpu < 60 else
                             ("CpuY.Horizontal.TProgressbar" if cpu < 85 else "CpuR.Horizontal.TProgressbar"))
        t = STATE["cpu_temp"]
        self.l_cpu_info.config(text=(f"{t:.1f} °C · " if t is not None else "") + f"{STATE['cpu_count']} {tr('cores')} · {tr('last 60 s')}")
        c = self.cpu_canvas; c.delete("all")
        w = max(10, c.winfo_width()); h = max(10, c.winfo_height()); hist = STATE["cpu_hist"]
        for g in (25, 50, 75):
            c.create_line(0, h - h * g / 100, w, h - h * g / 100, fill=C["line"])
        if len(hist) > 1:
            pts = []
            for i, v in enumerate(hist):
                pts += [w - (len(hist) - 1 - i) * (w / 59.0), h - 2 - (h - 4) * v / 100.0]
            c.create_line(*pts, fill=C["grn"] if cpu < 60 else (C["yel"] if cpu < 85 else C["red"]), width=2)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=None, help="USB camera number (same as --source usb:N)")
    ap.add_argument("--source", default=None, help="video source: auto | usb:N | pi:N | rtsp://... | http://... (saved in the settings)")
    ap.add_argument("--web", action="store_true", help="(default now) start the web page / stream immediately")
    ap.add_argument("--no-web", action="store_true", help="do not start the web page / stream (it can be switched on in the window)")
    ap.add_argument("--headless", action="store_true", help="no desktop window, web page only (implies --web)")
    ap.add_argument("--port", type=int, default=None, help="web port (default 5000)")
    ap.add_argument("--web-password", default="", help="protect the web page with this password")
    ap.add_argument("--notify-url", default=None, help="webhook / ntfy URL called when a person is detected")
    ap.add_argument("--bind", default="0.0.0.0", help="address the web page listens on (127.0.0.1 = this computer only; use with a VPN / reverse proxy)")
    ap.add_argument("--https", action="store_true", help="serve the web page over HTTPS (self-signed certificate is created if --cert/--key are missing)")
    ap.add_argument("--cert", default="", help="certificate file (PEM) for --https")
    ap.add_argument("--key", default="", help="private key file (PEM) for --https")
    ap.add_argument("--boot", action="store_true", help="(used by the autostart) started at boot: switch the own Wi-Fi on")
    ap.add_argument("--config", default="", help="folder for settings / log / certificate (default ~/.config/motionwatch)")
    ap.add_argument("--allow-wifi", action="store_true", help="allow this user to manage Wi-Fi, the own hotspot and the clock (run once with sudo) and exit")
    ap.add_argument("--print-service", action="store_true", help="print a systemd unit file for autostart and exit")
    ap.add_argument("--install-service", action="store_true", help="install + enable the systemd service (run with sudo) and exit")
    a = ap.parse_args()
    if a.allow_wifi:
        sys.exit(allow_wifi())
    if a.print_service:
        print(service_text()); sys.exit(0)
    if a.install_service:
        sys.exit(install_service())
    WEB_OPTS.update(bind=a.bind, https=a.https or bool(a.cert and a.key), cert=a.cert, key=a.key)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))          # systemd stop -> finish the recording, save the settings
    set_data_dir(a.config or DATA_DIR)
    took = prepare_settings_file()
    load_settings()
    if took:
        log_event("sys", took); print(took)
    print(f"Settings: {SETTINGS_FILE}")
    if a.port:
        CFG["web_port"] = a.port
    CFG["web_password"] = a.web_password
    if a.notify_url is not None:
        CFG["notify_url"] = a.notify_url
    if not a.headless and not GUI_OK:
        print(f"Desktop window not available ({GUI_ERR}) - running headless with the web page instead.")
        print("   To get the window:  sudo apt install python3-pil.imagetk python3-tk")
        a.headless = True
    if a.source:
        if SRC_RE.match(a.source):
            CFG["source"] = a.source
        elif _url_ok(a.source):
            known = next((x for x in CFG["ip_sources"] if x["url"] == a.source), None)
            if known is None:
                _ok, _err, _sid = source_add("Command line camera", a.source)
                CFG["source"] = "url:" + _sid
            else:
                CFG["source"] = "url:" + known["id"]
        else:
            ap.error("--source must be auto, usb:N, pi:N or an rtsp:// / http:// URL")
    elif a.cam is not None:
        CFG["source"] = f"usb:{a.cam}"
    WATCH = MotionWatch()
    WEB = WebStream(WATCH)
    arm_tick()
    NetAuto()
    if a.boot and CFG["net_mode"] == "hotspot":                    # started by the autostart: own Wi-Fi on
        boot_hotspot()
    elif a.boot and CFG["net_mode"] == "client" and CFG["hotspot_on"]:
        CFG["hotspot_on"] = False
    elif CFG["hotspot_on"] and not a.boot:                         # e.g. camping: the own Wi-Fi comes back after a restart
        hotspot_switch_later(True, 3.0)
    try:
        autostart_follow_version(); autostart_refresh()
    except Exception:
        pass
    if not a.no_web or a.headless:                                 # the web page is on from the start (1.6.3)
        CFG["web_stream"] = True
        WEB.start()
    threading.Thread(target=WATCH.run, daemon=True).start()
    apply_theme()
    ip = local_ip()
    print("Motion Watch 1.7.4 started" + (f" - web page on {page_address(ip) if ip else 'http://<ip>:' + str(CFG['web_port']) + '/'}" if CFG["web_stream"] else ""))
    if CFG["web_stream"] and not CFG["web_password"]:
        print("   Note: the web page has no password - anybody in this network can open it. Start with --web-password SECRET")
    if a.headless:
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
    else:
        App(WATCH, WEB).run()