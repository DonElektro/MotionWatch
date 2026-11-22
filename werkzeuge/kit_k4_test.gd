extends SceneTree
## Kapitel 4 «Nebel im Couloir» (Grossvater Phase 2, 22.11.2026) einmal ganz durchspielen, mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_k4_test.gd" -- --no-update --no-tour
## Wie ein Spieler: Wärmebild mit der Aktion, gehen (Eingabe «ziel»), auf Kurs mit dem Stick RELATIV ZUR KAMERA nur nach dem
## Kompass (kein Leuchtpunkt), am Seil: Haken einhängen, dann klettern; am Stahlseil: ohne Umhängen geht es nicht weiter,
## mit schon; Steinschlag warnen (QTE), Maggie im Rucksack, ins Biwak zum Buch - bis «Ende von Kapitel 4».
## Dazu: die Kamera am Start jeder Szene, auf den Stufen, am Stahlseil und im Biwak (unter dem Dach), jede Filmeinstellung.
## Ende: «K4-Test OK» oder «SCRIPT ERROR: K4-Test: …».

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
	c({"do": "start", "kapitel": 4, "rolle": "enkelin", "name": "Test", "touch": false, "kette": false})
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) in ["film", "spiel"], 60.0)
	pruef(ok, "Start Kapitel 4")
	if not ok:
		_ende()
		return
	k = m.kit
	pruef(k.kapitel == 4 and str(k.daten.TITEL) == "Nebel im Couloir" and k.k3 != null and k.k3.name == "kit_k4", "Kapitel 4: Daten, Modul kit_k4 geladen")
	# 1 fog, the thermal picture
	await filme_weg()
	pruef(szene() == "s01_nebel", "Szene 1: Nebel")
	await _warte(0.5)
	pruef(k.k3.nebel_an and float(m.env.fog_density) > 0.05, "dichter Nebel im Couloir (%.3f)" % float(m.env.fog_density))
	await aktion()
	ok = await _bis(func(): return k.k3.waerme_an, 2.0)
	pruef(ok and k.erledigt.has("waerme"), "Aktion: Wärmebild an")
	var lia = k.personen.get("lia", null)
	var glut := false
	if lia != null:
		for mi in lia.find_children("*", "MeshInstance3D", true, false):
			glut = glut or (mi as MeshInstance3D).material_overlay != null
	pruef(lia != null and glut, "Wärmebild: Lia leuchtet durch den Nebel")
	ok = await _bis(func(): return szene() == "s02_waerme", 6.0)
	pruef(ok, "Szene 2: Lia und Maggie suchen")
	ok = await geh([[8.0, 0.2], [14.6, 0.4]], 0.7)
	pruef(ok, "zu Lia und Maggie gegangen")
	await filme_weg()
	pruef(not k.k3.waerme_an, "Wärmebild wieder aus")
	ok = await _bis(func(): return szene() == "s03_peilung", 6.0)
	pruef(ok, "Szene 3: Peilung")
	# 3 the bearing: the stick relative to the camera, after the compass only
	await _bis(func(): return not k.k3.peilung.is_empty(), 3.0)
	await _warte(0.3)
	pruef(k.k3.kein_marker() and (k._marker == null or not k._marker.visible), "Peilung: kein Leuchtpunkt, nur der Kompass")
	var t := 0.0
	while t < 120.0 and szene() == "s03_peilung":
		var zw = k.k3.ziel()
		if zw is Vector3:
			var st2: Array = stick_zu(zw)
			c({"do": "eingabe", "mv": [st2[0], st2[1]], "run": true, "s": 0.2})
		await _warte(0.1)
		t += 0.1
		if k.phase == "film":
			break
	pruef(szene() == "s04_seil" or k.par.sq_von(k.figur.pos()).distance_to(Vector2(21.5, 0.4)) < 1.9, "auf Kurs zum Fuss der Felsstufen (%.0f s)" % t)
	ok = await _bis(func(): return szene() == "s04_seil", 6.0)
	pruef(ok, "Szene 4: Seilschaft")
	await filme_weg()
	pruef(bool(k.k3.seil["an"]), "Seil an, Lia sichert")
	# 4 the rope: clip in, then climb - three times
	var y0: float = k.figur.pos().y
	for i in range(3):
		var hs := 23.25 + 4.0 * i
		ok = await geh([[hs - 0.5, 0.0], [hs, 0.0]], 0.3)
		var ak: Dictionary = k.par.aktion_bei(k.figur.a.global_position)
		pruef(str(ak.get("id", "")) == "haken%d" % (i + 1), "Stufe %d: zuerst kommt der Haken (%s)" % [i + 1, str(ak.get("id", ""))])
		await aktion()
		pruef((k.k3.seil["haken"] as Array).size() == i + 1, "Haken %d eingehängt" % (i + 1))
		await aktion()
		ok = await _bis(func(): return zustand() == "klettern", 1.5)
		await _bis(func(): return zustand() == "boden", 4.0)
		pruef(ok, "Stufe %d hochgeklettert" % (i + 1))
	pruef(k.figur.pos().y - y0 > 6.0, "oben auf den Felsstufen (%.1f m höher)" % (k.figur.pos().y - y0))
	ok = await geh([[33.4, 0.0]], 0.6)
	ok = await _bis(func(): return szene() == "s05_querung", 6.0)
	pruef(ok, "Szene 5: Querung")
	# 5 the traverse: without clipping it does not go on
	ok = await geh([[33.6, -2.6], [34.3, -3.6]], 0.35)
	pruef(ok, "am Anfang des Stahlseils")
	var w_weit: Vector3 = k.par.welt(37.0, -3.6)
	for i in range(10):
		c({"do": "eingabe", "ziel": [w_weit.x, w_weit.z], "s": 0.3})
		await _warte(0.25)
	var sq_fest: Vector2 = k.par.sq_von(k.figur.pos())
	pruef(sq_fest.x < 34.8 + 0.35 + 0.15, "ohne Umhängen kein Weiterkommen (s %.2f)" % sq_fest.x)
	for an in [[34.6, -3.6], [37.3, -3.6], [40.0, -3.6]]:
		await geh([[an[0] - 0.1, an[1]]], 0.3)
		await aktion()
	pruef(k.k3.anker.size() == 3, "an allen drei Ankern umgehängt")
	ok = await geh([[41.0, -3.4], [41.6, -2.0]], 0.4)
	pruef(ok and not k.k3.gestuerzt and int(k.figur.nass) == 0, "über den Spalt ohne Sturz")
	# 6 the rock fall: warn Lia
	ok = await _bis(func(): return szene() == "s06_steinschlag" and k.phase == "film", 8.0)
	pruef(ok, "Szene 6: Steinschlag")
	ok = await _bis(func(): return not k.qte.is_empty(), 4.0)
	c({"do": "eingabe", "sprung": true, "s": 0.2})
	ok = await _bis(func(): return k.merker.has("lia_gewarnt"), 3.0)
	pruef(ok, "QTE: Lia gewarnt")
	await filme_weg()
	ok = await _bis(func(): return k.abzeichen.has("seilschaft"), 4.0)
	pruef(ok, "Abzeichen «Seilschaft»")
	# 7 Maggie in the backpack
	ok = await _bis(func(): return szene() == "s07_rucksack", 8.0)
	await filme_weg()
	pruef(k.k3.rucksack and k.hund.welt().y > k.figur.pos().y + 0.7, "Maggie sitzt im Rucksack")
	ok = await geh([[46.0, 0.6], [50.0, 1.0]], 0.8)
	ok = await _bis(func(): return szene() == "s08_biwak", 8.0)
	pruef(ok, "Szene 8: das Biwak")
	await filme_weg()
	pruef(not k.k3.rucksack, "Maggie läuft wieder selbst")
	# 8 into the bivouac, the book
	ok = await geh([[51.2, 1.8], [52.6, 1.8], [54.0, 2.4], [54.5, 2.6]], 0.4)
	pruef(ok, "durch die Tür ins Biwak")
	await aktion()
	ok = await _bis(func(): return k.funde.has("logbuch"), 3.0)
	pruef(ok, "das Biwakbuch gefunden")
	for i in range(8):
		await filme_weg()
		if k.phase == "ende":
			break
	ok = await _bis(func(): return k.phase == "ende", 30.0)
	pruef(ok and k.hud._ende != null, "Ende von Kapitel 4")
	var sm: ShaderMaterial = m.sky_mat
	var oben: Color = sm.get_shader_parameter("top_color")
	pruef(k.k3.nacht and float(sm.get_shader_parameter("night")) > 0.9 and oben.get_luminance() < 0.08 and float(sm.get_shader_parameter("star_vis")) >= 1.0,
			"die Nacht am Biwak: dunkler Himmel (%.3f), Sterne %s" % [oben.get_luminance(), str(sm.get_shader_parameter("star_vis"))])
	pruef(k.k3._fenster_mat.emission_energy_multiplier > 1.0 and (k.k3._biwak_lichter[0] as OmniLight3D).light_energy > 1.0, "das Biwakfenster leuchtet")
	await _film_shots()
	await _kameras()
	await _rollen()
	_ende()


func _rollen() -> void:
	"""the book card and the flashback name the year and the relation of the role: Tochter / Sohn 2000 and «Vater»,
	Enkelin / Enkel 1974 and «Grossvater» (the text, the speaker's name and the pre-spoken voice line)"""
	var karte: Dictionary = {}
	if FileAccess.file_exists("res://klang/stimmen/stimmen.json"):
		karte = JSON.parse_string(FileAccess.get_file_as_string("res://klang/stimmen/stimmen.json")).get("zeilen", {})
	for r in [["tochter", "2000", "1974", "Vater"], ["sohn", "2000", "1974", "Vater"], ["enkelin", "1974", "2000", "Grossvater"]]:
		k.rolle = str(r[0])
		var jahr := str(r[1])
		var falsch := str(r[2])
		c({"do": "eintrag", "e": {"k": "logbuch_zeigen"}})
		var texte: Array = []
		if k.k3._buch != null:
			for l in k.k3._buch.find_children("*", "Label", true, false):
				texte.append((l as Label).text)
		var buch := " | ".join(texte)
		pruef(buch.contains("Biwakbuch · " + jahr) and not buch.contains(falsch), "Rolle %s: Biwakbuch-Karte nennt %s (%s)" % [r[0], jahr, buch.substr(0, 40)])
		c({"do": "eintrag", "e": {"k": "logbuch_weg"}})
		pruef(k.tx(str(k.daten.FUNDE["logbuch"][0])) == "Biwakbuch " + jahr, "Rolle %s: der Fund heisst «Biwakbuch %s»" % [r[0], jahr])
		# the flashback: its title, the narrator's year, the grandfather / father as the speaker, the voice of the line
		var titel := ""
		var sturm := ""
		var gv := ""
		for sz in k.daten.SZENEN:
			if str(sz["id"]) == "s09_rueckblende":
				titel = k.tx(str(sz["titel"]))
				for e in sz["schritte"][0]["film"]:
					if str(e.get("k", "")) == "sag" and str(e["text"]).contains("Sturm kam"):
						sturm = k.tx(str(e["text"]))
		c({"do": "szene", "value": "s09_rueckblende"})
		var gesehen := {}
		for i in range(160):
			await _warte(0.1)
			var t: String = k.hud._sub.text
			if t.contains("Sturm kam"):
				gesehen["sturm"] = t
			if t.contains("Ich steige ab"):
				gv = k.hud._sub_wer.text
				break
		pruef(titel == jahr and sturm.begins_with(jahr + ".") and str(gesehen.get("sturm", "")) == sturm, "Rolle %s: Rückblende «%s» – %s" % [r[0], titel, str(gesehen.get("sturm", "(kein Untertitel)"))])
		pruef(gv == str(r[3]), "Rolle %s: in der Rückblende spricht «%s»" % [r[0], gv])
		pruef(karte.has(sturm) and karte.has(k.tx("Das alte Biwak. Seit {jahr} hat sich hier wenig verändert.")), "Rolle %s: die Stimme für das Jahr %s ist da" % [r[0], jahr])
		c({"do": "skip"})
		await _bis(func(): return k.phase != "film", 4.0)


func _film_shots() -> void:
	for sz in k.daten.SZENEN:
		for st in sz["schritte"]:
			for e in st.get("film", []):
				if str(e.get("k", "")) != "shot":
					continue
				var r: Dictionary = k.regie.pruef_shot(e)
				if r.get("folge", false):
					continue
				var at: Vector3 = k.regie._p(e)
				var lk: Vector3 = k.regie._blick(e)
				var neig: float = rad_to_deg(asin(clampf((lk - at).normalized().y, -1.0, 1.0)))
				pruef(absf(neig) < 22.0 or bool(e.get("himmel", false)), "Film-Einstellung %s: Neigung %.0f° (keine steile Untersicht / Aufsicht)" % [sz["id"], neig])
				pruef(bool(r["ok"]), "Film-Einstellung %s %s: Anteil %.2f, im Bild %s, frei %s, Abstand %.1f m" % [sz["id"], str(e.get("art", "")), float(r["anteil"]), str(r["im_bild"]), str(r["frei"]), float(r["abstand"])])


func _kameras() -> void:
	"""the follow camera: scene starts, on the rock steps, on the strip at the cable, in the bivouac (under its roof)"""
	k.phase = "spiel"
	var orte := []
	for sz in k.daten.SZENEN:
		if (sz["start"] as Array).size() >= 2:
			orte.append([str(sz["id"]), float(sz["start"][0]), float(sz["start"][1])])
	orte.append(["stufe2", 28.3, 0.0])
	orte.append(["stahlseil", 37.3, -3.6])
	orte.append(["biwak_innen", 54.0, 2.4])
	orte.append(["biwak_regal", 54.9, 2.6])
	orte.append(["biwak_tuer", 52.9, 1.9])
	orte.append(["biwak_bank", 54.2, 3.6])
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
				var unter_decke: bool = cp.y < k.decke_bei(cp, k.figur.pos().y) - 0.1
				var im_bild: bool = cam.is_position_in_frustum(kopf_p) and cam.is_position_in_frustum(bauch)
				var bl: float = k.regie._blocker(cp, kopf_p, 24)
				var l1: Dictionary = m.line_blocker(cp, kopf_p)
				var l2: Dictionary = m.line_blocker(kopf_p, cp)
				var frei: bool = bl < 0.0 and l1.is_empty() and l2.is_empty()
				var gut: bool = ueber_boden and unter_decke and im_bild and frei
				if str(o[0]).begins_with("biwak_"):          # inside: a fixed corner camera, not the follow camera from above
					var vorn: Vector3 = -cam.global_transform.basis.z
					var regal: Vector3 = k.par.welt(55.3, 2.6, 0.75)
					var innen_ok: bool = k.regie.art == "shot" and vorn.y > -0.6 and cam.is_position_in_frustum(regal) and cp.y - k.figur.pos().y < 2.1
					if not innen_ok or i == 0:
						pruef(innen_ok, "Biwak-Kamera %s Blick %d/8: Eckkamera %s, Neigung %.2f, Regal im Bild %s" % [o[0], i, k.regie.art, vorn.y, cam.is_position_in_frustum(regal)])
				if not gut or i % 4 == 0:
					pruef(gut, "Kamera %s Blick %d/8%s: Boden %s, Decke %s, Figur im Bild %s, Sicht frei %s %s" % [o[0], i, " gedreht" if zieh != 0.0 else "", ueber_boden, unter_decke, im_bild, frei,
							"" if frei else "(Boden/Fels %.2f, Hindernis %s / %s)" % [bl, str(l1.get("id", "")), str(l2.get("id", ""))]])


func _ende() -> void:
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("K4-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("K4-Test: " + str(e))
		quit(1)
