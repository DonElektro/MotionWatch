extends SceneTree
## Test «Frei erkunden mit eigener Figur», Etappe 1 (Besitzer 21.11.2026), ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/frei_erkunden_test.gd" -- --no-update --no-tour
## Prüft:
##   1. Start: «🥾 Frei erkunden» (Spielen, Steuerbefehl spielbereich «frei») = Erkunden als Figur in der Welt, die geladen
##      ist (Camping-Platz, dann Stellplatz); die Figur ist die des Kits (kit_figur.gd + kit_regie.gd), ein gesteuerter
##      Wanderer (actor.gd), in der Welt sichtbar wie ein Besucher.
##   2. Haltungen: Taste C stehen → geduckt → kriechen → stehen; geduckt / kriechend ist die Figur wirklich niedriger
##      (Höhe über den Füssen), die Ich-Sicht geht mit hinunter; X sitzen (auf eine Bank daneben, sonst Boden), Z hinlegen
##      (bleibt still liegen; losgehen = kriechen); Knöpfe für Handy / iPad (Symbol = Haltung).
##   3. Springen (Leertaste) und an einer Kante hochklettern (eine Stufe von 1,2 m im Gelände).
##   4. Wasser: Tiefe → trocken / waten / schwimmen (erkunden_welt.gd), ein Teich: waten langsamer, schwimmen an der
##      Oberfläche (kein Tauchen), hinaus geht es von selbst; im Bergtal der Bergsee.
##   5. Schnelllauf: Stufen 1,8 / 3 / 5 / 10 / 15 / 20 / 30 / 40 m/s, nie über 40, rennt wirklich ≈ 40 m/s und nicht durch eine dünne
##      Wand; Schalter «Schnelllauf» aus = normales Rennen 3,45 m/s, Knopf «Tempo» weg.
##   6. Der alte Steuerbefehl {"action": "explore", "person": …, "pwalk": …, "pplace": …} geht weiter (+ haltung, sitzen …),
##      und why_not() gilt auch für «Frei erkunden» (Messung: geht nicht).
## Ende: «Frei-Erkunden-Test OK» oder «SCRIPT ERROR: Frei-Erkunden-Test: …» (Exit-Code 0 / 1).

const Welt = preload("res://scripts/erkunden_welt.gd")
const T = preload("res://scripts/i18n.gd")

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


func _ctl(d: Dictionary) -> Dictionary:
	return main._control(d)


func _speed(p, secs: float) -> float:
	"""the speed over secs: the way, frame by frame, through the engine's own frame times (what the figure moves by) - not the
	wall clock (on a busy machine the frame times drift from it, a fast run then looked faster / slower than it is)"""
	var a: Node3D = p.actor
	var q := _xz(a)
	var weg := 0.0
	var t := 0.0
	while t < secs:
		await process_frame
		t += get_root().get_process_delta_time()
		var q2 := _xz(a)
		weg += q2.distance_to(q)
		q = q2
	return weg / maxf(0.01, t)


func _linie(o: Vector3, d: Vector3, L: float) -> Dictionary:
	"""a straight line on the ground: mean slope, steepest metre up / down - {} with an obstacle or water on it"""
	var g0: float = main.ground_y(o.x, o.z)
	var prev := g0
	var smax := 0.0
	var smin := 99.0
	for i in range(1, int(L) + 1):
		var q := o + d * float(i)
		var g: float = main.ground_y(q.x, q.z)
		smax = maxf(smax, g - prev)
		smin = minf(smin, g - prev)
		prev = g
		if i % 3 == 0 and (main.keep_out(Vector2(q.x, q.z), 0.4, true).distance_to(Vector2(q.x, q.z)) > 0.01 or not Welt.wasser(main, q).is_empty()):
			return {}
	return {"mean": (prev - g0) / L, "max": smax, "min": smin}


func _hang_suchen(p0: Vector3, lo: float, hi: float) -> Dictionary:
	for r in [0.0, 40.0, 80.0, 120.0, 180.0, 250.0]:
		for k in range(12):
			var c: Vector3 = p0 + Vector3(cos(k * 0.52), 0, sin(k * 0.52)) * float(r)
			for j in range(16):
				var d := Vector3(cos(j * PI / 8.0), 0, sin(j * PI / 8.0))
				var l: Dictionary = _linie(c, d, 60.0)
				if not l.is_empty() and float(l["mean"]) >= lo and float(l["mean"]) <= hi and float(l["max"]) < 1.1 and float(l["min"]) > -0.2:
					return {"o": c, "d": d, "l": l}
	return {}


func _hang_lauf(p, o: Vector3, d: Vector3, v: float) -> Dictionary:
	"""run along d from o (fast run v, or the normal run with v < 4): the speed after speeding up, frames off the ground"""
	main.ex_schnell = v > 4.0
	p.set_tempo(v if v > 4.0 else 3.0)
	p.figur.setzen(o, atan2(-d.x, -d.z))
	p.actor.cur_speed = 0.0
	await wait(0.1)
	p.test_walk(Vector2(1, 0), 3.0, true)
	await wait(1.1)
	var a: Node3D = p.actor
	var q := _xz(a)
	var weg := 0.0
	var t := 0.0
	var luft := 0
	var tief := 0.0
	while t < 0.5:
		await process_frame
		t += get_root().get_process_delta_time()
		weg += _xz(a).distance_to(q)
		q = _xz(a)
		if str(p.figur.zustand) != "boden":
			luft += 1
		tief = minf(tief, a.global_position.y - main.ground_y(a.global_position.x, a.global_position.z))
	var r := {"v": weg / maxf(0.01, t), "luft": luft, "tief": tief}
	p.test_walk(Vector2.ZERO, 0.1, false)
	await wait(0.3)
	return r


func _hang_test(p, b) -> void:
	"""Besitzer 22.11.2026: fast run uphill got slow (a slope seen as a step per frame) - now: the chosen speed up to the
	walkable slope, on the ground (no flying off downhill, never into the ground)"""
	var schnell0: bool = main.ex_schnell
	var f := _hang_suchen(p.actor.global_position, 0.3, 0.6)
	ok("Bergtal: ein Hang (Steigung 0,3 … 0,6) gefunden", not f.is_empty())
	if f.is_empty():
		return
	print("  Hang: ", f["l"])
	for v in [10.0, 20.0, 40.0]:
		var r: Dictionary = await _hang_lauf(p, f["o"], f["d"], v)
		ok("bergauf %d m/s: %.1f m/s, am Boden, nicht im Gelände" % [int(v), r["v"]], r["v"] > v * 0.85 and r["luft"] == 0 and r["tief"] > -0.05)
	var dn: Dictionary = await _hang_lauf(p, f["o"] + f["d"] * 60.0, -f["d"], 40.0)
	ok("bergab 40 m/s: %.1f m/s, am Boden (fliegt nicht ab)" % dn["v"], dn["v"] > 40.0 * 0.85 and dn["luft"] <= 2 and dn["tief"] > -0.05)
	var nr: Dictionary = await _hang_lauf(p, f["o"], f["d"], 3.45)
	ok("ohne Schnelllauf bergauf: normal rennen (%.2f m/s)" % nr["v"], nr["v"] > 2.6 and nr["v"] < 4.0 and nr["luft"] == 0)
	main.ex_schnell = schnell0
	p.set_tempo(3.0)


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false                                  # headless: nobody looks - the world must still move
	main.set_scene("camping")
	await wait(2.0)
	main.clear_obstacles()                                 # an open place (the moving itself is checked)
	print("  Sitzplätze der Szene: %d" % (main.scenes.data.get("sitze", []) as Array).size())
	main.scenes.data.erase("sitze")                        # (no stone of the scene beside the start: sitting on the ground first)
	main.home_pos = Vector3.ZERO
	main.mover_home()
	var ex = main.explore
	var p = ex.person
	# ---- 1. «🥾 Frei erkunden» ----
	ok("Erkunden zuerst aus", not ex.on)
	var r: Dictionary = _ctl({"action": "spielbereich", "do": "frei"})
	await wait(0.4)
	ok("Frei erkunden: Erkunden an, gleich als Figur", bool(r.get("ok", false)) and ex.on and ex.person_on())
	ok("die Figur ist ein gesteuerter Wanderer (actor.gd)", p.ok() and bool(p.actor.get("controlled")) and str(p.actor.get("kind")) == "person")
	ok("die Figur ist die des Kits (kit_figur.gd, Zustand boden)", p.figur != null and p.figur.a == p.actor and str(p.figur.zustand) == "boden")
	ok("MoveEye sieht sie wie einen Besucher (sichtbar, in der Welt)", p.actor.is_visible_in_tree() and p.actor.get_parent() == main)
	ok("walker_pos = Figur", main.walker_kind() == "person")
	var wiz_cards: Array = main.gamewiz.model().get("quick", [])
	ok("Spiel-Assistent: Karte «Frei erkunden»", wiz_cards.any(func(c): return str(c.get("v", "")) == "frei_erkunden"))
	ex.view = "chase"
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	await wait(0.3)
	# walking: W goes away from the camera (the spring camera turns behind the figure)
	var a: Node3D = p.actor
	var p0 := _xz(a)
	ex.test_drive = Vector2(1, 0)
	ex.test_until = main.now() + 2.0
	await wait(2.1)
	ok("W: die Figur geht (%.1f m)" % _xz(a).distance_to(p0), _xz(a).distance_to(p0) > 1.5)
	var cam_d: float = _xz(main.view_cam).distance_to(_xz(a))
	ok("Federkamera hinter der Figur (%.1f m)" % cam_d, cam_d > 1.5 and cam_d < 8.0)
	await wait(0.6)
	# ---- 2. postures ----
	ok("steht", p.haltung == "stehen")
	await wait(0.8)
	var h_st: float = p.hoehe()
	ex.view = "driver"
	await wait(0.5)
	var eye_st: float = main.view_cam.global_position.y - p.figur.y
	await _key(KEY_C)
	ok("C: geduckt", p.haltung == "geduckt" and int(a.ctl_posture) == 1)
	await wait(1.2)
	var h_ge: float = p.hoehe()
	var eye_ge: float = main.view_cam.global_position.y - p.figur.y
	await _key(KEY_C)
	ok("C: kriechen", p.haltung == "kriechen" and int(a.ctl_posture) == 2)
	await wait(1.6)
	var h_kr: float = p.hoehe()
	var eye_kr: float = main.view_cam.global_position.y - p.figur.y
	await _key(KEY_C)
	ok("C: wieder stehen", p.haltung == "stehen" and int(a.ctl_posture) == 0)
	print("  Höhe: stehen %.2f · geduckt %.2f · kriechen %.2f m; Augen %.2f · %.2f · %.2f m" % [h_st, h_ge, h_kr, eye_st, eye_ge, eye_kr])
	ok("stehend gross (%.2f m)" % h_st, h_st > 1.35 and h_st < 2.1)
	ok("geduckt niedriger (%.2f < 0.8 × %.2f)" % [h_ge, h_st], h_ge < h_st * 0.8)
	ok("kriechend ganz niedrig, um 0,5 m (%.2f m)" % h_kr, h_kr > 0.3 and h_kr < 0.62 and h_kr < h_ge)
	ok("Ich-Sicht: Augen folgen der Haltung (%.2f > %.2f > %.2f)" % [eye_st, eye_ge, eye_kr], eye_st > eye_ge + 0.2 and eye_ge > eye_kr + 0.15)
	ok("Ich-Sicht stehend auf Augenhöhe (%.2f m)" % eye_st, absf(eye_st - 1.62) < 0.25)
	await wait(1.2)
	ex.view = "top"
	await wait(0.6)
	ok("Ansicht von oben", main.view_cam.global_position.y - p.figur.y > 8.0)
	await _key(KEY_V)
	ok("V: wieder hinter der Figur", ex.view == "chase")
	# crouched: no running
	await _key(KEY_C)
	p.test_walk(Vector2(1, 0), 2.5, true)
	await wait(1.0)
	var v_ge: float = await _speed(p, 1.0)
	ok("geduckt: langsam, kein Rennen (%.2f m/s)" % v_ge, v_ge < 1.1)
	await _key(KEY_C)
	await _key(KEY_C)
	await wait(0.6)
	# sitting: on the ground, then on a bench beside
	await _key(KEY_X)
	await wait(1.0)
	ok("X: sitzt auf dem Boden", p.haltung == "sitzen" and str(p.sitz.get("art", "")) == "boden" and bool(a.ctl_sit))
	var h_si: float = p.hoehe()
	ok("sitzend niedriger (%.2f m)" % h_si, h_si < h_st * 0.85)
	var ps := _xz(a)
	p.test_walk(Vector2(1, 0), 0.6, false)                 # walking off: up
	await wait(0.8)
	ok("losgehen: steht auf", p.haltung == "stehen" and not bool(a.ctl_sit))
	p.test_walk(Vector2.ZERO, 0.1, false)
	await wait(0.4)
	var hd := float(a.heading)
	var fw := Vector3(-sin(hd), 0, -cos(hd))
	var side := fw.cross(Vector3.UP)
	main.add_obstacle(a.global_position - side * 0.9, 0.5)  # a camping table / fire ring beside: no seat
	main.set_obstacle_height(0.5)
	await _key(KEY_X)
	await wait(0.8)
	ok("X: nie auf den Tisch daneben (Boden)", p.haltung == "sitzen" and str(p.sitz.get("art", "")) == "boden")
	await _key(KEY_X)
	await wait(0.3)
	main.sitz_merken(a.global_position + side * 1.3, 0.3, "stein")   # a stone and a bench of the scene beside
	main.sitz_merken(a.global_position + side * 0.8, 0.45, "bank")
	await _key(KEY_X)
	await wait(1.0)
	ok("X: sitzt auf der Bank daneben (%s)" % str(p.sitz.get("art", "")), p.haltung == "sitzen" and str(p.sitz.get("art", "")) == "bank" and absf(float(a.sit_seat) - 0.45) < 0.06)
	await _key(KEY_X)
	ok("X nochmals: steht auf", p.haltung == "stehen")
	main.clear_obstacles()
	main.scenes.data.erase("sitze")
	main.sitz_merken(a.global_position + side * 0.9, 0.3, "stein")
	await _key(KEY_X)
	await wait(0.8)
	ok("X: sonst auf den Stein", str(p.sitz.get("art", "")) == "stein")
	await _key(KEY_X)
	main.scenes.data.erase("sitze")
	# lying still
	await _key(KEY_Z)
	await wait(1.6)
	ok("Z: liegt", p.haltung == "liegen" and int(a.ctl_posture) == 2 and bool(a.frozen))
	var pl := _xz(a)
	await wait(0.5)
	ok("liegt still", _xz(a).distance_to(pl) < 0.02 and p.hoehe() < 0.7)
	var ph0: float = float(a.get("phase"))
	await wait(0.6)
	ok("still liegend: kein Kriech-Takt (keine rutschenden Ellbogen)", absf(float(a.get("phase")) - ph0) < 0.01 and float(a.get("_crawl_m")) < 0.05)
	p.test_walk(Vector2(1, 0), 0.8, false)
	await wait(0.9)
	ok("losgehen aus dem Liegen: kriecht", p.haltung == "kriechen")
	await _key(KEY_C)
	await wait(0.8)
	# going down: crouched -> crawling in about 0.35 s (blended, no snap)
	p.set_haltung("geduckt")
	await wait(0.8)
	p.set_haltung("kriechen")
	await wait(0.42)
	ok("hinunter zum Kriechen in ~0,35 s (prone %.2f)" % float(a.prone), float(a.prone) > 0.95)
	p.test_walk(Vector2(1, 0), 1.6, false)
	await wait(1.0)
	ok("kriechend: Takt läuft mit dem Tempo", float(a.get("_crawl_m")) > 0.8)
	await wait(0.8)
	p.set_haltung("stehen")
	await wait(0.6)
	# the buttons for phone / iPad
	p.touch.forced = 1
	await wait(0.2)
	var ti: Dictionary = p.touch.info()
	ok("Handy: Knöpfe am Rand sichtbar", bool(ti.get("visible", false)) and ti.has("haltung") and ti.has("sitzen") and ti.has("liegen") and ti.has("sprung"))
	ok("Handy: Symbol = stehen", str(ti["haltung"]["symbol"]) == "stehen")
	p.touch_tipp("haltung")
	await wait(0.2)
	ok("Handy: Knopf Haltung → geduckt, Symbol mit", p.haltung == "geduckt" and str(p.touch.info()["haltung"]["symbol"]) == "geduckt")
	p.touch_tipp("haltung")
	await wait(0.2)
	p.touch_tipp("haltung")
	await wait(0.3)
	ok("Handy: wieder stehen", p.haltung == "stehen")
	p.touch.forced = -1
	await wait(0.6)
	# ---- 3. jump, climb ----
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	await wait(0.3)
	await _key(KEY_SPACE)
	await wait(0.15)
	ok("Leertaste: springt (luft)", str(p.figur.zustand) == "luft" and p.figur.y > 0.05)
	await wait(1.2)
	ok("landet wieder (boden)", str(p.figur.zustand) == "boden")
	var gf_alt: Callable = main.ground_fn
	main.ground_fn = func(_x: float, z: float) -> float: return 1.2 if z < -1.5 else 0.0     # a step of 1.2 m ahead (heading 0 = -z)
	p.figur.setzen(Vector3(0, 0, -0.8), 0.0)
	await wait(0.3)
	ok("Kante vor der Figur gefunden", not Welt.kante(main, p.figur.pos(), 0.0).is_empty())
	await _key(KEY_SPACE)
	await wait(0.1)
	ok("an der Kante: klettert hoch (klettern)", str(p.figur.zustand) == "klettern")
	await wait(2.5)
	ok("oben auf der Stufe (y %.2f)" % p.figur.y, str(p.figur.zustand) == "boden" and p.figur.y > 1.1 and p.figur.pos().z < -1.5)
	main.ground_fn = gf_alt
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	await wait(0.4)
	# ---- 4. water ----
	ok("Tiefe 0,1 m: trocken", Welt.art_fuer_tiefe(0.1) == "")
	ok("Tiefe 0,5 m: waten", Welt.art_fuer_tiefe(0.5) == "waten")
	ok("Tiefe 1,0 m: waten", Welt.art_fuer_tiefe(1.0) == "waten")
	ok("Tiefe 1,5 m: schwimmen", Welt.art_fuer_tiefe(1.5) == "schwimmen")
	ok("Bach: waten", Welt.art_fuer_tiefe(0.35, true) == "waten")
	# a pond: 0.6 m deep at the shore, 2 m in the middle, the water level at 0
	main.ground_fn = func(x: float, z: float) -> float:
		var d := Vector2(x, z).distance_to(Vector2(0, -20))
		return -2.0 if d < 5.0 else (-0.6 if d < 9.0 else 0.0)
	main.set_meta("erkunden_wasser", [{"c": Vector2(0, -20), "r": 9.0, "spiegel": 0.0}])
	p.figur.setzen(Vector3(0, -0.6, -12.5), 0.0)
	await wait(0.4)
	ok("im seichten Wasser: watet", p.wasser == "waten")
	p.test_walk(Vector2(0, 0), 0.1, false)
	main.ex_schnell = true
	p.set_tempo(20.0)
	p.figur.setzen(Vector3(-7.0, -0.6, -20.0), 0.0)           # in the shallow ring, along it (heading 0 = -z)
	await wait(0.2)
	p.test_walk(Vector2(1, 0), 2.0, true)                    # running wished
	await wait(0.8)
	var v_wa: float = await _speed(p, 0.8)
	ok("waten: langsamer, kein Rennen (%.2f m/s)" % v_wa, v_wa < 1.0)
	p.figur.setzen(Vector3(0, -2.0, -20.0), 0.0)
	await wait(0.5)
	ok("tief: schwimmt", p.wasser == "schwimmen")
	ok("an der Oberfläche (Füsse %.2f, Wasser 0)" % p.figur.y, absf(p.figur.y - (0.0 - p.SCHWIMM_TIEF)) < 0.05)
	ok("schwimmend liegt der Körper (Haltung kriechen in actor.gd)", int(a.ctl_posture) == 2)
	await _key(KEY_SPACE)
	await wait(0.2)
	ok("kein Sprung / Tauchen im Wasser", p.wasser == "schwimmen" and str(p.figur.zustand) == "boden")
	await _key(KEY_Z)
	ok("im Wasser nicht hinlegen", p.haltung == "stehen")
	p.test_walk(Vector2(1, 0), 14.0, false)                  # straight out (heading 0 = -z: 5 m deep, then 4 m shallow, then dry)
	var t0 := Time.get_ticks_msec()
	var seen_wade := false
	while Time.get_ticks_msec() - t0 < 16000 and p.figur.pos().z > -30.5:
		if p.wasser == "waten":
			seen_wade = true
		await process_frame
	print("  aus dem Teich: z %.1f, y %.2f, %s" % [p.figur.pos().z, p.figur.y, p.wasser])
	ok("schwimmt hinaus, watet, ist draussen (trocken, y 0)", seen_wade and p.wasser == "" and absf(p.figur.y) < 0.05 and str(p.figur.zustand) == "boden")
	p.test_walk(Vector2.ZERO, 0.1, false)
	main.remove_meta("erkunden_wasser")
	main.ground_fn = gf_alt
	await wait(0.3)
	# ---- 5. fast run ----
	ok("Stufen 1,8 / 3 / 5 / 10 / 15 / 20 / 30 / 40", str(p.TEMPI) == str([1.8, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0]))
	p.set_tempo(1.8)
	var seen := []
	for i in range(8):
		p.tempo_stufe(1, true)
		seen.append(main.ex_ptempo)
	ok("Knopf geht durch alle Stufen (%s)" % str(seen), str(seen) == str([3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 1.8]))
	p.set_tempo(90.0)
	ok("nie über 40 m/s", is_equal_approx(main.ex_ptempo, 40.0) and is_equal_approx(p.renn_tempo(main), 40.0))
	ex._process(0.016)
	ok("Knopf «Rennen» sichtbar (Schnelllauf an)", ex._btn_speed.visible and ex._btn_speed.text.find("40") >= 0)
	main.clear_obstacles()
	main.add_obstacle_box(Vector3(0, 0, -150), 14.0, 0.1, 0.0)  # a thin wall 150 m ahead
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	ex.view = "chase"
	await wait(0.3)
	p.test_walk(Vector2(1, 0), 9.0, true)
	await wait(1.8)
	var v40: float = await _speed(p, 1.0)
	print("  Schnelllauf: %.1f m/s" % v40)
	ok("rennt etwa 40 m/s (%.1f)" % v40, v40 > 32.0 and v40 < 41.0)
	await wait(4.5)
	print("  vor der Wand: z = %.2f (Wand bei -150)" % a.global_position.z)
	ok("bei 40 m/s nicht durch die Wand", a.global_position.z > -150.0 and a.global_position.z < -146.0)
	# a long frame right in front of the wall
	p.figur.setzen(Vector3(0, 0, -140.0), 0.0)
	a.cur_speed = 40.0
	a.ctl_move = Vector2(0, -1)
	a.ctl_run = true
	var py: Vector3 = a.position
	var t_us := Time.get_ticks_usec()
	a._step(0.9)                                             # one frame of 0.9 s: 36 m in one go (180 steps of 0.2 m)
	print("  langes Bild bei 40 m/s: %d µs" % (Time.get_ticks_usec() - t_us))
	p._waende(py)
	ok("auch ein langes Bild bei 40 m/s nicht durch die Wand (z %.2f)" % a.position.z, a.position.z > -150.0)
	main.clear_obstacles()
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	main.ex_schnell = false
	ex._process(0.016)
	ok("Schalter aus: normales Rennen 3,45 m/s", is_equal_approx(p.renn_tempo(main), 3.45))
	ok("Schalter aus: Knopf «Rennen» weg", not ex._btn_speed.visible)
	p.test_walk(Vector2(1, 0), 4.0, true)
	await wait(2.0)
	var vn: float = await _speed(p, 1.0)
	ok("rennt normal (%.2f m/s)" % vn, vn > 2.6 and vn < 3.7)
	var dev_ids: Array = preload("res://scripts/devtool_schalter.gd").ids(main).map(func(c): return str(c.id))
	ok("Schalter im Entwickler-Bereich", "ex_schnell" in dev_ids)
	main._save_settings()
	var saved = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	ok("Schnelllauf und Tempo bleiben in den Einstellungen", saved is Dictionary and saved.get("ex_schnell", true) == false and is_equal_approx(float(saved.get("ex_ptempo", 0.0)), 40.0))
	main.ex_schnell = true
	p.set_tempo(3.0)
	ex._process(0.016)
	# «Rennen beim Erkunden» (Besitzer 22.11.2026): the speed beside «Schnelllauf», the same setting as the bar button
	ok("Entwickler: «Rennen beim Erkunden» gleich nach «Schnelllauf»", "ex_ptempo" in dev_ids and dev_ids.find("ex_ptempo") == dev_ids.find("ex_schnell") + 1)
	var ctl_t: Dictionary = {}
	for c in main.controls:
		if str(c.id) == "ex_ptempo":
			ctl_t = c
	ok("Rennen beim Erkunden: 8 Stufen 1,8 … 40 m/s", ctl_t.extra.get("options", []).map(func(o): return str(o[0])) == ["1.8", "3", "5", "10", "15", "20", "30", "40"])
	ctl_t["set"].call("10")
	ok("Wahl im Entwickler-Fenster = Tempo der Figur (10 m/s)", is_equal_approx(float(main.ex_ptempo), 10.0) and str(ctl_t["get"].call()) == "10")
	ex._process(0.016)
	ok("… und der Knopf der Leiste zeigt es", "10" in ex._btn_speed.text)
	p.tempo_stufe(1)
	ok("Knopf der Leiste (+1 Stufe) → Wahl im Fenster 15", str(ctl_t["get"].call()) == "15")
	ok("ohne Schnelllauf ausgegraut", bool(ctl_t.extra["an"].call()) == bool(main.ex_schnell))
	var dv = main.mehr.dev if main.get("mehr") != null and main.mehr != null else null
	if dv != null:
		main.dev_area = true
		main.dev_window("schalter")
		await wait(0.3)
		dv._paint()
		ok("Flugkamera-Tempo heisst so", dv._speed_lbl.text == T.t("Flugkamera-Tempo"))
		ok("Flugkamera-Tempo ausgegraut ohne Flugkamera", dv._speed_opt.disabled and not ex.fly)
		var sch = dv.extra.schalter
		sch.sync()
		var ob_t: OptionButton = null
		for w in sch._alle(sch._state.get_parent()):
			if w is OptionButton and w.has_meta("ctl") and str(w.get_meta("ctl").id) == "ex_ptempo":
				ob_t = w
		ok("Reiter «Schalter»: die Wahl zeigt 15 m/s", ob_t != null and ob_t.get_item_text(ob_t.selected) == "15 m/s")
		p.tempo_stufe(-1)
		sch.sync()
		ok("… und folgt dem Knopf der Leiste (10 m/s)", ob_t != null and ob_t.get_item_text(ob_t.selected) == "10 m/s")
		dv.panel.global_position = ex._btn_speed.get_global_rect().position - Vector2(20, 20)
		dv._paint()
		ok("Fenster über dem Knopf «Rennen»: Hinweis, wo das Tempo ist", dv.tempo_verdeckt() and dv._tempo_hint.visible)
		dv.close()
		main.dev_area = false
	else:
		ok("Entwickler-Fenster vorhanden", false)
	p.set_tempo(3.0)
	p.test_walk(Vector2.ZERO, 0.1, false)
	await wait(0.5)
	# ---- 6. the old control command, why_not ----
	var st: Dictionary = _ctl({"action": "explore", "person": false})
	ok("Steuerbefehl person false: Mover", not ex.person_on() and not bool(st["person"]["on"]))
	st = _ctl({"action": "explore", "person": true})
	ok("Steuerbefehl person true: Figur", ex.person_on() and bool(st["person"]["on"]))
	st = _ctl({"action": "explore", "pplace": [5.0, -5.0]})
	ok("Steuerbefehl pplace", Vector2(float(st["person"]["x"]), float(st["person"]["z"])).distance_to(Vector2(5, -5)) < 0.4)
	var q0 := _xz(p.actor)
	_ctl({"action": "explore", "pwalk": [1.0, 0.0, 1.5, false]})
	await wait(1.7)
	ok("Steuerbefehl pwalk (%.1f m)" % _xz(p.actor).distance_to(q0), _xz(p.actor).distance_to(q0) > 1.0)
	st = _ctl({"action": "explore", "haltung": "kriechen"})
	ok("Steuerbefehl haltung", str(st["person"]["haltung"]) == "kriechen")
	st = _ctl({"action": "explore", "haltung": "weiter"})
	ok("Steuerbefehl haltung weiter: stehen", str(st["person"]["haltung"]) == "stehen")
	st = _ctl({"action": "explore", "sitzen": true, "pview": "driver"})
	ok("Steuerbefehl sitzen + pview", str(st["person"]["haltung"]) == "sitzen" and ex.view == "driver")
	st = _ctl({"action": "explore", "sitzen": false, "pview": "chase", "ptempo": 10, "schnell": true})
	ok("Steuerbefehl ptempo / schnell", str(st["person"]["haltung"]) == "stehen" and is_equal_approx(float(st["person"]["run_top"]), 10.0))
	main.testrun.running = true                              # (only for this frame: as if a test run had started)
	ex._process(0.016)
	ok("Messung: zurück im Mover", not ex.person_on())
	ok("Messung: «Frei erkunden» geht nicht", not ex.frei_erkunden())
	main.testrun.running = false
	ex.set_on(false)
	await wait(0.3)
	ok("Erkunden aus: die Figur ist weg", p.actor == null)
	# ---- another world: the camper van site ----
	main.set_scene("stellplatz")
	await wait(3.0)
	r = _ctl({"action": "spielbereich", "do": "frei"})
	await wait(0.6)
	ok("Frei erkunden auch auf dem Stellplatz", bool(r.get("ok", false)) and ex.person_on() and p.ok() and main.scene == "stellplatz")
	var s0 := _xz(p.actor)
	p.test_walk(Vector2(1, 0), 1.5, false)
	await wait(1.7)
	ok("geht auf dem Stellplatz", _xz(p.actor).distance_to(s0) > 0.8)
	# the spring camera of the kit (kit_regie.gd) asks its kit for a ceiling and a room: the figure answers «none»
	ok("Kamera-Fragen des Kits beantwortet (decke_bei, raum_klemmen)", p.has_method("decke_bei") and p.has_method("raum_klemmen")
		and p.decke_bei(Vector3.ZERO, 0.0) == INF)
	# back to a caravan / a house of the place: the camera stays outside (walls: main.line_blocker, Sim 3.74.0)
	var n_box := 0
	var n_drin := 0
	for o in main.obstacles:
		if n_box >= 6 or not o.has("h") or bool(o["po"]) or minf(o["h"].x, o["h"].y) < 1.0:
			continue
		var nrm: Vector3 = (o["b"] as Basis) * Vector3(0, 0, 1)
		var at: Vector3 = Vector3(o["c"].x, 0, o["c"].y) + nrm * (float(o["h"].y) + 0.6)
		if main.keep_out(Vector2(at.x, at.z), 0.3, true).distance_to(Vector2(at.x, at.z)) > 0.01:
			continue
		n_box += 1
		p.figur.setzen(at, atan2(nrm.x, nrm.z))
		await wait(0.05)
		p.regie.hinter_figur()
		await wait(0.8)
		var cam: Vector3 = main.view_cam.global_position
		var l: Vector3 = (o["bi"] as Basis) * Vector3(cam.x - o["c"].x, 0, cam.z - o["c"].y)
		if absf(l.x) < float(o["h"].x) and absf(l.z) < float(o["h"].y) and cam.y - main.ground_y(cam.x, cam.z) < float(o.get("ht", 3.0)):
			n_drin += 1
	print("  Rücken zu Wohnwagen / Haus: %d Stellen, Kamera drin: %d" % [n_box, n_drin])
	ok("Rücken zum Wohnwagen: die Kamera bleibt draussen", n_box >= 3 and n_drin == 0)
	ex.set_on(false)
	# ---- the Bergtal: the lake ----
	main.set_scene("bergtal")
	var t1 := Time.get_ticks_msec()
	while (main.scene != "bergtal" or main.scenes.data.get("bergtal", null) == null) and Time.get_ticks_msec() - t1 < 60000:
		await process_frame
	await wait(2.0)
	var b = main.scenes.data.get("bergtal", null)
	ok("Bergtal geladen", b != null)
	if b != null:
		var lk: Array = b.LAKE1
		var lw: Vector3 = b.W(Vector3((lk[0] as Vector2).x, 0, (lk[0] as Vector2).y))
		var wd: Dictionary = Welt.wasser(main, lw)
		print("  Bergsee: ", wd)
		ok("Bergsee: tief (schwimmen)", str(wd.get("art", "")) == "see" and Welt.art_fuer_tiefe(float(wd["tiefe"])) == "schwimmen")
		ok("neben dem See: trocken", Welt.wasser(main, b.W(Vector3((lk[0] as Vector2).x + float(lk[1]) * 2.5, 0, (lk[0] as Vector2).y))).is_empty())
		ex.frei_erkunden()
		await wait(0.5)
		p.place(lw)
		await wait(0.6)
		ok("im Bergsee: schwimmt", p.wasser == "schwimmen" and absf(p.figur.y - (float(wd["spiegel"]) - p.SCHWIMM_TIEF)) < 0.1)
		await _hang_test(p, b)
		ex.set_on(false)
	if errs.is_empty():
		print("Frei-Erkunden-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Frei-Erkunden-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
