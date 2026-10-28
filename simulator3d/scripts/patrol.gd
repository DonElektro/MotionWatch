extends Node3D
## 3D-3.61: «Patrouille» - the mover drives Motion Watch round a fixed route (points set with the mouse) or to random
## points in an area (dragged open with the mouse). Motion Watch watches the whole time: while driving the head swings to
## and fro, at every point the mover stops and the head looks all round. Optional: the head turns to something
## suspicious (a box of Motion Watch, or a player the simulator guard suspects) and the mover drives slower.
## The game «Patrouille» (game.gd): the players sneak to the goal while the patrol drives; caught by the real detection
## of Motion Watch or by the simulator guard (setting).

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
var _saved_max := 0.8
var _mk: Node3D
var _dirty := true
var _stuck_t := 0.0
var _stuck_pos := Vector2.ZERO
var _back_until := 0.0                 # stuck at an object: back a little and turn, then on
var _back_turn := 1.0
var _tries := 0


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
			random_route()                               # nothing set yet: a route round Motion Watch
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


func random_route() -> void:
	"""6 points in a ring round the place of Motion Watch, never inside an object"""
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


func _next() -> void:
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
	if not active:
		return Vector2.ZERO
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
	if not active:
		return
	main.mover_max = speed
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
	suspect = false
	if follow:
		var s = _suspect_angle()
		if s != null:
			suspect = true
			want_h = float(s)
	head_yaw = want_h


func _suspect_angle():
	"""where something suspicious is, relative to the mover: a box of Motion Watch, else a player the guard suspects"""
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
	if edit == "points" and ev is InputEventMouseButton and ev.pressed and hit != null:
		var q := Vector2(hit.x, hit.z)
		if ev.button_index == MOUSE_BUTTON_LEFT:
			var p: Vector3 = main.free_spot(Vector3(q.x, 0, q.y), 0.8, false)
			points.append(Vector2(p.x, p.z))
			mode = "points"
		elif ev.button_index == MOUSE_BUTTON_RIGHT:
			for i in range(points.size()):
				if (points[i] as Vector2).distance_to(q) < 1.8:
					points.remove_at(i)
					break
		_dirty = true
		return true
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
			_mk.add_child(post)
			post.position = Vector3(p.x, y.call(p) + 0.6, p.y)
			var lb := Label3D.new()
			lb.text = str(i + 1)
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
			"head": snappedf(head_yaw, 0.01), "suspect": suspect, "follow": follow}
