extends Node
## 3D-4.4 «Dein Platz» (first called «Zwilling», internal names twin_* / zwilling.json stay for old saves): a photo or a panorama of the real place behind the scene (a piece of a cylinder round
## MoveEye, far away: the 3D ground with the visitors in front, the real trees, houses and mountains behind), plus the
## tent and the car placed by hand where they really stand. Everything per place (scene, at a real place also lat / lon)
## in user://zwilling.json, the pictures in user://zwilling/. Import: the window «Dein Platz» (inventar.gd, first tab; button
## or drag a .jpg / .png into the window), settings in «Szene · Dein Platz».
## 3D-4.x (Aufräumen, Daniel 29.10.2026): one thing «Dein Platz» - the inventory window holds this tab, the tent and the car
## are tiles there; the Vorlagen window has no tab «Dein Platz» any more.
## 3D-4.22 (Angleichen, Daniel 30.10.2026): «Dein Platz» is MoveEye's place (zones, patrol); here: «Foto des Platzes» (part of
## «Szene»), the window is «Gegenstände» (group «Platz & Umgebung»).

var main
const FILE := "user://zwilling.json"
const DIR := "user://zwilling"
var on := true
var data := {}                     # place key -> {img, span, yaw, dist, horizon, bright, items: [{k, x, z, r}]}
var info_txt := ""
var _back: MeshInstance3D = null
var _mat: StandardMaterial3D = null
var _nodes: Array = []
var _tex_key := ""
var _tex: ImageTexture = null
var _slow := 0.0
var _box: VBoxContainer = null     # the photo part of the tab «Dein Platz» (inventar.gd)
var _fd: FileDialog = null

const UI = preload("res://scripts/ui_style.gd")


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		on = bool(d.get("on", true))
		if typeof(d.get("places")) == TYPE_DICTIONARY:
			data = d["places"]


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"on": on, "places": data}))
		f.close()


func key() -> String:
	"""the place: the scene, at a real place (map) with its coordinates"""
	if main.scene == "ort" and main.ort_lat != 0.0:
		return "ort:%.4f,%.4f" % [main.ort_lat, main.ort_lon]
	return str(main.scene)


func cur() -> Dictionary:
	return data.get(key(), {})


func gv(k: String, def):
	return cur().get(k, def)


func set_val(k: String, v) -> void:
	var e: Dictionary = cur()
	if e.is_empty():
		return
	e[k] = v
	data[key()] = e
	save()
	_rebuild_back()


func add_controls() -> void:
	var m = main
	m.add_control("toggle", "twin_on", "Foto des Platzes: Foto / Panorama deines echten Platzes als Hintergrund (laden im Fenster «Gegenstände»)",
			func(): return on, func(v): on = bool(v); save(); on_scene(), "Szene", {"sub": "Foto des Platzes"})
	m.add_control("button", "twin_open", "«Gegenstände» öffnen: Foto des Platzes, Zelt, Auto, bewachte Sachen", null, func(): open_tab(), "Szene", {"sub": "Foto des Platzes"})
	m.add_control("slider", "twin_yaw", "Foto: Richtung der Bildmitte (0 = geradeaus)", func(): return float(gv("yaw", 0.0)), func(v): set_val("yaw", float(v)), "Szene",
			{"sub": "Foto des Platzes", "min": -180, "max": 180, "step": 1, "unit": "°"})
	m.add_control("slider", "twin_span", "Foto: Bildwinkel (Handyfoto etwa 65°, Panorama bis 360°)", func(): return float(gv("span", 66.0)), func(v): set_val("span", float(v)), "Szene",
			{"sub": "Foto des Platzes", "min": 30, "max": 360, "step": 1, "unit": "°"})
	m.add_control("slider", "twin_dist", "Foto: Entfernung des Hintergrunds", func(): return float(gv("dist", 60.0)), func(v): set_val("dist", float(v)), "Szene",
			{"sub": "Foto des Platzes", "min": 15, "max": 300, "step": 5, "unit": "m", "expert": true})
	m.add_control("slider", "twin_horizon", "Foto: Horizont im Bild höher / tiefer", func(): return float(gv("horizon", 0.0)), func(v): set_val("horizon", float(v)), "Szene",
			{"sub": "Foto des Platzes", "min": -20, "max": 20, "step": 0.5, "unit": "°", "expert": true})
	# 3D-4.x: tent and car are tiles in the window «Gegenstände» (3D-4.22, was «Dein Platz») (not twice here); for MoveEye's page they stay hidden controls
	m.add_control("button", "twin_tent", "Zelt hierhin – danach in die Welt klicken", null, func(): main.place_kind = "twin_tent", "Szene", {"sub": "Foto des Platzes", "hide": true})
	m.add_control("button", "twin_car", "Auto hierhin – danach in die Welt klicken", null, func(): main.place_kind = "twin_car", "Szene", {"sub": "Foto des Platzes", "hide": true})
	m.add_control("button", "twin_turn", "Zuletzt gesetztes Zelt / Auto um 15° drehen", null, func(): turn_last(15.0), "Szene", {"sub": "Foto des Platzes", "expert": true})
	m.add_control("button", "twin_clear", "Zelt und Auto dieses Platzes entfernen", null, func(): clear_items(), "Szene", {"sub": "Foto des Platzes", "expert": true})


# ---- import ----------------------------------------------------------------------------------------------------------
func import_image(path: String) -> bool:
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		_say("Bild nicht lesbar: " + path.get_file())
		return false
	if img.get_width() > 4096:
		img.resize(4096, int(img.get_height() * 4096.0 / img.get_width()), Image.INTERPOLATE_LANCZOS)
	if img.get_height() > 2048:
		img.resize(int(img.get_width() * 2048.0 / img.get_height()), 2048, Image.INTERPOLATE_LANCZOS)
	DirAccess.make_dir_recursive_absolute(DIR)
	var k := key()
	var fn := DIR + "/" + k.validate_filename().replace(":", "_").replace(",", "_") + ".jpg"
	if img.save_jpg(fn, 0.88) != OK:
		_say("Kann nicht speichern: " + fn)
		return false
	var asp := float(img.get_width()) / float(img.get_height())
	var e: Dictionary = cur()
	e["img"] = fn
	e["src"] = path.get_file()
	e["aspect"] = asp
	if not e.has("span") or e.has("auto_span"):
		e["span"] = 360.0 if asp >= 1.95 else (minf(300.0, asp * 40.0) if asp > 2.2 else 66.0)   # 2:1 = a whole panorama
		e["auto_span"] = true
	for kk in [["yaw", 0.0], ["dist", 60.0], ["horizon", 0.0], ["bright", 1.0]]:
		if not e.has(kk[0]):
			e[kk[0]] = kk[1]
	if not e.has("items"):
		e["items"] = []
	data[k] = e
	_tex_key = ""
	on = true
	save()
	on_scene()
	_say("«%s» ist jetzt der Hintergrund von «%s» (%d × %d, Bildwinkel %d°). Richtung und Winkel unter «Szene · Foto des Platzes»." % [path.get_file(), place_name(), img.get_width(), img.get_height(), int(e["span"])])
	_paint()
	return true


func place_name() -> String:
	return main.place_label() if main.scene == "ort" and main.ort_lat != 0.0 else main.Scenes.name_of(main.scene)


func remove_image() -> void:
	var e: Dictionary = cur()
	e.erase("img")
	data[key()] = e
	save()
	on_scene()
	_paint()


# ---- the backdrop and the things -------------------------------------------------------------------------------------
func on_scene() -> void:
	"""after a scene was built (main._build_scene): backdrop and things of this place"""
	_back = null
	_nodes.clear()
	if not on:
		return
	_rebuild_back()
	for it in cur().get("items", []):
		_build_item(it)
	_paint()


func _rebuild_back() -> void:
	if _back != null and is_instance_valid(_back):
		_back.queue_free()
		if _back.has_meta("th") and is_instance_valid(_back.get_meta("th")):
			_back.get_meta("th").queue_free()
	_back = null
	var e: Dictionary = cur()
	if not on or not e.has("img") or main.scenes == null or main.scenes.root == null:
		info_txt = "kein Foto für «%s»" % place_name() if main.scenes != null else ""
		return
	if _tex_key != str(e["img"]):
		var img := Image.load_from_file(ProjectSettings.globalize_path(str(e["img"])))
		if img == null or img.is_empty():
			info_txt = "Foto fehlt: " + str(e["img"])
			return
		img.generate_mipmaps()
		_tex = ImageTexture.create_from_image(img)
		_tex_key = str(e["img"])
	var span := deg_to_rad(clampf(float(e.get("span", 66.0)), 10.0, 360.0))
	var asp := maxf(0.5, float(e.get("aspect", 1.5)))
	var R := clampf(float(e.get("dist", 60.0)), 10.0, 400.0)
	var vspan := clampf(span / asp, deg_to_rad(10.0), deg_to_rad(150.0))      # the picture keeps its shape (cylinder)
	var yaw := deg_to_rad(float(e.get("yaw", 0.0)))
	var hp: Vector3 = main.head.global_position if main.head != null and main.head.is_inside_tree() else Vector3(main.home_pos.x, 1.5, main.home_pos.z)
	var c := Vector3(hp.x, 0, hp.z)
	var y_mid: float = hp.y + R * tan(deg_to_rad(float(e.get("horizon", 0.0))))
	var half_h: float = R * tan(vspan * 0.5) if vspan < deg_to_rad(120.0) else R * vspan * 0.5
	var n: int = clampi(int(rad_to_deg(span) / 4.0), 8, 90)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in range(n):
		for q in [[j, 0], [j + 1, 0], [j + 1, 1], [j, 0], [j + 1, 1], [j, 1]]:
			var u: float = float(q[0]) / n
			var a: float = yaw - span * 0.5 + span * u
			var top: bool = q[1] == 1
			st.set_uv(Vector2(u, 0.0 if top else 1.0))
			st.add_vertex(c + Vector3(sin(a) * R, (y_mid + half_h) if top else (y_mid - half_h), -cos(a) * R))
	var mesh := st.commit()
	_mat = StandardMaterial3D.new()
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mat.albedo_texture = _tex
	_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_mat.disable_fog = false
	_back = MeshInstance3D.new()
	_back.mesh = mesh
	_back.material_override = _mat
	_back.layers = 1
	_back.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.scenes.root.add_child(_back)
	var th := MeshInstance3D.new()                       # thermal: far away, a little colder than the air (like the hills)
	th.mesh = mesh
	th.material_override = main.tmat("hill")
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.scenes.root.add_child(th)
	_back.set_meta("th", th)
	_light()
	info_txt = "Hintergrund: %s · %d° · %d m" % [str(e.get("src", "Foto")), int(rad_to_deg(span)), int(R)]


func _light() -> void:
	"""the photo was taken by day: as dark as the light of the scene (at night only the infrared reaches it - nearly black)"""
	if _mat == null or _back == null or not is_instance_valid(_back):
		return
	var k: float = clampf(main.light_level() * 1.05, 0.02, 1.0) * float(cur().get("bright", 1.0))
	_mat.albedo_color = Color(k, k, k)


func _process(dt: float) -> void:
	_slow -= dt
	if _slow <= 0.0:
		_slow = 0.5
		_light()


func place_at_screen(kind: String, sp: Vector2) -> void:
	var cam: Camera3D = main.view_cam
	var from := cam.project_ray_origin(sp)
	var hit = main.ground_hit(from, cam.project_ray_normal(sp))
	if hit == null or from.distance_to(hit) > 400.0:
		return
	add_item(kind.trim_prefix("twin_"), hit.x, hit.z, 0.0)


func add_item(k: String, x: float, z: float, r: float) -> void:
	var e: Dictionary = cur()
	if not e.has("items"):
		e["items"] = []
	var it := {"k": k, "x": snappedf(x, 0.01), "z": snappedf(z, 0.01), "r": snappedf(r, 0.1)}
	(e["items"] as Array).append(it)
	data[key()] = e
	save()
	_build_item(it)
	if main.inventar != null:
		main.inventar._paint()
		main.inventar._paint_list()
	_say("%s gesetzt (%.1f / %.1f m). Drehen: «Zuletzt gesetztes … drehen»." % ["Zelt" if k == "tent" else "Auto", x, z])
	_paint()


func turn_last(deg: float) -> void:
	var items: Array = cur().get("items", [])
	if items.is_empty():
		return
	items[-1]["r"] = fposmod(float(items[-1].get("r", 0.0)) + deg, 360.0)
	save()
	main.set_scene(main.scene)                             # obstacles too: the scene is built again


func clear_items() -> void:
	var e: Dictionary = cur()
	e["items"] = []
	data[key()] = e
	save()
	main.set_scene(main.scene)
	_paint()


func _build_item(it: Dictionary) -> void:
	var sc = main.scenes
	if sc == null or sc.root == null:
		return
	var p := Vector3(float(it["x"]), 0, float(it["z"]))
	p.y = main.ground_y(p.x, p.z)
	var r := deg_to_rad(float(it.get("r", 0.0)))
	if str(it["k"]) == "car":
		sc.static_car(p, r, Color(0.75, 0.75, 0.78))
		return
	var tn: Node3D = sc.node(sc.root, p, r)
	var tent := PrismMesh.new()
	tent.size = Vector3(2.6, 1.5, 2.4)
	sc.put(tn, tent, Vector3(0, 0.75, 0), Color(0.25, 0.45, 0.3), "tent")
	var fly := PrismMesh.new()
	fly.size = Vector3(2.9, 1.58, 2.0)
	sc.put(tn, fly, Vector3(0, 0.78, 0), Color(0.2, 0.38, 0.25), "tent")
	var door := PrismMesh.new()
	door.size = Vector3(0.9, 0.9, 0.02)
	sc.put(tn, door, Vector3(0, 0.45, 1.21), Color(0.1, 0.08, 0.06), "tent")
	main.add_obstacle_node(tn, Vector3.ZERO, 3.0, 2.8)
	main.set_obstacle_height(1.4)
	main.obj["pir"] = p                                       # the PIR sensor «Zelt» and the visitors go to this tent
	_nodes.append(tn)


# ---- the photo part «Foto des Platzes» of the group «Platz & Umgebung» (inventar.gd) -------------------------------------------------------------
func open_tab() -> void:
	if main.inventar != null:
		main.inventar.open_sec("photo")                  # 3D-4.22: window «Gegenstände», part «Foto des Platzes»
		_paint()


func build_tab(v: VBoxContainer) -> void:
	"""inventar.gd: the photo / panorama part «Foto des Platzes»"""
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 8)
	v.add_child(_box)
	_fd = FileDialog.new()
	_fd.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	_fd.access = FileDialog.ACCESS_FILESYSTEM
	_fd.filters = PackedStringArray(["*.jpg, *.jpeg, *.png, *.webp ; Foto oder Panorama"])
	_fd.title = "Foto oder Panorama deines Platzes wählen"
	_fd.size = Vector2i(760, 480)
	_fd.file_selected.connect(func(p): import_image(p))
	v.add_child(_fd)
	_paint()


func _paint() -> void:
	if _box == null or not is_instance_valid(_box):
		return
	for ch in _box.get_children():
		ch.queue_free()
	var e: Dictionary = cur()
	var l := UI.small("Platz: «%s»  ·  %s" % [place_name(), info_txt if e.has("img") else "noch kein Foto"], UI.TXT)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(520, 0)
	_box.add_child(l)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	_box.add_child(h)
	var b := Button.new()
	b.text = "Foto / Panorama wählen …"
	UI.primary(b)
	b.pressed.connect(func(): _fd.popup_centered())
	h.add_child(b)
	if e.has("img"):
		var x := Button.new()
		x.text = "Foto weg"
		x.pressed.connect(remove_image)
		h.add_child(x)
	var items: Array = e.get("items", [])
	if not items.is_empty():
		var t := UI.small("Zelt / Auto gesetzt (%d): %s" % [items.size(), ", ".join(items.map(func(i): return ("Zelt" if i["k"] == "tent" else "Auto") + " %.0f/%.0f m" % [float(i["x"]), float(i["z"])]))], UI.MUT)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size = Vector2(520, 0)
		_box.add_child(t)


func _say(s: String) -> void:
	info_txt = s
	if main.inventar != null and main.inventar._msg != null:
		main.inventar._msg.text = s


func info() -> Dictionary:
	return {"on": on, "key": key(), "place": cur(), "back": _back != null and is_instance_valid(_back), "items": cur().get("items", []).size(), "info": info_txt}


func control(d: Dictionary) -> Dictionary:
	"""control API {action: zwilling, do: info | import (path) | set (key, value) | item (k, x, z, r) | clear | remove}"""
	var op := str(d.get("do", "info"))
	if op == "import":
		return {"ok": import_image(str(d.get("path", ""))), "zwilling": info()}
	elif op == "set":
		set_val(str(d.get("key", "yaw")), float(d.get("value", 0.0)))
	elif op == "item":
		add_item(str(d.get("k", "tent")), float(d.get("x", 0.0)), float(d.get("z", -8.0)), float(d.get("r", 0.0)))
	elif op == "clear":
		clear_items()
	elif op == "remove":
		remove_image()
	elif op == "on":
		on = bool(d.get("value", true))
		save()
		on_scene()
	return {"ok": true, "zwilling": info()}
