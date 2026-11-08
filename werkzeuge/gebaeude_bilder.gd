extends SceneTree
## Vorher/Nachher-Bilder und Messwerte für «Ort von der Karte» mit den 3D-Gebäuden von swisstopo (3.65.0),
## ohne Fenster unter Xvfb aus dem Quelltext (wie wege_bilder.gd):
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/gebaeude_bilder.gd" \
##       -- --no-update --ort 47.34753,8.16017,Seon --b3d on|off [--qual normal|lite] --ansichten <ansichten.json> --aus <ordner/prefix_>
## ansichten.json: [{"name", "pos": [x, y über Boden, z], "look": [x, y über Boden, z], "fov", "hour", "pan", "tilt"}]
## Schreibt <prefix><name>.png (freie Ansicht), <prefix><name>_kopf.png (Kopfkamera MoveEye), <prefix><name>_waerme.png (Wärmebild)
## und <prefix>werte.json (Laden: Zeiten, Kacheln, Häuser, Dreiecke, Hindernisse, Hinweis; je Ansicht Bilder pro Sekunde).
## Ohne --ansichten nur laden und messen (Test: «geladen», Grund, Hindernisse).

var main
var vp: SubViewport
var cam: Camera3D
var out := "/tmp/gebaeude_"
var views: Array = []
var res := {}


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	i = args.find("--ansichten")
	if i >= 0:
		views = JSON.parse_string(FileAccess.get_file_as_string(args[i + 1]))
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s).timeout


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	var args := OS.get_cmdline_user_args()
	var qi := args.find("--qual")
	if qi >= 0:
		main._set_quality(args[qi + 1])
	var oi := args.find("--ort")
	var o := (args[oi + 1] if oi >= 0 else "47.34753,8.16017,Seon").split(",")
	var bi := args.find("--b3d")
	main.geo.b3d_on = bi < 0 or args[bi + 1] != "off"
	var t0 := Time.get_ticks_msec()
	main.choose_place(float(o[0]), float(o[1]), o[2] if o.size() > 2 else "")
	while (main.geo.busy or not main.geo.loaded or main.scene != "ort") and Time.get_ticks_msec() - t0 < 400000:
		await wait(0.5)
	var t_load := Time.get_ticks_msec() - t0
	await wait(3.0)
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()
	var g = main.geo
	var th := 0
	var stack: Array = [main.scenes.root]
	var b3d_parts := 0
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is MeshInstance3D and n.mesh != null:
			for part in g.b3d_meshes:
				if part["mesh"] == n.mesh:
					if (n.layers & 2) != 0:
						th += 1
					else:
						b3d_parts += 1
	var inside := 0                                      # MoveEye (0, 0) inside a building footprint?
	for bd in g.buildings:
		if Geometry2D.is_point_in_polygon(Vector2.ZERO, bd["poly"]):
			inside += 1
	res["laden"] = {"ms": t_load, "loaded": g.loaded, "b3d_on": g.b3d_on, "b3d": g.b3d_stats, "grund": g.b3d_reason, "diag": g.b3d_diag,
			"counts": g.counts, "hindernisse": main.obstacles.size(), "gebaeude": g.buildings.size(), "b3d_netze": b3d_parts, "b3d_waerme_zwillinge": th,
			"kopf_im_haus": inside, "hinweis": main.geo_note, "info": g.info, "osm": g.osm.size(), "quality": main.quality}
	print("GEB laden ", JSON.stringify(res["laden"]))
	if not views.is_empty():
		vp = SubViewport.new()
		vp.size = Vector2i(1280, 720)
		vp.world_3d = root.world_3d
		vp.msaa_3d = root.msaa_3d
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		root.add_child(vp)
		var fl = main.get_node_or_null("flora_licht")
		if fl != null:
			fl.attach(vp)
		cam = Camera3D.new()
		cam.cull_mask = 1
		cam.far = 2000.0
		vp.add_child(cam)
		cam.current = true
	for v in views:
		main.weather = "clear"
		main.set_hour(float(v.get("hour", 11.0)))
		if v.has("pan"):
			if main.patrol != null:
				main.patrol.active = false
			main.mw["servo"] = {"pan_deg": float(v["pan"]), "tilt_deg": float(v.get("tilt", 0.0))}
			main.head.rotation.y = -deg_to_rad(float(v["pan"]))
		var p: Array = v["pos"]
		var l: Array = v["look"]
		if v.get("auto", false):                              # a free place in the street, looking at the most houses
			var auto := _street_spot(g, float(v.get("r0", 15.0)), float(v.get("r1", 60.0)))
			p = [auto[0].x, 1.7, auto[0].y]
			l = [auto[1].x, 5.0, auto[1].y]
			print("GEB auto ", v["name"], " ", p, " -> ", l)
		var pos := Vector3(p[0], p[1] + main.ground_y(p[0], p[2]), p[2])
		var look := Vector3(l[0], l[1] + main.ground_y(l[0], l[2]), l[2])
		cam.fov = float(v.get("fov", 60.0))
		cam.look_at_from_position(pos, look, Vector3.UP)
		main.view_cam.global_transform = cam.global_transform
		main.view_cam.fov = cam.fov
		await wait(1.5)
		var f0 := Engine.get_frames_drawn()
		var ts := Time.get_ticks_msec()
		await wait(float(v.get("fps_s", 5.0)))
		var fps := (Engine.get_frames_drawn() - f0) * 1000.0 / maxf(1.0, Time.get_ticks_msec() - ts)
		var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var prim := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		vp.get_texture().get_image().save_png(out + str(v["name"]) + ".png")
		for k in [[0, "_kopf"], [2, "_waerme"]]:
			var im: Image = main.vps[k[0]].get_texture().get_image()
			if im != null:
				im.save_png(out + str(v["name"]) + k[1] + ".png")
		res[str(v["name"])] = {"fps": snappedf(fps, 0.01), "draw_calls": dc, "primitives": prim}
		print("GEB view ", v["name"], " ", res[str(v["name"])])
	var f := FileAccess.open(out + "werte.json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(res, "  "))
		f.close()
	quit()


func _street_spot(g, r0: float, r1: float) -> Array:
	"""[pos, look] (x / z): free (no obstacle within 7 m), looking where most building corners are within 70 m"""
	var best := [Vector2(r0, 0), Vector2.ZERO]
	var score := -1.0
	var r := r0
	while r <= r1:
		for k in range(36):
			var pt := Vector2.from_angle(k * TAU / 36.0) * r
			var free := true
			for o in main._ob_near(pt):
				if float(main._ob_closest(o, pt)[1]) < 7.0:
					free = false
					break
			if not free:
				continue
			for k2 in range(12):
				var dir := Vector2.from_angle(k2 * TAU / 12.0)
				var s := 0.0
				for bd in g.buildings:
					var c: Vector2 = (bd["poly"] as PackedVector2Array)[0] - pt
					if c.length() < 70.0 and c.length() > 8.0 and c.normalized().dot(dir) > 0.8:
						s += 1.0
				if s > score:
					score = s
					best = [pt, pt + dir * 30.0]
		r += 7.0
	return best
