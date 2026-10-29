extends Node
## 3D-4.x: game type «Fehlalarm-Jäger». The players are NOT persons: everyone steers a «Lockvogel» - an animal (fox, cat,
## deer, boar - the same figures as the visitors), a branch in the wind, a lamp beam, a balloon, a falling thing or
## insects at the light. A point = the real detection of MoveEye reports a PERSON although no person is in the picture.
## Every such false alarm is a case for MoveEye's learning: the spot of the picture goes to MoveEye (mw_cmd «fa_box»,
## MoveEye fa_game_box() -> fa_learn/) with the situation (lure, distance, light, weather), and the simulator keeps the
## picture and the cases in user://spiel/<round>/fehlalarme.json (sent with «Spielbericht senden»).
## Needs MoveEye connected (it is the referee); set up only in the wizard (gamewiz.gd), the card «Spiel» is unchanged.

var game
var main

# [id, icon, name, figure (an actor kind; "" = a thing, built here), tip for the phone]
const LURES := [["fox", "🦊", "Fuchs", "fox", "Schnell und schlau: lauf quer vor der Kamera durch."],
		["cat", "🐈", "Katze", "cat", "Klein, aber ganz nah an der Kamera wirkt sie gross."],
		["deer", "🦌", "Reh", "deer", "Gross und hoch – fast wie ein Mensch? Probier's aus."],
		["boar", "🐗", "Wildschwein", "boar", "Breit und dunkel – am besten in der Nacht."],
		["branch", "🌿", "Ast im Wind", "", "«Windstoss» schüttelt den Ast – Bewegung mag die Kamera nicht."],
		["torch", "🔦", "Lampen-Strahl", "", "Nachts: lass den Lichtkegel über den Platz wandern («Schwenken»)."],
		["balloon", "🎈", "Ballon", "", "Er schwebt auf Kopfhöhe. «Steigen» lässt ihn hochsteigen."],
		["drop", "📦", "Fallender Gegenstand", "", "Trag ihn hoch und lass ihn vor der Kamera «Fallen»."],
		["bugs", "🦟", "Insekten am Licht", "", "Ein Schwarm nah vor der Linse – nachts am besten."]]
const ALL := ["fox", "cat", "deer", "boar", "branch", "torch", "balloon", "drop", "bugs"]
const ACT := {"branch": ["💨", "Windstoss"], "torch": ["↔", "Schwenken"], "balloon": ["⬆", "Steigen"], "drop": ["⬇", "Fallen"], "bugs": ["✨", "Schwärmen"]}
# how big the lure is: [from height, to height, half width] (m) - for its box in the picture
const SIZE := {"fox": [0.0, 0.55, 0.45], "cat": [0.0, 0.35, 0.3], "deer": [0.0, 1.35, 0.6], "boar": [0.0, 0.85, 0.6]}
const POINTS := 100                        # per false alarm
const NEW_KIND := 50                       # the first false alarm with a lure in this round: bonus
const COOL_P := 5.0                        # one player: not again before (s)
const EP_GAP := 4.0                        # a report of MoveEye with gaps shorter than this is one false alarm
const COOL_ALL := 2.5                      # anybody: MoveEye gets one request at a time (mw_cmd)
const MAX_CASES := 30                      # per round
const FILE := "user://spiel/fehlalarm_jaeger.json"

var allowed: Array = ALL.duplicate()       # which lures the wizard allows
var cases: Array = []                      # this round: {"n", "lure", "t", "dist", "dark", "hour", "light", "weather", "wind", "scene", "box", "file"}
var res := {}                              # end of the round: {"n", "text", "cases": [[icon, name, lure name, m]]}
var _cool_t := 0.0
var _warn_t := 0.0
var _warn_p := 0.0
var _mw_seen := false                      # MoveEye was there during this round
var _armed := true                         # (without boxes) a new false alarm only after MoveEye was quiet for a moment
var _quiet_t := 0.0
var _vis_was = null                        # [auto visitors, daily life, surprises] before the round


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY and typeof(d.get("allowed")) == TYPE_ARRAY:
		set_allowed(",".join(PackedStringArray(d["allowed"])), false)


func on() -> bool:
	return main.game_mode == "jaeger"


func mw_on() -> bool:
	"""MoveEye sends its detections (a busy PC: up to 6 s between two)"""
	return main.now() - main.mw_det_t < 6.0


func now() -> float:
	return game.now()


func lure_info(id: String) -> Array:
	for l in LURES:
		if l[0] == id:
			return l
	return LURES[0]


func allowed_str() -> String:
	return ",".join(PackedStringArray(allowed))


func set_allowed(s: String, save := true) -> void:
	"""the wizard: «fox,cat,branch» - at least one stays"""
	var out: Array = []
	for x in s.split(",", false):
		if str(x).strip_edges() in ALL and not (str(x).strip_edges() in out):
			out.append(str(x).strip_edges())
	if out.is_empty():
		out = ALL.duplicate()
	allowed = out
	if save:
		DirAccess.make_dir_recursive_absolute("user://spiel")
		var f := FileAccess.open(FILE, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify({"allowed": allowed}))


func lure_of(p: Dictionary) -> String:
	var l := str(p.get("lure", ""))
	if not (l in allowed):
		l = str(allowed[int(p["slot"]) % allowed.size()])
		p["lure"] = l
	return l


func choose(p: Dictionary, v: String) -> void:
	"""a player picks his lure on the phone (before the round)"""
	if game.round_state in ["countdown", "play"] or not (v in allowed):
		return
	p["lure"] = v
	var li := lure_info(v)
	game._say(p, "%s Du bist: %s" % [li[1], li[2]], 2.5)


# ---- the round ---------------------------------------------------------------------------------------------------------
func round_start() -> void:
	cases.clear()
	res = {}
	_cool_t = 0.0
	_armed = true
	_mw_seen = mw_on()
	_vis_was = [main.auto_visitors, main.daily_life, main.surprise_on]   # no people during the round (they would be real persons)
	main.auto_visitors = false
	main.daily_life = false
	main.surprise_on = false
	main.clear_visitors()                                  # the place is empty: only the lures are there
	if game.goal_node != null:
		game.goal_node.visible = false                     # no goal: the arrow points to the camera
	for p in game.players:
		if p != null and p["role"] == "runner":
			p["fa_n"] = 0
			p["fa_kinds"] = []
			p["fa_t"] = 0.0
			p.erase("fa_last")
			_equip(p)
	game.news("🦊 Fehlalarm-Jäger: bringt MoveEye dazu, «Person!» zu melden – ohne Mensch im Bild")
	if not mw_on():
		game.news("⚠ MoveEye ist nicht verbunden – ohne MoveEye zählt kein Fehlalarm")


func _equip(p: Dictionary) -> void:
	"""the figure of the player becomes his lure: an animal, or an invisible carrier with the thing"""
	var id := lure_of(p)
	var li := lure_info(id)
	var old = p["actor"]
	if game.round_state in ["countdown", "play"]:          # 3D-4.x: the lures start 12-20 m in front of the camera, not far away
		var cam: Camera3D = main.cams[0]
		var fw: Vector3 = -cam.global_transform.basis.z
		fw.y = 0.0
		fw = fw.normalized() if fw.length() > 0.01 else Vector3(0, 0, -1)
		var side := Vector3(-fw.z, 0, fw.x)
		var k := int(p["slot"])
		var sp: Vector3 = cam.global_position + fw * (13.0 + 2.5 * (k % 3)) + side * (float(k % 5) - 2.0) * 3.0
		sp = main.free_spot(Vector3(sp.x, 0, sp.z), 0.5, false)
		sp.y = main.ground_y(sp.x, sp.z) if main.terrain else 0.0
		old.position = sp
		var to: Vector3 = cam.global_position - sp
		p["yaw"] = atan2(-to.x, -to.z)
		old.heading = p["yaw"]
		old.rotation.y = old.heading
		(p["cam"] as Camera3D).position = sp + Vector3(sin(p["yaw"]) * 3.2, 1.95, cos(p["yaw"]) * 3.2)
	var a = game.Actor.new()
	a.controlled = true
	game.root.add_child(a)
	a.setup(main, li[3] if li[3] != "" else "cat", old.position, game.goal, 1.5)
	a.heading = old.heading
	a.rotation.y = old.rotation.y
	a.frozen = old.frozen
	a.visible = old.visible
	var cone = p.get("cone")
	if cone != null and is_instance_valid(cone):
		cone.reparent(a, false)
		cone.position.y = 2.6 if id in ["balloon", "drop"] else (1.9 if id in ["deer", "branch", "bugs"] else 1.2)
	var loot := Node3D.new()                               # (the game hides / shows the loot - here there is none)
	loot.visible = false
	a.add_child(loot)
	p["loot"] = loot
	old.queue_free()
	p["actor"] = a
	if li[3] == "":
		a.body_root.visible = false                        # the carrier is invisible, only the thing is there
		p["lure_node"] = _build_thing(id, a)
	else:
		p.erase("lure_node")
	p["lure_st"] = {"t": 0.0, "y": 0.0, "vy": 0.0, "down": false, "sweep": false}


func unequip(p: Dictionary) -> void:
	if p.has("lure_node") or str(p["actor"].kind) != "person":
		p.erase("lure_node")
		game._rebuild(p)                                   # the person figure again (look, colour)


func round_end() -> void:
	"""after the scores: the report of the cases, the text for the end screen, the person figures back"""
	var n := cases.size()
	var lst: Array = []
	for c in cases:
		var li := lure_info(str(c["lure"]))
		lst.append([li[1], str(c["n"]), li[2], float(c["dist"])])
	var txt := ""
	if n == 0:
		txt = "Kein Fehlalarm – MoveEye hat sich nicht täuschen lassen" if _mw_seen else "Kein Fehlalarm – MoveEye war nicht verbunden"
	else:
		txt = ("1 Fehlalarm ausgelöst" if n == 1 else "%d Fehlalarme ausgelöst" % n) + " – MoveEye lernt daraus"
	res = {"n": n, "text": txt, "cases": lst, "mw": _mw_seen}
	game.news(("🦊 " if n > 0 else "🛡 ") + txt)
	if n > 0 and game.learn.round_id != "":
		var dir: String = "user://spiel/" + game.learn.round_id
		DirAccess.make_dir_recursive_absolute(dir)
		var f := FileAccess.open(dir + "/fehlalarme.json", FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify({"v": 1, "quelle": "Spiel Fehlalarm-Jäger", "datum": Time.get_datetime_string_from_system(false, true),
					"simulator": main.VERSION, "mw_version": str(main.mw.get("mw_version", "")), "ki": str(main.mw.get("ai_status", "")),
					"szene": main.scene, "faelle": cases}, " "))
	for p in game.players:
		if p != null and p["role"] == "runner":
			unequip(p)
	if typeof(_vis_was) == TYPE_ARRAY and _vis_was.size() == 3:
		main.auto_visitors = bool(_vis_was[0])
		main.daily_life = bool(_vis_was[1])
		main.surprise_on = bool(_vis_was[2])
		_vis_was = null


func score(p: Dictionary) -> Array:
	"""[points, text] for the end screen"""
	var n := int(p.get("fa_n", 0))
	var li := lure_info(lure_of(p))
	var kinds: int = (p.get("fa_kinds", []) as Array).size()
	var sc: int = n * POINTS + kinds * NEW_KIND
	return [sc, "%s %s · %s" % [li[1], li[2], ("1 Fehlalarm" if n == 1 else "%d Fehlalarme" % n)]]


func target_of(p: Dictionary) -> Vector3:
	"""where a bot goes (and the arrow of the phone points): somewhere in front of the head camera"""
	var cam: Camera3D = main.cams[0]
	if not p.has("jg_tgt") or now() > float(p.get("jg_tgt_t", 0.0)) or (p["actor"].position.distance_to(p["jg_tgt"]) < 1.0):
		var fw: Vector3 = -cam.global_transform.basis.z
		fw.y = 0.0
		fw = fw.normalized() if fw.length() > 0.01 else Vector3(0, 0, -1)
		var side := Vector3(-fw.z, 0, fw.x)
		var pt: Vector3 = cam.global_position + fw * randf_range(4.0, 14.0) + side * ((float(int(p["slot"]) % 5) - 2.0) * 2.5 + randf_range(-2.0, 2.0))
		p["jg_tgt"] = main.free_spot(Vector3(pt.x, 0, pt.z), 0.4, false)
		p["jg_tgt_t"] = now() + randf_range(6.0, 12.0)
	return p["jg_tgt"]


# ---- the action button of the things -----------------------------------------------------------------------------------
func act(p: Dictionary) -> void:
	if game.round_state != "play" or p["role"] != "runner" or not p.has("lure_node"):
		return
	var s: Dictionary = p["lure_st"]
	var id := lure_of(p)
	s["t"] = now()
	match id:
		"torch":
			s["sweep"] = not bool(s["sweep"])
		"drop":
			if not bool(s["down"]) and float(s["y"]) <= 0.01:
				s["down"] = true                           # let it fall
				s["vy"] = 0.0


func _build_thing(id: String, a: Node3D) -> Node3D:
	var n := Node3D.new()
	n.name = "lure"
	a.add_child(n)
	match id:
		"branch":
			n.position = Vector3(0, 1.3, 0)
			var stick := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.025
			cm.bottom_radius = 0.05
			cm.height = 1.8
			stick.mesh = cm
			stick.rotation.z = deg_to_rad(65)
			stick.material_override = _mat(Color(0.35, 0.24, 0.14))
			n.add_child(stick)
			for i in range(8):
				var lf := MeshInstance3D.new()
				var sm := SphereMesh.new()
				var r := randf_range(0.16, 0.28)
				sm.radius = r
				sm.height = r * 1.6
				lf.mesh = sm
				var f := (float(i) / 7.0) - 0.5
				lf.position = Vector3(f * 1.6, 0.35 * f + randf_range(-0.1, 0.15), randf_range(-0.15, 0.15))
				lf.material_override = _mat(Color(0.18, 0.42, 0.16).lerp(Color(0.3, 0.55, 0.2), randf()))
				n.add_child(lf)
		"torch":
			n.position = Vector3(0, 1.25, 0)
			var lamp := MeshInstance3D.new()
			var lm := CylinderMesh.new()
			lm.top_radius = 0.035
			lm.bottom_radius = 0.045
			lm.height = 0.22
			lamp.mesh = lm
			lamp.rotation.x = deg_to_rad(90)
			lamp.material_override = _mat(Color(0.95, 0.92, 0.7), 4.0)
			n.add_child(lamp)
			var sp := SpotLight3D.new()
			sp.rotation.x = deg_to_rad(-22)
			sp.spot_range = 22.0
			sp.spot_angle = 16.0
			sp.light_energy = 8.0
			sp.light_color = Color(1.0, 0.96, 0.85)
			sp.shadow_enabled = false
			n.add_child(sp)
		"balloon":
			n.position = Vector3(0, 1.8, 0)
			var bl := MeshInstance3D.new()
			var bm := SphereMesh.new()
			bm.radius = 0.3
			bm.height = 0.72
			bl.mesh = bm
			bl.material_override = _mat(Color(0.92, 0.15, 0.2))
			n.add_child(bl)
			var st := MeshInstance3D.new()
			var sm2 := CylinderMesh.new()
			sm2.top_radius = 0.004
			sm2.bottom_radius = 0.004
			sm2.height = 1.0
			st.mesh = sm2
			st.position.y = -0.85
			st.material_override = _mat(Color(0.9, 0.9, 0.9))
			n.add_child(st)
		"drop":
			n.position = Vector3(0, 2.4, 0)
			var bx := MeshInstance3D.new()
			var bxm := BoxMesh.new()
			bxm.size = Vector3(0.4, 0.32, 0.32)
			bx.mesh = bxm
			bx.material_override = _mat(Color(0.7, 0.52, 0.3))
			n.add_child(bx)
		"bugs":
			n.position = Vector3(0, 1.9, 0)
			for i in range(26):
				var bg := MeshInstance3D.new()
				var bgm := SphereMesh.new()
				bgm.radius = 0.035
				bgm.height = 0.05
				bgm.radial_segments = 6
				bgm.rings = 3
				bg.mesh = bgm
				bg.material_override = _mat(Color(0.95, 0.93, 0.85), 2.5)
				bg.position = Vector3(randf_range(-0.4, 0.4), randf_range(-0.3, 0.3), randf_range(-0.4, 0.4))
				bg.set_meta("ph", randf() * TAU)
				n.add_child(bg)
	return n


func _mat(c: Color, glow := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	if glow > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = glow
	return m


func _process(dt: float) -> void:
	if game == null or not on() or not game.open:
		return
	var t := now()
	for p in game.players:
		if p == null or not p.has("lure_node") or not is_instance_valid(p["lure_node"]):
			continue
		var n: Node3D = p["lure_node"]
		var s: Dictionary = p["lure_st"]
		var busy: bool = t - float(s["t"]) < 2.5
		match lure_of(p):
			"branch":                                      # swings in the wind, much more with «Windstoss»
				var amp: float = (0.08 + float(main.wind) / 120.0) * (4.0 if busy else 1.0)
				n.rotation = Vector3(sin(t * 3.1) * amp * 0.5, 0, sin(t * 2.3 + 0.7) * amp)
				n.position.y = 1.3 + sin(t * 2.9) * amp * 0.3
			"torch":                                       # the beam: sweeps over the place
				n.rotation.y = sin(t * 1.4) * 0.8 if bool(s["sweep"]) else 0.0
				n.rotation.x = sin(t * 0.9) * 0.08
			"balloon":                                     # bobs; «Steigen»: up to 3.6 m for a moment
				var want: float = 1.6 if busy else 0.0
				s["y"] = move_toward(float(s["y"]), want, dt * (1.2 if busy else 0.5))
				n.position = Vector3(sin(t * 0.8) * 0.15, 1.8 + float(s["y"]) + sin(t * 1.7) * 0.12, cos(t * 0.6) * 0.1)
				n.rotation.z = sin(t * 1.1) * 0.15
			"drop":                                        # falls with gravity, bounces, lies 2 s, is carried up again
				if bool(s["down"]):
					s["vy"] = float(s["vy"]) - 9.8 * dt
					s["y"] = float(s["y"]) + float(s["vy"]) * dt
					if 2.4 + float(s["y"]) <= 0.16:
						s["y"] = 0.16 - 2.4
						s["vy"] = -float(s["vy"]) * 0.3 if abs(float(s["vy"])) > 1.0 else 0.0
						if float(s["vy"]) == 0.0:
							s["down"] = false
							s["t_down"] = t
				elif float(s["y"]) < 0.0 and t - float(s.get("t_down", 0.0)) > 2.0:
					s["y"] = minf(0.0, float(s["y"]) + dt * 1.2)
				n.position.y = 2.4 + float(s["y"])
				n.rotation.x = float(s["y"]) * 0.8
			"bugs":                                        # a swarm: every insect on its own little path, wider with «Schwärmen»
				var r: float = 0.9 if busy else 0.4
				for b in n.get_children():
					var ph: float = float(b.get_meta("ph", 0.0))
					b.position = Vector3(sin(t * 3.0 + ph) * r, sin(t * 4.3 + ph * 2.0) * r * 0.6, cos(t * 2.6 + ph * 1.3) * r)


# ---- the referee: MoveEye reports a person - who fooled it? -----------------------------------------------------------
func tick(_dt: float) -> void:
	var t := now()
	for p in game.players:                                 # the meter on the phone: how well the camera sees your lure
		if p == null or p["role"] != "runner" or p["state"] != "play":
			continue
		var b := lure_box(p)
		p["seen"] = not b.is_empty()
		p["susp"] = clampf(float(b[3]) * 300.0, 5.0, 100.0) if not b.is_empty() else 0.0
		if str(p.get("kind", "")) == "bot" and p.has("lure_node") and randf() < 0.04:
			act(p)                                         # the bots use the button too
	if mw_on():
		_mw_seen = true
	else:
		if t > _warn_t:
			_warn_t = t + 15.0
			for p in game.players:
				if p != null and p["role"] == "runner":
					game._say(p, "⚠ MoveEye ist nicht verbunden – ohne MoveEye zählt kein Fehlalarm", 4.0)
		return
	if main.now() - main.mw_det_t > 3.0 or int(main.mw_det.get("persons", 0)) <= 0:
		if _quiet_t == 0.0:
			_quiet_t = t
		if t - _quiet_t >= 1.0:
			_armed = true                                  # MoveEye stopped reporting: the next report is a new false alarm
		return
	_quiet_t = 0.0
	if t < _cool_t or cases.size() >= MAX_CASES:
		return
	if _person_in_view():                                  # a real person: that is no false alarm
		if t > _warn_p:
			_warn_p = t + 8.0
			game.news("🚶 Ein echter Mensch ist im Bild – das zählt nicht")
		return
	var mwb: Array = game.learn.mw_boxes()
	var best = null
	var best_box: Array = []
	var top := -1.0
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play":
			continue
		var b := lure_box(p, mwb.is_empty())             # MoveEye says where: then it saw it (the line of sight here is rough)
		if b.is_empty():
			continue
		if mwb.is_empty():                                 # MoveEye says only «a person»: the lure the camera sees biggest
			if _armed and t >= float(p.get("fa_t", 0.0)) and b[2] * b[3] > top:
				top = b[2] * b[3]
				best = p
				best_box = b
			continue
		var hit: Array = []                                # MoveEye says where: is one of its boxes at this lure?
		var near_best := 0.85
		for m in mwb:
			var near: float = 1.0 - Vector2(m[0] + m[2] / 2.0 - b[0] - b[2] / 2.0, m[1] + m[3] / 2.0 - b[1] - b[3] / 2.0).length()
			if game.learn.overlap(_grow(b, 0.04), m):
				near += 1.0
			if near > near_best:
				near_best = near
				hit = m
		if hit.is_empty():
			continue
		# one report of MoveEye = one false alarm: as long as MoveEye keeps reporting this lure (gaps under 4 s), it counted already
		if t - float(p.get("fa_last", -100.0)) < EP_GAP or t < float(p.get("fa_t", 0.0)):
			p["fa_last"] = t
			continue
		if near_best > top:
			top = near_best
			best = p
			best_box = hit
	if best != null:
		best["fa_last"] = t
		_credit(best, best_box)


func _grow(b: Array, m: float) -> Array:
	return [b[0] - m, b[1] - m, b[2] + 2.0 * m, b[3] + 2.0 * m]


func _person_in_view() -> bool:
	var cam: Camera3D = main.cams[0]
	for v in main.visitors.get_children():
		if not (str(v.kind) in ["person", "car"]):
			continue
		if cam.is_position_in_frustum(v.global_position + Vector3(0, 1.0, 0)) and cam.global_position.distance_to(v.global_position) < 60.0:
			return true
	return false


func _points(p: Dictionary) -> Array:
	"""a few points of the lure in the world (for its box in the picture)"""
	var a = p["actor"]
	var id := lure_of(p)
	var cam: Camera3D = main.cams[0]
	var right: Vector3 = cam.global_transform.basis.x
	var up := Vector3.UP
	if SIZE.has(id):
		var sz: Array = SIZE[id]
		var base: Vector3 = a.global_position
		return [base + up * float(sz[0]) + right * float(sz[2]), base + up * float(sz[0]) - right * float(sz[2]),
				base + up * float(sz[1]) + right * float(sz[2]), base + up * float(sz[1]) - right * float(sz[2])]
	if not p.has("lure_node") or not is_instance_valid(p["lure_node"]):
		return []
	var c: Vector3 = (p["lure_node"] as Node3D).global_position
	var hw: float = {"branch": 0.9, "torch": 0.25, "balloon": 0.32, "drop": 0.22, "bugs": 0.5}.get(id, 0.3)
	var hh: float = {"branch": 0.5, "torch": 0.25, "balloon": 0.4, "drop": 0.2, "bugs": 0.4}.get(id, 0.3)
	var out := [c + up * hh + right * hw, c + up * hh - right * hw, c - up * hh + right * hw, c - up * hh - right * hw]
	if id == "torch":                                      # the spot of light on the ground counts too
		var fw: Vector3 = -(p["lure_node"] as Node3D).global_transform.basis.z
		var spot: Vector3 = c + fw * 4.0
		spot.y = a.global_position.y
		out.append_array([spot + right * 1.0, spot - right * 1.0, spot + up * 0.3])
	return out


func lure_box(p: Dictionary, sight := true) -> Array:
	"""where the lure is in the picture of the head camera: [x, y, w, h] (0..1), or [] if not in the picture / hidden"""
	var cam: Camera3D = main.cams[0]
	var vs: Vector2 = Vector2(main.vps[0].size)
	var pts := _points(p)
	if pts.is_empty():
		return []
	var x0 := 2.0
	var y0 := 2.0
	var x1 := -1.0
	var y1 := -1.0
	var n := 0
	for w in pts:
		if cam.is_position_behind(w):
			continue
		var q: Vector2 = cam.unproject_position(w) / vs
		x0 = minf(x0, q.x)
		y0 = minf(y0, q.y)
		x1 = maxf(x1, q.x)
		y1 = maxf(y1, q.y)
		n += 1
	if n < 2 or x1 < 0.0 or x0 > 1.0 or y1 < 0.0 or y0 > 1.0:
		return []
	var mid: Vector3 = Vector3.ZERO
	for w in pts:
		mid += w
	mid /= float(pts.size())
	var top: Vector3 = mid
	for w in pts:
		if w.y > top.y:
			top = Vector3(mid.x, w.y, mid.z)
	if cam.global_position.distance_to(mid) > 70.0 or sight and not (main.line_free(cam.global_position, top) or main.line_free(cam.global_position, mid)):
		return []                                          # (hidden: neither its top nor its middle can be seen)
	x0 = clampf(x0, 0.0, 1.0)
	x1 = clampf(x1, 0.0, 1.0)
	y0 = clampf(y0, 0.0, 1.0)
	y1 = clampf(y1, 0.0, 1.0)
	if x1 - x0 < 0.002 or y1 - y0 < 0.002:
		return []
	return [snappedf(x0, 0.001), snappedf(y0, 0.001), snappedf(x1 - x0, 0.001), snappedf(y1 - y0, 0.001)]


func _credit(p: Dictionary, box: Array) -> void:
	var t := now()
	_cool_t = t + COOL_ALL
	_armed = false
	p["fa_t"] = t + COOL_P
	p["fa_n"] = int(p.get("fa_n", 0)) + 1
	var id := lure_of(p)
	var li := lure_info(id)
	var first: bool = not (id in p["fa_kinds"])
	if first:
		p["fa_kinds"].append(id)
	var a = p["actor"]
	var d: float = main.cams[0].global_position.distance_to(a.global_position)
	var c := {"n": str(p["name"]), "lure": id, "t": snappedf(t - game.t_start, 0.1), "dist": snappedf(d, 0.1), "dark": main.is_dark(),
			"hour": snappedf(main.hour(), 0.1), "light": snappedf(game.light_at(a.global_position, 0), 0.01), "weather": str(main.weather),
			"wind": snappedf(float(main.wind), 1.0), "scene": str(main.scene), "box": box, "persons": int(main.mw_det.get("persons", 0)),
			"boxes": game.learn.has_boxes()}
	cases.append(c)
	# MoveEye keeps this spot of its picture as a «no person» example, with the situation (2.98.18: «info»)
	main.mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1), "op": "fa_box", "box": box,
			"info": {"game": "jaeger", "lure": id, "dist": c["dist"], "dark": c["dark"], "hour": c["hour"], "light": c["light"],
				"weather": c["weather"], "wind": c["wind"], "scene": c["scene"]}}
	_pic(c)
	var bonus := " +%d" % (POINTS + (NEW_KIND if first else 0))
	game._say(p, "🎉 Fehlalarm! MoveEye hält %s %s für einen Menschen (%s)" % [li[1], li[2], bonus.strip_edges()], 3.5)
	game._event(p, "goal")
	game.news("🎉 %s: %s %s löst einen Fehlalarm aus (%d m)" % [p["name"], li[1], li[2], int(d)])
	main.spectate_cut("cheer", int(p["slot"]), "🎉 Fehlalarm durch %s %s!" % [li[1], li[2]])
	game.paint()


func _pic(c: Dictionary) -> void:
	"""the picture of the head camera for the report (the same as for the missed persons of gamelearn.gd)"""
	if game.learn.round_id == "":
		return
	main.want_snapshot(0)
	get_tree().create_timer(0.35).timeout.connect(func():
		var j: PackedByteArray = main.latest_jpg(0)
		if j.size() < 100:
			return
		var dir: String = "user://spiel/" + game.learn.round_id
		DirAccess.make_dir_recursive_absolute(dir)
		var fn := "fehlalarm_%02d.jpg" % cases.size()
		var f := FileAccess.open(dir + "/" + fn, FileAccess.WRITE)
		if f != null:
			f.store_buffer(j)
			c["file"] = fn)


# ---- for the phone, the spectators, the wizard -------------------------------------------------------------------------
func state_for(p: Dictionary) -> Dictionary:
	var id := lure_of(p)
	var li := lure_info(id)
	var lst: Array = []
	for l in LURES:
		if l[0] in allowed:
			lst.append({"v": l[0], "i": l[1], "n": l[2]})
	return {"lures": lst, "lure": id, "li": li[1], "ln": li[2], "tip": li[4], "act": ACT.get(id, []), "n": int(p.get("fa_n", 0)),
			"mw": mw_on(), "rep": main.now() - main.mw_det_t < 3.0 and int(main.mw_det.get("persons", 0)) > 0, "all": cases.size()}


func allowed_text() -> String:
	var o := PackedStringArray()
	for l in LURES:
		if l[0] in allowed:
			o.append(l[1] + " " + l[2])
	return ", ".join(o)


func join(p: Dictionary) -> void:
	"""somebody comes during a round: he runs as a lure too"""
	p["fa_n"] = 0
	p["fa_kinds"] = []
	p["fa_t"] = 0.0
	if p["role"] == "runner":
		_equip(p)
