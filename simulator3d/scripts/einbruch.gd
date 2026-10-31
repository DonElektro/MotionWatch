extends Node
## Einbruch-Abläufe (Paket «real-einbruch», 31.10.2026): echte Diebstahl- und Einbruch-Muster auf dem Campingplatz als
## abspielbare Abläufe mit Bewertung - wann hat MoveEye erkannt, gewarnt, Licht oder Sirene gemacht, was hat es verpasst.
##
##   kundschaft   tagsüber vorbeigehen und schauen, nachts zurückkommen, aus der Deckung beobachten, zugreifen
##   ablenkung    zu zweit: einer geht vorne zum Gerät und redet (der Kopf folgt ihm), der andere stiehlt hinten
##   velo         Velo nachts: von Deckung zu Deckung, Schloss knacken (Geräusch, Velo-Sensor), Velo wegschieben
##   rucksack     Gelegenheitsdieb: geht ganz normal vorbei, nimmt den Rucksack im Vorbeigehen, geht ruhig weiter
##   kuehlbox     Kühlbox aus der Deckung: kriecht heran, trägt sie geduckt weg
##   autos_zelte  Runde mit Taschenlampe: Blick in Auto / Wohnwagen / Zelt, Türgriff probieren, nichts gefunden - weg
##   warten       sehr geduldig: lange in der Deckung beobachten, näher, nochmals warten, dann zugreifen
##
## Jeder Ablauf ist ein Zufall mit Seed (gleicher Seed + gleiche Szene = gleicher Ablauf), sucht sich in jeder Szene Ziel,
## Deckung (von der Kopfkamera aus verdeckt) und Wege selbst (main.obj, main.obstacles, Kamera-Blickfeld). Nachts meiden
## die Diebe das Licht: geht das weisse Licht von MoveEye an, erstarren sie, ziehen sich in die Deckung zurück, warten und
## versuchen es nochmals; beim zweiten Mal oder bei der Sirene: Flucht (mit der Beute, wenn sie sie schon haben).
##
## Bewertung (Wahrheit wie Testlauf / Prüfstand: testrun.visible / thermal_visible / present): pro Abschnitt
## (Auskundschaften, Beobachten, Annähern, Griff, Flucht …) wie lange sichtbar, ob MoveEye erkannt hat (det.persons),
## Pushes (det.pushes, Teil 068), Vorwarnung, Licht, Sirene. Hauptfrage: Push VOR dem Griff? Note 1–6 (6 = beste).
## Bericht im Fenster (Testen → Einbruch-Abläufe), in der Statuszeile (auch auf der Simulator-Seite von MoveEye), als
## JSON / HTML in user://einbruch/ und über {"action": "einbruch", "do": "result"}.
##
## Control API: {"action": "einbruch", "do": info | start (ablauf, seed, zeit) | serie (seed, zeit, liste) | stop |
##               state | result}
## Nacht-Testlauf (Zweig «nachttest», scripts/nachtlauf.gd, Knoten main.nacht): ist er da, spielt sein «echter Vorfall» einen Nacht-Ablauf
## von hier (register_kind("incident", …)) - ohne Zeitsprung, ohne eigene Sperre; die Wahrheit schreibt nachtlauf.gd.

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")

var main

# id -> [Name, kurze Beschreibung, Uhrzeit (Tag), Uhrzeit (Nacht) - -1 = nicht gebraucht]
const ABL := {
	"kundschaft": ["Auskundschaften und nachts zurück", "tagsüber vorbeigehen und schauen, nachts zurück, beobachten, zugreifen", 15.5, 23.8],
	"ablenkung": ["Ablenkung zu zweit", "einer redet vorne am Gerät, der andere stiehlt hinten", 20.6, -1.0],
	"velo": ["Velo-Diebstahl in der Nacht", "Deckung, Schloss knacken, Velo wegschieben", -1.0, 0.8],
	"rucksack": ["Rucksack im Vorbeigehen", "geht normal vorbei, nimmt den Rucksack, geht ruhig weiter", 17.5, -1.0],
	"kuehlbox": ["Kühlbox aus der Deckung", "kriecht heran, trägt die Kühlbox geduckt weg", -1.0, 1.6],
	"autos_zelte": ["Blick in Autos und Zelte", "Runde mit Taschenlampe, Türgriff probieren, nichts gefunden", -1.0, 23.2],
	"warten": ["Lange beobachten, dann zugreifen", "minutenlang in der Deckung, näher, nochmals warten, Griff", -1.0, 2.4],
}
const ORDER := ["kundschaft", "ablenkung", "velo", "rucksack", "kuehlbox", "autos_zelte", "warten"]
# the names of the parts of a run (the report shows them in this order)
const SEC := {"kundschaft": "Auskundschaften", "beobachten": "Beobachten", "ablenken": "Ablenken", "annaehern": "Annähern",
		"pruefen": "Autos / Zelte prüfen", "griff": "Griff", "flucht": "Weg / Flucht"}
const SEC_ORDER := ["kundschaft", "beobachten", "ablenken", "annaehern", "pruefen", "griff", "flucht"]
const ALARM_EVS := ["person", "prealarm", "warm"]   # «tamper» is counted apart (_sample)
const HOLD := 99999.0                 # a standing actor waits «for ever» - the next step comes from here (never deletes itself)
const SETTLE := 12.0                  # after a jump of the clock: MoveEye and the exposure adapt
const GRACE := 2.5                    # a detection counts for an actor up to … s after it was last visible

var running := false
var embedded := false                 # played by the night test run (no clock, no lock, no own report)
var ablauf := ""
var seed_n := 0                       # 0 = a new one every time
var use_time := true                  # the hour of the run (else: the time it is now)
var series: Array = []                # «alle nacheinander»: the ids still to come
var series_res: Array = []
var series_seed := 0
var acts: Array = []                  # [{hour, settle, roles: [role]}]
var act_i := -1
var act_t0 := 0.0
var roles: Array = []                 # the roles of the current act
var flags := {}                       # synchronisation between two roles («ablenker angekommen»)
var props: Array = []                 # nodes put into the scene for the run (backpack, cool box)
var hidden: Array = []                # nodes hidden while a thief carries their copy (the bike)
var secs := {}                        # section key -> record
var events: Array = []                # [{t, what, sec}] - what MoveEye did and what happened
var t0 := 0.0
var saved := {}
var rep := {}                         # the last report
var info := ""
var last_html := ""
var label: Label
var _rng := RandomNumberGenerator.new()
var _sample_t := 0.0
var _push_seen := {}
var _push_known := false
var _prev_light := false
var _prev_sound := false
var _prev_pre := false
var _grab_t := -1.0
var _cur_sec := ""
var _pic_last := -100.0               # the last time somebody of the run was in the picture (a push then is about them)


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func _ready() -> void:
	call_deferred("_plug_night")


func _plug_night() -> void:
	"""the night test run (nachtlauf.gd, branch «nachttest»): its one real incident becomes one of our night runs"""
	var nl = null
	for nm in ["nacht", "nachtlauf"]:                    # branch «nachttest»: main.nacht
		if nl == null and main != null and main.get(nm) != null:
			nl = main.get(nm)
	if nl != null and is_instance_valid(nl) and nl.has_method("register_kind"):
		nl.register_kind("incident", _night_incident)
		print("einbruch: Nacht-Testlauf - Vorfall «incident» eingesteckt")


# ---- places ----------------------------------------------------------------------------------------------------------
func _hp() -> Vector3:
	return main.head.global_position if main.head != null and main.head.is_inside_tree() else Vector3(0, 1.6, 0)


func _flat(p: Vector3) -> Vector3:
	return Vector3(p.x, 0, p.z)


func _in_view(p: Vector3, h := 0.8) -> bool:
	return main.cams.size() > 0 and (main.cams[0] as Camera3D).is_position_in_frustum(p + Vector3(0, h, 0))


func _view_point(dist: float, off_deg := 0.0) -> Vector3:
	var hp := _hp()
	var f := Vector3(0, 0, -1)
	if main.cams.size() > 0:
		f = -(main.cams[0] as Camera3D).global_transform.basis.z
	f.y = 0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	return _flat(hp) + f.rotated(Vector3.UP, deg_to_rad(off_deg)) * dist


func _target(kind: String) -> Vector3:
	"""where the thing to steal (or to look at) is: the scene's bike / tent / door - one the head camera sees, else in view"""
	var key: String = {"velo": "bike", "zelt": "pir", "tuer": "door"}.get(kind, "")
	if key != "":
		var p: Vector3 = main.obj.get(key, Vector3.ZERO)
		if p != Vector3.ZERO:
			return p
	return main.free_spot(_view_point(_rng.randf_range(7.0, 10.0), _rng.randf_range(-12.0, 12.0)), 0.6, false)


func _place_near_tent() -> Vector3:
	"""a spot for the backpack / cool box: beside the tent if the camera sees it, else 7-10 m in front of the camera"""
	var tent: Vector3 = main.obj.get("pir", Vector3.ZERO)
	var cands := []
	if tent != Vector3.ZERO:
		for a in [0.6, 2.2, 3.6, 5.0]:
			cands.append(tent + Vector3(cos(a), 0, sin(a)) * 1.5)
	for c in cands:
		var q: Vector3 = main.free_spot(c, 0.4, false)
		if _in_view(q, 0.3) and q.distance_to(_flat(_hp())) > 4.0 and q.distance_to(_flat(_hp())) < 16.0:
			return q
	return main.free_spot(_view_point(_rng.randf_range(7.0, 10.0), _rng.randf_range(-15.0, 15.0)), 0.4, false)


func _away(goal: Vector3) -> Vector3:
	var a := _flat(goal) - _flat(_hp())
	return a.normalized() if a.length() > 0.5 else Vector3(0, 0, -1)


func _cover(near: Vector3, rmin: float, rmax: float, toward := Vector3.INF) -> Vector3:
	"""a spot the head camera cannot see (behind a tent, car, bush, tree …) rmin…rmax m from near; Vector3.INF = none.
	toward: prefer spots on that side (where the thief comes from)"""
	var cam := _hp()
	var best := Vector3.INF
	var best_s := -1e9
	for o in main.obstacles:
		var c: Vector2 = o["c"]
		var cp := Vector3(c.x, 0, c.y)
		var d := cp.distance_to(_flat(near))
		if d > rmax + 3.0 or d < maxf(0.0, rmin - 3.0):
			continue
		var size: float = float(o["r"]) if o.has("r") else (o["h"] as Vector2).length()
		if size < 0.35 or size > 8.0:
			continue
		var aw := cp - _flat(cam)
		aw = aw.normalized() if aw.length() > 0.1 else Vector3(0, 0, -1)
		for rot in [0.0, 0.5, -0.5]:
			var p: Vector3 = main.free_spot(cp + aw.rotated(Vector3.UP, rot) * (size + 0.7), 0.45, true)
			var dn := p.distance_to(_flat(near))
			if dn < rmin or dn > rmax:
				continue
			if main.line_free(cam, p + Vector3(0, 0.9, 0)):
				continue                                  # the camera sees it: no cover
			var s := -absf(dn - (rmin + rmax) * 0.5) + _rng.randf_range(0.0, 2.0)
			if toward != Vector3.INF:
				s -= 0.25 * p.distance_to(_flat(toward))
			if s > best_s:
				best_s = s
				best = p
	return best


func _dark_spot(near: Vector3, rmin: float, rmax: float, toward: Vector3) -> Vector3:
	"""no cover found: a spot out of the picture of the head camera (or at least in the dark)"""
	var a0 := _away(near)
	for i in range(16):
		var ang := _rng.randf_range(-PI, PI)
		var p: Vector3 = main.free_spot(_flat(near) + Vector3(cos(ang), 0, sin(ang)) * _rng.randf_range(rmin, rmax), 0.45, true)
		if not _in_view(p) and (toward == Vector3.INF or p.distance_to(toward) < near.distance_to(toward) + rmax):
			return p
	return main.free_spot(_flat(near) + a0 * rmax, 0.45, true)


func _hide_spot(near: Vector3, rmin: float, rmax: float, toward: Vector3) -> Vector3:
	var c := _cover(near, rmin, rmax, toward)
	return c if c != Vector3.INF else _dark_spot(near, rmin, rmax, toward)


func _start_far(goal: Vector3, side: float) -> Vector3:
	"""from beyond the target (seen from the device) and to one side - like a thief from the dark side of the place"""
	var away := _away(goal)
	var lat := Vector3(-away.z, 0, away.x)
	return main.free_spot(_flat(goal) + away * _rng.randf_range(16.0, 24.0) + lat * side * _rng.randf_range(8.0, 14.0), 0.5, true)


func _exit_far(goal: Vector3, side: float) -> Vector3:
	var away := _away(goal)
	var lat := Vector3(-away.z, 0, away.x)
	return _flat(goal) + away * _rng.randf_range(20.0, 28.0) + lat * side * _rng.randf_range(18.0, 26.0)


# ---- the runs: acts and roles ----------------------------------------------------------------------------------------
func _role(kind: String, from: Vector3, steps: Array, opts := {}) -> Dictionary:
	var r := {"kind": kind, "from": from, "steps": steps, "i": -1, "v": null, "t_step": 0.0, "until": 0.0, "lit_n": 0,
			"state": "", "back_i": -1, "loot": null, "fled": false, "gone": false, "torch": bool(opts.get("torch", false)),
			"shy": bool(opts.get("shy", false)), "spd": float(opts.get("spd", 1.2)), "name": str(opts.get("name", "Dieb")),
			"pack": bool(opts.get("pack", false))}
	return r


func _go(p: Vector3, c := 0.0, sec := "", spd := -1.0, look = null) -> Dictionary:
	return {"do": "go", "p": p, "c": c, "sec": sec, "spd": spd, "look": look}


func _wait(s: float, c := 0.0, look = null, sec := "") -> Dictionary:
	return {"do": "wait", "s": s, "c": c, "look": look, "sec": sec}


func _build(id: String, night_only := false) -> Array:
	"""the acts of one run (positions are chosen now, from the seed)"""
	var out := []
	var side := 1.0 if _rng.randf() < 0.5 else -1.0
	var hp := _hp()
	var day_h: float = ABL[id][2]
	var night_h: float = ABL[id][3]
	match id:
		"kundschaft":
			var what: String = ["velo", "rucksack", "kuehlbox"][_rng.randi() % 3]
			var goal := _loot_place(what)
			if not night_only:
				var away := _away(goal)
				var lat := Vector3(-away.z, 0, away.x)
				var line := _flat(goal) + away * _rng.randf_range(3.0, 6.0)
				var a: Vector3 = main.free_spot(line - lat * side * 26.0, 0.5, true)
				var stop: Vector3 = main.free_spot(line + lat * side * _rng.randf_range(-1.5, 1.5), 0.5, true)
				var b := line + lat * side * 30.0
				var s1 := [_go(stop, 0.0, "kundschaft"), _wait(_rng.randf_range(5.0, 9.0), 0.0, goal, "kundschaft"),
						_wait(_rng.randf_range(1.5, 3.0), 0.0, hp, "kundschaft"), {"do": "leave", "p": b, "sec": "kundschaft"}]
				out.append({"hour": day_h, "roles": [_role("person", a, s1, {"name": "Spaziergänger", "spd": 1.2})]})
			out.append({"hour": night_h, "settle": SETTLE, "roles": [_thief_role(what, goal, side, _rng.randf_range(15.0, 35.0), true)]})
		"ablenkung":
			var what2: String = ["rucksack", "kuehlbox", "velo"][_rng.randi() % 3]
			var goal2 := _loot_place(what2)
			var front: Vector3 = main.free_spot(_view_point(_rng.randf_range(2.6, 3.6), _rng.randf_range(-10.0, 10.0)), 0.5, true)
			var away2 := _away(front)
			var lat2 := Vector3(-away2.z, 0, away2.x)
			var fa: Vector3 = main.free_spot(_flat(front) + away2 * 18.0 + lat2 * side * 16.0, 0.5, true)
			var talk := _rng.randf_range(35.0, 55.0)
			var s_a := [_go(front, 0.0, "ablenken", 1.25), {"do": "signal", "key": "vorne", "sec": "ablenken"},
					{"do": "talk", "s": talk, "look": hp, "sec": "ablenken"},
					{"do": "leave", "p": _flat(front) + away2 * 20.0 - lat2 * side * 30.0, "sec": "", "spd": 1.4}]
			var ra := _role("person", fa, s_a, {"name": "Ablenker", "spd": 1.25})
			var rb := _thief_role(what2, goal2, -side, 0.0, false)
			rb["steps"].push_front({"do": "sync", "key": "vorne", "sec": "beobachten", "extra": _rng.randf_range(3.0, 8.0)})
			rb["name"] = "Dieb (hinten)"
			out.append({"hour": day_h, "roles": [ra, rb]})
		"velo":
			out.append({"hour": night_h, "roles": [_thief_role("velo", _loot_place("velo"), side, _rng.randf_range(6.0, 14.0), true)]})
		"rucksack":
			var goal3 := _loot_place("rucksack")
			var away3 := _away(goal3)
			var lat3 := Vector3(-away3.z, 0, away3.x)
			var a3: Vector3 = main.free_spot(_flat(goal3) + away3 * 1.2 - lat3 * side * 26.0, 0.5, true)
			var grab: Vector3 = main.free_spot(goal3 + away3 * 0.6, 0.35, true)
			var b3 := _flat(goal3) + away3 * 2.0 + lat3 * side * 30.0
			var s3 := [_go(main.free_spot(grab - lat3 * side * 6.0, 0.4, true), 0.0, "annaehern"), _go(grab, 0.0, "annaehern", 1.0),
					{"do": "grab", "s": _rng.randf_range(1.4, 2.6), "c": 0.7, "look": goal3, "what": "rucksack", "sec": "griff"},
					{"do": "leave", "p": b3, "sec": "flucht", "spd": 1.3}]
			out.append({"hour": day_h, "roles": [_role("person", a3, s3, {"name": "Gelegenheitsdieb", "spd": 1.3})]})
		"kuehlbox":
			out.append({"hour": night_h, "roles": [_thief_role("kuehlbox", _loot_place("kuehlbox"), side, _rng.randf_range(8.0, 16.0), true)]})
		"autos_zelte":
			var spots := _look_spots()
			var st0 := _start_far(spots[0], side)
			var s4 := []
			for i in range(spots.size()):
				var sp: Vector3 = spots[i]
				var at: Vector3 = main.free_spot(sp + (_flat(st0) - _flat(sp)).normalized() * 1.4, 0.45, true)
				s4.append(_go(at, 0.0 if i == 0 else 0.3, "annaehern" if i == 0 else "pruefen", 1.0))
				s4.append(_wait(_rng.randf_range(4.0, 8.0), 0.6, sp + Vector3(0, 1.0, 0), "pruefen"))   # crouched: the torch shines in
				if i == 0 or _rng.randf() < 0.4:
					s4.append({"do": "handle", "s": _rng.randf_range(2.0, 3.5), "look": sp, "sec": "pruefen"})
			s4.append({"do": "leave", "p": _exit_far(spots[spots.size() - 1], -side), "sec": "flucht", "spd": 1.3})
			out.append({"hour": night_h, "roles": [_role("burglar", st0, s4, {"name": "Dieb mit Lampe", "torch": true, "shy": true, "spd": 1.1})]})
		"warten":
			var what5: String = ["velo", "rucksack", "kuehlbox"][_rng.randi() % 3]
			var goal5 := _loot_place(what5)
			var r5 := _thief_role(what5, goal5, side, _rng.randf_range(60.0, 110.0), true)
			# a second, closer cover and a second wait before the approach
			var c2 := _hide_spot(goal5, 5.0, 8.0, r5["from"])
			var k := 0
			for j in range(r5["steps"].size()):
				if str(r5["steps"][j].get("sec", "")) == "annaehern":
					k = j
					break
			r5["steps"].insert(k, _wait(_rng.randf_range(20.0, 40.0), 1.0, goal5, "beobachten"))
			r5["steps"].insert(k, _go(c2, 1.0, "beobachten", 0.8))
			r5["name"] = "geduldiger Dieb"
			out.append({"hour": night_h, "roles": [r5]})
	return out


func _thief_role(what: String, goal: Vector3, side: float, watch_s: float, night: bool) -> Dictionary:
	"""a night thief: far start, (cover: watch), from cover to cover crouching, the last metres crawling, grab, away"""
	var st := _start_far(goal, side)
	var steps := []
	var cov := _hide_spot(goal, 9.0, 15.0, st)
	if watch_s > 0.0:
		steps.append(_go(cov, 0.0, "annaehern" if not night else "beobachten", 1.1))
		steps.append(_wait(watch_s, 1.0, goal, "beobachten"))
	var near := _hide_spot(goal, 3.5, 6.5, cov)
	steps.append(_go(near, 1.0, "annaehern", 0.9))
	steps.append(_wait(_rng.randf_range(3.0, 7.0), 1.0, _hp(), "annaehern"))     # looks at the camera
	var grab: Vector3 = main.free_spot(goal + (_flat(near) - _flat(goal)).normalized() * 0.75, 0.4, true)
	steps.append(_go(grab, 2.0 if what != "velo" and _rng.randf() < 0.6 else 1.0, "annaehern", 0.8))
	var gs := _rng.randf_range(8.0, 18.0) if what == "velo" else _rng.randf_range(2.5, 5.0)
	steps.append({"do": "grab", "s": gs, "c": 1.0, "look": goal, "what": what, "sec": "griff"})
	steps.append(_go(_hide_spot(goal, 6.0, 12.0, st), 0.7 if what != "velo" else 0.0, "flucht", 1.0 if what == "velo" else 0.9))
	steps.append({"do": "leave", "p": _exit_far(goal, side), "sec": "flucht", "spd": 1.5 if what == "velo" else 1.2})
	return _role("burglar" if night else "person", st, steps, {"name": "Dieb", "torch": night and _rng.randf() < 0.5, "shy": night, "spd": 1.1})


func _loot_place(what: String) -> Vector3:
	if what == "velo":
		return _target("velo")
	return _ensure_prop(what)


func _look_spots() -> Array:
	"""what a thief looks into at night: the caravan door, the tent, big things (cars, caravans) near the place"""
	var out := []
	for k in ["door", "pir"]:
		var p: Vector3 = main.obj.get(k, Vector3.ZERO)
		if p != Vector3.ZERO and p.distance_to(_flat(_hp())) < 30.0:
			out.append(_flat(p))
	var big := []
	for o in main.obstacles:
		if not o.has("h"):
			continue
		var c: Vector2 = o["c"]
		var p2 := Vector3(c.x, 0, c.y)
		var ext: float = (o["h"] as Vector2).length()
		if ext > 1.6 and ext < 5.0 and p2.distance_to(_flat(_hp())) > 5.0 and p2.distance_to(_flat(_hp())) < 25.0:
			var dup := false
			for q in out:
				if (q as Vector3).distance_to(p2) < 4.0:
					dup = true
			if not dup:
				big.append(p2)
	big.shuffle()                                      # global randomness is seeded in start() - the same seed, the same order
	for b in big:
		if out.size() >= 4:
			break
		out.append(b)
	if out.is_empty():
		out.append(_view_point(9.0, -10.0))
		out.append(_view_point(11.0, 14.0))
	return out


# ---- things to steal --------------------------------------------------------------------------------------------------
func _ensure_prop(what: String) -> Vector3:
	for pr in props:
		if is_instance_valid(pr) and str(pr.get_meta("einbruch", "")) == what:
			return _flat(pr.global_position)
	var p := _place_near_tent()
	var n := Node3D.new()
	n.set_meta("einbruch", what)
	main.scenes.root.add_child(n)
	n.global_position = Vector3(p.x, main.ground_y(p.x, p.z), p.z)
	n.rotation.y = _rng.randf_range(0.0, TAU)
	var amb: float = float(main.ambient)
	if what == "rucksack":
		var col: Color = [Color(0.55, 0.12, 0.1), Color(0.1, 0.25, 0.5), Color(0.2, 0.35, 0.2)][_rng.randi() % 3]
		var bm := BoxMesh.new()
		bm.size = Vector3(0.34, 0.48, 0.22)
		main.add_mesh(n, bm, Vector3(0, 0.24, 0), main.mat(col), amb)
		var tm := BoxMesh.new()
		tm.size = Vector3(0.3, 0.14, 0.08)
		main.add_mesh(n, tm, Vector3(0, 0.16, 0.14), main.mat(col.darkened(0.3)), amb)
	else:
		var bx := BoxMesh.new()
		bx.size = Vector3(0.56, 0.36, 0.36)
		main.add_mesh(n, bx, Vector3(0, 0.18, 0), main.mat(Color(0.12, 0.35, 0.7)), amb)
		var lid := BoxMesh.new()
		lid.size = Vector3(0.58, 0.06, 0.38)
		main.add_mesh(n, lid, Vector3(0, 0.39, 0), main.mat(Color(0.92, 0.93, 0.95)), amb)
	props.append(n)
	return p


func _take(r: Dictionary, what: String) -> void:
	"""the grab: the thing goes with the thief (the original is hidden until the end of the run)"""
	var v = r["v"]
	var src: Node3D = null
	if what == "velo":
		src = main.bike_node
		main.add_event("Velo", "tag")                   # the bike tag sensor (like the scene «Velodieb»)
	else:
		for pr in props:
			if is_instance_valid(pr) and str(pr.get_meta("einbruch", "")) == what:
				src = pr
	if src == null or not is_instance_valid(src) or not src.visible:
		return
	if what == "rucksack" and v.has_method("add_backpack"):
		v.add_backpack(Color(0.3, 0.1, 0.08))            # puts it on
	else:
		var cp: Node3D = src.duplicate()
		v.add_child(cp)
		if what == "velo":
			cp.transform = Transform3D(Basis.IDENTITY, Vector3(0.5, 0.05, 0.0))
		else:
			cp.transform = Transform3D(Basis.IDENTITY, Vector3(0, 0.62, -0.38))
			v.carry = true
	src.visible = false
	hidden.append(src)
	r["loot"] = what


# ---- start / stop -----------------------------------------------------------------------------------------------------
func ablauf_name(id: String) -> String:
	return T.t(str(ABL[id][0])) if ABL.has(id) else id


func start(id: String, sd := -1, zeit = null) -> String:
	if running:
		return T.t("Es läuft schon ein Einbruch-Ablauf.")
	if sd >= 0:
		seed_n = sd
	var s_used: int = seed_n if seed_n > 0 else randi_range(1, 9999)
	if id == "zufall" or id == "":
		id = ORDER[(s_used * 7 + 3) % ORDER.size()]      # the same seed: the same run
	if not ABL.has(id):
		return T.t("Unbekannter Ablauf.")
	var b: String = main.busy_with()
	if b != "" and series.is_empty():
		info = main.busy_msg(b)
		paint()
		return info
	if zeit != null:
		use_time = bool(zeit)
	if series.is_empty():
		saved = {"hour": main.hour(), "speed": main.speed, "auto": main.auto_visitors}
	main.auto_visitors = false
	main.clear_visitors()
	main._set_speed(1.0)
	_reset_run()
	ablauf = id
	_rng.seed = s_used * 7919 + ORDER.find(id) * 31 + 7
	seed(s_used * 104729 + ORDER.find(id))              # the look of the visitors and the shuffles: same seed, same run
	acts = _build(id)
	randomize()
	rep = {"ablauf": id, "name": ablauf_name(id), "seed": s_used, "scene": str(main.scene), "date": Time.get_datetime_string_from_system(false, true)}
	running = true
	t0 = now()
	_known_pushes()
	_next_act()
	info = T.t("Einbruch-Ablauf läuft: %s (Zufall %d)", [ablauf_name(id), s_used])
	main.start_info = info
	paint()
	print("einbruch: start %s seed %d scene %s" % [id, s_used, main.scene])
	return ""


func start_series(sd := -1, zeit = null, liste: Array = []) -> String:
	if running:
		return T.t("Es läuft schon ein Einbruch-Ablauf.")
	var b: String = main.busy_with()
	if b != "":
		info = main.busy_msg(b)
		paint()
		return info
	series = []
	for x in (liste if not liste.is_empty() else ORDER):
		if ABL.has(str(x)):
			series.append(str(x))
	if series.is_empty():
		return T.t("Unbekannter Ablauf.")
	series_res = []
	series_seed = sd if sd >= 0 else seed_n
	saved = {"hour": main.hour(), "speed": main.speed, "auto": main.auto_visitors}
	var first: String = series.pop_front()
	series.push_front("")                               # a marker: «a series is running» while the first one runs
	var r := start(first, series_seed, zeit)
	series.pop_front()
	if r != "":
		series = []
	elif series.is_empty():
		series = ["-"]                                   # a series of one: still report as a series
	return r


func _reset_run() -> void:
	for n in props:
		if is_instance_valid(n):
			n.queue_free()
	props.clear()
	for n in hidden:
		if is_instance_valid(n):
			n.visible = true
	hidden.clear()
	acts = []
	act_i = -1
	roles = []
	flags = {}
	secs = {}
	events = []
	_grab_t = -1.0
	_pic_last = -100.0
	_cur_sec = ""
	_prev_light = bool(main.mw.get("lights", {}).get("white", false))
	_prev_sound = str(main.mw.get("sound", "")) != ""
	_prev_pre = false


func _known_pushes() -> void:
	_push_seen.clear()
	var pl = main.mw_det.get("pushes", null)
	_push_known = typeof(pl) == TYPE_ARRAY
	if _push_known:
		for x in pl:
			_push_seen[str(x[0])] = true


func stop(finished := false) -> void:
	if not running:
		return
	running = false
	for r in roles:
		var v = r["v"]
		if v != null and is_instance_valid(v) and not embedded:
			v.queue_free()
	if not embedded:
		_make_report(finished)
	var nxt := ""
	while not series.is_empty() and nxt == "":
		var x: String = series.pop_front()
		if x != "-":
			nxt = x
	_reset_run()
	if finished and nxt != "":
		series.push_front("")
		start(nxt, series_seed)
		series.pop_front()
		if not running:
			series = []
		return
	if not embedded:
		if not series_res.is_empty() and (finished or nxt == ""):
			_series_report()
		series = []
		main.auto_visitors = bool(saved.get("auto", main.auto_visitors))
		main._set_speed(float(saved.get("speed", 1.0)))
		if use_time and saved.has("hour"):
			main.set_hour(float(saved["hour"]))
	embedded = false
	paint()


# ---- the run, frame by frame ------------------------------------------------------------------------------------------
func _next_act() -> void:
	act_i += 1
	if act_i >= acts.size():
		stop(true)
		return
	var a: Dictionary = acts[act_i]
	if use_time and not embedded and float(a.get("hour", -1.0)) >= 0.0:
		main.set_hour(float(a["hour"]))
		if ABL.has(ablauf) and is_equal_approx(float(a["hour"]), float(ABL[ablauf][2])):
			# a day act in autumn / winter: 17:30 or 20:36 is already dark - earlier until it is real daylight (the sun
			# of the scene's date and place, main.sun_el); the night acts stay as they are
			var h := float(a["hour"])
			while main.light_level() < 0.5 and h > 11.5:
				h -= 0.5
				main.set_hour(h)
			a["hour"] = h
		_note(T.t("Uhr: %s", ["%02d:%02d" % [int(a["hour"]), int(fmod(float(a["hour"]), 1.0) * 60.0)]]))
	act_t0 = now() + (float(a.get("settle", 0.0)) if act_i > 0 and not embedded else 0.0)
	roles = a["roles"]


func _spawn(r: Dictionary) -> void:
	var first: Vector3 = r["from"]
	for s in r["steps"]:
		if s.has("p"):
			first = s["p"]
			break
	seed(int(rep.get("seed", 1)) * 1000 + act_i * 10 + roles.find(r))   # the look of the visitors: same seed, same thief
	_thief_look(r)
	var v = main.spawn(r["kind"], r["from"], first)
	randomize()
	v.route = [[first, HOLD, 0.0, first]]                # never ends by itself - the steps come from here
	v.next_idle = v.now_s() + 9999.0                    # no idle «look round / phone» in between
	v.speed = float(r["spd"])
	if bool(r["torch"]) and main.is_dark() and v.torch == null:
		v.add_torch()
	r["v"] = v
	r["i"] = -1
	_step_next(r)


func _thief_look(r: Dictionary) -> void:
	"""menschen.gd (branch real-menschen): the look of the next figure - at night dark clothes, often a hood or cap, never
	a high-visibility vest; by day like everybody (a thief in daylight does not want to stand out). The pace and the
	posture stay ours (menschen._testing() is true while a run is on, so no random pace / detours from there)."""
	var M = main.get("menschen")
	if M == null or not is_instance_valid(M) or not str(r["kind"]) in ["person", "burglar"]:
		return
	var dark: bool = main.is_dark()
	var nl := {"force": true, "vest": false, "bag": false, "bike": false, "umbrella": false}
	nl["height"] = clampf(randfn(1.76, 0.07), 1.6, 1.95)
	if str(r["kind"]) == "burglar":
		pass                                             # actor.gd: the burglar has his own dark clothes and hood
	elif dark:
		nl["jacket"] = M.DARK[randi() % M.DARK.size()]
		nl["trousers"] = M.DARK[randi() % M.DARK.size()]
		nl["hood"] = randf() < 0.55
		nl["cap"] = not bool(nl["hood"]) and randf() < 0.4
	else:
		nl["jacket"] = (M.DARK + M.BRIGHT)[randi() % (M.DARK.size() + M.BRIGHT.size())]
		nl["hood"] = false
		nl["cap"] = randf() < 0.3
	nl["pack"] = randf() < 0.35                         # a backpack for the loot
	M._next_look = nl


func _posture(v, c: float) -> void:
	v._want_p = 1.0 if c >= 1.5 else 0.0
	v._want_c = minf(c, 1.0)
	v._post_smooth = true


func _step_next(r: Dictionary) -> void:
	r["i"] = int(r["i"]) + 1
	var v = r["v"]
	if int(r["i"]) >= (r["steps"] as Array).size():
		r["gone"] = true
		if v != null and is_instance_valid(v):
			v.route = []
			v.wait_until = 0.0
		return
	var s: Dictionary = r["steps"][r["i"]]
	r["t_step"] = now()
	for k in ["near_d", "near_t", "near_i", "out_t"]:
		r.erase(k)
	_enter_sec(str(s.get("sec", "")))
	var spd: float = float(s.get("spd", -1.0))
	v.speed = spd if spd > 0.0 else float(r["spd"])
	match str(s["do"]):
		"go":
			_move(v, s["p"], float(s.get("c", 0.0)), s.get("look"))
			r["until"] = now() + v.position.distance_to(s["p"]) / maxf(0.2, float(v.speed) * (0.3 if float(s.get("c", 0.0)) >= 1.5 else (0.6 if float(s.get("c", 0.0)) > 0.5 else 1.0))) * 2.2 + 12.0
		"wait", "grab", "handle", "talk":
			_stand(v, float(s.get("c", 0.0)), s.get("look"))
			r["until"] = now() + float(s.get("s", 3.0))
			if str(s["do"]) == "handle":
				main.add_sound(-30.0, v.position + Vector3(0, 1.0, 0), 0.6)       # a quiet click of the handle
			elif str(s["do"]) == "talk":
				main.emit_sound("voice", 1, v.position + Vector3(0, 1.5, 0))
				r["next_talk"] = now() + _rng.randf_range(6.0, 10.0)
			elif str(s["do"]) == "grab":
				_grab_t = now() - t0 if _grab_t < 0.0 else _grab_t
				_note(T.t("%s greift zu (%s)", [T.t(str(r["name"])), T.t(_what_name(str(s.get("what", ""))))]))
				if str(s.get("what", "")) == "velo":
					main.add_sound(-14.0, v.position + Vector3(0, 0.5, 0), 0.5)   # the bolt cutter
		"signal":
			flags[str(s["key"])] = now()
			_step_next(r)
		"sync":
			_stand(v, 0.8, _hp())
			r["until"] = 1e12
		"leave":
			v.route = []
			v.target = s["p"]
			v.wait_until = 0.0
			_posture(v, 0.0)
			v._face(s["p"])
			r["until"] = now() + 120.0


func _move(v, p: Vector3, c: float, look) -> void:
	v.target = p
	v.wait_until = 0.0
	v.route = [[p, HOLD, c, look if look != null else p]]
	_posture(v, c)
	v._face(p)


func _stand(v, c: float, look) -> void:
	v.route = []
	v.target = v.position
	v.wait_until = v.now_s() + HOLD
	_posture(v, c)
	if look != null:
		v._face(look)


func _what_name(w: String) -> String:
	return {"velo": "Velo", "rucksack": "Rucksack", "kuehlbox": "Kühlbox"}.get(w, w)


func _step_done(r: Dictionary) -> bool:
	var s: Dictionary = r["steps"][r["i"]]
	var v = r["v"]
	match str(s["do"]):
		"go":
			return (v.route.is_empty() and _flat(v.position).distance_to(_flat(s["p"])) < 0.7) or now() > float(r["until"]) or _stuck(r, s["p"])
		"sync":
			if flags.has(str(s["key"])):
				return now() > float(flags[str(s["key"])]) + float(s.get("extra", 0.0))
			return false
		"leave":
			return v.done or now() > float(r["until"]) or _gone_out(r)
	return now() >= float(r["until"])


func _stuck(r: Dictionary, p: Vector3) -> bool:
	"""a point behind a tent / car / fence: no closer for 6 s (1.5 m away: 3 s) - take the next step from where it is"""
	var d: float = _flat(r["v"].position).distance_to(_flat(p))
	var t := now()
	if not r.has("near_d") or d < float(r["near_d"]) - 0.25 or float(r.get("near_i", -1)) != float(r["i"]):
		r["near_d"] = d
		r["near_t"] = t
		r["near_i"] = r["i"]
		return false
	return t - float(r["near_t"]) > (3.0 if d < 1.5 else 6.0)


func _gone_out(r: Dictionary) -> bool:
	"""leaving: once out of the picture (head + thermal camera) for 6 s and 14 m from the device, the run need not wait
	until the figure reaches its far exit point (shorter runs, the same truth - nothing more to see)"""
	var v = r["v"]
	if main.testrun.visible(v) or main.testrun.thermal_visible(v) or _flat(v.position).distance_to(_flat(_hp())) < 14.0:
		r["out_t"] = now()
		return false
	if not r.has("out_t"):
		r["out_t"] = now()
	return now() - float(r["out_t"]) > 6.0


func _process(dt: float) -> void:
	if not running:
		return
	var t := now()
	if t < act_t0:
		return
	var all_gone := true
	for r in roles:
		if bool(r["gone"]):
			continue
		all_gone = false
		if r["v"] == null:
			_spawn(r)
			continue
		var v = r["v"]
		if not is_instance_valid(v) or v.is_queued_for_deletion() or v.done:
			r["gone"] = true
			continue
		_react(r, t)
		if str(r.get("state", "")) == "back":
			if _back_done(r):
				_resume(r)
			continue
		if int(r["i"]) < (r["steps"] as Array).size() and _step_done(r):
			var s: Dictionary = r["steps"][r["i"]]
			if str(s["do"]) == "grab":
				_take(r, str(s.get("what", "")))
			elif str(s["do"]) == "leave":
				r["gone"] = true
				if is_instance_valid(v):
					v.queue_free()
				continue
			_step_next(r)
		elif int(r["i"]) < (r["steps"] as Array).size() and str(r["steps"][r["i"]]["do"]) == "talk" and t > float(r.get("next_talk", 0.0)):
			main.emit_sound("voice", 1, v.position + Vector3(0, 1.5, 0))
			r["next_talk"] = t + _rng.randf_range(6.0, 10.0)
	_sample_t -= dt
	if _sample_t <= 0.0:
		var dd := 0.5 if Quality.lite() else 0.25          # Lite (Pi 5): half as often - cheap anyway
		_sample(dd)
		_sample_t = dd
	if all_gone:
		_next_act()
	elif t - t0 > 900.0:
		_note(T.t("Zeit um (15 Minuten) – abgebrochen."))
		stop(true)


func _react(r: Dictionary, t: float) -> void:
	"""night thieves: the white light of MoveEye - freeze, back into cover, wait, try again; twice or the siren - away"""
	if not bool(r["shy"]) or bool(r["fled"]):
		return
	var v = r["v"]
	var L: Dictionary = main.mw.get("lights", {})
	var lit: bool = bool(L.get("white", false)) and main.is_dark() and v.position.distance_to(_hp()) < 22.0
	var loud: bool = str(main.mw.get("sound", "")) != ""
	if loud or (lit and int(r["lit_n"]) >= 1 and str(r["state"]) != "back"):
		_flee(r, T.t("Sirene") if loud else T.t("Licht (zweites Mal)"))
		return
	if lit and str(r["state"]) == "":
		r["lit_n"] = int(r["lit_n"]) + 1
		r["state"] = "back"
		r["back_i"] = int(r["i"])
		v.startle()
		if v.torch != null:
			v.torch.visible = false
		_note(T.t("%s: Licht an – erstarrt, zieht sich zurück", [T.t(str(r["name"]))]))
		var hide := _hide_spot(v.position, 4.0, 9.0, r["from"])
		# freeze lying down a moment, then into cover, then wait until it is dark again
		r["back_steps"] = [_wait(_rng.randf_range(4.0, 9.0), 2.0, _hp()), _go(hide, 1.0, "", 1.0), {"do": "dark", "s": _rng.randf_range(15.0, 35.0)}]
		r["back_k"] = 0
		_back_step(r)


func _back_step(r: Dictionary) -> void:
	var v = r["v"]
	var bs: Array = r["back_steps"]
	var k: int = int(r["back_k"])
	if k >= bs.size():
		return
	var s: Dictionary = bs[k]
	r["t_step"] = now()
	if str(s["do"]) == "go":
		_move(v, s["p"], float(s.get("c", 0.0)), null)
		r["until"] = now() + v.position.distance_to(s["p"]) / 0.4 + 10.0
	else:
		_stand(v, 1.0 if str(s["do"]) == "dark" else float(s.get("c", 0.0)), s.get("look"))
		r["until"] = now() + float(s.get("s", 5.0))
	# the role's own step test looks at the step of the plan - while «back» we use the small list
	r["back_s"] = s


func _back_done(r: Dictionary) -> bool:
	var s: Dictionary = r["back_s"]
	var v = r["v"]
	if str(s["do"]) == "go":
		return (v.route.is_empty() and _flat(v.position).distance_to(_flat(s["p"])) < 0.7) or now() > float(r["until"])
	return now() >= float(r["until"])


func _resume(r: Dictionary) -> void:
	"""a step of the retreat is done: the next one, or (dark again) back to the step that was cut off"""
	var s: Dictionary = r["back_s"]
	if str(s["do"]) == "dark" and bool(main.mw.get("lights", {}).get("white", false)):
		r["until"] = now() + 5.0                         # still light: wait on
		return
	r["back_k"] = int(r["back_k"]) + 1
	if int(r["back_k"]) < (r["back_steps"] as Array).size():
		_back_step(r)
		return
	r["state"] = ""
	_note(T.t("%s: wieder dunkel – versucht es nochmals", [T.t(str(r["name"]))]))
	var v = r["v"]
	if v.torch != null and bool(r["torch"]):
		v.torch.visible = true
	r["i"] = int(r["back_i"]) - 1
	_step_next(r)


func _flee(r: Dictionary, why: String) -> void:
	r["fled"] = true
	r["state"] = "flucht"
	var v = r["v"]
	v.startle()
	if v.torch != null:
		v.torch.visible = false
	_enter_sec("flucht")
	_note(T.t("%s flieht (%s)%s", [T.t(str(r["name"])), why, (" " + T.t("mit Beute")) if r["loot"] != null else ""]))
	var out := _flat(v.position) + _away(v.position) * 18.0 + Vector3(-_away(v.position).z, 0, _away(v.position).x) * (24.0 if _rng.randf() < 0.5 else -24.0)
	r["steps"] = (r["steps"] as Array).slice(0, int(r["i"]) + 1) + [{"do": "leave", "p": out, "sec": "flucht", "spd": 3.4 if str(r["loot"]) != "velo" else 4.0}]
	rep["flucht_grund"] = why
	_step_next(r)


# ---- the check: what was visible, what did MoveEye do -----------------------------------------------------------------
func _enter_sec(k: String) -> void:
	if k == "" or k == _cur_sec:
		return
	if SEC_ORDER.find(k) < SEC_ORDER.find(_cur_sec) and _cur_sec != "":
		return                                            # the second role is still behind - the run is already further
	var t := now() - t0
	if secs.has(_cur_sec):
		secs[_cur_sec]["t1"] = snappedf(t, 0.1)
	_cur_sec = k
	if running and not embedded:
		main.start_info = T.t("Einbruch-Ablauf läuft: %s · %s", [ablauf_name(ablauf), T.t(str(SEC.get(k, k)))])
	if not secs.has(k):
		secs[k] = {"key": k, "name": SEC.get(k, k), "t0": snappedf(t, 0.1), "t1": -1.0, "vis_s": 0.0, "th_s": 0.0, "pic_s": 0.0,
				"first_vis": -1.0, "det_t": -1.0, "push_t": -1.0, "pre_t": -1.0, "light_t": -1.0, "sound_t": -1.0, "pushes": 0}


func _note(what: String) -> void:
	events.append({"t": snappedf(now() - t0, 0.1), "what": what, "sec": _cur_sec})


func _mw_on() -> bool:
	return main.now() - main.mw_t < 6.0


func _sample(dt: float) -> void:
	if not secs.has(_cur_sec):
		return
	var t := now() - t0
	var S: Dictionary = secs[_cur_sec]
	var any_vis := false
	var any_pic := false
	for r in roles:
		var v = r["v"]
		if v == null or not is_instance_valid(v) or v.is_queued_for_deletion():
			continue
		var cam_v: bool = main.testrun.visible(v)
		var th_v: bool = (not cam_v) and main.testrun.thermal_visible(v)
		if cam_v or th_v:
			r["last_vis"] = t
		if main.testrun.present(v):
			any_pic = true
		if t - float(r.get("last_vis", -100.0)) <= GRACE:
			any_vis = true
		if cam_v:
			S["vis_s"] = float(S["vis_s"]) + dt
		elif th_v:
			S["th_s"] = float(S["th_s"]) + dt
	if any_pic:
		S["pic_s"] = float(S["pic_s"]) + dt
		_pic_last = t
	if any_vis and float(S["first_vis"]) < 0.0:
		S["first_vis"] = snappedf(t, 0.1)
	if not _mw_on():
		return
	var det: Dictionary = main.mw_det
	if int(det.get("persons", 0)) > 0 and (any_vis or any_pic):
		_first(S, "det_t", t, T.t("MoveEye erkennt eine Person"))
	var pre: bool = "prealarm" in (det.get("present", []) as Array)
	if pre and not _prev_pre and (any_vis or any_pic):
		_first(S, "pre_t", t, T.t("MoveEye: Vorwarnung"))
	_prev_pre = pre
	var L: bool = bool(main.mw.get("lights", {}).get("white", false))
	if L and not _prev_light:
		_first(S, "light_t", t, T.t("MoveEye macht Licht"))
	_prev_light = L
	var snd: bool = str(main.mw.get("sound", "")) != ""
	if snd and not _prev_sound:
		_first(S, "sound_t", t, T.t("MoveEye: Ton / Sirene (%s)", [str(main.mw.get("sound", ""))]))
	_prev_sound = snd
	var pl = det.get("pushes", null)
	if typeof(pl) != TYPE_ARRAY:
		return
	if not _push_known:
		_known_pushes()
		return
	for x in pl:
		if typeof(x) != TYPE_ARRAY or x.size() < 3 or _push_seen.has(str(x[0])):
			continue
		_push_seen[str(x[0])] = true
		var ev := str(x[2])
		if ev == "tamper":
			# «Kamera verdeckt / verdreht»: no scenario touches the camera - at night after the clock jump or in a dark,
			# noisy picture it is a false alarm of MoveEye, not a warning about the thief (counted apart, shown in the report)
			S["tamper"] = int(S.get("tamper", 0)) + 1
			_note(T.t("Push von MoveEye (tamper) – Sabotage-Meldung, zählt nicht als Warnung"))
		elif ev in ALARM_EVS or ev == "noise":
			if any_vis or any_pic or t - _pic_last <= 6.0:
				S["pushes"] = int(S["pushes"]) + 1
				_first(S, "push_t", t, T.t("Push von MoveEye (%s)", [ev]), true)
			else:
				S["fehl"] = int(S.get("fehl", 0)) + 1          # nobody of the run in the picture: not about the thief
				_note(T.t("Push von MoveEye (%s) – kein Dieb im Bild (Fehlalarm?)", [ev]))


func _first(S: Dictionary, key: String, t: float, what: String, always_note := false) -> void:
	var newone := float(S[key]) < 0.0
	if newone:
		S[key] = snappedf(t, 0.1)
	if newone or always_note:
		_note(what)


# ---- the report -------------------------------------------------------------------------------------------------------
func _first_any(key: String) -> float:
	var best := -1.0
	for k in secs:
		var v := float(secs[k][key])
		if v >= 0.0 and (best < 0.0 or v < best):
			best = v
	return best


func _make_report(finished: bool) -> void:
	if secs.has(_cur_sec) and float(secs[_cur_sec]["t1"]) < 0.0:
		secs[_cur_sec]["t1"] = snappedf(now() - t0, 0.1)
	var parts := []
	var missed := []
	var vis_parts := 0
	var det_parts := 0
	for k in SEC_ORDER:
		if not secs.has(k):
			continue
		var S: Dictionary = secs[k]
		for f in ["vis_s", "th_s", "pic_s"]:
			S[f] = snappedf(float(S[f]), 0.1)
		S["name"] = T.t(str(SEC.get(k, k)))
		parts.append(S)
		if float(S["vis_s"]) + float(S["th_s"]) >= 2.0:
			vis_parts += 1
			if float(S["det_t"]) >= 0.0 or float(S["push_t"]) >= 0.0:
				det_parts += 1
			else:
				missed.append(S["name"])
	var push_t := _first_any("push_t")
	var det_t := _first_any("det_t")
	var light_t := _first_any("light_t")
	var sound_t := _first_any("sound_t")
	var grab := _grab_t
	var verdict := ""
	var score := 0.0
	var mw_on := _mw_on() or det_t >= 0.0 or push_t >= 0.0
	if not mw_on:
		verdict = T.t("MoveEye war nicht verbunden – nur Ablauf und Sichtbarkeit")
	elif push_t >= 0.0 and (grab < 0.0 or push_t <= grab):
		verdict = T.t("gewarnt vor dem Griff") if grab >= 0.0 else T.t("gewarnt (kein Griff)")
		score += 55.0 + (10.0 * clampf((grab - push_t) / 20.0, 0.0, 1.0) if grab >= 0.0 else 10.0)
	elif push_t >= 0.0:
		verdict = T.t("zu spät gewarnt (erst nach dem Griff)")
		score += 25.0
	elif det_t >= 0.0:
		verdict = T.t("erkannt, aber kein Push")
		score += 10.0
	else:
		verdict = T.t("verpasst – nichts gemerkt")
	if mw_on:
		score += 25.0 * (float(det_parts) / float(vis_parts) if vis_parts > 0 else 0.0)
		var react := minf(light_t if light_t >= 0.0 else 1e9, sound_t if sound_t >= 0.0 else 1e9)
		if react < 1e9 and (grab < 0.0 or react <= grab):
			score += 10.0                               # light / siren before the grab: the thief is disturbed
	var n_tamper := 0
	var n_fehl := 0
	for k2 in secs:
		n_tamper += int(secs[k2].get("tamper", 0))
		n_fehl += int(secs[k2].get("fehl", 0))
	var note := clampf(snappedf(1.0 + 5.0 * score / 100.0, 0.5), 1.0, 6.0)
	rep.merge({"fertig": finished, "dauer_s": snappedf(now() - t0, 0.1), "abschnitte": parts, "ereignisse": events.duplicate(),
			"griff_s": snappedf(grab, 0.1), "erkannt_s": det_t, "push_s": push_t, "licht_s": light_t, "sirene_s": sound_t,
			"vorsprung_s": snappedf(grab - push_t, 0.1) if grab >= 0.0 and push_t >= 0.0 else null,
			"verpasst": missed, "urteil": verdict, "punkte": snappedf(score, 0.1), "note": note, "moveeye": mw_on,
			"schutz_an": bool(main.mw_det.get("armed", main.mw.get("armed", false))), "lite": Quality.lite(),
			"simulator": str(main.VERSION), "beute": _loot_of_run(), "sabotage_pushes": n_tamper, "pushes_ohne_dieb": n_fehl}, true)
	_save()
	info = _summary(rep)
	main.start_info = T.t("Einbruch-Ablauf: %s", [info])
	print("einbruch: done %s seed %d - %s, grade %.1f, push %.1f s, grab %.1f s" % [rep["ablauf"], int(rep["seed"]), verdict, note, push_t, grab])
	if not series.is_empty() or not series_res.is_empty():
		series_res.append(rep.duplicate(true))


func _loot_of_run() -> String:
	for a in acts:
		for r in a["roles"]:
			if r["loot"] != null:
				return _what_name(str(r["loot"]))
	return ""


func _summary(r: Dictionary) -> String:
	var s := "%s · %s · %s %.1f" % [r.get("name", ""), r.get("urteil", ""), T.t("Note"), float(r.get("note", 1.0))]
	if r.get("vorsprung_s") != null:
		s += " · " + T.t("Push %.0f s vor dem Griff", [float(r["vorsprung_s"])])
	if not (r.get("verpasst", []) as Array).is_empty():
		s += " · " + T.t("verpasst: %s", [", ".join(PackedStringArray(r["verpasst"]))])
	return s


func _series_report() -> void:
	var sum := 0.0
	var warned := 0
	for r in series_res:
		sum += float(r["note"])
		if float(r.get("push_s", -1.0)) >= 0.0 and (float(r.get("griff_s", -1.0)) < 0.0 or float(r["push_s"]) <= float(r["griff_s"])):
			warned += 1
	var n := series_res.size()
	rep = {"serie": series_res.duplicate(true), "n": n, "vor_griff_gewarnt": warned, "note_mittel": snappedf(sum / maxf(1.0, n), 0.1),
			"date": Time.get_datetime_string_from_system(false, true), "scene": str(main.scene), "name": T.t("Alle Abläufe nacheinander")}
	_save()
	info = T.t("Serie: %d Abläufe, %d vor dem Griff gewarnt, Note im Mittel %.1f", [n, warned, float(rep["note_mittel"])])
	main.start_info = T.t("Einbruch-Abläufe: %s", [info])
	series_res = []


func _save() -> void:
	var dir := OS.get_user_data_dir().path_join("einbruch")
	DirAccess.make_dir_recursive_absolute(dir)
	var stamp := Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
	var base := dir.path_join(("serie_" if rep.has("serie") else "einbruch_%s_" % str(rep.get("ablauf", ""))) + stamp)
	var f := FileAccess.open(base + ".json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(rep, " "))
	var h := FileAccess.open(base + ".html", FileAccess.WRITE)
	if h != null:
		h.store_string(html(rep))
		last_html = base + ".html"


func _ts(x) -> String:
	return "–" if x == null or float(x) < 0.0 else "%.0f s" % float(x)


func _one_html(r: Dictionary) -> String:
	var rows := ""
	for S in r.get("abschnitte", []):
		rows += "<tr><td>%s</td><td>%s – %s</td><td>%.0f s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % [S["name"], _ts(S["t0"]), _ts(S["t1"]),
				float(S["vis_s"]), (" <span class=mut>(+%.0f s Wärmebild)</span>" % float(S["th_s"])) if float(S["th_s"]) > 0.0 else "",
				_ts(S["det_t"]), _ts(S["push_t"]), _ts(S["pre_t"]), "%s / %s" % [_ts(S["light_t"]), _ts(S["sound_t"])]]
	var ev := ""
	for e in r.get("ereignisse", []):
		ev += "<li>%.0f s · %s</li>" % [float(e["t"]), str(e["what"])]
	return """<h2>%s <span class=mut>· %s %d · %s</span></h2><div class="big"><div class="t">%s<b>%s</b></div><div class="t">%s<b>%.1f</b></div>
<div class="t">%s<b>%s</b></div><div class="t">%s<b>%s</b></div><div class="t">%s<b>%s</b></div></div>
<table><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>%s</table><h3>%s</h3><ul>%s</ul>""" % [
			r.get("name", ""), T.t("Zufall"), int(r.get("seed", 0)), r.get("scene", ""), T.t("Urteil"), r.get("urteil", ""), T.t("Note"), float(r.get("note", 1.0)),
			T.t("Erster Push"), _ts(r.get("push_s")), T.t("Griff"), _ts(r.get("griff_s")), T.t("Verpasst"), ", ".join(PackedStringArray(r.get("verpasst", []))) if not (r.get("verpasst", []) as Array).is_empty() else "–",
			T.t("Abschnitt"), T.t("Zeit"), T.t("sichtbar"), T.t("erkannt"), T.t("Push"), T.t("Vorwarnung"), T.t("Licht / Ton"), rows, T.t("Ablauf"), ev if ev != "" else "<li>–</li>"]


func html(r: Dictionary) -> String:
	var body := ""
	if r.has("serie"):
		body = "<p>%s</p>" % T.t("Serie: %d Abläufe, %d vor dem Griff gewarnt, Note im Mittel %.1f", [int(r["n"]), int(r["vor_griff_gewarnt"]), float(r["note_mittel"])])
		for x in r["serie"]:
			body += _one_html(x)
	else:
		body = _one_html(r)
		if int(r.get("sabotage_pushes", 0)) + int(r.get("pushes_ohne_dieb", 0)) > 0:
			body += "<p class=mut>%s</p>" % T.t("Nicht als Warnung gezählt: %d Sabotage-Pushes (tamper), %d Pushes ohne Dieb im Bild.", [int(r.get("sabotage_pushes", 0)), int(r.get("pushes_ohne_dieb", 0))])
		if not bool(r.get("moveeye", false)):
			body += "<p class=mut>%s</p>" % T.t("MoveEye war nicht verbunden – nur Ablauf und Sichtbarkeit")
		elif not bool(r.get("schutz_an", false)):
			body += "<p class=mut>%s</p>" % T.t("Hinweis: der Schutz von MoveEye war aus – ohne Schutz gibt es keine Pushes.")
	return """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Einbruch-Abläufe</title><style>body{font:15px system-ui,sans-serif;background:#0a0e14;color:#e8eef5;margin:0;padding:16px;max-width:960px}
h1{font-size:22px}h2{font-size:18px;margin-top:26px}.big{display:flex;gap:10px;flex-wrap:wrap}.t{background:#151e2b;border:1px solid #1f2b3a;border-radius:12px;padding:10px 14px}
.t b{display:block;font-size:20px}table{border-collapse:collapse;width:100%%;margin-top:12px;font-size:14px}td,th{border-bottom:1px solid #1f2b3a;padding:5px 6px;text-align:left}
.mut{color:#8a9bb0}</style></head><body><h1>%s · %s</h1><p class="mut">%s · %s %s</p>%s</body></html>""" % [
			T.t("Einbruch-Abläufe"), r.get("name", ""), r.get("date", ""), T.t("Szene"), r.get("scene", ""), body]


func open_report() -> void:
	if last_html != "" and FileAccess.file_exists(last_html):
		OS.shell_open(last_html)
	else:
		info = T.t("Noch kein Bericht – zuerst einen Ablauf starten.")
		paint()


# ---- the night test run (nachtlauf.gd) ---------------------------------------------------------------------------------
func _night_incident(ev: Dictionary) -> Array:
	"""nachtlauf.gd «incident»: one of the night runs at its target (no clock jump, no lock, nachtlauf writes the truth)"""
	if running:
		return []
	var tg := str(ev.get("target", "tent"))
	var pick: Array = {"bike": ["velo", "warten", "kundschaft"], "door": ["autos_zelte", "warten"]}.get(tg, ["kuehlbox", "warten", "autos_zelte", "kundschaft"])
	var id: String = pick[int(ev.get("id", 0)) % pick.size()]
	embedded = true
	_reset_run()
	ablauf = id
	_rng.seed = int(ev.get("id", 1)) * 7919 + 13
	acts = _build(id, true)
	acts = [acts[acts.size() - 1]]                      # only the night act
	rep = {"ablauf": id, "name": ablauf_name(id), "seed": int(ev.get("id", 0)), "scene": str(main.scene)}
	running = true
	t0 = now()
	act_i = -1
	_next_act()
	var out := []
	for r in roles:
		_spawn(r)
		out.append(r["v"])
	return out


# ---- the panel ----------------------------------------------------------------------------------------------------------
func state() -> Dictionary:
	return {"running": running, "ablauf": ablauf, "abschnitt": _cur_sec, "t": snappedf(now() - t0, 0.1) if running else 0.0,
			"serie_rest": series.size(), "info": info, "embedded": embedded}


func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	match dd:
		"start":
			var e := start(str(d.get("ablauf", "zufall")), int(d.get("seed", -1)), d.get("zeit", null))
			return {"ok": e == "", "error": e, "state": state()}
		"serie":
			var e2 := start_series(int(d.get("seed", -1)), d.get("zeit", null), d.get("liste", []))
			return {"ok": e2 == "", "error": e2, "state": state()}
		"stop":
			series = []
			stop(false)
			return {"ok": true, "state": state()}
		"state":
			return {"ok": true, "state": state()}
		"result":
			return {"ok": true, "result": rep, "html": last_html}
	var ab := []
	for k in ORDER:
		ab.append({"id": k, "name": ablauf_name(k), "info": T.t(str(ABL[k][1]))})
	return {"ok": true, "ablaeufe": ab, "state": state(), "seed": seed_n, "zeit": use_time}


func add_controls() -> void:
	var g := "Testen"
	var X := {"sub": "Einbruch-Abläufe"}
	var opts := [["zufall", T.t("zufällig")]]
	for k in ORDER:
		opts.append([k, ablauf_name(k)])
	main.add_control("select", "einbruch_ablauf", T.t("Einbruch-Ablauf"), func(): return ablauf_pick, func(v): ablauf_pick = str(v), g, _x(X, {"options": opts}))
	main.add_control("slider", "einbruch_seed", T.t("Zufall (Seed, 0 = jedes Mal neu)"), func(): return seed_n, func(v): seed_n = int(v), g, _x(X, {"min": 0, "max": 99, "step": 1}))
	main.add_control("toggle", "einbruch_zeit", T.t("Tageszeit des Ablaufs (tagsüber auskundschaften, nachts zurück) – sonst die jetzige Zeit"), func(): return use_time, func(v): use_time = bool(v), g, X)
	main.add_control("button", "einbruch_start", T.t("▶ Ablauf starten (Bewertung: wann warnt MoveEye?)"), null, func(): _ui_msg(start(ablauf_pick)), g, X)
	main.add_control("button", "einbruch_serie", T.t("▶ Alle Abläufe nacheinander (etwa 20 Minuten)"), null, func(): _ui_msg(start_series()), g, X)
	main.add_control("button", "einbruch_stop", T.t("⏹ Ablauf abbrechen"), null, func(): series = []; stop(false), g, X)
	main.add_control("button", "einbruch_bericht", T.t("Bericht zeigen"), null, func(): open_report(), g, _x(X, {"expert": true}))


var ablauf_pick := "zufall"


func _x(a: Dictionary, b: Dictionary) -> Dictionary:
	var o := a.duplicate()
	o.merge(b, true)
	return o


func _ui_msg(e: String) -> void:
	if e != "":
		info = e
		main.start_info = e
	paint()


func add_info(body, UI) -> void:
	body.add_child(UI.small(T.t("Diebe wie echt: auskundschaften, warten, Licht meiden, Deckung, Ablenkung zu zweit, Flucht. Jeder Ablauf ist ein Zufall mit Seed und findet Ziel und Deckung in jeder Szene selbst. Für Pushes muss der Schutz von MoveEye an sein.")))
	label = UI.small("", UI.TXT)
	label.add_theme_font_size_override("font_size", 13)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(label)
	paint()


func paint() -> void:
	if label != null:
		label.text = main.no_emoji(info) if info != "" else T.t("Noch kein Einbruch-Ablauf.")


func status() -> String:
	if running and not embedded:
		return T.t("Einbruch-Ablauf: %s · %s", [ablauf_name(ablauf), T.t(str(SEC.get(_cur_sec, _cur_sec)))])
	return ""
