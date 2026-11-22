extends SceneTree
## Test des Abenteuer-Kits (Grossvater-Neubau 20.11.2026: kit_abenteuer.gd, kit_figur.gd, kit_parcours.gd, kit_regie.gd,
## kit_maggie.gd, kit_hud.gd, klang.gd Musik-Zustände) mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_figur_test.gd" -- --no-update --no-tour --port 9449
## Prüft: die Daten (Dinge, Aktionen, Checkpoints, Szenen-Schritte), dann im Bergtal: gehen, springen, Steinsprünge ohne
## nasse Füsse, ins Wasser = zurück zum Checkpoint, Felsstufe hochklettern, Maggie hochheben und durch den Spalt zum Riegel
## steuern, Baumstamm (Kindermodus hinüber; ohne Hilfe ausrutschen → hängen → hochziehen), Absatz + Leiter, Seil schwingen,
## Sturz in den Spalt → hängen → zurück zum Checkpoint, Fund, Filmszene überspringen, Pause, Musik-Zustand, Rolle → Texte.
## Dazu die eigene Schlucht (kit_schlucht.gd): Tiefe 15–20 m in der Mitte, Boden = main.ground_y, Ausschnitt / Steine zurück.
## Ende: «Kit-Test OK» oder «SCRIPT ERROR: Kit-Test: …» (Exit-Code 0 / 1).

var errs: Array = []
var m = null
var k = null


func _init() -> void:
	_daten()
	_welt.call_deferred()


func _daten() -> void:
	var D = load("res://scripts/kit_k2_daten.gd")
	var ids := {}
	for d in D.DINGE:
		if ids.has(d["id"]):
			errs.append("Ding doppelt: %s" % d["id"])
		ids[d["id"]] = d
	for a in D.AKTIONEN:
		if a.has("ding") and not ids.has(a["ding"]):
			errs.append("Aktion %s: Ding %s fehlt" % [a["id"], a["ding"]])
		for sid in a.get("kette", []):
			if not ids.has(sid):
				errs.append("Aktion %s: Stein %s fehlt" % [a["id"], sid])
	var arten := ["film", "ziel", "sag", "musik", "checkpoint", "abzeichen", "maggie"]
	for sz in D.SZENEN:
		for st in sz["schritte"]:
			var ok := false
			for k_ in arten:
				ok = ok or (st as Dictionary).has(k_)
			if not ok:
				errs.append("Szene %s: unbekannter Schritt %s" % [sz["id"], str(st)])
			if st.has("checkpoint") and not D.CHECKPOINTS.has(st["checkpoint"]):
				errs.append("Szene %s: Checkpoint %s fehlt" % [sz["id"], st["checkpoint"]])
	if D.SZENEN.size() != 12:
		errs.append("Kapitel 2 hat %d statt 12 Szenen" % D.SZENEN.size())
	for r in D.ROLLEN:
		var b: Dictionary = D.bezug(r)
		var want := "Grossvater" if r in ["enkelin", "enkel"] else "Vater"
		if str(b["bezug"]) != want or str(b["jahr"]) != ("1974" if want == "Grossvater" else "2000"):
			errs.append("Rolle %s: %s" % [r, str(b)])
	print("Daten: %d Dinge, %d Aktionen, %d Szenen" % [D.DINGE.size(), D.AKTIONEN.size(), D.SZENEN.size()])


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func c(d: Dictionary) -> Dictionary:
	d["action"] = "kit"
	return m.control(d)


func info() -> Dictionary:
	return c({"do": "info"}).get("kit", {})


func fig() -> Dictionary:
	return info().get("figur", {})


func zustand() -> String:
	return str(fig().get("zustand", ""))


func _bis(cond: Callable, secs: float) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call():
			return true
		await _warte(0.1)
		t += 0.1
	return cond.call()


func pruef(ok: bool, was: String) -> void:
	print(("ok   " if ok else "FEHL ") + was)
	if not ok:
		errs.append(was + "  " + JSON.stringify(fig()))


func setzen(sv: float, qv: float) -> void:
	c({"do": "setzen", "s": sv, "q": qv})
	await _warte(0.4)


func _welt() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	c({"do": "start", "rolle": "sohn", "name": "Test", "figur_test": true, "touch": true, "kette": false})
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) == "spiel", 60.0)
	pruef(ok, "Start: Spiel läuft")
	if not ok:
		_ende()
		return
	k = m.kit
	pruef(k.tx("{bezug}") == "Vater" and k.tx("{jahr}") == "2000", "Rolle Sohn: Vater / 2000")
	pruef(k.hud.touch and k.hud.stick.visible, "Touch: Stick sichtbar")
	print("Leistung: ", JSON.stringify(k.par.info()), " fps ", Engine.get_frames_per_second())
	var sch = k.par.schlucht
	pruef(sch != null, "Schlucht: gebaut")
	if sch != null:
		var tp: Vector2 = sch.tal(40.0, 0.0)
		var tiefe: float = load("res://scripts/bergtal.gd").H(tp.x, tp.y) - float(sch.boden_sq(40.0, 0.0))
		pruef(tiefe > 14.0 and tiefe < 22.0, "Schlucht: %.1f m tief bei s 40" % tiefe)
		var w: Vector3 = k.par.welt(20.0, 0.0)
		pruef(absf(float(m.ground_y(w.x, w.z)) - w.y) < 0.05, "Schlucht: main.ground_y = Schlucht-Boden")
	# every film shot: subject >= 15 % of the picture height, in the picture, no rock in front
	for r in c({"do": "filmcheck"}).get("shots", []):
		pruef(bool(r["ok"]), "Film-Einstellung %s: Anteil %.2f, im Bild %s, frei %s, Abstand %.1f m" % [r["wo"], float(r["anteil"]), str(r["im_bild"]), str(r["frei"]), float(r["abstand"])])
	# walking
	await setzen(3.0, 0.0)
	var s0 := float(fig()["s"])
	c({"do": "eingabe", "mv": [1, 0], "s": 2.0})
	await _warte(2.3)
	pruef(float(fig()["s"]) - s0 > 1.5 and zustand() == "boden", "Gehen: vorwärts den Bach hinunter")
	# a jump
	c({"do": "eingabe", "sprung": true, "s": 0.2})
	ok = await _bis(func(): return zustand() == "luft", 1.0)
	pruef(ok, "Springen: in der Luft")
	ok = await _bis(func(): return zustand() == "boden", 3.0)
	pruef(ok, "Springen: wieder am Boden")
	# stepping stones
	await setzen(11.6, 0.2)
	pruef(str(fig().get("prompt", "")) == "Springen!", "Steine: Hinweis «Springen!»")
	for i in range(5):
		c({"do": "eingabe", "mv": [1, 0], "sprung": true, "s": 0.15})
		await _bis(func(): return zustand() == "luft", 1.0)
		await _bis(func(): return zustand() == "boden", 3.0)
		await _warte(0.3)
	var f := fig()
	pruef(float(f["s"]) > 20.0 and int(f["nass"]) == 0, "Steine: trockene Füsse bis ans andere Ufer (s %.1f)" % float(f["s"]))
	# into the water -> back to the checkpoint
	k.checkpoint_setzen("steine")
	await setzen(16.2, 5.0)
	ok = await _bis(func(): return int(fig()["nass"]) == 1 and zustand() == "boden", 4.0)
	await _warte(0.6)
	pruef(ok and absf(float(fig()["s"]) - 21.0) < 1.0, "Wasser: zurück zum Checkpoint")
	# the rock step
	await setzen(24.5, 0.0)
	var y0 := float(fig()["y"])
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return zustand() == "klettern", 1.0)
	pruef(ok, "Felsstufe: klettert")
	await _bis(func(): return zustand() == "boden", 3.0)
	pruef(float(fig()["y"]) - y0 > 1.3, "Felsstufe: oben (%.2f m höher)" % (float(fig()["y"]) - y0))
	# Maggie: lift onto the ledge, steer her through the window to the bolt
	await setzen(34.6, -4.3)
	k.hund.setzen_welt(k.par.welt(34.0, -3.0))
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return k.erledigt.has("maggie_heben") and str(k.hund.modus) == "oben", 5.0)
	pruef(ok, "Maggie hochgehoben")
	k._maggie_steuern(true)
	pruef(k.steuer_maggie and zustand() == "steuern" and k.regie.art == "maggie", "Maggie steuern: Kamera bei Maggie")
	var z0 = k.ziel_welt()
	pruef(z0 is Vector3 and absf(k.par.sq_von(z0).y + 5.6) < 0.3, "Maggie steuern: Kompass zeigt zuerst auf das Loch")
	# recovery: if she lands in the gap in front of the wall anyway, she is put back up onto the ledge
	k.hund.place(k.hund.hund, k.hund.VL(k.par.welt(36.62, -4.62)), false)
	await _warte(0.3)
	var hz: Vector3 = k.hund.VL(k.hund.hund.global_position)
	pruef(k.maggie_zurueck_n >= 1 and hz.y > k._sims_top() - 0.3, "Maggie aus der Lücke zurück auf den Sims (%d, y %.2f / Sims %.2f)" % [k.maggie_zurueck_n, hz.y, k._sims_top()])
	# like a player (owner 3.73.0: she fell into the gap and never got through): forward on the stick, a little drift to
	# the side; she never drops below the ledge before the wall, and down behind the wall she runs on to the bolt
	var tiefst := INF
	var t := 0.0
	var n0: int = k.maggie_zurueck_n
	while t < 8.0 and not k._maggie_auto and not k.erledigt.has("maggie_spalt"):
		c({"do": "eingabe", "mv": [1.0, 0.45 if t < 0.4 else 0.0], "s": 0.2})
		await _warte(0.05)
		t += 0.05
		var hy: Vector3 = k.hund.VL(k.hund.hund.global_position)
		var hsq: Vector2 = k.par.sq(Vector2(hy.x, hy.z))
		if hsq.x < 36.9:
			tiefst = minf(tiefst, hy.y)
	pruef(tiefst > k._sims_top() - 0.3 and k.maggie_zurueck_n == n0, "Maggie fällt vor dem Loch nicht hinunter (tiefst %.2f, Sims %.2f)" % [tiefst, k._sims_top()])
	pruef(k._maggie_auto or k.erledigt.has("maggie_spalt"), "Maggie mit dem Stick durch das Loch (%.1f s)" % t)
	var z1 = k.ziel_welt()
	pruef(z1 is Vector3 and absf(k.par.sq_von(z1).y - 0.2) < 0.4, "Maggie steuern: dann zeigt er auf den Riegel")
	ok = await _bis(func(): return k.erledigt.has("maggie_spalt"), 8.0)
	pruef(ok and not k.steuer_maggie, "Maggie durch den Spalt, läuft drüben selbst zum Riegel")
	k.par.tor_auf("tor")
	pruef(k.maggie_frei(k.par.tal(36.0, 0.8), k.par.tal(38.0, 0.8)), "Tor offen: Maggie kommt durch")
	# the log: children's mode across; without help: slip -> hang -> pull up
	k.kinder = true
	k.figur.kinder = true
	await setzen(39.4, 2.4)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return zustand() == "balance", 1.0)
	pruef(ok, "Baumstamm: balanciert")
	c({"do": "eingabe", "mv": [1, 0], "s": 9.0})
	ok = await _bis(func(): return zustand() == "boden", 10.0)
	pruef(ok and float(fig()["s"]) > 43.0, "Baumstamm: drüben (Kindermodus)")
	k.kinder = false
	k.figur.kinder = false
	await setzen(39.4, 2.4)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	await _bis(func(): return zustand() == "balance", 1.0)
	k.figur.balance = 0.97
	ok = await _bis(func(): return zustand() == "haengen", 3.0)
	pruef(ok, "Baumstamm: ausgerutscht → hängt")
	for i in range(6):
		c({"do": "eingabe", "sprung": true, "s": 0.08})
		await _warte(0.12)
	ok = await _bis(func(): return zustand() == "balance", 3.0)
	pruef(ok, "Hochgezogen: wieder auf dem Stamm")
	# ledge + ladder
	await setzen(43.1, -3.2)
	k.figur.zustand = "boden"
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	await _bis(func(): return zustand() == "boden" and float(fig()["y"]) > -100.0 and str(fig().get("prompt", "")) == "Leiter", 4.0)
	pruef(str(fig().get("prompt", "")) == "Leiter", "Absatz oben, Leiter da")
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return zustand() == "leiter", 1.0)
	pruef(ok, "Leiter: dran")
	c({"do": "eingabe", "mv": [1, 0], "s": 5.0})
	ok = await _bis(func(): return zustand() == "boden", 6.0)
	var top_a: float = k.par.welt(45.4, -3.2).y
	pruef(ok and absf(float(fig()["y"]) - top_a) < 0.15, "Leiter: oben auf der Wand")
	# the rope over the gap
	await setzen(46.1, -1.9)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return zustand() == "seil", 1.0)
	pruef(ok, "Seil: gepackt")
	ok = await _bis(func(): return str(fig().get("prompt", "")) == "Jetzt springen!", 3.0)
	pruef(ok, "Seil: Hinweis «Jetzt springen!»")
	c({"do": "eingabe", "sprung": true, "s": 0.1})
	await _bis(func(): return zustand() == "boden", 3.0)
	pruef(float(fig()["q"]) > 2.4 and absf(float(fig()["y"]) - k.par.welt(46.1, 3.3).y) < 0.2, "Seil: drüben (q %.1f)" % float(fig()["q"]))
	# a jump into the gap: grab the edge, nothing pressed -> back to the checkpoint
	k.checkpoint_setzen("oben")
	await setzen(46.1, -1.2)
	k.figur.a.heading = k.par.yaw_achse() - PI * 0.5
	c({"do": "eingabe", "mv": [0.0, 1.0], "sprung": true, "s": 0.4})
	ok = await _bis(func(): return zustand() == "haengen", 3.0)
	pruef(ok, "Spalt: am Rand festgehalten")
	ok = await _bis(func(): return zustand() == "boden" and absf(float(fig()["q"]) + 4.6) < 1.0, 8.0)
	pruef(ok, "Spalt: zurück zum Checkpoint")
	# the find
	await setzen(46.4, 5.9)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return k.funde.has("karabiner"), 2.0)
	pruef(ok, "Fund: Karabiner")
	# scenes 6–12 (the chapter as it is played: one scene after the other)
	await _szenen_6_12()
	# film + skip, pause, music
	c({"do": "szene", "value": "s02_schlucht"})
	ok = await _bis(func(): return str(info().get("phase", "")) == "film", 2.0)
	pruef(ok and k.regie.balken_ziel > 0.5, "Film: läuft mit Balken")
	c({"do": "skip"})
	ok = await _bis(func(): return str(info().get("phase", "")) == "spiel" and not k.regie.film_an, 2.0)
	pruef(ok and Engine.time_scale == 1.0, "Film: übersprungen")
	c({"do": "pause", "on": true})
	pruef(str(info()["phase"]) == "pause", "Pause an")
	c({"do": "pause", "on": false})
	pruef(str(info()["phase"]) == "spiel", "Pause aus")
	c({"do": "musik", "z": "action"})
	pruef(str(m.klang.kit_zustand) == "action" and m.klang.musik_wahl() in ["ostinato", "kit_action"] if m.klang.kontext == "kit" else str(m.klang.kit_zustand) == "action", "Musik: Zustand action")
	k.regie.zeitlupe(0.3, 0.2)
	await _warte(0.5)
	pruef(Engine.time_scale == 1.0, "Zeitlupe: wieder normal")
	pruef(m.busy_with() != "", "Welt belegt während des Spiels")
	c({"do": "stop"})
	await _warte(1.0)
	pruef(not k.running and k.figur == null, "Stopp: aufgeräumt")
	var bt2 = m.scenes.data.get("bergtal", null) if m.scenes != null else null
	pruef(bt2 == null or not bt2.boden_fn.is_valid(), "Stopp: eigener Boden weg")
	_ende()


func _skip_film() -> void:
	await _bis(func(): return str(info().get("phase", "")) == "film", 3.0)
	c({"do": "skip"})
	await _bis(func(): return str(info().get("phase", "")) != "film", 3.0)
	await _warte(0.3)


func _szenen_6_12() -> void:
	# 6: the bridge collapses behind you
	c({"do": "szene", "value": "s06_bruecke"})
	await _skip_film()
	var w0: Vector3 = k.par.welt(54.0, 3.0)
	var top0: float = m.ground_y(w0.x, w0.z)
	await setzen(54.0, -0.6)
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) == "film", 3.0)
	pruef(ok, "Brücke: Einsturz-Film beginnt in der Mitte")
	ok = await _bis(func(): return not k.qte.is_empty(), 5.0)
	pruef(ok and Engine.time_scale < 0.5, "Brücke: Zeitlupe und Greifen-Moment")
	c({"do": "eingabe", "sprung": true, "s": 0.1})
	await _warte(0.3)
	c({"do": "skip"})
	await _bis(func(): return str(info().get("phase", "")) == "spiel", 3.0)
	await _warte(0.5)
	var top1: float = m.ground_y(w0.x, w0.z)
	pruef(top0 - top1 > 1.0, "Brücke: hinter dir eingestürzt (%.1f m tiefer)" % (top0 - top1))
	pruef(k.abzeichen.has("bruecken_sprinter") and k.abzeichen.has("maggies_held"), "Brücke: «Brücken-Sprinter» (nie angehalten) und «Maggies Held» (gegriffen) %s" % str(k.abzeichen.keys()))
	pruef(str(info().get("szene", "")) == "s07_steinmann", "Brücke: weiter zum Steinmann")
	# 7: the map piece over the landscape
	await setzen(57.0, -4.6)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return k.karte_an, 2.0)
	pruef(ok, "Steinmann: Kartenstück hochgehalten")
	var dw: Vector3 = k.bt.tal.global_transform.basis * (Vector3(-20.0, 0, -350.0).normalized())
	k.regie.yaw = atan2(-dw.x, -dw.z)
	ok = await _bis(func(): return k.erledigt.has("karte"), 4.0)
	pruef(ok and not k.karte_an, "Steinmann: Linie passt zum Seeblock")
	# 8: the flashback (warm old colours, two young guides)
	ok = await _bis(func(): return str(info().get("szene", "")) == "s08_rueckblende" and str(info().get("phase", "")) == "film", 6.0)
	await _warte(1.5)
	pruef(ok and k.personen.has("toni") and k.personen.has("gv"), "Rückblende: Toni und {bezug} {jahr}")
	pruef(k.hud._sepia_ziel > 0.5, "Rückblende: alte Farben")
	c({"do": "skip"})
	await _bis(func(): return str(info().get("phase", "")) == "spiel", 3.0)
	pruef(k.personen.is_empty() and k.hud._sepia_ziel < 0.5, "Rückblende: vorbei")
	# 9: photo and diary scrap
	for f in [[58.6, -5.4, "foto"], [55.2, -5.9, "tagebuch"]]:
		await setzen(float(f[0]), float(f[1]))
		c({"do": "eingabe", "aktion": true, "s": 0.15})
		await _bis(func(): return k.funde.has(f[2]), 2.0)
	pruef(k.funde.has("foto") and k.funde.has("tagebuch") and k.abzeichen.has("alle_funde"), "Funde: Foto, Tagebuch → «Alle Funde»")
	# 10: Lia at the second waterfall
	ok = await _bis(func(): return str(info().get("szene", "")) == "s10_lia", 3.0)
	await setzen(58.0, -3.0)
	ok = await _bis(func(): return k.personen.has("lia"), 4.0)
	pruef(ok, "Lia: am zweiten Wasserfall")
	await _skip_film()
	# 11: the night camp with MoveEye
	ok = await _bis(func(): return str(info().get("szene", "")) == "s11_nachtlager", 3.0)
	await _skip_film()
	pruef(m.is_dark(), "Nachtlager: Nacht")
	c({"do": "setzen", "tal": [-21.0, -8.0]})
	await _warte(0.4)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return k.ir_an, 2.0)
	pruef(ok, "Nachtlager: IR-Licht an")
	await _skip_film()
	c({"do": "setzen", "tal": [-17.6, -4.6]})
	await _warte(0.4)
	c({"do": "eingabe", "aktion": true, "s": 0.15})
	ok = await _bis(func(): return k.funde.has("ir_zeichen"), 2.0)
	pruef(ok, "Nachtlager: Zeichen im IR gefunden")
	k.foto()
	pruef(k.erledigt.has("foto"), "Fotomodus: Foto")
	# 12: the empty tent, the open notebook
	ok = await _bis(func(): return str(info().get("szene", "")) == "s12_cliffhanger", 3.0)
	c({"do": "setzen", "tal": [-11.5, -14.0]})
	ok = await _bis(func(): return str(info().get("phase", "")) == "film", 4.0)
	pruef(ok, "Cliffhanger: Film beim leeren Zelt")
	c({"do": "skip"})
	ok = await _bis(func(): return str(info().get("phase", "")) == "ende", 3.0)
	pruef(ok and k.hud._ende != null, "Cliffhanger: Ende von Kapitel 2 mit Abzeichen")


func _ende() -> void:
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("Kit-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Kit-Test: " + str(e))
		quit(1)
