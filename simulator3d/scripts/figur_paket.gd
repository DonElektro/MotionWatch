extends Node3D
## F5 «Figuren-Paket» (31.10.2026): Menschen aus einem nachladbaren Paket (Quaternius, CC0) mit echtem Skelett und
## echten Bewegungen (Gehen, Joggen, Rennen, Schleichen, Stehen, Sitzen, Telefonieren, Tragen) statt der Figur aus Ringen.
## The pack is NOT in the simulator ZIP: a small ZIP (figuren_v1.zip, ~4 MB, werkzeuge/figuren_paket.py) next to the .exe,
## in user:// (button «Figuren-Paket laden», System → Grafik) or in simulator3d/pakete/ (tests from the repository).
## Without the pack, on Lite and on Grafik «einfach» nothing changes: figur.gd (rings) or the old shapes (actor.gd).
##
## actor.gd stays the one place for the behaviour: it moves its joints (hips, torso, head, legs, arms) and its variables
## (cur_speed, crouch, prone, emote, carry, phone_out, idle_kind …) as before. Here, every frame (sync, like figur.gd):
##   * a clip is chosen from that state and played at the speed of the steps (no sliding feet),
##   * where there is no clip (crawling, on the bike / e-scooter, hands up, waving, door handle, pram …) the joints of
##     actor.gd are copied onto the bones (retarget: the turn of the joint × the bone in a standing reference pose),
##   * the head looks where actor.gd turns its head, things on the joints (hood, cap, backpack, lamp, umbrella, stick)
##     ride on the bones, the box of the pose is written for the training pictures (like figur.gd).
## Same interface as figur.gd: build(actor, p), sync(dt), recolour(jacket, trousers), mi / th.

const PACK := "figuren_v1.zip"
const PACK_URL := "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/simulator3d/pakete/figuren_v1.zip"
const PACK_SIZE := 3817330
const PACK_SHA := "b9a602ccef2deb292ba4773b6221cf263cda29929cf6eec847247bb350834b4b"
const MANNEQUIN_PELVIS := 0.9167          # height of the pelvis in the animation files (rest)
# clips: [name, speed of the steps in m/s at speed_scale 1 (0 = stands)]
const CLIP_SPEED := {"Walk_Loop": 1.15, "Jog_Fwd_Loop": 3.4, "Sprint_Loop": 6.0, "Crouch_Fwd_Loop": 0.7, "Walk_Carry_Loop": 1.05,
		"Walk_Formal_Loop": 1.15}
const CHAINS := ["root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head", "clavicle_l", "upperarm_l", "lowerarm_l",
		"hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
const ARM_BONES := ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"]

static var setting := "auto"             # «Figuren»: auto (pack if there) | paket (same, tells when missing) | eigen (never)
static var mode := ""                    # tests: "" | "an" | "aus"
static var _st := {}                     # the loaded pack: man, scenes {file: PackedScene}, libs {sex: AnimationLibrary}
static var _tried := ""                  # path tried last ("" = not yet)
static var last_error := ""
static var cost_us := 0
static var cost_n := 0

var a                                    # the actor
var root3: Node3D                        # the model (turned to -z)
var skel: Skeleton3D
var ap: AnimationPlayer
var mi: MeshInstance3D                   # the main visible mesh (pose_parts) - like figur.gd
var th: MeshInstance3D
var meshes: Array = []                   # visible MeshInstance3D
var twins: Array = []                    # thermal twins (layer 2)
var sex := "m"
var outfit := ""
var clip := ""
var _bi := {}                            # bone name -> index
var _ref_local := {}                     # bone -> local rotation in the standing reference pose (Idle, t = 0)
var _ref_body := {}                      # bone -> rotation in the space of body_root (reference pose)
var _ref_pelvis := Vector3.ZERO
var _K := Basis()                        # skeleton -> body_root (rotation only)
var _Ki := Basis()
var _w_full := 0.0                       # 0 = clip, 1 = all bones from the joints of actor.gd
var _w_arm := [0.0, 0.0]
var _boxes: Array = []                   # bone -> AABB (bone space)
var _mats := {}                          # tint key -> [StandardMaterial3D …]
var _hair_c := Color.BLACK
var _attached := false
var _n := 0


# ---- the pack --------------------------------------------------------------------------------------------------------
static func pack_paths() -> Array:
	var out := []
	var exe_dir := OS.get_executable_path().get_base_dir()
	out.append(exe_dir.path_join(PACK))
	out.append(exe_dir.path_join("figuren").path_join(PACK))
	out.append(ProjectSettings.globalize_path("user://" + PACK))
	out.append(ProjectSettings.globalize_path("res://").path_join("pakete").path_join(PACK))    # tests from the repository
	return out


static func pack_path() -> String:
	for p in pack_paths():
		if FileAccess.file_exists(p):
			return p
	return ""


static func wanted(main) -> bool:
	"""a figure from the pack? (actor.gd asks this before building the figure with a skeleton)"""
	load_setting()
	if mode == "aus" or (mode == "" and setting == "eigen"):
		return false
	if mode != "an":
		var Quality = load("res://scripts/quality.gd")
		if Quality.lite() or str(main.quality) == "simple":
			return false
	return ensure_loaded()


static func ensure_loaded() -> bool:
	if not _st.is_empty():
		return true
	var p := pack_path()
	if p == "" or p == _tried:
		return false
	_tried = p
	var t0 := Time.get_ticks_msec()
	var zr := ZIPReader.new()
	if zr.open(p) != OK:
		last_error = "Paket lässt sich nicht öffnen: " + p
		push_warning(last_error)
		return false
	var man = JSON.parse_string(zr.read_file("figuren.json").get_string_from_utf8())
	if typeof(man) != TYPE_DICTIONARY or int(man.get("version", 0)) < 1:
		last_error = "figuren.json fehlt oder ist kaputt"
		zr.close()
		return false
	var scenes := {}
	var files := []
	for grp in ["kleider", "haare"]:
		for k in man[grp]:
			files.append(str(man[grp][k]["file"]))
	for k in man["koepfe"]:
		files.append(str(man["koepfe"][k]))
	for f in files:
		var n := _gen(zr.read_file(f))
		if n == null:
			last_error = "Datei im Paket kaputt: " + f
			zr.close()
			return false
		var ps := PackedScene.new()
		ps.pack(n)
		n.free()
		scenes[f] = ps
	# animations: the tracks onto «Skeleton3D:bone», the way of the pelvis to the height of each body (man / woman)
	var base := AnimationLibrary.new()
	var done := {}
	for nm in man["anims"]:
		var f := str(man["anims"][nm])
		if done.has(f):
			continue
		done[f] = true
		var an := _gen(zr.read_file(f))
		if an == null:
			continue
		var ap0: AnimationPlayer = an.find_child("AnimationPlayer", true, false)
		if ap0 != null:
			for n2 in ap0.get_animation_list():
				var A: Animation = ap0.get_animation(n2).duplicate(true)
				for t in range(A.get_track_count() - 1, -1, -1):
					var tp := A.track_get_path(t)
					var bone := str(tp.get_name(tp.get_name_count() - 1)) if tp.get_subname_count() == 0 else str(tp.get_subname(0))
					if bone == "root":
						A.remove_track(t)                       # facing and place: actor.gd
						continue
					A.track_set_path(t, NodePath("Skeleton3D:" + bone))
				base.add_animation(n2, A)
		an.free()
	zr.close()
	var libs := {}
	for sx in ["m", "f"]:
		var hp := 0.9491 if sx == "m" else 0.9318              # rest height of the pelvis of the bodies of the pack
		var lib := AnimationLibrary.new()
		for n3 in base.get_animation_list():
			var A2: Animation = base.get_animation(n3).duplicate(true)
			for t in range(A2.get_track_count()):
				if A2.track_get_type(t) == Animation.TYPE_POSITION_3D:
					for k in range(A2.track_get_key_count(t)):
						A2.track_set_key_value(t, k, (A2.track_get_key_value(t, k) as Vector3) * (hp / MANNEQUIN_PELVIS))
			if n3.ends_with("_Loop"):
				A2.loop_mode = Animation.LOOP_LINEAR
			lib.add_animation(n3, A2)
		libs[sx] = lib
	_st = {"man": man, "scenes": scenes, "libs": libs, "path": p}
	print("Figuren-Paket: %s geladen (%d Teile, %d Bewegungen, %d ms)" % [p, scenes.size(), base.get_animation_list().size(), Time.get_ticks_msec() - t0])
	last_error = ""
	return true


static func _gen(bytes: PackedByteArray) -> Node:
	if bytes.is_empty():
		return null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_buffer(bytes, "", st) != OK:
		return null
	return doc.generate_scene(st)


static func info() -> Dictionary:
	return {"setting": setting, "mode": mode, "loaded": not _st.is_empty(), "path": _st.get("path", pack_path()),
			"error": last_error, "sync_us": snappedf(float(cost_us) / maxf(1.0, cost_n), 0.1)}


static func reset() -> void:
	"""a new pack was put in place: load it again with the next figure"""
	_st = {}
	_tried = ""


# ---- building --------------------------------------------------------------------------------------------------------
static func _inst(f: String) -> Node:
	var ps: PackedScene = _st["scenes"].get(f, null)
	return ps.instantiate() if ps != null else null


static func _skel_of(n: Node) -> Skeleton3D:
	return n.find_child("Skeleton3D", true, false) as Skeleton3D if not (n is Skeleton3D) else n


func build(actor, p: Dictionary) -> void:
	a = actor
	name = "figur"
	var man: Dictionary = _st["man"]
	var v: String = a.variant
	var kid: bool = v == "child"
	sex = "f" if randf() < (0.45 if not v in ["police", "burglar", "courier"] else 0.25) else "m"
	var hooded: bool = v == "burglar"                              # the hood of the ranger only for the burglar
	var kl := "ranger" if (hooded or (v in ["", "elderly"] and randf() < 0.25)) else "peasant"
	outfit = "kleid_%s_%s" % [sex, kl]
	if not man["kleider"].has(outfit):
		outfit = man["kleider"].keys()[0]
	root3 = _inst(str(man["kleider"][outfit]["file"]))
	add_child(root3)
	root3.rotation.y = PI                                         # the model looks to +z, actor.gd to -z
	skel = _skel_of(root3)
	skel.name = "Skeleton3D"
	for i in range(skel.get_bone_count()):
		_bi[skel.get_bone_name(i)] = i
	_take(str(man["koepfe"].get(sex, man["koepfe"].values()[0])), false)
	if kl != "ranger" or not hooded:
		var hs := []
		for h in man["haare"]:
			if str(man["haare"][h].get("sex", "m")) == sex and (h != "haar_bart" or randf() < 0.3):
				hs.append(h)
		if not hs.is_empty():
			_take(str(man["haare"][hs[randi() % hs.size()]]["file"]), true)
	if kl == "ranger" and not hooded:
		for c in skel.get_children():
			if c is MeshInstance3D and str(c.name).contains("Hood"):
				skel.remove_child(c)
				c.free()
	ap = AnimationPlayer.new()
	root3.add_child(ap)
	ap.root_node = ap.get_path_to(skel.get_parent())
	ap.add_animation_library("", _st["libs"][sex])
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	ap.playback_default_blend_time = 0.25
	_reference()
	_dress(p)
	_thermal(p)
	_bone_boxes()
	_play("Idle_Loop", 0.0, 1.0)
	ap.seek(randf() * 2.0, true)
	sync(0.0)


func _take(f: String, hair: bool) -> void:
	"""the meshes of another file of the pack onto this skeleton (same bones, same order)"""
	var n := _inst(f)
	if n == null:
		return
	var s := _skel_of(n)
	for c in s.get_children():
		if c is MeshInstance3D:
			s.remove_child(c)
			c.owner = null
			skel.add_child(c)
			c.skeleton = NodePath("..")
			if hair:
				c.set_meta("hair", true)
	n.free()


func _reference() -> void:
	"""the standing pose (Idle, first frame) = the pose of actor.gd with all joints at 0"""
	ap.play("Idle_Loop")
	ap.seek(0.0, true)
	var xf: Transform3D = (root3.transform * skel.get_parent().transform * skel.transform)
	_K = xf.basis.orthonormalized()
	_Ki = _K.inverse()
	var glob := {}
	for b in CHAINS:
		if not _bi.has(b):
			continue
		var i: int = _bi[b]
		var q := skel.get_bone_pose_rotation(i)
		_ref_local[b] = q
		var pi_ := skel.get_bone_parent(i)
		var pq: Quaternion = glob.get(skel.get_bone_name(pi_), _parent_global(pi_)) if pi_ >= 0 else Quaternion.IDENTITY
		glob[b] = pq * q
		_ref_body[b] = Quaternion(_K) * (glob[b] as Quaternion)
	if _bi.has("pelvis"):
		_ref_pelvis = skel.get_bone_pose_position(_bi["pelvis"])


func _parent_global(i: int) -> Quaternion:
	var q := Quaternion.IDENTITY
	while i >= 0:
		q = skel.get_bone_pose_rotation(i) * q
		i = skel.get_bone_parent(i)
	return q


func _dress(p: Dictionary) -> void:
	"""colours of actor.gd: jacket (body, sleeves, hood), trousers, shoes, skin, hair - the textures of the clothes are grey"""
	var skin: Color = p.get("skin", Color(0.85, 0.66, 0.55))
	_hair_c = p.get("hair", Color(0.3, 0.2, 0.1))
	var skin_k: Color = Color(skin.r / 0.85, skin.g / 0.66, skin.b / 0.55)
	for m in skel.get_children():
		if not (m is MeshInstance3D):
			continue
		var mi3 := m as MeshInstance3D
		mi3.layers = 1
		meshes.append(mi3)
		var nm := str(mi3.name)
		for si in range(mi3.mesh.get_surface_count()):
			var src = mi3.mesh.surface_get_material(si)
			if not (src is StandardMaterial3D):
				continue
			var mt: StandardMaterial3D = (src as StandardMaterial3D).duplicate()
			mt.metallic_specular = 0.3
			var mn := str(src.resource_name)
			var key := "skin"
			if mn.contains("Hair"):
				key = "hair"
				mt.albedo_color = _hair_c.lightened(0.1)
			elif mn.contains("Eye"):
				key = "eye"
			elif mn.contains("Regular") or mn.contains("Superhero"):
				mt.albedo_color = Color(clampf(skin_k.r, 0.4, 1.15), clampf(skin_k.g, 0.4, 1.15), clampf(skin_k.b, 0.4, 1.15))
				mt.roughness = 0.6
			else:
				key = "trousers" if nm.contains("Legs") else ("shoe" if nm.contains("Feet") else ("belt" if nm.contains("Belt") else "jacket"))
				var c: Color = p.get(key, Color(0.3, 0.3, 0.3)) if key != "belt" else Color(0.25, 0.17, 0.1)
				mt.albedo_color = c * 1.25
				mt.roughness = 0.92
			mi3.set_surface_override_material(si, mt)
			if not _mats.has(key):
				_mats[key] = []
			_mats[key].append(mt)
	mi = meshes[0] if not meshes.is_empty() else null
	for m2 in meshes:
		if str(m2.name).contains("Body"):
			mi = m2


func _thermal(p: Dictionary) -> void:
	"""the twin for the thermal camera: skin warm, clothes as warm as actor.gd says, hair cooler"""
	var ct: float = p.get("cloth_t", 26.0)
	var main = a.main
	for m in meshes:
		var t := MeshInstance3D.new()
		t.mesh = m.mesh
		t.skin = m.skin
		t.layers = 2
		t.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		skel.add_child(t)
		t.skeleton = NodePath("..")
		t.transform = m.transform
		for si in range(m.mesh.get_surface_count()):
			var src = m.mesh.surface_get_material(si)
			var mn := str(src.resource_name) if src != null else ""
			var temp := ct
			if mn.contains("Hair"):
				temp = 30.0 if not bool(p.get("gloves", false)) else 27.0
			elif mn.contains("Eye") or mn.contains("Superhero"):
				temp = 34.5
			elif mn.contains("Regular"):
				temp = 32.0 if not bool(p.get("gloves", false)) else 24.0
			t.set_surface_override_material(si, main.tmat_fixed(temp))
		twins.append(t)
	th = twins[meshes.find(mi)] if mi != null and not twins.is_empty() else null


func _bone_boxes() -> void:
	"""the box of every bone (bone space at rest) from the vertices of the meshes - for the box of the pose"""
	_boxes.resize(skel.get_bone_count())
	for m in meshes:
		var sk: Skin = m.skin
		if sk == null or m.mesh == null:
			continue
		var binds := {}
		for bi in range(sk.get_bind_count()):
			var bn := sk.get_bind_name(bi)
			var idx: int = skel.find_bone(bn) if bn != "" else sk.get_bind_bone(bi)
			binds[bi] = [idx, sk.get_bind_pose(bi)]
		for si in range(m.mesh.get_surface_count()):
			var arr: Array = m.mesh.surface_get_arrays(si)
			var V: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var B = arr[Mesh.ARRAY_BONES]
			var W = arr[Mesh.ARRAY_WEIGHTS]
			if B == null or W == null or V.is_empty():
				continue
			var nb: int = B.size() / V.size()
			for vi in range(0, V.size(), 3):                 # every third vertex is enough for a box
				var best := 0
				for j in range(1, nb):
					if W[vi * nb + j] > W[vi * nb + best]:
						best = j
				var bb = binds.get(int(B[vi * nb + best]), null)
				if bb == null or int(bb[0]) < 0:
					continue
				var lp: Vector3 = (bb[1] as Transform3D) * V[vi]
				var bi2: int = bb[0]
				_boxes[bi2] = AABB(lp, Vector3.ZERO) if _boxes[bi2] == null else (_boxes[bi2] as AABB).expand(lp)


func recolour(jacket, trousers) -> void:
	"""vielfalt.gd: new clothes for the training pictures"""
	if jacket != null:
		for mt in _mats.get("jacket", []):
			mt.albedo_color = (jacket as Color) * 1.25
	if trousers != null:
		for mt in _mats.get("trousers", []):
			mt.albedo_color = (trousers as Color) * 1.25


# ---- every frame -----------------------------------------------------------------------------------------------------
func _play(n: String, blend: float, spd: float) -> void:
	if not ap.has_animation(n):
		n = "Idle_Loop"
	if n != clip:
		clip = n
		ap.play(n, blend)
	ap.speed_scale = spd


func _choose(now: float) -> Array:
	"""clip, speed scale, weight «all from the joints», weight of the arms from the joints [left, right]"""
	var spd: float = a.cur_speed
	var v: String = a.variant
	var pr: float = clampf(a.prone, 0.0, 1.0)
	var cr: float = clampf(a.crouch, 0.0, 1.0)
	var idle: String = a.idle_kind if now < a.idle_until else ""
	var em: String = a.emote if now < a.emote_until else ""
	var arms := [0.0, 0.0]
	if v in ["cyclist", "escooter", "wheelchair"] or pr > 0.35 or a.stars != null or idle == "bend":
		return ["Idle_Loop", 1.0, 1.0, arms]
	var c := "Idle_Loop"
	var k := 1.0
	var sitting: bool = (now < a.wait_until and cr > 0.4 and cr < 0.85 and spd < 0.15)
	if sitting:
		c = "Sitting_Idle_Loop"
	elif cr > 0.5:
		c = "Crouch_Fwd_Loop" if spd > 0.08 else "Crouch_Idle_Loop"
	elif spd > 0.12:
		if spd > 4.4:
			c = "Sprint_Loop"
		elif spd > 2.1:
			c = "Jog_Fwd_Loop"
		elif a.carry:
			c = "Walk_Carry_Loop"
		else:
			c = "Walk_Loop"
	elif idle == "phone" and ap.has_animation("Idle_TalkingPhone_Loop"):
		c = "Idle_TalkingPhone_Loop"
	if CLIP_SPEED.has(c):
		k = clampf(spd / CLIP_SPEED[c], 0.45, 1.9)
	if v == "elderly":
		k *= 0.9
	# the arms do something of their own (actor.gd): copy them from the joints
	var own: bool = em != "" or now < a.startle_until or (a.carry and c != "Walk_Carry_Loop") or v == "stroller" \
			or idle == "wave"
	if own:
		arms = [1.0, 1.0]
	elif (a.phone_out or (now < a.wait_until and cr == 0.0 and a._at_door())) and c != "Idle_TalkingPhone_Loop":
		arms[1] = 1.0                                              # right hand: phone light ahead / door handle
	return [c, k, 0.0, arms]


func sync(dt: float) -> void:
	if skel == null or ap == null:
		return
	var t0 := Time.get_ticks_usec()
	var now: float = a.now_s() if a.main != null else 0.0
	var ch: Array = _choose(now) if not a.preview else ["Idle_Loop", 1.0, 0.0, [0.0, 0.0]]
	var kk: float = clampf(dt * 4.0, 0.0, 1.0) if dt > 0.0 else 1.0
	_w_full = move_toward(_w_full, ch[2], kk)
	_w_arm[0] = move_toward(_w_arm[0], ch[3][0], kk * 1.5)
	_w_arm[1] = move_toward(_w_arm[1], ch[3][1], kk * 1.5)
	_play(ch[0], 0.3, ch[1])
	ap.advance(dt)
	# body_root: actor.gd lowers / tilts it for its own crouch, bob and crawl - the clip does that itself
	var br: Node3D = a.body_root
	var wf := _w_full
	var keep_x: float = br.position.x if a.variant == "drunk" else 0.0
	br.position = Vector3(lerpf(keep_x, br.position.x, wf), br.position.y * wf, br.position.z * wf)
	br.rotation = Vector3(br.rotation.x * wf, 0.0, br.rotation.z if a.variant == "drunk" else br.rotation.z * wf)
	_retarget(wf)
	_n += 1
	if dt == 0.0 or _n % 2 == 0:
		_pose_box()
	if not _attached and dt > 0.0:
		_attach()
	cost_us += Time.get_ticks_usec() - t0
	cost_n += 1


func _joint_q(b: String) -> Variant:
	"""the turn of the joint of actor.gd that moves bone b, in the space of body_root (null = none)"""
	var hq: Quaternion = a.hips.quaternion if a.hips != null else Quaternion.IDENTITY
	var tq: Quaternion = a.torso.quaternion if a.torso != null else Quaternion.IDENTITY
	match b:
		"pelvis":
			return hq
		"spine_01":
			return tq
		"Head":
			return tq * a.head.quaternion
		"upperarm_l", "upperarm_r":
			var A = a.arms[0 if b.ends_with("_l") else 1]
			return tq * (A[0] as Node3D).quaternion
		"lowerarm_l", "lowerarm_r":
			var A2 = a.arms[0 if b.ends_with("_l") else 1]
			return tq * (A2[0] as Node3D).quaternion * (A2[2] as Node3D).quaternion
		"thigh_l", "thigh_r":
			var L = a.legs[0 if b.ends_with("_l") else 1]
			return hq * (L[0] as Node3D).quaternion
		"calf_l", "calf_r":
			var L2 = a.legs[0 if b.ends_with("_l") else 1]
			return hq * (L2[0] as Node3D).quaternion * (L2[2] as Node3D).quaternion
	return null


func _retarget(wf: float) -> void:
	"""bones from the joints of actor.gd (weight wf for all, _w_arm for the arms), the head looks where actor.gd says"""
	var glob := {}
	var Kq := Quaternion(_K)
	var Kiq := Quaternion(_Ki)
	var head_extra := Quaternion.IDENTITY
	if a.head != null and wf < 1.0:
		var hx: float = a.head.rotation.x
		var idle: String = a.idle_kind if a.now_s() < a.idle_until else ""
		if a.kind == "person" and idle == "":
			hx -= 1.05 * clampf(a.prone, 0.0, 1.0) + 0.5 * clampf(a.crouch, 0.0, 1.0) * (1.0 - clampf(a.prone, 0.0, 1.0))
		head_extra = Quaternion(Vector3.UP, a.head.rotation.y) * Quaternion(Vector3.RIGHT, clampf(hx, -1.0, 0.6) * 0.8)
	for b in CHAINS:
		if not _bi.has(b):
			continue
		var i: int = _bi[b]
		var pi_ := skel.get_bone_parent(i)
		var pg: Quaternion = glob.get(skel.get_bone_name(pi_), Quaternion.IDENTITY) if pi_ >= 0 else Quaternion.IDENTITY
		if pi_ >= 0 and not glob.has(skel.get_bone_name(pi_)):
			pg = _parent_global(pi_)
		var local := skel.get_bone_pose_rotation(i)
		var w := wf
		if b in ARM_BONES:
			w = maxf(wf, _w_arm[0 if b.ends_with("_l") else 1])
		if w > 0.001:
			var jq = _joint_q(b)
			var lr: Quaternion = _ref_local.get(b, local)
			if jq != null:
				var gd: Quaternion = Kiq * (jq as Quaternion) * (_ref_body[b] as Quaternion)
				lr = (pg.inverse() * gd).normalized()
			local = local.slerp(lr, w)
		if b == "Head" and head_extra != Quaternion.IDENTITY:
			var gh: Quaternion = pg * local
			gh = Kiq * head_extra * Kq * gh
			local = local.slerp((pg.inverse() * gh).normalized(), 1.0 - wf)
		skel.set_bone_pose_rotation(i, local)
		glob[b] = pg * local
	if _bi.has("pelvis") and wf > 0.001:
		var pp := skel.get_bone_pose_position(_bi["pelvis"])
		skel.set_bone_pose_position(_bi["pelvis"], pp.lerp(_ref_pelvis, wf))


func _attach() -> void:
	"""what actor.gd hung onto its joints (hood, cap, backpack, umbrella, lamp, stick, coat …) rides on the bones now;
	its hair from shapes is hidden (the pack has real hair)"""
	_attached = true
	var pairs := []
	if a.head != null:
		pairs.append([a.head, "Head"])
	if a.torso != null:
		pairs.append([a.torso, "spine_02"])
	if a.hips != null:
		pairs.append([a.hips, "pelvis"])
	for k in range(a.arms.size()):
		var sfx := "_l" if k == 0 else "_r"
		pairs.append([a.arms[k][0], "upperarm" + sfx])
		pairs.append([a.arms[k][2], "lowerarm" + sfx])
	for k in range(a.legs.size()):
		var sfx2 := "_l" if k == 0 else "_r"
		pairs.append([a.legs[k][0], "thigh" + sfx2])
		pairs.append([a.legs[k][2], "calf" + sfx2])
	var has_hair := false
	for m in meshes:
		if m.has_meta("hair"):
			has_hair = true
	for pr in pairs:
		var pv: Node3D = pr[0]
		var bn: String = pr[1]
		if pv == null or not _bi.has(bn):
			continue
		var kids := []
		for c in pv.get_children():
			if c is Node3D and not (c in [a.head, a.torso, a.hips]) and not _is_pivot(c):
				kids.append(c)
		if kids.is_empty():
			continue
		var ba := BoneAttachment3D.new()
		ba.bone_name = bn
		skel.add_child(ba)
		# joint (rest of actor.gd) -> bone (reference pose): same place in body space
		var pivot_body: Transform3D = _rest_in_body(pv)
		var bone_body: Transform3D = Transform3D(Basis(_ref_body.get(bn, Quaternion(_K))), _bone_rest_body(bn))
		var off := bone_body.affine_inverse() * pivot_body
		var skip_next := false
		var kids_sorted := kids
		for c in kids_sorted:
			if skip_next:
				skip_next = false
				c.visible = false
				continue
			if has_hair and bn == "Head" and c is MeshInstance3D and c.material_override is StandardMaterial3D \
					and ((c.material_override as StandardMaterial3D).albedo_color.is_equal_approx(_hair_c)):
				c.visible = false                                   # hair from shapes: the twin (next) goes too
				skip_next = true
				continue
			var lt: Transform3D = c.transform
			pv.remove_child(c)
			ba.add_child(c)
			c.transform = off * lt


func _is_pivot(n: Node) -> bool:
	for k in range(a.arms.size()):
		if n == a.arms[k][0] or n == a.arms[k][2]:
			return true
	for k in range(a.legs.size()):
		if n == a.legs[k][0] or n == a.legs[k][2]:
			return true
	return false


func _rest_in_body(pv: Node3D) -> Transform3D:
	"""the joint at rest (all joints of actor.gd at 0) in the space of body_root - positions only"""
	var p := Vector3.ZERO
	var n: Node = pv
	while n != null and n != a.body_root:
		p += (n as Node3D).position
		n = n.get_parent()
	return Transform3D(Basis(), p)


func _bone_rest_body(bn: String) -> Vector3:
	"""the bone in the reference pose, in the space of body_root"""
	var i: int = _bi[bn]
	var xf := Transform3D()
	var chain := []
	while i >= 0:
		chain.push_front(i)
		i = skel.get_bone_parent(i)
	for j in chain:
		var nm := skel.get_bone_name(j)
		var q: Quaternion = _ref_local.get(nm, skel.get_bone_rest(j).basis.get_rotation_quaternion())
		var pos: Vector3 = _ref_pelvis if nm == "pelvis" else skel.get_bone_rest(j).origin
		xf = xf * Transform3D(Basis(q), pos)
	var m: Transform3D = root3.transform * skel.get_parent().transform * skel.transform
	return (m * xf).origin


func _pose_box() -> void:
	"""like figur.gd: the box of the pose (skeleton space) for the training pictures and the camera"""
	var out := AABB()
	var first := true
	var parts := []
	for i in range(_boxes.size()):
		if _boxes[i] == null:
			continue
		var gp := skel.get_bone_global_pose(i)
		var b2: AABB = gp * (_boxes[i] as AABB)
		parts.append([gp, _boxes[i]])
		out = b2 if first else out.merge(b2)
		first = false
	if first:
		return
	for m in meshes:
		m.set_meta("pose_aabb", out)
		m.custom_aabb = out.grow(0.1)
	for t in twins:
		t.set_meta("pose_aabb", out)
		t.custom_aabb = out.grow(0.1)
	if mi != null:
		mi.set_meta("pose_parts", parts)


# ---- setting, download (System → Grafik) -----------------------------------------------------------------------------
const SAVE := "user://figuren_einst.json"
static var _busy := false
static var _loaded_setting := false


static func load_setting() -> void:
	if _loaded_setting:
		return
	_loaded_setting = true
	var f := FileAccess.open(SAVE, FileAccess.READ)
	if f != null:
		var d = JSON.parse_string(f.get_as_text())
		if typeof(d) == TYPE_DICTIONARY and str(d.get("setting", "auto")) in ["auto", "eigen"]:
			setting = str(d.get("setting", "auto"))


static func set_setting(v: String) -> void:
	setting = v if v in ["auto", "eigen"] else "auto"
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"setting": setting}))


static func status_text() -> String:
	if setting == "eigen":
		return "Figuren: eigene (aus Ringen)"
	var p := pack_path()
	if p == "":
		return "Figuren-Paket fehlt – «Figuren-Paket laden» holt es (%.1f MB)" % (PACK_SIZE / 1048576.0)
	return "Figuren-Paket da (%s)%s" % [p.get_file(), "" if last_error == "" else " – Fehler: " + last_error]


static func add_controls(main) -> void:
	load_setting()
	var G := {"sub": "Grafik", "options": [["auto", "aus dem Paket (Quaternius, echte Bewegungen) – sonst eigene"], ["eigen", "eigene (aus Ringen, ohne Paket)"]]}
	main.add_control("select", "fig_pack", "Figuren der Menschen (gilt für neue Besucher; Lite und «einfach»: immer einfache Figuren)",
			func(): return setting, func(v): set_setting(str(v)); main.start_info = status_text(), "System", G)
	main.add_control("button", "fig_pack_load", "Figuren-Paket laden (%.1f MB, einmalig)" % (PACK_SIZE / 1048576.0), null,
			func(): download(main), "System", {"sub": "Grafik"})


static func download(main) -> void:
	"""the pack from GitHub into user:// (curl.exe on Windows like update.gd, else HTTPRequest), checked with SHA-256"""
	if _busy:
		return
	var have := pack_path()
	if have != "" and _sha_ok(have):
		main.start_info = "Figuren-Paket ist schon da: " + have
		return
	_busy = true
	main.start_info = "Figuren-Paket wird geladen …"
	var to := ProjectSettings.globalize_path("user://" + PACK + ".part")
	var ok := false
	if OS.get_name() == "Windows":
		var th := Thread.new()
		th.start(func(): return OS.execute("curl.exe", ["-L", "--fail", "-s", "-S", "--retry", "2", "-o", to, PACK_URL], [], true, false))
		while th.is_alive():
			await main.get_tree().create_timer(0.3).timeout
		ok = int(th.wait_to_finish()) == 0
	if not ok:
		var http := HTTPRequest.new()
		main.add_child(http)
		http.download_file = to
		http.body_size_limit = PACK_SIZE + 4096
		if http.request(PACK_URL) == OK:
			var r: Array = await http.request_completed
			ok = r[0] == HTTPRequest.RESULT_SUCCESS and r[1] == 200
		http.queue_free()
	_busy = false
	if not ok or not _sha_ok(to):
		DirAccess.remove_absolute(to)
		main.start_info = "Figuren-Paket: Download fehlgeschlagen oder Prüfsumme falsch – nichts geändert."
		return
	var dst := ProjectSettings.globalize_path("user://" + PACK)
	DirAccess.remove_absolute(dst)
	DirAccess.rename_absolute(to, dst)
	reset()
	main.start_info = "Figuren-Paket geladen – neue Besucher kommen mit den neuen Figuren."


static func _sha_ok(p: String) -> bool:
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null or f.get_length() != PACK_SIZE:
		return false
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	f.close()
	return h.finish().hex_encode() == PACK_SHA
