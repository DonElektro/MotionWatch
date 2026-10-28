extends Control
## Driving the mover in the simulator itself (from 3D-3.15): a green stick at the bottom right (drag with the mouse:
## up = forward, down = back, sideways = turn on the spot), or the arrow keys. «Hinterher» = the view follows the mover.
## Shown only when «Mover simulieren» is on. Overrides Motion Watch while it is used.

var main
var dragging := false
var knob := Vector2.ZERO          # -1 … 1 (x = turn right, y = back)
var chase := false
var chase_btn: Button
const R := 58.0
const SZ := Vector2(150, 186)


func _ready() -> void:
	custom_minimum_size = SZ
	size = SZ
	set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	offset_left = -SZ.x - 18
	offset_top = -SZ.y - 70
	offset_right = -18
	offset_bottom = -70
	mouse_filter = Control.MOUSE_FILTER_STOP
	tooltip_text = "Mover fahren: Kugel ziehen (hoch = vorwärts, runter = rückwärts, seitlich = an Ort drehen) oder Pfeiltasten"
	chase_btn = Button.new()
	chase_btn.text = "Hinterher"
	chase_btn.toggle_mode = true
	chase_btn.tooltip_text = "Die Ansicht fährt hinter dem Mover her"
	chase_btn.position = Vector2(20, SZ.y - 36)
	chase_btn.size = Vector2(SZ.x - 40, 32)
	chase_btn.toggled.connect(func(on): chase = on)
	add_child(chase_btn)


func center() -> Vector2:
	return Vector2(SZ.x / 2.0, 8.0 + R + 6.0)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		dragging = ev.pressed and ev.position.distance_to(center()) < R + 14.0
		if dragging:
			_set_knob(ev.position)
		else:
			knob = Vector2.ZERO
		accept_event()
		queue_redraw()
	elif ev is InputEventMouseMotion and dragging:
		_set_knob(ev.position)
		accept_event()


func _set_knob(p: Vector2) -> void:
	var d := (p - center()) / R
	if d.length() > 1.0:
		d = d.normalized()
	knob = d
	queue_redraw()


func command() -> Vector2:
	"""(forward, turn right) of the stick or the arrow keys; ZERO when nobody drives here"""
	var k := Vector2.ZERO
	var g = main.game
	if g != null and g.round_state == "play" and g.seek_drive != Vector2.ZERO:
		return g.seek_drive.limit_length(1.0)               # 3D-3.78: the seeker of «Verstecken» drives
	if main.localplay != null and main.localplay.active:
		return Vector2.ZERO                                  # 3D-3.77: the keys belong to the player at the PC
	if not main.karte.visible:
		if Input.is_key_pressed(KEY_UP):
			k.x += 1.0
		if Input.is_key_pressed(KEY_DOWN):
			k.x -= 1.0
		if Input.is_key_pressed(KEY_RIGHT):
			k.y += 1.0
		if Input.is_key_pressed(KEY_LEFT):
			k.y -= 1.0
	if main.explore != null and main.explore.on:          # 3D-3.55: exploring - also W A S D and the game controller
		k += main.explore.command()
	if dragging:
		k = Vector2(-knob.y, knob.x)
	if k == Vector2.ZERO and main.patrol != null and main.patrol.active:   # 3D-3.61: the patrol drives (a hand on the stick wins)
		k = main.patrol.command()
	return k.limit_length(1.0)


func _process(dt: float) -> void:
	visible = main.mover_on
	var clean: bool = main.now() - main.view_clean_t < 3.0     # 3D-3.67: the browser shows full screen: not drawn, but still drives
	modulate.a = 0.0 if clean else 1.0
	mouse_filter = Control.MOUSE_FILTER_IGNORE if clean else Control.MOUSE_FILTER_STOP
	if not visible:
		dragging = false
		main.pad_on = false
		return
	# 3D-3.32: next to the control panel when it is shown, at the right edge when it is hidden (it covered the stick)
	var right := 18.0
	if main.ui_root != null and main.ui_root.visible:
		right = main.ui_root.size.x + 14.0
	if not is_equal_approx(offset_right, -right):
		offset_right = -right
		offset_left = -right - SZ.x
	if dragging and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):   # let go outside (the release went elsewhere)
		dragging = false
		knob = Vector2.ZERO
		queue_redraw()
	var c := command()
	main.pad_on = c != Vector2.ZERO or dragging
	if c != Vector2.ZERO or dragging:
		main.pad_drive = c
		main.pad_t = main.now()
		if not dragging:
			knob = knob.lerp(Vector2(c.y, -c.x).limit_length(1.0), clampf(dt * 12.0, 0.0, 1.0))
			queue_redraw()
	elif knob != Vector2.ZERO and not dragging:
		knob = Vector2.ZERO
		queue_redraw()
	if chase and main.view_mode == 0 and not (main.explore != null and main.explore.on):
		var rig: Node3D = main.rig
		var fwd := Vector3(-sin(rig.rotation.y), 0, -cos(rig.rotation.y))
		var tp := rig.global_position + Vector3(0, 0.8, 0)
		var want := tp - fwd * 7.0 + Vector3(0, 3.2, 0)
		want.y = max(want.y, main.ground_y(want.x, want.z) + 1.5)
		main.view_cam.global_position = main.view_cam.global_position.lerp(want, clampf(dt * 3.0, 0.0, 1.0))
		main.view_cam.look_at(tp + fwd * 3.0, Vector3.UP)


func _draw() -> void:
	var c := center()
	draw_rect(Rect2(Vector2.ZERO, SZ), Color(0.07, 0.09, 0.11, 0.55))
	draw_circle(c, R + 8.0, Color(0.1, 0.14, 0.12, 0.85))
	draw_arc(c, R + 8.0, 0, TAU, 48, Color(0.3, 0.6, 0.35, 0.9), 2.0)
	for sx in [-1.0, 1.0]:                                     # the two tracks
		draw_rect(Rect2(c + Vector2(sx * (R - 4.0) - 5.0, -R * 0.6), Vector2(10, R * 1.2)), Color(0.25, 0.28, 0.3, 0.9))
	draw_string(ThemeDB.fallback_font, c + Vector2(-5, -R + 12), "▲", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.6))
	draw_string(ThemeDB.fallback_font, c + Vector2(-5, R - 2), "▼", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.6))
	draw_string(ThemeDB.fallback_font, c + Vector2(-R + 14, 5), "⟲", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 1, 1, 0.6))
	draw_string(ThemeDB.fallback_font, c + Vector2(R - 26, 5), "⟳", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 1, 1, 0.6))
	var kp := c + knob * R
	draw_circle(kp, 25.0, Color(0.15, 0.5, 0.22))
	draw_circle(kp - Vector2(5, 6), 18.0, Color(0.25, 0.72, 0.35))
	draw_string(ThemeDB.fallback_font, Vector2(8, 14), "Mover fahren", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.9))
