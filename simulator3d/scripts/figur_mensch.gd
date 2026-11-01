extends "res://scripts/figur_paket.gd"
## «Figuren menschlicher» (01.11.2026): Menschen aus dem Menschen-Paket (MakeHuman / MPFB2, CC0) für Grafik mittel / hoch.
## Echte Proportionen (Mann, Frau, schlank, kräftig, Ältere, Kinder), Gesicht mit Augen, Brauen, Wimpern, Lippen, Haare
## (kurz, lang, Dutt, Kranz), Kleider mit Stoffstruktur, Saum und Sohle, Haut mit Rand-Licht (Rim) und - in Forward+ -
## leichter Streuung (Subsurface). Das Paket (menschen_v1.zip, ~5 MB, werkzeuge/menschen_paket.py) ist NICHT im
## Simulator-ZIP: neben der .exe, in user:// («Menschen-Paket laden», System → Grafik) oder simulator3d/pakete/ (Tests).
##
## Gleiche Schnittstelle und gleiche Bewegungen wie figur_paket.gd (davon abgeleitet): das Skelett hat die Knochen und die
## Ruhe-Ausrichtung der Quaternius-Animationen (Retarget beim Bauen des Pakets), darum laufen dieselben Clips; die Gelenke
## von actor.gd (Kriechen, Winken, Handlungen aus anim_mensch.gd) kommen über _retarget() wie bisher.
## Leistung: ein Netz pro Figur (Teile je Kleidung / Haar einmal zusammengesetzt und geteilt), automatische LOD-Stufen
## (ImporterMesh.generate_lods), ab LOD_FAR Metern Bewegung nur jedes 2. Bild, ab 2 × LOD_FAR jedes 4.

const MPACK := "menschen_v1.zip"
const MPACK_URL := "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/simulator3d/pakete/menschen_v1.zip"
const MPACK_SIZE := 5350219
const MPACK_SHA := "9ba3eaef7da96fa9279121690087c55464b06e35da6d1130486f0d93651a3b39"
const REF_HP := 0.9491                     # height of the pelvis of the clips (library «m» of figur_paket.gd)
const BASE_H := 1.86                       # actor.gd BASE_H: height of a figure with body_root.scale.y = 1
const LOD_FAR := 25.0                      # m: further away the bones move less often (and the LOD meshes are smaller)
const GROUPS := [                          # surface -> parts of the pack (in this order; names in lower case)
	["skin", ["skin"]], ["skin_hand", ["skin_hand"]], ["bare_arm", ["bare_arm"]], ["bare_leg", ["bare_leg"]],
	["jacke", ["jacke", "aermel", "kapuze"]], ["hose", ["hose", "hosenbein"]], ["schuh", ["schuh"]],
	["hair", ["haar", "brauen", "wimpern"]], ["eye", ["augen"]]]

static var mensch_mode := ""               # tests: "" | "aus" (always the Quaternius pack)
static var _ms := {}                       # the loaded pack: man, bodies {key: {scene, skin, parts}}
static var _mtried := ""
static var mlast_error := ""
static var _meshes := {}                   # composed meshes (shared by all figures with the same body / clothes / hair)
static var _tex := {}                      # generated textures: weave, strands, pores
static var lods := true                    # tests: LOD meshes

var body_key := ""
var hair_key := ""
var info_b := {}
var _pel_k := 1.0
var _stoop := 0.0
var _hood := false
var _short := [false, false]
var _p := {}
var _skip_n := 0
var _acc := 0.0


# ---- the pack --------------------------------------------------------------------------------------------------------
static func mpack_paths() -> Array:
	var out := []
	var exe_dir := OS.get_executable_path().get_base_dir()
	out.append(exe_dir.path_join(MPACK))
	out.append(exe_dir.path_join("figuren").path_join(MPACK))
	out.append(ProjectSettings.globalize_path("user://" + MPACK))
	out.append(ProjectSettings.globalize_path("res://").path_join("pakete").path_join(MPACK))
	return out


static func mpack_path() -> String:
	for p in mpack_paths():
		if FileAccess.file_exists(p):
			return p
	return ""


static func wanted(main) -> bool:
	"""a figure from the Menschen-Paket? (actor.gd asks this first; then figur_paket.gd, then figur.gd)"""
	load_setting()
	if mensch_mode == "aus" or (mode == "" and setting in ["eigen", "quaternius"]) or mode == "aus":
		return false
	if mode != "an":
		var Quality = load("res://scripts/quality.gd")
		if Quality.lite() or str(main.quality) == "simple":
			return false
	return ensure_mloaded() and clips_ok()


static func ensure_mloaded() -> bool:
	if not _ms.is_empty():
		return true
	var p := mpack_path()
	if p == "" or p == _mtried:
		return false
	_mtried = p
	var t0 := Time.get_ticks_msec()
	var zr := ZIPReader.new()
	if zr.open(p) != OK:
		mlast_error = "menschen_v1.zip: open failed " + p
		return false
	var man = JSON.parse_string(zr.read_file("menschen.json").get_string_from_utf8())
	if typeof(man) != TYPE_DICTIONARY or int(man.get("version", 0)) < 1:
		mlast_error = "menschen.json: missing or broken"
		zr.close()
		return false
	var bodies := {}
	for k in man["koerper"]:
		var n := _gen(zr.read_file(str(man["koerper"][k]["file"])))
		if n == null:
			mlast_error = "menschen_v1.zip: this file is broken: " + str(man["koerper"][k]["file"])
			zr.close()
			return false
		var parts := {}
		var sk: Skin = null
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var m3 := mi as MeshInstance3D
			if m3.mesh == null:
				continue
			parts[str(m3.name).to_lower()] = m3.mesh.surface_get_arrays(0)
			if sk == null:
				sk = m3.skin
			m3.get_parent().remove_child(m3)
			m3.free()
		var ps := PackedScene.new()
		for c in n.find_children("*", "", true, false):
			c.owner = n
		ps.pack(n)
		n.free()
		bodies[k] = {"scene": ps, "skin": sk, "parts": parts}
	zr.close()
	# the clips come from the same ZIP (anim_1.glb, anim_2.glb): figur_paket.gd loads them, if its own pack is missing
	_ms = {"man": man, "bodies": bodies, "path": p}
	print("Menschen-Paket: %s geladen (%d Körper, %d ms)" % [p, bodies.size(), Time.get_ticks_msec() - t0])
	mlast_error = ""
	return true


static func clips_ok() -> bool:
	"""the clips: from the Quaternius pack if it is there, else the same clips inside the Menschen-Paket"""
	if not clip_libs().is_empty():
		return true
	return load_clips(mpack_path(), "menschen.json")


static func minfo() -> Dictionary:
	return {"loaded": not _ms.is_empty(), "path": _ms.get("path", mpack_path()), "error": mlast_error, "meshes": _meshes.size()}


static func mreset() -> void:
	_ms = {}
	_mtried = ""
	_meshes = {}


# ---- building --------------------------------------------------------------------------------------------------------
func build(actor, p: Dictionary) -> void:
	a = actor
	name = "figur"
	_p = p
	var man: Dictionary = _ms["man"]
	var v: String = a.variant
	var kid: bool = v == "child"
	var old: bool = v == "elderly" or str(p.get("alter", "")) == "alt"
	sex = str(p.get("sex", ""))
	if sex == "":
		sex = "f" if randf() < (0.45 if not v in ["police", "burglar", "courier"] else 0.25) else "m"
	var bau := str(p.get("bau", ""))
	if bau == "":
		bau = "kraeftig" if float(p.get("wide", 1.0)) > 1.05 else "schlank"
	var want := ("k_" + sex) if kid else (("%s_alt" % sex) if old else ("%s_%s" % [sex, bau]))
	if not man["koerper"].has(want):
		want = man["koerper"].keys()[0]
	body_key = want
	info_b = man["koerper"][want]
	var B: Dictionary = _ms["bodies"][want]
	root3 = (B["scene"] as PackedScene).instantiate()
	add_child(root3)
	root3.rotation.y = PI                                         # the model looks to +z, actor.gd to -z
	var wide: float = maxf(0.5, float(p.get("wide", 1.0)))
	var s: float = BASE_H / maxf(0.5, float(info_b.get("hoehe", 1.75)))
	root3.scale = Vector3(s / wide, s, s / wide)                  # the build is in the body itself
	skel = _skel_of(root3)
	skel.name = "Skeleton3D"
	for i in range(skel.get_bone_count()):
		_bi[skel.get_bone_name(i)] = i
	_pel_k = float(info_b.get("becken", REF_HP)) / REF_HP
	_stoop = 0.16 if old else 0.0
	var hs: Array = info_b.get("haare", ["kurz"])
	hair_key = str(p.get("haar", ""))
	if not hair_key in hs:
		hair_key = str(hs[randi() % hs.size()])
	_short = [bool(p.get("shorts", false)), bool(p.get("short_sleeves", false))]
	_hood = bool(p.get("hood", false))
	mi = MeshInstance3D.new()
	mi.name = "Body"
	skel.add_child(mi)
	mi.skin = B["skin"]
	mi.skeleton = NodePath("..")
	mi.mesh = _compose()
	mi.set_meta("hair", true)                                     # figur_paket.gd _attach(): the hair from shapes goes
	meshes = [mi]
	ap = AnimationPlayer.new()
	root3.add_child(ap)
	ap.root_node = ap.get_path_to(skel.get_parent())
	ap.add_animation_library("", clip_libs()["m"])
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	ap.playback_default_blend_time = 0.25
	_reference()
	_ref_pelvis *= _pel_k
	_dress(p)
	_thermal(p)
	_bone_boxes()
	_play("Idle_Loop", 0.0, 1.0)
	ap.seek(randf() * 2.0, true)
	sync(0.0)


func _compose() -> Mesh:
	"""one mesh from the parts: skin, clothes (long or short), one hair (or the hood) - made once, shared"""
	var key := "%s|%s|%d%d|%d" % [body_key, hair_key, int(_short[0]), int(_short[1]), int(_hood)]
	if _meshes.has(key):
		return _meshes[key]
	var parts: Dictionary = _ms["bodies"][body_key]["parts"]
	var use := {}
	for k in parts:
		use[k] = true
	for k in parts:
		if str(k).begins_with("haar_"):
			use[k] = false
	use["haar_" + hair_key] = not _hood
	use["kapuze"] = _hood
	use["aermel"] = not _short[1]
	use["bare_arm"] = _short[1]
	use["hosenbein"] = not _short[0]
	use["bare_leg"] = _short[0]
	var im := ImporterMesh.new()
	for g in GROUPS:
		var arrs := []
		for pn in g[1]:
			var full: String = pn
			if pn == "haar":
				full = "haar_" + hair_key
			if parts.has(full) and bool(use.get(full, false)):
				arrs.append(parts[full])
		if arrs.is_empty():
			continue
		var arr: Array = arrs[0] if arrs.size() == 1 else _merge(arrs)
		var mt := StandardMaterial3D.new()
		mt.resource_name = g[0]
		var flags := 0
		im.add_surface(Mesh.PRIMITIVE_TRIANGLES, arr, [], {}, mt, g[0], flags)
	if lods:
		im.generate_lods(25.0, 60.0, [])
	var m := im.get_mesh()
	_meshes[key] = m
	return m


static func _merge(list: Array) -> Array:
	"""the arrays of several parts as one surface (same format: vertex, normal, uv, colour, bones, weights, index)"""
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	var V := PackedVector3Array()
	var N := PackedVector3Array()
	var TG := PackedFloat32Array()
	var UV := PackedVector2Array()
	var C := PackedColorArray()
	var Bn := PackedInt32Array()
	var W := PackedFloat32Array()
	var I := PackedInt32Array()
	for arr in list:
		var off := V.size()
		V.append_array(arr[Mesh.ARRAY_VERTEX])
		N.append_array(arr[Mesh.ARRAY_NORMAL])
		if arr[Mesh.ARRAY_TANGENT] != null:
			TG.append_array(arr[Mesh.ARRAY_TANGENT])
		UV.append_array(arr[Mesh.ARRAY_TEX_UV])
		C.append_array(arr[Mesh.ARRAY_COLOR])
		Bn.append_array(arr[Mesh.ARRAY_BONES])
		W.append_array(arr[Mesh.ARRAY_WEIGHTS])
		var ii: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		for x in ii:
			I.append(x + off)
	out[Mesh.ARRAY_VERTEX] = V
	out[Mesh.ARRAY_NORMAL] = N
	if TG.size() == V.size() * 4:
		out[Mesh.ARRAY_TANGENT] = TG
	out[Mesh.ARRAY_TEX_UV] = UV
	out[Mesh.ARRAY_COLOR] = C
	out[Mesh.ARRAY_BONES] = Bn
	out[Mesh.ARRAY_WEIGHTS] = W
	out[Mesh.ARRAY_INDEX] = I
	return out


func hood(on: bool) -> void:
	"""actor.gd add_hood(): the hood of the jacket instead of the hair"""
	if on == _hood or mi == null:
		return
	_hood = on
	mi.mesh = _compose()
	if not twins.is_empty():
		(twins[0] as MeshInstance3D).mesh = mi.mesh
	_dress(_p)
	_thermal_mats(_p)


# ---- materials -------------------------------------------------------------------------------------------------------
static func _weave() -> Texture2D:
	"""a fabric (normal map): threads over and under, made once"""
	if _tex.has("weave"):
		return _tex["weave"]
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for y in range(n):
		for x in range(n):
			var cx := (x % 8) / 8.0
			var cy := (y % 8) / 8.0
			var warp := ((x / 8 + y / 8) % 2) == 0
			var h := sin(cx * PI) if warp else sin(cy * PI)
			h = 0.25 + 0.6 * h + 0.15 * sin(float(x * 7 + y * 13))
			img.set_pixel(x, y, Color(h, h, h))
	img.bump_map_to_normal_map(3.0)
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_tex["weave"] = t
	return t


static func _strands() -> Texture2D:
	"""hair: fine strands along v (normal map)"""
	if _tex.has("strands"):
		return _tex["strands"]
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var col := []
	for x in range(n):
		col.append(rng.randf())
	for y in range(n):
		for x in range(n):
			var h: float = 0.5 + 0.4 * sin(float(x) * 1.7 + col[x] * 6.0) * (0.7 + 0.3 * sin(float(y) * 0.2 + col[x] * 9.0))
			img.set_pixel(x, y, Color(h, h, h))
	img.bump_map_to_normal_map(4.0)
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_tex["strands"] = t
	return t


static func _pores() -> Texture2D:
	if _tex.has("pores"):
		return _tex["pores"]
	var nt := NoiseTexture2D.new()
	nt.width = 128
	nt.height = 128
	nt.seamless = true
	nt.as_normal_map = true
	nt.bump_strength = 1.2
	var fn := FastNoiseLite.new()
	fn.frequency = 0.25
	nt.noise = fn
	_tex["pores"] = nt
	return nt


func _dress(p: Dictionary) -> void:
	var skin: Color = p.get("skin", Color(0.85, 0.66, 0.55))
	_hair_c = p.get("hair", Color(0.3, 0.2, 0.1))
	var rain: bool = str(p.get("stil", "")) == "regen"
	var hq: bool = str(a.main.quality) in ["nice", "ultra"]
	_mats = {}
	var m: Mesh = mi.mesh
	for si in range(m.get_surface_count()):
		var nm := str(m.surface_get_material(si).resource_name) if m.surface_get_material(si) != null else ""
		var mt := StandardMaterial3D.new()
		mt.resource_name = nm
		mt.vertex_color_use_as_albedo = true
		var key := nm
		match nm:
			"skin", "skin_hand", "bare_arm", "bare_leg":
				key = "skin"
				mt.albedo_color = Color(skin.r / 0.8, skin.g / 0.8, skin.b / 0.8)
				mt.roughness = 0.55
				mt.metallic_specular = 0.35
				mt.rim_enabled = true
				mt.rim = 0.25
				mt.rim_tint = 0.6
				if hq:
					mt.subsurf_scatter_enabled = true                # Forward+ only (Mobile / Compatibility: ignored)
					mt.subsurf_scatter_strength = 0.3
					mt.subsurf_scatter_skin_mode = true
					mt.normal_enabled = true
					mt.normal_texture = _pores()
					mt.normal_scale = 0.15
					mt.uv1_scale = Vector3(14, 14, 1)
			"hair":
				key = "hair"
				mt.albedo_color = Color(_hair_c.r / 0.8, _hair_c.g / 0.8, _hair_c.b / 0.8)
				mt.roughness = 0.55
				mt.metallic_specular = 0.45
				mt.rim_enabled = true
				mt.rim = 0.3
				mt.rim_tint = 0.3
				mt.normal_enabled = true
				mt.normal_texture = _strands()
				mt.normal_scale = 0.7
				mt.uv1_scale = Vector3(3, 1, 1)
			"eye":
				key = "eye"
				mt.albedo_color = Color(1, 1, 1)
				mt.roughness = 0.08
				mt.metallic_specular = 0.8
			"jacke", "hose", "schuh":
				key = {"jacke": "jacket", "hose": "trousers", "schuh": "shoe"}[nm]
				var c: Color = p.get(key, Color(0.3, 0.3, 0.3))
				mt.albedo_color = Color(c.r / 0.8, c.g / 0.8, c.b / 0.8)
				mt.roughness = 0.42 if (rain and nm == "jacke") else (0.6 if nm == "schuh" else 0.9)
				if nm != "schuh":
					mt.normal_enabled = true
					mt.normal_texture = _weave()
					mt.normal_scale = 0.25 if (rain and nm == "jacke") else 0.6
					mt.uv1_scale = Vector3(36, 36, 1)
		mi.set_surface_override_material(si, mt)
		if not _mats.has(key):
			_mats[key] = []
		_mats[key].append(mt)


func recolour(jacket, trousers) -> void:
	if jacket != null:
		for mt in _mats.get("jacket", []):
			var c: Color = jacket
			mt.albedo_color = Color(c.r / 0.8, c.g / 0.8, c.b / 0.8)
	if trousers != null:
		for mt in _mats.get("trousers", []):
			var c2: Color = trousers
			mt.albedo_color = Color(c2.r / 0.8, c2.g / 0.8, c2.b / 0.8)


func _thermal(p: Dictionary) -> void:
	var t := MeshInstance3D.new()
	t.mesh = mi.mesh
	t.skin = mi.skin
	t.layers = 2
	t.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	skel.add_child(t)
	t.skeleton = NodePath("..")
	twins = [t]
	th = t
	_thermal_mats(p)


func _thermal_mats(p: Dictionary) -> void:
	"""skin warm (face, hands, bare arms / legs as waerme.gd), clothes as warm as actor.gd says, hair and shoes cooler"""
	if th == null:
		return
	var ct: float = p.get("cloth_t", 26.0)
	var main = a.main
	var amb: float = float(main.ambient)
	var act: bool = p.get("active", false)
	var gloves: bool = p.get("gloves", false)
	var real: bool = main.simreal != null and main.simreal.th_real
	var m: Mesh = th.mesh
	for si in range(m.get_surface_count()):
		var nm := str(m.surface_get_material(si).resource_name) if m.surface_get_material(si) != null else ""
		var temp := ct
		match nm:
			"skin":
				temp = Waerme.skin("face", amb, act) if real else 34.5
			"skin_hand":
				temp = (Waerme.skin("hand", amb, act) if real else 32.0) if not gloves else 24.0
			"bare_arm":
				temp = Waerme.skin("arm", amb, act)
			"bare_leg":
				temp = Waerme.skin("leg", amb, act)
			"hair":
				temp = 30.0 if not gloves else 27.0
			"eye":
				temp = 34.5
			"schuh":
				temp = ct - 4.0
		th.set_surface_override_material(si, main.tmat_fixed(temp))


# ---- every frame -----------------------------------------------------------------------------------------------------
func _nach_clip() -> void:
	"""after the clip: the pelvis to the height of this body, the older ones bent a little forward"""
	if _bi.has("pelvis"):
		var pi_: int = _bi["pelvis"]
		skel.set_bone_pose_position(pi_, skel.get_bone_pose_position(pi_) * _pel_k)
	if _stoop > 0.0 and _w_full < 0.5:
		var Rs: Quaternion = Quaternion(_Ki) * Quaternion(Vector3.RIGHT, -_stoop * 0.5) * Quaternion(_K)
		for bn in ["spine_02", "spine_03"]:
			if not _bi.has(bn):
				continue
			var i: int = _bi[bn]
			var pg: Quaternion = _parent_global(skel.get_bone_parent(i))
			skel.set_bone_pose_rotation(i, (pg.inverse() * Rs * pg * skel.get_bone_pose_rotation(i)).normalized())
		if _bi.has("neck_01"):
			var j: int = _bi["neck_01"]
			var pg2: Quaternion = _parent_global(skel.get_bone_parent(j))
			var Rb: Quaternion = Quaternion(_Ki) * Quaternion(Vector3.RIGHT, _stoop * 0.8) * Quaternion(_K)
			skel.set_bone_pose_rotation(j, (pg2.inverse() * Rb * pg2 * skel.get_bone_pose_rotation(j)).normalized())


func _rate() -> int:
	"""LOD of the movement: near every frame, beyond LOD_FAR every 2nd, beyond 2 × LOD_FAR every 4th"""
	var vp: Viewport = a.get_viewport() if a.is_inside_tree() else null
	var cam: Camera3D = vp.get_camera_3d() if vp != null else null
	if cam == null:
		return 1
	var d: float = cam.global_position.distance_to(a.global_position)
	return 1 if d < LOD_FAR else (2 if d < 2.0 * LOD_FAR else 4)


func sync(dt: float) -> void:
	if skel == null or ap == null:
		return
	_acc += dt
	_skip_n += 1
	if dt > 0.0 and _skip_n % _rate() != 0:
		var br: Node3D = a.body_root                             # the joints of actor.gd still must not move the body
		var wf := _w_full
		var keep_x: float = br.position.x if a.variant == "drunk" else 0.0
		br.position = Vector3(lerpf(keep_x, br.position.x, wf), br.position.y * wf, br.position.z * wf)
		br.rotation = Vector3(br.rotation.x * wf, 0.0, br.rotation.z if a.variant == "drunk" else br.rotation.z * wf)
		return
	var d2 := _acc
	_acc = 0.0
	super.sync(d2)
