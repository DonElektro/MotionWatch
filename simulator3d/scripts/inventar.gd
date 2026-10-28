extends PanelContainer
## 3D-3.86: das Inventar - alles, was die KI von MoveEye kennt (80 COCO-Klassen) und alle Besucher, in einem Fenster.
## Reiter: Menschen · Tiere · Fahrzeuge · Draussen · Gepäck & Sport · Küche & Essen · Haus & Elektro (+ Suche).
## Bild anklicken = setzen (dann in die Welt klicken, mehrmals möglich, Esc = fertig) oder direkt in die Welt ziehen.
## Menschen / laufende Tiere / fahrende Fahrzeuge kommen als Besucher; Gegenstände bleiben stehen und werden pro Szene in
## user://objekte.json gespeichert (beim Laden der Szene wieder hingestellt). Grosse Dinge sind Hindernisse.

var main
var Obj = preload("res://scripts/objects.gd")
var tabs: TabContainer
var _search: LineEdit
var _grids := {}                      # cat -> GridContainer
var _tiles := {}                      # key -> Button
var _list: VBoxContainer
var _msg: Label
var placed := {}                      # scene -> [{k, x, z, r}]
var _nodes: Array = []                # the objects of this scene in the world
var obj_thumbs := {}                  # kind -> Texture2D
var _thumbs_done := false
var _built := false

const UI = preload("res://scripts/ui_style.gd")
const FILE := "user://objekte.json"
const ANIMAL_VISITORS := ["fox", "deer", "boar", "cat", "dog", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "cow", "sheep", "horse",
		"chamois", "ibex", "lynx"]
const VEHICLE_VISITORS := [["car", "Auto (fährt)", "car"], ["moto", "Motorrad (fährt)", "motorcycle"], ["van", "Lieferwagen (fährt)", "truck"],
		["tractor", "Traktor (fährt)", "truck"], ["cyclist", "Velofahrer", "bicycle"]]


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.ACC, 14, 10, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	add_child(v)
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 8)
	v.add_child(hd)
	var t := UI.heading("Inventar")
	hd.add_child(t)
	_search = UI.search_field("Suchen (z. B. Koffer, Hund, Auto) …")
	_search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_search.text_changed.connect(func(_s): _filter())
	hd.add_child(_search)
	var x := Button.new()
	x.text = "✕"
	x.pressed.connect(func(): close())
	hd.add_child(x)
	tabs = TabContainer.new()
	tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(tabs)
	for c in Obj.CATS:
		var sc := ScrollContainer.new()
		sc.name = c[1]
		sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		tabs.add_child(sc)
		var g := GridContainer.new()
		g.columns = 6
		g.add_theme_constant_override("h_separation", 6)
		g.add_theme_constant_override("v_separation", 6)
		sc.add_child(g)
		_grids[c[0]] = g
	var ps := ScrollContainer.new()                    # the last tab: what stands in this scene
	ps.name = "In der Szene"
	tabs.add_child(ps)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ps.add_child(_list)
	_msg = UI.small("Bild anklicken und in die Welt klicken (mehrmals, Esc = fertig) – oder ins Bild ziehen. KI = so heisst es bei der Erkennung von MoveEye.")
	_msg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_msg.custom_minimum_size = Vector2(600, 0)
	v.add_child(_msg)
	_load()


func open() -> void:
	if not _built:
		_built = true
		_fill()
	visible = true
	get_parent().move_child(self, -1)
	_paint_list()
	if not _thumbs_done:
		_thumbs_done = true
		_make_thumbs()


func close() -> void:
	visible = false
	if main.place_kind.begins_with("obj:") or main.place_kind in _tiles:
		main.place_kind = ""
	_paint()


func toggle() -> void:
	if visible:
		close()
	else:
		open()


func _process(_dt: float) -> void:
	if not visible:
		return
	var vs := get_viewport_rect().size
	var w := minf(640.0, vs.x - (420.0 if main.ui_root.visible else 30.0))
	size = Vector2(w, minf(470.0, vs.y - 160.0))
	position = Vector2(14, vs.y - size.y - 110)


# ---- the tiles -----------------------------------------------------------------------------------------------------------
func _fill() -> void:
	for k in main.VISITOR_LIST:                        # people and walking animals: the visitors with their moving pictures
		var kind: String = k[0]
		var cat := "people" if kind in main.PEOPLE_KINDS else ("animals" if kind in ANIMAL_VISITORS else "")
		if cat == "":
			continue
		var coco: String = "person" if cat == "people" else {"cat": "cat", "dog": "dog", "horse": "horse", "sheep": "sheep", "cow": "cow"}.get(kind, "Tier (2. KI)")
		_tile(cat, kind, k[1], coco, main.thumbs.get(kind), "läuft")
	for k in VEHICLE_VISITORS:
		_tile("vehicles", k[0], k[1], k[2], main.thumbs.get(k[0]), "fährt")
	for kind in Obj.OBJ:
		var d: Dictionary = Obj.OBJ[kind]
		_tile(d["cat"], "obj:" + kind, d["n"], d["coco"], null, "steht")


func _tile(cat: String, key: String, name_: String, coco: String, tex, how: String) -> void:
	var b := Button.new()
	b.custom_minimum_size = Vector2(96, 104)
	b.clip_text = true
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = "%s · KI: %s · %s – anklicken und in die Welt klicken, oder hineinziehen" % [name_, coco, how]
	b.set_meta("search", (name_ + " " + coco + " " + key).to_lower())
	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.add_theme_constant_override("separation", 1)
	b.add_child(v)
	var tr := TextureRect.new()
	tr.custom_minimum_size = Vector2(84, 58)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tr.texture = tex
	tr.name = "pic"
	v.add_child(tr)
	var l := Label.new()
	l.text = name_
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", 11)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(88, 0)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(l)
	var c := Label.new()
	c.text = "KI: " + coco
	c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	c.add_theme_font_size_override("font_size", 9)
	c.add_theme_color_override("font_color", UI.MUT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(c)
	b.pressed.connect(func():
		main.place_kind = "" if main.place_kind == key else key
		_paint()
		if main.place_kind != "":
			main.start_info = "Setzen: %s – in die Welt klicken (mehrmals), Esc = fertig" % name_)
	b.set_drag_forwarding(func(_p):
		main.drag_kind = key
		var pv := TextureRect.new()
		pv.texture = tr.texture
		pv.custom_minimum_size = Vector2(72, 60)
		pv.size = Vector2(72, 60)
		pv.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pv.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		b.set_drag_preview(pv)
		return {"visitor": key}, func(_p, _d): return false, func(_p, _d): pass)
	_grids[cat].add_child(b)
	_tiles[key] = b


func _paint() -> void:
	for k in _tiles:
		var on: bool = main.place_kind == k
		_tiles[k].add_theme_stylebox_override("normal", UI.box(UI.ACC.darkened(0.5) if on else UI.BTN2, UI.ACC if on else UI.LINE, 10, 4, 2 if on else 1))


func _filter() -> void:
	var q := _search.text.strip_edges().to_lower()
	var first := -1
	for i in range(Obj.CATS.size()):
		var g: GridContainer = _grids[Obj.CATS[i][0]]
		var n := 0
		for b in g.get_children():
			var ok: bool = q == "" or str(b.get_meta("search")).contains(q)
			b.visible = ok
			if ok:
				n += 1
		if n > 0 and first < 0 and q != "":
			first = i
	if first >= 0:
		tabs.current_tab = first


func _make_thumbs() -> void:
	"""a picture of every object, once: one small world, the objects one after the other"""
	var vp := SubViewport.new()
	vp.size = Vector2i(128, 96)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var cam := Camera3D.new()
	cam.fov = 30
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.8, 0.82, 0.88)
	e.ambient_light_energy = 0.75
	cam.environment = e
	vp.add_child(cam)
	var sun_ := DirectionalLight3D.new()
	sun_.rotation = Vector3(deg_to_rad(-45), deg_to_rad(-35), 0)
	sun_.light_energy = 1.3
	vp.add_child(sun_)
	for kind in Obj.OBJ:
		var n: Node3D = Obj.build(main, kind)
		for ch in n.get_children():                    # the thermal twins are not needed here
			if ch is MeshInstance3D and (ch as MeshInstance3D).layers != 1:
				ch.visible = false
		vp.add_child(n)
		var box := AABB()
		var first := true
		for ch in n.get_children():
			if ch is MeshInstance3D and ch.visible:
				var a: AABB = (ch as MeshInstance3D).transform * (ch as MeshInstance3D).mesh.get_aabb()
				box = a if first else box.merge(a)
				first = false
		box = AABB(box.position * n.scale, box.size * n.scale)
		var c := box.get_center()
		var r := maxf(0.05, box.size.length() * 0.5)
		cam.position = c + Vector3(0.9, 0.55, 1.3).normalized() * r * 3.6
		cam.look_at(c, Vector3.UP)
		await get_tree().process_frame
		await get_tree().process_frame
		var img := vp.get_texture().get_image()
		obj_thumbs[kind] = ImageTexture.create_from_image(img)
		if _tiles.has("obj:" + kind):
			var pic: TextureRect = _tiles["obj:" + kind].find_child("pic", true, false)
			if pic != null:
				pic.texture = obj_thumbs[kind]
		n.queue_free()
	vp.queue_free()


# ---- placing, keeping ------------------------------------------------------------------------------------------------------
func is_obj(key: String) -> bool:
	return key.begins_with("obj:")


func place_at_screen(key: String, sp: Vector2) -> void:
	var cam: Camera3D = main.view_cam
	var from := cam.project_ray_origin(sp)
	var hit = main.ground_hit(from, cam.project_ray_normal(sp))
	if hit == null or from.distance_to(hit) > 400.0:
		return
	add_object(key.trim_prefix("obj:"), Vector3(hit.x, 0, hit.z), randf_range(0.0, 360.0))


func add_object(kind: String, p: Vector3, rot_deg: float, save := true) -> void:
	if not Obj.OBJ.has(kind):
		return
	var n: Node3D = Obj.build(main, kind)
	n.position = Vector3(p.x, main.ground_y(p.x, p.z), p.z)
	n.rotation.y = deg_to_rad(rot_deg)
	main.scene_parent.add_child(n)
	_nodes.append(n)
	var o = Obj.OBJ[kind].get("o")
	if o != null:
		main.add_obstacle_box(n.position, float(o[0]), float(o[1]), n.rotation.y)
	if save:
		var arr: Array = placed.get(main.scene, [])
		arr.append({"k": kind, "x": snappedf(p.x, 0.01), "z": snappedf(p.z, 0.01), "r": snappedf(rot_deg, 0.1)})
		placed[main.scene] = arr
		_save()
		_paint_list()


func rebuild() -> void:
	"""called after a scene was built: put this scene's objects back"""
	_nodes.clear()
	for e in placed.get(main.scene, []):
		add_object(str(e["k"]), Vector3(float(e["x"]), 0, float(e["z"])), float(e.get("r", 0.0)), false)


func remove(i: int) -> void:
	var arr: Array = placed.get(main.scene, [])
	if i < 0 or i >= arr.size():
		return
	arr.remove_at(i)
	placed[main.scene] = arr
	_save()
	main.set_scene(main.scene)                         # obstacles too: the scene is built again
	_paint_list()


func clear_scene() -> void:
	placed[main.scene] = []
	_save()
	main.set_scene(main.scene)
	_paint_list()


func _paint_list() -> void:
	if _list == null:
		return
	for c in _list.get_children():
		c.queue_free()
	var arr: Array = placed.get(main.scene, [])
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	_list.add_child(h)
	var l := UI.small("%d Gegenstände in «%s»" % [arr.size(), main.Scenes.name_of(main.scene)], UI.TXT)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	if not arr.is_empty():
		var cb := Button.new()
		cb.text = "Alle entfernen"
		cb.pressed.connect(clear_scene)
		h.add_child(cb)
	for i in range(arr.size()):
		var e: Dictionary = arr[i]
		var r := HBoxContainer.new()
		_list.add_child(r)
		var t := Label.new()
		t.text = "%s  ·  %.0f / %.0f m" % [Obj.OBJ.get(e["k"], {}).get("n", e["k"]), float(e["x"]), float(e["z"])]
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(t)
		var x := Button.new()
		x.text = "Weg"
		x.pressed.connect(remove.bind(i))
		r.add_child(x)


func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(placed))


func _load() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var js = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if typeof(js) == TYPE_DICTIONARY:
		placed = js


func info() -> Dictionary:
	return {"visible": visible, "objects": Obj.OBJ.size(), "coco": Obj.coco_count(), "scene": placed.get(main.scene, []).size(),
			"thumbs": obj_thumbs.size(), "tiles": _tiles.size()}
