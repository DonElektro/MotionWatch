extends RefCounted
## 3D-4.x: the computer players, smarter: they use the bushes and stones, collect crystals on the way and adapt their skill
## after every round (a bot that won gets weaker, one that lost gets better). And the «Bot-Wächter»: with nobody as guard
## in the game type «Wächter», a bot turns the head and calls «Erwischt!» - so «Wächter» also works with two people.

var game
var main
var skill := {}                          # name of the bot -> skill 0.3 … 1.0 (kept for the evening)
var guard := {}                          # the bot guard of this round: {"name", "catches", "false", "who", "t", "skill", "slot"}
var _gt := 0.0
var _call_t := 0.0
var _fa_t := 0.0
const GUARD_NAME := "🤖 Bot-Wächter"


func skill_for(name_: String) -> float:
	if not skill.has(name_):
		skill[name_] = {"easy": 0.5, "normal": 0.75, "hard": 0.95}.get(main.game_level, 0.75)
	return float(skill[name_])


func now() -> float:
	return game.now()


# ---- the sneaking bots -------------------------------------------------------------------------------------------------
func tick(dt: float) -> void:
	for p in game.players:
		if p == null or str(p.get("kind", "")) != "bot":
			continue
		_bot(p, dt)


func _head_looks_at(pos: Vector3, deg: float) -> bool:
	var cam: Camera3D = main.cams[0]
	var fw: Vector3 = -cam.global_transform.basis.z
	var to: Vector3 = pos - cam.global_position
	var a := rad_to_deg(abs(wrapf(atan2(-to.x, -to.z) - atan2(-fw.x, -fw.z), -PI, PI)))
	return a < deg


func _bot(p: Dictionary, dt: float) -> void:
	var a = p["actor"]
	var hiding: bool = game.seek_hiding() and p["state"] == "play"
	if p["role"] != "runner" or p["state"] != "play" or (game.round_state != "play" and not hiding):
		p["mx"] = 0.0
		p["my"] = 0.0
		return
	var B: Dictionary = p["bot"]
	var sk: float = float(B["skill"])
	var t := now()
	var tgt: Vector3 = game._target_of(p)
	if main.game_mode == "seek":                       # 3D-3.78: first hide somewhere, wait, then sneak to the base
		if not B.has("hide"):
			var ang := randf() * TAU
			B["hide"] = main.free_spot(game.seek_base + Vector3(cos(ang), 0, sin(ang)) * randf_range(14.0, 26.0), 0.6, true)
			B["go_t"] = game.t_start + randf_range(25.0, 90.0)
		if hiding or t < float(B["go_t"]):
			tgt = B["hide"]
			if a.position.distance_to(tgt) < 1.5:
				p["my"] = 0.0
				a.ctl_posture = 1 if hiding else 2
				return
	var vis: float = game.visibility(p)
	var d_head: float = a.position.distance_to(main.cams[0].global_position)
	var susp: float = float(p["susp"])
	var looked: bool = _head_looks_at(a.position, 30.0) and d_head < 35.0
	# ---- in a bush: stay while the camera looks this way (a hiding place lasts 8 s) ----
	if int(p.get("hide_i", -1)) >= 0:
		var left: float = game.HIDE_MAX - (t - float(p["hide_t0"]))
		if (looked or susp > 20.0) and left > 1.5:
			p["my"] = 0.0
			a.ctl_posture = 2
			return
	# ---- 3D-4.x: where to go now - a crystal close by, a bush when it gets dangerous, else the goal ----
	if t > float(B.get("plan_t", 0.0)):
		B["plan_t"] = t + 1.2
		B["way"] = null
		var best := 1e9
		if (susp > 30.0 * sk + 10.0 or (looked and vis > 0.15)) and not game.hides.is_empty():
			for i in range(game.hides.size()):
				var hp: Vector3 = game.hides[i]["pos"]
				var dd: float = a.position.distance_to(hp)
				if dd < 9.0 and dd < best and t > float(p["hide_cd"].get(i, 0.0)):
					best = dd
					B["way"] = hp
					B["way_k"] = "bush"
		if B["way"] == null and int(main.game_items) > 0 and sk > 0.35:
			var to_goal: float = a.position.distance_to(tgt)
			for it in game.items:
				if int(it["by"]) >= 0:
					continue
				var ip: Vector3 = it["pos"]
				var detour: float = a.position.distance_to(ip) + ip.distance_to(tgt) - to_goal
				if a.position.distance_to(ip) < 16.0 and detour < 9.0 * sk + 3.0 and detour < best:
					best = detour
					B["way"] = ip
					B["way_k"] = "item"
	if B.get("way") != null:
		tgt = B["way"]
		if a.position.distance_to(tgt) < 0.8:
			if str(B.get("way_k", "")) == "bush":
				a.ctl_posture = 2                              # into the bush: lie down
				p["my"] = 0.0
				B["way"] = null
				return
			B["way"] = null
	var to: Vector3 = tgt - a.position
	var want := atan2(-to.x, -to.z)
	var ahead := Vector2(a.position.x, a.position.z) + Vector2(-sin(float(p["yaw"])), -cos(float(p["yaw"]))) * 1.6
	if main.blocked(ahead, 0.5, true) and t > float(B["turn_t"]):
		B["turn"] = deg_to_rad(55.0) * (1.0 if randf() < 0.5 else -1.0)      # an object in the way: round it
		B["turn_t"] = t + 1.6
	if t < float(B["turn_t"]):
		want += float(B["turn"])
	# ---- 3D-4.x: a stone to the side when the camera looks this way ----
	if main.game_stones and float(p["stone_t"]) <= t and looked and d_head < 32.0 and (susp > 25.0 or vis > 0.3) and randf() < sk * dt * 0.8:
		var y0: float = p["yaw"]
		p["yaw"] = y0 + deg_to_rad(110.0) * (1.0 if randf() < 0.5 else -1.0)
		game._throw(p)
		p["yaw"] = y0
	p["yaw"] = lerp_angle(float(p["yaw"]), want, clampf(dt * 3.0, 0.0, 1.0))
	if hiding:                                         # 3D-3.78: hiding time - run to the hiding place
		a.ctl_posture = 0
		a.ctl_run = true
		p["my"] = -1.0
		p["mx"] = 0.0
		return
	if t < float(B["hold"]):                               # frozen: wait until the camera looks away
		p["my"] = 0.0
		a.ctl_posture = 2
		return
	if (susp > 55.0 * sk or vis > 0.6) and randf() < sk:
		B["hold"] = t + randf_range(1.0, 3.5) * sk
		p["my"] = 0.0
		a.ctl_posture = 2
		return
	if susp > 25.0 or (vis > 0.25 and d_head < 25.0):
		a.ctl_posture = 2 if susp > 40.0 else 1
		p["my"] = -0.8
	elif d_head < 14.0 * sk or (looked and d_head < 22.0):
		a.ctl_posture = 1
		p["my"] = -0.9
	else:
		a.ctl_posture = 0
		p["my"] = -1.0
	a.ctl_run = a.ctl_posture == 0 and d_head > 28.0 and vis < 0.05 and not looked and randf() < 0.3
	p["mx"] = 0.0


func round_end(results: Array) -> Array:
	"""after the round every bot adapts: the best sneaker becomes weaker, a weak one better. Returns the changes [name, old, new]."""
	var humans := []
	var bots := []
	for p in game.players:
		if p == null or p["role"] != "runner":
			continue
		var sc := 0
		for r in results:
			if r["n"] == p["name"]:
				sc = int(r["score"])
		if str(p.get("kind", "")) == "bot":
			bots.append([p, sc])
		else:
			humans.append(sc)
	var out := []
	if humans.is_empty():
		return out
	var hb := 0
	for h in humans:
		hb = max(hb, int(h))
	var avg := 0.0
	for h in humans:
		avg += float(h)
	avg /= float(humans.size())
	for b in bots:
		var p: Dictionary = b[0]
		var old := skill_for(str(p["name"]))
		var nw := old
		if int(b[1]) > hb:                                # beat every person: a bit weaker next time
			nw = old - 0.1
		elif float(b[1]) < avg * 0.6 or int(p["caught"]) >= 2:
			nw = old + 0.07
		nw = clampf(nw, 0.3, 1.0)
		if absf(nw - old) > 0.001:
			skill[str(p["name"])] = nw
			p["bot"]["skill"] = nw
			out.append([str(p["name"]), snappedf(old, 0.01), snappedf(nw, 0.01)])
	if not guard.is_empty():                              # the bot guard: catches everybody - weaker, catches nobody - better
		var n: int = max(1, int(guard.get("runners", 1)))
		var share: float = float(guard["who"].size()) / float(n)
		var old2 := skill_for(GUARD_NAME)
		var nw2 := clampf(old2 + (-0.1 if share > 0.6 else (0.08 if share < 0.2 else 0.0)), 0.3, 1.0)
		if absf(nw2 - old2) > 0.001:
			skill[GUARD_NAME] = nw2
			out.append([GUARD_NAME, snappedf(old2, 0.01), snappedf(nw2, 0.01)])
	return out


# ---- the bot guard -------------------------------------------------------------------------------------------------------
func guard_on() -> bool:
	"""«Wächter» without a person as guard: the bot guards (if switched on)"""
	return main.game_mode == "guard" and main.game_botguard and game.guard_player() == null


func guard_start(runners: int) -> void:
	guard = {}
	if not guard_on():
		return
	guard = {"name": GUARD_NAME, "catches": 0, "false": 0, "who": {}, "t": 0.0, "skill": skill_for(GUARD_NAME), "runners": runners}
	_call_t = now() + 3.0
	game.news("🤖 Der Bot-Wächter passt auf (Stärke %d %%)" % int(float(guard["skill"]) * 100.0))


func guard_drive(dt: float) -> void:
	"""the head: swings, looks at noises, follows the one it suspects most (faster the better the bot)"""
	var sk: float = float(guard.get("skill", 0.75))
	game.guard_auto = true
	game.guard_tilt = deg_to_rad(-9.0)
	var want: float = 1.05 * sin(now() * (0.25 + 0.15 * sk))
	if now() < game.attention_until:
		want = atan2(-game.attention.x, -game.attention.z)
	var top := 30.0
	for p in game.players:
		if p != null and p["state"] == "play" and p["role"] == "runner" and float(p["susp"]) > top:
			top = float(p["susp"])
			var d: Vector3 = p["actor"].position
			want = atan2(-d.x, -d.z)
	game.guard_yaw = lerp_angle(game.guard_yaw, want, clampf(dt * (1.5 + 3.0 * sk), 0.0, 1.0))


func guard_tick() -> void:
	"""every 0.2 s: «Erwischt!» when somebody is clearly seen; now and then a false alarm after a noise"""
	if guard.is_empty() or game.round_state != "play":
		return
	var t := now()
	if t < _call_t:
		return
	var sk: float = float(guard["skill"])
	var thr: float = 88.0 - 30.0 * sk                   # a good bot calls earlier
	var hit = null
	var best := 0.0
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or t < float(p["safe_until"]):
			continue
		var f: float = game.cam_sees(p, 0)
		if float(p["susp"]) >= thr and f > 0.02 and float(p["susp"]) > best:
			best = float(p["susp"])
			hit = p
	if hit != null:
		_call_t = t + 2.5
		game._say(hit, "🤖 Der Bot-Wächter hat dich erwischt!", 3.0)
		game._caught(hit, guard)
		return
	if t < game.attention_until and t > _fa_t and randf() < (1.0 - sk) * 0.04:   # fooled by a stone
		_fa_t = t + 6.0
		_call_t = t + 4.0
		guard["false"] = int(guard["false"]) + 1
		game.news("❌ Bot-Wächter: Fehlalarm (ein Stein hat ihn getäuscht)")
