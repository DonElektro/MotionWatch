extends SceneTree
## Test «Roboter-Labor, 3 und 2 Segmente» (Besitzer 28.11.2026 14:40): 6 bzw. 4 Beine, gleiche Masse wie der 8er. Ohne Bild.
## Geprüft je Variante (erst 3, dann 2):
##   · Öffnen über /control mit variante «3» / «2»: Segmente, Antriebe (2·(N−1) + 6·N + Kamera + Riegel), Körper; variante_aus
##   · Segmentzahl fest (Regler «Segmente» gesperrt, set_shape bleibt bei N)
##   · Ring geht nicht: Knopf «Ring», «Einrollen», «Im Ring rollen» und «Rund rollen» gesperrt, Hinweis sichtbar,
##     /control ring → Fehler, Pose «Ring» ändert nichts, der Riegel bleibt offen
##   · Stehen: 3 s in der Pose «Gerade», aufrecht, Körper über dem Boden
##   · Jede Gangart (Wellengang, Dreifuss / Trab, Raupengang, Automatisch) kommt vorwärts, ohne zu kippen
##   · Seitwärts links, Kamera vorne schwenkt
##   · Gelände-Test «Stufe 6 cm» läuft und meldet ein Ergebnis
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter23_test.gd"   (absoluter Pfad nötig)
## Ende: «Roboter23-Test OK» oder «SCRIPT ERROR: Roboter23-Test: …» (Exit-Code 0 / 1).

const GAENGE := ["welle", "dreifuss", "raupe", "auto"]
const GANG_S := 8.0                    # s je Gangart
const MIN_WEG := 0.10                  # m vorwärts in GANG_S

var main
var lab
var m
var errs := []
var step := 0
var f0 := 0
var t_start := 0.0
var vari := ["3", "2"]
var vi := 0
var gi := 0


func _initialize() -> void:
	var p := ProjectSettings.globalize_path("user://roboter_labor.json")
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)                    # every test starts from the start values
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	t_start = Time.get_ticks_msec() / 1000.0
	var a := OS.get_cmdline_user_args()
	if "--nur" in a:                                    # lokal: nur eine Variante (-- --nur 2)
		vari = [a[a.find("--nur") + 1]]


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func frames() -> int:
	return Engine.get_physics_frames() - f0


func next_step(to := -1) -> void:
	step = step + 1 if to < 0 else to
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


func lowest_body() -> float:
	"""height of the lowest segment centre above the ground (the start lane is flat at y = 0)"""
	var y := 99.0
	for k in range(m.n()):
		y = minf(y, m.segment_xf(k).origin.y)
	return y


func _process(_dt: float) -> bool:
	if Time.get_ticks_msec() / 1000.0 - t_start > 500.0:
		errs.append("Zeit abgelaufen in Schritt %d (Variante %s)" % [step, vari[mini(vi, vari.size() - 1)]])
		return _end()
	var v: String = vari[mini(vi, vari.size() - 1)]
	var N := int(v)
	match step:
		0:
			if Time.get_ticks_msec() / 1000.0 - t_start < 2.0:
				return false
			var L = load("res://scripts/roboter_labor.gd")
			check("variante_aus: 3 → 3, 2 → 2, 5 → 8", L.variante_aus("3") == "3" and L.variante_aus("2") == "2" and L.variante_aus("5") == "8")
			next_step()
		1:
			var d: Dictionary = main.control({"action": "roboter", "do": "open", "variante": v})
			lab = main.roboter
			m = lab.model
			var act := 2 * (N - 1) + 6 * N + 2
			check("%ser offen" % v, bool(d.get("open", false)) and str(d.get("variante", "")) == v, str(d.get("variante")))
			check("%s Segmente, %d Beine, %d Antriebe, %d Körper" % [v, 2 * N, act, act - 1], m.n() == N and m.actuator_count() == act
					and m.servos.size() == act and m.bodies.size() == act - 1, "%d / %d / %d" % [m.n(), m.actuator_count(), m.bodies.size()])
			check("%ser: gleiche Masse wie der 8er (Startwerte)" % v, is_equal_approx(float(m.p["halbe_breite"]), 0.45)
					and is_equal_approx(float(m.p["oberschenkel"]), 1.19) and is_equal_approx(float(m.p["massstab"]), 0.10), "")
			lab.set_shape("segmente", 7)
			check("%ser: Segmente bleiben %s, Regler gesperrt" % [v, v], int(m.p["segmente"]) == N
					and not (lab._w["form_segmente"]["sl"] as HSlider).editable, str(m.p["segmente"]))
			# Ring: geht geometrisch nicht
			check("%ser: kein Ring möglich" % v, not lab.ring_ok() and not m.ring_ok() and not bool(lab.info().get("ring_ok", true)))
			var need: Array = lab._w.get("ring_need", [])
			var all_off := need.size() >= 8
			for c in need:
				if c is BaseButton and not (c as BaseButton).disabled:
					all_off = false
				elif c is Range and (c as Range).editable:
					all_off = false
			check("%ser: Ring-Knöpfe gesperrt (Pose, Einrollen, Im Ring rollen, Rund rollen, Gelände)" % v, all_off
					and (lab._w["pose_ring"] as Button).disabled and (lab._w["ab_einrollen"] as Button).disabled
					and (lab._w["ring_btn"] as Button).disabled and (lab._w["terrain_ring"] as BaseButton).disabled, "%d Elemente" % need.size())
			var hints: Array = lab._w.get("ring_hints", [])
			var hv := hints.size() >= 3
			for l in hints:
				hv = hv and (l as Label).visible and (l as Label).text != ""
			check("%ser: Hinweis «Ring braucht mindestens 4 Segmente» sichtbar" % v, hv, "%d Hinweise" % hints.size())
			var r: Dictionary = lab.control({"do": "ring", "drive": 1.0})
			check("%ser: /control ring abgelehnt" % v, not bool(r.get("ok", true)) and str(r.get("error", "")) != "" and lab.bew.mode != "ring", str(r.get("error", "")))
			lab.apply_pose("ring", true)
			lab.start_ablauf("einrollen")
			lab.rund_start("eine")
			check("%ser: Pose Ring / Einrollen / Rund messen tun nichts" % v, lab.last_pose != "ring" and lab.bew.mode != "ablauf"
					and lab.rund_jobs.is_empty(), "%s / %s / %d" % [lab.last_pose, lab.bew.mode, lab.rund_jobs.size()])
			if N == 2:
				check("2er: «Dreifuss» heisst Trab", (lab._w["gang_dreifuss"] as Button).text != "" and lab.gang_name("dreifuss") != lab.gang_name("welle")
						and "Dreifuss" not in lab.gang_name("dreifuss"), lab.gang_name("dreifuss"))
			lab.apply_pose("gerade", true)
			next_step()
		2:
			if frames() < 120 * 3:
				return false
			var tilt := 1.0
			for k in range(N):
				tilt = minf(tilt, m.segment_xf(k).basis.y.y)
			check("%ser steht (3 s): aufrecht, Körper über dem Boden, ruhig" % v, sane() and tilt > 0.9 and lowest_body() > 0.04
					and m.max_speed() < 0.1 and m.latch["state"] == "open", "Neigung cos %.2f, Höhe %.1f cm, %.2f m/s, Riegel %s"
					% [tilt, lowest_body() * 100.0, m.max_speed(), m.latch["state"]])
			gi = 0
			next_step()
		3:
			lab.stop_all()
			lab.reset()
			lab.control({"do": "gang", "name": GAENGE[gi], "drive": 1.0})
			set_meta("c0", centre())
			set_meta("tip", false)
			set_meta("tilt", 1.0)
			next_step()
		4:
			if lab._tipped():
				set_meta("tip", true)
			if frames() > 120:
				for k in range(N):
					set_meta("tilt", minf(float(get_meta("tilt")), m.segment_xf(k).basis.y.y))
			if frames() < int(120 * GANG_S):
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			var tilt_deg := rad_to_deg(acos(clampf(float(get_meta("tilt")), -1.0, 1.0)))
			check("%ser %s vorwärts (%d s) ohne Sturz, höchstens 30° geneigt" % [v, GAENGE[gi], int(GANG_S)], rel.x > MIN_WEG and sane()
					and not bool(get_meta("tip")) and tilt_deg < 30.0,
					"%.2f m, Gang %s, Höhe %.1f cm, Neigung bis %.0f°" % [rel.x, lab.bew.gang_now, lowest_body() * 100.0, tilt_deg])
			gi += 1
			if gi < GAENGE.size():
				next_step(3)
				return false
			lab.stop_all()
			lab.reset()
			lab.drive_dir(Vector3(1.0, 0.0, 0.0))
			set_meta("c0", centre())
			next_step()
		5:
			if frames() < 120 * 6:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			check("%ser seitwärts links (6 s)" % v, rel.z < -0.08 and absf(rel.x) < 0.08 and not lab._tipped(), "dx %.2f dz %.2f m" % [rel.x, rel.z])
			lab.stop_all()
			lab.control({"do": "set", "id": "pan", "value": 45.0})
			next_step()
		6:
			if frames() < 120:
				return false
			var pa: float = float(m.servos[m.servo_index("pan")]["angle"])
			check("%ser: Kamera vorne schwenkt (45°)" % v, absf(pa - 45.0) < 3.0, "%.1f°" % pa)
			lab.control({"do": "set", "id": "pan", "value": 0.0})
			lab.control({"do": "gelaende", "name": "stufe"})
			next_step()
		7:
			var res: Array = lab.terrain_results.get("stufe", [])
			if lab.terrain.is_empty() == false and frames() < 120 * 60:
				return false
			check("%ser Gelände-Test «Stufe» meldet ein Ergebnis" % v, not res.is_empty() and str(res[1]) != "", str(res))
			print("  info %ser Stufe: %s" % [v, str(res)])
			lab.terrain = {}
			lab.stop_all()
			vi += 1
			if vi < vari.size():
				next_step(1)
				return false
			main.roboter.control({"do": "close"})
			next_step()
		8:
			if frames() < 10:
				return false
			check("Geschlossen: Physik wieder wie vorher", Engine.physics_ticks_per_second == 30, str(Engine.physics_ticks_per_second))
			return _end()
	return false


func _end() -> bool:
	if errs.is_empty():
		print("Roboter23-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Roboter23-Test: " + " | ".join(errs))
		quit(1)
	return true
