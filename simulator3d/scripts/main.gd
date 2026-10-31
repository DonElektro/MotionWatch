extends Node3D
## MoveEye 3D simulator - scenes: camping place, forest, car park, garden, funny place, wildlife watching (scenes.gd)
## The world, the cameras for MoveEye (head camera on the pan / tilt head, fixed camera, thermal camera),
## day and night, weather, lights, visitors, sensors, the window on the PC and the connection (net.gd).

const VERSION := "3D-4.84"
const TestrunS := preload("res://scripts/testrun.gd")    # 3D-3.90: plan names and times for the card «Testen»
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
var abenteuer                         # bergtal_abenteuer.gd: Bergtal-Abenteuer «Die Karte des Bergführers» (Rucksack, Tour, Nacht, Morgen)
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
var game_minutes := 3.0                # 3D-4.x: short rounds (Spielkonzept Daniel, before 5)
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
var grafik_mode := "auto"             # 3D-4.25: «Grafik-Modus» auto | lite | normal (quality.gd; later «hoch»)
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
var umgebung                          # umgebung.gd (3D-4.x): lamps, puddles, smoke, insects, plants, tracks, robots, pets
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


func _ready() -> void:
	if Updater.old_name_forward():               # 3D-4.24: started as MotionWatch3D.exe - MoveEyeSim3D.exe takes over
		get_tree().quit()
		return
	preload("res://scripts/werk.gd").apply_pending()    # Werksrücksetzung: right after the restart, before anything reads user://
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
	DisplayServer.window_set_title("3D-Simulator Live · %s" % VERSION)
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
	statusled = preload("res://scripts/statusled.gd").new()   # Status-LED auf dem Kopf, Tasten «Schutz» / «Alarm quittieren»
	statusled.main = self
	add_child(statusled)
	smalltv = preload("res://scripts/smalltv.gd").new()     # 3D-4.19: virtueller SmallTV (gleiche HTTP-Schnittstelle, Kachel im Fenster)
	smalltv.main = self
	add_child(smalltv)
	parcours = preload("res://scripts/parcours.gd").new()   # 3D-4.18: the tracking parcours (scene «parcours»)
	parcours.main = self
	add_child(parcours)
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
	umgebung = preload("res://scripts/umgebung.gd").new()     # 3D-4.x: the surroundings like real (every part can be switched off)
	umgebung.main = self
	add_child(umgebung)
	menschen = preload("res://scripts/menschen.gd").new()     # P10 «Menschen-Verhalten»: gaits, variety, groups, daily routine, scenario API
	menschen.main = self
	add_child(menschen)
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
		add_child(up)
		await up.check(VERSION, update_url)
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
	DisplayServer.window_set_title("3D-Simulator Live · %s (Port %d)" % [VERSION, port])
	_fps0 = Engine.max_fps
	mini_box = preload("res://scripts/mini.gd").new()      # minimize = small box, the simulator keeps drawing
	mini_box.main = self
	add_child(mini_box)
	_restore_window(args)
	if OS.get_environment("MWSIM_PRINT_RESTART") == "1":         # only for tests: which options an update restart would pass on
		get_tree().create_timer(5.0).timeout.connect(func(): print("RESTART_ARGS: ", " ".join(restart_args())))
	set_process(true)
	set_process_unhandled_input(true)


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
	release_ports()
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
	"""3D-4.26: measure how the renderer stores colours (a ramp 128 … 255 in a 16 × 8 picture: linear, sRGB, squeezed?) and
	build th_inv; then check with a surface of exactly 20 °C"""
	var vp := SubViewport.new()
	vp.size = Vector2i(16, 16)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(vp)
	var cam := Camera3D.new()
	cam.cull_mask = 8
	cam.environment = th_env
	vp.add_child(cam)
	cam.global_transform = Transform3D(Basis(), Vector3(0, -500, 3))
	var rq := MeshInstance3D.new()                       # the ramp: pixel x + 16 y shows 128 + that (written like the code)
	rq.mesh = box(40, 40, 0.1)
	var rs := Shader.new()
	rs.code = "shader_type spatial;\nrender_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;\nuniform float srgb = 0.0;\n" + \
			"void fragment() { vec3 c = vec3(min(255.0, 128.0 + floor(FRAGCOORD.x) + 16.0 * floor(FRAGCOORD.y)) / 255.0);\n" + \
			"if (srgb > 0.5) { c = mix(c / 12.92, pow((c + vec3(0.055)) / 1.055, vec3(2.4)), step(vec3(0.04045), c)); }\nALBEDO = c; }"
	var rm := ShaderMaterial.new()
	rm.shader = rs
	rq.material_override = rm
	rq.layers = 8
	add_child(rq)
	rq.global_position = Vector3(0, -500, 0)
	var bg_was := th_env.background_color
	_make_lut(false)
	var ok := false
	for srgb in [false, true]:
		rm.set_shader_parameter("srgb", 1.0 if srgb else 0.0)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var ri := vp.get_texture().get_image()
		if ri == null or ri.is_empty():
			break
		var inv := PackedInt32Array()
		inv.resize(256)
		inv.fill(-1)
		var distinct := true
		for k in range(128):
			var st := roundi(ri.get_pixel(k % 16, k / 16).r * 255.0)
			if inv[st] >= 0:
				distinct = false
			inv[st] = 128 + k
		if distinct:
			var last := 128
			for b2 in range(256):                         # bytes the ramp never gave: the nearest below (or 128)
				if inv[b2] >= 0:
					last = inv[b2]
				else:
					inv[b2] = last
			th_inv = inv
			_make_lut(srgb)
			ok = true
			break
	rq.queue_free()
	var q := MeshInstance3D.new()                        # the check: 20 °C in the middle, background in the corners
	q.mesh = box(4, 4, 0.1)
	q.material_override = tmat_fixed(20.0)
	q.layers = 8
	add_child(q)
	q.global_position = Vector3(0, -500, 0)
	q.scale = Vector3(0.5, 0.5, 1)
	th_env.background_color = Color(0.25, 0.25, 0.25)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img != null and not img.is_empty():
		var rb := img.get_pixel(0, 0).r                 # background colour 0.25 comes back as ...
		th_bg_raw = abs(rb - 0.25) < 0.04
		var got := _th_read(img, 8, 8)
		print("thermal calibration: 20.00 °C -> %.2f °C (%s%s), background %.3f -> %s" % [got, "sRGB" if th_srgb else "linear",
				"" if ok else ", ramp not clean", rb, "raw" if th_bg_raw else "converted"])
	th_env.background_color = bg_was
	q.queue_free()
	vp.queue_free()


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
	get_tree().create_timer(dist / 340.0).timeout.connect(func(): add_sound(30.0, dir * dist, 2.5))
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
	"""a quad right in front of camera 0 and 1 (own layer 32 / 64): grain, dark corners, raindrops (shaders/lens.gdshader).
	Insects round the head at night when a light is on (CPU particles, only the normal cameras see them, not the thermal one)."""
	var sh: Shader = load("res://shaders/lens.gdshader")
	for i in range(2):
		var cam: Camera3D = cams[i]
		var lay := 32 if i == 0 else 64
		cam.cull_mask = 1 | lay
		var dist := 0.12
		var w := 2.0 * dist * tan(deg_to_rad(CAM_FOV[i]) / 2.0) * 1.04
		var hgt := w * float(CAM_H[i]) / float(CAM_W[i]) * 1.04
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(w, hgt)
		q.mesh = qm
		q.position = Vector3(0, 0, -dist)
		q.layers = lay
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var m := ShaderMaterial.new()
		m.shader = sh
		m.set_shader_parameter("res", Vector2(CAM_W[i], CAM_H[i]))
		q.material_override = m
		cam.add_child(q)
		lens_mats.append(m)
		var eq := MeshInstance3D.new()                       # exposure: a bit behind the lens quad, so it is drawn first
		var eqm := QuadMesh.new()
		eqm.size = Vector2(w, hgt) * 1.05
		eq.mesh = eqm
		eq.position = Vector3(0, 0, -dist * 1.05)
		eq.layers = lay
		eq.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var em := ShaderMaterial.new()
		em.shader = load("res://shaders/expo.gdshader")
		eq.material_override = em
		cam.add_child(eq)
		expo_mats.append(em)
		var fq := MeshInstance3D.new()                       # 3D-3.94: the camera effects - between exposure and lens (drawn in that order)
		var fqm := QuadMesh.new()
		fqm.size = Vector2(w, hgt) * 1.02
		fq.mesh = fqm
		fq.position = Vector3(0, 0, -dist * 1.02)
		fq.layers = lay
		fq.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var fm := ShaderMaterial.new()
		fm.shader = load("res://shaders/camfx.gdshader")
		fm.set_shader_parameter("res", Vector2(CAM_W[i], CAM_H[i]))
		fq.material_override = fm
		cam.add_child(fq)
		camfx_mats.append(fm)
	insects = CPUParticles3D.new()
	insects.amount = 28
	insects.lifetime = 2.5
	insects.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	insects.emission_sphere_radius = 0.7
	insects.direction = Vector3(0, 0, -1)
	insects.spread = 180.0
	insects.gravity = Vector3.ZERO
	insects.initial_velocity_min = 0.3
	insects.initial_velocity_max = 1.4
	insects.orbit_velocity_min = -1.5
	insects.orbit_velocity_max = 1.5
	insects.damping_min = 0.0
	insects.damping_max = 0.8
	insects.angular_velocity_min = -200.0
	insects.angular_velocity_max = 200.0
	var im := SphereMesh.new()
	im.radius = 0.012
	im.height = 0.02
	im.radial_segments = 4
	im.rings = 2
	var imm := StandardMaterial3D.new()
	imm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	imm.albedo_color = Color(0.95, 0.93, 0.85)
	im.material = imm
	insects.mesh = im
	insects.position = Vector3(0, 0.2, -0.9)          # in front of the head, in its light
	insects.emitting = false
	insects.layers = 1
	head_pitch.add_child(insects)


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
	var wl_on: bool = L.get("white", false) or (game != null and game.now() < game.flash_until)
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
	capturing = true
	last_cap[i] = now()
	var L: Dictionary = mw.get("lights", {})
	var dark := is_dark()
	ir_light.spot_range = ir_range
	ir_light.light_energy = 9.0 if (i == 0 and ir_on()) else 0.0   # infrared: only the NoIR camera sees it
	if i == 0:
		var grey: bool = ir_on() and dark and not white_light.light_energy > 0.0   # infrared picture: black and white
		cams[0].environment = (night_envs[0] if grey else night_envs[1]) if dark and night_envs[0] != null else null
	if i == 1:
		cams[1].environment = night_envs[1] if dark and night_envs[1] != null else null    # little light: little colour
	if i < 2 and expo_mats.size() > i:
		var ex: float = NIGHT_SCALE * gain[i] if dark else 1.0
		if i == 0 and dark and ir_on() and not white_light.light_energy > 0.0:
			ex = ir_ex                           # 3D-4.1: the infrared picture has its own exposure (before: fixed 0.85 - almost white)
		expo_mats[i].set_shader_parameter("expo", ex)
		lens_mats[i].set_shader_parameter("expo", ex)
	if i < 2:
		cam_attr[i].exposure_multiplier = gain[i] if not dark else 1.0   # at night the lens shader does the exposure
		if realism != null:
			realism.before_capture(i)
		if simreal != null:
			simreal.before_capture(i)            # 3D-4.4: lens, rolling shutter, noise, infrared, reflectors
		weit.before_capture(i)                   # 3D-4.17: NoIR Wide - infrared picture, fisheye, the wide infrared light
		if zwilling != null and zwilling.fm != null:
			zwilling.fm.before_capture(i)        # 3D-4.27: Foto-Modus - the camera sees the real photo, the figures are fitted to it
		if wetter != null:
			wetter.before_capture(i)             # real-wetter: drops and fog on the lens, ground fog
		if camphys != null:
			camphys.before_capture(i)            # 3D-4.x P1: last - exposure time, gain, sensor noise, NoIR colours
	vps[i].render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var img: Image = vps[i].get_texture().get_image()
	ir_light.light_energy = 0.0
	weit.after_capture(i, img)
	if img != null and not img.is_empty():
		if i < 2:
			_auto_exposure(i, img)
			if realism != null:
				realism.after_capture(i, img)
			var hold := false
			if cond["net"] and i == 0:                   # 3D-3.74: bad Wi-Fi - pictures get lost, sometimes it stands still
				if now() < _net_hold:
					hold = true
				elif randf() < 0.05:
					_net_hold = now() + randf_range(0.8, 2.5)
					hold = true
				elif randf() < 0.3:
					hold = true
			if not hold:
				jpgs[i] = img.save_jpg_to_buffer(realism.jpg_q if realism != null and realism.fx_on else 0.8)
				frame_no[i] += 1
				if simreal != null:
					simreal.on_jpg(i, jpgs[i])           # 3D-4.4: «Wie ein echter Pi 5» - the picture comes late
		else:
			_decode_thermal(img)
	capturing = false


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
	r["buttons"] = statusled.reply() if statusled != null else null   # die Tasten des Geräts wie ein GPIO (MoveEye 163a)
	r["horror"] = horror.reply() if horror != null else null   # Horror-Modus: neue «Aufnahmen» -> MoveEye Verlauf (539a)
	r["spieltest"] = spieltest.reply() if spieltest != null else null   # Spieltest-Assistent: Meldung nach jeder Runde -> MoveEye 635a (Push)
	r["sky"] = licht.reply() if licht != null else null   # «Licht & Nacht»: lux am Gerät, Dämmerung, Sonne, Mond (MoveEye liest es noch nicht)
	r["season"] = jahreszeiten.reply() if jahreszeiten != null else null   # «Jahreszeiten»: Jahreszeit, Sonnenauf-/untergang, Belegung (MoveEye liest es noch nicht)
	if simwerte != null:
		r.merge(simwerte.reply())                     # Simulator-Werte: battery, pi_temp, net, clock, place, forecast (power.gd)
	return r


var schnitt = null                     # schnittstelle.gd (Aufräumen 2)
var maggie = null                      # maggie_story.gd: «Maggie und der Bergkristall» (API für maggie_hund / maggie_gefahr)
var horror = null                      # bergtal_horror.gd: Bergtal · Horror-Modus (Hook für die Stimmungswahl: horror.mood_slot / open_from_mood)
var spieltest = null                   # spieltest.gd: Spieltest-Assistent (Haken für Spiele: Spieltest.ereignis(modus, art, daten))
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
	return {"v": 1, "name": "MoveEye Sim · 3D %s" % VERSION, "host": host_name(),
			"cameras": [{"id": 0, "name": "Head camera (NoIR)", "w": CAM_W[0], "h": CAM_H[0], "fps": CAM_FPS[0], "fov_h": CAM_FOV[0], "fov_v": 41.0, "on_head": true, "noir": true},
						weit.cam_info()],          # 3D-4.17: the wide camera with its mount (weitwinkel.gd)
			"thermal": simint.thermal_info() if simint != null else {"w": TH_W, "h": TH_H, "fps": th_fps, "fov_h": TH_FOV, "fov_v": 35.0, "unit": "C", "on_head": true},
			"view": {"input": 1, "path": "/view.mjpg", "padview": 1},
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
			if kk != "" and (jahreszeiten == null or jahreszeiten.accept_visit(kk, PEOPLE_KINDS)):   # «Jahreszeiten»: campsite by season
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
	var st = setter
	if setter != null and type != "button":
		st = func(v):                                 # a changed setting is saved (a few seconds later)
			setter.call(v)
			_settings_dirty = true
	controls.append({"type": type, "id": id, "label": label, "group": group, "get": getter, "set": st, "extra": extra})


# ---- order of the settings: groups with a symbol, parts inside (from 3D-3.5) ------------------------------------------------
# [group, symbol (window: drawn; page of MoveEye: emoji), parts in their order]
const GROUPS := [["Szene", "globe", "🌍", ["", "Bergtal", "Ort von der Karte", "Foto des Platzes", "Zeit", "Licht & Nacht"]],
		["Wetter", "cloud", "🌦", ["", "Mehr Wetter", "Natur und Wind"]],
		["Besuch", "person", "🚶", ["Vorlagen", "Besucher hinsetzen", "Menschen schicken", "Tiere schicken", "Fahrzeuge", "Abläufe", "Von selbst", "Verhalten"]],
		["Kamerabild", "lens", "👁", ["", "Weitwinkel-Kamera", "Wärmebild", "Wie echt", "Schwierige Bedingungen", "Feineinstellungen"]],
		["Sensoren", "bell", "🔔", ["", "Bewegungsmelder (PIR)", "Strom", "Netz", "Zusatz-Bildschirm (SmallTV)"]],
		["Mover", "track", "🚜", ["", "Patrouille", "Controller"]],
		["Licht & Ton", "sun", "💡", ["", "Status-LED & Tasten", "Lautsprecher", "Mikrofon", "Umgebungsgeräusche"]],      # 3D-4.22: «Lautsprecher» here like MoveEye (was «Sensoren»)
		["Spiel", "pad", "🎮", ["", "Entdecken", "Assistent"]],        # Erlebniswelt 20–23: «Entdecken» (entdecken.gd) on the card
		["Wildtier", "target", "🎯", [""]],
		["Testen", "check", "✅", ["", "Verfolgungs-Parcours", "Störungen", "Einbruch-Abläufe"]],
		["System", "gear", "⚙", ["Grafik", "Start mit dem PC", "Updates", "Sicherheit / Benutzer"]],
		["Entwickler", "tools", "🧪", ["", "Updates"]]]
# 3D-4.21 (Menü 2, Daniel 30.10.2026): the same names as MoveEye - the controls keep their old group / part in add_control,
# _order_controls renames them here (MoveEye reads the fixed «gid», not the name)
const GROUP_RENAME := {"Testlauf": "Testen", "Wildbeobachtung": "Wildtier"}
const SUB_RENAME := {"Akku und Strom": "Strom", "Netz-Ausfall testen": "Netz", "Zusatz-Bildschirm": "Zusatz-Bildschirm (SmallTV)", "Kinder-Modus": "Sicherheit / Benutzer"}
# 3D-4.21: what only the developer needs (like the group «Entwickler» of MoveEye) - always «Experte»
# Paket «Entwickler zusammenlegen» (Daniel 31.10.2026): «dev_open» is the only entry of the card in the panel (opens the window
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
		"flee_sound": ["Besuch", "Verhalten"], "avoid_on": ["Besuch", "Verhalten"], "lens_vignette": ["Kamerabild", "Feineinstellungen"],
		"sound_on": ["Kamerabild", "Feineinstellungen"], "game_open": ["Spiel", "Runde"], "game_start": ["Spiel", ""],
		"game_stop": ["Spiel", ""], "game_wizard": ["Spiel", ""], "tv_mode": ["Spiel", "Anzeige"], "game_minutes": ["Spiel", "Runde"], "game_mode": ["Spiel", "Runde"], "game_goal": ["Spiel", "Runde"],
		"game_level": ["Spiel", "Regeln"], "game_glevel": ["Spiel", "Regeln"], "game_real": ["Spiel", "Regeln"], "game_lives": ["Spiel", "Regeln"], "game_items": ["Spiel", "Regeln"], "game_teams": ["Spiel", "Regeln"],
		"game_rescue": ["Spiel", "Regeln"], "game_teamgoal": ["Spiel", "Regeln"], "game_stones": ["Spiel", "Regeln"], "game_powers": ["Spiel", "Regeln"], "game_spectate": ["Spiel", "Anzeige"], "game_photos": ["Spiel", "Extras"], "game_fx_laser": ["Spiel", "Treffer"], "game_fx_paint": ["Spiel", "Treffer"], "game_fx_flash": ["Spiel", "Treffer"], "game_tap": ["Spiel", "Treffer"],
		"game_learn_miss": ["Spiel", "Erkennung lernen"], "game_learn_report": ["Spiel", "Erkennung lernen"], "game_learn_paths": ["Spiel", "Erkennung lernen"], "game_blind_bonus": ["Spiel", "Erkennung lernen"], "game_report_send": ["Spiel", "Erkennung lernen"], "game_hides": ["Spiel", "Extras"], "game_decoy": ["Spiel", "Extras"],
		"game_night": ["Spiel", "Extras"], "game_events": ["Spiel", "Extras"], "game_checkpoints": ["Spiel", "Extras"], "game_tasks": ["Spiel", "Extras"], "game_autohandicap": ["Spiel", "Extras"],
		"game_board_reset": ["Spiel", "Extras"], "spectate_now": ["Spiel", "Anzeige"], "game_noise": ["Spiel", "Regeln"],
		"game_random": ["Spiel", "Regeln"], "game_guard": ["Spiel", "Regeln"], "game_cones": ["Spiel", "Anzeige"], "game_quality": ["Spiel", "Anzeige"], "game_max": ["Spiel", "Runde"],
		"grafik_mode": ["System", "Grafik"], "quality": ["System", "Grafik"], "grafik_dof": ["System", "Grafik"], "view_scale": ["System", "Grafik"], "win_fps": ["System", "Grafik"], "auto_perf": ["System", "Grafik"], "map_on": ["System", "Ansicht"], "live_on": ["System", "Ansicht"], "live_cam": ["System", "Ansicht"], "live_size": ["System", "Ansicht"], "eco_idle": ["System", "Grafik"], "autostart": ["System", "Start mit dem PC"],
		"autostart_min": ["System", "Start mit dem PC"], "autostart_mwpc": ["System", "Start mit dem PC"], "autostart_lock": ["System", "Start mit dem PC"],
		"cond_glare": ["Kamerabild", "Schwierige Bedingungen"], "cond_drops": ["Kamerabild", "Schwierige Bedingungen"],
		"cond_web": ["Kamerabild", "Schwierige Bedingungen"], "cond_headlights": ["Kamerabild", "Schwierige Bedingungen"],
		"cond_shadows": ["Kamerabild", "Schwierige Bedingungen"], "cond_ir": ["Kamerabild", "Schwierige Bedingungen"],
		"autologon": ["System", "Start mit dem PC"], "kids_scary": ["System", "Sicherheit / Benutzer"], "kids_thief": ["System", "Sicherheit / Benutzer"], "kids_laser": ["System", "Sicherheit / Benutzer"], "kids_sound": ["System", "Sicherheit / Benutzer"], "kids_ask": ["System", "Sicherheit / Benutzer"], "auto_update": ["System", "Updates"], "update_mode": ["System", "Updates"], "dev_updates": ["Entwickler", "Updates"], "news_popup": ["System", "Updates"], "news_show": ["System", "Updates"], "update_now": ["System", "Updates"]}


const SIMPLE_GROUPS := ["Szene", "Wetter", "Besuch", "Testen", "Spiel"]
# 3D-4.7 («Spiel-Karte schlank», Daniel): the card «Spiel» = Assistent öffnen, Start, Stopp and the state line; every other
# setting of the game is only in the assistant (gamewiz.gd). Those controls stay (control API, saved settings) but get
# extra «wiz»: not in this panel and not in the Simulator control of MoveEye.
const GAME_MAIN := ["game_wizard", "game_start", "game_stop"]
# Erlebniswelt 20–23 (entdecken.gd): the part «Entdecken» stays on the card «Spiel» (not in the assistant); the first three in «Einfach»
const DISC_IDS := ["disc_book", "disc_photo", "disc_hints", "disc_hint_min", "disc_demo", "disc_seek", "fp_task_kind", "fp_task_velo", "fp_task_zelt"]
const DISC_SIMPLE := ["disc_book", "disc_photo", "disc_hints"]
# 3D-4.7: a fixed id per group for MoveEye (the visible names may change); sent as «gid» with every control
const GROUP_IDS := {"Szene": "scene", "Wetter": "weather", "Besuch": "visit", "Kamerabild": "camera", "Sensoren": "sensors", "Mover": "mover", "Licht & Ton": "lightsound",
		"Spiel": "game", "Wildtier": "wildlife", "Testen": "testrun", "System": "system", "Entwickler": "dev"}
const SIMPLE_HIDE_SUBS := ["Besucher hinsetzen", "Menschen schicken", "Tiere schicken", "Fahrzeuge", "Verhalten", "Mehr Wetter", "Natur und Wind"]


func _simple_ok(c: Dictionary) -> bool:
	"""3D-3.90: what «Einfach» shows - scene, time, weather, visitors (the inventory picks the single ones), the test run and
	the game assistant; everything else is «Experte»"""
	if c.group == "Spiel":
		return c.id in GAME_MAIN or c.id in DISC_SIMPLE
	if c.id == "mast_h":
		return true                                   # 3D-4.x: the height of the pole - easy to find (wish of Daniel)
	if c.group == "System":
		return c.id in ["update_mode", "kids_ask", "grafik_mode"]
	if not c.group in SIMPLE_GROUPS:
		return false
	return not str(c.extra.get("sub", "")) in SIMPLE_HIDE_SUBS


func _order_controls() -> void:
	"""every setting into its group and part, sorted like GROUPS (the window and the page of MoveEye show this order)"""
	var gi := {}
	for i in range(GROUPS.size()):
		gi[GROUPS[i][0]] = i
	var keyed := []
	for i in range(controls.size()):
		var c: Dictionary = controls[i]
		c.extra = c.extra.duplicate()                     # several controls share one dictionary ({"expert": true})
		var pl = PLACE.get(c.id, null)
		if pl == null and str(c.id).begins_with("spawn_"):
			pl = ["Besuch", "Menschen schicken" if str(c.id).trim_prefix("spawn_") in PEOPLE_KINDS else "Tiere schicken"]
		if VISIT_EMOJI.has(str(c.id).trim_prefix("spawn_")):
			c.extra["emoji"] = VISIT_EMOJI[str(c.id).trim_prefix("spawn_")]      # a picture on the button of the page (3D-3.38)
		if pl != null:
			c.group = pl[0]
			c.extra["sub"] = pl[1]
		c.group = GROUP_RENAME.get(c.group, c.group)       # 3D-4.21: names like MoveEye
		if SUB_RENAME.has(str(c.extra.get("sub", ""))):
			c.extra["sub"] = SUB_RENAME[str(c.extra.get("sub", ""))]
		if c.id in DEV_IDS:
			c.extra["sub"] = "Updates" if c.id == "dev_updates" else ""
		if c.group == "Spiel":                            # 3D-4.7: only open / start / stop on the card, the rest in the assistant
			if c.id in DISC_IDS:
				c.extra["sub"] = "Entdecken"           # Erlebniswelt 20–23: its own part on the card
			elif c.id in GAME_MAIN:
				c.extra["sub"] = ""                    # straight on the card (no part «Runde» any more)
			else:
				c.extra["wiz"] = true
				c.extra["sub"] = "Assistent"
		c.extra["gid"] = GROUP_IDS.get(c.group, str(c.group).to_lower())
		if not _simple_ok(c):
			c.extra["expert"] = true                      # 3D-3.90: «Einfach» = about 60 settings (the page of MoveEye has the same switch, stored in MoveEye «sim»)
		var g: int = gi.get(c.group, GROUPS.size())
		var sub := str(c.extra.get("sub", ""))
		c.extra["icon"] = GROUPS[g][2] if g < GROUPS.size() else ""
		c.extra["iconk"] = GROUPS[g][1] if g < GROUPS.size() else ""          # the drawn symbol (page of MoveEye from 2.93.16)
		var si: int = (GROUPS[g][3] as Array).find(sub) if g < GROUPS.size() else 0
		keyed.append([g * 1000 + max(si, 0) * 100, i, c])
	keyed.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	controls = keyed.map(func(k): return k[2])
	# 3D-4.21 (Menü 2, like MoveEye): «Einfach» = the main switch of every group - a group without one gets its first switch
	var has_main := {}
	for c in controls:
		if not c.extra.get("expert", false) and not c.extra.get("hide", false) and not c.extra.get("wiz", false):
			has_main[c.group] = true
	for c in controls:
		if has_main.has(c.group) or c.group in ["Entwickler", "Spiel"] or c.extra.get("hide", false) or c.extra.get("wiz", false):
			continue
		if c.type in ["toggle", "select", "button"]:
			c.extra.erase("expert")
			has_main[c.group] = true


func _register_controls() -> void:
	"""every setting of the simulator - for the window and for the web page of MoveEye (CONTROL protocol).
	extra "expert": true = only shown with «Experte» - in the window and on the page of MoveEye (its switch Einfach / Experte
	is stored in the settings of MoveEye, page «sim», like on its main page)."""
	var sc := []
	for s in Worlds.SHOWN:                        # 3D-4.x Welten: only the worlds and the tools (the old scenes are places in them)
		sc.append([s, Scenes.name_of(s)])
	var ex := {"expert": true}
	add_control("select", "scene", "Szene", func(): return Worlds.world_of(scene), func(v): set_scene(v), "Szene", {"options": sc})
	for w in Worlds.WORLDS:                       # «Ort in dieser Welt»: the old scenes of this world (one select per world)
		add_control("select", "welt_ort_" + w, "Ort in dieser Welt", func(): return scene if Worlds.is_place(scene) else "",
				func(v): set_scene(str(v) if str(v) != "" else w), "Szene", {"options": Worlds.place_options(w)})
		controls[-1]["only"] = func(): return Worlds.world_of(scene) == w
	add_control("toggle", "welt_solo", "Alte Szenen allein laden (ohne Welt drumherum – für Prüfstand-Vergleiche)", func(): return welt_solo,
			func(v): welt_solo = bool(v); set_scene(scene), "Szene", {"expert": true})
	add_control("button", "home_edit", "Mein Zuhause bauen (Baukasten mit der Maus)", null, func(): home_editor.open(true), "Szene")
	add_control("select", "fp_spot", "Standort im Ferienpark am See", func(): return fp_spot, func(v): set_fp_spot(str(v)), "Szene",
			{"options": preload("res://scripts/ferienpark.gd").spot_options()})
	controls[-1]["only"] = func(): return scene == "ferienpark"   # 3D-4.28: only shown in its scene (window and MoveEye; not in a place of the park)
	var Bt = preload("res://scripts/bergtal.gd")
	add_control("select", "bt_spot", "Schlafplatz im Bergtal", func(): return bt_spot, func(v): set_bt("bt_spot", str(v)), "Szene", {"options": Bt.spot_options()})
	add_control("select", "bt_bed", "Übernachten im Bergtal", func(): return bt_bed, func(v): set_bt("bt_bed", str(v)), "Szene", {"options": Bt.BEDS})
	var mo := []
	for k in Bt.MOUNTS:
		mo.append([k, Bt.MOUNTS[k][0]])
	add_control("select", "bt_mount", "MoveEye-Halterung am Schlafplatz (Bergtal)", func(): return bt_mount, func(v): set_bt("bt_mount", str(v)), "Szene", {"options": mo})
	add_control("select", "bt_bag", "Schlafsack (Bergtal)", func(): return bt_bag, func(v): set_bt("bt_bag", str(v)), "Szene", {"options": [["sommer", "Sommerschlafsack"], ["winter", "Winterschlafsack"]], "expert": true})
	add_control("toggle", "bt_stove", "Kocher am Schlafplatz (Bergtal)", func(): return bt_stove, func(v): set_bt("bt_stove", bool(v)), "Szene", {"expert": true})
	add_control("toggle", "bt_wall", "Windschutzmauer aus Steinen bauen (Bergtal)", func(): return bt_wall, func(v): set_bt("bt_wall", bool(v)), "Szene")
	add_control("select", "bt_orient", "Orientierung im Bergtal", func(): return bt_orient, func(v): set_bt("bt_orient", str(v)), "Szene",
			{"options": [["leicht", "leicht (Karte, Kompass, eigener Standort)"], ["mittel", "mittel (Karte und Kompass)"], ["schwer", "schwer (nur Wegweiser)"]], "expert": true})
	add_control("text", "bt_mark", "Eigene Markierung auf der Karte (Name; wird in der Bildmitte gesetzt)", func(): return "", func(v): bt_mark(str(v)), "Szene", {"expert": true})
	add_control("button", "bt_here", "Hier übernachten (Bergtal: der Platz in der Bildmitte oder beim Rover)", null, func(): bt_here(), "Szene")
	add_control("select", "bt_goto", "Schnellreise im Bergtal (Ort wählen)", func(): return "", func(v): bt_goto(str(v)), "Szene", {"options": Bt.place_options()})
	add_control("select", "bt_season", "Jahreszeit im Bergtal", func(): return bt_season, func(v): set_bt("bt_season", str(v)), "Szene",
			{"options": [["auto", "nach dem Monat (Jahreszeit)"], ["fruehling", "Frühling"], ["sommer", "Sommer"], ["herbst", "Herbst (Lärchen gelb, Nebel)"], ["winter", "Winter (Schnee, Eis)"]]})
	add_control("button", "bt_ride", "Mit der Materialseilbahn fahren (Bergtal)", null, func(): _bt_do("ride"), "Szene", {"expert": true})
	add_control("button", "bt_morning", "Wie gut war dein Platz? (Bergtal: Bewertung jetzt)", null, func(): _bt_do("morning"), "Szene", {"expert": true})
	# 3D-4.40: Horror-Modus «Das Hospiz» opens from the 5th mood of the Bergtal adventure (bergtal_abenteuer.gd), no button here
	add_control("toggle", "bt_events", "Bergtal: Ereignisse von selbst (Steinschlag, Fremder, Tier am Proviant, Wetterumschwung)", func(): return bt_events, func(v): bt_events = bool(v), "Besuch", {"sub": "Von selbst"})
	add_control("button", "bt_ev_rockfall", "Steinschlag (Bergtal)", null, func(): _bt_do("rockfall"), "Besuch", {"sub": "Abläufe"})
	add_control("button", "bt_ev_stranger", "Fremder am Rucksack (Bergtal)", null, func(): _bt_do("stranger"), "Besuch", {"sub": "Abläufe"})
	add_control("button", "bt_ev_food", "Tier am Proviant (Bergtal)", null, func(): _bt_do("fox_food"), "Besuch", {"sub": "Abläufe"})
	add_control("button", "bt_ev_storm", "Gewitter zieht auf (Bergtal)", null, func(): _bt_do("storm"), "Wetter", {"sub": "Mehr Wetter"})
	add_control("button", "bt_ev_fog", "Nebel kommt schnell (Bergtal)", null, func(): _bt_do("fog"), "Wetter", {"sub": "Mehr Wetter"})
	add_control("button", "bt_ev_fogsea", "Nebelmeer (Bergtal: das Tal im Nebel, oben Sonne)", null, func(): _bt_do("fogsea"), "Wetter", {"sub": "Mehr Wetter"})
	preload("res://scripts/bergtal_aussicht.gd").add_controls(self)     # «Bergtal · Aussichtspunkte»: Fernrohr, Panorama, Reichweite …
	for _c in controls:   # Bergtal-only controls: only shown in its scene (like fp_spot); season, quick travel, events also in its places
		if str(_c.id).begins_with("bt_"):
			if str(_c.id) in ["bt_season", "bt_goto", "bt_events", "bt_orient", "bt_mark"] or str(_c.id).begins_with("bt_ev_"):
				_c["only"] = func(): return Worlds.world_of(scene) == "bergtal"
			else:
				_c["only"] = func(): return scene == "bergtal"
			if _c.group == "Szene":
				_c.extra = _c.extra.duplicate()
				_c.extra["sub"] = "Bergtal"            # 3D-4.36 (Daniel): own part «Bergtal» on the card Szene, only in the Bergtal
	add_control("select", "szene_spot", "Standort an diesem Ort (Pfadilager, Hofladen, Bergdorf, Festival)", func(): return scene_spot(scene),
			func(v): set_scene_spot(str(v)), "Szene", {"options": _spot_options()})     # 3D-4.x: where MoveEye stands in a compact place (kompakt.gd)
	controls[-1]["only"] = func(): return Kompakt.is_kompakt(scene)
	add_control("map", "ort_map", "Ort auf der Karte wählen (Schweiz)", func(): return "%.6f, %.6f" % [ort_lat, ort_lon] if ort_lat != 0.0 else "",
			func(v): set_place_text(str(v)), "Ort von der Karte")
	add_control("text", "ort", "Ort (Name oder Koordinaten, z. B. «Zermatt» oder «46.0207, 7.7491»)", func(): return place_label(), func(v): set_place_text(str(v)), "Ort von der Karte")
	add_control("slider", "hour", "Uhrzeit", func(): return snappedf(hour(), 0.01), func(v): set_hour(v), "Szene", {"min": 0, "max": 23.75, "step": 0.25, "unit": "h"})
	add_control("select", "season", "Jahreszeit (Sonnenbahn)", func(): return season, func(v): season = str(v); _sun_cache = [-1.0, Vector2.ZERO]; _update_sky(), "Szene",
			{"options": [["today", "wie heute (echtes Datum)"], ["1", "Januar"], ["2", "Februar"], ["3", "März"], ["4", "April"], ["5", "Mai"], ["6", "Juni"],
			["7", "Juli"], ["8", "August"], ["9", "September"], ["10", "Oktober"], ["11", "November"], ["12", "Dezember"]]})
	add_control("slider", "speed", "Zeit läuft x-fach", func(): return speed, func(v): _set_speed(v), "Szene", {"min": 1, "max": 120, "step": 1, "unit": "×", "expert": true})
	add_control("toggle", "moon_auto", "Mondphase automatisch (Ort, Form und Licht des Monds nach Datum und Uhrzeit)", func(): return moon_auto, func(v): moon_auto = v, "Szene", {"expert": true})
	add_control("slider", "moon", "Mondphase fest: beleuchteter Teil (0 = Neumond, 1 = Vollmond)", func(): return moon, func(v):
		moon = v
		moon_auto = false, "Szene", {"min": 0, "max": 1, "step": 0.1, "expert": true})
	add_control("slider", "cam1_yaw", "Weitwinkel am Mast: Richtung", func(): return cam1_yaw, func(v): cam1_yaw = v, "Szene", {"min": -90, "max": 90, "step": 1, "unit": "°", "expert": true})
	add_control("select", "weather", "Wetter", func(): return weather, func(v): weather = v, "Wetter",
			{"options": [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]]})
	add_control("toggle", "world_cloth", "Fahnen und Wäsche im Wind", func(): return world_cloth, func(v): set_cloth(v), "Wetter", ex)
	add_control("toggle", "world_smoke", "Rauch aus Kaminen", func(): return world_smoke, func(v): set_smoke(v), "Wetter", ex)
	add_control("toggle", "world_fireflies", "Glühwürmchen in warmen Nächten", func(): return world_fireflies, func(v): world_fireflies = v, "Wetter", ex)
	add_control("toggle", "fauna_on", "Vögel am Tag (fliegen vorbei, Krähen, Elstern und Möwen am Boden), Fledermäuse in der Nacht (warm im Wärmebild, typische Fehlalarm-Ursache)", func(): return fauna_on, func(v): fauna_on = bool(v); fauna.on = fauna_on, "Wetter", {"sub": "Natur und Wind"})
	add_control("toggle", "gusts", "Wind in Böen", func(): return gusts, func(v): gusts = v, "Wetter", ex)
	add_control("toggle", "cloud_shadows", "Wolkenschatten (die Helligkeit wechselt)", func(): return cloud_shadows, func(v): cloud_shadows = v, "Wetter", ex)
	add_control("slider", "lamp_share", "Nachts mit Stirnlampe oder Handylicht", func(): return lamp_share, func(v): lamp_share = v, "Besuch", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	add_control("toggle", "look_at_light", "Menschen schauen zum Licht, wenn es angeht", func(): return look_at_light, func(v): look_at_light = v, "Besuch", ex)
	add_control("slider", "wind", "Wind", func(): return wind, func(v): wind = v, "Wetter", {"min": 0, "max": 120, "step": 1, "unit": "km/h"})
	add_control("toggle", "real_weather", "Echtes Wetter vom Ort (alle 10 Minuten, braucht Internet)", func(): return real_weather, func(v): real_weather = v; life._wx_t = -10000.0, "Wetter")
	add_control("toggle", "surprise_on", "Überraschungsnacht: nachts ab und zu Stromausfall, Nebelbank, Ablenkung, Scheinwerfer, ein Tier steht still – am Morgen die Bewertung von MoveEye", func(): return surprise_on, func(v): surprise.set_on(bool(v)), "Wetter")
	add_control("toggle", "night_weather", "Wetterverlauf über die Nacht (Dämmerung, Regenschauer, Tau auf der Linse, Morgennebel)", func(): return night_weather, func(v): night_weather = v; _nw["day"] = -1, "Wetter")
	add_control("toggle", "real_time", "Echte Uhrzeit (die Uhr des PCs)", func(): return real_time, func(v): real_time = v, "Szene")
	add_control("slider", "ambient", "Temperatur", func(): return ambient, func(v): ambient = v, "Wetter", {"min": -15, "max": 40, "step": 0.5, "unit": "°C"})
	add_control("slider", "humidity", "Luftfeuchtigkeit", func(): return humidity, func(v): humidity = v, "Wetter", {"min": 10, "max": 100, "step": 1, "unit": "%", "expert": true})
	add_control("slider", "pressure", "Luftdruck", func(): return pressure, func(v): pressure = v, "Wetter", {"min": 960, "max": 1040, "step": 0.5, "unit": "hPa", "expert": true})
	add_control("button", "storm", "Sturm zieht auf", null, func(): storm_t = now(), "Wetter", ex)
	add_control("toggle", "thunder", "Gewitter mit Blitzen (bei Regen; die Blitze sind auch eine typische Fehlalarm-Ursache)", func(): return thunder, func(v): thunder = v, "Wetter")
	# visitors: one button each (the window has the pictures to drag, the web page these buttons)
	for k in VISITOR_LIST:
		add_control("button", "spawn_" + k[0], k[1], null, func(): visit(k[0]), "Besuch")
	add_control("button", "car", "Auto", null, func(): car(), "Besuch")
	add_control("button", "thief", "Dieb (Velo, Tür)", null, func(): thief(), "Besuch")
	add_control("button", "dogwalk", "Spaziergang mit Hund", null, func(): visit("dogwalk"), "Besuch")
	add_control("button", "herd", "Rehrudel", null, func(): visit("herd"), "Besuch")
	# 3D-3.39: more visitors (single people and animals are in VISITOR_LIST; these come in groups or do something)
	add_control("button", "couple", "Paar (zu zweit)", null, func(): visit("couple"), "Besuch")
	add_control("button", "horse_walk", "Mit dem Pferd unterwegs", null, func(): visit("horse_walk"), "Besuch")
	add_control("button", "cows", "Kühe auf der Weide", null, func(): visit("cows"), "Besuch")
	add_control("button", "sheep_flock", "Schafherde", null, func(): visit("sheep_flock"), "Besuch")
	add_control("button", "bats", "Fledermäuse am Licht (nachts)", null, func(): visit("bats"), "Besuch")
	add_control("button", "owl", "Eule fliegt vorbei", null, func(): visit("owl"), "Besuch")
	add_control("button", "burglar", "Einbruchsversuch (schleicht, prüft die Tür – flieht vor Licht und Sirene)", null, func(): visit("burglar"), "Besuch")
	add_control("button", "sneaker", "Vorsichtiger Schleicher (von Deckung zu Deckung, kriecht, erstarrt bei Licht, Lampe aus)", null, func(): visit("sneaker"), "Besuch")
	add_control("button", "bbq", "Grillabend (Grill, Rauch, Freunde kommen)", null, func(): visit("bbq"), "Besuch")
	add_control("button", "homecoming", "Spät heimkommen (Auto hält, Tür auf und zu)", null, func(): visit("homecoming"), "Besuch")
	add_control("button", "parcel", "Paket wird gebracht", null, func(): visit("parcel"), "Besuch")
	add_control("button", "fox_trash", "Fuchs am Abfalleimer", null, func(): visit("fox_trash"), "Besuch")
	add_control("button", "boar_group", "Wildschweine mit Jungen", null, func(): visit("boar_group"), "Besuch")
	add_control("button", "kids_tag", "Kinder spielen Fangen", null, func(): visit("kids_tag"), "Besuch")
	add_control("button", "mowing", "Bauer mäht mit dem Traktor", null, func(): visit("mowing"), "Besuch")
	add_control("button", "night_lapse", "Ganze Nacht im Zeitraffer (20 → 6 Uhr, 60-fach, etwa 10 Minuten)", null, func(): stories.night_lapse(), "Besuch")
	add_control("toggle", "calendar", "Kalender: am Wochenende mehr Leute, im Winter weniger", func(): return calendar_on, func(v): calendar_on = v, "Besuch")
	add_control("button", "tractor", "Traktor", null, func(): visit("tractor"), "Besuch")
	add_control("button", "moto", "Töff", null, func(): visit("moto"), "Besuch")
	add_control("button", "van", "Lieferwagen", null, func(): visit("van"), "Besuch")
	add_control("button", "car_park", "Auto kommt an und parkiert (Leute steigen aus)", null, func(): visit("car_park"), "Besuch", ex)
	add_control("button", "bench", "Besuch setzt sich auf die Bank (Lustiger Platz)", null, func(): visit("bench"), "Besuch", ex)
	add_control("button", "feed", "Reh kommt zur Futterstelle (Wildbeobachtung)", null, func(): visit("feed_deer"), "Besuch", ex)
	add_control("button", "garden_person", "Besuch kommt durchs Gartentor (Garten)", null, func(): visit("garden_person"), "Besuch", ex)
	var pre_opts := [["", "– Vorlage wählen –"]]
	for vp in VISIT_PRESETS:
		pre_opts.append([vp[0], vp[1]])
	add_control("select", "visit_preset", "Vorlage für den Besuch (stellt «Von selbst» passend ein)", func(): return visit_preset, func(v): apply_visit_preset(str(v)), "Besuch",
			{"options": pre_opts})
	add_control("button", "clear", "Alle Besucher weg", null, func(): clear_visitors(), "Besuch")
	add_control("toggle", "auto", "ab und zu Besuch von selbst", func(): return auto_visitors, func(v): auto_visitors = v, "Besuch")
	add_control("toggle", "daily_life", "Tagesablauf: jeder kommt zu seiner Zeit (Fuchs nachts, Reh in der Dämmerung, Briefträger um 10 Uhr …)", func(): return daily_life, func(v): daily_life = v, "Besuch")
	add_control("select", "mix", "Wer kommt", func(): return mix, func(v): mix = v, "Besuch",
			{"options": [["mixed", "Tiere und Menschen"], ["more_animals", "mehr Tiere"], ["more_people", "mehr Menschen"], ["animals", "nur Tiere"], ["people", "nur Menschen"]]})
	add_control("slider", "visit_rate", "Wie oft Besuch kommt", func(): return visit_rate, func(v): visit_rate = v, "Besuch", {"min": 0.25, "max": 4.0, "step": 0.25, "unit": "×"})
	add_control("slider", "max_visitors", "Höchstens gleichzeitig", func(): return max_visitors, func(v): max_visitors = int(v); _perf_orig.erase("max_visitors"), "Besuch", {"min": 1, "max": 30, "step": 1, "expert": true})
	add_control("slider", "visitor_speed", "Tempo der Besucher", func(): return visitor_speed, func(v): visitor_speed = v, "Besuch", {"min": 0.25, "max": 2.5, "step": 0.05, "unit": "×", "expert": true})
	add_control("toggle", "flee_light", "Tiere flüchten nachts vor dem weissen Licht", func(): return flee_light, func(v): flee_light = v, "Besuch", ex)
	add_control("toggle", "flee_sound", "Tiere flüchten vor der Sirene", func(): return flee_sound, func(v): flee_sound = v, "Besuch", ex)
	add_control("toggle", "avoid_on", "Um Bäume, Häuser und Fahrzeuge herumgehen", func(): return avoid_on, func(v): avoid_on = v, "Besuch", ex)
	# 3D-4.x P1: the noise slider is also the one of «Kamera wie echt» (camphys.gd: noise from the gain of the sensor) - no second one
	add_control("slider", "lens_noise", "Rauschen (wie der Sensor: mehr Verstärkung = mehr Rauschen, am Tag sauber)", func(): return lens_noise, func(v): lens_noise = v, "Kamerabild", {"sub": "Wie echt", "min": 0, "max": 1, "step": 0.05, "expert": true})
	add_control("slider", "night_gain", "Nachtverstärkung der Kameras (höchstens)", func(): return night_gain, func(v): night_gain = v, "Kamerabild", {"min": 1, "max": 8, "step": 0.5, "unit": "×"})
	add_control("slider", "ir_range", "Reichweite des Infrarot-Lichts", func(): return ir_range, func(v): ir_range = v, "Kamerabild", {"min": 4, "max": 30, "step": 1, "unit": "m"})
	add_control("slider", "lens_vignette", "Dunkle Bildecken", func(): return lens_vignette, func(v): lens_vignette = v, "Kamerabild", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	# 3D-3.94: the camera like a real one - and like the real one of MoveEye
	add_control("toggle", "real_fx", "Kamera wie echt (Camera Module 3 NoIR): Belichtung und Verstärkung mit echten Grenzen, Rauschen bei wenig Licht, Bewegungsunschärfe, NoIR-Farben, Blendung nachts", func(): return realism.fx_on, func(v): realism.fx_on = bool(v); realism.save(), "Kamerabild", {"sub": "Wie echt"})
	add_control("toggle", "real_look", "Echt-Abgleich: Helligkeit, Farbe, Schärfe und Rauschen an die echten Bilder von MoveEye angleichen", func(): return realism.real_on, func(v): realism.real_on = bool(v); realism.save(), "Kamerabild", {"sub": "Wie echt"})
	add_control("toggle", "real_servo", "Servos wie echt: MG90S-Tempo nach Spannung, Getriebespiel, Nachschwingen, Anlaufstrom", func(): return realism.servo_real, func(v): realism.servo_real = bool(v); realism.save(), "Kamerabild", {"sub": "Wie echt"})
	if servo != null:
		servo.add_controls()                           # «Servo-Mechanik»: head weight, gear play; Störung «Schwaches Servosignal»
	add_control("button", "real_reset", "Echt-Abgleich zurücksetzen", null, func(): realism.reset(), "Kamerabild", {"sub": "Wie echt", "expert": true})
	camphys.add_controls()                                 # 3D-4.x P1: «Bewegungsunschärfe», «NoIR-Farben»
	add_control("toggle", "colors_on", "Natürliche Farben und Materialien (Metall, Glas, Stoff, nass bei Regen) – wirkt nach dem Szenenwechsel", func(): return colors_on, func(v): colors_on = v; colors.on = v; _settings_dirty = true, "Kamerabild", {"sub": "Wie echt"})
	add_control("toggle", "seasons_on", "Jahreszeiten: Gras und Laub nach dem Monat (Frühling, Sommer, Herbst, Winter)", func(): return seasons_on, func(v): seasons_on = v; colors.seasons_on = v; colors._month = -1; _update_sky(); _settings_dirty = true, "Szene", {"sub": "Zeit"})
	add_control("toggle", "show_laser", "Blickrichtung: roter Strahl aus dem Kopf und Bildränder am Boden (nur für dich sichtbar)", func(): return show_laser, func(v): show_laser = v; _settings_dirty = true, "Kamerabild")
	add_control("toggle", "show_zones3d", "Zonen von MoveEye in der 3D-Ansicht (nur für dich sichtbar)", func(): return show_zones3d, func(v): show_zones3d = v; _settings_dirty = true, "Kamerabild")
	add_control("toggle", "show_det3d", "Erkennung live in 3D: Rahmen von MoveEye über den Figuren (grün erkannt, rot Fehlalarm, orange übersehen)", func(): return show_det3d, func(v): show_det3d = v; _settings_dirty = true, "Kamerabild")
	add_control("toggle", "lens_drops", "Regentropfen auf der Linse", func(): return lens_drops, func(v): lens_drops = v, "Kamerabild")
	add_control("toggle", "sound_on", "Geräusche der Welt ans Mikrofon von MoveEye", func(): return sound_on, func(v): sound_on = v, "Kamerabild", ex)
	add_control("toggle", "insects", "Insekten am Licht (nachts, lösen wie echt Bewegung aus)", func(): return insects_on, func(v): insects_on = v, "Kamerabild")
	for cd in [["glare", "Gegenlicht (tiefe Sonne in der Linse, Äste lassen sie flackern)"], ["drops", "Tropfen auf der Linse (auch ohne Regen)"],
			["web", "Spinnennetz vor der Kopfkamera (nachts im Licht hell)"], ["headlights", "Scheinwerfer: nachts fahren immer wieder Autos vorbei"],
			["shadows", "Wolkenschatten: schnelle, tiefe Schatten"], ["ir", "Infrarot-Licht immer an (auch ohne MoveEye)"],
			["fogged", "Beschlagene Linse (Tau am Morgen, milchiger Schleier)"], ["dirt", "Schmutz und Pollen auf der Linse"],
			["shake", "Kamera wackelt im Wind (Mast, Stange)"], ["net", "Schlechtes WLAN: das Bild ruckelt und bleibt hängen"]]:
		var key: String = cd[0]
		add_control("toggle", "cond_" + key, cd[1], func(): return cond[key], func(v): cond[key] = bool(v), "Kamerabild")
	simreal.add_controls()                                 # 3D-4.4: closer to the real device
	objplus.add_controls()                                 # 3D-4.x «Gegenstände»: lures
	inhalte.add_controls()                                 # F2: System → Grafik «Echte Oberflächen und Himmel»
	umgebung.add_controls()                                # 3D-4.x: surroundings like real
	menschen.add_controls()                                # P10: people like real (Besuch → Verhalten / Von selbst / Menschen schicken)
	tiere.add_controls()                                   # Paket «Tiere»: free dog, birds on the ground
	fahrzeuge.add_controls()                               # Paket «Fahrzeuge»
	licht.add_controls()                                   # «Licht & Nacht»: light pollution, place lamps, tents / windows
	jahreszeiten.add_controls()                            # «Jahreszeiten & Tageslauf»: season, snow, fog, leaves, campsite occupancy
	gelaende.add_controls()                                # 3D-4.x: hills and more plants (Szene)
	wetter.add_controls()                                  # real-wetter: rain strength, visibility, ground fog, snow, lens, lightning
	wind_fx.add_controls()                                 # F6: wind in the plants and tents (Wetter → Natur und Wind)
	preload("res://scripts/figur_paket.gd").add_controls(self)   # F5: figures from the pack (System → Grafik)
	szenen.add_controls()                                  # 3D-4.x: the visitors of the new scenes (szenenplus.gd)
	if statusled != null:
		statusled.add_controls()                           # Licht & Ton → Status-LED & Tasten (Fenster «Gerät»)
	if smalltv != null:
		smalltv.add_controls()                             # 3D-4.19: Sensoren → Zusatz-Bildschirm (virtueller SmallTV)
	weit.add_controls()                                    # 3D-4.17: the wide camera (card «Kamerabild», part «Weitwinkel-Kamera»)
	parcours.add_controls()                                # 3D-4.18: card «Testlauf», part «Verfolgungs-Parcours»
	einbruch.add_controls()                                # card «Testen», part «Einbruch-Abläufe» (einbruch.gd)
	zwilling.add_controls()
	add_control("toggle", "dev2_on", "Zweites MoveEye-Gerät in der Welt (eigene Adresse: Port des Simulators + 20, meist 8785)", func(): return dev2.on, func(v): dev2.set_on(v), "Mover")
	add_control("select", "dev2_place", "Platz des zweiten Geräts", func(): return dev2.place, func(v): dev2.set_place(str(v)), "Mover",
			{"options": [["opposite", "gegenüber (30 m)"], ["left", "links"], ["right", "rechts"], ["door", "bewacht Zelt / Tür"], ["bike", "bewacht das Velo"], ["car", "bewacht das Auto (Strasse)"]]})
	add_control("toggle", "mover_on", "Mover (Kettenfahrzeug) simulieren – fahren mit dem grünen Stick unten rechts, den Pfeiltasten oder dem zweiten Stick in MoveEye", func(): return mover_on, func(v): set_mover(v), "Mover")
	# 3D-3.61: «Patrouille»
	add_control("toggle", "patrol_on", "Patrouille: der Mover fährt MoveEye die Route ab", func(): return patrol != null and patrol.active, func(v): if patrol != null: patrol.set_active(bool(v)), "Mover")
	add_control("select", "patrol_mode", "Route", func(): return patrol.mode if patrol != null else "points", func(v): if patrol != null: patrol.mode = str(v); patrol._dirty = true, "Mover",
			{"options": [["points", "feste Punkte (mit der Maus gesetzt)"], ["area", "zufällig im Bereich"]]})
	add_control("button", "patrol_points", "Punkte setzen: in die Welt klicken (Rechtsklick = Punkt weg)", null, func(): patrol.edit = "points"; patrol.mode = "points", "Mover")
	add_control("button", "patrol_area", "Bereich aufziehen (mit gedrückter Maustaste)", null, func(): patrol.edit = "area", "Mover")
	add_control("button", "patrol_random", "Zufällige Route rund um MoveEye", null, func(): patrol.random_route(), "Mover")
	add_control("button", "patrol_clear", "Route löschen", null, func(): patrol.clear_route(), "Mover")
	add_control("slider", "patrol_speed", "Tempo der Patrouille", func(): return patrol.speed if patrol != null else 0.9, func(v): if patrol != null: patrol.speed = float(v), "Mover", {"min": 0.3, "max": 3.0, "step": 0.1, "unit": "m/s"})
	add_control("slider", "patrol_dwell", "An jedem Punkt umschauen", func(): return patrol.dwell if patrol != null else 5.0, func(v): if patrol != null: patrol.dwell = float(v), "Mover", {"min": 1.0, "max": 20.0, "step": 1.0, "unit": "s"})
	add_control("slider", "patrol_sweep", "Kopf schwenkt beim Fahren", func(): return patrol.sweep if patrol != null else 70.0, func(v): if patrol != null: patrol.sweep = float(v), "Mover", {"min": 0.0, "max": 160.0, "step": 10.0, "unit": "°"})
	add_control("toggle", "patrol_follow", "Kopf dreht zu Verdächtigem, der Mover fährt dann langsamer", func(): return patrol.follow if patrol != null else true, func(v): if patrol != null: patrol.follow = bool(v), "Mover")
	add_control("select", "patrol_judge", "Spiel «Patrouille»: wer erwischt", func(): return patrol_judge, func(v): patrol_judge = str(v), "Mover",
			{"options": [["mw", "die echte Erkennung von MoveEye"], ["sim", "der Wächter des Simulators (geht ohne Pi)"]]})
	add_control("button", "rover_place", "📍 Rover versetzen – danach in die Welt klicken (beim Erkunden: Strg + Klick)", null, func(): place_kind = "rover", "Mover")
	add_control("slider", "mast_h", "Höhe der Kamera (Stange; beim Erkunden Bild auf / ab oder Steuerkreuz)", func(): return mast_h, func(v): set_mast(float(v)), "Mover", {"min": MAST_MIN, "max": MAST_MAX, "step": 0.05, "unit": "m", "live": true})
	add_control("button", "pad_roles", "🎮 Controller zuteilen (mehrere Controller: Wächter, Schleicher, Rover)", null, func(): padmap.open_roles(), "Mover", {"sub": "Controller"})
	add_control("button", "pad_test", "🎮 Controller testen (zeigt Stick roh und nach der Drift-Korrektur)", null, func(): _pad_test(), "Mover", {"sub": "Controller"})
	add_control("toggle", "pad_auto", "Stick-Drift selbst lernen (ein Stick, der 3 s genau gleich steht, gilt als Ruhelage)", func(): return pad_auto, func(v): pad_auto = v; _settings_dirty = true, "Mover", {"sub": "Controller"})
	add_control("button", "pad_cal", "🎮 Controller kalibrieren (gegen Stick-Drift: Sticks 2 s nicht berühren)", null, func(): start_info = explore.calibrate() if explore != null else "", "Mover", {"sub": "Controller"})
	add_control("slider", "pad_dead", "Totzone der Sticks (höher = weniger Drift, aber träger)", func(): return pad_dead, func(v): pad_dead = v; _settings_dirty = true, "Mover", {"min": 0.02, "max": 0.5, "step": 0.01, "sub": "Controller"})
	add_control("slider", "pad_sens", "Empfindlichkeit von Kopf und Ansicht (Stick)", func(): return pad_sens, func(v): pad_sens = float(v), "Mover", {"min": 0.3, "max": 2.5, "step": 0.1, "sub": "Controller"})
	add_control("toggle", "pad_inv_y", "Y umkehren (Stick hoch = Kopf / Blick runter)", func(): return pad_inv_y, func(v): pad_inv_y = bool(v), "Mover", {"sub": "Controller"})
	add_control("toggle", "pad_swap", "Sticks tauschen (links Rover / gehen, rechts Kopf / schauen)", func(): return pad_swap, func(v): pad_swap = bool(v), "Mover", {"sub": "Controller"})
	add_control("toggle", "pad_rumble", "Vibration (erwischt, Treffer, Alarm, die Kamera sieht dich)", func(): return pad_rumble, func(v): pad_rumble = bool(v), "Mover", {"sub": "Controller"})
	add_control("slider", "explore_speed", "Tempo beim Erkunden (Shift / A = schneller)", func(): return explore.speed if explore != null else 1.6, func(v): if explore != null: explore.speed = v, "Mover", {"min": 0.5, "max": 6.0, "step": 0.1, "unit": "m/s"})
	add_control("slider", "mover_max", "Höchstgeschwindigkeit des Movers", func(): return mover_max, func(v): mover_max = v, "Mover", {"min": 0.2, "max": 2.0, "step": 0.1, "unit": "m/s"})
	add_control("button", "mover_home", "Mover zurück an den Startplatz", null, func(): mover_home(), "Mover")
	add_control("toggle", "door", "Wohnwagentür offen", func(): return door_open, func(v): set_door(v), "Sensoren")
	add_control("toggle", "gas", "Gas / Rauch", func(): return gas_on, func(v): set_gas(v), "Sensoren")
	add_control("button", "pir", "PIR Zelt auslösen", null, func(): add_event("PIR Zelt", "pir"), "Sensoren")
	add_control("button", "bike", "Velo-Sensor auslösen (jemand rüttelt am Velo)", null, func(): add_event("Velo", "tag"), "Sensoren")
	simint.add_controls()                              # 30.10.2026: Lautsprecher, Störungen, Wärmebild (simint.gd)
	thermsensor.add_controls()                         # 3D-4.26: Kamerabild → Wärmebild (palette, sensor, tent, warm car)
	pir.add_controls()                                 # real-pir-ton: Sensoren → Bewegungsmelder (PIR)
	mikro.add_controls()                               # real-pir-ton: Licht & Ton → Mikrofon, Umgebungsgeräusche
	simwerte.add_controls()                            # Simulator-Werte: Akku und Strom, Netz-Ausfall testen (power.gd)
	add_control("toggle", "rifle", "Gewehr (unblutig, nur Tiere)", func(): return rifle_on, func(v): rifle_on = v, "Wildbeobachtung")
	add_control("button", "shoot_head", "Schuss aus der Kopfkamera", null, func(): shoot_head(), "Wildbeobachtung")
	add_control("button", "score0", "Punkte auf 0", null, func(): reset_score(), "Wildbeobachtung")
	zimmertiere.add_controls()                         # Erlebniswelt «mehr Tiere drinnen»: Wildtier → Hamster, Vogel, Spinne
	add_control("toggle", "news_popup", "Nach einem Update kurz zeigen, was neu ist (und was als Nächstes kommt)", func(): return news_popup, func(v): news_popup = v; _settings_dirty = true, "Updates")
	add_control("button", "news_show", "Was ist neu?", null, func(): news.show_news(), "Updates")
	# 3D-3.90: one choice instead of two switches (the old ids stay for MoveEye, hidden in the window)
	add_control("select", "update_mode", "Neue Versionen", func(): return "dev" if dev_updates else ("auto" if auto_update else "off"),
			func(v): dev_updates = str(v) == "dev"; set_auto_update(str(v) != "off"), "Updates",
			{"options": [["off", "nur von Hand (Knopf oben)"], ["auto", "automatisch installieren"], ["dev", "Entwicklungsphase: jede Minute, sofort"]]})
	# 3D-4.21: group «Entwickler» (like MoveEye, only «Experte»): test bench and faults - the same buttons as in «Testen»
	# Paket «Entwickler zusammenlegen»: in the panel only «Entwickler-Fenster öffnen»; the rest («devwin») in the window, tab «Schalter»
	add_control("button", "dev_open", "Entwickler-Fenster öffnen", null, func(): dev_window("schalter"), "Entwickler", {"expert": true})
	add_control("button", "pruef_open", "Prüfstand öffnen", null, func(): pruef.open(not pruef.visible), "Entwickler", {"expert": true, "devwin": true})
	add_control("button", "simint_open", "Störungen testen", null, func(): _open_stoer(), "Entwickler", {"expert": true, "devwin": true})
	preload("res://scripts/spieltest.gd").add_controls(self)   # Spieltest-Assistent + «Spieltest-Meldungen» (wie MoveEye Entwickler)
	add_control("toggle", "dev_updates", "Entwicklungsphase: jede Minute nach neuen Versionen schauen und sofort installieren", func(): return dev_updates, func(v): dev_updates = v; _settings_dirty = true, "Updates", {"expert": true, "hide": true})
	add_control("toggle", "auto_update", "Neue Versionen automatisch installieren", func(): return auto_update, func(v): set_auto_update(v), "Updates", {"expert": true, "hide": true})
	add_control("button", "update_now", "Jetzt nach Updates suchen und installieren", null, func(): run_update(true, false), "Updates", {"expert": true, "hide": true})
	add_control("select", "testrun_plan", "Welcher Testlauf", func(): return testrun.plan, func(v): testrun.plan = v, "Testlauf",
			{"options": testrun.plan_options()})
	add_control("button", "testrun_start", "Testlauf starten (MoveEye muss verbunden sein)", null, func(): testrun.start(), "Testlauf")
	add_control("button", "testrun_stop", "Testlauf abbrechen", null, func(): testrun.stop(false), "Testlauf")
	add_control("button", "rec_start", "● Aufnahme starten (wer wo geht, Zeit, Wetter – höchstens 5 Minuten)", null, func(): recorder.start_rec(), "Testlauf")
	add_control("button", "rec_stop", "■ Aufnahme beenden und speichern", null, func(): recorder.stop_rec(), "Testlauf")
	add_control("select", "rec_pick", "Aufnahme", func(): return recorder.pick, func(v): recorder.pick = str(v), "Testlauf", {"options": recorder.options()})
	add_control("button", "rec_play", "▶ Aufnahme abspielen (genau gleich wie aufgenommen)", null, func(): recorder.play(), "Testlauf")
	add_control("toggle", "rec_loop", "Immer wieder abspielen", func(): return recorder.loop, func(v): recorder.loop = v, "Testlauf")
	add_control("button", "rec_stopplay", "Wiedergabe beenden", null, func(): recorder.stop_play(), "Testlauf")
	add_control("button", "testrun_open", "Letzten Bericht öffnen", null, func(): testrun.open_report(), "Testlauf")
	add_control("button", "tv_mode", "📺 TV-Modus für den Spielabend (Taste T, ganzer Bildschirm)", null, func(): tv.set_on(not tv.on), "Spiel")
	add_control("button", "game_wizard", "🎮 Assistent öffnen: Spiel einrichten und starten", null, func(): gamewiz.open_wiz(), "Spiel")
	# 3D-4.39: the Bergtal adventure starts from the game wizard (quick start card «Bergtal-Abenteuer», gamewiz.gd)
	add_control("toggle", "game_open", "Spiel öffnen (Handys können mitspielen)", func(): return game.open, func(v): game.set_open(v), "Spiel")
	add_control("button", "game_start", "▶ Start", null, func(): _game_card_start(), "Spiel")
	add_control("button", "game_stop", "⏹ Stopp", null, func(): _game_card_stop(), "Spiel")
	entdecken.register_controls()                       # Erlebniswelt 20–23: Spiel → Entdecken (Buch, Foto, Blinki-Hinweise)
	add_control("button", "disc_seek", "🙈 Verstecken mit MoveEye", null, func(): _fp_seek(), "Spiel")   # Erlebniswelt 12
	controls[-1]["only"] = func(): return scene == "ferienpark"   # 3D-4.30: only in the Ferienpark (like «Standort im Ferienpark»)
	preload("res://scripts/ferienpark_leben.gd").add_controls(self)   # Ferienpark-Leben: 3 tasks (Spiel → Entdecken) + «Leben nach Uhrzeit» (Besuch → Von selbst)
	add_control("slider", "game_minutes", "Dauer einer Runde", func(): return game_minutes, func(v): game_minutes = v, "Spiel", {"min": 1, "max": 15, "step": 1, "unit": "min"})
	add_control("select", "game_mode", "Spielart", func(): return game_mode, func(v): game_mode = v, "Spiel",
			{"options": [["mw", "Gegen MoveEye (echte Erkennung)"], ["guard", "Wächter (ein Spieler oder der Bot-Wächter)"], ["seek", "Verstecken mit dem Rover (Fänger sieht nur die Kamera)"], ["free", "Zonen-Check – ohne Erwischen (zum Testen der Erkennung)"], ["jaeger", "Fehlalarm-Jäger – Tiere und Dinge täuschen MoveEye (nur mit MoveEye)"], ["camera", "ältere: Alle gegen die Kamera"], ["mwhand", "ältere: Team gegen MoveEye (Wächter steuern MoveEye)"], ["patrol", "ältere: Patrouille mit dem Mover"]]})
	# Balance 30.10.2026: two levels, ONE text (gamerules.gd LEVEL_TXT / GLEVEL_TXT - the same as in the wizard)
	add_control("select", "game_level", "Schleicher-Stufe (wie schnell die Kamera / MoveEye dich bemerkt)", func(): return game_level, func(v): game_level = v, "Spiel",
			{"options": preload("res://scripts/gamerules.gd").level_options()})
	add_control("select", "game_glevel", "Wächter-Stufe (Treffer-Kreis und Energie)", func(): return game.rules.guard_level, func(v): game.rules.cfg_set({"game_glevel": str(v)}), "Spiel",
			{"options": preload("res://scripts/gamerules.gd").glevel_options()})
	add_control("toggle", "game_real", preload("res://scripts/gamerules.gd").REAL_TXT, func(): return game.rules.real_hw, func(v): game.rules.cfg_set({"game_real": bool(v)}), "Spiel")
	add_control("select", "game_lives", "Leben", func(): return str(game_lives), func(v): game_lives = int(v), "Spiel",
			{"options": [["0", "unbegrenzt"], ["3", "3 Leben"], ["1", "1 Leben"]]})
	add_control("slider", "game_items", "Kristalle zum Sammeln", func(): return game_items, func(v): game_items = int(v), "Spiel", {"min": 0, "max": 6, "step": 1})
	# 3D-4.x (Aufräumen): no toggle «Zwei Teams» any more - teams only with the goal «Fahne erobern» (game.sync_teams)
	add_control("toggle", "game_rescue", "Befreien: Erwischte kommen in die Zelle, ein Teamkollege befreit sie", func(): return game_rescue, func(v): game_rescue = v, "Spiel")
	add_control("toggle", "game_teamgoal", "Team-Ziel: das Ziel öffnet erst, wenn alle Kristalle gefunden sind", func(): return game_teamgoal, func(v): game_teamgoal = v, "Spiel", ex)
	add_control("select", "game_goal", "Spielziel", func(): return game_goal, func(v): game_goal = v, "Spiel",
			{"options": [["reach", "Zum Ziel schleichen"], ["return", "Beute holen und zurückbringen"], ["flag", "Fahne erobern (zwei Teams)"], ["sprint", "Sprint: 90 s, fester Parcours"], ["theft", "Diebstahl: Velo oder Kühlbox zum Ausgang tragen"],
				["mission", "Mission mit Gegenständen (Portemonnaie, Früchte, Paket)"], ["sweat", "Bring MoveEye ins Schwitzen"]]})
	add_control("toggle", "game_stones", "Steine werfen zum Ablenken", func(): return game_stones, func(v): game_stones = v, "Spiel")
	add_control("toggle", "game_powers", "Power-ups: Unsichtbar-Trank (lila) und Turbo (gelb)", func(): return game_powers, func(v): game_powers = v, "Spiel")
	add_control("toggle", "game_photos", "Erwischt-Fotos (Bild der Kamera beim Erwischen, Galerie am Schluss)", func(): return game_photos, func(v): game_photos = v, "Spiel")
	# 3D-3.52: the hit sequence (each on its own) and what the game teaches MoveEye
	add_control("toggle", "game_fx_laser", "Treffer: roter Laser vom Kamerakopf (Handy: Fadenkreuz)", func(): return game_fx_laser, func(v): game_fx_laser = v, "Spiel")
	add_control("toggle", "game_fx_paint", "Treffer: Farbklecks (Handy: Klecks auf dem Bildschirm)", func(): return game_fx_paint, func(v): game_fx_paint = v, "Spiel")
	add_control("toggle", "game_fx_flash", "Treffer: Blitz wie ein Radarfoto (Handy: weisser Blitz)", func(): return game_fx_flash, func(v): game_fx_flash = v, "Spiel")
	add_control("toggle", "game_tap", "Jäger an MoveEye zielt durch Antippen im Livebild", func(): return game_tap, func(v): game_tap = v, "Spiel")
	add_control("toggle", "game_learn_miss", "Erkennung lernen: Bilder von Spielern, die MoveEye nicht gemeldet hat", func(): return game_learn_miss, func(v): game_learn_miss = v, "Spiel")
	add_control("toggle", "game_learn_report", "Erkennung lernen: Spielbericht (wie schnell gemeldet, Abstand, Haltung, Licht)", func(): return game_learn_report, func(v): game_learn_report = v, "Spiel")
	add_control("toggle", "game_learn_paths", "Erkennung lernen: unerkannte Schleichwege als Testlauf speichern", func(): return game_learn_paths, func(v): game_learn_paths = v, "Spiel")
	add_control("toggle", "game_blind_bonus", "Bonus für blinde Flecken (+20 Punkte pro Sekunde sichtbar, aber nicht gemeldet)", func(): return game_blind_bonus, func(v): game_blind_bonus = v, "Spiel")
	add_control("button", "game_report_send", "📊 Spielberichte senden (GitHub-Schlüssel vom Prüfstand, sonst Schreibtisch)", null, func(): _game_report_send(), "Spiel")
	add_control("slider", "game_hides", "Verstecke (Büsche: 8 s unsichtbar)", func(): return game_hides, func(v): game_hides = int(v), "Spiel", {"min": 0, "max": 6, "step": 1})
	add_control("toggle", "game_decoy", "Lockvogel erlaubt (lockt die Kamera weg, Teampunkte)", func(): return game_decoy, func(v): game_decoy = v, "Spiel")
	add_control("toggle", "game_night", "Nacht-Runde mit Taschenlampen", func(): return game_night, func(v): game_night = v, "Spiel")
	add_control("toggle", "game_events", "Zufallsereignisse (Gewitter, Hund, Auto)", func(): return game_events, func(v): game_events = v, "Spiel")
	add_control("slider", "game_checkpoints", "Checkpoints (+150 Punkte)", func(): return game_checkpoints, func(v): game_checkpoints = int(v), "Spiel", {"min": 0, "max": 3, "step": 1})
	add_control("select", "game_bots", "Computer-Spieler (Bots), die mitschleichen", func(): return str(game_bots), func(v): game_bots = int(v); game.set_bots(game_bots), "Spiel",
			{"options": [["0", "keine"], ["1", "1 Bot"], ["2", "2 Bots"], ["3", "3 Bots"]]})
	add_control("toggle", "game_tutorial", "Übungsrunde: Schritt für Schritt erklärt, niemand wird erwischt", func(): return game_tutorial, func(v): game_tutorial = v, "Spiel")
	add_control("toggle", "game_daily", "Tagesaufgabe: heute für alle dieselbe Szene, dasselbe Ziel und dieselben Startpunkte", func(): return game_daily, func(v): game_daily = v, "Spiel")
	add_control("toggle", "game_ghost", "Geisterläufer: der eigene beste Weg läuft als Geist mit (nur die Spieler sehen ihn)", func(): return game_ghost, func(v): game_ghost = v, "Spiel")
	add_control("toggle", "game_heart", "Herzschlag, wenn die Kamera dich gleich sieht (Handy vibriert)", func(): return game_heart, func(v): game_heart = v, "Spiel")
	add_control("toggle", "game_botguard", "Bot-Wächter, wenn niemand Wächter sein will (Spielart «Wächter»)", func(): return game_botguard, func(v): game_botguard = v, "Spiel")
	add_control("toggle", "game_kiguard", "🤖 MoveEye als KI-Wächter (Runden mit Wächter: MoveEye bewacht selbst – echte Erkennung, Kopf folgt, Auslöser-Autopilot; braucht MoveEye)",
			func(): return game_kiguard, func(v): game_kiguard = bool(v), "Spiel")
	add_control("button", "game_kig_reset", "Liste «gegen die KI» zurücksetzen", null, func(): if game != null: game.kig.command({"op": "reset"}), "Spiel")
	add_control("button", "game_local", "Hier am PC mitspielen (Tastatur, Maus oder Controller)", null, func(): localplay.start("runner"), "Spiel")
	add_control("button", "game_local_guard", "Hier am PC Wächter sein (Kopf drehen, «Erwischt!»)", null, func(): localplay.start("guard"), "Spiel")
	add_control("toggle", "game_tasks", "Aufgabe für jede Runde (z. B. nur kriechend ins Ziel, Bonus)", func(): return game_tasks, func(v): game_tasks = v, "Spiel")
	add_control("toggle", "game_autohandicap", "Handicap für den Ersten der Rangliste", func(): return game_autohandicap, func(v): game_autohandicap = v, "Spiel")
	add_control("button", "game_board_reset", "Rangliste des Abends zurücksetzen", null, func(): game.board_reset(), "Spiel")
	add_control("toggle", "game_spectate", "Zuschauer-Kamera: fliegt bei Spielstart selbst übers Spielfeld", func(): return game_spectate, func(v): game_spectate = v, "Spiel")
	add_control("toggle", "spectate_now", "Zuschauer-Kamera jetzt", func(): return spectate, func(v): spectate_start() if v else spectate_stop(), "Spiel")
	add_control("toggle", "game_noise", "Mikrofon hört laute Schritte", func(): return game_noise, func(v): game_noise = v, "Spiel", ex)
	add_control("toggle", "game_cones", "Sichtfeld der Kameras zeigen (für Anfänger)", func(): return game_cones, func(v): game_cones = v, "Spiel")
	add_control("toggle", "game_random", "Start und Ziel zufällig", func(): return game_random, func(v): game_random = v, "Spiel", ex)
	add_control("select", "game_quality", "Bild auf dem Handy", func(): return game_quality, func(v): game_quality = v, "Spiel",
			{"options": [["small", "klein (schnell)"], ["mid", "mittel"], ["big", "gross (braucht mehr Leistung)"]], "expert": true})
	add_control("slider", "game_max", "Läufer höchstens (mehr Spieler schauen zu)", func(): return game_max, func(v): game_max = int(v), "Spiel",
			{"min": 2, "max": 12, "step": 1, "tip": "Jeder Läufer ist ein eigenes 3D-Bild auf dem PC und ein eigenes Video übers Netz. Laptop: etwa 4, PC mit Grafikkarte: 6–8. Ab 5 Läufern werden die Bilder automatisch kleiner."})
	add_control("toggle", "game_guard", "Ohne MoveEye bewacht der Kopf selbst", func(): return game_guard, func(v): game_guard = v, "Spiel", ex)
	for tl in [["light", "💡 Licht"], ["siren", "📢 Sirene"], ["scan", "📡 Scan"], ["zoom", "🔍 Zoom"]]:   # 3D-4.x: tools of the guards at MoveEye (gametools.gd, part 543)
		var tid: String = tl[0]
		add_control("button", "game_tool_" + tid, "Wächter an MoveEye: " + tl[1], null, func(): game.tools.use(null, tid, "MoveEye"), "Spiel")
	add_control("toggle", "autostart", "Mit dem PC starten (sendet gleich an MoveEye)", func(): return autostart_on, func(v): set_autostart(v), "Start mit dem PC")
	add_control("toggle", "autostart_min", "Dabei klein (nur das Kästchen in der Ecke)", func(): return autostart_min, func(v): autostart_min = v, "Start mit dem PC")
	add_control("toggle", "autostart_mwpc", "Dabei auch MoveEye auf diesem PC starten (ohne Pi)", func(): return autostart_mwpc, func(v): autostart_mwpc = v, "Start mit dem PC")
	if OS.get_name() == "Windows":
		add_control("toggle", "autostart_lock", "Danach den Bildschirm sperren", func(): return autostart_lock, func(v): autostart_lock = v, "Start mit dem PC")
		add_control("button", "autologon", "Ohne Anmelden: automatische Anmeldung von Windows einrichten …", null, func(): setup_autologon(), "Start mit dem PC", {"expert": true})
	# 3D-3.69: what the «Kinder» mode shows (only the adults can change it - in the Kinder mode these settings are hidden)
	add_control("toggle", "kids_scary", "Kinder-Modus: Wildschwein, Wolf und Luchs", func(): return kids_scary, func(v): kids_scary = v, "Kinder-Modus")
	add_control("toggle", "kids_thief", "Kinder-Modus: Schleicher (Dieb) und Einbrecher", func(): return kids_thief, func(v): kids_thief = v, "Kinder-Modus")
	add_control("toggle", "kids_laser", "Kinder-Modus: Laser-Treffer im Spiel", func(): return kids_laser, func(v): kids_laser = v, "Kinder-Modus")
	add_control("toggle", "kids_sound", "Kinder-Modus: Töne bei den Knöpfen", func(): return kids_sound, func(v): kids_sound = v, "Kinder-Modus")
	add_control("toggle", "kids_ask", "Kinder-Modus: zum Verlassen eine Rechenaufgabe stellen (aus = ein Klick auf «Erwachsene» genügt)", func(): return kids_ask, func(v): kids_ask = bool(v), "Kinder-Modus")
	# F1 (Konzept-Wunsch): EINE Wahl «Grafik-Modus» Automatisch / Lite / Normal / Hoch; die Feinheiten (Grafik-Details,
	# «Automatisch leichter», Tiefenschärfe) nur unter «Experte»
	add_control("select", "grafik_mode", "Grafik-Modus", func(): return grafik_mode, func(v): set_grafik_mode(str(v)), "Grafik",
			{"options": Quality.MODES, "tip": "Hoch: Licht prallt von Flächen ab, Dunst, weiche Schatten, Spiegelungen auf Wasser und nassen Flächen, bessere Oberflächen. Braucht eine gute Grafikkarte (Vulkan); der Simulator startet dafür einmal neu."})
	add_control("select", "quality", "Grafik-Details (Schatten, Leuchten, Wolken)", func(): return quality, func(v): _set_quality(v), "Grafik",
			{"expert": true, "options": [["simple", "einfach (schnell)"], ["medium", "mittel"], ["nice", "schön (Schatten, Leuchten, Wolken)"],
						 ["ultra", "ultra (für starke Grafikkarten; mit Vulkan noch mehr Effekte)"]]})
	add_control("toggle", "grafik_dof", "Hoch: Tiefenschärfe in der freien Ansicht (die Kamerabilder für MoveEye bleiben scharf)", func(): return hoch.dof_free, func(v): hoch.set_dof(bool(v)), "Grafik", ex)
	add_control("slider", "view_scale", "Schärfe der Ansicht im Fenster (weniger = schneller; die Bilder für MoveEye bleiben scharf)", func(): return view_scale, func(v): set_view_scale(float(v)), "Grafik", {"min": 0.4, "max": 1.0, "step": 0.05, "unit": "×"})
	add_control("select", "win_fps", "Bilder pro Sekunde im Fenster", func(): return str(win_fps), func(v): win_fps = int(v); _perf_orig.erase("win_fps"); _settings_dirty = true, "Grafik",
			{"options": [["0", "so viele wie möglich"], ["60", "60"], ["30", "30 (spart Strom)"], ["20", "20 (schwacher PC)"]]})
	add_control("toggle", "auto_perf", "Automatisch leichter, wenn der PC zu langsam ist", func(): return auto_perf, func(v): auto_perf = v; _slow_n = 0, "Grafik", ex)
	add_control("toggle", "eco_idle", "Simulator ruht, wenn niemand zuschaut (rechnet nur, wenn das Fenster offen oder MoveEye verbunden ist)", func(): return eco_idle, func(v): eco_idle = v, "Grafik", ex)
	add_control("toggle", "meadow", "Gras und Blumen auf der Wiese", func(): return meadow_on, func(v): set_meadow(v), "Grafik", ex)
	add_control("toggle", "map_on", "Übersichtskarte oben links (M)", func(): return map_on, func(v): set_map(v), "Grafik")
	add_control("toggle", "live_on", "Livebild unter der Karte (L)", func(): return live_on, func(v): set_live(v), "Grafik")
	add_control("select", "live_cam", "Livebild: welche Kamera", func(): return str(live_cam), func(v): set_live(live_on, int(v)), "Grafik",
			{"options": [["0", "Kamera 1 (Kopf)"], ["1", "Kamera 2"], ["2", "Wärmebild"]]})
	add_control("slider", "live_size", "Livebild: Breite", func(): return live_size, func(v): set_live(live_on, -1, float(v)), "Grafik",
			{"min": 160, "max": 520, "step": 20, "unit": "px"})


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
	if not _perf_auto:
		_perf_orig.erase("view_scale")
	view_scale = clampf(v, 0.4, 1.0)
	get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	get_viewport().scaling_3d_scale = view_scale
	_settings_dirty = true


func _perf_tick() -> void:
	"""3D-3.75: the window draws fewer than 14 pictures per second for 20 s: one step lighter (quality, then sharpness of the
	view, then the grass). The pictures for MoveEye are not touched."""
	if not auto_perf or not win_open or not sim_active or now() - _perf_t < 30.0 or busy_with() != "":
		_slow_n = 0 if not auto_perf else _slow_n
		return
	var lim: int = win_fps if win_fps > 0 else 60
	if Engine.get_frames_per_second() < min(14.0, lim * 0.7):
		_slow_n += 1
	else:
		_slow_n = max(0, _slow_n - 2)
	if _slow_n < 40:
		return
	_slow_n = 0
	_perf_t = now()
	for k_ in ["quality", "view_scale", "meadow_on"]:     # 3D-3.88: only for this session - the own choice stays saved
		if not _perf_orig.has(k_):
			_perf_orig[k_] = get(k_)
	_perf_auto = true
	var lvl: int = ["simple", "medium", "nice", "ultra"].find(quality)
	var what := ""
	if lvl > 0:
		_set_quality(["simple", "medium", "nice", "ultra"][lvl - 1])
		what = "Grafik «%s»" % ["einfach", "mittel", "schön"][lvl - 1]
	elif view_scale > 0.75:
		set_view_scale(0.75)
		what = "Ansicht 75 % scharf"
	elif meadow_on:
		set_meadow(false)
		what = "ohne Gras und Blumen"
	elif view_scale > 0.55:
		set_view_scale(0.55)
		what = "Ansicht 55 % scharf"
	else:
		_perf_auto = false
		return
	_perf_auto = false
	start_info = "Der PC ist langsam – leichter gemacht: %s (nur bis zum Neustart; Bilder für MoveEye unverändert)" % what
	print("auto graphics: " + what)


func _set_quality(v: String) -> void:
	if not _perf_auto:
		_perf_orig.erase("quality")
	quality = v
	_apply_quality()


func auto_quality() -> String:
	"""3D-3.33: first start - the graphics level from the graphics card (later the own choice is kept)"""
	var a := RenderingServer.get_video_adapter_name().to_lower() + " " + RenderingServer.get_video_adapter_vendor().to_lower()
	if Engine.get_architecture_name() in ["arm64", "arm32"] or a.contains("v3d") or a.contains("videocore"):
		return "simple"                                   # 3D-3.43: Raspberry Pi - the light graphics
	if in_vm or a.contains("llvmpipe") or a.contains("swiftshader") or a.contains("basic render") or a.contains("software"):
		return "simple"
	if a.contains("nvidia") or a.contains("geforce") or a.contains("radeon") or a.contains("amd") or a.contains("arc"):
		return "nice"
	return "medium"                                       # Intel and other built-in graphics


func _apply_quality() -> void:
	if not quality in ["simple", "medium", "nice", "ultra"]:
		quality = "nice"
	var lvl: int = ["simple", "medium", "nice", "ultra"].find(quality)
	var nice := lvl >= 2
	sun.shadow_enabled = lvl >= 1
	sun.directional_shadow_max_distance = [40.0, 60.0, 80.0, 120.0][lvl]
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if lvl <= 1 else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	white_light.shadow_enabled = lvl >= 1
	env.glow_enabled = lvl >= 1
	env.glow_intensity = 0.5 if lvl == 1 else 0.7
	env.glow_bloom = 0.0 if lvl < 2 else 0.06
	RenderingServer.directional_shadow_atlas_set_size(2048 if lvl <= 1 else 4096, true)
	var aa: Viewport.MSAA = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_2X, Viewport.MSAA_4X][lvl]
	for i in range(2):
		vps[i].msaa_3d = aa
	get_viewport().msaa_3d = aa
	sky_mat.set_shader_parameter("detail", 1.0 if lvl >= 1 else 0.0)
	for m in mats.values():
		_mat_detail(m, lvl >= 1)
	# Forward+ (Vulkan) only: light bouncing off surfaces, shadows in corners, reflections, light shafts in the fog
	var fwd: bool = RenderingServer.get_rendering_device() != null       # Vulkan / Forward+ (not the OpenGL renderer)
	env.ssao_enabled = fwd and lvl >= 2
	env.ssao_intensity = 1.6
	env.ssil_enabled = fwd and lvl >= 3
	env.ssr_enabled = fwd and lvl >= 3
	env.sdfgi_enabled = fwd and lvl >= 3
	env.volumetric_fog_enabled = fwd and lvl >= 3
	env.volumetric_fog_density = 0.008
	env.volumetric_fog_length = 80.0
	get_viewport().use_taa = fwd and lvl >= 3
	if hoch != null:
		hoch.after_quality()                       # F1: «Hoch» on top of the chosen level (or away again)


# ---- 3D-4.25 «Lite» (Wunsch Daniel 31.10.2026): the same simulator, lighter for the Raspberry Pi 5 ---------------------------
# «Grafik-Modus» Automatisch (Lite on a Pi / ARM computer or when the first seconds are very slow) / Lite / Normal. Lite: graphics
# level «einfach» (no shadows, no glow, no SSAO / SSR / fog volumes), the big view 60 % sharp, at most 25 pictures per second,
# rain / snow / smoke / fire with about a third of the particles, a third of the grass, small things far away not drawn, at
# most 6 visitors at once, a smaller picture of the window for MoveEye. The camera pictures for MoveEye keep their size.
# The own choices (Grafik, Schärfe, Bilder/s, Besucher) stay saved (_perf_orig) and come back with «Normal».
const LITE_KEYS := ["quality", "view_scale", "win_fps", "max_visitors"]


func set_grafik_mode(v: String) -> void:
	grafik_mode = Quality.mode_id(v)
	lite_update()
	if hoch != null and (grafik_mode == "hoch") != (hoch.stufe == "hoch"):
		hoch.set_stufe(grafik_mode)                       # F1: Hoch = Neustart mit Forward+; jede andere Wahl = wieder normal
	_settings_dirty = true


func lite_update() -> void:
	"""Lite on or off - from «Grafik-Modus» and the hardware (quality.gd)"""
	var why := ""
	if grafik_mode == "lite":
		why = "von Hand"
	elif grafik_mode == "auto":
		var w := Quality.weak_reason()
		if w != "":
			why = "automatisch: " + w
		elif _lite_slow:
			why = "automatisch: wenige Bilder pro Sekunde beim Start"
	lite_why = why
	var on := why != ""
	if Engine.has_meta("lite") and on == Quality.lite():
		return
	Quality.set_lite(on)
	_lite_apply(on)
	print("graphics mode %s -> Lite %s%s" % [grafik_mode, "on" if on else "off", (" (" + why + ")") if on else ""])


func _lite_apply(on: bool) -> void:
	if on:
		for k_ in LITE_KEYS:
			if not _perf_orig.has(k_):
				_perf_orig[k_] = get(k_)
		_perf_auto = true                                  # not the own choice: the setters keep _perf_orig
		_set_quality("simple")
		set_view_scale(minf(view_scale, Quality.SCALE))
		if win_fps <= 0 or win_fps > Quality.FPS:
			win_fps = Quality.FPS
		max_visitors = mini(max_visitors, Quality.VISITORS)
		_perf_auto = false
		view_w = mini(view_w, Quality.VIEW_W)
		view_q = minf(view_q, Quality.VIEW_Q)
	else:
		for k_ in LITE_KEYS:
			if _perf_orig.has(k_):
				var v = _perf_orig[k_]
				_perf_orig.erase(k_)
				if k_ == "quality":
					quality = str(v)
					_apply_quality()
				elif k_ == "view_scale":
					set_view_scale(float(v))
				else:
					set(k_, int(v))
	for pa in [[rain, 2500], [snow, 3000], [splashes, 700]]:
		if pa[0] != null:
			pa[0].amount = Quality.n(pa[1])
	_lite_scene(on)
	_settings_dirty = true


func _lite_scene(on: bool) -> void:
	"""the things of the scene: fewer particles, thinner grass, small things far away not drawn (visibility range)"""
	if scene_parent == null:
		return
	var todo: Array = [scene_parent]
	while not todo.is_empty():
		var n = todo.pop_back()
		todo.append_array(n.get_children())
		if n is CPUParticles3D or n is GPUParticles3D:
			if not n.has_meta("full_n"):
				n.set_meta("full_n", n.amount)
			n.amount = maxi(1, roundi(int(n.get_meta("full_n")) * Quality.KEEP)) if on else int(n.get_meta("full_n"))
		elif n is MultiMeshInstance3D and n.is_in_group("meadow"):
			if n.multimesh != null:
				n.multimesh.visible_instance_count = roundi(n.multimesh.instance_count * Quality.KEEP) if on else -1
		elif n is GeometryInstance3D:
			if on:
				var sz: Vector3 = n.get_aabb().size * n.global_transform.basis.get_scale()
				if maxf(sz.x, maxf(sz.y, sz.z)) < 1.5 and n.visibility_range_end == 0.0:
					n.visibility_range_end = Quality.FAR
					n.set_meta("lite_far", true)
			elif n.has_meta("lite_far"):
				n.visibility_range_end = 0.0
				n.remove_meta("lite_far")


func _lite_tick() -> void:
	"""«Automatisch» on a normal PC: are the first seconds very slow (under 12 pictures per second)? Then Lite for this session"""
	if grafik_mode != "auto" or Quality.lite() or _lite_slow or not _lite_auto_ok:
		return
	var age := now() - _lite_t0
	if age < 6.0 or age > 40.0 or not win_open or not sim_active or busy_with() != "":
		return
	_lite_fps.append(Engine.get_frames_per_second())
	if _lite_fps.size() < 16:
		return
	var avg := 0.0
	for f in _lite_fps:
		avg += float(f) / _lite_fps.size()
	_lite_fps.clear()
	_lite_t0 = -1000.0                                   # decided once per start
	if avg < 12.0:
		_lite_slow = true
		lite_update()
		start_info = "Der Rechner ist langsam (%d Bilder/s) – «Grafik-Modus: Automatisch» hat Lite eingeschaltet (System → Grafik)." % roundi(avg)


func perf_info() -> Dictionary:
	"""for «Leistung» in the self-diagnosis and «Über»: frames per second, renderer, Lite, resolution"""
	var vs: Vector2 = get_viewport().get_visible_rect().size
	var k: float = get_viewport().scaling_3d_scale
	return {"fps": Engine.get_frames_per_second(), "renderer": Quality.renderer(), "lite": Quality.lite(), "why": lite_why,
			"mode": grafik_mode, "res": "%d × %d" % [roundi(vs.x * k), roundi(vs.y * k)], "scale": roundi(k * 100.0),
			"cams": "%d × %d" % [CAM_W[0], CAM_H[0]], "max_fps": Engine.max_fps}


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
	var out := []
	for c in controls:
		if c.has("only") and not bool(c["only"].call()):
			continue                                     # 3D-4.28: e.g. «Standort im Ferienpark» only in that scene
		var d := {"type": c.type, "id": c.id, "label": c.label, "group": c.group}
		d.merge(c.extra)
		if c["get"] != null:
			var v = c["get"].call()
			d["value"] = snappedf(v, 0.001) if typeof(v) == TYPE_FLOAT else v
		if c.has("ro"):
			d["ro"] = bool(c["ro"].call())            # Aufräumen 2: the page of MoveEye shows it read-only too
		out.append(d)
	return {"ok": true, "v": 1, "name": "MoveEye Sim · 3D %s" % VERSION,
				"scenarios": scenarios(), "scenario": Worlds.world_of(scene), "place": scene if Worlds.is_place(scene) else "",
			"controls": out, "status": status_text(), "upload": null, "groups_on": _groups_on(),
			"game": {"open": game != null and game.open, "url": game.address() if game != null and game.open else "", "players": game.count() if game != null else 0}}


func control(d: Dictionary) -> Dictionary:
	_ctl_frame = Engine.get_process_frames()
	var r := _control(d)
	_ctl_frame = -1
	return r


func _control(d: Dictionary) -> Dictionary:
	var a := str(d.get("action", "get"))
	var cid := str(d.get("id", ""))
	if a == "scenario":
		solo_scene = cid if bool(d.get("solo", false)) else ""   # 3D-4.x: this scene alone, without its world (training night)
		if not set_scene(cid):
			return {"ok": false, "error": "unknown scenario"}
	elif a == "welt":                                  # 3D-4.x Welten: the worlds, their places and what is loaded (worlds.gd)
		return Worlds.info(self)
	elif a == "delete":
		return {"ok": false, "error": "cannot be deleted"}
	elif a == "lang":                                  # Sprachen (i18n.gd): switch / translate, for tests
		return preload("res://scripts/i18n.gd").control(d)
	elif a == "ui_width":                              # for tests: is the content of the panel wider than the panel?
		_fold_all("open")
		var sim_was := ui_simple
		set_simple(false)
		var w := ui_box.get_combined_minimum_size().x
		set_simple(sim_was)
		var wide := []
		var stack: Array = [ui_box]
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			for ch in n.get_children():
				if ch is Control and ch.visible:
					var mw_: float = ch.get_combined_minimum_size().x
					if mw_ > 330.0:
						wide.append("%s %s %d" % [ch.get_class(), str(ch.get("text")).left(30), int(mw_)])
					stack.append(ch)
		return {"ok": true, "content_min": w, "panel": ui_root.size.x, "scroll_space": ui_box.get_parent().size.x, "wide": wide}
	elif a == "world":                                 # for tests: life in the world
		var sm := []
		for n in get_tree().get_nodes_in_group("smoke"):
			sm.append([n.emitting, n.global_position, n.visible, n.is_visible_in_tree()])
		return {"ok": true, "smoke": str(sm), "fireflies": [fireflies.emitting, fireflies.is_visible_in_tree()], "cloth": get_tree().get_nodes_in_group("cloth").size()}
	elif a == "busy":                                  # one lock with MoveEye: who has the world right now ('' = free)
		if bool(d.get("with_mw", false)):              # for tests / display: also what MoveEye itself does
			_ctl_frame = -1
		return {"ok": true, "busy": busy_with(str(d.get("except", "")))}
	elif a == "test_report":                           # the test run: progress and the last report
		return testrun.state()
	elif a == "test_start":                            # MoveEye starts a test run (3D-3.27): {"plan": "standard" | "quick" | "hard" | "night"}
		var err: String = testrun.start(str(d.get("plan", testrun.plan)), d.get("cams", []) if typeof(d.get("cams", [])) == TYPE_ARRAY else [], int(d.get("mult", 1)), int(d.get("seed", 1)))
		var st: Dictionary = testrun.state()
		st["ok"] = err == ""
		if err != "":
			st["error"] = err
		return st
	elif a == "test_stop":
		testrun.stop(false)
		return testrun.state()
	elif a == "game":                                  # for tests: the game (players, meter, round)
		var ps := []
		for p in game.players:
			if p != null:
				ps.append({"slot": p["slot"], "name": p["name"], "x": snappedf(p["actor"].position.x, 0.01), "z": snappedf(p["actor"].position.z, 0.01),
						"susp": snappedf(p["susp"], 0.1), "seen": p["seen"], "state": p["state"], "caught": p["caught"], "posture": p["actor"].ctl_posture,
						"online": p["sock"] != null, "vis": snappedf(game.visibility(p), 0.01), "cams": game.vis_debug(p)})
		return {"ok": true, "open": game.open, "round": game.round_state, "players": ps, "guard": game.guard_auto, "guard_yaw": snappedf(game.guard_yaw, 0.01),
				"goal": [snappedf(game.goal.x, 0.01), snappedf(game.goal.z, 0.01)], "address": game.address(),
				"items": game.items.map(func(it): return [snappedf(it["pos"].x, 0.1), snappedf(it["pos"].z, 0.1), it["by"], snappedf(it["pos"].y, 0.01), snappedf(ground_y(it["pos"].x, it["pos"].z), 0.01)]),
				"goal_y": [snappedf(game.goal.y, 0.01), snappedf(ground_y(game.goal.x, game.goal.z), 0.01)], "insects": insects.emitting,
				"powers": game.powers.map(func(w): return [w["kind"], snappedf(w["pos"].x, 0.1), snappedf(w["pos"].z, 0.1), float(w["back"]) > 0.0]),
				"last_minute": game.last_minute,
				"hides": game.hides.map(func(h): return [snappedf(h["pos"].x, 0.1), snappedf(h["pos"].z, 0.1)]),
				"cps": game.checkpoints.map(func(h): return [snappedf(h["pos"].x, 0.1), snappedf(h["pos"].z, 0.1)]),
				"ev": game.ev_kind, "gallery": game.gallery.size(), "board": game.board_list(), "hour": snappedf(hour(), 0.1)}
	elif a == "game_put":                              # for tests: put a player somewhere
		var p2 = game.players[clampi(int(d.get("slot", 0)), 0, 3)]
		if p2 == null:
			return {"ok": false, "error": "no such player"}
		p2["actor"].position = free_spot(Vector3(float(d.get("x", 0.0)), 0, float(d.get("z", 0.0))), 0.4, true)
		return {"ok": true}
	elif a == "ui_scroll":                             # for tests: fold the cards (open / close / groups) and scroll the panel
		if d.has("fold"):
			_fold_all(str(d["fold"]))
		if d.has("simple"):
			set_simple(bool(d["simple"]))
		if d.has("open"):                                  # one card open, with all its parts
			for b in fold_bodies:
				if str(b.get_meta("title", "")) == str(d["open"]):
					UI.set_open(b, true)
					for sb in sub_bodies:
						if b.is_ancestor_of(sb):
							UI.set_sub_open(sb, true)
		show_panel(true)
		if d.has("y"):
			_test_scroll(float(d["y"]))
		return {"ok": true, "max": (ui_box.get_parent() as ScrollContainer).get_v_scroll_bar().max_value}
	elif a == "tunnel":                                # 3D-3.45: for tests / remote: {"host", "code", "on"}
		if d.has("host"):
			tunnel_host = str(d["host"])
			tunnel.host = tunnel_host
		if d.has("code"):
			tunnel_code = str(d["code"])
			tunnel.code = tunnel_code
		if d.has("on"):
			tunnel_on = bool(d["on"])
			tunnel.set_on(false)
			tunnel.set_on(tunnel_on)
		var tst: Dictionary = tunnel.state()
		tst["ok"] = true
		return tst
	elif a == "dataset":                               # Trainingsbilder (3D-3.44)
		var op2 := str(d.get("op", "get"))
		if op2 == "start":
			return dataset.start(int(d.get("n", 40)), d.get("conds", []) if typeof(d.get("conds", [])) == TYPE_ARRAY else [])
		if op2 == "game":                                # 3D-3.53: the «missed» pictures of the game
			return dataset.load_game()
		if op2 == "export":                              # 3D-3.74: a training set (YOLO) for an own AI model
			return dataset.export_pack(int(d.get("n", 500)), bool(d.get("scenes", true)), str(d.get("vielfalt", "")))
		if op2 == "stop":
			dataset.stop()
		if op2 == "packs" or op2 == "clean":            # «KI-Daten aufräumen» (kidaten.gd)
			var KD = preload("res://scripts/kidaten.gd")
			if op2 == "packs":
				return KD.state()
			if dataset.busy or kitrain.running:
				return KD.state({"ok": false, "error": "busy"})
			return KD.state(KD.aufraeumen(true, str(dataset.last_pack.get("dir", "")).get_file()))
		var st2: Dictionary = dataset.state()
		if op2 == "list":
			st2["items"] = dataset.list()
		return st2
	elif a == "kitrain":                               # «KI trainieren»: get / start {n, vielfalt, dry} / upload {dry}
		var op3 := str(d.get("op", "get"))
		if op3 == "start":
			return kitrain.start(int(d.get("n", 200)), str(d.get("vielfalt", dataset.vielfalt)), bool(d.get("dry", false)))
		if op3 == "upload":
			return kitrain.upload_last(bool(d.get("dry", false)))
		return kitrain.state()
	elif a == "netmap":                                # Empfangskarte (3D-3.44): measured spots as patches on the ground
		return {"ok": true, "n": show_netmap(d.get("points", []))}
	elif a == "replay":                                # Alarm-Rückblick in 3D (3D-3.44)
		if bool(d.get("stop", false)):
			replay.stop()
			return {"ok": true}
		if typeof(d.get("track")) != TYPE_DICTIONARY:
			return {"ok": false, "error": "track missing"}
		return replay.start(d["track"])
	elif a == "pruefstand":                            # Prüfstand (3D-3.49): get / open / start (for tests)
		var w_: String = str(d.get("do", "get"))
		if w_ == "open":
			pruef.open(true)
		elif w_ == "start":
			pruef.open(true)
			for k_ in pruef.plan_cbs:
				pruef.plan_cbs[k_].button_pressed = k_ in (d.get("plans", ["quick"]) as Array)
			pruef.reps.value = int(d.get("reps", 1))
			pruef.start()
		elif w_ == "send":
			pruef.send()
		elif w_ == "auto":                             # 3D-3.75: {on} - automatically after every update of MoveEye
			pruef.set_auto(bool(d.get("on", true)))
			if d.has("last"):
				var ad: Dictionary = pruef._auto_data()
				ad["last"] = str(d["last"])
				pruef._auto_save(ad)
			if d.has("touch_ago"):
				pruef._touch_t = now() - float(d["touch_ago"])
		return pruef.state()
	elif a == "planner":                               # Aufstell-Planer (3D-3.44): get / open / close / best / put
		var op := str(d.get("op", "get"))
		if op == "open":
			planner.open(true)
		elif op == "close":
			planner.open(false)
		elif op == "best":
			if not planner.visible:
				planner.open(true)
			planner.search_best()                    # runs on over a few frames; "busy" in the answer
		elif op == "put":
			planner.place_here()
		elif op == "home":
			set_home(Vector3.ZERO, 0.0)
		return planner.state()
	elif a == "tv":                                    # TV mode (3D-3.44): {"on": true/false, "info_url": "...", "fullscreen": true}
		if d.has("info_url"):
			tv.info_url = str(d["info_url"]).substr(0, 200)
		if d.has("on"):
			tv.set_on(bool(d["on"]), bool(d.get("fullscreen", true)))
		return {"ok": true, "tv": tv.state()}
	elif a == "ui_wide":                               # for tests: which parts of the panel are wider than it (3D-3.43)
		var lim := float(d.get("w", 360.0))
		var out := []
		var stack: Array = [ui_root]
		while stack.size() > 0:
			var n = stack.pop_back()
			if n is Control:
				var w: float = (n as Control).get_combined_minimum_size().x
				if w > lim and (n as Control).is_visible_in_tree():
					var t := ""
					if n is Label or n is Button:
						t = str(n.text).substr(0, 40)
					out.append([n.get_class(), int(w), t, str(n.get_path()).right(80)])
			for ch in n.get_children():
				stack.append(ch)
		return {"ok": true, "panel": [int(ui_root.size.x), int(ui_root.position.x)], "win": get_viewport().get_visible_rect().size, "wide": out.slice(0, 60), "float": [cam_float.position, cam_float.size, cam_float.visible] if cam_float != null else []}
	elif a == "geo":                                   # for tests: the place (loading, what was built)
		return {"ok": true, "busy": geo.busy, "loaded": geo.loaded, "info": geo.info, "counts": geo.counts, "terrain": terrain,
				"h0": geo.h0, "src": geo.dem_source, "note": geo_note, "y": ground_y(float(d.get("x", 0.0)), float(d.get("z", 0.0))),
				"map": karte.visible, "map_info": karte.status_text(), "dark": is_dark(), "anims": anims.size(), "b3d_night": geo.b3d_mat.get_shader_parameter("night") if geo.b3d_mat != null else -1, "sun": [snappedf(sun_pos().x, 0.1), snappedf(sun_pos().y, 0.1),
				snappedf(horizon_el(sun_pos().y), 0.1), sun_behind_hills(), snappedf(sun.light_energy, 0.01)]}
	elif a == "map":                                   # for tests: open the map at a place, zoom
		show_panel(false)
		karte.open(float(d.get("lat", 46.95)), float(d.get("lon", 7.44)), int(d.get("zoom", 0)))
		return {"ok": true}
	elif a == "wizard":                                # for tests: the place wizard (karte.gd) step by step
		var op := str(d.get("op", ""))
		if op == "pick":
			karte.sel = Vector2(float(d.get("lat", 46.95)), float(d.get("lon", 7.45)))
			karte.sel_name = str(d.get("name", ""))
			karte._show_step(1)
		elif op == "next":
			karte._next()
		elif op == "set":
			karte.set("w_" + str(d.get("key", "")), d.get("value"))
			karte._show_step(karte.step)
		return {"ok": true, "step": karte.step, "env": geo.env, "why": geo.env_why, "info": karte.info.text, "waiting": karte.waiting,
				"counts": geo.counts, "ort_env": ort_env, "visible": karte.visible}
	elif a == "input":                                 # the simulator window seen in MoveEye: mouse / finger / keys from there
		var ev = d.get("ev", [])
		return {"ok": true, "n": view_input(ev if ev is Array else [])}
	elif a == "game_handicap":                         # MoveEye: handicap for a player (0 … 2)
		game.set_handicap(int(d.get("slot", -1)), int(d.get("level", 0)))
		return {"ok": true}
	elif a == "view_look":                             # the phone as a window (3D-3.27): turn the phone = look round in the free view
		_to_free_view()
		if d.get("start", false) or _look_base.is_empty():
			_look_base = [view_cam.rotation.y, view_cam.rotation.x]
		var yw := float(_look_base[0]) + deg_to_rad(clampf(float(d.get("yaw", 0.0)), -360.0, 360.0))
		var pt := clampf(float(_look_base[1]) + deg_to_rad(float(d.get("pitch", 0.0))), deg_to_rad(-85.0), deg_to_rad(60.0))
		view_cam.rotation = Vector3(pt, yw, 0)
		view_want_t = now()
		return {"ok": true}
	elif a == "game_compare":                          # 3D-4.x: «Mensch gegen KI» (gamecompare.gd) - state / start / stop
		return game.cmp.command(d) if game != null and game.cmp != null else {"ok": false, "error": "not supported"}
	elif a == "game_kig":                              # 3D-4.x: «MoveEye als KI-Wächter» (gamekiwaechter.gd): info / set / reset
		return game.kig.command(d) if game != null and game.kig != null else {"ok": false, "error": "no game"}
	elif a == "game_shut":                             # 3D-4.x: «Auslöser» (gameshutter.gd) - info / aim / fire, for tests
		return game.shut.command(d) if game != null and game.shut != null else {"ok": false, "error": "no game"}
	elif a == "game_more":                             # «Gameplay ausfeilen» (gamemore.gd): info / set / probe … (tests, MoveEye)
		return game.more.command(d) if game != null and game.more != null else {"ok": false, "error": "no game"}
	elif a == "game_tool":                             # 3D-4.x: a tool of the guard (gametools.gd): {tool, slot} or {op: "info"}
		return game.tools.command(d) if game != null and game.tools != null else {"ok": false, "error": "no game"}
	elif a == "game_rules":                            # 3D-4.x: for tests - fairness, next guard, winner (gamerules.gd)
		var grd: Dictionary = game.rules.debug() if game != null and game.rules != null else {}
		grd["ok"] = not grd.is_empty()
		return grd
	elif a == "game_test":                             # 3D-3.52: for tests - where a player is in the head camera / move him there
		if game == null or not d.has("slot") or int(d["slot"]) < 0 or int(d["slot"]) >= game.players.size() or game.players[int(d["slot"])] == null:
			return {"ok": false, "error": "no player"}
		var gp: Dictionary = game.players[int(d["slot"])]
		if d.has("x") and d.has("z"):
			gp["actor"].position = Vector3(float(d["x"]), ground_y(float(d["x"]), float(d["z"])), float(d["z"]))
		if d.get("hit", false):
			game._caught(gp, null)
		var hp: Vector3 = cams[0].global_position
		var ap: Vector3 = gp["actor"].position
		return {"ok": true, "box": game.learn.box(gp), "sees": game.cam_sees(gp, 0), "state": gp["state"], "fx": game.fx_nodes.size(),
				"head": [hp.x, hp.y, hp.z], "pos": [ap.x, ap.y, ap.z], "goal": [game.goal.x, game.goal.z], "report": game.learn.report_dict() if d.get("report", false) else {}}
	elif a == "padview":                               # the «Controller-Ansicht» of MoveEye (padview.gd)
		return padview.command(d) if padview != null else {"ok": false, "error": "no padview"}
	elif a == "pad":                                   # 3D-3.59: a game controller at the browser (MoveEye page): axes and buttons
		if explore == null:
			return {"ok": false, "error": "no explore"}
		explore.remote_pad(d.get("ax", []), d.get("bt", []), str(d.get("name", "")))
		if d.has("hold"):                              # for tests on a slow PC: the values stay valid for «hold» s
			explore.rp_t = now() + clampf(float(d["hold"]), 0.0, 30.0)
		return {"ok": true, "on": explore.on, "view": explore.view, "rumble": padmap.take_web_rumble() if padmap != null else ""}
	elif a == "padmap":                                # 3D-4.13: the controller mapping (tests): state, act, menu, roles, help, rumble
		return padmap.command(d) if padmap != null else {"ok": false, "error": "no padmap"}
	elif a == "patrol":                                # 3D-3.61: «Patrouille» (for tests and remote): {on, points: [[x, z], …], area: [x, z, w, d], mode}
		if patrol == null:
			return {"ok": false, "error": "no patrol"}
		if d.has("points"):
			patrol.points = []
			for q in d["points"]:
				patrol.points.append(Vector2(float(q[0]), float(q[1])))
			patrol.mode = "points"
			patrol._dirty = true
		if d.has("area"):
			var ar: Array = d["area"]
			patrol.area = Rect2(float(ar[0]), float(ar[1]), float(ar[2]), float(ar[3]))
			patrol.mode = "area"
			patrol._dirty = true
		if d.has("mode"):
			patrol.mode = str(d["mode"])
		if d.has("guard"):                             # 3D-3.76: {guard: [x, z, radius, name]} - plan the route round it and start
			var gd: Array = d["guard"]
			patrol.guard_start(Vector2(float(gd[0]), float(gd[1])), float(gd[2]) if gd.size() > 2 else 10.0, str(gd[3]) if gd.size() > 3 else "Ort")
		if d.has("ask"):
			patrol.ask()
		if d.has("on"):
			patrol.set_active(bool(d["on"]))
		return patrol.state_dict()
	elif a == "explore":                               # 3D-3.55: explore with the rover (for tests and remote)
		if explore == null:
			return {"ok": false, "error": "no explore"}
		if d.has("on"):
			explore.set_on(bool(d["on"]))
		if d.has("view") and str(d["view"]) in explore.VIEWS:
			explore.view = str(d["view"])
		if d.has("invite"):
			explore.set_invite(bool(d["invite"]))
		if d.has("spectate"):
			explore.spectator(bool(d["spectate"]))
		if d.has("place"):                               # [x, z]: the rover there (3D-3.60)
			var pl: Array = d["place"]
			if mover_on:
				rig.position = Vector3(float(pl[0]), ground_y(float(pl[0]), float(pl[1])), float(pl[1]))
			else:
				home_pos = Vector3(float(pl[0]), 0, float(pl[1]))
				mover_home()
		if d.has("drive"):                             # [forward, turn, seconds] for a test drive
			var dv: Array = d["drive"]
			explore.test_drive = Vector2(float(dv[0]), float(dv[1]))
			explore.test_until = explore.main.now() + (float(dv[2]) if dv.size() > 2 else 2.0)
		return explore.state()
	elif a == "inventar":                              # 3D-3.86: {do: info | open | close | add (kind, x, z, r) | clear}
		var iv := str(d.get("do", "info"))
		if iv == "open":
			inventar.open()
			if d.has("tab"):
				inventar.tabs.current_tab = int(d["tab"])
		elif iv == "close":
			inventar.close()
		elif iv == "add":
			inventar.add_object(str(d.get("kind", "")), Vector3(float(d.get("x", 0)), 0, float(d.get("z", -8))), float(d.get("r", 0)))
		elif iv == "clear":
			inventar.clear_scene()
		return {"ok": true, "inventar": inventar.info()}
	elif a == "blindmap":                              # 3D-3.85: makeover 22 / 23 {do: start (az, dist, hour, walk) | info | stop}
		var bd := str(d.get("do", "info"))
		if bd == "game":                               # 3D-3.90: the blind spots the players found (az°, m), for MoveEye's map
			return {"ok": true, "pts": game.learn.blind_pts if game != null and game.learn != null else [],
					"badges": game.badges_all() if game != null else {}}                       # 3D-3.92: the badges of the players
		if bd == "start":
			return blindmap.start(d)
		if bd == "stop":
			blindmap.stop()
		return blindmap.info()
	elif a == "farecreate":                            # 3D-3.85: makeover 21 - re-enact the cause of a false alarm
		return farecreate(d)
	elif a == "rover":                                 # 3D-3.84: makeover 17 {do: info | patrol (on) | alarm | dock | goto (x, z)}
		var rd := str(d.get("do", "info"))
		if rd == "patrol":
			patrol.set_active(bool(d.get("on", true)))
		elif rd == "alarm":
			var ap = patrol.alarm_point()
			patrol.goto_point(ap, "alarm")
		elif rd == "dock":
			patrol.goto_point(Vector2(home_pos.x, home_pos.z), "dock")
		elif rd == "goto":
			patrol.goto_point(Vector2(float(d.get("x", 0)), float(d.get("z", -8))), "goto")
		return {"ok": true, "rover": patrol.rover_info()}
	elif a == "overlay":
		return {"ok": true, "overlay": overlay.info()}
	elif a == "kompakt":                               # 3D-4.x: the four compact scenes {do: info | spot (value) | perf} (kompakt.gd)
		return Kompakt.control(self, d)
	elif a == "bergtal":                               # 3D-4.x: {do: info | spot | bed | season | here | goto | event | ride | morning | rate | horn | perf} (bergtal.gd)
		return preload("res://scripts/bergtal.gd").control(self, d)
	elif a == "maggie":                                # «Maggie und der Bergkristall» (maggie_story.gd): {do: info | open | start | region …}
		return maggie.control(d) if maggie != null else {"ok": false, "error": "no maggie"}
	elif a == "horror":                                # Bergtal · Horror-Modus: {do: info | open | unlock | start | skip | pause | stop …} (bergtal_horror.gd)
		return horror.command(d) if horror != null else {"ok": false, "error": "no horror"}
	elif a == "ferienpark":                            # 3D-4.x: {do: info | spot (value) | kinds | perf} (ferienpark.gd)
		return preload("res://scripts/ferienpark.gd").control(self, d)
	elif a == "szenen":                                # 3D-4.x: the new scenes {do: info | spawn (kind) | restore}
		return szenen.control(d)
	elif a == "simreal":                               # 3D-4.4: {do: info | set (key, value) | sweep | bird | spawn (kind, from, to)}
		return simreal.control(d)
	elif a == "camphys":                               # 3D-4.x P1: {do: info | set (key: blur_k | noir_k, value)} - exposure, gain, light
		return camphys.control(d)
	elif a == "objekte":                               # 3D-4.x «Gegenstände»: {do: info | lure | test_place | test_clear | set}
		return objplus.control(d)
	elif a == "wind_fx":                               # F6: {do: info | set (on)}
		return wind_fx.control(d)
	elif a == "inhalte":                               # F2: {do: info | set (value) | laden | anwenden | zuruecksetzen}
		return inhalte.control(d)
	elif a == "umgebung":                              # 3D-4.x: {do: info | set (key, value) | spawn (kind) | snow_puff | clear_tracks}
		return umgebung.control(d)
	elif a == "menschen":                              # P10: {do: info | set (key, value) | spawn (kind) | api (id, fn, args) | probe (gait, dist, dark)}
		return menschen.control(d)
	elif a == "tiere":                                 # Paket «Tiere»: {do: info | spawn (kind, from, to) | threat (x, z, secs) | curl | pounce | car}
		return tiere.control(d)
	elif a == "fahrzeuge":                             # Paket «Fahrzeuge»: {do: info | set | spawn | arrive | toward | leave | reset}
		return fahrzeuge.control(d)
	elif a == "maggie_gefahr":                         # «Maggie und der Bergkristall» S3: böse Tiere, Schutzdinge (maggie_gefahr.gd)
		return load("res://scripts/maggie_gefahr.gd").control(self, d)
	elif a == "maggie_hund":                           # «Maggie und der Bergkristall», Paket S2: {do: info | start (region) | befehl (f) | spieler | loesen | stop}
		return preload("res://scripts/maggie_hund.gd").control(self, d)
	elif a == "licht":                                 # «Licht & Nacht»: {do: info | set | sources (cam) | lux | attach | headlights | at}
		return licht.control(d)
	elif a == "jahreszeiten":                          # «Jahreszeiten»: {do: info | set (key, value) | sun (doy, lat, lon) | year}
		return jahreszeiten.control(d)
	elif a == "gelaende":                              # 3D-4.x: {do: info | set (key, value) | height (x, z) | los (from, to) | cloud (x, z)}
		return gelaende.control(d)
	elif a == "wetter":                                # real-wetter: {do: info | set | flash | wipe | splash | fog | snow | morning}
		return wetter.control(d)
	elif a == "weit":                                  # 3D-4.17: wide camera {mount, tilt, tilt_follow, fisheye, pan_limit, do: info | probe | spawn}
		return weit.control(d)
	elif a == "nacht":                                 # Nacht-Testlauf: {do: info | start | stop | state | truth | plan} (nachtlauf.gd)
		return nacht.control(d)
	elif a == "abenteuer":                             # Bergtal-Abenteuer: {do: state | open | start | pick | next | choose | night | save | replay | report …}
		return abenteuer.op(d)
	elif a == "parcours":                              # 3D-4.18: {do: info | start (lessons, night, seed, prep_s) | stop | state | result | game | steer ...}
		return parcours.control(d)
	elif a == "einbruch":                              # {do: info | start (ablauf, seed, zeit) | serie | stop | state | result}
		return einbruch.control(d)
	elif a == "zwilling":                              # 3D-4.4: {do: info | import (path) | set (key, value) | item (k, x, z, r) | clear | remove | on}
		return zwilling.control(d)
	elif a == "fotomodus":                             # 3D-4.27: {do: info | on | set | mask_rect | mask_clear | more | measure | size | debug}
		return zwilling.fm.control(d)
	elif a == "whatif":                                # 3D-3.83: makeover 8 - MoveEye re-enacts a real recording
		return whatif(d)
	elif a == "twin":                                  # 3D-3.83: makeover 9 - the twin of the real place
		if str(d.get("op", "")) == "info":
			return {"ok": true, "twin": twin_info()}
		twin = {"name": str(d.get("name", "")), "t": Time.get_datetime_string_from_system()}
		if d.has("lat") and d.has("lon"):
			twin["lat"] = float(d["lat"])
			twin["lon"] = float(d["lon"])
			karte.open(twin["lat"], twin["lon"], 17)
			karte.sel = Vector2(twin["lat"], twin["lon"])
			karte.sel_name = "Dein Platz: " + twin["name"]
			karte._show_step(1)
			start_info = "Dein Platz («%s»): Karte an diesem Ort – «Diesen Ort laden» bestätigen" % twin["name"]
		else:
			start_info = "Dein Platz: MoveEye kennt seinen Ort nicht (GPS oder Ort in den Einstellungen) – Zonen und Patrouille kommen trotzdem"
		_settings_dirty = true
		return {"ok": true, "twin": twin_info(), "map": d.has("lat")}
	elif a == "news":                                  # 3D-3.82: {do: info | show | close}
		if str(d.get("do", "")) == "show":
			news.show_news()
		elif str(d.get("do", "")) == "close":
			news.close(bool(d.get("off", false)))
		return {"ok": true, "news": news.info()}
	elif a == "templates":                             # 3D-3.82: {do: info|open|import|remove|adjust, path, i, key, d, tab}
		var dd := str(d.get("do", "info"))
		if dd == "open":
			templates.toggle(int(d.get("tab", 0)))
		elif dd == "close":
			templates.visible = false
		elif dd == "import":
			return {"ok": templates.import_file(str(d.get("path", "")), bool(d.get("show", true))), "info": templates.info(), "msg": templates._msg.text}
		elif dd == "drop":
			templates._on_drop(PackedStringArray([str(d.get("path", ""))]))
		elif dd == "remove":
			templates.remove(int(d.get("i", 0)))
		elif dd == "adjust":
			templates._adjust(int(d.get("i", 0)), str(d.get("key", "x")), float(d.get("d", 1.0)))
		return {"ok": true, "info": templates.info(), "obstacles": obstacles.size(), "scene": scene}
	elif a == "visits":                                # 3D-3.80: finished visits for the diary of MoveEye {since: id}
		return {"ok": true, "visits": visitlog.since(int(d.get("since", 0))), "seq": visitlog.seq, "live": visitlog.live.size(), "sim": VERSION}
	elif a == "localplay":                             # 3D-3.77: play here at the PC (tests): {do: start | stop | get, role}
		var dl := str(d.get("do", "get"))
		if dl == "start":
			localplay.start(str(d.get("role", "runner")))
		elif dl == "stop":
			localplay.stop()
		elif dl == "key":
			var ke := InputEventKey.new()
			ke.keycode = int(d.get("key", KEY_ENTER))
			ke.pressed = true
			localplay._input(ke)
		return localplay.debug()
	elif a == "surprise":                              # 3D-3.75: {op: get | on | off | start (kind) | morning}
		var op_ := str(d.get("op", "get"))
		if op_ == "on" or op_ == "off":
			surprise.set_on(op_ == "on")
		elif op_ == "start":
			surprise.start(str(d.get("kind", "power")))
		elif op_ == "morning":
			surprise.morning()
		return {"ok": true, "surprise": surprise.info()}
	elif a == "entdecken":                             # Erlebniswelt 20–23: {do: info | open | close | photo | mark (id) | reset | hint | set | where (id)}
		return entdecken.control(d) if entdecken != null else {"ok": false, "error": "no entdecken"}
	elif a == "spielbereich":                          # Paket «Spielbereich»: {do: info | open | close | start (id) | seen | reset}
		return spielbereich.control(d) if spielbereich != null else {"ok": false, "error": "no spielbereich"}
	elif a == "dev":                                   # Entwicklertool 1 (devtool.gd): {do: places | goto (id) | fly (on, speed) | open | close | info}
		return mehr.dev.control(d) if mehr != null and mehr.dev != null else {"ok": false, "error": "not ready"}
	elif a == "werk":                                  # Werksrücksetzung (werk.gd): {do: info | open | close | reset (confirm: true)}
		return mehr.werk.control(d) if mehr != null and mehr.werk != null else {"ok": false, "error": "not ready"}
	elif a == "mehr":                                  # 3D-4.2x: «Mehr» (tests): {"do": open | theme | tour | diag | log | fb_* | shot}
		return mehr.control(d) if mehr != null else {"ok": false, "error": "not ready"}
	elif a == "feedback":                              # MoveEye 2.98.33: the dialog «Rückmeldung» (tests: {text, kind, stars, shot})
		_feedback_open()
		if feedback_dlg != null and str(d.get("text", "")) != "" and feedback_dlg.visible:
			feedback_dlg.fill_and_send(d)
		return {"ok": true, "open": feedback_dlg != null and feedback_dlg.visible, "connected": feedback_dlg != null and feedback_dlg.connected()}
	elif a == "mw_request":                            # 3D-3.71: like the buttons «Referenz-Scan» / «Vergleichen» (tests, remote)
		mw_request(str(d.get("op", "")))
		return {"ok": true, "cmd": mw_cmd}
	elif a == "bike":
		set_bike(bool(d.get("on", true)))
		return {"ok": true}
	elif a == "prop":                                  # 3D-3.72: test aids {name: Velo | Zelt | Tisch | Kühlboxen | Grill, on}
		set_prop(str(d.get("name", "")), bool(d.get("on", true)))
		return {"ok": true, "props": test_props.keys()}
	elif a == "sabotage":                              # {cover: bool, turn: degrees}
		set_sabotage(d.get("cover", null), d.get("turn", null))
		return {"ok": true, "cover": sabotage_cover, "turn": rad_to_deg(sabotage_turn)}
	elif a == "ref_night_test":
		ref_night_test()
		return {"ok": true}
	elif a == "home":                                  # 3D-3.73: «Mein Zuhause» {op: get | set (items) | edit (on)}
		var op := str(d.get("op", "get"))
		if op == "set" and d.get("items") is Array:
			home_items = (d["items"] as Array).filter(func(x): return typeof(x) == TYPE_DICTIONARY).slice(0, 400)
			home_save()
			home_rebuild()
		elif op == "edit":
			home_editor.open(bool(d.get("on", true)))
		return {"ok": true, "items": home_items, "kinds": Scenes.HOME_KINDS, "scene": scene}
	elif a == "shoot":                                 # 3D-3.70: a shot / trigger from MoveEye at a spot of the head camera picture
		if bool(d.get("shutter", false)) and game != null and game.shut.human_mode() == "mw":   # 3D-4.x: «Auslöser» (gameshutter.gd)
			return game.shut.fire(null, str(d.get("who", "")).left(30))
		return mw_shot(float(d.get("x", 0.5)), float(d.get("y", 0.5)), str(d.get("who", "")).left(30))
	elif a == "game_mwcatch":                          # «Team gegen MoveEye»: «Erwischt!» pressed at MoveEye (3D-3.27)
		if game == null:
			return {"ok": false, "error": "no game"}
		return game.mw_catch(str(d.get("who", "")).left(30), float(d.get("x", -1.0)), float(d.get("y", -1.0)))
	elif a == "gps":                                   # 3D-3.98: {steal: true | false} - the device is carried away
		if d.has("steal"):
			return gps_steal(bool(d["steal"]))
		var gr := gps_reading()
		gr["ok"] = true
		gr["steal"] = gps_steal_t > 0.0
		gr["solar"] = solar_reading()
		return gr
	elif a == "pir":                                   # real-pir-ton: {do: info | fire | set (key, value) | reset} (pir.gd)
		return pir.op(d)
	elif a == "mikro":                                 # real-pir-ton: {do: info | set (key, value) | probe (kind, db1m, x, z)} (mikrofon.gd)
		return mikro.op(d)
	elif a == "servo":                                 # «Servo-Mechanik»: {do: info | set (key, value) | sim (deg, mass, play, v)} (servo.gd)
		return servo.control(d)
	elif a == "simint":                                # 30.10.2026: {do: info | uv | pca | i2c | block (axis) | off | model (m) | hand (on)} (simint.gd)
		return simint.op(d)
	elif a == "sound":                                 # 3D-3.98: {kind: clap | sneeze | voice | shout, n, x, z}
		var sp = null
		if d.has("x") and d.has("z"):
			sp = Vector3(float(d["x"]), ground_y(float(d["x"]), float(d["z"])) + 1.5, float(d["z"]))
		return emit_sound(str(d.get("kind", "clap")), int(d.get("n", 2)), sp)
	elif a == "zimmertiere":                           # Erlebniswelt «mehr Tiere drinnen»: {do: info | lens (dist, hold) | set (pets, spider) | state (who, state)}
		return zimmertiere.control(d) if zimmertiere != null else {"ok": false, "error": "no zimmertiere"}
	elif a == "sleeper":                               # 3D-3.96: the person in the bed (bedroom scene)
		if sleeper == null:
			return {"ok": false, "error": "no sleeper"}
		return sleeper.command(d)
	elif a == "fenster":                               # Paket «Fenster» (fenster.gd): info / drag / resize / close / list / check / reset
		return fenster.control(d) if fenster != null else {"ok": false, "error": "no fenster"}
	elif a == "smalltv":                               # 3D-4.19: virtueller SmallTV - Zähler, letztes Bild (Tests, Prüfstand)
		return smalltv.control(d) if smalltv != null else {"ok": false, "error": "no smalltv"}
	elif a == "game_info":                             # the spectators in MoveEye: the game in numbers (3D-3.22)
		if game == null:
			return {"ok": false, "error": "no game"}
		var gi: Dictionary = game.spectator_info()
		gi["ok"] = true
		return gi
	elif a == "mover":                                 # for tests: where the mover is
		return {"ok": true, "pad": [pad_drive.x, pad_drive.y, now() - pad_t, _pad_l, _pad_r, rover_pad.dragging, sim_active, now() - _drive_t], "on": mover_on, "x": snappedf(rig.position.x, 0.01), "z": snappedf(rig.position.z, 0.01),
				"yaw": snappedf(rad_to_deg(rig.rotation.y), 0.1), "drive": mw.get("drive", {}),
				"near": _ob_near(Vector2(rig.position.x, rig.position.z - 0.3)).map(func(o): return [o["c"], _ob_closest(o, Vector2(rig.position.x, rig.position.z))[1]])}
	elif a == "grafik":                                # F1 «Grafikstufe Hoch» (tests, measuring): {do: info | set (value) | dof | off_session | on_session}
		return hoch.op(d)
	elif a == "view":                                  # for tests: the free view from a point to a point, panel away
		var vp_: Array = d.get("pos", [0, 3, 6])
		var la_: Array = d.get("look", [0, 1, 0])
		view_mode = 0
		view_cam.position = Vector3(float(vp_[0]), float(vp_[1]), float(vp_[2]))
		view_cam.look_at(Vector3(float(la_[0]), float(la_[1]), float(la_[2])))
		show_panel(bool(d.get("panel", false)))
		return {"ok": true}
	elif a == "window":                                # for tests: minimized? (2 = minimized) and how many frames were drawn
		return {"ok": true, "mode": DisplayServer.window_get_mode(), "frames": Engine.get_frames_drawn(), "autostart": autostart_on}
	elif a == "visitors":                              # for tests: where every visitor is, and whether it is inside an object
		var out := []
		for v in visitors.get_children():
			var p2 := Vector2(v.position.x, v.position.z)
			var deepest := 99.0
			for o in _ob_near(p2):
				if o["po"] and v.kind != "person":
					continue
				deepest = min(deepest, float(_ob_closest(o, p2)[1]))
			var sp := view_cam.unproject_position(v.global_position + Vector3(0, 0.6, 0))
			out.append({"kind": v.kind, "x": snappedf(v.position.x, 0.01), "z": snappedf(v.position.z, 0.01), "gap": snappedf(deepest, 0.01), "variant": v.variant, "route": v.route.size(), "wait": snappedf(max(0.0, v.wait_until - v.now_s()), 0.1), "tx": snappedf(v.target.x, 0.1), "tz": snappedf(v.target.z, 0.1), "spd": snappedf(v.cur_speed, 0.01), "r": v.radius,
					"y": snappedf(v.position.y, 0.01), "sx": int(sp.x), "sy": int(sp.y), "selected": v == selected})
		return {"ok": true, "visitors": out}
	elif a == "wheel_probe":                           # for tests (3D-3.35): a mouse wheel at a point, through the whole input path
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_WHEEL_UP if int(d.get("dir", 1)) > 0 else MOUSE_BUTTON_WHEEL_DOWN
		e.pressed = true
		e.position = Vector2(float(d.get("x", 0)), float(d.get("y", 0)))
		e.global_position = e.position
		var cam_before := view_cam.global_position
		get_viewport().push_input(e)
		var e2 := e.duplicate()
		e2.pressed = false
		get_viewport().push_input(e2)
		return {"ok": true, "moved": snappedf(view_cam.global_position.distance_to(cam_before), 0.001), "over": _over_hud(e.position)}
	elif a == "pose_probe":                            # for tests: a person standing still in a given pose (joints in radians)
		var px := float(d.get("x", 0.0))
		var pz := float(d.get("z", -10.0))
		var pv = spawn("person", Vector3(px, 0, pz), Vector3(px, 0, pz - 5.0))
		pv.preview = true
		pv.heading = float(d.get("heading", 0.0))
		pv.rotation.y = pv.heading
		var jt: Dictionary = d.get("j", {})
		for i in range(2):
			pv.legs[i][0].rotation = Vector3(float(jt.get("hip%d" % i, 0.0)), 0, float(jt.get("hipz%d" % i, 0.0)))
			pv.legs[i][2].rotation.x = float(jt.get("knee%d" % i, 0.0))
			pv.arms[i][0].rotation = Vector3(float(jt.get("sh%d" % i, 0.0)), 0, float(jt.get("shz%d" % i, 0.0)))
			pv.arms[i][2].rotation.x = float(jt.get("el%d" % i, 0.0))
		pv.torso.rotation.x = float(jt.get("torso", 0.0))
		pv.head.rotation.x = float(jt.get("head", 0.0))
		pv.body_root.rotation.x = float(jt.get("body", 0.0))
		pv.body_root.position = Vector3(0, float(jt.get("by", 0.0)), float(jt.get("bz", 0.0)))
		return {"ok": true}
	elif a == "spawn_at":                              # for tests: a visitor from one point to another
		var f: Array = d.get("from", [0, 0])
		var t: Array = d.get("to", [10, 0])
		var sv = spawn(str(d.get("kind", "person")), Vector3(float(f[0]), 0, float(f[1])), Vector3(float(t[0]), 0, float(t[1])))
		if d.has("wait"):                              # stand there for a while, looking at the head camera
			sv.route = [[Vector3(float(t[0]), 0, float(t[1])), float(d["wait"]), 0.0, Vector3(0, 0, 0)], Vector3(float(t[0]) + 40.0, 0, float(t[1]))]
			sv.next_idle = now() + 999.0
		return {"ok": true}
	elif a == "gamewiz":                               # the game wizard, worked from the page of MoveEye (3D-3.41)
		return gamewiz.op(d)
	elif a == "game_debug":                            # 3D-4.x: for tests - results, duel, levels, bots, votes
		return game.debug_info()
	elif a == "gameplus":                              # 3D-4.x: weather change, camouflage things, theft (gameplus.gd, tests)
		return game.plus.op(d)
	elif a == "figuren":                               # 3D-4.12: for tests - figures in a row, a picture, frames per second (figur.gd)
		return preload("res://scripts/figur.gd").op(self, d)
	elif a == "set" or a == "press":
		var c = null
		for x in controls:
			if x.id == cid:
				c = x
		if c == null or c["set"] == null:
			return {"ok": false, "error": "unknown control"}
		_ctl_frame = -1                                 # a button / switch pressed from the page counts like one in the window (one lock)
		if a == "press":
			c["set"].call()
		else:
			var v = d.get("value")
			match c.type:
				"slider":
					v = clamp(float(v), float(c.extra.get("min", -1e9)), float(c.extra.get("max", 1e9)))
				"toggle":
					v = bool(v)
				_:
					v = str(v)
			c["set"].call(v)
		_sync_ui()
	elif a != "get":
		return {"ok": false, "error": "unknown action"}
	return control_info()


func status_text() -> String:
	var h := hour()
	var mwc := "verbunden mit %s" % str(mw.get("device", "MoveEye")) if now() - mw_t < 3.0 else ("MoveEye nicht verbunden" if stream_on else "Senden aus")
	var mww := mw_watchers()
	if not mww.is_empty():                     # 3D-4.9: a second MoveEye only watches (does not steer the head)
		mwc += " · schaut nur zu: " + ", ".join(mww)
	if schnitt != null:
		mwc += schnitt.mw_extra()                 # Aufräumen 2: «Schutz an · Relais …» from MoveEye
	var score := " · Treffer %d von %d Schüssen, %d Punkte" % [hits, shots, points] if rifle_on else ""
	return "%s · %02d:%02d · %s · %s · %.1f °C · Besucher %d%s · %s" % [Worlds.full_name(scene) if Worlds.is_place(scene) and not Worlds.solo(self, scene) else Scenes.name_of(scene), int(h), int(fmod(h, 1.0) * 60), "Nacht" if is_dark() else "Tag", {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(weather, weather), ambient, visitors.get_child_count(), score, mwc] + (" · Update: " + update_info if update_info != "" else "") + (" · " + start_info if start_info != "" else "") + (" · " + game.status() if game != null and game.status() != "" else "") + (" · " + testrun.status() if testrun != null and testrun.status() != "" else "") + (" · " + nacht.status() if nacht != null and nacht.running else "") + (" · " + dev2.status() if dev2 != null and dev2.on else "") + (" · " + recorder.info if recorder != null and recorder.info != "" and (recorder.recording or recorder.playing) else "") + (" · " + life.info if life != null and life.info != "" and (real_weather or daily_life) else "") + (" · " + geo.info if geo != null and geo.busy else "") + (" · " + geo_note if geo_note != "" else "")


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
	"""the window: phone on the left, on the right the panel in the look of the web page of MoveEye (ui_style.gd):
	toolbar (hide, search, groups only, expand all, collapse all), cards, at the bottom «Einfach | Experte»"""
	var layer := CanvasLayer.new()
	add_child(layer)
	ui_layer = layer
	var th: Theme = UI.theme()
	phone = Phone.new()
	phone.main = self
	phone.position = Vector2(0, 0)
	phone.theme = th
	layer.add_child(phone)
	_build_crosshair(layer)
	_build_view_bar(layer, th)
	_build_cpu_pill(layer)
	karte = Karte.new()
	karte.main = self
	karte.theme = th
	karte.visible = false
	layer.add_child(karte)
	dataset = preload("res://scripts/dataset.gd").new()      # Trainingsbilder (3D-3.44)
	dataset.main = self
	add_child(dataset)
	kitrain = preload("res://scripts/kitrain.gd").new()      # «KI trainieren»: pack -> GitHub release «ki-daten» -> workflow
	kitrain.main = self
	add_child(kitrain)
	replay = preload("res://scripts/replay.gd").new()        # Alarm-Rückblick (3D-3.44)
	replay.main = self
	add_child(replay)
	replay.setup(layer)
	planner = preload("res://scripts/planner.gd").new()      # Aufstell-Planer (3D-3.44)
	planner.main = self
	planner.theme = th
	layer.add_child(planner)
	pruef = preload("res://scripts/pruefstand.gd").new()    # Prüfstand (3D-3.49)
	pruef.main = self
	pruef.theme = th
	layer.add_child(pruef)
	var tvl := CanvasLayer.new()                            # the TV mode lies over everything (3D-3.44)
	tvl.layer = 5
	add_child(tvl)
	tv = preload("res://scripts/tv.gd").new()
	tv.main = self
	tv.theme = th
	tvl.add_child(tv)
	gamewiz = preload("res://scripts/gamewiz.gd").new()     # the game wizard (3D-3.41)
	gamewiz.main = self
	gamewiz.theme = th
	layer.add_child(gamewiz)
	abenteuer = preload("res://scripts/bergtal_abenteuer.gd").new()   # Bergtal-Abenteuer (same look as the wizard)
	abenteuer.main = self
	abenteuer.theme = th
	layer.add_child(abenteuer)
	var panel := PanelContainer.new()
	panel.theme = th
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -392
	panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN   # 3D-3.43: if something is too wide it grows to the left, never off the window
	var sb := UI.box(Color(UI.BG, 0.97), UI.LINE, 0, 8, 0)
	sb.border_width_left = 1
	sb.content_margin_left = 10
	sb.content_margin_right = 6
	sb.content_margin_top = 10
	sb.content_margin_bottom = 6
	panel.add_theme_stylebox_override("panel", sb)
	layer.add_child(panel)
	ui_root = panel
	show_btn = UI.icon_button("show", "Bedienfeld zeigen (H)")
	show_btn.theme = th
	show_btn.anchor_left = 1.0
	show_btn.anchor_right = 1.0
	show_btn.offset_left = -48
	show_btn.offset_top = 10
	show_btn.offset_right = -10
	show_btn.offset_bottom = 48
	show_btn.visible = false
	show_btn.pressed.connect(func(): show_panel(true))
	layer.add_child(show_btn)
	var outer := VBoxContainer.new()                      # from 3D-3.7: name, toolbar and the camera pictures stay at the top,
	outer.add_theme_constant_override("separation", 10)  # only the rest scrolls
	panel.add_child(outer)
	var top_box := VBoxContainer.new()
	top_box.add_theme_constant_override("separation", 10)
	top_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.add_child(top_box)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)
	var box_ := VBoxContainer.new()
	ui_box = box_
	box_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box_.add_theme_constant_override("separation", 10)
	scroll.add_child(box_)
	# header: logo, name, version (like the top bar of the page)
	var hdr := HBoxContainer.new()
	hdr.add_theme_constant_override("separation", 8)
	top_box.add_child(hdr)
	var wm = preload("res://scripts/wordmark.gd").new()   # 3D-3.87: the wordmark W6 like on the web page
	if wm.build(44.0):                                   # 3D-4.23: moving like on the web (person, cone, pupil, blink)
		hdr.add_child(wm)
	else:
		wm.free()
		var logo: Control = load("res://scripts/mw_logo.gd").new()  # (fallback) the orange MoveEye symbol
		logo.custom_minimum_size = Vector2(30, 30)
		hdr.add_child(logo)
	var title := Label.new()
	title.text = "Simulator"
	title.add_theme_font_override("font", UI.heading_font())
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", UI.MUT)
	title.size_flags_vertical = Control.SIZE_SHRINK_END
	hdr.add_child(title)
	var ver := UI.small(VERSION)
	ver.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	ver.size_flags_vertical = Control.SIZE_SHRINK_END
	hdr.add_child(ver)
	# toolbar like above the settings of MoveEye
	var tb := HBoxContainer.new()
	ui_tb = tb
	tb.add_theme_constant_override("separation", 6)
	top_box.add_child(tb)
	var hide_b := UI.icon_button("hide", "Bedienfeld ausblenden (H)")
	hide_b.pressed.connect(func(): show_panel(false))
	tb.add_child(hide_b)
	search_in = UI.search_field("Einstellung suchen …")
	search_in.text_changed.connect(_search)
	tb.add_child(search_in)
	# 3D-4.18 (Daniel): same order and look as MoveEye 2.98.46 - «Alle zuklappen · Nur Gruppen · Alle aufklappen»,
	# the button of the current fold state is blue (mixed = none)
	var cb := UI.icon_button("close", "Alle zuklappen")
	cb.pressed.connect(func(): _fold_all("close", true))
	tb.add_child(cb)
	var gb := UI.icon_button("groups", "Nur Gruppen")
	gb.pressed.connect(func(): _fold_all("groups", true))
	tb.add_child(gb)
	var ob := UI.icon_button("open", "Alle aufklappen")
	ob.pressed.connect(func(): _fold_all("open", true))
	tb.add_child(ob)
	_fold_btns = {"close": cb, "groups": gb, "open": ob}
	search_none = UI.small("Kein Treffer")
	search_none.visible = false
	box_.add_child(search_none)
	_mode_row = HBoxContainer.new()                 # 3D-3.94: one small line; 3D-3.90: Einfach | Experte and Kinder | Erwachsene on top (were at the very bottom)
	_mode_row.add_theme_constant_override("separation", 6)
	box_.add_child(_mode_row)
	top_cards.append(_mode_row)
	# Paket nurgruppen (Daniel, 31.10.2026): «Beim Start: Nur Gruppen» right below Einfach | Experte - like MoveEye (530 / 570)
	_sg_cb = CheckButton.new()
	_sg_cb.text = "Beim Start: Nur Gruppen"
	_sg_cb.tooltip_text = "Bei jedem Start zeigen die Einstellungen nur die Gruppen. Aus: Die Menüs sind auf- und zugeklappt, wie du sie verlassen hast."
	_sg_cb.add_theme_font_size_override("font_size", 13)
	_sg_cb.focus_mode = Control.FOCUS_NONE
	_sg_cb.button_pressed = start_groups
	_sg_cb.toggled.connect(set_start_groups)
	box_.add_child(_sg_cb)
	top_cards.append(_sg_cb)
	quick = preload("res://scripts/quick.gd").new()            # 3D-3.86: the quick tiles, at the very top
	quick.main = self
	box_.add_child(quick)
	top_cards.append(quick)
	# connection to MoveEye
	var cn := UI.fold_card(box_, "Verbindung", true, "link")     # from 3D-3.37 it folds; the symbol is green when connected
	fold_bodies.append(cn)
	top_cards.append(cn.get_meta("card"))
	conn_body = cn
	stream_cb = CheckButton.new()
	stream_cb.text = "An MoveEye senden (Port %d)" % stream_port
	stream_cb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stream_cb.add_theme_font_size_override("font_size", 15)
	stream_cb.button_pressed = stream_on
	stream_cb.toggled.connect(func(on): set_stream(on, true); stream_last = on; _settings_dirty = true)   # 3D-3.75: busy -> spare port
	cn.add_child(stream_cb)
	stream_note = UI.small("")
	cn.add_child(stream_note)
	status_label = UI.small("", UI.TXT)
	status_label.add_theme_font_size_override("font_size", 13)
	cn.add_child(status_label)
	# 3D-3.45: tunnel - when the firewall of this PC lets nothing in (no admin rights)
	if OS.get_name() == "Windows":                 # 3D-3.92: the real fix for «MoveEye findet den Simulator nicht»: one firewall rule
		var fwb := Button.new()
		fwb.text = "Windows-Firewall: Simulator freigeben (einmal, fragt nach Adminrechten)"
		fwb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		fwb.tooltip_text = "Erlaubt dem Simulator eingehende Verbindungen im privaten Netz. Danach braucht es keinen Tunnel und keinen Code mehr."
		fwb.pressed.connect(_firewall_allow)
		cn.add_child(fwb)
	var tn := UI.sub_fold(cn, "Tunnel zu MoveEye (Firewall ohne Adminrechte)", tunnel_on)
	tn.set_meta("always", true)                     # 3D-3.46: it has no settings of the list - without this it was always hidden
	sub_bodies.append(tn)
	var tnote := UI.small("Lässt die Firewall dieses PCs MoveEye nicht herein, verbindet sich der Simulator selbst zu MoveEye. Adresse und Code stehen auf der Seite von MoveEye unter Simulator → «Simulator hinter einer Firewall».")
	tnote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tn.add_child(tnote)
	var th_ := LineEdit.new()
	th_.placeholder_text = "Adresse von MoveEye, z. B. 192.168.1.20"
	th_.text = tunnel_host
	tn.add_child(th_)
	var tc_ := LineEdit.new()
	tc_.placeholder_text = "Code (6 Ziffern)"
	tc_.max_length = 6
	tc_.text = tunnel_code
	tn.add_child(tc_)
	var tcb := CheckButton.new()
	tcb.text = "Tunnel verwenden"
	tcb.button_pressed = tunnel_on
	tn.add_child(tcb)
	tunnel_label = UI.small("")
	tunnel_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tn.add_child(tunnel_label)
	var apply_t := func():
		tunnel_host = th_.text.strip_edges().trim_prefix("http://").trim_prefix("https://").get_slice("/", 0).get_slice(":", 0)
		tunnel_code = tc_.text.strip_edges()
		tunnel_on = tcb.button_pressed
		tunnel.host = tunnel_host
		tunnel.code = tunnel_code
		tunnel.set_on(false)
		tunnel.set_on(tunnel_on)
		_settings_dirty = true
	th_.text_submitted.connect(func(_t): apply_t.call())
	th_.focus_exited.connect(apply_t)
	tc_.text_submitted.connect(func(_t): apply_t.call())
	tc_.focus_exited.connect(apply_t)
	# 3D-3.92: saved at once while typing (an update a minute later restarted the simulator before the field was left)
	var keep_t := func(_t):
		tunnel_host = th_.text.strip_edges().trim_prefix("http://").trim_prefix("https://").get_slice("/", 0).get_slice(":", 0)
		tunnel_code = tc_.text.strip_edges()
		_save_settings()
	th_.text_changed.connect(keep_t)
	tc_.text_changed.connect(keep_t)
	tcb.toggled.connect(func(_v): apply_t.call())
	# camera pictures
	# 3D-3.50: order by logic - first the connection, then the cameras (still visible while searching: not in top_cards)
	var cm := UI.fold_card(box_, "Kameras", true, "camera")
	fold_bodies.append(cm)
	cam_body = cm
	cam_card = cm.get_meta("card")
	box_.move_child(cam_card, conn_body.get_meta("card").get_index() + 1)
	cam_float = VBoxContainer.new()
	cam_float.theme = th
	cam_float.visible = false
	cam_float.add_theme_constant_override("separation", 0)
	cam_float.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var grip := PanelContainer.new()
	grip.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.92), UI.LINE, 8, 4, 1))
	grip.mouse_default_cursor_shape = Control.CURSOR_MOVE
	grip.tooltip_text = "Kamerabilder verschieben: hier ziehen"
	var gl := UI.small("✥ Ziehen zum Verschieben · H = Bedienfeld")
	gl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grip.add_child(gl)
	grip.gui_input.connect(_cam_float_input)
	cam_float.add_child(grip)
	layer.add_child(cam_float)
	prev0 = TextureRect.new()
	prev0.texture = vps[0].get_texture()
	prev0.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev0.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prev0.custom_minimum_size = Vector2(300, 169)
	cm.add_child(prev0)
	var row := HBoxContainer.new()
	cm.add_child(row)
	prev1 = TextureRect.new()
	prev1.texture = vps[1].get_texture()
	prev1.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev1.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prev1.custom_minimum_size = Vector2(146, 82)
	row.add_child(prev1)
	prevt = TextureRect.new()
	prevt.texture = th_preview
	prevt.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prevt.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prevt.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	prevt.custom_minimum_size = Vector2(146, 112)
	row.add_child(prevt)
	# tools: MoveEye on this PC, map, phone
	var tl := UI.fold_card(box_, "Testen", true, "tools")      # 3D-3.90: everything that measures or tests MoveEye in one card
	fold_bodies.append(tl)
	tools_body = tl
	top_cards.append(tl.get_meta("card"))
	mwpc_btn = Button.new()
	mwpc_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mwpc_btn.pressed.connect(func(): mwpc.toggle())
	UI.primary(mwpc_btn)
	tl.add_child(mwpc_btn)
	mwpc_label = UI.small("")
	tl.add_child(mwpc_label)
	var tl_main := tl                                # 3D-3.86: the rest in folds - tests for MoveEye, training pictures, more
	tl = UI.sub_fold(tl_main, "Erkennung messen (Testlauf, Prüfstand, blinde Flecken)", true)
	tl.set_meta("always", true)
	sub_bodies.append(tl)
	testen_measure = tl                              # 3D-4.x: the group «Testlauf» lives here now (one place for testing)
	testen_rec = UI.sub_fold(tl_main, "Aufnahme: Besuch aufnehmen und genau gleich abspielen", false)
	testen_rec.set_meta("always", true)
	sub_bodies.append(testen_rec)
	var trh := HBoxContainer.new()
	trh.add_theme_constant_override("separation", 6)
	tl.add_child(trh)
	var trp := OptionButton.new()
	for p_ in ["quick", "standard", "night", "hard", "wetter"]:      # real-wetter: + «Wetter physikalisch»
		trp.add_item(str(TestrunS.PLANS[p_]["name"]).get_slice(" (", 0) + " · " + str(int(round(TestrunS.DAUER[p_] / 30.0)) / 2.0).trim_suffix(".0") + " Min.")
	trp.select(0)
	trh.add_child(trp)
	var trb := Button.new()
	trb.text = "Testlauf starten"
	trb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trb.pressed.connect(func():
		var r_: String = testrun.start(["quick", "standard", "night", "hard", "wetter"][trp.selected])
		if r_ != "":
			start_info = r_)
	trh.add_child(trb)
	var bmb := Button.new()
	bmb.text = "Blinde Flecken: Person rund um MoveEye aufstellen"
	bmb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bmb.pressed.connect(func():
		var r2: Dictionary = blindmap.start({})
		if not bool(r2.get("ok", true)):
			start_info = "Blinde Flecken: " + str(r2.get("error", "")))
	tl.add_child(bmb)
	var psb := Button.new()
	psb.text = "Prüfstand: mehrere Testläufe, Ergebnis für GitHub"
	psb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	psb.pressed.connect(func(): pruef.open(not pruef.visible))
	tl.add_child(psb)
	tl = UI.sub_fold(tl_main, "Geräusche (Klatschschalter, Gesundheit, Lärm)", false)   # 3D-3.98
	tl.set_meta("always", true)
	sub_bodies.append(tl)
	tl.add_child(UI.small("Das Geräusch kommt von der Person im Bett, sonst vom nächsten Besucher, sonst 2 m vor MoveEye. MoveEye braucht dafür «Klatschschalter» bzw. «Gesundheit» – beim klingelnden Wecker heisst Klatschen schlummern."))
	var sgr := GridContainer.new()
	sgr.columns = 3
	tl.add_child(sgr)
	for b_ in [["Klatschen 2×", "clap", 2], ["Klatschen 3×", "clap", 3], ["Klatschen 4×", "clap", 4], ["Niesen", "sneeze", 1], ["Reden", "voice", 1], ["Rufen", "shout", 1]]:
		var snb := Button.new()
		snb.text = b_[0]
		snb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		snb.pressed.connect(func(): emit_sound(b_[1], b_[2]))
		sgr.add_child(snb)
	testen_stoer = UI.sub_fold(tl_main, "Störungen (Servos, Unterspannung, I2C – reagiert MoveEye richtig?)", false)   # 30.10.2026 (simint.gd)
	testen_stoer.set_meta("always", true)
	sub_bodies.append(testen_stoer)
	testen_stoer.add_child(UI.small("Wie bei echter Hardware: MoveEye stoppt die Servos, meldet die Störung im Fehlerspeicher (Servo-Diagnose) und braucht bei Treiber-Fehlern «Freigeben»."))
	simint.add_info(testen_stoer, UI)
	testen_einbruch = UI.sub_fold(tl_main, "Einbruch-Abläufe (auskundschaften, ablenken, stehlen – wann warnt MoveEye?)", false)
	testen_einbruch.set_meta("always", true)
	sub_bodies.append(testen_einbruch)
	einbruch.add_info(testen_einbruch, UI)
	tl = UI.sub_fold(tl_main, "Diebstahlschutz prüfen (Referenz-Scan, Sabotage, Überraschung)", false)
	tl.set_meta("always", true)
	sub_bodies.append(tl)
	# 3D-3.71: the reference scan of MoveEye, started from here
	var rsh := HBoxContainer.new()
	rsh.add_theme_constant_override("separation", 6)
	tl.add_child(rsh)
	for b_ in [["MoveEye: Referenz-Scan", "refscan"], ["Mit Referenz vergleichen", "refcompare"]]:
		var rb := Button.new()
		rb.text = b_[0]
		rb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		rb.tooltip_text = "MoveEye fährt mit dem Kopf alle Richtungen ab: Referenz-Fotos aufnehmen bzw. vergleichen (Bericht in MoveEye unter Werkzeuge → Referenz-Scan)"
		rb.pressed.connect(mw_request.bind(b_[1]))
		rsh.add_child(rb)
	var ntb := Button.new()                          # 3D-3.72
	ntb.text = "Referenz-Scan: am Tag aufnehmen, in der Nacht vergleichen"
	ntb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ntb.pressed.connect(ref_night_test)
	tl.add_child(ntb)
	var gsb := Button.new()                          # 3D-3.98: theft with the GPS module
	gsb.text = "GPS: MoveEye wird weggetragen"
	gsb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	gsb.tooltip_text = "Die GPS-Position wandert mit 1.6 m/s weg (wie zu Fuss). MoveEye braucht «GPS-Modul» und «Diebstahl-Alarm» und muss scharf sein. Nochmals drücken = zurückstellen."
	gsb.pressed.connect(func():
		gps_steal(gps_steal_t <= 0.0)
		gsb.text = "GPS: zurückstellen" if gps_steal_t > 0.0 else "GPS: MoveEye wird weggetragen")
	tl.add_child(gsb)
	# 3D-4.7 («Dinge wegnehmen zusammenlegen»): ONE list of the things to take away - «Bewachte Sachen» in «Gegenstände»
	var pgb := Button.new()
	pgb.text = "→ Bewachte Sachen: Velo, Zelt, Tisch, Kühlbox, Grill wegnehmen – merkt MoveEye, dass etwas fehlt?"
	pgb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pgb.pressed.connect(func(): inventar.open_sec("guard"))   # 3D-4.22: window «Gegenstände», part «Bewachte Sachen»
	tl.add_child(pgb)
	tl.add_child(UI.small("Sabotage-Test für den Diebstahlschutz von MoveEye (scharf schalten):"))
	var sg := HBoxContainer.new()
	sg.add_theme_constant_override("separation", 6)
	tl.add_child(sg)
	for b2 in [["Kamera abdecken", "cover"], ["Kopf wegdrehen", "turn"], ["Alles normal", "off"]]:
		var sb_ := Button.new()
		sb_.text = b2[0]
		sb_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sb_.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		sb_.pressed.connect(_sabotage_btn.bind(str(b2[1])))
		sg.add_child(sb_)
	refscan_label = UI.small("")
	tl.add_child(refscan_label)
	tl.add_child(UI.small("Überraschung jetzt auslösen (bewertet MoveEye; nachts von selbst: Wetter → Überraschungsnacht):"))
	var sug := GridContainer.new()                   # 3D-3.75
	sug.columns = 3
	sug.add_theme_constant_override("h_separation", 6)
	sug.add_theme_constant_override("v_separation", 6)
	tl.add_child(sug)
	for kk in surprise.KINDS + [["morning", "Bewertung jetzt"]]:
		var ub := Button.new()
		ub.text = kk[1]
		ub.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var key_: String = kk[0]
		ub.pressed.connect(func(): surprise.morning() if key_ == "morning" else surprise.start(key_))
		sug.add_child(ub)
	surprise_label = UI.small("")
	tl.add_child(surprise_label)
	tl = UI.sub_fold(tl_main, "Trainingsbilder für eine eigene KI", false)
	testen_train = tl
	tl.set_meta("always", true)
	sub_bodies.append(tl)
	var dsr := HBoxContainer.new()                   # 3D-3.74: a training set for an own AI model
	dsr.add_theme_constant_override("separation", 6)
	tl.add_child(dsr)
	var dsn := OptionButton.new()
	for n_ in [200, 500, 1000, 2000]:
		dsn.add_item("%d Bilder" % n_)
	dsn.select(1)
	dsr.add_child(dsn)
	var dsb := Button.new()
	dsb.text = "Trainingspaket (YOLO) machen"
	dsb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dsb.tooltip_text = "Bilder mit Rahmen für ein eigenes KI-Modell: viele Szenen, Tag, Nacht, Regen, Nebel, Schnee, Menschen und Tiere. ZIP auf den Schreibtisch."
	dsb.pressed.connect(func():
		if dataset.busy:
			dataset.stop()
		else:
			dataset.export_pack([200, 500, 1000, 2000][dsn.selected], true))
	dsr.add_child(dsb)
	ds_label = UI.small("")
	tl.add_child(ds_label)
	kitrain.build(tl, dsn)                           # Vielfalt normal / hoch, «KI trainieren» (kitrain.gd)
	var kdr := HBoxContainer.new()                   # «KI-Daten aufräumen» (kidaten.gd)
	kdr.add_theme_constant_override("separation", 6)
	tl.add_child(kdr)
	var kdl := UI.small(preload("res://scripts/kidaten.gd").summary())
	kdl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kdl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var kdb := Button.new()
	kdb.text = "Alte KI-Daten löschen"
	kdb.tooltip_text = "Löscht alle Trainingspakete ausser dem neuesten (Ordner und ZIP). Das KI-Modell bleibt."
	kdb.pressed.connect(func():
		if dataset.busy or kitrain.running:
			kdl.text = "Gerade beschäftigt – später nochmals."
			return
		var KD = preload("res://scripts/kidaten.gd")
		var r: Dictionary = KD.aufraeumen(true, str(dataset.last_pack.get("dir", "")).get_file())
		kdl.text = "Gelöscht: %d Pakete (%.0f MB) · %s" % [int(r["deleted"]), float(r["freed_mb"]), KD.summary()])
	kdr.add_child(kdb)
	kdr.add_child(kdl)
	tl = UI.sub_fold(tl_main, "Mehr: Aufstellen, Erkunden, Handy-Simulator", false)
	tl.set_meta("always", true)
	sub_bodies.append(tl)
	var plb := Button.new()
	plb.text = "Aufstell-Planer: Wo soll MoveEye hin?"
	plb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	plb.pressed.connect(func(): planner.open(not planner.visible))
	tl.add_child(plb)
	var exb := Button.new()                         # 3D-3.55: explore with the rover
	exb.text = "Erkunden mit dem Rover (Tastatur, Maus, Touch, Controller)"
	exb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	exb.tooltip_text = "Mit dem Rover durch die Gegend fahren: W A S D / Pfeile, grüner Stick, oder ein Game-Controller (auch Bluetooth; Start = ein / aus). Esc beendet."
	exb.pressed.connect(func(): explore.set_on(not explore.on))
	tl.add_child(exb)
	var pv := Button.new()
	pv.text = "Handy- / Tablet-Simulator (P)"
	pv.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pv.pressed.connect(_toggle_phone)
	tl.add_child(pv)
	var fbb := Button.new()                         # MoveEye 2.98.33: feedback to the developer (feedback.gd)
	fbb.text = "Rückmeldung an den Entwickler"
	fbb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fbb.tooltip_text = "Fehler, Wunsch, Lob oder Frage – geht über das verbundene MoveEye anonym an den Entwickler."
	fbb.pressed.connect(_feedback_open)
	tl.add_child(fbb)
	# the settings of the simulator: one card per group (with a symbol), parts inside (the same list the page of Motion
	# Watch shows, in the same order - GROUPS / PLACE)
	var groups := {}
	var subs := {}
	var fine_folds := {}
	for c in controls:
		if c.extra.get("hide", false) or c.extra.get("wiz", false) or c.extra.get("devwin", false):
			continue                                     # 3D-3.90: only for MoveEye (the web page), not in the window; 3D-4.7: «wiz» = only in the game assistant; «devwin»: in the window «Mehr → Entwickler» (tab «Schalter» / «Spieltest»)
		if c.group == "Testen" and testen_measure != null:   # 3D-4.x: into the card «Testen» (no own card «Testlauf» any more)
			if c.id in ["testrun_plan", "testrun_start"]:
				continue                                 # the card has its own row «plan + Testlauf starten»
			var tgt: VBoxContainer = testen_rec if c.id.begins_with("rec_") else (testen_stoer if c.id.begins_with("stoer_") and testen_stoer != null else testen_measure)
			if c.id.begins_with("einbruch_") and testen_einbruch != null:
				tgt = testen_einbruch

			var k0 := ui_items.size()
			_ui_control(tgt, c)
			for i in range(k0, ui_items.size()):
				ui_items[i][3] = tools_body
				ui_items[i].append(tgt)
			continue
		if not groups.has(c.group):
			var ic := ""
			for g in GROUPS:
				if g[0] == c.group:
					ic = g[1]
			groups[c.group] = UI.fold_card(box_, c.group, c.group in ["Szene", "Besuch"], ic)
			group_bodies[c.group] = groups[c.group]
			fold_bodies.append(groups[c.group])
			setting_bodies.append(groups[c.group])
		if c.group == "Besuch" and str(c.extra.get("sub", "")) != "Vorlagen" and not subs.has("Besuch/Besucher hinsetzen"):
			# after «Vorlagen»: the pictures of the visitors, people and animals apart (3D-3.38)
			var vs := UI.sub_fold(groups[c.group], "Besucher hinsetzen", true)
			vs.set_meta("always", true)
			sub_bodies.append(vs)
			subs["Besuch/Besucher hinsetzen"] = vs
			var ivb := Button.new()                  # 3D-3.86: all people, animals and things in the inventory
			ivb.text = "«Gegenstände» öffnen"
			ivb.tooltip_text = "Zelt, Auto, bewachte Sachen, Menschen, Tiere und alle 80 Dinge der KI"
			ivb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			UI.primary(ivb)
			ivb.pressed.connect(func(): inventar.toggle())
			vs.add_child(ivb)
			vs.add_child(UI.small("Bild in die Welt ziehen – oder anklicken und dann in die Welt klicken. Die Knöpfe weiter unten schicken Besuch, der von selbst daherkommt."))
		var card_body: VBoxContainer = groups[c.group]
		var target: VBoxContainer = card_body
		var sub := str(c.extra.get("sub", ""))
		var to_fine: bool = c.extra.get("expert", false) and c.group != "Entwickler"
		if sub == "Feineinstellungen":                    # 3D-4.22: a part named «Feineinstellungen» = the one fold of the card (not two)
			sub = ""
			to_fine = true
		if sub != "":
			var key: String = c.group + "/" + sub
			if not subs.has(key):
				subs[key] = UI.sub_fold(card_body, sub, sub in ["Vorlagen", "Menschen schicken", "Tiere schicken", "Runde"])
				sub_bodies.append(subs[key])
			target = subs[key]
		# 3D-4.21 (Menü 2, same rule as MoveEye): «Einfach» shows the main switches, the rest sits in a closed «Feineinstellungen»
		var folded := false
		if to_fine:
			var fk := str(target.get_instance_id())
			if not fine_folds.has(fk):
				var fb := UI.sub_fold(target, "Feineinstellungen", false)
				if target != card_body:
					fb.set_meta("outer", target)
				fine_folds[fk] = fb
				sub_bodies.append(fb)
				fine_bodies.append(fb)
			target = fine_folds[fk]
			folded = true
		var n0 := ui_items.size()
		_ui_control(target, c)
		for i in range(n0, ui_items.size()):
			ui_items[i][3] = card_body
			ui_items[i].append(target)
			if folded:
				ui_items[i][2] = false                     # not hidden in «Einfach» - folded
	for fb in fine_folds.values():                     # «Feineinstellungen» last in its part / card
		var w: Control = fb.get_meta("wrap")
		w.get_parent().move_child(w, -1)
	if groups.has("Entwickler"):
		# 3D-4.22 (Angleichen, Daniel 30.10.2026): «Entwickler» like MoveEye - shown when MoveEye's «Entwickler-Bereich» is on
		# (dev_area, sent by MoveEye), no longer tied to «Experte». Paket «Entwickler zusammenlegen»: the card has only the
		# button «Entwickler-Fenster öffnen» (dev_open); «Diagnose-Paket» is in the window (devtool_schalter.gd); only the owner
		dev_body = groups["Entwickler"]
	update_btn = Button.new()
	update_btn.text = "Nach Updates suchen (jetzt %s)" % VERSION
	update_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	update_btn.pressed.connect(check_updates)
	(subs.get("System/Updates", tl) as Control).add_child(update_btn)
	if testen_measure != null:
		testrun.add_info(testen_measure, UI)          # progress and result of the test run (card «Testen»)
		nacht.add_info(testen_measure, UI)            # Nacht-Testlauf: progress, «abbrechen»
	elif groups.has("Testen"):
		testrun.add_info(groups["Testen"], UI)
	if subs.has("Licht & Ton/Status-LED & Tasten") and statusled != null:   # 3D-4.22: the rules of the buttons are in MoveEye - hint + link
		statusled.add_info(subs["Licht & Ton/Status-LED & Tasten"], UI)
	if subs.has("Sensoren/Bewegungsmelder (PIR)"):    # real-pir-ton: state, reach, triggers (pir.gd)
		pir.add_info(subs["Sensoren/Bewegungsmelder (PIR)"], UI)
	if subs.has("Licht & Ton/Mikrofon"):              # real-pir-ton: level, background, the loudest sources (mikrofon.gd)
		mikro.add_info(subs["Licht & Ton/Mikrofon"], UI)
	if subs.has("Sensoren/Strom"):                    # Simulator-Werte: what goes to MoveEye (power.gd)
		simwerte.add_info(subs["Sensoren/Strom"], UI)
	if subs.has("Kamerabild/Wie echt"):              # 3D-3.94: what the real look adjustment does
		real_label = UI.small("")
		real_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		subs["Kamerabild/Wie echt"].add_child(real_label)
	if subs.has("Spiel/Runde"):
		game.add_info(subs["Spiel/Runde"], UI)        # address, QR code and players of the game
	elif groups.has("Spiel"):
		game.add_info(groups["Spiel"], UI)
	var keys := UI.fold_card(box_, "Tasten", false, "keys")
	fold_bodies.append(keys)
	info_label = UI.small("Maus: links ziehen = verschieben · rechts ziehen = drehen · Rad = zoomen (Shift + Rad: Tempo von W A S D) · mittlere Taste oder Alt + rechts = umschauen · Doppelklick = hinfliegen · Besucher anklicken = auswählen, ziehen = tragen.  Tasten: W A S D Q E fliegen (Shift schneller) · 1 / 2 Kamera · 3 Wärmebild · 0 frei · F folgen · Entf entfernen · Esc abwählen · H Bedienfeld · P Handy / Tablet · K Karte · G Gewehr (Linksklick = Schuss)")
	keys.add_child(info_label)
	expert_cards.append(keys.get_meta("card"))
	top_cards.append(keys.get_meta("card"))
	mehr = preload("res://scripts/mehr.gd").new()      # 3D-4.2x: card «Mehr» like MoveEye (Hilfe, Rundgang, Diagnose, Protokoll, Ansicht, Rückmeldung, Über)
	mehr.main = self
	add_child(mehr)
	mehr.build(box_)
	# Simple | Expert and Kinder | Erwachsene: on top, next to the search (3D-3.90)
	var se := UI.segment("Einfach", "Experte", not ui_simple, func(expert): set_simple(not expert), true)
	simple_seg = se
	se.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_mode_row.add_child(se)
	kids_seg = UI.segment("Kinder", "Erwachsene", not kids_on, func(adult): _kids_switch(adult), true)   # 3D-3.69
	kids_seg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_mode_row.add_child(kids_seg)
	se.tooltip_text = "Einfach: das Wichtigste (Szene, Zeit, Wetter, Besuch, Testen, Spiel-Assistent). «Experte» zeigt alle."
	simple_note = UI.small("")                      # 3D-3.94: the explanation as a tooltip, no line of its own
	simple_note.visible = false
	_apply_simple()
	_sync_ui()
	_fold_setup()                                      # nurgruppen: the own open / closed state, then «Nur Gruppen» on start
	await _make_thumbs()
	kids = preload("res://scripts/kids.gd").new()       # 3D-3.69: the panel of the «Kinder» mode (after the pictures)
	kids.main = self
	box_.add_child(kids)
	box_.move_child(kids, 0)
	_apply_kids()


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
	"""which of the three fold buttons matches what is open now ("" = mixed)"""
	var all_open := true
	var all_closed := true
	var groups := true
	for b in fold_bodies:
		if not is_instance_valid(b) or not b.get_parent().visible:
			continue
		var o: bool = b.visible
		all_open = all_open and o
		all_closed = all_closed and not o
		groups = groups and o == (not b in setting_bodies and b.get_meta("title", "") in ["Kameras"])
	for sb in sub_bodies:
		if not is_instance_valid(sb) or not sb.has_meta("fold"):
			continue
		var so: bool = (sb.get_meta("fold") as Control).visible
		all_open = all_open and so
		all_closed = all_closed and not so
	if all_closed:
		return "close"
	if all_open:
		return "open"
	return "groups" if groups else ""


func _fold_paint() -> void:
	"""light the button of the current fold state (called a few times a second, repaints only on a change)"""
	if _fold_btns.is_empty():
		return
	var st := _fold_state()
	if st == _fold_lit:
		return
	_fold_lit = st
	for k in _fold_btns:
		var b: Button = _fold_btns[k]
		for n in ["normal", "hover", "pressed"]:
			if k == st:
				b.add_theme_stylebox_override(n, UI.box(UI.ACC, UI.ACC, 10))
			else:
				b.remove_theme_stylebox_override(n)


func _fold_all(how: String, own := false) -> void:
	"""own: pressed by the user (the three buttons) - kept as the own state like on the page of MoveEye; the start view is not"""
	_fold_lit = "-"
	for b in fold_bodies:
		var open: bool = how == "open" or (how == "groups" and not b in setting_bodies and b.get_meta("title") in ["Kameras"])   # 3D-4.12 (Daniel): «Verbindung» stays closed
		UI.set_open(b, open)
	if how != "groups":
		for sb in sub_bodies:
			UI.set_sub_open(sb, how == "open")
	if own:
		for b in fold_bodies + sub_bodies:
			_fold_keep(b)


# ---- Paket nurgruppen (Daniel, 31.10.2026): «Beim Start: Nur Gruppen» ------------------------------------------------------
# Every start shows the settings as «Nur Gruppen» (_fold_all("groups"), not saved). What the user opens / closes himself is kept in
# fold_mem (simulator_settings.json; before, the cards always started as built). Switch off: everything as the user left it.
var start_groups := true              # the switch, factory: on (saved)
var fold_mem := {}                    # the own state: {"c:Karte": true, "s:Karte/Teil": false} (saved)
var _fold_init := {}                  # how the panel was built (for cards the user never touched)
var _sg_cb: CheckButton


func _fold_key(b: Control) -> String:
	if b.has_meta("fold"):                             # a part (sub_fold): its card in front, the names are not unique
		var w: Node = b.get_meta("wrap")
		var par: Node = w.get_parent() if w != null else null
		return "s:%s/%s" % [str(par.get_meta("title", "")) if par != null else "", str(b.get_meta("title", ""))]
	return "c:" + str(b.get_meta("title", ""))


func _fold_is_open(b: Control) -> bool:
	return (b.get_meta("fold") as Control).visible if b.has_meta("fold") else b.visible


func _fold_put(b: Control, open: bool) -> void:
	if b.has_meta("fold"):
		UI.set_sub_open(b, open)
	else:
		UI.set_open(b, open)


func _fold_keep(b: Control) -> void:
	if is_instance_valid(b):
		fold_mem[_fold_key(b)] = _fold_is_open(b)
		_settings_dirty = true


func _fold_setup() -> void:
	"""after building the panel: remember how it was built, follow the clicks on the headings, own state, then the start view"""
	for b in fold_bodies + sub_bodies:
		if not is_instance_valid(b):
			continue
		_fold_init[_fold_key(b)] = _fold_is_open(b)
		var hdr: Node = null
		if b.has_meta("fold"):
			var w: Node = b.get_meta("wrap")
			hdr = w.get_child(1) if w != null and w.get_child_count() > 1 else null
		elif b.get_parent() != null:
			hdr = b.get_parent().get_child(0)
		if hdr is Button:
			(hdr as Button).pressed.connect(func(): _fold_keep(b))   # after the heading's own handler: the new state
	_fold_own()
	if start_groups:
		_fold_all("groups")


func _fold_own() -> void:
	"""every card and part as the user left it (cards he never touched: as built)"""
	_fold_lit = "-"
	for b in fold_bodies + sub_bodies:
		if is_instance_valid(b):
			var k := _fold_key(b)
			if fold_mem.has(k) or _fold_init.has(k):
				_fold_put(b, bool(fold_mem.get(k, _fold_init.get(k))))


func set_start_groups(on: bool) -> void:
	start_groups = on
	_settings_dirty = true
	if _sg_cb != null and _sg_cb.button_pressed != on:
		_sg_cb.set_pressed_no_signal(on)
	if on:
		_fold_all("groups")
	else:
		_fold_own()


func _search(q: String) -> void:
	"""type into the search field: only the matching settings stay, their cards open; empty = everything as before"""
	q = q.strip_edges().to_lower()
	var any := false
	for c in top_cards:
		c.visible = q == "" and not (c in expert_cards and ui_simple)
	var hit_bodies := {}
	for it in ui_items:
		var show_it: bool = (q == "" or str(it[1]).to_lower().contains(q)) and not (ui_simple and it[2] and q == "") and not _dev_hidden(it)
		it[0].visible = show_it
		if q != "" and show_it:
			hit_bodies[it[3]] = true
			any = true
			if it.size() > 4 and it[4] != it[3]:
				UI.set_sub_open(it[4], true)
				if it[4].has_meta("outer"):
					UI.set_sub_open(it[4].get_meta("outer"), true)
	for b in setting_bodies:
		b.get_meta("card").visible = q == "" or hit_bodies.has(b)
		if q != "":
			UI.set_open(b, hit_bodies.has(b))
	search_none.visible = q != "" and not any
	if q == "":
		_apply_simple()


func _kids_switch(adult: bool) -> void:
	"""the switch «Kinder | Erwachsene»: to the children at once, back to the adults only with a little sum"""
	if not adult:
		kids_on = true
		_settings_dirty = true
		_apply_kids()
		return
	if not kids_on:
		return
	ask_adult(func(ok):
		if ok:
			kids_on = false
			_settings_dirty = true
			_apply_kids()
		else:
			kids_seg.get_meta("paint").call(false))


func _apply_kids() -> void:
	"""Kinder: only the panel with the picture buttons and the switch; no search, no tool bar. Erwachsene: as before."""
	if ui_box == null or kids == null:
		return
	if kids_on:
		for c in ui_box.get_children():
			c.visible = c == kids or c == kids_seg or c == _mode_row
		if simple_seg != null:
			simple_seg.visible = false
		kids._build()
		var sc := ui_box.get_parent()
		if sc is ScrollContainer:
			(sc as ScrollContainer).scroll_vertical = 0      # start at the top with the marmot
	else:
		kids.visible = false
		for c in ui_box.get_children():
			if c != kids and c != search_none:
				c.visible = true
		if simple_seg != null:
			simple_seg.visible = true
		var keep := kids_on
		kids_on = false
		_apply_simple()
		kids_on = keep
	if ui_tb != null:
		ui_tb.visible = not kids_on
	if toolbar != null:
		toolbar.visible = not kids_on
	if kids_seg != null and kids_seg.has_meta("paint"):
		kids_seg.get_meta("paint").call(not kids_on)


var _adult_box: Control = null


func ask_adult(done: Callable) -> void:
	"""a little sum for the adults (7 × 8 = ?) before leaving the «Kinder» mode (3D-3.95: can be switched off)"""
	if not kids_ask:
		done.call(true)
		return
	if _adult_box != null and is_instance_valid(_adult_box):
		_adult_box.queue_free()
	var a := randi_range(6, 9)
	var b := randi_range(6, 9)
	var pc := PanelContainer.new()
	pc.theme = ui_root.theme
	pc.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ACC, 14, 16, 2))
	ui_layer.add_child(pc)
	_adult_box = pc
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	pc.add_child(v)
	v.add_child(UI.heading("Frage für Erwachsene"))
	var q := Label.new()
	q.text = "Wie viel ist %d × %d?" % [a, b]
	q.add_theme_font_size_override("font_size", 22)
	v.add_child(q)
	var le := LineEdit.new()
	le.placeholder_text = "Antwort"
	le.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_NUMBER
	v.add_child(le)
	var msg := UI.small("")
	v.add_child(msg)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	v.add_child(h)
	var ok_b := Button.new()
	ok_b.text = "Weiter"
	UI.primary(ok_b)
	var no_b := Button.new()
	no_b.text = "Abbrechen"
	for x in [ok_b, no_b]:
		x.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		x.custom_minimum_size = Vector2(0, 40)
		h.add_child(x)
	var check := func(_t = null):
		if le.text.strip_edges() == str(a * b):
			pc.queue_free()
			done.call(true)
		else:
			msg.text = "Leider falsch – noch einmal."
			le.text = ""
	ok_b.pressed.connect(check)
	le.text_submitted.connect(check)
	no_b.pressed.connect(func():
		pc.queue_free()
		done.call(false))
	pc.custom_minimum_size = Vector2(320, 0)
	await get_tree().process_frame
	var vs := get_viewport().get_visible_rect().size
	pc.position = (vs - pc.size) / 2.0
	le.grab_focus()


func set_simple(on: bool) -> void:
	ui_simple = on
	_settings_dirty = true
	_apply_simple()


func _apply_simple() -> void:
	"""Simple: settings marked "expert" are hidden (and cards that would be empty)"""
	var counts := {}
	for it in ui_items:
		var vis: bool = not (ui_simple and it[2])
		if dev_body != null and it[3] == dev_body:
			vis = _dev_card_ok()                           # 3D-4.22: «Entwickler» with MoveEye's switch, also in «Einfach» (+ only the owner)
		elif vis and _dev_hidden(it):
			vis = false                                    # 3D-4.28: «only» (e.g. «Standort im Ferienpark» only in that scene)
		it[0].visible = vis
		if vis:
			counts[it[3]] = true
	for b in setting_bodies:
		b.get_meta("card").visible = counts.has(b)
	var sub_counts := {}
	for it in ui_items:
		if it.size() > 4 and it[0].visible:
			sub_counts[it[4]] = true
			if (it[4] as Control).has_meta("outer"):          # 3D-4.22: a part with only «Feineinstellungen» stays visible
				sub_counts[it[4].get_meta("outer")] = true
	for sb in sub_bodies:
		sb.get_meta("wrap").visible = sub_counts.has(sb) or sb.has_meta("always")
	for c in expert_cards:
		c.visible = not ui_simple
	for fb in fine_bodies:                             # 3D-4.21: closed in «Einfach», open in «Experte»
		if is_instance_valid(fb):
			UI.set_sub_open(fb, not ui_simple)
	if simple_note != null:
		simple_note.visible = false                    # 3D-3.94: tooltip of the switch instead
	if kids_on and kids != null:
		_apply_kids()


# ---- the pictures of the visitors: click to choose, drag into the world ------------------------------------------------
var thumbs := {}                      # kind -> ImageTexture
var thumb_rects := {}
var palette_items := {}
var thumb_btns: Array = []            # [button, visitor kind]: the picture comes when it is drawn
var drag_kind := ""


func _palette_item(kind: String, name_: String) -> Control:
	var pc := PanelContainer.new()
	pc.custom_minimum_size = Vector2(72, 88)
	pc.tooltip_text = name_ + ": in die Welt ziehen, oder anklicken und in die Welt klicken"
	pc.mouse_default_cursor_shape = Control.CURSOR_DRAG
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(v)
	var tr := TextureRect.new()
	tr.custom_minimum_size = Vector2(60, 54)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tr)
	var l := Label.new()
	l.text = name_
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", 11)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART     # 3D-3.43: long names wrap - before they pushed the panel over the right edge
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(l)
	thumb_rects[kind] = tr
	palette_items[kind] = pc
	pc.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and not ev.pressed and drag_kind == "":
			place_kind = "" if place_kind == kind else kind
			_paint_palette())
	var drag_fn := func(_pos):
		drag_kind = kind
		var pv := TextureRect.new()
		pv.texture = thumbs.get(kind)
		pv.custom_minimum_size = Vector2(72, 66)
		pv.size = Vector2(72, 66)
		pv.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pv.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pv.modulate = Color(1, 1, 1, 0.85)
		pc.set_drag_preview(pv)
		return {"visitor": kind}
	pc.set_drag_forwarding(drag_fn, func(_p, _d): return false, func(_p, _d): pass)
	_paint_palette.call_deferred()
	return pc


func _paint_palette() -> void:
	for k in palette_items:
		var on: bool = k == place_kind
		palette_items[k].add_theme_stylebox_override("panel", UI.box(UI.PANEL if not on else UI.ACC.darkened(0.55), UI.ACC if on else UI.LINE, 10, 4, 2 if on else 1))


func _notification(what: int) -> void:
	if what == NOTIFICATION_DRAG_END and drag_kind != "":
		var k := drag_kind
		drag_kind = ""
		var mp := get_viewport().get_mouse_position()
		var over_ui: bool = (ui_root != null and ui_root.visible and ui_root.get_global_rect().has_point(mp)) or (phone != null and phone.visible and phone.get_global_rect().has_point(mp))
		if not over_ui:
			_place_at(k, mp)


func _make_thumbs() -> void:
	"""a little moving picture of every visitor (3D-3.24): each walks on the spot in a small world of its own; only
	the pictures that can be seen are drawn again, about 12 times a second"""
	var sizes := {"person": 1.9, "child": 1.3, "jogger": 1.9, "deer": 1.7, "boar": 1.1, "fox": 0.8, "dog": 0.9, "cat": 0.6, "badger": 0.6, "hare": 0.65, "hedgehog": 0.32,
			"wolf": 1.1, "marten": 0.38, "squirrel": 0.3, "cyclist": 1.9, "stroller": 1.9, "courier": 1.9, "police": 1.9, "drunk": 1.9,
			"cow": 1.7, "sheep": 0.9, "horse": 2.0, "chamois": 1.1, "ibex": 1.3, "lynx": 0.9}
	for k in VISITOR_LIST:
		var vp := SubViewport.new()
		vp.size = Vector2i(128, 116)
		vp.transparent_bg = true
		vp.own_world_3d = true
		vp.msaa_3d = Viewport.MSAA_2X
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		add_child(vp)
		var cam := Camera3D.new()
		cam.cull_mask = 1
		cam.fov = 30
		var e := Environment.new()
		e.background_mode = Environment.BG_CLEAR_COLOR
		e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		e.ambient_light_color = Color(0.75, 0.78, 0.85)
		e.ambient_light_energy = 0.7
		cam.environment = e
		vp.add_child(cam)
		var sun_ := DirectionalLight3D.new()
		sun_.rotation = Vector3(deg_to_rad(-45), deg_to_rad(-35), 0)
		sun_.light_energy = 1.3
		vp.add_child(sun_)
		var a = Actor.new()
		a.preview = true
		vp.add_child(a)
		a.setup(self, k[0], Vector3.ZERO, Vector3(-0.8, 0, 1.0), 0.0)
		a.speed = THUMB_SPEED.get(k[0], 1.0)
		var h: float = sizes.get(k[0], 1.0)
		var wide: bool = k[0] in ["fox", "deer", "boar", "dog", "cat", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "cow", "sheep", "horse",
				"chamois", "ibex", "lynx", "cyclist", "stroller"]
		cam.position = Vector3(h * 1.1, h * 0.62, h * 1.75) * (1.15 if wide else 0.78)
		cam.look_at(Vector3(0, h * 0.48, 0), Vector3.UP)
		thumb_vps[k[0]] = [vp, a]
		var t: Texture2D = vp.get_texture()
		thumbs[k[0]] = t
		if thumb_rects.has(k[0]):
			thumb_rects[k[0]].texture = t
		for tb in thumb_btns:
			if tb[1] == k[0] and is_instance_valid(tb[0]):
				tb[0].icon = t
		await get_tree().process_frame


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
	"""button «Nach Updates suchen» in the window: asks before installing and also says when there is nothing new"""
	run_update(false, true)


func run_update(automatic: bool, by_hand: bool) -> void:
	"""check GitHub for a newer simulator. automatic: install by itself after 15 s (can be cancelled) - for the setting
	«Neue Versionen automatisch installieren» and for the button on the web page of MoveEye (from far away)."""
	if update_busy:
		return
	update_busy = true
	if update_btn != null:
		update_btn.disabled = true
	update_info = "suche …"
	var up = Updater.new()
	up.manual = by_hand
	up.quiet = not by_hand
	up.auto = automatic
	add_child(up)
	await up.check(VERSION, update_url)
	update_info = up.result
	up.queue_free()
	update_busy = false
	if update_btn != null:
		update_btn.disabled = false
	_sync_update_ui()


func _restore_window(args: PackedStringArray) -> void:
	"""after an update (or from the options): the window comes back as it was - size and place, full screen, or the
	small box / icon in the corner"""
	var w := get_window()
	var i := args.find("--win")
	if i >= 0 and i + 1 < args.size():
		var p := args[i + 1].split(",")
		if p.size() == 4:
			w.size = Vector2i(maxi(400, int(p[2])), maxi(300, int(p[3])))
			w.position = Vector2i(int(p[0]), int(p[1]))
	if "--maximized" in args:
		w.mode = Window.MODE_MAXIMIZED
	if "--mini" in args or "--mini-tiny" in args:
		var tiny := "--mini-tiny" in args
		get_tree().create_timer(1.0).timeout.connect(func():
			if not mini_box.mini:
				mini_box.enter()
			if tiny:
				mini_box.set_tiny(true))


func restart_args() -> PackedStringArray:
	"""options for the start after an update: as before, plus what is on now (sending, scene, MoveEye on this PC,
	the window: size and place, full screen, or the small box)"""
	var a := OS.get_cmdline_user_args()
	var out := PackedStringArray()
	var skip := false
	var early := net == null                     # the update check right at the start: nothing is switched on yet - keep what was asked for
	for x in a:
		if skip:
			skip = false
			continue
		if x in ["--stream", "--updated", "--mwpc"] or (not early and x in ["--mini", "--mini-tiny", "--maximized"]):
			continue
		if x == "--scene" or x == "--old-pid" or (x == "--win" and not early):
			skip = true
			continue
		out.append(x)
	if stream_on or (early and "--stream" in a):
		out.append("--stream")
	if not early:
		var w := get_window()
		if mini_box != null and mini_box.mini:
			out.append("--mini-tiny" if mini_box.tiny else "--mini")
			var sz: Vector2i = mini_box.saved.get("size", Vector2i(1440, 860))
			var ps: Vector2i = mini_box.saved.get("pos", Vector2i(60, 60))
			out.append("--win")
			out.append("%d,%d,%d,%d" % [ps.x, ps.y, sz.x, sz.y])
		elif w.mode == Window.MODE_MAXIMIZED or w.mode == Window.MODE_FULLSCREEN:
			out.append("--maximized")
		elif w.mode == Window.MODE_MINIMIZED:
			out.append("--mini")
		else:
			out.append("--win")
			out.append("%d,%d,%d,%d" % [w.position.x, w.position.y, w.size.x, w.size.y])
	out.append("--scene")
	out.append(scene)
	out.append("--old-pid")                       # 3D-3.75: the new simulator may stop this one if it still holds the port
	out.append(str(OS.get_process_id()))
	if mwpc != null and mwpc.state == "running":
		out.append("--mwpc")
	return out


const KEEP := ["pad_auto", "pad_sens", "pad_inv_y", "pad_swap", "pad_rumble", "colors_on", "seasons_on", "pad_dead", "pad_center", "show_laser", "game_max", "tunnel_host", "tunnel_code", "tunnel_on", "cam_fx", "cam_fy", "calendar_on", "ort_env", "ort_hide", "ort_cars", "ort_forest", "ort_camp", "game_rescue", "game_teamgoal", "game_teams", "world_cloth", "world_smoke", "world_fireflies", "lamp_share", "cloud_shadows", "gusts", "look_at_light", "game_goal", "sound_on", "night_gain", "ir_range", "game_mode", "game_lives", "game_items", "game_cones", "game_noise", "game_stones", "game_powers", "game_spectate", "game_photos", "game_fx_laser", "game_fx_paint", "game_fx_flash", "game_tap", "game_learn_miss", "game_learn_report", "game_learn_paths", "game_blind_bonus", "game_hides", "game_decoy", "game_night", "game_events", "game_checkpoints", "game_tasks", "game_autohandicap", "game_random", "lens_noise", "lens_vignette", "lens_drops", "insects_on", "game_minutes", "game_level", "game_quality", "game_guard", "eco_idle", "autostart_min", "autostart_mwpc", "autostart_lock", "last_scene", "fp_spot", "szene_spot", "bt_spot", "bt_bed", "bt_season", "bt_free", "bt_events", "bt_mount", "bt_bag", "bt_stove", "bt_wall", "bt_orient", "bt_marks", "bt_visited", "auto_update", "dev_updates", "news_seen", "news_popup", "show_zones3d", "show_det3d", "fauna_on", "twin", "ui_simple", "start_groups", "auto_visitors", "daily_life", "real_weather", "real_time", "night_weather", "surprise_on", "mix", "visit_rate", "max_visitors", "visitor_speed", "flee_light", "flee_sound",
		"avoid_on", "grafik_mode", "quality", "view_scale", "win_fps", "auto_perf", "meadow_on", "season", "mover_on", "mover_max", "mast_h", "patrol_judge", "map_on", "map_size", "map_span", "live_on", "live_cam", "live_size", "ort_lat", "ort_lon", "ort_name", "weather", "wind", "ambient", "moon", "moon_auto", "cam1_yaw", "stream_last", "game_bots", "game_tutorial", "game_daily", "game_ghost", "game_heart", "game_botguard", "kids_on", "kids_ask", "kids_thief", "kids_scary", "kids_laser", "kids_sound", "kids_stars", "dev_area"]
var _settings_dirty := false


func _load_settings() -> void:
	"""the settings of the last time (simulator_settings.json in the user folder)"""
	if not FileAccess.file_exists(SETTINGS_FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(SETTINGS_FILE))
	if typeof(d) != TYPE_DICTIONARY:
		return
	quality_set = d.has("quality")
	for k in KEEP:
		if d.has(k):
			var v = d[k]
			var old = get(k)
			if typeof(old) == TYPE_INT:
				v = int(v)
			elif typeof(old) == TYPE_BOOL:
				v = bool(v)
			elif typeof(old) == TYPE_FLOAT:
				v = float(v)
			else:
				v = str(v)
			set(k, v)
	if typeof(d.get("fold_mem")) == TYPE_DICTIONARY:      # nurgruppen: the own open / closed state of the cards and parts
		fold_mem = d["fold_mem"]
	grafik_mode = Quality.mode_id(grafik_mode)            # 3D-4.25: unknown / older names -> «Automatisch»
	if game_mode == "teamguard":                          # Balance 30.10.2026: «Team gegen Team» is gone
		game_mode = "guard"
	if d.has("hour_now") and not "--hour" in OS.get_cmdline_user_args() and not "--hour" in OS.get_cmdline_args() and not real_time:
		# 3D-3.76: the time as it was set; a short break (update, restart) - the clock went on meanwhile, like outside
		speed = clampf(float(d.get("speed_now", 1.0)), 1.0, 120.0)
		var gap: float = Time.get_unix_time_from_system() - float(d.get("hour_at", 0))
		set_hour(float(d["hour_now"]) + (gap * speed / 3600.0 if gap >= 0.0 and gap < 1800.0 else 0.0))


var _hour_saved_t := 0.0


func _save_settings() -> void:
	var d := {}
	for k in KEEP:
		d[k] = get(k)
	for k in _perf_orig:                                   # 3D-3.88: «automatisch leichter» is not saved
		d[k] = _perf_orig[k]
	d["hour_now"] = snappedf(hour(), 0.001)               # 3D-3.76: the time of the scene stays after a restart
	d["hour_at"] = int(Time.get_unix_time_from_system())
	d["speed_now"] = speed
	d["fold_mem"] = fold_mem                              # nurgruppen
	if mehr != null:
		d.merge(mehr.keep(), true)                        # 3D-4.2x: look (Hell / Rotlicht / Dunkel) and the tour
	_hour_saved_t = now()
	var f := FileAccess.open(SETTINGS_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d, " "))
	_settings_dirty = false


func set_autostart(on: bool) -> void:
	var err: String = Autostart.set_on(on)
	autostart_on = Autostart.is_on()
	start_info = "Autostart: " + err if err != "" else ("Startet mit dem PC" if autostart_on else "")
	_sync_ui()


func setup_autologon() -> void:
	"""without signing in: Windows signs in by itself (Autologon of Microsoft), the simulator starts and locks the screen"""
	start_info = "Autologon wird geladen …"
	_update_status()
	await get_tree().process_frame
	var err: String = Autostart.get_autologon()
	if err != "":
		start_info = "Autologon: " + err
		return
	if not autostart_on:
		set_autostart(true)
	autostart_lock = true
	_settings_dirty = true
	start_info = "Im Fenster «Autologon» das Windows-Passwort eingeben und «Enable» drücken"
	_sync_ui()


func _dev_check() -> void:
	"""3D-3.81: the development phase - has simulator3d/version.json a new commit on GitHub? The answer «unchanged» (304
	with the ETag) does not count against GitHub's limit of 60 questions per hour. New commit -> update at once."""
	_dev["busy"] = true
	_dev["t"] = now()
	var h := HTTPRequest.new()
	h.timeout = 8.0
	add_child(h)
	var hd := ["User-Agent: MoveEye-Sim", "Accept: application/vnd.github+json"]
	if str(_dev["etag"]) != "":
		hd.append("If-None-Match: " + str(_dev["etag"]))
	var err := h.request("https://api.github.com/repos/DonElektro/MotionWatch/commits?path=simulator3d/version.json&per_page=1", hd)
	if err == OK:
		var r: Array = await h.request_completed
		if r[0] == HTTPRequest.RESULT_SUCCESS and r[1] == 200:
			for x in r[2]:
				if str(x).to_lower().begins_with("etag:"):
					_dev["etag"] = str(x).substr(5).strip_edges()
			var j = JSON.parse_string((r[3] as PackedByteArray).get_string_from_utf8())
			var sha: String = str(j[0].get("sha", "")) if typeof(j) == TYPE_ARRAY and j.size() > 0 else ""
			if sha != "" and sha != str(_dev["sha"]):
				var first: bool = str(_dev["sha"]) == ""
				_dev["sha"] = sha
				if not first:                               # (the first answer only notes the state)
					print("development phase: new simulator commit - looking for the update")
					run_update(true, false)
	h.queue_free()
	_dev["busy"] = false


func set_auto_update(on: bool) -> void:
	auto_update = on
	_save_settings()
	next_update_check = now() + 5.0 if on else now() + UPDATE_EVERY   # switched on: look soon
	_sync_update_ui()


func _sync_update_ui() -> void:
	if update_btn != null:
		update_btn.text = "Nach Updates suchen (jetzt %s)" % VERSION


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
	match c.type:
		"button":
			var b := Button.new()
			b.text = UI.short(no_emoji(c.label))[0]     # 3D-3.98: the window has no emoji font (the page of MoveEye keeps them); 3D-4.21: short, the rest in the tooltip
			b.pressed.connect(func(): c["set"].call())
			var tk: String = {"dogwalk": "dog", "herd": "deer", "feed": "deer", "garden_person": "person", "bench": "person", "thief": "person"}.get(
					str(c.id), str(c.id).trim_prefix("spawn_"))
			if not tk in VISITOR_KINDS_ALL and Sym.lead(c.label)[0] != "":
				b.icon = Sym.tex(Sym.lead(c.label)[0])      # 3D-4.22: the drawn symbol instead of the emoji
			if tk in VISITOR_KINDS_ALL:                    # the small picture of the visitor on its button (3D-3.38)
				b.add_theme_constant_override("icon_max_width", 26)
				b.alignment = HORIZONTAL_ALIGNMENT_LEFT
				thumb_btns.append([b, tk])
				if thumbs.has(tk):
					b.icon = thumbs[tk]
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var flow: HFlowContainer = null                # buttons side by side, wrapping (like the tiles on the page)
			if parent.get_child_count() > 0 and parent.get_child(parent.get_child_count() - 1) is HFlowContainer:
				flow = parent.get_child(parent.get_child_count() - 1)
			else:
				flow = HFlowContainer.new()
				flow.add_theme_constant_override("h_separation", 6)
				flow.add_theme_constant_override("v_separation", 6)
				parent.add_child(flow)
			b.custom_minimum_size = Vector2(150 if b.text.length() < 22 else 300, 0)
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART   # long texts on two lines (never wider than the panel)
			b.tooltip_text = c.label
			flow.add_child(b)
			ui_items.append([b, c.label, c.extra.get("expert", false), parent])
		"toggle":
			var row := HBoxContainer.new()                   # text (wraps) + switch on the right, like on the page of MoveEye
			var tl := Label.new()
			var sh: Array = UI.short(no_emoji(c.label))          # 3D-4.21: at most ~40 characters, the rest in the tooltip
			if Sym.lead(c.label)[0] != "":
				row.add_child(Sym.icon_rect(Sym.lead(c.label)[0]))   # 3D-4.22: the drawn symbol in front
			tl.text = sh[0]
			tl.tooltip_text = sh[1]
			tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			tl.custom_minimum_size = Vector2(60, 0)
			tl.mouse_filter = Control.MOUSE_FILTER_STOP
			row.add_child(tl)
			var cb := CheckButton.new()
			cb.toggled.connect(func(on): c["set"].call(on))
			cb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			row.add_child(cb)
			tl.gui_input.connect(func(ev):
				if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
					cb.button_pressed = not cb.button_pressed)
			parent.add_child(row)
			ui_rows[c.id] = cb
			ui_items.append([row, c.label, c.extra.get("expert", false), parent])
		"select":
			var hb := VBoxContainer.new()                    # label above the choice: long choices never widen the panel
			hb.add_theme_constant_override("separation", 2)
			var l := Label.new()
			var shs: Array = UI.short(no_emoji(c.label))
			l.text = shs[0]
			l.tooltip_text = shs[1]
			l.mouse_filter = Control.MOUSE_FILTER_PASS
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			hb.add_child(l)
			var ob := OptionButton.new()
			ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			ob.fit_to_longest_item = false
			ob.clip_text = true
			ob.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			for o in c.extra.options:
				ob.add_item(o[1])
				ob.set_item_metadata(ob.item_count - 1, o[0])
			ob.item_selected.connect(func(idx): c["set"].call(ob.get_item_metadata(idx)))
			hb.add_child(ob)
			parent.add_child(hb)
			ui_rows[c.id] = ob
			ui_items.append([hb, c.label, c.extra.get("expert", false), parent])
		"map":                                            # in the window: a button that opens the map (karte.gd)
			var mb := Button.new()
			mb.text = "Karte öffnen: " + c.label + " (K)"
			mb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			mb.pressed.connect(open_map)
			parent.add_child(mb)
			ui_items.append([mb, c.label, c.extra.get("expert", false), parent])
		"text":
			var tb := VBoxContainer.new()
			tb.add_theme_constant_override("separation", 2)
			var tl2 := Label.new()
			var sht: Array = UI.short(no_emoji(c.label))
			tl2.text = sht[0]
			tl2.tooltip_text = sht[1]
			tl2.mouse_filter = Control.MOUSE_FILTER_PASS
			tl2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tb.add_child(tl2)
			var le := LineEdit.new()
			le.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			le.text_submitted.connect(func(t): c["set"].call(t))
			tb.add_child(le)
			parent.add_child(tb)
			ui_rows[c.id] = le
			ui_items.append([tb, c.label, c.extra.get("expert", false), parent])
		"slider":
			var vb := VBoxContainer.new()
			var hb2 := HBoxContainer.new()
			var l2 := Label.new()
			var shl: Array = UI.short(no_emoji(c.label))
			if Sym.lead(c.label)[0] != "":
				hb2.add_child(Sym.icon_rect(Sym.lead(c.label)[0]))   # 3D-4.22: the drawn symbol in front
			l2.text = shl[0]
			l2.tooltip_text = shl[1]
			l2.mouse_filter = Control.MOUSE_FILTER_PASS
			l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			var val := Label.new()
			hb2.add_child(l2)
			hb2.add_child(val)
			vb.add_child(hb2)
			var hs := HSlider.new()
			hs.min_value = c.extra["min"]
			hs.max_value = c.extra["max"]
			hs.step = c.extra.get("step", 1)
			hs.value_changed.connect(func(v):
				val.text = "%s %s" % [str(snappedf(v, 0.01)), c.extra.get("unit", "")]
				if not _syncing:
					c["set"].call(v))
			vb.add_child(hs)
			if c.extra.has("tip"):                       # 3D-3.95: explanation when the mouse is over it
				vb.tooltip_text = str(c.extra["tip"])
				hs.tooltip_text = str(c.extra["tip"])
			parent.add_child(vb)
			ui_rows[c.id] = hs
			ui_items.append([vb, c.label, c.extra.get("expert", false), parent])


var _syncing := false


func refresh_controls() -> void:
	"""the list of recordings changed: new options for the select (the page of MoveEye shows them at once)"""
	for c in controls:
		if c.id == "rec_pick":
			c.extra["options"] = recorder.options()
	_sync_ui()


func _sync_ui() -> void:
	_syncing = true
	for c in controls:
		if not ui_rows.has(c.id) or c["get"] == null:
			continue
		var w = ui_rows[c.id]
		var v = c["get"].call()
		if w is CheckBox or w is CheckButton:
			w.set_pressed_no_signal(bool(v))
		elif w is OptionButton:
			for i in range(w.item_count):
				if str(w.get_item_metadata(i)) == str(v):
					w.select(i)
		elif w is HSlider and not w.has_focus():
			w.value = float(v)
		elif w is LineEdit and not w.has_focus():
			w.text = str(v)
		if w is HSlider and c.has("ro"):              # Aufräumen 2: only readable now (e.g. the battery size «von MoveEye»)
			w.editable = not bool(c["ro"].call())
	_syncing = false


func group_active(g: String) -> int:
	"""3D-3.43: is something of this group switched on? 0 = no, 1 = on (green), 2 = something to watch (orange)"""
	match g:
		"Szene":
			return 1 if geo != null and geo.loaded and scene == "ort" else 0
		"Wetter":
			return 1 if real_weather else 0
		"Besuch":
			return 1 if auto_visitors else 0
		"Kamerabild":
			return 2 if cond.values().has(true) else 0
		"Sensoren":
			return 2 if door_open or gas_on else 0
		"Mover":
			return 1 if mover_on else 0
		"Spiel":
			return 1 if game != null and game.open else 0
		"Wildtier":
			return 1 if rifle_on else 0
		"Testen":
			return 1 if testrun != null and testrun.running else 0
	return 0


func _game_report_send() -> void:
	if game == null:
		return
	var m: String = game.learn.send()
	game.learn.info = m
	game.news("📊 " + m)


func _groups_on() -> Dictionary:
	var o := {}
	for g in group_bodies:
		var v := group_active(g)
		if v > 0:
			o[g] = v
	o["Verbindung"] = 1 if connected() else 0
	return o


func _paint_groups() -> void:
	"""the symbol of a group card turns green when it is on (like «Verbindung»), orange when something is to be watched"""
	for g in group_bodies:
		var st := group_active(g)
		if _group_state.get(g, -1) == st:
			continue
		_group_state[g] = st
		UI.fold_active(group_bodies[g], st)              # 3D-3.50: symbol and arrow green / orange, the name stays white
	if cam_body != null:
		UI.fold_active(cam_body, 1 if connected() else 0)
	if tools_body != null:
		UI.fold_active(tools_body, 1 if (mwpc != null and mwpc.state == "running") or (pruef != null and pruef.running) or (dataset != null and dataset.busy) or (testrun != null and testrun.running) or (blindmap != null and blindmap.busy) else 0)


func _update_status() -> void:
	if real_label != null and realism != null:
		real_label.text = "Echt-Abgleich: " + realism.info
		var cps: String = camphys.status() if camphys != null else ""
		if cps != "":
			real_label.text += "\n" + cps                 # 3D-4.x P1: exposure and gain of the head camera right now
	_night_test_tick()
	if refscan_label != null:
		refscan_label.text = refscan_text()
	if surprise_label != null:
		surprise_label.text = surprise.status_text()
	if ds_label != null and dataset != null:
		ds_label.text = ("Trainingspaket: " + dataset.msg) if dataset.msg != "" else ""
	if not mw_cmd.is_empty() and start_info.begins_with("MoveEye: "):
		var r_ = mw.get("refscan", null)
		if typeof(r_) == TYPE_DICTIONARY and int(r_.get("cmd_seen", 0)) >= int(mw_cmd["id"]):
			start_info = ""                                  # MoveEye took the request
	if status_label != null:
		status_label.text = Sym.clean(status_text())     # 3D-4.22: no empty boxes (MoveEye gets the text with its emoji)
	if tunnel_label != null and tunnel != null:
		var ts: Dictionary = tunnel.state()
		tunnel_label.text = ("Ziel: %s:%d (Port von MoveEye) · " % [tunnel_host if tunnel_host != "" else "?", tunnel.PORT]) + str(ts["msg"]) + ((" · %d offen · %.1f MB" % [int(ts["pipes"]), float(ts["mb"])]) if ts["on"] else "")
		tunnel_label.add_theme_color_override("font_color", UI.GRN if ts["ok"] else (UI.ORG if ts["on"] else UI.MUT))
	if conn_body != null:                                  # symbol: green = MoveEye connected, orange = sending, grey = off
		var st := 2 if connected() else (1 if stream_on else 0)
		if st != _conn_state:
			_conn_state = st
			UI.fold_active(conn_body, [0, 2, 1][st])          # 3D-3.50: symbol and arrow; the name stays white
			var hd: Label = conn_body.get_meta("head", null)
			if hd != null:
				hd.text = ("Verbindung · " + ["aus", "wartet auf MoveEye", "verbunden"][st]).to_upper()
	_paint_groups()
	if stream_note != null:
		if stream_on:
			stream_note.text = "Sendet: MoveEye findet den Simulator im Netz und bekommt die Bilder." + ("" if net.port == stream_port else " (Port %d war besetzt – sendet auf Port %d; MoveEye findet ihn von selbst, der Tunnel auch.)" % [stream_port, net.port])
			stream_note.add_theme_color_override("font_color", UI.GRN)
		elif net != null and net.error_text != "":
			stream_note.text = "⚠ " + net.error_text + (" – versucht es weiter (gleich auf einem freien Port)" if (stream_last or tunnel_on) else "")
			stream_note.add_theme_color_override("font_color", UI.ORG)
		else:
			stream_note.text = "Senden aus – zum Ausprobieren. MoveEye sieht den Simulator erst, wenn der Schalter eingeschaltet ist."
			stream_note.add_theme_color_override("font_color", UI.MUT)
	if Engine.get_process_frames() % 4 == 0:
		_sync_ui()


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
	"""buttons at the bottom of the view, a compass at the top left, the box of the chosen visitor"""
	thermal_full = TextureRect.new()
	thermal_full.texture = th_preview
	thermal_full.set_anchors_preset(Control.PRESET_FULL_RECT)
	thermal_full.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	thermal_full.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	thermal_full.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	thermal_full.mouse_filter = Control.MOUSE_FILTER_IGNORE
	thermal_full.visible = false
	layer.add_child(thermal_full)
	layer.move_child(thermal_full, 0)
	view_bar = HBoxContainer.new()
	view_bar.theme = th
	view_bar.add_theme_constant_override("separation", 6)
	view_bar.anchor_top = 1.0
	view_bar.anchor_bottom = 1.0
	view_bar.offset_left = 12
	view_bar.offset_top = -50
	view_bar.offset_bottom = -12
	view_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	view_bar.anchor_right = 1.0
	view_bar.offset_right = -404                          # not under the panel
	layer.add_child(view_bar)
	for k in [[0, "Frei", "Frei herumfliegen (0)"], [1, "Kamera 1", "Durch die Kopfkamera schauen (1)"], [2, "Kamera 2", "Durch die zweite Kamera schauen (2)"],
			[3, "Wärmebild", "Das Wärmebild gross (3)"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		var m: int = k[0]
		b.pressed.connect(func(): set_view(m))
		view_bar.add_child(b)
		view_btns[m] = b
	map_btn = Button.new()
	map_btn.text = "Karte"
	map_btn.tooltip_text = "Übersichtskarte ein / aus (M)"
	map_btn.toggle_mode = true
	map_btn.focus_mode = Control.FOCUS_NONE
	map_btn.button_pressed = map_on
	map_btn.toggled.connect(func(on): set_map(on))
	view_bar.add_child(map_btn)
	live_btn = Button.new()
	live_btn.text = "Livebild"
	live_btn.tooltip_text = "Livebild einer Kamera unter der Karte ein / aus (L)"
	live_btn.toggle_mode = true
	live_btn.focus_mode = Control.FOCUS_NONE
	live_btn.button_pressed = live_on
	live_btn.toggled.connect(func(on): set_live(on))
	view_bar.add_child(live_btn)
	for k in [["head", "Zum Kopf", "Zurück zu MoveEye"], ["top", "Von oben", "Von oben auf den Platz schauen"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.focus_mode = Control.FOCUS_NONE
		var w: String = k[0]
		b.pressed.connect(func(): _view_preset(w))
		view_bar.add_child(b)
	set_view(view_mode)
	var help := UI.small("Links ziehen: verschieben · Rechts ziehen: drehen · Rad: zoomen · Doppelklick: hinfliegen")
	view_help = help
	help.add_theme_color_override("font_color", Color(1, 1, 1, 0.75))
	help.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	help.add_theme_constant_override("shadow_offset_x", 1)
	help.add_theme_constant_override("shadow_offset_y", 1)
	help.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	help.autowrap_mode = TextServer.AUTOWRAP_OFF
	help.clip_text = true
	help.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	help.custom_minimum_size = Vector2(10, 0)
	help.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	view_bar.add_child(help)
	# compass: the red needle shows north; a click turns the view to the north
	compass = Control.new()
	compass.position = Vector2(14, 26)
	compass.size = Vector2(54, 54)
	compass.tooltip_text = "Norden – anklicken: nach Norden schauen"
	compass.draw.connect(func():
		var c := compass.size / 2.0                        # Paket «Fenster»: in the middle of its frame (room for the «N»)
		compass.draw_circle(c, 25, Color(0.05, 0.07, 0.1, 0.75))
		compass.draw_arc(c, 25, 0, TAU, 32, Color(1, 1, 1, 0.35), 1.5, true)
		var fwd := -view_cam.global_transform.basis.z
		var a := atan2(fwd.x, -fwd.z)                      # 0 = looking north
		var n := Vector2(sin(-a), -cos(-a))
		compass.draw_colored_polygon(PackedVector2Array([c + n * 19, c + n.orthogonal() * 5, c - n.orthogonal() * 5]), Color(0.95, 0.3, 0.25))
		compass.draw_colored_polygon(PackedVector2Array([c - n * 19, c + n.orthogonal() * 5, c - n.orthogonal() * 5]), Color(0.85, 0.87, 0.9))
		compass.draw_string(ThemeDB.fallback_font, c + n * 33 + Vector2(-4, 4), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.95)))
	compass.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			set_view(0)
			var p := view_cam.global_position
			var fwd := -view_cam.global_transform.basis.z
			var tilt := asin(clampf(fwd.y, -1.0, 1.0))
			var start := view_cam.global_transform
			var end := Transform3D(Basis.from_euler(Vector3(tilt, 0.0, 0.0)), p)
			if fly_tw != null:
				fly_tw.kill()
			fly_tw = create_tween()
			fly_tw.tween_method(func(f: float): view_cam.global_transform = start.interpolate_with(end, f), 0.0, 1.0, 0.5))
	layer.add_child(compass)
	sel_ring = Control.new()                              # a ring round the chosen visitor
	sel_ring.set_anchors_preset(Control.PRESET_FULL_RECT)
	sel_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sel_ring.draw.connect(func():
		if selected == null or not is_instance_valid(selected) or view_mode != 0:
			return
		var w: Vector3 = selected.global_position
		if view_cam.is_position_behind(w):
			return
		var pts := PackedVector2Array()
		for i in range(33):
			var a := TAU * i / 32.0
			pts.append(view_cam.unproject_position(w + Vector3(cos(a), 0.05, sin(a)) * (selected.radius + 0.35)))
		sel_ring.draw_polyline(pts, Color(1.0, 0.75, 0.2, 0.95), 2.5, true))
	layer.add_child(sel_ring)
	layer.move_child(sel_ring, 1)
	minimap = preload("res://scripts/minimap.gd").new()
	minimap.main = self
	minimap.size_px = map_size
	minimap.span = map_span
	minimap.visible = map_on
	layer.add_child(minimap)
	liveview = preload("res://scripts/liveview.gd").new()
	liveview.main = self
	liveview.cam = live_cam
	liveview.width_px = live_size
	liveview.visible = live_on
	layer.add_child(liveview)
	if statusled != null:
		statusled.make_tile(layer)                         # das Fenster «Gerät» (LED + Tasten)
	if smalltv != null:
		smalltv.make_tile(layer)                           # 3D-4.19: das Bild des virtuellen SmallTV, unter Karte / Livebild
	rover_pad = preload("res://scripts/rover_pad.gd").new()
	rover_pad.main = self
	layer.add_child(rover_pad)
	explore = preload("res://scripts/explore.gd").new()       # 3D-3.55: explore with the rover
	explore.main = self
	layer.add_child(explore)
	padview = preload("res://scripts/padview.gd").new()       # the «Controller-Ansicht» of MoveEye: views, turning, zoom, picture without buttons
	padview.main = self
	add_child(padview)
	padmap = preload("res://scripts/padmap.gd").new()         # 3D-4.13: ONE controller mapping (window, explore, game, MoveEye)
	padmap.main = self
	add_child(padmap)
	padhud = preload("res://scripts/padhud.gd").new()         # 3D-4.13: chips, direction, focus ring of the controller
	padhud.main = self
	padhud.pm = padmap
	var phl := CanvasLayer.new()                              # above the control panel (the focus ring), below the game at the PC
	phl.layer = 25
	add_child(phl)
	phl.add_child(padhud)
	padmap.hud = padhud
	patrol = preload("res://scripts/patrol.gd").new()         # 3D-3.61: the mover drives MoveEye round a route
	patrol.main = self
	add_child(patrol)
	patrol.load_route()
	toolbar = preload("res://scripts/toolbar.gd").new()       # 3D-3.61: everything with the mouse
	toolbar.main = self
	layer.add_child(toolbar)
	headpad = preload("res://scripts/headpad.gd").new()       # 3D-3.77: steer the head of MoveEye
	headpad.main = self
	headpad.theme = th
	layer.add_child(headpad)
	templates = preload("res://scripts/templates.gd").new()   # 3D-3.82: «Vorlagen»
	templates.main = self
	templates.theme = th
	layer.add_child(templates)
	if scene == "vorlage":
		set_scene("vorlage")                                   # built before the window existed: once more with the files
	inventar = preload("res://scripts/inventar.gd").new()     # 3D-3.86: the inventory (all 80 things of the AI)
	inventar.main = self
	inventar.theme = th
	layer.add_child(inventar)
	inventar.rebuild()
	blindmap = preload("res://scripts/blindmap.gd").new()     # 3D-3.85: blind spots / night rehearsal
	blindmap.main = self
	add_child(blindmap)
	overlay = preload("res://scripts/overlay3d.gd").new()     # 3D-3.83: zones and detections of MoveEye in 3D
	overlay.main = self
	add_child(overlay)
	news = preload("res://scripts/news.gd").new()             # 3D-3.82: «Neu in dieser Version» after an update
	news.main = self
	news.theme = th
	layer.add_child(news)
	get_tree().create_timer(3.0).timeout.connect(func(): news.check())
	localplay = preload("res://scripts/localplay.gd").new()   # 3D-3.77: play here at the PC
	localplay.main = self
	localplay.theme = th
	var lp_layer := CanvasLayer.new()                         # above everything of the window
	lp_layer.layer = 30
	add_child(lp_layer)
	lp_layer.add_child(localplay)
	home_editor = preload("res://scripts/home_editor.gd").new()   # 3D-3.73: «Mein Zuhause bauen»
	home_editor.main = self
	home_editor.theme = th
	home_editor.position = Vector2(10, 345)
	layer.add_child(home_editor)
	# the chosen visitor
	sel_box = PanelContainer.new()
	sel_box.theme = th
	sel_box.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.95), UI.LINE, 10, 8))
	sel_box.anchor_top = 1.0
	sel_box.anchor_bottom = 1.0
	sel_box.offset_left = 12
	sel_box.offset_top = -104
	sel_box.offset_bottom = -58
	sel_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	sel_box.visible = false
	layer.add_child(sel_box)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	sel_box.add_child(hb)
	sel_label = Label.new()
	sel_label.custom_minimum_size = Vector2(90, 0)
	sel_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hb.add_child(sel_label)
	follow_btn = Button.new()
	follow_btn.focus_mode = Control.FOCUS_NONE
	follow_btn.pressed.connect(func():
		follow = not follow
		_paint_sel())
	hb.add_child(follow_btn)
	for k in [["scare", "Erschrecken"], ["away", "Wegschicken"], ["del", "Entfernen (Entf)"]]:
		var b := Button.new()
		b.text = k[1]
		b.focus_mode = Control.FOCUS_NONE
		var w: String = k[0]
		b.pressed.connect(_sel_action.bind(w))
		hb.add_child(b)
	var x := Button.new()
	x.text = "×"
	x.focus_mode = Control.FOCUS_NONE
	x.pressed.connect(func(): select_visitor(null))
	hb.add_child(x)


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
		view_cam.fov = 41
		return
	if view_mode == 2:
		view_cam.global_transform = cams[1].global_transform
		view_cam.fov = 62
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
	if place_kind == "rover":                          # 3D-3.60: «Rover versetzen» - the next click puts it there
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
	crosshair = Control.new()
	crosshair.set_anchors_preset(Control.PRESET_FULL_RECT)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	crosshair.visible = false
	crosshair.draw.connect(func():
		var p: Vector2 = crosshair.size / 2.0 if look else crosshair.get_local_mouse_position()
		var c := Color(1.0, 0.25, 0.2, 0.95)
		crosshair.draw_arc(p, 18.0, 0.0, TAU, 40, c, 2.0)
		for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			crosshair.draw_line(p + d * 8.0, p + d * 30.0, c, 2.0)
		crosshair.draw_circle(p, 1.5, c)
		var f := ThemeDB.fallback_font
		var txt := "Gewehr (unblutig): Treffer %d von %d Schüssen · %d Punkte · G: Gewehr aus" % [hits, shots, points]
		crosshair.draw_string(f, Vector2(18, 34), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 1, 1))
		if now() - shot_msg_t < 2.5:
			crosshair.draw_string(f, Vector2(18, 64), shot_msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(1.0, 0.85, 0.3)))
	layer.add_child(crosshair)
	shot_sound = AudioStreamPlayer.new()
	shot_sound.stream = _make_sound("shot")
	add_child(shot_sound)
	hit_sound = AudioStreamPlayer.new()
	hit_sound.stream = _make_sound("boing")
	add_child(hit_sound)


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
	## the name of this computer (MoveEye shows it next to the simulator in its list)
	for k in ["COMPUTERNAME", "HOSTNAME"]:
		var h := OS.get_environment(k).strip_edges()
		if h != "":
			return h.substr(0, 40)
	var f := FileAccess.open("/etc/hostname", FileAccess.READ)
	if f != null:
		return f.get_as_text().strip_edges().substr(0, 40)
	return ""


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
	if q.has("w") and str(q["w"]).is_valid_int():
		view_w = clampi(int(q["w"]), 320, 2560)
	if q.has("q") and str(q["q"]).is_valid_float():
		view_q = clampf(float(q["q"]) / 100.0, 0.3, 0.95)
	if Quality.lite():                          # 3D-4.25: Lite - a smaller picture of the window (the cameras for MoveEye stay)
		view_w = mini(view_w, Quality.VIEW_W)
		view_q = minf(view_q, Quality.VIEW_Q)
	if q.has("fmt"):
		view_webp = str(q["fmt"]) == "webp"
	if str(q.get("clean", "")) == "1":
		view_clean_t = now()                    # 3D-3.67: MoveEye shows the picture in full screen: no rover stick
	if str(q.get("bare", "")) == "1" and padview != null:
		padview.bare_t = now()                  # «Controller-Ansicht»: the picture without the buttons of the window
	if str(q.get("dock", "")) == "1" and padview != null:
		padview.dock_t = now()                  # 3D-4.x: MoveEye's simulator page: only the 3D view and the dock (padview.gd)
const VIEW_KEYS := {"ArrowUp": KEY_UP, "ArrowDown": KEY_DOWN, "ArrowLeft": KEY_LEFT, "ArrowRight": KEY_RIGHT, "w": KEY_W, "a": KEY_A,
		"s": KEY_S, "d": KEY_D, "q": KEY_Q, "e": KEY_E, "r": KEY_R, "f": KEY_F, "PageUp": KEY_PAGEUP, "PageDown": KEY_PAGEDOWN,
		"0": KEY_0, "1": KEY_1, "2": KEY_2, "3": KEY_3, "4": KEY_4, "5": KEY_5, "+": KEY_PLUS, "-": KEY_MINUS, "Shift": KEY_SHIFT, "p": KEY_P}


func view_rect() -> Rect2:
	"""the part of the window with the 3D world (without the panel on the right)"""
	var vs: Vector2 = Vector2(remote_vp.size) if remote_vp != null else get_viewport().get_visible_rect().size
	var w := vs.x
	if ui_root != null and ui_root.visible:
		w = min(w, ui_root.get_global_rect().position.x)
	return Rect2(0, 0, max(64.0, w), vs.y)


func _view_capture() -> void:
	var t := now()
	for kc in _rkeys.keys():
		if t > float(_rkeys[kc]):
			_rkeys.erase(kc)
			var ku := InputEventKey.new()
			ku.keycode = kc
			ku.physical_keycode = kc
			ku.pressed = false
			Input.parse_input_event(ku)
	# the window is the small box (or minimized): the view for MoveEye is drawn in a picture of its own (3D-3.19)
	_remote_set(t - view_want_t < (10.0 if remote_vp != null else 3.0) and not win_open)
	if t - view_want_t > 3.0 or t - _view_t < 1.0 / max(1.0, minf(view_fps, Quality.VIEW_FPS) if Quality.lite() else view_fps):
		return
	_view_t = t
	var img := (remote_vp.get_texture() if remote_vp != null else get_viewport().get_texture()).get_image()
	if img == null or img.is_empty():
		return
	var vs: Vector2 = Vector2(remote_vp.size) if remote_vp != null else get_viewport().get_visible_rect().size
	var k: float = float(img.get_width()) / maxf(1.0, vs.x)
	if padview != null and padview.dock_compose():      # 3D-4.x: MoveEye's simulator page: only the 3D view and the dock
		img = padview.compose(img, k)
		if img == null:
			return
	var r := view_rect()
	var rr := Rect2i(int(r.position.x * k), int(r.position.y * k), int(r.size.x * k), int(r.size.y * k)).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	if rr.size.x < 16 or rr.size.y < 16:
		return
	var sub := img.get_region(rr)
	if sub.get_width() > view_w:
		sub.resize(view_w, int(sub.get_height() * float(view_w) / sub.get_width()), Image.INTERPOLATE_BILINEAR)
	if view_webp and t - view_mjpg_t > 3.0:            # 3D-3.58: WebP - the same sharpness with about a third less data
		view_jpg = sub.save_webp_to_buffer(true, view_q)
		view_mime = "image/webp"
	else:
		view_jpg = sub.save_jpg_to_buffer(view_q)
		view_mime = "image/jpeg"
	view_no += 1


func view_input(evs: Array) -> int:
	"""events from MoveEye: x / y 0 … 1 in the picture of /view.mjpg -> the same as mouse / keys here"""
	var r := view_rect()
	var n := 0
	for e in evs.slice(0, 60):
		if not (e is Dictionary):
			continue
		var t := str(e.get("t", ""))
		var p := r.position + Vector2(clampf(float(e.get("x", 0.5)), 0.0, 1.0) * r.size.x, clampf(float(e.get("y", 0.5)), 0.0, 1.0) * r.size.y)
		if t == "move":
			var m := InputEventMouseMotion.new()
			m.position = p
			m.global_position = p
			m.relative = p - _in_pos
			m.velocity = m.relative * 30.0
			m.button_mask = _in_mask
			_view_send(m)
		elif t in ["down", "up", "dbl"]:
			var b := clampi(int(e.get("b", 1)), 1, 3)
			var mb := InputEventMouseButton.new()
			mb.button_index = b
			mb.pressed = t != "up"
			mb.double_click = t == "dbl"
			mb.alt_pressed = bool(e.get("alt", false))
			mb.shift_pressed = bool(e.get("shift", false))
			mb.position = p
			mb.global_position = p
			var bit := 1 << (b - 1)
			_in_mask = (_in_mask | bit) if mb.pressed else (_in_mask & ~bit)
			mb.button_mask = _in_mask
			_view_send(mb)
		elif t == "wheel":
			for pr in [true, false]:
				var w := InputEventMouseButton.new()
				w.button_index = MOUSE_BUTTON_WHEEL_UP if float(e.get("d", 1)) > 0 else MOUSE_BUTTON_WHEEL_DOWN
				w.pressed = pr
				w.factor = 1.0
				w.position = p
				w.global_position = p
				_view_send(w)
		elif t == "key":
			var kc = VIEW_KEYS.get(str(e.get("k", "")))
			if kc == null:
				continue
			var ke := InputEventKey.new()
			ke.keycode = kc
			ke.physical_keycode = kc
			ke.pressed = bool(e.get("down", true))
			Input.parse_input_event(ke)
			if ke.pressed:
				_rkeys[kc] = now() + 1.2                 # held from MoveEye: let go by itself if no news comes (lost connection)
			else:
				_rkeys.erase(kc)
		else:
			continue
		if t != "key":
			_in_pos = p
		n += 1
	return n


var ui_layer: CanvasLayer
var remote_vp: SubViewport = null
var view_clean_t := -100.0              # 3D-3.67: last picture asked for «clean» (full screen in the browser)
var _remote_back := []                 # [node, parent, index] to put back


func _remote_set(on: bool) -> void:
	"""small box / minimized while MoveEye looks at the window: the window (3D view, map, compass, buttons, panel)
	is drawn into an invisible picture of the normal window size; back into the window as soon as it is big again"""
	if on == (remote_vp != null) or ui_layer == null or view_cam == null:
		return
	if on:
		var sz := Vector2i(1440, 860)
		if mini_box != null and mini_box.mini:
			sz = mini_box.saved.get("size", sz)
		remote_vp = SubViewport.new()
		remote_vp.size = Vector2i(clampi(sz.x, 640, 2560), clampi(sz.y, 400, 1600))
		remote_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		remote_vp.msaa_3d = Viewport.MSAA_2X
		add_child(remote_vp)
		_remote_back = []
		for n in [ui_layer, view_cam]:
			_remote_back.append([n, n.get_parent(), n.get_index()])
			n.reparent(remote_vp)
		view_cam.current = true
		print("view for MoveEye: drawn on its own (window small)")
	else:
		for e in _remote_back:
			var n: Node = e[0]
			if is_instance_valid(n):
				n.reparent(e[1])
				(e[1] as Node).move_child(n, mini(int(e[2]), (e[1] as Node).get_child_count() - 1))
		_remote_back = []
		view_cam.current = true
		remote_vp.queue_free()
		remote_vp = null
		print("view for MoveEye: back in the window")


func _view_send(ev: InputEvent) -> void:
	"""a mouse event from MoveEye: into the window, or into the picture of its own (then the 3D view gets what the
	panel, the map and the buttons do not take)"""
	if remote_vp == null:
		Input.parse_input_event(ev)
		return
	remote_vp.push_input(ev, true)
	if not remote_vp.is_input_handled():
		_unhandled_input(ev)



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
	var out := [["Rover", rig, abs(_pad_l) + abs(_pad_r) > 0.05]]
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
	"""always to see: CPU of this PC and of the simulator (3D-3.26), like in the small box"""
	cpu_pill = Label.new()
	cpu_pill.add_theme_font_size_override("font_size", 13)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.1, 0.72)
	sb.set_corner_radius_all(9)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 3
	sb.content_margin_bottom = 3
	cpu_pill.add_theme_stylebox_override("normal", sb)
	cpu_pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cpu_pill.text = "CPU …"
	layer.add_child(cpu_pill)


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
	if compass == null or view_bar == null or phone == null:
		return
	var vw: float = get_viewport().get_visible_rect().size.x
	var right: float = ui_root.get_global_rect().position.x if ui_root != null and ui_root.visible else vw
	var ph: bool = phone.visible
	var left: float = phone.get_global_rect().end.x + 10.0 if ph else 0.0
	var key := "%s|%d|%d|%d" % [ph, int(left), int(right), int(minimap.size.x) if minimap != null else 0]
	if key == _hud_key:
		return
	_hud_key = key
	if ph:
		if fenster == null:                              # Paket «Fenster»: the frames place compass and map (fenster.gd)
			compass.position = Vector2(right - 68.0, 26.0)
			if minimap != null:
				minimap.position = Vector2(right - minimap.size.x - 14.0, 92.0)
		view_bar.offset_left = left + 12.0
		view_bar.offset_right = -(vw - right) - 12.0
		view_bar.alignment = BoxContainer.ALIGNMENT_CENTER
		if view_help != null:
			view_help.visible = false                   # not enough room next to the phone
		var room: float = right - left - 24.0
		var fs: int = 14 if room > 640.0 else (12 if room > 520.0 else 11)
		view_bar.add_theme_constant_override("separation", 6 if room > 640.0 else 3)
		for b in view_bar.get_children():
			if b is Button:
				b.add_theme_font_size_override("font_size", fs)
	else:
		if fenster == null:
			compass.position = Vector2(14, 26)
			if minimap != null:
				minimap.position = Vector2(14, 92)
		view_bar.offset_left = 12.0
		view_bar.offset_right = -404.0
		view_bar.alignment = BoxContainer.ALIGNMENT_BEGIN
		if view_help != null:
			view_help.visible = true
		view_bar.add_theme_constant_override("separation", 6)
		for b in view_bar.get_children():
			if b is Button:
				b.remove_theme_font_size_override("font_size")


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
	"""one setting by its id (the game wizard; like the CONTROL action «set»)"""
	for c in controls:
		if c.id == id and c["set"] != null:
			match c.type:
				"slider":
					v = clamp(float(v), float(c.extra.get("min", -1e9)), float(c.extra.get("max", 1e9)))
				"toggle":
					v = bool(v)
				"button":
					c["set"].call()
					return {"ok": true}
				_:
					v = str(v)
			c["set"].call(v)
			_settings_dirty = true
			_sync_ui()
			return {"ok": true}
	return {"ok": false}



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
