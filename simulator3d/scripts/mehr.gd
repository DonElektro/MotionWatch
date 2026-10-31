extends Node
## 3D-4.2x «Mehr» (Wunsch Daniel 30.10.2026): der Simulator übernimmt die Seite «Mehr» von MoveEye (525 / 584 / 516 / 586 /
## 589 / 510 / 578) – gleiche Namen, gleiche Reihenfolge, gleiches Aussehen:
##   Karte «Mehr» ganz unten im Bedienfeld: Hilfe · Rundgang mit Blinki · Selbstdiagnose · Protokoll · Updates (führt zur
##   Karte System → Updates, keine zweite) · Ansicht Hell / Rotlicht / Dunkel · Rückmeldung an den Entwickler · Über den
##   Simulator (mit «Version und Status»). Dazu «Entwickler» (devtool.gd: Karte aller Orte, Sprung, Flugkamera, Reiter «Schalter» mit den Knöpfen der früheren Gruppe «Entwickler»; nur der Besitzer - das einzige «Entwickler» im Simulator). Das «?» der Leiste unten öffnet ein kleines Menü mit denselben Punkten, der Knopf
##   ◐ daneben schaltet Hell → Rotlicht → Dunkel (wie MoveEye). Die Teile: feedback.gd, tour.gd, diagnose.gd, protokoll.gd,
##   farbschema.gd, Symbole mehr_icons.gd. main.gd ruft nur build() auf, speichert keep() mit und gibt /control «mehr» weiter.

var main
var card: Control = null               # the card «Mehr» in the panel
var protokoll
var feedback
var tour
var farben
var theme_name := "dark"               # light | red | dark (saved: ui_theme)
var tour_state := "new"                # new | running | later | skipped | done (saved)
var tour_step := 0
var layer: CanvasLayer                 # the windows of «Mehr» (above the panel, below the look filter)
var win: PanelContainer = null         # the open window (one at a time)
var win_id := ""
var _menu: PanelContainer = null       # the small menu of «?»
var _menu_out := 0.0
var _toast: PanelContainer
var _toast_l: Label
var _toast_t := 0.0
var _theme_seg: HBoxContainer
var _rows := {}
var _about_vals := {}
var _t := 0.0
var _auto_t := 6.0
var dev                                # devtool.gd: Entwicklertool 1 «Karte, Sprung, Kamera» (row «Entwickler», only the owner)
var _dev_row: Control = null

const UI = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const Diagnose = preload("res://scripts/diagnose.gd")
const ITEMS := [["help", "help", "Hilfe", "Maus, Tasten, Leiste – und die Anleitung von MoveEye"],
		["tour", "tour", "Rundgang mit Blinki", "das Bedienfeld Schritt für Schritt"],
		["diag", "steth", "Selbstdiagnose", "was läuft und was fehlt – mit einem Tipp, was zu tun ist"],
		["log", "log", "Protokoll", "die letzten Ereignisse und Fehler – Filter, Kopieren"],
		["updates", "update", "Updates", ""],
		["theme", "theme", "Ansicht", ""],
		["feedback", "chat", "Rückmeldung an den Entwickler", "Fehler, Wünsche, Lob, Fragen – anonym"],
		["dev", "bug", "Entwickler", "Karte aller Orte, Flugkamera, Prüfstand, Störungen, Spieltest – nur für den Besitzer"],
		["about", "info", "Über den Simulator", "Version und Status, Geschichte, Entwickler"]]


func _ready() -> void:
	_load_keep()
	layer = CanvasLayer.new()
	layer.layer = 60
	add_child(layer)
	farben = preload("res://scripts/farbschema.gd").new()
	farben.main = main
	add_child(farben)
	protokoll = preload("res://scripts/protokoll.gd").new()
	protokoll.main = main
	add_child(protokoll)
	feedback = preload("res://scripts/feedback.gd").new()
	feedback.main = main
	feedback.mehr = self
	feedback.theme = main.ui_root.theme if main.ui_root != null else UI.theme()
	layer.add_child(feedback)
	if main.feedback_dlg == null:
		main.feedback_dlg = feedback                 # the old button «Rückmeldung an den Entwickler» (Testen) opens this one
	tour = preload("res://scripts/tour.gd").new()
	tour.main = main
	tour.mehr = self
	add_child(tour)
	dev = preload("res://scripts/devtool.gd").new()
	dev.main = main
	add_child(dev)
	_toast = PanelContainer.new()
	_toast.theme = feedback.theme
	_toast.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.97), UI.GRN.darkened(0.2), 12, 10, 1))
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast_l = Label.new()
	_toast_l.add_theme_font_size_override("font_size", 14)
	_toast.add_child(_toast_l)
	_toast.visible = false
	layer.add_child(_toast)
	for c in [main.ui_root, main.show_btn, feedback, _toast]:
		if c != null:
			farben.register(c, "all")
	farben.set_mode(theme_name)
	var a := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	if "--no-update" in a or "--no-tour" in a or main.autostart_lock:
		_auto_t = -1.0                                # automatic runs (test bench, tests, autostart): no tour by itself
	if "--tour" in a:
		_auto_t = 3.0                                 # tests: the tour by itself all the same
	call_deferred("_late_register")


func _late_register() -> void:
	if main.toolbar != null:
		farben.register(main.toolbar, "red")         # the bar over the 3D view: only in the red light
		for k in ["_sub", "_help", "_hint"]:
			var c = main.toolbar.get(k)
			if c is Control:
				farben.register(c, "red")


# ---- saved with the settings of the simulator (main.gd _save_settings -> keep()) ------------------------------------------
func keep() -> Dictionary:
	return {"ui_theme": theme_name, "tour_state": "later" if tour_state == "running" else tour_state, "tour_step": tour_step}


func _load_keep() -> void:
	if not FileAccess.file_exists(main.SETTINGS_FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	if typeof(d) != TYPE_DICTIONARY:
		return
	if str(d.get("ui_theme", "")) in UI.THEMES:
		theme_name = str(d["ui_theme"])
	if str(d.get("tour_state", "")) in ["new", "later", "skipped", "done"]:
		tour_state = str(d["tour_state"])
	tour_step = int(d.get("tour_step", 0))


# ---- the card «Mehr» (like the page «Mehr» of MoveEye: one row per thing, symbol, name, small text, ›) --------------------
func build(box_: VBoxContainer) -> void:
	var body := UI.fold_card(box_, "Mehr", false, "more")
	card = body.get_meta("card")
	main.fold_bodies.append(body)
	main.top_cards.append(card)
	for it in ITEMS:
		if it[0] == "theme":
			body.add_child(_theme_row())
			continue
		var r := _row(it[0], it[1], it[2], it[3])
		body.add_child(r)
		if it[0] == "dev":
			_dev_row = r
	_paint_rows()


func _row(id: String, icon: String, title: String, sub: String) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_ALL
	b.custom_minimum_size = Vector2(0, 52)
	b.add_theme_stylebox_override("normal", UI.box(UI.PANEL, UI.LINE, 14, 8, 1))
	b.add_theme_stylebox_override("hover", UI.box(UI.PANEL, UI.ACC, 14, 8, 1))
	b.add_theme_stylebox_override("pressed", UI.box(UI.PANEL2, UI.ACC, 14, 8, 1))
	b.add_theme_stylebox_override("focus", UI.box(Color(0, 0, 0, 0), UI.ACC, 14, 8, 1))
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 12
	h.offset_right = -10
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_theme_constant_override("separation", 12)
	b.add_child(h)
	var ic := Icons.icon(icon, UI.TXT, 22.0)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ic)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 0)
	h.add_child(v)
	var tl := Label.new()
	tl.text = title
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 14)
	tl.clip_text = true
	v.add_child(tl)
	var sl := UI.small(sub)
	sl.autowrap_mode = TextServer.AUTOWRAP_OFF
	sl.clip_text = true
	sl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	v.add_child(sl)
	var ar := Label.new()
	ar.text = "›"
	ar.add_theme_font_size_override("font_size", 18)
	ar.add_theme_color_override("font_color", UI.MUT)
	h.add_child(ar)
	b.pressed.connect(func(): act(id))
	_rows[id] = sl
	return b


func _theme_row() -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.LINE, 14, 10, 1))
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 12)
	p.add_child(h)
	var ic := Icons.icon("theme", UI.TXT, 22.0)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ic)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var tl := Label.new()
	tl.text = "Ansicht: Hell / Rotlicht / Dunkel"
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 14)
	v.add_child(tl)
	_theme_seg = HBoxContainer.new()
	_theme_seg.add_theme_constant_override("separation", 0)
	v.add_child(_theme_seg)
	for k in UI.THEMES:                                 # the order of MoveEye: Hell → Rotlicht → Dunkel
		var b := Button.new()
		b.text = UI.THEME_NAMES[k]
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 28)
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_size_override("font_size", 12)
		b.tooltip_text = {"light": "Helle Farben wie MoveEye «Hell» – für draussen am Tag", "red": "Rotlicht: sehr dunkel und rot – für einen kurzen Blick in der Nacht im Zelt (die Augen bleiben ans Dunkel gewöhnt)",
				"dark": "Die dunklen Farben (wie bisher)"}[k]
		b.pressed.connect(func(): set_theme(k))
		b.set_meta("k", k)
		_theme_seg.add_child(b)
	v.add_child(UI.small("Für das Bedienfeld und die Fenster – die 3D-Ansicht bleibt. Auch mit ◐ in der Leiste unten."))
	return p


func _paint_rows() -> void:
	if _theme_seg != null:
		var n := _theme_seg.get_child_count()
		for j in range(n):
			var b: Button = _theme_seg.get_child(j)
			var on: bool = b.get_meta("k") == theme_name
			var st := UI.box(UI.ACC if on else UI.FIELD, UI.ACC if on else UI.LINE, 10, 6, 1)
			if j > 0:
				st.corner_radius_top_left = 0
				st.corner_radius_bottom_left = 0
			if j < n - 1:
				st.corner_radius_top_right = 0
				st.corner_radius_bottom_right = 0
			for s in ["normal", "hover", "pressed", "focus"]:
				b.add_theme_stylebox_override(s, st)
			b.add_theme_color_override("font_color", Color.WHITE if on else UI.MUT)
			b.add_theme_color_override("font_hover_color", Color.WHITE)
	if _rows.has("updates"):
		var ui := str(main.update_info)
		_rows["updates"].text = "Version %s · %s" % [main.VERSION, ui if ui != "" else "zur Karte System → Updates"]
	if _rows.has("tour"):
		_rows["tour"].text = ("weiter bei Schritt %d – das Bedienfeld Schritt für Schritt" % (tour_step + 1)) if tour_state == "later" else "das Bedienfeld Schritt für Schritt"
	if _rows.has("diag"):
		var its := Diagnose.check(main)
		var pf: Dictionary = main.perf_info()            # 3D-4.25: «Leistung» right on the card (to test on the Raspberry Pi)
		_rows["diag"].text = Diagnose.summary(its) + " · Leistung: %d Bilder/s, Lite %s" % [int(pf["fps"]), "an" if pf["lite"] else "aus"]


# ---- what a row does ------------------------------------------------------------------------------------------------------------
func act(id: String) -> void:
	close_menu()
	match id:
		"help", "about", "diag", "log":
			open_window(id)
		"tour":
			close_window()
			tour.start(tour_step if tour_state == "later" else 0)
		"updates":
			open_updates()
		"feedback":
			close_window()
			feedback.open("Mehr")
		"theme":
			theme_next()
		"dev":
			close_window()
			dev.open()
		"mehr":
			show_card()


func set_theme(k: String) -> void:
	theme_name = k if k in UI.THEMES else "dark"
	farben.set_mode(theme_name)
	_paint_rows()
	main._settings_dirty = true
	if main.toolbar != null and main.toolbar.get("_items") != null and main.toolbar._items.has("theme"):
		main.toolbar._items["theme"].queue_redraw()
	if protokoll != null:
		protokoll.add("info", "Ansicht: " + UI.THEME_NAMES[theme_name])


func theme_next() -> void:
	set_theme(UI.theme_next(theme_name))
	toast(UI.THEME_NAMES[theme_name])


func show_card() -> void:
	"""the card «Mehr» open and in view"""
	main.show_panel(true)
	var body: Control = null
	for b in main.fold_bodies:
		if is_instance_valid(b) and b.get_meta("card", null) == card:
			body = b
	if body != null:
		UI.set_open(body, true)
	await get_tree().process_frame
	_scroll_to(card)


func _scroll_to(c: Control) -> void:
	var p := c.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(c)


func open_updates() -> void:
	"""no second update card: open System → Updates (switch to «Experte» if it is hidden in «Einfach»)"""
	close_window()
	main.show_panel(true)
	var sysb: Control = main.group_bodies.get("System", null)
	var upd: Control = null
	for sb in main.sub_bodies:
		if is_instance_valid(sb) and str(sb.get_meta("title", "")) == "Updates" and sysb != null and sysb.is_ancestor_of(sb):
			upd = sb
	if sysb == null:
		toast("Updates: Karte System nicht gefunden")
		return
	if not sysb.get_meta("card").visible or (upd != null and not upd.get_meta("wrap").visible):
		main.set_simple(false)
		if main.simple_seg != null and main.simple_seg.has_meta("paint"):
			main.simple_seg.get_meta("paint").call(true)
		toast("«Experte» eingeschaltet – die Updates stehen unter System.")
	UI.set_open(sysb, true)
	if upd != null:
		UI.set_sub_open(upd, true)
	await get_tree().process_frame
	await get_tree().process_frame
	_scroll_to(upd if upd != null else sysb.get_meta("card"))


# ---- one window at a time (the look of the feedback window of MoveEye) --------------------------------------------------------
func _window(title: String, icon: String) -> VBoxContainer:
	close_window()
	win = PanelContainer.new()
	win.theme = feedback.theme
	win.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.99), UI.LINE, 16, 16, 1))
	layer.add_child(win)
	farben.register(win, "all")
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	win.add_child(v)
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 8)
	v.add_child(hd)
	var ic := Icons.icon(icon, UI.TXT, 22.0)
	if not Icons.KINDS.has(icon):
		ic = UI.group_icon(icon)
		ic.set_meta("col", UI.TXT)
	hd.add_child(ic)
	var tl := Label.new()
	tl.text = title
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	var x := Button.new()
	x.flat = true
	x.custom_minimum_size = Vector2(30, 30)
	x.tooltip_text = "Schliessen (Esc)"
	var xi := Icons.icon("x", UI.MUT, 16.0)
	xi.position = Vector2(7, 7)
	x.add_child(xi)
	x.pressed.connect(close_window)
	hd.add_child(x)
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", 8)
	v.add_child(body)
	_place_win()
	return body


func _place_win() -> void:
	await get_tree().process_frame
	if win == null or not is_instance_valid(win):
		return
	win.reset_size()
	await get_tree().process_frame
	if win == null or not is_instance_valid(win):
		return
	win.reset_size()
	var vs: Vector2 = win.get_viewport_rect().size
	var right: float = vs.x - (main.ui_root.size.x if main.ui_root != null and main.ui_root.visible else 0.0)
	var x: float = (right - win.size.x) / 2.0 if right - win.size.x > 16.0 else (vs.x - win.size.x) / 2.0
	win.position = Vector2(maxf(8.0, x), maxf(8.0, (vs.y - win.size.y) / 2.0))


func close_window() -> void:
	if win != null and is_instance_valid(win):
		win.queue_free()
	win = null
	win_id = ""
	_about_vals = {}


func open_window(id: String) -> void:
	match id:
		"help":
			var b := _window("Hilfe", "help")
			_help(b)
		"about":
			var b := _window("Über den Simulator", "info")
			_about(b)
		"diag":
			var b := _window("Selbstdiagnose", "steth")
			Diagnose.build(main, b, self)
		"log":
			var b := _window("Protokoll", "log")
			protokoll.build(b, self)
		_:
			return
	win_id = id


func _help(b: VBoxContainer) -> void:
	var tx := ""
	if main.toolbar != null and main.toolbar.has_method("_help_text"):
		tx = main.toolbar._help_text()
	for part in [["Ansicht und Tasten", tx], ["Alle Tasten", str(main.info_label.text) if main.info_label != null else ""]]:
		if str(part[1]) == "":
			continue
		var h := UI.heading(part[0])
		b.add_child(h)
		var l := UI.small(str(part[1]), UI.TXT)
		l.custom_minimum_size = Vector2(520, 0)
		b.add_child(l)
	b.add_child(UI.heading("Weiter"))
	var tips := UI.small("· Die Kacheln oben (Welt · Testen · Lernen · Spielen) tun das Häufigste mit einem Klick.\n· «Einfach» zeigt das Wichtigste, «Experte» alles; das Suchfeld findet jede Einstellung.\n· Die ganze Anleitung steht in MoveEye: Reiter Mehr → Anleitung (Kapitel 3D-Simulator).", UI.TXT)
	tips.custom_minimum_size = Vector2(520, 0)
	b.add_child(tips)
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	b.add_child(bt)
	var t := Button.new()
	t.text = "Rundgang mit Blinki"
	t.pressed.connect(func(): act("tour"))
	bt.add_child(t)
	var mw := Button.new()
	mw.text = "Anleitung von MoveEye"
	mw.tooltip_text = "Öffnet die Anleitung im Browser (MoveEye muss verbunden sein)"
	mw.pressed.connect(func():
		if main.mw_addr != "" and main.now() - main.mw_t < 10.0:
			OS.shell_open("%s://%s:%d/help#sim3d" % [str(main.mw.get("mw_scheme", "http")), main.mw_addr, int(main.mw.get("mw_port", 5000))])
		else:
			toast("MoveEye ist nicht verbunden – die Anleitung steht in MoveEye unter Mehr → Anleitung."))
	bt.add_child(mw)
	var cl := Button.new()
	cl.text = "Schliessen"
	cl.pressed.connect(close_window)
	bt.add_child(cl)


func _about(b: VBoxContainer) -> void:
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 12)
	b.add_child(hd)
	var logo: Control = load("res://scripts/mw_logo.gd").new()
	logo.custom_minimum_size = Vector2(52, 52)
	hd.add_child(logo)
	var hv := VBoxContainer.new()
	hv.alignment = BoxContainer.ALIGNMENT_CENTER
	hd.add_child(hv)
	var t1 := Label.new()
	t1.text = "MoveEye 3D-Simulator"
	t1.add_theme_font_override("font", UI.heading_font())
	t1.add_theme_font_size_override("font_size", 18)
	hv.add_child(t1)
	hv.add_child(UI.small("Version %s · Elektro (alias Daniel) · Schweiz" % main.VERSION))
	var st := UI.small("Der 3D-Simulator baut den Platz von MoveEye nach – Personen, Tiere, Wetter, Nacht –, damit MoveEye üben kann, ohne echte Nächte. Der Prüfstand misst jede Version von MoveEye damit, und am Lagerfeuer wird er zum Spiel «Team gegen MoveEye». Gebaut mit Godot 4 – von Elektro zusammen mit Claude (einer KI von Anthropic).", UI.TXT)
	st.custom_minimum_size = Vector2(520, 0)
	st.add_theme_font_size_override("font_size", 13)
	b.add_child(st)
	# «Version und Status» (like the part of the card System of MoveEye)
	var vc := PanelContainer.new()
	vc.add_theme_stylebox_override("panel", UI.box(UI.PANEL2, UI.LINE, 12, 10, 1))
	b.add_child(vc)
	var vv := VBoxContainer.new()
	vv.add_theme_constant_override("separation", 6)
	vc.add_child(vv)
	vv.add_child(UI.heading("Version und Status"))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 14)
	g.add_theme_constant_override("v_separation", 4)
	vv.add_child(g)
	_about_vals = {}
	for k in ["Simulator", "Godot", "Grafik", "Bilder pro Sekunde", "Leistung", "CPU", "Arbeitsspeicher", "MoveEye", "Ports", "System", "Ordner"]:
		var kl := UI.small(k)
		kl.autowrap_mode = TextServer.AUTOWRAP_OFF
		kl.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		g.add_child(kl)
		var vl := UI.small("", UI.TXT)
		vl.custom_minimum_size = Vector2(380, 0)
		g.add_child(vl)
		_about_vals[k] = vl
	_about_paint()
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	b.add_child(bt)
	var cp := Button.new()
	cp.text = "Kopieren"
	cp.tooltip_text = "Version und Status als Text in die Zwischenablage"
	cp.pressed.connect(func():
		var out := PackedStringArray()
		for k in _about_vals:
			out.append("%s: %s" % [k, _about_vals[k].text])
		DisplayServer.clipboard_set("\n".join(out))
		toast("Kopiert."))
	bt.add_child(cp)
	var fb := Button.new()
	fb.text = "Rückmeldung an den Entwickler"
	fb.pressed.connect(func(): act("feedback"))
	bt.add_child(fb)
	var cl := Button.new()
	cl.text = "Schliessen"
	cl.pressed.connect(close_window)
	bt.add_child(cl)


func about_status() -> Dictionary:
	var v: Dictionary = Engine.get_version_info()
	var own: Dictionary = main.mini_box.own if main.mini_box != null else {}
	var pc := float(own.get("pc", -1.0))
	var sm := float(own.get("sim", -1.0))
	var mi: Dictionary = OS.get_memory_info() if OS.has_method("get_memory_info") else {}
	var conn: bool = main.mw_addr != "" and main.now() - main.mw_t < 3.0
	var ports := "Senden und Steuerung %d (%s)" % [int(main.stream_port), "ein" if main.stream_on else "aus"]
	if main.tunnel_on and main.tunnel != null:
		ports += " · Tunnel %s:%d (%s)" % [str(main.tunnel_host), int(main.tunnel.PORT), str(main.tunnel.msg)]
	return {"Simulator": "%s%s" % [main.VERSION, (" · Update: " + str(main.update_info)) if str(main.update_info) != "" else ""],
			"Godot": "%s · %s" % [str(v.get("string", "")), str(ProjectSettings.get_setting("rendering/renderer/rendering_method", ""))],
			"Grafik": "Stufe «%s» · %s%s" % [Diagnose.QNAMES.get(str(main.quality), str(main.quality)), RenderingServer.get_video_adapter_name(), " · virtuelle Maschine" if main.in_vm else ""],
			"Bilder pro Sekunde": "%d" % Engine.get_frames_per_second(),
			"Leistung": _perf_line(),
			"CPU": "PC %s · Simulator %s · %d Kerne" % ["–" if pc < 0 else "%d %%" % roundi(pc), "–" if sm < 0 else "%d %%" % roundi(sm), OS.get_processor_count()],
			"Arbeitsspeicher": ("frei %s von %s · " % [Diagnose._gb(float(mi.get("available", 0))), Diagnose._gb(float(mi.get("physical", 0)))] if float(mi.get("physical", -1)) > 0 else "") + "Simulator " + Diagnose._gb(float(OS.get_static_memory_usage())),
			"MoveEye": ("verbunden mit «%s» · MoveEye %s · %s" % [str(main.mw.get("device", "MoveEye")), str(main.mw.get("mw_version", "?")), main.mw_addr]) if conn else ("nicht verbunden" + (" (zuletzt %s)" % main.mw_addr if main.mw_addr != "" else "")),
			"Ports": ports,
			"System": "%s · %s" % [OS.get_name(), OS.get_distribution_name() if OS.has_method("get_distribution_name") else ""],
			"Ordner": OS.get_user_data_dir()}


func _perf_line() -> String:
	"""3D-4.25: Lite an / aus, Renderer, Auflösung (wie «Leistung» in der Selbstdiagnose)"""
	var pf: Dictionary = main.perf_info()
	return "%s · %s · 3D %s (%d %%)" % [("Lite an (%s)" % str(pf["why"])) if pf["lite"] else "Lite aus", str(pf["renderer"]), str(pf["res"]), int(pf["scale"])]


func _about_paint() -> void:
	if _about_vals.is_empty():
		return
	var s := about_status()
	for k in _about_vals:
		if is_instance_valid(_about_vals[k]):
			_about_vals[k].text = str(s.get(k, ""))


# ---- the menu of «?» in the bar at the bottom ---------------------------------------------------------------------------------
func help_menu(anchor: Control) -> void:
	if _menu != null and is_instance_valid(_menu):
		close_menu()
		return
	_menu = PanelContainer.new()
	_menu.theme = feedback.theme
	_menu.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.96), Color(1, 1, 1, 0.14), 14, 8, 1))
	layer.add_child(_menu)
	farben.register(_menu, "all")
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	_menu.add_child(v)
	var hl := UI.small(main.toolbar._help_text() if main.toolbar != null and main.toolbar.has_method("_help_text") else "", Color(0.85, 0.88, 0.92))
	hl.custom_minimum_size = Vector2(360, 0)
	v.add_child(hl)
	var sep := ColorRect.new()
	sep.color = Color(1, 1, 1, 0.12)
	sep.custom_minimum_size = Vector2(0, 1)
	v.add_child(sep)
	for it in [["tour", "tour", "Rundgang mit Blinki"], ["help", "help", "Hilfe"], ["diag", "steth", "Selbstdiagnose"], ["log", "log", "Protokoll"],
			["feedback", "chat", "Rückmeldung an den Entwickler"], ["about", "info", "Über den Simulator"], ["mehr", "more", "Alles unter «Mehr» im Bedienfeld"]]:
		var b := Button.new()
		b.flat = true
		b.focus_mode = Control.FOCUS_ALL
		b.custom_minimum_size = Vector2(260, 32)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.text = "         " + it[2]
		b.add_theme_font_size_override("font_size", 13)
		var ic := Icons.icon(it[1], Color(0.85, 0.88, 0.92), 18.0)
		ic.position = Vector2(8, 7)
		b.add_child(ic)
		b.pressed.connect(func(): act(it[0]))
		v.add_child(b)
	_menu.reset_size()
	var vs: Vector2 = _menu.get_viewport_rect().size
	var ar := anchor.get_global_rect()
	_menu.position = Vector2(clampf(ar.end.x - _menu.size.x, 4.0, vs.x - _menu.size.x - 4.0), ar.position.y - _menu.size.y - 14.0)
	_menu_out = 0.8


func menu_open() -> bool:
	return _menu != null and is_instance_valid(_menu)


func close_menu() -> void:
	if _menu != null and is_instance_valid(_menu):
		_menu.queue_free()
	_menu = null


func toast(t: String) -> void:
	_toast_l.text = t
	_toast.visible = true
	_toast.reset_size()
	var vs: Vector2 = _toast.get_viewport_rect().size
	var right: float = vs.x - (main.ui_root.size.x if main.ui_root != null and main.ui_root.visible else 0.0)
	_toast.position = Vector2(maxf(8.0, (right - _toast.size.x) / 2.0), vs.y - _toast.size.y - 84.0)
	_toast_t = 3.5


func _process(dt: float) -> void:
	if _dev_row != null and _dev_row.visible != dev.is_owner(main):
		_dev_row.visible = dev.is_owner(main)          # Entwicklertool: only the owner (not in the children's mode)
	if _toast_t > 0.0:
		_toast_t -= dt
		if _toast_t <= 0.0:
			_toast.visible = false
	if menu_open():                                   # the menu goes when the mouse has left it (like the menus of the bar)
		var mp := _menu.get_viewport().get_mouse_position()
		var hb: Control = main.toolbar._items.get("help") if main.toolbar != null else null
		if _menu.get_global_rect().grow(10).has_point(mp) or (hb != null and hb.get_global_rect().grow(4).has_point(mp)):
			_menu_out = 0.8
		else:
			_menu_out -= dt
			if _menu_out <= 0.0:
				close_menu()
	_t -= dt
	if _t <= 0.0:
		_t = 1.0
		_about_paint()
		if win_id == "log":
			protokoll.refresh()
		if card != null and card.is_visible_in_tree():
			_paint_rows()
	if _auto_t > 0.0:                                 # the tour by itself: once, a little after the start, when nothing else runs
		_auto_t -= dt
		if _auto_t <= 0.0:
			if tour_state in ["new", "later"] and main.win_open and not main.kids_on and not (main.game != null and main.game.open) \
					and not (main.testrun != null and main.testrun.running) and not (main.gamewiz != null and main.gamewiz.visible) \
					and not (main.news != null and main.news.visible):
				tour.start(tour_step if tour_state == "later" else 0)
			elif tour_state in ["new", "later"]:
				_auto_t = 20.0                         # busy: try again later


func _unhandled_key_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and (e as InputEventKey).keycode == KEY_ESCAPE:
		if menu_open():
			close_menu()
		elif win != null:
			close_window()
		else:
			return
		get_viewport().set_input_as_handled()


# ---- /control «mehr» (tests and MoveEye): {"do": …} -----------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	"""synchronous (main.control answers at once): longer things run on by themselves"""
	var dd := str(d.get("do", "state"))
	match dd:
		"open":
			var id := str(d.get("id", "mehr"))
			if id in ["help", "about", "diag", "log"]:
				open_window(id)
			elif id == "card":
				show_card()
			else:
				act(id)
		"close":
			close_window()
			close_menu()
			feedback.visible = false
		"theme":
			if d.has("set"):
				set_theme(str(d["set"]))
			else:
				theme_next()
		"menu":
			if main.toolbar != null and main.toolbar._items.has("help"):
				help_menu(main.toolbar._items["help"])
		"tour":
			var op := str(d.get("op", "start"))
			if op == "start":
				tour.start(int(d.get("step", 0)))
			elif op == "go":
				tour.go(int(d.get("by", 1)))
			elif op in ["later", "skipped", "done"]:
				tour.stop(op)
			return dict_ok(tour.state())
		"diag":
			return {"ok": true, "items": Diagnose.check(main), "summary": Diagnose.summary(Diagnose.check(main))}
		"log":
			if d.has("add"):
				protokoll.add(str(d.get("kind", "info")), str(d["add"]))
			if d.has("filter"):
				protokoll._filter = str(d["filter"])
				protokoll._shown = -1
				protokoll.refresh()
			var st: Dictionary = protokoll.state()
			st["ok"] = true
			st["text"] = protokoll.as_text(str(d.get("filter", "")))
			return st
		"fb_test":                                    # tests: send to a local address only (never the real channel)
			var u := str(d.get("url", ""))
			var host := u.split("/")[2].split(":")[0] if u.count("/") >= 3 else ""
			if u != "" and not (u.begins_with("http://") and host in ["127.0.0.1", "localhost"]):
				return {"ok": false, "error": "only http://127.0.0.1 or localhost"}
			feedback.test_url = u
			return dict_ok(feedback.status())
		"fb_open":
			feedback.open(str(d.get("page", "Mehr")))
			if d.has("text"):
				feedback.fill_and_send(d)
			return dict_ok(feedback.status())
		"fb_flush":
			feedback.flush()
			return dict_ok(feedback.status())
		"fb_status":
			return dict_ok(feedback.status())
		"shot":                                       # tests: the whole window as PNG into user://mehr_shots/<name>.png
			var nm := str(d.get("name", "shot")).validate_filename().replace(" ", "_").substr(0, 60)
			var img := get_viewport().get_texture().get_image()
			DirAccess.make_dir_recursive_absolute("user://mehr_shots")
			var p := "user://mehr_shots/%s.png" % nm
			img.save_png(p)
			return {"ok": true, "path": ProjectSettings.globalize_path(p)}
	return {"ok": true, "theme": theme_name, "tour": tour.state(), "win": win_id, "menu": menu_open(), "card": card != null and card.is_visible_in_tree(),
			"feedback": feedback.status(), "about": about_status() if dd == "about" else {}, "log_n": protokoll.items.size()}


static func dict_ok(x: Dictionary) -> Dictionary:
	var o := x.duplicate()
	o["ok"] = true
	return o
