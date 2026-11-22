extends SceneTree
## Test «Roboter-Labor» (roboter_labor.gd, roboter_modell.gd, roboter_bewegung.gd): der Segment-Roboter des Besitzers in
## seiner eigenen Welt. Ohne Bild. Geprüft:
##   · Öffnen über /control «roboter»: 8 Segmente, 64 Antriebe, Physik mit 120 Schritten/s (nach dem Schliessen wieder wie vorher)
##   · Stehen («Gerade»): ruhig nach 4 s (keine Explosion, kein Wegrutschen), Servos am Ziel, Körper in der richtigen Höhe
##   · Gelenk-Grenzen: Ziele ausserhalb werden begrenzt, die Gelenke bleiben innerhalb (Segmentgelenk ±90°, Knie ±180°)
##   · Bein-Rechnung: Fuss-Lage aus den Winkeln = gewünschte Lage (inverse Kinematik und Modell rechnen gleich)
##   · Ring: 8 × 45°, die Kupplung verriegelt, der Ring bleibt stabil stehen
##   · Servo-Grenze: schwache Bein-Servos geben nach und melden «überlastet»
##   · Kollision rot: zwei Beine, die sich kreuzen, werden gefunden
##   · Formregler: 6 Segmente → neuer Aufbau mit 2·5 + 6·6 + 2 = 48 Antrieben
##   · Wellengang läuft vorwärts und kippt nie; Strom und Last werden gerechnet
##   · Automatisch: ein Ziel links vorne wird selbst erreicht (Kurve + Gang)
##   · Abläufe: «Aufstehen» endet stehend, «Einrollen und öffnen» läuft ohne Explosion durch (ob der Ring schliesst,
##     hängt vom Servo-Moment ab: nur gemeldet)
##   · Ring rollen: die Füsse stossen den verriegelten Ring vorwärts; mit «Kurve» neigt er sich und fährt nach links
##   · Stufe 4: seitwärts (Krebsgang), an Ort drehen ≥ 90°, schräg; Ziel hinten → zuerst an Ort drehen; «Körper passt sich
##     dem Untergrund an»: Stufe 6 cm und Rampe 15° geschafft, nicht gekippt, Bodenabstand je Segment 0.5 … 15 cm
##   · Direkt öffnen (Homepage-Kachel, 22.11.2026): Browser ?roboter=1 → --roboter=1 (nicht zusammen mit ?grossvater), das Labor
##     geht nach dem Start von selbst auf; kleiner Bildschirm (Handy): Hinweis «Am besten am PC», Bedienfeld zu, Knopf «Bedienfeld»
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_test.gd"   (absoluter Pfad nötig)
## Ende: «Robotertest OK» oder «SCRIPT ERROR: Robotertest: …» (Exit-Code 0 / 1).

var main
var lab
var m
var errs := []
var step := 0
var f0 := 0
var vmax_all := 0.0
var t_start := 0.0
var notes := []
const RS = preload("res://scripts/roboter_start.gd")
const WEB = preload("res://scripts/web.gd")


func _initialize() -> void:
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


func max_err(ids := []) -> Array:
	var e := 0.0
	var who := ""
	for sv in m.servos:
		if sv["parent"] < 0 or (not ids.is_empty() and not ids.has(sv["id"])):
			continue
		var d := absf(float(sv["angle"]) - float(sv["target"]))
		if d > e:
			e = d
			who = sv["id"]
	return [e, who]


func centre() -> Vector3:
	var c := Vector3.ZERO
	for k in range(m.n()):
		c += m.segment_xf(k).origin
	return c / m.n()


func head() -> float:
	var h: Vector3 = m.segment_xf(0).origin - m.segment_xf(m.n() - 1).origin
	return rad_to_deg(atan2(-h.z, h.x))


func sample_clearance() -> void:
	"""belly to the local ground (the same gap-bridging profile the robot uses: highest of centre and ± one segment)"""
	var w: float = m.u("halbe_breite")
	for k in range(m.n()):
		var xf: Transform3D = m.segment_xf(k)
		var g := -9.0
		for kk in [-1.0, 0.0, 1.0]:
			g = maxf(g, lab.bew._ground_at(xf.origin + xf.basis.x * m.pitch_len() * kk, xf.origin.y + 0.4, -1.0))
		var cl: float = xf.origin.y - w - g
		set_meta("cnt", int(get_meta("cnt")) + 1)
		if cl < 0.005 or cl > 0.15:
			set_meta("bad", int(get_meta("bad")) + 1)
	if lab._tipped():
		set_meta("tip", true)


func sane() -> bool:
	for b in m.bodies:
		var p: Vector3 = (b["rb"] as RigidBody3D).global_position
		if is_nan(p.x) or is_nan(p.y) or is_nan(p.z) or p.length() > 50.0:
			return false
	return true


func _process(_dt: float) -> bool:
	var t := Time.get_ticks_msec() / 1000.0 - t_start
	if t > 850.0:
		errs.append("Zeit abgelaufen in Schritt %d" % step)
		return _end()
	if m != null and m.built_ok:
		vmax_all = maxf(vmax_all, m.max_speed() if step not in [6] else 0.0)
	match step:
		0:
			if t < 2.0:
				return false
			if not has_meta("auto"):
				set_meta("auto", t)
				set_meta("auto_f", Engine.get_process_frames())
				check("?roboter=1 → --roboter=1 (Wert geht als «variante» ans Labor)", Array(WEB.roboter_args({"roboter": "1"})) == ["--roboter=1"]
						and Array(WEB.roboter_args({"roboter": "4"})) == ["--roboter=4"] and Array(WEB.roboter_args({"szene": "wald"})).is_empty()
						and Array(WEB.roboter_args({"roboter": "0"})).is_empty() and Array(WEB.roboter_args({"roboter": "1", "grossvater": "1"})).is_empty()
						and Array(WEB.roboter_args({"roboter": "<x>"})).is_empty())
				check("Startoption --roboter: Labor, mit dem Spiel nicht", RS.autostart_ziel(PackedStringArray(["--scene", "garten", "--roboter"])) == "1"
						and RS.autostart_ziel(PackedStringArray(["--roboter=4"])) == "4" and RS.autostart_ziel(PackedStringArray(["--roboter", "--grossvater-neu"])) == ""
						and RS.autostart_ziel(PackedStringArray([])) == "")
				check("Handy-Grösse: 390 × 844 klein, 1366 × 768 nicht", RS.klein_fuer(Vector2(390, 844)) and not RS.klein_fuer(Vector2(1366, 768)))
				check("ohne --roboter bleibt das Labor zu", main.roboter == null or not main.roboter.is_open())
				RS.klein_test = false                                # (the headless window is tiny: the PC case here, the phone at the end)
				RS.autostart_pruefen(main, WEB.roboter_args({"roboter": "1"}))
				return false
			if not main.roboter.is_open():
				if t - float(get_meta("auto")) < RS.AUTOSTART_SEK + 10.0 or Engine.get_process_frames() - int(get_meta("auto_f")) < 300:
					return false
				errs.append("--roboter: das Labor ging nicht auf")
				return _end()
			var d: Dictionary = main.control({"action": "roboter", "do": "info"})
			check("--roboter: das Labor geht nach dem Start von selbst auf (am PC Bedienfeld offen, kein Hinweis)", bool(d.get("open", false))
					and (main.roboter._w["panel"] as Control).visible and main.roboter.layer.find_child("hinweis_pc", true, false) == null)
			lab = main.roboter
			m = lab.model
			check("Labor offen", bool(d.get("open", false)), str(d))
			check("8 Segmente", int(d.get("segments", 0)) == 8, str(d.get("segments")))
			check("64 Antriebe (README: 14 + 48 + Kamera + Riegel)", int(d.get("actuators", 0)) == 64 and m.servos.size() == 64, str(d.get("actuators")))
			check("63 Körper (8 Segmente, 7 Bügel, 16 × 3 Beinteile)", m.bodies.size() == 63, str(m.bodies.size()))
			check("Physik 120 Schritte/s", Engine.physics_ticks_per_second == 120, str(Engine.physics_ticks_per_second))
			lab.apply_pose("gerade", true)
			set_meta("c0", m.com())
			next_step()
		1:
			if frames() < 480:
				return false
			var e := max_err()
			var c: Vector3 = m.com()
			check("Stehen: ruhig nach 4 s", m.max_speed() < 0.05 and sane(), "v %.3f m/s" % m.max_speed())
			check("Stehen: Servos am Ziel", float(e[0]) < 3.0, "%.1f° bei %s" % e)
			check("Stehen: Schwerpunkt 5 … 12 cm hoch", c.y > 0.05 and c.y < 0.12, "%.3f m" % c.y)
			check("Stehen: nicht weggerutscht", Vector2(c.x - (get_meta("c0") as Vector3).x, c.z - (get_meta("c0") as Vector3).z).length() < 0.03, str(c))
			check("Stehen: keine Überlast, keine Kollision", m.overloaded().is_empty() and m.collide.is_empty(), "%s %s" % [m.overloaded(), m.colliding_names()])
			# leg maths = model
			var bw = lab.bew
			var worst := 0.0
			for foot in [Vector3(0.03, -0.08, 0.17), Vector3(-0.05, -0.02, 0.2), Vector3(0.0, -0.12, 0.1)]:
				for s in [-1, 1]:
					var want := Vector3(foot.x, foot.y, s * foot.z)
					var a: Array = bw.leg_ik(s, want)
					worst = maxf(worst, (bw.leg_fk(s, a[0], a[1], a[2]) - want).length())
			check("Bein-Rechnung: Fuss dort, wo gewünscht", worst < 0.001, "%.5f m" % worst)
			# FK of the model = the physics (the read angles give the same feet)
			var fr: Array = m.fk(m.targets(), m.segment_xf(0), true)
			var dev := 0.0
			for bi in range(m.bodies.size()):
				dev = maxf(dev, ((fr[bi] as Transform3D).origin - m.frame_of(bi).origin).length())
			check("Modell-Kinematik = Physik", dev < 0.01, "%.4f m" % dev)
			# joint limits (in the air)
			lab.set_hold(true)
			lab.apply_pose("gerade")
			m.set_target("kn2l", 250.0)
			m.set_target("hp2l", -150.0)
			m.set_target("hy2r", 200.0)
			m.set_target("sp0", 150.0)
			check("Grenzen: Ziele begrenzt", is_equal_approx(float(m.servos[m.servo_index("kn2l")]["target"]), 180.0)
					and is_equal_approx(float(m.servos[m.servo_index("hp2l")]["target"]), -90.0)
					and is_equal_approx(float(m.servos[m.servo_index("sp0")]["target"]), 90.0), "")
			next_step()
		2:
			if frames() < 300:
				return false
			var ok := true
			var det := ""
			for id in ["kn2l", "hp2l", "hy2r", "sp0"]:
				var sv: Dictionary = m.servos[m.servo_index(id)]
				var a := float(sv["angle"])
				det += "%s %.0f° " % [id, a]
				if a < float(sv["min"]) - 4.0 or a > float(sv["max"]) + 4.0:
					ok = false
			check("Grenzen: Gelenke bleiben innerhalb", ok, det)
			check("Grenzen: Knie erreicht 180°", absf(float(m.servos[m.servo_index("kn2l")]["angle"]) - 180.0) < 6.0, det)
			# collision: two legs on the same side crossing
			lab.apply_pose("gerade")
			m.set_target("hy0r", -90.0)
			m.set_target("hy1r", 90.0)
			m.set_target("hp0r", 0.0)
			m.set_target("hp1r", 0.0)
			m.set_target("kn0r", 0.0)
			m.set_target("kn1r", 0.0)
			next_step()
		3:
			if frames() < 240:
				return false
			var names: Array = m.colliding_names()
			check("Kollision: gekreuzte Beine rot", names.has("ober_0_2") and names.has("ober_1_2"), str(names))
			lab.set_hold(false)
			lab.apply_pose("ring", true)
			next_step()
		4:
			if frames() < 240:
				return false
			check("Ring: Kupplung verriegelt", m.latch["state"] == "locked", "%s, %.4f m, %.1f°" % [m.latch["state"], m.latch["err_pos"], m.latch["err_ang"]])
			var ids := []
			for i in range(7):
				ids.append("sp%d" % i)
			var worst := 0.0
			for id in ids:
				worst = maxf(worst, absf(float(m.servos[m.servo_index(id)]["angle"]) - 45.0))
			check("Ring: alle Segmentgelenke 45°", worst < 4.0, "höchstens %.1f° daneben" % worst)
			next_step()
		5:
			if frames() < 360:
				return false
			var c: Vector3 = m.com()
			check("Ring: steht nach 3 s noch (kippt nicht, explodiert nicht)", sane() and m.max_speed() < 0.5 and c.y > 0.17 and c.y < 0.28 and m.latch["state"] == "locked",
					"v %.3f, Schwerpunkt %.3f m" % [m.max_speed(), c.y])
			check("Ring: keine Überlast", m.overloaded().is_empty(), str(m.overloaded()))
			# weak leg servos: they give way
			lab.apply_pose("gerade", true)
			lab.set_shape("moment_bein", 0.1)
			next_step()
		6:
			if frames() < 360:
				return false
			check("Schwache Servos: überlastet gemeldet", m.overloaded().size() >= 8, "%d überlastet" % m.overloaded().size())
			check("Schwache Servos: Körper sinkt ab", m.com().y < 0.06, "%.3f m" % m.com().y)
			lab.set_shape("moment_bein", 1.5)
			lab.set_shape("segmente", 6)
			next_step()
		7:
			if frames() < 120:
				return false
			check("Formregler: 6 Segmente, 48 Antriebe", m.n() == 6 and m.actuator_count() == 48 and m.servos.size() == 48, "%d / %d" % [m.n(), m.actuator_count()])
			check("Formregler: steht", sane(), "")
			lab.set_shape("segmente", 8)
			next_step()
		8:
			if frames() < 240:
				return false
			lab.apply_pose("gerade", true)
			lab.control({"do": "gang", "name": "welle", "drive": 1.0})
			set_meta("x0", m.segment_xf(0).origin)
			set_meta("tipmin", 99.0)
			next_step()
		9:
			if frames() > 120:
				set_meta("tipmin", minf(get_meta("tipmin"), lab.anz.margin))
			if frames() < 720:
				return false
			var dx: float = m.segment_xf(0).origin.x - (get_meta("x0") as Vector3).x
			check("Wellengang: läuft vorwärts (6 s)", dx > 0.15 and sane(), "%.3f m" % dx)
			check("Wellengang: kippt nie (Reserve > 0)", float(get_meta("tipmin")) > 0.0, "kleinste Reserve %.3f m" % get_meta("tipmin"))
			check("Anzeigen: Strom und Last gerechnet", m.total_current > 1.0 and lab.anz.top_loads(3).size() == 3, "%.1f A" % m.total_current)
			lab.stop_all()
			lab.reset()
			var g: Vector3 = m.segment_xf(0).origin + Vector3(1.0, 0.0, -0.6)
			g.y = 0.0
			set_meta("goal", g)
			lab.control({"do": "goal", "pos": [g.x, g.y, g.z]})
			next_step()
		10:
			if not lab.bew.goal_reached and frames() < 120 * 45:
				return false
			var dg: float = Vector2(m.segment_xf(0).origin.x - (get_meta("goal") as Vector3).x, m.segment_xf(0).origin.z - (get_meta("goal") as Vector3).z).length()
			check("Automatisch: Ziel links vorne erreicht", lab.bew.goal_reached and dg < 0.2, "%.1f s, %.2f m vom Ziel" % [frames() / 120.0, dg])
			lab.stop_all()
			lab.apply_pose("eingeklappt", true)
			next_step()
		11:
			if frames() < 120:
				return false
			lab.control({"do": "ablauf", "name": "aufstehen"})
			next_step()
		12:
			if frames() < 120 * 6:
				return false
			check("Ablauf Aufstehen: steht danach", m.com().y > 0.07 and lab.bew.mode == "", "Schwerpunkt %.3f m, %s" % [m.com().y, lab.bew.mode])
			lab.control({"do": "ablauf", "name": "einrollen"})
			set_meta("locked", false)
			next_step()
		13:
			if m.latch["state"] == "locked":
				set_meta("locked", true)
			if frames() < 120 * 18:
				return false
			print("  info Ablauf Einrollen: Ring %s (mit %.1f N·m je Segmentgelenk)" % ["verriegelt" if get_meta("locked") else "NICHT geschlossen", m.p["moment_koerper"]])
			check("Ablauf Einrollen und öffnen: fertig, ohne Explosion", lab.bew.mode == "" and sane(), lab.bew.mode)
			lab.stop_all()
			lab.reset()
			lab.control({"do": "ring", "drive": 0.0})
			next_step()
		14:
			if frames() < 120:
				return false
			check("Ring rollen: Ring verriegelt", m.latch["state"] == "locked", m.latch["state"])
			set_meta("c0", lab.bew.ring_state()["c"])
			lab.control({"do": "ring", "drive": 1.0})
			next_step()
		15:
			if frames() < 120 * 5:
				return false
			var c: Vector3 = lab.bew.ring_state()["c"]
			var dx: float = c.x - (get_meta("c0") as Vector3).x
			check("Ring rollen: die Füsse stossen ihn vorwärts (5 s)", dx > 0.3 and m.latch["state"] == "locked", "%.2f m" % dx)
			set_meta("c0", c)
			set_meta("leanmax", 0.0)
			lab.control({"do": "ring", "drive": 1.0, "turn": 1.0})
			next_step()
		16:
			set_meta("leanmax", maxf(get_meta("leanmax"), lab.bew.ring_lean))
			if frames() < 120 * 6:
				return false
			var c: Vector3 = lab.bew.ring_state()["c"]
			var dz: float = c.z - (get_meta("c0") as Vector3).z
			check("Ring lenken: neigt sich etwas (> 1°) und fährt links (−z)", dz < -0.2 and float(get_meta("leanmax")) > 1.0 and m.latch["state"] == "locked",
					"dz %.2f m, Neigung bis %.1f°" % [dz, get_meta("leanmax")])
			lab.stop_all()
			lab.apply_pose("gerade", true)
			lab.drive_dir(Vector3(1.0, 0.0, 0.0))
			set_meta("c0", centre())
			set_meta("h0", head())
			next_step()
		17:
			if frames() < 120 * 6:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			var dh := wrapf(head() - float(get_meta("h0")), -180.0, 180.0)
			check("Seitwärts (Krebsgang) links: ≥ 20 cm, Richtung bleibt", rel.z < -0.2 and absf(rel.x) < 0.05 and absf(dh) < 5.0, "dx %.2f dz %.2f m, %.1f°" % [rel.x, rel.z, dh])
			lab.stop_all()
			lab.reset()
			lab.drive_dir(Vector3(0.0, 0.0, 1.0))
			set_meta("c0", centre())
			set_meta("h0", head())
			next_step()
		18:
			if frames() < 120 * 12:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			var dh := wrapf(head() - float(get_meta("h0")), -180.0, 180.0)
			check("An Ort drehen (Q): ≥ 90°, bleibt am Platz", dh >= 90.0 and Vector2(rel.x, rel.z).length() < 0.12, "%.1f°, %.2f m" % [dh, Vector2(rel.x, rel.z).length()])
			lab.stop_all()
			lab.reset()
			lab.drive_dir(Vector3(-1.0, 1.0, 0.0))
			set_meta("c0", centre())
			set_meta("h0", head())
			next_step()
		19:
			if frames() < 120 * 6:
				return false
			var rel: Vector3 = centre() - (get_meta("c0") as Vector3)
			var dh := wrapf(head() - float(get_meta("h0")), -180.0, 180.0)
			check("Schräg vorne rechts (W + D): vor und seitwärts", rel.x > 0.15 and rel.z > 0.15 and absf(dh) < 5.0, "dx %.2f dz %.2f m, %.1f°" % [rel.x, rel.z, dh])
			lab.stop_all()
			lab.reset()
			var g: Vector3 = centre() - Vector3(1.0, 0.0, 0.0)
			g.y = 0.0
			set_meta("goal", g)
			set_meta("spun", false)
			lab.control({"do": "goal", "pos": [g.x, g.y, g.z]})
			next_step()
		20:
			if lab.bew.plan == "drehen":
				set_meta("spun", true)
			if not lab.bew.goal_reached and frames() < 120 * 70:
				return false
			check("Ziel hinten: dreht zuerst an Ort, kommt an", lab.bew.goal_reached and bool(get_meta("spun")), "%.1f s, gedreht %s" % [frames() / 120.0, get_meta("spun")])
			lab.stop_all()
			lab.bew.tempo = 0.12
			lab.bew.anpassen = true
			lab.control({"do": "gelaende", "name": "stufe"})
			set_meta("cnt", 0)
			set_meta("bad", 0)
			set_meta("tip", false)
			next_step()
		21, 22:
			if frames() > 240:
				sample_clearance()
			var lane := "stufe" if step == 21 else "rampe"
			if not lab.terrain.is_empty() and frames() < 120 * 90:
				return false
			var r: Array = lab.terrain_results.get(lane, [false, "kein Ergebnis"])
			var cnt: int = get_meta("cnt")
			var bad: int = get_meta("bad")
			check("Untergrund anpassen: %s geschafft, nicht gekippt" % lane, bool(r[0]) and not bool(get_meta("tip")), str(r[1]))
			check("Untergrund anpassen: %s Bodenabstand je Segment 0.5 … 15 cm (98 %%)" % lane, cnt > 100 and bad <= cnt * 0.02,
					"%d von %d ausserhalb" % [bad, cnt])
			if step == 21:
				lab.control({"do": "gelaende", "name": "rampe"})
				set_meta("cnt", 0)
				set_meta("bad", 0)
				next_step()
			else:
				check("Keine Explosion im ganzen Test", vmax_all < 5.0, "%.2f m/s" % vmax_all)
				main.roboter.control({"do": "close"})
				next_step()
		23:
			if frames() < 10:
				return false
			check("Geschlossen: Physik wieder wie vorher", Engine.physics_ticks_per_second == 30 and not main.roboter.is_open(), str(Engine.physics_ticks_per_second))
			RS.klein_test = true                                 # phone-sized: the hint, the panel closed, the button «Bedienfeld»
			RS.oeffnen(main)
			var d: Dictionary = main.control({"action": "roboter", "do": "info"})
			var lw = main.roboter
			var hint: Node = lw.layer.find_child("hinweis_pc", true, false)
			var pb: Button = lw.layer.find_child("bedienfeld_knopf", true, false)
			check("Handy: Hinweis «Am besten am PC», Bedienfeld zu, Labor trotzdem offen", bool(d.get("open")) and hint != null
					and not (lw._w["panel"] as Control).visible and int(d.get("segments", 0)) == 8)
			if pb != null:
				pb.pressed.emit()
			check("Handy: Knopf «Bedienfeld» öffnet das Bedienfeld", pb != null and (lw._w["panel"] as Control).visible)
			if hint != null:
				(hint.find_child("ok", true, false) as Button).pressed.emit()
			next_step()
		24:
			if frames() < 10:
				return false
			check("Handy: «OK» schliesst den Hinweis", main.roboter.layer.find_child("hinweis_pc", true, false) == null)
			main.roboter.control({"do": "close"})
			RS.klein_test = null
			return _end()
	return false


func _end() -> bool:
	if errs.is_empty():
		print("Robotertest OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Robotertest: " + " | ".join(errs))
		quit(1)
	return true
