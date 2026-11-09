extends SceneTree
## Vergleich freie Ansicht / Kopfkamera / Weitwinkel / Wärmebild in derselben Szene und Zeit (Fehlerbericht 3.67.0 «Kamerabild»):
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/kamerabild_bilder.gd" \
##       -- --no-update --grafik normal|lite [--qual simple|medium|high] --szene ferienpark --stunde 13 [--pan 30 --tilt -5]
##          [--noir 0|1] [--splash n] [--warten 20] --aus <ordner/prefix_>
## Schreibt <prefix>frei.png (hinter und über dem Kopf, in Blickrichtung), <prefix>kopf.png, <prefix>weit.png, <prefix>waerme.png
## und <prefix>info.json (Kopf-Lage, Szene, Qualität, Zahl der sichtbaren Netze pro Shader in Ebene 1).

var main
var out := "/tmp/kamerabild_"


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s).timeout


func _arg(k: String, d: String) -> String:
	var args := OS.get_cmdline_user_args()
	var i := args.find(k)
	return args[i + 1] if i >= 0 and i + 1 < args.size() else d


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	if _arg("--qual", "") != "":
		main._set_quality(_arg("--qual", ""))
	var sc := _arg("--szene", "ferienpark")
	if main.scene != sc:
		main.set_scene(sc)
		await wait(5.0)
	main.weather = "clear"
	main.set_hour(float(_arg("--stunde", "13")))
	main.control({"action": "set", "id": "auto", "value": false})
	if _arg("--noir", "") != "" and main.camphys != null:      # NoIR colours 0 … 1.5 (test: 0 = without the pink cast)
		main.camphys.noir_k = float(_arg("--noir", "1"))
	if _arg("--splash", "") != "" and main.get("wetter") != null:   # n drops on both lenses (test of the lens drops)
		main.control({"action": "wetter", "do": "splash", "n": int(_arg("--splash", "0")), "cam": 0})
		main.control({"action": "wetter", "do": "splash", "n": int(_arg("--splash", "0")), "cam": 1})
	if _arg("--pan", "") != "":
		if main.patrol != null:
			main.patrol.active = false
		main.mw["servo"] = {"pan_deg": float(_arg("--pan", "0")), "tilt_deg": float(_arg("--tilt", "0"))}
	await wait(float(_arg("--warten", "20")))
	var hp: Vector3 = main.head.global_position
	var fwd: Vector3 = -main.head.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3.FORWARD
	var vp := SubViewport.new()
	vp.size = Vector2i(960, 540)
	vp.world_3d = root.world_3d
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	root.add_child(vp)
	var cam := Camera3D.new()
	cam.cull_mask = main.view_cam.cull_mask
	cam.far = 2000.0
	vp.add_child(cam)
	cam.look_at_from_position(hp - fwd * 9.0 + Vector3(0, 5.0, 0), hp + fwd * 14.0, Vector3.UP)
	cam.current = true
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	vp.get_texture().get_image().save_png(out + "frei.png")
	for k in [[0, "kopf"], [1, "weit"], [2, "waerme"]]:
		var im: Image = main.vps[k[0]].get_texture().get_image()
		if im != null:
			im.save_png(out + k[1] + ".png")
	var shaders := {}
	var stack: Array = [main.scenes.root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is GeometryInstance3D and (n as GeometryInstance3D).visible and ((n as VisualInstance3D).layers & 1) != 0:
			var m = (n as GeometryInstance3D).material_override
			var key := "none"
			if m is ShaderMaterial and (m as ShaderMaterial).shader != null:
				key = (m as ShaderMaterial).shader.resource_path.get_file()
			elif m != null:
				key = m.get_class()
			shaders[key] = shaders.get(key, 0) + 1
	var info := {"scene": main.scene, "quality": main.quality, "head": [hp.x, hp.y, hp.z], "fwd": [fwd.x, fwd.z], "shaders": shaders}
	print("KAM ", JSON.stringify(info))
	var f := FileAccess.open(out + "info.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(info, "  "))
	f.close()
	quit()
