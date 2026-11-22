extends SceneTree
## Handwerkzeug (kein CI-Test): Bilder der 8 Bergtal-Aussichtspunkte (bergtal.gd VIEWPOINTS) zum Vergleichen, ohne Bedienung,
## je am Tag (14:00, klar) und im Abendrot (Sommer, Bergstimmungen an, Sonne knapp über dem Horizont). Unter Xvfb:
##   cd simulator3d && HOME=<test-home> xvfb-run -a -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/aussicht_bilder.gd" \
##       -- --no-update --no-tour --grafik normal --quality nice --aus <ordner/prefix_> [--nur-tag]
## Schreibt <prefix><vp_id>_tag.jpg und <prefix><vp_id>_abend.jpg (1280 × 720) und <prefix>liste.json (Namen, Stunde, Sonne).
## Auf dem HP: werkzeuge/aussicht_bilder.py (startet dies mit xvfb-run).

const Bergtal = preload("res://scripts/bergtal.gd")

var main
var vp: SubViewport
var cam: Camera3D
var out := "/tmp/aussicht_"
var liste := []


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	DisplayServer.window_set_size(Vector2i(1280, 720))
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _mod():
	var bt = main.scenes.data.get("bergtal", null) if main.scenes != null else null
	return bt.aussicht if bt != null and bt.get("aussicht") != null else null


func _quiet() -> void:
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()


func _abend_stunde() -> float:
	"""die Stunde am Abend, in der die Sonne etwa 2.5° hoch steht (Abendrot, bergtal_aussicht._moods_frame: −5° … 7°)"""
	var h := 17.0
	while h < 22.5:
		main.set_hour(h)
		if main.sun_el() <= 2.5:
			return h
		h += 0.05
	return 20.5


func _bild(name: String) -> void:
	cam.global_transform = main.view_cam.global_transform
	cam.fov = main.view_cam.fov
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	img.save_jpg(out + name + ".jpg", 0.9)
	print("AUSSICHT bild ", out + name + ".jpg ", img.get_size())


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	var Q = load("res://scripts/quality.gd")
	if main.get("jahreszeiten") != null:
		main.control({"action": "jahreszeiten", "do": "set", "key": "mode", "value": "sommer"})
	main.set_scene("bergtal")
	var t0 := Time.get_ticks_msec()
	while _mod() == null and Time.get_ticks_msec() - t0 < 120000:
		await wait(0.5)
	if _mod() == null:
		print("AUSSICHT FEHLER: Bergtal nicht geladen")
		quit(1)
		return
	await wait(4.0)
	print("AUSSICHT lite=", Q.lite(), " quality=", main.quality, " grafik=", main.grafik_mode, " renderer=", Q.renderer(),
			" season=", main.season, " moods=", _mod().state().get("moods"))
	vp = SubViewport.new()
	vp.size = Vector2i(1280, 720)
	vp.world_3d = root.world_3d
	vp.msaa_3d = root.msaa_3d
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	vp.own_world_3d = false
	root.add_child(vp)
	var fl = main.get_node_or_null("flora_licht")             # the free view's colour grading also in these pictures
	if fl != null and fl.has_method("attach"):
		fl.attach(vp)
	cam = Camera3D.new()
	cam.cull_mask = 1
	cam.far = 4000.0
	vp.add_child(cam)
	cam.current = true
	main._set_speed(0.0)
	var abend := _abend_stunde()
	var zeiten := [["tag", 14.0]]
	if not ("--nur-tag" in OS.get_cmdline_user_args()):
		zeiten.append(["abend", abend])
	for z in zeiten:
		for v in Bergtal.VIEWPOINTS:
			_quiet()
			main.weather = "clear"
			main.set_hour(float(z[1]))
			var r: Dictionary = _mod().control({"what": "visit", "value": v[0]})
			await wait(4.0)                                  # sky update (0.5 s), moods, streaming around the view
			main.weather = "clear"
			await _bild("%s_%s" % [v[0], z[0]])
			var e := {"id": v[0], "name": v[1], "zeit": z[0], "stunde": snappedf(main.hour(), 0.01), "sonne_el": snappedf(main.sun_el(), 0.1),
					"glow": _mod()._mood.get("glow", 0.0), "ok": r.get("ok", false)}
			liste.append(e)
			print("AUSSICHT ", e)
	var f := FileAccess.open(out + "liste.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(liste, " "))
	f.close()
	print("AUSSICHT fertig")
	quit(0)
