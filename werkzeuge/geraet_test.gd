extends SceneTree
## Test «Echtes Gerät» (sim-echte-kamera, Idee 4): das Gerät in der Szene ist das echte Gehäuse v5.x (gehaeuse.gd) und folgt den
## Servo-Befehlen von MoveEye (Zustand «servo»: pan_deg / tilt_deg) sichtbar: Drehteller + Gabel drehen (Pan), der Kopf kippt
## (Tilt). Dazu: Linse Weisslicht leuchtet, IR-Lampe glimmt nur schwach, Sichtweiten (LOD), Weitwinkel-Modul am Kopf,
## Gerät 2 (device.gd) mit dem echten Gehäuse statt des roten Kastens. Ohne Bild.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/geraet_test.gd"   (absoluter Pfad nötig)
## Ende: «Geraetetest OK» oder «SCRIPT ERROR: Geraetetest: …» (Exit-Code 0 / 1).

var main
var t0 := 0.0
var step := 0
var errs := []
var phase_t := 0.0


func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main


func _find(n: Node, nm: String) -> Node:
	if str(n.name) == nm:
		return n
	for c in n.get_children():
		var r := _find(c, nm)
		if r != null:
			return r
	return null


func _yaw_pitch(n: Node3D, rig: Node3D) -> Vector2:
	"""Pan (Grad, um die Hochachse) und Tilt (Grad) eines Teils relativ zum Gestell"""
	var b: Basis = rig.global_transform.basis.orthonormalized().inverse() * n.global_transform.basis.orthonormalized()
	var e := b.get_euler(EULER_ORDER_YXZ)
	return Vector2(rad_to_deg(e.y), rad_to_deg(e.x))


func _check(ok: bool, what: String) -> void:
	print(("  ok   " if ok else "  FEHLER ") + what)
	if not ok:
		errs.append(what)


func _cmd(pan: float, tilt: float, white := false, ir := false) -> void:
	main.mw = {"servo": {"pan_deg": pan, "tilt_deg": tilt, "moving": false}, "lights": {"white": white, "ir": ir}, "sound": "", "armed": false, "device": ""}
	main.mw_t = main.now()


func _process(_dt: float) -> bool:
	var t := Time.get_ticks_msec() / 1000.0
	if step == 0:
		t0 = t
		step = 1
		return false
	if step == 1 and t - t0 > 10.0:
		main.eco_idle = false
		main.auto_visitors = false
		if main.patrol != null:
			main.patrol.active = false
		var gh = main.gehaeuse
		_check(gh != null and gh.ok and gh.on, "echtes Gehäuse geladen (%s)" % (str(gh.info()) if gh != null else "-"))
		if gh == null or not gh.ok:
			return _end()
		_check(main.head_box != null and not main.head_box.visible, "Platzhalter-Kasten ausgeblendet")
		_check(gh.lod or gh.lite, "Sichtweiten: fein bis %.0f m, dahinter grob (lod %s, lite %s)" % [gh.LOD_M, gh.lod, gh.lite])
		_cmd(40.0, 10.0, true, false)
		phase_t = t
		step = 2
	elif step == 2 and t - phase_t > 2.5:
		_measure(40.0, 10.0)
		var g: Dictionary = main.gehaeuse.lists.get("glow", {})
		var wl: StandardMaterial3D = g.get("lens_w")
		var il: StandardMaterial3D = g.get("lens_ir")
		_check(wl != null and wl.emission_energy_multiplier > 1.0, "Weisslicht an: Linse leuchtet (%.2f)" % (wl.emission_energy_multiplier if wl != null else -1.0))
		_check(il != null and il.emission_energy_multiplier == 0.0, "IR aus: IR-Linse dunkel")
		_cmd(-40.0, -15.0, false, true)
		phase_t = t
		step = 3
	elif step == 3 and t - phase_t > 2.5:
		_measure(-40.0, -15.0)
		var g: Dictionary = main.gehaeuse.lists.get("glow", {})
		var wl: StandardMaterial3D = g.get("lens_w")
		var il: StandardMaterial3D = g.get("lens_ir")
		_check(wl != null and wl.emission_energy_multiplier == 0.0, "Weisslicht aus: Linse dunkel")
		_check(il != null and il.emission_energy_multiplier > 0.0 and il.emission_energy_multiplier < 1.0, "IR an: schwaches Glimmen (%.2f)" % (il.emission_energy_multiplier if il != null else -1.0))
		var old_mount: String = main.weit.mount
		main.weit.mount = "head_front"                   # direkt (nicht speichern)
		main.set_meta("geraet_test_mount", old_mount)
		phase_t = t
		step = 4
	elif step == 4 and t - phase_t > 0.5:
		var gh = main.gehaeuse
		_check(gh.wmod != null and gh.wmod.visible, "Weitwinkel «Kopf vorne»: Modul auf dem Kopf zu sehen")
		if gh.wmod != null:
			var want: Vector3 = main.head.global_transform * gh.WMOD_FRONT
			var d: float = main.cams[1].global_position.distance_to(want)
			_check(d < 0.02, "Weitwinkel-Kamera sitzt am Modul (%.3f m)" % d)
		main.weit.mount = str(main.get_meta("geraet_test_mount"))
		phase_t = t
		step = 5
	elif step == 5 and t - phase_t > 0.5:
		var gh = main.gehaeuse
		_check(gh.wmod == null or not gh.wmod.visible, "Weitwinkel zurück: kein Modul am Kopf")
		var r: Dictionary = main.control({"action": "werkstatt", "do": "v53", "on": false})   # Bauen: v5.2 wählen
		var t53: Node3D = _find(main.rig, "geh_tub53")
		var t52: Node3D = _find(main.rig, "geh_tub52")
		_check(t53 != null and t52 != null and not t53.visible and t52.visible, "Bauen → v5.2: Unterteil v5.2 zu sehen (%s)" % str(r).left(60))
		main.control({"action": "werkstatt", "do": "v53", "on": true})
		_check(t53 != null and t52 != null and t53.visible and not t52.visible, "Bauen → v5.3: Unterteil v5.3 zu sehen")
		var lod_n := 0
		for n in [_find(main.rig, "geh_tub53_lod"), _find(main.rig, "geh_tub53_schatten")]:
			if n != null and (n as Node3D).visible == t53.visible:
				lod_n += 1
		_check(lod_n == 2 or main.gehaeuse.lite, "grobe Teile (Ferne, Schatten) folgen der Wahl")
		main.dev2.set_on(true)
		phase_t = t
		step = 6
	elif step == 6 and t - phase_t > 1.0:
		var d2 = main.dev2
		_check(bool(d2.case.get("ok", false)), "Gerät 2: echtes Gehäuse statt rotem Kasten")
		d2.on_state({"servo": {"pan_deg": 30.0, "tilt_deg": 5.0}, "lights": {"white": false, "ir": true}, "led": {"rgb": "#00ff00", "br": 1.0}}, "")
		phase_t = t
		step = 7
	elif step == 7 and t - phase_t > 2.0:
		var d2 = main.dev2
		if bool(d2.case.get("ok", false)):
			var yoke: Node3D = _find(d2.rig, "geh_yoke")
			var hd: Node3D = _find(d2.rig, "geh_head52")
			if hd == null:
				hd = _find(d2.rig, "geh_head")
			_check(yoke != null and hd != null, "Gerät 2: Gabel und Kopf gefunden")
			if yoke != null and hd != null:
				var yp := _yaw_pitch(yoke, d2.rig)
				var hp := _yaw_pitch(hd, d2.rig)
				_check(absf(yp.x + 30.0) < 2.0, "Gerät 2 Pan 30°: Gabel %.1f°" % -yp.x)
				_check(absf(hp.y - (5.0 - 6.0)) < 2.0, "Gerät 2 Tilt 5°: Kopf %.1f° (Sim-Versatz −6°)" % hp.y)
			var il: StandardMaterial3D = (d2.case["lists"] as Dictionary).get("glow", {}).get("lens_ir")
			_check(il != null and il.emission_energy_multiplier > 0.0, "Gerät 2: IR glimmt")
			_check(d2.led_mat != null and d2.led_mat.emission.g > 0.9, "Gerät 2: Status-LED grün")
		main.dev2.set_on(false)
		return _end()
	return false


func _measure(pan: float, tilt: float) -> void:
	var rig: Node3D = main.rig
	var yoke: Node3D = _find(rig, "geh_yoke")
	var tt: Node3D = _find(rig, "geh_turntable")
	var hd: Node3D = _find(rig, "geh_head52")
	var base: Node3D = _find(rig, "geh_tub53")
	if base == null:
		base = _find(rig, "geh_tub52")
	_check(yoke != null and tt != null and hd != null and base != null, "Teile gefunden (Gabel, Drehteller, Kopf, Unterteil)")
	if yoke == null or tt == null or hd == null or base == null:
		return
	var yp := _yaw_pitch(yoke, rig)
	var tp := _yaw_pitch(tt, rig)
	var hp := _yaw_pitch(hd, rig)
	var bp := _yaw_pitch(base, rig)
	# Sim: Pan +° = nach rechts = Drehung −° um die Hochachse; Tilt: Kopf = tilt − 6° (Versatz der Kopfkamera, main.gd)
	_check(absf(yp.x + pan) < 1.5 and absf(tp.x + pan) < 1.5, "Pan %+.0f°: Gabel %+.1f°, Drehteller %+.1f°" % [pan, -yp.x, -tp.x])
	_check(absf(hp.x + pan) < 1.5 and absf(hp.y - (tilt - 6.0)) < 1.5, "Tilt %+.0f°: Kopf kippt %+.1f° (Soll %+.1f°)" % [tilt, hp.y, tilt - 6.0])
	_check(absf(yp.y) < 0.5, "Gabel kippt nicht mit (%.2f°)" % yp.y)
	_check(absf(bp.x) < 0.5 and absf(bp.y) < 0.5, "Unterteil bleibt stehen")
	var cam_fw: Vector3 = -main.cams[0].global_transform.basis.z
	var head_fw: Vector3 = -hd.global_transform.basis.z
	_check(cam_fw.angle_to(head_fw) < deg_to_rad(2.0), "Kopfkamera schaut wohin der Kopf schaut (%.1f°)" % rad_to_deg(cam_fw.angle_to(head_fw)))


func _end() -> bool:
	if errs.is_empty():
		print("Geraetetest OK")
		quit(0)
	else:
		for e in errs:
			printerr("SCRIPT ERROR: Geraetetest: " + str(e))
		quit(1)
	return true
