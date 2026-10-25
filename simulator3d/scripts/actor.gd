extends Node3D
## A visitor: person, fox, deer, wild boar, cat, dog - or a car. Built from simple shapes, with a twin in the thermal
## picture (layer 2) for every part. Walks along a line, animals flee from the siren or the white light at night.

var main
var kind := "person"
var speed := 1.3
var dir := Vector3.RIGHT
var target := Vector3.ZERO
var phase := 0.0
var fled := false
var done := false
var pir_done := false
var legs: Array = []          # [pivot, sign]
var arms: Array = []
var lights: Array = []
var route: Array = []         # further points to walk to (Vector3)
var wait_until := 0.0
var behaviour := "walk"       # walk | thief
var crouch := 0.0
var torch: SpotLight3D = null
var body_root: Node3D

const COLORS := {
	"jacket": [Color(0.24, 0.24, 0.6), Color(0.5, 0.31, 0.16), Color(0.16, 0.43, 0.24), Color(0.6, 0.6, 0.6), Color(0.16, 0.16, 0.16), Color(0.7, 0.36, 0.12)],
}


func setup(m, k: String, from: Vector3, to: Vector3, spd: float) -> void:
	main = m
	kind = k
	position = from
	target = to
	speed = spd
	body_root = Node3D.new()
	add_child(body_root)
	match kind:
		"person":
			_build_person()
		"car":
			_build_car()
		_:
			_build_animal()
	_face(to)


func _face(p: Vector3) -> void:
	var d := p - position
	d.y = 0
	if d.length() > 0.05:
		dir = d.normalized()
		rotation.y = atan2(-dir.x, -dir.z)


# ---- building ------------------------------------------------------------------------------------------------------
func _part(parent: Node3D, mesh: Mesh, pos: Vector3, color: Color, temp: float, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	mi.material_override = main.mat(color)
	mi.layers = 1
	parent.add_child(mi)
	var th := MeshInstance3D.new()                 # its twin for the thermal camera
	th.mesh = mesh
	th.position = pos
	th.rotation = rot
	th.material_override = main.tmat_fixed(temp)
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(th)
	return mi


func _box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


func _caps(r: float, h: float) -> CapsuleMesh:
	var c := CapsuleMesh.new()
	c.radius = r
	c.height = max(h, 2.0 * r + 0.01)
	c.radial_segments = 10
	c.rings = 4
	return c


func _sph(r: float) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = 2 * r
	s.radial_segments = 12
	s.rings = 6
	return s


func _pivot(parent: Node3D, pos: Vector3) -> Node3D:
	var p := Node3D.new()
	p.position = pos
	parent.add_child(p)
	return p


func _build_person() -> void:
	var cold: bool = main.ambient < 10.0
	var jacket: Color = COLORS["jacket"][randi() % COLORS["jacket"].size()]
	var trousers := Color(0.18, 0.17, 0.16) if randf() < 0.6 else Color(0.25, 0.3, 0.45)
	var skin := Color(0.85, 0.66, 0.55)
	var cloth_t := 26.0 - (3.0 if cold else 0.0)
	for s in [-1, 1]:
		var hip := _pivot(body_root, Vector3(0.1 * s, 0.9, 0))
		_part(hip, _caps(0.07, 0.88), Vector3(0, -0.44, 0), trousers, cloth_t - 1.0)
		_part(hip, _box(0.11, 0.08, 0.26), Vector3(0, -0.88, -0.06), Color(0.1, 0.1, 0.1), cloth_t - 3.0)
		legs.append([hip, s])
	_part(body_root, _box(0.4, 0.62, 0.24), Vector3(0, 1.22, 0), jacket, cloth_t)
	for s in [-1, 1]:
		var sh := _pivot(body_root, Vector3(0.25 * s, 1.48, 0))
		_part(sh, _caps(0.055, 0.62), Vector3(0, -0.3, 0), jacket, cloth_t)
		_part(sh, _sph(0.05), Vector3(0, -0.63, 0), skin, 31.5)
		arms.append([sh, s])
	_part(body_root, _caps(0.05, 0.12), Vector3(0, 1.58, 0), skin, 33.0)
	_part(body_root, _sph(0.115), Vector3(0, 1.7, 0), skin, 34.0)
	_part(body_root, _sph(0.118), Vector3(0, 1.74, 0.01), Color(0.15, 0.12, 0.1) if randf() < 0.7 else Color(0.5, 0.4, 0.2), 30.0)


func _build_animal() -> void:
	# height of the back, body length, colour, body temperature (fur), legs thickness
	var spec := {"fox": [0.42, 0.62, Color(0.8, 0.38, 0.12), 28.0, 0.035], "deer": [0.95, 1.05, Color(0.55, 0.38, 0.22), 29.0, 0.045],
			"boar": [0.62, 1.05, Color(0.2, 0.18, 0.16), 28.0, 0.07], "cat": [0.26, 0.4, Color(0.35, 0.33, 0.3), 29.0, 0.025],
			"dog": [0.5, 0.7, Color(0.45, 0.35, 0.22), 30.0, 0.045], "badger": [0.3, 0.7, Color(0.4, 0.4, 0.4), 28.0, 0.05]}
	var s: Array = spec.get(kind, spec["fox"])
	var hb: float = s[0]
	var L: float = s[1]
	var col: Color = s[2]
	var t: float = s[3]
	var lw: float = s[4]
	var bodyr := hb * (0.32 if kind != "boar" else 0.45)
	_part(body_root, _caps(bodyr, L), Vector3(0, hb, 0), col, t, Vector3(PI / 2, 0, 0))
	if kind == "fox" or kind == "deer":                  # light belly
		_part(body_root, _caps(bodyr * 0.7, L * 0.7), Vector3(0, hb - bodyr * 0.45, 0), col.lightened(0.5), t - 1.0, Vector3(PI / 2, 0, 0))
	for i in range(4):
		var fx := 0.6 * bodyr * (1 if i % 2 == 0 else -1)
		var fz := (-L * 0.38) if i < 2 else (L * 0.38)
		var p := _pivot(body_root, Vector3(fx, hb, fz))
		_part(p, _caps(lw, hb), Vector3(0, -hb / 2, 0), col.darkened(0.25), t - 4.0)
		legs.append([p, 1 if i in [0, 3] else -1])
	var head_y := hb + bodyr * 0.4
	var head_z := -L * 0.55 - bodyr * 0.4
	if kind == "deer":
		_part(body_root, _caps(0.07, 0.55), Vector3(0, hb + 0.3, -L * 0.48), col, t, Vector3(-0.6, 0, 0))
		head_y = hb + 0.55
		head_z = -L * 0.62
	var hr := bodyr * (0.75 if kind != "boar" else 0.9)
	_part(body_root, _sph(hr), Vector3(0, head_y, head_z), col, t + 2.0)
	_part(body_root, _caps(hr * 0.45, hr * 1.6), Vector3(0, head_y - hr * 0.2, head_z - hr * 0.9), col.darkened(0.1) if kind != "fox" else col, t + 1.0, Vector3(PI / 2, 0, 0))
	for s2 in [-1, 1]:                                  # eyes (warm, and they shine in the light at night)
		var e := _part(body_root, _sph(hr * 0.13), Vector3(hr * 0.45 * s2, head_y + hr * 0.25, head_z - hr * 0.75), Color(0.05, 0.05, 0.05), 36.5)
		var em := StandardMaterial3D.new()
		em.albedo_color = Color(0.05, 0.05, 0.05)
		em.emission_enabled = true
		em.emission = Color(0.9, 0.95, 0.8)
		em.emission_energy_multiplier = 0.0
		e.material_override = em
		lights.append(em)
	if kind == "fox" or kind == "cat" or kind == "dog":  # ears
		for s3 in [-1, 1]:
			var ear := PrismMesh.new()
			ear.size = Vector3(hr * 0.6, hr * 0.8, hr * 0.25)
			_part(body_root, ear, Vector3(hr * 0.5 * s3, head_y + hr * 0.95, head_z), col.darkened(0.2), t - 2.0)
	if kind == "deer":
		for s4 in [-1, 1]:
			var ear2 := PrismMesh.new()
			ear2.size = Vector3(0.08, 0.16, 0.03)
			_part(body_root, ear2, Vector3(0.07 * s4, head_y + 0.15, head_z + 0.05), col, t - 2.0)
	if kind == "fox":                                    # bushy tail with white tip
		_part(body_root, _caps(bodyr * 0.55, L * 0.75), Vector3(0, hb - 0.05, L * 0.75), col, t - 4.0, Vector3(PI / 2 + 0.35, 0, 0))
		_part(body_root, _sph(bodyr * 0.45), Vector3(0, hb - 0.18, L * 1.08), Color(0.95, 0.95, 0.92), t - 6.0)
	elif kind == "cat" or kind == "dog":
		_part(body_root, _caps(lw * 0.8, L * 0.6), Vector3(0, hb + 0.08, L * 0.62), col, t - 4.0, Vector3(PI / 2 - 0.7, 0, 0))


func _build_car() -> void:
	var col: Color = [Color(0.6, 0.1, 0.1), Color(0.75, 0.75, 0.78), Color(0.08, 0.08, 0.1), Color(0.1, 0.25, 0.55)][randi() % 4]
	_part(body_root, _box(1.75, 0.7, 4.2), Vector3(0, 0.6, 0), col, main.ambient + 4.0)
	_part(body_root, _box(1.6, 0.55, 2.2), Vector3(0, 1.22, 0.25), col.darkened(0.3), main.ambient + 2.0)
	_part(body_root, _box(1.5, 0.45, 0.6), Vector3(0, 0.75, -1.85), col, 75.0)            # hot engine (front)
	_part(body_root, _box(0.12, 0.12, 0.3), Vector3(0.5, 0.35, 2.15), Color(0.2, 0.2, 0.2), 90.0)  # exhaust
	for x in [-0.85, 0.85]:
		for z in [-1.35, 1.35]:
			var w := CylinderMesh.new()
			w.top_radius = 0.33
			w.bottom_radius = 0.33
			w.height = 0.22
			_part(body_root, w, Vector3(x, 0.33, z), Color(0.05, 0.05, 0.05), main.ambient + 12.0, Vector3(0, 0, PI / 2))
	for x2 in [-0.6, 0.6]:
		var hl := SpotLight3D.new()                       # headlights
		hl.position = Vector3(x2, 0.7, -2.15)
		hl.spot_range = 45.0
		hl.spot_angle = 24.0
		hl.light_energy = 0.0
		hl.light_color = Color(1.0, 0.95, 0.85)
		hl.shadow_enabled = false
		body_root.add_child(hl)
		lights.append(hl)
		var lamp := _part(body_root, _box(0.3, 0.12, 0.05), Vector3(x2, 0.72, -2.11), Color(1, 1, 0.9), main.ambient + 30.0)
		var lm := StandardMaterial3D.new()
		lm.albedo_color = Color(1, 1, 0.9)
		lm.emission_enabled = true
		lm.emission = Color(1, 0.97, 0.85)
		lm.emission_energy_multiplier = 0.0
		lamp.material_override = lm
		lights.append(lm)


# ---- moving --------------------------------------------------------------------------------------------------------
func set_night(night: bool) -> void:
	for l in lights:
		if l is SpotLight3D:
			l.light_energy = 6.0 if night else 0.0
		elif l is StandardMaterial3D:
			if kind == "car":
				l.emission_energy_multiplier = 4.0 if night else 0.3
			else:
				l.emission_energy_multiplier = main.eye_shine(global_position) if night else 0.0


func scare() -> void:
	if fled or kind == "person" or kind == "car":
		return
	fled = true
	target = position - dir * 60.0                        # turn round and run
	speed *= 2.6
	route.clear()
	_face(target)


func _process(dt: float) -> void:
	if done:
		return
	var now := Time.get_ticks_msec() / 1000.0
	if now < wait_until:
		_animate(dt, 0.0)
		return
	var to := target - position
	to.y = 0
	var step: float = speed * dt * main.time_scale_visitors()
	if to.length() <= step:
		position = Vector3(target.x, position.y, target.z)
		if route.size() > 0:
			var nxt = route.pop_front()
			if typeof(nxt) == TYPE_ARRAY:                 # [point, wait seconds, crouch]
				target = nxt[0]
				wait_until = now + float(nxt[1])
				crouch = float(nxt[2]) if nxt.size() > 2 else 0.0
			else:
				target = nxt
				crouch = 0.0
			_face(target)
		else:
			done = true
			queue_free()
		return
	position += to.normalized() * step
	_animate(dt, speed)


func _animate(dt: float, spd: float) -> void:
	phase += dt * spd * (5.5 if kind == "person" else 7.0)
	var sw := sin(phase) * (0.55 if spd > 0.0 else 0.0)
	for l in legs:
		l[0].rotation.x = sw * l[1]
	for a in arms:
		a[0].rotation.x = -sw * a[1] * 0.8
	if kind == "person":
		body_root.position.y = -0.55 * crouch
		body_root.rotation.x = -0.35 * crouch
		if torch != null:
			torch.light_energy = 3.0 if crouch > 0.5 and int(now_s() * 3.0) % 4 != 0 else 0.0


func now_s() -> float:
	return Time.get_ticks_msec() / 1000.0


func add_torch() -> void:
	torch = SpotLight3D.new()
	torch.position = Vector3(0.25, 1.1, -0.3)
	torch.rotation = Vector3(-0.5, 0, 0)
	torch.spot_range = 8.0
	torch.spot_angle = 18.0
	torch.light_energy = 0.0
	torch.light_color = Color(1, 0.97, 0.9)
	body_root.add_child(torch)
