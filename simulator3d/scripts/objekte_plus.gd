extends Node
## 3D-4.x «Gegenstände» (Wunsch Daniel, 30.10.2026): was die neuen Dinge des Katalogs (objekte_neu.gd) können.
##  - Wind (main.wind × Böen): Früchte fallen vom Obstbaum / Beerenstrauch, Hängematte schaukelt, Windspiel dreht, Ballon
##    tanzt an der Schnur, Tonnendeckel klappert, Gartentor schwingt, Plastiksack wird herumgetragen, Stoff flattert
##    (Fahne, Wäsche, Vorhang: flap.gdshader wie die Zeltplane von simreal.gd).
##  - Licht: Strassenlampe / Laterne / Solarleuchten nachts an (wie die Lampen der Szene), Lampe mit Bewegungsmelder geht an,
##    wenn jemand in die Nähe kommt, Fernseher flackert hinter dem Fenster, Kerze und Lagerfeuer flackern (Funken).
##  - Rauch und Dampf: Kugelgrill, Gaskocher (Schalter «Rauch und Dampf» in umgebung.gd).
##  - Wertsachen («steal»): stehen in main.test_props wie Velo und Kühlbox - also in «Bewachte Sachen» (Wegnehmen / Referenz-
##    Scan), im Spielziel «Diebstahl» (gameplus.gd) und im Prüfstand.
##  - Lockmittel («lure»): Fuchs, Wildschwein, Igel, Katze … kommen absichtlich hin, schnüffeln, wühlen und gehen wieder.
##  - Prüfstand-Plan «gegenstaende» (testrun.gd): stellt eine feste Auswahl vor die Kopfkamera (test_place / test_clear).
## Leicht: alles in einer Liste, nur was im Bild sein kann; bei Grafik «einfach» ohne kleine Lichter und ohne Funken.
## Einstellungen in user://objekte_plus.json.

var main
const Obj = preload("res://scripts/objects.gd")
const Neu = preload("res://scripts/objekte_neu.gd")
const FILE := "user://objekte_plus.json"
var lure_on := true                   # animals come to the lures by themselves (with «Besucher von selbst»)
var items: Array = []                 # [{n, k, d, fruits, piv, glow, light, ...}]
var _test_nodes: Array = []           # the things of the test run «gegenstaende»
var _next_lure := 0.0
var _lure_log: Array = []             # [{t, kind, lure, arrived}] (test bench)
var _slow := 0.0
var _seed := 0.0

# test bench «gegenstaende»: [kind, distance from the head (m), to the side (°)] - known (COCO) and unknown things, wind and light
const TEST_SET := [["flag", 11.0, -22.0], ["plastic_bag", 7.0, 8.0], ["balloon", 9.0, -8.0], ["laundry_line", 13.0, 18.0],
		["windchime", 6.5, -15.0], ["hammock", 12.0, 4.0], ["garden_gate", 8.5, 22.0], ["fruit_tree", 15.0, -12.0],
		["solar_lights", 6.0, 0.0], ["campfire", 10.0, 12.0], ["candle", 4.5, -4.0], ["motion_lamp", 16.0, 26.0],
		["trash_bag", 9.0, -18.0], ["food_bowl", 7.5, 14.0], ["parcel", 5.5, 20.0], ["camp_chair", 6.0, -26.0],
		["bin_lid", 10.0, -28.0], ["kettle_grill", 8.0, 28.0]]


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		lure_on = bool(d.get("lure_on", lure_on))
	_seed = randf() * 10.0


func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"lure_on": lure_on}))


func add_controls() -> void:
	var m = main
	m.add_control("toggle", "lure_on", "Tiere kommen absichtlich zu Futternapf, Abfallsack, offener Kühlbox und Obst (Gegenstände «Lockt Tiere an», mit «Besucher von selbst»)",
			func(): return lure_on, func(v): lure_on = bool(v); _save(), "Besuch", {"sub": "Verhalten"})
	m.add_control("button", "lure_now", "Tier zum Lockmittel schicken (zuerst Futternapf, Abfallsack … hinstellen)", null, func(): send_lure(), "Besuch", {"sub": "Tiere schicken"})


# ---- the tiles of the catalogue --------------------------------------------------------------------------------------------
func tile_how(kind: String) -> String:
	var d: Dictionary = Obj.def(kind)
	var o := ["steht"]
	if d.has("steal") or Neu.STEAL_OLD.has(kind):
		o.append("kann gestohlen werden")
	if d.has("wind") or _has_flap(d):
		o.append("bewegt sich im Wind")
	if d.has("lure"):
		o.append("lockt Tiere an")
	if str(d.get("fx", "")) in ["lamp", "lantern", "solar", "pir_lamp", "tv", "candle", "fire"]:
		o.append("leuchtet")
	elif str(d.get("fx", "")) in ["smoke", "steam"]:
		o.append("raucht / dampft")
	return " · ".join(o)


func _has_flap(d: Dictionary) -> bool:
	for p in d.get("p", []):
		if str(p[0]) == "f":
			return true
	return false


static func steal_kinds() -> Array:
	"""[kind, icon + name] of every valuable (wizard «Diebstahl»: was wird geklaut?)"""
	var out := []
	for k in Neu.STEAL_OLD:
		out.append([k, "%s %s" % [Neu.STEAL_OLD[k][0], Neu.STEAL_OLD[k][2]]])
	for k in Neu.OBJ:
		if Neu.OBJ[k].has("steal"):
			out.append([k, "%s %s" % [Neu.OBJ[k]["steal"][0], Neu.OBJ[k]["steal"][2]]])
	return out


static func steal_def(kind: String) -> Array:
	if Neu.STEAL_OLD.has(kind):
		return Neu.STEAL_OLD[kind]
	return Neu.OBJ.get(kind, {}).get("steal", [])


# ---- placed -------------------------------------------------------------------------------------------------------------
func on_placed(n: Node3D, kind: String) -> void:
	"""inventar.add_object (and the test bench): give the thing its wind, light, smoke, lure and theft"""
	var d: Dictionary = Obj.def(kind)
	var it := {"n": n, "k": kind, "d": d, "fruits": [], "piv": {}, "glow": [], "seed": randf() * 10.0, "on_until": 0.0, "fallen": 0}
	var simple: bool = main.quality == "simple"
	for c in _all(n):
		if c.has_meta("flap"):
			main.cloth_mats.append(c.get_meta("flap"))     # main.gd gives it the wind with the gusts
			c.add_to_group("cloth")
			c.visible = main.world_cloth
		if c.has_meta("glow"):
			it["glow"].append(c.get_meta("glow"))
		if c.has_meta("role"):
			if str(c.get_meta("role")) == "fruit":
				it["fruits"].append(c)
			else:
				it["piv"][str(c.get_meta("role"))] = c
	var fx := str(d.get("fx", ""))
	var top: Vector3 = _top(n)
	match fx:
		"lamp":                                          # like the lamps of the scene: on at night (main.gd)
			for g in it["glow"]:
				main.lamp_mats.append(g)
			var l := OmniLight3D.new()
			l.position = Vector3(0.8, 4.2, 0)
			l.light_color = Color(1.0, 0.82, 0.55)
			l.omni_range = 12.0
			l.light_energy = 0.0
			n.add_child(l)
			main.lamps.append(l)
		"lantern", "solar":
			for g in it["glow"]:
				main.lamp_mats.append(g)
			if fx == "lantern" and not simple:
				var l2 := OmniLight3D.new()
				l2.position = Vector3(0, 0.15, 0)
				l2.light_color = Color(1.0, 0.8, 0.5)
				l2.omni_range = 4.0
				l2.light_energy = 0.0
				n.add_child(l2)
				it["light"] = l2
		"pir_lamp":
			var sp := SpotLight3D.new()
			sp.position = Vector3(0.5, 2.05, 0.3)
			sp.rotation = Vector3(deg_to_rad(-55), 0, 0)
			sp.spot_range = 11.0
			sp.spot_angle = 55.0
			sp.light_color = Color(1.0, 0.95, 0.85)
			sp.light_energy = 0.0
			n.add_child(sp)
			it["light"] = sp
			_glow(it, 0.0)
		"tv":
			if not simple:
				var tl := OmniLight3D.new()
				tl.position = Vector3(0, 1.45, 0.6)
				tl.light_color = Color(0.55, 0.65, 1.0)
				tl.omni_range = 3.5
				tl.light_energy = 0.0
				n.add_child(tl)
				it["light"] = tl
			_glow(it, 0.0)
		"candle", "fire":
			if fx == "fire" or not simple:
				var fl := OmniLight3D.new()
				fl.position = Vector3(0, 0.35 if fx == "candle" else 0.6, 0)
				fl.light_color = Color(1.0, 0.6, 0.25)
				fl.omni_range = 2.5 if fx == "candle" else 9.0
				fl.light_energy = 0.0
				n.add_child(fl)
				it["light"] = fl
			if fx == "fire" and not simple:
				it["sparks"] = _particles(n, Vector3(0, 0.5, 0), "sparks")
		"smoke":
			it["smoke"] = _particles(n, top + Vector3(0, 0.05, 0), "smoke")
		"steam":
			if not simple:
				it["smoke"] = _particles(n, Vector3(0.12, 0.26, 0), "steam")
		"bees":
			if not simple:
				it["smoke"] = _particles(n, Vector3(0, 0.5, 0.35), "bees")
		"chickens":
			it["chickens"] = _chickens(n)
	if d.has("steal") or Neu.STEAL_OLD.has(kind):
		_register_steal(n, kind)
	items.append(it)


func _all(n: Node) -> Array:
	var out := []
	for c in n.get_children():
		out.append(c)
		out += _all(c)
	return out


func _top(n: Node3D) -> Vector3:
	var hi := 0.3
	for c in n.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).layers == 1:
			var a: AABB = (c as MeshInstance3D).transform * (c as MeshInstance3D).mesh.get_aabb()
			hi = maxf(hi, a.end.y)
	return Vector3(0, hi, 0)


func _glow(it: Dictionary, e: float) -> void:
	for g in it["glow"]:
		(g as StandardMaterial3D).emission_energy_multiplier = e


func _particles(n: Node3D, at: Vector3, what: String) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.position = at
	var sm := SphereMesh.new()
	sm.radial_segments = 6
	sm.rings = 3
	var mt := StandardMaterial3D.new()
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	match what:
		"smoke", "steam":
			p.amount = 10 if main.quality == "simple" else 24
			p.lifetime = 4.5 if what == "smoke" else 2.0
			p.direction = Vector3(0, 1, 0)
			p.spread = 14.0
			p.initial_velocity_min = 0.3
			p.initial_velocity_max = 0.6
			var c := Curve.new()
			c.add_point(Vector2(0, 0.3))
			c.add_point(Vector2(1, 1.8))
			p.scale_amount_curve = c
			sm.radius = 0.18 if what == "smoke" else 0.08
			sm.height = sm.radius * 2.0
			mt.albedo_color = Color(0.55, 0.55, 0.57, 0.4) if what == "smoke" else Color(0.95, 0.95, 0.97, 0.35)
			p.add_to_group("smoke")
		"sparks":
			p.amount = 16
			p.lifetime = 1.6
			p.direction = Vector3(0, 1, 0)
			p.spread = 25.0
			p.initial_velocity_min = 1.0
			p.initial_velocity_max = 2.4
			sm.radius = 0.012
			sm.height = 0.024
			mt.albedo_color = Color(1.0, 0.75, 0.3)
			mt.emission_enabled = true
			mt.emission = Color(1.0, 0.6, 0.2)
			mt.emission_energy_multiplier = 4.0
			p.add_to_group("smoke")
		"bees":
			p.amount = 12
			p.lifetime = 3.0
			p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
			p.emission_sphere_radius = 0.6
			p.direction = Vector3(1, 0.2, 0)
			p.spread = 180.0
			p.gravity = Vector3.ZERO
			p.initial_velocity_min = 0.4
			p.initial_velocity_max = 1.0
			sm.radius = 0.01
			sm.height = 0.02
			mt.albedo_color = Color(0.2, 0.15, 0.05)
	sm.material = mt
	p.mesh = sm
	p.emitting = true
	n.add_child(p)
	return p


func _register_steal(n: Node3D, kind: String) -> void:
	"""the valuable joins main.test_props: «Bewachte Sachen» (take away / reference scan), theft game, test bench"""
	var sd := steal_def(kind)
	var base := str(sd[2]) if sd.size() > 2 else kind
	var nm := base
	var i := 2
	while main.test_props.has(nm) and is_instance_valid(main.test_props[nm]) and main.test_props[nm] != n:
		nm = "%s %d" % [base, i]
		i += 1
	n.set_meta("steal_kind", kind)
	main.test_props[nm] = n


func steal_info(nm: String) -> Array:
	"""[icon, with article, short, speed] of a valuable in main.test_props (gameplus.gd), [] when it is none of them"""
	var n = main.test_props.get(nm, null)
	if n == null or not is_instance_valid(n) or not n.has_meta("steal_kind"):
		return []
	var sd := steal_def(str(n.get_meta("steal_kind")))
	if sd.is_empty():
		return []
	return [sd[0], sd[1], nm, sd[3]]


func valuables_here() -> Array:
	"""the names (main.test_props) of the valuables of the catalogue in this scene, that are there"""
	var out := []
	for nm in main.test_props:
		var n = main.test_props[nm]
		if n != null and is_instance_valid(n) and n.has_meta("steal_kind") and n.visible:
			out.append(nm)
	return out


func ensure_valuable(kind: String) -> String:
	"""the theft game wants this valuable but it is not in the scene: put one beside your tent (or in front of the camera)"""
	for nm in main.test_props:
		var n = main.test_props[nm]
		if n != null and is_instance_valid(n) and str(n.get_meta("steal_kind", "")) == kind:
			return nm
	if steal_def(kind).is_empty() or main.inventar == null:
		return ""
	var tent = main.obj.get("pir", null)
	var p: Vector3 = (tent + Vector3(1.3, 0, 1.1)) if tent is Vector3 and tent != Vector3.ZERO else _in_view(7.0, 10.0)
	p = main.free_spot(p, 0.5, false)
	main.inventar.add_object(kind, Vector3(p.x, 0, p.z), randf_range(0.0, 360.0), false)
	for nm in main.test_props:
		var n = main.test_props[nm]
		if n != null and is_instance_valid(n) and str(n.get_meta("steal_kind", "")) == kind:
			return nm
	return ""


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


# ---- every frame ------------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or not main.sim_active or items.is_empty() and _test_nodes.is_empty():
		return
	var t: float = main.now()
	var w: float = main.wind * main.gust()
	var dark: bool = main.is_dark()
	var smoke_ok: bool = main.world_smoke and (main.umgebung == null or main.umgebung.u_smoke)
	_slow -= dt
	var slow := _slow <= 0.0
	if slow:
		_slow = 0.25
	for it in items.duplicate():
		var n = it["n"]
		if n == null or not is_instance_valid(n) or not n.is_inside_tree():
			items.erase(it)
			continue
		if not n.visible:
			continue
		var d: Dictionary = it["d"]
		var sd: float = it["seed"]
		match str(d.get("wind", "")):
			"fall":
				_fruit_fall(it, w, dt)
			"swing":
				var pv: Node3D = it["piv"].get("swing")
				if pv != null:
					var amp := 0.03 + 0.32 * clampf(w / 50.0, 0.0, 1.0)
					pv.rotation.x = sin(t * 1.3 + sd) * amp
			"spin":
				var ps: Node3D = it["piv"].get("spin")
				if ps != null:
					ps.rotation.y += dt * (0.15 + w * 0.03)
					ps.rotation.z = sin(t * 2.3 + sd) * clampf(w / 60.0, 0.02, 0.35)
			"bob":
				var pb: Node3D = it["piv"].get("bob")
				if pb != null:
					var a2 := clampf(w / 40.0, 0.04, 0.55)
					pb.rotation.z = sin(t * 0.9 + sd) * a2
					pb.rotation.x = cos(t * 1.27 + sd) * a2 * 0.6
			"lid":
				var pl: Node3D = it["piv"].get("lid")
				if pl != null:
					var op := clampf((w - 18.0) / 35.0, 0.0, 1.0)
					pl.rotation.x = -op * (0.12 + 0.45 * absf(sin(t * 3.1 + sd)) * absf(sin(t * 0.7)))
			"gate":
				var pg: Node3D = it["piv"].get("gate")
				if pg != null:
					var ag := clampf(w / 45.0, 0.0, 1.0)
					pg.rotation.y = (sin(t * 0.55 + sd) * 0.55 + 0.15 * sin(t * 2.1)) * ag
			"drift":
				_drift(it, w, dt, t)
		var fx := str(d.get("fx", ""))
		match fx:
			"candle", "fire":
				var pf: Node3D = it["piv"].get("flame")
				var fk := 0.75 + 0.25 * sin(t * 13.0 + sd) * sin(t * 7.3) + randf_range(-0.08, 0.08)
				if pf != null:
					pf.scale = Vector3(1.0 + 0.1 * (fk - 0.75), fk * 1.15, 1.0 + 0.1 * (fk - 0.75))
				var l = it.get("light")
				if l != null:
					l.light_energy = (1.6 if fx == "fire" else 0.5) * fk * (1.0 if dark else 0.25)
				if it.has("sparks"):
					it["sparks"].emitting = smoke_ok
			"lantern":
				if it.get("light") != null:
					it["light"].light_energy = 0.9 if dark else 0.0
			"pir_lamp":
				if slow:
					if dark and _someone_near((n as Node3D).global_position, 8.0):
						it["on_until"] = t + 45.0                 # on for 45 s after the last movement
					var on: bool = dark and t < float(it["on_until"])
					it["light"].light_energy = 3.0 if on else 0.0
					_glow(it, 4.0 if on else 0.0)
			"tv":
				var h: float = main.hour()
				var on2: bool = dark and (h >= 18.5 or h < 0.7)
				if on2 and randf() < dt * 6.0:                    # a new scene on the screen
					var c := Color(randf_range(0.3, 1.0), randf_range(0.4, 1.0), randf_range(0.6, 1.0))
					for g in it["glow"]:
						(g as StandardMaterial3D).emission = c
					it["tv_e"] = randf_range(1.0, 3.5)
				_glow(it, float(it.get("tv_e", 2.0)) if on2 else 0.0)
				if it.get("light") != null:
					it["light"].light_energy = float(it.get("tv_e", 2.0)) * 0.35 if on2 else 0.0
			"smoke", "steam", "bees":
				if it.has("smoke"):
					it["smoke"].emitting = smoke_ok if fx != "bees" else (not dark and main.weather != "rain")
					if fx == "smoke":
						it["smoke"].gravity = Vector3(0.15 + w * 0.025, 0.08, 0)
			"chickens":
				_chicken_tick(it, dt, t, dark)
	if slow:
		_lure_tick(t, dark)


func _fruit_fall(it: Dictionary, w: float, dt: float) -> void:
	"""in the wind now and then a fruit falls (stronger wind = more); it stays on the ground (and lures animals then)"""
	if w < 22.0:
		return
	for f in it["fruits"]:
		if not is_instance_valid(f) or f.has_meta("down"):
			continue
		if randf() < dt * (w - 22.0) / 900.0:
			f.set_meta("down", true)
			it["fallen"] = int(it["fallen"]) + 1
			var to := Vector3(f.position.x * 1.2 + randf_range(-0.3, 0.3), 0.04, f.position.z * 1.2 + randf_range(-0.3, 0.3))
			var tw := (f as Node3D).create_tween()
			tw.tween_property(f, "position", to, sqrt(2.0 * maxf(0.1, f.position.y) / 9.81)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
			tw.tween_property(f, "position:y", 0.12, 0.12).set_ease(Tween.EASE_OUT)      # a small bounce
			tw.tween_property(f, "position:y", 0.04, 0.12).set_ease(Tween.EASE_IN)
			if int(it["fallen"]) == 3 and not it["d"].has("lure"):
				it["lure2"] = ["deer", "boar", "hedgehog", "fox"]      # fruit on the ground: animals come
			return


func _drift(it: Dictionary, w: float, dt: float, t: float) -> void:
	"""a plastic bag: the wind carries it over the ground, now and then it lifts - stays within 8 m of its place"""
	var pv: Node3D = it["piv"].get("bag")
	if pv == null:
		return
	var spd := clampf((w - 8.0) / 18.0, 0.0, 2.2)
	var wd := Vector3(1, 0, 0.25).normalized()
	var p: Vector3 = pv.position + wd * spd * dt * (0.6 + 0.4 * sin(t * 1.7 + float(it["seed"])))
	if Vector2(p.x, p.z).length() > 8.0:
		p = -wd * 7.5                                      # blown away: the next one comes from the other side
	p.y = absf(sin(t * 2.2 + float(it["seed"]))) * 0.35 * spd
	pv.position = p
	pv.rotation.y += dt * spd * 2.0
	pv.rotation.z = sin(t * 3.0) * 0.4 * spd


func _someone_near(p: Vector3, r: float) -> bool:
	for v in main.visitors.get_children():
		if v is Node3D and (v as Node3D).global_position.distance_to(p) < r:
			return true
	if main.game != null:
		for pl in main.game.players:
			if pl != null and pl["actor"] != null and is_instance_valid(pl["actor"]) and pl["actor"].visible and (pl["actor"] as Node3D).global_position.distance_to(p) < r:
				return true
	return false


# ---- chickens at the coop -------------------------------------------------------------------------------------------------
func _chickens(n: Node3D) -> Array:
	var out := []
	for i in range(3):
		var c := Node3D.new()
		c.position = Vector3(randf_range(-1.5, 1.5), 0, randf_range(0.9, 2.2))
		n.add_child(c)
		var col: Color = [Color(0.95, 0.93, 0.88), Color(0.55, 0.3, 0.15), Color(0.2, 0.18, 0.15)][i % 3]
		var body := SphereMesh.new()
		body.radius = 0.13
		body.height = 0.22
		main.add_mesh(c, body, Vector3(0, 0.2, 0), main.mat(col), 39.0, Vector3.ZERO, Vector3(0.8, 1.0, 1.3))
		var hd := Node3D.new()
		hd.position = Vector3(0, 0.33, 0.12)
		c.add_child(hd)
		var hm := SphereMesh.new()
		hm.radius = 0.055
		hm.height = 0.11
		main.add_mesh(hd, hm, Vector3.ZERO, main.mat(col), 40.0)
		main.add_mesh(hd, main.box(0.02, 0.05, 0.04), Vector3(0, 0.05, 0), main.mat(Color(0.8, 0.1, 0.1)), 38.0)
		var bk := CylinderMesh.new()
		bk.top_radius = 0.0
		bk.bottom_radius = 0.015
		bk.height = 0.04
		main.add_mesh(hd, bk, Vector3(0, 0, 0.06), main.mat(Color(0.9, 0.7, 0.2)), 35.0, Vector3(PI / 2, 0, 0))
		for s in [-1, 1]:
			main.add_mesh(c, main.box(0.015, 0.12, 0.015), Vector3(0.04 * s, 0.06, 0), main.mat(Color(0.9, 0.7, 0.2)), 34.0)
		out.append({"n": c, "hd": hd, "to": c.position, "peck": 0.0})
	return out


func _chicken_tick(it: Dictionary, dt: float, t: float, dark: bool) -> void:
	for ch in it.get("chickens", []):
		var c: Node3D = ch["n"]
		if not is_instance_valid(c):
			continue
		c.visible = not dark                                   # at night they are in the coop
		if dark:
			continue
		var to: Vector3 = ch["to"]
		var dd: Vector3 = to - c.position
		if dd.length() < 0.08:
			if randf() < dt * 0.4:
				ch["to"] = Vector3(randf_range(-2.0, 2.0), 0, randf_range(0.8, 2.6))
			ch["peck"] = float(ch["peck"]) + dt
			(ch["hd"] as Node3D).position.y = 0.33 - 0.14 * maxf(0.0, sin(float(ch["peck"]) * 9.0))   # pecking
		else:
			var st := dd.normalized() * minf(dd.length(), dt * 0.45)
			c.position += st
			c.rotation.y = atan2(st.x, st.z)
			(ch["hd"] as Node3D).position.y = 0.33 + 0.02 * sin(t * 14.0)


# ---- lures: animals come on purpose -----------------------------------------------------------------------------------------
func _lures() -> Array:
	var out := []
	for it in items:
		if is_instance_valid(it["n"]) and (it["n"] as Node3D).visible and (it["d"].has("lure") or it.has("lure2")):
			out.append(it)
	return out


func _lure_tick(t: float, dark: bool) -> void:
	if not lure_on or not main.auto_visitors or main.measuring() or main.busy_with() != "":
		return
	if _next_lure == 0.0:
		_next_lure = t + randf_range(25.0, 60.0)
	if t < _next_lure:
		return
	_next_lure = t + randf_range(80.0, 180.0) / maxf(0.25, float(main.visit_rate))
	if not _lures().is_empty() and main.visitors.get_child_count() < int(main.max_visitors):
		send_lure()


func send_lure(it = null, only := "") -> Node3D:
	"""an animal that likes this lure comes, sniffs / roots there for a while and goes again (night animals at night)"""
	var ls := _lures()
	if ls.is_empty():
		main.start_info = "Zuerst etwas aus «Lockt Tiere an» hinstellen (Futternapf, Abfallsack, offene Kühlbox, Obst)."
		return null
	if it == null:
		it = ls[randi() % ls.size()]
	var want: Array = it["d"].get("lure", it.get("lure2", ["fox"]))
	var dark: bool = main.is_dark()
	var day_ok := ["cat", "squirrel", "deer", "hedgehog", "dog"] if not dark else want
	var pick: Array = want.filter(func(k): return k in day_ok)
	if pick.is_empty():
		pick = want
	var kind: String = pick[randi() % pick.size()] if only == "" else only
	var c: Vector3 = (it["n"] as Node3D).global_position
	var ang := randf() * TAU
	var far: float = {"hedgehog": 9.0, "badger": 14.0, "cat": 16.0, "squirrel": 14.0}.get(kind, 24.0)   # slow ones start nearer
	var start := c + Vector3(cos(ang), 0, sin(ang)) * far
	var at: Vector3 = main.free_spot(c + Vector3(cos(ang), 0, sin(ang)) * 0.7, 0.3, false)
	var away := c + Vector3(cos(ang + 2.2), 0, sin(ang + 2.2)) * (far + 10.0)
	var v = main.spawn(kind, start, at)
	if v == null:
		return null
	var wait := randf_range(14.0, 30.0)
	v.route = [[at, wait, 0.0, c], away]
	var rec := {"t": t_now(), "kind": kind, "lure": str(it["k"]), "arrived": false}
	_lure_log.append(rec)
	if _lure_log.size() > 60:
		_lure_log.pop_front()
	var hold := {"v": v, "t0": main.now()}
	main.anims.append(func(_dt, _t):                         # when it is there: sniff / root (like the fox at the bin)
		var a = hold["v"]
		if a == null or not is_instance_valid(a) or a.done or main.now() - float(hold["t0"]) > 240.0:
			return true
		if a.position.distance_to(at) < 0.7:
			a.idle_kind = "root" if a.kind in ["boar", "badger", "fox"] else "sniff"
			a.idle_until = a.now_s() + wait * 0.8
			rec["arrived"] = true
			return true
		return false)
	main.start_info = "%s kommt zu: %s" % [kind, str(it["d"]["n"])]
	return v


func t_now() -> float:
	return main.now()


# ---- test bench «gegenstaende» ---------------------------------------------------------------------------------------------------
func test_place(set_ := TEST_SET) -> Array:
	"""the fixed set in front of the head camera (not saved, no obstacles) -> [{k, n, coco}]"""
	test_clear()
	var out := []
	for e in set_:
		var kind := str(e[0])
		var d: Dictionary = Obj.def(kind)
		if d.is_empty():
			continue
		var p: Vector3 = main.free_spot(_in_view(float(e[1]), float(e[2])), 0.4, false)
		var n: Node3D = Obj.build(main, kind)
		n.position = Vector3(p.x, main.ground_y(p.x, p.z), p.z)
		n.rotation.y = atan2(_hp().x - p.x, _hp().z - p.z)   # facing the camera
		main.scene_parent.add_child(n)
		on_placed(n, kind)
		_test_nodes.append(n)
		out.append({"k": kind, "n": str(d["n"]), "coco": str(d["coco"]), "ki_kennt": str(d["coco"]) != ""})
	_lure_log.clear()
	return out


func test_clear() -> void:
	for n in _test_nodes:
		if is_instance_valid(n):
			for nm in main.test_props.keys():
				if main.test_props[nm] == n:
					main.test_props.erase(nm)
			n.queue_free()
	_test_nodes.clear()


func lure_visit() -> Node3D:
	"""testrun.gd visit «lure»: an animal goes to one of the lures of the test set"""
	return send_lure()


func report_extra(tr) -> Dictionary:
	"""the numbers of the plan «gegenstaende»: the things, the animals at the lures, false pushes (things / wind / light)"""
	var known := 0
	var things := []
	for n in _test_nodes:
		if not is_instance_valid(n):
			continue
		var k: String = str(n.name).trim_prefix("obj_")
		var d: Dictionary = Obj.def(k)
		things.append({"k": k, "coco": str(d.get("coco", ""))})
		if str(d.get("coco", "")) != "":
			known += 1
	var lu := 0
	var la := 0
	for r in _lure_log:
		if float(r["t"]) >= float(tr.t0):
			lu += 1
			if bool(r["arrived"]):
				la += 1
	var pa: Dictionary = tr.push_numbers(-1)
	return {"art": "gegenstaende", "dinge": things.size(), "ki_kennt": known, "ki_kennt_nicht": things.size() - known, "liste": things,
			"lockmittel_tiere": lu, "lockmittel_angekommen": la, "push_falsch": int(pa.get("false", 0)), "push_richtig": int(pa.get("ok", 0))}


# ---- control / info ----------------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var by := {}
	for it in items:
		if is_instance_valid(it["n"]):
			by[str(it["k"])] = int(by.get(str(it["k"]), 0)) + 1
	var fallen := 0
	for it in items:
		fallen += int(it.get("fallen", 0))
	return {"items": by, "lure_on": lure_on, "lures": _lures().size(), "valuables": valuables_here(), "fruit_fallen": fallen,
			"lure_log": _lure_log.slice(-8), "test": _test_nodes.size(), "kinds": Obj.kinds().size(), "new": Neu.OBJ.size()}


func control(d: Dictionary) -> Dictionary:
	"""{do: info | lure | test_place | test_clear | set (key, value)}"""
	var op := str(d.get("do", "info"))
	if op == "lure":
		var v = send_lure()
		return {"ok": v != null, "kind": v.kind if v != null else "", "info": info()}
	elif op == "test_place":
		return {"ok": true, "things": test_place()}
	elif op == "dump":                                   # tests: where every thing is, and its moving / flapping parts
		var out := []
		for it in items:
			var n = it["n"]
			if not is_instance_valid(n):
				continue
			var fl := []
			for c in _all(n):
				if c.has_meta("flap"):
					fl.append([snappedf(c.global_position.x, 0.01), snappedf(c.global_position.y, 0.01), snappedf(c.global_position.z, 0.01), c.is_visible_in_tree()])
			out.append({"k": it["k"], "p": [snappedf(n.global_position.x, 0.1), snappedf(n.global_position.z, 0.1)], "vis": n.is_visible_in_tree(), "flaps": fl})
		return {"ok": true, "items": out}
	elif op == "test_clear":
		test_clear()
	elif op == "set" and str(d.get("key", "")) == "lure_on":
		lure_on = bool(d.get("value", true))
		_save()
	return {"ok": true, "info": info()}
