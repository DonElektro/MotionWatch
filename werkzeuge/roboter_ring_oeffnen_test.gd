extends SceneTree
## Test «Roboter-Labor: Ring öffnen» (Besitzer 28.11.2026: «Gerade» brachte den Roboter nicht aus dem Ring, er kämpfte gegen
## den Riegel). Ohne Bild. Geprüft:
##   · Knopf «Ring öffnen (gerade)» (Seite Bewegen und Haltungen): Ring verriegelt → zuerst rollt der Ring den Riegel nach
##     oben (offen trägt der Ring seine Hälften nicht), dann Riegel auf, unten beginnend gestreckt; nach der Zeit gerade
##     (alle Segmentgelenke klein), «Riegel darf schliessen» wieder an, und der Riegel schliesst danach nicht von selbst
##   · Haltung «Gerade» bei geschlossenem Ring nimmt denselben Ablauf (statt gegen den Riegel zu drücken)
##   · Schalter «Riegel darf schliessen (Ring)» während des Öffnens aus → bleibt danach aus (zählt erst, wenn die Enden weit
##     genug auseinander sind)
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_ring_oeffnen_test.gd"   (absoluter Pfad nötig)
## Ende: «Ring-öffnen-Test OK» oder «SCRIPT ERROR: Ring-öffnen-Test: …» (Exit-Code 0 / 1).

var main
var lab
var m
var errs := []
var step := 0
var f0 := 0
var t_start := 0.0
var closed_again := false


func _initialize() -> void:
	var p := ProjectSettings.globalize_path("user://roboter_labor.json")
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)                    # every test starts from the start values (8 segments)
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


func body_angle() -> float:
	"""largest segment joint angle (up / down and left / right), measured"""
	var w := 0.0
	for i in range(m.n() - 1):
		for k in ["sp%d" % i, "sy%d" % i]:
			w = maxf(w, absf(float(m.servos[m.servo_index(k)]["angle"])))
	return w


func angles_text() -> String:
	var t := []
	for i in range(m.n() - 1):
		for k in ["sp%d" % i, "sy%d" % i]:
			var sv: Dictionary = m.servos[m.servo_index(k)]
			t.append("%s %.0f/%.0f" % [k, float(sv["angle"]), float(sv["target"])])
	return ", ".join(t)


func sane() -> bool:
	for b in m.bodies:
		var q: Vector3 = (b["rb"] as RigidBody3D).global_position
		if is_nan(q.x) or q.length() > 50.0:
			return false
	return true


func _process(_dt: float) -> bool:
	if Time.get_ticks_msec() / 1000.0 - t_start > 300.0:
		errs.append("Zeit abgelaufen in Schritt %d" % step)
		return _end()
	if m != null and m.built_ok and step in [3, 7] and m.latch["state"] != "open":
		closed_again = true
	match step:
		0:
			if Time.get_ticks_msec() / 1000.0 - t_start < 2.0:
				return false
			var d: Dictionary = main.control({"action": "roboter", "do": "open", "variante": "8"})
			lab = main.roboter
			m = lab.model
			check("Labor offen, 8 Segmente", bool(d.get("open", false)) and m.n() == 8, str(d.get("segments")))
			check("Knopf «Ring öffnen (gerade)» auf Bewegen und bei den Haltungen", lab._w.get("oeffnen_btn") is Button and lab._w.get("oeffnen_btn_posen") is Button)
			lab.set_hold(false)
			lab.apply_pose("ring", true)
			next_step()
		1, 5:
			if m.latch["state"] != "locked" and frames() < 120 * 6:
				return false
			check("Ring verriegelt (%s)" % ("Knopf" if step == 1 else "Haltung «Gerade»"), m.latch["state"] == "locked",
					"%s, %.4f m, %.1f°" % [m.latch["state"], m.latch["err_pos"], m.latch["err_ang"]])
			if step == 1:
				(lab._w["oeffnen_btn"] as Button).pressed.emit()
			else:
				lab.apply_pose("gerade")
			check("Öffnen läuft (%s)" % ("Knopf" if step == 1 else "Haltung «Gerade»"),
					lab.bew.mode == "ablauf" and lab.bew.seq_name == "oeffnen", "%s / %s" % [lab.bew.mode, lab.bew.seq_name])
			closed_again = false
			next_step()
		2, 6:
			if m.latch["state"] == "open" and not has_meta("phi%d" % step):
				set_meta("phi%d" % step, rad_to_deg(lab.bew.latch_phi()))
				set_meta("t%d" % step, frames() / 120.0)
			if step == 6 and frames() >= 60 and not has_meta("aus"):
				set_meta("aus", true)
				var lt: CheckButton = lab._w.get("latch_ok")
				if lt != null:
					lt.toggled.emit(false)                  # the switch off while it opens
			if lab.bew.mode == "ablauf" and frames() < 120 * 25:
				return false
			var who := "Knopf" if step == 2 else "Haltung «Gerade»"
			check("Riegel geht oben auf (%s)" % who, has_meta("phi%d" % step) and absf(float(get_meta("phi%d" % step))) < 20.0,
					"%.0f° nach %.1f s" % [get_meta("phi%d" % step, 999.0), get_meta("t%d" % step, -1.0)])
			check("Ganzer Ablauf unter 15 s (%s)" % who, frames() < 120 * 15, "%.1f s" % (frames() / 120.0))
			check("Danach: Riegel offen (%s)" % who, m.latch["state"] == "open" and not closed_again, m.latch["state"])
			check("Danach: Körper gerade, Segmentgelenke < 6° (%s)" % who, body_angle() < 6.0, "höchstens %.1f°: %s" % [body_angle(), angles_text()])
			check("Danach: Ablauf fertig, ohne Explosion (%s)" % who, lab.bew.mode == "" and sane(), lab.bew.mode)
			if step == 2:
				check("«Riegel darf schliessen» wieder an", m.latch_wanted and not lab.bew.latch_wait, "%s / %s" % [m.latch_wanted, lab.bew.latch_wait])
			else:
				check("Schalter während des Öffnens aus → bleibt aus", not m.latch_wanted and not lab.bew.latch_wait, "%s / %s" % [m.latch_wanted, lab.bew.latch_wait])
			next_step()
		3, 7:
			if frames() < 120 * 4:
				return false
			check("4 s später: Riegel schliesst nicht von selbst (%s)" % ("Knopf" if step == 3 else "Haltung «Gerade»"),
					m.latch["state"] == "open" and not closed_again and body_angle() < 6.0, "%s, %.1f°" % [m.latch["state"], body_angle()])
			if step == 3:
				lab.apply_pose("ring", true)
				next_step()
				step = 5                                    # round 2: the pose «Gerade»
				f0 = Engine.get_physics_frames()
			else:
				var lt: CheckButton = lab._w.get("latch_ok")
				if lt != null:
					lt.toggled.emit(true)
				check("Schalter wieder an → Riegel darf schliessen", m.latch_wanted)
				main.roboter.control({"do": "close"})
				return _end()
	return false


func _end() -> bool:
	if errs.is_empty():
		print("Ring-öffnen-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Ring-öffnen-Test: " + " | ".join(errs))
		quit(1)
	return true
