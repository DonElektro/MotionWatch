extends Node
## Status-LED und Tasten des Geräts (Entscheide Daniel 30.10.2026 21:55, MoveEye Teil 163a / 599c):
##   * die Farb-LED oben auf dem Kopf (Diffusor in der Form von Blinkis Auge: oranger Ring, leuchtende Kuppel) zeigt, was
##     MoveEye schickt (state «led»: rgb, br, layer, hb) - Zustand, Alarm (blinkt rot), Störung (violett), Blinki-Zwinkern
##   * das kleine Fenster «Gerät»: die LED als Punkt, die Zeile von MoveEye («LED: Wachsam (orange)») und die zwei Tasten
##     «Schutz» (kurz Wachsam <-> Aus, lang 1,5 s Voll) und «Alarm quittieren». Die Tasten gehen wie ein GPIO an MoveEye:
##     world_reply «buttons» = {"protect"|"ack": {"down", "held_ms", "seq", "last_ms"}} - entprellt und kurz / lang
##     unterscheidet MoveEye selbst (wie am echten Gerät).
## Feldliste: schnittstelle.json («led» im Zustand, «buttons» in der Antwort).

var main
var FILE := "user://statusled.json"
var show_panel := true
var tile: PanelContainer
var _dot: Panel
var _dot_box: StyleBoxFlat
var _txt: Label
var _btn := {}
var btn := {"protect": {"down": false, "t0": 0.0, "seq": 0, "last_ms": 0}, "ack": {"down": false, "t0": 0.0, "seq": 0, "last_ms": 0}}
var _rig: Node3D
var _dome: MeshInstance3D
var _dome_mat: StandardMaterial3D
var _glow: OmniLight3D
var _hb_seen := -1
var _hb_t := -10.0
var _rules_btn: Button                                     # 3D-4.22: «Regeln der Tasten → in MoveEye» (only while MoveEye is connected)


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		show_panel = bool(d.get("panel", true))


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"panel": show_panel}))
		f.close()


func add_controls() -> void:
	main.add_control("toggle", "statusled_panel", "Fenster «Gerät»: Status-LED und die Tasten «Schutz» / «Alarm quittieren» zeigen (gehen wie echte Tasten an MoveEye)",
			func(): return show_panel, func(v): show_panel = bool(v); save(), "Licht & Ton", {"sub": "Status-LED & Tasten"})
	# für Tests (Prüfstand / Selbsttest): «protect:300» = Taste 300 ms gedrückt, «click:ack:200» = Mausklick auf den Knopf im Fenster
	main.add_control("select", "statusled_press", "Taste drücken (Test)", func(): return "", func(v): test_press(str(v)), "Licht & Ton",
			{"sub": "Status-LED & Tasten", "hide": true, "expert": true, "options": [["protect:200", "Schutz kurz"], ["protect:1800", "Schutz lang"], ["ack:200", "Alarm quittieren"]]})


# ---- 3D-4.22: the rules of the buttons are settings of MoveEye (163a / 599c) - a hint in the card, the link only when connected
func add_info(parent: Control, UI) -> void:
	parent.add_child(UI.small("Regeln der Tasten (was sie dürfen, Push bei Ausschalten / Sirene-Stopp) stellt man in MoveEye ein: Einstellungen → Licht & Ton → Status-LED & Tasten."))
	_rules_btn = Button.new()
	_rules_btn.text = "Regeln der Tasten → in MoveEye"
	_rules_btn.tooltip_text = "Öffnet in MoveEye die Einstellungen «Status-LED & Tasten» im Browser"
	_rules_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_rules_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_rules_btn.pressed.connect(open_rules)
	_rules_btn.visible = mw_connected()
	parent.add_child(_rules_btn)


func mw_connected() -> bool:
	return main != null and main.mw_addr != "" and main.now() - main.mw_t < 10.0


func open_rules() -> void:
	if not mw_connected():
		return
	OS.shell_open("%s://%s:%d/settings?open=sec%%3AStatus%%20LED" % [str(main.mw.get("mw_scheme", "http")), main.mw_addr, int(main.mw.get("mw_port", 5000))])


# ---- what MoveEye gets (world_reply «buttons») ---------------------------------------------------------------------------
func reply() -> Dictionary:
	var out := {}
	var t := Time.get_ticks_msec()
	for k in btn.keys():
		var b: Dictionary = btn[k]
		out[k] = {"down": bool(b["down"]), "held_ms": int(t - int(b["t0"])) if b["down"] else 0, "seq": int(b["seq"]), "last_ms": int(b["last_ms"])}
	return out


func press(k: String, down: bool) -> void:
	if not btn.has(k):
		return
	var b: Dictionary = btn[k]
	var t := Time.get_ticks_msec()
	if down and not b["down"]:
		b["down"] = true
		b["t0"] = t
	elif not down and b["down"]:
		b["down"] = false
		b["last_ms"] = t - int(b["t0"])
		b["seq"] = int(b["seq"]) + 1


func test_press(v: String) -> void:
	"""«protect:300» = the button held 300 ms; «click:ack:200» = through the button of the window (its signals, like a click)"""
	var p := v.split(":")
	var via := p.size() >= 3 and p[0] == "click"
	if via:
		p = p.slice(1)
	if p.size() < 2 or not btn.has(p[0]):
		return
	var k: String = p[0]
	if via and _btn.has(k):
		(_btn[k] as Button).button_down.emit()
	else:
		press(k, true)
	_pending.append([Time.get_ticks_msec() + maxi(20, int(p[1])), k, via])


var _pending: Array = []                                   # [release at (ms), button, through the window]


func _release_due() -> void:
	"""ends the test presses by the clock (timers of a slow simulator fire too early / late)"""
	if _pending.is_empty():
		return
	var t := Time.get_ticks_msec()
	var keep := []
	for q in _pending:
		if t >= int(q[0]):
			if bool(q[2]) and _btn.has(str(q[1])):
				(_btn[str(q[1])] as Button).button_up.emit()
			else:
				press(str(q[1]), false)
		else:
			keep.append(q)
	_pending = keep


# ---- the LED on the head --------------------------------------------------------------------------------------------------
func _build_led() -> void:
	if main.head_pitch == null or _rig != null:
		return
	_rig = Node3D.new()
	_rig.position = Vector3(0, 0.092, -0.02)             # on top of the head box (0.25 × 0.18 × 0.2), a little to the front
	main.head_pitch.add_child(_rig)
	var ring := MeshInstance3D.new()                     # Blinkis Auge: der orange Rand ...
	var tm := TorusMesh.new()
	tm.inner_radius = 0.026
	tm.outer_radius = 0.036
	tm.rings = 24
	tm.ring_segments = 8
	ring.mesh = tm
	ring.scale = Vector3(1, 0.5, 1)
	ring.material_override = main.mat(Color("#e8590c"))
	_rig.add_child(ring)
	_dome = MeshInstance3D.new()                         # ... und die weisse Kuppel, die in der Farbe der LED leuchtet
	var sm := SphereMesh.new()
	sm.radius = 0.027
	sm.height = 0.032
	sm.radial_segments = 20
	sm.rings = 10
	_dome.mesh = sm
	_dome.position = Vector3(0, 0.004, 0)
	_dome_mat = StandardMaterial3D.new()
	_dome_mat.albedo_color = Color(0.85, 0.86, 0.88)
	_dome_mat.roughness = 0.35
	_dome_mat.emission_enabled = true
	_dome_mat.emission = Color.BLACK
	_dome.material_override = _dome_mat
	_rig.add_child(_dome)
	_glow = OmniLight3D.new()
	_glow.omni_range = 0.6
	_glow.light_energy = 0.0
	_glow.shadow_enabled = false
	_glow.position = Vector3(0, 0.03, 0)
	_rig.add_child(_glow)


func led_state() -> Dictionary:
	"""what MoveEye sent (empty while not connected)"""
	if main.now() - main.mw_t > 3.0:
		return {}
	var l = main.mw.get("led", null)
	return l if typeof(l) == TYPE_DICTIONARY else {}


func _process(_dt: float) -> void:
	_release_due()
	_build_led()
	var l := led_state()
	var c := Color.BLACK
	var br := 0.0
	if not l.is_empty() and bool(l.get("on", true)):
		c = Color.html(str(l.get("rgb", "#000000")))
		br = clampf(float(l.get("br", 0.0)), 0.0, 1.0)
		var hb := int(l.get("hb", 0))
		if _hb_seen >= 0 and hb != _hb_seen:
			_hb_t = main.now()                            # Blinki-Zwinkern: hier selbst abspielen (genau, auch bei langsamen Paketen)
		_hb_seen = hb
		var h: float = main.now() - _hb_t
		if h >= 0.0 and h < 0.6 and (h < 0.15 or (h >= 0.3 and h < 0.45)):
			br = 0.0
	if _dome_mat != null:
		var lit := br > 0.001 and c != Color.BLACK
		_dome_mat.emission = c if lit else Color.BLACK
		_dome_mat.emission_energy_multiplier = 0.6 + 3.5 * br if lit else 0.0
		_dome_mat.albedo_color = c.lerp(Color(0.85, 0.86, 0.88), 0.35) if lit else Color(0.7, 0.71, 0.73)
		_glow.light_color = c
		_glow.light_energy = 0.35 * br if lit else 0.0
	if _rules_btn != null:
		_rules_btn.visible = mw_connected()
	if tile == null:
		return
	tile.visible = show_panel and main.ui_root != null
	if not tile.visible:
		return
	_dot_box.bg_color = c.lerp(Color(0.16, 0.19, 0.23), clampf(0.55 - br, 0.0, 0.5)) if br > 0.001 else Color(0.16, 0.19, 0.23)   # nachts gedimmt = dunkler
	_dot_box.shadow_color = Color(c.r, c.g, c.b, 0.7) if br > 0.001 else Color(0, 0, 0, 0)
	_dot_box.shadow_size = int(4 + 6 * br) if br > 0.001 else 0
	if l.is_empty():
		_txt.text = "LED: wartet auf MoveEye"
	else:
		_txt.text = str(l.get("text", "LED"))
	for k in _btn.keys():
		(_btn[k] as Button).disabled = l.is_empty()
	var vp: Vector2 = main.get_viewport().get_visible_rect().size
	tile.reset_size()
	tile.position = Vector2(vp.x - tile.size.x - 14.0, 64.0)          # oben rechts unter dem Zurück-Knopf (unten sind die Kameras)


# ---- the window «Gerät» ----------------------------------------------------------------------------------------------------
func make_tile(layer: Node) -> void:
	tile = PanelContainer.new()
	tile.mouse_filter = Control.MOUSE_FILTER_STOP
	tile.tooltip_text = "Gerät: Status-LED oben auf dem Kopf und die zwei Tasten (wie am echten MoveEye)"
	tile.add_theme_stylebox_override("panel", main.UI.box(main.UI.PANEL, main.UI.LINE, 10, 8, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	tile.add_child(v)
	var title := Label.new()
	title.text = "GERÄT"
	title.add_theme_font_size_override("font_size", 11)
	title.add_theme_color_override("font_color", main.UI.MUT)
	v.add_child(title)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	v.add_child(row)
	_dot = Panel.new()
	_dot.custom_minimum_size = Vector2(18, 18)
	_dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_dot_box = StyleBoxFlat.new()
	_dot_box.set_corner_radius_all(9)
	_dot_box.bg_color = Color(0.16, 0.19, 0.23)
	_dot_box.border_color = Color("#e8590c")
	_dot_box.set_border_width_all(2)
	_dot_box.anti_aliasing = true
	_dot.add_theme_stylebox_override("panel", _dot_box)
	_dot.tooltip_text = "Status-LED oben auf dem Kopf"
	row.add_child(_dot)
	_txt = Label.new()
	_txt.add_theme_font_size_override("font_size", 13)
	_txt.add_theme_color_override("font_color", main.UI.TXT)
	_txt.custom_minimum_size = Vector2(210, 0)
	_txt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	row.add_child(_txt)
	var bb := HBoxContainer.new()
	bb.add_theme_constant_override("separation", 6)
	v.add_child(bb)
	for k in [["protect", "Schutz", "kurz: Wachsam ↔ Aus · lang (1,5 s): Voll"], ["ack", "Alarm quittieren", "stoppt Sirene und rotes Blinken"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.focus_mode = Control.FOCUS_NONE
		var key: String = k[0]
		b.button_down.connect(func(): press(key, true))
		b.button_up.connect(func(): press(key, false))
		bb.add_child(b)
		_btn[key] = b
	var hint := Label.new()
	hint.text = "Schutz kurz: Wachsam ↔ Aus · lang: Voll"
	hint.add_theme_font_size_override("font_size", 10)
	hint.add_theme_color_override("font_color", main.UI.MUT)
	v.add_child(hint)
	tile.visible = false
	layer.add_child(tile)
