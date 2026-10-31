extends Node
## 3D-4.13 «Ein Controller-Konzept» (wish of Daniel 30.10.2026): ONE mapping of the game controller for the whole simulator
## (window, «Erkunden», game at the PC) and MoveEye (Controller-Ansicht 538, the phone game page of game.gd):
##   left stick = head (pan / tilt) · right stick = rover / view (R1 held = turn the view) · R2 = shutter ·
##   A / B / X / Y = light / IR / photo / follow (in a game round: the tools of the guard / the moves of the sneaker, always
##   on the same places) · Select = swap pictures / views · Start = menu (held = leave) · L3 = head to the middle · R3 = view.
## The mapping itself is MAP inside the JS below (one text for the simulator and MoveEye part 542, the self-test of MoveEye
## compares them): [key, action, English, German] per mode. The simulator acts on the action, every help text is made from it.
## Also here: the sticks of every controller (rest position + round dead zone of 3D-3.97, sensitivity, invert Y, swap the
## sticks), the menus with the controller (focus navigation, A = select, B = back), vibration, several controllers with a
## role each (padroles.gd) and the controller of the browser (explore.remote_pad, device WEB).

var main
var MAP := {}
var roles := {}                       # device -> {"role": all | guard | runner | rover, "n": 1 …}; empty = every controller does everything
var menu := false                     # the menu mode: the controller moves the focus of the control panel / a dialog
var light_on := false                 # what the controller switched at MoveEye (MoveEye has no reply for it)
var ir_on := false
var hud                               # padhud.gd: chips of the controllers, direction, focus ring
var roles_ui                          # padroles.gd: «Controller zuteilen»
var last_use := -100.0                # when a controller was used last (the hud shows itself)
var last_dev := -1
var info := ""                        # the last thing the controller did (status line)
var _cur := {}                        # device -> {key: bool} this frame
var _prev := {}
var _ev := {}                         # device -> [keys that happened this frame: "a", "start", "start_long", "r1" (tap) …]
var _down_t := {}
var _long_done := {}
var _r1_used := {}
var _web_rumble := ""                 # a vibration for the controller at the browser (sent back with the next «pad» reply)
var _head_t := 0.0
var _head_ax := 0
var _nav_t := 0.0
var _nav_dir := Vector2.ZERO
var _seen_t := 0.0

const WEB := 99                       # the controller at the browser of MoveEye's simulator page (explore.rp_ax / rp_bt)
const GB := {"a": JOY_BUTTON_A, "b": JOY_BUTTON_B, "x": JOY_BUTTON_X, "y": JOY_BUTTON_Y, "l1": JOY_BUTTON_LEFT_SHOULDER,
		"r1": JOY_BUTTON_RIGHT_SHOULDER, "select": JOY_BUTTON_BACK, "start": JOY_BUTTON_START, "l3": JOY_BUTTON_LEFT_STICK,
		"r3": JOY_BUTTON_RIGHT_STICK, "up": JOY_BUTTON_DPAD_UP, "down": JOY_BUTTON_DPAD_DOWN, "left": JOY_BUTTON_DPAD_LEFT,
		"right": JOY_BUTTON_DPAD_RIGHT}
const WB := {"a": 0, "b": 1, "x": 2, "y": 3, "l1": 4, "r1": 5, "l2": 6, "r2": 7, "select": 8, "start": 9, "l3": 10, "r3": 11,
		"up": 12, "down": 13, "left": 14, "right": 15}
const ACT_ROLE := {"head": "guard", "center": "guard", "light": "guard", "ir": "guard", "photo": "guard", "follow": "guard",
		"shutter": "guard", "drive": "rover", "orbit": "rover", "zoom_in": "rover", "zoom_out": "rover", "view": "rover",
		"swap": "rover", "pole": "rover"}
const ROLE_ORDER := ["all", "guard", "runner", "rover"]


func _ready() -> void:
	process_priority = -100                               # before everybody else: the keys of this frame are known
	var j = JSON.parse_string(JS.get_slice("/*MAP*/", 1).get_slice("/*END*/", 0))
	MAP = j if j is Dictionary else {"keys": {}, "modes": {}, "roles": {}, "rumble": {}, "long": {}}
	Input.joy_connection_changed.connect(_on_joy)


func _on_joy(dev: int, connected: bool) -> void:
	if not connected:
		roles.erase(dev)
		_renumber()
		return
	var n := Input.get_connected_joypads().size()
	main.start_info = "Controller %d verbunden: %s%s" % [n, Input.get_joy_name(dev).left(30),
			" – mehrere Controller: Bedienfeld Mover › Controller › «Controller zuteilen»" if n > 1 else ""]


# ---- the controllers and their keys ------------------------------------------------------------------------------------
func rp_on() -> bool:
	var ex = main.explore
	return ex != null and main.now() - float(ex.rp_t) < 0.6


func devices() -> Array:
	var L: Array = Input.get_connected_joypads().duplicate()
	if rp_on():
		L.append(WEB)
	return L


func any() -> bool:
	return not devices().is_empty()


func dev_name(d: int) -> String:
	if d == WEB:
		return "Browser" + ((": " + str(main.explore.rp_name).left(24)) if main.explore != null and str(main.explore.rp_name) != "" else "")
	return Input.get_joy_name(d).left(28)


func raw_btn(k: String, d: int) -> bool:
	if d == WEB:
		var bt: Array = main.explore.rp_bt if main.explore != null else []
		var i: int = WB.get(k, -1)
		return rp_on() and i >= 0 and i < bt.size() and float(bt[i]) > 0.5
	if k == "l2":
		return Input.get_joy_axis(d, JOY_AXIS_TRIGGER_LEFT) > 0.5
	if k == "r2":
		return Input.get_joy_axis(d, JOY_AXIS_TRIGGER_RIGHT) > 0.5
	return GB.has(k) and Input.is_joy_button_pressed(d, GB[k])


func raw_axis(a: int, d: int) -> float:
	"""Godot's numbering (left x / y = 0 / 1, right = 2 / 3, triggers 4 / 5); the browser controller too"""
	if d == WEB:
		if not rp_on():
			return 0.0
		var ex = main.explore
		if a == JOY_AXIS_TRIGGER_LEFT or a == JOY_AXIS_TRIGGER_RIGHT:
			var i := 6 if a == JOY_AXIS_TRIGGER_LEFT else 7
			return float(ex.rp_bt[i]) if i < ex.rp_bt.size() else 0.0
		return float(ex.rp_ax[a]) if a < ex.rp_ax.size() else 0.0
	return Input.get_joy_axis(d, a)


func devs_for(role: String) -> Array:
	"""the controllers that may do the things of this role (nobody assigned: all)"""
	if roles.is_empty():
		return devices()
	var L := []
	for d in devices():
		if roles.has(d) and str(roles[d]["role"]) in [role, "all"]:
			L.append(d)
	return L


func role_of(d: int) -> String:
	return str(roles[d]["role"]) if roles.has(d) else ("all" if roles.is_empty() else "")


func btn(k: String, devs = null) -> bool:
	for d in (devices() if devs == null else devs):
		if bool(_cur.get(d, {}).get(k, false)):
			return true
	return false


func hit(k: String, devs = null) -> bool:
	"""pressed in this frame («start» / «select» / «r1»: see keys())"""
	for d in (devices() if devs == null else devs):
		if k in _ev.get(d, []):
			return true
	return false


func keys(devs = null) -> Array:
	var o := []
	for d in (devices() if devs == null else devs):
		for k in _ev.get(d, []):
			if not k in o:
				o.append(k)
	return o


func fired(mode: String, devs = null) -> Array:
	"""the actions of this mode whose key happened in this frame"""
	var o := []
	var M: Array = MAP.get("modes", {}).get(mode, [])
	for k in keys(devs):
		for e in M:
			if str(e[0]) == k and not str(e[1]) in o:
				o.append(str(e[1]))
	return o


func has_key(mode: String, k: String) -> bool:
	for e in MAP.get("modes", {}).get(mode, []):
		if str(e[0]) == k:
			return true
	return false


# ---- the sticks ----------------------------------------------------------------------------------------------------------
func stick_raw(st: int, d := -1) -> Vector2:
	"""st 0 = the left stick, 1 = the right one (physically); d -1 = the strongest of all controllers"""
	if d >= 0:
		return Vector2(raw_axis(JOY_AXIS_LEFT_X if st == 0 else JOY_AXIS_RIGHT_X, d), raw_axis(JOY_AXIS_LEFT_Y if st == 0 else JOY_AXIS_RIGHT_Y, d))
	var best := Vector2.ZERO
	for dd in devices():
		var v := stick_raw(st, dd)
		if v.length() > best.length():
			best = v
	return best


func stick_clean(st: int, d := -1) -> Vector2:
	"""3D-3.97: the rest position taken off and a ROUND dead zone; outside it starts smoothly at 0 and still reaches 1"""
	if devices().is_empty():
		return Vector2.ZERO
	var c := Vector2(float(main.pad_center[st * 2]), float(main.pad_center[st * 2 + 1])) if main.pad_center.size() >= 4 else Vector2.ZERO
	if d < 0:
		var best := Vector2.ZERO
		for dd in devices():
			var w := stick_clean(st, dd)
			if w.length() > best.length():
				best = w
		return best
	var v := stick_raw(st, d) - c
	var dead: float = clampf(float(main.pad_dead), 0.02, 0.5)
	var l := v.length()
	if l <= dead:
		return Vector2.ZERO
	var k := clampf((l - dead) / maxf(0.05, 1.0 - dead - c.length() * 0.5), 0.0, 1.0)
	return v / l * k


func _strongest(st: int, devs) -> Vector2:
	var best := Vector2.ZERO
	for d in (devices() if devs == null else devs):
		var v := stick_clean(st, d)
		if v.length() > best.length():
			best = v
	return best


func look(devs = null) -> Vector2:
	"""the «head» stick (left; right with «Sticks tauschen»): sensitivity and invert Y applied"""
	var v := _strongest(1 if main.pad_swap else 0, devs) * clampf(float(main.pad_sens), 0.2, 3.0)
	if main.pad_inv_y:
		v.y = -v.y
	return v


func move(devs = null) -> Vector2:
	"""the «rover / walk» stick (right; left with «Sticks tauschen»)"""
	return _strongest(0 if main.pad_swap else 1, devs)


func dpad(devs = null) -> Vector2:
	return Vector2(float(btn("right", devs)) - float(btn("left", devs)), float(btn("down", devs)) - float(btn("up", devs)))


func trig(k: String, devs = null) -> float:
	var v := 0.0
	for d in (devices() if devs == null else devs):
		v = maxf(v, raw_axis(JOY_AXIS_TRIGGER_LEFT if k == "l2" else JOY_AXIS_TRIGGER_RIGHT, d))
	return 0.0 if v < 0.12 else (v - 0.12) / 0.88


# ---- every frame -----------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	var t: float = main.now()
	_prev = _cur
	_cur = {}
	_ev = {}
	for d in devices():
		var s := {}
		for k in WB:
			s[k] = raw_btn(k, d)
		_cur[d] = s
		var p: Dictionary = _prev.get(d, {})
		var ev := []
		for k in ["a", "b", "x", "y", "l1", "l2", "r2", "l3", "r3", "up", "down", "left", "right"]:
			if s[k] and not bool(p.get(k, false)):
				ev.append(k)
		var kk := "%d:r1" % d                                # R1: a tap = zoom in, held with the right stick = turn the view
		if s["r1"] and not bool(p.get("r1", false)):
			_down_t[kk] = t
			_r1_used[d] = false
			ev.append("r1_down")                             # (the menus: R1 at once)
		if s["r1"] and stick_clean(0 if main.pad_swap else 1, d) != Vector2.ZERO:
			_r1_used[d] = true
		if not s["r1"] and bool(p.get("r1", false)) and not bool(_r1_used.get(d, false)) and t - float(_down_t.get(kk, 0.0)) < 0.4:
			ev.append("r1")
		for k in ["start", "select"]:                        # short = on release, long = when held long enough
			var key := "%d:%s" % [d, k]
			if s[k] and not bool(p.get(k, false)):
				_down_t[key] = t
				_long_done[key] = false
			if s[k] and not bool(_long_done.get(key, false)) and t - float(_down_t.get(key, t)) >= float(MAP.get("long", {}).get(k, 1000)) / 1000.0:
				_long_done[key] = true
				ev.append(k + "_long")
			if not s[k] and bool(p.get(k, false)) and not bool(_long_done.get(key, false)):
				ev.append(k)
		_ev[d] = ev
		if not ev.is_empty() or stick_clean(0, d) != Vector2.ZERO or stick_clean(1, d) != Vector2.ZERO:
			last_use = t
			last_dev = d
	if roles_ui != null and roles_ui.visible:
		return                                               # «Controller zuteilen» takes every key
	_seen_tick()
	if menu and main.localplay != null and main.localplay.active:
		set_menu(false)                                      # the game at the PC has its own menus
	if menu:
		_menu_tick(dt)
		return
	if _menu_wanted():
		set_menu(true)
		return
	var own: Array = main.localplay.pad_devs() if main.localplay != null and main.localplay.active else []
	if main.abenteuer != null and main.abenteuer.zweit != null:
		own.append_array(main.abenteuer.zweit.pad_devs())   # A5: the walkers of the Bergtal adventure (zu zweit)
	var free := []
	for d in devices():
		if not d in own:
			free.append(d)
	if not free.is_empty():
		_sim_tick(dt, free)


func game_owns(d: int) -> bool:
	return main.localplay != null and main.localplay.active and d in main.localplay.pad_devs()


# ---- the simulator window («sim» mode) -----------------------------------------------------------------------------------
func _ok(d: int, act: String) -> bool:
	if roles.is_empty():
		return true
	var r := role_of(d)
	return r == "all" or r == str(ACT_ROLE.get(act, r))


func _devs_ok(devs: Array, act: String) -> Array:
	return devs.filter(func(d): return _ok(d, act))


func _sim_tick(dt: float, devs: Array) -> void:
	var ex = main.explore
	var pv = main.padview
	for d in devs:
		for act in fired("sim", [d]):
			if _ok(d, act):
				do_sim(act)
	if menu:
		return
	# left stick / D-pad: the head of MoveEye in steps (MoveEye turns it - «look» through mw_cmd)
	var hd := _devs_ok(devs, "head")
	var hv := look(hd)
	var pole := btn("l2", _devs_ok(devs, "pole"))
	if not pole:
		hv += dpad(hd)
	var t: float = main.now()
	if hv != Vector2.ZERO and t - _head_t > 0.12:
		_head_t = t
		_head_ax = 1 - _head_ax if absf(hv.x) > 0.0 and absf(hv.y) > 0.0 else (0 if absf(hv.x) > 0.0 else 1)
		if _head_ax == 0:
			main.mw_look("right" if hv.x > 0.0 else "left", 0.6 + 2.0 * minf(absf(hv.x), 2.5))
		else:
			main.mw_look("down" if hv.y > 0.0 else "up", 0.6 + 2.0 * minf(absf(hv.y), 2.5))
	if pole and t - _head_t > 0.25:                          # L2 + ✚ ↑↓: the pole
		var pd := dpad(_devs_ok(devs, "pole"))
		if pd.y != 0.0:
			_head_t = t
			main.set_mast(main.mast_h - 0.1 * signf(pd.y))
	# R1 held + right stick: turn the view (with the rover around it)
	var od := _devs_ok(devs, "orbit")
	if btn("r1", od):
		var o := _strongest(0 if main.pad_swap else 1, od) * clampf(float(main.pad_sens), 0.2, 3.0)
		if main.pad_inv_y:
			o.y = -o.y
		if o != Vector2.ZERO and pv != null:
			pv._look(o.x, o.y, dt)
		return
	# right stick: the rover drives (rover_pad.command reads drive_cmd()), without the rover the view moves
	var m := move(_devs_ok(devs, "drive"))
	if m != Vector2.ZERO and not main.mover_on and pv != null and not (ex != null and ex.on):
		pv._fly(-m.y, m.x, dt)


func drive_cmd() -> Vector2:
	"""(forward, turn right) for the rover from the right stick - only in the «sim» mode and not while R1 turns the view"""
	if menu or (roles_ui != null and roles_ui.visible) or not main.mover_on:
		return Vector2.ZERO
	var devs := []
	for d in devices():
		if not game_owns(d) and _ok(d, "drive"):
			devs.append(d)
	if devs.is_empty() or btn("r1", devs):
		return Vector2.ZERO
	var m := move(devs)
	return Vector2(-m.y, m.x)


func _mw(op: String, extra := {}) -> void:
	var c := {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1), "op": op}
	c.merge(extra)
	main.mw_cmd = c


func mw_ok() -> bool:
	return main.now() - float(main.mw_t) < 3.0


func do_sim(act: String) -> void:
	"""one action of the «sim» mode (also for tests: control «padmap» do = act)"""
	var ex = main.explore
	var pv = main.padview
	var g = main.game
	var need_mw := act in ["light", "ir", "follow", "center"]
	match act:
		"menu":
			set_menu(true)
		"exit":
			if ex != null and ex.on:
				ex.set_on(false)
				_say("Erkunden beendet")
			elif pv != null and pv.view != "":
				pv._set_view("off")
				_say("Ansicht zurück")
		"center":
			main.mw_look("center")
			_say("Kopf zur Mitte")
		"light":
			light_on = not light_on
			main.mw_light(light_on)
			if main.headpad != null:
				main.headpad._light = light_on
			_say("Licht " + ("ein" if light_on else "aus"))
		"ir":
			ir_on = not ir_on
			_mw("ir", {"on": ir_on})
			_say("IR-Licht " + ("ein" if ir_on else "aus"))
		"photo":
			_say(photo())
		"follow":
			var on: bool = not main.mw_follow_on()
			_mw("track", {"on": on})
			_say("Folgen " + ("ein" if on else "aus"))
		"shutter":
			if g != null and g.shut != null and g.shut.human_mode() == "mw":
				var r: Dictionary = g.shut.fire(null, "Sim-PC")
				_say(str(r.get("text", r.get("error", ""))))
				rumble("hit" if bool(r.get("hit", false)) else "seen", _devs_ok(devices(), "shutter"))
			elif pv != null:
				pv._zoom(1.0)
		"zoom_in":
			if pv != null:
				pv._zoom(1.0)
		"zoom_out":
			if pv != null:
				pv._zoom(-1.0)
		"view":
			if ex != null and ex.on:
				ex.next_view()
				_say("Ansicht: " + str(ex.VIEW_NAMES.get(ex.view, ex.view)))
			elif pv != null:
				pv._set_view(pv._next(pv.NEXT_ROVER if main.mover_on else pv.NEXT_FREE))
				_say("Ansicht: " + str({"head": "Kopfkamera", "top": "von oben", "follow": "hinter dem Rover", "free": "frei"}.get(pv.view, pv.view)))
		"swap":
			if ex != null and ex.on:
				main.set_live(not main.live_on)
				_say("Livebild " + ("ein" if main.live_on else "aus"))
			else:
				main.set_view(0 if main.view_mode == 1 else 1)
				_say("Ansicht: " + ("Kopfkamera" if main.view_mode == 1 else "frei"))
	if need_mw and not mw_ok():
		_say("MoveEye ist nicht verbunden – Kopf, Licht und Folgen gehen nur mit MoveEye")


func photo() -> String:
	"""X: a photo of the head camera into the folder «Fotos» of the simulator (MoveEye records nothing in the simulation)"""
	var tex: Texture2D = main.vps[0].get_texture() if not main.vps.is_empty() else null
	var img: Image = tex.get_image() if tex != null else null
	if img == null or img.is_empty():
		return "Foto: noch kein Bild"
	DirAccess.make_dir_recursive_absolute("user://Fotos")
	var fn := "user://Fotos/Kopfkamera_%s.jpg" % Time.get_datetime_string_from_system().replace(":", "-")
	img.save_jpg(fn, 0.9)
	return "Foto gespeichert: " + ProjectSettings.globalize_path(fn)


func _say(t: String) -> void:
	if t == "":
		return
	info = t
	main.start_info = "🎮 " + t


# ---- the menus with the controller ------------------------------------------------------------------------------------
func set_menu(on: bool) -> void:
	if on == menu:
		return
	menu = on
	_nav_dir = Vector2.ZERO
	if on:
		if main.ui_root != null and not main.ui_root.visible and _dialog() == null:
			main.show_panel(true)
		focus_first(menu_root())
		_say("Menü: ✚ / linker Stick wählen · A auswählen · B zurück · Start schliessen")
	else:
		var f := get_viewport().gui_get_focus_owner()
		if f != null:
			f.release_focus()


func _dialog() -> Control:
	"""an open dialog of the window (the game wizard, «Controller zuteilen», news, a box …) - the topmost one"""
	var lay: Node = main.ui_layer
	if lay == null:
		return null
	var kids := lay.get_children()
	kids.reverse()
	for c in kids:
		if c is PanelContainer and c != main.ui_root and c != main.toolbar and c.visible and c.size.x > 180.0 and c.size.y > 120.0 and _first_focus(c) != null:
			return c
	return null


func _close_dialog(dl: Control) -> void:
	"""its own close button (✕, Schliessen, …), else just hide it"""
	var b := _find_close(dl)
	if b != null:
		b.emit_signal("pressed")
	else:
		dl.visible = false


func _find_close(n: Node) -> BaseButton:
	if n is BaseButton and (n as Control).is_visible_in_tree():
		var tx := str(n.get("text")).strip_edges()
		if tx in ["✕", "×", "x", "X", "Schliessen", "Zu", "Abbrechen", "Nicht jetzt", "Später", "OK"] or tx.begins_with("Schliessen"):
			return n
	for k in n.get_children():
		var f := _find_close(k)
		if f != null:
			return f
	return null


func menu_root() -> Control:
	var dl := _dialog()
	return dl if dl != null else main.ui_root


func _first_focus(n: Node) -> Control:
	if n is Control:
		var c: Control = n
		if not c.visible:
			return null
		if c.focus_mode != Control.FOCUS_NONE and not (c is BaseButton and (c as BaseButton).disabled) and not (c is Label) and not (c is LineEdit) and not (c is TextEdit):
			return c
	for k in n.get_children():
		var f := _first_focus(k)
		if f != null:
			return f
	return null


func focus_first(root: Control) -> bool:
	if root == null:
		return false
	var f := _first_focus(root)
	if f == null:
		return false
	f.grab_focus()
	_keep_visible(f)
	return true


func _menu_wanted() -> bool:
	return false                                             # (only Start opens the menu - a dialog does not take the controller by itself)


func _ui(act: String) -> void:
	for p in [true, false]:
		var e := InputEventAction.new()
		e.action = act
		e.pressed = p
		Input.parse_input_event(e)


func _keep_visible(c: Control) -> void:
	var n: Node = c.get_parent()
	while n != null:
		if n is ScrollContainer:
			(n as ScrollContainer).ensure_control_visible(c)
		n = n.get_parent()


func nav_tick(devs = null) -> void:
	"""✚ or the left stick move the focus (Godot focus navigation, held = repeats), A = ui_accept, B = ui_cancel"""
	var v := dpad(devs)
	var s := stick_clean(0, -1) if devs == null else _strongest(0, devs)
	if v == Vector2.ZERO and s.length() > 0.5:
		v = Vector2(signf(s.x), 0.0) if absf(s.x) > absf(s.y) else Vector2(0.0, signf(s.y))
	var t: float = main.now()
	if v != Vector2.ZERO:
		if v != _nav_dir or t >= _nav_t:
			_nav_t = t + (0.45 if v != _nav_dir else 0.16)
			_nav_dir = v
			var f := get_viewport().gui_get_focus_owner()
			if f == null:
				focus_first(menu_root())
			else:
				_ui("ui_down" if v.y > 0.0 else "ui_up" if v.y < 0.0 else "ui_right" if v.x > 0.0 else "ui_left")
			var f2 := get_viewport().gui_get_focus_owner()
			if f2 != null:
				_keep_visible(f2)
	else:
		_nav_dir = Vector2.ZERO
	if hit("a", devs):
		if get_viewport().gui_get_focus_owner() == null:
			focus_first(menu_root())
		else:
			_ui("ui_accept")


func _menu_tick(_dt: float) -> void:
	var dl0 := _dialog()                                     # a dialog came up meanwhile: the focus goes into it
	var fo := get_viewport().gui_get_focus_owner()
	if dl0 != null and (fo == null or not dl0.is_ancestor_of(fo)) and (fo == null or fo.get_window() == get_window()):
		focus_first(dl0)
	nav_tick()
	if hit("l1") or hit("r1_down"):                               # L1 / R1: control panel ⇄ the dock at the bottom (toolbar.gd)
		var tb = main.toolbar
		var fo2 := get_viewport().gui_get_focus_owner()
		if tb != null and tb.visible and not (fo2 != null and tb.is_ancestor_of(fo2)):
			focus_first(tb)
		elif main.ui_root != null:
			if not main.ui_root.visible:
				main.show_panel(true)
			focus_first(main.ui_root)
	if hit("b") :
		var f := get_viewport().gui_get_focus_owner()
		var dl := _dialog()
		if f != null and f.has_meta("pad_back"):
			(f.get_meta("pad_back") as Callable).call()       # e.g. a menu of the dock: close it, back to its symbol
		elif f != null and f.get_window() != get_window():
			_ui("ui_cancel")                                  # a list (OptionButton) is open: close it
		elif dl != null:
			_close_dialog(dl)                                 # B closes the dialog, the focus goes on below
			focus_first.call_deferred(menu_root())
		else:
			set_menu(false)
			_say("Menü geschlossen")
	elif hit("start") or hit("start_long"):
		set_menu(false)
		_say("Menü geschlossen")
	elif main.ui_root != null and not main.ui_root.visible and _dialog() == null:
		set_menu(false)


# ---- vibration -------------------------------------------------------------------------------------------------------------
func rumble(kind: String, devs = null) -> void:
	"""caught · hit · alarm · seen · catch (MAP.rumble: strong, weak, ms)"""
	if not main.pad_rumble:
		return
	var r: Array = MAP.get("rumble", {}).get(kind, [0.6, 0.5, 250])
	for d in (devices() if devs == null else devs):
		if d == WEB:
			_web_rumble = kind
		else:
			Input.start_joy_vibration(d, float(r[1]), float(r[0]), float(r[2]) / 1000.0)


func take_web_rumble() -> String:
	var k := _web_rumble
	_web_rumble = ""
	return k


func _seen_tick() -> void:
	"""the camera looks at the sneaker at the PC: a soft buzz every 2.5 s (like the phones)"""
	var lp = main.localplay
	if lp == null or not lp.active or str(lp.role) != "runner":
		return
	var SX: Dictionary = (lp._st.get("rx", {}) as Dictionary).get("sx", {})
	if bool(SX.get("lk", false)) and main.now() - _seen_t > 2.5:
		_seen_t = main.now()
		rumble("seen", lp.pad_devs())


# ---- several controllers ------------------------------------------------------------------------------------------------------
func set_role(d: int, r: String) -> void:
	if r == "":
		roles.erase(d)
	else:
		roles[d] = {"role": r, "n": int(roles[d]["n"]) if roles.has(d) else 0}
	_renumber()


func _renumber() -> void:
	var ds := roles.keys()
	ds.sort()
	var n := 1
	for d in ds:
		roles[d]["n"] = n
		n += 1


func number(d: int) -> int:
	if roles.has(d):
		return int(roles[d]["n"])
	return devices().find(d) + 1


func role_color(r: String) -> Color:
	var R: Array = MAP.get("roles", {}).get(r, ["", "", "#c0ccdd"])
	return Color(str(R[2]))


func role_name(r: String) -> String:
	var R: Array = MAP.get("roles", {}).get(r, ["", r, ""])
	return str(R[1])


func open_roles() -> void:
	if roles_ui == null:
		var cl := CanvasLayer.new()
		cl.layer = 62
		main.add_child(cl)
		roles_ui = preload("res://scripts/padroles.gd").new()
		roles_ui.pm = self
		roles_ui.theme = main.ui_root.theme if main.ui_root != null else null
		cl.add_child(roles_ui)
	set_menu(false)
	roles_ui.open()


# ---- the help (made from MAP) --------------------------------------------------------------------------------------------------
func help_rows(mode: String) -> Array:
	var o := []
	for e in MAP.get("modes", {}).get(mode, []):
		o.append([str(MAP.get("keys", {}).get(str(e[0]), e[0])), str(e[3]), str(e[1]), str(e[0])])
	return o


func help_line(mode: String, only := []) -> String:
	var L := PackedStringArray()
	for r in help_rows(mode):
		if only.is_empty() or (str(r[2]) in only and str(r[3]) != "dpad"):   # a short line: the D-pad only in the full help
			L.append("%s %s" % [r[0], r[1]])
	return " · ".join(L)


func mode_now() -> String:
	if menu:
		return "menu"
	var lp = main.localplay
	if lp != null and lp.active:
		return lp.pad_mode()
	return "sim"


func state() -> Dictionary:
	var ds := []
	for d in devices():
		ds.append({"dev": d, "name": dev_name(d), "role": role_of(d), "n": number(d)})
	return {"ok": true, "mode": mode_now(), "menu": menu, "devices": ds, "roles_open": roles_ui != null and roles_ui.visible,
			"focus": str(get_viewport().gui_get_focus_owner().get_class()) + ":" + str(get_viewport().gui_get_focus_owner().get("text")) if get_viewport().gui_get_focus_owner() != null else "",
			"info": info, "light": light_on, "ir": ir_on, "look": [look().x, look().y], "move": [move().x, move().y],
			"settings": {"dead": main.pad_dead, "sens": main.pad_sens, "inv": main.pad_inv_y, "swap": main.pad_swap, "rumble": main.pad_rumble}}


func command(d: Dictionary) -> Dictionary:
	"""control «padmap» (tests): {do: state | act | menu | roles | role | help, …}"""
	match str(d.get("do", "state")):
		"act":
			do_sim(str(d.get("act", "")))
		"menu":
			set_menu(bool(d.get("on", true)))
		"dock":
			return main.toolbar.dock_state() if main.toolbar != null else {}
		"roles":
			if bool(d.get("on", true)):
				open_roles()
			elif roles_ui != null:
				roles_ui.close()
		"role":
			set_role(int(d.get("dev", 0)), str(d.get("role", "")))
		"help":
			return {"ok": true, "mode": str(d.get("mode", mode_now())), "rows": help_rows(str(d.get("mode", mode_now())))}
		"rumble":
			rumble(str(d.get("kind", "hit")))
	return state()


# ---- the JS of the same mapping for the browser pages (phone game page of game.gd; MoveEye part 542 has the same text) ----------
# <padmap-js>
const JS := r"""window.MWPad = window.MWPad || (function () {
  "use strict";
  // ONE mapping of the game controller for MoveEye and its simulator (3D-4.13 / MoveEye 2.98.38, wish of Daniel 30.10.2026).
  // The same text is in simulator3d/scripts/padmap.gd (JS) and in MoveEye part 542 (PADMAP_JS) - the self-test compares them.
  // modes: [key, action, English, Deutsch]; the simulator acts on the action, the help overlays are made from the texts.
  const MAP = /*MAP*/{
    "keys": {"ls": "L ◉", "rs": "R ◉", "r1rs": "R1 + R ◉", "dpad": "✚", "a": "A", "b": "B", "x": "X", "y": "Y", "l1": "L1", "r1": "R1",
             "l2": "L2", "r2": "R2", "select": "Select", "select_long": "Select ⏱", "start": "Start", "start_long": "Start ⏱", "l3": "L3", "r3": "R3"},
    "modes": {
      "sim": [["ls", "head", "Turn / tilt the head of MoveEye", "Kopf von MoveEye drehen / neigen"],
              ["rs", "drive", "Drive the rover (without rover: move the view)", "Rover fahren (ohne Rover: Ansicht bewegen)"],
              ["r1rs", "orbit", "Hold R1: turn the view", "R1 halten: Ansicht drehen"],
              ["r2", "shutter", "Shutter in a game round (otherwise zoom in)", "Auslöser in einer Spielrunde (sonst hineinzoomen)"],
              ["l1", "zoom_out", "Zoom out", "Herauszoomen"], ["r1", "zoom_in", "Tap R1: zoom in", "R1 tippen: hineinzoomen"],
              ["a", "light", "Light on / off", "Licht ein / aus"], ["b", "ir", "IR light on / off", "IR-Licht ein / aus"],
              ["x", "photo", "Photo", "Foto"], ["y", "follow", "Follow on / off", "Folgen ein / aus"],
              ["l3", "center", "Head to the centre", "Kopf zur Mitte"], ["r3", "view", "Next view", "Nächste Ansicht"],
              ["select", "swap", "Swap pictures / views", "Bilder / Ansichten tauschen"],
              ["start", "menu", "Menu (control panel)", "Menü (Bedienfeld)"], ["start_long", "exit", "Hold 1 s: leave", "1 s halten: beenden"],
              ["dpad", "head", "Head in small steps", "Kopf in kleinen Schritten"],
              ["l2", "pole", "Hold L2 + ✚ ↑↓: pole longer / shorter", "L2 halten + ✚ ↑↓: Stange länger / kürzer"]],
      "view": [["ls", "head", "Turn / tilt the head of MoveEye", "Kopf von MoveEye drehen / neigen"],
               ["rs", "drive", "Drive the rover (without rover: move the view)", "Rover fahren (ohne Rover: Ansicht bewegen)"],
               ["r1rs", "orbit", "Hold R1: turn the view", "R1 halten: Ansicht drehen"],
               ["r2", "shutter", "Shutter in a game round (otherwise zoom in)", "Auslöser in einer Spielrunde (sonst hineinzoomen)"],
               ["l1", "zoom_out", "Zoom out", "Herauszoomen"], ["r1", "zoom_in", "Tap R1: zoom in", "R1 tippen: hineinzoomen"],
               ["a", "light", "Light on / off", "Licht ein / aus"], ["b", "ir", "IR light on / off", "IR-Licht ein / aus"],
               ["x", "photo", "Photo", "Foto"], ["y", "follow", "Follow on / off", "Folgen ein / aus"],
               ["l3", "center", "Head to the centre", "Kopf zur Mitte"], ["r3", "view", "Next view", "Nächste Ansicht"],
               ["select", "swap", "Swap pictures / views", "Bilder / Ansichten tauschen"],
               ["select_long", "estop", "Hold 1.5 s: emergency stop of the servos", "1,5 s halten: Not-Aus der Servos"],
               ["start", "menu", "Menu (the bar)", "Menü (die Leiste)"], ["start_long", "exit", "Hold 1 s: leave", "1 s halten: beenden"],
               ["dpad", "nav", "Choose a button of the bar (A = press, B = back)", "Knopf der Leiste wählen (A = drücken, B = zurück)"]],
      "guard": [["ls", "head", "Turn / tilt the head (the camera)", "Kopf (die Kamera) drehen / neigen"],
                ["rs", "fine", "Aim finely (slow)", "Fein zielen (langsam)"],
                ["r2", "shutter", "Shutter: a shot at the middle of the picture", "Auslöser: Schuss auf die Bildmitte"],
                ["l1", "zoom", "Zoom (tool)", "Zoom (Werkzeug)"],
                ["a", "light", "Light", "Licht"], ["b", "scan", "Scan (tool)", "Scan (Werkzeug)"],
                ["x", "catch", "«Caught!»", "«Erwischt!»"], ["y", "siren", "Siren (tool)", "Sirene (Werkzeug)"],
                ["l3", "center", "Head back to the start direction", "Kopf zurück in die Startrichtung"],
                ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
                ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
                ["dpad", "head", "Head in steps · menus: choose", "Kopf in Schritten · Menüs: wählen"]],
      "seek": [["ls", "head", "Turn / tilt the head (the camera)", "Kopf (die Kamera) drehen / neigen"],
               ["rs", "drive", "Drive the rover", "Rover fahren"],
               ["a", "light", "Light", "Licht"], ["x", "catch", "«Found!»", "«Gefunden!»"],
               ["l3", "center", "Head back to the start direction", "Kopf zurück in die Startrichtung"],
               ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
               ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
               ["dpad", "head", "Head in steps · menus: choose", "Kopf in Schritten · Menüs: wählen"]],
      "runner": [["ls", "look", "Look around", "Umschauen"], ["rs", "walk", "Walk", "Gehen"],
                 ["r2", "run", "Run (hold)", "Rennen (halten)"],
                 ["a", "lamp", "Lamp", "Lampe"], ["b", "crouch", "Crouch", "Ducken"],
                 ["x", "stone", "Throw a stone (hunter: press the thing)", "Stein werfen (Jäger: Ding drücken)"], ["y", "crawl", "Crawl", "Kriechen"],
                 ["l3", "center", "Look straight ahead", "Geradeaus schauen"],
                 ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
                 ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
                 ["dpad", "walk", "Walk · menus: choose", "Gehen · Menüs: wählen"]],
      "menu": [["dpad", "nav", "Choose (left stick too)", "Wählen (auch linker Stick)"], ["a", "ok", "Select", "Auswählen"],
               ["b", "back", "Back / close", "Zurück / schliessen"], ["l1", "area", "L1 / R1: control panel ⇄ dock", "L1 / R1: Bedienfeld ⇄ Leiste"],
               ["start", "close", "Close the menu", "Menü schliessen"]]},
    "roles": {"all": ["everything", "alles", "#c0ccdd"], "guard": ["guard (head)", "Wächter (Kopf)", "#ff9933"],
              "runner": ["sneaker", "Schleicher", "#59e673"], "rover": ["rover", "Rover", "#59a6ff"]},
    "rumble": {"caught": [1.0, 0.8, 500], "hit": [0.7, 0.5, 250], "alarm": [0.9, 0.6, 800], "seen": [0.25, 0.35, 120], "catch": [0.5, 0.7, 200]},
    "long": {"start": 800, "select": 1500}
  }/*END*/;
  const IX = {a: 0, b: 1, x: 2, y: 3, l1: 4, r1: 5, l2: 6, r2: 7, select: 8, start: 9, l3: 10, r3: 11, up: 12, down: 13, left: 14, right: 15};
  const SK = "mw-padset";                                  // dead zone, sensitivity, invert Y, swap sticks, vibration - per device
  const S = {dead: 0.18, sens: 1, inv: false, swap: false, rumble: true};
  try { Object.assign(S, JSON.parse(localStorage.getItem(SK) || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem(SK, JSON.stringify(S)); } catch (e) {} };
  function pads() { try { return [...(navigator.getGamepads ? navigator.getGamepads() : [])].filter(g => g && g.connected); } catch (e) { return []; } }
  const name = g => (g ? String(g.id).replace(/[(].*?[)]/g, "").trim().slice(0, 30) : "");
  function dz(x, y) {
    const d = Math.max(0.02, Math.min(0.5, +S.dead || 0.18)), l = Math.hypot(x, y);
    if (l <= d) return [0, 0];
    const k = Math.min(1, (l - d) / (1 - d)) / l; return [x * k, y * k];
  }
  // a reader for one controller: call read(gamepad, mode) every tick; then .head .move .orbit .dpad, .fired (actions), .btn(key)
  function Pad(mode) {
    const P = {mode: mode || "sim", cur: [], prev: [], fired: [], keys: [], head: [0, 0], move: [0, 0], orbit: [0, 0], dpad: [0, 0], downT: {}, longDone: {}, r1Used: false, g: null};
    P.btn = k => !!P.cur[IX[k]];
    P.val = k => { const b = P.g && P.g.buttons[IX[k]]; return b ? (b.value || (b.pressed ? 1 : 0)) : 0; };
    P.read = function (g, md) {
      if (md) P.mode = md;
      P.g = g || null; P.prev = P.cur; P.fired = []; P.keys = [];
      if (!g) { P.cur = []; P.head = P.move = P.orbit = P.dpad = [0, 0]; return P; }
      P.cur = [...g.buttons].map(b => !!(b && (b.pressed || b.value > 0.5)));
      let L = dz(g.axes[0] || 0, g.axes[1] || 0), R = dz(g.axes[2] || 0, g.axes[3] || 0);
      if (S.swap) [L, R] = [R, L];
      const k = Math.max(0.2, Math.min(3, +S.sens || 1)), iv = S.inv ? -1 : 1, now = Date.now();
      const M = MAP.modes[P.mode] || [], has = key => M.some(e => e[0] === key);
      const dn = i => P.cur[i] && !P.prev[i], up = i => !P.cur[i] && P.prev[i];
      P.head = [L[0] * k, L[1] * k * iv];
      P.dpad = [(P.cur[15] ? 1 : 0) - (P.cur[14] ? 1 : 0), (P.cur[13] ? 1 : 0) - (P.cur[12] ? 1 : 0)];
      const r1 = P.cur[5] && has("r1rs");
      if (dn(5)) { P.downT.r1 = now; P.r1Used = false; }
      if (r1 && (R[0] || R[1])) P.r1Used = true;
      P.orbit = r1 ? [R[0] * k, R[1] * k * iv] : [0, 0];
      P.move = r1 ? [0, 0] : R;
      ["a", "b", "x", "y", "l1", "l2", "r2", "l3", "r3", "up", "down", "left", "right"].forEach(key => { if (dn(IX[key])) P.keys.push(key); });
      if (up(5) && !P.r1Used && now - (P.downT.r1 || 0) < 400) P.keys.push("r1");
      ["start", "select"].forEach(key => {
        const i = IX[key], ms = MAP.long[key];
        if (dn(i)) { P.downT[key] = now; P.longDone[key] = false; }
        if (P.cur[i] && !P.longDone[key] && now - (P.downT[key] || now) >= ms && has(key + "_long")) { P.longDone[key] = true; P.keys.push(key + "_long"); }
        if (up(i) && !P.longDone[key]) P.keys.push(key);
      });
      P.keys.forEach(key => { const e = M.find(x => x[0] === key); if (e) P.fired.push(e[1]); });
      return P;
    };
    return P;
  }
  // vibration (Gamepad API: vibrationActuator, or hapticActuators where only those exist); g = null: all controllers
  function rumble(g, kind) {
    if (!S.rumble) return false;
    const r = MAP.rumble[kind] || MAP.rumble.hit; let ok = false;
    (g ? [g] : pads()).forEach(p => {
      try {
        const va = p.vibrationActuator;
        if (va && va.playEffect) { const q = va.playEffect("dual-rumble", {startDelay: 0, duration: r[2], strongMagnitude: r[0], weakMagnitude: r[1]}); if (q && q.catch) q.catch(() => {}); ok = true; }
        else if (p.hapticActuators && p.hapticActuators[0] && p.hapticActuators[0].pulse) { p.hapticActuators[0].pulse(r[0], r[2]); ok = true; }
      } catch (e) {}
    });
    return ok;
  }
  // the help: rows [key, text] of a mode (T = translation of the English text, de = take the German text)
  function help(mode, T, de) { return (MAP.modes[mode] || []).map(e => [MAP.keys[e[0]] || e[0], de ? e[3] : (T ? T(e[2]) : e[2])]); }
  function helpLine(mode, T, de, only) { return help(mode, T, de).filter((r, i) => !only || only.includes(MAP.modes[mode][i][1])).map(r => r[0] + " " + r[1]).join(" · "); }
  function helpTable(mode, T, de) {
    const tb = document.createElement("table"); tb.className = "mwpad-help";
    help(mode, T, de).forEach(([k, v]) => { const tr = document.createElement("tr"), a = document.createElement("td"), b = document.createElement("td"); a.textContent = k; b.textContent = v; tr.append(a, b); tb.appendChild(tr); });
    return tb;
  }
  // ONE crosshair: a red ring with a cross through it (simulator: gameshutter.gd draws the same)
  const XH_CSS = sel => sel + "{position:absolute;pointer-events:none;border:3px solid #ff3b30;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 1px rgba(0,0,0,.55),inset 0 0 0 1px rgba(0,0,0,.55)}"
    + sel + "::before," + sel + "::after{content:'';position:absolute;left:50%;top:50%;width:3px;height:calc(100% + 28px);background:#ff3b30;transform:translate(-50%,-50%);box-shadow:0 0 0 1px rgba(0,0,0,.4)}"
    + sel + "::after{transform:translate(-50%,-50%) rotate(90deg)}";
  // the mini-map: north up, the head in the middle, its field of view (yellow), the rover (green), me (white);
  // on the rim: yellow = where the head looks, green = where the rover drives. d = {hx, hz, hy (deg), fov, rx, rz, ry (deg), me: [x, z]}
  function drawMap(cv, d, span) {
    if (!cv || !cv.getContext || !d) return;
    const c = cv.getContext("2d"), W = cv.width, H = cv.height, R = Math.min(W, H) / 2 - 3, cx = W / 2, cy = H / 2, sc = R / ((span || 40) / 2);
    const dir = deg => { const a = deg * Math.PI / 180; return [-Math.sin(a), -Math.cos(a)]; };
    const at = (x, z) => [cx + (x - (d.hx || 0)) * sc, cy + (z - (d.hz || 0)) * sc];
    c.clearRect(0, 0, W, H);
    c.save(); c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.fillStyle = "rgba(8,12,20,.72)"; c.fill(); c.clip();
    const half = (d.fov || 66) / 2, n = 12;
    c.beginPath(); c.moveTo(cx, cy);
    for (let i = 0; i <= n; i++) { const v = dir((d.hy || 0) - half + 2 * half * i / n); c.lineTo(cx + v[0] * R * 0.95, cy + v[1] * R * 0.95); }
    c.closePath(); c.fillStyle = "rgba(255,210,60,.28)"; c.fill();
    if (d.rx != null) { const p = at(d.rx, d.rz), v = dir(d.ry || 0); c.save(); c.translate(p[0], p[1]); c.rotate(Math.atan2(v[1], v[0]) + Math.PI / 2);
      c.beginPath(); c.moveTo(0, -7); c.lineTo(5, 5); c.lineTo(-5, 5); c.closePath(); c.fillStyle = "#59e673"; c.fill(); c.restore(); }
    if (d.me) { const p = at(d.me[0], d.me[1]); c.beginPath(); c.arc(p[0], p[1], 4, 0, 2 * Math.PI); c.fillStyle = "#fff"; c.fill(); }
    c.beginPath(); c.arc(cx, cy, 4, 0, 2 * Math.PI); c.fillStyle = "#ff9933"; c.fill();
    c.restore();
    c.lineWidth = 2; c.strokeStyle = "rgba(255,255,255,.35)"; c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.stroke();
    const mark = (deg, col) => { const v = dir(deg), a = Math.atan2(v[1], v[0]); c.save(); c.translate(cx + v[0] * R, cy + v[1] * R); c.rotate(a + Math.PI / 2);
      c.beginPath(); c.moveTo(0, -1); c.lineTo(6, 9); c.lineTo(-6, 9); c.closePath(); c.fillStyle = col; c.fill(); c.restore(); };
    mark(d.hy || 0, "#ffd34d"); if (d.ry != null) mark(d.ry, "#59e673");
    c.fillStyle = "rgba(255,255,255,.8)"; c.font = "bold 10px system-ui,sans-serif"; c.textAlign = "center"; c.fillText("N", cx, cy - R + 12);
  }
  // the settings (one place per device: dead zone, sensitivity, invert Y, swap sticks, vibration)
  function settingsUI(el, T, de) {
    const tx = (en, dt) => (de ? dt : (T ? T(en) : en));
    const box = document.createElement("div"); box.className = "mwpad-set";
    const row = (lb, inp) => { const l = document.createElement("label"); l.style.cssText = "display:flex;align-items:center;gap:8px;margin:4px 0"; const s = document.createElement("span"); s.textContent = lb; s.style.flex = "1"; l.append(s, inp); box.appendChild(l); };
    const rng = (k, min, max, step) => { const i = document.createElement("input"); i.type = "range"; i.min = min; i.max = max; i.step = step; i.value = S[k]; i.style.width = "120px"; i.oninput = () => { S[k] = parseFloat(i.value); save(); }; return i; };
    const chk = k => { const i = document.createElement("input"); i.type = "checkbox"; i.checked = !!S[k]; i.onchange = () => { S[k] = i.checked; save(); }; return i; };
    row(tx("Dead zone", "Totzone"), rng("dead", 0.02, 0.5, 0.01)); row(tx("Sensitivity", "Empfindlichkeit"), rng("sens", 0.3, 2.5, 0.1));
    row(tx("Invert Y (look)", "Y umkehren (schauen)"), chk("inv")); row(tx("Swap the sticks", "Sticks tauschen"), chk("swap"));
    row(tx("Vibration", "Vibration"), chk("rumble"));
    box.addEventListener("click", e => e.stopPropagation());
    el.appendChild(box); return box;
  }
  return {MAP, IX, S, save, pads, name, Pad, rumble, help, helpLine, helpTable, XH_CSS, drawMap, settingsUI};
})();
"""
# </padmap-js>
