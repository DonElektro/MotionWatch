extends Node
## 3D-3.75: «Überraschungsnacht» - during the night, now and then something unexpected happens: a power cut (all lamps
## go out), a fog bank drifts through, a distraction (an animal on one side, a careful sneaker on the other), a car stops
## and blinds the camera with its headlights, an animal stands still in front of the camera for minutes.
## Motion Watch is watched all the time (what it reports in «det», its light and siren); in the morning there is a score:
## stayed calm when nothing was there, found the person when there was one.

var main
var next_t := 0.0
var cur := {}                    # the event running now
var log_: Array = []             # the events of this night
var report := ""                 # the last morning report (text)
var report_n := [0, 0]           # right, all
var _was_dark := false
var _old_weather := ""

const KINDS := [["power", "Stromausfall"], ["fogbank", "Nebelbank"], ["distract", "Ablenkung"], ["glare", "Scheinwerfer blenden"], ["still", "Tier steht still"]]
const ANIMALS := ["deer", "fox", "boar", "hare"]


func kind_name(k: String) -> String:
	for x in KINDS:
		if x[0] == k:
			return x[1]
	return k


func set_on(v: bool) -> void:
	main.surprise_on = v
	main._settings_dirty = true
	next_t = main.now() + randf_range(20.0, 60.0)
	if v:
		log_.clear()
		report = ""


func status_text() -> String:
	if not cur.is_empty():
		return "Überraschung läuft: %s (%d s)" % [kind_name(str(cur["k"])), int(main.now() - float(cur["t0"]))]
	if report != "":
		return report
	if main.surprise_on:
		return "Überraschungsnacht an – %s. %d Ereignisse bisher." % ["wartet auf die Nacht" if not main.is_dark() else "irgendwann passiert etwas", log_.size()]
	return ""


func _process(_dt: float) -> void:
	if main == null:
		return
	var t: float = main.now()
	if not cur.is_empty():
		_watch(t)
	elif main.surprise_on and main.is_dark() and t > next_t:
		start(str(KINDS[randi() % KINDS.size()][0]))
	var dark: bool = main.is_dark()
	if _was_dark and not dark and not log_.is_empty() and cur.is_empty():
		morning()                                         # the sun is up: the score of the night
	_was_dark = dark


# ---- the events -----------------------------------------------------------------------------------------------------------
func start(k: String) -> void:
	if not cur.is_empty():
		_finish()
	var t: float = main.now()
	cur = {"k": k, "t0": t, "t1": t + 60.0, "person": false, "fa": false, "seen": -1.0, "react": false, "mw": main.now() - main.mw_t < 10.0,
			"hour": main.hour(), "who": []}
	var fwd: Vector3 = -main.cams[0].global_transform.basis.z
	fwd.y = 0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3(0, 0, -1)
	var rig: Vector3 = main.head.global_position
	rig.y = 0
	match k:
		"power":                                          # all lamps of the place go out, then come back with a flicker
			cur["t1"] = t + randf_range(50.0, 100.0)
			main.power_off = true
		"fogbank":
			cur["t1"] = t + randf_range(80.0, 140.0)
			_old_weather = main.weather
			main.weather = "fog"
		"distract":                                       # an animal crosses in front, a sneaker comes from the side
			cur["t1"] = t + 150.0
			cur["person"] = true
			var side := fwd.rotated(Vector3.UP, PI / 2.0)
			var a0: Vector3 = main.free_spot(rig + fwd * 11.0 + side * 14.0, 0.6, true)
			var a1: Vector3 = main.free_spot(rig + fwd * 9.0 - side * 14.0, 0.6, true)
			var an = main.spawn(ANIMALS[randi() % ANIMALS.size()], a0, a1)
			an.speed = 0.7
			cur["who"].append(an)
			await get_tree().create_timer(4.0).timeout
			if cur.is_empty() or str(cur["k"]) != "distract":
				return
			main.stories.sneaker()
			var last = main.visitors.get_child(main.visitors.get_child_count() - 1)
			if last != null and last.has_meta("sneak"):
				cur["who"].append(last)
		"glare":                                          # a car comes towards the camera, stops, the headlights blind it
			cur["t1"] = t + 55.0
			var far: Vector3 = main.free_spot(rig + fwd * 55.0 + fwd.rotated(Vector3.UP, PI / 2.0) * randf_range(-6.0, 6.0), 1.5, false)
			var stop: Vector3 = rig + (far - rig).normalized() * randf_range(9.0, 13.0)
			var c = main.spawn("car", far, stop)
			c.speed = 4.0
			c.route = [[stop, randf_range(18.0, 28.0), 0.0, rig], far + (far - rig).normalized() * 30.0]
			cur["who"].append(c)
		"still":                                          # an animal stops in front of the camera and hardly moves
			cur["t1"] = t + randf_range(150.0, 220.0)
			var p: Vector3 = main.free_spot(rig + fwd.rotated(Vector3.UP, randf_range(-0.3, 0.3)) * randf_range(7.0, 12.0), 0.6, true)
			var from: Vector3 = main.free_spot(p + fwd.rotated(Vector3.UP, PI / 2.0) * 18.0, 0.6, true)
			var an2 = main.spawn(["deer", "fox", "boar", "sheep"][randi() % 4], from, p)
			an2.speed = 0.8
			an2.route = [[p, float(cur["t1"]) - t - 20.0, 0.0, rig], p - fwd * 30.0]
			cur["who"].append(an2)
	main.start_info = "Überraschung: " + kind_name(k)


func _truth_person() -> bool:
	"""is there a person in front of Motion Watch right now (inside 40 m)?"""
	for v in main.visitors.get_children():
		if v.kind == "person" and not v.done and v.position.distance_to(main.head.global_position) < 40.0:
			return true
	return false


func _person_in_view() -> bool:
	"""a person the head camera can see well (big enough, free view, light) - like the truth of the test runs"""
	var keep: Array = main.testrun.truth_cams
	main.testrun.truth_cams = [0]
	var seen := false
	for v in main.visitors.get_children():
		if v.kind == "person" and not v.done and main.testrun.visible(v):
			seen = true
			break
	main.testrun.truth_cams = keep
	return seen


var _last_t := 0.0


func _watch(t: float) -> void:
	var dt_ := clampf(t - _last_t, 0.0, 0.5)
	_last_t = t
	if bool(cur["person"]) and _person_in_view():
		cur["vis"] = float(cur.get("vis", 0.0)) + dt_
	if t - main.mw_t < 5.0:
		cur["mw"] = true
	var fresh: bool = t - main.mw_det_t < 3.0
	var persons: int = int(main.mw_det.get("persons", 0)) if fresh else 0
	var L: Dictionary = main.mw.get("lights", {}) if t - main.mw_t < 5.0 else {}
	var react: bool = bool(L.get("white", false)) or str(main.mw.get("sound", "")) != ""
	var truth := _truth_person()
	if persons > 0 and truth and float(cur["seen"]) < 0.0:
		cur["seen"] = t - float(cur["t0"])
	if persons > 0 and not truth:
		cur["fa"] = true
	if react and not truth:
		cur["react"] = true
	if str(cur["k"]) == "power" and main.power_off and t > float(cur["t1"]) - 3.0:
		main.power_off = false                            # the power is back
	if t > float(cur["t1"]) + 12.0:                       # a little time after the end: did it react late?
		_finish()


func _finish() -> void:
	match str(cur["k"]):
		"power":
			main.power_off = false
		"fogbank":
			if main.weather == "fog":
				main.weather = _old_weather if _old_weather != "" else "clear"
	var ok: bool
	var why: String
	if not bool(cur["mw"]):
		ok = false
		why = "Motion Watch war nicht verbunden"
	elif bool(cur["person"]) and float(cur["seen"]) < 0.0 and float(cur.get("vis", 0.0)) < 2.0:
		ok = true
		why = "nicht bewertet: der Mensch war nie gut im Bild der Kopfkamera"
		cur["skip"] = true
	elif bool(cur["person"]):
		ok = float(cur["seen"]) >= 0.0
		why = ("Mensch erkannt nach %d s" % int(cur["seen"])) if ok else ("Mensch nicht erkannt (%d s gut im Bild)" % int(cur.get("vis", 0.0)))
	else:
		ok = not bool(cur["fa"]) and not bool(cur["react"])
		why = "ruhig geblieben" if ok else ("Fehlalarm: Person gemeldet" if bool(cur["fa"]) else "Fehlalarm: Licht oder Sirene")
	log_.append({"k": cur["k"], "name": kind_name(str(cur["k"])), "hour": snappedf(float(cur["hour"]), 0.01), "ok": ok, "why": why,
			"seen_s": cur["seen"], "false_alarm": cur["fa"], "reaction": cur["react"], "skip": bool(cur.get("skip", false)),
			"visible_s": snappedf(float(cur.get("vis", 0.0)), 0.1)})
	main.start_info = "Überraschung vorbei: %s – %s" % [kind_name(str(cur["k"])), why]
	cur = {}
	next_t = main.now() + randf_range(90.0, 240.0)


func morning() -> void:
	"""the score of the night: a short text, saved in user://ueberraschung/"""
	if not cur.is_empty():
		_finish()
	if log_.is_empty():
		report = "Überraschungsnacht: noch keine Ereignisse."
		return
	var good := 0
	var n := 0
	var lines := []
	for e in log_:
		if not bool(e.get("skip", false)):
			n += 1
			if bool(e["ok"]):
				good += 1
		var h := float(e["hour"])
		lines.append("%s %02d:%02d %s – %s" % ["–" if bool(e.get("skip", false)) else ("✓" if bool(e["ok"]) else "✗"), int(h), int(fmod(h, 1.0) * 60.0), e["name"], e["why"]])
	report_n = [good, n]
	var st := int(round(5.0 * good / max(1, n)))
	var stars := "★".repeat(st) + "☆".repeat(5 - st)
	report = "Guten Morgen! Überraschungsnacht: %d von %d richtig %s\n%s" % [good, n, stars, "\n".join(lines)]
	DirAccess.make_dir_recursive_absolute("user://ueberraschung")
	var f := FileAccess.open("user://ueberraschung/%s.json" % Time.get_datetime_string_from_system().replace(":", "-"), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"right": good, "all": n, "events": log_, "mw_version": str(main.mw.get("mw_version", ""))}, " "))
	main.start_info = "Überraschungsnacht: %d von %d richtig" % [good, n]
	main._say("%d / %d ★" % [good, n], main.head.global_position + Vector3(0, 1.2, 0), Color("#ffd166"), main.HELPER_LAYER)
	log_.clear()


func info() -> Dictionary:
	return {"on": main.surprise_on, "running": "" if cur.is_empty() else str(cur["k"]), "events": log_, "report": report, "right": report_n[0], "all": report_n[1]}
