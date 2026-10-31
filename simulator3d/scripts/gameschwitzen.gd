extends RefCounted
## «Bring MoveEye ins Schwitzen» (Gameplay ausfeilen, Punkt 8, Daniel 31.10.2026): the game goal «🥵». Nobody has to reach
## the goal - the sneakers try to give MoveEye as much work and confusion as possible WITHOUT being caught. Measured with
## what MoveEye itself reports to the simulator every second (state «det» and «cpu», part 290 of MoveEye):
##   · every person box MoveEye reports           +BOX per second
##   · a box comes or goes (new track, lost track)  +FLIP
##   · MoveEye's own CPU above its value at the start of the round  +1 per CPU_STEP % and second (at most CPU_MAX)
##   · «noise» of the microphone                     +NOISE per second
## The points of a second go to the sneakers the head camera sees right now (split). Caught = −150 as always.
## Without MoveEye the simulator estimates (marked «Simulator-Schätzung»): what is moving in the picture of the head camera
## (cam_sees, moving fast, several at once).
## SAFE: simulation only - this goal does not switch anything on at MoveEye (no siren, no light, no push of its own); what
## MoveEye does with its detections is MoveEye's normal behaviour with the simulator.

const T = preload("res://scripts/i18n.gd")
const BOX := 4.0
const FLIP := 8.0
const NOISE := 2.0
const CPU_STEP := 5.0
const CPU_MAX := 6.0

var game
var main
var more
var pts := {}                            # slot -> points
var stat := {"boxes_max": 0, "flips": 0, "cpu_max": -1.0, "cpu0": -1.0, "secs": 0, "est": false}
var _last_n := 0
var _t := 0.0


func active() -> bool:
	return main.game_goal == "sweat" and not main.game_mode in ["free", "jaeger", "seek", "escape"]


func mw_on() -> bool:
	return main.now() - float(main.mw_det_t) < 3.0


func round_start() -> void:
	pts.clear()
	_last_n = 0
	_t = 0.0
	stat = {"boxes_max": 0, "flips": 0, "cpu_max": -1.0, "cpu0": _cpu(), "secs": 0, "est": not mw_on()}
	if active():
		game.news(T.t("🥵 Bring MoveEye ins Schwitzen: viel Arbeit für die Erkennung – aber nicht erwischt werden!") +
				("" if mw_on() else " " + T.t("(MoveEye nicht verbunden: Simulator-Schätzung)")))


func _cpu() -> float:
	var c = main.cpu_info.get("mw", null) if typeof(main.cpu_info) == TYPE_DICTIONARY else null
	return float(c) if c != null else -1.0


func tick(dt: float) -> void:
	"""gamemore._process during a round (every 0.25 s); counts once per second"""
	if not active() or game.round_state != "play":
		return
	_t += dt
	if _t < 1.0:
		return
	var secs := mini(5, int(_t))                           # a slow PC: the seconds since the last count
	_t -= float(int(_t))
	stat["secs"] = int(stat["secs"]) + secs
	var seen := []
	for p in game.players:
		if p != null and p["role"] == "runner" and p["state"] == "play" and game.cam_sees(p, 0) > 0.05:
			seen.append(p)
	var got := 0.0
	if mw_on():
		stat["est"] = false
		var bx: Array = main.mw_det.get("boxes", []) if typeof(main.mw_det.get("boxes", [])) == TYPE_ARRAY else []
		var n: int = maxi(bx.size(), int(main.mw_det.get("persons", 0)))
		got += BOX * n
		if n != _last_n:
			got += FLIP * absi(n - _last_n)
			stat["flips"] = int(stat["flips"]) + absi(n - _last_n)
		_last_n = n
		stat["boxes_max"] = maxi(int(stat["boxes_max"]), n)
		var c := _cpu()
		if c >= 0.0:
			stat["cpu_max"] = maxf(float(stat["cpu_max"]), c)
			if float(stat["cpu0"]) < 0.0:
				stat["cpu0"] = c
			got += minf(CPU_MAX, maxf(0.0, c - float(stat["cpu0"])) / CPU_STEP)
		if bool(main.mw_det.get("noise", false)):
			got += NOISE
	else:                                                  # the simulator's estimate: things moving in the picture
		stat["est"] = true
		var n2 := 0
		for p in seen:
			var f: float = game.cam_sees(p, 0)
			got += BOX * f + (FLIP * 0.5 if float(p["actor"].cur_speed) > 1.5 else 0.0)
			n2 += 1
		if n2 != _last_n:
			stat["flips"] = int(stat["flips"]) + absi(n2 - _last_n)
			got += FLIP * absi(n2 - _last_n) * 0.5
		_last_n = n2
		stat["boxes_max"] = maxi(int(stat["boxes_max"]), n2)
	if seen.is_empty() or got <= 0.0:
		return
	for p in seen:
		pts[int(p["slot"])] = float(pts.get(int(p["slot"]), 0.0)) + got * secs / seen.size()


func score(p: Dictionary, sc: int, info: String) -> Array:
	if not active() or p["role"] != "runner":
		return [sc, info]
	var s := int(round(float(pts.get(int(p["slot"]), 0.0))))
	var total: int = maxi(0, s - 150 * int(p.get("caught", 0)) + 100 * int(p.get("items", 0)))
	var head := T.t("🥵 MoveEye-Arbeit: %d", [s]) + (" (" + T.t("Simulator-Schätzung") + ")" if bool(stat["est"]) else "")
	return [total, head + " · " + T.t("%d× erwischt", [int(p.get("caught", 0))])]


func summary() -> String:
	if not active() and int(stat["secs"]) == 0:
		return ""
	var t := T.t("🥵 MoveEye: höchstens %d Personen gleichzeitig, %d× neue / verlorene Spur", [int(stat["boxes_max"]), int(stat["flips"])])
	if float(stat["cpu_max"]) >= 0.0:
		t += " · " + T.t("CPU bis %d %%", [int(stat["cpu_max"])])
	if bool(stat["est"]):
		t += " · " + T.t("(Simulator-Schätzung, MoveEye nicht verbunden)")
	return t


func state_for(p: Dictionary) -> Dictionary:
	if not active() or game.round_state != "play" or p["role"] != "runner":
		return {}
	return {"pts": int(round(float(pts.get(int(p["slot"]), 0.0)))), "est": bool(stat["est"]), "t": T.t("🥵 Schwitz-Punkte"),
			"seen": game.cam_sees(p, 0) > 0.05}


func debug() -> Dictionary:
	return {"active": active(), "mw": mw_on(), "pts": pts, "stat": stat}
