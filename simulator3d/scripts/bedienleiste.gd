extends HFlowContainer
## Bedienleiste (Paket real-layout-leiste, Besitzer 31.10.2026): dieselbe Leiste wie oben auf jeder Seite von MoveEye
## (Web 639o #mwbar, Pi-Fenster App._mwbar): «Einfach | Experte» und rechts das Menü «Darstellung» (MoveEye 3.88) mit
## «Symbole farbig | schlicht» und «Alle zuklappen · Meine Ansicht · Nur Gruppen · Alle aufklappen».
## Ein Baustein für jedes Menü-Fenster des Simulators: build(main) mit
## einem Objekt, das die drei Wechsel kennt (je EINE Funktion, Review P0):
##   set_simple(on: bool)        ui_simple   (true = einfach)
##   set_icons(v: String)        ui_icons    ("color" | "plain")
##   _fold_all(how, true)        how = "close" | "mine" | "groups" | "open" (mine: set_mine; jede Änderung: _mine_change)
## HFlowContainer: wird das Fenster schmal, bricht die Leiste um (kein seitliches Scrollen).

const UI = preload("res://scripts/ui_style.gd")
const T := preload("res://scripts/i18n.gd")

var host: Object
var simple_seg: HBoxContainer
var icons_seg: HBoxContainer              # (before MoveEye 3.88; now in the menu «Darstellung» - stays null)
var view_btn: MenuButton
var sg_cb: CheckButton
var fold_btns := {}


func build(h: Object, fold := true) -> void:
	"""fold = false: a window without fold cards - the three buttons are there but grey (the bar stays the same)"""
	host = h
	add_theme_constant_override("h_separation", 8)
	add_theme_constant_override("v_separation", 6)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	simple_seg = UI.segment(T.t("Einfach"), T.t("Experte"), not bool(h.get("ui_simple")), func(expert): h.set_simple(not expert), true)
	simple_seg.custom_minimum_size = Vector2(150, 0)
	simple_seg.tooltip_text = T.t("Einfach: nur das Wichtigste. «Experte» zeigt alle Einstellungen.")
	add_child(simple_seg)
	# MoveEye 3.88 (Design «Klar» Etappe 1, Besitzer 13.11.2026): «Symbole» and the fold buttons are in ONE menu «Darstellung»
	# at the right end of the bar (like the web bar 639o and the Pi window); «Einfach | Experte» stays visible.
	# «Nur Gruppen» is its own line (before only a long press on «Meine Ansicht»).
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(sp)
	view_btn = MenuButton.new()
	view_btn.text = T.t("Darstellung") + " ▾"
	view_btn.flat = false
	view_btn.custom_minimum_size = Vector2(0, 36)
	view_btn.tooltip_text = T.t("Symbole: grüner Punkt oder grünes Symbol = eingeschaltet")
	var pm: PopupMenu = view_btn.get_popup()
	pm.add_separator(T.t("Symbole"))
	pm.add_radio_check_item(T.t("Symbole farbig"), 1)
	pm.add_radio_check_item(T.t("schlicht"), 2)
	pm.add_separator(T.t("Menüs auf- und zuklappen"))
	for it in [["close", T.t("Alle zuklappen"), 10], ["mine", T.t("Meine Ansicht"), 11], ["groups", T.t("Nur Gruppen"), 12], ["open", T.t("Alle aufklappen"), 13]]:
		pm.add_item(it[1], it[2])
		pm.set_item_disabled(pm.get_item_index(it[2]), not fold)
	if not fold:
		pm.set_item_tooltip(pm.get_item_index(10), T.t("Auf dieser Seite gibt es nichts zum Klappen"))
	_paint_icons(str(h.get("ui_icons")))
	pm.id_pressed.connect(_on_view)
	add_child(view_btn)


func _on_view(id: int) -> void:
	"""a line of the menu «Darstellung»"""
	if id == 1 or id == 2:
		var v := "color" if id == 1 else "plain"
		host.set_icons(v)
		_paint_icons(v)
	elif id >= 10 and id <= 13:
		host._fold_all(["close", "mine", "groups", "open"][id - 10], true)


func paint(simple: bool, icons: String, start_groups: bool) -> void:
	"""show the current values (after a change from outside, e.g. the page of MoveEye)"""
	if simple_seg != null and simple_seg.has_meta("paint"):
		simple_seg.get_meta("paint").call(not simple)
	if icons_seg != null and icons_seg.has_meta("paint"):
		icons_seg.get_meta("paint").call(icons == "plain")
	_paint_icons(icons)
	if sg_cb != null and sg_cb.button_pressed != start_groups:
		sg_cb.set_pressed_no_signal(start_groups)


func _paint_icons(icons: String) -> void:
	if view_btn == null:
		return
	var pm: PopupMenu = view_btn.get_popup()
	pm.set_item_checked(pm.get_item_index(1), icons != "plain")
	pm.set_item_checked(pm.get_item_index(2), icons == "plain")


var _hold_t := -1.0
var _hold_long := false


func _mine_button(b: Button, h: Object) -> void:
	"""639r: a click = «Meine Ansicht»; a long press (0.6 s) or a right click = «Nur Gruppen» (it stays, Besitzer: nothing removed)"""
	b.button_down.connect(func():
		_hold_long = false
		_hold_t = Time.get_ticks_msec() / 1000.0
		var t := b.get_tree().create_timer(0.6)
		var at := _hold_t
		t.timeout.connect(func():
			if _hold_t == at and b.button_pressed:
				_hold_long = true
				h._fold_all("groups", true)))
	b.button_up.connect(func(): _hold_t = -1.0)
	b.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_RIGHT and ev.pressed:
			_hold_long = true
			h._fold_all("groups", true))
	b.pressed.connect(func():
		if _hold_long:
			_hold_long = false
			return
		h._fold_all("mine", true))
