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
var puppet := false           # replay (recorder.gd, 3D-3.27): position and pose are set from outside, only the animation runs
# ---- joints and extras of a person (from 3D-2.7) ----
var hips: Node3D = null
var torso: Node3D = null
var lamp: SpotLight3D = null  # headlamp or phone light at night
var lamp_mat: StandardMaterial3D = null
var phone_out := false        # walks with the phone light in the hand (arm held forward)
var startle_until := 0.0      # the light went on: startled, arms up for a moment
var gait_amp := 0.0           # persons (3D-3.21): swing of the legs, matched to the speed (no sliding feet)
var gait_fs := 0.0            # steps per second
var want_heading := 0.0       # players: where the stick points (the head turns there first)
var last_spd := 0.0
var lean_acc := 0.0           # leaning into a start, back when stopping
var seed_t := randf() * 10.0  # standing: breathing and shifting the weight, not all in step
var power := ""               # players: «cloak» / «turbo» for a few seconds (game.gd, 3D-3.21)
var player_lamp := false      # players: the torch is on (night round, 3D-3.25)
var handicap := 0             # players: 0 … 2 - a little slower (game.gd, 3D-3.25)
var gear_speed := 1.0         # players: a camouflage thing or the stolen bike makes slower (gameplus.gd, 3D-4.x)
var gear_norun := false       # ... the cardboard box: no running
var gear_pmin := 0            # ... the postures it allows (box: only crouching, umbrella: no crawling)
var gear_pmax := 2
static var npc_camo := false   # szenenplus.gd «Tarnen»: the next figure built wears the camouflage clothes of the players
var power_until := 0.0
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


const PERSON_VARIANTS := ["child", "jogger", "cyclist", "stroller", "drunk", "courier", "police", "burglar", "elderly"]   # 3D-3.95: elderly
var _eye_t := 0.0                          # 3D-3.95: eye shine follows where the animal looks
var _bike_lamps := false
var bike_lamp: Array = []                 # [spot, front material, rear material]
const CAR_VARIANTS := ["tractor", "moto", "van"]
var wheels: Array = []        # cyclist, stroller: wheels that turn
var carry := false            # courier: holds the box in front with both hands
var _lie_k := 0.0             # 3D-4.4: 0 standing … 1 lying (deer bedded down, simreal.gd «deer_bedded»)
# ---- 3D-4.12 «Figuren»: a real figure with a skeleton (figur.gd) on «mittel» and better, the old one on «einfach» ----
const Figur = preload("res://scripts/figur.gd")
var fig = null                # the figure with a skeleton (null = built from shapes)
var demo := -1.0              # tests (figur.gd «row»): walks on the spot at this speed
var tag_p = null              # players: the dictionary of game.gd (name, role, team above the head)
var tag_col := Color.WHITE
var tag_lb: Label3D = null
var tag_ring: MeshInstance3D = null
var tag_t := 0.0
var _glance_until := 0.0      # persons look round now and then (towards the camera when sneaking)
var _glance_next := 0.0
var _glance_yaw := 0.0
var _want_c := 0.0            # visitors: the posture of the next point of the route - changes smoothly
var _want_p := 0.0
var _post_smooth := false
var _jacket_c := Color(0.3, 0.3, 0.3)
var _cloth_t := 26.0


func setup(m, k: String, from: Vector3, to: Vector3, spd: float) -> void:
	main = m
	kind = k
	if kind in PERSON_VARIANTS:
		variant = kind
		kind = "person"
	elif kind in CAR_VARIANTS:                          # tractor, motorbike, van (3D-3.39): drive like a car
		variant = kind
		kind = "car"
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
			radius = 1.2 if variant != "moto" else 0.6
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
	var camo: bool = (controlled and bool(look.get("camo", false))) or (npc_camo and not controlled)
	var jacket: Color = Color(0.33, 0.38, 0.22) if camo else (player_color if player_color.a > 0.0 else (_pick("sport") if jog else _pick("jacket")))
	if variant == "police":
		jacket = Color(0.1, 0.13, 0.25)
	elif variant == "burglar":                                  # dark clothes, hood up (3D-3.40)
		jacket = Color(0.1, 0.1, 0.11)
	elif variant == "courier":
		jacket = [Color(0.85, 0.15, 0.1), Color(0.95, 0.55, 0.1), Color(0.1, 0.55, 0.3)][randi() % 3]
	elif variant == "cyclist":
		jacket = _pick("sport")
	var shirt: Color = [Color(0.9, 0.9, 0.88), Color(0.2, 0.25, 0.35), Color(0.6, 0.15, 0.15), Color(0.85, 0.75, 0.4)][randi() % 4]
	var trousers: Color = Color(0.3, 0.3, 0.2) if camo else (Color(0.1, 0.1, 0.12) if jog or variant == "burglar" else _pick("trousers"))
	var skin := _pick("skin")
	var hair := _pick("hair")
	var shoe: Color = Color(0.95, 0.95, 0.95) if jog else [Color(0.12, 0.1, 0.09), Color(0.35, 0.22, 0.12), Color(0.2, 0.2, 0.22)][randi() % 3]
	var cloth_t := 26.0 - (3.0 if cold else 0.0) + (2.0 if jog else 0.0)
	if main.simreal != null:
		cloth_t = main.simreal.cloth_t(cloth_t, jog)                    # 3D-4.4: clothes insulate (cooler than the skin)
	var old_ := variant == "elderly"                                      # 3D-3.95: more kinds of people
	var shorts: bool = main.ambient > 21.0 and not wet and not kid and not old_ and variant not in ["police", "burglar", "courier"] and randf() < 0.45
	var coat: bool = cold and not jog and not kid and variant == "" and randf() < 0.3
	if old_:
		hair = Color(0.78, 0.78, 0.76) if randf() < 0.7 else Color(0.55, 0.55, 0.53)
	var wide := randf_range(0.9, 1.15) if not kid else 1.0                  # build: slim … sturdy
	var tall := randf_range(0.93, 1.07)
	if controlled and not look.is_empty():                                 # 3D-4.12: the own look of a player
		var lc := str(look.get("col", ""))
		if Figur.LOOK_COLS.has(lc) and not camo and not bool(look.get("gold", false)):
			jacket = Figur.LOOK_COLS[lc]
		tall = float(Figur.LOOK_SIZE.get(str(look.get("size", "")), 1.0))
		wide = float(Figur.LOOK_BUILD.get(str(look.get("build", "")), 1.0))
	body_root.scale = Vector3(wide, tall, wide) * (0.62 if kid else 1.0)
	var open_jacket := not jog and not cold and variant not in ["police", "burglar"] and randf() < 0.4
	var hand_c: Color = Color(0.15, 0.15, 0.16) if cold else skin             # gloves in the cold
	_jacket_c = jacket
	_cloth_t = cloth_t
	if Figur.wanted(main):
		_figure_body(jacket, shirt, trousers, skin, hair, shoe, hand_c, cloth_t, shorts, open_jacket, cold, jog, kid, old_, wide)
	else:
		_shape_body(jacket, shirt, trousers, skin, hair, shoe, hand_c, cloth_t, shorts, open_jacket, cold, jog)
	if coat:                                                               # 3D-3.95: a long coat down to the knees
		_part(hips, _cyl(0.2, 0.27, 0.62, 12), Vector3(0, -0.25, 0), jacket.darkened(0.15), cloth_t - 1.0)
	if camo:                                                               # camouflage: darker and brown patches
		for k2 in range(7):
			var pc: Color = Color(0.2, 0.24, 0.13) if k2 % 2 == 0 else Color(0.38, 0.3, 0.18)
			var a2 := randf() * TAU
			_part(torso, _sph(0.07, 0.05), Vector3(cos(a2) * 0.16, randf_range(0.05, 0.45), sin(a2) * 0.12), pc, cloth_t, Vector3(0, a2, 0), Vector3(1.4, 1.0, 0.4))
	if (controlled and bool(look.get("pack", false))) or (not jog and not kid and not controlled and randf() < 0.35):   # backpack
		add_backpack(jacket)
	var style := randi() % 5
	var hooded: bool = ((cold or wet) and not jog and randf() < 0.45) or variant == "burglar"
	if controlled and not look.is_empty():                                  # a player chose
		hooded = look.get("hat", "") == "hood"
		style = 3 if look.get("hat", "") == "cap" else 0
	if hooded:                                                             # hood up
		add_hood(jacket)
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
	_person_extras(jacket, cloth_t)
	if wet and not kid and not jog and variant in ["", "elderly"] and not controlled and randf() < 0.55:   # 3D-3.95: umbrella in the rain
		add_umbrella()
	if old_:                                                              # walking stick
		_part(arms[1][2], _cyl(0.014, 0.014, 0.9, 6), Vector3(0.02, -0.75, -0.1), Color(0.3, 0.2, 0.12), main.ambient)
	# at night some people carry a light: a headlamp or the light of the phone (MoveEye sees it)
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


func _shape_body(jacket: Color, shirt: Color, trousers: Color, skin: Color, hair: Color, shoe: Color, hand_c: Color, cloth_t: float,
		shorts: bool, open_jacket: bool, cold: bool, jog: bool) -> void:
	"""the old figure from shapes (Grafik «einfach», the Pi): joints with boxes, capsules and spheres"""
	# ---- hips and legs ----
	hips = _pivot(body_root, Vector3(0, 0.95, 0))
	_part(hips, _caps(0.165, 0.3), Vector3(0, 0.02, 0), trousers, cloth_t, Vector3(0, 0, PI / 2), Vector3(1, 1, 0.78))
	for s in [-1, 1]:
		var hip := _pivot(hips, Vector3(0.1 * s, -0.03, 0))
		_part(hip, _caps(0.078, 0.5), Vector3(0, -0.22, 0), trousers, cloth_t - 1.0)            # thigh
		var knee := _pivot(hip, Vector3(0, -0.46, 0))
		_part(knee, _caps(0.062, 0.46), Vector3(0, -0.21, 0), skin if shorts else trousers, 31.0 if shorts else cloth_t - 1.5)   # shin (bare with shorts)
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


func _figure_body(jacket: Color, shirt: Color, trousers: Color, skin: Color, hair: Color, shoe: Color, hand_c: Color, cloth_t: float,
		shorts: bool, open_jacket: bool, cold: bool, jog: bool, kid: bool, old_: bool, wide: float) -> void:
	"""3D-4.12: the joints only (the same places as the old figure) + one skinned body with a skeleton (figur.gd)"""
	hips = _pivot(body_root, Vector3(0, 0.95, 0))
	for s in [-1, 1]:
		var hip := _pivot(hips, Vector3(0.1 * s, -0.03, 0))
		var knee := _pivot(hip, Vector3(0, -0.46, 0))
		legs.append([hip, s, knee])
	torso = _pivot(body_root, Vector3(0, 0.98, 0))
	for s in [-1, 1]:
		var sh := _pivot(torso, Vector3(0.245 * s, 0.48, 0))
		var el := _pivot(sh, Vector3(0, -0.3, 0))
		arms.append([sh, s, el])
	head = _pivot(torso, Vector3(0, 0.6, 0))
	var q: String = str(main.quality)
	var strong := wide > 1.06
	var p := {"skin": skin, "jacket": jacket, "shirt": shirt, "trousers": trousers, "shoe": shoe, "hand": hand_c, "hair": hair,
			"shorts": shorts, "open": open_jacket, "short_sleeves": jog and not cold, "gloves": cold, "cloth_t": cloth_t,
			"seg": {"medium": 8, "nice": 10, "ultra": 12}.get(q, 10),
			"sh": 1.0 if kid else randf_range(0.93, 1.07), "hp": 1.0 if kid else randf_range(0.94, 1.1),
			"bl": 0.0 if kid or jog else (randf_range(0.012, 0.045) if randf() < (0.5 if old_ or strong else 0.25) else 0.0),
			"ch": 0.0 if kid else (randf_range(0.012, 0.03) if randf() < 0.4 else 0.0),
			"lt": randf_range(0.93, 1.08) * (1.06 if strong else 1.0)}
	fig = Figur.new()
	body_root.add_child(fig)
	fig.build(self, p)


func rand_jacket() -> Color:
	return _pick("jacket")


func add_backpack(col: Color) -> void:
	var bp: Color = col.darkened(0.5).lerp(Color(0.2, 0.3, 0.2), 0.5)
	_part(torso, _box(0.3, 0.4, 0.15), Vector3(0, 0.3, 0.19), bp, main.ambient + 3.0)
	_part(torso, _box(0.26, 0.12, 0.05), Vector3(0, 0.18, 0.28), bp.darkened(0.2), main.ambient + 3.0)


func add_hood(col: Color) -> void:
	_part(head, _sph(0.13, 0.27), Vector3(0, 0.18, 0.02), col.darkened(0.1), _cloth_t - 2.0, Vector3.ZERO, Vector3(1.0, 1.0, 1.05))
	_part(torso, _sph(0.11, 0.12), Vector3(0, 0.55, 0.12), col.darkened(0.1), _cloth_t)


func add_umbrella() -> void:
	var uc: Color = [Color(0.1, 0.1, 0.12), Color(0.55, 0.1, 0.12), Color(0.1, 0.25, 0.55), Color(0.85, 0.75, 0.2)][randi() % 4]
	_part(torso, _cyl(0.012, 0.012, 0.85, 6), Vector3(0.12, 0.85, -0.12), Color(0.15, 0.15, 0.15), main.ambient)
	_part(torso, _cyl(0.02, 0.55, 0.22, 16), Vector3(0.12, 1.28, -0.12), uc, main.ambient)


static func clean_look(m, out: Dictionary) -> Dictionary:
	"""game.gd: jacket colour, size and build of a player (3D-4.12, figur.gd)"""
	return Figur.clean_look(m, out)


static func tag(p: Dictionary, col: Color) -> void:
	"""game.gd: name, role and team colour above the head of a player - only players and the operator see it"""
	Figur.tag(p, col)


func _person_extras(jacket: Color, cloth_t: float) -> void:
	"""bike, pram, pizza box, police vest (3D-3.39)"""
	match variant:
		"police":
			for y in [0.18, 0.4]:                                              # reflective stripes, a cap
				_part(torso, _caps(0.21, 0.36), Vector3(0, y, 0), Color(0.85, 0.9, 0.2), cloth_t, Vector3.ZERO, Vector3(1.08, 0.12, 0.7))
			_part(head, _cyl(0.12, 0.12, 0.06, 16), Vector3(0, 0.25, 0), Color(0.08, 0.1, 0.2), 27.0)
			_part(head, _box(0.2, 0.015, 0.1), Vector3(0, 0.225, -0.1), Color(0.05, 0.05, 0.05), 27.0)
			if main.is_dark() and not preview:
				add_torch()
		"courier":
			carry = true
			_part(torso, _box(0.36, 0.06, 0.36), Vector3(0, 0.18, -0.32), Color(0.85, 0.75, 0.55), 45.0)   # warm pizza box
			_part(torso, _box(0.34, 0.4, 0.22), Vector3(0, 0.3, 0.2), jacket.darkened(0.3), cloth_t)          # delivery bag
			_part(head, _sph(0.125, 0.16), Vector3(0, 0.22, 0.0), jacket.lightened(0.2), 26.0)               # helmet
		"stroller":
			var pr := _pivot(body_root, Vector3(0, 0, -0.85))
			_part(pr, _box(0.5, 0.32, 0.75), Vector3(0, 0.62, 0), Color(0.2, 0.25, 0.32), main.ambient + 2.0)
			_part(pr, _sph(0.3, 0.3), Vector3(0, 0.82, 0.2), Color(0.18, 0.22, 0.3), main.ambient + 2.0, Vector3.ZERO, Vector3(0.85, 1.0, 1.0))   # hood
			_part(pr, _sph(0.08), Vector3(0, 0.8, -0.05), Color(0.95, 0.8, 0.7), 34.0)                         # the baby, warm
			_part(pr, _cyl(0.015, 0.015, 0.5, 6), Vector3(0, 0.95, 0.5), Color(0.1, 0.1, 0.1), main.ambient, Vector3(0, 0, PI / 2))   # handle
			for sx in [-0.22, 0.22]:
				_part(pr, _cyl(0.015, 0.015, 0.5, 6), Vector3(sx, 0.75, 0.42), Color(0.1, 0.1, 0.1), main.ambient, Vector3(-0.6, 0, 0))
				for z in [-0.28, 0.3]:
					var w := _pivot(pr, Vector3(sx * 1.05, 0.14, z))
					_part(w, _cyl(0.14, 0.14, 0.04, 14), Vector3.ZERO, Color(0.08, 0.08, 0.08), main.ambient + 3.0, Vector3(0, 0, PI / 2))
					wheels.append([w, 0.14])
		"cyclist":
			var bk := _pivot(body_root, Vector3.ZERO)
			var fc: Color = [Color(0.1, 0.4, 0.75), Color(0.75, 0.1, 0.1), Color(0.15, 0.15, 0.15), Color(0.9, 0.9, 0.9)][randi() % 4]
			for z in [-0.55, 0.55]:
				var w2 := _pivot(bk, Vector3(0, 0.34, z))
				_part(w2, _cyl(0.34, 0.34, 0.035, 20), Vector3.ZERO, Color(0.06, 0.06, 0.06), main.ambient + 4.0, Vector3(0, 0, PI / 2))
				_part(w2, _cyl(0.05, 0.05, 0.05, 8), Vector3.ZERO, Color(0.6, 0.6, 0.62), main.ambient + 2.0, Vector3(0, 0, PI / 2))
				wheels.append([w2, 0.34])
			_part(bk, _cyl(0.022, 0.022, 0.75, 6), Vector3(0, 0.55, -0.05), fc, main.ambient + 1.0, Vector3(PI / 2 - 0.25, 0, 0))   # top tube
			_part(bk, _cyl(0.022, 0.022, 0.62, 6), Vector3(0, 0.48, 0.12), fc, main.ambient + 1.0, Vector3(0.35, 0, 0))            # seat tube
			_part(bk, _cyl(0.022, 0.022, 0.6, 6), Vector3(0, 0.48, -0.45), fc, main.ambient + 1.0, Vector3(-0.3, 0, 0))            # fork
			_part(bk, _box(0.12, 0.04, 0.24), Vector3(0, 0.86, 0.08), Color(0.08, 0.08, 0.08), main.ambient + 3.0)              # saddle
			_part(bk, _cyl(0.016, 0.016, 0.5, 6), Vector3(0, 0.98, -0.5), Color(0.1, 0.1, 0.1), main.ambient, Vector3(0, 0, PI / 2))   # handlebar
			_part(head, _sph(0.12, 0.14), Vector3(0, 0.23, 0.0), fc.lightened(0.3), 27.0)                          # helmet
			body_root.position.y = -0.06
			if not preview:                                                    # 3D-3.95: bike lamps (on at night)
				var fl := MeshInstance3D.new()
				fl.mesh = _sph(0.035)
				var flm := StandardMaterial3D.new()
				flm.albedo_color = Color(1, 1, 0.95)
				flm.emission_enabled = true
				flm.emission = Color(1, 1, 0.95)
				fl.material_override = flm
				fl.position = Vector3(0, 0.8, -0.62)
				bk.add_child(fl)
				var rl := MeshInstance3D.new()
				rl.mesh = _sph(0.03)
				var rlm := StandardMaterial3D.new()
				rlm.albedo_color = Color(0.9, 0.05, 0.05)
				rlm.emission_enabled = true
				rlm.emission = Color(1, 0.05, 0.05)
				rl.material_override = rlm
				rl.position = Vector3(0, 0.75, 0.62)
				bk.add_child(rl)
				var bl := SpotLight3D.new()
				bl.spot_range = 12.0
				bl.spot_angle = 22.0
				bl.position = Vector3(0, 0.8, -0.64)
				bl.rotation = Vector3(-0.12, 0, 0)
				bk.add_child(bl)
				bike_lamp = [bl, flm, rlm]


func _build_animal() -> void:
	# height of the back, body length, colour, body temperature (fur), leg thickness
	var spec := {"fox": [0.42, 0.62, Color(0.82, 0.38, 0.12), 28.0, 0.035], "deer": [0.95, 1.05, Color(0.58, 0.4, 0.23), 29.0, 0.042],
			"boar": [0.62, 1.05, Color(0.22, 0.19, 0.16), 28.0, 0.07], "cat": [0.26, 0.4, Color(0.35, 0.33, 0.3), 29.0, 0.025],
			"dog": [0.5, 0.7, Color(0.45, 0.35, 0.22), 30.0, 0.045], "badger": [0.3, 0.7, Color(0.42, 0.42, 0.42), 28.0, 0.05],
			"hare": [0.28, 0.42, Color(0.55, 0.45, 0.32), 30.0, 0.03], "hedgehog": [0.12, 0.26, Color(0.35, 0.28, 0.2), 27.0, 0.02],
			# 3D-3.27: wolf, marten, squirrel
			"wolf": [0.66, 1.0, Color(0.5, 0.48, 0.44), 30.0, 0.05], "marten": [0.17, 0.48, Color(0.34, 0.22, 0.12), 30.0, 0.02],
			"squirrel": [0.13, 0.2, Color(0.62, 0.28, 0.1), 31.0, 0.014],
			# 3D-3.39: cow, sheep, horse, chamois, ibex, lynx
			"cow": [1.05, 1.6, Color(0.95, 0.93, 0.9), 32.0, 0.06], "sheep": [0.55, 0.85, Color(0.9, 0.88, 0.8), 29.0, 0.032],
			"horse": [1.25, 1.55, Color(0.45, 0.28, 0.15), 32.0, 0.06], "chamois": [0.7, 0.9, Color(0.38, 0.29, 0.2), 30.0, 0.035],
			"ibex": [0.8, 1.05, Color(0.52, 0.45, 0.36), 30.0, 0.045], "lynx": [0.55, 0.8, Color(0.72, 0.56, 0.38), 30.0, 0.045]}
	var s: Array = spec.get(kind, spec["fox"])
	var hb: float = s[0]
	var L: float = s[1]
	var col: Color = s[2]
	if kind == "cat":
		col = [Color(0.35, 0.33, 0.3), Color(0.85, 0.5, 0.2), Color(0.1, 0.1, 0.1), Color(0.9, 0.88, 0.85)][randi() % 4]
	elif kind == "dog":
		col = [Color(0.45, 0.35, 0.22), Color(0.1, 0.1, 0.1), Color(0.85, 0.75, 0.55), Color(0.6, 0.55, 0.5)][randi() % 4]
	elif kind == "cow":
		col = [Color(0.95, 0.93, 0.9), Color(0.55, 0.36, 0.2), Color(0.7, 0.55, 0.4)][randi() % 3]
	elif kind == "horse":
		col = [Color(0.45, 0.28, 0.15), Color(0.2, 0.14, 0.1), Color(0.75, 0.72, 0.68), Color(0.6, 0.42, 0.25)][randi() % 4]
	col = col.lerp(col.lightened(0.15), randf())
	var t: float = s[3]
	var lw: float = s[4]
	var sc := randf_range(0.9, 1.1)
	body_root.scale = Vector3.ONE * sc
	var bodyr := hb * (0.32 if kind != "boar" else 0.45)
	if kind in ["cow", "sheep"]:
		bodyr = hb * 0.42
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
	if kind in ["fox", "deer", "hare", "wolf"]:                               # light belly / chest
		_part(body_root, _caps(bodyr * 0.72, L * 0.65), Vector3(0, hb - bodyr * 0.42, -L * 0.05), col.lightened(0.55), t - 1.0, Vector3(PI / 2, 0, 0))
	if kind == "boar":                                                         # bristle ridge
		_part(body_root, _box(0.06, 0.08, L * 0.8), Vector3(0, hb + bodyr * 0.95, -L * 0.05), col.darkened(0.3), t - 3.0)
	if kind == "badger":
		_part(body_root, _caps(bodyr * 0.8, L * 0.9), Vector3(0, hb - bodyr * 0.3, 0), Color(0.12, 0.12, 0.12), t - 1.0, Vector3(PI / 2, 0, 0))
	if kind == "cow":                                                          # patches and the udder
		if col.r > 0.9:
			for i in range(6):
				var a := randf() * TAU
				_part(body_root, _sph(bodyr * 0.45, bodyr * 0.3), Vector3(cos(a) * bodyr * 0.95, hb + sin(a) * bodyr * 0.7, randf_range(-L * 0.4, L * 0.4)),
						Color(0.08, 0.08, 0.08), t - 1.0, Vector3(0, 0, a + PI / 2), Vector3(1.4, 1.0, 1.4))
		_part(body_root, _sph(bodyr * 0.32), Vector3(0, hb - bodyr * 0.9, L * 0.3), Color(0.95, 0.7, 0.7), t + 2.0, Vector3.ZERO, Vector3(1.0, 0.8, 1.2))
	if kind == "sheep":                                                        # thick wool
		for i in range(10):
			_part(body_root, _sph(bodyr * 0.55), Vector3(randf_range(-0.6, 0.6) * bodyr, hb + randf_range(-0.3, 0.75) * bodyr, randf_range(-0.45, 0.45) * L), col.darkened(randf() * 0.08), t - 4.0)
	if kind == "lynx":                                                         # spots
		for i in range(12):
			var a2 := randf() * PI
			_part(body_root, _sph(0.025), Vector3(cos(a2) * bodyr * 1.0, hb + sin(a2) * bodyr * 0.9, randf_range(-0.4, 0.4) * L), col.darkened(0.55), t - 1.0)
	if kind == "horse":                                                        # mane along the neck comes below
		pass
	for i in range(4):
		var fx := 0.6 * bodyr * (1 if i % 2 == 0 else -1)
		var fz := (-L * 0.38) if i < 2 else (L * 0.38)
		var p := _pivot(body_root, Vector3(fx, hb, fz))
		var legc: Color = Color(0.1, 0.08, 0.07) if kind in ["fox", "sheep"] else col.darkened(0.25)
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
	elif kind in ["horse", "chamois", "ibex"]:                                  # a neck like the deer, the horse a strong one
		var nk: float = {"horse": 0.13, "chamois": 0.07, "ibex": 0.09}[kind]
		var nl: float = {"horse": 0.72, "chamois": 0.4, "ibex": 0.42}[kind]
		var na := -0.75 if kind == "horse" else -0.6
		_part(head, _caps(nk, nl), Vector3(0, nl * 0.4 * cos(na), nl * 0.4 * sin(na)), col, t, Vector3(na, 0, 0))
		hy = nl * 0.82 * cos(na)
		hz = nl * 0.82 * sin(na)
		if kind == "horse":
			_part(head, _box(0.05, nl * 0.9, 0.12), Vector3(0, nl * 0.45 * cos(na), nl * 0.45 * sin(na) + 0.08), Color(0.1, 0.08, 0.06), t - 4.0, Vector3(na, 0, 0))   # mane
	var hr := bodyr * (0.75 if kind != "boar" else 0.9)
	if kind == "deer":
		hr = 0.12                                                          # a slim head on the long neck
	elif kind in ["horse", "cow"]:
		hr = 0.17 if kind == "horse" else 0.2
	elif kind in ["chamois", "ibex", "sheep"]:
		hr = 0.1 if kind != "sheep" else 0.12
	_part(head, _sph(hr), Vector3(0, hy, hz), col, t + 2.0)
	if kind == "marten":                                                       # the cream patch on the throat
		_part(body_root, _sph(bodyr * 0.7), Vector3(0, hb - bodyr * 0.1, -L * 0.42), Color(0.93, 0.85, 0.6), t, Vector3.ZERO, Vector3(1.0, 0.9, 1.4))
	if kind in ["fox", "dog", "cat", "badger", "hare", "wolf", "marten", "squirrel", "cow", "sheep", "lynx"]:   # neck
		_part(head, _caps(hr * 0.62, max(0.05, Vector2(hy, hz).length()) + hr * 0.6), Vector3(0, hy * 0.5, hz * 0.5), col, t + 1.0, Vector3(-PI / 2 + atan2(hy, -hz), 0, 0))
	if kind == "fox":                                                          # white chin and cheeks
		_part(head, _sph(hr * 0.55), Vector3(0, hy - hr * 0.55, hz - hr * 0.55), Color(0.95, 0.93, 0.88), t + 1.0, Vector3.ZERO, Vector3(1.4, 0.8, 1.2))
	if kind in ["cow", "chamois", "ibex", "sheep", "horse"]:                     # ears to the side / up
		for s7 in [-1, 1]:
			var ear3 := PrismMesh.new()
			ear3.size = Vector3(hr * 0.5, hr * (1.1 if kind == "horse" else 0.7), hr * 0.18)
			_part(head, ear3, Vector3(hr * 0.75 * s7, hy + hr * (0.8 if kind == "horse" else 0.45), hz + hr * 0.2), col.darkened(0.15) if kind != "sheep" else Color(0.15, 0.13, 0.12), t - 2.0, Vector3(0, 0, -0.9 * s7 if kind in ["cow", "sheep"] else -0.2 * s7))
	if kind == "cow":                                                          # short horns
		for s8 in [-1, 1]:
			_part(head, _cyl(0.008, 0.025, 0.14, 6), Vector3(hr * 0.6 * s8, hy + hr * 0.75, hz + hr * 0.1), Color(0.9, 0.88, 0.78), t - 8.0, Vector3(0, 0, -1.0 * s8))
	if kind == "chamois":                                                      # small black hooked horns
		for s8 in [-1, 1]:
			_part(head, _cyl(0.006, 0.014, 0.16, 5), Vector3(hr * 0.3 * s8, hy + hr * 1.3, hz + hr * 0.1), Color(0.05, 0.05, 0.05), t - 8.0, Vector3(0.15, 0, 0))
			_part(head, _cyl(0.004, 0.008, 0.07, 5), Vector3(hr * 0.3 * s8, hy + hr * 2.0, hz + hr * 0.4), Color(0.05, 0.05, 0.05), t - 8.0, Vector3(1.6, 0, 0))
	if kind == "ibex":                                                         # the big curved horns, backwards
		for s8 in [-1, 1]:
			for i in range(5):
				var a3 := 0.25 + i * 0.32
				_part(head, _cyl(0.022 - i * 0.003, 0.026 - i * 0.003, 0.13, 6), Vector3(hr * 0.3 * s8, hy + hr * 0.9 + sin(a3) * 0.2, hz + hr * 0.1 + (1.0 - cos(a3)) * 0.25),
						Color(0.45, 0.4, 0.32), t - 8.0, Vector3(a3, 0, 0))
	if kind == "lynx":                                                         # ear tufts, whiskers
		for s8 in [-1, 1]:
			_part(head, _cyl(0.004, 0.006, 0.06, 4), Vector3(hr * 0.5 * s8, hy + hr * 1.5, hz), Color(0.05, 0.05, 0.05), t - 6.0)
	if kind == "boar" or kind == "badger":                                     # small round ears
		for s6 in [-1, 1]:
			_part(head, _sph(hr * 0.25), Vector3(hr * 0.55 * s6, hy + hr * 0.7, hz + hr * 0.2), col.darkened(0.2), t - 2.0, Vector3.ZERO, Vector3(1.0, 1.2, 0.4))
	var snout := col.darkened(0.1) if kind != "fox" else col
	if kind == "sheep":
		snout = Color(0.15, 0.13, 0.12)
		_part(head, _sph(hr * 1.02), Vector3(0, hy, hz), Color(0.15, 0.13, 0.12), t + 2.0)               # dark face
	if kind == "cow":
		snout = Color(0.85, 0.65, 0.6)
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
	if kind in ["fox", "cat", "dog", "wolf", "marten", "squirrel", "lynx"] and not floppy:   # pointed ears (fox: black tips)
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
	elif kind == "wolf":                                                       # a bushy tail, hanging down
		_part(tail, _caps(bodyr * 0.42, L * 0.62), Vector3(0, -0.2, L * 0.16), col.darkened(0.1), t - 4.0, Vector3(0.45, 0, 0))
	elif kind == "marten":                                                     # long bushy tail, held low
		_part(tail, _caps(bodyr * 0.55, L * 0.75), Vector3(0, -0.03, L * 0.33), col.darkened(0.25), t - 4.0, Vector3(PI / 2 - 0.15, 0, 0))
	elif kind in ["cow", "horse"]:                                             # a long hanging tail (horse: full of hair)
		_part(tail, _caps(0.02 if kind == "cow" else 0.06, L * 0.5), Vector3(0, -0.3, 0.06), col.darkened(0.2) if kind == "cow" else Color(0.1, 0.08, 0.06), t - 4.0, Vector3(0.15, 0, 0))
		if kind == "cow":
			_part(tail, _sph(0.05, 0.12), Vector3(0, -0.6, 0.1), Color(0.1, 0.1, 0.1), t - 4.0)
	elif kind in ["lynx", "chamois", "ibex", "sheep"]:                         # short tails (lynx: black tip)
		_part(tail, _caps(0.035, 0.14), Vector3(0, -0.02, 0.06), col, t - 4.0, Vector3(0.6, 0, 0))
		if kind == "lynx":
			_part(tail, _sph(0.035), Vector3(0, -0.06, 0.12), Color(0.05, 0.05, 0.05), t - 4.0)
	elif kind == "squirrel":                                                   # the big tail, curled up over the back
		_part(tail, _caps(0.045, 0.22), Vector3(0, 0.1, 0.05), col, t - 4.0, Vector3(-0.3, 0, 0))
		_part(tail, _caps(0.05, 0.16), Vector3(0, 0.22, -0.02), col.darkened(0.1), t - 4.0, Vector3(-1.1, 0, 0))


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
	if variant == "tractor":
		_build_tractor()
		return
	if variant == "moto":
		_build_moto()
		return
	var van := variant == "van"
	var col: Color = [Color(0.6, 0.1, 0.1), Color(0.75, 0.75, 0.78), Color(0.08, 0.08, 0.1), Color(0.1, 0.25, 0.55), Color(0.85, 0.85, 0.85), Color(0.25, 0.35, 0.25)][randi() % 6]
	if van:
		col = [Color(0.92, 0.92, 0.9), Color(0.85, 0.75, 0.15), Color(0.1, 0.3, 0.6)][randi() % 3]
		_part(body_root, _box(1.95, 1.55, 3.3), Vector3(0, 1.3, 0.65), col, main.ambient + 3.0)        # the high cargo box
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
	if main.simreal != null and not preview and not van:
		main.simreal.note_car(body_root, false)            # 3D-4.4: number plates that reflect


func _headlight(pos: Vector3) -> void:
	var hl := SpotLight3D.new()
	hl.position = pos
	hl.spot_range = 40.0
	hl.spot_angle = 26.0
	hl.light_energy = 0.0
	hl.light_color = Color(1.0, 0.95, 0.85)
	hl.shadow_enabled = false
	body_root.add_child(hl)
	lights.append(hl)
	var lp := _part(body_root, _box(0.22, 0.14, 0.05), pos + Vector3(0, 0, 0.02), Color(1, 1, 0.9), main.ambient + 30.0)
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(1, 1, 0.9)
	lm.emission_enabled = true
	lm.emission = Color(1, 0.97, 0.85)
	lm.emission_energy_multiplier = 0.0
	lp.material_override = lm
	lights.append(lm)


func _build_tractor() -> void:
	var col: Color = [Color(0.15, 0.5, 0.2), Color(0.75, 0.12, 0.1), Color(0.2, 0.35, 0.6)][randi() % 3]
	_part(body_root, _box(0.9, 0.8, 2.0), Vector3(0, 1.0, -0.7), col, 70.0)                       # bonnet (warm engine)
	_part(body_root, _box(1.3, 0.25, 1.2), Vector3(0, 0.95, 0.65), col.darkened(0.2), main.ambient + 6.0)
	_part(body_root, _box(1.2, 1.3, 1.15), Vector3(0, 1.95, 0.65), Color(0.2, 0.25, 0.3), main.ambient + 8.0)   # cab (glass)
	_part(body_root, _box(1.3, 0.08, 1.25), Vector3(0, 2.62, 0.65), col, main.ambient + 4.0)
	_part(body_root, _cyl(0.05, 0.05, 1.2, 8), Vector3(0.35, 1.9, -1.2), Color(0.15, 0.15, 0.15), 120.0)        # exhaust, hot
	for sx in [-1.0, 1.0]:
		_part(body_root, _cyl(0.75, 0.75, 0.45, 18), Vector3(sx * 0.95, 0.75, 0.75), Color(0.07, 0.07, 0.07), main.ambient + 10.0, Vector3(0, 0, PI / 2))
		_part(body_root, _cyl(0.42, 0.42, 0.3, 14), Vector3(sx * 0.75, 0.42, -1.25), Color(0.07, 0.07, 0.07), main.ambient + 10.0, Vector3(0, 0, PI / 2))
		_part(body_root, _cyl(0.3, 0.3, 0.46, 12), Vector3(sx * 0.95, 0.75, 0.75), Color(0.85, 0.75, 0.2), main.ambient + 8.0, Vector3(0, 0, PI / 2))
		_headlight(Vector3(sx * 0.35, 1.25, -1.72))
	_part(body_root, _box(0.06, 0.06, 0.06), Vector3(0, 2.7, 0.65), Color(1.0, 0.6, 0.1), main.ambient + 5.0)   # orange beacon
	body_h = 2.6
	body_r = 1.6


func _build_moto() -> void:
	var col: Color = [Color(0.1, 0.1, 0.1), Color(0.8, 0.1, 0.1), Color(0.1, 0.3, 0.75), Color(0.9, 0.55, 0.1)][randi() % 4]
	for z in [-0.72, 0.72]:
		_part(body_root, _cyl(0.32, 0.32, 0.14, 18), Vector3(0, 0.32, z), Color(0.06, 0.06, 0.06), main.ambient + 10.0, Vector3(0, 0, PI / 2))
	_part(body_root, _box(0.32, 0.4, 1.0), Vector3(0, 0.62, 0.0), col, main.ambient + 4.0)
	_part(body_root, _box(0.3, 0.3, 0.45), Vector3(0, 0.5, -0.05), Color(0.3, 0.3, 0.32), 80.0)            # engine, hot
	_part(body_root, _cyl(0.05, 0.05, 0.8, 8), Vector3(0.2, 0.38, 0.45), Color(0.6, 0.6, 0.6), 110.0, Vector3(PI / 2, 0, 0))   # exhaust
	_part(body_root, _cyl(0.02, 0.02, 0.7, 6), Vector3(0, 1.05, -0.62), Color(0.1, 0.1, 0.1), main.ambient, Vector3(0, 0, PI / 2))
	# the rider (simple): legs, body, arms to the handlebar, helmet
	var rc: Color = [Color(0.1, 0.1, 0.1), Color(0.3, 0.3, 0.35), Color(0.6, 0.15, 0.1)][randi() % 3]
	for sx in [-1.0, 1.0]:
		_part(body_root, _caps(0.08, 0.6), Vector3(sx * 0.2, 0.7, -0.1), rc, 26.0, Vector3(1.2, 0, 0))
		_part(body_root, _caps(0.06, 0.6), Vector3(sx * 0.22, 1.12, -0.38), rc, 26.0, Vector3(1.0, 0, 0))
	_part(body_root, _caps(0.19, 0.6), Vector3(0, 1.15, 0.05), rc, 27.0, Vector3(-0.45, 0, 0))
	_part(body_root, _sph(0.15, 0.3), Vector3(0, 1.55, -0.15), Color(0.9, 0.9, 0.9) if randf() < 0.5 else col, 25.0)   # helmet
	_headlight(Vector3(0, 0.9, -0.95))
	body_h = 1.5
	body_r = 0.9


# ---- moving --------------------------------------------------------------------------------------------------------
func set_night(night: bool) -> void:
	if not bike_lamp.is_empty():
		bike_lamp[0].light_energy = 5.0 if night else 0.0
		bike_lamp[1].emission_energy_multiplier = 12.0 if night else 0.0
		bike_lamp[2].emission_energy_multiplier = 6.0 if night else 0.0
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
	_step(dt)
	if kind == "person" and not preview and main != null and main.is_dark():
		var tn: float = now_s() + float(get_instance_id() % 97)   # 3D-3.95: lights are not held still - they sweep
		if lamp != null and phone_out:
			lamp.rotation = Vector3(-1.2 + 0.25 * sin(tn * 1.1), 0.5 * sin(tn * 0.7), 0)
		if torch != null and torch.light_energy > 0.0:
			torch.rotation = Vector3(-0.5 + 0.2 * sin(tn * 0.9), 0.6 * sin(tn * 0.55), 0)
	if is_animal() and not preview and main != null and not lights.is_empty():
		_eye_t -= dt
		if _eye_t <= 0.0:                                # 3D-3.95: the eyes glow only when the animal looks into the light
			_eye_t = 0.2
			var base: float = main.eye_shine(global_position) if main.is_dark() else 0.0
			var f := 1.0
			if head != null and base > 0.06:
				var fw: Vector3 = -head.global_transform.basis.z
				var tc: Vector3 = (main.head.global_position - head.global_position).normalized()
				f = pow(maxf(0.0, fw.dot(tc)), 4.0)
			for l in lights:
				if l is StandardMaterial3D:
					l.emission_energy_multiplier = base * f
	if main != null and main.terrain and not preview and is_inside_tree():
		position.y = main.ground_y(position.x, position.z)   # a real place (from 3D-3.4): on the hills
	if fig != null:
		fig.sync(dt)                                         # 3D-4.12: the joints -> the bones, feet on the ground
	if tag_p != null:
		Figur.tag_tick(self, dt)


func _step(dt: float) -> void:
	if done or preview:
		return
	var now := now_s()
	if puppet:
		_animate(dt, cur_speed, now)
		return
	if controlled:
		_player(dt, now)
		return
	if demo >= 0.0:                                       # tests: on the spot
		cur_speed = demo
		_animate(dt, demo, now)
		return
	if _post_smooth:                                      # 3D-4.12: standing <-> crouching <-> crawling smoothly
		var wc := 1.0 if _want_p < prone and prone > 0.3 else _want_c   # getting up from the ground: over the crouch
		crouch = move_toward(crouch, wc, dt * 2.5)
		prone = move_toward(prone, _want_p, dt * 1.6)
		if is_equal_approx(crouch, _want_c) and is_equal_approx(prone, _want_p):
			_post_smooth = false
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
		if main.simreal != null and main.simreal.anim_real and now >= idle_until:   # 3D-4.4: a herd stops together
			if leader.kind == kind and now < leader.idle_until and leader.idle_kind != "":
				idle_kind = leader.idle_kind if randf() < 0.7 else ["look", "graze", "sniff"][randi() % 3]
				idle_until = leader.idle_until + randf_range(-0.5, 1.0)
			elif is_animal() and leader.kind == "person" and leader.cur_speed < 0.1 and randf() < 0.02:
				idle_kind = "sniff"                              # the dog sniffs while its person stands
				idle_until = now + randf_range(1.5, 4.0)
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
	var real_a: bool = is_animal() and main.simreal != null and main.simreal.anim_real   # 3D-4.4: stop and sniff more often
	if kind != "car" and not fled and leader == null and now > next_idle and route.size() >= 0:
		next_idle = now + (randf_range(4.0, 11.0) if real_a else randf_range(8.0, 20.0))
		if randf() < (0.8 if real_a else (0.55 if is_animal() else 0.3)):
			var kinds: Array = {"person": ["look", "look", "phone", "bend"], "deer": ["graze", "graze", "look"], "boar": ["root", "graze"],
					"fox": ["sniff", "look"], "hare": ["sit_up", "graze"], "cat": ["sit", "look"], "dog": ["sniff", "sit"],
					"badger": ["root", "sniff"], "hedgehog": ["sniff"], "wolf": ["look", "sniff", "look"], "marten": ["sniff", "look"],
					"squirrel": ["sit_up", "look", "sit_up"], "cow": ["graze", "graze", "look"], "sheep": ["graze", "graze", "look"],
					"horse": ["graze", "look"], "chamois": ["look", "graze", "look"], "ibex": ["look", "graze"], "lynx": ["look", "sniff", "sit"]}.get(kind, ["look"])
			idle_kind = kinds[randi() % kinds.size()]
			idle_until = now + randf_range(2.0, 5.0)
			if is_animal() and main.is_dark() and main.eye_shine(global_position) > 0.5 and randf() < 0.6:
				idle_kind = "stare"                                  # 3D-3.95: in the light animals stop and stare into it (eyes glow)
				idle_until = now + randf_range(2.5, 6.0)
			if real_a and kind in ["deer", "chamois", "ibex"] and randf() < 0.35:
				idle_kind = "alert"                                  # 3D-4.4: head up high, ears to the noise, very still
				idle_until = now + randf_range(2.5, 6.0)
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
	var want: float = speed * main.time_scale_visitors() * (0.3 if prone > 0.5 else (0.6 if crouch > 0.5 else 1.0))
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
	ctl_posture = clampi(ctl_posture, gear_pmin, gear_pmax)            # 3D-4.x: what the camouflage thing allows (gameplus.gd)
	var want_p := 1.0 if ctl_posture == 2 else 0.0
	var want_c := 1.0 if ctl_posture == 1 or (ctl_posture == 2 and prone < 0.9) or (want_p < prone and prone > 0.3) else 0.0   # 3D-4.12: over the crouch
	crouch = move_toward(crouch, want_c, dt * 2.5)
	prone = move_toward(prone, want_p, dt * 2.0)
	var mv := ctl_move.limit_length(1.0)
	if frozen:
		mv = Vector2.ZERO
	var top: float = PLAYER_SPEED[ctl_posture] * (2.3 if ctl_run and ctl_posture == 0 and not gear_norun else 1.0) * gear_speed
	if power == "turbo" and now < power_until:
		top *= 1.45
	top *= 1.0 - 0.07 * handicap
	var want: float = top * mv.length()
	if mv.length() > 0.08:
		dir = Vector3(mv.x, 0, mv.y).normalized()
		want_heading = atan2(-dir.x, -dir.z)
		var diff: float = abs(wrapf(want_heading - heading, -PI, PI))
		want *= clamp(1.15 - diff / 1.8, 0.15, 1.0)            # a sharp turn: slow down, turn, go on (no turning on the spot at full speed)
		var rate: float = [7.0, 5.0, 2.2][ctl_posture] * (0.75 if cur_speed > 2.5 else 1.0)
		heading = rotate_toward(heading, want_heading, rate * dt)
		rotation.y = heading
	else:
		want_heading = heading
	cur_speed = move_toward(cur_speed, want, dt * (4.0 if want > cur_speed else 6.0))   # starts a bit slower than it stops
	if cur_speed > 0.01:
		var mdir := Vector3(-sin(heading), 0, -cos(heading)).slerp(dir, 0.25) if mv.length() > 0.08 else Vector3(-sin(heading), 0, -cos(heading))
		position += mdir.normalized() * cur_speed * dt
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
			var wc := float(nxt[2]) if nxt.size() > 2 else 0.0
			_want_p = 1.0 if wc >= 1.5 else 0.0            # 3D-3.74: crouch 2 = crawling (a sneaking person)
			_want_c = minf(wc, 1.0)
			_post_smooth = true                            # 3D-4.12: goes down / gets up smoothly (_step)
			_face(nxt[3] if nxt.size() > 3 else target)
		else:
			target = nxt
			_want_c = 0.0
			_want_p = 0.0
			_post_smooth = crouch > 0.0 or prone > 0.0
			_face(target)
	else:
		done = true
		queue_free()


func _turn(dt: float, standing: bool) -> void:
	"""turn smoothly towards dir (cars a bit slower, small animals quicker)"""
	var want := atan2(-dir.x, -dir.z)
	var rate := 2.2 if kind == "car" else (6.0 if kind in ["cat", "hare", "hedgehog", "fox", "marten", "squirrel"] else 3.5)
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
	var amp: float
	if kind == "person":
		# steps matched to the speed (3D-3.21): the feet stay on the ground instead of sliding. A person walks with about
		# 1.8 steps per second at 1.4 m/s, runs with about 3; the step length gives the swing of the legs.
		var L: float = 0.92 * body_root.scale.y * (1.0 - 0.38 * crouch)
		var turning: bool = controlled and spd < 0.15 and abs(wrapf(want_heading - heading, -PI, PI)) > 0.15
		var fs: float = 0.0
		if prone > 0.5:
			fs = clamp(spd / 0.45 * 1.3, 0.0, 2.2)
		elif spd > 0.05:
			fs = clamp(0.95 + 0.6 * spd, 0.95, 3.3)
		elif turning:
			fs = 1.6                                                   # turning on the spot: small steps
		var stepl: float = spd / max(0.6, fs) if spd > 0.05 else (0.18 if turning else 0.0)
		var want_amp: float = asin(clamp(stepl / (2.0 * L), 0.0, 0.8))
		gait_amp = lerp(gait_amp, want_amp, clamp(dt * 8.0, 0.0, 1.0))
		gait_fs = lerp(gait_fs, fs, clamp(dt * 6.0, 0.0, 1.0))
		if gait_fs > 0.05 or abs(sin(phase)) > 0.05:
			phase += dt * PI * max(gait_fs, 1.2 if gait_fs < 0.05 else 0.0)   # standing: the last step is finished
		amp = gait_amp
		lean_acc = lerp(lean_acc, clamp((spd - last_spd) / max(dt, 0.001) * 0.06, -0.15, 0.15), clamp(dt * 5.0, 0.0, 1.0))
		last_spd = spd
	else:
		phase += dt * spd * (9.0 if kind in ["cat", "hedgehog", "hare", "marten", "squirrel"] else 6.5) / max(0.5, body_root.scale.y)
		amp = clamp(spd / 1.2, 0.0, 1.0) * 0.55 * (1.0 + 0.25 * clamp(spd - 1.8, 0.0, 1.0))
	var sw := sin(phase) * amp
	var k: float = clamp(dt * 12.0, 0.0, 1.0)
	var idle: String = idle_kind if now < idle_until else ""
	var leap := kind == "deer" and fled and spd > 2.0                     # a fleeing deer jumps
	_lie_k = move_toward(_lie_k, 1.0 if idle == "lie" else 0.0, dt * (0.9 if idle == "lie" else 0.75))   # 3D-4.4: lying / standing up
	for l in legs:
		if kind == "person":
			break                                         # persons: legs in _animate_person (3D-3.24)
		var want: float = sw * l[1]
		if kind == "hare":
			want = sin(phase * 0.5) * amp * 1.6 * (1 if legs.find(l) < 2 else -1)
		elif leap:
			var air: float = abs(sin(phase * 0.5))
			want = (-0.7 if legs.find(l) < 2 else 0.8) * air + sw * 0.3
		elif kind == "person" and prone > 0.5:
			want = sw * l[1] * 0.5 + 0.2                                   # crawling: legs push a little
		if _lie_k > 0.0:
			want = lerpf(want, -1.45 if legs.find(l) < 2 else 1.45, _lie_k)   # folded under the body
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
			if _lie_k > 0.0:
				y = lerpf(y, -body_h * 0.62, _lie_k)
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
			"stare":                                                     # 3D-3.95: towards the camera
				var to_c: Vector3 = main.head.global_position - global_position
				hyaw = clampf(wrapf(atan2(-to_c.x, -to_c.z) - heading, -PI, PI), -1.3, 1.3)
				hx = 0.1
			"sit_up":
				hx = -0.6
			"lie":                                                       # 3D-4.4: lying, the head up now and then
				hx = 0.15 * sin(now * 0.4 + seed_t)
				hyaw = 0.5 * sin(now * 0.23 + seed_t)
			"alert":                                                     # 3D-4.4: head high, towards the camera
				var to_c2: Vector3 = main.head.global_position - global_position
				hyaw = clampf(wrapf(atan2(-to_c2.x, -to_c2.z) - heading, -PI, PI), -1.2, 1.2)
				hx = 0.45
		if kind == "person" and not controlled and idle == "" and not puppet and not preview:
			hyaw = _glance(now)                                         # 3D-4.12: looks round now and then
		if kind == "person" and (now < startle_until or emote == "caught" and now < emote_until):
			hx = 0.15
		if kind == "person" and idle == "":
			hx += 1.05 * clamp(prone, 0.0, 1.0) + 0.5 * clamp(crouch, 0.0, 1.0) * (1.0 - clamp(prone, 0.0, 1.0))   # crouching / lying: looks ahead
		head.rotation.x = lerp(head.rotation.x, hx, clamp(dt * 4.0, 0.0, 1.0))
		if kind == "person" and controlled and idle == "":
			hyaw = clamp(wrapf(want_heading - heading, -PI, PI), -0.75, 0.75)   # the head turns first, the body follows
		head.rotation.y = lerp(head.rotation.y, hyaw, clamp(dt * (6.0 if controlled else 3.0), 0.0, 1.0))
	if tail != null:
		tail.rotation.y = sin(now * (9.0 if kind == "dog" else 2.0)) * (0.5 if kind == "dog" else 0.15)


func _animate_person(dt: float, spd: float, now: float, sw: float, amp: float, k: float, idle: String) -> void:
	"""a person (rebuilt in 3D-3.24): joints bend like a human's - hip + = thigh forward, knee - = lower leg back,
	elbow + = forearm forward, torso - = leaning forward. Crouching = hips and knees bent, the body low and leaning
	forward, the head up; crawling = lying on the belly, arms reach forward in turn, the opposite knee is drawn up."""
	for w in wheels:                                               # bike and pram wheels turn
		w[0].rotation.x -= spd * dt / float(w[1])
	if variant == "cyclist":
		_animate_cyclist(dt, spd, k)
		return
	var run_f: float = clamp((spd - 1.8) / 1.5, 0.0, 1.0)
	var jog := variant == "jogger"
	var em: String = emote if now < emote_until else ""
	var still: float = clamp(1.0 - spd / 0.2, 0.0, 1.0) * (1.0 - prone) * (0.0 if em != "" else 1.0)
	var c: float = clamp(crouch, 0.0, 1.0) * (1.0 - prone)
	if idle == "bend":
		c = max(c, 0.35)
	var pr: float = clamp(prone, 0.0, 1.0)
	var sc: float = body_root.scale.y
	var kl: float = 1.0 if not (now < startle_until or em == "caught") else 0.0
	# ---- legs: base pose of the crouch + the swing of the steps ----
	var hf: float = 1.05 * c                                       # thigh forward
	var kf: float = 1.8 * c                                        # knee bent
	var drop: float = 0.46 * (1.0 - cos(hf)) + 0.46 * (1.0 - cos(hf - kf))   # how much lower the hips are
	var swing_k: float = 1.0 - 0.45 * c                            # crouched: shorter steps
	for l in legs:
		var side: int = l[1]
		var hip_x: float
		var hip_z := 0.0
		var knee_x: float
		if pr > 0.5:
			# belly crawl: one knee drawn up to the side while the other leg is stretched, in turn
			var draw: float = max(0.0, sin(phase + (0.0 if side > 0 else PI)))
			hip_x = 0.06 + 0.3 * draw                                    # (lying: + = towards the ground)
			hip_z = side * (0.08 + 0.85 * draw)                          # the knee comes up at the side, on the ground
			knee_x = -(0.08 + 0.4 * draw)
		else:
			var s: float = sin(phase) * amp * side * swing_k
			var swing_fw: float = max(0.0, cos(phase) * side)            # this leg is swinging forward: the knee bends
			hip_x = hf + s
			knee_x = -(kf + swing_fw * amp * (1.5 + 1.0 * run_f) + 0.12 * amp)
			if idle == "bend":
				knee_x = -0.6
		l[0].rotation.x = lerp(l[0].rotation.x, hip_x, k)
		l[0].rotation.z = lerp(l[0].rotation.z, hip_z, k)
		l[2].rotation.x = lerp(l[2].rotation.x, knee_x, k)
	# ---- the body ----
	var bob: float = (abs(cos(phase)) - 0.6) * (0.03 + 0.05 * run_f) * clamp(amp / 0.35, 0.0, 1.3) * (1.0 - c * 0.6)
	var jump := 0.0
	if em == "goal":
		jump = abs(sin(now * 7.0)) * 0.18
	var crawl_bob: float = abs(sin(phase)) * 0.02
	body_root.position.y = lerp((-drop * sc + bob + jump), 0.05 * sc + crawl_bob, pr)
	body_root.rotation.x = -1.52 * pr
	body_root.rotation.z = sin(phase) * 0.06 * pr                     # crawling: the body rolls a little from side to side
	body_root.position.z = 0.95 * pr * sc                              # lying down: the hips stay where the player is
	body_root.position.x = sin(phase) * 0.025 * clamp(amp / 0.35, 0.0, 1.0) * (1.0 - pr) + still * 0.018 * sin(now * 0.45 + seed_t)
	if variant == "drunk":                                         # sways and staggers
		body_root.rotation.z = sin(now * 1.3 + seed_t) * 0.14 + sin(now * 3.1) * 0.04
		body_root.position.x += sin(now * 0.9 + seed_t) * 0.25
	if hips != null:
		hips.rotation.y = sin(phase) * amp * 0.2 * (1.0 - pr)
		hips.rotation.z = sin(phase) * 0.05 * amp + still * 0.03 * sin(now * 0.45 + seed_t)
		torso.rotation.y = -sin(phase) * amp * 0.25 * (1.0 - pr) + sin(phase) * 0.15 * pr
		var lean := -0.62 * c - 0.28 * run_f - (0.1 if jog and spd > 0.5 else 0.0) - (0.14 if variant == "elderly" else 0.0) - lean_acc * (1.0 - pr) + still * 0.02 * sin(now * 1.6 + seed_t)
		if idle == "bend":
			lean = -1.05
		if kl == 0.0:
			lean = 0.12
		if pr > 0.5:
			lean = 0.0
		torso.rotation.x = lerp(torso.rotation.x, lean, k)
	# ---- arms ----
	for a in arms:
		var side: int = a[1]
		var sx: float = -sin(phase) * amp * side * (1.25 if jog or run_f > 0.3 else 0.85) * swing_k + 0.35 * c
		var ex: float = 0.2 + (1.1 if jog else 0.0) + 1.0 * run_f + 0.55 * c
		var sz := 0.06 * side + 0.1 * c * side
		if pr > 0.5:                                                   # crawling: reach forward along the ground, pull back
			var reach: float = max(0.0, sin(phase + (PI if side > 0 else 0.0)))
			sx = lerp(0.4, -3.2, reach)                                  # elbow beside the chest, forearm flat ahead -> arm stretched ahead
			ex = lerp(2.6, 0.15, reach)
			sz = side * lerp(0.45, 0.2, reach)
		elif kl == 0.0:                                                # startled / caught: hands up
			sx = 2.8
			ex = 0.35
			sz = 0.3 * side
		elif em == "goal":                                             # cheering
			sx = 2.95 + 0.25 * sin(now * 10.0 + side)
			ex = 0.15
			sz = 0.35 * side
		elif em == "throw" and side > 0:                               # throwing a stone: back over the shoulder, then forward
			var f: float = clamp(1.0 - (emote_until - now) / 0.6, 0.0, 1.0)
			sx = lerp(-2.6, 0.9, f)
			ex = lerp(1.2, 0.1, f)
		elif idle == "phone" and side > 0:                             # on the phone
			sx = 0.5
			ex = 2.3
			sz = 0.25
		elif side > 0 and now < wait_until and crouch == 0.0 and _at_door():   # at a door: reaches for the handle
			sx = 1.3
			ex = 0.3
		elif phone_out and side > 0:                                   # walking with the phone light ahead
			sx = 0.9
			ex = 0.9
		elif carry or variant == "stroller":                           # holding the box / pushing the pram
			sx = 0.75 if carry else 0.85
			ex = 1.0 if carry else 0.35
			sz = 0.12 * side
		elif idle == "bend":
			sx = 0.8
			ex = 0.2
		a[0].rotation.x = lerp(a[0].rotation.x, sx, k)
		a[0].rotation.z = lerp(a[0].rotation.z, sz, k)
		if a.size() > 2:
			a[2].rotation.x = lerp(a[2].rotation.x, ex, k)
	if torch != null:
		if controlled:
			torch.light_energy = 4.5 if player_lamp else 0.0
		else:
			torch.light_energy = 3.0 if crouch > 0.5 and int(now * 3.0) % 4 != 0 else 0.0


func _glance(now: float) -> float:
	"""3D-4.12: a person looks to the side now and then - a sneaking one mostly towards the camera"""
	if now >= _glance_next:
		_glance_next = now + randf_range(2.5, 7.0)
		_glance_until = now + randf_range(0.6, 1.6)
		var sneaky: bool = crouch > 0.3 or prone > 0.3 or variant == "burglar"
		_glance_yaw = randf_range(-0.9, 0.9)
		if main != null and main.head != null and randf() < (0.7 if sneaky else 0.3):
			var to_c: Vector3 = main.head.global_position - global_position
			if to_c.length() < 25.0:
				_glance_yaw = clampf(wrapf(atan2(-to_c.x, -to_c.z) - heading, -PI, PI), -1.1, 1.1)
	return _glance_yaw if now < _glance_until else 0.0


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


func _animate_cyclist(dt: float, spd: float, k: float) -> void:
	"""sitting on the bike: the legs go round with the pedals, hands on the handlebar, leaning forward"""
	phase += dt * spd * 1.6
	for l in legs:
		var a: float = phase + (0.0 if l[1] > 0 else PI)
		l[0].rotation.x = lerp(l[0].rotation.x, 1.05 + 0.38 * sin(a), k)
		l[2].rotation.x = lerp(l[2].rotation.x, -(1.15 + 0.45 * cos(a)), k)
	if torso != null:
		torso.rotation.x = lerp(torso.rotation.x, -0.55, k)
	for a2 in arms:
		a2[0].rotation.x = lerp(a2[0].rotation.x, 1.0, k)
		a2[0].rotation.z = lerp(a2[0].rotation.z, 0.12 * a2[1], k)
		if a2.size() > 2:
			a2[2].rotation.x = lerp(a2[2].rotation.x, 0.25, k)
	if head != null:
		head.rotation.x = lerp(head.rotation.x, 0.45, k)
