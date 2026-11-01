extends Node
## Tasten statt Mausrad (Wunsch Daniel, 01.11.2026: Touchpad ohne Scrollfunktion am Linux-PC). Alles, was das Mausrad kann,
## geht auch mit der Tastatur:
##   + / −  (auch Ziffernblock; US-Tastatur: = / −)  zoomen - in der freien Ansicht, in den Kamera-Ansichten 1 / 2 (nur das
##          Bild auf dem Bildschirm, MoveEye sieht unverändert), beim Erkunden, in der Flugkamera (explore.gd hat es schon),
##          bei Maggie, über der Übersichtskarte, der Ortskarte (karte.gd), der Werkstatt und der Karte im Entwicklertool.
##   Bild ↑ / Bild ↓  blättern die Liste unter der Maus (ScrollContainer, ItemList, Textfeld, Handy-Seite), sonst das offene
##          Seitenmenü. Shift + Bild ↑ / ↓ = Mast höher / tiefer (überall). Beim Erkunden bleibt Bild ↑ / ↓ ohne Shift wie
##          bisher der Mast, ausser die Maus steht über einer Liste (explore.gd fragt scroll_page).
##   Pfeiltasten  drehen (← →) und neigen (↑ ↓) die freie Ansicht bzw. schauen in der Flugkamera um - nur wenn die Pfeile
##          nicht schon belegt sind (Mover an = Pfeile fahren, Erkunden, Spiel am PC, Maggie, Rundgang, Karte offen).
##   F1     zeigt eine kurze Tasten-Hilfe (5 Sprachen, i18n/texte.json); F1, Esc oder ein Klick schliesst sie. (H ist schon
##          «Bedienfeld ein / aus» und bleibt so.)
## Nie, während jemand in ein Textfeld tippt (main.typing()), und nie mit Ctrl / Alt / Meta (deren Kürzel bleiben frei).
## Steuerelemente, die das Rad selbst auswerten, tragen das Meta «rad_zoom» (zoomen) bzw. «rad_scroll» (blättern):
## dorthin geht ein künstliches Mausrad an der Mausposition. Test: werkzeuge/tasten_test.gd.

const T = preload("res://scripts/i18n.gd")
const UIS = preload("res://scripts/ui_style.gd")

const ZOOM_IN := [KEY_PLUS, KEY_KP_ADD, KEY_EQUAL]
const ZOOM_OUT := [KEY_MINUS, KEY_KP_SUBTRACT]
const TURN_PX := 260.0                 # arrows: like dragging the mouse this many pixels per second
const VIEW_ZOOM_MAX := 4.0

static func help_rows() -> Array:
	"""[key, what it does] in the current language (texts in i18n/texte.json)"""
	return [
		["+ / −", T.t("zoomen (auch Ziffernblock) – Ansicht, Kamera, Karte, Werkstatt")],
		[T.t("Bild ↑ / Bild ↓"), T.t("blättert die Liste unter der Maus, sonst das Seitenmenü")],
		[T.t("Shift + Bild ↑ / ↓"), T.t("Mast höher / tiefer (beim Erkunden auch ohne Shift)")],
		["← → ↑ ↓", T.t("Ansicht drehen und neigen (fährt der Mover, steuern die Pfeile ihn)")],
		["W A S D Q E", T.t("fliegen · Shift schneller")],
		["0 · 1 · 2 · 3", T.t("freie Ansicht · Kamera 1 · Kamera 2 · Wärmebild")],
		["H", T.t("Bedienfeld ein / aus")],
		[T.t("Scrollbalken"), T.t("rechts an jeder Liste: mit der Maus ziehen")],
	]

var main
var help_box: PanelContainer = null
var test_hover: Control = null         # tests: the control «under the mouse» (instead of gui_get_hovered_control)
var test_mouse := Vector2(-1, -1)      # tests: the mouse position
var test_arrows := Vector2.ZERO        # tests: arrows held (x: → = +1, y: ↓ = +1)
var last := ""                         # what the last key did (tests / state)
var _wst = null                        # werkstatt.gd once it exists (main.werkstatt would make it)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


# ---- where the mouse is ----------------------------------------------------------------------------------------------------
func mouse_pos() -> Vector2:
	if test_mouse.x >= 0.0:
		return test_mouse
	return get_viewport().get_mouse_position()


func hovered() -> Control:
	if test_hover != null:
		return test_hover if is_instance_valid(test_hover) and test_hover.is_visible_in_tree() else null
	var vp := get_viewport()
	if vp == null:
		return null
	var c := vp.gui_get_hovered_control()
	if c == null or not c.is_visible_in_tree():
		return null
	var r := Rect2(Vector2.ZERO, vp.get_visible_rect().size)
	return c if r.has_point(mouse_pos()) else null         # the mouse left the window: nothing is under it


static func _with_meta(c: Control, key: String) -> Control:
	var n: Node = c
	while n != null:
		if n is Control and (n as Control).has_meta(key):
			return n
		n = n.get_parent()
	return null


# ---- Bild ↑ / Bild ↓ -----------------------------------------------------------------------------------------------------
static func _vbar(c: Control) -> ScrollBar:
	"""the vertical scroll bar of a list, if it can scroll (content longer than the box)"""
	var sb: ScrollBar = null
	if c is ScrollContainer:
		if (c as ScrollContainer).vertical_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED:
			return null
		sb = (c as ScrollContainer).get_v_scroll_bar()
	elif c is ItemList:
		sb = (c as ItemList).get_v_scroll_bar()
	elif c is RichTextLabel and (c as RichTextLabel).scroll_active:
		sb = (c as RichTextLabel).get_v_scroll_bar()
	elif c is TextEdit:
		sb = (c as TextEdit).get_v_scroll_bar()
	if sb == null or sb.max_value - sb.page <= sb.min_value + 0.5:
		return null
	return sb


static func scroll_target(c: Control) -> Control:
	"""the nearest list round c (c itself or a parent) that can scroll"""
	var n: Node = c
	while n != null:
		if n is Control and _vbar(n) != null and (n as Control).is_visible_in_tree():
			return n
		n = n.get_parent()
	return null


func side_menu() -> ScrollContainer:
	"""the scrolling part of the open side panel (main_menues.gd: ui_box sits in a ScrollContainer)"""
	if main == null or main.ui_root == null or not main.ui_root.is_visible_in_tree() or main.ui_box == null:
		return null
	var sc = main.ui_box.get_parent()
	return sc if sc is ScrollContainer else null


func scroll_page(dir: int, menu_too := true) -> bool:
	"""one page down (dir +1) or up (-1): the list under the mouse, else (menu_too) the open side menu. True = something scrolled"""
	var h := hovered()
	var ws: Control = _with_meta(h, "rad_scroll") if h != null else null
	if ws != null:                                     # the phone page: three notches of the wheel there
		for i in range(3):
			_wheel(-dir, mouse_pos())
		last = "scroll:phone"
		return true
	var t: Control = scroll_target(h) if h != null else null
	if t == null and menu_too:
		var sm := side_menu()
		if sm != null and _vbar(sm) != null:
			t = sm
	if t == null:
		return false
	var sb := _vbar(t)
	var page := maxf(40.0, (t.size.y if not (t is ItemList) else sb.page) * 0.85)
	sb.value = clampf(sb.value + dir * page, sb.min_value, sb.max_value - sb.page)
	last = "scroll:%s" % ("menu" if t == side_menu() else t.get_class())
	return true


# ---- + / − -------------------------------------------------------------------------------------------------------------------
func _wheel(dir: int, p: Vector2) -> void:
	"""an artificial notch of the mouse wheel at p (dir +1 = up = zoom in) through the whole input path"""
	for pr in [true, false]:
		var w := InputEventMouseButton.new()
		w.button_index = MOUSE_BUTTON_WHEEL_UP if dir > 0 else MOUSE_BUTTON_WHEEL_DOWN
		w.pressed = pr
		w.factor = 1.0
		w.position = p
		w.global_position = p
		get_viewport().push_input(w)


func _werkstatt():
	if _wst == null or not is_instance_valid(_wst):
		_wst = null
		for c in main.get_children():
			var s = c.get_script()
			if s != null and str(s.resource_path).ends_with("/werkstatt.gd"):
				_wst = c
				break
	return _wst


func free_point() -> Vector2:
	"""the middle of the 3D view left of the open side panel"""
	var vs: Vector2 = get_viewport().get_visible_rect().size
	var right := vs.x
	if main.ui_root != null and main.ui_root.is_visible_in_tree():
		right = minf(right, main.ui_root.get_global_rect().position.x)
	return Vector2(maxf(40.0, right * 0.5), vs.y * 0.5)


func zoom(dir: int) -> String:
	"""+1 = closer, -1 = further; what was zoomed (for tests)"""
	var h := hovered()
	var p := mouse_pos()
	var z: Control = _with_meta(h, "rad_zoom") if h != null else null
	if z != null:                                      # minimap, Ortskarte, Werkstatt, Entwickler-Karte: their own wheel
		_wheel(dir, p)
		return "wheel:" + str(z.get_meta("rad_zoom"))
	if main.karte != null and main.karte.visible and main.karte.view != null and main.karte.view.is_visible_in_tree():
		_wheel(dir, main.karte.view.get_global_rect().get_center())
		return "wheel:karte"
	var ws = _werkstatt()
	if ws != null and ws.is_open() and ws.vpc != null and ws.vpc.is_visible_in_tree():
		_wheel(dir, ws.vpc.get_global_rect().get_center())
		return "wheel:werkstatt"
	var ex = main.explore
	if ex != null and ex.fly:
		ex.fly_step(dir)                               # the fly camera: + / − = speed (as before, explore.gd)
		return "fly"
	if ex != null and ex.on:
		ex.dist = clampf(ex.dist - 0.8 * dir, 2.5, 30.0)
		return "explore"
	if main.maggie != null and is_instance_valid(main.maggie) and main.maggie.walking():
		main.maggie.cam_dist = clampf(main.maggie.cam_dist - 0.6 * dir, 2.5, 16.0)
		return "maggie"
	if main.view_mode in [1, 2]:                       # camera views: only the picture on the screen (MoveEye sees the same)
		main.view_zoom = clampf(main.view_zoom * (1.25 if dir > 0 else 0.8), 1.0, VIEW_ZOOM_MAX)
		return "camera"
	var q := p if (p.x >= 0.0 and not main._over_hud(p) and Rect2(Vector2.ZERO, get_viewport().get_visible_rect().size).has_point(p)) else free_point()
	main._zoom_at(q, float(dir))
	return "view"


# ---- the keys ----------------------------------------------------------------------------------------------------------------
func _blocked() -> bool:
	if main == null or main.typing():
		return true
	if main.phone != null and main.phone.visible and main.phone.screen != null and main.phone.screen.has_focus():
		return true                                    # keys go to the phone
	return preload("res://scripts/trailer.gd").busy(main)


func _input(ev: InputEvent) -> void:
	if not (ev is InputEventKey) or not ev.pressed:
		return
	var k := ev as InputEventKey
	if help_box != null and help_box.visible and not k.echo and k.keycode in [KEY_F1, KEY_ESCAPE]:
		show_help(false)
		get_viewport().set_input_as_handled()
		return
	if k.ctrl_pressed or k.alt_pressed or k.meta_pressed or _blocked():
		return
	var kc := k.keycode
	if kc == KEY_F1 and not k.echo:
		show_help(help_box == null or not help_box.visible)
		get_viewport().set_input_as_handled()
	elif kc in ZOOM_IN or kc in ZOOM_OUT:
		if main.explore != null and main.explore.fly:
			return                                     # explore.gd: + / − = speed of the fly camera
		last = zoom(1 if kc in ZOOM_IN else -1)
		get_viewport().set_input_as_handled()
	elif kc in [KEY_PAGEUP, KEY_PAGEDOWN]:
		var dir := 1 if kc == KEY_PAGEDOWN else -1
		if k.shift_pressed:
			main.set_mast(main.mast_h - 0.1 * dir)     # Shift + Bild ↑ = higher
			last = "mast"
		elif main.explore != null and main.explore.on:
			return                                     # explore.gd: the list under the mouse, else the mast (as before)
		elif not scroll_page(dir):
			return
		get_viewport().set_input_as_handled()
	elif kc in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN] and arrows_free():
		var f := get_viewport().gui_get_focus_owner()
		if f == null or f is BaseButton and not (f is OptionButton):
			get_viewport().set_input_as_handled()      # a clicked button keeps the focus: the arrows turn the view, not the focus


# ---- arrows ------------------------------------------------------------------------------------------------------------------
func arrows_free() -> bool:
	"""may the arrows turn the view? Not where they already do something"""
	if _blocked() or main.karte == null or main.karte.visible:
		return false
	if main.mover_on or main.spectate:
		return false                                   # rover_pad.gd: the arrows drive the mover
	if main.localplay != null and main.localplay.active:
		return false                                   # the player at the PC
	if main.maggie != null and is_instance_valid(main.maggie) and bool(main.maggie.running):
		return false
	if main.mehr != null and main.mehr.get("tour") != null and bool(main.mehr.tour.active):
		return false                                   # the tour: ← → back / on
	var ws = _werkstatt()
	if ws != null and ws.is_open():
		return false
	var f := get_viewport().gui_get_focus_owner()
	if f != null and (f is Range or f is ItemList or f is Tree or f is OptionButton or f is LineEdit or f is TextEdit):
		return false                                   # a slider / list with the focus: its arrows stay
	var ex = main.explore
	if ex != null and ex.on:
		return false
	return (ex != null and ex.fly) or main.view_mode == 0


func arrow_dir() -> Vector2:
	if test_arrows != Vector2.ZERO:
		return test_arrows
	return Vector2(float(Input.is_key_pressed(KEY_RIGHT)) - float(Input.is_key_pressed(KEY_LEFT)),
			float(Input.is_key_pressed(KEY_DOWN)) - float(Input.is_key_pressed(KEY_UP)))


func turn(a: Vector2, dt: float) -> void:
	"""a.x: → = +1 (turn right), a.y: ↓ = +1 (tilt down / look down)"""
	var cam: Camera3D = main.view_cam
	if main.explore != null and main.explore.fly:
		var r := cam.rotation
		cam.rotation = Vector3(clampf(r.x - a.y * dt * 1.0, -1.5, 1.5), r.y - a.x * dt * 1.4, 0.0)
		return
	if main.m_btn != 0:
		return                                         # the mouse drags right now
	if main.fly_tw != null and main.fly_tw.is_running():
		return
	main.follow = false
	var g = main._ground_at(free_point())
	main.m_grab = g if g != null else cam.global_position - cam.global_transform.basis.z * 30.0
	main._orbit(Vector2(a.x, -a.y) * TURN_PX * dt)        # ↑ = the view from higher up


func _process(dt: float) -> void:
	if main == null or main.view_cam == null:
		return
	var a := arrow_dir()
	if a != Vector2.ZERO and arrows_free():
		turn(a, minf(dt, 0.1))


# ---- F1: the help --------------------------------------------------------------------------------------------------------
func show_help(on: bool) -> void:
	if on and help_box == null:
		_build_help()
	if help_box != null:
		help_box.visible = on
	last = "help:%s" % on


func _build_help() -> void:
	var cl := CanvasLayer.new()
	cl.layer = 62
	add_child(cl)
	var dim := Control.new()                           # a click anywhere closes it
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cl.add_child(dim)
	help_box = PanelContainer.new()
	help_box.theme = UIS.theme()
	help_box.set_anchors_preset(Control.PRESET_CENTER)
	help_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	help_box.grow_vertical = Control.GROW_DIRECTION_BOTH
	help_box.custom_minimum_size = Vector2(520, 0)
	dim.add_child(help_box)
	help_box.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			show_help(false))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	help_box.add_child(v)
	v.add_child(UIS.heading(T.t("Tasten ohne Mausrad")))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 14)
	g.add_theme_constant_override("v_separation", 4)
	v.add_child(g)
	for row in help_rows():
		var kl := Label.new()
		kl.text = str(row[0])
		kl.add_theme_color_override("font_color", UIS.ACC.lightened(0.25))
		g.add_child(kl)
		var dl := Label.new()
		dl.text = str(row[1])
		dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		dl.custom_minimum_size = Vector2(330, 0)
		g.add_child(dl)
	v.add_child(UIS.small(T.t("F1, Esc oder Klick: schliessen")))


func help_lines() -> Array:
	"""the help as text in the current language (tests, «Tasten» card)"""
	var out := []
	for row in help_rows():
		out.append("%s: %s" % [row[0], row[1]])
	return out


func state() -> Dictionary:
	return {"ok": true, "help": help_box != null and help_box.visible, "last": last, "view_zoom": main.view_zoom, "arrows": arrows_free()}
