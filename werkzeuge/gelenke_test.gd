extends SceneTree
## Test «Gelenke» (actor.gd): Figuren aus Grundformen (Grafik «einfach», wie auf dem Pi und in den Erkennungstests) gehen
## und rennen an Ort; gemessen wird, ob die Füsse / Pfoten am Boden bleiben (nicht einsinken, nicht schweben), wie stark
## Knie und Ellbogen beugen und wie viele Teile eine Figur hat. Ohne Bild.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/gelenke_test.gd"   (absoluter Pfad nötig)
##   GELENKE_LITE=1 davor: dasselbe in der Grafik-Stufe Lite
## Ende: «Gelenketest OK» oder «SCRIPT ERROR: Gelenketest: …» (Exit-Code 0 / 1).

const CASES := [
	# [Art, Tempo m/s, Haltung (0 stehen, 1 geduckt), Name]
	["person", 0.0, 0, "Mensch steht"], ["person", 1.3, 0, "Mensch geht"], ["person", 3.6, 0, "Mensch rennt"],
	["child", 1.0, 0, "Kind geht"], ["person", 0.6, 1, "Mensch geduckt"], ["jogger", 3.0, 0, "Jogger"],
	["elderly", 0.9, 0, "Seniorin"],
	["deer", 1.2, 0, "Reh geht"], ["deer", 2.6, 0, "Reh trabt"], ["fox", 1.5, 0, "Fuchs"], ["dog", 1.6, 0, "Hund"],
	["cow", 1.0, 0, "Kuh"], ["boar", 1.2, 0, "Wildschwein"], ["horse", 1.4, 0, "Pferd"], ["wolf", 1.8, 0, "Wolf"],
]
var main
var t0 := 0.0
var step := 0
var vs := []
var stat := []
var frames := 0
var errs := []


func _initialize() -> void:
	var F = load("res://scripts/figur.gd")
	F.mode = "neu" if OS.get_environment("GELENKE_FIGUR") == "neu" else "alt"   # shapes (Grafik «einfach»); neu = skinned figure (only no errors)
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main


func _low_person(v) -> float:
	var low := 99.0
	for a in v.ankles:
		for p in [Vector3(0, -0.06, -0.2), Vector3(0, -0.06, 0.08), Vector3(0, -0.06, -0.06)]:
			low = minf(low, ((a as Node3D).global_transform * p).y)
	return low


func _low_animal(v) -> float:
	var low := 99.0
	for e in v._paws:
		var pt: Vector3 = e[2]
		if e[1] != null:
			pt = (e[1] as Node3D).transform * pt
		low = minf(low, ((e[0] as Node3D).global_transform * pt).y - float(e[3]) * v.body_root.scale.y)
	return low


func _count(n: Node) -> int:
	var c := 1 if n is MeshInstance3D and (n as MeshInstance3D).layers == 1 else 0
	for ch in n.get_children():
		c += _count(ch)
	return c


func _process(_dt: float) -> bool:
	var t := Time.get_ticks_msec() / 1000.0
	if step == 0:
		t0 = t
		step = 1
	elif step == 1 and t - t0 > 12.0:
		main.eco_idle = false                          # keeps running without a window
		main.auto_visitors = false
		if OS.get_environment("GELENKE_LITE") == "1":   # Lite: fewer joint balls
			load("res://scripts/quality.gd").set_lite(true)
		for v in main.visitors.get_children():
			v.queue_free()
		for i in range(CASES.size()):
			var c: Array = CASES[i]
			var p := Vector3(-14.0 + i * 2.0, 0, -12.0) if i < 7 else Vector3(-40.0 + (i - 7) * 12.0, 0, -70.0)   # animals far apart (no fleeing)
			var v = main.spawn(str(c[0]), p, p + Vector3(0, 0, -40.0))
			v.set_process(true)
			v.demo = float(c[1])
			v.next_idle = v.now_s() + 9999.0
			v.idle_until = 0.0
			if v.kind != "person":                     # tiere.gd leaves puppets alone (no fleeing, no jumps)
				v.puppet = true
				v.cur_speed = float(c[1])
			if int(c[2]) == 1:
				v.crouch = 1.0
			vs.append(v)
			stat.append({"min": 99.0, "max": -99.0, "knee": 0.0, "elbow": 0.0, "parts": _count(v)})
		step = 2
		t0 = t
	elif step == 2:
		frames += 1
		if t - t0 > 1.5:                               # after the start
			for i in range(vs.size()):
				var v = vs[i]
				if not is_instance_valid(v):
					continue
				var gy: float = v.global_position.y
				var low: float = (_low_person(v) if v.kind == "person" else _low_animal(v)) - gy
				var s: Dictionary = stat[i]
				s["min"] = minf(s["min"], low)
				s["max"] = maxf(s["max"], low)
				for l in v.legs:
					if l.size() > 2 and l[2] != null:
						s["knee"] = maxf(s["knee"], absf((l[2] as Node3D).rotation.x))
				for a in v.arms:
					s["elbow"] = maxf(s["elbow"], absf((a[2] as Node3D).rotation.x))
		if t - t0 > 7.5:
			for i in range(CASES.size()):
				var c: Array = CASES[i]
				var s: Dictionary = stat[i]
				print("%-16s Fuss tiefster %+.3f … %+.3f m   Knie max %.2f   Ellbogen max %.2f   Teile %d" % [c[3], s["min"], s["max"], s["knee"], s["elbow"], s["parts"]])
				# the lowest foot / paw: never deeper than 2.5 cm in the ground, never higher than 3 cm (running: flight 11 cm)
				var fly: float = 0.11 if float(c[1]) > 2.5 and str(c[0]) in ["person", "jogger"] else 0.03
				if s["min"] > 50.0:
					continue                                   # GELENKE_FIGUR=neu: the skinned figure has no ankles here
				if s["min"] < -0.025:
					errs.append("%s: Fuss %.3f m im Boden" % [c[3], s["min"]])
				if s["max"] > fly:
					errs.append("%s: Fuss schwebt %.3f m" % [c[3], s["max"]])
				if str(c[0]) in ["person", "child", "elderly"] and float(c[1]) >= 1.0 and s["knee"] < 0.75:
					errs.append("%s: Knie beugt nur %.2f" % [c[3], s["knee"]])
			print("Bilder: %d" % frames)
			if errs.is_empty():
				print("Gelenketest OK")
				quit(0)
			else:
				for e in errs:
					printerr("SCRIPT ERROR: Gelenketest: " + e)
				quit(1)
			return true
	return false
