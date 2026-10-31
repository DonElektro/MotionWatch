extends Node
## 3D-4.x «MoveEye als KI-Wächter» (wish of Daniel 30.10.2026, for his development tests in online games): when the switch is
## on (main.game_kiguard: MoveEye's simulator page / game card, or the simulator panel «Spiel») and a round WITH a guard role
## starts («Wächter» / Wächter-Duell, «Team gegen Team», «Team gegen MoveEye», also online rounds), MoveEye itself is the guard:
##   · the round runs as «Team gegen MoveEye» (main.game_mode = "mwhand" for this round, back afterwards): every player
##     (phones, online guests, bots) sneaks, nobody guards by hand, the Bot-Wächter (gamebots.gd) stays out;
##   · the shutter of the guards at MoveEye gets «KI-Autopilot» (gamekihilfe.gd mode "auto" for "mw"): MoveEye's REAL
##     detection gives the boxes, MoveEye's head follows (MoveEye 542 kihilfe_follow: «Folgen pausiert in Team gegen
##     MoveEye» (2.98.39) lets the head follow because the mode is «auto»), the autopilot fires (energy of gametools.gd);
##   · the results say «Wächter: MoveEye (KI)», the round gives no XP / badges and is NOT added to the leaderboard of the
##     people - it goes into its own list «gegen die KI» (user://game_kiboard.json, game_info "kig").
## Needs MoveEye connected at the start of the round (otherwise a normal round, a news line says why).
## Control: {action: "game_kig", op: "info" | "set" (on) | "reset"} - the switch is also the control «game_kiguard».

const NAME := "Wächter: MoveEye (KI)"
## Fair like a person (Daniel 30.10.2026): the same energy and cooldowns of gametools.gd (the fairness of gamerules.gd - more
## energy, Bot-Helfer - does not apply: it is off in «Team gegen MoveEye»), a reaction time of 0.5 s, and the difficulty sets
## how long and how big it must see a sure box in the hit circle before it fires (gamekihilfe._auto): easy slower, hard faster.
## «Rollen reihum» (gamerules._rotate) pauses while the switch is on - everybody stays sneaker.
const REACT := 0.5
const LEVEL := {"easy": [0.6, 0.14], "normal": [0.3, 0.09], "hard": [0.1, 0.06]}   # [seconds more to see, smallest box height]
const FILE := "user://game_kiboard.json"

var game
var main
var active := false                        # this round is guarded by MoveEye's AI
var mode_was := ""                         # the game type before (back after the round)
var board := {}                            # name (lower case) -> {n, c, rounds, score, caught, goal, clean}
var ki_stats := {"rounds": 0, "catches": 0, "false": 0, "shots": 0}
var _loaded := false


func mw_ok() -> bool:
	return main.now() - float(main.mw_t) < 3.0


func guard_mode(m: String) -> bool:
	return m in ["guard", "mwhand"]


func round_start() -> void:
	"""game.start_round (first thing): take the guard role for MoveEye"""
	active = false
	if not bool(main.game_kiguard) or not guard_mode(str(main.game_mode)):
		return
	if game.cmp != null and game.cmp.busy():               # «Mensch gegen KI» (gamecompare.gd) has its own guards
		return
	if not mw_ok():
		game.news("🤖 KI-Wächter: MoveEye ist nicht verbunden – normale Runde")
		return
	mode_was = str(main.game_mode)
	main.game_mode = "mwhand"
	active = true
	for p in game.players:                                 # everybody sneaks (the elif of start_round does it too)
		if p != null and p["role"] == "guard":
			game._assign(p, "runner")
	game.news("🤖 MoveEye ist der Wächter (KI): echte Erkennung, der Kopf folgt, der Auslöser löst selbst aus")


func after_start() -> void:
	"""game.start_round (after shut.round_start): the autopilot for the guards at MoveEye"""
	if active:
		game.shut.ki.mode["mw"] = "auto"


func _process(_dt: float) -> void:
	if not active or game == null:
		return
	if game.round_state in ["countdown", "play"]:
		if str(game.shut.ki.mode.get("mw", "off")) != "auto":     # somebody switched the help off: the KI guard stays
			game.shut.ki.mode["mw"] = "auto"
		return
	active = false                                         # the round is over: the game type back
	if mode_was != "":
		main.game_mode = mode_was
		mode_was = ""


func hold_s() -> float:
	return REACT + float(LEVEL.get(game.rules.glevel(), LEVEL["normal"])[0])


func big_enough(bx: Array) -> bool:
	return float(bx[3]) >= float(LEVEL.get(game.rules.glevel(), LEVEL["normal"])[1])


func guard_line(gm: Array) -> Dictionary:
	"""game.end_round: the line of the guard"""
	return {"n": "🤖 " + NAME, "c": "#3b8cff", "info": NAME + " · " + str(gm[1]) + game._shut_info(game.mwg),
			"score": max(0, int(gm[0]) + int(game.mwg.get("shut_pts", 0))), "kig": true}


func mark_results(results: Array) -> void:
	"""game.end_round: every line says it, the round goes into the list «gegen die KI» (not into the leaderboard)"""
	_load()
	for r in results:
		r["ki"] = true
		r["kig"] = true
		if not str(r["n"]).begins_with("🤖 "):
			r["info"] = str(r.get("info", "")) + " · 🤖 gegen die KI – eigene Liste, zählt nicht für die Rangliste"
	for p in game.players:
		if p == null or p["role"] != "runner":
			continue
		var k := str(p["name"]).to_lower()
		var b: Dictionary = board.get(k, {"n": p["name"], "c": "#" + game.COLORS[p["slot"]].to_html(false), "rounds": 0, "score": 0, "caught": 0, "goal": 0, "clean": 0})
		var sc := 0
		for r in results:
			if r["n"] == p["name"]:
				sc = int(r["score"])
		b["n"] = p["name"]
		b["rounds"] = int(b["rounds"]) + 1
		b["score"] = int(b["score"]) + sc
		b["caught"] = int(b["caught"]) + int(p["caught"])
		if p["state"] == "goal" or float(p.get("t_goal", 0.0)) > 0.0:
			b["goal"] = int(b["goal"]) + 1
		if int(p["caught"]) == 0:
			b["clean"] = int(b["clean"]) + 1
		if str(p.get("kind", "")) == "bot":
			b["bot"] = true
		board[k] = b
	ki_stats["rounds"] = int(ki_stats["rounds"]) + 1
	ki_stats["catches"] = int(ki_stats["catches"]) + int(game.mwg.get("catches", 0))
	ki_stats["false"] = int(ki_stats["false"]) + int(game.mwg.get("false", 0))
	ki_stats["shots"] = int(ki_stats["shots"]) + int(game.shut.ki.auto_shots)
	_save()
	game.news("🤖 Runde gegen die KI – sie steht in der Liste «gegen die KI», nicht in der Rangliste")


func board_list() -> Array:
	_load()
	var out: Array = board.values()
	out.sort_custom(func(x, y): return int(x["score"]) > int(y["score"]))
	return out.slice(0, 10)


func info() -> Dictionary:
	return {"on": bool(main.game_kiguard), "active": active, "mw": mw_ok(), "name": NAME, "hold": snappedf(hold_s(), 0.01), "board": board_list(), "ki": ki_stats.duplicate(),
			"mode_was": mode_was,
			"turm": game.more.turm.board() if game.more != null and game.more.turm != null else [],    # «Gameplay ausfeilen»: KI-Turm (gameturm.gd)
			"turm_on": game.more != null and game.more.turm != null and game.more.turm.on, "turm_floor": game.more.turm.floor_n() if game.more != null and game.more.turm != null else 0}


func command(d: Dictionary) -> Dictionary:
	var op := str(d.get("op", "info"))
	if op == "set":
		main.game_kiguard = bool(d.get("on", false))
		game.news("🤖 MoveEye als KI-Wächter: " + ("ein" if main.game_kiguard else "aus"))
	elif op == "reset":
		board = {}
		ki_stats = {"rounds": 0, "catches": 0, "false": 0, "shots": 0}
		_loaded = true
		_save()
	return dict_ok(info())


func dict_ok(d: Dictionary) -> Dictionary:
	d["ok"] = true
	return d


func _load() -> void:
	if _loaded:
		return
	_loaded = true
	var f := FileAccess.open(FILE, FileAccess.READ)
	if f == null:
		return
	var d = JSON.parse_string(f.get_as_text())
	if d is Dictionary:
		if d.get("board", null) is Dictionary:
			board = d["board"]
		if d.get("ki", null) is Dictionary:
			for k in ki_stats:
				ki_stats[k] = int(d["ki"].get(k, 0))


func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"board": board, "ki": ki_stats}))
