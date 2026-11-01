extends SceneTree
## Test ohne Bild: Tasten statt Mausrad (simulator3d/scripts/tasten.gd, Touchpad ohne Scrollfunktion).
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/tasten_test.gd" -- --no-update --no-tour
## Prüft über den echten Eingabeweg (push_input): + / − (auch Ziffernblock, = der US-Tastatur) zoomen die freie Ansicht und
## die Kamera-Ansicht, nicht beim Tippen in ein Textfeld; Bild ↓ / ↑ blättern das Seitenmenü und eine Liste unter der Maus;
## Shift + Bild ↑ hebt den Mast, beim Erkunden Bild ↑ ohne Liste auch (wie bisher); Pfeile drehen / neigen die freie Ansicht,
## nicht wenn der Mover fährt; F1 öffnet und schliesst die Hilfe (übersetzt in en / fr / it / rm); die Scrollbalken sind
## sichtbar und breit genug zum Ziehen. Ende: «Tasten-Test OK» oder «SCRIPT ERROR: Tasten-Test: …» (Exit-Code 0 / 1).

var errs := []
var m = null


func _ok(what: String, cond: bool, info = null) -> void:
	print(("  ok   " if cond else "  FEHLER ") + what + ("" if info == null or cond else "  (%s)" % str(info)))
	if not cond:
		errs.append(what + ("" if info == null else " (%s)" % str(info)))


func _init() -> void:
	# the texts of the help: all in the 4 other languages
	var tx = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
	var src := FileAccess.get_file_as_string("res://scripts/tasten.gd")
	var rx := RegEx.create_from_string('T\\.t\\("([^"]+)"\\)')
	var n := 0
	for mt in rx.search_all(src):
		var row = tx.get(mt.get_string(1), null)
		var full: bool = row is Dictionary
		if full:
			for l in ["en", "fr", "it", "rm"]:
				full = full and str(row.get(l, "")) != ""
		_ok("übersetzt: " + mt.get_string(1).left(50), full)
		n += 1
	_ok("Hilfe hat Texte", n >= 10, n)
	var th: Theme = load("res://scripts/ui_style.gd").theme()
	var sb: StyleBox = th.get_stylebox("grabber", "VScrollBar")
	_ok("Scrollbalken mind. 10 px breit", sb.get_minimum_size().x >= 10.0, sb.get_minimum_size())
	_ok("Scrollbalken sichtbar (Griff nicht wie der Hintergrund)", (sb as StyleBoxFlat).bg_color.v > 0.3, (sb as StyleBoxFlat).bg_color)
	_welt.call_deferred()


func _ende() -> void:
	if m != null and m.tasten != null:
		m.tasten.test_hover = null
	if errs.is_empty():
		print("Tasten-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Tasten-Test: " + str(e))
		quit(1)


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func key(kc: int, shift := false) -> void:
	for pr in [true, false]:
		var e := InputEventKey.new()
		e.keycode = kc
		e.physical_keycode = kc
		e.pressed = pr
		e.shift_pressed = shift
		root.push_input(e)
	await process_frame


func _welt() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(90):
		await process_frame
	var t = m.tasten
	_ok("tasten.gd geladen", t != null)
	if t == null:
		_ende()
		return
	t.test_mouse = Vector2(300, 300)
	m.explore.set_on(false)
	m.set_mover(false)
	m.set_view(0)
	m.show_panel(true)
	await _warte(0.3)
	# + / − in the free view (KEY_PLUS of the German keyboard, number pad, = of the US keyboard)
	for kc in [KEY_PLUS, KEY_KP_ADD, KEY_EQUAL]:
		var p0: Vector3 = m.view_cam.global_position
		await key(kc)
		_ok("Taste %s zoomt die freie Ansicht" % OS.get_keycode_string(kc), m.view_cam.global_position.distance_to(p0) > 0.01 and t.last == "view", t.last)
	var p1: Vector3 = m.view_cam.global_position
	await key(KEY_MINUS)
	await key(KEY_KP_SUBTRACT)
	_ok("− zoomt zurück", m.view_cam.global_position.distance_to(p1) > 0.01)
	# typing into a text field: the keys stay there
	var le := LineEdit.new()
	m.ui_layer.add_child(le)
	le.grab_focus()
	await process_frame
	var p2: Vector3 = m.view_cam.global_position
	t.last = ""
	await key(KEY_KP_ADD)
	await key(KEY_PAGEDOWN)
	_ok("beim Tippen (main.typing) keine Wirkung", m.typing() and m.view_cam.global_position.distance_to(p2) < 0.001 and t.last == "", t.last)
	le.release_focus()
	le.queue_free()
	await process_frame
	# camera view 1: only the picture zooms (fov), the view stays camera 1
	m.set_view(1)
	await process_frame
	await key(KEY_PLUS)
	await key(KEY_PLUS)
	m._fly(0.0)                                        # (headless the TV / spectator may own the view camera)
	_ok("Kamera 1: + zoomt das Bild", m.view_mode == 1 and m.view_zoom > 1.4 and m.view_cam.fov < 30.0, [m.view_mode, m.view_zoom, m.view_cam.fov])
	await key(KEY_MINUS)
	await key(KEY_MINUS)
	await key(KEY_MINUS)
	_ok("Kamera 1: − zurück bis 1×", is_equal_approx(m.view_zoom, 1.0), m.view_zoom)
	m.set_view(0)
	# Bild ↓ / ↑: the side menu
	var sm: ScrollContainer = t.side_menu()
	_ok("Seitenmenü gefunden", sm != null)
	if sm != null:
		for b in m.fold_bodies:                        # open all cards so the menu is long
			m.UI.set_open(b, true)
		await _warte(0.3)
		var bar := sm.get_v_scroll_bar()
		bar.value = 0
		await process_frame
		_ok("Seitenmenü hat einen Scrollbalken", bar.max_value > bar.page, [bar.max_value, bar.page])
		_ok("Scrollbalken des Menüs sichtbar und ziehbar", bar.visible and bar.mouse_filter != Control.MOUSE_FILTER_IGNORE and bar.size.x >= 9.0, [bar.visible, bar.size])
		await key(KEY_PAGEDOWN)
		var v1 := bar.value
		_ok("Bild ↓ blättert das Seitenmenü", v1 > 20.0 and t.last == "scroll:menu", [v1, t.last])
		await key(KEY_PAGEUP)
		_ok("Bild ↑ blättert zurück", bar.value < v1, bar.value)
	# a list under the mouse
	var sc := ScrollContainer.new()
	sc.position = Vector2(20, 120)
	sc.size = Vector2(200, 120)
	m.ui_layer.add_child(sc)
	var vb := VBoxContainer.new()
	sc.add_child(vb)
	for i in range(40):
		var l := Label.new()
		l.text = "Zeile %d" % i
		vb.add_child(l)
	await _warte(0.2)
	t.test_hover = vb.get_child(3)
	await key(KEY_PAGEDOWN)
	_ok("Bild ↓ blättert die Liste unter der Maus", sc.scroll_vertical > 50 and t.last == "scroll:ScrollContainer", [sc.scroll_vertical, t.last])
	# Shift + Bild ↑ = mast; exploring: Bild ↑ over the list scrolls, without a list the mast (as before)
	var h0: float = m.mast_h
	t.test_hover = null
	await key(KEY_PAGEUP, true)
	_ok("Shift + Bild ↑ hebt den Mast", m.mast_h > h0 + 0.05, [h0, m.mast_h])
	await key(KEY_PAGEDOWN, true)
	m.explore.set_on(true)
	await _warte(0.3)
	var h1: float = m.mast_h
	var s1: int = sc.scroll_vertical
	t.test_hover = vb.get_child(3)
	await key(KEY_PAGEDOWN)
	_ok("Erkunden: Bild ↓ über der Liste blättert (Mast bleibt)", sc.scroll_vertical > s1 and absf(m.mast_h - h1) < 0.001, [sc.scroll_vertical, m.mast_h])
	t.test_hover = null
	await key(KEY_PAGEUP)
	_ok("Erkunden: Bild ↑ ohne Liste = Mast (wie bisher)", m.mast_h > h1 + 0.05, [h1, m.mast_h])
	await key(KEY_PAGEDOWN)
	var d0: float = m.explore.dist
	await key(KEY_KP_ADD)
	_ok("Erkunden: + zoomt näher", m.explore.dist < d0 and t.last == "explore", [d0, m.explore.dist, t.last])
	m.explore.set_on(false)
	sc.queue_free()
	await _warte(0.3)
	# arrows: turn the free view (mover off), not while the mover drives
	m.set_mover(false)
	m.set_view(0)
	await process_frame
	_ok("Pfeile frei (Mover aus, freie Ansicht)", t.arrows_free())
	var b0: Basis = m.view_cam.global_transform.basis
	t.test_arrows = Vector2(1, 0)
	await _warte(0.4)
	t.test_arrows = Vector2.ZERO
	var b1: Basis = m.view_cam.global_transform.basis
	_ok("→ dreht die Ansicht", b0.z.angle_to(b1.z) > 0.05, b0.z.angle_to(b1.z))
	var y0: float = m.view_cam.global_position.y
	t.test_arrows = Vector2(0, -1)
	await _warte(0.4)
	t.test_arrows = Vector2.ZERO
	_ok("↑ neigt die Ansicht (Kamera geht höher)", m.view_cam.global_position.y > y0 + 0.01, [y0, m.view_cam.global_position.y])
	m.set_mover(true)
	await process_frame
	_ok("Mover an: Pfeile gehören dem Mover", not t.arrows_free())
	m.set_mover(false)
	# F1: help
	await key(KEY_F1)
	_ok("F1 öffnet die Tasten-Hilfe", t.help_box != null and t.help_box.visible)
	await key(KEY_ESCAPE)
	_ok("Esc schliesst sie", t.help_box != null and not t.help_box.visible)
	await key(KEY_F1)
	await key(KEY_F1)
	_ok("F1 schliesst sie auch", not t.help_box.visible)
	_ok("Hilfe hat 8 Zeilen", t.help_lines().size() == 8, t.help_lines().size())
	_ende()
