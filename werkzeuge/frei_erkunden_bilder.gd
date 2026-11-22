extends SceneTree
## Bilder «Frei erkunden mit eigener Figur» (Etappe 1): geduckt, kriechen, sitzen, schwimmen - das ganze Fenster mit Bedienung
## (Erkunden-Leiste, auf dem Handy die Knöpfe am Rand), dazu das Bild der Kopfkamera von MoveEye (_kopf). Unter Xvfb:
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1920x1920x24" <godot> --path . -s "$PWD/../werkzeuge/frei_erkunden_bilder.gd" \
##       -- --no-update --no-tour --aus <ordner/prefix_> [--handy]
## --handy: 390 × 844 Punkte mit Faktor 2 (780 × 1688 Pixel), die Touch-Knöpfe sichtbar; sonst PC 1280 × 720.
## --etappe2: «Figur gestalten» (Fenster offen, Vorschau), Begleiter (Maggie, Blinki) und das Auge «MoveEye sieht dich».
## --etappe3: Rucksack packen, Feldstecher (Reh mit Name und Distanz), Menü «Rucksack» mit Kompass / Uhr / Kraft, Lager.
## --etappe4: Reiter «Welt» (Tageszeit, Wetter, Ort), Fotomodus, «Spielen» mit «Weiter am gemerkten Ort».
## --kriechen: das Kriechen (Robben) von der Seite und von hinten, in Bewegung und still liegend (vorher / nachher).

const Welt = preload("res://scripts/erkunden_welt.gd")

var main
var out := "/tmp/erkunden_"
var handy := false
var etappe2 := false
var kriechen := false
var etappe := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	handy = "--handy" in args
	etappe2 = "--etappe2" in args
	kriechen = "--kriechen" in args
	etappe = 3 if "--etappe3" in args else (4 if "--etappe4" in args else 0)
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
	if etappe2:
		await _etappe2(ex, p)
		quit(0)
		return
	if kriechen:
		await _kriechen(p)
		quit(0)
		return
	if etappe == 3:
		await _etappe3(ex, p)
		quit(0)
		return
	if etappe == 4:
		await _etappe4(ex, p)
		quit(0)
		return
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
	var bd := 60.0
	for e in main.scenes.data.get("sitze", []):              # benches first, then stones (erkunden_welt.gd sitz)
		var dd: float = Vector2((e[0] as Vector3).x, (e[0] as Vector3).z).distance_to(Vector2(main.rig.position.x, main.rig.position.z)) + (0.0 if str(e[2]) == "bank" else 20.0)
		if dd < bd:
			bd = dd
			best = e
	print("SITZPLAETZE ", (main.scenes.data.get("sitze", []) as Array).size())
	if best != null:
		var sp: Vector3 = best[0]
		p.place(sp + Vector3(0.6, 0, 0))
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


func _etappe2(ex, p) -> void:
	"""«Figur gestalten» open on two tabs, then the figure with Maggie and Blinki in front of MoveEye (eye open)"""
	main.ex_figur = {"sex": "m", "alter": "erw", "haar": "kurz", "haarfarbe": "59260f", "bart": true, "jacke": "2e8c4d",
			"hose": "4d4733", "hut": "hut", "rucksack": true, "stoecke": true, "feldstecher": true}
	p.figur_setzen(main.ex_figur)
	await wait(0.6)
	ex.figur_gestalten(true)
	await wait(1.5)
	await _bild("gestalten_person")
	p.gestalten.druecke("reiter:kleider")
	await wait(1.0)
	await _bild("gestalten_kleider")
	p.gestalten.druecke("reiter:unterwegs")
	main.ex_maggie = true
	p.gestalten.druecke("reiter:unterwegs")
	await wait(1.0)
	await _bild("gestalten_unterwegs")
	ex.figur_gestalten(false)
	await wait(0.5)
	var cam: Camera3D = main.cams[0]
	var fw := -cam.global_transform.basis.z
	fw.y = 0.0
	fw = fw.normalized()
	p.test_walk(Vector2(1, 0), 2.5, false)
	await wait(2.6)
	_seitlich(p, 2.4)
	p.begleiter.sag(load("res://scripts/i18n.gd").t("Achtung, MoveEye sieht dich!"), 8.0)
	await wait(1.2)
	print("BEGLEITER ", p.begleiter.info())
	await _bild("begleiter")


func _kriechen(p) -> void:
	"""the belly crawl: side and back while moving (two moments of the cycle), lying still from the side"""
	p.set_haltung("kriechen")
	p.test_walk(Vector2(1, 0), 30.0, false)
	await wait(2.5)
	for k in [["seite_a", PI * 0.5], ["seite_b", PI * 0.5], ["hinten", 0.0]]:
		p.regie.yaw = float(p.actor.heading) + float(k[1])
		p.regie.pitch = 0.18
		p.regie.dist = 3.0
		p.regie.drag_t = p.uhr + 100.0
		await wait(0.35 if str(k[0]) == "seite_b" else 0.8)
		await _bild("kriechen_" + str(k[0]))
	print("KRIECHEN hoehe %.2f" % p.hoehe())
	p.test_walk(Vector2.ZERO, 0.1, false)
	await wait(2.0)
	p.regie.yaw = float(p.actor.heading) + PI * 0.5
	p.regie.drag_t = p.uhr + 100.0
	await wait(0.8)
	await _bild("kriechen_still")
	print("KRIECHEN still hoehe %.2f" % p.hoehe())


func _etappe3(ex, p) -> void:
	main.ex_rucksack = {"pack": "50", "n": {"stirnlampe": 1, "feldstecher": 1, "kompass": 1, "taschenuhr": 1, "essen": 3, "wasser": 2,
			"kocher": 1, "einmannzelt": 1, "sommerschlafsack": 1, "isomatte": 1, "seil": 1, "jacke": 1}}
	main.ex_kraft_echt = true
	ex.figur_gestalten(true)
	p.gestalten.druecke("reiter:rucksack")
	await wait(1.5)
	await _bild("rucksack_packen")
	ex.figur_gestalten(false)
	await wait(0.5)
	p.sachen.ort_merken()
	p.figur.setzen(p.figur.pos() + Vector3(6, 0, 6), float(p.actor.heading))
	p.sachen.kraft = 62.0
	p.sachen.durst = 35.0
	p.sachen.menu(true)
	await wait(1.0)
	await _bild("rucksack_menu")
	p.sachen.menu(false)
	var fw := Vector3(-sin(float(p.actor.heading)), 0, -cos(float(p.actor.heading)))
	var at: Vector3 = p.figur.pos() + fw * 35.0
	var deer = main.spawn("deer", at, at + Vector3(0.2, 0, 0.2))
	if deer != null:
		deer.speed = 0.0
	await wait(1.0)
	p.sachen.feldstecher(true)
	p.sachen.set_zoom(5.0)
	await wait(1.5)
	await _bild("feldstecher")
	p.sachen.tu_fernglas("nacht")
	await wait(0.6)
	await _bild("feldstecher_nacht")
	p.sachen.feldstecher(false)
	main.set_hour(21.5)
	await wait(0.5)
	p.sachen.lampe()
	await wait(0.8)
	await _bild("stirnlampe_nacht")
	p.sachen.uebernachten()
	await wait(1.5)
	_seitlich(p, 2.5)
	p.regie.dist = 5.0
	await wait(1.0)
	await _bild("lager_morgen")


func _etappe4(ex, p) -> void:
	ex.figur_gestalten(true)
	p.gestalten.druecke("reiter:welt")
	p.gestalten.druecke("zeit=Abend")
	await wait(1.5)
	await _bild("welt_reiter")
	p.gestalten.druecke("zeit=Mittag")
	ex.figur_gestalten(false)
	p.extras.ort_merken()
	ex.startpunkt_melden("grossvater_grat", "Grat beim Sonnenaufgang", str(main.scene), p.figur.pos() + Vector3(10, 0, 10), 0.0)
	p.extras.fotomodus(true)
	ex.dist += 4.0
	await wait(1.5)
	await _bild("fotomodus")
	var fp: String = await p.extras.foto()
	print("FOTO ", fp)
	var img := Image.load_from_file(fp) if fp != "" and FileAccess.file_exists(fp) else null
	if img != null:
		img.save_png(out + "fotomodus_foto.png")
	p.extras.fotomodus(false)
	ex.set_on(false)
	await wait(0.5)
	main.spielbereich.open()
	await wait(1.5)
	await _bild("spielen_weiter")
