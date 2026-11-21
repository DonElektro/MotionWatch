extends SceneTree
## Kapitel 1 «Die Karte» (Grossvater Phase 2, 21.11.2026) einmal ganz durchspielen, mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_k1_test.gd" -- --no-update --no-tour
## Die Figur GEHT (Eingabe «ziel» wie ein Spieler mit Stick) von Ziel zu Ziel - durch die Tür in die Stube, zum Ofen, die
## Leiter hoch (Eingabe vorwärts), sucht mit der Stirnlampe die Dose, packt den Rucksack (3 von 6), stellt MoveEye auf, lässt
## Maggie suchen - bis «Ende von Kapitel 1». Filme werden übersprungen. Geprüft: jeder Schritt kommt weiter, die Funde, die
## Wahl, der Dachboden als Ebene (oben fest, unten wieder frei), Licht des Ofens, die Kamera am Start jeder Szene frei.
## Ende: «K1-Test OK» oder «SCRIPT ERROR: K1-Test: …».

var errs: Array = []
var m = null
var k = null


func _init() -> void:
	_lauf.call_deferred()


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func c(d: Dictionary) -> Dictionary:
	d["action"] = "kit"
	return m.control(d)


func info() -> Dictionary:
	return c({"do": "info"}).get("kit", {})


func pruef(ok: bool, was: String) -> void:
	print(("ok   " if ok else "FEHL ") + was)
	if not ok:
		errs.append(was + "  " + JSON.stringify(info().get("figur", {})))


func _bis(cond: Callable, secs: float) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call():
			return true
		await _warte(0.1)
		t += 0.1
	return cond.call()


func szene() -> String:
	return str(info().get("szene", ""))


func filme_weg() -> void:
	"""skip the films until the game waits for the player"""
	for i in range(6):
		await _warte(0.4)
		if k.phase == "film":
			c({"do": "skip"})
			await _bis(func(): return k.phase != "film", 4.0)
		elif k.phase == "spiel":
			return


func geh(punkte: Array, r := 0.45) -> bool:
	"""walk like a player over [s, q] points (stick towards the next one)"""
	for p in punkte:
		var w: Vector3 = k.par.welt(float(p[0]), float(p[1]))
		var t := 0.0
		while t < 25.0:
			var fp: Vector3 = k.figur.pos()
			if Vector2(fp.x, fp.z).distance_to(Vector2(w.x, w.z)) < r:
				break
			if k.phase == "film":
				return true                                  # a film started (the goal was reached on the way)
			c({"do": "eingabe", "ziel": [w.x, w.z], "s": 0.3})
			await _warte(0.25)
			t += 0.25
		if t >= 25.0:
			print("     geh: hängt bei ", k.par.sq_von(k.figur.pos()), " auf dem Weg zu ", p)
			return false
	return true


func aktion() -> void:
	c({"do": "eingabe", "mv": [0, 0], "aktion": true, "s": 0.15})
	await _warte(0.5)


func _lauf() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	c({"do": "start", "kapitel": 1, "rolle": "enkelin", "name": "Test", "touch": false})
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) in ["film", "spiel"], 60.0)
	pruef(ok, "Start Kapitel 1")
	if not ok:
		_ende()
		return
	k = m.kit
	pruef(k.kapitel == 1 and str(k.daten.TITEL) == "Die Karte", "Kapitel 1: Daten «Die Karte»")
	pruef(str(m.weather) == "rain", "Regen bei der Ankunft")
	# 1 arrival
	await filme_weg()
	pruef(szene() == "s01_ankunft", "Szene 1: Ankunft")
	ok = await geh([[-12.0, -1.8], [-8.0, -2.1], [-5.2, -2.25]])
	pruef(ok, "zur Hütte gegangen")
	ok = await _bis(func(): return szene() == "s02_ofen", 6.0)
	pruef(ok, "Szene 2: kalte Stube")
	# 2 the stove
	ok = await geh([[-4.2, -2.25], [-2.8, -2.25], [-1.4, -1.0], [0.0, 0.6], [1.6, 2.2]])
	pruef(ok, "durch die Tür zum Ofen")
	await aktion()
	ok = await _bis(func(): return k.erledigt.has("ofen"), 3.0)
	pruef(ok and k.par._ofen_licht != null, "Ofen brennt (Licht, Rauch)")
	await filme_weg()
	ok = await _bis(func(): return szene() == "s03_dachboden", 6.0)
	pruef(ok, "Szene 3: Dachboden")
	# 3 the ladder, the headlamp, the tin box
	ok = await geh([[0.6, 2.9], [-0.15, 3.6]], 0.3)
	pruef(ok, "zur Leiter")
	await aktion()
	pruef(k.figur.zustand == "leiter", "auf der Leiter (%s)" % k.figur.zustand)
	c({"do": "eingabe", "mv": [1, 0], "halten": true, "s": 6.0})
	ok = await _bis(func(): return k.erledigt.has("dach_hoch_oben"), 9.0)
	c({"do": "eingabe", "mv": [0, 0], "s": 0.1})
	pruef(ok and bool(k.par.ebene_an.get("dach", false)), "oben: Dachboden als Ebene an")
	pruef(k.figur.pos().y > m.ground_y(k.par.welt(-6.0, 0.0).x, k.par.welt(-6.0, 0.0).z) + 1.8, "Figur steht 2.5 m über der Stube")
	await _warte(0.6)
	await aktion()
	pruef(k.lampe_an, "Stirnlampe an")
	ok = await geh([[0.4, 0.0], [0.3, -2.9]], 0.4)
	pruef(ok, "zur Ecke mit der Dose")
	var ziel: Vector3 = k.par.welt(0.25, -3.7)
	var d3: Vector3 = ziel - k.figur.pos()
	k.figur.a.heading = atan2(-d3.x, -d3.z)
	k.figur.a.rotation.y = k.figur.a.heading
	await _warte(0.5)
	pruef((k.par.dinge["dose"]["node"] as Node3D).visible, "die Dose glänzt im Licht der Stirnlampe")
	await aktion()
	ok = await _bis(func(): return k.funde.has("dose"), 3.0)
	pruef(ok, "Dose gefunden")
	# 4 the map, the flashback (it takes the figure down: the attic is off again)
	await filme_weg()
	await filme_weg()
	pruef(not bool(k.par.ebene_an.get("dach", false)), "Dachboden wieder aus (unten in der Stube)")
	# 5 the backpack
	ok = await _bis(func(): return k.hud.wahl_offen(), 8.0)
	pruef(ok, "Rucksack-Karte offen")
	c({"do": "wahl", "ids": ["seil", "kompass", "fernglas"]})
	await _warte(0.4)
	pruef(k.merker.has("rucksack_seil") and k.merker.has("rucksack_fernglas"), "Rucksack gepackt (Seil, Kompass, Fernglas)")
	# 6 MoveEye outside
	await filme_weg()
	ok = await _bis(func(): return szene() == "s06_moveeye", 6.0)
	await filme_weg()
	ok = await geh([[-1.0, 0.0], [-2.6, -2.25], [-3.2, -2.25], [-4.8, -2.25], [-6.0, -1.0], [-7.8, 5.6]])
	pruef(ok, "hinaus zu MoveEye")
	await aktion()
	ok = await _bis(func(): return k.erledigt.has("moveeye"), 3.0)
	pruef(ok, "MoveEye aufgestellt")
	await filme_weg()
	pruef(k.ir_an and m.is_dark(), "Nacht, IR an")
	# 7 the marmot, 8 Maggie fetches
	await filme_weg()
	ok = await _bis(func(): return szene() == "s08_holzstapel", 8.0)
	pruef(ok, "Szene 8: Holzstapel")
	await filme_weg()
	ok = await geh([[-6.0, 3.0], [-4.6, 5.4], [-1.0, 5.4], [0.4, 4.6]])
	pruef(ok, "zum Holzstapel")
	await aktion()
	ok = await _bis(func(): return k.funde.has("kartenecke"), 25.0)
	pruef(ok, "Maggie bringt die Kartenecke")
	# 9, 10 to the end
	for i in range(5):
		await filme_weg()
		if k.phase == "ende":
			break
	ok = await _bis(func(): return k.phase == "ende", 20.0)
	pruef(ok and k.hud._ende != null, "Ende von Kapitel 1")
	pruef(k.funde.has("dose") and k.funde.has("kartenecke"), "Funde: Dose, Kartenecke")
	# the camera at the start of every scene and in the attic: above the ground, under the ceiling, the head in view
	k.phase = "spiel"
	var orte := []
	for sz in k.daten.SZENEN:
		if (sz["start"] as Array).size() >= 2:
			orte.append([str(sz["id"]), float(sz["start"][0]), float(sz["start"][1]), false])
	orte.append(["dachboden", 0.9, 1.6, true])
	for o in orte:
		k._ebene("dach", bool(o[3]))
		for blick in [0.0, PI * 0.5, PI, -PI * 0.5]:
			c({"do": "setzen", "s": o[1], "q": o[2]})
			k.figur.a.heading = k.par.yaw_achse() + blick
			k.regie.hinter_figur()
			await _warte(0.9)
			var cp: Vector3 = m.view_cam.global_position
			var kopf_p: Vector3 = k.figur.pos() + Vector3(0, 1.45, 0)
			var unter_decke: bool = cp.y < k.decke_bei(cp, k.figur.pos().y) - 0.1
			var ueber_boden: bool = cp.y > float(m.ground_y(cp.x, cp.z)) + 0.25
			var frei: bool = k.regie._blocker(cp, kopf_p, 16) < 0.0 and m.line_blocker(cp, kopf_p).is_empty()
			pruef(unter_decke and ueber_boden and frei, "Kamera %s Blick %.1f: Decke %s, Boden %s, Sicht %s" % [o[0], blick, unter_decke, ueber_boden, frei])
	k._ebene("dach", false)
	_ende()


func _ende() -> void:
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("K1-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("K1-Test: " + str(e))
		quit(1)
