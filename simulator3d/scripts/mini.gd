extends CanvasLayer
## Mini window: when the simulator window is minimized, it becomes a small box in the corner of the screen instead
## (on top of the other windows). A minimized window draws no pictures any more - then MoveEye would only see
## «CONNECTING…». The box shows whether the simulator sends, how many pictures per second, and the connection.
## Click on the box: big again. Drag: move it. While it sends, the PC and the screen do not go to sleep.
## From 3D-2.3 also the CPU (measured by MoveEye: the whole computer, MoveEye, the simulator) and «Pause».
## From 3D-3.11 also the CPU of this PC and of the simulator (measured here: Windows with a small PowerShell loop while the box
## is shown, Linux from /proc), and «▁» folds the box into a small icon (click on it: the box again).

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

const MINI_SIZE := Vector2i(330, 84)                # 3D-3.77: compact
const ICON_SIZE := Vector2i(64, 64)
var tiny := false                          # folded into the small icon
var icon_box: PanelContainer
var icon_dot: Label
var line_own: Label
var own := {"pc": -1.0, "sim": -1.0}       # CPU of this PC / of the simulator (%), -1 = not known
var cpu_pipe := {}
var cpu_thread: Thread
var cpu_run := false
var _lin_prev := []


func _ready() -> void:
	"""3D-3.77: compact - logo, version, state at the top; pictures, CPU and MoveEye in one line; a note only when needed"""
	layer = 120
	panel = PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.09, 0.12, 1.0)
	sb.border_color = Color(0.25, 0.32, 0.42)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 10
	sb.content_margin_right = 6
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.mouse_default_cursor_shape = Control.CURSOR_MOVE
	panel.tooltip_text = "Ziehen: verschieben · ▢: wieder gross · ▁: nur ein Symbol"
	panel.gui_input.connect(_on_input)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(v)
	var h := HBoxContainer.new()                     # logo · name and version · state · buttons
	h.add_theme_constant_override("separation", 6)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(h)
	var logo: Control = load("res://scripts/mw_logo.gd").new()
	logo.custom_minimum_size = Vector2(22, 22)
	h.add_child(logo)
	line1 = Label.new()
	line1.add_theme_font_size_override("font_size", 14)
	line1.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	line1.clip_text = true
	h.add_child(line1)
	dot = Label.new()
	dot.text = "●"
	dot.add_theme_font_size_override("font_size", 13)
	h.add_child(dot)
	line3 = Label.new()                               # the state in a word
	line3.add_theme_font_size_override("font_size", 12)
	h.add_child(line3)
	var fold := Button.new()
	fold.text = "▁"
	fold.flat = true
	fold.tooltip_text = "Einklappen: nur noch ein kleines Symbol"
	fold.add_theme_font_size_override("font_size", 12)
	fold.custom_minimum_size = Vector2(24, 22)
	fold.focus_mode = Control.FOCUS_NONE
	fold.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	fold.pressed.connect(func(): set_tiny(true))
	h.add_child(fold)
	var big := Button.new()
	big.text = "▢"
	big.flat = true
	big.tooltip_text = "Wieder gross"
	big.add_theme_font_size_override("font_size", 13)
	big.custom_minimum_size = Vector2(24, 22)
	big.focus_mode = Control.FOCUS_NONE
	big.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS      # react at once (some systems lose the release here)
	big.pressed.connect(leave)
	h.add_child(big)
	line2 = Label.new()                               # pictures/s · CPU of this PC · simulator
	line2.add_theme_font_size_override("font_size", 12)
	line2.add_theme_color_override("font_color", Color(0.82, 0.86, 0.9))
	line2.clip_text = true
	v.add_child(line2)
	line_cpu = Label.new()                            # MoveEye: device, version, its CPU
	line_cpu.add_theme_font_size_override("font_size", 12)
	line_cpu.add_theme_color_override("font_color", Color(0.65, 0.7, 0.77))
	line_cpu.clip_text = true
	line_cpu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(line_cpu)
	line_own = Label.new()                            # a note only when something needs attention
	line_own.add_theme_font_size_override("font_size", 11)
	line_own.add_theme_color_override("font_color", Color(0.95, 0.7, 0.3))
	line_own.clip_text = true
	line_own.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(line_own)
	for c in [dot, line1, line2, line3]:
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.visible = false
	add_child(panel)
	# the folded icon: the coloured «3D» - click = the box again, drag = move
	icon_box = PanelContainer.new()
	icon_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	var ib := StyleBoxFlat.new()
	ib.bg_color = Color(0.07, 0.09, 0.12, 1.0)
	ib.border_color = Color(0.25, 0.32, 0.42)
	ib.set_border_width_all(1)
	ib.set_corner_radius_all(14)
	icon_box.add_theme_stylebox_override("panel", ib)
	icon_box.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	icon_box.tooltip_text = "Anklicken: Kästchen wieder gross · Ziehen: verschieben"
	icon_box.gui_input.connect(_on_input)
	var iv := VBoxContainer.new()
	iv.alignment = BoxContainer.ALIGNMENT_CENTER
	iv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon_box.add_child(iv)
	var il: Control = load("res://scripts/mw_logo.gd").new()   # 3D-3.86: the MoveEye eye instead of «3D»
	il.custom_minimum_size = Vector2(40, 40)
	il.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	il.mouse_filter = Control.MOUSE_FILTER_IGNORE
	iv.add_child(il)
	icon_dot = Label.new()
	icon_dot.text = "●"
	icon_dot.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	icon_dot.add_theme_font_size_override("font_size", 12)
	icon_dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	iv.add_child(icon_dot)
	icon_box.visible = false
	add_child(icon_box)
	if OS.get_environment("MWSIM_MINI_TEST") in ["1", "2"]:   # only for tests: mini mode by itself after 12 s (2: then the icon)
		get_tree().create_timer(12.0).timeout.connect(enter)
		if OS.get_environment("MWSIM_MINI_TEST") == "2":
			get_tree().create_timer(24.0).timeout.connect(func(): set_tiny(true))


func _process(dt: float) -> void:
	# CPU of this PC: measured while the box is shown or while MoveEye is connected (it shows it, 3D-3.24)
	var want_cpu := true                       # always (3D-3.26): the window shows it at the top, MoveEye in its header
	if want_cpu and not cpu_run:
		_cpu_start()
	elif not want_cpu and cpu_run and not mini:
		_cpu_stop()
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
	var col := Color(0.25, 0.85, 0.45) if connected else (Color(0.95, 0.7, 0.2) if sending else Color(0.55, 0.6, 0.66))
	dot.add_theme_color_override("font_color", col)
	line3.add_theme_color_override("font_color", col)
	line3.text = "verbunden" if connected else ("wartet" if sending else "aus")
	line1.text = "MoveEye Sim  %s" % main.VERSION
	var parts := PackedStringArray()
	parts.append(("%.0f Bilder/s" % fps) if sending else "sendet nicht")
	if own["pc"] >= 0:
		parts.append("PC %d %%" % roundi(own["pc"]))
	if own["sim"] >= 0:
		parts.append("Sim %d %%" % roundi(own["sim"]))
	if sending and main.net != null and main.net.port != main.stream_port:
		parts.append("Port %d" % main.net.port)
	line2.text = "  ·  ".join(parts)
	if connected:
		var c: Dictionary = main.cpu_info
		var mwp := PackedStringArray([(str(main.mw.get("device", "MoveEye")) + " " + str(main.mw.get("mw_version", ""))).strip_edges()])
		if c.get("total", null) != null and c.get("sim", null) == null:
			mwp.append("Gerät-CPU %d %%" % roundi(float(c["total"])))
		elif c.get("mw", null) != null:
			mwp.append("MoveEye-CPU %d %%" % roundi(float(c["mw"])))   # 3D-4.22: «MoveEye-CPU» instead of «MW»
		line_cpu.text = "  ·  ".join(mwp).strip_edges()
	else:
		line_cpu.text = "MoveEye: –" if sending else "MoveEye sieht den Simulator nicht"
	var note := ""
	if not main.sim_active:
		note = "Pause – spart Strom, bis MoveEye fragt"
	elif sending and not connected:
		note = "wartet auf MoveEye …"
	if net_err() != "":
		note = net_err()
	line_own.text = note
	line_own.visible = note != ""
	icon_dot.add_theme_color_override("font_color", col)
	icon_box.tooltip_text = "%s · %s\n%s\n%s\nAnklicken: Kästchen wieder gross · Ziehen: verschieben" % [line1.text, line3.text, line2.text, line_cpu.text]


func net_err() -> String:
	if main.net != null and not main.stream_on and str(main.net.error_text) != "":
		return str(main.net.error_text)
	return ""


static func cpu_text(c: Dictionary) -> String:
	"""CPU as MoveEye measures it. Same computer (the simulator is found there): whole PC, MoveEye, simulator.
	MoveEye on the Pi: the Pi and MoveEye on it (the CPU of this PC cannot be measured then)."""
	var pc = c.get("total", null)
	if pc == null:
		return "CPU: – (misst MoveEye, sobald verbunden)"
	var mw = c.get("mw", null)
	var sim = c.get("sim", null)
	if sim != null:
		return "CPU PC %d %%  ·  MoveEye %s  ·  Simulator %d %%" % [roundi(float(pc)), "–" if mw == null else "%d %%" % roundi(float(mw)), roundi(float(sim))]
	return "CPU MoveEye-Gerät %d %%  ·  davon MoveEye %s" % [roundi(float(pc)), "–" if mw == null else "%d %%" % roundi(float(mw))]


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
	tiny = false
	panel.visible = true
	icon_box.visible = false
	t_upd = 0.0
	_cpu_start()
	_paint()


func set_tiny(on: bool) -> void:
	"""▁: the box becomes a small icon in the same corner (and back)"""
	if not mini:
		return
	var w := get_window()
	var corner := w.position + w.size                     # keep the lower right corner where it is
	tiny = on
	panel.visible = not on
	icon_box.visible = on
	w.min_size = Vector2i(48, 48)
	w.size = ICON_SIZE if on else MINI_SIZE
	w.position = corner - w.size
	_paint()


func leave() -> void:
	var w := get_window()
	mini = false
	tiny = false
	panel.visible = false
	icon_box.visible = false
	_cpu_stop()
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
			if tiny and not moved:
				set_tiny(false)                           # click on the icon: the box again
	elif ev is InputEventMouseMotion and dragging:
		var d := DisplayServer.mouse_get_position() - drag_from
		if d.length() > 4:
			moved = true
		if moved:
			get_window().position = drag_win + d



# ---- CPU of this PC and of the simulator (only while the box is shown) -----------------------------------------------------
func _cpu_start() -> void:
	if cpu_run:
		return
	cpu_run = true
	own = {"pc": -1.0, "sim": -1.0}
	if OS.get_name() == "Windows":
		# one small PowerShell loop (language-independent, unlike the names of the performance counters): load of the
		# processor in % and the CPU seconds of the simulator; it ends by itself when the simulator is gone
		var pid := OS.get_process_id()
		var cmd := ("$p=%d; while($true){ $pr=Get-Process -Id $p -ErrorAction SilentlyContinue; if(-not $pr){break}; " % pid
				+ "$l=(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average; "
				+ "Write-Output ('{0};{1}' -f $l, $pr.CPU); Start-Sleep -Seconds 3 }")
		cpu_pipe = OS.execute_with_pipe("powershell.exe", ["-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", cmd])
		if cpu_pipe.is_empty():
			return
		cpu_thread = Thread.new()
		cpu_thread.start(_win_reader)
	else:
		cpu_thread = Thread.new()
		cpu_thread.start(_linux_reader)


func _cpu_stop() -> void:
	cpu_run = false
	if cpu_pipe.has("pid"):
		OS.kill(int(cpu_pipe["pid"]))
	cpu_pipe = {}
	if cpu_thread != null:
		cpu_thread.wait_to_finish()
		cpu_thread = null


func _win_reader() -> void:
	var io: FileAccess = cpu_pipe.get("stdio")
	var last_cpu := -1.0
	var last_t := 0.0
	var cores: int = max(1, OS.get_processor_count())
	while cpu_run and io != null and io.is_open():
		var line := io.get_line().strip_edges()
		if line == "":
			if io.eof_reached() or io.get_error() != OK:
				break
			continue
		var parts := line.replace(",", ".").split(";")
		if parts.size() < 2:
			continue
		var t := Time.get_ticks_msec() / 1000.0
		var c := float(parts[1])
		var pc := float(parts[0])
		var sim := -1.0
		if last_t > 0.0 and t > last_t:
			sim = clampf((c - last_cpu) / (t - last_t) / cores * 100.0, 0.0, 100.0)
		last_cpu = c
		last_t = t
		own = {"pc": pc, "sim": sim if sim >= 0.0 else own["sim"]}


func _linux_reader() -> void:
	var cores: int = max(1, OS.get_processor_count())
	var tick := 100.0
	var prev := []
	while cpu_run:
		var st := _proc("/proc/stat").get_slice("\n", 0).split(" ", false)
		var me := _proc("/proc/self/stat")
		me = me.substr(me.rfind(")") + 2)
		var mf := me.split(" ", false)
		if st.size() > 5 and mf.size() > 14:
			var total := 0.0
			for i in range(1, st.size()):
				total += float(st[i])
			var idle := float(st[4]) + (float(st[5]) if st.size() > 5 else 0.0)
			var mine := float(mf[11]) + float(mf[12])
			var t := Time.get_ticks_msec() / 1000.0
			if not prev.is_empty() and total > prev[0]:
				var pc: float = (1.0 - (idle - prev[1]) / (total - prev[0])) * 100.0
				var sim: float = (mine - prev[2]) / tick / max(0.001, t - prev[3]) / cores * 100.0
				own = {"pc": clampf(pc, 0.0, 100.0), "sim": clampf(sim, 0.0, 100.0)}
			prev = [total, idle, mine, t]
		for _i in range(30):
			if not cpu_run:
				return
			OS.delay_msec(100)


static func _proc(path: String) -> String:
	"""files in /proc say «size 0»: read a block instead of «the whole file»"""
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	return f.get_buffer(8192).get_string_from_utf8()


func _exit_tree() -> void:
	_cpu_stop()
