#@ Motion Watch – Teil 000: Kopf: Beschreibung und die Liste aller Änderungen (neueste oben). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
#!/usr/bin/env python3
"""
MoveEye 1.4.0  -  Webcam motion / person detection with weather awareness,
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
    when the Pi joins a network. Without root once:  sudo python3 webcam_bewegung_2_98_65.py --allow-wifi
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
  * 1.7.1: AUTOSTART switch: on = at boot MoveEye starts by itself (systemd, no screen needed) and switches the own
    Wi-Fi on; off = nothing starts at boot and the Pi joins its known networks
  * 1.7.2: NETWORK AUTOMATIC: known networks first (phone hotspot = internet + push), otherwise the own Wi-Fi; when the
    phone hotspot disappears the own Wi-Fi comes on, and every 10 min (only if no device is connected) it looks again
  * 1.7.3: web page: the 26 menus are now 8 groups (Alarm & camping, Notifications, Detection, Camera & servos,
    Recordings & timelapse, Thermal camera, Relays & schedule, System & network); fine tuning under "Advanced"; more compact
  * 1.7.4: the desktop window uses the same 8 groups as the web page
  * 1.7.5: own texts for the push messages (title + text for person, pre-alarm, thermal alarm, device name) with placeholders
    {name} {time} {date} {count} {camera} {link}; umlauts / emoji work with ntfy (RFC 2047)
  * 1.7.6: POWER: shut down / restart the Pi from the page and the window (recording is finished first, settings saved).
    AUDIO: choose microphone + loudspeaker; noise alarm (louder than the background, push + browser + relay trigger
    "noise" + recording), live listening in the browser, sound in the recordings, siren / own sounds on the Pi at an alarm
  * 1.7.7: TALK from the phone through the loudspeaker of the Pi (hold the button); a second, secure page (https, port + 1)
    starts by itself, because phones only allow their microphone on https pages
  * 1.8.0: hardware of the 3D-printed pan/tilt head: servos on a PCA9685 (I2C, address selectable, no jitter on the Pi 5),
    pan / tilt limits in degrees; LIGHTS white + infrared (PCA9685 channel or GPIO, Off / On / Auto: at an alarm or the whole
    night by sunset); grey picture at night (NoIR camera); Waveshare Thermal-90 (SPI, pysenxor) as thermal camera with zoom /
    shift to match the camera picture; the noise alarm ignores the servo motors; push message when the Pi gets too hot
  * 1.8.1: POWER SAVING mode: while all is quiet only a few pictures per second (camera itself slower), full speed at once at
    any movement, noise, alarm, recording, manual control or while somebody watches; part of the camping profile, schedulable
  * 1.8.2: under-voltage warning (power bank / cable, Pi 5 shows the input voltage); memory card: free space shown, push message
    and the oldest recordings are deleted when it gets full; watchdog (autostart restarts a hanging program, --allow-wifi switches
    the hardware watchdog on); settings export / import; web password can be set on the page / in the window (asked at the
    first visit, stored as a hash)
  * 1.8.3: settings tidied up: 9 groups (new: "Light & sound"), inside a group every topic opens / closes the same way (the
    first one is open), fine-tuning at the end under its own line, power saving has its own topic; web page and window alike
  * 1.8.4: BLUETOOTH loudspeaker: search, pair + connect from the page / window, used for siren, test sound and talking;
    reconnects by itself when the speaker comes back
  * 1.8.5: started by hand while the autostart copy (maybe an older version) runs: the copy is stopped and this program takes
    over its web page (before, the page silently stayed the old one); the version is shown on the page; pages are never cached
  * 1.8.6: Bluetooth loudspeaker also on the "Cameras" page (search, connect, test sound); the version stands next to the name
    at the top left (all pages and the window)
  * 1.8.7: UPDATES: choose a version (newer or older) and switch with one tap; source = versions.json on the internet (e.g. GitHub)
    or a folder (USB stick); checked before it starts (checksum, Python, version); older versions stay for going back
  * 1.8.8: header tidied up: status first (armed, persons, recording), then what is switched on (camping, power saving,
    timelapse, lights, thermal camera, patrol, own Wi-Fi, schedule, relays, microphone), then warnings, then CPU / FPS;
    things in their normal state (no rain, calm wind, light ok, source connected ...) are not shown any more
  * 1.8.9: MANUAL on the web page (tab "Manual", /help): quick start, all functions, tips & tricks, troubleshooting, setup;
    search, table of contents, printable, German / English; button "Manual" in the desktop window
  * 1.9.0: first version on GitHub (updates from github.com/<user>/motionwatch); older program files are recognised by their
    real version number in the update list
  * 1.9.1: a failed camera switch (the old camera keeps running) shows a yellow "switch failed" note for one minute
    instead of a red badge that stayed until restart; red only when no camera works at all
  * 1.9.2: web full screen button works on phones: the video fills the screen (real full screen on Android / PC,
    page layout on iPhone / iPad where browsers allow no full screen), round ✕ button top right to go back
  * 1.9.3: remote access (Tailscale): header badge "🌐 Remote: <device>" while somebody watches from outside, Tailscale
    status + address under System, log entries, optional push message, new relay trigger "remote access" (also when
    disarmed) e.g. for a small warning lamp
  * 1.9.4: web full screen: the buttons "expand all / collapse all" are hidden (phone held sideways)
  * 1.9.5: live picture reconnects by itself when the phone loses the stream (no more "?" icon, spinning ↻ meanwhile),
    also when coming back to the browser; phone full screen upright: stick right under the picture
  * 1.9.6: phone: direction buttons centred like the stick; German texts in Swiss spelling (ss instead of sharp s)
  * 2.0.0: animal diary (tab "Diary": best picture of every animal visit, filter, favourites, share), night report (push in
    the morning with what happened at night + best picture), privacy zones (painted black right after the camera, also in
    recordings / for guests), guest access (view-only link /g/<key>, time limit, can be ended at once), app icon for the
    phone home screen (manifest, icons), powerbank runtime estimate (capacity, "battery full", header badge, warning at 15 %)
  * 2.0.1: web: search box above the settings - typing hides every group / section / field without the words (German or
    English), matches are framed and opened; ✕ / Esc shows everything again
  * 2.0.2: pause the program (System & network -> System, window: Setup): switches off at once (recording finished,
    settings saved) and starts again by itself after 5 min ... 12 h; meanwhile a small page with countdown and "Start now"
    (same process: autostart and watchdog keep working)
  * 2.0.3: app mode (home screen icon): reload button ⟳ in the header; every page shows "New version running - Reload"
    after an update
  * 2.0.4: home screen icon depends on the address: green "MW Intern" (home network / hotspot), red "MW Extern"
    (Tailscale 100.x / *.ts.net) - two shortcuts can be told apart
  * 2.0.5: internet check also over normal web traffic (port 443, first the push server itself) - no more false
    "no internet" when a router blocks port 53 to outside servers
  * 2.0.6: tablet / computer (wider than 960 px): settings column and picture column scroll separately - the live picture
    always stays in view
  * 2.0.7: recordings page: timelapse videos appear in the list (marked ⏱), new type filter "Timelapse" shows the videos and
    all single photos; play, download, star (starred photos are kept), delete, ZIP work as for recordings
  * 2.0.8: updates from a private GitHub repository: new secret field "GitHub key (token)" (read-only token; only sent to
    GitHub addresses, never shown or logged); clear hint when the repository is private and no key is set
  * 2.0.9: in low light the visible picture is brightened too (gamma curve, adapts to the darkness; switch under
    Detection -> Low light) - before, a dark scene looked black while the detection still marked movements;
    autostart more robust after a power cut: restarts after any exit and never gives up (Restart=always,
    StartLimitIntervalSec=0), start without login (linger) is checked at every start and switched on or explained
  * 2.0.10: small 🎧 button next to the stick / buttons (row "Control") switches listening to the microphone on and off;
    green and pulsing while listening
  * 2.1.0: operator mode (System -> "Operator mode (lock settings)", window: Setup): settings locked with a PIN (4-8 digits,
    hash); the operator can still arm / disarm, use the camping profile, the main switches (detection, recording,
    notifications, power saving, patrol, timelapse ...), lights, camera, listen / talk, recordings; the web server refuses
    everything else (HTTP 423), the window shows only the operator panel; 5 wrong PINs = 5 minutes pause
  * 2.1.1: event log: status line every 15 min (CPU, temperature, FPS, camera, Wi-Fi, internet, memory, voltage, battery),
    daily archive (logs/motionwatch_YYYY-MM-DD.log.gz, kept 60 days, also when a file grows over 20 MB), new page /log
    ("Whole log & archive": filter by kind, search, 300 / 1000 / 5000 lines, download every day); the card shows 40 entries
  * 2.1.2: phone: the page could become wider than the screen (zoomed out, header only half as wide) when a list held a
    long entry - now every list / field / log line stays inside the screen width
  * 2.1.3: the event log card shows only the important entries (alarms, persons, animals, recordings, arming, problems,
    remote access, restarts ...) with small icons; the log page has the filter "Important only"; everything stays in the file
  * 2.1.4: updates: always the newest version list (GitHub's file server kept an old copy for up to 5 minutes), the list
    shows when it was searched and from when the list is; versions with date and time
  * 2.1.5: event log card: at least 10 lines (important ones, filled up pale with the newest others), also right after a
    restart (taken from the log file); log page: "← Back to the live picture"; automatic update check (2 min after the
    start, then every 3 hours): bar "New version … – Update now" on the page, badge in the window, one push message
  * 2.2.0: Waveshare UPS HAT (INA219 on I2C 0x42, 2 x 18650 in series): found by itself, battery % from the cell voltage,
    time left from the measured power, mains / battery / charging in the header, push + log at a power cut and when the
    power is back, warning at 20 %, clean shutdown at 8 % (adjustable); powerbank estimate stays for devices without UPS
  * 2.2.1: compact header: armed / disarmed big (red and pulsing at an alarm), values in their normal range (no person, CPU,
    FPS, Wi-Fi, microphone ...) behind one "✓ all ok" chip (tap = show them), short symbols (⏱ 4′, 🌙, 🍃 …), theme /
    language / settings panel / hide header moved into the ☰ menu, header shrinks to one line when scrolling down
  * 2.2.2: statistics tiles under the picture (FPS, persons now, objects, detections) and the object list removed - web
    page and window (the values are still in the header and the event log)
  * 2.2.3: automatic update (Updates: "Install new versions automatically", hour, also when armed): installs the newest
    version in the chosen hour when nothing is going on, push before; start guard: a new version that does not start
    3 times is replaced by the previous one again
  * 2.2.4: update list shows only about three versions, the rest scrolls (web page and window).
  * 2.2.5: tidier header on tablet/PC: status badges on the right next to the buttons (separated by a line), all header
    buttons the same size with drawn icons (bell, reload, menu, full screen) instead of characters, equal heights.
  * 2.2.6: tablet/PC header: status badges in their own line below the tabs, title/tabs/buttons no longer jump.
  * 2.2.7: header no longer flickers: badges are shortened in the same step as they are filled (before, the long texts
    showed for a moment and the line wrapped); on tablet/PC the badge line never wraps (scrolls sideways if ever too long).
  * 2.2.8: no more zooming in when a text field is tapped on iPad / iPhone (fields 16 px on touch screens); the two
    scrolling columns on the tablet can no longer be pushed sideways.
  * 2.2.9: tablet / computer: "Expand all / Collapse all" are two small symbols right of the settings search
    (phone unchanged); window: small symbol buttons too.
  * 2.2.10: the reload button (app mode) first looks for a new version, then reloads the page - a new version shows
    right away in the update bar.
  * 2.3.0: new app icon: orange tile with the white camera head (pan / tilt fork); one icon and one name «MoveEye»
    for every address (no more green / red, «MW Intern / Extern») - one Tailscale link works at home and away.
  * 2.3.1: phone too: "Expand all / Collapse all" as two symbols right of the settings search (no more big buttons).
  * 2.4.0: signed updates: every version in versions.json is signed with the developer's secret key (Ed25519, kept offline);
    only signed versions are offered and installed (update bar, automatic update, list shows signed / not signed). Setting
    "Also accept unsigned versions" for own builds. --make-manifest DIR --sign-key FILE signs.
  * 2.5.0: setup assistant at the first start (web page): language + device name, push messages (ntfy topic with QR code
    and test message), web password, QR codes of all addresses; System -> "Setup assistant" / "Quick start (QR)": printable
    card with QR codes (own Wi-Fi of the Pi to join, page addresses). Window: QR codes for the phone at the first start and
    under Setup. Own QR encoder (no extra package).
  * 2.6.0: web push: alarm messages straight into the browser / home screen app (no ntfy app needed): Notifications ->
    "Switch on on this device", test; needs https - button "https over Tailscale" (tailscale serve, real certificate);
    iPhone / iPad from the home screen app. Standard Web Push (VAPID + aes128gcm) with python3-cryptography.
  * 2.7.0: backup (Recordings -> Backup): finished alarm recordings are copied away from the device - WebDAV (Nextcloud,
    NAS, cloud), a folder (USB stick / NAS) or Telegram (video); one folder per day, waits for the sound, 3 tries, test button.
  * 2.8.0: theft protection (Alarm & camping): sabotage alarm when the camera is covered or turned away (picture check,
    pauses while the head moves itself), optional motion sensor MPU-6050 (I2C 0x68: moved / knocked over), power cut
    while armed = alarm; when armed an urgent push with picture + siren.
  * 2.9.0: targeted deterrence (Light & sound -> Deterrence): own reaction for person, big animal, small animal, warm
    body - sound (new: high whistle, bangs / claps, or own sound files) and / or the white light flashing; duration, pause,
    also when disarmed (garden).
  * 2.10.0: sharing with a small logo: animal diary pictures, snapshots, recordings and timelapse videos (new share button
    in the recordings viewer) and the night report picture get a discreet strip "MoveEye" + what / when (switch:
    Recording -> "Shared pictures and videos with a small MoveEye logo").
  * 2.11.0: several devices: Cameras page -> "Other MoveEye devices": picture, armed / alarm, battery, last event of
    every device (home network or Tailscale), arm / disarm one or all, search in the network, own password per device.
  * 2.12.0: MQTT / Home Assistant (System & network): state, events and the alarm picture to an MQTT broker, commands back
    (arm / disarm, lights, snapshot); Home Assistant discovery (alarm panel, person / motion / animal / recording, battery,
    temperature, camera picture). Own small MQTT client (no extra package), optional TLS.
  * 2.13.0: demo mode (--demo): a drawn camping scene where a person, a dog or a bear walks by now and then - alarm,
    recording, diary, deterrence work as with a real camera; own settings folder, "DEMO" in the header, nothing that changes
    the computer (shutdown, Wi-Fi, updates, passwords ...). For trying it out or an online demo.
  * 2.14.0: SMS over an LTE stick (Notifications -> SMS): alarm (person, sabotage, warm body, noise) as a text message -
    by default only when there is no internet; ModemManager, AT commands or Huawei HiLink; pause + daily limit; test SMS.
  * 2.15.0: manual: new chapter "Privacy & security" (what is stored, what leaves the device and when, sound, privacy zones,
    legal hints CH / EU); --self-test (checks signatures, QR codes, web push encryption, the web pages) - also run
    automatically on GitHub for every new version.
  * 2.16.0: overview in the settings: the arrow of a topic turns green while its main function is on (e.g. night report,
    timelapse, backup, MQTT); a group's arrow is green when at least one of its topics is on. Window: green dot at the title.
  * 2.16.1: "Recalibrate / Reset counter / Reset settings" and the settings line moved from Controls to System;
    the settings line in German ("gespeichert 10:51", not "saved").
  * 2.17.0: full screen on tablet, phone and computer: the picture fills the whole screen, the joystick floats see-through
    at the bottom right (pale after 3 s, ⇆ = other side) with "centre" and "listen"; the phone no longer puts the stick
    below / beside the picture.
  * 2.17.1: phone held sideways: the full-screen stick sits higher (away from the swipe bar at the bottom edge), so it can
    be pushed down too.
  * 2.17.2: joystick: the point where the finger lands is the middle (no jump upwards when the finger is put on it),
    small dead zone while the finger rests.
  * 2.17.3: full screen: "other side" (⇆) moved to the top next to ✕ - on the phone held sideways "centre" no longer
    switched the side by mistake; more space between the round buttons.
  * 2.17.4: full screen: the round buttons next to the stick react reliably (the nearest button wins, the touch area is
    bigger) - on the phone they reacted only when touched below them; short flash as feedback.
  * 2.17.5: full screen: stick and buttons are placed inside the picture box instead of "fixed" to the screen - on the
    iPhone they reacted about 1 cm below where they were drawn.
  * 2.18.0: quick switches below the joystick (green = on): thermal overlay, mark objects, white light, IR light, follow
    person, patrol, record now (max. 10 min, red while recording) and photo into the recordings; also in operator mode.
  * 2.19.0: recordings and alarm pictures without the big red boxes: thin corner marks only (face stays visible), or none,
    or like before (Recording -> "Markings in recordings"); "Feedback to the developer" (anonymous, sent by the Pi, waits
    without internet); app mode: "Save settings" and other downloads go to the share sheet (no page without "back");
    "Recalibrate" also under Controls; the deterrence arrow is only green when a loudspeaker / light can react.
  * 2.20.0: compact controls: stick | quick switches (now also listen and the relays) | small things (speed, centre,
    calibrate, waypoints, stick / buttons) in one bar; tablet / computer: the picture always fits completely above it;
    duplicates removed (listen twice, snapshot = photo, pan / tilt twice); light and relay Off / On / Auto moved into
    their settings topics.
  * 2.20.1: controls bar: small things now next to the stick, quick switches on the right; groups spread over the
    full width in landscape.
  * 2.21.0: waypoints store pan and tilt; patrol moves both servos together in a straight line (shown as 24/60);
    old pan-only waypoints are taken over with the former patrol tilt.
  * 2.22.0: patrol route selectable: back and forth (1-2-3-2-1) or round trip (1-2-3-1); the patrol quick switch steps
    off -> back and forth -> round trip -> off and shows the mode; setting «Patrol route» in Patrol (web and window).
  * 2.23.0: waypoints drawn on the joystick background (numbered points, line in patrol order, dashed back to 1 for a
    round trip; brighter while the patrol runs).
  * 2.23.1: phone turned to landscape: the control column next to the picture is more compact (fits the screen height) and
    the picture is put in the middle of the screen reliably after turning (no scrolling up needed).
  * 2.23.2: relay quick switch can be switched back: it used the relay state from when the page was loaded and so always
    sent «on»; now on -> back to the mode before (mostly automatic), with a short message.
  * 2.24.0: controls: only the joystick - the arrow buttons and the «Stick / Buttons» switch were removed.
  * 2.25.0: the window on the Raspberry looks like the web page: header with dot, name, tabs (Live / Weather & system /
    Event log) and symbol buttons; the picture in a card; control bar with a round joystick (drag from where you press,
    orange ring = camera position, numbered waypoints), speed / centre / calibrate / waypoints and the same quick switches
    (thermal, marks, light, IR, follow, patrol 3-way, record, photo, one per relay); settings with search field, ⊞ / ⊟ and
    green arrows; adapts to small screens (800x480: compact header, controls folded first, picture never cut wider);
    relay rows moved to «Relays & schedule». Patrol status in words (web and window).
  * 2.25.1: the app icon (orange camera head) top left instead of the blue dot - web page and window.
  * 2.26.0: ⇆ next to the speed swaps the stick and the small buttons (left- / right-handed); on the phone in landscape the
    control column goes to the other side of the picture, in fullscreen the stick too (one choice per device; window: kept).
  * 2.27.0: always a live picture: phone and tablet upright show a small live picture in a corner as soon as the big one
    is scrolled away (the same picture moves, no second stream); tap = back up, drag = other corner, ✕ = away; red frame
    while a person is seen. Tablet landscape / computer: the picture column stays anyway (only the settings scroll).
  * 2.28.0: five languages: German, French, Italian, Romansh (Rumantsch Grischun) and English - web page, window,
    manual, setup assistant, push / SMS texts, quick start card, guest page; language menu instead of DE/EN (Ctrl+L
    in the window: next language); missing Romansh texts fall back to German. Two small surprises for Swiss users.
  * 2.29.0: night vision look: green image-intensifier picture with grain and dark corners, the thermal camera draws
    glowing outlines of warm bodies and (Thermal-90) their temperature; quick switch 🌙 and «automatically at night».
  * 2.30.0: GPS: the phone sends its location (https page), otherwise the place from the settings; photos, snapshots,
    timelapse and diary pictures get EXIF GPS data, videos a location tag (shown on the map in photo apps); the phone
    location also keeps sunrise / sunset right.
  * 2.31.0: temperature sensor: BME280 / BMP280 (temperature, humidity, air pressure, I2C 0x76/0x77) or DS18B20 (1-Wire
    GPIO 4) are found by themselves; shown in the header and under Setup; every 10 minutes a value is kept for the diary.
  * 2.32.0: diary: day overview for every day - persons, animals (best pictures), warm bodies, noises, recordings; 24-hour
    chart with temperature / humidity of the sensor, weather (Open-Meteo, off by default), rain and the events; sun, moon,
    place and the night report. Browse the days with ‹ › or the date.
  * 2.33.0: small improvements.
  * 2.34.0: recordings: filter by place (pictures within 2 km = one place, names from OpenStreetMap, can be renamed) and
    a map with all places (tap = preview, «show only this place»). The Bluetooth loudspeaker is no longer on the page
    «Cameras» (still under Settings -> Loudspeaker).
  * 2.35.0: small improvements of the live picture.
  * 2.36.0: settings: the location is either taken automatically from the phone or picked by tapping on a map
    (with place search and «my position»); replaces the two number fields.
  * 2.37.0: privacy: shared pictures and videos no longer carry the location (switch «Send the location along when
    sharing», off by default). Downloads and the ZIP keep it - they are for yourself.
  * 2.38.0: self-check: one traffic light per part (camera, AI, servos, thermal camera, microphone, loudspeaker,
    temperature sensor, location, clock, internet, push, memory card, CPU temperature, power supply, battery,
    password, https) with what to do; on the web (panel + header badge) and in the Pi window (Weather & system).
  * 2.39.0: settings «Simple / Expert» (simple: only the important ones, on the web and in the Pi window); button
    «Guard tonight»: switches on what a night needs, arms with the countdown and tells what is still missing.
  * 2.40.0: false alarms: mark a recording «was nothing» (animal, wind, light, rain, car, other); the recordings page
    then suggests matching settings (one tap to take them over) and can show only the false alarms.
  * 2.41.0: one-page quick guide for the campsite (5 languages, printable): set up, connect, evening, alarm, morning,
    when something does not work. The QR card is now called «QR codes for connecting».
  * 2.42.0: AI model with one tap: «Download AI model» (self-check, AI settings, Pi window) fetches the two model files
    (about 70 MB) into the data folder and switches the AI on - no commands needed any more.
  * 2.42.1: «download failed» message in all languages.
  * 2.42.2: AI model download from Google's storage address (the old address has no valid certificate); shorter error
    messages.
  * 2.42.3: the green arrows follow a switch at once (also in Simple), taken from the switches on the page itself.
  * 2.43.0: protection against crashes of the whole Pi: the AI runs at most a few times per second and slower when the
    Pi gets hot; every 10 s the program notes CPU temperature and power supply - after an unexpected end the self-check
    shows what it was like; two short runs in a row -> «safe start» (AI, thermal camera, night vision, IR light,
    patrol off) with a push message. The UPS shutdown needs plausible values and 3 minutes of running first.
  * 2.43.1: only one MoveEye at a time: started by hand while the autostart runs it in the background (without a
    window), the program asks and takes over with its window (the background service starts again when the window
    is closed). The web page notices when a switched-off Pi is back and reloads by itself.
  * 2.44.0: operator mode keeps a copy of all settings when it is switched on; unlocking with the PIN puts back
    everything that was changed in the meantime (not: armed / disarmed, camera position, location, own Wi-Fi).
  * 2.45.0: operator mode may change everything (also zones, schedules, waypoints, relays) - except what could lock
    you out: Wi-Fi / own Wi-Fi / network, web password, autostart, loading settings, «reset settings», update source.
    Unlocking with the PIN puts everything back.
  * 2.45.1: «Recalibrate» and «Reset counter» removed from System («↻ Calibrate» stays next to the stick).
  * 2.45.2: operator mode button shows when it is on (since when) and ends it with the PIN; the header badge too.
  * 2.46.0: backup: the first picture of an alarm goes off the device at once (not only the clip at the end); clips
    too big for Telegram are made smaller instead of skipped; the self-check shows the backup.
  * 2.47.0: zones: «line» (a person crosses it - in both directions or only in the arrow direction) and «dwell area»
    (a person stays longer than N seconds); message in the log and - when armed - a push message with picture.
  * 2.48.0: storage: the self-check shows where the program and the recordings are (SD card / SSD / USB); the
    recordings can be put on an SSD or USB drive (Settings -> Recording, existing ones are moved over); if the drive
    is missing at a start, the memory card is used and the self-check says so.
  * 2.49.0: continuous recording (off by default): all the time with few pictures per second in 10-minute pieces,
    kept for N hours; the recordings page shows a 24-hour timeline with the alarms marked - tap to watch.
  * 2.50.0: picture for other programs (Home Assistant, Frigate, Blue Iris, VLC, NAS recorders): a secret address
    for the video (MJPEG) and a still picture, no login needed; optionally RTSP (H.264) if mediamtx is installed.
  * 2.51.0: System: bars for memory (RAM) and storage; the buttons are in small fold-out groups. Message texts:
    one card per message with bigger fields, tap to insert a placeholder, «standard text» and a preview.
  * 2.51.1: settings: a third button «open the groups only» (all groups open, their topics closed = overview).
  * 2.51.2: message texts: every message (person, pre-alarm, thermal, noise) folds open and closed.
  * 2.51.3: the settings search with its three buttons stays at the top while scrolling.
  * 2.52.0: thermal camera settings in three parts (alarm / picture / camera & alignment); a button left of the
    settings search hides the whole settings column (a tab at the right edge brings it back).
  * 2.53.0: every settings topic has its own symbol (web and window); the camera picture can be turned
    (90° / 180° / 270°) and mirrored - for a camera mounted sideways or upside down.
  * 2.54.0: extra sensors (new group «Sensors»): motion detector (PIR), door / lid contact and gas / smoke module on a GPIO,
    433 MHz radio sensors (RTL-SDR stick + rtl_433), Zigbee sensors (Zigbee2MQTT over MQTT) and Bluetooth tags
    (RuuviTag: moved / out of range). Alarm when armed or always (gas); a PIR wakes the power saving mode.
  * 2.55.0: storm warning (Sensors): push message when the air pressure falls fast (BME280), when a wind meter
    (anemometer on a GPIO) measures strong wind, or (optional) when the forecast expects gusts.
  * 2.56.0: own GPS module (USB / serial, or gpsd): location without the phone; theft tracking - when the armed device
    is carried away, an alarm and then its position (map link) every 5 minutes.
  * 2.57.0: «Talk» as a quick switch in the camera control - safe against an accidental press: tap once to unlock
    (6 s; a long press does not unlock), then hold to talk. It replaces the unprotected big button next to the joystick.
  * 2.58.0: «Mask» as a quick switch in the camera control (web and window): shows the motion mask over the picture.
  * 2.58.1: the motion mask keeps the picture as bright as it is and only tints the moving parts in a soft red.
  * 2.58.2: self-check: the loudspeaker hint is shorter.
  * 2.59.0: lens check - push message when the picture stays blurred and flat for 15 minutes (dew, dirt, spider web);
    temperature alarm (e.g. a pet in the caravan): push when it gets too hot or too cold, and when it is fine again.
  * 2.60.0: event report as PDF (recordings: 📄): pictures, time, place with map link, device, the log around the
    event and a checksum of the video - for the police or the insurance. No extra program needed.
  * 2.61.0: announcement from text (Loudspeaker): the Pi speaks a typed text, offline (pico2wave or espeak-ng);
    it can be saved as an own sound and then used for the siren / deterrence.
  * 2.62.0: solar panel (Sensors): an INA219 current meter shows watts, volts and today's yield; night forecast -
    does the battery last until sunrise? (self-check, and a push message in the evening when it will not).
  * 2.63.0: several users (System → Users): own login per person with a role - «Operate» (arm / disarm, lights,
    camera, talk; no settings) or «View only». The web password stays the administrator. The log shows who did what.
  * 2.64.0: hardware check step by step (System → Help and setup): camera, movement, AI, thermal camera, servos,
    microphone, loudspeaker, lights, push message and every extra sensor - each step checks itself where it can.
  * 2.65.0: animal species (AI detection): a second AI model (ONNX, e.g. for fox, badger, wild boar, marten, deer)
    looks at every animal the first AI finds; the species appears on the picture, in the log and in the diary.
    The model is not included - it is installed from an address (URL) or copied into the models folder.
  * 2.66.0: the guide (all five languages) describes the new parts: sensors, storm warning, GPS, solar, turning the
    picture, mask and talk tiles, lens check, announcements, animal species, PDF report, users, hardware check.
  * 2.67.0: when MoveEye starts in the background (autostart), a small message appears on the Pi's desktop
    with the address of the page (waits for the desktop after booting; can be switched off under Setup).
  * 2.68.0: Waveshare UPS HAT (E) (4 x 21700, for the Pi 5): found by itself at I2C 0x2D - charge level, time left
    and charging from its battery chip, the 4 cell voltages, USB-C input; power cut / back and safe shutdown as before.
    The «Listen» quick switch lights up green while listening (it never did).
  * 2.68.1: UPS HAT (E): the state register read as in the Waveshare register manual (bit 7 charging, bit 6 fast
    charging, bit 5 power at the input); the chip is recognised by its ID (0x0A).
  * 2.69.0: simulator connection: one button (quick switch «Simulation», F9 in the window) switches to a separate
    simulation program (motionwatch_simulator.py): its two cameras and thermal camera become the sources, MoveEye
    sends servos, lights, relays and sound, and takes day / night, temperature, pressure, wind and sensor events from it.
    Switching off brings the real cameras back.
  * 2.70.0: the simulator is inside MoveEye (signed with it): «Install simulator» puts it on the Pi with a menu
    entry and a desktop icon, «Start» / «Stop» runs it on the Pi; «Download (ZIP)» for a PC.
  * 2.71.0: simulator 2: real 3D view into a 360° world (own 360° photo possible), clock with fast time, moon and stars,
    rain / fog / snow, wind in the trees, cars with headlights, insects in the IR light, dew and spider web on the lens,
    covered camera, auto exposure and night noise, own cut-out photos as visitors, a ready-made night test.
  * 2.72.0: during the simulation nothing is saved: no alarm videos or pictures, no continuous recording, no timelapse,
    no photos, no diary entries, no backup. Push messages still come (to test them), marked «[SIM]».
  * 2.72.1: switching the simulation off no longer starts a recording: the alarms of the simulation are forgotten and
    the real camera first learns its picture for 30 seconds (no recording, no alarm during that time).
  * 2.73.0: Simulator 3 - updates itself (on the Pi when MoveEye starts, on a PC when it connects: it fetches the new
    version from MoveEye, checks the checksums and restarts); much more real: a distance for every pixel, light that
    falls off with the distance, haze and fog, ground pattern, clouds, sun, stars, better figures, lens distortion, glare;
    thermal picture with physics (cold clear sky, ground warmed by the sun and cooling at night, warm walls, clothes, engine).
  * 2.74.0: much less CPU during the simulation: MoveEye fetches only 6 pictures per second (adjustable, fixed camera and
    thermal picture half of it), the simulator draws every picture once for all viewers (its window shows the fetched ones),
    smaller simulator pictures (960x540, --hd for the big ones), pre-made picture noise.
  * 2.74.1: simulation with CPU saving: the AI runs only half as often (smoother CPU load when somebody is in the picture).
  * 2.75.0: simulator video scenarios: a 360° video (or a normal video) instead of the drawn world - real pictures, the cameras
    look around in it with the servos, big videos are made smaller once, rough thermal picture (what moves is warm),
    optional sensor events per video second (.json next to the video).
  * 2.76.0: the camera can also follow animals and other movement when no person is in the picture (also animals the AI does
    not know): it must go in one direction for 2 s, swinging branches are let go, off in strong wind; once chosen the animal is
    followed by its look while the camera turns. Video scenarios of the simulator chosen, played, deleted and uploaded from the
    web page. Simulator: the camera tilt was upside down (fixed).
  * 2.77.0: simulator control on the web page for every simulator (CONTROL protocol 1: the simulator describes its scenarios,
    sliders, choices, switches and buttons itself - ready for a later 3D simulator on a PC); three example 360° video scenes
    (forest at night, car park at night with a thief, misty camping morning) made by the simulator itself; a running simulator
    now also restarts when MoveEye has already put the new files in place.
  * 2.78.0: header shows how many watch right now: every browser with the page or a guest link open, plus the window on the
    Pi screen (when it is not minimised); the tooltip splits web / Pi screen.
  * 2.79.0: the quick switches below the joystick can be chosen and arranged («Arrange» tile: tick, ▲ ▼, reset) - web page
    and window; the viewer count moved to the right in the header.
  * 2.80.0: page /preview: the web page as on a phone or a tablet, upright or across, with or without full screen (button in
    the simulators and in the simulator section); the page may be shown in a frame of its own origin only (SAMEORIGIN).
  * 2.81.0: simulators are found by themselves: every simulator announces itself every 2 s (UDP 8764), MoveEye lists
    them («Use») and - with «find by itself» on and no working connection - takes over the address (a PC before the Pi);
    simulator requests never go through a proxy.
  * 2.82.0: simulator section tidied up: status with statistics (connected for, response time, camera / thermal pictures
    per second, messages, sensor events, errors), «Simulators in the network» with «Search now» (asks every address of the
    own network, progress and result), per simulator: seen since, last message, number of messages, response time;
    settings and tools folded away.
  * 2.83.0: System: size of the project (program file, lines, data, settings, recordings, simulator), running time, memory,
    Python version, Pi model and operating system.
  * 2.84.0: New page "Tools": network scanner (makers, names, warning about new devices, "am I at home" with automatic
    arming), Wi-Fi surroundings with the best channel, internet test, security check, Bluetooth scanner with tracker warning,
    focus assistant, servo test, loudspeaker / microphone test, memory card test, diagnosis package without secrets, power calculator.
  * 2.85.0: Second Wi-Fi adapter (USB stick): repeater (own Wi-Fi + internet from another network at the same time), change to
    another known network when the internet is gone, push message when it is back, devices in the own Wi-Fi without internet,
    Wi-Fi guard (alarm on jamming / deauthentication, needs a stick that can listen), adapter list with chip and abilities.
    Tools page tidied up: groups, every tool folds up and shows its last result. Fix: the Wi-Fi search of the settings works again.
  * 2.86.0: The 3D simulator for Windows can be downloaded from the Pi: /sim/simulator3d.zip (button under Simulator → Tools).
  * 2.87.0: Tools page redesigned, calmer: list of the tools on the left (with status), one tool at a time on the right; on a phone
    first the list, then the tool with a back button. Plain line icons, switches instead of check boxes, no empty boxes.
  * 2.88.0: Download of the 3D simulator 3D-1.4: it starts without sending; the switch «An MoveEye senden» in its window
    turns sending on.
  * 2.89.0: Tools: «Full power for the tools» - MoveEye rests for 10 to 120 minutes (camera, detection, AI, extra cameras;
    a recording is finished first), the web page and the tools keep running; it comes back by itself or with «Resume now».
  * 2.90.0: 3D simulator 3D-1.5 for download: six scenes to switch (camping place, forest, car park, garden with house, a funny
    place with a bench, carousel and ducks, wildlife watching with a high seat and a feeder) and a bloodless rifle for the
    wildlife watching (only animals: a hit animal hops, sees stars and runs away; aim also with the head camera).
  * 2.90.1: 3D simulator 3D-1.6: starts with the simple graphics (OpenGL), so a double click on the .exe works on PCs where the
    Vulkan graphics closed the window at once; the nicer Vulkan graphics with «Start mit Vulkan-Grafik (schoener).bat».
  * 2.90.2: 3D simulator 3D-1.7: it looks for a newer version on GitHub before it starts and offers «Jetzt aktualisieren»
    (download, check, replace itself, start again) or «Ohne Update starten».
  * 2.90.3: 3D simulator 3D-1.8: in a virtual machine (VMware, VirtualBox) it starts again with the ANGLE graphics by itself -
    the OpenGL driver there showed only the sky.
  * 2.90.4: 3D simulator 3D-1.9: «MoveEye auf diesem PC» - the simulator runs MoveEye itself on the Windows PC
    (Python and MoveEye are fetched once), so the phone / tablet simulator works without a Raspberry Pi.
  * 2.90.5: 3D simulator 3D-1.10: the Python download for «MoveEye auf diesem PC» uses the curl of Windows (it failed with
    the own download of the simulator); clearer error messages.
  * 2.90.6: 3D simulator 3D-1.11: «MoveEye auf diesem PC» takes the cameras from the simulator (the picture was black);
    the phone simulator starts with the normal start page.
  * 2.90.7: 3D simulator 3D-1.12: button «Nach Updates suchen» in its window (check and install at any time); faster updates.
  * 2.90.8: 3D simulator 3D-1.13: updates from far away (switch «Neue Versionen automatisch installieren» and a button, also in
    the simulator control on this web page); its window in the look of MoveEye; switches and the joystick work in its
    phone simulator; lighter in virtual machines; the rifle goes off when leaving the wildlife watching.
  * 2.90.9: The download of the 3D simulator for Windows (ZIP) is now a button right under «Search now» in the simulator section
    (before hidden under Tools); the desktop window shows its address for the PC browser in the simulator line.
  * 2.91.0: 3D simulator 3D-2.0 (big update): toolbar, search and «Einfach | Experte» like MoveEye; visitors as small
    pictures to drag into the world; people and animals walk around objects; smoother movement, finer objects, grass and
    flowers; new visitors (child, jogger, hare, hedgehog, dog walk, deer herd, birds); new visitor settings (also here in the
    simulator control).
  * 2.92.0: Fix: plugging in a second Wi-Fi adapter made the Pi unreachable (the repeater switched itself on and took the
    built-in adapter away from the home Wi-Fi). Now the repeater only runs when switched on by hand, the connected adapter keeps
    its connection, and it switches itself off again when the Pi has no connection for 2.5 minutes. New tab «Simulator» in the
    header: everything about the simulator on one page (switch, statistics, connection and search, picture, the control of the
    simulator, computing power, programs and downloads, short guide).
  * 2.92.1: Download of the 3D simulator 3D-2.1: minimizing makes it a small box in the corner (it keeps drawing pictures -
    before, MoveEye only showed «CONNECTING…»); while it sends, the PC does not go to sleep.
  * 2.92.2: Tab «Simulator»: the live picture is at the very top and moves (like on the live page); scrolled down, it shrinks
    into a corner (tap: back up, drag: other corner, ✕: away).
  * 2.92.3: 3D simulator 3D-2.2: starts with the PC (also small in the corner and without signing in, see its group «Start mit
    dem PC»). Simulator control: when the simulator brings new settings, they appear at once and the open groups stay open.
  * 2.92.4: 3D simulator 3D-2.3: it only calculates while its window is open or MoveEye is connected (saves power); its
    small box shows the CPU of the whole computer, of MoveEye and of the simulator (MoveEye measures and sends it).
  * 2.93.0: Clap switch (Light & sound): 2, 3 or 4 claps switch a relay, the white / infrared light, take a photo, record
    or arm / disarm; beep as answer, practice mode, only when not armed (adjustable). «Bless you!»: a small sound recognition
    model (YAMNet) recognises sneezing and the loudspeaker answers (spoken words or an own recording, uploaded from the
    phone); quiet at night; sneezes of the day in the diary. Tab «Simulator»: the sections fold up with arrows.
  * 2.93.1: Download of the 3D simulator 3D-2.4: game «Unentdeckt ans Ziel» for up to 4 players with their phones (own view,
    joystick, crouch, crawl); the simulator is the referee. Its settings appear in the simulator control (group «Spiel»).
  * 2.93.2: Download of the 3D simulator 3D-2.5: more realistic camera pictures (grain at night, raindrops on the lens, insects
    in the light at night - real false alarms to test); game: one player can be the guard (sees through the head camera),
    stones to distract, crystals to collect, lives, a microphone hears running; the referee works like a real detection.
  * 2.93.3: For the 3D simulator 3D-2.6: MoveEye tells the simulator what it detects (persons, animals, motion, noise) -
    for its test run with report (detection rate, reaction time, false alarms) and the game mode «MoveEye decides»;
    without a real microphone the noise alarm uses the sound of the simulated world. Its CPU is measured as before.
  * 2.93.4: Download of the 3D simulator 3D-2.7: nicer people (face, build, clothes), natural walking, activities, headlamps and
    phone lights at night; animals jump, hop, root and sniff.
  * 2.93.5: Download of the 3D simulator 3D-2.8: nicer animals (shaped body, darker back, neck, ears), people reach for the door
    handle.
  * 2.93.6: Download of the 3D simulator 3D-2.9: flags and laundry in the wind, chimney smoke, fireflies (all can be switched
    off); fixed: rain was missing in the camera pictures since 3D-2.6.
  * 2.93.7: Download of the 3D simulator 3D-3.0: game with two teams, team signals, choose your look (cap, hood, backpack,
    camouflage); figures react (startled, cheering, throwing).
  * 2.93.8: Download of the 3D simulator 3D-3.1: game mode team against team (robbers and guards, roles swap), rescue from the
    jail, team goal, bonus for a good distraction.
  * 2.93.9: Download of the 3D simulator 3D-3.2: game goal capture the flag with two teams.
  * 2.93.10: 3D simulator 3D-3.3: shadows are no longer black on some graphics cards (sky light as ambient colour), softer
    shadow edges.
  * 2.93.11: 3D simulator 3D-3.4: real place from the map (Switzerland: swisstopo terrain and aerial picture, OpenStreetMap
    buildings), sturdier update.
  * 2.93.12: Simulator control: group symbols and sub-headings (3D simulator 3D-3.5 with a tidied panel).
  * 2.93.13: 3D simulator 3D-3.6: mouse control (move, turn, zoom, select and carry visitors).
  * 2.93.14: 3D simulator 3D-3.7: camera pictures stay visible while the panel scrolls.
  * 2.93.15: 3D simulator 3D-3.8: real sun path for place and season, mountain shadows, game on real places.
  * 2.93.16: Simulator control looks like the panel of the 3D simulator (cards with symbols, parts, search, Simple / Expert) and
    a swisstopo map to choose a real place (3D-3.9).
  * 2.93.17: 3D simulator 3D-3.10: real 3D buildings of swisstopo at real places.
  * 2.94.0: NEW: mover (optional tracked vehicle): second stick on the web page (also full screen) and in the window, settings
    Camera & servos -> Mover (Motor HAT with PCA9685 + TB6612 found by itself, top / turning speed, gentle start, invert / swap
    tracks, stops after 0.6 s without a command); the 3D simulator 3D-3.11 can simulate it.
  * 2.94.1: 3D simulator 3D-3.12: overview map.
  * 2.94.2: 3D simulator 3D-3.13: new scene «hiding game» with many hiding places, more hiding places in all scenes
  * 2.94.3: 3D simulator 3D-3.14: place wizard (surroundings detected, presets for objects, objects that fit the surroundings)
  * 2.94.4: Mover stick can be shown in the simulation even without a mover or motor driver (setting, look only); 3D simulator
    3D-3.15: drive the mover in the simulator, report on the 3D buildings
  * 2.94.5: 3D simulator 3D-3.16: after an update it starts again as it was (sending or not, small box / icon, size and place
    of the window). Simulator search: the number counts simulators (not addresses), also ports 8767 / 8768 (a second simulator),
    a hint when a simulator is missing.
  * 2.95.0: second simulator «Python world simulator» (simulator_python/) as an alternative to the 3D simulator: download button
    (/sim/simulator_py.zip, fetched once and checked like the 3D one), tested with its settings in the tab Simulator.
  * 2.95.1: «Simulators in the network» shows the computer name next to each simulator (the simulator tells it, else the
    router's name service is asked once). 3D simulator 3D-3.17 (tells its computer name), Python world simulator PY-1.1.
  * 2.95.2: Live view: the simulator control (the same switches as in the simulator) under the picture while the simulation
    is on. Driving with the second stick switches the simulator's vehicle on by itself (3D simulator «Mover simulieren»).
  * 2.95.3: Live view: the window of the 3D simulator (map, compass, view buttons Frei / Kamera 1 / Kamera 2 / Wärmebild /
    Karte / Zum Kopf / Von oben) in the simulator control, operated with mouse, finger or keys (/sim/view.mjpg; 3D-3.18).
  * 2.95.4: pan up to ±180°: new setting «Pan servo: turning range» (180 / 270 / 360°), the pan limit goes up to half of it.
    The simulator gets the real angle (before, a tilt limit of 60° was shown as only 40° in the simulation).
  * 2.95.5: tab Simulator: button «Update the simulator» next to «Switch the simulation off» (blue with the version number when
    a newer 3D simulator exists); the simulator installs it and starts again by itself.
  * 2.95.6: tab Simulator: the picture at the top shows the simulator window (map, compass, view buttons) and is operated
    with mouse / finger / keys; switch «Simulator window» / «Camera picture» above it.
  * 2.95.7: 3D simulator 3D-3.19: the simulator window also works while the simulator is the small box on the PC.
  * 2.95.8: tab Simulator: installed and newest simulator version (looked up in the project once an hour), a warning with
    what is new when an update is there; the header shows «SIMULATION · ⟳ Update 3D-x.y» too.
  * 2.95.9: tab Simulator: «Connection» right under the picture, the picture as big as the screen allows, full screen
    button ⛶ for the picture (simulator window or camera picture).
  * 2.95.10: tab Simulator: order Connection, status, picture. The simulator window is fetched picture by picture (never
    a growing delay). Finger on the picture: scrolls the page, a tap clicks; with ✋ the finger controls the simulator.
  * 2.95.11: tab Simulator: the game of the 3D simulator (open / close, QR code and address, big QR code to photograph).
    Touch controls on the simulator window (✋ or full screen): left stick = fly, right stick = look around, ▲ ▼. 3D-3.20.
  * 2.95.12: game wizard in the tab Simulator: game type, goal, difficulty (beginners / normal / pros), start - with the
    rules; «Like last time» starts with the settings of the last game.
  * 2.95.13: tab Simulator: the status can be folded (arrow on the right); the arrows are green when what is inside works /
    is switched on. Game wizard: power-ups. 3D simulator 3D-3.21: more natural movements, power-ups, the last minute.
  * 2.95.14: spectators: over the simulator window the time, the players with their «seen» meter, what happened and at the
    end the result (📊 on / off). Game wizard: spectator camera (3D-3.22 flies over the field by itself).
  * 2.95.15: 3D simulator 3D-3.23: the game page on a phone lying on its side tidied up, full screen help for the iPhone.
  * 2.95.16: game wizard: «Open the game & show the QR code» shows its progress, errors of the simulator in the wizard,
    and the QR code at once.
  * 2.95.17: CPU of the PC the simulator runs on (tab Simulator, header «SIMULATION · PC 45 %»). The simulator is updated
    by itself when a newer version is there (switch in «Connection»). 3D simulator 3D-3.24: human crouching and crawling.
  * 2.95.18: game (3D-3.25): «caught» photos and gallery, hiding places, decoy, night round with torches, random events,
    checkpoints, ranking of the evening with records, handicap per player - in the wizard (Extras), the game card and the
    spectator view.
  * 2.95.19: trusted devices (a browser that logged in once stays logged in, also after updates; list in Users,
    removable; a new password logs all out). Power mode 🚀 (counterpart of power saving: every picture through the AI,
    best stream, simulator at full speed, processor governor «performance»; switching off restores everything).
    Small camera live picture inside the simulator window (📷). 3D simulator 3D-3.26.
  * 2.95.20: tab Simulator: the simulator window uses the whole screen width; the small camera picture sits top right
    (no longer over the control stick and the arrow buttons).
  * 2.95.21: tab Simulator: the fold arrow of the status sits in the title line (on the phone it stood alone below the
    button) and is hidden while the simulation is off; «Computing power» turns green only when «Save CPU» is on.
  * 2.95.22: tab Simulator: «Test run and optimization» - the 3D simulator (3D-3.27) plays a fixed test (standard, short,
    difficult conditions, night), MoveEye judges it (persons found, reaction time, false alarms by cause, score) and
    proposes better settings: take over one or all, undo, «take over and test again», or «optimize automatically» (keeps
    a change only if the next run is better); earlier runs with a bar chart. Game: «Team against MoveEye» (floating
    «Caught!» button on the live page), a task for every round, ranking of the week. 📱 phone as a window (motion sensor).
  * 2.95.23: new app icon (radar eye) with a choice of 7 (settings → Setup → App icon; also the old orange one); iPhone /
    iPad home screen: a hint how to renew the icon. The simulators are called MW Sim · Basis, MW Sim · 3D, MW Sim · Welt
    (Kevin), each with its own symbol. 3D simulator 3D-3.28.
  * 2.95.24: Python world simulator PY-1.2 (Kevin: computer name, panning up to ±180°); «pan_range» in the state for the
    simulators.
  * 2.95.25: the simulation goes on by itself when a simulator is online (and off again 60 s after the last one is gone;
    switch «Switch the simulation on by itself»); CPU of a simulator's PC in the list before the simulation is on
    (3D-3.29); power saving also saves in the simulation; the radar sweep turns in the page header.
  * 2.95.26: Pushover as an extra way for alarms (emergency = critical alert on the iPhone, rings also when muted);
    «simulation on by itself» is off by default on a Raspberry Pi; the simulator calculates slower while MoveEye
    saves power (3D-3.30); MW Sim · Basis 3.7 (new name and symbol).
  * 2.95.27: FIX - since 2.95.25 a few settings were missing from the defaults (simulator auto update, network watch,
    presence): errors on some pages. New: a keyword at the start of every message (MW-ALARM, MW-WAERME …) for iPhone
    shortcut automations, e-mail as a way for messages, shortcut addresses (/k/<key>/arm, siren_off, light_on, photo.jpg …).
  * 2.95.28: test runs flow back into the development: «Report for the development» (ZIP with versions, settings,
    results, causes and pictures - no secrets; for the chat or GitHub feedback/), pictures of every false alarm and missed
    person (3D-3.31), comparison with the last run of another MoveEye version, test run every night (optional).
  * 2.95.29: game corner for game nights (Tools → Leisure): guests join with the phone via QR code - quiz with buzzer,
    werewolf with narrator, drawing and guessing, connect four, dice and timer, scores. Game collection (8 free open-source
    browser games, 13.5 MB, offline). In the own Wi-Fi without login at /spiele. Fix: 'random' was not imported.
  * 2.95.30: tool «USB devices» (maker, model, type, speed, power need, driver, serial number and what the Pi made of it:
    Wi-Fi card, drive, camera …; newly plugged devices are marked; hints for USB 3 in a USB 2 socket and high power need).
    Update with a progress bar: real download progress, check, restart (estimated from the last restarts).
  * 2.95.31: the game corner has its own tab in the header. New button «Rest mode: only game server»: camera, detection
    and alarms pause, the Pi gives all its power to the games; ends by itself when the game corner closes.
  * 2.95.32: game corner: six new games for the phones - Stadt-Land-Fluss, estimating, explaining words (taboo), who am I,
    reaction, battleships. Game collection GS-1.1 with 15 games (new: Tetris, Pong, Dino run, and own games snake,
    minesweeper, sudoku, memory). Typed text is kept when the page updates.
  * 2.95.33: security and stability review. Camera loop restarts itself after an error (push after 5 errors), camera loss
    finishes the recording and tells the owner; damaged settings file -> backup copy instead of defaults; settings saved
    atomically; a new version that does not start is not installed again; update key never follows a redirect elsewhere;
    pages of other web sites cannot send commands (CSRF); viewers cannot move the clock by years or switch Tailscale HTTPS;
    alarm push tried 3 times, then SMS; the Wi-Fi password is not overwritten by a wrong one, the own Wi-Fi comes back
    after a failed switch; MQTT robust and disarm via MQTT announced; diagnosis package without secrets; optimizer
    restores the settings after an interruption; simulator never switches on by itself while armed; game corner: player
    keys secret. Encoders: a missing USB disk no longer disables them, memory use limited.
  * 2.95.34: review part 2. Mover: a clock set back no longer drives at full speed, motors stop on error / program end;
    battery shutdown tried again; a lost temperature sensor is reported; motion sensor and sound player robust; solar meter
    on the servo board address detected. Simulator control icons escaped (XSS); live pictures of rebuilt tiles stop their
    stream. Recordings: ZIP only with free space and without leftovers, share copies deleted with the recording, starring
    during a recording works, drive change never moves the running recording, unplugged drive under /media or /mnt is not
    used, loop pieces never overwritten, PDF report not while writing; import cannot move the recordings folder; diary keeps
    starred entries; operator mode also locks users, trusted devices and shortcuts.
  * 2.95.35: clock jumps (Pi without clock battery) no longer break timers and cool-downs; health list with detection loop,
    recording, continuous recording, background tasks and I2C conflicts - push message when something important fails
    while armed; alarm outbox: alarms that could not be sent are kept and sent later (also after a restart), «+N more
    detections»; live pictures limited (16, 6 per device), security headers, upload limit; browser games from their own
    port (web port + 2, only in the own Wi-Fi); one central list of what viewers may read; «Test all channels»; push
    address and I2C addresses checked when saved.
  * 2.95.36: game corner: «🚪 Leave» button on the phone page (also inside every game), «✕ Back» in every game of the
    collection; after joining the page shows the game at once (it waited up to 20 s). Collection GS-1.2 (Hextris without
    share buttons). 3D simulator 3D-3.32: the mover stick sits next to the control panel instead of under it.
  * 2.95.37: 3D simulator 3D-3.33 (new sky with clouds, stars and moon, four graphics levels, lightning, realistic
    infrared night picture - persons near the camera are now seen at night).
  * 2.98.65: Simulator 3D-4.34: neue Welt «Bergtal» (2 × 2 km) und Szenen zusammengefasst – Welten Bergtal, Ferienpark, Zuhause
    mit den alten Szenen als Orte; alte Kennungen gehen weiter, Trainingsnacht lädt Orte allein.
  * 2.98.64: Simulator 3D-4.33: Weitwinkel-Kamera wie im Gehäuse v5.2 – Montage «Im Gehäuse (v5.2)» (Standard) und «Nicht
    verbaut (Blindstopfen)», Fischauge wie das echte Objektiv, kleine IR-LED; Kachel 🔭 mit den neuen Knöpfen.
  * 2.98.63: Simulator 3D-4.32: Gameplay ausgefeilt – Probe-Runde mit Blinki, Wiederholung und Höhepunkte, Missionen,
    Nacht-Spiel, neue Werkzeuge, Turnier, Fairness, «MoveEye ins Schwitzen», KI-Turm (Rangliste auch in MoveEye), Abzeichen pro
    Szene.
  * 2.98.62: Simulator 3D-4.31: Nacht-Testlauf – ganze Nacht im Simulator mit Wahrheit, Abgleich in MoveEye, Bericht /nacht (nur
    der Besitzer startet); Trainings-Nacht 🏋 und Nacht-Generalprobe 🎭 mit eigenen Symbolen.
  * 2.98.61: Simulator 3D-4.30: Erlebniswelt im «Ferienpark am See» – 19 kleine Szenen mit Tieren und Menschen im
    Entdeckungsbuch, «Verstecken mit MoveEye» (nur im Ferienpark).
  * 2.98.60: Simulator 3D-4.29: Fenster «Neu in dieser Version» scrollt, OK immer sichtbar, Esc schliesst.
  * 2.98.59: Simulator 3D-4.28: neue Szene «Ferienpark am See» mit fünf MoveEye-Standorten (Zelt, Wohnmobil, Bungalow,
    Bootssteg, Rezeption); die Auswahl «Standort im Ferienpark am See» erscheint in der Simulator-Steuerung nur, wenn diese
    Szene gewählt ist. Szenen-Name in allen Sprachen.
  * 2.98.58: Simulator-Zentrale: neue Kachel «📖 Entdeckungen» (Spielen) – Stand des Entdeckungsbuchs im Simulator, Liste, «📷
    Foto für Entdeckungsbuch», «Im Simulator öffnen», «Blinki-Hinweis». Simulator 3D-4.27: Entdecken (Buch, Fund per Ansicht
    oder Foto der Kopfkamera, Tageszeit-/Wetter-Geheimnisse, Blinki-Hinweise, Demo im Camping-Platz).
  * 2.98.57: Simulator 3D-4.26: alle schwebenden Fenster (Kompass, Karte, Livebild, SmallTV, Gerät, Mover, Kopf, Kameras, CPU)
    in einem gemeinsamen Rahmen – verschieben, Grösse ändern, ✕ ausblenden, Schnappen, neuer Knopf «Fenster» in der Leiste unten
    (Liste, «Anordnung zurücksetzen»), Anordnung pro PC gespeichert.
  * 2.98.56: Sim-Kompakt: hat es neben dem Hauptbild Platz (PC, Tablet quer), steht das zweite Bild (Simulator bzw. Kamera)
    rechts daneben statt darüber – nichts wird mehr verdeckt; am Handy hochkant bleibt Bild im Bild. Das Simulator-Bild wächst
    nicht mehr mit dem Zoom «Grösse» aus seinem Platz.
  * 2.98.55: «MoveEye Sim · Basis» (alter Python-Simulator) nur noch mit dem neuen Schalter «Basis-Simulator anzeigen»
    (Simulator, Experte, Standard aus): ohne ihn kein Download, keine Knöpfe zum Installieren / Starten auf dem Pi (bestehende
    Installationen bleiben). Simulator 3D-4.25: Grafik-Stufe «Lite» für den Raspberry Pi 5 und «Leistung» in der Selbstdiagnose.
  * 2.98.54: Live-Seite am Handy: die Status-Chips stehen in einer Zeile zum seitlichen Wischen (Schutz-Zustand, Status-LED,
    alles ok / Probleme, Akku zuerst; Rand blendet aus, wenn weitere folgen) – die Sticks von Sim-Kompakt haben wieder ihre
    normale Grösse
  * 2.98.53: Sim-Kompakt «Bild im Bild»: Simulator-Bild gross, Kamera klein in der Ecke (antippen = tauschen, pro Gerät
    gemerkt); Simulator 3D-4.24: Simulator-Datei heisst neu MoveEyeSim3D.exe – alte Dateien löschen und neu herunterladen;
    Simulator startet mit frischen Einstellungen; Windows fragt evtl. nochmals (SmartScreen/Firewall) (ein Update aus dem
    Simulator erledigt den Wechsel von selbst); Logo-Person geht mit echtem Gang (Bein und Gegenarm zusammen, Web und
    Simulator); Falsche Meldung «Servo blockiert» in der Simulation behoben; Prüfung ab Werk aus (neue Einstellung «Blockierten
    Servo im Simulator melden»)
  * 2.98.52: Logo-Schriftzug: die Pupille im Auge schaut zur gehenden Person, das Auge blinzelt ab und zu (bei «Bewegung
    reduzieren» still); Simulator-Logo bewegt sich gleich (3D-4.23)
  * 2.98.51: Namen «MoveEye» statt «MW» / «MotionWatch»: Simulatoren heissen MoveEye Sim · 3D / Basis / Welt (Kevin);
    Push-Stichwort ab Werk «MoveEye» (MoveEye-ALARM, MoveEye-WAERME …; ein unverändertes «MW» wird einmal umgestellt –
    iPhone-Kurzbefehle auf "MoveEye-" anpassen); eigenes WLAN neu «MoveEye» (bestehende Geräte behalten «MotionWatch»);
    Downloads MoveEye_…; Simulator 3D-4.22: Lautsprecher in «Licht & Ton», Hinweis «Regeln der Tasten → in MoveEye»
  * 2.98.50: Status-LED & 2 Tasten am Gerät (GPIO 16 / 26; dürfen alles, einzeln abschaltbar, Push bei Ausschalten /
    Sirene-Stopp am Gerät), Simulator-Gerätefenster, «Alarm quittieren» im Alarmfenster, Sprachen-Grundlage im Simulator,
    Grundsprache Deutsch, Romanisch «Aura»; dazu Menü-Umbau, 57 neue Gegenstände im Simulator, 💬 aus der Kopfzeile,
    Entwickler-Schalter geteilt, Karte «Mehr» im Simulator, Angleichen MoveEye ↔ Simulator
  * 2.98.49: Push-Nachrichten als Kanal-Karten (Stufen, Ruhezeiten, ntfy Standard), Simulator als Lautsprecher, Servo-Störungen,
    Wärmebild ausrichten (warme Hand), Übungen über Simulator-Werte, In 3D nachspielen aus Zeitleiste und Aufnahmen,
    Schnittstellen-Test, SmallTV Live-Bild/Akku/Alarm-GIF, Simulator 3D-4.20
  * 2.98.48: Zusatz-Bildschirm GeekMagic SmallTV (Status, Alarmbild, Spielstand, nachts rot, mehrere Bildschirme, Einrichtung
    mit QR-Code, virtueller SmallTV im Simulator 3D-4.19)
  * 2.98.47: Weitwinkel-Kamera (Montage im Simulator, Übersicht lenkt den Kopf automatisch, IR breit Kanal 4), Werte aus dem
    Simulator (Akku, Uhr, Ort/Wetter, Pi-Wärme, Netz-Ausfall, 🧪), Verfolgungs-Parcours (Kachel 🎯: Regler, A/B,
    Auto-Tuning-Vorschlag), Online-Spiel über Tailscale Funnel (nur Spiel öffentlich, nur Admin mit Passwort, geht von selbst
    aus), neue Szenen, Simulator 3D-4.18
  * 2.98.46: Sim-Kompakt (Live-Seite mit Simulator: zwei Bilder, Kopf- und Rover-Stick, Kacheln), MoveEye als KI-Wächter, Stopp
    im Simulator ausgeblendet, Stange-Regler, Aufklapp-Knöpfe zeigen den Zustand blau (Reihenfolge zu · Gruppen · auf),
    Simulator 3D-4.17 mit Spiel-Balance
  * 2.98.45: KI-Hilfe für den Menschen am Auslöser (Knopf 🤖 im Bild, L2): KI-Rahmen, KI zielt, KI-Autopilot; solche Runden
    zählen nicht für die Rangliste (mit Simulator 3D-4.16).
  * 2.98.44: Mit Simulator 3D-4.15: neue Menschen-Figuren mit Skelett (echtere Bewegungen, Wärmebild, Avatar am Handy, Namen nur
    für Spieler).
  * 2.98.43: Benutzer mit Rollen Kind / Freund / Familie / Nur ansehen / Eigene Rechte, Handy per QR verknüpfen, Geräte pro
    Person, Zugangszeiten und Ablaufdatum, Push pro Person. Controller überall gleich belegt (mit Simulator 3D-4.14:
    Symbol-Dock, Menüs mit Controller, Vibration, mehrere Controller). «⏹ Stopp» nur mit Schwenkkopf und abschaltbar.
  * 2.98.42: Fehlalarm-Lernbilder aus dem Spiel: Der Ausschnitt kommt aus dem richtigen Bild, zweifelhafte (Person in der Nähe,
    zu gross, Kopf gedreht) gehen nach fa_learn/zweifel/ statt ins Training; Knopf «🔍 Lernbilder prüfen» sortiert vorhandene aus
    (mit Simulator 3D-4.13: im Spiel nur noch 1–4 statt ≥19 Fehlalarme pro Minute).
  * 2.98.41: 3D-Simulator auf dem Pi (HDMI) entfernt – Updates werden ~25 MB kleiner; «Kluge Runde» ist jetzt ein Unterschalter
    von «Patrouille» («klug: wichtige Richtungen länger anschauen»).
  * 2.98.40: Schnellere Seiten: MoveEye schickt Seiten, Skripte und Daten komprimiert (gzip, die Hauptseite 810 KB → 250 KB);
    die grossen Seiten werden fertig komprimiert vorgehalten.
  * 2.98.39: Aufräumen: ein Eintrag «Servos» (Positionen, Test, Diagnose); alter Kurzbefehl-Schlüssel wird App-Schlüssel (/k/
    geht weiter); Almanach folgt Hell/Dunkel/Rotlicht; Ausblenden überall pro Gerät; Zonen-Art «Nur melden» und Schalter «Bleibt
    am Platz»; Licht/Sirene zielen auf Person oder Zelt; kluge Runde nur mit Patrouille; während «Team gegen MoveEye» keine
    automatische Kopfbewegung; Tierart-Gruppe; «Weckton» und «Sirenenton» statt zweimal «Ton».
  * 2.98.38: Live-Bild: wird das Bild nach dem Wechseln der Reiter wieder sichtbar, holt die Seite einen frischen Bildstrom
    (vorher blieb es auf dem iPhone manchmal schwarz); solange kein Bild da ist, zeigt eine Sanduhr ⏳ «Bild wird geladen –
    tippen zum Neuladen».
  * 2.98.37: Spiel: drei feste Spiele + «Eigene Regeln», Rollen reihum, Wächter-Werkzeuge mit Energie, Hinweise für Schleicher,
    Siegerbild, Fairness; «Mensch gegen KI» (Vergleich + Trainingsbilder); online mitspielen mit Einladungslink (läuft ab,
    widerrufbar, QR, Gäste sehen nur das Spiel). Knopf Hell → Rotlicht → Dunkel (mit Simulator 3D-4.12).
  * 2.98.36: Auslöser im Spiel (Fadenkreuz in der Bildmitte, 🎯-Knopf / R2: Treffer = Foto, Alarm ins Test-Postfach, Spieler
    raus, Punkte; daneben = Minuspunkte und 3 s Sperre). Servos wie bei Industrierobotern: Rampen aus einem Bewegungsplaner,
    Selbstdiagnose mit Fehlerspeicher und Betriebsstunden, Not-Aus mit Freigeben, sichere Grenzen und Watchdog, Teach-in mit
    benannten Positionen, Anzeige «wer steuert» auf allen Geräten (mit Simulator 3D-4.11).
  * 2.98.35: Blinki, das Maskottchen im Guide und in den Rundgängen (blinzelt, schaut, hüpft; abschaltbar mit «Blinki zeigen»).
  * 2.98.34: «Über MoveEye»: Elektro ist Robotik-Entwickler.
  * 2.98.33: Ein Guide nach der Installation (zuerst «Schnell oder ausgiebig?»), Rundgänge mit Sprechblasen auf allen Reitern
    («?» startet neu), Einfach/Experte pro Seite, Karten «Tipps & Tricks», «?» an den Einstellungen, Tipp des Tages; geschützte
    Werkseinstellungen (WLAN, Fernzugang, ntfy, Updates, KI-Modell bleiben). Rückmeldung 💬 von jeder Seite (Art, Sterne, Bild,
    geht an beide ntfy-Server), «Über MoveEye» (Versionsnummer antippen). QR-Codes neben den Links und eine QR-Galerie unter
    Mehr.
  * 2.98.32: Controller-Ansicht für Handy und Tablet: mit Bluetooth-Controller (oder Knopf 🎮) Live-Bild und nacktes
    Simulator-Bild über- bzw. nebeneinander, tauschbar; Gesten auf dem Simulator-Bild (drehen, zoomen, Ansicht wechseln);
    schlanke Leiste (Licht, IR, Wärmebild, Nachtsicht, Markieren, Foto, Aufnahme, Folgen); linker Stick Kopf, rechter Stick
    Rover (später auch echter Mover), R1 Ansicht drehen, R3 Blick wechseln (mit Simulator 3D-4.10).
  * 2.98.31: Kein Live-Bild seit 2.98.30 behoben: die Pi-Kamera stand noch als Zusatzkamera in der Liste (Hauptkamera
    «Automatisch»), und seit Zusatzkameras nach dem Neustart wieder starten, stritten beide um die Kamera. Die Hauptkamera hat
    jetzt immer Vorrang und wird aus der Zusatzliste entfernt. Live-Seite: ohne Bild ein schwarzes 16:9-Feld statt eines
    schmalen Streifens.
  * 2.98.30: Assistent «Platz einrichten» (Schutz): Rundblick mit Panorama, Bewegung und KI, nachts mit IR und Wärmebild;
    antippen Zelt / Zugang / Wertsachen / Ignorieren → Zonen, Linie, Patrouille, Masken, bewachte Sachen; Zonen bleiben am
    Platz, wenn der Kopf dreht. Blickwinkel pro Kamera (Modell wird erkannt). Automatische Kopfbewegung: kluge Runde, zum Alarm
    drehen, Parken bei Aus, Wertsachen-Blick, sparsam bei Akku/Nacht, Gehtest folgt, Wildtier-Modus, Sabotage-Prüfung; 360°- und
    Endlos-Servos, Übersichtskamera lenkt den Kopf. Behoben: Webseite konnte ohne https nach 60 s hängen; Zusatzkameras
    starteten nach einem Neustart nicht.
  * 2.98.29: Zwei MoveEye am selben Simulator (Pi und KI-Hilfe auf dem PC): nur eines steuert den Kopf, das andere schaut zu
    (vorher wackelte der Kopf und die Kamerabilder flackerten); Live-Seite: Regler «Grösse» 60–160 %, iPad-Grössen, ein Weg zum
    Ordnen (Bearbeiten in «Ansicht», «Für alle Geräte übernehmen»), Kalibrieren ohne Kopf unter «… mehr», Simulator nur einmal,
    Fenster mit Ansicht-Menü; Wärmebild: Personen auch bei klarer, kalter Nacht; Controller im Spiel (Simulator 3D-4.9).
  * 2.98.28: Neue Live-Seite: ordnet sich nach dem Fensterformat (hoch: Bild oben; quer: Bild links, Steuerung rechts; klein:
    nur Bild mit schwebenden Knöpfen), Bild immer ganz sichtbar, Bildgrösse-Regler, Joystick nur mit Schwenkkopf (quer im Bild),
    Lieblingsknöpfe, Simulator direkt unter dem Bild und darunter der Gehtest, Knopf «Ansicht» mit Vorlagen (Nur schauen,
    Bedienen, Einrichten) und Bearbeiten-Modus, pro Gerät gespeichert. Überlappungen in «Bedienung» behoben.
  * 2.98.27: Pi-Kamera als Hauptkamera: läuft sie noch als Zusatzkamera, wird diese zuerst geschlossen (vorher «Camera __init__
    sequence did not complete»); die Hauptkamera lässt sich nicht mehr ein zweites Mal als Zusatzkamera hinzufügen.
  * 2.98.26: Simulator: zwei offene Simulator-Fenster liessen das Bild zwischen zwei Ansichten springen – jetzt zählt nur das
    neueste (mit Simulator 3D-4.8). Nach dem Ausschalten der Simulation bleibt das Simulator-Bild nicht mehr stehen (man sieht
    den Stand der echten Kamera); die Pi-Kamera als Hauptkamera hat Vorrang vor einer Zusatzkamera und wird bei «besetzt»
    nochmals versucht.
  * 2.98.25: App-Schlüssel für Home Assistant und Kurzbefehle (auch über http, können Passwort und Sicherheit nie ändern,
    jederzeit sperrbar); alles zur Sicherheit an einem Ort (Einstellungen → Sicherheit); ein Knopf Hell → Dunkel → Rotlicht
    (früher eigener Knopf «Dunkle Ansicht»); Simulator: Spiel-Karte schlank, Bewachte Sachen, Sim-Schalter nur als Kachel,
    Unsichtbar-Trank.
  * 2.98.24: Kamera am Pi 5: die inneren Knoten des Pi (rp1-cfe, /dev/video0 … 7) gelten nicht mehr als USB-Kamera;
    «Automatisch» nimmt ohne USB-Kamera die Pi-Kamera, und eine gewählte «USB camera 0», die in Wahrheit ein innerer Knoten ist,
    wird zur Pi-Kamera. Zusatzkameras zeigen die echte Bildrate (vorher z. B. «707 fps»), Aufnahmen haben dadurch das richtige
    Tempo.
  * 2.98.23: Aufräumen: «Nachtblick» heisst «Dunkle Ansicht», Testen nur noch an einer Stelle (Karte «Testen»), KI-Modell in
    einer Gruppe, «Dein Platz» (früher Zwilling), KI-Daten aufräumen (Vielfalt im Paket, alte Pakete weg, PC-Hilfe mit eigenem
    Modell), Anmelden nur verschlüsselt (Passwort von anderen Geräten nur über https).
  * 2.98.22: Wärmebild läuft mit: sobald eine Wärmebild-Kamera gewählt ist, sucht MoveEye darin Tag und Nacht nach Personen –
    auch wenn Überlagerung und Wärme-Alarm aus sind. Ältere Einstellungen werden einmal umgestellt (Ausschalten bleibt möglich:
    «… auch am Tag»).
  * 2.98.21: Simulator 3D-4.5: Spiel mit Wetterwechsel, Tarn-Sachen, Diebstahl-Missionen (MoveEye prüft mit dem Referenz-Scan)
    und Lern-Punkten
  * 2.98.20: KI-Modell: Auswertung «wo versagt die KI» im Modellfeld, neues Modell nur wenn nicht schlechter (täglich);
    Simulator 3D-4.4 (realistischer: Pi-5-Modus, Objektiv, Infrarot, Wärmebild, Fehlalarm-Quellen, schwierige Personen, Tiere,
    Dein Platz; KI-Training mit Vielfalt)
  * 2.98.19: «Aus» in der Push-Nachricht nur mit PIN, Push nach Stromausfall, Fehlerseiten übersetzt (Anmeldung «MoveEye»),
    Nachtblick, Bildschirmleser, Aufnahmen nach Tagen löschen, Push ohne Bild; Code-Pflege (Doppelte-Funktionen-Prüfung,
    Web-Rauchtest, Übersetzungs-Test), Echtbild-Prüfsatz, Einrichtungs-Skript; Prüfstand zählt echte Pushes; Fehlalarm-Jäger
    lernt mit; Simulator 3D-4.3
  * 2.98.18: Nachts strenger: eine Person, die nur die Bewegung fand (ohne KI), muss in 3 Bildern aufrecht stehen – gegen
    Fehlalarme durch Tiere
  * 2.98.17: Fehler behoben: Lautsprecher-Suche (Bluetooth) startete die Tracker-Suche
  * 2.98.16: Weniger Fehlalarme durch Tiere: Grössen-Prüfung (zu klein für eine Person an dieser Stelle = keine Person; lernt
    aus KI-bestätigten Personen)
  * 2.98.15: Eine Wochenmeldung (mit der Simulator-Woche), eine Zeitleiste, Spiel-Gruppe nur Assistent/Öffnen/Start/Stopp,
    Akku-Schwellen zusammen, «Wenn mein Handy zurückkommt: ausschalten / fragen / nichts», Auto-Tuner höchstens ±20 %,
    Gehtest-Anzeige; Simulator 3D-4.2
  * 2.98.14: Gesamtrunde: ntfy-Knöpfe (Fehlalarm/Sirene/Aus), Akku-Prognose, Morgen-Push mit Bildstreifen, «Was war das?», Zonen
    nach Art, doppelte Bestätigung, Ansage beim Scharfschalten, «Bist du's?»; Gehtest, Entfernung im Alarm, Personen im
    Wärmebild, Akku-Sparautomatik; Zeitleiste der Nacht, Gesichter verpixeln beim Teilen, Wochenbericht; eigenes KI-Modell
    (ONNX); Assistent «Erkennung verbessern», Modi vereint, Einfach-Modus 9 Bereiche, Fenster mit 6 Reitern, Sim-Zentrale in
    Gruppen; Speicherkarten-Schutz, Selbstheilung, eine Sperre mit dem Simulator; Tiere seltener als Person; Simulator 3D-4.1
  * 2.98.13: Erkennung: Schattenfilter schnitt blasse Personen weg (NoIR) – behoben; Lichtwechsel im ganzen Bild = sofort neuer
    Hintergrund; Auto-Tuner zählt Gehende nicht mehr als Rauschen; KI-Lupe für Personen weit weg; Menü Verlauf → Nachrichten
    (gesendete Push-Nachrichten, ntfy-Server); Tunnel-Selbsttest; Simulator 3D-4.0
  * 2.98.12: Simulator 3D-3.99 (Start mit Tunnel, Kopfkamera am Tag nicht zu dunkel)
  * 2.98.11: Livebild nach Simulator-Update: Wiederverbindung nach 6 s ohne Bild, alte Tunnel-Leitungen werden geschlossen;
    Geräusche aus dem Simulator (Klatschschalter, Gesundheit, Wecker schlummern); Solarpanel und GPS-Modul im Simulator;
    Simulator 3D-3.98
  * 2.98.10: Simulator 3D-3.97 (Farben, Jahreszeiten, Kamerafarben, Stick-Drift-Korrektur, Kopf mit Controller);
    Browser-Controller schickt rohe Achsen
  * 2.98.9: Privatsphäre-Zonen bleiben am Ort, wenn der Kopf sich dreht; eine Nachtzeit für Nachtbericht, Wecker und «Heute
    Nacht bewachen»; 2× klatschen = schlummern; Assistent «Wofür brauchst du MoveEye?»; Guide mit Erklärungen beim ersten Öffnen
    (Stufen); Logo mit roter, laufender Figur; Prüfstand nach jeder Version; Gesten im Simulator geprüft
  * 2.98.8: Entwickler-Bereich (nur eigenes Gerät, nur lesen: eigene Verbindungen, erreichte Namen, Datenmenge der
    Netzwerkkarten), ausblendbar, mit eigener PIN; jede Nutzung im Protokoll
  * 2.98.7: Spiele freigeben: eine Taste für Spielecke, Spielesammlung und Simulator-Spiel (ein QR-Code); Wecker mit
    Schlafplatz: nachts wegschauen, beim Wecken zum Bett drehen, Gesten (winken = schlummern, aufstehen = aus); Schlafplatz in
    jedem Bild abgedeckt
  * 2.98.6: Echt-Abgleich: MoveEye misst das Aussehen seiner echten Bilder (Tag/Nacht) und schickt es dem 3D-Simulator;
    Schnellschalter kompakt, nicht verfügbare ausgeblendet
  * 2.98.5: Simulator-Zentrale: «Zonen in 3D» und «Erkennung in 3D» sind jetzt im Simulator unter «Ansicht»
  * 2.98.4: Simulator-Zentrale in zwei Gruppen: «Ausprobieren» und «Lernen & Testen»
  * 2.98.3: Kopf der Einstellungen aufgeräumt: Suche über die ganze Breite, darunter Einfach/Experte und Symbole kompakt,
    Erklärungen als Hinweis beim Darüberfahren
  * 2.98.2: MoveEye-Punkte (Spiel und echter Betrieb, mit Abzeichen der Spieler), ein Morgen-Push (Panorama und Simulator-Woche
    im Nachtbericht), Fehlalarme aus den Spielen ins Fehlalarm-Lernen
  * 2.98.1: Ein «Folgen» für Personen, Tiere und Bewegtes: die Kamera zielt auf das Objekt (Winkel aus dem Sichtfeld) statt in
    kleinen Schritten, gleich wie «Verfolgen» im Simulator
  * 2.98.0: Menüs nach Ziel: 6 Reiter (Live, Schutz, Verlauf, Einstellungen, Simulator, Mehr), Schutz-Seite mit Alarm-Kette,
    Seite «Mehr», Aus / Wachsam / Voll überall, «Einfach» neu gewichtet, Spiele mit Nutzen (blinde Flecken aus den Spielen auf
    der Karte, Schleichwege als Testplan)
  * 2.97.1: Ordnung im Hintergrund: eine Sperre für alle Simulator-Aufgaben, Zeitplan schaltet über die Scharf-Logik, Modi
    stellen in jeder Reihenfolge richtig zurück, Optimierung fragt «auch echt übernehmen?», AutoTuner pausiert bei Tests,
    Anwesenheit aus beiden Quellen, Updates warten auf Tests
  * 2.97.0: Sicherheit: PIN beim Klatschschalter, Simulation fragt bei scharfem MoveEye, Sirene nicht mehr doppelt, Spiele und
    Übungen ohne echte Sirene und Pushes, Lagerfeuer ohne Personen-Alarm, Herkunft bei Aufnahmen
  * 2.96.13: Passt zum Simulator 3D-3.87 (Schriftzug MoveEye auch im Simulator)
  * 2.96.12: Aufgeräumt: die Knopfzeile über den Einstellungen hat wieder nur ihre drei Knöpfe (Kino und Demo standen dort leer
    über der Suche) – «Kino» und «Demo» sind jetzt bei den Schaltern unter dem Livebild (mit «Anpassen» ein- / ausblendbar)
  * 2.96.11: Neuer Schriftzug in der Kopfzeile: am PC eine Zeile (W6: «Move» hell, «Eye» orange, das «o» ist das Auge mit
    Sichtfächer und erkannter Person), auf dem Handy untereinander (W1, wie die Skizze)
  * 2.96.10: Einstellungen aus der Simulation: Schwenken / Neigen werden nie mehr gefragt (nur zurückgestellt); bei jeder
    Einstellung «🔕 nie fragen» – sie wird künftig ausgelassen (die echte bleibt), «wieder fragen» setzt das zurück
  * 2.96.9: Reiter Simulator: die Zentrale steht jetzt unter dem Livebild; Schiessen-Knopf im Livebild: ausgeschaltet nur noch
    ein kleiner runder Knopf am Rand und nur, solange das Livebild sichtbar ist; passt zum Simulator 3D-3.86 (aufgeräumte Menüs,
    Inventar mit allen 80 Dingen der KI)
  * 2.96.8: Makeover 21–25 (Simulator-Zentrale): Fehlalarm-Lernen (nach 👎 stellt der Simulator die Ursache 60 s nach, Bilder als
    «keine Person» fürs Training); Karte der blinden Flecken mit Tipp; Nacht-Generalprobe («heute Nacht erkennst du Personen bis
    … m», auf Wunsch beim Scharfschalten); Schwellen automatisch (Tag + Nacht); Erkennungs-Check jede Woche mit Warnung; passt
    zum Simulator 3D-3.85
  * 2.96.7: Makeover 16–20: mehrere Geräte (zweites Gerät bewacht Zelt / Velo / Auto, Übergabe einer Person zwischen Geräten im
    Protokoll); Rover (Patrouille, Ladestation mit Akku, zum Alarm fahren – auch von selbst bei Personen-Alarm); Statistik aus
    dem Simulator (4 Wochen, Arten, Erkennungsrate, Wochenbericht als Push); Versionen vergleichen (Erkennungsrate und
    Testlauf-Punkte pro Version); Ein-Klick-Demo (3 Minuten im Kino-Modus); passt zum Simulator 3D-3.84
  * 2.96.6: Makeover 12–15 (Simulator-Zentrale): Trainings-Nacht (Testläufe in 5 Szenen, Optimierung, Trainingsbilder, Bericht);
    A/B-Vergleich von Einstellungen; Test-Posteingang (Meldungen in der Simulation hierhin statt aufs Handy) und «Alarm-Kette
    testen» (Push, Licht, Sirene); Störfall-Übungen Akku leer, WLAN weg, Hitze, Kälte mit Bericht, wie MoveEye reagiert hat
  * 2.96.5: Makeover 8–11: «Was wäre wenn …?» – jede Aufnahme mit 🧪 im Simulator nachstellen (Uhrzeit, Regen, Richtung, Anzahl
    Personen; neue Aufnahmen merken sich die Situation); Zwilling deines Platzes (Ort, Zonen, Patrouillen-Punkte an den
    Simulator, zurück Ort und Stangenhöhe); Zonen und Erkennung live in der 3D-Ansicht (Kacheln in der Simulator-Zentrale);
    passt zum Simulator 3D-3.83
  * 2.96.4: Makeover 1–7: gleiche Farben in Fenster, Webseite und Simulator; Streifen «SIMULATION – Alarme sind nicht echt» mit
    orangem Rahmen auf allen Seiten; Simulator-Kachel auf der Startseite und Simulator-Zentrale (Szene, Tageszeit, Wetter,
    Besuch schicken, Überraschungsnacht, Vorlagen, Spiel, Tests, Tagebuch); Kino-Modus /kino (Vollbild für TV / Beamer mit
    Laufband); einheitliche Ereignis-Symbole in Push-Titeln, Tagebuch und Fenster-Protokoll
  * 2.96.3: Nach jedem Update erscheint einmal kurz «Neu in dieser Version» (Webseite und Fenster) mit dem, was als Nächstes im
    Makeover kommt (abschaltbar unter Updates); passt zum Simulator 3D-3.82 (Fenster «Vorlagen»: fertige Szenen, echte Orte,
    3D-Bausätze, eigene .glb-Dateien; 4 neue Szenen)
  * 2.96.2: Entwicklungsphase: schnelle Updates einmalig eingeschaltet (jede Minute nachsehen, sofort installieren); passt zum
    Simulator 3D-3.81 (der Simulator schaut jetzt auch jede Minute)
  * 2.96.1: Panorama-Bericht «Fehlende Gegenstände» (separat einschaltbar, jeden Morgen mit Bild und Uhrzeiten);
    Simulator-Tagebuch im Tagebuch (alle Besuche mit Auswertung); passt zum Simulator 3D-3.80
  * 2.96.0: Neuer Name: MoveEye (früher Motion Watch) mit neuem Logo (Sichtfeld, gehende Person in Erkennungs-Ecken, bewegt sich
    in der Kopfzeile); einmalige Umstellung des App-Symbols; passt zum Simulator 3D-3.79
  * 2.95.105: Schutz: Stufen Aus / Wachsam / Voller Schutz, Schutz-Assistent, Ampel mit «Beheben», Diebstahlschutz-Zeile,
    bewachte Gegenstände, Sirene nach X s, PIN zum Ausschalten, «Schutz testen»; Begriffe «Schutz an / aus»;
    Bluetooth-Lautsprecher schnell erreichbar unter den Modi
  * 2.95.104: Passt zum Simulator 3D-3.78 (Spiel-Assistent neu, übersichtlich und animiert)
  * 2.95.103: Simulator: Kopf steuern und Licht aus dem Simulator-Fenster; Disco-Licht in einem kleinen Untermenü; passt zum
    Simulator 3D-3.77 (am PC mitspielen, Verstecken mit dem Rover, Bots, Wiederholung u. a.)
  * 2.95.102: Passt zum Simulator 3D-3.76 (Überwachen mit Ort-Frage, Uhrzeit bleibt, Spiel verlassen, Startkamera frei)
  * 2.95.101: Simulator-Tunnel stabiler (neuste Leitung zuerst, alte Leitungen verworfen); passt zum Simulator 3D-3.75
    (Überraschungsnacht, Verbindung nach Updates, leichtere Grafik, Prüfstand automatisch)
  * 2.95.100: Oranges App-Symbol überall (einmalige Umstellung), orange Simulator-Symbole; passt zum Simulator 3D-3.74
    (Kamerafehler, Schleicher, Nachtwetter, Kinder-Missionen)
  * 2.95.99: Simulation: Trainingspaket für ein eigenes KI-Modell (YOLO, im Simulator gemacht); 3D-Simulator 3D-3.73: Szene
    «Mein Zuhause» mit Baukasten
  * 2.95.98: Referenz-Scan: Gegenstände bewachen (Rechteck im Referenz-Foto, fehlt er beim Vergleich = sofort Alarm), eigene
    Nacht-Referenz; 3D-Simulator 3D-3.72: Nacht-Test, Testhilfen, Sabotage-Test, Planer + Referenz-Scan
  * 2.95.97: Referenz-Scan: Assistent (Werkzeuge) – der Kopf fährt alle Richtungen ab und speichert Referenz-Fotos; Vergleich
    von Hand, beim Scharfschalten oder alle N Minuten, Bericht mit fehlt / neu / verändert, Push-Meldung; auch vom 3D-Simulator
    aus startbar (3D-3.71)
  * 2.95.96: Simulation: 🎯 Schiessen im Livebild (Schuss / Auslöser an die angetippte Stelle, in jedem Spiel und in der freien
    Welt; daneben = Fehlalarm, wird markiert); nach dem Schwenken von Hand keine weissen Bewegungs-Umrisse mehr (Hintergrund
    wird sofort neu gelernt); 3D-Simulator 3D-3.70
  * 2.95.95: 3D-Simulator 3D-3.69: Kinder-Modus (grosse Bild-Knöpfe, Murmli, Töne, Konfetti; zurück zu Erwachsene mit
    Rechenaufgabe)
  * 2.95.94: 3D-Simulator 3D-3.68: nach einem Update verbindet sich der Simulator wieder von selbst (kein «Port 8765 is busy»
    mehr)
  * 2.95.93: Simulator: «verbunden» und grün nur, wenn der Simulator antwortet UND Bilder ankommen (vorher immer «verbunden»,
    sobald die Simulation an war) – auch in den Menüs und im Fenster; Einstellungen aus der Simulation: nur noch fragen, was
    während dieser Simulation geändert wurde, ohne Wärmekamera-Quelle und Werte der Selbstoptimierung
  * 2.95.92: Simulator-Vollbild im Browser: nur noch das Bild und ✕, Steuer-Sticks und Knöpfe mit 🕹 einblendbar, der Mover-Stick
    im Simulatorbild verschwindet; 3D-Simulator 3D-3.67
  * 2.95.91: 3D-Simulator 3D-3.66: beim Setzen der Patrouillen-Punkte bleibt die Ansicht bedienbar, «Fertig» und Esc beenden das
    Setzen
  * 2.95.90: 3D-Simulator 3D-3.65: «An MoveEye senden» bleibt nach einem Update und Neustart so wie vorher
  * 2.95.89: 3D-Simulator 3D-3.64: die Pfosten der Patrouillen-Route stören die Bildauswertung nicht mehr (nur der Bediener
    sieht sie)
  * 2.95.88: Wärmebild in der Simulation passend über dem Videobild (Blickwinkel beider Kameras, vorher nach aussen verschoben);
    Symbol «Klassisch»: nur die Pupille bewegt sich; kleines Extra: 3 s Zielscheibe, dann 3 s das Geheimnis; Simulator 3D-3.63
  * 2.95.87: Symbol «Klassisch (orange)»: das Auge in der Kopfzeile schaut links und rechts; Simulator 3D-3.62 mit dem orangen
    Symbol
  * 2.95.86: Simulation mit eigenen Einstellungen: beim Zurückschalten die Liste der Änderungen, Übernahme wählbar (abschaltbar)
  * 2.95.85: 3D-Simulator 3D-3.61: Patrouille mit dem Mover, Spielart «Patrouille», Werkzeugleiste – alles mit der Maus
  * 2.95.84: 3D-Simulator 3D-3.60: Rover versetzen, Mitspieler frei beim Erkunden, besserer Beobachter-Modus
  * 2.95.83: Game-Controller am Browser (z. B. PS5) steuert den Rover im Simulator – auch wenn der Simulator in einer VM läuft;
    3D-Simulator 3D-3.59
  * 2.95.82: Vollbild: Mover-Stick mit ✥ frei auf dem Bild verschiebbar (doppelt tippen = zurück), Platz je Seite gemerkt
  * 2.95.81: Simulator-Fenster im Browser schärfer: Bildgrösse passend zum Bildschirm, Wahl «Bildqualität» (automatisch, sehr
    hoch, hoch, mittel, niedrig), WebP; 3D-Simulator 3D-3.58
  * 2.95.80: 3D-Simulator 3D-3.57: Stangenlänge des Kamerakopfs einstellbar (Mover, Erkunden)
  * 2.95.79: 3D-Simulator 3D-3.56: Erkunden – Ansicht wechselt von selbst nach oben, wenn etwas im Weg steht
  * 2.95.78: 3D-Simulator 3D-3.55: Erkunden mit dem Rover (Tastatur, Maus, Touch, Game-Controller)
  * 2.95.77: Vollbild: Knopf 🚜 blendet den Mover-Stick ein (gegenüber dem Kamera-Stick, mit ⇆ tauschbar)
  * 2.95.76: 3D-Simulator 3D-3.54: Schleichwege nur auf ihrer eigenen Karte
  * 2.95.75: Simulator: MoveEye schickt die Rahmen der erkannten Personen (genaue Zuordnung im Spiel); KI-Prüfung mit den
    verpassten Bildern aus dem Spiel; Rangliste «Bester Schleicher»
  * 2.95.74: Spiel «Team gegen MoveEye»: der Jäger zielt durch Antippen der Spieler im Livebild (oder Knopf); 3D-Simulator
    3D-3.52: Treffer-Effekte und Erkennung lernen aus dem Spiel
  * 2.95.73: Handy: Einstellungen als Knopf unten bei der Bedienung statt am rechten Rand; Mover-Stick standardmässig
    ausgeblendet, mit 🚜 einblendbar
  * 2.95.72: Live-Ansicht: beim Wechsel der Videoquelle (z. B. Simulation aus → Webcam) holt die Seite das Livebild von selbst
    neu
  * 2.95.71: Updates: Test-Modus «neue Versionen sofort holen» (schaut jede Minute auf GitHub, installiert gleich); Werkzeuge-Seite und Fenster auf dem Pi: Symbol links, Pfeil rechts, beide grün, wenn die Funktion läuft
  * 2.95.70: Einstellungen: Umschalter «Symbole» – farbige Emoji mit grünem Punkt oder schlichte Symbole, die grün werden;
    3D-Simulator 3D-3.51: Verbindung vor Kameras
  * 2.95.69: Simulator-Seite nach Logik geordnet (Verbindung, Status, dann Livebild und Steuerung erst wenn verbunden); Symbol
    und Pfeil grün, wenn die Funktion läuft; Vollbild quer: Steuer-Stick wieder am richtigen Platz
  * 2.95.68: Simulator über den Tunnel: MoveEye stellt nicht mehr auf die direkte Adresse um (schwarzes Livebild), und
    kehrt von selbst zum Tunnel zurück
  * 2.95.67: Simulator-Verbindung meldet die Version und den KI-Stand (für den Prüfstand im 3D-Simulator 3D-3.49)
  * 2.95.66: simulator: when it announces itself in the network but does not answer, the page says so (firewall or security
    software of the PC blocks MoveEye - use the tunnel); the own simulator search no longer knocks at the own tunnel port,
    the tunnel shows only real simulator tries
  * 2.95.65: detection with few pictures per second (power saving, night, slow simulator): the speed limits in pixels per
    picture and the distance of the tracker grow with the real frame rate - before a walking person counted as a vehicle and was
    ignored, or the tracker lost it; a vehicle is judged from the median speed of two steps on
  * 2.95.64: detection: the frame rate is now the real number of pictures per second (before 1 / processing time, far too high
    with a slow camera, power saving or the simulator - the auto-tuner then wanted up to 24 pictures of walking before a person
    counted); FPS badge shows the power saving; 3D simulator 3D-3.48 (test bench: head camera as truth, visitors by size)
  * 2.95.63: program split into parts by topic (folder quelle/, put together by werkzeuge/bauen.py into this one file - nothing
    changes for the Pi); test bench pruefstand/ measures the detection with the 3D simulator
  * 2.95.62: the little extra: the secret is drawn tiny (one screen pixel per square, about 2 mm on a phone) - only readable
    with a magnifier; stays 20 s, a tap ends it
  * 2.95.61: the little extra (web page and window): a turning heart to touch, a big heart drawn counter-clockwise bursts into
    pieces before the secret shows
  * 2.95.60: 3D simulator 3D-3.47 (tunnel field visible, shows the target with port); simulator page: the tunnel card shows the
    port MoveEye listens on, the last try of a simulator (wrong code?) and the port of the direct connection
  * 2.95.59: 3D simulator 3D-3.46: the field «Tunnel zu MoveEye» in the simulator was hidden and can now be seen
  * 2.95.58: product page for guests: the logo top left and the icon of the tab are now the app icon of this MoveEye (the
    same as in the tab)
  * 2.95.57: product page for guests: the night story is now a deck of cards to swipe away, every situation plays its own little
    animation (countdown and scan, wind with leaves, fox in the thermal picture, intruder with light, siren and loudspeaker,
    deer photo into the diary, night report); swipe over the camera picture for day / night
  * 2.95.56: every page without its own way back (almanac, game corner, network check, party pages ...) gets a «✕ Zurück»
    button: as an app on the home screen there is no back button, so such pages could not be closed; it also leaves full screen;
    the product page and the preview use the same logic
  * 2.95.55: new product page for guests (/info/): animations start while scrolling, a scrollable night story, real camera
    pictures and current app screens, close button (leaves full screen); simulation on but its camera gives no picture (slow PC
    / VM): MoveEye now tries the simulator again every 10 s instead of keeping the webcam for good; tunnel address no
    longer stays after a restart
  * 2.95.54: Survival almanac (German, offline, /almanach/, also for guests: emergency numbers, weather, health, water, fire,
    orientation, camp and wild animals, knots, night sky, evening stories; search, red light, reading aloud; tip of the evening
    on the TV view). Disco light: the white light flashes with the music (microphone) or a fixed tempo, at most 3 times a
    second, alarms first. Bluetooth loudspeaker: pairing with an agent for speakers without keyboard, search with newer bluez.
    Tunnel for a simulator behind a firewall without admin rights (port 8766, code). Game collection GS-1.3: touch games and
    games with on-screen buttons (Tetris, Racer, Breakout, Pong, Astray). Simulator 3D-3.45.
  * 2.95.53: AI helper: a PC in the network does the detection for the Pi (MoveEye with --helper on port 5057, pairing
    code; found by itself through the 3D simulator; the Pi takes over again at once when the PC is gone). TV mode of the 3D
    simulator from the page. Aufstell-Planer: take over the patrol. Alarm replay in 3D (tracks round each alarm). Reception map
    (walk round in the network check). AI test with simulator pictures and training pictures as ZIP. Preview page: close button.
    Simulator 3D-3.44.
  * 2.95.52: Network check of the players (Tools): every phone measures reaction time, jitter, losses, download and upload to
    MoveEye - phones in the game corner by themselves, others with a QR code; with the own Wi-Fi also the signal of each
    phone, grades and tips. Product page for guests (Tools, /info/): the MoveEye homepage straight from the Pi for
    everybody in the same Wi-Fi, without login and internet; questions from its form arrive as push message; QR code also on the
    TV view.
  * 2.95.51: TV view for the HDMI of the Pi (/tv/<key>/: simulator or camera picture, game wizard, QR code to join, time,
    players, ranking, game corner; starts by itself in the campfire / gamer mode; any screen in the network can open the link);
    the 3D simulator can run on the Pi itself (button in the tab Simulator, fetched and checked like the Windows package); USB
    tethering: a phone on the USB cable gives internet, also to the own Wi-Fi. Simulator 3D-3.43.
    The symbols of the simulator groups are green when something is on (orange: something to watch).
  * 2.95.50: the game wizard shows a picture for every game type, goal and difficulty (3D simulator 3D-3.42).
  * 2.95.49: fix: the campfire games and the gamer mode no longer switch the own Wi-Fi on (it cut the phone off the network, the
    page froze); the camping guard asks first, as the camping profile does.
  * 2.95.48: the game wizard of the 3D simulator now runs in the simulator itself (3D-3.41); the tab Simulator shows the same
    steps and works it from afar (both stay the same).
  * 2.95.47: modes: one switch for the whole device (tab Live → Camping / protection, also in the window): camping guard,
    campfire games (game corner, the guard watches on sparingly, back to the camping guard at a set time or with a low battery),
    gamer (only with mains power: power mode, all games, guard if wanted; falls back to campfire games on battery), home,
    wildlife watching, night guard, transport. «Own settings» restores what was set before.
  * 2.95.46: eight new app icons from the proposals (light radar, night radar, forest with a find, thermal picture, field of
    view, tent watch, shield, radar with finds).
  * 2.95.45: 3D simulator 3D-3.40 (scenes that play by themselves: break-in attempt, barbecue evening, coming home late, parcel,
    fox at the bin, wild boars, children playing tag, farmer mowing; new moods, the whole night in time-lapse, calendar).
  * 2.95.44: 3D simulator 3D-3.39 (more visitors: cyclist, pram, pizza courier, police round, drunk, couple, horse, cows, sheep,
    chamois, ibex, lynx, bats and owl at night, tractor, motorbike, van).
  * 2.95.43: simulator interface for the mover written down (simulator/Simulator_Schnittstelle.md); optional answer
    field «mover_pose» (position, direction, metres, blocked) is taken and shown in /api/state; order 3.11 for the world simulator.
  * 2.95.42: 3D simulator 3D-3.38 (card «Besuch» newly arranged: presets, people, animals, vehicles and scenes, by itself,
    behaviour; buttons with pictures). Simulator panel on the page: a symbol in front of the visitor buttons.
  * 2.95.41: 3D simulator 3D-3.37 (the card «Verbindung» folds; its symbol and title turn green when MoveEye is connected).
  * 2.95.40: 3D simulator 3D-3.36 (new name «3D-Simulator Live» in the panel and the window title).
  * 2.95.39: 3D simulator 3D-3.35 (mouse wheel and clicks over the control panel, map, live picture and stick no longer move the 3D view).
  * 2.95.38: 3D simulator 3D-3.34 (live picture of a camera below the overview map, settings under System → Ansicht).

Install:  sudo apt install python3-pil.imagetk python3-tk python3-gpiozero ffmpeg python3-picamera2 alsa-utils
          pip install opencv-python numpy pillow flask psutil
AI model (optional, put next to the script):
          wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz
          tar xzf ssd_mobilenet_v2_coco_2018_03_29.tar.gz
          cp ssd_mobilenet_v2_coco_2018_03_29/frozen_inference_graph.pb .
          wget https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt -O ssd_mobilenet_v2_coco.pbtxt
Run:      python3 webcam_bewegung_2_98_65.py  [--source auto|usb:0|pi:0|rtsp://...] [--cam 0] [--no-web] [--headless] [--port 5000]
                                            [--web-password SECRET] [--bind 127.0.0.1] [--https [--cert F --key F]]
Autostart: python3 webcam_bewegung_2_98_65.py --headless --web-password SECRET --https --print-service   (shows the systemd unit)
           sudo python3 webcam_bewegung_2_98_65.py --headless --web-password SECRET --https --install-service
Web pages: /  live + settings   /cams  all cameras   /recordings  preview   /zones  zone editor
            --web        start the web page right away      --headless   no desktop window (web only)
            --web-password  protect the web page (user name: anything)

Servo backends: gpiozero (works on Raspberry Pi 5) -> pigpio (older Pis, needs
"sudo pigpiod") -> simulation (no hardware, everything else still works).
"""

