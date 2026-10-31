extends RefCounted
## Gameplay ausfeilen, Punkte 5 / 6 / 8 (Daniel 31.10.2026 01:58) - three rules of the referee, kept by gamemore.gd:
##   5 «Nacht-Spiel» (game_nightrule): the round is at night and the cameras of the guard see ONLY what lies in the cone of
##     the infrared light of the head (or what the white light / the 💡 tool lights up, or a player's own torch). The
##     thermal camera sees warm bodies as before - in the dark it is the guard's best friend. The fixed camera has no
##     infrared light of its own: at night it is blind in this rule.
##     IR cone: half angle IR_HALF and the reach of the simulator's IR light (main.ir_range). ASSUMPTION, not a data sheet:
##     typical 850 nm IR LED spotlights for the Pi camera are given with 30-60° beam angle; 40° (20° half angle) is used.
##   6 «Geräusche zählen» (game_noisecount): a few patches of gravel lie between the starts and the goal. Walking on gravel
##     is loud (crouching less, crawling nearly silent), running is loud everywhere. Every noise is counted (−NOISE_PTS at the
##     end), the guard hears it as a direction ping (phone: arrow at the edge, PC: line, hint marker), the automatic head and
##     the Bot-Wächter turn there. «Wie echte Hardware»: MoveEye has no microphone - the rule is off.
##   8 «Fairness automatisch» (game_autofair): after a round with sneakers against a guard (person, bot, MoveEye, the camera)
##     the result decides: did the sneakers win too easily (≥ 75 % in the goal, at most 1 catch) - the next round the guard
##     gets +15 % energy and the camera notices 12 % faster per step; did the guard win too easily (nobody in the goal, at least
##     1.5 catches per sneaker) - the other way round and one bush more per step. At most ±2 steps, shown openly before and
##     after the round («⚖ Ausgleich: …»). The fairness by the ratio of the roles (gamerules.gd) stays as it is.

const T = preload("res://scripts/i18n.gd")

const IR_HALF := 20.0                    # degrees (see above: an assumption)
const GRAVEL_N := 4
const GRAVEL_R := 1.7                    # m
const NOISE_CD := 1.5                    # s between two counted noises of one player
const NOISE_PTS := 15
const NOISE_LOUD := [0.6, 0.35, 0.08]    # on gravel: walking, crouching, crawling (0..1)
const RUN_LOUD := 0.7                    # running anywhere
const AF_E := 0.15                       # +15 % energy per step
const AF_R := 0.12                       # +12 % faster noticed per step

var game
var main
var more
var gravel: Array = []                   # {"node", "pos"}
var bal := 0                             # Fairness automatisch: −2 (help the sneakers) … +2 (help the guard)
var bal_txt := ""
var _nz := {}                            # slot -> time of the last counted noise
var night_on := false                    # this round plays with the night rule
var pings: Array = []                    # the last pings (tests)


func _lite() -> bool:
	return more._lite()


# ---- round ----------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	_nz.clear()
	pings.clear()
	night_on = more.on("game_nightrule") and not main.game_mode in ["free", "jaeger", "escape"] and not game.jaeger.on()
	if night_on and not main.is_dark() and float(game.night_saved) < 0.0:
		game.night_saved = main.hour()                     # night, back afterwards (like «Nacht-Runde»: game.end_round)
		main.set_hour(23.0)
	if night_on:
		game.news(T.t("🌙 Nacht-Spiel: der Wächter sieht nur im Infrarot-Kegel und im Wärmebild"))
	_gravel_clear()
	if noise_on():
		_gravel_place()
	if bal != 0 and bal_txt != "":
		game.news(bal_txt)
	for p in game.players:
		if p != null:
			p["nz_n"] = 0


func round_end() -> void:
	_gravel_clear()


func clear() -> void:
	_gravel_clear()


# ==== 5 Nacht-Spiel =========================================================================================================
func night_k(p: Dictionary, i: int) -> float:
	"""game.visibility: × this for camera i (1 = as always)"""
	if not night_on or not main.is_dark():
		return 1.0
	if i == 2:
		return 1.0                                         # the thermal camera: warm is warm
	var a = p["actor"]
	if a.player_lamp:
		return 1.0                                         # the own torch gives you away
	if game.now() < float(game.flash_until) or bool(main.mw.get("lights", {}).get("white", false)):
		return 1.0                                         # the white light (light_at decides how bright)
	if i != 0:
		return 0.0                                         # the fixed camera has no infrared light
	return ir_cone(a.position)


func ir_cone(pos: Vector3) -> float:
	"""0..1: how much the infrared light of the head reaches this place (angle to the middle of the picture, reach)"""
	var cam: Camera3D = main.cams[0]
	var to: Vector3 = pos + Vector3(0, 0.8, 0) - cam.global_position
	var d := to.length()
	if d > float(main.ir_range) or d < 0.1:
		return 0.0
	var fw: Vector3 = -cam.global_transform.basis.z
	var ang := rad_to_deg(fw.angle_to(to.normalized()))
	return (1.0 - smoothstep(IR_HALF * 0.75, IR_HALF, ang)) * (1.0 - smoothstep(float(main.ir_range) * 0.8, float(main.ir_range), d))


# ==== 6 Geräusche zählen ====================================================================================================
func noise_on() -> bool:
	return more.on("game_noisecount") and not game.rules.real() and not main.game_mode in ["free", "jaeger", "escape"] and not game.jaeger.on()


func _gravel_place() -> void:
	"""patches of gravel on the way: between the starts and the goal, a bit to the side"""
	var st: Vector3 = game.start_point(0)
	var g: Vector3 = game.goal
	for k in range(GRAVEL_N):
		var f := (k + 1.0) / (GRAVEL_N + 1.0)
		var c := st.lerp(g, f)
		var side := Vector3(-(g - st).z, 0, (g - st).x).normalized() * randf_range(-6.0, 6.0)
		var pos: Vector3 = main.free_spot(c + side, 1.2, true)
		pos.y = main.ground_y(pos.x, pos.z)
		var m := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = GRAVEL_R
		cm.bottom_radius = GRAVEL_R
		cm.height = 0.04
		cm.radial_segments = 10 if _lite() else 20
		m.mesh = cm
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(0.62, 0.58, 0.52)
		mt.roughness = 1.0
		m.material_override = mt
		m.position = pos + Vector3(0, 0.02, 0)
		game.root.add_child(m)
		if not _lite():                                    # a few stones on it (cheap, but not on the Pi)
			for s in range(6):
				var st_ := MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = randf_range(0.06, 0.12)
				sm.height = sm.radius * 1.2
				sm.radial_segments = 6
				sm.rings = 3
				st_.mesh = sm
				st_.material_override = mt
				var ang := randf() * TAU
				st_.position = Vector3(cos(ang), 0.5, sin(ang)) * randf_range(0.2, GRAVEL_R * 0.85)
				st_.position.y = 0.03
				m.add_child(st_)
		gravel.append({"node": m, "pos": pos})


func _gravel_clear() -> void:
	for g in gravel:
		if is_instance_valid(g["node"]):
			g["node"].queue_free()
	gravel.clear()


func on_gravel(pos: Vector3) -> bool:
	for g in gravel:
		if Vector2(pos.x - g["pos"].x, pos.z - g["pos"].z).length() < GRAVEL_R:
			return true
	return false


func loud(p: Dictionary) -> float:
	"""0..1 how loud this runner is right now (gravel, running)"""
	var a = p["actor"]
	var spd: float = a.cur_speed
	if spd < 0.25:
		return 0.0
	var l := 0.0
	if on_gravel(a.position):
		l = NOISE_LOUD[int(a.ctl_posture)]
	if spd > 2.2:
		l = maxf(l, RUN_LOUD)
	return l


func hear(p: Dictionary) -> float:
	"""game._referee: the microphone hears the gravel (the normal hearing - running - stays in game.hearing)"""
	if not noise_on():
		return 0.0
	var a = p["actor"]
	if not on_gravel(a.position):
		return 0.0
	var d: float = a.position.distance_to(main.cams[0].global_position)
	return clampf(loud(p) * 0.8 * (1.0 - d / 45.0), 0.0, 1.0)


func tick() -> void:
	"""every 0.25 s in a round: count the noises, ping the guard"""
	if not noise_on():
		return
	var t: float = game.now()
	for p in game.players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or t < float(p["safe_until"]):
			continue
		var l := loud(p)
		if l < 0.5 or t - float(_nz.get(p["slot"], -9.0)) < NOISE_CD:
			continue
		_nz[p["slot"]] = t
		p["nz_n"] = int(p.get("nz_n", 0)) + 1
		var pos: Vector3 = p["actor"].position
		var kind := "gravel" if on_gravel(pos) else "run"
		game._say(p, (T.t("🔊 Kies knirscht – man hat dich gehört (%d×)", [int(p["nz_n"])]) if kind == "gravel" else T.t("🔊 Rennen ist laut – man hat dich gehört (%d×)", [int(p["nz_n"])])), 2.0)
		game.tools.add_hint(pos, "noise", 2.5, int(p["slot"]))
		game.attention = pos                               # the automatic head and the bot guard look there
		game.attention_until = t + 2.5
		_ping(pos, kind)


func _ping(pos: Vector3, kind: String) -> void:
	"""the guard hears it: the direction relative to the picture he looks at (+ = right), the distance"""
	var cam: Camera3D = main.cams[0]
	var fw: Vector3 = -cam.global_transform.basis.z
	var to: Vector3 = pos - cam.global_position
	var rel := rad_to_deg(wrapf(atan2(-to.x, -to.z) - atan2(-fw.x, -fw.z), -PI, PI))   # > 0 = left
	var d := Vector2(to.x, to.z).length()
	var side := T.t("links") if rel > 0 else T.t("rechts")
	var txt := T.t("👂 Geräusch %s %d° · %d m", [side, int(absf(rel)), int(round(d))]) if absf(rel) > 8.0 else T.t("👂 Geräusch geradeaus · %d m", [int(round(d))])
	pings.append([snappedf(game.now(), 0.1), int(rel), int(d), kind])
	if pings.size() > 20:
		pings.pop_front()
	for g in game.players:
		if g == null or g["role"] != "guard":
			continue
		game._say(g, txt, 2.2)
		if g.get("sock") != null:
			g["sock"]["ws"].send_text(JSON.stringify({"t": "gmping", "a": -int(rel), "d": int(d), "k": kind, "txt": txt}))


func score_info(p: Dictionary) -> Array:
	"""[points, text] for the end line of a runner"""
	var n := int(p.get("nz_n", 0))
	if not noise_on() or p["role"] != "runner" or n == 0:
		return [0, ""]
	return [-NOISE_PTS * n, T.t("🔊 %d× gehört (−%d)", [n, NOISE_PTS * n])]


# ==== 8 Fairness automatisch ================================================================================================
func af_on() -> bool:
	return more.on("game_autofair") and not more.tower_on()


func energy_mul() -> float:
	return 1.0 + AF_E * bal if af_on() else 1.0


func rate_mul() -> float:
	return maxf(0.5, 1.0 + AF_R * bal) if af_on() else 1.0


func extra_hides() -> int:
	return maxi(0, -bal) if af_on() else 0


func judge(results: Array) -> void:
	"""game.end_round (gamemore.round_end): who won too easily? - the step for the next round"""
	if not af_on() or main.game_mode in ["free", "jaeger", "seek", "escape"] or main.game_goal in ["flag", "sweat"]:
		return
	var n := 0
	var goal := 0
	var caught := 0
	for r in results:
		if str(r.get("role", "")) == "runner":
			n += 1
			goal += 1 if bool(r.get("goal", false)) else 0
			caught += int(r.get("caught", 0))
	if n == 0:
		return
	var old := bal
	var why := ""
	if float(goal) / n >= 0.75 and caught <= 1:
		bal = mini(2, bal + 1)
		why = T.t("die Schleicher hatten es zu leicht (%d von %d im Ziel, %d× erwischt)", [goal, n, caught])
	elif goal == 0 and float(caught) / n >= 1.5:
		bal = maxi(-2, bal - 1)
		why = T.t("der Wächter hatte es zu leicht (niemand im Ziel, %d× erwischt)", [caught])
	if bal == old:
		bal_txt = "" if bal == 0 else bal_txt
		return
	bal_txt = describe(why)
	game.news(bal_txt)


func describe(why := "") -> String:
	if bal == 0:
		return T.t("⚖ Ausgleich: wieder ausgeglichen – keine Hilfe mehr") + (" (" + why + ")" if why != "" else "")
	var pc_e := int(round(AF_E * absf(bal) * 100.0))
	var pc_r := int(round(AF_R * absf(bal) * 100.0))
	var t := ""
	if bal > 0:
		t = T.t("⚖ Ausgleich für die nächste Runde: Wächter +%d %% Energie, die Kamera bemerkt %d %% schneller", [pc_e, pc_r])
	else:
		t = T.t("⚖ Ausgleich für die nächste Runde: Wächter −%d %% Energie, die Kamera bemerkt %d %% langsamer, %d Busch mehr", [pc_e, pc_r, -bal])
	return t + (" – " + why if why != "" else "")


func debug() -> Dictionary:
	return {"night": night_on, "dark": main.is_dark(), "ir_range": main.ir_range, "noise": noise_on(), "gravel": gravel.map(func(g): return [snappedf(g["pos"].x, 0.1), snappedf(g["pos"].z, 0.1)]),
			"pings": pings, "bal": bal, "bal_txt": bal_txt, "e_mul": energy_mul(), "r_mul": rate_mul()}
