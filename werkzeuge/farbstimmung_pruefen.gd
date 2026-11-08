extends SceneTree
## Prüfung «Flora und Fauna» Paket 2: die Farbstimmung der freien Ansicht (scripts/farbstimmung.gd) darf die Bilder der
## MoveEye-Kameras und des Wärmebilds NICHT verändern. Bilder aller Kamera-SubViewports (main.vps) mit Farbstimmung aus /
## an / aus, ohne Wind, Besucher, Zeit und die eigenen Effekt-Vierecke der Kameras (Rauschen, Nachziehen); Ergebnis: Anzahl verschiedener Pixel (an gegen aus muss 0 sein, sofern aus
## gegen aus 0 ist).
##   cd simulator3d && HOME=<test-home> xvfb-run -a -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/farbstimmung_pruefen.gd" \
##       -- --no-update --grafik normal [--scene camping] [--aus ordner/prefix_]

var main
var out := ""
var g0: Array = []


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func _shots() -> Array:
	for k in range(3):
		main.set_hour(14.0)                                   # the clock of the simulation runs on real time: hold it
		if not g0.is_empty():
			main.gain = g0.duplicate()                        # and the auto exposure of the cameras (main._auto_exposure)
		await process_frame
	await RenderingServer.frame_post_draw
	var imgs := []
	for vp in main.vps:
		imgs.append((vp as SubViewport).get_texture().get_image())
	return imgs


func _diff(a: Image, b: Image) -> int:
	if a.get_size() != b.get_size():
		return -1
	var n := 0
	for y in range(a.get_height()):
		for x in range(a.get_width()):
			if a.get_pixel(x, y) != b.get_pixel(x, y):
				n += 1
	return n


func _run() -> void:
	await create_timer(3.0).timeout
	main.eco_idle = false
	var args := OS.get_cmdline_user_args()
	var si := args.find("--scene")
	main.set_scene(args[si + 1] if si >= 0 else "camping")
	await create_timer(4.0).timeout
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()
	main.wind = 0.0
	main.set_hour(14.0)
	# everything that changes from frame to frame off: camera noise / realism, cloud shadows, insects, animals, time
	if main.realism != null:
		main.realism.fx_on = false
	main.lens_noise = 0.0
	main.cloud_shadows = false
	main.insects_on = false
	main.fauna_on = false
	# the camera's own post quads (exposure, camera effects, lens grain) change every picture by design (noise, trail):
	# hidden for this test, so the 3D picture of each MoveEye camera is compared as it is rendered
	var fx: Array = []
	fx.append_array(main.lens_mats)
	fx.append_array(main.expo_mats)
	fx.append_array(main.camfx_mats)
	for vp in main.vps:
		for q in (vp as Node).find_children("*", "GeometryInstance3D", true, false):
			if (q is MeshInstance3D and fx.has((q as MeshInstance3D).material_override)) or q is CPUParticles3D:
				(q as GeometryInstance3D).visible = false
	await create_timer(2.0).timeout
	if RenderingServer.has_method("set_shader_time_scale"):
		RenderingServer.call("set_shader_time_scale", 0.0)
	Engine.time_scale = 0.0                                   # (after the last timer: timers stand still now)
	var fl = main.get_node_or_null("flora_licht")
	if fl == null:
		print("LICHT keine Farbstimmung (Stufe Lite / alt?)")
		quit(1)
		return
	var cls: Array = fl.layers
	for c in cls:
		c.visible = false
	g0 = Array(main.gain).duplicate()
	var off1: Array = await _shots()
	for c in cls:
		c.visible = true
	var on: Array = await _shots()
	for c in cls:
		c.visible = false
	var off2: Array = await _shots()
	var ok := true
	for i in range(off1.size()):
		var d_on := _diff(off1[i], on[i])
		var d_off := _diff(off1[i], off2[i])
		print("LICHT Kamera ", i, " ", off1[i].get_size(), ": an/aus verschieden=", d_on, " aus/aus verschieden=", d_off)
		if d_on != 0:
			ok = false
		if out != "":
			(on[i] as Image).save_png(out + "kamera_%d_an.png" % i)
			(off1[i] as Image).save_png(out + "kamera_%d_aus1.png" % i)
			(off2[i] as Image).save_png(out + "kamera_%d_aus2.png" % i)
	print("LICHT ", "OK: Kamera-Bilder gleich" if ok else "ACHTUNG: Kamera-Bilder verschieden")
	quit(0 if ok else 2)
