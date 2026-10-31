extends Node
## Little stories that play by themselves (from 3D-3.40): a break-in attempt, a barbecue evening, coming home late, a
## parcel at the door, a fox at the bin, a family of wild boars, children playing tag, the farmer mowing - and the whole
## night in time-lapse. Every story uses the normal visitors (actor.gd) with routes, and a few things put into the scene
## for a while (grill, bin, parcel). MoveEye sees them like real ones.

var main
var lapse := false                 # «ganze Nacht im Zeitraffer» runs


func _scn() -> Node3D:
	return main.scenes.root


func _road_z() -> float:
	return float(main.scenes.data.get("road_z", -28.0))


func _part(parent: Node3D, mesh: Mesh, p: Vector3, c: Color, temp, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	return main.add_mesh(parent, mesh, p, main.mat(c), temp, rot, scl)


func _cyl(r: float, h: float, seg := 12) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = r
	c.bottom_radius = r
	c.height = h
	c.radial_segments = seg
	return c


func _later(secs: float, f: Callable) -> void:
	"""f after secs seconds (only if the scene is still the same)"""
	var sc_root := _scn()
	await get_tree().create_timer(secs).timeout
	if is_instance_valid(sc_root) and sc_root == _scn():
		f.call()


func _watch(v, check: Callable, then: Callable, max_secs := 180.0) -> void:
	"""every frame: when check(v) is true, then(v) once (stops when v is gone)"""
	var t0: float = main.now()
	var hold := {"v": v}
	main.anims.append(func(_dt, _t):
		var a = hold["v"]
		if a == null or not is_instance_valid(a) or a.done or main.now() - t0 > max_secs:
			return true
		if check.call(a):
			then.call(a)
			return true
		return false)


func _ground(p: Vector3) -> Vector3:
	p.y = main.ground_y(p.x, p.z)
	return p


# ---- a break-in attempt: sneaks up crouching, looks round, tries the door, looks in the window - flees from light ------
func burglar() -> void:
	var door: Vector3 = main.obj["door"]
	var tent: Vector3 = main.obj["pir"]
	var side := 1.0 if randf() < 0.5 else -1.0
	var start := Vector3(side * 35.0, 0, randf_range(-6.0, 8.0))
	var mid: Vector3 = main.free_spot(door.lerp(start, 0.45) + Vector3(0, 0, 2.0), 0.5, true)
	var v = main.spawn("burglar", start, mid)
	v.speed = 1.0
	v.add_torch()
	v.set_meta("shy", true)
	v.route = [[mid, 4.0, 0.6, door], [door + Vector3(0.4, 0, 0.6), 6.0, 0.0, door], [door + Vector3(-1.5, 0, 0.8), 5.0, 0.0],
			[main.free_spot(tent + Vector3(1.6, 0, 1.2), 0.5, true), 4.0, 0.7, tent], Vector3(-side * 40.0, 0, randf_range(-8.0, 6.0))]


# ---- 3D-3.74: a careful sneaker: comes from far, from cover to cover, crouching, the last metres crawling; when the light
# goes on it freezes and switches its torch off; the siren drives it away. Waits behind things like a real one.
func sneaker() -> void:
	var goal: Vector3 = main.obj["bike"] if randf() < 0.5 else main.obj["door"]
	var side := 1.0 if randf() < 0.5 else -1.0
	var start := Vector3(side * 42.0, 0, randf_range(-30.0, 10.0))
	var v = main.spawn("burglar", start, start.lerp(goal, 0.3))
	v.speed = 1.1
	v.set_meta("sneak", true)
	if main.is_dark():
		v.add_torch()
	var r := []
	for f in [0.45, 0.62, 0.76]:                          # cover to cover: stops, crouches, looks at the camera
		var p: Vector3 = main.free_spot(start.lerp(goal, f) + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3)), 0.6, true)
		r.append([p, randf_range(4.0, 12.0), 0.8 if f < 0.7 else 1.0, main.head.global_position])
	var near: Vector3 = main.free_spot(start.lerp(goal, 0.9), 0.6, true)
	r.append([near, randf_range(3.0, 7.0), 2.0, goal])     # crawling
	r.append([main.free_spot(goal + Vector3(0.7, 0, 0.6), 0.5, true), randf_range(6.0, 10.0), 1.0, goal])
	r.append(Vector3(-side * 45.0, 0, randf_range(-25.0, 5.0)))
	v.route = r


# ---- a barbecue evening: a grill, smoke, a warm glow at night, friends come one by one and stand round it --------------
func bbq() -> void:
	var c: Vector3 = main.free_spot(Vector3(randf_range(-7.0, 7.0), 0, randf_range(-13.0, -8.0)), 2.2, true)
	c = _ground(c)
	var g := Node3D.new()
	g.position = c
	_scn().add_child(g)
	for i in range(3):
		var a := i * TAU / 3.0
		_part(g, _cyl(0.02, 0.7, 6), Vector3(cos(a) * 0.22, 0.35, sin(a) * 0.22), Color(0.15, 0.15, 0.15), main.ambient + 30.0, Vector3(sin(a) * 0.15, 0, -cos(a) * 0.15))
	_part(g, _cyl(0.32, 0.18, 18), Vector3(0, 0.72, 0), Color(0.1, 0.1, 0.1), 180.0)            # the hot bowl
	_part(g, _cyl(0.3, 0.02, 18), Vector3(0, 0.82, 0), Color(0.5, 0.15, 0.05), 320.0)          # glowing coals
	main.scenes.smoke(c + Vector3(0, 1.0, 0))
	var glow := OmniLight3D.new()                                     # at night: the warm light of the coals
	glow.position = Vector3(0, 1.0, 0)
	glow.light_color = Color(1.0, 0.55, 0.25)
	glow.omni_range = 6.0
	glow.light_energy = 1.4 if main.is_dark() else 0.0
	g.add_child(glow)
	main.add_obstacle(c, 0.45)
	var n := randi_range(4, 6)
	var stay := randf_range(120.0, 170.0)
	for i in range(n):
		var a2 := i * TAU / n + randf_range(-0.25, 0.25)
		var spot: Vector3 = main.free_spot(c + Vector3(cos(a2), 0, sin(a2)) * randf_range(1.5, 2.4), 0.4, true)
		var side := 1.0 if randf() < 0.5 else -1.0
		var from := Vector3(side * 32.0, 0, randf_range(-20.0, 4.0))
		_later(i * randf_range(4.0, 9.0), func():
			var p = main.spawn("child" if randf() < 0.2 else "person", from, spot)
			p.route = [[spot, stay - i * 5.0, 0.0, c], from + Vector3(0, 0, 3.0)]
			p.next_idle = main.now() + 999.0)
	_later(stay + 25.0, func():
		if is_instance_valid(g):
			g.queue_free())


# ---- coming home late: a car stops at the road, somebody walks to the caravan, opens the door and goes in --------------
func homecoming(parcel := false) -> void:
	var door: Vector3 = main.obj["door"]
	var rz := _road_z() - 1.2
	var side := 1.0 if randf() < 0.5 else -1.0
	var stop := Vector3(clampf(door.x, -30.0, 30.0) + side * 3.0, 0, rz - side * 1.2)
	var car = main.spawn("van" if parcel else "car", Vector3(-side * 90.0, 0, stop.z), stop)
	car.route = [[stop, 14.0 if not parcel else 22.0, 0.0], Vector3(side * 90.0, 0, stop.z)]
	_watch(car, func(a): return a.position.distance_to(stop) < 1.0, func(_a):
		_later(1.5, func():
			var out := stop + Vector3(0, 0, 1.8)
			if main.fahrzeuge != null and main.fahrzeuge.fz_real and is_instance_valid(car):   # Paket «Fahrzeuge»: the door opens
				var sd: int = main.fahrzeuge.side_towards(car, door)
				main.fahrzeuge.door(car, sd, true)
				out = main.fahrzeuge.exit_point(car, sd)
				_later(2.6, func():
					if is_instance_valid(car):
						main.fahrzeuge.door(car, sd, false))
			var w = main.spawn("courier" if parcel else "person", out, door + Vector3(0, 0, 0.9))
			w.next_idle = main.now() + 999.0
			if parcel:
				w.route = [[door + Vector3(0, 0, 0.9), 3.0, 0.0, door], out]
				_watch(w, func(a): return a.position.distance_to(door + Vector3(0, 0, 0.9)) < 0.6, func(a):
					a.carry = false                                         # puts the parcel down at the door
					var bm := BoxMesh.new()
					bm.size = Vector3(0.45, 0.32, 0.35)
					var b: MeshInstance3D = _part(_scn(), bm, _ground(door + Vector3(0.5, 0.16, 0.7)), Color(0.72, 0.55, 0.35), main.ambient)
					_later(240.0, func():
						if is_instance_valid(b):
							b.queue_free()))
			else:
				if main.is_dark() and randf() < 0.6:
					w.add_torch()
				w.route = [[door + Vector3(0, 0, 0.9), 2.5, 0.0, door], door]
				_watch(w, func(a): return a.position.distance_to(door + Vector3(0, 0, 0.9)) < 0.6, func(a):
					main.set_door(true)                                     # the door sensor: opens ...
					_later(2.6, func():
						if is_instance_valid(a):
							a.done = true
							a.queue_free()                                  # ... goes in ...
						_later(1.5, func(): main.set_door(false))))))      # ... and closes


# ---- a fox at the bin: it noses about, the bin falls over -------------------------------------------------------------
func fox_trash() -> void:
	var door: Vector3 = main.obj["door"]
	var c: Vector3 = _ground(main.free_spot(door + Vector3(2.4, 0, 1.6), 0.5, false))
	var bin := Node3D.new()
	bin.position = c
	_scn().add_child(bin)
	_part(bin, _cyl(0.28, 0.8, 14), Vector3(0, 0.4, 0), Color(0.15, 0.3, 0.18), main.ambient + 2.0)
	_part(bin, _cyl(0.3, 0.06, 14), Vector3(0, 0.83, 0), Color(0.1, 0.22, 0.12), main.ambient + 1.0)
	var side := 1.0 if randf() < 0.5 else -1.0
	var start := Vector3(side * 35.0, 0, randf_range(-25.0, -10.0))
	var at := c + Vector3(0.7 * side, 0, 0.3)
	var f = main.spawn(["fox", "fox", "marten", "badger"][randi() % 4], start, at)
	f.route = [[at, 16.0, 0.0, c], start + Vector3(0, 0, 8.0)]
	_watch(f, func(a): return a.position.distance_to(at) < 0.5, func(a):
		a.idle_kind = "root"
		a.idle_until = main.now() + 15.0
		var tw := bin.create_tween()
		tw.tween_interval(4.0)
		tw.tween_property(bin, "rotation:z", -side * 1.45, 0.5))
	_later(200.0, func():
		if is_instance_valid(bin):
			bin.queue_free())


# ---- wild boars: a sow with her young ones, rooting in the meadow -----------------------------------------------------
func boar_group() -> void:
	var lead = main.spawn("boar")
	lead.speed = 1.0
	for i in range(randi_range(2, 5)):
		var o := Vector3(randf_range(-2.0, 2.0), 0, randf_range(0.8, 3.5))
		var b = main.spawn("boar", lead.position + o, lead.target + o)
		b.leader = lead
		b.follow_off = o
		b.speed = 1.6
		if i > 0:
			b.body_root.scale *= 0.55                                  # young ones (striped piglets in real life)
	lead.next_idle = main.now() + 2.0


# ---- children playing tag: they run about in front of the camera for a minute ------------------------------------------
func kids_tag() -> void:
	var c: Vector3 = main.free_spot(Vector3(randf_range(-6.0, 6.0), 0, randf_range(-14.0, -9.0)), 3.0, true)
	var side := 1.0 if randf() < 0.5 else -1.0
	for i in range(randi_range(3, 4)):
		var k = main.spawn("child", Vector3(side * 30.0, 0, c.z + randf_range(-3.0, 3.0)), c)
		k.speed = 2.6
		k.next_idle = main.now() + 999.0
		for j in range(10):
			k.route.append(main.free_spot(c + Vector3(randf_range(-6.0, 6.0), 0, randf_range(-4.0, 4.0)), 0.4, true))
		k.route.append(Vector3(-side * 35.0, 0, c.z))


# ---- the farmer mows: a tractor drives up and down in lanes ------------------------------------------------------------
func mowing() -> void:
	var best := []
	var best_n := 99999
	for z0 in [12.0, 20.0, 28.0, -40.0, -48.0, -56.0]:
		var n := 0
		for dz in [0.0, 5.0, 10.0]:
			var x := -36.0
			while x <= 36.0:
				for o in main._ob_near(Vector2(x, z0 + dz)):
					if float(main._ob_closest(o, Vector2(x, z0 + dz))[1]) < 2.2:
						n += 1
				x += 3.0
		if n < best_n:
			best_n = n
			best = [z0, z0 + 5.0, z0 + 10.0]
	var side := 1.0 if randf() < 0.5 else -1.0
	var t = main.spawn("tractor", Vector3(-side * 60.0, 0, best[0]), Vector3(-side * 36.0, 0, best[0]))
	t.speed = 3.0
	var s := side
	for z in best:
		t.route.append(Vector3(s * 36.0, 0, z))
		if z != best[2]:
			t.route.append(Vector3(s * 38.0, 0, z + 2.5))
		s = -s
	t.route.append(Vector3(s * 70.0, 0, best[2]))


# ---- the whole night in time-lapse: 20:00 to 6:00 at 60 × (about ten minutes), visitors at their own times ------------
func night_lapse() -> void:
	main.set_hour(20.0)
	main._set_speed(60.0)
	main.auto_visitors = true
	main.daily_life = true
	main.next_auto = main.now() + 2.0
	lapse = true
	main._sync_ui()
	main.anims.append(func(_dt, _t):
		if not lapse:
			return true
		var h: float = main.hour()
		if h >= 6.0 and h < 12.0:
			main._set_speed(1.0)
			main.set_hour(6.0)
			lapse = false
			main._sync_ui()
			return true
		return false)
