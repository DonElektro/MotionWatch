extends SceneTree
## Test «Frei erkunden mit eigener Figur», Etappe 4 (Besitzer 21.11.2026): Tageszeit und Wetter (Reiter «Welt»), Karte mit
## der Figur, Ort merken / weiter am gemerkten Ort (auch aus einer anderen Welt), Startpunkte anderer Spiele (Grossvater),
## Fotomodus (P, freie Kamera, Foto ohne Bedienung, Esc).
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/erkunden_extras_test.gd" -- --no-update --no-tour
## Ende: «Erkunden-Extras-Test OK» oder «SCRIPT ERROR: Erkunden-Extras-Test: …».

var main
var errs := []
var n_ok := 0


func ok(what: String, cond: bool) -> void:
	if cond:
		n_ok += 1
		print("  ok ", what)
	else:
		errs.append(what)
		print("  FEHLER ", what)


func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _ctl(d: Dictionary) -> Dictionary:
	return main._control(d)


func _key(code: int) -> void:
	for pressed in [true, false]:
		var k := InputEventKey.new()
		k.keycode = code
		k.physical_keycode = code
		k.pressed = pressed
		Input.parse_input_event(k)
		await process_frame


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false
	main.set_scene("camping")
	await wait(2.0)
	main.clear_obstacles()
	main.ex_ort = {}
	main.ex_startpunkte = {}
	var ex = main.explore
	_ctl({"action": "spielbereich", "do": "frei"})
	await wait(0.6)
	var p = ex.person
	ok("Frei erkunden", ex.person_on())
	# ---- time and weather ----
	var g = p.gestalten
	g.zeigen(true)
	g.druecke("reiter:welt")
	ok("Reiter Welt: Abend", g.druecke("zeit=Abend"))
	ok("Tageszeit 19:30", absf(main.hour() - 19.5) < 0.05)
	ok("Wetter Regen", g.druecke("wetter=rain") and str(main.weather) == "rain")
	g.druecke("wetter=clear")
	g.druecke("zeit=Mittag")
	g.zeigen(false)
	# ---- the map ----
	p.place(Vector3(12, 0, -7))
	await wait(0.3)
	var mm = main.get("minimap")
	if mm == null:
		mm = main.find_child("*minimap*", true, false)
	ok("Karte folgt der Figur", mm != null and Vector2(mm.center().x, mm.center().z).distance_to(Vector2(12, -7)) < 0.5)
	# ---- remember the place ----
	p.figur.setzen(Vector3(15, 0, -9), 1.0)
	await wait(0.2)
	var o: Dictionary = p.extras.ort_merken()
	ok("Ort gemerkt", str(o.get("scene", "")) == "camping" and absf(float(o["x"]) - 15.0) < 0.1)
	main._save_settings()
	var saved = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	ok("Ort in den Einstellungen", saved is Dictionary and saved.get("ex_ort", {}) is Dictionary and str(saved["ex_ort"].get("scene", "")) == "camping")
	ex.set_on(false)
	await wait(0.3)
	ex.frei_erkunden()
	await wait(0.4)
	ok("Frei erkunden beginnt am gemerkten Ort", Vector2(p.figur.pos().x, p.figur.pos().z).distance_to(Vector2(15, -9)) < 0.6)
	ex.set_on(false)
	main.set_scene("stellplatz")
	await wait(2.0)
	var sb = main.spielbereich
	var weiter: Array = sb._frei_weiter() if sb != null else []
	ok("Spielen: «Weiter am gemerkten Ort»", weiter.any(func(e): return str(e[0]) == "ort"))
	var r: Dictionary = _ctl({"action": "spielbereich", "do": "frei_ab", "id": "ort"})
	await wait(1.0)
	ok("aus einer anderen Welt: zurück zum Camping, am Ort (%s)" % str(main.scene), bool(r.get("ok", false)) and str(main.scene) == "camping" and Vector2(p.figur.pos().x, p.figur.pos().z).distance_to(Vector2(15, -9)) < 0.6)
	# ---- start points of other games ----
	ex.startpunkt_melden("grossvater_grat", "Grat beim Sonnenaufgang", "camping", Vector3(-20, 0, 18), 2.0)
	weiter = sb._frei_weiter() if sb != null else []
	ok("Startpunkt gemeldet, Spielen zeigt ihn", weiter.any(func(e): return str(e[0]) == "grossvater_grat"))
	ok("Startpunkt gespeichert", main.ex_startpunkte.has("grossvater_grat"))
	ex.frei_ab("grossvater_grat")
	await wait(0.5)
	ok("Frei erkunden ab dem Startpunkt", Vector2(p.figur.pos().x, p.figur.pos().z).distance_to(Vector2(-20, 18)) < 0.6)
	# ---- photo mode ----
	var cam0: Vector3 = main.view_cam.global_position
	await _key(KEY_P)
	await wait(0.4)
	ok("P: Fotomodus", bool(p.extras.foto_an))
	ex.dist += 8.0
	await wait(0.5)
	var d: float = main.view_cam.global_position.distance_to(p.figur.pos())
	ok("freie Kamera: weiter weg (%.1f m)" % d, d > 5.0)
	var p0: Vector3 = p.figur.pos()
	ex.test_drive = Vector2(1, 0)
	ex.test_until = main.now() + 1.0
	await wait(1.1)
	ok("Figur bleibt im Fotomodus stehen", p.figur.pos().distance_to(p0) < 0.1)
	if DisplayServer.get_name() != "headless":            # (headless: no renderer, no picture - frei_erkunden_bilder.gd checks it)
		var fp: String = await p.extras.foto()
		var img := Image.load_from_file(fp) if FileAccess.file_exists(fp) else null
		ok("Foto gespeichert (%s)" % fp, img != null and img.get_width() >= 320)
	await _key(KEY_ESCAPE)
	ok("Esc: Fotomodus aus, Erkunden bleibt", not bool(p.extras.foto_an) and ex.on)
	ex.set_on(false)
	if errs.is_empty():
		print("Erkunden-Extras-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Erkunden-Extras-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
