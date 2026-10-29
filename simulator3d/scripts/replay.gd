extends Node3D
## Alarm-Rückblick in 3D (3D-3.44): MoveEye sends what its camera saw around an alarm - where its head looked and where in
## the picture each person / animal was, about twice a second. Here that is turned back into the world: a ray from the head
## through the spot in the picture, the distance from the height of the box (a person ~1.7 m, an animal ~0.6 m). A see-through
## figure walks the way again, with its trail; the head turns like it did; a strip at the top tells the time and what it was.
## CONTROL action "replay": {"track": {"title", "samples": [{"t", "pan", "tilt", "objs": [{"k", "x", "y", "h"}]}]}} / {"stop": true}

const UI = preload("res://scripts/ui_style.gd")

var main
var on := false
var samples := []
var title := ""
var t0 := 0.0                 # real time the replay started
var dur := 0.0
var speed := 1.0
var ghosts := {}              # kind index -> MeshInstance3D
var trail: MeshInstance3D
var trail_pts := []
var strip: Label
var servo := Vector2.ZERO     # pan / tilt in degrees while replaying (main takes this instead of MoveEye)
var _cam_t := 0.0
var last_track := {}          # Prüfstand 2: the last track played - can be kept as a bench case (pruefstand.gd)


func setup(layer: CanvasLayer) -> void:
	strip = Label.new()
	strip.add_theme_font_size_override("font_size", 20)
	strip.add_theme_color_override("font_color", Color.WHITE)
	strip.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	strip.add_theme_constant_override("outline_size", 8)
	strip.position = Vector2(340, 58)
	strip.visible = false
	layer.add_child(strip)


func start(track: Dictionary) -> Dictionary:
	stop()
	samples = []
	for s in track.get("samples", []):
		if typeof(s) == TYPE_DICTIONARY:
			samples.append(s)
	if samples.size() < 2:
		return {"ok": false, "error": "too few samples"}
	samples.sort_custom(func(a, b): return float(a.get("t", 0)) < float(b.get("t", 0)))
	title = str(track.get("title", "Alarm"))
	last_track = {"title": title, "samples": samples.duplicate(true)}
	var ta := float(samples[0].get("t", 0.0))
	for s in samples:
		s["_rt"] = float(s.get("t", 0.0)) - ta
		s["_pos"] = []
		for o in s.get("objs", []):
			s["_pos"].append([str(o.get("k", "person")), _world(s, o)])
	dur = float(samples[-1]["_rt"])
	speed = clampf(float(track.get("speed", 1.0)), 0.25, 8.0)
	t0 = main.now()
	on = true
	strip.visible = true
	trail_pts = []
	trail = MeshInstance3D.new()
	trail.mesh = ImmediateMesh.new()
	var tm := StandardMaterial3D.new()
	tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tm.albedo_color = Color(1.0, 0.55, 0.15)
	trail.material_override = tm
	add_child(trail)
	main.set_view(0)
	main.follow = false
	main.visitors.visible = false                   # only the replay is seen (the visitors go on, invisible)
	return {"ok": true, "samples": samples.size(), "seconds": snappedf(dur, 0.1)}


func stop() -> void:
	if on:
		main.visitors.visible = true
	on = false
	for g in ghosts.values():
		g.queue_free()
	ghosts.clear()
	if trail != null:
		trail.queue_free()
		trail = null
	if strip != null:
		strip.visible = false


func _world(s: Dictionary, o: Dictionary) -> Vector3:
	"""the spot of a box in the picture -> a point on the ground (head camera: 66° × 41°)"""
	var fov_h := deg_to_rad(float(main.CAM_FOV[0]))
	var fov_v := deg_to_rad(41.0)
	var x := float(o.get("x", 0.5))
	var y := float(o.get("y", 0.5))
	var h := clampf(float(o.get("h", 0.2)), 0.02, 1.0)
	var k := str(o.get("k", "person"))
	var real_h := 1.7 if k == "person" else (1.0 if k in ["deer", "horse", "cow"] else 0.6)
	var dist := clampf(real_h / (2.0 * tan(fov_v / 2.0) * h), 1.0, 60.0)
	var yaw: float = main.rig.rotation.y - deg_to_rad(float(s.get("pan", 0.0))) - (x - 0.5) * fov_h
	var pitch: float = deg_to_rad(float(s.get("tilt", 0.0)) - 6.0) - (y - 0.5) * fov_v
	var dir := Vector3(-sin(yaw) * cos(pitch), sin(pitch), -cos(yaw) * cos(pitch))
	var head: Vector3 = main.rig.global_position + Vector3(0, main.HEAD_H, 0)
	var p := head + dir * dist
	p.y = main.ground_y(p.x, p.z)
	return p


func _ghost(i: int, kind: String) -> MeshInstance3D:
	if ghosts.has(i):
		return ghosts[i]
	var m := MeshInstance3D.new()
	var person := kind == "person"
	var cap := CapsuleMesh.new()
	cap.radius = 0.25 if person else 0.22
	cap.height = 1.7 if person else 0.6
	m.mesh = cap
	var mt := StandardMaterial3D.new()
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.albedo_color = Color(1.0, 0.45, 0.1, 0.55) if person else Color(0.3, 0.8, 1.0, 0.55)
	mt.emission_enabled = true
	mt.emission = mt.albedo_color
	mt.emission_energy_multiplier = 0.6
	m.material_override = mt
	var lb := Label3D.new()
	lb.text = {"person": "Person", "dog": "Hund", "cat": "Katze", "bird": "Vogel", "horse": "Pferd", "sheep": "Schaf", "cow": "Kuh",
			"bear": "Bär"}.get(kind, kind)
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.position = Vector3(0, cap.height / 2.0 + 0.45, 0)
	lb.font_size = 48
	lb.outline_size = 10
	m.add_child(lb)
	add_child(m)
	ghosts[i] = m
	return m


func _process(dt: float) -> void:
	if not on:
		return
	var rt: float = (main.now() - t0) * speed
	if rt > dur + 3.0:
		stop()
		return
	# the two samples around now
	var a = samples[0]
	var b = samples[-1]
	for i in range(samples.size() - 1):
		if float(samples[i]["_rt"]) <= rt and float(samples[i + 1]["_rt"]) >= rt:
			a = samples[i]
			b = samples[i + 1]
			break
	var span: float = max(0.001, float(b["_rt"]) - float(a["_rt"]))
	var f := clampf((rt - float(a["_rt"])) / span, 0.0, 1.0)
	servo = Vector2(lerpf(float(a.get("pan", 0.0)), float(b.get("pan", 0.0)), f), lerpf(float(a.get("tilt", 0.0)), float(b.get("tilt", 0.0)), f))
	var focus := Vector3.ZERO
	var nf := 0
	var seen := {}
	for i in range(a["_pos"].size()):
		var kind: String = a["_pos"][i][0]
		var pa: Vector3 = a["_pos"][i][1]
		var pb: Vector3 = b["_pos"][i][1] if i < b["_pos"].size() else pa
		var p := pa.lerp(pb, f)
		var g := _ghost(i, kind)
		g.visible = true
		var hh: float = (g.mesh as CapsuleMesh).height / 2.0
		g.global_position = p + Vector3(0, hh, 0)
		seen[i] = true
		focus += p
		nf += 1
		if i == 0 and (trail_pts.is_empty() or (trail_pts[-1] as Vector3).distance_to(p) > 0.25):
			trail_pts.append(p + Vector3(0, 0.05, 0))
	for i in ghosts:
		if not seen.has(i):
			ghosts[i].visible = false
	if trail != null and trail_pts.size() >= 2:
		var im: ImmediateMesh = trail.mesh
		im.clear_surfaces()
		im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
		for q in trail_pts:
			im.surface_add_vertex(q)
		im.surface_end()
	strip.text = "Alarm-Rückblick: %s  ·  %d / %d s%s  ·  Esc beendet" % [title, int(rt), int(dur), "  ·  %dx schneller" % int(speed) if speed > 1.0 else ""]
	# the camera: from above and behind MoveEye, looking at what happens
	if nf > 0:
		focus /= nf
	else:
		focus = main.rig.global_position + Vector3(-sin(main.rig.rotation.y - deg_to_rad(servo.x)), 0, -cos(main.rig.rotation.y - deg_to_rad(servo.x))) * 8.0
	var head: Vector3 = main.rig.global_position
	var back := (head - focus)
	back.y = 0
	back = back.normalized() if back.length() > 0.1 else Vector3(0, 0, 1)
	var pos := head + back * 7.0 + Vector3(0, 6.0, 0)
	var want := Transform3D(Basis(), pos).looking_at(focus.lerp(head, 0.3) + Vector3(0, 0.6, 0), Vector3.UP)
	main.view_cam.global_transform = main.view_cam.global_transform.interpolate_with(want, 1.0 - exp(-dt * 2.0))
