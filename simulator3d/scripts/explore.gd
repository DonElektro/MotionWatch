extends Control
## 3D-3.55: «Erkunden» - drive the rover (the mover) through the world and look around, to try out and develop the
## simulation. Works with the keyboard (W A S D or the arrows, Shift = faster), the mouse (green stick, right button
## drag = look round, wheel = distance), touch (green stick) and a game controller, also by Bluetooth.
## 3D-4.13: the controller follows the ONE mapping of padmap.gd (right stick = drive, R1 + right stick = look round,
## left stick = the head of MoveEye, R3 = view, Select = live picture, Start held = end); here only the device symbol.
## A symbol at the top shows what steers right now: mouse, touch, controller or keyboard.
## Entwicklertool 1 (devtool.gd, 31.10.2026): «Flugkamera» (fly) - the free camera flies through everything (walls, ground,
## no collision): W A S D / Q E (Shift × 3), right mouse button = look round, wheel or + / − = speed; controller: right
## stick = fly, left stick = look round (the head of MoveEye stays still meanwhile), R2 / L2 = up / down, ✚ ↑↓ = speed,
## Start held = back. Esc or «Zurück» = the normal view again. Exploring and flying exclude each other.

const T = preload("res://scripts/i18n.gd")

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
var fly := false                      # Entwicklertool 1: the free fly camera (devtool.gd)
var fly_speed := 8.0                  # m/s (devtool.gd SPEEDS; Shift = × 3)
var _fly_back: Button = null
const FLY_SPEEDS := [1.0, 3.0, 8.0, 20.0, 60.0]
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
	_fly_back = Button.new()
	_fly_back.text = T.t("Zurück (Esc)")
	_fly_back.position = Vector2(520, 14)
	_fly_back.size = Vector2(110, 34)
	_fly_back.focus_mode = Control.FOCUS_NONE
	_fly_back.visible = false
	_fly_back.pressed.connect(func(): set_fly(false))
	add_child(_fly_back)


func _add_invite() -> void:
	get_parent().add_child(invite)


func set_invite(v: bool) -> void:
	"""players with their phone move freely in the world (walk, run, crouch, crawl) - to test the detection"""
	var g = main.game
	if g == null:
		return
	if v:
		if main.game_mode != "free":                     # 3D-3.88: say it instead of switching silently
			main.start_info = "Spielart auf «Zonen-Check» gestellt (Mitspieler einladen)"
		main.gamewiz.apply_preset("free")                # 3D-4.x: the preset of the wizard (no crystals, events, bots …)
	invite.visible = v
	_inv_for = ""


func set_fly(v: bool) -> void:
	"""Entwicklertool 1: the free fly camera on / off (the view stays where it is when it ends)"""
	if v == fly:
		return
	if v and on:
		set_on(false)                                    # exploring and flying exclude each other
	fly = v
	if fly:
		if main.spectate:
			main.spectate_stop()
		if main.fly_tw != null:
			main.fly_tw.kill()
		main.follow = false
		main.set_view(0)
		main.start_info = T.t("Flugkamera an – Esc oder «Zurück» = normale Ansicht")
	else:
		main.start_info = T.t("Flugkamera aus – normale Ansicht")
	_fly_back.visible = fly
	_info.size = Vector2(450 if fly else 570, 52)
	visible = fly or on
	queue_redraw()


func fly_step(dir: int) -> void:
	var i := 0
	for k in FLY_SPEEDS.size():
		if absf(float(FLY_SPEEDS[k]) - fly_speed) < absf(float(FLY_SPEEDS[i]) - fly_speed):
			i = k
	fly_speed = float(FLY_SPEEDS[clampi(i + dir, 0, FLY_SPEEDS.size() - 1)])


func _fly_input(ev: InputEvent) -> void:
	"""the keys and the mouse of the fly camera (W A S D Q E are read in _fly_tick)"""
	if ev is InputEventKey and ev.pressed and not ev.echo and not main.typing():
		_set_device("keyboard")
		match ev.keycode:
			KEY_ESCAPE:
				set_fly(false)
				get_viewport().set_input_as_handled()
			KEY_PLUS, KEY_KP_ADD, KEY_EQUAL:
				fly_step(1)
				get_viewport().set_input_as_handled()
			KEY_MINUS, KEY_KP_SUBTRACT:
				fly_step(-1)
				get_viewport().set_input_as_handled()
	elif ev is InputEventMouseButton and ev.pressed:
		if main._over_hud(ev.position):
			return
		_set_device("mouse")
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			fly_step(1)
			get_viewport().set_input_as_handled()
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			fly_step(-1)
			get_viewport().set_input_as_handled()
		elif ev.button_index == MOUSE_BUTTON_RIGHT:
			get_viewport().set_input_as_handled()        # right button: look round (not the orbit of the free view)
	elif ev is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		var cam: Camera3D = main.view_cam
		var r := cam.rotation
		cam.rotation = Vector3(clampf(r.x - ev.relative.y * 0.004, -1.5, 1.5), r.y - ev.relative.x * 0.004, 0.0)
		get_viewport().set_input_as_handled()


func _fly_tick(dt: float) -> void:
	main.view_mode = 0
	visible = true
	var cam: Camera3D = main.view_cam
	if main.fly_tw != null and main.fly_tw.is_running():
		return                                           # a jump of the developer tool is flying the view
	var mv := Vector3.ZERO
	if not main.typing() and not main.karte.visible:
		if Input.is_key_pressed(KEY_W):
			mv.z -= 1
		if Input.is_key_pressed(KEY_S):
			mv.z += 1
		if Input.is_key_pressed(KEY_A):
			mv.x -= 1
		if Input.is_key_pressed(KEY_D):
			mv.x += 1
		if Input.is_key_pressed(KEY_E):
			mv.y += 1
		if Input.is_key_pressed(KEY_Q):
			mv.y -= 1
	mv = mv.normalized()
	var pm = main.padmap
	if pm != null and not _game_pad():
		var m: Vector2 = pm.move()
		var lk: Vector2 = pm.look()
		var up: float = pm.trig("r2") - pm.trig("l2")
		if m != Vector2.ZERO or lk != Vector2.ZERO or absf(up) > 0.0:
			_set_device("pad")
		mv += Vector3(m.x, up, m.y)
		if lk != Vector2.ZERO:
			var r := cam.rotation
			cam.rotation = Vector3(clampf(r.x - lk.y * dt * 1.2, -1.5, 1.5), r.y - lk.x * dt * 1.8, 0.0)
		if pm.hit("up"):
			fly_step(1)
		if pm.hit("down"):
			fly_step(-1)
	var f := fly_speed * (3.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0)
	if mv != Vector3.ZERO:
		cam.global_translate(cam.global_transform.basis * mv.limit_length(1.0) * f * dt)   # no collision, no ground: through everything
	var dn: String = {"keyboard": T.t("Tastatur"), "mouse": T.t("Maus"), "touch": T.t("Touch"), "pad": T.t("Controller")}[device]
	var hl := T.t("rechter Stick fliegen · linker Stick umschauen · R2 / L2 hoch / runter · ✚ ↑↓ Tempo · Start halten = zurück") if device == "pad" \
			else T.t("W A S D fliegen · Q / E runter / hoch · Shift schneller · rechte Maustaste umschauen · Rad oder + / − Tempo · Esc zurück")
	_info.text = "%s · %s · %s m/s%s\n%s" % [T.t("Flugkamera"), dn, str(fly_speed).trim_suffix(".0"), " × 3" if Input.is_key_pressed(KEY_SHIFT) else "", hl]


func set_on(v: bool) -> void:
	if v == on:
		return
	if v and fly:
		set_fly(false)
	on = v
	if on and main.patrol != null and main.patrol.active:
		main.patrol.set_active(false)                    # 3D-3.88: exploring and patrol exclude each other
		main.start_info = "Patrouille angehalten (Erkunden)"
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
	return {"ok": true, "mast": main.mast_h, "on": on, "fly": fly, "fly_speed": fly_speed, "view": view, "auto_top": auto_top, "device": device, "speed": speed, "turbo": turbo,
			"x": snappedf(r.position.x, 0.01), "z": snappedf(r.position.z, 0.01), "pads": Input.get_connected_joypads().size(),
			"pad_name": Input.get_joy_name(Input.get_connected_joypads()[0]) if not Input.get_connected_joypads().is_empty() else ""}


func _set_device(d: String) -> void:
	if d != device:
		device = d
		queue_redraw()
	_dev_t = main.now()


func _input(ev: InputEvent) -> void:
	# which device steers - also when exploring is off (the controller's Start switches it on)
	if fly:
		_fly_input(ev)                                   # Entwicklertool 1: the fly camera
		return
	if _game_pad():
		return                                           # 3D-4.x: the controller belongs to the player at the PC (localplay.gd)
	if ev is InputEventJoypadButton and ev.pressed:
		if on:
			_set_device("pad")                           # 3D-4.13: the keys themselves: padmap.gd
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
	"""a controller at the browser (MoveEye page, e.g. a PS5 controller at the PC while the simulator runs in a VM).
	Standard mapping: axes 0/1 left stick, 2/3 right stick; buttons 0 A/✕, 1 B/○, 3 Y/△, 6 LT/L2, 7 RT/R2, 8 Back/Create,
	9 Start/Options, 12 / 13 pad up / down"""
	rp_ax = ax
	rp_bt = bt
	rp_t = main.now()
	rp_name = nm
	if on and not _game_pad():
		_set_device("pad")                               # 3D-4.13: the keys and sticks: padmap.gd (device WEB)


func _game_pad() -> bool:
	"""3D-4.x: somebody plays here at the PC (localplay.gd): the controller is his - no exploring, no MoveEye head"""
	return main.localplay != null and main.localplay.active


func _btn(gb: int, bi: int) -> bool:
	"""a button of the controller at the PC (Godot number) or at the browser (standard mapping number)"""
	if _rp_on() and bi < rp_bt.size() and float(rp_bt[bi]) > 0.5:
		return true
	for d in Input.get_connected_joypads():
		if Input.is_joy_button_pressed(d, gb):
			return true
	return false


func _lt_held() -> bool:
	return _raw_axis(JOY_AXIS_TRIGGER_LEFT) > 0.5


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


func _raw_axis(a: int) -> float:
	var v := _rp_axis(a)
	for d in Input.get_connected_joypads():
		var x := Input.get_joy_axis(d, a)
		if abs(x) > abs(v):
			v = x
	return v


func _axis(a: int) -> float:
	"""3D-3.97: stick drift cleaned properly (wish of Daniel - the per-axis dead zone of 3D-3.96 was not enough):
	  1. the rest position of each stick is taken off (measured with «Controller kalibrieren», and learnt by itself while a
	     stick rests: a value that stays the same for 3 s with nothing pressed is drift, not a hand)
	  2. a ROUND dead zone per stick (x and y together) - no more creeping along one axis when the other drifts
	  3. outside the dead zone the stick starts smoothly at 0 (no jump) and still reaches 1"""
	if a == JOY_AXIS_TRIGGER_LEFT or a == JOY_AXIS_TRIGGER_RIGHT:
		var tv := _raw_axis(a)
		return 0.0 if tv < 0.12 else (tv - 0.12) / 0.88
	var st := 0 if a in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y] else 1
	var v := stick(st)
	return v.x if a in [JOY_AXIS_LEFT_X, JOY_AXIS_RIGHT_X] else v.y


func stick_raw(st: int) -> Vector2:
	"""3D-4.13: the strongest controller (padmap.gd keeps the sticks of every controller)"""
	return main.padmap.stick_raw(st, -1) if main.padmap != null else Vector2.ZERO


func stick(st: int) -> Vector2:
	"""the stick with the rest position taken off and the round dead zone (3D-3.97, now in padmap.gd)"""
	return main.padmap.stick_clean(st, -1) if main.padmap != null else Vector2.ZERO


var _rest := [{"v": Vector2.ZERO, "t": 0.0}, {"v": Vector2.ZERO, "t": 0.0}]


func _learn_rest() -> void:
	"""a stick that stays exactly where it is for 3 s (± 0.02), not far out, with no button pressed: that is drift -
	it becomes the new rest position (the controller slowly drifts more when it gets warm or old)"""
	var t: float = main.now()
	var any_btn := _btn(JOY_BUTTON_A, 0) or _btn(JOY_BUTTON_LEFT_SHOULDER, 4) or _raw_axis(JOY_AXIS_TRIGGER_LEFT) > 0.2 or _raw_axis(JOY_AXIS_TRIGGER_RIGHT) > 0.2
	for st in range(2):
		var r := stick_raw(st)
		var R: Dictionary = _rest[st]
		if r.distance_to(R["v"]) > 0.02 or any_btn or r.length() > 0.4 or (Input.get_connected_joypads().is_empty() and not _rp_on()):
			R["v"] = r
			R["t"] = t
			continue
		if t - float(R["t"]) >= 3.0:
			var c := Vector2(float(main.pad_center[st * 2]), float(main.pad_center[st * 2 + 1]))
			if c.distance_to(r) > 0.01:
				main.pad_center[st * 2] = snappedf(r.x, 0.001)
				main.pad_center[st * 2 + 1] = snappedf(r.y, 0.001)
				main._settings_dirty = true
			R["t"] = t


var _cal := {}


func calibrate() -> String:
	"""measure the rest position of both sticks for 2 s (do not touch them)"""
	if Input.get_connected_joypads().is_empty() and not _rp_on():
		return "Kein Controller gefunden"
	_cal = {"t": main.now(), "sum": [0.0, 0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0, 0.0], "n": 0}
	return "Sticks nicht berühren – messe 2 s …"


func _cal_tick() -> void:
	if main.pad_auto:
		_learn_rest()
	if _cal.is_empty():
		return
	for a in range(4):
		var v := _raw_axis(a)
		_cal["sum"][a] += v
		_cal["max"][a] = maxf(float(_cal["max"][a]), absf(v))
	_cal["n"] += 1
	if main.now() - float(_cal["t"]) >= 2.0 and int(_cal["n"]) > 0:
		var c := []
		var worst := 0.0
		for a in range(4):
			var m: float = float(_cal["sum"][a]) / float(_cal["n"])
			c.append(snappedf(m, 0.001))
			worst = maxf(worst, absf(m))
		main.pad_center = c
		var wob := 0.0                                                       # how far the stick wobbles round its rest position
		for a in range(4):
			wob = maxf(wob, absf(float(_cal["max"][a]) - absf(float(c[a]))))
		main.pad_dead = clampf(wob * 2.0 + 0.06, 0.06, 0.3)
		main._settings_dirty = true
		main.start_info = "Controller kalibriert: Ruhelage %s, Totzone %d %%" % [str(c), int(main.pad_dead * 100)]
		_cal = {}


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
	if not main.karte.visible and not main.typing():
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
	if main.padmap != null and main.padmap.drive_cmd() != Vector2.ZERO:
		_set_device("pad")                               # 3D-4.13: the right stick drives (rover_pad.gd adds padmap.drive_cmd())
	return k.limit_length(1.0) if k.length() > 1.0 else k


func _process(dt: float) -> void:
	_cal_tick()                                              # 3D-3.96: calibration of the sticks
	if fly:
		_fly_tick(dt)
		return
	if not on:
		return
	turbo = Input.is_key_pressed(KEY_SHIFT)
	main.mover_max = speed * (2.2 if turbo else 1.0)
	var pm = main.padmap                                  # 3D-4.13: R1 + right stick turns the view (padmap.gd -> padview._look)
	if pm != null and pm.btn("r1") and pm.move() != Vector2.ZERO:
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
	_info.text = "Erkunden · %s · %s · %.1f km/h · Höhe der Kamera %.1f m%s\n%s" % [dn,
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
			return main.padmap.help_line("sim", ["drive", "orbit", "head", "view", "swap", "exit", "pole", "menu"]) if main.padmap != null else ""
		"touch":
			return "Grüner Stick unten rechts fahren · Ansicht und Ende oben im Feld"
		"mouse":
			return "Grünen Stick ziehen · rechte Taste = umschauen · Rad = Abstand · Strg+Klick = Rover hierhin · C Beobachter · Esc"
	return "W A S D / Pfeile fahren · Shift schnell · V Ansicht · Bild ↑↓ Höhe der Kamera · C Beobachter · J Mitspieler · Esc"


func _draw() -> void:
	if not on and not fly:
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
