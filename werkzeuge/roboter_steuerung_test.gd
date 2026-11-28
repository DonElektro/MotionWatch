extends SceneTree
## Test «Roboter-Labor: Steuerung und Körper verschieben» (roboter_steuerung.gd, Besitzer 28.11.2026). Ohne Bild. Geprüft:
##   · Profile: Standard fest (W = vorwärts, linker Stick ↑), eine Änderung legt ein eigenes Profil an; zuweisen durch Drücken
##     («Taste drücken …» mit einem Tasten- und einem Joypad-Ereignis), Doppelbelegung wird gemeldet, umbenennen, löschen,
##     «Standard wiederherstellen»; Speichern und Laden (user://roboter_steuerung.json) mit denselben Werten
##   · Achse umkehren, Totzone (Ausschlag unter der Totzone = 0, darüber neu skaliert)
##   · Simulierte Ereignisse → Bewegungsbefehl: linker Stick ↑ = vorwärts (sanft: kein Sprung, nach 1 s voll), Taste D =
##     seitwärts rechts, Shift = schneller, Knopf A = Stopp, RB = nächste Gangart, R = neu aufstellen
##   · Körper verschieben (8, 6 und 4 Segmente): Füsse bleiben stehen (Toleranz), der Körper geht vor / seitwärts,
##     nicht gekippt; zu viel Wunsch wird an der Grenze gehalten; loslassen = sanft zurück zur Mitte, danach aus
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_steuerung_test.gd"   (absoluter Pfad nötig)
## Ende: «Steuerungstest OK» oder «SCRIPT ERROR: Steuerungstest: …» (Exit-Code 0 / 1).

const STEUERUNG = preload("res://scripts/roboter_steuerung.gd")
var main
var lab
var m
var st
var errs := []
var step := 0
var f0 := 0
var t_start := 0.0
var varianten := ["8", "6", "4"]
var vi := 0


func _initialize() -> void:
	for f in ["user://roboter_labor.json", "user://roboter_steuerung.json"]:
		var p := ProjectSettings.globalize_path(f)
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)                # every test starts from the start values
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


func key(code: int, down := true) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.pressed = down
	lab._input(e)


func joy_axis(axis: int, v: float) -> void:
	var e := InputEventJoypadMotion.new()
	e.axis = axis
	e.axis_value = v
	lab._input(e)


func joy_btn(b: int, down := true) -> void:
	var e := InputEventJoypadButton.new()
	e.button_index = b
	e.pressed = down
	lab._input(e)


func feet() -> Array:
	var out := []
	for i in range(m.n()):
		out.append(m.foot_world(i, -1))
		out.append(m.foot_world(i, 1))
	return out


func centre() -> Vector3:
	var c := Vector3.ZERO
	for k in range(m.n()):
		c += m.segment_xf(k).origin
	return c / m.n()


func upright() -> float:
	var w := 1.0
	for i in range(m.n()):
		w = minf(w, m.segment_xf(i).basis.y.normalized().y)
	return w


func _process(_dt: float) -> bool:
	if Time.get_ticks_msec() / 1000.0 - t_start > 500.0:
		errs.append("Zeit abgelaufen in Schritt %d" % step)
		return _end()
	match step:
		0:
			if Time.get_ticks_msec() / 1000.0 - t_start < 2.0:
				return false
			main.control({"action": "roboter", "do": "open", "variante": "8"})
			lab = main.roboter
			m = lab.model
			st = lab.steu
			check("Steuerung da, untere Leiste sichtbar", st != null and (st._ui["bar"] as Control).visible and st._ui.has("joy") and st._ui.has("kompass"), "")
			_profile_tests()
			next_step()
		1:
			if frames() < 240:                           # stand still first
				return false
			lab.reset()
			next_step()
		2:
			if frames() < 120:
				return false
			joy_axis(JOY_AXIS_LEFT_Y, -1.0)              # left stick fully up
			set_meta("c0", centre())
			next_step()
		3:
			if frames() >= 6 and not has_meta("s3"):
				set_meta("s3", true)
				check("Stick ↑: sanft (kein Sprung) nach 50 ms", st.out.y > 0.0 and st.out.y < 0.3 and lab.bew.mode == "gang",
						"%.2f, %s" % [st.out.y, lab.bew.mode])
			if frames() < 120:
				return false
			check("Stick ↑ nach 1 s: voll vorwärts", is_equal_approx(lab.bew.cmd.y, 1.0) and absf(lab.bew.cmd.x) < 1e-3, str(lab.bew.cmd))
			key(KEY_SHIFT)
			next_step()
		4:
			if frames() < 60:
				return false
			check("Shift = schneller", lab.bew.cmd.y > 1.4, "%.2f" % lab.bew.cmd.y)
			key(KEY_SHIFT, false)
			joy_axis(JOY_AXIS_LEFT_Y, 0.0)
			next_step()
		5:
			if frames() >= 6 and not has_meta("s5"):
				set_meta("s5", true)
				check("Stick los: sanft zurück (kein Sprung)", st.out.y > 0.5, "%.2f" % st.out.y)
			if frames() < 90:
				return false
			check("Stick los: Befehl 0", lab.bew.cmd == Vector3.ZERO, str(lab.bew.cmd))
			key(KEY_D)
			next_step()
		6:
			if frames() < 120:
				return false
			check("Taste D: seitwärts rechts", lab.bew.cmd.x < -0.99 and absf(lab.bew.cmd.y) < 1e-3, str(lab.bew.cmd))
			key(KEY_D, false)
			var g0: String = lab.bew.gang
			joy_btn(JOY_BUTTON_RIGHT_SHOULDER)
			joy_btn(JOY_BUTTON_RIGHT_SHOULDER, false)
			check("RB: nächste Gangart", lab.bew.gang != g0, "%s → %s" % [g0, lab.bew.gang])
			joy_btn(JOY_BUTTON_A)
			joy_btn(JOY_BUTTON_A, false)
			check("Knopf A: Stopp", lab.bew.mode == "" and st.out == Vector3.ZERO, lab.bew.mode)
			key(KEY_R)
			key(KEY_R, false)
			lab.bew.gang = "auto"
			next_step()
		7:
			if vi == 0 and not has_meta("p0") and frames() >= 240:
				set_meta("p0", true)
				st._ui["page_joy"].ziehen(Vector2(0.0, 1.0))        # virtual stick on the page «Bewegen»: up
				set_meta("pf", frames())
			elif vi == 0 and has_meta("p0") and not has_meta("p1") and frames() - int(get_meta("pf")) >= 120:
				set_meta("p1", true)
				check("virtueller Stick ↑ (Seite «Bewegen»): vorwärts", lab.bew.cmd.y > 0.99 and lab.bew.mode == "gang", str(lab.bew.cmd))
				st._ui["page_joy"].loslassen()
				st._ui["page_dreh"].ziehen(Vector2(1.0, 0.0))       # turn slider: right
				set_meta("pf", frames())
			elif vi == 0 and has_meta("p1") and not has_meta("p2") and frames() - int(get_meta("pf")) >= 120:
				set_meta("p2", true)
				check("Stick los + Dreh-Regler rechts: an Ort drehen rechts", lab.bew.cmd.z < -0.99 and absf(lab.bew.cmd.y) < 1e-3, str(lab.bew.cmd))
				st._ui["page_dreh"].loslassen()
				check("Dreh-Regler los: Stopp (kein Fahrbefehl der Knöpfe bleibt)", lab.manual == Vector3.ZERO and st.maus_dreh == 0.0, str(lab.manual))
				set_meta("pf", frames())
			elif (vi > 0 and frames() >= 240) or (has_meta("p2") and frames() - int(get_meta("pf")) >= 120):
				if vi == 0:
					check("Dreh-Regler los: Befehl 0", lab.bew.cmd == Vector3.ZERO, str(lab.bew.cmd))
				_koerper_start()
				next_step()
			return false
		8:
			if frames() < 120 * 3:
				return false
			_koerper_check("vor")
			lab.control({"do": "koerper", "x": 1.0, "y": 0.0})    # sideways: + = left
			set_meta("seit0", st.k_off)
			next_step()
		9:
			if frames() < 120 * 3:
				return false
			var f1: Array = feet()
			var f0_: Array = get_meta("feet0")
			var worst := 0.0
			for i in range(f1.size()):
				worst = maxf(worst, Vector2(f1[i].x - f0_[i].x, f1[i].z - f0_[i].z).length())
			var dz: float = centre().dot(st._k_left) - (get_meta("cc0") as Vector3).dot(st._k_left)
			check("%ser seitwärts links: Körper verschoben" % m.n(), dz > 0.02 and st.k_off.z > 0.02, "%.1f cm (soll %.1f cm)" % [dz * 100.0, st.k_off.z * 100.0])
			check("%ser seitwärts: Füsse bleiben stehen" % m.n(), worst < 0.025, "%.1f cm" % (worst * 100.0))
			check("%ser seitwärts: nicht gekippt" % m.n(), upright() > 0.9 and not lab._tipped(), "%.2f" % upright())
			lab.control({"do": "koerper", "x": 5.0, "y": 5.0, "h": -1.0})
			next_step()
		10:
			if frames() < 120 * 2:
				return false
			check("%ser zu viel Wunsch: an der Grenze gehalten, nicht gekippt" % m.n(), st.k_grenze < 1.0 and upright() > 0.85 and not lab._tipped(),
					"Anteil %.2f" % st.k_grenze)
			lab.control({"do": "koerper", "los": true})
			st._k_cmd = {}                                 # release: back to the middle
			next_step()
		11:
			if frames() < 120 * 2:
				return false
			check("%ser loslassen: sanft zurück zur Mitte" % m.n(), st.k_off.length() < 0.004, "%.1f cm" % (st.k_off.length() * 100.0))
			lab.control({"do": "koerper", "on": false})
			next_step()
		12:
			if frames() < 120:
				return false
			check("%ser Körper verschieben aus" % m.n(), not st.koerper, st.k_phase)
			vi += 1
			if vi < varianten.size():
				lab.set_variante(varianten[vi])
				m = lab.model
				st = lab.steu
				step = 6                                     # stand, then the body test again
				next_step()
				f0 = Engine.get_physics_frames()
			else:
				_ring_check()
				return _end()
	return false


func _profile_tests() -> void:
	check("Standard: W = vorwärts, linker Stick ↑ = vorwärts, A = Stopp", st.aktiv == "Standard" and int(st.prof()["tasten"]["vor"]) == KEY_W
			and st.prof()["pad"]["vor"] == {"t": "achse", "i": JOY_AXIS_LEFT_Y, "d": -1} and st.prof()["pad"]["stopp"] == {"t": "knopf", "i": JOY_BUTTON_A}, "")
	var glyphs := []
	for n in lab.win.find_children("*", "Button", true, false):
		for g in ["✕", "⟲", "⟳"]:
			if (n as Button).text.contains(g):
				glyphs.append((n as Button).text)
	check("keine Zeichen ✕ ⟲ ⟳ im Labor (gezeichnet statt Schrift)", glyphs.is_empty(), str(glyphs))
	check("Seite «Bewegen»: virtueller Stick und Dreh-Regler statt Richtungsknöpfe", st._ui.has("page_joy") and st._ui.has("page_dreh")
			and (st._ui["page_joy"] as Control).is_inside_tree(), "")
	check("Standard: keine Doppelbelegung", st.doppelt().is_empty(), str(st.doppelt()))
	st.open_map()
	check("Fenster «Belegung» offen", st.map_open() and (st._ui["map_body"] as Control).get_child_count() > 20, "")
	# assign by pressing: «vor» gets the key I (Standard → an own profile first)
	st.start_capture("vor", "taste")
	key(KEY_I)
	key(KEY_I, false)
	check("Taste drücken: «Vorwärts» = I in einem eigenen Profil", st.aktiv != "Standard" and int(st.prof()["tasten"]["vor"]) == KEY_I
			and int(STEUERUNG.standard()["tasten"]["vor"]) == KEY_W, st.aktiv)
	var own: String = st.aktiv
	st.start_capture("stopp", "pad")
	joy_axis(JOY_AXIS_TRIGGER_LEFT, 0.9)
	joy_axis(JOY_AXIS_TRIGGER_LEFT, 0.0)
	check("Controller drücken: «Stopp» = LT (Achse +)", st.prof()["pad"]["stopp"] == {"t": "achse", "i": JOY_AXIS_TRIGGER_LEFT, "d": 1},
			str(st.prof()["pad"].get("stopp")))
	var dp: Dictionary = st.doppelt()
	check("LT doppelt (Stopp und Langsamer) wird gemeldet", dp.has("stopp") and (dp["stopp"] as Array).has("langsamer"), str(dp))
	st.start_capture("zurueck", "pad")
	joy_btn(JOY_BUTTON_DPAD_DOWN)
	joy_btn(JOY_BUTTON_DPAD_DOWN, false)
	check("Controller drücken: «Rückwärts» = Steuerkreuz ↓", st.prof()["pad"]["zurueck"] == {"t": "knopf", "i": JOY_BUTTON_DPAD_DOWN}, "")
	st.start_capture("neu", "taste")
	key(KEY_ESCAPE)
	check("Esc bricht ab (R bleibt)", st.capture.is_empty() and int(st.prof()["tasten"]["neu"]) == KEY_R and lab.is_open(), "")
	# invert + dead zone
	st.set_totzone(0.2)
	joy_axis(JOY_AXIS_LEFT_X, 0.15)
	var under: float = st.achse(JOY_AXIS_LEFT_X)
	joy_axis(JOY_AXIS_LEFT_X, 0.6)
	var over: float = st.achse(JOY_AXIS_LEFT_X)
	check("Totzone 20 %: 0.15 → 0, 0.6 → 0.5", under == 0.0 and absf(over - 0.5) < 1e-3, "%.3f / %.3f" % [under, over])
	st.umkehren(JOY_AXIS_LEFT_X, true)
	check("Achse umkehren: 0.6 → −0.5, also links statt rechts", absf(st.achse(JOY_AXIS_LEFT_X) + 0.5) < 1e-3
			and st.wert("links") > 0.49 and st.wert("rechts") == 0.0, "%.2f" % st.achse(JOY_AXIS_LEFT_X))
	joy_axis(JOY_AXIS_LEFT_X, 0.0)
	# save / load
	check("umbenennen", st.umbenennen("Mein Pad") and st.aktiv == "Mein Pad" and not st.profile.has(own), st.aktiv)
	var s2 = STEUERUNG.new()
	s2.laden()
	check("Speichern / Laden: gleiches Profil, gleiche Werte", s2.aktiv == "Mein Pad" and s2.prof() == st.prof(), "%s / %s" % [s2.aktiv, str(s2.prof()["totzone"])])
	check("Gespeichert: I, LT, umgekehrt, Totzone", int(s2.prof()["tasten"]["vor"]) == KEY_I and (s2.prof()["umkehren"] as Array) == [JOY_AXIS_LEFT_X]
			and is_equal_approx(float(s2.prof()["totzone"]), 0.2), "")
	st.neues_profil("Zweites")
	check("neues Profil = Kopie", st.aktiv == "Zweites" and int(st.prof()["tasten"]["vor"]) == KEY_I and st.namen() == ["Standard", "Mein Pad", "Zweites"], str(st.namen()))
	check("löschen", st.loeschen() and st.aktiv == "Standard" and st.namen() == ["Standard", "Mein Pad"], str(st.namen()))
	check("Standard lässt sich nicht löschen / umbenennen", not st.loeschen() and not st.umbenennen("X"), "")
	st.waehle("Mein Pad")
	st.standard_wiederherstellen()
	check("Standard wiederherstellen", st.aktiv == "Mein Pad" and st.prof() == STEUERUNG.standard() and st.doppelt().is_empty(), "")
	st.waehle("Standard")
	st.close_map()
	check("Fenster zu", not st.map_open(), "")


func _koerper_start() -> void:
	lab.control({"do": "koerper", "on": true, "y": 1.0})          # forward, held
	set_meta("start_t", Engine.get_physics_frames())


func _koerper_check(_what: String) -> void:
	# called 3 s after the start: the feet were taken after 0.6 s (phase «warten»)
	var ki: Dictionary = st.koerper_info()
	check("%ser Körper verschieben an" % m.n(), st.koerper and st.k_phase == "aktiv", st.k_phase)
	var f0_ := []
	for f in ki["feet"]:
		f0_.append(Vector3(f[0][0], f[0][1], f[0][2]))
		f0_.append(Vector3(f[1][0], f[1][1], f[1][2]))
	set_meta("feet0", f0_)
	var f1: Array = feet()
	var worst := 0.0
	for i in range(f1.size()):
		worst = maxf(worst, Vector2(f1[i].x - f0_[i].x, f1[i].z - f0_[i].z).length())
	var c0: Vector3 = st._k_c0
	var dx: float = (centre() - c0).dot(st._k_fw)
	check("%ser vor: Körper verschoben" % m.n(), dx > 0.02 and st.k_off.x > 0.02, "%.1f cm (soll %.1f cm, Anteil %.2f)" % [dx * 100.0, st.k_off.x * 100.0, st.k_grenze])
	check("%ser vor: Füsse bleiben stehen" % m.n(), worst < 0.025, "%.1f cm" % (worst * 100.0))
	check("%ser vor: nicht gekippt" % m.n(), upright() > 0.9 and not lab._tipped(), "%.2f" % upright())
	set_meta("cc0", c0)


func _ring_check() -> void:
	# Modus «Ring» on the 4er (the variant at the end) and in the ring: «links» = Kurve (Ring kippen)
	st.set_modus("ring")
	check("Modus Ring: Ring verriegelt / rollt", lab.bew.mode == "ring", lab.bew.mode)
	check("Körper verschieben im Ring: abgelehnt", not st.koerper_an() and not st.koerper, "")


func _end() -> bool:
	if main != null and main.roboter != null and main.roboter.is_open():
		main.roboter.close()
	if errs.is_empty():
		print("Steuerungstest OK")
		quit(0)
	else:
		push_error("Steuerungstest: " + "; ".join(errs))
		quit(1)
	return true
