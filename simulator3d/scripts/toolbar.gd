extends PanelContainer
## 3D-3.61: the tool bar at the bottom of the simulator window - everything of «Erkunden», «Patrouille» and the view
## with the mouse only. 3D-4.13 (wish of Daniel 30.10.2026): a «Symbol-Dock» - round drawn symbols (no emoji font needed):
##   Erkunden · Rover ▴ (route) · Folgen · Kopf · Versetzen · Stange ▴ · Mitspieler · Ansicht ▴ · Menü · ?
## Hover (or the focus of the controller, padmap.gd): the symbol grows and its name slides out; an active function has a
## gently pulsing green ring; the groups (Rover, Stange, Ansicht) slide a small menu up on hover / click / A. «Ansicht» has
## the old camera row of the window too (Frei, Kamera 1 / 2, Wärmebild, Karte, Livebild, Zum Kopf, Von oben) - main.view_bar
## stays as the keeper of the states and shows itself only when the dock is hidden (kids mode, building kit, game at the PC).
## «?» opens the mouse help of the view on hover. Light on the CPU: tweens only on hover, the state is read 3 times a second.

var main
var folded := false                    # (kept for older calls - the dock does not fold any more)
var _row: HBoxContainer
var _items := {}                       # id -> DockBtn
var _labels := {}                      # id -> Label (slides out)
var _t := 0.0
var _hint: PanelContainer              # 3D-3.66: while setting points / the area: what to do and «Fertig»
var _hint_l: Label
var _sub: PanelContainer               # the open group menu
var _sub_box: VBoxContainer
var _sub_for := ""
var _sub_btns := {}                    # id -> Button of the open menu
var _mast_sl: HSlider                  # 3D-4.x: «Stange» - the height with the mouse (live)
var _mast_l: Label
var _sub_out_t := 0.0
var _help: PanelContainer
var _st := {}

const UI = preload("res://scripts/ui_style.gd")
const ON := Color(0.45, 0.95, 0.55)
const OFF := Color(0.85, 0.88, 0.92)

# [id, symbol, name, tooltip (shortcut · one sentence), [ids of the group menu]]
const DOCK := [["explore", "compass", "Erkunden", "Start (Controller) · mit dem Rover herumfahren – Tastatur, Maus, Touch oder Controller", []],
		["rover", "track", "Rover", "Rover-Route: Punkte setzen, Bereich, Zufall – der Mover fährt MoveEye ab", ["patrol", "points", "area", "random", "clear", "route"]],
		["follow", "target", "Folgen", "Y (Controller) · der Kopf hält Personen, Tiere und Bewegtes in der Bildmitte", []],
		["head", "pad", "Kopf", "L ◉ (Controller) · den Kopf von MoveEye drehen, Licht ein / aus", []],
		["place", "move", "Versetzen", "Strg + Klick beim Erkunden · den Rover an eine andere Stelle setzen", []],
		["mast", "ruler", "Stange", "Bild ↑ / ↓ beim Erkunden · Höhe des Kamerakopfs", ["mast_up", "mast_dn"]],
		["invite", "people", "Mitspieler", "J beim Erkunden · QR-Code: Mitspieler mit dem Handy, frei bewegen", []],
		["view", "lens", "Ansicht", "0 – 3, M, L · Kameras, Karte, Livebild und was angezeigt wird", ["v0", "v1", "v2", "v3", "map", "live", "to_head", "to_top", "exview", "spectate", "cams", "info", "laser", "zones3d", "det3d"]],
		["panel", "menu", "Menü", "H · das Bedienfeld rechts ein / aus", []],
		["help", "help", "Hilfe", "Maus und Tasten in der Ansicht", []]]

const NAMES := {"patrol": ["Rover-Route starten", "Der Mover fährt MoveEye die Route ab, MoveEye passt die ganze Zeit auf"],
		"points": ["Punkte setzen", "In die Welt klicken = Punkt, Rechtsklick auf einen Punkt = weg"],
		"area": ["Bereich aufziehen", "Der Mover fährt zufällige Punkte darin ab"],
		"random": ["Zufällige Route", "Zufällige Route rund um MoveEye"],
		"clear": ["Route löschen", "Route und Bereich löschen"],
		"route": ["Route anzeigen", "Route und Bereich in der Welt zeigen"],
		"mast_up": ["Stange + (höher)", "Kamerakopf 10 cm höher"], "mast_dn": ["Stange − (tiefer)", "Kamerakopf 10 cm tiefer"],  # + slider (_mast_row)
		"v0": ["Frei (0)", "Frei herumfliegen"], "v1": ["Kamera 1 (1)", "Durch die Kopfkamera schauen"],
		"v2": ["Kamera 2 (2)", "Durch die zweite Kamera schauen"], "v3": ["Wärmebild (3)", "Das Wärmebild gross"],
		"map": ["Karte (M)", "Übersichtskarte oben links"], "live": ["Livebild (L)", "Livebild einer Kamera unter der Karte"],
		"to_head": ["Zum Kopf", "Zurück zu MoveEye"], "to_top": ["Von oben", "Von oben auf den Platz schauen"],
		"exview": ["Rover-Ansicht (V)", "Erkunden: hinterher, Fahrersicht, von oben"],
		"spectate": ["Beobachter (C)", "Wechselnde Kamera-Einstellungen von Rover und Spielern"],
		"cams": ["Kamerabilder", "Was MoveEye sieht (im Bedienfeld)"], "info": ["Info oben", "Anzeige oben (Steuerung, Tempo, Stange)"],
		"laser": ["Blickrichtung", "Roter Strahl: wohin die Kamera von MoveEye schaut (nur für dich sichtbar)"],
		"zones3d": ["Zonen in 3D", "Die Zonen von MoveEye auf dem Boden (nur für dich sichtbar)"],
		"det3d": ["Erkennung in 3D", "Rahmen von MoveEye über den Figuren: grün erkannt, rot Fehlalarm, orange übersehen"]}


func _ready() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.09, 0.78)
	sb.set_corner_radius_all(30)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 5
	sb.content_margin_bottom = 5
	sb.border_color = Color(1, 1, 1, 0.12)
	sb.set_border_width_all(1)
	sb.shadow_color = Color(0, 0, 0, 0.35)
	sb.shadow_size = 8
	add_theme_stylebox_override("panel", sb)
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 2)
	add_child(_row)
	for d in DOCK:
		var id: String = d[0]
		var b := DockBtn.new()
		b.kind = d[1]
		b.tooltip_text = "%s – %s" % [d[2], d[3]]
		b.group = not (d[4] as Array).is_empty()
		b.focus_mode = Control.FOCUS_ALL
		b.pressed.connect(_press_item.bind(id))
		b.mouse_entered.connect(_hover.bind(id, true, true))
		b.mouse_exited.connect(_hover.bind(id, false, true))
		b.focus_entered.connect(_hover.bind(id, true, false))
		b.focus_exited.connect(_hover.bind(id, false, false))
		_row.add_child(b)
		_items[id] = b
		var l := Label.new()
		l.text = d[2] + (" ▴" if b.group else "")
		l.clip_text = true
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		l.add_theme_font_size_override("font_size", 13)
		l.add_theme_color_override("font_color", Color.WHITE)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		l.visible = false
		_row.add_child(l)
		_labels[id] = l
	# what to do while setting points / the area
	_hint = PanelContainer.new()
	_hint.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.9), Color(1.0, 0.85, 0.35, 0.6), 10, 6, 1))
	var hh := HBoxContainer.new()
	hh.add_theme_constant_override("separation", 8)
	_hint.add_child(hh)
	_hint_l = Label.new()
	_hint_l.add_theme_font_size_override("font_size", 12)
	_hint_l.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
	hh.add_child(_hint_l)
	var done := Button.new()
	done.text = "✓ Fertig (Esc)"
	done.tooltip_text = "Keine Punkte mehr setzen – die Maus bewegt wieder nur die Ansicht"
	done.add_theme_font_size_override("font_size", 12)
	done.pressed.connect(func(): main.patrol.edit = ""; main.patrol._click_at = null; _paint())
	hh.add_child(done)
	_hint.visible = false
	# the group menu (slides up) and the help «?»
	_sub = PanelContainer.new()
	_sub.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.94), Color(1, 1, 1, 0.14), 14, 8, 1))
	_sub_box = VBoxContainer.new()
	_sub_box.add_theme_constant_override("separation", 2)
	_sub.add_child(_sub_box)
	_sub.visible = false
	_help = PanelContainer.new()
	_help.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.94), Color(1, 1, 1, 0.14), 12, 10, 1))
	_help.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var hl := Label.new()
	hl.add_theme_font_size_override("font_size", 12)
	hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hl.custom_minimum_size = Vector2(380, 0)
	_help.add_child(hl)
	_help.visible = false
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	call_deferred("_add_popups")


func _add_popups() -> void:
	for c in [_hint, _sub, _help]:
		c.theme = theme if theme != null else main.ui_root.theme
		get_parent().add_child(c)


func set_folded(v: bool) -> void:
	folded = v


# ---- hover: the symbol grows, the name slides out (a tween only now) -----------------------------------------------------------
func _hover(id: String, on: bool, mouse: bool) -> void:
	var b: DockBtn = _items[id]
	if not on:
		on = (b.has_focus() and mouse) or (b.is_hovered() and not mouse)   # the other one still holds it
	b.hover_to(on)
	var l: Label = _labels[id]
	var w: float = l.get_theme_font("font").get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x + 8.0 if on else 0.0
	if on:
		l.visible = true
	var tw := l.create_tween()
	tw.tween_property(l, "custom_minimum_size:x", w, 0.16).set_trans(Tween.TRANS_SINE)
	if not on:
		tw.tween_callback(func(): if l.custom_minimum_size.x < 1.0: l.visible = false)
	if on and b.group and mouse:
		_open_sub(id, false)
	if id == "help" and (mouse or not on):
		_help.visible = on
		if on:
			(_help.get_child(0) as Label).text = _help_text()
			_help.reset_size()


func _help_text() -> String:
	var t := "Ansicht mit der Maus: links ziehen = verschieben · rechts ziehen = drehen · Rad = zoomen · Doppelklick = hinfliegen\nTasten: 0 frei · 1 / 2 Kameras · 3 Wärmebild · M Karte · L Livebild · H Bedienfeld · Esc Punkte fertig"
	if main.padmap != null:
		t += "\nController: " + main.padmap.help_line("sim", ["head", "drive", "orbit", "view", "swap", "menu"])
	return t


func _press_item(id: String) -> void:
	var d := _dock(id)
	if not (d[4] as Array).is_empty():
		if _sub.visible and _sub_for == id and not (_items[id] as Control).has_focus():
			_close_sub(false)
		else:
			_sub_for = "" if _sub_for == id and _sub.visible and (_items[id] as Control).has_focus() else _sub_for
			_open_sub(id, (_items[id] as Control).has_focus())
		return
	if id == "help":
		_help.visible = not _help.visible
		(_help.get_child(0) as Label).text = _help_text()
		_help.reset_size()
		return
	_press(id)


func _dock(id: String) -> Array:
	for d in DOCK:
		if d[0] == id:
			return d
	return []


# ---- the group menu: slides up above its symbol -----------------------------------------------------------------------------
func _open_sub(id: String, focus: bool) -> void:
	_sub_out_t = 0.35
	if not (_sub.visible and _sub_for == id):
		_sub_for = id
		for c in _sub_box.get_children():
			c.queue_free()
		_sub_btns = {}
		for k in _dock(id)[4]:
			var b := Button.new()
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.flat = true
			b.add_theme_font_size_override("font_size", 13)
			b.custom_minimum_size = Vector2(220, 30)
			b.tooltip_text = NAMES[k][1]
			b.pressed.connect(func(): _press(k); _paint_sub())
			b.set_meta("pad_back", func(): _close_sub(true))           # B of the controller (padmap.gd)
			_sub_box.add_child(b)
			_sub_btns[k] = b
		_mast_sl = null
		if id == "mast":
			_mast_row()
		_paint_sub()
		_sub.visible = true
		_sub.reset_size()
		var ib: Control = _items[id]
		var x: float = ib.global_position.x + ib.size.x / 2.0 - _sub.size.x / 2.0
		var y: float = global_position.y - _sub.size.y - 6.0
		_sub.position = Vector2(clampf(x, 4.0, get_viewport_rect().size.x - _sub.size.x - 4.0), y + 12.0)
		_sub.modulate.a = 0.0
		var tw := _sub.create_tween().set_parallel(true)
		tw.tween_property(_sub, "position:y", y, 0.16).set_trans(Tween.TRANS_SINE)
		tw.tween_property(_sub, "modulate:a", 1.0, 0.16)
	if focus and not _sub_btns.is_empty():
		(_sub_btns.values()[0] as Button).grab_focus.call_deferred()


func _mast_row() -> void:
	"""3D-4.x (wish of Daniel): a slider for the height of the pole - drag with the mouse (or ◀ ▶ of the controller), the
	head moves along live; the value in m. Limits = main.MAST_MIN … MAST_MAX (like set_mast and the page of MoveEye)."""
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	_mast_l = Label.new()
	_mast_l.add_theme_font_size_override("font_size", 13)
	_mast_l.add_theme_color_override("font_color", Color.WHITE)
	box.add_child(_mast_l)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	for tx in ["%.1f" % main.MAST_MIN, "", "%.1f m" % main.MAST_MAX]:
		if tx == "":
			_mast_sl = HSlider.new()
			_mast_sl.min_value = main.MAST_MIN
			_mast_sl.max_value = main.MAST_MAX
			_mast_sl.step = 0.05
			_mast_sl.value = main.mast_h
			_mast_sl.custom_minimum_size = Vector2(170, 26)
			_mast_sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_mast_sl.focus_mode = Control.FOCUS_ALL
			_mast_sl.tooltip_text = "Höhe des Kamerakopfs: ziehen (oder ◀ ▶ am Controller)"
			_mast_sl.value_changed.connect(func(v: float):
				main.set_mast(v)
				main._settings_dirty = true
				_mast_text())
			_mast_sl.set_meta("pad_back", func(): _close_sub(true))
			row.add_child(_mast_sl)
		else:
			var l := Label.new()
			l.text = tx
			l.add_theme_font_size_override("font_size", 11)
			l.add_theme_color_override("font_color", OFF)
			row.add_child(l)
	box.add_child(row)
	_sub_box.add_child(box)
	_mast_text()


func _mast_text() -> void:
	if _mast_l != null and is_instance_valid(_mast_l):
		_mast_l.text = "Höhe: %.2f m" % main.mast_h


func _close_sub(refocus: bool) -> void:
	var id := _sub_for
	_sub.visible = false
	_sub_for = ""
	if refocus and _items.has(id):
		(_items[id] as Control).grab_focus()


func _paint_sub() -> void:
	_paint()
	if _mast_sl != null and is_instance_valid(_mast_sl) and absf(_mast_sl.value - main.mast_h) > 0.001 and not _mast_sl.has_focus():
		_mast_sl.set_value_no_signal(main.mast_h)       # changed elsewhere (Bild ↑↓, L2 + ✚, the page of MoveEye)
		_mast_text()
	elif _mast_sl != null and is_instance_valid(_mast_sl):
		_mast_text()
	for k in _sub_btns:
		var b: Button = _sub_btns[k]
		var on := bool(_st.get(k, false))
		var tx: String = NAMES[k][0]
		if k == "patrol":
			tx = "Rover-Route stoppen" if main.patrol.active else "Rover-Route starten"
		b.text = ("●  " if on else "○  ") + tx
		b.add_theme_color_override("font_color", ON if on else OFF)
		b.add_theme_color_override("font_focus_color", ON if on else Color.WHITE)


# ---- the functions (as before) --------------------------------------------------------------------------------------------------
func _press(id: String) -> void:
	var ex = main.explore
	var pt = main.patrol
	if id in ["points", "area", "random", "clear"]:
		pt.guard = {}                                   # 3D-3.76: a route by hand - no guarded place
	match id:
		"explore":
			ex.set_on(not ex.on)
		"patrol":
			if pt.active:
				pt.set_active(false)
			else:
				pt.ask()                                     # 3D-3.76: first: what shall be guarded?
		"points":
			pt.edit = "" if pt.edit == "points" else "points"
			pt.mode = "points"
			pt._dirty = true
		"area":
			pt.edit = "" if pt.edit == "area" else "area"
		"random":
			pt.random_route()
		"clear":
			pt.clear_route()
		"follow":                                    # 3D-3.91: one mode with «Folgen» of MoveEye
			var on_: bool = not (main.mw_follow_on() if main.now() - main.mw_t < 3.0 else pt.follow)
			pt.follow = on_
			if main.now() - main.mw_t < 3.0:
				main.mw_track(on_)
			else:
				main.start_info = "Folgen braucht MoveEye – zuerst verbinden (bis dahin dreht nur die Patrouille zu Verdächtigem)"
		"place":
			main.place_kind = "" if main.place_kind == "rover" else "rover"
		"head":
			main.headpad.toggle()
		"mast_dn":
			main.set_mast(main.mast_h - 0.1)
		"mast_up":
			main.set_mast(main.mast_h + 0.1)
		"view", "exview":
			if not ex.on:
				ex.set_on(true)
			ex.next_view()
		"v0", "v1", "v2", "v3":
			if ex.on:
				ex.set_on(false)
			main.set_view(int(id.substr(1)))
		"to_head", "to_top":
			if ex.on:
				ex.set_on(false)
			main._view_preset("head" if id == "to_head" else "top")
		"live":
			main.set_live(not main.live_on)
		"spectate":
			ex.spectator(not main.spectate)
		"invite":
			ex.set_invite(not ex.invite.visible)
		"route":
			pt.show_route = not pt.show_route
		"map":
			main.set_map(not main.map_on)
		"cams":
			if main.cam_card != null:
				main.cam_card.visible = not main.cam_card.visible
		"info":
			ex.info_hidden = not ex.info_hidden
		"laser":                                     # 3D-3.96: the direction MoveEye looks (beginners)
			main.show_laser = not main.show_laser
		"zones3d":
			main.show_zones3d = not main.show_zones3d
		"det3d":
			main.show_det3d = not main.show_det3d
		"panel":
			main.show_panel(not main.ui_root.visible)
		"templates":
			main.templates.toggle()
		"inventar":
			main.inventar.toggle()
	main._settings_dirty = true
	_paint()


func _paint() -> void:
	var ex = main.explore
	var pt = main.patrol
	var vm: int = main.view_mode
	var st := {"explore": ex.on, "patrol": pt.active, "points": pt.edit == "points", "area": pt.edit == "area" or (pt.mode == "area" and pt.area.size.x > 0.5),
			"follow": main.mw_follow_on() if main.now() - main.mw_t < 3.0 else pt.follow, "place": main.place_kind == "rover", "spectate": main.spectate, "invite": ex.invite != null and ex.invite.visible,
			"route": pt.show_route, "map": main.map_on, "cams": main.cam_card != null and main.cam_card.visible, "info": not ex.info_hidden, "laser": main.show_laser, "zones3d": main.show_zones3d, "det3d": main.show_det3d,
			"panel": main.ui_root.visible, "exview": ex.on, "head": main.headpad != null and main.headpad.visible,
			"v0": vm == 0 and not ex.on, "v1": vm == 1, "v2": vm == 2, "v3": vm == 3, "live": main.live_on,
			"templates": main.templates != null and main.templates.visible, "inventar": main.inventar != null and main.inventar.visible}
	st["rover"] = st["patrol"] or st["points"] or st["area"]
	st["view"] = vm != 0 or main.spectate
	st["mast"] = false
	_st = st
	for k in _items:
		(_items[k] as DockBtn).set_active(bool(st.get(k, false)))
	var ed: String = pt.edit
	_hint.visible = ed != "" and visible
	if ed == "points":
		_hint_l.text = "Punkte setzen: klicken = Punkt · Rechtsklick auf einen Punkt = weg · Ziehen = Ansicht bewegen"
	elif ed == "area":
		_hint_l.text = "Bereich: mit gedrückter Maustaste aufziehen"
	if _labels.has("view"):
		(_labels["view"] as Label).text = ("Ansicht: " + str(ex.VIEW_NAMES.get(ex.view, ex.view)) if ex.on else ["Ansicht", "Kamera 1", "Kamera 2", "Wärmebild"][clampi(vm, 0, 3)]) + " ▴"
	if _labels.has("rover"):
		(_labels["rover"] as Label).text = ("Rover-Route: " + {"drive": "fährt", "look": "schaut"}.get(pt.state, "")) if pt.active else "Rover ▴"


func _process(dt: float) -> void:
	visible = not main.kids_on and not (main.home_editor != null and main.home_editor.visible) and not (main.localplay != null and main.localplay.active)   # 3D-3.69 / 3.73
	if main.view_bar != null and main.view_bar.visible == visible:
		main.view_bar.visible = not visible             # the old camera row only while the dock is hidden
	if not visible:
		_sub.visible = false
		_help.visible = false
		_hint.visible = false
		return
	# at the bottom in the middle of the view (left of the panel when it is shown)
	var vs: Vector2 = get_viewport_rect().size
	var right: float = vs.x
	if main.ui_root != null and main.ui_root.visible:
		right -= main.ui_root.size.x + 10.0
	size = get_combined_minimum_size()
	var extra := 0.0                                   # a name that slides out: the dock grows to the right, the symbols stay put
	for k in _labels:
		extra += (_labels[k] as Label).custom_minimum_size.x
	position = Vector2(max(8.0, (right - size.x + extra) / 2.0), vs.y - size.y - 12.0)
	if _hint.visible:
		_hint.reset_size()
		_hint.position = Vector2(max(8.0, (right - _hint.size.x) / 2.0), position.y - _hint.size.y - 8.0)
	if _help.visible:
		var hb: Control = _items["help"]
		_help.position = Vector2(clampf(hb.global_position.x - _help.size.x + hb.size.x, 4.0, vs.x - _help.size.x - 4.0), position.y - _help.size.y - 8.0)
	if _sub.visible:                                   # the menu goes when the mouse and the focus have left it
		var f := get_viewport().gui_get_focus_owner()
		var inside: bool = f != null and (_sub.is_ancestor_of(f) or f == _items.get(_sub_for))
		var mp := get_viewport().get_mouse_position()
		var over: bool = _sub.get_global_rect().grow(6.0).has_point(mp) or (_items[_sub_for] as DockBtn)._hov \
				or _sub_btns.values().any(func(x): return (x as Button).is_hovered())
		if over or inside:
			_sub_out_t = 0.35
		else:
			_sub_out_t -= dt
			if _sub_out_t <= 0.0:
				_close_sub(false)
	_t -= dt
	if _t <= 0.0:
		_t = 0.3
		_paint()
		if _sub.visible:
			_paint_sub()


func dock_state() -> Dictionary:
	"""for tests (control «padmap» do = dock)"""
	var fo := get_viewport().gui_get_focus_owner()
	return {"focus": _items.find_key(fo) if fo != null and _items.values().has(fo) else ("sub" if fo != null and _sub.is_ancestor_of(fo) else ""), "items": _items.keys(), "sub": _sub_for if _sub.visible else "", "sub_items": _sub_btns.keys(), "active": _items.keys().filter(func(k): return (_items[k] as DockBtn).active),
			"rect": [position.x, position.y, size.x, size.y], "view_bar": main.view_bar.visible if main.view_bar != null else null}


# ---- one round symbol of the dock ---------------------------------------------------------------------------------------------
class DockBtn extends Button:
	var kind := ""
	var group := false
	var active := false
	var s := 1.0                        # the size of the symbol (grows on hover)
	var glow := 0.0                     # the pulse of an active function
	var _hov := false
	var _tw: Tween
	var _pulse: Tween

	func _init() -> void:
		custom_minimum_size = Vector2(44, 44)
		flat = true
		var e := StyleBoxEmpty.new()
		for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
			add_theme_stylebox_override(st, e)

	func hover_to(on: bool) -> void:
		_hov = on
		if _tw != null:
			_tw.kill()
		_tw = create_tween()
		_tw.tween_method(func(v: float): s = v; queue_redraw(), s, 1.3 if on else 1.0, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	func set_active(on: bool) -> void:
		if on == active:
			return
		active = on
		if _pulse != null:
			_pulse.kill()
			_pulse = null
		glow = 0.0
		if on:                                         # gently: 1.6 s in and out, only while it is on
			_pulse = create_tween().set_loops()
			_pulse.tween_method(func(v: float): glow = v; queue_redraw(), 0.0, 1.0, 0.8).set_trans(Tween.TRANS_SINE)
			_pulse.tween_method(func(v: float): glow = v; queue_redraw(), 1.0, 0.0, 0.8).set_trans(Tween.TRANS_SINE)
		queue_redraw()

	func _draw() -> void:
		var c := size / 2.0
		var r := 19.0
		draw_circle(c, r, Color(1, 1, 1, 0.16 if _hov else 0.07))
		if active:
			draw_circle(c, r, Color(0.3, 0.9, 0.45, 0.14 + 0.1 * glow))
			draw_arc(c, r + 1.0 + glow * 1.5, 0.0, TAU, 40, Color(0.45, 0.95, 0.55, 0.55 + 0.35 * glow), 2.0, true)
		if has_focus():
			draw_arc(c, r + 3.0, 0.0, TAU, 40, Color(1.0, 0.83, 0.3), 2.5, true)
		var col: Color = Color(0.55, 1.0, 0.65) if active else (Color.WHITE if _hov else Color(0.85, 0.88, 0.92))
		set_meta("col", col)
		draw_set_transform(c - Vector2(10, 10) * s, 0.0, Vector2(s, s))
		_icon(col)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if group:                                      # a small «up» mark: there is a menu
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r - 1), c + Vector2(-3, -r + 3), c + Vector2(3, -r + 3)]), Color(1, 1, 1, 0.5))

	func _icon(col: Color) -> void:
		var c := Vector2(10, 10)
		var w := 1.8
		match kind:
			"compass":                                 # Erkunden
				draw_arc(c, 8.0, 0.0, TAU, 28, col, w, true)
				draw_colored_polygon(PackedVector2Array([c + Vector2(0, -6.5), c + Vector2(2.6, 0), c + Vector2(-2.6, 0)]), Color(1.0, 0.45, 0.4))
				draw_colored_polygon(PackedVector2Array([c + Vector2(0, 6.5), c + Vector2(2.6, 0), c + Vector2(-2.6, 0)]), col)
			"move":                                    # Versetzen: a cross of arrows
				for v in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
					draw_line(c, c + v * 6.5, col, w, true)
					var n := Vector2(-v.y, v.x)
					draw_colored_polygon(PackedVector2Array([c + v * 9.5, c + v * 6.0 + n * 3.0, c + v * 6.0 - n * 3.0]), col)
			"ruler":                                   # Stange: the pole with the head and a height arrow
				draw_line(c + Vector2(-2, 9), c + Vector2(-2, -5), col, 2.2, true)
				draw_rect(Rect2(c + Vector2(-6, -9), Vector2(8, 5)), col, false, w)
				draw_line(c + Vector2(5, -6), c + Vector2(5, 6), col, 1.4, true)
				draw_colored_polygon(PackedVector2Array([c + Vector2(5, -9), c + Vector2(7.5, -5), c + Vector2(2.5, -5)]), col)
				draw_colored_polygon(PackedVector2Array([c + Vector2(5, 9), c + Vector2(7.5, 5), c + Vector2(2.5, 5)]), col)
			"people":                                  # Mitspieler: two persons
				for dx in [-4.0, 4.5]:
					draw_arc(c + Vector2(dx, -4), 2.6, 0.0, TAU, 12, col, w, true)
					draw_arc(c + Vector2(dx, 8), 5.5, PI * 1.15, PI * 1.85, 10, col, w, true)
			"menu":                                    # ☰
				for dy in [-5.0, 0.0, 5.0]:
					draw_line(c + Vector2(-7, dy), c + Vector2(7, dy), col, 2.0, true)
			"help":
				draw_arc(c, 8.0, 0.0, TAU, 28, col, w, true)
				draw_string(ThemeDB.fallback_font, c + Vector2(-3.5, 5), "?", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col)
			_:
				UI._draw_group_icon(self, kind)     # track, target, pad, lens (ui_style.gd)
