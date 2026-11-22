extends SceneTree
## Test «Camp aufstellen» beim Frei erkunden (Fragebogen des Besitzers 22.11.2026): erkunden_camp.gd, erkunden_camp_daten.gd,
## erkunden_ruhe.gd und der Haken in simreal.gd (lose Zeltplane).
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/erkunden_camp_test.gd" -- --no-update --no-tour
## Prüft: Regeln zum Aufstellen (zu steil je Schlafplatz, zu nah, Feuer 3 m vom Zelt, im Wasser, nur was im Rucksack ist),
## die Vorschau (grün / rot, drehen, Aufstellen mit Aufbau-Zeit), das Feuer (anzünden, Glut, aus, löschen, Glut-Wächter),
## Einpacken (das Feuer muss zuerst aus sein, einzeln und «Alles einpacken»), die lose Zeltplane nur mit Tarp im Rucksack
## (danach wieder wie vorher), ein stehen gelassenes Camp speichern und beim nächsten Mal wieder aufbauen, die Frage beim
## Verlassen, die Nacht (spulen mit Bericht, Live), den ruhigen Bildschirm (Fenster weg, danach genau wie vorher).
## Ende: «Erkunden-Camp-Test OK» oder «SCRIPT ERROR: Erkunden-Camp-Test: …».

const RS = preload("res://scripts/erkunden_rucksack.gd")
const D = preload("res://scripts/erkunden_camp_daten.gd")

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


func _regeln() -> void:
	"""the rules alone (erkunden_camp_daten.gd)"""
	var p0 := Vector2.ZERO
	ok("Zelt auf 6°: grün", bool(D.pruefen("kuppelzelt", p0, 6.0, false, [])["ok"]))
	ok("Zelt auf 9°: rot, zu steil", not bool(D.pruefen("kuppelzelt", p0, 9.0, false, [])["ok"]) and str(D.pruefen("kuppelzelt", p0, 9.0, false, [])["farbe"]) == "rot")
	ok("Biwaksack auf 11°: grün (bis 12° wie bergtal.gd)", bool(D.pruefen("biwaksack", p0, 11.0, false, [])["ok"]))
	ok("Grenzen wie bergtal.gd flat_limit", is_equal_approx(float(D.ding("kuppelzelt")["steil"]), preload("res://scripts/bergtal.gd").flat_limit("tent"))
			and is_equal_approx(float(D.ding("biwaksack")["steil"]), preload("res://scripts/bergtal.gd").flat_limit("bivy")))
	ok("im Wasser: rot", not bool(D.pruefen("isomatte", p0, 0.0, true, [])["ok"]))
	var zelt := [{"id": "kuppelzelt", "x": 0.0, "z": 0.0}]
	ok("Rucksack 1 m neben dem Zelt: rot (zu nah)", not bool(D.pruefen("rucksack", Vector2(1.0, 0), 0.0, false, zelt)["ok"]))
	ok("Rucksack 2,5 m neben dem Zelt: grün", bool(D.pruefen("rucksack", Vector2(2.5, 0), 0.0, false, zelt)["ok"]))
	ok("Feuer 3,5 m vom Zelt: rot (Funken, mind. 3 m vom Rand)", not bool(D.pruefen("feuerstelle", Vector2(3.5, 0), 0.0, false, zelt)["ok"]))
	ok("Feuer 5,5 m vom Zelt: grün", bool(D.pruefen("feuerstelle", Vector2(5.5, 0), 0.0, false, zelt)["ok"]))
	var leer := RS.norm({"pack": "50", "n": {}})
	ok("nur was im Rucksack ist: leer = nur der Rucksack selbst", D.moeglich(leer, []) == ["rucksack"])
	var r := RS.norm({"pack": "70", "n": {"einmannzelt": 1, "isomatte": 1, "zuendhoelzer": 1, "kocher": 1, "ministativ": 1, "stuhl": 1}})
	ok("Isomatte ohne Schlafsack: nicht", D.verfuegbar(r, "isomatte") != "")
	ok("im Rucksack: Einmannzelt, Feuerstelle, Kocher, Stuhl, MoveEye", D.moeglich(r, []) == ["einmannzelt", "feuerstelle", "kocher", "rucksack", "stuhl", "moveeye"])
	ok("… jedes Ding nur einmal", not D.moeglich(r, [{"id": "einmannzelt"}]).has("einmannzelt"))
	ok("Hinweis Bach, Steinschlag, Wildruhezone", D.hinweise("einmannzelt", 2.0, {"bach_m": 5.0, "steinschlag": 0.6, "wildruhezone": {"name": "Test", "z": "1.1.–1.5."}}).size() == 3)
	ok("Feuerverbot: Wald, Schutzgebiet, Trockenheit", D.feuer_verbot({"wald": true, "schutz": true, "trocken": true}).size() == 3 and D.feuer_verbot({}).is_empty())
	# the fire
	var f := D.feuer_neu()
	ok("Feuer neu: aus", D.ist_aus(f))
	f = D.anzuenden(f)["f"]
	ok("angezündet: brennt, %d °C" % int(D.temp(f, 10.0)), str(f["phase"]) == "brennt" and D.temp(f, 10.0) > 500.0)
	ok("brennt: nicht einpacken", D.darf_einpacken("feuerstelle", [{"id": "feuerstelle"}], f) != "" and D.darf_einpacken("*", [{"id": "feuerstelle"}], f) != "")
	f = D.nachlegen(f)["f"]
	ok("nachgelegt: 2 Scheite", is_equal_approx(float(f["holz"]), 2.0))
	f = D.ticken(f, D.HOLZ_S * 2.0 + 1.0, 22.0)
	ok("heruntergebrannt: Glut (%d °C)" % int(D.temp(f, 10.0)), str(f["phase"]) == "glut" and D.temp(f, 10.0) > D.T_AUS)
	ok("Glut: immer noch nicht einpacken", D.darf_einpacken("feuerstelle", [{"id": "feuerstelle"}], f) != "")
	var f2: Dictionary = D.nachlegen(f)["f"]
	ok("Holz auf die Glut: brennt wieder", str(f2["phase"]) == "brennt")
	f = D.ticken(f, D.GLUT_S + 1.0, 22.0)
	ok("Glut kalt: aus, «aus seit» gesetzt", D.ist_aus(f) and float(f["aus_seit"]) > 22.0)
	ok("aus: einpacken erlaubt", D.darf_einpacken("feuerstelle", [{"id": "feuerstelle"}], f) == "")
	var f3: Dictionary = D.loeschen(D.anzuenden(D.feuer_neu())["f"])["f"]
	ok("gelöscht: dampft zuerst noch (nicht aus)", not D.ist_aus(f3))
	f3 = D.ticken(f3, D.GELOESCHT_S + 1.0)
	ok("… nach einer halben Minute aus", D.ist_aus(f3))
	ok("eine ganze Nacht auf einmal: aus", D.ist_aus(D.ticken(D.anzuenden(D.feuer_neu())["f"], 8.0 * 3600.0)))
	# saving
	ok("Camp-Daten: Unsinn = leer", D.camp_norm({"scene": "x", "stehen": [{"id": "gibtsnicht"}]}).is_empty() and D.camp_norm(null).is_empty())
	var c := D.camp_norm({"scene": "camping", "stehen": [{"id": "tarp", "x": 1, "z": 2}, {"id": "tarp", "x": 3}], "feuer": {"phase": "quatsch"}})
	ok("Camp-Daten: doppelt nur einmal, falsches Feuer = aus", (c["stehen"] as Array).size() == 1 and str(c["feuer"]["phase"]) == "aus")
	# the night
	var plan := D.nacht_plan(7, {"tiere": 1.0, "leute": 1.0, "wind": 1.0})
	ok("Nachtplan fest (gleicher Zufall = gleiche Nacht), %d Ereignisse" % plan.size(), plan == D.nacht_plan(7, {"tiere": 1.0, "leute": 1.0, "wind": 1.0}) and plan.size() >= 2)
	ok("MoveEye sieht nur im Bildwinkel, ohne MoveEye nichts", D.gesehen({"art": "fuchs", "winkel": 0.2}, true, 0.0) and not D.gesehen({"art": "fuchs", "winkel": 2.5}, true, 0.0)
			and not D.gesehen({"art": "fuchs", "winkel": 0.0}, false, 0.0))


func _run() -> void:
	_regeln()
	await wait(2.0)
	main.eco_idle = false
	main.news_popup = false
	main.set_scene("camping")
	await wait(2.0)
	if main.news != null:
		main.news.visible = false
	main.clear_obstacles()
	main.weather = "clear"
	main.set_hour(14.0)
	var ex = main.explore
	var sr = main.simreal
	ok("lose Zeltplane in der Szene (simreal.gd)", sr.zeltplane != null and is_instance_valid(sr.zeltplane) and sr.zeltplane.visible)
	# ---- the clean screen: what is on the screen before ----
	var vorher := {}
	for n in [main.toolbar, main.minimap, main.view_bar, main.get("handy")]:
		if n != null and n is CanvasItem:
			vorher[n] = (n as CanvasItem).visible
	var ui_vorher: bool = main.ui_root.visible
	main.ex_rucksack = RS.norm({"pack": "70", "n": {"einmannzelt": 1, "isomatte": 1, "sommerschlafsack": 1, "zuendhoelzer": 1, "kocher": 1,
			"ministativ": 1, "powerbank": 1, "stuhl": 1, "essen": 2}})
	var cdatei := "user://erkunden_camp_test.json"
	if FileAccess.file_exists(cdatei):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(cdatei))
	ex.frei_erkunden()
	var p = ex.person
	var cp = p.camp
	var ru = p.ruhe
	cp.datei = cdatei                                     # (before the first frame: never the real file)
	await wait(0.8)
	ok("Frei erkunden: Camp und ruhiger Bildschirm da", ex.person_on() and cp != null and ru != null)
	ok("ruhiger Bildschirm an, %d Fenster weg (%s)" % [int(ru.info()["versteckt"]), ", ".join(PackedStringArray(ru.info()["namen"]))], bool(ru.info()["an"]) and int(ru.info()["versteckt"]) >= 1)
	var noch := []
	for n in vorher:
		if is_instance_valid(n) and (n as CanvasItem).visible:
			noch.append(str(n.name))
	ok("… Leisten / Karte / Handy-Leiste weg (noch sichtbar: %s)" % ", ".join(PackedStringArray(noch)), noch.is_empty())
	ok("… der grüne Stick, Camp-Knopf und «☰ Menü» bleiben", (main.rover_pad == null or ru._erlaubt(main.rover_pad)) and cp.knopf.visible and ru.knopf.visible)
	ru.set_menu(true)
	await wait(0.2)
	ok("☰ Menü: alles wieder da (Bedienfeld offen)", not bool(ru.info()["an"]) and main.ui_root.visible)
	ru.set_menu(false)
	await wait(0.4)
	ok("☰ nochmals: wieder ruhig", bool(ru.info()["an"]) and not main.ui_root.visible)
	# ---- the loose tarp: no tarp in the pack ----
	await wait(0.2)
	ok("ohne Tarp im Rucksack: lose Zeltplane weg", not sr.zeltplane.visible)
	main.ex_rucksack = RS.dazu(RS.norm(main.ex_rucksack), "tarp", 1)["d"]
	await wait(0.2)
	ok("mit Tarp im Rucksack: die Zeltplane ist da (die eigene)", sr.zeltplane.visible)
	main.ex_rucksack = RS.dazu(RS.norm(main.ex_rucksack), "tarp", -1)["d"]
	await wait(0.2)
	# ---- placing: the preview ----
	p.place(Vector3(0, 0, 0))
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	await wait(0.4)
	await _key(KEY_TAB)
	ok("… offen, bietet nur was im Rucksack ist", cp.menu_offen() and (cp.info()["moeglich"] as Array).has("einmannzelt") and not (cp.info()["moeglich"] as Array).has("kuppelzelt"))
	await _key(KEY_TAB)
	ok("vorschau: Kuppelzelt nicht im Rucksack", not cp.vorschau_start("kuppelzelt"))
	ok("Vorschau Einmannzelt", cp.vorschau_start("einmannzelt"))
	await wait(0.4)
	ok("flach: grün (%s)" % str(cp.info()["platz"]), str(cp.info()["platz"].get("farbe", "")) == "gruen")
	var yaw0: float = cp.platz["yaw"]
	await _key(KEY_E)
	await wait(0.3)
	ok("E: gedreht", absf(wrapf(float(cp.platz["yaw"]) - yaw0 - PI / 8.0, -PI, PI)) < 0.05)
	var gf_alt: Callable = main.ground_fn
	main.ground_fn = func(x: float, _z: float) -> float: return x * 0.2     # 11°: too steep for a tent
	await wait(0.4)
	ok("steil 11°: rot (%s)" % str(cp.info()["platz"].get("grund", "")), str(cp.info()["platz"].get("farbe", "")) == "rot" and not bool(cp.aufstellen()))
	main.ground_fn = gf_alt
	main.set_meta("erkunden_wasser", [{"c": Vector2(cp.platz["p"].x, cp.platz["p"].z), "r": 2.0, "spiegel": 0.6}])
	await wait(0.4)
	ok("im Wasser: rot (%s)" % str(cp.info()["platz"].get("grund", "")), str(cp.info()["platz"].get("farbe", "")) == "rot")
	main.remove_meta("erkunden_wasser")
	await wait(0.4)
	await _key(KEY_ENTER)
	ok("Enter: Aufbau läuft, die Figur kniet", cp.info()["bau"] == "einmannzelt" and p.haltung == "geduckt")
	await wait(4.2)
	ok("nach ein paar Sekunden: Zelt steht, Figur steht auf", cp.hat("einmannzelt") and cp.info()["bau"] == "" and p.haltung == "stehen")
	var zp: Vector3 = cp._ding_pos("einmannzelt")
	ok("zu nah: Stuhl direkt neben dem Zelt geht nicht", not cp.setzen("stuhl", zp + Vector3(0.6, 0, 0)))
	ok("Feuer 2,5 m vom Zelt: nicht (Funken)", not cp.setzen("feuerstelle", zp + Vector3(2.5, 0, 0)))
	ok("Feuer 6 m vom Zelt: ja", cp.setzen("feuerstelle", zp + Vector3(6.0, 0, 0)))
	ok("Stuhl, Kocher, MoveEye auf dem Mini-Stativ", cp.setzen("stuhl", zp + Vector3(4.0, 0, 2.5)) and cp.setzen("kocher", zp + Vector3(4.0, 0, -2.5))
			and cp.setzen("moveeye", zp + Vector3(3.0, 0, 5.0)))
	ok("MoveEye steht im Camp, Kopf tief (%.2f m)" % main.mast_h, Vector2(main.rig.position.x, main.rig.position.z).distance_to(Vector2(zp.x + 3.0, zp.z + 5.0)) < 0.1
			and main.mast_h < 0.5)
	# ---- the fire ----
	main.set_meta("erkunden_camp_umgebung", {"wald": true})
	ok("Feuerverbot (Wald): zuerst die Frage", not cp.anzuenden() and cp.dialog == "verbot")
	cp._dlg_zu()
	main.remove_meta("erkunden_camp_umgebung")
	ok("anzünden", cp.anzuenden() and str(cp.feuer["phase"]) == "brennt")
	ok("Holz nachlegen", cp.nachlegen() and float(cp.feuer["holz"]) > 1.5)
	var gl: Dictionary = cp.glut_pruefen()
	ok("Glut-Wächter: brennt (%s)" % str(gl), str(gl["status"]) in ["brennt", "sieht_nicht"])
	ok("brennt: Feuerstelle nicht einpacken", not cp.einpacken("feuerstelle") and cp.hat("feuerstelle"))
	ok("brennt: «Alles einpacken» nicht", not cp.einpacken("*") and cp.hat("einmannzelt"))
	ok("kochen am Feuer (Entspannt: geht, ohne Wirkung)", cp.kochen() and RS.anzahl(cp.rs(), "essen") == 2)
	main.ex_kraft_echt = true
	p.sachen.hunger = 40.0
	ok("kochen mit «Echt»: satt, eine Portion weniger", cp.kochen() and p.sachen.hunger > 99.0 and RS.anzahl(cp.rs(), "essen") == 1)
	p.sachen.waerme = 50.0
	p.place(zp + Vector3(6.0, 0, 1.6))
	cp._feuer_tick(2.0)
	ok("am Feuer wird es warm («Echt»)", p.sachen.waerme > 51.0)
	main.ex_kraft_echt = false
	cp._feuer_tick(D.HOLZ_S * 3.0)
	ok("heruntergebrannt: Glut", str(cp.feuer["phase"]) == "glut")
	cp._feuer_tick(D.GLUT_S + 5.0)
	gl = cp.glut_pruefen()
	ok("Glut-Wächter: aus (%s)" % str(gl), str(gl["status"]) in ["aus", "sieht_nicht"] and D.ist_aus(cp.feuer))
	ok("aus: Feuerstelle einpacken", cp.einpacken("feuerstelle") and not cp.hat("feuerstelle"))
	ok("wieder aufstellen und löschen", cp.setzen("feuerstelle", zp + Vector3(6.0, 0, 0)) and cp.anzuenden() and cp.loeschen())
	ok("gelöscht, dampft: noch nicht einpacken", not cp.einpacken("feuerstelle"))
	cp._feuer_tick(D.GELOESCHT_S + 1.0)
	# ---- the night ----
	main.set_hour(22.0)
	p.place(zp + Vector3(0.5, 0, 0.5))
	await wait(0.3)
	p.set_haltung("liegen")
	await wait(0.3)
	ok("hinlegen am Schlafplatz: Wahl der Nacht", cp.dialog == "nacht")
	var ber: Array = cp.nacht_spulen()
	print("  Bericht: ", ber)
	ok("Nacht gespult: 7 Uhr, Bericht am Morgen", absf(main.hour() - 7.0) < 0.2 and not ber.is_empty() and cp.dialog == "morgen")
	cp._dlg_zu()
	p.set_haltung("stehen")
	await wait(0.2)
	p.set_haltung("liegen")
	await wait(0.3)
	ok("… nochmals hinlegen: Wahl", cp.dialog == "nacht")
	cp.nacht_live()
	ok("Live: kein Dialog, Uhr läuft normal", cp.dialog == "" and main.hour() < 7.5)
	p.set_haltung("stehen")
	# ---- leaving: the question ----
	ok("Esc mit Camp: zuerst die Frage", cp.frage_beim_ende(func(): ex.set_on(false)) and cp.dialog == "ende")
	cp._dlg_zu()
	ok("Weiter erkunden: Erkunden bleibt an", ex.on)
	# leaving the camp standing (as the dialog does): saved, place remembered
	cp._ende_danach = func(): ex.set_on(false)
	cp.stehen_lassen()
	cp._ende_fertig()
	await wait(0.4)
	ok("stehen gelassen: gespeichert, Ort gemerkt, Erkunden aus", FileAccess.file_exists(cdatei) and not ex.on and str(main.ex_ort.get("scene", "")) == "camping")
	ok("Mover wieder wie vorher (nicht mehr auf dem Mini-Stativ)", main.mast_h > 0.5)
	var bleibt := []
	for n in vorher:
		if is_instance_valid(n) and (n as CanvasItem).visible != bool(vorher[n]):
			bleibt.append(str(n.name))
	ok("ruhiger Bildschirm aus: alles wie vorher (anders: %s)" % ", ".join(PackedStringArray(bleibt)), bleibt.is_empty() and main.ui_root.visible == ui_vorher)
	ok("lose Zeltplane wieder wie vorher (da)", sr.zeltplane.visible)
	var gs: Dictionary = cp.gespeichert()
	ok("gespeichert: Zelt, Stuhl, Kocher, MoveEye, Feuerstelle", (gs.get("stehen", []) as Array).size() == 5)
	# ---- next time: the camp is there again ----
	ex.frei_erkunden()
	await wait(0.8)
	ok("nächstes Mal: das Camp steht wieder (%d Dinge)" % cp.stehen.size(), cp.stehen.size() == 5 and cp.hat("einmannzelt") and cp.hat("feuerstelle"))
	ok("… die Figur beginnt beim Camp", Vector2(p.figur.pos().x, p.figur.pos().z).distance_to(Vector2(zp.x, zp.z)) < 5.0)
	ok("… MoveEye wieder auf dem Mini-Stativ", main.mast_h < 0.5)
	# ---- packing up everything ----
	ok("Alles einpacken (Feuer ist aus)", cp.einpacken("*") and cp.stehen.is_empty())
	ok("… die gespeicherte Datei ist weg", not FileAccess.file_exists(cdatei))
	ok("… MoveEye zurück", main.mast_h > 0.5)
	ex.set_on(false)
	await wait(0.3)
	ok("Erkunden aus ohne Camp: nichts gespeichert", not FileAccess.file_exists(cdatei))
	if errs.is_empty():
		print("Erkunden-Camp-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Erkunden-Camp-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
