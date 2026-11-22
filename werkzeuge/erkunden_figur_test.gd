extends SceneTree
## Test «Frei erkunden mit eigener Figur», Etappe 2 (Besitzer 21.11.2026), ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/erkunden_figur_test.gd" -- --no-update --no-tour
## Prüft:
##   1. Ab Werk: MoveEye sieht die Figur, Auge-Symbol an (Besitzer), Blinki an, Maggie aus; erkunden_figur.norm füllt auf,
##      verwirft Unbekanntes, Bart nur für erwachsene Männer.
##   2. «Figur gestalten» (Knopf «🎨 Figur», Steuerbefehl): öffnet, Vorschau = Kamera vor der Figur; Knöpfe ändern die Figur
##      sofort (Kind kleiner als Jugendlich kleiner als Erwachsen, Jackenfarbe, Bart, Kapuze, Feldstecher, Stöcke, Stirnlampe),
##      «Zufall», «Zurücksetzen», «Fertig»; die Wahl bleibt in den Einstellungen (auch nach dem Laden).
##   3. Maggie: kommt mit (folgt), kommt nach einem Sprung von 40 m wieder dazu, geht weg, wenn ausgeschaltet.
##   4. Blinki: sichtbar und sagt etwas; aus = weg.
##   5. MoveEye: die Figur vor der Kamera = «MoveEye sieht dich» (Auge offen); Schalter aus = kein Netz der Figur mehr auf den
##      Ebenen der Kameras von MoveEye (1 = Bild, 2 = Wärmebild), Auge durchgestrichen; wieder an = wie vorher. Auge aus = weg.
## Ende: «Erkunden-Figur-Test OK» oder «SCRIPT ERROR: Erkunden-Figur-Test: …» (Exit-Code 0 / 1).

const EF = preload("res://scripts/erkunden_figur.gd")

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


func _mw_netze(a: Node) -> int:
	"""meshes of the figure the cameras of MoveEye render (layer 1 picture, layer 2 thermal)"""
	var n := 0
	for g in a.find_children("*", "GeometryInstance3D", true, false):
		if ((g as GeometryInstance3D).layers & 3) != 0 and (g as GeometryInstance3D).is_visible_in_tree():
			n += 1
	return n


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false
	main.set_scene("camping")
	await wait(2.0)
	main.clear_obstacles()
	main.home_pos = Vector3.ZERO
	main.mover_home()
	var ex = main.explore
	# ---- 1. defaults, data ----
	ok("ab Werk: MoveEye sieht die Figur", bool(main.ex_mw_sieht))
	ok("ab Werk: Auge-Symbol an (Besitzer)", bool(main.ex_auge))
	ok("ab Werk: Blinki an, Maggie aus", bool(main.ex_blinki) and not bool(main.ex_maggie))
	var n0: Dictionary = EF.norm({"sex": "x", "alter": "teen", "jacke": "zzz", "bart": true})
	ok("norm: Unbekanntes verworfen, Rest ab Werk", str(n0["sex"]) == "f" and str(n0["alter"]) == "teen" and str(n0["jacke"]) == str(EF.DEFAULT["jacke"]))
	ok("norm: Bart nur für erwachsene Männer", not bool(n0["bart"]) and bool(EF.norm({"sex": "m", "alter": "erw", "bart": true})["bart"]))
	main.ex_figur = EF.DEFAULT.duplicate()
	_ctl({"action": "spielbereich", "do": "frei"})
	await wait(0.6)
	var p = ex.person
	ok("Frei erkunden: als Figur", ex.person_on() and p.ok())
	ok("Knopf «🎨 Figur» sichtbar", ex._btn_figur.visible)
	# ---- 2. the window ----
	ex._btn_figur.pressed.emit()
	await wait(0.4)
	var g = p.gestalten
	ok("Figur gestalten: offen", bool(g.offen) and g.panel.visible)
	var cam: Camera3D = main.view_cam
	var mid: Vector3 = p.actor.global_position + Vector3(0, 1.0, 0)
	ok("Vorschau: Kamera vor der Figur (%.1f m)" % cam.global_position.distance_to(mid), cam.global_position.distance_to(mid) < 6.5 and cam.is_position_in_frustum(mid))
	var to_cam: Vector3 = cam.global_position - p.actor.global_position
	var fw := Vector3(-sin(float(p.actor.heading)), 0, -cos(float(p.actor.heading)))
	ok("die Figur schaut zur Kamera", fw.dot(Vector3(to_cam.x, 0, to_cam.z).normalized()) > 0.8)
	ok("Knöpfe gebaut (%d)" % int(g.info()["knoepfe"]), int(g.info()["knoepfe"]) >= 8)
	await wait(1.0)
	var h_erw: float = p.hoehe()
	ok("Knopf Alter: Kind", g.druecke("alter=kind"))
	await wait(1.0)
	var h_kind: float = p.hoehe()
	ok("Kind: eigene Figur (variant child)", str(p.actor.get("variant")) == "child")
	g.druecke("alter=teen")
	await wait(1.0)
	var h_teen: float = p.hoehe()
	print("  Höhe: Kind %.2f · Jugendlich %.2f · Erwachsen %.2f" % [h_kind, h_teen, h_erw])
	ok("Kind < Jugendlich < Erwachsen", h_kind < h_teen - 0.1 and h_teen < h_erw - 0.05)
	g.druecke("alter=erw")
	g.druecke("reiter:kleider")
	ok("Knopf Jacke grün", g.druecke("jacke=2e8c4d"))
	await wait(0.3)
	ok("Jacke ist grün", (p.actor.get("_jacket_c") as Color).is_equal_approx(Color.html("2e8c4d")))
	ok("gespeichert in main.ex_figur", str(main.ex_figur["jacke"]) == "2e8c4d")
	g.druecke("hut=kapuze")
	await wait(0.2)
	ok("Kapuze", str(p.actor.look.get("hat", "")) == "hood")
	g.druecke("reiter:person")
	g.druecke("sex=m")
	g.druecke("reiter:kopf")
	ok("Bart wählbar (Mann, erwachsen)", g.druecke("bart=true"))
	await wait(0.2)
	ok("Bart da", bool(p.figur_wahl()["bart"]))
	g.druecke("reiter:person")
	g.druecke("sex=f")
	await wait(0.2)
	ok("Frau: kein Bart mehr", not bool(p.figur_wahl()["bart"]))
	g.druecke("reiter:kopf")
	ok("Bart gesperrt für Frauen", not g.druecke("bart=true"))
	g.druecke("reiter:ausruestung")
	var n_vor: int = p.actor.find_children("*", "MeshInstance3D", true, false).size()
	g.druecke("feldstecher=true")
	g.druecke("stoecke=true")
	g.druecke("stirnlampe=true")
	await wait(0.4)
	var n_nach: int = p.actor.find_children("*", "MeshInstance3D", true, false).size()
	ok("Feldstecher und Stöcke: mehr Teile (%d → %d)" % [n_vor, n_nach], n_nach > n_vor)
	ok("Stirnlampe", p.actor.get("lamp") != null)
	var f_alt: Dictionary = p.figur_wahl()
	g.druecke("zufall")
	await wait(0.2)
	ok("Zufall ändert die Figur", str(p.figur_wahl()) != str(f_alt))
	g.druecke("zurueck")
	await wait(0.2)
	ok("Zurücksetzen = ab Werk", str(p.figur_wahl()) == str(EF.norm(EF.DEFAULT)))
	g.druecke("reiter:kleider")
	g.druecke("hose=2e3d59")
	main._save_settings()
	var saved = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	ok("Figur in den Einstellungen gespeichert", saved is Dictionary and saved.get("ex_figur", {}) is Dictionary and str(saved["ex_figur"].get("hose", "")) == "2e3d59")
	main.ex_figur = {}
	main._load_settings()
	ok("… und wieder geladen", main.ex_figur is Dictionary and str(main.ex_figur.get("hose", "")) == "2e3d59")
	g.druecke("fertig")
	await wait(0.6)
	ok("Fertig: zu, Kamera wieder hinter der Figur", not bool(g.offen) and main.view_cam.global_position.distance_to(p.actor.global_position) < 8.0)
	_ctl({"action": "explore", "gestalten": true})
	ok("Steuerbefehl gestalten", bool(g.offen))
	_ctl({"action": "explore", "gestalten": false, "figur": {"alter": "teen", "jacke": "e6731a"}})
	await wait(0.2)
	ok("Steuerbefehl figur", str(p.figur_wahl()["alter"]) == "teen" and str(p.figur_wahl()["jacke"]) == "e6731a" and not bool(g.offen))
	# ---- 3. Maggie ----
	p.figur.setzen(Vector3(0, 0, 0), 0.0)
	_ctl({"action": "explore", "maggie": true})
	await wait(0.5)
	var b = p.begleiter
	ok("Maggie kommt mit", bool(b.info()["maggie"]) and b.hund.get("leader") == p.actor)
	p.test_walk(Vector2(1, 0), 3.0, false)
	await wait(3.5)
	var md: float = float(b.info()["maggie_d"])
	ok("Maggie folgt (%.1f m)" % md, md >= 0.0 and md < 6.0)
	p.place(Vector3(40, 0, -10))
	await wait(0.5)
	md = float(b.info()["maggie_d"])
	ok("Maggie nach 40 m wieder da (%.1f m)" % md, md >= 0.0 and md < 4.0)
	_ctl({"action": "explore", "maggie": false})
	await wait(0.3)
	ok("Maggie aus: weg", not bool(b.info()["maggie"]))
	# ---- 4. Blinki ----
	ok("Blinki sichtbar", bool(b.info()["blinki"]))
	b.sag("Test", 3.0)
	await wait(0.3)
	ok("Blinki sagt etwas", str(b.info()["blinki_sagt"]) == "Test")
	_ctl({"action": "explore", "blinki": false})
	await wait(0.3)
	ok("Blinki aus: weg", not bool(b.info()["blinki"]))
	_ctl({"action": "explore", "blinki": true})
	# ---- 5. MoveEye sees the figure ----
	var mc: Camera3D = main.cams[0]
	var cf := -mc.global_transform.basis.z
	cf.y = 0.0
	cf = cf.normalized()
	p.place(mc.global_position + cf * 7.0)
	await wait(1.0)
	var ib: Dictionary = b.info()
	ok("vor der Kamera: MoveEye sieht dich", bool(ib["sieht"]) and str(ib["auge_zustand"]) == "open" and bool(ib["auge"]))
	var nn: int = _mw_netze(p.actor)
	ok("Netze für MoveEye (%d)" % nn, nn > 0)
	_ctl({"action": "explore", "mw_sieht": false})
	await wait(0.6)
	ib = b.info()
	ok("Schalter aus: kein Netz mehr für MoveEye (%d)" % _mw_netze(p.actor), _mw_netze(p.actor) == 0)
	ok("Schalter aus: man selbst sieht sie noch", p.actor.is_visible_in_tree())
	ok("Schalter aus: Auge durchgestrichen, sieht nicht", not bool(ib["sieht"]) and str(ib["auge_zustand"]) == "off")
	_ctl({"action": "explore", "figur": {"jacke": "1f2961"}})        # rebuilt while off: stays hidden
	await wait(0.4)
	ok("neu gebaut, bleibt für MoveEye unsichtbar", _mw_netze(p.actor) == 0)
	_ctl({"action": "explore", "mw_sieht": true})
	await wait(0.6)
	ok("Schalter wieder an: wie vorher (%d)" % _mw_netze(p.actor), _mw_netze(p.actor) > 0 and bool(b.info()["sieht"]))
	p.place(mc.global_position - cf * 12.0)                 # behind the camera
	await wait(0.6)
	ok("hinter der Kamera: nicht im Bild", not bool(b.info()["sieht"]) and str(b.info()["auge_zustand"]) == "shut")
	_ctl({"action": "explore", "auge": false})
	await wait(0.3)
	ok("Auge-Symbol aus: weg", not bool(b.info()["auge"]))
	_ctl({"action": "explore", "auge": true})
	ex.set_on(false)
	await wait(0.3)
	ok("Erkunden aus: Figur, Auge, Blinki weg", p.actor == null and not b.auge.visible and not b.blinki.visible)
	if errs.is_empty():
		print("Erkunden-Figur-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		printerr("SCRIPT ERROR: Erkunden-Figur-Test: ", "; ".join(PackedStringArray(errs)))
		quit(1)
