extends Node
## Recording and replay (3D-3.27): an interesting situation (who walked where, how, at which time of day, in which
## weather) is recorded and can be played again exactly the same, as often as wanted - good to compare settings of
## MoveEye. The visitors of the replay are puppets: they walk the recorded ways, the same figures (same colours).
## Files: user://aufnahmen/*.json (at most 12, at most 5 minutes each).

var main
const STEP := 0.1                       # one frame every 0.1 s
const MAX_S := 300.0
const DIR := "user://aufnahmen"

var recording := false
var rec := {}                           # {"name", "t", "world", "spawns": {id: {kind, seed, t0, ...}}, "frames": [[t, [[id, x, z, h, s, c, idle]...]]]}
var _rt0 := 0.0
var _acc := 0.0
var _ids := {}                          # instance id -> short id
var playing := false
var loop := false
var pick := ""                          # the file chosen for replay
var _play := {}
var _pt0 := 0.0
var _fi := 0
var _puppets := {}                      # short id -> actor
var _saved := {}
var info := ""


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func list() -> Array:
	var out := []
	var d := DirAccess.open(DIR)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".json"):
			out.append(f)
	out.sort()
	out.reverse()
	return out


func options() -> Array:
	var o := [["", "– Aufnahme wählen –"]]
	for f in list():
		o.append([f, f.get_basename().replace("aufnahme_", "").replace("_", " ")])
	return o


# ---- recording -----------------------------------------------------------------------------------------------------
func start_rec() -> void:
	if recording or playing:
		return
	recording = true
	_rt0 = now()
	_acc = 0.0
	_ids.clear()
	rec = {"v": 1, "t": Time.get_datetime_string_from_system(false, true), "scene": main.scene,
			"world": {"hour": main.hour(), "weather": main.weather, "wind": main.wind, "ambient": main.ambient, "cond": main.cond.duplicate()},
			"spawns": {}, "frames": []}
	for v in main.visitors.get_children():               # who is there already
		_note(v, -1)
	info = "● Aufnahme läuft …"


func note_spawn(v, sd: int) -> void:
	"""main.spawn() tells every new visitor (with the seed of its look)"""
	if recording:
		_note(v, sd)


func _note(v, sd: int) -> void:
	if v.get("kind") == null:
		return
	var sid := str(_ids.size())
	_ids[v.get_instance_id()] = sid
	rec["spawns"][sid] = {"kind": v.kind, "seed": sd, "t0": snappedf(now() - _rt0, 0.01), "speed": v.speed}


func stop_rec() -> void:
	if not recording:
		return
	recording = false
	if rec["frames"].size() < 10:
		info = "Aufnahme zu kurz – nicht gespeichert."
		return
	DirAccess.make_dir_recursive_absolute(DIR)
	var name := "aufnahme_" + Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
	var f := FileAccess.open(DIR + "/" + name + ".json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(rec))
	var all := list()
	for i in range(12, all.size()):                     # keep the newest 12
		DirAccess.remove_absolute(DIR + "/" + all[i])
	pick = name + ".json"
	info = "Aufnahme gespeichert: %d s, %d Besucher." % [int(rec["frames"][-1][0]), rec["spawns"].size()]
	main.refresh_controls()


# ---- replay --------------------------------------------------------------------------------------------------------
func play(file := "") -> String:
	if recording:
		stop_rec()
	if file != "":
		pick = file
	if pick == "":
		var l := list()
		if l.is_empty():
			info = "Noch keine Aufnahme."
			return info
		pick = l[0]
	var txt := FileAccess.get_file_as_string(DIR + "/" + pick)
	var d = JSON.parse_string(txt)
	if typeof(d) != TYPE_DICTIONARY or not d.has("frames"):
		info = "Aufnahme nicht lesbar."
		return info
	if not playing:
		_saved = {"auto": main.auto_visitors, "hour": main.hour(), "weather": main.weather, "wind": main.wind, "cond": main.cond.duplicate()}
	_play = d
	playing = true
	_start_pass()
	return ""


func _start_pass() -> void:
	main.auto_visitors = false
	main.clear_visitors()
	_puppets.clear()
	var w: Dictionary = _play.get("world", {})
	main.set_hour(float(w.get("hour", main.hour())))
	main.weather = str(w.get("weather", main.weather))
	main.wind = float(w.get("wind", main.wind))
	var c: Dictionary = w.get("cond", {})
	for k in main.cond:
		main.cond[k] = bool(c.get(k, false))
	_pt0 = now()
	_fi = 0
	info = "▶ Wiedergabe: " + pick.get_basename().replace("aufnahme_", "")


func stop_play() -> void:
	if not playing:
		return
	playing = false
	main.clear_visitors()
	_puppets.clear()
	main.auto_visitors = bool(_saved.get("auto", true))
	main.set_hour(float(_saved.get("hour", main.hour())))
	main.weather = str(_saved.get("weather", main.weather))
	main.wind = float(_saved.get("wind", main.wind))
	main.cond = _saved.get("cond", main.cond)
	info = "Wiedergabe beendet."


func _process(dt: float) -> void:
	if main == null:
		return
	if recording:
		_acc += dt
		if _acc >= STEP:
			_acc = 0.0
			var fr := []
			for v in main.visitors.get_children():
				var id: int = v.get_instance_id()
				if not _ids.has(id):
					_note(v, -1)
				fr.append([_ids[id], snappedf(v.position.x, 0.01), snappedf(v.position.z, 0.01), snappedf(v.heading, 0.01),
						snappedf(v.cur_speed, 0.01), snappedf(v.crouch, 0.01), v.idle_kind])
			var t := now() - _rt0
			rec["frames"].append([snappedf(t, 0.01), fr])
			info = "● Aufnahme läuft … %d s, %d Besucher" % [int(t), rec["spawns"].size()]
			if t > MAX_S:
				stop_rec()
	if playing:
		_tick_play()


func _tick_play() -> void:
	var t := now() - _pt0
	var frames: Array = _play["frames"]
	while _fi < frames.size() - 1 and float(frames[_fi + 1][0]) <= t:
		_fi += 1
	if _fi >= frames.size() - 1 and t > float(frames[-1][0]):
		if loop:
			_start_pass()
		else:
			stop_play()
		return
	var a: Array = frames[_fi]
	var b: Array = frames[mini(_fi + 1, frames.size() - 1)]
	var k: float = clampf((t - float(a[0])) / max(0.001, float(b[0]) - float(a[0])), 0.0, 1.0)
	var nb := {}
	for e in b[1]:
		nb[str(e[0])] = e
	var seen := {}
	for e in a[1]:
		var sid := str(e[0])
		seen[sid] = true
		var p = _puppets.get(sid)
		if p == null or not is_instance_valid(p):
			var sp: Dictionary = _play["spawns"].get(sid, {})
			if sp.is_empty():
				continue
			p = _make(sp, Vector3(float(e[1]), 0, float(e[2])))
			_puppets[sid] = p
		var e2: Array = nb.get(sid, e)
		p.position.x = lerpf(float(e[1]), float(e2[1]), k)
		p.position.z = lerpf(float(e[2]), float(e2[2]), k)
		p.heading = lerp_angle(float(e[3]), float(e2[3]), k)
		p.rotation.y = p.heading
		p.cur_speed = lerpf(float(e[4]), float(e2[4]), k)
		p.crouch = lerpf(float(e[5]), float(e2[5]), k)
		p.idle_kind = str(e[6])
	for sid in _puppets.keys():                           # gone in the recording: gone here too
		if not seen.has(sid):
			var q = _puppets[sid]
			if is_instance_valid(q):
				q.queue_free()
			_puppets.erase(sid)
	info = "▶ Wiedergabe %d / %d s%s" % [int(t), int(float(frames[-1][0])), " (wiederholen)" if loop else ""]


func _make(sp: Dictionary, at: Vector3):
	var sd := int(sp.get("seed", -1))
	if sd >= 0:
		seed(sd)                                          # the same look as in the recording
	var v = main.Actor.new()
	main.visitors.add_child(v)
	v.setup(main, str(sp["kind"]), at, at + Vector3(0, 0, -1), float(sp.get("speed", 1.3)))
	v.set_night(main.is_dark())
	v.puppet = true
	randomize()
	return v
