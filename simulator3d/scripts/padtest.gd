extends Control
## 3D-3.97: «Controller testen» - both sticks as circles: grey dot = what the stick sends, ring = rest position + dead zone,
## green dot = what the simulator uses after the drift is taken off. A drifting stick shows a grey dot off the middle while
## the green dot stays in the middle. Click / any button to close it.

var main


func _ready() -> void:
	set_anchors_preset(Control.PRESET_CENTER)
	custom_minimum_size = Vector2(380, 230)
	size = custom_minimum_size
	position = Vector2(-190, -115)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed:
		visible = false


func _process(_dt: float) -> void:
	if visible:
		queue_redraw()


func _draw() -> void:
	var ex = main.explore
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.07, 0.09, 0.92))
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.3, 0.6, 1.0, 0.9), false, 1.5)
	var f := get_theme_default_font()
	draw_string(f, Vector2(12, 22), "Controller-Test (Klick = schliessen)", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(0.9, 0.93, 0.97))
	for st in range(2):
		var c := Vector2(100 + st * 180, 120)
		var R := 70.0
		draw_arc(c, R, 0, TAU, 48, Color(0.5, 0.55, 0.6), 1.5)
		var cen := Vector2(float(main.pad_center[st * 2]), float(main.pad_center[st * 2 + 1]))
		draw_arc(c + cen * R, float(main.pad_dead) * R, 0, TAU, 32, Color(1.0, 0.65, 0.2, 0.9), 1.5)
		var raw: Vector2 = ex.stick_raw(st)
		var cl: Vector2 = ex.stick(st)
		draw_circle(c + raw * R, 6.0, Color(0.6, 0.6, 0.65))
		draw_circle(c + cl * R, 5.0, Color(0.3, 0.95, 0.45))
		draw_string(f, c + Vector2(-60, R + 22), ("links" if st == 0 else "rechts") + "  roh %.2f / %.2f" % [raw.x, raw.y], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.75, 0.8, 0.85))
	draw_string(f, Vector2(12, size.y - 10), "grau = Stick roh · grün = nach Drift-Korrektur · Ring = Totzone %d %%" % int(float(main.pad_dead) * 100), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.75, 0.8, 0.85))
