extends HFlowContainer
## Bedienleiste (Paket real-layout-leiste, Daniel 31.10.2026): dieselbe Leiste wie oben auf jeder Seite von MoveEye
## (Web 639o #mwbar, Pi-Fenster App._mwbar): «Einfach | Experte» · «Symbole farbig | schlicht» · «Beim Start: Nur Gruppen» ·
## «Alle zuklappen · Nur Gruppen · Alle aufklappen». Ein Baustein für jedes Menü-Fenster des Simulators: build(main) mit
## einem Objekt, das die drei Wechsel kennt (je EINE Funktion, Review P0):
##   set_simple(on: bool)        ui_simple   (true = einfach)
##   set_icons(v: String)        ui_icons    ("color" | "plain")
##   set_start_groups(on: bool)  start_groups
##   _fold_all(how, true)        how = "close" | "groups" | "open"
## HFlowContainer: wird das Fenster schmal, bricht die Leiste um (kein seitliches Scrollen).

const UI = preload("res://scripts/ui_style.gd")
const T := preload("res://scripts/i18n.gd")

var host: Object
var simple_seg: HBoxContainer
var icons_seg: HBoxContainer
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
	icons_seg = UI.segment(T.t("Symbole farbig"), T.t("schlicht"), str(h.get("ui_icons")) == "plain",
		func(plain): h.set_icons("plain" if plain else "color"), true)
	icons_seg.custom_minimum_size = Vector2(230, 0)
	icons_seg.tooltip_text = T.t("Symbole: grüner Punkt oder grünes Symbol = eingeschaltet")
	add_child(icons_seg)
	sg_cb = CheckButton.new()
	sg_cb.text = T.t("Beim Start: Nur Gruppen")
	sg_cb.tooltip_text = T.t("Bei jedem Start zeigen die Einstellungen nur die Gruppen. Aus: Die Menüs sind auf- und zugeklappt, wie du sie verlassen hast.")
	sg_cb.add_theme_font_size_override("font_size", 13)
	sg_cb.focus_mode = Control.FOCUS_NONE
	sg_cb.button_pressed = bool(h.get("start_groups"))
	sg_cb.toggled.connect(func(on): h.set_start_groups(on))
	add_child(sg_cb)
	var fb := HBoxContainer.new()
	fb.add_theme_constant_override("separation", 6)
	for k in ["close", "groups", "open"]:
		var tip: String = {"close": T.t("Alle zuklappen"), "groups": T.t("Nur Gruppen"), "open": T.t("Alle aufklappen")}[k]
		var b := UI.icon_button(k, tip if fold else T.t("Auf dieser Seite gibt es nichts zum Klappen"))
		b.custom_minimum_size = Vector2(34, 32)
		b.disabled = not fold
		if fold:
			b.pressed.connect(func(): h._fold_all(k, true))
		fb.add_child(b)
		fold_btns[k] = b
	add_child(fb)


func paint(simple: bool, icons: String, start_groups: bool) -> void:
	"""show the current values (after a change from outside, e.g. the page of MoveEye)"""
	if simple_seg != null and simple_seg.has_meta("paint"):
		simple_seg.get_meta("paint").call(not simple)
	if icons_seg != null and icons_seg.has_meta("paint"):
		icons_seg.get_meta("paint").call(icons == "plain")
	if sg_cb != null and sg_cb.button_pressed != start_groups:
		sg_cb.set_pressed_no_signal(start_groups)
