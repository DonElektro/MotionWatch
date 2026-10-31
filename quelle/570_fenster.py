#@ Motion Watch – Teil 570: Fenster auf dem Pi / PC (Tkinter). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
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
        Canvas = object

C = dict(THEMES["dark"])


def apply_theme():
    C.clear(); C.update(THEMES.get(CFG.get("theme", "dark"), THEMES["dark"]))


def kind_colors():
    return {"person": C["red"], "rain": C["blu"], "wind": C["yel"], "car": C["mut"], "rec": C["grn"],
            "auto": C["org"], "ai": C["pur"], "servo": C["acc"], "patrol": C["acc"], "web": C["mut"], "sys": C["mut"], "sched": C["pur"]}

DAYS_SHORT_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DAYS_SHORT = {"de": ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"), "fr": ("lu", "ma", "me", "je", "ve", "sa", "di"),
              "it": ("lu", "ma", "me", "gi", "ve", "sa", "do"), "rm": ("gli", "ma", "me", "gie", "ve", "so", "du"), "en": DAYS_SHORT_EN}
DAYS_SHORT_DE = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
SLIDERS = [  # (section, key, label, min, max, step)
    ("Mover", "mover_speed", "Top speed (%)", 10, 100, 5),
    ("Mover", "mover_turn", "Turning speed (%)", 10, 100, 5),
    ("Mover", "mover_ramp", "Gentle start and stop (seconds)", 0.0, 2.0, 0.1),
    ("AI detection", "species_conf", "Animal species: minimum certainty", 0.2, 0.95, 0.05),
    ("Solar panel", "solar_shunt", "Current meter: shunt resistor (Ohm, usually 0.1)", 0.01, 0.1, 0.005),
    ("GPS module", "gps_theft_m", "Theft tracking: alarm from a distance of (m)", 50, 1000, 50),
    ("Storm warning", "storm_drop", "Warn when the air pressure falls by (hPa in 3 hours)", 1.0, 8.0, 0.5),
    ("Storm warning", "storm_wind", "Warn from wind / gusts of (km/h)", 20, 120, 5),
    ("Storm warning", "wind_factor", "Wind meter: km/h per pulse per second", 0.5, 5.0, 0.1),
    ("Extra sensors", "tag_missing", "Bluetooth tag: alarm when not seen for (min)", 1, 30, 1),
    ("SMS (LTE stick)", "sms_pause", "At most one SMS every (minutes)", 1, 60, 1),
    ("SMS (LTE stick)", "sms_day_max", "At most SMS per day", 1, 100, 1),
    ("Deterrence", "deter_seconds", "Duration of sound / flashing (s)", 2, 30, 1),
    ("Deterrence", "deter_pause", "Pause between two reactions (s)", 10, 600, 10),
    ("Theft protection", "tamper_tilt", "Motion sensor: alarm from a tilt of (degrees)", 5, 45, 1),
    ("Reference scan", "refscan_pan_steps", "Directions side by side", 1, 12, 1),
    ("Reference scan", "refscan_pan_from", "Turn from (% of the pan range)", 0, 100, 1),
    ("Reference scan", "refscan_pan_to", "Turn to (% of the pan range)", 0, 100, 1),
    ("Reference scan", "refscan_tilt_steps", "Heights (rows)", 1, 3, 1),
    ("Reference scan", "refscan_tilt_mid", "Middle height (tilt %)", 20, 80, 1),
    ("Reference scan", "refscan_tilt_span", "Distance between the rows (tilt %)", 4, 40, 1),
    ("Reference scan", "refscan_photos", "Photos per direction (more = less noise)", 1, 5, 1),
    ("Reference scan", "refscan_settle", "Wait after turning (seconds)", 0.5, 5, 0.5),
    ("Reference scan", "refscan_sens", "Sensitivity of the comparison (%)", 10, 100, 5),
    ("Reference scan", "refscan_min_area", "Smallest change (% of the picture)", 0.1, 5, 0.1),
    ("Reference scan", "refscan_every", "Compare every (minutes while armed, 0 = off)", 0, 240, 5),
    ("Camera / Servos", "pan", "Pan (%)", 0, 100, 1),
    ("Camera / Servos", "tilt", "Tilt (%)", 0, 100, 1),
    ("Camera / Servos", "track_gain", "Tracking gain", 0.1, 2.0, 0.1),
    ("Camera / Servos", "track_motion_min", "Follow movement: smallest size (% of the picture)", 0.02, 3.0, 0.02),
    ("Camera / Servos", "track_motion_hold", "Follow movement: must move for (seconds)", 0.3, 5.0, 0.1),
    ("Camera / Servos", "track_deadzone", "Tracking dead zone", 0.02, 0.3, 0.01),
    ("Camera / Servos", "manual_hold", "Manual control pause (s)", 0, 60, 1),
    ("Patrol", "patrol_dwell", "Dwell at waypoint (s)", 0, 15, 0.5),
    ("Patrol", "patrol_speed", "Patrol speed (%/s)", 5, 100, 5),
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
    ("Recording", "loop_hours", "Continuous recording: keep (hours)", 1, 168, 1),
    ("Recording", "loop_fps", "Continuous recording: pictures per second", 1, 15, 1),
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
    ("Power saving", "eco_fps", "Pictures per second while quiet", 1, 10, 1),
    ("Simulator", "sim_fps", "Pictures per second in the simulation (CPU saving)", 2, 15, 1),
    ("Power saving", "eco_wake", "Full speed after an event for (s)", 5, 300, 5),
    ("Night report", "report_from", "Night time from (o'clock) – for the night report, the wake-up alarm and «Guard tonight»", 12, 23, 1),
    ("Updates", "update_hour", "Automatic update at (o'clock)", 0, 23, 1),
    ("Setup", "log_status_min", "Event log: status line every N minutes (0 = off)", 0, 120, 5),
    ("Setup", "log_keep_days", "Event log: keep the archive (days)", 7, 365, 1),
    ("Night report", "report_hour", "Night time until (o'clock) – the night report comes, «Guard tonight» ends", 3, 12, 1),
    ("Night report", "diary_keep_days", "Keep diary entries (days, ★ always)", 7, 365, 1),
    ("Night report", "weekrep_hour", "Weekly detection report: hour", 0, 23, 1),
    ("Setup", "temp_hot", "Temperature alarm: too hot from (°C)", 20, 45, 1),
    ("Setup", "temp_cold", "Temperature alarm: too cold below (°C)", -20, 10, 1),
    ("Setup", "env_offset", "Temperature sensor: correction (°C)", -5.0, 5.0, 0.1),
    ("Battery", "ups_mah", "UPS HAT: capacity of ONE 18650 cell (mAh)", 1000, 4000, 50),
    ("Battery", "ups_shutdown_pct", "UPS HAT: shut the Pi down at (%, 0 = never)", 0, 30, 1),
    ("Battery", "batt_mah", "Powerbank capacity (mAh, as on the label; 0 = off)", 0, 60000, 1000),
    ("Battery", "batt_extra_w", "Other devices (W): camera, USB, servos", 0.0, 10.0, 0.5),
    ("Camping / protection", "auto_retry", "Automatic: look for known networks every (min, 0 = never)", 0, 60, 1),
    ("Microphone", "audio_gain", "Microphone gain (dB)", 0, 30, 1),
    ("Camera / Servos", "pan_servo_range", "Pan servo: turning range (degrees: 180, 270 or 360)", 90, 360, 90),
    ("Camera / Servos", "pan_limit", "Pan limit: max. degrees from the middle", 10, 180, 5),
    ("Camera / Servos", "tilt_limit", "Tilt limit: max. degrees from the middle", 10, 90, 5),
    ("Lights", "light_hold", "Light stays on after an alarm (s)", 5, 600, 5),
    ("Servo driver", "pca_pan_ch", "PCA9685 channel pan", 0, 15, 1),
    ("Servo driver", "pca_tilt_ch", "PCA9685 channel tilt", 0, 15, 1),
    ("Setup", "temp_warn", "Push message when the CPU is hotter than (°C)", 60, 90, 1),
    ("Setup", "disk_warn_mb", "Push message when less free space than (MB)", 100, 5000, 100),
    ("Thermal camera", "thermal_zoom", "Thermal: zoom - part the camera sees (%)", 30, 100, 1),
    ("Thermal camera", "thermal_dx", "Thermal: shift left / right (%)", -30, 30, 1),
    ("Thermal camera", "thermal_dy", "Thermal: shift up / down (%)", -30, 30, 1),
    ("Microphone", "noise_threshold", "Noise alarm: louder than the background by (dB)", 6, 40, 1),
    ("Microphone", "noise_min", "Noise alarm: at least (s)", 0.1, 3, 0.1),
    ("Clap switch", "clap_sens", "Sensitivity (higher = also softer claps)", 1, 10, 1),
    ("Clap switch", "clap_volume", "Volume of the beep", 0, 100, 5),
    ("Bless you", "sneeze_sens", "Sensitivity (higher = answers more readily)", 1, 10, 1),
    ("Wake-up alarm", "wake_snooze", "Snooze (minutes)", 3, 30, 1),
    ("Wake-up alarm", "wake_ring_max", "Rings at most (minutes)", 3, 60, 1),
    ("Wake-up alarm", "wake_volume", "Volume of the alarm", 10, 100, 5),
    ("Bless you", "sneeze_volume", "Volume of the answer", 0, 100, 5),
    ("Loudspeaker", "siren_volume", "Volume (%)", 5, 100, 5),
    ("Loudspeaker", "siren_seconds", "Duration of the siren (s)", 1, 60, 1),
    ("Loudspeaker", "siren_pause", "Siren: min. pause between two alarms (s)", 0, 600, 10),
    ("Loudspeaker", "talk_gain", "Speaking from the phone: volume boost (dB)", 0, 20, 1),
]
TOGGLES = [  # (section, key, label)
    ("Mover", "mover_inv_l", "Left track runs the wrong way (turn round)"),
    ("Mover", "mover_inv_r", "Right track runs the wrong way (turn round)"),
    ("Mover", "mover_swap", "Left and right tracks swapped"),
    ("Mover", "mover_sim_show", "Simulation: show the stick even without a mover or motor driver (to try it out)"),
    ("Simulator", "sim_eco", "Simulator: fewer pictures (the simulator draws only what is fetched)"),
    ("Simulator", "notify_sandbox", "Simulation: messages into the test inbox instead of to the phone (nobody is disturbed)"),
    ("Simulator", "train_night_on", "Training night: every night test runs in several scenes, optimization, training pictures"),
    ("Simulator", "rover_alarm", "Rover: at a person alarm drive there by itself (simulator)"),
    ("Simulator", "fa_learn_auto", "False alarm marked: re-enact it in the simulator and learn from it"),
    ("Simulator", "rehearsal_on_arm", "Night rehearsal by itself when arming in the simulation"),
    ("Simulator", "weekcheck_on", "Recognition check every week (Sunday night) with a warning when it got worse"),
    ("Simulator", "sim_auto", "Find the simulator in the network by itself (and take over its address)"),
    ("Simulator", "sim_autostart", "Switch the simulation on by itself as soon as a simulator is online (and off again when none is left)"),
    ("Simulator", "sim_autoupd", "Update the simulator by itself (the setting «Neue Versionen» of the simulator)"),
    ("Simulator", "sim_separate", "The simulation has its own settings (when switching back: ask which changes to take over)"),
    ("Simulator", "sim_basis_show", "Show the basic simulator (MoveEye Sim · Basis, the old Python simulator)"),
    ("AI detection", "species_on", "Recognise the animal species (second AI model - see the guide)"),
    ("Setup", "desktop_notice", "Small message on the Pi's desktop when MoveEye starts in the background"),
    ("Solar panel", "solar_on", "Solar panel with current meter (INA219 on I2C)"),
    ("Battery", "night_warn", "Push message in the evening when the battery will probably not last until sunrise"),
    ("GPS module", "gpsmod_on", "Own GPS module (USB or serial; gpsd is used if installed)"),
    ("GPS module", "gps_theft", "Theft tracking: alarm when the armed device is carried away, then its position every 5 minutes"),
    ("Storm warning", "storm_on", "Storm warning (push message)"),
    ("Storm warning", "storm_forecast", "Also from the weather forecast: gusts in the next 12 hours (sends the location to Open-Meteo)"),
    ("Extra sensors", "sens_on", "Extra sensors on"),
    ("Extra sensors", "rf433_on", "433 MHz radio sensors (RTL-SDR stick + program rtl_433)"),
    ("Extra sensors", "zigbee_on", "Zigbee sensors (Zigbee2MQTT - needs MQTT)"),
    ("Extra sensors", "ble_on", "Bluetooth tags (RuuviTag - needs python3-bleak)"),
    ("Power saving", "eco_pir", "With a motion detector (PIR): only 1 picture per second while all is quiet"),
    ("Camera / Servos", "track_person", "Follow detected person (auto pan/tilt)"),
    ("Camera / Servos", "track_motion", "Also follow animals and other movement (when no person is in the picture)"),
    ("Camera / Servos", "invert_pan", "Invert pan direction"),
    ("Camera / Servos", "invert_tilt", "Invert tilt direction"),
    ("Camera / Servos", "lens_check", "Warn when the lens is fogged or dirty (picture blurred for 15 minutes)"),
    ("Setup", "temp_alarm_on", "Temperature alarm (e.g. a pet in the caravan): push when too hot or too cold"),
    ("Setup", "dev_area", "Developer area (own network, with its own PIN) - only for the developer"),
    ("Camera / Servos", "cam_mirror", "Mirror picture (left ↔ right)"),
    ("Patrol", "patrol", "Patrol active"),
    ("AI detection", "ai_enabled", "AI person detection (SSD MobileNet V2)"),
    ("AI detection", "show_objects", "Mark all detected objects (cars, animals, ...)"),
    ("AI detection", "ai_require", "Motion persons need AI confirmation"),
    ("AI detection", "ai_zoom", "AI magnifier: look again, enlarged, at small moving things (persons far away)"),
    ("AI detection", "night_strict", "At night stricter: a person found only by movement must stand upright (against animals)"),
    ("AI detection", "size_check", "Size check: much smaller than a person at that place = no person (learns from the persons the AI confirmed)"),
    ("Web stream", "web_stream", "Web stream + remote control (port 5000)"),
    ("Web stream", "ext_on", "Picture for other programs (Home Assistant, recorder, VLC) with a secret address"),
    ("Web stream", "rtsp_on", "RTSP video for recorders (needs mediamtx; uses CPU)"),
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
    ("Low light", "lowlight_view", "In the dark also brighten the picture you see (live, recordings)"),
    ("Low light", "nightvision", "Night vision look: green picture, thermal outlines and temperatures"),
    ("Setup", "gps_phone", "Take the location from the phone (the page must be open over https)"),
    ("Setup", "gps_tag", "GPS position in photos and videos"),
    ("Setup", "map_online", "Recordings map and place names from the internet (OpenStreetMap)"),
    ("Setup", "env_on", "Temperature sensor (BME280 / BMP280 on I2C or DS18B20 on GPIO 4), if connected"),
    ("Low light", "nightvision_auto", "Night vision automatically at night (sunset to sunrise)"),
    ("Relays", "relays_on", "Auto relays enabled"),
    ("Notifications", "notify_on", "Send notifications"),
    ("Notifications", "notify_prealarm", "Pre-alarm push: message at the first movement"),
    ("Notifications", "prealarm_photo", "Pre-alarm push with a small picture"),
    ("Notifications", "browser_alarm", "Alarm sound in open browsers (switch on with the bell at the top)"),
    ("Notifications", "notify_network", "Push message with the address when the Pi joins a network"),
    ("Notifications", "notify_remote", "Push message when somebody watches from outside (Tailscale)"),
    ("SMS (LTE stick)", "sms_on", "Alarm also as SMS (person, sabotage, warm body, noise)"),
    ("SMS (LTE stick)", "sms_only_offline", "Only when push messages cannot be sent (no internet)"),
    ("MQTT / Home Assistant", "mqtt_on", "MQTT on (state, events, commands)"),
    ("MQTT / Home Assistant", "mqtt_tls", "Encrypted (TLS, usually port 8883)"),
    ("MQTT / Home Assistant", "mqtt_discovery", "Home Assistant finds MoveEye by itself (discovery)"),
    ("Recording", "share_logo", "Shared pictures and videos with a small MoveEye logo"),
    ("Recording", "share_gps", "Send the location along when sharing pictures and videos"),
    ("Recording", "share_blur_faces", "Blur faces when sharing (only the shared copy, the original stays)"),
    ("Recording", "loop_on", "Continuous recording (all the time, few pictures per second) with a timeline"),
    ("Deterrence", "deter_always", "Also when disarmed (e.g. keep animals out of the garden)"),
    ("Theft protection", "tamper_on", "Sabotage alarm: camera covered or turned away (when armed)"),
    ("Reference scan", "refscan_on_arm", "Compare with the reference when armed"),
    ("Reference scan", "refscan_push", "Push message when something is missing"),
    ("Reference scan", "refscan_push_all", "Push message also for new or changed things"),
    ("Reference scan", "refscan_pano_on", "Panorama report «Missing things» every morning (separate from the night report)"),
    ("Theft protection", "tamper_motion", "Motion sensor (MPU-6050, if fitted): alarm when the device is moved or knocked over"),
    ("Theft protection", "tamper_power", "Power cut while armed = alarm (needs the UPS HAT)"),
    ("Backup", "backup_all", "Copy all recordings (otherwise only alarm recordings: armed or with a person)"),
    ("Notifications", "webpush_on", "Web push: alarm messages also to browsers that switched it on (no app needed)"),
    ("Notifications", "pushover_on", "Pushover: alarm messages also to the Pushover app (iPhone: can ring when muted)"),
    ("Notifications", "msg_icons", "Symbols in messages and the log (🚶 person, 🦊 animal, 🛑 sabotage …)"),
    ("Notifications", "msg_keyword_on", "Keyword at the start of every message (MoveEye-ALARM, MoveEye-WAERME …: for iPhone shortcuts)"),
    ("Notifications", "email_on", "E-mail: messages also by e-mail (the iPhone can start a shortcut from it)"),
    ("Notifications", "pushover_emergency", "Pushover: alarms as emergency (critical alert, repeats until confirmed)"),
    ("Updates", "update_auto", "Look for new versions by itself (every 3 hours)"),
    ("Updates", "update_install", "Install new versions automatically"),
    ("Updates", "update_fast", "Test mode: get new versions at once (looks on GitHub every minute and installs right away, also while armed; while on, the other update switches do not count)"),
    ("Updates", "news_popup", "After an update: show briefly what is new and what comes next"),
    ("Updates", "update_install_armed", "Automatic update also while armed (otherwise only when disarmed)"),
    ("Updates", "update_unsigned", "Also accept unsigned versions (not recommended - only for own builds)"),
    ("Battery", "ups_on", "UPS HAT (battery pack on the Pi): use it when found"),
    ("Battery", "ups_push", "UPS HAT: push message at a power cut / when power is back"),
    ("Battery", "ups_invert", "UPS HAT: charging and discharging are shown the wrong way round"),
    ("Updates", "update_push", "Push message when a new version is there"),
    ("Night report", "report_on", "Night report: push message in the morning with what happened in the night"),
    ("Night report", "weekrep_on", "Weekly detection report: push once a week with the trend and a tip"),
    ("Night report", "weekrep_sim", "Weekly report: with the week in the simulator (visits, animals, recognised persons)"),
    ("Night report", "weather_on", "Day overview: weather from the internet (Open-Meteo; the location is sent there)"),
    ("Night report", "diary_on", "Note animals, persons and noises (animal diary + night report)"),
    ("Power saving", "eco_on", "Power saving mode: fewer pictures while all is quiet"),
    ("Power saving", "eco_view_full", "Full speed while somebody watches the live picture"),
    ("Camping / protection", "time_from_browser", "Take the clock from the phone (when the Pi has no internet time)"),
    ("Thermal camera", "thermal_alarm", "Alarm when a warm body moves inside the zones"),
    ("Thermal camera", "thermal_need_motion", "Only warm bodies that move (ignore warm stones, engines)"),
    ("Timelapse", "timelapse_on", "Timelapse active"),
    ("Timelapse", "timelapse_return", "Return to the previous position afterwards"),
    ("Thermal camera", "thermal_on", "Overlay the thermal picture"),
    ("Thermal camera", "thermal_hot", "Show only the hot areas (people, animals, engines)"),
    ("Microphone", "noise_alarm", "Noise alarm: alarm when it gets loud (cracking, rustling, voices)"),
    ("Microphone", "noise_push", "Noise alarm: push message"),
    ("Clap switch", "clap_on", "Clap switch on"),
    ("Clap switch", "clap_beep", "Beep when recognised"),
    ("Clap switch", "clap_disarmed", "Only when not armed (claps of strangers switch nothing)"),
    ("Clap switch", "clap_practice", "Practice: only count and beep, switch nothing"),
    ("Bless you", "sneeze_on", "Say «Bless you!» after a sneeze"),
    ("Wake-up alarm", "wake_on", "Wake-up alarm on"),
    ("Wake-up alarm", "wake_light", "Switch the white light on"),
    ("Wake-up alarm", "wake_gestures", "Gestures: wave = snooze, sit up / get up = off"),
    ("Wake-up alarm", "wake_clap", "Clap twice = snooze (microphone)"),
    ("Wake-up alarm", "wake_away_night", "Look away during the night time (Night report → night time)"),
    ("Bless you", "sneeze_night", "Quiet at night (22 to 7 o'clock)"),
    ("Microphone", "audio_record", "Sound in the recordings"),
]
DE.update({"Mode": "Modus", "one switch for the whole device": "ein Schalter für das ganze Gerät", "Camping guard": "Camping-Wache", "Campfire games": "Lagerfeuer-Spiele", "Gamer": "Gamer", "Home / garden": "Zuhause / Garten", "Wildlife watching": "Wildbeobachtung", "Night guard": "Nachtwache", "Transport / rest": "Transport / Ruhe", "Own settings": "Eigene Einstellungen", "no mode": "kein Modus", "since": "seit", "Mode switched": "Modus gewechselt", "Guard during the games": "Wache während der Spiele", "needs mains power": "braucht Netzstrom", "runs on the battery": "läuft auf Akku", "under-voltage: the power supply is too weak": "Unterspannung: das Netzteil ist zu schwach", "The gamer mode needs mains power: ": "Der Gamer-Modus braucht Netzstrom: ", "unknown mode": "unbekannter Modus", "Back to the camping guard at": "Zurück zur Camping-Wache um", "or below": "oder unter", "or battery below": "oder Akku unter", "battery": "Akku", "never": "nie", "Your own settings, no mode.": "Deine eigenen Einstellungen, kein Modus.", "Campfire games ended (battery low) - camping guard on": "Lagerfeuer-Spiele beendet (Akku knapp) – Camping-Wache ein", "Campfire games ended (time) - camping guard on": "Lagerfeuer-Spiele beendet (Zeit) – Camping-Wache ein"})   # modes (2.95.47)
DE.update({    # mover (2.94.0)
    "Mover": "Mover",
    "Mover (tracked vehicle)": "Mover (Kettenfahrzeug)",
    "Motor driver": "Motortreiber",
    "Motor driver: address (I2C)": "Motortreiber: Adresse (I2C)",
    "Top speed (%)": "Höchstgeschwindigkeit (%)",
    "Turning speed (%)": "Drehgeschwindigkeit (%)",
    "Gentle start and stop (seconds)": "Sanft anfahren und bremsen (Sekunden)",
    "Left track runs the wrong way (turn round)": "Linke Kette läuft falsch herum (umdrehen)",
    "Right track runs the wrong way (turn round)": "Rechte Kette läuft falsch herum (umdrehen)",
    "Left and right tracks swapped": "Linke und rechte Kette vertauscht",
    "automatic: on when the motor driver is found": "automatisch: an, wenn der Motortreiber gefunden wird",
    "Motor HAT (Adafruit or compatible): M1 left, M2 right": "Motor HAT (Adafruit oder kompatibel): M1 links, M2 rechts",
    "Waveshare Motor Driver HAT: A left, B right": "Waveshare Motor Driver HAT: A links, B rechts",
    "the address is the one of the servo driver": "die Adresse ist die des Servo-Treibers",
    "no motor driver found": "kein Motortreiber gefunden",
    "motor driver found": "Motortreiber gefunden",
    "simulated": "simuliert",
    "test only - nothing moves": "nur Test – nichts fährt",
    "Simulation: show the stick even without a mover or motor driver (to try it out)": "Simulation: den Stick auch ohne Mover oder Motortreiber zeigen (zum Ausprobieren)",
    "stick shown for testing (the simulator has no mover)": "Stick zum Testen eingeblendet (der Simulator hat keinen Mover)",
    "the simulator has no mover": "der Simulator hat keinen Mover (im Simulator «Mover simulieren» einschalten)",
    "A tracked vehicle under MoveEye: the second stick drives it (up = forward, down = back, sideways = turn on the spot). The motor driver (Motor HAT with PCA9685 + TB6612 on I2C) is found by itself - without it the stick stays hidden. Without a new command for 0.6 s both tracks stop.": "Ein Kettenfahrzeug unter MoveEye: der zweite Stick fährt es (hoch = vorwärts, runter = rückwärts, seitlich = an Ort drehen). Der Motortreiber (Motor HAT mit PCA9685 + TB6612 an I2C) wird von selbst gefunden – ohne ihn bleibt der Stick verborgen. Kommt 0,6 s lang kein neuer Befehl, halten beide Ketten an.",
})
DE.update({    # window in the look of the web page (2.25.0)
    "Weather & system": "Wetter & System", "Slow": "Langsam", "Medium": "Mittel", "Fast": "Schnell", "Speed: slow": "Tempo: langsam", "Speed: medium": "Tempo: mittel", "Speed: fast": "Tempo: schnell",
    "Calibrate": "Kalibrieren", "Waypoint": "Wegpunkt", "Thermal": "Wärme", "Marks": "Markieren", "Lamp": "Licht", "IR light": "IR-Licht",
    "Follow": "Folgen", "Record": "Aufnahme", "Photo": "Foto", "Round": "Runde", "Pendulum": "Pendel",
    "Camera to the middle": "Kamera in die Mitte", "Learn the picture again (after moving the camera)": "Bild neu lernen (nach dem Verschieben der Kamera)",
    "Save the current position as waypoint for the patrol": "Aktuelle Position als Wegpunkt für die Patrouille speichern",
    "Clear waypoints": "Wegpunkte löschen", "Clear all waypoints?": "Alle Wegpunkte löschen?",
    "Thermal picture over the live picture": "Wärmebild über dem Live-Bild", "Mark detected objects (animals, cars ...)": "Erkannte Objekte markieren (Tiere, Autos …)",
    "White light on / off": "Weisses Licht ein / aus", "Infrared light on / off": "Infrarot-Licht ein / aus", "Follow a detected person": "Einer erkannten Person folgen",
    "Patrol: tap = off → back and forth (1-2-3-2-1) → round trip (1-2-3-1) → off": "Patrouille: Klick = Aus → hin und zurück (1-2-3-2-1) → Runde (1-2-3-1) → Aus",
    "Record now (max. 10 min) / stop": "Jetzt aufnehmen (max. 10 min) / stoppen", "Photo into the recordings": "Foto zu den Aufnahmen",
    "Relay: on / automatic": "Relais: Ein / zurück auf Automatisch", "Search settings …": "Einstellung suchen …", "No match": "Kein Treffer",
    "show / hide fields": "Felder ein-/ausblenden", "All quiet – I'm keeping watch!": "Alles ruhig – ich halte Wache!",
    "Happy Swiss National Day!": "Schöne Bundesfeier!", "Swap stick and buttons (left- / right-handed)": "Stick und Knöpfe tauschen (Links- / Rechtshänder)", "moving to waypoint": "fährt zu Wegpunkt", "waiting at": "wartet bei",
    "need 2+ waypoints": "mindestens 2 Wegpunkte nötig", "paused (tracking person)": "Pause (verfolgt Person)",
    "paused (manual control)": "Pause (Handsteuerung)", "System": "System", "Log": "Protokoll", "Expand all": "Alle öffnen", "Collapse all": "Alle schliessen",
})
DE.update({    # texts that were written twice in the code (German / English) - now one English text + translations
    "not possible in the demo": "In der Demo nicht möglich",
    "recording": "Aufnahme",
    "camera covered": "Kamera abgedeckt",
    "camera turned / picture changed": "Kamera verdreht / Bild verändert",
    "device moved": "Gerät bewegt",
    "device knocked over": "Gerät umgeworfen",
    "power cut while armed": "Strom getrennt (Schutz an)",
    "TAMPER ALARM": "SABOTAGE",
    "network": "Netzwerk",
    "Remote access: {who} is watching": "Fernzugriff: {who} schaut gerade zu",
    "remote access": "Fernzugriff",
    "o'clock": "Uhr",
    "Quiet night – nothing detected ({span}).": "Ruhige Nacht – nichts erkannt ({span}).",
    "thermal": "Wärmebild",
    "noise": "Geräusch",
    "{n} persons": "{n} Personen",
    "{n} person": "{n} Person",
    "{n} animals": "{n} Tiere",
    "{n} animal": "{n} Tier",
    "night report": "Nachtbericht",
    "power": "Strom",
    "Power cut – running on the battery ({pct} %)": "Stromausfall – läuft auf Akku ({pct} %)",
    "Power back – battery {pct} %": "Strom wieder da – Akku {pct} %",
    "Battery almost empty: about {pct} % ({hours:.1f} h)": "Akku fast leer: noch ca. {pct} % ({hours:.1f} h)",
    "Battery empty – the Pi shuts down cleanly": "Akku leer – der Pi wird sauber ausgeschaltet",
    "Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap": "Akku fast leer: noch ca. {pct} % ({hours:.1f} h) – bitte laden oder wechseln",
    "battery": "Akku",
    "Under-voltage: power bank almost empty or cable too weak": "Unterspannung: Powerbank fast leer oder Kabel zu schwach",
    "Memory card almost full: {free} MB free - the oldest recordings are deleted": "Speicherkarte fast voll: noch {free} MB frei - die ältesten Aufnahmen werden gelöscht",
    "memory": "Speicher",
    "Pi too hot: {temp:.0f} °C (limit {lim:.0f} °C) - check the cooling / ventilation": "Pi zu heiss: {temp:.0f} °C (Grenze {lim:.0f} °C) - Kühlung / Lüftung prüfen",
    "temperature": "Temperatur",
    "MoveEye is online in Wi-Fi {ssid}: {addr}": "MoveEye ist online im WLAN {ssid}: {addr}",
    "Program paused": "Programm pausiert",
    "Starts again at": "Startet wieder um",
    "While paused there is no monitoring and there are no alarms.": "Während der Pause gibt es keine Überwachung und keine Alarme.",
    "Start now": "Jetzt starten",
    "Starting …": "Startet …",
    "Automatic update to version {v} – the program restarts (about 20 s)": "Automatisches Update auf Version {v} – das Programm startet neu (ca. 20 s)",
    "New version {v} available - tap «Update now» on the page": "Neue Version {v} verfügbar - auf der Seite antippen: «Jetzt aktualisieren»",
    "Web push works ✓": "Web-Push funktioniert ✓",
    "test SMS - it works": "Test-SMS – funktioniert ✓",
    "1 · Join the device's Wi-Fi": "1 · Mit dem WLAN des Geräts verbinden",
    "Wi-Fi": "WLAN",
    "2 · Open the page (own Wi-Fi)": "2 · Seite öffnen (eigenes WLAN)",
    "Open the page (home network)": "Seite öffnen (Heimnetz)",
    "On the road (Tailscale)": "Von unterwegs (Tailscale)",
    "<li>Scan the QR code with the phone camera.</li><li>Open the page; the first time the setup assistant guides you through password and push messages.</li><li>Share → «Add to Home Screen»: start MoveEye like an app.</li><li>Arm the protection: big «Armed» button at the top.</li>": "<li>QR-Code mit der Handy-Kamera scannen.</li><li>Seite öffnen, beim ersten Mal führt der Einrichtungs-Assistent durch Passwort und Push-Nachrichten.</li><li>Teilen → «Zum Home-Bildschirm»: MoveEye wie eine App starten.</li><li>Schutz Schutz einschalten: grosse Taste «Schutz» oben.</li>",
    "Quick start": "Kurzanleitung",
    "Quick start – print it and keep it with the device": "Kurzanleitung – zum Ausdrucken und ins Gehäuse legen",
    "No address found (network?)": "Keine Adresse gefunden (Netzwerk?)",
    "Note: the Wi-Fi code contains the password – do not post the card in public.": "Achtung: der WLAN-Code enthält das Passwort – Karte nicht öffentlich aushängen.",
    "Print": "Drucken",
    "saved {t}": "gespeichert {t}",
    "loaded: {a} settings, {b} waypoints, {c} relays, {d} schedules": "geladen: {a} Einstellungen, {b} Wegpunkte, {c} Relais, {d} Zeitpläne",
    "save failed": "Speichern fehlgeschlagen",
    "defaults": "Standardwerte",
    "defaults (no file yet)": "Standardwerte (noch keine Datei)",
    "GPIO {n} is used by a servo": "GPIO {n} wird von einem Servo benutzt",
    "GPIO {n} is already used by another relay": "GPIO {n} wird schon von einem anderen Relais benutzt",
    "GPIO {n} is used by the thermal camera": "GPIO {n} wird von der Wärmebildkamera benutzt",
    "GPIO {n} is used by a light": "GPIO {n} wird von einem Licht benutzt",
    "maximum {n} relays": "maximal {n} Relais",
    "maximum {n} schedules": "maximal {n} Zeitpläne",
    "maximum {n} extra cameras": "maximal {n} Zusatzkameras",
    "Guest view · watch only · tap the picture = full screen": "Gast-Ansicht · nur zuschauen · Tippen aufs Bild = Vollbild",
    "access expired": "Zugang abgelaufen",
    "person in view": "Person im Bild",
    "quiet": "ruhig",
})
DE.update({    # 2.29.0
    "Night vision look: green picture, thermal outlines and temperatures": "Nachtsicht-Look: grünes Bild, Wärme-Umrisse und Temperaturen",
    "Night vision automatically at night (sunset to sunrise)": "Nachtsicht automatisch in der Nacht (Sonnenuntergang bis -aufgang)",
    "Night vision": "Nachtsicht",
    "Night vision: green picture, thermal outlines and temperatures": "Nachtsicht: grünes Bild, Wärme-Umrisse und Temperaturen",
})
DE.update({    # 2.30.0
    "Take the location from the phone (the page must be open over https)": "Standort vom Handy übernehmen (die Seite muss über https offen sein)",
    "GPS position in photos and videos": "GPS-Position in Fotos und Videos",
    "Location": "Standort",
    "from the phone": "vom Handy",
    "fixed (settings)": "fest (Einstellungen)",
    "unknown – the phone shares it only over the https page": "unbekannt – das Handy gibt ihn nur über die https-Seite weiter",
})
DE.update({    # 2.31.0
    "Temperature sensor (BME280 / BMP280 on I2C or DS18B20 on GPIO 4), if connected": "Temperaturfühler (BME280 / BMP280 an I2C oder DS18B20 an GPIO 4), falls angeschlossen",
    "Temperature sensor: correction (°C)": "Temperaturfühler: Korrektur (°C)",
    "Outside": "Aussen",
    "no temperature sensor": "kein Temperaturfühler",
    "Outside temperature": "Aussentemperatur",
})
DE.update({    # 2.32.0
    "Day overview": "Tagesübersicht",
    "Persons": "Personen",
    "Animals": "Tiere",
    "Warm bodies": "Warme Körper",
    "Noises": "Geräusche",
    "Photos": "Fotos",
    "Sensor": "Fühler",
    "Temperature (sensor)": "Temperatur (Fühler)",
    "Temperature (weather)": "Temperatur (Wetter)",
    "Rain / humidity": "Regen / Feuchte",
    "Person": "Person",
    "Animal": "Tier",
    "Warm body": "Warmer Körper",
    "Noise": "Geräusch",
    "No measurements for this day yet.": "Für diesen Tag gibt es noch keine Messwerte.",
    "Weather from the internet: switch on under Notifications → Night report.": "Wetter aus dem Internet: einschalten unter Benachrichtigungen → Nachtbericht.",
    "No weather for this day": "Kein Wetter für diesen Tag",
    "no location": "kein Standort",
    "Day overview: weather from the internet (Open-Meteo; the location is sent there)": "Tagesübersicht: Wetter aus dem Internet (Open-Meteo; dafür wird der Standort dorthin geschickt)",
    "clear": "klar",
    "partly cloudy": "leicht bewölkt",
    "cloudy": "bewölkt",
    "fog": "Nebel",
    "drizzle": "Nieselregen",
    "rain": "Regen",
    "snow": "Schnee",
    "showers": "Schauer",
    "thunderstorm": "Gewitter",
    "new moon": "Neumond",
    "waxing crescent": "zunehmende Sichel",
    "first quarter": "erstes Viertel",
    "waxing gibbous": "zunehmender Mond",
    "full moon": "Vollmond",
    "waning gibbous": "abnehmender Mond",
    "last quarter": "letztes Viertel",
    "waning crescent": "abnehmende Sichel",
})
DE.update({    # 2.37.0
    "Send the location along when sharing pictures and videos": "Ort beim Teilen von Bildern und Videos mitschicken",
})
DE.update({    # 2.34.0
    "Recordings map and place names from the internet (OpenStreetMap)": "Karte und Ortsnamen bei den Aufnahmen aus dem Internet (OpenStreetMap)",
})
def tk_main_on(sec):
    """2.95.71: is the main function of this settings topic on? (the same as MAINSW on the web page)"""
    g = CFG.get
    try:
        return bool({
            "Camping / protection": lambda: g("camping"), "Power saving": lambda: g("eco_on"), "Battery": lambda: g("ups_on"),
            "Theft protection": lambda: g("tamper_on") or g("tamper_motion") or g("tamper_power"), "Notifications": lambda: g("notify_on"),
            "Night report": lambda: g("report_on"), "SMS (LTE stick)": lambda: g("sms_on"), "Detection": lambda: g("detection_on"),
            "AI detection": lambda: g("ai_enabled"), "Vehicle filter": lambda: g("car_filter"), "Rain": lambda: g("rain_auto"), "Wind": lambda: g("wind_auto"),
            "Low light": lambda: g("lowlight_auto") or g("nightvision") or g("nightvision_auto"), "Auto-tune": lambda: g("auto_tune"),
            "Camera / Servos": lambda: g("track_person"), "Patrol": lambda: g("patrol"), "Thermal camera": lambda: g("thermal_on") or g("thermal_alarm"),
            "Extra sensors": lambda: g("sens_on") and g("sensors"), "Storm warning": lambda: g("storm_on"), "GPS module": lambda: g("gpsmod_on"),
            "Solar panel": lambda: g("solar_on"), "Lights": lambda: g("light_white", "off") != "off" or g("light_ir", "off") != "off",
            "Microphone": lambda: g("audio_in"), "Loudspeaker": lambda: g("siren_on") and g("siren_on") != "off", "Recording": lambda: g("record"),
            "Timelapse": lambda: g("timelapse_on"), "Backup": lambda: g("backup_type") and g("backup_type") != "off", "Relays": lambda: g("relays_on"),
            "Web stream": lambda: g("web_stream"), "MQTT / Home Assistant": lambda: g("mqtt_on"), "Updates": lambda: g("update_auto") or g("update_fast"),
            "Simulator": lambda: sim_live(), "Mover": lambda: g("mover_on"), "Guest access": lambda: g("guest_on"),
            "Reference scan": lambda: bool(refscan_meta())}.get(sec, lambda: False)())
    except Exception:
        return False


TK_GROUP_ICONS = {"alarm": "🛡", "notify": "⚠", "sched": "🗓", "detect": "◎", "camera": "▣", "sensors": "◉", "power": "⚡", "net": "📶", "security": "🔐", "sys": "⚙", "simset": "⚗"}
TK_TAB_HEAD = {"alarm": "Protection", "detect": "Settings"}     # 2.98.0: the tabs of the web page as headings

TK_SUB_ICONS = {"Camping / protection": "⌂", "Power saving": "◔", "Battery": "▮", "Theft protection": "⚷", "Reference scan": "◎", "Notifications": "✉",
                "Night report": "☾", "Messages": "✎", "SMS (LTE stick)": "☏", "Detection": "◎", "AI detection": "⌬",
                "Walking recognition": "➜", "Vehicle filter": "⛀", "Rain": "☂", "Wind": "≋", "Low light": "◐", "Auto-tune": "✱",
                "Camera / Servos": "✥", "Patrol": "↻", "Video source": "▣", "Servo driver": "⚒", "Lights": "☀", "Deterrence": "⚠",
                "Microphone": "♪", "Loudspeaker": "♫", "Clap switch": "✋", "Bless you": "☺", "Wake-up alarm": "⏰", "Recording": "●", "Timelapse": "◷", "Backup": "☁", "Relays": "⚡",
                "Schedule": "▦", "Setup": "⊕", "Wi-Fi / hotspot": "⌁", "Web stream": "⇅", "Security": "⚿", "Guest access": "⚇",
                "MQTT / Home Assistant": "⇆", "Updates": "⬆", "Extra sensors": "◉", "Simulator": "⚗", "Storm warning": "≈", "GPS module": "✈", "Solar panel": "☼", "Mover": "⇕"}

TK_GROUPS = [  # (id, name, topics; None = "fine-tuning" line) - 2.98.0: the same groups as the web page, «Schutz» first, then «Einstellungen»
    ("alarm", "Protection", ["Camping / protection", "Theft protection", "Reference scan", "Backup"]),
    ("notify", "What happens at an alarm?", ["Notifications", "Deterrence", "Recording", "Messages", "SMS (LTE stick)", "Night report"]),
    ("sched", "Zones, schedule, presence", ["Schedule"]),
    ("detect", "Detection", ["Improve detection", "Detection", "AI detection", "Thermal camera", None, "Walking recognition", "Vehicle filter", "Rain", "Wind", "Low light", "Auto-tune"]),
    ("camera", "Cameras & head", ["Camera / Servos", "Patrol", "Video source", "Timelapse", "Mover", None, "Servo driver"]),
    ("sensors", "Devices & sensors", ["Lights", "Microphone", "Loudspeaker", "Relays", "Extra sensors", "Clap switch", "Bless you", "Wake-up alarm", "Storm warning", "GPS module"]),
    ("power", "Power supply", ["Battery", "Power saving", "Solar panel"]),
    ("net", "Network & access", ["Wi-Fi / hotspot", "Web stream", "Guest access", "MQTT / Home Assistant"]),
    ("security", "Security", ["Security"]),     # 573: password, users, app keys, encrypted login, security check in one place
    ("sys", "System", ["Setup", "Updates"]),
]
# 2.98.14 (Konzept): which tab shows a group (like the web page); the simulator settings are in the tab Simulator
TK_PANEL_TABS = ("protect", "settings", "sim")
TK_GROUP_TAB = {"alarm": "protect", "notify": "protect", "theft": "protect", "sched": "protect"}
TK_SIM_GROUPS = [("simset", "Settings of the simulation", ["Simulator"])]
TK_PSEUDO = {"Improve detection"}
TK_AI_MODEL_KEYS = ("ai_model", "ai_own_url", "ai_own_auto")   # 2.98.23 (Konzept): shown together in the group «KI-Modell» (section AI detection)
TK_SPECIES_KEYS = ("species_on", "species_model", "species_norm", "species_conf")   # aufr (Konzept): the group «Tierart» (like «KI-Modell»)
SECTIONS = ["Wake-up alarm", "Reference scan", "Mover", "Simulator", "Extra sensors", "Storm warning", "GPS module", "Solar panel", "Night report", "Battery", "Guest access", "Messages", "Microphone", "Loudspeaker", "Clap switch", "Bless you", "Lights", "Servo driver", "Power saving", "Updates", "Camping / protection", "Camera / Servos", "Video source", "Wi-Fi / hotspot", "Schedule", "Relays", "Timelapse", "Thermal camera", "Patrol", "AI detection", "Notifications", "Web stream", "Auto-tune",
            "Detection", "Low light", "Walking recognition", "Vehicle filter", "Rain", "Wind", "Recording", "Backup", "Theft protection", "Deterrence", "MQTT / Home Assistant", "SMS (LTE stick)", "Setup", "Security"]


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
VIEW_GROUPS = ["Header", "Panels", "Settings sections"]
VIEW_ITEMS = [  # (group, key, label)
    ("Header", "title", "Title"), ("Header", "hdr_buttons", "Header buttons"),
    ("Header", "b_arm", "Armed / disarmed"), ("Header", "b_person", "Persons"), ("Header", "b_count", "Persons total"),
    ("Header", "b_objects", "Objects"), ("Header", "b_rec", "Recording"), ("Header", "b_camp", "Camping profile"),
    ("Header", "b_eco", "Power saving"), ("Header", "b_tl", "Timelapse"), ("Header", "b_lights", "Lights"),
    ("Header", "b_therm", "Thermal camera"), ("Header", "b_patrol", "Patrol"), ("Header", "b_hs", "Own Wi-Fi (hotspot)"), ("Header", "b_remote", "Remote access"), ("Header", "b_batt", "Battery"), ("Header", "b_update", "New version"),
    ("Header", "b_relays", "Relays"), ("Header", "b_rain", "Rain"), ("Header", "b_wind", "Wind"), ("Header", "b_light", "Light level"),
    ("Header", "b_auto", "Auto-tune"), ("Header", "b_fps", "FPS"), ("Header", "b_env", "Outside temperature"), ("Header", "b_view", "Viewers"),
    ("Panels", "weather", "Weather"), ("Panels", "cpu", "System · CPU"),     # aufr: «Camera control» only in ◫ Ansicht (581, card «Controls»)
    ("Panels", "log", "Event log"), ("Panels", "settings_line", "Settings status"),
] + [("Settings sections", "sec:" + s, s) for s in SECTIONS]
STAT_TILES = []          # the statistics tiles were removed in 2.2.2 (FPS / persons / objects are in the header and the log)
TYPING = ("Entry", "TEntry", "Spinbox", "TSpinbox", "TCombobox", "TScale", "Listbox")


class Tip:
    """Small help text when the mouse rests on a button (the window has symbols like the web page)."""
    def __init__(self, w, text):
        self.w, self.text, self.tw, self.job = w, text, None, None
        w.bind("<Enter>", self._in, add="+"); w.bind("<Leave>", self._out, add="+"); w.bind("<ButtonPress>", self._out, add="+")

    def _in(self, _e=None):
        self._out(); self.job = self.w.after(600, self._show)

    def _show(self):
        self.job = None
        try:
            if self.tw is not None or not self.w.winfo_exists():
                return
            x, y = self.w.winfo_rootx() + 8, self.w.winfo_rooty() + self.w.winfo_height() + 4
            self.tw = tk.Toplevel(self.w); self.tw.wm_overrideredirect(True); self.tw.geometry(f"+{x}+{y}")
            tk.Label(self.tw, text=self.text, bg=C["field"], fg=C["txt"], font=("DejaVu Sans", 9), padx=8, pady=4, justify="left",
                     wraplength=320, highlightthickness=1, highlightbackground=C["line"]).pack()
        except tk.TclError:
            self.tw = None

    def _out(self, _e=None):
        if self.job is not None:
            try:
                self.w.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None
        if self.tw is not None:
            try:
                self.tw.destroy()
            except tk.TclError:
                pass
            self.tw = None


class StickPad(tk.Canvas):
    """Round joystick like the web page. Dragging starts where the mouse / finger lands (no jump), 12 % dead zone;
    the further out, the faster the camera turns. Orange ring = where the camera looks, numbered points = waypoints."""
    ORANGE, WPC = "#f59a4a", "#9fc3ff"

    def __init__(self, parent, app, size):
        super().__init__(parent, width=size, height=size, bg=C["panel"], highlightthickness=0, bd=0, cursor="fleur")
        self.app, self.S, self.R = app, size, size * 0.30
        self.o = None; self.dx = self.dy = 0.0; self.job = None
        self.bind("<ButtonPress-1>", self._press); self.bind("<B1-Motion>", self._drag); self.bind("<ButtonRelease-1>", self._release)
        self.draw()

    def _xy(self, pan, tilt):
        a = self.S * 0.1465; b = self.S - a
        return a + (b - a) * max(0.0, min(100.0, pan)) / 100.0, a + (b - a) * (1 - max(0.0, min(100.0, tilt)) / 100.0)

    def draw(self):
        mix = App._mix; P = C["panel"]; s = self.S; c = s / 2
        self.delete("all")
        self.create_oval(4, 4, s - 4, s - 4, fill=mix(P, "#000000", 0.25), outline=mix(P, C["acc"], 0.28), width=6)
        for txt, x, y in (("▲", c, 13), ("▼", c, s - 13), ("◀", 13, c), ("▶", s - 13, c)):
            self.create_text(x, y, text=txt, fill=C["mut"], font=("DejaVu Sans", 7))
        a = s * 0.1465
        self.create_rectangle(a, a, s - a, s - a, outline=mix(P, self.ORANGE, 0.5), dash=(3, 3))
        pts = [self._xy(w[0], w[1]) for w in WAYPOINTS]
        lc = mix(P, self.WPC, 0.55)
        if len(pts) > 1:
            self.create_line(*[v for pt in pts for v in pt], fill=lc, width=1)
        if len(pts) > 2 and CFG["patrol_mode"] == "loop":
            self.create_line(*pts[-1], *pts[0], fill=lc, width=1, dash=(3, 3))
        px, py = self._xy(CFG["pan"], CFG["tilt"])
        oc = mix(P, self.ORANGE, 0.4)
        self.create_line(a, py, s - a, py, fill=oc); self.create_line(px, a, px, s - a, fill=oc)
        kx, ky, kr = c + self.dx * self.R, c + self.dy * self.R, s * 0.2
        self.create_oval(kx - kr, ky - kr, kx + kr, ky + kr, fill=mix(C["acc"], "#ffffff", 0.18 if self.o else 0.1), outline=mix(C["acc"], "#000000", 0.15))
        dc = mix(P, self.WPC, 0.85 if CFG["patrol"] else 0.7)
        for n, (x, y) in enumerate(pts):
            self.create_oval(x - 7, y - 7, x + 7, y + 7, fill=mix(P, "#16233a", 0.7), outline=dc)
            self.create_text(x, y, text=str(n + 1), fill=dc, font=("DejaVu Sans", 7, "bold"))
        self.create_oval(px - 11, py - 11, px + 11, py + 11, outline=mix(P, self.ORANGE, 0.35), width=3)
        self.create_oval(px - 8, py - 8, px + 8, py + 8, outline=self.ORANGE, width=2)

    def _press(self, e):
        self.o = (e.x, e.y); self.dx = self.dy = 0.0
        if self.job is None:
            self._tick()

    def _drag(self, e):
        if self.o is None:
            return
        dx, dy = (e.x - self.o[0]) / self.R, (e.y - self.o[1]) / self.R
        m = math.hypot(dx, dy)
        if m > 1:
            dx, dy = dx / m, dy / m
        self.dx, self.dy = dx, dy

    def _tick(self):
        self.job = None
        if self.o is None:
            return
        m = math.hypot(self.dx, self.dy)
        x, y = (self.dx, -self.dy) if m >= 0.12 else (0.0, 0.0)
        stick_camera(x, y, self.app.stick_speed)
        self.app._pos_label(); self.draw()
        self.job = self.after(60, self._tick)

    def _release(self, _e=None):
        self.o = None; self.dx = self.dy = 0.0
        if self.job is not None:
            self.after_cancel(self.job); self.job = None
        stick_camera(0, 0)
        self.draw()


class MoverPad(tk.Canvas):
    """The second stick (from 2.94.0): drives the mover (tracked vehicle). Up = forward, down = back, sideways = turn on
    the spot; release = stop. Green bars on the left and right = how fast each track runs."""

    def __init__(self, parent, app, size):
        super().__init__(parent, width=size, height=size, bg=C["panel"], highlightthickness=0, bd=0, cursor="fleur")
        self.app, self.S, self.R = app, size, size * 0.30
        self.o = None; self.dx = self.dy = 0.0; self.job = None
        self.bind("<ButtonPress-1>", self._press); self.bind("<B1-Motion>", self._drag); self.bind("<ButtonRelease-1>", self._release)
        self.draw()

    def draw(self):
        mix = App._mix; P = C["panel"]; s = self.S; c = s / 2
        self.delete("all")
        self.create_oval(4, 4, s - 4, s - 4, fill=mix(P, "#000000", 0.25), outline=mix(P, C["grn"], 0.3), width=6)
        for txt, x, y in (("⇧", c, 14), ("⇩", c, s - 14), ("↺", 14, c), ("↻", s - 14, c)):
            self.create_text(x, y, text=txt, fill=C["mut"], font=("DejaVu Sans", 9))
        for side, val in ((0, MOVER["l"]), (1, MOVER["r"])):
            x0 = s * (0.09 if side == 0 else 0.86); x1 = x0 + s * 0.05; top, bot = s * 0.2, s * 0.8
            self.create_rectangle(x0, top, x1, bot, outline=mix(P, C["mut"], 0.3))
            h = (bot - top) / 2 * min(1.0, abs(val))
            if h > 1:
                y0, y1 = (c - h, c) if val > 0 else (c, c + h)
                self.create_rectangle(x0, y0, x1, y1, fill=C["grn"] if val > 0 else C["org"], outline="")
        kx, ky, kr = c + self.dx * self.R, c + self.dy * self.R, s * 0.2
        self.create_oval(kx - kr, ky - kr, kx + kr, ky + kr, fill=mix(C["grn"], "#ffffff", 0.18 if self.o else 0.05), outline=mix(C["grn"], "#000000", 0.2))

    def _press(self, e):
        self.o = (e.x, e.y); self.dx = self.dy = 0.0
        if self.job is None:
            self._tick()

    def _drag(self, e):
        if self.o is None:
            return
        dx, dy = (e.x - self.o[0]) / self.R, (e.y - self.o[1]) / self.R
        m = math.hypot(dx, dy)
        if m > 1:
            dx, dy = dx / m, dy / m
        self.dx, self.dy = dx, dy

    def _tick(self):
        self.job = None
        if self.o is None:
            return
        m = math.hypot(self.dx, self.dy)
        v, w = (-self.dy, self.dx) if m >= 0.12 else (0.0, 0.0)
        mover_drive(v, w, "window")
        self.draw()
        self.job = self.after(80, self._tick)

    def _release(self, _e=None):
        self.o = None; self.dx = self.dy = 0.0
        if self.job is not None:
            self.after_cancel(self.job); self.job = None
        mover_drive(0, 0, "window")
        self.draw()


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
        self.root.title("MoveEye 2.98.64")
        try:                                             # window / taskbar icon = the app icon
            import base64
            self._icon = tk.PhotoImage(data=base64.b64encode(app_icon_png(64)).decode())
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass
        self.root.geometry(f"{min(1360, self.root.winfo_screenwidth())}x{min(820, self.root.winfo_screenheight())}"); self.root.minsize(640, 400)
        self.video_only = False; self.is_fullscreen = False; self.photo = None
        self.open_secs = set(CFG["ui_open"])                    # open sidebar groups: kept in the settings file
        if not any(x.startswith("grp:") for x in self.open_secs):   # settings of an older version: start with "Alarm & camping" open
            self.open_secs = {"grp:alarm"}
        self.step_var = tk.StringVar(value="3")
        self.tab = "live"; self.stick_speed = 30.0; self.relay_prev = {}
        self.left_f = self.stick = self.l_wp = None; self.qs_tiles = {}; self.tab_btns = {}
        self.relay_err = ""; self._err_job = None; self._rb_pending = False; self._hold_job = None
        self.right_f = self.side_canvas = None
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        self.root.bind("<Control-t>", lambda e: self.toggle_theme())
        self.root.bind("<Control-l>", lambda e: self.toggle_lang())
        self.root.bind("<Control-b>", lambda e: self.toggle_sidebar())
        self.root.bind("<F9>", lambda e: self._sim_toggle("window (F9)"))
        for key, cmd in (("<Left>", "left"), ("<Right>", "right"), ("<Up>", "up"), ("<Down>", "down"), ("<Home>", "center")):
            self.root.bind_all(key, lambda e, c=cmd: self._key_move(c))
        self.root.bind_all("<Button-4>", lambda e: self._wheel(e, -1))
        self.root.bind_all("<Button-5>", lambda e: self._wheel(e, 1))
        self.root.bind_all("<MouseWheel>", lambda e: self._wheel(e, -1 if e.delta > 0 else 1))
        self._rebuild()
        if CFG.get("fullscreen"):
            self.toggle_fullscreen()
        self.root.after(30, self._update_video); self.root.after(500, self._update_state)
        self.root.after(2500, self._news)                  # 2.96.3: after an update: what is new

    def _news(self, force=False):
        """2.96.3: a small window «Neu in dieser Version» (once per version; «Nicht mehr anzeigen» switches it off)"""
        try:
            st = news_state("tk")
            if not (st["show"] or force):
                return
            top = tk.Toplevel(self.root); top.title("MoveEye " + st["version"]); top.configure(bg=C["panel"]); top.transient(self.root)
            tk.Label(top, text="✨ " + tr("New in this version"), bg=C["panel"], fg=C["fg"], font=("TkDefaultFont", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
            for it in st["items"] or [{"v": st["version"], "t": tr("No changes noted.")}]:
                tk.Label(top, text=it["v"] + "  " + it["t"], bg=C["panel"], fg=C["fg"], wraplength=520, justify="left").pack(anchor="w", padx=16, pady=2)
            if st["next"]:
                tk.Label(top, text="🔜 %s (%d/%d)" % (tr("Next in the makeover"), st["done"], st["total"]), bg=C["panel"], fg=C["fg"],
                         font=("TkDefaultFont", 11, "bold")).pack(anchor="w", padx=16, pady=(10, 2))
                for x in st["next"]:
                    tk.Label(top, text="%d. %s" % (x["n"], x["t"]), bg=C["panel"], fg=C.get("mut", C["fg"]), justify="left").pack(anchor="w", padx=24)
            bf = tk.Frame(top, bg=C["panel"]); bf.pack(fill="x", padx=16, pady=12)
            def close(off):
                if off:
                    CFG["news_popup"] = False
                news_seen("tk"); top.destroy()
            tk.Button(bf, text=tr("OK"), command=lambda: close(False)).pack(side="right")
            tk.Button(bf, text=tr("Do not show any more"), command=lambda: close(True)).pack(side="right", padx=8)
            top.protocol("WM_DELETE_WINDOW", lambda: close(False))
        except Exception as e:
            print("news:", e)

    # ---- (re)building the window ----------------------------------------
    def _rebuild(self):
        """(Re)create the whole window content - theme, language, shown/hidden fields, relays."""
        apply_theme()
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg=C["bg"])
        self.vars, self.value_labels, self.status_labels = {}, {}, {}
        self.sections = {}
        self.dragging = None; self._last_ev = None; self._pw_shown = False; self._pw_line = None
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
        """2.98.14: the settings are a tab now (like the web page) - Ctrl+B goes there and back to Live"""
        self._tab("settings" if self.tab != "settings" else "live")

    def toggle_theme(self):
        self._set("theme", "light" if CFG["theme"] == "dark" else "dark"); self._rebuild()

    def toggle_lang(self, x=None, y=None):
        """Menu with the five languages (Ctrl+L: next language)."""
        if x is None:
            i = (LANGS.index(cur_lang()) + 1) % len(LANGS)
            self._set("lang", LANGS[i]); self._rebuild(); return
        m = tk.Menu(self.root, tearoff=0, bg=C["panel"], fg=C["txt"], activebackground=C["acc"], activeforeground="#ffffff", font=("DejaVu Sans", 10))
        for k in LANGS:
            m.add_command(label=("● " if k == cur_lang() else "   ") + LANG_NAMES[k], command=lambda k=k: (self._set("lang", k), self._rebuild()))
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen); CFG["fullscreen"] = self.is_fullscreen
        if self.b_fs is not None and self.b_fs.winfo_exists():
            self.b_fs.config(bg=C["acc"] if self.is_fullscreen else C["panel"], fg="#ffffff" if self.is_fullscreen else C["txt"])

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
        m.add_command(label=tr("Settings") + "   (Ctrl+B)", command=self.toggle_sidebar)
        m.add_command(label=tr("Show all"), command=self.show_all)
        if self.tab == "live":
            m.add_command(label="◫ " + tr("View of the live page …"), command=self._tkv_dialog)     # 2.98.29 (581)
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

    def _sb(self, key, text, color=None, show=True):
        lbl = self.badges.get(key)
        if lbl is not None:
            if getattr(lbl, "_show", True) != show:
                lbl._show = show; self._flow_due = True
            lbl.config(text=text, fg=color or C["mut"], highlightbackground=color or C["line"],
                       bg=(C["badge_red_bg"] if color == C["red"] else C["field"]))

    def _flow(self, _e=None):
        """Badges wrap onto a second line when the window is narrow."""
        f = self.badge_f
        if f is None or not f.winfo_exists():
            return
        W = max(f.winfo_width(), 200); x = y = rowh = 0
        for w in self.badges.values():
            if not getattr(w, "_show", True):
                w.place_forget(); continue
            ww, hh = w.winfo_reqwidth(), w.winfo_reqheight()
            if x and x + ww > W:
                x = 0; y += rowh + 6; rowh = 0
            w.place(x=x, y=y); x += ww + 8; rowh = max(rowh, hh)
        if int(f.cget("height")) != y + rowh:
            f.configure(height=y + rowh)

    def _panel(self, parent):
        return tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=10)

    def _tk_live_land(self, w=None, h=None):
        """2.98.26: wide, low window (like Daniel's PC): the controls go right of the live picture instead of under it."""
        try:
            w = w or self.root.winfo_width(); h = h or self.root.winfo_height()
            if w < 50 or h < 50:
                w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        except Exception:
            return False
        return w >= 1000 and w >= h * 1.45

    def _win_w(self):
        w = self.root.winfo_width()
        return w if w > 50 else min(self.root.winfo_screenwidth(), 1360)

    def _layout(self, w=None):
        """(compact header, sidebar width, quick switches beside the stick) for a window width."""
        w = w or self._win_w()
        side = 0                                         # 2.98.14: no settings beside the picture - they have their tabs
        left = w - side - 60
        return (w < 1100, side, left >= 800)

    def _on_resize(self, e):
        if e.widget is self.root and not self.video_only and (self._layout(e.width) != getattr(self, "_lay", None)
                                                              or self._tk_live_land(e.width, e.height) != getattr(self, "_lay_land", None)):
            self._schedule_rebuild()

    def _build(self):
        r = self.root
        self._lay = self._layout(); self._lay_land = self._tk_live_land()
        if not getattr(self, "_resize_bound", False):
            self._resize_bound = True; r.bind("<Configure>", self._on_resize, add="+")
        self.stat, self.badges = {}, {}
        self.badge_f = self.b_fs = self.video = None
        self.p_rain = self.p_wind = self.l_rain = self.l_wind = self.l_boost = None
        self.l_cpu = self.p_cpu = self.cpu_canvas = self.l_cpu_info = self.log = None
        self.l_wifi = None; self.wifi_canvas = None
        self.l_pt = self.l_ctl_status = self.l_settings = None
        self.stick = self.l_wp = None; self.qs_tiles = {}; self.tab_btns = {}
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
        if self.tab not in [t for t, _ in self._tabs()]:
            self.tab = "live"
        if self.tab in TK_PANEL_TABS:                     # 2.98.14: Schutz / Einstellungen / Simulator: the settings over the whole width
            self.left_f = None
            self._build_sidebar(body, self.tab)
            return
        left = ttk.Frame(body, style="Bg.TFrame"); left.grid(row=0, column=0, sticky="nsew")
        side_open = False
        strip = tk.Frame(body, bg=C["bg"]); strip.grid(row=0, column=1, sticky="ns", padx=(6 if not self.is_shown("hdr_buttons") else 8, 6))
        for txt, cmd in [] if self.is_shown("hdr_buttons") else (("☰", self._view_menu),):
            l = tk.Label(strip, text=txt, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11, "bold"), width=2, pady=6,
                         cursor="hand2", highlightthickness=1, highlightbackground=C["line"])
            l.pack(pady=(0, 6)); l.bind("<Button-1>", lambda e, c=cmd: c())
        self._build_left(left)
        if side_open:
            self._build_sidebar(body)

    # ---- small look helpers (same look as the web page) --------------------
    @staticmethod
    def _mix(a, b, f):
        """Colour between a and b (f = 0 .. 1)."""
        a, b = a.lstrip("#"), b.lstrip("#")
        return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - f) + int(b[i:i + 2], 16) * f):02x}" for i in (0, 2, 4))

    def _btn2(self):
        return self._mix(C["panel"], C["txt"], 0.07)

    def _fbtn(self, parent, text, cmd, tip=None, primary=False, font=("DejaVu Sans", 9, "bold")):
        """Flat button like the web page (grey, a bit lighter when the mouse is over it)."""
        bg = C["acc"] if primary else self._btn2()
        hv = self._mix(bg, "#ffffff", 0.12) if primary else self._mix(C["panel"], C["txt"], 0.13)
        b = tk.Label(parent, text=text, bg=bg, fg="#ffffff" if primary else C["txt"], font=font, padx=8, pady=5, cursor="hand2",
                     highlightthickness=1, highlightbackground=C["line"])
        b.bind("<Enter>", lambda e: b.config(bg=hv)); b.bind("<Leave>", lambda e: b.config(bg=bg))
        b.bind("<Button-1>", lambda e: cmd())
        if tip:
            Tip(b, tip)
        return b

    def _ibtn(self, parent, text, cmd, tip, on=False):
        """Square symbol button of the header (like the web page: bell, menu, fullscreen)."""
        b = tk.Label(parent, text=text, width=2 if self._lay[0] else 3, pady=4, cursor="hand2", font=("DejaVu Sans", 11, "bold"),
                     bg=C["acc"] if on else C["panel"], fg="#ffffff" if on else C["txt"], highlightthickness=1, highlightbackground=C["line"])
        b.bind("<Button-1>", lambda e: cmd()); Tip(b, tip)
        return b

    def _card(self, parent, title=None):
        f = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=10)
        if title:
            tk.Label(f, text=title.upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        return f

    def _messages_win(self):
        """2.98.13: the push messages (like Verlauf → Nachrichten on the web page): what MoveEye sent, newest first"""
        w = getattr(self, "_msg_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); self._msg_fill(); return
        w = self._msg_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Message list")); w.configure(bg=C["bg"]); w.geometry("620x520")
        top = tk.Frame(w, bg=C["bg"]); top.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(top, text=tr("Everything MoveEye sent to your phone - and the messages on the ntfy server."), bg=C["bg"], fg=C["mut"],
                 font=("DejaVu Sans", 9), wraplength=420, justify="left").pack(side="left")
        tk.Button(top, text=tr("↻ Refresh"), command=self._msg_fill).pack(side="right")
        self._msg_txt = tk.Text(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), wrap="word", bd=0, padx=10, pady=8)
        self._msg_txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._msg_txt.tag_configure("tt", font=("DejaVu Sans", 10, "bold")); self._msg_txt.tag_configure("mt", foreground=C["mut"], font=("DejaVu Sans", 8))
        self._msg_txt.tag_configure("bad", foreground=C.get("red", "#ff453a"))
        self._msg_fill()

    def _msg_fill(self):
        t_ = getattr(self, "_msg_txt", None)
        if t_ is None or not t_.winfo_exists():
            return
        ICON = {"person": "🚨", "tamper": "🛑", "warm": "🔥", "noise": "🔊", "prealarm": "👀", "test": "🧪"}
        ST = {"sent": tr("sent"), "failed": tr("failed"), "test": tr("test inbox"), "none": tr("no push channel")}
        t_.config(state="normal"); t_.delete("1.0", "end")
        items = msglog_list()
        if not items:
            t_.insert("end", tr("No messages yet."), "mt")
        for m in items:
            t_.insert("end", ICON.get(m.get("ev"), "📩") + " " + (m.get("title") or "MoveEye") + "\n", "tt")
            if m.get("text"):
                t_.insert("end", m["text"] + "\n")
            t_.insert("end", datetime.fromtimestamp(float(m.get("t") or 0)).strftime("%a %d.%m. %H:%M:%S") + " · " + ST.get(m.get("status"), m.get("status", "")) +
                      ((" · " + m["where"]) if m.get("where") and m.get("status") == "sent" else "") + "\n\n", "bad" if m.get("status") == "failed" else "mt")
        t_.config(state="disabled")

    def _tabs(self):
        """2.98.14: the same 6 tabs as the web page: Live · Schutz · Verlauf · Einstellungen · Simulator · Mehr"""
        return [(k, lab) for k, _h, lab, _s in NAV_ITEMS]

    def _build_header(self):
        """Like the web page: dot + name + version, the tabs, symbol buttons on the right; the badges below."""
        show = self.is_shown
        badge_keys = [k for g, k, l in VIEW_ITEMS if g == "Header" and k.startswith("b_")]
        head = tk.Frame(self.root, bg=C["bg"]); head.pack(fill="x", padx=16, pady=(10, 0))
        top = tk.Frame(head, bg=C["bg"]); top.pack(fill="x")
        if show("title"):
            tl = tk.Frame(top, bg=C["bg"]); tl.pack(side="left")
            try:                                         # the app icon (orange camera head), like the web page
                import base64
                self._logo = tk.PhotoImage(data=base64.b64encode(app_icon_png(26 if self._lay[0] else 30)).decode())
                tk.Label(tl, image=self._logo, bg=C["bg"], bd=0).pack(side="left")
            except Exception:
                tk.Label(tl, text="●", bg=C["bg"], fg=C["acc"], font=("DejaVu Sans", 12)).pack(side="left")
            small = self._lay[0]
            nm = tk.Label(tl, text="MoveEye", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 12 if small else 15, "bold")); nm.pack(side="left", padx=(6, 0))
            if not small:
                vl = tk.Label(tl, text=APP_VERSION, bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 8), cursor="hand2"); vl.pack(side="left", padx=(8, 0), pady=(5, 0))
                vl.bind("<Button-1>", self._ver_tap, add="+"); Tip(vl, tr("About MoveEye"))       # 2.98.33: one tap = «About MoveEye» (584)
            Tip(nm, f"{tr('Build')} 2.98.64 · {tr('Pan/Tilt surveillance with AI, patrol & relay')}")
            self._egg_taps = []
            for w_ in tl.winfo_children():                # little extra
                w_.bind("<Button-1>", self._egg_tap, add="+")
            d_ = datetime.now()
            if (d_.month == 8 and d_.day == 1) or os.environ.get("MW_AUG1") == "1":
                self._aug1(tl)
        small_ = self._lay[0]
        tabs = tk.Frame(head if small_ else top, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=3, pady=3)
        self._tabs_row = tabs
        shorts = {k: sh for k, _h, _l, sh in NAV_ITEMS}
        self.tab_btns = {}
        for tid, lab in self._tabs():
            if small_ and self._win_w() < 760:
                lab = shorts.get(tid, lab)
            b = tk.Label(tabs, text=tr(lab), font=("DejaVu Sans", 9 if small_ else 10), padx=5 if small_ else 12, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 2), expand=small_, fill="x" if small_ else None); b.bind("<Button-1>", lambda e, t=tid: self._tab(t))
            self.tab_btns[tid] = b
        self._paint_tabs()
        if show("hdr_buttons"):
            ctl = tk.Frame(top, bg=C["bg"]); ctl.pack(side="right")
            lb = self._ibtn(ctl, cur_lang().upper(), lambda: None, tr("Language") + " (Ctrl+L)")
            lb.bind("<Button-1>", lambda e: self.toggle_lang(lb.winfo_rootx(), lb.winfo_rooty() + lb.winfo_height()))
            lb.config(width=3, font=("DejaVu Sans", 9, "bold")); lb.pack(side="right")
            self._ibtn(ctl, "◐", self.toggle_theme, tk_theme_tip(), on=bool(CFG.get("tk_night"))).pack(side="right", padx=(0, 6))   # Hell → Dunkel → Rotlicht (578)
            self._ibtn(ctl, "✉", self._messages_win, tr("Message list")).pack(side="right", padx=(0, 6))     # 2.98.13
            # 2.98.50 (Daniel): no 💬 in the header any more - feedback under System (see _feedback button below) and «About»
            self._ibtn(ctl, "◷", lambda: tk_timeline_win(self), tr("Night timeline")).pack(side="right", padx=(0, 6))   # 2.98.14 (575)
            self._ibtn(ctl, "?", lambda: self._g2_tour(self.tab, True), tr("Tour of this page")).pack(side="right", padx=(0, 6))   # 584
            self.b_fs = self._ibtn(ctl, "⇱", self.toggle_fullscreen, tr("Fullscreen (F11)"), on=self.is_fullscreen)
            self.b_fs.pack(side="right", padx=(0, 6))
            vb = self._ibtn(ctl, "☰", lambda: None, tr("View") + " – " + tr("show / hide fields"))
            vb.bind("<Button-1>", lambda e: self._view_menu(vb.winfo_rootx(), vb.winfo_rooty() + vb.winfo_height()))
            vb.pack(side="right", padx=(0, 6))
            self._ibtn(ctl, "?", self._open_help, tr("Manual") + "\n\n" + tr("Double-click video: video only · F11: fullscreen · Esc: back · Ctrl+B: settings panel · right-click video: show / hide fields")).pack(side="right", padx=(0, 6))
        keys = [k for k in badge_keys if show(k)]
        if keys:
            self.badge_f = tk.Frame(head, bg=C["bg"], height=30); self.badge_f.pack(fill="x", pady=(8, 0))
            texts = {"b_person": tr("No person"), "b_count": f"{tr('Persons total')}: 0", "b_objects": f"0 {tr('objects')}",
                     "b_rain": tr("No rain"), "b_wind": f"{tr('Wind')}: calm", "b_rec": tr("Idle"), "b_relays": tr("Relays"),
                     "b_patrol": tr("Patrol off"), "b_light": tr("Light ok"), "b_auto": tr("Auto-tune"), "b_fps": "– FPS", "b_arm": "🛡",
                     "b_camp": "⛺", "b_eco": "🍃", "b_env": "🌡", "b_tl": "⏱", "b_lights": "💡", "b_therm": "🌡", "b_hs": "📡", "b_remote": "🌐", "b_batt": "🔋", "b_update": "⬆", "b_view": "👁"}
            for k in keys:
                self.badges[k] = self._badge(self.badge_f, texts[k])
            if "b_count" in self.badges:
                self.badges["b_count"].bind("<Button-1>", lambda e: self._reset_count())
            if "b_update" in self.badges:
                self.badges["b_update"].bind("<Button-1>", lambda e: self._upd_new())
            self.badge_f.bind("<Configure>", self._flow)
            self.root.after(50, self._flow)
        if small_:                                        # 2.98.14: on a small screen the 6 tabs get a row of their own
            tabs.pack(fill="x", pady=(8, 0), before=self.badge_f if self.badge_f is not None else None)
        else:
            tabs.pack(side="left", padx=(18, 0), after=tl if show("title") else None)
        tk.Frame(self.root, bg=C["line"], height=1).pack(fill="x", pady=(10, 12))

    def _egg_tap(self, _e=None):
        now = time.time()
        self._egg_taps = [x for x in self._egg_taps if now - x < 3.0] + [now]
        if len(self._egg_taps) >= 7:
            self._egg_taps = []; self._marmot()

    def _marmot(self):
        """A little extra."""
        now = time.time()
        if getattr(self, "_egg_t0", 0) and now < self._egg_leave + 0.45:
            return
        if self.video is None or not self.video.winfo_exists():
            self._tab("live")                                          # only over the live picture
            if self.video is None:
                return
        self._egg_t0 = now; self._egg_leave = now + 3.2; self._egg_held = False; self._egg_qr = 0.0; self._egg_qr_from = 0.0; self._egg_pts = []
        self._egg_burst = None
        if getattr(self, "_egg_bound", None) is not self.video:
            self._egg_bound = self.video
            self.video.bind("<ButtonPress-1>", self._egg_press, add="+")
            self.video.bind("<B1-Motion>", self._egg_move, add="+")
            self.video.bind("<ButtonRelease-1>", self._egg_release, add="+")
        if out_selected():
            sound_play("marmot", 1.0, 45, reason="test")

    def _egg_xy(self, e):
        """Event position in the coordinates of the shown picture (the label centres it)."""
        iw, ih = getattr(self, "_egg_img", (0, 0))
        return e.x - (self.video.winfo_width() - iw) / 2, e.y - (self.video.winfo_height() - ih) / 2

    def _egg_press(self, e):
        b = getattr(self, "_egg_belly", None)
        if not b or time.time() > self._egg_leave:
            return
        x, y = self._egg_xy(e); cx, cy, rx, ry = b
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:          # grabbed at the belly
            self._egg_held = True; self._egg_pts = [(x, y)]

    def _egg_move(self, e):
        if getattr(self, "_egg_held", False):
            self._egg_pts.append(self._egg_xy(e)); self._egg_leave = max(self._egg_leave, time.time() + 0.5)

    def _egg_release(self, e):
        if not getattr(self, "_egg_held", False):
            return
        self._egg_held = False; now = time.time()
        if ccw_heart(self._egg_pts):                                   # 2.95.61: a big heart, counter-clockwise
            xs = [p[0] for p in self._egg_pts]; ys = [p[1] for p in self._egg_pts]
            self._egg_burst = (now, (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2)
            self._egg_qr_from = now + 3.7; self._egg_qr = now + 6.7; self._egg_leave = now + 6.9   # 2.95.88: 3 s target, then 3 s code
        else:
            self._egg_leave = max(self._egg_leave, now + 0.7)
        self._egg_pts = []

    def _egg_draw(self, im):
        """Draw the little extra into the PIL picture while it runs."""
        now = time.time(); t = now - getattr(self, "_egg_t0", 0)
        if getattr(self, "_egg_held", False):
            self._egg_leave = max(self._egg_leave, now + 0.5)
        if t < 0 or now > self._egg_leave + 0.4:
            self._egg_t0 = 0; self._egg_belly = None
            return im
        up = min(1.0, t / 0.35) if now < self._egg_leave else max(0.0, 1 - (now - self._egg_leave) / 0.4)
        up = 1 - (1 - up) ** 3
        from PIL import ImageDraw, ImageFont
        W, H = im.size; k = max(0.6, min(1.6, H / 330.0))
        bm = belly_matrix(); n = len(bm); mp = 1          # 2.95.62: one pixel per square - only readable with a magnifier
        S = (n + 8) * mp
        x0 = W / 2 - 60 * k; y0 = H - (78 * k + S + 3) * up
        d = ImageDraw.Draw(im)
        def ov(cx, cy, rx, ry, col):
            d.ellipse([x0 + (cx - rx) * k, y0 + (cy - ry) * k, x0 + (cx + rx) * k, y0 + (cy + ry) * k], fill=col)
        ov(60, 104, 40, 30, "#8a5a3b"); ov(60, 108, 23, 20, "#c99d6e")
        for ex in (35, 85):
            ov(ex, 31, 8, 8, "#6e4529"); ov(ex, 31, 4, 4, "#b98457")
        ov(60, 54, 30, 30, "#8a5a3b"); ov(60, 66, 17, 13, "#ecd3b2")
        for ex in (48, 72):
            ov(ex, 49, 4.6, 4.6, "#1b1410"); ov(ex + 1.5, 47.5, 1.5, 1.5, "#ffffff")
        ov(60, 60, 5.5, 3.8, "#2a1a12")
        for tx in (55.6, 60.4):
            d.rectangle([x0 + tx * k, y0 + 67.5 * k, x0 + (tx + 4) * k, y0 + 74.5 * k], fill="#ffffff")
        ov(40, 88, 9, 6.5, "#6e4529"); ov(80, 88, 9, 6.5, "#6e4529")
        bx0 = int(W / 2 - S / 2); by0 = min(int(y0 + 100 * k - S / 2), H - S - 2)
        self._egg_img = (W, H); self._egg_belly = (W / 2, y0 + 106 * k, max(30 * k, S * 0.6), max(26 * k, S * 0.55))
        if getattr(self, "_egg_burst", None) and now < getattr(self, "_egg_qr", 0):
            pass                                                       # burst and secret: no turning heart
        else:                                                          # 2.95.61: the turning heart where to touch
            sx = math.cos(t * 3.2); hcx, hcy = W / 2, y0 + 106 * k; hs = 15 * k
            if abs(sx) > 0.06:
                d.polygon(heart_points(hcx, hcy, hs, 40, abs(sx)), fill="#e8436a" if sx > 0 else "#b8284c")
        if getattr(self, "_egg_held", False) and len(self._egg_pts) > 1:   # the line while drawing
            ox, oy = 0, 0
            d.line([(p[0] + ox, p[1] + oy) for p in self._egg_pts], fill="#ff7aa2", width=max(2, int(3 * k)), joint="curve")
        bu = getattr(self, "_egg_burst", None)
        if bu and now - bu[0] < 0.75:                                  # the heart bursts into pieces
            q = (now - bu[0]) / 0.75; pts_ = heart_points(bu[1], bu[2], bu[3], 48)
            for i in range(12):
                a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12; am = (a0 + a1) / 2
                dx_, dy_ = math.cos(am) * bu[3] * 1.4 * q, math.sin(am) * bu[3] * 1.4 * q + 60 * k * q * q
                seg_ = [p for j, p in enumerate(pts_) if a0 <= (math.atan2(p[1] - bu[2], p[0] - bu[1]) % (2 * math.pi)) < a1]
                if not seg_:
                    continue
                poly = [(bu[1] + dx_, bu[2] + dy_)] + [(p[0] + dx_, p[1] + dy_) for p in seg_]
                if len(poly) >= 3:
                    d.polygon(poly, fill="#e8436a" if i % 2 else "#ff7aa2")
        if getattr(self, "_egg_burst", None) and getattr(self, "_egg_qr_from", 0) - 3.0 <= now < getattr(self, "_egg_qr_from", 0):
            tcx, tcy = bx0 + S / 2, by0 + S / 2                          # 2.95.88: a tiny target where the code comes
            for rr, col in ((4, "#ffffff"), (4, None), (2.4, None), (0.9, "#e8436a")):
                d.ellipse([tcx - rr, tcy - rr, tcx + rr, tcy + rr], fill=col, outline="#e8436a" if col is None else None)
        for r_, row in (enumerate(bm) if getattr(self, "_egg_qr_from", 0) <= now < getattr(self, "_egg_qr", 0) else ()):
            if r_ == 0:
                d.rectangle([bx0, by0, bx0 + S - 1, by0 + S - 1], fill="#c99d6e")
            for c_, v in enumerate(row):
                if v:
                    d.rectangle([bx0 + (c_ + 4) * mp, by0 + (r_ + 4) * mp, bx0 + (c_ + 5) * mp - 1, by0 + (r_ + 5) * mp - 1], fill="#6e4529")
        if up > 0.85:
            try:
                f = ImageFont.truetype("DejaVuSans-Bold.ttf", int(13 * k))
            except OSError:
                f = ImageFont.load_default()
            txt = tr("All quiet – I'm keeping watch!")
            bx = d.textbbox((0, 0), txt, font=f); tw, th = bx[2] - bx[0], bx[3] - bx[1]
            cx, by = W / 2, y0 - 16 * k
            d.rounded_rectangle([cx - tw / 2 - 12 * k, by - th - 14 * k, cx + tw / 2 + 12 * k, by], radius=int(10 * k), fill="#ffffff")
            d.polygon([(cx - 7 * k, by), (cx + 7 * k, by), (cx, by + 8 * k)], fill="#ffffff")
            d.text((cx - tw / 2, by - th - 7 * k - bx[1]), txt, font=f, fill="#1b2430")
        return im

    def _aug1(self, parent):
        """1 August: a small Swiss cross with twinkling sparks next to the name."""
        cv = tk.Canvas(parent, width=46, height=26, bg=C["bg"], highlightthickness=0, bd=0); cv.pack(side="left", padx=(8, 0))
        cv.create_rectangle(4, 4, 22, 22, fill="#e8112d", outline="")
        cv.create_rectangle(10.5, 7.5, 15.5, 18.5, fill="#ffffff", outline=""); cv.create_rectangle(7.5, 10.5, 18.5, 15.5, fill="#ffffff", outline="")
        Tip(cv, "🇨🇭 " + tr("Happy Swiss National Day!"))
        import random
        def twinkle():
            try:
                if not cv.winfo_exists():
                    return
                cv.delete("sp")
                for _ in range(3):
                    x, y = random.uniform(26, 44), random.uniform(3, 23)
                    cv.create_oval(x - 1.6, y - 1.6, x + 1.6, y + 1.6, fill=random.choice(("#ffd166", "#ffffff", "#ff6b6b")), outline="", tags="sp")
                self.root.after(450, twinkle)
            except tk.TclError:
                pass
        twinkle()

    def _paint_tabs(self):
        for tid, b in getattr(self, "tab_btns", {}).items():
            on = tid == self.tab
            b.config(bg=C["acc"] if on else C["panel"], fg="#ffffff" if on else C["txt"])

    def _tab(self, tid):
        """Switch the tab (2.98.14: the 6 tabs of the web page; another kind of tab = the window is built again)."""
        if tid == self.tab:
            return
        panel = tid in TK_PANEL_TABS or self.tab in TK_PANEL_TABS or self.left_f is None or not self.left_f.winfo_exists()
        self.tab = tid; CFG["ui_tab"] = tid
        if panel:
            self._schedule_rebuild(); return
        for w in self.left_f.winfo_children():
            w.destroy()
        self.video = self.p_rain = self.p_wind = self.l_rain = self.l_wind = self.l_boost = None
        self.l_cpu = self.p_cpu = self.cpu_canvas = self.l_cpu_info = self.log = None
        self.l_wifi = self.wifi_canvas = None
        self.l_pt = self.l_ctl_status = self.l_settings = None
        self.stick = None; self.qs_tiles = {}; self._last_ev = None
        self._build_left(self.left_f); self._paint_tabs(); self._refresh()

    def _build_left(self, left):
        show = self.is_shown
        self.left_f = left
        if self.tab not in [t for t, _ in self._tabs()]:
            self.tab = "live"
        left.columnconfigure(0, weight=1)
        for r_ in range(4):
            left.rowconfigure(r_, weight=0)
        if self.tab == "live":
            vc = tk.Frame(left, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=10, pady=10)
            vc.grid(row=0, column=0, sticky="nsew"); left.rowconfigure(0, weight=1)        # the picture gets all spare room
            vh = tk.Frame(vc, bg="#000", width=240, height=120); vh.pack(fill="both", expand=True); vh.pack_propagate(False)   # the picture never makes the window wider
            self.video = tk.Label(vh, bg="#000", bd=0, cursor="hand2"); self.video.pack(fill="both", expand=True)
            self.video.bind("<Double-Button-1>", lambda e: self.toggle_video_only())
            self.video.bind("<Button-3>", lambda e: self._view_menu(e.x_root, e.y_root))
            land = self._tk_live_land()                   # 2.98.26: wide window = the controls right of the picture (the picture keeps the height)
            self._ctl_side = land
            show_c = show("controls") and self._tkv_card("controls")      # 2.98.29: «Ansicht» of the window (581)
            show_s = self._tkv_card("lvsetup")
            folded = self._ctl_folded()
            wp = self._tkv_pic_weight()
            left.rowconfigure(0, weight=wp)
            colf = None
            if land and (show_c or show_s):
                colf = tk.Frame(left, bg=C["bg"]); colf.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
                left.columnconfigure(1, weight=0, minsize=self._tkv_side_w())
            if show_c:
                c = tk.Frame(colf if colf is not None else left, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=8)
                if colf is not None:
                    c.pack(fill="both", expand=not show_s)
                else:
                    c.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
                    if not folded and wp < 100:
                        left.rowconfigure(1, weight=100 - wp)     # smaller picture size: the controls get the room
                hd = tk.Frame(c, bg=C["panel"], cursor="hand2"); hd.pack(fill="x")
                h1 = tk.Label(hd, text=tr("CAMERA CONTROL"), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), cursor="hand2")
                h1.pack(side="left")
                h2 = tk.Label(hd, text="▸" if folded else "▾", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 10), cursor="hand2"); h2.pack(side="right")
                h3 = tk.Label(hd, text="◫", bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11), cursor="hand2", padx=6); h3.pack(side="right")
                h3.bind("<Button-1>", lambda e: self._tkv_dialog()); Tip(h3, tr("View: layout, picture size, buttons, cards"))
                for w_ in (hd, h1, h2):
                    w_.bind("<Button-1>", lambda e: self._fold_ctl())
                if not folded:
                    inner = tk.Frame(c, bg=C["panel"]); inner.pack(fill="x", pady=(6, 2))
                    self._build_controls(inner)
            if show_s:
                su = self._tkv_setup_card(colf if colf is not None else left)
                if colf is not None:
                    su.pack(fill="x", pady=(10 if show_c else 0, 0))
                else:
                    su.grid(row=3, column=0, sticky="ew", pady=(10, 0))
            if not show_c:                                # no controls card: the «Ansicht» stays reachable (right click or this button)
                vb = tk.Label(vc, text="◫", bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11), cursor="hand2")
                vb.place(relx=1.0, x=-4, y=4, anchor="ne"); vb.bind("<Button-1>", lambda e: self._tkv_dialog())
        elif self.tab == "more":                          # 2.98.14: «Mehr» = weather, system, self-check + manual, tools …
            self._tk_more_bar(left).grid(row=3, column=0, sticky="ew", pady=(10, 0))
            mid = tk.Frame(left, bg=C["bg"]); mid.grid(row=0, column=0, sticky="new")
            col = 0
            if show("weather"):
                wx = self._card(mid, tr("WEATHER")); wx.grid(row=0, column=col, sticky="nsew"); mid.columnconfigure(col, weight=1); col += 1
                g = tk.Frame(wx, bg=C["panel"]); g.pack(fill="x"); g.columnconfigure(1, weight=1)
                ttk.Label(g, text=tr("Rain score")).grid(row=0, column=0, sticky="w")
                self.p_rain = ttk.Progressbar(g, maximum=1.0); self.p_rain.grid(row=0, column=1, sticky="ew", padx=10)
                self.l_rain = ttk.Label(g, text="0.00", style="Mut.TLabel", width=6); self.l_rain.grid(row=0, column=2)
                ttk.Label(g, text=tr("Wind score")).grid(row=1, column=0, sticky="w", pady=(6, 0))
                self.p_wind = ttk.Progressbar(g, maximum=1.0, style="Wind.Horizontal.TProgressbar")
                self.p_wind.grid(row=1, column=1, sticky="ew", padx=10, pady=(6, 0))
                self.l_wind = ttk.Label(g, text="0.00", style="Mut.TLabel", width=6); self.l_wind.grid(row=1, column=2, pady=(6, 0))
                ttk.Label(g, text=tr("Trigger multiplier (wind)")).grid(row=2, column=0, sticky="w", pady=(6, 0))
                self.l_boost = ttk.Label(g, text="x1.0", style="Mut.TLabel"); self.l_boost.grid(row=2, column=1, sticky="w", padx=10, pady=(6, 0))
            if show("cpu"):
                sysf = self._card(mid, tr("SYSTEM · CPU")); sysf.grid(row=0, column=col, sticky="nsew", padx=(10 if col else 0, 0))
                mid.columnconfigure(col, weight=1)
                self.l_cpu = ttk.Label(sysf, text="–", style="Stat.TLabel"); self.l_cpu.pack(anchor="w")
                self.p_cpu = ttk.Progressbar(sysf, maximum=100, style="CpuG.Horizontal.TProgressbar"); self.p_cpu.pack(fill="x", pady=(2, 4))
                self.cpu_canvas = tk.Canvas(sysf, height=60, bg=C["field"], bd=0, highlightthickness=0); self.cpu_canvas.pack(fill="x")
                self.l_cpu_info = ttk.Label(sysf, text="", style="Mut.TLabel"); self.l_cpu_info.pack(anchor="w", pady=(4, 0))
                self.l_wifi = ttk.Label(sysf, text="", style="Mut.TLabel", wraplength=420, justify="left"); self.l_wifi.pack(anchor="w", pady=(6, 0))
                self.wifi_canvas = tk.Canvas(sysf, height=60, bg=C["field"], bd=0, highlightthickness=0); self.wifi_canvas.pack(fill="x", pady=(2, 0))
            hf = self._card(left, tr("SELF-CHECK")); hf.grid(row=1, column=0, sticky="nsew", pady=(10, 0)); left.rowconfigure(1, weight=1)
            self.h_text = tk.Text(hf, bg=C["panel"], fg=C["txt"], bd=0, highlightthickness=0, height=12, font=("DejaVu Sans", 10),
                                  state="disabled", wrap="word", takefocus=0, spacing1=2, spacing3=1, cursor="arrow")
            hsb = ttk.Scrollbar(hf, orient="vertical", command=self.h_text.yview); self.h_text.configure(yscrollcommand=hsb.set)
            hsb.pack(side="right", fill="y"); self.h_text.pack(side="left", fill="both", expand=True)
            for lv, colr in (("ok", C["grn"]), ("warn", C["yel"]), ("bad", C["red"]), ("off", C["mut"])):
                self.h_text.tag_configure(lv, foreground=colr, font=("DejaVu Sans", 12))
            self.h_text.tag_configure("t", font=("DejaVu Sans", 10, "bold")); self.h_text.tag_configure("m", foreground=C["mut"])
            self.h_text.tag_configure("tip", foreground=C["txt"], lmargin1=26, lmargin2=26, font=("DejaVu Sans", 9))
            self._h_sig = None; self._update_health()
        else:                                             # 2.98.14: «Verlauf» = the event log + recordings, diary, messages
            self._tk_history_bar(left).grid(row=1, column=0, sticky="ew", pady=(10, 0))
            logf = self._card(left, tr("EVENT LOG") + " · " + tr("important")); logf.grid(row=0, column=0, sticky="nsew")
            left.rowconfigure(0, weight=1)
            self.log = tk.Text(logf, bg=C["panel"], fg=C["txt"], bd=0, highlightthickness=0, height=10,
                               font=("DejaVu Sans Mono", 10), state="disabled", wrap="word", takefocus=0, spacing1=2, spacing3=2)
            sb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview); self.log.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y"); self.log.pack(side="left", fill="both", expand=True)
            for k, colr in kind_colors().items():
                self.log.tag_configure(k, foreground=colr)
            self.log.tag_configure("t", foreground=C["mut"])
        if show("settings_line"):
            self.l_settings = ttk.Label(left, text="", style="Sub.TLabel"); self.l_settings.grid(row=2, column=0, sticky="w", pady=(6, 0))

    # ---- camera control bar (like the web page: stick | small things | quick switches) ----
    SPEEDS = (("Slow", 12.0), ("Medium", 30.0), ("Fast", 60.0))

    def _build_controls(self, f):
        side_col = getattr(self, "_ctl_side", False)     # 2.98.26: in the column right of the picture = the narrow arrangement
        wide = self._lay[2] and not side_col             # wide: stick | small things | quick switches in one row
        left_w = self._win_w() - self._lay[1] - 60
        tiny = side_col or (not wide and left_w < 520)   # very narrow: small things beside the stick, switches below both
        head = self._tk_head()                           # 2.98.26: joystick, centre, calibrate, waypoints only with a pan / tilt head (2.98.29: «Ansicht» → Joystick always / never)
        u = self._tk_ui()
        bar = tk.Frame(f, bg=C["panel"]); bar.pack(fill="x")
        # 1) joystick with the camera position (orange ring) and the waypoints
        swap = "ctl:swap" in self.open_secs                # ⇆ left- / right-handed: stick and small buttons change places
        c_st, c_sd = (1, 0) if swap else (0, 1)
        sb = tk.Frame(bar, bg=C["panel"])
        if head or MOVER["avail"]:
            sb.grid(row=0, column=c_st, rowspan=1 if (wide or tiny) else 2, sticky="n")
        if head:
            self.stick = StickPad(sb, self, int((176 if wide else 140) * u)); self.stick.pack()
            self.l_pt = tk.Label(sb, text="", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8)); self.l_pt.pack(pady=(2, 0))
        # the mover (2.94.0): second stick under the camera stick, only while the mover is there
        self.mstick = MoverPad(sb, self, 140 if wide else 116)
        if MOVER["avail"]:
            self.mstick.pack(pady=(8, 0))
        # 2) speed, centre, calibrate, waypoints (narrow window: one row of symbols)
        names = [tr(n) for n, _ in self.SPEEDS]
        if wide:
            side = tk.Frame(bar, bg=C["panel"]); side.grid(row=0, column=c_sd, sticky="n", padx=(0 if swap else 22, 22), pady=(14, 0))
        else:
            side = tk.Frame(bar, bg=C["panel"]); side.grid(row=0, column=c_sd, sticky="ew", padx=(0, 14) if swap else (14, 0))
        cb = ttk.Combobox(side, values=names, state="readonly", width=12 if wide else 9, font=("DejaVu Sans", 10))
        Tip(cb, tr("Speed"))
        cb.current(next((i for i, (_, v) in enumerate(self.SPEEDS) if v == self.stick_speed), 1))
        cb.bind("<<ComboboxSelected>>", lambda e: (setattr(self, "stick_speed", self.SPEEDS[cb.current()][1]), self.root.focus_set()))
        btns = (("◎ " + tr("Centre"), "◎", lambda: self._move("center"), tr("Camera to the middle")),
                ("↻ " + tr("Calibrate"), "↻", self._recal, tr("Learn the picture again (after moving the camera)")),
                ("⚑ + " + tr("Waypoint"), "⚑+", self._add_wp, tr("Save the current position as waypoint for the patrol")),
                ("⚑ ✕", "⚑✕", self._clear_wp_ask, tr("Clear waypoints")),
                ("⏹ " + tr("Stop"), "⏹", self._srv_estop_btn, tr("Emergency stop") + " / " + tr("Release")),          # 2.98.35 (588)
                ("📍 " + tr("Positions"), "📍", lambda: self._srv_win("teach"), tr("Servos: safety, positions, test, diagnosis")))
        swb = lambda par: self._fbtn(par, "⇆", self._swap_side, tr("Swap stick and buttons (left- / right-handed)"), font=("DejaVu Sans", 11, "bold"))
        if wide:
            r0 = tk.Frame(side, bg=C["panel"]); r0.pack(fill="x")
            cb.pack(in_=r0, side="left", fill="x", expand=True); cb.lift(r0); swb(r0).pack(side="left", padx=(6, 0))
            r1 = tk.Frame(side, bg=C["panel"]); r1.pack(fill="x", pady=(6, 0))
            self._fbtn(r1, btns[0][0], btns[0][2], btns[0][3]).pack(side="left", fill="x", expand=True)
            self._fbtn(r1, btns[1][0], btns[1][2], btns[1][3]).pack(side="left", fill="x", expand=True, padx=(6, 0))
            r2 = tk.Frame(side, bg=C["panel"]); r2.pack(fill="x", pady=(6, 0))
            self._fbtn(r2, btns[2][0], btns[2][2], btns[2][3]).pack(side="left", fill="x", expand=True)
            self._fbtn(r2, btns[3][0], btns[3][2], btns[3][3]).pack(side="left", padx=(6, 0))
            r3 = tk.Frame(side, bg=C["panel"]); r3.pack(fill="x", pady=(6, 0))     # 2.98.35: Not-Aus + positions (588)
            self._srv_btn = self._fbtn(r3, btns[4][0], btns[4][2], btns[4][3]); self._srv_btn.pack(side="left", fill="x", expand=True)
            self._srv_btn.config(bg="#d1242f", fg="#ffffff"); self._srv_btn.bind("<Leave>", lambda e: self._srv_btn.config(bg="#d1242f"))
            self._fbtn(r3, btns[5][0], btns[5][2], btns[5][3]).pack(side="left", fill="x", expand=True, padx=(6, 0))
        elif tiny:
            side.grid_configure(sticky="n", pady=(10, 0))
            cb.config(width=12); cb.pack(fill="x")
            g2 = tk.Frame(side, bg=C["panel"]); g2.pack(fill="x", pady=(6, 0))
            swb(side).pack(fill="x")
            for n_, (_, short, cmd, tip) in enumerate(btns):
                self._fbtn(g2, short, cmd, tip).grid(row=n_ // 2, column=n_ % 2, sticky="ew", padx=(0, 6), pady=(0, 6))
                g2.columnconfigure(n_ % 2, weight=1)
        else:
            cb.pack(side="left")
            for _, short, cmd, tip in btns:
                self._fbtn(side, short, cmd, tip).pack(side="left", padx=(6, 0))
            swb(side).pack(side="left", padx=(6, 0))
        if not head:
            side.grid_remove()
            tk.Label(bar, text=tr("no pan / tilt head - joystick hidden (Settings → Camera / Servos → Servo driver)"), bg=C["panel"], fg=C["mut"],
                     font=("DejaVu Sans", 8), wraplength=360, justify="left").grid(row=3, column=0, columnspan=4, sticky="w")
        self.l_ctl_status = tk.Label(side if wide else bar, text="", bg=C["panel"], fg=C["yel"], font=("DejaVu Sans", 8), wraplength=200 if wide else 400,
                                     justify="left")
        if wide:
            self.l_ctl_status.pack(anchor="w", pady=(6, 0))
        else:
            self.l_ctl_status.grid(row=2, column=0, columnspan=4, sticky="w")
        # 3) quick switches, the waypoints below
        qf = tk.Frame(bar, bg=C["panel"])
        if wide:
            qf.grid(row=0, column=3, sticky="new", pady=(10, 0)); bar.columnconfigure(3, weight=1); cols = 5
        elif tiny:
            qf.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)); bar.columnconfigure(c_sd, weight=1); cols = 5
        else:
            qf.grid(row=1, column=c_sd, sticky="new", padx=(0, 14) if swap else (14, 0), pady=(8, 0)); bar.columnconfigure(c_sd, weight=1)
            cols = 5 if left_w - 170 >= 380 else 4
        grid = tk.Frame(qf, bg=C["panel"]); grid.pack(fill="x")
        for k in range(cols):
            grid.columnconfigure(k, weight=1, uniform="qs")
        self.qs_tiles = {}
        th = int((58 if wide else 50) * u)
        qs = self._tkv_tiles(head)                       # 2.98.29: favourites + «… mehr» (581); the old «Anpassen» is the «Ansicht» now
        for n, q in enumerate(qs):
            t = tk.Frame(grid, bg=self._btn2(), highlightthickness=1, highlightbackground=C["line"], width=50, height=th, cursor="hand2")
            t.grid(row=n // cols, column=n % cols, padx=(0, 6), pady=(0, 6), sticky="ew"); t.pack_propagate(False)
            ic = tk.Label(t, text=q["ic"], bg=t["bg"], fg=C["txt"], font=("DejaVu Sans", 15 if wide else 13)); ic.pack(pady=(6 if wide else 3, 0))
            lb = tk.Label(t, text=q["lb"], bg=t["bg"], fg=C["mut"], font=("DejaVu Sans", 8, "bold")); lb.pack()
            for w in (t, ic, lb):
                w.bind("<Button-1>", lambda e, qq=q: self._qs_click(qq))
            Tip(t, q["tip"])
            self.qs_tiles[q["id"]] = (t, ic, lb, q)
        self.l_wp = tk.Label(qf, text="", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8), anchor="w", justify="left", wraplength=470 if wide else 380)
        self.l_wp.pack(anchor="w", pady=(2, 0))
        self._qs_paint()

    def _swap_side(self):
        (self.open_secs.discard if "ctl:swap" in self.open_secs else self.open_secs.add)("ctl:swap")
        CFG["ui_open"] = sorted(self.open_secs); save_settings()
        tid, self.tab = self.tab, None
        self._tab(tid)

    def _ctl_folded(self):
        """Folded by the user - or by default on a low screen (picture first), until unfolded."""
        h = self.root.winfo_height()
        h = h if h > 50 else self.root.winfo_screenheight()
        return "ctl:folded" in self.open_secs or (h < 640 and "ctl:open" not in self.open_secs and not self._tk_live_land())

    def _fold_ctl(self):
        fold = not self._ctl_folded()
        self.open_secs.discard("ctl:folded"); self.open_secs.discard("ctl:open")
        self.open_secs.add("ctl:folded" if fold else "ctl:open")
        CFG["ui_open"] = sorted(self.open_secs); save_settings()
        tid, self.tab = self.tab, None
        self._tab(tid)

    def _qs_list(self):
        """The same quick switches as on the web page (listening is only on the phone / browser)."""
        st = STATE; L = st.get("lights") or {}
        q = [
            dict(id="therm", ic="♨", lb=tr("Thermal"), tip=tr("Thermal picture over the live picture"), on=lambda: CFG["thermal_on"],
                 ok=lambda: bool(CFG["thermal_source"]), go=lambda: self._set("thermal_on", not CFG["thermal_on"])),
            dict(id="nv", ic="☾", lb=tr("Night vision"), tip=tr("Night vision: green picture, thermal outlines and temperatures"),
                 on=lambda: bool(STATE.get("nightvision")), go=lambda: self._set("nightvision", not CFG["nightvision"])),
            dict(id="marks", ic="▣", lb=tr("Marks"), tip=tr("Mark detected objects (animals, cars ...)"), on=lambda: CFG["show_objects"],
                 go=lambda: self._set("show_objects", not CFG["show_objects"])),
            dict(id="mask", ic="▒", lb=tr("Mask"), tip=tr("Motion mask over the picture: red = what the detection sees as movement"),
                 on=lambda: CFG["show_mask"], ok=lambda: CFG.get("detection_on", True), go=lambda: self._set("show_mask", not CFG["show_mask"])),
            dict(id="white", ic="☀", lb=tr("Lamp"), tip=tr("White light on / off"), on=lambda: bool((STATE.get("lights") or {}).get("white")),
                 ok=lambda: bool(CFG["light_white_out"]) or CFG["sim_on"], go=lambda: light_set("white", "off" if (STATE.get("lights") or {}).get("white") else "on")),
            dict(id="ir", ic="◉", lb=tr("IR light"), tip=tr("Infrared light on / off"), on=lambda: bool((STATE.get("lights") or {}).get("ir")),
                 ok=lambda: bool(CFG["light_ir_out"]) or CFG["sim_on"], go=lambda: light_set("ir", "off" if (STATE.get("lights") or {}).get("ir") else "on")),
            dict(id="sim", ic="⚗", lb=tr("Simulation"), tip=tr("Simulation on / off: cameras, thermal camera and sensors from the simulation program") + " (F9)",
                 on=lambda: sim_live(), go=lambda: self._sim_toggle("window")),
            dict(id="track", ic="◎", lb=tr("Follow"), tip=tr("Keep what is detected in the middle: persons, animals, moving things"),
                 on=lambda: CFG["track_person"] or CFG["track_motion"],
                 go=lambda: follow_set(not (CFG["track_person"] or CFG["track_motion"]), "window")),
            dict(id="patrol", ic="⇄", lb=tr("Patrol"), tip=tr("Patrol: tap = off → back and forth (1-2-3-2-1) → round trip (1-2-3-1) → off"),
                 on=lambda: CFG["patrol"], go=lambda: quick_patrol("window")),
            dict(id="rec", ic="●", lb=tr("Record"), tip=tr("Record now (max. 10 min) / stop"), on=lambda: time.time() < QUICK["rec_until"],
                 go=quick_rec, red=True),
            dict(id="photo", ic="⊡", lb=tr("Photo"), tip=tr("Photo into the recordings"), on=lambda: False,
                 go=lambda: quick_photo(self.watch.frame_out), flash=True),
            dict(id="games", ic="♣", lb=tr("Games"), tip=tr("All games for the phones: game corner, game collection and the simulator game - one QR code"),
                 on=party_on, go=self._games_toggle)]                # 2.98.7
        for i, r in enumerate(RELAYS):
            q.append(dict(id=f"rel{i}", ic="⚡", lb=r["name"][:12], tip=tr("Relay: on / automatic"),
                          on=lambda i=i: bool(i < len(STATE.get("relay_states", [])) and STATE["relay_states"][i]),
                          go=lambda i=i: self._relay_quick(i)))
        del st, L
        return q

    def _games_toggle(self):
        """2.98.7: «Spiele freigeben» in the window - opens all games and shows the address of the game corner"""
        if party_on():
            if messagebox.askyesno("MoveEye", tr("Close all games? The players are logged out.")):
                games_all_close("window")
            return
        games_all_open(6.0, "window")
        url = page_address().rstrip("/") + "/p/" + PARTY["key"] + "/"
        messagebox.showinfo("MoveEye", tr("All games are open for 6 hours. The players open this address with the phone (same Wi-Fi):") + "\n\n" + url)

    def _qs_click(self, q):
        if q.get("ok") and not q["ok"]():
            return
        try:
            q["go"]()
        except Exception as e:                                        # a switch must never break the window
            log_event("sys", f"Quick switch {q['id']}: {e}")
        if q.get("flash"):
            t = self.qs_tiles[q["id"]][0]
            for w in self.qs_tiles[q["id"]][:3]:
                w.config(bg=C["acc"])
            self.root.after(350, self._qs_paint)
        self._qs_paint()

    def _relay_quick(self, i):
        """On <-> back to the mode from before (mostly automatic) - like the web page."""
        r = RELAYS[i]
        if r["mode"] == "on":
            v = self.relay_prev.get(i) if self.relay_prev.get(i) not in (None, "on") else "auto"
        else:
            self.relay_prev[i] = r["mode"]; v = "on"
        self._relay_set(i, "mode", v)

    def _qs_paint(self):
        tiles = getattr(self, "qs_tiles", None) or {}
        if not tiles:
            return
        try:
            if not next(iter(tiles.values()))[0].winfo_exists():
                return
        except tk.TclError:
            return
        for qid, (t, ic, lb, q) in tiles.items():
            ok = q["ok"]() if q.get("ok") else True
            on = bool(q["on"]()) and ok
            if on:
                col = C["red"] if q.get("red") else C["grn"]
                bg, bd, fg, ifg = self._mix(C["panel"], col, 0.16), col, col, C["txt"]
            else:
                bg, bd, fg, ifg = self._btn2(), C["line"], C["mut"] if ok else self._mix(C["panel"], C["mut"], 0.45), C["txt"] if ok else self._mix(C["panel"], C["mut"], 0.45)
            if qid == "patrol":
                lb_t = tr("Patrol") if not CFG["patrol"] else (tr("Round") if CFG["patrol_mode"] == "loop" else tr("Pendulum"))
                ic.config(text="⟳" if CFG["patrol"] and CFG["patrol_mode"] == "loop" else "⇄"); lb.config(text=lb_t)
            t.config(bg=bg, highlightbackground=bd, cursor="hand2" if ok else "arrow")
            ic.config(bg=bg, fg=ifg); lb.config(bg=bg, fg=fg)
        if getattr(self, "l_wp", None) is not None and self.l_wp.winfo_exists():
            txt = ""
            if CFG["patrol"]:
                txt = f"{tr('Patrol')}: {patrol_status_text(STATE['patrol_status'])}"
            if WAYPOINTS:
                txt += (" · " if txt else "") + f"{tr('waypoints')} (↔/↕): {wp_text()}"
            self.l_wp.config(text=txt)

    def _recal(self):
        self.watch.tuner.reset(); log_event("auto", "Recalibration started (window)")

    def _clear_wp_ask(self):
        if WAYPOINTS and messagebox.askyesno("MoveEye", tr("Clear all waypoints?")):
            self._clear_wp()

    def _trigger_box(self, parent, i, rl, labels):
        cb = ttk.Combobox(parent, values=labels, width=11, state="readonly")
        cb.current(TRIGGERS.index(rl["trigger"]) if rl["trigger"] in TRIGGERS else 0)
        cb.bind("<<ComboboxSelected>>", lambda e, i=i, c=cb: (self.root.focus_set(), self._relay_set(i, "trigger", TRIGGERS[c.current()])))
        return cb

    # ---- settings sidebar (collapsible: ▶ strip button, header button or Ctrl+B) ----
    def _ai_dl(self):
        ok, err = ai_model_download()
        if not ok:
            self._status("AI model", "⚠ " + tr_err(err)); return
        def poll():
            if AI_MODEL["busy"]:
                self._status("AI model", tr("downloading the AI model …") + f" {AI_MODEL['pct']} %"); self.root.after(1000, poll)
            else:
                self._status("AI model", ("✓ " + tr("AI ready")) if AI_MODEL["msg"] == "ready" else "⚠ " + AI_MODEL["msg"])
                if AI_MODEL["msg"] == "ready":
                    self.root.after(1500, self._rebuild)
        poll()

    def _own_ai_dl(self):
        ok, err = own_ai_download(only_better=bool(own_ai_paths()[0]))     # part 196: only a new model that is not worse
        if not ok:
            self._status("Own AI model", "⚠ " + tr_err(err)); return
        def poll():
            if OWN_AI["busy"]:
                self._status("Own AI model", tr("downloading the own model …") + f" {OWN_AI['pct']} %"); self.root.after(1000, poll)
            else:
                self._status("Own AI model", ("✓ " + tr("own model ready") + "\n" + own_ai_long_text()) if OWN_AI["msg"] == "ready" else "⚠ " + OWN_AI["msg"])
        poll()

    def _set_simple(self, v):
        """586: Simple / Expert of THIS tab (the default stays - it is chosen in the guide)"""
        tab = self.tab
        if page_simple(tab) != v:
            m_ = page_modes(); m_[tab] = "simple" if v else "expert"
            if v == bool(CFG["ui_simple"]):
                m_.pop(tab)
            web_ui_update({"mw-page-mode": json.dumps(m_)}); self.root.after(30, self._rebuild)

    def _protect(self, level):
        """2.95.105: protection level; switching off needs the PIN if one is set"""
        if level == "off" and CFG.get("protect_pin"):
            from tkinter import simpledialog
            pin = simpledialog.askstring("MoveEye", tr("PIN for switching off"), show="*", parent=self.root)
            if pin is None:
                return
            ok_, err_ = protect_disarm(pin, "window")
        else:
            ok_, err_ = protect_set(level, "window")
        self._status("Protection", ("✓ " if ok_ else "⚠ ") + (tr(err_) if err_ else tr({"off": "Off", "watch": "Watchful", "full": "Full protection"}[level])))

    def _night(self):
        r = night_guard()
        txt = "\n".join("✓ " + x for x in r["done"])
        if r["missing"]:
            txt += "\n\n" + tr("Still missing:") + "\n" + "\n".join("⚠ " + x["title"] + ": " + x["text"] + (("\n   → " + x["tip"]) if x["tip"] else "") for x in r["missing"])
        else:
            txt += "\n\n" + tr("Everything ready - good night!")
        messagebox.showinfo(tr("Guard tonight"), txt, parent=self.root)

    def _build_sidebar(self, body, tab="settings"):
        """2.98.14: the tabs Schutz / Einstellungen / Simulator - their groups over the whole width (before: a panel beside the picture)"""
        right = tk.Frame(body, bg=C["bg"]); right.grid(row=0, column=0, sticky="nsew")
        self.right_f = right
        canvas = tk.Canvas(right, bg=C["bg"], bd=0, highlightthickness=0); self.side_canvas = canvas
        sb = ttk.Scrollbar(right, orient="vertical", command=canvas.yview); canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas, style="Bg.TFrame"); win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=min(e.width, 860)))     # readable lines on a wide screen
        bar = tk.Frame(right, bg=C["bg"]); bar.pack(side="top", fill="x", pady=(0, 10), before=sb)   # stays at the top while scrolling
        # like the web page: search field, then two symbols - ⊞ expand all, ⊟ collapse all
        self._ibtn(bar, "⊟", lambda: self._all_sections(False), tr("Collapse all")).pack(side="right")
        self._ibtn(bar, "⊞", lambda: self._all_sections(True), tr("Expand all")).pack(side="right", padx=(0, 6))
        self._ibtn(bar, "☰", self._groups_only, tr("Groups only")).pack(side="right", padx=(0, 6))
        sf = tk.Frame(bar, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"]); sf.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(sf, text="⚲", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11)).pack(side="left", padx=(8, 0))
        self.search_var = tk.StringVar()
        se = tk.Entry(sf, textvariable=self.search_var, bg=C["panel"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=0, font=("DejaVu Sans", 10))
        se.pack(side="left", fill="x", expand=True, padx=(6, 8), pady=6)
        ph = tk.Label(sf, text=tr("Search settings …"), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 10), cursor="xterm")
        ph.place(in_=se, x=1, rely=0.5, anchor="w"); ph.bind("<Button-1>", lambda e: se.focus_set())
        self.search_ph = ph
        self.search_var.trace_add("write", lambda *a: self._search())
        if tab == "sim":                                   # 2.98.14: tab Simulator - status, the assistant, the simulator settings
            self._tk_sim_head(inner)
        # Simple / Expert (like the web page)
        mrow = tk.Frame(inner, bg=C["line"], padx=1, pady=1)
        if tab != "sim":
            mrow.pack(fill="x", pady=(0, 10))
        self._simple_seen = bool(CFG["ui_simple"])
        _G2_SIMPLE.v = page_simple(tab)                    # 586: Simple / Expert of this tab (simple_hidden in the window thread)
        for i, (val, lab) in enumerate(((True, tr("Simple")), (False, tr("Expert")))):
            on = page_simple(tab) == val
            l = tk.Label(mrow, text=lab, font=("DejaVu Sans", 9, "bold"), pady=4, cursor="hand2",
                         bg=C["acc"] if on else C["field"], fg="#ffffff" if on else C["mut"])
            l.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 1, 0))
            l.bind("<Button-1>", lambda e, v=val: self._set_simple(v))
        if page_simple(tab) and tab != "sim":
            tk.Label(inner, text=tr("Simple: only the important settings. «Expert» shows all of them."), bg=C["bg"], fg=C["mut"],
                     font=("DejaVu Sans", 8), anchor="w", justify="left", wraplength=330).pack(fill="x", pady=(0, 8))
        self.grp_meta = {}; self._open_before = None
        self.no_match = tk.Label(inner, text=tr("No match"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9))
        # 9 groups (same as the web page). Inside a group every topic opens / closes the same way (the first one is open);
        # fine-tuning comes last under a small line. A group with one topic shows it directly.
        self.group_titles = {}; self.subs = {}; self.sub_parts = {}; self.grp_icons = {}
        self._lock_seen = bool(CFG["lock_on"])
        if CFG["lock_on"]:                               # operator mode: all may be changed, unlocking puts it back
            card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
            tk.Label(card, text="🔐 " + tr("Operator mode"), bg=C["panel"], fg=C["yel"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
            ttk.Label(card, text=tr("Everything may be changed (except Wi-Fi, password, autostart). Unlocking with the PIN puts everything back."),
                      style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(2, 6))
            ttk.Button(card, text=tr("Unlock") + " …", command=self._unlock).pack(fill="x")
        listed = {x for g in TK_GROUPS + TK_SIM_GROUPS for x in g[2] if x}
        groups = [list(g) for g in TK_GROUPS]
        groups[-1][2] = groups[-1][2] + [x for x in SECTIONS if x not in listed]     # sections added later -> System
        groups = [g for g in groups if TK_GROUP_TAB.get(g[0], "settings") == tab] if tab != "sim" else [list(g) for g in TK_SIM_GROUPS]
        for gid, name, items in groups:
            items = [x for x in items if x is None or x in TK_PSEUDO or (x in SECTIONS and self.is_shown("sec:" + x) and (tab == "sim" or not simple_hidden(None, x)))]
            real = [x for x in items if x]
            if not real:
                continue
            key = "grp:" + gid
            # 2.98.14: no headings «Schutz» / «Einstellungen» any more - the tab is the heading
            card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
            hr = tk.Frame(card, bg=C["panel"], cursor="hand2"); hr.pack(fill="x")
            gic = tk.Label(hr, text=TK_GROUP_ICONS.get(gid, ""), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11), width=2, anchor="w", cursor="hand2")
            gic.pack(side="left"); self.grp_icons["grp:" + gid] = gic
            gic.bind("<Button-1>", lambda e, k="grp:" + gid: self._toggle_section(k))
            head = tk.Label(hr, text="", bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9, "bold"), anchor="w", cursor="hand2")
            head.pack(side="left", fill="x", expand=True)
            arr = tk.Label(hr, text="▸", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 10), cursor="hand2"); arr.pack(side="right")
            gbody = tk.Frame(card, bg=C["panel"])
            self.sections[key] = (head, gbody); self.group_titles[key] = tr(name)
            for w_ in (hr, head, arr):
                w_.bind("<Button-1>", lambda e, k=key: self._toggle_section(k))
            words = [tr(name)] + [tr(x) for x in real]
            for lst in (TOGGLES, SLIDERS, TEXTS):
                words += [tr(t_[2]) + " " + tr(MENU_LONG.get(t_[1], "")) for t_ in lst if t_[0] in real]   # 639c: + the long text («?»)
            self.grp_meta[key] = (arr, real, card, " ".join(words).lower())
            if len(real) == 1:
                sb = tk.Frame(gbody, bg=C["panel"]); sb.pack(fill="x", pady=(4, 0))
                self._build_section(real[0], sb)
                continue
            first = True
            for i, sec in enumerate(items):
                if sec is None:
                    if any(items[i + 1:]):
                        tk.Frame(gbody, bg=C["line"], height=1).pack(fill="x", pady=(12, 4))
                        tk.Label(gbody, text=tr("Fine-tuning").upper(), bg=C["panel"], fg=C["acc"], font=("DejaVu Sans", 7, "bold"),
                                 anchor="w").pack(fill="x")
                    continue
                self._sub(gbody, sec, default_open=first); first = False
        for sec in self.sections:
            self._set_section(sec, sec in self.open_secs or (tab == "sim" and sec == "grp:simset"), save=False)

    def _sub(self, parent, sec, default_open=False):
        """One topic of a group: thin line + title that opens / closes it (state kept in the settings)."""
        tk.Frame(parent, bg=C["line"], height=1).pack(fill="x", pady=(8, 4))
        title = MENU_TITLES.get(sec, sec)                  # 639c: the same part names as the web page
        # 2.95.71: like every menu - symbol left, name, arrow right; symbol and arrow green while the function is on
        h = tk.Frame(parent, bg=C["panel"], cursor="hand2"); h.pack(fill="x")
        ic = TK_SUB_ICONS.get(sec, "")
        il = tk.Label(h, text=ic, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 10), width=2, anchor="w", cursor="hand2"); il.pack(side="left")
        tl = tk.Label(h, text=tr(title).upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), anchor="w", cursor="hand2")
        tl.pack(side="left", fill="x", expand=True)
        al = tk.Label(h, text="▸", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), cursor="hand2"); al.pack(side="right")
        body = tk.Frame(parent, bg=C["panel"])
        k = "sub:" + sec
        self.subs[k] = (h, body, tr(title).upper())
        self.sub_parts[k] = (il, tl, al, sec)
        for w_ in (h, il, tl, al):
            w_.bind("<Button-1>", lambda e, kk=k: self._set_sub(kk, not self._sub_open(kk)))
        self._build_section(sec, body)
        if k not in self.open_secs and ("subx:" + sec) not in self.open_secs and default_open:
            self.open_secs.add(k)
        self._set_sub(k, k in self.open_secs, save=False)

    def _sub_arrow(self, k, open_):
        p_ = self.sub_parts.get(k)
        if p_ is not None:
            p_[2].config(text="▾" if open_ else "▸"); p_[1].config(fg=C["txt"] if open_ else C["mut"])

    def _paint_main(self):
        """2.95.71: symbol and arrow green while the main function of a topic is on (group: one of its topics) - like the web page"""
        meta = getattr(self, "grp_meta", {})
        for k, (il, tl, al, sec) in getattr(self, "sub_parts", {}).items():
            on = tk_main_on(sec)
            col = C["grn"] if on else C["mut"]
            if il.cget("fg") != col:
                il.config(fg=col); al.config(fg=col)
        for key, m in meta.items():
            on = any(tk_main_on(x) for x in m[1])
            col = C["grn"] if on else C["mut"]
            if m[0].cget("fg") != col:
                m[0].config(fg=col)
            ic_ = getattr(self, "grp_icons", {}).get(key)
            if ic_ is not None and ic_.cget("fg") != (C["grn"] if on else C["txt"]):
                ic_.config(fg=C["grn"] if on else C["txt"])

    def _sub_open(self, k):
        return k in self.open_secs

    def _set_sub(self, k, open_, save=True):
        h, body, title = self.subs[k]
        closed = "subx:" + k[4:]
        if open_:
            self.open_secs.add(k); self.open_secs.discard(closed)
        else:
            self.open_secs.discard(k); self.open_secs.add(closed)
        if save and sorted(self.open_secs) != sorted(CFG["ui_open"]):
            CFG["ui_open"] = sorted(self.open_secs); save_settings()
        self._sub_arrow(k, open_)
        if open_ and save:                                   # 2.98.9: guide - the topic is explained the first time
            tip_ = guide_tip_for("sec:" + k[4:])
            if tip_:
                guide_mark_seen("sec:" + k[4:])
                self.root.after(200, lambda t_=tip_: messagebox.showinfo("💡 " + t_[0], t_[1], parent=self.root))
        if open_:
            body.pack(fill="x", pady=(2, 0), after=h)
        else:
            body.pack_forget()

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
        if sec == "Improve detection":                     # 2.98.14: the assistant (312) - one guided flow
            ttk.Label(sbody, text=tr("One guided flow: check, measure, improve, see the result. Replaces the single tools (they stay in «Expert»)."), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w")
            ttk.Button(sbody, text="🎯 " + tr("Improve detection") + " …", command=self._tune_win).pack(fill="x", pady=(6, 0))
            return
        if sec in ("Setup", "Camera / Servos", "Video source", "Schedule", "Patrol", "AI detection", "Web stream", "Auto-tune", "Notifications", "Timelapse", "Thermal camera", "Wi-Fi / hotspot", "Camping / protection", "Microphone", "Loudspeaker", "Lights", "Servo driver", "Clap switch", "Bless you"):
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w")
        if sec == "Web stream":
            ttk.Button(sbody, text=tr("Tools: network, Wi-Fi, tests (browser)"), command=lambda: self._open_page("/tools")).pack(fill="x", pady=(4, 0))
        if sec == "Wake-up alarm":                     # 2.98.7: the wake-up alarm with the sleeping place
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w")
            def _wk(a):
                ok_, err_ = wake_action(a, "window")
                if not ok_:
                    messagebox.showinfo("MoveEye", tr(err_))
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            ttk.Button(bf, text=tr("Draw the sleeping place (browser)"), command=lambda: self._open_page("/zones")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Look here at night"), command=lambda: _wk("away_here")).pack(side="left", expand=True, fill="x")
            bf2 = ttk.Frame(sbody); bf2.pack(fill="x", pady=(4, 0))
            for a_, l_ in (("test", "Test now"), ("snooze", "Snooze"), ("stop", "Alarm off")):
                ttk.Button(bf2, text=tr(l_), command=lambda a_=a_: _wk(a_)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        if sec in ("Night report", "Battery", "Guest access"):
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w")
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            if sec == "Night report":
                ttk.Button(bf, text=tr("Send now"), command=lambda: threading.Thread(target=report_send, args=(WATCH_REF["w"], True), daemon=True).start()
                           ).pack(side="left", expand=True, fill="x", padx=(0, 4))
                ttk.Button(bf, text=tr("Open animal diary (browser)"), command=lambda: self._open_page("/diary")).pack(side="left", expand=True, fill="x")
            elif sec == "Battery":
                ttk.Button(bf, text=tr("Battery is full now"), command=battery_full).pack(side="left", expand=True, fill="x")
            else:
                ttk.Button(bf, text=tr("Create link (24 h)"), command=lambda: self._guest("create", 24)).pack(side="left", expand=True, fill="x", padx=(0, 4))
                ttk.Button(bf, text=tr("Create link (no limit)"), command=lambda: self._guest("create", 0)).pack(side="left", expand=True, fill="x")
                bf2 = ttk.Frame(sbody); bf2.pack(fill="x", pady=(4, 0))
                ttk.Button(bf2, text=tr("Copy link"), command=lambda: self._guest("copy")).pack(side="left", expand=True, fill="x", padx=(0, 4))
                ttk.Button(bf2, text=tr("End guest access"), command=lambda: self._guest("end")).pack(side="left", expand=True, fill="x")
                self.guest_var = tk.StringVar(value="")
                tk.Entry(sbody, textvariable=self.guest_var, state="readonly", readonlybackground=C["field"], fg=C["txt"], relief="flat",
                         highlightthickness=1, highlightbackground=C["line"]).pack(fill="x", pady=(4, 0))
                ttk.Label(sbody, text=tr("The guest must be able to reach the Pi: same Wi-Fi / hotspot or Tailscale."), style="Mut.TLabel",
                          wraplength=330, justify="left").pack(anchor="w", pady=(4, 0))
        if sec == "Lights":
            self.light_segs, self.light_dots = {}, {}
            for n in ("white", "ir"):
                rf = tk.Frame(sbody, bg=C["panel"]); rf.pack(fill="x", pady=(4, 0))
                dot = tk.Label(rf, text="●", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11)); dot.pack(side="left")
                tk.Label(rf, text=tr(LIGHT_NAMES[n]), bg=C["panel"], fg=C["txt"], width=14, anchor="w").pack(side="left", padx=(4, 6))
                sg = Seg(rf, CFG["light_" + n], lambda m, n=n: light_set(n, m)); sg.pack(side="left")
                self.light_segs[n], self.light_dots[n] = sg, dot
        if sec == "Microphone":
            self.au_meter = tk.Canvas(sbody, height=12, bg=C["field"], highlightthickness=1, highlightbackground=C["line"], bd=0)
            self.au_meter.pack(fill="x", pady=(4, 2))
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            ttk.Button(bf, text=tr("Search devices"), command=self._audio_scan).pack(side="left", expand=True, fill="x")
        if sec == "Loudspeaker":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            ttk.Button(bf, text=tr("Test sound"), command=lambda: self._sound("test")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Siren now"), command=lambda: self._sound("siren")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Stop"), command=lambda: self._sound("stop")).pack(side="left", expand=True, fill="x")
            ttk.Label(sbody, text=tr("Announcement: the Pi speaks this text"), style="Mut.TLabel").pack(anchor="w", pady=(8, 0))
            self.tts_var = tk.StringVar(value=tr("Please keep your distance - you are being filmed."))
            tk.Entry(sbody, textvariable=self.tts_var, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                     highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"]).pack(fill="x", pady=(2, 0))
            tf = ttk.Frame(sbody); tf.pack(fill="x", pady=(4, 0))
            def tts_do(save):
                def run():
                    ok, m = tts_say(self.tts_var.get(), None, save)
                    self._status("Announcement", ("✓ " + (tr("Saved - now selectable as sound for the siren / deterrence") + ": " + m if save else "")) if ok else "⚠ " + tr_err(m))
                threading.Thread(target=run, daemon=True).start()
            ttk.Button(tf, text=tr("Speak now"), command=lambda: tts_do(False)).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(tf, text=tr("Save as own sound"), command=lambda: tts_do(True)).pack(side="left", expand=True, fill="x")
            self.status_labels["Announcement"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Announcement"].pack(anchor="w", pady=(2, 0))
            ttk.Label(sbody, text=tr("Own sounds (.wav / .mp3): put the files into") + " " + sounds_dir(), style="Mut.TLabel",
                      wraplength=330, justify="left").pack(anchor="w", pady=(4, 0))
            tk.Label(sbody, text=tr("Bluetooth").upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
            self.bt_cb = ttk.Combobox(sbody, state="readonly"); self.bt_cb.pack(fill="x", pady=(2, 0))
            self.bt_cb.bind("<<ComboboxSelected>>", lambda e: self.root.focus_set())
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            ttk.Button(bf, text=tr("Search Bluetooth"), command=lambda: (bt_scan(), self._status("Bluetooth", tr("searching …")))).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Connect"), command=lambda: self._bt("connect")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Disconnect"), command=lambda: self._bt("disconnect")).pack(side="left", expand=True, fill="x")
            self.status_labels["Bluetooth"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Bluetooth"].pack(anchor="w", pady=(2, 0))
            self._bt_sig = None
        for s, key, label in TOGGLES:
            if s != sec or simple_hidden(key) or (CFG["lock_on"] and key in LOCK_DENY_KEYS): continue
            if key in TK_AI_MODEL_KEYS or key in TK_SPECIES_KEYS: continue      # 2.98.23 / aufr: in the groups «KI-Modell» / «Tierart» below
            tg = Toggle(sp, tr(label), CFG[key], lambda val, k=key: self._set(k, val)); tg.pack(fill="x", pady=3)
            self.vars[key] = tg; self._g2_q(tg, key)          # «?»: explanation + recommendation (584)
        for s, key, label, lo, hi, step in SLIDERS:
            if s != sec or simple_hidden(key) or key in TK_SPECIES_KEYS: continue
            row = ttk.Frame(sp); row.pack(fill="x", pady=(6, 0))
            ttk.Label(row, text=tr(label)).pack(side="left")
            vl = ttk.Label(row, text=str(CFG[key]), style="Mut.TLabel"); vl.pack(side="right"); self.value_labels[key] = vl
            self._g2_q(row, key)
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
            alx_tk_zones(self, sbody)                  # 2.98.13: zones by kind (066)
        if sec == "Messages":
            ttk.Label(sp, text=tr("Empty = standard text. Placeholders:") + " " + MSG_PLACEHOLDERS, style="Mut.TLabel",
                      wraplength=330, justify="left").pack(anchor="w", pady=(2, 0))
        self._build_texts(sp, sec, skip=TK_AI_MODEL_KEYS + TK_SPECIES_KEYS)
        if sec == "SMS (LTE stick)":
            def sms_test():
                ok, err = sms_send(f"{CFG['device_name'] or 'MoveEye'}: " + tr("test SMS - it works"), force=True)
                self._status("SMS (LTE stick)", ("✓ " + tr("SMS sent")) if ok else "⚠ " + tr_err(err))
            ttk.Button(sbody, text="📱 " + tr("Send test SMS"), command=lambda: threading.Thread(target=sms_test, daemon=True).start()).pack(fill="x", pady=(8, 0))
            self.status_labels["SMS (LTE stick)"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["SMS (LTE stick)"].pack(anchor="w", pady=(4, 0))
        if sec == "MQTT / Home Assistant":
            self.status_labels["MQTT / Home Assistant"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["MQTT / Home Assistant"].pack(anchor="w", pady=(4, 0))
        if sec == "Deterrence":
            ttk.Label(sbody, text=tr("What is seen decides the reaction. Animals need the AI detection, warm bodies the thermal camera. Light flashes: the white light."),
                      style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(6, 0))
        if sec == "Extra sensors":
            self._build_sensor_editor(sbody)
        if sec == "Solar panel":
            self.status_labels["Solar panel"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Solar panel"].pack(anchor="w", pady=(4, 0))
        if sec == "Simulator":
            self.status_labels["Simulator"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Simulator"].pack(anchor="w", pady=(4, 0))
            ttk.Button(sbody, text=tr("Simulation on / off") + "  (F9)", command=lambda: self._sim_toggle("window")).pack(fill="x", pady=(6, 0))
            sf = ttk.Frame(sbody); sf.pack(fill="x", pady=(4, 0))
            def sim_do(fn, done):
                def run():
                    ok, m = fn()
                    self._status("Simulator", ("✓ " + tr(done)) if ok else "⚠ " + tr_err(m))
                threading.Thread(target=run, daemon=True).start()
            if CFG.get("sim_basis_show"):                 # 2.98.55: «MoveEye Sim · Basis» only with «Basis-Simulator anzeigen» (639h)
                ttk.Button(sf, text=tr("Install"), command=lambda: sim_do(sim_install, "Simulator installed")).pack(side="left", expand=True, fill="x", padx=(0, 4))
                ttk.Button(sf, text=tr("Start"), command=lambda: sim_do(sim_start, "Simulator started")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            if CFG.get("sim_basis_show") or sim_running():    # a running one can always be stopped
                ttk.Button(sf, text=tr("Stop"), command=lambda: sim_do(sim_stop, "Simulator stopped")).pack(side="left", expand=True, fill="x")
            kidata_tk_build(self, sbody)                  # training pack with «Vielfalt», «Delete old AI data» (197)
            falearn_tk_build(self, sbody)                 # 2.98.38: «Lernbilder prüfen» (148)
        if sec == "Security":                             # «Log in only encrypted» (574)
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w", pady=(4, 0))
            ttk.Label(sbody, text=tr(SECLOGIN_NOTE), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(4, 0))
        if sec == "Mover":
            self.status_labels["Mover"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Mover"].pack(anchor="w", pady=(4, 0))
        if sec == "GPS module":
            self.status_labels["GPS module"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["GPS module"].pack(anchor="w", pady=(4, 0))
        if sec == "Storm warning":
            self.status_labels["Storm warning"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Storm warning"].pack(anchor="w", pady=(4, 0))
            ttk.Button(sbody, text=tr("Test"), command=lambda: storm_warn("test", tr("test - it works"), test=True)).pack(fill="x", pady=(6, 0))
        if sec == "Reference scan":                                   # 2.95.97
            self.status_labels[sec] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels[sec].pack(anchor="w", pady=(4, 0))
            ttk.Label(sbody, text=tr("refscan-note"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(4, 0))
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(6, 0))
            def rs_go(op):
                ok, err = refscan_start(op, "window")
                if not ok:
                    self._status("Reference scan", "⚠ " + tr(err))
            ttk.Button(bf, text="📸 " + tr("Scan now"), command=lambda: rs_go("scan")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text="🔍 " + tr("Compare now"), command=lambda: rs_go("compare")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Stop"), command=refscan_stop).pack(side="left", expand=True, fill="x")
            ttk.Button(sbody, text=tr("Reports (browser)"), command=lambda: self._open_page("/refscan")).pack(fill="x", pady=(4, 0))
        if sec == "Theft protection":
            self.status_labels["Theft protection"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Theft protection"].pack(anchor="w", pady=(4, 0))
        if sec == "Backup":
            def bk_test():
                ok, err = backup_copy("", None, test=True)
                self._status("Backup", ("✓ " + tr("Test file copied - the settings work.")) if ok else "⚠ " + tr_err(err))
            ttk.Button(sbody, text="🧪 " + tr("Test the backup"), command=lambda: threading.Thread(target=bk_test, daemon=True).start()).pack(fill="x", pady=(8, 0))
            self.status_labels["Backup"] = ttk.Label(sbody, text=STATE.get("backup_status", ""), style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Backup"].pack(anchor="w", pady=(4, 0))
        if sec == "Web stream":
            lk = ext_links()
            txt = (tr("Off – switch on «Picture for other programs» above.") if not lk.get("on") else
                   "MJPEG: " + lk["mjpeg"] + "\n" + tr("Still picture") + ": " + lk["jpg"] + (("\nRTSP: " + lk["rtsp"]) if lk.get("rtsp") else ""))
            e_ = tk.Text(sbody, height=4 if lk.get("on") else 2, bg=C["field"], fg=C["txt"], relief="flat", wrap="char", font=("DejaVu Sans Mono", 8))
            e_.insert("1.0", txt); e_.config(state="disabled"); e_.pack(fill="x", pady=(6, 0))
        if sec == "Recording":
            tk.Label(sbody, text=tr("Recordings stored on").upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
            cands = storage_candidates()
            self._store_opts = [("", tr("memory card (next to the program)"))] + [(c["path"], f"{c['path']} · {c['free_gb']} GB {tr('free')}") for c in cands]
            if CFG["storage_path"] and CFG["storage_path"] not in [p for p, _l in self._store_opts]:
                self._store_opts.append((CFG["storage_path"], CFG["storage_path"] + " (" + tr("missing") + ")"))
            self.store_cb = ttk.Combobox(sbody, state="readonly", values=[l for _p, l in self._store_opts]); self.store_cb.pack(fill="x", pady=(2, 0))
            self.store_cb.current([p for p, _l in self._store_opts].index(CFG["storage_path"]) if CFG["storage_path"] in [p for p, _l in self._store_opts] else 0)
            def pick(_e=None):
                p = self._store_opts[self.store_cb.current()][0]
                if p == CFG["storage_path"]:
                    return
                if not messagebox.askyesno("MoveEye", tr("Store the recordings there from now on? The existing ones are moved over (this can take a while)."), parent=self.root):
                    return
                ok, err = storage_set(p)
                self._status("Storage", ("✓ " + rec_dir()) if ok else "⚠ " + tr_err(err))
            self.store_cb.bind("<<ComboboxSelected>>", pick)
            self.status_labels["Storage"] = ttk.Label(sbody, text=tr("now") + ": " + rec_dir(), style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Storage"].pack(anchor="w", pady=(2, 0))
        if sec == "AI detection":                        # 2.98.23 (Konzept): choice, standard model and own model in ONE group «KI-Modell»
            sbody = tk.Frame(sbody, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
            sbody.pack(fill="x", pady=(10, 0))
            tk.Label(sbody, text="🧠 " + tr("AI model"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
            self._build_texts(sbody, sec, only=("ai_model",))
        if sec == "AI detection" and not ai_model_paths()[0]:
            ttk.Button(sbody, text=tr("Download AI model") + " (≈ 70 MB)", command=self._ai_dl).pack(fill="x", pady=(8, 0))
            self.status_labels["AI model"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["AI model"].pack(anchor="w", pady=(2, 0))
        if sec == "AI detection":                        # part 195: own MoveEye model (YOLO) next to the standard
            ttk.Label(sbody, text="🧠 " + tr("Own model: trained on GitHub from simulator pictures and your labelled alarm pictures (person, animal, vehicle). After the download MoveEye uses it (back to the standard: «AI model», Expert view). If it is missing or fails, the standard model runs."),
                      style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(8, 0))
            ttk.Button(sbody, text=tr("Update own model" if own_ai_paths()[0] else "Download own model"), command=self._own_ai_dl).pack(fill="x", pady=(4, 0))
            self.status_labels["Own AI model"] = ttk.Label(sbody, text=own_ai_long_text(), style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Own AI model"].pack(anchor="w", pady=(2, 0))
            for s_, key_, label_ in TOGGLES:               # 2.98.23: the switch «update by itself» and the address in the same group
                if s_ == sec and key_ in TK_AI_MODEL_KEYS and not simple_hidden(key_) and not (CFG["lock_on"] and key_ in LOCK_DENY_KEYS):
                    tg_ = Toggle(sbody, tr(label_), CFG[key_], lambda val, k=key_: self._set(k, val)); tg_.pack(fill="x", pady=(6, 0))
                    self.vars[key_] = tg_
            self._build_texts(sbody, sec, only=("ai_own_url",))
            self._tk_species_group(sbody.master, sec)          # aufr: «Tierart» as its own group below «KI-Modell»
        if sec == "Notifications":
            ttk.Button(sbody, text=tr("Test notification"),
                       command=lambda: self.watch.notifier.test(self.watch.frame_out)).pack(fill="x", pady=(8, 0))
        if sec == "Wi-Fi / hotspot" and not CFG["lock_on"]:
            self._build_wifi_box(sbody)
        if sec == "Camping / protection":
            ttk.Label(sbody, text="🛡 " + tr("Protection")).pack(anchor="w", pady=(8, 2))      # 2.95.105: one level
            pf = ttk.Frame(sbody); pf.pack(fill="x")
            for i_, (lv_, nm_) in enumerate([("off", "Off"), ("watch", "Watchful"), ("full", "Full protection")]):
                ttk.Button(pf, text=tr(nm_), command=lambda l_=lv_: self._protect(l_)).grid(row=0, column=i_, sticky="ew", padx=(0, 4))
                pf.columnconfigure(i_, weight=1)
            ttk.Label(sbody, text=tr(protect_status().get("device", "")), foreground="#8a96a6", wraplength=380).pack(anchor="w", pady=(4, 0))
            ttk.Label(sbody, text=tr("Mode") + " (" + tr("one switch for the whole device") + ")").pack(anchor="w", pady=(8, 2))
            mg = ttk.Frame(sbody); mg.pack(fill="x")
            for i_, (mid, mic, mname) in enumerate([(x_["id"], x_["icon"], x_["name"]) for x_ in mode_state()["list"]] + [("", "⚙", "Own settings")]):
                def _pick(m_=mid):
                    ok_, err_ = mode_set(m_, "window")
                    self._status("Mode", ("✓ " if ok_ else "⚠ ") + (tr(err_) if err_ else tr(dict((x[0], x[2]) for x in MODES).get(m_, "Own settings"))))
                ttk.Button(mg, text=mic + " " + tr(mname), command=_pick).grid(row=i_ // 2, column=i_ % 2, sticky="ew", padx=(0, 4), pady=2)
            mg.columnconfigure(0, weight=1); mg.columnconfigure(1, weight=1)
            ttk.Button(sbody, text="☾ " + tr("Guard tonight"), command=self._night).pack(fill="x", pady=(8, 0))
            ttk.Button(sbody, text="📍 " + tr("Set up the place"), command=self._place).pack(fill="x", pady=(6, 0))     # 2.98.30 (317, 582)
            ttk.Button(sbody, text="🚶 " + tr("Walk test"), command=self._walktest).pack(fill="x", pady=(6, 0))     # 2.98.13 (415, 575)
        if sec == "Camera / Servos":
            self._fov_box(sbody)                                                    # 2.98.30: field of view per camera (318, 582)
            self.status_labels["Battery saver"] = ttk.Label(sbody, text=batt_save_text(), style="Mut.TLabel", wraplength=380, justify="left")
            self.status_labels["Battery saver"].pack(anchor="w", pady=(4, 0))
            ttk.Button(sbody, text=tr("Open quick guide (browser)"), command=lambda: self._open_page("/quick")).pack(fill="x", pady=(6, 0))
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(6, 0))
            ttk.Button(bf, text=tr("Arm (countdown)"), command=arm).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Arm now"), command=lambda: arm(0)).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Disarm"), command=lambda: self._protect("off")).pack(side="left", expand=True, fill="x")
            bf3 = ttk.Frame(sbody)
            if not CFG["lock_on"]:
                bf3.pack(fill="x", pady=(6, 0))
            ttk.Button(bf3, text=tr("Own Wi-Fi ON"), command=lambda: (netauto_pause(), hotspot_switch_later(True, 0.2))).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf3, text=tr("Own Wi-Fi OFF"), command=lambda: (netauto_pause(), hotspot_switch_later(False, 0.2))).pack(side="left", expand=True, fill="x")
            bf4 = ttk.Frame(sbody)
            if not CFG["lock_on"]:
                bf4.pack(fill="x", pady=(6, 0))
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
        if sec == "Setup":
            self.status_labels["Other devices"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Other devices"].pack(anchor="w", pady=(6, 0))
            # 639d: «Pi ausschalten / neu starten / Programm pausieren» moved to the part «System» of the group System (like the web)
            if CFG["lock_on"]:
                info = lock_info()
                ttk.Label(sbody, text="🔐 " + tr("Operator mode is on") + (f" {tr('since')} {info['since']}" if info["since"] else ""),
                          style="Mut.TLabel").pack(anchor="w", pady=(10, 2))
                ttk.Button(sbody, text=tr("End operator mode (PIN)") + " …", command=self._unlock).pack(fill="x")
            pwf = tk.Frame(sbody, bg=C["panel"])
            if not CFG["lock_on"]:                       # operator mode: password, operator mode, settings files are off limits
                pwf.pack(fill="x")
            sbody_ = sbody; sbody = pwf
            tk.Frame(sbody, bg=C["line"], height=1).pack(fill="x", pady=(10, 6))
            ttk.Label(sbody, text="🔐 " + tr("Password, users and app keys: Settings → Security"), style="Mut.TLabel", wraplength=330,
                      justify="left").pack(anchor="w")                    # 573: moved there (one place for the security)
            ttk.Button(sbody, text="🔐 " + tr("Operator mode (lock settings)") + " …", command=self._lock).pack(fill="x", pady=(6, 0))  # (hidden while locked)
            ttk.Button(sbody, text="📱 " + tr("QR code for the phone") + " …", command=lambda: self._qr_window(False)).pack(fill="x", pady=(6, 0))
            ttk.Button(sbody, text="💬 " + tr("Feedback to the developer") + " …", command=self._feedback).pack(fill="x", pady=(6, 0))
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Save settings …"), command=self._export).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Load settings …"), command=self._import).pack(side="left", expand=True, fill="x")
            sbody = sbody_
        if sec == "Updates":
            self.upd_cb = ttk.Combobox(sbody, state="readonly", height=3); self.upd_cb.pack(fill="x", pady=(6, 0))
            self.upd_cb.bind("<<ComboboxSelected>>", lambda e: self.root.focus_set())
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
            ttk.Button(bf, text=tr("Search versions"), command=self._upd_check).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("Switch to this version"), command=self._upd_install).pack(side="left", expand=True, fill="x")
            self.status_labels["Updates"] = ttk.Label(sbody, text=tr("Running now") + ": " + APP_VERSION, style="Mut.TLabel", wraplength=330, justify="left")
            self.status_labels["Updates"].pack(anchor="w", pady=(4, 0))
            self._upd_fill()
        if sec == "Auto-tune":
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(8, 0))
            ttk.Button(bf, text=tr("Recalibrate (scene empty)"), command=self.watch.tuner.reset).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text=tr("⚠ Reset to factory settings …"), command=self._reset_settings).pack(side="left", expand=True, fill="x")

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
            if not ai_ok and rl["trigger"] not in ("person", "motion", "prealarm", "warm", "noise"):
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

    # ---- extra sensors ----------------------------------------------------
    def _build_sensor_editor(self, parent):
        self.sens_rows = {}
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        S = STATE.get("sens") or {}
        seen = S.get("seen") or []
        kinds = [(k, tr(l)) for k, l in (("pir", "Motion detector (PIR)"), ("door", "Door / lid contact"), ("gas", "Gas / smoke"),
                                           ("tag", "Bluetooth tag"), ("other", "Other sensor"))]
        alarms = [("armed", tr("only when armed")), ("always", tr("always (also when disarmed)")), ("off", tr("no alarm, only note it"))]

        def src_label(v):
            if not v:
                return "– " + tr("not connected") + " –"
            if v.startswith("gpio:"):
                return "GPIO " + v[5:]
            f = next((e for e in seen if e["src"] == v), None)
            return {"rf": "433 MHz: ", "zb": "Zigbee: ", "bl": "Bluetooth: ", "si": "Sim: "}.get(v[:2], "") + (f["label"] if f else v.split(":", 1)[1])

        def combo(row, pairs, val, cb):
            lab = dict(pairs); back = {l: c for c, l in pairs}
            c = ttk.Combobox(row, values=[l for _c, l in pairs], state="readonly"); c.set(lab.get(val, val)); c.pack(fill="x", pady=(2, 0))
            c.bind("<<ComboboxSelected>>", lambda e: (self.root.focus_set(), cb(back.get(c.get(), c.get()))))
            return c
        for x in CFG["sensors"]:
            card = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
            card.pack(fill="x", pady=(6, 0))
            r1 = tk.Frame(card, bg=C["panel"]); r1.pack(fill="x")
            dot = tk.Label(r1, text="●", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 11)); dot.pack(side="left")
            nv = tk.StringVar(value=x["name"])
            ent = tk.Entry(r1, textvariable=nv, width=16, **ent_kw); ent.pack(side="left", padx=(4, 8), fill="x", expand=True)
            for ev in ("<Return>", "<FocusOut>"):
                ent.bind(ev, lambda e, i=x["id"], v=nv: self._sens_do({"action": "set", "id": i, "field": "name", "value": v.get()}, rebuild=False))
            xl = tk.Label(r1, text="✕", bg=C["panel"], fg=C["red"], font=("DejaVu Sans", 11, "bold"), cursor="hand2")
            xl.pack(side="right"); xl.bind("<Button-1>", lambda e, s_=x: self._sens_remove(s_))
            opts = [""] + [f"gpio:{g}" for g in S.get("free", sens_free_gpios())] + [e["src"] for e in seen]
            if x["src"] and x["src"] not in opts:
                opts.insert(1, x["src"])
            opts = list(dict.fromkeys(opts))
            for lbl, pairs, val, f in ((tr("Kind"), kinds, x["kind"], "kind"), (tr("Connected to"), [(v, src_label(v)) for v in opts], x["src"], "src"),
                                       (tr("Alarm"), alarms, x["alarm"], "alarm")):
                ttk.Label(card, text=lbl, style="Mut.TLabel").pack(anchor="w", pady=(4, 0))
                combo(card, pairs, val, lambda v, i=x["id"], f=f: self._sens_do({"action": "set", "id": i, "field": f, "value": v}))
            if x["src"].startswith("gpio:"):
                Toggle(card, tr("Reversed (reports at LOW)"), x["inv"],
                       lambda v, i=x["id"]: self._sens_do({"action": "set", "id": i, "field": "inv", "value": v}, rebuild=False)).pack(fill="x", pady=(4, 0))
            r3 = tk.Frame(card, bg=C["panel"]); r3.pack(fill="x", pady=(4, 0))
            stl = ttk.Label(r3, text="", style="Mut.TLabel", wraplength=230, justify="left"); stl.pack(side="left", fill="x", expand=True)
            ttk.Button(r3, text=tr("Test"), command=lambda i=x["id"]: self._sens_do({"action": "test", "id": i}, rebuild=False)).pack(side="right")
            self.sens_rows[x["id"]] = (dot, stl)
        self.sens_err = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330); self.sens_err.pack(anchor="w", pady=(4, 0))
        bf = tk.Frame(parent, bg=C["panel"]); bf.pack(fill="x", pady=(4, 0))
        for i, (k, l) in enumerate((("pir", "Motion detector"), ("door", "Door contact"), ("gas", "Gas / smoke"), ("tag", "Bluetooth tag"), ("other", "Radio sensor"))):
            ttk.Button(bf, text="+ " + tr(l), command=lambda k=k: self._sens_do({"action": "add", "kind": k})).grid(row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2)
        bf.columnconfigure(0, weight=1); bf.columnconfigure(1, weight=1)
        fresh = [e for e in seen if not any(x["src"] == e["src"] for x in CFG["sensors"])][:8]
        if fresh:
            ttk.Label(parent, text=tr("Found radio devices - tap one to add it:"), style="Mut.TLabel").pack(anchor="w", pady=(8, 0))
            for e in fresh:
                d = e.get("data") or {}
                g = ("tag" if e["src"].startswith("ble:") else "door" if any(k in d for k in ("contact", "closed", "contact_open", "state"))
                     else "gas" if any(k in d for k in ("smoke", "gas", "carbon_monoxide")) else "pir" if any(k in d for k in ("occupancy", "motion")) else "other")
                ttk.Button(parent, text=src_label(e["src"]), command=lambda e=e, g=g: self._sens_do(
                    {"action": "add", "kind": g, "src": e["src"], "name": e["label"][:24]})).pack(fill="x", pady=(2, 0))
        self.status_labels["Extra sensors"] = ttk.Label(parent, text="", style="Mut.TLabel", wraplength=330, justify="left")
        self.status_labels["Extra sensors"].pack(anchor="w", pady=(6, 0))

    def _sens_do(self, d, rebuild=True):
        ok, err = sens_action(d)
        try:
            self.sens_err.config(text="" if ok else "⚠ " + tr_err(err))
        except Exception:
            pass
        if ok and d.get("action") == "test":
            self._toast("✓ " + tr("Test sent")) if hasattr(self, "_toast") else None
        if ok and rebuild:
            self.open_secs.add("grp:extras"); self._schedule_rebuild()

    def _sens_remove(self, x):
        if messagebox.askyesno(tr("Remove"), tr("Remove this sensor?") + "\n\n" + x["name"], parent=self.root):
            self._sens_do({"action": "remove", "id": x["id"]})

    def _sens_paint(self, st):
        S = st.get("sens") or {}
        col = {"active": C["red"], "pulse": C["yel"], "missing": C["org"] if "org" in C else C["yel"], "ok": C["grn"], "error": C["red"]}
        word = {"active": lambda x: {"door": "open", "gas": "gas / smoke!", "pir": "motion"}.get(x["kind"], "triggered"),
                "pulse": lambda x: "moved / triggered", "missing": lambda x: "out of range", "ok": lambda x: "closed" if x["kind"] == "door" else "quiet",
                "error": lambda x: "GPIO error", "unknown": lambda x: "waiting for data", "off": lambda x: "off"}
        for x in CFG["sensors"]:
            w_ = getattr(self, "sens_rows", {}).get(x["id"])
            if not w_:
                continue
            q = (S.get("st") or {}).get(x["id"]) or {}
            try:
                w_[0].config(fg=col.get(q.get("state"), C["mut"]))
                w_[1].config(text=(tr(word.get(q.get("state"), word["unknown"])(x)) if x["src"] else tr("choose where it is connected"))
                             + ((" · " + tr("last") + ": " + q["last"]) if q.get("last") else ""))
            except tk.TclError:
                pass
        p = []
        if CFG["rf433_on"]:
            p.append("433 MHz: " + tr_err(S.get("rf", "off")))
        if CFG["zigbee_on"]:
            p.append("Zigbee: " + tr_err(S.get("zb", "off")))
        if CFG["ble_on"]:
            p.append("Bluetooth: " + tr_err(S.get("ble", "off")))
        if not CFG["sens_on"]:
            p.insert(0, tr("Extra sensors are switched off"))
        self._status("Extra sensors", " · ".join(p))

    # ---- text settings (notifications, location, presence) ----------------
    def _build_texts(self, parent, sec, skip=(), only=None):
        specs = [x for x in TEXTS if x[0] == sec and not simple_hidden(x[1]) and not (CFG["lock_on"] and x[1] in LOCK_DENY_KEYS)
                 and x[1] not in skip and (only is None or x[1] in only)]
        if not specs:
            return
        ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                      highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
        err = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330, justify="left")
        for _s, key, label, kind, extra in specs:
            m_ = re.fullmatch(r"msg_(person|prealarm|warm|noise)_(title|text)", key)
            std = ("\n" + tr("standard") + ": " + msg_defaults()[m_.group(1)][0 if m_.group(2) == "title" else 1]) if m_ else ""
            ttk.Label(parent, text=tr(label) + std, style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(8, 0))
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
        for txt, path in (("Open recordings preview (browser)", "/recordings"), ("Open camera grid (browser)", "/cams"), ("Open zone editor (browser)", "/zones"),
                          ("Open event log & archive (browser)", "/log")):
            ttk.Button(parent, text=tr(txt), command=lambda p=path: self._open_page(p)).pack(fill="x", pady=(6 if path != "/recordings" else 10, 0))
        self.src_msg = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330)
        self.src_msg.pack(anchor="w", pady=(4, 0))
        self._fill_sources()

    def _lock(self):
        from tkinter import simpledialog
        np_ = ""
        if not CFG["lock_pin"] or messagebox.askyesno("MoveEye", tr("Set a new PIN? (No = keep the current PIN)"), parent=self.root):
            np_ = simpledialog.askstring("MoveEye", tr("New PIN for unlocking (4-8 digits):"), show="•", parent=self.root) or ""
            if not np_:
                return
            if (simpledialog.askstring("MoveEye", tr("Repeat the PIN:"), show="•", parent=self.root) or "") != np_:
                messagebox.showerror("MoveEye", tr("The PINs are not the same"), parent=self.root); return
        if not messagebox.askyesno("MoveEye", tr("Lock the settings now? Only the main switches stay usable. Everything changed until then is put back when unlocking with the PIN."), parent=self.root):
            return
        ok, err = lock_set("lock", new_pin=np_, source="window")
        if not ok:
            messagebox.showerror("MoveEye", tr_err(err), parent=self.root); return
        self._rebuild()

    def _unlock(self):
        from tkinter import simpledialog
        pin = simpledialog.askstring("MoveEye", tr("PIN:"), show="•", parent=self.root)
        if not pin:
            return
        ok, err = lock_set("unlock", pin=pin, source="window")
        if not ok:
            messagebox.showerror("MoveEye", tr_err(err), parent=self.root); return
        n = len(LOCK_LAST["restored"])
        if n:
            messagebox.showinfo("MoveEye", tr("Settings unlocked") + " · " + str(n) + " " + tr("changes put back"), parent=self.root)
        self._rebuild()

    def _pause(self):
        try:
            m = PAUSE_CHOICES[self.pause_cb.current()]
        except (IndexError, tk.TclError, TypeError, AttributeError):
            m = 30
        txt = f"{m} min" if m < 60 else f"{m // 60} h"
        if not messagebox.askyesno("MoveEye", tr("Switch the program off now and start it again in") + f" {txt}?\n\n"
                                   + tr("While paused there is no monitoring and there are no alarms."), parent=self.root):
            return
        ok, err = pause_program(m, source="window")
        self._status("Power", ("⏸ " + tr("Program is pausing …")) if ok else "⚠ " + tr_err(err))

    def _guest(self, action, hours=24):
        if action in ("create", "end"):
            guest_set(action, hours)
        g = guest_info()
        link = (page_address() or f"http://<pi-ip>:{CFG['web_port']}/").rstrip("/") + g["path"] if g["active"] else ""
        if hasattr(self, "guest_var"):
            self.guest_var.set(link)
        if link and action in ("create", "copy"):
            try:
                self.root.clipboard_clear(); self.root.clipboard_append(link)
                self._status("Guest access", tr("Link copied") + ": " + link)
            except tk.TclError:
                pass

    def _tk_extras(self, st):
        # overview: the title of a topic is green while its main function is on
        main = {"Camping / protection": lambda: CFG["camping"], "Power saving": lambda: CFG["eco_on"], "Battery": lambda: (st.get("battery") or {}).get("on"),
                "Theft protection": lambda: CFG["tamper_on"] or CFG["tamper_motion"] or CFG["tamper_power"], "Notifications": lambda: CFG["notify_on"],
                "Night report": lambda: CFG["report_on"], "SMS (LTE stick)": lambda: CFG["sms_on"], "Detection": lambda: CFG["detection_on"],
                "AI detection": lambda: CFG["ai_enabled"], "Vehicle filter": lambda: CFG["car_filter"], "Rain": lambda: CFG["rain_auto"],
                "Wind": lambda: CFG["wind_auto"], "Low light": lambda: CFG["lowlight_auto"], "Auto-tune": lambda: CFG["auto_tune"],
                "Camera / Servos": lambda: CFG["track_person"], "Patrol": lambda: CFG["patrol"], "Thermal camera": lambda: CFG["thermal_on"],
                "Lights": lambda: CFG["light_white"] != "off" or CFG["light_ir"] != "off",
                "Deterrence": lambda: any((a == "sound" and out_selected()) or (a == "light" and bool(CFG["light_white_out"]))
                                          or (a == "both" and (out_selected() or bool(CFG["light_white_out"])))
                                          for a in (CFG[f"deter_{g}_act"] for g in ("person", "big", "small", "warm"))),
                "Microphone": lambda: bool(CFG["audio_in"]), "Loudspeaker": lambda: CFG["siren_on"] != "off", "Recording": lambda: CFG["record"],
                "Timelapse": lambda: CFG["timelapse_on"], "Backup": lambda: CFG["backup_type"] != "off", "Relays": lambda: CFG["relays_on"],
                "Schedule": lambda: any(x.get("enabled") for x in SCHEDULES), "Wi-Fi / hotspot": lambda: CFG["hotspot_on"],
                "Web stream": lambda: CFG["web_stream"], "MQTT / Home Assistant": lambda: CFG["mqtt_on"], "Updates": lambda: CFG["update_auto"],
                "Extra sensors": lambda: CFG["sens_on"] and bool(CFG["sensors"]), "Storm warning": lambda: CFG["storm_on"], "GPS module": lambda: CFG["gpsmod_on"], "Mover": lambda: MOVER["avail"], "Simulator": lambda: sim_live(), "Solar panel": lambda: CFG["solar_on"]}
        for key, (arr, secs, _c, _w) in list(getattr(self, "grp_meta", {}).items()):
            try:
                if arr.winfo_exists():
                    on = any(main[x]() for x in secs if x in main) or (key == "grp:alarm" and st.get("arm_state") in ("armed", "arming"))
                    arr.config(fg=C["grn"] if on else C["mut"])
            except Exception:
                pass
        for k, (h, _b, _t) in list(getattr(self, "subs", {}).items()):
            f = main.get(k[4:])
            try:
                if f is not None and h.winfo_exists():
                    h.config(fg=C["grn"] if f() else C["mut"])
            except Exception:
                pass
        self._status("MQTT / Home Assistant", "MQTT: " + (("✓ " + tr("connected")) if MQTT["status"] == "connected" else MQTT["status"].replace("error: ", "⚠ "))
                     + ((" · " + (CFG["mqtt_prefix"].strip("/") or "motionwatch") + "/" + device_uid() + "/…") if CFG["mqtt_on"] else ""))
        if CFG["fleet"]:
            FLEET["seen"] = time.time()
            parts = []
            for d in CFG["fleet"]:
                x = FLEET["state"].get(d["id"], {})
                parts.append(f"{d.get('name') or d['url']}: " + ((("🚨 " if x.get("persons") else "") + tr(x.get("arm", "?"))) if x.get("ok") else "⚠ " + tr(x.get("err") or "not reachable")))
            self._status("Other devices", "🛰 " + tr("Other devices") + ": " + " · ".join(parts) + "  (" + tr("overview on the web page: Cameras") + ")")
        self._sens_paint(st)
        si_ = sim_status()
        self._status("Simulator", (tr("off - the real cameras and sensors are used") if not si_["on"] else
                                   (tr("connected") + f" · {si_['url']} · " + (tr("night") if si_["dark"] else tr("day")) + f" · {si_['ambient']} °C"
                                    if si_["ok"] else tr_err(si_["msg"]) + " · " + si_["url"]))
                     + ("\n🔎 " + tr("Simulators in the network:") + " " + ", ".join(f"{x['name']} ({x['ip']}:{x['port']})" for x in si_["found"]) if si_["found"] else "")
                     + ("\n🎮 " + tr("3D simulator for Windows (ZIP)") + ": " + page_address(ip3_) + "sim/simulator3d.zip" if (ip3_ := local_ip()) else ""))
        so_ = st.get("solar") or {}; nf_ = st.get("night")
        l_ = [(tr("off") if not CFG["solar_on"] else tr("no current meter found at this address") if not so_.get("ok")
               else f"{so_['w']} W ({so_['v']} V · {so_['a']} A) · {tr('today')} {so_['wh']} Wh · {tr('max.')} {so_['max']} W")]
        l_.append((tr("Battery lasts until sunrise") if nf_["enough"] else tr("Battery probably too low until sunrise")) + f" ({nf_['sunrise']}): {nf_['have_h']} h / {nf_['need_h']} h"
                  if nf_ else tr("Night forecast: needs a battery value (Settings → Battery)"))
        self._status("Solar panel", "\n".join(l_))
        if CFG["gpsmod_on"]:
            g_ = GPSMOD
            if g_["lat"] is not None and time.time() - g_["t"] < 300:
                t_ = f"{g_['lat']:.5f}, {g_['lon']:.5f}" + (f" · {g_['sats']} {tr('satellites')}" if g_["sats"] is not None else "") + " · " + g_["via"]
            else:
                t_ = tr(g_["status"]) + (f" ({g_['sats']} {tr('satellites')})" if g_["sats"] is not None else "")
            if CFG["gps_theft"]:
                t_ += "\n" + (tr("THEFT ALARM") if g_["alarm_t"] else tr("Theft tracking on guard") if g_["anchor"] else tr("Theft tracking starts when armed"))
                if g_.get("dist") is not None and g_["anchor"]:
                    t_ += f" · {g_['dist']} m"
            self._status("GPS module", t_)
        else:
            self._status("GPS module", tr("off"))
        self._status("Mover", ("✓ " if MOVER["avail"] else "") + tr(MOVER["msg"]))
        S_ = st.get("storm") or {}
        if S_:
            L_ = [tr("Air pressure") + ": " + ((f"{S_['p']} hPa" + (f" ({S_['trend']:+.1f} hPa / 3 h)" if S_.get("trend") is not None else " (" + tr("trend after 1 hour") + ")"))
                                                if S_.get("p") else tr("no BME280 sensor")),
                  tr("Wind meter") + ": " + (tr("none") if not S_.get("meter") else tr("GPIO error") if not S_.get("meter_ok")
                                             else (f"{S_['wind']} km/h" if S_.get("wind") is not None else "–") + (f" · {tr('gusts')} {S_['gust']} km/h" if S_.get("gust") is not None else ""))]
            if CFG["storm_forecast"]:
                L_.append(tr("Forecast, next 12 h") + ": " + (f"{tr('gusts')} {S_['fc']:.0f} km/h" if S_.get("fc") is not None else tr("no forecast yet")))
            if S_.get("last"):
                L_.append(tr("Last warning") + ": " + S_["last"])
            self._status("Storm warning", "\n".join(L_))
        tp = st.get("tamper") or {}
        if tp:
            self._status("Theft protection", "🧭 " + tr("Motion sensor") + ": " + (tr("found") if tp.get("sensor") else tr("not fitted"))
                         + " · 📷 " + tr({"learning": "learning the picture", "watching": "on guard"}.get(tp.get("state"), "–"))
                         + ((" · ⚠ " + tp["last"]) if tp.get("last") else ""))
        L = st.get("report_last") or {}
        self._status("Night report", (f"{tr('Last report')} {L['t'][11:16]} ({tr('sent') if L.get('sent') else tr('not sent')}): {L['text']}"
                                      if L.get("text") else tr("No report sent yet - the first one comes in the morning.")))
        b = st.get("battery") or {}
        press = tr("Press 'Battery is full now' after charging.")
        if b.get("src") == "ups":
            self._status("Battery", f"🔋 {tr('UPS HAT')}{' (E)' if b.get('model') == 'e' else ''}: {b['pct']} % · {b['volt']} V · " + (
                f"⚡ {tr('on battery')} · {b['hours'] or 0:.1f} h {tr('left')} · {b['watts']} W" if b.get("on_battery")
                else ("🔌 " + (tr("fast charging" if b.get("fast") else "charging") if b.get("charging") else tr("mains power"))))
                + (("\n" + tr("Cells") + ": " + " / ".join(f"{c:.2f}" for c in b["cells"]) + " V") if b.get("cells") else ""))
        else:
          self._status("Battery", tr("Off - enter the capacity of the powerbank.") if not b.get("on") else
                     (f"{press} · {b['watts']} W" if b.get("pct") is None else
                      f"🔋 {b['pct']} % · {b['hours']:.1f} h {tr('left')} · {b['watts']} W" + (f" ({tr('estimated')})" if b.get("src") == "estimate" else "")))
        if BATT_SAVE["on"] and self.status_labels.get("Battery") is not None:      # 2.98.13: battery saver (105)
            self._status("Battery", self.status_labels["Battery"].cget("text") + "\n🐢 " + batt_save_text())
        self._status("Battery saver", ("🐢 " if BATT_SAVE["on"] else "🔋 ") + batt_save_text())
        g = guest_info()
        if g["active"]:
            until = f"{tr('until')} " + datetime.fromtimestamp(g["until"]).strftime("%a %H:%M") if g["until"] else tr("no time limit")
            self._status("Guest access", f"🟢 {tr('Guest access is on')} · {until}" + (f" · 👁 {g['watching']}" if g["watching"] else ""))
            if hasattr(self, "guest_var") and not self.guest_var.get():
                self.guest_var.set((page_address() or f"http://<pi-ip>:{CFG['web_port']}/").rstrip("/") + g["path"])
        else:
            self._status("Guest access", "⚪ " + tr("Guest access is off"))
            if hasattr(self, "guest_var"):
                self.guest_var.set("")

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
            if messagebox.askyesno("MoveEye", tr("Remove this network camera?")):
                source_remove(self.watch, self.src_items[i]["id"][4:]); self._fill_sources()

    def _open_page(self, path):
        import webbrowser
        self.web.start()
        webbrowser.open(f"{'https' if WEB_OPTS['https'] else 'http'}://127.0.0.1:{CFG['web_port']}{path}")

    # ---- schedule ----------------------------------------------------------
    def _build_schedule_box(self, parent):
        ttk.Label(parent, text=tr(SCHED_NOTE), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(0, 2))
        names = DAYS_SHORT[cur_lang()]
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
        if messagebox.askyesno("MoveEye", tr("Remove this schedule?")):
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
        for d, nm in enumerate(DAYS_SHORT[cur_lang()]):
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
                    messagebox.showerror("MoveEye", tr("Time must look like 07:30"), parent=dlg); return
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
        return json.dumps([{k: v for k, v in r.items() if k != "mode"} for r in RELAYS], sort_keys=True) + str(self._ai_ok()) + str(live_has_head())

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
        self.open_secs.add("grp:extras"); self._schedule_rebuild()

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
        self._pos_label()
        if self.stick is not None:
            self.stick.draw()

    def _pos_label(self):
        if self.l_pt is not None and self.l_pt.winfo_exists():
            self.l_pt.config(text=f"◎ Pan {CFG['pan']:.0f} % · Tilt {CFG['tilt']:.0f} %")

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
        self._g2_factory()                               # 586 / 584: «Reset to factory settings» (password / PIN, typed word, backup)

    # ---- collapsible sections -------------------------------------------
    def _set_section(self, sec, open_, save=True):
        head, body = self.sections[sec]
        if save:
            (self.open_secs.add if open_ else self.open_secs.discard)(sec)
            if sorted(self.open_secs) != sorted(CFG["ui_open"]):
                CFG["ui_open"] = sorted(self.open_secs); save_settings()
        meta = getattr(self, "grp_meta", {}).get(sec)
        if meta is not None:
            head.config(text=self.group_titles.get(sec, tr(sec)).upper()); meta[0].config(text="▾" if open_ else "▸")
        else:
            head.config(text=("▾  " if open_ else "▸  ") + self.group_titles.get(sec, tr(sec)).upper())
        if open_:
            body.pack(fill="x", pady=(4, 0))
        else:
            body.pack_forget()

    def _search(self):
        """Search field of the settings: only the groups that contain the word, opened (like the web page)."""
        q = self.search_var.get().strip().lower()
        try:
            self.search_ph.place_forget() if q else self.search_ph.place(in_=self.search_ph.master.winfo_children()[1], x=1, rely=0.5, anchor="w")
        except (tk.TclError, IndexError):
            pass
        meta = getattr(self, "grp_meta", {})
        if q and self._open_before is None:
            self._open_before = set(self.open_secs)
        cards = [m[2] for m in meta.values()]
        for c in cards:
            c.pack_forget()
        self.no_match.pack_forget()
        hits = 0
        for key, (arr, secs, card, words) in meta.items():
            if q and q not in words:
                continue
            card.pack(fill="x", pady=(0, 8)); hits += 1
            if q:
                self._set_section(key, True, save=False)
                for sec in secs:
                    k = "sub:" + sec
                    if k in self.subs:
                        sw = " ".join([tr(sec)] + [tr(t_[2]) for lst in (TOGGLES, SLIDERS, TEXTS) for t_ in lst if t_[0] == sec]).lower()
                        self._show_sub(k, q in sw)
        if q and not hits:
            self.no_match.pack(anchor="w", pady=(4, 0))
        if not q and self._open_before is not None:              # search cleared: back to how it was
            self.open_secs = self._open_before; self._open_before = None
            for key in meta:
                self._set_section(key, key in self.open_secs, save=False)
            for k in self.subs:
                self._show_sub(k, k in self.open_secs)

    def _show_sub(self, k, open_):
        h, body, title = self.subs[k]
        self._sub_arrow(k, open_)
        if open_:
            body.pack(fill="x", pady=(2, 0), after=h)
        else:
            body.pack_forget()

    def _toggle_section(self, sec):
        self._set_section(sec, sec not in self.open_secs)

    def _groups_only(self):
        for sec in self.sections:
            self._set_section(sec, True)
        for k in getattr(self, "subs", {}):
            self._set_sub(k, False)

    def _all_sections(self, open_):
        for sec in self.sections:
            self._set_section(sec, open_)
        for k in getattr(self, "subs", {}):
            self._set_sub(k, open_)

    # ---- callbacks -------------------------------------------------------
    def _set(self, key, value):
        if CFG["lock_on"] and key in LOCK_DENY_KEYS:
            return
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
        wp_add(); save_settings()
        log_event("patrol", f"Waypoint added at pan {CFG['pan']:.0f}% / tilt {CFG['tilt']:.0f}%  ->  {wp_text()}")

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
                pim = Image.fromarray(img)
                if getattr(self, "_egg_t0", 0):
                    pim = self._egg_draw(pim)
                self.photo = ImageTk.PhotoImage(pim); self.video.config(image=self.photo)
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

    def _audio_scan(self):
        def work():
            audio_scan()
            self.root.after(0, self._schedule_rebuild)          # the device lists of the selection boxes are rebuilt
        threading.Thread(target=work, daemon=True).start()

    def _sound(self, what):
        if what == "stop":
            sound_stop(); return
        ok, err = sound_play(None, 2.5 if what == "test" else None, None, "test" if what == "test" else "by hand (desktop)")
        self._status("Loudspeaker", "" if ok else "⚠ " + tr_err(err))

    def _power(self, action):
        from tkinter import messagebox
        q = (tr("Shut down the Raspberry Pi now?") + "\n\n" + tr("A running recording is finished first. To switch it on again: unplug the power and plug it in again.")
             if action == "poweroff" else tr("Restart the Raspberry Pi now?"))
        if not messagebox.askyesno("MoveEye", q, parent=self.root):
            return
        ok, err = power_action(action, source="desktop")
        self._status("Power", (tr("The Pi is shutting down …") if action == "poweroff" else tr("The Pi is restarting …")) if ok else "⚠ " + tr_err(err))

    def _open_help(self):
        """The manual is a page of the web interface: open it in the browser of the Pi."""
        import webbrowser
        if not self.web.started:
            self.web.start()
        url = f"{'https' if WEB_OPTS['https'] else 'http'}://127.0.0.1:{CFG['web_port']}/help"
        try:
            webbrowser.open(url)
        except Exception:
            pass
        log_event("sys", f"Manual: {url}")

    def _upd_fill(self):
        cb = getattr(self, "upd_cb", None)
        if cb is None or not cb.winfo_exists():
            return
        cb["values"] = [it["version"] + "  ·  " + (tr("running now") if it.get("current") else (tr("on the Pi") if it.get("installed") else tr("available")))
                        + (f"  ·  {it['date']}" if it.get("date") else "")
                        + (("  ·  🔏 " + tr("signed") if it.get("signed") else "  ·  ⚠ " + tr("not signed")) if it.get("available") and not it.get("installed") else "")
                        for it in UPD["items"]]
        if UPD["items"] and cb.current() < 0:
            cb.current(0)

    def _upd_check(self):
        self._status("Updates", tr("Searching …"))
        def work():
            _items, err = update_check()
            self.root.after(0, lambda: (self._upd_fill(), self._status("Updates", (("⚠ " + tr_err(err) + " · ") if err else "") + tr("Running now") + ": " + APP_VERSION
                                                                       + " · " + tr("searched at") + " " + datetime.now().strftime("%H:%M")
                                                                       + ((" · " + tr("list from") + " " + UPD["list_time"]) if UPD["list_time"] else ""))))
        threading.Thread(target=work, daemon=True).start()

    def _upd_new(self):
        from tkinter import messagebox
        v = (STATE.get("update_new") or {}).get("version")
        if not v or CFG["lock_on"]:
            return
        if not messagebox.askyesno("MoveEye", tr("Switch to version") + f" {v}?\n\n" + tr("The program restarts (about 20 seconds). Settings, recordings and zones stay."), parent=self.root):
            return
        def work():
            ok, err = update_install(v)
            if not ok:
                self.root.after(0, lambda: messagebox.showerror("MoveEye", tr_err(err), parent=self.root))
        threading.Thread(target=work, daemon=True).start()

    def _upd_install(self):
        from tkinter import messagebox
        i = self.upd_cb.current() if getattr(self, "upd_cb", None) is not None else -1
        if not 0 <= i < len(UPD["items"]):
            self._status("Updates", "⚠ " + tr("Search versions")); return
        v = UPD["items"][i]["version"]
        if not messagebox.askyesno("MoveEye", tr("Switch to version") + f" {v}?\n\n" + tr("The program restarts (about 20 seconds). Settings, recordings and zones stay."), parent=self.root):
            return
        self._status("Updates", tr("Downloading and checking …"))
        def work():
            ok, err = update_install(v)
            self.root.after(0, lambda: self._status("Updates", (tr("Switching to version") + f" {v} …") if ok else "⚠ " + tr_err(err)))
        threading.Thread(target=work, daemon=True).start()

    def _bt(self, action):
        i = self.bt_cb.current() if getattr(self, "bt_cb", None) is not None else -1
        devs = list(BT["devices"])
        if not 0 <= i < len(devs):
            self._status("Bluetooth", "⚠ " + tr("Search Bluetooth")); return
        mac = devs[i]["mac"]
        self._status("Bluetooth", tr("connecting …") if action == "connect" else "…")

        def work():
            ok, err = bt_connect(mac) if action == "connect" else bt_disconnect(mac)
            self.root.after(0, lambda: (self._status("Bluetooth", ("✓ " + tr("connected")) if ok and action == "connect" else ("" if ok else "⚠ " + tr_err(err))),
                                        self._schedule_rebuild() if ok and action == "connect" else None))
        threading.Thread(target=work, daemon=True).start()

    def _pw(self, on):
        ok, err = web_pw_set(self.pw_var.get() if on else "")
        self.pw_var.set("")
        self._status("Web password", (tr("Web password") + ": " + (tr("set") if web_pw_active() else "–")) if ok else "⚠ " + tr_err(err))

    def _export(self):
        from tkinter import filedialog
        p = filedialog.asksaveasfilename(parent=self.root, defaultextension=".json", filetypes=[("JSON", "*.json")],
                                         initialfile="moveeye_einstellungen_" + datetime.now().strftime("%Y%m%d_%H%M") + ".json")
        if p:
            try:
                with open(p, "w") as f:
                    json.dump(dict(settings_data(), app="MoveEye", version=os.path.basename(__file__)), f, indent=1)
                self._status("Power", "✓ " + p)
            except OSError as e:
                self._status("Power", f"⚠ {e}")

    def _import(self):
        from tkinter import filedialog, messagebox
        p = filedialog.askopenfilename(parent=self.root, filetypes=[("JSON", "*.json")])
        if not p or not messagebox.askyesno("MoveEye", tr("Load settings …") + "\n\n" + os.path.basename(p), parent=self.root):
            return
        try:
            with open(p) as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = None
        ok, err = import_settings(data)
        if not ok:
            self._status("Power", "⚠ " + tr_err(err))

    def _update_audio(self):
        a = STATE.get("audio") or {}
        on = a.get("level") is not None and a.get("status") == "listening"
        st = a.get("status") or ""
        txt = (tr("no microphone selected") if not a.get("mic") else
               (f"{tr('microphone on')} · {a['level']:.0f} dB" + (f" · {tr('background')} {a['bg']:.0f} dB · {tr('noise alarm from')} {a['thr']:.0f} dB"
                                                                if a.get("bg") is not None else "") if on else
                ("⚠ " + st[7:] if st.startswith("error: ") else tr("starting …"))))
        self._status("Microphone", txt)
        self._status("Clap switch", soundev_text("clap"))
        self._status("Bless you", soundev_text("sneeze"))
        self._status("Wake-up alarm", wake_text())
        self._status("Loudspeaker", (tr("no loudspeaker selected") if not a.get("spk") else (tr("playing …") if a.get("playing") else ""))
                     + (" ⚠ " + a["sound_msg"] if a.get("sound_msg") else ""))
        cb = getattr(self, "bt_cb", None)
        if cb is not None and cb.winfo_exists():
            sig = json.dumps([[d["mac"], d["connected"], d["paired"]] for d in BT["devices"]])
            if sig != self._bt_sig:
                self._bt_sig = sig
                cb["values"] = [d["name"] + (" ✓ " + tr("connected") if d["connected"] else (" (" + tr("paired") + ")" if d["paired"] else "")) for d in BT["devices"]]
                if BT["devices"] and cb.current() < 0:
                    cb.current(0)
            if BT["scanning"]:
                self._status("Bluetooth", tr("searching …"))
            elif not bt_available():
                self._status("Bluetooth", tr("bluetoothctl is missing (sudo apt install bluez)"))
        sp, dk = STATE.get("supply") or {}, STATE.get("disk") or {}
        line = []
        if sp.get("known"):
            line.append(f"{tr('Supply')}: " + (f"{sp['volt']:.2f} V · " if sp.get("volt") else "") + ("⚠ " + tr("under-voltage") if sp.get("uv_now") else "ok"))
        if dk.get("free_mb") is not None:
            line.append(f"{dk['free_mb']} MB {tr('free')}")
        if POWER["msg"]:
            self._status("Power", "⚠ " + tr_err(POWER["msg"]))
        elif line and getattr(self, "_pw_line", None) != line:
            self._pw_line = line; self._status("Power", " · ".join(line))
        if not getattr(self, "_pw_shown", False) and "Web password" in self.status_labels:
            self._pw_shown = True
            self._status("Web password", tr("Web password") + ": " + (tr("set") if web_pw_active() else "–"))
        if SETTINGS_GEN["n"] != getattr(self, "_gen", SETTINGS_GEN["n"]):
            self._gen = SETTINGS_GEN["n"]; self._schedule_rebuild()
        self._gen = SETTINGS_GEN["n"]
        c = getattr(self, "au_meter", None)
        if c is None or not c.winfo_exists():
            return
        c.delete("all")
        w = max(10, c.winfo_width()); h = max(6, c.winfo_height())
        x = lambda v: w * max(0.0, min(1.0, (v + 70.0) / 70.0))
        if on:
            lvl = a.get("peak") if a.get("peak") is not None else a["level"]
            c.create_rectangle(0, 0, x(lvl), h, fill=C["red"] if a.get("loud") else C["grn"], width=0)
            if a.get("bg") is not None:
                c.create_line(x(a["bg"]), 0, x(a["bg"]), h, fill=C["mut"], width=2)
            if a.get("thr") is not None:
                c.create_line(x(a["thr"]), 0, x(a["thr"]), h, fill=C["red"], width=3)

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

    def _simprof_ask(self):
        q_ = SIMPROF.get("q")
        if not q_:
            return
        def val(v):
            return tr("on") if v is True else tr("off") if v is False else str(v)[:30]
        lines = [f"• {tr(c['label'])}: {val(c['real'])} → {val(c['sim'])}" for c in q_["changes"][:15]]
        if len(q_["changes"]) > 15:
            lines.append(f"… (+{len(q_['changes']) - 15})")
        try:
            from tkinter import messagebox as mb_
            yes = mb_.askyesno(tr("Settings from the simulation"),
                               tr("During the simulation these settings were changed. MoveEye now uses the real settings again. Take over changes for the real camera?") + "\n\n" + "\n".join(lines))
        except Exception:
            return
        simprof_answer([c["key"] for c in q_["changes"]] if yes else [])
        self._schedule_rebuild() if hasattr(self, "_schedule_rebuild") else None

    def _sim_toggle(self, who):
        """2.97.0: simulation on / off; armed -> ask first (the real camera is not watched during the simulation)"""
        ok, err = sim_set(not CFG["sim_on"], who)
        if not ok and err == "armed":
            if messagebox.askyesno("MoveEye", tr("MoveEye is armed. The simulation replaces the real camera - nothing real is watched then. Disarm and switch the simulation on?"), parent=self.root):
                sim_set(True, who, True)

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
        if "Reference scan" in self.status_labels:
            try:
                self._status("Reference scan", refscan_status_text())
            except Exception:
                pass
        self._sync_relays()
        q_ = SIMPROF.get("q")                              # 2.95.86: back from the simulation - take over its changes?
        if q_ and getattr(self, "_simprof_t", None) != q_["t"]:
            self._simprof_t = q_["t"]
            self.root.after(200, self._simprof_ask)
        try:
            self._paint_main()
        except Exception:
            pass
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
                 (f"{tr('Patrol')}: {tr(st['patrol_status'])}" if CFG["patrol"] else tr("Patrol off"))),
                 C["yel"] if manual else (C["acc"] if (st["tracking"] or CFG["patrol"]) else None))
        self._sb("b_auto", f"{tr('Auto')}: {st['auto_status']}", C["org"])
        self._sb("b_light", tr("LOW LIGHT") if st["lowlight"] else tr("Light ok"), C["yel"] if st["lowlight"] else None)
        fps = float(st["fps"] or 0)
        self._sb("b_fps", ("💤 " if st.get("eco") == "saving" else "") + f"{fps:.0f} FPS",     # 2.95.64: real pictures per second
                 C["blu"] if st.get("eco") == "saving" else (C["grn"] if fps >= 12 else (C["yel"] if fps >= 6 else C["red"])))
        a_st = st["arm_state"]
        self._sb("b_arm", "🛡 " + protect_label(a_st, st.get("arm_left", 0)),
                 C["grn"] if a_st == "armed" else (C["yel"] if a_st == "arming" else None))
        # header: only what is not in its normal state (no rain, calm, light ok ... are not shown)
        L, hs = st.get("lights") or {}, st["hotspot"] or {}
        self._sb("b_objects", f"{st['objects']} {tr('objects')}" + (f": {summ[:40]}" if summ else ""), C["org"], show=st["objects"] > 0)
        self._sb("b_rain", tr("RAIN MODE"), C["blu"], show=st["rain_mode"])
        self._sb("b_wind", f"{tr('Wind')}: {tr(wl)}", C["yel"], show=wl not in ("calm", "off"))
        self._sb("b_rec", "● " + tr("REC"), C["red"], show=st["recording"])
        self._sb("b_relays", f"{tr('Relays')}: {on}/{len(RELAYS)} {tr('on')}", C["grn"], show=on > 0)
        self._sb("b_light", "🌙 " + tr("LOW LIGHT"), C["yel"], show=st["lowlight"])
        self._sb("b_auto", f"{tr('Auto')}: {st['auto_status']}", C["org"], show=str(st["auto_status"]).startswith("calibrat"))
        kt = kopf_text()                           # 2.98.30: automatic head movement (162): parked, quick look, saving, estimated position
        self._sb("b_patrol", tr("MANUAL") if manual else (tr("TRACKING") if st["tracking"] else (f"{tr('Patrol')}: {patrol_status_text(st['patrol_status'])}" if CFG["patrol"] or KOPF["round_on"] else "⟲ " + kt)),
                 C["yel"] if manual else C["acc"], show=bool(manual or st["tracking"] or CFG["patrol"] or KOPF["round_on"] or kt))
        self._sb("b_camp", "⛺ " + tr("Camping profile"), C["grn"], show=bool(CFG["camping"]))
        try:                                       # this window counts as a viewer while it is on the screen (not minimised)
            if self.root.state() != "iconic" and self.root.winfo_viewable():
                STATE["local_view_t"] = time.time()
        except Exception:
            pass
        vw = viewers_now()
        self._sb("b_view", f"👁 {vw['n']} {tr('viewer' if vw['n'] == 1 else 'viewers')}", None, show=vw["n"] > 0)
        self._sb("b_eco", "🍃 " + tr("power saving") + " · " + (f"{CFG['eco_fps']} FPS" if st["eco"] == "saving" else tr("awake")), C["blu"], show=st["eco"] != "off")
        m_ = re.fullmatch(r"next photo in (\d+) min", st["timelapse"] or "")
        self._sb("b_tl", "⏱ " + tr("Timelapse") + (f" · {m_.group(1)} min" if m_ else ""), C["acc"], show=bool(CFG["timelapse_on"]))
        self._sb("b_lights", " · ".join(x for x in (("💡 " + tr("White light")) if L.get("white") else "", "IR" if L.get("ir") else "") if x), C["yel"],
                 show=bool(L.get("white") or L.get("ir")))
        th_ok = st["thermal"] == "connected"
        self._sb("b_therm", "🌡 " + tr("Thermal camera") + (f" · {st['thermal_max']:.0f} °C" if th_ok and st.get("thermal_max") is not None else ("" if th_ok else " ⚠")),
                 (C["red"] if st.get("warm") else C["acc"]) if th_ok else C["yel"], show=bool(CFG["thermal_on"] or CFG["thermal_alarm"]))
        self._sb("b_hs", "📡 " + (hs.get("ssid") or tr("Own Wi-Fi (hotspot)")) + (f" · {hs.get('clients')}" if hs.get("clients") else ""), C["grn"], show=bool(hs.get("on")))
        bt = st.get("battery") or {}
        ups_mains = bt.get("src") == "ups" and not bt.get("on_battery")
        self._sb("b_batt", ("🔌 " if ups_mains else "🔋 ") + f"{bt.get('pct')} %" + (f" · {bt['hours']:.1f} h" if bt.get("hours") is not None else "")
                 + (" · " + tr("charging") if bt.get("charging") else "") + (" · 🐢 " + tr("saver") if BATT_SAVE["on"] else ""),
                 C["grn"] if ups_mains else (C["red"] if (bt.get("pct") or 0) <= 15 else (C["yel"] if (bt.get("pct") or 0) <= 30 else C["grn"])),
                 show=bool(bt.get("on") and bt.get("pct") is not None))
        un = st.get("update_new") or {}
        self._sb("b_update", "⬆ " + tr("New version") + f" {un.get('version', '')} – " + tr("click to update"), C["grn"],
                 show=bool(un.get("version")) and not CFG["lock_on"])
        self._tk_extras(st)
        if bool(CFG["lock_on"]) != getattr(self, "_lock_seen", bool(CFG["lock_on"])):
            self._lock_seen = bool(CFG["lock_on"]); self.root.after(50, self._rebuild)
        if bool(CFG["ui_simple"]) != getattr(self, "_simple_seen", bool(CFG["ui_simple"])):
            self._simple_seen = bool(CFG["ui_simple"]); self.root.after(50, self._rebuild)
        rem = st.get("remote") or []
        self._sb("b_remote", "🌐 " + tr("Remote") + ": " + ", ".join(rem)[:30], C["org"], show=bool(rem))
        if self.badges and (getattr(self, "_flow_due", True) or True):
            self._flow_due = False
            self._flow()
        if self.l_pt is not None:
            self._pos_label()
            if manual:
                txt = f"{tr('Manual control - tracking / patrol paused')} ({MANUAL['until'] - time.time():.0f} s)"
            elif st["tracking"]:
                txt = tr("Tracking person")
            else:
                txt = ""
            sv_ = servo_tk_line(self)                      # 2.98.35: Not-Aus / who steers the head (588)
            self.l_ctl_status.config(text=(sv_ + ("\n" + txt if txt else "")) if sv_ else txt, fg=C["red"] if servo_blocked() else C["yel"])
        self._qs_paint()
        ms_ = getattr(self, "mstick", None)
        if ms_ is not None:
            try:
                if MOVER["avail"] and not ms_.winfo_ismapped():
                    ms_.pack(pady=(8, 0))
                elif not MOVER["avail"] and ms_.winfo_ismapped():
                    ms_.pack_forget()
                if ms_.winfo_ismapped() and ms_.o is None:
                    ms_.draw()
            except tk.TclError:
                pass
        if self.stick is not None and self.stick.o is None:
            try:
                self.stick.draw()
            except tk.TclError:
                pass
        self._status("Camera / Servos", f"{tr('backend')}: {st['servo_backend']} · {tr('pan')} {CFG['pan']:.0f}% · {tr('tilt')} {CFG['tilt']:.0f}%"
                                        + (" · " + tr("TRACKING") if st["tracking"] else "") + (" · " + tr("MANUAL") if manual else ""))
        self._status("Video source", f"{st['source_label'] or '–'}" + (f" · {st['source_res']}" if st["source_res"] else "") + f" · {tr_status(st['source_status'])}")
        self._status("Schedule", (tr("active now") + ": " + ", ".join(st["sched_active"])) if st["sched_active"] else "–")
        e_ = STATE.get("env")
        self._sb("b_env", ("🌡 " + f"{e_['t']:.1f} °C" + (f" · {e_['h']} %" if e_.get("h") is not None else "")) if e_ else "", None, show=bool(e_))
        g_ = gps_state()
        self._status("Setup", (("📍 " + tr("Location") + f": {g_['lat']:.4f}, {g_['lon']:.4f} · " + (tr("from the phone") if g_["src"] == "phone" else tr("fixed (settings)")))
                     if g_ else ("📍 " + tr("Location") + ": " + tr("unknown"))) + "\n" + (
                     ("🌡 " + tr("Outside") + f": {e_['t']:.1f} °C" + (f" · {e_['h']} %" if e_.get("h") is not None else "") + (f" · {e_['p']:.0f} hPa" if e_.get("p") else "") + f" ({e_['src']})")
                     if e_ else "🌡 " + tr("no temperature sensor")))
        if getattr(self, "_scan_done", None) and getattr(self, "b_scan", None) is not None and self.b_scan.winfo_exists():
            self._scan_done = False; self.b_scan.config(state="normal", text=tr("Scan for cameras")); self._fill_sources()
        if st["source_id"] != getattr(self, "_src_seen", None):
            self._src_seen = st["source_id"]; self._fill_sources()
        sig = json.dumps([SCHEDULES, st["sched_active"]], sort_keys=True)
        if sig != getattr(self, "_sched_sig", sig) and not any(isinstance(w, tk.Toplevel) for w in self.root.winfo_children()):
            self._sched_sig = sig; self._schedule_rebuild()
        self._sched_sig = sig
        self._status("Patrol", f"{tr(st['patrol_status'])} · {tr('waypoints')} (↔/↕): {wp_text() or tr('none')}")
        self._status("AI detection", f"{st['ai_status']} · {st['ai_persons']} {tr('AI persons')}"
                                     + (f" · {tr('objects')}: {st['object_summary']}" if st["object_summary"] else "")
                                     + "\n" + own_ai_text())
        ts_, rem = st.get("remote_ts") or {}, st.get("remote") or []
        ts_txt = (tr("not installed") if not ts_.get("state") else
                  (tr("connected") + (f" · http://{ts_['ip']}:{CFG['web_port']}/" if ts_.get("ip") else "") if ts_["state"] == "Running" else ts_["state"]))
        pj_ = project_info()
        self._status("Web stream", f"{st['web_status']}  (http://<pi-ip>:{CFG['web_port']}/)\n🌐 Tailscale: {ts_txt} · "
                     + (f"{tr('watching now')}: {', '.join(rem)}" if rem else tr("nobody from outside"))
                     + f"\n📦 {tr('Program')}: {pj_.get('version')} · {pj_.get('file_kb', 0) / 1024:.2f} MB · {pj_.get('lines', 0)} {tr('lines')}"
                     + f" · {tr('Data')}: {pj_.get('data_mb')} MB · {tr('recordings')} {pj_.get('rec_mb')} MB ({pj_.get('rec_n')})"
                     + (f" · {tr('memory')} {pj_['ram_mb']} MB" if pj_.get("ram_mb") else ""))
        self._status("Auto-tune", f"{st['auto_status']} · {st['auto_changes']} {tr('automatic changes')}")
        self._status("Security", seclogin_text())
        self._status("Notifications", f"{tr('status')}: {st['notify_status']}")
        hs = st["hotspot"] or {}
        a_st = st["arm_state"]
        fc_ = arm_forecast_text()                      # 2.98.13: battery forecast (066)
        self._status("Camping / protection", "🛡 " + protect_label(a_st, st.get("arm_left", 0)) + (f" · 🔋 {fc_}" if fc_ else "")
                     + (" · ⛺ " + tr("Camping profile") if CFG["camping"] else "")
                     + (f" · 📡 «{hs.get('ssid')}» {hs.get('clients', 0)} {tr('devices')} · {page_address('10.42.0.1')}" if hs.get("on") else
                        f" · 📡 «{CFG['hotspot_ssid']}» / {CFG['hotspot_password'] or '–'}")
                     + (f" · {tr('Clock')}: {st['time_status']}" if st["time_status"] else "")
                     + f" · 🔁 {tr('Autostart ON') if (st['autostart'] or {}).get('on') else tr('Autostart OFF')}"
                     + (f" · {tr('power saving')}: {tr('few pictures') if st['eco'] == 'saving' else tr('full speed')}" if st["eco"] != "off" else "")
                     + (f" · {tr(st['netauto'])}" if CFG["net_mode"] == "auto" and st["netauto"] not in ("", "off") else ""))
        w = st["wifi"] or {}
        self._status("Wi-Fi / hotspot", (f"{tr('Wi-Fi')}: «{w.get('ssid') or '?'}» · {w.get('ip') or ''}" if w.get("connected") else f"{tr('Wi-Fi')}: {tr('not connected')}")
                     + (f" · {WIFI['job']}" if WIFI["job"] else ""))
        self._update_audio()
        lt = st.get("lights") or {}
        for n, sg in getattr(self, "light_segs", {}).items():
            if sg.winfo_exists():
                sg.set(CFG["light_" + n]); self.light_dots[n].config(fg=C["yel"] if lt.get(n) else C["mut"])
        self._status("Lights", (tr("night") if lt.get("dark") else tr("day")) + " · "
                     + " · ".join(f"{tr(LIGHT_NAMES[n])}: {tr('ON') if lt.get(n) else tr('off')}" + ("" if CFG[f'light_{n}_out'] else f" ({tr('not connected')})")
                                  for n in ("white", "ir")))
        self._status("Servo driver", f"{tr('backend')}: {st['servo_backend']}")
        self._status("Timelapse", tl_status_text(st["timelapse"]) + (" · " + tl_status_text(st["timelapse_render"]) if st["timelapse_render"] else ""))
        self._status("Thermal camera", tl_status_text(st["thermal"]) + (f" · {st['thermal_res']}" if st["thermal"] == "connected" and st["thermal_res"] else "")
                     + (f" · max {st['thermal_max']:.1f} °C" if st["thermal"] == "connected" and st.get("thermal_max") is not None else ""))
        if self.l_settings is not None:
            self.l_settings.config(text=f"{tr('Settings')}: {settings_status_text()} · {tr('recordings')} {st['rec_dir_mb']} MB"
                                        + (" · " + tr("LOW LIGHT") if st["lowlight"] else f" · {tr('brightness')} {st['brightness']}"))
        if self.l_cpu is not None:
            self._update_cpu()
        if getattr(self, "h_text", None) is not None:
            self._update_health()
        for key, v in self.vars.items():
            if key == self.dragging: continue
            cur = CFG[key]
            if isinstance(v, Toggle):
                v.set(cur)
            elif abs(v.get() - cur) > 1e-9:
                v.set(cur); self.value_labels[key].config(text=str(round(cur, 2)))
        if self.log is not None:
            with LOCK:
                events = [e for e in st["events"] if e.get("imp")][:150]     # only the important ones (all in the log file)
            if events and events[0] is not self._last_ev:
                self._last_ev = events[0]
                self.log.config(state="normal"); self.log.delete("1.0", "end")
                for e in events:
                    self.log.insert("end", e["t"] + "  ", "t")
                    self.log.insert("end", (LOG_ICON.get(e["kind"], "·") + " " if CFG.get("msg_icons", True) else "") + e["text"] + "\n", e["kind"])   # 2.96.4
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

    def _update_health(self):
        try:
            if not self.h_text.winfo_exists():
                self.h_text = None; return
            h = health_check()
        except tk.TclError:
            self.h_text = None; return
        sig = json.dumps(h["items"], sort_keys=True)
        if sig == self._h_sig:
            return
        self._h_sig = sig; y = self.h_text.yview()[0]
        tx = self.h_text; tx.config(state="normal"); tx.delete("1.0", "end")
        for x in h["items"]:
            tx.insert("end", "●" if x["level"] != "off" else "○", x["level"])
            tx.insert("end", "  " + x["title"], "t"); tx.insert("end", ("  " + x["text"]) if x["text"] else "", "m")
            if x["tip"] and x["level"] != "ok":
                tx.insert("end", "\n→ " + x["tip"], "tip")
            tx.insert("end", "\n")
        tx.config(state="disabled"); tx.yview_moveto(y)

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
        mm, dk = STATE.get("mem"), STATE.get("disk") or {}
        extra = (f"\nRAM {mm['used'] / 1024:.1f} / {mm['total'] / 1024:.1f} GB ({mm['pct']:.0f} %)" if mm else "") + (
            f" · {tr('Storage')}: {dk['free_mb'] / 1024:.1f} GB {tr('free')} / {dk['total_mb'] / 1024:.0f} GB" if dk.get("total_mb") else "")
        self.l_cpu_info.config(text=(f"{t:.1f} °C · " if t is not None else "") + f"{STATE['cpu_count']} {tr('cores')} · {tr('last 60 s')}" + extra)
        c = self.cpu_canvas; c.delete("all")
        w = max(10, c.winfo_width()); h = max(10, c.winfo_height()); hist = STATE["cpu_hist"]
        for g in (25, 50, 75):
            c.create_line(0, h - h * g / 100, w, h - h * g / 100, fill=C["line"])
        if len(hist) > 1:
            pts = []
            for i, v in enumerate(hist):
                pts += [w - (len(hist) - 1 - i) * (w / 59.0), h - 2 - (h - 4) * v / 100.0]
            c.create_line(*pts, fill=C["grn"] if cpu < 60 else (C["yel"] if cpu < 85 else C["red"]), width=2)

    # _feedback (feedback to the developer) and _about_win («About MoveEye»): part 584

    def _qr_window(self, first):
        """QR codes on the Pi screen: scan with the phone camera - the setup goes on there (own Wi-Fi of the Pi: first its code)."""
        import base64
        w = tk.Toplevel(self.root); w.title("MoveEye – " + tr("QR code for the phone")); w.configure(bg=C["bg"])
        tk.Label(w, text=("👋 " + tr("Welcome to MoveEye")) if first else ("📱 " + tr("QR code for the phone")), bg=C["bg"], fg=C["txt"],
                 font=("DejaVu Sans", 14, "bold")).pack(padx=16, pady=(14, 4))
        ttk.Label(w, text=tr("Scan a code with the phone camera and open the page - the setup assistant continues there (password, push messages)."),
                  style="Mut.TLabel", wraplength=520, justify="center").pack(padx=16)
        row = tk.Frame(w, bg=C["bg"]); row.pack(padx=12, pady=10)
        codes = []
        if CFG["hotspot_on"] and CFG["hotspot_password"]:
            codes.append((tr("Own Wi-Fi of the device") + ": " + CFG["hotspot_ssid"], wifi_qr_text(CFG["hotspot_ssid"], CFG["hotspot_password"])))
        for a in setup_addresses():
            codes.append(({"lan": tr("Home network"), "hotspot": tr("Own Wi-Fi of the device"), "tailscale": tr("On the road (Tailscale)")}[a["kind"]]
                          + "\n" + a["url"], a["url"]))
        if not codes:
            ttk.Label(row, text=tr("No address found (network?)"), style="Mut.TLabel").pack()
        self._qr_imgs = []
        for label, text in codes[:3]:
            f = tk.Frame(row, bg=C["bg"]); f.pack(side="left", padx=8)
            try:
                img = tk.PhotoImage(data=base64.b64encode(qr_png(text, 5)).decode()); self._qr_imgs.append(img)
                tk.Label(f, image=img, bg="#ffffff").pack()
            except Exception:
                pass
            ttk.Label(f, text=label, style="Mut.TLabel", justify="center").pack(pady=(4, 0))
        bf = ttk.Frame(w); bf.pack(fill="x", padx=16, pady=(0, 14))

        def done():
            if first:
                CFG["setup_done"] = True; save_settings()
            w.destroy()
        ttk.Button(bf, text=tr("Close"), command=done).pack(side="right")
        w.protocol("WM_DELETE_WINDOW", done)

    def run(self):
        if not CFG["setup_done"] and not CFG["lock_on"]:
            self.root.after(1500, self._g2_first)            # the one guide (584); the QR codes come at its end
        self.root.mainloop()



