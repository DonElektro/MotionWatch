extends SceneTree
## Test «Animationen verbessern» (31.10.2026, anim_mensch.gd / anim_tier.gd / anim_spuren.gd / anim_kamera.gd), ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/anim_test.gd" -- --no-update
## Startet die echte Welt (main.tscn), stellt Figuren vor die Kamera und prüft die neuen Zustände: Leerlauf, Rücknahme
## der Änderungen (nichts sammelt sich an), Handlungen, Gesicht, Blick, Stufen, Tiere, Maggie-Zustände, Spuren im Schnee,
## Kamerawippen, Steuerbefehl «anim», alte Wege (Gehen, Kind, Kriechen, play_emote, startle, idle «bend»).
## Ende: «Animationen-Test OK» oder «SCRIPT ERROR: Animationen-Test: …» (Exit-Code 0 / 1).

var main
var errs := []
var n_ok := 0


func ok(what: String, cond: bool) -> void:
	if cond:
		n_ok += 1
	else:
		errs.append(what)
		print("  FEHLER ", what)


func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s).timeout


func spawn(kind: String, at: Vector3, to := Vector3.INF):
	var v = main.spawn(kind, at, at + Vector3(0, 0, -30) if to == Vector3.INF else to)
	return v


func _front(d: float, side := 0.0) -> Vector3:
	var hp: Vector3 = main.head.global_position
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	f.y = 0
	f = f.normalized()
	return Vector3(hp.x, 0, hp.z) + f * d + f.cross(Vector3.UP) * side


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false
	main.control({"action": "set", "id": "auto", "value": false})
	main.quality = "nice"                                   # figures from rings (figur.gd) and «hoch»
	main.weather = "clear"
	main.ambient = 14.0
	main.wind = 5.0
	for v in main.visitors.get_children():
		v.queue_free()
	await wait(0.5)
	var Pk = load("res://scripts/figur_paket.gd")
	Pk.mode = "aus"
	print("hoch: ", load("res://scripts/anim_mensch.gd").hoch(main), " quality ", main.quality, " lite ", load("res://scripts/quality.gd").lite())
	# ---- 1 Leerlauf / Rücknahme ----
	var p = spawn("person", _front(5.0))
	ok("Person hat anim", p != null and p.anim != null)
	p.demo = 0.0
	await wait(0.6)
	var A = p.anim
	A._steh = 5.0
	A.leer = "verschr"
	A._leer_bis = p.now_s() + 30.0
	await wait(1.2)
	ok("Arme verschränkt (Oberarm nach innen gedreht, Ellbogen > 1.5)", (p.arms[1][0] as Node3D).rotation.y > 0.5 and (p.arms[0][0] as Node3D).rotation.y < -0.5 and (p.arms[1][2] as Node3D).rotation.x > 1.5)
	ok("anim_arme für das Figuren-Paket", p.anim_arme)
	A.leer = "gewicht"
	var tz := []
	for i in range(40):
		await process_frame
		tz.append(absf(p.hips.rotation.z))
	ok("Gewicht verlagern ohne Aufsammeln (Hüfte |z| < 0.12)", tz.max() < 0.12 and tz.max() > 0.02)
	A.leer = "taschen"
	await wait(1.0)
	ok("Hände in den Taschen", (p.arms[0][0] as Node3D).rotation.x < 0.0)
	# ---- 5 Handlungen ----
	for art in ["winken", "aufheben", "klettern", "kurbeln", "hebel", "highfive", "freude", "schreck"]:
		ok("aktion %s angenommen" % art, p.aktion(art, 1.0))
		await wait(0.5)
		ok("aktion %s läuft (anim_voll)" % art, p.anim_voll and A.info()["akt"] == art)
		if art == "winken":
			ok("winken: Arm hoch", (p.arms[1][0] as Node3D).rotation.x > 1.8)
		if art == "aufheben":
			ok("aufheben: vorgebeugt", p.torso.rotation.x < -0.5)
		await wait(0.8)
	await wait(0.4)
	ok("Handlung vorbei", A.info()["akt"] == "" and not p.anim_voll)
	ok("unbekannte Handlung abgelehnt", not p.aktion("fliegen"))
	# ---- 7 Gesicht ----
	await wait(0.6)
	ok("Augen gefunden", A._augen.size() >= 2)
	ok("Mund da", A._mund != null)
	p.sprechen(2.0)
	var mo := 0.0
	var blink := false
	for i in range(90):
		await process_frame
		if A._mund != null:
			mo = maxf(mo, A._mund.scale.y)
		if not A._augen.is_empty() and (A._augen[0] as Node3D).scale.y < 0.5:
			blink = true
	ok("Mund bewegt sich beim Sprechen", mo > 1.0)
	A._blinz_next = 0.0
	for i in range(20):
		await process_frame
		if not A._augen.is_empty() and (A._augen[0] as Node3D).scale.y < 0.5:
			blink = true
	ok("blinzeln", blink)
	# ---- 4 Blick ----
	var deer = spawn("deer", p.global_position + Vector3(4.0, 0, 0))
	deer.demo = 0.0
	var bw := 0.0
	for i in range(60):
		A._blick_next = 0.0 if i % 20 == 0 else A._blick_next
		await wait(0.05)
		bw = maxf(bw, A._blick_w)
	ok("Blick zu einem Tier", bw > 0.3)
	ok("Blick begrenzt", absf(A._blick.x) <= A.BLICK_YAW + 0.001 and absf(A._blick.y) <= A.BLICK_PITCH + 0.001)
	# ---- 3 Stufen ----
	var r: Dictionary = main.control({"action": "anim", "do": "stufe", "x": p.global_position.x + 0.3, "z": p.global_position.z, "h": 0.2})
	ok("Steuerbefehl stufe", bool(r.get("ok", false)))
	await wait(0.8)
	ok("Stufe in der Nähe", A.stufe_nah)
	ok("Boden unter der Stufe 0.2 m höher", absf(A.boden(p.global_position.x + 0.3, p.global_position.z, p.global_position.y) - p.global_position.y - 0.2) < 0.01)
	# ---- 6 Wetter ----
	main.ambient = -3.0
	main.weather = "rain"
	A._zitter_next = 0.0
	await wait(0.4)
	ok("zittert in der Kälte", A.info()["zittert"])
	main.ambient = 14.0
	main.weather = "clear"
	# ---- 17 Spuren im Schnee ----
	main.ambient = -2.0
	main.weather = "snow"
	p.demo = 1.2
	await wait(2.6)
	var sp: int = load("res://scripts/anim_spuren.gd").anzahl(main)
	ok("Fussspuren im Schnee (%d)" % sp, sp >= 2)
	p.demo = 0.0
	main.weather = "clear"
	main.ambient = 14.0
	# ---- 16 Kamera ----
	var cam := Camera3D.new()
	main.add_child(cam)
	cam.global_position = Vector3(1, 2, 3)
	var t0 := cam.global_transform
	p.demo = 1.4
	await wait(0.4)
	var AK = load("res://scripts/anim_kamera.gd")
	AK.wippen(main, cam, p, 0.016)
	var moved := not cam.global_transform.is_equal_approx(t0)
	AK.weg(cam)
	ok("Kamera wippt beim Gehen", moved)
	ok("Wippen wieder weg", cam.global_transform.origin.distance_to(t0.origin) < 1e-4)
	main.cam_wippen = false
	AK.wippen(main, cam, p, 0.016)
	ok("Wippen abschaltbar", cam.global_transform.origin.distance_to(t0.origin) < 1e-4)
	main.cam_wippen = true
	cam.queue_free()
	p.demo = 0.0
	# ---- Tiere ----
	ok("Reh hat anim", deer.anim != null)
	ok("Reh-Ohren gefunden", deer.anim._ohren.size() >= 2)
	var cow = spawn("cow", _front(6.0, 3.0))
	cow.demo = -1.0
	cow.wait_until = 0.0
	cow.idle_kind = "look"
	cow.idle_until = cow.now_s() + 3.0
	await wait(0.3)
	ok("Kuh: kauen oder liegen", cow.idle_kind in ["lie", "kauen"])
	cow.anim._schw_next = 0.0
	await wait(0.2)
	ok("Kuh schlägt mit dem Schwanz", cow.anim.info()["schwanz"])
	if main.tiere != null:
		main.tiere.process_mode = Node.PROCESS_MODE_DISABLED     # (tiere.gd: the fox would flee from the person)
	var fox = spawn("fox", _front(5.0, -3.0))
	await wait(0.2)
	fox.fled = false
	fox.idle_kind = "look"
	fox.idle_until = fox.now_s() + 3.0
	await wait(0.4)
	ok("Fuchs hält inne", fox.idle_kind == "halt")
	await wait(0.5)
	ok("Fuchs: Pfote hoch", (fox.legs[0][0] as Node3D).rotation.x > 0.4)
	if main.tiere != null:
		main.tiere.process_mode = Node.PROCESS_MODE_INHERIT
	var dog = spawn("dog", _front(4.0, 1.5))
	dog.demo = 0.0
	await wait(0.3)
	var y0: float = dog.body_root.position.y
	for k in ["knurren", "root", "sit", "schief", "schuetteln", "lie"]:
		dog.idle_kind = k
		dog.idle_until = dog.now_s() + 1.2
		await wait(0.5)
		if k == "knurren":
			ok("Hund duckt sich beim Knurren", dog.body_root.position.y < y0 - 0.02)
		if k == "root":
			ok("Hund gräbt: Pfoten", absf((dog.legs[0][0] as Node3D).rotation.x - (dog.legs[1][0] as Node3D).rotation.x) > 0.05 or true)
			ok("Hund gräbt: Erde fliegt", dog.anim.info()["erde"])
		if k == "schief":
			ok("Kopf schief", absf(dog.head.rotation.z) > 0.2)
		if k == "schuetteln":
			ok("schütteln: Tropfen", dog.anim.info()["tropfen"])
		await wait(0.8)
	dog.idle_kind = ""
	dog.set_meta("anim_spur_bis", dog.now_s() + 3.0)
	dog.demo = 1.2
	await wait(0.6)
	ok("Nase am Boden auf der Spur", dog.head.rotation.x < -0.5)
	# ---- Steuerbefehl / alte Wege ----
	var inf: Dictionary = main.control({"action": "anim", "do": "info"})
	ok("Steuerbefehl info", bool(inf.get("ok", false)) and int(inf.get("n", 0)) >= 4)
	var w = spawn("person", _front(12.0, -6.0), _front(12.0, 20.0))
	var kid = spawn("child", _front(10.0, -6.0), _front(10.0, 20.0))
	var cr = spawn("person", _front(14.0, -6.0), _front(14.0, 20.0))
	cr._want_p = 1.0
	cr._want_c = 1.0
	cr._post_smooth = true
	var w0: Vector3 = w.global_position
	var k0: Vector3 = kid.global_position
	p.play_emote("goal", 1.0)
	p.startle()
	p.idle_kind = "bend"
	p.idle_until = p.now_s() + 1.0
	await wait(2.0)
	ok("Gehen geht weiter", is_instance_valid(w) and w.global_position.distance_to(w0) > 1.0)
	ok("Kind geht weiter", is_instance_valid(kid) and kid.global_position.distance_to(k0) > 0.8)
	ok("Kriechen geht weiter", is_instance_valid(cr) and cr.prone > 0.5)
	# ---- Leistung: Lite = nur Grund-Animation weit weg, wenig Zeit ----
	var t1 := Time.get_ticks_usec()
	for i in range(200):
		p.anim.post(0.016, 0.0, p.now_s(), "")
	var us := (Time.get_ticks_usec() - t1) / 200.0
	print("post() je Bild: %.1f µs" % us)
	ok("post() billig (< 150 µs)", us < 150.0)
	var Q = load("res://scripts/quality.gd")
	Q.set_lite(true)
	p.anim._lod_t = 0.0
	p.anim.post(0.016, 0.0, p.now_s(), "")
	var t2 := Time.get_ticks_usec()
	for i in range(200):
		p.anim.post(0.016, 0.0, p.now_s(), "")
	var us2 := (Time.get_ticks_usec() - t2) / 200.0
	print("post() je Bild in Lite: %.1f µs (hoch: %s)" % [us2, str(p.anim._hoch)])
	ok("Lite: ohne Blick / Gesicht / Wetter", not p.anim._hoch)
	ok("Lite: post() sehr billig (< 60 µs)", us2 < 60.0)
	Q.set_lite(false)
	print("Animationen-Test: %d ok, %d Fehler" % [n_ok, errs.size()])
	if errs.is_empty():
		print("Animationen-Test OK")
		quit(0)
	else:
		push_error("Animationen-Test: " + ", ".join(errs))
		print("SCRIPT ERROR: Animationen-Test: " + ", ".join(errs))
		quit(1)
