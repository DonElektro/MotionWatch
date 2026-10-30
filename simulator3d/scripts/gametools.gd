extends Node
## 3D-4.x «Wächter-Werkzeuge mit Kosten» (Spielkonzept Daniel, 30.10.2026): the guard has a budget of energy per round
## (by the difficulty: easy 70, normal 100, hard 130 - the fairness of gamerules.gd may change it) and every tool has a
## price and a cooldown:
##   💡 Licht   20 ⚡, 20 s   the light of the head for 6 s (the former «Licht» button with its 20 s)
##   📢 Sirene  30 ⚡, 25 s   4 s: whoever moves now is noticed much faster (the siren sound of gameshutter.gd)
##   📡 Scan    25 ⚡, 15 s   4 s: hint markers where runners are within 30 m of the head (not in a bush)
##   🔍 Zoom    15 ⚡, 10 s   8 s: the head camera zooms in (narrower picture, people look bigger - also for MoveEye)
##   🎯 Auslöser 8 ⚡ a shot, +10 ⚡ more for a miss (gameshutter.gd)
## The energy comes back slowly (0.4 per second). Who uses it: the guard at the phone (game.gd page, message «tool»), at the
## PC (localplay.gd: G V N Z, controller B Y X LB) and the guards at MoveEye in «Team gegen MoveEye» (key «mw»: controls
## game_tool_* through CONTROL «press», part 543 of MoveEye shows the gauges and buttons on the live page).
## The hint markers (also from loud runners, gamerules.gd) are shown on the picture of the guard (phone, PC, MoveEye).
## With «Werkzeuge mit Energie» off (wizard) the old way stays: only the light, 20 s cooldown, no costs.

var game
var main

const TOOLS := [["light", "💡", "Licht", 20, 20.0], ["siren", "📢", "Sirene", 30, 25.0], ["scan", "📡", "Scan", 25, 15.0],
		["zoom", "🔍", "Zoom", 15, 10.0], ["shut", "🎯", "Auslöser", 8, 0.0]]
const MAX := {"easy": 70.0, "normal": 100.0, "hard": 130.0}
const REGEN := 0.4                       # energy per second
const MISS_EXTRA := 10                   # a missed shot costs more
const SIREN_S := 4.0
const SCAN_S := 4.0
const ZOOM_S := 8.0
const ZOOM_K := 0.55                     # the field of view while zoomed (× the normal one)
const SCAN_R := 30.0

var st := {}                             # key ("mw" or "p<slot>") -> {"e", "max", "cd": {tool: time free again}, "used": {tool: n}}
var siren_until := 0.0
var zoom_until := 0.0
var _fov0 := -1.0
var hints: Array = []                    # {"pos": Vector3, "k": "noise" | "scan", "t": until, "slot": int}
var _t := 0.0
var last := {}                           # the last answer for the guards at MoveEye (they press through CONTROL «press»)


func now() -> float:
	return game.now()


func on() -> bool:
	return game.rules == null or game.rules.tools_on


func _tool(id: String) -> Array:
	for t in TOOLS:
		if t[0] == id:
			return t
	return []


func key(g) -> String:
	return "mw" if g == null else "p%d" % int(g["slot"])


func _s(k: String) -> Dictionary:
	if not st.has(k):
		var mx: float = float(MAX.get(main.game_level, 100.0)) * (game.rules.energy_mul() if game.rules != null else 1.0)
		st[k] = {"e": mx, "max": mx, "cd": {}, "used": {}}
	return st[k]


# ---- round --------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	st.clear()
	hints.clear()
	siren_until = 0.0
	_zoom_off()


func round_end() -> void:
	siren_until = 0.0
	_zoom_off()


func _process(dt: float) -> void:
	if game == null or not game.open:
		return
	if game.round_state == "play":
		for k in st:
			var s: Dictionary = st[k]
			s["e"] = minf(float(s["max"]), float(s["e"]) + REGEN * dt)
	if zoom_until > 0.0 and now() >= zoom_until:
		_zoom_off()
	_t -= dt
	if _t <= 0.0:
		_t = 0.5
		var t := now()
		hints = hints.filter(func(h): return float(h["t"]) > t)


# ---- using a tool ---------------------------------------------------------------------------------------------------------
func check(g, id: String) -> String:
	"""'' = the tool can be used now, else why not"""
	var T := _tool(id)
	if T.is_empty():
		return "Unbekanntes Werkzeug"
	if game.round_state != "play":
		return "Nur während einer Runde"
	if not on():
		return ""
	var s := _s(key(g))
	var left: float = float(s["cd"].get(id, 0.0)) - now()
	if left > 0.0:
		return "%s lädt noch %d s" % [T[2], int(ceil(left))]
	if float(s["e"]) < float(T[3]):
		return "Zu wenig Energie für %s (%d ⚡ nötig)" % [T[2], int(T[3])]
	return ""


func _pay(g, id: String) -> void:
	if not on():
		return
	var T := _tool(id)
	var s := _s(key(g))
	s["e"] = maxf(0.0, float(s["e"]) - float(T[3]))
	if float(T[4]) > 0.0:
		s["cd"][id] = now() + float(T[4])
	s["used"][id] = int(s["used"].get(id, 0)) + 1


func pay_shot(g) -> String:
	"""gameshutter.fire: the price of a shot ('' = paid, else the reason it does not go)"""
	if not on() or game.round_state != "play":
		return ""
	var e := check(g, "shut")
	if e != "":
		return e
	_pay(g, "shut")
	return ""


func miss(g) -> void:
	"""a missed shot costs a bit more"""
	if on() and st.has(key(g)):
		var s: Dictionary = st[key(g)]
		s["e"] = maxf(0.0, float(s["e"]) - MISS_EXTRA)


func use(g, id: String, who := "") -> Dictionary:
	"""a guard (phone / PC: its player, null = the guards at MoveEye) uses a tool"""
	if g == null and game.shut.human_mode() != "mw":
		return {"ok": false, "error": "Die Werkzeuge an MoveEye gibt es nur in «Team gegen MoveEye»."}
	if g != null and str(g.get("role", "")) != "guard":
		return {"ok": false, "error": "Nur der Wächter hat Werkzeuge."}
	if id == "light" and not on():                     # the old way: only the light, 20 s
		if now() < float(game.light_ready):
			return {"ok": false, "error": "Licht lädt noch %d s" % int(ceil(float(game.light_ready) - now()))}
		game.light_ready = now() + game.LIGHT_EVERY
		game.flash_until = now() + 6.0
		return {"ok": true, "text": "💡 Licht an"}
	var err := check(g, id)
	if err != "":
		if g != null:
			game._say(g, "⏳ " + err, 2.0)
		else:
			last = {"t": now(), "text": "⏳ " + err}
		return {"ok": false, "error": err}
	var by: String = who if who != "" else ("MoveEye" if g == null else str(g["name"]))
	var txt := ""
	match id:
		"light":
			game.flash_until = now() + 6.0
			game.light_ready = now() + float(_tool("light")[4])
			txt = "💡 Licht an (6 s)"
		"siren":
			siren_until = now() + SIREN_S
			if game.shut != null and game.shut._siren != null:
				game.shut._siren.play()
			main.add_sound(-4.0, main.cams[0].global_position, SIREN_S)
			for q in game.players:
				if q != null and q["role"] == "runner" and q["state"] == "play":
					game._say(q, "📢 Sirene! Wer sich jetzt bewegt, fällt auf – stillhalten!", SIREN_S)
			txt = "📢 Sirene (4 s): wer sich bewegt, fällt auf"
		"scan":
			var n := 0
			var hp: Vector3 = main.cams[0].global_position
			for q in game.players:
				if q == null or q["role"] != "runner" or q["state"] != "play" or int(q.get("hide_i", -1)) >= 0:
					continue
				var pos: Vector3 = q["actor"].position
				if Vector2(pos.x - hp.x, pos.z - hp.z).length() <= SCAN_R:
					add_hint(pos, "scan", SCAN_S, int(q["slot"]))
					n += 1
					game._say(q, "📡 Der Wächter scannt – er weiss ungefähr, wo du bist!", 2.5)
			txt = "📡 Scan: %s in der Nähe" % ("niemand" if n == 0 else ("1 Schleicher" if n == 1 else "%d Schleicher" % n))
		"zoom":
			if _fov0 < 0.0:
				_fov0 = main.cams[0].fov
			main.cams[0].fov = _fov0 * ZOOM_K
			zoom_until = now() + ZOOM_S
			txt = "🔍 Zoom (8 s): Leute wirken grösser, das Bild ist enger"
		_:
			return {"ok": false, "error": "Unbekanntes Werkzeug"}
	_pay(g, id)
	game.news("%s – %s" % [txt, by])
	if g != null:
		game._say(g, txt, 2.5)
	else:
		last = {"t": now(), "text": txt}
	return {"ok": true, "text": txt, "tool": id}


func _zoom_off() -> void:
	zoom_until = 0.0
	if _fov0 > 0.0 and main != null and main.cams.size() > 0:
		main.cams[0].fov = _fov0
	_fov0 = -1.0


# ---- effects for the referee of game.gd -------------------------------------------------------------------------------------
func zoom_k(i: int) -> float:
	"""cam_sees: with the zoom a person is bigger in the picture of the head camera"""
	return 1.0 / ZOOM_K if i == 0 and zoom_until > now() else 1.0


func extra_rate(p: Dictionary) -> float:
	"""the siren: whoever moves while it sounds gets noticed fast (per second, like the rate of the meter)"""
	if siren_until <= now():
		return 0.0
	var a = p["actor"]
	if float(a.cur_speed) < 0.35 or a.position.distance_to(main.cams[0].global_position) > 40.0:
		return 0.0
	return 22.0 + 18.0 * clampf(float(a.cur_speed) / 3.0, 0.0, 1.0)


# ---- hint markers on the picture of the guard ---------------------------------------------------------------------------
func add_hint(pos: Vector3, k: String, secs := 3.0, slot := -1) -> void:
	for h in hints:                                    # one marker per runner and kind (renewed)
		if int(h["slot"]) == slot and slot >= 0 and str(h["k"]) == k:
			h["pos"] = pos
			h["t"] = now() + secs
			return
	hints.append({"pos": pos, "k": k, "t": now() + secs, "slot": slot})
	if hints.size() > 24:
		hints.pop_front()


func hints_for(cam_i: int) -> Array:
	"""[[x 0..1 in the picture (clamped to the edge), kind, distance m, at the edge]] for the camera the guard looks through"""
	var out := []
	var cam: Camera3D = main.cams[clampi(cam_i, 0, 1)]
	var fw: Vector3 = -cam.global_transform.basis.z
	var vs := Vector2(main.vps[clampi(cam_i, 0, 1)].size)
	var hf: float = 2.0 * atan(tan(deg_to_rad(cam.fov) / 2.0) * vs.x / maxf(1.0, vs.y)) if cam.keep_aspect == Camera3D.KEEP_HEIGHT else deg_to_rad(cam.fov)
	var t := now()
	for h in hints:
		if float(h["t"]) <= t:
			continue
		var to: Vector3 = (h["pos"] as Vector3) - cam.global_position
		var rel := wrapf(atan2(-to.x, -to.z) - atan2(-fw.x, -fw.z), -PI, PI)      # > 0 = left
		var x := 0.5 - rel / maxf(0.2, hf)
		var edge := x < 0.03 or x > 0.97
		out.append([snappedf(clampf(x, 0.03, 0.97), 0.001), str(h["k"]), int(round(Vector2(to.x, to.z).length())), edge])
	return out


# ---- what the screens show -------------------------------------------------------------------------------------------------
func info_for(g) -> Dictionary:
	"""the gauges of a guard: energy and every tool (id, icon, name, price, seconds left, usable)"""
	var playing: bool = game.round_state == "play"
	if not on():
		var l := maxf(0.0, float(game.light_ready) - now())
		return {"on": false, "t": [["light", "💡", "Licht", 0, int(ceil(l)), l <= 0.0]]}
	var s := _s(key(g)) if playing else {"e": float(MAX.get(main.game_level, 100.0)) * (game.rules.energy_mul() if game.rules != null else 1.0), "cd": {}}
	if not s.has("max"):
		s["max"] = s["e"]
	var ts := []
	for T in TOOLS:
		if T[0] == "shut" and not game.shut.active():
			continue
		var left := maxf(0.0, float(s["cd"].get(T[0], 0.0)) - now())
		ts.append([T[0], T[1], T[2], int(T[3]), int(ceil(left)), playing and left <= 0.0 and float(s["e"]) >= float(T[3])])
	var cam: int = 0 if g == null else game.guard_cam(g)
	var o := {"on": true, "e": int(floor(float(s["e"]))), "max": int(s["max"]), "t": ts, "siren": siren_until > now(), "zoom": zoom_until > now(),
			"hints": hints_for(cam) if playing else []}
	if g == null and not last.is_empty() and now() - float(last["t"]) < 4.0:
		o["msg"] = last["text"]
	return o


func hud_text(g) -> String:
	"""one line for the PC guard (localplay.gd): energy as a little bar, the tools that wait"""
	var I := info_for(g)
	if not bool(I["on"]):
		var l: int = int(I["t"][0][4])
		return "Licht " + ("bereit" if l <= 0 else "%d s" % l)
	var f := clampf(float(I["e"]) / maxf(1.0, float(I["max"])), 0.0, 1.0)
	var n := int(round(f * 10.0))
	var o := "Energie [" + "■".repeat(n) + "□".repeat(10 - n) + "] %d" % int(I["e"])
	for t in I["t"]:
		if t[0] == "shut":
			continue
		o += " · %s %s" % [t[2], "bereit" if bool(t[5]) else ("%d s" % int(t[4]) if int(t[4]) > 0 else "–")]
	return o


func debug() -> Dictionary:
	var o := {}
	for k in st:
		o[k] = {"e": snappedf(float(st[k]["e"]), 0.1), "max": st[k]["max"], "used": st[k]["used"]}
	return {"on": on(), "st": o, "siren": siren_until > now(), "zoom": zoom_until > now(), "fov": snappedf(main.cams[0].fov, 0.1), "hints": hints.size()}


func command(d: Dictionary) -> Dictionary:
	"""CONTROL «game_tool» (tests, MoveEye): {tool, slot (-1 = the guards at MoveEye), who} or {op: "info"}"""
	if str(d.get("op", "")) == "info":
		var r := debug()
		r["ok"] = true
		return r
	var sl := int(d.get("slot", -1))
	var g = null
	if sl >= 0 and sl < game.players.size():
		g = game.players[sl]
		if g == null:
			return {"ok": false, "error": "no player"}
	return use(g, str(d.get("tool", "")), str(d.get("who", "")).left(30))
