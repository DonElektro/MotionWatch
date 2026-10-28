extends PanelContainer
## 3D-3.61: the tool bar at the bottom of the simulator window - everything of «Erkunden», «Patrouille» and the view
## with the mouse only (also on a PC with a keyboard). Green = on. «▾» folds it to one small button.
## Row 1 (drive): Erkunden, Patrouille, Punkte, Bereich, Zufall, Löschen, Kopf folgt, Versetzen, Stange − / +
## Row 2 (show):  Ansicht, Beobachter, Mitspieler, Route, Karte, Kameras, Info, Menü

var main
var folded := false
var _rows: VBoxContainer
var _fold_b: Button
var _btn := {}                         # id -> Button
var _t := 0.0
var _hint: HBoxContainer               # 3D-3.66: while setting points / the area: what to do and «Fertig»
var _hint_l: Label

const ROW1 := [["explore", "Erkunden", "Mit dem Rover herumfahren (Tastatur, Maus, Touch, Controller)"],
		["patrol", "Patrouille", "Der Mover fährt Motion Watch die Route ab, Motion Watch passt die ganze Zeit auf"],
		["points", "Punkte", "Route setzen: in die Welt klicken = Punkt, Rechtsklick auf einen Punkt = weg"],
		["area", "Bereich", "Bereich aufziehen: der Mover fährt zufällige Punkte darin ab"],
		["random", "Zufall", "Zufällige Route rund um Motion Watch"],
		["clear", "Löschen", "Route und Bereich löschen"],
		["follow", "Kopf folgt", "Der Kopf dreht zu Verdächtigem, der Mover fährt dann langsamer"],
		["place", "Versetzen", "Rover versetzen: danach in die Welt klicken"],
		["mast_dn", "Stange −", "Kamerakopf tiefer"], ["mast_up", "Stange +", "Kamerakopf höher"]]
const ROW2 := [["view", "Ansicht", "Hinterher, Fahrersicht, von oben"],
		["spectate", "Beobachter", "Wechselnde Kamera-Einstellungen von Rover und Spielern"],
		["invite", "Mitspieler", "QR-Code: Mitspieler mit dem Handy, frei bewegen"],
		["route", "Route", "Route und Bereich anzeigen"],
		["map", "Karte", "Kleine Karte oben links"],
		["cams", "Kameras", "Kamerabilder (was Motion Watch sieht)"],
		["info", "Info", "Anzeige oben (Steuerung, Tempo, Stange)"],
		["panel", "Menü", "Bedienfeld rechts"]]


func _ready() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.09, 0.82)
	sb.set_corner_radius_all(12)
	sb.set_content_margin_all(6)
	sb.border_color = Color(0.25, 0.75, 0.4, 0.6)
	sb.set_border_width_all(1)
	add_theme_stylebox_override("panel", sb)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	add_child(hb)
	_fold_b = Button.new()
	_fold_b.text = "▾"
	_fold_b.tooltip_text = "Leiste ein- / ausklappen"
	_fold_b.focus_mode = Control.FOCUS_NONE
	_fold_b.custom_minimum_size = Vector2(30, 30)
	_fold_b.pressed.connect(func(): set_folded(not folded))
	hb.add_child(_fold_b)
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", 4)
	hb.add_child(_rows)
	_hint = HBoxContainer.new()
	_hint.add_theme_constant_override("separation", 8)
	_hint_l = Label.new()
	_hint_l.add_theme_font_size_override("font_size", 12)
	_hint_l.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
	_hint.add_child(_hint_l)
	var done := Button.new()
	done.text = "✓ Fertig (Esc)"
	done.tooltip_text = "Keine Punkte mehr setzen – die Maus bewegt wieder nur die Ansicht"
	done.focus_mode = Control.FOCUS_NONE
	done.add_theme_font_size_override("font_size", 12)
	done.custom_minimum_size = Vector2(0, 28)
	done.pressed.connect(func(): main.patrol.edit = ""; main.patrol._click_at = null; _paint())
	_hint.add_child(done)
	_hint.visible = false
	_rows.add_child(_hint)
	for row in [ROW1, ROW2]:
		var r := HBoxContainer.new()
		r.add_theme_constant_override("separation", 4)
		_rows.add_child(r)
		for d in row:
			var b := Button.new()
			b.text = d[1]
			b.tooltip_text = d[2]
			b.focus_mode = Control.FOCUS_NONE
			b.add_theme_font_size_override("font_size", 12)
			b.custom_minimum_size = Vector2(0, 28)
			b.pressed.connect(_press.bind(d[0]))
			r.add_child(b)
			_btn[d[0]] = b
	set_anchors_preset(Control.PRESET_TOP_LEFT)


func set_folded(v: bool) -> void:
	folded = v
	_rows.visible = not v
	_fold_b.text = "▴ Werkzeuge" if v else "▾"
	size = get_combined_minimum_size()


func _press(id: String) -> void:
	var ex = main.explore
	var pt = main.patrol
	match id:
		"explore":
			ex.set_on(not ex.on)
		"patrol":
			pt.set_active(not pt.active)
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
		"follow":
			pt.follow = not pt.follow
		"place":
			main.place_kind = "" if main.place_kind == "rover" else "rover"
		"mast_dn":
			main.set_mast(main.mast_h - 0.1)
		"mast_up":
			main.set_mast(main.mast_h + 0.1)
		"view":
			if not ex.on:
				ex.set_on(true)
			ex.next_view()
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
		"panel":
			main.show_panel(not main.ui_root.visible)
	main._settings_dirty = true
	_paint()


func _paint() -> void:
	var ex = main.explore
	var pt = main.patrol
	var st := {"explore": ex.on, "patrol": pt.active, "points": pt.edit == "points", "area": pt.edit == "area" or (pt.mode == "area" and pt.area.size.x > 0.5),
			"follow": pt.follow, "place": main.place_kind == "rover", "spectate": main.spectate, "invite": ex.invite != null and ex.invite.visible,
			"route": pt.show_route, "map": main.map_on, "cams": main.cam_card != null and main.cam_card.visible, "info": not ex.info_hidden,
			"panel": main.ui_root.visible, "view": ex.on}
	for k in _btn:
		var b: Button = _btn[k]
		var on: bool = st.get(k, false)
		b.add_theme_color_override("font_color", Color(0.45, 0.95, 0.55) if on else Color(0.85, 0.88, 0.92))
		b.add_theme_color_override("font_hover_color", Color(0.6, 1.0, 0.7) if on else Color(1, 1, 1))
	var ed: String = pt.edit
	_hint.visible = ed != ""
	if ed != "" and folded:
		set_folded(false)
	if ed == "points":
		_hint_l.text = "Punkte setzen: klicken = Punkt · Rechtsklick auf einen Punkt = weg · Ziehen = Ansicht bewegen"
	elif ed == "area":
		_hint_l.text = "Bereich: mit gedrückter Maustaste aufziehen"
	if _btn.has("view"):
		(_btn["view"] as Button).text = "Ansicht: " + str(ex.VIEW_NAMES.get(ex.view, ex.view)) if ex.on else "Ansicht"
	if _btn.has("patrol"):
		(_btn["patrol"] as Button).text = ("Patrouille: " + {"drive": "fährt", "look": "schaut"}.get(pt.state, "")) if pt.active else "Patrouille"


func _process(dt: float) -> void:
	visible = not main.kids_on and not (main.home_editor != null and main.home_editor.visible)   # 3D-3.69 / 3.73
	if not visible:
		return
	# at the bottom in the middle of the view (left of the panel when it is shown), above the view buttons
	var vs: Vector2 = get_viewport_rect().size
	var right: float = vs.x
	if main.ui_root != null and main.ui_root.visible:
		right -= main.ui_root.size.x + 10.0
	size = get_combined_minimum_size()
	position = Vector2(max(8.0, (right - size.x) / 2.0), vs.y - size.y - 52.0)
	_t -= dt
	if _t <= 0.0:
		_t = 0.3
		_paint()
