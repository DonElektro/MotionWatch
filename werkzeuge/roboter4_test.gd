extends SceneTree
## Test «Roboter-Labor, 4 Segmente» (Besitzer 22.11.2026 21:33): die zweite Variante neben der mit 8 Segmenten. Ohne Bild.
## Eigener Test, damit roboter_test.gd (8 Segmente) im CI nicht zu lang wird. Geprüft:
##   · Öffnen über /control mit variante «4»: 4 Segmente, 8 Beine, 32 Antriebe (2·3 + 8·3 + Kamera + Riegel); variante_aus
##   · Jede Variante behält ihre eigenen Regler (4er ändern, auf 8 wechseln: Startwert, zurück auf 4: der geänderte Wert)
##   · Ring 4 × 90° (die Schrägen liegen flach): Kupplung verriegelt, alle Segmentgelenke 90°
##   · Gehen: Wellengang vorwärts, seitwärts; Spurbreite beim Gehen
##   · Rund rollen, Methode C «Füsse passen sich an»: eine ganze Drehung, Messwerte (Mittenhöhe, Tempo, Kontakte) da
##   · 6er (Besitzer 21:54): 6 Segmente, 48 Antriebe, Ring 6 × 60° verriegelt ohne Kollision
##   · Ansicht (Besitzer 23.11.2026): Kamerabild und Info-Feld mit I / K, Knopf «Bedienfeld» aus / ein, je Variante gespeichert
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter4_test.gd"   (absoluter Pfad nötig)
## Ende: «Roboter4-Test OK» oder «SCRIPT ERROR: Roboter4-Test: …» (Exit-Code 0 / 1).

var main
var lab
var m
var errs := []
var step := 0
var f0 := 0
var t_start := 0.0


func _initialize() -> void:
	var p := ProjectSettings.globalize_path("user://roboter_labor.json")
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)                    # every test starts from the start values
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	t_start = Time.get_ticks_msec() / 1000.0


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func frames() -> int:
	return Engine.get_physics_frames() - f0


func next_step() -> void:
	step += 1
	f0 = Engine.get_physics_frames()


func centre() -> Vector3:
	var c := Vector3.ZERO
	for k in range(m.n()):
		c += m.segment_xf(k).origin
	return c / m.n()


func sane() -> bool:
	for b in m.bodies:
		var q: Vector3 = (b["rb"] as RigidBody3D).global_position
		if is_nan(q.x) or q.length() > 50.0:
			return false
	return true


func _process(_dt: float) -> bool:
	if Time.get_ticks_msec() / 1000.0 - t_start > 400.0:
		errs.append("Zeit abgelaufen in Schritt %d" % step)
		return _end()
	match step:
		0:
			if Time.get_ticks_msec() / 1000.0 - t_start < 2.0:
				return false
			var L = load("res://scripts/roboter_labor.gd")
			check("variante_aus: 4 → 4, 6 → 6, 1 → 8", L.variante_aus("4") == "4" and L.variante_aus("6") == "6" and L.variante_aus("1") == "8" and L.variante_aus("") == "8")
			var d: Dictionary = main.control({"action": "roboter", "do": "open", "variante": "4"})
			lab = main.roboter
			m = lab.model
			check("4er offen", bool(d.get("open", false)) and str(d.get("variante", "")) == "4", str(d.get("variante")))
			check("4 Segmente, 32 Antriebe, 31 Körper", m.n() == 4 and m.actuator_count() == 32 and m.servos.size() == 32 and m.bodies.size() == 31,
					"%d / %d / %d" % [m.n(), m.actuator_count(), m.bodies.size()])
			# Besitzer 23.11.2026: Kamerabild und Info-Feld ausblenden (✕, Leiste, K / I), je Variante gespeichert
			check("Kamerabild und Info-Feld zu Beginn sichtbar, Knöpfe in der Leiste", lab.pip_box.visible and (lab._w["info_box"] as Control).visible
					and lab._w.has("chip_pip") and lab._w.has("chip_info") and lab._w.has("chip_panel"), "")
			var kev := InputEventKey.new()
			kev.pressed = true
			kev.keycode = KEY_I
			lab._input(kev)
			kev.keycode = KEY_K
			lab._input(kev)
			check("Taste I / K blendet Info-Feld und Kamerabild aus", not (lab._w["info_box"] as Control).visible and not lab.pip_box.visible,
					"info %s, kamera %s" % [(lab._w["info_box"] as Control).visible, lab.pip_box.visible])
			(lab._w["chip_panel"] as Button).pressed.emit()
			check("Knopf «Bedienfeld» blendet das Bedienfeld aus", not (lab._w["panel"] as Control).visible, "")
			(lab._w["chip_panel"] as Button).pressed.emit()
			lab.set_shape("oberschenkel", 1.4)
			lab.set_shape("segmente", 7)
			check("4er: Segmente bleiben 4", int(m.p["segmente"]) == 4, str(m.p["segmente"]))
			lab.set_variante("8")
			m = lab.model
			check("Wechsel auf 8: eigene Werte (Startwert)", m.n() == 8 and is_equal_approx(float(m.p["oberschenkel"]), 1.19), "%d, %.2f" % [m.n(), m.p["oberschenkel"]])
			check("8er: eigene Ansicht (Kamerabild und Info sichtbar)", lab.pip and lab.info_on and lab.pip_box.visible and (lab._w["info_box"] as Control).visible, "")
			lab.set_variante("4")
			m = lab.model
			check("Zurück auf 4: der geänderte Wert ist noch da", m.n() == 4 and is_equal_approx(float(m.p["oberschenkel"]), 1.4), "%.2f" % m.p["oberschenkel"])
			check("Zurück auf 4: Kamerabild und Info bleiben ausgeblendet (gespeichert)", not lab.pip and not lab.info_on and not lab.pip_box.visible
					and not (lab._w["info_box"] as Control).visible, "pip %s info %s" % [lab.pip, lab.info_on])
			lab.control({"do": "pip", "on": true})
			lab.control({"do": "info", "on": true})
			check("Wieder einblenden über /control", lab.pip_box.visible and (lab._w["info_box"] as Control).visible, "")
			lab.set_shape("oberschenkel", 1.19)
			next_step()
		1:
			if frames() < 90:
				return false
			lab.apply_pose("ring", true)
			next_step()
		2:
			if frames() < 240:
				return false
			var worst := 0.0
			for i in range(3):
				worst = maxf(worst, absf(float(m.servos[m.servo_index("sp%d" % i)]["angle"]) - 90.0))
			check("Ring 4 × 90°: Kupplung verriegelt", m.latch["state"] == "locked", "%s %.4f m %.1f°" % [m.latch["state"], m.latch["err_pos"], m.latch["err_ang"]])
			check("Ring 4 × 90°: Segmentgelenke 90°", worst < 4.0, "höchstens %.1f° daneben" % worst)
			check("Ring 4 × 90°: ruhig, ganz", sane() and m.max_speed() < 0.5, "%.2f m/s" % m.max_speed())
			lab.stop_all()
			lab.apply_pose("gerade", true)
			lab.control({"do": "gang", "name": "welle", "drive": 1.0})
			set_meta("c0", centre())
			next_step()
		3:
			if frames() < 120 * 6:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			check("4er Wellengang vorwärts (6 s)", rel.x > 0.1 and sane() and not lab._tipped(), "%.2f m" % rel.x)
			lab.stop_all()
			lab.reset()
			lab.drive_dir(Vector3(1.0, 0.0, 0.0))
			set_meta("c0", centre())
			next_step()
		4:
			if frames() < 120 * 6:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			check("4er seitwärts links (6 s)", rel.z < -0.1 and absf(rel.x) < 0.06, "dx %.2f dz %.2f m" % [rel.x, rel.z])
			lab.stop_all()
			lab.bew.set_spur_gehen(0.3)
			check("Spurbreite beim Gehen 30 cm", absf(lab.bew.spur_gehen() - 0.3) < 0.002, "%.3f m" % lab.bew.spur_gehen())
			lab.control({"do": "rund", "methode": "c"})             # the measured start values of the 4er (height, track)
			lab.apply_pose("ring", true)
			next_step()
		5:
			if frames() < 180:
				return false
			lab.control({"do": "ring", "drive": 1.0})
			next_step()
		6:
			if frames() < 120:
				return false
			lab.bew.start_ring_measure()
			next_step()
		7:
			var r: Dictionary = lab.bew.ring_result
			if r.is_empty() and frames() < 120 * 40 and m.latch["state"] == "locked":
				return false
			check("4er rollt im Ring (C): eine ganze Drehung gemessen", not r.is_empty() and m.latch["state"] == "locked",
					JSON.stringify(r).left(240) if not r.is_empty() else "keine ganze Drehung")
			if not r.is_empty():
				check("4er C: Mitte schwankt höchstens 4 cm, Kontakte gezählt", float(r["dh"]) < 4.0 and float(r["kavg"]) > 1.0,
						"%.2f cm, Ø %.1f Kontakte" % [r["dh"], r["kavg"]])
			lab.stop_all()
			lab.set_variante("6")
			m = lab.model
			check("6er (Besitzer 21:54): 6 Segmente, 48 Antriebe, 47 Körper", m.n() == 6 and m.actuator_count() == 48 and m.bodies.size() == 47,
					"%d / %d / %d" % [m.n(), m.actuator_count(), m.bodies.size()])
			lab.apply_pose("ring", true)
			next_step()
		8:
			if frames() < 240:
				return false
			var worst := 0.0
			for i in range(5):
				worst = maxf(worst, absf(float(m.servos[m.servo_index("sp%d" % i)]["angle"]) - 60.0))
			check("Ring 6 × 60°: Kupplung verriegelt, Gelenke 60°, keine Kollision", m.latch["state"] == "locked" and worst < 4.0 and m.collide.is_empty(),
					"%s, %.1f° daneben, %s" % [m.latch["state"], worst, m.colliding_names()])
			main.roboter.control({"do": "close"})
			next_step()
		9:
			if frames() < 10:
				return false
			check("Geschlossen: Physik wieder wie vorher", Engine.physics_ticks_per_second == 30, str(Engine.physics_ticks_per_second))
			return _end()
	return false


func _end() -> bool:
	if errs.is_empty():
		print("Roboter4-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Roboter4-Test: " + " | ".join(errs))
		quit(1)
	return true
