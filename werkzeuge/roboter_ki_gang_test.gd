extends SceneTree
## Test «Gang-KI» im Roboter-Labor (roboter_ki_gang.gd: Stufe 1 Sehen + Stufe 2 Setzen). Ohne Bild. Geprüft:
##   · Sehen: Höhenraster 75 × 50 Zellen à 2 cm; vor jeder Prüfstrecke wird das Hindernis erkannt und vermessen
##     (Art und Masse ± Toleranz: Stufe 6 / 10 cm, Treppe 3 × 4 cm, Graben 20 cm, Lücke 15 / 30 cm, Rohr 6 / 10 cm,
##     Balken 16 cm, Rampe 15°, Kies und Geröll), auf der freien Startspur nichts
##   · Schnittstelle für Stufe 3: STRATEGIEN, strategie_ausfuehren / strategie_status / abbrechen / neu_aufstellen
##   · Setzen: mit der Gangart «KI» schafft der 8er Stufe 6 cm, Rampe 15° und Kies ohne Sturz; kein Fuss setzt ins Leere
##     (auch an der Lücke 15 cm); der 6er und der 4er schaffen die Stufe 6 cm mit der KI
##   Mit --alle (nach dem Skriptnamen): zusätzlich alle anderen Strecken mit dem 8er (nur gemeldet).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_ki_gang_test.gd"   (absoluter Pfad nötig)
## Ende: «Gang-KI-Test OK» oder «SCRIPT ERROR: Gang-KI-Test: …» (Exit-Code 0 / 1).

const GEL = preload("res://scripts/roboter_gelaende.gd")
const KI = preload("res://scripts/roboter_ki_gang.gd")
var main
var lab
var errs := []
var notes := []


func _initialize() -> void:
	var p := ProjectSettings.globalize_path("user://roboter_labor.json")
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run()


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func warte(sek: float) -> void:
	var f := Engine.get_physics_frames() + int(sek * Engine.physics_ticks_per_second)
	while Engine.get_physics_frames() < f:
		await physics_frame


func aufstellen(lane: String) -> void:
	lab.stop_all()
	lab.ki.abbrechen()
	lab.model.root_xf = lab.starts[lane]
	lab.apply_pose("gerade", true)
	await warte(1.0)


func lauf(lane: String) -> Array:
	"""walk the lane with the KI: [ok, text, seconds, tipped]"""
	lab.control({"do": "gelaende", "name": lane, "ki": true})
	var t0 := Engine.get_physics_frames()
	var tip := false
	while not lab.terrain.is_empty() and Engine.get_physics_frames() - t0 < 120 * 160:
		await physics_frame
		if lab._tipped():
			tip = true
	var r: Array = lab.terrain_results.get(lane, [false, "kein Ergebnis"])
	return [bool(r[0]), str(r[1]), (Engine.get_physics_frames() - t0) / 120.0, tip]


func ohne_lernen() -> void:
	"""Stufe 2 allein prüfen: das Lernen im Hintergrund (Stufe 3, roboter_ki_lernen.gd) aus - es hat einen eigenen Test"""
	if lab.get("ki_lernen") != null:
		lab.ki_lernen.an = false


func nah(a: float, b: float, tol: float) -> bool:
	return absf(a - b) <= tol


func _run() -> void:
	await create_timer(2.0).timeout
	main.control({"action": "roboter", "do": "open"})
	lab = main.roboter
	await warte(1.0)
	ohne_lernen()
	var ki = lab.ki
	check("Labor offen, Gang-KI angelegt", lab.is_open() and ki != null and lab.bew.ki == ki and "ki" in lab.bew.GAENGE.map(func(x): return x[0]))
	check("Schnittstelle A → B: Strategien und Funktionen", KI.STRATEGIEN == ["normal", "hoch_steigen", "aufrichten_vorne", "bruecke", "umgehen", "einrollen_rollen", "kriechen_drunter"]
			and ki.has_method("sehen") and ki.has_method("setze_stil") and ki.has_method("setze_befehl") and ki.has_method("strategie_ausfuehren")
			and ki.has_method("strategie_status") and ki.has_method("abbrechen") and ki.has_method("neu_aufstellen"))
	# ---- Sehen ----
	await aufstellen("start")
	var b: Dictionary = ki.sehen()
	check("Raster 75 × 50 Zellen à 2 cm", (b["hoehe"] as PackedFloat32Array).size() == 75 * 50 and is_equal_approx(float(b["zelle"]), 0.02))
	check("Startspur: freie Bahn", (b["hindernisse"] as Array).is_empty(), str(b["hindernisse"]))
	var tol := {"hoehe": 0.015, "breite": 0.035, "tiefe": 0.025, "neigung": 3.0, "stufen": 0.0}
	for lane in GEL.SOLL:
		await aufstellen(lane)
		b = ki.sehen()
		var hs: Array = b["hindernisse"]
		var soll: Dictionary = GEL.SOLL[lane]
		var h: Dictionary = hs[0] if not hs.is_empty() else {}
		var ok: bool = not h.is_empty() and str(h["art"]) == str(soll["art"])
		var det := []
		for k in soll:
			if k == "art":
				continue
			var ist := float(h.get(k, -1.0))
			det.append("%s %.3f/%.3f" % [k, ist, float(soll[k])])
			if lane == "rampe" and k == "hoehe":
				continue                               # the window does not reach the top of the ramp
			if not nah(ist, float(soll[k]), float(tol[k])):
				ok = false
		var ab := float(h.get("abstand", -1.0))
		check("Sehen %s: %s erkannt" % [lane, soll["art"]], ok, (str(h.get("art", "nichts")) + " · " + ", ".join(det) + " · Abstand %.2f m" % ab))
	# ---- Strategie-Schnittstelle ----
	await aufstellen("stufe")
	ki.sehen()
	ki.strategie_ausfuehren("hoch_steigen", {"tempo": 0.08})
	await warte(0.5)
	var st: Dictionary = ki.strategie_status()
	check("strategie_status läuft (hoch_steigen, Tempo vom Parameter)", bool(st["laeuft"]) and str(st["strategie"]) == "hoch_steigen" and is_equal_approx(lab.bew.tempo, 0.08), str(st))
	ki.abbrechen()
	st = ki.strategie_status()
	check("abbrechen: fertig, kein Erfolg", not bool(st["laeuft"]) and bool(st["fertig"]) and not bool(st["erfolg"]), str(st))
	ki.sehen()
	var h0: Dictionary = ki.bild["hindernisse"][0]
	ki.neu_aufstellen(h0)
	await warte(1.0)
	var d0: float = (h0["pos"] as Vector3).dot(Vector3.RIGHT) - ki._kopf().x
	check("neu_aufstellen: 0.5 m vor dem Hindernis, Blick hin", nah(d0, 0.5, 0.06) and ki._vorne().dot(Vector3.RIGHT) > 0.98, "%.2f m" % d0)
	# ---- Setzen: gehen mit der KI ----
	ki.tritte = 0
	ki.tritte_leer = 0
	for lane in ["stufe", "rampe", "kies", "luecke"]:
		var r := await lauf(lane)
		if lane == "luecke":
			notes.append("luecke: %s" % r[1])
			print("  info Lücke 15 cm mit KI: %s (%.0f s)" % [r[1], r[2]])
		else:
			check("KI 8 Segmente: %s geschafft, nicht gestürzt" % lane, bool(r[0]) and not bool(r[3]), "%s, %.0f s" % [r[1], r[2]])
	check("Trittpunkte nie ins Leere (8er, %d Tritte geprüft)" % ki.tritte, ki.tritte > 50 and ki.tritte_leer == 0, "%d ins Leere, %d versetzt" % [ki.tritte_leer, ki.tritte_versetzt])
	if "--alle" in OS.get_cmdline_user_args() or "--alle" in OS.get_cmdline_args():
		for lane in ["graben", "stufe_hoch", "treppe", "luecke_breit", "rohr", "rohr_dick", "balken", "geroell"]:
			var r := await lauf(lane)
			print("  info %s mit KI: %s (%.0f s)%s · %s" % [lane, r[1], r[2], " GEKIPPT" if r[3] else "", str(ki.strategie_status())])
	# ---- 6 und 4 Segmente ----
	for v in ["6", "4"]:
		lab.control({"do": "info", "variante": v})
		lab = main.roboter
		ohne_lernen()
		await warte(1.0)
		lab.ki.tritte_leer = 0
		var r := await lauf("stufe")
		check("KI %s Segmente: stufe geschafft, nicht gestürzt, nie ins Leere" % v, bool(r[0]) and not bool(r[3]) and lab.ki.tritte_leer == 0, "%s, %.0f s, %d ins Leere" % [r[1], r[2], lab.ki.tritte_leer])
	lab.control({"do": "info", "variante": "8"})
	main.roboter.control({"do": "close"})
	if errs.is_empty():
		print("Gang-KI-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Gang-KI-Test: " + " | ".join(errs))
		quit(1)
