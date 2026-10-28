#@ Motion Watch – Teil 020: CFG: alle Einstellungen mit Standardwerten. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
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
    "loop_on": False, "loop_hours": 24, "loop_fps": 4,    # continuous recording: on, keep N hours, pictures per second
    "ext_on": False, "ext_token": "", "rtsp_on": False, "rtsp_port": 8554,   # picture for other programs
    "storage_path": "",                      # recordings on this drive (mount point); empty = next to the program
    "record": True, "record_dir": "recordings", "record_tail": 3.0,
    "record_max_gb": 2.0,        # oldest recordings are deleted above this size
    "snapshot_on_person": True,  # save a JPG the moment a person is detected
    "rec_marks": "thin",         # markings in recordings / alarm pictures: none | thin (corner brackets, face stays free) | full
    # low light
    "lowlight_auto": True, "lowlight_threshold": 60,   # mean brightness (0-255) below which CLAHE is applied
    "lowlight_view": True,       # in low light also brighten the picture you see (live, recordings, photos)
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
    "cam_rotate": "0", "cam_mirror": False,       # picture turned (0/90/180/270 clockwise) and mirrored, right after the camera
    "track_person": True,        # keep the detected person centred
    "qs_layout": {"order": [], "hidden": []},   # quick switches below the joystick: own order, hidden ones (empty = all)
    "track_motion": False,       # also follow animals and other movement when no person is in the picture
    "track_motion_min": 0.08,    # ... at least this big (% of the picture)
    "track_motion_hold": 2.0,    # ... and moving for at least this many seconds (swaying branches stay in place)
    "track_gain": 0.6,           # how aggressively the camera follows
    "track_deadzone": 0.08,      # fraction of the frame treated as "centred"
    # patrol
    "patrol": False, "patrol_mode": "pendulum", "patrol_dwell": 2.0, "patrol_speed": 30.0,   # %/second
    "patrol_tilt": 50.0,
    # manual camera control (pad / arrow keys / web) pauses tracking + patrol for this many seconds
    "manual_hold": 5.0,
    # appearance
    "theme": "dark", "lang": "en", "fullscreen": False,
    "tv_key": "", "tv_auto": True,   # 2.95.51: TV view on the HDMI of the Pi (and for any other screen with the link)
    "tunnel_on": True, "tunnel_code": "", "tunnel_prev_url": "",                       # 2.95.54: the simulator connects out to the Pi (firewall without admin)
    "helper_use": True, "helper_url": "", "helper_code": "",   # 2.95.53: let a PC do the AI (address + pairing code; empty = found by itself)
    "helper_serve": False, "helper_my_code": "",                # 2.95.53: this MoveEye works as AI helper for others (port 5057)
    "info_page": True, "info_mail": "",   # 2.95.52: the product page for guests in the same Wi-Fi (/info/), own e-mail address on it
    "app_icon": "moveeye", "app_icon_orange_done": False, "app_icon_moveeye_done": False,         # the app icon (2.95.23): radar | radar2 | cross | trail | rings4 | waves | classic (+ 2.95.46: light, night, forest, thermal, fov, camp, shield, hits)
    "app_icon_anim": True,       # 2.95.25: the radar sweep turns in the page header
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
    "latitude": 47.37, "longitude": 8.54,   # for sunrise / sunset schedules (the phone keeps it up to date when gps_phone is on)
    "gps_phone": True, "gps_tag": True,
    "map_online": True,                      # recordings map: map tiles and place names from OpenStreetMap (the area is sent there)
    "weather_on": False,                     # day overview: weather from the internet (Open-Meteo, the location is sent there)
    "env_on": True, "env_offset": 0.0,       # temperature / humidity sensor (BME280 / BMP280 on I2C, DS18B20 on 1-Wire GPIO 4), correction      # location from the phone (https page) / GPS data in photos and videos
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
    "nightvision": False, "nightvision_auto": False,     # night vision look: green picture, thermal outlines and °C written over it
    "thermal_on": False, "thermal_source": "", "thermal_alpha": 0.5, "thermal_map": "inferno",
    "thermal_hot": False, "thermal_hot_pct": 80.0,          # hot mode: only the warmest N percent are shown
    # pre-alarm push: a short message (small picture) to the phone at the first movement, before a person is confirmed
    "notify_prealarm": False, "prealarm_cooldown": 120.0, "prealarm_photo": True,
    "browser_alarm": True,       # open web pages get pre-alarm / person alarms live (sound in the browser)
    # layout: which cards are open / closed, hidden fields, theme, language, stick or buttons ... (web and desktop window)
    "web_ui": {}, "ui_open": ["grp:alarm"],
    "notify_remote": False,      # push message when somebody opens the page from outside (Tailscale)
    "report_on": True, "report_hour": 7, "report_from": 20, "report_last_day": "",   # night report (push in the morning)
    "diary_on": True, "diary_keep_days": 90,      # note animals / persons / noises (animal diary + night report)
    "guest_token": "", "guest_until": 0.0,        # guest access: link /g/<token>, 0 = no time limit
    "ups_on": True, "ups_addr": "0x42", "ups_mah": 3450,   # Waveshare UPS HAT (INA219, 2 x 18650 in series): mAh of ONE cell
    "ups_model": "auto",         # auto | e (UPS HAT (E), I2C 0x2D) | ina (UPS HAT A/B/C with INA219)
    "ups_shutdown_pct": 8, "ups_push": True, "ups_invert": False,
    "batt_mah": 0, "batt_extra_w": 1.5, "batt_used_wh": 0.0, "batt_full_t": 0.0, "batt_warned": False,   # powerbank estimate
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
    # own texts of the push messages (empty = standard text); placeholders {name} {time} {date} {count} {camera} {link}
    "device_name": "", "msg_person_title": "", "msg_person_text": "", "msg_prealarm_title": "", "msg_prealarm_text": "",
    "msg_warm_title": "", "msg_warm_text": "",
    # audio: microphone ("" = none, "default", "plughw:CARD=<name>,DEV=<n>") and loudspeaker of the Pi
    "audio_in": "", "audio_out": "", "audio_gain": 0, "audio_record": True,
    "noise_alarm": False, "noise_push": True, "noise_threshold": 20, "noise_min": 0.3,
    "siren_on": "off", "siren_sound": "siren", "siren_seconds": 10, "siren_volume": 80, "siren_pause": 60,
    "talk_gain": 6,              # talking from the phone through the loudspeaker of the Pi: boost in dB
    "https_extra": True,         # also a secure page (https, port + 1): phones only allow their microphone there
    # servo driver: auto = PCA9685 if found, else GPIO 17 / 27 | pca9685 | gpio; limits in degrees from the middle
    "servo_driver": "auto", "pca_address": "0x41", "pca_pan_ch": 0, "pca_tilt_ch": 1,
    "pan_limit": 90, "tilt_limit": 60, "servo_range": 180,
    "pan_servo_range": 180,      # turning range of the pan servo in degrees (180 / 270 / 360): the pan limit can go up to half of it
    # lights (white + infrared): off | on | auto, where they are connected, what "auto" means, how long after an alarm
    "light_white": "off", "light_ir": "off", "light_white_out": "", "light_ir_out": "",
    "light_white_auto": "alarm_dark", "light_ir_auto": "dark", "light_hold": 60,
    "picture_mode": "color",     # color | night_grey | grey  (NoIR camera: natural grey picture at night)
    "temp_warn": 80,             # push message when the CPU gets hotter than this (degrees C)
    "thermal_zoom": 100, "thermal_dx": 0, "thermal_dy": 0,   # which part of the thermal picture the camera sees
    # power saving: few pictures per second while all is quiet; any movement / noise / alarm = full speed for eco_wake s
    "eco_on": False, "eco_fps": 3, "eco_wake": 30, "eco_view_full": True,
    "mode": "", "mode_prev": {}, "mode_since": 0.0,   # 2.95.47: one switch for the whole device (camping, campfire, gamer ...)
    "mode_fire_until": "23:00", "mode_fire_min_pct": 30, "mode_gamer_watch": False, "mode_fire_hours": 4.0,
    "turbo_on": False, "turbo_prev": {},   # power mode (2.95.19): everything on the highest performance, the values before are kept
    "users": [],                 # extra logins: [{"name", "hash", "role": "operate" | "view"}] (the web password = administrator)
    "trusted": [],               # trusted devices (2.95.19): [{"h": sha256 of the cookie, "user", "name", "t0", "seen", "ip"}] - no login after updates
    "web_pw_hash": "",           # web password set on the page / in the window (only a salted hash is stored)
    "disk_warn_mb": 500,         # push message when less space is free on the memory card
    "setup_done": False,
    "webpush_on": True,
    # Pushover (2.95.26): an extra way for alarms; «emergency» = priority 2: on an iPhone a critical alert (rings also when muted,
    # if «Critical Alerts» is on in the Pushover app), repeated every minute until it is acknowledged
    "pushover_on": False, "pushover_user": "", "pushover_token": "", "pushover_emergency": True,
    # 2.95.27: a keyword at the start of every message (MW-ALARM, MW-WAERME ...): an iPhone shortcut automation reacts to it
    "msg_keyword_on": True, "msg_keyword_prefix": "MW",
    # e-mail as a way for messages (the iPhone «E-Mail» automation can start a shortcut)
    "email_on": False, "email_to": "", "email_host": "", "email_port": "587", "email_user": "", "email_password": "", "email_from": "",
    "email_events": "alarms",       # alarms | all
    # shortcut key (2.95.27): /k/<key>/<action> works without the password, only for a few actions (arm, siren off, light ...)
    "shortcut_token": "",
    # 2.95.28: a short test run every night (when the simulator runs), message only when it gets clearly worse
    "testopt_nightly": False, "testopt_hour": 3, "testopt_plan": "quick",
    "deter_person_act": "off", "deter_person_sound": "two-tone",
    "deter_big_act": "both", "deter_big_sound": "bangs",
    "deter_small_act": "off", "deter_small_sound": "whistle",
    "deter_warm_act": "off", "deter_warm_sound": "beeps",
    "deter_seconds": 6, "deter_pause": 60, "deter_always": False,
    "share_logo": True,
    "ui_simple": True,                       # settings: only the important ones (Expert shows everything)
    "share_gps": False,                      # shared pictures / videos keep their GPS position (off: removed before sharing)
    "fleet": [],
    "sms_on": False, "sms_numbers": "", "sms_mode": "auto", "sms_port": "/dev/ttyUSB2", "sms_hilink": "192.168.8.1",
    "sms_only_offline": True, "sms_pause": 5, "sms_day_max": 20,          # SMS over an LTE stick
    "mqtt_on": False, "mqtt_host": "", "mqtt_port": "1883", "mqtt_user": "", "mqtt_password": "", "mqtt_tls": False,
    "mqtt_prefix": "motionwatch", "mqtt_discovery": True,   # MQTT / Home Assistant                 # other MoveEye devices in the overview: [{id, url, name, pw}]          # shared pictures / videos get a small MoveEye logo strip
    "gpsmod_on": False, "gpsmod_port": "auto", "gps_theft": True, "gps_theft_m": 150,
    # mover: tracked vehicle under MoveEye (from 2.94.0) - found by itself, second stick on the page and in the window
    "mover_mode": "auto", "mover_driver": "adafruit", "mover_addr": "0x60", "mover_speed": 70, "mover_turn": 50, "mover_ramp": 0.5,
    "mover_inv_l": False, "mover_inv_r": False, "mover_swap": False, "mover_sim_show": True,
    "storm_on": True, "storm_drop": 3.0, "storm_wind": 50, "storm_forecast": False, "wind_gpio": "", "wind_factor": 2.4,
    "solar_on": False, "solar_addr": "0x41", "solar_shunt": 0.1, "night_warn": True,
    "species_on": False, "species_model": "", "species_norm": "imagenet", "species_size": 224, "species_conf": 0.5,
    "desktop_notice": True,
    "sim_on": False, "sim_url": "http://127.0.0.1:8765", "sim_eco": True, "sim_fps": 6, "sim_auto": True,
    "sim_autostart": True, "sim_autostart_v2": False,   # v2 (2.95.26): on a Raspberry Pi off by default (it guards the real place)
    # 2.95.25: a simulator announces itself -> the simulation goes on by itself (and off again when it is gone)
    "sim_auto_on": False,        # ... it was switched on by that (only then it is switched off again by itself)
    "sim_autoupd": True, "sim_separate": True, "net_watch": False, "net_known": {}, "presence_macs": [], "presence_auto": False, "presence_gone_min": 10.0,
    "bt_tracker_warn": False, "bt_tracker_min": 30.0, "presence_bt": [], "wifi_dual": True, "wifi_repeater": False, "clap_on": False, "clap_sens": 5, "clap_beep": True, "clap_volume": 60, "clap_2": "relay:0",
    "clap_3": "light_white", "clap_4": "none", "clap_disarmed": True, "clap_practice": False, "sneeze_on": False, "sneeze_sens": 5,
    "sneeze_volume": 70, "sneeze_reply": "tts", "sneeze_texts": "Gesundheit!|Gsundheit!|Zum Wohl!", "sneeze_night": True, "wifi_swap": False, "wifi_guard": False,
    "wifi_guard_thr": 20, "wifi_count": False, "wifi_presence": False, "net_noinet": [], "net_inet_notify": True, "sim_prev_source": "", "sim_prev_thermal": "",
    "lens_check": True, "temp_alarm_on": False, "temp_hot": 30, "temp_cold": 3,
    "sens_on": False, "sensors": [], "rf433_on": False, "zigbee_on": False, "ble_on": False, "tag_missing": 5, "eco_pir": True,
    "refscan_pan_steps": 6, "refscan_pan_from": 10, "refscan_pan_to": 90, "refscan_tilt_steps": 1, "refscan_tilt_span": 16, "refscan_tilt_mid": 50,
    "refscan_photos": 2, "refscan_settle": 1.5, "refscan_sens": 50, "refscan_min_area": 0.6,   # reference scan (2.95.97)
    "refscan_on_arm": False, "refscan_every": 0, "refscan_push": True, "refscan_push_all": False, "refscan_pano_on": False, "refscan_pano_day": "",
    "protect_level": "off", "protect_pin": "", "escalate_on": False, "escalate_siren_s": 30,   # 2.95.105: protection (135)
    "tamper_on": True,           # sabotage: camera covered or turned away (picture check)
    "tamper_motion": True,       # motion sensor MPU-6050 (I2C 0x68), if fitted: device moved / knocked over
    "tamper_power": True,        # power cut while armed = alarm (needs the UPS HAT)
    "tamper_tilt": 12.0,         # degrees
    "backup_type": "off",        # copy finished alarm recordings: off | webdav | folder | telegram
    "backup_url": "", "backup_user": "", "backup_password": "", "backup_folder": "",
    "backup_all": False,         # copy every recording (otherwise only alarm recordings: armed or with a person)          # alarm messages also as web push to browsers that switched it on (no extra app)         # first start: the setup assistant shows on the web page (and the QR code in the window)
    "update_unsigned": False,    # also install versions without a valid signature (own builds) - not recommended
    "update_url": "",            # where new versions come from: https://.../versions.json or a folder (USB stick)
    "update_auto": True,         # look for a new version every 3 hours (and 2 minutes after the start)
    "update_install": False,     # install a new version by itself ...
    "update_fast": False, "dev_phase_done": False, "news_popup": True, "msg_icons": True, "news_seen_web": "", "news_seen_tk": "",   # 2.96.3: «Neu in dieser Version»
           # 2.95.71: test mode - look on GitHub every minute, install a new version at once
    "update_hour": 12,           # ... in this hour of the day
    "update_install_armed": False,   # ... also while armed (otherwise only when disarmed)
    "update_push": True,         # push message when a new version is there (once per version)
    "update_notified": "",
    "update_token": "",          # GitHub key (read-only token) for a private repository - only ever sent to GitHub
    "log_status_min": 15,        # a status line in the log every N minutes (0 = off)
    "log_keep_days": 60,         # how long the daily log files are kept in the archive
    "lock_on": False, "lock_pin": "", "lock_snap": {},   # operator mode: settings locked, unlock with the PIN (stored as a hash)
    "msg_noise_title": "", "msg_noise_text": "",
}

STATE = {
    "rain_score": 0.0, "rain_mode": False,
    "wind_score": 0.0, "wind_level": "calm", "wind_boost": 1.0,
    "persons": 0, "candidates": 0, "recording": False,
    "fps": 0.0, "events": [], "frames": 0, "uptime": 0,
    "ignored_vehicles": 0, "detections_total": 0,
    "auto_status": "idle", "auto_changes": 0,
    "ai_status": "off", "ai_persons": 0, "ai_ms": 0, "shadow_pct": 0,
    "servo_backend": "–", "relay": False, "patrol_status": "off", "tracking": False, "track_what": "",
    "web_status": "off",
    "objects": 0, "object_summary": "",
    "cpu": 0.0, "cpu_temp": None, "cpu_hist": [], "cpu_count": 1,
    "lowlight": False, "brightness": 0, "rec_dir_mb": 0, "notify_status": "off", "backup_status": "", "web_viewers": 0,
    "remote": [], "remote_ts": {"state": "", "ip": "", "name": ""}, "report_last": {}, "battery": {"on": False}, "update_new": {},
    "settings_status": "defaults",
    "relay_states": [], "relay_out": [], "present": [], "manual": False,
    "source_id": "", "source_label": "", "source_status": "starting", "source_res": "", "rec_name": "",
    "sched_active": [], "sched_active_idx": [], "sched_forced": {}, "sched_manual": [],
    "presence": "unknown", "web_open": False, "extra": [], "recording_enc": "",
    "timelapse": "off", "timelapse_last": "", "timelapse_render": "", "thermal": "off", "thermal_res": "",
    "wifi": None, "net": {"online": None, "ms": None}, "wifi_hist": [],
    "arm_state": "armed", "arm_left": 0, "hotspot": {"on": False, "ssid": "", "clients": 0, "ip": "", "busy": False, "available": False, "msg": ""},
    "time_status": "", "warm": 0, "autostart": {"on": False, "mode": "", "msg": "", "path": ""}, "netauto": "off",
    "audio": {"status": "off", "level": None, "mic": False, "spk": False, "playing": False, "listeners": 0}, "power": "",
    "https_port": None, "lights": {"white": False, "ir": False, "dark": False}, "thermal_max": None, "eco": "off",
    "supply": {"volt": None, "uv_now": False, "uv_boot": False, "throttled": False, "known": False},
    "disk": {"free_mb": None, "total_mb": None},
}
DEFAULTS = dict(CFG)
WAYPOINTS = []          # [pan, tilt] positions in percent


def wp_text():
    """Waypoints as short text: 24/60, 79/55 ... (pan/tilt in %)."""
    return ", ".join(f"{w[0]:.0f}/{w[1]:.0f}" for w in WAYPOINTS)


def wp_add():
    WAYPOINTS.append([round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1)])
START = time.time()
LOCK = threading.Lock()
GPIO_PAN, GPIO_TILT, GPIO_RELAY = 17, 27, 22
GPIO_RESERVED = (GPIO_PAN, GPIO_TILT) + ((4,) if os.path.isdir("/sys/bus/w1/devices/w1_bus_master1") else ())   # servo pins / 1-Wire never as relays
MAX_RELAYS = 8
FREE_GPIOS = (23, 24, 25, 5, 6, 12, 13, 16, 26, 4, 22, 18, 19, 20, 21)


def default_relays():
    """Relay 1 = the original alarm relay on GPIO 22 (switches while a person is detected)."""
    return [{"name": "Relay 1", "gpio": GPIO_RELAY, "mode": "auto", "trigger": "person", "hold": 5.0, "active_low": False}]


RELAYS = default_relays()          # edited in the desktop window and on the web page, saved in the settings file
QUICK = {"rec_until": 0.0}          # quick switches on the live page: manual recording until (time), at most 10 minutes


def quick_rec():
    """Quick switch «Record»: manual recording on (max. 10 min) / off. Returns True while recording."""
    if CFG.get("sim_on"):
        log_event("rec", "Simulation: no recordings"); QUICK["rec_until"] = 0.0; return False
    if time.time() < QUICK["rec_until"]:
        QUICK["rec_until"] = 0.0; log_event("rec", "Manual recording stopped"); return False
    QUICK["rec_until"] = time.time() + 600; log_event("rec", "Manual recording started (max. 10 min)"); return True


def quick_photo(frame):
    """Quick switch «Photo»: the current picture into the recordings. Returns the file name (None: no picture yet)."""
    if frame is None or CFG.get("sim_on"):
        return None                                        # simulation: nothing goes into the recordings
    os.makedirs(CFG["record_dir"], exist_ok=True)
    name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(os.path.join(CFG["record_dir"], name), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    gps_tag_jpg(os.path.join(CFG["record_dir"], name))
    log_event("rec", f"Photo saved: {name}")
    return name


def patrol_status_text(st, lang=None):
    """«moving to waypoint 2/4 (88/82)» -> «fährt zu Wegpunkt 2/4 (88/82)» ..."""
    m = re.fullmatch(r"moving to waypoint (\d+)/(\d+) \((.+)\)", st or "")
    if m:
        return tr("moving to waypoint", lang) + f" {m.group(1)}/{m.group(2)} ({m.group(3)})"
    m = re.fullmatch(r"dwelling at (.+)", st or "")
    if m:
        return tr("waiting at", lang) + " " + m.group(1)
    return tr(st or "", lang)


def quick_patrol(source="web"):
    """One patrol button: off -> back and forth -> round trip -> off."""
    if not CFG["patrol"]:
        CFG["patrol"], CFG["patrol_mode"] = True, "pendulum"
    elif CFG["patrol_mode"] == "pendulum":
        CFG["patrol_mode"] = "loop"
    else:
        CFG["patrol"] = False
    save_settings()
    log_event("patrol", ("Patrol ON: " + ("round trip 1-2-3-1" if CFG["patrol_mode"] == "loop" else "back and forth 1-2-3-2-1"))
              if CFG["patrol"] else f"Patrol switched OFF ({source})")
    return CFG["patrol"], CFG["patrol_mode"]
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
    try:
        protect_on_alert(kind)                         # 2.95.105: escalation (light, then the siren unless disarmed)
    except NameError:
        pass
    if not CFG.get("browser_alarm", True):
        return
    if kind in ("person", "prealarm", "warm", "noise") and not is_armed():
        return
    with ALERTS_COND:
        ALERTS["seq"] += 1
        ALERTS["items"].append(dict(seq=ALERTS["seq"], kind=kind, text=text, time=datetime.now().strftime("%H:%M:%S"), ts=time.time(), **extra))
        ALERTS_COND.notify_all()


_LOGDAY = {"d": ""}
# what the overview shows ("important"): alarms, persons, animals, arming, problems, remote access, restarts ...
# everything else (auto-tune, camera moves, status lines, patrol, weather, AI details ...) is only in the full log / archive
_IMP = {
    "person": re.compile(r"^(?!Person counter reset)"),
    "rec": re.compile(r"^(Recording started|Recording failed|Sound recording failed|Diary: [a-z ]+ \()"),
    "sys": re.compile(r"Armed now|Armed in|Disarmed|UNDER-VOLTAGE|CPU hot|Memory card almost full|Battery almost empty|"
                      r"Camera stopped|not available|could not|failed|Camping profile|Operator mode|wrong PIN|paused for|"
                      r"Pause over|Pause ended|Switching to version|Version .* downloaded|Autostart:|Internet not reachable|"
                      r"Internet reachable again|Wi-Fi signal weak|Settings reset|Settings imported|Shutting down|Restarting the Pi|"
                      r"Talking through|Own Wi-Fi .* switched ON|Network automatic: connected|Power cut|Mains power back|UPS HAT found|Battery empty|Automatic update|runs fine \(update|did not start 3 times|SABOTAGE|Motion sensor found|Device .* not reachable|Device added"),
    "web": re.compile(r"Remote access from|Login blocked|Notification failed|Guest access|WARNING|NOT started|Web password|MQTT connected|MQTT: |SMS "),
    "sched": re.compile(r"Schedule started|Schedule ended|Presence"),
}


def log_important(kind, text):
    rx = _IMP.get(kind)
    return bool(rx and rx.search(text or ""))


def log_event(kind, text):
    today = datetime.now().strftime("%Y-%m-%d")
    if _LOGDAY["d"] != today:                             # first line of a new day: archive the old day's log first
        _LOGDAY["d"] = today
        try:
            log_rotate()
        except Exception:
            pass
    with LOCK:
        STATE["events"].insert(0, {"t": datetime.now().strftime("%H:%M:%S"), "kind": kind, "text": text,
                                   "imp": log_important(kind, text)})
        del STATE["events"][300:]
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  [{kind}]  {text}\n")
    except OSError:
        pass


