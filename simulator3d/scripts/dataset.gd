extends Node
## Trainingsbilder (3D-3.44): the simulator makes pictures of the head camera with a person or an animal in it - by day, at
## dusk, at night with infrared, in rain and fog, near and far - and knows for each picture where the visitor really is
## (the box in the picture). Motion Watch fetches them (/dataset.json, /dataset/<i>.jpg) and checks how well its AI finds
## them; it can also pack them as training pictures. CONTROL action "dataset": {"op": "start", "n": 40} / "get" / "stop".

const CONDS := [["Tag", 11.0, "clear"], ["Abend", 19.6, "clear"], ["Nacht (Infrarot)", 23.5, "clear"], ["Regen", 14.0, "rain"],
		["Nebel", 9.0, "fog"], ["Nacht + Regen", 1.0, "rain"]]
const KINDS := ["person", "person", "person", "fox", "deer", "dog", "cat", "boar"]

var main
var busy := false
var total := 0
var items := []               # {"i", "kind", "cond", "dist", "box": [x, y, w, h] (0..1), "jpg": PackedByteArray}
var msg := ""
var _stop := false
var servo = null              # Vector2 pan / tilt degrees while making the pictures


var only := []                # which conditions (index into CONDS); empty = all


func start(n: int, conds := []) -> Dictionary:
	if busy:
		return state()
	n = clampi(n, 2, 80)
	only = conds.filter(func(c): return int(c) >= 0 and int(c) < CONDS.size()).map(func(c): return int(c))
	_run(n)
	return state()


func state() -> Dictionary:
	var by := {}
	for it in items:
		by[it["cond"]] = int(by.get(it["cond"], 0)) + 1
	return {"ok": true, "busy": busy, "done": items.size(), "total": total, "msg": msg, "conds": by}


func list() -> Array:
	var out := []
	for it in items:
		out.append({"i": it["i"], "kind": it["kind"], "cond": it["cond"], "dist": it["dist"], "box": it["box"], "w": it["w"], "h": it["h"]})
	return out


func jpg(i: int) -> PackedByteArray:
	for it in items:
		if int(it["i"]) == i:
			return it["jpg"]
	return PackedByteArray()


func _run(n: int) -> void:
	busy = true
	_stop = false
	total = n
	items = []
	msg = "bereitet vor …"
	# keep what the user had
	var keep := {"hour": main.hour(), "weather": main.weather, "auto": main.auto_visitors}
	main.auto_visitors = false
	for v in main.visitors.get_children():
		v.visible = false
	var k := 0
	while k < n and not _stop:
		var cond: Array = CONDS[only[k % only.size()]] if not only.is_empty() else CONDS[k % CONDS.size()]
		main.set_hour(float(cond[1]))
		main.weather = str(cond[2])
		var kind: String = KINDS[randi() % KINDS.size()]
		var dist := randf_range(4.0, 18.0) if kind == "person" else randf_range(3.0, 11.0)
		var side := randf_range(-22.0, 22.0)
		# where the head looks: the visitor somewhere in the picture, not always in the middle
		var yaw0: float = main.rig.rotation.y
		var a := yaw0 + deg_to_rad(side)
		var p: Vector3 = main.rig.global_position + Vector3(-sin(a) * dist, 0, -cos(a) * dist)
		p = main.free_spot(p, 0.5, true) if main.has_method("free_spot") else p
		p.y = main.ground_y(p.x, p.z)
		var aim := side + randf_range(-14.0, 14.0)
		servo = Vector2(-aim, randf_range(-6.0, 4.0))
		var far := p + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * 40.0
		var v = main.spawn(kind, p, far)                 # a far goal: it must not reach it and leave (it would free itself)
		v.speed = 0.02
		msg = "Bild %d von %d · %s · %s" % [k + 1, n, cond[0], kind]
		# let the head turn, the light settle and the camera expose
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 1600:
			await main.get_tree().process_frame
		if not is_instance_valid(v):
			continue
		# the normal picture loop takes the pictures (never a second capture at the same time - that crashed the graphics);
		# three new ones: the exposure settles like on the real camera
		var f0: int = int(main.frame_no[0])
		var t1 := Time.get_ticks_msec()
		while int(main.frame_no[0]) < f0 + 3 and Time.get_ticks_msec() - t1 < 8000:
			main.snap_want[0] = main.now()
			await main.get_tree().process_frame
		while main.capturing:
			await main.get_tree().process_frame
		if not is_instance_valid(v):
			continue
		var j: PackedByteArray = main.jpgs[0]
		var box := _box(v)
		var shown: bool = not box.is_empty() and main.line_free(main.cams[0].global_position, v.global_position + Vector3(0, 0.5, 0))
		if shown and j.size() > 0:
			var sz: Vector2i = main.vps[0].size
			items.append({"i": items.size(), "kind": kind, "cond": cond[0], "dist": snappedf(dist, 0.1), "box": box, "jpg": j, "w": sz.x, "h": sz.y})
			k += 1
		v.queue_free()
		await main.get_tree().process_frame
	servo = null
	main.set_hour(float(keep["hour"]))
	main.weather = str(keep["weather"])
	main.auto_visitors = bool(keep["auto"])
	for v2 in main.visitors.get_children():
		v2.visible = true
	msg = "fertig: %d Bilder" % items.size()
	busy = false


func stop() -> void:
	_stop = true


func _box(v: Node3D) -> Array:
	"""the box of the visitor in the picture of the head camera (0..1), from the corners of its meshes"""
	var cam: Camera3D = main.cams[0]
	var sz: Vector2 = Vector2(main.vps[0].size)
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	var any := false
	for m in v.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		if not mi.visible or mi.mesh == null:
			continue
		var ab: AABB = mi.get_aabb()
		for c in 8:
			var w: Vector3 = mi.global_transform * ab.get_endpoint(c)
			if cam.is_position_behind(w):
				continue
			var q := cam.unproject_position(w)
			lo = lo.min(q)
			hi = hi.max(q)
			any = true
	if not any:
		return []
	lo = lo.clamp(Vector2.ZERO, sz)
	hi = hi.clamp(Vector2.ZERO, sz)
	if hi.x - lo.x < 4.0 or hi.y - lo.y < 4.0:
		return []
	return [snappedf(lo.x / sz.x, 0.001), snappedf(lo.y / sz.y, 0.001), snappedf((hi.x - lo.x) / sz.x, 0.001), snappedf((hi.y - lo.y) / sz.y, 0.001)]
