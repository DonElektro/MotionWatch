extends Node
# 3D-3.52: the game teaches MoveEye. While a round runs with MoveEye connected, this compares what the head
# camera really sees (the players, game.cam_sees) with what MoveEye reports (main.mw_det.persons):
#  - «verpasste Personen»: a player the hunter hit (or who was visible for a while) but MoveEye did not report ->
#    picture of the head camera + box of the player (training pictures of exactly the hard cases)
#  - «Spielbericht»: every time a player is visible: how long until MoveEye reported him (distance, posture, light)
#  - «Schleichwege»: the way of a player who reached the goal without being reported -> a fixed test run for the bench
#  - «blinde Flecken»: points for every second a player was visible but not reported
# Everything is saved in user://spiel/ and can be sent with «Spielbericht senden» (GitHub key of the test bench, or the desktop).

var main
var game

const VIS := 0.15                         # the head camera sees the player clearly enough (game.cam_sees)
const REPORT_GRACE := 1.5                 # a report up to ... s after the player was visible still counts
const MISS_AFTER := 3.0                   # visible this long and not reported: a «missed» picture
const MAX_MISS := 30                      # pictures per round at most

var round_id := ""
var eps: Array = []                       # finished episodes {"n", "t", "dur", "lat", "dist", "post", "dark", "px", "weather"}
var open_ep := {}                         # slot -> running episode
var misses: Array = []                    # {"file", "n", "box": [x, y, w, h] (0..1), "why", "dist", "post", "dark", "t"}
var paths := {}                           # slot -> [[t, x, z, posture, speed], …]
var blind := {}                           # slot -> seconds visible but not reported
var blind_pts: Array = []                 # 3D-3.90: where (az° to the head, m) players were visible but not reported - all rounds
var _bp_t := {}
var _zc_t := {}
const BLIND_FILE := "user://spiel/blinde_flecken.json"
var hunter := {"shots": 0, "hits": 0, "miss_mw": 0}
var _path_t := 0.0
var _last_report := -100.0
var _rep_by := {}                         # 3D-3.53: slot -> last time MoveEye reported exactly this player (its boxes)
var mw_false: Array = []                  # boxes MoveEye reported where no player was {"t", "box"}
var _false_t := 0.0
var info := ""
var http: HTTPRequest
var saved_by: Array = []                  # 3D-4.x: names whose sneaking way was saved in this round (learning points, gameplus.gd)


func _ready() -> void:
	http = HTTPRequest.new()
	add_child(http)
	var bp = JSON.parse_string(FileAccess.get_file_as_string(BLIND_FILE)) if FileAccess.file_exists(BLIND_FILE) else null
	if typeof(bp) == TYPE_ARRAY:
		blind_pts = bp


func now() -> float:
	return game.now()                                     # the clock of the game (t_start), not the one of main


func mw_on() -> bool:
	return main.now() - main.mw_det_t < 3.0


func any_on() -> bool:
	return main.game_learn_miss or main.game_learn_report or main.game_learn_paths or main.game_blind_bonus


func round_start() -> void:
	round_id = Time.get_datetime_string_from_system(false, true).replace(":", "").replace(" ", "_").replace("-", "")
	eps.clear()
	open_ep.clear()
	misses.clear()
	paths.clear()
	_rep_by.clear()
	mw_false.clear()
	blind.clear()
	saved_by.clear()
	hunter = {"shots": 0, "hits": 0, "miss_mw": 0}
	_path_t = 0.0


func tick(dt: float) -> void:
	"""every 0.2 s while a round is played (from game._referee)"""
	if not any_on() or not mw_on():
		return
	var t := now()
	if int(main.mw_det.get("persons", 0)) > 0:
		_last_report = t
	var mwb: Array = mw_boxes()
	if not mwb.is_empty():                                # 3D-3.53: which player is meant (MoveEye 2.95.75 sends boxes)
		var used := {}
		for p in game.players:
			if p == null or p["role"] != "runner" or p["state"] != "play":
				continue
			var pb := box(p)
			for i in range(mwb.size()):
				if not pb.is_empty() and overlap(pb, mwb[i]):
					_rep_by[int(p["slot"])] = t
					used[i] = true
		if t - _false_t > 2.0:
			for i in range(mwb.size()):
				if not used.has(i) and not _visitor_at(mwb[i]) and mw_false.size() < 20:
					mw_false.append({"t": snappedf(t - game.t_start, 0.1), "box": mwb[i]})
					_false_t = t
					# 3D-3.92: MoveEye keeps this spot of its picture as a «no person» example (false alarm learning)
					main.mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1), "op": "fa_box", "box": mwb[i]}
	_path_t -= dt
	var rec_path: bool = _path_t <= 0.0
	if rec_path:
		_path_t = 0.5
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play":
			continue
		var s := int(p["slot"])
		var a = p["actor"]
		if rec_path and main.game_learn_paths:
			if not paths.has(s):
				paths[s] = []
			paths[s].append([snappedf(t - game.t_start, 0.1), snappedf(a.position.x, 0.01), snappedf(a.position.z, 0.01), int(a.ctl_posture), snappedf(float(a.cur_speed), 0.01)])
		var f: float = game.cam_sees(p, 0)
		var vis: bool = f >= VIS
		var reported: bool = reported_for(p)
		if vis and not reported:
			blind[s] = float(blind.get(s, 0.0)) + dt
			if t > float(_bp_t.get(s, 0.0)):              # 3D-3.90: one point per second for MoveEye's map of blind spots
				_bp_t[s] = t + 1.0
				var hp: Vector3 = main.head.global_position
				var off: Vector3 = a.position - hp
				var fw3: Vector3 = -(main.cams[0] as Camera3D).global_transform.basis.z      # like blindmap.gd: az relative to the head
				var az := rad_to_deg(wrapf(atan2(off.x, -off.z) - atan2(fw3.x, -fw3.z), -PI, PI))
				blind_pts.append({"az": snappedf(az, 1.0), "d": snappedf(Vector2(off.x, off.z).length(), 0.1), "dark": main.is_dark(), "scene": str(main.scene)})
				if blind_pts.size() > 400:
					blind_pts.pop_front()
		if main.game_mode == "free" and t > float(_zc_t.get(s, 0.0)):   # 3D-3.90: «Zonen-Check» - the player hears what MoveEye sees
			_zc_t[s] = t + 0.6
			game._say(p, "👁 MoveEye sieht dich" if reported else ("🙈 Im Bild – MoveEye meldet dich NICHT" if vis else "· ausser Sicht der Kamera"), 0.8)
		if vis:
			if not open_ep.has(s):
				open_ep[s] = {"n": p["name"], "t": t, "lat": -1.0, "dist": snappedf(_dist(a), 0.1), "post": int(a.ctl_posture),
						"dark": main.is_dark(), "px": int(_px(p)), "weather": str(main.weather), "shot": false}
				open_ep[s].merge(_tags(p))                # 3D-4.x: weather phase and camouflage thing (gameplus.gd)
			var e: Dictionary = open_ep[s]
			if reported and float(e["lat"]) < 0.0:
				e["lat"] = snappedf(t - float(e["t"]), 0.1)
			if float(e["lat"]) < 0.0 and not bool(e["shot"]) and t - float(e["t"]) >= MISS_AFTER and main.game_learn_miss:
				e["shot"] = true                          # one picture per episode
				_miss_pic(p, "sichtbar %d s, nicht gemeldet" % int(t - float(e["t"])))
		elif open_ep.has(s) and t - float(open_ep[s]["t"]) > 0.0:
			_close(s, t)


func _close(s: int, t: float) -> void:
	var e: Dictionary = open_ep[s]
	open_ep.erase(s)
	e["dur"] = snappedf(t - float(e["t"]), 0.1)
	if float(e["dur"]) < 0.6:                             # a glimpse: not an episode
		return
	e["t"] = snappedf(float(e["t"]) - game.t_start, 0.1)
	eps.append(e)


func _dist(a) -> float:
	return main.cams[0].global_position.distance_to(a.position)


func _px(p: Dictionary) -> float:
	var b := box(p)
	return b[3] * float(main.vps[0].size.y) if not b.is_empty() else 0.0


func box(p: Dictionary) -> Array:
	"""where the player is in the picture of the head camera: [x, y, w, h] as 0..1, or [] if not in front of it"""
	var cam: Camera3D = main.cams[0]
	var a = p["actor"]
	var h: float = game.HEIGHT[int(a.ctl_posture)]
	var pos: Vector3 = a.position
	var top := pos + Vector3(0, h, 0)
	if cam.is_position_behind(top) or cam.is_position_behind(pos):
		return []
	var vs: Vector2 = Vector2(main.vps[0].size)
	var p1: Vector2 = cam.unproject_position(top) / vs
	var p2: Vector2 = cam.unproject_position(pos) / vs
	var right: Vector3 = cam.global_transform.basis.x
	var p3: Vector2 = cam.unproject_position(pos + Vector3(0, h * 0.5, 0) + right * 0.35) / vs
	var p4: Vector2 = cam.unproject_position(pos + Vector3(0, h * 0.5, 0) - right * 0.35) / vs
	var x0: float = min(min(p1.x, p2.x), min(p3.x, p4.x))
	var x1: float = max(max(p1.x, p2.x), max(p3.x, p4.x))
	var y0: float = min(p1.y, p2.y)
	var y1: float = max(p1.y, p2.y)
	if x1 < 0.0 or x0 > 1.0 or y1 < 0.0 or y0 > 1.0:
		return []
	x0 = clampf(x0, 0.0, 1.0)
	x1 = clampf(x1, 0.0, 1.0)
	y0 = clampf(y0, 0.0, 1.0)
	y1 = clampf(y1, 0.0, 1.0)
	return [snappedf(x0, 0.001), snappedf(y0, 0.001), snappedf(x1 - x0, 0.001), snappedf(y1 - y0, 0.001)]


func on_shot(hit, reported_recently: bool) -> void:
	"""the hunter fired (button or tap): hit = the player or null"""
	hunter["shots"] = int(hunter["shots"]) + 1
	if hit == null:
		return
	hunter["hits"] = int(hunter["hits"]) + 1
	if not reported_recently and mw_on():
		hunter["miss_mw"] = int(hunter["miss_mw"]) + 1
		if main.game_learn_miss:
			_miss_pic(hit, "vom Jäger getroffen, nicht gemeldet")


func reported_recently(p = null) -> bool:
	if p != null:
		return reported_for(p)
	return now() - _last_report < REPORT_GRACE or int(main.mw_det.get("persons", 0)) > 0


func has_boxes() -> bool:
	"""MoveEye 2.95.75 or newer: it sends where the persons are"""
	return main.mw_det.has("boxes")


func mw_boxes() -> Array:
	var out: Array = []
	var b = main.mw_det.get("boxes", [])
	if typeof(b) == TYPE_ARRAY:
		for x in b:
			if typeof(x) == TYPE_ARRAY and x.size() == 4:
				out.append([float(x[0]), float(x[1]), float(x[2]), float(x[3])])
	return out


func overlap(a: Array, b: Array) -> bool:
	"""the same figure? the boxes overlap clearly, or the centre of one lies in the other"""
	var ix: float = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
	var iy: float = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
	var inter: float = ix * iy
	var uni: float = a[2] * a[3] + b[2] * b[3] - inter
	if uni > 0.0 and inter / uni > 0.1:
		return true
	var cx: float = b[0] + b[2] / 2.0
	var cy: float = b[1] + b[3] / 2.0
	return cx >= a[0] and cx <= a[0] + a[2] and cy >= a[1] and cy <= a[1] + a[3]


func reported_for(p: Dictionary) -> bool:
	"""did MoveEye report this player just now? With boxes exactly him, otherwise any person"""
	if has_boxes():
		return now() - float(_rep_by.get(int(p["slot"]), -100.0)) < REPORT_GRACE
	return now() - _last_report < REPORT_GRACE


func _visitor_at(b: Array) -> bool:
	"""a visitor of the simulation (person or animal) is there: not a false alarm of the game"""
	var cam: Camera3D = main.cams[0]
	var vs: Vector2 = Vector2(main.vps[0].size)
	for v in main.visitors.get_children():
		if cam.is_position_behind(v.position):
			continue
		var q: Vector2 = cam.unproject_position(v.position + Vector3(0, 0.5, 0)) / vs
		if q.x >= b[0] - 0.05 and q.x <= b[0] + b[2] + 0.05 and q.y >= b[1] - 0.1 and q.y <= b[1] + b[3] + 0.1:
			return true
	return false



func _tags(p: Dictionary) -> Dictionary:
	"""3D-4.x: under which conditions (weather change before / after, the conditions now) and with which camouflage thing"""
	if game.plus == null:
		return {}
	var d := {"cond": game.plus.cond_now()}
	if game.plus.phase() != "":
		d["wx"] = game.plus.phase()
	if game.plus.gear_of(p) != "":
		d["gear"] = game.plus.gear_of(p)
	return d


func _miss_pic(p: Dictionary, why: String) -> void:
	if misses.size() >= MAX_MISS:
		return
	var b := box(p)
	if b.is_empty():
		return
	var a = p["actor"]
	var rec := {"n": p["name"], "box": b, "why": why, "dist": snappedf(_dist(a), 0.1), "post": int(a.ctl_posture),
			"dark": main.is_dark(), "weather": str(main.weather), "t": snappedf(now() - game.t_start, 0.1)}
	rec.merge(_tags(p))
	main.want_snapshot(0)
	get_tree().create_timer(0.35).timeout.connect(func():
		var b2 := box(p)                                  # where the player is when the picture is taken
		if not b2.is_empty():
			rec["box"] = b2
		_save_pic(rec))


func _save_pic(rec: Dictionary) -> void:
	var j: PackedByteArray = main.latest_jpg(0)
	if j.size() < 100:
		return
	var dir := "user://spiel/" + round_id
	DirAccess.make_dir_recursive_absolute(dir)
	var fn := "verpasst_%02d.jpg" % (misses.size() + 1)
	var f := FileAccess.open(dir + "/" + fn, FileAccess.WRITE)
	if f == null:
		return
	f.store_buffer(j)
	f.close()
	rec["file"] = fn
	misses.append(rec)


func bonus(p: Dictionary) -> int:
	"""points for the blind spots of MoveEye: 20 per second visible but not reported (at most 600)"""
	if not main.game_blind_bonus:
		return 0
	return min(600, int(float(blind.get(int(p["slot"]), 0.0)) * 20.0))


func blind_s(p: Dictionary) -> int:
	return int(float(blind.get(int(p["slot"]), 0.0)))


func round_end() -> void:
	"""end of the round: close the episodes, save the report and the sneaking ways"""
	if not blind_pts.is_empty():                           # 3D-3.90: the blind spots of all rounds stay
		DirAccess.make_dir_recursive_absolute("user://spiel")
		var fb := FileAccess.open(BLIND_FILE, FileAccess.WRITE)
		if fb != null:
			fb.store_string(JSON.stringify(blind_pts))
			fb.close()
	if round_id == "" or not any_on():
		return
	var t := now()
	for s in open_ep.keys():
		_close(int(s), t)
	if eps.is_empty() and misses.is_empty() and paths.is_empty() and int(hunter["shots"]) == 0:
		return
	var dir := "user://spiel/" + round_id
	DirAccess.make_dir_recursive_absolute(dir)
	var saved_paths := 0
	if main.game_learn_paths:
		for p in game.players:
			if p == null or p["role"] != "runner" or not paths.has(int(p["slot"])):
				continue
			var reached: bool = float(p.get("t_goal", 0.0)) > 0.0 and int(p["caught"]) == 0
			var unseen: bool = true
			for e in eps:
				if e["n"] == p["name"] and float(e["lat"]) >= 0.0:
					unseen = false
			if reached and unseen and paths[int(p["slot"])].size() >= 6:
				var w := {"v": 1, "name": p["name"], "date": Time.get_datetime_string_from_system(false, true), "scene": main.scene,
						"hour": snappedf(main.hour(), 0.1), "weather": str(main.weather), "wind": snappedf(float(main.wind), 1.0),
						"blind_s": blind_s(p), "points": paths[int(p["slot"])]}
				var fw := FileAccess.open(dir + "/schleichweg_%s.json" % _safe(p["name"]), FileAccess.WRITE)
				if fw != null:
					fw.store_string(JSON.stringify(w))
					fw.close()
					saved_paths += 1
					saved_by.append(str(p["name"]))
	var rep := report_dict()
	rep["schleichwege"] = saved_paths
	if main.game_learn_report or not misses.is_empty():
		var fr := FileAccess.open(dir + "/spielbericht.json", FileAccess.WRITE)
		if fr != null:
			fr.store_string(JSON.stringify(rep, " "))
			fr.close()
	info = "Spielbericht gespeichert: %d× sichtbar, %d verpasste Bilder, %d Schleichwege" % [eps.size(), misses.size(), saved_paths]
	game.news("📊 " + info)


func _safe(s: String) -> String:
	var o := ""
	for c in s:
		o += c if c.is_valid_identifier() or c.is_valid_int() else "_"
	return o.left(20)


func report_dict() -> Dictionary:
	var n := 0
	var found := 0
	var lats: Array = []
	var bands := {"nah": [0, 0], "mittel": [0, 0], "weit": [0, 0]}
	for e in eps:
		n += 1
		var ok: bool = float(e["lat"]) >= 0.0
		if ok:
			found += 1
			lats.append(float(e["lat"]))
		var bd: String = "nah" if int(e["px"]) >= 100 else ("mittel" if int(e["px"]) >= 60 else "weit")
		bands[bd][0] += 1
		if ok:
			bands[bd][1] += 1
	lats.sort()
	return {"v": 1, "quelle": "Spiel", "datum": Time.get_datetime_string_from_system(false, true), "runde": round_id,
			"simulator": main.VERSION, "mw_version": str(main.mw.get("mw_version", "")), "ki": str(main.mw.get("ai_status", "")),
			"spielart": main.game_mode, "szene": main.scene, "wetter": str(main.weather), "dunkel": main.is_dark(),
			"sichtbar": n, "gemeldet": found, "rate": (round(100.0 * found / n) if n > 0 else -1),
			"reaktion_median_s": (lats[lats.size() / 2] if not lats.is_empty() else -1), "baender": bands,
			"jaeger": hunter, "verpasst": misses, "episoden": eps, "zuordnung": "rahmen" if has_boxes() else "anzahl",
			"fehlalarme_mw": mw_false, "extras": game.plus.report() if game.plus != null else {},
			"ausloeser": game.shut.report() if game.shut != null else {}}   # 3D-4.x: the shots of the shutter (gameshutter.gd)


# ---- sending (same way as the test bench: GitHub key, otherwise the desktop) -----------------------------------------
func send() -> String:
	"""all rounds not sent yet -> one ZIP -> GitHub feedback/spiel/ (with the key of the test bench) or the desktop"""
	var base := "user://spiel"
	var d := DirAccess.open(base)
	if d == null:
		return "Noch kein Spielbericht – zuerst eine Runde mit MoveEye spielen."
	var rounds: Array = []
	for r in d.get_directories():
		if not FileAccess.file_exists(base + "/" + r + "/.gesendet"):
			rounds.append(r)
	if rounds.is_empty():
		return "Alle Spielberichte sind schon gesendet."
	var zp := ProjectSettings.globalize_path(base + "/spielbericht_%s.zip" % rounds[-1])
	var z := ZIPPacker.new()
	if z.open(zp) != OK:
		return "Konnte die ZIP-Datei nicht schreiben."
	for r in rounds:
		var rd := DirAccess.open(base + "/" + r)
		if rd == null:
			continue
		for fn in rd.get_files():
			if fn.begins_with("."):
				continue
			z.start_file(r + "/" + fn)
			z.write_file(FileAccess.get_file_as_bytes(base + "/" + r + "/" + fn))
			z.close_file()
	z.close()
	var tok := ""
	if FileAccess.file_exists("user://pruefstand/schluessel.txt"):
		tok = FileAccess.get_file_as_string("user://pruefstand/schluessel.txt").strip_edges()
	if tok == "":
		var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
		if desk == "" or not DirAccess.dir_exists_absolute(desk):
			desk = OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)
		if desk == "" or not DirAccess.dir_exists_absolute(desk):
			OS.shell_show_in_file_manager(zp)
			_mark(rounds)
			return "Gespeichert: %s – diese Datei im Chat anhängen." % zp
		var to := desk.path_join(zp.get_file())
		DirAccess.copy_absolute(zp, to)
		OS.shell_show_in_file_manager(to)
		_mark(rounds)
		return "Auf den Schreibtisch gelegt: %s – diese Datei im Chat anhängen." % to.get_file()
	_upload(zp, tok, rounds)
	return "Sende an GitHub …"


func _mark(rounds: Array) -> void:
	for r in rounds:
		var f := FileAccess.open("user://spiel/" + r + "/.gesendet", FileAccess.WRITE)
		if f != null:
			f.store_string("1")
			f.close()


func _upload(zp: String, tok: String, rounds: Array) -> void:
	var data := JSON.stringify({"message": "Spielbericht vom Simulator (%d Runden)" % rounds.size(),
			"content": Marshalls.raw_to_base64(FileAccess.get_file_as_bytes(zp))})
	var headers := ["Authorization: Bearer " + tok, "Accept: application/vnd.github+json", "User-Agent: MotionWatch3D", "Content-Type: application/json"]
	var url := "https://api.github.com/repos/DonElektro/MotionWatch/contents/feedback/spiel/" + zp.get_file()
	if http.request(url, headers, HTTPClient.METHOD_PUT, data) != OK:
		info = "Senden ging nicht."
		return
	var r: Array = await http.request_completed
	if int(r[1]) in [200, 201]:
		_mark(rounds)
		info = "✓ Spielbericht gesendet (%d Runden)." % rounds.size()
	else:
		info = "Senden ging nicht (GitHub %d) – Schlüssel prüfen." % int(r[1])
	game.news("📊 " + info)


# ---- the sneaking ways as a test run (testrun.gd plan «spielwege») ---------------------------------------------------
static func load_ways() -> Array:
	"""saved sneaking ways: shipped with the simulator (res://spielwege/) and from own rounds (user://spiel/*/), newest first"""
	var out: Array = []
	var seen := {}
	for base in ["res://spielwege", "user://spiel"]:
		var d := DirAccess.open(base)
		if d == null:
			continue
		var files: Array = []
		for fn in d.get_files():
			if fn.ends_with(".json") and fn.begins_with("schleichweg"):
				files.append(base + "/" + fn)
		for sub in d.get_directories():
			var sd := DirAccess.open(base + "/" + sub)
			if sd == null:
				continue
			for fn in sd.get_files():
				if fn.ends_with(".json") and fn.begins_with("schleichweg"):
					files.append(base + "/" + sub + "/" + fn)
		for fp in files:
			var w = JSON.parse_string(FileAccess.get_file_as_string(fp))
			if typeof(w) == TYPE_DICTIONARY and typeof(w.get("points")) == TYPE_ARRAY and w["points"].size() >= 6:
				var key := way_key(w)
				if seen.has(key):                         # Prüfstand 2: the same way (shipped and own) only once
					continue
				seen[key] = true
				w["file"] = fp
				w["key"] = key
				out.append(w)
	out.sort_custom(func(a, b): return str(a.get("date", "")) > str(b.get("date", "")))
	return out


static func way_key(w: Dictionary) -> String:
	"""Prüfstand 2: the same sneaking way has the same key (scene + the points rounded to 10 cm) - for the file name on GitHub
	and so the test bench walks each way once (pruefstand.py dedups with the same rule)"""
	var t := str(w.get("scene", ""))
	for q in w.get("points", []):
		if typeof(q) == TYPE_ARRAY and q.size() >= 3:
			t += ";%d,%d" % [int(round(float(q[1]) * 10.0)), int(round(float(q[2]) * 10.0))]
	return t.md5_text().left(12)
