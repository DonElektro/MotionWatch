extends PanelContainer
## 3D-3.73: «Mein Zuhause bauen» - a little building kit. Choose a thing, click into the world to place it (fence, hedge,
## wall and path: two clicks, start and end). Click a placed thing to choose it, then turn / bigger / smaller / away.
## Right click on a thing = away. Everything is saved in user://zuhause.json; the scene «Mein Zuhause» is built from it.

const Scenes = preload("res://scripts/scenes.gd")
const UI = preload("res://scripts/ui_style.gd")

var main
var kind := ""                 # the thing to place ("" = choose things)
var sel := -1                  # index of the chosen thing in main.home_items
var _start = null              # first click of a line
var _undo: Array = []
var _info: Label
var _btns := {}
var _mk: Node3D


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.94), UI.ACC, 12, 10, 1))
	custom_minimum_size = Vector2(300, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	add_child(v)
	var h := Label.new()
	h.text = "Mein Zuhause bauen"
	h.add_theme_font_override("font", UI.heading_font())
	h.add_theme_font_size_override("font_size", 16)
	v.add_child(h)
	_info = UI.small("")
	_info.custom_minimum_size = Vector2(280, 0)
	v.add_child(_info)
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 4)
	g.add_theme_constant_override("v_separation", 4)
	v.add_child(g)
	for k in Scenes.HOME_KINDS:
		var b := Button.new()
		b.text = k[1]
		b.focus_mode = Control.FOCUS_NONE
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.add_theme_font_size_override("font_size", 12)
		b.pressed.connect(_pick.bind(k[0]))
		g.add_child(b)
		_btns[k[0]] = b
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 4)
	v.add_child(r1)
	for d in [["⟲ 15°", func(): _turn(-15.0)], ["⟳ 15°", func(): _turn(15.0)], ["Grösser", func(): _size(1.15)], ["Kleiner", func(): _size(1.0 / 1.15)], ["Weg", _delete_sel]]:
		var b2 := Button.new()
		b2.text = d[0]
		b2.focus_mode = Control.FOCUS_NONE
		b2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b2.add_theme_font_size_override("font_size", 12)
		b2.pressed.connect(d[1])
		r1.add_child(b2)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 4)
	v.add_child(r2)
	for d in [["↶ Rückgängig", _undo_last], ["Alles leeren", _clear_all], ["Beispiel", _example], ["✓ Fertig", func(): open(false)]]:
		var b3 := Button.new()
		b3.text = d[0]
		b3.focus_mode = Control.FOCUS_NONE
		b3.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b3.add_theme_font_size_override("font_size", 12)
		b3.pressed.connect(d[1])
		r2.add_child(b3)
	_mk = Node3D.new()
	main.add_child.call_deferred(_mk)
	_paint()


func open(on: bool) -> void:
	visible = on
	kind = ""
	sel = -1
	_start = null
	if on and main.scene != "zuhause":
		main.set_scene("zuhause")
	if on and main.home_items.is_empty():
		main.home_items = Scenes.HOME_DEFAULT.duplicate(true)       # start from the example - easier than an empty meadow
		main.home_save()
	_paint()


func _pick(k: String) -> void:
	kind = "" if kind == k else k
	_start = null
	sel = -1
	_paint()


func _paint() -> void:
	for k in _btns:
		(_btns[k] as Button).add_theme_color_override("font_color", Color(0.45, 0.95, 0.55) if k == kind else Color(0.88, 0.9, 0.93))
	var nm := ""
	for k in Scenes.HOME_KINDS:
		if k[0] == kind:
			nm = k[1]
	if kind != "":
		_info.text = ("%s: in die Welt klicken" % nm) + (" – Anfang" if kind in Scenes.HOME_LINES and _start == null else (" – Ende" if kind in Scenes.HOME_LINES else "")) + ". Rechtsklick auf ein Ding = weg. Nochmals drücken = nichts setzen."
	elif sel >= 0 and sel < main.home_items.size():
		_info.text = "Gewählt: %s – drehen, grösser / kleiner oder weg. Ziehen bewegt weiterhin die Ansicht." % _name(str(main.home_items[sel].get("k", "")))
	else:
		_info.text = "Ein Ding wählen und in die Welt klicken, oder ein gesetztes Ding anklicken. MoveEye steht in der Mitte (roter Punkt auf der Karte). %d Dinge." % main.home_items.size()
	_mark()


func _name(k: String) -> String:
	for x in Scenes.HOME_KINDS:
		if x[0] == k:
			return x[1]
	return k


func _mark() -> void:
	for c in _mk.get_children():
		c.queue_free()
	if not visible or sel < 0 or sel >= main.home_items.size():
		return
	var it: Dictionary = main.home_items[sel]
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 1.6
	tm.outer_radius = 1.8
	ring.mesh = tm
	var mt := StandardMaterial3D.new()
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.albedo_color = Color(1.0, 0.85, 0.3)
	ring.material_override = mt
	ring.layers = main.HELPER_LAYER
	var p := _pos(it)
	ring.position = Vector3(p.x, main.ground_y(p.x, p.y) + 0.1, p.y)
	_mk.add_child(ring)


func _pos(it: Dictionary) -> Vector2:
	var a := Vector2(float(it.get("x", 0.0)), float(it.get("z", 0.0)))
	if str(it.get("k", "")) in Scenes.HOME_LINES:
		return (a + Vector2(float(it.get("x2", a.x)), float(it.get("z2", a.y)))) / 2.0
	return a


func _nearest(q: Vector2) -> int:
	var best := -1
	var bd := 3.5
	for i in range(main.home_items.size()):
		var d := _pos(main.home_items[i]).distance_to(q)
		if d < bd:
			bd = d
			best = i
	return best


func _change() -> void:
	main.home_save()
	main.home_rebuild()
	_paint()


func _push_undo() -> void:
	_undo.append(main.home_items.duplicate(true))
	if _undo.size() > 40:
		_undo.pop_front()


func handle_input(ev: InputEvent) -> bool:
	"""clicks into the world while the kit is open (a drag still moves the view)"""
	if not visible or not (ev is InputEventMouseButton) or main._over_hud(ev.position) or get_global_rect().has_point(ev.position):
		return false
	var cam: Camera3D = main.view_cam
	var hit = main.ground_hit(cam.project_ray_origin(ev.position), cam.project_ray_normal(ev.position))
	if hit == null:
		return false
	var q := Vector2(hit.x, hit.z)
	if ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			set_meta("down", ev.position)
			return false
		var dn = get_meta("down", null)
		if dn == null or (ev.position as Vector2).distance_to(dn) > 8.0:
			return false                                  # a drag: the view moved
		if kind == "":
			sel = _nearest(q)
			_paint()
			return false
		if kind in Scenes.HOME_LINES:
			if _start == null:
				_start = q
				_paint()
				return false
			_push_undo()
			main.home_items.append({"k": kind, "x": snappedf(_start.x, 0.1), "z": snappedf(_start.y, 0.1), "x2": snappedf(q.x, 0.1), "z2": snappedf(q.y, 0.1), "r": 0.0, "s": 1.0})
			_start = null
		else:
			_push_undo()
			main.home_items.append({"k": kind, "x": snappedf(q.x, 0.1), "z": snappedf(q.y, 0.1), "r": 0.0, "s": 1.0})
		sel = main.home_items.size() - 1
		_change()
		return false
	if ev.button_index == MOUSE_BUTTON_RIGHT and ev.pressed:
		var i := _nearest(q)
		if i >= 0:
			_push_undo()
			main.home_items.remove_at(i)
			sel = -1
			_change()
			return true
	return false


func _turn(deg: float) -> void:
	if sel < 0 or sel >= main.home_items.size():
		return
	_push_undo()
	var it: Dictionary = main.home_items[sel]
	if str(it.get("k", "")) in Scenes.HOME_LINES:              # a line turns round its middle
		var c := _pos(it)
		var a := Vector2(float(it["x"]), float(it["z"])) - c
		var b := Vector2(float(it["x2"]), float(it["z2"])) - c
		a = a.rotated(deg_to_rad(deg)) + c
		b = b.rotated(deg_to_rad(deg)) + c
		it["x"] = snappedf(a.x, 0.1); it["z"] = snappedf(a.y, 0.1); it["x2"] = snappedf(b.x, 0.1); it["z2"] = snappedf(b.y, 0.1)
	else:
		it["r"] = wrapf(float(it.get("r", 0.0)) + deg, -180.0, 180.0)
	_change()


func _size(f: float) -> void:
	if sel < 0 or sel >= main.home_items.size():
		return
	_push_undo()
	var it: Dictionary = main.home_items[sel]
	it["s"] = clampf(float(it.get("s", 1.0)) * f, 0.3, 3.0)
	_change()


func _delete_sel() -> void:
	if sel < 0 or sel >= main.home_items.size():
		return
	_push_undo()
	main.home_items.remove_at(sel)
	sel = -1
	_change()


func _undo_last() -> void:
	if _undo.is_empty():
		return
	main.home_items = _undo.pop_back()
	sel = -1
	_change()


func _clear_all() -> void:
	_push_undo()
	main.home_items = [{"k": "busch", "x": 30.0, "z": -40.0, "r": 0.0, "s": 0.5}]    # nearly empty (empty = the example)
	sel = -1
	_change()


func _example() -> void:
	_push_undo()
	main.home_items = Scenes.HOME_DEFAULT.duplicate(true)
	sel = -1
	_change()
