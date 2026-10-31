extends RefCounted
## «KI-Turm» (Gameplay ausfeilen, Punkt 9, Daniel 31.10.2026): round after round against the AI guard, floor by floor harder.
## The guard is «MoveEye als KI-Wächter» (gamekiwaechter.gd: MoveEye's real AI, the head follows, the autopilot shoots)
## when MoveEye is connected - otherwise the Bot-Wächter of the simulator (gamebots.gd). A floor is won when at least one
## person reaches the goal; then the next floor starts harder (FLOORS: difficulty, Wächter-Stufe, lives, minutes, bushes,
## and the skill of the Bot-Wächter). Lost = the tower is over. The highest floor goes into the own list «KI-Turm – gegen
## die KI» (user://spiel/kiturm.json, per name; not into the ranking of the evening). Fairness automatisch is off in the tower.
## Started with the quick card «🗼 KI-Turm» (or CONTROL game_more op turm_start).

const T = preload("res://scripts/i18n.gd")
const FILE := "user://spiel/kiturm.json"
# per floor: [Schleicher-Stufe, Wächter-Stufe, lives, minutes, bushes, bot skill]
const FLOORS := [["easy", "easy", "0", 3, 4, 0.55], ["easy", "normal", "3", 3, 3, 0.65], ["normal", "normal", "3", 3, 3, 0.72],
		["normal", "normal", "3", 3, 2, 0.8], ["normal", "hard", "1", 3, 2, 0.86], ["hard", "hard", "1", 3, 2, 0.9],
		["hard", "hard", "1", 2, 1, 0.94], ["hard", "hard", "1", 2, 1, 0.97], ["hard", "hard", "1", 2, 0, 1.0]]

var game
var main
var more
var on := false
var floor_i := 0                         # 0 = floor 1
var best := 0                            # the highest floor reached in this tower
var who: Array = []                      # the people in this tower
var over := false
var ki_mw := false                       # MoveEye's AI is the guard (else the Bot-Wächter)
var last := ""                           # the line after the last round


func start() -> void:
	on = true
	over = false
	floor_i = 0
	best = 0
	last = ""
	_apply()
	game.news(T.t("🗼 KI-Turm: Stufe 1 – schaffst du es an der KI vorbei?"))


func stop() -> void:
	on = false


func floor_n() -> int:
	return floor_i + 1


func _apply() -> void:
	"""the settings of the floor (like the wizard would set them)"""
	var F: Array = FLOORS[mini(floor_i, FLOORS.size() - 1)]
	ki_mw = game.kig != null and game.kig.mw_ok()
	main.control_set("game_mode", "guard")
	main.control_set("game_goal", "reach")
	main.control_set("game_level", F[0])
	main.control_set("game_lives", F[2])
	main.control_set("game_minutes", F[3])
	main.control_set("game_hides", F[4])
	main.control_set("game_botguard", true)
	main.control_set("game_kiguard", ki_mw)
	game.rules.guard_level = str(F[1])
	game.rules.rotate = "off"
	game.bots.skill[game.bots.GUARD_NAME] = float(F[5])
	for p in game.players:                                 # everybody sneaks against the AI
		if p != null and p["role"] == "guard":
			game._set_role(p, "runner")


func round_start() -> void:
	if not on or over:
		return
	who = []
	for p in game.players:
		if p != null and p["role"] == "runner" and str(p.get("kind", "phone")) != "bot":
			who.append(str(p["name"]))
	var g_name: String = T.t("MoveEye (KI)") if game.kig != null and game.kig.active else T.t("Bot-Wächter (Stärke %d %%)", [int(float(FLOORS[mini(floor_i, FLOORS.size() - 1)][5]) * 100.0)])
	game.news(T.t("🗼 KI-Turm Stufe %d – Wächter: %s", [floor_n(), g_name]))
	for p in game.players:
		if p != null:
			game._say(p, T.t("🗼 KI-Turm Stufe %d von %d", [floor_n(), FLOORS.size()]), 4.0)


func after_round(results: Array) -> void:
	if not on or over:
		return
	var won := false
	for p in game.players:
		if p != null and p["role"] == "runner" and str(p.get("kind", "phone")) != "bot" and (p["state"] == "goal" or float(p.get("t_goal", 0.0)) > 0.0):
			won = true
	best = maxi(best, floor_n() if won else floor_i)
	for r in results:
		if str(r.get("role", "")) == "runner":
			r["info"] = str(r.get("info", "")) + " · " + T.t("🗼 KI-Turm Stufe %d", [floor_n()])
	if won and floor_i < FLOORS.size() - 1:
		last = T.t("🗼 Stufe %d geschafft! Weiter auf Stufe %d – die KI wird schwerer.", [floor_n(), floor_n() + 1])
		floor_i += 1
		_save()
		_apply.call_deferred()
	elif won:
		last = T.t("🗼 Ganz oben! Alle %d Stufen des KI-Turms geschafft!", [FLOORS.size()])
		over = true
		_save()
	else:
		last = T.t("🗼 Die KI hat gewonnen – der Turm endet auf Stufe %d. Neuer Versuch: Schnellstart «KI-Turm».", [maxi(1, best)])
		over = true
		_save()
	game.news(last)


func _db() -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _save() -> void:
	"""the own list «KI-Turm – gegen die KI»: the highest floor per name (and when)"""
	if best <= 0:
		return
	var d := _db()
	for nm in who:
		var k := str(nm).strip_edges().to_lower()
		var e: Dictionary = d.get(k, {"n": nm, "best": 0, "towers": 0, "ki": false})
		if best > int(e["best"]):
			e["best"] = best
			e["t"] = Time.get_datetime_string_from_system(false, true)
			e["ki"] = ki_mw
		e["n"] = nm
		e["towers"] = int(e.get("towers", 0)) + (1 if over else 0)
		d[k] = e
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func board() -> Array:
	var out: Array = _db().values()
	out.sort_custom(func(x, y): return int(x["best"]) > int(y["best"]))
	return out.slice(0, 10)


func lines() -> Array:
	if not on:
		return []
	var out := [last if last != "" else T.t("🗼 KI-Turm Stufe %d", [floor_n()])]
	var b := board()
	if not b.is_empty():
		out.append(T.t("Rangliste «KI-Turm – gegen die KI»: %s", [" · ".join(PackedStringArray(b.slice(0, 5).map(func(e): return "%s %s %d" % [e["n"], T.t("Stufe"), int(e["best"])])))]))
	return out


func state() -> Dictionary:
	if not on:
		return {}
	return {"on": true, "floor": floor_n(), "of": FLOORS.size(), "over": over, "best": best, "last": last, "ki": ki_mw,
			"board": board().slice(0, 5), "t_head": T.t("🗼 KI-Turm"), "t_floor": T.t("Stufe"), "t_board": T.t("Rangliste «gegen die KI»")}
