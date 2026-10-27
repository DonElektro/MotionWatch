extends Node3D
## A visitor: person (adult, child, jogger), animal (fox, deer, wild boar, cat, dog, badger, hare, hedgehog) or a car.
## Built from simple shapes, with a twin in the thermal picture (layer 2) for every part.
## From 3D-2.0: moves with inertia (turns smoothly, speeds up and slows down), goes round obstacles (main.avoid / main.keep_out),
## animals graze now and then and look up, people stop and look round; a dog can walk with its person (leader).

var main
var kind := "person"
var variant := ""             # person: "" | child | jogger
var speed := 1.3              # wanted speed (m/s)
var cur_speed := 0.0
var heading := 0.0            # direction it walks (rotation.y)
var dir := Vector3.RIGHT
var target := Vector3.ZERO
var phase := 0.0
var fled := false
var done := false
var pir_done := false
var legs: Array = []          # [pivot, sign]
var arms: Array = []
var lights: Array = []
var route: Array = []         # further points: Vector3, or [point, wait seconds, crouch, look at]
var wait_until := 0.0
var crouch := 0.0
var torch: SpotLight3D = null
var body_root: Node3D
var head: Node3D              # head (and neck) pivot: grazing, looking round
var tail: Node3D = null
var body_h := 0.9             # height of the body (for the rifle and the words above it)
var body_r := 0.5
var radius := 0.3             # keeps this far from obstacles
var dizzy_until := 0.0        # hit by the (bloodless) rifle: hops, sees stars, then runs away
var hop_t := -10.0
var stars: Node3D = null
var leader: Node3D = null     # a dog on a walk follows its person
var follow_off := Vector3(0.9, 0, 1.2)
var avoid_dir := Vector2.ZERO # steering, refreshed a few times a second
var avoid_t := 0.0
var avoid_side := 0.0         # going round an obstacle on this side (+1 / -1) ...
var side_until := 0.0         # ... until then
var idle_until := 0.0         # grazing / looking round: stands still until then
var next_idle := 0.0
var idle_kind := ""
var look_yaw := 0.0
var stuck_t := 0.0
var stuck_pos := Vector3.ZERO
var detour_until := 0.0
var detour_sign := 1.0
var preview := false          # only a picture for the list of visitors (does not move)
# ---- a player of the game (game.gd, from 3D-2.4): moved by the phone instead of a route ----
var controlled := false
var player_color := Color(0, 0, 0, 0)  # jacket colour of the player (red, blue, green, yellow)
var look := {}                # a player's choice (3D-3.0): {"hat": "" | "cap" | "hood", "pack": bool, "camo": bool}
var ctl_move := Vector2.ZERO  # wanted direction in the world (x, z), length 0..1
var ctl_run := false
var ctl_posture := 0          # 0 standing, 1 crouching, 2 crawling
var prone := 0.0              # 0..1 lying (crawling)
var frozen := false           # stands still (countdown, at the goal, caught)
# ---- joints and extras of a person (from 3D-2.7) ----
var hips: Node3D = null
var torso: Node3D = null
var lamp: SpotLight3D = null  # headlamp or phone light at night
var lamp_mat: StandardMaterial3D = null
var phone_out := false        # walks with the phone light in the hand (arm held forward)
var startle_until := 0.0      # the light went on: startled, arms up for a moment
var emote := ""               # players: caught / goal / throw (game.gd)
var emote_until := 0.0

const COLORS := {
	"jacket": [Color(0.24, 0.24, 0.6), Color(0.5, 0.31, 0.16), Color(0.16, 0.43, 0.24), Color(0.6, 0.6, 0.6), Color(0.16, 0.16, 0.16),
			Color(0.7, 0.36, 0.12), Color(0.75, 0.15, 0.15), Color(0.1, 0.45, 0.55)],
	"sport": [Color(0.95, 0.35, 0.1), Color(0.1, 0.6, 0.9), Color(0.85, 0.9, 0.2), Color(0.9, 0.2, 0.5)],
	"trousers": [Color(0.18, 0.17, 0.16), Color(0.25, 0.3, 0.45), Color(0.35, 0.3, 0.22), Color(0.12, 0.12, 0.14)],
	"skin": [Color(0.92, 0.75, 0.62), Color(0.85, 0.66, 0.55), Color(0.65, 0.47, 0.35), Color(0.45, 0.32, 0.24)],
	"hair": [Color(0.15, 0.12, 0.1), Color(0.45, 0.32, 0.18), Color(0.75, 0.6, 0.35), Color(0.6, 0.6, 0.6), Color(0.35, 0.15, 0.08)],
}


func setup(m, k: String, from: Vector3, to: Vector3, spd: float) -> void:
	main = m
	kind = k
	if kind == "child" or kind == "jogger":
		variant = kind
		kind = "person"
	position = from
	target = to
	speed = spd
	body_root = Node3D.new()
	add_child(body_root)
	match kind:
		"person":
			_build_person()
			radius = 0.3
		"car":
			_build_car()
			radius = 1.2
		_:
			_build_animal()
	var d := to - from
	heading = atan2(-d.x, -d.z) if d.length() > 0.05 else randf() * TAU
	rotation.y = heading
	dir = Vector3(-sin(heading), 0, -cos(heading))
	next_idle = now_s() + randf_range(4.0, 12.0)
	stuck_pos = position
	stuck_t = now_s()


func _face(p: Vector3) -> void:
	"""turn towards p (smoothly from 3D-2.0: only the wanted direction is set here)"""
	var d := p - position
	d.y = 0
	if d.length() > 0.05:
		dir = d.normalized()
		if preview:
			heading = atan2(-dir.x, -dir.z)
			rotation.y = heading


# ---- building ------------------------------------------------------------------------------------------------------
func _part(parent: Node3D, mesh: Mesh, pos: Vector3, color: Color, temp: float, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	mi.scale = scl
	mi.material_override = main.mat(color)
	mi.layers = 1
	parent.add_child(mi)
	var th := MeshInstance3D.new()                 # its twin for the thermal camera
	th.mesh = mesh
	th.position = pos
	th.rotation = rot
	th.scale = scl
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
	c.radial_segments = 12
	c.rings = 4
	return c


func _sph(r: float, h := -1.0) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = 2 * r if h < 0 else h
	s.radial_segments = 14
	s.rings = 7
	return s


func _cyl(rt: float, rb: float, h: float, seg := 10) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = seg
	return c


func _pivot(parent: Node3D, pos: Vector3) -> Node3D:
	var p := Node3D.new()
	p.position = pos
	parent.add_child(p)
	return p


func _pick(key: String) -> Color:
	var a: Array = COLORS[key]
	return a[randi() % a.size()]


func _build_person() -> void:
	"""a person (from 3D-2.7): hips and upper body as own joints (they swing against each other when walking), a face,
	different builds and clothes, hood or cap in the cold, at night now and then a headlamp or a phone light"""
	var cold: bool = main.ambient < 10.0
	var wet: bool = main.weather == "rain"
	var kid := variant == "child"
	var jog := variant == "jogger"
	var camo: bool = controlled and bool(look.get("camo", false))
	var jacket: Color = Color(0.33, 0.38, 0.22) if camo else (player_color if player_color.a > 0.0 else (_pick("sport") if jog else _pick("jacket")))
	var shirt: Color = [Color(0.9, 0.9, 0.88), Color(0.2, 0.25, 0.35), Color(0.6, 0.15, 0.15), Color(0.85, 0.75, 0.4)][randi() % 4]
	var trousers: Color = Color(0.3, 0.3, 0.2) if camo else (Color(0.1, 0.1, 0.12) if jog else _pick("trousers"))
	var skin := _pick("skin")
	var hair := _pick("hair")
	var shoe: Color = Color(0.95, 0.95, 0.95) if jog else [Color(0.12, 0.1, 0.09), Color(0.35, 0.22, 0.12), Color(0.2, 0.2, 0.22)][randi() % 3]
	var cloth_t := 26.0 - (3.0 if cold else 0.0) + (2.0 if jog else 0.0)
	var wide := randf_range(0.9, 1.15) if not kid else 1.0                  # build: slim … sturdy
	var tall := randf_range(0.93, 1.07)
	body_root.scale = Vector3(wide, tall, wide) * (0.62 if kid else 1.0)
	var open_jacket := not jog and not cold and randf() < 0.4
	# ---- hips and legs ----
	hips = _pivot(body_root, Vector3(0, 0.95, 0))
	_part(hips, _caps(0.165, 0.3), Vector3(0, 0.02, 0), trousers, cloth_t, Vector3(0, 0, PI / 2), Vector3(1, 1, 0.78))
	for s in [-1, 1]:
		var hip := _pivot(hips, Vector3(0.1 * s, -0.03, 0))
		_part(hip, _caps(0.078, 0.5), Vector3(0, -0.22, 0), trousers, cloth_t - 1.0)            # thigh
		var knee := _pivot(hip, Vector3(0, -0.46, 0))
		_part(knee, _caps(0.062, 0.46), Vector3(0, -0.21, 0), trousers, cloth_t - 1.5)           # shin
		_part(knee, _box(0.11, 0.06, 0.27), Vector3(0, -0.43, -0.06), shoe, cloth_t - 4.0)       # shoe
		_part(knee, _box(0.115, 0.02, 0.28), Vector3(0, -0.465, -0.06), shoe.darkened(0.5), cloth_t - 5.0)   # sole
		legs.append([hip, s, knee])
	# ---- upper body ----
	torso = _pivot(body_root, Vector3(0, 0.98, 0))
	_part(torso, _caps(0.17, 0.34), Vector3(0, 0.12, 0), jacket, cloth_t, Vector3.ZERO, Vector3(1.0, 1.0, 0.68))      # belly
	_part(torso, _caps(0.205, 0.36), Vector3(0, 0.36, 0), jacket, cloth_t, Vector3.ZERO, Vector3(1.05, 1.0, 0.66))    # chest
	_part(torso, _caps(0.07, 0.5), Vector3(0, 0.49, 0), jacket, cloth_t, Vector3(0, 0, PI / 2))                       # shoulders
	if open_jacket:                                                        # open jacket: the shirt shows in front
		_part(torso, _box(0.13, 0.42, 0.02), Vector3(0, 0.27, -0.142), shirt, cloth_t + 2.0)
	else:
		_part(torso, _box(0.012, 0.42, 0.012), Vector3(0, 0.27, -0.142), jacket.darkened(0.45), cloth_t)               # zip
	if camo:                                                               # camouflage: darker and brown patches
		for k2 in range(7):
			var pc: Color = Color(0.2, 0.24, 0.13) if k2 % 2 == 0 else Color(0.38, 0.3, 0.18)
			var a2 := randf() * TAU
			_part(torso, _sph(0.07, 0.05), Vector3(cos(a2) * 0.16, randf_range(0.05, 0.45), sin(a2) * 0.12), pc, cloth_t, Vector3(0, a2, 0), Vector3(1.4, 1.0, 0.4))
	if (controlled and bool(look.get("pack", false))) or (not jog and not kid and not controlled and randf() < 0.35):   # backpack
		var bp: Color = jacket.darkened(0.5).lerp(Color(0.2, 0.3, 0.2), 0.5)
		_part(torso, _box(0.3, 0.4, 0.15), Vector3(0, 0.3, 0.19), bp, main.ambient + 3.0)
		_part(torso, _box(0.26, 0.12, 0.05), Vector3(0, 0.18, 0.28), bp.darkened(0.2), main.ambient + 3.0)
	var hand_c: Color = Color(0.15, 0.15, 0.16) if cold else skin             # gloves in the cold
	for s in [-1, 1]:
		var sh := _pivot(torso, Vector3(0.245 * s, 0.48, 0))
		_part(sh, _caps(0.058, 0.34), Vector3(0, -0.15, 0), jacket, cloth_t)
		var el := _pivot(sh, Vector3(0, -0.3, 0))
		_part(el, _caps(0.05, 0.32), Vector3(0, -0.14, 0), jacket if cold or not jog else skin, cloth_t if cold or not jog else 32.0)
		_part(el, _caps(0.045, 0.11), Vector3(0, -0.32, -0.01), hand_c, 31.5 if not cold else 22.0, Vector3.ZERO, Vector3(1.0, 1.0, 0.7))  # hand
		arms.append([sh, s, el])
	# ---- head ----
	head = _pivot(torso, Vector3(0, 0.6, 0))
	_part(head, _caps(0.052, 0.13), Vector3(0, 0.02, 0), skin, 33.0)                                   # neck
	_part(head, _sph(0.105, 0.25), Vector3(0, 0.16, 0), skin, 34.0, Vector3.ZERO, Vector3(1.0, 1.0, 1.08))   # head
	_part(head, _sph(0.06, 0.07), Vector3(0, 0.085, -0.035), skin, 34.0, Vector3.ZERO, Vector3(1.2, 1.0, 1.1))  # chin / jaw
	_part(head, _caps(0.016, 0.05), Vector3(0, 0.15, -0.115), skin.darkened(0.06), 34.0, Vector3(0.3, 0, 0))     # nose
	for s3 in [-1, 1]:
		_part(head, _sph(0.022), Vector3(0.042 * s3, 0.178, -0.093), Color(0.95, 0.95, 0.93), 35.0)            # eye white
		_part(head, _sph(0.012), Vector3(0.042 * s3, 0.178, -0.11), Color(0.08, 0.07, 0.06), 35.0)             # pupil
		_part(head, _box(0.045, 0.01, 0.012), Vector3(0.044 * s3, 0.21, -0.1), hair.darkened(0.2), 34.0, Vector3(0, 0, -0.12 * s3))   # eyebrow
		_part(head, _sph(0.025, 0.05), Vector3(0.107 * s3, 0.16, 0.0), skin.darkened(0.05), 33.5, Vector3.ZERO, Vector3(0.5, 1.0, 0.8))   # ear
	_part(head, _box(0.05, 0.008, 0.01), Vector3(0, 0.11, -0.108), Color(0.45, 0.2, 0.18), 34.0)           # mouth
	var style := randi() % 5
	var hooded: bool = (cold or wet) and not jog and randf() < 0.45
	if controlled and not look.is_empty():                                  # a player chose
		hooded = look.get("hat", "") == "hood"
		style = 3 if look.get("hat", "") == "cap" else 0
	if hooded:                                                             # hood up
		_part(head, _sph(0.13, 0.27), Vector3(0, 0.18, 0.02), jacket.darkened(0.1), cloth_t - 2.0, Vector3.ZERO, Vector3(1.0, 1.0, 1.05))
		_part(torso, _sph(0.11, 0.12), Vector3(0, 0.55, 0.12), jacket.darkened(0.1), cloth_t)
	elif style == 0 or kid:
		_part(head, _sph(0.112, 0.15), Vector3(0, 0.21, 0.012), hair, 30.0)                                # short hair
	elif style == 1:
		_part(head, _sph(0.116, 0.17), Vector3(0, 0.21, 0.015), hair, 30.0)
		_part(head, _caps(0.07, 0.26), Vector3(0, 0.08, 0.085), hair, 30.0)                                # long hair
	elif style == 2:
		_part(head, _sph(0.114, 0.15), Vector3(0, 0.21, 0.012), hair, 30.0)
		_part(head, _caps(0.035, 0.16), Vector3(0, 0.12, 0.12), hair, 30.0, Vector3(0.4, 0, 0))            # ponytail
	elif style == 3 or (cold and not jog and not controlled):
		_part(head, _sph(0.118, 0.14), Vector3(0, 0.23, 0.0), jacket.lightened(0.3), 28.0)                 # cap
		_part(head, _sph(0.03), Vector3(0, 0.31, 0.0), Color(0.95, 0.95, 0.95), 26.0)
	else:
		_part(head, _cyl(0.115, 0.115, 0.05, 16), Vector3(0, 0.245, 0), Color(0.3, 0.25, 0.2), 27.0)       # hat
		_part(head, _cyl(0.16, 0.16, 0.012, 18), Vector3(0, 0.22, 0), Color(0.3, 0.25, 0.2), 27.0)
	body_h = 0.9 * body_root.scale.y
	# at night some people carry a light: a headlamp or the light of the phone (Motion Watch sees it)
	if main.is_dark() and not kid and not controlled and not preview and randf() < main.lamp_share:
		lamp = SpotLight3D.new()
		lamp.spot_range = 9.0
		lamp.spot_angle = 24.0
		lamp.light_color = Color(1.0, 0.97, 0.9)
		var bulb := MeshInstance3D.new()
		bulb.mesh = _sph(0.032)
		lamp_mat = StandardMaterial3D.new()                         # seen straight on, a lamp dazzles the camera
		lamp_mat.albedo_color = Color(1.0, 0.98, 0.9)
		lamp_mat.emission_enabled = true
		lamp_mat.emission = Color(1.0, 0.98, 0.9)
		lamp_mat.emission_energy_multiplier = 16.0
		bulb.material_override = lamp_mat
		if randf() < 0.5:
			head.add_child(lamp)                                           # headlamp
			lamp.position = Vector3(0, 0.24, -0.16)
			lamp.rotation = Vector3(-0.35, 0, 0)
			_part(head, _box(0.2, 0.025, 0.2), Vector3(0, 0.235, 0), Color(0.1, 0.1, 0.1), 28.0)
			bulb.position = Vector3(0, 0.24, -0.135)
			head.add_child(bulb)
		else:
			arms[1][2].add_child(lamp)                                     # phone in the right hand
			lamp.position = Vector3(0, -0.36, -0.05)
			lamp.rotation = Vector3(-1.2, 0, 0)
			bulb.position = Vector3(0, -0.36, -0.05)
			arms[1][2].add_child(bulb)
			phone_out = true
		lamp.light_energy = 6.0


func _build_animal() -> void:
	# height of the back, body length, colour, body temperature (fur), leg thickness
	var spec := {"fox": [0.42, 0.62, Color(0.82, 0.38, 0.12), 28.0, 0.035], "deer": [0.95, 1.05, Color(0.58, 0.4, 0.23), 29.0, 0.042],
			"boar": [0.62, 1.05, Color(0.22, 0.19, 0.16), 28.0, 0.07], "cat": [0.26, 0.4, Color(0.35, 0.33, 0.3), 29.0, 0.025],
			"dog": [0.5, 0.7, Color(0.45, 0.35, 0.22), 30.0, 0.045], "badger": [0.3, 0.7, Color(0.42, 0.42, 0.42), 28.0, 0.05],
			"hare": [0.28, 0.42, Color(0.55, 0.45, 0.32), 30.0, 0.03], "hedgehog": [0.12, 0.26, Color(0.35, 0.28, 0.2), 27.0, 0.02]}
	var s: Array = spec.get(kind, spec["fox"])
	var hb: float = s[0]
	var L: float = s[1]
	var col: Color = s[2]
	if kind == "cat":
		col = [Color(0.35, 0.33, 0.3), Color(0.85, 0.5, 0.2), Color(0.1, 0.1, 0.1), Color(0.9, 0.88, 0.85)][randi() % 4]
	elif kind == "dog":
		col = [Color(0.45, 0.35, 0.22), Color(0.1, 0.1, 0.1), Color(0.85, 0.75, 0.55), Color(0.6, 0.55, 0.5)][randi() % 4]
	col = col.lerp(col.lightened(0.15), randf())
	var t: float = s[3]
	var lw: float = s[4]
	var sc := randf_range(0.9, 1.1)
	body_root.scale = Vector3.ONE * sc
	var bodyr := hb * (0.32 if kind != "boar" else 0.45)
	if kind == "hedgehog":
		bodyr = 0.11
	body_h = hb * sc
	body_r = max(L * 0.6, hb * 0.55) * sc
	radius = max(0.15, L * 0.45) * sc
	if kind == "hedgehog":
		_part(body_root, _sph(0.13, 0.18), Vector3(0, 0.1, 0), col, t - 6.0, Vector3.ZERO, Vector3(1, 1, 1.4))
		for i in range(26):                                                  # spines
			var a := randf() * TAU
			var e := randf_range(0.2, 1.3)
			var p := Vector3(cos(a) * 0.12 * cos(e), 0.1 + 0.09 * sin(e), sin(a) * 0.17 * cos(e))
			var sp := _part(body_root, _cyl(0.0, 0.012, 0.07, 4), p, Color(0.25, 0.2, 0.15), t - 8.0)
			sp.look_at_from_position(sp.position, p * 3.0 + Vector3(0, 0.2, 0), Vector3.UP)
		head = _pivot(body_root, Vector3(0, 0.08, -0.2))
		_part(head, _sph(0.05), Vector3.ZERO, Color(0.6, 0.5, 0.4), t)
		_part(head, _sph(0.015), Vector3(0, -0.01, -0.05), Color(0.05, 0.05, 0.05), t)
		for i in range(4):
			var p2 := _pivot(body_root, Vector3(0.07 * (1 if i % 2 == 0 else -1), 0.05, 0.08 if i < 2 else -0.08))
			_part(p2, _caps(lw, 0.06), Vector3(0, -0.02, 0), Color(0.3, 0.25, 0.2), t - 4.0)
			legs.append([p2, 1 if i in [0, 3] else -1, null])
		_eyes(head, 0.03, 0.01, -0.035)
		return
	_part(body_root, _caps(bodyr, L), Vector3(0, hb, 0), col, t, Vector3(PI / 2, 0, 0))
	# from 3D-2.8: a shaped body - chest in front, haunch behind, a darker back, legs thicker at the top
	var bulk: float = {"deer": 0.88, "boar": 1.02, "dog": 1.0}.get(kind, 1.02)
	_part(body_root, _sph(bodyr * bulk, bodyr * bulk * 2.2), Vector3(0, hb + bodyr * 0.05, -L * 0.3), col, t)        # chest / shoulders
	_part(body_root, _sph(bodyr * bulk * 0.96, bodyr * bulk * 2.1), Vector3(0, hb + bodyr * 0.08, L * 0.3), col.darkened(0.04), t)   # haunch
	_part(body_root, _caps(bodyr * 0.45, L * 0.95), Vector3(0, hb + bodyr * 0.68, 0), col.darkened(0.22), t - 1.0, Vector3(PI / 2, 0, 0), Vector3(1.0, 1.0, 0.5))  # darker back
	if kind in ["fox", "deer", "hare"]:                                       # light belly / chest
		_part(body_root, _caps(bodyr * 0.72, L * 0.65), Vector3(0, hb - bodyr * 0.42, -L * 0.05), col.lightened(0.55), t - 1.0, Vector3(PI / 2, 0, 0))
	if kind == "boar":                                                         # bristle ridge
		_part(body_root, _box(0.06, 0.08, L * 0.8), Vector3(0, hb + bodyr * 0.95, -L * 0.05), col.darkened(0.3), t - 3.0)
	if kind == "badger":
		_part(body_root, _caps(bodyr * 0.8, L * 0.9), Vector3(0, hb - bodyr * 0.3, 0), Color(0.12, 0.12, 0.12), t - 1.0, Vector3(PI / 2, 0, 0))
	for i in range(4):
		var fx := 0.6 * bodyr * (1 if i % 2 == 0 else -1)
		var fz := (-L * 0.38) if i < 2 else (L * 0.38)
		var p := _pivot(body_root, Vector3(fx, hb, fz))
		var legc: Color = Color(0.1, 0.08, 0.07) if kind == "fox" else col.darkened(0.25)
		var hare_back := kind == "hare" and i >= 2
		_part(p, _caps(lw * (1.6 if hare_back else 1.0), hb * (0.55 if hare_back else 1.0)), Vector3(0, -hb / (3.0 if hare_back else 2.0), 0), legc, t - 4.0)
		if not hare_back:                                                   # upper leg in the colour of the body
			_part(p, _caps(lw * 1.75, hb * 0.48), Vector3(0, -hb * 0.17, 0), col, t - 1.0)
		_part(p, _sph(lw * 1.2), Vector3(0, -hb + lw, -lw * 0.6), legc.darkened(0.3), t - 5.0)   # paw / hoof
		legs.append([p, 1 if i in [0, 3] else -1, null])
	var head_y := hb + bodyr * 0.4
	var head_z := -L * 0.55 - bodyr * 0.4
	head = _pivot(body_root, Vector3(0, hb + bodyr * 0.2, -L * 0.45))
	var hy := head_y - head.position.y
	var hz := head_z - head.position.z
	if kind == "deer":
		_part(head, _caps(0.07, 0.6), Vector3(0, 0.25, -0.05), col, t, Vector3(-0.5, 0, 0))     # neck
		hy = 0.55
		hz = -0.18
	var hr := bodyr * (0.75 if kind != "boar" else 0.9)
	if kind == "deer":
		hr = 0.12                                                          # a slim head on the long neck
	_part(head, _sph(hr), Vector3(0, hy, hz), col, t + 2.0)
	if kind in ["fox", "dog", "cat", "badger", "hare"]:                         # neck
		_part(head, _caps(hr * 0.62, max(0.05, Vector2(hy, hz).length()) + hr * 0.6), Vector3(0, hy * 0.5, hz * 0.5), col, t + 1.0, Vector3(-PI / 2 + atan2(hy, -hz), 0, 0))
	if kind == "fox":                                                          # white chin and cheeks
		_part(head, _sph(hr * 0.55), Vector3(0, hy - hr * 0.55, hz - hr * 0.55), Color(0.95, 0.93, 0.88), t + 1.0, Vector3.ZERO, Vector3(1.4, 0.8, 1.2))
	if kind == "boar" or kind == "badger":                                     # small round ears
		for s6 in [-1, 1]:
			_part(head, _sph(hr * 0.25), Vector3(hr * 0.55 * s6, hy + hr * 0.7, hz + hr * 0.2), col.darkened(0.2), t - 2.0, Vector3.ZERO, Vector3(1.0, 1.2, 0.4))
	var snout := col.darkened(0.1) if kind != "fox" else col
	_part(head, _caps(hr * 0.45, hr * 1.6), Vector3(0, hy - hr * 0.2, hz - hr * 0.9), snout, t + 1.0, Vector3(PI / 2, 0, 0))
	_part(head, _sph(hr * 0.16), Vector3(0, hy - hr * 0.15, hz - hr * 1.7), Color(0.05, 0.05, 0.05), t)         # nose
	if kind == "boar":                                                         # snout disc and tusks
		_part(head, _cyl(hr * 0.32, hr * 0.32, 0.03, 12), Vector3(0, hy - hr * 0.2, hz - hr * 1.72), Color(0.45, 0.35, 0.32), t, Vector3(PI / 2, 0, 0))
		for s2 in [-1, 1]:
			_part(head, _cyl(0.0, 0.012, 0.07, 5), Vector3(hr * 0.3 * s2, hy - hr * 0.3, hz - hr * 1.35), Color(0.95, 0.93, 0.85), t - 6.0, Vector3(-0.6, 0, 0.3 * s2))
	if kind == "badger":                                                       # white stripes on the head
		for s2 in [-1, 1]:
			_part(head, _box(hr * 0.25, hr * 0.3, hr * 1.8), Vector3(hr * 0.35 * s2, hy + hr * 0.6, hz - hr * 0.3), Color(0.92, 0.92, 0.9), t)
	_eyes(head, hr * 0.13, hr * 0.45, hz - hr * 0.75, hy + hr * 0.25)
	var floppy := kind == "dog" and randf() < 0.5
	if kind in ["fox", "cat", "dog"] and not floppy:                           # pointed ears (fox: black tips)
		for s3 in [-1, 1]:
			var ear := PrismMesh.new()
			ear.size = Vector3(hr * 0.6, hr * 0.8, hr * 0.25)
			_part(head, ear, Vector3(hr * 0.5 * s3, hy + hr * 0.95, hz), col.darkened(0.2), t - 2.0)
			if kind == "fox":
				var tip := PrismMesh.new()
				tip.size = Vector3(hr * 0.25, hr * 0.32, hr * 0.27)
				_part(head, tip, Vector3(hr * 0.5 * s3, hy + hr * 1.23, hz), Color(0.08, 0.06, 0.05), t - 3.0)
	if floppy:                                                                 # hanging ears
		for s3 in [-1, 1]:
			_part(head, _caps(hr * 0.22, hr * 1.2), Vector3(hr * 0.85 * s3, hy - hr * 0.1, hz + hr * 0.1), col.darkened(0.3), t - 2.0, Vector3(0, 0, 0.25 * s3), Vector3(0.6, 1.0, 1.0))
	if kind == "hare":                                                         # long ears
		for s3 in [-1, 1]:
			_part(head, _caps(hr * 0.22, hr * 2.4), Vector3(hr * 0.3 * s3, hy + hr * 1.4, hz + hr * 0.2), col, t - 2.0, Vector3(0.25, 0, 0.15 * s3))
	if kind == "deer":
		for s4 in [-1, 1]:
			var ear2 := PrismMesh.new()
			ear2.size = Vector3(0.08, 0.16, 0.03)
			_part(head, ear2, Vector3(0.08 * s4, hy + 0.13, hz + 0.05), col, t - 2.0, Vector3(0, 0, 0.5 * s4))
		if randf() < 0.4:                                                      # a buck: antlers
			for s5 in [-1, 1]:
				_part(head, _cyl(0.008, 0.014, 0.24, 5), Vector3(0.05 * s5, hy + 0.2, hz + 0.02), Color(0.55, 0.45, 0.32), t - 8.0, Vector3(0.2, 0, 0.25 * s5))
				_part(head, _cyl(0.005, 0.009, 0.1, 5), Vector3(0.09 * s5, hy + 0.27, hz - 0.03), Color(0.55, 0.45, 0.32), t - 8.0, Vector3(-0.6, 0, 0.3 * s5))
		_part(body_root, _sph(0.09), Vector3(0, hb + 0.05, L * 0.55), Color(0.95, 0.93, 0.9), t - 3.0)   # white rump
	# tails
	tail = _pivot(body_root, Vector3(0, hb, L * 0.5))
	if kind == "fox":
		_part(tail, _caps(bodyr * 0.55, L * 0.75), Vector3(0, -0.05, L * 0.3), col, t - 4.0, Vector3(PI / 2 + 0.35, 0, 0))
		_part(tail, _sph(bodyr * 0.45), Vector3(0, -0.17, L * 0.62), Color(0.95, 0.95, 0.92), t - 6.0)
	elif kind == "cat":
		_part(tail, _caps(lw * 0.8, L * 0.8), Vector3(0, 0.15, L * 0.1), col, t - 4.0, Vector3(0.2, 0, 0))
	elif kind == "dog":
		_part(tail, _caps(lw * 0.9, L * 0.45), Vector3(0, 0.1, L * 0.14), col, t - 4.0, Vector3(PI / 2 - 0.8, 0, 0))
	elif kind == "boar":
		_part(tail, _caps(0.015, 0.18), Vector3(0, -0.05, 0.05), col, t - 4.0, Vector3(0.3, 0, 0))
	elif kind == "hare":
		_part(tail, _sph(0.05), Vector3(0, 0.02, 0.0), Color(0.95, 0.95, 0.95), t - 4.0)


func _eyes(parent: Node3D, r: float, x: float, z: float, y := 0.0) -> void:
	"""eyes: warm, and they shine in the light at night"""
	for s2 in [-1, 1]:
		var e := _part(parent, _sph(r), Vector3(x * s2, y, z), Color(0.05, 0.05, 0.05), 36.5)
		var em := StandardMaterial3D.new()
		em.albedo_color = Color(0.05, 0.05, 0.05)
		em.emission_enabled = true
		em.emission = Color(0.9, 0.95, 0.8)
		em.emission_energy_multiplier = 0.0
		e.material_override = em
		lights.append(em)


func _build_car() -> void:
	var col: Color = [Color(0.6, 0.1, 0.1), Color(0.75, 0.75, 0.78), Color(0.08, 0.08, 0.1), Color(0.1, 0.25, 0.55), Color(0.85, 0.85, 0.85), Color(0.25, 0.35, 0.25)][randi() % 6]
	_part(body_root, _box(1.75, 0.6, 4.2), Vector3(0, 0.6, 0), col, main.ambient + 4.0)
	_part(body_root, _box(1.6, 0.5, 2.1), Vector3(0, 1.15, 0.25), col.darkened(0.15), main.ambient + 2.0)
	_part(body_root, _box(1.5, 0.42, 0.05), Vector3(0, 1.15, -0.82), Color(0.15, 0.2, 0.25), main.ambient + 2.0, Vector3(-0.5, 0, 0))   # windscreen
	_part(body_root, _box(1.5, 0.4, 0.05), Vector3(0, 1.15, 1.32), Color(0.15, 0.2, 0.25), main.ambient + 2.0, Vector3(0.4, 0, 0))     # rear window
	for s in [-1, 1]:
		_part(body_root, _box(0.05, 0.36, 1.9), Vector3(0.81 * s, 1.15, 0.25), Color(0.15, 0.2, 0.25), main.ambient + 2.0)               # side windows
	_part(body_root, _box(1.5, 0.45, 0.6), Vector3(0, 0.75, -1.85), col, 75.0)            # hot engine (front)
	_part(body_root, _box(1.8, 0.18, 0.12), Vector3(0, 0.42, -2.12), Color(0.15, 0.15, 0.15), main.ambient + 3.0)   # bumpers
	_part(body_root, _box(1.8, 0.18, 0.12), Vector3(0, 0.42, 2.12), Color(0.15, 0.15, 0.15), main.ambient + 3.0)
	_part(body_root, _box(0.12, 0.12, 0.3), Vector3(0.5, 0.35, 2.15), Color(0.2, 0.2, 0.2), 90.0)  # exhaust
	for x in [-0.85, 0.85]:
		for z in [-1.35, 1.35]:
			_part(body_root, _cyl(0.33, 0.33, 0.22, 16), Vector3(x, 0.33, z), Color(0.05, 0.05, 0.05), main.ambient + 12.0, Vector3(0, 0, PI / 2))
			_part(body_root, _cyl(0.18, 0.18, 0.23, 12), Vector3(x, 0.33, z), Color(0.6, 0.6, 0.62), main.ambient + 10.0, Vector3(0, 0, PI / 2))
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
		_part(body_root, _box(0.28, 0.1, 0.04), Vector3(x2, 0.72, 2.12), Color(0.7, 0.05, 0.05), main.ambient + 8.0)   # tail lights


# ---- moving --------------------------------------------------------------------------------------------------------
func set_night(night: bool) -> void:
	if lamp != null:
		lamp.light_energy = 6.0 if night else 0.0
		lamp_mat.emission_energy_multiplier = 16.0 if night else 0.0
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
	leader = null
	target = position - dir * 60.0                        # turn round and run
	speed *= 2.6
	route.clear()
	idle_until = 0.0
	wait_until = 0.0
	_face(target)


func is_animal() -> bool:
	return kind != "person" and kind != "car"


func _process(dt: float) -> void:
	if done or preview:
		return
	var now := now_s()
	if controlled:
		_player(dt, now)
		return
	if stars != null:
		_dizzy(dt, now)
	if leader != null:                                    # a dog on a walk: goes along with its person
		if not is_instance_valid(leader) or leader.done:
			leader = null
			done = true
			queue_free()
			return
		var off: Vector3 = leader.global_transform.basis * follow_off
		target = leader.position + off
		route.clear()
	if now < wait_until or now < idle_until:
		cur_speed = move_toward(cur_speed, 0.0, dt * 3.0)
		_turn(dt, true)
		_animate(dt, cur_speed, now)
		return
	var to := target - position
	to.y = 0
	var dist := to.length()
	if dist < 0.35 + (0.4 if leader != null else 0.0):
		if leader != null:
			cur_speed = move_toward(cur_speed, 0.0, dt * 3.0)
			_animate(dt, cur_speed, now)
			return
		_next_point(now)
		return
	# graze / look round now and then (not when fleeing, not cars, not on a walk)
	if kind != "car" and not fled and leader == null and now > next_idle and route.size() >= 0:
		next_idle = now + randf_range(8.0, 20.0)
		if randf() < (0.55 if is_animal() else 0.3):
			var kinds: Array = {"person": ["look", "look", "phone", "bend"], "deer": ["graze", "graze", "look"], "boar": ["root", "graze"],
					"fox": ["sniff", "look"], "hare": ["sit_up", "graze"], "cat": ["sit", "look"], "dog": ["sniff", "sit"],
					"badger": ["root", "sniff"], "hedgehog": ["sniff"]}.get(kind, ["look"])
			idle_kind = kinds[randi() % kinds.size()]
			idle_until = now + randf_range(2.0, 5.0)
			look_yaw = randf_range(-0.8, 0.8)
			return
	idle_kind = ""
	dir = Vector3(to.x / dist, 0, to.z / dist)
	# steering round obstacles (people and animals; cars stay on their way)
	if kind != "car" and main.avoid_on:
		avoid_t -= dt
		if avoid_t <= 0.0:
			avoid_t = 0.12
			var d2 := Vector2(dir.x, dir.z)
			if now < detour_until:
				d2 = d2.rotated(detour_sign * 1.3)
			var r3: Vector3 = main.avoid(Vector2(position.x, position.z), d2, radius, kind == "person", avoid_side if now < side_until else 0.0)
			avoid_dir = Vector2(r3.x, r3.y)
			if r3.z != 0.0 and (avoid_side != r3.z or now >= side_until):
				avoid_side = r3.z
				side_until = now + 2.5                   # keep going round on this side
		if avoid_dir != Vector2.ZERO:
			dir = Vector3(avoid_dir.x, 0, avoid_dir.y)
	var want: float = speed * main.time_scale_visitors()
	if route.size() > 0 and typeof(route[0]) == TYPE_ARRAY and dist < 2.0:
		want *= max(0.35, dist / 2.0)                    # slows down before a stop
	cur_speed = move_toward(cur_speed, want, dt * (2.0 if kind != "car" else 3.0) * max(1.0, want))
	_turn(dt, false)
	var fwd := Vector3(-sin(heading), 0, -cos(heading))
	var step: float = cur_speed * dt
	position += fwd * min(step, dist)
	if kind != "car" and main.avoid_on:                   # never inside an object
		var q: Vector2 = main.keep_out(Vector2(position.x, position.z), radius, kind == "person")
		position.x = q.x
		position.z = q.y
	# stuck? (against a fence, between trees) - try round the other side for a moment
	if now - stuck_t > 3.0:
		if position.distance_to(stuck_pos) < 0.4 and cur_speed > 0.05 and now > detour_until:
			detour_until = now + 1.8
			detour_sign = 1.0 if randf() < 0.5 else -1.0
			if position.distance_to(stuck_pos) < 0.1 and route.size() > 0 and randf() < 0.3:
				_next_point(now)                          # really stuck: skip this point
		stuck_t = now
		stuck_pos = position
	_animate(dt, cur_speed, now)


const PLAYER_SPEED := [1.5, 0.9, 0.45]   # walking: standing, crouching, crawling (m/s); running: × 2.3 (only standing)


func player_speed_now() -> float:
	return cur_speed


func _player(dt: float, now: float) -> void:
	"""moved by the phone: direction from the joystick, posture from the buttons, never inside an object"""
	var want_c := 0.55 if ctl_posture == 1 else 0.0
	var want_p := 1.0 if ctl_posture == 2 else 0.0
	crouch = move_toward(crouch, want_c, dt * 2.5)
	prone = move_toward(prone, want_p, dt * 2.0)
	var mv := ctl_move.limit_length(1.0)
	if frozen:
		mv = Vector2.ZERO
	var top: float = PLAYER_SPEED[ctl_posture] * (2.3 if ctl_run and ctl_posture == 0 else 1.0)
	var want: float = top * mv.length()
	cur_speed = move_toward(cur_speed, want, dt * 5.0)
	if mv.length() > 0.08:
		dir = Vector3(mv.x, 0, mv.y).normalized()
		heading = lerp_angle(heading, atan2(-dir.x, -dir.z), clamp(10.0 * dt, 0.0, 1.0))
		rotation.y = heading
	if cur_speed > 0.01:
		var mdir := dir if mv.length() > 0.08 else Vector3(-sin(heading), 0, -cos(heading))
		position += mdir * cur_speed * dt
		var q: Vector2 = main.keep_out(Vector2(position.x, position.z), radius, true)
		position.x = q.x
		position.z = q.y
	speed = max(1.0, top)
	_animate(dt, cur_speed, now)


func _next_point(now: float) -> void:
	if route.size() > 0:
		var nxt = route.pop_front()
		if typeof(nxt) == TYPE_ARRAY:                     # [point, wait seconds, crouch, look at]
			target = nxt[0]
			wait_until = now + float(nxt[1])
			crouch = float(nxt[2]) if nxt.size() > 2 else 0.0
			_face(nxt[3] if nxt.size() > 3 else target)
		else:
			target = nxt
			crouch = 0.0
			_face(target)
	else:
		done = true
		queue_free()


func _turn(dt: float, standing: bool) -> void:
	"""turn smoothly towards dir (cars a bit slower, small animals quicker)"""
	var want := atan2(-dir.x, -dir.z)
	var rate := 2.2 if kind == "car" else (6.0 if kind in ["cat", "hare", "hedgehog", "fox"] else 3.5)
	if fled:
		rate *= 1.6
	if standing and now_s() < wait_until and crouch > 0.0:
		rate *= 0.6
	heading = lerp_angle(heading, want, clamp(rate * dt, 0.0, 1.0))
	rotation.y = heading


func _animate(dt: float, spd: float, now: float) -> void:
	"""walking, running, crawling, standing about - persons with hips and upper body swinging against each other (3D-2.7),
	animals with their own ways (hopping, jumping when fleeing, stalking, grazing, sniffing, rooting, sitting up)"""
	var gait: float = spd / max(0.3, speed if not fled else speed / 2.6)
	phase += dt * spd * (5.0 if kind == "person" else (9.0 if kind in ["cat", "hedgehog", "hare"] else 6.5)) / max(0.5, body_root.scale.y)
	var amp: float = clamp(spd / 1.2, 0.0, 1.0) * (0.6 if kind == "person" else 0.55)
	var sw := sin(phase) * amp
	var k: float = clamp(dt * 12.0, 0.0, 1.0)
	var idle: String = idle_kind if now < idle_until else ""
	var leap := kind == "deer" and fled and spd > 2.0                     # a fleeing deer jumps
	for l in legs:
		var want: float = sw * l[1]
		if kind == "hare":
			want = sin(phase * 0.5) * amp * 1.6 * (1 if legs.find(l) < 2 else -1)
		elif leap:
			var air: float = abs(sin(phase * 0.5))
			want = (-0.7 if legs.find(l) < 2 else 0.8) * air + sw * 0.3
		elif kind == "person" and prone > 0.5:
			want = sw * l[1] * 0.5 + 0.2                                   # crawling: legs push a little
		l[0].rotation.x = want
		if l.size() > 2 and l[2] != null:                 # knee bends while the leg swings back (more when running)
			var bend: float = max(0.0, -sin(phase * l[1])) * amp * (1.2 + (0.8 if spd > 2.2 else 0.0)) + crouch * 1.4
			if kind == "person" and idle == "bend":
				bend = 0.5
			l[2].rotation.x = lerp(l[2].rotation.x, bend, k)
	if kind == "person":
		_animate_person(dt, spd, now, sw, amp, k, idle)
	elif kind != "car":
		if stars == null:
			var y: float = abs(sin(phase)) * 0.025 * clamp(gait, 0.0, 1.5)
			var rx := 0.0
			if kind == "hare":
				y = abs(sin(phase * 0.5)) * 0.14 * clamp(gait, 0.0, 1.5)          # hopping
			if leap:
				y = abs(sin(phase * 0.5)) * 0.5
				rx = cos(phase * 0.5) * 0.25 * sign(sin(phase * 0.5))
			if kind == "cat" and spd > 0.05 and spd < 0.9:
				y = -0.05                                                      # stalking: low
			match idle:
				"sit_up":
					rx = 0.85
					y = 0.04
				"sit":
					rx = 0.4
					y = -0.03
				"root":
					y = 0.01 * sin(now * 13.0)
			body_root.position.y = lerp(body_root.position.y, y, k) if not leap and kind != "hare" else y
			body_root.rotation.x = lerp(body_root.rotation.x, rx, clamp(dt * 6.0, 0.0, 1.0))
	# head: grazing (down), rooting, sniffing, looking round, else forward
	if head != null:
		var hx := 0.0
		var hyaw := 0.0
		match idle:
			"graze":
				hx = -0.9 + 0.08 * sin(now * 3.0)
			"root":
				hx = -1.0 + 0.15 * sin(now * 12.0)
				hyaw = 0.25 * sin(now * 2.3)
			"sniff":
				hx = -0.55 + 0.08 * sin(now * 15.0)
				hyaw = 0.4 * sin(now * 1.7)
			"look":
				hyaw = look_yaw * sin(min(1.0, (idle_until - now)) * PI)
			"phone":
				hx = -0.25
			"sit_up":
				hx = -0.6
		if kind == "person" and (now < startle_until or emote == "caught" and now < emote_until):
			hx = 0.15
		head.rotation.x = lerp(head.rotation.x, hx, clamp(dt * 4.0, 0.0, 1.0))
		head.rotation.y = lerp(head.rotation.y, hyaw, clamp(dt * 3.0, 0.0, 1.0))
	if tail != null:
		tail.rotation.y = sin(now * (9.0 if kind == "dog" else 2.0)) * (0.5 if kind == "dog" else 0.15)


func _animate_person(dt: float, spd: float, now: float, sw: float, amp: float, k: float, idle: String) -> void:
	var run_f: float = clamp((spd - 1.8) / 1.5, 0.0, 1.0)
	var jog := variant == "jogger"
	var bob: float = abs(sin(phase)) * (0.025 + 0.03 * run_f) * clamp(spd / max(0.3, speed), 0.0, 1.5)
	var em: String = emote if now < emote_until else ""
	var jump := 0.0
	if em == "goal":
		jump = abs(sin(now * 7.0)) * 0.18
	body_root.position.y = (-0.5 * crouch * body_root.scale.y + bob + jump) * (1.0 - prone) + 0.12 * prone
	body_root.rotation.x = -1.35 * prone
	if hips != null:                                                      # hips and upper body swing against each other
		hips.rotation.y = sw * 0.2 * (1.0 - prone)
		hips.rotation.z = sin(phase) * 0.035 * amp
		torso.rotation.y = -sw * 0.25 * (1.0 - prone)
		var lean := -0.3 * crouch - 0.28 * run_f - (0.1 if jog and spd > 0.5 else 0.0)
		if idle == "bend":
			lean = -1.0
		if now < startle_until or em == "caught":
			lean = 0.12
		torso.rotation.x = lerp(torso.rotation.x, lean, k)
	for a in arms:
		var side: int = a[1]
		var sx := -sw * side * (1.2 if jog or run_f > 0.3 else 0.8)
		var ex := -(0.25 + (0.9 if jog else 0.0) + 0.9 * run_f)
		var sz := 0.0
		if prone > 0.5:                                                   # crawling: arms reach forward in turn
			sx = -2.7 + sin(phase + (0.0 if side > 0 else PI)) * 0.5
			ex = -0.3
		elif now < startle_until or em == "caught":                          # startled / caught: hands up
			sx = -2.7
			ex = -0.4
			sz = 0.35 * side
		elif em == "goal":                                                 # cheering
			sx = -2.9 + 0.3 * sin(now * 10.0 + side)
			ex = -0.2
			sz = 0.3 * side
		elif em == "throw" and side > 0:                                   # throwing a stone
			var f: float = clamp(1.0 - (emote_until - now) / 0.6, 0.0, 1.0)
			sx = lerp(-2.9, 0.6, f)
			ex = -0.3
		elif idle == "phone" and side > 0:                                 # on the phone
			sx = -0.4
			ex = -2.3
			sz = 0.25
		elif side > 0 and now < wait_until and crouch == 0.0 and _at_door():   # at a door: reaches for the handle
			sx = -1.4
			ex = -0.35
		elif phone_out and side > 0:                                       # walking with the phone light ahead
			sx = -0.9
			ex = -0.9
		elif idle == "bend":
			sx = -0.7
			ex = -0.2
		a[0].rotation.x = lerp(a[0].rotation.x, sx, k)
		a[0].rotation.z = lerp(a[0].rotation.z, sz, k)
		if a.size() > 2:
			a[2].rotation.x = lerp(a[2].rotation.x, ex, k)
	if torch != null:
		torch.light_energy = 3.0 if crouch > 0.5 and int(now * 3.0) % 4 != 0 else 0.0


func _at_door() -> bool:
	var d = main.obj.get("door", null)
	return d != null and d != Vector3.ZERO and Vector2(position.x - d.x, position.z - d.z).length() < 1.6


func startle() -> void:
	"""the light went on: stop, look at it, hands up for a moment (people only)"""
	if kind == "person" and not controlled:
		startle_until = now_s() + randf_range(0.6, 1.2)


func play_emote(e: String, secs: float) -> void:
	emote = e
	emote_until = now_s() + secs


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


# ---- the bloodless rifle of the wildlife watching ------------------------------------------------------------------
func hit_spheres() -> Array:
	"""where the rifle can hit: [height, radius] (people and cars too - so a shot at them is noticed and stopped)"""
	if kind == "person":
		var k: float = body_root.scale.y
		return [[0.45 * k, 0.3 * k], [1.05 * k, 0.33 * k], [1.6 * k, 0.25 * k]]
	if kind == "car":
		return [[0.8, 2.2]]
	return [[body_h, body_r]]


func hit() -> int:
	"""hit by the bloodless rifle: a hop with a turn, stars round the head - then away. Points (0 = already dizzy)."""
	if kind == "person" or kind == "car":
		return 0
	var t := now_s()
	if t < dizzy_until:
		return 0
	dizzy_until = t + 2.6
	hop_t = t
	wait_until = max(wait_until, dizzy_until)
	stars = Node3D.new()
	stars.position = Vector3(0, body_h + (0.75 if kind == "deer" else 0.35), 0)
	add_child(stars)
	var sm := StandardMaterial3D.new()
	sm.albedo_color = Color(1.0, 0.9, 0.2)
	sm.emission_enabled = true
	sm.emission = Color(1.0, 0.85, 0.2)
	sm.emission_energy_multiplier = 1.5
	for i in range(5):
		var st := MeshInstance3D.new()
		var pm := PrismMesh.new()
		pm.size = Vector3(0.12, 0.12, 0.03)
		st.mesh = pm
		st.material_override = sm
		st.layers = 1
		var a := i * TAU / 5.0
		st.position = Vector3(cos(a) * 0.3, 0, sin(a) * 0.3)
		stars.add_child(st)
	return int(main.POINTS.get(kind, 10))


func _dizzy(dt: float, t: float) -> void:
	stars.rotation.y += dt * 7.0
	var h := t - hop_t
	if h < 0.7:
		body_root.position.y = sin(h / 0.7 * PI) * 0.7
		body_root.rotation.y = h / 0.7 * TAU
	else:
		body_root.position.y = 0.0
		body_root.rotation.y = 0.0
		body_root.rotation.z = 0.12 * sin(t * 9.0)          # wobbly
	if t >= dizzy_until:
		stars.queue_free()
		stars = null
		body_root.rotation = Vector3.ZERO
		fled = false
		scare()
