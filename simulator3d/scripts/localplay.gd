extends Control
## 3D-3.77: play here at the PC - no phone needed. A player like the ones on the phones (game.gd, kind «local»):
##   Schleicher: W A S D / arrows = go, mouse drag (left button) or Q / E = look round, Shift = run, C = crouch,
##               X = crawl, F = throw a stone, L = torch
##   Wächter:    the picture of the head camera; mouse drag or A / D / arrows = turn the head, Space = «Erwischt!»,
##               G = light, V = siren, N = scan, Z = zoom (3D-4.x: with energy, gametools.gd; controller B Y X LB)
##   Enter = start the round, R = replay after the round, B = one more / fewer bot (Shift+B), Esc = menu (leave)
## 3D-4.13: a game controller follows the ONE mapping of padmap.gd (modes «guard», «seek», «runner»): left stick = head /
## look, right stick = walk / the rover, R2 = shutter / run, A B X Y = light scan «Erwischt!» siren / lamp crouch stone
## crawl, Select = replay, Start = menu or start the round (held = leave), ✚ + A / B in the menus and on the card.
## One player per PC; with «Controller zuteilen» only the controllers of his role steer him (padmap.roles).
## The big 3D view of the window is switched off meanwhile (main._check_active), the own view is the camera of the figure.

var main
var active := false
var role := "runner"
var p = null                          # the player (game.gd dictionary)
var view: TextureRect
var hud: Control
var meter: ProgressBar
var meter_l: Label
var top_l: Label
var msg_l: Label
var tut_l: Label
var arrow: Control
var card: PanelContainer
var card_v: VBoxContainer
var help_l: Label
var menu_box: PanelContainer
var rp_view: Control                  # the replay
var _st := {}
var _st_t := 0.0
var _exp_t := 0.0
var _beat_t := 0.0
var _snd: AudioStreamPlayer
var _beat: AudioStreamWAV
var _drag := false
var _card_sig := ""
var _rp_t := 0.0
var _rp_play := true
var _rp_only := []                    # 3D-4.x: only this part of the replay [t0, t1] (the closest moment, gamerules.gd)

const UI = preload("res://scripts/ui_style.gd")


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	view = TextureRect.new()
	view.set_anchors_preset(Control.PRESET_FULL_RECT)
	view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	view.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(view)
	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(hud)
	var bar := PanelContainer.new()                   # top: name, time, meter
	bar.add_theme_stylebox_override("panel", UI.box(Color(0.03, 0.05, 0.08, 0.72), Color(0, 0, 0, 0), 12, 10, 0))
	bar.position = Vector2(14, 12)
	hud.add_child(bar)
	var bv := VBoxContainer.new()
	bar.add_child(bv)
	top_l = Label.new()
	top_l.add_theme_font_size_override("font_size", 16)
	bv.add_child(top_l)
	var mr := HBoxContainer.new()
	bv.add_child(mr)
	meter_l = Label.new()
	meter_l.text = "Gesehen"
	meter_l.add_theme_font_size_override("font_size", 13)
	mr.add_child(meter_l)
	meter = ProgressBar.new()
	meter.custom_minimum_size = Vector2(240, 16)
	meter.show_percentage = false
	meter.max_value = 100
	mr.add_child(meter)
	arrow = Control.new()                              # top right: the way to the goal
	arrow.custom_minimum_size = Vector2(96, 96)
	arrow.size = Vector2(96, 96)
	arrow.draw.connect(_draw_arrow)
	arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(arrow)
	msg_l = Label.new()                                # the middle: messages
	msg_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg_l.add_theme_font_size_override("font_size", 26)
	msg_l.add_theme_color_override("font_outline_color", Color.BLACK)
	msg_l.add_theme_constant_override("outline_size", 8)
	msg_l.set_anchors_preset(Control.PRESET_CENTER_TOP)
	hud.add_child(msg_l)
	tut_l = Label.new()
	tut_l.add_theme_font_size_override("font_size", 18)
	tut_l.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
	tut_l.add_theme_color_override("font_outline_color", Color.BLACK)
	tut_l.add_theme_constant_override("outline_size", 6)
	hud.add_child(tut_l)
	help_l = Label.new()                               # bottom: the keys
	help_l.add_theme_font_size_override("font_size", 13)
	help_l.add_theme_color_override("font_color", Color(0.85, 0.9, 0.95, 0.85))
	help_l.add_theme_color_override("font_outline_color", Color.BLACK)
	help_l.add_theme_constant_override("outline_size", 5)
	hud.add_child(help_l)
	card = PanelContainer.new()                        # lobby / end of the round
	card.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.08, 0.11, 0.94), UI.ACC, 16, 18, 1))
	card.custom_minimum_size = Vector2(520, 0)
	add_child(card)
	card_v = VBoxContainer.new()
	card_v.add_theme_constant_override("separation", 8)
	card.add_child(card_v)
	rp_view = Control.new()
	rp_view.set_anchors_preset(Control.PRESET_FULL_RECT)
	rp_view.visible = false
	rp_view.draw.connect(_draw_replay)
	rp_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rp_view)
	_snd = AudioStreamPlayer.new()
	add_child(_snd)
	call_deferred("_add_padhud")
	_beat = _make_beat()


var padhud: Control = null


func _add_padhud() -> void:
	"""3D-4.13: chips of the controllers, the mini-map with the field of view of the head, the focus ring (padhud.gd)"""
	if main.padmap == null:
		return
	padhud = preload("res://scripts/padhud.gd").new()
	padhud.main = main
	padhud.pm = main.padmap
	padhud.local = true
	add_child(padhud)


func _make_beat() -> AudioStreamWAV:
	"""a low double thump: the heartbeat"""
	var rate := 22050
	var data := PackedByteArray()
	var n := int(rate * 0.42)
	for i in range(n):
		var t := float(i) / rate
		var v := 0.0
		for st in [[0.0, 1.0], [0.17, 0.7]]:
			var dt: float = t - float(st[0])
			if dt >= 0.0 and dt < 0.14:
				v += sin(TAU * 55.0 * dt) * exp(-dt * 28.0) * float(st[1])
		var s := int(clampf(v, -1.0, 1.0) * 22000.0)
		data.append(s & 0xff)
		data.append((s >> 8) & 0xff)
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = data
	return w


# ---- start / stop -----------------------------------------------------------------------------------------------------
func start(r := "runner") -> void:
	var g = main.game
	if active:
		stop()
	if not g.open:
		g.set_open(true)
	if r == "guard" and not main.game_mode in ["guard", "seek"]:
		main.start_info = "Wächter am PC: zuerst die Spielart «Ein Spieler ist Wächter», «Team gegen Team» oder «Verstecken» wählen"
		r = "runner"
	p = g.add_local(r)
	if p == null or (p as Dictionary).is_empty():
		main.start_info = "Das Spiel ist voll"
		p = null
		return
	role = str(p["role"])
	active = true
	visible = true
	if main.gamewiz != null:
		main.gamewiz.close_wiz()
	main.show_panel(false)
	_card_sig = ""
	_paint_card()


func stop() -> void:
	if not active:
		return
	active = false
	visible = false
	rp_view.visible = false
	main.game.remove_local()
	p = null
	main.show_panel(true)


func on_event(k: String) -> void:
	if main.padmap != null and k in ["caught", "seen"]:      # 3D-4.13: the controller feels it
		main.padmap.rumble(k, pad_devs())
	if k == "caught":
		var tw := create_tween()
		modulate = Color(1.6, 0.6, 0.6)
		tw.tween_property(self, "modulate", Color.WHITE, 0.6)
	elif k in ["goal", "item"]:
		var tw2 := create_tween()
		modulate = Color(0.8, 1.5, 0.9)
		tw2.tween_property(self, "modulate", Color.WHITE, 0.5)


# ---- every frame --------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if not active:
		return
	var g = main.game
	if p == null or g.local_player() != p:
		stop()
		return
	role = str(p["role"])
	var vs := get_viewport_rect().size
	if size != vs:                                    # under a CanvasLayer the anchors do not size it
		position = Vector2.ZERO
		size = vs
	if role == "guard":
		view.texture = main.vps[g.guard_cam(p)].get_texture()
		view.modulate = Color.BLACK if g.seek_hiding() else Color.WHITE   # 3D-3.78: eyes closed while the others hide
	else:
		var vp: SubViewport = p["vp"]
		var want := Vector2i(int(clampf(vs.x * 0.6, 640, 1280)), int(clampf(vs.x * 0.6, 640, 1280) * 9.0 / 16.0))
		if vp.size != want:
			vp.size = want
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		view.texture = vp.get_texture()
		_exp_t -= dt
		if _exp_t <= 0.0:
			_exp_t = 1.0
			var img := vp.get_texture().get_image()
			if img != null and not img.is_empty():
				g._exposure(p, img)
	_controls(dt)
	_pad(dt)                                          # 3D-4.x: the game controller
	if not active:
		return                                            # 3D-4.13: Start held = left the game
	_st_t -= dt
	if _st_t <= 0.0:
		_st_t = 0.2
		_st = g.state_for(p)
		_paint_hud(vs)
		_paint_card()
	_heart(dt)
	if rp_view.visible:
		if _rp_play:
			_rp_t += dt * 2.0
		rp_view.queue_redraw()


func _controls(dt: float) -> void:
	var g = main.game
	var a = p["actor"]
	var fw := float(Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)) - float(Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN))
	var rt := float(Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT)) - float(Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT))
	var turn := float(Input.is_key_pressed(KEY_E)) - float(Input.is_key_pressed(KEY_Q))
	if menu_box != null or rp_view.visible:
		fw = 0.0
		rt = 0.0
		turn = 0.0
	if role == "guard" and main.game_mode == "seek":     # 3D-3.78: the seeker drives the rover, Q / E / mouse turn the head
		p["mx"] = rt
		p["my"] = -fw
		g.guard_yaw = wrapf(g.guard_yaw - turn * dt * 1.2, -PI, PI)
		return
	if role == "guard":
		g.guard_yaw = wrapf(g.guard_yaw - (rt + turn) * dt * 1.2, -PI, PI)
		g.guard_tilt = clampf(g.guard_tilt + fw * dt * 0.6, deg_to_rad(-40.0), deg_to_rad(15.0))
		return
	p["mx"] = rt
	p["my"] = -fw
	p["yaw"] = wrapf(float(p["yaw"]) - turn * dt * 2.0, -PI, PI)
	a.ctl_run = Input.is_key_pressed(KEY_SHIFT)


# ---- the game controller (3D-4.13: padmap.gd) ---------------------------------------------------------------------------
var _pad_n := 0
var _catches := -1


func pad_devs() -> Array:
	"""the controllers of the player at the PC: all, or (after «Controller zuteilen») those of his role"""
	var pm = main.padmap
	return pm.devs_for(role) if pm != null else []


func pad_on() -> bool:
	"""a controller at this PC or at the browser (MoveEye's simulator page) steers this player"""
	return main.padmap != null and not pad_devs().is_empty()


func pad_mode() -> String:
	if role == "guard":
		return "seek" if main.game_mode == "seek" else "guard"
	return "runner"


func _pad(dt: float) -> void:
	_pad_n += 1
	if not pad_on():
		return
	var pm = main.padmap
	var devs := pad_devs()
	var g = main.game
	var mode := pad_mode()
	var acts: Array = pm.fired(mode, devs)
	if "exit" in acts:
		stop()
		return
	if menu_box != null:                                   # the pause menu: ✚ / left stick + A, B or Start = go on
		pm.nav_tick(devs)
		if "menu" in acts or pm.hit("b", devs):
			_close_menu()
		return
	if "menu" in acts:
		if g.round_state in ["lobby", "end"]:
			rp_view.visible = false
			g.start_round()
		else:
			_open_menu()
		return
	if "replay" in acts and g.round_state == "end" and not g.replay.is_empty():
		rp_view.visible = not rp_view.visible
		_rp_t = 0.0
		_rp_play = true
		_rp_only = []
		_card_sig = ""
	if rp_view.visible:
		if pm.hit("b", devs):
			rp_view.visible = false
			_card_sig = ""
		return
	if card.visible:                                        # lobby / end: ✚ + A on the buttons of the card
		pm.nav_tick(devs)
		acts = acts.filter(func(a): return not a in ["light", "lamp", "catch", "stone"])   # A belongs to the card here
	var lk: Vector2 = pm.look(devs)
	var mv: Vector2 = pm.move(devs)
	var dp: Vector2 = Vector2.ZERO if card.visible else pm.dpad(devs)
	if role == "guard":
		for a in acts:
			match a:
				"catch", "shutter":
					g._guard_catch(p)
				"light":
					g._guard_light(p)
				"scan", "siren", "zoom":
					g.tools.use(p, a)                          # the tools of the guard (gametools.gd)
				"center":
					g.guard_yaw = 0.0
					g.guard_tilt = deg_to_rad(-9.0)
		var hv := lk + dp
		if mode == "seek":                                 # the seeker drives the rover with the right stick
			if mv != Vector2.ZERO:
				p["mx"] = mv.x
				p["my"] = mv.y
		else:
			hv += mv * 0.3                                 # right stick: aim finely
		g.guard_yaw = wrapf(g.guard_yaw - hv.x * dt * 1.4, -PI, PI)
		g.guard_tilt = clampf(g.guard_tilt - hv.y * dt * 0.7, deg_to_rad(-40.0), deg_to_rad(15.0))
		return
	var a = p["actor"]
	var wk := (mv + dp).limit_length(1.0)
	if wk != Vector2.ZERO:                                 # the keys keep working when the sticks rest
		p["mx"] = wk.x
		p["my"] = wk.y
	if lk != Vector2.ZERO:
		p["yaw"] = wrapf(float(p["yaw"]) - lk.x * dt * 2.4, -PI, PI)
		p["pitch"] = clampf(float(p["pitch"]) - lk.y * dt * 1.2, deg_to_rad(-40.0), deg_to_rad(15.0))
	if pm.trig("r2", devs) > 0.3:
		a.ctl_run = true
	for k in acts:
		match k:
			"stone":
				if g.jaeger.on():
					g.jaeger.act(p)
				else:
					g._throw(p)
			"crouch":
				a.ctl_posture = 0 if a.ctl_posture == 1 else 1
			"crawl":
				a.ctl_posture = 0 if a.ctl_posture == 2 else 2
			"lamp":
				p["lamp"] = not bool(p.get("lamp", false))
				if a.torch == null:
					a.add_torch()
				a.player_lamp = p["lamp"]
			"center":
				p["pitch"] = 0.0


func _input(ev: InputEvent) -> void:
	if not active:
		return
	var g = main.game
	if ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_LEFT:
			_drag = ev.pressed and not _over_card(ev.position)
			if role == "guard" and ev.pressed and ev.double_click:
				g._guard_catch(p)
		if not _over_card(ev.position):
			get_viewport().set_input_as_handled()
		return
	if ev is InputEventMouseMotion and _drag:
		if role == "guard":
			g.guard_yaw = wrapf(g.guard_yaw - ev.relative.x * 0.004, -PI, PI)
			g.guard_tilt = clampf(g.guard_tilt - ev.relative.y * 0.003, deg_to_rad(-40.0), deg_to_rad(15.0))
		else:
			p["yaw"] = wrapf(float(p["yaw"]) - ev.relative.x * 0.005, -PI, PI)
			p["pitch"] = clampf(float(p["pitch"]) - ev.relative.y * 0.004, deg_to_rad(-40.0), deg_to_rad(15.0))
		get_viewport().set_input_as_handled()
		return
	if not (ev is InputEventKey):
		return
	get_viewport().set_input_as_handled()                 # the keys belong to the game now (not to the view of the window)
	if not ev.pressed or ev.echo:
		return
	var a = p["actor"]
	match ev.keycode:
		KEY_ESCAPE:
			if rp_view.visible:
				rp_view.visible = false
			elif menu_box != null:
				_close_menu()
			else:
				_open_menu()
		KEY_ENTER, KEY_KP_ENTER:
			if g.more != null and g.more.probe_on():       # «Gameplay ausfeilen»: skip the probe round with Blinki
				g.more.probe_skip(p)
			elif g.round_state in ["lobby", "end"]:
				rp_view.visible = false
				g.start_round()
		KEY_C:
			a.ctl_posture = 0 if a.ctl_posture == 1 else 1
		KEY_X:
			a.ctl_posture = 0 if a.ctl_posture == 2 else 2
		KEY_F:
			if g.jaeger.on():
				g.jaeger.act(p)                            # «Fehlalarm-Jäger»: the button of the thing
			else:
				g._throw(p)
		KEY_L:
			p["lamp"] = not bool(p.get("lamp", false))
			if a.torch == null:
				a.add_torch()
			a.player_lamp = p["lamp"]
		KEY_SPACE:
			if role == "guard":
				g._guard_catch(p)
		KEY_G:
			if role == "guard":
				g._guard_light(p)
		KEY_V, KEY_N, KEY_Z:                               # 3D-4.x: siren, scan, zoom of the guard (gametools.gd)
			if role == "guard":
				g.tools.use(p, {KEY_V: "siren", KEY_N: "scan", KEY_Z: "zoom"}[ev.keycode])
		KEY_R:
			if g.round_state == "end" and not g.replay.is_empty():
				rp_view.visible = not rp_view.visible
				_rp_t = 0.0
				_rp_play = true
				_rp_only = []
		KEY_P:
			_rp_play = not _rp_play
		KEY_B:
			main.game_bots = clampi(main.game_bots + (-1 if ev.shift_pressed else 1), 0, 3)
			g.set_bots(main.game_bots)
			main._settings_dirty = true
			_card_sig = ""


func _over_card(pos: Vector2) -> bool:
	return (card.visible and card.get_global_rect().has_point(pos)) or (menu_box != null and menu_box.get_global_rect().has_point(pos)) \
			or (main.game != null and main.game.shut != null and main.game.shut.over_button(pos))      # 3D-4.x: the round shutter button


# ---- the picture on top -------------------------------------------------------------------------------------------------
func _paint_hud(vs: Vector2) -> void:
	var S := _st
	var rs := str(S.get("rs", "lobby"))
	var left := int(S.get("left", 0))
	var lives := int(S.get("lives", 0))
	var t := "%s · %s" % [p["name"], "Wächter" if role == "guard" else "Schleicher"]
	if rs == "play":
		t += " · ⏱ %d:%02d" % [left / 60, left % 60]
	elif rs == "countdown":
		t += " · Start in %d" % int(S.get("cd", 0))
	if role == "runner":
		t += " · erwischt %d%s" % [int(S.get("caught", 0)), (" / %d" % lives) if lives > 0 else ""]
		if int(S.get("items_all", 0)) > 0:
			t += " · Kristalle %d" % int(S.get("items", 0))
	else:
		t += " · %d× erwischt · %s" % [int(S.get("catches", 0)), main.game.tools.hud_text(p)]   # 3D-4.x: energy and tools
	var SX: Dictionary = (S.get("rx", {}) as Dictionary).get("sx", {})     # 3D-4.x: infos for the sneaker (gamerules.gd)
	if role == "runner" and not SX.is_empty():
		var nz := int(round(float(SX.get("nz", 0.0)) * 5.0))
		t += " · Lärm " + "■".repeat(nz) + "□".repeat(5 - nz) + (" · im Schatten" if bool(SX.get("sh", false)) else "") + (" · KAMERA SCHAUT HER" if bool(SX.get("lk", false)) else "")
	top_l.text = _plain(t)
	var su := int(S.get("susp", 0))
	meter.value = su
	meter.visible = role == "runner"
	meter_l.visible = role == "runner"
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.25, 0.85, 0.4).lerp(Color(1.0, 0.25, 0.2), su / 100.0)
	sb.set_corner_radius_all(6)
	meter.add_theme_stylebox_override("fill", sb)
	meter_l.text = "GESEHEN!" if bool(S.get("seen", false)) else "Gesehen"
	meter_l.add_theme_color_override("font_color", Color(1, 0.4, 0.35) if bool(S.get("seen", false)) else Color(0.85, 0.9, 0.95))
	msg_l.text = _plain(str(S.get("msg", "")))
	msg_l.position = Vector2((vs.x - msg_l.size.x) / 2.0, vs.y * 0.22)
	msg_l.size.x = 0
	tut_l.text = "" if str(S.get("tut", "")) == str(S.get("msg", "")) else _plain(str(S.get("tut", "")))
	tut_l.position = Vector2(16, vs.y - 86)
	arrow.visible = role == "runner" and rs in ["play", "countdown"]
	arrow.position = Vector2(vs.x - 118, 14)
	arrow.queue_redraw()
	if role == "guard" and main.game_mode == "seek":
		msg_l.text = ("AUGEN ZU! Noch %d s" % int(S.get("cd", 0))) if rs == "countdown" else msg_l.text
	help_l.text = ("W A S D: Rover fahren · Maus ziehen / Q E: Kopf drehen · Leertaste oder Doppelklick: «Gefunden!» · G: Licht · Esc: Menü" if role == "guard" and main.game_mode == "seek"
			else "Maus ziehen / Q E: umschauen · Bildmitte auf einen Spieler, dann Leertaste, Doppelklick oder runder Knopf: Auslöser · G Licht · V Sirene · N Scan · Z Zoom · W S: Kopf hoch / runter · Esc: Menü" if role == "guard"
			else "W A S D: gehen · Maus ziehen / Q E: umschauen · Shift: rennen · C: ducken · X: kriechen · F: Stein · L: Lampe · Esc: Menü")
	if pad_on():                                          # 3D-4.13: the controller - made from the one mapping (padmap.gd)
		var only: Array = {"seek": ["head", "drive", "catch", "light", "menu"], "guard": ["head", "shutter", "light", "scan", "catch", "siren", "zoom", "menu"],
				"runner": ["look", "walk", "run", "lamp", "crouch", "stone", "crawl", "menu"]}[pad_mode()]
		help_l.text = "Controller: " + main.padmap.help_line(pad_mode(), only) + "\n" + help_l.text
	var cn := int(S.get("catches", 0))                      # 3D-4.13: a catch of the guard: the controller feels the hit
	if role == "guard" and _catches >= 0 and cn > _catches and main.padmap != null:
		main.padmap.rumble("hit", pad_devs())
	_catches = cn
	help_l.position = Vector2(16, vs.y - 30 - (20 if pad_on() else 0))


func _draw_arrow() -> void:
	var c := Vector2(48, 48)
	arrow.draw_circle(c, 44, Color(0.03, 0.05, 0.08, 0.7))
	var ga := deg_to_rad(float(_st.get("ga", 0)))
	var tip := c + Vector2(sin(ga), -cos(ga)) * 30.0
	var l := c + Vector2(sin(ga - 2.5), -cos(ga - 2.5)) * 20.0
	var r := c + Vector2(sin(ga + 2.5), -cos(ga + 2.5)) * 20.0
	arrow.draw_colored_polygon(PackedVector2Array([tip, l, c, r]), Color(0.3, 1.0, 0.5))
	arrow.draw_string(get_theme_default_font(), Vector2(0, 92), "%d m" % int(float(_st.get("gd", 0))), HORIZONTAL_ALIGNMENT_CENTER, 96, 14, Color.WHITE)


func _heart(dt: float) -> void:
	if not main.game_heart or role != "runner" or str(_st.get("rs", "")) != "play":
		return
	var su := float(_st.get("susp", 0))
	if su < 35.0:
		_beat_t = 0.0
		return
	_beat_t -= dt
	if _beat_t <= 0.0:
		_beat_t = lerpf(0.95, 0.38, clampf((su - 35.0) / 65.0, 0.0, 1.0))
		_snd.stream = _beat
		_snd.volume_db = lerpf(-14.0, -2.0, clampf((su - 35.0) / 65.0, 0.0, 1.0))
		_snd.play()


# ---- lobby and end of the round -------------------------------------------------------------------------------------------
func _paint_card() -> void:
	var g = main.game
	var rs: String = g.round_state
	var show := rs in ["lobby", "end"] and menu_box == null and not rp_view.visible
	card.visible = show
	if not show:
		return
	var sig := "%s|%d|%d|%d|%s|%d|%d" % [rs, g.results.size(), g.count(), main.game_bots, str(_st.get("daily", {})), int(g.plus.seq), int(g.rules.seq)]
	if sig == _card_sig:
		_center(card)
		return
	_card_sig = sig
	for c in card_v.get_children():
		c.queue_free()
	var h := UI.heading("Runde fertig" if rs == "end" else "Bereit?")
	card_v.add_child(h)
	var RX: Dictionary = g.rules.state_for(p) if p != null else {}
	if rs == "end" and not (RX.get("win", {}) as Dictionary).is_empty():   # 3D-4.x: the winner screen (gamerules.gd)
		var W: Dictionary = RX["win"]
		var wl := UI.heading(_plain(str(W["title"])) + (" · %d Punkte" % int(W["score"]) if int(W["score"]) >= 0 else ""))
		wl.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
		card_v.add_child(wl)
		var rl: Array = W.get("roles", [])
		for ro in (rl if rl.size() > 1 else []):            # Balance: the best guard and the best sneaker, the team result
			var rl_ := UI.small(_plain("%s: %s – %d Punkte" % [ro["label"], ro["n"], int(ro["score"])]), UI.TXT)
			card_v.add_child(rl_)
		if str(W.get("team", "")) != "":
			card_v.add_child(UI.small(_plain(str(W["team"])), UI.TXT))
		if not (W.get("hl", {}) as Dictionary).is_empty():
			var hb := Button.new()
			hb.text = _plain(str(W["hl"]["text"])) + " – ansehen"
			hb.pressed.connect(func(): rp_view.visible = true; _rp_t = 0.0; _rp_play = true; _rp_only = [float(W["hl"]["t0"]), float(W["hl"]["t1"])]; _paint_card())
			card_v.add_child(hb)
	for k in ["fair", "next"]:
		if str(RX.get(k, "")) != "":
			var fl_ := UI.small(_plain(str(RX[k])), UI.TXT)
			fl_.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			fl_.custom_minimum_size.x = 480
			card_v.add_child(fl_)
	if rs == "end":
		if not g.flag_res.is_empty():                       # 3D-4.x: «Fahne erobern» - decided by the captures
			var fl := UI.heading("%s – %s" % [g.flag_res["text"], g.flag_res["title"]])
			card_v.add_child(fl)
		if not g.duel.is_empty():                           # 3D-4.x: MoveEye against the guard
			var dl_ := UI.heading(_plain("Duell: MoveEye %d : %d %s" % [int(g.duel["mw"]), int(g.duel["human"]), g.duel["who"]]))
			card_v.add_child(dl_)
			card_v.add_child(UI.small(_plain(str(g.duel["text"])), UI.TXT))
		var me0 = g.local_player()                          # 3D-4.x: what the round taught MoveEye, weather change, theft
		var pl_: Array = ([g.plus.teach_text(str(me0["name"]))] if me0 != null else []) + g.plus.lines()
		for ln in pl_:
			if str(ln) == "":
				continue
			var pll := UI.small(_plain(str(ln)), UI.TXT)
			pll.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			pll.custom_minimum_size.x = 480
			card_v.add_child(pll)
		for r in g.results:
			var l := Label.new()
			l.text = _plain("%d  %s – %s" % [int(r["score"]), r["n"], r["info"]])
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.custom_minimum_size.x = 480
			l.add_theme_color_override("font_color", Color(str(r["c"])) if str(r["c"]).begins_with("#") else Color.WHITE)
			card_v.add_child(l)
	else:
		var tip := UI.small("Ziel: %s. Folge dem grünen Pfeil oben rechts. Du bist %s." % [g.goal_name, "Wächter" if role == "guard" else "Schleicher"], UI.TXT)
		tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tip.custom_minimum_size.x = 480
		card_v.add_child(tip)
	var me_ = g.local_player()
	if me_ != null:                                         # 3D-4.x: the level of the player at the PC
		var xi: Dictionary = g.xp.info(str(me_["name"]))
		var lvl := UI.small("Stufe %d · %d XP (noch %d bis Stufe %d)%s" % [int(xi["lv"]), int(xi["xp"]), int(xi["to"]) - int(xi["xp"]), int(xi["lv"]) + 1,
				(" · als Nächstes: " + _plain(str(xi["next"]))) if str(xi["next"]) != "" else ""], UI.TXT)
		lvl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lvl.custom_minimum_size.x = 480
		card_v.add_child(lvl)
	var dl: Dictionary = _st.get("daily", {})
	if not dl.is_empty():
		var dd := UI.small(_plain(str(dl["text"])) + ("" if (dl["best"] as Array).is_empty() else " · Beste: " + ", ".join(PackedStringArray((dl["best"] as Array).map(func(b): return "%s %d" % [b["n"], b["score"]])))), UI.TXT)
		dd.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		dd.custom_minimum_size.x = 480
		card_v.add_child(dd)
	var phones := 0
	for q in g.players:
		if q != null and str(q.get("kind", "phone")) == "phone":
			phones += 1
	var others := UI.small("Handys: %d (QR-Code im Spiel-Assistenten) · Bots: %d (B / Shift+B)" % [phones, main.game_bots])
	others.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	others.custom_minimum_size.x = 480
	card_v.add_child(others)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	card_v.add_child(row)
	var sb := Button.new()
	sb.text = "▶ Runde starten (Enter)"
	UI.primary(sb)
	sb.pressed.connect(func(): rp_view.visible = false; g.start_round())
	row.add_child(sb)
	if pad_on():
		sb.grab_focus.call_deferred()                       # 3D-4.13: ✚ + A on the card
	if rs == "end" and not g.replay.is_empty():
		var rb := Button.new()
		rb.text = "Wiederholung (R)"
		rb.pressed.connect(func(): rp_view.visible = true; _rp_t = 0.0; _rp_play = true; _rp_only = []; _paint_card())
		row.add_child(rb)
	var bb := Button.new()
	bb.text = "+ Bot"
	bb.pressed.connect(func(): main.game_bots = mini(3, main.game_bots + 1); g.set_bots(main.game_bots); _card_sig = "")
	row.add_child(bb)
	var bm := Button.new()
	bm.text = "− Bot"
	bm.pressed.connect(func(): main.game_bots = maxi(0, main.game_bots - 1); g.set_bots(main.game_bots); _card_sig = "")
	row.add_child(bm)
	var me1 = g.local_player()
	if me1 != null and me1["role"] == "runner" and g.plus.gear_active():   # 3D-4.x: the camouflage thing (cycles through)
		var gb := Button.new()
		var cur: Array = g.plus._gear(str(me1.get("gear", "")))
		gb.text = _plain("Tarnung: " + str(cur[2]))
		gb.tooltip_text = _plain(str(cur[3]))
		gb.pressed.connect(func():
			var ids: Array = g.plus.GEAR.map(func(x): return x[0])
			var i: int = (ids.find(str(me1.get("gear", ""))) + 1) % ids.size()
			g.plus.choose(me1, ids[i])
			_card_sig = "")
		row.add_child(gb)
	var lv := Button.new()
	lv.text = "Verlassen"
	lv.pressed.connect(stop)
	row.add_child(lv)
	card.reset_size()
	card.modulate.a = 0.0
	create_tween().tween_property(card, "modulate:a", 1.0, 0.25)
	_center.call_deferred(card)


func _center(c: Control) -> void:
	var vs := get_viewport_rect().size
	c.position = Vector2((vs.x - c.size.x) / 2.0, (vs.y - c.size.y) / 2.0)


func _open_menu() -> void:
	menu_box = PanelContainer.new()
	menu_box.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.08, 0.11, 0.96), UI.ACC, 16, 18, 1))
	add_child(menu_box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	menu_box.add_child(v)
	v.add_child(UI.heading("Pause"))
	for d in [["Weiterspielen", _close_menu], ["Spiel verlassen", stop]]:
		var b := Button.new()
		b.text = d[0]
		b.custom_minimum_size = Vector2(260, 40)
		b.pressed.connect(d[1])
		v.add_child(b)
		if pad_on() and d[0] == "Weiterspielen":
			b.grab_focus.call_deferred()                    # 3D-4.13: ✚ + A in the menu
	card.visible = false
	_center.call_deferred(menu_box)


func _close_menu() -> void:
	if menu_box != null:
		menu_box.queue_free()
		menu_box = null
	_card_sig = ""


# ---- the replay: a map with all ways, the camera and who was seen when ---------------------------------------------------
func _draw_replay() -> void:
	var R: Dictionary = main.game.replay
	if R.is_empty():
		return
	var vs := get_viewport_rect().size
	rp_view.draw_rect(Rect2(Vector2.ZERO, vs), Color(0.03, 0.05, 0.07, 0.93))
	var pts: Array = R["pts"]
	var lo := Vector2(R["goal"][0], R["goal"][1])
	var hi := lo
	for q in [Vector2(R["mw"][0], R["mw"][1])]:
		lo = lo.min(q)
		hi = hi.max(q)
	for row in pts:
		for e in row[1]:
			var q2 := Vector2(e[1], e[2])
			lo = lo.min(q2)
			hi = hi.max(q2)
	lo -= Vector2(8, 8)
	hi += Vector2(8, 8)
	var area := Rect2(Vector2(40, 70), vs - Vector2(80, 130))
	var sc: float = min(area.size.x / max(1.0, hi.x - lo.x), area.size.y / max(1.0, hi.y - lo.y))
	var off := area.position + (area.size - (hi - lo) * sc) / 2.0
	var to := func(x: float, z: float) -> Vector2: return off + (Vector2(x, z) - lo) * sc
	var font := get_theme_default_font()
	rp_view.draw_string(font, Vector2(40, 44), "Wiederholung – Leertaste/P: Pause · R: schliessen", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
	for o in R["obst"]:
		rp_view.draw_circle(to.call(float(o[0]), float(o[1])), max(2.0, float(o[2]) * sc), Color(0.3, 0.33, 0.36, 0.8))
	var t_max: float = float(pts[-1][0]) if not pts.is_empty() else 1.0
	var tnow: float = fmod(_rp_t, t_max + 3.0)
	if _rp_only.size() == 2:                               # 3D-4.x: the closest moment only (slower)
		tnow = float(_rp_only[0]) + fmod(_rp_t * 0.5, float(_rp_only[1]) - float(_rp_only[0]) + 1.5)
	var k := 0
	while k < pts.size() - 1 and float(pts[k][0]) < tnow:
		k += 1
	var mw: Vector2 = to.call(float(R["mw"][0]), float(R["mw"][1]))
	if not pts.is_empty():                                 # the field of view of the head camera at this moment
		var yaw := deg_to_rad(float(pts[k][2]))
		var half := deg_to_rad(float(R["fov"]) / 2.0)
		var reach := 30.0 * sc
		var poly := PackedVector2Array([mw])
		for i in range(9):
			var a := yaw - half + 2.0 * half * i / 8.0
			poly.append(mw + Vector2(-sin(a), -cos(a)) * reach)
		rp_view.draw_colored_polygon(poly, Color(1.0, 0.85, 0.3, 0.18))
	rp_view.draw_circle(mw, 9, Color(1.0, 0.55, 0.15))
	var gp: Vector2 = to.call(float(R["goal"][0]), float(R["goal"][1]))
	rp_view.draw_circle(gp, 10, Color(0.3, 1.0, 0.45, 0.8))
	var cols := {}
	for w in R["who"]:
		cols[int(w[0])] = [Color(str(w[2])), str(w[1])]
	var last := {}
	for i in range(min(k + 1, pts.size())):
		for e in pts[i][1]:
			var sl := int(e[0])
			var q3: Vector2 = to.call(float(e[1]), float(e[2]))
			if last.has(sl):
				var c: Color = cols.get(sl, [Color.WHITE, ""])[0]
				rp_view.draw_line(last[sl], q3, Color(1, 0.3, 0.25) if int(e[4]) == 1 else c, 3.0 if int(e[4]) == 1 else 2.0)
			last[sl] = q3
	for sl in last:
		rp_view.draw_circle(last[sl], 7, cols.get(sl, [Color.WHITE, ""])[0])
		rp_view.draw_string(font, last[sl] + Vector2(9, -6), str(cols.get(sl, [Color.WHITE, "?"])[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)
	for ev in R["ev"]:
		if float(ev[0]) <= tnow:
			for i in range(pts.size()):
				if float(pts[i][0]) >= float(ev[0]):
					for e in pts[i][1]:
						if int(e[0]) == int(ev[1]):
							var q4: Vector2 = to.call(float(e[1]), float(e[2]))
							rp_view.draw_string(font, q4 + Vector2(-10, 6), "X" if ev[2] == "caught" else "ZIEL", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
					break
	rp_view.draw_string(font, Vector2(40, vs.y - 24), "%d:%02d / %d:%02d  ·  rot = gesehen" % [int(tnow) / 60, int(tnow) % 60, int(t_max) / 60, int(t_max) % 60], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.85, 0.9, 0.95))


func debug() -> Dictionary:
	var o := {"ok": true, "active": active, "role": role, "card": [card.position.x, card.position.y, card.size.x, card.size.y], "st": _st.get("rs", "")}
	if main.explore != null:                               # 3D-4.x: the controller (tests through control «pad»)
		var l0: Vector2 = main.explore.stick(0)
		o["pad"] = {"on": pad_on(), "l": [l0.x, l0.y], "n": _pad_n, "mode": pad_mode(), "devs": pad_devs(), "rp": main.explore.rp_bt,
				"menu": menu_box != null, "focus": str(get_viewport().gui_get_focus_owner().get("text")) if get_viewport().gui_get_focus_owner() != null else ""}
	if p != null:
		o["in"] = [p["mx"], p["my"], p["yaw"], int(p["actor"].ctl_posture), bool(p["actor"].ctl_run), bool(p.get("lamp", false))]
		var vp: SubViewport = p["vp"]
		o["vp"] = [vp.size.x, vp.size.y, vp.render_target_update_mode]
		var img := vp.get_texture().get_image()
		if img != null:
			img.save_png("user://localplay_debug.png")
			o["img"] = [img.get_width(), img.get_height()]
		o["cam"] = str((p["cam"] as Camera3D).global_position)
		o["layer"] = get_parent().get("layer")
		o["view"] = [view.position.x, view.position.y, view.size.x, view.size.y, view.visible, view.texture != null, size.x, size.y, is_visible_in_tree()]
	return o


func _plain(t: String) -> String:
	"""the font of the window has no emoji on every PC: leave them out (like the game wizard)"""
	var o := ""
	for i in range(t.length()):
		var c := t.unicode_at(i)
		if (c >= 0x2600 and c != 0x2715 and c < 0x3000) or c >= 0x1F000 or c == 0xFE0F or c == 0x200D:
			continue
		o += String.chr(c)
	return o.strip_edges().replace("  ", " ")
