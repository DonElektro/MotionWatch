extends Node
## Test run with evaluation (from 3D-2.6): a fixed sequence of phases (day, wind and clouds, night with insects, rain at
## night) with visitors crossing the picture. The simulator knows the truth (who is visible to the cameras, when) and
## compares it with what MoveEye reports (sim_state «det», from MoveEye 2.93.3): persons recognised, how fast,
## animals reported, false alarms and their probable cause, noise alarms. Report: in the window, on the web page of
## MoveEye (status), as JSON / HTML file in the user folder (testlauf/), and via CONTROL {"action": "test_report"}.
## Prüfstand 2 (Wunsch Daniel, 29.10.2026):
##  - the headline are the real PUSH messages of MoveEye (det.pushes, MoveEye part 068): each one is «richtig» (a person was
##    visible or in the picture just before) or «falsch»; the same visitor again within 10 s counts once. Every 0→>0 change
##    of the person count stays as «Flackern» (it was called «Fehlalarme» before).
##  - at night without light the THERMAL camera is truth and sensor too: a person counts as visible when the thermal camera
##    sees the warm body big enough (cams[2]); such persons are reported separately («nur Wärmebild»).
##  - plan «nacht»: a whole night 20–6 h in time-lapse with animals, wind, a rain shower and 2 persons (pushes per night).
##  - seeds: seed 1 = the fixed 4711 of before, seed 2, 3 … other positions (the spread shows how sure the numbers are).
##  - plan «echtenaechte»: alarm tracks of real nights (simulator3d/pruefnaechte/*.json, format in pruefstand/LIESMICH.md)
##    walked again, as recorded and with other weather / time.

var main

const STANDARD := [
	{"name": "Tag, klar", "hour": 11.0, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "deer", "child", "person"]},
	{"name": "Tag, Wind und Wolken", "hour": 14.5, "weather": "cloudy", "wind": 65.0, "visits": ["person", "cat", "jogger", "person"]},
	{"name": "Nacht, klar (Insekten am Licht)", "hour": 22.5, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "boar"]},
	{"name": "Nacht, Regen", "hour": 23.5, "weather": "rain", "wind": 20.0, "visits": ["person", "cat", "person"]},
]
# 3D-3.27: more test runs. «cond» = difficult conditions of main.gd (switched on only during the phase)
const DAUER := {"quick": 150, "night": 230, "standard": 300, "hard": 520, "nacht": 650, "camping_voll": 290, "tarnen": 270, "velodieb": 230, "gegenstaende": 290}   # 3D-3.90: the one place for names and times (also the test bench)
# Prüfstand 2: a whole night in time-lapse. «until» = the hour at the end of the phase (the clock runs faster meanwhile),
# «every» = a visitor every … s, "-" = a quiet slot (nobody comes: wind and rain alone must not give a push).
# Realistic numbers: about 20 animals, 2 persons in 10 hours; «fixed»: --mal does not multiply it.
const NACHT := [
	{"name": "Abend, Dämmerung", "hour": 20.0, "until": 21.5, "weather": "clear", "wind": 15.0, "visits": ["cat", "person", "-", "fox"]},
	{"name": "Nacht, Windböen", "hour": 21.5, "until": 23.0, "weather": "cloudy", "wind": 60.0, "visits": ["-", "hedgehog", "-", "badger", "cat"]},
	{"name": "Nacht, Regenschauer", "hour": 23.0, "until": 0.5, "weather": "rain", "wind": 30.0, "visits": ["-", "fox", "-", "hare"]},
	{"name": "Mitternacht, nach dem Regen", "hour": 0.5, "until": 2.5, "weather": "cloudy", "wind": 10.0, "visits": ["boar", "-", "person", "badger"]},
	{"name": "Tiefe Nacht", "hour": 2.5, "until": 4.5, "weather": "clear", "wind": 5.0, "visits": ["hedgehog", "fox", "-", "cat", "marten"]},
	{"name": "Morgendämmerung", "hour": 4.5, "until": 6.0, "weather": "clear", "wind": 20.0, "visits": ["deer", "-", "hare", "deer"]},
]
const PLANS := {
	"standard": {"name": "Standard (Tag, Wind, Nacht, Regen · etwa 5 Min.)", "phases": STANDARD},
	"quick": {"name": "Kurz (Tag und Nacht · etwa 2½ Min., für die automatische Optimierung)", "phases": [
		{"name": "Tag, Wind", "hour": 13.0, "weather": "cloudy", "wind": 45.0, "visits": ["person", "fox", "jogger", "person"]},
		{"name": "Nacht mit Infrarot", "hour": 22.5, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["person", "cat", "person"]}]},
	"hard": {"name": "Schwierige Bedingungen (Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten · etwa 9 Min.)", "phases": [
		{"name": "Gegenlicht am Morgen", "hour": 7.3, "weather": "clear", "wind": 35.0, "cond": ["glare"], "visits": ["person", "deer", "person"]},
		{"name": "Nebel", "hour": 9.0, "weather": "fog", "wind": 5.0, "visits": ["person", "fox", "person"]},
		{"name": "Schnee", "hour": 15.0, "weather": "snow", "wind": 25.0, "visits": ["person", "hare", "child"]},
		{"name": "Tropfen auf der Linse", "hour": 12.0, "weather": "cloudy", "wind": 15.0, "cond": ["drops"], "visits": ["person", "cat", "person"]},
		{"name": "Spinnennetz, Nacht mit Infrarot", "hour": 23.0, "weather": "clear", "wind": 30.0, "cond": ["web", "ir"], "visits": ["person", "fox", "person"]},
		{"name": "Scheinwerfer in der Nacht", "hour": 22.0, "weather": "clear", "wind": 5.0, "cond": ["headlights"], "visits": ["person", "badger", "person"]},
		{"name": "Wolkenschatten und Wind", "hour": 14.0, "weather": "cloudy", "wind": 55.0, "cond": ["shadows"], "visits": ["person", "cat", "jogger"]}]},
	"nacht": {"name": "Ganze Nacht (20–6 Uhr im Zeitraffer, Tiere, Wind, Regenschauer, 2 Personen · etwa 11 Min.)", "phases": NACHT, "every": 20.0, "fixed": true},
	# 3D-4.x «Neue Szenen» (szenenplus.gd): each plan loads its own scene («scene») and puts it back at the end; «dists» =
	# the distances of the ways through the picture (crawling: near); «-» = a quiet slot (only the neighbours move)
	"camping_voll": {"name": "Voller Campingplatz (Nachbarn bewegen sich, Fremde kommen an deinen Platz · etwa 5 Min.)", "scene": "camping_voll", "every": 24.0, "phases": [
		{"name": "Nachmittag, Nachbarn kochen, Kinder spielen", "hour": 15.5, "weather": "clear", "wind": 10.0, "visits": ["platz_besuch", "-", "platz_besuch"]},
		{"name": "Nacht mit Infrarot, Nachbarn gehen zum WC", "hour": 23.0, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["-", "platz_besuch", "-"]}]},
	"tarnen": {"name": "Tarnen und Kriechen (Tarnkleidung, robben, Schirm, Karton · etwa 4½ Min.)", "scene": "tarnen", "every": 16.0, "phases": [
		{"name": "Tag, Tarnkleidung und Robben", "hour": 13.0, "weather": "clear", "wind": 10.0, "dists": [6.0, 8.0, 10.0, 7.0], "visits": ["tarn_robben", "tarn_schirm", "tarn_karton", "tarn_robben"]},
		{"name": "Dämmerung", "hour": 20.3, "weather": "cloudy", "wind": 15.0, "dists": [6.0, 8.0, 10.0], "visits": ["tarn_robben", "tarn_karton", "tarn_schirm"]},
		{"name": "Nacht mit Infrarot", "hour": 23.0, "weather": "clear", "wind": 10.0, "cond": ["ir"], "dists": [5.0, 6.5, 8.0], "visits": ["tarn_robben", "tarn_schirm", "tarn_karton"]}]},
	"velodieb": {"name": "Velodieb (schnell hin, Velo greifen, weg – Reaktionszeit · etwa 4 Min.)", "scene": "velodieb", "every": 18.0, "phases": [
		{"name": "Tag", "hour": 14.0, "weather": "clear", "wind": 10.0, "visits": ["velodieb", "-", "velodieb"]},
		{"name": "Dämmerung", "hour": 20.4, "weather": "cloudy", "wind": 15.0, "visits": ["velodieb", "-"]},
		{"name": "Nacht mit Infrarot", "hour": 23.5, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["velodieb", "-", "velodieb"]}]},
	# 3D-4.x «Gegenstände» (objekte_plus.gd TEST_SET): things in front of the head camera - fluttering, swinging, glowing, luring.
	# Persons and animals count as truth; the things the AI does not know must not give a push («lure» = an animal goes to a lure,
	# robots = no persons). Only on Sundays / by hand (not in «quick»).
	"gegenstaende": {"name": "Gegenstände (Wind, Lampen, Feuer, Lockmittel, Wertsachen vor der Kamera – unbekannte Dinge dürfen nicht alarmieren · etwa 5 Min.)", "props": true, "every": 16.0, "phases": [
		{"name": "Tag, Böen (Fahne, Plastiksack, Ballon, Wäsche, Tor, Obstbaum)", "hour": 13.0, "weather": "cloudy", "wind": 55.0, "visits": ["person", "-", "lure", "robomower", "person"]},
		{"name": "Dämmerung, Tiere am Lockmittel", "hour": 20.6, "weather": "clear", "wind": 25.0, "visits": ["lure", "-", "person", "lure"]},
		{"name": "Nacht mit Infrarot (Lampe mit Bewegungsmelder, Feuer, Kerze, Solarleuchten)", "hour": 23.0, "weather": "clear", "wind": 30.0, "cond": ["ir"], "visits": ["lure", "person", "-", "delivery_bot", "e_trotti"]}]},
	"night": {"name": "Nacht (dunkel, Infrarot, Tiere · etwa 4 Min.)", "phases": [
		{"name": "Nacht, ohne Licht", "hour": 1.0, "weather": "clear", "wind": 5.0, "visits": ["person", "fox", "person", "hedgehog"]},
		{"name": "Nacht, Infrarot an", "hour": 2.0, "weather": "clear", "wind": 10.0, "cond": ["ir"], "visits": ["person", "boar", "child", "badger"]},
		{"name": "Nacht, Regen", "hour": 3.0, "weather": "rain", "wind": 25.0, "visits": ["person", "cat", "person"]}]},
}
const COND_NAMES := {"glare": "Gegenlicht", "drops": "Tropfen auf der Linse", "web": "Spinnennetz", "headlights": "Scheinwerfer",
		"shadows": "Wolkenschatten", "ir": "Infrarot"}
var plan := "standard"
var mult := 1                           # 3D-4.0: every visitor list of a phase so many times (the test bench: more visitors = surer numbers)
var seed_n := 1                         # Prüfstand 2: 1 = the fixed visitors of before (4711), 2, 3 … other positions
var truth_cams := [0, 1]                # 3D-3.48: which cameras count for the truth (the test bench: only the head camera, 0)
var PHASES: Array = STANDARD
var _cond_saved := {}
var _props_rep := {}                    # 3D-4.x plan «gegenstaende»: objekte_plus.report_extra (made before the things go away)
const EVERY := 13.0                     # a new visitor every ... seconds
const SETTLE := 15.0                    # quiet time at the start of a phase (MoveEye and the exposure of the camera adapt - 3D-4.0: 8 → 15 s)
const GRACE := 2.5                      # a report counts for a visitor up to ... s after it was last visible
const PUSH_WIN := 6.0                   # Prüfstand 2: a push is «richtig» when a person was visible up to … s before it came
const SAME_S := 10.0                    # the same visitor (or the same false cause) again within … s counts once
const TH_VFOV := 35.0                   # thermal camera, vertical field of view (main.gd: TH_FOV 45° wide)

var running := false
var phase := -1
var t_phase := 0.0
var next_visit := 0.0
var visit_i := 0
var truth := {}                         # instance id -> record of a visitor
var falses: Array = []                  # «Flackern»: every new person report without a visible person {t, phase, cause, dup}
var pushes: Array = []                  # Prüfstand 2: the real pushes of MoveEye {t, phase, ev, ok, who, dup}
var _push_seen := {}
var _push_known := false                # MoveEye sends its pushes (part 068) - else the report says «unbekannt»
var _last_false_push := -100.0
var _last_flicker := -100.0
var _pending: Array = []                # echtenaechte: figures that come later in the recorded track [t, kind, route, speed]
var _speed_saved := 1.0
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
	var nc: int = cases().size()
	if nc > 0:                                            # Prüfstand 2: alarm tracks of real nights
		o.append(["echtenaechte", "Echte Nächte nachspielen (%d Alarm-Spuren, auch mit anderem Wetter)" % nc])
	return o


# ---- Prüfstand 2: real nights (alarm tracks of MoveEye, «Alarm-Rückblick in 3D») as bench cases ----------------------
# A case file (simulator3d/pruefnaechte/*.json or user://pruefstand/faelle/*.json):
#   {"v": 1, "title": "…", "date": "2026-11-02 23:41", "hour": 23.7, "weather": "clear", "wind": 10,
#    "variants": [{"name": "…", "hour": 1.0, "weather": "rain", "wind": 25, "cond": ["ir"]}, …]   (optional)
#    "samples": [{"t": 1730587260.1, "pan": 12.0, "tilt": -3.0, "objs": [{"k": "person", "x": 0.41, "y": 0.62, "h": 0.22}]}, …]}
# «samples» is exactly what MoveEye keeps round an alarm (part 180, alarm_track_sample). Without «variants»: as recorded,
# at night in the rain, at night without light, by day.
const CASE_VARIANTS := [
	{"name": "Nacht, Regen", "hour": 23.5, "weather": "rain", "wind": 25.0},
	{"name": "Nacht, ohne Licht", "hour": 1.5, "weather": "clear", "wind": 5.0},
	{"name": "Tag, Wind", "hour": 13.0, "weather": "cloudy", "wind": 45.0},
]
var _cases: Array = []
var _cases_t := -100.0


static func load_cases() -> Array:
	var out: Array = []
	for base in ["res://pruefnaechte", "user://pruefstand/faelle"]:
		var d := DirAccess.open(base)
		if d == null:
			continue
		for fn in d.get_files():
			if not fn.ends_with(".json"):
				continue
			var c = JSON.parse_string(FileAccess.get_file_as_string(base + "/" + fn))
			if typeof(c) == TYPE_DICTIONARY and typeof(c.get("samples")) == TYPE_ARRAY and c["samples"].size() >= 3:
				c["file"] = base + "/" + fn
				out.append(c)
	out.sort_custom(func(a, b): return str(a.get("date", "")) > str(b.get("date", "")))
	return out


func cases() -> Array:
	if now() - _cases_t > 10.0:
		_cases = load_cases().slice(0, 4)
		_cases_t = now()
	return _cases


func _case_phases() -> Array:
	var out: Array = []
	for i in range(cases().size()):
		var c: Dictionary = cases()[i]
		var smp: Array = c["samples"]
		var dur: float = float(smp[-1].get("t", 0.0)) - float(smp[0].get("t", 0.0))
		var title: String = str(c.get("title", "Alarm %s" % str(c.get("date", "")).left(16)))
		var vs: Array = [{"name": "wie aufgenommen", "hour": float(c.get("hour", 23.0)), "weather": str(c.get("weather", "clear")), "wind": float(c.get("wind", 10.0))}]
		vs.append_array(c.get("variants", CASE_VARIANTS) if typeof(c.get("variants")) == TYPE_ARRAY else CASE_VARIANTS)
		for va in vs:
			out.append({"name": "%s · %s" % [title, str(va.get("name", "?"))], "hour": float(va.get("hour", 23.0)), "weather": str(va.get("weather", "clear")),
					"wind": float(va.get("wind", 10.0)), "cond": va.get("cond", []), "visits": ["case:%d" % i], "way_s": dur + 4.0})
	return out


func _track_point(s: Dictionary, o: Dictionary) -> Vector3:
	"""like replay.gd: the spot of a box in the picture of the head camera → a point on the ground"""
	var fov_h := deg_to_rad(float(main.CAM_FOV[0]))
	var fov_v := deg_to_rad(41.0)
	var h := clampf(float(o.get("h", 0.2)), 0.02, 1.0)
	var k := str(o.get("k", "person"))
	var real_h := 1.7 if k == "person" else (1.0 if k in ["deer", "horse", "cow"] else 0.6)
	var dist := clampf(real_h / (2.0 * tan(fov_v / 2.0) * h), 1.5, 40.0)
	var yaw: float = main.rig.rotation.y - deg_to_rad(float(s.get("pan", 0.0))) - (float(o.get("x", 0.5)) - 0.5) * fov_h
	var p: Vector3 = main.rig.global_position + Vector3(-sin(yaw), 0, -cos(yaw)) * dist
	return Vector3(p.x, 0, p.z)


const TRACK_KIND := {"person": "person", "cat": "cat", "dog": "dog", "horse": "deer", "cow": "deer", "sheep": "deer", "bear": "boar", "deer": "deer",
		"fox": "fox", "boar": "boar", "badger": "badger", "hedgehog": "hedgehog"}


func case_figures(c: Dictionary) -> Array:
	"""the figures of a recorded track: [{kind, t (s after the start), pts: [Vector3], speed}] - the n-th object of a kind in
	each sample is the same figure (MoveEye keeps at most 6 persons and 4 animals per sample)"""
	var smp: Array = c["samples"].duplicate()
	smp.sort_custom(func(a, b): return float(a.get("t", 0)) < float(b.get("t", 0)))
	var ta := float(smp[0].get("t", 0.0))
	var figs := {}
	for s_ in smp:
		var cnt := {}
		for o in s_.get("objs", []):
			var k: String = str(o.get("k", "person"))
			if not TRACK_KIND.has(k) and k != "animal":
				continue
			var n: int = int(cnt.get(k, 0))
			cnt[k] = n + 1
			var key := "%s:%d" % [k, n]
			if not figs.has(key):
				figs[key] = {"kind": TRACK_KIND.get(k, "fox"), "t": float(s_.get("t", 0.0)) - ta, "pts": [], "ts": []}
			var p := _track_point(s_, o)
			var f: Dictionary = figs[key]
			if f["pts"].is_empty() or (f["pts"][-1] as Vector3).distance_to(p) > 0.4:
				f["pts"].append(p)
				f["ts"].append(float(s_.get("t", 0.0)) - ta)
	var out: Array = []
	for f in figs.values():
		if f["pts"].size() < 2:
			continue
		var d := 0.0
		for j in range(1, f["pts"].size()):
			d += (f["pts"][j] as Vector3).distance_to(f["pts"][j - 1])
		var span: float = max(0.5, float(f["ts"][-1]) - float(f["ts"][0]))
		out.append({"kind": f["kind"], "t": f["t"], "pts": f["pts"], "speed": clampf(d / span, 0.3, 4.0)})
	return out


func _spawn_figure(f: Dictionary):
	var pts: Array = f["pts"]
	var v = main.spawn(str(f["kind"]), pts[0], pts[1])
	var r: Array = []
	for k in range(2, pts.size()):
		r.append(pts[k])
	v.route = r
	v.speed = float(f["speed"])
	return v


func _note_visitor(v, k: String) -> void:
	truth[v.get_instance_id()] = {"kind": k, "person": v.kind == "person", "phase": phase, "first": -1.0, "last": -100.0,
			"vis": 0.0, "det": -1.0, "rep": false, "as_person": false, "seen_ever": false, "px": 0.0, "light": 1.0, "crouch": false,
			"cam": false, "th": false, "push": -1.0, "last_push": -100.0}


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
			"left_s": int(left), "total_s": int(duration()), "seed": seed_n, "mult": mult}


func duration() -> float:
	var s := 0.0
	for ph in PHASES:
		s += phase_s(ph)
	return s


func _fixed() -> bool:
	"""the visitor list is not multiplied (sneaking ways, real nights, the whole night: realistic numbers)"""
	return plan in ["spielwege", "echtenaechte"] or bool(PLANS.get(plan, {}).get("fixed", false))


func _every() -> float:
	return float(PLANS.get(plan, {}).get("every", EVERY))


func phase_s(ph: Dictionary) -> float:
	var n: int = ph["visits"].size() * (1 if _fixed() else mult)
	return SETTLE + max(_every() * n, float(ph.get("way_s", 0.0)) + 2.0) + 6.0


func _visit_kind(ph: Dictionary, i: int) -> String:
	var v: Array = ph["visits"]
	return str(v[i % v.size()])


func _route(i: int, ph: Dictionary) -> Array:
	"""3D-4.0: the way of a test visitor - straight through the picture of the head camera (before: across the whole place,
	many visitors never came into the picture or only far away, and at night never into the infrared light). Distances
	cycle (near / middle / far) so every run has the same mix; at night with light only as far as the light reaches."""
	var cam: Camera3D = main.cams[0]
	var o: Vector3 = cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var r := Vector3(-f.z, 0, f.x)
	var lit: bool = "ir" in ph.get("cond", []) or bool(main.mw.get("lights", {}).get("white", false))
	var ds: Array = [7.0, 11.0, 15.0, 9.0, 19.0, 13.0, 24.0] if float(ph["hour"]) > 6.5 and float(ph["hour"]) < 19.5 else \
			([4.0, 6.5, 9.0, 5.5, 11.0, 7.5] if lit else [5.0, 8.0, 12.0])
	if ph.has("dists"):
		ds = ph["dists"]                                  # 3D-4.x: the plan sets the distances (crawling persons: near)
	var d: float = ds[i % ds.size()] * randf_range(0.92, 1.08)
	var half: float = d * 0.68 + 5.0
	var side := 1.0 if i % 2 == 0 else -1.0
	var skew: float = randf_range(-0.25, 0.25) * d
	var a: Vector3 = o + f * (d + skew) - r * side * half
	var b: Vector3 = o + f * (d - skew) + r * side * half
	return [Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z)]


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


func start(which := "", cams: Array = [], times: int = 1, seed_: int = 1) -> String:
	if running:
		return "Es läuft schon ein Testlauf."
	mult = clampi(times, 1, 5)
	seed_n = clampi(seed_, 1, 99)
	truth_cams = [0, 1]
	if not cams.is_empty():
		truth_cams = []
		for c in cams:
			if int(c) in [0, 1] and not int(c) in truth_cams:
				truth_cams.append(int(c))
	if which != "":
		if not PLANS.has(which) and not which in ["spielwege", "echtenaechte"]:
			return "unbekannter Testlauf"
		plan = which
	if plan == "spielwege":
		PHASES = _way_phases()
		if PHASES.is_empty():
			plan = "standard"
			return "Noch keine Schleichwege – zuerst eine Spielrunde mit MoveEye spielen."
	elif plan == "echtenaechte":
		PHASES = _case_phases()
		if PHASES.is_empty():
			plan = "standard"
			return "Noch keine echten Nächte – zuerst einen Alarm-Rückblick als Prüfstand-Fall speichern."
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
	saved = {"hour": main.hour(), "weather": main.weather, "wind": main.wind, "auto": main.auto_visitors, "speed": main.speed}
	var psc := str(PLANS.get(plan, {}).get("scene", ""))
	if psc != "" and psc != main.scene:                  # 3D-4.x: a plan with its own scene (szenenplus.gd) - back at the end
		saved["scene"] = main.scene
		main.set_scene(psc)
	_cond_saved = main.cond.duplicate()
	main.auto_visitors = false
	main.clear_visitors()
	_props_rep = {}
	if bool(PLANS.get(plan, {}).get("props", false)) and main.objplus != null:
		main.objplus.test_place()                        # 3D-4.x «Gegenstände»: the fixed set in front of the head camera
	running = true
	truth.clear()
	falses.clear()
	noises.clear()
	pushes.clear()
	_pending.clear()
	_push_seen.clear()
	var pl = main.mw_det.get("pushes", null)
	_push_known = typeof(pl) == TYPE_ARRAY
	if _push_known:
		for x in pl:                                     # what MoveEye sent before the test run does not count
			_push_seen[str(x[0])] = true
	_last_false_push = -100.0
	_last_flicker = -100.0
	report = {}
	t0 = now()
	_start_phase(0)
	return ""


func stop(finished := false) -> void:
	if not running:
		return
	running = false
	main.speed = float(saved.get("speed", 1.0))
	main.set_hour(float(saved.get("hour", 12.0)))
	main.weather = str(saved.get("weather", "clear"))
	main.wind = float(saved.get("wind", 10.0))
	main.auto_visitors = bool(saved.get("auto", true))
	if not _cond_saved.is_empty():
		main.cond = _cond_saved.duplicate()
	main.clear_visitors()
	if main.szenen != null:
		main.szenen.restore()                            # 3D-4.x: a bike thief had the bike
	if main.objplus != null and bool(PLANS.get(plan, {}).get("props", false)):
		_props_rep = main.objplus.report_extra(self)
		main.objplus.test_clear()
	if finished:
		_make_report()
	else:
		info = "Testlauf abgebrochen."
	if saved.has("scene") and str(saved["scene"]) != main.scene:
		main.set_scene(str(saved["scene"]))
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
	_pending.clear()
	# the same visitors on the same ways every time: runs can be compared (seed 1 = the numbers of before; 2, 3 … other ways)
	seed(4711 + 1000 * (seed_n - 1) + 97 * i + plan.hash() % 1000)
	main.speed = 1.0
	if ph.has("until"):                                     # the whole night: the clock runs faster, from «hour» to «until»
		var span: float = fposmod(float(ph["until"]) - float(ph["hour"]), 24.0)
		main.speed = clampf(span * 3600.0 / max(30.0, phase_s(ph)), 1.0, 600.0)
		main.set_hour(float(ph["hour"]))
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
	if main.now() - main.mw_t > 25.0:                      # Prüfstand 2: 10 → 25 s (a busy PC answers late now and then)
		info = "MoveEye hat die Verbindung verloren – Testlauf abgebrochen."
		stop(false)
		return
	var ph: Dictionary = PHASES[phase]
	var n_vis: int = ph["visits"].size() * (1 if _fixed() else mult)
	for pd in _pending.duplicate():                       # echtenaechte: figures that appear later in the track
		if t >= float(pd[0]):
			_pending.erase(pd)
			var fv = _spawn_figure(pd[1])
			_note_visitor(fv, str(pd[1]["kind"]))
	if visit_i < n_vis and t >= next_visit:
		var k: String = _visit_kind(ph, visit_i)
		if k.begins_with("case:"):
			for f in case_figures(cases()[int(k.substr(5))]):
				_pending.append([t + float(f["t"]), f])
		elif k != "-":                                    # "-" = a quiet slot: nobody comes
			var v
			if k.begins_with("way:"):
				v = _spawn_way(int(k.substr(4)))
			elif k == "lure" and main.objplus != null:
				v = main.objplus.lure_visit()                # 3D-4.x: an animal goes to a lure of the set
			elif k in ["delivery_bot", "robomower"]:
				main.spawn(k)                                # 3D-4.x: no person - only robustness (no push expected)
				v = null
			else:
				var rt: Array = _route(visit_i, ph)
				v = main.spawn(k, rt[0], rt[1])
			if k.begins_with("way:"):
				k = "person"
			if v != null and v.get("kind") != null:
				_note_visitor(v, v.kind if k == "lure" else k)
		visit_i += 1
		next_visit = t + max(_every(), float(ph.get("way_s", 0.0)) + 2.0)
	elif visit_i >= n_vis and t >= next_visit + 6.0:
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
		# 3D-4.0: also the body must be free (before: the head over a tent counted as «well visible»)
		if not main.line_free(cp, pos + Vector3(0, h * 0.6, 0)) and not main.line_free(cp, pos + Vector3(0, h * 0.35, 0)):
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


var _th_px := 0.0


func thermal_visible(v) -> bool:
	"""Prüfstand 2: at night the thermal camera (cams[2], on the head) sees the warm body - big enough, free view, warmer than
	the night (MoveEye 2.98.14 and newer finds persons in the thermal picture, part 232). Fog and rain cool the picture."""
	if main.cams.size() < 3 or not main.is_dark():
		return false
	var cam: Camera3D = main.cams[2]
	var h: float = 1.7 * v.body_root.scale.y if v.kind == "person" else max(0.4, float(v.body_h) * 1.5)
	var pos: Vector3 = v.position
	var cp := cam.global_position
	var d: float = max(0.5, cp.distance_to(pos))
	if not cam.is_position_in_frustum(pos + Vector3(0, h * 0.6, 0)):
		return false
	if not main.line_free(cp, pos + Vector3(0, h * 0.6, 0)):
		return false
	if absf(34.0 - float(main.ambient)) < 6.0:
		return false                                       # a hot summer night: the body is hardly warmer than the ground
	var vf: float = float(main.simint.th()["fov_v"]) if main.simint != null else TH_VFOV   # 30.10.2026: the chosen thermal model
	var px: float = h / (2.0 * d * tan(deg_to_rad(vf) / 2.0)) * float(main.TH_H)
	var need: float = (8.0 if v.kind == "person" else 4.0) * {"fog": 1.6, "rain": 1.25, "snow": 1.25}.get(main.weather, 1.0)
	_th_px = px
	return px >= need


func _cause(animals_vis: Array) -> String:
	"""the probable cause of a report without a visible person"""
	var conds: Array = PHASES[phase].get("cond", [])
	var nbc: String = main.szenen.cause(self) if main.szenen != null else ""
	if nbc != "":
		return nbc                                         # 3D-4.x «Voller Campingplatz»: a neighbour was in the picture
	if not animals_vis.is_empty():
		return "Tier (%s)" % ", ".join(PackedStringArray(animals_vis))
	if "web" in conds:
		return "Spinnennetz"
	if "glare" in conds:
		return "Gegenlicht"
	if "headlights" in conds:
		return "Scheinwerfer"
	if "drops" in conds:
		return "Tropfen auf der Linse"
	if "shadows" in conds:
		return "Wolkenschatten"
	if main.weather == "snow":
		return "Schnee"
	if main.weather == "fog":
		return "Nebel"
	if main.insects != null and main.insects.emitting:
		return "Insekten am Licht"
	if main.wind > 40.0:
		return "Wind (Bäume, Büsche)"
	if main.weather == "rain":
		return "Regen"
	return "unbekannt"


func _sample(dt: float) -> void:
	var t := now()
	var det: Dictionary = main.mw_det
	var persons := int(det.get("persons", 0))
	var present: Array = det.get("present", [])
	var any_person_vis := false
	var any_present := false
	var animals_vis := []
	var best_person = null                                 # the person seen last (for the push: who was it?)
	var best_last := -100.0
	for v in main.visitors.get_children():
		var id: int = v.get_instance_id()
		if not truth.has(id) or v.is_queued_for_deletion():
			continue
		var r: Dictionary = truth[id]
		if int(r["phase"]) != phase:
			continue                                        # Prüfstand 2: a visitor of the phase before (just removed) - not in the new light
		var cam_v: bool = visible(v)
		var th_v: bool = thermal_visible(v) if not cam_v else false
		if cam_v or th_v:
			if float(r["first"]) < 0.0:
				r["first"] = t
			r["last"] = t
			r["vis"] = float(r["vis"]) + dt
			if cam_v:
				r["cam"] = true
				r["px"] = max(float(r["px"]), _vis_px)
				r["light"] = min(float(r["light"]), _vis_light)
			else:
				r["th"] = true
				r["th_px"] = max(float(r.get("th_px", 0.0)), _th_px)
				r["light"] = min(float(r["light"]), main.game.light_at(v.position, 0))
			if v.kind == "person" and float(v.get("crouch") if v.get("crouch") != null else 0.0) > 0.3:
				r["crouch"] = true
		var recent := t - float(r["last"]) <= GRACE and float(r["first"]) >= 0.0
		if r["person"] and present(v):
			any_present = true
			r["seen_ever"] = true
			r["in_pic"] = t
		if r["person"]:
			if recent:
				any_person_vis = true
				if persons > 0 and float(r["det"]) < 0.0:
					r["det"] = t
			var lp: float = max(float(r["last"]) if float(r["first"]) >= 0.0 else -100.0, float(r.get("in_pic", -100.0)))
			if lp > best_last:
				best_last = lp
				best_person = id
		else:
			if recent:
				animals_vis.append(r["kind"])
				if "animal" in present or "motion" in present or "prealarm" in present:
					r["rep"] = true
				if persons > 0:
					r["as_person"] = true
	if any_person_vis or any_present:
		_last_person_vis = t
	# «Flackern»: every new person report without a visible person (with the probable cause; again within 10 s = «dup»)
	if persons > 0 and _prev_persons == 0 and t - _last_person_vis > GRACE:
		falses.append({"t": snappedf(t - t0, 0.1), "phase": phase, "cause": _cause(animals_vis), "dup": t - _last_flicker < SAME_S})
		_last_flicker = t
	_prev_persons = persons
	_check_pushes(det, t, best_person, best_last, animals_vis)
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


const ALARM_EVS := ["person", "warm", "prealarm"]


func _check_pushes(det: Dictionary, t: float, best_person, best_last: float, animals_vis: Array) -> void:
	"""Prüfstand 2: the new push messages of MoveEye (det.pushes = the newest messages of its list «Nachrichten»):
	«richtig» when a person was visible (or at least in the picture) up to PUSH_WIN s before, else «falsch»"""
	var pl = det.get("pushes", null)
	if typeof(pl) != TYPE_ARRAY:
		return
	if not _push_known:
		_push_known = true
		for x in pl:
			_push_seen[str(x[0])] = true
		return
	for x in pl:
		if typeof(x) != TYPE_ARRAY or x.size() < 3 or _push_seen.has(str(x[0])):
			continue
		_push_seen[str(x[0])] = true
		var ev := str(x[2])
		var rec := {"t": snappedf(t - t0, 0.1), "phase": phase, "ev": ev, "ok": false, "who": "", "dup": false}
		if ev == "noise":
			rec["who"] = "Geräusch"
		elif not ev in ALARM_EVS:
			continue                                        # info messages (address, night report …) are no alarms
		elif best_person != null and t - best_last <= PUSH_WIN:
			var r: Dictionary = truth[best_person]
			rec["ok"] = true
			rec["who"] = str(r["kind"]) + (" (nur Wärmebild)" if bool(r.get("th")) and not bool(r.get("cam")) else "")
			rec["dup"] = t - float(r["last_push"]) < SAME_S    # the same visitor again within 10 s: counts once
			r["last_push"] = t
			if float(r["push"]) < 0.0:
				r["push"] = t
		else:
			rec["who"] = _cause(animals_vis)
			rec["dup"] = t - _last_false_push < SAME_S
			_last_false_push = t
		pushes.append(rec)


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
					"det_s": snappedf(float(r0["det"]) - float(r0["first"]), 0.1) if float(r0["det"]) >= 0.0 else -1.0, "reported": r0["rep"],
					"thermal_only": bool(r0.get("th")) and not bool(r0.get("cam")), "th_px": int(float(r0.get("th_px", 0.0))),
					"push_s": snappedf(float(r0["push"]) - float(r0["first"]), 0.1) if float(r0.get("push", -1.0)) >= 0.0 else -1.0})
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
		var tn := 0                                    # Prüfstand 2: persons only the thermal camera saw
		var tdn := 0
		var pushed := 0
		for r in truth.values():
			if int(r["phase"]) != i:
				continue
			if float(r["first"]) < 0.0:
				if r["person"]:
					hidden += 1                            # never well visible (too dark, too far, hidden): does not count
				continue
			if r["person"]:
				pn += 1
				if bool(r.get("th")) and not bool(r.get("cam")):
					tn += 1
					if float(r["det"]) >= 0.0:
						tdn += 1
				if float(r.get("push", -1.0)) >= 0.0:
					pushed += 1
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
		var fe := falses.filter(func(f): return int(f["phase"]) == i and not bool(f.get("dup", false))).size()
		var pu: Dictionary = push_numbers(i)
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
				"cond": PHASES[i].get("cond", []), "dark": float(PHASES[i]["hour"]) < 6.0 or float(PHASES[i]["hour"]) > 20.5,
				"flicker": fa, "false_events": fe, "persons_thermal": tn, "persons_thermal_detected": tdn, "persons_pushed": pushed,
				"pushes_ok": pu["ok"], "pushes_false": pu["false"], "pushes_noise": pu["noise"], "pushes_repeat": pu["repeat"]})
	var lat_avg := -1.0
	if not lat_all.is_empty():
		var s2 := 0.0
		for x in lat_all:
			s2 += x
		lat_avg = s2 / lat_all.size()
	var dev := str(main.mw.get("device", "MoveEye"))
	var pa: Dictionary = push_numbers(-1)
	var fe_all := falses.filter(func(f): return not bool(f.get("dup", false))).size()
	var th_all := 0
	var thd_all := 0
	for p_ in phs:
		th_all += int(p_["persons_thermal"])
		thd_all += int(p_["persons_thermal_detected"])
	var pname: String = str(PLANS[plan]["name"]) if PLANS.has(plan) else ("Schleichwege aus dem Spiel" if plan == "spielwege" else "Echte Nächte nachgespielt")
	report = {"v": 3, "plan": plan, "plan_name": pname, "seed": seed_n,
			"pushes": pa if _push_known else {}, "push_list": pushes, "flicker": falses.size(), "false_events": fe_all,
			"persons_thermal": th_all, "persons_thermal_detected": thd_all, "date": Time.get_datetime_string_from_system(false, true), "simulator": main.version(), "scene": main.scene,
			"device": dev, "persons": tp, "persons_detected": td, "rate": snappedf(100.0 * td / max(1, tp), 1),
			"latency_s": snappedf(lat_avg, 0.1), "false_alarms": falses.size(), "false_list": falses, "missed_list": all_missed, "noise_alarms": noises,
			"phases": phs, "truth_cams": truth_cams, "visitors": each, "mult": mult,
			"realism": {"fx": bool(main.realism.fx_on), "look": bool(main.realism.real_on)} if main.realism != null else {},
			"szene": _props_rep if not _props_rep.is_empty() else (main.szenen.report_extra(self) if main.szenen != null else {}),
			"note": ("Wahrheit: sichtbar für Kopf- oder Weitwinkel-Kamera" if truth_cams.size() > 1 else "Wahrheit: sichtbar für die Kopfkamera") + " (frei, gross genug, genug Licht) – nachts auch für die Wärmebildkamera (warm und gross genug)."}
	info = "Testlauf fertig: Personen erkannt %d von %d (%d %%), Reaktionszeit %s, %s, Flackern %d, Geräuschalarme %d." % [
			td, tp, int(report["rate"]), ("%.1f s" % lat_avg) if lat_avg >= 0.0 else "–",
			("Pushes richtig %d / falsch %d" % [pa["ok"], pa["false"]]) if _push_known else "Pushes unbekannt (MoveEye zu alt)", falses.size(), noises.size()]
	_save()


func push_numbers(ph_i: int) -> Dictionary:
	"""the pushes of one phase (or all: -1): right, false (each counted once within 10 s), noise, repeats left out"""
	var o := {"alarm": 0, "ok": 0, "false": 0, "noise": 0, "repeat": 0, "raw": 0}
	for p in pushes:
		if ph_i >= 0 and int(p["phase"]) != ph_i:
			continue
		if p["ev"] == "noise":
			o["noise"] += 1
			continue
		o["raw"] += 1
		if bool(p["dup"]):
			o["repeat"] += 1
			continue
		o["alarm"] += 1
		o["ok" if bool(p["ok"]) else "false"] += 1
	return o


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
		rows += "<tr><td>%s</td><td>%d / %d%s</td><td>%s</td><td>%s</td><td>%d / %d</td><td>%d</td><td>%s</td><td>%d</td></tr>" % [p["name"], p["persons_detected"], p["persons"],
				(" <span class=mut>(Wärmebild %d / %d)</span>" % [p.get("persons_thermal_detected", 0), p.get("persons_thermal", 0)]) if int(p.get("persons_thermal", 0)) > 0 else "",
				("%.1f s" % p["latency_s"]) if float(p["latency_s"]) >= 0.0 else "–",
				("%d / %d" % [p.get("pushes_ok", 0), p.get("pushes_false", 0)]) if not r.get("pushes", {}).is_empty() else "?",
				p["animals_reported"], p["animals"], p.get("flicker", p["false_alarms"]),
				", ".join(PackedStringArray(p["missed"])) if not p["missed"].is_empty() else "–", p.get("not_visible", 0)]
	var pl := ""
	for q in r.get("push_list", []):
		pl += "<li>%.0f s · %s · %s · %s%s</li>" % [q["t"], PHASES[int(q["phase"])]["name"], q["ev"], ("richtig: " if q["ok"] else "FALSCH: ") + str(q["who"]),
				" <span class=mut>(gleicher Besuch innert 10 s – zählt nicht)</span>" if q["dup"] else ""]
	var fl := ""
	for f in r.get("false_list", []):
		fl += "<li>%.0f s · %s · %s</li>" % [f["t"], PHASES[int(f["phase"])]["name"], f["cause"]]
	var nl := ""
	for n in r.get("noise_alarms", []):
		nl += "<li>%.0f s · %s · %s</li>" % [n["t"], PHASES[int(n["phase"])]["name"], n["cause"]]
	var pu: Dictionary = r.get("pushes", {})
	var push_t: String = ("%d / %d" % [pu["ok"], pu["false"]]) if not pu.is_empty() else "?"
	return """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Testlauf %s</title><style>body{font:15px system-ui,sans-serif;background:#0a0e14;color:#e6edf3;margin:0;padding:20px;max-width:900px}
h1{font-size:22px}.big{display:flex;gap:12px;flex-wrap:wrap}.t{background:#151e2b;border:1px solid #1f2b3a;border-radius:12px;padding:12px 16px}
.t b{display:block;font-size:26px}table{border-collapse:collapse;width:100%%;margin-top:14px}td,th{border-bottom:1px solid #1f2b3a;padding:6px 8px;text-align:left}
.mut{color:#8b98a8}</style></head><body><h1>Testlauf · %s</h1><p class="mut">%s · Szene %s · Simulator %s · Zufall %d</p>
<div class="big"><div class="t">Pushes richtig / falsch<b>%s</b></div><div class="t">Personen erkannt<b>%d / %d (%s %%)</b></div><div class="t">Reaktionszeit (Mittel)<b>%s</b></div>
<div class="t">Flackern (Person kurz gemeldet)<b>%d</b></div><div class="t">Geräuschalarme<b>%d</b></div></div>
<table><tr><th>Phase</th><th>Personen erkannt</th><th>Reaktionszeit</th><th>Pushes richtig / falsch</th><th>Tiere gemeldet</th><th>Flackern</th><th>Nicht erkannt</th><th>Für die Kamera unsichtbar</th></tr>%s</table>
<h3>Pushes</h3><ul>%s</ul><h3>Flackern (ohne sichtbare Person)</h3><ul>%s</ul><h3>Geräuschalarme</h3><ul>%s</ul><p class="mut">%s</p></body></html>""" % [
			r.get("date", ""), r.get("device", ""), r.get("date", ""), r.get("scene", ""), r.get("simulator", ""), int(r.get("seed", 1)), push_t,
			r.get("persons_detected", 0), r.get("persons", 0), str(r.get("rate", 0)), ("%.1f s" % r["latency_s"]) if float(r.get("latency_s", -1)) >= 0.0 else "–",
			r.get("flicker", r.get("false_alarms", 0)), r.get("noise_alarms", []).size(), rows, pl if pl != "" else "<li>keine</li>",
			fl if fl != "" else "<li>keine</li>", nl if nl != "" else "<li>keine</li>", r.get("note", "")]


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
		var pu: Dictionary = report.get("pushes", {})
		return "Testlauf: Personen %d/%d, Pushes %s, Flackern %d" % [report["persons_detected"], report["persons"],
				("%d richtig / %d falsch" % [pu["ok"], pu["false"]]) if not pu.is_empty() else "?", report.get("flicker", report["false_alarms"])]
	return ""
