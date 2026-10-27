extends PanelContainer
## The map to choose a place in Switzerland (from 3D-3.4): swisstopo map or aerial picture, drag with the mouse, zoom with
## the wheel, search a name; a click puts the marker (where Motion Watch stands, the square shows the detailed 400 × 400 m),
## «Diesen Ort laden» loads the place (geo.gd) and builds the scene. Map tiles are kept on the disk like the place data.

const ZMIN := 7
const ZMAX := 19
const CH_CENTER := Vector2(46.8, 8.23)

var main
var geo
var zoom := 8
var center := Vector2.ZERO        # world pixel at the zoom
var kind := "map"                 # map | photo
var tiles := {}                   # "kind/z/x/y" -> ImageTexture, or false while loading / failed
var loading := 0
var want: Array = []               # tiles still to load (newest first)
var sel := Vector2.ZERO           # chosen (lat, lon); ZERO = none
var sel_name := ""
var waiting := false              # loading the place: close when it is ready
var dragging := false
var drag_from := Vector2.ZERO
var moved := 0.0

var view: Control
var search: LineEdit
var results: ItemList
var found: Array = []
var info: Label
var load_btn: Button
var kind_btn: Button
var title: Label
var top_bar: HBoxContainer
var back_btn: Button
var wiz: ScrollContainer          # steps 2 and 3 of the wizard (3D-3.14)
var wiz_box: VBoxContainer
var step := 1                     # 1 the place, 2 the surroundings, 3 the objects
var w_env := "auto"
var w_hide := 1
var w_cars := true
var w_forest := 1
var w_camp := 0


func _ready() -> void:
	geo = main.geo
	set_anchors_preset(Control.PRESET_FULL_RECT)
	offset_left = 24
	offset_top = 24
	offset_right = -24
	offset_bottom = -24
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.08, 0.1, 0.97)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(10)
	add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	add_child(v)
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 6)
	v.add_child(bar)
	top_bar = bar
	title = Label.new()
	title.text = "Schritt 1 von 3 · Ort wählen (Schweiz)"
	bar.add_child(title)
	search = LineEdit.new()
	search.placeholder_text = "Ort suchen, z. B. Zermatt, Bahnhofstrasse 1 Zürich …"
	search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	search.text_submitted.connect(func(_x): _search())
	bar.add_child(search)
	var sbtn := Button.new()
	sbtn.text = "Suchen"
	sbtn.pressed.connect(_search)
	bar.add_child(sbtn)
	kind_btn = Button.new()
	kind_btn.text = "Luftbild"
	kind_btn.tooltip_text = "Zwischen Landeskarte und Luftbild wechseln"
	kind_btn.pressed.connect(func():
		kind = "photo" if kind == "map" else "map"
		kind_btn.text = "Landeskarte" if kind == "photo" else "Luftbild"
		view.queue_redraw())
	bar.add_child(kind_btn)
	var close := Button.new()
	close.text = "×"
	close.tooltip_text = "Karte schliessen (Esc)"
	close.pressed.connect(func(): visible = false)
	bar.add_child(close)
	results = ItemList.new()
	results.custom_minimum_size = Vector2(0, 130)
	results.visible = false
	results.item_selected.connect(_pick_result)
	v.add_child(results)
	view = Control.new()
	view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	view.clip_contents = true
	view.mouse_default_cursor_shape = Control.CURSOR_CROSS
	view.draw.connect(_draw_map)
	view.gui_input.connect(_map_input)
	view.resized.connect(func(): view.queue_redraw())
	v.add_child(view)
	wiz = ScrollContainer.new()
	wiz.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wiz.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	wiz.visible = false
	v.add_child(wiz)
	wiz_box = VBoxContainer.new()
	wiz_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	wiz_box.add_theme_constant_override("separation", 10)
	wiz.add_child(wiz_box)
	var bottom := HBoxContainer.new()
	bottom.add_theme_constant_override("separation", 8)
	v.add_child(bottom)
	info = Label.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.text = "Klicken = Ort wählen · Ziehen = verschieben · Mausrad = zoomen"
	bottom.add_child(info)
	back_btn = Button.new()
	back_btn.text = "‹ Zurück"
	back_btn.visible = false
	back_btn.pressed.connect(func(): _show_step(step - 1))
	bottom.add_child(back_btn)
	load_btn = Button.new()
	load_btn.text = "Weiter: Umgebung ›"
	load_btn.disabled = true
	load_btn.pressed.connect(_next)
	if main.UI.has_method("primary"):
		main.UI.primary(load_btn)
	bottom.add_child(load_btn)
	var attr := Label.new()
	attr.text = "Karte und Luftbild © swisstopo · Gebäude, Wald, Strassen © OpenStreetMap-Mitwirkende · Höhen © swisstopo / Terrarium"
	attr.add_theme_font_size_override("font_size", 11)
	attr.add_theme_color_override("font_color", Color(0.6, 0.64, 0.7))
	v.add_child(attr)


func open(la := 0.0, lo := 0.0, z := 0) -> void:
	visible = true
	_show_step(1)
	get_parent().move_child(self, -1)                     # above everything else in the window
	if la != 0.0:
		sel = Vector2(la, lo)
		sel_name = main.ort_name if is_equal_approx(la, main.ort_lat) else ""
		zoom = z if z > 0 else 15
		center = geo.world_px(geo.merc(la, lo), zoom)
	else:
		zoom = z if z > 0 else 8
		center = geo.world_px(geo.merc(CH_CENTER.x, CH_CENTER.y), zoom)
	load_btn.disabled = sel == Vector2.ZERO
	_update_info()
	view.queue_redraw()


func status_text() -> String:
	return info.text if info != null else ""


func _unhandled_key_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		visible = false
		get_viewport().set_input_as_handled()


# ---- drawing -----------------------------------------------------------------------------------------------------
func _draw_map() -> void:
	var sz := view.size
	view.draw_rect(Rect2(Vector2.ZERO, sz), Color(0.82, 0.84, 0.82))
	var tl := center - sz / 2.0
	var n := 1 << zoom
	var tx0 := int(floor(tl.x / 256.0))
	var ty0 := int(floor(tl.y / 256.0))
	var tx1 := int(floor((tl.x + sz.x) / 256.0))
	var ty1 := int(floor((tl.y + sz.y) / 256.0))
	var need := []
	for ty in range(ty0, ty1 + 1):
		for tx in range(tx0, tx1 + 1):
			if tx < 0 or ty < 0 or tx >= n or ty >= n:
				continue
			var r := Rect2(Vector2(tx * 256.0, ty * 256.0) - tl, Vector2(256, 256))
			var key := "%s/%d/%d/%d" % [kind, zoom, tx, ty]
			var tex = tiles.get(key)
			if tex is ImageTexture:
				view.draw_texture_rect(tex, r, false)
				continue
			for up in range(1, 6):                          # meanwhile a bigger tile of a smaller zoom, cut out
				var z2 := zoom - up
				if z2 < 0:
					break
				var k2 := "%s/%d/%d/%d" % [kind, z2, tx >> up, ty >> up]
				var t2 = tiles.get(k2)
				if t2 is ImageTexture:
					var part := 256.0 / float(1 << up)
					var src := Rect2((tx - ((tx >> up) << up)) * part, (ty - ((ty >> up) << up)) * part, part, part)
					view.draw_texture_rect_region(t2, r, src)
					break
			if not tiles.has(key):
				need.append([key, zoom, tx, ty])
	# nearest to the middle first
	need.sort_custom(func(a, b): return Vector2(a[2], a[3]).distance_to((tl + sz / 2.0) / 256.0) < Vector2(b[2], b[3]).distance_to((tl + sz / 2.0) / 256.0))
	want = need + want.filter(func(w): return not need.any(func(x): return x[0] == w[0]))
	want = want.slice(0, 60)
	_pump()
	if sel != Vector2.ZERO:
		var p: Vector2 = geo.world_px(geo.merc(sel.x, sel.y), zoom) - tl
		var mpp: float = 2.0 * PI * geo.ER * cos(deg_to_rad(sel.x)) / (256.0 * n)
		var half: float = geo.NEAR / mpp
		if half > 6.0:
			view.draw_rect(Rect2(p - Vector2(half, half), Vector2(half, half) * 2.0), Color(1.0, 0.55, 0.1, 0.9), false, 2.0)
			view.draw_rect(Rect2(p - Vector2(half, half), Vector2(half, half) * 2.0), Color(1.0, 0.55, 0.1, 0.12), true)
		view.draw_circle(p, 9.0, Color(1, 1, 1))
		view.draw_circle(p, 6.5, Color(0.95, 0.35, 0.1))
		view.draw_line(p + Vector2(0, -16), p + Vector2(0, -30), Color(0.95, 0.35, 0.1), 3.0)   # north
	# scale bar
	var lat_c: float = geo.unmerc(geo.from_px(center, zoom)).x
	var mpp2: float = 2.0 * PI * geo.ER * cos(deg_to_rad(lat_c)) / (256.0 * n)
	var bar_m := 1.0
	for cand in [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]:
		if cand / mpp2 > 80.0:
			bar_m = cand
			break
	var bl: float = bar_m / mpp2
	var o := Vector2(12, sz.y - 16)
	view.draw_rect(Rect2(o - Vector2(4, 18), Vector2(bl + 8, 26)), Color(1, 1, 1, 0.75))
	view.draw_line(o, o + Vector2(bl, 0), Color(0, 0, 0), 2.0)
	view.draw_string(ThemeDB.fallback_font, o + Vector2(0, -5), ("%d m" % bar_m) if bar_m < 1000 else ("%d km" % (bar_m / 1000)), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0, 0, 0))
	if loading > 0:
		view.draw_string(ThemeDB.fallback_font, Vector2(sz.x - 150, sz.y - 10), "Karte lädt …", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0, 0, 0))


func _pump() -> void:
	while loading < 6 and not want.is_empty():
		var w: Array = want.pop_front()
		if tiles.has(w[0]):
			continue
		tiles[w[0]] = false
		loading += 1
		_get_tile(w)


func _get_tile(w: Array) -> void:
	var parts: PackedStringArray = (w[0] as String).split("/")
	var bytes: PackedByteArray = await geo.fetch(geo.url(parts[0], w[1], w[2], w[3]), "", true, 20.0)
	loading -= 1
	var img := Image.new()
	if bytes.size() > 0 and (img.load_jpg_from_buffer(bytes) == OK or img.load_png_from_buffer(bytes) == OK):
		tiles[w[0]] = ImageTexture.create_from_image(img)
	elif bytes.size() == 0 and info != null and not waiting:
		info.text = "Karte: " + geo._last_err + " – ist der PC mit dem Internet verbunden?"
	if tiles.size() > 900:                                  # forget old tiles (memory)
		var ks := tiles.keys()
		for i in range(300):
			tiles.erase(ks[i])
	view.queue_redraw()


# ---- mouse -------------------------------------------------------------------------------------------------------
func _map_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		if ev.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			if ev.pressed:
				dragging = true
				drag_from = ev.position
				moved = 0.0
				if ev.double_click and ev.button_index == MOUSE_BUTTON_LEFT:
					_zoom_at(ev.position, 2)
			else:
				dragging = false
				if moved < 5.0 and ev.button_index == MOUSE_BUTTON_LEFT:
					_choose(ev.position)
		elif ev.pressed and ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_at(ev.position, 1)
		elif ev.pressed and ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_at(ev.position, -1)
	elif ev is InputEventMouseMotion and dragging:
		center -= ev.relative
		moved += ev.relative.length()
		_clamp()
		view.queue_redraw()


func _zoom_at(p: Vector2, dz: int) -> void:
	var z2 := clampi(zoom + dz, ZMIN, ZMAX)
	if z2 == zoom:
		return
	var at: Vector2 = center + (p - view.size / 2.0)        # the point under the mouse stays where it is
	var f := pow(2.0, z2 - zoom)
	center = at * f - (p - view.size / 2.0)
	zoom = z2
	_clamp()
	view.queue_redraw()


func _clamp() -> void:
	var a: Vector2 = geo.world_px(geo.merc(48.3, 5.3), zoom)
	var b: Vector2 = geo.world_px(geo.merc(45.4, 11.0), zoom)
	center = Vector2(clampf(center.x, a.x, b.x), clampf(center.y, a.y, b.y))


func _choose(p: Vector2) -> void:
	var w: Vector2 = center + (p - view.size / 2.0)
	var ll: Vector2 = geo.unmerc(geo.from_px(w, zoom))
	if not geo.in_ch(ll.x, ll.y):
		info.text = "Bitte einen Punkt in der Schweiz wählen."
		return
	sel = ll
	sel_name = ""
	load_btn.disabled = false
	_update_info()
	view.queue_redraw()


func _update_info() -> void:
	if waiting:
		return
	if sel == Vector2.ZERO:
		info.text = "Klicken = Ort wählen (dort steht Motion Watch) · Ziehen = verschieben · Mausrad = zoomen"
	else:
		info.text = "%s%.5f, %.5f – das Quadrat (400 × 400 m) wird genau gebaut, rundherum bis 1.6 km die Landschaft." % [(sel_name + " · ") if sel_name != "" else "", sel.x, sel.y]


# ---- search and loading ------------------------------------------------------------------------------------------
func _search() -> void:
	var t := search.text.strip_edges()
	if t == "":
		return
	info.text = "Suche «%s» …" % t
	found = await geo.search(t)
	results.clear()
	for r in found:
		results.add_item(r["label"])
	results.visible = not found.is_empty()
	if found.is_empty():
		info.text = "Nichts gefunden" + (" (" + geo.info + ")" if geo.info.begins_with("Ortssuche") else "") + "."
	elif found.size() == 1:
		_pick_result(0)
	else:
		info.text = "%d Treffer – bitte einen auswählen." % found.size()


func _pick_result(i: int) -> void:
	var r: Dictionary = found[i]
	sel = Vector2(r["lat"], r["lon"])
	sel_name = r["label"]
	zoom = 16
	center = geo.world_px(geo.merc(sel.x, sel.y), zoom)
	results.visible = false
	load_btn.disabled = false
	_update_info()
	view.queue_redraw()


func _next() -> void:
	match step:
		1:
			_load()
		2:
			_show_step(3)
		_:
			_build()


func _load() -> void:
	"""step 1 → 2: get the data of the place (not built yet), then look what kind of place it is"""
	if sel == Vector2.ZERO:
		return
	if geo.loaded and not geo.busy and is_equal_approx(geo.lat, sel.x) and is_equal_approx(geo.lon, sel.y):
		_loaded()
		return
	waiting = true
	load_btn.disabled = true
	geo.load_place(sel.x, sel.y, sel_name, false)


func _loaded() -> void:
	if geo.env == "":
		geo.detect_env()
	w_env = main.ort_env if is_equal_approx(main.ort_lat, sel.x) and is_equal_approx(main.ort_lon, sel.y) else "auto"
	w_hide = main.ort_hide
	w_cars = main.ort_cars
	w_forest = main.ort_forest
	w_camp = main.ort_camp
	_show_step(2)


func _build() -> void:
	"""step 3: build the scene with the choices"""
	main.ort_env = w_env
	main.ort_hide = w_hide
	main.ort_cars = w_cars
	main.ort_forest = w_forest
	main.ort_camp = w_camp
	main._settings_dirty = true
	visible = false
	main.place_loaded()


func _process(_dt: float) -> void:
	if not visible or not waiting:
		return
	if geo.busy:
		info.text = geo.info + " (beim ersten Mal etwa eine Minute, danach ist der Ort gespeichert)"
	else:
		waiting = false
		load_btn.disabled = false
		if geo.loaded and is_equal_approx(geo.lat, sel.x):
			_loaded()
		else:
			info.text = geo.info


# ---- the wizard (from 3D-3.14): step 2 the surroundings, step 3 the objects ------------------------------------------
func _show_step(n: int) -> void:
	step = clampi(n, 1, 3)
	var on_map := step == 1
	view.visible = on_map
	for c in top_bar.get_children():
		if c != title:
			c.visible = on_map
	results.visible = on_map and not found.is_empty() and results.visible
	wiz.visible = not on_map
	back_btn.visible = not on_map
	load_btn.disabled = on_map and sel == Vector2.ZERO
	match step:
		1:
			title.text = "Schritt 1 von 3 · Ort wählen (Schweiz)"
			load_btn.text = "Weiter: Umgebung ›"
			_update_info()
		2:
			title.text = "Schritt 2 von 3 · Umgebung"
			load_btn.text = "Weiter: Objekte ›"
			_page_env()
		3:
			title.text = "Schritt 3 von 3 · Objekte und Verstecke"
			load_btn.text = "Szene bauen ✓"
			_page_objects()


func _clear_wiz() -> void:
	for c in wiz_box.get_children():
		c.queue_free()


func _text(t: String, sz := 14, col := Color(0.85, 0.88, 0.92)) -> Label:
	var l := Label.new()
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	wiz_box.add_child(l)
	return l


func _choice(head: String, opts: Array, cur, on_pick: Callable) -> void:
	"""a row of buttons, one of them pressed"""
	_text(head, 15, Color(1, 1, 1))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 6)
	row.add_theme_constant_override("v_separation", 6)
	wiz_box.add_child(row)
	var grp := ButtonGroup.new()
	for o in opts:
		var b := Button.new()
		b.text = str(o[1])
		b.toggle_mode = true
		b.button_group = grp
		b.custom_minimum_size = Vector2(120, 34)
		b.button_pressed = o[0] == cur
		var key = o[0]
		b.pressed.connect(func(): on_pick.call(key))
		row.add_child(b)


func _page_env() -> void:
	_clear_wiz()
	var place: String = sel_name if sel_name != "" else geo.place_name
	_text("%s – so sieht es dort aus:" % place, 16, Color(1, 1, 1))
	_text("Erkannt: %s  (%s)" % [geo.env_name(geo.env), geo.env_why], 14, Color(0.55, 0.85, 1.0))
	_text("Die Umgebung bestimmt, welche Dinge zusätzlich in die Szene kommen. Gebäude, Strassen, Wald und Wasser kommen immer vom echten Ort.", 13, Color(0.7, 0.74, 0.8))
	var opts := []
	for e in geo.ENVS:
		opts.append([e[0], (e[1] + " → " + geo.env_name(geo.env)) if e[0] == "auto" else e[1]])
	_choice("Umgebung", opts, w_env, _pick_env)
	var hint := _text("", 13, Color(0.8, 0.82, 0.7))
	hint.name = "hint"
	_env_hint()
	info.text = "Umgebung prüfen oder ändern, dann «Weiter»."


func _pick_env(k) -> void:
	w_env = k
	_env_hint()


func _env_hint() -> void:
	var h := wiz_box.get_node_or_null("hint")
	if h == null:
		return
	var e: String = geo.env if w_env == "auto" else w_env
	h.text = "Dazu kommen: " + str(geo.ENV_INFO.get(e, ""))


func _page_objects() -> void:
	_clear_wiz()
	var e: String = geo.env if w_env == "auto" else w_env
	_text("Umgebung: %s – jetzt noch ein paar Voreinstellungen zu den Objekten:" % geo.env_name(e), 15, Color(1, 1, 1))
	_choice("Verstecke (für die Spiele)", [[0, "wenige"], [1, "mittel"], [2, "viele"]], w_hide, func(k): w_hide = k)
	_choice("Fahrzeuge (parkierte Autos)", [[true, "ja"], [false, "keine"]], w_cars, func(k): w_cars = k)
	_choice("Wald und Bäume", [[0, "licht"], [1, "normal"], [2, "dicht"]], w_forest, func(k): w_forest = k)
	_choice("Lager von Motion Watch", [[0, "Wohnwagen und Zelt"], [1, "nur Wohnwagen"], [2, "Zelt und Hütte"]], w_camp, func(k): w_camp = k)
	_text("Mit «Szene bauen» entsteht der Ort. Ändern kann man es jederzeit: Karte öffnen (K) und den Ort nochmals laden.", 13, Color(0.7, 0.74, 0.8))
	info.text = "Alles gewählt? Dann «Szene bauen»."
