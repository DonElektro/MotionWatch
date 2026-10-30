extends Node
## 3D-4.x «Umgebung wie echt» (Wunsch Daniel, 30.10.2026): kleine Dinge der Umgebung, die echte Kameras stören - jedes
## einzeln abschaltbar, bei Grafik «einfach» ohne die teuren Teile (Partikel, kleine Lichter).
##  Kamerabild · Schwierige Bedingungen
##   - Lampen gehen an: Lampe mit Bewegungsmelder beim Nachbarn und ein Fenster, hinter dem der Fernseher flackert
##     (die Lampen der Szene, das Licht im Wohnwagen und die Strassenlampen gab es schon: main.gd / scenes.gd)
##   - Spiegelungen: Pfützen nach dem Regen spiegeln (Scheinwerfer, Lampen), Spritzer, wenn jemand hineintritt
##     (Augen der Tiere im Infrarot, Rückstrahler und Scheinwerfer gab es schon: actor.gd / simreal.gd)
##   - Rauch und Dampf: Grill, Gaskocher, Funken des Lagerfeuers (objekte_plus.gd), Nebelschwaden in feuchten Nächten
##   - Mücken-Schwarm in der Dämmerung (Motten am Licht, Spinnennetz, Fledermäuse gab es schon: main.insects, cond «web», fauna.gd)
##   - Türen und Tore: ein Gartentor und eine Mülltonne mit Deckel im Bild bewegen sich im Wind
##  Wetter · Natur und Wind
##   - Pflanzen: fallende Blätter im Herbst, Schnee fällt von den Ästen (Gras und Büsche wiegen sich schon: foliage / meadow)
##   - Boden: Spuren im Schnee (Menschen und Tiere) bleiben liegen, nach dem Regen Fussspuren im Matsch;
##     Schritte auf Kies, Laub und Schnee hört das Mikrofon (sound_db)
##  Besuch
##   - Fahrzeuge: E-Trottinett, Rollstuhl (Personen, actor.gd), Lieferroboter, Mähroboter (keine Personen: kein Push erwartet)
##     (Kinderwagen gab es schon: «stroller»)
##   - Haustiere: Katze auf dem Zaun, Hühner (Hühnerstall), Igel am Futternapf (Hund an der Leine gab es schon: simreal.gd)
## Einstellungen in user://umgebung.json.

var main
const FILE := "user://umgebung.json"
const Obj = preload("res://scripts/objects.gd")
const SAVE := ["u_lamps", "u_reflect", "u_smoke", "u_insects", "u_plants", "u_doors", "u_tracks", "u_steps", "u_vehicles"]
var u_lamps := false        # neighbour's motion lamp + TV window (puts things into the scene: off by default - comparable tests)
var u_reflect := true       # puddles reflect, splashes
var u_smoke := true         # smoke / steam of the things, sparks, fog wisps
var u_insects := false      # mosquito swarm at dusk
var u_plants := true        # falling leaves, snow from the branches
var u_doors := false        # garden gate + bin lid in the picture (puts things into the scene)
var u_tracks := true        # tracks in the snow / mud stay
var u_steps := true         # steps on gravel / leaves / snow for the microphone
var u_vehicles := false     # e-scooter, wheelchair, delivery robot, robot mower come by themselves now and then

# (e_trotti / rollstuhl: persons with the actor.gd variants «escooter» / «wheelchair»)
const KINDS := {"e_trotti": ["E-Trottinett (Person, schnell)", "Fahrzeuge"], "rollstuhl": ["Rollstuhl (Person, sitzt)", "Fahrzeuge"],
		"delivery_bot": ["Lieferroboter (keine Person)", "Fahrzeuge"], "robomower": ["Mähroboter (keine Person)", "Fahrzeuge"],
		"cat_fence": ["Katze auf dem Zaun", "Tiere schicken"], "hedgehog_bowl": ["Igel am Futternapf", "Tiere schicken"],
		"chickens": ["Hühner (mit Hühnerstall)", "Tiere schicken"]}
const GRAVEL := ["camping", "stellplatz", "parkplatz", "baustelle", "camping_voll", "velodieb", "bauernhof"]

var _placed: Array = []              # things this script put into the scene (lamps, gate, bin, bowl, coop, fence)
var _puddles: Array = []             # [MeshInstance3D, StandardMaterial3D, Vector3 centre, radius]
var _wisps: Array = []               # [MeshInstance3D, StandardMaterial3D, phase]
var _movers: Array = []              # robots: {n, kind, path, i, spd, t_end, wheels}
var _mosq: CPUParticles3D = null
var _leaves: CPUParticles3D = null
var _snowfall: CPUParticles3D = null
var _tracks: MultiMeshInstance3D = null
var _track_n := 0
var _last_print := {}                # instance id -> [position, left/right]
var _slow := 0.0
var _next_snow := 0.0
var _next_veh := 0.0
const TRACK_MAX := 600
var stats := {"prints": 0, "splashes": 0, "steps": 0, "snow_puffs": 0, "robots": 0}


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, bool(d[k]))


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _put(k: String, v, rebuild := false) -> void:
	set(k, v)
	save()
	if rebuild:
		on_scene()


func add_controls() -> void:
	var m = main
	var hb := {"sub": "Schwierige Bedingungen"}
	m.add_control("toggle", "u_lamps", "Lampen gehen an: Lampe mit Bewegungsmelder beim Nachbarn, Fernseher flackert hinter einem Fenster (stellt beides ins Bild)",
			func(): return u_lamps, func(v): _put("u_lamps", bool(v), true), "Kamerabild", hb)
	m.add_control("toggle", "u_reflect", "Pfützen nach dem Regen spiegeln Scheinwerfer und Lampen, Spritzer beim Hineintreten",
			func(): return u_reflect, func(v): _put("u_reflect", bool(v), true), "Kamerabild", hb)
	m.add_control("toggle", "u_smoke", "Rauch und Dampf: Grill, Gaskocher, Funken vom Lagerfeuer, Nebelschwaden in feuchten Nächten",
			func(): return u_smoke, func(v): _put("u_smoke", bool(v)), "Kamerabild", hb)
	m.add_control("toggle", "u_insects", "Mücken-Schwarm in der Dämmerung vor der Kamera",
			func(): return u_insects, func(v): _put("u_insects", bool(v)), "Kamerabild", hb)
	m.add_control("toggle", "u_doors", "Türen und Tore im Wind: Gartentor und Mülltonnen-Deckel im Bild (stellt beides ins Bild)",
			func(): return u_doors, func(v): _put("u_doors", bool(v), true), "Kamerabild", hb)
	var nw := {"sub": "Natur und Wind"}
	m.add_control("toggle", "u_plants", "Fallende Blätter im Herbst, Schnee fällt in Böen von den Ästen",
			func(): return u_plants, func(v): _put("u_plants", bool(v)), "Wetter", nw)
	m.add_control("toggle", "u_tracks", "Spuren im Schnee (Menschen und Tiere) bleiben liegen, nach dem Regen Fussspuren im Matsch",
			func(): return u_tracks, func(v): _put("u_tracks", bool(v)), "Wetter", nw)
	m.add_control("toggle", "u_steps", "Schritte auf Kies, Laub und Schnee hört das Mikrofon",
			func(): return u_steps, func(v): _put("u_steps", bool(v)), "Wetter", nw)
	m.add_control("toggle", "u_vehicles", "Alltag: E-Trottinett, Rollstuhl, Lieferroboter und Mähroboter kommen ab und zu von selbst",
			func(): return u_vehicles, func(v): _put("u_vehicles", bool(v)), "Besuch", {"sub": "Von selbst"})
	for k in KINDS:
		var kk: String = k
		m.add_control("button", "u_send_" + kk, KINDS[kk][0], null, func(): main.spawn(kk), "Besuch", {"sub": KINDS[kk][1]})


func info() -> Dictionary:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	d["placed"] = _placed.filter(func(n): return is_instance_valid(n)).size()
	d["puddles"] = _puddles.size()
	d["puddle_on"] = not _puddles.is_empty() and (_puddles[0][0] as MeshInstance3D).visible
	d["wisps"] = _wisps.size()
	d["tracks"] = _track_n
	d["movers"] = _movers.size()
	d["stats"] = stats
	d["kinds"] = KINDS.keys()
	return d


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | spawn (kind) | snow_puff | clear_tracks}"""
	var op := str(d.get("do", "info"))
	if op == "set" and str(d.get("key", "")) in SAVE:
		_put(str(d["key"]), bool(d.get("value", true)), str(d["key"]) in ["u_lamps", "u_doors", "u_reflect"])
	elif op == "spawn":
		var v = main.spawn(str(d.get("kind", "e_trotti")))
		return {"ok": v != null, "info": info()}
	elif op == "snow_puff":
		_snow_puff()
	elif op == "clear_tracks":
		_clear_tracks()
	return {"ok": true, "info": info()}


# ---- the scene -----------------------------------------------------------------------------------------------------------------
func on_scene() -> void:
	"""after a scene was built (main._build_scene): the things of the switched-on parts"""
	for n in _placed:
		if is_instance_valid(n):
			n.queue_free()
	_placed.clear()
	_puddles.clear()
	_wisps.clear()
	for mv in _movers:
		if is_instance_valid(mv["n"]):
			mv["n"].queue_free()
	_movers.clear()
	_mosq = null
	_leaves = null
	_snowfall = null
	_tracks = null
	_track_n = 0
	_last_print.clear()
	if main.scenes == null or main.scenes.root == null or main.scene == "schlafzimmer":
		return
	var simple: bool = main.quality == "simple"
	if u_lamps:
		_place("motion_lamp", 16.0, 27.0)
		_place("window_tv", 19.0, -31.0)
	if u_doors:
		_place("garden_gate", 9.0, -21.0)
		_place("bin_lid", 7.0, 24.0)
	if u_reflect:
		for i in range(5):
			_puddle(_in_view(randf_range(5.0, 16.0), randf_range(-25.0, 25.0)), randf_range(0.5, 1.2))
	if u_smoke and not simple:
		for i in range(4):
			_wisp()
	if not simple:
		_mosq = _swarm()
		_leaves = _leaf_fall()
	_tracks_setup()


func _place(kind: String, dist: float, off: float) -> Node3D:
	"""a thing of the catalogue that this script puts there (not saved in the scene, no obstacle needed)"""
	var p: Vector3 = main.free_spot(_in_view(dist, off), 0.8, false)
	var n: Node3D = Obj.build(main, kind)
	n.position = Vector3(p.x, main.ground_y(p.x, p.z), p.z)
	n.rotation.y = atan2(_hp().x - p.x, _hp().z - p.z)
	main.scenes.root.add_child(n)
	if main.objplus != null:
		main.objplus.on_placed(n, kind)
	_placed.append(n)
	return n


func _hp() -> Vector3:
	return main.head.global_position if main.head != null and main.head.is_inside_tree() else Vector3(0, 1.6, 0)


func _in_view(dist: float, off_deg := 0.0) -> Vector3:
	var ok: bool = main.head != null and main.head.is_inside_tree() and main.cams.size() > 0
	var hp: Vector3 = main.head.global_position if ok else Vector3(0, 1.6, 0)    # before the device is built: from the origin
	var f: Vector3 = -main.cams[0].global_transform.basis.z if ok else Vector3(0, 0, -1)
	f.y = 0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	f = f.rotated(Vector3.UP, deg_to_rad(-off_deg))
	return Vector3(hp.x, 0, hp.z) + f * dist


func _puddle(p: Vector3, r: float) -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(r * 2.0, r * 1.4)
	mi.mesh = pm
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.12, 0.13, 0.15, 0.0)
	mt.metallic = 0.9
	mt.roughness = 0.04
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = mt
	mi.position = Vector3(p.x, main.ground_y(p.x, p.z) + 0.012, p.z)
	mi.rotation.y = randf() * TAU
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.layers = 1
	mi.visible = false
	main.scenes.root.add_child(mi)
	var th := MeshInstance3D.new()                        # water is cool in the thermal picture
	th.mesh = pm
	th.position = mi.position
	th.rotation = mi.rotation
	th.material_override = main.tmat_fixed(maxf(0.0, main.ambient - 3.0))
	th.layers = 2
	th.visible = false
	main.scenes.root.add_child(th)
	_puddles.append([mi, mt, mi.position, r, th])


func _wisp() -> void:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(randf_range(4.0, 8.0), randf_range(0.8, 1.6))
	mi.mesh = q
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.82, 0.84, 0.86, 0.0)
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	var g := Gradient.new()                               # soft edges
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	mt.albedo_texture = gt
	mi.material_override = mt
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var p := _in_view(randf_range(6.0, 22.0), randf_range(-30.0, 30.0))
	mi.position = Vector3(p.x, randf_range(0.4, 1.1), p.z)
	mi.visible = false
	main.scenes.root.add_child(mi)
	_wisps.append([mi, mt, randf() * TAU, p])


func _cpu(n_: int, life: float, col: Color, size: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = n_
	p.lifetime = life
	var sm := SphereMesh.new()
	sm.radius = size
	sm.height = size * 2.0
	sm.radial_segments = 4
	sm.rings = 2
	var mt := StandardMaterial3D.new()
	mt.albedo_color = col
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.material = mt
	p.mesh = sm
	p.emitting = false
	main.scenes.root.add_child(p)
	return p


func _swarm() -> CPUParticles3D:
	var p := _cpu(60, 2.5, Color(0.08, 0.08, 0.08), 0.006)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 0.5
	p.gravity = Vector3.ZERO
	p.direction = Vector3(0, 1, 0)
	p.spread = 180.0
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.7
	var c := _in_view(2.8, 6.0)
	p.position = Vector3(c.x, _hp().y - 0.2, c.z)
	return p


func _leaf_fall() -> CPUParticles3D:
	var p := _cpu(40, 6.0, Color(0.75, 0.42, 0.12), 0.035)
	p.mesh = QuadMesh.new()
	(p.mesh as QuadMesh).size = Vector2(0.07, 0.05)
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.72, 0.4, 0.12)
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	(p.mesh as QuadMesh).material = mt
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(9.0, 1.5, 6.0)
	p.gravity = Vector3(1.2, -0.9, 0.2)
	p.angular_velocity_min = -180.0
	p.angular_velocity_max = 180.0
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.8
	var c := _in_view(11.0)
	p.position = Vector3(c.x, 5.0, c.z)
	return p


func _snow_puff() -> void:
	"""a gust: snow falls from a branch (a short white cloud from 3-5 m height)"""
	if main.quality == "simple" or main.scenes.root == null:
		return
	var p := _cpu(50, 2.2, Color(0.95, 0.96, 1.0), 0.03)
	p.one_shot = true
	p.explosiveness = 0.8
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(0.8, 0.2, 0.8)
	p.gravity = Vector3(0.6, -3.5, 0)
	p.initial_velocity_min = 0.1
	p.initial_velocity_max = 0.5
	var c := _in_view(randf_range(7.0, 16.0), randf_range(-25.0, 25.0))
	p.position = Vector3(c.x, randf_range(3.0, 5.0), c.z)
	p.emitting = true
	stats["snow_puffs"] += 1
	get_tree().create_timer(3.5).timeout.connect(func():
		if is_instance_valid(p):
			p.queue_free())


func _tracks_setup() -> void:
	_tracks = MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var pm := PlaneMesh.new()
	pm.size = Vector2(0.11, 0.26)
	var mt := StandardMaterial3D.new()
	mt.vertex_color_use_as_albedo = true
	mt.roughness = 0.95
	pm.material = mt
	mm.mesh = pm
	mm.instance_count = TRACK_MAX
	mm.visible_instance_count = 0
	_tracks.multimesh = mm
	_tracks.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.scenes.root.add_child(_tracks)


func _clear_tracks() -> void:
	_track_n = 0
	if _tracks != null and is_instance_valid(_tracks):
		_tracks.multimesh.visible_instance_count = 0


func _print(p: Vector3, yaw: float, small: bool, col: Color) -> void:
	if _tracks == null or not is_instance_valid(_tracks):
		return
	var i := _track_n % TRACK_MAX
	var b := Basis(Vector3.UP, yaw)
	if small:
		b = b.scaled(Vector3(0.6, 1.0, 0.35))
	_tracks.multimesh.set_instance_transform(i, Transform3D(b, Vector3(p.x, main.ground_y(p.x, p.z) + 0.008, p.z)))
	_tracks.multimesh.set_instance_color(i, col)
	_track_n += 1
	_tracks.multimesh.visible_instance_count = mini(_track_n, TRACK_MAX)
	stats["prints"] += 1


# ---- every frame -------------------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or not main.sim_active or main.scenes == null:
		return
	var t: float = main.now()
	_move_robots(dt, t)
	for w in _wisps:                                       # fog wisps drift slowly with the wind
		var mi: MeshInstance3D = w[0]
		if is_instance_valid(mi) and mi.visible:
			w[2] = float(w[2]) + dt * 0.05
			var c: Vector3 = w[3]
			mi.position = Vector3(c.x + sin(float(w[2])) * 3.0 + main.wind * 0.02, mi.position.y, c.z + cos(float(w[2]) * 0.7) * 1.5)
	_slow -= dt
	if _slow > 0.0:
		return
	_slow = 0.25
	var dark: bool = main.is_dark()
	var simple: bool = main.quality == "simple"
	var col = main.colors
	var wet: float = float(col.puddle) if col != null else 0.0
	var snow_ground: bool = main.weather == "snow"
	# puddles: after (long) rain; they reflect the lamps and headlights
	for pd in _puddles:
		var on: bool = u_reflect and (wet > 0.12 or main.weather == "rain")
		(pd[0] as MeshInstance3D).visible = on and not snow_ground
		(pd[4] as MeshInstance3D).visible = on and not snow_ground
		(pd[1] as StandardMaterial3D).albedo_color.a = clampf(maxf(wet, 0.6 if main.weather == "rain" else 0.0) * 1.2, 0.0, 0.9)
	# fog wisps: calm, humid nights and mornings (or fog)
	var fogy: bool = u_smoke and (main.weather == "fog" or (main.humidity > 82.0 and main.wind < 15.0 and (dark or main.hour() < 9.0)))
	for w in _wisps:
		(w[0] as MeshInstance3D).visible = fogy
		(w[1] as StandardMaterial3D).albedo_color.a = 0.22 if main.weather != "fog" else 0.35
	if _mosq != null and is_instance_valid(_mosq):
		var h: float = main.hour()
		_mosq.emitting = u_insects and main.ambient > 10.0 and main.wind < 15.0 and main.weather in ["clear", "cloudy"] and (h > 19.0 or h < 5.0 or dark)
	var m_: int = col.month() if col != null else 6
	if _leaves != null and is_instance_valid(_leaves):
		_leaves.emitting = u_plants and m_ >= 9 and m_ <= 11 and main.wind * main.gust() > 12.0 and main.weather != "snow"
	if u_plants and snow_ground and not simple and main.gust() > 1.2 and t > _next_snow:
		_next_snow = t + randf_range(6.0, 18.0)
		_snow_puff()
	if _tracks != null and is_instance_valid(_tracks):
		_tracks.visible = u_tracks and (snow_ground or wet > 0.35)
	_feet(t, snow_ground, wet, m_)
	if u_vehicles and main.auto_visitors and not main.measuring() and main.busy_with() == "" and t > _next_veh:
		if _next_veh > 0.0 and main.visitors.get_child_count() < int(main.max_visitors):
			main.spawn(["e_trotti", "rollstuhl", "delivery_bot", "robomower", "e_trotti"][randi() % 5])
		_next_veh = t + randf_range(120.0, 300.0) / maxf(0.25, float(main.visit_rate))


func _feet(t: float, snow: bool, wet: float, month: int) -> void:
	"""footprints in the snow / mud, steps on gravel / leaves / snow for the microphone, splashes in the puddles"""
	var leaves: bool = (month >= 9 and month <= 11) or main.scene == "wald"
	var gravel: bool = main.scene in GRAVEL
	var mud: bool = wet > 0.35
	for v in main.visitors.get_children():
		if not v is Node3D or v.get("kind") == null or v.get("cur_speed") == null:
			continue
		var spd: float = v.cur_speed
		if spd < 0.2:
			continue
		var p: Vector3 = (v as Node3D).position
		var person: bool = v.kind == "person"
		var walking: bool = (person and not str(v.variant) in ["cyclist", "escooter", "wheelchair", "stroller"]) or (not person and v.kind != "car")
		if u_steps and walking and main.sound_on:
			var db := -100.0
			if snow:
				db = -36.0
			elif leaves:
				db = -32.0
			elif gravel:
				db = -30.0
			if db > -90.0:
				main.add_sound(db + (8.0 if spd > 2.2 else 0.0) - (10.0 if not person else 0.0), p, 0.4)
				stats["steps"] += 1
		if u_tracks and (snow or mud) and v.kind != "car":
			var id: int = v.get_instance_id()
			var lp = _last_print.get(id, null)
			var step: float = 0.65 if person else 0.35
			if lp == null or (lp[0] as Vector3).distance_to(p) > step:
				var side: float = 1.0 if lp == null or float(lp[1]) < 0.0 else -1.0
				var yaw: float = (v as Node3D).rotation.y
				var off := Vector3(cos(yaw), 0, -sin(yaw)) * (0.1 if person else 0.06) * side
				var c := Color(0.42, 0.46, 0.56) if snow else Color(0.2, 0.15, 0.1)
				if not walking:
					c = c.darkened(0.15)                          # wheel tracks
				_print(p + off, yaw, not person, c)
				_last_print[id] = [p, side]
		if u_reflect and not snow and (main.weather == "rain" or wet > 0.3):
			for pd in _puddles:
				if (pd[0] as MeshInstance3D).visible and Vector2(p.x - pd[2].x, p.z - pd[2].z).length() < float(pd[3]) * 0.8:
					if randf() < 0.5:
						_splash(p)
						main.add_sound(-36.0, p, 0.3)
					break


func _splash(p: Vector3) -> void:
	stats["splashes"] += 1
	if main.quality == "simple":
		return
	var s := _cpu(14, 0.5, Color(0.7, 0.75, 0.8), 0.015)
	s.one_shot = true
	s.explosiveness = 0.9
	s.direction = Vector3(0, 1, 0)
	s.spread = 45.0
	s.initial_velocity_min = 0.8
	s.initial_velocity_max = 1.6
	s.position = p + Vector3(0, 0.03, 0)
	s.emitting = true
	get_tree().create_timer(1.2).timeout.connect(func():
		if is_instance_valid(s):
			s.queue_free())


# ---- visitors: vehicles and pets ------------------------------------------------------------------------------------------------
func is_kind(k: String) -> bool:
	return KINDS.has(k)


func spawn_kind(kind: String, from, to) -> Node3D:
	"""main.spawn(kind) with one of KINDS"""
	var a: Vector3 = from if from != null else _in_view(14.0, -45.0)
	var b: Vector3 = to if to != null else _in_view(14.0, 45.0)
	match kind:
		"e_trotti":
			var v = main.spawn("escooter", a, b)
			v.speed = randf_range(4.5, 6.0)
			return v
		"rollstuhl":
			var v2 = main.spawn("wheelchair", a, b)
			v2.speed = randf_range(0.8, 1.2)
			return v2
		"delivery_bot", "robomower":
			return _robot(kind, a, b)
		"cat_fence":
			return _cat_fence()
		"hedgehog_bowl":
			var bowl := _place("food_bowl", 6.0, randf_range(-15.0, 15.0))
			var it = null
			for x in main.objplus.items:
				if x["n"] == bowl:
					it = x
			if it != null:
				var hv = main.objplus.send_lure(it, "hedgehog")
				return hv
			return null
		"chickens":
			_place("chicken_coop", 9.0, randf_range(-20.0, 20.0))
			return null
	return null


func _cat_fence() -> Node3D:
	"""a short garden fence in the picture, a cat jumps on it, sits, looks round and jumps down (like the cat on the car)"""
	var c := _in_view(7.5, randf_range(-15.0, 15.0))
	var f := Node3D.new()
	f.position = Vector3(c.x, main.ground_y(c.x, c.z), c.z)
	f.rotation.y = atan2(_hp().x - c.x, _hp().z - c.z) + PI / 2.0
	main.scenes.root.add_child(f)
	_placed.append(f)
	var wood: StandardMaterial3D = main.mat(Color(0.55, 0.42, 0.28))
	main.add_mesh(f, main.box(3.0, 0.08, 0.06), Vector3(0, 1.05, 0), wood, "stone")
	main.add_mesh(f, main.box(3.0, 0.08, 0.06), Vector3(0, 0.45, 0), wood, "stone")
	for i in range(7):
		main.add_mesh(f, main.box(0.09, 1.1, 0.03), Vector3(-1.35 + i * 0.45, 0.55, 0.05), wood, "stone")
	var top: Vector3 = f.global_transform * Vector3(0.3, 1.1, 0)
	var side: Vector3 = f.global_transform.basis.z.normalized()
	var start: Vector3 = top + side * 20.0
	var v = main.spawn("cat", Vector3(start.x, 0, start.z), Vector3(top.x, 0, top.z))
	if v == null:
		return null
	v.position = Vector3(top.x, 1.1, top.z)
	v.route = [[Vector3(top.x, 0, top.z), randf_range(20.0, 40.0), 0.0, _hp()], top - side * 25.0]
	v.target = Vector3(top.x, 0, top.z)
	v.next_idle = main.now() + 999.0
	if main.simreal != null:
		main.simreal._track.append({"v": v, "do": "roof", "y": 1.1, "up": false})   # sits up there, then jumps down
	return v


func _robot(kind: String, a: Vector3, b: Vector3) -> Node3D:
	"""a delivery robot drives across, a robot mower mows a patch in the picture - no persons (MoveEye must not push)"""
	if main.scenes.root == null:
		return null
	var n := Node3D.new()
	main.scenes.root.add_child(n)
	var wheels := []
	var mower: bool = kind == "robomower"
	if mower:
		main.add_mesh(n, main.box(0.55, 0.22, 0.7), Vector3(0, 0.16, 0), main.mat(Color(0.3, 0.35, 0.32)), 32.0)
		main.add_mesh(n, main.box(0.4, 0.04, 0.4), Vector3(0, 0.29, -0.05), main.mat(Color(0.85, 0.4, 0.1)), 30.0)
		for x in [-0.3, 0.3]:
			var w := Node3D.new()
			w.position = Vector3(x, 0.12, 0.2)
			n.add_child(w)
			var cm := CylinderMesh.new()
			cm.top_radius = 0.12
			cm.bottom_radius = 0.12
			cm.height = 0.06
			main.add_mesh(w, cm, Vector3.ZERO, main.mat(Color(0.08, 0.08, 0.08)), 30.0, Vector3(0, 0, PI / 2))
			wheels.append(w)
	else:
		main.add_mesh(n, main.box(0.6, 0.45, 0.75), Vector3(0, 0.42, 0), main.mat(Color(0.92, 0.92, 0.9)), 30.0)
		main.add_mesh(n, main.box(0.62, 0.08, 0.77), Vector3(0, 0.66, 0), main.mat(Color(0.15, 0.15, 0.17)), 28.0)
		main.add_mesh(n, main.box(0.3, 0.06, 0.02), Vector3(0, 0.5, -0.38), Scenes_glow(Color(0.4, 0.8, 1.0)), 30.0)
		var pole := CylinderMesh.new()
		pole.top_radius = 0.008
		pole.bottom_radius = 0.008
		pole.height = 1.0
		main.add_mesh(n, pole, Vector3(0.25, 1.15, 0.3), main.mat(Color(0.8, 0.8, 0.8)), "stone")
		main.add_mesh(n, main.box(0.02, 0.18, 0.25), Vector3(0.25, 1.55, 0.42), main.mat(Color(1.0, 0.45, 0.05)), "stone")
		for x in [-0.28, 0.28]:
			for z in [-0.28, 0.0, 0.28]:
				var w2 := Node3D.new()
				w2.position = Vector3(x, 0.1, z)
				n.add_child(w2)
				var cm2 := CylinderMesh.new()
				cm2.top_radius = 0.1
				cm2.bottom_radius = 0.1
				cm2.height = 0.06
				main.add_mesh(w2, cm2, Vector3.ZERO, main.mat(Color(0.1, 0.1, 0.1)), 30.0, Vector3(0, 0, PI / 2))
				wheels.append(w2)
	var path := []
	if mower:                                              # lanes over a patch of 6 × 4 m in the picture
		var c := _in_view(8.0, randf_range(-12.0, 12.0))
		for i in range(6):
			var z := c.z - 2.0 + i * 0.8
			path.append(Vector3(c.x - 3.0 if i % 2 == 0 else c.x + 3.0, 0, z))
			path.append(Vector3(c.x + 3.0 if i % 2 == 0 else c.x - 3.0, 0, z))
		path.append(c + Vector3(30, 0, 0))
	else:
		path = [b]
	n.position = Vector3(a.x, main.ground_y(a.x, a.z), a.z) if not mower else Vector3(path[0].x, 0, path[0].z)
	_movers.append({"n": n, "kind": kind, "path": path, "i": 0, "spd": 0.35 if mower else 1.6, "t_end": main.now() + 300.0, "wheels": wheels})
	stats["robots"] += 1
	main.start_info = "%s fährt durchs Bild (keine Person – MoveEye soll keinen Push senden)" % KINDS[kind][0].split(" (")[0]
	return n


func Scenes_glow(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = 1.5
	return m


func _move_robots(dt: float, t: float) -> void:
	for mv in _movers.duplicate():
		var n: Node3D = mv["n"]
		if not is_instance_valid(n) or t > float(mv["t_end"]) or int(mv["i"]) >= (mv["path"] as Array).size():
			if is_instance_valid(n):
				n.queue_free()
			_movers.erase(mv)
			continue
		var to: Vector3 = mv["path"][int(mv["i"])]
		var d := Vector3(to.x - n.position.x, 0, to.z - n.position.z)
		if d.length() < 0.1:
			mv["i"] = int(mv["i"]) + 1
			continue
		var st: Vector3 = d.normalized() * minf(d.length(), float(mv["spd"]) * dt)
		n.position += st
		n.position.y = main.ground_y(n.position.x, n.position.z)
		n.rotation.y = lerp_angle(n.rotation.y, atan2(-d.x, -d.z), minf(1.0, dt * 4.0))
		for w in mv["wheels"]:
			(w as Node3D).rotation.x -= float(mv["spd"]) * dt / 0.11
