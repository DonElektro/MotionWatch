extends SceneTree
## Vorher/Nachher-Bilder für «Wege und Strassen» (wie flora_bilder.gd, dazu «puddle»: Pfützen 0 … 1 sofort, «wet» Nässe),
## ohne Fenster unter Xvfb aus dem Quelltext:
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/wege_bilder.gd" \
##       -- --no-update --grafik normal --ansichten <ansichten.json> --aus <ordner/prefix_>
## ansichten.json: [{"name", "scene", "hour", "pos": [x,y,z], "look": [x,y,z], "fov", "tier": {"kind", "at": [x,z], "to": [x,z]},
##                  "wind", "fps_s", "weather", "puddle", "wet", "pan", "tilt",
##                  "saison", "snow" (on / off / auto), "snow_cm" (Schneedecke von wetter.gd),
##                  "tal": Bergtal-Koordinaten (pos / look = x, Höhe über Boden, z)}]
## Schreibt <prefix><name>.png (freie Ansicht, ohne Bedienung), <prefix><name>_kopf.png (Bild der Kopfkamera für MoveEye)
## und <prefix>fps.json (Bilder pro Sekunde je Ansicht, gemessen mit derselben Kameralage in der grossen Ansicht).

var main
var vp: SubViewport
var cam: Camera3D
var out := "/tmp/wege_"
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


func _layout() -> String:
	"""Fingerabdruck der Szene (Hindernisse, Kronen): muss vorher / nachher gleich sein"""
	var h := 0.0
	for o in main.obstacles:
		h += str(o).hash() % 100000
	for t in main.tree_spots:
		h += Vector2(t[0]).x * 3.1 + Vector2(t[0]).y * 1.7 + float(t[1])
	var f := FileAccess.open(out + "hindernisse_%s.txt" % str(main.scene), FileAccess.WRITE)
	if f != null:
		for o in main.obstacles:
			f.store_line(str(o))
		for t in main.tree_spots:
			f.store_line(str(t))
		f.close()
	return "obstacles=%d trees=%d sum=%.2f" % [main.obstacles.size(), main.tree_spots.size(), h]


func _wege_stats() -> Dictionary:
	"""Netze von «Wege und Strassen» in der Szene: Anzahl (sichtbar, Ebene 1) und Dreiecke, nach Art"""
	var out := {}
	var Wg = load("res://scripts/wege.gd")
	var neu: bool = Wg != null and Wg.has_method("steps")      # (3.63.0: only the shaders)
	var stack: Array = [main.scenes.root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if not (n is MeshInstance3D) or not (n as MeshInstance3D).visible or ((n as MeshInstance3D).layers & 1) == 0:
			continue
		var mi := n as MeshInstance3D
		var mt = mi.material_override
		var kind := ""
		if mt is ShaderMaterial and (mt as ShaderMaterial).shader != null:
			var pth := (mt as ShaderMaterial).shader.resource_path.get_file().get_basename()
			if pth in ["strasse", "feldweg", "wanderweg", "pfad"]:
				kind = pth
		elif neu and mt != null and (mt == Wg._step_mat or mt == Wg._mark_mat or mt == Wg._kerb_mat):
			kind = "stufen" if mt == Wg._step_mat else ("pfosten" if mt == Wg._mark_mat else "randstein")
		if kind == "" or mi.mesh == null:
			continue
		var tris := 0
		for si in range(mi.mesh.get_surface_count()):
			var arr: Array = mi.mesh.surface_get_arrays(si)
			tris += (arr[Mesh.ARRAY_INDEX].size() if arr[Mesh.ARRAY_INDEX] != null else arr[Mesh.ARRAY_VERTEX].size()) / 3
		if not out.has(kind):
			out[kind] = [0, 0]
		out[kind][0] += 1
		out[kind][1] += tris
	return out


func _quiet() -> void:
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	var args := OS.get_cmdline_user_args()
	var qi := args.find("--qual")
	if qi >= 0:
		main._set_quality(args[qi + 1])
	var si := args.find("--saison")
	if si >= 0 and main.get("jahreszeiten") != null:
		main.control({"action": "jahreszeiten", "do": "set", "key": "mode", "value": args[si + 1]})
	var Q = load("res://scripts/quality.gd")
	print("WEGE lite=", Q.lite(), " quality=", main.quality, " grafik=", main.grafik_mode, " renderer=", Q.renderer())
	vp = SubViewport.new()
	vp.size = Vector2i(1280, 720)
	vp.world_3d = root.world_3d
	vp.msaa_3d = root.msaa_3d
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	vp.own_world_3d = false
	root.add_child(vp)
	var fl = main.get_node_or_null("flora_licht")             # Paket 2: the free view's colour grading also in these pictures
	if fl != null:
		fl.attach(vp)
	cam = Camera3D.new()
	cam.cull_mask = 1
	cam.far = 2000.0
	vp.add_child(cam)
	cam.current = true
	var cur_scene := ""
	for v in views:
		var sc := str(v.get("scene", "camping"))
		if sc != cur_scene:
			main.set_scene(sc)
			cur_scene = sc
			await wait(4.0)
		_quiet()
		await wait(0.3)
		print("WEGE layout ", sc, " ", _layout())
		print("WEGE netze ", _wege_stats())
		main.weather = str(v.get("weather", "clear"))
		main.wind = float(v.get("wind", 8.0))
		main.set_hour(float(v.get("hour", 13.0)))
		if main.colors != null and v.has("puddle"):
			main.colors.puddle = float(v["puddle"])
			main.colors.wetness = float(v.get("wet", 1.0))
		if v.has("saison") and main.get("jahreszeiten") != null:   # season (fixed) and snow lying (jahreszeiten «jz_snow»: on / off / auto)
			main.control({"action": "jahreszeiten", "do": "set", "key": "mode", "value": str(v["saison"])})
		if v.has("snow") and main.get("jahreszeiten") != null:
			main.jahreszeiten.snow_mode = str(v["snow"])
			if main.get("wetter") != null and v.has("snow_cm"):
				main.wetter.snow_cm = float(v["snow_cm"])     # wetter.gd «Schnee bleibt liegen»: e.g. 8 = as after a snowfall
			main.jahreszeiten.update()
		if v.has("pan"):                                     # the MoveEye head: pan / tilt like a servo packet of MoveEye
			if main.patrol != null:
				main.patrol.active = false
			main.mw["servo"] = {"pan_deg": float(v["pan"]), "tilt_deg": float(v.get("tilt", 0.0))}
			main.head.rotation.y = -deg_to_rad(float(v["pan"]))
		var p: Array = v["pos"]
		var l: Array = v["look"]
		var pos := Vector3(p[0], p[1], p[2])
		var look := Vector3(l[0], l[1], l[2])
		if v.get("ground", false):
			pos.y += main.ground_y(pos.x, pos.z)
			look.y += main.ground_y(look.x, look.z)
		var bt = main.scenes.data.get("bergtal") if main.scenes.data.has("bergtal") else null
		if v.get("tal", false) and bt != null:                # Bergtal: pos / look in valley coordinates (x, height above ground, z)
			pos = bt.WG(pos.x, pos.z, pos.y)
			look = bt.WG(look.x, look.z, look.y)
		cam.fov = float(v.get("fov", 60.0))
		cam.look_at_from_position(pos, look, Vector3.UP)
		main.view_cam.global_transform = cam.global_transform
		main.view_cam.fov = cam.fov
		var tier = v.get("tier", null)
		var actor = null
		if tier != null:
			var at: Array = tier["at"]
			var to: Array = tier.get("to", at)
			var a3 := Vector3(at[0], 0, at[1])
			var t3 := Vector3(to[0], 0, to[1])
			actor = main.spawn(str(tier["kind"]), a3, t3)
			await wait(float(tier.get("walk_s", 2.5)))
			if tier.get("freeze", true) and actor != null and is_instance_valid(actor):
				actor.process_mode = Node.PROCESS_MODE_DISABLED
		await wait(1.5)
		# FPS: the big view with this camera
		var fs := float(v.get("fps_s", 6.0))
		var f0 := Engine.get_frames_drawn()
		var t0 := Time.get_ticks_msec()
		await wait(fs)
		var fps := (Engine.get_frames_drawn() - f0) * 1000.0 / maxf(1.0, Time.get_ticks_msec() - t0)
		var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var prim := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		var obj := Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		img.save_png(out + str(v["name"]) + ".png")
		var hc: Image = main.vps[0].get_texture().get_image()
		if hc != null:
			hc.save_png(out + str(v["name"]) + "_kopf.png")
		res[str(v["name"])] = {"fps": snappedf(fps, 0.01), "draw_calls": dc, "primitives": prim, "objects": obj}
		print("WEGE view ", v["name"], " ", res[str(v["name"])])
		if actor != null and is_instance_valid(actor):
			actor.queue_free()
	var f := FileAccess.open(out + "fps.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(res))
	f.close()
	print("WEGE fertig")
	quit(0)
