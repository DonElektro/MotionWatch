extends RefCounted
## The look of the web page of Motion Watch for the window of the simulator (from 3D-1.13): the same colours (dark blue-grey,
## cards with round corners, blue accent), small spaced capitals as headings, buttons like on the page.

const BG := Color("#0a0e14")
const PANEL := Color("#111822")
const PANEL2 := Color("#151e2b")
const LINE := Color("#1f2b3a")
const TXT := Color("#e8eef5")
const MUT := Color("#8a9bb0")
const ACC := Color("#3b8cff")
const GRN := Color("#3fcf6b")
const ORG := Color("#f59a4a")
const RED := Color("#ff4d4d")
const FIELD := Color("#0c121a")
const BTN2 := Color("#1a2433")


static func box(bg: Color, border := LINE, r := 10, pad := 8, bw := 1) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(bw)
	s.set_corner_radius_all(r)
	s.content_margin_left = pad + 2
	s.content_margin_right = pad + 2
	s.content_margin_top = pad - 2
	s.content_margin_bottom = pad - 2
	s.anti_aliasing = true
	return s


static func _buttons(t: Theme, kind: String) -> void:
	t.set_stylebox("normal", kind, box(BTN2))
	t.set_stylebox("hover", kind, box(BTN2.lightened(0.07), LINE.lightened(0.25)))
	t.set_stylebox("pressed", kind, box(ACC.darkened(0.25), ACC))
	t.set_stylebox("hover_pressed", kind, box(ACC.darkened(0.15), ACC))
	t.set_stylebox("disabled", kind, box(BTN2.darkened(0.25), LINE))
	var f := box(Color(0, 0, 0, 0), ACC, 10, 8, 1)
	f.draw_center = false
	t.set_stylebox("focus", kind, f)
	t.set_color("font_color", kind, TXT)
	t.set_color("font_hover_color", kind, Color.WHITE)
	t.set_color("font_pressed_color", kind, Color.WHITE)
	t.set_color("font_hover_pressed_color", kind, Color.WHITE)
	t.set_color("font_focus_color", kind, TXT)
	t.set_color("font_disabled_color", kind, MUT.darkened(0.2))


static func theme() -> Theme:
	var t := Theme.new()
	t.default_font_size = 14
	_buttons(t, "Button")
	_buttons(t, "OptionButton")
	for kind in ["CheckBox", "CheckButton"]:
		var e := StyleBoxEmpty.new()
		e.content_margin_top = 3
		e.content_margin_bottom = 3
		for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
			t.set_stylebox(st, kind, e)
		t.set_color("font_color", kind, TXT)
		t.set_color("font_hover_color", kind, Color.WHITE)
		t.set_color("font_pressed_color", kind, TXT)
		t.set_color("font_hover_pressed_color", kind, Color.WHITE)
		t.set_color("font_focus_color", kind, TXT)
	t.set_color("font_color", "Label", TXT)
	t.set_stylebox("normal", "LineEdit", box(FIELD, LINE, 8))
	t.set_stylebox("focus", "LineEdit", box(FIELD, ACC, 8))
	t.set_color("font_color", "LineEdit", TXT)
	t.set_color("font_placeholder_color", "LineEdit", MUT.darkened(0.2))
	var track := box(LINE, LINE, 3, 2, 0)
	track.content_margin_top = 2
	track.content_margin_bottom = 2
	t.set_stylebox("slider", "HSlider", track)
	var fill := box(ACC, ACC, 3, 2, 0)
	fill.content_margin_top = 2
	fill.content_margin_bottom = 2
	t.set_stylebox("grabber_area", "HSlider", fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", fill)
	t.set_stylebox("panel", "PopupMenu", box(PANEL2, LINE, 10, 6))
	t.set_stylebox("hover", "PopupMenu", box(ACC.darkened(0.3), ACC.darkened(0.3), 6, 4, 0))
	t.set_color("font_color", "PopupMenu", TXT)
	t.set_color("font_hover_color", "PopupMenu", Color.WHITE)
	t.set_stylebox("panel", "PanelContainer", box(PANEL2, LINE, 14, 12))
	var sb := box(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 4, 0, 0)
	t.set_stylebox("scroll", "VScrollBar", sb)
	t.set_stylebox("grabber", "VScrollBar", box(LINE, LINE, 4, 0, 0))
	t.set_stylebox("grabber_highlight", "VScrollBar", box(LINE.lightened(0.2), LINE, 4, 0, 0))
	t.set_stylebox("grabber_pressed", "VScrollBar", box(ACC, ACC, 4, 0, 0))
	return t


static func primary(b: Button) -> void:
	"""the blue main button of a card (like «Simulation ausschalten» on the page)"""
	b.add_theme_stylebox_override("normal", box(ACC, ACC))
	b.add_theme_stylebox_override("hover", box(ACC.lightened(0.12), ACC.lightened(0.12)))
	b.add_theme_stylebox_override("pressed", box(ACC.darkened(0.2), ACC))
	b.add_theme_stylebox_override("disabled", box(ACC.darkened(0.5), ACC.darkened(0.5)))
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.6))


static func heading_font() -> FontVariation:
	var fv := FontVariation.new()
	fv.base_font = ThemeDB.fallback_font
	fv.variation_embolden = 0.7
	fv.spacing_glyph = 1
	return fv


static func heading(text: String) -> Label:
	"""small spaced capitals, like the card titles on the page"""
	var l := Label.new()
	l.text = text.to_upper()
	l.add_theme_font_override("font", heading_font())
	l.add_theme_font_size_override("font_size", 11)
	l.add_theme_color_override("font_color", MUT)
	return l


static func card(parent: Control) -> VBoxContainer:
	"""a card (round corners, line); returns the box to put things into"""
	var c := PanelContainer.new()
	parent.add_child(c)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	c.add_child(v)
	return v


static func fold_card(parent: Control, title: String, open: bool, icon := "") -> VBoxContainer:
	"""a card whose heading opens / closes it (▸ / ▾ on the right, green when open - as on the page); from 3D-3.5 with a
	drawn symbol in front of the name"""
	var v := card(parent)
	var hdr := Button.new()
	hdr.flat = true
	hdr.focus_mode = Control.FOCUS_NONE
	hdr.custom_minimum_size = Vector2(0, 22)
	var e := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		hdr.add_theme_stylebox_override(st, e)
	v.add_child(hdr)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hdr.add_child(row)
	var ic: Control = null
	if icon != "":
		row.add_theme_constant_override("separation", 8)
		ic = group_icon(icon)
		row.add_child(ic)
	var h := heading(title)
	h.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if icon != "":
		h.add_theme_font_size_override("font_size", 12)
		h.add_theme_color_override("font_color", TXT)
		h.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(h)
	var arrow := Label.new()
	arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(arrow)
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", 6)
	v.add_child(body)
	var paint := func():
		arrow.text = "▾" if body.visible else "▸"
		arrow.add_theme_color_override("font_color", GRN if body.visible else MUT)
	body.visible = open
	paint.call()
	hdr.pressed.connect(func():
		body.visible = not body.visible
		paint.call())
	body.set_meta("card", v.get_parent())            # for «alle auf / zu», the search and Simple / Expert
	body.set_meta("paint", paint)
	body.set_meta("title", title)
	body.set_meta("head", h)
	if ic != null:
		body.set_meta("icon", ic)
	return body


static func sub_fold(parent: Control, title: String, open: bool) -> VBoxContainer:
	"""a part inside a card (3D-3.5): a thin line, the name with ▸ / ▾, the settings a bit indented"""
	var wrap := VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 4)
	parent.add_child(wrap)
	var sep := ColorRect.new()
	sep.color = LINE
	sep.custom_minimum_size = Vector2(0, 1)
	wrap.add_child(sep)
	var hdr := Button.new()
	hdr.flat = true
	hdr.focus_mode = Control.FOCUS_NONE
	hdr.alignment = HORIZONTAL_ALIGNMENT_LEFT
	hdr.add_theme_font_size_override("font_size", 13)
	hdr.add_theme_color_override("font_color", MUT)
	hdr.add_theme_color_override("font_hover_color", TXT)
	var e := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		hdr.add_theme_stylebox_override(st, e)
	wrap.add_child(hdr)
	var mc := MarginContainer.new()
	mc.add_theme_constant_override("margin_left", 10)
	wrap.add_child(mc)
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", 6)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mc.add_child(body)
	var paint := func():
		hdr.text = ("▾  " if mc.visible else "▸  ") + title
		hdr.add_theme_color_override("font_color", TXT if mc.visible else MUT)
	mc.visible = open
	paint.call()
	hdr.pressed.connect(func():
		mc.visible = not mc.visible
		paint.call())
	body.set_meta("wrap", wrap)
	body.set_meta("fold", mc)
	body.set_meta("paint", paint)
	body.set_meta("title", title)
	return body


static func set_sub_open(body: Control, open: bool) -> void:
	(body.get_meta("fold") as Control).visible = open
	body.get_meta("paint").call()


static func group_icon(kind: String) -> Control:
	"""a small drawn symbol for a card (no emoji font needed - the same on every PC)"""
	var d := Control.new()
	d.custom_minimum_size = Vector2(20, 20)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	d.draw.connect(func(): _draw_group_icon(d, kind))
	return d


static func _draw_group_icon(d: Control, kind: String) -> void:
	var c := Vector2(10, 10)
	var col: Color = d.get_meta("col", ACC)             # from 3D-3.16 a symbol can change its colour (connection: green)
	var w := 1.8
	var P := func(pts: Array) -> PackedVector2Array:
		var out := PackedVector2Array()
		for q in pts:
			out.append(c + q)
		return out
	match kind:
		"link":                                       # two links of a chain
			d.draw_arc(c + Vector2(-3.5, 0), 4.5, PI * 0.5, PI * 1.5, 10, col, w, true)
			d.draw_arc(c + Vector2(3.5, 0), 4.5, -PI * 0.5, PI * 0.5, 10, col, w, true)
			d.draw_line(c + Vector2(-3.5, -4.5), c + Vector2(-1, -4.5), col, w, true)
			d.draw_line(c + Vector2(-3.5, 4.5), c + Vector2(-1, 4.5), col, w, true)
			d.draw_line(c + Vector2(1, -4.5), c + Vector2(3.5, -4.5), col, w, true)
			d.draw_line(c + Vector2(1, 4.5), c + Vector2(3.5, 4.5), col, w, true)
			d.draw_line(c + Vector2(-3, 0), c + Vector2(3, 0), col, w, true)
		"camera":
			d.draw_rect(Rect2(c + Vector2(-8, -5), Vector2(16, 11)), col, false, w)
			d.draw_rect(Rect2(c + Vector2(-4, -8), Vector2(6, 3)), col, true)
			d.draw_arc(c + Vector2(0, 0.5), 3.2, 0, TAU, 16, col, w, true)
		"tools":                                      # spanner
			d.draw_line(c + Vector2(-6, 6), c + Vector2(2, -2), col, 2.6, true)
			d.draw_arc(c + Vector2(4, -4), 4.0, PI * 0.95, PI * 2.55, 14, col, w, true)
		"globe":
			d.draw_arc(c, 8, 0, TAU, 24, col, w, true)
			d.draw_line(c + Vector2(-8, 0), c + Vector2(8, 0), col, 1.4, true)
			d.draw_arc(c, 8, 0, TAU, 24, col, w, true)
			var e := PackedVector2Array()
			for i in range(25):
				var a := TAU * i / 24.0
				e.append(c + Vector2(cos(a) * 3.6, sin(a) * 8))
			d.draw_polyline(e, col, 1.4, true)
		"cloud":
			d.draw_arc(c + Vector2(-3, 1), 4, PI * 0.5, PI * 1.6, 10, col, w, true)
			d.draw_arc(c + Vector2(1, -2), 5, PI * 1.05, PI * 2.0, 12, col, w, true)
			d.draw_arc(c + Vector2(5, 2), 3, PI * 1.5, PI * 2.5, 8, col, w, true)
			d.draw_line(c + Vector2(-3, 5), c + Vector2(5, 5), col, w, true)
			d.draw_line(c + Vector2(-2, 8), c + Vector2(-3, 10), col, 1.4, true)
			d.draw_line(c + Vector2(2, 8), c + Vector2(1, 10), col, 1.4, true)
		"person":
			d.draw_arc(c + Vector2(0, -5), 3, 0, TAU, 14, col, w, true)
			d.draw_arc(c + Vector2(0, 8), 7, PI * 1.1, PI * 1.9, 14, col, w, true)
			d.draw_line(c + Vector2(-6.2, 4.6), c + Vector2(6.2, 4.6), col, w, true)
		"lens":                                       # an eye
			d.draw_arc(c + Vector2(0, 6), 10, PI * 1.22, PI * 1.78, 14, col, w, true)
			d.draw_arc(c + Vector2(0, -6), 10, PI * 0.22, PI * 0.78, 14, col, w, true)
			d.draw_circle(c, 2.6, col)
		"bell":
			d.draw_polyline(P.call([Vector2(-6, 4), Vector2(-5, -2), Vector2(-3, -6), Vector2(0, -7), Vector2(3, -6), Vector2(5, -2), Vector2(6, 4), Vector2(-6, 4)]), col, w, true)
			d.draw_circle(c + Vector2(0, 7), 1.8, col)
		"pad":                                        # game pad
			d.draw_rect(Rect2(c + Vector2(-9, -5), Vector2(18, 10)), col, false, w)
			d.draw_line(c + Vector2(-6, 0), c + Vector2(-2, 0), col, w, true)
			d.draw_line(c + Vector2(-4, -2), c + Vector2(-4, 2), col, w, true)
			d.draw_circle(c + Vector2(3, -1), 1.3, col)
			d.draw_circle(c + Vector2(6, 1.5), 1.3, col)
		"target":
			d.draw_arc(c, 7.5, 0, TAU, 24, col, w, true)
			d.draw_arc(c, 3.5, 0, TAU, 16, col, w, true)
			d.draw_line(c + Vector2(0, -10), c + Vector2(0, -5), col, w, true)
			d.draw_line(c + Vector2(0, 5), c + Vector2(0, 10), col, w, true)
			d.draw_line(c + Vector2(-10, 0), c + Vector2(-5, 0), col, w, true)
			d.draw_line(c + Vector2(5, 0), c + Vector2(10, 0), col, w, true)
		"check":
			d.draw_rect(Rect2(c + Vector2(-7, -7), Vector2(14, 14)), col, false, w)
			d.draw_polyline(P.call([Vector2(-4, 0), Vector2(-1, 3), Vector2(4, -3)]), col, 2.2, true)
		"gear":
			for i in range(8):
				var a := TAU * i / 8.0
				d.draw_line(c + Vector2(cos(a), sin(a)) * 5.5, c + Vector2(cos(a), sin(a)) * 8.5, col, 2.6, true)
			d.draw_arc(c, 5.5, 0, TAU, 20, col, w, true)
			d.draw_arc(c, 2.2, 0, TAU, 12, col, 1.4, true)
		"track":                                      # tracked vehicle
			d.draw_rect(Rect2(c + Vector2(-9, -1), Vector2(18, 8)), col, false, w)
			for x in [-5, 0, 5]:
				d.draw_arc(c + Vector2(x, 3), 1.8, 0, TAU, 8, col, 1.4, true)
			d.draw_polyline(P.call([Vector2(-4, -1), Vector2(-4, -6), Vector2(4, -6), Vector2(4, -1)]), col, w, true)
		"keys":
			d.draw_rect(Rect2(c + Vector2(-9, -5), Vector2(18, 11)), col, false, w)
			for x in [-5, -1, 3]:
				d.draw_rect(Rect2(c + Vector2(x, -2), Vector2(2, 2)), col, true)
			d.draw_line(c + Vector2(-4, 3), c + Vector2(4, 3), col, w, true)
		_:
			d.draw_circle(c, 4, col)


static func set_open(body: Control, open: bool) -> void:
	body.visible = open
	var p = body.get_meta("paint", null)
	if p != null:
		p.call()


static func icon_button(kind: String, tip: String) -> Button:
	"""a square button with a drawn symbol like on the page of Motion Watch (no font needed):
	hide «⟩», groups only (two bars), expand all (arrows out), collapse all (arrows in)"""
	var b := Button.new()
	b.custom_minimum_size = Vector2(38, 38)
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_NONE
	var d := Control.new()
	d.set_anchors_preset(Control.PRESET_FULL_RECT)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(d)
	d.draw.connect(func(): _draw_icon(d, kind))
	return b


static func _draw_icon(d: Control, kind: String) -> void:
	var c := d.size / 2.0
	var col := TXT
	var w := 2.0
	if kind == "hide":
		d.draw_polyline(PackedVector2Array([c + Vector2(-3, -8), c + Vector2(4, 0), c + Vector2(-3, 8)]), col, w, true)
	elif kind == "show":
		d.draw_polyline(PackedVector2Array([c + Vector2(3, -8), c + Vector2(-4, 0), c + Vector2(3, 8)]), col, w, true)
	elif kind == "groups":
		d.draw_rect(Rect2(c + Vector2(-8, -7), Vector2(16, 5)), col, false, w)
		d.draw_rect(Rect2(c + Vector2(-8, 2), Vector2(16, 5)), col, false, w)
	elif kind == "open":
		d.draw_polyline(PackedVector2Array([c + Vector2(-5, -3), c + Vector2(0, -8), c + Vector2(5, -3)]), col, w, true)
		d.draw_polyline(PackedVector2Array([c + Vector2(-5, 3), c + Vector2(0, 8), c + Vector2(5, 3)]), col, w, true)
	elif kind == "close":
		d.draw_polyline(PackedVector2Array([c + Vector2(-5, -8), c + Vector2(0, -3), c + Vector2(5, -8)]), col, w, true)
		d.draw_polyline(PackedVector2Array([c + Vector2(-5, 8), c + Vector2(0, 3), c + Vector2(5, 8)]), col, w, true)


static func search_field(placeholder: String) -> LineEdit:
	"""the search field with a drawn magnifier on the left"""
	var e := LineEdit.new()
	e.placeholder_text = placeholder
	e.clear_button_enabled = true
	e.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	e.custom_minimum_size = Vector2(0, 38)
	var n := box(FIELD, LINE, 10)
	n.content_margin_left = 34
	var f := box(FIELD, ACC, 10)
	f.content_margin_left = 34
	e.add_theme_stylebox_override("normal", n)
	e.add_theme_stylebox_override("focus", f)
	var d := Control.new()
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	d.position = Vector2(8, 9)
	d.size = Vector2(20, 20)
	e.add_child(d)
	d.draw.connect(func():
		d.draw_arc(Vector2(8, 8), 5.5, 0, TAU, 24, MUT, 2.0, true)
		d.draw_line(Vector2(12, 12), Vector2(17, 17), MUT, 2.2, true))
	return e


static func segment(left: String, right: String, right_on: bool, on_change: Callable) -> HBoxContainer:
	"""two buttons side by side, one of them blue (like «Einfach | Experte» at the bottom of the page)"""
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 0)
	var a := Button.new()
	var b := Button.new()
	for x in [a, b]:
		x.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		x.custom_minimum_size = Vector2(0, 40)
		x.focus_mode = Control.FOCUS_NONE
		h.add_child(x)
	a.text = left
	b.text = right
	var paint := func(r_on: bool):
		var on_box := box(ACC, ACC, 10)
		var off_box := box(FIELD, LINE, 10)
		on_box.corner_radius_top_right = 0 if not r_on else 10
		var l_st: StyleBoxFlat = off_box.duplicate() if r_on else on_box.duplicate()
		var r_st: StyleBoxFlat = on_box.duplicate() if r_on else off_box.duplicate()
		l_st.corner_radius_top_right = 0
		l_st.corner_radius_bottom_right = 0
		r_st.corner_radius_top_left = 0
		r_st.corner_radius_bottom_left = 0
		for st in ["normal", "hover", "pressed", "focus"]:
			a.add_theme_stylebox_override(st, l_st)
			b.add_theme_stylebox_override(st, r_st)
		a.add_theme_color_override("font_color", MUT if r_on else Color.WHITE)
		b.add_theme_color_override("font_color", Color.WHITE if r_on else MUT)
		a.add_theme_color_override("font_hover_color", Color.WHITE)
		b.add_theme_color_override("font_hover_color", Color.WHITE)
	paint.call(right_on)
	a.pressed.connect(func():
		paint.call(false)
		on_change.call(false))
	b.pressed.connect(func():
		paint.call(true)
		on_change.call(true))
	return h


static func small(text: String, col := MUT) -> Label:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", 12)
	l.add_theme_color_override("font_color", col)
	return l
