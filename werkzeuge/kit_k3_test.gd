extends SceneTree
## Kapitel 3 «Der Seeblock» (Grossvater Phase 2, 22.11.2026) einmal ganz durchspielen, mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_k3_test.gd" -- --no-update --no-tour
## Wie ein Spieler: gehen (Eingabe «ziel»), über die Steine mit dem Stick vorwärts + Springen, an der Kante klettern, die Duftspur
## zu Fuss, das Floss mit dem Stick RELATIV ZUR KAMERA (vorwärts + lenken) und bei jeder Böe die Aktion im richtigen Moment,
## die Zeichen lesen, das Schloss (erst falsch, dann richtig) - bis «Ende von Kapitel 3». Filme werden übersprungen.
## Dazu: die Kamera am Start jeder Szene, auf den Steinen, auf dem Block und dem Steg (8 Richtungen, frei, Figur im Bild),
## jede Filmeinstellung (Anteil, im Bild, frei - auch von Wänden), die verlorene Duftspur (Maggie schnüffelt neu) und das Floss
## vom Kurs ab (zurück zur letzten Boje).
## Ende: «K3-Test OK» oder «SCRIPT ERROR: K3-Test: …».

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
	for i in range(6):
		await _warte(0.4)
		if k.phase == "film":
			c({"do": "skip"})
			await _bis(func(): return k.phase != "film", 4.0)
		elif k.phase == "spiel":
			return


func geh(punkte: Array, r := 0.45) -> bool:
	for p in punkte:
		var w: Vector3 = k.par.welt(float(p[0]), float(p[1]))
		var t := 0.0
		while t < 70.0:
			var fp: Vector3 = k.figur.pos()
			if Vector2(fp.x, fp.z).distance_to(Vector2(w.x, w.z)) < r:
				break
			if k.phase == "film":
				return true
			c({"do": "eingabe", "ziel": [w.x, w.z], "run": true, "s": 0.3})
			await _warte(0.25)
			t += 0.25
		if t >= 70.0:
			print("     geh: hängt bei ", k.par.sq_von(k.figur.pos()), " auf dem Weg zu ", p)
			return false
	return true


func aktion() -> void:
	c({"do": "eingabe", "mv": [0, 0], "aktion": true, "s": 0.15})
	await _warte(0.5)


func zustand() -> String:
	return str(k.figur.zustand)


func stick_zu(w: Vector3) -> Array:
	"""the stick like a player: forward, turned towards w relative to where the camera looks"""
	var cam: Camera3D = m.view_cam
	var fw := -cam.global_transform.basis.z
	fw.y = 0.0
	fw = fw.normalized()
	var rt := fw.cross(Vector3.UP).normalized()
	var to := Vector3(w.x - k.figur.pos().x, 0, w.z - k.figur.pos().z).normalized()
	return [clampf(to.dot(fw), -1.0, 1.0), clampf(to.dot(rt), -1.0, 1.0)]


func _lauf() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	c({"do": "start", "kapitel": 3, "rolle": "enkelin", "name": "Test", "touch": false, "kette": false})
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) in ["film", "spiel"], 60.0)
	pruef(ok, "Start Kapitel 3")
	if not ok:
		_ende()
		return
	k = m.kit
	pruef(k.kapitel == 3 and str(k.daten.TITEL) == "Der Seeblock" and k.k3 != null, "Kapitel 3: Daten «Der Seeblock», Mechanik geladen")
	var wl: float = k.par.see_y()
	# Lia's tent stands (review 22.11.: it lay flat on the ground): its meshes are at least 1 m high
	var zelt: Node3D = k.par.dinge["lia_zelt"]["node"]
	var bb := AABB()
	var erst := true
	for mi in zelt.find_children("*", "MeshInstance3D", true, false):
		var b2: AABB = (mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb()
		bb = b2 if erst else bb.merge(b2)
		erst = false
	pruef(not erst and bb.size.y > 1.0 and bb.size.x > 1.0 and bb.size.z > 1.0, "Lias Zelt steht (Höhe %.2f m, %.1f × %.1f m)" % [bb.size.y, bb.size.x, bb.size.z])
	# 1 the empty tent
	await filme_weg()
	pruef(szene() == "s01_zelt", "Szene 1: das leere Zelt")
	ok = await geh([[8.6, -284.5], [9.5, -279.0]])
	pruef(ok, "zu den Spuren hinter dem Zelt")
	await filme_weg()
	ok = await _bis(func(): return szene() == "s02_duft", 8.0)
	pruef(ok, "Szene 2: am Ufer des Gumpisees")
	# 2 the scent trail on foot: from cloud to cloud
	await filme_weg()
	ok = await _bis(func(): return not k.k3.duft.is_empty(), 6.0)
	pruef(ok, "Duftspur beginnt")
	var t := 0.0
	while t < 400.0 and not k.erledigt.has("duft"):
		if k.k3.duft.is_empty():
			await _warte(0.2)
			t += 0.2
			continue
		var w: Vector3 = k.k3.duft["pts"][int(k.k3.duft["i"])]
		c({"do": "eingabe", "ziel": [w.x, w.z], "run": true, "s": 0.3})
		await _warte(0.25)
		t += 0.25
	pruef(k.erledigt.has("duft"), "Duftspur: alle Wolken erreicht (%.0f s)" % t)
	ok = await _bis(func(): return k.abzeichen.has("spuernase"), 3.0)
	pruef(ok, "Abzeichen «Spürnase» (Spur nie verloren)")
	ok = await _bis(func(): return szene() == "s03_blockfeld", 6.0)
	pruef(ok, "Szene 3: Blockfeld")
	# 3 over the brook: stick forward + jump, stone by stone
	ok = await geh([[27.4, -7.0], [26.0, -7.0]], 0.35)
	pruef(ok, "ans Bachufer")
	c({"do": "setzen", "s": 26.0, "q": -7.0, "blick": k.par.yaw_achse() + PI})
	await _warte(0.8)
	for i in range(7):
		if k.par.sq_von(k.figur.pos()).x < 14.6:
			break
		c({"do": "eingabe", "mv": [1, 0], "sprung": true, "s": 0.15})
		await _bis(func(): return zustand() == "luft", 1.0)
		await _bis(func(): return zustand() == "boden", 3.0)
		await _warte(0.3)
	var sq: Vector2 = k.par.sq_von(k.figur.pos())
	pruef(sq.x < 14.8 and int(k.figur.nass) == 0, "Steine: trocken über den Bach (s %.1f, nass %d)" % [sq.x, int(k.figur.nass)])
	# the boulders: up at the edge, then one step higher
	ok = await geh([[12.6, -5.6], [11.6, -5.0]], 0.3)
	pruef(ok, "an der Kante des ersten Blocks")
	var y0: float = k.figur.pos().y
	await aktion()
	ok = await _bis(func(): return zustand() == "klettern", 1.5)
	pruef(ok, "Block: klettert")
	await _bis(func(): return zustand() == "boden", 4.0)
	pruef(k.figur.pos().y - y0 > 1.1, "Block: oben (%.2f m höher)" % (k.figur.pos().y - y0))
	ok = await geh([[9.6, -4.8], [7.6, -4.6]], 0.4)
	pruef(ok, "auf den zweiten Block gestiegen")
	ok = await _bis(func(): return szene() == "s04_floss", 4.0)
	pruef(ok, "Szene 4: oben auf den Felsblöcken, Treibholz in Sicht")
	# 4 down to the beach, three logs, the raft
	ok = await geh([[6.3, -4.4], [5.1, -4.0], [3.6, -3.0]], 0.45)
	pruef(ok and k.par.VL(k.figur.pos()).y - wl < 1.2, "über zwei Felsstufen hinunter an den Strand (ohne Sprung)")
	for st in [[6.5, -0.6], [3.0, 2.0], [9.0, 3.4]]:
		ok = await geh([st], 0.6)
		await aktion()
	ok = await _bis(func(): return k.erledigt.has("staemme"), 3.0)
	pruef(ok and k.funde.has("stamm1") and k.funde.has("stamm2") and k.funde.has("stamm3"), "drei Stämme Treibholz gesammelt")
	ok = await geh([[5.0, 4.2]], 0.6)
	await aktion()
	ok = await _bis(func(): return k.erledigt.has("floss_bauen"), 3.0)
	pruef(ok, "Floss gebaut")
	await filme_weg()
	ok = await _bis(func(): return szene() == "s05_see" and not k.k3.floss.is_empty() and bool(k.k3.floss["an"]), 8.0)
	pruef(ok and zustand() == "steuern", "Szene 5: auf dem Floss")
	# 5 the raft like a player: stick relative to the camera, the action when the gust bar is nearly full
	t = 0.0
	var max_ab := 0.0
	var gedrueckt := {}
	while t < 400.0 and not k.erledigt.has("floss"):
		var zw = k.k3.ziel()
		if zw is Vector3:
			var st2: Array = stick_zu(zw)
			var b: Dictionary = k.k3.floss["boe"]
			var druecken := str(b["phase"]) == "warn" and float(b["t"]) > 0.95 and not gedrueckt.has(int(k.k3.floss["boeen"]))
			if druecken:
				gedrueckt[int(k.k3.floss["boeen"])] = true
			c({"do": "eingabe", "mv": [st2[0], st2[1]], "aktion": druecken, "s": 0.2})
			max_ab = maxf(max_ab, k.k3._seg_abstand(k.k3.floss["p"]))
		await _warte(0.1)
		t += 0.1
		if int(t * 10) % 50 == 0:
			print("     floss t %.0f " % t, k.k3.info().get("floss", {}), " kamera ", k.par.sq_von(m.view_cam.global_position), " art ", k.regie.art)
	var fi: Dictionary = k.k3.info().get("floss", {})
	pruef(k.erledigt.has("floss"), "Floss: am Seeblock angelegt (%.0f s)" % t)
	pruef(int(fi.get("zurueck", 1)) == 0 and max_ab < 7.0, "Floss: nie vom Kurs (grösster Abstand %.1f m)" % max_ab)
	pruef(int(fi.get("boeen", 0)) >= 2 and int(fi.get("gehalten", 0)) == int(fi.get("boeen", 0)), "Floss: Böen %d, gehalten %d" % [int(fi.get("boeen", 0)), int(fi.get("gehalten", 0))])
	ok = await _bis(func(): return k.abzeichen.has("kapitaen"), 3.0)
	pruef(ok, "Abzeichen «Kapitän»")
	await _warte(0.4)
	pruef(zustand() in ["boden", "film"] and absf(k.figur.pos().y - k.par.welt_abs(42.0, 34.7, wl + 0.55).y) < 0.25, "auf dem Steg des Seeblocks (y %.2f)" % (k.figur.pos().y - k.par.welt_abs(42.0, 34.7, wl).y))
	# 6 the crack
	await filme_weg()
	ok = await _bis(func(): return szene() == "s06_seeblock", 6.0)
	pruef(ok, "Szene 6: Seeblock")
	await filme_weg()
	ok = await geh([[42.0, 34.5]], 0.35)
	await aktion()
	ok = await _bis(func(): return k.erledigt.has("zeichen"), 3.0)
	pruef(ok, "Riss mit dem Zeichen verglichen")
	await filme_weg()
	ok = await _bis(func(): return szene() == "s07_kiste", 6.0)
	pruef(ok, "Szene 7: die Kiste")
	# 7 the marks, the lock
	for mk in [[39.4, 34.6], [41.0, 34.6], [44.6, 34.6]]:
		await geh([mk], 0.3)
		await aktion()
	ok = await _bis(func(): return k.erledigt.has("marken"), 3.0)
	pruef(ok and k.k3.gelesen.size() == 3, "drei Zeichen am Fels gelesen")
	pruef(zustand() == "boden" and k.par.sq_von(k.figur.pos()).y < 35.4 and int(k.figur.nass) == 0, "nie in den See gefallen")
	await geh([[42.8, 34.7]], 0.3)
	await aktion()
	ok = await _bis(func(): return k.k3._schloss != null, 2.0)
	pruef(ok and zustand() == "steuern", "Schloss offen: drei Rädchen")
	c({"do": "k3", "was": "schloss", "zeichen": ["T", "+", "G"]})
	await _warte(0.3)
	pruef(not k.erledigt.has("schloss") and k.k3.schloss_falsch == 1 and k.k3._schloss != null, "falsche Reihenfolge: bleibt zu")
	c({"do": "k3", "was": "schloss", "zeichen": ["G", "+", "T"]})
	ok = await _bis(func(): return k.erledigt.has("schloss"), 2.0)
	pruef(ok and k.k3._schloss == null, "richtige Zeichen: die Kiste geht auf")
	# 8–11
	for i in range(8):
		await filme_weg()
		if k.phase == "ende":
			break
	ok = await _bis(func(): return k.phase == "ende", 30.0)
	pruef(ok and k.hud._ende != null, "Ende von Kapitel 3")
	pruef(k.funde.has("kartenstueck") and k.funde.has("notiz"), "Funde: zweites Kartenstück, Notiz «Treffpunkt Biwak»")
	pruef(k.k3._feuer_an, "Feuer am Ufer brennt")
	await _film_shots()
	await _kameras(wl)
	await _duft_verlieren()
	await _floss_abdriften()
	_ende()


func _film_shots() -> void:
	"""every shot of the chapter: the subject big enough, in the picture, nothing (rock, wall) in front"""
	for sz in k.daten.SZENEN:
		for st in sz["schritte"]:
			for e in st.get("film", []):
				if str(e.get("k", "")) != "shot":
					continue
				var r: Dictionary = k.regie.pruef_shot(e)
				if r.get("folge", false):
					continue
				pruef(bool(r["ok"]), "Film-Einstellung %s %s: Anteil %.2f, im Bild %s, frei %s, Abstand %.1f m" % [sz["id"], str(e.get("art", "")), float(r["anteil"]), str(r["im_bild"]), str(r["frei"]), float(r["abstand"])])


func _kameras(wl: float) -> void:
	"""the follow camera at the start of the scenes, on the stones, on the blocks and on the landing: above the ground,
	the figure (head, belly) in the picture, nothing in between (ground, rock, the block, walls)"""
	k.phase = "spiel"
	var orte := []
	for sz in k.daten.SZENEN:
		if (sz["start"] as Array).size() >= 2:
			orte.append([str(sz["id"]), float(sz["start"][0]), float(sz["start"][1])])
	orte.append(["stein3", 20.0, -7.2])
	orte.append(["block_b", 7.6, -4.6])
	orte.append(["steg_links", 39.4, 34.6])
	orte.append(["steg_rechts", 44.6, 34.6])
	for o in orte:
		for i in range(8):
			var blick := TAU * i / 8.0
			for zieh in [0.0, 0.35]:
				c({"do": "setzen", "s": o[1], "q": o[2]})
				k.figur.a.heading = k.par.yaw_achse() + blick
				k.regie.hinter_figur()
				if zieh != 0.0:
					k.regie.yaw = float(k.figur.a.heading) + zieh
					k.regie.drag_t = k.uhr + 100.0
				await _warte(0.6)
				var cam: Camera3D = m.view_cam
				var cp: Vector3 = cam.global_position
				var kopf_p: Vector3 = k.figur.pos() + Vector3(0, 1.45, 0)
				var bauch: Vector3 = k.figur.pos() + Vector3(0, 0.9, 0)
				var ueber_boden: bool = cp.y > float(m.ground_y(cp.x, cp.z)) + 0.25
				var im_bild: bool = cam.is_position_in_frustum(kopf_p) and cam.is_position_in_frustum(bauch)
				var bl: float = k.regie._blocker(cp, kopf_p, 24)
				var l1: Dictionary = m.line_blocker(cp, kopf_p)
				var l2: Dictionary = m.line_blocker(kopf_p, cp)
				var im_block := false
				for kg in k.k3.kugeln_welt():
					if cp.distance_to(kg[0]) < float(kg[1]):
						im_block = true
				var frei: bool = bl < 0.0 and l1.is_empty() and l2.is_empty() and not im_block
				var gut: bool = ueber_boden and im_bild and frei
				if not gut or i % 4 == 0:
					pruef(gut, "Kamera %s Blick %d/8%s: Boden %s, Figur im Bild %s, Sicht frei %s %s" % [o[0], i, " gedreht" if zieh != 0.0 else "", ueber_boden, im_bild, frei,
							"" if frei else "(Boden/Fels %.2f, Hindernis %s / %s, im Block %s)" % [bl, str(l1.get("id", "")), str(l2.get("id", "")), im_block]])


func _duft_verlieren() -> void:
	"""wait until a cloud is gone: the trail is lost (marker off), the action lets Maggie sniff again"""
	k.phase = "spiel"
	k.erledigt.erase("duft")
	k.k3.duft_start("spur")
	k.k3.duft["t"] = float(k.k3.duft["fade"]) - 0.3
	var ok: bool = await _bis(func(): return bool(k.k3.duft.get("weg", false)), 3.0)
	pruef(ok and k.k3.ziel() == null and k.merker.has("duft_verloren"), "Duftspur verblasst: verloren, kein Marker")
	await aktion()
	pruef(not bool(k.k3.duft.get("weg", true)) and float(k.k3.duft.get("t", 9.0)) < 1.0 and k.k3.ziel() != null, "Aktion: Maggie schnüffelt die Spur neu")
	k.k3.duft = {}


func _floss_abdriften() -> void:
	"""off the course on the raft: back at the last buoy"""
	k.phase = "spiel"
	k.k3.floss_start()
	var K: Array = k.k3.floss["kurs"]
	var seg: Vector2 = ((K[2] as Vector2) - (K[1] as Vector2)).normalized()
	k.k3.floss["letzte"] = K[1]
	k.k3.floss["i"] = 2
	k.k3.floss["p"] = (K[1] as Vector2).lerp(K[2], 0.5) + Vector2(-seg.y, seg.x) * 6.8
	k.k3.floss["v"] = Vector2(-seg.y, seg.x) * 1.5
	var z0: int = int(k.k3.floss["zurueck"])
	var ok: bool = await _bis(func(): return int(k.k3.floss["zurueck"]) > z0, 12.0)
	pruef(ok and (k.k3.floss["p"] as Vector2).distance_to(k.k3.floss["kurs"][1]) < 0.5, "Floss vom Kurs: zurück zur letzten Boje")
	k.k3.floss["an"] = false


func _ende() -> void:
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("K3-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("K3-Test: " + str(e))
		quit(1)
