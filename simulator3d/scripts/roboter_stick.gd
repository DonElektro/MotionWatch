extends Control
## Virtueller Stick fürs Roboter-Labor (Besitzer 28.11.2026 14:47): eine Komponente, mehrfach nutzbar (untere Leiste, Seite
## «Bewegen»), Maus und Touch (ein Finger = Maus). Stufenlos, loslassen = zurück auf 0 (Signal «losgelassen»).
##   achsen «xy»: runder Stick (x + = rechts, y + = vor / hoch) · achsen «x»: waagrechter Dreh-Regler (x + = rechts drehen)
##   anzeige: Callable -> Vector2, was der Knopf zeigt, solange niemand zieht (z. B. der Fahrbefehl aus Tasten / Controller)
## Dazu x_symbol(): ein gezeichnetes «Schliessen»-Kreuz - die Schrift des Simulators hat ✕ / ⟲ / ⟳ nicht überall (Web).

signal bewegt(v: Vector2)
signal losgelassen

const UI = preload("res://scripts/ui_style.gd")
const KNOPF := 9.0

var achsen := "xy"
var wert := Vector2.ZERO
var anzeige := Callable()
var _zieh := false


static func neu(achsen_: String, groesse: Vector2, tip := "") -> Control:
	var s = load("res://scripts/roboter_stick.gd").new()
	s.achsen = achsen_
	s.custom_minimum_size = groesse
	s.tooltip_text = tip
	s.mouse_filter = Control.MOUSE_FILTER_STOP
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return s


func zieht() -> bool:
	return _zieh


func ziehen(v: Vector2) -> void:
	"""set the stick (also for tests): −1 … 1, «x» uses only v.x"""
	if achsen == "x":
		v = Vector2(clampf(v.x, -1.0, 1.0), 0.0)
	elif v.length() > 1.0:
		v = v.normalized()
	_zieh = true
	wert = v
	bewegt.emit(wert)
	queue_redraw()


func loslassen() -> void:
	_zieh = false
	wert = Vector2.ZERO
	bewegt.emit(wert)
	losgelassen.emit()
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_EXIT and _zieh and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		loslassen()


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and (ev as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		if (ev as InputEventMouseButton).pressed:
			ziehen(_aus_punkt((ev as InputEventMouseButton).position))
		else:
			loslassen()
		accept_event()
	elif ev is InputEventMouseMotion and _zieh:
		ziehen(_aus_punkt((ev as InputEventMouseMotion).position))
		accept_event()


func _aus_punkt(p: Vector2) -> Vector2:
	var mid := size * 0.5
	if achsen == "x":
		return Vector2((p.x - mid.x) / maxf(1.0, mid.x - KNOPF - 4.0), 0.0)
	var rad := minf(size.x, size.y) * 0.5 - KNOPF
	var v := (p - mid) / maxf(rad, 1.0)
	return Vector2(v.x, -v.y)


func _zeige() -> Vector2:
	if _zieh or not anzeige.is_valid():
		return wert
	var v: Vector2 = anzeige.call()
	return v.limit_length(1.0) if achsen == "xy" else Vector2(clampf(v.x, -1.0, 1.0), 0.0)


func _draw() -> void:
	var mid := size * 0.5
	var v := _zeige()
	var aktiv := _zieh or v.length() > 0.02
	if achsen == "x":
		var r := Rect2(Vector2(2, mid.y - 13.0), Vector2(size.x - 4.0, 26.0))
		draw_style_box(UI.box(UI.FIELD, UI.LINE, 13, 0, 1), r)
		draw_line(Vector2(mid.x, r.position.y + 4.0), Vector2(mid.x, r.end.y - 4.0), UI.LINE, 1.0)
		for sd in [-1.0, 1.0]:                             # curved arrows: turn left / right (drawn, no font)
			var c := Vector2(mid.x + sd * (mid.x - 20.0), mid.y)
			var a0 := PI * 1.15 if sd < 0.0 else -PI * 0.15
			var a1 := PI * 1.85 if sd < 0.0 else PI * -0.85
			draw_arc(c, 6.0, a0, a1, 12, UI.MUT, 1.5, true)
			var tip := c + Vector2(cos(a1), sin(a1)) * 6.0
			var tg := Vector2(-sin(a1), cos(a1)) * (1.0 if a1 > a0 else -1.0)
			draw_line(tip, tip - tg * 4.0 + tg.orthogonal() * 3.0, UI.MUT, 1.5, true)
			draw_line(tip, tip - tg * 4.0 - tg.orthogonal() * 3.0, UI.MUT, 1.5, true)
		var kx := mid.x + v.x * (mid.x - KNOPF - 4.0)
		draw_circle(Vector2(kx, mid.y), KNOPF + 1.0, UI.ACC if aktiv else UI.BTN2)
		draw_arc(Vector2(kx, mid.y), KNOPF + 1.0, 0.0, TAU, 20, UI.TXT if _zieh else UI.LINE, 1.0, true)
		return
	var rad := minf(size.x, size.y) * 0.5 - 2.0
	draw_circle(mid, rad, UI.FIELD)
	draw_arc(mid, rad, 0.0, TAU, 48, UI.LINE, 1.5, true)
	draw_line(mid - Vector2(rad * 0.6, 0), mid + Vector2(rad * 0.6, 0), UI.LINE, 1.0)
	draw_line(mid - Vector2(0, rad * 0.6), mid + Vector2(0, rad * 0.6), UI.LINE, 1.0)
	var k := mid + Vector2(v.x, -v.y) * (rad - KNOPF)
	var kr := KNOPF * (1.0 if rad < 45.0 else 1.5)
	draw_circle(k, kr, UI.ACC if aktiv else UI.BTN2)
	draw_arc(k, kr, 0.0, TAU, 20, UI.TXT if _zieh else UI.LINE, 1.0, true)


static func x_symbol(b: Button, col: Color, groesse := 5.0) -> Button:
	"""draw a «close» cross on the button instead of the ✕ character"""
	b.text = ""
	var d := Control.new()
	d.set_anchors_preset(Control.PRESET_FULL_RECT)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(d)
	d.draw.connect(func():
		var c := d.size * 0.5
		d.draw_line(c + Vector2(-groesse, -groesse), c + Vector2(groesse, groesse), col, 1.8, true)
		d.draw_line(c + Vector2(groesse, -groesse), c + Vector2(-groesse, groesse), col, 1.8, true))
	if b.custom_minimum_size.x < 22.0:
		b.custom_minimum_size = Vector2(maxf(22.0, b.custom_minimum_size.x), maxf(20.0, b.custom_minimum_size.y))
	return b
