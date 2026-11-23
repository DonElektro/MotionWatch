extends RefCounted
## Roboter-Labor direkt öffnen (Kachel «🤖 Roboter-Labor» der Homepage, Besitzer 22.11.2026): Startoption --roboter, im
## Browser Sim/?roboter=1 (web.gd roboter_args); der Wert geht als «variante» an das Labor (control open). Kurz nach dem
## Start (AUTOSTART_SEK) geht das Labor (roboter_labor.gd) auf.
## Vorerst nur am PC: auf kleinen Bildschirmen (kürzere Seite unter KLEIN_PT Punkten, im Browser CSS-Pixel) zuerst der kurze
## Hinweis «Am besten am PC», das Bedienfeld ist zu und geht über den Knopf «Bedienfeld» auf (eine Taste H gibt es dort nicht);
## das Labor geht trotzdem. Das Labor selbst bleibt, wie es ist: hier nur Öffnen und die zwei Dinge fürs Handy obendrauf.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const AUTOSTART_SEK := 3.0             # the start of the simulator first (scene, panel, news), then the lab
const KLEIN_PT := 600.0

# tests: the meta «klein_test» (true / false) of the lab node instead of the size of the window (no static var: with one,
# Godot 4.3 crashed at the exit of other tests, signal 11 after «… OK»)


static func autostart_ziel(args: PackedStringArray) -> String:
	"""--roboter / --roboter=<variante> (browser: …?roboter=1) opens the lab after the start: the variant ("1" for a plain
	--roboter), "" = not wanted; the game (--grossvater-…) goes first"""
	var v := ""
	for x in args:
		if str(x) == "--grossvater-neu" or str(x).begins_with("--grossvater-kapitel="):
			return ""
		if str(x) == "--roboter":
			v = "1"
		elif str(x).begins_with("--roboter="):
			v = str(x).substr(10)
	return v


static func autostart_pruefen(m, args = null) -> void:
	"""called once after the start (main.gd); args: tests, instead of the real start options"""
	var alle: PackedStringArray = PackedStringArray(args) if args != null else OS.get_cmdline_args() + OS.get_cmdline_user_args() + preload("res://scripts/web.gd").args()
	var v := autostart_ziel(alle)
	if v == "":
		return
	await m.get_tree().create_timer(AUTOSTART_SEK).timeout
	if m.get("news") != null and m.news.has_method("close") and m.news.visible:
		m.news.close(false)                             # (like «OK» on the card)
	oeffnen(m, v)


static func oeffnen(m, variante := "1") -> void:
	"""open the lab the same way as /control {"action": "roboter", "do": "open", "variante": …} (the lab decides the variant)"""
	var r = m.roboter
	if r == null or r.is_open():
		return
	r.control({"do": "open", "variante": variante})
	print("Roboter-Labor: geöffnet (Startoption --roboter)")
	if klein(r):
		handy(r)


static func klein_fuer(size: Vector2) -> bool:
	"""a phone-sized window (points): the shorter side below KLEIN_PT"""
	return minf(size.x, size.y) < KLEIN_PT


static func klein(r) -> bool:
	if r.has_meta("klein_test"):
		return bool(r.get_meta("klein_test"))
	return r.is_inside_tree() and klein_fuer(r.get_viewport().get_visible_rect().size)


static func _panel(r, on: bool) -> void:
	var p: Control = r._w.get("panel")
	if p != null:
		p.visible = on
		r._panel_on = on                                # (the key H of the lab toggles from here)


static func handy(r) -> void:
	"""phone: panel closed, a button «Bedienfeld» in the bar of the views, the hint «Am besten am PC» (OK closes it)"""
	_panel(r, false)
	var vb: Control = r._w.get("viewbar")
	if vb != null:
		var pb := Button.new()
		pb.name = "bedienfeld_knopf"
		pb.text = T.t("Bedienfeld")
		pb.focus_mode = Control.FOCUS_NONE
		pb.pressed.connect(func(): _panel(r, not bool(r._panel_on)))
		vb.add_child(pb)
	var area: Control = r._w.get("area")
	if area == null:
		return
	var box := PanelContainer.new()
	box.name = "hinweis_pc"
	box.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ACC, 10, 12, 2))
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.offset_left = -170
	box.offset_right = 170
	box.offset_top = -90
	box.offset_bottom = 90
	area.add_child(box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	box.add_child(v)
	var h := Label.new()
	h.text = T.t("Am besten am PC")
	h.add_theme_font_override("font", UI.heading_font())
	h.add_theme_font_size_override("font_size", 17)
	v.add_child(h)
	var l := UI.small(T.t("Das Roboter-Labor ist für Maus, Tastatur und einen grossen Bildschirm gebaut. Auf dem Handy geht es trotzdem – das Bedienfeld öffnest du mit «Bedienfeld»."), UI.TXT)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(300, 0)
	v.add_child(l)
	var ok := Button.new()
	ok.name = "ok"
	ok.text = T.t("OK")
	UI.primary(ok)
	ok.pressed.connect(box.queue_free)
	v.add_child(ok)
