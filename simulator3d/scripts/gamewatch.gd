extends RefCounted
## 3D-4.x: the watchers take part. Who watches (all places to run are taken, or out of lives) guesses «Wer kommt durch?»
## at the start of a round (a right guess gives XP) and may throw two decoy stones: a tap into the picture of the head
## camera - the noise there draws the camera away and helps the runners.

var game
var main
const VOTE_SECS := 45.0                  # a guess is possible in the countdown and in the first 45 s
const STONES := 2                        # decoy stones per watcher and round
const STONE_WAIT := 10.0
var votes_res: Array = []               # after the round: [{"n", "c", "pick", "ok"}]


func now() -> float:
	return game.now()


func can_vote(p: Dictionary) -> bool:
	if not game.round_state in ["countdown", "play"]:
		return false
	if game.round_state == "play" and now() - game.t_start > VOTE_SECS:
		return false
	return p["role"] == "watch" or (p["role"] == "runner" and p["state"] in ["out", "found"]) or str(p.get("kind", "")) == "watcher"


func vote(p: Dictionary, slot: int) -> void:
	if not can_vote(p) or slot < 0 or slot >= game.players.size():
		return
	var q = game.players[slot]
	if q == null or q == p or q["role"] != "runner":
		return
	p["vote"] = slot
	game._say(p, "🔮 Dein Tipp: %s kommt durch" % q["name"], 3.0)


func stone(p: Dictionary, x: float, y: float) -> void:
	"""a decoy stone: x, y (0..1) = the spot in the picture of the head camera, the stone lands on the ground there"""
	if p["role"] != "watch" or game.round_state != "play":
		return
	if int(p.get("wst", 0)) >= STONES:
		game._say(p, "🪨 Keine Locksteine mehr in dieser Runde", 2.5)
		return
	if now() < float(p.get("wst_t", 0.0)):
		game._say(p, "🪨 Noch %d s warten" % int(ceil(float(p["wst_t"]) - now())), 2.0)
		return
	var cam: Camera3D = main.cams[0]
	var tf := tan(deg_to_rad(cam.fov) / 2.0)
	var asp := 16.0 / 9.0
	var dir: Vector3 = cam.global_transform.basis * Vector3((clampf(x, 0.0, 1.0) * 2.0 - 1.0) * tf * asp, -(clampf(y, 0.0, 1.0) * 2.0 - 1.0) * tf, -1.0)
	dir = dir.normalized()
	var o: Vector3 = cam.global_position
	if dir.y > -0.02:                                     # above the horizon: 25 m ahead
		dir.y = -0.02
		dir = dir.normalized()
	var to := o
	for k in range(1, 61):                               # walk along the ray until the ground
		var q: Vector3 = o + dir * (k * 0.75)
		to = q
		if q.y <= main.ground_y(q.x, q.z) + 0.05 or k * 0.75 > 45.0:
			break
	to = Vector3(to.x, 0, to.z)
	p["wst"] = int(p.get("wst", 0)) + 1
	p["wst_t"] = now() + STONE_WAIT
	game.stone_at(main.free_spot(to, 0.3, true))
	game.news("🪨 %s (Zuschauer) wirft einen Lockstein" % p["name"])
	game._say(p, "🪨 Lockstein geworfen – noch %d" % (STONES - int(p["wst"])), 2.5)
	for q in game.players:
		if q != null and q != p and q["role"] == "runner" and q["state"] == "play":
			game._say(q, "🪨 Ein Zuschauer lenkt die Kamera ab!", 2.0)


func round_start() -> void:
	votes_res.clear()
	for p in game.players:
		if p != null:
			p["vote"] = -1
			p["wst"] = 0
			p["wst_t"] = 0.0


func _through(q: Dictionary) -> bool:
	if game.flag_mode():
		return int(q.get("caps_n", 0)) > 0
	if main.game_mode == "seek":
		return q["state"] != "found"
	return float(q.get("t_goal", 0.0)) > 0.0 or q["state"] == "goal"


func round_end() -> Array:
	"""who guessed right; returns [[player, ok]] for the XP"""
	var out := []
	votes_res.clear()
	for p in game.players:
		if p == null or int(p.get("vote", -1)) < 0:
			continue
		var q = game.players[int(p["vote"])]
		if q == null:
			continue
		var ok := _through(q)
		votes_res.append({"n": p["name"], "c": "#" + game.COLORS[p["slot"]].to_html(false), "pick": q["name"], "ok": ok})
		out.append([p, ok])
	return out


func state_for(p: Dictionary) -> Dictionary:
	"""what the phone of a watcher needs: may he guess, whom, the decoy stones"""
	var d := {"vote_ok": can_vote(p), "vote": int(p.get("vote", -1)), "wst": STONES - int(p.get("wst", 0)) if p["role"] == "watch" else -1,
			"wst_wait": int(max(0.0, float(p.get("wst_t", 0.0)) - now()))}
	if d["vote_ok"]:
		var rs := []
		for q in game.players:
			if q != null and q != p and q["role"] == "runner":
				rs.append({"s": int(q["slot"]), "n": q["name"], "c": "#" + game.COLORS[q["slot"]].to_html(false)})
		d["vote_list"] = rs
	var tally := {}
	for q in game.players:
		if q != null and int(q.get("vote", -1)) >= 0:
			tally[str(q["vote"])] = int(tally.get(str(q["vote"]), 0)) + 1
	d["tally"] = tally
	if game.round_state == "end":
		d["votes_res"] = votes_res
	return d
