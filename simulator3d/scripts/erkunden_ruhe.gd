extends Node
## «Ruhiger Bildschirm» beim Frei erkunden (Fragebogen des Besitzers 22.11.2026, Frage 8): solange man als Figur erkundet, sind
## alle Fenster und Leisten weg, die man dafür nicht braucht (Menüs, Statusfelder, Kamerabilder, Entwickler-Anzeigen, die
## Handy-Leiste …). Es bleiben: die Steuerung der Figur (grüner Stick, Knöpfe am Rand mit der Haltung), der Knopf «Camp» und
## klein oben rechts «☰ Menü» - damit kommt alles zurück (nochmals = wieder ruhig). Beim Verlassen ist alles wie vorher.
## NICHTS wird entfernt: die Knoten werden nur unsichtbar gemacht und genau so wieder gezeigt, wie sie waren (auch was
## während des Erkundens erscheinen wollte, kommt danach). PC, Handy und iPad gleich. Ein Kind von explore_person.gd.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

var person
var main
var an := false                      # the screen is quiet now
var menu_zeigen := false             # «☰ Menü»: everything back for a moment (until tapped again or exploring ends)
var _weg := {}                       # instance id -> [WeakRef, visible before]
var _scan_t := -100.0
var _layer: CanvasLayer
var knopf: Button


func _ready() -> void:
	process_priority = 99                                             # after the others have shown their things
	_layer = CanvasLayer.new()
	_layer.layer = 9
	add_child(_layer)
	knopf = Button.new()
	knopf.name = "ruhe_menu"
	knopf.focus_mode = Control.FOCUS_NONE
	knopf.custom_minimum_size = Vector2(48, 44)
	knopf.add_theme_font_size_override("font_size", 15)
	knopf.pressed.connect(func(): set_menu(not menu_zeigen))
	knopf.visible = false
	_layer.add_child(knopf)


func _soll() -> bool:
	return person != null and person.ok() and bool(person.active) and person.ex != null and bool(person.ex.on)


func set_menu(v: bool) -> void:
	"""«☰ Menü»: v = true shows everything again (the menus work as always), false = quiet again"""
	menu_zeigen = v
	if v and an:
		aus()
		main.show_panel(true)
	elif not v and _soll():
		main.show_panel(false)
		ein()


func _erlaubt(n: Node) -> bool:
	"""what stays: the figure's own controls (explore with the figure, its children), the green stick, this button"""
	for a in [main.get("rover_pad"), _layer, person, person.get("camp")]:
		if a != null and is_instance_valid(a) and (a == n or (a as Node).is_ancestor_of(n)):
			return true
	var ex = main.get("explore")
	if ex != null and is_instance_valid(ex) and n == ex:
		return true
	return false


func _ist_bild(c: Control) -> bool:
	"""a full-screen picture effect (lens, fade, night) - not a panel: stays"""
	var s: Vector2 = c.get_viewport_rect().size
	return c.mouse_filter == Control.MOUSE_FILTER_IGNORE and c.size.x >= s.x * 0.9 and c.size.y >= s.y * 0.9 \
			and c.find_children("*", "BaseButton", true, false).is_empty()


func kandidaten() -> Array:
	"""the visible panels: the top Controls of every CanvasLayer and of main, windows - without the allowed ones"""
	var out := []
	var wurzeln := [main]
	var tree := get_tree()
	if tree != null and tree.root != null:
		for c in tree.root.get_children():
			if c != main:
				wurzeln.append(c)
	var stapel := []
	for w in wurzeln:
		stapel.append([w, 0])
	while not stapel.is_empty():
		var e: Array = stapel.pop_back()
		var n: Node = e[0]
		var tief: int = e[1]
		if _erlaubt(n) and n != main:
			continue
		if n is Window and n != tree.root:
			if (n as Window).visible:
				out.append(n)
			continue
		if n is Control and n != main:
			var c := n as Control
			if c.visible and not _ist_bild(c):
				out.append(c)
			continue                                                  # (its children go with it)
		if tief < 4:
			for k in n.get_children():
				stapel.append([k, tief + 1])
	# inside «Erkunden» itself: the long help text at the top and the invitation (the buttons of the figure stay)
	var ex = main.get("explore")
	if ex != null and is_instance_valid(ex):
		for nm in ["_info", "invite"]:
			var x = ex.get(nm)
			if x is Control and is_instance_valid(x) and (x as Control).visible:
				out.append(x)
	return out


func ein() -> void:
	an = true
	_verstecken()


func _verstecken() -> void:
	for c in kandidaten():
		var id: int = (c as Object).get_instance_id()
		if not _weg.has(id):
			_weg[id] = [weakref(c), true]
		c.visible = false
	for id in _weg:                                                   # wanted to show meanwhile: hidden again, shown afterwards
		var n = (_weg[id][0] as WeakRef).get_ref()
		if n != null and n.visible:
			_weg[id][1] = true
			n.visible = false


func aus() -> void:
	"""everything back exactly as it was"""
	for id in _weg:
		var n = (_weg[id][0] as WeakRef).get_ref()
		if n != null and is_instance_valid(n):
			n.visible = bool(_weg[id][1])
	_weg = {}
	an = false


func knopf_unten() -> float:
	"""where the «Camp» button may begin (below this one)"""
	return knopf.position.y + knopf.size.y if knopf.visible else 4.0


func _process(_dt: float) -> void:
	if person == null or main == null:
		return
	var s := _soll()
	knopf.visible = s and not person.ruhig()
	if not s:
		if an:
			aus()
		menu_zeigen = false
		return
	knopf.text = "☰ " + (T.t("Ruhig") if menu_zeigen else T.t("Menü"))
	knopf.tooltip_text = T.t("Alle Fenster und Menüs wieder zeigen / wieder ausblenden")
	var vs: Vector2 = knopf.get_viewport_rect().size
	knopf.size = Vector2.ZERO
	knopf.position = Vector2(vs.x - knopf.get_combined_minimum_size().x - 8.0, 8.0)
	if menu_zeigen:
		return
	if not an:
		ein()
	elif main.now() - _scan_t > 0.25:
		_scan_t = main.now()
		_verstecken()


func info() -> Dictionary:
	var namen := []
	for id in _weg:
		var n = (_weg[id][0] as WeakRef).get_ref()
		if n != null:
			namen.append(str(n.name))
	return {"an": an, "menu": menu_zeigen, "versteckt": namen.size(), "namen": namen, "knopf": knopf.visible}
