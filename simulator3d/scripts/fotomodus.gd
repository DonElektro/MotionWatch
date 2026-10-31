extends Node
## 3D-4.27 Foto-Modus (Paket «Fotorealismus F4», Daniel 31.10.2026): das echte Foto des Platzes IST die Welt.
## Grundlage ist «Foto des Platzes» (zwilling.gd: Foto / Panorama pro Platz, Bildwinkel, Richtung). Im Foto-Modus:
##  - die Szene wird ausgeblendet; das Foto liegt auf einer grossen Kugel um die MoveEye-Kamera (shaders/fotowelt.gdshader),
##    so wie die Kamera es von ihrem Platz sieht (Lochkamera fürs Handyfoto, Zylinder fürs Panorama; bis 3 Fotos, weich
##    überblendet). Dreht der Kopf aus dem Foto heraus: Hinweis oben im Bild.
##  - Kalibrierung: Horizont (Klick, zweiter Klick = schief), Kamerahöhe (= Stangenlänge), Bildwinkel. Boden = flache Ebene
##    auf Höhe des Bodens unter MoveEye; Linien 5 / 10 / 20 / 40 m und «Grösse prüfen» (1.75 m Person) zum Nachprüfen.
##  - die Figuren (Besucher) laufen davor auf dieser Ebene: Grösse nach Distanz von selbst (gleiche Geometrie),
##    weicher Schatten in das Foto gezeichnet (Richtung / Länge von der Sonne des Simulators, Fusskontakt immer).
##  - Farbanpassung: camfx.gdshader erkennt die Figuren-Pixel (Bild ≠ Foto) und gleicht sie an: Helligkeit, Weissabgleich
##    (Grauwelt des Fotos), Weichheit, Rauschen (gemessen im Foto bei der Auflösung, in der MoveEye es sieht).
##  - Verdeckung: Bereiche «vorne» (Hecke, Zelt …) mit Finger / Maus malen; jede Fläche wird in ihrer Entfernung (vom
##    untersten Punkt auf dem Boden) nochmals gezeichnet – Figuren dahinter verschwinden, davor bleiben sie sichtbar.
## Daten im Eintrag des Platzes in user://zwilling.json (fm_*), Masken als PNG in user://zwilling/. Test-Aktion
## {"action": "fotomodus", "do": info | on | set | mask_rect | mask_clear | more | measure | size | debug}.

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")

var main
var zw                                   # zwilling.gd (owns the photos of the place)
var on := false
var root: Node3D = null                  # follows the camera (only moves, never turns)
var _sphere: MeshInstance3D = null
var _wmat: ShaderMaterial = null
var _masks: Array = []                   # MeshInstance3D
var _mats: Array = []                    # every material that needs the photo uniforms (sphere, masks)
var _texs := {}                          # path -> ImageTexture
var _mask_tex: Array = [null, null, null]
var _env: Environment = null
var _env_t := 0.0
var cover := 1.0
var hint := ""
var dbg := false
var _hint_layer: CanvasLayer = null
var _hint_lbl: Label = null
var _hidden: Array = []
var _sh: Array = []
var _slow := 0.0
var sel := 0                             # the photo the window works on (0 = main photo)
var _canvas = null


# ---- the photos of the place ----------------------------------------------------------------------------------------
func photos() -> Array:
	"""the photos of this place: the main one (the entry of zwilling.gd) and up to 2 more («more»)"""
	var e: Dictionary = zw.cur()
	if not e.has("img"):
		return []
	var out := [e]
	for p in e.get("more", []):
		if typeof(p) == TYPE_DICTIONARY and p.has("img"):
			out.append(p)
	return out.slice(0, 3)


func gv(k: String, def):
	return zw.cur().get(k, def)


func set_val(k: String, v) -> void:
	var e: Dictionary = zw.cur()
	if e.is_empty():
		return
	e[k] = v
	zw.data[zw.key()] = e
	zw.save()
	if k == "fm_h" and on:
		main.set_mast(float(v))
	if k == "fm_front":
		_build_masks()
	_paint_canvas()


func set_pval(i: int, k: String, v) -> void:
	"""a value of one photo (horizon, roll, yaw, span, mask)"""
	var ps := photos()
	if i < 0 or i >= ps.size():
		return
	ps[i][k] = v
	zw.save()
	if k in ["fm_hz", "fm_roll", "yaw", "span"]:
		_build_masks()
	_paint_canvas()


func _rig_yaw() -> float:
	return main.rig.global_rotation.y if main.rig != null and main.rig.is_inside_tree() else 0.0


func pose(p: Dictionary) -> Array:
	"""[Basis photo -> world, Vector4 projection (see foto.gdshaderinc), cylinder?]"""
	var span := deg_to_rad(clampf(float(p.get("span", 66.0)), 10.0, 360.0))
	var asp := maxf(0.3, float(p.get("aspect", 1.5)))
	var cyl := span > deg_to_rad(150.0)
	var pv: Vector4
	var tv: float
	if cyl:
		tv = span / asp
		pv = Vector4(span, tv, 2.0 if span >= deg_to_rad(359.0) else 1.0, 0.06)
	else:
		var th := tan(span * 0.5)
		tv = th / asp
		pv = Vector4(th, tv, 0.0, 0.08)
	var hz := clampf(float(p.get("fm_hz", 0.5)), 0.0, 1.0)
	var pitch := atan((hz - 0.5) * 2.0 * tv) if not cyl else atan((hz - 0.5) * tv)
	var b := Basis(Vector3.UP, _rig_yaw() - deg_to_rad(float(p.get("yaw", 0.0)))) * Basis(Vector3.RIGHT, pitch) \
			* Basis(Vector3.BACK, deg_to_rad(float(p.get("fm_roll", 0.0))))
	return [b, pv, cyl]


static func uv_of(b: Basis, pv: Vector4, d: Vector3) -> Vector2:
	"""world direction -> uv in the photo (like foto_uv in the shader); (-1, -1) = not in it"""
	var q: Vector3 = b.transposed() * d
	if pv.z < 0.5:
		if q.z > -0.0001:
			return Vector2(-1, -1)
		return Vector2(0.5 + q.x / -q.z / (2.0 * pv.x), 0.5 - q.y / -q.z / (2.0 * pv.y))
	var u := 0.5 + atan2(q.x, -q.z) / pv.x
	if pv.z > 1.5:
		u = fposmod(u, 1.0)
	return Vector2(u, 0.5 - q.y / maxf(Vector2(q.x, q.z).length(), 0.0001) / pv.y)


static func dir_of(b: Basis, pv: Vector4, uv: Vector2) -> Vector3:
	"""uv in the photo -> world direction"""
	var q: Vector3
	if pv.z < 0.5:
		q = Vector3((uv.x - 0.5) * 2.0 * pv.x, (0.5 - uv.y) * 2.0 * pv.y, -1.0)
	else:
		var az := (uv.x - 0.5) * pv.x
		q = Vector3(sin(az), (0.5 - uv.y) * pv.y, -cos(az))
	return (b * q).normalized()


func eye() -> Vector3:
	return main.cams[0].global_position if main.cams.size() > 0 and main.cams[0].is_inside_tree() else Vector3(0, main.mast_h, 0)


func ground() -> float:
	if main.rig != null and main.rig.is_inside_tree():
		return main.ground_y(main.rig.global_position.x, main.rig.global_position.z)
	return 0.0


func ground_hit(d: Vector3) -> float:
	"""distance along d from the camera to the ground of the photo (-1 = above the horizon)"""
	if d.y > -0.002:
		return -1.0
	return (eye().y - ground()) / -d.y


func _tex(path: String) -> ImageTexture:
	if _texs.has(path):
		return _texs[path]
	var img := Image.load_from_file(ProjectSettings.globalize_path(path))
	if img == null or img.is_empty():
		return null
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_texs[path] = t
	return t


# ---- on / off --------------------------------------------------------------------------------------------------------
func set_on(v: bool) -> void:
	if v and photos().is_empty():
		on = false
		hint = T.t("Kein Foto für diesen Platz – zuerst «Foto / Panorama wählen …» (Fenster «Gegenstände» · Foto des Platzes)")
		_say(hint)
		return
	on = v
	zw.fm_on = v
	zw.save()
	_apply()


func on_scene() -> void:
	"""zwilling.on_scene (after every new scene): build it again for the photos of this place"""
	_texs.clear()
	if on and photos().is_empty():
		on = false
	_apply()


func _apply() -> void:
	_clear()
	if not on:
		_show_scene(true)
		hint = ""
		_paint_canvas()
		return
	_show_scene(false)
	main.set_mast(float(gv("fm_h", main.mast_h)))
	var e: Dictionary = zw.cur()
	if not e.has("fm_h"):
		e["fm_h"] = main.mast_h
	if not e.has("fm_st"):
		measure()
	root = Node3D.new()
	root.name = "Fotomodus"
	main.add_child(root)
	root.global_position = eye()
	_wmat = ShaderMaterial.new()
	_wmat.shader = load("res://shaders/fotowelt.gdshader")
	_wmat.render_priority = -10
	_mats.append(_wmat)
	var sm := SphereMesh.new()
	sm.radius = 300.0
	sm.height = 600.0
	sm.radial_segments = 48
	sm.rings = 24
	_sphere = MeshInstance3D.new()
	_sphere.mesh = sm
	_sphere.material_override = _wmat
	_sphere.layers = 1
	_sphere.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_sphere.extra_cull_margin = 400.0
	root.add_child(_sphere)
	_build_masks()
	_update(true)
	_paint_canvas()


func _clear() -> void:
	if root != null and is_instance_valid(root):
		root.queue_free()
	root = null
	_sphere = null
	_masks.clear()
	_mats.clear()
	for i in range(mini(2, main.camfx_mats.size())):
		main.camfx_mats[i].set_shader_parameter("foto_on", 0.0)


func _show_scene(v: bool) -> void:
	"""the 3D scene is hidden in the Foto-Modus (the photo is the world); the thermal ground stays"""
	if not v:
		if main.scene_parent != null and main.scene_parent.visible:
			main.scene_parent.visible = false
			_hidden.append(main.scene_parent)
		for n in main.flat_nodes:
			if is_instance_valid(n) and n is VisualInstance3D and (n.layers & 1) != 0 and n.visible:
				n.visible = false
				_hidden.append(n)
		return
	for n in _hidden:
		if is_instance_valid(n):
			n.visible = true
	_hidden.clear()
	for n in main.flat_nodes:                      # like main._build_scene
		if is_instance_valid(n):
			n.visible = not main.terrain


# ---- the painted parts in front ----------------------------------------------------------------------------------------
func mask_path(i: int) -> String:
	var k: String = zw.key().validate_filename().replace(":", "_").replace(",", "_")
	return zw.DIR + "/" + k + ("_maske.png" if i == 0 else "_%d_maske.png" % (i + 1))


func mask_img(i: int, make := false) -> Image:
	var ps := photos()
	if i >= ps.size():
		return null
	var p: Dictionary = ps[i]
	var fn := str(p.get("fm_mask", ""))
	var img: Image = null
	if fn != "" and FileAccess.file_exists(fn):
		img = Image.load_from_file(ProjectSettings.globalize_path(fn))
	if (img == null or img.is_empty()) and make:
		var asp := maxf(0.3, float(p.get("aspect", 1.5)))
		img = Image.create(256, clampi(int(256.0 / asp), 16, 512), false, Image.FORMAT_L8)
	elif img != null and img.get_format() != Image.FORMAT_L8:
		img.convert(Image.FORMAT_L8)
	return img


func save_mask(i: int, img: Image) -> void:
	var ps := photos()
	if i >= ps.size():
		return
	DirAccess.make_dir_recursive_absolute(zw.DIR)
	var fn := mask_path(i)
	img.save_png(fn)
	ps[i]["fm_mask"] = fn
	zw.save()
	_build_masks()


func clear_mask(i: int) -> void:
	var ps := photos()
	if i >= ps.size():
		return
	ps[i].erase("fm_mask")
	zw.save()
	_build_masks()
	_paint_canvas()


static func components(img: Image) -> Array:
	"""connected painted areas: [{x0, y0, x1, y1, bx (x of the lowest point), by}] in mask pixels"""
	var w := img.get_width()
	var h := img.get_height()
	var data := img.get_data()
	var seen := PackedByteArray()
	seen.resize(w * h)
	var out := []
	for start in range(w * h):
		if seen[start] != 0 or data[start] < 128:
			continue
		var c := {"x0": w, "y0": h, "x1": 0, "y1": 0, "bx": 0, "by": -1, "n": 0}
		var stack := PackedInt32Array([start])
		seen[start] = 1
		var sx := 0
		var sn := 0
		while not stack.is_empty():
			var q: int = stack[stack.size() - 1]
			stack.resize(stack.size() - 1)
			var x := q % w
			var y := q / w
			c["n"] += 1
			c["x0"] = mini(c["x0"], x)
			c["x1"] = maxi(c["x1"], x)
			c["y0"] = mini(c["y0"], y)
			if y > int(c["y1"]):
				c["y1"] = y
				sx = 0
				sn = 0
			if y == int(c["y1"]):
				sx += x
				sn += 1
			for nb in [q - 1, q + 1, q - w, q + w]:
				if nb < 0 or nb >= w * h or seen[nb] != 0 or data[nb] < 128:
					continue
				if (nb == q - 1 and x == 0) or (nb == q + 1 and x == w - 1):
					continue
				seen[nb] = 1
				stack.append(nb)
		if int(c["n"]) >= 6:
			c["bx"] = float(sx) / maxf(1.0, sn)
			c["by"] = c["y1"]
			out.append(c)
	return out


func mask_dist(i: int, c: Dictionary, img: Image) -> float:
	"""how far a painted area stands: where its lowest point meets the ground of the photo"""
	if bool(gv("fm_front", false)):
		return 0.6
	var ps := photos()
	var po: Array = pose(ps[i])
	var uv := Vector2((float(c["bx"]) + 0.5) / img.get_width(), (float(c["by"]) + 1.0) / img.get_height())
	var t := ground_hit(dir_of(po[0], po[1], uv))
	return 200.0 if t < 0.0 else clampf(t * 0.97, 0.6, 250.0)


func _build_masks() -> void:
	for m in _masks:
		if is_instance_valid(m):
			_mats.erase(m.material_override)
			m.queue_free()
	_masks.clear()
	if not on or root == null:
		return
	var ps := photos()
	var grid := 4 if Quality.lite() else 6
	for i in range(ps.size()):
		_mask_tex[i] = null
		var img := mask_img(i)
		if img == null or img.is_empty():
			continue
		var t := ImageTexture.create_from_image(img)
		_mask_tex[i] = t
		var po: Array = pose(ps[i])
		var w := float(img.get_width())
		var h := float(img.get_height())
		for c in components(img):
			var d := mask_dist(i, c, img)
			var u0 := (float(c["x0"]) - 1.0) / w
			var u1 := (float(c["x1"]) + 2.0) / w
			var v0 := (float(c["y0"]) - 1.0) / h
			var v1 := (float(c["y1"]) + 2.0) / h
			var st := SurfaceTool.new()
			st.begin(Mesh.PRIMITIVE_TRIANGLES)
			for gy in range(grid):
				for gx in range(grid):
					for q in [[gx, gy], [gx + 1, gy], [gx + 1, gy + 1], [gx, gy], [gx + 1, gy + 1], [gx, gy + 1]]:
						var uv := Vector2(lerpf(u0, u1, float(q[0]) / grid), lerpf(v0, v1, float(q[1]) / grid))
						st.add_vertex(dir_of(po[0], po[1], uv) * d)
			var mi := MeshInstance3D.new()
			mi.mesh = st.commit()
			var mm := ShaderMaterial.new()
			mm.shader = load("res://shaders/fotomaske.gdshader")
			mm.set_shader_parameter("mask_t", t)
			mm.set_shader_parameter("mask_i", i)
			mi.material_override = mm
			mi.layers = 1
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.set_meta("dist", d)
			root.add_child(mi)
			_masks.append(mi)
			_mats.append(mm)
	_update(true)


# ---- colours of the photo ----------------------------------------------------------------------------------------------
func measure() -> Dictionary:
	"""brightness, colour cast and noise of the main photo - at the size MoveEye sees it (about 960 px per 66°)"""
	var ps := photos()
	if ps.is_empty():
		return {}
	var p: Dictionary = ps[0]
	var img := Image.load_from_file(ProjectSettings.globalize_path(str(p["img"])))
	if img == null or img.is_empty():
		return {}
	var span := clampf(float(p.get("span", 66.0)), 10.0, 360.0)
	var weff := clampi(int(960.0 * span / 66.0), 160, img.get_width())
	var small: Image = img.duplicate()
	small.resize(weff, maxi(16, int(weff * img.get_height() / float(img.get_width()))), Image.INTERPOLATE_BILINEAR)
	var tiny: Image = small.duplicate()
	tiny.resize(64, maxi(8, int(64.0 * small.get_height() / small.get_width())), Image.INTERPOLATE_BILINEAR)
	var s := Vector3.ZERO
	for y in range(tiny.get_height()):
		for x in range(tiny.get_width()):
			var c := tiny.get_pixel(x, y)
			s += Vector3(c.r, c.g, c.b)
	s /= float(tiny.get_width() * tiny.get_height())
	# noise: median of |Laplacian| in the lower middle (the ground, where the figures walk), robust against edges
	var cw := mini(200, small.get_width() - 2)
	var chh := mini(120, small.get_height() - 2)
	var x0 := (small.get_width() - cw) / 2
	var y0 := clampi(int(small.get_height() * 0.62) - chh / 2, 1, small.get_height() - chh - 1)
	var vals := PackedFloat32Array()
	for y in range(y0, y0 + chh, 2):
		for x in range(x0, x0 + cw, 2):
			var l := small.get_pixel(x, y).get_luminance() * 4.0 - small.get_pixel(x - 1, y).get_luminance() - small.get_pixel(x + 1, y).get_luminance() \
					- small.get_pixel(x, y - 1).get_luminance() - small.get_pixel(x, y + 1).get_luminance()
			vals.append(absf(l))
	vals.sort()
	var mad: float = vals[vals.size() / 2] if vals.size() > 0 else 0.0
	var sigma := clampf(mad * 1.4826 / sqrt(20.0), 0.0, 0.08)
	var lum := s.x * 0.299 + s.y * 0.587 + s.z * 0.114
	var st := {"mean": [snappedf(s.x, 0.001), snappedf(s.y, 0.001), snappedf(s.z, 0.001)], "lum": snappedf(lum, 0.001), "noise": snappedf(sigma, 0.0001), "w": weff}
	var e: Dictionary = zw.cur()
	e["fm_st"] = st
	zw.save()
	return st


func gain() -> Vector3:
	"""what camfx multiplies the figures with: colour cast of the photo (grey world, partly) × brightness"""
	var st: Dictionary = gv("fm_st", {})
	var m: Array = st.get("mean", [0.45, 0.45, 0.45])
	var lum := maxf(0.02, float(st.get("lum", 0.45)))
	var wb := clampf(float(gv("fm_wb", 0.5)), 0.0, 1.0)
	var cast := Vector3(float(m[0]), float(m[1]), float(m[2])) / lum
	cast = Vector3.ONE.lerp(cast, wb)
	var br := pow(clampf(lum / 0.42, 0.45, 1.8), 0.6) * float(gv("fm_bright", 1.0))
	return cast * br


# ---- every frame / every picture ---------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if not on or root == null:
		if _hint_lbl != null:
			_hint_lbl.visible = false
		return
	_update(false)
	_slow -= dt
	if _slow <= 0.0:
		_slow = 0.5
		_coverage()


func _update(full: bool) -> void:
	if root == null:
		return
	var ey := eye()
	root.global_position = ey
	var ps := photos()
	var k: float = clampf(main.light_level() * 1.05, 0.02, 1.0)
	var st: Dictionary = gv("fm_st", {})
	var mean: Array = st.get("mean", [0.4, 0.42, 0.4])
	_shadows()
	for m in _mats:
		_set_common(m, ps, ey, k, mean, full)
		if m != _wmat:
			m.set_shader_parameter("foto_shk", 0.0)


func _set_common(m: ShaderMaterial, ps: Array, ey: Vector3, k: float, mean: Array, full: bool) -> void:
	m.set_shader_parameter("foto_eye", ey)
	m.set_shader_parameter("foto_gy", ground())
	m.set_shader_parameter("foto_k", k)
	m.set_shader_parameter("foto_sh", _sh)
	m.set_shader_parameter("foto_shn", _sh_n)
	m.set_shader_parameter("foto_sun", _sun)
	m.set_shader_parameter("foto_shk", float(gv("fm_shk", 0.5)))
	if not full and m.has_meta("set"):
		return
	m.set_meta("set", true)
	m.set_shader_parameter("foto_n", ps.size())
	m.set_shader_parameter("foto_fill", Vector3(float(mean[0]), float(mean[1]), float(mean[2])) * 0.55)
	for i in range(3):
		if i < ps.size():
			var po: Array = pose(ps[i])
			m.set_shader_parameter("foto_t%d" % i, _tex(str(ps[i]["img"])))
			m.set_shader_parameter("foto_b%d" % i, (po[0] as Basis).transposed())
			m.set_shader_parameter("foto_p%d" % i, po[1])


var _sh_n := 0
var _sun := Vector3(0, 0, 0)


func _shadows() -> void:
	"""up to 16 figures with their soft shadow; the sun of the simulator gives direction and length"""
	var arr := []
	var ey := eye()
	var list := []
	for v in main.visitors.get_children():
		if not (v is Node3D) or not v.visible:
			continue
		var p: Vector3 = v.global_position
		var dd := Vector2(p.x - ey.x, p.z - ey.z).length()
		if dd > 120.0:
			continue
		list.append([dd, v])
	list.sort_custom(func(a, b): return a[0] < b[0])
	var nmax := 8 if Quality.lite() else 16
	for it in list.slice(0, nmax):
		var v: Node3D = it[1]
		var sz: Vector2 = v.get_meta("fm_sz") if v.has_meta("fm_sz") else _size_of(v)
		arr.append(Vector4(v.global_position.x, v.global_position.z, sz.x, sz.y))
	_sh_n = arr.size()
	while arr.size() < 16:
		arr.append(Vector4.ZERO)
	_sh = arr
	var s: DirectionalLight3D = main.sun
	if s == null or not s.visible or main.sun_el() < 2.0:
		_sun = Vector3(0, 1, 0)
		return
	var ld := -s.global_transform.basis.z                     # where the light goes
	var hl := Vector2(ld.x, ld.z).length()
	var k := clampf(s.light_energy / 1.2, 0.0, 1.0)             # clouds: only the soft contact shadow
	_sun = Vector3(ld.x, ld.z, clampf(hl / maxf(absf(ld.y), 0.05), 0.0, 4.0) * k)


func _size_of(v: Node3D) -> Vector2:
	"""radius and height of a figure (from its meshes, once)"""
	var box := AABB()
	var first := true
	var inv := v.global_transform.affine_inverse()
	for n in v.find_children("*", "VisualInstance3D", true, false):
		var vi: VisualInstance3D = n
		if (vi.layers & 1) == 0 or not vi.is_visible_in_tree():
			continue
		var b: AABB = (inv * vi.global_transform) * vi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	var sz := Vector2(0.3, 1.7) if first else Vector2(clampf(maxf(box.size.x, box.size.z) * 0.5, 0.12, 3.5), clampf(box.end.y, 0.2, 4.0))
	v.set_meta("fm_sz", sz)
	return sz


func before_capture(i: int) -> void:
	"""main._capture (after the other camera effects): the camera sees the photo world; camfx fits the figures to it"""
	if i >= 2 or i >= main.camfx_mats.size():
		return
	var m: ShaderMaterial = main.camfx_mats[i]
	if not on or root == null:
		m.set_shader_parameter("foto_on", 0.0)
		return
	_update(false)
	var cam: Camera3D = main.cams[i]
	main.cam_attr[i].exposure_multiplier = 1.0          # the photo is already exposed (no auto exposure on it)
	var mine := false
	if cam.environment == null:                          # by day: no film curve, no fog / glow - the photo stays as it is
		if _env == null or main.now() - _env_t > 3.0:
			_env = main.env.duplicate()
			_env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
			_env.glow_enabled = false
			_env.fog_enabled = false
			_env.volumetric_fog_enabled = false
			_env.adjustment_enabled = false
			_env_t = main.now()
		cam.environment = _env
		mine = true
	var ps := photos()
	var st: Dictionary = gv("fm_st", {})
	_set_common(m, ps, root.global_position, clampf(main.light_level() * 1.05, 0.02, 1.0), st.get("mean", [0.4, 0.42, 0.4]), true)
	m.set_shader_parameter("foto_on", 1.0 if mine else 0.0)    # at night (other environment) only the darker photo
	m.set_shader_parameter("foto_cam", cam.global_transform.basis.orthonormalized())
	var th := tan(deg_to_rad(cam.fov) * 0.5)
	m.set_shader_parameter("foto_tan", Vector2(th, th * float(main.CAM_H[i]) / float(main.CAM_W[i])))
	m.set_shader_parameter("foto_gain", gain())
	var nz := float(st.get("noise", 0.006)) * float(gv("fm_noise", 1.0))
	m.set_shader_parameter("foto_noise", nz)
	m.set_shader_parameter("foto_soft", 0.0 if Quality.lite() else float(gv("fm_soft", 0.6)))
	m.set_shader_parameter("foto_thr", clampf(0.03 + nz * 2.0, 0.03, 0.12))
	m.set_shader_parameter("foto_dbg", 1.0 if dbg else 0.0)


func _coverage() -> void:
	"""how much of the picture of the MoveEye camera the photos cover (3 × 5 points)"""
	var cam: Camera3D = main.cams[0]
	var ps := photos()
	var poses := []
	for p in ps:
		poses.append(pose(p))
	var th := tan(deg_to_rad(cam.fov) * 0.5)
	var tv := th * float(main.CAM_H[0]) / float(main.CAM_W[0])
	var b := cam.global_transform.basis.orthonormalized()
	var n := 0
	var hit := 0
	for gy in [-0.9, 0.0, 0.9]:
		for gx in [-0.95, -0.5, 0.0, 0.5, 0.95]:
			var d := (b * Vector3(gx * th, gy * tv, -1.0)).normalized()
			n += 1
			for po in poses:
				var uv := uv_of(po[0], po[1], d)
				if uv.x >= 0.0 and uv.y >= 0.0 and uv.x <= 1.0 and uv.y <= 1.0:
					hit += 1
					break
	cover = float(hit) / n
	if cover >= 0.99:
		hint = ""
	elif ps.size() > 1 or bool(poses[0][2]):
		hint = T.t("Foto-Modus: Kopf schaut neben die Fotos (%d %% abgedeckt)", [int(cover * 100)])
	else:
		hint = T.t("Foto-Modus: Kopf schaut neben das Foto (%d %% abgedeckt) – zum Schwenken ein Panorama oder weitere Fotos laden", [int(cover * 100)])
	_show_hint()


func _show_hint() -> void:
	if _hint_lbl == null:
		_hint_layer = CanvasLayer.new()
		_hint_layer.layer = 4
		add_child(_hint_layer)
		_hint_lbl = Label.new()
		_hint_lbl.add_theme_color_override("font_color", Color(1, 0.92, 0.6))
		_hint_lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		_hint_lbl.add_theme_constant_override("outline_size", 5)
		_hint_lbl.add_theme_font_size_override("font_size", 15)
		_hint_lbl.position = Vector2(20, 54)
		_hint_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_hint_layer.add_child(_hint_lbl)
	_hint_lbl.text = hint
	_hint_lbl.visible = on and hint != ""


# ---- settings (Szene · Foto des Platzes) -------------------------------------------------------------------------------
func add_controls() -> void:
	var m = main
	var sub := {"sub": "Foto des Platzes"}
	m.add_control("toggle", "fm_on", "Foto-Modus: das Foto ist die Welt – die MoveEye-Kamera sieht das echte Foto, die Figuren laufen davor",
			func(): return on, func(v): set_on(bool(v)), "Szene", sub)
	m.add_control("slider", "fm_h", "Foto-Modus: Kamerahöhe beim Foto (= Stangenlänge)", func(): return float(gv("fm_h", main.mast_h)),
			func(v): set_val("fm_h", float(v)), "Szene", {"sub": "Foto des Platzes", "min": main.MAST_MIN, "max": main.MAST_MAX, "step": 0.05, "unit": "m"})
	m.add_control("slider", "fm_hz", "Foto-Modus: Horizont im Foto (0 = oben, 100 = unten; im Fenster per Klick)",
			func(): return float(photos()[0].get("fm_hz", 0.5)) * 100.0 if not photos().is_empty() else 50.0,
			func(v): set_pval(0, "fm_hz", float(v) / 100.0), "Szene", {"sub": "Foto des Platzes", "min": 0, "max": 100, "step": 0.5, "unit": "%"})
	m.add_control("slider", "fm_roll", "Foto-Modus: Horizont schief (rechts tiefer = plus)",
			func(): return float(photos()[0].get("fm_roll", 0.0)) if not photos().is_empty() else 0.0,
			func(v): set_pval(0, "fm_roll", float(v)), "Szene", {"sub": "Foto des Platzes", "min": -15, "max": 15, "step": 0.5, "unit": "°", "expert": true})
	m.add_control("slider", "fm_shk", "Foto-Modus: Schatten der Figuren", func(): return float(gv("fm_shk", 0.5)) * 100.0,
			func(v): set_val("fm_shk", float(v) / 100.0), "Szene", {"sub": "Foto des Platzes", "min": 0, "max": 100, "step": 5, "unit": "%"})
	m.add_control("slider", "fm_bright", "Foto-Modus: Figuren heller / dunkler (zur Messung am Foto)", func(): return float(gv("fm_bright", 1.0)) * 100.0,
			func(v): set_val("fm_bright", float(v) / 100.0), "Szene", {"sub": "Foto des Platzes", "min": 40, "max": 160, "step": 5, "unit": "%", "expert": true})
	m.add_control("slider", "fm_wb", "Foto-Modus: Farbstich des Fotos auf die Figuren", func(): return float(gv("fm_wb", 0.5)) * 100.0,
			func(v): set_val("fm_wb", float(v) / 100.0), "Szene", {"sub": "Foto des Platzes", "min": 0, "max": 100, "step": 5, "unit": "%", "expert": true})
	m.add_control("slider", "fm_noise", "Foto-Modus: Rauschen der Figuren (100 = wie gemessen)", func(): return float(gv("fm_noise", 1.0)) * 100.0,
			func(v): set_val("fm_noise", float(v) / 100.0), "Szene", {"sub": "Foto des Platzes", "min": 0, "max": 300, "step": 10, "unit": "%", "expert": true})
	m.add_control("toggle", "fm_front", "Foto-Modus: gemalte Bereiche immer ganz vorne (sonst Abstand vom untersten Punkt am Boden)",
			func(): return bool(gv("fm_front", false)), func(v): set_val("fm_front", bool(v)), "Szene", {"sub": "Foto des Platzes", "expert": true})
	m.add_control("button", "fm_measure", "Foto-Modus: Helligkeit, Farbe und Rauschen neu vom Foto messen", null,
			func(): measure(); _paint_canvas(), "Szene", {"sub": "Foto des Platzes", "expert": true})
	m.add_control("toggle", "fm_dbg", "Foto-Modus: zeigen, was als Figur angeglichen wird (rot)", func(): return dbg, func(v): dbg = bool(v),
			"Szene", {"sub": "Foto des Platzes", "expert": true})


# ---- more photos -------------------------------------------------------------------------------------------------------
func import_more(path: String) -> bool:
	"""a second / third photo of the same place (turn the phone a bit between them); placed next to the last one"""
	var e: Dictionary = zw.cur()
	if not e.has("img"):
		return zw.import_image(path)
	var more: Array = e.get("more", [])
	if more.size() >= 2:
		_say(T.t("Höchstens 3 Fotos pro Platz – zuerst eines entfernen"))
		return false
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		_say(T.t("Bild nicht lesbar: %s", [path.get_file()]))
		return false
	if img.get_width() > 4096:
		img.resize(4096, int(img.get_height() * 4096.0 / img.get_width()), Image.INTERPOLATE_LANCZOS)
	DirAccess.make_dir_recursive_absolute(zw.DIR)
	var fn: String = zw.DIR + "/" + zw.key().validate_filename().replace(":", "_").replace(",", "_") + "_%d.jpg" % (more.size() + 2)
	if img.save_jpg(fn, 0.88) != OK:
		return false
	var last: Dictionary = more[-1] if not more.is_empty() else e
	var span := float(last.get("span", 66.0))
	more.append({"img": fn, "src": path.get_file(), "aspect": float(img.get_width()) / img.get_height(), "span": span,
			"yaw": fposmod(float(last.get("yaw", 0.0)) + span * 0.85 + 180.0, 360.0) - 180.0, "fm_hz": float(last.get("fm_hz", 0.5))})
	e["more"] = more
	zw.data[zw.key()] = e
	zw.save()
	_texs.clear()
	_apply()
	_say(T.t("Foto %d dazu – rechts neben dem letzten (Richtung im Fenster anpassen)", [more.size() + 1]))
	return true


func remove_more() -> void:
	var e: Dictionary = zw.cur()
	var more: Array = e.get("more", [])
	if not more.is_empty():
		more.pop_back()
		e["more"] = more
		zw.save()
		sel = 0
		_apply()


# ---- the window part (Gegenstände · Foto des Platzes) -------------------------------------------------------------------
var _fd2: FileDialog = null
var _box: VBoxContainer = null


func paint_box(box: VBoxContainer) -> void:
	"""zwilling._paint: the Foto-Modus part under the photo"""
	_box = box
	var ps := photos()
	if ps.is_empty():
		return
	sel = clampi(sel, 0, ps.size() - 1)
	var hd := UI.small(T.t("Foto-Modus – das Foto ist die Welt der MoveEye-Kamera"), UI.TXT)
	hd.add_theme_font_size_override("font_size", 12)
	box.add_child(hd)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	box.add_child(h)
	var b := Button.new()
	b.text = T.t("Foto-Modus aus") if on else T.t("Foto-Modus an")
	if not on:
		UI.primary(b)
	b.pressed.connect(func(): set_on(not on); zw._paint())
	h.add_child(b)
	if ps.size() > 1:
		for i in range(ps.size()):
			var pb := Button.new()
			pb.text = T.t("Foto %d", [i + 1])
			pb.toggle_mode = true
			pb.button_pressed = i == sel
			pb.pressed.connect(func(): sel = i; zw._paint())
			h.add_child(pb)
	if ps.size() < 3:
		var mb := Button.new()
		mb.text = T.t("Weiteres Foto …")
		mb.tooltip_text = T.t("Für Kopf-Schwenken: ein zweites / drittes Foto daneben (weich überblendet)")
		mb.pressed.connect(func(): _more_dialog())
		h.add_child(mb)
	if ps.size() > 1:
		var rb := Button.new()
		rb.text = T.t("Letztes Foto weg")
		rb.pressed.connect(func(): remove_more(); zw._paint())
		h.add_child(rb)
	_canvas = FotoCanvas.new()
	_canvas.fm = self
	_canvas.idx = sel
	box.add_child(_canvas)
	_canvas.setup()
	var tools := HBoxContainer.new()
	tools.add_theme_constant_override("separation", 6)
	box.add_child(tools)
	for md in [["hz", T.t("Horizont")], ["paint", T.t("Vorne malen")], ["erase", T.t("Radieren")], ["size", T.t("Grösse prüfen")]]:
		var tb := Button.new()
		tb.text = md[1]
		tb.toggle_mode = true
		tb.button_pressed = _canvas.mode == md[0]
		tb.pressed.connect(func():
			_canvas.mode = md[0]
			for c in tools.get_children():
				if c is Button and c.toggle_mode:
					c.button_pressed = c == tb)
		tools.add_child(tb)
	var cb := Button.new()
	cb.text = T.t("Maske löschen")
	cb.pressed.connect(func(): clear_mask(sel))
	tools.add_child(cb)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	box.add_child(row)
	for adj in [[T.t("Richtung"), "yaw", 2.0, "°"], [T.t("Bildwinkel"), "span", 1.0, "°"]]:
		var l := UI.small("%s %.0f%s" % [adj[0], float(ps[sel].get(adj[1], 0.0 if adj[1] == "yaw" else 66.0)), adj[3]], UI.MUT)
		row.add_child(l)
		for sg in [-1.0, 1.0]:
			var ab := Button.new()
			ab.text = "−" if sg < 0 else "+"
			ab.pressed.connect(func():
				var v: float = float(ps[sel].get(adj[1], 0.0 if adj[1] == "yaw" else 66.0)) + sg * float(adj[2])
				if adj[1] == "span":
					v = clampf(v, 20.0, 360.0)
				set_pval(sel, adj[1], v)
				if sel == 0:
					zw._rebuild_back()
				_texs.clear()
				_apply()
				zw._paint())
			row.add_child(ab)
	var st: Dictionary = gv("fm_st", {})
	var info := UI.small(T.t("Kamerahöhe %.2f m · Horizont %d %% · gemessen: Helligkeit %d %%, Rauschen %.1f %% · Masken: %d · Bild abgedeckt: %d %%",
			[float(gv("fm_h", main.mast_h)), int(float(ps[sel].get("fm_hz", 0.5)) * 100.0), int(float(st.get("lum", 0.0)) * 100.0),
			float(st.get("noise", 0.0)) * 100.0, _masks.size(), int(cover * 100.0)]), UI.MUT)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.custom_minimum_size = Vector2(520, 0)
	box.add_child(info)
	var help := UI.small(T.t("Horizont: auf den Horizont klicken (zweiter Klick weiter rechts = schief). Prüfen: die Linien 5 / 10 / 20 / 40 m und «Grösse prüfen» (1.75 m Person) – passt es nicht, Kamerahöhe oder Bildwinkel ändern. «Vorne malen»: Hecke, Zelt … mit Finger / Maus anmalen, Figuren dahinter werden verdeckt."), UI.MUT)
	help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.custom_minimum_size = Vector2(520, 0)
	box.add_child(help)
	if _fd2 == null or not is_instance_valid(_fd2):
		_fd2 = FileDialog.new()
		_fd2.file_mode = FileDialog.FILE_MODE_OPEN_FILE
		_fd2.access = FileDialog.ACCESS_FILESYSTEM
		_fd2.filters = PackedStringArray(["*.jpg, *.jpeg, *.png, *.webp ; Foto"])
		_fd2.title = T.t("Weiteres Foto vom gleichen Platz")
		_fd2.size = Vector2i(760, 480)
		_fd2.file_selected.connect(func(p): import_more(p); zw._paint())
		add_child(_fd2)


func _more_dialog() -> void:
	if _fd2 != null:
		_fd2.popup_centered()


func _paint_canvas() -> void:
	if _canvas != null and is_instance_valid(_canvas):
		_canvas.queue_redraw()


func _say(s: String) -> void:
	zw._say(s)


# ---- the drawing area: photo, horizon, distance lines, masks, size check ------------------------------------------------
class FotoCanvas extends Control:
	var fm
	var idx := 0
	var mode := "hz"
	var tex: Texture2D = null
	var mimg: Image = null
	var mdisp: Image = null
	var mtex: ImageTexture = null
	var brush := 7
	var clicks: Array = []
	var checks: Array = []          # uv of «Grösse prüfen» points
	var _drag := false
	var _dirty := false

	func setup() -> void:
		var ps: Array = fm.photos()
		if idx >= ps.size():
			return
		var p: Dictionary = ps[idx]
		tex = fm._tex(str(p["img"]))
		var asp := maxf(0.3, float(p.get("aspect", 1.5)))
		var w := 520.0
		custom_minimum_size = Vector2(w, clampf(w / asp, 60.0, 420.0))
		mouse_filter = Control.MOUSE_FILTER_STOP
		mimg = fm.mask_img(idx, true)
		_refresh_mask()

	func _refresh_mask() -> void:
		if mimg == null:
			return
		mdisp = Image.create(mimg.get_width(), mimg.get_height(), false, Image.FORMAT_RGBA8)
		var d := mimg.get_data()
		var out := PackedByteArray()
		out.resize(d.size() * 4)
		for i in range(d.size()):
			out[i * 4] = 255
			out[i * 4 + 1] = 60
			out[i * 4 + 2] = 40
			out[i * 4 + 3] = int(d[i] * 0.45)
		mdisp.set_data(mimg.get_width(), mimg.get_height(), false, Image.FORMAT_RGBA8, out)
		if mtex == null:
			mtex = ImageTexture.create_from_image(mdisp)
		else:
			mtex.update(mdisp)
		queue_redraw()

	func _rect() -> Rect2:
		var s := custom_minimum_size
		return Rect2(Vector2.ZERO, s)

	func _to_px(uv: Vector2) -> Vector2:
		return uv * _rect().size

	func _project(po: Array, w: Vector3) -> Vector2:
		return fm.uv_of(po[0], po[1], w.normalized())

	func _draw() -> void:
		var r := _rect()
		if tex != null:
			draw_texture_rect(tex, r, false)
		if mtex != null:
			draw_texture_rect(mtex, r, false)
		var ps: Array = fm.photos()
		if idx >= ps.size():
			return
		var po: Array = fm.pose(ps[idx])
		var ey: Vector3 = fm.eye()
		var hgt: float = ey.y - fm.ground()
		var fwd: Vector3 = (po[0] as Basis) * Vector3(0, 0, -1)
		var yaw0 := atan2(fwd.x, -fwd.z)
		var spanr := deg_to_rad(clampf(float(ps[idx].get("span", 66.0)), 10.0, 360.0))
		var font := get_theme_default_font()
		# the horizon (projected far points at height of the eye) and the ground at 5 / 10 / 20 / 40 m
		for dist in [-1.0, 5.0, 10.0, 20.0, 40.0]:
			var pts := PackedVector2Array()
			for k in range(41):
				var a: float = yaw0 + (float(k) / 40.0 - 0.5) * minf(spanr * 1.1, TAU * 0.999)
				var wv: Vector3 = Vector3(sin(a), 0.0, -cos(a)) * (1000.0 if dist < 0 else dist) + Vector3(0, 0 if dist < 0 else -hgt, 0)
				var uv := _project(po, wv)
				if uv.x < -0.2 or uv.x > 1.2 or uv.y < -0.2 or uv.y > 1.2:
					continue
				pts.append(_to_px(uv))
			if pts.size() > 1:
				var col := Color(0.35, 0.8, 1.0, 0.95) if dist < 0 else Color(1.0, 1.0, 1.0, 0.55)
				draw_polyline(pts, col, 2.0 if dist < 0 else 1.0, true)
				if dist > 0 and font != null:
					var mid: Vector2 = pts[pts.size() / 2]
					draw_string(font, mid + Vector2(4, -3), "%d m" % int(dist), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1, 0.8))
		# size check: a 1.75 m person at the clicked ground point
		for c in checks:
			var d: Vector3 = fm.dir_of(po[0], po[1], c)
			var t: float = fm.ground_hit(d)
			if t < 0.0:
				continue
			var foot := d * t
			var head := foot + Vector3(0, 1.75, 0)
			var a := _to_px(c)
			var b := _to_px(_project(po, head))
			draw_line(a, b, Color(1, 0.85, 0.2), 3.0)
			draw_circle(b + Vector2(0, (a.y - b.y) * 0.07), maxf(2.0, (a.y - b.y) * 0.07), Color(1, 0.85, 0.2))
			if font != null:
				draw_string(font, a + Vector2(5, -2), "1.75 m · %.1f m" % Vector2(foot.x, foot.z).length(), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 0.9, 0.4))
		for c in clicks:
			draw_circle(_to_px(c), 4.0, Color(0.35, 0.8, 1.0))
		draw_rect(r, Color(1, 1, 1, 0.25), false, 1.0)

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			var uv: Vector2 = (ev.position / _rect().size).clamp(Vector2.ZERO, Vector2.ONE)
			if ev.pressed:
				accept_event()
				if mode == "hz":
					_horizon_click(uv)
				elif mode == "size":
					checks.append(uv)
					if checks.size() > 4:
						checks.pop_front()
					queue_redraw()
				else:
					_drag = true
					_dab(uv)
			elif _drag:
				_drag = false
				if _dirty:
					_dirty = false
					fm.save_mask(idx, mimg)
		elif ev is InputEventMouseMotion and _drag:
			accept_event()
			_dab((ev.position / _rect().size).clamp(Vector2.ZERO, Vector2.ONE))

	func _horizon_click(uv: Vector2) -> void:
		var ps: Array = fm.photos()
		if idx >= ps.size():
			return
		var p: Dictionary = ps[idx]
		if clicks.size() >= 2:
			clicks.clear()
		clicks.append(uv)
		var asp := maxf(0.3, float(p.get("aspect", 1.5)))
		if clicks.size() == 1:
			fm.set_pval(idx, "fm_roll", 0.0)
			fm.set_pval(idx, "fm_hz", uv.y)
		else:
			var a: Vector2 = clicks[0]
			var b: Vector2 = clicks[1]
			if absf(b.x - a.x) < 0.05:
				clicks = [b]
				fm.set_pval(idx, "fm_hz", b.y)
			else:
				var roll := rad_to_deg(atan2((b.y - a.y), (b.x - a.x) * asp))
				var hz: float = a.y + (0.5 - a.x) * (b.y - a.y) / (b.x - a.x)
				fm.set_pval(idx, "fm_roll", clampf(roll if b.x > a.x else -roll, -15.0, 15.0))
				fm.set_pval(idx, "fm_hz", clampf(hz, 0.0, 1.0))
		queue_redraw()

	func _dab(uv: Vector2) -> void:
		if mimg == null:
			return
		var w := mimg.get_width()
		var h := mimg.get_height()
		var cx := int(uv.x * w)
		var cy := int(uv.y * h)
		var v := 255 if mode == "paint" else 0
		for y in range(maxi(0, cy - brush), mini(h, cy + brush + 1)):
			for x in range(maxi(0, cx - brush), mini(w, cx + brush + 1)):
				if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= brush * brush:
					mimg.set_pixel(x, y, Color8(v, v, v))
		_dirty = true
		_refresh_mask()


# ---- test / control API ------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var ps := photos()
	var ms := []
	for m in _masks:
		if is_instance_valid(m):
			ms.append(snappedf(float(m.get_meta("dist", 0.0)), 0.1))
	return {"on": on, "photos": ps.size(), "cover": snappedf(cover, 0.01), "hint": hint, "masks": ms, "cam_h": snappedf(float(gv("fm_h", main.mast_h)), 0.01),
			"hz": [] if ps.is_empty() else ps.map(func(p): return snappedf(float(p.get("fm_hz", 0.5)), 0.001)),
			"stats": gv("fm_st", {}), "gain": [snappedf(gain().x, 0.01), snappedf(gain().y, 0.01), snappedf(gain().z, 0.01)],
			"shadows": _sh_n, "sun": [snappedf(_sun.x, 0.01), snappedf(_sun.y, 0.01), snappedf(_sun.z, 0.01)]}


func control(d: Dictionary) -> Dictionary:
	"""{action: fotomodus, do: info | on (value) | set (key, value; fm_hz / fm_roll / yaw / span with i) | mask_rect (i, u0, v0, u1, v1, value)
	| mask_clear (i) | more (path) | measure | size (i, u, v -> distance, height in px) | debug (value)}"""
	var op := str(d.get("do", "info"))
	var i := int(d.get("i", 0))
	if op == "on":
		set_on(bool(d.get("value", true)))
	elif op == "set":
		var k := str(d.get("key", ""))
		if k in ["fm_hz", "fm_roll", "yaw", "span"]:
			set_pval(i, k, float(d.get("value", 0.0)))
			_texs.clear()
			_apply()
		elif k == "fm_front":
			set_val(k, bool(d.get("value", false)))
		elif k.begins_with("fm_"):
			set_val(k, float(d.get("value", 0.0)))
	elif op == "mask_rect":
		var img := mask_img(i, true)
		if img == null:
			return {"ok": false, "error": "kein Foto"}
		var w := img.get_width()
		var h := img.get_height()
		var v := 255 if bool(d.get("value", true)) else 0
		for y in range(int(float(d.get("v0", 0.4)) * h), int(float(d.get("v1", 0.6)) * h)):
			for x in range(int(float(d.get("u0", 0.4)) * w), int(float(d.get("u1", 0.6)) * w)):
				img.set_pixel(clampi(x, 0, w - 1), clampi(y, 0, h - 1), Color8(v, v, v))
		save_mask(i, img)
	elif op == "mask_clear":
		clear_mask(i)
	elif op == "more":
		return {"ok": import_more(str(d.get("path", ""))), "fotomodus": info()}
	elif op == "measure":
		measure()
	elif op == "debug":
		dbg = bool(d.get("value", true))
	elif op == "size":
		var ps := photos()
		if i >= ps.size():
			return {"ok": false}
		var po: Array = pose(ps[i])
		var dd := dir_of(po[0], po[1], Vector2(float(d.get("u", 0.5)), float(d.get("v", 0.8))))
		var t := ground_hit(dd)
		if t < 0.0:
			return {"ok": true, "above_horizon": true}
		var foot := dd * t
		var top := uv_of(po[0], po[1], (foot + Vector3(0, 1.75, 0)).normalized())
		var ey := eye()
		return {"ok": true, "dist": snappedf(Vector2(foot.x, foot.z).length(), 0.01), "head_v": snappedf(top.y, 0.001),
				"x": snappedf(ey.x + foot.x, 0.01), "z": snappedf(ey.z + foot.z, 0.01),
				"person_h": snappedf(float(d.get("v", 0.8)) - top.y, 0.0001)}
	return {"ok": true, "fotomodus": info()}
