extends SceneTree
## Bilder «Frei erkunden mit eigener Figur» (Etappe 1): geduckt, kriechen, sitzen, schwimmen - das ganze Fenster mit Bedienung
## (Erkunden-Leiste, auf dem Handy die Knöpfe am Rand), dazu das Bild der Kopfkamera von MoveEye (_kopf). Unter Xvfb:
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1920x1920x24" <godot> --path . -s "$PWD/../werkzeuge/frei_erkunden_bilder.gd" \
##       -- --no-update --no-tour --aus <ordner/prefix_> [--handy]
## --handy: 390 × 844 Punkte mit Faktor 2 (780 × 1688 Pixel), die Touch-Knöpfe sichtbar; sonst PC 1280 × 720.

const Welt = preload("res://scripts/erkunden_welt.gd")

var main
var out := "/tmp/erkunden_"
var handy := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	handy = "--handy" in args
	if handy:
		DisplayServer.window_set_size(Vector2i(780, 1688))
		root.content_scale_factor = 2.0
	else:
		DisplayServer.window_set_size(Vector2i(1280, 720))
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _bild(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	img.save_png(out + name + ".png")
	var hc: Image = main.vps[0].get_texture().get_image() if main.vps.size() > 0 else null
	if hc != null:
		hc.save_png(out + name + "_kopf.png")
	print("BILD ", out + name + ".png ", img.get_size())


func _seitlich(p, k: float) -> void:
	"""the spring camera a little from the front side (standing still it stays there)"""
	p.regie.yaw = float(p.actor.heading) + k
	p.regie.pitch = 0.3
	p.regie.dist = 3.6
	p.regie.drag_t = p.uhr + 100.0
	p.regie.hinter_figur()
	p.regie.yaw = float(p.actor.heading) + k
	p.regie.drag_t = p.uhr + 100.0


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	main.news_popup = false
	main.set_scene("camping")
	await wait(4.0)
	if main.news != null and main.news.visible:
		main.news.visible = false                           # «Neu in dieser Version» (not part of these pictures)
	main.weather = "clear"
	main.set_hour(14.0)
	var ex = main.explore
	ex.frei_erkunden()
	var p = ex.person
	if handy:
		p.touch.forced = 1
		ex.device = "touch"
	await wait(1.0)
	# MoveEye looks at a free spot in front of it: the figure there, 7 m away
	var cam: Camera3D = main.cams[0]
	var fw := -cam.global_transform.basis.z
	fw.y = 0.0
	fw = fw.normalized()
	var at := Vector3.ZERO
	var frei_best := -1.0
	for dist in [6.0, 8.0, 10.0, 12.0, 14.0]:                # an open place in front of MoveEye (nothing within a few metres)
		for side in [0.0, -2.5, 2.5, -5.0, 5.0]:
			var q3: Vector3 = cam.global_position + fw * float(dist) + fw.cross(Vector3.UP) * float(side)
			var fr := 8.0
			for o in main._ob_near(Vector2(q3.x, q3.z)):
				fr = minf(fr, float(main._ob_closest(o, Vector2(q3.x, q3.z))[1]))
			if fr > frei_best + 0.3:
				frei_best = fr
				at = q3
	print("PLATZ frei %.1f m" % frei_best)
	p.place(at)
	var to_cam := cam.global_position - at
	p.figur.setzen(p.figur.pos(), atan2(to_cam.x, to_cam.z) + PI * 0.5)   # side-on to MoveEye
	await wait(0.5)
	# crouched
	p.set_haltung("geduckt")
	p.test_walk(Vector2(1, 0), 1.6, false)
	await wait(1.0)
	_seitlich(p, 2.1)
	await wait(0.7)
	await _bild("geduckt")
	# crawling
	p.set_haltung("kriechen")
	p.test_walk(Vector2(1, 0), 2.2, false)
	await wait(1.6)
	_seitlich(p, 2.1)
	await wait(0.7)
	await _bild("kriechen")
	p.set_haltung("stehen")
	await wait(0.8)
	# sitting: on a low thing (bench, stone) near the mover, else on the ground
	var best = null
	var bd := 40.0
	for o in main.obstacles:
		var ht := float(o.get("ht", 3.0))
		if ht >= 0.3 and ht <= 0.8 and not o.has("wasser"):
			var dd: float = (o["c"] as Vector2).distance_to(Vector2(main.rig.position.x, main.rig.position.z))
			if dd < bd:
				bd = dd
				best = o
	if best != null:
		var r: Array = main._ob_closest(best, (best["c"] as Vector2) + Vector2(2, 0))
		var q: Vector2 = (r[0] as Vector2) + (r[2] as Vector2) * 0.45
		p.place(Vector3(q.x, 0, q.y))
		await wait(0.4)
	p.set_haltung("sitzen")
	await wait(1.6)
	print("SITZ ", p.sitz)
	_seitlich(p, 2.6)
	await wait(0.6)
	await _bild("sitzen")
	p.set_haltung("stehen")
	# swimming: the Bergsee
	ex.set_on(false)
	main.set_scene("bergtal")
	var t0 := Time.get_ticks_msec()
	while (main.scene != "bergtal" or main.scenes.data.get("bergtal", null) == null) and Time.get_ticks_msec() - t0 < 90000:
		await process_frame
	await wait(5.0)
	main.weather = "clear"
	main.set_hour(14.0)
	var b = main.scenes.data.get("bergtal", null)
	if b != null:
		ex.frei_erkunden()
		if handy:
			p.touch.forced = 1
			ex.device = "touch"
		var lk: Array = b.LAKE1
		var c: Vector2 = lk[0]
		var spot := Vector3.ZERO
		for k in range(20):                                  # from the shore inwards: the first place 1.4 m deep
			var e := 0.98 - 0.03 * k
			var v := c + Vector2(float(lk[1]) * e, 0).rotated(float(lk[3]))
			var w: Vector3 = b.W(Vector3(v.x, 0, v.y))
			var wd: Dictionary = Welt.wasser(main, w)
			if float(wd.get("tiefe", 0.0)) > 1.4:
				spot = w
				break
		p.place(spot)
		var cw: Vector3 = b.W(Vector3(c.x, 0, c.y))
		var to_c := cw - spot
		p.figur.setzen(p.figur.pos(), atan2(-to_c.x, -to_c.z))
		await wait(0.6)
		p.test_walk(Vector2(1, 0), 2.5, false)
		await wait(2.0)
		print("SCHWIMMEN ", p.wasser, " y ", p.figur.y)
		_seitlich(p, 2.0)
		await wait(0.7)
		await _bild("schwimmen")
	quit(0)
