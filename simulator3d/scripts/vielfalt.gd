extends RefCounted
## 3D-4.x «Vielfalt» der Trainingsbilder (domain randomisation, Wunsch Daniel): dataset.gd fragt hier nach zufälligen
## Kleidern (Farben, Muster), Haltungen, Dingen in der Hand, Licht (Sonnenstand, Lampen, Farbtemperatur), Wetter,
## Verdeckung (Hecke, Zaun, Auto davor), schwierigen leeren Bildern (Ast vor der Linse, Fahne, Licht, Insekten) und
## Kamera-Fehlern (Rauschen, Unschärfe, Bewegungsunschärfe, JPEG-Qualität). Dazu misst es pro Objekt, wie viel davon
## verdeckt ist und wie hell es im Bild ist (für labels_meta/ und die Auswertung «wo versagt die KI»).
## Nur Bilddaten, keine Kartendaten. Alles, was hier entsteht, hängt unter `holder` und wird nach jedem Bild gelöscht.

const Scenes = preload("res://scripts/scenes.gd")

var main
var hi := false                  # «Vielfalt: hoch»
var holder: Node3D = null        # everything added for one picture (lamps, occluders, negatives)
var occluders: Array = []        # [MeshInstance3D, size] - boxes that may hide a visitor (own ones)
var _tex: Array = []             # pattern textures for clothes
var _noise: Array = []           # noise tiles (RGBA8, different strength)

const POSTURES := ["stehend", "geduckt", "kriechend"]
const NEG_KINDS := ["ast", "fahne", "licht", "insekt", "schatten"]
const CARRY := ["kiste", "tasche", "brett", "sack", "kanister"]


func scene_list() -> Array:
	"""all scenes for «hoch» (incl. the real place when one is loaded and «Meine Vorlage» when a file is there);
	the bedroom (indoor, the alarm clock) is left out"""
	var out := []
	for s in Scenes.LIST:
		var id: String = s[0]
		if id == "schlafzimmer":
			continue
		if id == "ort" and not (main.geo != null and main.geo.loaded):
			continue
		if id == "vorlage":
			var d := DirAccess.open("user://vorlagen")
			if d == null or d.get_files().is_empty():
				continue
		out.append(id)
	return out


func begin() -> void:
	end()
	holder = Node3D.new()
	holder.name = "vielfalt"
	main.add_child(holder)
	occluders = []


func end() -> void:
	if holder != null and is_instance_valid(holder):
		holder.queue_free()
	holder = null
	occluders = []


# ---- light ---------------------------------------------------------------------------------------------------------
static func kelvin(k: float) -> Color:
	"""colour of a light of k kelvin (approximation by Tanner Helland), 1800 .. 9000 K"""
	var t := clampf(k, 1000.0, 40000.0) / 100.0
	var r := 255.0 if t <= 66.0 else 329.7 * pow(t - 60.0, -0.1332)
	var g := (99.47 * log(t) - 161.12) if t <= 66.0 else 288.12 * pow(t - 60.0, -0.0755)
	var b := 255.0 if t >= 66.0 else (0.0 if t <= 19.0 else 138.52 * log(t - 10.0) - 305.04)
	return Color(clampf(r, 0, 255) / 255.0, clampf(g, 0, 255) / 255.0, clampf(b, 0, 255) / 255.0)


func add_lamps(aim_yaw: float) -> Array:
	"""at night 1-2 lamps near where the camera looks (yard lamp, lantern, window): colour temperature 2200-6500 K"""
	var out := []
	for i in range(1 if randf() < 0.6 else 2):
		var a := aim_yaw + deg_to_rad(randf_range(-35.0, 35.0))
		var d := randf_range(3.0, 14.0)
		var p: Vector3 = main.rig.global_position + Vector3(-sin(a) * d, 0, -cos(a) * d)
		p.y = main.ground_y(p.x, p.z) + randf_range(1.8, 4.0)
		var k := randf_range(2200.0, 6500.0)
		var l := OmniLight3D.new()
		l.light_color = kelvin(k)
		l.light_energy = randf_range(1.5, 6.0)
		l.omni_range = randf_range(7.0, 16.0)
		l.shadow_enabled = randf() < 0.5
		holder.add_child(l)
		l.global_position = p
		var b := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.08
		sm.height = 0.16
		b.mesh = sm
		var m := StandardMaterial3D.new()
		m.albedo_color = l.light_color
		m.emission_enabled = true
		m.emission = l.light_color
		m.emission_energy_multiplier = 6.0
		b.material_override = m
		holder.add_child(b)
		b.global_position = p
		out.append({"kelvin": int(k), "dist": snappedf(d, 0.1), "energy": snappedf(l.light_energy, 0.1)})
	return out


# ---- clothes, animals, things to carry -------------------------------------------------------------------------------
func _patterns() -> void:
	if not _tex.is_empty():
		return
	for kind in ["streifen", "karo", "tarn", "punkte"]:
		var im := Image.create(16, 16, false, Image.FORMAT_RGB8)
		for y in 16:
			for x in 16:
				var v := 1.0
				match kind:
					"streifen":
						v = 1.0 if (y / 2) % 2 == 0 else 0.55
					"karo":
						v = 1.0 if ((x / 4) + (y / 4)) % 2 == 0 else 0.6
					"tarn":
						v = 0.6 + 0.4 * (0.5 + 0.5 * sin(x * 0.9 + y * 0.4) * cos(y * 0.7 - x * 0.3))
					"punkte":
						v = 0.55 if (x % 6 < 2 and y % 6 < 2) else 1.0
				im.set_pixel(x, y, Color(v, v, v))
		_tex.append([kind, ImageTexture.create_from_image(im)])


func _cloth_mat(c: Color, pattern: int) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = randf_range(0.6, 0.95)
	if pattern >= 0:
		_patterns()
		m.albedo_texture = _tex[pattern][1]
		m.uv1_triplanar = true
		m.uv1_scale = Vector3.ONE * randf_range(3.0, 9.0)
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	return m


static func rand_cloth_colour() -> Color:
	var r := randf()
	if r < 0.12:
		return Color(0.05, 0.05, 0.06).lightened(randf() * 0.1)              # black
	if r < 0.2:
		return Color(0.92, 0.92, 0.9)                                     # white
	if r < 0.27:
		return Color(0.85, 0.95, 0.15)                                    # hi-vis yellow
	if r < 0.4:
		return Color.from_hsv(randf_range(0.18, 0.32), randf_range(0.3, 0.6), randf_range(0.2, 0.45))   # olive / camo green
	if r < 0.5:
		return Color.from_hsv(randf_range(0.05, 0.11), randf_range(0.3, 0.7), randf_range(0.2, 0.5))    # brown / beige
	return Color.from_hsv(randf(), randf_range(0.25, 0.95), randf_range(0.15, 0.95))


func _meshes(v: Node) -> Array:
	var out := []
	for m in v.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		if mi.layers & 1 and mi.visible and mi.mesh != null:
			out.append(mi)
	return out


func _first_colour(n: Node3D):
	if n == null:
		return null
	for c in n.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).layers & 1 and c.material_override is StandardMaterial3D:
			return (c.material_override as StandardMaterial3D).albedo_color
	return null


func dress(v) -> String:
	"""new jacket and trousers (colour, now and then a pattern) - returns a short description for the meta file"""
	if v.get("fig") != null:                         # 3D-4.12: the figure with a skeleton - new colours (no pattern)
		var fj := rand_cloth_colour()
		var ft := rand_cloth_colour() if randf() < 0.7 else fj.darkened(0.3)
		v.fig.recolour(fj, ft)
		return "#%s/#%s" % [fj.to_html(false), ft.to_html(false)]
	var jc = _first_colour(v.torso)
	var tc = _first_colour(v.hips)
	if jc == null:
		return ""
	var pat := randi() % 4 if randf() < 0.4 else -1
	var nj := rand_cloth_colour()
	var nt := rand_cloth_colour() if randf() < 0.7 else nj.darkened(0.3)
	var mj := _cloth_mat(nj, pat)
	var mt := _cloth_mat(nt, -1 if randf() < 0.7 else randi() % 4)
	for mi in _meshes(v):
		var m = mi.material_override
		if not (m is StandardMaterial3D):
			continue
		var c: Color = (m as StandardMaterial3D).albedo_color
		if c.is_equal_approx(jc):
			mi.material_override = mj
		elif tc != null and c.is_equal_approx(tc):
			mi.material_override = mt
	return "#%s/#%s%s" % [nj.to_html(false), nt.to_html(false), (" " + str(_tex[pat][0])) if pat >= 0 else ""]


func vary_animal(v) -> Dictionary:
	"""a bit bigger or smaller, fur a bit lighter or darker"""
	var s := randf_range(0.85, 1.2)
	v.scale = Vector3.ONE * s
	var f := randf_range(0.75, 1.25)
	var done := {}
	for mi in _meshes(v):
		var m = mi.material_override
		if not (m is StandardMaterial3D) or (m as StandardMaterial3D).emission_enabled:
			continue
		if not done.has(m):
			var m2: StandardMaterial3D = (m as StandardMaterial3D).duplicate()
			var c: Color = m2.albedo_color
			m2.albedo_color = Color(clampf(c.r * f, 0, 1), clampf(c.g * f, 0, 1), clampf(c.b * f, 0, 1), c.a)
			done[m] = m2
		mi.material_override = done[m]
	return {"scale": snappedf(s, 0.01), "fur": snappedf(f, 0.01)}


func vary_person(v) -> Dictionary:
	"""3D-4.12: height, build, hood, backpack, umbrella (figur.gd)"""
	return preload("res://scripts/figur.gd").vary(v)


func carry(v) -> String:
	"""something in the hands or on the shoulder - the AI must still see the person"""
	if v.torso == null or v.arms.size() < 2:
		return ""
	var what: String = CARRY[randi() % CARRY.size()]
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	var col := rand_cloth_colour()
	var parent: Node3D = v.torso
	match what:
		"kiste":
			bm.size = Vector3(0.45, 0.32, 0.32)
			mi.position = Vector3(0, 0.15, -0.34)
			col = Color(0.7, 0.55, 0.35) if randf() < 0.6 else col
		"tasche":
			bm.size = Vector3(0.12, 0.32, 0.38)
			parent = v.arms[1][2]
			mi.position = Vector3(0.05, -0.5, 0)
		"brett":
			bm.size = Vector3(0.12, 0.05, randf_range(1.6, 2.6))
			mi.position = Vector3(0.22, 0.56, 0)
			col = Color(0.6, 0.45, 0.28) if randf() < 0.6 else Color(0.7, 0.7, 0.72)
		"sack":
			bm.size = Vector3(0.45, 0.55, 0.3)
			mi.position = Vector3(0, 0.45, 0.25)
			col = Color(0.75, 0.7, 0.55) if randf() < 0.5 else col
		"kanister":
			bm.size = Vector3(0.18, 0.34, 0.3)
			parent = v.arms[0][2]
			mi.position = Vector3(-0.04, -0.52, 0)
			col = [Color(0.8, 0.1, 0.1), Color(0.15, 0.4, 0.15), Color(0.2, 0.2, 0.2)][randi() % 3]
	mi.mesh = bm
	mi.material_override = main.mat(col)
	parent.add_child(mi)
	if what == "kiste":
		v.carry = true                                   # 3D-4.12: both hands hold the box
	return what


static func set_posture(v, post: int) -> void:
	"""0 standing, 1 crouching, 2 crawling - for a visitor that is not a player (actor.gd keeps crouch / prone)"""
	v.ctl_posture = post
	v.crouch = 1.0 if post >= 1 else 0.0
	v.prone = 1.0 if post == 2 else 0.0


# ---- occlusion -------------------------------------------------------------------------------------------------------
func add_occluder(cam: Vector3, target: Vector3) -> String:
	"""a hedge, a fence, a car or a bush between the camera and the visitor - hides part of it"""
	var kinds := ["hecke", "zaun", "auto", "busch", "kiste"]
	var what: String = kinds[randi() % kinds.size()]
	var t := randf_range(0.45, 0.85)
	var p := cam.lerp(target, t)
	var side := Vector3(target.z - cam.z, 0, -(target.x - cam.x)).normalized()
	p += side * randf_range(-0.5, 0.5)
	p.y = main.ground_y(p.x, p.z)
	var size := Vector3.ONE
	var col := Color(0.2, 0.35, 0.15)
	match what:
		"hecke":
			size = Vector3(randf_range(1.5, 3.5), randf_range(0.7, 1.4), 0.6)
		"zaun":
			size = Vector3(randf_range(2.0, 4.0), randf_range(0.8, 1.2), 0.06)
			col = Color(0.45, 0.33, 0.2)
		"auto":
			size = Vector3(4.2, 1.45, 1.8)
			col = rand_cloth_colour()
		"busch":
			size = Vector3(randf_range(0.8, 1.6), randf_range(0.6, 1.5), randf_range(0.8, 1.4))
			col = Color(0.18, randf_range(0.3, 0.45), 0.12)
		"kiste":
			size = Vector3(randf_range(0.6, 1.2), randf_range(0.5, 1.1), randf_range(0.6, 1.0))
			col = Color(0.55, 0.42, 0.28)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = main.mat(col)
	holder.add_child(mi)
	mi.global_position = p + Vector3(0, size.y / 2.0, 0)
	mi.look_at(mi.global_position + side, Vector3.UP)       # broad side to the camera
	mi.rotate_y(PI / 2.0)
	occluders.append([mi, size])
	return what


func _seg_hits_box(a: Vector3, b: Vector3, n: Node3D, aabb: AABB) -> bool:
	var inv := n.global_transform.affine_inverse()
	return aabb.intersects_segment(inv * a, inv * b) != null


func occlusion(v, cam: Vector3, others: Array) -> float:
	"""0 = fully visible, 1 = hidden: sample points on the body parts (weighted by their size), each tested against the
	objects of the scene (main.line_free), the own occluders and the other visitors"""
	var tot := 0.0
	var hid := 0.0
	var boxes := []
	for o in occluders:
		if is_instance_valid(o[0]):
			boxes.append([o[0], AABB(-o[1] / 2.0, o[1])])
	for ov in others:
		if is_instance_valid(ov) and ov != v:
			boxes.append([ov, _local_aabb(ov).grow(-0.05)])
	var items := []
	for mi in _meshes(v):
		if mi.has_meta("pose_parts"):                    # 3D-4.12: a skinned figure - every bone in its pose
			for pp in mi.get_meta("pose_parts"):
				items.append([mi.global_transform * (pp[0] as Transform3D), pp[1]])
		elif not mi.has_meta("pose_aabb"):
			items.append([mi.global_transform, mi.get_aabb()])
	for it in items:
		var ab: AABB = it[1]
		var xf: Transform3D = it[0]
		var ext: Vector3 = (xf.basis * ab.size).abs()
		var w: float = ext.x * ext.y + ext.y * ext.z + ext.x * ext.z
		if w < 0.004:
			continue                                     # eyes, buttons: too small to count
		var c: Vector3 = ab.get_center()
		var ax := Vector3.ZERO
		var lng: int = ab.size.max_axis_index()
		ax[lng] = ab.size[lng] * 0.3
		for q in [c, c + ax, c - ax]:
			var pw: Vector3 = xf * q
			tot += w
			var blocked: bool = not main.line_free(cam, pw)
			if not blocked:
				for bx in boxes:
					if _seg_hits_box(cam, pw, bx[0], bx[1]):
						blocked = true
						break
			if blocked:
				hid += w
	return clampf(hid / tot, 0.0, 1.0) if tot > 0.0 else 1.0


func _local_aabb(v: Node3D) -> AABB:
	var inv := v.global_transform.affine_inverse()
	var out := AABB()
	var first := true
	for mi in _meshes(v):
		var ab: AABB = mi.get_meta("pose_aabb") if mi.has_meta("pose_aabb") else mi.get_aabb()   # 3D-4.12: the box of the pose
		var xf: Transform3D = inv * mi.global_transform
		var b2: AABB = xf * ab
		out = b2 if first else out.merge(b2)
		first = false
	return out


# ---- hard negatives: things that look like something, but nobody is there -------------------------------------------
func add_negative(kind: String, aim_yaw: float) -> String:
	var cam: Camera3D = main.cams[0]
	var cx: Transform3D = cam.global_transform
	match kind:
		"ast":                                          # a branch right in front of the lens (moves in the wind)
			var n := Node3D.new()
			holder.add_child(n)
			n.global_transform = cx.translated_local(Vector3(randf_range(-0.8, 0.8), randf_range(-0.2, 0.6), -randf_range(0.8, 3.0)))
			n.rotate_object_local(Vector3.FORWARD, randf() * TAU)
			var tw := MeshInstance3D.new()
			var cy := CylinderMesh.new()
			cy.top_radius = 0.015
			cy.bottom_radius = 0.03
			cy.height = randf_range(1.0, 2.0)
			tw.mesh = cy
			tw.material_override = main.mat(Color(0.3, 0.22, 0.14))
			n.add_child(tw)
			for i in range(randi_range(4, 9)):
				var lf := MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = randf_range(0.06, 0.16)
				sm.height = sm.radius * 1.2
				lf.mesh = sm
				lf.material_override = main.mat(Color(0.15, randf_range(0.3, 0.5), 0.1))
				lf.position = Vector3(randf_range(-0.2, 0.2), randf_range(-cy.height / 2, cy.height / 2), randf_range(-0.1, 0.1))
				n.add_child(lf)
		"fahne":                                        # a flag or laundry on a pole
			var a := aim_yaw + deg_to_rad(randf_range(-25.0, 25.0))
			var d := randf_range(4.0, 16.0)
			var p: Vector3 = main.rig.global_position + Vector3(-sin(a) * d, 0, -cos(a) * d)
			p.y = main.ground_y(p.x, p.z)
			var pole := MeshInstance3D.new()
			var cy2 := CylinderMesh.new()
			cy2.top_radius = 0.03
			cy2.bottom_radius = 0.03
			cy2.height = randf_range(1.8, 4.0)
			pole.mesh = cy2
			pole.material_override = main.mat(Color(0.75, 0.75, 0.78))
			holder.add_child(pole)
			pole.global_position = p + Vector3(0, cy2.height / 2.0, 0)
			var fl := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(randf_range(0.6, 1.4), randf_range(0.4, 0.9), 0.02)
			fl.mesh = bm
			fl.material_override = _cloth_mat(rand_cloth_colour(), randi() % 4 if randf() < 0.4 else -1)
			holder.add_child(fl)
			fl.global_position = p + Vector3(0, cy2.height - bm.size.y / 2.0, 0)
			fl.rotation = Vector3(randf_range(-0.2, 0.2), randf() * TAU, randf_range(-0.3, 0.3))
			fl.translate_object_local(Vector3(bm.size.x / 2.0, 0, 0))
		"licht":                                        # headlights far away, a lantern, a torch spot on the ground
			var a2 := aim_yaw + deg_to_rad(randf_range(-25.0, 25.0))
			var d2 := randf_range(6.0, 30.0)
			var p2: Vector3 = main.rig.global_position + Vector3(-sin(a2) * d2, 0, -cos(a2) * d2)
			p2.y = main.ground_y(p2.x, p2.z) + randf_range(0.5, 1.2)
			var pair := randf() < 0.5
			for s in ([-0.75, 0.75] if pair else [0.0]):
				var b := MeshInstance3D.new()
				var sm2 := SphereMesh.new()
				sm2.radius = randf_range(0.06, 0.15)
				sm2.height = sm2.radius * 2.0
				b.mesh = sm2
				var m := StandardMaterial3D.new()
				m.albedo_color = kelvin(randf_range(3000.0, 6500.0))
				m.emission_enabled = true
				m.emission = m.albedo_color
				m.emission_energy_multiplier = randf_range(4.0, 16.0)
				b.material_override = m
				holder.add_child(b)
				b.global_position = p2 + Vector3(cos(a2) * s, 0, -sin(a2) * s)
			var sp := SpotLight3D.new()
			sp.light_energy = randf_range(2.0, 8.0)
			sp.spot_range = 14.0
			sp.spot_angle = randf_range(12.0, 30.0)
			holder.add_child(sp)
			sp.global_position = p2 + Vector3(0, 1.5, 0)
			sp.look_at(p2 + Vector3(randf_range(-3, 3), -1.5, randf_range(-3, 3)), Vector3.UP)
		"insekt":                                       # moths / flies in front of the lens (at night bright in the infrared)
			for i in range(randi_range(1, 4)):
				var b3 := MeshInstance3D.new()
				var sm3 := SphereMesh.new()
				sm3.radius = randf_range(0.002, 0.008)
				sm3.height = sm3.radius * 1.4
				b3.mesh = sm3
				var m3 := StandardMaterial3D.new()
				var bright: bool = main.is_dark()
				m3.albedo_color = Color(0.85, 0.85, 0.8) if bright else Color(0.1, 0.09, 0.08)
				if bright:
					m3.emission_enabled = true
					m3.emission = Color(0.9, 0.9, 0.85)
					m3.emission_energy_multiplier = randf_range(0.5, 3.0)
				b3.material_override = m3
				holder.add_child(b3)
				b3.global_position = cx * Vector3(randf_range(-0.12, 0.12), randf_range(-0.07, 0.07), -randf_range(0.2, 0.6))
		"schatten":                                     # a dark shape on the ground (shadow of something outside the picture)
			var a4 := aim_yaw + deg_to_rad(randf_range(-20.0, 20.0))
			var d4 := randf_range(3.0, 10.0)
			var p4: Vector3 = main.rig.global_position + Vector3(-sin(a4) * d4, 0, -cos(a4) * d4)
			p4.y = main.ground_y(p4.x, p4.z) + 0.01
			var sh := MeshInstance3D.new()
			var pm := BoxMesh.new()
			pm.size = Vector3(randf_range(0.4, 0.8), 0.005, randf_range(1.2, 2.2))
			sh.mesh = pm
			var m4 := StandardMaterial3D.new()
			m4.albedo_color = Color(0.0, 0.0, 0.0, randf_range(0.35, 0.7))
			m4.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m4.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			sh.material_override = m4
			sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			holder.add_child(sh)
			sh.global_position = p4
			sh.rotation.y = randf() * TAU
	return kind


# ---- camera faults after the picture ---------------------------------------------------------------------------------
func _noise_tile(alpha: int, colour: bool) -> Image:
	var im := Image.create(128, 128, false, Image.FORMAT_RGBA8)
	for y in 128:
		for x in 128:
			var g := randf()
			im.set_pixel(x, y, Color(randf(), randf(), randf(), alpha / 255.0) if colour else Color(g, g, g, alpha / 255.0))
	return im


func postfx(j: PackedByteArray, grey := false) -> Dictionary:
	"""a worse camera: blur (focus), motion blur (sideways), grain, white balance, brightness, JPEG quality.
	Returns {"jpg", "img", "fx": {...}} - fx goes into the meta file"""
	var img := Image.new()
	if img.load_jpg_from_buffer(j) != OK:
		return {"jpg": j, "img": null, "fx": {}}
	var w := img.get_width()
	var h := img.get_height()
	var fx := {"soft": 0.0, "blur_px": 0, "noise": 0, "wb": "", "bcs": [1.0, 1.0, 1.0], "jpg_q": 0.0}
	if randf() < 0.3:                                    # out of focus / dirty lens
		var f := randf_range(1.4, 3.0)
		img.resize(maxi(8, int(w / f)), maxi(8, int(h / f)), Image.INTERPOLATE_BILINEAR)
		img.resize(w, h, Image.INTERPOLATE_BILINEAR)
		fx["soft"] = snappedf(f, 0.1)
	if randf() < 0.3:                                    # motion blur: the head turns or the exposure is long
		var k := randi_range(2, 10)
		img.resize(maxi(8, w / k), h, Image.INTERPOLATE_LANCZOS)
		img.resize(w, h, Image.INTERPOLATE_BILINEAR)
		fx["blur_px"] = k
	if randf() < 0.6:
		var bcs := [snappedf(randf_range(0.75, 1.25), 0.01), snappedf(randf_range(0.8, 1.2), 0.01), snappedf(randf_range(0.6, 1.2), 0.01)]
		img.adjust_bcs(bcs[0], bcs[1], bcs[2])
		fx["bcs"] = bcs
	img.convert(Image.FORMAT_RGBA8)
	if not grey and randf() < 0.4:                       # white balance off (not on the grey infrared picture): too warm or too cold
		var warm := randf() < 0.5
		var ov := Image.create(w, h, false, Image.FORMAT_RGBA8)
		ov.fill(Color(1.0, 0.65, 0.3, randf_range(0.05, 0.16)) if warm else Color(0.45, 0.65, 1.0, randf_range(0.05, 0.16)))
		img.blend_rect(ov, Rect2i(0, 0, w, h), Vector2i.ZERO)
		fx["wb"] = "warm" if warm else "kalt"
	if randf() < 0.55:                                   # grain (stronger at night)
		if _noise.is_empty():
			_noise = [_noise_tile(14, false), _noise_tile(28, false), _noise_tile(45, false), _noise_tile(28, true)]
		var lvl := randi() % _noise.size()
		var tile: Image = _noise[lvl]
		var ox := randi() % 128
		var oy := randi() % 128
		var y := -oy
		while y < h:
			var x := -ox
			while x < w:
				img.blend_rect(tile, Rect2i(0, 0, 128, 128), Vector2i(x, y))
				x += 128
			y += 128
		fx["noise"] = lvl + 1
	img.convert(Image.FORMAT_RGB8)
	var q := randf_range(0.3, 0.9)
	fx["jpg_q"] = snappedf(q, 0.01)
	return {"jpg": img.save_jpg_to_buffer(q), "img": img, "fx": fx}


static func box_lum(img: Image, box: Array) -> float:
	"""mean brightness (0..1) inside the box [x, y, w, h] (0..1) of the picture"""
	if img == null or box.size() < 4:
		return -1.0
	var W := img.get_width()
	var H := img.get_height()
	var x0 := clampi(int(box[0] * W), 0, W - 1)
	var y0 := clampi(int(box[1] * H), 0, H - 1)
	var x1 := clampi(int((box[0] + box[2]) * W), x0 + 1, W)
	var y1 := clampi(int((box[1] + box[3]) * H), y0 + 1, H)
	var step := maxi(1, int(sqrt(float((x1 - x0) * (y1 - y0)) / 900.0)))
	var s := 0.0
	var n := 0
	var y := y0
	while y < y1:
		var x := x0
		while x < x1:
			s += img.get_pixel(x, y).get_luminance()
			n += 1
			x += step
		y += step
	return snappedf(s / maxf(1.0, n), 0.001)
