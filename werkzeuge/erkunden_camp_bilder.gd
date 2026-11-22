extends SceneTree
## Bilder «Camp aufstellen» beim Frei erkunden (Besitzer 22.11.2026): ruhiger Bildschirm vorher / nachher, Vorschau grün / rot,
## das Camp mit Feuer am Abend, die Wahl der Nacht, der Bericht am Morgen. Unter Xvfb:
##   cd simulator3d && HOME=<test-home> xvfb-run -s "-screen 0 1920x1920x24" <godot> --path . -s "$PWD/../werkzeuge/erkunden_camp_bilder.gd" \
##       -- --no-update --no-tour --aus <ordner/prefix_> [--handy]
## --handy: 390 × 844 Punkte mit Faktor 2 (780 × 1688 Pixel), die Touch-Knöpfe sichtbar; sonst PC 1280 × 720.

const RS = preload("res://scripts/erkunden_rucksack.gd")

var main
var out := "/tmp/camp_"
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
	print("BILD ", out + name + ".png ", img.get_size())


func _blick(p, von: Vector3, auf: Vector3) -> void:
	"""the figure at von, looking at auf; the spring camera behind it"""
	p.place(von)
	var to := auf - von
	p.figur.setzen(p.figur.pos(), atan2(-to.x, -to.z))
	p.regie.hinter_figur()


func _run() -> void:
	await wait(3.0)
	main.eco_idle = false
	main.news_popup = false
	main.set_scene("camping")
	await wait(4.0)
	if main.news != null and main.news.visible:
		main.news.visible = false
	main.weather = "clear"
	main.set_hour(16.0)
	main.ex_rucksack = RS.norm({"pack": "70", "n": {"kuppelzelt": 1, "isomatte": 1, "sommerschlafsack": 1, "zuendhoelzer": 1, "kocher": 1,
			"ministativ": 1, "powerbank": 1, "stuhl": 1, "waescheleine": 1, "stirnlampe": 1, "essen": 2}})
	var ex = main.explore
	ex.frei_erkunden()
	var p = ex.person
	var cp = p.camp
	cp.datei = "user://erkunden_camp_bilder.json"
	if handy:
		p.touch.forced = 1
		ex.device = "touch"
	await wait(1.0)
	# an open place: a few metres beside the mover
	var c0: Vector3 = main.rig.global_position + main.rig.global_transform.basis.x * 9.0
	c0 = main.free_spot(c0, 4.0, true)
	c0.y = main.ground_y(c0.x, c0.z)
	print("PLATZ ", c0)
	# ---- the clean screen: before (as until now) / after ----
	var ru = p.ruhe
	_blick(p, c0 + Vector3(0, 0, 4.0), c0)
	await wait(0.6)
	ru.menu_zeigen = true
	ru.aus()
	await wait(0.5)
	await _bild("ruhe_vorher")
	ru.menu_zeigen = false
	await wait(0.6)
	print("RUHE ", ru.info())
	await _bild("ruhe_nachher")
	# ---- preview: green ----
	_blick(p, c0 + Vector3(0, 0, 4.0), c0)
	await wait(0.4)
	cp.vorschau_start("kuppelzelt")
	await wait(0.8)
	print("VORSCHAU ", cp.info()["platz"])
	await _bild("vorschau_gruen")
	cp.aufstellen()
	await wait(1.4)
	await _bild("aufbauen")
	await wait(3.5)
	# ---- preview: red (the fire right beside the tent: sparks) ----
	var zp: Vector3 = cp._ding_pos("kuppelzelt")
	_blick(p, zp + Vector3(4.2, 0, 2.0), zp + Vector3(0, 0, 0.6))
	await wait(0.4)
	cp.vorschau_start("feuerstelle")
	await wait(0.8)
	print("VORSCHAU ", cp.info()["platz"])
	await _bild("vorschau_rot")
	cp.vorschau_ende()
	# ---- the camp with the fire, in the evening ----
	cp.setzen("feuerstelle", zp + Vector3(5.2, 0, 0.5), 0.0)
	cp.setzen("stuhl", zp + Vector3(5.0, 0, 2.6), PI * 0.8)
	cp.setzen("kocher", zp + Vector3(3.2, 0, 2.6), 0.0)
	cp.setzen("rucksack", zp + Vector3(2.1, 0, 2.0), 0.4)
	cp.setzen("stirnlampe", zp + Vector3(-1.8, 0, 2.0), 0.0)
	cp.setzen("waescheleine", zp + Vector3(1.0, 0, -3.2), 0.0)
	cp.setzen("moveeye", zp + Vector3(7.4, 0, 3.4), 0.0)
	cp.anzuenden()
	cp.nachlegen()
	main.set_hour(20.6)
	_blick(p, zp + Vector3(8.0, 0, 7.5), zp + Vector3(2.5, 0, 0.5))
	await wait(1.2)
	cp.menu(true)
	await wait(0.4)
	await _bild("camp_menu")
	cp.menu(false)
	await wait(0.4)
	await _bild("camp_feuer")
	# ---- the night: lying down at the tent ----
	main.set_hour(22.5)
	p.place(zp + Vector3(1.2, 0, 2.2))
	await wait(0.3)
	p.set_haltung("liegen")
	await wait(0.8)
	await _bild("nacht_wahl")
	cp.nacht_spulen()
	await wait(0.8)
	await _bild("morgen_bericht")
	cp._dlg_zu()
	cp.loeschen()
	cp._feuer_tick(60.0)
	cp.einpacken("*")
	quit(0)
