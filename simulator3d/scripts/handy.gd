extends Node
## «Handy-Modus» (Besitzer 15.11.2026): auf dem Handy (Browser-Demo und Simulator in einem schmalen Fenster, auch quer)
## eine eigene, einfache Oberfläche statt Bedienfeld, Leiste unten und schwebender Fenster:
##   * die 3D-Ansicht füllt den Bildschirm
##   * eine Leiste mit 5 grossen Knöpfen: Szene · Tageszeit · Besuch · Schutz · ☰ Mehr (hoch unten, quer rechts)
##   * jeder Knopf öffnet ein Blatt VON UNTEN (wie die Unterseiten-Fenster «Von unten» in MoveEye), immer nur eines;
##     zu mit ✕, Griff nach unten wischen, Tipp auf den abgedunkelten Hintergrund, Zurück (Esc / Zurück-Geste Android)
##   * Karte, Gerät und Kamera sind kleine runde Knöpfe am linken Rand: Tipp = gross zeigen, nochmals = weg
##   * Listen einspaltig, ganze Breite, Text bricht um
##   * Steuerkreuz (Kopf drehen) unten rechts (quer: links der Leiste), Hinweis Schutz / Alarm oben
## Erkennung: kurze Seite der Ansicht < SHORT Punkte; Wahl in «Mehr → Darstellung»: Automatisch / Handy / Tablet-PC
## (user://handy.json). Aus = alles wie bisher (Bedienfeld, Leiste, Fenster kommen zurück).
## Die schwebenden Fenster bleiben in fenster.gd angemeldet; im Handy-Modus blendet fenster.handy_hide sie aus, und für
## «gross zeigen» hängt dieser Teil den Inhalt (Karte, Gerät, Kameras) kurz in seine eigene Karte und danach zurück.
## Tests: /control {"action": "handy", "do": "info" | "mode" (value) | "sheet" (id) | "close" | "win" (id, on)}

const UI = preload("res://scripts/ui_style.gd")
const Q = preload("res://scripts/quick.gd")
const W = preload("res://scripts/worlds.gd")
const Tpl = preload("res://scripts/templates.gd")
const T = preload("res://scripts/i18n.gd")

const FILE := "user://handy.json"
const SHORT := 500.0                   # kürzere Seite unter so vielen Punkten = Handy
const BAR_H := 66.0                    # Leiste unten (hoch)
const BAR_W := 78.0                    # Leiste rechts (quer)
const TAP := 44.0                      # kleinste Tippfläche
const SHEETS := [["scene", "globe", "Szene"], ["time", "clock", "Tageszeit"], ["visit", "person", "Besuch"],
		["protect", "shield", "Schutz"], ["more", "menu", "Mehr"]]
const WINS := [["map", "map", "Karte"], ["geraet", "keys", "Gerät"], ["kameras", "camera", "Kamera"]]

var main
var mode := "auto"                     # "auto" | "phone" | "tablet"
var on := false
var layer: CanvasLayer
var root: Control
var bar: PanelContainer
var bar_box: BoxContainer
var bar_btns := {}
var dim: ColorRect
var sheet: PanelContainer
var sheet_title: Label
var sheet_scroll: ScrollContainer
var sheet_body: VBoxContainer
var cur := ""
var big_id := ""
var big: PanelContainer
var big_title: Label
var big_scroll: ScrollContainer
var _big_home := {}
var win_box: VBoxContainer
var win_btns := {}
var dpad: Control
var top: PanelContainer
var top_l: Label
var panel_x: Button                    # «✕» über dem Bedienfeld (Mehr → Alle Einstellungen)
var _vs := Vector2.ZERO
var _was := {}
var _drag_y0 := -1.0
var _drag_off := 0.0
var _hold := ""
var _hold_t := 0.0
var _t := 0.0
var _search: LineEdit
var _scene_list: VBoxContainer
var _visit_l: Label


func _ready() -> void:
	process_priority = 900                              # nach den anderen Teilen (sie zeigen ihre Knöpfe wieder)
	_load()
	_build()
	layer.visible = false
	if OS.has_feature("web"):                           # Zurück-Geste / Zurück-Taste des Browsers schliesst das Blatt
		_pop_cb = JavaScriptBridge.create_callback(_on_pop)
		JavaScriptBridge.get_interface("window").addEventListener("popstate", _pop_cb)


var _pop_cb                                             # JavaScriptObject (muss gehalten werden)
var _hist := false                                      # ein Eintrag im Verlauf des Browsers steht für das offene Blatt
var _skip_pop := false


func _on_pop(_args: Array) -> void:
	if _skip_pop:
		_skip_pop = false
		return
	_hist = false
	_back()


func _web_history() -> void:
	"""ein offenes Blatt / grosses Fenster = ein Schritt im Verlauf: «Zurück» (Geste, Taste) schliesst es statt die Seite"""
	var open: bool = cur != "" or big_id != "" or panel_x.visible
	if open and not _hist:
		_hist = true
		JavaScriptBridge.eval("history.pushState({moveeye: 1}, '')", true)
	elif not open and _hist:
		_hist = false
		_skip_pop = true
		JavaScriptBridge.eval("history.back()", true)


func _load() -> void:
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY and str(d.get("mode", "auto")) in ["auto", "phone", "tablet"]:
			mode = str(d["mode"])


func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"mode": mode}))


func set_mode(m: String) -> void:
	if m in ["auto", "phone", "tablet"]:
		mode = m
		_save()


func view_size() -> Vector2:
	return main.get_viewport().get_visible_rect().size


func wanted() -> bool:
	var wd = main.get("web_demo")
	if wd != null:                                      # Browser: nach den Punkten des Handys (web_demo.gd vergrössert sonst)
		return wd.phone()
	var vs := view_size()
	return mode == "phone" or (mode == "auto" and minf(vs.x, vs.y) < SHORT)


func landscape() -> bool:
	var vs := view_size()
	return vs.x > vs.y


# ---- bauen ---------------------------------------------------------------------------------------------------------------
func _round(r: int, bg: Color, border := UI.LINE, bw := 1) -> StyleBoxFlat:
	var sb := UI.box(bg, border, r, 0, bw)
	return sb


func _style_btn(b: Button, bg: Color, r := 12, border := UI.LINE) -> void:
	for st in ["normal", "focus"]:
		b.add_theme_stylebox_override(st, _round(r, bg, border))
	b.add_theme_stylebox_override("hover", _round(r, bg.lightened(0.08), border))
	b.add_theme_stylebox_override("pressed", _round(r, UI.ACC.darkened(0.45), UI.ACC))


func _icon(kind: String, k := 1.3) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(20, 20) * k
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if kind == "menu":                                   # ☰ gezeichnet (keine Emoji-Schrift nötig)
		c.draw.connect(func():
			for i in range(3):
				var y: float = (5.0 + i * 5.0) * k
				c.draw_line(Vector2(3.0 * k, y), Vector2(17.0 * k, y), UI.TXT, 2.0 * k, true))
		return c
	var ic := UI.group_icon(kind)
	ic.scale = Vector2(k, k)
	c.add_child(ic)
	return c


func _close_btn(cb: Callable) -> Button:
	var x := Button.new()
	x.text = "✕"
	x.tooltip_text = T.t("Schliessen")
	x.custom_minimum_size = Vector2(TAP, TAP)
	x.focus_mode = Control.FOCUS_NONE
	x.add_theme_font_size_override("font_size", 20)
	_style_btn(x, UI.BTN2, 22)
	x.pressed.connect(cb)
	return x


func _build() -> void:
	layer = CanvasLayer.new()
	layer.layer = 50                                     # über dem Bedienfeld und den Fenstern, unter «Mehr» (60)
	add_child(layer)
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = main.ui_root.theme if main.ui_root != null else UI.theme()
	layer.add_child(root)
	# Hinweis oben (Schutz / Alarm)
	top = PanelContainer.new()
	top.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.82), UI.LINE, 18, 10, 1))
	top.mouse_filter = Control.MOUSE_FILTER_STOP
	top_l = Label.new()
	top_l.add_theme_font_size_override("font_size", 14)
	top_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top.add_child(top_l)
	top.gui_input.connect(func(ev): if _is_tap(ev): _sheet("protect"))
	root.add_child(top)
	# runde Fenster-Knöpfe am Rand
	win_box = VBoxContainer.new()
	win_box.add_theme_constant_override("separation", 10)
	root.add_child(win_box)
	for d in WINS:
		var b := Button.new()
		b.custom_minimum_size = Vector2(48, 48)
		b.focus_mode = Control.FOCUS_NONE
		b.tooltip_text = T.t(d[2])
		var ic := _icon(d[1], 1.25)
		ic.position = Vector2(11, 11)
		b.add_child(ic)
		var id: String = d[0]
		b.pressed.connect(func(): show_win(id, big_id != id))
		win_box.add_child(b)
		win_btns[id] = b
	# Steuerkreuz
	dpad = Control.new()
	dpad.custom_minimum_size = Vector2(TAP * 3 + 8, TAP * 3 + 8)
	dpad.size = dpad.custom_minimum_size
	dpad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(dpad)
	var bg := Panel.new()
	bg.add_theme_stylebox_override("panel", _round(80, Color(UI.BG, 0.45), Color(UI.LINE, 0.8)))
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dpad.add_child(bg)
	for d in [["up", "▲", Vector2(1, 0)], ["left", "◀", Vector2(0, 1)], ["center", "●", Vector2(1, 1)], ["right", "▶", Vector2(2, 1)], ["down", "▼", Vector2(1, 2)]]:
		var b := Button.new()
		b.text = d[1]
		b.focus_mode = Control.FOCUS_NONE
		b.position = Vector2(4, 4) + (d[2] as Vector2) * TAP
		b.size = Vector2(TAP, TAP)
		b.add_theme_font_size_override("font_size", 16 if d[0] != "center" else 12)
		for st in ["normal", "hover", "focus"]:
			b.add_theme_stylebox_override(st, StyleBoxEmpty.new())
		b.add_theme_stylebox_override("pressed", _round(22, Color(UI.ACC, 0.45), UI.ACC))
		var dir: String = d[0]
		b.button_down.connect(func(): _hold = dir; _hold_t = 0.0)
		b.button_up.connect(func(): _hold = "")
		dpad.add_child(b)
	# Leiste
	bar = PanelContainer.new()
	bar.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(bar)
	# Abdunkeln + Blatt + grosses Fenster
	dim = ColorRect.new()
	dim.color = Color(0, 0, 0, 0.5)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.visible = false
	dim.gui_input.connect(func(ev): if _is_tap(ev): close())
	root.add_child(dim)
	_build_big()
	_build_sheet()
	panel_x = _close_btn(func(): _panel(false))
	panel_x.visible = false
	root.add_child(panel_x)
	_build_bar(false)


func _build_bar(side: bool) -> void:
	if bar_box != null:
		bar_box.queue_free()
	bar_btns.clear()
	bar_box = VBoxContainer.new() if side else HBoxContainer.new()
	bar_box.add_theme_constant_override("separation", 2)
	bar.add_child(bar_box)
	for d in SHEETS:
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.size_flags_vertical = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(TAP, TAP + 8)
		b.tooltip_text = T.t(d[2])
		var v := VBoxContainer.new()
		v.set_anchors_preset(Control.PRESET_FULL_RECT)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_theme_constant_override("separation", 2)
		b.add_child(v)
		var ic := _icon(d[1], 1.3)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		var l := Label.new()
		l.text = T.t(d[2])
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", 12)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(l)
		var id: String = d[0]
		b.pressed.connect(func(): _sheet(id) if cur != id else close())
		bar_box.add_child(b)
		bar_btns[id] = b


func _build_sheet() -> void:
	sheet = PanelContainer.new()
	var sb := UI.box(Color(UI.BG, 0.98), UI.LINE, 18, 0, 1)
	sb.corner_radius_bottom_left = 0
	sb.corner_radius_bottom_right = 0
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_bottom = 10
	sheet.add_theme_stylebox_override("panel", sb)
	sheet.visible = false
	sheet.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(sheet)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	sheet.add_child(v)
	var grab := Control.new()                            # der Griff: nach unten wischen = zu
	grab.custom_minimum_size = Vector2(0, 22)
	grab.mouse_filter = Control.MOUSE_FILTER_STOP
	grab.draw.connect(func(): grab.draw_line(Vector2(grab.size.x / 2 - 20, 12), Vector2(grab.size.x / 2 + 20, 12), UI.MUT, 5.0, true))
	grab.gui_input.connect(_drag_input)
	v.add_child(grab)
	var hd := HBoxContainer.new()
	hd.mouse_filter = Control.MOUSE_FILTER_STOP
	hd.gui_input.connect(_drag_input)
	v.add_child(hd)
	sheet_title = UI.heading("")
	sheet_title.add_theme_font_size_override("font_size", 18)
	sheet_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hd.add_child(sheet_title)
	hd.add_child(_close_btn(close))
	sheet_scroll = ScrollContainer.new()
	sheet_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sheet_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(sheet_scroll)
	sheet_body = VBoxContainer.new()
	sheet_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_body.add_theme_constant_override("separation", 8)
	sheet_scroll.add_child(sheet_body)


func _build_big() -> void:
	big = PanelContainer.new()
	big.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.97), UI.LINE, 16, 10, 1))
	big.visible = false
	big.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(big)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	big.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	big_title = UI.heading("")
	big_title.add_theme_font_size_override("font_size", 18)
	big_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	big_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hd.add_child(big_title)
	hd.add_child(_close_btn(func(): show_win(big_id, false)))
	big_scroll = ScrollContainer.new()
	big_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO   # breiter Inhalt: wischen, das Fenster bleibt im Bild
	big_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(big_scroll)


# ---- an / aus --------------------------------------------------------------------------------------------------------------
func _hideables() -> Array:
	return [main.view_bar, main.toolbar, main.phone, main.show_btn, main.cpu_pill]


func _set_on(v: bool) -> void:
	on = v
	layer.visible = v
	if main.fenster != null:
		main.fenster.handy_hide = v
	if main.sun != null and main.quality == "simple":    # Grafik «Handy» statt unscharfer Ansicht (main_start.handy_gfx)
		main._mod("start").handy_gfx(v)
		if not v:
			main._apply_quality()
	if v:
		_was.clear()
		for c in _hideables():
			if c != null and is_instance_valid(c):
				_was[c] = (c as CanvasItem).visible
				if not (c as CanvasItem).visibility_changed.is_connected(_rehide):
					(c as CanvasItem).visibility_changed.connect(_rehide.bind(c))   # auch zwischen zwei Bildern (Timer)
		main.show_panel(false)
	else:
		close()
		show_win(big_id, false)
		_panel(false)
		for c in _was:
			if is_instance_valid(c):
				(c as CanvasItem).visible = bool(_was[c])
		if main.show_btn != null and main.ui_root != null:
			main.show_btn.visible = not main.ui_root.visible
	print("handy: ", "an" if v else "aus", " (", mode, ", ", view_size(), ")")


func _rehide(c: CanvasItem) -> void:
	if on and is_instance_valid(c) and c.visible:
		c.set_deferred("visible", false)


func _process(dt: float) -> void:
	var w := wanted()
	if w != on:
		_set_on(w)
	if not on:
		return
	for c in _hideables():                              # andere Teile zeigen ihre Knöpfe wieder: im Handy-Modus nie
		if c != null and is_instance_valid(c) and (c as CanvasItem).visible:
			(c as CanvasItem).visible = false
	var vs := view_size()
	if vs != _vs:
		_vs = vs
		_build_bar(landscape())
	_layout()
	if _hold != "":
		_hold_t -= dt
		if _hold_t <= 0.0:
			_hold_t = 0.12
			if _hold == "center":
				main.mw_look("center")
				_hold = ""
			else:
				main.mw_look(_hold, 2.5)
	if _pop_cb != null:
		_web_history()
	_t -= dt
	if _t <= 0.0:
		_t = 0.4
		_paint()


func free_rect() -> Rect2:
	"""the room above the bar (portrait) / left of it (landscape) - where windows and panels must fit"""
	var vs := view_size()
	if landscape():
		return Rect2(Vector2.ZERO, Vector2(vs.x - BAR_W, vs.y))
	return Rect2(Vector2.ZERO, Vector2(vs.x, vs.y - BAR_H))


func _layout() -> void:
	var vs := view_size()
	var ls := landscape()
	if ls:
		bar.position = Vector2(vs.x - BAR_W, 0)
		bar.size = Vector2(BAR_W, vs.y)
		bar.add_theme_stylebox_override("panel", _bar_style(true))
		dpad.position = Vector2(vs.x - BAR_W - dpad.size.x - 10, vs.y - dpad.size.y - 10)
	else:
		bar.position = Vector2(0, vs.y - BAR_H)
		bar.size = Vector2(vs.x, BAR_H)
		bar.add_theme_stylebox_override("panel", _bar_style(false))
		dpad.position = Vector2(vs.x - dpad.size.x - 10, vs.y - BAR_H - dpad.size.y - 10)
	var fr := free_rect()
	top.reset_size()
	top.position = Vector2(roundf((fr.size.x - top.size.x) / 2.0), 10)
	win_box.position = Vector2(10, 64 if not ls else 10)
	var other: bool = main.get("waechter") != null and main.waechter.big_open   # ein anderes grosses Fenster ist offen
	dpad.visible = big_id == "" and cur == "" and not other and not panel_x.visible
	win_box.modulate.a = 0.0 if other or panel_x.visible else 1.0
	win_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for b in win_btns.values():
		(b as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE if other or panel_x.visible else Control.MOUSE_FILTER_STOP
	# Blatt von unten
	if sheet.visible:
		var sw: float = vs.x if not ls else minf(560.0, fr.size.x - 20.0)
		var maxh: float = vs.y * (0.86 if not ls else 0.94)
		var want: float = 22 + 50 + sheet_body.get_combined_minimum_size().y + 26
		var h: float = minf(maxh, maxf(want, 220.0)) if cur not in ["scene", "more"] else maxh
		sheet.size = Vector2(sw, h)
		sheet.position = Vector2(roundf((fr.size.x - sw) / 2.0) if ls else 0.0, vs.y - h + _drag_off)
	# grosses Fenster
	if big.visible:
		var bw: float
		var bh: float
		if ls:
			bh = vs.y - 20.0
			bw = minf(fr.size.x - 90.0, bh * 1.15)
			big.position = Vector2(70, 10)
		else:
			bw = vs.x - 20.0
			bh = minf(fr.size.y - 74.0, bw * 1.4)
			big.position = Vector2(10, 64)
		var inner: float = 0.0
		if big_scroll.get_child_count() > 0:
			inner = (big_scroll.get_child(0) as Control).get_combined_minimum_size().y
		var inner_w: float = 0.0
		if big_scroll.get_child_count() > 0:
			inner_w = (big_scroll.get_child(0) as Control).get_combined_minimum_size().x
		if ls and inner_w > 0.0:
			bw = minf(bw, maxf(inner_w + 22.0, 260.0))
		var sb_h: float = 14.0 if inner_w > bw - 22.0 else 0.0   # Platz für den Schiebebalken unten
		big.size = Vector2(bw, minf(bh, 44.0 + 6.0 + inner + 22.0 + sb_h) if inner > 0.0 else bh)
		if not ls:                                       # hoch: die runden Knöpfe rücken unter das grosse Fenster
			win_box.position = Vector2(10, big.position.y + big.size.y + 10)
		else:                                            # quer: der Hinweis oben («MoveEye (Demo) · Wachsam») bleibt lesbar
			var x0: float = big.position.x + big.size.x + 8.0
			if fr.size.x - x0 >= top.size.x + 8.0:       # rechts neben dem Fenster
				top.position = Vector2(roundf(x0 + (fr.size.x - x0 - top.size.x) / 2.0), 10)
			else:                                        # kein Platz daneben: das Fenster beginnt unter dem Hinweis
				var y0: float = top.position.y + top.size.y + 6.0
				big.position.y = y0
				big.size.y = minf(big.size.y, vs.y - y0 - 10.0)
	if panel_x.visible:
		panel_x.position = Vector2(8, 8)


func _bar_style(side: bool) -> StyleBoxFlat:
	var sb := UI.box(Color(UI.BG, 0.94), UI.LINE, 0, 4, 0)
	if side:
		sb.border_width_left = 1
	else:
		sb.border_width_top = 1
	return sb


func _paint() -> void:
	for k in bar_btns:
		var a: bool = cur == k
		_style_btn(bar_btns[k], UI.ACC.darkened(0.55) if a else Color(0, 0, 0, 0), 12, UI.ACC if a else Color(0, 0, 0, 0))
	for k in win_btns:
		var a: bool = big_id == k
		_style_btn(win_btns[k], UI.ACC.darkened(0.45) if a else Color(UI.BG, 0.8), 24, UI.ACC if a else UI.LINE)
	var st := _state()
	top_l.text = st[0]
	top.add_theme_stylebox_override("panel", UI.box(Color(UI.RED, 0.9) if st[1] == "alarm" else Color(UI.BG, 0.82),
			UI.RED if st[1] == "alarm" else UI.LINE, 18, 8, 1))
	if _visit_l != null and is_instance_valid(_visit_l):
		_visit_l.text = T.t("%d Besucher da") % main.visitors.get_child_count()


func _state() -> Array:
	"""[text, kind] for the pill at the top: alarm / armed / off / demo"""
	var wd = main.get("web_demo")
	if wd != null:
		if bool(wd.get("alarm")):
			return ["⚠ " + T.t("ALARM – Person erkannt") + " · " + T.t("tippen"), "alarm"]
		return ["● MoveEye (Demo) · " + (T.t("Wachsam") if bool(wd.get("armed")) else T.t("Schutz aus")), "ok"]
	if main.now() - float(main.mw_t) < 3.0:
		if bool(main.mw.get("alarm", false)):
			return ["⚠ " + T.t("ALARM"), "alarm"]
		return ["● MoveEye · " + (T.t("Schutz an") if bool(main.mw.get("armed", false)) else T.t("Schutz aus")), "ok"]
	return ["○ " + T.t("MoveEye nicht verbunden"), "off"]


# ---- Blätter --------------------------------------------------------------------------------------------------------------
func _sheet(id: String) -> void:
	show_win(big_id, false)
	_panel(false)
	cur = id
	_drag_off = 0.0
	for c in sheet_body.get_children():
		c.queue_free()
	_search = null
	_scene_list = null
	_visit_l = null
	var title := ""
	match id:
		"scene":
			title = "Szene wählen"
			_fill_scene()
		"time":
			title = "Tageszeit und Wetter"
			_fill_time()
		"visit":
			title = "Besuch schicken"
			_fill_visit()
		"protect":
			title = "Schutz"
			_fill_protect()
		"more":
			title = "Mehr"
			_fill_more()
	sheet_title.text = T.t(title)
	sheet.visible = true
	dim.visible = true
	sheet_scroll.scroll_vertical = 0
	_paint()
	_layout()


func close() -> void:
	cur = ""
	_drag_off = 0.0
	if sheet != null:
		sheet.visible = false
		dim.visible = false
	if bar_btns.size() > 0:
		_paint()


func _is_tap(ev: InputEvent) -> bool:
	return (ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and not ev.pressed) or (ev is InputEventScreenTouch and not ev.pressed)


func _drag_input(ev: InputEvent) -> void:
	"""Griff / Kopf des Blatts nach unten ziehen: mehr als 90 Punkte = zu, sonst zurück"""
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			_drag_y0 = ev.global_position.y
		else:
			if _drag_off > 90.0:
				close()
			_drag_y0 = -1.0
			_drag_off = 0.0
	elif ev is InputEventMouseMotion and _drag_y0 >= 0.0:
		_drag_off = maxf(0.0, ev.global_position.y - _drag_y0)


func _input(ev: InputEvent) -> void:
	if not on:
		return
	if ev.is_action_pressed("ui_cancel") and (cur != "" or big_id != "" or panel_x.visible):
		_back()
		get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST and on:   # Zurück-Geste (Android); im Browser über web.gd (Verlauf)
		_back()


func _back() -> bool:
	if cur != "":
		close()
	elif big_id != "":
		show_win(big_id, false)
	elif panel_x.visible:
		_panel(false)
	else:
		return false
	return true


func _section(t: String) -> void:
	var l := UI.small(T.t(t).to_upper(), UI.MUT)
	l.add_theme_font_size_override("font_size", 11)
	sheet_body.add_child(l)


func _row(parent: Control, title: String, sub: String, cb: Callable, mark := false, green := false) -> Control:
	"""one entry of a list: full width, the text wraps; the whole card is the button (at least 52 high)"""
	var pc := PanelContainer.new()
	var bg: Color = UI.PANEL2.lerp(UI.GRN, 0.10) if green else UI.PANEL2
	pc.add_theme_stylebox_override("panel", UI.box(bg if not mark else UI.ACC.darkened(0.6), UI.ACC if mark else UI.LINE, 12, 12, 1 if not mark else 2))
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pc.custom_minimum_size = Vector2(0, 52)
	parent.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(v)
	var a := Label.new()
	a.text = ("● " if mark else "") + T.t(title)
	a.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	a.add_theme_font_size_override("font_size", 16)
	if green:
		a.add_theme_color_override("font_color", Color(0.55, 0.95, 0.6))
	a.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(a)
	if sub != "":
		var s := Label.new()
		s.text = T.t(sub)
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		s.add_theme_font_size_override("font_size", 13)
		s.add_theme_color_override("font_color", UI.MUT)
		s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(s)
	var b := Button.new()                                 # lies over the whole card (PanelContainer stacks its children)
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_PASS           # PASS: wischen scrollt die Liste weiter
	for st in ["normal", "hover", "focus"]:
		b.add_theme_stylebox_override(st, StyleBoxEmpty.new())
	b.add_theme_stylebox_override("pressed", UI.box(Color(UI.ACC, 0.18), UI.ACC, 12, 0, 1))
	b.pressed.connect(cb)
	pc.add_child(b)
	return pc


func _grid(cols: int) -> GridContainer:
	var g := GridContainer.new()
	g.columns = cols
	g.add_theme_constant_override("h_separation", 8)
	g.add_theme_constant_override("v_separation", 8)
	g.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_body.add_child(g)
	return g


func _big_btn(parent: Control, text: String, cb: Callable, active := false) -> Button:
	var b := Button.new()
	b.text = T.t(text)
	b.custom_minimum_size = Vector2(0, 52)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.focus_mode = Control.FOCUS_NONE
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.add_theme_font_size_override("font_size", 15)
	_style_btn(b, UI.ACC.darkened(0.55) if active else UI.BTN2, 12, UI.ACC if active else UI.LINE)
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _fill_scene() -> void:
	var l := UI.small(T.t("Tippen = Szene laden (Besucher kommen von selbst). Grün = neu."))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sheet_body.add_child(l)
	_search = UI.search_field(T.t("Szene suchen …"))
	_search.custom_minimum_size.y = TAP
	_search.text_changed.connect(func(_s): _paint_scenes())
	sheet_body.add_child(_search)
	_scene_list = VBoxContainer.new()
	_scene_list.add_theme_constant_override("separation", 8)
	_scene_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_body.add_child(_scene_list)
	_paint_scenes()
	_big_btn(sheet_body, "Vorlagen, echte Orte, eigene 3D-Datei …", func(): close(); main.templates.toggle(0))


func _paint_scenes() -> void:
	for c in _scene_list.get_children():
		c.queue_free()
	var q := _search.text.strip_edges().to_lower() if _search != null else ""
	for w in W.SHOWN:
		var rows := [[w, main.Scenes.name_of(w), false]]
		for pl in W.places_of(w):
			rows.append([pl[0], str(pl[1]), true])
		for s in rows:
			var id: String = s[0]
			var info: String = Tpl.SCENE_INFO.get(id, "")
			if q != "" and not (T.t(str(s[1])).to_lower().contains(q) or T.t(info).to_lower().contains(q) or str(s[1]).to_lower().contains(q)):
				continue
			var cur_s: bool = id == main.scene or (id == W.world_of(main.scene) and not W.is_place(id))
			_row(_scene_list, ("↳ " if s[2] else "") + T.t(str(s[1])), info, func(): _pick_scene(id), cur_s, id in Tpl.NEW_SCENES)   # «↳ » vor dem Übersetzen fände nichts


func _pick_scene(id: String) -> void:
	close()
	if id == "ort":
		main.open_map()
		return
	main.set_scene(id)


func _fill_time() -> void:
	_section("Tageszeit")
	var h: float = main.hour()
	for t in Q.TIMES:
		var hv: float = t[1]
		_row(sheet_body, t[0], "", func(): main.set_hour(hv); main._settings_dirty = true; _sheet("time"), absf(fmod(h - hv + 24.0, 24.0)) < 0.5)
	_section("Wetter")
	var g := _grid(3)
	for wd in Q.WEATHER:
		var k: String = wd[1]
		_big_btn(g, wd[0], func(): main.weather = k; main._update_sky(); main._sync_ui(); main._settings_dirty = true; _sheet("time"), main.weather == k)


func _fill_visit() -> void:
	_visit_l = UI.small("")
	sheet_body.add_child(_visit_l)
	var g := _grid(2)
	for vd in Q.VISITS:
		var k: String = vd[1]
		_big_btn(g, vd[0], func(): _visit(k))
	_paint()


func _visit(k: String) -> void:
	if k == "clear":
		for v in main.visitors.get_children():
			v.queue_free()
	elif k == "thief":
		main.thief()
	elif k == "car":
		main.car()
	else:
		main.visit(k)


func _fill_protect() -> void:
	var st := _state()
	var l := Label.new()
	l.text = st[0]
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", 16)
	sheet_body.add_child(l)
	var sl = main.statusled
	_big_btn(sheet_body, "Schutz: Wachsam ↔ Aus (kurz)", func(): _press("protect", 0.2))
	_big_btn(sheet_body, "Schutz: Voll (lang, 1,5 s)", func(): _press("protect", 1.8))
	_big_btn(sheet_body, "Alarm quittieren", func(): _press("ack", 0.2))
	var h := UI.small(T.t("Die Tasten gehen wie die echten Tasten am Gerät an MoveEye.") if sl != null else T.t("Ohne Gerät-Fenster nicht verfügbar."))
	h.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sheet_body.add_child(h)


func _press(k: String, s: float) -> void:
	if main.statusled == null:
		return
	main.statusled.press(k, true)
	get_tree().create_timer(s).timeout.connect(func(): main.statusled.press(k, false))


func _fill_more() -> void:
	_section("Welt")
	_row(sheet_body, "Gegenstände", "Zelt, Velo, 80 Dinge", func(): close(); main.inventar.toggle())
	_row(sheet_body, "Echter Ort", "Karte der Welt", func(): close(); main.open_map())
	_row(sheet_body, "Aufstellen", "wohin?", func(): close(); main.planner.open(true))
	_row(sheet_body, "Vorlagen", "Fertige Szenen, ganze Orte, Bausätze, eigene Datei", func(): close(); main.templates.toggle(0))
	_section("Testen · Lernen · Spielen")
	_row(sheet_body, "Testen", "Testlauf, Prüfstand, blinde Flecken", func(): close(); main.open_testen())
	_row(sheet_body, "Trainingsbilder", "eigene KI", func(): close(); main.open_train())
	if main.spielbereich != null:
		_row(sheet_body, "Spielen", "", func(): close(); main.spielbereich.toggle())
	_section("Alles")
	_row(sheet_body, "Alle Einstellungen", "das ganze Bedienfeld (Einfach / Experte)", func(): close(); _panel(true))
	_section("Darstellung")
	var g := _grid(3)
	for m in [["auto", "Automatisch"], ["phone", "Handy"], ["tablet", "Tablet-PC"]]:
		var mk: String = m[0]
		_big_btn(g, m[1], func(): _mode_pick(mk), mode == mk)


func _mode_pick(m: String) -> void:
	set_mode(m)
	if wanted():
		_sheet("more")


func _panel(v: bool) -> void:
	"""«Alle Einstellungen»: the whole panel over the full width (it scrolls inside), ✕ top left"""
	if main.ui_root == null:
		return
	panel_x.visible = v
	if v:
		main.show_panel(true)
		var vs := view_size()
		main.ui_root.offset_left = -vs.x
		var mw: float = main.ui_root.get_combined_minimum_size().x
		main.ui_root.scale = Vector2.ONE * minf(1.0, vs.x / maxf(mw, 1.0))
		main.ui_root.pivot_offset = Vector2(0, 0)
		main.ui_root.position.x = 0
	else:
		main.ui_root.scale = Vector2.ONE
		main.ui_root.offset_left = -392
		if on:
			main.show_panel(false)


# ---- Karte · Gerät · Kamera gross -------------------------------------------------------------------------------------------
func show_win(id: String, v: bool) -> void:
	if id == "":
		return
	if big_id != "" and big_id != id:
		show_win(big_id, false)
	var f = main.fenster
	var pip: Control = null                              # Browser-Demo: «Kamera» = das Bild von MoveEye mit den Rahmen
	if id == "kameras" and main.get("web_demo") != null:
		pip = main.web_demo.pip_frame()
	var w = f.win(id) if f != null and pip == null else null
	if w == null and pip == null:
		return
	var c: Control = pip if pip != null else w.content
	if v:
		close()
		_big_home = {"parent": c.get_parent(), "i": c.get_index(), "w": c.size.x, "min": c.custom_minimum_size,
				"on": f.is_on(id) if w != null else true}
		if w != null:
			f.set_on(id, true)
		c.get_parent().remove_child(c)
		big_scroll.add_child(c)
		c.visible = true
		big_id = id
		big_title.text = w.title() if w != null else T.t("Kamera von MoveEye")
		big.visible = true
		_layout()
		var cw: float = big.size.x - 22.0
		if id == "map":                                  # quadratisch: quer passt sie in die Höhe
			cw = minf(cw, view_size().y - (100.0 if landscape() else 160.0))
		if pip != null:                                  # 16:9 (das Bild der Kopfkamera); quer: in die Höhe
			var isz := Vector2(main.vps[0].size)
			var asp := isz.y / maxf(isz.x, 1.0)
			cw = minf(cw, (view_size().y - (90.0 if landscape() else 200.0)) / asp)
			c.custom_minimum_size = Vector2(cw, cw * asp)
		elif w.opts.has("set_size"):
			(w.opts["set_size"] as Callable).call(cw, 0.0)
			var over := c.get_combined_minimum_size().x - (big.size.x - 22.0)   # Rahmen des Inhalts: noch einmal kleiner
			if over > 0.5:
				(w.opts["set_size"] as Callable).call(cw - over, 0.0)
		else:
			c.custom_minimum_size.x = cw
	else:
		if big_id != id:
			return
		big_scroll.remove_child(c)
		var p: Node = _big_home.get("parent")
		if p != null and is_instance_valid(p):
			p.add_child(c)
			p.move_child(c, mini(int(_big_home.get("i", 0)), p.get_child_count() - 1))
		var pw: float = float(_big_home.get("w", 0.0))
		if pip != null:
			c.custom_minimum_size = _big_home.get("min", Vector2.ZERO)
		elif pw > 0.0 and w.opts.has("set_size"):
			(w.opts["set_size"] as Callable).call(pw, 0.0)
		if w != null:
			f.set_on(id, bool(_big_home.get("on", true)))
		big_id = ""
		big.visible = false
	_paint()


# ---- Tests ---------------------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	return {"on": on, "mode": mode, "view": [view_size().x, view_size().y], "landscape": landscape(), "sheet": cur, "big": big_id,
			"free": [free_rect().size.x, free_rect().size.y]}


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"mode":
			set_mode(str(d.get("value", "auto")))
		"sheet":
			_sheet(str(d.get("id", "scene")))
		"close":
			close()
		"win":
			show_win(str(d.get("id", "map")), bool(d.get("on", true)))
		"panel":
			_panel(bool(d.get("on", true)))
	return info()
