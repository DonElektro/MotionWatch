extends Node
## Nacht-Testlauf (Paket «Nacht-Testlauf», Daniel 31.10.2026): MoveEye (Seite «Sim», nur der Besitzer) startet eine ganze
## Nacht im Simulator; hier läuft ein Ablauf mit festem Zufall («seed») und hier wird die «Wahrheit» aufgeschrieben:
##   * jedes Ereignis mit Beginn / Ende (Sekunden ab Start, echte Zeit), Simulator-Uhr, Ort (Start, nächster Punkt zum
##     Gerät, ein paar Wegpunkte), wie lange es für die Kopf- oder Wärmebildkamera sichtbar war (testrun.visible /
##     thermal_visible - dieselbe Wahrheit wie Testlauf und Prüfstand),
##   * Ereignisse: WC-Gänge (manche mit Taschenlampe), Katze / Fuchs / Igel, ein spätes Auto (Scheinwerfer), eine Stunde
##     Regen, Windböen, Morgennebel und GENAU EIN echter Vorfall (jemand schleicht zu Zelt, Velo oder Wohnwagen / Auto),
##   * Tempo: «echt» (1×) oder «schnell» (8×: 8 h in 1 h); die Besucher laufen in echter Zeit, die Uhr schneller.
## MoveEye fragt mit {"action": "nacht", "do": "state"} den Fortschritt ab und holt am Schluss {"do": "truth"} – den
## Abgleich (Treffer, verpasst, Fehlalarme mit Ursache, Zeit bis erkannt) macht MoveEye (Teil 579b), der Bericht steht dort.
##
## Später einstecken (die Realismus-Pakete «Menschen», «Tiere», «Licht» sind noch nicht zusammengeführt): jede Ereignis-Art
## wird über HANDLERS gespielt. Ein Paket ersetzt eine Art mit register_kind("wc", func(ev): … return [actor, …]) – der
## Ablauf, die Wahrheit und der Abgleich bleiben gleich. Neue Arten: register_kind("dachs", …, "animal", "badger") – die
## Ursache («cause») ist der Schlüssel, den MoveEye übersetzt (unbekannte Schlüssel erscheinen so, wie sie sind).
##
## Control API: {"action": "nacht", "do": info | start (scene, busy ruhig|normal|viel, tempo echt|schnell, speed, from, to,
##               seed) | stop | state | truth}

const T = preload("res://scripts/i18n.gd")

var main
var running := false
var run_id := ""
var opts := {}
var plan: Array = []                  # [{id, kind, at_s, dur_s, torch, target}] - sorted by at_s
var truth: Array = []                 # the «Wahrheit»: one record per started event
var active := {}                      # id -> {"rec": record, "actors": [Actor], "until": real s (weather), "cap": real s}
var next_i := 0
var t0 := 0.0
var total_s := 0.0
var speed_x := 8.0
var saved := {}
var last := {}                        # the last finished run (truth + meta) for MoveEye
var info := ""
var _sample_t := 0.0
var _hl_until := -1.0                 # the headlights effect of the late car (real s)
var label: Label
var stop_btn: Button
var _rng := RandomNumberGenerator.new()

const SAMPLE := 0.25
const BUSY := {"ruhig": {"wc": 0.15, "animal": 0.5, "car": 0.0}, "normal": {"wc": 0.3, "animal": 1.0, "car": 0.12},
		"viel": {"wc": 0.7, "animal": 1.8, "car": 0.3}}       # events per hour of the night
const TEMPO := {"echt": 1.0, "schnell": 8.0}
const ANIMALS := ["cat", "fox", "hedgehog"]
# kind -> [category, cause]: the cause is a key MoveEye translates (579b NACHT_CAUSES)
var KINDS := {"wc": ["people", "wc"], "cat": ["animal", "cat"], "fox": ["animal", "fox"], "hedgehog": ["animal", "hedgehog"],
		"car": ["vehicle", "car"], "rain": ["weather", "rain"], "wind": ["weather", "wind"], "fog": ["weather", "fog"],
		"incident": ["incident", "incident"]}
var HANDLERS := {}                    # kind -> Callable(ev) -> Array of actors (plug-in point for the realism packages)


func _ready() -> void:
	HANDLERS = {"wc": _ev_wc, "cat": _ev_animal, "fox": _ev_animal, "hedgehog": _ev_animal, "car": _ev_car, "incident": _ev_incident}


func register_kind(kind: String, f: Callable, cat := "", cause := "") -> void:
	"""a realism package plays a kind its own way (or adds a new one). f(ev) returns the actors it spawned (may be [])."""
	HANDLERS[kind] = f
	if cat != "" or not KINDS.has(kind):
		KINDS[kind] = [cat if cat != "" else "animal", cause if cause != "" else kind]


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func elapsed() -> float:
	return now() - t0 if running else 0.0


# ---- the plan: a seeded random night ---------------------------------------------------------------------------------
static func span_h(from_h: float, to_h: float) -> float:
	var s := fposmod(to_h - from_h, 24.0)
	return s if s > 0.01 else 24.0


func make_plan(o: Dictionary) -> Array:
	"""the events of one night: same seed + same options = the same night (also the order of the spawns)"""
	_rng.seed = int(o.get("seed", 1)) * 7919 + 13
	var sp: float = span_h(float(o["from"]), float(o["to"]))
	var real_s: float = sp * 3600.0 / float(o["speed"])
	var R: Dictionary = BUSY.get(str(o.get("busy", "normal")), BUSY["normal"])
	var out: Array = []
	var n_wc: int = maxi(1, roundi(R["wc"] * sp + _rng.randf_range(-0.5, 0.5)))
	var n_an: int = maxi(1, roundi(R["animal"] * sp + _rng.randf_range(-0.5, 0.5)))
	var n_car: int = maxi(0 if str(o.get("busy")) == "ruhig" else 1, roundi(R["car"] * sp + _rng.randf_range(-0.4, 0.4)))
	for i in range(n_wc):
		out.append({"kind": "wc", "at_h": _rng.randf_range(0.04, 0.92) * sp, "torch": _rng.randf() < 0.5})
	var kinds := ANIMALS.duplicate()
	for i in range(n_an):
		var k: String = kinds[i % kinds.size()] if i < kinds.size() else kinds[_rng.randi() % kinds.size()]
		out.append({"kind": k, "at_h": _rng.randf_range(0.03, 0.95) * sp})
	for i in range(n_car):
		# «a late car»: between 23:00 and 01:30 when the night has that time, else anywhere
		var late := fposmod(23.0 + _rng.randf_range(0.0, 2.5) - float(o["from"]), 24.0)
		out.append({"kind": "car", "at_h": late if late < sp * 0.95 else _rng.randf_range(0.1, 0.9) * sp})
	# weather: one hour of rain, wind gusts, fog in the morning (shorter in a short night)
	var rd: float = minf(1.0, 0.2 * sp)
	out.append({"kind": "rain", "at_h": _rng.randf_range(0.15, 0.6) * sp, "dur_h": rd})
	var wd: float = minf(0.75, 0.15 * sp)
	out.append({"kind": "wind", "at_h": _rng.randf_range(0.05, 0.8) * sp, "dur_h": wd, "wind": _rng.randf_range(45.0, 70.0)})
	var fd: float = minf(1.5, 0.25 * sp)
	out.append({"kind": "fog", "at_h": sp - fd, "dur_h": fd})
	# exactly ONE real incident: somebody sneaks to the tent, the bike or the caravan / car
	var tg := []
	for k2 in [["pir", "tent"], ["bike", "bike"], ["door", "door"]]:
		if main != null and main.obj.get(k2[0], Vector3.ZERO) != Vector3.ZERO:
			tg.append(k2[1])
	if tg.is_empty():
		tg = ["tent"]
	var seen := []                                      # what the head camera sees now: a test of the guarding, not of the setup
	if main != null and not main.cams.is_empty():
		for k3 in tg:
			var p3: Vector3 = main.obj.get({"tent": "pir", "bike": "bike", "door": "door"}[k3], Vector3.ZERO)
			if (main.cams[0] as Camera3D).is_position_in_frustum(p3 + Vector3(0, 0.8, 0)):
				seen.append(k3)
	if not seen.is_empty():
		tg = seen
	var inc := {"kind": "incident", "at_h": _rng.randf_range(0.15, 0.8) * sp, "target": tg[_rng.randi() % tg.size()]}
	out.append(inc)
	# real seconds; people / animals / cars not on top of each other (and never right at the incident)
	for e in out:
		e["at_s"] = snappedf(float(e["at_h"]) * 3600.0 / float(o["speed"]), 0.1)
		if e.has("dur_h"):
			e["dur_s"] = snappedf(float(e["dur_h"]) * 3600.0 / float(o["speed"]), 0.1)
	var actors := out.filter(func(e): return KINDS.get(e["kind"], ["weather"])[0] != "weather")
	actors.sort_custom(func(a, b): return float(a["at_s"]) < float(b["at_s"]))
	var gap: float = clampf(real_s / (actors.size() + 2.0), 12.0, 45.0)
	var prev := -1000.0
	for e in actors:
		if e["kind"] != "incident":
			if absf(float(e["at_s"]) - float(inc["at_s"])) < gap:
				e["at_s"] = float(inc["at_s"]) + gap * (1.0 if float(e["at_s"]) >= float(inc["at_s"]) else -1.0)
			if float(e["at_s"]) < prev + gap * 0.6:
				e["at_s"] = prev + gap * 0.6
			e["at_s"] = clampf(float(e["at_s"]), minf(15.0, real_s * 0.1), real_s * 0.93)   # MoveEye arms first
		prev = float(e["at_s"])
	out.sort_custom(func(a, b): return float(a["at_s"]) < float(b["at_s"]))
	for i in range(out.size()):
		out[i]["id"] = i + 1
		out[i]["at_h"] = snappedf(float(out[i]["at_s"]) * float(o["speed"]) / 3600.0, 0.001)
	return out


func _opts(d: Dictionary) -> Dictionary:
	var tempo := str(d.get("tempo", "schnell"))
	var sp: float = float(d.get("speed", TEMPO.get(tempo, 8.0)))
	return {"scene": str(d.get("scene", "")).left(40), "busy": str(d.get("busy", "normal")) if BUSY.has(str(d.get("busy", ""))) else "normal",
			"tempo": tempo if TEMPO.has(tempo) else "schnell", "speed": clampf(sp, 1.0, 240.0 if bool(d.get("free", false)) else 60.0),
			"from": fposmod(float(d.get("from", 20.0)), 24.0), "to": fposmod(float(d.get("to", 7.0)), 24.0),
			"seed": clampi(int(d.get("seed", randi() % 9000 + 1)), 1, 999999), "by": str(d.get("by", "")).left(40),
			# Bergtal-Abenteuer (bergtal_abenteuer.gd): its own plan, runs also without MoveEye («free»), up to 240× fast
			"free": bool(d.get("free", false))}


# ---- start / stop -----------------------------------------------------------------------------------------------------
func start(d: Dictionary) -> Dictionary:
	if running:
		return {"ok": false, "error": "a night test run is already running"}
	var b: String = main.busy_with("Nacht-Testlauf")
	if b != "":
		return {"ok": false, "error": main.busy_msg(b)}
	var o := _opts(d)
	saved = {"hour": main.hour(), "speed": main.speed, "weather": main.weather, "wind": main.wind, "auto": main.auto_visitors,
			"daily": main.daily_life, "lamp": main.lamp_share, "cond": main.cond.duplicate(), "scene": main.scene}
	if o["scene"] != "" and o["scene"] != main.scene:
		if not main.set_scene(o["scene"]):
			return {"ok": false, "error": "unknown scenario"}
	o["scene"] = main.scene
	opts = o
	main.auto_visitors = false                          # only the planned night: every visitor is in the truth
	main.daily_life = false
	main.clear_visitors()
	main.weather = "clear"
	main.wind = 8.0
	for k in main.cond:
		main.cond[k] = false
	speed_x = float(o["speed"])
	main.set_hour(float(o["from"]))
	main._set_speed(speed_x)
	main.set_hour(float(o["from"]))
	plan = d["plan"] if d.get("plan") is Array else make_plan(o)
	truth = []
	active = {}
	next_i = 0
	_hl_until = -1.0
	total_s = span_h(float(o["from"]), float(o["to"])) * 3600.0 / speed_x
	run_id = "%d" % int(Time.get_unix_time_from_system() * 1000.0)
	t0 = now()
	running = true
	info = T.t("Nacht-Testlauf läuft")
	main.start_info = info
	_paint()
	return {"ok": true, "run": {"id": run_id, "est_s": int(total_s), "n_plan": plan.size(), "seed": o["seed"], "from": o["from"],
			"to": o["to"], "speed": speed_x, "scene": main.scene, "busy": o["busy"], "tempo": o["tempo"]}}


func stop(finished := false) -> void:
	if not running:
		return
	running = false
	for id in active.keys():
		_end_event(int(id), true)
	main._set_speed(float(saved.get("speed", 1.0)))
	main.set_hour(float(saved.get("hour", 12.0)))
	main.weather = str(saved.get("weather", "clear"))
	main.wind = float(saved.get("wind", 8.0))
	main.auto_visitors = bool(saved.get("auto", true))
	main.daily_life = bool(saved.get("daily", true))
	main.lamp_share = float(saved.get("lamp", 0.35))
	var c: Dictionary = saved.get("cond", {})
	for k in c:
		main.cond[k] = c[k]
	main.clear_visitors()
	if main.szenen != null:
		main.szenen.restore()
	last = {"id": run_id, "truth": truth.duplicate(true), "plan": plan.duplicate(true), "stopped": not finished,
			"meta": {"seed": opts.get("seed", 1), "scene": opts.get("scene", ""), "from": opts.get("from", 20.0), "to": opts.get("to", 7.0),
					"speed": speed_x, "busy": opts.get("busy", ""), "tempo": opts.get("tempo", ""), "sim_version": main.VERSION,
					"real_s": snappedf(now() - t0, 0.1), "date": Time.get_datetime_string_from_system(false, true)}}
	_save()
	if str(saved.get("scene", "")) != "" and str(saved["scene"]) != main.scene:
		main.set_scene(str(saved["scene"]))
	info = T.t("Nacht-Testlauf fertig") if finished else T.t("Nacht-Testlauf abgebrochen")
	main.start_info = info
	_paint()


func _save() -> void:
	DirAccess.make_dir_recursive_absolute("user://nachttest")
	var f := FileAccess.open("user://nachttest/%s.json" % run_id, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(last))
	var d := DirAccess.open("user://nachttest")
	if d != null:
		var fs := Array(d.get_files())
		fs.sort()
		for i in range(fs.size() - 10):
			d.remove(fs[i])


# ---- the events ---------------------------------------------------------------------------------------------------------
func _head_pos() -> Vector3:
	return main.rig.global_position if main.rig != null else Vector3.ZERO


func _through_view(near := 4.0, far := 12.0) -> Array:
	"""a way across the picture of the head camera (like the test run), now and then a bit beside it"""
	var cam: Camera3D = main.cams[0]
	var o: Vector3 = cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	f = f.rotated(Vector3.UP, _rng.randf_range(-0.5, 0.5))
	var r := Vector3(-f.z, 0, f.x)
	var d := _rng.randf_range(near, far)
	var side := 1.0 if _rng.randf() < 0.5 else -1.0
	var half := d * 0.7 + 6.0
	var a: Vector3 = o + f * d - r * side * half
	var b: Vector3 = o + f * (d + _rng.randf_range(-2.0, 2.0)) + r * side * half
	return [Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z)]


func _ev_wc(ev: Dictionary) -> Array:
	"""somebody of the own pitch goes to the toilet block (out of the picture) and comes back - sometimes with a torch"""
	var home: Vector3 = main.obj.get("pir", Vector3.ZERO)
	if home == Vector3.ZERO:
		home = main.obj.get("door", Vector3.ZERO)
	if home == Vector3.ZERO:
		home = _head_pos() + Vector3(4.0, 0, -6.0)
	var side := 1.0 if _rng.randf() < 0.5 else -1.0
	var wc := Vector3(home.x + side * 38.0, 0, home.z + _rng.randf_range(-8.0, 8.0))
	var keep: float = main.lamp_share
	main.lamp_share = 1.0 if bool(ev.get("torch", false)) else 0.0
	var start: Vector3 = main.free_spot(home + Vector3(side * 1.2, 0, 1.0), 0.4, true)
	var v = main.spawn("person", start, wc)
	main.lamp_share = keep
	v.next_idle = main.now() + 999.0
	v.route = [[wc, clampf(120.0 / speed_x, 6.0, 120.0), 0.0], start]
	return [v]


func _ev_animal(ev: Dictionary) -> Array:
	var rt := _through_view(3.0 if ev["kind"] == "hedgehog" else 4.0, 9.0 if ev["kind"] == "hedgehog" else 13.0)
	var v = main.spawn(str(ev["kind"]), rt[0], rt[1])
	if ev["kind"] == "fox" and _rng.randf() < 0.5:                 # a fox noses about on its way
		var mid: Vector3 = rt[0].lerp(rt[1], 0.5)
		v.route = [[mid, _rng.randf_range(4.0, 10.0), 0.0], rt[1]]
		v.target = mid
	return [v]


func _ev_car(_ev: Dictionary) -> Array:
	var n0: int = main.visitors.get_child_count()
	main.car()
	_hl_until = now() + 25.0                                         # the headlights sweep over the place while it passes
	main.cond["headlights"] = true
	return [main.visitors.get_child(main.visitors.get_child_count() - 1)] if main.visitors.get_child_count() > n0 else []


func _ev_incident(ev: Dictionary) -> Array:
	"""the one real incident: comes from far, from cover to cover, crouching, the last metres crawling, at the target a
	while, then away (like events.gd sneaker - here with the target of the plan and the actor back for the truth)"""
	var key: String = {"tent": "pir", "bike": "bike", "door": "door"}.get(str(ev.get("target", "tent")), "pir")
	var goal: Vector3 = main.obj.get(key, Vector3.ZERO)
	if goal == Vector3.ZERO:
		goal = _head_pos() + Vector3(3.0, 0, -7.0)
	var side := 1.0 if _rng.randf() < 0.5 else -1.0
	# from beyond the target, seen from the device (the head camera can see the last part of the way - like a thief who
	# comes from the dark side of the place); off to one side so it is not a straight line at the camera
	var away: Vector3 = goal - _head_pos()
	away.y = 0.0
	away = away.normalized() if away.length() > 0.5 else Vector3(0, 0, -1)
	var lat := Vector3(-away.z, 0, away.x)
	var start: Vector3 = goal + away * _rng.randf_range(18.0, 26.0) + lat * side * _rng.randf_range(6.0, 12.0)
	var v = main.spawn("burglar", start, start.lerp(goal, 0.35))
	v.speed = 1.0
	v.set_meta("sneak", true)
	if main.is_dark() and _rng.randf() < 0.5:
		v.add_torch()
	var r := []
	for f in [0.55, 0.75]:
		var p: Vector3 = main.free_spot(start.lerp(goal, f) + Vector3(_rng.randf_range(-2, 2), 0, _rng.randf_range(-2, 2)), 0.6, true)
		r.append([p, _rng.randf_range(3.0, 8.0), 0.8, main.head.global_position])
	r.append([main.free_spot(start.lerp(goal, 0.9), 0.6, true), _rng.randf_range(2.0, 5.0), 2.0, goal])
	r.append([main.free_spot(goal + Vector3(0.7, 0, 0.6), 0.5, true), _rng.randf_range(6.0, 12.0), 1.0, goal])
	r.append(goal + away * 24.0 - lat * side * 14.0)
	v.route = r
	return [v]


func _begin(ev: Dictionary) -> void:
	var k: String = ev["kind"]
	var kc: Array = KINDS.get(k, ["animal", k])
	var t := elapsed()
	var rec := {"id": int(ev["id"]), "kind": k, "cat": kc[0], "cause": kc[1] + ("_torch" if k == "wc" and bool(ev.get("torch", false)) else ""),
			"t0": snappedf(t, 0.1), "t1": -1.0, "h0": snappedf(main.hour(), 0.001), "h1": -1.0, "pos": [], "near_m": -1.0,
			"vis_s": 0.0, "th_s": 0.0, "first_vis": -1.0, "vis_iv": [], "path": [], "torch": bool(ev.get("torch", false)), "target": str(ev.get("target", ""))}
	var ent := {"rec": rec, "actors": [], "until": -1.0, "cap": t + maxf(240.0, 3600.0 / speed_x)}
	if kc[0] == "weather":
		ent["until"] = t + float(ev.get("dur_s", 60.0))
		if k == "rain":
			main.weather = "rain"
		elif k == "fog":
			main.weather = "fog"
		elif k == "wind":
			main.wind = float(ev.get("wind", 55.0))
	else:
		seed(int(opts.get("seed", 1)) * 1000 + int(ev["id"]))          # the look of the visitors: same seed, same night
		var f: Callable = HANDLERS.get(k, _ev_animal)
		var acts = f.call(ev)
		randomize()
		ent["actors"] = acts if typeof(acts) == TYPE_ARRAY else []
		if not ent["actors"].is_empty() and is_instance_valid(ent["actors"][0]):
			var p: Vector3 = ent["actors"][0].position
			rec["pos"] = [snappedf(p.x, 0.1), snappedf(p.z, 0.1)]
	truth.append(rec)
	active[int(ev["id"])] = ent


func _end_event(id: int, forced := false) -> void:
	var ent: Dictionary = active.get(id, {})
	if ent.is_empty():
		return
	var rec: Dictionary = ent["rec"]
	rec["t1"] = snappedf(elapsed() if running else maxf(float(rec["t0"]), now() - t0), 0.1)
	rec["h1"] = snappedf(main.hour(), 0.001)
	rec["vis_s"] = snappedf(float(rec["vis_s"]), 0.1)
	rec["th_s"] = snappedf(float(rec["th_s"]), 0.1)
	if forced:
		rec["cut"] = true
	if rec["kind"] == "rain" or rec["kind"] == "fog":
		var other_fog := false
		for k in active:
			if int(k) != id and str(active[k]["rec"]["kind"]) in ["rain", "fog"]:
				other_fog = true
		if not other_fog:
			main.weather = "clear"
	elif rec["kind"] == "wind":
		main.wind = 8.0
	for a in ent["actors"]:
		if is_instance_valid(a) and forced:
			a.queue_free()
	active.erase(id)


func _process(dt: float) -> void:
	if not running:
		return
	var t := elapsed()
	if main.now() - main.mw_t > 60.0 and not bool(opts.get("free", false)):
		info = T.t("MoveEye hat die Verbindung verloren – Nacht-Testlauf abgebrochen.")
		stop(false)
		return
	while next_i < plan.size() and t >= float(plan[next_i]["at_s"]):
		_begin(plan[next_i])
		next_i += 1
	if _hl_until > 0.0 and now() > _hl_until:
		_hl_until = -1.0
		main.cond["headlights"] = false
	_sample_t -= dt
	if _sample_t <= 0.0:
		_sample_t = SAMPLE
		_sample(t)
	for id in active.keys():
		var ent: Dictionary = active[id]
		if float(ent["until"]) > 0.0:
			if t >= float(ent["until"]) or t >= total_s:
				_end_event(int(id))
			continue
		var alive := false
		for a in ent["actors"]:
			if is_instance_valid(a) and not a.is_queued_for_deletion() and not a.done:
				alive = true
		if not alive:
			_end_event(int(id))
		elif t > float(ent["cap"]):
			_end_event(int(id), true)
	if t >= total_s and next_i >= plan.size():
		var people := false
		for id in active:
			if float(active[id]["until"]) < 0.0:
				people = true
		if not people or t > total_s + 120.0:
			stop(true)
			return
	if Engine.get_process_frames() % 30 == 0:
		_paint()


func _sample(t: float) -> void:
	var hp := _head_pos()
	for id in active:
		var ent: Dictionary = active[id]
		var rec: Dictionary = ent["rec"]
		for a in ent["actors"]:
			if not is_instance_valid(a) or a.is_queued_for_deletion():
				continue
			var cam_v: bool = main.testrun.visible(a)
			var th_v: bool = (not cam_v) and main.testrun.thermal_visible(a)
			if cam_v or th_v:
				if float(rec["first_vis"]) < 0.0:
					rec["first_vis"] = snappedf(t, 0.1)
				rec["vis_s"] = float(rec["vis_s"]) + SAMPLE
				var iv: Array = rec["vis_iv"]                  # when it was visible: [[from, to], …] (MoveEye matches alarms with it)
				if not iv.is_empty() and t - float(iv[-1][1]) <= 1.0:
					iv[-1][1] = snappedf(t, 0.1)
				elif iv.size() < 40:
					iv.append([snappedf(t, 0.1), snappedf(t, 0.1)])
				if th_v:
					rec["th_s"] = float(rec["th_s"]) + SAMPLE
			var p: Vector3 = a.position
			var dd := Vector2(p.x - hp.x, p.z - hp.z).length()
			if float(rec["near_m"]) < 0.0 or dd < float(rec["near_m"]):
				rec["near_m"] = snappedf(dd, 0.1)
			var path: Array = rec["path"]
			if path.size() < 60 and (path.is_empty() or t - float(path[-1][0]) >= 3.0):
				path.append([snappedf(t, 0.1), snappedf(p.x, 0.1), snappedf(p.z, 0.1)])


# ---- for MoveEye ----------------------------------------------------------------------------------------------------
func state() -> Dictionary:
	var act := []
	for id in active:
		var r: Dictionary = active[id]["rec"]
		act.append({"id": r["id"], "kind": r["kind"], "cat": r["cat"], "vis": float(r["first_vis"]) >= 0.0})
	return {"ok": true, "running": running, "id": run_id, "t": snappedf(elapsed(), 0.1), "hour": snappedf(main.hour(), 0.001),
			"total_s": int(total_s), "left_s": int(maxf(0.0, total_s - elapsed())) if running else 0, "n_plan": plan.size(),
			"n_done": next_i, "active": act, "opts": opts, "info": info, "done_id": str(last.get("id", ""))}


func control(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "state"))
	if op == "start":
		return start(d)
	if op == "stop":
		stop(false)
		return state()
	if op == "truth":
		if str(d.get("id", "")) != "" and str(d.get("id", "")) != str(last.get("id", "")):
			var f := "user://nachttest/%s.json" % str(d["id"]).validate_filename()
			var o = JSON.parse_string(FileAccess.get_file_as_string(f)) if FileAccess.file_exists(f) else null
			return {"ok": typeof(o) == TYPE_DICTIONARY, "run": o if typeof(o) == TYPE_DICTIONARY else {}}
		return {"ok": not last.is_empty(), "run": last}
	if op == "info":
		return {"ok": true, "busy": BUSY.keys(), "tempo": TEMPO, "kinds": KINDS, "scene": main.scene}
	if op == "plan":                                       # for tests: the plan of a seed without starting
		var o2 := _opts(d)
		return {"ok": true, "plan": make_plan(o2)}
	return state()


# ---- the window: card «Testen» → «Erkennung messen» ---------------------------------------------------------------
func add_info(body, UI) -> void:
	label = UI.small("", UI.TXT)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", 13)
	body.add_child(label)
	stop_btn = Button.new()
	stop_btn.text = T.t("⏹ Nacht-Testlauf abbrechen")
	stop_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stop_btn.pressed.connect(func(): stop(false))
	body.add_child(stop_btn)
	_paint()


func _paint() -> void:
	if label == null:
		return
	label.visible = running or info != ""
	stop_btn.visible = running
	if running:
		var h: float = main.hour()
		label.text = T.t("🌙 Nacht-Testlauf (von MoveEye): %02d:%02d · Ereignis %d von %d · noch etwa %d Min.") % [int(h), int(fmod(h, 1.0) * 60.0),
				next_i, plan.size(), int(ceil(maxf(0.0, total_s - elapsed()) / 60.0))]
	else:
		label.text = info


func status() -> String:
	return T.t("Nacht-Testlauf läuft") if running else ""
