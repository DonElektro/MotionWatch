extends Node
## 3D-4.x «Mensch gegen KI vergleichen» (Wunsch Daniel, 30.10.2026): the same round is played twice.
##   Round 1: a PERSON guards (spielart «Wächter»: phone / PC, the shutter of gameshutter.gd). Without a person the
##            Bot-Wächter stands in (then it runs without anybody - with bots as sneakers).
##   Round 2: the REAL detection of MoveEye guards (spielart «mw»). Same scene, same seed, and every sneaker walks
##            exactly the way of round 1 (recorded every 0.1 s, like the replay rec of game.gd), the head turns exactly
##            like in round 1 - so MoveEye gets the same pictures the person had.
##   Instead of the recording the sneakers can also walk saved sneaking ways (gamelearn.load_ways, the routes of the
##   test run «spielwege») in both rounds: source «ways».
## Result: «Wer hat mehr erwischt? Mensch 4 · MoveEye 3», per sneaker who was faster, the false alarms. Every situation
## the person caught but MoveEye missed becomes training data: the picture of round 2 with the box of the sneaker as
## «verpasst_NN.jpg» + spielbericht.json in user://spiel/vergleich_<time>/ (dataset.gd puts it into the training pack
## like the missed pictures of gamelearn.gd) and the way up to there as schleichweg_*.json (testrun «spielwege»,
## Prüfstand). MoveEye's false alarms of round 2 go to its fa_learn/ as before (gamelearn.gd «fa_box»).
## Hooks: game.gd _ready (cmp = this), main.gd control «game_compare», gamewiz.gd (card «Mensch gegen KI»).

const REC_EVERY := 0.1
const PAUSE := 8.0                       # seconds between the two rounds (the result of round 1 is shown)
const LATE := 1.0                        # a catch of MoveEye up to 1 s after the catch of the person still counts for that way
const VIS := 0.15                        # like gamelearn.VIS: the head camera sees the sneaker clearly enough
const KEEP := ["game_mode", "game_lives", "game_rescue", "game_events", "game_tutorial", "game_botguard", "game_minutes", "game_bots", "game_ghost"]
const WIZ := ["compare", "⚖", "Mensch gegen KI", "Dieselbe Runde zweimal: zuerst bewacht ein Mensch (Wächter mit Auslöser – oder der Bot-Wächter), dann die echte Erkennung von MoveEye – mit genau denselben Wegen der Schleicher und denselben Kamerabildern. Am Schluss: Wer hat mehr erwischt? Was der Mensch sah und MoveEye verpasste, wird ein Lernbild und ein Prüfstand-Weg."]

var game
var main
var state := "idle"                      # idle | r1 | pause | r2 | done
var armed := false                       # the wizard chose «Mensch gegen KI»: its start plays both rounds
var source := "rec"                      # rec = round 1 is played freely and recorded · ways = saved sneaking ways
var seed_n := 1
var tracks := {}                         # slot -> [[t, x, z, heading, posture, speed, code (1 play, 2 goal, 0 away)], …]
var head: Array = []                     # [[t, yaw, tilt], …] of round 1
var who := {}                            # slot -> {"n", "c", "bot"}
var ev1: Array = []                      # catches of round 1 (the person): {"t", "s", "seg", "snap"}
var ev2: Array = []                      # catches of round 2 (MoveEye): {"t", "s", "seg"}
var vis_t := {}                          # "slot:seg" -> when the head camera saw the sneaker first on this way
var guard1 := {"n": "", "human": false, "false": 0}
var mw_false := 0
var result := {}
var info := ""
var error := ""
var _saved := {}
var _caught_n := {}
var _rec_t := -1.0
var _pause_until := 0.0
var _pics := {}                          # "slot:seg" -> picture of round 2 at the moment the person caught
var _idx := {}                           # slot -> last index in its track (the search goes on from there)
var _hidx := 0
var _was_open := false
var _layer: CanvasLayer
var _panel: PanelContainer
var _label: Label
var _until := 0.0


func now() -> float:
	return game.now()


func busy() -> bool:
	return state in ["r1", "pause", "r2"]


func mw_on() -> bool:
	return main.now() - main.mw_det_t < 3.0


# ---- start / stop ----------------------------------------------------------------------------------------------------
func start(d := {}) -> String:
	"""both rounds: d = {"bots": 0..3, "minutes": 1..15, "source": "rec" | "ways"} - returns an error text or \"\""""
	armed = false
	error = ""
	if busy():
		return "Der Vergleich läuft schon."
	if game.round_state in ["countdown", "play"]:
		return "Zuerst die laufende Runde beenden."
	if not mw_on():
		return "MoveEye ist nicht verbunden – die zweite Runde braucht die echte Erkennung von MoveEye."
	_saved = {}
	for k in KEEP:
		_saved[k] = main.get(k)
	if d.has("minutes"):
		main.game_minutes = clampi(int(d["minutes"]), 1, 15)
	source = "ways" if str(d.get("source", "rec")) == "ways" else "rec"
	if d.has("bots"):
		main.game_bots = clampi(int(d["bots"]), 0, 3)   # before opening: set_open brings main.game_bots along (deferred)
	if not game.open:
		game.set_open(true)
		if not game.open:
			_restore()
			return "Das Spiel konnte nicht geöffnet werden (Port belegt?)."
	game.set_bots(int(main.game_bots))
	if source == "ways":
		var err := _load_ways()
		if err != "":
			_restore()
			return err
	var runners := 0
	for p in game.players:
		if p != null and p["role"] == "runner":
			runners += 1
	if runners == 0:
		_restore()
		return "Niemand schleicht: mindestens einen Bot (oder ein Handy als Läufer) dazunehmen."
	main.game_mode = "guard"
	main.game_lives = 0                                  # both rounds: every catch counts, nobody drops out
	main.game_rescue = false
	main.game_events = false                             # random events would make the two rounds different
	main.game_tutorial = false
	main.game_botguard = true                            # without a person the Bot-Wächter stands in
	main.game_ghost = false
	seed_n = randi() % 1000000 + 1
	if source == "rec":
		tracks.clear()
	head.clear()
	who.clear()
	ev1.clear()
	ev2.clear()
	vis_t.clear()
	_pics.clear()
	result = {}
	mw_false = 0
	var e := _round(1)
	if e != "":
		_restore()
		state = "idle"
		return e
	return ""


func stop(why := "abgebrochen") -> void:
	if not busy():
		return
	state = "idle"
	info = "Vergleich " + why
	if game.round_state in ["countdown", "play"]:
		game.end_round()
	_restore()
	game.news("⚖ Mensch gegen KI: " + why)


func _restore() -> void:
	for k in _saved:
		main.set(k, _saved[k])
	if _saved.has("game_bots") and game.open:
		game.set_bots(int(_saved["game_bots"]))
	_saved = {}


func _round(n: int) -> String:
	seed(seed_n)                                         # the same chance in both rounds (crystals, hiding places, starts …)
	game._rng.seed = seed_n
	main.game_mode = "guard" if n == 1 else "mw"
	game.start_round()
	if game.round_state != "countdown":
		return "Die Runde startet nicht: %s" % (main.start_info if main.start_info != "" else "unbekannt")
	state = "r1" if n == 1 else "r2"
	_caught_n.clear()
	_idx.clear()
	_hidx = 0
	_rec_t = -1.0
	for p in game.players:
		if p == null:
			continue
		p["tut_on"] = false                              # no practice protection - it would make the rounds different
		if p["role"] == "runner":
			_caught_n[int(p["slot"])] = 0
	if n == 1:
		var g = game.guard_player()
		guard1 = {"n": str(g["name"]) if g != null else str(game.bots.GUARD_NAME), "human": g != null, "false": 0}
		for p in game.players:
			if p != null and p["role"] == "runner" and (source == "rec" or tracks.has(int(p["slot"]))):
				who[int(p["slot"])] = {"n": str(p["name"]), "c": "#" + game.COLORS[p["slot"]].to_html(false), "bot": str(p.get("kind", "")) == "bot"}
		info = "Runde 1 von 2: %s bewacht" % guard1["n"]
		game.news("⚖ Mensch gegen KI – Runde 1: %s bewacht. Danach bewacht MoveEye dieselbe Runde." % guard1["n"])
	else:
		info = "Runde 2 von 2: MoveEye bewacht dieselbe Runde"
		game.news("⚖ Runde 2: jetzt bewacht die echte Erkennung von MoveEye – dieselben Wege, dieselben Bilder")
	for p in game.players:
		if p == null:
			continue
		if n == 2 and not tracks.has(int(p["slot"])) and p["role"] == "runner":
			p["state"] = "out"                           # not in round 1 (or the guard of round 1): watches
			p["actor"].visible = false
		if p["sock"] != null:
			game._say(p, ("⚖ Runde 1: %s bewacht – danach MoveEye" % guard1["n"]) if n == 1 else "🔁 Runde 2: MoveEye bewacht – deine Figur läuft deinen Weg von Runde 1 nach, du schaust zu", 6.0)
	return ""


func _load_ways() -> String:
	"""source «ways»: every bot walks one saved sneaking way of this scene (as the test run «spielwege» does)"""
	var ws: Array = preload("res://scripts/gamelearn.gd").load_ways().filter(func(w): return str(w.get("scene", "")) == str(main.scene))
	if ws.is_empty():
		return "Keine gespeicherten Schleichwege für diese Szene – zuerst mit «eigenen Wegen» spielen."
	tracks.clear()
	var i := 0
	for p in game.players:
		if p == null or p["role"] != "runner" or str(p.get("kind", "")) != "bot":
			continue
		var pts: Array = ws[i % ws.size()]["points"]
		var t0 := float(pts[0][0])
		var tr: Array = []
		for k in range(pts.size()):
			var q: Array = pts[k]
			var nx: Array = pts[min(k + 1, pts.size() - 1)]
			var dx := float(nx[1]) - float(q[1])
			var dz := float(nx[2]) - float(q[2])
			var hd: float = 0.0 if tr.is_empty() else float(tr[-1][3])
			if absf(dx) + absf(dz) > 0.01:
				hd = atan2(-dx, -dz)
			tr.append([float(q[0]) - t0, float(q[1]), float(q[2]), hd, int(q[3]), float(q[4]) if q.size() > 4 else 1.0, 1])
		tracks[int(p["slot"])] = tr
		i += 1
	if tracks.is_empty():
		return "Für «Schleichwege» braucht es mindestens einen Bot."
	return ""


# ---- every frame -----------------------------------------------------------------------------------------------------
func _process(_dt: float) -> void:
	if _panel != null and _panel.visible and now() > _until:
		_panel.visible = false
	if not busy():
		return
	if not game.open:
		stop("abgebrochen (Spiel geschlossen)")
		return
	var rs: String = game.round_state
	var t: float = now() - game.t_start
	if state == "pause":
		if now() >= _pause_until:
			var e := _round(2)
			if e != "":
				error = e
				stop("abgebrochen: " + e)
		return
	if rs in ["countdown", "play"]:
		if state == "r1":
			if rs == "play":
				_record(t)
			if source == "ways":
				_drive(max(t, 0.0))
		else:
			_drive(max(t, 0.0))
			if rs == "play":
				_snaps(t)
				if t > _last_t() + 1.5:
					game.end_round()                     # the recording is over (round 1 was stopped early)
		if rs == "play":
			_catches(t)
		return
	if state == "r1":                                    # round 1 is over
		var g = game.guard_player()
		guard1["false"] = int(g["false"]) if g != null else int(game.bots.guard.get("false", 0))
		state = "pause"
		_pause_until = now() + PAUSE
		info = "Runde 1 vorbei: %s hat %d× erwischt – gleich bewacht MoveEye dieselbe Runde" % [guard1["n"], ev1.size()]
		game.news("⚖ " + info)
		for p in game.players:
			if p != null and p["sock"] != null:
				game._say(p, "⚖ " + info, PAUSE)
	else:
		mw_false = game.learn.mw_false.size()
		_finish()


func _last_t() -> float:
	var m := 0.0
	for s in tracks:
		if not tracks[s].is_empty():
			m = max(m, float(tracks[s][-1][0]))
	return m


func _record(t: float) -> void:
	if t - _rec_t < REC_EVERY:
		return
	_rec_t = t
	head.append([snappedf(t, 0.01), snappedf(main.head.rotation.y, 0.001), snappedf(main.head_pitch.rotation.x, 0.001)])
	for p in game.players:
		if p == null or p["role"] != "runner" or not who.has(int(p["slot"])):
			continue
		var s := int(p["slot"])
		var a = p["actor"]
		if source == "rec":
			if not tracks.has(s):
				tracks[s] = []
			var code := 1 if p["state"] == "play" else (2 if p["state"] == "goal" else 0)
			tracks[s].append([snappedf(t, 0.01), snappedf(a.position.x, 0.01), snappedf(a.position.z, 0.01), snappedf(float(a.heading), 0.01),
					int(a.ctl_posture), snappedf(float(a.cur_speed), 0.01), code])
		var k := "%d:%d" % [s, _seg(s, t)]
		if not vis_t.has(k) and p["state"] == "play" and game.cam_sees(p, 0) >= VIS:
			vis_t[k] = snappedf(t, 0.1)


func _seg(s: int, t: float) -> int:
	"""the way number of a sneaker: how often the person had caught him up to t"""
	var n := 0
	for e in ev1:
		if int(e["s"]) == s and float(e["t"]) <= t:
			n += 1
	return n


func _sample(tr: Array, s: int, t: float) -> Array:
	var i: int = clampi(int(_idx.get(s, 0)), 0, tr.size() - 1)
	if float(tr[i][0]) > t:
		i = 0
	while i + 1 < tr.size() and float(tr[i + 1][0]) <= t:
		i += 1
	_idx[s] = i
	var a: Array = tr[i]
	if i + 1 >= tr.size():
		return a
	var b: Array = tr[i + 1]
	var dt_: float = float(b[0]) - float(a[0])
	var f: float = clampf((t - float(a[0])) / dt_, 0.0, 1.0) if dt_ > 0.0 else 0.0
	if Vector2(float(b[1]) - float(a[1]), float(b[2]) - float(a[2])).length() > 3.0:
		return a                                         # back to the start after a catch: a jump, not a walk
	return [t, lerpf(float(a[1]), float(b[1]), f), lerpf(float(a[2]), float(b[2]), f), lerp_angle(float(a[3]), float(b[3]), f), a[4], lerpf(float(a[5]), float(b[5]), f), a[6]]


func _drive(t: float) -> void:
	"""round 2 (and both rounds with saved ways): the figures walk the recorded way, the head turns as in round 1"""
	if state == "r2" and not head.is_empty():
		while _hidx + 1 < head.size() and float(head[_hidx + 1][0]) <= t:
			_hidx += 1
		var h: Array = head[_hidx]
		game.guard_auto = true                           # main.gd: the head follows guard_yaw / guard_tilt
		game.guard_yaw = float(h[1])
		game.guard_tilt = float(h[2])
	for s in tracks:
		var p = game.players[int(s)]
		if p == null or not who.has(int(s)) or str(p["name"]) != str(who[s]["n"]) or tracks[s].is_empty():
			continue
		var q: Array = _sample(tracks[s], int(s), t)
		var a = p["actor"]
		a.position.x = float(q[1])
		a.position.z = float(q[2])
		a.heading = float(q[3])
		a.rotation.y = float(q[3])
		a.ctl_posture = int(q[4])
		a.cur_speed = float(q[5])
		a.ctl_move = Vector2.ZERO
		a.frozen = game.round_state != "play"
		p["mx"] = 0.0
		p["my"] = 0.0
		if game.round_state == "play" and state == "r2":
			var code := int(q[6])
			p["state"] = "play" if code == 1 else ("goal" if code == 2 else "out")
			a.visible = code != 0


func _catches(t: float) -> void:
	for p in game.players:
		if p == null or not _caught_n.has(int(p["slot"])):
			continue
		var s := int(p["slot"])
		var c := int(p["caught"])
		if c <= int(_caught_n[s]):
			continue
		_caught_n[s] = c
		if state == "r1":
			ev1.append({"t": snappedf(t, 0.1), "s": s, "seg": _seg(s, t), "snap": false})
		else:
			var sg := _seg(s, t - LATE)
			ev2.append({"t": snappedf(t, 0.1), "s": s, "seg": sg})


func _snaps(t: float) -> void:
	"""round 2: just before the moment the person caught somebody, the picture of MoveEye's camera is kept - it becomes
	a training picture if MoveEye does not catch him on this way"""
	for e in ev1:
		if bool(e["snap"]) or t < float(e["t"]) - 0.45:
			continue
		e["snap"] = true
		var p = game.players[int(e["s"])]
		if p == null:
			continue
		var b: Array = game.learn.box(p)
		if b.is_empty() or game.cam_sees(p, 0) <= 0.02:
			continue                                     # not in the picture of the head camera (the fixed camera saw him)
		var a = p["actor"]
		var k := "%d:%d" % [int(e["s"]), int(e["seg"])]
		var rec := {"n": str(p["name"]), "box": b, "why": "Mensch erwischt, MoveEye nicht", "dist": snappedf(main.cams[0].global_position.distance_to(a.position), 0.1),
				"post": int(a.ctl_posture), "dark": main.is_dark(), "weather": str(main.weather), "t": snappedf(float(e["t"]), 0.1)}
		main.want_snapshot(0)
		get_tree().create_timer(0.3).timeout.connect(func():
			var b2: Array = game.learn.box(p)
			if not b2.is_empty():
				rec["box"] = b2
			var j: PackedByteArray = main.latest_jpg(0)
			if j.size() > 100:
				rec["jpg"] = j
				_pics[k] = rec)


# ---- the result ------------------------------------------------------------------------------------------------------
func _finish() -> void:
	state = "done"
	var mw_segs := {}
	for e in ev2:
		mw_segs["%d:%d" % [int(e["s"]), int(e["seg"])]] = true
	var per: Array = []
	for s in who:
		var h1 = null
		var m1 = null
		var hn := 0
		var mn := {}
		for e in ev1:
			if int(e["s"]) == int(s):
				hn += 1
				if h1 == null:
					h1 = e
		for e in ev2:
			if int(e["s"]) == int(s):
				mn[int(e["seg"])] = true
				if m1 == null:
					m1 = e
		var rh := -1.0
		var rm := -1.0
		if h1 != null:
			rh = maxf(0.0, float(h1["t"]) - float(vis_t.get("%d:%d" % [int(s), int(h1["seg"])], h1["t"])))
		if m1 != null:
			rm = maxf(0.0, float(m1["t"]) - float(vis_t.get("%d:%d" % [int(s), int(m1["seg"])], m1["t"])))
		var faster := ""
		if h1 != null and m1 != null:
			faster = "human" if float(h1["t"]) < float(m1["t"]) - 0.05 else ("mw" if float(m1["t"]) < float(h1["t"]) - 0.05 else "same")
		elif h1 != null:
			faster = "human"
		elif m1 != null:
			faster = "mw"
		per.append({"n": who[s]["n"], "c": who[s]["c"], "bot": who[s]["bot"], "human": hn, "mw": mn.size(),
				"t_human": float(h1["t"]) if h1 != null else -1.0, "t_mw": float(m1["t"]) if m1 != null else -1.0,
				"rt_human": snappedf(rh, 0.1), "rt_mw": snappedf(rm, 0.1), "faster": faster})
	var missed: Array = []
	for e in ev1:
		if not mw_segs.has("%d:%d" % [int(e["s"]), int(e["seg"])]):
			missed.append(e)
	var mw_n := 0
	for k in mw_segs:
		mw_n += 1
	var saved := _save(missed, per)
	var hum_n := ev1.size()
	var head_ := "Wer hat mehr erwischt? %s %d · MoveEye %d" % ["Mensch" if guard1["human"] else "Bot-Wächter", hum_n, mw_n]
	var win := "Gleichstand" if hum_n == mw_n else (("Der Mensch" if guard1["human"] else "Der Bot-Wächter") + " gewinnt" if hum_n > mw_n else "MoveEye gewinnt")
	result = {"title": head_, "win": win, "human": hum_n, "mw": mw_n, "guard": guard1["n"], "guard_human": guard1["human"],
			"false_human": int(guard1["false"]), "false_mw": mw_false, "per": per, "missed": missed.size(), "pics": int(saved[0]), "ways": int(saved[1]),
			"dir": str(saved[2]), "scene": str(main.scene), "seed": seed_n, "source": source, "date": Time.get_datetime_string_from_system(false, true)}
	info = "%s – %s" % [head_, win]
	_restore()
	game.news("⚖ " + info)
	if missed.size() > 0:
		game.news("🧠 %d Situationen hat der Mensch gesehen, MoveEye nicht: %d Lernbilder, %d Prüfstand-Wege gespeichert" % [missed.size(), int(saved[0]), int(saved[1])])
	for p in game.players:
		if p != null and p["sock"] != null:
			game._say(p, "⚖ %s – %s" % [head_, win], 15.0)
	_show()


func _safe(s: String) -> String:
	var o := ""
	for ch in s.to_lower():
		o += ch if ch in "abcdefghijklmnopqrstuvwxyz0123456789" else "_"
	return o.left(20)


func _save(missed: Array, per: Array) -> Array:
	"""the training pictures (like gamelearn.gd «verpasst»: dataset.gd takes them into the pack) and the ways (Prüfstand)"""
	var rid := "vergleich_" + Time.get_datetime_string_from_system(false, true).replace(":", "").replace(" ", "_").replace("-", "")
	var dir := "user://spiel/" + rid
	DirAccess.make_dir_recursive_absolute(dir)
	var pics: Array = []
	var n_ways := 0
	for e in missed:
		var k := "%d:%d" % [int(e["s"]), int(e["seg"])]
		if _pics.has(k):
			var rec: Dictionary = _pics[k].duplicate()
			var fn := "verpasst_%02d.jpg" % (pics.size() + 1)
			var f := FileAccess.open(dir + "/" + fn, FileAccess.WRITE)
			if f != null:
				f.store_buffer(rec["jpg"])
				f.close()
				rec.erase("jpg")
				rec["file"] = fn
				pics.append(rec)
		if not tracks.has(e["s"]):
			continue
		var pts: Array = []                              # the way of this sneaker up to the catch, every 0.5 s
		var last := -9.0
		for q in tracks[e["s"]]:
			if float(q[0]) > float(e["t"]):
				break
			if _seg(int(e["s"]), float(q[0])) != int(e["seg"]) or float(q[0]) - last < 0.5 or int(q[6]) != 1:
				continue
			last = float(q[0])
			pts.append([snappedf(float(q[0]), 0.1), snappedf(float(q[1]), 0.01), snappedf(float(q[2]), 0.01), int(q[4]), snappedf(float(q[5]), 0.01)])
		if pts.size() < 6:
			continue
		var w := {"v": 1, "name": str(who[e["s"]]["n"]), "date": Time.get_datetime_string_from_system(false, true), "scene": main.scene,
				"hour": snappedf(main.hour(), 0.1), "weather": str(main.weather), "wind": snappedf(float(main.wind), 1.0), "from": "Mensch gegen KI",
				"why": "Mensch erwischt nach %.1f s, MoveEye nicht" % float(e["t"]), "points": pts}
		var fw := FileAccess.open(dir + "/schleichweg_vergleich_%s_%d.json" % [_safe(str(who[e["s"]]["n"])), int(e["seg"]) + 1], FileAccess.WRITE)
		if fw != null:
			fw.store_string(JSON.stringify(w))
			fw.close()
			n_ways += 1
	var rep := {"v": 1, "art": "vergleich", "verpasst": pics, "vergleich": {"human": ev1.size(), "mw_events": ev2.size(), "per": per, "seed": seed_n,
			"scene": main.scene, "guard": guard1["n"]}}
	var fr := FileAccess.open(dir + "/spielbericht.json", FileAccess.WRITE)
	if fr != null:
		fr.store_string(JSON.stringify(rep, " "))
		fr.close()
	return [pics.size(), n_ways, rid]


# ---- the result screen in this window --------------------------------------------------------------------------------
func text() -> String:
	if result.is_empty():
		return info
	var t: String = "⚖ %s\n%s\n" % [result["title"], result["win"]]
	for r in result["per"]:
		var f: String = {"human": "Mensch schneller", "mw": "MoveEye schneller", "same": "gleich schnell"}.get(str(r["faster"]), "keiner hat ihn erwischt")
		if str(r["faster"]) == "human" and not bool(result["guard_human"]):
			f = "Bot-Wächter schneller"
		t += "\n%s: %s %d · MoveEye %d – %s" % [r["n"], "Mensch" if result["guard_human"] else "Bot", int(r["human"]), int(r["mw"]), f]
		if float(r["rt_human"]) >= 0.0 or float(r["rt_mw"]) >= 0.0:
			t += " (%s / %s)" % ["%.1f s" % float(r["rt_human"]) if int(r["human"]) > 0 else "–", "%.1f s" % float(r["rt_mw"]) if int(r["mw"]) > 0 else "–"]
	t += "\n\nFehlalarme: %s %d · MoveEye %d" % ["Mensch" if result["guard_human"] else "Bot", int(result["false_human"]), int(result["false_mw"])]
	if int(result["missed"]) > 0:
		t += "\n🧠 Mensch sah, MoveEye nicht: %d× → %d Lernbilder, %d Prüfstand-Wege" % [int(result["missed"]), int(result["pics"]), int(result["ways"])]
	return t


func _show() -> void:
	if _layer == null:
		_layer = CanvasLayer.new()
		_layer.layer = 60
		add_child(_layer)
		_panel = PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.05, 0.07, 0.1, 0.94)
		sb.border_color = Color(0.23, 0.55, 1.0)
		sb.set_border_width_all(2)
		sb.set_corner_radius_all(14)
		sb.set_content_margin_all(18)
		_panel.add_theme_stylebox_override("panel", sb)
		_panel.set_anchors_preset(Control.PRESET_CENTER)
		_layer.add_child(_panel)
		var v := VBoxContainer.new()
		_panel.add_child(v)
		_label = Label.new()
		_label.add_theme_font_size_override("font_size", 18)
		_label.custom_minimum_size = Vector2(520, 0)
		_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(_label)
		var b := Button.new()
		b.text = "Schliessen"
		b.pressed.connect(func(): _panel.visible = false)
		v.add_child(b)
	_label.text = text()
	_panel.visible = true
	_panel.reset_size()
	_panel.position = (_panel.get_viewport_rect().size - _panel.size) / 2.0
	_until = now() + 90.0


# ---- the wizard (gamewiz.gd) and MoveEye (control «game_compare») ------------------------------------------------------
func wiz_card(on: bool) -> Dictionary:
	var tx: String = WIZ[3]
	if not mw_on():
		tx += " ⚠ MoveEye ist gerade nicht verbunden."
	return {"v": WIZ[0], "icon": WIZ[1], "title": WIZ[2], "text": tx, "on": on, "pic": ""}


func wiz_apply(W: Dictionary) -> void:
	"""the wizard takes over its settings: «compare» is played as «Wächter» (round 1), the start then runs both rounds"""
	armed = str(W.get("game_mode", "")) == "compare"
	if armed:
		W["game_mode"] = "guard"


func state_dict() -> Dictionary:
	var left := 0.0
	if state in ["r1", "r2"] and game.round_state in ["countdown", "play"]:
		left = maxf(0.0, game.t_end - now())
	elif state == "pause":
		left = maxf(0.0, _pause_until - now())
	return {"ok": true, "state": state, "round": 1 if state == "r1" else (2 if state == "r2" else 0), "info": info, "error": error,
			"left_s": int(left), "mw": mw_on(), "open": game.open, "bots": int(main.game_bots), "minutes": int(main.game_minutes),
			"result": result, "text": text() if not result.is_empty() else "", "ways_n": preload("res://scripts/gamelearn.gd").load_ways().filter(func(w): return str(w.get("scene", "")) == str(main.scene)).size()}


func command(d: Dictionary) -> Dictionary:
	"""control «game_compare»: op state | start {bots, minutes, source} | stop"""
	var op := str(d.get("op", "state"))
	if op == "start":
		var e := start(d)
		var st := state_dict()
		if e != "":
			st["ok"] = false
			st["error"] = e
		return st
	if op == "stop":
		stop()
	return state_dict()
