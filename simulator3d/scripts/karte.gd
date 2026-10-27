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
	var t := Label.new()
	t.text = "Ort wählen (Schweiz)"
	bar.add_child(t)
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
	var bottom := HBoxContainer.new()
	bottom.add_theme_constant_override("separation", 8)
	v.add_child(bottom)
	info = Label.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.text = "Klicken = Ort wählen · Ziehen = verschieben · Mausrad = zoomen"
	bottom.add_child(info)
	load_btn = Button.new()
	load_btn.text = "Diesen Ort laden"
	load_btn.disabled = true
	load_btn.pressed.connect(_load)
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


func _load() -> void:
	if sel == Vector2.ZERO:
		return
	waiting = true
	load_btn.disabled = true
	main.choose_place(sel.x, sel.y, sel_name)


func _process(_dt: float) -> void:
	if not visible or not waiting:
		return
	if geo.busy:
		info.text = geo.info + " (beim ersten Mal etwa eine Minute, danach ist der Ort gespeichert)"
	else:
		waiting = false
		load_btn.disabled = false
		if geo.loaded and is_equal_approx(geo.lat, sel.x):
			visible = false
		else:
			info.text = geo.info
