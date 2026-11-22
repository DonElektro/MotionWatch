extends SceneTree
## Test «Frei erkunden mit eigener Figur», Etappe 3 (Besitzer 21.11.2026): Rucksack und Sachen, Kraft «Entspannt» / «Echt».
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/erkunden_sachen_test.gd" -- --no-update --no-tour
## Prüft: packen (30 / 50 / 70 L, Gewicht, Platz, kleinerer Rucksack), Fenster-Reiter «Rucksack», Stirnlampe (L), Feldstecher
## (B, Zoom 2–10×, Tier mit Name und Distanz, Foto, Nachtsicht), Kompass (Ort merken), Taschenuhr, Seil (abseilen), Pickel
## (Schnee, höhere Kanten), Essen / Trinken / Auffüllen / Kochen, Erste Hilfe nach hartem Sturz, MoveEye aufstellen,
## Übernachten (Lager, Morgen, Kraft voll), Kraft «Echt» (sinkt, Ausruhen, Stöcke, Tempo) und «Entspannt» (bleibt voll).
## Ende: «Erkunden-Sachen-Test OK» oder «SCRIPT ERROR: Erkunden-Sachen-Test: …».

const RS = preload("res://scripts/erkunden_rucksack.gd")

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
	main.home_pos = Vector3.ZERO
	main.mover_home()
	main.weather = "clear"
	main.set_hour(13.0)
	var ex = main.explore
	# ---- packing ----
	ok("ab Werk: Kraft «Entspannt»", not bool(main.ex_kraft_echt))
	var r0: Dictionary = RS.norm(main.ex_rucksack)
	ok("ab Werk gepackt: Lampe, Kompass, Uhr, Feldstecher, Essen, Wasser, Jacke", RS.hat(r0, "stirnlampe") and RS.hat(r0, "kompass") and RS.hat(r0, "taschenuhr") and RS.hat(r0, "feldstecher") and RS.hat(r0, "essen"))
	var r := RS.norm({"pack": "30", "n": {}})
	var dazu := RS.dazu(r, "kuppelzelt", 1)
	r = dazu["d"]
	r = RS.dazu(r, "winterschlafsack", 1)["d"]
	var voll := RS.dazu(r, "isomatte", 1)
	ok("30 L: Zelt 9 L + Winterschlafsack 12 L + Isomatte 6 L passt", bool(voll["ok"]))
	r = voll["d"]
	ok("… dann ist der 30-L-Rucksack fast voll (%d L)" % int(RS.volumen(r)), not bool(RS.dazu(r, "essen", 1)["ok"]) or RS.volumen(r) + 2.0 <= 30.0)
	ok("… ein zweites Zelt nie (höchstens 1)", not bool(RS.dazu(r, "kuppelzelt", 1)["ok"]))
	ok("Gewicht = Rucksack + Sachen (%.2f kg)" % RS.gewicht(r), is_equal_approx(RS.gewicht(r), 0.9 + 2.6 + 1.6 + 0.5))
	var r70 := RS.norm({"pack": "70", "n": {"kuppelzelt": 1, "winterschlafsack": 1, "isomatte": 1, "essen": 4, "wasser": 3, "seil": 1, "kocher": 1}})
	var r30 := RS.pack_setzen(r70, "30")
	ok("kleinerer Rucksack: was nicht passt, kommt heraus (%d L)" % int(RS.volumen(r30)), RS.volumen(r30) <= 30.0 and str(r30["pack"]) == "30")
	main.ex_rucksack = RS.norm({"pack": "70", "n": {}})
	_ctl({"action": "spielbereich", "do": "frei"})
	await wait(0.6)
	var p = ex.person
	var sa = p.sachen
	ok("Frei erkunden", ex.person_on() and sa != null)
	var g = p.gestalten
	g.zeigen(true)
	g.druecke("reiter:rucksack")
	ok("Fenster: Reiter Rucksack", int(g.info()["knoepfe"]) > 20)
	ok("Knopf 30 L", g.druecke("pack=30"))
	ok("Knopf Seil +", g.druecke("seil+"))
	ok("Knopf Kocher +", g.druecke("kocher+"))
	ok("im Rucksack: Seil und Kocher, 30 L", RS.hat(sa.rs(), "seil") and RS.hat(sa.rs(), "kocher") and str(sa.rs()["pack"]) == "30")
	g.druecke("pack=70")
	g.zeigen(false)
	await wait(0.3)
	# ---- headlamp ----
	main.ex_figur = {}
	p.figur_setzen({})
	await wait(0.3)
	sa.lampe()
	ok("ohne Stirnlampe: geht nicht", not sa.lampe_an())
	_ctl({"action": "explore", "rucksack": {"pack": "70", "n": {"stirnlampe": 1, "feldstecher": 1, "kompass": 1, "taschenuhr": 1, "essen": 2, "wasser": 1, "kocher": 1, "apotheke": 1, "stoecke": 1}}})
	await _key(KEY_L)
	ok("L: Stirnlampe an", sa.lampe_an() and p.actor.get("lamp") != null)
	await _key(KEY_L)
	ok("L: Stirnlampe aus", not sa.lampe_an())
	# ---- binoculars ----
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	await wait(0.3)
	var deer = main.spawn("deer", Vector3(0, 0, -40), Vector3(0.1, 0, -40.2))
	if deer != null:
		deer.speed = 0.0
		deer.set("demo", 0.0)
	await _key(KEY_B)
	await wait(0.4)
	ok("B: Feldstecher", bool(sa.fernglas))
	sa.set_zoom(20.0)
	ok("Zoom höchstens 10×", is_equal_approx(sa.zoom, 10.0))
	sa.set_zoom(0.5)
	ok("Zoom mindestens 2×", is_equal_approx(sa.zoom, 2.0))
	sa.set_zoom(4.0)
	await wait(0.3)
	ok("Bildwinkel = 62° / Zoom (%.1f)" % main.view_cam.fov, absf(main.view_cam.fov - 15.5) < 0.5)
	var sicht: Array = sa.sichtbare()
	print("  im Feldstecher: ", sicht.map(func(e): return [e[0], snappedf(e[1], 0.1)]))
	ok("Reh im Feldstecher mit Name und Distanz", sicht.any(func(e): return str(e[0]) == sa.T.t("Reh") and float(e[1]) > 35.0 and float(e[1]) < 45.0))
	sa.tu_fernglas("nacht")
	ok("Nachtsicht an", bool(sa.nacht))
	var fp: String = sa.foto()
	ok("Foto gespeichert (%s)" % fp, FileAccess.file_exists(fp))
	await _key(KEY_B)
	ok("B: zurück", not bool(sa.fernglas) and not bool(sa.nacht))
	if deer != null and is_instance_valid(deer):
		deer.queue_free()
	# ---- compass, watch ----
	await _key(KEY_O)
	ok("O: Ort gemerkt (Kompass)", sa.ziel is Vector3)
	var h0: float = main.hour()
	await _key(KEY_PERIOD)
	ok("Uhr: ½ Stunde vor", absf(fposmod(main.hour() - h0, 24.0) - 0.5) < 0.05)
	await _key(KEY_COMMA)
	ok("Uhr: wieder zurück", absf(fposmod(main.hour() - h0 + 12.0, 24.0) - 12.0) < 0.05)
	# ---- food and water ----
	var n_e: int = RS.anzahl(sa.rs(), "essen")
	sa.tu("essen")
	ok("Essen: eine Portion weniger", RS.anzahl(sa.rs(), "essen") == n_e - 1)
	sa.tu("trinken")
	ok("Trinken: Wasser leer", RS.anzahl(sa.rs(), "wasser") == 0)
	ok("nicht am Wasser: auffüllen geht nicht", not sa.am_wasser())
	main.set_meta("erkunden_wasser", [{"c": Vector2(0, -2.0), "r": 1.5, "spiegel": 0.4}])
	ok("am Wasser", sa.am_wasser())
	sa.tu("auffuellen")
	ok("aufgefüllt (%d L)" % RS.anzahl(sa.rs(), "wasser"), RS.anzahl(sa.rs(), "wasser") == 3)
	main.remove_meta("erkunden_wasser")
	sa.tu("kochen")
	ok("Kochen: braucht Proviant, eine Portion weniger", RS.anzahl(sa.rs(), "essen") == n_e - 2)
	# ---- strength ----
	_ctl({"action": "explore", "kraft_echt": true})
	ok("Kraft «Echt»", bool(sa.echt()))
	sa.kraft = 100.0
	p.test_walk(Vector2(1, 0), 3.0, true)
	await wait(3.1)
	var k1: float = sa.kraft
	print("  Kraft nach 3 s rennen: %.1f" % k1)
	ok("rennen macht müde", k1 < 99.0)
	_ctl({"action": "explore", "rucksack": {"pack": "70", "n": {"essen": 1, "apotheke": 1, "seil": 1, "ministativ": 1, "powerbank": 1, "kuppelzelt": 1, "sommerschlafsack": 1}}})
	sa.kraft = 100.0
	p.test_walk(Vector2(1, 0), 3.0, true)
	await wait(3.1)
	var k_ohne: float = 100.0 - sa.kraft
	_ctl({"action": "explore", "rucksack": {"pack": "70", "n": {"essen": 1, "apotheke": 1, "seil": 1, "ministativ": 1, "powerbank": 1, "kuppelzelt": 1, "sommerschlafsack": 1, "stoecke": 1}}})
	sa.kraft = 100.0
	p.test_walk(Vector2(1, 0), 3.0, true)
	await wait(3.1)
	var k_mit: float = 100.0 - sa.kraft
	print("  verbraucht ohne / mit Stöcken: %.2f / %.2f" % [k_ohne, k_mit])
	ok("Stöcke: weniger müde", k_mit < k_ohne)
	sa.kraft = 40.0
	p.set_haltung("sitzen")
	await wait(1.5)
	ok("sitzen: Kraft kommt zurück (%.1f)" % sa.kraft, sa.kraft > 40.5)
	p.set_haltung("stehen")
	sa.kraft = 5.0
	ok("ohne Kraft: langsamer, kein Rennen", sa.tempo_faktor() < 0.7 and not sa.darf_rennen())
	sa.gelandet(3.0)
	ok("harter Sturz: verletzt", bool(sa.verletzt))
	sa.tu("erste_hilfe")
	ok("Erste Hilfe: wieder gut", not bool(sa.verletzt))
	_ctl({"action": "explore", "kraft_echt": false})
	await wait(0.3)
	ok("«Entspannt»: Kraft wieder voll", is_equal_approx(sa.kraft, 100.0) and sa.tempo_faktor() > 0.99)
	# ---- snow, ice axe ----
	main.weather = "snow"
	ok("Schnee ohne Pickel: langsamer", sa.auf_schnee() and sa.tempo_faktor() < 0.8)
	_ctl({"action": "explore", "rucksack": {"pack": "70", "n": {"pickel": 1, "seil": 1, "ministativ": 1, "powerbank": 1, "kuppelzelt": 1, "sommerschlafsack": 1}}})
	ok("Schnee mit Pickel: normal", sa.tempo_faktor() > 0.99)
	var gf_alt: Callable = main.ground_fn
	main.ground_fn = func(_x: float, z: float) -> float: return 3.0 if z < -1.5 else 0.0
	p.figur.setzen(Vector3(0, 0, -0.8), 0.0)
	await wait(0.3)
	await _key(KEY_E)
	await wait(0.1)
	ok("mit Pickel im Schnee: 3-m-Kante hoch", str(p.figur.zustand) == "klettern")
	await wait(3.0)
	main.weather = "clear"
	# ---- the rope ----
	main.ground_fn = func(_x: float, z: float) -> float: return -6.0 if z < -1.0 else 0.0
	p.figur.setzen(Vector3(0, 0, -0.3), 0.0)
	await wait(0.3)
	ok("Kante 6 m vor der Figur", not sa.abgrund().is_empty())
	await _key(KEY_E)
	await wait(0.2)
	ok("E mit Seil: abseilen", bool(p.state()["abseilen"]))
	await wait(6.5)
	print("  nach dem Abseilen: y %.2f, %s" % [p.figur.y, p.figur.zustand])
	ok("unten angekommen (y -6)", absf(p.figur.y + 6.0) < 0.1 and str(p.figur.zustand) == "boden" and not bool(p.state()["abseilen"]))
	main.ground_fn = gf_alt
	p.figur.setzen(Vector3(3, 0, 3), 0.0)
	await wait(0.3)
	# ---- MoveEye on the tripod ----
	sa.tu("moveeye")
	ok("MoveEye hier aufgestellt", Vector2(main.rig.position.x, main.rig.position.z).distance_to(Vector2(3, 2.4)) < 0.8)
	# ---- the night ----
	main.set_hour(22.0)
	sa.kraft = 30.0
	_ctl({"action": "explore", "kraft_echt": true})
	sa.kraft = 30.0
	sa.tu("uebernachten")
	await wait(0.3)
	ok("übernachtet: Lager steht, Morgen 7 Uhr, Kraft voll", bool(sa.info()["lager"]) and absf(main.hour() - 7.0) < 0.2 and sa.kraft > 99.0)
	ok("… die Figur liegt", p.haltung == "liegen")
	_ctl({"action": "explore", "kraft_echt": false})
	# ---- the menu ----
	await _key(KEY_R)
	ok("R: Menü Rucksack", bool(sa.menu_offen()) and sa.aktionen().size() >= 10)
	await _key(KEY_ESCAPE)
	ok("Esc: Menü zu (Erkunden bleibt an)", not bool(sa.menu_offen()) and ex.on)
	ex.set_on(false)
	await wait(0.3)
	ok("Erkunden aus: Lager weg", not bool(sa.info().get("lager", false)) if p.ok() else sa.lager == null)
	if errs.is_empty():
		print("Erkunden-Sachen-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Erkunden-Sachen-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
