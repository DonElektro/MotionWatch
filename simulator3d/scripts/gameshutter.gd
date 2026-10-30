extends Node
## 3D-4.x «Auslöser» (wish of Daniel): when a PERSON steers the camera instead of the AI, the guard aims the middle of the
## camera picture at a player and presses the shutter. Used by:
##   · «Team gegen MoveEye» (mwhand): the guards sit at MoveEye (live page, Controller-Ansicht R2, round 🎯 button) or at
##     the simulator PC («Kopf steuern» headpad.gd, R2 of the controller: padmap.gd) - control «shoot» with shutter = true → main.mw_shot → fire(null)
##   · «Wächter» / «Team gegen Team» with a person as guard: phone (button «Auslöser», game.gd page), PC (localplay.gd:
##     Space / A / double click / R2 / the round button) → game._guard_catch → fire(guard)
## Hit = a runner touches the circle in the middle of the picture (size by the difficulty: easy big, hard small).
##   → photo with the crosshair (time, name, distance) into the gallery of the round report, the runner is caught like
##     at «Erwischt!» (back to the start / a life less), an alarm like a real one of MoveEye: light + siren here, and
##     MoveEye puts a push into its TEST INBOX only (world_reply «shut» → MoveEye 539, never a real push).
##     Points for the guard: 100 + up to 100 for near + up to 100 for fast (since the runner came into the picture).
## Miss = a false alarm: −50 points, one false alarm more, the shutter is locked 3 s (ring on the button).
## Balance 30.10.2026 (review, approved by Daniel):
##   · ONE scoring rule for every guard (score_catch, guard_points): a catch gives its points at once - with the shutter
##     the shot (100 + near + fast), otherwise CATCH_PTS - × REPEAT for the same sneaker again in this round (100/50/25/0 %);
##     every false alarm −50 (once - not again in game.guard_score); at the end + «nicht im Ziel» (200 × share of the
##     sneakers who did not reach the goal). What the phone / PC shows during the round is exactly what counts.
##   · a shot on a protected player (just caught, start protection) is neutral: no points, no energy, «schon erwischt».
##   · start protection (spawn_protect): after (re)starting a sneaker is safe until SPAWN_M away from the start or SPAWN_S.
##   · the guard at the phone sees the picture late: a shot is judged against where everything was LAG s ago (_hist).

const RADIUS := {"easy": 0.17, "normal": 0.10, "hard": 0.05}   # of the picture height (by the Wächter-Stufe)
const LOCK := 3.0
const MISS := -50
const CATCH_PTS := 150                  # a catch without the shutter («Erwischt!», MoveEye, the bot guard, the camera meter)
const REPEAT := [1.0, 0.5, 0.25, 0.0]   # the same sneaker caught again in this round: less (no spawn camping)
const LAG := 0.25                       # s: the picture on the phone of the guard is about this old
const SPAWN_S := 6.0                    # start protection: at most this long …
const SPAWN_M := 6.0                    # … or until this far away from the start

var game
var main
var lock := {}                          # shooter ("mw" or "p<slot>") -> time the shutter is free again
var lock_len := {}                      # shooter -> length of the lock (for the ring)
var seen_t := {}                        # "<slot>:<cam>" -> when the runner came into this picture
var log_: Array = []                    # the last shots for MoveEye: {"id", "hit", "n", "pts", "d", "rt", "by", "t"}
var shots: Array = []                   # all shots of this round (for the game report of gamelearn.gd)
var jpgs := {}                          # id -> the photo (jpg)
var _id := 0
var _t := 0.0
var _r2_old := false
var _siren: AudioStreamPlayer
var _ui: Array = []                     # the overlays (crosshair + button) in the windows of the simulator
var ki                                  # gamekihilfe.gd: «KI-Rahmen», «KI zielt», «KI-Autopilot» for the person with the shutter
var _ki_tag := ""
var _hist: Array = []                   # [t, transform of the head camera, {slot: position}] - the last second (LAG)


func _ready() -> void:
	_siren = AudioStreamPlayer.new()
	_siren.stream = _make_siren()
	_siren.volume_db = -6.0
	add_child(_siren)
	ki = preload("res://scripts/gamekihilfe.gd").new()
	ki.shut = self
	ki.game = game
	ki.main = main
	add_child(ki)


var _ui_done := {}


func _add_ui() -> void:
	"""the crosshair on the picture of the head camera in the panel of the window, in «Kopf steuern» and in the game at the PC
	(each once, as soon as it exists)"""
	if not _ui_done.has("prev") and main.prev0 != null:
		_ui_done["prev"] = true
		_ui.append(attach(main.prev0, func(): return 0 if active() else -1, Callable(), false))
	if not _ui_done.has("head") and main.headpad != null and main.headpad.img != null:
		_ui_done["head"] = true
		var hp_ := attach(main.headpad.img, func(): return 0 if human_mode() == "mw" else -1, func(): return fire(null, "Sim-PC"), false)
		hp_.shooter = func(): return [true, null]                # KI-Hilfe: the guards at MoveEye
		_ui.append(hp_)
	if not _ui_done.has("local") and main.localplay != null and main.localplay.view != null:
		_ui_done["local"] = true
		var lp = main.localplay
		var lo_ := attach(lp.view, func(): return game.guard_cam(lp.p) if lp.active and lp.p != null and str(lp.role) == "guard" and human_mode() == "guard" else -1,
				func(): return fire(lp.p, str(lp.p["name"])) if lp.p != null else {}, true, func(): return lock_left(lp.p) if lp.p != null else 0.0)
		lo_.shooter = func(): return [lp.p != null, lp.p]         # KI-Hilfe: the guard at this PC
		_ui.append(lo_)


func over_button(pos: Vector2) -> bool:
	"""localplay.gd takes the mouse for the game - except on the round shutter button"""
	for o in _ui:
		if o != null and o.visible and o.btn != null and o.btn.get_global_rect().has_point(pos):
			return true
		if o != null and o.visible and o.kib != null and o.kib.visible and o.kib.get_global_rect().has_point(pos):
			return true                                    # the button «KI-Hilfe»
	return false


func now() -> float:
	return game.now()


func glevel() -> String:
	return game.rules.glevel() if game.rules != null else str(main.game_level)


func radius() -> float:
	return float(RADIUS.get(glevel(), 0.10))


func human_mode() -> String:
	"""«mw» = the guards at MoveEye steer the real head, «guard» = a person (phone / PC) is the guard, «» = the AI or a bot"""
	if not game.round_state in ["countdown", "play"]:
		return ""
	if main.game_mode == "mwhand":
		return "mw"
	if main.game_mode == "guard":
		var g = game.guard_player()
		if g != null and str(g.get("kind", "phone")) != "bot":
			return "guard"
	return ""


func active() -> bool:
	return human_mode() != ""


func _key(g) -> String:
	return "mw" if g == null else "p%d" % int(g["slot"])


func lock_left(g) -> float:
	return max(0.0, float(lock.get(_key(g), 0.0)) - now())


func info_for(g) -> Dictionary:
	"""for the page of the guard (phone) and for MoveEye (game_info): is the shutter on, the circle, the lock"""
	var k := _key(g)
	var gd: Dictionary = game.mwg if g == null else g
	return {"on": (human_mode() == "mw") if g == null else (human_mode() == "guard" and g["role"] == "guard"), "r": radius(),
			"lv": glevel(), "lock": snappedf(lock_left(g), 0.1), "len": float(lock_len.get(k, LOCK)),
			"pts": guard_points(gd), "hits": int(gd.get("shut_hits", 0)), "miss": int(gd.get("shut_miss", 0)),
			"ki": ki.info_for(g, g != null) if ki != null else {}}   # KI-Hilfe (gamekihilfe.gd); the boxes for the phone


func box_cam(p: Dictionary, cam_i: int) -> Array:
	"""where the player is in the picture of camera cam_i: [x, y, w, h] 0..1 (the head camera: gamelearn.box)"""
	if cam_i == 0:
		return game.learn.box(p)
	var cam: Camera3D = main.cams[cam_i]
	var a = p["actor"]
	var h: float = game.HEIGHT[int(a.ctl_posture)]
	var pos: Vector3 = a.position
	var top := pos + Vector3(0, h, 0)
	if cam.is_position_behind(top) or cam.is_position_behind(pos):
		return []
	var vs: Vector2 = Vector2(main.vps[cam_i].size)
	var right: Vector3 = cam.global_transform.basis.x
	var pts := [cam.unproject_position(top) / vs, cam.unproject_position(pos) / vs,
			cam.unproject_position(pos + Vector3(0, h * 0.5, 0) + right * 0.35) / vs, cam.unproject_position(pos + Vector3(0, h * 0.5, 0) - right * 0.35) / vs]
	var x0 := 9.0
	var x1 := -9.0
	var y0 := 9.0
	var y1 := -9.0
	for q in pts:
		x0 = min(x0, q.x)
		x1 = max(x1, q.x)
		y0 = min(y0, q.y)
		y1 = max(y1, q.y)
	if x1 < 0.0 or x0 > 1.0 or y1 < 0.0 or y0 > 1.0:
		return []
	x0 = clampf(x0, 0.0, 1.0)
	y0 = clampf(y0, 0.0, 1.0)
	return [x0, y0, clampf(x1, 0.0, 1.0) - x0, clampf(y1, 0.0, 1.0) - y0]


func visible_to(p: Dictionary, cam_i: int) -> bool:
	"""the guard is a person: what is really in the picture counts (not hidden, not in a hiding place) - not the AI numbers"""
	var a = p["actor"]
	if not a.visible or int(p.get("hide_i", -1)) >= 0:
		return false
	var cam: Camera3D = main.cams[cam_i]
	var h: float = game.HEIGHT[int(a.ctl_posture)]
	var pos: Vector3 = a.position
	if cam.global_position.distance_to(pos) > 90.0:
		return false
	for f in [0.9, 0.6, 0.3]:                              # one part of the body free is enough (head, chest, legs)
		var q: Vector3 = pos + Vector3(0, h * f, 0)
		if cam.is_position_in_frustum(q) and main.line_free(cam.global_position, q):
			return true
	return false


func _process(dt: float) -> void:
	_record()
	_t -= dt
	if _t <= 0.0:
		_t = 0.2
		if _ui_done.size() < 3:
			_add_ui()
		_track_seen()
		_spawn_tick()


# ---- Balance: one scoring rule for the guards -----------------------------------------------------------------------------
func score_catch(g: Dictionary, p: Dictionary, by_meter := false) -> int:
	"""game._caught: the points of this catch for the guard g (a player, mwg, the bot guard). With the shutter the shot
	(p["shot_base"]), otherwise CATCH_PTS; the same sneaker again in this round counts less (REPEAT)."""
	var cn: Dictionary = g.get("cn", {})
	var sl := int(p["slot"])
	var n := int(cn.get(sl, 0))
	var pts := int(round(float(p.get("shot_base", CATCH_PTS)) * float(REPEAT[mini(n, REPEAT.size() - 1)])))
	cn[sl] = n + 1
	g["cn"] = cn
	g["cpts"] = int(g.get("cpts", 0)) + pts
	p["catch_pts"] = pts
	p["catch_n"] = n + 1
	if by_meter and g.has("sock") and g.get("sock") != null:
		game._say(g, "📷 Die Kamera hat %s erwischt: +%d%s" % [p["name"], pts, _rep_txt(n + 1)], 3.0)
	return pts


func _rep_txt(n: int) -> String:
	return "" if n <= 1 else " (%d. Mal – zählt %d %%)" % [n, int(REPEAT[mini(n - 1, REPEAT.size() - 1)] * 100.0)]


func guard_points(g: Dictionary) -> int:
	"""the points of a guard so far (without the end bonus «nicht im Ziel»): catches − 50 per false alarm"""
	return int(g.get("cpts", 0)) + MISS * int(g.get("false", 0))


# ---- Balance: start protection --------------------------------------------------------------------------------------------
func spawn_protect(p: Dictionary) -> void:
	"""game._to_start during a round: safe until SPAWN_M away from the start or SPAWN_S over (counted from the start of play)"""
	if not game.round_state in ["countdown", "play"] or p["role"] != "runner":
		return
	p["spawn_pos"] = p["actor"].position
	p["spawn_until"] = maxf(now(), float(game.t_start)) + SPAWN_S
	p["safe_until"] = maxf(float(p["safe_until"]), float(p["spawn_until"]))
	if game.round_state == "play":
		game._say(p, "🛡 Startschutz: %d s oder %d m vom Start weg – so lange kann dich niemand erwischen" % [int(SPAWN_S), int(SPAWN_M)], 2.5)


func _spawn_tick() -> void:
	"""the protection ends early when the sneaker has left the start"""
	if game.round_state != "play":
		return
	for p in game.players:
		if p == null or not p.has("spawn_pos"):
			continue
		var t := now()
		if t >= float(p["spawn_until"]) or p["state"] != "play":
			p.erase("spawn_pos")
			continue
		if p["actor"].position.distance_to(p["spawn_pos"]) > SPAWN_M:
			if float(p["safe_until"]) <= float(p["spawn_until"]) + 0.01:
				p["safe_until"] = t
			p.erase("spawn_pos")


func protected(p: Dictionary) -> bool:
	return now() < float(p["safe_until"])


func _why_safe(p: Dictionary) -> String:
	return "Startschutz" if p.has("spawn_pos") else "schon erwischt"


# ---- Balance: what the guard at the phone saw (LAG s ago) ------------------------------------------------------------------
func _record() -> void:
	if game == null or game.round_state != "play":
		if not _hist.is_empty():
			_hist.clear()
		return
	var pos := {}
	for p in game.players:
		if p != null and p["role"] == "runner":
			pos[int(p["slot"])] = p["actor"].position
	var t := now()
	_hist.append([t, main.cams[0].global_transform, pos])
	while _hist.size() > 2 and t - float(_hist[0][0]) > 1.0:
		_hist.pop_front()


func _past(lag: float) -> Array:
	"""the newest record at least lag s old ([] = none)"""
	var want := now() - lag
	var best: Array = []
	for h in _hist:
		if float(h[0]) <= want:
			best = h
	return best


func _track_seen() -> void:
	"""since when every runner is in the picture (points for a fast shot)"""
	if game.round_state != "play":
		seen_t.clear()
		return
	for p in game.players:
		if p == null or p["role"] != "runner":
			continue
		for ci in [0, 1]:
			var k := "%d:%d" % [int(p["slot"]), ci]
			if p["state"] == "play" and visible_to(p, ci):
				if not seen_t.has(k):
					seen_t[k] = now()
			else:
				seen_t.erase(k)


func fire(g, who: String) -> Dictionary:
	"""the shutter: a shot at the middle of the picture. g = the guard (phone / PC) or null = the guards at MoveEye"""
	var mode := human_mode()
	if game.round_state != "play" or mode == "" or (g == null) != (mode == "mw"):
		return {"ok": false, "error": "Der Auslöser gilt nur in einer laufenden Runde, in der ein Mensch die Kamera steuert."}
	var k := _key(g)
	if ki != null and not ki.firing:
		ki.human(g)                                    # KI-Hilfe: the person shoots - the autopilot waits
	_ki_tag = ("auto" if ki.firing else ki.mode_of(g)) if ki != null else ""
	var left := lock_left(g)
	if left > 0.0:
		return {"ok": false, "locked": true, "lock": snappedf(left, 0.1), "error": "Auslöser gesperrt – noch %d s (Fehlalarm)" % int(ceil(left))}
	var pe: String = game.tools.check(g, "shut") if game.tools != null and game.tools.on() else ""   # 3D-4.x: a shot costs energy (gametools.gd)
	if pe != "":
		if g != null:
			game._say(g, "⏳ " + pe, 2.0)
		return {"ok": false, "energy": true, "error": pe}
	var cam_i: int = 0 if g == null else game.guard_cam(g)
	var vs := Vector2(main.vps[cam_i].size)
	var asp: float = vs.x / max(1.0, vs.y)
	var r := radius()
	# Balance: the guard at the phone saw the picture LAG s ago - judge against the head camera and the sneakers of then
	var lag: float = LAG if g != null and str(g.get("kind", "phone")) == "phone" and g.get("sock") != null and not (ki != null and ki.firing) else 0.0
	var past: Array = _past(lag) if lag > 0.0 else []
	var keep := {}
	var cam_keep: Transform3D = main.cams[0].global_transform
	if not past.is_empty():
		if cam_i == 0:
			main.cams[0].global_transform = past[1]
		for p in game.players:
			if p != null and (past[2] as Dictionary).has(int(p["slot"])):
				keep[int(p["slot"])] = p["actor"].position
				p["actor"].position = past[2][int(p["slot"])]
	var hit = null
	var prot = null                                        # Balance: a protected player in the circle (just caught, start)
	var best := 9.0
	var bestp := 9.0
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or not visible_to(p, cam_i):
			continue
		var b := box_cam(p, cam_i)
		if b.is_empty():
			continue
		var nx := clampf(0.5, float(b[0]), float(b[0]) + float(b[2]))      # the point of the figure nearest to the middle
		var ny := clampf(0.5, float(b[1]), float(b[1]) + float(b[3]))
		var dd := Vector2((nx - 0.5) * asp, ny - 0.5).length()
		if dd > r:
			continue
		if protected(p):
			if dd < bestp:
				bestp = dd
				prot = p
		elif dd < best:
			best = dd
			hit = p
	if not past.is_empty():                                # back to now
		main.cams[0].global_transform = cam_keep
		for sl in keep:
			game.players[sl]["actor"].position = keep[sl]
	if hit == null and prot != null:                       # Balance: neutral - no penalty, no energy, a short hint
		lock[k] = now() + 0.8
		lock_len[k] = 0.8
		var why := _why_safe(prot)
		if g != null:
			game._say(g, "🛡 %s – %s" % [prot["name"], why], 1.5)
		return {"ok": true, "hit": false, "neutral": true, "shutter": true, "pts": 0, "name": prot["name"], "text": "🛡 %s – %s (zählt nicht)" % [prot["name"], why]}
	if game.tools != null:
		game.tools.pay_shot(g)
	var gd: Dictionary = game.mwg if g == null else g
	if g == null and who != "" and not (who in game.mwg["names"]) and not (ki != null and ki.firing):
		game.mwg["names"].append(who)
	game.learn.on_shot(hit, game.learn.reported_recently(hit) if hit != null else game.learn.reported_recently())
	var by: String = who if who != "" else ("MoveEye" if g == null else str(g["name"]))
	var t_round := maxf(0.0, now() - game.t_start)
	if hit == null:
		gd["false"] = int(gd.get("false", 0)) + 1
		gd["shut_pts"] = int(gd.get("shut_pts", 0)) + MISS
		gd["shut_miss"] = int(gd.get("shut_miss", 0)) + 1
		lock[k] = now() + LOCK
		lock_len[k] = LOCK
		if game.tools != null:
			game.tools.miss(g)                             # 3D-4.x: a miss costs more energy
		if main.shot_sound != null:
			main.shot_sound.play()
		game.news("❌ Auslöser daneben – Fehlalarm (%s, %d)" % [by, MISS])
		if g != null:
			game._say(g, "✗ Daneben – Fehlalarm (%d), 3 s gesperrt" % MISS, 3.0)
		_log(false, "", MISS, 0.0, 0.0, by, t_round, PackedByteArray())
		return {"ok": true, "hit": false, "shutter": true, "pts": MISS, "lock": LOCK, "text": "✗ Daneben – Fehlalarm (%d). Auslöser 3 s gesperrt." % MISS}
	var a = hit["actor"]
	var dist: float = main.cams[cam_i].global_position.distance_to(a.position + Vector3(0, 1.0, 0))
	var rt: float = now() - float(seen_t.get("%d:%d" % [int(hit["slot"]), cam_i], now()))
	var pts: int = 100 + int(clampf(100.0 - dist * 5.0, 0.0, 100.0)) + int(clampf(100.0 - rt * 12.0, 0.0, 100.0))
	if main.game_tutorial or game._practising(hit):
		pts = 0                                            # practice: nobody is really caught (game._caught says so)
	var base_pts := pts
	var rep_n := int((gd.get("cn", {}) as Dictionary).get(int(hit["slot"]), 0))        # Balance: caught before in this round
	if pts > 0:
		pts = int(round(float(pts) * float(REPEAT[mini(rep_n, REPEAT.size() - 1)])))
	var cap := "🎯 %s · %d:%02d · %d m · +%d" % [hit["name"], int(t_round) / 60, int(t_round) % 60, int(round(dist)), pts]
	var jpg := _photo(cam_i, best, r, asp)
	if not jpg.is_empty() and base_pts > 0:
		game.gallery.append({"n": cap, "c": "#" + game.COLORS[hit["slot"]].to_html(false), "jpg": jpg})
		if game.gallery.size() > 8:
			game.gallery.pop_front()
		if hit["sock"] != null:
			hit["sock"]["ws"].send_text(JSON.stringify({"t": "pic", "b64": Marshalls.raw_to_base64(jpg), "txt": "🎯 Erwischt vom Auslöser von %s" % by}))
	gd["shut_pts"] = int(gd.get("shut_pts", 0)) + pts
	gd["shut_hits"] = int(gd.get("shut_hits", 0)) + (1 if base_pts > 0 else 0)
	lock[k] = now() + 0.8                                  # no double shot with a held button
	lock_len[k] = 0.8
	if g == null and base_pts > 0:                         # the guards at MoveEye: like mw_catch
		game.mwg["catches"] = int(game.mwg["catches"]) + 1
		game.mwg["who"][int(hit["slot"])] = true
	hit["no_pic"] = true                                   # the photo of the shutter is the proof (no second photo)
	hit.erase("catch_pts")
	hit["shot_base"] = base_pts                            # Balance: game._caught → score_catch (× REPEAT) - the one rule
	game._say(hit, "🎯 %s hat dich mit dem Auslöser erwischt!" % by, 3.0)
	game._caught(hit, g if g != null else {"name": by})
	hit.erase("no_pic")
	hit.erase("shot_base")
	if base_pts <= 0:
		return {"ok": true, "hit": true, "shutter": true, "pts": 0, "name": hit["name"], "text": "Übung: %s wäre erwischt" % hit["name"]}
	pts = int(hit.get("catch_pts", pts))
	var rep := _rep_txt(int(hit.get("catch_n", rep_n + 1)))
	_alarm(hit, by)
	if g != null:
		game._say(g, "✓ %s erwischt! +%d (%d m, %.1f s)%s" % [hit["name"], pts, int(round(dist)), rt, rep], 3.0)
	_log(true, str(hit["name"]), pts, dist, rt, by, t_round, jpg)
	if lag > 0.0:
		log_[log_.size() - 1]["lag"] = lag
	return {"ok": true, "hit": true, "shutter": true, "pts": pts, "name": hit["name"], "dist": snappedf(dist, 0.1), "rt": snappedf(rt, 0.1),
			"rep": int(hit.get("catch_n", 1)), "text": "✓ %s erwischt! +%d Punkte (%d m, %.1f s)%s" % [hit["name"], pts, int(round(dist)), rt, rep]}


func _alarm(hit: Dictionary, by: String) -> void:
	"""an alarm like a real one of MoveEye: the light, the siren; MoveEye puts the push into its test inbox (world_reply)"""
	var real: bool = game.rules != null and game.rules.real()
	if not real:                                          # «Wie echte Hardware»: MoveEye has no light and no siren
		game.flash_until = max(float(game.flash_until), now() + 6.0)
		_siren.play()
	if main.padmap != null:
		main.padmap.rumble("alarm")                           # 3D-4.13: every controller feels the alarm
	game.news("🚨 Alarm: %s fotografiert (Auslöser von %s) – %sPush ins Test-Postfach" % [hit["name"], by, "" if real else "Licht und Sirene, "])


func _log(is_hit: bool, nm: String, pts: int, dist: float, rt: float, by: String, t_round: float, jpg: PackedByteArray) -> void:
	_id = max(int(Time.get_unix_time_from_system() * 1000.0), _id + 1)
	log_.append({"id": _id, "hit": is_hit, "n": nm, "pts": pts, "d": snappedf(dist, 0.1), "rt": snappedf(rt, 0.1), "by": by.left(30),
			"t": int(t_round), "mode": main.game_mode})
	if _ki_tag != "" and _ki_tag != "off":
		log_[log_.size() - 1]["ki"] = _ki_tag                  # KI-Hilfe: «auto» = fired by the autopilot
	if log_.size() > 6:
		log_.pop_front()
	shots.append(log_[log_.size() - 1].duplicate())
	if not jpg.is_empty():
		jpgs[_id] = jpg
		for old in jpgs.keys():
			if int(old) < int(log_[0]["id"]):
				jpgs.erase(old)


func round_start() -> void:
	lock.clear()
	lock_len.clear()                                       # Balance (point 12): nothing of the last round stays
	log_.clear()
	shots.clear()
	_hist.clear()
	for p in game.players:                                 # Balance: the catch points of this round (score_catch)
		if p != null:
			p.erase("cn")
			p.erase("cpts")
			p.erase("spawn_pos")
	if ki != null:
		ki.round_start()


func report() -> Dictionary:
	"""for the game report (gamelearn.gd «Spielberichte»): the shots of the round"""
	var h := 0
	for s_ in shots:
		h += 1 if bool(s_["hit"]) else 0
	return {"schuesse": shots.size(), "treffer": h, "daneben": shots.size() - h, "radius": radius(), "stufe": glevel(), "liste": shots,
			"ki_hilfe": ki.report() if ki != null else {}}


func command(d: Dictionary) -> Dictionary:
	"""control «game_shut» (for tests): op info | aim {slot, dist, off, posture, hold, safe (s protected), spawn (start
	protection here)} (a runner in front of the head camera) | fire {slot = guard}"""
	var op := str(d.get("op", "info"))
	if op == "ki" and ki != null:                          # KI-Hilfe (gamekihilfe.gd)
		return ki.command(d)
	if op == "aim":
		var sl := int(d.get("slot", 0))
		if sl < 0 or sl >= game.players.size() or game.players[sl] == null:
			return {"ok": false, "error": "no player"}
		var p: Dictionary = game.players[sl]
		var cam: Camera3D = main.cams[0]
		var fw: Vector3 = -cam.global_transform.basis.z
		fw.y = 0.0
		fw = fw.normalized()
		var rt: Vector3 = cam.global_transform.basis.x
		rt.y = 0.0
		rt = rt.normalized()
		var at: Vector3 = cam.global_position + fw * float(d.get("dist", 8.0)) + rt * float(d.get("off", 0.0))
		var ac = p["actor"]
		ac.position = Vector3(at.x, main.ground_y(at.x, at.z), at.z)
		ac.ctl_posture = int(d.get("posture", 0))
		p["safe_until"] = 0.0
		p.erase("spawn_pos")
		if bool(d.get("spawn", false)):                    # Balance tests: here is his start (start protection)
			spawn_protect(p)
		elif float(d.get("safe", 0.0)) > 0.0:              # Balance tests: just caught (protected)
			p["safe_until"] = now() + float(d["safe"])
		if float(d.get("hold", 0.0)) > 0.0:                # a bot stands still for a moment (tests)
			ac.frozen = true
			get_tree().create_timer(float(d["hold"])).timeout.connect(func(): ac.frozen = false)
		return {"ok": true, "pos": [at.x, at.z]}
	if op == "fire":
		var g = null
		if d.has("slot") and int(d["slot"]) >= 0 and int(d["slot"]) < game.players.size():
			g = game.players[int(d["slot"])]
		return fire(g, str(d.get("who", "")))
	var bx := []
	for p in game.players:
		if p != null and p["role"] == "runner":
			bx.append({"slot": p["slot"], "name": p["name"], "box": game.learn.box(p), "sees": game.cam_sees(p, 0), "vis": visible_to(p, 0), "hid": int(p.get("hide_i", -1)), "post": int(p["actor"].ctl_posture), "state": p["state"],
					"caught": p["caught"], "x": snappedf(p["actor"].position.x, 0.1), "z": snappedf(p["actor"].position.z, 0.1)})
	var gp = game.guard_player()
	return {"ok": true, "mode": human_mode(), "ki_used": ki.used_round() if ki != null else false, "mw": info_for(null), "guard": info_for(gp) if gp != null else {}, "log": log_, "runners": bx, "gallery": game.gallery.map(func(x): return x["n"]),
			"flash": game.flash_until > now(), "siren": _siren.playing, "report": report()}


func log_tail() -> Variant:
	"""for MoveEye (world_reply): the last shots - it pushes the hits into its test inbox"""
	return log_ if not log_.is_empty() else null


func pic(id: int) -> PackedByteArray:
	return jpgs.get(id, PackedByteArray())


func _photo(cam_i: int, dd: float, r: float, asp: float) -> PackedByteArray:
	"""the proof: the picture of the camera right now, with the crosshair (circle = hit area) in red"""
	var tex: Texture2D = main.vps[cam_i].get_texture()
	if tex == null:
		return PackedByteArray()
	var img: Image = tex.get_image()
	if img == null or img.is_empty():
		return PackedByteArray()
	if img.get_width() > 640:
		img.resize(640, int(640.0 * img.get_height() / img.get_width()), Image.INTERPOLATE_BILINEAR)
	img.convert(Image.FORMAT_RGB8)
	var w := img.get_width()
	var h := img.get_height()
	var c := Vector2(w / 2.0, h / 2.0)
	var rad: float = r * h
	var red := Color(1.0, 0.23, 0.19)
	for i in range(360):                                  # the circle (3 px)
		var an := TAU * i / 360.0
		for k in [-1.0, 0.0, 1.0]:
			var q: Vector2 = c + Vector2(cos(an), sin(an)) * (rad + float(k))
			if q.x >= 0 and q.y >= 0 and q.x < w and q.y < h:
				img.set_pixelv(Vector2i(q), red)
	var arm: int = int(rad + 14.0)                         # the cross through the middle (3D-4.13: the one crosshair of padhud.gd)
	for i in range(-arm, arm + 1):
		for k in [-1, 0, 1]:
			var px := Vector2i(int(c.x) + i, int(c.y) + k)
			var py := Vector2i(int(c.x) + k, int(c.y) + i)
			if true:
				if px.x >= 0 and px.x < w and px.y >= 0 and px.y < h:
					img.set_pixelv(px, red)
				if py.x >= 0 and py.x < w and py.y >= 0 and py.y < h:
					img.set_pixelv(py, red)
	for x in range(w):                                   # a red frame: «Auslöser»
		for k in range(3):
			img.set_pixel(x, k, red)
			img.set_pixel(x, h - 1 - k, red)
	for y in range(h):
		for k in range(3):
			img.set_pixel(k, y, red)
			img.set_pixel(w - 1 - k, y, red)
	return img.save_jpg_to_buffer(0.75)


func _make_siren() -> AudioStreamWAV:
	"""a short wailing siren (1.6 s), made here - no sound file needed"""
	var rate := 22050
	var n := int(rate * 1.6)
	var data := PackedByteArray()
	data.resize(n * 2)
	var ph := 0.0
	for i in range(n):
		var t := float(i) / rate
		var f := 700.0 + 380.0 * sin(TAU * 1.25 * t)
		ph += TAU * f / rate
		var env: float = min(1.0, t * 20.0) * min(1.0, (1.6 - t) * 10.0)
		var v: float = (sin(ph) + 0.3 * sin(2.0 * ph)) * 0.42 * env
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.stereo = false
	w.data = data
	return w


# ---- the crosshair and the round shutter button on a picture of the simulator ------------------------------------------
func attach(target: TextureRect, cam_of: Callable, press: Callable, big: bool, lock_of := Callable()) -> Control:
	var o := Cross.new()
	o.shut = self
	o.target = target
	o.cam_of = cam_of
	o.press = press
	o.big = big
	o.lock_of = lock_of if lock_of.is_valid() else func(): return lock_left(null)
	target.add_child(o)
	return o


class Cross extends Control:
	var shut
	var target: TextureRect
	var cam_of: Callable
	var press: Callable
	var lock_of: Callable
	var big := false
	var btn: Control
	var shooter: Callable                    # KI-Hilfe: [has a person with the shutter, g] (gamekihilfe.gd)
	var kib: Button                          # KI-Hilfe: the button (aus → Rahmen → zielt → Autopilot)
	var _pic := Rect2()
	var _cam := -1

	func _ready() -> void:
		set_anchors_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		visible = false
		if press.is_valid():
			btn = Control.new()
			btn.mouse_filter = Control.MOUSE_FILTER_STOP
			btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
			btn.tooltip_text = "Auslöser: Schuss auf die Bildmitte (R2)"
			btn.gui_input.connect(_btn_input)
			btn.draw.connect(_btn_draw)
			add_child(btn)

	func _btn_input(ev: InputEvent) -> void:
		var tap: bool = (ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and ev.pressed) or (ev is InputEventScreenTouch and ev.pressed)
		if tap:
			press.call()
			btn.accept_event()

	func _process(_dt: float) -> void:
		_cam = int(cam_of.call()) if cam_of.is_valid() else -1
		var on: bool = _cam >= 0 and target.is_visible_in_tree()
		if visible != on:
			visible = on
		if not on:
			return
		size = target.size
		var ts := Vector2(shut.main.vps[_cam].size)
		var k: float
		if target.stretch_mode == TextureRect.STRETCH_KEEP_ASPECT_COVERED:
			k = max(size.x / ts.x, size.y / ts.y)
		else:
			k = min(size.x / ts.x, size.y / ts.y)
		var ps := ts * k
		_pic = Rect2((size - ps) / 2.0, ps)
		if btn != null:
			var bs: float = (96.0 if big else 46.0)
			var vis := _pic.intersection(Rect2(Vector2.ZERO, size))
			btn.size = Vector2(bs, bs)
			btn.position = vis.position + vis.size - Vector2(bs, bs) - Vector2(18.0, 18.0 + (64.0 if big else 0.0)) * (1.0 if big else 0.4)
			btn.queue_redraw()
			_ki_button()
		queue_redraw()

	func _ki_button() -> void:
		"""KI-Hilfe: the button left of the shutter; click (or key K) = the next help"""
		if not shooter.is_valid():
			return
		if kib == null:
			kib = Button.new()
			kib.focus_mode = Control.FOCUS_NONE
			kib.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
			kib.tooltip_text = "KI-Hilfe für diese Runde (Taste K): aus → KI-Rahmen → KI zielt → KI-Autopilot. Mit KI-Hilfe zählt die Runde nicht für die Rangliste."
			kib.add_theme_font_size_override("font_size", 17 if big else 11)
			kib.pressed.connect(func():
				var s_: Array = shooter.call()
				if bool(s_[0]):
					shut.ki.cycle(s_[1]))
			add_child(kib)
		var s: Array = shooter.call()
		kib.visible = bool(s[0])
		if not kib.visible:
			return
		var ki = shut.ki
		var m: String = ki.mode_of(s[1])
		var tx: String = "KI: aus" if m == "off" else str(ki.NAMES[m])
		var pz: float = ki.paused(s[1])
		if m == "auto" and pz > 0.0:
			tx += " · Pause %d s" % int(ceil(pz))
		elif m != "off" and m != "frame" and s[1] != null and ki._cam(s[1]) != 0:
			tx += " (Weitwinkel-Kamera)"
		if m != "off" and str(ki.boxes(_cam)["src"]) == "sim":
			tx += " · Sim-KI"
		if kib.text != tx:
			kib.text = tx
		kib.modulate = Color(1, 1, 1, 0.75) if m == "off" else Color(0.75, 1.0, 0.8)
		kib.size = kib.get_combined_minimum_size()
		kib.position = btn.position + Vector2(-kib.size.x - (14.0 if big else 6.0), (btn.size.y - kib.size.y) / 2.0)

	func _draw() -> void:
		if _cam < 0:
			return
		if shooter.is_valid():                           # KI-Hilfe: MoveEye's boxes (persons green, uncertain dashed)
			var s: Array = shooter.call()
			if bool(s[0]) and shut.ki.mode_of(s[1]) != "off":
				var lw_: float = 3.0 if big else 2.0
				var gc := Color(0.2, 1.0, 0.4, 0.95)
				var hd: float = shut.ki.hold(s[1])
				for b in shut.ki.boxes(_cam)["b"]:
					var r := Rect2(_pic.position + Vector2(float(b[0]), float(b[1])) * _pic.size, Vector2(float(b[2]), float(b[3])) * _pic.size)
					if bool(b[4]):
						draw_rect(r, gc, false, lw_)
						if hd > 0.0:                         # the autopilot: how long the person is in the circle already
							draw_rect(Rect2(r.position + Vector2(0, r.size.y + 3.0), Vector2(r.size.x * hd, 4.0)), Color(1.0, 0.85, 0.3))
					else:
						var q := [r.position, r.position + Vector2(r.size.x, 0), r.end, r.position + Vector2(0, r.size.y)]
						for i in range(4):
							draw_dashed_line(q[i], q[(i + 1) % 4], Color(0.2, 1.0, 0.4, 0.8), lw_, 8.0)
		var c := _pic.position + _pic.size / 2.0
		var rad: float = shut.radius() * _pic.size.y
		preload("res://scripts/padhud.gd").draw_crosshair(self, c, rad, 3.0 if big else 2.0)   # 3D-4.13: ONE crosshair

	func _btn_draw() -> void:
		var s: Vector2 = btn.size
		var c := s / 2.0
		var r: float = s.x / 2.0 - 3.0
		var left: float = float(lock_of.call()) if lock_of.is_valid() else 0.0
		btn.draw_circle(c, r, Color(0.9, 0.16, 0.14, 0.45 if left > 0.0 else 0.9))
		btn.draw_arc(c, r, 0.0, TAU, 48, Color(1, 1, 1, 0.7), 2.0, true)
		if left > 0.0:                                     # the lock: a ring that runs out
			var f: float = clampf(left / shut.LOCK, 0.0, 1.0)
			btn.draw_arc(c, r - 4.0, -PI / 2.0, -PI / 2.0 + TAU * f, 48, Color(1.0, 0.85, 0.3), 5.0, true)
		if left <= 0.0:                                    # a target (the emoji is not in every font)
			btn.draw_arc(c, r * 0.5, 0.0, TAU, 40, Color.WHITE, 2.5 if big else 1.5, true)
			btn.draw_arc(c, r * 0.24, 0.0, TAU, 32, Color.WHITE, 2.5 if big else 1.5, true)
			btn.draw_circle(c, 2.5 if big else 1.5, Color.WHITE)
			return
		var fnt := btn.get_theme_default_font()
		var fs: int = 30 if big else 16
		var txt := "%d" % int(ceil(left))
		var tw := fnt.get_string_size(txt, HORIZONTAL_ALIGNMENT_CENTER, -1, fs)
		btn.draw_string(fnt, Vector2(c.x - tw.x / 2.0, c.y + fs * 0.36), txt, HORIZONTAL_ALIGNMENT_CENTER, -1, fs, Color.WHITE)
