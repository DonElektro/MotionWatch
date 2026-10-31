extends Node3D
## 3D-4.12 «Figuren» (Wunsch Daniel): echte 3D-Figuren mit Skelett statt Kästchen und Kapseln.
## Self-made in code (no model file, no licence question - see simulator3d/LIZENZEN.md): a Skeleton3D with 15 bones and
## one smooth skinned body built from rings (legs, pelvis, trunk, arms, hands, neck, head, shoes), with a twin mesh for
## the thermal camera where every corner has its own temperature (face warm, nose and ears cooler, hands, clothes cool).
## The joints of actor.gd (hips, torso, head, legs, arms) stay the «controls»: actor.gd moves them like before (walk,
## run, crouch, crawl, idle, carry …), here they are copied to the bones every frame, plus: the feet stay on the ground
## on a slope (the hips go down, the higher leg bends - two-bone IK), the foot stays flat, the box of the figure follows
## the pose (for the training pictures). Grafik «einfach» (Pi) keeps the old figures (actor.gd), from «mittel» these.
## Also here: the name and role above the head of a player (only the players and the operator see it, never MoveEye),
## the own look of a player (colour, size, build), more variety for the training pictures (vary()).

enum {B_HIPS, B_THIGH_L, B_SHIN_L, B_FOOT_L, B_THIGH_R, B_SHIN_R, B_FOOT_R, B_TORSO, B_UARM_L, B_FARM_L, B_HAND_L,
		B_UARM_R, B_FARM_R, B_HAND_R, B_HEAD}
enum {R_SKIN, R_JACKET, R_TROUSERS, R_SHOE, R_SOLE, R_SHIRT, R_HAND, R_LIPS, R_ZIP, R_CUFF}
const L1 := 0.46                     # thigh (hip joint -> knee)
const L2 := 0.42                     # shin (knee -> ankle)
const TAG_LAYERS := 16 | 128         # game players (16) and the operator (main.HELPER_LAYER) - not the cameras of MoveEye
const LOOK_COLS := {"black": Color(0.12, 0.12, 0.13), "grey": Color(0.5, 0.5, 0.52), "navy": Color(0.12, 0.16, 0.38),
		"olive": Color(0.33, 0.36, 0.2), "brown": Color(0.42, 0.28, 0.16), "red": Color(0.72, 0.14, 0.12),
		"orange": Color(0.9, 0.45, 0.1), "white": Color(0.88, 0.88, 0.86)}
const LOOK_SIZE := {"s": 0.92, "": 1.0, "l": 1.08}
const LOOK_BUILD := {"slim": 0.9, "": 1.0, "strong": 1.12}

static var mode := ""                # "" = by the graphics level, "alt" / "neu" = always (tests, A/B with MoveEye)
static var test_slope := 0.0         # tests: a pretend slope (rise per metre along x) where the ground is flat
static var _mat_v: StandardMaterial3D = null
static var _mat_t: ShaderMaterial = null
static var _mat_eye := {}
static var cost_us := 0              # tests: time spent in sync() (µs) and how often
static var cost_n := 0

var a                                # the actor
var skel: Skeleton3D
var mi: MeshInstance3D               # visible (layer 1)
var th: MeshInstance3D               # thermal twin (layer 2)
var mesh_v := ArrayMesh.new()
var mesh_t := ArrayMesh.new()
var arrays: Array = []
var pal := {}                        # region -> colour
var pivots: Array = []               # bone -> the joint of actor.gd that moves it (or null)
var boxes: Array = []                # bone -> AABB of its vertices (bone space at rest)
var rest_g: Array = []               # bone -> origin in the skeleton at rest
var _drop := 0.0
var _n := 0
var _V := PackedVector3Array()
var _B := PackedInt32Array()
var _W := PackedFloat32Array()
var _R := PackedByteArray()
var _T := PackedFloat32Array()
var _I := PackedInt32Array()
var _dom := PackedInt32Array()       # main bone of every vertex


static func wanted(main) -> bool:
	var m := mode if mode != "" else OS.get_environment("MW3D_FIGUR")
	if m == "alt":
		return false
	if m == "neu":
		return true
	return str(main.quality) != "simple"


# ---- building ------------------------------------------------------------------------------------------------------
func build(actor, p: Dictionary) -> void:
	"""p: colours (skin, jacket, shirt, trousers, shoe, hand), flags (shorts, open, short_sleeves), cloth_t (°C),
	shape (sh shoulders, hp hips, bl belly, ch chest, lt limbs), seg (ring corners)"""
	a = actor
	name = "figur"
	var main = a.main
	var n: int = int(p.get("seg", 10))
	var sh: float = p.get("sh", 1.0)
	var hp: float = p.get("hp", 1.0)
	var bl: float = p.get("bl", 0.0)
	var ch: float = p.get("ch", 0.0)
	var lt: float = p.get("lt", 1.0)
	var ct: float = p.get("cloth_t", 26.0)
	var amb: float = main.ambient
	var cold_k: float = clampf((12.0 - amb) / 20.0, 0.0, 1.0)      # the colder, the cooler nose, ears, hands
	var face_t: float = 34.6 - 1.2 * cold_k
	var nose_t: float = face_t - 1.2 - 3.0 * cold_k
	var hand_t: float = (31.5 - 5.0 * cold_k) if not p.get("gloves", false) else ct - 2.5
	var skin_t := 31.5 - 2.0 * cold_k
	if main.simreal != null and main.simreal.th_real:              # 3D-4.26: the heat table (waerme.gd), warmer after running
		var W = preload("res://scripts/waerme.gd")
		var act: bool = p.get("active", false)
		face_t = W.skin("face", amb, act)
		nose_t = W.skin("nose", amb, act)
		hand_t = W.skin("hand", amb, act) if not p.get("gloves", false) else ct - 2.5
		skin_t = W.skin("arm", amb, act)
	var shorts: bool = p.get("shorts", false)
	var short_sl: bool = p.get("short_sleeves", false)
	pal = {R_SKIN: p["skin"], R_JACKET: p["jacket"], R_TROUSERS: p["trousers"], R_SHOE: p["shoe"], R_SOLE: (p["shoe"] as Color).darkened(0.55),
			R_SHIRT: p["shirt"], R_HAND: p["hand"], R_LIPS: (p["skin"] as Color).darkened(0.22).lerp(Color(0.55, 0.25, 0.22), 0.35),
			R_ZIP: (p["jacket"] as Color).darkened(0.45), R_CUFF: (p["jacket"] as Color).darkened(0.18)}
	# ---- the skeleton (the same places as the joints of actor.gd) ----
	skel = Skeleton3D.new()
	skel.name = "skel"
	add_child(skel)
	var bones := [["hips", -1, Vector3(0, 0.95, 0)], ["thigh.L", 0, Vector3(-0.1, -0.03, 0)], ["shin.L", 1, Vector3(0, -L1, 0)], ["foot.L", 2, Vector3(0, -L2, 0)],
			["thigh.R", 0, Vector3(0.1, -0.03, 0)], ["shin.R", 4, Vector3(0, -L1, 0)], ["foot.R", 5, Vector3(0, -L2, 0)],
			["torso", -1, Vector3(0, 0.98, 0)], ["uarm.L", 7, Vector3(-0.245, 0.48, 0)], ["farm.L", 8, Vector3(0, -0.3, 0)], ["hand.L", 9, Vector3(0, -0.28, 0)],
			["uarm.R", 7, Vector3(0.245, 0.48, 0)], ["farm.R", 11, Vector3(0, -0.3, 0)], ["hand.R", 12, Vector3(0, -0.28, 0)], ["head", 7, Vector3(0, 0.6, 0)]]
	for i in range(bones.size()):
		var b: Array = bones[i]
		skel.add_bone(b[0])
		if int(b[1]) >= 0:
			skel.set_bone_parent(i, int(b[1]))
		skel.set_bone_rest(i, Transform3D(Basis.IDENTITY, b[2]))
		rest_g.append((rest_g[int(b[1])] if int(b[1]) >= 0 else Vector3.ZERO) + b[2])
		boxes.append(null)
	skel.reset_bone_poses()
	pivots = [a.hips, a.legs[0][0], a.legs[0][2], null, a.legs[1][0], a.legs[1][2], null, a.torso, a.arms[0][0], a.arms[0][2], null,
			a.arms[1][0], a.arms[1][2], null, a.head]
	# ---- the body: rings [y or z, rx, rz, weights, region, temp, front, back, side] ----
	for s in [-1, 1]:
		var x0: float = 0.1 * s
		var th_ := B_THIGH_L if s < 0 else B_THIGH_R
		var sn := th_ + 1
		var ft := th_ + 2
		var tr: int = R_TROUSERS
		var lower: int = R_SKIN if shorts else R_TROUSERS
		var lower_t: float = skin_t if shorts else ct - 1.8
		var legs := [[0.99, 0.095, 0.09, [[B_HIPS, 1.0]], tr, ct - 0.5],
				[0.92, 0.1 * lt * hp, 0.094 * lt, [[B_HIPS, 0.45], [th_, 0.55]], tr, ct - 0.6],
				[0.82, 0.093 * lt, 0.088 * lt, [[th_, 1.0]], tr, ct - 0.8],
				[0.66, 0.078 * lt, 0.075 * lt, [[th_, 1.0]], tr, ct - 1.0]]
		if shorts:
			legs.append_array([[0.57, 0.066 * lt, 0.066 * lt, [[th_, 1.0]], tr, ct - 1.0], [0.555, 0.058 * lt, 0.059 * lt, [[th_, 0.95], [sn, 0.05]], R_SKIN, skin_t]])
		legs.append_array([[0.53, 0.06 * lt, 0.061 * lt, [[th_, 0.85], [sn, 0.15]], lower, lower_t + 0.3],
				[0.46, 0.054 * lt, 0.056 * lt, [[th_, 0.5], [sn, 0.5]], lower, lower_t, 0.008],
				[0.40, 0.054 * lt, 0.058 * lt, [[sn, 0.85], [th_, 0.15]], lower, lower_t, 0.0, 0.008],
				[0.30, 0.056 * lt, 0.06 * lt, [[sn, 1.0]], lower, lower_t - 0.3, 0.0, 0.012],
				[0.19, 0.044 * lt, 0.046 * lt, [[sn, 1.0]], lower, lower_t - 0.6],
				[0.10, 0.038, 0.041, [[sn, 0.9], [ft, 0.1]], lower, lower_t - 1.0]])
		if not shorts:
			legs.append([0.075, 0.043, 0.046, [[sn, 0.6], [ft, 0.4]], R_TROUSERS, ct - 2.5])     # the hem, a little wider
		legs.append([0.055, 0.034, 0.036, [[sn, 0.4], [ft, 0.6]], R_SKIN if shorts else R_TROUSERS, lower_t - 1.5])
		_tube(legs, Vector3(x0, 0, 0), "y", n, true, true)
		# the shoe: rings from the heel to the toe (along -z), flat sole
		var sht: float = ct - 4.5
		var shoe := [[0.075, 0.044, 0.05, [[ft, 0.8], [sn, 0.2]], R_SHOE, sht, 0.05],
				[0.045, 0.05, 0.056, [[ft, 1.0]], R_SHOE, sht, 0.055],
				[-0.02, 0.052, 0.05, [[ft, 1.0]], R_SHOE, sht, 0.05],
				[-0.09, 0.05, 0.04, [[ft, 1.0]], R_SHOE, sht - 0.5, 0.04],
				[-0.15, 0.045, 0.031, [[ft, 1.0]], R_SHOE, sht - 0.8, 0.031],
				[-0.19, 0.033, 0.02, [[ft, 1.0]], R_SHOE, sht - 1.0, 0.022]]
		_tube(shoe, Vector3(x0, 0, 0), "z", n, true, true)
	# pelvis and trunk
	var jk: int = R_JACKET
	var trunk := [[0.835, 0.11 * hp, 0.08, [[B_HIPS, 1.0]], R_TROUSERS, ct - 0.5, 0.0, 0.01],
			[0.90, 0.162 * hp, 0.104, [[B_HIPS, 1.0]], R_TROUSERS, ct - 0.3, 0.0, 0.026],
			[0.955, 0.168 * hp, 0.108, [[B_HIPS, 0.75], [B_TORSO, 0.25]], R_TROUSERS, ct, bl * 0.4, 0.02],
			[0.965, 0.172 * hp, 0.112, [[B_HIPS, 0.7], [B_TORSO, 0.3]], jk, ct + 0.2, bl * 0.45, 0.02],         # the hem of the jacket
			[1.04, 0.156 * lerpf(hp, 1.0, 0.5), 0.101, [[B_HIPS, 0.35], [B_TORSO, 0.65]], jk, ct + 0.3, bl, 0.0],
			[1.12, 0.153, 0.103, [[B_TORSO, 1.0]], jk, ct + 0.4, bl * 0.8, 0.0],
			[1.22, 0.163 * sh, 0.11, [[B_TORSO, 1.0]], jk, ct + 0.6, ch * 0.5, 0.006],
			[1.31, 0.178 * sh, 0.118, [[B_TORSO, 1.0]], jk, ct + 0.7, ch, 0.01],
			[1.39, 0.19 * sh, 0.112, [[B_TORSO, 1.0]], jk, ct + 0.6, ch * 0.3, 0.012],
			[1.45, 0.19 * sh, 0.1, [[B_TORSO, 1.0]], jk, ct + 0.3, 0.0, 0.005],
			[1.497, 0.145 * sh, 0.078, [[B_TORSO, 1.0]], jk, ct + 0.2],
			[1.527, 0.062, 0.056, [[B_TORSO, 0.8], [B_HEAD, 0.2]], jk, ct + 0.5]]
	var front_reg := R_SHIRT if p.get("open", false) else R_ZIP
	_tube(trunk, Vector3.ZERO, "y", n + 2, true, true, func(ri: int, sn_: float) -> int: return front_reg if ri >= 4 and ri <= 9 and sn_ > (0.8 if front_reg == R_SHIRT else 0.96) else -1)
	# arms and hands
	for s in [-1, 1]:
		var x0: float = 0.245 * s
		var ua := B_UARM_L if s < 0 else B_UARM_R
		var fa := ua + 1
		var hd := ua + 2
		var low: int = R_SKIN if short_sl else R_JACKET
		var low_t: float = skin_t + 0.5 if short_sl else ct - 0.9
		var arm := [[1.505, 0.05, 0.05, [[B_TORSO, 0.6], [ua, 0.4]], jk, ct + 0.2],
				[1.47, 0.068 * lt, 0.066 * lt, [[B_TORSO, 0.3], [ua, 0.7]], jk, ct],
				[1.40, 0.066 * lt, 0.064 * lt, [[ua, 1.0]], jk, ct - 0.3]]
		if short_sl:
			arm.append_array([[1.30, 0.058 * lt, 0.057 * lt, [[ua, 1.0]], jk, ct - 0.4], [1.29, 0.05 * lt, 0.05 * lt, [[ua, 1.0]], R_SKIN, skin_t + 0.5]])
		else:
			arm.append([1.28, 0.06 * lt, 0.058 * lt, [[ua, 1.0]], jk, ct - 0.4])
		arm.append_array([[1.19, 0.053 * lt, 0.053 * lt, [[ua, 0.7], [fa, 0.3]], low, low_t],
				[1.16, 0.051 * lt, 0.052 * lt, [[ua, 0.5], [fa, 0.5]], low, low_t, 0.0, 0.006],
				[1.12, 0.052 * lt, 0.052 * lt, [[fa, 0.8], [ua, 0.2]], low, low_t],
				[1.03, 0.048 * lt, 0.047 * lt, [[fa, 1.0]], low, low_t - 0.2],
				[0.93, 0.04, 0.038, [[fa, 1.0]], low, low_t - 0.4]])
		if not short_sl:
			arm.append([0.905, 0.043, 0.041, [[fa, 1.0]], R_CUFF, ct - 1.2])
		var hr: int = R_HAND
		arm.append_array([[0.895, 0.03, 0.028, [[fa, 0.5], [hd, 0.5]], hr, hand_t + 0.5],
				[0.87, 0.022, 0.04, [[hd, 1.0]], hr, hand_t + 0.3, 0.004],
				[0.83, 0.025, 0.045, [[hd, 1.0]], hr, hand_t, 0.006],
				[0.79, 0.02, 0.04, [[hd, 1.0]], hr, hand_t - 0.4],
				[0.765, 0.012, 0.024, [[hd, 1.0]], hr, hand_t - 0.8]])
		_tube(arm, Vector3(x0, 0, 0), "y", maxi(6, n - 2), true, true)
	# neck and head (one tube: neck rings, then the head as an egg: narrow jaw, chin, nose, ears, the back of the head)
	var hy := 1.58
	var head := [[hy - 0.055, 0.056, 0.054, [[B_TORSO, 0.6], [B_HEAD, 0.4]], R_SKIN, 33.0],
			[hy - 0.015, 0.052, 0.051, [[B_TORSO, 0.25], [B_HEAD, 0.75]], R_SKIN, 33.4],
			[hy + 0.035, 0.05, 0.052, [[B_HEAD, 1.0]], R_SKIN, 33.6]]
	var hc := hy + 0.15
	for t in [-0.95, -0.72, -0.5, -0.3, -0.12, 0.05, 0.22, 0.45, 0.75, 1.05, 1.32]:
		var jaw: float = 0.8 + 0.2 * clampf((t + 0.95) / 0.9, 0.0, 1.0)
		var ring := [hc + 0.125 * sin(t), 0.093 * cos(t) * jaw, 0.105 * cos(t), [[B_HEAD, 1.0]], R_SKIN, face_t if t < 0.6 else face_t - 0.6,
				(0.014 if t > -0.85 and t < -0.55 else 0.0), (0.012 if t > -0.2 and t < 0.9 else 0.0), (0.02 if t > -0.2 and t < 0.15 else 0.0)]
		head.append(ring)
	var mouth_ring := 5
	_tube(head, Vector3.ZERO, "y", n + 2, false, true, func(ri: int, sn_: float) -> int:
		if ri == mouth_ring and sn_ > 0.97:
			return R_LIPS
		return -1)
	_shape_face(n + 2, hc, nose_t, face_t)
	_commit(main)
	# the eyes, brows and the mouth: small, only for the eye (MoveEye does not need them in the thermal picture)
	var hn: Node3D = a.head
	for s3 in [-1, 1]:
		_deco(hn, _sph(0.019), Vector3(0.04 * s3, 0.18, -0.084), Color(0.93, 0.93, 0.9))
		_deco(hn, _sph(0.011), Vector3(0.04 * s3, 0.18, -0.1), Color(0.08, 0.07, 0.06))
		var bm := BoxMesh.new()
		bm.size = Vector3(0.042, 0.009, 0.012)
		_deco(hn, bm, Vector3(0.043 * s3, 0.208, -0.094), (p.get("hair", Color(0.2, 0.15, 0.1)) as Color).darkened(0.2), Vector3(0, 0, -0.12 * s3))


func _shape_face(n: int, hc: float, nose_t: float, face_t: float) -> void:
	"""the nose: the front corner of two rings a little forward (cooler in the cold), the ears warm at the side"""
	for i in range(_V.size()):
		var v := _V[i]
		if _dom[i] != B_HEAD or v.y < hc - 0.04 or v.y > hc + 0.04:
			continue
		var r := Vector2(v.x, v.z)
		if r.length() < 0.06:
			continue
		var dirn := r.normalized()
		if dirn.y < -0.96:                                    # front (-z): the nose
			_V[i] = v + Vector3(0, 0, -0.028 * (1.0 - absf(v.y - (hc - 0.005)) / 0.04))
			_T[i] = nose_t
		elif absf(dirn.x) > 0.96:                             # the ears
			_T[i] = face_t - 1.4


func _tube(rings: Array, off: Vector3, axis: String, n: int, cap0: bool, cap1: bool, regf = null) -> void:
	"""rings of n corners along y (from any end) or along -z (the shoe); weights per ring, region and temperature per ring
	(regf can give one corner another region: zip, open jacket, lips)"""
	var first := _V.size()
	var u: Vector3
	var vv: Vector3
	if axis == "y":
		u = Vector3.RIGHT
		vv = Vector3(0, 0, -1)                                # sin > 0 = front
	else:
		u = Vector3.RIGHT
		vv = Vector3.UP                                       # sin > 0 = up
	for ri in range(rings.size()):
		var r: Array = rings[ri]
		var c: Vector3 = off + (Vector3(0, float(r[0]), 0) if axis == "y" else Vector3(0, float(r[6]) if r.size() > 6 else 0.05, float(r[0])))
		var rx: float = r[1]
		var rz: float = r[2]
		var fr: float = float(r[6]) if axis == "y" and r.size() > 6 else 0.0
		var bk: float = float(r[7]) if r.size() > 7 else 0.0
		var sd: float = float(r[8]) if r.size() > 8 else 0.0
		for j in range(n):
			var ang := TAU * j / n
			var co := cos(ang)
			var sn := sin(ang)
			var ex := rx + sd * pow(absf(co), 6.0)
			var ez := rz + (fr * pow(maxf(sn, 0.0), 3.0) + bk * pow(maxf(-sn, 0.0), 2.0))
			var p := c + u * co * ex + vv * sn * ez
			var reg: int = r[4]
			if axis == "z":
				if p.y < 0.0:
					p.y = 0.0                                 # flat sole on the ground
				if p.y < 0.012:
					reg = R_SOLE
			elif regf != null:
				var o: int = regf.call(ri, sn)
				if o >= 0:
					reg = o
			_add_v(p, r[3], reg, float(r[5]))
	var last := rings.size() - 1
	# winding: outward faces are clockwise for Godot; the rings may run against the axis
	var c0: Vector3 = _V[first]
	var c1: Vector3 = _V[first + last * n]
	var ax := Vector3.UP if axis == "y" else Vector3(0, 0, -1)
	var w := u.cross(vv)
	var flip: bool = (c1 - c0).dot(ax) * w.dot(ax) < 0.0
	for ri in range(last):
		for j in range(n):
			var p00 := first + ri * n + j
			var p01 := first + ri * n + (j + 1) % n
			var p10 := p00 + n
			var p11 := p01 + n
			_tri(p00, p01, p11, flip)
			_tri(p00, p11, p10, flip)
	for k in [0, 1]:
		if (k == 0 and not cap0) or (k == 1 and not cap1):
			continue
		var ri2: int = 0 if k == 0 else last
		var cen := Vector3.ZERO
		for j in range(n):
			cen += _V[first + ri2 * n + j]
		cen /= n
		var r2: Array = rings[ri2]
		var nb := ri2 + (1 if k == 0 else -1)
		var away: Vector3 = (cen - (_V[first + nb * n] + _V[first + nb * n + int(n / 2.0)]) * 0.5).normalized() * minf(float(r2[1]), float(r2[2])) * 0.5
		var ci := _V.size()
		_add_v(cen + away, r2[3], int(r2[4]) if axis == "y" else R_SHOE, float(r2[5]))
		for j in range(n):
			var q0 := first + ri2 * n + j
			var q1 := first + ri2 * n + (j + 1) % n
			_tri(ci, q1, q0, flip != (k == 1))


func _add_v(p: Vector3, wts: Array, reg: int, temp: float) -> void:
	_V.append(p)
	var tot := 0.0
	for e in wts:
		tot += float(e[1])
	var best := 0
	var bw := -1.0
	for k in range(4):
		if k < wts.size():
			_B.append(int(wts[k][0]))
			_W.append(float(wts[k][1]) / tot)
			if float(wts[k][1]) > bw:
				bw = float(wts[k][1])
				best = int(wts[k][0])
		else:
			_B.append(0)
			_W.append(0.0)
	_dom.append(best)
	_R.append(reg)
	_T.append(temp)


func _tri(i0: int, i1: int, i2: int, flip: bool) -> void:
	# (i0, i1, i2) is counter-clockwise seen from outside; Godot wants clockwise front faces
	if flip:
		_I.append_array([i0, i1, i2])
	else:
		_I.append_array([i0, i2, i1])


func _colours() -> PackedColorArray:
	var out := PackedColorArray()
	out.resize(_V.size())
	var nat: bool = a.main.colors != null and a.main.colors.on
	var cache := {}
	for k in pal.keys():
		cache[k] = a.main.colors.natural(pal[k]) if nat else pal[k]
	for i in range(_V.size()):
		out[i] = cache.get(_R[i], Color.MAGENTA)
	return out


func _temps() -> PackedColorArray:
	var out := PackedColorArray()
	out.resize(_V.size())
	for i in range(_V.size()):
		var tn := clampf((_T[i] + 40.0) / 120.0, 0.0, 1.0) * 255.0
		out[i] = Color(floorf(tn) / 255.0, tn - floorf(tn), 0.0, 1.0)
	return out


func _commit(main) -> void:
	# smooth normals from the faces
	var nrm := PackedVector3Array()
	nrm.resize(_V.size())
	for t in range(0, _I.size(), 3):
		var i0 := _I[t]
		var i1 := _I[t + 1]
		var i2 := _I[t + 2]
		var fn := (_V[i2] - _V[i0]).cross(_V[i1] - _V[i0])        # clockwise -> outward
		nrm[i0] += fn
		nrm[i1] += fn
		nrm[i2] += fn
	for i in range(nrm.size()):
		nrm[i] = nrm[i].normalized() if nrm[i].length() > 1e-9 else Vector3.UP
	arrays = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = _V
	arrays[Mesh.ARRAY_NORMAL] = nrm
	arrays[Mesh.ARRAY_BONES] = _B
	arrays[Mesh.ARRAY_WEIGHTS] = _W
	arrays[Mesh.ARRAY_INDEX] = _I
	arrays[Mesh.ARRAY_COLOR] = _colours()
	mesh_v.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var at := arrays.duplicate()
	at[Mesh.ARRAY_COLOR] = _temps()
	mesh_t.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, at)
	# the box of every bone (for the box of the whole figure in any pose)
	for i in range(_V.size()):
		var b := _dom[i]
		var lp: Vector3 = _V[i] - rest_g[b]
		boxes[b] = AABB(lp, Vector3.ZERO) if boxes[b] == null else (boxes[b] as AABB).expand(lp)
	var skin := skel.create_skin_from_rest_transforms()
	if _mat_v == null:
		_mat_v = StandardMaterial3D.new()
		_mat_v.vertex_color_use_as_albedo = true
		_mat_v.vertex_color_is_srgb = true
		_mat_v.albedo_color = Color.WHITE
		_mat_v.roughness = 0.88
		_mat_v.metallic_specular = 0.35
		_mat_t = ShaderMaterial.new()
		_mat_t.shader = load("res://shaders/thermal_vc.gdshader")
		_mat_t.set_shader_parameter("spread", 0.6)
		if main.has_method("th_reg"):
			main.th_reg(_mat_t)                                  # 3D-4.26: air and code of the thermal picture (main.gd)
	mi = MeshInstance3D.new()
	mi.mesh = mesh_v
	mi.skin = skin
	mi.material_override = _mat_v
	mi.layers = 1
	skel.add_child(mi)
	mi.skeleton = NodePath("..")
	th = MeshInstance3D.new()
	th.mesh = mesh_t
	th.skin = skin
	th.material_override = _mat_t
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	skel.add_child(th)
	th.skeleton = NodePath("..")
	_V = PackedVector3Array()                                   # the arrays keep them; region and temperature stay for a new dress
	_B = PackedInt32Array()
	_W = PackedFloat32Array()
	_I = PackedInt32Array()
	_dom = PackedInt32Array()
	sync(0.0)


func _deco(parent: Node3D, mesh: Mesh, pos: Vector3, col: Color, rot := Vector3.ZERO) -> void:
	var k := col.to_html()
	if not _mat_eye.has(k):
		var m := StandardMaterial3D.new()
		m.albedo_color = col
		m.roughness = 0.4
		_mat_eye[k] = m
	var d := MeshInstance3D.new()
	d.mesh = mesh
	d.position = pos
	d.rotation = rot
	d.material_override = _mat_eye[k]
	d.layers = 1
	d.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(d)


static func _sph(r: float) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = 2.0 * r
	s.radial_segments = 8
	s.rings = 4
	return s


# ---- every frame: the joints of actor.gd -> the bones; feet on the ground; the box of the pose --------------------
func sync(dt: float) -> void:
	if skel == null:
		return
	var t0 := Time.get_ticks_usec()
	for i in range(pivots.size()):
		var pv = pivots[i]
		if pv != null:
			skel.set_bone_pose_rotation(i, (pv as Node3D).quaternion)
	var pr: float = clampf(a.prone, 0.0, 1.0)
	var on_slope: bool = dt > 0.0 and not a.preview and a.variant != "cyclist" and pr < 0.1 and a.is_inside_tree() and (a.main.terrain or test_slope != 0.0)
	var raise := [0.0, 0.0]
	var pitch := 0.0
	if on_slope:
		var g0: float = a.global_position.y
		var dl := [0.0, 0.0]
		for li in range(2):
			var ank: Vector3 = (a.legs[li][2] as Node3D).global_transform * Vector3(0, -L2, 0)
			dl[li] = _ground(ank.x, ank.z) - g0
		_drop = lerpf(_drop, clampf(minf(dl[0], dl[1]), -0.3, 0.0), clampf(dt * 10.0, 0.0, 1.0))
		a.body_root.position.y += _drop
		for li in range(2):
			raise[li] = maxf(0.0, dl[li] - _drop)
		var fw := Vector3(-sin(a.heading), 0, -cos(a.heading))
		var gp: Vector3 = a.global_position
		pitch = atan((_ground(gp.x + fw.x * 0.3, gp.z + fw.z * 0.3) - _ground(gp.x - fw.x * 0.3, gp.z - fw.z * 0.3)) / 0.6)
	else:
		_drop = 0.0
	var sc: float = maxf(0.2, a.body_root.scale.y)
	for li in range(2):
		var hip_p: Node3D = a.legs[li][0]
		var knee_p: Node3D = a.legs[li][2]
		var hx: float = hip_p.rotation.x
		var kx: float = knee_p.rotation.x
		if raise[li] > 0.004:
			# two-bone IK in the plane of the leg (hips space): the ankle goes up by «raise»
			var hb: Node3D = a.hips
			var up: Vector3 = hb.global_transform.basis.inverse() * Vector3(0, raise[li], 0)
			var pa := Basis.from_euler(Vector3(hx, 0, 0)) * (Vector3(0, -L1, 0) + Basis.from_euler(Vector3(kx, 0, 0)) * Vector3(0, -L2, 0))
			var tgt := pa + Vector3(0, up.y, up.z)
			var d := clampf(Vector2(tgt.y, tgt.z).length(), 0.15, L1 + L2 - 0.002)
			var ck := clampf((L1 * L1 + L2 * L2 - d * d) / (2.0 * L1 * L2), -1.0, 1.0)
			kx = -(PI - acos(ck))
			var phi := atan2(-tgt.z, -tgt.y)
			var ca := clampf((L1 * L1 + d * d - L2 * L2) / (2.0 * L1 * d), -1.0, 1.0)
			hx = phi + acos(ca)
			skel.set_bone_pose_rotation(B_THIGH_L if li == 0 else B_THIGH_R, Basis.from_euler(Vector3(hx, hip_p.rotation.y, hip_p.rotation.z)).get_rotation_quaternion())
			skel.set_bone_pose_rotation(B_SHIN_L if li == 0 else B_SHIN_R, Basis.from_euler(Vector3(kx, 0, 0)).get_rotation_quaternion())
		var fx: float = lerpf(-(hx + kx) * 0.9 + pitch, -1.2, pr)          # flat on the ground; crawling: toes back
		skel.set_bone_pose_rotation(B_FOOT_L if li == 0 else B_FOOT_R, Basis.from_euler(Vector3(fx, 0, 0)).get_rotation_quaternion())
	for hb2 in [B_HAND_L, B_HAND_R]:
		skel.set_bone_pose_rotation(hb2, Basis.from_euler(Vector3(0.08, 0, 0)).get_rotation_quaternion())
	_n += 1
	if dt == 0.0 or _n % 2 == 0:
		_pose_box()
	cost_us += Time.get_ticks_usec() - t0
	cost_n += 1


func _ground(x: float, z: float) -> float:
	if a.main.terrain:
		return a.main.ground_y(x, z)
	return test_slope * x


func _pose_box() -> void:
	"""the box of the figure in its pose (skeleton space): for the training pictures (dataset.gd / vielfalt.gd read the meta
	«pose_aabb», a skinned mesh only knows its standing box) and for not being cut off by the camera (custom_aabb)"""
	var out := AABB()
	var first := true
	var parts := []
	for i in range(boxes.size()):
		if boxes[i] == null:
			continue
		var gp := skel.get_bone_global_pose(i)
		var b2: AABB = gp * (boxes[i] as AABB)
		parts.append([gp, boxes[i]])
		out = b2 if first else out.merge(b2)
		first = false
	mi.set_meta("pose_aabb", out)
	th.set_meta("pose_aabb", out)
	mi.set_meta("pose_parts", parts)
	mi.custom_aabb = out.grow(0.1)
	th.custom_aabb = out.grow(0.1)


# ---- a new dress (vielfalt.gd) and more variety -----------------------------------------------------------------------
func recolour(jacket, trousers) -> void:
	if jacket != null:
		pal[R_JACKET] = jacket
		pal[R_ZIP] = (jacket as Color).darkened(0.45)
		pal[R_CUFF] = (jacket as Color).darkened(0.18)
	if trousers != null:
		pal[R_TROUSERS] = trousers
	arrays[Mesh.ARRAY_COLOR] = _colours()
	mesh_v.clear_surfaces()
	mesh_v.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)


static func vary(v) -> Dictionary:
	"""more variety for the training pictures (vielfalt.gd «hoch»): height, build, and now and then a hood, a backpack or
	an umbrella - for the old and the new figures"""
	if v.kind != "person" or v.variant in ["cyclist", "stroller"]:
		return {}
	var h := randf_range(0.9, 1.12)
	var w := randf_range(0.88, 1.16)
	v.body_root.scale = Vector3(v.body_root.scale.x * w, v.body_root.scale.y * h, v.body_root.scale.z * w)
	v.body_h = 0.9 * v.body_root.scale.y
	var out := {"height": snappedf(h, 0.01), "build": snappedf(w, 0.01)}
	var r := randf()
	if r < 0.15:
		v.add_hood(v.rand_jacket())
		out["extra"] = "kapuze"
	elif r < 0.32:
		v.add_backpack(v.rand_jacket())
		out["extra"] = "rucksack"
	elif r < 0.45 and v.variant in ["", "elderly"]:
		v.add_umbrella()
		out["extra"] = "schirm"
	return out


# ---- the name and role of a player above the head (only players and the operator see it) -------------------------
static func tag(p: Dictionary, col: Color) -> void:
	"""game.gd (_paint_cone): name, role and colour of a player; the figure keeps the player and refreshes the words"""
	var a = p.get("actor", null)
	if a == null or not is_instance_valid(a):
		return
	a.tag_p = p
	a.tag_col = col
	if a.tag_lb == null:
		var lb := Label3D.new()
		lb.name = "tag"
		lb.font_size = 44
		lb.pixel_size = 0.0045
		lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lb.outline_size = 10
		lb.outline_modulate = Color(0, 0, 0, 0.85)
		lb.layers = TAG_LAYERS
		lb.position = Vector3(0, 2.62, 0)
		lb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		a.add_child(lb)
		a.tag_lb = lb
		var ring := MeshInstance3D.new()                    # a ring round the feet in the colour of the team / the player
		ring.name = "tag_ring"
		var tm := TorusMesh.new()
		tm.inner_radius = 0.36
		tm.outer_radius = 0.42
		tm.rings = 24
		tm.ring_segments = 4
		ring.mesh = tm
		ring.scale = Vector3(1, 0.25, 1)
		ring.position.y = 0.05
		ring.layers = TAG_LAYERS
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		a.add_child(ring)
		a.tag_ring = ring
	tag_tick(a, 99.0)


static func tag_tick(a, dt: float) -> void:
	a.tag_t -= dt
	if a.tag_t > 0.0:
		return
	a.tag_t = 0.5
	var p = a.tag_p
	if typeof(p) != TYPE_DICTIONARY or a.tag_lb == null or not is_instance_valid(a.tag_lb):
		return
	var role := str(p.get("role", "runner"))
	var rtxt: String = {"runner": "Schleicher", "guard": "Wächter", "watch": "Zuschauer"}.get(role, role)
	var team := ""
	if a.main != null and bool(a.main.get("game_teams")):
		team = ["Team Rot", "Team Blau"][clampi(int(p.get("team", 0)), 0, 1)] + " · "
	var txt := "%s\n%s%s" % [str(p.get("name", "")), team, rtxt]
	if a.tag_lb.text != txt:
		a.tag_lb.text = txt
	a.tag_lb.modulate = (a.tag_col as Color).lightened(0.25)
	if a.tag_ring.material_override == null or not (a.tag_ring.material_override as StandardMaterial3D).albedo_color.is_equal_approx(a.tag_col):
		var rm := StandardMaterial3D.new()
		rm.albedo_color = a.tag_col
		rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		rm.emission_enabled = true
		rm.emission = a.tag_col
		a.tag_ring.material_override = rm
	# carrying the stolen thing in front (gameplus.gd «Diebstahl»): both hands hold it
	var loot = p.get("loot", null)
	a.carry = bool(p.get("carry", false)) and (loot == null or not is_instance_valid(loot) or not loot.visible)


static func clean_look(m, out: Dictionary) -> Dictionary:
	"""game.gd: the own look from the phone - jacket colour, size, build (the rest: hat, backpack, level things in game.gd)"""
	if typeof(m) != TYPE_DICTIONARY:
		return out
	var c := str(m.get("col", ""))
	var s := str(m.get("size", ""))
	var b := str(m.get("build", ""))
	out["col"] = c if LOOK_COLS.has(c) else ""
	out["size"] = s if LOOK_SIZE.has(s) else ""
	out["build"] = b if LOOK_BUILD.has(b) else ""
	return out


# ---- for tests (main.gd «figuren»): a row of figures, a picture from a camera, frames per second ---------------------
static func op(main, d: Dictionary) -> Dictionary:
	var o := str(d.get("op", "info"))
	if o == "mode":
		mode = str(d.get("value", ""))
		test_slope = float(d.get("slope", test_slope))
		return {"ok": true, "mode": mode, "slope": test_slope}
	if o == "row":
		var kinds: Array = d.get("kinds", ["person"])
		var x0 := float(d.get("x", 0.0))
		var z := float(d.get("z", -8.0))
		var gap := float(d.get("gap", 1.2))
		var post := int(d.get("post", 0))
		var spd := float(d.get("spd", 0.0))
		var n := 0
		for i in range(kinds.size()):
			var x := x0 + (i - (kinds.size() - 1) / 2.0) * gap
			var p := Vector3(x, main.ground_y(x, z), z)
			var v = main.spawn(str(kinds[i]), p, p + Vector3(0, 0, 40.0))
			if v == null:
				continue
			v.demo = spd
			v.heading = float(d.get("heading", PI))
			v.rotation.y = v.heading
			v.dir = Vector3(-sin(v.heading), 0, -cos(v.heading))
			v.next_idle = v.now_s() + 9999.0
			if post > 0:
				v.ctl_posture = post
				v.crouch = 1.0 if post == 1 else 0.0
				v.prone = 1.0 if post == 2 else 0.0
			if d.has("carry"):
				v.carry = bool(d["carry"])
			n += 1
		return {"ok": true, "n": n}
	if o == "clear":
		for v in main.visitors.get_children():
			v.queue_free()
		return {"ok": true}
	if o == "shot":
		return _shot(main, d)
	if o == "info":
		var nf := 0
		var np := 0
		for v in main.visitors.get_children():
			if v.kind == "person":
				np += 1
				if v.get("fig") != null:
					nf += 1
		var out := {"ok": true, "fps": Engine.get_frames_per_second(), "persons": np, "figures": nf, "mode": mode, "quality": main.quality,
				"visitors": main.visitors.get_child_count(), "process_ms": snappedf(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, 0.01),
				"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
				"primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "sync_us": snappedf(float(cost_us) / maxf(1.0, cost_n), 0.1),
				"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT)}
		cost_us = 0
		cost_n = 0
		return out
	return {"ok": false, "error": "unknown op"}


static func _shot(main, d: Dictionary) -> Dictionary:
	"""a picture from a free camera (mask: 1 = what the cameras see, 2 = thermal, +16/+128 = the marks of the players);
	the file is written a few frames later (the answer comes at once)"""
	var w := int(d.get("w", 960))
	var h := int(d.get("h", 540))
	var mask := int(d.get("mask", 1))
	var vp := SubViewport.new()
	vp.size = Vector2i(w, h)
	vp.world_3d = main.get_viewport().world_3d
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.msaa_3d = Viewport.MSAA_4X if mask & 1 else Viewport.MSAA_DISABLED
	var cam := Camera3D.new()
	cam.cull_mask = mask
	cam.fov = float(d.get("fov", 50.0))
	cam.near = 0.1
	cam.far = 2000.0
	cam.attributes = CameraAttributesPractical.new()          # not the exposure / blur of the world (night)
	vp.add_child(cam)
	if mask & 2 and not (mask & 1):
		cam.environment = main.th_env                         # thermal: the environment of the thermal camera
	main.add_child(vp)
	var pp: Array = d.get("pos", [0, 1.5, 0])
	var la: Array = d.get("look", [0, 1, -8])
	cam.position = Vector3(float(pp[0]), float(pp[1]), float(pp[2]))
	cam.look_at(Vector3(float(la[0]), float(la[1]), float(la[2])))
	var path := str(d.get("path", "user://figur_shot.png"))
	var left := [int(d.get("frames", 5))]
	var hold := []                                            # the callable itself (a lambda does not see its own name)
	var cb := func() -> void:
		left[0] -= 1
		if left[0] > 0:
			return
		RenderingServer.frame_post_draw.disconnect(hold[0])
		vp.get_texture().get_image().save_png(path)
		vp.queue_free()
	hold.append(cb)
	RenderingServer.frame_post_draw.connect(cb)
	return {"ok": true, "path": path}
