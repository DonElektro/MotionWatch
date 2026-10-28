extends Node3D
## 3D-3.95: small things that fly - birds by day (a flock crosses, now and then one flies low past the camera) and bats
## at dusk and at night (fast, zig-zag, close to the light). Both are warm on the thermal picture. Classic causes of false
## alarms («Bewegung, aber keine Person»). They rest while a test or a measurement runs (comparable results).
## (The moths at the light of the head were already there: main.insects.)

var main
var on := true
var _flock: Array = []           # [{node, wings: [Node3D, Node3D], from, to, t0, dur, h, wob}]
var _next_birds := 0.0
var _bats: Array = []            # [{node, wings, c: Vector3, r, w, ph, until}]
var _next_bats := 0.0


func _process(dt: float) -> void:
	if main == null or not main.sim_active:
		return
	var t: float = main.now()
	var quiet: bool = not on or main.measuring() or main.weather in ["rain", "snow"]
	var dark: bool = main.is_dark()
	# ---- birds by day ----
	if not quiet and not dark and t > _next_birds and _flock.is_empty():
		_next_birds = t + randf_range(40.0, 140.0)
		_spawn_flock()
	# ---- bats at dusk / night (warm enough) ----
	if not quiet and dark and main.ambient > 6.0 and t > _next_bats and _bats.is_empty():
		_next_bats = t + randf_range(50.0, 160.0)
		_spawn_bats()
	_move_flock(t, dt)
	_move_bats(t)


func _bird(size: float, col: Color, temp: float) -> Dictionary:
	var n := Node3D.new()
	add_child(n)
	var bm := SphereMesh.new()
	bm.radius = size * 0.5
	bm.height = size * 0.6
	bm.radial_segments = 6
	bm.rings = 3
	main.add_mesh(n, bm, Vector3.ZERO, main.mat(col), temp, Vector3.ZERO, Vector3(0.7, 0.7, 1.6))
	var wings := []
	for s in [-1, 1]:
		var w := Node3D.new()
		n.add_child(w)
		var wm := BoxMesh.new()
		wm.size = Vector3(size * 1.3, size * 0.06, size * 0.55)
		main.add_mesh(w, wm, Vector3(size * 0.65 * s, 0, 0), main.mat(col), temp - 4.0)
		wings.append(w)
	return {"node": n, "wings": wings}


func _spawn_flock() -> void:
	var head: Vector3 = main.head.global_position
	var low := randf() < 0.25                             # one bird close past the camera
	var n := 1 if low else randi_range(4, 11)
	var d := randf_range(6.0, 14.0) if low else randf_range(12.0, 55.0)
	var ang := randf() * TAU
	var side := Vector3(cos(ang), 0, sin(ang))
	var fwd := Vector3(-side.z, 0, side.x)
	var center := head + fwd * d * (1.0 if randf() < 0.7 else -1.0)
	var h := randf_range(-0.5, 2.0) if low else randf_range(4.0, 22.0)
	var col: Color = [Color(0.1, 0.1, 0.1), Color(0.35, 0.3, 0.25), Color(0.55, 0.55, 0.58)][randi() % 3]
	var spd := randf_range(7.0, 12.0)
	var half := 70.0
	for i in range(n):
		var b := _bird(0.22 if not low else 0.28, col, 38.0)
		var off := Vector3(randf_range(-3, 3), randf_range(-1.2, 1.2), randf_range(-3, 3)) * (0.0 if low else 1.0)
		b["from"] = center - side * half + off + Vector3(0, h, 0)
		b["to"] = center + side * half + off + Vector3(0, h + randf_range(-2, 2), 0)
		b["t0"] = main.now() + randf_range(0.0, 1.5)
		b["dur"] = 2.0 * half / spd
		b["wob"] = randf() * TAU
		b["node"].position = b["from"]
		b["node"].look_at_from_position(b["from"], b["to"], Vector3.UP)
		_flock.append(b)


func _move_flock(t: float, _dt: float) -> void:
	for b in _flock.duplicate():
		var k: float = (t - float(b["t0"])) / float(b["dur"])
		if k > 1.0:
			b["node"].queue_free()
			_flock.erase(b)
			continue
		var p: Vector3 = (b["from"] as Vector3).lerp(b["to"], clampf(k, 0.0, 1.0))
		p.y += 0.6 * sin(t * 1.3 + float(b["wob"]))
		b["node"].position = p
		var fl: float = 0.9 * sin(t * 16.0 + float(b["wob"]))
		b["wings"][0].rotation.z = fl
		b["wings"][1].rotation.z = -fl


func _spawn_bats() -> void:
	var head: Vector3 = main.head.global_position
	for i in range(randi_range(1, 3)):
		var b := _bird(0.12, Color(0.12, 0.09, 0.08), 37.0)
		b["c"] = head + Vector3(randf_range(-5, 5), randf_range(0.5, 3.0), -randf_range(2.0, 9.0))
		b["r"] = randf_range(1.5, 4.5)
		b["w"] = randf_range(1.6, 2.8) * (1.0 if randf() < 0.5 else -1.0)
		b["ph"] = randf() * TAU
		b["until"] = main.now() + randf_range(20.0, 70.0)
		_bats.append(b)


func _move_bats(t: float) -> void:
	for b in _bats.duplicate():
		if t > float(b["until"]) or not main.is_dark():
			b["node"].queue_free()
			_bats.erase(b)
			continue
		var a: float = t * float(b["w"]) + float(b["ph"])
		var zig: float = sin(t * 7.0 + float(b["ph"])) * 0.6 + sin(t * 13.0) * 0.3   # bats change direction all the time
		var c: Vector3 = b["c"]
		b["node"].position = c + Vector3(cos(a) * (float(b["r"]) + zig), 0.7 * sin(a * 1.7) + 0.3 * zig, sin(a) * (float(b["r"]) + zig))
		b["node"].rotation.y = -a
		var fl: float = 1.1 * sin(t * 28.0 + float(b["ph"]))
		b["wings"][0].rotation.z = fl
		b["wings"][1].rotation.z = -fl
