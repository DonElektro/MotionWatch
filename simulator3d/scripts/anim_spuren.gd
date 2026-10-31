extends Node
## «Animationen verbessern» 17 (Daniel 31.10.2026): Fussspuren im Schnee, Staub auf dem Kiesweg.
## Ein Knoten unter main («anim_spuren»), von anim_mensch.gd / anim_tier.gd bei jedem Schritt aufgerufen: tritt(main, …).
## Schnee: jahreszeiten.snow_now(), im Bergtal die Jahreszeit «winter», oder Wetter «snow» unter 1 °C.
## Kies: die Wege «kies» von gelaende.gd und die Kies-Flecken des Nacht-Spiels (gamenacht.on_gravel); nur trocken.
## Leistung: nur bei hoher Qualität (anim_mensch.hoch), höchstens MAX Spuren (die ältesten verschwinden), Staub aus
## wenigen wiederverwendeten Teilchen-Wolken. Die Spuren liegen auf Ebene 1 (MoveEye sieht sie wie echte).

const MAX := 220
const DAUER := 90.0                 # s, dann verblasst eine Spur
const STAUB_N := 6

var main
var _spuren: Array = []             # [mesh, born]
var _mat: StandardMaterial3D
var _mesh_f: Mesh
var _mesh_p: Mesh
var _staub: Array = []
var _staub_i := 0
var _boden_t := -10.0
var _schnee := false
var _nass := false
var _t := 0.0


static func _ich(m) -> Node:
	if m == null or not m.is_inside_tree():
		return null
	var n = m.get_node_or_null("anim_spuren")
	if n == null:
		n = load("res://scripts/anim_spuren.gd").new()
		n.name = "anim_spuren"
		n.main = m
		m.add_child(n)
	return n


static func tritt(m, p: Vector3, heading: float, pfote := false, spd := 1.0) -> void:
	var s = _ich(m)
	if s != null:
		s._tritt(p, heading, pfote, spd)


static func anzahl(m) -> int:
	var s = m.get_node_or_null("anim_spuren") if m != null and m.is_inside_tree() else null
	return s._spuren.size() if s != null else 0


func _process(dt: float) -> void:
	_t += dt
	if _spuren.is_empty():
		return
	var i := 0
	while i < _spuren.size():                                  # fade the old ones (a few per frame)
		var e: Array = _spuren[i]
		var age := _t - float(e[1])
		if not is_instance_valid(e[0]) or age > DAUER:
			if is_instance_valid(e[0]):
				(e[0] as Node).queue_free()
			_spuren.remove_at(i)
			continue
		i += 1
		if i > 12:
			break


func _boden() -> void:
	if _t - _boden_t < 2.0:
		return
	_boden_t = _t
	_nass = str(main.weather) in ["rain", "snow"]
	_schnee = false
	if main.get("jahreszeiten") != null and main.jahreszeiten.has_method("snow_now") and float(main.jahreszeiten.snow_now()) > 0.3:
		_schnee = true
	elif str(main.weather) == "snow" and float(main.ambient) < 1.0:
		_schnee = true
	elif main.get("scenes") != null and main.scenes.data.has("bergtal"):
		var bt = main.scenes.data["bergtal"]
		if bt != null and bt.get("tal") != null and is_instance_valid(bt.tal) and bt.tal.is_inside_tree() and str(bt.get("season")) == "winter":
			_schnee = true


func _kies(p: Vector3) -> bool:
	var g = main.get("gelaende")
	if g != null and g.get("paths") != null:
		for pa in g.paths:
			if str(pa[2]) != "kies":
				continue
			var line: PackedVector2Array = pa[0]
			var r: float = float(pa[1])
			var q := Vector2(p.x, p.z)
			for k in range(0, line.size() - 1):
				if Geometry2D.get_closest_point_to_segment(q, line[k], line[k + 1]).distance_to(q) < r:
					return true
	var gm = main.get("game")
	if gm != null and gm.get("more") != null and gm.more.get("nacht") != null and gm.more.nacht.has_method("on_gravel"):
		return bool(gm.more.nacht.on_gravel(p))
	return false


func _tritt(p: Vector3, heading: float, pfote: bool, spd: float) -> void:
	_boden()
	if _schnee:
		_abdruck(p, heading, pfote)
	elif not _nass and spd > 0.4 and _kies(p):
		_wolke(p, spd)


func _abdruck(p: Vector3, heading: float, pfote: bool) -> void:
	if _mat == null:
		_mat = StandardMaterial3D.new()
		_mat.albedo_color = Color(0.62, 0.68, 0.78, 0.55)
		_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_mat.roughness = 1.0
		var bf := BoxMesh.new()
		bf.size = Vector3(0.1, 0.004, 0.26)
		_mesh_f = bf
		var bp := BoxMesh.new()
		bp.size = Vector3(0.05, 0.004, 0.06)
		_mesh_p = bp
	var mi := MeshInstance3D.new()
	mi.mesh = _mesh_p if pfote else _mesh_f
	mi.material_override = _mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.layers = 1
	add_child(mi)
	var gy: float = main.ground_y(p.x, p.z) if main.hilly() else 0.0
	mi.global_position = Vector3(p.x, maxf(gy, p.y - 0.05) + 0.006, p.z)
	mi.rotation.y = heading
	_spuren.append([mi, _t])
	while _spuren.size() > MAX:
		var e: Array = _spuren.pop_front()
		if is_instance_valid(e[0]):
			(e[0] as Node).queue_free()


func _wolke(p: Vector3, spd: float) -> void:
	if _staub.size() < STAUB_N:
		var c := CPUParticles3D.new()
		c.one_shot = true
		c.emitting = false
		c.amount = 10
		c.lifetime = 0.9
		c.explosiveness = 0.9
		c.direction = Vector3(0, 1, 0)
		c.spread = 70.0
		c.initial_velocity_min = 0.2
		c.initial_velocity_max = 0.6
		c.gravity = Vector3(0, -0.3, 0)
		c.scale_amount_min = 0.5
		c.scale_amount_max = 1.2
		var sm := SphereMesh.new()
		sm.radius = 0.035
		sm.height = 0.07
		sm.radial_segments = 6
		sm.rings = 3
		c.mesh = sm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.72, 0.68, 0.6, 0.45)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		c.material_override = m
		c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(c)
		_staub.append(c)
	var cp: CPUParticles3D = _staub[_staub_i % _staub.size()]
	_staub_i += 1
	cp.global_position = p + Vector3(0, 0.03, 0)
	cp.initial_velocity_max = 0.4 + 0.25 * spd
	cp.restart()
	cp.emitting = true
