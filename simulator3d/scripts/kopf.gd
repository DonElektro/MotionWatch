extends HBoxContainer
## Der gemeinsame Kopf (Besitzer 01.11.2026: «ein Kopf, überall gleich» – Gegenstück zu MoveEye Teil 639t und dem Pi-Fenster):
##   ? Hilfe · 🔔 Ton · ↻ zurück und neu laden · DE Sprache · ☰ Menü · ⛶ Vollbild · ▲ Kopf einklappen · 🛠 Entwickler
## in dieser Reihenfolge, alle gleich gross (38 × 38) mit gezeichneten Symbolen (die Schrift hat keine Emoji). Die Liste, die Symbole
## und die Texte (de / en / fr / it / rm) kommen aus res://ui_gemeinsam.json («kopf»), genau wie in MoveEye.
## Das Bedienfeld ist schmal (unter «schmal_px»): ab «Sprache» stehen die Knöpfe im ☰-Menü, in derselben Reihenfolge (wie auf dem
## Handy). Im ☰-Menü auch «Allgemein»: Hell / Dunkel / Rotlicht, Rückmeldung, alles unter «Mehr».
##   ? = das Hilfe-Menü von «Mehr» (Rundgang, Hilfe, Selbstdiagnose …) · 🔔 = «Ton am PC» (simint.set_pc_sound, wie unter
##   Licht & Ton) · ↻ = Fenster zu, Blick zurück zu MoveEye («Zum Kopf»), Handy-Ansicht neu laden · DE = Sprache des Simulators
##   (i18n.gd, «wie MoveEye» = auto) · ⛶ = Fenster / Vollbild · ▲ = Leiste und Suche einklappen · 🛠 = Entwickler-Fenster (nur
##   Entwickler-Bereich an und Besitzer, wie die Karte «Entwickler»; der Zweig real-dev-zugang hängt seinen Knopf hier ein).

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const UG = preload("res://scripts/ui_gemeinsam.gd")

var main
var btns := {}                         # id -> Button (only the ones in the row)
var folded := false
var _pop: PanelContainer = null
var _pop_out := 0.0
var _anchor: Control = null


static func knoepfe() -> Array:
	"""the list of ui_gemeinsam.json «kopf.knoepfe» (in this order)"""
	return ((UG.data().get("kopf", {}) as Dictionary).get("knoepfe", []) as Array)


static func text(id: String) -> String:
	"""the name of a button in the language of the simulator (from ui_gemeinsam.json, not from texte.json)"""
	for b in knoepfe():
		if str(b.get("id")) == id:
			var tx: Dictionary = b.get("texts", {})
			return str(tx.get(T.lang(), tx.get("de", id)))
	return id


static func menu_text(k: String) -> String:
	var m: Dictionary = (UG.data().get("kopf", {}) as Dictionary).get("menue", {})
	var tx: Dictionary = m.get(k, {})
	return str(tx.get(T.lang(), tx.get("de", k)))


func narrow() -> bool:
	"""the panel of the simulator is narrower than «schmal_px» of MoveEye: from «Sprache» on the buttons are in ☰"""
	var px := float((UG.data().get("kopf", {}) as Dictionary).get("schmal_px", 760))
	var w: float = main.ui_root.size.x if main != null and main.ui_root != null and main.ui_root.size.x > 0 else 392.0
	return w < px


func in_row() -> Array:
	"""the ids shown in the row (the others: in ☰, same order)"""
	var out := []
	var cut := str((UG.data().get("kopf", {}) as Dictionary).get("schmal_ab", "lang"))
	var past := false
	for b in knoepfe():
		var id := str(b.get("id"))
		if id == cut:
			past = true
		if id == "menu" or not (past and narrow()):
			if id != "dev" or dev_ok():
				out.append(id)
	return out


func dev_ok() -> bool:
	return main != null and main.has_method("_dev_card_ok") and bool(main._dev_card_ok())


func build(m) -> void:
	main = m
	add_theme_constant_override("separation", 6)
	alignment = BoxContainer.ALIGNMENT_END
	for c in get_children():
		c.queue_free()
	btns = {}
	for id in in_row():
		var b := _button(id)
		btns[id] = b
		add_child(b)


func _button(id: String) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(38, 38)
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = text(id)
	b.name = "Kopf_" + id
	var d := Control.new()
	d.set_anchors_preset(Control.PRESET_FULL_RECT)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(d)
	d.draw.connect(func(): _paint_icon(d, id))
	b.pressed.connect(func(): press(id, b))
	return b


func sound_on() -> bool:
	var si = main.get("simint") if main != null else null
	return si == null or not bool(si.get("spk_mute"))


func press(id: String, from: Control = null) -> void:
	"""what a button does - the same from the row and from the ☰ menu"""
	close_pop()
	match id:
		"help":
			if main.mehr != null:
				main.mehr.help_menu(from if from != null else self)
				var mn = main.mehr.get("_menu")
				if mn != null and is_instance_valid(mn) and from != null:      # below the header button (the bar's menu opens above)
					var r := from.get_global_rect()
					var vs: Vector2 = mn.get_viewport_rect().size
					mn.position = Vector2(clampf(r.end.x - mn.size.x, 4.0, vs.x - mn.size.x - 4.0), r.end.y + 4.0)
		"sound":
			var si = main.get("simint")
			if si != null:
				si.set_pc_sound(not sound_on())
				_toast(text("sound") + ": " + T.t("an" if sound_on() else "aus"))
			_redraw()
		"reload":
			if main.mehr != null:
				main.mehr.close_window()
			if main.has_method("_view_preset"):
				main._view_preset("head")                      # «Live» of the simulator: back to MoveEye's head
			if main.phone != null and main.phone.visible and main.phone.has_method("_navigate"):
				main.phone._navigate()                         # the phone view of MoveEye loads the page anew
			_toast(text("reload"))
		"lang":
			_lang_menu(from if from != null else self)
		"menu":
			open_menu(from if from != null else btns.get("menu", self))
		"fs":
			var full := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if full else DisplayServer.WINDOW_MODE_FULLSCREEN)
		"fold":
			set_folded(not folded)
		"dev":
			if dev_ok() and main.mehr != null:
				main.mehr.act("dev")


func set_folded(v: bool) -> void:
	"""▲ the bar (Einfach | Experte …) and the row with the search fold away; ▼ brings them back"""
	folded = v
	for n in [main.get("leiste"), main.get("ui_tb")]:
		if n != null and n is Control:
			(n as Control).visible = not v
	_redraw()


func _redraw() -> void:
	for b in btns.values():
		for c in (b as Control).get_children():
			(c as Control).queue_redraw()


func _toast(t: String) -> void:
	if main.mehr != null and main.mehr.has_method("toast"):
		main.mehr.toast(t)


# ---- the ☰ menu: header buttons that did not fit (same order), general ----
func _popup(anchor: Control) -> VBoxContainer:
	close_pop()
	_pop = PanelContainer.new()
	_pop.theme = main.ui_root.theme if main.ui_root != null else null
	_pop.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.98), UI.LINE, 12, 10, 1))
	var lay: Node = main.mehr.layer if main.mehr != null and main.mehr.get("layer") != null else main.ui_layer
	lay.add_child(_pop)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	_pop.add_child(v)
	_anchor = anchor
	_pop_out = 1.0
	return v


func _place() -> void:
	if _pop == null or _anchor == null:
		return
	_pop.reset_size()
	var vs: Vector2 = _pop.get_viewport_rect().size
	var r := _anchor.get_global_rect()
	_pop.position = Vector2(clampf(r.end.x - _pop.size.x, 4.0, vs.x - _pop.size.x - 4.0), r.end.y + 4.0)


func _h3(v: VBoxContainer, t: String) -> void:
	var l := UI.small(t.to_upper(), UI.MUT)
	l.add_theme_font_size_override("font_size", 11)
	v.add_child(l)


func _row(v: Control, id: String, label: String, fn: Callable) -> void:
	var b := Button.new()
	b.custom_minimum_size = Vector2(250, 36)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.text = "          " + label
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 13)
	var d := Control.new()
	d.position = Vector2(4, 4)
	d.size = Vector2(28, 28)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(d)
	d.draw.connect(func(): _paint_icon(d, id))
	b.pressed.connect(fn)
	v.add_child(b)


func open_menu(anchor: Control) -> void:
	if _pop != null and is_instance_valid(_pop) and _anchor == anchor:
		close_pop()
		return
	var v := _popup(anchor)
	var row := in_row()
	var over := []
	for b in knoepfe():
		var id := str(b.get("id"))
		if not row.has(id) and (id != "dev" or dev_ok()):
			over.append(id)
	if not over.is_empty():
		_h3(v, menu_text("head"))
		for id in over:
			_row(v, id, text(id), func(): press(id, anchor))
	_h3(v, menu_text("general"))
	if main.mehr != null:
		_row(v, "theme", T.t("Hell / Dunkel / Rotlicht"), func(): main.mehr.theme_next())
		_row(v, "chat", T.t("Rückmeldung an den Entwickler"), func(): close_pop(); main.mehr.act("feedback"))
		_row(v, "more", T.t("Alles unter «Mehr» im Bedienfeld"), func(): close_pop(); main.mehr.show_card())
	_place()


func _lang_menu(anchor: Control) -> void:
	var v := _popup(anchor)
	_h3(v, text("lang"))
	var cur := T.choice()
	for l in [["auto", T.t("wie MoveEye")]] + T.langs():
		var code := str(l[0])
		var b := Button.new()
		b.custom_minimum_size = Vector2(200, 34)
		b.toggle_mode = true
		b.button_pressed = (code == "auto" and cur == "") or code == cur
		b.text = str(l[1])
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(func():
			T.set_lang(code)
			close_pop()
			_redraw()
			_toast(text("lang") + ": " + str(l[1])))
		v.add_child(b)
	_place()


func close_pop() -> void:
	if _pop != null and is_instance_valid(_pop):
		_pop.queue_free()
	_pop = null


func _process(dt: float) -> void:
	if _pop == null or not is_instance_valid(_pop):
		return
	var mp := _pop.get_viewport().get_mouse_position()
	if _pop.get_global_rect().grow(12).has_point(mp) or (_anchor != null and is_instance_valid(_anchor) and _anchor.get_global_rect().grow(6).has_point(mp)):
		_pop_out = 1.0
	else:
		_pop_out -= dt
		if _pop_out <= 0.0:
			close_pop()


func state() -> Dictionary:
	"""for tests (control «kopf»): the order of the row and of the ☰ menu"""
	return {"row": in_row(), "all": knoepfe().map(func(b): return str(b.get("id"))), "narrow": narrow(), "folded": folded,
			"texts": knoepfe().map(func(b): return text(str(b.get("id"))))}


# ---- the drawn symbols (stroke 2 like ui_style.gd: no emoji font needed) ----
func _paint_icon(d: Control, id: String) -> void:
	var c := d.size / 2.0
	var col := UI.TXT
	var w := 2.0
	match id:
		"help":
			d.draw_arc(c + Vector2(0, -3), 4.5, PI, TAU + PI * 0.45, 14, col, w, true)
			d.draw_line(c + Vector2(1.6, 1.2), c + Vector2(0, 3.5), col, w, true)
			d.draw_circle(c + Vector2(0, 7.5), 1.3, col)
		"sound":
			var p := PackedVector2Array([c + Vector2(-6, 4), c + Vector2(-6, -1)])
			for i in 9:
				var a := PI + i * PI / 8.0
				p.append(c + Vector2(cos(a) * 6.0, -1.0 + sin(a) * 6.0))
			p.append_array([c + Vector2(6, 4), c + Vector2(7.5, 6), c + Vector2(-7.5, 6), c + Vector2(-6, 4)])
			d.draw_polyline(p, col, w, true)
			d.draw_arc(c + Vector2(0, 7.5), 2.0, 0, PI, 6, col, w, true)
			if not sound_on():
				d.draw_line(c + Vector2(-8, -8), c + Vector2(8, 8), col, w, true)
		"reload":
			d.draw_arc(c, 7.0, -PI * 0.25, PI * 1.6, 20, col, w, true)
			var e := c + Vector2(cos(-PI * 0.25), sin(-PI * 0.25)) * 7.0
			d.draw_polyline(PackedVector2Array([e + Vector2(-4.5, -0.5), e, e + Vector2(0.5, 4.5)]), col, w, true)
		"lang":
			var f := ThemeDB.fallback_font
			var s := T.lang().to_upper()
			var tw := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
			d.draw_string(f, c + Vector2(-tw / 2.0, 5), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, col)
		"menu":
			for y in [-5.0, 0.0, 5.0]:
				d.draw_line(c + Vector2(-7, y), c + Vector2(7, y), col, w, true)
		"fs":
			for s in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1)]:
				var k: Vector2 = c + s * 7.0
				d.draw_polyline(PackedVector2Array([k - Vector2(s.x * 4.0, 0), k, k - Vector2(0, s.y * 4.0)]), col, w, true)
		"fold":
			var u := -1.0 if not folded else 1.0
			d.draw_polyline(PackedVector2Array([c + Vector2(-6, -u * 3), c + Vector2(0, u * 3), c + Vector2(6, -u * 3)]), col, w, true)
		"dev":
			d.draw_line(c + Vector2(-7, 7), c + Vector2(1.5, -1.5), col, 3.0, true)
			d.draw_arc(c + Vector2(4.5, -4.5), 4.2, -PI / 4.0 + 0.95, -PI / 4.0 + TAU - 0.95, 16, col, 2.4, true)
		"theme":
			d.draw_arc(c, 7.0, 0, TAU, 24, col, w, true)
			var hp := PackedVector2Array()
			for i in 13:
				var a := -PI / 2.0 + i * PI / 12.0
				hp.append(c + Vector2(cos(a), sin(a)) * 7.0)
			d.draw_colored_polygon(hp, col)
		"chat":
			d.draw_rect(Rect2(c + Vector2(-8, -6), Vector2(16, 10)), col, false, w)
			d.draw_polyline(PackedVector2Array([c + Vector2(-4, 4), c + Vector2(-5, 8), c + Vector2(0, 4)]), col, w, true)
		"more":
			for x in [-6.0, 0.0, 6.0]:
				d.draw_circle(c + Vector2(x, 0), 1.8, col)
