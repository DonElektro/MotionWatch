extends Node
## «Flora und Fauna» Phase 1 (Idee Nr. 5): ein Tier als echtes Modell mit Skelett und eigenen Bewegungen – zuerst der Fuchs.
## Modell: Quaternius «Ultimate Animated Animals» (CC0, wie Maggie), mit werkzeuge/tier_modelle.py zu einem Netz mit
## Fuchs-Fell (Vertex-Farben) gemacht; Datei modelle/fuchs_glb.bin. Fell: shaders/maggie_fell.gdshader (Haarstruktur, Randlicht).
##
## Was gleich bleibt (Wahrheit der Erkennung):
##   - actor.gd bewegt das Tier wie bisher (Weg, Tempo, Flucht, Verhalten aus tiere.gd); das Modell hängt an body_root
##     (gleiche Lage, gleiche Grösse: Rückenhöhe wie die Grundformen).
##   - Das Wärmebild bleibt genau gleich: die Zwillinge der Grundformen (Ebene 2) bleiben sichtbar, nur ihre sichtbaren
##     Teile (Ebene 1) werden ausgeblendet.
##   - Der Rahmen der Trainingsbilder (dataset.gd: sichtbare Netze der Ebene 1) kommt aus «pose_aabb», jede 0.2 s aus den
##     Knochen der Pose gerechnet (wie figur.gd).
##   - Die Augen leuchten nachts wie bisher (a.lights), jetzt am Kopf-Knochen des Modells.
## Bewegungen: Gehen / Traben (Walk, Tempo nach der Geschwindigkeit), Galopp auf der Flucht, Mäusesprung (Gallop_Jump),
## Schnüffeln (Idle_2_HeadLow), Fressen / Graben (Eating), Stehen und Sichern (Idle / Idle_2), weich überblendet.
## Nur ab Stufe «normal» (scripts/flora.gd), nicht in Lite (Pi: die Grundformen bleiben).

const DATEI := {"fox": "res://modelle/fuchs_glb.bin"}
const RUECKEN := {"fox": 2.4002}             # Modell-Einheiten: höchster Punkt am Rumpf (tier_modelle.py gibt ihn aus)
const AUGEN := {"fox": Vector3(0.237, 2.15, 2.199)}   # Modell-Raum (Ruhelage), ± x
const SCHRITT := {"fox": [0.75, 3.2]}         # m/s, bei denen Walk / Gallop mit Tempo 1 ohne Rutschen laufen (geschätzt)
const HAAR := {"fox": 63.0}

static var _bytes := {}
static var fehler := ""

var a
var kind := ""
var sk: Skeleton3D
var mi: MeshInstance3D
var ap: AnimationPlayer
var holder: Node3D
var _cur := ""
var _box_t := 0.0


static func verfuegbar(k: String) -> bool:
	if not DATEI.has(k):
		return false
	if not _bytes.has(k):
		_bytes[k] = FileAccess.get_file_as_bytes(DATEI[k]) if FileAccess.file_exists(DATEI[k]) else PackedByteArray()
		if (_bytes[k] as PackedByteArray).is_empty():
			fehler = "Modell fehlt: " + str(DATEI[k])
	return not (_bytes[k] as PackedByteArray).is_empty()


static func bauen(act) -> Node:
	"""das Modell an actor.gd (Tier) hängen; null = nicht möglich (dann bleiben die Grundformen)"""
	var k: String = act.kind
	if not verfuegbar(k):
		return null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_buffer(_bytes[k], "", st) != OK:
		fehler = "Modell nicht lesbar"
		return null
	var sc := doc.generate_scene(st) as Node3D
	if sc == null:
		return null
	var r = load("res://scripts/tier_modell.gd").new()
	r.name = "tier_modell"
	if not r._aufbauen(act, k, sc):
		r.free()
		sc.free()
		return null
	return r


func _aufbauen(act, k: String, sc: Node3D) -> bool:
	a = act
	kind = k
	var sks := sc.find_children("*", "Skeleton3D", true, false)
	var mis := sc.find_children("*", "MeshInstance3D", true, false)
	var aps := sc.find_children("*", "AnimationPlayer", true, false)
	if sks.is_empty() or mis.is_empty() or aps.is_empty():
		fehler = "Modell ohne Skelett / Bewegungen"
		return false
	sk = sks[0]
	mi = mis[0]
	ap = aps[0]
	# the visible basic shapes go (layer 1); their thermal twins (layer 2) stay - the thermal picture is the same
	for n in a.body_root.find_children("*", "MeshInstance3D", true, false):
		if (n as MeshInstance3D).layers == 1:
			(n as MeshInstance3D).visible = false
	var hb: float = 0.31                                     # actor.gd spec «fox»: back = hb + body radius (hb × 0.32)
	var back_m: float = hb + hb * 0.32
	holder = Node3D.new()
	holder.name = "modell"
	holder.basis = Basis(Vector3.UP, PI).scaled(Vector3.ONE * (back_m / float(RUECKEN[k])))   # the model looks to +z
	a.body_root.add_child(holder)
	holder.add_child(sc)
	var lite := Engine.has_meta("lite") and bool(Engine.get_meta("lite"))
	var fm := ShaderMaterial.new()
	fm.shader = load("res://shaders/maggie_fell.gdshader")
	fm.set_shader_parameter("fein", 0.0 if lite else 1.0)
	fm.set_shader_parameter("haar", float(HAAR[k]))
	fm.set_shader_parameter("rand", 0.45)
	mi.set_surface_override_material(0, fm)
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	mi.extra_cull_margin = 1.0
	# eyes: they shine in the light at night (like _eyes in actor.gd)
	var hi := sk.find_bone("Head")
	if hi >= 0:
		var ba := BoneAttachment3D.new()
		ba.bone_name = "Head"
		sk.add_child(ba)
		var inv := sk.get_bone_global_rest(hi).affine_inverse()
		var em := StandardMaterial3D.new()
		em.albedo_color = Color(0.03, 0.025, 0.02)
		em.roughness = 0.1
		em.emission_enabled = true
		em.emission = Color(0.9, 0.95, 0.8)
		em.emission_energy_multiplier = 0.0
		a.lights.append(em)
		var eye := SphereMesh.new()
		eye.radius = 0.06
		eye.height = 0.09
		eye.radial_segments = 8
		eye.rings = 4
		for s in [-1.0, 1.0]:
			var e := MeshInstance3D.new()
			e.mesh = eye
			e.material_override = em
			e.layers = 1
			var p: Vector3 = AUGEN[k]
			e.position = inv * Vector3(p.x * s, p.y, p.z + 0.01)
			ba.add_child(e)
	for an in ap.get_animation_list():
		var anim := ap.get_animation(an)
		if anim != null:
			anim.loop_mode = Animation.LOOP_NONE if an == "Gallop_Jump" else Animation.LOOP_LINEAR
	_play("Idle_2", 0.0)
	ap.seek(float(a.get_instance_id() % 997) / 997.0 * 2.0, true)   # (no randf(): the global random numbers stay the same)
	process_priority = 120                                   # after actor.gd and tiere.gd
	a.add_child(self)
	_update_box()
	return true


func _play(n: String, blend := 0.3, spd := 1.0) -> void:
	if not ap.has_animation(n):
		return
	if n != _cur:
		ap.play(n, blend)
		_cur = n
	ap.speed_scale = spd


func _process(dt: float) -> void:
	if a == null or not is_instance_valid(a):
		return
	var spd: float = float(a.cur_speed)
	var st := ""
	if a.main != null and a.main.get("tiere") != null:
		var s = a.main.tiere._st.get(a.get_instance_id(), null)
		if typeof(s) == TYPE_DICTIONARY:
			st = str(s.get("st", ""))
	var stp: Array = SCHRITT[kind]
	if st == "pounce":
		_play("Gallop_Jump", 0.15)
	elif spd > 2.6 or (bool(a.fled) and spd > 1.0):
		_play("Gallop", 0.25, clampf(spd / float(stp[1]), 0.6, 2.2))
	elif spd > 0.08:
		_play("Walk", 0.3, clampf(spd / float(stp[0]), 0.4, 2.4))
	else:
		var idle: String = str(a.idle_kind) if a.now_s() < float(a.idle_until) else ""
		match idle:
			"sniff", "halt", "lie":
				_play("Idle_2_HeadLow", 0.4)
			"graze", "root", "dig":
				_play("Eating", 0.4)
			"look":
				_play("Idle", 0.4)
			_:
				_play("Idle_2", 0.5)
	_box_t -= dt
	if _box_t <= 0.0:
		_box_t = 0.2
		_update_box()


func _update_box() -> void:
	"""«pose_aabb» (dataset.gd, vielfalt.gd): the box of the pose from the bones (space of the mesh), with a margin for fur,
	ears, snout and tail tip"""
	if sk == null:
		return
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	var to_mi := mi.transform.affine_inverse() if mi.get_parent() == sk else Transform3D()
	for i in range(sk.get_bone_count()):
		var n := sk.get_bone_name(i)
		if n.begins_with("IK") or n.begins_with("Pole") or n.begins_with("FF"):
			continue
		var p: Vector3 = to_mi * sk.get_bone_global_pose(i).origin
		lo = lo.min(p)
		hi = hi.max(p)
	if lo.x == INF:
		return
	var m := 0.38                                            # model units (≈ 6.5 cm)
	var box := AABB(lo - Vector3(m, m, m), hi - lo + Vector3(2 * m, 2 * m, 2 * m))
	box = box.merge(AABB(Vector3(box.position.x, minf(box.position.y, 0.0), box.position.z), Vector3(box.size.x, 0.01, box.size.z)))   # down to the paws
	mi.set_meta("pose_aabb", box)
