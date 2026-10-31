extends Node
## Paket «Fenster im Simulator» (31.10.2026, Wunsch Daniel: 1a, 2a, 3a, 4): EIN Rahmen für alle schwebenden Fenster über
## der 3D-Ansicht - Kompass, Karte, Livebild, SmallTV, Gerät, Mover-Stick, Kopf steuern, Kameras (Bedienfeld zu), CPU -
## im Aussehen des alten Fensters «Kameras» (dunkle Karte, runde Ecken, Titelleiste mit ✥):
##   * Titelleiste ziehen = verschieben (Maus; Finger über die Maus-Nachbildung von Godot, emulate_mouse_from_touch)
##   * Ecke unten rechts ziehen = Grösse (der Griff erscheint, wenn die Maus über dem Fenster ist); Grenzen pro Fenster;
##     Bilder (Karte, Kameras, Livebild, SmallTV) ändern nur die Breite - die Höhe folgt, das Seitenverhältnis bleibt
##   * «✕» blendet aus; zurück über «Fenster» in der Leiste unten (Liste mit Häkchen + «Anordnung zurücksetzen»);
##     Fenster mit eigener Taste (M Karte, L Livebild …) schalten über dieselbe Stelle wie die Taste
##   * schnappt an den Bildschirmrand (14 px wie die alten Plätze), ans Bedienfeld, an die Leiste unten und an andere
##     Fenster (Fang 12 px)
##   * Doppelklick auf die Titelleiste = zurück an den Standardplatz
##   * merkt sich Ort, Grösse und «ausgeblendet» pro PC in user://fenster.json; der Ort relativ zum freien Platz
##     (0 = links / oben, 1 = rechts / unten), damit er eine andere Auflösung übersteht; beim Start ins Bild geholt.
##     Die Grösse bleibt in Pixeln (die Schrift wächst nicht mit der Auflösung), wird aber ins Fenster eingepasst.
## Solange ein Fenster nie verschoben wurde, steht es am alten Platz (folgt dem Handy-Simulator, dem Bedienfeld …).
## Rechnet in den Koordinaten der Ansicht (get_visible_rect): eine Grössen-Einstellung der Oberfläche
## (content_scale_factor) gilt damit von selbst. Leicht für Lite: keine Schatten, kein Shader; pro Fenster nur ein paar
## Vergleiche je Bild, Titel 4 × pro Sekunde.
##
## Ein neues Fenster anmelden - eine Zeile (z. B. Blinki-Hinweis, Entdeckerbuch auf den anderen Zweigen):
##   main.fenster.add("blinki", "Blinki", mein_panel)
##   main.fenster.add("buch", "Entdeckerbuch", panel, {"resize": "w", "min": Vector2(260, 0), "max": Vector2(640, 0)})
## Der Inhalt darf schon in einer Ebene hängen (er wird an derselben Stelle in den Rahmen gehängt) oder noch nirgends
## (dann kommt er in main.ui_layer). Optionen (alle freiwillig):
##   home: Vector2 oder Callable(win) -> Vector2   Platz, solange nie verschoben (Standard: links oben gestapelt)
##   resize: "none" (Standard) | "w" (Breite; Höhe folgt dem Inhalt - für Bilder) | "wh" (frei)
##   min / max: Vector2   Grenzen der Inhaltsgrösse (bei "w" zählt x)
##   set_size: Callable(w, h)   wie der Inhalt eine neue Grösse übernimmt (Standard: custom_minimum_size)
##   on / set_on: Callable() -> bool / Callable(bool)   eigener Schalter (Taste, Einstellung) statt des Häkchens hier
##   shown: Callable() -> bool   will der Inhalt jetzt gezeigt werden (Standard: inhalt.visible)
##   hint: String   kurzer Hinweis in der Liste (z. B. «nur mit Mover»)
##   compact: true   schmale Leiste ohne Titeltext (Kompass, CPU); der Titel steht dann im Tooltip
##   hide: [Control]   Teile des Inhalts, die der Rahmen ersetzt (eigene Titelzeile)
##   on_hide: Callable()   das Fenster ist eben verschwunden
##   list: false   nicht in der Liste «Fenster»
## Der Inhalt bekommt set_meta("fenster", id): Skripte, die sich bisher selbst platziert haben, lassen das dann.
## Tests: /control {"action": "fenster", "do": "info" | "drag" | "resize" | "close" | "list" | "check" | "reset" | "over"}

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const FILE := "user://fenster.json"
const SNAP := 12.0                     # Fang beim Schnappen (px)
const EDGE := 14.0                     # Abstand zum Bildschirmrand (wie die alten Plätze)
const GAP := 6.0                       # Abstand zwischen zwei Fenstern
const STACK := ["compass", "map", "live", "smalltv"]   # links oben untereinander (wie bisher)

var main
var wins := {}                         # id -> Win
var order: Array = []                  # ids in the order they were added
var _saved := {}                       # from user://fenster.json
var _save_t := -1.0
var _vs := Vector2.ZERO
var _list: PanelContainer = null
var _list_anchor: Control = null
var _checks := {}                      # id -> CheckBox of the open list
var _list_t := 0.0


func _ready() -> void:
	_saved = {}
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY and typeof(d.get("win")) == TYPE_DICTIONARY:
			_saved = d["win"]


# ---- anmelden --------------------------------------------------------------------------------------------------------------
func add(id: String, title, content: Control, opts := {}) -> Control:
	"""put «content» into a window frame (see the head of the file). title: German text (T.t) or Callable() -> String"""
	if content == null or not is_instance_valid(content):
		return null
	if wins.has(id):
		return wins[id]
	var w := Win.new()
	w.mgr = self
	w.id = id
	w.title_src = title
	w.content = content
	w.opts = opts
	var parent: Node = content.get_parent()
	var idx := -1
	if parent == null:
		parent = main.ui_layer
	else:
		idx = content.get_index()
		parent.remove_child(content)
	content.set_meta("fenster", id)
	w.def_cms = content.custom_minimum_size
	if content is PanelContainer:                       # the frame is the card now (no card in the card)
		content.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	content.set_anchors_preset(Control.PRESET_TOP_LEFT)
	content.position = Vector2.ZERO
	for h in opts.get("hide", []):
		if h is Control:
			(h as Control).visible = false
	w.build()
	parent.add_child(w)
	if idx >= 0:
		parent.move_child(w, idx)
	var s: Dictionary = _saved.get(id, {}) if typeof(_saved.get(id, {})) == TYPE_DICTIONARY else {}
	w.user_hidden = bool(s.get("hid", false)) and not opts.has("set_on")
	wins[id] = w
	order.append(id)
	return w


func win(id_or_content) -> Win:
	if id_or_content is String:
		return wins.get(id_or_content)
	for k in wins:
		if (wins[k] as Win).content == id_or_content:
			return wins[k]
	return null


func home_at(id_or_content, p: Vector2) -> void:
	"""the standard place of a window (used while it was never moved by hand)"""
	var w := win(id_or_content)
	if w != null:
		w.home_pos = p


func is_on(id: String) -> bool:
	var w: Win = wins.get(id)
	if w == null:
		return false
	return bool((w.opts["on"] as Callable).call()) if w.opts.has("on") else not w.user_hidden


func set_on(id: String, v: bool, from_close := false) -> void:
	var w: Win = wins.get(id)
	if w == null:
		return
	if w.opts.has("set_on"):
		(w.opts["set_on"] as Callable).call(v)
	else:
		w.user_hidden = not v
	changed()
	if from_close and main.mehr != null and main.mehr.has_method("toast"):
		main.mehr.toast(T.t("«%s» ausgeblendet – wieder zeigen: «Fenster» in der Leiste unten", [w.title()]))


func over(p: Vector2) -> bool:
	"""is p over one of the windows? (main._over_hud: the 3D view does not move there)"""
	for k in wins:
		var w: Win = wins[k]
		if w.visible and w.is_visible_in_tree() and w.card.get_global_rect().has_point(p):
			return true
	return _list != null and _list.visible and _list.get_global_rect().has_point(p)


func reset() -> void:
	"""«Anordnung zurücksetzen»: every window back to its place and size; the ones hidden with ✕ come back"""
	for k in wins:
		var w: Win = wins[k]
		w.placed = false
		w.user_hidden = false
		if w.sized and w.opts.has("reset_size"):
			(w.opts["reset_size"] as Callable).call(w)
		elif w.sized and not w.opts.has("set_size"):
			w.content.custom_minimum_size = w.def_cms
			w.card.reset_size()
		elif w.sized and w.def_w > 0.0:
			w.apply_size(w.def_w, w.def_h)
		w.sized = false
	_saved = {}
	changed()


func changed() -> void:
	_save_t = 0.6


func _process(dt: float) -> void:
	var vs := view_size()
	if vs != _vs:                                        # the window got another size: placed windows keep their share
		_vs = vs
		for k in wins:
			var w: Win = wins[k]
			if w.placed and w.rel.x >= 0.0:
				w.position = clamp_pos(w, w.rel * (vs - w.size))
	if _save_t >= 0.0:
		_save_t -= dt
		if _save_t < 0.0:
			save()
	if _list != null and _list.visible:
		_list_t -= dt
		if _list_t <= 0.0:
			_list_t = 0.4
			_paint_list()
		if main.toolbar != null and not main.toolbar.visible:
			_list.visible = false


func _exit_tree() -> void:
	if _save_t >= 0.0:
		save()


func save() -> void:
	_save_t = -1.0
	var out := {}
	for k in _saved:                                     # windows of other branches / not yet shown keep their entry
		out[k] = _saved[k]
	for k in wins:
		var w: Win = wins[k]
		if not w._init_done:
			continue
		var e := {}
		if w.placed and w.rel.x >= 0.0:
			e["x"] = snappedf(w.rel.x, 0.0001)
			e["y"] = snappedf(w.rel.y, 0.0001)
		if w.sized:
			e["w"] = roundf(w.want_w)
			e["h"] = roundf(w.want_h)
		if w.user_hidden:
			e["hid"] = true
		if e.is_empty():
			out.erase(k)
		else:
			out[k] = e
	_saved = out
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"v": 1, "win": out}, " "))


# ---- Platz, Schnappen ---------------------------------------------------------------------------------------------------
func view_size() -> Vector2:
	return main.get_viewport().get_visible_rect().size


func free_lr() -> Vector2:
	"""left and right end of the free view (between the phone simulator and the control panel)"""
	var vw: float = view_size().x
	var right: float = main.ui_root.get_global_rect().position.x if main.ui_root != null and main.ui_root.visible else vw
	var left: float = main.phone.get_global_rect().end.x + 10.0 if main.phone != null and main.phone.visible else 0.0
	return Vector2(left, right)


func phone_open() -> bool:
	return main.phone != null and main.phone.visible


func home_of(w: Win) -> Vector2:
	var h = w.opts.get("home")
	if h is Callable:
		return (h as Callable).call(w)
	if h is Vector2:
		return h
	if w.home_pos.x > -9000.0:
		return w.home_pos
	return Vector2(stack_x(w), stack_y(w))


func stack_x(w: Win) -> float:
	"""the column at the top left (with the phone simulator open: at the right of the free view, like before)"""
	if phone_open():
		return free_lr().y - w.size.x - EDGE
	return EDGE


func stack_y(w: Win) -> float:
	var y := 8.0
	var x := stack_x(w)
	for k in wins:                                       # a window at the top in the way (the CPU display)
		var o: Win = wins[k]
		if not (k in STACK) and o.visible and not o.placed and o.position.y < 40.0 and o.position.x < x + w.size.x and o.position.x + o.size.x > x:
			y = maxf(y, o.position.y + o.size.y + GAP)
	for k in STACK:
		if k == w.id:
			break
		var o: Win = wins.get(k)
		if o != null and o.visible and not o.placed:
			y = maxf(y, o.position.y + o.size.y + GAP)
	return y


func clamp_pos(w: Win, p: Vector2) -> Vector2:
	var vs := view_size()
	var sz: Vector2 = w.size
	var x := clampf(p.x, 0.0, maxf(0.0, vs.x - sz.x))
	var y := clampf(p.y, 0.0, maxf(0.0, vs.y - (sz.y if sz.y <= vs.y else 24.0)))
	return Vector2(x, y).floor()


func _rects(w: Win) -> Array:
	"""what a window snaps to: the other windows, the control panel, the phone, the bar at the bottom"""
	var out := []
	for k in wins:
		var o: Win = wins[k]
		if o != w and o.visible:
			out.append(o.get_global_rect())
	for c in [main.ui_root, main.phone, main.toolbar, main.show_btn]:
		if c != null and is_instance_valid(c) and (c as Control).is_visible_in_tree():
			out.append((c as Control).get_global_rect())
	return out


func _best(edges: Array, lines: Array) -> float:
	"""the smallest move (≤ SNAP) that puts one of the edges on one of the lines; 0 = none"""
	var best := SNAP + 1.0
	var mv := 0.0
	for e in edges:
		for l in lines:
			var d: float = float(l) - float(e)
			if absf(d) < best:
				best = absf(d)
				mv = d
	return mv if best <= SNAP else 0.0


func _lines(w: Win, r: Rect2) -> Array:
	"""[x lines for the left edge, x lines for the right edge, y lines for the top, y lines for the bottom]"""
	var vs := view_size()
	var xl := [EDGE, 0.0]
	var xr := [vs.x - EDGE, vs.x]
	var yt := [EDGE, 0.0]
	var yb := [vs.y - EDGE, vs.y]
	for o in _rects(w):
		var q: Rect2 = o
		if q.position.y < r.end.y + SNAP and q.end.y > r.position.y - SNAP:   # side by side
			xl.append_array([q.end.x + GAP, q.position.x])
			xr.append_array([q.position.x - GAP, q.end.x])
		if q.position.x < r.end.x + SNAP and q.end.x > r.position.x - SNAP:   # one above the other
			yt.append_array([q.end.y + GAP, q.position.y])
			yb.append_array([q.position.y - GAP, q.end.y])
	return [xl, xr, yt, yb]


func snap_pos(w: Win, p: Vector2) -> Vector2:
	var r := Rect2(p, w.size)
	var ln := _lines(w, r)
	var dx := _best([r.position.x], ln[0])
	var dx2 := _best([r.end.x], ln[1])
	if dx == 0.0 or (dx2 != 0.0 and absf(dx2) < absf(dx)):
		dx = dx2
	if dx != 0.0:                                        # side by side now: the top / bottom of the neighbour counts too
		r.position.x += dx
		ln = _lines(w, r)
	var dy := _best([r.position.y], ln[2])
	var dy2 := _best([r.end.y], ln[3])
	if dy == 0.0 or (dy2 != 0.0 and absf(dy2) < absf(dy)):
		dy = dy2
	return p + Vector2(dx, dy)


func resize_drag(w: Win, d: Vector2) -> void:
	var mode: String = w.opts.get("resize", "none")
	var s0: Vector2 = w._res_size
	var mn: Vector2 = w.opts.get("min", Vector2(80, 60))
	var mx: Vector2 = w.opts.get("max", Vector2(900, 700))
	var over_v: Vector2 = w._res_frame - s0                 # frame around the content (strip, margins)
	var vs := view_size()
	var r := Rect2(w.position, w._res_frame)
	var ln := _lines(w, r)
	var nw := s0.x + d.x
	var nh := s0.y + d.y
	if mode == "w":
		var k := s0.y / maxf(1.0, s0.x)                     # a picture: height per width
		if k > 0.01 and absf(d.y) > absf(d.x):
			nw = s0.x + d.y / k                              # pulled down: the width follows
		nh = 0.0
	var right := w.position.x + nw + over_v.x
	nw += _best([right], ln[1])
	nw = clampf(nw, mn.x, maxf(mn.x, minf(mx.x, vs.x - w.position.x - over_v.x)))
	if mode == "wh":
		var bottom := w.position.y + nh + over_v.y
		nh += _best([bottom], ln[3])
		nh = clampf(nh, mn.y, maxf(mn.y, minf(mx.y, vs.y - w.position.y - over_v.y)))
	w.apply_size(roundf(nw), roundf(nh))


func raise(w: Win) -> void:
	"""to the front of the other windows, but below the control panel"""
	var p := w.get_parent()
	if p == null:
		return
	var ui: Control = main.ui_root
	if ui != null and ui.get_parent() == p:
		var ti := ui.get_index()
		p.move_child(w, ti - 1 if w.get_index() < ti else ti)
	else:
		p.move_child(w, -1)


func _shown(w: Win) -> void:
	"""a window appears: the first time its saved size and place, later its own size again (Kameras)"""
	if not w._init_done:
		w._init_done = true
		var cm: Vector2 = w.content.get_combined_minimum_size()
		w.def_w = cm.x
		w.def_h = cm.y if w.opts.get("resize", "none") == "wh" else 0.0
		var s: Dictionary = _saved.get(w.id, {}) if typeof(_saved.get(w.id, {})) == TYPE_DICTIONARY else {}
		if s.has("w") and w.opts.get("resize", "none") != "none":
			var mn: Vector2 = w.opts.get("min", Vector2(80, 60))
			var mx: Vector2 = w.opts.get("max", Vector2(900, 700))
			var vs := view_size()
			w.apply_size(clampf(float(s["w"]), mn.x, maxf(mn.x, minf(mx.x, vs.x - 40.0))),
					clampf(float(s.get("h", 0.0)), 0.0, maxf(mn.y, minf(mx.y, vs.y - 60.0))) if w.opts.get("resize") == "wh" else 0.0)
			w.sized = true
		if s.has("x"):
			w.rel = Vector2(clampf(float(s["x"]), 0.0, 1.0), clampf(float(s.get("y", 0.0)), 0.0, 1.0))
			w.placed = true
			w._rel_frames = 3                                 # the size settles in the first frames
	elif w.sized:
		w.apply_size(w.want_w, w.want_h)


func _hidden(w: Win) -> void:
	if w.opts.has("on_hide"):
		(w.opts["on_hide"] as Callable).call()


# ---- die Liste «Fenster» (Knopf in der Leiste unten) ---------------------------------------------------------------------
func list_open() -> bool:
	return _list != null and _list.visible


func toggle_list(anchor: Control = null) -> void:
	if list_open():
		_list.visible = false
		return
	_list_anchor = anchor
	_build_list()
	_list.visible = true
	_list.reset_size()
	var vs := view_size()
	var p := Vector2(EDGE, vs.y - _list.size.y - 80.0)
	if anchor != null and is_instance_valid(anchor):
		var ar := anchor.get_global_rect()
		p = Vector2(ar.position.x + ar.size.x / 2.0 - _list.size.x / 2.0, ar.position.y - _list.size.y - 12.0)
	_list.position = Vector2(clampf(p.x, 4.0, vs.x - _list.size.x - 4.0), maxf(4.0, p.y)).floor()
	if anchor != null and anchor.has_focus() and not _checks.is_empty():
		(_checks.values()[0] as Control).grab_focus.call_deferred()   # opened with the controller


func _build_list() -> void:
	if _list != null:
		_list.queue_free()
	_checks = {}
	_list = PanelContainer.new()
	_list.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.95), Color(1, 1, 1, 0.14), 14, 10, 1))
	_list.mouse_filter = Control.MOUSE_FILTER_STOP
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	_list.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := Label.new()
	t.text = T.t("Fenster").to_upper()
	t.add_theme_font_size_override("font_size", 11)
	t.add_theme_color_override("font_color", UI.MUT)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := _flat_button("✕", T.t("Schliessen"))
	x.pressed.connect(func(): _list.visible = false)
	hd.add_child(x)
	for id in order:
		var w: Win = wins[id]
		if w.opts.get("list", true) == false:
			continue
		var cb := CheckBox.new()
		cb.text = w.title()
		cb.add_theme_font_size_override("font_size", 13)
		cb.add_theme_color_override("font_color", Color(0.85, 0.88, 0.92))
		cb.add_theme_color_override("font_pressed_color", Color.WHITE)
		cb.add_theme_color_override("font_hover_color", Color.WHITE)
		cb.add_theme_color_override("font_hover_pressed_color", Color.WHITE)
		cb.add_theme_color_override("font_focus_color", Color(1.0, 0.83, 0.3))
		cb.add_theme_icon_override("checked", _box_icon(true))
		cb.add_theme_icon_override("unchecked", _box_icon(false))
		cb.button_pressed = is_on(id)
		cb.tooltip_text = T.t("Fenster zeigen / ausblenden")
		cb.toggled.connect(func(on: bool): set_on(id, on))
		cb.set_meta("pad_back", func(): _list.visible = false)   # B of the controller (padmap.gd)
		if w.opts.has("hint"):
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 6)
			row.add_child(cb)
			var hl := Label.new()
			hl.text = T.t(str(w.opts["hint"]))
			hl.add_theme_font_size_override("font_size", 11)
			hl.add_theme_color_override("font_color", UI.MUT)
			hl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			row.add_child(hl)
			v.add_child(row)
		else:
			v.add_child(cb)
		_checks[id] = cb
	var sep := HSeparator.new()
	sep.add_theme_constant_override("separation", 8)
	v.add_child(sep)
	var rb := Button.new()
	rb.text = T.t("Anordnung zurücksetzen")
	rb.tooltip_text = T.t("Alle Fenster an ihren Standardplatz und in die Standardgrösse; mit ✕ ausgeblendete kommen zurück")
	rb.add_theme_font_size_override("font_size", 13)
	rb.pressed.connect(func(): reset(); _paint_list())
	rb.set_meta("pad_back", func(): _list.visible = false)
	v.add_child(rb)
	var h2 := Label.new()
	h2.text = T.t("Titelleiste ziehen = verschieben · Ecke unten rechts = Grösse · Doppelklick auf die Leiste = zurück an den Platz")
	h2.add_theme_font_size_override("font_size", 10)
	h2.add_theme_color_override("font_color", UI.MUT)
	h2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	h2.custom_minimum_size = Vector2(260, 0)
	v.add_child(h2)
	_list.visible = false
	main.ui_layer.add_child(_list)                       # above the windows and the panel


var _icons := {}


func _box_icon(on: bool) -> Texture2D:
	"""a check box that is seen on the dark card (blue and ticked like the active switches, or a grey frame)"""
	if _icons.has(on):
		return _icons[on]
	var n := 16
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in range(n):
		for x in range(n):
			var edge := x <= 1 or y <= 1 or x >= n - 2 or y >= n - 2
			var corner := (x <= 1 or x >= n - 2) and (y <= 1 or y >= n - 2)
			if corner:
				continue
			if on:
				img.set_pixel(x, y, UI.ACC)
			elif edge:
				img.set_pixel(x, y, Color(0.6, 0.66, 0.74))
	if on:                                               # the tick
		for p in [[4, 8], [5, 9], [6, 10], [7, 9], [8, 8], [9, 7], [10, 6], [11, 5]]:
			for dy in [0, 1]:
				img.set_pixel(p[0], p[1] + dy - 1, Color.WHITE)
	var t := ImageTexture.create_from_image(img)
	_icons[on] = t
	return t


func _paint_list() -> void:
	for id in _checks:
		var cb: CheckBox = _checks[id]
		var on := is_on(id)
		if cb.button_pressed != on:
			cb.set_pressed_no_signal(on)


var mouse := Vector2(-1, -1)           # last mouse position (also of events sent by MoveEye / the tests)


func _input(ev: InputEvent) -> void:
	if ev is InputEventMouse:
		mouse = (ev as InputEventMouse).global_position
	if not list_open():
		return
	if ev is InputEventMouseButton and ev.pressed:
		var p: Vector2 = ev.position
		if _list.get_global_rect().has_point(p):
			return
		if _list_anchor != null and is_instance_valid(_list_anchor) and _list_anchor.get_global_rect().has_point(p):
			return                                       # the button itself closes it (toggle)
		_list.visible = false                            # a click elsewhere closes the list (the click still counts)
	elif ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		_list.visible = false


func _flat_button(tx: String, tip: String) -> Button:
	var b := Button.new()
	b.text = tx
	b.tooltip_text = tip
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 11)
	b.add_theme_color_override("font_color", Color(1, 1, 1, 0.6))
	b.add_theme_color_override("font_hover_color", Color(1.0, 0.55, 0.5))
	b.add_theme_color_override("font_pressed_color", Color(1.0, 0.45, 0.4))
	var e := StyleBoxEmpty.new()
	e.content_margin_left = 3
	e.content_margin_right = 3
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		b.add_theme_stylebox_override(st, e)
	b.custom_minimum_size = Vector2(16, 14)
	return b


# ---- die Fenster des Simulators ------------------------------------------------------------------------------------------
func setup_sim() -> void:
	"""all floating boxes of the simulator in one frame each (called once after main._build_ui)"""
	var m = main
	if m.compass != null:                                # the needle and the «N» around it need room
		m.compass.custom_minimum_size = Vector2(84, 84)
		add("compass", "Kompass", m.compass, {"compact": true})
	if m.minimap != null:
		add("map", "Karte", m.minimap, {"resize": "w", "min": Vector2(130, 0), "max": Vector2(520, 0),
				"on": func(): return m.map_on, "set_on": func(v): m.set_map(bool(v)), "set_size": _map_size,
				"reset_size": func(_w): _map_size(220.0, 0.0)})
	if m.liveview != null:
		var lv = m.liveview
		add("live", func(): return T.t(lv.title.text), lv, {"resize": "w", "min": Vector2(160, 0), "max": Vector2(640, 0), "hide": [lv.title],
				"on": func(): return m.live_on, "set_on": func(v): m.set_live(bool(v)), "set_size": _live_size,
				"reset_size": func(_w): _live_size(260.0, 0.0)})
	if m.smalltv != null and m.smalltv.tile != null:
		var tv = m.smalltv
		add("smalltv", "SmallTV (virtuell)", tv.tile, {"resize": "w", "min": Vector2(130, 0), "max": Vector2(460, 0), "hide": [tv._title],
				"hint": "sobald MoveEye ein Bild schickt", "set_size": _tv_size, "reset_size": func(_w): tv.big = false; tv._size(),
				"on": func(): return tv.show, "set_on": func(v): tv.show = bool(v); tv.save()})
	if m.statusled != null and m.statusled.tile != null:
		var sl = m.statusled
		add("geraet", "Gerät (LED und Tasten)", sl.tile, {"resize": "w", "min": Vector2(240, 0), "max": Vector2(560, 0),
				"hide": [sl._title] if sl.get("_title") != null else [], "home": _home_geraet,
				"on": func(): return sl.show_panel, "set_on": func(v): sl.show_panel = bool(v); sl.save()})
	if m.rover_pad != null:
		add("mover", "Mover fahren", m.rover_pad, {"compact": true, "hint": "nur mit «Mover simulieren»", "home": _home_mover})
	if m.headpad != null:
		var hp = m.headpad
		add("kopf", "Kopf steuern", hp, {"resize": "w", "min": Vector2(260, 0), "max": Vector2(760, 0),
				"hide": [hp.head_row] if hp.get("head_row") != null else [], "hint": "Knopf «Kopf» unten",
				"on": func(): return hp.visible, "set_on": func(v): hp.visible = bool(v), "set_size": _kopf_size, "home": _home_kopf,
				"reset_size": func(_w): hp.img.custom_minimum_size = Vector2(320, 180); hp.info.custom_minimum_size.x = 320})
	if m.cam_float != null and m.cam_card != null:
		var cf: Control = m.cam_float
		var cc: Control = m.cam_card
		_cam_keep = [m.prev0.custom_minimum_size, m.prev1.custom_minimum_size, m.prevt.custom_minimum_size]
		add("kameras", "Kameras · H = Bedienfeld", cf, {"resize": "w", "min": Vector2(240, 0), "max": Vector2(720, 0),
				"hide": [cf.get_child(0)] if cf.get_child_count() > 0 else [], "hint": "wenn das Bedienfeld zu ist (H)",
				"shown": func(): return cf.visible and cc.visible and cc.get_parent() == cf,
				"on": func(): return cc.visible, "set_on": func(v): cc.visible = bool(v),
				"set_size": _cam_size, "on_hide": _cam_restore, "reset_size": _cam_reset})
		home_at(cf, Vector2(EDGE, 300))
	if m.cpu_pill != null:
		add("cpu", "CPU-Anzeige", m.cpu_pill, {"compact": true, "home": _home_cpu})


func _map_size(w: float, _h: float) -> void:
	main.minimap.size_px = w
	main.minimap._apply_size()
	main.minimap.queue_redraw()
	main.map_size = w
	main._settings_dirty = true


func _live_size(w: float, _h: float) -> void:
	main.live_size = w
	main.liveview.width_px = w
	main.liveview.apply()
	main._settings_dirty = true


func _tv_size(w: float, _h: float) -> void:
	var tv = main.smalltv
	var pad: float = tv.tile.size.x - tv._tex.size.x if tv._tex.size.x > 0.0 else 16.0
	var s: float = maxf(80.0, w - pad)
	tv._tex.custom_minimum_size = Vector2(s, s)


func _kopf_size(w: float, _h: float) -> void:
	main.headpad.img.custom_minimum_size = Vector2(w, roundf(w * 9.0 / 16.0))
	main.headpad.info.custom_minimum_size.x = w


var _cam_keep := []


func _cam_size(w: float, _h: float) -> void:
	"""Kameras (Bedienfeld zu): the card and its three pictures grow together"""
	var cc: Control = main.cam_card
	if cc.get_parent() != main.cam_float:
		return
	var f: float = w / 330.0
	cc.custom_minimum_size.x = w
	main.prev0.custom_minimum_size = (_cam_keep[0] as Vector2) * f
	main.prev1.custom_minimum_size = (_cam_keep[1] as Vector2) * f
	main.prevt.custom_minimum_size = (_cam_keep[2] as Vector2) * f


func _cam_restore() -> void:
	"""back in the panel: the pictures in their usual size"""
	main.prev0.custom_minimum_size = _cam_keep[0]
	main.prev1.custom_minimum_size = _cam_keep[1]
	main.prevt.custom_minimum_size = _cam_keep[2]


func _cam_reset(w: Win) -> void:
	_cam_restore()
	if main.cam_card.get_parent() == main.cam_float:
		main.cam_card.custom_minimum_size.x = w.def_w


func _home_geraet(w: Win) -> Vector2:
	var lr := free_lr()
	return Vector2(lr.x + EDGE if phone_open() else lr.y - w.size.x - EDGE, 64.0)


func _home_mover(w: Win) -> Vector2:
	return Vector2(free_lr().y - w.size.x - 18.0, view_size().y - w.size.y - 70.0)


func _home_kopf(w: Win) -> Vector2:
	return Vector2(free_lr().x + EDGE, view_size().y - w.size.y - 110.0)


func _home_cpu(w: Win) -> Vector2:
	var lr := free_lr()
	return Vector2((lr.x + lr.y - w.size.x) / 2.0, 2.0)


# ---- Tests (/control {"action": "fenster", …}) ------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	var id := str(d.get("id", ""))
	var w: Win = wins.get(id)
	match dd:
		"drag":                                          # the title strip with the mouse: {id, dx, dy}
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			var a := w.strip.get_global_rect().get_center() + Vector2(-10, 0)
			_mouse_path(a, a + Vector2(float(d.get("dx", 0)), float(d.get("dy", 0))))
		"resize":                                        # the corner: {id, dx, dy}
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			var a := w.get_global_rect().end - Vector2(5, 5)
			_mouse_path(a, a + Vector2(float(d.get("dx", 0)), float(d.get("dy", 0))))
		"close":                                         # click on «✕»
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			_mouse_path(w.close_b.get_global_rect().get_center(), w.close_b.get_global_rect().get_center())
		"dblclick":
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			_mouse_path(w.strip.get_global_rect().get_center(), w.strip.get_global_rect().get_center(), true)
		"list":                                          # the button «Fenster» of the bar
			if main.toolbar != null:
				main.toolbar._press_item("windows")
		"check":                                         # click on the check box of a window in the open list
			if not list_open() or not _checks.has(id):
				return {"ok": false, "error": "list not open"}
			var c := (_checks[id] as Control).get_global_rect()
			_mouse_path(c.position + Vector2(10, c.size.y / 2.0), c.position + Vector2(10, c.size.y / 2.0))
		"reset":
			reset()
		"save":
			save()
		"over":
			return {"ok": true, "hud": main._over_hud(Vector2(float(d.get("x", 0)), float(d.get("y", 0))))}
	return info()


func info() -> Dictionary:
	var o := {}
	for k in order:
		var w: Win = wins[k]
		o[k] = {"vis": w.visible, "on": is_on(k), "placed": w.placed, "sized": w.sized, "rect": [w.position.x, w.position.y, w.size.x, w.size.y],
				"content": [w.content.size.x, w.content.size.y], "grip": w.grip.visible}
	return {"ok": true, "busy": _busy > 0, "wins": o, "list": list_open(), "file": ProjectSettings.globalize_path(FILE), "saved": _saved, "view": [view_size().x, view_size().y]}


func _mouse_path(a: Vector2, b: Vector2, dbl := false) -> void:
	"""for tests: real mouse events through the GUI (move there, press, move in steps, let go)"""
	_busy += 1
	_ev_move(a, 0)
	await get_tree().process_frame
	await get_tree().process_frame
	_ev_button(a, true, false)
	await get_tree().process_frame
	var n := 8
	for i in range(1, n + 1):
		_ev_move(a.lerp(b, float(i) / n), MOUSE_BUTTON_MASK_LEFT)
		await get_tree().process_frame
	_ev_button(b, false, false)
	if dbl:
		await get_tree().process_frame
		_ev_button(b, true, true)
		await get_tree().process_frame
		_ev_button(b, false, false)
	await get_tree().process_frame
	_ev_move(b + Vector2(0, 1), 0)
	await get_tree().process_frame
	_busy -= 1


var _last_mouse := Vector2.ZERO
var _busy := 0


func _ev_move(p: Vector2, mask: int) -> void:
	var m := InputEventMouseMotion.new()
	m.position = p
	m.global_position = p
	m.relative = p - _last_mouse
	m.button_mask = mask
	_last_mouse = p
	Input.parse_input_event(m)


func _ev_button(p: Vector2, down: bool, dbl: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = down
	e.double_click = dbl
	e.position = p
	e.global_position = p
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
	Input.parse_input_event(e)


# ---- der Rahmen ---------------------------------------------------------------------------------------------------------
class Win extends Control:
	var mgr
	var id := ""
	var title_src = ""
	var content: Control
	var opts := {}
	var card: PanelContainer
	var strip: PanelContainer
	var title_l: Label
	var close_b: Button
	var grip: Grip
	var placed := false                # moved by hand (else at its standard place)
	var sized := false                 # resized by hand
	var user_hidden := false           # hidden with ✕ (windows without their own switch)
	var rel := Vector2(-1, -1)         # the place as a share of the free room (0 … 1), what is saved
	var home_pos := Vector2(-9999, -9999)
	var want_w := 0.0
	var want_h := 0.0
	var def_w := -1.0
	var def_h := 0.0
	var def_cms := Vector2.ZERO          # the minimum size of the content before any change (for «zurücksetzen»)
	var _init_done := false
	var _rel_frames := 0
	var _was := false
	var _t := 0.0
	var _drag := false
	var _drag_off := Vector2.ZERO
	var _drag_from := Vector2.ZERO
	var _res := false
	var _res_from := Vector2.ZERO
	var _res_size := Vector2.ZERO
	var _res_frame := Vector2.ZERO

	func title() -> String:
		if title_src is Callable:
			return str((title_src as Callable).call())
		return T.t(str(title_src))

	func build() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE        # only the card catches the mouse, never the room around it
		visible = false
		card = PanelContainer.new()
		card.mouse_filter = Control.MOUSE_FILTER_STOP
		card.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.88), UI.LINE, 8, 4, 1))
		add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 3)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(v)
		strip = PanelContainer.new()                    # the title strip (like the grip of the old «Kameras» window)
		var ss := UI.box(Color(UI.BG, 0.92), UI.LINE, 6, 2, 1)
		ss.content_margin_left = 6
		ss.content_margin_right = 2
		ss.content_margin_top = 1
		ss.content_margin_bottom = 1
		strip.add_theme_stylebox_override("panel", ss)
		strip.mouse_filter = Control.MOUSE_FILTER_STOP
		strip.mouse_default_cursor_shape = Control.CURSOR_MOVE
		strip.gui_input.connect(_strip_input)
		v.add_child(strip)
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 4)
		h.mouse_filter = Control.MOUSE_FILTER_IGNORE
		strip.add_child(h)
		var dots := Dots.new()                         # the grip: six dots (drawn - no font needed)
		dots.custom_minimum_size = Vector2(8, 12)
		dots.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		dots.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(dots)
		title_l = Label.new()
		title_l.add_theme_font_size_override("font_size", 11)
		title_l.add_theme_color_override("font_color", UI.MUT)
		title_l.clip_text = true
		title_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		title_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		title_l.custom_minimum_size = Vector2(12, 0)
		title_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(title_l)
		close_b = mgr._flat_button("✕", T.t("Fenster ausblenden (zurück über «Fenster» in der Leiste unten)"))
		close_b.pressed.connect(func(): mgr.set_on(id, false, true))
		h.add_child(close_b)
		v.add_child(content)
		grip = Grip.new()
		grip.size = Vector2(16, 16)
		grip.mouse_filter = Control.MOUSE_FILTER_STOP
		grip.mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
		grip.tooltip_text = T.t("Ziehen: Grösse ändern")
		grip.gui_input.connect(_grip_input)
		grip.visible = false
		add_child(grip)
		_title()

	func _title() -> void:
		var tx := title()
		var compact: bool = opts.get("compact", false)
		title_l.text = "" if compact else tx
		strip.tooltip_text = tx + " · " + T.t("Ziehen zum Verschieben · Doppelklick: zurück an den Platz")

	func apply_size(w: float, h: float) -> void:
		var mode: String = opts.get("resize", "none")
		if mode == "none":
			return
		if opts.has("set_size"):
			(opts["set_size"] as Callable).call(w, h)
		else:
			content.custom_minimum_size = Vector2(w, h if mode == "wh" else content.custom_minimum_size.y)
		want_w = w
		want_h = h
		card.reset_size()

	func _process(dt: float) -> void:
		var want: bool = bool((opts["shown"] as Callable).call()) if opts.has("shown") else content.visible
		if not opts.has("set_on"):
			want = want and not user_hidden
		var vis: bool = want and content.modulate.a > 0.01     # the rover stick: MoveEye shows the picture full screen
		if vis != visible:
			visible = vis
		if vis != _was:
			_was = vis
			if vis:
				mgr._shown(self)
			else:
				_drag = false
				_res = false
				mgr._hidden(self)
		if not vis:
			return
		var cs := card.get_combined_minimum_size()
		if card.size != cs:
			card.size = cs
		if size != card.size:
			size = card.size
		_t -= dt
		if _t <= 0.0:
			_t = 0.25
			_title()
		if not (_drag or _res):
			if placed:
				if _rel_frames > 0:
					_rel_frames -= 1
					position = mgr.clamp_pos(self, rel * (mgr.view_size() - size))
				else:
					position = mgr.clamp_pos(self, position)
			else:
				position = mgr.clamp_pos(self, mgr.home_of(self))
		var g: bool = opts.get("resize", "none") != "none" and (_res or get_global_rect().has_point(mgr.mouse))
		if g != grip.visible:
			grip.visible = g
		if g:
			grip.position = size - grip.size

	func _strip_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed and ev.double_click:              # back to its place
				_drag = false
				placed = false
				rel = Vector2(-1, -1)
				mgr.changed()
			elif ev.pressed:
				_drag = true
				_drag_off = ev.global_position - position
				_drag_from = ev.global_position
				mgr.raise(self)
			elif _drag:
				_end_drag(ev.global_position)
			strip.accept_event()
		elif ev is InputEventMouseMotion and _drag:
			if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):   # let go somewhere else
				_end_drag(ev.global_position)
				return
			position = mgr.clamp_pos(self, mgr.snap_pos(self, ev.global_position - _drag_off))
			strip.accept_event()

	func _end_drag(p: Vector2) -> void:
		_drag = false
		if p.distance_to(_drag_from) < 3.0:
			return                                       # only a click: stays where it is (and at its place)
		placed = true
		var room: Vector2 = mgr.view_size() - size
		rel = Vector2(clampf(position.x / maxf(1.0, room.x), 0.0, 1.0), clampf(position.y / maxf(1.0, room.y), 0.0, 1.0))
		mgr.changed()

	func _grip_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed:
				_res = true
				_res_from = ev.global_position
				_res_size = content.size
				_res_frame = size
				mgr.raise(self)
			elif _res:
				_res = false
				sized = true
				if placed:                                   # the share of the room changes with the size
					var room: Vector2 = mgr.view_size() - card.get_combined_minimum_size()
					rel = Vector2(clampf(position.x / maxf(1.0, room.x), 0.0, 1.0), clampf(position.y / maxf(1.0, room.y), 0.0, 1.0))
				mgr.changed()
			grip.accept_event()
		elif ev is InputEventMouseMotion and _res:
			if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):
				_res = false
				sized = true
				mgr.changed()
				return
			mgr.resize_drag(self, ev.global_position - _res_from)
			grip.accept_event()


class Dots extends Control:
	func _draw() -> void:
		for i in range(3):
			for j in range(2):
				draw_circle(Vector2(2.0 + j * 4.0, 2.0 + i * 4.0), 1.2, Color(1, 1, 1, 0.55))


class Grip extends Control:
	func _draw() -> void:
		var s := size
		for j in range(3):
			var o := 4.0 + j * 4.0
			draw_line(Vector2(s.x - o, s.y - 2), Vector2(s.x - 2, s.y - o), Color(1, 1, 1, 0.75), 1.5, true)
