extends PanelContainer
## 3D-3.61: the tool bar at the bottom of the simulator window - everything of «Erkunden», «Patrouille» and the view
## with the mouse only (also on a PC with a keyboard). Green = on. «▾» folds it to one small button.
## 3D-3.86: one row: Erkunden, Patrouille ▾, Kopf steuern, Versetzen, Stange ▾, Inventar, Vorlagen, Mitspieler, Ansicht ▾, Menü (ROW1 / ROW2 = the names)
## Row 2 (show):  Ansicht, Beobachter, Mitspieler, Route, Karte, Kameras, Info, Vorlagen, Menü

var main
var folded := false
var _rows: VBoxContainer
var _fold_b: Button
var _btn := {}                         # id -> Button
var _t := 0.0
var _hint: HBoxContainer               # 3D-3.66: while setting points / the area: what to do and «Fertig»
var _hint_l: Label
var _menus := {}                       # 3D-3.86: title -> [MenuButton, ids]

# 3D-3.86: the one row - a string is a button, an array a menu [title, tooltip, ids]
# 3D-3.91: the bar is for moving and the view (concept); Inventar / Vorlagen are tiles of «Schnellzugriff» - not twice here.
# «Verfolgen» on its own (it is not only for the patrol).
const MAIN_ROW := ["explore", ["Patrouille", "Route für den Mover", ["patrol", "points", "area", "random", "clear", "route"]],
		"follow", "head", "place", ["Stange", "Höhe des Kamerakopfs", ["mast_up", "mast_dn"]], "invite",
		["Ansicht", "Was angezeigt wird", ["view", "spectate", "map", "cams", "info", "laser", "zones3d", "det3d"]], "panel"]

const ROW1 := [["explore", "Erkunden", "Mit dem Rover herumfahren (Tastatur, Maus, Touch, Controller)"],
		["patrol", "Patrouille", "Der Mover fährt MoveEye die Route ab, MoveEye passt die ganze Zeit auf"],
		["points", "Punkte", "Route setzen: in die Welt klicken = Punkt, Rechtsklick auf einen Punkt = weg"],
		["area", "Bereich", "Bereich aufziehen: der Mover fährt zufällige Punkte darin ab"],
		["random", "Zufall", "Zufällige Route rund um MoveEye"],
		["clear", "Löschen", "Route und Bereich löschen"],
		["follow", "Verfolgen", "Der Kopf hält Personen, Tiere und Bewegtes in der Bildmitte (= «Folgen» in MoveEye); auf Patrouille fährt der Mover dann langsamer"],
		["place", "Versetzen", "Rover versetzen: danach in die Welt klicken"],
		["head", "Kopf steuern", "Den Kopf von MoveEye mit Pfeilen drehen, Licht ein / aus"],
		["mast_dn", "Stange −", "Kamerakopf tiefer"], ["mast_up", "Stange +", "Kamerakopf höher"]]
const ROW2 := [["view", "Ansicht", "Hinterher, Fahrersicht, von oben"],
		["spectate", "Beobachter", "Wechselnde Kamera-Einstellungen von Rover und Spielern"],
		["invite", "Mitspieler", "QR-Code: Mitspieler mit dem Handy, frei bewegen"],
		["route", "Route", "Route und Bereich anzeigen"],
		["map", "Minikarte", "Kleine Karte oben links"],
		["cams", "Kameras", "Kamerabilder (was MoveEye sieht)"],
		["info", "Info", "Anzeige oben (Steuerung, Tempo, Stange)"],
		["laser", "Blickrichtung", "Roter Strahl: wohin die Kamera von MoveEye schaut, mit den Bildrändern am Boden (nur für dich sichtbar)"],
		["zones3d", "Zonen in 3D", "Die Zonen von MoveEye auf dem Boden (nur für dich sichtbar)"],
		["det3d", "Erkennung in 3D", "Rahmen von MoveEye über den Figuren: grün erkannt, rot Fehlalarm, orange übersehen"],
		["templates", "Vorlagen", "Fertige Szenen, echte Orte, 3D-Bausätze, eigene 3D-Datei (.glb) laden"],
		["inventar", "Inventar", "Alle Menschen, Tiere, Fahrzeuge und Dinge, die die KI kennt – in die Welt ziehen"],
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
	# 3D-3.86: one row - the main buttons, the rest in small menus (▾)
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", 4)
	_rows.add_child(r)
	var all := {}
	for d in ROW1 + ROW2:
		all[d[0]] = d
	for item in MAIN_ROW:
		if typeof(item) == TYPE_ARRAY:                  # a menu: [title, tooltip, [ids]]
			var mb := MenuButton.new()
			mb.text = item[0] + " ▾"
			mb.tooltip_text = item[1]
			mb.flat = false
			mb.focus_mode = Control.FOCUS_NONE
			mb.add_theme_font_size_override("font_size", 12)
			mb.custom_minimum_size = Vector2(0, 28)
			var pm := mb.get_popup()
			for i in range(item[2].size()):
				var id_: String = item[2][i]
				pm.add_check_item(all[id_][1], i)
				pm.set_item_tooltip(i, all[id_][2])
			var ids: Array = item[2]
			pm.id_pressed.connect(func(i): _press(ids[i]))
			pm.about_to_popup.connect(func(): _paint_menu(pm, ids))
			r.add_child(mb)
			_menus[item[0]] = [mb, ids]
		else:
			var d = all[item]
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
				main.start_info = "Verfolgen braucht MoveEye – zuerst verbinden (bis dahin dreht nur die Patrouille zu Verdächtigem)"
		"place":
			main.place_kind = "" if main.place_kind == "rover" else "rover"
		"head":
			main.headpad.toggle()
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
		"laser":                                     # 3D-3.96: the direction MoveEye looks (beginners)
			main.show_laser = not main.show_laser
			main._settings_dirty = true
		"zones3d":                                   # 3D-3.93: from the centre of MoveEye to the view menu (display only)
			main.show_zones3d = not main.show_zones3d
			main._settings_dirty = true
		"det3d":
			main.show_det3d = not main.show_det3d
			main._settings_dirty = true
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
	var st := {"explore": ex.on, "patrol": pt.active, "points": pt.edit == "points", "area": pt.edit == "area" or (pt.mode == "area" and pt.area.size.x > 0.5),
			"follow": main.mw_follow_on() if main.now() - main.mw_t < 3.0 else pt.follow, "place": main.place_kind == "rover", "spectate": main.spectate, "invite": ex.invite != null and ex.invite.visible,
			"route": pt.show_route, "map": main.map_on, "cams": main.cam_card != null and main.cam_card.visible, "info": not ex.info_hidden, "laser": main.show_laser, "zones3d": main.show_zones3d, "det3d": main.show_det3d,
			"panel": main.ui_root.visible, "view": ex.on, "head": main.headpad != null and main.headpad.visible,
			"templates": main.templates != null and main.templates.visible, "inventar": main.inventar != null and main.inventar.visible}
	_st = st
	for t in _menus:
		var any := bool(st.get(_menus[t][1][0], false))      # the first entry says it (patrol drives, view of the rover)
		(_menus[t][0] as MenuButton).add_theme_color_override("font_color", Color(0.45, 0.95, 0.55) if any else Color(0.85, 0.88, 0.92))
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
	visible = not main.kids_on and not (main.home_editor != null and main.home_editor.visible) and not (main.localplay != null and main.localplay.active)   # 3D-3.69 / 3.73
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



var _st := {}


func _paint_menu(pm: PopupMenu, ids: Array) -> void:
	_paint()
	for i in range(ids.size()):
		pm.set_item_checked(i, bool(_st.get(ids[i], false)))
		if ids[i] == "patrol":
			pm.set_item_text(i, "Patrouille stoppen" if main.patrol.active else "Patrouille starten")
