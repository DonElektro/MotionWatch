extends Node3D
## Motion Watch 3D simulator - scenes: camping place, forest, car park, garden, funny place, wildlife watching (scenes.gd)
## The world, the cameras for Motion Watch (head camera on the pan / tilt head, fixed camera, thermal camera),
## day and night, weather, lights, visitors, sensors, the window on the PC and the connection (net.gd).

const VERSION := "3D-1.8"
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
var place_kind := "fox"
var place_menu: OptionButton

var obj := {"door": Vector3.ZERO, "pir": Vector3.ZERO, "bike": Vector3.ZERO}   # set by the scene


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
	DisplayServer.window_set_title("Motion Watch – 3D-Simulator %s" % VERSION)
	if not ("--no-update" in args or "--updated" in args):      # first: is there a newer version? (update.gd)
		var url := ""
		var k := args.find("--update-url")
		if k >= 0 and k + 1 < args.size():
			url = args[k + 1]
		var up = Updater.new()
		add_child(up)
		await up.check(VERSION, url)
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
	_build_world()
	_build_head()
	_build_viewports()
	_build_weather()
	visitors = Node3D.new()
	add_child(visitors)
	_build_view_camera()
	stream_port = port
	_register_controls()
	_build_ui()
	net = Net.new()
	net.main = self
	add_child(net)
	if "--stream" in args:                    # start sending at once (old behaviour)
		set_stream(true)
	_apply_quality()
	_calibrate_thermal()
	next_auto = now() + 20.0
	for i in range(args.size()):
		if args[i] == "--phone":                  # start with the phone open (optionally: --phone http://address:5000)
			if i + 1 < args.size() and args[i + 1].begins_with("http"):
				phone.addr.text = args[i + 1]
			get_tree().create_timer(2.0).timeout.connect(func(): phone.open())
	DisplayServer.window_set_title("Motion Watch – 3D-Simulator %s (Port %d)" % [VERSION, port])
	set_process(true)
	set_process_unhandled_input(true)


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
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
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
	var gt := MeshInstance3D.new()
	gt.mesh = plane
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/ground_thermal.gdshader")
	tmats["ground"] = gm
	gt.material_override = gm
	gt.layers = 2
	world.add_child(gt)
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
		add_mesh(world, hill, pos_of(i * 360.0 / 14 + rng.randf_range(-8, 8), rng.randf_range(420, 520), -hill.radius * 0.15),
				mat(Color(0.25, 0.33, 0.25)), "hill")
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
	lamps.clear()
	lamp_mats.clear()
	anims.clear()
	door_open = false
	scenes.build(scene, scene_parent)
	if scene == "wild":
		rifle_on = true                          # wildlife watching: the rifle is on by itself


func set_scene(id: String) -> bool:
	var ok := false
	for s in Scenes.LIST:
		if s[0] == id:
			ok = true
	if not ok:
		return false
	scene = id
	for v in visitors.get_children():
		v.queue_free()
	for c in scene_parent.get_children():
		c.queue_free()
	_build_scene()
	next_auto = now() + 8.0
	_update_sky()
	_update_temps()
	_sync_ui()
	return true


func _build_head() -> void:
	head = Node3D.new()
	head.position = Vector3(0, HEAD_H, 0)
	add_child(head)
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


func sun_el() -> float:
	var h := hour()
	if h >= 6.5 and h <= 19.5:
		return 50.0 * sin((h - 6.5) / 13.0 * PI)
	var x := h - 19.5 if h > 19.5 else h + 4.5
	return -20.0 * sin(x / 11.0 * PI)


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
	var az := -60.0 + (hour() - 13.0) * 15.0
	sun.rotation = Vector3(deg_to_rad(-max(el, -10.0)), deg_to_rad(180.0 - az), 0)
	sun.light_energy = max(0.0, sin(deg_to_rad(max(el, 0.0)))) * 1.6 * (1.0 - 0.6 * cl) + (0.02 if el > -4 else 0.0)
	sun.visible = el > -4.0
	var dusk: float = max(0.0, 1.0 - abs(el - 2.0) / 10.0) if el > -8.0 else 0.0
	sun.light_color = Color(1.0, 0.95, 0.88).lerp(Color(1.0, 0.6, 0.35), dusk)
	moonlight.light_energy = 0.035 * moon * (1.0 - cl) * (1.0 - day)
	var top := Color(0.25, 0.45, 0.8).lerp(Color(0.55, 0.57, 0.6), cl)
	var hor := Color(0.7, 0.78, 0.88).lerp(Color(0.95, 0.65, 0.45), dusk).lerp(Color(0.7, 0.71, 0.72), cl * 0.8)
	var k: float = max(0.02, day)
	sky_mat.sky_top_color = top * k + Color(0.01, 0.015, 0.03) * (1.0 - k)
	sky_mat.sky_horizon_color = hor * k + Color(0.02, 0.025, 0.04) * (1.0 - k)
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = Color(0.1, 0.12, 0.08) * k
	sky_mat.sky_energy_multiplier = 0.06 + 0.94 * day
	env.ambient_light_energy = 0.025 + 0.95 * day
	var dens: float = {"clear": 0.0007, "cloudy": 0.0012, "rain": 0.006, "fog": 0.045, "snow": 0.012}.get(weather, 0.0008)
	env.fog_density = dens
	env.fog_light_color = Color(0.72, 0.74, 0.78) * (0.05 + 0.95 * day)
	rain.emitting = weather == "rain"
	snow.emitting = weather == "snow"
	grass_mat.set_shader_parameter("snow_amount", 0.85 if weather == "snow" else 0.0)
	grass_mat.set_shader_parameter("wet", 1.0 if weather == "rain" else 0.0)
	for fm in foliage_mats:
		fm.set_shader_parameter("wind", wind)
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
	var sunk: float = max(0.0, el) / 50.0
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
	var s: Dictionary = mw.get("servo", {})
	head.rotation.y = -deg_to_rad(float(s.get("pan_deg", 0.0)))
	head_pitch.rotation.x = deg_to_rad(float(s.get("tilt_deg", 0.0)) - 6.0)
	cams[0].global_transform = head_pitch.global_transform.translated_local(Vector3(0, 0.0, -0.13))
	cams[2].global_transform = head_pitch.global_transform.translated_local(Vector3(0.12, 0.0, -0.12))
	var c1 := Transform3D(Basis.from_euler(Vector3(deg_to_rad(-10.0), -deg_to_rad(cam1_yaw), 0)), Vector3(-3.0, 2.4, 3.0))
	cams[1].global_transform = c1
	var L: Dictionary = mw.get("lights", {})
	white_light.light_energy = 9.0 if L.get("white", false) else 0.0
	rain.position = Vector3(0, 12, -8)
	_slow_t -= dt
	if _slow_t <= 0.0:
		_slow_t = 0.5
		_update_sky()
		_update_temps()
		_life()
		_update_status()
	var t := now() - clock0
	for a in anims:
		a.call(dt, t)
	_fly(dt)
	if crosshair != null:
		crosshair.visible = rifle_on
		if rifle_on:
			crosshair.queue_redraw()
	if not capturing:
		_capture_next()


# ---- pictures for Motion Watch -------------------------------------------------------------------------------------
func _wanted_fps(i: int) -> float:
	var d: Dictionary = net.stream_demand() if net != null else {}
	var f: float = float(d.get(i, 0.0))
	if i < 2 and now() - snap_want[i] < 3.0:
		f = max(f, 2.0)
	if i == 2 and now() - _th_asked < 3.0:
		f = max(f, 8.0)
	if preview_on:
		f = max(f, 4.0 if i < 2 else 3.0)
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
	ir_light.light_energy = 6.0 if (i == 0 and L.get("ir", false)) else 0.0   # infrared: only the NoIR camera sees it
	if i == 0:
		var grey: bool = L.get("ir", false) and dark and not L.get("white", false)
		if grey:
			var e: Environment = env.duplicate()
			e.adjustment_enabled = true
			e.adjustment_saturation = 0.0
			cams[0].environment = e
		else:
			cams[0].environment = null
	if i < 2:
		cam_attr[i].exposure_multiplier = gain[i]
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


func _auto_exposure(i: int, img: Image) -> void:
	var small: Image = img.duplicate()
	small.resize(32, 18, Image.INTERPOLATE_BILINEAR)
	var sum := 0.0
	for y in range(6, 18):
		for x in range(32):
			var c := small.get_pixel(x, y)
			sum += (c.r + c.g + c.b) / 3.0
	var mean: float = max(0.01, sum / (12.0 * 32.0))
	var want: float = clamp(gain[i] * 0.35 / mean, 0.6, 6.0)
	gain[i] += (want - gain[i]) * 0.25


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
	mw_addr = host
	if str(d.get("sound", "")) != "" and old_sound == "":
		_scare_all(true)


func world_reply() -> Dictionary:
	var press := pressure
	if storm_t > 0.0:
		press -= min(6.0, (now() - storm_t) / 180.0 * 6.0)
	var t := Time.get_datetime_dict_from_system()
	var midnight: float = now() - (t.hour * 3600 + t.minute * 60 + t.second)
	return {"v": 1, "ok": true, "sim_time": midnight + hour() * 3600.0, "dark": is_dark(), "ambient_c": snappedf(ambient, 0.1),
			"pressure_hpa": snappedf(press, 0.1), "wind_kmh": snappedf(wind, 0.1), "last_event": next_event_id - 1,
			"weather": weather, "humidity": humidity}


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
	return 1.0


func spawn(kind: String, from = null, to = null) -> Node3D:
	var depth := randf_range(6.0, 22.0)
	var side := 1.0 if randf() < 0.5 else -1.0
	var a: Vector3 = from if from != null else Vector3(-side * (depth * 1.6 + 6.0), 0, -depth)
	var b: Vector3 = to if to != null else Vector3(side * (depth * 1.6 + 6.0), 0, -depth)
	var spd: float = {"person": 1.3, "fox": 2.0, "boar": 1.5, "deer": 1.6, "cat": 1.1, "dog": 1.8, "badger": 0.9, "car": 11.0}.get(kind, 1.3)
	var v = Actor.new()
	visitors.add_child(v)
	v.setup(self, kind, a, b, spd * randf_range(0.85, 1.15))
	v.set_night(is_dark())
	return v


func car() -> void:
	var side := 1.0 if randf() < 0.5 else -1.0
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
		var k: String = au[0][randi() % au[0].size()]
		visit(k)
		next_auto = t + randf_range(au[1], au[2])
	var L: Dictionary = mw.get("lights", {})
	if L.get("white", false) and is_dark():
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
	controls.append({"type": type, "id": id, "label": label, "group": group, "get": getter, "set": setter, "extra": extra})


func _register_controls() -> void:
	var sc := []
	for s in Scenes.LIST:
		sc.append([s[0], s[1]])
	add_control("select", "scene", "Szene", func(): return scene, func(v): set_scene(v), "Szene", {"options": sc})
	add_control("slider", "hour", "Uhrzeit", func(): return snappedf(hour(), 0.01), func(v): set_hour(v), "Szene", {"min": 0, "max": 23.75, "step": 0.25, "unit": "h"})
	add_control("slider", "speed", "Zeit läuft x-fach", func(): return speed, func(v): _set_speed(v), "Szene", {"min": 1, "max": 120, "step": 1, "unit": "×"})
	add_control("slider", "moon", "Mond", func(): return moon, func(v): moon = v, "Szene", {"min": 0, "max": 1, "step": 0.1})
	add_control("slider", "cam1_yaw", "Kamera 1: Richtung", func(): return cam1_yaw, func(v): cam1_yaw = v, "Szene", {"min": -90, "max": 90, "step": 1, "unit": "°"})
	add_control("select", "weather", "Wetter", func(): return weather, func(v): weather = v, "Wetter",
			{"options": [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]]})
	add_control("slider", "wind", "Wind", func(): return wind, func(v): wind = v, "Wetter", {"min": 0, "max": 120, "step": 1, "unit": "km/h"})
	add_control("slider", "ambient", "Temperatur", func(): return ambient, func(v): ambient = v, "Wetter", {"min": -15, "max": 40, "step": 0.5, "unit": "°C"})
	add_control("slider", "pressure", "Luftdruck", func(): return pressure, func(v): pressure = v, "Wetter", {"min": 960, "max": 1040, "step": 0.5, "unit": "hPa"})
	add_control("button", "storm", "Sturm zieht auf", null, func(): storm_t = now(), "Wetter")
	for k in [["person", "Person"], ["fox", "Fuchs"], ["boar", "Wildschwein"], ["deer", "Reh"], ["cat", "Katze"], ["badger", "Dachs"], ["dog", "Hund"]]:
		add_control("button", "spawn_" + k[0], k[1], null, func(): spawn(k[0]), "Besuch")
	add_control("button", "car", "Auto", null, func(): car(), "Besuch")
	add_control("button", "thief", "Dieb (Velo, Tür)", null, func(): thief(), "Besuch")
	add_control("button", "car_park", "Auto parkiert (Parkplatz)", null, func(): visit("car_park"), "Besuch")
	add_control("button", "bench", "Besuch setzt sich auf die Bank (Lustiger Platz)", null, func(): visit("bench"), "Besuch")
	add_control("button", "feed", "Reh kommt zur Futterstelle (Wildbeobachtung)", null, func(): visit("feed_deer"), "Besuch")
	add_control("toggle", "auto", "ab und zu Besuch von selbst", func(): return auto_visitors, func(v): auto_visitors = v, "Besuch")
	add_control("toggle", "door", "Wohnwagentür offen", func(): return door_open, func(v): set_door(v), "Sensoren")
	add_control("toggle", "gas", "Gas / Rauch", func(): return gas_on, func(v): set_gas(v), "Sensoren")
	add_control("button", "pir", "PIR Zelt auslösen", null, func(): add_event("PIR Zelt", "pir"), "Sensoren")
	add_control("button", "bike", "Velo bewegen", null, func(): add_event("Velo", "tag"), "Sensoren")
	add_control("button", "nighttest", "Nacht-Test starten (2 Min.)", null, func(): night_test(), "Sensoren")
	add_control("toggle", "rifle", "Gewehr (unblutig, nur Tiere)", func(): return rifle_on, func(v): rifle_on = v, "Wildbeobachtung")
	add_control("button", "shoot_head", "Schuss aus der Kopfkamera", null, func(): shoot_head(), "Wildbeobachtung")
	add_control("button", "score0", "Punkte auf 0", null, func(): reset_score(), "Wildbeobachtung")
	add_control("select", "quality", "Grafik", func(): return quality, func(v): _set_quality(v), "Grafik",
			{"options": [["simple", "einfach (schnell)"], ["nice", "schön (Schatten, Leuchten)"]]})


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
	return "%s · %02d:%02d · %s · %s · %.1f °C · Besucher %d%s · %s" % [Scenes.name_of(scene), int(h), int(fmod(h, 1.0) * 60), "Nacht" if is_dark() else "Tag", {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(weather, weather), ambient, visitors.get_child_count(), score, mwc]


func scenarios() -> Array:
	var out := []
	for s in Scenes.LIST:
		out.append({"id": s[0], "name": s[1] + " (3D)", "kind": "world", "deletable": false})
	return out


# ---- the window on the PC ------------------------------------------------------------------------------------------------
var ui_root: Control
var prev0: TextureRect
var prev1: TextureRect
var prevt: TextureRect
var info_label: Label


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	phone = Phone.new()
	phone.main = self
	phone.position = Vector2(0, 0)
	layer.add_child(phone)
	_build_crosshair(layer)
	var panel := PanelContainer.new()
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -390
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.09, 0.11, 0.14, 0.94)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 8
	panel.add_theme_stylebox_override("panel", sb)
	layer.add_child(panel)
	ui_root = panel
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var box_ := VBoxContainer.new()
	box_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box_.add_theme_constant_override("separation", 6)
	scroll.add_child(box_)
	var title := Label.new()
	title.text = "Motion Watch – 3D-Simulator"
	title.add_theme_font_size_override("font_size", 18)
	box_.add_child(title)
	stream_cb = CheckButton.new()
	stream_cb.text = "An Motion Watch senden (Port %d)" % stream_port
	stream_cb.add_theme_font_size_override("font_size", 16)
	stream_cb.button_pressed = stream_on
	stream_cb.toggled.connect(func(on): set_stream(on))
	box_.add_child(stream_cb)
	stream_note = Label.new()
	stream_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stream_note.add_theme_font_size_override("font_size", 12)
	box_.add_child(stream_note)
	status_label = Label.new()
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status_label.add_theme_color_override("font_color", Color(0.7, 0.75, 0.8))
	box_.add_child(status_label)
	prev0 = TextureRect.new()
	prev0.texture = vps[0].get_texture()
	prev0.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev0.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prev0.custom_minimum_size = Vector2(360, 203)
	box_.add_child(prev0)
	var row := HBoxContainer.new()
	box_.add_child(row)
	prev1 = TextureRect.new()
	prev1.texture = vps[1].get_texture()
	prev1.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev1.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prev1.custom_minimum_size = Vector2(176, 99)
	row.add_child(prev1)
	prevt = TextureRect.new()
	prevt.texture = th_preview
	prevt.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prevt.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	prevt.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	prevt.custom_minimum_size = Vector2(176, 136)
	row.add_child(prevt)
	var lbl := Label.new()
	lbl.text = "Linksklick in die Welt setzt hin:"
	box_.add_child(lbl)
	place_menu = OptionButton.new()
	for k in [["", "nichts"], ["person", "Person"], ["fox", "Fuchs"], ["boar", "Wildschwein"], ["deer", "Reh"], ["cat", "Katze"], ["badger", "Dachs"], ["dog", "Hund"]]:
		place_menu.add_item(k[1])
		place_menu.set_item_metadata(place_menu.item_count - 1, k[0])
	place_menu.select(2)
	box_.add_child(place_menu)
	var pv := Button.new()
	pv.text = "Handy- / Tablet-Simulator (P)"
	pv.pressed.connect(_toggle_phone)
	box_.add_child(pv)
	var groups := {}
	for c in controls:
		if not groups.has(c.group):
			var head_btn := Button.new()
			head_btn.text = "▸ " + c.group
			head_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
			head_btn.flat = true
			box_.add_child(head_btn)
			var gb := VBoxContainer.new()
			gb.visible = c.group in ["Szene", "Besuch"]
			head_btn.text = ("▾ " if gb.visible else "▸ ") + c.group
			box_.add_child(gb)
			head_btn.pressed.connect(func():
				gb.visible = not gb.visible
				head_btn.text = ("▾ " if gb.visible else "▸ ") + c.group)
			groups[c.group] = gb
		_ui_control(groups[c.group], c)
	info_label = Label.new()
	info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info_label.add_theme_color_override("font_color", Color(0.55, 0.6, 0.65))
	info_label.text = "Maus rechts gedrückt halten: umschauen · W A S D Q E: fliegen · Shift: schneller · 1: durch Kamera 0 schauen · 2: Kamera 1 · 0: frei · H: Bedienung aus/ein · P: Handy / Tablet · G: Gewehr ein/aus (Linksklick = Schuss)"
	box_.add_child(info_label)
	_sync_ui()


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
			parent.add_child(b)
		"toggle":
			var cb := CheckBox.new()
			cb.text = c.label
			cb.toggled.connect(func(on): c["set"].call(on))
			parent.add_child(cb)
			ui_rows[c.id] = cb
		"select":
			var hb := HBoxContainer.new()
			var l := Label.new()
			l.text = c.label
			l.custom_minimum_size = Vector2(120, 0)
			hb.add_child(l)
			var ob := OptionButton.new()
			ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			for o in c.extra.options:
				ob.add_item(o[1])
				ob.set_item_metadata(ob.item_count - 1, o[0])
			ob.item_selected.connect(func(idx): c["set"].call(ob.get_item_metadata(idx)))
			hb.add_child(ob)
			parent.add_child(hb)
			ui_rows[c.id] = ob
		"slider":
			var vb := VBoxContainer.new()
			var hb2 := HBoxContainer.new()
			var l2 := Label.new()
			l2.text = c.label
			l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
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


var _syncing := false


func _sync_ui() -> void:
	_syncing = true
	for c in controls:
		if not ui_rows.has(c.id) or c["get"] == null:
			continue
		var w = ui_rows[c.id]
		var v = c["get"].call()
		if w is CheckBox:
			w.set_pressed_no_signal(bool(v))
		elif w is OptionButton:
			for i in range(w.item_count):
				if str(w.get_item_metadata(i)) == str(v):
					w.select(i)
		elif w is HSlider and not w.has_focus():
			w.value = float(v)
	_syncing = false


func _update_status() -> void:
	if status_label != null:
		status_label.text = status_text()
	if stream_note != null:
		if stream_on:
			stream_note.text = "Sendet: Motion Watch findet den Simulator im Netz und bekommt die Bilder."
			stream_note.add_theme_color_override("font_color", Color(0.35, 0.8, 0.45))
		elif net != null and net.error_text != "":
			stream_note.text = "⚠ " + net.error_text
			stream_note.add_theme_color_override("font_color", Color(0.95, 0.6, 0.3))
		else:
			stream_note.text = "Senden aus – zum Ausprobieren. Motion Watch sieht den Simulator erst, wenn der Schalter eingeschaltet ist."
			stream_note.add_theme_color_override("font_color", Color(0.6, 0.65, 0.7))
	if Engine.get_process_frames() % 4 == 0:
		_sync_ui()


# ---- flying through the world, placing visitors ---------------------------------------------------------------------------
var look := false
var yaw := 0.0
var pitch := 0.0
var fly_speed := 8.0
var view_mode := 0


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_RIGHT:
			look = ev.pressed
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if look else Input.MOUSE_MODE_VISIBLE
			if look:
				yaw = view_cam.rotation.y
				pitch = view_cam.rotation.x
		elif ev.button_index == MOUSE_BUTTON_LEFT and ev.pressed:
			if rifle_on:
				var sp: Vector2 = get_viewport().get_visible_rect().size / 2.0 if look else ev.position
				shoot(view_cam.project_ray_origin(sp), view_cam.project_ray_normal(sp))
			else:
				_place(ev.position)
		elif ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			fly_speed = min(80.0, fly_speed * 1.2)
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			fly_speed = max(1.0, fly_speed / 1.2)
	elif ev is InputEventMouseMotion and look:
		yaw -= ev.relative.x * 0.004
		pitch = clamp(pitch - ev.relative.y * 0.004, -1.5, 1.5)
		view_cam.rotation = Vector3(pitch, yaw, 0)
		view_mode = 0
	elif ev is InputEventKey and ev.pressed and not ev.echo:
		match ev.keycode:
			KEY_1:
				view_mode = 1
			KEY_2:
				view_mode = 2
			KEY_0:
				view_mode = 0
			KEY_H:
				ui_root.visible = not ui_root.visible
			KEY_P:
				_toggle_phone()
			KEY_G:
				rifle_on = not rifle_on
				_sync_ui()


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
		view_cam.position.y = max(0.3, view_cam.position.y)


func _place(p: Vector2) -> void:
	var k: String = str(place_menu.get_item_metadata(place_menu.selected))
	if k == "":
		return
	var from := view_cam.project_ray_origin(p)
	var d := view_cam.project_ray_normal(p)
	var hit = Plane(Vector3.UP, 0).intersects_ray(from, d)
	if hit == null:
		return
	var a: Vector3 = hit
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
