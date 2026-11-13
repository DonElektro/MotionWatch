extends SceneTree
## Test «Als Person gehen» und «schneller Mover» (Besitzer 13.11.2026), ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/person_tempo_test.gd" -- --no-update --no-tour
## Prüft:
##   1. Erkunden: Mover -> Person -> Mover (Knopf, Taste U), die Person geht mit denselben Befehlen wie der Mover
##      (explore.command / rover_pad), der Mover bleibt dabei stehen, zurück im Mover bleibt die Person stehen,
##      main.walker_pos() ist die Person bzw. der Mover, die Ich-Sicht ist auf Augenhöhe der Person.
##   2. Tempo: die Stufen 1,8 / 3 / 5 / 7,5 / 10 m/s, Shift höchstens 10 m/s, der Mover fährt wirklich ≈ 10 m/s, fährt bei
##      10 m/s nicht durch eine dünne Wand - auch nicht, wenn ein Bild fast 1 s dauert (Schritte von 0,2 m in main._drive);
##      main.mover_max (MoveEye fährt) bleibt, wie es war; ex_speed bleibt in den Einstellungen.
##   3. Messung (Testlauf / Prüfstand): kein Knopf, eine laufende Person wird wieder zum Mover; mover_speed() = mover_max.
##   4. «Die Karte des Grossvaters»: der Knopf steht in der Abenteuer-Spalte, die Person geht mit der Gruppe mit (höchstens
##      110 m weg), geht selbst zum Steinmännchen (Fund + ein Zeichen des Geheimnisses «SEELI») und hebt beim Licht das
##      versteckte Tagebuchblatt auf; der Aussichtspunkt / «Hier übernachten» nehmen ihren Standort (walker_kind «person»).
## Ende: «Person-Tempo-Test OK» oder «SCRIPT ERROR: Person-Tempo-Test: …» (Exit-Code 0 / 1).

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


func _key(code: int) -> void:
	for pressed in [true, false]:
		var k := InputEventKey.new()
		k.keycode = code
		k.physical_keycode = code
		k.pressed = pressed
		Input.parse_input_event(k)
		await process_frame


func _xz(n: Node3D) -> Vector2:
	return Vector2(n.global_position.x, n.global_position.z)


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false                                  # headless: nobody looks - the world must still move
	main.set_scene("camping")
	await wait(2.0)
	main.clear_obstacles()                                 # an open place (the walking itself is checked, not the caravan)
	main.home_pos = Vector3.ZERO
	main.mover_home()
	var ex = main.explore
	var mm0: float = main.mover_max
	# ---- 1. Mover -> Person -> Mover ----
	ex.set_on(true)
	await wait(0.3)
	ok("Erkunden an", ex.on and main.mover_on)
	ok("Knopf «Person» sichtbar", ex._btn_person.visible and ex._btn_person.text.find(ex.T.t("Person")) >= 0)
	ok("Knopf «Tempo» sichtbar", ex._btn_speed.visible)
	var rig0 := _xz(main.rig)
	ex._btn_person.pressed.emit()
	await wait(0.3)
	ok("Person an (Knopf)", ex.person_on() and ex.person.actor != null)
	ok("Knopf heisst jetzt «Mover»", ex._btn_person.text.find(ex.T.t("Mover")) >= 0)
	ok("walker_pos = Person", main.walker_kind() == "person" and (main.walker_pos() as Vector3).distance_to(ex.person.actor.global_position) < 0.01)
	var a: Node3D = ex.person.actor
	ok("Person neben dem Mover", _xz(a).distance_to(rig0) < 3.0)
	ok("Person ist ein gesteuerter Wanderer (actor.gd)", bool(a.get("controlled")) and str(a.get("kind")) == "person")
	var p0 := _xz(a)
	ex.test_drive = Vector2(1, 0)                         # W (explore.command -> rover_pad -> Person)
	ex.test_until = main.now() + 2.5
	await wait(2.6)
	var p1 := _xz(a)
	print("  Person ging %.2f m, Mover %.2f m" % [p1.distance_to(p0), _xz(main.rig).distance_to(rig0)])
	ok("Person geht vorwärts (W)", p1.distance_to(p0) > 1.5)
	ok("Mover bleibt stehen, solange die Person geht", _xz(main.rig).distance_to(rig0) < 0.05)
	ex.test_drive = Vector2(0, 1)                         # D: drehen
	ex.test_until = main.now() + 0.6
	var y0: float = ex.person.yaw
	await wait(0.7)
	ok("Person dreht (D)", absf(wrapf(ex.person.yaw - y0, -PI, PI)) > 0.5)
	ex.view = "driver"
	await wait(0.3)
	var eye_d: float = main.view_cam.global_position.y - a.global_position.y
	ok("Ich-Sicht auf Augenhöhe (%.2f m)" % eye_d, absf(eye_d - 1.62) < 0.2)
	ex.view = "chase"
	await _key(KEY_U)
	await wait(0.2)
	ok("Taste U: zurück im Mover", not ex.person_on() and ex.on)
	var pp := _xz(a)
	ex.test_drive = Vector2(1, 0)
	ex.test_until = main.now() + 1.5
	await wait(1.6)
	ok("Person bleibt stehen, wo sie war", is_instance_valid(a) and _xz(a).distance_to(pp) < 0.05)
	ok("Mover fährt wieder", _xz(main.rig).distance_to(rig0) > 1.0)
	ok("walker_pos = Mover", main.walker_kind() == "rover")
	await _key(KEY_U)
	await wait(0.2)
	ok("Taste U: wieder Person, an derselben Stelle", ex.person_on() and ex.person.actor == a and _xz(a).distance_to(pp) < 0.3)
	ex.set_person(false)
	# ---- 2. the speed ----
	ok("Tempo-Stufen", str(ex.SPEEDS) == str([1.8, 3.0, 5.0, 7.5, 10.0]))
	ex.set_speed(1.8)
	var seen := []
	for i in range(5):
		ex.speed_step(1, true)
		seen.append(main.ex_speed)
	ok("Knopf Tempo geht durch alle Stufen (%s)" % str(seen), str(seen) == str([3.0, 5.0, 7.5, 10.0, 1.8]))
	ex.set_speed(10.0)
	ok("Tempo 10 m/s", is_equal_approx(ex.drive_speed(), 10.0))
	ex.turbo = true
	ok("Shift: höchstens 10 m/s", ex.drive_speed() <= 10.0)
	ex.set_speed(3.0)
	ok("Shift auf 3 m/s = 6,6 m/s", is_equal_approx(ex.drive_speed(), 6.6))
	ex.turbo = false
	ex.set_speed(10.0)
	main._save_settings()
	var saved = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	ok("Tempo bleibt in den Einstellungen", saved is Dictionary and is_equal_approx(float(saved.get("ex_speed", 0.0)), 10.0))
	# a free track: no obstacles, a thin wall 60 m ahead
	main.clear_obstacles()
	main.add_obstacle_box(Vector3(0, 0, -60), 12.0, 0.1, 0.0)
	main.rig.position = Vector3(0, main.ground_y(0, 0), 0)
	main.rig.rotation = Vector3.ZERO
	main.avoid_on = true
	ex.test_drive = Vector2(1, 0)
	ex.test_until = main.now() + 12.0
	await wait(2.0)
	var t1: float = main.now()
	var z1: float = main.rig.position.z
	await wait(2.0)
	var v: float = absf(main.rig.position.z - z1) / (main.now() - t1)
	print("  Mover bei Tempo 10: %.2f m/s" % v)
	ok("Mover fährt etwa 10 m/s (%.1f)" % v, v > 8.5 and v < 10.5)
	await wait(5.0)
	var zw: float = main.rig.position.z
	print("  vor der Wand: z = %.2f (Wand bei -60)" % zw)
	ok("Mover fährt bei 10 m/s nicht durch die Wand", zw > -60.0 and zw < -58.0)
	# a frame of almost 1 s right in front of the wall (before: one jump of 10 m, straight through)
	main.rig.position = Vector3(0, 0, -52.0)
	main.pad_on = true
	main.pad_drive = Vector2(1, 0)
	main._pad_l = 1.0
	main._pad_r = 1.0
	main._drive_t = main.now() - 0.95
	main._drive(0.016)
	print("  nach einem Bild von 0,95 s: z = %.2f" % main.rig.position.z)
	ok("auch ein langes Bild fährt nicht durch die Wand", main.rig.position.z > -60.0)
	ex.test_until = 0.0
	ok("Drehen bleibt wie bei 2 m/s", is_equal_approx(minf(main.mover_speed(), main.MOVER_TURN_V), 2.0))
	ex.set_on(false)
	await wait(0.2)
	ok("Erkunden aus: die Person ist weg", ex.person.actor == null)
	ok("mover_max (MoveEye fährt) unverändert", is_equal_approx(main.mover_max, mm0))
	ok("ohne Erkunden: mover_speed = mover_max", is_equal_approx(main.mover_speed(), main.mover_max))
	# ---- 3. a measurement ----
	ex.set_on(true)
	ex.set_person(true)
	await wait(0.2)
	main.testrun.running = true                           # (only for this frame: as if a test run had started)
	ok("Testlauf: why_not", ex.Person.why_not(main) != "")
	ex._process(0.016)
	ok("Testlauf: zurück im Mover", not ex.person_on())
	ok("Testlauf: kein Knopf", not ex._btn_person.visible)
	ex.set_person(true)
	ok("Testlauf: Person geht nicht", not ex.person_on())
	main.testrun.running = false
	main.pruef.running = true
	ok("Prüfstand: why_not", ex.Person.why_not(main) != "")
	main.pruef.running = false
	ex._process(0.016)
	ok("nach der Messung: Knopf wieder da", ex._btn_person.visible)
	ex.set_on(false)
	# ---- 4. the story ----
	var ab = main.abenteuer
	ok("Abenteuer da", ab != null)
	ex.set_on(true)                                       # (Erkunden first: no cut scene flies the view)
	ab.op({"do": "start", "chapter": 1, "mood": "abenteuerlich", "level": "mittel", "goal": "dunkel", "season": "sommer", "pack": "50", "seed": 4711})
	var t0 := Time.get_ticks_msec()
	while (main.scene != "bergtal" or int(ab.step) != 4 or ab.bt() == null) and Time.get_ticks_msec() - t0 < 60000:
		await process_frame
	ok("Geschichte unterwegs (Schritt 4, Bergtal)", int(ab.step) == 4 and main.scene == "bergtal")
	if not ex.on:
		ex.set_on(true)
	await wait(1.0)
	ab.leg = {}                                            # the group stands (as at a question)
	ab.R["walking"] = false
	ab._changed()
	await wait(0.5)
	var pb = ab.body.find_child("person_btn", true, false)
	ok("Knopf «Person» in der Abenteuer-Spalte", pb != null)
	if pb != null:
		pb.pressed.emit()
	else:
		ex.set_person(true)
	await wait(0.3)
	ok("Person in der Geschichte", ex.person_on() and ex.person.story() != null)
	var g = ab.geheim
	var b = ab.bt()
	var sq: Vector2 = g.stein_xz(1)
	ab.R["pos"] = sq + Vector2(20, 0)                     # the group stands 20 m from the stone man of chapter 1
	await wait(0.4)
	ok("Person geht mit der Gruppe mit", (ex.person.valley_pos() as Vector2).distance_to(ab.R["pos"]) < 8.0)
	ok("Steinmännchen 1 noch nicht gefunden", not g.S()["steine"].has("1"))
	var start_q: Vector2 = sq + Vector2(7, 0)
	ex.person.place(b.WG(start_q.x, start_q.y))
	await wait(0.1)
	var w_from: Vector3 = ex.person.actor.global_position
	var w_to: Vector3 = b.WG(sq.x, sq.y)
	ex.person.yaw = atan2(-(w_to.x - w_from.x), -(w_to.z - w_from.z))
	ex.person.actor.heading = ex.person.yaw
	ex.person.test_walk(Vector2(1, 0), 6.0, false)        # walks there itself
	var t2 := Time.get_ticks_msec()
	while not g.S()["steine"].has("1") and Time.get_ticks_msec() - t2 < 8000:
		await process_frame
	print("  Person beim Steinmännchen: %.1f m" % (ex.person.valley_pos() as Vector2).distance_to(sq))
	ok("Person findet das Steinmännchen (Zeichen «S» von SEELI)", str(g.S()["steine"].get("1", "")) == "S")
	ok("Zeichen im Rätsel: %s" % g.zeichen(), g.zeichen().begins_with("S"))
	# the hidden diary page at the light (as if MoveEye had recorded it in a night)
	g.S()["blatt"] = false
	var lq: Vector2 = sq + Vector2(-30, 10)
	g.S()["licht"] = {"x": lq.x, "z": lq.y, "gesehen": true, "ch": 1}
	g._root_key = ""                                      # (the reflector is built with the next frame of geheim)
	await wait(0.8)
	ab.R["pos"] = lq + Vector2(15, 5)
	ab.R["pending"] = {}
	await wait(0.3)
	ex.person.place(b.WG(lq.x + 1.5, lq.y))
	var t3 := Time.get_ticks_msec()
	while not bool(g.S()["blatt"]) and Time.get_ticks_msec() - t3 < 4000:
		await process_frame
	ok("Person hebt das versteckte Tagebuchblatt auf", bool(g.S()["blatt"]))
	ok("… und es steht im Tagebuch", (ab.R["log"] as Array).any(func(e): return str(e.get("title", "")) == ab.T.t("Ein verstecktes Tagebuchblatt")))
	# the leash: not further than 110 m from the group
	ex.person.place(b.WG(ab.R["pos"].x + 300.0, ab.R["pos"].y))
	await wait(0.3)
	var dl: float = (ex.person.valley_pos() as Vector2).distance_to(ab.R["pos"])
	ok("höchstens 110 m von der Gruppe (%.0f m)" % dl, dl <= 110.5)
	ok("Spieler-Standort in der Welt = Person", main.walker_kind() == "person")
	ab.R["pending"] = {}
	ex.person.place(b.WG(ab.R["pos"].x + 2.0, ab.R["pos"].y))   # back beside the group (on the path)
	await wait(0.2)
	var ph: Dictionary = b.pick_here()
	print("  Hier übernachten: ", ph)
	var vpp: Vector2 = ex.person.valley_pos()
	var sl_here: float = snappedf(b.ground_slope(vpp.x, vpp.y), 0.1)
	ok("«Hier übernachten» prüft den Platz der Person", str(ph.get("from", "")) == "person" or (ph.has("slope") and absf(float(ph["slope"]) - sl_here) < 0.3))
	# back into the mover: the person stays
	ex.set_person(false)
	await wait(0.2)
	ok("Geschichte: zurück im Mover", not ex.person_on() and ex.person.actor != null)
	ok("ohne Person zählt sie nicht", g.walkers().is_empty())
	ex.set_on(false)
	ab.op({"do": "close"})
	if errs.is_empty():
		print("Person-Tempo-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Person-Tempo-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
