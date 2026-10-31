extends Node3D
## 3D-3.61: «Patrouille» - the mover drives MoveEye round a fixed route (points set with the mouse) or to random
## points in an area (dragged open with the mouse). MoveEye watches the whole time: while driving the head swings to
## and fro, at every point the mover stops and the head looks all round. Optional: the head turns to something
## suspicious (a box of MoveEye, or a player the simulator guard suspects) and the mover drives slower.
## The game «Patrouille» (game.gd): the players sneak to the goal while the patrol drives; caught by the real detection
## of MoveEye or by the simulator guard (setting).

var main
var active := false
var mode := "points"                  # points: the route · area: random points in the area
var points: Array = []                # Vector2 (x, z)
var area := Rect2()                   # x, z, width, depth
var idx := 0
var target := Vector2.ZERO
var state := "drive"                  # drive | look
var look_t0 := 0.0
var dwell := 5.0                      # seconds at every point (looking round)
var speed := 0.9                      # m/s
var sweep := 70.0                     # degrees the head swings while driving
var follow := true                    # turn to something suspicious, drive slower
var head_yaw := 0.0                   # wanted pan of the head (relative to the mover)
var suspect := false
var edit := ""                        # "" | points | area: the mouse sets points / drags the area
var show_route := true
var _drag_from = null
var _click_at = null                   # 3D-3.66: where the left button went down (a click, not a drag, sets a point)
var _saved_max := 0.8
var _mk: Node3D
var _dirty := true
var _stuck_t := 0.0
var _stuck_pos := Vector2.ZERO
var _back_until := 0.0                 # stuck at an object: back a little and turn, then on
var _back_turn := 1.0
var _tries := 0
# 3D-3.76: «Überwachen»: first the question which place is guarded; the mover plans its own route round it (around the
# objects) and MoveEye keeps looking towards the place while it drives.
var guard := {}                        # {"c": Vector2, "r": float, "name": String} - empty = a route set by hand
# 3D-3.84 (makeover 17): the rover fully in MoveEye - a one-way trip («to the alarm», «to the charger»), its battery, the dock
var mission := ""                      # "" | alarm | dock | goto
var batt := 100.0
var _saved := {}
var _dock: Node3D
var _ask: PanelContainer
var _ask_r := 10.0


func _ready() -> void:
	_mk = Node3D.new()
	add_child(_mk)


func now() -> float:
	return main.now()


func ready_to_go() -> bool:
	return (mode == "points" and points.size() >= 2) or (mode == "area" and area.size.x > 2.0 and area.size.y > 2.0)


func set_active(v: bool) -> String:
	if v == active:
		return ""
	if v:
		if not ready_to_go():
			random_route()                               # nothing set yet: a route round MoveEye
		if main.explore != null and main.explore.on:
			main.explore.set_on(false)                   # 3D-3.88: exploring and patrol exclude each other
		active = true
		_saved_max = main.mover_max
		main.set_mover(true)
		idx = -1
		_next()
	else:
		active = false
		main.mover_max = _saved_max
		head_yaw = 0.0
	_dirty = true
	return ""


func ask() -> void:
	"""the question at the start: what shall be guarded? (things of the scene, MoveEye itself, or a click into the world)"""
	if _ask != null and is_instance_valid(_ask):
		_ask.queue_free()
	var UI = preload("res://scripts/ui_style.gd")
	var pc := PanelContainer.new()
	pc.theme = main.ui_root.theme
	pc.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ACC, 14, 16, 2))
	main.ui_layer.add_child(pc)
	_ask = pc
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	pc.add_child(v)
	v.add_child(UI.heading("Was soll überwacht werden?"))
	var tip := UI.small("Der Mover fährt selbst eine Runde um diesen Ort – um Hindernisse herum – und MoveEye schaut dabei immer wieder hin.")
	tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tip.custom_minimum_size = Vector2(380, 0)
	v.add_child(tip)
	var g := GridContainer.new()
	g.columns = 3
	g.add_theme_constant_override("h_separation", 6)
	g.add_theme_constant_override("v_separation", 6)
	v.add_child(g)
	for pl in places():
		var b := Button.new()
		b.text = pl[0]
		b.custom_minimum_size = Vector2(122, 40)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var c: Vector2 = pl[1]
		var nm: String = pl[0]
		b.pressed.connect(func():
			pc.queue_free()
			guard_start(c, _ask_r, nm))
		g.add_child(b)
	var pick := Button.new()
	pick.text = "📍 Ort in der Welt anklicken"
	pick.pressed.connect(func():
		pc.queue_free()
		edit = "pick"
		main.start_info = "Überwachen: den Ort in der Welt anklicken (Esc = abbrechen)")
	g.add_child(pick)
	if points.size() >= 2 or area.size.x > 2.0:
		var own := Button.new()
		own.text = "Eigene Route (wie gesetzt)"
		own.pressed.connect(func():
			pc.queue_free()
			guard = {}
			set_active(true))
		g.add_child(own)
	var rr := HBoxContainer.new()
	rr.add_theme_constant_override("separation", 6)
	v.add_child(rr)
	var rl := UI.small("Runde:", UI.TXT)
	rl.autowrap_mode = TextServer.AUTOWRAP_OFF
	rr.add_child(rl)
	var rbs := []
	for o in [[6.0, "eng (6 m)"], [10.0, "mittel (10 m)"], [16.0, "weit (16 m)"]]:
		var rb := Button.new()
		rb.text = o[1]
		rb.toggle_mode = true
		rb.button_pressed = absf(float(o[0]) - _ask_r) < 0.1
		rb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rr.add_child(rb)
		rbs.append(rb)
		var val: float = o[0]
		rb.pressed.connect(func():
			_ask_r = val
			for x in rbs:
				x.set_pressed_no_signal(x == rb))
	var cancel := Button.new()
	cancel.text = "Abbrechen"
	cancel.pressed.connect(func(): pc.queue_free())
	v.add_child(cancel)
	await get_tree().process_frame
	if is_instance_valid(pc):
		pc.position = (pc.get_viewport().get_visible_rect().size - pc.size) / 2.0
		pc.modulate.a = 0.0                               # a small fade in
		pc.create_tween().tween_property(pc, "modulate:a", 1.0, 0.25)


func places() -> Array:
	"""[name, Vector2] of the things worth guarding in this scene"""
	var out := [["MoveEye (Standort)", Vector2(main.home_pos.x, main.home_pos.z)]]
	for k in ["door", "bike"]:
		var p: Vector3 = main.obj.get(k, Vector3.ZERO)
		if p != Vector3.ZERO:
			out.append([{"door": "Tür / Haus", "bike": "Velo-Platz"}[k], Vector2(p.x, p.z)])
	for nm in main.test_props:
		var n = main.test_props[nm]
		if n != null and is_instance_valid(n) and n.visible:
			out.append([nm, Vector2(n.global_position.x, n.global_position.z)])
	return out


func guard_start(c: Vector2, r: float, nm: String) -> void:
	if _ask != null and is_instance_valid(_ask):
		_ask.queue_free()
	guard = {"c": c, "r": r, "name": nm}
	plan_round(c, r)
	if active:
		idx = -1
		_next()
	else:
		set_active(true)
	main.start_info = "Überwachen: %s – Runde %d m, %d Punkte" % [nm, int(r), points.size()]


func plan_round(c: Vector2, r: float) -> void:
	"""a round of points about r metres round c; every point at least 1.2 m from any object (pushed outwards, else
	inwards); where the way between two points touches an object, a point further out is put in between"""
	points.clear()
	var n := clampi(int(TAU * r / 5.0), 6, 14)
	var a0 := randf() * TAU
	for i in range(n):
		var dir := Vector2.from_angle(a0 + TAU * i / n)
		var got = null
		for k in range(0, 24):                              # 0, +0.5, -0.5, +1, -1 … metres
			var rr: float = r + (0.5 * ((k + 1) / 2)) * (1.0 if k % 2 == 1 else -1.0)
			if rr < 2.5:
				continue
			var q := c + dir * rr
			if not main.blocked(q, 1.2):
				got = q
				break
		if got != null:
			points.append(got)
	for _pass in range(2):
		var out := []
		for i in range(points.size()):
			var a: Vector2 = points[i]
			var b: Vector2 = points[(i + 1) % points.size()]
			out.append(a)
			if _way_blocked(a, b):
				var m := (a + b) / 2.0
				var away := (m - c).normalized() if (m - c).length() > 0.1 else Vector2.RIGHT
				for k in range(1, 20):
					var q := m + away * 0.6 * k
					if not main.blocked(q, 1.2) and not _way_blocked(a, q) and not _way_blocked(q, b):
						out.append(q)
						break
		points = out
	mode = "points"
	_dirty = true


func _way_blocked(a: Vector2, b: Vector2) -> bool:
	var n := maxi(1, int(a.distance_to(b) / 0.5))
	for k in range(1, n):
		if main.blocked(a.lerp(b, float(k) / n), 0.9):
			return true
	return false


func random_route() -> void:
	"""6 points in a ring round the place of MoveEye, never inside an object"""
	points.clear()
	var c := Vector2(main.home_pos.x, main.home_pos.z)
	var n := 6
	var a0 := randf() * TAU
	for i in range(n):
		var a := a0 + TAU * i / n + randf_range(-0.3, 0.3)
		var r := randf_range(6.0, 14.0)
		var p: Vector3 = main.free_spot(Vector3(c.x + cos(a) * r, 0, c.y + sin(a) * r), 0.8, false)
		points.append(Vector2(p.x, p.z))
	mode = "points"
	_dirty = true


func clear_route() -> void:
	points.clear()
	area = Rect2()
	_dirty = true


func goto_point(p: Vector2, why := "goto") -> void:
	"""drive to p, look round, back to the charger, stop - then the old route again"""
	if mission == "":
		_saved = {"points": points.duplicate(), "mode": mode, "guard": guard.duplicate(), "active": active}
	var home := Vector2(main.home_pos.x, main.home_pos.z)
	points = [p, home] if why != "dock" else [home]
	mode = "points"
	guard = {}
	mission = why
	idx = -1
	_dirty = true
	if active:
		_next()
	else:
		set_active(true)
	main.start_info = {"alarm": "Mover fährt zum Alarm", "dock": "Mover fährt zur Ladestation", "goto": "Mover fährt hin"}.get(why, why)


func _mission_end() -> void:
	var was := mission
	mission = ""
	var keep_on: bool = bool(_saved.get("active", false)) and was != "dock"
	if not _saved.is_empty():
		points = _saved["points"]
		mode = _saved["mode"]
		guard = _saved["guard"]
	_saved = {}
	_dirty = true
	if not keep_on:
		set_active(false)
	else:
		idx = -1
		_next()
	main.start_info = "Mover zurück an der Ladestation" if not keep_on else "Mover: weiter mit der Patrouille"


func _next() -> void:
	if mission != "" and idx >= points.size() - 1:
		_mission_end()
		return
	state = "drive"
	if mode == "area":
		var p := Vector3(randf_range(area.position.x, area.end.x), 0, randf_range(area.position.y, area.end.y))
		p = main.free_spot(p, 0.8, false)
		target = Vector2(p.x, p.z)
	elif not points.is_empty():
		idx = (idx + 1) % points.size()
		target = points[idx]
	_stuck_t = now()
	_tries = 0


func command() -> Vector2:
	"""(forward, turn right) for the mover, like the green stick"""
	if not active or main.measuring():
		return Vector2.ZERO                               # 3D-3.88: a test measures - the patrol waits where it is
	var rig: Node3D = main.rig
	var me := Vector2(rig.position.x, rig.position.z)
	if state == "look":
		return Vector2.ZERO
	if now() < _back_until:
		return Vector2(-0.6, _back_turn)
	var d := target - me
	if d.length() < 0.8:
		state = "look"
		look_t0 = now()
		return Vector2.ZERO
	var yaw: float = rig.rotation.y
	var want := atan2(-d.x, -d.y)
	var diff := wrapf(want - yaw, -PI, PI)
	var turn := clampf(-diff * 1.8, -1.0, 1.0)
	var fwd := clampf(cos(diff), 0.0, 1.0) * clampf(d.length() / 2.0, 0.35, 1.0)
	if suspect and follow:
		fwd *= 0.4                                        # something suspicious: slower
	return Vector2(fwd, turn)


func _process(dt: float) -> void:
	if _dirty:
		_dirty = false
		_draw_route()
		save_route()
	_mk.visible = show_route and (active or edit != "" or main.explore.on)
	_dock_tick()
	if not active:
		var rr: Node3D = main.rig
		if Vector2(rr.position.x - main.home_pos.x, rr.position.z - main.home_pos.z).length() < 1.5:
			batt = minf(100.0, batt + dt * 1.0)               # on the charger
		return
	main.mover_max = speed
	batt = maxf(0.0, batt - dt * 0.05)                      # about 30 minutes of driving
	if batt < 20.0 and mission == "":
		goto_point(Vector2(main.home_pos.x, main.home_pos.z), "dock")
	var t := now()
	var rig: Node3D = main.rig
	var me := Vector2(rig.position.x, rig.position.z)
	if state == "drive":                                   # stuck at an object for long: the next point
		if me.distance_to(_stuck_pos) > 0.3:
			_stuck_pos = me
			_stuck_t = t
		elif t - _stuck_t > 2.5:
			_tries += 1
			_stuck_t = t
			if _tries > 3:                              # this point cannot be reached: the next one
				_tries = 0
				_next()
			else:
				_back_until = t + 1.3
				_back_turn = 1.0 if randf() < 0.5 else -1.0
	# the head
	var want_h: float
	if state == "look":                                    # at the point: once all round, then on
		var k: float = clampf((t - look_t0) / dwell, 0.0, 1.0)
		want_h = lerpf(-PI * 0.95, PI * 0.95, k) if k > 0.05 else 0.0
		if k >= 1.0:
			_next()
	else:
		want_h = deg_to_rad(sweep * 0.5) * sin(t * 0.7)
		if not guard.is_empty():                           # 3D-3.76: towards the guarded place, swinging a little round it
			var dc: Vector2 = guard["c"] - me
			want_h = wrapf(atan2(-dc.x, -dc.y) - rig.rotation.y, -PI, PI) + deg_to_rad(sweep * 0.3) * sin(t * 0.7)
	suspect = false
	if follow:
		var s = _suspect_angle()
		if s != null:
			suspect = true
			want_h = float(s)
	head_yaw = want_h


func _suspect_angle():
	"""where something suspicious is, relative to the mover: a box of MoveEye, else a player the guard suspects"""
	var b = main.mw_det.get("boxes", [])
	if main.now() - main.mw_det_t < 2.0 and typeof(b) == TYPE_ARRAY and not b.is_empty():
		var bb: Array = b[0]
		var cx: float = float(bb[0]) + float(bb[2]) / 2.0
		var hfov: float = deg_to_rad(main.cams[0].fov) * 16.0 / 9.0
		return main.head.rotation.y + (0.5 - cx) * hfov
	var g = main.game
	if g != null and g.round_state == "play":
		var best = null
		for p in g.players:
			if p != null and p["role"] == "runner" and p["state"] == "play" and float(p["susp"]) > 40.0:
				if best == null or float(p["susp"]) > float(best["susp"]):
					best = p
		if best != null:
			var rig: Node3D = main.rig
			var d: Vector3 = best["actor"].position - rig.position
			return wrapf(atan2(-d.x, -d.z) - rig.rotation.y, -PI, PI)
	return null


# ---- the mouse sets the route: click = a point, right click = away; area: drag ------------------------------------------
func handle_input(ev: InputEvent) -> bool:
	if edit == "" or not (ev is InputEventMouseButton or ev is InputEventMouseMotion):
		return false
	if ev is InputEventMouseButton and main._over_hud(ev.position):
		return false
	var hit = _ground(ev.position)
	if edit == "pick" and ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			_click_at = ev.position
		elif _click_at != null and (ev.position as Vector2).distance_to(_click_at) < 8.0 and hit != null:
			edit = ""
			_click_at = null
			guard_start(Vector2(hit.x, hit.z), _ask_r, "gewählter Ort")
		return false
	if edit == "points" and ev is InputEventMouseButton:
		# 3D-3.66: only a short click sets a point - dragging still moves / turns the view; right click only on a point removes it
		if ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed:
				_click_at = ev.position
			elif _click_at != null and (ev.position as Vector2).distance_to(_click_at) < 8.0 and hit != null:
				var p: Vector3 = main.free_spot(Vector3(hit.x, 0, hit.z), 0.8, false)
				points.append(Vector2(p.x, p.z))
				mode = "points"
				_dirty = true
				_click_at = null
			else:
				_click_at = null
			return false
		if ev.button_index == MOUSE_BUTTON_RIGHT and ev.pressed and hit != null:
			var q := Vector2(hit.x, hit.z)
			for i in range(points.size()):
				if (points[i] as Vector2).distance_to(q) < 1.8:
					points.remove_at(i)
					_dirty = true
					return true
		return false
	if edit == "area":
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed and hit != null:
				_drag_from = Vector2(hit.x, hit.z)
			elif not ev.pressed and _drag_from != null:
				_drag_from = null
				mode = "area"
				edit = ""
			return true
		if ev is InputEventMouseMotion and _drag_from != null and hit != null:
			var a: Vector2 = _drag_from
			var b := Vector2(hit.x, hit.z)
			area = Rect2(Vector2(min(a.x, b.x), min(a.y, b.y)), (a - b).abs())
			_dirty = true
			return true
	return false


func _ground(p: Vector2):
	var cam: Camera3D = main.view_cam
	return main.ground_hit(cam.project_ray_origin(p), cam.project_ray_normal(p))


func _draw_route() -> void:
	for c in _mk.get_children():
		c.queue_free()
	var col := Color(0.25, 0.85, 0.45)
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.emission_enabled = true
	m.emission = col
	m.emission_energy_multiplier = 1.5
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var y := func(p: Vector2) -> float: return main.ground_y(p.x, p.y)
	if mode == "points" or area.size.x < 0.5:
		for i in range(points.size()):
			var p: Vector2 = points[i]
			var post := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.12
			cm.bottom_radius = 0.12
			cm.height = 1.2
			post.mesh = cm
			post.material_override = m
			post.layers = main.HELPER_LAYER        # 3D-3.64: MoveEye must not see the posts
			_mk.add_child(post)
			post.position = Vector3(p.x, y.call(p) + 0.6, p.y)
			var lb := Label3D.new()
			lb.text = str(i + 1)
			lb.layers = main.HELPER_LAYER
			lb.font_size = 64
			lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lb.modulate = col
			lb.outline_size = 12
			_mk.add_child(lb)
			lb.position = Vector3(p.x, y.call(p) + 1.6, p.y)
			if points.size() >= 2:
				_line(p, points[(i + 1) % points.size()], m)
	if area.size.x >= 0.5:
		var a := area.position
		var e := area.end
		for s in [[a, Vector2(e.x, a.y)], [Vector2(e.x, a.y), e], [e, Vector2(a.x, e.y)], [Vector2(a.x, e.y), a]]:
			_line(s[0], s[1], m)


func _line(a: Vector2, b: Vector2, m: Material) -> void:
	var d := b - a
	var n := maxi(1, int(d.length() / 2.0))
	for k in range(n):                                     # in pieces, so it follows the ground
		var p0 := a + d * (float(k) / n)
		var p1 := a + d * (float(k + 1) / n)
		var mid := (p0 + p1) / 2.0
		var seg := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.08, 0.04, p0.distance_to(p1))
		seg.mesh = bm
		seg.material_override = m
		seg.layers = main.HELPER_LAYER
		_mk.add_child(seg)
		seg.position = Vector3(mid.x, main.ground_y(mid.x, mid.y) + 0.06, mid.y)
		seg.rotation.y = atan2(-(p1 - p0).x, -(p1 - p0).y)


const FILE := "user://patrouille.json"


func save_route() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"scene": str(main.scene), "mode": mode, "points": points.map(func(p): return [p.x, p.y]),
				"area": [area.position.x, area.position.y, area.size.x, area.size.y], "speed": speed, "dwell": dwell, "sweep": sweep, "follow": follow}))
		f.close()


func load_route() -> void:
	"""the route of the last time - only on the same map (a route belongs to its place)"""
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) != TYPE_DICTIONARY:
		return
	speed = float(d.get("speed", speed))
	dwell = float(d.get("dwell", dwell))
	sweep = float(d.get("sweep", sweep))
	follow = bool(d.get("follow", follow))
	if str(d.get("scene", "")) != str(main.scene):
		return
	mode = str(d.get("mode", "points"))
	points = []
	for q in d.get("points", []):
		points.append(Vector2(float(q[0]), float(q[1])))
	var ar: Array = d.get("area", [0, 0, 0, 0])
	area = Rect2(float(ar[0]), float(ar[1]), float(ar[2]), float(ar[3]))
	_dirty = true


func state_dict() -> Dictionary:
	var r: Node3D = main.rig
	return {"ok": true, "active": active, "mode": mode, "points": points.map(func(p): return [snappedf(p.x, 0.1), snappedf(p.y, 0.1)]),
			"area": [area.position.x, area.position.y, area.size.x, area.size.y], "state": state, "idx": idx, "edit": edit,
			"target": [snappedf(target.x, 0.1), snappedf(target.y, 0.1)], "x": snappedf(r.position.x, 0.1), "z": snappedf(r.position.z, 0.1),
			"head": snappedf(head_yaw, 0.01), "suspect": suspect, "follow": follow,
			"guard": {} if guard.is_empty() else {"x": snappedf(guard["c"].x, 0.1), "z": snappedf(guard["c"].y, 0.1), "r": guard["r"], "name": guard["name"]},
			"blocked_points": points.filter(func(p): return main.blocked(p, 1.0)).size()}



func _dock_tick() -> void:
	"""the charging station at the place of MoveEye: a flat plate with a green lamp (a real object, the cameras see it)"""
	if _dock != null and is_instance_valid(_dock) and _dock.is_inside_tree():
		return
	_dock = Node3D.new()
	main.scene_parent.add_child(_dock)
	_dock.position = Vector3(main.home_pos.x, 0, main.home_pos.z) + Vector3(0, 0.02, 0)
	var pl := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(1.2, 0.04, 1.4)
	pl.mesh = b
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.2, 0.22, 0.25)
	pl.material_override = m
	_dock.add_child(pl)
	var lp := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.05
	s.height = 0.1
	lp.mesh = s
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(0.3, 1.0, 0.4)
	lm.emission_enabled = true
	lm.emission = Color(0.3, 1.0, 0.4)
	lp.material_override = lm
	lp.position = Vector3(0.5, 0.08, -0.6)
	_dock.add_child(lp)


func alarm_point():
	"""where MoveEye saw the person: the first box of MoveEye on the ground, else 8 m in the direction of the head"""
	var cam: Camera3D = main.cams[0]
	var vs := Vector2(main.vps[0].size)
	var b = main.mw_det.get("boxes", [])
	if typeof(b) == TYPE_ARRAY and not b.is_empty() and typeof(b[0]) == TYPE_ARRAY and b[0].size() == 4:
		var px := Vector2(float(b[0][0]) + float(b[0][2]) / 2.0, float(b[0][1]) + float(b[0][3])) * vs
		var o := cam.project_ray_origin(px)
		var d := cam.project_ray_normal(px)
		if d.y < -0.01:
			var hit := o + d * (-o.y / d.y)
			return Vector2(hit.x, hit.z)
	var f := -cam.global_transform.basis.z
	f.y = 0
	f = f.normalized() * 8.0
	return Vector2(cam.global_position.x + f.x, cam.global_position.z + f.z)


func rover_info() -> Dictionary:
	return {"active": active, "mission": mission, "batt": int(round(batt)), "state": state, "guard": guard.get("name", ""),
			"charging": not active and Vector2(main.rig.position.x - main.home_pos.x, main.rig.position.z - main.home_pos.z).length() < 1.5 and batt < 100.0,
			"mover": main.mover_on}
