extends CanvasLayer
## Mini window: when the simulator window is minimized, it becomes a small box in the corner of the screen instead
## (on top of the other windows). A minimized window draws no pictures any more - then Motion Watch would only see
## «CONNECTING…». The box shows whether the simulator sends, how many pictures per second, and the connection.
## Click on the box: big again. Drag: move it. While it sends, the PC and the screen do not go to sleep.
## From 3D-2.3 also the CPU (measured by Motion Watch: the whole computer, Motion Watch, the simulator) and «Pause».

var main                                   # the main script
var mini := false
var saved := {}                            # window before the mini mode
var panel: PanelContainer
var dot: Label
var line1: Label
var line2: Label
var line3: Label
var line_cpu: Label
var t_upd := 0.0
var last_frames := 0
var last_t := 0.0
var fps := 0.0
var keep_on := -1
var drag_from := Vector2i.ZERO
var drag_win := Vector2i.ZERO
var dragging := false
var moved := false

const MINI_SIZE := Vector2i(360, 136)


func _ready() -> void:
	layer = 120
	panel = PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.09, 0.12, 1.0)
	sb.border_color = Color(0.25, 0.32, 0.42)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 14
	sb.content_margin_right = 12
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.mouse_default_cursor_shape = Control.CURSOR_MOVE
	panel.tooltip_text = "«Gross»: wieder normal · Ziehen: verschieben"
	panel.gui_input.connect(_on_input)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(v)
	var h := HBoxContainer.new()
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(h)
	dot = Label.new()
	dot.text = "●"
	dot.add_theme_font_size_override("font_size", 18)
	h.add_child(dot)
	line1 = Label.new()
	line1.add_theme_font_size_override("font_size", 16)
	h.add_child(line1)
	line2 = Label.new()
	line2.add_theme_font_size_override("font_size", 13)
	line2.add_theme_color_override("font_color", Color(0.75, 0.8, 0.86))
	line2.clip_text = true
	v.add_child(line2)
	line_cpu = Label.new()
	line_cpu.add_theme_font_size_override("font_size", 13)
	line_cpu.add_theme_color_override("font_color", Color(0.75, 0.8, 0.86))
	line_cpu.clip_text = true
	line_cpu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(line_cpu)
	var h2 := HBoxContainer.new()
	h2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(h2)
	line3 = Label.new()
	line3.add_theme_font_size_override("font_size", 12)
	line3.add_theme_color_override("font_color", Color(0.55, 0.6, 0.66))
	line3.text = "ziehen = verschieben"
	line3.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h2.add_child(line3)
	var big := Button.new()
	big.text = "▢ Gross"
	big.add_theme_font_size_override("font_size", 13)
	big.focus_mode = Control.FOCUS_NONE
	big.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS      # react at once (some systems lose the release here)
	big.pressed.connect(leave)
	h2.add_child(big)
	for c in [dot, line1, line2, line3]:
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.visible = false
	add_child(panel)
	if OS.get_environment("MWSIM_MINI_TEST") == "1":          # only for tests: mini mode by itself after 12 s
		get_tree().create_timer(12.0).timeout.connect(enter)


func _process(dt: float) -> void:
	var w := get_window()
	if not mini and w.mode == Window.MODE_MINIMIZED:
		enter()
	# while it sends: no sleep of the PC or the screen
	var want := 1 if main != null and main.stream_on else 0
	if want != keep_on:
		keep_on = want
		DisplayServer.screen_set_keep_on(want == 1 or bool(ProjectSettings.get_setting("display/window/energy_saving/keep_screen_on", true)))
	# pictures per second (both cameras together)
	var now := Time.get_ticks_msec() / 1000.0
	if now - last_t >= 1.0 and main != null:
		var n := int(main.frame_no[0]) + int(main.frame_no[1])
		if last_t > 0.0:
			fps = float(n - last_frames) / (now - last_t)
		last_frames = n
		last_t = now
	t_upd -= dt
	if mini and t_upd <= 0.0:
		t_upd = 0.5
		_paint()


func _paint() -> void:
	var sending: bool = main.stream_on
	var connected: bool = sending and main.now() - main.mw_t < 3.0
	dot.add_theme_color_override("font_color", Color(0.25, 0.85, 0.45) if connected else (Color(0.95, 0.7, 0.2) if sending else Color(0.55, 0.6, 0.66)))
	line1.text = ("Sendet an Motion Watch" if sending else "Senden aus") + ("  ·  %.0f Bilder/s" % fps if sending else "")
	if connected:
		line2.text = "verbunden mit %s" % str(main.mw.get("device", "Motion Watch"))
	elif sending:
		line2.text = "wartet auf Motion Watch …"
	else:
		line2.text = "Motion Watch sieht den Simulator nicht"
	if not main.sim_active:
		line2.text += "  ·  Pause (spart Strom)"
	line_cpu.text = cpu_text(main.cpu_info if connected else {})


static func cpu_text(c: Dictionary) -> String:
	"""CPU as Motion Watch measures it. Same computer (the simulator is found there): whole PC, Motion Watch, simulator.
	Motion Watch on the Pi: the Pi and Motion Watch on it (the CPU of this PC cannot be measured then)."""
	var pc = c.get("total", null)
	if pc == null:
		return "CPU: – (misst Motion Watch, sobald verbunden)"
	var mw = c.get("mw", null)
	var sim = c.get("sim", null)
	if sim != null:
		return "CPU PC %d %%  ·  Motion Watch %s  ·  Simulator %d %%" % [roundi(float(pc)), "–" if mw == null else "%d %%" % roundi(float(mw)), roundi(float(sim))]
	return "CPU Motion-Watch-Gerät %d %%  ·  davon Motion Watch %s" % [roundi(float(pc)), "–" if mw == null else "%d %%" % roundi(float(mw))]


func enter() -> void:
	"""minimized -> small box in the lower right corner, on top of the other windows"""
	var w := get_window()
	saved = {"size": w.size, "pos": w.position, "borderless": w.borderless, "top": w.always_on_top, "min": w.min_size}
	mini = true
	w.mode = Window.MODE_WINDOWED
	w.min_size = Vector2i(200, 80)
	w.borderless = true
	w.always_on_top = true
	w.size = MINI_SIZE
	var scr := DisplayServer.window_get_current_screen()
	var r := DisplayServer.screen_get_usable_rect(scr)
	w.position = r.position + r.size - MINI_SIZE - Vector2i(16, 16)
	panel.visible = true
	t_upd = 0.0
	_paint()


func leave() -> void:
	var w := get_window()
	mini = false
	panel.visible = false
	w.always_on_top = bool(saved.get("top", false))
	w.borderless = bool(saved.get("borderless", false))
	w.min_size = saved.get("min", Vector2i.ZERO)
	w.size = saved.get("size", Vector2i(1440, 860))
	w.position = saved.get("pos", Vector2i(60, 60))
	w.grab_focus()


func _on_input(ev: InputEvent) -> void:
	if not mini:
		return
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			dragging = true
			moved = false
			drag_from = DisplayServer.mouse_get_position()
			drag_win = get_window().position
		else:
			dragging = false
	elif ev is InputEventMouseMotion and dragging:
		var d := DisplayServer.mouse_get_position() - drag_from
		if d.length() > 4:
			moved = true
		if moved:
			get_window().position = drag_win + d
