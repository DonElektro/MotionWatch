extends Node3D
## MoveEye 3D simulator - scenes: camping place, forest, car park, garden, funny place, wildlife watching (scenes.gd)
## The world, the cameras for MoveEye (head camera on the pan / tilt head, fixed camera, thermal camera),
## day and night, weather, lights, visitors, sensors, the window on the PC and the connection (net.gd).

const VERSION := "3.67.0"
const Versionen = preload("res://scripts/versionen.gd")   # Versionierung 3.0.0: from 3.0.0 VERSION = "X.Y.Z" like MoveEye (see there)
const Stimme = preload("res://scripts/abenteuer_stimme.gd")   # 3.23: the one switch «Stimme» (an | aus | untertitel)
const TestrunS := preload("res://scripts/testrun.gd")    # 3D-3.90: plan names and times for the card «Testen»
const T := preload("res://scripts/i18n.gd")              # Menüs A: new texts of the panel in the language (Sprachen)
const Quality := preload("res://scripts/quality.gd")     # 3D-4.25: «Lite» for the Raspberry Pi 5 (Quality.lite(), Engine meta «lite»)
const Kompakt := preload("res://scripts/kompakt.gd")    # 3D-4.x: the four compact scenes (Pfadilager, Hofladen, Bergdorf, Festival)
const Waerme := preload("res://scripts/waerme.gd")       # 3D-4.26: the heat table (people, animals, engines, fire, sun)
const CAM_W := [960, 640]
const CAM_H := [540, 360]
const CAM_FPS := [12.0, 8.0]
const CAM_FOV := [66.0, 102.0]            # 3D-4.17: camera 1 = the wide camera (Camera Module 3 Wide NoIR, weitwinkel.gd)
const TH_W := 80
const TH_H := 62
var TH_FOV := 90.0                # 30.10.2026: the model of the thermal camera decides (simint.gd: Thermal-90 or the old 45°)
var th_fps := 15.0
var th_noise := 0.125             # °C noise per pixel (NETD of the module)
const HEAD_H := 1.6
const HELPER_LAYER := 128         # 3D-3.64: marks for the operator only - the cameras of MoveEye do not see them

var Actor = preload("res://scripts/actor.gd")
var Net = preload("res://scripts/net.gd")
var Phone = preload("res://scripts/phone.gd")
var Scenes = preload("res://scripts/scenes.gd")
var Updater = preload("res://scripts/update.gd")
var Mwpc = preload("res://scripts/mwpc.gd")
var UI = preload("res://scripts/ui_style.gd")
var Sym = preload("res://scripts/symbole.gd")          # 3D-4.22: drawn symbols, text without the emoji the font lacks
var sym_node = null
var Autostart = preload("res://scripts/autostart.gd")
var Game = preload("res://scripts/game.gd")
var GrafikHoch = preload("res://scripts/grafik_hoch.gd")   # F1 «Grafikstufe Hoch» (Forward+: GI, Nebel, Spiegelungen, Oberflächen)
var hoch                              # grafik_hoch.gd (null until _ready)
var TestRun = preload("res://scripts/testrun.gd")
var Life = preload("res://scripts/life.gd")
var stories                           # events.gd: break-in, barbecue, coming home ... (3D-3.40)
var preset_kinds: Array = []          # a mood of «Vorlagen» brings its own visitors (empty = those of the scene)
var calendar_on := true               # weekend more people, winter fewer
var Recorder = preload("res://scripts/recorder.gd")
var Device = preload("res://scripts/device.gd")
var Geo = preload("res://scripts/geo.gd")
var Karte = preload("res://scripts/karte.gd")
var geo                               # geo.gd: a real place in Switzerland (scene «ort», from 3D-3.4)
var karte                             # karte.gd: the map to choose the place
var gamewiz                           # gamewiz.gd: the game wizard (3D-3.41), also worked from MoveEye
var abenteuer                         # bergtal_abenteuer.gd: Bergtal-Abenteuer «Die Karte des Grossvaters» (Rucksack, Tour, Nacht, Morgen)
var ort_lat := 0.0                    # the chosen place (kept)
var ort_lon := 0.0
var ort_name := ""
var ort_env := "auto"                 # the wizard (3D-3.14): surroundings, how many hiding places, cars, forest, camp
var ort_hide := 1
var ort_cars := true
var ort_forest := 1
var ort_camp := 0
var terrain := false                  # the scene has hills (ground_y), else the ground is flat at y = 0
var ground_fn := Callable()            # 3D-4.x: a scene with its own ground (ferienpark.gd): height in world coordinates
var fp_spot := "zelt"                  # 3D-4.x: where MoveEye stands in the «Ferienpark am See» (ferienpark.gd SPOTS)
var szene_spot := ""                   # 3D-4.x: where MoveEye stands in the compact scenes (kompakt.gd): "szene=standort;…"
const Worlds := preload("res://scripts/worlds.gd")   # 3D-4.x Welten: the old scenes are places in a few worlds
var welt_solo := false                # «allein»: old scenes without their world (--solo, Prüfstand: comparable measurements)
var solo_scene := ""                  # this one scene alone ({"action": "scenario", "id": …, "solo": true}, e.g. the training night)
var bt_spot := "huette"                # 3D-4.x «Bergtal» (bergtal.gd): the sleeping spot (SPOTS, viewpoints or «frei»)
var bt_bed := "tent"                   # tent | mat (Isomatte + Schlafsack)
var bt_season := "auto"                # auto (from the month) | fruehling | sommer | herbst | winter
var bt_free: Array = []                # the own spot: [x, z, looking] in valley coordinates
var bt_events := true                  # random events in the valley (rockfall, stranger, animal at the food, weather)
var bt_mount := "stativ"               # MoveEye's mount at the spot: stativ | rucksack | stein | zelt | baum (height of the head)
var bt_bag := "sommer"                 # sleeping bag: sommer | winter
var bt_stove := true                   # a stove at the spot (hot while cooking: thermal picture)
var bt_wall := false                   # a wind wall of stones on the side of the main wind
var bt_orient := "leicht"              # orientation: leicht (map + marks + position) | mittel (map only) | schwer (signposts only)
var bt_marks: Array = []               # own marks on the map [[name, x, z]] (valley coordinates)
var bt_visited: Array = []             # places already visited (quick travel only goes there)
var ground_mats: Array = []           # ground materials of the place (snow, wet)
var flat_nodes: Array = []            # flat meadow and the hills far away: hidden at a real place
var geo_note := ""
var testrun                           # testrun.gd: test run with evaluation (from 3D-2.6)
var life                              # life.gd: daily life, real weather and time (3D-3.27)
var recorder                          # recorder.gd: recording and replay of situations (3D-3.27)
var dev2                              # device.gd: a second MoveEye device in the world (3D-3.27)
var game_bots := 0                    # 3D-3.77: computer players
var game_tutorial := false            # 3D-3.77: practice round with explanations, nobody is caught
var game_daily := false               # 3D-3.77: the challenge of the day
var game_ghost := true                # 3D-3.77: the ghost of the own best way
var game_heart := true                # 3D-3.77: heartbeat when the camera nearly sees you
var game_botguard := true             # 3D-4.x: «Wächter» without a person as guard: a bot guards (gamebots.gd)
var game_kiguard := false            # 3D-4.x: «MoveEye als KI-Wächter» (gamekiwaechter.gd) - not saved, only for this session
var localplay                         # 3D-3.77: localplay.gd - play here at the PC
var headpad                           # 3D-3.77: headpad.gd - steer the head of MoveEye
var templates                         # 3D-3.82: templates.gd - «Vorlagen»: scenes, places, kits, own 3D files
var game_tasks := true                # a task for every round of the game (bonus) - 3D-3.27
var daily_life := true                # visitors at their own times, the postman and the neighbour every day
var real_weather := false             # the weather of the place from open-meteo.com
var surprise_on := false             # 3D-3.75: «Überraschungsnacht» (surprise.gd)
var power_off := false               # 3D-3.75: power cut - the lamps of the place are out
var surprise
var simint                            # simint.gd (30.10.2026): loudspeaker of MoveEye, servo faults, thermal model, warm hand
var pir                               # pir.gd (real-pir-ton): the AS312 PIR at the front of the housing
var mikro                             # mikrofon.gd (real-pir-ton): the USB microphone like real + the sounds of the surroundings
var simwerte                          # Simulator-Werte (30.10.2026): battery, Pi heat, network test, clock (power.gd)
var visitlog                          # 3D-3.80: visitlog.gd
var night_weather := false            # 3D-3.74: the weather runs through the night (dusk, showers, dew, morning fog)
var _nw := {"day": -1, "plan": [], "last": "", "fog_lens": false}
var real_time := false                # the clock of the PC
var game                              # game.gd: «Unentdeckt ans Ziel» with up to 12 phones (3D-3.95, before 4)
var game_minutes := 3.0                # 3D-4.x: short rounds (Spielkonzept des Besitzers, before 5)
var game_level := "normal"            # easy | normal | hard
var game_quality := "mid"             # picture on the phone: small | mid | big
var game_max := 6                     # 3D-3.95: runners at most (2..12); more players watch through the head camera
var game_guard := true                # without MoveEye the head guards by itself
var game_mode := "camera"             # camera: all against the camera · guard: one player is the guard
var game_lives := 0                   # 0 = unlimited
var game_items := 3                   # crystals to collect (+100 each)
var game_cones := false               # show the fields of view of the cameras (for beginners)
var game_noise := true                # the microphone hears loud steps
var game_stones := true               # stones to throw (distract the guard)
var game_powers := true               # power-ups: cloak and turbo (3D-3.21)
var game_spectate := true             # spectator camera: flies over the field by itself while a round runs (3D-3.22)
var game_photos := true               # «caught» photos (3D-3.25)
var game_fx_laser := true             # 3D-3.52: hit sequence - red laser from the camera head
var game_fx_paint := false            # ... paint ball with a splash on the ground
var game_fx_flash := true             # ... flash like a speed camera
var game_tap := true                  # the hunter at MoveEye aims by tapping the live picture
var game_learn_miss := true           # the game teaches MoveEye: pictures of players it did not report
var game_learn_report := true         # ... game report (how long until reported, distance, posture, light)
var game_learn_paths := true          # ... ways of players who reached the goal unreported (test run for the bench)
var game_blind_bonus := true          # ... points for seconds visible but not reported
var game_hides := 3                   # hiding places (bushes)
var game_decoy := true                # a player may be the decoy
var game_night := false               # night round with torches
var game_events := true               # random events: thunderstorm, dog, car
var game_checkpoints := 0             # checkpoints with a bonus
var game_autohandicap := false        # whoever leads the ranking gets a handicap
var game_random := false              # start and goal by chance
var game_rescue := false              # caught -> jail, a team mate frees you (3D-3.1)
var game_teamgoal := false            # the goal opens only when all crystals are found
var game_teams := false               # two teams: red against blue (3D-3.0)
var game_goal := "reach"              # reach: get to the goal · return: fetch the loot and bring it back to the start
# ---- start with the PC (from 3D-2.1; autostart.gd) ----
var autostart_on := false             # read from Windows (Run key) / Linux (autostart folder), not from the settings
var autostart_min := true             # at the autostart: minimized = the small box of mini.gd
var autostart_mwpc := false           # at the autostart: also start MoveEye on this PC
var autostart_lock := false           # at the autostart: lock the screen afterwards (with the automatic sign-in of Windows)
var last_scene := ""                  # the scene of the last time (the autostart comes back to it)
var start_info := ""                  # message of the autostart for the status line
var _bg_t := 0.0
# ---- saving power (from 3D-2.3): the world only moves while the window is open or MoveEye is connected ----
var eco_idle := true                  # setting «Nur rechnen, wenn ...» (saved)
var sim_active := true                # false = pause: nobody looks (window small / minimized, no MoveEye)
var win_open := true                  # the big window is visible (not the small box, not minimized)
var mini_box                          # mini.gd
var cpu_info := {}                    # measured by MoveEye: {"total", "mw", "sim"} in % of the whole computer
var _fps0 := 0
var mwpc                              # MoveEye on this PC (mwpc.gd)
var mwpc_btn: Button
var mwpc_label: Label
var in_vm := false                    # virtual machine / no graphics card: lighter graphics, fewer preview pictures
var update_url := ""                  # --update-url (tests); empty = GitHub
var update_btn: Button
var show_laser := false                 # 3D-3.96: red beam in the direction MoveEye looks (laser.gd, for beginners)
var laser
var show_zones3d := true               # 3D-3.83: makeover 10 - the zones of MoveEye on the ground (overlay3d.gd)
var show_det3d := true                 # 3D-3.83: makeover 11 - the detections of MoveEye over the figures
var overlay                            # overlay3d.gd
var inventar                           # 3D-3.86: inventar.gd - everything the AI knows, to place in the world
var blindmap                           # 3D-3.85: blindmap.gd - blind spots / night rehearsal (makeover 22, 23)
var _fa_saved := {}                    # 3D-3.85: makeover 21 - what farecreate changed
var twin := {}                         # 3D-3.83: makeover 9 - the twin of the real place {name, lat, lon, t}
var news_seen := ""                   # 3D-3.82: «Neu in dieser Version» - the version whose news was seen
var news_popup := true
var news_links := "auto"              # «Links zu Neuerungen» (Entwickler): auto = Projektschalter projekt_veroeffentlicht (ui_gemeinsam.json), on | off
var news                              # news.gd
var dev_updates := true               # 3D-3.81: development phase - ask GitHub every minute, install a new version at once
var _dev := {"t": 0.0, "etag": "", "sha": "", "busy": false}
var auto_update := false              # «Neue Versionen automatisch installieren» (saved; also from the web page of MoveEye)
var update_busy := false
var update_info := ""                 # result of the last check
var next_update_check := 0.0
const UPDATE_EVERY := 600.0           # with auto_update: look on GitHub every 10 minutes
const SETTINGS_FILE := "user://simulator_settings.json"
var scenes
var scene := "camping"
var scene_parent: Node3D
var lamps: Array = []                 # lights of the scene that are on at night
var lamp_mats: Array = []             # lamps that glow at night
var anims: Array = []                 # things of the scene that move: func(dt, t)
var rifle_on := false                 # wildlife watching: the rifle (bloodless, only animals)
var shots := 0
var hits := 0
var points := 0
var crosshair: Control
var shot_sound: AudioStreamPlayer
var hit_sound: AudioStreamPlayer
var phone

# ---- the simulated world --------------------------------------------------------------------------------------
var hour0 := 21.0
var clock0 := 0.0
var speed := 1.0
var weather := "clear"
var wind := 8.0
var ambient := 14.0
var humidity := 70.0
var pressure := 1013.0
var storm_t := 0.0
var thunder := false                  # 3D-3.33: thunderstorm with lightning (also a typical cause of false alarms)
var flash_light: DirectionalLight3D
var _flash_next := 0.0
var _flash_seq: Array = []            # [time, energy] steps of the flash now
var splashes: CPUParticles3D
var _flash_boost := 0.0
var _amb_base := 0.3
var _sky_e_base := 1.0
var moon := 0.6
var moon_auto := true                # 3D-3.98: moon light and shape from the real moon phase of the date
var moon_ph := 0.5
var auto_visitors := true
var next_auto := 0.0
var door_open := false
var gas_on := false
var quality := "nice"
var view_scale := 1.0                 # 3D-3.75: sharpness of the big view on the screen (the pictures for MoveEye stay sharp)
var win_fps := 0                     # 3D-3.75: frames per second of the big view (0 = as fast as it goes)
var auto_perf := true                 # 3D-3.75: too slow? the graphics get lighter by themselves
var cam_wippen := true                 # anim_kamera.gd: die Ansicht wippt beim Gehen der Spielfigur (Maggie)
var foto_tex := true                   # 3.30 bergtal_texturen.gd: Foto-Texturen im Bergtal (Fotos des Besitzers; nie in Lite)
var reduce_motion := "auto"            # 3.23 «Bewegung reduzieren»: auto (wie das Betriebssystem) | an | aus - Logo, Blinki, Wippen, Trailer sanfter
var tour_auto := true                  # 3.23: «Rundgang mit Blinki beim ersten Start von selbst» (System → Gerät & Hilfe, wie MoveEye)
var blinki_on := true                  # 3.23: «Blinki zeigen» (System → Gerät & Hilfe, wie MoveEye)
var _os_motion := -1                   # 3.23: the operating system asks for less motion (1), not (0), unknown (-1)
var grafik_mode := "auto"             # 3D-4.25: «Grafik-Modus» auto | lite | normal (quality.gd; later «hoch»)
var _grafik_keep := ""                 # Notfall-Start (Stabil-Start): --grafik gilt nur für diesen Start - das wird gespeichert
var lite_why := ""                    # why Lite is on («Raspberry Pi 5 …», «von Hand», «wenige Bilder/s») - for «Leistung»
var _lite_slow := false               # auto: the first seconds were very slow -> Lite for this session
var _lite_fps: Array = []
var _lite_t0 := 0.0
var _lite_auto_ok := true             # «--quality» given (Prüfstand): no automatic Lite from the frames per second
var _slow_n := 0
var _perf_t := 0.0
var cam1_yaw := -12.0

# ---- what MoveEye sends -----------------------------------------------------------------------------------
var mw := {"servo": {"pan_deg": 0.0, "tilt_deg": 0.0, "moving": false}, "lights": {"white": false, "ir": false}, "sound": "", "armed": false, "device": ""}
var mw_t := 0.0
var mw_addr := ""

# ---- sensor events ---------------------------------------------------------------------------------------------
var events: Array = []
var next_event_id := 1

# ---- nodes -----------------------------------------------------------------------------------------------------
var env: Environment
var sun: DirectionalLight3D
var moonlight: DirectionalLight3D
var sky_mat: ShaderMaterial              # 3D-3.33: own sky (clouds, stars, moon)
var quality_set := false                  # the quality came from the saved settings (else: chosen by the graphics card)
var detail_alb: NoiseTexture2D            # 3D-3.33: fine structure on every surface (no picture files needed)
var detail_nrm: NoiseTexture2D
var head: Node3D
var rig: Node3D                       # from 3D-3.11: the base of MoveEye - stands still, or drives as the mover
var chassis: Node3D
const MAST_MIN := 0.4                  # 3D-4.x: the limits of the pole (dock slider toolbar.gd, set_mast, the page of MoveEye)
const MAST_MAX := 4.0
var mast_h := HEAD_H                  # 3D-3.57: length of the pole with the camera head (m), adjustable (Mover, Erkunden)
var mast_pole: MeshInstance3D
var mover_on := false                 # «Mover simulieren»: a tracked vehicle under MoveEye, driven by its second stick
var mover_max := 0.8                  # top speed (m/s)
var mover_wheels: Array = []
var mover_dist := 0.0
var _drive_t := 0.0
var head_pitch: Node3D
var white_light: SpotLight3D
var ir_light: SpotLight3D
var vps: Array = []               # SubViewports: cam0, cam1, thermal
var cams: Array = []
var cam_attr: Array = []
var th_env: Environment
var visitors: Node3D
var rain: CPUParticles3D
var snow: CPUParticles3D
var view_cam: Camera3D
var net
var mats := {}
var tmats := {}
var tmat_fixed_cache := {}
var grass_mat: ShaderMaterial
var foliage_mats: Array = []
var window_mat: StandardMaterial3D
var door_node: Node3D
var door_light: OmniLight3D
var noise_tex: NoiseTexture2D

# ---- pictures --------------------------------------------------------------------------------------------------
var jpgs := [PackedByteArray(), PackedByteArray()]
var frame_no := [0, 0]
var last_cap := [0.0, 0.0, 0.0]
var snap_want := [0.0, 0.0]
var thermal := PackedFloat32Array()
var th_srgb := true
var th_bg_raw := false
var gain := [1.0, 1.0]
# ---- the picture of the cameras (from 3D-2.5; saved) ----
var lens_noise := 0.5                 # grain, stronger at night
var lens_vignette := 0.3              # dark corners
var lens_drops := true                # raindrops on the lens when it rains
var insects_on := true                # insects fly round the light at night (false alarms, as in reality)
# difficult conditions (3D-3.27): each can be switched on by hand or by the test run «Schwierige Bedingungen»
var cond := {"glare": false, "drops": false, "web": false, "headlights": false, "shadows": false, "ir": false, "fogged": false, "dirt": false, "shake": false, "net": false}
var _net_hold := 0.0                  # 3D-3.74: bad Wi-Fi - the picture stands still until then
var _next_headlight := 0.0
var night_gain := 2.5                 # how much a camera may amplify at night (real cameras: limited -> dark, grainy)
var ir_range := 10.0                  # reach of the infrared light (m); 3D-4.x P1: 10 m like a small 3 W 850 nm module (was 14)
var sound_on := true                  # the sounds of the world go to the microphone of MoveEye (from 3D-2.6)
var sounds: Array = []                # [dB at 1 m, position, until]
var sound_ev: Array = []              # 3D-3.98: short sounds for MoveEye [{id, kind: clap | sneeze | voice | shout, n, db, t}]
var sound_ev_id := 0
const SOUND_EV_DB := {"clap": -13.0, "sneeze": -16.0, "voice": -36.0, "shout": -12.0}   # loudness at 1 m (dBFS ≈ SPL − 100; real-pir-ton: was -4 / -10 / -18 / -4)
var mw_det := {}                      # what MoveEye detects right now (from 2.93.3: persons, present, noise)
var mw_det_t := 0.0
var lens_mats: Array = []
var camfx_mats: Array = []            # 3D-3.94: camfx.gdshader per camera (realism.gd sets it)
var realism                           # realism.gd
var simreal                           # simreal.gd (3D-4.4): Pi 5, lens, infrared, thermal, false alarms, difficult visitors
var thermsensor                       # thermsensor.gd (3D-4.26, P2): the thermal module like the real Thermal-90 (noise, drift, optics, AGC)
var waerme_welt                       # waerme_welt.gd (3D-4.26, P3): engines cool down, the person in the tent, lamps (table: waerme.gd)
var camphys                           # camphys.gd (3D-4.x P1): exposure / gain / noise / NoIR colours of the Camera Module 3 NoIR
var szenen                            # szenenplus.gd (3D-4.x): Voller Campingplatz, Tarnen und Kriechen, Velodieb
var smalltv                           # smalltv.gd (3D-4.19): virtueller Zusatz-Bildschirm GeekMagic SmallTV Ultra (MoveEye 552)
var fenster                           # fenster.gd (Paket «Fenster»): ein Rahmen für alle schwebenden Fenster (ziehen, Grösse, ✕, Liste «Fenster»)
var gehaeuse                          # gehaeuse.gd (real-gehaeuse): die vereinfachten echten Teile des Gehäuses v5.1 am Gerät
var werkstatt = null:                 # werkstatt.gd (real-gehaeuse): Mehr → Werkstatt (Gehäuse drehen, zerlegen, Montage)
	get:                              # Vorschlag 24: made at its first use (Mehr → Werkstatt, /control «werkstatt»), not at the start
		if werkstatt == null and is_inside_tree():
			werkstatt = load("res://scripts/werkstatt.gd").new()
			werkstatt.main = self
			add_child(werkstatt)
		return werkstatt
var head_box: MeshInstance3D          # the dark box of the head (hidden while the real case is shown, gehaeuse.gd)
var tasten                            # tasten.gd: + / − zoomen, Bild ↑ / ↓ blättern, Pfeile drehen, F1 Tasten-Hilfe (ohne Mausrad)
var view_zoom := 1.0                  # tasten.gd: + / − in the camera views 1 / 2 (only the picture on the screen)
var statusled                         # statusled.gd: Status-LED auf dem Kopf + Fenster «Gerät» mit den Tasten (MoveEye 163a / 599c)
var weit                              # weitwinkel.gd (3D-4.17): camera 1 = the wide camera with its mount (mast, base, head front / rear)
var nacht                             # nachtlauf.gd (Paket «Nacht-Testlauf»): eine ganze Nacht mit Wahrheit, von MoveEye gestartet
var parcours                          # parcours.gd (3D-4.18): «Verfolgungs-Parcours» - lessons, ground truth, game «Entkomme der Kamera»
var zwilling                          # zwilling.gd (3D-4.4): «Dein Platz als Zwilling» - photo / panorama of the real place
var fauna                             # fauna.gd (3D-3.95)
var entdecken                         # entdecken.gd (Erlebniswelt 20–23): register() / mark_found() / is_found() / count() of the scenes
var spielbereich                      # spielbereich.gd (Paket «Spielbereich»): start screen «Spielen» - adventures, badges, level, Blinki
var objplus                           # objekte_plus.gd (3D-4.x «Gegenstände»): wind, light, lures, valuables of the catalogue
var gelaende                          # gelaende.gd (3D-4.x real-gelaende): hills and hollows, paths, cloud shadows (vegetation.gd: plants)
var inhalte                           # inhalte.gd (F2): Foto-Texturen und HDRI-Himmel (CC0), nachgeladen, nicht in Lite
var sicherung                         # sicherung.gd: System → Sicherung (ZIP auf dem PC / USB-Stick / in MoveEye, wiederherstellen)
var umgebung                          # umgebung.gd (3D-4.x): lamps, puddles, smoke, insects, plants, tracks, robots, pets
var statisten                         # statisten.gd: background people - goals, things to do, groups, react to the player, keep away from the games
var menschen                          # menschen.gd (P10): people behave like real ones - gaits, groups, the day of a campsite, API for scenarios
var tiere                             # tiere.gd (Paket «Tiere»): animals behave like real ones (flee, curl up, pounce …)
var fahrzeuge                         # fahrzeuge.gd (Paket «Fahrzeuge»): speed, lights, glare, doors, parking, engine heat
var licht                             # licht.gd («Licht & Nacht»): sun, twilight, moon, stars, light pollution, lamps, glare
var jahreszeiten                      # jahreszeiten.gd («Jahreszeiten & Tageslauf»): season, bare trees, blossom, leaves, fog, snow, occupancy
var wetter                            # wetter.gd (real-wetter): rain strength, fog visibility, ground fog, snow cover, lens drops, lightning
var wind_fx                           # F6 wind_fx.gd: grass, bushes, crowns and tents move in the wind (vertex shaders)
var colors                            # colors.gd (3D-3.97): natural colours, materials, seasons, blue hour
var colors_on := true
var tracks                            # tracks.gd (3D-3.98)
var seasons_on := true
var sleeper                           # sleeper.gd (3D-3.96): the person in the bed of the bedroom scene
var zimmertiere                       # zimmertiere.gd (Erlebniswelt «mehr Tiere drinnen»): hamster, budgie, spider in the bedroom
var fauna_on := true
var servo                             # servo.gd («Servo-Mechanik»): the two MG90S of the head with «Servos wie echt»
var pan_vel := 0.0                    # rad/s of the head (for the blur while turning; with «Servo-Mechanik» incl. overshoot)
var tilt_vel := 0.0
var _srv := {"v": 0.0, "wob": 0.0, "t": 0.0, "dir": 1.0}
var expo_mats: Array = []             # exposure quads (multiply) in front of camera 0 / 1
var night_envs: Array = [null, null]  # [grey (infrared), little colour] - copies of env, renewed every 0.5 s at night
var insects: CPUParticles3D
var capturing := false
var preview_on := true
var th_preview: ImageTexture

# ---- remote control (CONTROL protocol 1, shared by the window and the web page of MoveEye) ---------------------
var controls: Array = []
var ui_rows := {}
var status_label: Label
var group_bodies := {}                # 3D-3.43: group name -> body of its card (the symbol shows when something is on)
var _group_state := {}
var conn_body: Control                # the card «Verbindung» (symbol and title show the state)
var cam_body: Control                 # 3D-3.50: the cards «Kameras» and «Werkzeuge» (symbol + arrow green while working)
var tools_body: Control
var testen_train: VBoxContainer       # 3D-4.21: card «Testen» → «Trainingsbilder» (quick tile «Lernen»)
var einbruch                          # einbruch.gd (Paket «real-einbruch»): Einbruch-Abläufe mit Bewertung
var testen_einbruch: VBoxContainer    # card «Testen» → «Einbruch-Abläufe»
var testen_stoer: VBoxContainer       # 30.10.2026: card «Testen» → «Störungen» (simint.gd: servos, 5 V, I2C)
var testen_measure: VBoxContainer     # 3D-4.x: card «Testen» → «Erkennung messen» (also the test run controls)
var testen_rec: VBoxContainer         # 3D-4.x: card «Testen» → «Aufnahme …» (the recorder)
var _conn_state := -1
var stream_on := false                     # sending to MoveEye: off at the start, the user switches it on in the window
var stream_last := false                   # 3D-3.65: was sending switched on the last time? then on again at the start (also after an update)
var stream_port := 8765
var stream_cb: CheckButton
var stream_note: Label

var obj := {"door": Vector3.ZERO, "pir": Vector3.ZERO, "bike": Vector3.ZERO}   # set by the scene
const SERVO_DEG_S := 200.0            # how fast the pan / tilt servos turn (MG90S: about 0.1 s per 60°, with load slower)
var next_birds := 0.0
# ---- settings for the visitors (from 3D-2.0; saved, also on the web page of MoveEye) ----
var visit_rate := 1.0                 # how often visitors come by themselves (× the scene's normal rate)
var max_visitors := 12
var visitor_speed := 1.0
var mix := "mixed"                    # mixed | more_animals | more_people | animals | people
var flee_light := true                # animals flee from the white light at night
var flee_sound := true                # ... and from the siren
var privat_on := true                 # Wunsch Nr. 2: normal visitors keep off your pitch (privatplatz.gd)
var privat                            # privatplatz.gd: the private circle round MoveEye and its tent
# ---- parts of main.gd in their own files (Vorschlag 24): main_*.gd, loaded at their first use ----
var _mods := {}                       # "steuerung" -> main_steuerung.gd … (load, not preload: parsed only when needed)


func _mod(n: String):
	var m = _mods.get(n)
	if m == null:
		m = load("res://scripts/main_%s.gd" % n).new()
		m.main = self
		_mods[n] = m
	return m


func _ready() -> void:
	if Updater.old_name_forward():               # 3D-4.24: started as MotionWatch3D.exe - MoveEyeSim3D.exe takes over
		get_tree().quit()
		return
	preload("res://scripts/werk.gd").apply_pending()    # Werksrücksetzung: right after the restart, before anything reads user://
	preload("res://scripts/sicherung.gd").apply_pending(VERSION)   # System → Sicherung: a restore waits for this start (sicherung.gd)
	randomize()
	_no_pad_ui_nav()
	colors = preload("res://scripts/colors.gd").new()        # 3D-3.97: natural colours, materials, seasons (before the world is built)
	colors.main = self
	add_child(colors)
	tracks = preload("res://scripts/tracks.gd").new()        # 3D-3.98: tracks in the snow
	tracks.main = self
	add_child(tracks)
	clock0 = Time.get_unix_time_from_system()
	var t := Time.get_datetime_dict_from_system()
	hour0 = t.hour + t.minute / 60.0
	var port := 8765
	var args := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--port" and i + 1 < args.size():
			port = int(args[i + 1])
		elif args[i] == "--hour" and i + 1 < args.size():
			hour0 = float(args[i + 1])
		elif args[i] == "--quality" and i + 1 < args.size():
			quality = args[i + 1]
		elif args[i] == "--scene" and i + 1 < args.size():
			scene = args[i + 1]
		elif args[i] == "--solo":
			welt_solo = true                         # 3D-4.x: the old scenes alone, without their world (Prüfstand)
	_lite_auto_ok = not "--quality" in args
	set_process(false)
	set_process_unhandled_input(false)
	if _vm_needs_angle(args):
		return
	if GrafikHoch.start_check(self, args):     # F1: «Hoch» saved but OpenGL running - start again once with Forward+
		return
	in_vm = _in_vm()
	if in_vm and not "--quality" in args:
		quality = "simple"                      # virtual machine: no real graphics card - the light graphics by default
	DisplayServer.window_set_title(("%s · Live" % Versionen.label(VERSION)) if Versionen.is_new(VERSION) else ("3D-Simulator Live · %s" % VERSION))
	var ic := load("res://icon_sim3d.png")              # the window icon (3D-3.28; 3D-3.63: the orange MoveEye symbol)
	if ic is Texture2D:
		DisplayServer.set_icon((ic as Texture2D).get_image())
	var k := args.find("--update-url")
	if k >= 0 and k + 1 < args.size():
		update_url = args[k + 1]
	_load_settings()
	hoch = GrafikHoch.new()                    # F1 «Grafikstufe Hoch» (own setting file user://grafik_stufe.json)
	hoch.main = self
	add_child(hoch)
	if hoch.stufe == "hoch":                   # the file of grafik_hoch.gd decides (it falls back to Normal if Vulkan failed)
		grafik_mode = "hoch"
	elif grafik_mode == "hoch":
		grafik_mode = "normal"
	home_load()                                # 3D-3.73: «Mein Zuhause»
	realism = preload("res://scripts/realism.gd").new()      # 3D-3.94: cameras like real ones (and like the real one of MoveEye)
	realism.main = self
	add_child(realism)
	simreal = preload("res://scripts/simreal.gd").new()      # 3D-4.4: closer to the real device (every part can be switched off)
	simreal.main = self
	add_child(simreal)
	thermsensor = preload("res://scripts/thermsensor.gd").new()   # 3D-4.26 «Wärmebild wie echt» (P2)
	thermsensor.main = self
	add_child(thermsensor)
	waerme_welt = preload("res://scripts/waerme_welt.gd").new()   # 3D-4.26 heat in the world (P3)
	waerme_welt.main = self
	add_child(waerme_welt)
	camphys = preload("res://scripts/camphys.gd").new()      # 3D-4.x P1: the sensor of the Camera Module 3 NoIR (exposure, gain, noise)
	camphys.main = self
	add_child(camphys)
	szenen = preload("res://scripts/szenenplus.gd").new()   # 3D-4.x: the new scenes (neighbours, camouflage, bike thief)
	szenen.main = self
	add_child(szenen)
	weit = preload("res://scripts/weitwinkel.gd").new()      # 3D-4.17: the wide camera (camera 1) and its mount
	weit.main = self
	add_child(weit)
	tasten = preload("res://scripts/tasten.gd").new()        # Tasten statt Mausrad (Touchpad ohne Scrollfunktion)
	tasten.main = self
	add_child(tasten)
	statusled = preload("res://scripts/statusled.gd").new()   # Status-LED auf dem Kopf, Tasten «Schutz» / «Alarm quittieren»
	statusled.main = self
	add_child(statusled)
	smalltv = preload("res://scripts/smalltv.gd").new()     # 3D-4.19: virtueller SmallTV (gleiche HTTP-Schnittstelle, Kachel im Fenster)
	smalltv.main = self
	add_child(smalltv)
	parcours = preload("res://scripts/parcours.gd").new()   # 3D-4.18: the tracking parcours (scene «parcours»)
	parcours.main = self
	add_child(parcours)
	privat = preload("res://scripts/privatplatz.gd").new()  # Wunsch Nr. 2: normal visitors keep off your pitch (burglars do not)
	privat.main = self
	add_child(privat)
	einbruch = preload("res://scripts/einbruch.gd").new()   # Einbruch-Abläufe: auskundschaften, ablenken, stehlen - wann warnt MoveEye?
	einbruch.main = self
	add_child(einbruch)
	nacht = preload("res://scripts/nachtlauf.gd").new()     # Nacht-Testlauf: plan, truth (MoveEye starts it, part 579b)
	nacht.main = self
	add_child(nacht)
	zwilling = preload("res://scripts/zwilling.gd").new()    # 3D-4.4: your place as a twin (photo behind the scene)
	zwilling.main = self
	add_child(zwilling)
	objplus = preload("res://scripts/objekte_plus.gd").new()  # 3D-4.x «Gegenstände»: what the new things of the catalogue do
	objplus.main = self
	add_child(objplus)
	wind_fx = preload("res://scripts/wind_fx.gd").new()       # F6: wind in grass, bushes, crowns, tents (before the scene is built)
	wind_fx.main = self
	add_child(wind_fx)
	inhalte = preload("res://scripts/inhalte.gd").new()       # F2: real photo surfaces and sky (downloaded once, fallback = code)
	inhalte.main = self
	add_child(inhalte)
	sicherung = preload("res://scripts/sicherung.gd").new()   # System → Sicherung: ZIP auf dem PC / USB-Stick / in MoveEye, wiederherstellen
	sicherung.main = self
	add_child(sicherung)
	umgebung = preload("res://scripts/umgebung.gd").new()     # 3D-4.x: the surroundings like real (every part can be switched off)
	umgebung.main = self
	add_child(umgebung)
	menschen = preload("res://scripts/menschen.gd").new()     # P10 «Menschen-Verhalten»: gaits, variety, groups, daily routine, scenario API
	menschen.main = self
	add_child(menschen)
	statisten = preload("res://scripts/statisten.gd").new()   # Paket «Statisten»: Hintergrund-Figuren (Ziele, Tätigkeiten, Gruppen, Spieler, Spielmodi)
	statisten.main = self
	add_child(statisten)
	tiere = preload("res://scripts/tiere.gd").new()           # Paket «Tiere»: real behaviour of the animals (with «Tiere wie echt»)
	tiere.main = self
	add_child(tiere)
	fahrzeuge = preload("res://scripts/fahrzeuge.gd").new()   # Paket «Fahrzeuge»: vehicles like real
	fahrzeuge.main = self
	add_child(fahrzeuge)
	licht = preload("res://scripts/licht.gd").new()           # «Licht & Nacht»: sky and lights like real
	licht.main = self
	add_child(licht)
	jahreszeiten = preload("res://scripts/jahreszeiten.gd").new()   # «Jahreszeiten & Tageslauf»: the season shared by all scenes
	jahreszeiten.main = self
	add_child(jahreszeiten)
	wetter = preload("res://scripts/wetter.gd").new()         # real-wetter: weather closer to physics (wetter.gd, linse.gd)
	wetter.main = self
	add_child(wetter)
	fauna = preload("res://scripts/fauna.gd").new()          # 3D-3.95: birds and bats
	fauna.main = self
	add_child(fauna)
	fauna.on = fauna_on
	laser = preload("res://scripts/laser.gd").new()          # 3D-3.96: «Blickrichtung» (only for the operator)
	laser.main = self
	add_child(laser)
	sleeper = preload("res://scripts/sleeper.gd").new()      # 3D-3.96: the bedroom (wake-up alarm of MoveEye)
	sleeper.main = self
	add_child(sleeper)
	if scene == "schlafzimmer" and scenes != null and scenes.data.has("bed") and is_instance_valid(scenes.data["bed"]):
		sleeper.place(scenes.data["bed"])
	zimmertiere = preload("res://scripts/zimmertiere.gd").new()   # Erlebniswelt «mehr Tiere drinnen»: animals in the bedroom
	zimmertiere.main = self
	add_child(zimmertiere)
	tunnel = preload("res://scripts/tunnel.gd").new()        # 3D-3.45: out through the firewall to MoveEye
	tunnel.main = self
	add_child(tunnel)
	tunnel.host = tunnel_host
	tunnel.code = tunnel_code
	tunnel.set_on(tunnel_on)
	var at_boot := "--autostart" in args             # started with the PC
	if at_boot and not "--scene" in args and last_scene != "":
		scene = last_scene
	if not ("--no-update" in args or "--updated" in args or (at_boot and not auto_update)):   # at the autostart nobody is there to answer      # first: is there a newer version? (update.gd)
		var up = Updater.new()
		up.auto = auto_update
		var held := _hold_children()             # Startfix 31.10.2026: während der Suche läuft noch keine Welt - die Teile warten
		up.process_mode = Node.PROCESS_MODE_ALWAYS
		add_child(up)
		await up.check(VERSION, update_url)
		_release_children(held)
		up.queue_free()
	_make_lut(true)
	noise_tex = NoiseTexture2D.new()
	var fn := FastNoiseLite.new()
	fn.frequency = 0.02
	noise_tex.noise = fn
	noise_tex.seamless = true
	noise_tex.width = 256
	noise_tex.height = 256
	_build_environment()
	geo = Geo.new()
	geo.main = self
	add_child(geo)
	gelaende = preload("res://scripts/gelaende.gd").new()   # 3D-4.x: before the first scene (it asks for the hills)
	gelaende.main = self
	add_child(gelaende)
	entdecken = preload("res://scripts/entdecken.gd").new()   # Erlebniswelt 20–23: Entdeckungsbuch, Blinki-Hinweise, Fotomodus (before the scene registers)
	entdecken.main = self
	add_child(entdecken)
	spielbereich = preload("res://scripts/spielbereich.gd").new()   # Paket «Spielbereich»: the start screen «Spielen» (quick tile)
	spielbereich.main = self
	add_child(spielbereich)
	_build_world()
	_build_head()
	gehaeuse = preload("res://scripts/gehaeuse.gd").new()     # real-gehaeuse: the real case v5.1 on the head (cameras stay where they are)
	gehaeuse.main = self
	add_child(gehaeuse)
	# werkstatt.gd (Mehr → Werkstatt): made at its first use (var werkstatt, Vorschlag 24)
	_build_viewports()
	_build_weather()
	_build_effects()
	_build_lens()
	_build_fireflies()
	visitors = Node3D.new()
	add_child(visitors)
	_build_view_camera()
	stream_port = port
	game = Game.new()
	game.main = self
	add_child(game)
	life = Life.new()
	life.main = self
	add_child(life)
	stories = preload("res://scripts/events.gd").new()    # little stories (3D-3.40)
	stories.main = self
	add_child(stories)
	visitlog = preload("res://scripts/visitlog.gd").new()   # 3D-3.80
	visitlog.main = self
	add_child(visitlog)
	surprise = preload("res://scripts/surprise.gd").new()   # 3D-3.75
	surprise.main = self
	add_child(surprise)
	simwerte = preload("res://scripts/power.gd").new()      # Simulator-Werte: UPS HAT, Pi heat, «WLAN weg» (sent to MoveEye)
	simwerte.main = self
	add_child(simwerte)
	simint = preload("res://scripts/simint.gd").new()      # 30.10.2026: siren on the PC + microphone, servo faults, thermal model
	simint.main = self
	add_child(simint)
	pir = preload("res://scripts/pir.gd").new()             # real-pir-ton: PIR at the device (AS312, 100°, 3–5 m)
	pir.main = self
	add_child(pir)
	mikro = preload("res://scripts/mikrofon.gd").new()      # real-pir-ton: microphone (1/r, direction, ground) + sounds of the surroundings
	mikro.main = self
	add_child(mikro)
	klang = preload("res://scripts/klang.gd").new()         # Spielton: buses, music, moments - only in games and stories (klang.gd)
	klang.main = self
	add_child(klang)
	servo = preload("res://scripts/servo.gd").new()        # «Servo-Mechanik»: MG90S model of the head (with «Servos wie echt»)
	servo.main = self
	add_child(servo)
	sym_node = Sym.new()                               # 3D-4.22: drawn symbols instead of missing emoji (symbole.gd)
	sym_node.main = self
	add_child(sym_node)
	schnitt = preload("res://scripts/schnittstelle.gd").new()   # Aufräumen 2: one field list with MoveEye (schnittstelle.json), armed / relays shown
	schnitt.main = self
	add_child(schnitt)
	recorder = Recorder.new()
	recorder.main = self
	add_child(recorder)
	dev2 = Device.new()
	dev2.main = self
	add_child(dev2)
	testrun = TestRun.new()
	testrun.main = self
	add_child(testrun)
	horror = preload("res://scripts/bergtal_horror.gd").new()   # Bergtal · Horror-Modus «Das Hospiz» (mit Passwort, bergtal_horror.gd)
	horror.main = self
	add_child(horror)
	spieltest = preload("res://scripts/spieltest.gd").new()   # Paket «Spieltest-Assistent»: beobachtet die Spiele (Mehr → Entwickler → Spieltest)
	spieltest.main = self
	add_child(spieltest)
	maggie = preload("res://scripts/maggie_story.gd").new()    # «Maggie und der Bergkristall» (Geschichte unter «Spielen», maggie_story.gd)
	maggie.main = self
	add_child(maggie)
	_register_controls()
	_order_controls()
	mwpc = Mwpc.new()
	mwpc.main = self
	add_child(mwpc)
	_build_ui()
	fenster = preload("res://scripts/fenster.gd").new()   # Paket «Fenster»: Karte, Kompass, Livebild … in einem gemeinsamen Rahmen
	fenster.main = self
	add_child(fenster)
	fenster.setup_sim()
	if entdecken != null:
		entdecken.join_fenster(fenster)              # 3D-4.27: the Blinki hint in the same frame
	mwpc.changed.connect(_on_mwpc)
	_on_mwpc()
	next_update_check = now() + UPDATE_EVERY
	if "--mwpc" in args:                          # after an update: MoveEye on this PC was running - start it again
		mwpc.start.call_deferred()
	net = Net.new()
	net.main = self
	add_child(net)
	if "--stream" in args or at_boot or stream_last:   # start sending at once (autostart, update, or it was on the last time)
		set_stream(true)
		if not stream_on:
			_stream_retry(60)                     # 3D-3.65: after an update the old simulator still holds the port for a moment
	autostart_on = Autostart.is_on()
	if autostart_on:
		Autostart.repair()                         # the folder of the program was moved: the autostart follows it (3D-4.24: also the old name)
	if Autostart.current(true) == "":              # 3D-4.24: MotionWatch3D.exe (.old) is not needed any more - removed a little later
		for d in [4.0, 20.0, 90.0]:                # (the old simulator may still be closing)
			get_tree().create_timer(d).timeout.connect(func(): Updater.remove_old_name_files())
	if "--renamed" in args:
		start_info = "Neu heisst die Datei MoveEyeSim3D.exe (die alte MotionWatch3D.exe wird entfernt). Der Simulator beginnt mit frischen Einstellungen."
	if at_boot:
		if autostart_mwpc and not "--mwpc" in args:
			mwpc.start.call_deferred()
		if autostart_min:
			get_tree().create_timer(1.5).timeout.connect(func(): DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_MINIMIZED))
		if autostart_lock and not "--updated" in args:
			get_tree().create_timer(6.0).timeout.connect(func(): Autostart.lock_screen())
	if not quality_set and not "--quality" in args:
		quality = auto_quality()
		print("graphics card: %s -> quality %s" % [RenderingServer.get_video_adapter_name(), quality])
	_apply_quality()
	if view_scale < 1.0:
		set_view_scale(view_scale)
	var gi := args.find("--grafik")                   # 3D-4.25: --grafik auto | lite | normal | hoch (for tests)
	if gi >= 0 and gi + 1 < args.size():
		_grafik_keep = grafik_mode                      # Notfall-Start: nur für diesen Start, gespeichert bleibt die eigene Wahl
		grafik_mode = Quality.mode_id(args[gi + 1])
		if hoch != null and grafik_mode != "hoch":
			hoch.stufe = "normal"                       # only for this start (the file stays)
	_lite_t0 = now()
	lite_update()
	_calibrate_thermal()
	next_auto = now() + 20.0
	for i in range(args.size()):
		if args[i] == "--phone":                  # start with the phone open (optionally: --phone http://address:5000)
			if i + 1 < args.size() and args[i + 1].begins_with("http"):
				phone.addr.text = args[i + 1]
			get_tree().create_timer(2.0).timeout.connect(func(): phone.open())
	DisplayServer.window_set_title((("%s · Live" % Versionen.label(VERSION)) if Versionen.is_new(VERSION) else ("3D-Simulator Live · %s" % VERSION)) + " (Port %d)" % port)
	_fps0 = Engine.max_fps
	mini_box = preload("res://scripts/mini.gd").new()      # minimize = small box, the simulator keeps drawing
	mini_box.main = self
	add_child(mini_box)
	_restore_window(args)
	if OS.get_environment("MWSIM_PRINT_RESTART") == "1":         # only for tests: which options an update restart would pass on
		get_tree().create_timer(5.0).timeout.connect(func(): print("RESTART_ARGS: ", " ".join(restart_args())))
	set_process(true)
	set_process_unhandled_input(true)
	preload("res://scripts/trailer.gd").from_args(self, args)   # --trailer grossvater|maggie (werkzeuge/trailer_aufnehmen.sh)


func _hold_children() -> Dictionary:
	"""Startfix 31.10.2026: _ready wartet auf die Update-Suche (await), die Welt (Szene, Boden, Kopf, Kameras) entsteht erst
	danach. In dieser Zeit liefen _process / _physics_process der schon angehängten Teile gegen eine halbe Welt - in der
	exportierten .exe wird ein Aufruf auf einer typisierten null-Variablen zum harten Absturz (kein Skriptfehler wie im
	Editor). Darum ruhen die Teile, bis die Suche fertig ist; gibt den alten process_mode je Teil zurück."""
	var held := {}
	for ch in get_children():
		held[ch] = ch.process_mode
		ch.process_mode = Node.PROCESS_MODE_DISABLED
	return held


func _release_children(held: Dictionary) -> void:
	for ch in held:
		if is_instance_valid(ch):
			ch.process_mode = held[ch]


func _in_vm() -> bool:
	var vn := (RenderingServer.get_video_adapter_vendor() + " " + RenderingServer.get_video_adapter_name()).to_lower()
	for k in ["vmware", "svga3d", "virtualbox", "vboxsvga", "parallels", "qxl", "virgl", "llvmpipe", "microsoft basic render"]:
		if vn.contains(k):
			return true
	return false


func _vm_needs_angle(args: Array) -> bool:
	"""In a virtual machine (VMware, VirtualBox ...) the OpenGL driver of Windows refuses the shaders of Godot (only the sky is
	seen). ANGLE (OpenGL over Direct3D 11) works around it: start once more with it. --no-angle switches this off."""
	if OS.get_name() != "Windows" or "--angle-tried" in args or "--no-angle" in args:
		return false
	var vn := (RenderingServer.get_video_adapter_vendor() + " " + RenderingServer.get_video_adapter_name()).to_lower()
	if vn.contains("angle"):
		return false
	var vm := false
	for k in ["vmware", "svga3d", "virtualbox", "vboxsvga", "parallels", "qxl", "virgl"]:
		if vn.contains(k):
			vm = true
	if not vm:
		return false
	print("virtual machine (%s): starting again with ANGLE" % vn)
	var a := OS.get_cmdline_args()
	for x in ["--rendering-driver", "opengl3_angle", "--"]:
		a.append(x)
	a.append_array(OS.get_cmdline_user_args())
	a.append("--angle-tried")
	# Startfix 31.10.2026: kein release_ports() hier - noch ist nichts offen, und dessen _save_settings() hätte VOR
	# _load_settings die gespeicherten Einstellungen mit den Standardwerten überschrieben (bei jedem Start in einer VM)
	OS.create_process(OS.get_executable_path(), a)
	get_tree().quit()
	return true


const ALT_PORTS := [8775, 8785, 8795]       # 3D-3.68: if 8765 stays busy (a process holds it), send on one of these


func _stream_retry(left: int, tries := 0) -> void:
	"""the port is still busy (the old simulator closes after an update): try again every second; after 8 tries a
	free port of ALT_PORTS (MoveEye finds it by the "here is a simulator" message, the tunnel follows it)"""
	if stream_on or left <= 0 or (stream_cb != null and not stream_last and not "--stream" in OS.get_cmdline_user_args()):
		return
	await get_tree().create_timer(1.0).timeout
	if stream_on:
		return
	set_stream(true, tries >= 8)
	if not stream_on:
		_stream_retry(left - 1, tries + 1)
	else:
		print("sending to MoveEye: port %d" % net.port)


var _sw_t := 0.0
var _sw_tries := 0
var _old_killed := false
var _released_t := -100.0              # 3D-3.98: release_ports() was called (an update / restart is starting)


func _stream_watch() -> void:
	"""3D-3.75: sending should be on (switched on the last time, the tunnel is on, or --stream) but the port is busy -
	after an update the old simulator (or a program it started, e.g. MoveEye on this PC) may still hold port 8765.
	Try again every 3 s; after 5 s stop the old simulator (--old-pid), after the 3rd try take a spare port (8775 …).
	Never gives up (before 3D-3.75 the tunnel switched sending on only once)."""
	var want: bool = stream_last or tunnel_on or "--stream" in OS.get_cmdline_user_args()
	if tunnel_on and tunnel != null and not tunnel.on and now() - _released_t > 20.0 and tunnel_host != "":
		tunnel.set_on(true)                           # 3D-3.98: an update was given up after release_ports: tunnel on again
	if stream_on or not want or net == null:
		_sw_tries = 0
		return
	if now() - _sw_t < 3.0:
		return
	_sw_t = now()
	_sw_tries += 1
	var oi := OS.get_cmdline_user_args().find("--old-pid")
	if not _old_killed and _sw_tries >= 2 and oi >= 0 and oi + 1 < OS.get_cmdline_user_args().size():
		var op := int(OS.get_cmdline_user_args()[oi + 1])
		if op > 0 and op != OS.get_process_id():
			_old_killed = true
			OS.kill(op)                                   # the old simulator hangs while closing: stop it
			print("old simulator %d stopped (port still busy)" % op)
	set_stream(true, _sw_tries >= 3)
	if stream_on:
		print("sending to MoveEye: port %d (try %d)" % [net.port, _sw_tries])
		_sw_tries = 0


func _firewall_allow() -> void:
	"""3D-3.92: Windows asks for admin rights once (UAC) and adds an inbound rule for this simulator (private networks)"""
	var exe := OS.get_executable_path().replace("/", "\\")
	var rule := "advfirewall firewall add rule name=\"MoveEye Simulator\" dir=in action=allow program=\"%s\" enable=yes profile=private,domain" % exe
	var ps := "Start-Process netsh -Verb RunAs -WindowStyle Hidden -ArgumentList '%s'" % rule.replace("'", "''")
	var pid := OS.create_process("powershell.exe", ["-NoProfile", "-WindowStyle", "Hidden", "-Command", ps])
	start_info = "Windows fragt jetzt nach Adminrechten – «Ja» wählen. Danach findet MoveEye den Simulator ohne Tunnel." if pid > 0 else "Konnte die Firewall-Freigabe nicht starten."


func release_ports() -> void:
	"""3D-3.68: before starting a new simulator (update, graphics restart): close every listening port. On Windows the
	new process would otherwise get them too and its own «An MoveEye senden» stays «Port 8765 is busy»."""
	_save_settings()                                  # 3D-3.76: the time of the scene for the new simulator
	if net != null:
		net.stop()
	_released_t = now()
	if tunnel != null and tunnel.on:                  # 3D-3.98: close the tunnel lines too - on Windows the new simulator would
		tunnel.set_on(false)                          # inherit them, MoveEye kept sending «GO» into lines nobody reads
	if game != null and game.open:
		game.set_open(false)


func set_stream(on: bool, alt := false) -> void:
	if on:
		net.start(stream_port)
		if not net.listening and alt:
			for p in ALT_PORTS:
				net.start(p)
				if net.listening:
					break
		stream_on = net.listening
	else:
		net.stop()
		stream_on = false
		mw_t = 0.0
	if stream_cb != null:
		stream_cb.set_pressed_no_signal(stream_on)
		stream_cb.text = "An MoveEye senden (Port %d)" % (net.port if stream_on else stream_port)
	_update_status()


func _make_lut(srgb: bool) -> void:
	"""3D-4.26: the thermal picture is a 14-bit code in the upper half of two colour channels (red = 128 + high 7 bits,
	green = 128 + low 7 bits, -40 … +400 °C, see shaders/thermal_inc.gdshaderinc). The dark end of a colour channel is not
	reliable (some renderers squeeze 0 … 100, measured with a ramp in _calibrate_thermal) - the upper half is.
	th_inv[stored byte] = the byte the shader wrote (identity until the calibration measured the renderer).
	srgb: the renderer turns colours into sRGB - the shaders then write the inverse (th_srgb_out) so the bytes stay right."""
	th_srgb = srgb
	th_uniforms({"th_srgb_out": 1.0 if srgb else 0.0})
	if th_inv.size() != 256:
		th_inv = PackedInt32Array()
		for i in range(256):
			th_inv.append(i)
	th_hi = PackedFloat32Array()
	th_lo = PackedFloat32Array()
	for i in range(256):
		th_hi.append(_th_byte(i) * 128.0 * TH_STEP)       # °C of the stored byte in red / green (+ -40 at the end)
		th_lo.append(_th_byte(i) * TH_STEP)


const TH_STEP := 440.0 / 16383.0     # °C per step of the 14-bit code
var th_inv := PackedInt32Array()
var th_hi := PackedFloat32Array()
var th_lo := PackedFloat32Array()
var th_mats: Array = []              # 3D-4.26: every material with a thermal shader (they share th_air, th_atm_k, th_srgb_out)
var th_u := {"th_air": 15.0, "th_atm_k": 0.0, "th_srgb_out": 0.0}


func th_reg(m: ShaderMaterial) -> ShaderMaterial:
	"""a new thermal material: it gets the shared values now and on every change (th_uniforms). (Plain uniforms: the
	global shader uniforms of Godot gave wrong values in the Compatibility renderer.)"""
	for k in th_u:
		m.set_shader_parameter(k, th_u[k])
	th_mats.append(weakref(m))
	return m


func th_uniforms(vals: Dictionary) -> void:
	"""the shared values of all thermal materials (only what changed; forgotten materials are dropped)"""
	var ch := {}
	for k in vals:
		if absf(float(vals[k]) - float(th_u.get(k, 0.0))) > 1e-6:
			ch[k] = float(vals[k])
			th_u[k] = float(vals[k])
	if ch.is_empty():
		return
	var keep: Array = []
	for w in th_mats:
		var m = w.get_ref()
		if m == null:
			continue
		for k in ch:
			m.set_shader_parameter(k, ch[k])
		keep.append(w)
	th_mats = keep


func th_code(t: float) -> Color:
	"""the colour the shaders write for t °C (without the sRGB inverse)"""
	var v := roundf(clampf((t + 40.0) / 440.0, 0.0, 1.0) * 16383.0)
	var hi := floorf(v / 128.0)
	return Color((128.0 + hi) / 255.0, (128.0 + v - hi * 128.0) / 255.0, (128.0 + hi) / 255.0)


func _th_byte(b: int) -> int:
	"""a stored byte -> the 7 bits the shader wrote"""
	return clampi(th_inv[b] - 128, 0, 127)


func _th_read(img: Image, x: int, y: int) -> float:
	"""°C of one pixel of a rendered thermal picture (calibration)"""
	var c := img.get_pixel(x, y)
	return (_th_byte(roundi(c.r * 255.0)) * 128 + _th_byte(roundi(c.g * 255.0))) * TH_STEP - 40.0


func _calibrate_thermal() -> void:
	await _mod("kamera")._calibrate_thermal()


func now() -> float:
	return Time.get_unix_time_from_system()


# ---- small helpers -----------------------------------------------------------------------------------------------
func mat(c: Color) -> StandardMaterial3D:
	var k := c.to_html()
	if not mats.has(k):
		var m := StandardMaterial3D.new()
		m.albedo_color = c
		m.roughness = 0.85
		_mat_detail(m, quality != "simple")
		mats[k] = m
	return mats[k]


func _make_detail() -> void:
	"""3D-3.33: one fine, seamless structure (bright / dark spots + bumps) for all plain surfaces - wood, cloth, metal and
	plastic no longer look like painted plastic. Made here from noise: no picture files."""
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.fractal_octaves = 4
	fn.frequency = 0.035
	detail_alb = NoiseTexture2D.new()
	detail_alb.noise = fn
	detail_alb.seamless = true
	detail_alb.width = 256
	detail_alb.height = 256
	var ramp := Gradient.new()
	ramp.set_color(0, Color(0.8, 0.8, 0.8))
	ramp.set_color(1, Color(1.0, 1.0, 1.0))
	detail_alb.color_ramp = ramp
	var fn2 := FastNoiseLite.new()
	fn2.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn2.fractal_octaves = 3
	fn2.frequency = 0.08
	detail_nrm = NoiseTexture2D.new()
	detail_nrm.noise = fn2
	detail_nrm.seamless = true
	detail_nrm.width = 256
	detail_nrm.height = 256
	detail_nrm.as_normal_map = true
	detail_nrm.bump_strength = 3.0


func _mat_detail(m: StandardMaterial3D, on: bool) -> void:
	if detail_alb == null:
		_make_detail()
	if on:
		m.albedo_texture = detail_alb
		m.normal_enabled = true
		m.normal_texture = detail_nrm
		m.normal_scale = 0.35
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3(1.2, 1.2, 1.2)
	else:
		m.albedo_texture = null
		m.normal_enabled = false
		m.uv1_triplanar = false


func tmat(key: String) -> ShaderMaterial:
	"""thermal material of a kind of surface whose temperature changes with the time of day (updated in _update_temps)"""
	if not tmats.has(key):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/thermal.gdshader")
		m.set_shader_parameter("temp", ambient)
		m.set_shader_parameter("spread", 0.8)
		tmats[key] = th_reg(m)
	return tmats[key]


func tmat_fixed(temp: float) -> ShaderMaterial:
	var k := snappedf(temp, 0.5)
	if not tmat_fixed_cache.has(k):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/thermal.gdshader")
		m.set_shader_parameter("temp", k)
		m.set_shader_parameter("spread", 0.6)
		tmat_fixed_cache[k] = th_reg(m)
	return tmat_fixed_cache[k]


func pos_of(az: float, d: float, y := 0.0) -> Vector3:
	var a := deg_to_rad(az)
	return Vector3(sin(a) * d, y, -cos(a) * d)


func add_mesh(parent: Node3D, mesh: Mesh, p: Vector3, m: Material, tkey, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	"""a visible part and its twin for the thermal camera (tkey: name of a thermal material or a fixed temperature)"""
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = p
	mi.rotation = rot
	mi.scale = scl
	if colors != null and m is StandardMaterial3D and mats.get((m as StandardMaterial3D).albedo_color.to_html()) == m:
		m = colors.material_for((m as StandardMaterial3D).albedo_color, tkey if typeof(tkey) == TYPE_STRING else "warm")   # 3D-3.97
	mi.material_override = m
	mi.layers = 1
	parent.add_child(mi)
	var th := MeshInstance3D.new()
	th.mesh = mesh
	th.position = p
	th.rotation = rot
	th.scale = scl
	th.material_override = tmat(tkey) if typeof(tkey) == TYPE_STRING else tmat_fixed(float(tkey))
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(th)
	return mi


func box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


# ---- building the world ------------------------------------------------------------------------------------------
func _build_environment() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR   # from 3D-3.3: the light of the sky as a colour - the
	env.ambient_light_sky_contribution = 0.0                         # Compatibility renderer of Godot gave almost no light
																	 # from the sky, so shadows were black (_update_sky)
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_density = 0.0008
	env.fog_sky_affect = 0.35                     # 3D-3.33: the haze covers the sky only partly (clouds, stars, moon stay visible)
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_hdr_threshold = 1.2
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 80.0
	sun.shadow_blur = 1.6                       # softer shadow edges (3D-3.3)
	sun.shadow_normal_bias = 1.4
	add_child(sun)
	moonlight = DirectionalLight3D.new()
	moonlight.light_color = Color(0.6, 0.7, 1.0)
	moonlight.rotation = Vector3(deg_to_rad(-40), deg_to_rad(140), 0)
	moonlight.shadow_enabled = false
	add_child(moonlight)


func _build_world() -> void:
	var world := Node3D.new()
	add_child(world)
	# meadow
	grass_mat = ShaderMaterial.new()
	grass_mat.shader = load("res://shaders/grass.gdshader")
	grass_mat.set_shader_parameter("noise_tex", noise_tex)
	var plane := PlaneMesh.new()
	plane.size = Vector2(1200, 1200)
	plane.subdivide_width = 8
	plane.subdivide_depth = 8
	var g := MeshInstance3D.new()
	g.mesh = plane
	g.material_override = grass_mat
	g.layers = 1
	world.add_child(g)
	flat_nodes.append(g)
	var gt := MeshInstance3D.new()
	gt.mesh = plane
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/ground_thermal.gdshader")
	tmats["ground"] = th_reg(gm)
	gt.material_override = gm
	gt.layers = 2
	world.add_child(gt)
	flat_nodes.append(gt)
	# the sky for the thermal camera: a big dome around everything (cold when clear, near air temperature when cloudy)
	var dome := SphereMesh.new()
	dome.radius = 1500.0
	dome.height = 3000.0
	var dm := MeshInstance3D.new()
	dm.mesh = dome
	dm.material_override = tmat("sky")
	dm.layers = 2
	dm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(dm)
	tmat("sky").set_shader_parameter("spread", 0.0)
	tmat("sky").set_shader_parameter("sky", 1.0)            # 3D-4.26: cold at the zenith, near the air at the horizon
	# hills far away (fade in the haze)
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in range(14):
		var hill := SphereMesh.new()
		hill.radius = rng.randf_range(90, 180)
		hill.height = hill.radius * 0.8
		flat_nodes.append(add_mesh(world, hill, pos_of(i * 360.0 / 14 + rng.randf_range(-8, 8), rng.randf_range(420, 520), -hill.radius * 0.15),
				mat(Color(0.25, 0.33, 0.25)), "hill"))
		flat_nodes.append(world.get_child(world.get_child_count() - 1))
	scene_parent = Node3D.new()
	add_child(scene_parent)
	scenes = Scenes.new()
	scenes.m = self
	_build_scene()


func _build_scene() -> void:
	"""everything of the chosen scene (scenes.gd)"""
	scene = Worlds.default_place(scene)          # 3D-4.x: a world without its own build -> its first place
	if Scenes.name_of(scene) == scene:
		scene = "camping"                        # unknown name
	foliage_mats.clear()
	cloth_mats.clear()
	clear_obstacles()
	lamps.clear()
	lamp_mats.clear()
	anims.clear()
	door_open = false
	terrain = false
	ground_fn = Callable()
	_horizon.clear()
	ground_mats.clear()
	geo_note = ""
	gelaende.reset()                             # 3D-4.x: flat until the scene asks for hills (gelaende.setup_relief)
	if entdecken != null:
		entdecken.begin_scene(scene)             # Erlebniswelt: the discoveries of the old scene go, the new scene registers its own
	scenes.build(scene, scene_parent)
	if entdecken != null:
		entdecken.on_scene()                     # ... and the demo set of «Camping-Platz»
	for n in flat_nodes:
		n.visible = not terrain
	gelaende.on_scene()
	if zwilling != null:
		zwilling.on_scene()                      # 3D-4.4: the photo of the real place, tent and car by hand (first: the tent moves obj["pir"])
	if simreal != null:
		simreal.on_scene()                       # 3D-4.4: tarp, pennant, road sign
	if umgebung != null:
		umgebung.on_scene()                      # 3D-4.x: neighbour's lamp, puddles, fog wisps, tracks …
	if wetter != null:
		wetter.on_scene()                        # real-wetter: tent walls in the wind
	if szenen != null:
		szenen.on_scene()                        # 3D-4.x: the neighbours of «Voller Campingplatz»
	if waerme_welt != null:
		waerme_welt.on_scene()                   # 3D-4.26: parked cars (warm engine, hot roof), the person in the tent
	if licht != null:
		licht.on_scene()                         # «Licht & Nacht»: place lamps, tents, windows of the scene
	if zimmertiere != null:
		zimmertiere.on_scene()                   # Erlebniswelt «mehr Tiere drinnen»: hamster, budgie, spider (bedroom only)
	if scene == "ort" and not geo.loaded and not geo.busy and ort_lat != 0.0:
		geo.load_place(ort_lat, ort_lon, ort_name)      # from the cache or the internet; then place_loaded()
	if scene == "wild":
		rifle_on = true                          # wildlife watching: the rifle is on by itself
	if inhalte != null:
		inhalte.on_scene()                       # F2: photo textures / HDRI sky for this scene (or back to the code materials)
	preload("res://scripts/flora.gd").ground(self)   # «Flora und Fauna»: meadow from the owner's photos (if F2 did not)
	if Quality.lite():
		_lite_scene.call_deferred(true)          # 3D-4.25: Lite - thin grass, far small things not drawn


func place_loaded() -> void:
	"""the data of a place is there (geo.gd): keep it and show it"""
	while visitors == null or ui_root == null or game == null:   # loaded from the cache at the start: wait for the rest
		await get_tree().process_frame
	ort_lat = geo.lat
	ort_lon = geo.lon
	ort_name = geo.place_name
	_sun_cache = [-1.0, Vector2.ZERO]
	_settings_dirty = true
	set_scene("ort")


func choose_place(la: float, lo: float, nm: String) -> void:
	"""from the map or the page of MoveEye: load this place"""
	if not geo.in_ch(la, lo):
		geo.info = "Dieser Punkt liegt nicht in der Schweiz."
		return
	if not (is_equal_approx(la, ort_lat) and is_equal_approx(lo, ort_lon)):
		ort_env = "auto"                                 # another place (from the page of MoveEye): look what it is
	geo.load_place(la, lo, nm)


func set_place_text(t: String) -> void:
	"""«Zermatt» or «46.0207, 7.7491» (field on the page of MoveEye)"""
	var parts := t.replace(";", ",").split(",")
	if parts.size() >= 2 and parts[0].strip_edges().is_valid_float() and parts[1].strip_edges().is_valid_float():
		var nm := ""
		if parts.size() > 2:
			nm = ",".join(parts.slice(2)).strip_edges()      # «46.02, 7.75, Zermatt» from the map on the page of MoveEye
		choose_place(float(parts[0]), float(parts[1]), nm)
		return
	geo.info = "Suche «%s» …" % t
	var res: Array = await geo.search(t)
	if res.is_empty():
		geo.info = "«%s» nicht gefunden." % t if geo.info.begins_with("Suche") else geo.info
		return
	choose_place(res[0]["lat"], res[0]["lon"], res[0]["label"])


func place_label() -> String:
	if geo.busy:
		return geo.info
	if ort_lat == 0.0:
		return ""
	return "%s (%.5f, %.5f)" % [ort_name, ort_lat, ort_lon] if not ort_name.begins_with("%.5f" % ort_lat) else "%.5f, %.5f" % [ort_lat, ort_lon]


func open_map() -> void:
	if karte == null:
		return
	karte.open(ort_lat, ort_lon)


func ground_y(x: float, z: float) -> float:
	"""height of the ground (0 everywhere except at a real place, a scene with its own ground or hills of gelaende.gd)"""
	if ground_fn.is_valid():
		return ground_fn.call(x, z)
	if terrain:
		return geo.height(x, z)
	return gelaende.height(x, z) if gelaende != null and gelaende.on else 0.0


func hilly() -> bool:
	"""the ground is not flat (a real place or hills of gelaende.gd; scenes with their own ground set terrain): things follow ground_y"""
	return terrain or (gelaende != null and gelaende.on)


func ground_hit(from: Vector3, d: Vector3):
	"""where a ray meets the ground (null if not within 400 m)"""
	if not hilly():
		return Plane(Vector3.UP, 0).intersects_ray(from, d)
	var t := 0.0
	var prev := from
	while t < 400.0:
		t += 0.5 + t * 0.01
		var p := from + d * t
		if p.y <= ground_y(p.x, p.z):
			var lo := prev
			var hi := p
			for _i in range(12):
				var mid := (lo + hi) / 2.0
				if mid.y <= ground_y(mid.x, mid.z):
					hi = mid
				else:
					lo = mid
			return hi
		prev = p
	return null


func set_scene(id: String) -> bool:
	id = Worlds.default_place(id)                # 3D-4.x: «Zuhause» = its garden (worlds.gd)
	if id != solo_scene:
		solo_scene = ""
	var ok := false
	for s in Scenes.LIST:
		if s[0] == id:
			ok = true
	if not ok:
		return false
	if scene == "wild" and id != "wild":
		rifle_on = false                         # leaving the wildlife watching: the rifle goes off by itself
	scene = id
	last_scene = id
	_settings_dirty = true
	for v in visitors.get_children():
		v.queue_free()
	for c in scene_parent.get_children():
		c.queue_free()
	_build_scene()
	if inventar != null:
		inventar.rebuild()                         # 3D-3.86: the objects of this scene from the inventory
	if dev2 != null and dev2.rig != null:
		dev2._put()                                # 3D-3.84: a second device guarding a thing moves with it
	if game != null:
		game.on_scene()                            # the game: new goal, players back to the start
	next_auto = now() + 8.0
	_update_sky()
	_update_temps()
	_spot_refresh()
	_only_refresh()                                # 3D-4.28: settings shown only in one scene
	_sync_ui()
	return true


func scene_spot(id: String) -> String:
	"""3D-4.x: the chosen place of MoveEye in a scene with several places («» = the first one)"""
	if id == "ferienpark":
		return fp_spot
	for e in szene_spot.split(";", false):
		var kv := e.split("=")
		if kv.size() == 2 and kv[0] == id:
			return kv[1]
	return ""


func set_scene_spot(v: String) -> void:
	"""3D-4.x: one setting «Standort in der Szene» for every scene with several places (Ferienpark, kompakt.gd)"""
	if scene == "ferienpark":
		set_fp_spot(v)
		return
	if not Kompakt.spots_of(scene).has(v):
		return
	var keep := []
	for e in szene_spot.split(";", false):
		if not e.begins_with(scene + "="):
			keep.append(e)
	keep.append(scene + "=" + v)
	szene_spot = ";".join(keep)
	_settings_dirty = true
	set_scene(scene)


func _spot_options() -> Array:
	"""the choices of «Standort in der Szene» for the scene that is there now"""
	if scene == "ferienpark":
		return preload("res://scripts/ferienpark.gd").spot_options()
	var o: Array = Kompakt.spot_options(scene)
	return o if not o.is_empty() else [["", "nur ein Standort in dieser Szene"]]


func _spot_refresh() -> void:
	"""a new scene: new choices for «Standort in der Szene» (window and the page of MoveEye)"""
	for c in controls:
		if c.id == "szene_spot":
			c.extra["options"] = _spot_options()
			var ob = ui_rows.get("szene_spot")
			if ob is OptionButton:
				ob.clear()
				for o in c.extra["options"]:
					ob.add_item(str(o[1]))
					ob.set_item_metadata(ob.item_count - 1, o[0])
func _fp_seek() -> void:
	"""Erlebniswelt 12 (erlebniswelt.gd): the children of the Ferienpark hide near MoveEye - MoveEye must report them"""
	if scene != "ferienpark":
		set_scene("ferienpark")
	var r: Dictionary = preload("res://scripts/ferienpark.gd").control(self, {"do": "verstecken"})
	if entdecken != null and r.get("ok", false):
		entdecken._say_small(preload("res://scripts/i18n.gd").t("Verstecken: vier Kinder verstecken sich bei MoveEye – findet MoveEye alle?"))


const BT_MONTH := {"fruehling": "5", "sommer": "7", "herbst": "10", "winter": "1"}


func set_bt(key: String, v) -> void:
	"""3D-4.x «Bergtal»: sleeping spot, bed, season - the valley is built again around the spot (MoveEye stays at the origin)"""
	set(key, v)
	if key == "bt_season" and BT_MONTH.has(str(v)):
		season = BT_MONTH[str(v)]                        # the path of the sun and the moon fit the season
		_sun_cache = [-1.0, Vector2.ZERO]
	_settings_dirty = true
	if Worlds.world_of(scene) == "bergtal":
		set_scene("bergtal" if key == "bt_spot" or not Worlds.is_place(scene) else scene)   # 3D-4.x: a sleeping spot leaves the place
	else:
		_sync_ui()


func bt_here() -> Dictionary:
	"""«Hier übernachten»: the place in the middle of the view (or where the rover stands) - flat enough? then sleep there"""
	var bt = scenes.data.get("bergtal", null)
	if bt == null:
		start_info = preload("res://scripts/i18n.gd").t("«Hier übernachten» geht nur in der Szene Bergtal.")
		return {"ok": false, "error": "not bergtal"}
	return bt_take(bt.pick_here())


func bt_take(r: Dictionary) -> Dictionary:
	if not bool(r.get("ok", false)):
		start_info = preload("res://scripts/i18n.gd").t(str(r.get("error", "")))
		return r
	bt_free = [snappedf(float(r["x"]), 0.01), snappedf(float(r["z"]), 0.01), snappedf(float(r.get("yaw", 0.0)), 0.1)]
	bt_spot = "frei"
	_settings_dirty = true
	mover_home()
	set_scene("bergtal")
	start_info = "%s %s" % [preload("res://scripts/i18n.gd").t("Neuer Schlafplatz:"), preload("res://scripts/i18n.gd").t(str(r.get("note", "")))]
	r["rating"] = scenes.data["bergtal"].rating if scenes.data.has("bergtal") else {}
	return r


func bt_goto(v: String) -> Dictionary:
	"""quick travel in the Bergtal: «s:<spot>» = sleep there (MoveEye moves), «p:<place>» = the view flies there"""
	var bt = scenes.data.get("bergtal", null)
	if bt == null or v == "":
		return {"ok": false}
	if v.begins_with("s:"):
		set_bt("bt_spot", v.substr(2))
		return {"ok": true, "spot": bt_spot}
	var nm := v.substr(2)
	var Bt = preload("res://scripts/bergtal.gd")
	var all: Array = Bt.all_places()
	for mk in bt_marks:
		all.append(mk)
	for pl in all:
		if str(pl[0]) == nm:
			if not nm in bt_visited and not bt_marks.any(func(x): return str(x[0]) == nm):
				start_info = "%s %s" % [preload("res://scripts/i18n.gd").t("Noch nicht besucht – zuerst hingehen oder hinfliegen:"), nm]
				return {"ok": false, "error": "not visited", "place": nm}
			var wp: Vector3 = bt.WG(float(pl[1]), float(pl[2]))
			if bt.get("orte") != null and bt.orte.fly(nm):        # a room (bergtal_orte.gd): the view flies inside
				return {"ok": true, "place": nm, "inside": true}
			fly_to(wp + Vector3(0, 2, 0), 45.0)
			return {"ok": true, "place": nm, "at": wp}
	return {"ok": false, "error": "unknown place"}


func bt_mark(nm: String) -> Dictionary:
	"""an own mark on the map at the place in the middle of the view"""
	var bt = scenes.data.get("bergtal", null)
	if bt == null or nm.strip_edges() == "":
		return {"ok": false}
	var r: Dictionary = bt.pick_here()
	if not r.has("x"):
		return r
	bt_marks.append([nm.strip_edges().left(30), snappedf(float(r["x"]), 0.1), snappedf(float(r["z"]), 0.1)])
	_settings_dirty = true
	bt._publish()
	return {"ok": true, "marks": bt_marks}


func _bt_do(what: String) -> void:
	var bt = scenes.data.get("bergtal", null)
	if bt == null:
		start_info = preload("res://scripts/i18n.gd").t("Das geht nur in der Szene Bergtal.")
		return
	match what:
		"ride":
			bt.ride(true)
		"morning":
			bt.morning()
		_:
			bt.spawn_kind("berg_" + what)


func set_fp_spot(v: String) -> void:
	"""3D-4.x: where MoveEye stands in the «Ferienpark am See»: the park is built again around this place"""
	if not preload("res://scripts/ferienpark.gd").SPOTS.has(v):
		return
	fp_spot = v
	_settings_dirty = true
	if Worlds.world_of(scene) == "ferienpark":
		set_scene("ferienpark")                    # 3D-4.x: also from a place of the park (worlds.gd)
	else:
		_sync_ui()


func _build_head() -> void:
	rig = Node3D.new()
	add_child(rig)
	head = Node3D.new()
	head.position = Vector3(0, mast_h, 0)
	rig.add_child(head)
	_build_chassis()
	head_pitch = Node3D.new()
	head.add_child(head_pitch)
	white_light = SpotLight3D.new()
	white_light.spot_range = 40.0
	white_light.spot_angle = 32.0
	white_light.light_energy = 0.0
	white_light.light_color = Color(1.0, 0.97, 0.92)
	white_light.position = Vector3(0, 0.15, 0)
	head_pitch.add_child(white_light)
	ir_light = SpotLight3D.new()
	ir_light.spot_range = 28.0
	ir_light.spot_angle = 48.0
	ir_light.light_energy = 0.0
	ir_light.position = Vector3(0, -0.1, 0)
	head_pitch.add_child(ir_light)
	var hm := box(0.25, 0.18, 0.2)                       # the head itself (visible from the fixed camera)
	var hmi := MeshInstance3D.new()
	hmi.mesh = hm
	hmi.material_override = mat(Color(0.12, 0.12, 0.13))
	hmi.layers = 1
	head_pitch.add_child(hmi)
	head_box = hmi
	var pole := MeshInstance3D.new()
	pole.mesh = box(0.06, 1.0, 0.06)
	pole.material_override = mat(Color(0.2, 0.2, 0.2))
	head.add_child(pole)
	mast_pole = pole
	set_mast(mast_h)


func set_mast(h: float) -> void:
	"""3D-3.57: the length of the pole (height of the camera head above the ground / the rover)"""
	mast_h = clampf(h, MAST_MIN, MAST_MAX)
	if head != null:
		head.position.y = mast_h
	if mast_pole != null:
		mast_pole.scale = Vector3(1, mast_h, 1)
		mast_pole.position = Vector3(0, -mast_h / 2.0, 0)


func _build_chassis() -> void:
	"""the mover: a small tracked vehicle under the pole (only seen when «Mover simulieren» is on)"""
	chassis = Node3D.new()
	rig.add_child(chassis)
	var wheel := CylinderMesh.new()
	wheel.top_radius = 0.07
	wheel.bottom_radius = 0.07
	wheel.height = 0.16
	wheel.radial_segments = 10
	add_mesh(chassis, box(0.62, 0.16, 0.78), Vector3(0, 0.2, 0), mat(Color(0.25, 0.27, 0.22)), "caravan")
	for sx in [-1.0, 1.0]:
		add_mesh(chassis, box(0.14, 0.2, 0.9), Vector3(sx * 0.37, 0.11, 0), mat(Color(0.08, 0.08, 0.08)), "stone")     # track
		for k in range(4):
			var wm: MeshInstance3D = add_mesh(chassis, wheel, Vector3(sx * 0.37, 0.1, -0.3 + k * 0.2), mat(Color(0.45, 0.45, 0.47)), "stone", Vector3(0, 0, PI / 2))
			mover_wheels.append(wm)
	add_mesh(chassis, box(0.3, 0.06, 0.08), Vector3(0, 0.3, -0.36), mat(Color(0.9, 0.55, 0.1)), "tent")       # front mark
	chassis.visible = mover_on


var home_pos := Vector3.ZERO           # 3D-3.44: where MoveEye stands (Aufstell-Planer «Hierhin stellen»)
var home_yaw := 0.0
var planner                           # planner.gd
var pruef                             # pruefstand.gd (3D-3.49): the test bench on this PC
var replay                            # replay.gd: Alarm-Rückblick in 3D (3D-3.44)
var dataset                           # dataset.gd: Trainingsbilder (3D-3.44)
var kitrain                           # kitrain.gd: «KI trainieren» - Paket auf GitHub, Training starten
var tunnel                            # tunnel.gd: Tunnel zu MoveEye (3D-3.45)
var tunnel_host := ""
var tunnel_code := ""
var tunnel_on := false
var tunnel_label: Label


var netmap_node: Node3D = null


func show_netmap(pts) -> int:
	"""Empfangskarte from MoveEye: x / z in metres from MoveEye (z = where the camera looks), q 0 (bad) .. 1 (good)"""
	if netmap_node != null:
		netmap_node.queue_free()
		netmap_node = null
	if typeof(pts) != TYPE_ARRAY or pts.is_empty():
		return 0
	netmap_node = Node3D.new()
	add_child(netmap_node)
	var n := 0
	for p in pts:
		if typeof(p) != TYPE_DICTIONARY:
			continue
		var x := float(p.get("x", 0.0))
		var z := float(p.get("z", 0.0))
		var q := clampf(float(p.get("q", 0.0)), 0.0, 1.0)
		var w: Vector3 = rig.global_position + rig.global_transform.basis * Vector3(x, 0, -z)
		w.y = ground_y(w.x, w.z) + 0.04
		var m := MeshInstance3D.new()
		var cy := CylinderMesh.new()
		cy.top_radius = 1.6
		cy.bottom_radius = 1.6
		cy.height = 0.04
		m.mesh = cy
		var mt := StandardMaterial3D.new()
		mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mt.albedo_color = Color.from_hsv(q * 0.33, 0.85, 0.95, 0.55)
		m.material_override = mt
		m.position = w
		m.layers = HELPER_LAYER
		netmap_node.add_child(m)
		var lb := Label3D.new()
		var txt := "%d ms" % int(float(p.get("rtt", 0))) if p.get("rtt") != null else ""
		if p.get("down") != null:
			txt += "  %.0f Mbit/s" % float(p.get("down"))
		if p.get("dbm") != null:
			txt += "  %d dBm" % int(p.get("dbm"))
		lb.text = txt
		lb.layers = HELPER_LAYER
		lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lb.font_size = 40
		lb.outline_size = 8
		lb.position = w + Vector3(0, 0.6, 0)
		netmap_node.add_child(lb)
		n += 1
	return n


func set_home(p: Vector3, yaw: float) -> void:
	home_pos = Vector3(p.x, 0, p.z)
	home_yaw = yaw
	mover_home()


func mover_home() -> void:
	rig.position = Vector3(home_pos.x, ground_y(home_pos.x, home_pos.z), home_pos.z)
	rig.rotation = Vector3(0, home_yaw, 0)


func set_mover(on: bool) -> void:
	mover_on = on
	if chassis != null:
		chassis.visible = on
	if not on and rig != null:
		mover_home()


var _pad_l := 0.0
var _pad_r := 0.0


func _drive(dt: float) -> void:
	"""the mover drives: left / right track from MoveEye (-1 … 1); stops when MoveEye is quiet for 2.5 s (it stops the tracks itself after 0.6 s without the stick)"""
	if not mover_on:
		if Vector2(rig.position.x - home_pos.x, rig.position.z - home_pos.z).length() > 0.01 or abs(rig.rotation.y - home_yaw) > 0.001:
			mover_home()
		return
	var tnow := now()                                      # real time since the last call (frames are skipped to save CPU)
	dt = clampf(tnow - _drive_t, 0.0, 1.0) if _drive_t > 0.0 else dt
	_drive_t = tnow
	var d: Dictionary = mw.get("drive", {})
	var l := float(d.get("l", 0.0)) if now() - mw_t < 2.5 else 0.0
	var r := float(d.get("r", 0.0)) if now() - mw_t < 2.5 else 0.0
	if pad_on:                                             # driven here in the simulator (stick at the bottom right, arrow keys)
		var tl := pad_drive.x + pad_drive.y * 0.7
		var trr := pad_drive.x - pad_drive.y * 0.7
		var mx: float = max(1.0, max(abs(tl), abs(trr)))
		_pad_l = move_toward(_pad_l, tl / mx, dt * 3.0)
		_pad_r = move_toward(_pad_r, trr / mx, dt * 3.0)
		l = _pad_l
		r = _pad_r
	else:
		_pad_l = 0.0
		_pad_r = 0.0
	var v := (l + r) / 2.0 * mover_max
	var om := (l - r) / 0.74 * mover_max                    # track distance 0.74 m: left faster = turns right
	rig.rotation.y -= om * dt
	var fwd := Vector3(-sin(rig.rotation.y), 0, -cos(rig.rotation.y))
	var np := rig.position + fwd * v * dt
	if avoid_on:                                           # never into a house, a tree, the caravan
		var cur := Vector2(rig.position.x, rig.position.z)
		var q := Vector2(np.x, np.z)
		for o in _ob_near(q):
			var rr: Array = _ob_closest(o, q)
			if float(rr[1]) < 0.55 and float(_ob_closest(o, cur)[1]) >= 0.5:   # (something it already stands in may be left)
				q = (rr[0] as Vector2) + (rr[2] as Vector2) * 0.55
		np.x = q.x
		np.z = q.y
	np.x = clampf(np.x, -180.0, 180.0)
	np.z = clampf(np.z, -180.0, 180.0)
	np.y = ground_y(np.x, np.z)
	rig.position = np
	mover_dist += (abs(l) + abs(r)) * mover_max * dt
	for w in mover_wheels:
		w.rotation.x = mover_dist * 4.0


func _build_viewports() -> void:
	for i in range(3):
		var vp := SubViewport.new()
		if i < 2:
			vp.size = Vector2i(CAM_W[i], CAM_H[i])
		else:
			vp.size = Vector2i(TH_W * 2, TH_H * 2)
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		vp.msaa_3d = Viewport.MSAA_2X if i < 2 else Viewport.MSAA_DISABLED
		add_child(vp)
		var cam := Camera3D.new()
		cam.keep_aspect = Camera3D.KEEP_WIDTH
		cam.fov = CAM_FOV[i] if i < 2 else TH_FOV
		cam.near = 0.1
		cam.far = 2000.0
		cam.cull_mask = 1 if i < 2 else 2
		var at := CameraAttributesPractical.new()
		cam.attributes = at
		cam_attr.append(at)
		vp.add_child(cam)
		vps.append(vp)
		cams.append(cam)
	th_env = Environment.new()
	th_env.background_mode = Environment.BG_COLOR
	th_env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	th_env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	th_env.fog_enabled = false
	th_env.glow_enabled = false
	cams[2].environment = th_env
	th_preview = ImageTexture.new()


func _build_weather() -> void:
	rain = CPUParticles3D.new()
	rain.amount = 2500
	rain.lifetime = 1.0
	rain.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	rain.emission_box_extents = Vector3(22, 1, 22)
	rain.direction = Vector3(0, -1, 0)
	rain.spread = 3.0
	rain.initial_velocity_min = 14.0
	rain.initial_velocity_max = 18.0
	rain.gravity = Vector3(0, -9.8, 0)
	var dm := box(0.012, 0.45, 0.012)
	var rm := StandardMaterial3D.new()
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rm.albedo_color = Color(0.75, 0.8, 0.85, 0.45)
	rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	dm.material = rm
	rain.mesh = dm
	rain.position = Vector3(0, 12, -8)
	rain.emitting = false
	add_child(rain)
	snow = CPUParticles3D.new()
	snow.amount = 3000
	snow.lifetime = 7.0
	snow.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	snow.emission_box_extents = Vector3(22, 1, 22)
	snow.direction = Vector3(0, -1, 0)
	snow.spread = 20.0
	snow.initial_velocity_min = 1.0
	snow.initial_velocity_max = 1.8
	snow.gravity = Vector3(0, -0.4, 0)
	var sm := SphereMesh.new()
	sm.radius = 0.025
	sm.height = 0.05
	sm.radial_segments = 4
	sm.rings = 2
	var smm := StandardMaterial3D.new()
	smm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smm.albedo_color = Color(0.95, 0.95, 0.97)
	sm.material = smm
	snow.mesh = sm
	snow.position = Vector3(0, 10, -8)
	snow.emitting = false
	add_child(snow)


func _build_effects() -> void:
	"""3D-3.33: lightning (a flash light from the sky) and raindrops splashing on the ground"""
	flash_light = DirectionalLight3D.new()
	flash_light.light_color = Color(0.85, 0.9, 1.0)
	flash_light.light_energy = 0.0
	flash_light.rotation = Vector3(deg_to_rad(-55), deg_to_rad(30), 0)
	flash_light.shadow_enabled = false
	flash_light.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	add_child(flash_light)
	splashes = CPUParticles3D.new()
	splashes.amount = 700
	splashes.lifetime = 0.35
	splashes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	splashes.emission_box_extents = Vector3(14, 0.01, 14)
	splashes.direction = Vector3(0, 1, 0)
	splashes.spread = 60.0
	splashes.initial_velocity_min = 0.6
	splashes.initial_velocity_max = 1.4
	splashes.gravity = Vector3(0, -9.8, 0)
	splashes.scale_amount_min = 0.6
	splashes.scale_amount_max = 1.2
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.4))
	sc.add_point(Vector2(1, 1.0))
	splashes.scale_amount_curve = sc
	var ramp := Gradient.new()
	ramp.set_color(0, Color(0.85, 0.9, 0.95, 0.55))
	ramp.set_color(1, Color(0.85, 0.9, 0.95, 0.0))
	splashes.color_ramp = ramp
	var q := QuadMesh.new()
	q.size = Vector2(0.05, 0.05)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qm.vertex_color_use_as_albedo = true
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	q.material = qm
	splashes.mesh = q
	splashes.position = Vector3(0, ground_y(0, -8) + 0.03, -8)
	splashes.emitting = false
	add_child(splashes)


func _lightning(dt: float) -> void:
	"""a flash now and then while it rains with «Gewitter» (or a storm is coming): 2-3 quick flashes, thunder later"""
	var on := thunder and weather == "rain" or (storm_t > 0.0 and now() - storm_t > 60.0 and weather == "rain")
	if not _flash_seq.is_empty():
		var t := now()
		while not _flash_seq.is_empty() and t >= float(_flash_seq[0][0]):
			var st: Array = _flash_seq.pop_front()
			flash_light.light_energy = float(st[1])
			_flash_boost = float(st[2])
			if wetter != null:
				wetter.on_flash(float(st[1]))           # real-wetter: the bolt in the sky
			env.ambient_light_energy = _amb_base + _flash_boost
			sky_mat.set_shader_parameter("energy", _sky_e_base + _flash_boost * 0.6)
		return
	if not on:
		flash_light.light_energy = 0.0
		return
	if _flash_next == 0.0:
		_flash_next = now() + randf_range(4.0, 12.0)
	if now() >= _flash_next:
		_flash_next = now() + randf_range(8.0, 30.0)
		lightning_strike()


func lightning_strike() -> void:
	"""one flash now: 2-3 quick flashes, thunder later (real-wetter: also the button «Blitz jetzt» and the test plan «wetter»)"""
	var t0 := now()
	var e := randf_range(2.0, 4.5)
	_flash_seq = [[t0, e, 1.2], [t0 + 0.07, 0.0, 0.0], [t0 + 0.16, e * 0.7, 0.9], [t0 + 0.22, 0.0, 0.0]]
	if randf() < 0.5:
		_flash_seq += [[t0 + 0.4, e * 0.5, 0.6], [t0 + 0.47, 0.0, 0.0]]
	var dist := randf_range(800.0, 4000.0)                # thunder: later and quieter the farther away
	var dir := Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized()
	get_tree().create_timer(dist / 340.0).timeout.connect(func():
		add_sound(30.0, dir * dist, 2.5)
		preload("res://scripts/klang.gd").donner(dist))      # Spielton: the thunder on the PC (only in games and stories)
	if wetter != null:
		wetter.on_strike(dist, dir)


func _build_fireflies() -> void:
	"""fireflies on warm nights: small blinking lights over the meadow in front of the cameras (from 3D-2.9)"""
	fireflies = CPUParticles3D.new()
	fireflies.amount = 40
	fireflies.lifetime = 4.0
	fireflies.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	fireflies.emission_box_extents = Vector3(14, 0.6, 9)
	fireflies.position = Vector3(0, 0.9, -12)
	fireflies.direction = Vector3(1, 0.2, 0)
	fireflies.spread = 180.0
	fireflies.gravity = Vector3.ZERO
	fireflies.initial_velocity_min = 0.1
	fireflies.initial_velocity_max = 0.5
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 0.5, 0))
	ramp.set_color(1, Color(1, 1, 0.5, 0))
	ramp.add_point(0.3, Color(0.85, 1.0, 0.35, 1))
	ramp.add_point(0.55, Color(0.85, 1.0, 0.35, 0.1))
	ramp.add_point(0.75, Color(0.85, 1.0, 0.35, 1))
	fireflies.color_ramp = ramp
	var sm := SphereMesh.new()
	sm.radius = 0.04
	sm.height = 0.08
	sm.radial_segments = 4
	sm.rings = 2
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(3.0, 3.0, 1.8)
	sm.material = mat
	fireflies.mesh = sm
	fireflies.emitting = false
	add_child(fireflies)


func set_cloth(on: bool) -> void:
	world_cloth = on
	for n in get_tree().get_nodes_in_group("cloth"):
		n.visible = on


func set_smoke(on: bool) -> void:
	world_smoke = on
	for n in get_tree().get_nodes_in_group("smoke"):
		n.emitting = on


func _build_lens() -> void:
	_mod("kamera")._build_lens()


# ---- sounds of the world (for the microphone of MoveEye) --------------------------------------------------------
func add_sound(db1m: float, pos: Vector3, secs: float, kind := "noise") -> void:
	"""a sound: loudness at 1 m (dB, 0 = very loud), where, how long, what (mikrofon.gd: how the ground dampens it)"""
	sounds.append([db1m, pos, now() + secs, kind])


func emit_sound(kind: String, n: int = 1, pos = null) -> Dictionary:
	"""3D-3.98: a short sound MoveEye should recognise (clap switch, «Gesundheit», noise alarm). Without a place: the person in
	the bed, else the nearest visitor, else 2 m in front of the head camera."""
	if not SOUND_EV_DB.has(kind):
		return {"ok": false, "error": "kind: clap | sneeze | voice | shout"}
	var ear := head.global_position if head != null else Vector3(0, HEAD_H, 0)
	var p: Vector3
	if pos is Vector3:
		p = pos
	elif sleeper != null and sleeper.root != null and is_instance_valid(sleeper.root) and sleeper.root.is_inside_tree() and sleeper.state != "gone":
		p = (sleeper.upper.global_position if sleeper.upper != null else sleeper.root.global_position) + Vector3(0, 0.3, 0)
	else:
		p = ear + (-cams[0].global_transform.basis.z * 2.0 if cams.size() > 0 else Vector3(0, 0, -2))
		var best := 30.0
		for v in visitors.get_children():
			if v is Node3D and v.get("kind") == "person" and (v as Node3D).global_position.distance_to(ear) < best:
				best = (v as Node3D).global_position.distance_to(ear)
				p = (v as Node3D).global_position + Vector3(0, 1.5, 0)
	var d: float = maxf(1.0, p.distance_to(ear))
	var db: float = float(SOUND_EV_DB[kind]) - 20.0 * log(d) / log(10.0)
	if mikro != null and mikro.real_on:
		db = mikro.level(float(SOUND_EV_DB[kind]), p, kind)   # real-pir-ton: 1/r + ground + housing (2 m: -19.5, 15 m: -43.5)
	sound_ev_id += 1
	n = clampi(n, 1, 6)
	sound_ev.append({"id": sound_ev_id, "kind": kind, "n": n, "db": snappedf(db, 0.1), "t": now()})
	add_sound(float(SOUND_EV_DB[kind]), p, {"clap": 0.45 * n, "sneeze": 0.6, "voice": 2.5, "shout": 3.5}[kind], kind)
	_sound_play(kind, n)
	return {"ok": true, "id": sound_ev_id, "db": snappedf(db, 0.1), "dist": snappedf(d, 0.1)}


var _snd_player: AudioStreamPlayer = null


func _sound_play(kind: String, n: int) -> void:
	"""a small generated sound so you hear it on the PC too (claps = noise bursts, sneeze = «hatschi»-like burst)"""
	if not sound_on:
		return
	var rate := 22050
	var pcm := PackedByteArray()
	var total := 0.0
	var parts: Array = []
	match kind:
		"clap":
			for i in range(n):
				parts.append([i * 0.32, 0.05, 0.9, 1.0])
			total = n * 0.32 + 0.1
		"sneeze":
			parts = [[0.0, 0.25, 0.25, 0.3], [0.25, 0.22, 0.8, 0.6]]
			total = 0.55
		_:
			return                                    # voices: only the level for MoveEye
	var ns := int(total * rate)
	pcm.resize(ns * 2)
	for i in range(ns):
		var t := float(i) / rate
		var v := 0.0
		for pt in parts:
			var dt: float = t - float(pt[0])
			if dt >= 0.0 and dt < float(pt[1]):
				var env := exp(-dt / (float(pt[1]) * 0.35)) * float(pt[2])
				v += (randf() * 2.0 - 1.0) * env * (0.6 + 0.4 * sin(dt * 900.0 * float(pt[3])))
		pcm.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 26000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = pcm
	if _snd_player == null:
		_snd_player = AudioStreamPlayer.new()
		add_child(_snd_player)
	_snd_player.stream = w
	_snd_player.volume_db = -8.0
	_snd_player.play()


# ---- 3D-3.98: sensors for MoveEye - solar panel and GPS module (PIR, door, gas, tag, wind were there before) ----------
var solar_wp := 20.0                   # the panel: watts in full sun
var gps_steal_t := 0.0                 # «carried away»: since when (0 = standing)
var gps_steal_dir := 0.0


func solar_reading() -> Dictionary:
	"""the current meter at the solar panel: volts and amperes from the sun height, clouds and weather"""
	var el: float = sun_el()
	var f := {"clear": 1.0, "cloudy": 0.4, "fog": 0.18, "rain": 0.15, "snow": 0.1}.get(weather, 0.6) as float
	var w: float = solar_wp * clampf(sin(deg_to_rad(maxf(0.0, el))) * 1.1, 0.0, 1.0) * f
	if el < -1.0:
		w = 0.0
	var v: float = 0.0 if w < 0.05 else clampf(14.0 + w * 0.35, 14.0, 19.5)
	return {"v": snappedf(v, 0.01), "a": snappedf(w / v if v > 0.0 else 0.0, 0.001)}


func gps_reading() -> Dictionary:
	"""the GPS module: the place of the scene (a real place / twin, else the middle of Switzerland); carried away = 1.6 m/s off"""
	var la: float = ort_lat if scene == "ort" and ort_lat != 0.0 else float(twin.get("lat", 46.80))
	var lo: float = ort_lon if scene == "ort" and ort_lat != 0.0 else float(twin.get("lon", 8.23))
	if gps_steal_t > 0.0:
		var m: float = (now() - gps_steal_t) * 1.6
		la += cos(gps_steal_dir) * m / 111320.0
		lo += sin(gps_steal_dir) * m / (111320.0 * cos(deg_to_rad(la)))
	return {"lat": snappedf(la, 0.000001), "lon": snappedf(lo, 0.000001), "sats": 9}


func gps_steal(on: bool) -> Dictionary:
	gps_steal_t = now() if on else 0.0
	gps_steal_dir = randf() * TAU
	return {"ok": true, "steal": on}


func sound_events() -> Array:
	"""the short sounds of the last 10 s (MoveEye takes each id once)"""
	var t := now()
	sound_ev = sound_ev.filter(func(e): return t - float(e["t"]) < 10.0)
	var out := []
	for e in sound_ev:
		out.append({"id": e["id"], "kind": e["kind"], "n": e["n"], "db": e["db"]})
	return out


func sound_db() -> float:
	"""what the microphone at the head hears now (dB): quiet background + weather + wind + the sounds, weaker with distance"""
	if mikro != null and mikro.real_on:
		return mikro.sound_db()                         # real-pir-ton: the microphone like real (mikrofon.gd)
	var base := -62.0 if is_dark() else -56.0
	if weather == "rain":
		base = -40.0 + (wetter.rain_db() if wetter != null else 0.0)   # real-wetter: louder in heavy rain
	base += clamp((wind - 10.0) * 0.35, 0.0, 22.0)
	var pw := pow(10.0, base / 10.0)
	var t := now()
	var ear := head.global_position if head != null else Vector3(0, HEAD_H, 0)
	for snd in sounds:
		if t < float(snd[2]):
			var d: float = max(1.0, (snd[1] as Vector3).distance_to(ear))
			pw += pow(10.0, (float(snd[0]) - 20.0 * log(d) / log(10.0)) / 10.0)
	return 10.0 * log(pw) / log(10.0)


func _update_sounds() -> void:
	"""every 0.5 s: steps of people, dogs barking now and then, cars"""
	var t := now()
	sounds = sounds.filter(func(x): return t < float(x[2]))
	for v in visitors.get_children():
		if not v is Node3D or v.get("kind") == null:
			continue
		var spd: float = v.cur_speed
		match v.kind:
			"car":
				add_sound(-8.0, v.position, 0.6)
			"dog":
				if randf() < 0.05:
					add_sound(-4.0, v.position, 0.7)            # barks
			"person":
				if spd > 0.3:
					add_sound(-26.0 if spd > 2.0 else -38.0, v.position, 0.6)
			"boar", "deer":
				if spd > 1.5:
					add_sound(-34.0, v.position, 0.6)
	if game != null:
		for p in game.players:
			if p != null and p["role"] == "runner" and p["actor"].visible:
				var a = p["actor"]
				if a.cur_speed > 0.2:
					add_sound([-38.0, -48.0, -56.0][a.ctl_posture] + (12.0 if a.cur_speed > 2.2 else 0.0), a.position, 0.6)


var _ir_curve: GradientTexture1D


func ir_curve() -> GradientTexture1D:
	if _ir_curve == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.04, 0.12, 0.3, 0.6, 1.0])
		g.colors = PackedColorArray([Color(0, 0, 0), Color(0.035, 0.035, 0.035), Color(0.3, 0.3, 0.3), Color(0.6, 0.6, 0.6), Color(0.85, 0.85, 0.85), Color(1, 1, 1)])
		_ir_curve = GradientTexture1D.new()
		_ir_curve.gradient = g
		_ir_curve.width = 256
	return _ir_curve


func _update_lens() -> void:
	"""every 0.5 s: grain from the amplification (gain), raindrops when it rains, insects at night with light"""
	var dark := is_dark()
	if dark:                                                # copies of the sky / light settings with less colour
		for k in range(2):
			var e: Environment = env.duplicate()
			e.adjustment_enabled = true
			e.adjustment_saturation = 0.0 if k == 0 else 0.4
			if k == 0:                                      # 3D-3.33: in near infrared clothes, skin and plants reflect much
				e.adjustment_brightness = 1.6                # more than in visible light - the lit area looks bright
				e.adjustment_color_correction = ir_curve()   # dark clothes too (but the unlit night stays black)
			night_envs[k] = e
	for i in range(lens_mats.size()):
		var amp: float = clamp((float(gain[i]) - 1.0) / max(0.5, gain_cap() - 1.0), 0.0, 1.0)
		var m: ShaderMaterial = lens_mats[i]
		m.set_shader_parameter("noise", 0.0 if camphys != null and camphys.active() else lens_noise * (0.08 + 0.92 * (amp if dark else amp * 0.4)) * (realism.noise_scale() if realism != null else 1.0))   # 3D-4.x: with «Kamera wie echt» the noise comes from camphys.gd (camfx)
		m.set_shader_parameter("vignette", lens_vignette)
		m.set_shader_parameter("drops", 0.55 if cond["drops"] else ((0.45 if i == 1 else 0.25) if lens_drops and weather == "rain" else 0.0))
		if fahrzeuge == null or not fahrzeuge.glaring(i):  # Paket «Fahrzeuge»: headlights blinding the lens set it themselves
			m.set_shader_parameter("glare", (0.85 if i == 0 else 0.6) if cond["glare"] and not dark else 0.0)
			m.set_shader_parameter("glare_pos", Vector2(0.84, 0.16) if i == 0 else Vector2(0.15, 0.2))
		m.set_shader_parameter("web", 1.0 if cond["web"] and i == 0 else 0.0)        # the web hangs in front of the head camera
		var lit_now: bool = dark and (ir_on() or white_light.light_energy > 0.0)
		m.set_shader_parameter("web_lit", 1.0 if lit_now else 0.0)
		m.set_shader_parameter("sway", clamp(wind * gust() / 60.0, 0.0, 1.0))
		m.set_shader_parameter("fogged", (0.8 if i == 0 else 0.5) if cond["fogged"] else 0.0)
		m.set_shader_parameter("dirt", 1.0 if cond["dirt"] and i == 0 else 0.0)
	var L: Dictionary = mw.get("lights", {})
	var lit: bool = L.get("white", false) or L.get("ir", false) or (game != null and game.guard_auto)
	insects.emitting = insects_on and dark and lit and weather != "rain" and weather != "snow" and ambient > 6.0 and scene != "schlafzimmer"   # 3D-3.96: no moths in the bedroom
	if wetter != null:
		wetter.lens_tick()                                # real-wetter: drops / fog on the lens come from linse.gd


func _build_view_camera() -> void:
	view_cam = Camera3D.new()
	view_cam.position = Vector3(6, 7, 9)
	view_cam.cull_mask = 1 | HELPER_LAYER          # 3D-3.64: helpers (route posts, net map, replay) only for the operator
	view_cam.fov = 70
	view_cam.far = 2000.0
	add_child(view_cam)
	view_cam.look_at(Vector3(0, 1, -8))
	view_cam.current = true


# ---- time, light, weather ------------------------------------------------------------------------------------------
func _night_weather_tick() -> void:
	"""3D-3.74: every night a little different - evening clear, maybe a shower before midnight, a clear cold night, dew on the
	lens towards morning and fog at dawn; the day clears up again"""
	if not night_weather or real_weather or busy_with() != "":
		return
	var h := hour()
	var day := int((now() - clock0) * speed / 86400.0 + hour0 / 24.0 + 0.5)
	if day != int(_nw["day"]):
		_nw["day"] = day
		var r := RandomNumberGenerator.new()
		r.seed = day * 7919 + 13
		var shower := r.randf() < 0.55
		var sh0 := r.randf_range(21.0, 23.5)
		_nw["plan"] = [[7.5, 18.5, "clear" if r.randf() < 0.6 else "cloudy"], [18.5, 21.0, "clear"], [sh0, sh0 + r.randf_range(0.6, 1.6), "rain" if shower else "cloudy"],
				[0.0, 4.0, "clear"], [4.0, 5.0, "cloudy"], [5.0, 7.5, "fog" if r.randf() < 0.7 else "cloudy"]]
	var want := "clear"
	for e in _nw["plan"]:
		if h >= float(e[0]) and h < float(e[1]):
			want = str(e[2])
	if want != weather and want != str(_nw["last"]):       # 3D-3.88: only when the plan changes - a weather chosen by hand stays
		weather = want
		_nw["last"] = want
	var dew := h >= 4.0 and h < 8.0                    # dew on the lens towards morning, gone when the sun warms it
	if dew != bool(_nw["fog_lens"]):
		_nw["fog_lens"] = dew
		cond["fogged"] = dew
	humidity = 92.0 if dew or weather in ["fog", "rain"] else (78.0 if h > 20.0 or h < 7.0 else 60.0)


func measuring() -> bool:
	"""3D-3.88: a measurement runs - the head and the mover must stand still (the patrol waits)"""
	return busy_with() in ["Testlauf", "Prüfstand", "Trainingsbilder", "Blinde Flecken", "Fehlalarm nachstellen"]


func typing() -> bool:
	"""3D-3.88: somebody types into a text field (search, inventory) - the keys must not move the view or the rover"""
	var f = get_viewport().gui_get_focus_owner()
	return f != null and (f is LineEdit or f is TextEdit)


func head_owner() -> String:
	"""3D-3.88: who turns the head right now (shown in «Kopf steuern»)"""
	if dataset != null and dataset.servo != null:
		return "Trainingsbilder"
	if replay != null and replay.on:
		return "Alarm-Rückblick"
	if patrol != null and patrol.active and not measuring() and not mw_following():
		return "Patrouille"
	if game != null and game.guard_auto:
		return "Spiel (Wächter)"
	return ""


func busy_with(except_ := "") -> String:
	"""3D-3.88: who has the world (time, weather, visitors) right now - a test, a measurement or a game round. While one runs,
	the automatics rest (real time and weather, night weather, surprise night, headlights, updates, lighter graphics) and a
	second one is refused instead of mixing."""
	var w := ""
	if testrun != null and testrun.running:
		w = "Testlauf"
	elif pruef != null and pruef.running:
		w = "Prüfstand"
	elif nacht != null and nacht.running:
		w = "Nacht-Testlauf"                          # Paket «Nacht-Testlauf»: the night has the world (clock, weather, visitors)
	elif abenteuer != null and abenteuer.status() != "":
		w = abenteuer.status()                        # Bergtal-Abenteuer: on the way the tour sets the clock and the weather
	elif dataset != null and dataset.busy:
		w = "Trainingsbilder"
	elif blindmap != null and blindmap.busy:
		w = "Blinde Flecken"
	elif not _fa_saved.is_empty():
		w = "Fehlalarm nachstellen"
	elif game != null and game.round_state in ["countdown", "play"]:
		w = "Spielrunde"
	elif parcours != null and (parcours.running or bool(parcours.game.get("on", false))):
		w = "Verfolgungs-Parcours"                    # 3D-4.18 (the head follows - not «measuring»: MoveEye steers it)
	elif einbruch != null and einbruch.running and not einbruch.embedded:
		w = "Einbruch-Ablauf"
	elif recorder != null and recorder.playing:
		w = "Wiedergabe"
	elif horror != null and horror.running:
		w = "Horror-Modus"                             # the nights of «Das Hospiz» (bergtal_horror.gd)
	elif maggie != null and maggie.running:
		w = "Maggie-Geschichte"                        # «Maggie und der Bergkristall» (maggie_story.gd)
	elif has_meta("trailer") and preload("res://scripts/trailer.gd").busy(self):
		w = "Trailer"                                  # ein Trailer der Geschichten läuft (trailer.gd)
	elif preload("res://scripts/ferienpark_leben.gd").task_busy(self) != "":
		w = "Ferienpark-Aufgabe"                       # Ferienpark-Leben: lost child / bike thief (the tent task: «Nacht-Testlauf»)
	elif _mw_task() != "":                             # 3D-4.x: one lock with MoveEye (a drill, a protection test … there)
		w = _mw_task()
	return "" if w == except_ else w


var _ctl_frame := -1                  # a request of MoveEye (/control) is being answered in this frame


func _mw_task() -> String:
	"""what MoveEye does with the simulator right now (sim_state «simtask_de»), not while answering MoveEye itself - its
	own steps (test_start, blindmap …) must not be refused because of its own task"""
	if _ctl_frame == Engine.get_process_frames() or now() - mw_t > 6.0:
		return ""
	var t := str(mw.get("simtask_de", ""))
	return "" if t == "" else t + " (von MoveEye)"


func open_testen() -> void:
	"""the tile «Testen»: the card «Testen» open, «Erkennung messen» open, scrolled to it"""
	if tools_body == null:
		return
	show_panel(true)
	UI.set_open(tools_body, true)
	if testen_measure != null:
		UI.set_sub_open(testen_measure, true)
	var card: Control = tools_body.get_meta("card") if tools_body.has_meta("card") else tools_body
	var sc := ui_box.get_parent() if ui_box != null else null
	if sc is ScrollContainer:
		(sc as ScrollContainer).ensure_control_visible.call_deferred(card)


func open_train() -> void:
	"""3D-4.21: the quick tile «Lernen»: card «Testen» with «Trainingsbilder» open"""
	open_testen()
	if testen_train != null:
		UI.set_sub_open(testen_train, true)


func _open_stoer() -> void:
	"""3D-4.21 (group «Entwickler»): the card «Testen» with «Störungen» open"""
	open_testen()
	if testen_stoer != null:
		UI.set_sub_open(testen_stoer, true)


func busy_msg(w: String) -> String:
	"""the same words as MoveEye: «Der Simulator ist belegt: …»"""
	return "Der Simulator ist belegt: " + w


func hour() -> float:
	return fposmod(hour0 + (now() - clock0) * speed / 3600.0, 24.0)


func set_hour(h: float) -> void:
	hour0 = fposmod(h, 24.0)
	clock0 = now()


var season := "today"                 # sun path: "today" (real date) or a month "1" .. "12" (from 3D-3.8)
var _sun_cache := [-1.0, Vector2.ZERO]
var _horizon := {}                    # real place: how high the hills are in a direction (2° steps) - mountain shadow


func jahreszeit() -> String:
	"""«Jahreszeiten & Tageslauf»: the season shared by all scenes - "fruehling" | "sommer" | "herbst" | "winter" (hook for
	Bergtal and other parts: chosen in Szene → Zeit → Jahreszeit, else from the date / month of «Jahreszeit (Sonnenbahn)»)"""
	return jahreszeiten.season() if jahreszeiten != null else "sommer"


func day_of_year() -> int:
	if season == "today":
		var d := Time.get_date_dict_from_system()
		var cum := [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
		return int(cum[int(d["month"]) - 1]) + int(d["day"])
	var m := clampi(int(season), 1, 12)
	return [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349][m - 1]


func sun_pos() -> Vector2:
	"""(elevation, azimuth from north) in degrees for the place (the map, else the middle of Switzerland), the date and the
	time on the clock (Swiss time, summer time from the end of March to the end of October) - NOAA formulas"""
	var h := hour()
	if abs(h - float(_sun_cache[0])) < 0.002:
		return _sun_cache[1]
	var la := ort_lat if ort_lat != 0.0 else 46.8
	var lo := ort_lon if ort_lon != 0.0 else 8.2
	var doy := day_of_year()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var hu := h - tz
	var g := TAU / 365.0 * (doy - 1 + (hu - 12.0) / 24.0)
	var eqt := 229.18 * (0.000075 + 0.001868 * cos(g) - 0.032077 * sin(g) - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
	var decl := 0.006918 - 0.399912 * cos(g) + 0.070257 * sin(g) - 0.006758 * cos(2 * g) + 0.000907 * sin(2 * g) - 0.002697 * cos(3 * g) + 0.00148 * sin(3 * g)
	var tst := hu * 60.0 + eqt + 4.0 * lo
	var ha := deg_to_rad(tst / 4.0 - 180.0)
	var phi := deg_to_rad(la)
	var cz := sin(phi) * sin(decl) + cos(phi) * cos(decl) * cos(ha)
	var el := 90.0 - rad_to_deg(acos(clampf(cz, -1.0, 1.0)))
	var az := fposmod(rad_to_deg(atan2(sin(ha), cos(ha) * sin(phi) - tan(decl) * cos(phi))) + 180.0, 360.0)
	_sun_cache = [h, Vector2(el, az)]
	return _sun_cache[1]


func sun_el() -> float:
	return sun_pos().x


func horizon_el(az: float) -> float:
	"""at a real place: the angle of the hills / mountains in this direction, seen from the head (0 on a flat scene)"""
	if not terrain:
		return 0.0
	var k := int(round(fposmod(az, 360.0) / 2.0)) % 180
	if not _horizon.has(k):
		var a := deg_to_rad(k * 2.0)
		var d := Vector2(sin(a), -cos(a))
		var best := -90.0
		var r := 15.0
		while r < 1600.0:
			var p := d * r
			best = max(best, rad_to_deg(atan2(ground_y(p.x, p.y) - 1.6, r)))
			r += 8.0 if r < 200.0 else 25.0
		_horizon[k] = best
	return _horizon[k]


func sun_behind_hills() -> float:
	"""1 = the sun is behind the mountains (only at a real place), 0 = free; soft over one degree"""
	var sp := sun_pos()
	return clampf((horizon_el(sp.y) - sp.x) + 0.5, 0.0, 1.0)


func clouds() -> float:
	return {"clear": 0.15, "cloudy": 0.75, "rain": 0.95, "fog": 0.6, "snow": 0.9}.get(weather, 0.2)


func light_level() -> float:
	var day: float = clamp((sun_el() + 6.0) / 18.0, 0.0, 1.0)
	var night: float = licht.night_level() if licht != null else 0.015 + 0.04 * moon * (1.0 - clouds())   # «Licht & Nacht»: from the lux
	return night + 0.95 * day * (1.0 - 0.45 * clouds())


func is_dark() -> bool:
	return light_level() < 0.12


static func no_emoji(t: String) -> String:
	"""3D-3.98: emoji and pictographs away (the window shows them as empty boxes); 3D-4.22: symbole.gd - no gap before a
	comma, a text that is only an emoji becomes a short word"""
	return preload("res://scripts/symbole.gd").clean(t).strip_edges()


func moon_phase() -> float:
	"""3D-3.98: the age of the moon 0 … 1 (0 = new moon, 0.5 = full moon) for the date of the simulation"""
	var t: float = Time.get_unix_time_from_system()
	if season != "today":
		var d0 := Time.get_datetime_dict_from_system()
		d0["month"] = int(season)
		d0["day"] = 15
		t = Time.get_unix_time_from_datetime_dict(d0)
	return fposmod((t - 947182440.0) / 86400.0 / 29.530588853, 1.0)     # new moon 6.1.2000 18:14 UTC


const CITY_SCENES := ["garten", "parkplatz", "stellplatz", "baustelle", "zuhause"]


func _update_sky() -> void:
	var el := sun_el()
	var day: float = clamp((el + 6.0) / 18.0, 0.0, 1.0)
	var cl := clouds()
	var az := sun_pos().y                                   # real path of the sun (from 3D-3.8)
	sun.rotation = Vector3(deg_to_rad(-max(el, -10.0)), deg_to_rad(180.0 - az), 0)
	sun.light_energy = (max(0.0, sin(deg_to_rad(max(el, 0.0)))) * 1.6 * (1.0 - 0.6 * cl) * cloud_shade() + (0.02 if el > -4 else 0.0)) * (1.0 - sun_behind_hills())
	sun.visible = el > -4.0
	sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_AND_SKY if sun_behind_hills() < 0.5 else DirectionalLight3D.SKY_MODE_LIGHT_ONLY   # no dark sun disk behind a mountain
	var dusk: float = max(0.0, 1.0 - abs(el - 2.0) / 10.0) if el > -8.0 else 0.0
	sun.light_color = Color(1.0, 0.95, 0.88).lerp(Color(1.0, 0.6, 0.35), dusk)
	if moon_auto:
		moon_ph = moon_phase()
		moon = snappedf(0.5 - 0.5 * cos(moon_ph * TAU), 0.01)
	sky_mat.set_shader_parameter("moon_phase", moon_ph if moon_auto else 0.5)
	moonlight.light_energy = 0.035 * moon * (1.0 - cl) * (1.0 - day)
	var top := Color(0.25, 0.45, 0.8).lerp(Color(0.55, 0.57, 0.6), cl)
	var hor := Color(0.7, 0.78, 0.88).lerp(Color(0.95, 0.65, 0.45), dusk).lerp(Color(0.7, 0.71, 0.72), cl * 0.8)
	var k: float = max(0.02, day)
	var sky_top := top * k + Color(0.01, 0.015, 0.03) * (1.0 - k)
	var sky_hor := hor * k + Color(0.02, 0.025, 0.04) * (1.0 - k)
	sky_mat.set_shader_parameter("top_color", sky_top)
	if scene in CITY_SCENES and licht == null:              # 3D-3.98: light pollution - the night sky glows orange over towns (licht.gd: Land / Dorf / Stadt)
		sky_hor += Color(0.07, 0.045, 0.025) * (1.0 - k) * (0.6 + 0.8 * cl)
		sky_top += Color(0.012, 0.009, 0.006) * (1.0 - k) * (0.5 + cl)
	sky_mat.set_shader_parameter("horizon_color", sky_hor)
	sky_mat.set_shader_parameter("ground_color", Color(0.1, 0.12, 0.08) * k if not terrain else sky_hor * 0.9)   # real place: haze below
	_sky_e_base = 0.06 + 0.94 * day
	sky_mat.set_shader_parameter("energy", _sky_e_base + _flash_boost * 0.6)
	sky_mat.set_shader_parameter("cloud_cover", clampf(cl * 1.05, 0.0, 1.0))
	sky_mat.set_shader_parameter("night", clampf(1.0 - day * 3.0, 0.0, 1.0))
	sky_mat.set_shader_parameter("cloud_light", Color(1.0, 0.97, 0.93).lerp(Color(1.0, 0.72, 0.55), dusk).lerp(Color(0.78, 0.79, 0.82), cl * 0.6) * (0.08 + 0.92 * day))
	sky_mat.set_shader_parameter("cloud_shadow", Color(0.55, 0.6, 0.7).lerp(Color(0.45, 0.46, 0.5), cl) * (0.06 + 0.94 * day))
	var wd := Vector2(0.006, 0.0025) * (0.4 + wind / 30.0)
	sky_mat.set_shader_parameter("wind", wd)
	# light from the whole sky: bluish in the sun (shadows are never black, as outside), grey when cloudy, dark at night
	env.ambient_light_color = Color(0.6, 0.68, 0.85).lerp(Color(0.72, 0.72, 0.74), cl).lerp(Color(0.9, 0.7, 0.6), dusk * 0.5)
	env.ambient_light_energy = 0.03 + (0.55 + 0.25 * cl) * day
	_amb_base = env.ambient_light_energy
	env.ambient_light_energy += _flash_boost
	var dens: float = {"clear": 0.0007, "cloudy": 0.0012, "rain": 0.006, "fog": 0.045, "snow": 0.012}.get(weather, 0.0008)
	env.fog_density = dens
	env.fog_light_color = Color(0.72, 0.74, 0.78) * (0.05 + 0.95 * day)
	rain.emitting = weather == "rain"
	if splashes != null:
		splashes.emitting = weather == "rain" and quality != "simple"
	snow.emitting = weather == "snow"
	grass_mat.set_shader_parameter("snow_amount", 0.85 if weather == "snow" else 0.0)
	grass_mat.set_shader_parameter("wet", 1.0 if weather == "rain" else 0.0)
	for gm in ground_mats:
		gm.set_shader_parameter("snow_amount", 0.85 if weather == "snow" else 0.0)
		gm.set_shader_parameter("wet", 1.0 if weather == "rain" else 0.0)
	var w_now := wind * gust()
	for fm in foliage_mats:
		fm.set_shader_parameter("wind", w_now)
	for cm in cloth_mats:
		cm.set_shader_parameter("wind", w_now)
	if fireflies != null:
		fireflies.emitting = world_fireflies and is_dark() and ambient >= 12.0 and weather in ["clear", "cloudy"] and wind < 30.0
	var dark := is_dark()
	var lit := dark and not power_off                  # 3D-3.75: a power cut - all lamps of the place are out
	window_mat.emission_energy_multiplier = 2.5 if lit else 0.0
	if is_instance_valid(door_node):                   # 3D-4.41: a world without the default house (Festival) frees them
		door_node.rotation.y = -1.3 if door_open else 0.0
	if is_instance_valid(door_light):
		door_light.light_energy = 2.5 if door_open and lit else 0.0
	for l in lamps:
		if is_instance_valid(l):
			l.light_energy = 2.2 if lit else 0.0
	for lm in lamp_mats:
		lm.emission_energy_multiplier = 3.0 if lit else 0.0
	for v in visitors.get_children():
		if v.has_method("set_night"):
			v.set_night(dark)
	if colors != null:
		colors.update()                                  # 3D-3.97: season, wet surfaces, blue hour, haze
	if licht != null:
		licht.update()                                   # «Licht & Nacht»: moon, stars, night brightness, lamps, low sun
	if jahreszeiten != null:
		jahreszeiten.update()                            # «Jahreszeiten»: bare trees, blossom, falling leaves, snow lying
	if wetter != null:
		wetter.sky_tick()                                # real-wetter: rain strength, visibility, ground fog, snow cover, lens climate


func _bg_for(read_value: float) -> Color:
	"""background colour that is read back as read_value"""
	if th_bg_raw:
		return Color(read_value, read_value, read_value)
	var c := Color(read_value, read_value, read_value).linear_to_srgb()
	return c


func eye_shine(p: Vector3) -> float:
	var L: Dictionary = mw.get("lights", {})
	if not (L.get("white", false) or L.get("ir", false)):
		return 0.05
	return clamp(30.0 / max(1.0, p.distance_to(head.global_position)), 0.0, 4.0)


func _update_temps() -> void:
	"""temperatures of the surfaces for the thermal camera: sun warms the ground by day, clear nights cool it"""
	var el := sun_el()
	var sunk: float = max(0.0, el) / 50.0 * (1.0 - sun_behind_hills())
	var cl := clouds()
	var h := hour()
	var evening := 1.0 if h >= 17.0 or h < 1.0 else 0.0
	var night := 1.0 if el < 0.0 else 0.0
	var wet := 2.0 if weather == "rain" else 0.0
	var ground := ambient + 9.0 * sunk * (1.0 - cl) - 3.5 * night * (1.0 - cl) - wet
	if weather == "snow" or (wetter != null and wetter.snow_lying()):      # real-wetter: also while the snow stays
		ground = min(ground, 0.0)
	tmats["ground"].set_shader_parameter("temp", ground)
	tmats["ground"].set_shader_parameter("far_temp", ambient - 4.0)
	tmat("road").set_shader_parameter("temp", ground + 2.0 * sunk)
	tmat("tree").set_shader_parameter("temp", ambient - 1.0 + 1.5 * night - wet)
	tmat("caravan").set_shader_parameter("temp", ambient + 6.0 * sunk + 3.0 * evening - wet)
	tmat("window").set_shader_parameter("temp", ambient + 8.0 * evening + 3.0)
	tmat("tent").set_shader_parameter("temp", ambient + 4.0 * sunk + 1.5 - wet)
	tmat("stone").set_shader_parameter("temp", ambient + 14.0 * sunk + 4.0 * evening * (1.0 - sunk) - wet)
	tmat("hill").set_shader_parameter("temp", ambient - 5.0)
	tmat("pond").set_shader_parameter("temp", ambient - 2.0)
	var sky_t := ambient - (35.0 * (1.0 - cl) + 4.0 * cl)
	if simreal != null and simreal.th_real:
		sky_t = Waerme.sky_zenith(ambient, cl, humidity)   # 3D-4.26: 8–14 µm, drier air = colder sky (waerme.gd)
	tmat("sky").set_shader_parameter("temp", sky_t)       # the sky is a big dome only the thermal camera sees (zenith)
	tmat("car").set_shader_parameter("temp", ambient + 6.0 * sunk + 3.0 * evening - wet)   # 3D-4.26 parked cars (simreal: sun)
	tmat("lamp").set_shader_parameter("temp", 45.0)       # 3D-4.26 street lamp heads (waerme_welt: only warm when lit)
	if simreal != null:
		simreal.temps()                                   # 3D-4.4: heat of the day in stones / cars / asphalt, rain, windows
	if thermsensor != null:
		thermsensor.air_update()                          # 3D-4.26: air temperature and what fog / snow swallow (shaders)
	if waerme_welt != null:
		waerme_welt.tick()                                # 3D-4.26: engines cool down, the person in the tent, lamps


# ---- every frame -----------------------------------------------------------------------------------------------------
var _slow_t := 0.0


func _process(dt: float) -> void:
	_fold_t += dt
	if _fold_t > 0.3:                                     # 3D-4.18: the fold buttons show the state
		_fold_t = 0.0
		_fold_paint()
	_lightning(dt)
	_view_capture()
	_hud_layout()
	_cpu_pill_tick(dt)
	_thumbs_tick(dt)
	# minimized: Godot stops drawing then - but the cameras must go on for MoveEye. mini.gd turns the window into a
	# small box at once; this is only the safety net (e.g. when the box cannot be shown)
	if sim_active and DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_MINIMIZED:
		_bg_t -= dt
		if _bg_t <= 0.0:
			_bg_t = 1.0 / 15.0
			RenderingServer.force_draw(false)
	_slow_t -= dt
	if _slow_t <= 0.0:
		_slow_t = 0.5
		_check_active()
		if game != null and game.open:
			game.paint()
		if testrun != null and testrun.running:
			testrun.paint()
		if sim_active:
			_update_sounds()
			_update_lens()
			_update_sky()
			_update_temps()
			_life()
		_update_status()
		_night_weather_tick()
		_perf_tick()
		_lite_tick()
		_stream_watch()
		if now() - _hour_saved_t > 20.0:
			_settings_dirty = true                         # 3D-3.76: the time of the scene is saved now and then
		if _settings_dirty:
			_save_settings()
		var _busy := busy_with()                      # 3D-3.88: no update in the middle of a test or a round
		if dev_updates and not update_busy and now() - float(_dev["t"]) > 60.0 and not bool(_dev["busy"]) and _busy == "":
			_dev_check()
		if auto_update and not update_busy and now() > next_update_check and _busy == "":
			next_update_check = now() + UPDATE_EVERY
			run_update(true, false)
	if not sim_active:
		return                                   # pause: nothing moves, nothing is drawn (net.gd still answers)
	var s: Dictionary = mw.get("servo", {})
	# the servos turn like real ones: towards the new angle with a limited speed (no jumps)
	var want_pan := -deg_to_rad(_srv_ahead(s, "pan"))
	var want_tilt := deg_to_rad(_srv_ahead(s, "tilt") - 6.0)
	if game != null and game.guard_auto:                 # the game: automatic guard or a player as guard turns the head
		want_pan = game.guard_yaw
		want_tilt = game.guard_tilt
	if patrol != null and patrol.active and not measuring() and not mw_following():   # 3D-3.61: on patrol the head swings (3D-3.88: not while measuring; 3D-3.91: MoveEye follows something -> its angles)
		want_pan = patrol.head_yaw
		want_tilt = deg_to_rad(-8.0)
	if dataset != null and dataset.servo != null:         # Trainingsbilder: the head looks where the picture needs it
		want_pan = -deg_to_rad(dataset.servo.x)
		want_tilt = deg_to_rad(dataset.servo.y - 6.0)
	if replay != null and replay.on:                     # Alarm-Rückblick: the head turns like it did then
		want_pan = -deg_to_rad(replay.servo.x)
		want_tilt = deg_to_rad(replay.servo.y - 6.0)
	var step: float = deg_to_rad(SERVO_DEG_S) * dt * weit.servo_k()     # 3D-4.17: wide camera on the head = a bit heavier
	if simint != null:
		step *= simint.servo_k()                          # 30.10.2026: under-voltage - weak and stuttering servos
	want_pan = weit.pan_clamp(want_pan)                   # ... and the cable allows only ± pan limit
	if dataset != null and dataset.servo != null:
		step *= 8.0                                      # the pictures: no need to wait for the slow servo
	_drive(dt)
	var y0: float = head.rotation.y
	var x0: float = head_pitch.rotation.x
	var sreal: bool = realism != null and realism.servo_real
	var dead := deg_to_rad(0.6) if sreal else 0.0          # 3D-3.94: an MG90S does not move for less than about half a degree
	var mech: bool = sreal and servo != null and sabotage_turn == 0.0 and not (dataset != null and dataset.servo != null)
	if mech:                                             # «Servo-Mechanik» (servo.gd): MG90S with voltage, inertia, play, overshoot, current
		servo.step(dt, want_pan, want_tilt)
		_srv["wob"] = 0.0                                # the overshoot is in the model now (no extra camera swing)
	else:
		if servo != null:
			servo.reset()
		if absf(want_pan + sabotage_turn - head.rotation.y) > dead and not (simint != null and simint.hold("pan") and sabotage_turn == 0.0):
			head.rotation.y = move_toward(head.rotation.y, want_pan + sabotage_turn, step * (6.0 if absf(sabotage_turn) > 0.0 else 1.0))
		if absf(want_tilt - head_pitch.rotation.x) > dead and not (simint != null and simint.hold("tilt")):
			head_pitch.rotation.x = move_toward(head_pitch.rotation.x, want_tilt, step)
		var vy: float = (head.rotation.y - y0) / maxf(dt, 0.0001)
		tilt_vel = (head_pitch.rotation.x - x0) / maxf(dt, 0.0001)
		if sreal and absf(float(_srv["v"])) > 0.3 and absf(vy) < 0.05:    # it stops: the light head swings a little
			_srv = {"v": vy, "wob": clampf(absf(float(_srv["v"])) * 0.012, 0.004, 0.02), "t": now(), "dir": signf(float(_srv["v"]))}
		_srv["v"] = vy
		pan_vel = vy
	cams[0].global_transform = head_pitch.global_transform.translated_local(Vector3(0, 0.0, -0.13))
	if sreal and float(_srv["wob"]) > 0.0:
		var k_: float = now() - float(_srv["t"])
		if k_ < 0.6:
			cams[0].rotate_object_local(Vector3.UP, float(_srv["dir"]) * float(_srv["wob"]) * exp(-k_ * 7.0) * sin(k_ * 38.0))
		else:
			_srv["wob"] = 0.0
	if cond["shake"]:                                    # 3D-3.74: the mast sways in the wind - the whole picture moves
		var amp: float = deg_to_rad(0.35 + 0.9 * clampf(wind * gust() / 40.0, 0.0, 1.0))
		var tt := now()
		cams[0].rotate_object_local(Vector3.UP, sin(tt * 7.3) * amp + sin(tt * 13.1) * amp * 0.4)
		cams[0].rotate_object_local(Vector3.RIGHT, sin(tt * 5.7 + 1.0) * amp * 0.6)
	cams[2].global_transform = head_pitch.global_transform.translated_local(Vector3(0.12, 0.0, -0.12))
	if _cover_mesh != null and sabotage_cover:           # 3D-3.72: the cloth hangs right in front of the lenses
		_cover_mesh.global_transform = head_pitch.global_transform.translated_local(Vector3(0.05, 0.0, -0.36))   # beyond the near plane of the cameras (0.1 m)
	weit.place()                                         # 3D-4.17: camera 1 = the wide camera (mast / base / head front / head rear)
	var L: Dictionary = mw.get("lights", {})
	var wl_on: bool = L.get("white", false) or (game != null and game.now() < game.flash_until) or (own_light and now() - mw_t >= 3.0)
	if wl_on and white_light.light_energy == 0.0 and look_at_light:
		for v in visitors.get_children():               # the light goes on: people stop and look at it for a moment
			if v.get("kind") == "person" and v.position.length() < 25.0 and not v.get("controlled"):
				v.wait_until = max(float(v.wait_until), v.now_s() + randf_range(1.0, 2.5))
				v._face(Vector3.ZERO)
				v.startle()
	white_light.light_energy = 9.0 if wl_on else 0.0
	rain.position = Vector3(0, 12, -8)
	var t := now() - clock0
	for i in range(anims.size() - 1, -1, -1):
		if anims[i].call(dt, t) == true:      # true = finished (e.g. the birds are gone)
			anims.remove_at(i)
	if spectate:
		_spectate(dt)
	elif replay != null and replay.on:
		pass                                             # the replay moves the camera itself
	elif tv != null and tv.on:
		tv.idle_cam(dt)
	else:
		_fly(dt)
	_view_overlays()
	if crosshair != null:
		crosshair.visible = rifle_on
		if rifle_on:
			crosshair.queue_redraw()
	if not capturing:
		_capture_next()


# ---- saving power ---------------------------------------------------------------------------------------------------
func connected() -> bool:
	"""MoveEye is connected: it sent its state lately or fetches pictures / thermal values"""
	if not stream_on:
		return false
	var t := now()
	return t - mw_t < 10.0 or not net.stream_demand().is_empty() or t - snap_want[0] < 10.0 or t - snap_want[1] < 10.0 or t - _th_asked < 10.0


func _check_active() -> void:
	"""every 0.5 s: is somebody looking? Window open -> everything; only MoveEye -> the world moves, but the big
	3D view is not drawn and at most 30 pictures per second; nobody -> pause with 5 frames per second (only answering)"""
	var small: bool = mini_box != null and mini_box.mini
	win_open = not small and DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_MINIMIZED
	var conn := connected()
	var playing: bool = game != null and game.busy()
	var act: bool = win_open or conn or playing or (testrun != null and testrun.running) or (einbruch != null and einbruch.running) or not eco_idle
	act = act or (nacht != null and nacht.running) or (abenteuer != null and abenteuer.status() != "")   # a night / the adventure runs also without a viewer
	if act != sim_active:
		sim_active = act
		visitors.process_mode = Node.PROCESS_MODE_INHERIT if act else Node.PROCESS_MODE_DISABLED
		if act:
			next_auto = max(next_auto, now() + 5.0)
		print("simulation " + ("runs" if act else "pauses (nobody looks)"))
	get_viewport().disable_3d = not win_open or (abenteuer != null and abenteuer.zweit != null and abenteuer.zweit.views_on())   # the big 3D view only when it can be seen (A5: not while the two views of «zu zweit» draw)
	# 3D-3.30: MoveEye saves power (nothing happens there): the simulator calculates slower too (window closed)
	var mw_saving: bool = conn and str(mw.get("eco", "")) == "saving" and not playing and not (testrun != null and testrun.running)
	var cap: int = (win_fps if win_fps > 0 else _fps0) if win_open else (60 if playing else ((12 if mw_saving else 30) if sim_active else 5))
	if Quality.lite():
		cap = Quality.FPS if cap <= 0 else mini(cap, Quality.FPS)    # 3D-4.25: Lite - at most 25 pictures per second
	Engine.max_fps = cap


# ---- pictures for MoveEye -------------------------------------------------------------------------------------
func _wanted_fps(i: int) -> float:
	if i == 1 and weit != null and not weit.installed():
		return 0.0                                       # P9: blind cover instead of the wide camera - nothing to render
	var d: Dictionary = net.stream_demand() if net != null else {}
	var f: float = float(d.get(i, 0.0))
	if i < 2 and now() - snap_want[i] < 3.0:
		f = max(f, 2.0)
	if i == 0 and headpad != null and headpad.visible:
		f = max(f, 8.0)                                  # 3D-3.77: «Kopf steuern» shows the head camera
	if i == 0 and game != null and game.guard_watching():
		f = max(f, 8.0)                                  # a player guards: he sees through the head camera
	if i == 1 and game != null and game.guard2_watching():
		f = max(f, 6.0)                                  # a second guard sees through the fixed camera
	if i == 0 and abenteuer != null and abenteuer.zweit != null:
		f = max(f, abenteuer.zweit.head_fps())           # A5: player 2 (Rollen) / the companion phone sees what MoveEye sees
	if i == 2 and now() - _th_asked < 3.0:
		f = max(f, th_fps)                               # 30.10.2026: the model (Thermal-90: 15 fps like the driver of MoveEye)
	if i == 2 and thermsensor != null:
		f = thermsensor.fps_cap(f)                     # 3D-4.26: Lite - at most 8 thermal pictures per second
	if preview_on and win_open:
		f = max(f, (2.0 if in_vm else 4.0) if i < 2 else (1.5 if in_vm else 3.0))
	return simreal.fps_cap(i, f) if simreal != null else f   # 3D-4.4: «Wie ein echter Pi 5»


var _th_asked := 0.0


func _capture_next() -> void:
	var best := -1
	var late := 0.0
	for i in range(3):
		var f := _wanted_fps(i)
		if f <= 0.0:
			continue
		var over: float = (now() - last_cap[i]) * f
		if over >= 1.0 and over > late:
			late = over
			best = i
	if best >= 0:
		_capture(best)


func _capture(i: int) -> void:
	await _mod("kamera")._capture(i)


var cloud_shadows := true             # clouds pass the sun: the light changes (from 3D-2.6; realistic cause of false alarms)
var gusts := true                     # the wind blows in gusts
var look_at_light := true             # people look at the light when it goes on
var world_cloth := true               # flags and laundry move in the wind (3D-2.9)
var world_smoke := true               # smoke from chimneys
var world_fireflies := true           # fireflies on warm nights
var cloth_mats: Array = []
var fireflies: CPUParticles3D
var lamp_share := 0.35                # at night this share of the people carries a headlamp or a phone light (3D-2.7)


func cloud_shade() -> float:
	"""1 = full sun; cloudy: now and then a cloud shadow for some seconds (faster with wind)"""
	if cond["shadows"]:                                   # condition «Wolkenschatten»: fast, deep shadows, also when clear
		var tt := now() - clock0
		var vv := 0.5 + 0.5 * sin(tt * 0.35) * cos(tt * 0.23 + 2.0)
		return 1.0 - 0.7 * smoothstep(0.4, 0.65, vv)
	if not cloud_shadows or weather in ["clear", "fog"]:
		return 1.0
	if gelaende != null and gelaende.cloud_active():
		return gelaende.shade_at_head()              # 3D-4.x: the same cloud shadow that drifts over the ground (gelaende.gd)
	var t := now() - clock0
	var w := 0.04 + wind * 0.0015
	var v := 0.5 + 0.5 * sin(t * w) * cos(t * w * 0.63 + 2.0)
	return 1.0 - 0.55 * smoothstep(0.45, 0.7, v)


func gust() -> float:
	"""the wind now: steady or in gusts (0.6 … 1.5 × the setting)"""
	if not gusts:
		return 1.0
	var t := now() - clock0
	return 0.6 + 0.9 * smoothstep(0.3, 0.9, 0.5 + 0.5 * sin(t * 0.21) * sin(t * 0.53 + 1.1))


func cpu_now() -> Dictionary:
	"""CPU of the PC and of the simulator in % (3D-3.29: also in every «here is a simulator» message, so MoveEye
	shows it before the simulation is on); null = not measured yet"""
	var d := {"pc": null, "sim": null}
	if mini_box != null:
		if float(mini_box.own["pc"]) >= 0.0:
			d["pc"] = snappedf(mini_box.own["pc"], 0.1)
		if float(mini_box.own["sim"]) >= 0.0:
			d["sim"] = snappedf(mini_box.own["sim"], 0.1)
	return d


func version() -> String:
	return VERSION


const NIGHT_SCALE := 0.15             # the night is rendered too bright for a camera: at night only this part reaches the sensor


func gain_cap() -> float:
	"""by day a camera may amplify up to 6×, at night only up to «Nachtverstärkung»: the picture stays dark like a real one"""
	return 6.0 if not is_dark() else night_gain


func ir_on() -> bool:
	"""infrared light: from MoveEye, or from the game (the guard switches it on at night)"""
	var L: Dictionary = mw.get("lights", {})
	return L.get("ir", false) or cond["ir"] or (game != null and game.guard_auto and is_dark()) \
			or (dataset != null and dataset.servo != null and is_dark())      # Trainingsbilder at night: like MoveEye, with infrared


var ir_ex := 0.5                        # 3D-4.1: exposure of the infrared picture (follows its own light, see _auto_exposure)


func _auto_exposure(i: int, img: Image) -> void:
	if i == 0 and is_dark() and ir_on() and not white_light.light_energy > 0.0:
		var sm: Image = img.duplicate()
		sm.resize(32, 18, Image.INTERPOLATE_BILINEAR)
		var sum_ := 0.0
		for y in range(18):
			for x in range(32):
				var c := sm.get_pixel(x, y)
				sum_ += (c.r + c.g + c.b) / 3.0
		var m: float = maxf(0.01, sum_ / (18.0 * 32.0))
		var ir_min: float = 0.003 if simreal != null and simreal.ir_real else 0.04   # 3D-4.4: the real camera can shorten the exposure much more
		ir_ex = clampf(ir_ex * pow(0.38 / m, 0.6), ir_min, 1.0)   # a near tent bright, the far meadow dark - not all white
		return
	var small: Image = img.duplicate()
	small.resize(32, 18, Image.INTERPOLATE_BILINEAR)
	var sum := 0.0
	for y in range(6, 18):
		for x in range(32):
			var c := small.get_pixel(x, y)
			sum += (c.r + c.g + c.b) / 3.0
	var mean: float = max(0.01, sum / (12.0 * 32.0))
	var tgt: float = realism.ae_target() if realism != null else 0.35
	var want: float = clamp(gain[i] * tgt / mean, 0.6, gain_cap())
	# 3D-3.94: a real camera needs 1-2 s to follow (headlights blind for a moment); before: a quarter per picture
	gain[i] += (want - gain[i]) * (0.1 if realism != null and realism.fx_on else 0.25)
	gain[i] = min(gain[i], gain_cap())


func _decode_thermal(img: Image) -> void:
	thermal = decode_thermal_img(img)
	if preview_on:
		_thermal_preview()


func decode_thermal_img(img: Image, fx: bool = true) -> PackedFloat32Array:
	"""the rendered thermal picture (2× size, grey = temperature) → TH_W × TH_H °C (also for the second device, 3D-3.98)"""
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	var d := img.get_data()
	var w := img.get_width()
	var h := img.get_height()                          # 30.10.2026: Thermal-90 renders 160 × 106 (90° × 67°, pixels not square)
	var out := PackedFloat32Array()
	out.resize(TH_W * TH_H)
	var real: bool = fx and thermsensor != null and thermsensor.on()     # 3D-4.26: the sensor model adds its own noise
	var nz := 0.0 if real else th_noise
	for y in range(TH_H):
		var yy := clampi(int((y + 0.5) * h / TH_H - 0.5), 0, h - 2)
		for x in range(TH_W):
			var a := (yy * w + clampi(int((x + 0.5) * w / TH_W - 0.5), 0, w - 2)) * 4
			var b := a + w * 4                         # 3D-4.26: 14-bit code (red: high 7 bits, green: low 7 bits), 4 render pixels per pixel
			var t := ((th_hi[d[a]] + th_hi[d[a + 4]] + th_hi[d[b]] + th_hi[d[b + 4]]) + (th_lo[d[a + 1]] + th_lo[d[a + 5]] + th_lo[d[b + 1]] + th_lo[d[b + 5]])) * 0.25 - 40.0
			out[y * TH_W + x] = t + (randfn(0.0, nz) if nz > 0.0 else 0.0)
	if real:
		out = thermsensor.process(out, TH_W, TH_H)    # 3D-4.26 «Wärmebild wie echt»: optics, water, noise + filter, drift
	elif fx and realism != null and realism.fx_on:     # 3D-3.98: like a real thermal module - see realism.thermal_fx()
		out = realism.thermal_fx(out, TH_W, TH_H)
	return out



func _thermal_preview() -> void:
	if thermsensor != null:                            # 3D-4.26: automatic range like the module's app, palettes
		th_preview.set_image(thermsensor.preview(thermal, TH_W, TH_H))
		return
	var lo := 1e9
	var hi := -1e9
	for v in thermal:
		lo = min(lo, v)
		hi = max(hi, v)
	var span: float = max(2.0, hi - lo)
	var im := Image.create(TH_W, TH_H, false, Image.FORMAT_RGB8)
	for y in range(TH_H):
		for x in range(TH_W):
			var f := (thermal[y * TH_W + x] - lo) / span
			im.set_pixel(x, y, _inferno(f))
	th_preview.set_image(im)


func _inferno(f: float) -> Color:
	var stops := [Color(0, 0, 0.02), Color(0.34, 0.06, 0.43), Color(0.73, 0.21, 0.33), Color(0.98, 0.55, 0.04), Color(0.99, 1.0, 0.64)]
	f = clamp(f, 0.0, 1.0) * 4.0
	var i := int(min(3.0, floor(f)))
	return stops[i].lerp(stops[i + 1], f - i)


func latest_jpg(i: int) -> PackedByteArray:
	return simreal.delayed(i, jpgs[i]) if simreal != null else jpgs[i]


func want_snapshot(i: int) -> void:
	snap_want[i] = now()


func thermal_values() -> PackedFloat32Array:
	_th_asked = now()
	return thermal


# ---- protocol with MoveEye -------------------------------------------------------------------------------------
var mw_owner := ""                     # 3D-4.9: the MoveEye that steers the simulator (uid); others only watch
var mw_owner_t := -100.0
var mw_owner_helper := false
var mw_owner_name := ""
var mw_others := {}                    # uid -> {"name", "t"} of MoveEye that only watch


func _mw_lead(d: Dictionary, host: String) -> bool:
	"""Two MoveEye on one simulator (e.g. the Pi and the AI helper on this PC) both sent the head position: the head went
	back and forth and the camera pictures flickered. Now one leads: the one that was there first, until it is silent
	4 s; a helper on this PC («--helper») gives way to a real device."""
	var uid := str(d.get("uid", ""))
	if uid == "":
		uid = str(d.get("device", "")) + "@" + host
	var helper := bool(d.get("helper", false))
	var t := now()
	if mw_owner == "" or uid == mw_owner or t - mw_owner_t > 4.0 or (mw_owner_helper and not helper):
		if uid != mw_owner and mw_owner != "" and t - mw_owner_t <= 4.0:
			mw_others[mw_owner] = {"name": mw_owner_name, "t": mw_owner_t}
		mw_owner = uid
		mw_owner_t = t
		mw_owner_helper = helper
		mw_owner_name = str(d.get("device", "MoveEye"))
		mw_others.erase(uid)
		return true
	mw_others[uid] = {"name": str(d.get("device", "MoveEye")), "t": t}
	return false


func mw_watchers() -> Array:
	"""names of the MoveEye that only watch (seen in the last 6 s) - for the card «Verbindung»"""
	var out := []
	for k in mw_others.keys():
		if now() - float(mw_others[k]["t"]) < 6.0:
			out.append(str(mw_others[k]["name"]))
	return out


func _srv_ahead(s: Dictionary, ax: String) -> float:
	"""MoveEye 2.98.35 sends the position of its motion planner (ramps) about 10 x per second and its speed: between two
	packets the head goes on with that speed (no staircase), never past the goal and at most 0.15 s ahead"""
	var deg := float(s.get(ax + "_deg", 0.0))
	if not s.has(ax + "_dps"):
		return deg
	var ahead := deg + float(s.get(ax + "_dps", 0.0)) * clampf(now() - mw_t, 0.0, 0.15)
	var goal := float(s.get(ax + "_goal", ahead))
	return clampf(ahead, minf(deg, goal), maxf(deg, goal))


func on_state(d: Dictionary, host: String) -> bool:
	if not _mw_lead(d, host):
		return false
	var old_sound: String = str(mw.get("sound", ""))
	if d.has("dev_area") and bool(d.get("dev_area", false)) != dev_area:   # 3D-4.22: MoveEye's developer switch -> group «Entwickler»
		dev_area = bool(d.get("dev_area", false))
		_settings_dirty = true
		if dev_body != null:
			_apply_simple.call_deferred()
	mw = d
	mw_t = now()
	if bt_ei != null and is_instance_valid(bt_ei):
		var L_ = d.get("lights", {})
		bt_ei.on_light(bool(L_.get("white", false)) if typeof(L_) == TYPE_DICTIONARY else false, "mw")
	var dt_ = d.get("det", null)
	if typeof(dt_) == TYPE_DICTIONARY:
		mw_det = dt_
		mw_det_t = now()
	var cp = d.get("cpu", null)
	cpu_info = cp if typeof(cp) == TYPE_DICTIONARY else {}
	mw_addr = host
	if str(d.get("sound", "")) != "" and old_sound == "":
		if flee_sound:
			_scare_all(true)
	return true


var update_node = null                # Ruhebild: the running updater (update.gd), for busy_reply()


func busy_reply():
	"""Ruhebild (MoveEye 639y): what keeps the simulator busy right now - {"what": "update", "ver", "pct", "phase"} while an
	update comes / loads / is installed, {"what": "scene"} while a place is loading; null otherwise"""
	if update_node != null and is_instance_valid(update_node):
		var b: Dictionary = update_node.busy()
		if not b.is_empty():
			return b
	if geo != null and geo.busy:
		return {"what": "scene"}
	return null


func world_reply() -> Dictionary:
	var press := pressure
	if storm_t > 0.0:
		press -= min(6.0, (now() - storm_t) / 180.0 * 6.0)
	# Aufräumen 2 (30.10.2026): one field list with MoveEye (simulator3d/schnittstelle.json, checked at the start by
	# schnittstelle.gd and in MoveEye's self-test); «sim_time» (= clock), «active» (always on while MoveEye is connected) and
	# «weather» (= forecast.weather) are no longer sent
	var r := {"v": 1, "ok": true, "dark": is_dark(), "ambient_c": snappedf(ambient, 0.1),
			"pressure_hpa": snappedf(press, 0.1), "wind_kmh": snappedf(wind, 0.1), "last_event": next_event_id - 1,
			"pid": OS.get_process_id(), "sound_db": snappedf(sound_db(), 0.1) if sound_on else null,
			"sound_ev": sound_events() if sound_on else null, "sound_ev_last": sound_ev_id,
			"mic": mikro.reply() if mikro != null and mikro.real_on and sound_on else null,   # real-pir-ton: level, background, sources -> MoveEye 558p (listening)
			"solar": solar_reading(), "gps": gps_reading(),
			"humidity": snappedf(humidity, 1.0), "mover": mover_on,   # humidity: MoveEye's climate sensor (060, field h)
			"pc_cpu": snappedf(mini_box.own["pc"], 0.1) if mini_box != null and float(mini_box.own["pc"]) >= 0.0 else null,
			"sim_cpu_own": snappedf(mini_box.own["sim"], 0.1) if mini_box != null and float(mini_box.own["sim"]) >= 0.0 else null,
			"cores": OS.get_processor_count(), "mw_cmd": mw_cmd if not mw_cmd.is_empty() else null,
			"shut": game.shut.log_tail() if game != null and game.shut != null else null,   # 3D-4.x: «Auslöser» hits -> MoveEye's test inbox
			"head_deg": [snappedf(-rad_to_deg(head.rotation.y), 0.01), snappedf(rad_to_deg(head_pitch.rotation.x) + 6.0, 0.01)] if head != null else null,   # MoveEye 2.98.35: where the head really is (servo diagnosis)
			"wide": weit.state() if weit != null else null,   # 3D-4.17: the mount of the wide camera (MoveEye 163 at once)
			"game_live": smalltv.game_live() if smalltv != null else null}   # 3D-4.19: Spiel-Anzeige auf dem SmallTV (MoveEye 552)
	r["busy"] = busy_reply()                        # Ruhebild (MoveEye 639y): update / place loading -> calm picture there
	r["buttons"] = statusled.reply() if statusled != null else null   # die Tasten des Geräts wie ein GPIO (MoveEye 163a)
	r["horror"] = horror.reply() if horror != null else null   # Horror-Modus: neue «Aufnahmen» -> MoveEye Verlauf (539a)
	r["spieltest"] = spieltest.reply() if spieltest != null else null   # Spieltest-Assistent: Meldung nach jeder Runde -> MoveEye 635a (Push)
	r["sky"] = licht.reply() if licht != null else null   # «Licht & Nacht»: lux am Gerät, Dämmerung, Sonne, Mond (MoveEye liest es noch nicht)
	r["season"] = jahreszeiten.reply() if jahreszeiten != null else null   # «Jahreszeiten»: Jahreszeit, Sonnenauf-/untergang, Belegung (MoveEye liest es noch nicht)
	r["egg"] = bt_ei.reply() if bt_ei != null and is_instance_valid(bt_ei) else null   # Bergtal-Geheimnis (nur wenn es etwas zu zeichnen gibt) -> MoveEye 639z
	if simwerte != null:
		r.merge(simwerte.reply())                     # Simulator-Werte: battery, pi_temp, net, clock, place, forecast (power.gd)
	return r


var schnitt = null                     # schnittstelle.gd (Aufräumen 2)
var maggie = null                      # maggie_story.gd: «Maggie und der Bergkristall» (API für maggie_hund / maggie_gefahr)
var horror = null                      # bergtal_horror.gd: Bergtal · Horror-Modus (Hook für die Stimmungswahl: horror.mood_slot / open_from_mood)
var spieltest = null                   # spieltest.gd: Spieltest-Assistent (Haken für Spiele: Spieltest.ereignis(modus, art, daten))
var bt_ei = null                       # bergtal_ei.gd (Bergtal): reads the white light, answers {"action": "egg"}, world_reply «egg»
var own_light := false                 # the light button here while no MoveEye is connected (bergtal_ei.gd hears it too)
var klang = null                       # klang.gd: Spielton (Musik, Effekte, Umgebung, Klicks - nur in Spielen und Geschichten)
var mw_cmd := {}                       # 3D-3.71: a request to MoveEye (button here): {"id": unix ms, "op": refscan | refcompare | refstop}
var bike_node: Node3D = null
var refscan_label: Label
var surprise_label: Label              # 3D-3.75
var ds_label: Label


func _pad_test() -> void:
	"""3D-3.97: the controller test window (padtest.gd) on its own layer above everything"""
	if padtest == null:
		var cl := CanvasLayer.new()
		cl.layer = 60
		add_child(cl)
		padtest = preload("res://scripts/padtest.gd").new()
		padtest.main = self
		cl.add_child(padtest)
	padtest.visible = not padtest.visible


func _no_pad_ui_nav() -> void:
	"""3D-3.97: Godot moves the focus of the menus with the sticks by itself - a drifting stick then jumps through the
	controls. The sticks only steer what the simulator asks for (explore.gd); the D-pad still works in menus."""
	# 3D-4.13: the buttons of the controller too - A would else press the last clicked button while it switches the light;
	# the menus with the controller come from padmap.gd (Start = menu, ✚ / left stick, A = select, B = back)
	for act in ["ui_left", "ui_right", "ui_up", "ui_down", "ui_focus_next", "ui_focus_prev", "ui_accept", "ui_select", "ui_cancel",
			"ui_page_up", "ui_page_down", "ui_home", "ui_end"]:
		if not InputMap.has_action(act):
			continue
		for ev in InputMap.action_get_events(act):
			if ev is InputEventJoypadMotion or ev is InputEventJoypadButton:
				InputMap.action_erase_event(act, ev)


func mw_look(dir: String, step := 3.0) -> void:
	"""3D-3.77: turn the head of MoveEye from here (MoveEye 2.95.103: op «look»)"""
	mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(mw_cmd.get("id", 0)) + 1), "op": "look", "dir": dir, "step": step}


func mw_light(on: bool) -> void:
	if now() - mw_t >= 3.0:                            # no MoveEye: the light of the simulator itself
		own_light = on
		if bt_ei != null and is_instance_valid(bt_ei):
			bt_ei.on_light(on, "sim")
	mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(mw_cmd.get("id", 0)) + 1), "op": "light", "on": on}


func mw_follow_on() -> bool:
	"""3D-3.91: «Folgen» of MoveEye is switched on (MoveEye 2.98.1 sends it with the servo)"""
	return now() - mw_t < 3.0 and bool(mw.get("servo", {}).get("track", false))


func mw_following() -> bool:
	"""MoveEye follows something right now - then its head angles win over the patrol"""
	return now() - mw_t < 3.0 and bool(mw.get("servo", {}).get("tracking", false))


func mw_track(on: bool) -> void:
	"""3D-3.91: «Verfolgen» here switches «Folgen» of MoveEye (one mode in both)"""
	mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(mw_cmd.get("id", 0)) + 1), "op": "track", "on": on}
	start_info = "Verfolgen %s: der Kopf hält Personen, Tiere und Bewegtes in der Bildmitte" % ("ein" if on else "aus")


func mw_request(op: String) -> void:
	"""a button here asks MoveEye for something; it fetches the request with its next state (about 10 times a second)"""
	mw_cmd = {"id": int(Time.get_unix_time_from_system() * 1000.0), "op": op}
	start_info = {"refscan": "MoveEye: Referenz-Scan angefordert …", "refcompare": "MoveEye: Vergleich angefordert …", "refcompare_day": "MoveEye: Vergleich mit der Tag-Referenz …", "refstop": "MoveEye: Scan abbrechen …"}.get(op, op)


func set_bike(on: bool) -> void:
	"""test aid for the reference scan: the bike is gone / back"""
	set_prop("Velo", on)


var home_items: Array = []             # 3D-3.73: the things of «Mein Zuhause» (user://zuhause.json)
var home_editor: Control = null
const HOME_FILE := "user://zuhause.json"


func home_load() -> void:
	if FileAccess.file_exists(HOME_FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(HOME_FILE))
		if d is Array:
			home_items = d


func home_save() -> void:
	var f := FileAccess.open(HOME_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(home_items, " "))


func home_rebuild() -> void:
	if scene == "zuhause":
		set_scene("zuhause")


var test_props := {}                   # 3D-3.72: name -> node the test aids take away (set by scenes.gd)
var sabotage_cover := false            # the head camera is covered (cloth over the lens)
var sabotage_turn := 0.0               # somebody turned the head by hand (radians, on top of the servo)
var _cover_mesh: MeshInstance3D = null


func set_prop(name_: String, on: bool) -> void:
	var n = test_props.get(name_, null)
	if n != null and is_instance_valid(n):
		n.visible = on
		start_info = "Testhilfe: %s %s" % [name_, "wieder da" if on else "weggenommen"]


func _sabotage_btn(k: String) -> void:
	if k == "cover":
		set_sabotage(not sabotage_cover, null)
	elif k == "turn":
		set_sabotage(null, 0.0 if sabotage_turn != 0.0 else 90.0)
	else:
		set_sabotage(false, 0.0)


func set_sabotage(cover, turn) -> void:
	"""3D-3.72: sabotage test - the head camera covered, or the head turned away by hand (MoveEye does not know)"""
	if cover != null:
		sabotage_cover = bool(cover)
		if _cover_mesh == null:
			_cover_mesh = MeshInstance3D.new()
			var q := QuadMesh.new()
			q.size = Vector2(0.9, 0.7)
			_cover_mesh.mesh = q
			var mt := StandardMaterial3D.new()
			mt.albedo_color = Color(0.06, 0.05, 0.05)
			mt.cull_mode = BaseMaterial3D.CULL_DISABLED
			_cover_mesh.material_override = mt
			_cover_mesh.layers = 1 | 2
			add_child(_cover_mesh)
		_cover_mesh.visible = sabotage_cover
	if turn != null:
		sabotage_turn = deg_to_rad(float(turn))
	start_info = "Sabotage-Test: " + ("Kamera abgedeckt" if sabotage_cover else ("Kopf um %d° weggedreht" % int(rad_to_deg(sabotage_turn)) if sabotage_turn != 0.0 else "aus"))


var _night_test := {"step": "", "t": 0.0, "hour": 12.0}


func ref_night_test() -> void:
	"""3D-3.72: the reference by day, the comparison at night with infrared - how well does it work in the dark?"""
	_night_test = {"step": "day0", "t": now(), "hour": hour()}
	set_hour(12.0)
	start_info = "Nacht-Test: es wird Tag …"


func _night_test_tick() -> void:
	if str(_night_test["step"]) == "":
		return
	var r = mw.get("refscan", null)
	if typeof(r) != TYPE_DICTIONARY or now() - float(_night_test["t"]) < 4.0:
		return
	var idle: bool = str(r.get("busy", "")) == "" and int(r.get("cmd_seen", 0)) >= int(mw_cmd.get("id", 0))
	if not idle:
		return
	if _night_test["step"] == "day0":                  # MoveEye has seen the day (a few states later): the reference
		_night_test["step"] = "day"
		_night_test["t"] = now()
		mw_request("refscan")
		start_info = "Nacht-Test: Referenz am Tag wird aufgenommen …"
		return
	if _night_test["step"] == "day":
		_night_test["step"] = "night"
		_night_test["t"] = now()
		set_hour(23.0)
		_night_test["step"] = "night0"
		start_info = "Nacht-Test: es wird Nacht …"
	elif _night_test["step"] == "night0":
		_night_test["step"] = "night"
		_night_test["t"] = now()
		mw_request("refcompare_day")                   # the night picture against the day reference
		start_info = "Nacht-Test: Vergleich in der Nacht …"
	elif _night_test["step"] == "night":
		_night_test["step"] = ""
		start_info = "Nacht-Test fertig – Bericht in MoveEye (Werkzeuge → Referenz-Scan)"


func refscan_text() -> String:
	"""what MoveEye tells about its reference scan (with its state)"""
	var r = mw.get("refscan", null)
	if typeof(r) != TYPE_DICTIONARY:
		return "MoveEye: noch keine Angaben (verbinden, MoveEye ab 2.95.97)"
	if str(r.get("busy", "")) != "":
		return "MoveEye %s: Richtung %d von %d …" % ["scannt" if r["busy"] == "scan" else "vergleicht", int(r.get("step", 0)), int(r.get("n", 0))]
	var s := ("Referenz: %d Richtungen" % int(r.get("ref_n", 0))) if r.get("ref", false) else "Noch keine Referenz"
	var l = r.get("last", null)
	if typeof(l) == TYPE_DICTIONARY:
		s += " · letzter Vergleich: %d fehlt, %d neu, %d verändert" % [int(l.get("missing", 0)), int(l.get("new", 0)), int(l.get("changed", 0))]
		var gone: Array = l.get("gone", [])
		if not gone.is_empty():
			s += "\n🚨 Bewacht und weg: " + ", ".join(PackedStringArray(gone.map(func(x): return str(x))))
	return s


func info() -> Dictionary:
	return {"v": 1, "name": Versionen.label(VERSION), "version": VERSION, "mw_min": preload("res://scripts/abgleich.gd").MW_MIN, "host": host_name(),   # «version»: Versionierung 3.0.0 (MoveEye 300 sim_versions); «mw_min»: 3 tracks (abgleich.gd, MoveEye 639zb)
			"cameras": [{"id": 0, "name": "Head camera (NoIR)", "w": CAM_W[0], "h": CAM_H[0], "fps": CAM_FPS[0], "fov_h": CAM_FOV[0], "fov_v": 41.0, "on_head": true, "noir": true},
						weit.cam_info()],          # 3D-4.17: the wide camera with its mount (weitwinkel.gd)
			"thermal": simint.thermal_info() if simint != null else {"w": TH_W, "h": TH_H, "fps": th_fps, "fov_h": TH_FOV, "fov_v": 35.0, "unit": "C", "on_head": true},
			"view": {"input": 1, "path": "/view.mjpg", "padview": 1},
			"features": preload("res://scripts/ui_gemeinsam.gd").features(),   # P1: what this simulator can (menu1 = gids sys / extras …)
			"sensors": [{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"}, {"name": "Gas Wohnwagen", "kind": "gas"}, {"name": "Velo", "kind": "tag"},
						{"name": "PIR Gerät", "kind": "pir"}],     # real-pir-ton: AS312 at the front of the housing (pir.gd)
			"helper": {"port": mwpc.HELPER_PORT, "code": str(mwpc.helper.get("code", "")), "accel": str(mwpc.helper.get("accel", ""))} if mwpc != null and mwpc.helper.has("code") else null}


func add_event(sensor: String, kind: String, active = null) -> void:
	events.append({"id": next_event_id, "t": now(), "sensor": sensor, "kind": kind, "active": active})
	next_event_id += 1
	if events.size() > 500:
		events = events.slice(events.size() - 500)


func events_since(n: int) -> Array:
	var out := []
	for e in events:
		if int(e["id"]) > n:
			out.append(e)
	return out


# ---- visitors ----------------------------------------------------------------------------------------------------------
func time_scale_visitors() -> float:
	return visitor_speed


func spawn(kind: String, from = null, to = null) -> Node3D:
	if kind.begins_with("berg_"):
		var bt = scenes.data.get("bergtal", null)                  # 3D-4.x: the animals and events of the «Bergtal» (bergtal.gd)
		return bt.spawn_kind(kind, from, to) if bt != null else null
	if simreal != null and simreal.is_kind(kind):
		return simreal.spawn_kind(kind, from, to)     # 3D-4.4: hood, backpack, phoning, groups, edge sneaker, deer lying ...
	if umgebung != null and umgebung.is_kind(kind):
		return umgebung.spawn_kind(kind, from, to)    # 3D-4.x: e-scooter, wheelchair, robots, cat on the fence, chickens …
	if szenen != null and szenen.is_kind(kind):
		return szenen.spawn_kind(kind, from, to)      # 3D-4.x: on your pitch, camouflage / crawling, bike thief (szenenplus.gd)
	if menschen != null and menschen.is_kind(kind):
		return menschen.spawn_kind(kind, from, to)    # P10: family, standing and talking, sitting, WC walk, gaits (menschen.gd)
	if tiere != null and tiere.is_kind(kind):
		return tiere.spawn_kind(kind, from, to)       # Paket «Tiere»: free dog, crows, magpies, gulls
	if kids_on and not kids_scary and kind in ["wolf", "lynx", "boar"]:
		kind = "hare"                             # 3D-3.69: Kinder-Modus without wild animals if so set
	if kids_on and not kids_thief and kind in ["thief", "burglar", "drunk"]:
		kind = "person"
	var depth := randf_range(6.0, 22.0)
	var side := 1.0 if randf() < 0.5 else -1.0
	var a: Vector3 = from if from != null else Vector3(-side * (depth * 1.6 + 6.0), 0, -depth)
	var b: Vector3 = to if to != null else Vector3(side * (depth * 1.6 + 6.0), 0, -depth)
	var spd: float = {"person": 1.3, "elderly": 0.7, "child": 1.0, "jogger": 2.8, "fox": 2.0, "boar": 1.5, "deer": 1.6, "cat": 1.1, "dog": 1.8, "badger": 0.9,
			"hare": 1.9, "hedgehog": 0.3, "car": 11.0, "wolf": 1.7, "marten": 1.5, "squirrel": 1.6,
			"cyclist": 4.6, "stroller": 1.1, "drunk": 0.75, "courier": 1.8, "police": 1.2, "cow": 0.8, "sheep": 0.9, "horse": 1.4,
			"chamois": 1.7, "ibex": 1.1, "lynx": 1.5, "tractor": 5.5, "moto": 14.0, "van": 10.0, "camper": 9.0}.get(kind, 1.3)
	var v = Actor.new()
	visitors.add_child(v)
	var sd := -1
	if recorder != null and recorder.recording:             # the recording keeps the seed: the replay has the same look
		sd = randi()
		seed(sd)
	if menschen != null:
		menschen.before_build(kind)                 # P10: height, clothes, hood, bag … of this figure (Actor.npc_look)
	v.setup(self, kind, a, b, spd * randf_range(0.85, 1.15))
	if menschen != null:
		menschen.after_build(v, kind)               # P10: vest, bag, bike, own pace, gentle bends, children run about
	if privat != null:
		privat.on_spawn(v)                          # Wunsch Nr. 2: from main.visit(): keeps off your pitch (privatplatz.gd)
	if tiere != null:
		tiere.on_spawn(v)                         # Paket «Tiere»: the real walking speed of the animal
	v.set_night(is_dark())
	if fahrzeuge != null:
		fahrzeuge.on_spawn(v)                     # Paket «Fahrzeuge»: lights, doors, heat, speed
	if sd >= 0:
		recorder.note_spawn(v, sd)
		randomize()
	if visitlog != null:
		visitlog.add(v)                           # 3D-3.80: the diary of the simulator
	return v


func car(kind_ := "car") -> void:
	var side := 1.0 if randf() < 0.5 else -1.0
	if scenes.data.has("road_line"):                      # a real place: along the nearest road (right-hand traffic)
		var pts := []
		var l: PackedVector2Array = scenes.data["road_line"]
		for i in range(l.size()):
			if l[i].length() < 140.0:
				pts.append(l[i])
		if side < 0:
			pts.reverse()
		if pts.size() >= 2:
			var path := []
			for i in range(pts.size()):
				var dd: Vector2 = (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]).normalized()
				var q: Vector2 = pts[i] + Vector2(-dd.y, dd.x) * -1.3
				path.append(Vector3(q.x, 0, q.y))
			var v = spawn(kind_, path[0], path[1])
			for i in range(2, path.size()):
				v.route.append(path[i])
			return
	var z: float = scenes.data.get("road_z", -28.0)
	var lz: float = z - side * 1.2
	if fahrzeuge != null and fahrzeuge.fz_real:
		lz = fahrzeuge.lane_z(side)                       # Paket «Fahrzeuge»: on the right lane
	spawn(kind_, Vector3(-side * 90.0, 0, lz), Vector3(side * 90.0, 0, lz))


func visit(k: String) -> void:
	"""Wunsch Nr. 2 (privatplatz.gd): the persons of a normal visit keep off your pitch - not the burglars, thieves, guests
	and deliveries (privatplatz.AUSNAHMEN)"""
	var pv: bool = privat != null and not privat.exempt(k)
	if pv:
		privat.ctx += 1
	_visit_kind(k)
	if pv:
		privat.ctx -= 1


func _visit_kind(k: String) -> void:
	"""a visitor that fits the scene: also the special ones (a car parks, somebody sits on the bench, an animal comes to the feeder)"""
	if k == "car":
		car()
	elif k == "car_park" and fahrzeuge != null and fahrzeuge.fz_real:
		fahrzeuge.arrive("car")                                # Paket «Fahrzeuge»: parks, people get out, comes back later
	elif k == "car_park":
		var c = spawn("car", Vector3(90, 0, -31.0), Vector3(26, 0, -31.0))
		scenes.park_route(c)
	elif k == "bench":
		var side := 1.0 if randf() < 0.5 else -1.0
		var p = spawn("person", Vector3(30.0 * side, 0, -18.0), Vector3(0, 0, -16.8))
		scenes.bench_route(p, "bench" if randf() < 0.6 else "bench2")
	elif k.begins_with("feed_"):
		var a = spawn(k.substr(5), Vector3(randf_range(-25, 25), 0, -45.0), Vector3(0, 0, -16))
		scenes.feed_route(a)
	elif k == "dogwalk":                                       # somebody walks the dog
		var w = spawn("person")
		var dg = spawn("dog", w.position + Vector3(1.0, 0, 1.0), w.target)
		simreal.leash(w, dg)                                   # 3D-4.4: on a leash (or free as before, «Verhalten»)
	elif k == "herd":                                          # a few deer together
		var lead = spawn("deer")
		for i in range(randi_range(1, 3)):
			var o := Vector3(randf_range(-2.5, 2.5), 0, randf_range(1.0, 3.5))
			var d2 = spawn("deer", lead.position + o, lead.target + o)
			d2.speed = lead.speed
			if randf() < 0.5:
				d2.body_root.scale *= 0.7                        # a young one
	elif k in ["tractor", "moto", "van", "camper"]:            # vehicles (3D-3.39; camper: fahrzeuge.gd): along the road like a car
		car(k)
	elif k == "cyclist":                                       # on the road (or across the meadow)
		var z0: float = scenes.data.get("road_z", -28.0) + 0.6
		var sd := 1.0 if randf() < 0.5 else -1.0
		if scenes.data.has("road_line"):
			car("cyclist")
		else:
			spawn("cyclist", Vector3(-sd * 80.0, 0, z0), Vector3(sd * 80.0, 0, z0))
	elif k == "couple":                                        # two people side by side, now and then they stop together
		var a = spawn("person")
		var b = spawn("person", a.position + Vector3(0.0, 0, 0.9), a.target)
		b.leader = a
		b.speed = a.speed * 1.3
		b.follow_off = Vector3(0.8, 0, 0.1)
	elif k == "cows" or k == "sheep_flock":                    # a herd moves slowly over the meadow
		var ak := "cow" if k == "cows" else "sheep"
		var lead2 = spawn(ak)
		lead2.speed *= 0.8
		for i in range(randi_range(2, 4) if ak == "cow" else randi_range(4, 8)):
			var o2 := Vector3(randf_range(-3.0, 3.0), 0, randf_range(1.0, 5.0)) * (1.6 if ak == "cow" else 1.0)
			var f2 = spawn(ak, lead2.position + o2, lead2.target + o2)
			f2.speed = lead2.speed
	elif k == "horse_walk":                                    # somebody leads a horse
		var w2 = spawn("person")
		w2.speed = 1.2
		var hs = spawn("horse", w2.position + Vector3(0.9, 0, 1.6), w2.target)
		hs.leader = w2
		hs.speed = 1.6
		hs.follow_off = Vector3(0.9, 0, 1.6)
	elif k == "courier":                                       # brings a pizza to the door, waits, goes back
		var door2: Vector3 = obj["door"]
		var st2 := Vector3(30.0 if randf() < 0.5 else -30.0, 0, scenes.data.get("road_z", -28.0) + 1.0)
		var c2 = spawn("courier", st2, door2 + Vector3(0, 0, 0.8))
		c2.route = [[door2 + Vector3(0, 0, 0.8), 8.0, 0.0], st2]
	elif k == "police":                                        # a round past the caravan and the tent, with a torch at night
		var d3: Vector3 = obj["door"]
		var p3: Vector3 = obj["pir"]
		var s3 := Vector3(-32.0, 0, -12.0)
		var c3 = spawn("police", s3, d3 + Vector3(1.5, 0, 1.5))
		c3.route = [[d3 + Vector3(1.5, 0, 1.5), 4.0, 0.0], p3 + Vector3(2.0, 0, 2.0), [p3 + Vector3(2.0, 0, 2.0), 3.0, 0.0], Vector3(32.0, 0, -14.0)]
	elif k == "drunk":                                         # staggers in a zigzag
		var dz := randf_range(-18.0, -7.0)
		var sd2 := 1.0 if randf() < 0.5 else -1.0
		var c4 = spawn("drunk", Vector3(-sd2 * 30.0, 0, dz), Vector3(-sd2 * 20.0, 0, dz + 2.0))
		for i in range(1, 9):
			c4.route.append(Vector3(-sd2 * 30.0 + sd2 * i * 7.0, 0, dz + (2.5 if i % 2 == 0 else -2.5) + randf_range(-1.0, 1.0)))
		if randf() < 0.5:
			c4.route.insert(3, [c4.route[2], 6.0, 0.0])               # stops, sways
	elif k in ["burglar", "sneaker", "bbq", "homecoming", "parcel", "fox_trash", "boar_group", "kids_tag", "mowing"]:
		if k == "parcel":
			stories.homecoming(true)
		else:
			stories.call(k)
	elif k == "bats":
		_night_flyers(false)
	elif k == "owl":
		_night_flyers(true)
	elif k == "garden_person":
		var side := 1.0 if randf() < 0.5 else -1.0
		var g = spawn("person", Vector3(side * 35.0, 0, -30.5), Vector3(0, 0, -30.0))
		scenes.garden_route(g)
	else:
		spawn(k)


func thief() -> void:
	"""somebody sneaks to the bike, kneels at it with a torch, then goes to the caravan door - and runs away"""
	if kids_on and not kids_thief:
		visit("person")                           # 3D-3.88: Kinder-Modus without thief - an ordinary walker instead
		return
	var bike: Vector3 = obj["bike"]
	var door: Vector3 = obj["door"]
	var v = spawn("person", Vector3(25, 0, -14), bike + Vector3(0.6, 0, 0.4))
	v.speed = 0.9
	v.add_torch()
	v.route = [[bike + Vector3(0.6, 0, 0.4), 7.0, 1.0], door, [door, 5.0, 0.6], Vector3(-30, 0, -6)]


func _life() -> void:
	var t := now()
	if auto_visitors and t > next_auto:
		var au: Array = Scenes.AUTO.get(scene, Scenes.AUTO["camping"])
		var kinds := _mixed(au[0] if preset_kinds.is_empty() else preset_kinds)
		if visitors.get_child_count() < max_visitors and not kinds.is_empty():
			var kk: String = life.pick(kinds) if daily_life else kinds[randi() % kinds.size()]
			if menschen != null:
				kk = menschen.pick_person(kk)             # P10: «Anteil Kinder», groups
			if kk != "" and (jahreszeiten == null or jahreszeiten.accept_visit(kk, PEOPLE_KINDS)) and (statisten == null or statisten.accept(kk)):   # «Jahreszeiten»: campsite by season
				visit(kk)
		var occ: float = maxf(1.0, jahreszeiten.visit_factor()) if jahreszeiten != null else 1.0   # high season: people more often
		next_auto = t + randf_range(au[1], au[2]) / max(0.1, visit_rate * occ)
	if cond["headlights"] and is_dark() and t > _next_headlight and busy_with() in ["", "Testlauf", "Prüfstand"]:     # condition «Scheinwerfer»: a car now and then
		_next_headlight = t + randf_range(9.0, 15.0)
		car()
	if t > next_birds:
		next_birds = t + randf_range(50.0, 140.0)
		if not is_dark() and weather != "rain":
			_birds()
	var L: Dictionary = mw.get("lights", {})
	if flee_light and L.get("white", false) and is_dark():
		_scare_all(false)
	var tent: Vector3 = obj["pir"]
	for v in visitors.get_children():
		if v.kind == "person" and not v.pir_done and v.position.distance_to(tent) < 3.0:
			v.pir_done = true
			add_event("PIR Zelt", "pir")
		var lit: bool = bool(L.get("white", false)) and is_dark() and v.position.distance_to(head.global_position) < 18.0
		if v.has_meta("sneak") and not v.has_meta("fled"):       # 3D-3.74: the sneaker - light: freeze and torch off; siren: away
			if str(mw.get("sound", "")) != "":
				v.set_meta("shy", true)
			elif lit and not v.has_meta("froze"):
				v.set_meta("froze", true)
				if v.torch != null:
					v.torch.light_energy = 0.0
					v.torch.visible = false
				v.route.push_front([v.position, randf_range(8.0, 15.0), 2.0, head.global_position])
				v.target = v.position
				v.wait_until = now() + randf_range(8.0, 15.0)
				v.prone = 1.0
		if v.has_meta("shy") and not v.has_meta("fled") and (lit or str(mw.get("sound", "")) != ""):
			v.set_meta("fled", true)                                     # the burglar: light or siren - and away (3D-3.40)
			v.startle()
			v.route = [Vector3(v.position.x + (40.0 if v.position.x > 0 else -40.0), 0, v.position.z + 12.0)]
			v.target = v.route.pop_front()
			v.speed = 4.2
			v.crouch = 0.0
			v.wait_until = 0.0
			continue
		if v.kind == "person" and v.torch != null and v.route.size() > 0 and str(mw.get("sound", "")) != "":
			v.route = [Vector3(v.position.x + 40.0, 0, v.position.z + 10.0)]      # the siren: the thief runs away
			v.target = v.route.pop_front()
			v.speed = 4.0
			v.crouch = 0.0
			v.wait_until = 0.0


const VISIT_EMOJI := {"person": "🚶", "elderly": "🧓", "child": "🧒", "jogger": "🏃", "fox": "🦊", "deer": "🦌", "boar": "🐗", "cat": "🐈", "dog": "🐕",
		"badger": "🦡", "hare": "🐇", "hedgehog": "🦔", "wolf": "🐺", "marten": "🐾", "squirrel": "🐿", "car": "🚗", "thief": "🦹",
		"dogwalk": "🦮", "herd": "🦌", "car_park": "🅿", "bench": "🪑", "feed": "🌾", "garden_person": "🚪", "clear": "🧹",
		"cyclist": "🚴", "stroller": "👶", "courier": "🍕", "police": "👮", "drunk": "🥴", "couple": "👫", "horse_walk": "🐎",
		"cow": "🐄", "sheep": "🐑", "horse": "🐎", "chamois": "🐐", "ibex": "🐐", "lynx": "🐆", "cows": "🐄", "sheep_flock": "🐑",
		"bats": "🦇", "owl": "🦉", "tractor": "🚜", "moto": "🏍", "van": "🚐", "burglar": "🥷", "sneaker": "🕵", "bbq": "🍖", "homecoming": "🏠",
		"parcel": "📦", "fox_trash": "🗑", "boar_group": "🐗", "kids_tag": "🏃", "mowing": "🌾", "night_lapse": "🌙"}
# presets of «Besuch» (3D-3.38): [id, name, auto, daily life, who comes, how often, at most]
const VISIT_PRESETS := [["calm", "Ruhige Nacht – selten jemand", true, false, "mixed", 0.4, 4],
		["burglary", "Einbruch-Nacht – Einbrecher, Diebe, Polizei", true, false, "mixed", 1.2, 6, ["burglar", "sneaker", "thief", "police", "drunk", "cat", "fox", "bats"]],
		["grill", "Grillabend – Gäste, Grill, Kinder", true, false, "mixed", 1.5, 16, ["bbq", "couple", "person", "child", "kids_tag", "dogwalk", "stroller", "bats", "homecoming"]],
		["farm", "Bauernhof – Kühe, Schafe, Traktor", true, false, "mixed", 1.2, 16, ["cows", "sheep_flock", "tractor", "mowing", "horse_walk", "cat", "dog", "person", "fox"]],
		["wildlife", "Wildtiere – Fuchs am Abfall, Wildschweine, Luchs", true, false, "mixed", 1.5, 12, ["fox_trash", "boar_group", "lynx", "deer", "herd", "badger", "hedgehog", "owl"]],
		["camp", "Belebter Campingplatz – viele Menschen", true, false, "more_people", 2.0, 18],
		["wild", "Wildtier-Nacht – nur Tiere, öfter", true, false, "animals", 1.6, 10],
		["daily", "Tagesablauf – jeder kommt zu seiner Zeit", true, true, "mixed", 1.0, 12],
		["busy", "Viel los – Belastungstest für MoveEye", true, false, "mixed", 4.0, 30],
		["off", "Kein Besuch von selbst", false, false, "mixed", 1.0, 12]]
const PRESET_HOUR := {"calm": 23.0, "burglary": 1.0, "grill": 20.0, "farm": 10.0, "wildlife": 22.0, "camp": 16.0, "wild": 23.5, "busy": 15.0}   # 3D-3.43
const PEOPLE_KINDS := ["person", "elderly", "child", "jogger", "dogwalk", "bench", "garden_person", "car_park", "car", "cyclist", "stroller", "courier",
		"police", "drunk", "couple", "horse_walk", "tractor", "moto", "van", "burglar", "bbq", "homecoming", "parcel", "kids_tag", "mowing"]


func _mixed(kinds: Array) -> Array:
	"""the visitors of the scene, filtered by the setting «Wer kommt» (more animals / more people / only ...)"""
	var animals := kinds.filter(func(k): return not k in PEOPLE_KINDS)
	var people := kinds.filter(func(k): return k in PEOPLE_KINDS)
	match mix:
		"animals":
			return animals if not animals.is_empty() else kinds
		"people":
			return people if not people.is_empty() else kinds
		"more_animals":
			return kinds + animals + animals
		"more_people":
			return kinds + people + people
	return kinds


func _scare_all(sound: bool) -> void:
	for v in visitors.get_children():
		if v.kind != "person" and v.kind != "car":
			if sound or v.position.distance_to(head.global_position) < 25.0:
				v.scare()


func night_test() -> void:
	set_hour(22.5)
	auto_visitors = false
	weather = "clear"
	var steps := [[5, "fox"], [25, "boar"], [45, "car"], [60, "thief"], [85, "door1"], [95, "door0"], [100, "bike"], [110, "gas1"], [120, "gas0"]]
	var t0 := now()
	for s in steps:
		var wait: float = t0 + float(s[0]) - now()
		if wait > 0:
			await get_tree().create_timer(wait).timeout
		match s[1]:
			"fox", "boar":
				spawn(s[1])
			"car":
				car()
			"thief":
				thief()
			"door1", "door0":
				set_door(s[1] == "door1")
			"bike":
				add_event("Velo", "tag")
			"gas1", "gas0":
				set_gas(s[1] == "gas1")


func set_door(o: bool) -> void:
	door_open = o
	add_event("Wohnwagen-Tür", "door", o)


func set_gas(o: bool) -> void:
	gas_on = o
	add_event("Gas Wohnwagen", "gas", o)


# ---- controls (window and web page) ----------------------------------------------------------------------------------
func add_control(type: String, id: String, label: String, getter, setter, group: String, extra := {}) -> void:
	_mod("einstellungen").add_control(type, id, label, getter, setter, group, extra)


# ---- order of the settings: groups with a symbol, parts inside (from 3D-3.5) ------------------------------------------------
# [group, symbol (window: drawn; page of MoveEye: emoji), parts in their order]
const GROUPS := [["Szene", "globe", "🌍", ["", "Bergtal", "Ort von der Karte", "Foto des Platzes", "Zeit", "Licht & Nacht"]],
		["Wetter", "cloud", "🌦", ["", "Mehr Wetter", "Natur und Wind"]],
		["Besuch", "person", "🚶", ["Vorlagen", "Besucher hinsetzen", "Menschen einzeln", "Gruppen und Alltag", "Mit Hund oder Pferd", "Schwierige Fälle (Tarnung, Diebe)",
				"Wildtiere", "Haus- und Nutztiere", "Vögel und Kleintiere", "Fahrzeuge", "Abläufe", "Von selbst", "Verhalten"]],   # Menüs A: «Menschen / Tiere schicken» geteilt (VISIT_SUB)
		["Kamerabild", "lens", "👁", ["", "Weitwinkel-Kamera", "Wärmebild", "Wie echt", "Schwierige Bedingungen", "Feineinstellungen"]],
		["Mover", "track", "🚜", ["", "Patrouille", "Controller"]],
		["Licht & Ton", "bulb", "💡", ["", "Status-LED & Tasten", "Lautsprecher", "Mikrofon", "Umgebungsgeräusche", "Spiel-Ton"]],      # 3D-4.22: «Lautsprecher» here like MoveEye (was «Sensoren»)
		["Zusatzgeräte", "puzzle", "🔌", ["", "Bewegungsmelder (PIR)", "Strom", "Netz", "Zusatz-Bildschirm (SmallTV)"]],   # P1 ui_gemeinsam: «Sensoren» -> «Zusatzgeräte» (extras), nach Licht & Ton wie MoveEye
		["Spiel", "pad", "🎮", ["", "Entdecken", "Assistent"]],        # Erlebniswelt 20–23: «Entdecken» (entdecken.gd) on the card
		["Wildtier", "target", "🎯", [""]],
		["Testen", "check", "✅", ["", "Verfolgungs-Parcours", "Störungen", "Einbruch-Abläufe"]],
		["System", "gear", "⚙", ["Grafik", "Karte und Livebild", "Start mit dem PC", "Updates", "Sicherung", "Kinder-Modus", "Gerät & Hilfe"]],   # Menüs A: «Ansicht» → «Karte und Livebild» (fehlte hier)
		["Entwickler", "tools", "🧪", ["", "Updates"]]]
# 3D-4.21 (Menü 2, Besitzer 30.10.2026): the same names as MoveEye - the controls keep their old group / part in add_control,
# _order_controls renames them here (MoveEye reads the fixed «gid», not the name)
# P1 ui_gemeinsam (Besitzer 31.10.2026): ids, names, symbols and order of the groups as in res://ui_gemeinsam.json (checked by
# werkzeuge/ui_gemeinsam_test.gd and at start, scripts/ui_gemeinsam.gd); «Sensoren» is «Zusatzgeräte» (extras), the part
# «Kinder-Modus» has its own name again («Sicherheit» is the password / users group of MoveEye)
const GROUP_RENAME := {"Testlauf": "Testen", "Wildbeobachtung": "Wildtier", "Sensoren": "Zusatzgeräte"}
const SUB_RENAME := {"Akku und Strom": "Strom", "Netz-Ausfall testen": "Netz", "Zusatz-Bildschirm": "Zusatz-Bildschirm (SmallTV)"}
# 3D-4.21: what only the developer needs (like the group «Entwickler» of MoveEye) - always «Experte»
# Paket «Entwickler zusammenlegen» (Besitzer 31.10.2026): «dev_open» is the only entry of the card in the panel (opens the window
# «Mehr → Entwickler» on its tab «Schalter»); the others carry «devwin": drawn in that window, not in the panel - same ids,
# same /control set / press, still sent to MoveEye (its Simulator page shows them in «Entwickler»)
const DEV_IDS := ["dev_updates", "dev_open", "pruef_open", "simint_open"]
# id -> [group, part]; not listed: the group given in add_control, no part
const PLACE := {"patrol_on": ["Mover", "Patrouille"], "patrol_mode": ["Mover", "Patrouille"], "patrol_points": ["Mover", "Patrouille"], "patrol_area": ["Mover", "Patrouille"],
		"patrol_random": ["Mover", "Patrouille"], "patrol_clear": ["Mover", "Patrouille"], "patrol_speed": ["Mover", "Patrouille"], "patrol_dwell": ["Mover", "Patrouille"],
		"patrol_sweep": ["Mover", "Patrouille"], "patrol_follow": ["Mover", "Patrouille"], "patrol_judge": ["Mover", "Patrouille"],
"ort_map": ["Szene", "Ort von der Karte"], "ort": ["Szene", "Ort von der Karte"], "speed": ["Szene", "Zeit"], "moon": ["Szene", "Licht & Nacht"], "moon_auto": ["Szene", "Licht & Nacht"], "season": ["Szene", "Zeit"],
		"cam1_yaw": ["Kamerabild", "Weitwinkel-Kamera"], "humidity": ["Wetter", "Mehr Wetter"], "pressure": ["Wetter", "Mehr Wetter"],
		"storm": ["Wetter", "Mehr Wetter"], "thunder": ["Wetter", "Mehr Wetter"], "cloud_shadows": ["Wetter", "Mehr Wetter"], "gusts": ["Wetter", "Natur und Wind"],
		"world_cloth": ["Wetter", "Natur und Wind"], "world_smoke": ["Wetter", "Natur und Wind"], "world_fireflies": ["Wetter", "Natur und Wind"],
		"meadow": ["Wetter", "Natur und Wind"], "car": ["Besuch", "Fahrzeuge"], "thief": ["Besuch", "Abläufe"], "burglar": ["Besuch", "Abläufe"], "sneaker": ["Besuch", "Abläufe"], "bbq": ["Besuch", "Abläufe"], "homecoming": ["Besuch", "Abläufe"], "parcel": ["Besuch", "Abläufe"], "fox_trash": ["Besuch", "Abläufe"], "boar_group": ["Besuch", "Abläufe"], "kids_tag": ["Besuch", "Abläufe"], "mowing": ["Besuch", "Abläufe"], "night_lapse": ["Besuch", "Von selbst"], "calendar": ["Besuch", "Von selbst"],
		"dogwalk": ["Besuch", "Menschen schicken"], "herd": ["Besuch", "Tiere schicken"], "clear": ["Besuch", "Vorlagen"], "visit_preset": ["Besuch", "Vorlagen"],
		"car_park": ["Besuch", "Fahrzeuge"], "bench": ["Besuch", "Menschen schicken"], "feed": ["Besuch", "Tiere schicken"],
		"garden_person": ["Besuch", "Menschen schicken"], "couple": ["Besuch", "Menschen schicken"], "horse_walk": ["Besuch", "Menschen schicken"],
		"courier_go": ["Besuch", "Menschen schicken"], "police_go": ["Besuch", "Menschen schicken"], "drunk_go": ["Besuch", "Menschen schicken"],
		"cows": ["Besuch", "Tiere schicken"], "sheep_flock": ["Besuch", "Tiere schicken"], "bats": ["Besuch", "Tiere schicken"], "owl": ["Besuch", "Tiere schicken"],
		"tractor": ["Besuch", "Fahrzeuge"], "moto": ["Besuch", "Fahrzeuge"], "van": ["Besuch", "Fahrzeuge"], "auto": ["Besuch", "Von selbst"], "mix": ["Besuch", "Von selbst"],
		"visit_rate": ["Besuch", "Von selbst"], "daily_life": ["Besuch", "Von selbst"], "real_time": ["Szene", "Zeit"], "max_visitors": ["Besuch", "Von selbst"], "visitor_speed": ["Besuch", "Verhalten"],
		"lamp_share": ["Besuch", "Verhalten"], "look_at_light": ["Besuch", "Verhalten"], "flee_light": ["Besuch", "Verhalten"],
		"flee_sound": ["Besuch", "Verhalten"], "avoid_on": ["Besuch", "Verhalten"], "privat_on": ["Besuch", "Verhalten"], "lens_vignette": ["Kamerabild", "Feineinstellungen"],
		"sound_on": ["Licht & Ton", "Mikrofon"], "game_open": ["Spiel", "Runde"], "game_start": ["Spiel", ""],
		"game_stop": ["Spiel", ""], "game_wizard": ["Spiel", ""], "tv_mode": ["Spiel", "Anzeige"], "game_minutes": ["Spiel", "Runde"], "game_mode": ["Spiel", "Runde"], "game_goal": ["Spiel", "Runde"],
		"game_level": ["Spiel", "Regeln"], "game_glevel": ["Spiel", "Regeln"], "game_real": ["Spiel", "Regeln"], "game_lives": ["Spiel", "Regeln"], "game_items": ["Spiel", "Regeln"], "game_teams": ["Spiel", "Regeln"],
		"game_rescue": ["Spiel", "Regeln"], "game_teamgoal": ["Spiel", "Regeln"], "game_stones": ["Spiel", "Regeln"], "game_powers": ["Spiel", "Regeln"], "game_spectate": ["Spiel", "Anzeige"], "game_photos": ["Spiel", "Extras"], "game_fx_laser": ["Spiel", "Treffer"], "game_fx_paint": ["Spiel", "Treffer"], "game_fx_flash": ["Spiel", "Treffer"], "game_tap": ["Spiel", "Treffer"],
		"game_learn_miss": ["Spiel", "Erkennung lernen"], "game_learn_report": ["Spiel", "Erkennung lernen"], "game_learn_paths": ["Spiel", "Erkennung lernen"], "game_blind_bonus": ["Spiel", "Erkennung lernen"], "game_report_send": ["Spiel", "Erkennung lernen"], "game_hides": ["Spiel", "Extras"], "game_decoy": ["Spiel", "Extras"],
		"game_night": ["Spiel", "Extras"], "game_events": ["Spiel", "Extras"], "game_checkpoints": ["Spiel", "Extras"], "game_tasks": ["Spiel", "Extras"], "game_autohandicap": ["Spiel", "Extras"],
		"game_board_reset": ["Spiel", "Extras"], "spectate_now": ["Spiel", "Anzeige"], "game_noise": ["Spiel", "Regeln"],
		"game_random": ["Spiel", "Regeln"], "game_guard": ["Spiel", "Regeln"], "game_cones": ["Spiel", "Anzeige"], "game_quality": ["Spiel", "Anzeige"], "game_max": ["Spiel", "Runde"],
		"grafik_mode": ["System", "Grafik"], "quality": ["System", "Grafik"], "grafik_dof": ["System", "Grafik"], "cam_wippen": ["System", "Grafik"], "foto_tex": ["System", "Grafik"], "view_scale": ["System", "Grafik"], "win_fps": ["System", "Grafik"], "auto_perf": ["System", "Grafik"], "map_on": ["System", "Karte und Livebild"], "live_on": ["System", "Karte und Livebild"], "live_cam": ["System", "Karte und Livebild"], "live_size": ["System", "Karte und Livebild"], "phone_sim": ["System", "Karte und Livebild"],"eco_idle": ["System", "Grafik"], "autostart": ["System", "Start mit dem PC"],
		"autostart_min": ["System", "Start mit dem PC"], "autostart_mwpc": ["System", "Start mit dem PC"], "autostart_lock": ["System", "Start mit dem PC"],
		"cond_glare": ["Kamerabild", "Schwierige Bedingungen"], "cond_drops": ["Kamerabild", "Schwierige Bedingungen"],
		"cond_web": ["Kamerabild", "Schwierige Bedingungen"], "cond_headlights": ["Kamerabild", "Schwierige Bedingungen"],
		"cond_shadows": ["Kamerabild", "Schwierige Bedingungen"], "cond_ir": ["Kamerabild", "Schwierige Bedingungen"],
		"linse_tropfen": ["Kamerabild", ""], "scheinwerfer": ["Kamerabild", "Schwierige Bedingungen"], "fz_glare": ["Kamerabild", "Schwierige Bedingungen"],
		"jahreszeit": ["Szene", "Zeit"], "tagesablauf": ["Besuch", "Von selbst"],
		"autologon": ["System", "Start mit dem PC"], "kids_scary": ["System", "Kinder-Modus"], "kids_thief": ["System", "Kinder-Modus"], "kids_laser": ["System", "Kinder-Modus"], "kids_sound": ["System", "Kinder-Modus"], "kids_ask": ["System", "Kinder-Modus"], "auto_update": ["System", "Updates"], "update_mode": ["System", "Updates"], "dev_updates": ["Entwickler", "Updates"], "news_popup": ["System", "Updates"], "news_show": ["System", "Updates"], "update_now": ["System", "Updates"]}


const SIMPLE_GROUPS := ["Szene", "Wetter", "Besuch", "Testen", "Spiel"]
# 3D-4.7 («Spiel-Karte schlank», Besitzer): the card «Spiel» = Assistent öffnen, Start, Stopp and the state line; every other
# setting of the game is only in the assistant (gamewiz.gd). Those controls stay (control API, saved settings) but get
# extra «wiz»: not in this panel and not in the Simulator control of MoveEye.
const GAME_MAIN := ["game_wizard", "game_start", "game_stop"]
# Erlebniswelt 20–23 (entdecken.gd): the part «Entdecken» stays on the card «Spiel» (not in the assistant); the first three in «Einfach»
const DISC_IDS := ["disc_book", "disc_photo", "disc_hints", "disc_hint_min", "disc_demo", "disc_seek", "fp_task_kind", "fp_task_velo", "fp_task_zelt"]
const DISC_SIMPLE := ["disc_book", "disc_photo", "disc_hints"]
# 3D-4.7: a fixed id per group for MoveEye (the visible names may change); sent as «gid» with every control
const GROUP_IDS := {"Szene": "scene", "Wetter": "weather", "Besuch": "visit", "Kamerabild": "camera", "Zusatzgeräte": "extras", "Mover": "mover", "Licht & Ton": "lightsound",
		"Spiel": "game", "Wildtier": "wildlife", "Testen": "testrun", "System": "sys", "Entwickler": "dev"}   # P1: «system» / «sensors» before (alias in ui_gemeinsam.json)
# Paket «Menüs aufräumen A» (Besitzer 31.10.2026): «Einfach» wirklich einfach - rund 60 statt 100 Einträge, eine feste Liste statt
# «ganze Gruppe»: Szene, Zeit, Wetter, Besuch (Vorlagen, die wichtigsten Abläufe, von selbst), Testlauf, Aufnahme, Parcours und
# Einbruch starten, je ein Hauptschalter von Kamerabild / Sensoren / Mover / Licht & Ton / Wildtier, System. Alles andere (Störungen,
# I2C, Pi-5-Werte, Seed, Fein-Regler) ist «Experte». Die Bergtal-, Welt- und Ferienpark-Regler zeigen sich nur in ihrer Szene.
const SIMPLE_IDS := ["scene", "home_edit", "hour", "fp_spot", "bt_spot", "bt_bed", "bt_mount", "bt_wall", "bt_here", "bt_goto", "bt_season",
		"ort_map", "ort", "twin_on", "twin_open", "twin_yaw", "twin_span", "jahreszeit", "real_time", "licht_lp", "licht_platz",
		"weather", "wind", "ambient", "real_weather", "night_weather", "w_rain",
		"visit_preset", "clear", "thief", "burglar", "sneaker", "homecoming", "parcel", "auto", "mix", "visit_rate", "tagesablauf", "night_lapse", "st_frei",
		"show_laser", "door", "mast_h", "statusled_panel", "rifle",
		"testrun_plan", "testrun_start", "testrun_stop", "testrun_open", "rec_start", "rec_stop", "rec_pick", "rec_play", "rec_stopplay",
		"parcours_pick", "parcours_start", "parcours_stop", "einbruch_ablauf", "einbruch_start", "einbruch_stop",
		"update_mode", "kids_ask", "grafik_mode"]
# Menüs A, Punkt 1 + 2: «Menschen schicken» (23) und «Tiere schicken» (46, davon 13 Menschen) in Unterkarten mit höchstens 14 Knöpfen.
# id -> Unterkarte; neue «spawn_*» ohne Eintrag: Mensch (PEOPLE_KINDS) -> «Menschen einzeln», sonst «Wildtiere»
const VISIT_SUB := {
		"spawn_person": "Menschen einzeln", "spawn_child": "Menschen einzeln", "spawn_jogger": "Menschen einzeln", "spawn_cyclist": "Menschen einzeln",
		"spawn_stroller": "Menschen einzeln", "spawn_courier": "Menschen einzeln", "spawn_police": "Menschen einzeln", "spawn_drunk": "Menschen einzeln",
		"spawn_elderly": "Menschen einzeln", "spawn_hooded": "Menschen einzeln", "spawn_backpacker": "Menschen einzeln", "spawn_phoner": "Menschen einzeln",
		"couple": "Gruppen und Alltag", "spawn_group2": "Gruppen und Alltag", "spawn_group3": "Gruppen und Alltag", "spawn_group4": "Gruppen und Alltag",
		"m_send_familie": "Gruppen und Alltag", "m_send_gespraech": "Gruppen und Alltag", "m_send_sitzen": "Gruppen und Alltag", "m_send_wc": "Gruppen und Alltag",
		"m_send_spazieren": "Gruppen und Alltag", "m_send_eilig": "Gruppen und Alltag", "m_send_velo": "Gruppen und Alltag", "bench": "Gruppen und Alltag",
		"garden_person": "Gruppen und Alltag", "m_send_gangarten": "Gruppen und Alltag",
		"dogwalk": "Mit Hund oder Pferd", "horse_walk": "Mit Hund oder Pferd", "tiere_dog_free": "Mit Hund oder Pferd", "spawn_dog_leash": "Mit Hund oder Pferd",
		"spawn_edge_sneak": "Schwierige Fälle (Tarnung, Diebe)", "spawn_platz_besuch": "Schwierige Fälle (Tarnung, Diebe)", "spawn_tarn_robben": "Schwierige Fälle (Tarnung, Diebe)",
		"spawn_tarn_schirm": "Schwierige Fälle (Tarnung, Diebe)", "spawn_tarn_karton": "Schwierige Fälle (Tarnung, Diebe)", "spawn_velodieb": "Schwierige Fälle (Tarnung, Diebe)",
		"spawn_fox": "Wildtiere", "spawn_deer": "Wildtiere", "spawn_boar": "Wildtiere", "spawn_badger": "Wildtiere", "spawn_wolf": "Wildtiere", "spawn_marten": "Wildtiere",
		"spawn_chamois": "Wildtiere", "spawn_ibex": "Wildtiere", "spawn_lynx": "Wildtiere", "herd": "Wildtiere", "feed": "Wildtiere", "spawn_deer_bedded": "Wildtiere",
		"spawn_boar_herd": "Wildtiere", "lure_now": "Wildtiere",
		"spawn_cat": "Haus- und Nutztiere", "spawn_dog": "Haus- und Nutztiere", "spawn_cow": "Haus- und Nutztiere", "spawn_sheep": "Haus- und Nutztiere",
		"spawn_horse": "Haus- und Nutztiere", "cows": "Haus- und Nutztiere", "sheep_flock": "Haus- und Nutztiere", "spawn_cat_roof": "Haus- und Nutztiere",
		"u_send_cat_fence": "Haus- und Nutztiere", "u_send_chickens": "Haus- und Nutztiere", "zt_pets": "Haus- und Nutztiere",
		"spawn_hare": "Vögel und Kleintiere", "spawn_hedgehog": "Vögel und Kleintiere", "spawn_squirrel": "Vögel und Kleintiere", "bats": "Vögel und Kleintiere",
		"owl": "Vögel und Kleintiere", "tiere_crows": "Vögel und Kleintiere", "tiere_magpies": "Vögel und Kleintiere", "tiere_gulls": "Vögel und Kleintiere",
		"u_send_hedgehog_bowl": "Vögel und Kleintiere", "zt_spider": "Vögel und Kleintiere", "zt_spider_lens": "Vögel und Kleintiere"}
# Menüs A, Punkt 4 + 5: eine Sache an einem Ort - die alten ids bleiben als Alias (extra «alias» + «wiz»: nicht im Bedienfeld, nicht
# auf der Simulator-Seite von MoveEye), /control set / press, Tests, Prüfstand und gespeicherte Einstellungen gehen weiter
const ALIAS_IDS := {"lens_drops": "linse_tropfen", "w_lens": "linse_tropfen", "cond_drops": "linse_tropfen",
		"cond_headlights": "scheinwerfer", "fa_sweep": "scheinwerfer", "season": "jahreszeit", "jz_mode": "jahreszeit", "seasons_on": "jahreszeit",
		"daily_life": "tagesablauf", "m_plan": "tagesablauf", "pruef_open": "Testen → Prüfstand"}
# Menüs A, Punkt 8: die Foto-Regler wirken nur mit einem geladenen Foto des Platzes - ohne Foto ausgegraut («ro»)
const PHOTO_IDS := ["twin_yaw", "twin_span", "twin_dist", "twin_horizon", "fm_on", "fm_h", "fm_hz", "fm_roll", "fm_shk", "fm_bright", "fm_wb",
		"fm_noise", "fm_front", "fm_measure"]


func _simple_ok(c: Dictionary) -> bool:
	return _mod("einstellungen")._simple_ok(c)


func _order_controls() -> void:
	_mod("einstellungen")._order_controls()


func _register_controls() -> void:
	_mod("einstellungen")._register_controls()


func _cget(id: String):
	return _mod("einstellungen")._cget(id)


func _cset(id: String, v) -> void:
	_mod("einstellungen")._cset(id, v)


func _menu_merge() -> void:
	_mod("einstellungen")._menu_merge()


const VISITOR_KINDS_ALL := ["person", "child", "jogger", "fox", "deer", "boar", "cat", "dog", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel",
		"cyclist", "stroller", "courier", "police", "drunk", "cow", "sheep", "horse", "chamois", "ibex", "lynx"]
const VISITOR_LIST := [["person", "Person"], ["child", "Kind"], ["jogger", "Jogger"], ["fox", "Fuchs"], ["deer", "Reh"], ["boar", "Wildschwein"],
		["cat", "Katze"], ["dog", "Hund"], ["badger", "Dachs"], ["hare", "Hase"], ["hedgehog", "Igel"], ["wolf", "Wolf"], ["marten", "Marder"],
		["squirrel", "Eichhörnchen"], ["cyclist", "Velofahrer"], ["stroller", "Kinderwagen"], ["courier", "Pizzakurier"], ["police", "Polizei-Rundgang"],
		["drunk", "Betrunkener"], ["elderly", "Älterer Mensch mit Stock"], ["cow", "Kuh"], ["sheep", "Schaf"], ["horse", "Pferd"], ["chamois", "Gämse"], ["ibex", "Steinbock"], ["lynx", "Luchs"]]
var meadow_on := true


var _perf_orig := {}                     # 3D-3.88: the own graphics choice before «automatisch leichter»
var _perf_auto := false


func set_meadow(on: bool) -> void:
	if not _perf_auto:
		_perf_orig.erase("meadow_on")                  # chosen by hand: saved again
	meadow_on = on
	for n in get_tree().get_nodes_in_group("meadow"):
		n.visible = on


func clear_visitors() -> void:
	for v in visitors.get_children():
		v.queue_free()


func _set_speed(v: float) -> void:
	set_hour(hour())
	speed = v


func set_view_scale(v: float) -> void:
	_mod("start").set_view_scale(v)


func _perf_tick() -> void:
	_mod("start")._perf_tick()


func _set_quality(v: String) -> void:
	_mod("start")._set_quality(v)


func auto_quality() -> String:
	return _mod("start").auto_quality()


func _apply_quality() -> void:
	_mod("start")._apply_quality()


# ---- 3D-4.25 «Lite» (Wunsch des Besitzers 31.10.2026): the same simulator, lighter for the Raspberry Pi 5 ---------------------------
# «Grafik-Modus» Automatisch (Lite on a Pi / ARM computer or when the first seconds are very slow) / Lite / Normal. Lite: graphics
# level «einfach» (no shadows, no glow, no SSAO / SSR / fog volumes), the big view 60 % sharp, at most 25 pictures per second,
# rain / snow / smoke / fire with about a third of the particles, a third of the grass, small things far away not drawn, at
# most 6 visitors at once, a smaller picture of the window for MoveEye. The camera pictures for MoveEye keep their size.
# The own choices (Grafik, Schärfe, Bilder/s, Besucher) stay saved (_perf_orig) and come back with «Normal».
const LITE_KEYS := ["quality", "view_scale", "win_fps", "max_visitors"]


func set_grafik_mode(v: String) -> void:
	_mod("start").set_grafik_mode(v)


func set_foto_tex(v: bool) -> void:
	"""3.30 Schalter «Foto-Texturen im Bergtal» (bergtal_texturen.gd): das Bergtal neu aufbauen, wenn es gerade geladen ist"""
	if v == foto_tex:
		return
	foto_tex = v
	_settings_dirty = true
	if scene == "bergtal":
		set_scene("bergtal")


func lite_update() -> void:
	_mod("start").lite_update()


func _lite_apply(on: bool) -> void:
	_mod("start")._lite_apply(on)


func _lite_scene(on: bool) -> void:
	_mod("start")._lite_scene(on)


func _lite_tick() -> void:
	_mod("start")._lite_tick()


func perf_info() -> Dictionary:
	return _mod("start").perf_info()


func _game_card_start() -> void:
	"""3D-4.7: the button «Start» of the card «Spiel»: the game closed = open it (QR code for the phones), otherwise start the round"""
	if not game.open:
		game.set_open(true)
		start_info = "Spiel offen – Handys scannen den QR-Code, dann nochmals «Start»"
		return
	if game.count() == 0:
		start_info = "Noch niemand dabei – Handys scannen zuerst den QR-Code"
		return
	game.start_round()


func _game_card_stop() -> void:
	"""3D-4.7: «Stopp»: a running round ends; without a round the game is closed"""
	if game.round_state in ["countdown", "play"]:
		game.end_round()
	elif game.open:
		game.set_open(false)


func control_info() -> Dictionary:
	return _mod("status").control_info()


func control(d: Dictionary) -> Dictionary:
	_ctl_frame = Engine.get_process_frames()
	var r := _control(d)
	_ctl_frame = -1
	return r


func _control(d: Dictionary) -> Dictionary:
	# All actions are in main_steuerung.gd (Vorschlag 24). The actions MoveEye sends (schnittstelle.json) stay listed here,
	# because part 558 of MoveEye and schnittstelle.gd read them from main.gd «func _control»:
	#   a in ["set", "scenario", "busy", "tv", "fehler", "game_info", "gamewiz", "game_compare", "game_handicap",
	#     "game_shut", "game_mwcatch", "shoot", "replay", "planner", "blindmap", "dataset", "farecreate", "whatif",
	#     "input", "pad", "padview", "press", "rover", "view_look", "netmap", "nacht", "parcours", "sabotage",
	#     "templates", "twin", "visits", "weit", "entdecken", "werkstatt", "trailer", "vorfuehrung", "spielbereich",
	#     "egg", "sicherung", "mehr", "localplay"]
	return _mod("steuerung")._control(d)


func status_text() -> String:
	return _mod("status").status_text()


func scenarios() -> Array:
	var out := []
	for s in Worlds.SHOWN:                        # 3D-4.x Welten: the worlds and tools (old ids still work for «scenario»)
		out.append({"id": s, "name": Scenes.name_of(s) + " (3D)", "kind": "world", "deletable": false, "en": Scenes.EN.get(s, "")})
	return out


# ---- the window on the PC ------------------------------------------------------------------------------------------------
var ui_root: Control
var tv                                # tv.gd: TV mode for the games evening (3D-3.44)
var cam_card: Control                 # 3D-3.43: the card with the camera pictures - floats where it was when the panel is hidden
var cam_float: VBoxContainer
var cam_fx := -1.0                    # where it was put (-1 = where it stood in the panel)
var cam_fy := -1.0
var _cam_drag := Vector2(-1, -1)
var ui_box: VBoxContainer             # the content of the panel (must never be wider than the panel)
var prev0: TextureRect
var prev1: TextureRect
var prevt: TextureRect
var info_label: Label
var real_label: Label


func _build_ui() -> void:
	await _mod("menues")._build_ui()


# ---- toolbar, search, Simple / Expert --------------------------------------------------------------------------------
var show_btn: Button
var search_in: LineEdit
var search_none: Label
var simple_note: Label
var ui_simple := true                 # «Einfach»: only the important settings (saved)
var kids_on := false                  # 3D-3.69: «Kinder»: a panel with big picture buttons instead of the settings (saved)
var kids_ask := true                   # 3D-3.95: the sum before leaving the «Kinder» mode (can be switched off)
var kids_thief := true                # what children may see (set by the adults; everything allowed at first)
var kids_scary := true
var kids_laser := true
var kids_sound := true
var kids_stars := 0                   # 3D-3.74: stars of the missions
var kids: Control
var kids_seg: Control
var _mode_row: HBoxContainer
var simple_seg: Control
var kopf = null                        # kopf.gd: the one header (MoveEye 639t), buttons in the order of ui_gemeinsam.json
var devzugang = null                   # devzugang.gd: long press on the logo / tool button = developer window (MoveEye 639s)
var leiste: Node                       # real-layout-leiste: the bar (bedienleiste.gd), the same as on every page of MoveEye
var ui_icons := "color"                # «Symbole farbig | schlicht» ("color" | "plain", saved); 3.23: «farbig» is the standard (like MoveEye)
var ui_icons_pick := false             # 3.23: true once somebody chose with the switch (then the saved choice counts)
var ui_tb: Control
var fold_bodies: Array = []           # every card that opens / closes
var setting_bodies: Array = []        # the cards of the settings groups
var top_cards: Array = []             # connection, cameras, visitors, tools (hidden while searching)
var quick                             # 3D-3.86: quick.gd
var expert_cards: Array = []
var ui_items: Array = []              # [widget, label, expert, card body, part body] of every setting
var sub_bodies: Array = []            # the parts inside the cards (3D-3.5)
var fine_bodies: Array = []           # 3D-4.21: «Feineinstellungen» of a part / card (closed in «Einfach», open in «Experte»)
var dev_body: VBoxContainer = null   # 3D-4.22: the card «Entwickler» (shown with MoveEye's «Entwickler-Bereich», dev_area)
var dev_area := false                 # 3D-4.22: the developer switch of MoveEye (last known, saved)


func _dev_hidden(it: Array) -> bool:
	"""3D-4.22: a setting of the card «Entwickler» while MoveEye's «Entwickler-Bereich» is off;
	3D-4.28: or a setting with «only» (add_control … controls[-1]["only"]) that does not fit now (e.g. not in its scene)"""
	if dev_body != null and it[3] == dev_body and not _dev_card_ok():
		return true
	for c in controls:
		if c.has("only") and c.label == it[1]:
			return not bool(c["only"].call())
	return false


func _dev_card_ok() -> bool:
	"""the card «Entwickler» of the panel: MoveEye's «Entwickler-Bereich» is on and it is the owner (devtool.is_owner: not in
	the children's mode) - like the row «Entwickler» of «Mehr» (Paket «Entwickler zusammenlegen»)"""
	return dev_area and preload("res://scripts/devtool.gd").is_owner(self)


func dev_window(tab := "schalter") -> Dictionary:
	"""Paket «Entwickler zusammenlegen»: the one «Entwickler» - the window «Mehr → Entwickler» (devtool.gd), on a tab
	(schalter | notizen | kontakt | kapitel | spieltest); only the owner (devtool.open says so otherwise)"""
	if mehr == null or mehr.dev == null:
		return {"ok": false, "error": "not ready"}
	return mehr.dev.control({"do": "tab", "value": tab})


func _only_refresh() -> void:
	"""3D-4.28: after a change of the scene the settings with «only» appear / go (search field: its filter stays)"""
	if ui_items.is_empty():
		return
	if search_in != null and search_in.text.strip_edges() != "":
		_search(search_in.text)
	else:
		_apply_simple()


func _diag_pack() -> void:
	"""3D-4.22: «Diagnose-Paket» of the group «Entwickler»: MoveEye builds it (its page /tools/diag.zip opens in the browser)"""
	if mw_addr == "" or now() - mw_t > 10.0:
		status_label.text = "Diagnose-Paket: MoveEye ist nicht verbunden – das Paket macht MoveEye (Werkzeuge → Diagnose-Paket). Zuerst in MoveEye die Simulation einschalten."
		start_info = status_label.text
		return
	OS.shell_open("%s://%s:%d/tools/diag.zip" % [str(mw.get("mw_scheme", "http")), mw_addr, int(mw.get("mw_port", 5000))])
	start_info = "Diagnose-Paket: MoveEye packt es – der Browser lädt das ZIP herunter."


func show_panel(on: bool) -> void:
	if on == ui_root.visible:
		show_btn.visible = not on
		return
	if not on and cam_card != null and cam_card.is_visible_in_tree():
		# 3D-3.43: the camera pictures stay where they were and can be moved freely
		var gp := cam_card.global_position
		var w := cam_card.size.x
		var home := cam_card.get_parent()
		cam_card.set_meta("home", home)
		cam_card.set_meta("home_i", cam_card.get_index())
		home.remove_child(cam_card)
		cam_card.custom_minimum_size.x = w
		cam_float.add_child(cam_card)
		cam_float.visible = true
		if fenster != null:                                # Paket «Fenster»: where the card was (until moved by hand)
			fenster.home_at(cam_float, gp - Vector2(6, 26))
		else:
			cam_float.size = Vector2.ZERO
			cam_float.position = Vector2(cam_fx, cam_fy) if cam_fx >= 0.0 else gp - Vector2(0, 26)
			_cam_clamp()
	elif on and cam_card != null and cam_card.get_parent() == cam_float:
		var home: Control = cam_card.get_meta("home")
		cam_float.remove_child(cam_card)
		cam_card.custom_minimum_size.x = 0
		home.add_child(cam_card)
		home.move_child(cam_card, int(cam_card.get_meta("home_i")))
		cam_float.visible = false
	ui_root.visible = on
	show_btn.visible = not on


func _cam_clamp() -> void:
	var vr := get_viewport().get_visible_rect().size
	cam_float.position = Vector2(clampf(cam_float.position.x, 0.0, maxf(0.0, vr.x - cam_float.size.x)),
			clampf(cam_float.position.y, 0.0, maxf(0.0, vr.y - 40.0)))


func _cam_float_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_cam_drag = get_viewport().get_mouse_position() - cam_float.position if ev.pressed else Vector2(-1, -1)
		if not ev.pressed:
			cam_fx = cam_float.position.x
			cam_fy = cam_float.position.y
			_settings_dirty = true
	elif ev is InputEventMouseMotion and _cam_drag.x >= 0.0:
		if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):
			_cam_drag = Vector2(-1, -1)
			return
		cam_float.position = get_viewport().get_mouse_position() - _cam_drag
		_cam_clamp()


var _fold_btns := {}
var _fold_lit := "-"
var _fold_t := 0.0


func _fold_state() -> String:
	return _mod("menues")._fold_state()


func _fold_paint() -> void:
	_mod("menues")._fold_paint()


func _fold_group_open(b: Control) -> bool:
	return _mod("menues")._fold_group_open(b)


func _fold_all(how: String, _own := false) -> void:
	_mod("menues")._fold_all(how, _own)


# ---- Paket nurgruppen (Besitzer, 31.10.2026): «Beim Start: Nur Gruppen» ------------------------------------------------------
# Every start shows the settings as «Nur Gruppen» (_fold_all("groups"), not saved). What the user opens / closes himself is kept in
# fold_mem (simulator_settings.json; before, the cards always started as built). Switch off: everything as the user left it.
var start_groups := true              # the switch, factory: on (saved); 639r: taken over once into «Meine Ansicht» (mine_mig)
var mine_on := true                   # 639r «Meine Ansicht» (Besitzer 1.11.2026): on = every fold by the user is kept in fold_mem
var mine_mig := false                 # 639r: «Beim Start: Nur Gruppen» taken over once (the first Meine Ansicht = «Nur Gruppen»), saved
var fold_mem := {}                    # the own state: {"c:Karte": true, "s:Karte/Teil": false} (saved)
var _fold_init := {}                  # how the panel was built (for cards the user never touched)
var _sg_cb: CheckButton


func _fold_key(b: Control) -> String:
	return _mod("menues")._fold_key(b)


func _fold_is_open(b: Control) -> bool:
	return _mod("menues")._fold_is_open(b)


func _fold_put(b: Control, open: bool) -> void:
	_mod("menues")._fold_put(b, open)


func _fold_keep(b: Control) -> void:
	_mod("menues")._fold_keep(b)


func _mine_change(key: String, open: bool) -> void:
	_mod("menues")._mine_change(key, open)


func set_mine() -> void:
	_mod("menues").set_mine()


func _fold_setup() -> void:
	_mod("menues")._fold_setup()


func _fold_own() -> void:
	_mod("menues")._fold_own()


func set_start_groups(_on: bool) -> void:
	_mod("menues").set_start_groups(_on)


func _search(q: String) -> void:
	_mod("menues")._search(q)


func _kids_switch(adult: bool) -> void:
	_mod("menues")._kids_switch(adult)


func _apply_kids() -> void:
	_mod("menues")._apply_kids()


var _adult_box: Control = null


func ask_adult(done: Callable) -> void:
	await _mod("menues").ask_adult(done)


func motion_reduced() -> bool:
	"""3.23 «Bewegung reduzieren»: an / aus, or «auto» = what the operating system says (Windows: MinAnimate, Linux / GNOME:
	enable-animations; asked once, not headless). Unknown = full motion."""
	if reduce_motion == "an":
		return true
	if reduce_motion == "aus":
		return false
	if _os_motion < 0:
		_os_motion = 0
		if DisplayServer.get_name() != "headless":
			var out := []
			if OS.get_name() == "Windows":
				if OS.execute("reg", ["query", "HKCU\\Control Panel\\Desktop\\WindowMetrics", "/v", "MinAnimate"], out) == 0 and not out.is_empty():
					var tx := str(out[0]).strip_edges()
					_os_motion = 1 if tx.ends_with(" 0") or tx.ends_with("\t0") else 0
			elif OS.get_name() == "Linux" and OS.execute("gsettings", ["get", "org.gnome.desktop.interface", "enable-animations"], out) == 0 and not out.is_empty():
				_os_motion = 1 if str(out[0]).strip_edges() == "false" else 0
	return _os_motion == 1


func set_icons(v: String) -> void:
	"""real-layout-leiste: symbols «color» (own colour, a green dot while on) or «plain» (grey, green while on) - the one switch"""
	ui_icons = "plain" if v == "plain" else "color"
	ui_icons_pick = true
	UI.icons_plain = ui_icons == "plain"
	_settings_dirty = true
	for b in fold_bodies:
		if is_instance_valid(b) and b.has_meta("icon"):
			(b.get_meta("icon") as Control).queue_redraw()
	if leiste != null:
		leiste.paint(ui_simple, ui_icons, start_groups)


func set_simple(on: bool) -> void:
	ui_simple = on
	_settings_dirty = true
	_apply_simple()


func _apply_simple() -> void:
	_mod("menues")._apply_simple()


# ---- the pictures of the visitors: click to choose, drag into the world ------------------------------------------------
var thumbs := {}                      # kind -> ImageTexture
var thumb_rects := {}
var palette_items := {}
var thumb_btns: Array = []            # [button, visitor kind]: the picture comes when it is drawn
var drag_kind := ""


func _palette_item(kind: String, name_: String) -> Control:
	return _mod("menues")._palette_item(kind, name_)


func _paint_palette() -> void:
	_mod("menues")._paint_palette()


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE:          # the parts main_*.gd (Object): go with main.gd, also their waiting functions (await)
		for m in _mods.values():
			m.free()
		_mods.clear()
		return
	if what == NOTIFICATION_DRAG_END and drag_kind != "":
		var k := drag_kind
		drag_kind = ""
		var mp := get_viewport().get_mouse_position()
		var over_ui: bool = (ui_root != null and ui_root.visible and ui_root.get_global_rect().has_point(mp)) or (phone != null and phone.visible and phone.get_global_rect().has_point(mp))
		if not over_ui:
			_place_at(k, mp)


func _make_thumbs() -> void:
	await _mod("menues")._make_thumbs()


const THUMB_SPEED := {"cyclist": 3.0, "stroller": 1.1, "courier": 1.6, "police": 1.2, "drunk": 0.8, "cow": 0.8, "sheep": 0.9, "horse": 1.3,
		"chamois": 1.2, "ibex": 1.0, "lynx": 1.1, "person": 1.35, "child": 1.1, "jogger": 2.9, "deer": 1.2, "boar": 1.1, "fox": 1.3, "dog": 1.4, "cat": 0.8, "badger": 0.7, "hare": 1.0, "wolf": 1.2, "marten": 1.0, "squirrel": 0.9, "hedgehog": 0.35}
var thumb_vps := {}                    # kind -> [SubViewport, actor walking on the spot]
var _thumb_t := 0.0


var _thumb_drawn := {}


func _thumbs_tick(dt: float) -> void:
	_thumb_t += dt
	if _thumb_t < 0.08 or not win_open:
		return
	var step := _thumb_t
	_thumb_t = 0.0
	var t_ := Time.get_ticks_msec() / 1000.0
	var mp := get_viewport().get_mouse_position()
	for kd in thumb_vps:
		var r = thumb_rects.get(kd)
		if r == null or not is_instance_valid(r) or not r.is_visible_in_tree():
			continue
		# 3D-3.90: only what is really in view (not scrolled away) and only the picture under the mouse moves -
		# the others are drawn once (before: up to 300 small pictures per second on an older PC)
		var rr: Rect2 = r.get_global_rect()
		var sc_ = r.get_parent()
		while sc_ != null and not (sc_ is ScrollContainer):
			sc_ = sc_.get_parent()
		if sc_ != null and not (sc_ as Control).get_global_rect().intersects(rr):
			continue
		if not rr.has_point(mp) and _thumb_drawn.has(kd):
			continue
		_thumb_drawn[kd] = true
		var vp: SubViewport = thumb_vps[kd][0]
		var a = thumb_vps[kd][1]
		a._animate(step, a.speed, t_)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE


func _on_mwpc() -> void:
	"""MoveEye on this PC changed: button, text, and the phone shows its page as soon as it runs"""
	var st: String = mwpc.state
	mwpc_btn.text = "MoveEye auf diesem PC stoppen" if st == "running" else ("MoveEye auf diesem PC wird vorbereitet …" if st == "busy" else "MoveEye auf diesem PC starten (ohne Pi)")
	mwpc_btn.disabled = st == "busy"
	mwpc_label.text = (mwpc.text + ("\n" + mwpc.helper_text() if mwpc.helper_text() != "" else "")) if st != "off" else "Für das Handy ohne Pi – und als KI-Rechenhilfe: Der Pi lässt dann die Erkennung von diesem PC rechnen (schneller, der Pi bleibt kühl). Beim ersten Mal werden Python, MoveEye und das KI-Modell geladen (rund 170 MB, einige Minuten). Windows fragt dabei, ob Python ins Netz darf: «Zulassen» wählen."
	mwpc_label.add_theme_color_override("font_color", UI.GRN if st == "running" else (UI.ORG if st == "error" else UI.MUT))
	phone.on_mwpc(st, mwpc.url(), mwpc.text)


func check_updates() -> void:
	_mod("start").check_updates()


func run_update(automatic: bool, by_hand: bool) -> void:
	await _mod("start").run_update(automatic, by_hand)


func _restore_window(args: PackedStringArray) -> void:
	_mod("start")._restore_window(args)


func restart_args() -> PackedStringArray:
	return _mod("start").restart_args()


const KEEP := ["pad_auto", "pad_sens", "pad_inv_y", "pad_swap", "pad_rumble", "colors_on", "seasons_on", "pad_dead", "pad_center", "show_laser", "game_max", "tunnel_host", "tunnel_code", "tunnel_on", "cam_fx", "cam_fy", "calendar_on", "ort_env", "ort_hide", "ort_cars", "ort_forest", "ort_camp", "game_rescue", "game_teamgoal", "game_teams", "world_cloth", "world_smoke", "world_fireflies", "lamp_share", "cloud_shadows", "gusts", "look_at_light", "game_goal", "sound_on", "night_gain", "ir_range", "game_mode", "game_lives", "game_items", "game_cones", "game_noise", "game_stones", "game_powers", "game_spectate", "game_photos", "game_fx_laser", "game_fx_paint", "game_fx_flash", "game_tap", "game_learn_miss", "game_learn_report", "game_learn_paths", "game_blind_bonus", "game_hides", "game_decoy", "game_night", "game_events", "game_checkpoints", "game_tasks", "game_autohandicap", "game_random", "lens_noise", "lens_vignette", "lens_drops", "insects_on", "game_minutes", "game_level", "game_quality", "game_guard", "eco_idle", "autostart_min", "autostart_mwpc", "autostart_lock", "last_scene", "fp_spot", "szene_spot", "bt_spot", "bt_bed", "bt_season", "bt_free", "bt_events", "bt_mount", "bt_bag", "bt_stove", "bt_wall", "bt_orient", "bt_marks", "bt_visited", "auto_update", "dev_updates", "news_seen", "news_popup", "show_zones3d", "show_det3d", "fauna_on", "twin", "ui_simple", "ui_icons", "ui_icons_pick", "start_groups", "mine_mig", "auto_visitors", "daily_life", "real_weather", "real_time", "night_weather", "surprise_on", "mix", "visit_rate", "max_visitors", "visitor_speed", "flee_light", "flee_sound", "privat_on",
		"avoid_on", "grafik_mode", "cam_wippen", "foto_tex", "reduce_motion", "tour_auto", "blinki_on", "quality", "view_scale", "win_fps", "auto_perf", "meadow_on", "season", "mover_on", "mover_max", "mast_h", "patrol_judge", "map_on", "map_size", "map_span", "live_on", "live_cam", "live_size", "ort_lat", "ort_lon", "ort_name", "weather", "wind", "ambient", "moon", "moon_auto", "cam1_yaw", "stream_last", "game_bots", "game_tutorial", "game_daily", "game_ghost", "game_heart", "game_botguard", "kids_on", "kids_ask", "kids_thief", "kids_scary", "kids_laser", "kids_sound", "kids_stars", "dev_area", "news_links"]
var _settings_dirty := false


func _load_settings() -> void:
	_mod("einstellungen")._load_settings()


var _hour_saved_t := 0.0


func _save_settings() -> void:
	_mod("einstellungen")._save_settings()


func set_autostart(on: bool) -> void:
	_mod("start").set_autostart(on)


func setup_autologon() -> void:
	await _mod("start").setup_autologon()


func _dev_check() -> void:
	await _mod("start")._dev_check()


func set_auto_update(on: bool) -> void:
	_mod("start").set_auto_update(on)


func _sync_update_ui() -> void:
	_mod("status")._sync_update_ui()


func _toggle_phone() -> void:
	if phone.visible:
		phone.visible = false
	else:
		phone.open()


var feedback_dlg = null                # MoveEye 2.98.33: feedback.gd (made at the first use; from 3D-4.2x by mehr.gd)
var mehr = null                        # 3D-4.2x: mehr.gd («Mehr»: feedback, tour, self-check, log, look)


func _feedback_open() -> void:
	if feedback_dlg == null:
		var cl := CanvasLayer.new()
		cl.layer = 61
		add_child(cl)
		feedback_dlg = preload("res://scripts/feedback.gd").new()
		feedback_dlg.main = self
		feedback_dlg.theme = UI.theme()
		cl.add_child(feedback_dlg)
	feedback_dlg.open()


func _open_preview() -> void:
	"""the web page of MoveEye as it looks on a phone / tablet, upright and across (page /preview of MoveEye)"""
	if mw_addr == "" or now() - mw_t > 10.0:
		status_label.text = "MoveEye ist nicht verbunden – zuerst in MoveEye die Simulation einschalten."
		return
	OS.shell_open("%s://%s:%d/preview" % [str(mw.get("mw_scheme", "http")), mw_addr, int(mw.get("mw_port", 5000))])


func _ui_control(parent: Control, c: Dictionary) -> void:
	_mod("einstellungen")._ui_control(parent, c)


var _syncing := false


func refresh_controls() -> void:
	_mod("status").refresh_controls()


func _sync_ui() -> void:
	_mod("status")._sync_ui()


func group_active(g: String) -> int:
	return _mod("status").group_active(g)


func _game_report_send() -> void:
	if game == null:
		return
	var m: String = game.learn.send()
	game.learn.info = m
	game.news("📊 " + m)


func _groups_on() -> Dictionary:
	return _mod("status")._groups_on()


func _paint_groups() -> void:
	_mod("status")._paint_groups()


func _update_status() -> void:
	_mod("status")._update_status()


# ---- flying through the world, placing visitors ---------------------------------------------------------------------------
# From 3D-3.6 everything with the mouse (like a map): left drag = move (the ground sticks to the mouse), right drag = turn
# round the point under the mouse, wheel = zoom to the mouse, middle drag (or Alt + right) = look round, double click = fly
# there, click on a visitor = choose it (box with Folgen / Erschrecken / Weg), drag a visitor = carry it. Buttons below.
var look := false
var yaw := 0.0
var pitch := 0.0
var fly_speed := 8.0
var view_mode := 0                    # 0 free, 1 camera 1, 2 camera 2, 3 thermal picture
var _look_base := []                  # «Handy als Fenster»: the direction when the phone started to steer
var m_btn := 0                        # mouse button held in the world
var m_from := Vector2.ZERO
var m_moved := 0.0
var m_grab := Vector3.ZERO            # ground point that sticks to the mouse (moving) / turning point
var m_drag = null                     # visitor carried with the mouse
var m_cand = null                     # visitor under the mouse when the button went down
var m_skip := false                   # the double click already did something
var selected = null                   # chosen visitor (box below)
var follow := false
var fly_tw: Tween
var view_bar: HBoxContainer
var sel_box: PanelContainer
var sel_label: Label
var follow_btn: Button
var compass: Control
var thermal_full: TextureRect
var view_btns := {}
var sel_ring: Control
var rover_pad                         # rover_pad.gd: drive the mover here (from 3D-3.15)
var patrol                            # patrol.gd: «Patrouille» (3D-3.61)
var toolbar                           # toolbar.gd: the tool bar at the bottom (3D-3.61)
var patrol_judge := "mw"              # game «Patrouille»: mw = the real detection of MoveEye decides, sim = the simulator guard
var pad_dead := 0.12                  # 3D-3.96: dead zone of the controller sticks (stick drift; 3D-3.97: round, per stick)
var pad_auto := true                  # 3D-3.97: learn the rest position by itself while a stick rests
var pad_sens := 1.0                   # 3D-4.13: sensitivity of the head / view stick (padmap.gd)
var pad_inv_y := false                # 3D-4.13: invert Y of the head / view stick
var pad_swap := false                 # 3D-4.13: swap the sticks (left = rover / walk, right = head / look)
var pad_rumble := true                # 3D-4.13: vibration of the controller (erwischt, Treffer, Alarm, Kamera sieht dich)
var padmap                            # 3D-4.13: padmap.gd - ONE controller mapping for the window, explore, game, MoveEye
var padhud                            # 3D-4.13: padhud.gd - chips of the controllers, direction, focus ring
var padtest
var pad_center := [0.0, 0.0, 0.0, 0.0] # 3D-3.96: rest position of the sticks (measured with «Controller kalibrieren»)
var explore                           # explore.gd: «Erkunden» with the rover - keyboard, mouse, touch, game controller (3D-3.55)
var padview                           # padview.gd: the «Controller-Ansicht» of MoveEye (phone / tablet + game controller)
var pad_drive := Vector2.ZERO         # (forward, turn right) from rover_pad, -1 … 1
var pad_t := -10.0
var pad_on := false                   # rover_pad is used right now
var minimap                           # minimap.gd: overview map in the corner (from 3D-3.12)
var liveview                          # liveview.gd: live picture of a camera below the map (3D-3.34)
var live_on := false
var live_cam := 0
var live_size := 260.0
var live_btn: Button
var map_on := true
var map_size := 220.0
var map_span := 80.0
var map_btn: Button


func _over_hud(p: Vector2) -> bool:
	"""is the mouse over the control panel or one of the boxes on the view (map, live picture, stick, bar …)?"""
	for c in [ui_root, show_btn, view_bar, minimap, liveview, rover_pad, sel_box, karte, toolbar, cam_card, home_editor, smalltv.tile if smalltv != null else null]:
		if c != null and is_instance_valid(c) and c is Control and (c as Control).is_visible_in_tree() and (c as Control).modulate.a > 0.01 and (c as Control).get_global_rect().has_point(p):
			return true
	return fenster != null and fenster.over(p)        # Paket «Fenster»: alle Fenster im gemeinsamen Rahmen


func _unhandled_input(ev: InputEvent) -> void:
	if home_editor != null and home_editor.handle_input(ev):
		return                                         # 3D-3.73: the building kit (right click = away)
	if patrol != null and patrol.handle_input(ev):
		return                                         # 3D-3.61: setting the route / dragging the area
	if spectate and ((ev is InputEventMouseButton and ev.pressed and ev.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE])
			or (ev is InputEventKey and ev.pressed and ev.keycode in [KEY_W, KEY_A, KEY_S, KEY_D, KEY_Q, KEY_E])):
		spectate_stop()                                # somebody steers by hand: the spectator camera lets go
	if ev is InputEventMouseButton and ev.pressed and _over_hud(ev.position):
		return                                         # 3D-3.35: over the control panel (or another box) the view never moves
	if ev is InputEventMouseButton:
		var b: int = ev.button_index
		if ev.pressed and b in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			if b == MOUSE_BUTTON_LEFT and rifle_on:
				shoot(view_cam.project_ray_origin(ev.position), view_cam.project_ray_normal(ev.position))
				return
			_to_free_view()
			m_btn = b
			m_from = ev.position
			m_moved = 0.0
			m_skip = false
			m_drag = null
			m_cand = _visitor_at(ev.position) if b == MOUSE_BUTTON_LEFT else null
			var g = _ground_at(ev.position)
			m_grab = g if g != null else view_cam.global_position - view_cam.global_transform.basis.z * 30.0
			yaw = view_cam.rotation.y
			pitch = view_cam.rotation.x
			look = b == MOUSE_BUTTON_MIDDLE or (b == MOUSE_BUTTON_RIGHT and ev.alt_pressed)
			if b == MOUSE_BUTTON_LEFT and ev.double_click and m_cand == null and g != null:
				fly_to(g)
				m_skip = true
		elif not ev.pressed and b == m_btn:
			if b == MOUSE_BUTTON_LEFT and m_moved < 6.0 and not m_skip:
				if place_kind != "":
					_place(ev.position)
				elif m_cand != null and is_instance_valid(m_cand):
					select_visitor(m_cand)
				else:
					select_visitor(null)
			m_btn = 0
			m_drag = null
			look = false
		elif ev.pressed and b == MOUSE_BUTTON_WHEEL_UP:
			if ev.shift_pressed:
				fly_speed = min(80.0, fly_speed * 1.2)
			else:
				_zoom_at(ev.position, 1.0)
		elif ev.pressed and b == MOUSE_BUTTON_WHEEL_DOWN:
			if ev.shift_pressed:
				fly_speed = max(1.0, fly_speed / 1.2)
			else:
				_zoom_at(ev.position, -1.0)
	elif ev is InputEventMouseMotion and m_btn != 0:
		m_moved += ev.relative.length()
		if m_moved < 4.0:
			return
		follow = false
		if look:                                          # look round from where the eye is
			yaw -= ev.relative.x * 0.004
			pitch = clamp(pitch - ev.relative.y * 0.004, -1.5, 1.5)
			view_cam.rotation = Vector3(pitch, yaw, 0)
		elif m_btn == MOUSE_BUTTON_LEFT:
			if m_cand != null and is_instance_valid(m_cand) and place_kind == "":
				m_drag = m_cand                           # carry the visitor
				var g = _ground_at(ev.position)
				if g != null:
					var q: Vector3 = free_spot(g, m_drag.radius, m_drag.kind == "person")
					m_drag.position = Vector3(q.x, ground_y(q.x, q.z), q.z)
			else:
				_pan_to(ev.position)
		elif m_btn == MOUSE_BUTTON_RIGHT:
			_orbit(ev.relative)
	elif ev is InputEventKey and ev.pressed and not ev.echo:
		match ev.keycode:
			KEY_1:
				set_view(1)
			KEY_2:
				set_view(2)
			KEY_3:
				set_view(3)
			KEY_0:
				set_view(0)
			KEY_H:
				show_panel(not ui_root.visible)
			KEY_T:
				tv.set_on(not tv.on)                    # TV mode (3D-3.44)
			KEY_P:
				_toggle_phone()
			KEY_K:
				if karte.visible:
					karte.visible = false
				else:
					open_map()
			KEY_G:
				rifle_on = not rifle_on
				_sync_ui()
			KEY_M:
				set_map(not map_on)
			KEY_L:
				set_live(not live_on)
			KEY_F:
				if selected != null:
					follow = not follow
					_paint_sel()
			KEY_ESCAPE:
				place_kind = ""
				_paint_palette()
				if patrol != null:
					patrol.edit = ""                # 3D-3.66: Esc ends setting points / the area
				if tv.on:
					tv.set_on(false)
				if replay.on:
					replay.stop()
				select_visitor(null)
			KEY_DELETE:
				if selected != null and is_instance_valid(selected):
					selected.queue_free()
					select_visitor(null)


func _ground_at(p: Vector2):
	return ground_hit(view_cam.project_ray_origin(p), view_cam.project_ray_normal(p))


func _to_free_view() -> void:
	if view_mode != 0:
		set_view(0)


func _pan_to(p: Vector2) -> void:
	"""the grabbed point of the ground stays under the mouse"""
	var o := view_cam.project_ray_origin(p)
	var d := view_cam.project_ray_normal(p)
	if abs(d.y) < 0.02:
		return
	var t := (m_grab.y - o.y) / d.y
	if t <= 0.0 or t > 3000.0:
		return
	var h := o + d * t
	var delta := m_grab - h
	delta.y = 0.0
	if delta.length() > 200.0:
		delta = delta.normalized() * 200.0
	view_cam.global_position += delta
	_keep_above()


func _orbit(rel: Vector2) -> void:
	"""turn round the grabbed point: sideways round the vertical, up / down round the side axis of the view"""
	var t := view_cam.global_transform
	t.origin -= m_grab
	t = Transform3D(Basis(Vector3.UP, -rel.x * 0.006), Vector3.ZERO) * t
	var side := t.basis.x.normalized()
	var t2 := Transform3D(Basis(side, -rel.y * 0.005), Vector3.ZERO) * t
	var up_ang := rad_to_deg(asin(clampf(t2.origin.normalized().y, -1.0, 1.0)))
	if up_ang > 3.0 and up_ang < 88.0 and t2.basis.y.y > 0.05:
		t = t2
	t.origin += m_grab
	view_cam.global_transform = t
	_keep_above()


func _zoom_at(p: Vector2, dir: float) -> void:
	_to_free_view()
	follow = false
	var g = _ground_at(p)
	var target: Vector3 = g if g != null else view_cam.global_position + view_cam.project_ray_normal(p) * 30.0
	var dist := view_cam.global_position.distance_to(target)
	var step: float = dist * (0.2 if dir > 0 else -0.25)
	if dir > 0 and dist - step < 1.5:
		step = max(0.0, dist - 1.5)
	var np := view_cam.global_position + (target - view_cam.global_position).normalized() * step
	if np.y - ground_y(np.x, np.z) > 400.0:
		return
	view_cam.global_position = np
	_keep_above()


func _keep_above() -> void:
	var gy := ground_y(view_cam.global_position.x, view_cam.global_position.z) + 0.4
	if view_cam.global_position.y < gy:
		view_cam.global_position.y = gy


func fly_to(p: Vector3, dist := 12.0) -> void:
	"""fly smoothly towards p (it stays in the middle of the view)"""
	_to_free_view()
	var fwd := -view_cam.global_transform.basis.z
	var to := p - fwd * dist
	to.y = max(to.y, ground_y(to.x, to.z) + 1.5)
	if fly_tw != null:
		fly_tw.kill()
	var start := view_cam.global_transform
	var end := Transform3D(Basis(), to).looking_at(p, Vector3.UP)
	fly_tw = create_tween()
	fly_tw.tween_method(func(f: float):
		view_cam.global_transform = start.interpolate_with(end, f), 0.0, 1.0, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


func _visitor_at(p: Vector2):
	"""the visitor nearest to the mouse on the screen (within 45 pixels)"""
	var best = null
	var bd := 45.0
	for v in visitors.get_children():
		if v.done:
			continue
		var w: Vector3 = v.global_position + Vector3(0, 0.6 if v.kind != "person" else 1.0, 0)
		if view_cam.is_position_behind(w):
			continue
		var d := view_cam.unproject_position(w).distance_to(p)
		if d < bd:
			bd = d
			best = v
	return best


func select_visitor(v) -> void:
	selected = v
	if v == null:
		follow = false
	_paint_sel()


func _visitor_name(v) -> String:
	var k: String = v.variant if v.kind == "person" and v.variant != "" else v.kind
	for e in VISITOR_LIST:
		if e[0] == k:
			return e[1]
	return {"person": "Person", "car": "Auto", "dog": "Hund"}.get(k, k)


func _paint_sel() -> void:
	if sel_box == null:
		return
	var ok: bool = selected != null and is_instance_valid(selected) and not selected.done
	sel_box.visible = ok
	if ok:
		sel_label.text = _visitor_name(selected)
		follow_btn.text = "Nicht mehr folgen" if follow else "Folgen (F)"


func set_view(m: int) -> void:
	if m != view_mode:
		view_zoom = 1.0                                # tasten.gd: a new view starts without zoom
	view_mode = m
	if thermal_full != null:
		thermal_full.visible = m == 3
	for k in view_btns:
		view_btns[k].set_pressed_no_signal(k == m)


func set_live(on: bool, which := -1, w := -1.0) -> void:
	live_on = on
	if which >= 0:
		live_cam = which
	if w > 0.0:
		live_size = w
	_settings_dirty = true
	if liveview != null:
		liveview.visible = on
		liveview.cam = live_cam
		liveview.width_px = live_size
		liveview.apply()
	if live_btn != null:
		live_btn.set_pressed_no_signal(on)


func set_map(on: bool) -> void:
	map_on = on
	_settings_dirty = true
	if minimap != null:
		minimap.visible = on
	if map_btn != null:
		map_btn.set_pressed_no_signal(on)


func _view_preset(which: String) -> void:
	set_view(0)
	follow = false
	var to: Transform3D
	match which:
		"top":
			to = Transform3D(Basis(), Vector3(0, ground_y(0, 0) + 70.0, 8.0)).looking_at(Vector3(0, ground_y(0, 0), -6.0), Vector3.UP)
		_:
			to = Transform3D(Basis(), Vector3(0.0, ground_y(0, 4) + 3.2, 5.0)).looking_at(Vector3(0, ground_y(0, -12) + 1.0, -12.0), Vector3.UP)
	if fly_tw != null:
		fly_tw.kill()
	var start := view_cam.global_transform
	fly_tw = create_tween()
	fly_tw.tween_method(func(f: float):
		view_cam.global_transform = start.interpolate_with(to, f), 0.0, 1.0, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


func _build_view_bar(layer: CanvasLayer, th: Theme) -> void:
	_mod("menues")._build_view_bar(layer, th)


func _sel_action(w: String) -> void:
	if selected == null or not is_instance_valid(selected):
		return
	if w == "scare":
		if selected.kind == "person":
			selected.startle()
		else:
			selected.scare()
	elif w == "away":
		var d: Vector3 = selected.position.normalized() if selected.position.length() > 0.5 else Vector3(1, 0, 0)
		selected.route = [selected.position + d * 70.0]
		selected.target = selected.position + d * 70.0
	elif w == "del":
		selected.queue_free()
		select_visitor(null)


func _view_overlays() -> void:
	"""every frame: compass, ring round the chosen visitor, follow it"""
	if compass != null:
		compass.queue_redraw()
	if selected != null and (not is_instance_valid(selected) or selected.done):
		select_visitor(null)
	if selected != null and follow and view_mode == 0 and (fly_tw == null or not fly_tw.is_running()):
		var tp: Vector3 = selected.global_position + Vector3(0, 1.0, 0)
		var back := view_cam.global_position - tp
		back.y = 0.0
		if back.length() < 0.1:
			back = Vector3(0, 0, 1)
		var want := tp + back.normalized() * 9.0 + Vector3(0, 4.0, 0)
		want.y = max(want.y, ground_y(want.x, want.z) + 1.5)
		view_cam.global_position = view_cam.global_position.lerp(want, clampf(get_process_delta_time() * 3.0, 0.0, 1.0))
		view_cam.look_at(tp, Vector3.UP)
	if sel_ring != null:
		sel_ring.queue_redraw()


func _fly(dt: float) -> void:
	if view_mode == 1:
		view_cam.global_transform = cams[0].global_transform
		view_cam.fov = 41.0 / view_zoom
		return
	if view_mode == 2:
		view_cam.global_transform = cams[1].global_transform
		view_cam.fov = 62.0 / view_zoom
		return
	view_cam.fov = 70
	view_cam.far = 7000.0 if terrain else 2000.0
	if phone != null and phone.visible and phone.screen.has_focus():
		return                                   # keys go to the phone
	if explore != null and (explore.on or explore.fly):
		return                                   # exploring: W A S D drive the rover (Entwicklertool: the fly camera, explore.gd)
	if maggie != null and maggie.walking():
		return                                   # «Maggie und der Bergkristall»: W A S D move the figure (maggie_story.gd)
	if typing():
		return                                   # 3D-3.88: letters typed into a search field do not fly the view
	var mv := Vector3.ZERO
	if Input.is_key_pressed(KEY_W):
		mv.z -= 1
	if Input.is_key_pressed(KEY_S):
		mv.z += 1
	if Input.is_key_pressed(KEY_A):
		mv.x -= 1
	if Input.is_key_pressed(KEY_D):
		mv.x += 1
	if Input.is_key_pressed(KEY_E):
		mv.y += 1
	if Input.is_key_pressed(KEY_Q):
		mv.y -= 1
	if mv != Vector3.ZERO:
		var f := fly_speed * (3.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0)
		view_cam.global_translate(view_cam.global_transform.basis * mv.normalized() * f * dt)
		view_cam.position.y = max(ground_y(view_cam.position.x, view_cam.position.z) + 0.3, view_cam.position.y)


var place_kind := ""                  # chosen in the pictures of the visitors: a click into the world puts it there


func _place(p: Vector2) -> void:
	if place_kind == "rover":                          # 3D-3.60: «Mover versetzen» - the next click puts it there
		place_rover_at(p)
		place_kind = ""
		_paint_palette()
		return
	if place_kind.begins_with("twin_"):                # 3D-4.4: tent / car of «Dein Platz»
		zwilling.place_at_screen(place_kind, p)
		place_kind = ""
		return
	if place_kind != "":
		_place_at(place_kind, p)


func place_rover_at(p: Vector2) -> bool:
	"""the rover (or MoveEye standing still) to the spot under the mouse, never inside an object"""
	var from := view_cam.project_ray_origin(p)
	var hit = ground_hit(from, view_cam.project_ray_normal(p))
	if hit == null or from.distance_to(hit) > 400.0:
		return false
	var a: Vector3 = free_spot(hit, 0.6, false)
	if mover_on:
		rig.position = Vector3(a.x, ground_y(a.x, a.z), a.z)
	else:
		home_pos = Vector3(a.x, 0, a.z)
		mover_home()
	return true


func _place_at(k: String, p: Vector2) -> void:
	"""a visitor where the mouse points (on the ground, never inside an object); it then walks off in some direction"""
	if k.begins_with("twin_"):                        # 3D-4.x: tent / car of «Dein Platz», dragged from its tile
		zwilling.place_at_screen(k, p)
		return
	if k.begins_with("obj:"):                         # 3D-3.86: an object of the inventory stays where it is put
		if inventar != null:
			inventar.place_at_screen(k, p)
		return
	var from := view_cam.project_ray_origin(p)
	var d := view_cam.project_ray_normal(p)
	var hit = ground_hit(from, d)
	if hit == null or from.distance_to(hit) > 400.0:
		return
	var a: Vector3 = free_spot(hit, 0.5, k in PEOPLE_KINDS)
	var ang := randf() * TAU
	var b := a + Vector3(cos(ang), 0, sin(ang)) * 40.0
	spawn(k, a, b)


# ---- wildlife watching: the rifle (bloodless - a hit animal hops, sees stars and runs away; people cannot be hit) ----------
var shot_msg := ""
var shot_msg_t := 0.0
const POINTS := {"chamois": 30, "ibex": 35, "lynx": 50, "fox": 10, "deer": 15, "boar": 20, "badger": 25, "cat": 5, "dog": 5, "wolf": 40, "marten": 30, "squirrel": 10}


func _build_crosshair(layer: CanvasLayer) -> void:
	_mod("menues")._build_crosshair(layer)


func _make_sound(kind: String) -> AudioStreamWAV:
	"""a short sound made from numbers: a soft 'plopp' for the shot, a 'boing' for a hit"""
	var rate := 22050
	var dur := 0.35 if kind == "shot" else 0.6
	var n := int(rate * dur)
	var data := PackedByteArray()
	data.resize(n * 2)
	var ph := 0.0
	for i in range(n):
		var t := float(i) / rate
		var v := 0.0
		if kind == "shot":
			v = randf_range(-1.0, 1.0) * exp(-t * 30.0) * 0.6 + sin(TAU * 70.0 * t) * exp(-t * 12.0) * 0.6
		else:
			ph += TAU * (220.0 + 180.0 * sin(t * 40.0) * exp(-t * 3.0)) / rate
			v = sin(ph) * exp(-t * 4.0) * 0.5
		data.encode_s16(i * 2, int(clamp(v, -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.stereo = false
	w.data = data
	return w


func reset_score() -> void:
	shots = 0
	hits = 0
	points = 0


func shoot_head() -> void:
	"""a shot straight out of the head camera: aim with the pan / tilt head of MoveEye"""
	var tr: Transform3D = cams[0].global_transform
	shoot(tr.origin, -tr.basis.z)


func shoot(from: Vector3, d: Vector3) -> void:
	shots += 1
	d = d.normalized()
	shot_sound.play()
	var best = null
	var best_t := 1e9
	var person_t := 1e9
	for v in visitors.get_children():
		if v.done:
			continue
		for sp in v.hit_spheres():
			var c: Vector3 = v.global_position + Vector3(0, sp[0], 0)
			var t := (c - from).dot(d)
			if t < 0.3 or t > 300.0 or (from + d * t).distance_to(c) > float(sp[1]):
				continue
			if v.kind == "person" or v.kind == "car":
				person_t = min(person_t, t)
			elif t < best_t:
				best_t = t
				best = v
	if best != null and best_t < person_t:
		var pts: int = best.hit()
		var above: Vector3 = best.global_position + Vector3(0, best.body_h + 0.9, 0)
		if pts > 0:
			hits += 1
			points += pts
			hit_sound.play()
			_say("Treffer! %s +%d" % [_animal_name(best.kind), pts], above, Color(1.0, 0.85, 0.2))
		else:
			_say("Der sieht schon Sterne", above, Color(0.9, 0.9, 0.9))
	elif person_t < 1e9:
		_say("Nicht auf Menschen! Nur Tiere.", from + d * min(person_t, 40.0), Color(1.0, 0.4, 0.3))
	else:
		var hit = Plane(Vector3.UP, 0).intersects_ray(from, d)
		if hit != null and from.distance_to(hit) < 300.0:
			_puff(hit)
			_say("Daneben", hit + Vector3(0, 1.0, 0), Color(0.85, 0.85, 0.85))
		else:
			_say("Daneben", from + d * 20.0, Color(0.85, 0.85, 0.85))
	_update_status()


var mw_shots := {"hits": 0, "false": 0}   # 3D-3.70: shots of MoveEye into the world (outside a game round)


func mw_shot(x: float, y: float, who: String) -> Dictionary:
	"""a shot from MoveEye: x, y (0..1) in the picture of the head camera. In a round: catch a runner (a miss is a false
	alarm). Otherwise into the world: a person is caught (runs away), an animal sees stars - a miss is a false alarm."""
	if game != null and game.round_state == "play":
		if game_mode == "mwhand":
			return game.mw_catch(who, x, y)
		return game.shot_at(who, x, y)
	var vs := Vector2(vps[0].size)
	var at := Vector2(clampf(x, 0.0, 1.0), clampf(y, 0.0, 1.0)) * vs
	var cam: Camera3D = cams[0]
	var from := cam.project_ray_origin(at)
	var d := cam.project_ray_normal(at).normalized()
	if shot_sound != null:
		shot_sound.play()
	var best = null
	var best_t := 1e9
	for v in visitors.get_children():
		if v.done:
			continue
		for sp in v.hit_spheres():
			var c: Vector3 = v.global_position + Vector3(0, sp[0], 0)
			var t := (c - from).dot(d)
			if t < 0.3 or t > 300.0 or (from + d * t).distance_to(c) > float(sp[1]) * 1.35:
				continue
			if t < best_t:
				best_t = t
				best = v
	if best != null:
		mw_shots["hits"] = int(mw_shots["hits"]) + 1
		var above: Vector3 = best.global_position + Vector3(0, best.body_h + 0.9, 0)
		var nm: String = "Person" if best.kind == "person" else ("Auto" if best.kind == "car" else _animal_name(best.kind))
		if best.kind in ["person", "child", "jogger", "thief", "burglar", "car"] or best.kind in PEOPLE_KINDS:
			if best.has_method("scare"):
				best.scare()
		else:
			best.hit()
		if hit_sound != null:
			hit_sound.play()
		_say("Erwischt! %s" % nm, above, Color(0.45, 1.0, 0.55))
		return {"ok": true, "hit": true, "kind": best.kind, "text": "✓ %s erwischt!" % nm, "stats": mw_shots}
	mw_shots["false"] = int(mw_shots["false"]) + 1
	var g = Plane(Vector3.UP, 0).intersects_ray(from, d)
	if g != null and from.distance_to(g) < 300.0:
		_puff(g)
		_say("Daneben – Fehlalarm", g + Vector3(0, 1.0, 0), Color(1.0, 0.45, 0.35))
	return {"ok": true, "hit": false, "text": "✗ Daneben – als Fehlalarm markiert", "stats": mw_shots}


func _animal_name(k: String) -> String:
	return {"fox": "Fuchs", "deer": "Reh", "boar": "Wildschwein", "badger": "Dachs", "cat": "Katze", "dog": "Hund", "wolf": "Wolf", "marten": "Marder",
			"squirrel": "Eichhörnchen", "hare": "Hase", "hedgehog": "Igel", "chamois": "Gämse", "ibex": "Steinbock", "lynx": "Luchs"}.get(k, k)


func _say(text: String, p: Vector3, col: Color, lay := 1) -> void:
	"""a word that floats up in the world (and on the screen at the top left)"""
	shot_msg = text
	shot_msg_t = now()
	var l := Label3D.new()
	l.text = text
	l.font_size = 96
	l.pixel_size = 0.004 * clamp(p.distance_to(view_cam.global_position) / 6.0, 1.5, 6.0)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.modulate = col
	l.outline_size = 12
	l.outline_modulate = Color(0, 0, 0, 0.8)
	l.layers = lay
	l.position = p
	add_child(l)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "position", p + Vector3(0, 1.4, 0), 1.8)
	tw.tween_property(l, "modulate:a", 0.0, 1.8).set_delay(0.6)
	tw.chain().tween_callback(l.queue_free)


func _puff(p: Vector3) -> void:
	"""a little cloud of dust where a shot hits the ground"""
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.12
	s.height = 0.24
	mi.mesh = s
	var mm := StandardMaterial3D.new()
	mm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mm.albedo_color = Color(0.75, 0.7, 0.6, 0.8)
	mi.material_override = mm
	mi.layers = 1
	mi.position = p + Vector3(0, 0.1, 0)
	add_child(mi)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE * 5.0, 0.8)
	tw.tween_property(mm, "albedo_color:a", 0.0, 0.8)
	tw.chain().tween_callback(mi.queue_free)


# ---- obstacles: visitors go round them and never through (from 3D-2.0) --------------------------------------------------
# circles (trees, posts) and turned boxes (houses, caravans, cars, fences), kept in a grid of 4 m cells so that even the forest
# with 300 trees stays quick. people_only: fences and hedges stop people, cats and foxes slip through.
var avoid_on := true
var obstacles: Array = []
var ob_grid := {}
const OB_CELL := 4.0


var tree_spots: Array = []             # 3D-3.76: [Vector2 trunk, crown radius, crown bottom] - the camera of a player keeps out


func clear_obstacles() -> void:
	tree_spots.clear()
	obstacles.clear()
	ob_grid.clear()


# 3D-4.x Welten (worlds.gd): while a place is built inside a world: obstacles beyond ob_clip (local) are left out, ob_xf moves
# them (a neighbour), none in ob_excl ([[centre (world), r], …]: the active place)
var ob_xf := Transform3D.IDENTITY
var ob_clip := 0.0
var ob_excl: Array = []
var _ob_skip := false


func _ob_place(p: Vector3):
	"""the obstacle point in the world, or null (left out)"""
	_ob_skip = false
	if ob_clip > 0.0 and Vector2(p.x, p.z).length() > ob_clip:
		_ob_skip = true
		return null
	var q := ob_xf * p
	for e in ob_excl:
		if Vector2(q.x, q.z).distance_to(e[0]) < float(e[1]):
			_ob_skip = true
			return null
	return q


func add_obstacle(p: Vector3, r: float, people_only := false) -> void:
	var pw = _ob_place(p)
	if pw == null:
		return
	p = pw
	var o := {"c": Vector2(p.x, p.z), "r": r, "po": people_only, "id": obstacles.size()}
	obstacles.append(o)
	_ob_insert(o, Vector2(p.x - r, p.z - r), Vector2(p.x + r, p.z + r))


func add_obstacle_box(p: Vector3, sx: float, sz: float, rot_y: float, people_only := false) -> void:
	"""a box of sx × sz metres around p, turned like a node with rotation.y = rot_y"""
	var pw = _ob_place(p)
	if pw == null:
		return
	p = pw
	rot_y += ob_xf.basis.get_euler().y
	var b := Basis(Vector3.UP, rot_y)
	var o := {"c": Vector2(p.x, p.z), "h": Vector2(sx / 2.0, sz / 2.0), "b": b, "bi": b.inverse(), "po": people_only, "id": obstacles.size()}
	obstacles.append(o)
	var ext := Vector2(sx, sz).length() / 2.0
	_ob_insert(o, Vector2(p.x - ext, p.z - ext), Vector2(p.x + ext, p.z + ext))


func add_obstacle_node(n: Node3D, local_center: Vector3, sx: float, sz: float, people_only := false) -> void:
	"""a box in the frame of a scene node (house, caravan, hut ...)"""
	add_obstacle_box(n.transform * local_center, sx, sz, n.rotation.y, people_only)


func _ob_insert(o: Dictionary, lo: Vector2, hi: Vector2) -> void:
	for x in range(int(floor(lo.x / OB_CELL)), int(floor(hi.x / OB_CELL)) + 1):
		for z in range(int(floor(lo.y / OB_CELL)), int(floor(hi.y / OB_CELL)) + 1):
			var k := Vector2i(x, z)
			if not ob_grid.has(k):
				ob_grid[k] = []
			ob_grid[k].append(o)


func _ob_near(p: Vector2) -> Array:
	var out := []
	var seen := {}
	var cx := int(floor(p.x / OB_CELL))
	var cz := int(floor(p.y / OB_CELL))
	for x in range(cx - 1, cx + 2):
		for z in range(cz - 1, cz + 2):
			for o in ob_grid.get(Vector2i(x, z), []):
				if not seen.has(o["id"]):
					seen[o["id"]] = true
					out.append(o)
	return out


func _ob_closest(o: Dictionary, p: Vector2) -> Array:
	"""[nearest point on the obstacle, distance to it (negative inside), outward direction]"""
	var c: Vector2 = o["c"]
	if o.has("r"):
		var v := p - c
		var l := v.length()
		var n := v / l if l > 0.0001 else Vector2(1, 0)
		return [c + n * float(o["r"]), l - float(o["r"]), n]
	var bi: Basis = o["bi"]
	var b: Basis = o["b"]
	var h: Vector2 = o["h"]
	var l3: Vector3 = bi * Vector3(p.x - c.x, 0, p.y - c.y)
	var lo := Vector2(l3.x, l3.z)
	if abs(lo.x) <= h.x and abs(lo.y) <= h.y:                 # inside: out through the nearest side
		var px: float = h.x - abs(lo.x)
		var pz: float = h.y - abs(lo.y)
		var ql := lo
		var nl := Vector2.ZERO
		if px < pz:
			ql.x = h.x * sign(lo.x if lo.x != 0.0 else 1.0)
			nl = Vector2(sign(lo.x if lo.x != 0.0 else 1.0), 0)
		else:
			ql.y = h.y * sign(lo.y if lo.y != 0.0 else 1.0)
			nl = Vector2(0, sign(lo.y if lo.y != 0.0 else 1.0))
		var qw: Vector3 = b * Vector3(ql.x, 0, ql.y)
		var nw: Vector3 = b * Vector3(nl.x, 0, nl.y)
		return [c + Vector2(qw.x, qw.z), -min(px, pz), Vector2(nw.x, nw.z)]
	var qc := Vector2(clamp(lo.x, -h.x, h.x), clamp(lo.y, -h.y, h.y))
	var q3: Vector3 = b * Vector3(qc.x, 0, qc.y)
	var q := c + Vector2(q3.x, q3.z)
	var v2 := p - q
	var d2 := v2.length()
	return [q, d2, v2 / d2 if d2 > 0.0001 else Vector2(1, 0)]


func avoid(p: Vector2, d: Vector2, rad: float, person := true, side := 0.0) -> Vector3:
	"""the way to walk: d, bent round the obstacles just ahead. side: go round on this side (+1 / -1, 0 = choose);
	returns (x, z, side used) - the visitor keeps its side for a while, else it swings to and fro at a corner"""
	var steer := Vector2.ZERO
	var used := side
	var strongest := 0.0
	for o in _ob_near(p):
		if o["po"] and not person:
			continue
		var r: Array = _ob_closest(o, p)
		var gap: float = float(r[1]) - rad
		if gap > 1.6:
			continue
		var n: Vector2 = r[2]
		if n.dot(d) > 0.3 and gap > 0.25:
			continue                                     # it is behind or beside: going away from it anyway
		var w: float = clamp((1.6 - gap) / 1.6, 0.0, 1.0)
		w *= w
		var t := Vector2(-n.y, n.x)
		var sd := used if used != 0.0 else (1.0 if t.dot(d) >= 0.0 else -1.0)
		t *= sd
		if w > strongest:
			strongest = w
			used = sd
		steer += (t * 1.3 + n * 0.5) * w
	var out := d + steer
	out = out.normalized() if out.length() > 0.001 else d
	return Vector3(out.x, out.y, used if strongest > 0.0 else 0.0)


func keep_out(p: Vector2, rad: float, person := true) -> Vector2:
	"""pushes a point that came too close out of every obstacle"""
	for o in _ob_near(p):
		if o["po"] and not person:
			continue
		var r: Array = _ob_closest(o, p)
		if float(r[1]) < rad:
			var n: Vector2 = r[2]
			var q: Vector2 = r[0]
			p = q + n * rad
	return p


func line_free(a: Vector3, b: Vector3) -> bool:
	return line_blocker(a, b).is_empty()


func line_blocker(a: Vector3, b: Vector3) -> Dictionary:
	"""what hides the point b (e.g. the top of the head of a player) from a camera at a - or {} if nothing.
	Every object has a height ("ht", set_obstacle_height; fences and hedges 1.2 m, else 3 m): the line of sight can
	pass above it. Thin things (trunks, poles, chairs) hide nobody; an object round the camera itself does not count."""
	var a2 := Vector2(a.x, a.z)
	var b2 := Vector2(b.x, b.z)
	var seg := b2 - a2
	var n := int(ceil(seg.length() / 2.0))
	var seen := {}
	for i in range(n + 1):
		var p: Vector2 = a2 + seg * (float(i) / float(max(1, n)))
		for o in _ob_near(p):
			if seen.has(o["id"]):
				continue
			seen[o["id"]] = true
			if o.has("r") and float(o["r"]) < 0.45:
				continue
			if float(_ob_closest(o, a2)[1]) < 0.3:
				continue                                  # the camera stands at / in it
			var t := _seg_hits(o, a2, b2)
			if t < 0.0:
				continue
			var ht: float = o.get("ht", 1.2 if o["po"] else 3.0)
			var hp := a2.lerp(b2, t)
			if lerp(a.y, b.y, t) - ground_y(hp.x, hp.y) > ht:
				continue                                  # the line of sight goes above it
			return o
	if terrain:                                           # a real place: hills hide too
		var m2 := int(ceil(seg.length() / 3.0))
		for i in range(1, m2):
			var f := float(i) / float(m2)
			var p := a2 + seg * f
			if ground_y(p.x, p.y) > lerp(a.y, b.y, f) + 0.05:
				return {"id": -1, "c": "Gelände", "terrain": true}
	elif gelaende != null and gelaende.hill_blocks(a, b):   # 3D-4.x: hills and hollows of the scene (gelaende.gd)
		return {"id": -1, "c": "Gelände", "terrain": true}
	return {}


func set_obstacle_height(ht: float) -> void:
	"""the height of the object added last (for the line of sight of the game)"""
	if not obstacles.is_empty() and not _ob_skip:
		obstacles[-1]["ht"] = ht


func _seg_hits(o: Dictionary, a: Vector2, b: Vector2) -> float:
	"""where the segment a-b enters the obstacle (0..1), -1 = not at all"""
	var c: Vector2 = o["c"]
	if o.has("r"):
		var ab := b - a
		var t: float = clamp((c - a).dot(ab) / max(0.0001, ab.length_squared()), 0.0, 1.0)
		return t if (a + ab * t).distance_to(c) < float(o["r"]) else -1.0
	var bi: Basis = o["bi"]
	var h: Vector2 = o["h"]
	var la3: Vector3 = bi * Vector3(a.x - c.x, 0, a.y - c.y)
	var lb3: Vector3 = bi * Vector3(b.x - c.x, 0, b.y - c.y)
	var p0 := Vector2(la3.x, la3.z)
	var d := Vector2(lb3.x, lb3.z) - p0
	var t0 := 0.0
	var t1 := 1.0
	for ax in range(2):                                    # slab test in the frame of the box
		var pa: float = p0[ax]
		var da: float = d[ax]
		var ha: float = h[ax]
		if abs(da) < 0.000001:
			if abs(pa) > ha:
				return -1.0
		else:
			var u0 := (-ha - pa) / da
			var u1 := (ha - pa) / da
			if u0 > u1:
				var tmp := u0
				u0 = u1
				u1 = tmp
			t0 = max(t0, u0)
			t1 = min(t1, u1)
			if t0 > t1:
				return -1.0
	return t0


func view_free(a: Vector2, b: Vector2, h: float, margin := 0.3) -> bool:
	"""3D-3.76: does the way from a (the player) to b (his camera, h metres high) pass through a tree crown or an object?"""
	var n := maxi(1, int(a.distance_to(b) / 0.3))
	for k in range(1, n + 1):
		var q := a.lerp(b, float(k) / n)
		for t in tree_spots:
			if h > float(t[2]) - 0.3 and q.distance_to(t[0]) < float(t[1]) + margin:
				return false
		if k == n and blocked(q, 0.35, true):
			return false
	return true


func blocked(p: Vector2, rad: float, person := false) -> bool:
	"""3D-3.76: is p closer than rad to an object (for the mover: person = false, things only for people do not count)"""
	for o in _ob_near(p):
		if o["po"] and not person:
			continue
		if float(_ob_closest(o, p)[1]) < rad:
			return true
	return false


func free_spot(p: Vector3, rad := 0.4, person := true) -> Vector3:
	"""a point near p that is not inside an obstacle (for placing visitors)"""
	var q := keep_out(Vector2(p.x, p.z), rad, person)
	q = keep_out(q, rad, person)
	return Vector3(q.x, p.y, q.y)


# ---- a flock of birds flying over now and then (more life in the pictures) -------------------------------------------
func _birds() -> void:
	var flock := Node3D.new()
	scene_parent.add_child(flock)
	var side := 1.0 if randf() < 0.5 else -1.0
	var z := randf_range(-60.0, -15.0)
	var y := randf_range(12.0, 25.0)
	var from := Vector3(-side * 120.0, y, z)
	var to := Vector3(side * 120.0, y + randf_range(-4, 4), z + randf_range(-30, 30))
	flock.position = from
	flock.look_at_from_position(from, to, Vector3.UP)
	var wings := []
	var dark := mat(Color(0.12, 0.12, 0.13))
	for i in range(randi_range(4, 9)):
		var b := Node3D.new()
		b.position = Vector3(randf_range(-4, 4), randf_range(-1.5, 1.5), randf_range(-1, 6) + i * 0.8)
		flock.add_child(b)
		var body := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.06
		cap.height = 0.3
		body.mesh = cap
		body.rotation.x = PI / 2
		body.material_override = dark
		b.add_child(body)
		for s in [-1, 1]:
			var w := Node3D.new()
			b.add_child(w)
			var wm := MeshInstance3D.new()
			wm.mesh = box(0.32, 0.015, 0.12)
			wm.position = Vector3(0.16 * s, 0, 0)
			wm.material_override = dark
			w.add_child(wm)
			wings.append([w, s, randf() * TAU])
	var t0 := now()
	var dur := from.distance_to(to) / randf_range(9.0, 13.0)
	var hold := {"flock": flock}           # in a dictionary, so the lambda does not keep a freed object
	var flap := func(_dt, t):
		var fl = hold["flock"]
		if fl == null or not is_instance_valid(fl):
			return true
		var f: float = (now() - t0) / dur
		fl.position = from.lerp(to, f)
		for w in wings:
			w[0].rotation.z = w[1] * (0.6 * sin(t * 11.0 + w[2]))
		if f >= 1.0:
			hold["flock"] = null
			wings.clear()
			fl.queue_free()
			return true
		return false
	anims.append(flap)


func host_name() -> String:
	return _mod("status").host_name()


# ---- the simulator window in MoveEye (3D-3.18): its picture as a stream, and mouse / finger / keys back -------------
var view_want_t := -100.0
var view_fps := 6.0
var view_jpg := PackedByteArray()
var view_no := 0
var _view_t := 0.0
var _in_pos := Vector2.ZERO
var _in_mask := 0
var _rkeys := {}                       # keys held from MoveEye -> time when they are let go by themselves
const VIEW_MAX_W := 1024
# 3D-3.58: the browser asks for its size (width × pixel density), quality and WebP (/view.jpg?w=&q=&fmt=)
var view_w := VIEW_MAX_W
var view_q := 0.72
var view_webp := false
var view_mime := "image/jpeg"
var view_mjpg_t := -100.0              # a stream (/view.mjpg) is open: it needs JPEG


func view_request(q: Dictionary) -> void:
	_mod("kamera").view_request(q)
const VIEW_KEYS := {"ArrowUp": KEY_UP, "ArrowDown": KEY_DOWN, "ArrowLeft": KEY_LEFT, "ArrowRight": KEY_RIGHT, "w": KEY_W, "a": KEY_A,
		"s": KEY_S, "d": KEY_D, "q": KEY_Q, "e": KEY_E, "r": KEY_R, "f": KEY_F, "PageUp": KEY_PAGEUP, "PageDown": KEY_PAGEDOWN,
		"0": KEY_0, "1": KEY_1, "2": KEY_2, "3": KEY_3, "4": KEY_4, "5": KEY_5, "+": KEY_PLUS, "-": KEY_MINUS, "Shift": KEY_SHIFT, "p": KEY_P,
		"Escape": KEY_ESCAPE, "Enter": KEY_ENTER, " ": KEY_SPACE, "k": KEY_K}      # 3.51.x: Esc / Enter / Leertaste / K for the stories


func view_rect() -> Rect2:
	return _mod("kamera").view_rect()


func _view_capture() -> void:
	_mod("kamera")._view_capture()


func view_input(evs: Array) -> int:
	return _mod("kamera").view_input(evs)


var ui_layer: CanvasLayer
var remote_vp: SubViewport = null
var view_clean_t := -100.0              # 3D-3.67: last picture asked for «clean» (full screen in the browser)
var _remote_back := []                 # [node, parent, index] to put back


func _remote_set(on: bool) -> void:
	_mod("kamera")._remote_set(on)


func _view_send(ev: InputEvent) -> void:
	_mod("kamera")._view_send(ev)



# ---- spectator camera (3D-3.22): a little director - follows the player in danger, shows the goal, the whole field,
# the view of MoveEye; changes the shot every few seconds and glides from one to the next ----
var spectate := false
var spec_shot := ""
var spec_who := -1
var spec_until := 0.0
var spec_label := ""
var spec_orbit := 0.0
var spec_order := 0
var spec_end_t := 0.0
var spec_switch_t := 0.0
var spec_cut_until := 0.0              # an event shot (caught / goal) runs until then


func spectate_cut(kind: String, slot: int, label: String) -> void:
	"""an event: the camera goes there at once and circles close round the player (3D-3.26)"""
	if not spectate:
		return
	spec_shot = kind
	spec_who = slot
	spec_label = label
	spec_orbit = randf() * TAU
	spec_until = now() + (3.2 if kind == "caught" else 4.5)
	spec_cut_until = spec_until
	spec_switch_t = now()


func spectate_start() -> void:
	spectate = true
	set_view(0)
	follow = false
	spec_until = 0.0
	spec_end_t = 0.0


func spectate_stop() -> void:
	spectate = false
	spec_label = ""


func _spec_runners() -> Array:
	var out := []
	if game == null:
		return out
	for p in game.players:
		if p != null and p["role"] == "runner" and p["state"] == "play":
			out.append(p)
	return out


func _spec_choose(t: float) -> void:
	spec_switch_t = t
	var rs := _spec_runners()
	spec_until = t + randf_range(6.0, 9.0)
	if game.round_state == "countdown":
		spec_shot = "field"
		spec_label = "Übersicht · gleich geht es los"
		return
	if game.round_state == "end":
		spec_shot = "goal"
		spec_label = "Ziel · die Runde ist vorbei"
		return
	var danger = null
	var near = null
	for p in rs:
		if danger == null or float(p["susp"]) > float(danger["susp"]):
			danger = p
		if near == null or p["actor"].position.distance_to(game.goal) < near["actor"].position.distance_to(game.goal):
			near = p
	if danger != null and float(danger["susp"]) > 55.0:
		spec_shot = "follow"
		spec_who = int(danger["slot"])
		spec_label = "Achtung: %s wird gleich entdeckt!" % danger["name"]
		spec_until = t + 5.0
		return
	if near != null and near["actor"].position.distance_to(game.goal) < 9.0 and randf() < 0.7:
		spec_shot = "goal"
		spec_who = int(near["slot"])
		spec_label = "%s ist kurz vor dem Ziel" % near["name"]
		return
	spec_order = (spec_order + 1) % 5
	if rs.size() >= 2 and spec_order == 4:              # 3D-3.60: all players in the picture
		spec_shot = "group"
		spec_label = "Alle Spieler im Bild"
		return
	if rs.is_empty() or spec_order == 1:
		spec_shot = "field"
		spec_label = "Übersicht über das Spielfeld"
	elif spec_order == 3:
		spec_shot = "mw"
		spec_label = "So sieht MoveEye das Feld"
		spec_until = t + 5.0
	else:
		var p = rs[randi() % rs.size()]
		spec_who = int(p["slot"])
		var kinds := ["follow", "side", "low", "orbit", "follow"]
		spec_shot = kinds[randi() % kinds.size()]
		spec_orbit = randf() * TAU
		spec_label = {"follow": "Wir folgen %s", "side": "%s von der Seite", "low": "%s kommt näher …", "orbit": "Rund um %s"}[spec_shot] % p["name"]
	if game.last_minute:
		spec_until = min(spec_until, t + randf_range(3.0, 5.0))      # the last minute: quicker cuts


func _spectate(dt: float) -> void:
	if explore != null and explore.on and not (game != null and game.open and game.round_state in ["countdown", "play"] and game_mode != "free"):
		_spectate_explore(dt)                           # 3D-3.60: exploring (also with players moving freely)
		return
	if game == null or not game.open:
		spectate_stop()
		return
	var t := now()
	if game.round_state == "end":
		if spec_end_t == 0.0:
			spec_end_t = t
			spec_until = 0.0
		elif t - spec_end_t > 15.0:
			spectate_stop()                              # after the end: the camera stays where it is
			return
	elif game.round_state == "lobby":
		spectate_stop()
		return
	if t < spec_cut_until:
		pass                                                       # an event shot is running
	elif game.round_state == "play" and t - spec_switch_t > 2.0:      # somebody is about to be discovered: show it at once
		for p in _spec_runners():
			if float(p["susp"]) > 65.0 and not (spec_shot == "follow" and spec_who == int(p["slot"])):
				spec_until = 0.0
				break
	if t >= spec_until:
		_spec_choose(t)
	view_cam.fov = 62.0
	var want: Transform3D = view_cam.global_transform
	var who = game.players[spec_who] if spec_who >= 0 and spec_who < game.players.size() else null
	if spec_shot in ["side", "low", "orbit", "caught", "cheer"]:
		if who == null:
			spec_until = 0.0
			return
		var a2 = who["actor"]
		var hd: float = a2.heading
		var fw := Vector3(-sin(hd), 0, -cos(hd))
		var rt := Vector3(cos(hd), 0, -sin(hd))
		var c2: Vector3 = a2.position
		var pos2: Vector3
		var look2: Vector3 = c2 + Vector3(0, 0.9, 0)
		match spec_shot:
			"side":                                         # tracking shot from the side, at eye level
				pos2 = c2 + rt * 4.2 + Vector3(0, 1.3, 0)
				look2 = c2 + fw * 1.2 + Vector3(0, 0.8, 0)
				view_cam.fov = 55.0
			"low":                                          # low in front: the player comes towards the camera
				pos2 = c2 + fw * 5.5 + Vector3(0, 0.45, 0)
				view_cam.fov = 48.0
			"orbit":                                        # slowly round the player
				spec_orbit += dt * 0.45
				pos2 = c2 + Vector3(sin(spec_orbit) * 4.0, 2.0, cos(spec_orbit) * 4.0)
			_:                                              # caught / in the goal: close and quick round
				spec_orbit += dt * (1.1 if spec_shot == "caught" else 0.8)
				var r := 2.6 if spec_shot == "caught" else 3.2
				pos2 = c2 + Vector3(sin(spec_orbit) * r, 1.4, cos(spec_orbit) * r)
				view_cam.fov = 44.0 + 6.0 * sin(t * 2.0)       # a little zoom pulse
		pos2.y = max(pos2.y, ground_y(pos2.x, pos2.z) + 0.35)
		pos2 = _spec_free(pos2, look2)                 # 3D-3.60: the player stays visible
		want = Transform3D(Basis(), pos2).looking_at(look2, Vector3.UP)
		var k2: float = 1.0 - exp(-dt * (4.5 if spec_shot in ["caught", "cheer"] else 2.6))
		view_cam.global_transform = view_cam.global_transform.interpolate_with(want, k2)
		return
	var focus: Vector3 = game.goal
	var rs := _spec_runners()
	if spec_shot == "follow":
		var p = game.players[spec_who] if spec_who >= 0 and spec_who < game.players.size() else null
		if p == null or p["state"] != "play":
			spec_until = 0.0
			return
		var a = p["actor"]
		var back := Vector3(sin(a.heading), 0, cos(a.heading))
		var pos: Vector3 = a.position + back * 4.5 + Vector3(0, 2.6, 0)
		pos.y = max(pos.y, ground_y(pos.x, pos.z) + 1.5)
		pos = _spec_free(pos, a.position + Vector3(0, 0.9, 0))
		want = Transform3D(Basis(), pos).looking_at(a.position + Vector3(0, 0.9, 0) - back * 1.5, Vector3.UP)
	elif spec_shot == "goal":
		var to := Vector3(0, 0, 8)
		if spec_who >= 0 and spec_who < game.players.size() and game.players[spec_who] != null:
			to = game.players[spec_who]["actor"].position - game.goal
		to.y = 0
		if to.length() < 0.5:
			to = Vector3(0, 0, 8)
		var pos: Vector3 = game.goal - to.normalized() * 5.0 + Vector3(0, 2.4, 0)
		pos.y = max(pos.y, ground_y(pos.x, pos.z) + 1.5)
		want = Transform3D(Basis(), pos).looking_at(game.goal + to * 0.45 + Vector3(0, 0.8, 0), Vector3.UP)
	elif spec_shot == "mw":
		want = cams[0].global_transform
		view_cam.fov = 41.0
	elif spec_shot == "group":                           # 3D-3.60: middle and spread of all players, slowly round
		var mid := Vector3.ZERO
		for p in rs:
			mid += p["actor"].position
		mid = (mid / rs.size()) if not rs.is_empty() else game.goal * 0.5
		var spread := 2.0
		for p in rs:
			spread = max(spread, mid.distance_to(p["actor"].position))
		spec_orbit += dt * 0.07
		var dd: float = spread * 1.6 + 6.0
		var pos := mid + Vector3(sin(spec_orbit) * dd, dd * 0.55 + 2.0, cos(spec_orbit) * dd)
		pos.y = max(pos.y, ground_y(pos.x, pos.z) + 1.5)
		pos = _spec_free(pos, mid + Vector3(0, 0.6, 0))
		want = Transform3D(Basis(), pos).looking_at(mid + Vector3(0, 0.6, 0), Vector3.UP)
	else:                                                # the whole field: slowly round from above
		var c := Vector3.ZERO
		for p in rs:
			c += p["actor"].position
		c = (c / rs.size()) if not rs.is_empty() else (game.goal * 0.5)
		c = c.lerp(game.goal * 0.5, 0.4)
		spec_orbit += dt * 0.08
		var pos := c + Vector3(sin(spec_orbit) * 18.0, 0, cos(spec_orbit) * 18.0)
		pos.y = ground_y(pos.x, pos.z) + 16.0
		focus = c
		want = Transform3D(Basis(), pos).looking_at(c + Vector3(0, 0.5, 0), Vector3.UP)
	var k: float = 1.0 - exp(-dt * (6.0 if spec_shot == "mw" else 2.2))
	view_cam.global_transform = view_cam.global_transform.interpolate_with(want, k)


# ---- 3D-3.60: the spectator also for «Erkunden» (the rover and the players moving freely), and a free line of sight:
# a shot whose view is blocked by a caravan, a tent, a house turns round the target until it is free (or looks from above)
func _spec_free(pos: Vector3, at: Vector3) -> Vector3:
	if line_free(pos, at):
		return pos
	var off := pos - at
	var r := Vector2(off.x, off.z).length()
	var base := atan2(off.x, off.z)
	for k in [1, -1, 2, -2, 3, -3, 4]:
		var a: float = base + float(k) * PI / 4.0
		var q := at + Vector3(sin(a) * r, off.y, cos(a) * r)
		q.y = max(q.y, ground_y(q.x, q.z) + 0.4)
		if line_free(q, at):
			return q
	return at + Vector3(off.x * 0.3, max(off.y, 7.0), off.z * 0.3)      # nothing free: from above


func _spec_targets() -> Array:
	"""what the spectator can show while exploring: the rover and the players moving freely - [name, node, moving]"""
	var out := [["Mover", rig, abs(_pad_l) + abs(_pad_r) > 0.05]]
	if game != null:
		for p in game.players:
			if p != null and p["state"] == "play":
				out.append([str(p["name"]), p["actor"], float(p["actor"].cur_speed) > 0.2])
	return out


var _spx_who := 0


func _spectate_explore(dt: float) -> void:
	var t := now()
	var tg := _spec_targets()
	if t >= spec_until or _spx_who >= tg.size():
		spec_switch_t = t
		spec_until = t + randf_range(6.0, 9.0)
		var moving := []
		for i in range(tg.size()):
			if tg[i][2]:
				moving.append(i)
		_spx_who = moving[randi() % moving.size()] if not moving.is_empty() and randf() < 0.75 else randi() % tg.size()
		var kinds := ["chase", "side", "low", "orbit", "crane", "chase"]
		if tg.size() >= 2:
			kinds.append("group")
			kinds.append("group")
		if randf() < 0.12:
			kinds = ["mw"]
		spec_shot = kinds[randi() % kinds.size()]
		spec_orbit = randf() * TAU
		var nm: String = tg[_spx_who][0]
		spec_label = {"chase": "Wir folgen: %s", "side": "%s von der Seite", "low": "%s kommt näher …", "orbit": "Rund um %s",
				"crane": "%s von oben", "group": "Alle im Bild", "mw": "So sieht MoveEye das"}[spec_shot] % ([nm] if spec_shot not in ["group", "mw"] else [])
	view_cam.fov = 60.0
	var n: Node3D = tg[_spx_who][1]
	var c: Vector3 = n.global_position
	var hd: float = n.rotation.y if n == rig else float(n.heading)
	var fw := Vector3(-sin(hd), 0, -cos(hd))
	var rt := Vector3(cos(hd), 0, -sin(hd))
	var look := c + Vector3(0, 0.8, 0)
	var pos: Vector3
	match spec_shot:
		"mw":
			view_cam.global_transform = view_cam.global_transform.interpolate_with(cams[0].global_transform, 1.0 - exp(-dt * 6.0))
			view_cam.fov = 41.0
			return
		"side":
			pos = c + rt * 4.5 + Vector3(0, 1.3, 0)
			look = c + fw * 1.5 + Vector3(0, 0.7, 0)
			view_cam.fov = 52.0
		"low":
			pos = c + fw * 6.0 + Vector3(0, 0.45, 0)
			view_cam.fov = 46.0
		"orbit":
			spec_orbit += dt * 0.4
			pos = c + Vector3(sin(spec_orbit) * 4.5, 2.2, cos(spec_orbit) * 4.5)
		"crane":                                          # high and slowly round: where it goes
			spec_orbit += dt * 0.12
			pos = c + Vector3(sin(spec_orbit) * 9.0, 11.0, cos(spec_orbit) * 9.0)
		"group":                                          # everybody in the picture: middle and spread of all
			var mid := Vector3.ZERO
			for x in tg:
				mid += (x[1] as Node3D).global_position
			mid /= float(tg.size())
			var spread := 2.0
			for x in tg:
				spread = max(spread, mid.distance_to((x[1] as Node3D).global_position))
			spec_orbit += dt * 0.06
			var d: float = spread * 1.6 + 6.0
			pos = mid + Vector3(sin(spec_orbit) * d, d * 0.55 + 2.0, cos(spec_orbit) * d)
			look = mid + Vector3(0, 0.6, 0)
		_:
			pos = c - fw * 5.0 + Vector3(0, 2.6, 0)
			look = c + fw * 1.5 + Vector3(0, 0.6, 0)
	pos.y = max(pos.y, ground_y(pos.x, pos.z) + 0.4)
	pos = _spec_free(pos, look)
	var want := Transform3D(Basis(), pos).looking_at(look, Vector3.UP)
	view_cam.global_transform = view_cam.global_transform.interpolate_with(want, 1.0 - exp(-dt * 2.4))


# ---- with the phone simulator open (left), the map and the compass move to the right, the buttons are centred (3D-3.26) ----
var _hud_key := ""
var view_help: Control = null


var cpu_pill: Label = null
var _cpu_t := 0.0


func _build_cpu_pill(layer: CanvasLayer) -> void:
	_mod("menues")._build_cpu_pill(layer)


func _cpu_pill_tick(dt: float) -> void:
	if cpu_pill == null or mini_box == null:
		return
	_cpu_t -= dt
	if _cpu_t > 0.0:
		return
	_cpu_t = 1.0
	var o: Dictionary = mini_box.own
	var pc: float = float(o.get("pc", -1.0))
	var sm: float = float(o.get("sim", -1.0))
	cpu_pill.text = "PC-CPU %s  ·  Simulator %s" % ["–" if pc < 0 else "%d %%" % roundi(pc), "–" if sm < 0 else "%d %%" % roundi(sm)]
	cpu_pill.add_theme_color_override("font_color", Color(1.0, 0.45, 0.4) if pc > 85.0 else (Color(1.0, 0.8, 0.35) if pc > 60.0 else Color(0.85, 0.9, 0.95)))
	# top, in the middle of the 3D view (between the phone and the panel)
	var vw: float = get_viewport().get_visible_rect().size.x
	var right: float = ui_root.get_global_rect().position.x if ui_root != null and ui_root.visible else vw
	var left: float = phone.get_global_rect().end.x if phone != null and phone.visible else 0.0
	if fenster == null:                                   # Paket «Fenster»: the frame places it (fenster.gd)
		cpu_pill.reset_size()
		cpu_pill.position = Vector2((left + right - cpu_pill.size.x) / 2.0, 10.0)


func _hud_layout() -> void:
	_mod("menues")._hud_layout()


# ---- presets for the visitors (from 3D-3.38) ------------------------------------------------------------------------------
var visit_preset := ""


func apply_visit_preset(id: String) -> void:
	"""set «Von selbst» in one go: calm night, busy camping place, wildlife night, daily life, load test, nothing"""
	visit_preset = id
	for vp in VISIT_PRESETS:
		if vp[0] == id:
			auto_visitors = bool(vp[2])
			daily_life = bool(vp[3])
			mix = str(vp[4])
			visit_rate = float(vp[5])
			max_visitors = int(vp[6])
			preset_kinds = (vp[7] as Array).duplicate() if vp.size() > 7 else []
			next_auto = min(next_auto, now() + 3.0)
	# 3D-3.43: the change is seen at once - the visitors of before go, the time fits the template, the first ones come now
	if PRESET_HOUR.has(id):
		set_hour(float(PRESET_HOUR[id]))
	clear_visitors()
	if auto_visitors:
		var au: Array = Scenes.AUTO.get(scene, Scenes.AUTO["camping"])
		var kinds: Array = _mixed(au[0] if preset_kinds.is_empty() else preset_kinds).duplicate()
		kinds.shuffle()
		for i in range(mini(3 if id != "calm" else 1, kinds.size())):
			visit(str(kinds[i]))
		next_auto = now() + 4.0
	_settings_dirty = true
	_sync_ui()


func _test_scroll(y: float) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	(ui_box.get_parent() as ScrollContainer).get_v_scroll_bar().value = y


func _test_scroll_to(c: Control) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var sc := ui_box.get_parent() as ScrollContainer
	sc.get_v_scroll_bar().value += c.global_position.y - sc.global_position.y


# ---- night flyers (from 3D-3.39): bats round the light, an owl gliding past - typical false alarms at night ---------------
func _night_flyers(owl: bool) -> void:
	var root_ := Node3D.new()
	scene_parent.add_child(root_)
	var fw: Vector3 = -cams[0].global_transform.basis.z
	fw.y = 0.0
	fw = fw.normalized() if fw.length() > 0.01 else Vector3(0, 0, -1)
	var side_v := Vector3(-fw.z, 0, fw.x)
	var base: Vector3 = head.global_position + fw * randf_range(5.0, 9.0)
	var dark := mat(Color(0.12, 0.1, 0.09) if not owl else Color(0.5, 0.4, 0.3))
	var flyers := []
	for i in range(1 if owl else randi_range(3, 6)):
		var b := Node3D.new()
		root_.add_child(b)
		var span: float = 0.55 if owl else 0.16
		add_mesh(b, sph_mesh(0.12 if owl else 0.04, 0.3 if owl else 0.09), Vector3.ZERO, dark, 36.0)
		if owl:
			add_mesh(b, sph_mesh(0.09, 0.17), Vector3(0, 0.08, -0.12), dark, 36.0)
		var ws := []
		for sg in [-1, 1]:
			var w := Node3D.new()
			b.add_child(w)
			add_mesh(w, box(span, 0.012, span * 0.45), Vector3(span * 0.5 * sg, 0, 0), dark, 30.0)
			ws.append([w, sg])
		flyers.append([b, ws, randf() * TAU, randf_range(0.7, 1.4)])
	var t0 := now()
	var dur := 22.0 if not owl else 9.0
	var from := base - side_v * 25.0 + Vector3(0, 4.5, 0)
	var to := base + side_v * 25.0 + Vector3(0, 3.0, 0) + fw * randf_range(-3.0, 3.0)
	var hold := {"r": root_}
	var fly := func(_dt, t):
		var r = hold["r"]
		if r == null or not is_instance_valid(r):
			return true
		var f: float = (now() - t0) / dur
		for fl in flyers:
			var b: Node3D = fl[0]
			var p: Vector3
			if owl:
				p = from.lerp(to, f) + Vector3(0, sin(f * PI) * -1.5, 0)
				b.look_at_from_position(p, p + (to - from).normalized(), Vector3.UP)
				for w in fl[1]:
					w[0].rotation.z = w[1] * (0.5 * sin(t * 6.0) if fmod(t, 2.5) < 1.2 else 0.05)   # flaps, then glides
			else:
				var ph: float = t * fl[3] * 2.2 + fl[2]
				var away: float = clamp((f - 0.8) / 0.2, 0.0, 1.0) * 30.0
				p = base + side_v * (sin(ph) * 3.0 + sin(ph * 2.3) * 1.2 + away) + fw * (cos(ph * 1.3) * 2.0) + Vector3(0, 2.8 + sin(ph * 1.7) * 1.2 + away * 0.3, 0)
				var nx: Vector3 = p - b.position
				if nx.length() > 0.001:
					b.look_at_from_position(p, p + nx, Vector3.UP)
				else:
					b.position = p
				for w in fl[1]:
					w[0].rotation.z = w[1] * 0.9 * sin(t * 18.0 + fl[2])
		if f >= 1.0:
			hold["r"] = null
			flyers.clear()
			r.queue_free()
			return true
		return false
	anims.append(fly)


func sph_mesh(r: float, h: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = r
	m.height = h
	m.radial_segments = 10
	m.rings = 6
	return m


func control_set(id: String, v) -> Dictionary:
	return _mod("einstellungen").control_set(id, v)



# ---- 3D-3.83: makeover 8 + 9 -------------------------------------------------------------------------------------------
func whatif(d: Dictionary) -> Dictionary:
	"""«Was wäre wenn …?»: the situation of a real recording - same time, rain, the direction of the head, as many people
	(or an animal / a car) crossing the picture at about the same distance"""
	var _b := busy_with()
	if _b != "":
		return {"ok": false, "error": "busy: " + _b}
	auto_visitors = false                                  # 3D-3.88: only the visitors of the situation
	set_hour(clampf(float(d.get("hour", 12.0)), 0.0, 23.75))
	weather = str(d.get("weather", "clear"))
	_update_sky()
	var kind := str(d.get("kind", "person"))
	var n := clampi(int(d.get("n", 1)), 1, 4)
	var az := -rad_to_deg(rig.rotation.y) + float(d.get("pan_deg", 0.0))
	var dist := clampf(float(d.get("dist", 12.0)), 4.0, 30.0)
	var base: Vector3 = rig.global_position
	if kind == "car":
		car()
	else:
		for i in range(n):
			var dd := dist + i * 1.5
			var a: Vector3 = base + pos_of(az - 32.0, dd)
			var b: Vector3 = base + pos_of(az + 32.0, dd)
			if randf() < 0.5:
				var t := a
				a = b
				b = t
			get_tree().create_timer(i * 1.2).timeout.connect(func(): spawn(kind, Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z)))
	start_info = ("Was wäre wenn: %s nachgestellt (%02d:%02d, %s)" % [str(d.get("name", "Aufnahme")), int(hour()), int(fmod(hour(), 1.0) * 60), {"rain": "Regen"}.get(weather, "klar")])
	return {"ok": true, "kind": kind, "n": n, "az": snappedf(az, 0.1)}


func twin_info() -> Dictionary:
	var zs = mw.get("zones", [])
	var wp = mw.get("waypoints", [])
	return {"name": str(twin.get("name", "")), "place": place_label() if scene == "ort" else Scenes.name_of(scene), "scene": scene,
			"mast": snappedf(mast_h, 0.01), "zones": zs.size() if typeof(zs) == TYPE_ARRAY else 0, "waypoints": wp.size() if typeof(wp) == TYPE_ARRAY else 0,
			"lat": twin.get("lat", null), "lon": twin.get("lon", null)}



# ---- 3D-3.85: makeover 21 - the cause of a false alarm, re-enacted ------------------------------------------------------
func farecreate(d: Dictionary) -> Dictionary:
	var cause := str(d.get("cause", "other"))
	if cause == "end":
		if _fa_saved.has("wind"):
			wind = float(_fa_saved["wind"])
			gusts = bool(_fa_saved["gusts"])
		if _fa_saved.has("weather"):
			weather = str(_fa_saved["weather"])
			_update_sky()
		if _fa_saved.has("auto"):
			auto_visitors = bool(_fa_saved["auto"])
		_fa_saved = {}
		start_info = "Fehlalarm-Lernen fertig"
		return {"ok": true}
	if not _fa_saved.is_empty():
		return {"ok": false, "error": "already running"}  # 3D-3.88: a second call kept the changed weather as «original»
	var _b := busy_with()
	if _b != "":
		return {"ok": false, "error": "busy: " + _b}
	_fa_saved = {"wind": wind, "gusts": gusts, "weather": weather, "auto": auto_visitors}
	auto_visitors = false
	if d.has("hour"):
		set_hour(clampf(float(d["hour"]), 0.0, 23.75))
	if bool(d.get("rain", false)):
		weather = "rain"
		_update_sky()
	var az := -rad_to_deg(rig.rotation.y) + float(d.get("pan_deg", 0.0))
	var base: Vector3 = rig.global_position
	var a: Vector3 = base + pos_of(az - 30.0, 9.0)
	var b: Vector3 = base + pos_of(az + 30.0, 9.0)
	match cause:
		"animal":
			spawn("fox", Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z))
			get_tree().create_timer(20.0).timeout.connect(func(): spawn("cat", Vector3(b.x, 0, b.z), Vector3(a.x, 0, a.z)))
			get_tree().create_timer(38.0).timeout.connect(func(): spawn("deer", Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z)))
		"wind":
			wind = 75.0
			gusts = true
		"light":
			car()
			get_tree().create_timer(25.0).timeout.connect(func(): car())
			if surprise != null:
				surprise.start("glare")
		"rain":
			weather = "rain"
			_update_sky()
		"car":
			car()
			get_tree().create_timer(20.0).timeout.connect(func(): car())
	start_info = "Fehlalarm-Lernen: Ursache «%s» nachgestellt (60 s)" % cause
	return {"ok": true, "cause": cause}
