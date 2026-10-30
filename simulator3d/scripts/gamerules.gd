extends Node
## 3D-4.x Spielkonzept (Daniel, 30.10.2026) - the rules around a round, here so game.gd stays small:
##   «Rollen wechseln reihum»: after a round with a guard (Wächter-Duell, Verstecken) another person becomes the guard -
##     in turn (by the place) or «wer am wenigsten erwischt wurde»; shown before the next round (phones, window, MoveEye).
##   «Fairness nach Rollen-Verhältnis»: many sneakers against one guard -> the guard gets 50 % more energy (gametools.gd)
##     and a 🤖 Bot-Helfer at the fixed camera (the AI: a bit more watchful); few sneakers -> 2 hiding places more, a bush
##     hides 12 s instead of 8 s (and the guard has a bit less energy). Automatic, explained in one line. The handicap for the
##     leader of the ranking (game._auto_handicap) stays as it is.
##   «Infos für Schleicher»: the phone vibrates when the head camera looks their way (in its view cone), a noise meter
##     (running = loud = a hint marker for the guard / the AI looks there), shadows as hiding places (by day the shadow of
##     an object - a ray towards the sun - halves the light the cameras get: game.light_at).
##   «Siegerbild»: at the end the winner, the closest moment (highest suspicion without being caught) as a short replay
##     (the recording of game.gd, «Knappster Moment»), the ranking of the evening (game.board: from the same day,
##     «Rangliste zurücksetzen» in the wizard) - on the phones and here in the window.
## The settings come from the wizard (gamewiz.gd OPTIONS, like gameplus.gd: kept in user://spiel/regeln.json).

var game
var main

const CFG_FILE := "user://spiel/regeln.json"
const UI = preload("res://scripts/ui_style.gd")
const ROT_OPTS := [["off", "aus – jeder wählt selbst"], ["turn", "der Reihe nach"], ["best", "wer am wenigsten erwischt wurde"]]
const HELPER_NAME := "🤖 Bot-Helfer"

var rotate := "turn"                     # off | turn | best
var tools_on := true                     # gametools.gd: energy and cooldowns
var fair_on := true
var vibe_on := true                      # vibration and noise meter on the phone
var shade_on := true
var seq := 0

var fair := {}                           # this round: {"runners", "guards", "kind", "text", "e_mul", "hides", "hide_s", "rate", "helper"}
var next_txt := ""                       # «Nächste Runde: Anna ist Wächter»
var _last_slot := -1
var helper := {}                         # the bot helper at the fixed camera: {"name", "catches", "false", "who"}
var _help_t := 0.0
var _tick := 0.0
var _smp := 0.0
var _noise_t := {}
var _shade := {}
var samples: Array = []                  # [t, slot, susp] every 0.5 s of the round
var win := {}                            # the winner screen of the last round

# the winner screen in this window
var layer: CanvasLayer
var panel: PanelContainer
var box: VBoxContainer
var mapc: Control
var _win_until := 0.0
var _hl_t := 0.0


func now() -> float:
	return game.now()


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(CFG_FILE)) if FileAccess.file_exists(CFG_FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		_take(d)
	layer = CanvasLayer.new()
	layer.layer = 29                                   # under the game at the PC (localplay, 30), over the panel
	add_child(layer)
	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.1, 0.95), Color(1.0, 0.8, 0.3), 16, 16, 2))
	panel.visible = false
	layer.add_child(panel)
	box = VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	panel.add_child(box)


# ---- the settings of the wizard -----------------------------------------------------------------------------------------
func cfg_get() -> Dictionary:
	return {"game_rotate": rotate, "game_tools": tools_on, "game_fair": fair_on, "game_vibe": vibe_on, "game_shade": shade_on}


func _take(d: Dictionary) -> void:
	if d.has("game_rotate"):
		rotate = str(d["game_rotate"]) if str(d["game_rotate"]) in ["off", "turn", "best"] else "turn"
	for k in [["game_tools", "tools_on"], ["game_fair", "fair_on"], ["game_vibe", "vibe_on"], ["game_shade", "shade_on"]]:
		if d.has(k[0]):
			set(k[1], bool(d[k[0]]))


func cfg_set(d: Dictionary) -> void:
	_take(d)
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(CFG_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(cfg_get()))
	seq += 1


# ---- fairness by the ratio of the roles --------------------------------------------------------------------------------------
func _guard_name() -> String:
	if game.guard_player() != null:
		return "1 Wächter"
	if main.game_mode == "guard" and main.game_botguard:
		return "den Bot-Wächter"
	if main.game_mode in ["mw", "patrol"] and game.mw_decides():
		return "MoveEye"
	return "die Kamera"


func calc() -> Dictionary:
	"""what the fairness does with the players there now (also the preview of the wizard)"""
	var runners := 0
	var humans := 0
	for p in game.players:
		if p == null:
			continue
		if p["role"] == "runner":
			runners += 1
		elif p["role"] == "guard":
			humans += 1
	var f := {"runners": runners, "guards": max(1, humans), "kind": "", "text": "", "e_mul": 1.0, "hides": 0, "hide_s": 0.0, "rate": 1.0, "helper": false}
	if not fair_on or main.game_mode in ["free", "jaeger", "mwhand", "teamguard"] or runners == 0 or main.game_goal == "flag":
		return f
	var gs: int = max(1, humans)
	var r := float(runners) / float(gs)
	var who := ("%d Wächter" % humans) if humans > 1 else _guard_name()
	if r >= 4.0:
		f["kind"] = "guard"
		if humans > 0:
			f["e_mul"] = 1.5
			f["helper"] = humans == 1 and main.game_mode == "guard"
			f["text"] = "⚖ %d Schleicher gegen %s: der Wächter hat 50 %% mehr Energie%s." % [runners, who, " und einen 🤖 Bot-Helfer an der festen Kamera" if f["helper"] else ""]
		else:
			f["rate"] = 1.15
			f["text"] = "⚖ %d Schleicher gegen %s: die Kamera passt etwas besser auf." % [runners, who]
	elif r <= 1.0:
		f["kind"] = "sneak"
		f["hides"] = 2
		f["hide_s"] = 4.0
		if humans > 0:
			f["e_mul"] = 0.8
		f["text"] = "⚖ %d Schleicher gegen %s: 2 Verstecke mehr, ein Busch versteckt 12 s statt 8 s%s." % [runners, who, ", der Wächter hat etwas weniger Energie" if humans > 0 else ""]
	else:
		f["text"] = "⚖ %d Schleicher gegen %s: ausgeglichen." % [runners, who]
	return f


func plan() -> void:
	"""game.start_round, before the hiding places are put down"""
	fair = calc()


func energy_mul() -> float:
	return float(fair.get("e_mul", 1.0))


func extra_hides() -> int:
	return int(fair.get("hides", 0))


func hide_bonus() -> float:
	return float(fair.get("hide_s", 0.0))


func rate_mul() -> float:
	return float(fair.get("rate", 1.0))


# ---- round ----------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	samples.clear()
	win = {}
	next_txt = ""
	_noise_t.clear()
	_shade.clear()
	_hide_win()
	helper = {}
	if bool(fair.get("helper", false)):
		helper = {"name": HELPER_NAME, "catches": 0, "false": 0, "who": {}}
		_help_t = now() + 6.0
	if str(fair.get("text", "")) != "":
		game.news(str(fair["text"]))
		for q in game.players:
			if q != null:
				game._say(q, str(fair["text"]), 4.0)
	game.tools.round_start()
	seq += 1


func _process(dt: float) -> void:
	if game == null or not game.open:
		if panel != null and panel.visible:
			_hide_win()
		return
	if panel.visible:
		_hl_t += dt
		if mapc != null:
			mapc.queue_redraw()
		var vs := panel.get_viewport_rect().size
		panel.size = panel.get_combined_minimum_size()     # (the old lines are gone one frame later - shrink again)
		panel.position = Vector2((vs.x - panel.size.x) / 2.0, maxf(20.0, vs.y - panel.size.y - 30.0))
		if now() > _win_until or game.round_state in ["countdown", "play"] or (main.localplay != null and main.localplay.active):
			_hide_win()
	if game.round_state != "play":
		return
	_tick -= dt
	if _tick > 0.0:
		return
	_tick = 0.25
	var t := now()
	var rec := t - _smp >= 0.5
	if rec:
		_smp = t
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play":
			continue
		if rec and t >= float(p["safe_until"]):
			samples.append([snappedf(t - game.t_start, 0.1), int(p["slot"]), int(p["susp"])])
		if noise(p) >= 0.55 and t >= float(_noise_t.get(p["slot"], 0.0)):   # running: a hint marker, the AI looks there
			_noise_t[p["slot"]] = t + 1.2
			game.tools.add_hint(p["actor"].position, "noise", 2.5, int(p["slot"]))
			game.attention = p["actor"].position
			game.attention_until = t + 2.5
	if samples.size() > 4000:
		samples = samples.slice(samples.size() - 4000)
	_helper_tick(t)


func _helper_tick(t: float) -> void:
	"""the bot helper at the fixed camera: calls «Erwischt!» when somebody is clearly seen there"""
	if helper.is_empty() or t < _help_t:
		return
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or t < float(p["safe_until"]):
			continue
		if float(p["susp"]) >= 80.0 and game.cam_sees(p, 1) > 0.12:
			_help_t = t + 4.0
			game._say(p, "🤖 Der Bot-Helfer an der festen Kamera hat dich erwischt!", 3.0)
			game._caught(p, helper)
			return


# ---- infos for the sneakers ------------------------------------------------------------------------------------------------------
func noise(p: Dictionary) -> float:
	"""how loud the steps are (0 still … 1 running), like game.hearing but without the distance"""
	var a = p["actor"]
	var spd: float = a.cur_speed
	if spd < 0.2:
		return 0.0
	return clampf(game.LOUD[a.ctl_posture] * (3.3 if spd > 2.2 else 1.0) * game.plus.loud_mul(p), 0.0, 1.0)


func looks_at(p: Dictionary) -> bool:
	"""the head camera looks this way (the player is in its view cone, near enough) - not whether it really sees him"""
	var cam: Camera3D = main.cams[0]
	var pos: Vector3 = p["actor"].position
	var to: Vector3 = pos - cam.global_position
	if Vector2(to.x, to.z).length() > 45.0:
		return false
	var fw: Vector3 = -cam.global_transform.basis.z
	var vs := Vector2(main.vps[0].size)
	var hf: float = 2.0 * atan(tan(deg_to_rad(cam.fov) / 2.0) * vs.x / maxf(1.0, vs.y))
	return absf(wrapf(atan2(-to.x, -to.z) - atan2(-fw.x, -fw.z), -PI, PI)) < hf / 2.0 + 0.05


func shade_mul(pos: Vector3) -> float:
	"""game.light_at by day: in the shadow of an object (towards the sun) the cameras get half the light"""
	if not shade_on or game.round_state != "play" or main.is_dark() or main.sun == null or float(main.sun.light_energy) < 0.25:
		return 1.0
	var k := "%d,%d" % [int(round(pos.x * 2.0)), int(round(pos.z * 2.0))]
	var c = _shade.get(k)
	var t := now()
	if c != null and t - float(c[0]) < 0.6:
		return float(c[1])
	var dir: Vector3 = main.sun.global_transform.basis.z.normalized()      # towards the sun
	var m := 1.0
	if dir.y > 0.05:
		var a := pos + Vector3(0, 1.0, 0)
		if not main.line_free(a, a + dir * 30.0):
			m = 0.5
	_shade[k] = [t, m]
	if _shade.size() > 600:
		_shade.clear()
	return m


func sneak_info(p: Dictionary) -> Dictionary:
	if p["role"] != "runner" or p["state"] != "play" or game.round_state != "play":
		return {}
	var d := {"nz": snappedf(noise(p), 0.01), "sh": shade_mul(p["actor"].position) < 1.0}
	if vibe_on:
		d["lk"] = looks_at(p)
	return d


# ---- end of the round: rotation, winner, closest moment ----------------------------------------------------------------------
func round_end() -> void:
	game.tools.round_end()
	if not helper.is_empty():
		game.results.append({"n": HELPER_NAME, "c": "#9aa7b8", "info": "Bot-Helfer an der festen Kamera · %d× erwischt" % int(helper["catches"]), "score": 0})
	helper = {}
	_make_win()
	_rotate()
	win["next"] = next_txt
	seq += 1
	_show_win()


func _make_win() -> void:
	var top = null
	for r in game.results:
		if str(r.get("n", "")) != HELPER_NAME:
			top = r
			break
	win = {}
	if top == null:
		return
	var title := "🏆 %s gewinnt!" % top["n"]
	if not game.flag_res.is_empty():
		title = "🚩 " + str(game.flag_res.get("title", title))
	elif not game.team_results.is_empty() and main.game_teams:
		title = "🏆 %s gewinnt!" % game.team_results[0]["n"]
	win = {"n": top["n"], "c": top["c"], "score": int(top["score"]), "info": str(top.get("info", "")), "title": title, "hl": _closest(),
			"board": game.board_list().slice(0, 5).map(func(b): return {"n": b["n"], "c": b["c"], "score": int(b["score"]), "rounds": int(b["rounds"])}),
			"fair": str(fair.get("text", ""))}


func _closest() -> Dictionary:
	"""the closest moment: the highest suspicion of a runner who was NOT caught within the next 2 s"""
	var best := []
	for s_ in samples:
		if int(s_[2]) < 25 or (not best.is_empty() and int(s_[2]) <= int(best[2])):
			continue
		var caught := false
		for e in game.rec_ev:
			if int(e[1]) == int(s_[1]) and str(e[2]) == "caught" and float(e[0]) >= float(s_[0]) - 0.2 and float(e[0]) <= float(s_[0]) + 2.0:
				caught = true
		if not caught:
			best = s_
	if best.is_empty():
		return {}
	var p = game.players[int(best[1])] if int(best[1]) < game.players.size() else null
	var nm: String = str(p["name"]) if p != null else "?"
	var t0 := float(best[0])
	return {"t0": maxf(0.0, t0 - 6.0), "t1": t0 + 3.0, "t": t0, "slot": int(best[1]), "n": nm, "susp": int(best[2]),
			"c": "#" + game.COLORS[int(best[1])].to_html(false),
			"text": "😮 Knappster Moment: %s war bei %d %% Verdacht – und kam davon (%d:%02d)" % [nm, int(best[2]), int(t0) / 60, int(t0) % 60]}


func _rotate() -> void:
	next_txt = ""
	if rotate == "off" or not main.game_mode in ["guard", "seek"]:
		return
	if game.kig != null and (game.kig.active or bool(main.game_kiguard)):
		return                                             # «MoveEye als KI-Wächter»: everybody stays sneaker (roles in turn pause)
	var cands := []
	for p in game.players:
		if p != null and str(p.get("kind", "phone")) != "bot" and p["role"] in ["runner", "guard"]:
			cands.append(p)
	if cands.size() < 2:
		return
	var cur = game.guard_player()
	var nxt = null
	if rotate == "best":
		var bk := 1 << 30
		var bs := -1
		for p in cands:
			if p == cur:
				continue
			var sc := 0
			for r in game.results:
				if r["n"] == p["name"]:
					sc = int(r["score"])
			if int(p["caught"]) < bk or (int(p["caught"]) == bk and sc > bs):
				bk = int(p["caught"])
				bs = sc
				nxt = p
	else:
		cands.sort_custom(func(x, y): return int(x["slot"]) < int(y["slot"]))
		var after: int = int(cur["slot"]) if cur != null else _last_slot
		for p in cands:
			if int(p["slot"]) > after:
				nxt = p
				break
		if nxt == null:
			nxt = cands[0]
		if nxt == cur:
			nxt = cands[1] if cands[0] == cur else cands[0]
	if nxt == null:
		return
	_last_slot = int(nxt["slot"])
	if cur != null and cur != nxt:
		game._set_role(cur, "runner")
	game._set_role(nxt, "guard")
	if nxt["role"] != "guard":
		return
	var rn := "Fänger" if main.game_mode == "seek" else "Wächter"
	next_txt = "🔄 Nächste Runde: %s ist %s (%s)" % [nxt["name"], rn, "der Reihe nach" if rotate == "turn" else "am wenigsten erwischt"]
	game.news(next_txt)
	for q in game.players:
		if q != null:
			game._say(q, ("🔄 Nächste Runde bist DU %s!" % rn) if q == nxt else next_txt, 6.0)


func send_hl(p: Dictionary) -> void:
	"""the phone asks for the closest moment: the replay of the round, only that part"""
	var hl: Dictionary = win.get("hl", {})
	if p["sock"] == null or game.replay.is_empty() or hl.is_empty():
		return
	var r: Dictionary = game.replay.duplicate()
	r["only"] = [hl["t0"], hl["t1"]]
	r["hs"] = hl["slot"]
	r["title"] = hl["text"]
	p["sock"]["ws"].send_text(JSON.stringify(r))


# ---- what the screens show ---------------------------------------------------------------------------------------------------
func state_for(p: Dictionary) -> Dictionary:
	var rs: String = game.round_state
	var d := {"sx": sneak_info(p), "vibe": vibe_on}
	if rs in ["lobby", "countdown", "end"]:
		d["fair"] = str(fair.get("text", "")) if rs != "lobby" else str(calc().get("text", ""))
	if rs in ["lobby", "end"]:
		d["next"] = next_txt
		d["rot"] = rotate if main.game_mode in ["guard", "seek"] else ""
	if rs == "end":
		d["win"] = win
	return d


func spec_info() -> Dictionary:
	var rs: String = game.round_state
	var d := {"fair": str(fair.get("text", "")) if rs != "lobby" else str(calc().get("text", "")), "next": next_txt, "rot": rotate}
	if rs == "end":
		d["win"] = win
	return d


func debug() -> Dictionary:
	return {"cfg": cfg_get(), "fair": fair, "next": next_txt, "win": win, "samples": samples.size(), "helper": helper.duplicate(), "panel": panel.visible}


# ---- the winner screen in the window ---------------------------------------------------------------------------------------
func _hide_win() -> void:
	if panel != null:
		panel.visible = false


func _show_win() -> void:
	if win.is_empty() or (main.localplay != null and main.localplay.active) or (main.tv != null and main.tv.on) or DisplayServer.get_name() == "headless":
		return
	for c in box.get_children():
		c.queue_free()
	var P = main.gamewiz
	var top := HBoxContainer.new()
	box.add_child(top)
	var h := Label.new()
	h.text = P.plain(str(win["title"])) + "  ·  %d Punkte" % int(win["score"])
	h.add_theme_font_size_override("font_size", 24)
	h.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
	h.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(h)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.pressed.connect(_hide_win)
	top.add_child(x)
	var lines := [str(win.get("info", ""))]
	var hl: Dictionary = win.get("hl", {})
	if not hl.is_empty():
		lines.append(str(hl["text"]))
	for k in ["fair", "next"]:
		if str(win.get(k, "")) != "":
			lines.append(str(win[k]))
	var bl := PackedStringArray()
	var i := 0
	for b in win.get("board", []):
		i += 1
		bl.append("%d. %s %d" % [i, b["n"], int(b["score"])])
	if not bl.is_empty():
		lines.append("Rangliste des Abends: " + " · ".join(bl))
	for ln in lines:
		if ln == "":
			continue
		var l := Label.new()
		l.text = P.plain(ln)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = 620
		l.add_theme_font_size_override("font_size", 14)
		box.add_child(l)
	mapc = null
	if not hl.is_empty() and not game.replay.is_empty():
		mapc = Control.new()
		mapc.custom_minimum_size = Vector2(620, 240)
		mapc.draw.connect(_draw_hl)
		box.add_child(mapc)
	_hl_t = 0.0
	_win_until = now() + 30.0
	panel.visible = true
	panel.reset_size()


func _draw_hl() -> void:
	"""the closest moment as a small map: the ways of these seconds, red = seen, the view of the head camera"""
	var R: Dictionary = game.replay
	var hl: Dictionary = win.get("hl", {})
	if R.is_empty() or hl.is_empty() or mapc == null:
		return
	var sz := mapc.size
	mapc.draw_rect(Rect2(Vector2.ZERO, sz), Color(0.03, 0.05, 0.07, 0.9))
	var t0 := float(hl["t0"])
	var t1 := float(hl["t1"])
	var rows: Array = (R["pts"] as Array).filter(func(r): return float(r[0]) >= t0 and float(r[0]) <= t1)
	if rows.is_empty():
		return
	var mw := Vector2(R["mw"][0], R["mw"][1])
	var lo := mw
	var hi := mw
	for r in rows:
		for e in r[1]:
			lo = lo.min(Vector2(e[1], e[2]))
			hi = hi.max(Vector2(e[1], e[2]))
	lo -= Vector2(5, 5)
	hi += Vector2(5, 5)
	var sc: float = minf((sz.x - 20.0) / maxf(1.0, hi.x - lo.x), (sz.y - 30.0) / maxf(1.0, hi.y - lo.y))
	var off := Vector2(10, 10) + (sz - Vector2(20, 30) - (hi - lo) * sc) / 2.0
	var to := func(q: Vector2) -> Vector2: return off + (q - lo) * sc
	for o in R["obst"]:
		var q := Vector2(float(o[0]), float(o[1]))
		if q.x > lo.x - 3 and q.x < hi.x + 3 and q.y > lo.y - 3 and q.y < hi.y + 3:
			mapc.draw_circle(to.call(q), maxf(2.0, float(o[2]) * sc), Color(0.3, 0.33, 0.36, 0.8))
	var tn := t0 + fmod(_hl_t, (t1 - t0) + 1.5)
	var k := 0
	while k < rows.size() - 1 and float(rows[k][0]) < tn:
		k += 1
	var m2: Vector2 = to.call(mw)
	var yaw := deg_to_rad(float(rows[k][2]))
	var half := deg_to_rad(float(R["fov"]) / 2.0)
	var poly := PackedVector2Array([m2])
	for i in range(9):
		var a := yaw - half + 2.0 * half * i / 8.0
		poly.append(m2 + Vector2(-sin(a), -cos(a)) * 30.0 * sc)
	mapc.draw_colored_polygon(poly, Color(1.0, 0.85, 0.3, 0.18))
	mapc.draw_circle(m2, 7, Color(1.0, 0.55, 0.15))
	var cols := {}
	for w in R["who"]:
		cols[int(w[0])] = Color(str(w[2]))
	var last := {}
	for i in range(k + 1):
		for e in rows[i][1]:
			var q3: Vector2 = to.call(Vector2(e[1], e[2]))
			if last.has(int(e[0])):
				mapc.draw_line(last[int(e[0])], q3, Color(1, 0.3, 0.25) if int(e[4]) == 1 else cols.get(int(e[0]), Color.WHITE), 3.0 if int(e[4]) == 1 else 2.0)
			last[int(e[0])] = q3
	for s_ in last:
		mapc.draw_circle(last[s_], 6, cols.get(s_, Color.WHITE))
		if int(s_) == int(hl["slot"]):
			mapc.draw_arc(last[s_], 11, 0, TAU, 24, Color(1, 0.85, 0.3), 2.0)
	var f: Font = ThemeDB.fallback_font
	mapc.draw_string(f, Vector2(10, sz.y - 8), "Knappster Moment  %d:%02d  ·  rot = gesehen" % [int(tn) / 60, int(tn) % 60], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.85, 0.9, 0.95))
