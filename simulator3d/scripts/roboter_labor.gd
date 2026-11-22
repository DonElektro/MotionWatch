extends Node
## «Roboter-Labor» (Besitzer 22.11.2026, Fragebogen 15:36–15:40): eine eigene kleine 3D-Welt für den Segment-Roboter des
## Besitzers (eigenes Projekt, erst im Simulator entwickeln, später vielleicht für MoveEye). Öffnen: Mehr → «Roboter»,
## /control {"action": "roboter", "do": "open"}. Vorerst nur am PC (Maus + Tasten); alles liegt in einem eigenen
## Fenster mit eigener Welt (eigene Physik, die Szene von MoveEye bleibt, wie sie ist), damit es später auch auf Handy /
## Pad / Kiosk gehen kann (nichts hier hängt an einer Bildschirmgrösse, das Bedienfeld scrollt).
##   Teile: roboter_modell.gd (Form, Körper, Servos, Physik, Kupplung, Kollision rot), roboter_bewegung.gd (Bein-Rechnung,
##   Posen; Stufe 2: Abläufe, Gangarten), roboter_gelaende.gd (Boden mit Raster, Rampe, Stufe, Kies, Graben).
## Physik: eigene World3D (SubViewport own_world_3d) mit 24 Löser-Durchgängen; solange das Labor offen ist, rechnet die
## Physik mit 120 Schritten pro Sekunde (sonst 30, beim Schliessen zurück).
## Bedienfeld rechts: Form · Gelenke · Posen · Physik · Ansicht. Tasten: 1 frei · 2 Seite · 3 oben · 4 Roboter-Kamera ·
## R neu aufstellen · P Physik anhalten · F festhalten · K Kamerabild klein · H Bedienfeld · + / − zoomen · Esc schliessen.
## Maus in der 3D-Ansicht: ziehen = drehen, rechts / Mitte ziehen = verschieben, Rad = zoomen.
## /control {"action": "roboter", "do": open | close | info | pose (name, snap) | set (id, value) | param (key, value) |
##           view (frei | seite | oben | roboter) | pause (on) | reset | hold (on) | tab (name) | pip (on)}

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const MODELL = preload("res://scripts/roboter_modell.gd")
const BEWEGUNG = preload("res://scripts/roboter_bewegung.gd")
const GELAENDE = preload("res://scripts/roboter_gelaende.gd")
const TICKS := 120
const PANEL_W := 380.0
const TABS := [["form", "Form"], ["gelenke", "Gelenke"], ["posen", "Posen"], ["physik", "Physik"], ["ansicht", "Ansicht"]]
const VIEWS := [["frei", "Frei"], ["seite", "Seite"], ["oben", "Oben"], ["roboter", "Roboter-Kamera"]]
const FORM := [   # [key, name, unit, step]
	["segmente", "Segmente", "", 1.0], ["halbe_breite", "Halbe Breite", "E", 0.01], ["halbe_breite_spitze", "Halbe Breite Spitze", "E", 0.01],
	["laenge_mittelteil", "Länge Mittelteil", "E", 0.01], ["abstand_gelenk", "Abstand im Gelenk", "E", 0.01],
	["oberschenkel", "Oberschenkel", "E", 0.01], ["unterschenkel", "Unterschenkel", "E", 0.01], ["mast_hoehe", "Mast der Kamera", "E", 0.01],
	["massstab", "Massstab (Meter pro Einheit)", "m", 0.005], ["masse_segment", "Masse je Segment", "kg", 0.01],
	["masse_bein", "Masse je Bein", "kg", 0.01]]
const PHYSIK := [["moment_koerper", "Servo-Moment Segmentgelenk", "N·m", 0.1], ["moment_bein", "Servo-Moment Bein", "N·m", 0.05],
	["tempo_servo", "Servo-Tempo", "°/s", 10.0], ["reibung", "Reibung am Boden", "", 0.05]]

var main
var mehr
var layer: CanvasLayer
var win: Control = null
var vpc: SubViewportContainer
var vp: SubViewport
var world: Node3D
var cam: Camera3D
var pip_vp: SubViewport
var pip_cam: Camera3D
var pip_box: Control
var model                              # roboter_modell.gd
var bew                                # roboter_bewegung.gd
var starts := {}                       # lane -> Transform3D (roboter_gelaende.gd)
var view := "frei"
var tab := "form"
var paused := false
var pip := true
var follow := true
var gravity := 9.81
var yaw := -35.0
var pitch := 24.0
var dist := 3.2
var target := Vector3(-0.5, 0.1, 0)
var last_pose := "gerade"
var _old_ticks := 30
var _w := {}                           # widgets
var _sl := {}                          # servo id -> {sl, val}
var _drag := 0
var _rebuild_t := -1.0
var _ui_t := 0.0
var _panel_on := true


func is_open() -> bool:
	return win != null and is_instance_valid(win)


func open() -> void:
	if is_open():
		return
	if mehr != null:
		mehr.close_window()
		mehr.close_menu()
	layer = CanvasLayer.new()
	layer.layer = 62
	add_child(layer)
	_old_ticks = Engine.physics_ticks_per_second
	Engine.physics_ticks_per_second = TICKS
	_build_world()
	_build_ui()
	_start_physics()
	set_view(view)
	set_tab(tab)


func close() -> void:
	if not is_open():
		return
	layer.queue_free()
	layer = null
	win = null
	model = null
	_sl = {}
	_w = {}
	Engine.physics_ticks_per_second = _old_ticks


# ---- die Welt ------------------------------------------------------------------------------------------------------------
func _build_world() -> void:
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_2X
	vp.positional_shadow_atlas_size = 2048
	world = Node3D.new()
	world.name = "roboter_labor"
	vp.add_child(world)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#c9d3dc")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("#b8c4d0")
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	world.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -35, 0)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 25.0
	world.add_child(sun)
	starts = GELAENDE.build(world)
	cam = Camera3D.new()
	cam.current = true
	cam.near = 0.02
	cam.far = 120.0
	world.add_child(cam)
	model = MODELL.new()
	model.name = "segmentroboter"
	world.add_child(model)
	bew = BEWEGUNG.new()
	bew.m = model


func _start_physics() -> void:
	"""once the viewport is in the tree (joints need node paths): own space settings, then the robot"""
	var sp: RID = vp.find_world_3d().space
	model.space_rid = sp
	PhysicsServer3D.space_set_param(sp, PhysicsServer3D.SPACE_PARAM_SOLVER_ITERATIONS, MODELL.LOESER)
	PhysicsServer3D.area_set_param(sp, PhysicsServer3D.AREA_PARAM_GRAVITY, gravity)
	_rebuild(true)


func _rebuild(new_pose: bool) -> void:
	"""after a change of the shape: build again, the robot stands at the start in the last pose"""
	var keep: Dictionary = {} if new_pose else model.targets()
	model.build(starts.get("start", Transform3D()), {})
	if new_pose or keep.is_empty() or keep.size() != model.servos.size():
		bew.apply(bew.pose(last_pose))
	else:
		bew.apply(keep)
	model.place(true)
	_fill_servo_sliders()


func _physics_process(dt: float) -> void:
	if not is_open() or model == null or paused:
		return
	model.step(dt)


func _process(dt: float) -> void:
	if not is_open():
		return
	if _rebuild_t > 0.0:
		_rebuild_t -= dt
		if _rebuild_t <= 0.0:
			_rebuild(false)
			_refresh_form_info()
	_camera(dt)
	_ui_t -= dt
	if _ui_t <= 0.0:
		_ui_t = 0.2
		_refresh()


# ---- Kamera ---------------------------------------------------------------------------------------------------------------
func set_view(v: String) -> void:
	view = v if v in VIEWS.map(func(x): return x[0]) else "frei"
	for x in VIEWS:
		var b: Button = _w.get("view_" + x[0])
		if b != null:
			_paint_btn(b, x[0] == view)
	if pip_box != null:
		pip_box.visible = pip and view != "roboter"
		pip_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS if pip_box.visible else SubViewport.UPDATE_DISABLED


func _camera(dt: float) -> void:
	if model == null or not model.built_ok:
		return
	var c: Vector3 = model.com()
	if follow:
		target = target.lerp(Vector3(c.x, maxf(0.05, c.y), c.z), clampf(dt * 3.0, 0.0, 1.0))
	var length: float = model.pitch_len() * model.n()
	match view:
		"seite":
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = maxf(0.5, length * 1.5) * dist / 3.2
			cam.global_transform = Transform3D(Basis(), target + Vector3(0, 0.25, 8.0))
			cam.look_at(target + Vector3(0, 0.25, 0), Vector3.UP)
		"oben":
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = maxf(0.5, length * 1.6) * dist / 3.2
			cam.global_transform = Transform3D(Basis(), target + Vector3(0, 9.0, 0.001))
			cam.look_at(target, Vector3.FORWARD)
		"roboter":
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 70.0
			if model.robot_cam != null:
				cam.global_transform = model.robot_cam.global_transform
		_:
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 50.0
			var r := deg_to_rad(yaw)
			var pt := deg_to_rad(pitch)
			var off := Vector3(cos(pt) * sin(r), sin(pt), cos(pt) * cos(r)) * dist
			cam.global_transform = Transform3D(Basis(), target + off)
			cam.look_at(target, Vector3.UP)
	if pip_cam != null and model.robot_cam != null:
		pip_cam.global_transform = model.robot_cam.global_transform


func _view_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom(1)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom(-1)
		elif mb.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			_drag = mb.button_index if mb.pressed else 0
	elif ev is InputEventMouseMotion and _drag != 0:
		var rel := (ev as InputEventMouseMotion).relative
		if _drag == MOUSE_BUTTON_LEFT and view == "frei":
			yaw -= rel.x * 0.35
			pitch = clampf(pitch + rel.y * 0.3, -5.0, 88.0)
		elif _drag != MOUSE_BUTTON_LEFT or view in ["seite", "oben"]:
			follow = false
			_paint_toggles()
			var k := dist * 0.0016
			var right := cam.global_transform.basis.x
			var upv := cam.global_transform.basis.y
			target -= (right * rel.x - upv * rel.y) * k
			if view == "oben":
				target.y = maxf(target.y, 0.0)


func zoom(dir: int) -> void:
	dist = clampf(dist * (0.88 if dir > 0 else 1.0 / 0.88), 0.3, 25.0)


func _input(ev: InputEvent) -> void:
	if not is_open() or not (ev is InputEventKey):
		return
	var k := ev as InputEventKey
	get_viewport().set_input_as_handled()            # the lab has the keyboard while it is open
	if not k.pressed or k.echo or k.ctrl_pressed or k.alt_pressed or k.meta_pressed:
		return
	match k.keycode:
		KEY_ESCAPE:
			close()
		KEY_1:
			set_view("frei")
		KEY_2:
			set_view("seite")
		KEY_3:
			set_view("oben")
		KEY_4:
			set_view("roboter")
		KEY_R:
			reset()
		KEY_P:
			set_paused(not paused)
		KEY_F:
			set_hold(not model.hold)
		KEY_K:
			set_pip(not pip)
		KEY_H:
			_panel_on = not _panel_on
			(_w["panel"] as Control).visible = _panel_on
		KEY_PLUS, KEY_KP_ADD, KEY_EQUAL:
			zoom(1)
		KEY_MINUS, KEY_KP_SUBTRACT:
			zoom(-1)


# ---- Aktionen -------------------------------------------------------------------------------------------------------------
func set_paused(on: bool) -> void:
	paused = on
	if model != null and model.space_rid.is_valid():
		PhysicsServer3D.space_set_active(model.space_rid, not on)
	_paint_toggles()


func set_hold(on: bool) -> void:
	model.set_hold(on)
	_paint_toggles()


func set_pip(on: bool) -> void:
	pip = on
	set_view(view)
	_paint_toggles()


func reset() -> void:
	model.place(true)
	follow = true
	_paint_toggles()


func apply_pose(name: String, snap := false) -> void:
	last_pose = name
	bew.apply(bew.pose(name))
	if snap:
		model.place(true)
	_sync_servo_sliders()


func set_gravity(g: float) -> void:
	gravity = clampf(g, 0.0, 30.0)
	if model != null and model.space_rid.is_valid():
		PhysicsServer3D.area_set_param(model.space_rid, PhysicsServer3D.AREA_PARAM_GRAVITY, gravity)


func set_shape(key: String, v: float) -> void:
	model.set_param(key, v)
	if key in ["reibung"]:
		for b in model.bodies:
			((b["rb"] as RigidBody3D).physics_material_override as PhysicsMaterial).friction = float(model.p["reibung"])
	elif key in ["moment_koerper", "moment_bein", "tempo_servo"]:
		pass                                         # read every physics step
	else:
		_rebuild_t = 0.4                             # build again when the slider rests
	_refresh_form_info()


# ---- Bedienfeld -----------------------------------------------------------------------------------------------------------
func _build_ui() -> void:
	win = Control.new()
	win.set_anchors_preset(Control.PRESET_FULL_RECT)
	win.theme = main.ui_root.theme if main != null and main.ui_root != null else UI.theme()
	layer.add_child(win)
	var bg := ColorRect.new()
	bg.color = UI.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	win.add_child(bg)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.add_theme_constant_override("separation", 0)
	win.add_child(row)
	# 3D view (the overlays are siblings above the container)
	var area := Control.new()
	area.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(area)
	_w["area"] = area
	vpc = SubViewportContainer.new()
	vpc.stretch = true
	vpc.set_anchors_preset(Control.PRESET_FULL_RECT)
	vpc.mouse_filter = Control.MOUSE_FILTER_STOP
	vpc.gui_input.connect(_view_input)
	vpc.set_meta("rad_zoom", "roboter")
	area.add_child(vpc)
	vpc.add_child(vp)
	_overlay(area)
	# panel
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(PANEL_W, 0)
	panel.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.LINE, 0, 10, 1))
	row.add_child(panel)
	_w["panel"] = panel
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	panel.add_child(pv)
	var hd := HBoxContainer.new()
	pv.add_child(hd)
	var tl := Label.new()
	tl.text = T.t("Roboter-Labor")
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.tooltip_text = T.t("Schliessen (Esc)")
	x.pressed.connect(close)
	hd.add_child(x)
	var sub := UI.small(T.t("Segment-Roboter – Form, Gelenke und Physik ausprobieren"))
	pv.add_child(sub)
	var tabs := HFlowContainer.new()
	tabs.add_theme_constant_override("h_separation", 4)
	tabs.add_theme_constant_override("v_separation", 4)
	pv.add_child(tabs)
	for tb in TABS:
		var b := Button.new()
		b.text = T.t(tb[1])
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(set_tab.bind(tb[0]))
		tabs.add_child(b)
		_w["tab_" + tb[0]] = b
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.set_meta("rad_scroll", true)
	pv.add_child(sc)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 8)
	sc.add_child(body)
	for tb in TABS:
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 6)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		body.add_child(v)
		_w["page_" + tb[0]] = v
	_page_form(_w["page_form"])
	_page_gelenke(_w["page_gelenke"])
	_page_posen(_w["page_posen"])
	_page_physik(_w["page_physik"])
	_page_ansicht(_w["page_ansicht"])
	var keys := UI.small(T.t("1 frei · 2 Seite · 3 oben · 4 Roboter-Kamera · R neu aufstellen · P anhalten · F festhalten · K Kamerabild · H Bedienfeld · Esc schliessen"))
	pv.add_child(keys)


func _overlay(area: Control) -> void:
	var st := Label.new()
	st.position = Vector2(14, 10)
	st.add_theme_font_size_override("font_size", 14)
	st.add_theme_color_override("font_color", Color("#16202c"))
	st.add_theme_color_override("font_outline_color", Color(1, 1, 1, 0.85))
	st.add_theme_constant_override("outline_size", 6)
	st.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(st)
	_w["status"] = st
	var vb := HBoxContainer.new()
	vb.add_theme_constant_override("separation", 4)
	vb.anchor_top = 1.0
	vb.anchor_bottom = 1.0
	vb.offset_left = 14
	vb.offset_top = -50
	vb.offset_bottom = -12
	area.add_child(vb)
	_w["viewbar"] = vb
	for v in VIEWS:
		var b := Button.new()
		b.text = T.t(v[1])
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(set_view.bind(v[0]))
		vb.add_child(b)
		_w["view_" + v[0]] = b
	var hint := UI.small(T.t("ziehen = drehen · rechts ziehen = verschieben · Rad = zoomen"), Color("#2a3644"))
	hint.autowrap_mode = TextServer.AUTOWRAP_OFF
	vb.add_child(hint)
	# the picture of the front camera (small, bottom right of the view)
	pip_vp = SubViewport.new()
	pip_vp.size = Vector2i(320, 200)
	pip_vp.world_3d = vp.find_world_3d()
	pip_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	pip_cam = Camera3D.new()
	pip_cam.fov = 70.0
	pip_cam.near = 0.01
	pip_cam.current = true
	pip_vp.add_child(pip_cam)
	add_child_pip()
	var box := PanelContainer.new()
	box.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ACC, 8, 4, 2))
	box.anchor_left = 1.0
	box.anchor_right = 1.0
	box.anchor_top = 1.0
	box.anchor_bottom = 1.0
	box.offset_left = -344
	box.offset_right = -14
	box.offset_top = -262
	box.offset_bottom = -60
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(box)
	var bv := VBoxContainer.new()
	box.add_child(bv)
	var cl := UI.small(T.t("Roboter-Kamera"), UI.TXT)
	bv.add_child(cl)
	var tr := TextureRect.new()
	tr.texture = pip_vp.get_texture()
	tr.custom_minimum_size = Vector2(320, 200)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bv.add_child(tr)
	pip_box = box


func add_child_pip() -> void:
	layer.add_child(pip_vp)                          # not inside a container: it renders by itself


func set_tab(t: String) -> void:
	tab = t if t in TABS.map(func(x): return x[0]) else "form"
	for tb in TABS:
		var pg: Control = _w.get("page_" + tb[0])
		if pg != null:
			pg.visible = tb[0] == tab
		var b: Button = _w.get("tab_" + tb[0])
		if b != null:
			_paint_btn(b, tb[0] == tab)
	_sync_servo_sliders()


func _paint_btn(b: Button, on: bool) -> void:
	for st in ["normal", "hover", "pressed", "focus"]:
		b.add_theme_stylebox_override(st, UI.box(UI.ACC if on else UI.FIELD, UI.ACC if on else UI.LINE, 8, 6, 1))
	b.add_theme_color_override("font_color", Color.WHITE if on else UI.TXT)


func _slider(parent: Control, title: String, lo: float, hi: float, stp: float, val: float, unit: String, cb: Callable) -> Dictionary:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	parent.add_child(v)
	var h := HBoxContainer.new()
	v.add_child(h)
	var l := Label.new()
	l.text = title
	l.add_theme_font_size_override("font_size", 13)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.clip_text = true
	h.add_child(l)
	var vl := Label.new()
	vl.add_theme_font_size_override("font_size", 13)
	vl.add_theme_color_override("font_color", UI.MUT)
	h.add_child(vl)
	var sl := HSlider.new()
	sl.min_value = lo
	sl.max_value = hi
	sl.step = stp
	sl.value = val
	sl.focus_mode = Control.FOCUS_NONE
	v.add_child(sl)
	var fmt := func(x: float) -> String:
		if stp >= 1.0:
			return "%d %s" % [int(round(x)), unit]
		return ("%.3f %s" if stp < 0.01 else "%.2f %s") % [x, unit]
	vl.text = fmt.call(val).strip_edges()
	sl.value_changed.connect(func(x: float):
		vl.text = fmt.call(x).strip_edges()
		cb.call(x))
	return {"sl": sl, "val": vl, "box": v, "fmt": fmt, "title": l}


func _toggle(parent: Control, title: String, on: bool, cb: Callable) -> CheckButton:
	var c := CheckButton.new()
	c.text = title
	c.button_pressed = on
	c.focus_mode = Control.FOCUS_NONE
	c.toggled.connect(cb)
	parent.add_child(c)
	return c


func _button(parent: Control, title: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = title
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(cb)
	if primary:
		UI.primary(b)
	parent.add_child(b)
	return b


func _page_form(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Startwerte aus modell.json (Einheiten der Vorlage, «E»). Nach einer Änderung baut das Labor den Roboter neu auf.")))
	for f in FORM:
		var g: Array = MODELL.GRENZEN[f[0]]
		var key: String = f[0]
		_w["form_" + key] = _slider(pg, T.t(f[1]), g[0], g[1], f[3], float(model.p[key]), f[2], func(x: float): set_shape(key, x))
	var info := UI.small("", UI.TXT)
	pg.add_child(info)
	_w["form_info"] = info
	_button(pg, T.t("Startwerte (modell.json)"), func():
		for k in MODELL.START:
			model.p[k] = MODELL.START[k]
		for f in FORM:
			(_w["form_" + f[0]]["sl"] as HSlider).set_value_no_signal(float(model.p[f[0]]))
			(_w["form_" + f[0]]["val"] as Label).text = (_w["form_" + f[0]]["fmt"] as Callable).call(float(model.p[f[0]])).strip_edges()
		_rebuild(true)
		_refresh_form_info())
	_refresh_form_info()


func _refresh_form_info() -> void:
	var l: Label = _w.get("form_info")
	if l == null or model == null:
		return
	var N: int = model.n()
	var length: float = model.pitch_len() * N
	var legs: float = model.u("oberschenkel") + model.u("unterschenkel")
	var mass: float = float(model.p["masse_segment"]) * N + float(model.p["masse_bein"]) * 2 * N
	l.text = T.t("Länge %.2f m · Breite %.2f m · Bein %.2f m · Masse %.2f kg · %d Antriebe") % [length, model.u("halbe_breite") * 2,
			legs, mass, model.actuator_count()]


func _page_gelenke(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Jedes Gelenk von Hand: Soll (Regler) und Ist (Zahl rechts). Rot = Servo überlastet.")))
	_w["servo_box"] = pg


func _fill_servo_sliders() -> void:
	var pg: VBoxContainer = _w.get("servo_box")
	if pg == null:
		return
	for c in pg.get_children():
		if c.has_meta("servo_ui"):
			pg.remove_child(c)
			c.queue_free()
	_sl = {}
	var top := VBoxContainer.new()
	top.set_meta("servo_ui", true)
	pg.add_child(top)
	_servo_slider(top, "pan", T.t("Kamera schwenken"))
	var lt := _toggle(top, T.t("Riegel darf schliessen (Ring)"), model.latch_wanted, func(on: bool):
		model.latch_wanted = on)
	_w["latch_ok"] = lt
	var N: int = model.n()
	for i in range(N - 1):
		var b := UI.sub_fold(pg, T.t("Segmentgelenk %d (zwischen Segment %d und %d)") % [i + 1, i + 1, i + 2], i == 0)
		(b.get_meta("wrap") as Control).set_meta("servo_ui", true)
		_servo_slider(b, "sp%d" % i, T.t("hoch / runter"))
		_servo_slider(b, "sy%d" % i, T.t("links / rechts"))
	for i in range(N):
		var b := UI.sub_fold(pg, T.t("Beine an Segment %d") % (i + 1), false)
		(b.get_meta("wrap") as Control).set_meta("servo_ui", true)
		for sd in ["l", "r"]:
			var side := T.t("links") if sd == "l" else T.t("rechts")
			_servo_slider(b, "hy%d%s" % [i, sd], "%s · %s" % [side, T.t("Hüfte vor / zurück")])
			_servo_slider(b, "hp%d%s" % [i, sd], "%s · %s" % [side, T.t("Hüfte hoch / runter")])
			_servo_slider(b, "kn%d%s" % [i, sd], "%s · %s" % [side, T.t("Knie")])


func _servo_slider(parent: Control, id: String, title: String) -> void:
	var si: int = model.servo_index(id)
	if si < 0:
		return
	var sv: Dictionary = model.servos[si]
	var d := _slider(parent, title, float(sv["min"]), float(sv["max"]), 1.0, float(sv["target"]), "°", func(x: float):
		model.set_target(id, x)
		last_pose = "")
	_sl[id] = d


func _sync_servo_sliders() -> void:
	if model == null:
		return
	for id in _sl:
		var si: int = model.servo_index(id)
		if si >= 0:
			(_sl[id]["sl"] as HSlider).set_value_no_signal(float(model.servos[si]["target"]))


func _page_posen(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Fertige Posen: die Servos fahren mit ihrem Tempo hin (die Physik rechnet mit). «Sofort» setzt den Roboter ohne Weg in die Pose.")))
	var snap := CheckButton.new()
	snap.text = T.t("Sofort (ohne Weg)")
	snap.focus_mode = Control.FOCUS_NONE
	var gr := GridContainer.new()
	gr.columns = 2
	gr.add_theme_constant_override("h_separation", 6)
	gr.add_theme_constant_override("v_separation", 6)
	pg.add_child(gr)
	for ps in BEWEGUNG.POSEN:
		var pname: String = ps[0]
		var b := _button(gr, T.t(ps[1]), func(): apply_pose(pname, snap.button_pressed))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pg.add_child(snap)
	_w["snap"] = snap
	_slider(pg, T.t("Körperhöhe über dem Boden"), 0.3, 1.8, 0.05, bew.hoehe, "E", func(x: float):
		bew.hoehe = x
		if last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			apply_pose(last_pose))
	_slider(pg, T.t("Füsse seitlich"), 0.3, 2.0, 0.05, bew.spreiz, "E", func(x: float):
		bew.spreiz = x
		if last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			apply_pose(last_pose))
	_button(pg, T.t("Neu aufstellen (R)"), reset)


func _page_physik(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Schwerkraft, Reibung und Servo-Grenzen. Die Servos halten höchstens ihr Moment – mehr Last = sie geben nach (rot).")))
	_slider(pg, T.t("Schwerkraft"), 0.0, 20.0, 0.1, gravity, "m/s²", set_gravity)
	for f in PHYSIK:
		var g: Array = MODELL.GRENZEN[f[0]]
		var key: String = f[0]
		_slider(pg, T.t(f[1]), g[0], g[1], f[3], float(model.p[key]), f[2], func(x: float): set_shape(key, x))
	_w["t_pause"] = _toggle(pg, T.t("Physik anhalten (P)"), paused, set_paused)
	_w["t_hold"] = _toggle(pg, T.t("Festhalten: mittleres Segment in der Luft (F)"), false, set_hold)
	var info := UI.small("", UI.TXT)
	pg.add_child(info)
	_w["phys_info"] = info


func _page_ansicht(pg: VBoxContainer) -> void:
	var gr := GridContainer.new()
	gr.columns = 2
	gr.add_theme_constant_override("h_separation", 6)
	gr.add_theme_constant_override("v_separation", 6)
	pg.add_child(gr)
	for v in VIEWS:
		var b := _button(gr, T.t(v[1]), set_view.bind(v[0]))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_w["t_pip"] = _toggle(pg, T.t("Kamerabild klein einblenden (K)"), pip, set_pip)
	_w["t_follow"] = _toggle(pg, T.t("Ansicht folgt dem Roboter"), follow, func(on: bool):
		follow = on)
	pg.add_child(UI.small(T.t("Rot = Teile des Roboters, die sich berühren oder durchdringen (z. B. Knie am Körper).")))


func _paint_toggles() -> void:
	for k in [["t_pause", paused], ["t_hold", model != null and model.hold], ["t_pip", pip], ["t_follow", follow]]:
		var c: CheckButton = _w.get(k[0])
		if c != null:
			c.set_pressed_no_signal(bool(k[1]))


func _refresh() -> void:
	if model == null or not model.built_ok:
		return
	var lstate := {"open": T.t("Kupplung offen"), "grip": T.t("Kupplung greift"), "locked": T.t("Ring verriegelt")}
	var red: int = model.collide.size()
	var over: Array = model.overloaded()
	var lines := [T.t("Roboter-Labor") + " · " + (T.t("Physik angehalten") if paused else T.t("Physik läuft")) + (" · " + T.t("festgehalten") if model.hold else ""),
			str(lstate.get(model.latch["state"], "")) + " · " + (T.t("%d Teile berühren sich (rot)") % red if red > 0 else T.t("keine Kollision")),
			T.t("Servos: %d · überlastet: %d · Strom ca. %.1f A") % [model.actuator_count(), over.size(), model.total_current]]
	(_w["status"] as Label).text = "\n".join(lines)
	var pi: Label = _w.get("phys_info")
	if pi != null and pi.is_visible_in_tree():
		var c: Vector3 = model.com()
		pi.text = T.t("Masse %.2f kg · Schwerpunkt %.0f cm über dem Boden · Strom ca. %.1f A") % [model.total_mass, c.y * 100.0, model.total_current] \
				+ ("\n" + T.t("Überlastet: %s") % ", ".join(over) if not over.is_empty() else "")
	if tab == "gelenke":
		for id in _sl:
			var si: int = model.servo_index(id)
			if si < 0:
				continue
			var sv: Dictionary = model.servos[si]
			var d: Dictionary = _sl[id]
			(d["val"] as Label).text = "%d° · %d°" % [int(round(sv["target"])), int(round(sv["angle"]))]
			(d["val"] as Label).add_theme_color_override("font_color", UI.RED if float(sv["load"]) > 1.0 else (UI.ORG if float(sv["load"]) > 0.7 else UI.MUT))


# ---- /control «roboter» -----------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var d := {"ok": true, "open": is_open()}
	if is_open() and model != null and model.built_ok:
		d.merge({"segments": model.n(), "servos": model.servos.size(), "actuators": model.actuator_count(), "view": view, "tab": tab,
				"paused": paused, "hold": model.hold, "latch": model.latch["state"], "com": [model.com().x, model.com().y, model.com().z],
				"mass": model.total_mass, "current": model.total_current, "overloaded": model.overloaded(),
				"collide": model.colliding_names(), "pose": last_pose, "ticks": Engine.physics_ticks_per_second})
	return d


func control(d: Dictionary) -> Dictionary:
	var do := str(d.get("do", "info"))
	if do == "open":
		open()
	elif do == "close":
		close()
		return info()
	if not is_open():
		return info() if do == "info" else {"ok": false, "error": "not open"}
	match do:
		"pose":
			apply_pose(str(d.get("name", "gerade")), bool(d.get("snap", false)))
		"set":
			model.set_target(str(d.get("id", "")), float(d.get("value", 0.0)))
			_sync_servo_sliders()
		"param":
			set_shape(str(d.get("key", "")), float(d.get("value", 0.0)))
		"view":
			set_view(str(d.get("value", "frei")))
		"pause":
			set_paused(bool(d.get("on", true)))
		"reset":
			reset()
		"hold":
			set_hold(bool(d.get("on", true)))
		"tab":
			set_tab(str(d.get("value", "form")))
		"pip":
			set_pip(bool(d.get("on", true)))
	return info()
