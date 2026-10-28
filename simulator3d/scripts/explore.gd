extends Control
## 3D-3.55: «Erkunden» - drive the rover (the mover) through the world and look around, to try out and develop the
## simulation. Works with the keyboard (W A S D or the arrows, Shift = faster), the mouse (green stick, right button
## drag = look round, wheel = distance), touch (green stick) and a game controller, also by Bluetooth (left stick = drive,
## right stick = look round, RT / LT = gas / back, A = faster, Y = view, B = end, Start = explore on / off).
## A symbol at the top shows what steers right now: mouse, touch, controller or keyboard.

var main
var on := false
var view := "chase"                   # chase: behind the rover · driver: from the rover · top: from above
var device := "keyboard"              # keyboard | mouse | touch | pad
var orbit := 0.0                      # looking round (rad) around the rover
var pitch := 0.5                     # how steep from above (rad)
var dist := 6.0                       # distance of the view behind the rover (m)
var speed := 1.6                      # top speed while exploring (m/s)
var turbo := false
var _saved := {}
var _info: Label
var _dev_t := 0.0
var auto_top := false                # 3D-3.56: something stands between the rover and the view: from above for now
var _blk_t := 0.0                     # blocked since … / free since …
var _free_t := 0.0
var info_hidden := false              # 3D-3.61: the info at the top hidden (tool bar «Info»)
var invite: Control = null           # 3D-3.60: «Mitspieler einladen»: QR code + address, players move freely (game mode «free»)
var _inv_qr: TextureRect
var _inv_lbl: Label
var _inv_for := ""
var rp_ax: Array = []                 # 3D-3.59: the controller at the browser (standard mapping): axes, buttons, when, its name
var rp_bt: Array = []
var rp_t := -100.0
var rp_name := ""
var test_drive := Vector2.ZERO        # for tests (control «explore» drive)
var test_until := 0.0
const VIEWS := ["chase", "driver", "top"]
const VIEW_NAMES := {"chase": "hinterher", "driver": "Fahrersicht", "top": "von oben"}
const DEAD := 0.18                    # dead zone of the sticks


func _ready() -> void:
	set_anchors_preset(Control.PRESET_CENTER_TOP)
	custom_minimum_size = Vector2(640, 62)
	size = custom_minimum_size
	offset_left = -320
	offset_right = 320
	offset_top = 44                                       # under the CPU line at the top
	offset_bottom = 106
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info = Label.new()
	_info.position = Vector2(62, 6)
	_info.size = Vector2(570, 52)
	_info.add_theme_font_size_override("font_size", 13)
	_info.add_theme_color_override("font_color", Color(1, 1, 1))
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_info)
	visible = false
	invite = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.09, 0.85)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(10)
	invite.add_theme_stylebox_override("panel", sb)
	var vb := VBoxContainer.new()
	invite.add_child(vb)
	_inv_lbl = Label.new()
	_inv_lbl.add_theme_font_size_override("font_size", 13)
	_inv_lbl.custom_minimum_size = Vector2(190, 0)
	_inv_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(_inv_lbl)
	_inv_qr = TextureRect.new()
	_inv_qr.custom_minimum_size = Vector2(170, 170)
	_inv_qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_inv_qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_inv_qr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	vb.add_child(_inv_qr)
	invite.visible = false
	invite.mouse_filter = Control.MOUSE_FILTER_IGNORE
	invite.set_anchors_preset(Control.PRESET_TOP_LEFT)
	invite.position = Vector2(14, 236)                     # under the small map, above the view buttons
	call_deferred("_add_invite")


func _add_invite() -> void:
	get_parent().add_child(invite)


func set_invite(v: bool) -> void:
	"""players with their phone move freely in the world (walk, run, crouch, crawl) - to test the detection"""
	var g = main.game
	if g == null:
		return
	if v:
		main.game_mode = "free"
		g.set_open(true)
	invite.visible = v
	_inv_for = ""


func set_on(v: bool) -> void:
	if v == on:
		return
	on = v
	if on:
		_saved = {"mover": main.mover_on, "max": main.mover_max, "panel": main.ui_root.visible}
		main.set_mover(true)
		main.view_mode = 0
		main.show_panel(false)
		orbit = 0.0
	else:
		main.mover_max = float(_saved.get("max", main.mover_max))
		if not bool(_saved.get("mover", false)):
			main.set_mover(false)
		if bool(_saved.get("panel", true)):
			main.show_panel(true)
		if invite != null:
			invite.visible = false
		if main.spectate:
			main.spectate_stop()
	visible = on
	queue_redraw()


func state() -> Dictionary:
	var r: Node3D = main.rig
	return {"ok": true, "mast": main.mast_h, "on": on, "view": view, "auto_top": auto_top, "device": device, "speed": speed, "turbo": turbo,
			"x": snappedf(r.position.x, 0.01), "z": snappedf(r.position.z, 0.01), "pads": Input.get_connected_joypads().size(),
			"pad_name": Input.get_joy_name(Input.get_connected_joypads()[0]) if not Input.get_connected_joypads().is_empty() else ""}


func _set_device(d: String) -> void:
	if d != device:
		device = d
		queue_redraw()
	_dev_t = main.now()


func _input(ev: InputEvent) -> void:
	# which device steers - also when exploring is off (the controller's Start switches it on)
	if ev is InputEventJoypadButton and ev.pressed:
		if ev.button_index == JOY_BUTTON_START:
			set_on(not on)
			get_viewport().set_input_as_handled()
			return
		if not on:
			return
		_set_device("pad")
		match ev.button_index:
			JOY_BUTTON_X:
				spectator(not main.spectate)
			JOY_BUTTON_DPAD_RIGHT:
				set_invite(not invite.visible)
			JOY_BUTTON_B:
				set_on(false)
			JOY_BUTTON_Y:
				next_view()
			JOY_BUTTON_BACK:
				main.show_panel(not main.ui_root.visible)
			JOY_BUTTON_DPAD_UP:
				main.set_mast(main.mast_h + 0.1)        # 3D-3.57: the pole longer / shorter
			JOY_BUTTON_DPAD_DOWN:
				main.set_mast(main.mast_h - 0.1)
		get_viewport().set_input_as_handled()
		return
	if not on:
		return
	if ev is InputEventJoypadMotion and abs(ev.axis_value) > 0.35:
		_set_device("pad")
	elif ev is InputEventScreenTouch or ev is InputEventScreenDrag:
		_set_device("touch")
	elif ev is InputEventMouseButton and ev.pressed:
		if main._over_hud(ev.position):
			return                                       # 3D-3.60: over the panel / a box: scrolling and clicks are theirs
		if not (device == "touch" and main.now() - _dev_t < 0.6):   # a tap also sends a mouse click: keep «touch»
			_set_device("mouse")
		if ev.button_index == MOUSE_BUTTON_LEFT and ev.ctrl_pressed:   # Ctrl + click: the rover there
			main.place_rover_at(ev.position)
			get_viewport().set_input_as_handled()
			return
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			dist = clampf(dist - 0.8, 2.5, 30.0)
			get_viewport().set_input_as_handled()
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			dist = clampf(dist + 0.8, 2.5, 30.0)
			get_viewport().set_input_as_handled()
		elif ev.button_index == MOUSE_BUTTON_RIGHT and main.patrol.edit == "":
			get_viewport().set_input_as_handled()        # right button: look round (not the free view)
	elif ev is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) and main.patrol.edit == "":
		_set_device("mouse")
		orbit -= ev.relative.x * 0.006
		pitch = clampf(pitch + ev.relative.y * 0.004, 0.05, 1.3)
		get_viewport().set_input_as_handled()
	elif ev is InputEventKey and ev.pressed:
		_set_device("keyboard")
		match ev.keycode:
			KEY_ESCAPE:
				set_on(false)
			KEY_V:
				next_view()
				get_viewport().set_input_as_handled()
			KEY_C:
				spectator(not main.spectate)
				get_viewport().set_input_as_handled()
			KEY_J:
				set_invite(not invite.visible)
				get_viewport().set_input_as_handled()
			KEY_HOME:
				orbit = 0.0
				get_viewport().set_input_as_handled()
			KEY_PAGEUP:
				main.set_mast(main.mast_h + 0.1)
				get_viewport().set_input_as_handled()
			KEY_PAGEDOWN:
				main.set_mast(main.mast_h - 0.1)
				get_viewport().set_input_as_handled()


func spectator(v: bool) -> void:
	"""3D-3.60: the spectator: changing camera shots of the rover and the players (C / controller X)"""
	if v:
		main.spectate_start()
	else:
		main.spectate_stop()
	queue_redraw()


func next_view() -> void:
	view = VIEWS[(VIEWS.find(view) + 1) % VIEWS.size()]
	orbit = 0.0
	auto_top = false
	queue_redraw()


func remote_pad(ax: Array, bt: Array, nm: String) -> void:
	"""a controller at the browser (Motion Watch page, e.g. a PS5 controller at the PC while the simulator runs in a VM).
	Standard mapping: axes 0/1 left stick, 2/3 right stick; buttons 0 A/✕, 1 B/○, 3 Y/△, 6 LT/L2, 7 RT/R2, 8 Back/Create,
	9 Start/Options, 12 / 13 pad up / down"""
	var old: Array = rp_bt
	rp_ax = ax
	rp_bt = bt
	rp_t = main.now()
	rp_name = nm
	var pressed := func(i: int) -> bool: return i < bt.size() and int(bt[i]) == 1 and not (i < old.size() and int(old[i]) == 1)
	if pressed.call(9):
		set_on(not on)
	if not on:
		return
	_set_device("pad")
	if pressed.call(1):
		set_on(false)
	elif pressed.call(3):
		next_view()
	elif pressed.call(8):
		main.show_panel(not main.ui_root.visible)
	if pressed.call(12):
		main.set_mast(main.mast_h + 0.1)
	if pressed.call(13):
		main.set_mast(main.mast_h - 0.1)


func _rp_on() -> bool:
	return main.now() - rp_t < 0.6


func _rp_axis(a: int) -> float:
	"""the browser controller in Godot's numbering (left x/y = 0/1, right x/y = 2/3, triggers = 4/5)"""
	if not _rp_on():
		return 0.0
	if a == JOY_AXIS_TRIGGER_LEFT or a == JOY_AXIS_TRIGGER_RIGHT:
		var i := 6 if a == JOY_AXIS_TRIGGER_LEFT else 7       # the triggers are buttons with a value in the browser
		return float(rp_bt[i]) if i < rp_bt.size() else 0.0
	return float(rp_ax[a]) if a < rp_ax.size() else 0.0


func _axis(a: int) -> float:
	var v := _rp_axis(a)
	for d in Input.get_connected_joypads():
		var x := Input.get_joy_axis(d, a)
		if abs(x) > abs(v):
			v = x
	return 0.0 if abs(v) < DEAD else (v - signf(v) * DEAD) / (1.0 - DEAD)


func _pad_btn(b: int) -> bool:
	if _rp_on() and b == JOY_BUTTON_A and rp_bt.size() > 0 and int(rp_bt[0]) == 1:
		return true
	for d in Input.get_connected_joypads():
		if Input.is_joy_button_pressed(d, b):
			return true
	return false


func command() -> Vector2:
	"""(forward, turn right) from W A S D (the arrows come from rover_pad) and the controller"""
	if not on:
		return Vector2.ZERO
	var k := Vector2.ZERO
	if not main.karte.visible:
		if Input.is_key_pressed(KEY_W):
			k.x += 1.0
		if Input.is_key_pressed(KEY_S):
			k.x -= 1.0
		if Input.is_key_pressed(KEY_D):
			k.y += 1.0
		if Input.is_key_pressed(KEY_A):
			k.y -= 1.0
	if main.now() < test_until:
		k += test_drive
	var gx := _axis(JOY_AXIS_LEFT_X)
	var gy := _axis(JOY_AXIS_LEFT_Y)
	var gas := _axis(JOY_AXIS_TRIGGER_RIGHT) - _axis(JOY_AXIS_TRIGGER_LEFT)
	if abs(gx) > 0.0 or abs(gy) > 0.0 or abs(gas) > 0.0:
		k.x += clampf(-gy + gas, -1.0, 1.0)
		k.y += gx
		_set_device("pad")
	return k.limit_length(1.0) if k.length() > 1.0 else k


func _process(dt: float) -> void:
	if not on:
		return
	turbo = Input.is_key_pressed(KEY_SHIFT) or _pad_btn(JOY_BUTTON_A)
	main.mover_max = speed * (2.2 if turbo else 1.0)
	var rx := _axis(JOY_AXIS_RIGHT_X)                    # right stick: look round
	var ry := _axis(JOY_AXIS_RIGHT_Y)
	if abs(rx) > 0.0 or abs(ry) > 0.0:
		orbit -= rx * dt * 2.2
		pitch = clampf(pitch + ry * dt * 1.2, 0.05, 1.3)
		_set_device("pad")
	elif not Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) and main.pad_on and view == "chase":
		orbit = lerp_angle(orbit, 0.0, clampf(dt * 0.8, 0.0, 1.0))   # driving: the view swings back behind the rover
	main.view_mode = 0
	_invite_tick()
	visible = not info_hidden
	if main.spectate:                                    # the spectator moves the view
		_info.text = "Erkunden · Beobachter: %s\nC / X = zurück zur eigenen Ansicht · J / Steuerkreuz → = Mitspieler einladen" % main.spec_label
		return
	var rig: Node3D = main.rig
	var yaw: float = rig.rotation.y
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	var tp := rig.global_position + Vector3(0, 0.7, 0)
	var cam: Camera3D = main.view_cam
	if view == "driver":                                  # from the rover: a bit above the front, looking ahead (turn with right stick / mouse)
		var y2 := yaw + orbit
		var f2 := Vector3(-sin(y2), 0, -cos(y2))
		cam.global_position = rig.global_position + Vector3(0, 1.05, 0) + fwd * 0.25
		cam.look_at(cam.global_position + f2 * 10.0 + Vector3(0, -1.2 + (0.38 - pitch) * 4.0, 0), Vector3.UP)
	elif view == "top":
		var want := tp + Vector3(0.01, dist * 2.6 + 6.0, 0.01)
		cam.global_position = cam.global_position.lerp(want, clampf(dt * 3.0, 0.0, 1.0))
		cam.look_at(tp, Vector3.FORWARD.rotated(Vector3.UP, yaw))
	else:
		var y3 := yaw + orbit
		var back := Vector3(sin(y3), 0, cos(y3))
		var want2 := tp + back * dist * cos(pitch) + Vector3(0, dist * sin(pitch) + 0.6, 0)
		# 3D-3.56: a caravan, a tent, a house between the rover and the view -> by itself from above (steep), back when free
		var t: float = main.now()
		if _blocked(tp, want2):
			_free_t = t
			if not auto_top and t - _blk_t > 0.3:
				auto_top = true
				queue_redraw()
		else:
			_blk_t = t
			if auto_top and t - _free_t > 1.5:
				auto_top = false
				queue_redraw()
		if auto_top:
			want2 = tp + back * 2.0 + Vector3(0, dist * 1.4 + 5.0, 0)
		want2.y = max(want2.y, main.ground_y(want2.x, want2.z) + 1.0)
		cam.global_position = cam.global_position.lerp(want2, clampf(dt * (2.5 if auto_top else 4.0), 0.0, 1.0))
		cam.look_at(tp + fwd * (0.5 if auto_top else 2.0), Vector3.UP)
	var kmh: float = main.mover_max * 3.6 * max(abs(main._pad_l), abs(main._pad_r))
	var dn: String = {"keyboard": "Tastatur", "mouse": "Maus", "touch": "Touch", "pad": "Controller"}[device]
	if device == "pad" and _rp_on():
		dn = "Controller im Browser"
	_info.text = "Erkunden · %s · %s · %.1f km/h · Stange %.1f m%s\n%s" % [dn,
			VIEW_NAMES[view] + (" (automatisch von oben)" if auto_top and view == "chase" else ""), kmh, main.mast_h, " · schnell" if turbo else "", _help()]


func _invite_tick() -> void:
	if invite == null or not invite.visible:
		return
	var g = main.game
	if g == null or not g.open:
		invite.visible = false
		return
	var url: String = g.address()
	if url != _inv_for:
		_inv_for = url
		_inv_qr.texture = g.Qr.texture(url, 6)
	var n: int = g.count()
	_inv_lbl.text = "Mitspieler: mit dem Handy scannen (gleiches WLAN)\n%s\n%s" % [url, ("%d dabei · frei bewegen, niemand wird erwischt" % n) if n > 0 else "noch niemand dabei"]


func _blocked(a: Vector3, b: Vector3) -> bool:
	"""is something higher than the rover close to the line between the rover (a) and the view (b)?"""
	var a2 := Vector2(a.x, a.z)
	var b2 := Vector2(b.x, b.z)
	var seg := b2 - a2
	var n := int(ceil(seg.length() / 0.7))
	for i in range(1, n + 1):
		var p: Vector2 = a2 + seg * (float(i) / float(n))
		for o in main._ob_near(p):
			if o.has("r") and float(o["r"]) < 0.3:
				continue                                  # thin poles, trunks: they hide nothing
			if float(o.get("ht", 3.0)) < 1.0:
				continue
			if float(main._ob_closest(o, p)[1]) < 0.6:
				return true
	return false


func _help() -> String:
	match device:
		"pad":
			return "Linker Stick fahren · rechter Stick umschauen · A schnell · Y Ansicht · X Beobachter · Steuerkreuz ↑↓ Stange, → Mitspieler · B Ende"
		"touch":
			return "Grüner Stick unten rechts fahren · Ansicht und Ende oben im Feld"
		"mouse":
			return "Grünen Stick ziehen · rechte Taste = umschauen · Rad = Abstand · Strg+Klick = Rover hierhin · C Beobachter · Esc"
	return "W A S D / Pfeile fahren · Shift schnell · V Ansicht · Bild ↑↓ Stange · C Beobachter · J Mitspieler · Esc"


func _draw() -> void:
	if not on:
		return
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.07, 0.09, 0.78))
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.25, 0.75, 0.4, 0.9), false, 1.5)
	var c := Vector2(30, 31)                              # the symbol of the device that steers
	var w := Color(0.4, 0.9, 0.5)
	match device:
		"pad":
			draw_rect(Rect2(c + Vector2(-19, -9), Vector2(38, 20)), w, false, 2.0)
			draw_circle(c + Vector2(-19, 5), 7.0, Color(0.05, 0.07, 0.09))
			draw_arc(c + Vector2(-19, 5), 7.0, PI * 0.5, PI * 1.5, 10, w, 2.0)
			draw_circle(c + Vector2(19, 5), 7.0, Color(0.05, 0.07, 0.09))
			draw_arc(c + Vector2(19, 5), 7.0, -PI * 0.5, PI * 0.5, 10, w, 2.0)
			draw_line(c + Vector2(-13, 0), c + Vector2(-5, 0), w, 2.0)
			draw_line(c + Vector2(-9, -4), c + Vector2(-9, 4), w, 2.0)
			draw_circle(c + Vector2(8, -2), 2.2, w)
			draw_circle(c + Vector2(13, 3), 2.2, w)
		"mouse":
			draw_rect(Rect2(c + Vector2(-10, -16), Vector2(20, 32)), w, false, 2.0)
			draw_line(c + Vector2(0, -16), c + Vector2(0, -4), w, 2.0)
			draw_line(c + Vector2(-10, -4), c + Vector2(10, -4), w, 2.0)
		"touch":
			draw_rect(Rect2(c + Vector2(-5, -16), Vector2(10, 22)), w, false, 2.0)
			draw_rect(Rect2(c + Vector2(-11, 2), Vector2(22, 14)), w, false, 2.0)
			draw_arc(c + Vector2(0, -16), 9.0, PI * 1.15, PI * 1.85, 8, w, 1.5)
		_:
			draw_rect(Rect2(c + Vector2(-20, -12), Vector2(40, 24)), w, false, 2.0)
			for i in range(4):
				draw_rect(Rect2(c + Vector2(-16 + i * 9, -8), Vector2(6, 5)), w)
				draw_rect(Rect2(c + Vector2(-16 + i * 9, -1), Vector2(6, 5)), w)
			draw_line(c + Vector2(-10, 8), c + Vector2(10, 8), w, 2.0)
