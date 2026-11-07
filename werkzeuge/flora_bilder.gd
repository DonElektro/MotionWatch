extends SceneTree
## Vorher/Nachher-Bilder für «Flora und Fauna» (Idee Nr. 5, Phase 1), ohne Fenster unter Xvfb aus dem Quelltext:
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/flora_bilder.gd" \
##       -- --no-update --grafik normal --ansichten <ansichten.json> --aus <ordner/prefix_>
## ansichten.json: [{"name", "scene", "hour", "pos": [x,y,z], "look": [x,y,z], "fov", "tier": {"kind", "at": [x,z], "to": [x,z]},
##                  "wind", "fps_s"}]
## Schreibt <prefix><name>.png (freie Ansicht, ohne Bedienung), <prefix><name>_kopf.png (Bild der Kopfkamera für MoveEye)
## und <prefix>fps.json (Bilder pro Sekunde je Ansicht, gemessen mit derselben Kameralage in der grossen Ansicht).

var main
var vp: SubViewport
var cam: Camera3D
var out := "/tmp/flora_"
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
	print("FLORA lite=", Q.lite(), " quality=", main.quality, " grafik=", main.grafik_mode, " renderer=", Q.renderer())
	vp = SubViewport.new()
	vp.size = Vector2i(1280, 720)
	vp.world_3d = root.world_3d
	vp.msaa_3d = root.msaa_3d
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	vp.own_world_3d = false
	root.add_child(vp)
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
		print("FLORA layout ", sc, " ", _layout())
		main.weather = str(v.get("weather", "clear"))
		main.wind = float(v.get("wind", 8.0))
		main.set_hour(float(v.get("hour", 13.0)))
		var p: Array = v["pos"]
		var l: Array = v["look"]
		var pos := Vector3(p[0], p[1], p[2])
		var look := Vector3(l[0], l[1], l[2])
		if v.get("ground", false):
			pos.y += main.ground_y(pos.x, pos.z)
			look.y += main.ground_y(look.x, look.z)
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
		print("FLORA view ", v["name"], " ", res[str(v["name"])])
		if actor != null and is_instance_valid(actor):
			actor.queue_free()
	var f := FileAccess.open(out + "fps.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(res))
	f.close()
	print("FLORA fertig")
	quit(0)
