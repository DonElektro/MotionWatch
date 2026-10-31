extends Node
## 3D-4.4 «simreal»: the simulator closer to the real device (Pi 5 + Camera Module 3 NoIR + Thermal-90) - every part can
## be switched off (settings: «Kamerabild · Wie echt», «Kamerabild · Schwierige Bedingungen», «Besuch», card «Testlauf»).
##  Sensors
##   - «Wie ein echter Pi 5»: the head camera delivers only ~10 pictures per second (what a Pi 5 with the AI manages) and
##     every picture comes a little late (processing time) - tests and games behave like on the device
##   - the lens of the Camera Module 3: slight barrel distortion (the wide fixed camera more), rolling shutter when the head
##     turns fast, sensor noise that depends on the light (camfx.gdshader: distort, rshutter, shot)
##   - infrared like real: LED cone with soft edge and fall-off with the square of the distance, near things blow out and
##     glow (bloom), retro-reflectors (bike reflector, number plate, road sign) flare up in the light
##   - thermal like real: clothes insulate (the surface of a jacket is much cooler than the skin, face and hands stay warm),
##     stones, cars and asphalt keep the heat of the sun into the night, rain cools the surfaces, windows reflect the cold sky
##  Situations
##   - false alarms: a flapping tarp at the tent and a pennant, light of a turning car sweeping over walls, a cat on the
##     car roof, birds right in front of the lens
##   - difficult persons and animals as spawn kinds (main.spawn(kind) - also for the test bench), see KINDS
##   - animals: sniff and stop more often, a deer lies and stands up, raises its head (alert), a herd stops together,
##     the dog on a walk goes on a leash
## Settings in user://simreal.json (like realism.gd: echt_abgleich.json).

var main
const Waerme = preload("res://scripts/waerme.gd")   # 3D-4.26: the heat table (Paket P3)
const FILE := "user://simreal.json"
const SAVE := ["pi_on", "pi_fps", "pi_delay", "lens_on", "ir_real", "th_real", "fa_flags", "fa_sweep", "fa_catroof", "fa_birds",
		"anim_real", "leash_on", "hard_auto"]
var pi_on := false                 # «Wie ein echter Pi 5»
var pi_fps := 10.0                 # pictures per second of the head camera on the Pi (with the AI)
var pi_delay := 0.3                # seconds from the light to the picture at MoveEye (processing, Wi-Fi)
var lens_on := true                # distortion, rolling shutter, light-dependent noise
var ir_real := true                # LED cone, fall-off, blow-out, retro-reflectors
var th_real := true                # clothes, heat of the day, rain, windows
var fa_flags := true               # tarp and pennant flap in the wind
var fa_sweep := false              # at night the light of a turning car sweeps over the walls now and then
var fa_catroof := false            # at night now and then a cat on the car roof
var fa_birds := true               # by day now and then a bird right in front of the lens
var anim_real := true              # animals sniff, stop, lie, rise, look up; herds stop together
var leash_on := true               # the dog on a walk is on a leash
var hard_auto := false             # difficult persons also come by themselves now and then

# spawn kinds (main.spawn(kind, from, to) and the buttons in «Besuch»): kind -> [German name, part of «Besuch»]
const KINDS := {
	"hooded": ["Mit Kapuze / Regenumhang (Umriss ohne Kopf, kühl im Wärmebild)", "Menschen schicken"],
	"backpacker": ["Mit grossem Rucksack (anderer Umriss)", "Menschen schicken"],
	"phoner": ["Telefoniert und bleibt lange stehen (kaum Bewegung)", "Menschen schicken"],
	"group2": ["Zwei Personen dicht beieinander", "Menschen schicken"],
	"group3": ["Gruppe zu dritt", "Menschen schicken"],
	"group4": ["Gruppe zu viert", "Menschen schicken"],
	"edge_sneak": ["Schleicht langsam am Bildrand der Kopfkamera", "Abläufe"],
	"deer_bedded": ["Reh liegt im Gras, steht auf und hebt den Kopf", "Tiere schicken"],
	"dog_leash": ["Hund an der Leine mit seinem Menschen", "Menschen schicken"],
	"boar_herd": ["Wildschwein-Rotte (wühlt zusammen, bleibt zusammen stehen)", "Tiere schicken"],
	"cat_roof": ["Katze auf dem Autodach", "Tiere schicken"],
}
const HARD_AUTO := ["hooded", "backpacker", "phoner", "group2", "group3", "edge_sneak"]

var _jit := 1.0
var _jit_t := 0.0
var _buf: Array = [[], []]         # [[time, jpg], ...] per camera (the late pictures of the Pi)
var _refl: Array = []              # [MeshInstance3D, StandardMaterial3D] retro-reflectors
var _cars: Array = []              # parked cars of the scene (Node3D) - a cat can sit on the roof
var _track: Array = []             # [{v, do, ...}] visitors with a little extra behaviour
var _leash: Array = []             # [{dog, person, mesh}]
var _sweep = null                  # {light, t0, dur, a0, a1}
var _next_sweep := 0.0
var _next_cat := 0.0
var _birds: Array = []             # [{b (fauna bird dict), from, mid, to, t0, dur, hover}]
var _next_bird := 0.0
var _next_hard := 0.0
var _slow := 0.0
var _flap_mats: Array = []
var _sign_done := false
var test_rs := 0.0                 # for tests (control «simreal», do: test): a fixed rolling-shutter skew


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				var old = get(k)
				set(k, float(d[k]) if typeof(old) == TYPE_FLOAT else bool(d[k]))
	pi_fps = clampf(pi_fps, 4.0, 15.0)
	pi_delay = clampf(pi_delay, 0.0, 1.5)


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))
		f.close()


func _put(k: String, v) -> void:
	set(k, v)
	save()


func add_controls() -> void:
	"""the switches - called by main.gd where the other camera settings are made"""
	var m = main
	m.add_control("toggle", "pi_on", "Wie ein echter Pi 5: Kopfkamera nur so viele Bilder pro Sekunde wie der Pi mit der KI schafft, jedes Bild etwas verspätet (Testläufe und Spiele wie auf dem Gerät)",
			func(): return pi_on, func(v): _put("pi_on", bool(v)); _buf = [[], []], "Testlauf")
	m.add_control("slider", "pi_fps", "Pi 5: Bilder pro Sekunde der Kopfkamera", func(): return pi_fps, func(v): _put("pi_fps", float(v)), "Testlauf",
			{"min": 4, "max": 15, "step": 1, "unit": "/s", "expert": true})
	m.add_control("slider", "pi_delay", "Pi 5: Verzögerung bis das Bild bei MoveEye ist (Verarbeitung, WLAN)", func(): return pi_delay, func(v): _put("pi_delay", float(v)), "Testlauf",
			{"min": 0.0, "max": 1.5, "step": 0.05, "unit": "s", "expert": true})
	m.add_control("toggle", "real_lens", "Objektiv wie das Camera Module 3: leichte Tonnenverzerrung am Rand (Weitwinkel stärker), schräges Bild beim schnellen Drehen (Rolling Shutter), Rauschen je nach Licht",
			func(): return lens_on, func(v): _put("lens_on", bool(v)), "Kamerabild", {"sub": "Wie echt"})
	m.add_control("toggle", "real_ir", "Infrarot wie echt: Lichtkegel der LED mit weichem Rand, nimmt mit der Entfernung stark ab, Nahes überstrahlt, Rückstrahler (Velo, Nummernschild, Schild) leuchten auf",
			func(): return ir_real, func(v): _put("ir_real", bool(v)); _ir_setup(), "Kamerabild", {"sub": "Wie echt"})
	# 3D-4.26 (Paket P2/P3): der eine Schalter für das Wärmebild steht jetzt in «Kamerabild → Wärmebild» (vorher «Wie echt»)
	m.add_control("toggle", "real_thermal", "Wärmebild wie echt: Sensor wie der Thermal-90 (80 × 62, Rauschen, Drift, Unschärfe, Wasser auf dem Fenster, Nebel schluckt), Wärme wie echt (Kleider isolieren, Tiere mit Fell, Motor kühlt ab, Sonne heizt Asphalt, Autodach und Zelt, kalter Himmel, Glas ist undurchsichtig)",
			func(): return th_real, func(v): _put("th_real", bool(v)), "Kamerabild", {"sub": "Wärmebild"})
	m.add_control("toggle", "fa_flags", "Lose Zeltplane und Wimpel flattern im Wind (wirkt nach dem Szenenwechsel)", func(): return fa_flags, func(v): _put("fa_flags", bool(v)), "Kamerabild", {"sub": "Schwierige Bedingungen"})
	m.add_control("toggle", "fa_sweep", "Nachts streift ab und zu das Licht eines einbiegenden Autos über Wände und Zelt", func(): return fa_sweep, func(v): _put("fa_sweep", bool(v)), "Kamerabild", {"sub": "Schwierige Bedingungen"})
	m.add_control("toggle", "fa_catroof", "Nachts setzt sich ab und zu eine Katze aufs Autodach", func(): return fa_catroof, func(v): _put("fa_catroof", bool(v)), "Kamerabild", {"sub": "Schwierige Bedingungen"})
	m.add_control("toggle", "fa_birds", "Am Tag fliegt ab und zu ein Vogel direkt vor der Linse durch", func(): return fa_birds, func(v): _put("fa_birds", bool(v)), "Kamerabild", {"sub": "Schwierige Bedingungen"})
	m.add_control("button", "sweep_now", "Lichtkegel eines Autos jetzt (nachts)", null, func(): start_sweep(), "Kamerabild", {"sub": "Schwierige Bedingungen", "expert": true})
	m.add_control("button", "bird_now", "Vogel vor der Linse jetzt", null, func(): lens_bird(), "Kamerabild", {"sub": "Schwierige Bedingungen", "expert": true})
	for k in KINDS:
		var kk: String = k
		m.add_control("button", "spawn_" + kk, KINDS[kk][0], null, func(): main.spawn(kk), "Besuch", {"sub": KINDS[kk][1]})
	m.add_control("toggle", "hard_auto", "Schwierige Personen kommen auch von selbst (Kapuze, Rucksack, Gruppe, telefoniert, schleicht am Rand)", func(): return hard_auto, func(v): _put("hard_auto", bool(v)), "Besuch", {"sub": "Von selbst"})
	m.add_control("toggle", "anim_real", "Tiere wie echt: schnüffeln und halten öfter an, Reh liegt und steht auf, hebt den Kopf, Rotten und Rudel bleiben zusammen stehen", func(): return anim_real, func(v): _put("anim_real", bool(v)), "Besuch", {"sub": "Verhalten"})
	m.add_control("toggle", "leash_on", "Hund beim Spaziergang an der Leine", func(): return leash_on, func(v): _put("leash_on", bool(v)), "Besuch", {"sub": "Verhalten"})


func info() -> Dictionary:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	d["reflectors"] = _refl.size()
	d["cars"] = _cars.size()
	d["tracked"] = _track.size()
	d["leashes"] = _leash.size()
	d["sweep"] = _sweep != null
	d["birds"] = _birds.size()
	d["buffer"] = [_buf[0].size(), _buf[1].size()]
	d["fps_cap0"] = snappedf(fps_cap(0, 99.0), 0.1)
	d["gain"] = [snappedf(float(main.gain[0]), 0.01), snappedf(float(main.gain[1]), 0.01)]
	d["ir_ex"] = snappedf(float(main.ir_ex), 0.001)
	var th := {}
	for k in ["ground", "stone", "road", "caravan", "window", "tent", "car", "sky", "lamp"]:
		var tm = main.tmats.get(k, null)
		if tm != null:
			th[k] = snappedf(float(tm.get_shader_parameter("temp")), 0.1)
	d["temps"] = th
	d["ambient"] = main.ambient
	if main.thermsensor != null:
		d["thermsensor"] = main.thermsensor.info()          # 3D-4.26: the sensor model (P2)
	if main.waerme_welt != null:
		d["waerme"] = main.waerme_welt.info()              # 3D-4.26: engines that cool down, tent (P3)
	return d


func control(d: Dictionary) -> Dictionary:
	"""control API {action: simreal, do: info | set (key, value) | sweep | bird | spawn (kind, from, to)}"""
	var op := str(d.get("do", "info"))
	if op == "set" and str(d.get("key", "")) in SAVE:
		var k := str(d["key"])
		set(k, float(d.get("value", 0)) if typeof(get(k)) == TYPE_FLOAT else bool(d.get("value", false)))
		save()
		if k == "ir_real":
			_ir_setup()
	elif op == "test":
		test_rs = float(d.get("rs", 0.0))
	elif op == "sweep":
		start_sweep(float(d.get("dur", 0.0)))           # dur: longer, for tests
	elif op == "bird":
		lens_bird(float(d.get("dur", 0.0)))
	elif op == "spawn":
		var f = d.get("from", null)
		var t = d.get("to", null)
		main.spawn(str(d.get("kind", "hooded")), Vector3(float(f[0]), 0, float(f[1])) if f is Array else null, Vector3(float(t[0]), 0, float(t[1])) if t is Array else null)
	return {"ok": true, "simreal": info()}


# ---- 1. like a real Pi 5 ---------------------------------------------------------------------------------------------
func fps_cap(i: int, f: float) -> float:
	if not pi_on or f <= 0.0:
		return f
	if i == 0:
		return minf(f, pi_fps * _jit)
	if i == 1:
		return minf(f, minf(8.0, pi_fps))
	return f


func on_jpg(i: int, jpg: PackedByteArray) -> void:
	if i > 1:
		return
	if not pi_on or pi_delay < 0.02:
		if not _buf[i].is_empty():
			_buf[i].clear()
		return
	var t: float = main.now()
	_buf[i].append([t, jpg])
	while _buf[i].size() > 2 and t - float(_buf[i][0][0]) > pi_delay + 1.0:
		_buf[i].pop_front()


func delayed(i: int, cur: PackedByteArray) -> PackedByteArray:
	if not pi_on or pi_delay < 0.02 or i > 1 or _buf[i].is_empty():
		return cur
	var t: float = main.now() - pi_delay
	var best: PackedByteArray = _buf[i][0][1]
	for e in _buf[i]:
		if float(e[0]) <= t:
			best = e[1]
		else:
			break
	return best


# ---- 2. + 3. lens, sensor, infrared ----------------------------------------------------------------------------------
func _ir_setup() -> void:
	var l: SpotLight3D = main.ir_light
	if l == null:
		return
	if ir_real:
		l.spot_angle = 32.0                 # an 850 nm LED with a lens: about 60° wide, brightest in the middle
		l.spot_angle_attenuation = 1.6
		l.spot_attenuation = 2.0            # the light falls off with the square of the distance
	else:
		l.spot_angle = 48.0
		l.spot_angle_attenuation = 1.0
		l.spot_attenuation = 1.0


func before_capture(i: int) -> void:
	if i >= main.camfx_mats.size():
		return
	var m: ShaderMaterial = main.camfx_mats[i]
	var fx: bool = main.realism != null and main.realism.fx_on
	var on: bool = lens_on and fx
	var dark: bool = main.is_dark()
	var grey: bool = i == 0 and dark and main.ir_on() and not main.white_light.light_energy > 0.0
	m.set_shader_parameter("distort", (0.05 if i == 0 else 0.16) if on else 0.0)
	var rs := 0.0
	if on and i == 0:
		rs = clampf(-float(main.pan_vel) * 0.024 / deg_to_rad(float(main.CAM_FOV[0])), -0.08, 0.08)   # ~24 ms to read all rows
	if test_rs != 0.0 and i == 0:
		rs = test_rs
	m.set_shader_parameter("rshutter", rs)
	var cap: float = main.gain_cap()
	var amp: float = clampf((float(main.gain[i]) - 1.0) / maxf(0.5, cap - 1.0), 0.0, 1.0)
	var sh := 0.0
	if on:
		sh = 0.012 + (0.07 * amp + 0.03 if dark else 0.03 * amp)
		if grey:
			sh = 0.018 + 0.02 * clampf(float(main.ir_ex) * 2.0, 0.0, 1.0)   # long exposure (far scene) = more grain
	m.set_shader_parameter("shot", sh)
	var bl := 0.0
	if ir_real and fx and dark and main.quality != "simple":
		bl = 0.9 if grey else (0.45 if main.white_light.light_energy > 0.05 else 0.0)
	elif ir_real and fx and dark and grey:
		bl = 0.5                                                # «simple»: the cheap half
	m.set_shader_parameter("bloom", bl)
	# fog, rain and snow in the camera's own light (infrared, or the white light at night): a veil, not a white wall -
	# the exposure (main.ir_ex) follows the brighter picture by itself, far parts fade, near drops / flakes shine
	var own_light: bool = dark and (grey or main.white_light.light_energy > 0.05)
	var hz := 0.0
	var fl := 0.0
	if ir_real and fx and own_light:
		hz = {"fog": 0.75, "rain": 0.28, "snow": 0.4, "cloudy": 0.0}.get(main.weather, 0.0) + (0.3 if main.cond["fogged"] else 0.0)
		fl = {"rain": 1.0, "snow": 1.0}.get(main.weather, 0.0) * (1.0 if i == 0 else 0.5)
	m.set_shader_parameter("haze", minf(hz, 0.9))
	m.set_shader_parameter("flakes", fl)
	m.set_shader_parameter("veil_k", clampf(float(main.ir_ex) * 3.0, 0.12, 1.0) if grey else 0.6)
	m.set_shader_parameter("flake_kind", 1.0 if main.weather == "snow" else 0.0)
	if i == 0 and grey and ir_real:
		main.ir_light.light_energy = 9.0 * 5.0 * 0.8          # same light at 5 m as before, but much more near and less far
		if main.ir_light.spot_attenuation < 1.5:
			_ir_setup()
	elif i == 0 and not ir_real and main.ir_light.spot_attenuation > 1.5:
		_ir_setup()
	_reflectors(i, dark, grey)


func add_reflector(parent: Node3D, pos: Vector3, size: Vector2, col: Color, rot := Vector3.ZERO) -> MeshInstance3D:
	"""a retro-reflector (quad, front = +Z of the node): flares up when the light of the camera shines on it"""
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = size
	mi.mesh = q
	mi.position = pos
	mi.rotation = rot
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.emission_enabled = true
	m.emission = col.lightened(0.35)
	m.emission_energy_multiplier = 0.0
	mi.material_override = m
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	_refl.append([mi, m])
	return mi


func _reflectors(i: int, dark: bool, grey: bool) -> void:
	if _refl.is_empty():
		return
	var cam: Camera3D = main.cams[i]
	var cp: Vector3 = cam.global_position
	var fwd: Vector3 = -main.cams[0].global_transform.basis.z
	var white: bool = main.white_light.light_energy > 0.05
	var keep := []
	for r in _refl:
		if not is_instance_valid(r[0]):
			continue
		keep.append(r)
		var e := 0.0
		if ir_real and dark and r[0].is_visible_in_tree() and (grey or white):
			var p: Vector3 = r[0].global_position
			var to: Vector3 = cp - p
			var d: float = maxf(0.3, to.length())
			var facing: float = r[0].global_transform.basis.z.normalized().dot(to / d)
			if facing > 0.15:
				var lp: Vector3 = main.head.global_position          # the lights sit on the head
				var ld: Vector3 = (p - lp).normalized()
				var in_cone: float = smoothstep(cos(deg_to_rad(36.0)), cos(deg_to_rad(24.0)), fwd.dot(ld))
				var reach: float = float(main.ir_range) * (2.5 if grey else 2.0)
				if d < reach:
					e = 10.0 * clampf(pow(7.0 / d, 1.1), 0.25, 3.0) * facing * in_cone
		r[1].emission_energy_multiplier = e
	_refl = keep


func note_car(c: Node3D, parked := true) -> void:
	"""scenes.gd (static_car) and actor.gd (cars driving): number plates that reflect; parked cars for the cat"""
	if c == null:
		return
	add_reflector(c, Vector3(0, 0.45, 2.185), Vector2(0.52, 0.12), Color(0.92, 0.92, 0.9))                       # rear plate
	add_reflector(c, Vector3(0, 0.45, -2.185), Vector2(0.52, 0.12), Color(0.92, 0.92, 0.9), Vector3(0, PI, 0))   # front plate
	for s in [-1, 1]:
		add_reflector(c, Vector3(0.72 * s, 0.5, 2.19), Vector2(0.09, 0.05), Color(0.85, 0.1, 0.08))               # red rear reflectors
	if parked:
		_cars.append(c)


func note_bike(b: Node3D) -> void:
	"""scenes.gd (bike): the red rear reflector and the spoke reflectors"""
	if b == null:
		return
	add_reflector(b, Vector3(0, 0.66, 0.5), Vector2(0.08, 0.05), Color(0.9, 0.08, 0.05))                       # red, behind
	add_reflector(b, Vector3(0, 0.8, -0.56), Vector2(0.07, 0.05), Color(0.95, 0.95, 0.92), Vector3(0, PI, 0))   # white, in front
	for z in [-0.55, 0.55]:
		for s in [-1, 1]:
			add_reflector(b, Vector3(0.012 * s, 0.54, z), Vector2(0.07, 0.035), Color(0.95, 0.75, 0.1), Vector3(0, PI / 2 * s, 0))   # spokes


# ---- scene: tarp, pennant, road sign -------------------------------------------------------------------------------
func on_scene() -> void:
	"""called after a scene was built (main._build_scene): the extra things of this scene"""
	_cars = _cars.filter(func(c): return is_instance_valid(c) and not c.is_queued_for_deletion())
	_flap_mats.clear()
	_sign_done = false
	var root: Node3D = main.scenes.root
	if root == null:
		return
	if fa_flags and main.scene != "schlafzimmer":
		var tent = main.obj.get("pir", null)
		if tent is Vector3 and tent != Vector3.ZERO:
			# a loose tarp on a line beside the tent: fixed at the top, the free edge flaps
			var tp: Vector3 = tent + Vector3(1.9, 0, 0.6)
			tp = main.free_spot(tp, 0.8, true)
			_pole(root, tp + Vector3(-0.8, 0, 0), 1.5)
			_pole(root, tp + Vector3(0.8, 0, 0), 1.5)
			_flap(root, Vector2(1.6, 1.1), tp + Vector3(0, 0.95, 0), Vector3(0, 0, 0), Color(0.15, 0.32, 0.55), true, 1.2)
		# a pennant on a short pole in front of the camera (the wind moves it all night)
		var pp: Vector3 = main.free_spot(Vector3(-1.6, 0, -13.0), 0.6, true)
		_pole(root, pp, 2.6)
		_flap(root, Vector2(0.75, 0.42), pp + Vector3(0.39, 2.35, 0), Vector3.ZERO, Color(0.9, 0.75, 0.1), false, 1.0)
	if ir_real and main.scene != "schlafzimmer":
		var rz: float = float(main.scenes.data.get("road_z", -28.0))
		var sp: Vector3 = Vector3(7.5, 0, rz + 3.2)
		if absf(rz) < 80.0:
			_road_sign(root, sp)


func _pole(root: Node3D, p: Vector3, h: float) -> void:
	main.scenes.put(root, main.scenes.cyl(0.025, 0.03, h, 6), p + Vector3(0, h / 2.0, 0), Color(0.6, 0.6, 0.62), "stone")


func _flap(root: Node3D, size: Vector2, pos: Vector3, rot: Vector3, col: Color, hang: bool, strength: float) -> MeshInstance3D:
	var q := QuadMesh.new()
	q.size = size
	q.subdivide_width = 10 if main.quality != "simple" else 6
	q.subdivide_depth = 6 if main.quality != "simple" else 4
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.position = pos
	mi.rotation = rot
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/flap.gdshader")
	sm.set_shader_parameter("color", col)
	sm.set_shader_parameter("seed", randf() * 10.0)
	sm.set_shader_parameter("hang", 1.0 if hang else 0.0)
	sm.set_shader_parameter("strength", strength)
	sm.set_shader_parameter("wind", main.wind)
	mi.material_override = sm
	mi.layers = 1
	mi.add_to_group("cloth")
	mi.visible = main.world_cloth
	main.cloth_mats.append(sm)                  # main.gd gives it the wind with the gusts (like flags and laundry)
	root.add_child(mi)
	var th := MeshInstance3D.new()              # the thermal camera sees it a little warmer than the air (it was in the sun)
	th.mesh = q
	th.position = pos
	th.rotation = rot
	th.material_override = main.tmat("tent")
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(th)
	return mi


func _road_sign(root: Node3D, p: Vector3) -> void:
	"""a road sign with a reflecting face (in the infrared light it shines like a lamp)"""
	_pole(root, p, 2.2)
	var face: Node3D = main.scenes.node(root, p + Vector3(0, 2.0, 0), 0.0)
	main.scenes.put(face, main.box(0.62, 0.62, 0.03), Vector3(0, 0, -0.02), Color(0.5, 0.5, 0.52), "stone")
	add_reflector(face, Vector3(0, 0, 0.0), Vector2(0.58, 0.58), Color(0.95, 0.95, 0.92))
	add_reflector(face, Vector3(0, 0, 0.002), Vector2(0.5, 0.1), Color(0.85, 0.1, 0.08))
	main.add_obstacle(p, 0.15)
	_sign_done = true


# ---- 4. thermal ------------------------------------------------------------------------------------------------------
func cloth_t(base: float, jog: bool, variant := "") -> float:
	"""the surface of clothes: between the air and the skin (a jacket insulates); wet clothes are close to the air.
	3D-4.26: the values come from waerme.gd (what people wear at this temperature, after running warmer, wet cooler)"""
	if not th_real:
		return base
	var amb: float = main.ambient
	var lvl := Waerme.cloth_level(amb, variant)
	if jog and lvl in ["jacket", "thick"]:
		lvl = "light"                               # joggers wear thin, tight clothes
	return Waerme.cloth(amb, lvl, main.weather == "rain", jog)


func _sun_at(h: float) -> float:
	"""elevation of the sun (degrees) at hour h of the day of the scene (the same NOAA formula as main.sun_pos)"""
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	var lo: float = main.ort_lon if main.ort_lon != 0.0 else 8.2
	var doy: int = main.day_of_year()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var hu := h - tz
	var g := TAU / 365.0 * (doy - 1 + (hu - 12.0) / 24.0)
	var eqt := 229.18 * (0.000075 + 0.001868 * cos(g) - 0.032077 * sin(g) - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
	var decl := 0.006918 - 0.399912 * cos(g) + 0.070257 * sin(g) - 0.006758 * cos(2 * g) + 0.000907 * sin(2 * g)
	var tst := hu * 60.0 + eqt + 4.0 * lo
	var ha := deg_to_rad(tst / 4.0 - 180.0)
	var phi := deg_to_rad(la)
	var cz := sin(phi) * sin(decl) + cos(phi) * cos(decl) * cos(ha)
	return 90.0 - rad_to_deg(acos(clampf(cz, -1.0, 1.0)))


func temps() -> void:
	"""after main._update_temps: heat that stays (stones, asphalt, cars), rain, windows - only with «Wärmebild wie echt»"""
	if not th_real:
		return
	var amb: float = main.ambient
	var cl: float = main.clouds()
	var rain: bool = main.weather == "rain"
	var h: float = main.hour()
	var sun := PackedFloat32Array()                 # the sun of the last 24 hours, every half hour
	for j in range(48):
		sun.append(maxf(0.0, _sun_at(fposmod(h - j * 0.5, 24.0))) / 50.0 * (1.0 - cl))
	# [thermal material, warming by the full sun (°C), how long it keeps the heat (hours)] - 3D-4.26: table in waerme.gd
	# (now also car roofs and tent cloth: hot in the afternoon sun, below the air in a clear night - false alarm sources)
	var clear_night: float = (1.0 - cl) if main.is_dark() else 0.0
	for key in Waerme.SUN:
		var k: Array = Waerme.SUN[key]
		var heat := 0.0
		var T: float = k[1]
		for j in range(48):
			heat += sun[j] * exp(-j * 0.5 / T) * (0.5 / T)
		heat *= float(k[0])
		if rain:
			heat *= 0.3                             # rain takes the heat away (and evaporates: colder than the air)
		var t: float = amb + heat - (1.6 if rain else 0.0) - float(Waerme.NIGHT_SKY_COOL.get(key, 0.0)) * clear_night
		if key == "road":
			t -= 1.0 if not rain else 0.0           # asphalt at night: a little under the air without the stored heat
		main.tmat(key).set_shader_parameter("temp", t)
	if rain:
		main.tmat("tent").set_shader_parameter("temp", amb - 1.2)
		main.tmat("tree").set_shader_parameter("temp", amb - 1.5)
	# windows: glass lets no thermal light through - it reflects; at a clear night the cold sky, in the day the warm world
	var sky_t: float = Waerme.sky_zenith(amb, cl, float(main.humidity))
	var ev := 1.0 if h >= 17.0 or h < 1.0 else 0.0
	var inside: float = amb + 8.0 * ev + 3.0
	var refl: float = sky_t if main.is_dark() else amb + 4.0 * sun[0]
	main.tmat("window").set_shader_parameter("temp", lerpf(inside, refl, 0.3))   # glass: emissivity ~0.85, at a slant it reflects more
	main.tmat("glass").set_shader_parameter("temp", lerpf(amb, refl, 0.35))


# ---- 5. false alarms: light sweep, cat on the roof, birds at the lens ------------------------------------------------
func start_sweep(dur := 0.0) -> void:
	"""the light of a car turning in at the road sweeps over the walls, the tent and the meadow (3-4 s)"""
	if _sweep != null:
		return
	var rz: float = float(main.scenes.data.get("road_z", -28.0))
	var side := 1.0 if randf() < 0.5 else -1.0
	var p := Vector3(side * randf_range(12.0, 22.0), 0.75, clampf(rz, -60.0, -12.0))
	var l := SpotLight3D.new()
	l.spot_range = 70.0
	l.spot_angle = 22.0
	l.spot_angle_attenuation = 1.4
	l.light_color = Color(1.0, 0.95, 0.85)
	l.light_energy = 0.0
	l.shadow_enabled = main.quality != "simple"
	main.scenes.root.add_child(l)
	l.global_position = p
	var to_c: Vector3 = main.head.global_position - p
	var a_c := atan2(-to_c.x, -to_c.z)
	_sweep = {"light": l, "t0": main.now(), "dur": dur if dur > 0.0 else randf_range(3.0, 4.5), "a0": a_c - side * 0.9, "a1": a_c + side * 0.7}


func _sweep_tick() -> void:
	if _sweep == null:
		return
	var l: SpotLight3D = _sweep["light"]
	if not is_instance_valid(l):
		_sweep = null
		return
	var k: float = (main.now() - float(_sweep["t0"])) / float(_sweep["dur"])
	if k >= 1.0:
		l.queue_free()
		_sweep = null
		return
	var a: float = lerp_angle(float(_sweep["a0"]), float(_sweep["a1"]), smoothstep(0.0, 1.0, k))
	l.rotation = Vector3(-0.04, a, 0)
	l.light_energy = 90.0 * smoothstep(0.0, 0.12, k) * (1.0 - smoothstep(0.85, 1.0, k))


func cat_roof() -> Node3D:
	"""a cat jumps onto a parked car, sits there, washes, looks round - and jumps down again"""
	_cars = _cars.filter(func(c): return is_instance_valid(c) and c.is_inside_tree())
	var car: Node3D = null
	var best := 1e9
	var hp: Vector3 = main.head.global_position
	var fw: Vector3 = -main.cams[0].global_transform.basis.z
	for c in _cars:
		var to: Vector3 = c.global_position - hp
		var d: float = to.length()
		var front: float = Vector2(fw.x, fw.z).normalized().dot(Vector2(to.x, to.z).normalized())
		if d < best and d < 35.0 and front > 0.87:          # a car the head camera sees (±30°)
			best = d
			car = c
	if car == null:                                            # no car in the picture: one parks for the cat
		var p: Vector3 = main.free_spot(_in_view(10.0, 14.0), 2.6, false)
		main.scenes.static_car(p, 0.5, Color(0.75, 0.75, 0.78))
		if _cars.is_empty():
			return null
		car = _cars[-1]
	var roof: Vector3 = car.global_transform * Vector3(0, 1.42, 0.25)
	var side: Vector3 = car.global_transform.basis.x.normalized()
	var start: Vector3 = car.global_position + side * 2.2 + Vector3(0, 0, 0.5)
	var v = main.spawn("cat", start, Vector3(roof.x, 0, roof.z))
	v.position = Vector3(roof.x, 1.42, roof.z)                # it is up there already (jumped)
	v.route = [[Vector3(roof.x, 0, roof.z), randf_range(20.0, 45.0), 0.0, hp], car.global_position - side * 25.0]
	v.target = Vector3(roof.x, 0, roof.z)
	v.next_idle = main.now() + 999.0
	_track.append({"v": v, "do": "roof", "y": 1.42, "up": false})
	return v


func lens_bird(dur := 0.0) -> void:
	"""a bird right in front of the head camera (0.4-1.5 m): crosses in a fraction of a second, or flutters for a moment"""
	if main.fauna == null:
		return
	var cam: Transform3D = main.cams[0].global_transform
	var d := randf_range(0.4, 1.5)
	var hover := randf() < 0.35 or dur > 0.0
	var s := 1.0 if randf() < 0.5 else -1.0
	var w := d * 0.75
	var b: Dictionary = main.fauna._bird(0.16, [Color(0.12, 0.1, 0.09), Color(0.45, 0.35, 0.25), Color(0.5, 0.5, 0.52)][randi() % 3], 39.0)
	b["from"] = cam * Vector3(-s * w * 1.6, randf_range(-0.2, 0.35) * d, -d)
	b["mid"] = cam * Vector3(s * randf_range(-0.2, 0.2) * d, randf_range(0.1, 0.3) * d, -d * 0.9)
	b["to"] = cam * Vector3(s * w * 1.6, randf_range(0.1, 0.6) * d, -d * randf_range(0.8, 1.4))
	b["t0"] = main.now()
	b["dur"] = dur if dur > 0.0 else randf_range(0.35, 0.7) + (1.8 if hover else 0.0)
	b["hover"] = hover
	b["node"].position = b["from"]
	_birds.append(b)


func _move_birds(dt: float) -> void:
	var t: float = main.now()
	for b in _birds.duplicate():
		var k: float = (t - float(b["t0"])) / float(b["dur"])
		if k >= 1.0 or not is_instance_valid(b["node"]):
			if is_instance_valid(b["node"]):
				b["node"].queue_free()
			_birds.erase(b)
			continue
		var p: Vector3
		if bool(b["hover"]):                                    # in - flutters in front of the lens - away
			if k < 0.2:
				p = (b["from"] as Vector3).lerp(b["mid"], k / 0.2)
			elif k < 0.8:
				p = (b["mid"] as Vector3) + Vector3(sin(t * 9.0) * 0.03, sin(t * 6.0) * 0.04, 0)
			else:
				p = (b["mid"] as Vector3).lerp(b["to"], (k - 0.8) / 0.2)
		else:
			p = (b["from"] as Vector3).lerp(b["to"], k)
		var n: Node3D = b["node"]
		var prev: Vector3 = n.position
		n.position = p
		if p.distance_to(prev) > 0.002:
			n.look_at(p + (p - prev), Vector3.UP)
		var fl: float = 1.0 * sin(t * 28.0)
		b["wings"][0].rotation.z = fl
		b["wings"][1].rotation.z = -fl


# ---- 6. + 7. difficult persons, animals ------------------------------------------------------------------------------
func is_kind(k: String) -> bool:
	return KINDS.has(k)


func _in_view(dist: float, off_deg := 0.0) -> Vector3:
	"""a point on the ground in the direction the head camera looks (off_deg: to the side)"""
	var hp: Vector3 = main.head.global_position
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	f.y = 0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	f = f.rotated(Vector3.UP, deg_to_rad(-off_deg))
	return Vector3(hp.x, 0, hp.z) + f * dist


func spawn_kind(kind: String, from, to) -> Node3D:
	"""main.spawn(kind) with one of KINDS: built from the normal visitors (actor.gd) with a few extras"""
	var now: float = Time.get_ticks_msec() / 1000.0          # the clock of the visitors (actor.now_s)
	match kind:
		"hooded":
			var v = main.spawn("person", from, to)
			_rain_cape(v)
			return v
		"backpacker":
			var v = main.spawn("person", from, to)
			_big_pack(v)
			return v
		"phoner":
			var stop: Vector3 = main.free_spot(_in_view(randf_range(8.0, 14.0), randf_range(-18.0, 18.0)), 0.5, true)
			var side := 1.0 if randf() < 0.5 else -1.0
			var a: Vector3 = from if from != null else stop + Vector3(side * 28.0, 0, randf_range(-4.0, 4.0))
			var v = main.spawn("person", a, stop)
			var secs := randf_range(35.0, 70.0)
			v.route = [[stop, secs, 0.0, stop + Vector3(randf_range(-5, 5), 0, randf_range(-5, 5))], to if to != null else stop + Vector3(-side * 30.0, 0, randf_range(-6.0, 6.0))]
			v.target = stop
			v.next_idle = now + 999.0
			_phone(v)
			_track.append({"v": v, "do": "phone", "secs": secs, "on": false})
			return v
		"group2", "group3", "group4":
			var n := int(kind.substr(5))
			var lead = main.spawn("person", from, to)
			lead.next_idle = now + 999.0                         # a group does not stand about one by one
			var offs := [Vector3(0.75, 0, 0.15), Vector3(-0.7, 0, 0.35), Vector3(0.2, 0, 0.9), Vector3(1.1, 0, 0.8)]
			for j in range(n - 1):
				var o: Vector3 = offs[j]
				var f = main.spawn("child" if randf() < 0.12 else "person", lead.position + lead.global_transform.basis * o, lead.target)
				f.leader = lead
				f.follow_off = o
				f.speed = lead.speed * 1.35
			return lead
		"edge_sneak":
			var half: float = float(main.CAM_FOV[0]) * 0.5 - 3.0       # just inside the edge of the picture
			var s := 1.0 if randf() < 0.5 else -1.0
			var far: Vector3 = _in_view(17.0, s * (half + 14.0))       # comes from outside the picture
			var v = main.spawn("burglar", far, _in_view(13.0, s * half))
			v.speed = 0.55
			v.set_meta("sneak", true)
			if main.is_dark() and randf() < 0.3:
				v.add_torch()
			var hp: Vector3 = main.head.global_position
			v.route = [[_in_view(11.0, s * half), randf_range(4.0, 8.0), 1.0, hp], [_in_view(8.5, s * (half - 1.0)), randf_range(5.0, 9.0), 1.0, hp],
					[_in_view(6.5, s * half), randf_range(4.0, 8.0), 2.0, hp], [_in_view(5.0, s * (half + 1.0)), randf_range(3.0, 6.0), 1.0, hp],
					_in_view(9.0, s * (half + 22.0)), _in_view(30.0, s * (half + 40.0))]
			v.next_idle = now + 999.0
			return v
		"deer_bedded":
			var p: Vector3 = main.free_spot(from if from != null else _in_view(randf_range(10.0, 16.0), randf_range(-15.0, 15.0)), 0.8, false)
			var away: Vector3 = to if to != null else p + Vector3(randf_range(-30, 30), 0, -35.0)
			var v = main.spawn("deer", p, away)
			v.idle_kind = "lie"
			v.idle_until = now + randf_range(12.0, 25.0)
			v.next_idle = now + 999.0
			_track.append({"v": v, "do": "rise", "step": 0})
			return v
		"dog_leash":
			var w = main.spawn("person", from, to)
			var dg = main.spawn("dog", w.position + Vector3(1.0, 0, 1.0), w.target)
			leash(w, dg)
			return w
		"boar_herd":
			var lead = main.spawn("boar", from, to)
			lead.speed = 0.9
			for j in range(randi_range(3, 6)):
				var o := Vector3(randf_range(-2.2, 2.2), 0, randf_range(0.6, 3.5))
				var b = main.spawn("boar", lead.position + o, lead.target + o)
				b.leader = lead
				b.follow_off = o
				b.speed = 1.5
				if j > 1:
					b.body_root.scale *= 0.55                          # young ones
			lead.next_idle = now + 2.0
			return lead
		"cat_roof":
			var c = cat_roof()
			return c if c != null else main.spawn("cat", from, to)
	return main.spawn("person", from, to)


func leash(person: Node3D, dog: Node3D) -> void:
	"""the dog walks close beside its person on a leash (a thin line from the hand to the collar)"""
	dog.leader = person
	dog.speed = person.speed * 1.6
	if not leash_on:
		dog.follow_off = Vector3(randf_range(-1.2, 1.2), 0, randf_range(0.8, 2.0))
		return
	dog.follow_off = Vector3(0.75 if randf() < 0.5 else -0.75, 0, randf_range(0.2, 0.9))
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.008
	cm.bottom_radius = 0.008
	cm.height = 1.0
	cm.radial_segments = 4
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = main.mat(Color(0.7, 0.15, 0.1))
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.scenes.root.add_child(mi)                # not under main.visitors: everything there is a visitor (actor.gd)
	_leash.append({"dog": dog, "person": person, "mesh": mi})


func _leash_tick() -> void:
	for e in _leash.duplicate():
		var d = e["dog"]
		var p = e["person"]
		var mi = e["mesh"]
		if not is_instance_valid(mi):
			_leash.erase(e)
			continue
		if not is_instance_valid(d) or not is_instance_valid(p) or d.done or p.done or not leash_on:
			mi.queue_free()
			_leash.erase(e)
			continue
		var hand: Vector3 = p.arms[0][2].global_transform * Vector3(0, -0.33, 0) if p.arms.size() > 0 else p.global_position + Vector3(0, 0.9, 0)
		var collar: Vector3 = d.head.global_position if d.head != null else d.global_position + Vector3(0, 0.45, 0)
		var mid := (hand + collar) * 0.5 + Vector3(0, -0.12, 0)        # it hangs a little
		var dv := collar - hand
		var L := dv.length()
		if L < 0.05:
			continue
		mi.global_position = mid
		var y := dv / L
		var x := y.cross(Vector3.UP)
		if x.length() < 0.01:
			x = Vector3.RIGHT
		x = x.normalized()
		var z := x.cross(y).normalized()
		mi.global_transform.basis = Basis(x, y * L, z)


func _rain_cape(v) -> void:
	"""a rain cape down to the knees and the hood up: no neck, no arms, a shapeless figure - and cool in the thermal picture"""
	var col: Color = [Color(0.12, 0.22, 0.15), Color(0.12, 0.15, 0.28), Color(0.45, 0.45, 0.47), Color(0.7, 0.6, 0.15)][randi() % 4]
	var t: float = main.ambient + (1.5 if th_real else 6.0)
	var cape = v._part(v.torso, v._cyl(0.17, 0.46, 1.12, 12), Vector3(0, -0.02, 0.02), col, t)
	cape.scale = Vector3(1.0, 1.0, 0.8)
	v._part(v.head, v._sph(0.14, 0.3), Vector3(0, 0.17, 0.025), col.darkened(0.1), t + 0.5, Vector3.ZERO, Vector3(1.0, 1.0, 1.08))
	v._part(v.head, v._cyl(0.13, 0.15, 0.08, 10), Vector3(0, 0.29, -0.04), col.darkened(0.05), t + 0.5, Vector3(-0.35, 0, 0))   # the brim of the hood


func _big_pack(v) -> void:
	"""a big trekking backpack above the head, with a sleeping mat - the outline is no longer a person's"""
	var col: Color = [Color(0.6, 0.15, 0.1), Color(0.15, 0.3, 0.2), Color(0.2, 0.2, 0.25), Color(0.85, 0.5, 0.1)][randi() % 4]
	var t: float = main.ambient + 2.0
	v._part(v.torso, v._box(0.42, 0.78, 0.3), Vector3(0, 0.42, 0.27), col, t)
	v._part(v.torso, v._cyl(0.09, 0.09, 0.6, 10), Vector3(0, 0.88, 0.27), Color(0.25, 0.45, 0.6), t, Vector3(0, 0, PI / 2))   # the mat on top
	v._part(v.torso, v._box(0.34, 0.2, 0.12), Vector3(0, 0.2, 0.46), col.darkened(0.25), t)


func _phone(v) -> void:
	"""a phone in the right hand (at the ear when calling); at night the screen glows"""
	if v.arms.size() < 2:
		return
	var ph = v._part(v.arms[1][2], v._box(0.07, 0.14, 0.012), Vector3(0.0, -0.36, -0.03), Color(0.08, 0.08, 0.1), 30.0)
	if main.is_dark():
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.7, 0.8, 1.0)
		m.emission_enabled = true
		m.emission = Color(0.6, 0.75, 1.0)
		m.emission_energy_multiplier = 2.5
		ph.material_override = m


func animals_real() -> bool:
	return anim_real


# ---- every frame -----------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or not main.sim_active:
		return
	var t: float = main.now()
	_jit_t -= dt
	if _jit_t <= 0.0:
		_jit_t = 1.0
		_jit = randf_range(0.85, 1.06)                 # the Pi does not deliver evenly (the AI needs more for some pictures)
	_sweep_tick()
	_move_birds(dt)
	_leash_tick()
	_track_tick(t, dt)
	_slow -= dt
	if _slow > 0.0:
		return
	_slow = 0.5
	var quiet: bool = main.measuring() or main.busy_with() != ""
	var dark: bool = main.is_dark()
	if fa_sweep and dark and not quiet and t > _next_sweep:
		_next_sweep = t + randf_range(35.0, 90.0)
		start_sweep()
	if fa_catroof and dark and not quiet and t > _next_cat:
		_next_cat = t + randf_range(120.0, 300.0)
		if not _cars.is_empty():
			cat_roof()
	if fa_birds and not dark and not quiet and main.fauna != null and main.fauna.on and main.weather not in ["rain", "snow"] and t > _next_bird:
		if _next_bird > 0.0:
			lens_bird()
		_next_bird = t + randf_range(70.0, 200.0)
	if hard_auto and main.auto_visitors and not quiet and t > _next_hard:
		if _next_hard > 0.0 and main.visitors.get_child_count() < int(main.max_visitors):
			main.spawn(HARD_AUTO[randi() % HARD_AUTO.size()])
		_next_hard = t + randf_range(90.0, 240.0) / maxf(0.25, float(main.visit_rate))


func _track_tick(t: float, dt: float) -> void:
	for e in _track.duplicate():
		var v = e["v"]
		if not is_instance_valid(v) or v.done:
			_track.erase(e)
			continue
		match str(e["do"]):
			"roof":                                          # on the roof until it goes on; then it jumps down
				if v.now_s() < v.wait_until:
					e["up"] = true                           # sitting up there
				elif bool(e["up"]):
					e["y"] = move_toward(float(e["y"]), 0.0, dt * 4.5)
				v.position.y = float(e["y"])
				if float(e["y"]) <= 0.0:
					_track.erase(e)
			"phone":                                         # arrived: on the phone as long as it stands there
				if not bool(e["on"]) and v.now_s() < v.wait_until:
					e["on"] = true
					v.idle_kind = "phone"
					v.idle_until = v.wait_until
				elif bool(e["on"]) and v.now_s() >= v.wait_until:
					_track.erase(e)
			"rise":                                          # lying -> stands up -> raises the head (alert) -> walks on
				if int(e["step"]) == 0 and v.now_s() >= v.idle_until:
					e["step"] = 1
					v.idle_kind = "alert"
					v.idle_until = v.now_s() + randf_range(3.5, 6.0)
				elif int(e["step"]) == 1 and v.now_s() >= v.idle_until:
					v.next_idle = v.now_s() + randf_range(3.0, 8.0)
					_track.erase(e)
