extends SceneTree
## Test «Privatsphäre am Platz» und die neuen Einbruch-Abläufe (Wünsche Nr. 2 und 3, 07.11.2026), ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/privatplatz_test.gd" -- --no-update --no-tour --port 9463
## Prüft auf dem Campingplatz: der private Kreis (MoveEye + eigenes Zelt), normale Besucher queren ihn nie (gerade Wege durch
## die Mitte werden umgelenkt, kommen trotzdem ans Ziel), über einige simulierte Minuten mit Besuch von selbst betritt kein
## markierter Besucher den Kreis; Ausnahmen (Einbrecher, Grillabend …) werden nicht markiert; ohne Markierung (Tests,
## Proben) bleibt der Weg wie bisher (geht mitten durch). Einbruch-Abläufe «zelt_runde» und «velo_weg»: anderer Seed =
## anderer Ablauf, beide laufen bis zum Schluss, der Dieb betritt den Kreis, die Beute ist weg.
## Ende: «Privatplatz-Test OK» oder «SCRIPT ERROR: Privatplatz-Test: …» (Exit-Code 0 / 1).

var main
var errs := []
var n_ok := 0
const TS := 4.0                    # Engine.time_scale: the visitors walk 4 × faster (the waits of the runs stay real time)


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
	await create_timer(s, true, false, true).timeout       # real seconds (ignore_time_scale)


func _d(v, c: Vector2) -> float:
	return Vector2(v.position.x, v.position.z).distance_to(c)


func _clear() -> void:
	for v in main.visitors.get_children():
		v.queue_free()


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false
	main.auto_visitors = false
	main.set_scene("camping")
	await wait(3.0)
	main.auto_visitors = false
	main.weather = "clear"
	main.set_hour(14.0)
	_clear()
	await wait(0.5)
	var P = main.privat
	ok("privatplatz.gd geladen", P != null)
	var z: Array = P.zone()
	var c: Vector2 = z[0]
	var r: float = float(z[1])
	var dev := Vector2(main.home_pos.x, main.home_pos.z)
	var tent3: Vector3 = main.obj["pir"]
	print("Kreis: Mitte %s, Radius %.2f m, Zelt %s" % [c, r, tent3])
	ok("Kreis enthält MoveEye", dev.distance_to(c) < r - 1.0)
	ok("Kreis enthält das eigene Zelt", Vector2(tent3.x, tent3.z).distance_to(c) < r - 1.0)
	ok("Steuerbefehl privat", bool(main.control({"action": "privat"}).get("ok", false)))
	# ---- 1 straight lines through the middle: marked persons go round, unmarked ones (tests, probes) as before ----
	Engine.time_scale = TS
	var marked := []
	var plain := []
	for k in range(4):
		var a := deg_to_rad(20.0 + 45.0 * k)
		var dv := Vector2(cos(a), sin(a))
		var p0 := c - dv * 22.0
		var p1 := c + dv * 22.0
		P.ctx += 1
		var v = main.spawn("person", Vector3(p0.x, 0, p0.y), Vector3(p1.x, 0, p1.y))
		P.ctx -= 1
		v.set_meta("privat_test", true)                       # statisten.gd: no goals on the way (only plain visitors get them)
		v.next_idle = v.now_s() + 9999.0
		marked.append([v, 1e9, p1])
		var u = main.spawn("person", Vector3(p0.x, 0, p0.y) + Vector3(0.4, 0, 0.4), Vector3(p1.x, 0, p1.y) + Vector3(0.4, 0, 0.4))
		u.set_meta("privat_test", true)
		u.next_idle = u.now_s() + 9999.0
		plain.append([u, 1e9, p1 + Vector2(0.4, 0.4)])
	ok("über visit-Kontext markiert", marked.all(func(m): return bool(m[0].privat)))
	ok("ohne Kontext nicht markiert", plain.all(func(m): return not bool(m[0].privat)))
	var t_end := Time.get_ticks_msec() / 1000.0 + 40.0
	while Time.get_ticks_msec() / 1000.0 < t_end:
		await process_frame
		for m in marked + plain:
			if is_instance_valid(m[0]):
				m[1] = minf(float(m[1]), _d(m[0], c))
	var arrived := 0
	var min_m := 1e9
	for m in marked:
		min_m = minf(min_m, float(m[1]))
		if not is_instance_valid(m[0]) or m[0].done or _d(m[0], m[2]) < 2.5:
			arrived += 1
	var min_p := 1e9
	var arrived_p := 0
	for m in plain:
		min_p = minf(min_p, float(m[1]))
		if not is_instance_valid(m[0]) or m[0].done or _d(m[0], m[2]) < 2.5:
			arrived_p += 1
	print("gerade Wege: markiert am nächsten %.2f m (Kreis %.2f + Abstand %.1f), ohne Markierung %.2f m, angekommen %d/4 (ohne Markierung %d/4)" % [min_m, r, P.MARGIN, min_p, arrived, arrived_p])
	ok("markierte Besucher nie im Kreis (%.2f >= %.2f)" % [min_m, r], min_m >= r - 0.05)
	ok("markierte Besucher halten meist den Abstand (%.2f >= %.2f)" % [min_m, r + P.MARGIN * 0.4], min_m >= r + P.MARGIN * 0.4)
	ok("markierte Besucher kommen trotzdem ans Ziel (%d/4, ohne Markierung %d/4)" % [arrived, arrived_p], arrived >= mini(3, arrived_p))
	ok("ohne Markierung geht der Weg wie bisher durch (%.2f < %.2f)" % [min_p, r], min_p < r)
	_clear()
	await wait(0.5)
	# ---- 2 exceptions: no marks for burglars, guests, deliveries ----
	for k in ["burglar", "sneaker", "bbq", "homecoming", "courier", "platz_besuch"]:
		ok("Ausnahme %s" % k, P.exempt(k))
	ok("keine Ausnahme: person, dogwalk, police, kids_tag", not P.exempt("person") and not P.exempt("dogwalk") and not P.exempt("police") and not P.exempt("kids_tag"))
	var n0: int = main.visitors.get_child_count()
	main.visit("burglar")
	await wait(0.3)
	var any_marked := false
	for i in range(n0, main.visitors.get_child_count()):
		if bool(main.visitors.get_child(i).privat):
			any_marked = true
	ok("Einbrecher (visit) nicht markiert", not any_marked)
	_clear()
	await wait(0.5)
	# ---- 3 some simulated minutes of visitors by themselves ----
	main.visit_rate = 4.0
	main.max_visitors = 14
	main.mix = "people"
	main.auto_visitors = true
	main.next_auto = 0.0
	var seen := {}
	var worst := 1e9
	var inside := 0
	t_end = Time.get_ticks_msec() / 1000.0 + 75.0             # 75 s × 4 = 5 simulated minutes of walking
	var t_visit := 0.0
	while Time.get_ticks_msec() / 1000.0 < t_end:
		await process_frame
		var tn := Time.get_ticks_msec() / 1000.0
		if tn > t_visit:                                       # and now and then one sent by hand («Besuch»)
			t_visit = tn + 6.0
			main.visit(["person", "dogwalk", "couple", "police", "kids_tag", "jogger"][randi() % 6])
		for v in main.visitors.get_children():
			if v.get("kind") != "person" or not bool(v.get("privat")):
				continue
			seen[v.get_instance_id()] = true
			var dd := _d(v, c)
			worst = minf(worst, dd)
			if dd < r - 0.05:
				inside += 1
	main.auto_visitors = false
	Engine.time_scale = 1.0
	print("Besuch von selbst: %d markierte Personen, am nächsten %.2f m (Kreis %.2f), Bilder im Kreis %d" % [seen.size(), worst, r, inside])
	ok("genug markierte Besucher (%d >= 6)" % seen.size(), seen.size() >= 6)
	ok("kein markierter Besucher im Kreis", inside == 0)
	_clear()
	await wait(0.5)
	# ---- 4 the new runs: variation by seed ----
	var E = main.einbruch
	ok("neue Abläufe in der Liste", E.all_ids().has("zelt_runde") and E.all_ids().has("velo_weg"))
	ok("«zufällig» / Serie unverändert", not E.ORDER.has("zelt_runde") and E.ORDER.size() == 7)
	var info: Dictionary = E.control({"do": "info"})
	ok("info nennt die neuen Abläufe", str(info.get("ablaeufe", [])).contains("zelt_runde") and str(info.get("ablaeufe", [])).contains("velo_weg"))
	main.set_hour(23.5)
	await wait(0.3)
	for id in ["zelt_runde", "velo_weg"]:
		var sig := []
		for sd in [3, 11]:
			E._rng.seed = sd * 7919 + 5
			var acts: Array = E._build(id)
			var ro: Dictionary = acts[0]["roles"][0]
			sig.append("%s|%d|%s" % [str(ro["from"].snapped(Vector3(0.1, 0.1, 0.1))), (ro["steps"] as Array).size(), ro["kind"]])
			E._reset_run()
		print(id, " Seeds: ", sig)
		ok("%s: anderer Seed, anderer Ablauf" % id, sig[0] != sig[1])
	# ---- 5 both runs to the end (the thief goes onto the pitch) ----
	Engine.time_scale = TS
	for id in ["zelt_runde", "velo_weg"]:
		_clear()
		await wait(0.5)
		main.set_hour(23.5)
		var e: String = E.start(id, 7, false)
		ok("%s startet" % id, e == "")
		var closest := 1e9
		var secs_seen := {}
		var bike_hidden := false
		var t0 := Time.get_ticks_msec() / 1000.0
		while E.running and Time.get_ticks_msec() / 1000.0 - t0 < 420.0:
			await process_frame
			for ro in E.roles:
				var v = ro.get("v")
				if v != null and is_instance_valid(v):
					closest = minf(closest, _d(v, c))
			secs_seen[E._cur_sec] = true
			if main.bike_node != null and is_instance_valid(main.bike_node) and not main.bike_node.visible:
				bike_hidden = true
		var rp: Dictionary = E.rep
		print("%s: %.0f s, Abschnitte %s, Beute «%s», am nächsten %.2f m, fertig %s" % [id, Time.get_ticks_msec() / 1000.0 - t0, secs_seen.keys(), rp.get("beute", ""), closest, rp.get("fertig", false)])
		ok("%s läuft bis zum Schluss" % id, not E.running and bool(rp.get("fertig", false)))
		ok("%s: der Dieb betritt den Kreis (%.2f < %.2f)" % [id, closest, r], closest < r)
		ok("%s: Griff" % id, float(rp.get("griff_s", -1.0)) > 0.0)
		if id == "zelt_runde":
			ok("zelt_runde: schleicht ums Zelt", secs_seen.has("umkreisen"))
			ok("zelt_runde: Beute", str(rp.get("beute", "")) in ["Rucksack", "Kühlbox", "Handy"])
		else:
			ok("velo_weg: am Schloss", secs_seen.has("schloss"))
			ok("velo_weg: Velo weg", bike_hidden and str(rp.get("beute", "")) == "Velo")
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("Privatplatz-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Privatplatz-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
