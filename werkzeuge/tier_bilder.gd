extends SceneTree
## Vorher/Nachher-Bilder der Tiere (Paket 3 «Tiere echt»), ohne Fenster unter Xvfb aus dem Quelltext:
##   cd simulator3d && HOME=<test-home> xvfb-run -a -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/tier_bilder.gd" \
##       -- --no-update --grafik normal [--flora alt|normal|hoch] --ansichten <ansichten.json> --aus <ordner/prefix_>
## ansichten.json: [{"name", "scene", "hour", "pos": [x,y,z], "look": [x,y,z], "fov", "ground",
##                  "tiere": [{"kind", "at": [x,z], "to": [x,z], "walk_s", "stand": true, "idle": "lie", "freeze"}],
##                  "waerme": true, "fps_s",
##                  "blick": [x,y,z], "hoehe", "vor_kopf": true, "ir": true}]
##   blick: die Kamera schaut aus dieser Richtung auf die Tiere (alle im Bild); vor_kopf: die Tiere vor die MoveEye-Kamera
##   (at / to = [rechts, vorne] in m), Infrarot an, dazu <prefix><name>_kopf.png (Bild der MoveEye-Kamera)
##   stand: das Tier bleibt stehen (Ruhe-Bewegung), sonst geht es walk_s Sekunden und wird dann angehalten.
## Schreibt <prefix><name>.png (freie Ansicht), mit "waerme" auch <prefix><name>_waerme.png (Wärmebild derselben Kamera,
## entschlüsselt, Farben «inferno» über 0 … 40 °C) und <prefix>werte.json (Bilder/s, Zeichenaufrufe, Dreiecke je Ansicht).

var main
var vp: SubViewport
var vt: SubViewport
var cam: Camera3D
var camt: Camera3D
var out := "/tmp/tiere_"
var views: Array = []
var res := {}


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	i = args.find("--ansichten")
	if i >= 0:
		var js = JSON.parse_string(FileAccess.get_file_as_string(args[i + 1]))
		if typeof(js) != TYPE_ARRAY:
			printerr("TIERE Ansichten nicht lesbar: ", args[i + 1])
			quit(2)
			return
		views = js
	i = args.find("--flora")
	if i >= 0:
		load("res://scripts/flora.gd").modus = args[i + 1]
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s).timeout


func _quiet() -> void:
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()


func _inferno(f: float) -> Color:
	var stops := [Color(0, 0, 0.02), Color(0.34, 0.06, 0.43), Color(0.73, 0.21, 0.33), Color(0.98, 0.55, 0.04), Color(0.99, 1.0, 0.64)]
	f = clampf(f, 0.0, 1.0) * 4.0
	var k := int(minf(3.0, floorf(f)))
	return stops[k].lerp(stops[k + 1], f - k)


func _waerme_bild(img: Image) -> Image:
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	var w := img.get_width()
	var h := img.get_height()
	var d := img.get_data()
	var o := Image.create(w, h, false, Image.FORMAT_RGB8)
	var lo := 0.0
	var hi := 40.0
	for y in range(h):
		for x in range(w):
			var a := (y * w + x) * 4
			var t: float = main.th_hi[d[a]] + main.th_lo[d[a + 1]] - 40.0
			o.set_pixel(x, y, _inferno((t - lo) / (hi - lo)))
	return o


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	var args := OS.get_cmdline_user_args()
	var qi := args.find("--qual")
	if qi >= 0:
		main._set_quality(args[qi + 1])
	var Fl = load("res://scripts/flora.gd")
	print("TIERE flora=", Fl.stufe(main), " quality=", main.quality, " grafik=", main.grafik_mode, " gpu=",
			RenderingServer.get_video_adapter_name(), " forward_plus=", RenderingServer.get_rendering_device() != null,
			" MW_TIERE=", OS.get_environment("MW_TIERE"))
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
	vt = SubViewport.new()
	vt.size = Vector2i(640, 360)
	vt.world_3d = root.world_3d
	vt.msaa_3d = Viewport.MSAA_DISABLED
	vt.render_target_update_mode = SubViewport.UPDATE_DISABLED
	root.add_child(vt)
	camt = Camera3D.new()
	camt.cull_mask = 2
	camt.far = 2000.0
	camt.attributes = CameraAttributesPractical.new()
	camt.environment = main.th_env
	vt.add_child(camt)
	camt.current = true
	var cur_scene := ""
	for v in views:
		var sc := str(v.get("scene", "wild"))
		if sc != cur_scene:
			main.set_scene(sc)
			cur_scene = sc
			await wait(4.0)
		_quiet()
		await wait(0.3)
		main.weather = str(v.get("weather", "clear"))
		main.wind = float(v.get("wind", 5.0))
		main.set_hour(float(v.get("hour", 13.0)))
		var p: Array = v["pos"]
		var l: Array = v["look"]
		var pos := Vector3(p[0], p[1], p[2])
		var look := Vector3(l[0], l[1], l[2])
		if v.get("ground", true):
			pos.y += main.ground_y(pos.x, pos.z)
			look.y += main.ground_y(look.x, look.z)
		cam.fov = float(v.get("fov", 40.0))
		cam.look_at_from_position(pos, look, Vector3.UP)
		camt.fov = cam.fov
		camt.global_transform = cam.global_transform
		main.view_cam.global_transform = cam.global_transform
		main.view_cam.fov = cam.fov
		var actors: Array = []
		var walk := 0.0
		if v.has("seed"):
			seed(int(v["seed"]))                                       # same colours / breeds before and after
		var kopf: Transform3D = (main.cams[0] as Camera3D).global_transform
		if v.has("vor_kopf"):
			main.cond["ir"] = bool(v.get("ir", true))                # infrared light of the MoveEye camera at night
			cam.global_transform = kopf
			cam.fov = (main.cams[0] as Camera3D).fov
			camt.global_transform = kopf
			camt.fov = cam.fov
		for tier in v.get("tiere", []):
			var at: Array = tier["at"]
			var to: Array = tier.get("to", at)
			var p0 := Vector3(at[0], 0, at[1])
			var p1 := Vector3(to[0], 0, to[1])
			if v.has("vor_kopf"):                                      # at / to: [to the right, ahead] of the MoveEye camera
				var fw := -kopf.basis.z
				fw.y = 0.0
				fw = fw.normalized()
				var rt := fw.cross(Vector3.UP)
				p0 = kopf.origin + fw * float(at[1]) + rt * float(at[0])
				p1 = kopf.origin + fw * float(to[1]) + rt * float(to[0])
				p0.y = 0.0
				p1.y = 0.0
			var a = main.spawn(str(tier["kind"]), p0, p1)
			if a == null:
				continue
			if tier.get("stand", false):
				a.wait_until = a.now_s() + 1000.0
			if tier.has("idle"):                                       # e.g. "lie", "graze", "sniff"
				a.idle_kind = str(tier["idle"])
				a.idle_until = a.now_s() + 1000.0
				a.wait_until = a.now_s() + 1000.0
			actors.append([a, tier])
			walk = maxf(walk, float(tier.get("walk_s", 2.5)))
		for vg in v.get("voegel", []):                                 # birds of fauna.gd: on the ground or on a tree
			var at2: Array = vg.get("at", [0, -10])
			if vg.get("perch", false) and main.fauna.has_method("perch_flock"):
				var pb = main.fauna.perch_flock(str(vg["kind"]))
				if pb != null and v.has("zu_vogel"):                     # the camera goes close to the first bird on the tree
					var zo: Array = v["zu_vogel"]
					var bp: Vector3 = (pb as Node3D).global_position
					cam.look_at_from_position(bp + Vector3(zo[0], zo[1], zo[2]), bp + Vector3(0, 0.1, 0), Vector3.UP)
					cam.fov = float(v.get("fov", 40.0))
					camt.global_transform = cam.global_transform
					main.view_cam.global_transform = cam.global_transform
			else:
				main.fauna.ground_flock(str(vg["kind"]), Vector3(at2[0], 0, at2[1]))
			if vg.has("scheuchen_s"):                                  # somebody comes: they fly up (frozen in the air)
				await wait(0.8)
				main.tiere._test_threat = [Vector3(at2[0], 0, at2[1]), 1e9]
				await wait(float(vg["scheuchen_s"]))
				main.fauna.process_mode = Node.PROCESS_MODE_DISABLED
		await wait(walk)
		for e in actors:
			if is_instance_valid(e[0]) and (e[1] as Dictionary).get("freeze", true):
				e[0].process_mode = Node.PROCESS_MODE_DISABLED
		if v.has("blick") and not actors.is_empty():
			# the camera from the animals: centre of their places, far enough that all fit into the picture
			var c := Vector3.ZERO
			for e in actors:
				c += (e[0] as Node3D).global_position
			c /= float(actors.size())
			var r := 0.0
			for e in actors:
				r = maxf(r, (e[0] as Node3D).global_position.distance_to(c) + float(e[0].radius) + 0.3)
			var bl: Array = v["blick"]
			var dv := Vector3(bl[0], bl[1], bl[2]).normalized()
			var hgt := float(v.get("hoehe", 0.3))
			var dist := r / tan(deg_to_rad(cam.fov * 0.5)) * 1.05
			cam.look_at_from_position(c + Vector3(0, hgt, 0) + dv * dist, c + Vector3(0, hgt * 0.7, 0), Vector3.UP)
			camt.global_transform = cam.global_transform
			main.view_cam.global_transform = cam.global_transform
		await wait(1.0)
		var fs := float(v.get("fps_s", 4.0))
		var f0 := Engine.get_frames_drawn()
		var t0 := Time.get_ticks_msec()
		await wait(fs)
		var fps := (Engine.get_frames_drawn() - f0) * 1000.0 / maxf(1.0, Time.get_ticks_msec() - t0)
		var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var prim := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		if v.get("waerme", false):
			vt.render_target_update_mode = SubViewport.UPDATE_ONCE
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		vp.get_texture().get_image().save_png(out + str(v["name"]) + ".png")
		if v.get("waerme", false):
			_waerme_bild(vt.get_texture().get_image()).save_png(out + str(v["name"]) + "_waerme.png")
		if v.has("vor_kopf"):
			var hc: Image = main.vps[0].get_texture().get_image()
			if hc != null:
				hc.save_png(out + str(v["name"]) + "_kopf.png")
		main.fauna.process_mode = Node.PROCESS_MODE_INHERIT
		if main.tiere != null:
			main.tiere._test_threat = null
		res[str(v["name"])] = {"fps": snappedf(fps, 0.01), "draw_calls": dc, "primitives": prim, "tiere": actors.size()}
		print("TIERE view ", v["name"], " ", res[str(v["name"])])
		for e in actors:
			if is_instance_valid(e[0]):
				e[0].queue_free()
	var f := FileAccess.open(out + "werte.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(res))
	f.close()
	print("TIERE fertig")
	quit(0)
