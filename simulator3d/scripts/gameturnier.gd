extends RefCounted
## «Spielabend-Turnier» (Gameplay ausfeilen, Punkt 8, Daniel 31.10.2026): several people play one after the other on ONE
## device (a phone or here at the PC). Before every round the device says who is next («Gerät weitergeben»); the player of
## that device plays under that name. After every round the points go into the table; after the last turn the winner screen
## (podium 1-2-3) on the device and in this window. The names are typed on the device (phone: lobby card; PC: defaults
## «Spieler 1 …», or CONTROL game_more op tour_names). Started with the quick card «🏆 Turnier» or op tour_start.
## Kept by gamemore.gd: on / player / after_round / state.

const T = preload("res://scripts/i18n.gd")

var game
var main
var more
var on := false
var names: Array = []                    # who plays, in this order
var rounds := 2                          # rounds per player
var turn := 0                            # 0 … names.size() × rounds − 1
var table := {}                          # name -> {"n", "pts", "list": [points per round], "goal", "caught"}
var done := false
var podium: Array = []                   # after the last turn: [{"n", "pts"}] (best first)
var _seq := 0


func start(n: int, r: int, nm := []) -> void:
	on = true
	done = false
	podium = []
	turn = 0
	rounds = clampi(r, 1, 3)
	names = []
	for i in range(clampi(n, 2, 8)):
		names.append(str(nm[i]).strip_edges().left(16) if i < nm.size() and str(nm[i]).strip_edges() != "" else T.t("Spieler %d", [i + 1]))
	table = {}
	for x in names:
		table[x] = {"n": x, "pts": 0, "list": [], "goal": 0, "caught": 0}
	game.news(T.t("🏆 Turnier: %d Spieler, je %d Runden – %s beginnt", [names.size(), rounds, names[0]]))
	_apply_name()


func stop() -> void:
	on = false
	done = false


func set_names(nm: Array) -> void:
	"""the names typed on the device (only before the first round)"""
	if not on or turn > 0:
		return
	var old := names.duplicate()
	for i in range(mini(nm.size(), 8)):
		var x := str(nm[i]).strip_edges().left(16)
		if x != "" and i < names.size():
			names[i] = x
	if nm.size() > names.size():
		for i in range(names.size(), mini(nm.size(), 8)):
			var x2 := str(nm[i]).strip_edges().left(16)
			if x2 != "":
				names.append(x2)
	table = {}
	for x in names:
		table[x] = {"n": x, "pts": 0, "list": [], "goal": 0, "caught": 0}
	if old != names:
		_apply_name()


func total() -> int:
	return names.size() * rounds


func current() -> String:
	return names[turn % names.size()] if on and not names.is_empty() else ""


func device_player() -> Variant:
	"""the one person who plays on the device: the PC player first, else the first connected phone"""
	for p in game.players:
		if p != null and str(p.get("kind", "")) == "local":
			return p
	for p in game.players:
		if p != null and str(p.get("kind", "phone")) == "phone" and p.get("sock") != null and p["role"] in ["runner", "guard"]:
			return p
	return null


func _apply_name() -> void:
	var p = device_player()
	if p == null or done:
		return
	p["name"] = current()
	game._say(p, T.t("🏆 %s ist dran (Runde %d von %d) – Gerät weitergeben, dann «Runde starten»", [current(), turn + 1, total()]), 8.0)
	if p.get("sock") != null:
		game._hello(p)


func round_start() -> void:
	if on and not done:
		_apply_name()


func after_round(results: Array) -> void:
	"""game.end_round (gamemore.round_end): the points of the device player into the table, the next turn"""
	if not on or done:
		return
	var p = device_player()
	if p == null:
		return
	var nm := current()
	var pts := 0
	for r in results:
		if int(r.get("slot", -1)) == int(p["slot"]):
			pts = int(r.get("score", 0))
			r["info"] = str(r.get("info", "")) + " · " + T.t("🏆 Turnier: %s, Runde %d/%d", [nm, turn / names.size() + 1, rounds])
	var e: Dictionary = table.get(nm, {"n": nm, "pts": 0, "list": [], "goal": 0, "caught": 0})
	e["pts"] = int(e["pts"]) + pts
	(e["list"] as Array).append(pts)
	e["goal"] = int(e["goal"]) + (1 if p["state"] == "goal" or float(p.get("t_goal", 0.0)) > 0.0 else 0)
	e["caught"] = int(e["caught"]) + int(p.get("caught", 0))
	table[nm] = e
	turn += 1
	if turn >= total():
		done = true
		podium = ranking()
		game.news(T.t("🏆 Turnier vorbei – %s gewinnt mit %d Punkten!", [podium[0]["n"], int(podium[0]["pts"])]))
	else:
		game.news(T.t("🏆 Turnier: %s holt %d – als Nächstes: %s", [nm, pts, current()]))
		_apply_name.call_deferred()
	_seq += 1


func ranking() -> Array:
	var out: Array = table.values()
	out.sort_custom(func(x, y): return int(x["pts"]) > int(y["pts"]))
	return out.map(func(e): return {"n": e["n"], "pts": int(e["pts"]), "list": e["list"], "goal": int(e["goal"]), "caught": int(e["caught"])})


func lines() -> Array:
	"""for the winner screen of this window and the panel"""
	if not on:
		return []
	var out := []
	var i := 0
	var parts := PackedStringArray()
	for e in ranking():
		i += 1
		parts.append("%d. %s %d" % [i, e["n"], int(e["pts"])])
	if done:
		out.append(T.t("🏆 Turnier-Sieger: %s (%d Punkte)", [podium[0]["n"], int(podium[0]["pts"])]))
	else:
		out.append(T.t("🏆 Turnier – als Nächstes: %s (Runde %d von %d)", [current(), turn + 1, total()]))
	out.append(T.t("Punktetabelle: %s", [" · ".join(parts)]))
	return out


func state() -> Dictionary:
	if not on:
		return {}
	return {"on": true, "done": done, "cur": current(), "turn": turn + 1, "total": total(), "rounds": rounds, "names": names,
			"table": ranking(), "podium": podium.slice(0, 3), "edit": turn == 0 and game.round_state == "lobby",
			"t_head": T.t("🏆 Spielabend-Turnier"), "t_next": T.t("Jetzt ist dran:"), "t_pass": T.t("Gerät weitergeben, dann «Runde starten»."),
			"t_names": T.t("Wer spielt mit? (ein Name pro Zeile)"), "t_save": T.t("Namen übernehmen"), "t_win": T.t("gewinnt das Turnier!"),
			"t_table": T.t("Punktetabelle"), "t_again": T.t("Neues Turnier")}
