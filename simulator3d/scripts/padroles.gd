extends PanelContainer
## 3D-4.13 «Controller zuteilen» (padmap.gd): every controller presses A to join and chooses its role with ◀ ▶ - Wächter
## (the head: left stick, light, photo, shutter), Schleicher (the player in the game at the PC), Rover (right stick, view) or
## alles. Each gets a number and the colour of its role (the chips of padhud.gd). B = not with us, Start = done.
## Done with a Schleicher: the game at the PC starts for him (localplay.gd).

var pm
var _list: VBoxContainer
var _help: Label
var _sig := ""

const UI = preload("res://scripts/ui_style.gd")
const CHOICE := ["guard", "runner", "rover", "all"]


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.ACC, 16, 18, 2))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)
	v.add_child(UI.heading("Controller zuteilen"))
	var t := UI.small("Jeder Controller: A = mitmachen · ◀ ▶ = Rolle wählen · B = nicht dabei · Start = fertig", UI.TXT)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.custom_minimum_size.x = 520
	v.add_child(t)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	v.add_child(_list)
	_help = UI.small("", UI.MUT)
	_help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_help.custom_minimum_size.x = 520
	v.add_child(_help)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	v.add_child(row)
	var ok := Button.new()
	ok.text = "Fertig (Start)"
	UI.primary(ok)
	ok.pressed.connect(close)
	row.add_child(ok)
	var rs := Button.new()
	rs.text = "Alle zurücksetzen (jeder macht alles)"
	rs.pressed.connect(func(): pm.roles.clear(); _sig = "")
	row.add_child(rs)


func open() -> void:
	visible = true
	_sig = ""


func close() -> void:
	visible = false
	var lp = pm.main.localplay
	var runner := false
	for d in pm.roles:
		if str(pm.roles[d]["role"]) == "runner":
			runner = true
	if runner and lp != null and not lp.active:
		lp.start("runner")                                   # a sneaker: the game at the PC
	pm._say("Controller: %d zugeteilt" % pm.roles.size() if not pm.roles.is_empty() else "Controller: jeder macht alles")


func _process(_dt: float) -> void:
	if not visible:
		return
	var vs := get_viewport_rect().size
	reset_size()
	position = (vs - size) / 2.0
	for d in pm.devices():
		var ks: Array = pm.keys([d])
		if "a" in ks and not pm.roles.has(d):
			pm.set_role(d, "guard" if pm.roles.is_empty() else ("rover" if _count("rover") == 0 else "runner"))
			pm.rumble("catch", [d])
		elif ("right" in ks or "left" in ks) and pm.roles.has(d):
			var i := CHOICE.find(str(pm.roles[d]["role"]))
			pm.set_role(d, CHOICE[(i + (1 if "right" in ks else -1) + CHOICE.size()) % CHOICE.size()])
		elif "b" in ks and pm.roles.has(d):
			pm.set_role(d, "")
		elif "start" in ks or "start_long" in ks:
			close()
			return
	_paint()


func _count(r: String) -> int:
	var n := 0
	for d in pm.roles:
		if str(pm.roles[d]["role"]) == r:
			n += 1
	return n


func _paint() -> void:
	var sig := str(pm.devices()) + str(pm.roles)
	if sig == _sig:
		return
	_sig = sig
	for c in _list.get_children():
		c.queue_free()
	if pm.devices().is_empty():
		_list.add_child(UI.small("Kein Controller verbunden (USB oder Bluetooth; im Browser: MoveEye-Seite Simulator).", UI.TXT))
	for d in pm.devices():
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 10)
		var r: String = str(pm.roles[d]["role"]) if pm.roles.has(d) else ""
		var col: Color = pm.role_color(r) if r != "" else Color(0.5, 0.55, 0.6)
		var num := Label.new()
		num.text = str(pm.number(d)) if r != "" else "–"
		num.add_theme_font_size_override("font_size", 22)
		num.add_theme_color_override("font_color", col)
		num.custom_minimum_size.x = 30
		h.add_child(num)
		var nm := Label.new()
		nm.text = pm.dev_name(d)
		nm.custom_minimum_size.x = 250
		h.add_child(nm)
		var rl := Label.new()
		rl.text = ("◀ %s ▶" % pm.role_name(r)) if r != "" else "A drücken = mitmachen"
		rl.add_theme_color_override("font_color", col)
		h.add_child(rl)
		_list.add_child(h)
	var parts := PackedStringArray()
	for r in ["guard", "runner", "rover"]:
		var mode: String = {"guard": "sim", "runner": "runner", "rover": "sim"}[r]
		var only: Array = {"guard": ["head", "light", "ir", "photo", "follow", "shutter", "center"], "runner": [], "rover": ["drive", "orbit", "view", "zoom_in", "zoom_out", "swap"]}[r]
		var hl: String = pm.help_line(mode, only)
		parts.append("%s: %s" % [pm.role_name(r), hl if r != "runner" else "Spiel am PC – " + pm.help_line("runner", ["look", "walk", "run", "lamp", "crouch", "stone", "crawl"])])
	_help.text = "\n".join(parts)
