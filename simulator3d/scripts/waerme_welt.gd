extends Node
## Wärme in der Welt (Paket P3 «Wärme-Signatur», 31.10.2026): was sich mit der Zeit ändert und die Werte aus waerme.gd braucht.
##   - Autos: der Motor kühlt nach der Fahrt ab (Motorhaube, Kühlergrill, Auspuff: Newton-Abkühlung, waerme.gd ENGINE).
##     Fahrende Autos, Traktoren und Motorräder (actor.gd) haben einen heissen Motor; bleiben sie stehen, kühlt er ab.
##     Geparkte Autos der Szene: ein Teil ist «eben angekommen» (warmer Motor), die anderen stehen schon lange.
##     Ihr Dach wird in der Sonne heiss und ist in klaren Nächten kälter als die Luft (Material «car», simreal.temps).
##   - Zelt: nachts schläft jemand im eigenen Zelt – ein schwacher warmer Fleck an der Zeltwand (Schalter in «Wärmebild»).
##   - Lampen: der Kopf der Strassenlampen ist nur warm, wenn sie brennt (Material «lamp»).
## Wird von main._update_temps zweimal pro Sekunde aufgerufen (tick) und nach jedem Szenenaufbau (on_scene).
## Nur mit «Wärmebild wie echt» (simreal.th_real); sonst bleiben die alten festen Werte.

const Waerme = preload("res://scripts/waerme.gd")

var main
var _cars: Array = []          # [{node, mats: [[ShaderMaterial, part]], min: Minuten seit der Fahrt, pos, actor}]
var _seen := {}                # actor instance id -> true (schon angeschaut)
var _tent: Array = []          # ShaderMaterial der warmen Flecken am Zelt
var _last := 0.0


func _thmat(t: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/thermal.gdshader")
	m.set_shader_parameter("temp", t)
	m.set_shader_parameter("spread", 0.5)
	return main.th_reg(m)


func _patch(parent: Node3D, size: Vector3, pos: Vector3, mat: ShaderMaterial, rot := Vector3.ZERO) -> MeshInstance3D:
	"""a thin part only the thermal camera sees (a warm area on a surface)"""
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.position = pos
	mi.rotation = rot
	mi.material_override = mat
	mi.layers = 2
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func on_scene() -> void:
	_cars = _cars.filter(func(c): return c.has("actor") and is_instance_valid(c["actor"]))
	_tent.clear()
	if not _real():
		return
	var amb: float = main.ambient
	# parked cars (simreal noted them while the scene was built): roof material «car», a hood that can be warm
	if main.simreal != null:
		var cav: Material = main.tmat("caravan")
		for c in main.simreal._cars:
			if not is_instance_valid(c):
				continue
			for ch in c.get_children():
				if ch is MeshInstance3D and ch.layers == 2 and ch.material_override == cav:
					ch.material_override = main.tmat("car")
			var mins := randf_range(300.0, 900.0)
			if randf() < 0.3:
				mins = randf_range(3.0, 45.0)                       # came a little while ago
			var hood := _thmat(amb)
			var grille := _thmat(amb)
			_patch(c, Vector3(1.66, 0.02, 1.2), Vector3(0, 0.915, -1.45), hood)          # bonnet (top of the body box at 0.9)
			_patch(c, Vector3(1.6, 0.36, 0.02), Vector3(0, 0.62, -2.115), grille)       # front / grille
			_cars.append({"node": c, "mats": [[hood, "hood"], [grille, "grille"]], "min": mins})
	# the own tent: a person in a sleeping bag lies along one side (warm patch on both slanted walls of the flysheet)
	var tn = main.test_props.get("Zelt", null)
	if tn is Node3D and is_instance_valid(tn):
		var m := _thmat(amb)
		var h := 0.38
		for s in [-1.0, 1.0]:
			var x := 1.45 * (1.0 - h / 1.58) + 0.02
			_patch(tn, Vector3(0.012, 0.5, 1.5), Vector3(s * x, h, 0.0), m, Vector3(0, 0, s * atan2(1.45, 1.58)))
		_tent.append(m)


func car_arrived() -> String:
	"""button «Geparktes Auto: Motor warm»: the parked car nearest to the camera has just arrived"""
	var best = null
	var bd := 1e9
	var f: Vector3 = -main.head.global_transform.basis.z
	f.y = 0.0
	for c in _cars:
		if c.has("actor") or not is_instance_valid(c["node"]):
			continue
		var to: Vector3 = (c["node"] as Node3D).global_position - main.head.global_position
		to.y = 0.0
		var d: float = to.length()
		var score := d + (0.0 if f.normalized().dot(to.normalized()) > 0.7 else 1000.0)   # in front of the thermal camera first
		if score < bd:
			bd = score
			best = c
	bd = fmod(bd, 1000.0)
	if best == null:
		return "Wärmebild: kein geparktes Auto in dieser Szene (oder «Wärmebild wie echt» aus)"
	best["min"] = 0.0
	tick(true)
	return "Wärmebild: Auto in %d m ist eben angekommen – Motor warm, kühlt in 1–2 h ab" % int(bd)


var _glass: Node3D = null


func glass_pane() -> String:
	"""button «Glasscheibe vor MoveEye»: a 2 × 2 m glass wall 4 m in front of the head (on / off) - the camera sees through it,
	the thermal camera does not (glass and acrylic are opaque for 8–14 µm: it shows the glass itself, a little of the
	reflected sky). Test: a person behind a window, in a caravan or behind a glass door is invisible in the thermal picture."""
	if _glass != null and is_instance_valid(_glass):
		_glass.queue_free()
		_glass = null
		return "Glasscheibe weg"
	var f: Vector3 = -main.head.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var p: Vector3 = main.head.global_position + f * 4.0
	p.y = 0.0
	_glass = Node3D.new()
	main.scenes.root.add_child(_glass)
	_glass.global_position = p
	_glass.rotation.y = atan2(-f.x, -f.z)
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.75, 0.85, 0.9, 0.18)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.roughness = 0.05
	m.metallic_specular = 0.9
	main.add_mesh(_glass, main.box(2.0, 2.0, 0.02), Vector3(0, 1.1, 0), m, "glass")
	main.add_mesh(_glass, main.box(2.08, 0.06, 0.06), Vector3(0, 0.08, 0), main.mat(Color(0.3, 0.3, 0.32)), "stone")    # frame
	main.add_mesh(_glass, main.box(2.08, 0.06, 0.06), Vector3(0, 2.12, 0), main.mat(Color(0.3, 0.3, 0.32)), "stone")
	# a person comes from the side, stands 30 s right behind the glass (1.5 m), then goes on
	var r := Vector3(-f.z, 0, f.x)
	var mid: Vector3 = p + f * 1.5
	var v = main.spawn("person", mid - r * 4.0, mid)
	if v != null:
		v.route = [[mid, 30.0, 0.0, Vector3.ZERO], mid + r * 6.0]
		v.next_idle = main.now() + 999.0
	return "Glasscheibe 4 m vor MoveEye, dahinter bleibt eine Person 30 s stehen – die Kamera sieht sie, das Wärmebild nicht"


func _real() -> bool:
	return main != null and main.simreal != null and main.simreal.th_real


func tick(force := false) -> void:
	var t: float = main.now()
	var dt := clampf(t - _last, 0.0, 5.0) if _last > 0.0 else 0.0
	_last = t
	if not _real():
		return
	var amb: float = main.ambient
	var dmin := dt * maxf(1.0, float(main.speed)) / 60.0                 # minutes of the scene (time runs faster)
	_scan_visitors(amb)
	var keep := []
	for c in _cars:
		if c.has("actor"):
			var a = c["actor"]
			if not is_instance_valid(a) or a.is_queued_for_deletion():
				continue
			var p: Vector3 = a.global_position
			if p.distance_to(c["pos"]) > 0.05 * maxf(dt, 0.1):                # it drives: the engine stays hot
				c["min"] = 0.0
			else:
				c["min"] = float(c["min"]) + dmin
			c["pos"] = p
		elif not is_instance_valid(c["node"]):
			continue
		else:
			c["min"] = float(c["min"]) + dmin
		for mp in c["mats"]:
			(mp[0] as ShaderMaterial).set_shader_parameter("temp", Waerme.engine(str(mp[1]), float(c["min"]), amb))
		keep.append(c)
	_cars = keep
	# tent: at night someone sleeps in it
	var tent_t: float = float(main.tmat("tent").get_shader_parameter("temp"))
	var sleeping: bool = main.thermsensor != null and main.thermsensor.tent_person and main.is_dark()
	for m in _tent:
		m.set_shader_parameter("temp", Waerme.T("tent_person", tent_t) if sleeping else tent_t)
	# street lamps: warm only when they burn (main switches them at dark; a power cut turns them off)
	var lit: bool = main.is_dark() and not main.power_off
	var stone_t: float = float(main.tmat("stone").get_shader_parameter("temp"))
	main.tmat("lamp").set_shader_parameter("temp", Waerme.T("lamp_led_on", amb) if lit else stone_t)


func _scan_visitors(amb: float) -> void:
	"""cars, tractors and motorbikes that drive through (actor.gd): their hot parts get an own material that can cool down"""
	if main.visitors == null:
		return
	for v in main.visitors.get_children():
		if str(v.get("kind")) != "car":
			continue
		var id: int = v.get_instance_id()
		if _seen.has(id):
			continue
		_seen[id] = true
		var mats := []
		for ch in _all_children(v):
			if not (ch is MeshInstance3D and ch.layers == 2 and ch.material_override is ShaderMaterial):
				continue
			var tv = (ch.material_override as ShaderMaterial).get_shader_parameter("temp")
			if tv == null or float(tv) < 60.0:
				continue
			var part := "hood"                                  # car engine 75 °C (actor.gd)
			if float(tv) >= 85.0:
				part = "exhaust"                                # exhaust 90 / 110 / 120 °C
			elif str(v.get("variant")) in ["tractor", "moto"]:
				part = "block"                                  # open engine (tractor bonnet 70, motorbike 80)
			var m := _thmat(Waerme.engine(part, 0.0, amb))
			ch.material_override = m
			mats.append([m, part])
		if not mats.is_empty():
			_cars.append({"actor": v, "node": v, "mats": mats, "min": 0.0, "pos": v.global_position})
	if _seen.size() > 400:
		_seen.clear()


func _all_children(n: Node) -> Array:
	var out := []
	for c in n.get_children():
		out.append(c)
		out.append_array(_all_children(c))
	return out


func info() -> Dictionary:
	var cars := []
	for c in _cars:
		var hood := -99.0
		for mp in c["mats"]:
			hood = maxf(hood, float((mp[0] as ShaderMaterial).get_shader_parameter("temp")))
		cars.append({"moving": c.has("actor"), "min": snappedf(float(c["min"]), 0.1), "hot_c": snappedf(hood, 0.1),
				"x": snappedf((c["node"] as Node3D).global_position.x, 0.1) if is_instance_valid(c["node"]) else 0.0,
				"z": snappedf((c["node"] as Node3D).global_position.z, 0.1) if is_instance_valid(c["node"]) else 0.0})
	return {"cars": cars, "tent": _tent.size()}
