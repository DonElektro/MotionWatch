extends SceneTree
## Test «Roboter-Labor, klassische Laufroboter» (Besitzer 28.11.2026 14:40): Vierbeiner und Sechsbeiner. Ohne Bild.
## Geprüft je Modell:
##   · Öffnen über /control mit variante «k4» / «k6»: ein Körper, 4 / 6 Beine, Antriebe 3 je Bein + Kamera, kein Ring
##   · gleiche Schnittstelle wie der Segment-Roboter: n() Beinpaare, segment_xf(i), legs(), leg_ik ↔ leg_fk, foot_world
##   · steht stabil (Kipp-Reserve > 0, keine Kollision, kein Servo überlastet)
##   · jede Gangart (Vierbeiner Schritt / Trab / Passgang, Sechsbeiner Dreifuss / Welle / Raupe, dazu Automatisch) kommt in
##     GANG_SEK s mindestens WEG_MIN m vorwärts, ohne zu kippen; Servo-Last im Rahmen (höchstens LAST_MAX)
##   · seitwärts, rückwärts, an Ort drehen (≥ 45°, dabei kaum verschoben), Kurve (vorwärts + drehen)
##   · Posen sitzen / liegen / eingeklappt, Ablauf «Aufstehen»
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_klassisch_test.gd"   (absoluter Pfad nötig)
## Ende: «RoboterKlassisch-Test OK» oder «SCRIPT ERROR: RoboterKlassisch-Test: …» (Exit-Code 0 / 1).

const GANG_SEK := 10.0
const WEG_MIN := 0.25
const LAST_MAX := 1.0

var main
var lab
var m
var errs := []
var t_start := 0.0
var jobs := []                         # [{name, variante?, do: Callable, dauer, check: Callable}]
var job := {}
var jt := 0.0
var p0 := Vector3.ZERO
var yaw0 := 0.0
var last_max := 0.0
var tipped := false
var ergebnisse := []


func _initialize() -> void:
	var p := ProjectSettings.globalize_path("user://roboter_labor.json")
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	t_start = Time.get_ticks_msec() / 1000.0
	for v in ["k4", "k6"]:
		_plan(v)


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func body() -> Transform3D:
	return m.body_xf()


func yaw() -> float:
	var x: Vector3 = body().basis.x
	return rad_to_deg(atan2(-x.z, x.x))


func _plan(v: String) -> void:
	var nm := "Vierbeiner" if v == "k4" else "Sechsbeiner"
	jobs.append({"name": nm + ": öffnen", "dauer": 3.0, "do": func(): _open(v), "check": func(): _check_build(v)})
	jobs.append({"name": nm + ": steht", "dauer": 2.0, "do": func(): pass, "check": func(): _check_stand(nm)})
	var gs: Array = ["schritt", "trab", "pass", "auto"] if v == "k4" else ["dreifuss", "welle", "raupe", "auto"]
	for g in gs:
		var gg: String = g
		jobs.append({"name": nm + ": Gangart " + gg, "dauer": GANG_SEK, "do": func(): _walk(gg, Vector3(0, 1, 0)),
				"check": func(): _check_walk(nm, gg, "vor")})
	jobs.append({"name": nm + ": seitwärts", "dauer": 6.0, "do": func(): _walk("auto", Vector3(1, 0, 0)), "check": func(): _check_walk(nm, "auto", "links")})
	jobs.append({"name": nm + ": rückwärts", "dauer": 6.0, "do": func(): _walk("auto", Vector3(0, -1, 0)), "check": func(): _check_walk(nm, "auto", "zurück")})
	jobs.append({"name": nm + ": diagonal", "dauer": 6.0, "do": func(): _walk("auto", Vector3(-1, 1, 0)), "check": func(): _check_walk(nm, "auto", "diagonal")})
	jobs.append({"name": nm + ": an Ort drehen", "dauer": 8.0, "do": func(): _walk("auto", Vector3(0, 0, 1)), "check": func(): _check_turn(nm)})
	jobs.append({"name": nm + ": Kurve", "dauer": 8.0, "do": func(): _walk("auto", Vector3(0, 1, 0.6)), "check": func(): _check_curve(nm)})
	for ps in ["sitzen", "liegen", "eingeklappt"]:
		var pp: String = ps
		jobs.append({"name": nm + ": Pose " + pp, "dauer": 2.5, "do": func():
				lab.control({"do": "stop"})
				lab.control({"do": "pose", "name": pp}), "check": func(): _check_pose(nm, pp)})
	jobs.append({"name": nm + ": Aufstehen", "dauer": 6.0, "do": func(): lab.control({"do": "ablauf", "name": "aufstehen"}),
			"check": func(): _check_stand(nm + " nach dem Aufstehen")})


func _open(v: String) -> void:
	var d: Dictionary = main.control({"action": "roboter", "do": "open", "variante": v})
	lab = main.roboter
	m = lab.model
	check(v + " offen", bool(d.get("open", false)) and str(d.get("variante", "")) == v and bool(d.get("klassisch", false)), str(d.get("variante")))


func _check_build(v: String) -> void:
	var legs := 4 if v == "k4" else 6
	check(v + ": %d Beine, %d Antriebe, %d Körper" % [legs, legs * 3 + 1, legs * 3 + 1],
			m.n() * 2 == legs and m.actuator_count() == legs * 3 + 1 and m.servos.size() == legs * 3 + 1 and m.bodies.size() == legs * 3 + 1,
			"%d / %d / %d" % [m.n(), m.servos.size(), m.bodies.size()])
	check(v + ": legs() hat %d Einträge, Paar 0 vorne" % legs, m.legs().size() == legs and m.leg_x(0) > m.leg_x(m.n() - 1))
	var ok_ik := true
	for lg in m.legs():
		var f: Vector3 = lab.bew.stand_foot(lg["s"]) + Vector3(0.02, 0.01, 0.0)
		var a: Array = lab.bew.leg_ik(lg["s"], f)
		if lab.bew.leg_fk(lg["s"], a[0], a[1], a[2]).distance_to(f) > 0.002:
			ok_ik = false
	check(v + ": leg_ik ↔ leg_fk stimmen (Rahmen des Beinpaars)", ok_ik)
	check(v + ": kein Ring, keine Kupplung, keine Segmentgelenke", m.servo_index("sp0") < 0 and m.servo_index("riegel") < 0 and m.latch["state"] == "open")
	# the foot in the physics is where the frame of its leg pair says
	var worst := 0.0
	for lg in m.legs():
		var want: Vector3 = m.segment_xf(lg["i"]) * lab.bew.leg_fk(lg["s"], m.servos[m.servo_index("hy" + lg["id"])]["angle"],
				m.servos[m.servo_index("hp" + lg["id"])]["angle"], m.servos[m.servo_index("kn" + lg["id"])]["angle"])
		worst = maxf(worst, want.distance_to(m.foot_world(lg["i"], lg["s"])))
	check(v + ": foot_world = segment_xf · leg_fk", worst < 0.01, "%.1f mm" % (worst * 1000.0))


func _check_stand(nm: String) -> void:
	var h: float = body().origin.y
	check(nm + ": steht (Körper %.1f cm hoch, Kipp-Reserve %.1f cm)" % [h * 100.0, lab.anz.margin * 100.0],
			h > 0.05 and not lab._tipped() and lab.anz.margin > 0.01 and m.overloaded().is_empty() and m.collide.is_empty(),
			"überlastet %s, rot %s" % [str(m.overloaded()), str(m.colliding_names())])


func _walk(g: String, c: Vector3) -> void:
	lab.control({"do": "stop"})
	lab.control({"do": "gang", "name": g, "drive": c.y, "strafe": c.x, "turn": c.z})


func _check_walk(nm: String, g: String, dir: String) -> void:
	var d: Vector3 = body().origin - p0
	var bx: Vector3 = Basis(Vector3.UP, deg_to_rad(yaw0)) * Vector3.RIGHT
	var fwd := d.dot(bx)
	var lat := d.dot(Vector3(bx.z, 0, -bx.x))                      # + links
	var weg := fwd
	var ziel := WEG_MIN
	match dir:
		"links":
			weg = lat
			ziel = 0.12
		"zurück":
			weg = -fwd
			ziel = 0.12
		"diagonal":
			weg = minf(fwd, -lat) * sqrt(2.0)
			ziel = 0.12
	var dauer: float = job["dauer"]
	var tempo := weg / dauer
	var gn: String = lab.bew.gang_now
	ergebnisse.append("%s %s %s: %.2f m in %d s = %.1f cm/s, Last max %.2f%s" % [nm, g + ("→" + gn if g == "auto" else ""), dir, weg, int(dauer), tempo * 100.0, last_max, ", GEKIPPT" if tipped else ""])
	check("%s: %s %s ≥ %.2f m ohne Sturz, Last ≤ %.1f" % [nm, g, dir, ziel, LAST_MAX], weg >= ziel and not tipped and last_max <= LAST_MAX,
			"%.2f m, Last %.2f, %s" % [weg, last_max, "gekippt" if tipped else "steht"])


func _check_turn(nm: String) -> void:
	var dy := absf(wrapf(yaw() - yaw0, -180.0, 180.0))
	var d: Vector3 = body().origin - p0
	d.y = 0.0
	ergebnisse.append("%s an Ort drehen: %d° in %d s (%.0f °/s), verschoben %.1f cm, Last max %.2f" % [nm, int(dy), int(job["dauer"]), dy / float(job["dauer"]), d.length() * 100.0, last_max])
	check(nm + ": dreht an Ort ≥ 45°, verschoben < 8 cm", dy >= 45.0 and d.length() < 0.08 and not tipped and last_max <= LAST_MAX,
			"%d°, %.1f cm, Last %.2f" % [int(dy), d.length() * 100.0, last_max])


func _check_curve(nm: String) -> void:
	var dy := wrapf(yaw() - yaw0, -180.0, 180.0)
	var d: Vector3 = body().origin - p0
	d.y = 0.0
	ergebnisse.append("%s Kurve links: %d°, %.2f m" % [nm, int(dy), d.length()])
	check(nm + ": Kurve links (dreht ≥ 20° nach links und kommt ≥ 0.15 m weit)", dy >= 20.0 and d.length() >= 0.15 and not tipped,
			"%d°, %.2f m" % [int(dy), d.length()])


func _check_pose(nm: String, ps: String) -> void:
	var h: float = body().origin.y
	var ok: bool = not lab._tipped() and m.overloaded().is_empty()
	if ps == "liegen":
		ok = ok and h < float(m.u("halbe_hoehe")) + 0.02
	if ps == "sitzen":
		ok = ok and body().basis.x.y > 0.1                        # front up
	check("%s: Pose %s (Körper %.1f cm)" % [nm, ps, h * 100.0], ok, "überlastet %s, Neigung %.2f" % [str(m.overloaded()), body().basis.x.y])


func _process(_dt: float) -> bool:
	var t := Time.get_ticks_msec() / 1000.0 - t_start
	if t > 700.0:
		errs.append("Zeit abgelaufen bei " + str(job.get("name", "")))
		return _end()
	if t < 2.0:
		return false
	if job.is_empty():
		if jobs.is_empty():
			return _end()
		job = jobs.pop_front()
		print("· " + str(job["name"]))
		(job["do"] as Callable).call()
		jt = 0.0
		m = lab.model if lab != null else m
		p0 = body().origin if m != null and m.built_ok else Vector3.ZERO
		yaw0 = yaw() if m != null and m.built_ok else 0.0
		last_max = 0.0
		tipped = false
		return false
	return false


func _physics_process(dt: float) -> bool:
	if job.is_empty() or m == null or not m.built_ok:
		return false
	jt += dt
	if jt > 1.0:                                                  # the first second: the servos reach the start
		for sv in m.servos:
			last_max = maxf(last_max, float(sv["load"]))
		if lab._tipped():
			tipped = true
	if jt >= float(job["dauer"]):
		(job["check"] as Callable).call()
		job = {}
	return false


func _end() -> bool:
	print("\nErgebnisse:")
	for r in ergebnisse:
		print("  " + r)
	if errs.is_empty():
		print("RoboterKlassisch-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: RoboterKlassisch-Test: " + " | ".join(errs))
		quit(1)
	return true
