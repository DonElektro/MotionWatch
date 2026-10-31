extends Node
## «Gameplay ausfeilen» (Plan docs/Gameplay_Ausfeilen_Plan.md, alle Punkte gewählt von Daniel am 31.10.2026 01:58).
## The hub of the new game rules - here so game.gd stays as it is (game.gd only calls the hooks below):
##   1  Probe-Runde mit Blinki (30 s before the real round): duck, hide, take cover (runners) · turn and 🎯 (the guard).
##      Nobody is caught, it can be skipped (phone button, PC: Enter, wizard: off / first round / always).
##   2  Wiederholung beim Erwischen: the last 3 s of the guard's camera as a short film on the phone of the caught one
##      (and as a small picture in this window) - a ring of the camera pictures that are made anyway (main.latest_jpg).
##   3  Höhepunkte am Schluss: closest call (gamerules._closest), longest time unseen (the recording game.rec),
##      best shot (the shutter, with its film) - played one after the other on the phones, listed on the winner screen.
##   (the later points: gamemission.gd, gamenacht.gd, gameturnier.gd, gameturm.gd, gameziele.gd, gametools.gd)
## The settings come from the wizard (gamewiz.gd OPTIONS / PLAYER_OPTS, kept in user://spiel/mehr.json, like gamerules.gd).
## Control: {action: "game_more", op: "info" | "set" (cfg) | "probe_skip" (slot) | "probe_now"}.
## Lite (Raspberry Pi, Compatibility renderer): _lite() - fewer, smaller film pictures, no picture in this window.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

var game
var main

const CFG_FILE := "user://spiel/mehr.json"
const PROBE_S := 30.0
const PROBE_OPTS := [["first", "für neue Spieler (vor ihrer ersten Runde)"], ["always", "vor jeder Runde"], ["off", "aus"]]
const RUN_STEPS := [["crouch", "🧎 Duck dich: «Ducken» (PC: C)"], ["hide", "🌳 Versteck dich: geduckt oder kriechend in einen Busch"],
		["cover", "🎯 Blinki zielt gleich auf dich – geh in Deckung: hinter ein Ding, in einen Busch oder flach kriechen"]]
const GUARD_STEPS := [["turn", "👀 Dreh die Kamera zu Blinki (die orange Zielscheibe)"], ["shot", "🎯 Kreis auf Blinki – und drück den Auslöser"]]

var cfg := {"game_probe": "first", "game_clip": true, "game_hl": true, "game_mission": "auto", "game_nightrule": false,
		"game_noisecount": false, "game_autofair": true, "game_badges": true, "game_tour_n": 3, "game_tour_rounds": 2,
		"game_runtools": true}
var mission                              # gamemission.gd (Punkt 4): the goal «🎒 Mission»
var nacht                                # gamenacht.gd (Punkte 5, 6, 8): Nacht-Spiel, Geräusche zählen, Fairness automatisch
var _ntick := 0.0
var turnier                              # gameturnier.gd (Punkt 8): Spielabend-Turnier on one device
var turm                                 # gameturm.gd (Punkt 9): KI-Turm
var ziele                                # gameziele.gd (Punkt 10): Abzeichen pro Szene
var sweat                                # gameschwitzen.gd (Punkt 8): «Bring MoveEye ins Schwitzen»
var sneak                                # gamesneak.gd (Punkt 7): the tools of the sneakers (Lockmittel, Verstecken)
var seq := 0

# ---- 1 Probe-Runde -------------------------------------------------------------------------------------------------------
var probe_until := 0.0                   # > now: the probe round runs (round_state stays «countdown»)
var probe_len := 0.0
var probed := {}                         # names (lower case) that did a probe round in this session
var dummy: Node3D                        # Blinki's target for the guard
var _ptick := 0.0

# ---- 2 Wiederholung beim Erwischen ---------------------------------------------------------------------------------------
const CLIP_S := 3.0
var ring := [[], []]                     # per camera (0 head, 1 fixed): [[time, jpg]] of the last CLIP_S + a bit
var _rno := [-1, -1]
var _rt := 0.0
var clips: Array = []                    # this round: {"n", "c", "slot", "by", "t", "pts", "dist", "fr": [jpg]}
var pip_layer: CanvasLayer
var pip: TextureRect
var pip_lab: Label
var _pip_tex: Array = []
var _pip_raw: Array = []
var _pip_t := 0.0
var _pip_until := 0.0

# ---- 3 Höhepunkte am Schluss ---------------------------------------------------------------------------------------------
var reel: Array = []                     # the highlights of the last round: {"k": "map" | "clip", "title", "text", ...}
const UNSEEN_MIN := 8.0                  # «längste Zeit unentdeckt» counts from 8 s on


func now() -> float:
	return game.now()


func _lite() -> bool:
	"""Lite-Grafikstufe (Raspberry Pi): the coordinator connects this with Quality.lite() when the branches are merged"""
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(CFG_FILE)) if FileAccess.file_exists(CFG_FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		_take(d)
	mission = preload("res://scripts/gamemission.gd").new()
	mission.game = game
	mission.main = main
	nacht = preload("res://scripts/gamenacht.gd").new()
	nacht.game = game
	nacht.main = main
	nacht.more = self
	for k in [["turnier", "res://scripts/gameturnier.gd"], ["turm", "res://scripts/gameturm.gd"], ["ziele", "res://scripts/gameziele.gd"],
			["sweat", "res://scripts/gameschwitzen.gd"], ["sneak", "res://scripts/gamesneak.gd"]]:
		var o = load(k[1]).new()
		o.game = game
		o.main = main
		o.more = self
		set(k[0], o)
	pip_layer = CanvasLayer.new()
	pip_layer.layer = 31                               # over the game at the PC (localplay, 30): the caught one sees it too
	add_child(pip_layer)
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.1, 0.92), Color(1.0, 0.27, 0.23), 12, 6, 2))
	pc.visible = false
	pip_layer.add_child(pc)
	var v := VBoxContainer.new()
	pc.add_child(v)
	pip = TextureRect.new()
	pip.custom_minimum_size = Vector2(320, 180)
	pip.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pip.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	v.add_child(pip)
	pip_lab = Label.new()
	pip_lab.add_theme_font_size_override("font_size", 13)
	v.add_child(pip_lab)


# ---- the settings of the wizard -----------------------------------------------------------------------------------------
func cfg_get() -> Dictionary:
	return cfg.duplicate()


func _take(d: Dictionary) -> void:
	for k in cfg:
		if not d.has(k):
			continue
		var v = d[k]
		if typeof(cfg[k]) == TYPE_BOOL:
			cfg[k] = bool(v)
		elif typeof(cfg[k]) == TYPE_INT:
			cfg[k] = int(v)
		else:
			cfg[k] = str(v)
	if not str(cfg["game_probe"]) in ["first", "always", "off"]:
		cfg["game_probe"] = "first"


func cfg_set(d: Dictionary) -> void:
	var tn := [int(cfg["game_tour_n"]), int(cfg["game_tour_rounds"])]
	_take(d)
	cfg["game_tour_n"] = clampi(int(cfg["game_tour_n"]), 2, 8)
	cfg["game_tour_rounds"] = clampi(int(cfg["game_tour_rounds"]), 1, 3)
	if turnier != null and turnier.on and turnier.turn == 0 and tn != [int(cfg["game_tour_n"]), int(cfg["game_tour_rounds"])]:
		turnier.start(int(cfg["game_tour_n"]), int(cfg["game_tour_rounds"]), turnier.names)
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(CFG_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(cfg))
	seq += 1


func on(k: String) -> bool:
	return bool(cfg.get(k, false))


func _human(p) -> bool:
	"""a person who is there now: the PC player, or a phone that is connected (not the bots, not a phone that went away)"""
	if p == null:
		return false
	var k := str(p.get("kind", "phone"))
	return k == "local" or (k == "phone" and p.get("sock") != null)


# ---- round ---------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	"""game.start_round (at the end): the probe round in front of the real one"""
	ring = [[], []]
	clips.clear()
	mission.start(str(cfg["game_mission"]))
	nacht.round_start()
	turnier.round_start()
	turm.round_start()
	ziele.round_start()
	sweat.round_start()
	sneak.round_start()
	_probe_start()
	seq += 1


func round_end() -> void:
	"""game.end_round (after the results, before the winner screen)"""
	_probe_stop(false)
	_make_reel()
	mission.clear()
	nacht.round_end()
	nacht.judge(game.results)
	sneak.round_end()
	turnier.after_round(game.results)
	turm.after_round(game.results)
	seq += 1


func _process(dt: float) -> void:
	if game == null or not game.open:
		return
	if probe_until > 0.0:
		_ptick -= dt
		if _ptick <= 0.0:
			_ptick = 0.25
			_probe_tick()
	if game.round_state == "play":
		_ntick -= dt
		if _ntick <= 0.0:
			_ntick = 0.25
			nacht.tick()
		sweat.tick(dt)                                     # real time (a slow PC has few frames)
		sneak.tick(dt)
	if game.round_state == "play" and on("game_clip"):
		_rt -= dt
		if _rt <= 0.0:
			_rt = 0.25
			_ring_tick()
	_pip_tick(dt)


# ---- hooks of the referee (game.gd) ---------------------------------------------------------------------------------------
func goal_tick(p: Dictionary) -> int:
	"""game._referee per runner: 0 = the normal goal, 1 = an own goal (mission …), 2 = reached just now (skip the rest)"""
	if sweat.active():
		return 1                                           # «MoveEye ins Schwitzen»: there is no goal to reach
	return mission.tick(p)


func target_of(p: Dictionary, t: Vector3) -> Vector3:
	"""where the arrow of the phone (and a bot) goes"""
	return mission.target_of(p, t)


func score_line(p: Dictionary, sc: int, info: String) -> Array:
	"""game.end_round: the points and the line of a player - the missions, the noises, the scene badges add their part"""
	if sweat.active():
		var sw: Array = sweat.score(p, sc, info)
		sc = int(sw[0])
		info = str(sw[1])
	var mi: String = mission.score_info(p)
	if mi != "":
		info += " · " + mi
	var nz: Array = nacht.score_info(p)
	if str(nz[1]) != "":
		sc = maxi(0, sc + int(nz[0]))
		info += " · " + str(nz[1])
	var zb: Array = ziele.check(p) if not (game.shut.ki.used_round() or game.kig.active) else []
	if not zb.is_empty():
		info += " · " + ziele.line_for(zb)
	return [sc, info]


func win_lines() -> Array:
	"""gamerules._show_win (this window): tournament, tower, scene badges, «Schwitzen»"""
	var out: Array = turnier.lines() + turm.lines() + ziele.lines()
	var sw: String = sweat.summary() if sweat.active() else ""
	if sw != "":
		out.append(sw)
	return out


func quick_started(id: String) -> void:
	"""gamewiz «quick»: a quick start - the tower / the tournament start here, every other quick start ends them"""
	if id == "turm":
		turnier.stop()
		turm.start()
	elif id == "turnier":
		turm.stop()
		turnier.start(int(cfg["game_tour_n"]), int(cfg["game_tour_rounds"]))
	else:
		turm.stop()
		turnier.stop()


func hidden(p: Dictionary) -> bool:
	"""game._referee: hidden with the tool «Verstecken» (washing line, tent)"""
	return sneak.hidden(p)


func night_k(p: Dictionary, i: int) -> float:
	return nacht.night_k(p, i)


func hear(p: Dictionary) -> float:
	return nacht.hear(p)


func energy_mul() -> float:
	return nacht.energy_mul()


func rate_mul() -> float:
	return nacht.rate_mul()


func extra_hides() -> int:
	return nacht.extra_hides()


func tower_on() -> bool:
	return turm != null and turm.on and not turm.over


# ==== 1 Probe-Runde mit Blinki =============================================================================================
func probe_on() -> bool:
	return probe_until > 0.0 and game.round_state == "countdown"


func _probe_wanted() -> bool:
	var mode := str(cfg["game_probe"])
	if mode == "off" or main.game_mode in ["free", "jaeger", "seek", "escape"] or game.jaeger.on():
		return false
	if game.cmp != null and game.cmp.busy():
		return false
	for p in game.players:
		if not _human(p) or not p["role"] in ["runner", "guard"]:
			continue
		if mode == "always" or not probed.has(str(p["name"]).to_lower()):
			return true
	return false


func _probe_start() -> void:
	probe_until = 0.0
	if not _probe_wanted():
		return
	probe_len = PROBE_S
	probe_until = now() + PROBE_S
	var shift: float = probe_until + 4.0 - float(game.t_start)
	game.t_start = float(game.t_start) + shift
	game.t_end = float(game.t_end) + shift
	var guard_h := false
	for p in game.players:
		if p == null:
			continue
		p["pr"] = {"i": 0, "done": false, "skip": false, "t0": now(), "ok_t": 0.0}
		if not _human(p):
			continue
		if p["role"] == "runner" and p["state"] == "play":
			p["actor"].frozen = false                       # the runners may move (nobody is caught - the referee waits)
			game._say(p, T.t("Probe-Runde mit Blinki (30 s): üben, niemand wird erwischt"), 3.0)
		elif p["role"] == "guard":
			guard_h = true
			game._say(p, T.t("Probe-Runde mit Blinki (30 s): Kamera drehen und den Auslöser üben"), 3.0)
	if guard_h:
		_dummy_make()
	game.news(T.t("Probe-Runde mit Blinki – 30 s üben, dann gilt's"))


func _probe_tick() -> void:
	var t := now()
	var all_done := true
	for p in game.players:
		if not _human(p) or not p.has("pr"):
			continue
		var pr: Dictionary = p["pr"]
		if bool(pr["done"]) or bool(pr["skip"]):
			continue
		if p["role"] == "runner" and p["state"] == "play":
			all_done = false
			_probe_runner(p, pr, t)
		elif p["role"] == "guard":
			all_done = false
			_probe_guard(p, pr, t)
	if t >= probe_until or all_done:
		_probe_stop(true)


func _step_ok(p: Dictionary, pr: Dictionary, steps: Array) -> void:
	pr["i"] = int(pr["i"]) + 1
	pr["t0"] = now()
	pr["ok_t"] = 0.0
	game._event(p, "item")
	if int(pr["i"]) >= steps.size():
		pr["done"] = true
		game._say(p, T.t("✅ Super – alles geübt! Gleich gilt's."), 3.0)
	else:
		game._say(p, T.t("✅ Gut gemacht!"), 1.2)


func _probe_runner(p: Dictionary, pr: Dictionary, t: float) -> void:
	var i := int(pr["i"])
	if i == 1 and game.hides.is_empty():                   # no bush in this round: crawling instead
		if p["actor"].ctl_posture == 2 and t - float(pr["t0"]) > 1.0:
			_step_ok(p, pr, RUN_STEPS)
		elif float(p["msg_until"]) < t:
			game._say(p, T.t("Probe %d/%d: %s", [i + 1, RUN_STEPS.size(), T.t("🐍 Jetzt kriechen: «Kriechen» (PC: X)")]), 1.0)
		return
	if i >= RUN_STEPS.size():
		return
	var a = p["actor"]
	var ok := false
	match RUN_STEPS[i][0]:
		"crouch":
			ok = a.ctl_posture == 1 and t - float(pr["t0"]) > 0.8
		"hide":
			ok = a.ctl_posture > 0 and _near_bush(a.position)
		"cover":
			if _covered(p):
				pr["ok_t"] = float(pr["ok_t"]) + 0.25
			else:
				pr["ok_t"] = 0.0
			ok = float(pr["ok_t"]) >= 1.5
	if ok:
		_step_ok(p, pr, RUN_STEPS)
	elif float(p["msg_until"]) < t:
		game._say(p, T.t("Probe %d/%d: %s", [i + 1, RUN_STEPS.size(), T.t(RUN_STEPS[i][1])]), 1.0)


func _near_bush(pos: Vector3) -> bool:
	for h in game.hides:
		if pos.distance_to(h["pos"]) < 1.1:
			return true
	return false


func covered(p: Dictionary) -> bool:
	return _covered(p)


func _covered(p: Dictionary) -> bool:
	"""Blinki «aims»: the runner counts as in cover when the head camera has no free line to his head (or he lies in a bush,
	or crawls far away) - where the head looks right now does not matter"""
	var a = p["actor"]
	if a.ctl_posture > 0 and _near_bush(a.position):
		return true
	var cp: Vector3 = main.cams[0].global_position
	var h: float = game.HEIGHT[int(a.ctl_posture)]
	if not main.line_free(cp, a.position + Vector3(0, h * 0.95, 0)):
		return true
	return a.ctl_posture == 2 and cp.distance_to(a.position) > 18.0


func _probe_guard(p: Dictionary, pr: Dictionary, t: float) -> void:
	var i := int(pr["i"])
	if i >= GUARD_STEPS.size():
		return
	if dummy == null or not is_instance_valid(dummy):
		pr["done"] = true
		return
	if GUARD_STEPS[i][0] == "turn" and _dummy_off(0) < 0.35:
		_step_ok(p, pr, GUARD_STEPS)
		return
	if float(p["msg_until"]) < t:
		game._say(p, T.t("Probe %d/%d: %s", [i + 1, GUARD_STEPS.size(), T.t(GUARD_STEPS[i][1])]), 1.0)


func _dummy_make() -> void:
	"""Blinki's target: an orange disc with an eye on a post, 10 m from the head, a bit to the side (the guard must turn)"""
	_dummy_free()
	var hp: Vector3 = main.cams[0].global_position
	var ang: float = float(game.guard_yaw) + deg_to_rad(38.0)
	var pos := Vector3(hp.x - sin(ang) * 10.0, 0, hp.z - cos(ang) * 10.0)
	pos = main.free_spot(pos, 0.6, false)
	pos.y = main.ground_y(pos.x, pos.z)
	dummy = Node3D.new()
	dummy.name = "blinki_ziel"
	var post := MeshInstance3D.new()
	var pm := CylinderMesh.new()
	pm.top_radius = 0.04
	pm.bottom_radius = 0.05
	pm.height = 1.2
	post.mesh = pm
	post.position = Vector3(0, 0.6, 0)
	post.material_override = _mat(Color(0.35, 0.38, 0.42), 0.0)
	dummy.add_child(post)
	for r in [[0.42, Color(1.0, 0.62, 0.26), 0.6], [0.3, Color(1, 1, 1), 0.3], [0.17, Color(1.0, 0.55, 0.15), 0.8], [0.07, Color(0.04, 0.05, 0.07), 0.0]]:
		var d := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = float(r[0])
		cm.bottom_radius = float(r[0])
		cm.height = 0.03
		d.mesh = cm
		d.rotation.x = PI / 2.0
		d.position = Vector3(0, 1.45, 0.02 * (0.42 - float(r[0])) * 10.0)
		d.material_override = _mat(r[1], float(r[2]))
		dummy.add_child(d)
	dummy.position = pos
	game.root.add_child(dummy)
	dummy.look_at(Vector3(hp.x, pos.y, hp.z), Vector3.UP)
	dummy.rotate_object_local(Vector3.UP, PI)


func _mat(c: Color, glow: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	if glow > 0.0 and not _lite():
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = glow
	return m


func _dummy_free() -> void:
	if dummy != null and is_instance_valid(dummy):
		dummy.queue_free()
	dummy = null


func _dummy_off(cam_i: int) -> float:
	"""how far Blinki's target is from the middle of the picture (share of the picture height; 9 = not in the picture)"""
	if dummy == null or not is_instance_valid(dummy):
		return 9.0
	var cam: Camera3D = main.cams[cam_i]
	var c: Vector3 = dummy.global_position + Vector3(0, 1.45, 0)
	if cam.is_position_behind(c):
		return 9.0
	var vs := Vector2(main.vps[cam_i].size)
	var q: Vector2 = cam.unproject_position(c) / vs
	return Vector2((q.x - 0.5) * vs.x / maxf(1.0, vs.y), q.y - 0.5).length()


func probe_shot(p: Dictionary) -> void:
	"""the guard presses 🎯 in the probe round: hit = Blinki's target in the circle of the shutter"""
	var pr: Dictionary = p.get("pr", {})
	if pr.is_empty() or bool(pr["done"]):
		return
	var d := _dummy_off(game.guard_cam(p))
	var r: float = game.shut.radius() if game.shut != null else 0.1
	if d <= r + 0.03:
		game._say(p, T.t("🎯 Treffer! So geht der Auslöser – in der Runde kostet jeder Schuss Energie ⚡."), 3.0)
		pr["i"] = GUARD_STEPS.size() - 1
		_step_ok(p, pr, GUARD_STEPS)
	elif d < 9.0:
		game._say(p, T.t("✗ Knapp daneben – der Kreis muss auf Blinki liegen (in der Runde wäre das ein Fehlalarm)"), 2.5)
	else:
		game._say(p, T.t("✗ Blinki ist nicht im Bild – dreh zuerst die Kamera"), 2.5)


func probe_skip(p) -> void:
	if p == null or not p.has("pr") or not probe_on():
		return
	p["pr"]["skip"] = true
	game._say(p, T.t("⏭ Probe übersprungen – gleich gilt's"), 2.0)


func _probe_stop(go: bool) -> void:
	if probe_until <= 0.0:
		return
	probe_until = 0.0
	_dummy_free()
	for p in game.players:
		if p == null:
			continue
		if _human(p) and p.has("pr"):
			probed[str(p["name"]).to_lower()] = true
			if bool(p["pr"]["done"]) and not main.game_tutorial:
				p["tut_on"] = false                        # practised with Blinki: no practice steps of the newcomers on top
		p.erase("pr")
		if go and p["role"] == "runner" and p["state"] == "play":
			game._to_start(p)
			p["actor"].frozen = true
			p["actor"].ctl_posture = 0
			p["susp"] = 0.0
			p["hide_i"] = -1
			game._say(p, T.t("▶ Probe vorbei – jetzt gilt's!"), 3.0)
	if go and game.round_state == "countdown":
		var dur: float = float(game.t_end) - float(game.t_start)
		game.t_start = minf(float(game.t_start), now() + 4.0)
		game.t_end = float(game.t_start) + dur
		game.news(T.t("▶ Probe vorbei – jetzt gilt's!"))
	seq += 1


func _probe_state(p: Dictionary) -> Dictionary:
	if not probe_on() or not p.has("pr") or not _human(p):
		return {}
	var pr: Dictionary = p["pr"]
	var steps: Array = GUARD_STEPS if p["role"] == "guard" else RUN_STEPS
	var lst := []
	for i in range(steps.size()):
		var tx: String = T.t(steps[i][1])
		if p["role"] != "guard" and i == 1 and game.hides.is_empty():
			tx = T.t("🐍 Jetzt kriechen: «Kriechen» (PC: X)")
		lst.append([tx, i < int(pr["i"]) or bool(pr["done"])])
	return {"left": int(ceil(maxf(0.0, probe_until - now()))), "len": int(probe_len), "i": int(pr["i"]), "steps": lst,
			"done": bool(pr["done"]), "skip": bool(pr["skip"]), "title": T.t("Probe-Runde mit Blinki"),
			"lead": T.t("Niemand wird erwischt. Übe kurz – dann gilt's."), "btn": T.t("⏭ Überspringen")}


# ==== 2 Wiederholung beim Erwischen ========================================================================================
func _ring_tick() -> void:
	"""keep the last seconds of the camera pictures the guard sees (they are made anyway for MoveEye and the guard; when
	nobody wants them, want_snapshot asks for 2 pictures per second - that is all a 3 s film needs)"""
	var t := now()
	var cams := [0, 1] if game.guard2_watching() else [0]
	for i in cams:
		main.want_snapshot(i)
		if int(main.frame_no[i]) != int(_rno[i]):
			_rno[i] = int(main.frame_no[i])
			var j: PackedByteArray = main.latest_jpg(i)
			if j.size() > 100:
				ring[i].append([t, j])
		while not ring[i].is_empty() and t - float(ring[i][0][0]) > 6.0:
			ring[i].pop_front()


func on_caught(p: Dictionary, by) -> void:
	"""game._caught: the film of the last 3 s from the camera of the one who caught (a person at the fixed camera: that one)"""
	mission.on_caught(p)
	if not on("game_clip") and not on("game_hl"):
		return
	var cam := 0
	if by is Dictionary and by.has("slot") and str(by.get("role", "")) == "guard":
		cam = game.guard_cam(by)
	var t := now()
	var fr := []
	for e in ring[cam]:
		if t - float(e[0]) <= CLIP_S + 0.1:
			fr.append(e[1])
	if fr.size() < 2:                                      # a slow PC: the last pictures there are (up to 6 s)
		fr = ring[cam].slice(maxi(0, ring[cam].size() - 3)).map(func(e): return e[1])
	var mx := 4 if _lite() else 8
	while fr.size() > mx:                                  # fewer pictures, spread over the 3 s
		var keep := []
		for k in range(mx):
			keep.append(fr[int(round(k * (fr.size() - 1) / float(mx - 1)))])
		fr = keep
	var dist: float = main.cams[cam].global_position.distance_to(p["actor"].position)
	var by_n: String = str(by["name"]) if by is Dictionary and by.has("name") else T.t("die Kamera")
	var c := {"n": str(p["name"]), "c": "#" + game.COLORS[int(p["slot"])].to_html(false), "slot": int(p["slot"]), "by": by_n,
			"t": snappedf(t - float(game.t_start), 0.1), "pts": int(p.get("shot_base", 0)), "dist": snappedf(dist, 0.1), "fr": fr}
	clips.append(c)
	if clips.size() > 12:
		clips.pop_front()
	if not on("game_clip") or fr.size() < 2:
		return
	var txt := T.t("🎬 Wiederholung: so hat dich %s gesehen (3 s)", [by_n])
	if p.get("sock") != null:
		var w: WebSocketPeer = p["sock"]["ws"]
		if w.get_ready_state() == WebSocketPeer.STATE_OPEN and w.get_current_outbound_buffered_amount() < 400000:
			w.send_text(JSON.stringify({"t": "gmclip", "fr": fr.map(func(j): return Marshalls.raw_to_base64(j)), "fps": snappedf(fr.size() / CLIP_S, 0.1), "txt": txt}))
	_pip_show(fr, T.t("🎬 %s erwischt – so hat es %s gesehen", [str(p["name"]), by_n]))


func _pip_show(fr: Array, txt: String) -> void:
	if DisplayServer.get_name() == "headless" or fr.is_empty():
		return
	_pip_raw = fr.duplicate()
	_pip_tex = []
	_pip_t = 0.0
	_pip_until = now() + CLIP_S * 2.0 + 0.5            # twice
	pip_lab.text = txt
	(pip.get_parent().get_parent() as Control).visible = true


func _pip_tick(dt: float) -> void:
	var pc := pip.get_parent().get_parent() as Control if pip != null else null
	if pc == null or not pc.visible:
		return
	if now() > _pip_until:
		pc.visible = false
		_pip_tex = []
		return
	if _pip_tex.size() < _pip_raw.size():                  # one picture per frame (no hitch)
		var img := Image.new()
		if img.load_jpg_from_buffer(_pip_raw[_pip_tex.size()]) == OK:
			if img.get_width() > 480:
				img.resize(480, int(480.0 * img.get_height() / img.get_width()), Image.INTERPOLATE_BILINEAR)
			_pip_tex.append(ImageTexture.create_from_image(img))
		else:
			_pip_raw.remove_at(_pip_tex.size())
		return
	if _pip_tex.is_empty():
		return
	_pip_t += dt
	pip.texture = _pip_tex[int(_pip_t * _pip_tex.size() / CLIP_S) % _pip_tex.size()]
	var vs := pc.get_viewport_rect().size
	pc.position = Vector2(16, vs.y - pc.size.y - 16)


# ==== 3 Höhepunkte am Schluss ===============================================================================================
func _make_reel() -> void:
	"""closest call, longest time unseen, best shot - in this order (only what happened in this round)"""
	reel = []
	if not on("game_hl") or main.game_mode in ["free", "jaeger"] or game.jaeger.on():
		return
	var cl: Dictionary = game.rules._closest() if game.rules != null else {}
	if not cl.is_empty():
		reel.append({"k": "map", "only": [cl["t0"], cl["t1"]], "hs": int(cl["slot"]), "n": cl["n"], "c": cl["c"],
				"title": T.t("😮 Knappster Moment"), "text": T.t("%s war bei %d %% Verdacht – und kam davon", [cl["n"], int(cl["susp"])])})
	var un := longest_unseen()
	if not un.is_empty():
		reel.append({"k": "map", "only": [maxf(float(un["t0"]), float(un["t1"]) - 8.0), float(un["t1"]) + 1.0], "hs": int(un["slot"]), "n": un["n"], "c": un["c"],
				"title": T.t("👻 Längste Zeit unentdeckt"), "text": T.t("%s – %d s am Stück nicht gesehen", [un["n"], int(un["secs"])])})
	var bs := best_shot()
	if not bs.is_empty():
		reel.append({"k": "clip", "fr": bs["fr"], "n": bs["n"], "c": bs["c"], "title": T.t("🎯 Bester Schuss"),
				"text": T.t("%s trifft %s auf %d m (+%d)", [bs["by"], bs["n"], int(round(float(bs["dist"]))), int(bs["pts"])])})
	if not reel.is_empty():
		game.news(T.t("🎬 Höhepunkte: %d Szenen", [reel.size()]))


func longest_unseen() -> Dictionary:
	"""from the recording of the round (game.rec, every 0.5 s): the longest time a runner was in play and not seen"""
	var run := {}                                          # slot -> [t0, t_last]
	var best := {}
	for row in game.rec:
		var t := float(row[0])
		var here := {}
		for e in row[1]:
			var sl := int(e[0])
			here[sl] = true
			if int(e[4]) == 0:
				if not run.has(sl):
					run[sl] = [t, t]
				run[sl][1] = t
			else:
				best = _better(best, run, sl)
				run.erase(sl)
		for sl in run.keys():
			if not here.has(sl):
				best = _better(best, run, sl)
				run.erase(sl)
	for sl in run.keys():
		best = _better(best, run, sl)
	if best.is_empty() or float(best["secs"]) < UNSEEN_MIN:
		return {}
	var p = game.players[int(best["slot"])] if int(best["slot"]) < game.players.size() else null
	best["n"] = str(p["name"]) if p != null else "?"
	best["c"] = "#" + game.COLORS[int(best["slot"])].to_html(false)
	return best


func _better(best: Dictionary, run: Dictionary, sl: int) -> Dictionary:
	if not run.has(sl):
		return best
	var secs: float = float(run[sl][1]) - float(run[sl][0])
	if best.is_empty() or secs > float(best["secs"]):
		return {"slot": sl, "t0": float(run[sl][0]), "t1": float(run[sl][1]), "secs": secs}
	return best


func best_shot() -> Dictionary:
	"""the catch with the most shutter points (100 + near + fast, gameshutter.fire) - with its film"""
	var best := {}
	for c in clips:
		if int(c["pts"]) > 0 and (best.is_empty() or int(c["pts"]) > int(best["pts"])) and (c["fr"] as Array).size() >= 2:
			best = c
	return best


func reel_lines() -> Array:
	return reel.map(func(r): return "%s: %s" % [r["title"], r["text"]])


func send_reel(p: Dictionary) -> bool:
	"""the phone asks for the highlights (button, or once after the round): the map parts come with the recording"""
	if reel.is_empty() or p.get("sock") == null:
		return false
	var items := []
	for r in reel:
		var it := {"k": r["k"], "title": r["title"], "text": r["text"], "c": r["c"]}
		if r["k"] == "map":
			it["only"] = r["only"]
			it["hs"] = r["hs"]
		else:
			it["fr"] = (r["fr"] as Array).map(func(j): return Marshalls.raw_to_base64(j))
		items.append(it)
	var msg := {"t": "gmreel", "items": items, "rp": game.replay, "head": T.t("🎬 Höhepunkte"), "close": T.t("✕ Schliessen")}
	p["sock"]["ws"].send_text(JSON.stringify(msg))
	return true


func show_reel_here() -> void:
	"""gamerules._show_win: the best shot plays in the small picture of this window"""
	for r in reel:
		if r["k"] == "clip":
			_pip_show(r["fr"], "%s – %s" % [r["title"], r["text"]])


# ---- the phone: messages and what it shows ---------------------------------------------------------------------------------
func message(p: Dictionary, t: String, m: Dictionary) -> bool:
	"""game._message: true = handled here (the message does not go further)"""
	match t:
		"gm":
			var k := str(m.get("k", ""))
			if k == "skip":
				probe_skip(p)
			elif k == "reel":
				send_reel(p)
			elif k == "tour_names":
				var nm = m.get("names", [])
				if typeof(nm) == TYPE_ARRAY:
					turnier.set_names(nm)
			elif k == "tour_new":
				turnier.start(int(cfg["game_tour_n"]), int(cfg["game_tour_rounds"]), turnier.names)
			elif k == "turm_new":
				turm.start()
			elif k == "rt":
				sneak.use(p, str(m.get("v", "")))
			return true
		"hl":                                           # the closest moment (gamerules.send_hl): now all highlights
			if on("game_hl") and send_reel(p):
				return true
	return false


func state_for(p: Dictionary) -> Dictionary:
	var d := {}
	var pr := _probe_state(p)
	if not pr.is_empty():
		d["pr"] = pr
	if game.round_state in ["lobby", "end", "countdown"] and nacht.af_on() and nacht.bal != 0 and nacht.bal_txt != "":
		d["af"] = nacht.bal_txt
	var rs: String = game.round_state
	if turnier.on and rs in ["lobby", "end", "countdown"]:
		d["tour"] = turnier.state()
	if turm.on and rs in ["lobby", "end", "countdown"]:
		d["turm"] = turm.state()
	if rs == "play":
		var si: Dictionary = sneak.info_for(p)
		if not si.is_empty():
			d["rt"] = si
	var sw: Dictionary = sweat.state_for(p)
	if not sw.is_empty():
		d["sw"] = sw
	if rs == "end" and ziele.on() and p["role"] == "runner" and str(p.get("kind", "phone")) != "bot":
		var zp: Dictionary = ziele.progress()
		zp["got"] = (ziele.fresh.get(str(p["name"]), []) as Array).map(func(b): return [b[1], b[2], b[3]])
		zp["new"] = T.t("neu")
		d["zg"] = zp
	if rs == "end":
		var wl: Array = turm.lines() + ([sweat.summary()] if sweat.active() else [])
		if not wl.is_empty():
			d["wl"] = wl
	var mt: String = mission.text_for(p) if game.round_state == "play" else ""
	if mt != "":
		d["ms"] = mt
	if game.round_state == "end" and not reel.is_empty():
		d["reel"] = {"n": reel.size(), "lines": reel_lines(), "btn": T.t("🎬 Höhepunkte ansehen"), "t": snappedf(float(game.t_end), 0.1)}
	return d


func info() -> Dictionary:
	var pl := []
	for p in game.players:
		if p != null and p.has("pr"):
			pl.append({"n": p["name"], "role": p["role"], "pr": p["pr"].duplicate()})
	return {"ok": true, "cfg": cfg_get(), "probe": probe_on(), "probe_left": snappedf(maxf(0.0, probe_until - now()), 0.1),
			"probe_players": pl, "dummy": dummy != null and is_instance_valid(dummy), "dummy_off": snappedf(_dummy_off(0), 0.01),
			"probed": probed.keys(), "round": game.round_state, "ring": [ring[0].size(), ring[1].size()],
			"clips": clips.map(func(c): return [c["n"], c["by"], c["t"], c["pts"], (c["fr"] as Array).size()]),
			"mission": mission.debug(),
			"nacht": nacht.debug(),
			"nk": game.players.filter(func(q): return q != null and q["role"] == "runner").map(func(q): return [q["name"], snappedf(nacht.night_k(q, 0), 0.01), snappedf(nacht.night_k(q, 1), 0.01), snappedf(nacht.night_k(q, 2), 0.01), snappedf(game.visibility(q), 0.02), int(q.get("nz_n", 0))]),
			"tour": turnier.state(), "turm": turm.state(), "ziele": ziele.debug(), "sweat": sweat.debug(), "sneak": sneak.debug(),
			"reel": reel.map(func(r): return [r["k"], r["title"], r["text"]]),
			"pip": pip != null and (pip.get_parent().get_parent() as Control).visible,
			"players": game.players.filter(func(q): return q != null).map(func(q): return [q["slot"], q["name"], q["role"], q["state"], str(q.get("kind", "phone")), q.get("sock") != null])}


func command(d: Dictionary) -> Dictionary:
	var op := str(d.get("op", "info"))
	match op:
		"set":
			cfg_set(d.get("cfg", {}) if typeof(d.get("cfg", {})) == TYPE_DICTIONARY else {})
		"probe_skip":
			var sl := int(d.get("slot", -1))
			if sl >= 0 and sl < game.players.size():
				probe_skip(game.players[sl])
		"probe_shot":
			var sg := int(d.get("slot", -1))
			if sg >= 0 and sg < game.players.size() and game.players[sg] != null:
				probe_shot(game.players[sg])
		"probe_forget":
			probed.clear()
		"tour_start":
			quick_started("turnier")
			if d.has("names"):
				turnier.start(int(d.get("n", cfg["game_tour_n"])), int(d.get("rounds", cfg["game_tour_rounds"])), d["names"])
		"tour_stop":
			turnier.stop()
		"turm_start":
			quick_started("turm")
		"turm_stop":
			turm.stop()
		"post":                                         # tests: the posture of a player {slot, pos 0..2}
			var sp3 := int(d.get("slot", -1))
			if sp3 >= 0 and sp3 < game.players.size() and game.players[sp3] != null:
				game.players[sp3]["actor"].ctl_posture = clampi(int(d.get("pos", 0)), 0, 2)
		"aim_dummy":                                    # tests: turn the head of the guard onto Blinki's target
			if dummy != null and is_instance_valid(dummy):
				var to: Vector3 = dummy.global_position - main.cams[0].global_position
				game.guard_yaw = atan2(-to.x, -to.z)
		"rt":                                           # tests: a tool of a sneaker {slot, v: lure | hide}
			var sr2 := int(d.get("slot", -1))
			if sr2 >= 0 and sr2 < game.players.size() and game.players[sr2] != null:
				return sneak.use(game.players[sr2], str(d.get("v", "")))
		"start_of":                                     # tests: the start point of a player, the goal
			var so := int(d.get("slot", 0))
			var sp: Vector3 = game.start_point(so)
			return {"ok": true, "x": sp.x, "z": sp.z}
		"goal":
			return {"ok": true, "x": game.goal.x, "z": game.goal.z}
		"role":                                         # tests: a role like the phone button
			var sr := int(d.get("slot", -1))
			if sr >= 0 and sr < game.players.size() and game.players[sr] != null:
				game._set_role(game.players[sr], str(d.get("r", "runner")))
				return {"ok": true, "role": game.players[sr]["role"], "mode": main.game_mode, "rs": game.round_state}
	return info()


# ---- the phone page: one script more (game.gd PAGE, before </body>) ---------------------------------------------------------
const PHONE_JS := r"""<style>
#gmpr{position:fixed;left:50%;top:calc(max(8px,env(safe-area-inset-top)) + 40px);transform:translateX(-50%);width:min(92vw,520px);z-index:12;display:flex;gap:10px;align-items:flex-start;background:#111822ee;border:1px solid #ff9f43;border-radius:14px;padding:8px 10px;pointer-events:auto}
#gmpr[hidden]{display:none}.pod{display:flex;gap:8px;justify-content:center;align-items:flex-end;margin:8px 0}.pod>div{display:flex;flex-direction:column;align-items:center;min-width:84px;border-radius:10px 10px 0 0;padding:6px}.pod span{font-size:28px}.pod i{font-style:normal;font-weight:800}.pod .p0{background:#ffd16633;height:120px}.pod .p1{background:#c0c7d033;height:96px}.pod .p2{background:#c9922e33;height:80px}
.gmzg{border:1px solid #1f2b3a;border-radius:12px;padding:6px 10px;margin:0 0 8px;text-align:left}.gmzg .zl{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}.gmzg .zl span{font-size:12px;border:1px solid #1f2b3a;border-radius:999px;padding:2px 8px;opacity:.45}.gmzg .zl span.on{opacity:1;border-color:#34c759}.gmzg .nw{color:#ffd166;font-size:11px}#gmping{position:fixed;top:30%;transform:translateX(-50%);background:#111822ee;border:1px solid #ffd166;border-radius:12px;padding:4px 10px;font-size:14px;font-weight:700;pointer-events:none;opacity:0;transition:opacity .3s;z-index:8;white-space:nowrap}#gmping b{color:#ffd166;margin-right:6px}.gmreel{border:1px solid #1f2b3a;border-radius:12px;padding:4px 10px;margin:0 0 8px;background:#3b8cff14}#pic.gmclip{border-color:#ffd166}#pic.gmclip #pictxt::before{content:"⏪ ";}#gmpr .say{flex:1;min-width:0;font-size:13px;line-height:1.35}#gmpr .say b{display:block;font-size:15px;margin-bottom:2px}
#gmpr ol{margin:4px 0 0;padding-left:18px}#gmpr li.ok{color:#34c759}#gmpr li.now{color:#ffd966;font-weight:700}
#gmpr button{background:#151e2b;color:#e6edf3;border:1px solid #1f2b3a;border-radius:10px;padding:6px 10px;font-size:13px;margin-top:4px}
.gmbk{width:46px;flex:none;line-height:0}.gmbk svg{width:100%;height:auto;display:block;overflow:visible}
.gmbk .f{fill:#ff9f43;opacity:.85}.gmbk .s{fill:#fff}.gmbk .i{fill:#ff9f43}.gmbk .p{fill:#0a0e14}.gmbk .r{fill:none;stroke:#e8590c;stroke-width:2.6}
.gmbk .l{fill:#e8590c;transform-box:fill-box;transform-origin:50% 0;transform:scaleY(0);animation:gmbl 4.8s infinite}
@keyframes gmbl{0%,90%,100%{transform:scaleY(0)}93%,94.5%{transform:scaleY(1)}}
@media (prefers-reduced-motion:reduce){.gmbk .l{animation:none}}
@media (max-height:440px){#gmpr{top:calc(max(6px,env(safe-area-inset-top)) + 32px);padding:5px 8px}#gmpr .say{font-size:12px}.gmbk{width:36px}}
</style>
<div id="gmpr" hidden></div>
<script>
// «Gameplay ausfeilen» (gamemore.gd): Probe-Runde mit Blinki, Wiederholung beim Erwischen, Höhepunkte - one script more
(function () {
  const G = window.GM = window.GM || {};
  const BK = '<svg viewBox="0 0 100 112"><path class="f" d="M50 80 L10.6 29.6 A64 64 0 0 1 89.4 29.6 Z"/><circle class="s" cx="50" cy="80" r="17"/><circle class="i" cx="50" cy="80" r="10.5"/><circle class="p" cx="50" cy="80" r="5.2"/><rect class="l" x="32" y="62" width="36" height="36"/><circle class="r" cx="50" cy="80" r="17"/></svg>';
  G.blinki = BK;
  let prSig = "";
  function probe(m) {
    const X = m.gm || {}, P = X.pr, box = document.getElementById("gmpr");
    if (!P || m.rs !== "countdown") { if (!box.hidden) box.hidden = true; prSig = ""; return; }
    ov("");                                   // no big countdown number while the probe runs
    const sig = JSON.stringify(P); if (sig === prSig) return; prSig = sig;
    box.innerHTML = '<div class="gmbk">' + BK + '</div><div class="say"><b>' + esc(P.title) + ' · ' + P.left + ' s</b>' + esc(P.lead) +
      '<ol>' + P.steps.map((s, i) => '<li class="' + (s[1] ? "ok" : (i === P.i && !P.done ? "now" : "")) + '">' + (s[1] ? "✅ " : "") + esc(s[0]) + '</li>').join("") + '</ol>' +
      (P.done || P.skip ? '' : '<button id="gmskip">' + esc(P.btn) + '</button>') + '</div>';
    box.hidden = false;
    const b = document.getElementById("gmskip"); if (b) b.onclick = () => send({t: "gm", k: "skip"});
  }
  // 2 Wiederholung beim Erwischen: the pictures of the guard's camera, shown twice in the box of the «caught» photo
  G.gmclip = function (m) {
    const fr = m.fr || []; if (fr.length < 2) return;
    const img = document.getElementById("picimg"), box = document.getElementById("pic"); let i = 0, n = 0;
    clearInterval(G._clipI); clearTimeout(G._clipT);
    const step = Math.max(120, Math.round(1000 / Math.max(0.5, m.fps || 2)));
    G._clipT = setTimeout(() => {               // first the «caught» photo (it comes a moment later), then the replay
      document.getElementById("pictxt").textContent = m.txt || ""; box.hidden = false; box.classList.add("gmclip");
      G._clipI = setInterval(() => { clearTimeout(window.__picT); img.src = "data:image/jpeg;base64," + fr[i]; i = (i + 1) % fr.length;
        if (i === 0 && ++n >= 2) { clearInterval(G._clipI); setTimeout(() => { box.hidden = true; box.classList.remove("gmclip"); }, step); } }, step);
    }, 1100);
  };
  // 3 Höhepunkte: the closest call and the longest time unseen on the map of the round (showReplay), the best shot as a film
  G.gmreel = function (m) {
    const items = m.items || []; let k = -1; clearTimeout(G._reelT); clearInterval(G._reelI); G._reelStop = false;
    const head = (i, it) => (m.head || "🎬") + " " + (i + 1) + "/" + items.length + " · " + it.title + " – " + it.text;
    const next = () => {
      clearInterval(G._reelI); let b = document.getElementById("rpbox"); if (b) { cancelAnimationFrame(b.__raf); b.remove(); }
      if (G._reelStop || ++k >= items.length) return;
      const it = items[k];
      if (it.k === "map" && m.rp && m.rp.pts) {
        showReplay(Object.assign({}, m.rp, {only: it.only, hs: it.hs, title: head(k, it)}));
        b = document.getElementById("rpbox"); const x = document.getElementById("rpx"); if (x) x.onclick = () => { G._reelStop = true; next(); };
        G._reelT = setTimeout(next, Math.min(14, (it.only[1] - it.only[0]) + 1.5) * 1000);
      } else if (it.k === "clip" && (it.fr || []).length) {
        b = document.createElement("div"); b.id = "rpbox"; b.innerHTML = '<img id="gmrimg" style="width:100vw;height:calc(100vh - 50px);object-fit:contain"><div id="rpi"></div><button class="lv" id="rpx"></button>';
        document.body.appendChild(b); document.getElementById("rpi").textContent = head(k, it); document.getElementById("rpx").textContent = m.close || "✕";
        document.getElementById("rpx").onclick = () => { G._reelStop = true; next(); };
        let i = 0; const im = document.getElementById("gmrimg"); im.src = "data:image/jpeg;base64," + it.fr[0];
        G._reelI = setInterval(() => { i = (i + 1) % it.fr.length; im.src = "data:image/jpeg;base64," + it.fr[i]; }, 380);
        G._reelT = setTimeout(next, Math.max(3500, it.fr.length * 380 * 2));
      } else next();
    };
    next();
  };
  G.reelSeen = "";
  function reelPaint(m) {
    const R = (m.gm || {}).reel, card = document.querySelector("#ov .card");
    if (!R || m.rs !== "end" || !card) return;
    if (!card.querySelector(".gmreel")) {
      const d = document.createElement("div"); d.className = "gmreel";
      d.innerHTML = '<p>' + R.lines.map(esc).join("<br>") + '</p><button class="sec" id="gmrb">' + esc(R.btn) + '</button>';
      const w = card.querySelector(".win"); if (w) w.after(d); else card.prepend(d);
      d.querySelector("#gmrb").onclick = () => send({t: "gm", k: "reel"});
      const hb = card.querySelector("#hlb"); if (hb) hb.remove();          // the closest moment is the first highlight
    }
    const WN = (m.rx || {}).win || {};
    if (G.reelSeen !== String(R.t)) { G.reelSeen = String(R.t); if (!(WN.hl && WN.hl.text)) setTimeout(() => { if (st.rs === "end") send({t: "gm", k: "reel"}); }, 1800); }
  }
  G.paints = G.paints || [];
  G.paints.push(reelPaint);
  // 7 Neue Werkzeuge: two buttons for the sneaker (energy), two for the guard (in the bar of the guard tools, TB of the page)
  function btn(id, parent, before) { let b = document.getElementById(id); if (!b) { b = document.createElement("div"); b.className = "b"; b.id = id; b.hidden = true; parent.insertBefore(b, before || parent.firstChild); } return b; }
  const RTB = {lure: btn("b-rt-lure", $("#rb")), hide: btn("b-rt-hide", $("#rb"))};
  Object.keys(RTB).forEach(k => RTB[k].addEventListener("pointerdown", e => { e.preventDefault(); send({t: "gm", k: "rt", v: k}); }));
  ["sweep", "ping"].forEach(k => { const b = btn("b-" + k, $("#gb"), $("#b-light")); TB[k] = "#b-" + k; b.addEventListener("pointerdown", e => { e.preventDefault(); send({t: "tool", k}); }); });
  G.paints.push(function (m) {
    const R = (m.gm || {}).rt, show = !!R && role === "runner" && m.rs === "play" && m.ps === "play";
    Object.keys(RTB).forEach(k => RTB[k].hidden = !show);
    if (!show) return;
    (R.t || []).forEach(x => { const b = RTB[x[0]]; if (!b) return; cool(b, x[4]); b.classList.toggle("noen", !x[5] && !(x[4] > 0));
      b.classList.toggle("on", x[0] === "hide" && (R.hid || !!R.near));
      const lab = x[1] + "|" + x[3]; if (b.dataset.l !== lab) { b.dataset.l = lab; b.innerHTML = "<i>" + x[1] + "</i>" + esc(x[2]) + "<small>" + x[3] + " ⚡</small>"; } });
    const e = document.getElementById("extra"), t = R.lab + " " + R.e + "/" + R.max + (R.hid ? " · 🧺 ✓" : (R.near ? " · 🧺 " + R.near : ""));
    if (!e.textContent.startsWith(t)) e.textContent = t + " · " + e.textContent;
  });
  // 6 Geräusche zählen: the guard hears a noise - an arrow at the edge of his picture
  G.gmping = function (m) {
    let e = document.getElementById("gmping"); if (!e) { e = document.createElement("div"); e.id = "gmping"; document.body.appendChild(e); }
    const a = m.a || 0, x = Math.max(6, Math.min(94, 50 + a / 1.2));
    e.style.left = x + "%"; e.innerHTML = '<b>' + (Math.abs(a) > 8 ? (a > 0 ? "▶" : "◀") : "▲") + '</b>' + esc(m.txt || "");
    e.style.opacity = 1; clearTimeout(G._pingT); G._pingT = setTimeout(() => e.style.opacity = 0, 2200);
    try { if (navigator.vibrate) navigator.vibrate(40); } catch (er) {}
  };
  // 8 Fairness automatisch: the balance line before / after the round
  G.paints.push(function (m) { const t = (m.gm || {}).af, card = document.querySelector("#ov .card"); if (!t || !card || card.querySelector(".gmaf")) return;
    const d = document.createElement("p"); d.className = "gmaf"; d.innerHTML = "<small><b>" + esc(t) + "</b></small>"; card.prepend(d); });
  // 8 Turnier / 9 KI-Turm / 10 Abzeichen: a block on the card before and after the round
  function card(m) { return document.querySelector("#ov .card"); }
  G.paints.push(function (m) {
    const X = m.gm || {}, c = card(m); if (!c || c.querySelector(".gmx")) return;
    let h = "";
    const U = X.tour;
    if (U) {
      if (U.done && U.podium.length) h += '<div class="win"><div class="big2">🏆 ' + esc(U.podium[0].n) + '</div><p>' + esc(U.t_win) + '</p><div class="pod">' +
        [1, 0, 2].filter(i => U.podium[i]).map(i => '<div class="p' + i + '"><b>' + esc(U.podium[i].n) + '</b><span>' + ["🥇", "🥈", "🥉"][i] + '</span><i>' + U.podium[i].pts + '</i></div>').join("") + '</div></div>';
      else h += '<div class="win"><p>' + esc(U.t_head) + ' · ' + U.turn + '/' + U.total + '</p><div class="big2">' + esc(U.cur) + '</div><p>' + esc(U.t_next) + ' <b>' + esc(U.cur) + '</b> – ' + esc(U.t_pass) + '</p></div>';
      h += '<h1>' + esc(U.t_table) + '</h1><table class="brd">' + U.table.map((e, i) => '<tr><td>' + (i + 1) + '.</td><td class="n">' + esc(e.n) + '</td><td><b>' + e.pts + '</b></td><td class="rec">' + e.list.join(" + ") + '</td></tr>').join("") + '</table>';
      if (U.edit) h += '<div class="lab">' + esc(U.t_names) + '</div><textarea id="gmtn" rows="4" style="width:100%;background:#0a0e14;color:#e6edf3;border:1px solid #1f2b3a;border-radius:10px;padding:8px;font-size:15px">' + esc(U.names.join("\n")) + '</textarea><button class="sec" id="gmtns">' + esc(U.t_save) + '</button>';
      if (U.done) h += '<button class="sec" id="gmtnew">' + esc(U.t_again) + '</button>';
    }
    const K = X.turm;
    if (K) h += '<div class="win"><p>' + esc(K.t_head) + '</p><div class="big2">' + esc(K.t_floor) + ' ' + K.floor + ' / ' + K.of + '</div>' + (K.last ? '<p>' + esc(K.last) + '</p>' : '') +
      ((K.board || []).length ? '<p><small>' + esc(K.t_board) + ': ' + K.board.map((e, i) => (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + ' ' + esc(e.n) + ' ' + e.best).join(" · ") + '</small></p>' : '') + '</div>';
    const Z = X.zg;
    if (Z) h += '<div class="gmzg"><b>' + esc(Z.head) + '</b>' + ((Z.got || []).length ? '<p>' + Z.got.map(b => b[0] + ' <b>' + esc(b[1]) + '</b>' + (b[2] ? ' <span class="nw">' + esc(Z.new) + '</span>' : '')).join(" · ") + '</p>' : '') +
      '<div class="zl">' + Z.list.map(b => '<span class="' + (b[3] ? "on" : "") + '" title="' + esc(b[2]) + '">' + b[0] + ' ' + esc(b[1]) + '</span>').join("") + '</div></div>';
    if ((X.wl || []).length && !K) h += '<p><small>' + X.wl.map(esc).join("<br>") + '</small></p>';
    if (!h) return;
    const d = document.createElement("div"); d.className = "gmx"; d.innerHTML = h; c.prepend(d);
    const sb = d.querySelector("#gmtns"); if (sb) sb.onclick = () => send({t: "gm", k: "tour_names", names: d.querySelector("#gmtn").value.split("\n").map(x => x.trim()).filter(x => x)});
    const nb = d.querySelector("#gmtnew"); if (nb) nb.onclick = () => send({t: "gm", k: "tour_new"});
    const ta = d.querySelector("#gmtn"); if (ta) { ta.addEventListener("focus", () => editing = true); ta.addEventListener("blur", () => setTimeout(() => editing = false, 300)); }
  });
  // 8 «MoveEye ins Schwitzen»: the points while playing
  G.paints.push(function (m) { const S = (m.gm || {}).sw; if (!S || role !== "runner") return; const e = document.getElementById("extra");
    const t = S.t + " " + S.pts + (S.seen ? " 📷" : "") + (S.est ? " ≈" : ""); if (!e.textContent.startsWith(t)) e.textContent = t + " · " + e.textContent; });
  // 4 Missionen: what to do now, in the line of the extras
  G.paints.push(function (m) { const t = (m.gm || {}).ms; if (t && role === "runner") { const e = document.getElementById("extra"); if (!e.textContent.startsWith(t)) e.textContent = t + " · " + e.textContent; } });
  G.paints.push(probe);
  const p0 = paint;
  paint = function (m) { p0(m); G.paints.forEach(f => { try { f(m); } catch (e) {} }); };
})();
</script>
"""
