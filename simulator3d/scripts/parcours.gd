extends Node
## 3D-4.18 (Entwurf; Plan Daniel 30.10.2026, docs/Verfolgungs_Parcours.md): «Verfolgungs-Parcours» - the following mode of
## MoveEye (Folgen, head of 410) is trained, tuned and measured. The simulator knows where every figure really is: exact
## ground truth.
##   * Scene «parcours» (scenes.gd calls build_scene): open meadow, distance marks 5 / 10 / 20 / 40 m, obstacles (bush, tent,
##     car, tree) for occlusions, optional ring round the device.
##   * Lessons 1-7 with fixed paths (fixed seeds, the figures are actors of actor.gd as puppets - the same figures as the
##     visitors, no second figure system) and lesson 8 = the chosen lessons again at night with infrared.
##   * Ground truth per lesson: aim error (degrees, target centre vs. centre of the head camera), time in the picture (%),
##     losses + time to find again, overshoot / swinging, servo travel, identity switches (two persons) -> grade (Swiss
##     school grade 1-6) and result card. Live overlay (only for the operator): planned and real path of the figure, the aim
##     ray of the head (laser.gd), the error curve.
##   * Game «Entkomme der Kamera»: one player steers a figure (control API, MoveEye's mover stick, the stick of the window)
##     and tries to get out of the picture; points go into the ranking of the evening (game.board_add_extra).
##   * Learning pictures: moving / far figures as picture data only (JPEG + box, distance, speed, blur - no map data),
##     dataset.gd puts them into the training pack (add_to_pack).
## Realism: during a run «Servos wie echt» is on (MG90S speed SERVO_DEG_S, play, swinging after a stop); the head mounts of
## the wide camera keep their pan limit (weitwinkel.gd), MoveEye keeps its own 180° range; the pictures come with the
## delay of simreal.gd.
## Control API: {"action": "parcours", "do": info | start | stop | state | result | overlay | ring | pics | game | steer | game_stop}

const FILE := "user://parcours.json"
const PICS_DIR := "user://parcours/lernbilder"
const NAMES := {1: "Langsam quer durchs Bild", 2: "Auf die Kamera zu / weg", 3: "Zickzack und Tempowechsel", 4: "Stopp und Weiterlaufen",
		5: "Verdeckung hinter Hindernissen", 6: "Zwei Personen kreuzen sich", 7: "Tier: Fuchs / Reh, schnell und unregelmässig", 8: "Nacht-Durchgang mit Infrarot"}
const ICONS := {1: "🚶", 2: "↕", 3: "〰", 4: "⏸", 5: "🌳", 6: "👥", 7: "🦊", 8: "🌙"}
const STEP := 0.05                 # metrics 20 × per second
const LOSS_MIN := 0.3              # out of the picture at least this long = a loss
const MAX_PICS := 40               # learning pictures per run

var main
var running := false
var run := {}                      # {"lessons": [ids], "night": bool, "seed": int, "i": index, "phase": prep | go | gap, "t": phase start, ...}
var report := {}                   # the last finished run (also for MoveEye)
var cur := {}                      # the lesson that runs now: figures, timeline, metrics
var overlay := true                # live overlay in the window (saved)
var ring := false                  # the ring round the device (saved)
var pics_on := true                # learning pictures (saved)
var pics_n := 0
var _acc := 0.0
var _saved := {}                   # what a run changed (hour, infrared, real servos, laser)
var _lay: CanvasLayer
var _draw: Control
var _card: PanelContainer
var _card_box: VBoxContainer
var _path_mi: MeshInstance3D
var _trail_mi: MeshInstance3D
var _mat_plan: StandardMaterial3D
var _mat_trail: StandardMaterial3D
var _frame_seen := -1
var game := {}                     # «Entkomme der Kamera»: {"on", "name", "t0", "secs", "actor", "score", ...}
var steer := Vector2.ZERO          # the player (control API: device coordinates x right, z away from the device)
var steer_t := -100.0
var steer_run := false


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		overlay = bool(d.get("overlay", true))
		ring = bool(d.get("ring", false))
		pics_on = bool(d.get("pics", true))
		if typeof(d.get("report")) == TYPE_DICTIONARY:
			report = d["report"]
	_lay = CanvasLayer.new()
	_lay.layer = 4
	add_child(_lay)
	_draw = Control.new()
	_draw.set_anchors_preset(Control.PRESET_FULL_RECT)
	_draw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_draw.draw.connect(_paint)
	_lay.add_child(_draw)
	_mat_plan = _line_mat(Color(0.35, 0.75, 1.0, 0.9))
	_mat_trail = _line_mat(Color(1.0, 0.95, 0.3, 1.0))
	_path_mi = MeshInstance3D.new()
	_path_mi.mesh = ImmediateMesh.new()
	_trail_mi = MeshInstance3D.new()
	_trail_mi.mesh = ImmediateMesh.new()
	for mi in [_path_mi, _trail_mi]:
		mi.layers = main.HELPER_LAYER                     # only for the operator - the cameras of MoveEye never see it
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"overlay": overlay, "ring": ring, "pics": pics_on, "report": report}))
		f.close()


func _line_mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = c
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.no_depth_test = true
	return m


func overlay_on() -> bool:
	"""laser.gd: the aim ray of the head is part of the overlay while a lesson or the game runs"""
	return overlay and (running or bool(game.get("on", false)))


# ---- the scene -----------------------------------------------------------------------------------------------------
func build_scene(sc) -> void:
	"""scenes.gd «parcours»: open meadow, distance marks, bush, tent, car, tree, optional ring (fixed sizes - the lessons
	need exactly these occlusions)"""
	var root: Node3D = sc.root
	var white := Color(0.92, 0.92, 0.88)
	for d in [5.0, 10.0, 20.0, 40.0]:                        # painted arcs ±60° and a sign at the left end
		var n := int(d * 0.6) + 8
		for k in range(n):
			var a0 := -60.0 + 120.0 * k / n
			var a1 := -60.0 + 120.0 * (k + 0.55) / n
			var p0: Vector3 = _dev(sin(deg_to_rad(a0)) * d, cos(deg_to_rad(a0)) * d)
			var p1: Vector3 = _dev(sin(deg_to_rad(a1)) * d, cos(deg_to_rad(a1)) * d)
			var mid := (p0 + p1) / 2.0
			var seg: MeshInstance3D = sc.put(root, main.box(0.12, 0.02, p0.distance_to(p1)), mid + Vector3(0, 0.012, 0), white, "stone")
			seg.look_at(p1 + Vector3(0, 0.012, 0), Vector3.UP)
		var sp: Vector3 = _dev(-sin(deg_to_rad(64.0)) * d, cos(deg_to_rad(64.0)) * d)
		var sign_: Node3D = sc.node(root, sp, 0.0)
		sc.put(sign_, sc.cyl(0.04, 0.04, 1.0, 6), Vector3(0, 0.5, 0), Color(0.3, 0.3, 0.32), "stone")
		sc.put(sign_, main.box(0.7, 0.4, 0.04), Vector3(0, 1.1, 0), white, "stone")
		var lb: Label3D = sc.label(sign_, "%d m" % int(d), Vector3(0, 1.1, 0.03), 64)
		lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	# the bush (big, 2 m), the family tent (2.2 m), the car, a big tree - lesson 5 walks behind bush and tent
	var bp: Vector3 = _dev(-5.0, 12.0)
	var bush: Node3D = sc.node(root, bp, 0.0)
	var fm = sc.foliage(2)
	for o in [Vector3(0, 0.9, 0), Vector3(-0.6, 0.7, 0.2), Vector3(0.6, 0.75, -0.2), Vector3(0.1, 1.4, 0.1), Vector3(-0.3, 1.2, -0.4)]:
		sc.put(bush, sc.sph(0.85, 1.5), o, fm, "tree")
	main.add_obstacle(bp, 1.25)
	main.set_obstacle_height(2.0)
	var tent: Node3D = sc.node(root, _dev(6.0, 15.0), 0.0)
	var tm := PrismMesh.new()
	tm.size = Vector3(3.2, 2.2, 3.0)
	sc.put(tent, tm, Vector3(0, 1.1, 0), Color(0.2, 0.42, 0.62), "tent")
	main.add_obstacle_node(tent, Vector3.ZERO, 3.2, 3.0)
	main.set_obstacle_height(2.2)
	sc.static_car(_dev(-9.0, 22.0), PI / 2, Color(0.75, 0.1, 0.1))
	sc.tree(root, _dev(10.0, 26.0), 1.6, 0)
	if ring:                                                  # posts and a rope 8 m round the device
		var rp := 24
		for k in range(rp):
			var a := TAU * k / rp
			var p: Vector3 = _dev(sin(a) * 8.0, cos(a) * 8.0)
			sc.put(root, sc.cyl(0.04, 0.05, 0.8, 6), p + Vector3(0, 0.4, 0), Color(0.85, 0.55, 0.15), "stone")
			var q: Vector3 = _dev(sin(a + TAU / rp) * 8.0, cos(a + TAU / rp) * 8.0)
			var rope: MeshInstance3D = sc.put(root, main.box(0.03, 0.03, p.distance_to(q)), (p + q) / 2.0 + Vector3(0, 0.7, 0), Color(0.95, 0.8, 0.2), "stone")
			rope.look_at(q + Vector3(0, 0.7, 0), Vector3.UP)
	# every scene needs a door (sensor), the tent (PIR) and the bike - far behind, out of the lessons
	var h: Node3D = sc.node(root, _dev(0.0, -30.0), PI)
	main.door_node = sc.node(h, Vector3(0, 0, 0))
	sc.put(main.door_node, main.box(1.0, 2.1, 0.06), Vector3(0.5, 1.05, 0), Color(0.35, 0.2, 0.12), "caravan")
	sc.door_light_at(h, Vector3(0.0, 2.5, 0.6))
	sc.put(h, main.box(0.8, 0.5, 0.05), Vector3(1.6, 1.5, 0), sc.window_mat(), "window")   # (main needs a window material)
	main.obj["door"] = _dev(0.0, -29.0)
	main.obj["pir"] = _dev(6.0, 13.0)
	main.obj["bike"] = _dev(-3.0, -4.0)
	sc.meadow(500, 3.0, 50.0)
	for i in range(24):
		sc.tree(root, main.pos_of(sc.rng.randf_range(-180, 180), sc.rng.randf_range(55, 110)), sc.rng.randf_range(0.8, 1.4))


func _dev(x: float, z: float) -> Vector3:
	"""device coordinates (x to the right, z away from the device, metres) -> a place on the ground of the world"""
	var o := Vector3.ZERO
	var b := Basis.IDENTITY
	if main.rig != null:
		o = main.rig.global_position
		b = main.rig.global_transform.basis.orthonormalized()
	var p: Vector3 = o + b.x * x - b.z * z
	p.y = main.ground_y(p.x, p.z) if main.hilly() else 0.0
	return p


# ---- the lessons ---------------------------------------------------------------------------------------------------
func lesson(id: int, seed_: int) -> Array:
	"""the figures of one lesson: [{"kind", "target", "t0", "pts": [[x, z, speed to here, wait there], ...]}] - fixed"""
	match id:
		1:
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": [[-14.0, 10.0, 0, 0], [14.0, 10.0, 1.0, 0]]}]
		2:
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": [[2.0, 30.0, 0, 0], [1.0, 5.0, 1.4, 2.0], [3.0, 22.0, 1.4, 0]]}]
		3:
			var p1 := [[-12.0, 8.0, 0, 0], [-8.0, 12.0, 1.3, 0], [-4.0, 7.0, 1.3, 0], [0.0, 12.0, 2.8, 0], [4.0, 7.0, 2.8, 0], [8.0, 12.0, 5.0, 0], [12.0, 7.0, 5.0, 0]]
			var t1 := _path_time(p1)
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": p1},           # walk -> jog -> run, then on the bike
					{"kind": "cyclist", "target": true, "t0": t1, "pts": [[12.0, 7.0, 0, 0], [15.0, 19.0, 6.5, 0], [-4.0, 23.0, 6.5, 0]]}]
		4:
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": [[-12.0, 10.0, 0, 0], [-4.0, 10.0, 1.4, 4.0], [4.0, 10.0, 2.5, 4.0], [12.0, 10.0, 1.4, 0]]}]
		5:
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": [[-16.0, 17.0, 0, 0], [16.0, 17.0, 1.3, 0]]}]
		6:                                                      # A near (followed first), B far -> after the crossing B is nearer
			return [{"kind": "person", "target": true, "t0": 0.0, "pts": [[-12.0, 10.0, 0, 0], [12.0, 10.0, 1.2, 0]]},
					{"kind": "person", "target": false, "t0": 0.0, "pts": [[13.0, 14.0, 0, 0], [-12.0, 7.0, 1.66, 0]]}]
		7:
			var r := RandomNumberGenerator.new()
			r.seed = 7000 + seed_
			var fox := [[-3.0, 8.0, 0, 0]]
			var deer := []
			for k in range(7):
				fox.append([r.randf_range(-10, 10), r.randf_range(5, 10), r.randf_range(3.0, 6.0), r.randf_range(0.2, 0.9) if r.randf() < 0.35 else 0.0])
			var tf := _path_time(fox)
			deer.append([clampf(float(fox[-1][0]), -6.0, 8.0), 18.0, 0, 0])
			for k in range(6):
				deer.append([r.randf_range(-6, 8), r.randf_range(17, 21), r.randf_range(2.5, 7.0), r.randf_range(0.3, 1.2) if r.randf() < 0.3 else 0.0])
			return [{"kind": "fox", "target": true, "t0": 0.0, "pts": fox}, {"kind": "deer", "target": true, "t0": tf, "pts": deer}]
	return []


func _path_time(pts: Array) -> float:
	var t := 0.0
	for i in range(1, pts.size()):
		var a := Vector2(float(pts[i - 1][0]), float(pts[i - 1][1]))
		var b := Vector2(float(pts[i][0]), float(pts[i][1]))
		t += a.distance_to(b) / maxf(0.1, float(pts[i][2])) + float(pts[i][3])
	return t


func _keys(fig: Dictionary) -> Array:
	"""the timeline of a figure: [[t, x, z, speed]] (a wait = two keys at the same place)"""
	var t := float(fig["t0"])
	var pts: Array = fig["pts"]
	var out := [[t, float(pts[0][0]), float(pts[0][1]), 0.0]]
	for i in range(1, pts.size()):
		var a := Vector2(float(pts[i - 1][0]), float(pts[i - 1][1]))
		var b := Vector2(float(pts[i][0]), float(pts[i][1]))
		var v := maxf(0.1, float(pts[i][2]))
		t += a.distance_to(b) / v
		out.append([t, b.x, b.y, v])
		if float(pts[i][3]) > 0.0:
			t += float(pts[i][3])
			out.append([t, b.x, b.y, 0.0])
	return out


func _at(keys: Array, t: float) -> Array:
	"""[active, x, z, speed] at time t"""
	if t < float(keys[0][0]) or t > float(keys[-1][0]):
		return [false, float(keys[0][1]), float(keys[0][2]), 0.0]
	for i in range(1, keys.size()):
		var k1: Array = keys[i]
		if t <= float(k1[0]):
			var k0: Array = keys[i - 1]
			var f: float = (t - float(k0[0])) / maxf(0.0001, float(k1[0]) - float(k0[0]))
			return [true, lerpf(float(k0[1]), float(k1[1]), f), lerpf(float(k0[2]), float(k1[2]), f), float(k1[3])]
	return [true, float(keys[-1][1]), float(keys[-1][2]), 0.0]


func lessons_info() -> Array:
	var out := []
	for id in range(1, 9):
		var dur := 0.0
		if id < 8:
			for f in lesson(id, 1):
				dur = maxf(dur, float(_keys(f)[-1][0]))
		out.append({"id": id, "name": NAMES[id], "icon": ICONS[id], "secs": snappedf(dur, 0.1)})
	return out


func start(ids: Array, night := false, seed_ := 1, prep_s := 6.0) -> String:
	if running:
		return "läuft schon"
	var b: String = main.busy_with()
	if b != "":
		return "Simulator beschäftigt: " + b
	var L := []
	for x in ids:
		var i := int(x)
		if i == 8:
			night = true                                      # lesson 8 = the chosen lessons again at night
		elif i >= 1 and i <= 7 and not L.has(i):
			L.append(i)
	if L.is_empty():
		L = [1, 2, 3, 4, 5, 6, 7]
	game_stop()
	if main.scene != "parcours":
		main.set_scene("parcours")
	_saved = {"hour": main.hour(), "ir": bool(main.cond["ir"]), "servo": main.realism.servo_real if main.realism != null else true}
	if night:
		main.set_hour(23.3)
		if main.life != null and main.life.get("_prev_h") != null:
			main.life._prev_h = main.hour()
		main.cond["ir"] = true                                # the infrared light of the head (MoveEye switches its own as well)
	if main.realism != null:
		main.realism.servo_real = true                        # realism: play and swinging of the MG90S
	main.clear_visitors()
	if not main.mw_follow_on() and main.connected():
		main.mw_track(true)                                   # «Folgen» of MoveEye on (one mode in both)
	var est := 0.0
	for i in L:
		est += float(lessons_info()[i - 1]["secs"]) + prep_s + 3.0
	_look_at_field()
	run = {"lessons": L, "night": night, "seed": seed_, "i": 0, "phase": "prep", "t": main.now(), "prep_s": clampf(prep_s, 0.5, 20.0),
			"results": [], "id": Time.get_datetime_string_from_system().replace(":", "").replace("-", "").replace("T", "_"), "est": est,
			"started": Time.get_datetime_string_from_system(false, true)}
	running = true
	pics_n = 0
	_card_hide()
	_prep()
	print("parcours: start %s%s" % [str(L), " (night)" if night else ""])
	return ""


func _look_at_field() -> void:
	"""the view of the window behind and above the device, looking over the field (overlay: path, aim ray, curve)"""
	if not overlay or main.view_cam == null or main.spectate or (main.tv != null and main.tv.on):
		return
	if main.has_method("_to_free_view"):
		main._to_free_view()
	main.view_cam.look_at_from_position(_dev(0.0, -9.0) + Vector3(0, 8.5, 0), _dev(0.0, 12.0), Vector3.UP)


func stop(finish := false) -> void:
	if not running:
		return
	_clear_figs()
	running = false
	if finish:
		_make_report()
	else:
		main.start_info = "Verfolgungs-Parcours abgebrochen"
	_restore()
	cur = {}
	_paint_lines()


func _restore() -> void:
	if _saved.is_empty():
		return
	if bool(run.get("night", false)):
		main.set_hour(float(_saved["hour"]))
		if main.life != null and main.life.get("_prev_h") != null:
			main.life._prev_h = main.hour()                       # going back over 10:00 is no reason for the postman
	main.cond["ir"] = bool(_saved["ir"])
	if main.realism != null:
		main.realism.servo_real = bool(_saved["servo"])
	_saved = {}


func _prep() -> void:
	run["phase"] = "prep"
	run["t"] = main.now()
	if main.connected():
		main.mw_look("center")                               # MoveEye: the head to the middle (pauses following for «manual_hold»)


func _clear_figs() -> void:
	for f in cur.get("figs", []):
		var a = f.get("actor")
		if a != null and is_instance_valid(a):
			a.queue_free()
		f["actor"] = null


func _begin() -> void:
	var id: int = int(run["lessons"][int(run["i"])])
	main.clear_visitors()                                     # only the figures of the lesson (a story may have sent somebody)
	var figs := []
	for f in lesson(id, int(run["seed"])):
		var g: Dictionary = f.duplicate()
		g["keys"] = _keys(f)
		g["actor"] = null
		figs.append(g)
	var dur := 0.0
	for g in figs:
		dur = maxf(dur, float(g["keys"][-1][0]))
	cur = {"id": id, "figs": figs, "t0": main.now(), "dur": dur, "m": _new_metrics(), "curve": [], "trail": [], "fps_n": 0, "fps_s": 0.0}
	run["phase"] = "go"
	_paint_lines()


func _new_metrics() -> Dictionary:
	return {"active": 0.0, "frame": 0.0, "seen": 0.0, "free": 0.0, "err_sum": 0.0, "errs": [], "losses": 0, "out_t": -1.0, "lost_since": -1.0,
			"reacq": [], "lost_end": false, "servo": 0.0, "last_pan": INF, "last_tilt": INF, "dir": 0.0, "ext": INF, "osc": 0,
			"overshoot": 0.0, "mv_sign": 0.0, "last_bear": INF, "followed": -1, "cand": -1, "cand_t": 0.0, "switches": 0, "follow_t": 0.0, "was_in": false}


func _process(dt: float) -> void:
	if main == null or main.cams.is_empty():
		return
	if running:
		main.next_auto = maxf(main.next_auto, main.now() + 30.0)        # no visitors by themselves while measuring
		_tick_run(_real_dt("run"))
	if bool(game.get("on", false)):
		main.next_auto = maxf(main.next_auto, main.now() + 30.0)
		_tick_game(_real_dt("game"))
	if overlay_on() or (_draw != null and _draw.visible and not overlay_on()):
		_draw.visible = overlay_on()
		_draw.queue_redraw()


var _last_t := {}


func _real_dt(k: String) -> float:
	"""the real time since the last frame (a slow PC: frames are skipped to save CPU - main.now() is the clock)"""
	var t: float = main.now()
	var d: float = clampf(t - float(_last_t.get(k, t)), 0.0, 3.0)
	_last_t[k] = t
	return d


func _tick_run(dt: float) -> void:
	var t: float = main.now()
	match str(run["phase"]):
		"prep":                                              # the head in the middle, then the figures
			var hp: float = absf(rad_to_deg(main.head.rotation.y))
			var waited: float = t - float(run["t"])
			if (waited >= float(run["prep_s"]) and hp < 5.0) or waited > float(run["prep_s"]) + 15.0:
				_begin()
		"gap":
			if t - float(run["t"]) > 1.5:
				run["i"] = int(run["i"]) + 1
				if int(run["i"]) >= (run["lessons"] as Array).size():
					stop(true)
					return
				_prep()
		"go":
			_move_figs(t - float(cur["t0"]))
			_acc += dt
			if _acc >= STEP:
				_measure(_acc)
				_acc = 0.0
			_pics()
			if t - float(cur["t0"]) > float(cur["dur"]) + 0.6:
				_end_lesson()


func _move_figs(lt: float) -> void:
	for f in cur["figs"]:
		var s: Array = _at(f["keys"], lt)
		var a = f["actor"]
		if not bool(s[0]):
			if a != null and is_instance_valid(a) and lt > float(f["keys"][-1][0]):
				a.queue_free()                                    # done (e.g. the person who now rides the bike)
				f["actor"] = null
			continue
		var p: Vector3 = _dev(float(s[1]), float(s[2]))
		if a == null or not is_instance_valid(a):
			seed(int(run["seed"]) * 100 + int(cur["id"]) * 10 + (cur["figs"] as Array).find(f))   # the same look every time
			a = main.spawn(str(f["kind"]), p, p + (_dev(float(f["pts"][1][0]), float(f["pts"][1][1])) - p).normalized())
			randomize()
			if a == null:
				continue
			a.puppet = true                                   # the parcours moves it (actor.gd only animates)
			if main.is_dark() and str(f["kind"]) in ["person", "cyclist"] and a.get("lamp") != null:
				a.lamp.light_energy = 0.0                         # no headlamp: the IR has to do it
			f["actor"] = a
		var old: Vector3 = a.position
		var mv := Vector2(p.x - old.x, p.z - old.z)
		if mv.length() > 0.01:
			a.heading = lerp_angle(a.heading, atan2(-mv.x, -mv.y), 0.35)
			a.rotation.y = a.heading
		a.position = Vector3(p.x, old.y if main.hilly() else p.y, p.z)
		a.cur_speed = float(s[3]) if mv.length() > 0.005 else 0.0
		a.idle_kind = ""


func _target():
	"""the figure the metrics are about (the first target that is there now)"""
	for f in cur.get("figs", []):
		if bool(f["target"]) and f["actor"] != null and is_instance_valid(f["actor"]):
			return f["actor"]
	return null


func _aim(cam: Camera3D, p: Vector3) -> Array:
	"""[error °, pan error °, in the frame, bearing °] of a world point for the camera"""
	var lp: Vector3 = cam.global_transform.affine_inverse() * p
	var fh := float(main.CAM_FOV[0])
	var fv := rad_to_deg(2.0 * atan(tan(deg_to_rad(fh) / 2.0) * 9.0 / 16.0))
	var ah := rad_to_deg(atan2(lp.x, -lp.z))
	var av := rad_to_deg(atan2(lp.y, -lp.z))
	var err := rad_to_deg((-cam.global_transform.basis.z).angle_to(p - cam.global_position))
	var inf := lp.z < -0.3 and absf(ah) < fh / 2.0 * 0.95 and absf(av) < fv / 2.0 * 0.95
	var rb: Basis = main.rig.global_transform.basis.orthonormalized()
	var d3: Vector3 = p - main.head.global_position
	var bear := rad_to_deg(atan2(d3.dot(rb.x), d3.dot(-rb.z)))
	return [err, ah, inf, bear]


func _centre(a) -> Vector3:
	return (a as Node3D).global_position + Vector3(0, float(a.body_h) * 0.55 if a.get("body_h") != null else 0.9, 0)


func _measure(dt: float) -> void:
	var m: Dictionary = cur["m"]
	var t: float = main.now() - float(cur["t0"])
	var cam: Camera3D = main.cams[0]
	var pan := -rad_to_deg(main.head.rotation.y)
	var tilt := rad_to_deg(main.head_pitch.rotation.x)
	if float(m["last_pan"]) != INF:                          # servo travel and swinging (small turns back and forth)
		var dp: float = pan - float(m["last_pan"])
		m["servo"] = float(m["servo"]) + absf(dp) + absf(tilt - float(m["last_tilt"]))
		if absf(dp) > 0.05:
			var sg := signf(dp)
			if float(m["dir"]) != 0.0 and sg != float(m["dir"]):
				if float(m["ext"]) != INF:
					var amp: float = absf(float(m["last_pan"]) - float(m["ext"]))
					if amp > 0.4 and amp < 6.0:
						m["osc"] = int(m["osc"]) + 1
				m["ext"] = float(m["last_pan"])
			elif float(m["ext"]) == INF:
				m["ext"] = float(m["last_pan"])
			m["dir"] = sg
	m["last_pan"] = pan
	m["last_tilt"] = tilt
	var a = _target()
	if a == null:
		return
	var c: Vector3 = _centre(a)
	var r: Array = _aim(cam, c)
	var occl: bool = not main.line_free(cam.global_position, c)
	m["active"] = float(m["active"]) + dt
	m["err_sum"] = float(m["err_sum"]) + float(r[0]) * dt
	(m["errs"] as Array).append(snappedf(float(r[0]), 0.1))
	var inf: bool = bool(r[2])
	if inf:
		m["frame"] = float(m["frame"]) + dt
	if not occl:
		m["free"] = float(m["free"]) + dt
		if inf:
			m["seen"] = float(m["seen"]) + dt
	if main.mw_following():
		m["follow_t"] = float(m["follow_t"]) + dt
	# losses: was in the picture, out for at least LOSS_MIN s; found again = back in the picture
	if inf:
		if float(m["lost_since"]) >= 0.0:
			(m["reacq"] as Array).append(snappedf(t - float(m["lost_since"]), 0.1))
			m["lost_since"] = -1.0
		m["out_t"] = -1.0
		m["was_in"] = true
	elif bool(m["was_in"]):
		if float(m["out_t"]) < 0.0:
			m["out_t"] = t
		elif float(m["lost_since"]) < 0.0 and t - float(m["out_t"]) >= LOSS_MIN:
			m["losses"] = int(m["losses"]) + 1
			m["lost_since"] = float(m["out_t"])
	# overshoot: the figure stands, the head went past it in the direction it walked before
	var bear: float = float(r[3])
	if float(m["last_bear"]) != INF and float(a.cur_speed) > 0.2:
		var db: float = bear - float(m["last_bear"])
		if absf(db) > 0.01:
			m["mv_sign"] = signf(db)
	m["last_bear"] = bear
	if float(a.cur_speed) <= 0.05 and float(m["mv_sign"]) != 0.0 and inf:
		var past: float = float(m["mv_sign"]) * float(r[1])        # r[1] > 0: the figure right of the middle
		m["overshoot"] = maxf(float(m["overshoot"]), -past)
	# identity: which person is the head on (nearest to the middle, < 12°) - lesson 6
	if int(cur["id"]) == 6 and main.mw_following():           # (only what MoveEye follows - a head standing still swaps nobody)
		var best := -1
		var be := 12.0
		var k := 0
		for f in cur["figs"]:
			var fa = f["actor"]
			if fa != null and is_instance_valid(fa):
				var rr: Array = _aim(cam, _centre(fa))
				if bool(rr[2]) and float(rr[0]) < be:
					be = float(rr[0])
					best = k
			k += 1
		if best >= 0 and best != int(m["followed"]):
			if best != int(m["cand"]):
				m["cand"] = best
				m["cand_t"] = t
			elif t - float(m["cand_t"]) > 0.6:
				if int(m["followed"]) >= 0:
					m["switches"] = int(m["switches"]) + 1
				m["followed"] = best
	(cur["curve"] as Array).append([snappedf(t, 0.05), snappedf(float(r[0]), 0.1), inf, occl])
	var tr: Array = cur["trail"]
	tr.append((a as Node3D).global_position + Vector3(0, 0.05, 0))
	if tr.size() > 600:
		tr.pop_front()
	cur["fps_n"] = int(cur["fps_n"]) + 1
	cur["fps_s"] = float(cur["fps_s"]) + Engine.get_frames_per_second()


func _end_lesson() -> void:
	var m: Dictionary = cur["m"]
	if float(m["lost_since"]) >= 0.0:
		m["lost_end"] = true
	_clear_figs()
	(run["results"] as Array).append(_result(int(cur["id"]), m, bool(run["night"])))
	run["phase"] = "gap"
	run["t"] = main.now()
	cur["figs"] = []
	_paint_lines()


func _pct(a: float, b: float) -> float:
	return snappedf(100.0 * a / b, 0.1) if b > 0.01 else 0.0


func _result(id: int, m: Dictionary, night: bool) -> Dictionary:
	var errs: Array = (m["errs"] as Array).duplicate()
	errs.sort()
	var act: float = float(m["active"])
	var mean: float = float(m["err_sum"]) / act if act > 0.01 else 0.0
	var reacq: Array = m["reacq"]
	var rmean := 0.0
	for x in reacq:
		rmean += float(x)
	rmean = rmean / reacq.size() if reacq.size() > 0 else 0.0
	var frame := _pct(float(m["frame"]), act)
	var osc_min: float = float(m["osc"]) / maxf(0.25, act / 60.0)
	# grade: in the picture 40 · aim 25 · losses 15 · calm 10 · identity (lesson 6) or servo economy 10
	var s_frame := frame / 100.0
	var s_err := clampf(1.0 - mean / 15.0, 0.0, 1.0)
	var s_loss := clampf(1.0 - 0.25 * int(m["losses"]) - rmean / 8.0 - (0.25 if bool(m["lost_end"]) else 0.0), 0.0, 1.0)
	var s_calm := 1.0 - 0.5 * clampf(osc_min / 6.0, 0.0, 1.0) - 0.5 * clampf(float(m["overshoot"]) / 10.0, 0.0, 1.0)
	var s_last := clampf(1.0 - 0.5 * int(m["switches"]), 0.0, 1.0) if id == 6 else clampf(1.0 - maxf(0.0, float(m["servo"]) / maxf(20.0, act * 25.0) - 1.0), 0.0, 1.0)
	var score := 100.0 * (0.4 * s_frame + 0.25 * s_err + 0.15 * s_loss + 0.1 * s_calm + 0.1 * s_last)
	var note := clampf(snappedf(1.0 + 5.0 * score / 100.0, 0.5), 1.0, 6.0)
	return {"id": id, "name": NAMES[id], "night": night, "secs": snappedf(act, 0.1),
			"err_mean": snappedf(mean, 0.1), "err_med": float(errs[errs.size() / 2]) if errs.size() > 0 else 0.0,
			"err_p90": float(errs[int(errs.size() * 0.9)]) if errs.size() > 0 else 0.0, "err_max": float(errs[-1]) if errs.size() > 0 else 0.0,
			"in_pic_pct": frame, "seen_pct": _pct(float(m["seen"]), float(m["free"])), "hidden_pct": _pct(act - float(m["free"]), act),
			"losses": int(m["losses"]), "reacq_s": snappedf(rmean, 0.1), "reacq_max_s": float(reacq.max()) if reacq.size() > 0 else 0.0,
			"lost_end": bool(m["lost_end"]), "overshoot_deg": snappedf(float(m["overshoot"]), 0.1), "osc": int(m["osc"]), "osc_min": snappedf(osc_min, 0.1),
			"servo_deg": snappedf(float(m["servo"]), 1.0), "switches": int(m["switches"]), "follow_pct": _pct(float(m["follow_t"]), act),
			"score": snappedf(score, 0.1), "note": note, "fps": snappedf(float(cur["fps_s"]) / maxf(1.0, float(cur["fps_n"])), 0.1),
			"curve": _curve_small(cur["curve"])}


func _curve_small(c: Array) -> Array:
	"""the error curve for MoveEye: 2 points per second [t, error, in the picture]"""
	var out := []
	var nt := 0.0
	for p in c:
		if float(p[0]) >= nt:
			out.append([p[0], p[1], 1 if bool(p[2]) else 0])
			nt = float(p[0]) + 0.5
	return out


func _make_report() -> void:
	var res: Array = run["results"]
	var sc := 0.0
	for r in res:
		sc += float(r["score"])
	sc = sc / res.size() if res.size() > 0 else 0.0
	var sv: Dictionary = main.mw.get("servo", {})
	report = {"ok": true, "id": run["id"], "t": run["started"], "seed": run["seed"], "night": run["night"], "lessons": res,
			"score": snappedf(sc, 0.1), "note": clampf(snappedf(1.0 + 5.0 * sc / 100.0, 0.5), 1.0, 6.0), "scene": main.scene,
			"mount": main.weit.mount if main.weit != null else "scene", "mw": main.connected(), "pics": pics_n,
			"realism": {"servo_deg_s": main.SERVO_DEG_S * (main.weit.servo_k() if main.weit != null else 1.0), "servo_real": true,
					"pan_range": float(sv.get("pan_range", 180.0)), "pan_limit": main.weit.pan_limit if main.weit != null and main.weit.on_head() else null,
					"delay": main.simreal != null}}
	save()
	main.start_info = "Verfolgungs-Parcours fertig: Note %.1f" % float(report["note"])
	print("parcours: done, score %.1f, grade %.1f" % [float(report["score"]), float(report["note"])])
	_card_show()


func state() -> Dictionary:
	var st := {"ok": true, "running": running, "lessons": lessons_info(), "overlay": overlay, "ring": ring, "pics": pics_on, "pics_n": pics_n,
			"game": game_state(), "scene": main.scene}
	if running:
		var L: Array = run["lessons"]
		st["run"] = {"lessons": L, "night": run["night"], "i": run["i"], "phase": run["phase"], "est": run["est"],
				"lesson": int(L[mini(int(run["i"]), L.size() - 1)]), "done": (run["results"] as Array).size()}
		if str(run["phase"]) == "go":
			var m: Dictionary = cur["m"]
			st["run"]["t"] = snappedf(main.now() - float(cur["t0"]), 0.1)
			st["run"]["dur"] = snappedf(float(cur["dur"]), 0.1)
			st["run"]["in_pic_pct"] = _pct(float(m["frame"]), float(m["active"]))
			var cv: Array = cur["curve"]
			st["run"]["err"] = cv[-1][1] if cv.size() > 0 else null
	if not report.is_empty():
		st["report"] = report
	return st


func control(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "state"))
	match op:
		"info", "state":
			return state()
		"result":
			return {"ok": not report.is_empty(), "report": report}
		"start":
			var ids: Array = d.get("lessons", []) if typeof(d.get("lessons", [])) == TYPE_ARRAY else []
			if d.has("lesson"):
				ids = [int(d["lesson"])]
			var err := start(ids, bool(d.get("night", false)), int(d.get("seed", 1)), float(d.get("prep_s", 6.0)))
			var st := state()
			st["ok"] = err == ""
			if err != "":
				st["error"] = err
			return st
		"stop":
			stop(false)
			return state()
		"overlay":
			overlay = bool(d.get("on", not overlay))
			save()
		"ring":
			set_ring(bool(d.get("on", not ring)))
		"pics":
			pics_on = bool(d.get("on", not pics_on))
			save()
		"card":
			if bool(d.get("on", true)):
				_card_show()
			else:
				_card_hide()
		"game":
			var e := game_start(str(d.get("name", "Spieler")), bool(d.get("bot", false)), float(d.get("secs", 60.0)))
			var st2 := state()
			st2["ok"] = e == ""
			if e != "":
				st2["error"] = e
			return st2
		"steer":
			steer = Vector2(clampf(float(d.get("x", 0.0)), -1.0, 1.0), clampf(float(d.get("z", 0.0)), -1.0, 1.0))
			steer_run = bool(d.get("run", false))
			steer_t = main.now()
		"game_stop":
			game_stop()
		_:
			return {"ok": false, "error": "unknown"}
	return state()


func set_ring(on: bool) -> void:
	ring = on
	save()
	if main.scene == "parcours" and not running and not bool(game.get("on", false)):
		main.set_scene("parcours")


# ---- learning pictures (only picture data) -----------------------------------------------------------------------------
func _pics() -> void:
	if not pics_on or pics_n >= MAX_PICS or main.frame_no[0] == _frame_seen:
		return
	_frame_seen = main.frame_no[0]
	var a = _target()
	if a == null:
		return
	var t: float = main.now()
	if t - float(cur.get("pic_t", -10.0)) < 1.5:
		return
	var cam: Camera3D = main.cams[0]
	var c: Vector3 = _centre(a)
	var dist: float = cam.global_position.distance_to(c)
	var pan_v: float = absf(rad_to_deg(main.pan_vel))
	var fast: bool = float(a.cur_speed) > 2.5 or pan_v > 40.0
	if not (fast or dist > 18.0) or not bool(_aim(cam, c)[2]) or not main.line_free(cam.global_position, c):
		return
	var box: Array = main.dataset._box(a) if main.dataset != null else []
	var jpg: PackedByteArray = main.jpgs[0]
	if box.size() < 4 or jpg.is_empty():
		return
	cur["pic_t"] = t
	var dir := PICS_DIR + "/" + str(run["id"])
	DirAccess.make_dir_recursive_absolute(dir)
	var fn := "%03d.jpg" % pics_n
	var f := FileAccess.open(dir + "/" + fn, FileAccess.WRITE)
	if f == null:
		return
	f.store_buffer(jpg)
	f.close()
	var fpx := float(main.CAM_W[0]) / (2.0 * tan(deg_to_rad(float(main.CAM_FOV[0]) / 2.0)))
	var lat: float = float(a.cur_speed) / maxf(1.0, dist)                 # rad/s of the figure (worst case: across)
	var blur := int(round((absf(main.pan_vel) + lat) / 60.0 * fpx))        # about 1/60 s exposure
	var kind := str(a.kind) if str(a.get("variant")) == "" else str(a.variant)
	var lst := []
	var jf := dir + "/lernbilder.json"
	if FileAccess.file_exists(jf):
		var old = JSON.parse_string(FileAccess.get_file_as_string(jf))
		if old is Array:
			lst = old
	lst.append({"file": fn, "kind": kind, "box": box, "dist": snappedf(dist, 0.1), "speed": snappedf(float(a.cur_speed), 0.1),
			"blur_px": blur, "dark": main.is_dark(), "why": "schnell" if fast else "weit"})
	var w := FileAccess.open(jf, FileAccess.WRITE)
	if w != null:
		w.store_string(JSON.stringify(lst))
		w.close()
	pics_n += 1


func add_to_pack(ds) -> int:
	"""dataset.gd: the learning pictures of the parcours into the training pack (YOLO line + meta, like the game misses)"""
	var d := DirAccess.open(PICS_DIR)
	if d == null:
		return 0
	var n := 0
	for r in d.get_directories():
		var jf := PICS_DIR + "/" + r + "/lernbilder.json"
		var lst = JSON.parse_string(FileAccess.get_file_as_string(jf)) if FileAccess.file_exists(jf) else null
		if not (lst is Array):
			continue
		for e in lst:
			var b: Array = e.get("box", [])
			var img := PICS_DIR + "/" + r + "/" + str(e.get("file", ""))
			var cls: String = str(ds.EXPORT_KIND_CLASS.get(str(e.get("kind", "")), e.get("kind", "")))
			var ci: int = ds.EXPORT_CLASSES.find(cls)
			if b.size() < 4 or ci < 0 or not FileAccess.file_exists(img):
				continue
			var nm := "parcours_%s_%s" % [r, str(e["file"]).get_basename()]
			var f := FileAccess.open(ds.export_dir.path_join("images/train/%s.jpg" % nm), FileAccess.WRITE)
			if f == null:
				continue
			f.store_buffer(FileAccess.get_file_as_bytes(img))
			f.close()
			var fl := FileAccess.open(ds.export_dir.path_join("labels/train/%s.txt" % nm), FileAccess.WRITE)
			if fl != null:
				fl.store_string("%d %.5f %.5f %.5f %.5f\n" % [ci, float(b[0]) + float(b[2]) / 2.0, float(b[1]) + float(b[3]) / 2.0, float(b[2]), float(b[3])])
				fl.close()
			var dark := bool(e.get("dark", false))
			ds._write(ds.export_dir.path_join("labels_meta/train/%s.json" % nm), JSON.stringify({"image": nm + ".jpg", "scene": "parcours", "cond": "parcours",
					"light": 0.05 if dark else 0.8, "ir": dark, "empty": false, "vielfalt": "parcours",
					"objects": [{"line": 0, "class": cls, "kind": str(e.get("kind", "")), "dist": float(e.get("dist", -1.0)), "posture": "stehend",
					"occlusion": 0.0, "cut": 0.0, "light": 0.05 if dark else 0.8, "box_lum": -1.0, "blur_px": int(e.get("blur_px", 0)),
					"speed": float(e.get("speed", 0.0)), "box": b}]}))
			n += 1
	return n


func pics_count() -> int:
	var d := DirAccess.open(PICS_DIR)
	if d == null:
		return 0
	var n := 0
	for r in d.get_directories():
		var dd := DirAccess.open(PICS_DIR + "/" + r)
		if dd != null:
			n += dd.get_files().size() - (1 if dd.file_exists("lernbilder.json") else 0)
	return n


# ---- the game «Entkomme der Kamera» ----------------------------------------------------------------------------------------
func game_start(name_: String, bot := false, secs := 60.0) -> String:
	if running:
		return "der Parcours läuft"
	if bool(game.get("on", false)):
		return "läuft schon"
	var b: String = main.busy_with()
	if b != "":
		return "Simulator beschäftigt: " + b
	if main.scene != "parcours":
		main.set_scene("parcours")
	main.clear_visitors()
	if not main.mw_follow_on() and main.connected():
		main.mw_track(true)
	var a = main.Actor.new()
	a.controlled = true
	a.player_color = Color(0.95, 0.45, 0.1)
	main.visitors.add_child(a)
	var p: Vector3 = _dev(0.0, 9.0)
	a.setup(main, "person", p, _dev(0.0, 12.0), 1.5)
	a.set_night(main.is_dark())
	var nm := name_.strip_edges().left(20)
	game = {"on": true, "name": nm if nm != "" else "Spieler", "t0": main.now(), "secs": clampf(secs, 15.0, 180.0), "actor": a, "score": 0.0,
			"out_s": 0.0, "hid_s": 0.0, "losses": 0, "held": 0.0, "out_t": -1.0, "bot": bot, "bot_t": 0.0, "bot_dir": Vector2.ZERO,
			"rng": RandomNumberGenerator.new(), "edge_s": 0.0}
	(game["rng"] as RandomNumberGenerator).seed = 4711
	_card_hide()
	_look_at_field()
	main.start_info = "Entkomme der Kamera: %d s – raus aus dem Bild (Stick)!" % int(game["secs"])
	return ""


func game_stop(finish := false) -> void:
	if not bool(game.get("on", false)):
		return
	var a = game.get("actor")
	if a != null and is_instance_valid(a):
		a.queue_free()
	game["on"] = false
	game["actor"] = null
	if finish:
		var sc := int(round(float(game["score"])))
		game["result"] = {"name": game["name"], "score": sc, "out_s": snappedf(float(game["out_s"]), 0.1), "hid_s": snappedf(float(game["hid_s"]), 0.1),
				"losses": int(game["losses"]), "secs": game["secs"], "bot": game["bot"]}
		if main.game != null and main.game.has_method("board_add_extra"):
			main.game.board_add_extra(str(game["name"]), sc, "escape", "Entkomme der Kamera")
		main.start_info = "Entkomme der Kamera: %s – %d Punkte" % [game["name"], sc]
		_card_show_game()


func game_state() -> Dictionary:
	if game.is_empty():
		return {"on": false}
	var o := {"on": bool(game.get("on", false)), "name": game.get("name", ""), "score": int(round(float(game.get("score", 0.0)))),
			"losses": int(game.get("losses", 0)), "out_s": snappedf(float(game.get("out_s", 0.0)), 0.1)}
	if bool(o["on"]):
		o["left"] = snappedf(float(game["secs"]) - (main.now() - float(game["t0"])), 0.1)
	if game.has("result"):
		o["result"] = game["result"]
	return o


func _stick() -> Vector2:
	"""the wanted direction in device coordinates (x right, z away): control API, then MoveEye's mover stick, then the stick here"""
	if main.now() - steer_t < 1.0:
		return steer
	var dv: Dictionary = main.mw.get("drive", {}) if typeof(main.mw.get("drive", {})) == TYPE_DICTIONARY else {}
	if main.now() - main.mw_t < 1.0 and (absf(float(dv.get("l", 0.0))) > 0.05 or absf(float(dv.get("r", 0.0))) > 0.05):
		var l := float(dv.get("l", 0.0))
		var r := float(dv.get("r", 0.0))
		return Vector2((l - r) / 2.0, (l + r) / 2.0)          # forward = away from the device, the turn = sideways
	if main.pad_on:
		return Vector2(main.pad_drive.y, main.pad_drive.x)
	return Vector2.ZERO


func _tick_game(dt: float) -> void:
	var a = game.get("actor")
	if a == null or not is_instance_valid(a):
		game_stop()
		return
	var t: float = main.now() - float(game["t0"])
	var mv := _stick()
	if bool(game["bot"]):
		mv = _bot(t)
	var rb: Basis = main.rig.global_transform.basis.orthonormalized()
	var w: Vector3 = rb.x * mv.x - rb.z * mv.y                    # device -> world
	a.ctl_move = Vector2(w.x, w.z).limit_length(1.0)
	a.ctl_run = steer_run or bool(game["bot"]) or mv.length() > 0.9
	var cam: Camera3D = main.cams[0]
	var c: Vector3 = _centre(a)
	var inf := bool(_aim(cam, c)[2])
	var occl: bool = not main.line_free(cam.global_position, c)
	var d := Vector2(a.global_position.x - main.rig.global_position.x, a.global_position.z - main.rig.global_position.z).length()
	var field := d >= 4.0 and d <= 25.0                             # out of the field: no points (just running away does not count)
	if not field:
		game["edge_s"] = float(game["edge_s"]) + dt
	elif not inf:
		game["out_s"] = float(game["out_s"]) + dt
		game["score"] = float(game["score"]) + 10.0 * dt
	elif occl:
		game["hid_s"] = float(game["hid_s"]) + dt
		game["score"] = float(game["score"]) + 5.0 * dt            # hidden behind the bush: half (the camera cannot do anything)
	if inf and not occl:
		game["held"] = float(game["held"]) + dt
		game["out_t"] = -1.0
	else:
		if float(game["held"]) >= 1.0 and float(game["out_t"]) < 0.0:
			game["out_t"] = t
		if float(game["out_t"]) >= 0.0 and t - float(game["out_t"]) >= 1.0 and float(game["held"]) >= 1.0 and field:
			game["losses"] = int(game["losses"]) + 1                 # it had you for a second and lost you: + 100
			game["score"] = float(game["score"]) + 100.0
			game["held"] = 0.0
			game["out_t"] = -1.0
		elif float(game["out_t"]) < 0.0:
			game["held"] = 0.0
	if t >= float(game["secs"]):
		game_stop(true)


func _bot(t: float) -> Vector2:
	"""the computer player: sprints across the aim of the head, turns when the head comes, stays in the field"""
	var a = game["actor"]
	var r: RandomNumberGenerator = game["rng"]
	var rb: Basis = main.rig.global_transform.basis.orthonormalized()
	var off: Vector3 = a.global_position - main.rig.global_position
	var p := Vector2(off.dot(rb.x), -off.dot(rb.z))
	if t > float(game["bot_t"]):
		var bear := atan2(p.x, p.y)
		var aim: float = -main.head.rotation.y
		var side := 1.0 if wrapf(bear - aim, -PI, PI) > 0.0 else -1.0     # away from where the head looks
		var tang := Vector2(cos(bear), -sin(bear)) * side
		var radial := (r.randf_range(-0.4, 0.4) if p.length() > 8.0 and p.length() < 18.0 else (0.7 if p.length() <= 8.0 else -0.7))
		game["bot_dir"] = (tang + p.normalized() * radial).normalized()
		game["bot_t"] = t + r.randf_range(1.2, 2.6)
	return game["bot_dir"]


# ---- the overlay (window only) -----------------------------------------------------------------------------------------
func _paint_lines() -> void:
	var im: ImmediateMesh = _path_mi.mesh
	im.clear_surfaces()
	(_trail_mi.mesh as ImmediateMesh).clear_surfaces()
	if not overlay or cur.is_empty() or (cur.get("figs", []) as Array).is_empty():
		return
	for f in cur["figs"]:
		var ks: Array = f["keys"]
		if ks.size() < 2:
			continue
		im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP, _mat_plan if bool(f["target"]) else _line_mat(Color(0.8, 0.8, 0.8, 0.6)))
		for k in ks:
			im.surface_add_vertex(_dev(float(k[1]), float(k[2])) + Vector3(0, 0.08, 0))
		im.surface_end()


func _paint() -> void:
	if not overlay_on():
		return
	var c := _draw
	var vs: Vector2 = c.get_viewport_rect().size
	var tr: Array = cur.get("trail", [])
	var tim: ImmediateMesh = _trail_mi.mesh
	tim.clear_surfaces()
	if tr.size() >= 2:
		tim.surface_begin(Mesh.PRIMITIVE_LINE_STRIP, _mat_trail)
		for p in tr:
			tim.surface_add_vertex(p)
		tim.surface_end()
	var w := 320.0
	var h := 96.0
	var o := Vector2(16.0, vs.y - h - 120.0)
	c.draw_rect(Rect2(o - Vector2(8, 26), Vector2(w + 16, h + 34)), Color(0.04, 0.06, 0.09, 0.78))
	var f := ThemeDB.fallback_font
	var title := ""
	var cv: Array = []
	if running and not cur.is_empty():
		var id: int = int(cur["id"])
		title = "Lektion %d · %s%s" % [id, NAMES[id], " · Nacht (IR)" if bool(run["night"]) else ""]
		cv = cur["curve"]
		if str(run["phase"]) == "prep":
			title = "Vorbereitung: Kopf zur Mitte …"
	elif bool(game.get("on", false)):
		title = "Entkomme der Kamera · %s · %d Punkte · noch %d s" % [game["name"], int(float(game["score"])), int(float(game["secs"]) - (main.now() - float(game["t0"])))]
	c.draw_string(f, o + Vector2(0, -8), title, HORIZONTAL_ALIGNMENT_LEFT, w + 10, 13, Color(0.92, 0.95, 1.0))
	c.draw_rect(Rect2(o, Vector2(w, h)), Color(0.5, 0.6, 0.7, 0.35), false, 1.0)
	for g in [5.0, 15.0]:                                     # lines at 5° and 15°
		var y: float = o.y + h - float(g) / 30.0 * h
		c.draw_line(Vector2(o.x, y), Vector2(o.x + w, y), Color(0.5, 0.6, 0.7, 0.25), 1.0)
		c.draw_string(f, Vector2(o.x + w - 26, y - 2), "%d°" % int(g), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.6, 0.7, 0.8))
	if cv.size() >= 2:
		var t1: float = float(cv[-1][0])
		var t0 := maxf(0.0, t1 - 30.0)
		var prev := Vector2.INF
		for p in cv:
			if float(p[0]) < t0:
				continue
			var q := Vector2(o.x + (float(p[0]) - t0) / 30.0 * w, o.y + h - clampf(float(p[1]) / 30.0, 0.0, 1.0) * h)
			var col := Color(0.3, 0.9, 0.45) if bool(p[2]) else Color(1.0, 0.3, 0.25)
			if bool(p[3]):
				col = Color(0.65, 0.65, 0.7)                         # hidden behind something
			if prev != Vector2.INF:
				c.draw_line(prev, q, col, 2.0)
			prev = q
		var m: Dictionary = cur["m"]
		c.draw_string(f, o + Vector2(4, 14), "Fehler %.1f° · im Bild %.0f %% · Verluste %d" % [float(cv[-1][1]), _pct(float(m["frame"]), float(m["active"])), int(m["losses"])],
				HORIZONTAL_ALIGNMENT_LEFT, w, 12, Color(0.9, 0.92, 0.95))
	if bool(game.get("on", false)):
		c.draw_string(f, o + Vector2(6, 30), "aus dem Bild %.0f s · verdeckt %.0f s · verloren %d×" % [float(game["out_s"]), float(game["hid_s"]), int(game["losses"])],
				HORIZONTAL_ALIGNMENT_LEFT, w, 13, Color(0.9, 0.92, 0.95))
		c.draw_string(f, o + Vector2(6, 54), "Stick: Mover-Stick in MoveEye oder Stick im Simulator", HORIZONTAL_ALIGNMENT_LEFT, w, 11, Color(0.6, 0.7, 0.8))
	c.draw_string(f, o + Vector2(0, h + 14), "grün = im Bild · rot = weg · grau = verdeckt · gelb = Weg · blau = Plan", HORIZONTAL_ALIGNMENT_LEFT, w + 10, 10, Color(0.6, 0.7, 0.8))


# ---- the result card ------------------------------------------------------------------------------------------------
func _card_make() -> void:
	if _card != null:
		return
	_card = PanelContainer.new()
	_card.add_theme_stylebox_override("panel", main.UI.box(Color(0.07, 0.1, 0.14, 0.96), Color("#3b8cff"), 12, 12, 1))
	_card.position = Vector2(110, 60)
	_lay.add_child(_card)
	_card_box = VBoxContainer.new()
	_card.add_child(_card_box)


func _card_hide() -> void:
	if _card != null:
		_card.visible = false


func _lab(t: String, sz := 13, col := Color(0.9, 0.93, 0.97)) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	_card_box.add_child(l)
	return l


func _card_clear() -> void:
	_card_make()
	for ch in _card_box.get_children():
		ch.queue_free()
	_card.visible = true
	_card.reset_size()


func _card_show() -> void:
	if report.is_empty():
		return
	_card_clear()
	_lab("Verfolgungs-Parcours · Note %.1f (%.0f / 100)%s" % [float(report["note"]), float(report["score"]), " · Nacht mit IR" if bool(report["night"]) else ""], 17)
	_lab("%s · Zufall %d · Weitwinkel: %s%s" % [str(report["t"]), int(report["seed"]), str(report["mount"]), "" if bool(report["mw"]) else " · ⚠ MoveEye nicht verbunden"], 11, Color(0.6, 0.68, 0.78))
	var g := GridContainer.new()
	g.columns = 8
	g.add_theme_constant_override("h_separation", 14)
	_card_box.add_child(g)
	for hd in ["Lektion", "Note", "Zielfehler", "im Bild", "Verluste", "wiederfinden", "Pendeln / Übersch.", "Servo-Weg"]:
		var l := Label.new()
		l.text = hd
		l.add_theme_font_size_override("font_size", 11)
		l.add_theme_color_override("font_color", Color(0.55, 0.65, 0.78))
		g.add_child(l)
	for r in report["lessons"]:
		var id: int = int(r["id"])
		var cells := ["%d %s%s" % [id, NAMES[id].left(26), " (Nacht)" if bool(r["night"]) else ""], "%.1f" % float(r["note"]),
				"Ø %.1f° (90 %%: %.0f°)" % [float(r["err_mean"]), float(r["err_p90"])], "%.0f %%" % float(r["in_pic_pct"]),
				"%d%s" % [int(r["losses"]), " · %d× Wechsel" % int(r["switches"]) if id == 6 else ""], "%.1f s" % float(r["reacq_s"]) if float(r["reacq_s"]) > 0.0 else "–",
				"%d / %.1f°" % [int(r["osc"]), float(r["overshoot_deg"])], "%d°" % int(r["servo_deg"])]
		for k in range(cells.size()):
			var l := Label.new()
			l.text = cells[k]
			l.add_theme_font_size_override("font_size", 12)
			var nt := float(r["note"])
			l.add_theme_color_override("font_color", (Color("#3fcf6b") if nt >= 4.5 else (Color("#f59a4a") if nt >= 3.5 else Color("#ff4d4d"))) if k == 1 else Color(0.9, 0.93, 0.97))
			g.add_child(l)
	var rz: Dictionary = report.get("realism", {})
	_lab("Realismus: MG90S %.0f°/s · Servos wie echt · Drehbereich %.0f°%s · Bild mit Verzögerung · Simulator %.0f Bilder/s" % [float(rz.get("servo_deg_s", 200.0)),
			float(rz.get("pan_range", 180.0)), (" · Kabel ±%.0f°" % float(rz["pan_limit"])) if rz.get("pan_limit") != null else "", _fps_mean()], 11, Color(0.6, 0.68, 0.78))
	if int(report.get("pics", 0)) > 0:
		_lab("%d Lernbilder (bewegt / weit, nur Bilddaten) – kommen ins Trainingsbilder-Paket" % int(report["pics"]), 11, Color(0.6, 0.68, 0.78))
	var b := Button.new()
	b.text = "Schliessen"
	b.pressed.connect(_card_hide)
	_card_box.add_child(b)


func _fps_mean() -> float:
	var s := 0.0
	var n := 0
	for r in report.get("lessons", []):
		s += float(r.get("fps", 0.0))
		n += 1
	return s / n if n > 0 else 0.0


func _card_show_game() -> void:
	var r: Dictionary = game.get("result", {})
	if r.is_empty():
		return
	_card_clear()
	_lab("Entkomme der Kamera · %s%s" % [r["name"], " (Bot)" if bool(r["bot"]) else ""], 17)
	_lab("%d Punkte" % int(r["score"]), 22, Color("#3fcf6b"))
	_lab("%.1f s aus dem Bild (10 Punkte/s) · %.1f s verdeckt (5 Punkte/s) · %d× verloren (je 100)" % [float(r["out_s"]), float(r["hid_s"]), int(r["losses"])], 12)
	_lab("Zählt in der Rangliste des Abends (Spiel-Karte). Nur zwischen 4 und 25 m vom Gerät gibt es Punkte.", 11, Color(0.6, 0.68, 0.78))
	var b := Button.new()
	b.text = "Schliessen"
	b.pressed.connect(_card_hide)
	_card_box.add_child(b)


# ---- the window (card «Testlauf», part «Verfolgungs-Parcours») ----------------------------------------------------------
var pick := "1,5,6"


func add_controls() -> void:
	var m = main
	var sub := {"sub": "Verfolgungs-Parcours"}
	var opts := [["1,2,3,4,5,6,7", "Alle Lektionen 1–7"], ["1,5,6", "Kurz: 1, 5, 6"]]
	for i in range(1, 8):
		opts.append([str(i), "%d · %s" % [i, NAMES[i]]])
	m.add_control("select", "parcours_pick", "Verfolgungs-Parcours: Lektionen", func(): return pick, func(v): pick = str(v), "Testlauf", {"sub": "Verfolgungs-Parcours", "options": opts})
	m.add_control("button", "parcours_start", "▶ Parcours starten (MoveEye folgt, die Szene wechselt)", null, func(): _start_pick(false), "Testlauf", sub)
	m.add_control("button", "parcours_night", "Lektion 8 (Nacht): dieselben Lektionen nachts mit Infrarot", null, func(): _start_pick(true), "Testlauf", sub)
	m.add_control("button", "parcours_stop", "⏹ Parcours abbrechen", null, func(): stop(false), "Testlauf", sub)
	m.add_control("button", "parcours_card", "Ergebniskarte zeigen", null, func(): _card_show(), "Testlauf", sub)
	m.add_control("toggle", "parcours_overlay", "Einblendung: Weg der Figur, Blickstrahl, Fehlerkurve (nur für dich)", func(): return overlay, func(v): overlay = bool(v); save(), "Testlauf", sub)
	m.add_control("toggle", "parcours_ring", "Ring rund ums Gerät (8 m)", func(): return ring, func(v): set_ring(bool(v)), "Testlauf", sub)
	m.add_control("toggle", "parcours_pics", "Lernbilder sammeln (bewegte / weite Figuren, nur Bilddaten)", func(): return pics_on, func(v): pics_on = bool(v); save(), "Testlauf", sub)
	m.add_control("button", "parcours_game", "Spiel «Entkomme der Kamera» (60 s, Stick)", null, func(): game_start("Spieler"), "Testlauf", sub)
	m.add_control("button", "parcours_bot", "«Entkomme der Kamera» mit dem Bot", null, func(): game_start("Bot", true), "Testlauf", sub)


func _start_pick(night: bool) -> void:
	var ids := []
	for s in pick.split(","):
		if s.strip_edges().is_valid_int():
			ids.append(int(s))
	var e := start(ids, night)
	if e != "":
		main.start_info = "Verfolgungs-Parcours: " + e
