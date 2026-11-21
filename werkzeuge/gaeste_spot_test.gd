extends SceneTree
## Test «Scheinwerfer kippt mit» + «Gäste besuchen das Zelt» (gaeste-licht, MoveEye 639zzzzl / Simulator gehaeuse.gd, gaeste.gd) -
## ohne Bild, ohne Welt, ohne Modelle (Ersatz-Teile mit den Namen aus modelle.json):
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/gaeste_spot_test.gd"   (absoluter Pfad nötig)
## 1. Die Lampen am Drehteller (lamp1 / lamp2 / lens_w / lens_ir) hängen nach lamp_pivot an einem eigenen Drehpunkt - an derselben
##    Stelle wie vorher (alle Sätze: fein, grob, Schatten); andere Teile bleiben am Drehteller.
## 2. Kippt der Kopf (head_pitch), kippt der Scheinwerfer gleich (lamp_follow): Richtung der Linse und des Lichts (SpotLight3D in
##    der Linse, light_to) zeigt nach unten / oben wie die Kamera, beim Schwenken auch zur Seite. Ohne Gehäuse: das Licht am
##    head_pitch kippt ebenso (wie bisher).
## 3. gaeste.gd: MoveEye-Meter <-> Szene (gedrehtes, verschobenes Gerät) hin und zurück; Ziel «Punkt» von MoveEye, «Zelt» und ohne
##    Ziel = das eigene Zelt; von selbst nur, wenn MoveEye «Gäste erwartet» meldet.
## Ende: «Gäste-Spot-Test OK» oder «SCRIPT ERROR: Gäste-Spot-Test: …».

var errs := []


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)


func _part(parent: Node3D, nm: String, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.02, 0.02, 0.02)
	mi.mesh = bm
	mi.name = nm
	mi.position = pos
	parent.add_child(mi)
	return mi


func _dir(n: Node3D) -> Vector3:
	return -n.global_transform.basis.z.normalized()


func _fake_main() -> Node:
	var s := GDScript.new()
	s.source_code = """extends Node
var t := 100.0
var mw := {}
var mw_t := 0.0
var rig: Node3D
var obj := {"pir": Vector3(10, 0, -4)}
var gaeste_auto := true
var sim_active := true
var start_info := ""
var busy := ""
func now() -> float:
	return t
func ground_y(_x: float, _z: float) -> float:
	return 0.0
func busy_with(_e := "") -> String:
	return busy
func measuring() -> bool:
	return false
"""
	s.reload()
	var m := Node.new()
	m.set_script(s)
	return m


func _initialize() -> void:
	var G = load("res://scripts/gehaeuse.gd")
	# ---- 1. the lamp pivot -----------------------------------------------------------------------------------------------------------
	var rig := Node3D.new()
	root.add_child(rig)
	var head := Node3D.new()
	head.position = Vector3(0, 1.6, 0)
	rig.add_child(head)
	var pitch := Node3D.new()
	head.add_child(pitch)
	var pan := Node3D.new()
	head.add_child(pan)
	var l1 := _part(pan, "geh_lamp1", Vector3(0.05, 0.02, -0.03))
	var lw := _part(pan, "geh_lens_w", Vector3(0.05, 0.02, -0.05))
	var lw2 := _part(pan, "geh_lens_w_lod", Vector3(0.05, 0.02, -0.05))
	var lir := _part(pan, "geh_lens_ir", Vector3(-0.05, 0.02, -0.05))
	var _l2 := _part(pan, "geh_lamp2_schatten", Vector3(-0.05, 0.02, -0.03))
	var yoke := _part(pan, "geh_yoke", Vector3(0, -0.02, 0))
	var before := {}
	for n in [l1, lw, lw2, lir]:
		before[n] = n.global_position
	var pv: Node3D = G.lamp_pivot(pan)
	ok("lamp_pivot gives a pivot", pv != null)
	if pv == null:
		_end()
		return
	ok("lamps hang at the pivot", l1.get_parent() == pv and lw.get_parent() == pv and lw2.get_parent() == pv and lir.get_parent() == pv)
	ok("other parts stay at the turntable", yoke.get_parent() == pan)
	for n in before:
		ok("%s stays where it was" % n.name, n.global_position.distance_to(before[n]) < 1e-5)
	ok("lens meta", pv.has_meta("lens_w") and pv.has_meta("lens_ir"))
	ok("no lamps: no pivot", G.lamp_pivot(Node3D.new()) == null)
	# ---- 2. the spot follows the tilt (and the pan) ----------------------------------------------------------------------------------
	var white := SpotLight3D.new()
	pitch.add_child(white)
	G.light_to(white, pv, pv.get_meta("lens_w"))
	ok("the light sits in the white lens", white.get_parent() == pv and white.global_position.distance_to(lw.global_position) < 0.002)
	for deg in [-25.0, -6.0, 0.0, 15.0]:
		pitch.rotation.x = deg_to_rad(deg)
		G.lamp_follow(pv, pitch)
		var want := sin(deg_to_rad(deg))
		ok("tilt %.0f°: lens points %.3f (wants %.3f)" % [deg, _dir(lw).y, want], absf(_dir(lw).y - want) < 1e-4)
		ok("tilt %.0f°: light points %.3f (wants %.3f)" % [deg, _dir(white).y, want], absf(_dir(white).y - want) < 1e-4)
		ok("tilt %.0f°: light = camera axis" % deg, _dir(white).distance_to(_dir(pitch)) < 1e-4)
	head.rotation.y = deg_to_rad(-30.0)                         # pan 30° to the right (main.gd: rotation.y = -pan)
	pitch.rotation.x = deg_to_rad(-20.0)
	G.lamp_follow(pv, pitch)
	var d := _dir(white)
	ok("pan + tilt: right and down (%s)" % d, d.x > 0.4 and d.y < -0.3 and d.distance_to(_dir(pitch)) < 1e-4)
	var old := SpotLight3D.new()                                # without the case: the light stays at head_pitch (as before)
	pitch.add_child(old)
	ok("without the case: the light at head_pitch tilts too", _dir(old).distance_to(_dir(pitch)) < 1e-4 and _dir(old).y < -0.3)
	# ---- 3. gaeste.gd ------------------------------------------------------------------------------------------------------------------
	var m := _fake_main()
	root.add_child(m)
	var mr := Node3D.new()
	root.add_child(mr)
	mr.position = Vector3(3, 0, -2)
	mr.rotation.y = deg_to_rad(40.0)
	m.rig = mr
	var g = load("res://scripts/gaeste.gd").new()
	g.main = m
	var w: Vector3 = g.to_world(2.0, 8.0)
	var back: Array = g.to_mw(w)
	ok("MoveEye metres -> scene -> back (%s)" % [back], absf(float(back[0]) - 2.0) < 0.01 and absf(float(back[1]) - 8.0) < 0.01)
	ok("8 m away from the device", Vector2(w.x - 3.0, w.z + 2.0).length() > 8.2 and Vector2(w.x - 3.0, w.z + 2.0).length() < 8.3)
	ok("no MoveEye: the own tent", g.target_world() == m.obj["pir"] and not g.mw_on())
	m.mw = {"guests": {"on": true, "target": {"kind": "point", "x": 2.0, "y": 8.0}}}
	m.mw_t = m.t
	ok("MoveEye «guests expected»: on", g.mw_on())
	ok("target point of MoveEye", g.target_world().distance_to(w) < 0.01)
	m.mw = {"guests": {"on": true, "target": {"kind": "tent", "x": 2.0, "y": 8.0}}}
	ok("target tent: the tent of the scene", g.target_world() == m.obj["pir"])
	m.mw_t = m.t - 30.0
	ok("old state (no connection): not on", not g.mw_on())
	var inf: Dictionary = g.info()
	ok("info: tent in MoveEye metres", inf.has("tent_mw") and (inf["tent_mw"] as Array).size() == 2)
	_end()


func _end() -> void:
	if errs.is_empty():
		print("Gäste-Spot-Test OK")
	else:
		push_error("Gäste-Spot-Test: " + " | ".join(errs))
		print("SCRIPT ERROR: Gäste-Spot-Test: " + " | ".join(errs))
	quit(0 if errs.is_empty() else 1)
