extends SceneTree
## «Die Karte des Grossvaters» mit den Bewegungen von «Frei erkunden» (22.11.2026, figur_haltung.gd), echte Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_haltung_test.gd" -- --no-update --no-tour
## * C / X / Z / V wie beim Erkunden: stehen → geduckt → kriechen → stehen, sitzen, liegen (losgehen = kriechen), drei Ansichten
## * die Kamera bei tiefer Haltung: über dem Boden, der Kopf im Bild
## * Ziele «geh zu …» in jedem Kapitel geduckt oder kriechend erreichbar (die Stelle zählt), das Biwakbuch geduckt holen
## * kein Festhängen: Springen aus der Hocke = zuerst aufstehen; ein Film setzt eine liegende Figur wieder auf die Füsse
## * auf dem Floss keine Haltung; im See von Kapitel 3 schwimmen, aber nie hinüber zum Seeblock (das Rätsel bleibt)
## Ende: «Haltung-Test OK» oder «SCRIPT ERROR: Haltung-Test: …».

const Haltung = preload("res://scripts/figur_haltung.gd")

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


func pruef(ok: bool, was: String) -> void:
	print(("ok   " if ok else "FEHL ") + was)
	if not ok:
		var fi: Dictionary = k.figur.info() if k != null and k.figur != null and k.figur.ok() else {}
		errs.append(was + "  " + JSON.stringify({"s": fi.get("s"), "q": fi.get("q"), "zustand": fi.get("zustand"), "haltung": k.halt.haltung if k != null else ""}))


func _bis(cond: Callable, secs: float) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call():
			return true
		await _warte(0.1)
		t += 0.1
	return cond.call()


func filme_weg() -> void:
	for i in range(8):
		await _warte(0.4)
		if k.phase == "film":
			c({"do": "skip"})
			await _bis(func(): return k.phase != "film", 4.0)
		elif k.phase == "spiel":
			return


func _start(n: int) -> bool:
	c({"do": "start", "kapitel": n, "rolle": "enkel", "name": "Test", "touch": false, "kette": false})
	var ok: bool = await _bis(func(): return m.kit.running and m.kit.kapitel == n and m.kit.phase in ["film", "spiel"], 60.0)
	k = m.kit
	pruef(ok, "Start Kapitel %d" % n)
	return ok


func _szene(id: String) -> void:
	c({"do": "szene", "value": id})
	await _warte(0.3)
	await filme_weg()


func _bis_schritt(bis: String) -> bool:
	"""the steps of this scene until the one with this goal (the others counted as reached)"""
	for i in range(14):
		await filme_weg()
		if str(k.schritt.get("bis", "")) == bis:
			return true
		if k.phase == "spiel" and k.schritt.has("ziel"):
			c({"do": "abschnitt"})
			await _warte(1.2)
		else:
			await _warte(0.5)
	return str(k.schritt.get("bis", "")) == bis


func _haltung(h: String) -> void:
	await _bis(func(): return k.haltung_frei(), 3.0)       # (after placing: a short fall first)
	c({"do": "haltung", "setzen": h})
	await _warte(0.2)
	if k.halt.haltung != h:
		print("     Haltung %s nicht gesetzt: frei %s, zustand %s, phase %s, maggie %s" % [h, k.haltung_frei(), k.figur.zustand, k.phase, k.steuer_maggie])


func _geh_zu(w: Vector3, secs: float, r := 0.5) -> bool:
	var t := 0.0
	while t < secs:
		var fp: Vector3 = k.figur.pos()
		if Vector2(fp.x, fp.z).distance_to(Vector2(w.x, w.z)) < r or k.phase != "spiel":
			return true
		c({"do": "eingabe", "ziel": [w.x, w.z], "s": 0.3})
		await _warte(0.25)
		t += 0.25
	return false


func _stelle(bis: String, h: String, weit := 8.0) -> void:
	"""a goal «reach X» of the chapter, crouched or crawling: the step must count (the next one starts)"""
	var ok := await _bis_schritt(bis)
	pruef(ok, "Kapitel %d: Schritt «%s» erreicht" % [k.kapitel, bis])
	if not ok:
		return
	var ziel = k._bis_ort(bis)
	var fp: Vector3 = k.figur.pos()
	var to := Vector3(fp.x - ziel.x, 0, fp.z - ziel.z)
	if to.length() > weit:
		k.figur.setzen(ziel + to.normalized() * weit)
		k.figur.geh_zu("boden")
		await _warte(0.4)
	await _haltung(h)
	var si: int = k.szene_i
	var schi: int = k.schritt_i
	var hoehe_ok: bool = k.halt.haltung == h and int(k.figur.a.ctl_posture) == int(Haltung.POSTUR[h])
	var weg0: float = Vector2(k.figur.pos().x, k.figur.pos().z).distance_to(Vector2(ziel.x, ziel.z))
	var t0: float = k.uhr
	ok = await _geh_zu(ziel, 70.0)
	var dt_lauf: float = k.uhr - t0
	await _bis(func(): return k.szene_i != si or k.schritt_i != schi, 3.0)
	var weiter: bool = k.szene_i != si or k.schritt_i != schi
	var v: float = weg0 / maxf(dt_lauf, 0.1)
	pruef(hoehe_ok and ok and weiter and v < 1.05, "Kapitel %d: «%s» %s erreicht (%.1f m in %.0f s = %.2f m/s, Schritt zählt %s)" % [k.kapitel,
			str(k.daten.SZENEN[si]["schritte"][schi].get("ziel", bis)) if si < k.daten.SZENEN.size() else bis, h, weg0, dt_lauf, v, weiter])
	await _haltung("stehen")


func _kamera_tief() -> void:
	"""the follow camera for every posture: above the ground, the head in the picture, lower when lower"""
	var hoehen := {}
	for h in ["stehen", "geduckt", "kriechen", "sitzen", "liegen"]:
		await _haltung(h)
		await _warte(1.2)
		var cam: Camera3D = m.view_cam
		var cp: Vector3 = cam.global_position
		var kopf: Vector3 = k.figur.pos() + Vector3(0, k.kopf_hoehe(), 0)
		var gut: bool = cp.y > float(m.ground_y(cp.x, cp.z)) + 0.2 and cam.is_position_in_frustum(kopf)
		hoehen[h] = k.kopf_hoehe()
		pruef(gut and k.halt.haltung == h, "Kamera %s: über dem Boden, Kopf im Bild (Kopf %.2f m)" % [h, k.kopf_hoehe()])
	pruef(float(hoehen["kriechen"]) < float(hoehen["geduckt"]) and float(hoehen["geduckt"]) < float(hoehen["stehen"]), "die Kamera schaut tiefer, wenn die Figur tiefer ist")
	await _haltung("stehen")


func _lauf() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)

	# ---- Kapitel 1: the keys, the views, the camera, the hut crouched ------------------------------------------------------------
	if await _start(1):
		await filme_weg()
		c({"do": "haltung", "wunsch": "haltung"})
		await _warte(0.3)
		var h1: String = k.halt.haltung
		c({"do": "haltung", "wunsch": "haltung"})
		await _warte(0.3)
		var h2: String = k.halt.haltung
		var p2 := int(k.figur.a.ctl_posture)
		c({"do": "haltung", "wunsch": "haltung"})
		await _warte(0.3)
		pruef(h1 == "geduckt" and h2 == "kriechen" and p2 == 2 and k.halt.haltung == "stehen", "C: stehen → geduckt → kriechen → stehen (%s, %s)" % [h1, h2])
		c({"do": "haltung", "wunsch": "sitzen"})
		await _warte(0.4)
		var sitzt: bool = k.halt.haltung == "sitzen" and bool(k.figur.a.ctl_sit)
		c({"do": "eingabe", "mv": [1, 0], "s": 0.6})
		await _warte(0.8)
		pruef(sitzt and k.halt.haltung == "stehen" and not bool(k.figur.a.ctl_sit), "X: hinsetzen, losgehen = aufstehen")
		c({"do": "haltung", "wunsch": "liegen"})
		await _warte(0.4)
		var liegt: bool = k.halt.haltung == "liegen" and bool(k.figur.a.frozen)
		var p0: Vector3 = k.figur.pos()
		c({"do": "eingabe", "mv": [1, 0], "s": 1.5})
		await _warte(1.8)
		pruef(liegt and k.halt.haltung == "kriechen" and k.figur.pos().distance_to(p0) > 0.15, "Z: hinlegen, losgehen = kriechen")
		await _haltung("stehen")
		var ans: Array = []
		for i in range(3):
			c({"do": "haltung", "wunsch": "ansicht"})
			await _warte(0.6)
			ans.append(k.ansicht)
			if k.ansicht == "augen":
				var cam: Camera3D = m.view_cam
				pruef(absf(cam.global_position.y - (k.figur.pos().y + 1.62)) < 0.3, "V: aus den Augen (Kamera auf Augenhöhe)")
			elif k.ansicht == "oben":
				pruef(m.view_cam.global_position.y > k.figur.pos().y + 5.0, "V: von oben")
		pruef(ans == ["augen", "oben", "folge"], "V: hinter dir → aus den Augen → von oben → hinter dir (%s)" % str(ans))
		await _kamera_tief()
		await _stelle("ort:-5.2,-2.25,1.6", "geduckt", 9.0)

	# ---- Kapitel 2: crawling along the gorge, a jump from crouching, a film while lying ----------------------------------------
	if await _start(2):
		await _szene("s02_schlucht")
		await _stelle("ort:10.5,0.0,2.5", "kriechen", 6.0)
		await filme_weg()
		await _haltung("geduckt")
		c({"do": "eingabe", "mv": [0, 0], "sprung": true, "s": 0.2})
		await _warte(0.5)
		var erst_auf: bool = k.halt.haltung == "stehen" and str(k.figur.zustand) == "boden"
		c({"do": "eingabe", "mv": [0, 0], "sprung": true, "s": 0.2})
		var sprang: bool = await _bis(func(): return str(k.figur.zustand) == "luft", 1.5)
		await _bis(func(): return str(k.figur.zustand) == "boden", 4.0)
		pruef(erst_auf and sprang, "Springen aus der Hocke: zuerst aufstehen, dann springt die Figur")
		await _haltung("liegen")
		c({"do": "szene", "value": "s04_wasserfall"})
		await _bis(func(): return k.phase == "film", 6.0)
		await filme_weg()
		var p1: Vector3 = k.figur.pos()
		c({"do": "eingabe", "mv": [1, 0], "s": 1.2})
		await _warte(1.5)
		pruef(k.halt.haltung == "stehen" and not bool(k.figur.a.frozen) and k.figur.pos().distance_to(p1) > 0.4,
				"ein Film stellt die liegende Figur wieder auf die Füsse, danach geht sie")

	# ---- Kapitel 3: behind the tent crouched, no posture on the raft, swimming never reaches the Seeblock -------------------
	if await _start(3):
		await filme_weg()
		await _stelle("ort_tal:-9.5,-21.0,2.4", "geduckt", 8.0)
		await _szene("s04_floss")
		await _haltung("stehen")
		var sb: Vector3 = k.par.welt(42.0, 40.0)
		var schwamm := false
		var am_block := false
		var nass0: int = int(k.figur.nass)
		var t := 0.0
		while t < 50.0:
			c({"do": "eingabe", "ziel": [sb.x, sb.z], "s": 0.4})
			await _warte(0.25)
			t += 0.25
			if k.halt.wasser == "schwimmen":
				schwamm = true
			var sq: Vector2 = k.par.sq_von(k.figur.pos())
			if absf(sq.x - 42.0) < 5.0 and absf(sq.y - 40.0) < 5.0:
				am_block = true
			if int(k.figur.nass) > nass0:
				break
		pruef(schwamm, "im See von Kapitel 3 schwimmt die Figur an der Oberfläche")
		pruef(not am_block, "schwimmend nie zum Seeblock (das Floss bleibt nötig; nass %d → %d)" % [nass0, int(k.figur.nass)])
		await _szene("s05_see")
		var fl: bool = await _bis(func(): return not k.k3.floss.is_empty(), 8.0)
		if fl:
			c({"do": "haltung", "wunsch": "haltung"})
			await _warte(0.4)
			pruef(not k.haltung_frei() and k.halt.haltung == "stehen", "auf dem Floss: keine Haltung (stehen)")
		else:
			print("     (Floss nicht aktiv - Schritt übersprungen)")

	# ---- Kapitel 4: in the fog crawling, the book of the bivouac crouched -------------------------------------------------------
	if await _start(4):
		await filme_weg()
		await _stelle("ort:15.0,0.4,2.4", "kriechen", 6.0)
		await _szene("s08_biwak")
		var ok: bool = await _bis_schritt("fund:logbuch")
		await _haltung("geduckt")
		for p in [[51.4, 1.8], [52.9, 1.8], [54.0, 2.4], [54.5, 2.6]]:
			ok = ok and await _geh_zu(k.par.welt(float(p[0]), float(p[1])), 40.0, 0.4)
		var noch_geduckt: bool = k.halt.haltung == "geduckt"
		c({"do": "eingabe", "mv": [0, 0], "aktion": true, "s": 0.15})
		ok = ok and await _bis(func(): return k.funde.has("logbuch"), 3.0)
		pruef(ok and noch_geduckt, "Kapitel 4: geduckt durch die Tür ins Biwak, das Buch genommen")
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("Haltung-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Haltung-Test: " + str(e))
		quit(1)
