extends Node3D
## Motion Watch 3D simulator - scenes: camping place, forest, car park, garden, funny place, wildlife watching (scenes.gd)
## The world, the cameras for Motion Watch (head camera on the pan / tilt head, fixed camera, thermal camera),
## day and night, weather, lights, visitors, sensors, the window on the PC and the connection (net.gd).

const VERSION := "3D-3.13"
const CAM_W := [960, 640]
const CAM_H := [540, 360]
const CAM_FPS := [12.0, 8.0]
const CAM_FOV := [66.0, 100.0]
const TH_W := 80
const TH_H := 62
const TH_FOV := 45.0
const HEAD_H := 1.6

var Actor = preload("res://scripts/actor.gd")
var Net = preload("res://scripts/net.gd")
var Phone = preload("res://scripts/phone.gd")
var Scenes = preload("res://scripts/scenes.gd")
var Updater = preload("res://scripts/update.gd")
var Mwpc = preload("res://scripts/mwpc.gd")
var UI = preload("res://scripts/ui_style.gd")
var Autostart = preload("res://scripts/autostart.gd")
var Game = preload("res://scripts/game.gd")
var TestRun = preload("res://scripts/testrun.gd")
var Geo = preload("res://scripts/geo.gd")
var Karte = preload("res://scripts/karte.gd")
var geo                               # geo.gd: a real place in Switzerland (scene «ort», from 3D-3.4)
var karte                             # karte.gd: the map to choose the place
var ort_lat := 0.0                    # the chosen place (kept)
var ort_lon := 0.0
var ort_name := ""
var terrain := false                  # the scene has hills (ground_y), else the ground is flat at y = 0
var ground_mats: Array = []           # ground materials of the place (snow, wet)
var flat_nodes: Array = []            # flat meadow and the hills far away: hidden at a real place
var geo_note := ""
var testrun                           # testrun.gd: test run with evaluation (from 3D-2.6)
var game                              # game.gd: «Unentdeckt ans Ziel» with up to 4 phones (from 3D-2.4)
var game_minutes := 5.0
var game_level := "normal"            # easy | normal | hard
var game_quality := "mid"             # picture on the phone: small | mid | big
var game_guard := true                # without Motion Watch the head guards by itself
var game_mode := "camera"             # camera: all against the camera · guard: one player is the guard
var game_lives := 0                   # 0 = unlimited
var game_items := 3                   # crystals to collect (+100 each)
var game_cones := false               # show the fields of view of the cameras (for beginners)
var game_noise := true                # the microphone hears loud steps
var game_stones := true               # stones to throw (distract the guard)
var game_random := false              # start and goal by chance
var game_rescue := false              # caught -> jail, a team mate frees you (3D-3.1)
var game_teamgoal := false            # the goal opens only when all crystals are found
var game_teams := false               # two teams: red against blue (3D-3.0)
var game_goal := "reach"              # reach: get to the goal · return: fetch the loot and bring it back to the start
# ---- start with the PC (from 3D-2.1; autostart.gd) ----
var autostart_on := false             # read from Windows (Run key) / Linux (autostart folder), not from the settings
var autostart_min := true             # at the autostart: minimized = the small box of mini.gd
var autostart_mwpc := false           # at the autostart: also start Motion Watch on this PC
var autostart_lock := false           # at the autostart: lock the screen afterwards (with the automatic sign-in of Windows)
var last_scene := ""                  # the scene of the last time (the autostart comes back to it)
var start_info := ""                  # message of the autostart for the status line
var _bg_t := 0.0
# ---- saving power (from 3D-2.3): the world only moves while the window is open or Motion Watch is connected ----
var eco_idle := true                  # setting «Nur rechnen, wenn ...» (saved)
var sim_active := true                # false = pause: nobody looks (window small / minimized, no Motion Watch)
var win_open := true                  # the big window is visible (not the small box, not minimized)
var mini_box                          # mini.gd
var cpu_info := {}                    # measured by Motion Watch: {"total", "mw", "sim"} in % of the whole computer
var _fps0 := 0
var mwpc                              # Motion Watch on this PC (mwpc.gd)
var mwpc_btn: Button
var mwpc_label: Label
var in_vm := false                    # virtual machine / no graphics card: lighter graphics, fewer preview pictures
var update_url := ""                  # --update-url (tests); empty = GitHub
var update_btn: Button
var auto_update := false              # «Neue Versionen automatisch installieren» (saved; also from the web page of Motion Watch)
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
var moon := 0.6
var auto_visitors := true
var next_auto := 0.0
var door_open := false
var gas_on := false
var quality := "nice"
var cam1_yaw := -12.0

# ---- what Motion Watch sends -----------------------------------------------------------------------------------
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
var sky_mat: ProceduralSkyMaterial
var head: Node3D
var rig: Node3D                       # from 3D-3.11: the base of Motion Watch - stands still, or drives as the mover
var chassis: Node3D
var mover_on := false                 # «Mover simulieren»: a tracked vehicle under Motion Watch, driven by its second stick
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
var th_lut := PackedFloat32Array()
var th_srgb := true
var th_bg_raw := false
var gain := [1.0, 1.0]
# ---- the picture of the cameras (from 3D-2.5; saved) ----
var lens_noise := 0.5                 # grain, stronger at night
var lens_vignette := 0.3              # dark corners
var lens_drops := true                # raindrops on the lens when it rains
var insects_on := true                # insects fly round the light at night (false alarms, as in reality)
var night_gain := 2.5                 # how much a camera may amplify at night (real cameras: limited -> dark, grainy)
var ir_range := 14.0                  # reach of the infrared light (m)
var sound_on := true                  # the sounds of the world go to the microphone of Motion Watch (from 3D-2.6)
var sounds: Array = []                # [dB at 1 m, position, until]
var mw_det := {}                      # what Motion Watch detects right now (from 2.93.3: persons, present, noise)
var mw_det_t := 0.0
var lens_mats: Array = []
var expo_mats: Array = []             # exposure quads (multiply) in front of camera 0 / 1
var night_envs: Array = [null, null]  # [grey (infrared), little colour] - copies of env, renewed every 0.5 s at night
var insects: CPUParticles3D
var capturing := false
var preview_on := true
var th_preview: ImageTexture

# ---- remote control (CONTROL protocol 1, shared by the window and the web page of Motion Watch) ---------------------
var controls: Array = []
var ui_rows := {}
var status_label: Label
var stream_on := false                     # sending to Motion Watch: off at the start, the user switches it on in the window
var stream_port := 8765
var stream_cb: CheckButton
var stream_note: Label

var obj := {"door": Vector3.ZERO, "pir": Vector3.ZERO, "bike": Vector3.ZERO}   # set by the scene
const SERVO_DEG_S := 200.0            # how fast the pan / tilt servos turn (MG90S: about 0.1 s per 60°, with load slower)
var next_birds := 0.0
# ---- settings for the visitors (from 3D-2.0; saved, also on the web page of Motion Watch) ----
var visit_rate := 1.0                 # how often visitors come by themselves (× the scene's normal rate)
var max_visitors := 12
var visitor_speed := 1.0
var mix := "mixed"                    # mixed | more_animals | more_people | animals | people
var flee_light := true                # animals flee from the white light at night
var flee_sound := true                # ... and from the siren


func _ready() -> void:
	randomize()
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
	set_process(false)
	set_process_unhandled_input(false)
	if _vm_needs_angle(args):
		return
	in_vm = _in_vm()
	if in_vm and not "--quality" in args:
		quality = "simple"                      # virtual machine: no real graphics card - the light graphics by default
	DisplayServer.window_set_title("Motion Watch – 3D-Simulator %s" % VERSION)
	var k := args.find("--update-url")
	if k >= 0 and k + 1 < args.size():
		update_url = args[k + 1]
	_load_settings()
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
	_build_world()
	_build_head()
	_build_viewports()
	_build_weather()
	_build_lens()
	_build_fireflies()
	visitors = Node3D.new()
	add_child(visitors)
	_build_view_camera()
	stream_port = port
	game = Game.new()
	game.main = self
	add_child(game)
	testrun = TestRun.new()
	testrun.main = self
	add_child(testrun)
	_register_controls()
	_order_controls()
	mwpc = Mwpc.new()
	mwpc.main = self
	add_child(mwpc)
	_build_ui()
	mwpc.changed.connect(_on_mwpc)
	_on_mwpc()
	next_update_check = now() + UPDATE_EVERY
	if "--mwpc" in args:                          # after an update: Motion Watch on this PC was running - start it again
		mwpc.start.call_deferred()
	net = Net.new()
	net.main = self
	add_child(net)
	if "--stream" in args or at_boot:          # start sending at once (old behaviour; always at the autostart)
		set_stream(true)
	autostart_on = Autostart.is_on()
	if autostart_on:
		Autostart.repair()                         # the folder of the program was moved: the autostart follows it
	if at_boot:
		if autostart_mwpc and not "--mwpc" in args:
			mwpc.start.call_deferred()
		if autostart_min:
			get_tree().create_timer(1.5).timeout.connect(func(): DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_MINIMIZED))
		if autostart_lock and not "--updated" in args:
			get_tree().create_timer(6.0).timeout.connect(func(): Autostart.lock_screen())
	_apply_quality()
	_calibrate_thermal()
	next_auto = now() + 20.0
	for i in range(args.size()):
		if args[i] == "--phone":                  # start with the phone open (optionally: --phone http://address:5000)
			if i + 1 < args.size() and args[i + 1].begins_with("http"):
				phone.addr.text = args[i + 1]
			get_tree().create_timer(2.0).timeout.connect(func(): phone.open())
	DisplayServer.window_set_title("Motion Watch – 3D-Simulator %s (Port %d)" % [VERSION, port])
	_fps0 = Engine.max_fps
	mini_box = preload("res://scripts/mini.gd").new()      # minimize = small box, the simulator keeps drawing
	mini_box.main = self
	add_child(mini_box)
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
	OS.create_process(OS.get_executable_path(), a)
	get_tree().quit()
	return true


func set_stream(on: bool) -> void:
	if on:
		net.start(stream_port)
		stream_on = net.listening
	else:
		net.stop()
		stream_on = false
		mw_t = 0.0
	if stream_cb != null:
		stream_cb.set_pressed_no_signal(stream_on)
	_update_status()


func _make_lut(srgb: bool) -> void:
	"""grey value of the thermal picture -> °C (the renderer writes it either linear or sRGB - found out at the start)"""
	th_lut = PackedFloat32Array()
	for i in range(256):
		var v := i / 255.0
		th_lut.append((Color(v, 0, 0).srgb_to_linear().r if srgb else v) * 120.0 - 40.0)


func _calibrate_thermal() -> void:
	"""render a surface of exactly 20 °C once and see how its grey value comes back"""
	var vp := SubViewport.new()
	vp.size = Vector2i(16, 16)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(vp)
	var cam := Camera3D.new()
	cam.cull_mask = 8
	cam.environment = th_env
	vp.add_child(cam)
	var q := MeshInstance3D.new()
	q.mesh = box(4, 4, 0.1)
	q.material_override = tmat_fixed(20.0)
	q.layers = 8
	add_child(q)
	cam.global_transform = Transform3D(Basis(), Vector3(0, -500, 3))
	q.global_position = Vector3(0, -500, 0)
	q.scale = Vector3(0.5, 0.5, 1)                       # covers the middle only: the corners show the background
	var bg_was := th_env.background_color
	th_env.background_color = Color(0.25, 0.25, 0.25)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img != null and not img.is_empty():
		var r := img.get_pixel(8, 8).r                  # 0.5 linear -> 0.5 (linear) or 0.735 (sRGB)
		th_srgb = r > 0.62
		_make_lut(th_srgb)
		var rb := img.get_pixel(0, 0).r                 # background colour 0.25 comes back as ...
		th_bg_raw = abs(rb - 0.25) < 0.04
		print("thermal calibration: grey %.3f -> %s, background %.3f -> %s" % [r, "sRGB" if th_srgb else "linear", rb, "raw" if th_bg_raw else "converted"])
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
		mats[k] = m
	return mats[k]


func tmat(key: String) -> ShaderMaterial:
	"""thermal material of a kind of surface whose temperature changes with the time of day (updated in _update_temps)"""
	if not tmats.has(key):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/thermal.gdshader")
		m.set_shader_parameter("temp", ambient)
		m.set_shader_parameter("spread", 0.8)
		tmats[key] = m
	return tmats[key]


func tmat_fixed(temp: float) -> ShaderMaterial:
	var k := snappedf(temp, 0.5)
	if not tmat_fixed_cache.has(k):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/thermal.gdshader")
		m.set_shader_parameter("temp", k)
		m.set_shader_parameter("spread", 0.6)
		tmat_fixed_cache[k] = m
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
	sky_mat = ProceduralSkyMaterial.new()
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR   # from 3D-3.3: the light of the sky as a colour - the
	env.ambient_light_sky_contribution = 0.0                         # Compatibility renderer of Godot gave almost no light
																	 # from the sky, so shadows were black (_update_sky)
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_density = 0.0008
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
	tmats["ground"] = gm
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
	_horizon.clear()
	ground_mats.clear()
	geo_note = ""
	scenes.build(scene, scene_parent)
	for n in flat_nodes:
		n.visible = not terrain
	if scene == "ort" and not geo.loaded and not geo.busy and ort_lat != 0.0:
		geo.load_place(ort_lat, ort_lon, ort_name)      # from the cache or the internet; then place_loaded()
	if scene == "wild":
		rifle_on = true                          # wildlife watching: the rifle is on by itself


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
	"""from the map or the page of Motion Watch: load this place"""
	if not geo.in_ch(la, lo):
		geo.info = "Dieser Punkt liegt nicht in der Schweiz."
		return
	geo.load_place(la, lo, nm)


func set_place_text(t: String) -> void:
	"""«Zermatt» or «46.0207, 7.7491» (field on the page of Motion Watch)"""
	var parts := t.replace(";", ",").split(",")
	if parts.size() >= 2 and parts[0].strip_edges().is_valid_float() and parts[1].strip_edges().is_valid_float():
		var nm := ""
		if parts.size() > 2:
			nm = ",".join(parts.slice(2)).strip_edges()      # «46.02, 7.75, Zermatt» from the map on the page of Motion Watch
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
	"""height of the ground (0 everywhere except at a real place)"""
	return geo.height(x, z) if terrain else 0.0


func ground_hit(from: Vector3, d: Vector3):
	"""where a ray meets the ground (null if not within 400 m)"""
	if not terrain:
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
	if game != null:
		game.on_scene()                            # the game: new goal, players back to the start
	next_auto = now() + 8.0
	_update_sky()
	_update_temps()
	_sync_ui()
	return true


func _build_head() -> void:
	rig = Node3D.new()
	add_child(rig)
	head = Node3D.new()
	head.position = Vector3(0, HEAD_H, 0)
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
	pole.mesh = box(0.06, HEAD_H, 0.06)
	pole.position = Vector3(0, -HEAD_H / 2.0, 0)
	pole.material_override = mat(Color(0.2, 0.2, 0.2))
	head.add_child(pole)


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


func mover_home() -> void:
	rig.position = Vector3(0, ground_y(0, 0), 0)
	rig.rotation = Vector3.ZERO


func set_mover(on: bool) -> void:
	mover_on = on
	if chassis != null:
		chassis.visible = on
	if not on and rig != null:
		mover_home()


func _drive(dt: float) -> void:
	"""the mover drives: left / right track from Motion Watch (-1 … 1); stops when Motion Watch is quiet for 2.5 s (it stops the tracks itself after 0.6 s without the stick)"""
	if not mover_on:
		if rig.position != Vector3.ZERO or rig.rotation != Vector3.ZERO:
			mover_home()
		return
	var tnow := now()                                      # real time since the last call (frames are skipped to save CPU)
	dt = clampf(tnow - _drive_t, 0.0, 1.0) if _drive_t > 0.0 else dt
	_drive_t = tnow
	var d: Dictionary = mw.get("drive", {})
	var l := float(d.get("l", 0.0)) if now() - mw_t < 2.5 else 0.0
	var r := float(d.get("r", 0.0)) if now() - mw_t < 2.5 else 0.0
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


# ---- sounds of the world (for the microphone of Motion Watch) --------------------------------------------------------
func add_sound(db1m: float, pos: Vector3, secs: float) -> void:
	"""a sound: loudness at 1 m (dB, 0 = very loud), where, how long"""
	sounds.append([db1m, pos, now() + secs])


func sound_db() -> float:
	"""what the microphone at the head hears now (dB): quiet background + weather + wind + the sounds, weaker with distance"""
	var base := -62.0 if is_dark() else -56.0
	if weather == "rain":
		base = -40.0
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


func _update_lens() -> void:
	"""every 0.5 s: grain from the amplification (gain), raindrops when it rains, insects at night with light"""
	var dark := is_dark()
	if dark:                                                # copies of the sky / light settings with less colour
		for k in range(2):
			var e: Environment = env.duplicate()
			e.adjustment_enabled = true
			e.adjustment_saturation = 0.0 if k == 0 else 0.4
			night_envs[k] = e
	for i in range(lens_mats.size()):
		var amp: float = clamp((float(gain[i]) - 1.0) / max(0.5, gain_cap() - 1.0), 0.0, 1.0)
		var m: ShaderMaterial = lens_mats[i]
		m.set_shader_parameter("noise", lens_noise * (0.08 + 0.92 * (amp if dark else amp * 0.4)))
		m.set_shader_parameter("vignette", lens_vignette)
		m.set_shader_parameter("drops", (0.45 if i == 1 else 0.25) if lens_drops and weather == "rain" else 0.0)
	var L: Dictionary = mw.get("lights", {})
	var lit: bool = L.get("white", false) or L.get("ir", false) or (game != null and game.guard_auto)
	insects.emitting = insects_on and dark and lit and weather != "rain" and weather != "snow" and ambient > 6.0


func _build_view_camera() -> void:
	view_cam = Camera3D.new()
	view_cam.position = Vector3(6, 7, 9)
	view_cam.cull_mask = 1
	view_cam.fov = 70
	view_cam.far = 2000.0
	add_child(view_cam)
	view_cam.look_at(Vector3(0, 1, -8))
	view_cam.current = true


# ---- time, light, weather ------------------------------------------------------------------------------------------
func hour() -> float:
	return fposmod(hour0 + (now() - clock0) * speed / 3600.0, 24.0)


func set_hour(h: float) -> void:
	hour0 = fposmod(h, 24.0)
	clock0 = now()


var season := "today"                 # sun path: "today" (real date) or a month "1" .. "12" (from 3D-3.8)
var _sun_cache := [-1.0, Vector2.ZERO]
var _horizon := {}                    # real place: how high the hills are in a direction (2° steps) - mountain shadow


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
	return 0.015 + 0.04 * moon * (1.0 - clouds()) + 0.95 * day * (1.0 - 0.45 * clouds())


func is_dark() -> bool:
	return light_level() < 0.12


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
	moonlight.light_energy = 0.035 * moon * (1.0 - cl) * (1.0 - day)
	var top := Color(0.25, 0.45, 0.8).lerp(Color(0.55, 0.57, 0.6), cl)
	var hor := Color(0.7, 0.78, 0.88).lerp(Color(0.95, 0.65, 0.45), dusk).lerp(Color(0.7, 0.71, 0.72), cl * 0.8)
	var k: float = max(0.02, day)
	sky_mat.sky_top_color = top * k + Color(0.01, 0.015, 0.03) * (1.0 - k)
	sky_mat.sky_horizon_color = hor * k + Color(0.02, 0.025, 0.04) * (1.0 - k)
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = Color(0.1, 0.12, 0.08) * k if not terrain else sky_mat.sky_horizon_color * 0.9   # real place: haze below
	sky_mat.sky_energy_multiplier = 0.06 + 0.94 * day
	# light from the whole sky: bluish in the sun (shadows are never black, as outside), grey when cloudy, dark at night
	env.ambient_light_color = Color(0.6, 0.68, 0.85).lerp(Color(0.72, 0.72, 0.74), cl).lerp(Color(0.9, 0.7, 0.6), dusk * 0.5)
	env.ambient_light_energy = 0.03 + (0.55 + 0.25 * cl) * day
	var dens: float = {"clear": 0.0007, "cloudy": 0.0012, "rain": 0.006, "fog": 0.045, "snow": 0.012}.get(weather, 0.0008)
	env.fog_density = dens
	env.fog_light_color = Color(0.72, 0.74, 0.78) * (0.05 + 0.95 * day)
	rain.emitting = weather == "rain"
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
	window_mat.emission_energy_multiplier = 2.5 if dark else 0.0
	door_node.rotation.y = -1.3 if door_open else 0.0
	door_light.light_energy = 2.5 if door_open and dark else 0.0
	for l in lamps:
		l.light_energy = 2.2 if dark else 0.0
	for lm in lamp_mats:
		lm.emission_energy_multiplier = 3.0 if dark else 0.0
	for v in visitors.get_children():
		if v.has_method("set_night"):
			v.set_night(dark)


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
	if weather == "snow":
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
	tmat("sky").set_shader_parameter("temp", sky_t)       # the sky is a big dome only the thermal camera sees


# ---- every frame -----------------------------------------------------------------------------------------------------
var _slow_t := 0.0


func _process(dt: float) -> void:
	# minimized: Godot stops drawing then - but the cameras must go on for Motion Watch. mini.gd turns the window into a
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
		if _settings_dirty:
			_save_settings()
		if auto_update and not update_busy and now() > next_update_check:
			next_update_check = now() + UPDATE_EVERY
			run_update(true, false)
	if not sim_active:
		return                                   # pause: nothing moves, nothing is drawn (net.gd still answers)
	var s: Dictionary = mw.get("servo", {})
	# the servos turn like real ones: towards the new angle with a limited speed (no jumps)
	var want_pan := -deg_to_rad(float(s.get("pan_deg", 0.0)))
	var want_tilt := deg_to_rad(float(s.get("tilt_deg", 0.0)) - 6.0)
	if game != null and game.guard_auto:                 # the game: automatic guard or a player as guard turns the head
		want_pan = game.guard_yaw
		want_tilt = game.guard_tilt
	var step := deg_to_rad(SERVO_DEG_S) * dt
	_drive(dt)
	head.rotation.y = move_toward(head.rotation.y, want_pan, step)
	head_pitch.rotation.x = move_toward(head_pitch.rotation.x, want_tilt, step)
	cams[0].global_transform = head_pitch.global_transform.translated_local(Vector3(0, 0.0, -0.13))
	cams[2].global_transform = head_pitch.global_transform.translated_local(Vector3(0.12, 0.0, -0.12))
	var c1 := Transform3D(Basis.from_euler(Vector3(deg_to_rad(-10.0), -deg_to_rad(cam1_yaw), 0)), Vector3(-3.0, 2.4, 3.0))
	cams[1].global_transform = c1
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
	"""Motion Watch is connected: it sent its state lately or fetches pictures / thermal values"""
	if not stream_on:
		return false
	var t := now()
	return t - mw_t < 10.0 or not net.stream_demand().is_empty() or t - snap_want[0] < 10.0 or t - snap_want[1] < 10.0 or t - _th_asked < 10.0


func _check_active() -> void:
	"""every 0.5 s: is somebody looking? Window open -> everything; only Motion Watch -> the world moves, but the big
	3D view is not drawn and at most 30 pictures per second; nobody -> pause with 5 frames per second (only answering)"""
	var small: bool = mini_box != null and mini_box.mini
	win_open = not small and DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_MINIMIZED
	var conn := connected()
	var playing: bool = game != null and game.busy()
	var act: bool = win_open or conn or playing or (testrun != null and testrun.running) or not eco_idle
	if act != sim_active:
		sim_active = act
		visitors.process_mode = Node.PROCESS_MODE_INHERIT if act else Node.PROCESS_MODE_DISABLED
		if act:
			next_auto = max(next_auto, now() + 5.0)
		print("simulation " + ("runs" if act else "pauses (nobody looks)"))
	get_viewport().disable_3d = not win_open      # the big 3D view only when it can be seen
	Engine.max_fps = _fps0 if win_open else (60 if playing else (30 if sim_active else 5))


# ---- pictures for Motion Watch -------------------------------------------------------------------------------------
func _wanted_fps(i: int) -> float:
	var d: Dictionary = net.stream_demand() if net != null else {}
	var f: float = float(d.get(i, 0.0))
	if i < 2 and now() - snap_want[i] < 3.0:
		f = max(f, 2.0)
	if i == 0 and game != null and game.guard_watching():
		f = max(f, 8.0)                                  # a player guards: he sees through the head camera
	if i == 1 and game != null and game.guard2_watching():
		f = max(f, 6.0)                                  # a second guard sees through the fixed camera
	if i == 2 and now() - _th_asked < 3.0:
		f = max(f, 8.0)
	if preview_on and win_open:
		f = max(f, (2.0 if in_vm else 4.0) if i < 2 else (1.5 if in_vm else 3.0))
	return f


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
	ir_light.light_energy = 6.0 if (i == 0 and ir_on()) else 0.0   # infrared: only the NoIR camera sees it
	if i == 0:
		var grey: bool = ir_on() and dark and not white_light.light_energy > 0.0   # infrared picture: black and white
		cams[0].environment = (night_envs[0] if grey else night_envs[1]) if dark and night_envs[0] != null else null
	if i == 1:
		cams[1].environment = night_envs[1] if dark and night_envs[1] != null else null    # little light: little colour
	if i < 2 and expo_mats.size() > i:
		var ex: float = NIGHT_SCALE * gain[i] if dark else 1.0
		expo_mats[i].set_shader_parameter("expo", ex)
		lens_mats[i].set_shader_parameter("expo", ex)
	if i < 2:
		cam_attr[i].exposure_multiplier = gain[i] if not dark else 1.0   # at night the lens shader does the exposure
	vps[i].render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var img: Image = vps[i].get_texture().get_image()
	ir_light.light_energy = 0.0
	if img != null and not img.is_empty():
		if i < 2:
			_auto_exposure(i, img)
			jpgs[i] = img.save_jpg_to_buffer(0.8)
			frame_no[i] += 1
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
	if not cloud_shadows or weather in ["clear", "fog"]:
		return 1.0
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


func version() -> String:
	return VERSION


const NIGHT_SCALE := 0.15             # the night is rendered too bright for a camera: at night only this part reaches the sensor


func gain_cap() -> float:
	"""by day a camera may amplify up to 6×, at night only up to «Nachtverstärkung»: the picture stays dark like a real one"""
	return 6.0 if not is_dark() else night_gain


func ir_on() -> bool:
	"""infrared light: from Motion Watch, or from the game (the guard switches it on at night)"""
	var L: Dictionary = mw.get("lights", {})
	return L.get("ir", false) or (game != null and game.guard_auto and is_dark())


func _auto_exposure(i: int, img: Image) -> void:
	var small: Image = img.duplicate()
	small.resize(32, 18, Image.INTERPOLATE_BILINEAR)
	var sum := 0.0
	for y in range(6, 18):
		for x in range(32):
			var c := small.get_pixel(x, y)
			sum += (c.r + c.g + c.b) / 3.0
	var mean: float = max(0.01, sum / (12.0 * 32.0))
	var want: float = clamp(gain[i] * 0.35 / mean, 0.6, gain_cap())
	gain[i] += (want - gain[i]) * 0.25
	gain[i] = min(gain[i], gain_cap())


func _decode_thermal(img: Image) -> void:
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	var d := img.get_data()
	var w := img.get_width()
	var out := PackedFloat32Array()
	out.resize(TH_W * TH_H)
	for y in range(TH_H):
		for x in range(TH_W):
			var a := ((2 * y) * w + 2 * x) * 4
			var b := a + w * 4
			var t := (th_lut[d[a]] + th_lut[d[a + 4]] + th_lut[d[b]] + th_lut[d[b + 4]]) * 0.25
			out[y * TH_W + x] = t + randf_range(-0.08, 0.08)
	thermal = out
	if preview_on:
		_thermal_preview()


func _thermal_preview() -> void:
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
	return jpgs[i]


func want_snapshot(i: int) -> void:
	snap_want[i] = now()


func thermal_values() -> PackedFloat32Array:
	_th_asked = now()
	return thermal


# ---- protocol with Motion Watch -------------------------------------------------------------------------------------
func on_state(d: Dictionary, host: String) -> void:
	var old_sound: String = str(mw.get("sound", ""))
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


func world_reply() -> Dictionary:
	var press := pressure
	if storm_t > 0.0:
		press -= min(6.0, (now() - storm_t) / 180.0 * 6.0)
	var t := Time.get_datetime_dict_from_system()
	var midnight: float = now() - (t.hour * 3600 + t.minute * 60 + t.second)
	return {"v": 1, "ok": true, "sim_time": midnight + hour() * 3600.0, "dark": is_dark(), "ambient_c": snappedf(ambient, 0.1),
			"pressure_hpa": snappedf(press, 0.1), "wind_kmh": snappedf(wind, 0.1), "last_event": next_event_id - 1,
			"pid": OS.get_process_id(), "active": sim_active, "sound_db": snappedf(sound_db(), 0.1) if sound_on else null,
			"weather": weather, "humidity": humidity, "mover": mover_on}


func info() -> Dictionary:
	return {"v": 1, "name": "Motion Watch 3D-Simulator %s" % VERSION,
			"cameras": [{"id": 0, "name": "Head camera (NoIR)", "w": CAM_W[0], "h": CAM_H[0], "fps": CAM_FPS[0], "fov_h": CAM_FOV[0], "fov_v": 41.0, "on_head": true, "noir": true},
						{"id": 1, "name": "Fixed camera", "w": CAM_W[1], "h": CAM_H[1], "fps": CAM_FPS[1], "fov_h": CAM_FOV[1], "fov_v": 62.0, "on_head": false, "noir": false}],
			"thermal": {"w": TH_W, "h": TH_H, "fps": 8.0, "fov_h": TH_FOV, "fov_v": 35.0, "unit": "C", "on_head": true},
			"sensors": [{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"}, {"name": "Gas Wohnwagen", "kind": "gas"}, {"name": "Velo", "kind": "tag"}]}


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
	var depth := randf_range(6.0, 22.0)
	var side := 1.0 if randf() < 0.5 else -1.0
	var a: Vector3 = from if from != null else Vector3(-side * (depth * 1.6 + 6.0), 0, -depth)
	var b: Vector3 = to if to != null else Vector3(side * (depth * 1.6 + 6.0), 0, -depth)
	var spd: float = {"person": 1.3, "child": 1.0, "jogger": 2.8, "fox": 2.0, "boar": 1.5, "deer": 1.6, "cat": 1.1, "dog": 1.8, "badger": 0.9,
			"hare": 1.9, "hedgehog": 0.3, "car": 11.0}.get(kind, 1.3)
	var v = Actor.new()
	visitors.add_child(v)
	v.setup(self, kind, a, b, spd * randf_range(0.85, 1.15))
	v.set_night(is_dark())
	return v


func car() -> void:
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
			var v = spawn("car", path[0], path[1])
			for i in range(2, path.size()):
				v.route.append(path[i])
			return
	var z: float = scenes.data.get("road_z", -28.0)
	spawn("car", Vector3(-side * 90.0, 0, z - side * 1.2), Vector3(side * 90.0, 0, z - side * 1.2))


func visit(k: String) -> void:
	"""a visitor that fits the scene: also the special ones (a car parks, somebody sits on the bench, an animal comes to the feeder)"""
	if k == "car":
		car()
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
		dg.leader = w
		dg.speed = w.speed * 1.6
		dg.follow_off = Vector3(randf_range(-1.2, 1.2), 0, randf_range(0.8, 2.0))
	elif k == "herd":                                          # a few deer together
		var lead = spawn("deer")
		for i in range(randi_range(1, 3)):
			var o := Vector3(randf_range(-2.5, 2.5), 0, randf_range(1.0, 3.5))
			var d2 = spawn("deer", lead.position + o, lead.target + o)
			d2.speed = lead.speed
			if randf() < 0.5:
				d2.body_root.scale *= 0.7                        # a young one
	elif k == "garden_person":
		var side := 1.0 if randf() < 0.5 else -1.0
		var g = spawn("person", Vector3(side * 35.0, 0, -30.5), Vector3(0, 0, -30.0))
		scenes.garden_route(g)
	else:
		spawn(k)


func thief() -> void:
	"""somebody sneaks to the bike, kneels at it with a torch, then goes to the caravan door - and runs away"""
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
		var kinds := _mixed(au[0])
		if visitors.get_child_count() < max_visitors and not kinds.is_empty():
			visit(kinds[randi() % kinds.size()])
		next_auto = t + randf_range(au[1], au[2]) / max(0.1, visit_rate)
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
		if v.kind == "person" and v.torch != null and v.route.size() > 0 and str(mw.get("sound", "")) != "":
			v.route = [Vector3(v.position.x + 40.0, 0, v.position.z + 10.0)]      # the siren: the thief runs away
			v.target = v.route.pop_front()
			v.speed = 4.0
			v.crouch = 0.0
			v.wait_until = 0.0


const PEOPLE_KINDS := ["person", "child", "jogger", "dogwalk", "bench", "garden_person", "car_park", "car"]


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
# [group, symbol (window: drawn; page of Motion Watch: emoji), parts in their order]
const GROUPS := [["Szene", "globe", "🌍", ["", "Ort von der Karte", "Zeit"]],
		["Wetter", "cloud", "🌦", ["", "Mehr Wetter", "Natur und Wind"]],
		["Besuch", "person", "🚶", ["Besucher hinsetzen", "Besucher schicken", "Von selbst", "In bestimmten Szenen", "Verhalten"]],
		["Kamerabild", "lens", "👁", ["", "Feineinstellungen"]],
		["Sensoren", "bell", "🔔", [""]],
		["Mover", "track", "🚜", [""]],
		["Spiel", "pad", "🎮", ["Runde", "Regeln", "Anzeige"]],
		["Wildbeobachtung", "target", "🎯", [""]],
		["Testlauf", "check", "✅", [""]],
		["System", "gear", "⚙", ["Grafik", "Start mit dem PC", "Updates"]]]
# id -> [group, part]; not listed: the group given in add_control, no part
const PLACE := {"ort_map": ["Szene", "Ort von der Karte"], "ort": ["Szene", "Ort von der Karte"], "speed": ["Szene", "Zeit"], "moon": ["Szene", "Zeit"], "season": ["Szene", "Zeit"],
		"cam1_yaw": ["Kamerabild", "Feineinstellungen"], "humidity": ["Wetter", "Mehr Wetter"], "pressure": ["Wetter", "Mehr Wetter"],
		"storm": ["Wetter", "Mehr Wetter"], "cloud_shadows": ["Wetter", "Mehr Wetter"], "gusts": ["Wetter", "Natur und Wind"],
		"world_cloth": ["Wetter", "Natur und Wind"], "world_smoke": ["Wetter", "Natur und Wind"], "world_fireflies": ["Wetter", "Natur und Wind"],
		"meadow": ["Wetter", "Natur und Wind"], "car": ["Besuch", "Besucher schicken"], "thief": ["Besuch", "Besucher schicken"],
		"dogwalk": ["Besuch", "Besucher schicken"], "herd": ["Besuch", "Besucher schicken"], "clear": ["Besuch", "Besucher schicken"],
		"car_park": ["Besuch", "In bestimmten Szenen"], "bench": ["Besuch", "In bestimmten Szenen"], "feed": ["Besuch", "In bestimmten Szenen"],
		"garden_person": ["Besuch", "In bestimmten Szenen"], "auto": ["Besuch", "Von selbst"], "mix": ["Besuch", "Von selbst"],
		"visit_rate": ["Besuch", "Von selbst"], "max_visitors": ["Besuch", "Von selbst"], "visitor_speed": ["Besuch", "Verhalten"],
		"lamp_share": ["Besuch", "Verhalten"], "look_at_light": ["Besuch", "Verhalten"], "flee_light": ["Besuch", "Verhalten"],
		"flee_sound": ["Besuch", "Verhalten"], "avoid_on": ["Besuch", "Verhalten"], "lens_vignette": ["Kamerabild", "Feineinstellungen"],
		"sound_on": ["Kamerabild", "Feineinstellungen"], "game_open": ["Spiel", "Runde"], "game_start": ["Spiel", "Runde"],
		"game_stop": ["Spiel", "Runde"], "game_minutes": ["Spiel", "Runde"], "game_mode": ["Spiel", "Runde"], "game_goal": ["Spiel", "Runde"],
		"game_level": ["Spiel", "Regeln"], "game_lives": ["Spiel", "Regeln"], "game_items": ["Spiel", "Regeln"], "game_teams": ["Spiel", "Regeln"],
		"game_rescue": ["Spiel", "Regeln"], "game_teamgoal": ["Spiel", "Regeln"], "game_stones": ["Spiel", "Regeln"], "game_noise": ["Spiel", "Regeln"],
		"game_random": ["Spiel", "Regeln"], "game_guard": ["Spiel", "Regeln"], "game_cones": ["Spiel", "Anzeige"], "game_quality": ["Spiel", "Anzeige"],
		"quality": ["System", "Grafik"], "eco_idle": ["System", "Grafik"], "autostart": ["System", "Start mit dem PC"],
		"autostart_min": ["System", "Start mit dem PC"], "autostart_mwpc": ["System", "Start mit dem PC"], "autostart_lock": ["System", "Start mit dem PC"],
		"autologon": ["System", "Start mit dem PC"], "auto_update": ["System", "Updates"], "update_now": ["System", "Updates"]}


func _order_controls() -> void:
	"""every setting into its group and part, sorted like GROUPS (the window and the page of Motion Watch show this order)"""
	var gi := {}
	for i in range(GROUPS.size()):
		gi[GROUPS[i][0]] = i
	var keyed := []
	for i in range(controls.size()):
		var c: Dictionary = controls[i]
		c.extra = c.extra.duplicate()                     # several controls share one dictionary ({"expert": true})
		var pl = PLACE.get(c.id, null)
		if pl == null and str(c.id).begins_with("spawn_"):
			pl = ["Besuch", "Besucher schicken"]
		if pl != null:
			c.group = pl[0]
			c.extra["sub"] = pl[1]
		var g: int = gi.get(c.group, GROUPS.size())
		var sub := str(c.extra.get("sub", ""))
		c.extra["icon"] = GROUPS[g][2] if g < GROUPS.size() else ""
		c.extra["iconk"] = GROUPS[g][1] if g < GROUPS.size() else ""          # the drawn symbol (page of Motion Watch from 2.93.16)
		var si: int = (GROUPS[g][3] as Array).find(sub) if g < GROUPS.size() else 0
		keyed.append([g * 1000 + max(si, 0) * 100, i, c])
	keyed.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	controls = keyed.map(func(k): return k[2])


func _register_controls() -> void:
	"""every setting of the simulator - for the window and for the web page of Motion Watch (CONTROL protocol).
	extra "expert": true = only shown with «Experte» in the window (the web page always shows everything)."""
	var sc := []
	for s in Scenes.LIST:
		sc.append([s[0], s[1]])
	var ex := {"expert": true}
	add_control("select", "scene", "Szene", func(): return scene, func(v): set_scene(v), "Szene", {"options": sc})
	add_control("map", "ort_map", "Ort auf der Karte wählen (Schweiz)", func(): return "%.6f, %.6f" % [ort_lat, ort_lon] if ort_lat != 0.0 else "",
			func(v): set_place_text(str(v)), "Ort von der Karte")
	add_control("text", "ort", "Ort (Name oder Koordinaten, z. B. «Zermatt» oder «46.0207, 7.7491»)", func(): return place_label(), func(v): set_place_text(str(v)), "Ort von der Karte")
	add_control("slider", "hour", "Uhrzeit", func(): return snappedf(hour(), 0.01), func(v): set_hour(v), "Szene", {"min": 0, "max": 23.75, "step": 0.25, "unit": "h"})
	add_control("select", "season", "Jahreszeit (Sonnenbahn)", func(): return season, func(v): season = str(v); _sun_cache = [-1.0, Vector2.ZERO]; _update_sky(), "Szene",
			{"options": [["today", "wie heute (echtes Datum)"], ["1", "Januar"], ["2", "Februar"], ["3", "März"], ["4", "April"], ["5", "Mai"], ["6", "Juni"],
			["7", "Juli"], ["8", "August"], ["9", "September"], ["10", "Oktober"], ["11", "November"], ["12", "Dezember"]]})
	add_control("slider", "speed", "Zeit läuft x-fach", func(): return speed, func(v): _set_speed(v), "Szene", {"min": 1, "max": 120, "step": 1, "unit": "×", "expert": true})
	add_control("slider", "moon", "Mond", func(): return moon, func(v): moon = v, "Szene", {"min": 0, "max": 1, "step": 0.1, "expert": true})
	add_control("slider", "cam1_yaw", "Kamera 1: Richtung", func(): return cam1_yaw, func(v): cam1_yaw = v, "Szene", {"min": -90, "max": 90, "step": 1, "unit": "°", "expert": true})
	add_control("select", "weather", "Wetter", func(): return weather, func(v): weather = v, "Wetter",
			{"options": [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]]})
	add_control("toggle", "world_cloth", "Fahnen und Wäsche im Wind", func(): return world_cloth, func(v): set_cloth(v), "Wetter", ex)
	add_control("toggle", "world_smoke", "Rauch aus Kaminen", func(): return world_smoke, func(v): set_smoke(v), "Wetter", ex)
	add_control("toggle", "world_fireflies", "Glühwürmchen in warmen Nächten", func(): return world_fireflies, func(v): world_fireflies = v, "Wetter", ex)
	add_control("toggle", "gusts", "Wind in Böen", func(): return gusts, func(v): gusts = v, "Wetter", ex)
	add_control("toggle", "cloud_shadows", "Wolkenschatten (die Helligkeit wechselt)", func(): return cloud_shadows, func(v): cloud_shadows = v, "Wetter", ex)
	add_control("slider", "lamp_share", "Nachts mit Stirnlampe oder Handylicht", func(): return lamp_share, func(v): lamp_share = v, "Besuch", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	add_control("toggle", "look_at_light", "Menschen schauen zum Licht, wenn es angeht", func(): return look_at_light, func(v): look_at_light = v, "Besuch", ex)
	add_control("slider", "wind", "Wind", func(): return wind, func(v): wind = v, "Wetter", {"min": 0, "max": 120, "step": 1, "unit": "km/h"})
	add_control("slider", "ambient", "Temperatur", func(): return ambient, func(v): ambient = v, "Wetter", {"min": -15, "max": 40, "step": 0.5, "unit": "°C"})
	add_control("slider", "humidity", "Luftfeuchtigkeit", func(): return humidity, func(v): humidity = v, "Wetter", {"min": 10, "max": 100, "step": 1, "unit": "%", "expert": true})
	add_control("slider", "pressure", "Luftdruck", func(): return pressure, func(v): pressure = v, "Wetter", {"min": 960, "max": 1040, "step": 0.5, "unit": "hPa", "expert": true})
	add_control("button", "storm", "Sturm zieht auf", null, func(): storm_t = now(), "Wetter", ex)
	# visitors: one button each (the window has the pictures to drag, the web page these buttons)
	for k in VISITOR_LIST:
		add_control("button", "spawn_" + k[0], k[1], null, func(): visit(k[0]), "Besuch")
	add_control("button", "car", "Auto", null, func(): car(), "Besuch")
	add_control("button", "thief", "Dieb (Velo, Tür)", null, func(): thief(), "Besuch")
	add_control("button", "dogwalk", "Spaziergang mit Hund", null, func(): visit("dogwalk"), "Besuch")
	add_control("button", "herd", "Rehrudel", null, func(): visit("herd"), "Besuch")
	add_control("button", "car_park", "Auto parkiert (Parkplatz)", null, func(): visit("car_park"), "Besuch", ex)
	add_control("button", "bench", "Besuch setzt sich auf die Bank (Lustiger Platz)", null, func(): visit("bench"), "Besuch", ex)
	add_control("button", "feed", "Reh kommt zur Futterstelle (Wildbeobachtung)", null, func(): visit("feed_deer"), "Besuch", ex)
	add_control("button", "garden_person", "Besuch kommt durchs Gartentor (Garten)", null, func(): visit("garden_person"), "Besuch", ex)
	add_control("button", "clear", "Alle Besucher weg", null, func(): clear_visitors(), "Besuch")
	add_control("toggle", "auto", "ab und zu Besuch von selbst", func(): return auto_visitors, func(v): auto_visitors = v, "Besuch")
	add_control("select", "mix", "Wer kommt", func(): return mix, func(v): mix = v, "Besuch",
			{"options": [["mixed", "Tiere und Menschen"], ["more_animals", "mehr Tiere"], ["more_people", "mehr Menschen"], ["animals", "nur Tiere"], ["people", "nur Menschen"]]})
	add_control("slider", "visit_rate", "Wie oft Besuch kommt", func(): return visit_rate, func(v): visit_rate = v, "Besuch", {"min": 0.25, "max": 4.0, "step": 0.25, "unit": "×"})
	add_control("slider", "max_visitors", "Höchstens gleichzeitig", func(): return max_visitors, func(v): max_visitors = int(v), "Besuch", {"min": 1, "max": 30, "step": 1, "expert": true})
	add_control("slider", "visitor_speed", "Tempo der Besucher", func(): return visitor_speed, func(v): visitor_speed = v, "Besuch", {"min": 0.25, "max": 2.5, "step": 0.05, "unit": "×", "expert": true})
	add_control("toggle", "flee_light", "Tiere flüchten nachts vor dem weissen Licht", func(): return flee_light, func(v): flee_light = v, "Besuch", ex)
	add_control("toggle", "flee_sound", "Tiere flüchten vor der Sirene", func(): return flee_sound, func(v): flee_sound = v, "Besuch", ex)
	add_control("toggle", "avoid_on", "Um Bäume, Häuser und Fahrzeuge herumgehen", func(): return avoid_on, func(v): avoid_on = v, "Besuch", ex)
	add_control("slider", "lens_noise", "Bildrauschen (nachts stärker)", func(): return lens_noise, func(v): lens_noise = v, "Kamerabild", {"min": 0, "max": 1, "step": 0.05})
	add_control("slider", "night_gain", "Nachtverstärkung der Kameras (höchstens)", func(): return night_gain, func(v): night_gain = v, "Kamerabild", {"min": 1, "max": 8, "step": 0.5, "unit": "×"})
	add_control("slider", "ir_range", "Reichweite des Infrarot-Lichts", func(): return ir_range, func(v): ir_range = v, "Kamerabild", {"min": 4, "max": 30, "step": 1, "unit": "m"})
	add_control("slider", "lens_vignette", "Dunkle Bildecken", func(): return lens_vignette, func(v): lens_vignette = v, "Kamerabild", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	add_control("toggle", "lens_drops", "Regentropfen auf der Linse", func(): return lens_drops, func(v): lens_drops = v, "Kamerabild")
	add_control("toggle", "sound_on", "Geräusche der Welt ans Mikrofon von Motion Watch", func(): return sound_on, func(v): sound_on = v, "Kamerabild", ex)
	add_control("toggle", "insects", "Insekten am Licht (nachts, lösen wie echt Bewegung aus)", func(): return insects_on, func(v): insects_on = v, "Kamerabild")
	add_control("toggle", "mover_on", "Mover (Kettenfahrzeug) simulieren – Motion Watch zeigt dann einen zweiten Stick zum Fahren", func(): return mover_on, func(v): set_mover(v), "Mover")
	add_control("slider", "mover_max", "Höchstgeschwindigkeit des Movers", func(): return mover_max, func(v): mover_max = v, "Mover", {"min": 0.2, "max": 2.0, "step": 0.1, "unit": "m/s"})
	add_control("button", "mover_home", "Mover zurück an den Startplatz", null, func(): mover_home(), "Mover")
	add_control("toggle", "door", "Wohnwagentür offen", func(): return door_open, func(v): set_door(v), "Sensoren")
	add_control("toggle", "gas", "Gas / Rauch", func(): return gas_on, func(v): set_gas(v), "Sensoren")
	add_control("button", "pir", "PIR Zelt auslösen", null, func(): add_event("PIR Zelt", "pir"), "Sensoren")
	add_control("button", "bike", "Velo bewegen", null, func(): add_event("Velo", "tag"), "Sensoren")
	add_control("button", "nighttest", "Nacht-Test starten (2 Min.)", null, func(): night_test(), "Sensoren")
	add_control("toggle", "rifle", "Gewehr (unblutig, nur Tiere)", func(): return rifle_on, func(v): rifle_on = v, "Wildbeobachtung")
	add_control("button", "shoot_head", "Schuss aus der Kopfkamera", null, func(): shoot_head(), "Wildbeobachtung")
	add_control("button", "score0", "Punkte auf 0", null, func(): reset_score(), "Wildbeobachtung")
	add_control("toggle", "auto_update", "Neue Versionen automatisch installieren", func(): return auto_update, func(v): set_auto_update(v), "Updates")
	add_control("button", "update_now", "Jetzt nach Updates suchen und installieren", null, func(): run_update(true, false), "Updates")
	add_control("button", "testrun_start", "Testlauf starten (etwa 4 Minuten, Motion Watch muss verbunden sein)", null, func(): testrun.start(), "Testlauf")
	add_control("button", "testrun_stop", "Testlauf abbrechen", null, func(): testrun.stop(false), "Testlauf")
	add_control("button", "testrun_open", "Letzten Bericht öffnen", null, func(): testrun.open_report(), "Testlauf")
	add_control("toggle", "game_open", "Spiel öffnen (Handys können mitspielen)", func(): return game.open, func(v): game.set_open(v), "Spiel")
	add_control("button", "game_start", "Runde starten", null, func(): game.start_round(), "Spiel")
	add_control("button", "game_stop", "Runde beenden", null, func(): game.end_round(), "Spiel")
	add_control("slider", "game_minutes", "Dauer einer Runde", func(): return game_minutes, func(v): game_minutes = v, "Spiel", {"min": 1, "max": 15, "step": 1, "unit": "min"})
	add_control("select", "game_mode", "Spielart", func(): return game_mode, func(v): game_mode = v, "Spiel",
			{"options": [["camera", "Alle gegen die Kamera"], ["guard", "Ein Spieler ist Wächter"], ["teamguard", "Team gegen Team (Räuber und Wächter)"], ["mw", "Motion Watch entscheidet (echte Erkennung)"]]})
	add_control("select", "game_level", "Wächter", func(): return game_level, func(v): game_level = v, "Spiel",
			{"options": [["easy", "leicht"], ["normal", "normal"], ["hard", "schwer"]]})
	add_control("select", "game_lives", "Leben", func(): return str(game_lives), func(v): game_lives = int(v), "Spiel",
			{"options": [["0", "unbegrenzt"], ["3", "3 Leben"], ["1", "1 Leben"]]})
	add_control("slider", "game_items", "Kristalle zum Sammeln", func(): return game_items, func(v): game_items = int(v), "Spiel", {"min": 0, "max": 6, "step": 1})
	add_control("toggle", "game_teams", "Zwei Teams (Rot gegen Blau)", func(): return game_teams, func(v): game_teams = v; game.on_teams(), "Spiel")
	add_control("toggle", "game_rescue", "Befreien: Erwischte kommen in die Zelle, ein Teamkollege befreit sie", func(): return game_rescue, func(v): game_rescue = v, "Spiel")
	add_control("toggle", "game_teamgoal", "Team-Ziel: das Ziel öffnet erst, wenn alle Kristalle gefunden sind", func(): return game_teamgoal, func(v): game_teamgoal = v, "Spiel", ex)
	add_control("select", "game_goal", "Spielziel", func(): return game_goal, func(v): game_goal = v, "Spiel",
			{"options": [["reach", "Zum Ziel schleichen"], ["return", "Beute holen und zurückbringen"], ["flag", "Fahne erobern (zwei Teams)"]]})
	add_control("toggle", "game_stones", "Steine werfen zum Ablenken", func(): return game_stones, func(v): game_stones = v, "Spiel")
	add_control("toggle", "game_noise", "Mikrofon hört laute Schritte", func(): return game_noise, func(v): game_noise = v, "Spiel", ex)
	add_control("toggle", "game_cones", "Sichtfeld der Kameras zeigen (für Anfänger)", func(): return game_cones, func(v): game_cones = v, "Spiel")
	add_control("toggle", "game_random", "Start und Ziel zufällig", func(): return game_random, func(v): game_random = v, "Spiel", ex)
	add_control("select", "game_quality", "Bild auf dem Handy", func(): return game_quality, func(v): game_quality = v, "Spiel",
			{"options": [["small", "klein (schnell)"], ["mid", "mittel"], ["big", "gross (braucht mehr Leistung)"]], "expert": true})
	add_control("toggle", "game_guard", "Ohne Motion Watch bewacht der Kopf selbst", func(): return game_guard, func(v): game_guard = v, "Spiel", ex)
	add_control("toggle", "autostart", "Mit dem PC starten (sendet gleich an Motion Watch)", func(): return autostart_on, func(v): set_autostart(v), "Start mit dem PC")
	add_control("toggle", "autostart_min", "Dabei klein (nur das Kästchen in der Ecke)", func(): return autostart_min, func(v): autostart_min = v, "Start mit dem PC")
	add_control("toggle", "autostart_mwpc", "Dabei auch Motion Watch auf diesem PC starten (ohne Pi)", func(): return autostart_mwpc, func(v): autostart_mwpc = v, "Start mit dem PC")
	if OS.get_name() == "Windows":
		add_control("toggle", "autostart_lock", "Danach den Bildschirm sperren", func(): return autostart_lock, func(v): autostart_lock = v, "Start mit dem PC")
		add_control("button", "autologon", "Ohne Anmelden: automatische Anmeldung von Windows einrichten …", null, func(): setup_autologon(), "Start mit dem PC", {"expert": true})
	add_control("select", "quality", "Grafik", func(): return quality, func(v): _set_quality(v), "Grafik",
			{"options": [["simple", "einfach (schnell)"], ["nice", "schön (Schatten, Leuchten)"]]})
	add_control("toggle", "eco_idle", "Strom sparen: nur rechnen, wenn das Fenster offen ist oder Motion Watch verbunden ist", func(): return eco_idle, func(v): eco_idle = v, "Grafik", ex)
	add_control("toggle", "meadow", "Gras und Blumen auf der Wiese", func(): return meadow_on, func(v): set_meadow(v), "Grafik", ex)


const VISITOR_LIST := [["person", "Person"], ["child", "Kind"], ["jogger", "Jogger"], ["fox", "Fuchs"], ["deer", "Reh"], ["boar", "Wildschwein"],
		["cat", "Katze"], ["dog", "Hund"], ["badger", "Dachs"], ["hare", "Hase"], ["hedgehog", "Igel"]]
var meadow_on := true


func set_meadow(on: bool) -> void:
	meadow_on = on
	for n in get_tree().get_nodes_in_group("meadow"):
		n.visible = on


func clear_visitors() -> void:
	for v in visitors.get_children():
		v.queue_free()


func _set_speed(v: float) -> void:
	set_hour(hour())
	speed = v


func _set_quality(v: String) -> void:
	quality = v
	_apply_quality()


func _apply_quality() -> void:
	var nice := quality == "nice"
	sun.shadow_enabled = nice
	white_light.shadow_enabled = nice
	env.glow_enabled = nice
	for i in range(2):
		vps[i].msaa_3d = Viewport.MSAA_2X if nice else Viewport.MSAA_DISABLED
	get_viewport().msaa_3d = Viewport.MSAA_2X if nice else Viewport.MSAA_DISABLED


func control_info() -> Dictionary:
	var out := []
	for c in controls:
		var d := {"type": c.type, "id": c.id, "label": c.label, "group": c.group}
		d.merge(c.extra)
		if c["get"] != null:
			var v = c["get"].call()
			d["value"] = snappedf(v, 0.001) if typeof(v) == TYPE_FLOAT else v
		out.append(d)
	return {"ok": true, "v": 1, "name": "Motion Watch 3D-Simulator %s" % VERSION,
				"scenarios": scenarios(), "scenario": scene,
			"controls": out, "status": status_text(), "upload": null}


func control(d: Dictionary) -> Dictionary:
	var a := str(d.get("action", "get"))
	var cid := str(d.get("id", ""))
	if a == "scenario":
		if not set_scene(cid):
			return {"ok": false, "error": "unknown scenario"}
	elif a == "delete":
		return {"ok": false, "error": "cannot be deleted"}
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
	elif a == "test_report":                           # the test run: progress and the last report
		return {"ok": true, "running": testrun.running, "info": testrun.info, "report": testrun.report}
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
				"goal_y": [snappedf(game.goal.y, 0.01), snappedf(ground_y(game.goal.x, game.goal.z), 0.01)], "insects": insects.emitting}
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
		show_panel(true)
		(ui_box.get_parent() as ScrollContainer).set_deferred("scroll_vertical", int(d.get("y", 0)))
		return {"ok": true, "max": (ui_box.get_parent() as ScrollContainer).get_v_scroll_bar().max_value}
	elif a == "geo":                                   # for tests: the place (loading, what was built)
		return {"ok": true, "busy": geo.busy, "loaded": geo.loaded, "info": geo.info, "counts": geo.counts, "terrain": terrain,
				"h0": geo.h0, "src": geo.dem_source, "note": geo_note, "y": ground_y(float(d.get("x", 0.0)), float(d.get("z", 0.0))),
				"map": karte.visible, "map_info": karte.status_text(), "dark": is_dark(), "anims": anims.size(), "b3d_night": geo.b3d_mat.get_shader_parameter("night") if geo.b3d_mat != null else -1, "sun": [snappedf(sun_pos().x, 0.1), snappedf(sun_pos().y, 0.1),
				snappedf(horizon_el(sun_pos().y), 0.1), sun_behind_hills(), snappedf(sun.light_energy, 0.01)]}
	elif a == "map":                                   # for tests: open the map at a place, zoom
		show_panel(false)
		karte.open(float(d.get("lat", 46.95)), float(d.get("lon", 7.44)), int(d.get("zoom", 0)))
		return {"ok": true}
	elif a == "mover":                                 # for tests: where the mover is
		return {"ok": true, "on": mover_on, "x": snappedf(rig.position.x, 0.01), "z": snappedf(rig.position.z, 0.01),
				"yaw": snappedf(rad_to_deg(rig.rotation.y), 0.1), "drive": mw.get("drive", {}),
				"near": _ob_near(Vector2(rig.position.x, rig.position.z - 0.3)).map(func(o): return [o["c"], _ob_closest(o, Vector2(rig.position.x, rig.position.z))[1]])}
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
			out.append({"kind": v.kind, "x": snappedf(v.position.x, 0.01), "z": snappedf(v.position.z, 0.01), "gap": snappedf(deepest, 0.01), "r": v.radius,
					"y": snappedf(v.position.y, 0.01), "sx": int(sp.x), "sy": int(sp.y), "selected": v == selected})
		return {"ok": true, "visitors": out}
	elif a == "spawn_at":                              # for tests: a visitor from one point to another
		var f: Array = d.get("from", [0, 0])
		var t: Array = d.get("to", [10, 0])
		var sv = spawn(str(d.get("kind", "person")), Vector3(float(f[0]), 0, float(f[1])), Vector3(float(t[0]), 0, float(t[1])))
		if d.has("wait"):                              # stand there for a while, looking at the head camera
			sv.route = [[Vector3(float(t[0]), 0, float(t[1])), float(d["wait"]), 0.0, Vector3(0, 0, 0)], Vector3(float(t[0]) + 40.0, 0, float(t[1]))]
			sv.next_idle = now() + 999.0
		return {"ok": true}
	elif a == "set" or a == "press":
		var c = null
		for x in controls:
			if x.id == cid:
				c = x
		if c == null or c["set"] == null:
			return {"ok": false, "error": "unknown control"}
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
	var mwc := "verbunden mit %s" % str(mw.get("device", "Motion Watch")) if now() - mw_t < 3.0 else ("Motion Watch nicht verbunden" if stream_on else "Senden aus")
	var score := " · Treffer %d von %d Schüssen, %d Punkte" % [hits, shots, points] if rifle_on else ""
	return "%s · %02d:%02d · %s · %s · %.1f °C · Besucher %d%s · %s" % [Scenes.name_of(scene), int(h), int(fmod(h, 1.0) * 60), "Nacht" if is_dark() else "Tag", {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(weather, weather), ambient, visitors.get_child_count(), score, mwc] + (" · Update: " + update_info if update_info != "" else "") + (" · " + start_info if start_info != "" else "") + (" · " + game.status() if game != null and game.status() != "" else "") + (" · " + testrun.status() if testrun != null and testrun.status() != "" else "") + (" · " + geo.info if geo != null and geo.busy else "") + (" · " + geo_note if geo_note != "" else "")


func scenarios() -> Array:
	var out := []
	for s in Scenes.LIST:
		out.append({"id": s[0], "name": s[1] + " (3D)", "kind": "world", "deletable": false})
	return out


# ---- the window on the PC ------------------------------------------------------------------------------------------------
var ui_root: Control
var ui_box: VBoxContainer             # the content of the panel (must never be wider than the panel)
var prev0: TextureRect
var prev1: TextureRect
var prevt: TextureRect
var info_label: Label


func _build_ui() -> void:
	"""the window: phone on the left, on the right the panel in the look of the web page of Motion Watch (ui_style.gd):
	toolbar (hide, search, groups only, expand all, collapse all), cards, at the bottom «Einfach | Experte»"""
	var layer := CanvasLayer.new()
	add_child(layer)
	var th: Theme = UI.theme()
	phone = Phone.new()
	phone.main = self
	phone.position = Vector2(0, 0)
	phone.theme = th
	layer.add_child(phone)
	_build_crosshair(layer)
	_build_view_bar(layer, th)
	karte = Karte.new()
	karte.main = self
	karte.theme = th
	karte.visible = false
	layer.add_child(karte)
	var panel := PanelContainer.new()
	panel.theme = th
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -392
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
	var logo := PanelContainer.new()
	logo.add_theme_stylebox_override("panel", UI.box(UI.ORG, UI.ORG, 7, 2, 0))
	logo.custom_minimum_size = Vector2(26, 26)
	var ll := Label.new()
	ll.text = "3D"
	ll.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ll.add_theme_font_override("font", UI.heading_font())
	ll.add_theme_font_size_override("font_size", 11)
	ll.add_theme_color_override("font_color", Color.WHITE)
	logo.add_child(ll)
	hdr.add_child(logo)
	var title := Label.new()
	title.text = "Motion Watch"
	title.add_theme_font_override("font", UI.heading_font())
	title.add_theme_font_size_override("font_size", 17)
	hdr.add_child(title)
	var ver := UI.small("3D-Simulator %s" % VERSION)
	ver.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	hdr.add_child(ver)
	# toolbar like above the settings of Motion Watch
	var tb := HBoxContainer.new()
	tb.add_theme_constant_override("separation", 6)
	top_box.add_child(tb)
	var hide_b := UI.icon_button("hide", "Bedienfeld ausblenden (H)")
	hide_b.pressed.connect(func(): show_panel(false))
	tb.add_child(hide_b)
	search_in = UI.search_field("Einstellung suchen …")
	search_in.text_changed.connect(_search)
	tb.add_child(search_in)
	var gb := UI.icon_button("groups", "Nur Gruppen")
	gb.pressed.connect(func(): _fold_all("groups"))
	tb.add_child(gb)
	var ob := UI.icon_button("open", "Alle aufklappen")
	ob.pressed.connect(func(): _fold_all("open"))
	tb.add_child(ob)
	var cb := UI.icon_button("close", "Alle zuklappen")
	cb.pressed.connect(func(): _fold_all("close"))
	tb.add_child(cb)
	search_none = UI.small("Kein Treffer")
	search_none.visible = false
	box_.add_child(search_none)
	# connection to Motion Watch
	var cn := UI.card(box_)
	top_cards.append(cn.get_parent())
	var cnh := HBoxContainer.new()
	cnh.add_theme_constant_override("separation", 8)
	cnh.add_child(UI.group_icon("link"))
	var cnl := UI.heading("Verbindung")
	cnl.add_theme_font_size_override("font_size", 12)
	cnl.add_theme_color_override("font_color", UI.TXT)
	cnh.add_child(cnl)
	cn.add_child(cnh)
	stream_cb = CheckButton.new()
	stream_cb.text = "An Motion Watch senden (Port %d)" % stream_port
	stream_cb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stream_cb.add_theme_font_size_override("font_size", 15)
	stream_cb.button_pressed = stream_on
	stream_cb.toggled.connect(func(on): set_stream(on))
	cn.add_child(stream_cb)
	stream_note = UI.small("")
	cn.add_child(stream_note)
	status_label = UI.small("", UI.TXT)
	status_label.add_theme_font_size_override("font_size", 13)
	cn.add_child(status_label)
	# camera pictures
	var cm := UI.fold_card(top_box, "Kameras", true, "camera")   # always visible (also while searching); can be folded
	fold_bodies.append(cm)
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
	# tools: Motion Watch on this PC, map, phone
	var tl := UI.fold_card(box_, "Werkzeuge", true, "tools")
	fold_bodies.append(tl)
	top_cards.append(tl.get_meta("card"))
	mwpc_btn = Button.new()
	mwpc_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mwpc_btn.pressed.connect(func(): mwpc.toggle())
	UI.primary(mwpc_btn)
	tl.add_child(mwpc_btn)
	mwpc_label = UI.small("")
	tl.add_child(mwpc_label)
	var kb := Button.new()
	kb.text = "Karte: echten Ort in der Schweiz wählen (K)"
	kb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kb.pressed.connect(open_map)
	tl.add_child(kb)
	var pv := Button.new()
	pv.text = "Handy- / Tablet-Simulator (P)"
	pv.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pv.pressed.connect(_toggle_phone)
	tl.add_child(pv)
	# the settings of the simulator: one card per group (with a symbol), parts inside (the same list the page of Motion
	# Watch shows, in the same order - GROUPS / PLACE)
	var groups := {}
	var subs := {}
	for c in controls:
		if not groups.has(c.group):
			var ic := ""
			for g in GROUPS:
				if g[0] == c.group:
					ic = g[1]
			groups[c.group] = UI.fold_card(box_, c.group, c.group in ["Szene", "Besuch"], ic)
			fold_bodies.append(groups[c.group])
			setting_bodies.append(groups[c.group])
			if c.group == "Besuch":                       # first part: the pictures of the visitors
				var vs := UI.sub_fold(groups[c.group], "Besucher hinsetzen", true)
				vs.set_meta("always", true)
				sub_bodies.append(vs)
				subs["Besuch/Besucher hinsetzen"] = vs
				vs.add_child(UI.small("Bild in die Welt ziehen – oder anklicken und dann in die Welt klicken."))
				var grid := GridContainer.new()
				grid.columns = 4
				grid.add_theme_constant_override("h_separation", 6)
				grid.add_theme_constant_override("v_separation", 6)
				vs.add_child(grid)
				for k in VISITOR_LIST:
					grid.add_child(_palette_item(k[0], k[1]))
		var card_body: VBoxContainer = groups[c.group]
		var target: VBoxContainer = card_body
		var sub := str(c.extra.get("sub", ""))
		if sub != "":
			var key: String = c.group + "/" + sub
			if not subs.has(key):
				subs[key] = UI.sub_fold(card_body, sub, sub in ["Besucher schicken", "Runde"])
				sub_bodies.append(subs[key])
			target = subs[key]
		var n0 := ui_items.size()
		_ui_control(target, c)
		for i in range(n0, ui_items.size()):
			ui_items[i][3] = card_body
			ui_items[i].append(target)
	update_btn = Button.new()
	update_btn.text = "Nach Updates suchen (jetzt %s)" % VERSION
	update_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	update_btn.pressed.connect(check_updates)
	(subs.get("System/Updates", tl) as Control).add_child(update_btn)
	if groups.has("Testlauf"):
		testrun.add_info(groups["Testlauf"], UI)      # progress and result of the test run
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
	# Simple | Expert at the very bottom (like on the page of Motion Watch)
	var se := UI.segment("Einfach", "Experte", not ui_simple, func(expert): set_simple(not expert))
	box_.add_child(se)
	simple_note = UI.small("Einfach: nur die wichtigen Einstellungen. «Experte» zeigt alle.")
	box_.add_child(simple_note)
	_apply_simple()
	_sync_ui()
	_make_thumbs()


# ---- toolbar, search, Simple / Expert --------------------------------------------------------------------------------
var show_btn: Button
var search_in: LineEdit
var search_none: Label
var simple_note: Label
var ui_simple := true                 # «Einfach»: only the important settings (saved)
var fold_bodies: Array = []           # every card that opens / closes
var setting_bodies: Array = []        # the cards of the settings groups
var top_cards: Array = []             # connection, cameras, visitors, tools (hidden while searching)
var expert_cards: Array = []
var ui_items: Array = []              # [widget, label, expert, card body, part body] of every setting
var sub_bodies: Array = []            # the parts inside the cards (3D-3.5)


func show_panel(on: bool) -> void:
	ui_root.visible = on
	show_btn.visible = not on


func _fold_all(how: String) -> void:
	for b in fold_bodies:
		var open: bool = how == "open" or (how == "groups" and not b in setting_bodies and b.get_meta("title") == "Kameras")
		UI.set_open(b, open)
	if how != "groups":
		for sb in sub_bodies:
			UI.set_sub_open(sb, how == "open")


func _search(q: String) -> void:
	"""type into the search field: only the matching settings stay, their cards open; empty = everything as before"""
	q = q.strip_edges().to_lower()
	var any := false
	for c in top_cards:
		c.visible = q == "" and not (c in expert_cards and ui_simple)
	var hit_bodies := {}
	for it in ui_items:
		var show_it: bool = (q == "" or str(it[1]).to_lower().contains(q)) and not (ui_simple and it[2] and q == "")
		it[0].visible = show_it
		if q != "" and show_it:
			hit_bodies[it[3]] = true
			any = true
			if it.size() > 4 and it[4] != it[3]:
				UI.set_sub_open(it[4], true)
	for b in setting_bodies:
		b.get_meta("card").visible = q == "" or hit_bodies.has(b)
		if q != "":
			UI.set_open(b, hit_bodies.has(b))
	search_none.visible = q != "" and not any
	if q == "":
		_apply_simple()


func set_simple(on: bool) -> void:
	ui_simple = on
	_settings_dirty = true
	_apply_simple()


func _apply_simple() -> void:
	"""Simple: settings marked "expert" are hidden (and cards that would be empty)"""
	var counts := {}
	for it in ui_items:
		var vis: bool = not (ui_simple and it[2])
		it[0].visible = vis
		if vis:
			counts[it[3]] = true
	for b in setting_bodies:
		b.get_meta("card").visible = counts.has(b)
	var sub_counts := {}
	for it in ui_items:
		if it.size() > 4 and it[0].visible:
			sub_counts[it[4]] = true
	for sb in sub_bodies:
		sb.get_meta("wrap").visible = sub_counts.has(sb) or sb.has_meta("always")
	for c in expert_cards:
		c.visible = not ui_simple
	if simple_note != null:
		simple_note.visible = ui_simple


# ---- the pictures of the visitors: click to choose, drag into the world ------------------------------------------------
var thumbs := {}                      # kind -> ImageTexture
var thumb_rects := {}
var palette_items := {}
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
	"""a little picture of every visitor: drawn once at the start in a small world of its own"""
	var vp := SubViewport.new()
	vp.size = Vector2i(128, 116)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_2X
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
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
	var sizes := {"person": 1.9, "child": 1.3, "jogger": 1.9, "deer": 1.7, "boar": 1.1, "fox": 0.8, "dog": 0.9, "cat": 0.6, "badger": 0.6, "hare": 0.65, "hedgehog": 0.32}
	for k in VISITOR_LIST:
		var a = Actor.new()
		a.preview = true
		vp.add_child(a)
		a.setup(self, k[0], Vector3.ZERO, Vector3(-0.8, 0, 1.0), 0.0)
		var h: float = sizes.get(k[0], 1.0)
		var wide: bool = k[0] in ["fox", "deer", "boar", "dog", "cat", "badger", "hare", "hedgehog"]
		cam.position = Vector3(h * 1.1, h * 0.62, h * 1.75) * (1.15 if wide else 0.78)
		cam.look_at(Vector3(0, h * 0.48, 0), Vector3.UP)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		if img != null and not img.is_empty():
			var t := ImageTexture.create_from_image(img)
			thumbs[k[0]] = t
			if thumb_rects.has(k[0]):
				thumb_rects[k[0]].texture = t
		a.queue_free()
		await get_tree().process_frame
	vp.queue_free()


func _on_mwpc() -> void:
	"""Motion Watch on this PC changed: button, text, and the phone shows its page as soon as it runs"""
	var st: String = mwpc.state
	mwpc_btn.text = "Motion Watch auf diesem PC stoppen" if st == "running" else ("Motion Watch auf diesem PC wird vorbereitet …" if st == "busy" else "Motion Watch auf diesem PC starten (ohne Pi)")
	mwpc_btn.disabled = st == "busy"
	mwpc_label.text = mwpc.text if st != "off" else "Für das Handy ohne Pi: Motion Watch läuft dann unsichtbar auf diesem PC. Beim ersten Mal werden Python und Motion Watch geladen (rund 100 MB, einige Minuten)."
	mwpc_label.add_theme_color_override("font_color", UI.GRN if st == "running" else (UI.ORG if st == "error" else UI.MUT))
	phone.on_mwpc(st, mwpc.url(), mwpc.text)


func check_updates() -> void:
	"""button «Nach Updates suchen» in the window: asks before installing and also says when there is nothing new"""
	run_update(false, true)


func run_update(automatic: bool, by_hand: bool) -> void:
	"""check GitHub for a newer simulator. automatic: install by itself after 15 s (can be cancelled) - for the setting
	«Neue Versionen automatisch installieren» and for the button on the web page of Motion Watch (from far away)."""
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


func restart_args() -> PackedStringArray:
	"""options for the start after an update: as before, plus what is on now (sending, scene, Motion Watch on this PC)"""
	var a := OS.get_cmdline_user_args()
	var out := PackedStringArray()
	var skip := false
	for x in a:
		if skip:
			skip = false
			continue
		if x in ["--stream", "--updated", "--mwpc"]:
			continue
		if x == "--scene":
			skip = true
			continue
		out.append(x)
	if stream_on:
		out.append("--stream")
	out.append("--scene")
	out.append(scene)
	if mwpc != null and mwpc.state == "running":
		out.append("--mwpc")
	return out


const KEEP := ["game_rescue", "game_teamgoal", "game_teams", "world_cloth", "world_smoke", "world_fireflies", "lamp_share", "cloud_shadows", "gusts", "look_at_light", "game_goal", "sound_on", "night_gain", "ir_range", "game_mode", "game_lives", "game_items", "game_cones", "game_noise", "game_stones", "game_random", "lens_noise", "lens_vignette", "lens_drops", "insects_on", "game_minutes", "game_level", "game_quality", "game_guard", "eco_idle", "autostart_min", "autostart_mwpc", "autostart_lock", "last_scene", "auto_update", "ui_simple", "auto_visitors", "mix", "visit_rate", "max_visitors", "visitor_speed", "flee_light", "flee_sound",
		"avoid_on", "quality", "meadow_on", "season", "mover_on", "mover_max", "map_on", "map_size", "map_span", "ort_lat", "ort_lon", "ort_name", "weather", "wind", "ambient", "moon", "cam1_yaw"]
var _settings_dirty := false


func _load_settings() -> void:
	"""the settings of the last time (simulator_settings.json in the user folder)"""
	if not FileAccess.file_exists(SETTINGS_FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(SETTINGS_FILE))
	if typeof(d) != TYPE_DICTIONARY:
		return
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


func _save_settings() -> void:
	var d := {}
	for k in KEEP:
		d[k] = get(k)
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


func _open_preview() -> void:
	"""the web page of Motion Watch as it looks on a phone / tablet, upright and across (page /preview of Motion Watch)"""
	if mw_addr == "" or now() - mw_t > 10.0:
		status_label.text = "Motion Watch ist nicht verbunden – zuerst in Motion Watch die Simulation einschalten."
		return
	OS.shell_open("%s://%s:%d/preview" % [str(mw.get("mw_scheme", "http")), mw_addr, int(mw.get("mw_port", 5000))])


func _ui_control(parent: Control, c: Dictionary) -> void:
	match c.type:
		"button":
			var b := Button.new()
			b.text = c.label
			b.pressed.connect(func(): c["set"].call())
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var flow: HFlowContainer = null                # buttons side by side, wrapping (like the tiles on the page)
			if parent.get_child_count() > 0 and parent.get_child(parent.get_child_count() - 1) is HFlowContainer:
				flow = parent.get_child(parent.get_child_count() - 1)
			else:
				flow = HFlowContainer.new()
				flow.add_theme_constant_override("h_separation", 6)
				flow.add_theme_constant_override("v_separation", 6)
				parent.add_child(flow)
			b.custom_minimum_size = Vector2(150 if c.label.length() < 22 else 300, 0)
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART   # long texts on two lines (never wider than the panel)
			b.tooltip_text = c.label
			flow.add_child(b)
			ui_items.append([b, c.label, c.extra.get("expert", false), parent])
		"toggle":
			var row := HBoxContainer.new()                   # text (wraps) + switch on the right, like on the page of Motion Watch
			var tl := Label.new()
			tl.text = c.label
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
			l.text = c.label
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
			tl2.text = c.label
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
			l2.text = c.label
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
			parent.add_child(vb)
			ui_rows[c.id] = hs
			ui_items.append([vb, c.label, c.extra.get("expert", false), parent])


var _syncing := false


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
	_syncing = false


func _update_status() -> void:
	if status_label != null:
		status_label.text = status_text()
	if stream_note != null:
		if stream_on:
			stream_note.text = "Sendet: Motion Watch findet den Simulator im Netz und bekommt die Bilder."
			stream_note.add_theme_color_override("font_color", UI.GRN)
		elif net != null and net.error_text != "":
			stream_note.text = "⚠ " + net.error_text
			stream_note.add_theme_color_override("font_color", UI.ORG)
		else:
			stream_note.text = "Senden aus – zum Ausprobieren. Motion Watch sieht den Simulator erst, wenn der Schalter eingeschaltet ist."
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
var minimap                           # minimap.gd: overview map in the corner (from 3D-3.12)
var map_on := true
var map_size := 220.0
var map_span := 80.0
var map_btn: Button


func _unhandled_input(ev: InputEvent) -> void:
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
			KEY_F:
				if selected != null:
					follow = not follow
					_paint_sel()
			KEY_ESCAPE:
				place_kind = ""
				_paint_palette()
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
	for k in [["head", "Zum Kopf", "Zurück zu Motion Watch"], ["top", "Von oben", "Von oben auf den Platz schauen"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.focus_mode = Control.FOCUS_NONE
		var w: String = k[0]
		b.pressed.connect(func(): _view_preset(w))
		view_bar.add_child(b)
	set_view(view_mode)
	var help := UI.small("Links ziehen: verschieben · Rechts ziehen: drehen · Rad: zoomen · Doppelklick: hinfliegen")
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
		var c := Vector2(27, 27)
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
	if place_kind != "":
		_place_at(place_kind, p)


func _place_at(k: String, p: Vector2) -> void:
	"""a visitor where the mouse points (on the ground, never inside an object); it then walks off in some direction"""
	var from := view_cam.project_ray_origin(p)
	var d := view_cam.project_ray_normal(p)
	var hit = ground_hit(from, d)
	if hit == null or from.distance_to(hit) > 400.0:
		return
	var a: Vector3 = free_spot(hit, 0.5, k in ["person", "child", "jogger"])
	var ang := randf() * TAU
	var b := a + Vector3(cos(ang), 0, sin(ang)) * 40.0
	spawn(k, a, b)


# ---- wildlife watching: the rifle (bloodless - a hit animal hops, sees stars and runs away; people cannot be hit) ----------
var shot_msg := ""
var shot_msg_t := 0.0
const POINTS := {"fox": 10, "deer": 15, "boar": 20, "badger": 25, "cat": 5, "dog": 5}


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
	"""a shot straight out of the head camera: aim with the pan / tilt head of Motion Watch"""
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


func _animal_name(k: String) -> String:
	return {"fox": "Fuchs", "deer": "Reh", "boar": "Wildschwein", "badger": "Dachs", "cat": "Katze", "dog": "Hund"}.get(k, k)


func _say(text: String, p: Vector3, col: Color) -> void:
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
	l.layers = 1
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


func clear_obstacles() -> void:
	obstacles.clear()
	ob_grid.clear()


func add_obstacle(p: Vector3, r: float, people_only := false) -> void:
	var o := {"c": Vector2(p.x, p.z), "r": r, "po": people_only, "id": obstacles.size()}
	obstacles.append(o)
	_ob_insert(o, Vector2(p.x - r, p.z - r), Vector2(p.x + r, p.z + r))


func add_obstacle_box(p: Vector3, sx: float, sz: float, rot_y: float, people_only := false) -> void:
	"""a box of sx × sz metres around p, turned like a node with rotation.y = rot_y"""
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
	return {}


func set_obstacle_height(ht: float) -> void:
	"""the height of the object added last (for the line of sight of the game)"""
	if not obstacles.is_empty():
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
