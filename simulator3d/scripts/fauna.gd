extends Node3D
## 3D-3.94: small things that fly - birds by day (a flock crosses, now and then one flies low past the camera) and bats
## at dusk and at night (fast, zig-zag, close to the light). Both are warm on the thermal picture. Classic causes of false
## alarms («Bewegung, aber keine Person»). They rest while a test or a measurement runs (comparable results).
## (The moths at the light of the head were already there: main.insects.)
## Paket «Tiere» (31.10.2026): birds on the ground - crows (walk, peck), magpies (hop, long tail), gulls at the water (stand,
## swim, glide in circles). They fly up when somebody comes closer than their flight distance (crow ~15 m, magpie ~10 m,
## gull ~12 m), at the siren, or by themselves after a while; crows often land again a bit further on. By day only.
## Sizes: Rabenkrähe 45–47 cm, Elster 44–46 cm (half of it the tail), Möwe 40–55 cm (Lachmöwe / Mittelmeermöwe,
## Schweizerische Vogelwarte). Heat: waerme.gd (if there, «bird»), else feathers k = 0.25 of core 41 °C [McCafferty 2007].

var main
var on := true
var _flock: Array = []           # [{node, wings: [Node3D, Node3D], from, to, t0, dur, h, wob}]
var _next_birds := 0.0
var _bats: Array = []            # [{node, wings, c: Vector3, r, w, ph, until}]
var _next_bats := 0.0
const Quality = preload("res://scripts/quality.gd")
var _ground: Array = []          # birds on the ground: {node, head, tail, wings, kind, st, t, ...}
var _next_ground := 0.0
var _gscan := 0.0
# kind: [length m, body colour, wing colour, flight distance m, hops (true) or walks]
const GROUND := {"crows": [0.46, Color(0.06, 0.06, 0.07), Color(0.05, 0.05, 0.06), 15.0, false],
		"magpies": [0.45, Color(0.05, 0.06, 0.09), Color(0.06, 0.08, 0.14), 10.0, true],
		"gulls": [0.45, Color(0.93, 0.93, 0.92), Color(0.62, 0.65, 0.7), 12.0, false]}


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
	# ---- birds on the ground by day (Paket «Tiere») ----
	if not quiet and not dark and t > _next_ground and _ground.is_empty():
		if _next_ground > 0.0 and randf() < 0.6:
			var water: bool = main.scene == "seeufer"
			ground_flock("gulls" if water and randf() < 0.7 else ("magpies" if randf() < 0.35 else "crows"), null)
		_next_ground = t + randf_range(60.0, 180.0)
	_ground_tick(t, dt, dark)


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
	if main.head == null or not main.head.is_inside_tree():
		return                                    # Startfix: die Welt steht noch nicht (main wartet auf die Update-Suche)
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


# ---- birds on the ground (Paket «Tiere») ------------------------------------------------------------------------------
func _warm(part: String) -> float:
	"""surface temperature of a bird: the heat table waerme.gd (3D-4.45: on main, no own values any more)"""
	return float(preload("res://scripts/waerme.gd").animal("bird", main.ambient, part, 0.0))


func _ground_bird(kind: String) -> Dictionary:
	var g: Array = GROUND[kind]
	var L: float = float(g[0]) * randf_range(0.92, 1.08)
	var col: Color = g[1]
	var n := Node3D.new()
	add_child(n)
	var body := Node3D.new()                                        # the body tips forward when it pecks
	body.position = Vector3(0, L * 0.2, 0)
	n.add_child(body)
	var tb := _warm("body")
	var bl := L * (0.42 if kind != "magpies" else 0.32)
	main.add_mesh(body, _ell(bl * 0.32), Vector3.ZERO, main.mat(col), tb, Vector3.ZERO, Vector3(0.75, 0.75, 1.6))
	if kind == "magpies":                                           # white belly and shoulders
		main.add_mesh(body, _ell(bl * 0.24), Vector3(0, -bl * 0.08, 0.0), main.mat(Color(0.95, 0.95, 0.95)), tb, Vector3.ZERO, Vector3(0.85, 0.7, 1.2))
		for sd in [-1, 1]:
			main.add_mesh(body, _ell(bl * 0.12), Vector3(bl * 0.2 * sd, bl * 0.06, 0.0), main.mat(Color(0.95, 0.95, 0.95)), tb, Vector3.ZERO, Vector3(0.4, 0.6, 1.4))
	if kind == "gulls":                                             # grey back
		main.add_mesh(body, _ell(bl * 0.3), Vector3(0, bl * 0.06, bl * 0.05), main.mat(g[2]), tb, Vector3.ZERO, Vector3(0.8, 0.5, 1.6))
	var head := Node3D.new()
	head.position = Vector3(0, bl * 0.2, -bl * 0.5)
	body.add_child(head)
	main.add_mesh(head, _ell(bl * 0.17), Vector3.ZERO, main.mat(col), _warm("head"))
	var beak := CylinderMesh.new()
	beak.top_radius = 0.0
	beak.bottom_radius = bl * 0.05
	beak.height = bl * (0.3 if kind == "crows" else 0.24)
	beak.radial_segments = 5
	main.add_mesh(head, beak, Vector3(0, -bl * 0.02, -bl * 0.25), main.mat(Color(0.9, 0.75, 0.1) if kind == "gulls" else Color(0.05, 0.05, 0.05)), _warm("legs"), Vector3(-PI / 2, 0, 0))
	var tail := Node3D.new()
	tail.position = Vector3(0, bl * 0.05, bl * 0.45)
	body.add_child(tail)
	var tl: float = L * (0.5 if kind == "magpies" else 0.22)
	var tm := BoxMesh.new()
	tm.size = Vector3(bl * 0.22, 0.01, tl)
	main.add_mesh(tail, tm, Vector3(0, 0, tl * 0.5), main.mat(g[2] if kind != "gulls" else Color(0.95, 0.95, 0.95)), _warm("legs") + 1.0, Vector3(-0.25, 0, 0))
	for sd in [-1, 1]:                                              # legs
		var lm := CylinderMesh.new()
		lm.top_radius = 0.006
		lm.bottom_radius = 0.005
		lm.height = L * 0.2
		lm.radial_segments = 4
		main.add_mesh(n, lm, Vector3(bl * 0.08 * sd, L * 0.1, 0.0), main.mat(Color(0.75, 0.6, 0.35) if kind == "gulls" else Color(0.05, 0.05, 0.05)), _warm("legs"))
	var wings := []
	for sd in [-1, 1]:                                              # wings: folded = hidden, open in the air
		var w := Node3D.new()
		w.position = Vector3(bl * 0.12 * sd, bl * 0.08, 0)
		body.add_child(w)
		var wm := BoxMesh.new()
		wm.size = Vector3(L * 1.0, 0.012, bl * 0.55)
		main.add_mesh(w, wm, Vector3(L * 0.5 * sd, 0, 0), main.mat(g[2]), tb - 2.0)
		if kind == "gulls":                                         # black wing tips
			var tip := BoxMesh.new()
			tip.size = Vector3(L * 0.25, 0.014, bl * 0.4)
			main.add_mesh(w, tip, Vector3(L * 0.9 * sd, 0, 0.02), main.mat(Color(0.05, 0.05, 0.05)), tb - 4.0)
		w.visible = false
		wings.append(w)
	return {"node": n, "body": body, "head": head, "tail": tail, "wings": wings, "kind": kind, "L": L, "st": "ground",
			"t": main.now() + randf_range(0.3, 1.5), "until": main.now() + randf_range(60.0, 180.0), "yaw": randf() * TAU,
			"hop": 0.0, "lands": 0}


func _ell(r: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = r
	m.height = r * 2.0
	m.radial_segments = 8
	m.rings = 4
	return m


func _gy(p: Vector3) -> float:
	return main.ground_y(p.x, p.z) if main.terrain else 0.0


func ground_flock(kind: String, at) -> Node3D:
	"""a few birds on the ground in the picture of the head camera (gulls: at the water if the scene has some)"""
	if not GROUND.has(kind):
		return null
	var n: int = {"crows": randi_range(2, 6), "magpies": randi_range(1, 3), "gulls": randi_range(3, 8)}[kind]
	n = maxi(1, Quality.n(n)) if Quality.lite() else n
	var c: Vector3
	if at != null:
		c = at
	else:
		var hp: Vector3 = main.head.global_position
		var f: Vector3 = -main.cams[0].global_transform.basis.z
		f.y = 0.0
		f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
		c = Vector3(hp.x, 0, hp.z) + f.rotated(Vector3.UP, randf_range(-0.4, 0.4)) * randf_range(7.0, 16.0)
	var water: bool = kind == "gulls" and main.scene == "seeufer"     # scenes.gd _seeufer: water from z = -25 on
	var first: Node3D = null
	for i in range(n):
		var b := _ground_bird(kind)
		var p := c + Vector3(randf_range(-2.5, 2.5), 0, randf_range(-2.0, 2.0)) * (1.0 + n * 0.12)
		if water:
			p = Vector3(randf_range(-14.0, 14.0), 0, -24.6 + randf_range(-0.5, 0.6))   # on the shore
			if i % 3 == 1:
				p.z = randf_range(-30.0, -40.0)                    # swimming
				b["st"] = "swim"
			elif i % 4 == 3 and not Quality.lite():
				b["st"] = "glide"                                   # sails in circles over the water
				b["c"] = Vector3(randf_range(-10.0, 10.0), randf_range(5.0, 11.0), randf_range(-32.0, -45.0))
				b["r"] = randf_range(8.0, 16.0)
				b["w"] = randf_range(0.25, 0.4) * (1.0 if randf() < 0.5 else -1.0)
				for w in b["wings"]:
					w.visible = true
		p = main.free_spot(p, 0.15, false) if b["st"] == "ground" else p
		p.y = _gy(p) if b["st"] == "ground" else 0.0
		b["node"].position = p
		b["node"].rotation.y = b["yaw"]
		_ground.append(b)
		if first == null:
			first = b["node"]
	return first


func ground_info() -> Array:
	var out := []
	for b in _ground:
		var p: Vector3 = b["node"].position
		out.append({"kind": b["kind"], "st": b["st"], "x": snappedf(p.x, 0.1), "y": snappedf(p.y, 0.1), "z": snappedf(p.z, 0.1)})
	return out


func _threat_near(p: Vector3, r: float) -> bool:
	for v in main.visitors.get_children():
		if v.has_method("is_animal") and not v.done and not v.preview and (v.kind == "person" or v.kind in ["dog", "cat", "fox"] or (v.kind == "car" and v.cur_speed > 1.0)):
			if Vector2(v.global_position.x - p.x, v.global_position.z - p.z).length() < r * (0.5 if v.kind == "car" else 1.0):
				return true
	if main.tiere != null and main.tiere._test_threat != null:
		var tp: Vector3 = main.tiere._test_threat[0]
		if Vector2(tp.x - p.x, tp.z - p.z).length() < r:
			return true
	return false


func _take_off(b: Dictionary, t: float) -> void:
	b["st"] = "fly"
	b["t"] = t
	var p: Vector3 = b["node"].position
	var ang := randf() * TAU
	var away := Vector3(cos(ang), 0, sin(ang))
	for v in main.visitors.get_children():                     # away from the nearest one
		if v.has_method("is_animal") and v.kind in ["person", "dog", "cat", "fox"] and v.global_position.distance_to(p) < 25.0:
			away = (p - v.global_position)
			away.y = 0.0
			away = away.normalized().rotated(Vector3.UP, randf_range(-0.6, 0.6))
			break
	var land: bool = b["kind"] == "crows" and int(b["lands"]) < 2 and randf() < 0.45   # crows often land again a bit further on
	b["from"] = p
	b["to"] = p + away * (randf_range(14.0, 24.0) if land else 70.0) + Vector3(0, 0 if land else randf_range(10.0, 18.0), 0)
	b["land"] = land
	b["dur"] = (b["to"] - p).length() / randf_range(7.0, 10.0)
	for w in b["wings"]:
		w.visible = true


func _ground_tick(t: float, dt: float, dark: bool) -> void:
	if _ground.is_empty():
		return
	if main.measuring():                                           # a test starts: no birds on the ground (comparable)
		for b0 in _ground:
			if is_instance_valid(b0["node"]):
				b0["node"].queue_free()
		_ground.clear()
		return
	_gscan -= dt
	var scan := _gscan <= 0.0
	if scan:
		_gscan = 0.3
	var siren: bool = str(main.mw.get("sound", "")) != ""
	for b in _ground.duplicate():
		var n: Node3D = b["node"]
		if not is_instance_valid(n):
			_ground.erase(b)
			continue
		var g: Array = GROUND[b["kind"]]
		match str(b["st"]):
			"ground", "swim":
				if scan and (siren or dark or t > float(b["until"]) or (b["st"] == "ground" and _threat_near(n.position, float(g[3])))):
					_take_off(b, t + randf_range(0.0, 0.35))          # not all at the same moment
					continue
				if b["st"] == "swim":
					n.position.y = 0.04 + 0.015 * sin(t * 1.7 + float(b["yaw"]))
					n.rotation.y += dt * 0.05 * sin(t * 0.3 + float(b["yaw"]))
					continue
				if t > float(b["t"]):                                  # next little thing to do
					b["t"] = t + randf_range(0.4, 1.6)
					var r := randf()
					b["do"] = "peck" if r < 0.45 else ("step" if r < 0.85 else "look")
					b["t0"] = t
					if b["do"] == "step":
						b["yaw"] = float(b["yaw"]) + randf_range(-0.9, 0.9)
					if b["do"] == "look":
						b["look"] = randf_range(-1.2, 1.2)
				var k: float = (t - float(b.get("t0", t))) / 0.35
				match str(b.get("do", "")):
					"peck":
						b["body"].rotation.x = -0.55 * maxf(0.0, sin(minf(k, 3.0) * PI)) if k < 3.0 else lerpf(b["body"].rotation.x, 0.0, 0.2)
					"step":
						var fw := Vector3(-sin(float(b["yaw"])), 0, -cos(float(b["yaw"])))
						if bool(g[4]):                                  # magpie: hops (two feet, a small jump)
							if k < 1.0:
								n.position += fw * dt * 0.8
								b["hop"] = sin(k * PI) * 0.06
						else:                                           # crow / gull: walks with nodding head
							if k < 2.5:
								n.position += fw * dt * 0.45
								b["head"].position.z = -float(b["L"]) * 0.17 + 0.015 * sin(k * TAU)
						n.rotation.y = lerp_angle(n.rotation.y, float(b["yaw"]), 0.3)
						b["body"].rotation.x = lerpf(b["body"].rotation.x, 0.0, 0.2)
					"look":
						b["head"].rotation.y = lerpf(b["head"].rotation.y, float(b["look"]), 0.15)
				n.position.y = _gy(n.position) + float(b["hop"])
				b["hop"] = move_toward(float(b["hop"]), 0.0, dt * 0.5)
			"fly":
				if t < float(b["t"]):
					continue
				var kk: float = (t - float(b["t"])) / float(b["dur"])
				if kk >= 1.0:
					if bool(b["land"]):
						b["st"] = "ground"
						b["lands"] = int(b["lands"]) + 1
						b["t"] = t + 0.5
						b["until"] = t + randf_range(30.0, 90.0)
						n.position = main.free_spot(Vector3(n.position.x, 0, n.position.z), 0.15, false)
						n.position.y = _gy(n.position)
						for w in b["wings"]:
							w.visible = false
						b["body"].rotation.x = 0.0
					else:
						n.queue_free()
						_ground.erase(b)
					continue
				var from: Vector3 = b["from"]
				var to: Vector3 = b["to"]
				var e: float = kk if not bool(b["land"]) else kk
				var p: Vector3 = from.lerp(to, e)
				p.y = from.y + (to.y - from.y) * sqrt(e) + (sin(e * PI) * 3.5 if bool(b["land"]) else 0.0) + 0.8 * minf(1.0, kk * 4.0)
				var prev: Vector3 = n.position
				n.position = p
				if p.distance_to(prev) > 0.001:
					n.rotation.y = atan2(-(p.x - prev.x), -(p.z - prev.z))
				b["body"].rotation.x = 0.25
				var fl: float = (1.0 if kk < 0.3 else 0.75) * sin(t * (18.0 if b["kind"] != "gulls" else 11.0) + float(b["yaw"]))
				b["wings"][0].rotation.z = fl
				b["wings"][1].rotation.z = -fl
			"glide":                                                    # gull: sails, a slow flap now and then
				if scan and (siren or dark or t > float(b["until"]) + 60.0):
					b["st"] = "fly"
					b["t"] = t
					b["from"] = n.position
					b["to"] = n.position + Vector3(randf_range(-60, 60), 8.0, -60.0)
					b["land"] = false
					b["dur"] = 9.0
					continue
				var a: float = t * float(b["w"]) + float(b["yaw"])
				var c: Vector3 = b["c"]
				var p2 := c + Vector3(cos(a) * float(b["r"]), 0.8 * sin(a * 0.7), sin(a) * float(b["r"]))
				var prev2: Vector3 = n.position
				n.position = p2
				if p2.distance_to(prev2) > 0.001:
					n.rotation.y = atan2(-(p2.x - prev2.x), -(p2.z - prev2.z))
				n.rotation.z = -0.35 * signf(float(b["w"]))
				var fl2: float = 0.12 * sin(t * 1.3) + (0.7 * sin(t * 10.0) if fmod(t + float(b["yaw"]), 9.0) < 1.2 else 0.0)
				b["wings"][0].rotation.z = fl2
				b["wings"][1].rotation.z = -fl2
