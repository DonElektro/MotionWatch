extends Node
## Test run with evaluation (from 3D-2.6): a fixed sequence of phases (day, wind and clouds, night with insects, rain at
## night) with visitors crossing the picture. The simulator knows the truth (who is visible to the cameras, when) and
## compares it with what MoveEye reports (sim_state «det», from MoveEye 2.93.3): persons recognised, how fast,
## animals reported, false alarms and their probable cause, noise alarms. Report: in the window, on the web page of
## MoveEye (status), as JSON / HTML file in the user folder (testlauf/), and via CONTROL {"action": "test_report"}.

var main

const STANDARD := [
	{"name": "Tag, klar", "hour": 11.0, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "deer", "child", "person"]},
	{"name": "Tag, Wind und Wolken", "hour": 14.5, "weather": "cloudy", "wind": 65.0, "visits": ["person", "cat", "jogger", "person"]},
	{"name": "Nacht, klar (Insekten am Licht)", "hour": 22.5, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "boar"]},
	{"name": "Nacht, Regen", "hour": 23.5, "weather": "rain", "wind": 20.0, "visits": ["person", "cat", "person"]},
]
# 3D-3.27: more test runs. «cond» = difficult conditions of main.gd (switched on only during the phase)
const PLANS := {
	"standard": {"name": "Standard (Tag, Wind, Nacht, Regen · etwa 4 Min.)", "phases": STANDARD},
	"quick": {"name": "Kurz (Tag und Nacht · etwa 2 Min., für die automatische Optimierung)", "phases": [
		{"name": "Tag, Wind", "hour": 13.0, "weather": "cloudy", "wind": 45.0, "visits": ["person", "fox", "jogger", "person"]},
		{"name": "Nacht mit Infrarot", "hour": 22.5, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["person", "cat", "person"]}]},
	"hard": {"name": "Schwierige Bedingungen (Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten · etwa 7 Min.)", "phases": [
		{"name": "Gegenlicht am Morgen", "hour": 7.3, "weather": "clear", "wind": 35.0, "cond": ["glare"], "visits": ["person", "deer", "person"]},
		{"name": "Nebel", "hour": 9.0, "weather": "fog", "wind": 5.0, "visits": ["person", "fox", "person"]},
		{"name": "Schnee", "hour": 15.0, "weather": "snow", "wind": 25.0, "visits": ["person", "hare", "child"]},
		{"name": "Tropfen auf der Linse", "hour": 12.0, "weather": "cloudy", "wind": 15.0, "cond": ["drops"], "visits": ["person", "cat", "person"]},
		{"name": "Spinnennetz, Nacht mit Infrarot", "hour": 23.0, "weather": "clear", "wind": 30.0, "cond": ["web", "ir"], "visits": ["person", "fox", "person"]},
		{"name": "Scheinwerfer in der Nacht", "hour": 22.0, "weather": "clear", "wind": 5.0, "cond": ["headlights"], "visits": ["person", "badger", "person"]},
		{"name": "Wolkenschatten und Wind", "hour": 14.0, "weather": "cloudy", "wind": 55.0, "cond": ["shadows"], "visits": ["person", "cat", "jogger"]}]},
	"night": {"name": "Nacht (dunkel, Infrarot, Tiere · etwa 3 Min.)", "phases": [
		{"name": "Nacht, ohne Licht", "hour": 1.0, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "hedgehog"]},
		{"name": "Nacht, Infrarot an", "hour": 2.0, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["person", "boar", "child", "badger"]},
		{"name": "Nacht, Regen", "hour": 3.0, "weather": "rain", "wind": 25.0, "visits": ["person", "cat", "person"]}]},
}
const COND_NAMES := {"glare": "Gegenlicht", "drops": "Tropfen auf der Linse", "web": "Spinnennetz", "headlights": "Scheinwerfer",
		"shadows": "Wolkenschatten", "ir": "Infrarot"}
var plan := "standard"
var truth_cams := [0, 1]                # 3D-3.48: which cameras count for the truth (the test bench: only the head camera, 0)
var PHASES: Array = STANDARD
var _cond_saved := {}
const EVERY := 13.0                     # a new visitor every ... seconds
const SETTLE := 8.0                     # quiet time at the start of a phase (MoveEye adapts to the new light)
const GRACE := 2.5                      # a report counts for a visitor up to ... s after it was last visible

var running := false
var phase := -1
var t_phase := 0.0
var next_visit := 0.0
var visit_i := 0
var truth := {}                         # instance id -> record of a visitor
var falses: Array = []                  # false alarms {t, phase, cause}
var noises: Array = []                  # noise alarms {t, phase, cause}
var _prev_persons := 0
var _prev_noise := false
var _last_person_vis := -100.0
var _sample_t := 0.0
var t0 := 0.0
var saved := {}
var report := {}
var info := "Noch kein Testlauf."
var last_html := ""
var label: Label


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func plan_options() -> Array:
	var o := []
	for k in PLANS:
		o.append([k, PLANS[k]["name"]])
	var n: int = ways().size()
	if n > 0:                                             # 3D-3.52: sneaking ways from the game, where MoveEye saw nobody
		o.append(["spielwege", "Schleichwege aus dem Spiel (%d unerkannte Wege nachgehen)" % n])
	return o


var _ways: Array = []
var _ways_t := -100.0


func ways() -> Array:
	if now() - _ways_t > 10.0:
		# 3D-3.53: a way only fits the map it was walked on (the places change) - only the ways of the scene shown now
		_ways = preload("res://scripts/gamelearn.gd").load_ways().filter(func(w): return str(w.get("scene", "")) == str(main.scene)).slice(0, 8)
		_ways_t = now()
	return _ways


func _way_phases() -> Array:
	"""one phase per sneaking way: its hour and weather, the way walked by a person (as the player did, also crouching)"""
	var out: Array = []
	for i in range(ways().size()):
		var w: Dictionary = ways()[i]
		var pts: Array = w["points"]
		var dur: float = float(pts[-1][0]) - float(pts[0][0])
		out.append({"name": "Schleichweg von %s (%s)" % [str(w.get("name", "?")), str(w.get("date", "")).left(10)], "hour": float(w.get("hour", 12.0)),
				"weather": str(w.get("weather", "clear")), "wind": float(w.get("wind", 10.0)), "visits": ["way:%d" % i], "way_s": dur})
	return out


func state() -> Dictionary:
	"""for MoveEye (CONTROL test_report): running, progress, the plans and the last report"""
	var left := 0.0
	if running:
		left = max(0.0, t0 + duration() - now())
	return {"ok": true, "running": running, "info": info, "report": report, "plan": plan, "plans": plan_options(),
			"phase": phase + 1, "phases": PHASES.size(), "phase_name": PHASES[phase]["name"] if running and phase >= 0 else "",
			"left_s": int(left), "total_s": int(duration())}


func duration() -> float:
	var s := 0.0
	for ph in PHASES:
		s += SETTLE + max(EVERY * ph["visits"].size(), float(ph.get("way_s", 0.0)) + 2.0) + 6.0
	return s


func _spawn_way(i: int):
	"""a person walks the saved way of a player: the points every 0.5 s, crouching where the player crouched"""
	var w: Dictionary = ways()[i]
	var pts: Array = w["points"]
	var p0 := Vector3(float(pts[0][1]), 0, float(pts[0][2]))
	var p1 := Vector3(float(pts[1][1]), 0, float(pts[1][2]))
	var v = main.spawn("person", p0, p1)
	var r: Array = []
	var sp := 0.0
	var n := 0
	for k in range(2, pts.size()):
		var q: Array = pts[k]
		r.append([Vector3(float(q[1]), 0, float(q[2])), 0.0, 1.0 if int(q[3]) > 0 else 0.0])
		if float(q[4]) > 0.1:
			sp += float(q[4])
			n += 1
	v.route = r
	if n > 0:
		v.speed = clampf(sp / n, 0.4, 4.0)
	return v


func start(which := "", cams: Array = []) -> String:
	if running:
		return "Es läuft schon ein Testlauf."
	truth_cams = [0, 1]
	if not cams.is_empty():
		truth_cams = []
		for c in cams:
			if int(c) in [0, 1] and not int(c) in truth_cams:
				truth_cams.append(int(c))
	if which != "":
		if not PLANS.has(which) and which != "spielwege":
			return "unbekannter Testlauf"
		plan = which
	if plan == "spielwege":
		PHASES = _way_phases()
		if PHASES.is_empty():
			plan = "standard"
			return "Noch keine Schleichwege – zuerst eine Spielrunde mit MoveEye spielen."
	else:
		PHASES = PLANS[plan]["phases"]
	if not main.stream_on or main.now() - main.mw_t > 3.0:
		info = "MoveEye ist nicht verbunden. Zuerst «An MoveEye senden» einschalten und MoveEye verbinden (oder «MoveEye auf diesem PC» starten)."
		paint()
		return info
	var _b: String = main.busy_with("Prüfstand")       # 3D-3.88: the test bench runs test runs itself
	if _b != "":
		info = "Zuerst beenden: %s." % _b
		paint()
		return info
	saved = {"hour": main.hour(), "weather": main.weather, "wind": main.wind, "auto": main.auto_visitors}
	_cond_saved = main.cond.duplicate()
	main.auto_visitors = false
	main.clear_visitors()
	running = true
	truth.clear()
	falses.clear()
	noises.clear()
	report = {}
	t0 = now()
	_start_phase(0)
	return ""


func stop(finished := false) -> void:
	if not running:
		return
	running = false
	main.set_hour(float(saved.get("hour", 12.0)))
	main.weather = str(saved.get("weather", "clear"))
	main.wind = float(saved.get("wind", 10.0))
	main.auto_visitors = bool(saved.get("auto", true))
	if not _cond_saved.is_empty():
		main.cond = _cond_saved.duplicate()
	main.clear_visitors()
	if finished:
		_make_report()
	else:
		info = "Testlauf abgebrochen."
	paint()


func _start_phase(i: int) -> void:
	phase = i
	var ph: Dictionary = PHASES[i]
	main.set_hour(float(ph["hour"]))
	main.weather = ph["weather"]
	main.wind = float(ph["wind"])
	for k in main.cond:                                   # the difficult conditions of this phase only
		main.cond[k] = k in ph.get("cond", [])
	main.clear_visitors()
	seed(4711 + 97 * i + plan.hash() % 1000)               # the same visitors on the same ways every time: runs can be compared
	t_phase = now()
	next_visit = t_phase + SETTLE
	visit_i = 0
	_prev_persons = int(main.mw_det.get("persons", 0))       # what MoveEye already sees does not count as new
	_last_person_vis = now()                                 # the light changes: give it a moment
	paint()


func _process(dt: float) -> void:
	if not running:
		return
	var t := now()
	if main.now() - main.mw_t > 10.0:
		info = "MoveEye hat die Verbindung verloren – Testlauf abgebrochen."
		stop(false)
		return
	var ph: Dictionary = PHASES[phase]
	if visit_i < ph["visits"].size() and t >= next_visit:
		var k: String = ph["visits"][visit_i]
		var v = _spawn_way(int(k.substr(4))) if k.begins_with("way:") else main.spawn(k)
		if k.begins_with("way:"):
			k = "person"
		truth[v.get_instance_id()] = {"kind": k, "person": v.kind == "person", "phase": phase, "first": -1.0, "last": -100.0,
				"vis": 0.0, "det": -1.0, "rep": false, "as_person": false, "seen_ever": false, "px": 0.0, "light": 1.0, "crouch": false}
		visit_i += 1
		next_visit = t + max(EVERY, float(ph.get("way_s", 0.0)) + 2.0)
	elif visit_i >= ph["visits"].size() and t >= next_visit + 6.0:
		if phase + 1 < PHASES.size():
			_start_phase(phase + 1)
		else:
			stop(true)
			return
	_sample_t -= dt
	if _sample_t <= 0.0:
		_sample_t = 0.25
		_sample(0.25)
	info = "Testlauf: Phase %d von %d – %s · noch etwa %d s" % [phase + 1, PHASES.size(), ph["name"], int(max(0.0, t0 + duration() - t))]


func present(v) -> bool:
	"""looser: somebody is in the picture at all (even too dark or too small) - then a report is no false alarm"""
	var pos: Vector3 = v.position
	for i in range(2):
		var cam: Camera3D = main.cams[i]
		if cam.is_position_in_frustum(pos + Vector3(0, 0.8, 0)) and main.line_free(cam.global_position, pos + Vector3(0, 1.6, 0)):
			return true
	return false


var _vis_px := 0.0
var _vis_light := 1.0


func visible(v) -> bool:
	"""the truth: could a camera (head or fixed) see this visitor well enough? (big enough in the picture, free view, light)
	(3D-3.27: also notes how big (_vis_px) and how well lit (_vis_light) it was, for the reasons of a miss)"""
	var h: float = 1.7 * v.body_root.scale.y if v.kind == "person" else max(0.4, float(v.body_h) * 1.5)
	var pos: Vector3 = v.position
	for i in truth_cams:
		var cam: Camera3D = main.cams[i]
		var cp := cam.global_position
		var d: float = max(0.5, cp.distance_to(pos))
		if not cam.is_position_in_frustum(pos + Vector3(0, h * 0.6, 0)):
			continue
		if not main.line_free(cp, pos + Vector3(0, h * 0.95, 0)):
			continue
		var px: float = h / (2.0 * d * tan(deg_to_rad([41.0, 62.0][i]) / 2.0)) * [540.0, 360.0][i]
		if px < (30.0 if v.kind == "person" else 18.0):
			continue
		var lt: float = main.game.light_at(pos, i)
		if lt < 0.25:
			continue
		_vis_px = px
		_vis_light = lt
		return true
	return false


func _sample(dt: float) -> void:
	var t := now()
	var det: Dictionary = main.mw_det
	var persons := int(det.get("persons", 0))
	var present: Array = det.get("present", [])
	var any_person_vis := false
	var any_present := false
	var animals_vis := []
	for v in main.visitors.get_children():
		var id: int = v.get_instance_id()
		if not truth.has(id):
			continue
		var r: Dictionary = truth[id]
		if visible(v):
			if float(r["first"]) < 0.0:
				r["first"] = t
			r["last"] = t
			r["vis"] = float(r["vis"]) + dt
			r["px"] = max(float(r["px"]), _vis_px)
			r["light"] = min(float(r["light"]), _vis_light)
			if v.kind == "person" and float(v.get("crouch") if v.get("crouch") != null else 0.0) > 0.3:
				r["crouch"] = true
		var recent := t - float(r["last"]) <= GRACE and float(r["first"]) >= 0.0
		if r["person"] and present(v):
			any_present = true
			r["seen_ever"] = true
		if r["person"]:
			if recent:
				any_person_vis = true
				if persons > 0 and float(r["det"]) < 0.0:
					r["det"] = t
		else:
			if recent:
				animals_vis.append(r["kind"])
				if "animal" in present or "motion" in present or "prealarm" in present:
					r["rep"] = true
				if persons > 0:
					r["as_person"] = true
	if any_person_vis or any_present:
		_last_person_vis = t
	# a new person alarm without a visible person = false alarm (with the probable cause)
	if persons > 0 and _prev_persons == 0 and t - _last_person_vis > GRACE:
		var cause := "unbekannt"
		var conds: Array = PHASES[phase].get("cond", [])
		if not animals_vis.is_empty():
			cause = "Tier (%s)" % ", ".join(PackedStringArray(animals_vis))
		elif "web" in conds:
			cause = "Spinnennetz"
		elif "glare" in conds:
			cause = "Gegenlicht"
		elif "headlights" in conds:
			cause = "Scheinwerfer"
		elif "drops" in conds:
			cause = "Tropfen auf der Linse"
		elif "shadows" in conds:
			cause = "Wolkenschatten"
		elif main.weather == "snow":
			cause = "Schnee"
		elif main.weather == "fog":
			cause = "Nebel"
		elif main.insects != null and main.insects.emitting:
			cause = "Insekten am Licht"
		elif main.wind > 40.0:
			cause = "Wind (Bäume, Büsche)"
		elif main.weather == "rain":
			cause = "Regen"
		falses.append({"t": snappedf(t - t0, 0.1), "phase": phase, "cause": cause})
	_prev_persons = persons
	var noisy := bool(det.get("noise", false))
	if noisy and not _prev_noise:
		var near := "Geräusch der Welt"
		for v in main.visitors.get_children():
			if v.get("kind") == "dog":
				near = "Hund bellt"
			elif v.get("kind") == "car":
				near = "Auto"
		noises.append({"t": snappedf(t - t0, 0.1), "phase": phase, "cause": near if main.weather != "rain" else "Regen"})
	_prev_noise = noisy


func _make_report() -> void:
	var phs := []
	var all_missed := []
	var tp := 0
	var td := 0
	var lat_all := []
	var each := []                                         # 3D-3.48: every visitor that was well visible (for the test bench: by size)
	for r0 in truth.values():
		if float(r0["first"]) >= 0.0:
			each.append({"kind": r0["kind"], "person": r0["person"], "phase": int(r0["phase"]), "px": int(float(r0["px"])),
					"light": snappedf(float(r0["light"]), 0.01), "vis_s": snappedf(float(r0["vis"]), 0.1), "crouch": r0["crouch"],
					"det_s": snappedf(float(r0["det"]) - float(r0["first"]), 0.1) if float(r0["det"]) >= 0.0 else -1.0, "reported": r0["rep"]})
	for i in range(PHASES.size()):
		var pn := 0
		var pd := 0
		var an := 0
		var ar := 0
		var lats := []
		var missed := []
		var why := {"dark": 0, "small": 0, "fast": 0, "crouch": 0}
		var as_person := 0
		var hidden := 0
		for r in truth.values():
			if int(r["phase"]) != i:
				continue
			if float(r["first"]) < 0.0:
				if r["person"]:
					hidden += 1                            # never well visible (too dark, too far, hidden): does not count
				continue
			if r["person"]:
				pn += 1
				if float(r["det"]) >= 0.0:
					pd += 1
					lats.append(max(0.0, float(r["det"]) - float(r["first"])))
				else:
					missed.append(r["kind"])
					var wy := []
					if float(r["light"]) < 0.5:
						wy.append("dark")
					if float(r["px"]) < 70.0:
						wy.append("small")
					if r["kind"] == "jogger":
						wy.append("fast")
					if r["crouch"]:
						wy.append("crouch")
					# when it was best to see (3D-3.31): MoveEye takes its own picture of that moment into the report
					all_missed.append({"t": snappedf(float(r["first"]) - t0 + min(3.0, float(r["vis"]) / 2.0), 0.1), "phase": i, "kind": r["kind"], "why": wy})
					if float(r["light"]) < 0.5:
						why["dark"] += 1
					if float(r["px"]) < 70.0:
						why["small"] += 1
					if r["kind"] == "jogger":
						why["fast"] += 1
					if r["crouch"]:
						why["crouch"] += 1
			else:
				an += 1
				if r["rep"]:
					ar += 1
				if r["as_person"]:
					as_person += 1
		var fa := falses.filter(func(f): return int(f["phase"]) == i).size()
		var lat := -1.0
		if not lats.is_empty():
			var s := 0.0
			for x in lats:
				s += x
			lat = s / lats.size()
		lat_all.append_array(lats)
		tp += pn
		td += pd
		phs.append({"name": PHASES[i]["name"], "persons": pn, "persons_detected": pd, "animals": an, "animals_reported": ar,
				"false_alarms": fa, "latency_s": snappedf(lat, 0.1), "missed": missed, "not_visible": hidden, "missed_why": why,
				"animals_as_person": as_person, "hour": PHASES[i]["hour"], "weather": PHASES[i]["weather"], "wind": PHASES[i]["wind"],
				"cond": PHASES[i].get("cond", []), "dark": float(PHASES[i]["hour"]) < 6.0 or float(PHASES[i]["hour"]) > 20.5})
	var lat_avg := -1.0
	if not lat_all.is_empty():
		var s2 := 0.0
		for x in lat_all:
			s2 += x
		lat_avg = s2 / lat_all.size()
	var dev := str(main.mw.get("device", "MoveEye"))
	report = {"v": 2, "plan": plan, "plan_name": PLANS[plan]["name"], "date": Time.get_datetime_string_from_system(false, true), "simulator": main.version(), "scene": main.scene,
			"device": dev, "persons": tp, "persons_detected": td, "rate": snappedf(100.0 * td / max(1, tp), 1),
			"latency_s": snappedf(lat_avg, 0.1), "false_alarms": falses.size(), "false_list": falses, "missed_list": all_missed, "noise_alarms": noises,
			"phases": phs, "truth_cams": truth_cams, "visitors": each,
			"note": ("Wahrheit: sichtbar für Kopf- oder feste Kamera" if truth_cams.size() > 1 else "Wahrheit: sichtbar für die Kopfkamera") + " (frei, gross genug, genug Licht)."}
	info = "Testlauf fertig: Personen erkannt %d von %d (%d %%), Reaktionszeit %s, Fehlalarme %d, Geräuschalarme %d." % [
			td, tp, int(report["rate"]), ("%.1f s" % lat_avg) if lat_avg >= 0.0 else "–", falses.size(), noises.size()]
	_save()


func _save() -> void:
	var dir := OS.get_user_data_dir().path_join("testlauf")
	DirAccess.make_dir_recursive_absolute(dir)
	var stamp := Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
	var base := dir.path_join("testlauf_" + stamp)
	var f := FileAccess.open(base + ".json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(report, " "))
	var h := FileAccess.open(base + ".html", FileAccess.WRITE)
	if h != null:
		h.store_string(html())
		last_html = base + ".html"


func html() -> String:
	var r := report
	var rows := ""
	for p in r.get("phases", []):
		rows += "<tr><td>%s</td><td>%d / %d</td><td>%s</td><td>%d / %d</td><td>%d</td><td>%s</td><td>%d</td></tr>" % [p["name"], p["persons_detected"], p["persons"],
				("%.1f s" % p["latency_s"]) if float(p["latency_s"]) >= 0.0 else "–", p["animals_reported"], p["animals"], p["false_alarms"],
				", ".join(PackedStringArray(p["missed"])) if not p["missed"].is_empty() else "–", p.get("not_visible", 0)]
	var fl := ""
	for f in r.get("false_list", []):
		fl += "<li>%.0f s · %s · %s</li>" % [f["t"], PHASES[int(f["phase"])]["name"], f["cause"]]
	var nl := ""
	for n in r.get("noise_alarms", []):
		nl += "<li>%.0f s · %s · %s</li>" % [n["t"], PHASES[int(n["phase"])]["name"], n["cause"]]
	return """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Testlauf %s</title><style>body{font:15px system-ui,sans-serif;background:#0a0e14;color:#e6edf3;margin:0;padding:20px;max-width:900px}
h1{font-size:22px}.big{display:flex;gap:12px;flex-wrap:wrap}.t{background:#151e2b;border:1px solid #1f2b3a;border-radius:12px;padding:12px 16px}
.t b{display:block;font-size:26px}table{border-collapse:collapse;width:100%%;margin-top:14px}td,th{border-bottom:1px solid #1f2b3a;padding:6px 8px;text-align:left}
.mut{color:#8b98a8}</style></head><body><h1>Testlauf · %s</h1><p class="mut">%s · Szene %s · Simulator %s</p>
<div class="big"><div class="t">Personen erkannt<b>%d / %d (%s %%)</b></div><div class="t">Reaktionszeit (Mittel)<b>%s</b></div>
<div class="t">Fehlalarme (Person)<b>%d</b></div><div class="t">Geräuschalarme<b>%d</b></div></div>
<table><tr><th>Phase</th><th>Personen erkannt</th><th>Reaktionszeit</th><th>Tiere gemeldet</th><th>Fehlalarme</th><th>Nicht erkannt</th><th>Für die Kamera unsichtbar</th></tr>%s</table>
<h3>Fehlalarme</h3><ul>%s</ul><h3>Geräuschalarme</h3><ul>%s</ul><p class="mut">%s</p></body></html>""" % [
			r.get("date", ""), r.get("device", ""), r.get("date", ""), r.get("scene", ""), r.get("simulator", ""),
			r.get("persons_detected", 0), r.get("persons", 0), str(r.get("rate", 0)), ("%.1f s" % r["latency_s"]) if float(r.get("latency_s", -1)) >= 0.0 else "–",
			r.get("false_alarms", 0), r.get("noise_alarms", []).size(), rows, fl if fl != "" else "<li>keine</li>", nl if nl != "" else "<li>keine</li>", r.get("note", "")]


func open_report() -> void:
	if last_html != "" and FileAccess.file_exists(last_html):
		OS.shell_open(last_html)
	else:
		info = "Noch kein Bericht – zuerst einen Testlauf machen."
		paint()


func add_info(body, UI) -> void:
	label = UI.small("", UI.TXT)
	label.add_theme_font_size_override("font_size", 13)
	body.add_child(label)
	paint()


func paint() -> void:
	if label != null:
		label.text = info


func status() -> String:
	if running:
		return "Testlauf läuft (Phase %d/%d)" % [phase + 1, PHASES.size()]
	if not report.is_empty():
		return "Testlauf: Personen %d/%d, Fehlalarme %d" % [report["persons_detected"], report["persons"], report["false_alarms"]]
	return ""
