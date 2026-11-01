extends Node
## Schneller Zugang zum Entwickler-Fenster (Daniel 1.11.2026, Wahl 2 und 4; Gegenstück zu MoveEye Teil 639s):
##   * langer Druck (0,8 s) auf den Schriftzug bzw. den Titel «Simulator» oben im Bedienfeld öffnet das Entwickler-Fenster
##     (devtool.gd, sonst «Mehr → Entwickler»); bei ausgeblendetem Bedienfeld wirkt der Knopf «Bedienfeld zeigen» gleich.
##     Rückmeldung: das Logo pulsiert (grösser / heller), beim Auslösen kurz aufblitzen.
##   * ein gezeichneter Werkzeug-Knopf (UI.icon_button "tools", keine Emoji - die Schrift hat keine) oben rechts im Kopf.
##   * beides nur mit dem Entwickler-Bereich von MoveEye an (main.dev_area, von MoveEye gemeldet und gespeichert) und für
##     den Besitzer (devtool.is_owner: nicht im Kinder-Modus). Sonst ist der Knopf weg und der lange Druck tut nichts.
##   * ein normaler Klick auf Schriftzug / Titel tut weiterhin nichts.

const UI = preload("res://scripts/ui_style.gd")
const Dev = preload("res://scripts/devtool.gd")
const HOLD := 0.8                      # seconds
const MOVE := 12.0                     # px: moving further cancels

var main
var btn: Button = null
var _held: Control = null
var _t := 0.0
var _pos := Vector2.ZERO
var _chk := 0.0
var _flash: Control = null
var _ft := 0.0


static func allowed(m) -> bool:
	"""developer area of MoveEye on and the owner (never in the children's mode)"""
	return m != null and bool(m.get("dev_area")) and Dev.is_owner(m)


func setup(m, hdr: Control, targets: Array) -> void:
	main = m
	for c in targets:
		if c == null or not (c is Control):
			continue
		if not (c is BaseButton):
			c.mouse_filter = Control.MOUSE_FILTER_STOP   # the wordmark / logo ignore the mouse by themselves
		c.gui_input.connect(_on_input.bind(c))
	btn = UI.icon_button("tools", "Entwickler-Fenster öffnen")
	btn.visible = allowed(main)
	btn.pressed.connect(open_dev)
	if hdr != null:
		hdr.add_child(btn)


func _on_input(ev: InputEvent, c: Control) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			_stop()
			if allowed(main):
				_held = c
				_t = 0.0
				_pos = ev.global_position
		elif _held == c:
			_stop()
	elif ev is InputEventMouseMotion and _held == c and ev.global_position.distance_to(_pos) > MOVE:
		_stop()


func _look(c: Control, k: float) -> void:
	"""k 0 = normal, 1 = biggest / brightest"""
	if c == null or not is_instance_valid(c):
		return
	c.pivot_offset = c.size / 2.0
	c.scale = Vector2.ONE * (1.0 + 0.08 * k)
	c.modulate = Color(1.0 + 0.45 * k, 1.0 + 0.35 * k, 1.0 + 0.1 * k, 1.0)


func _stop() -> void:
	if _held != null:
		_look(_held, 0.0)
	_held = null
	_t = 0.0


func _process(dt: float) -> void:
	_chk -= dt
	if _chk <= 0.0:
		_chk = 1.0
		if btn != null:
			btn.visible = allowed(main)
	if _flash != null:
		_ft += dt
		_look(_flash, maxf(0.0, 1.0 - _ft / 0.35))
		if _ft >= 0.35:
			_look(_flash, 0.0)
			_flash = null
	if _held == null:
		return
	if not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):      # released outside the control
		_stop()
		return
	_t += dt
	if _t > 0.15:                                                # the logo pulses while it is held
		_look(_held, 0.5 - 0.5 * cos((_t - 0.15) * TAU / 0.4))
	if _t >= HOLD:
		var c := _held
		_stop()
		_flash = c
		_ft = 0.0
		_look(c, 1.0)
		open_dev()


func open_dev() -> void:
	if not allowed(main):
		return
	if main.mehr == null or main.mehr.get("dev") == null:
		return
	if main.mehr.has_method("close_window"):
		main.mehr.close_window()
	main.mehr.dev.open()


func info() -> Dictionary:
	return {"ok": true, "allowed": allowed(main), "button": btn != null and btn.visible}
