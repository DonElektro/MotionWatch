extends Node
## 3D-4.x: four extras of the phone games that also help MoveEye (Daniel, 29.10.2026). Set up only in the wizard (gamewiz.gd).
##  1. «Wetterwechsel»: in the middle of a round a thunderstorm, a fog bank or the dusk / dawn comes (10 s warning on the
##     phones). The round report says under which conditions MoveEye caught / missed the players (gamelearn: tag «wx»).
##  2. «Tarn-Sachen»: before the round every runner may take Tarnkleidung (the camo look of actor.gd), a Wärmedecke (cold in
##     the thermal picture), a Karton (a box over the crouching player) or a Regenschirm (hides the upper body). Each has a
##     downside. What MoveEye missed goes into gamelearn as usual, with the thing noted (tag «gear»).
##  3. «Diebstahl» (game goal «theft»): carry the bike or the cool box (main.test_props) to the exit without being caught.
##     MoveEye takes a reference scan before the round and compares afterwards: «MoveEye hat bemerkt: Velo fehlt ✓ / ✗».
##  4. «Lern-Punkte»: what the round of every player taught MoveEye (missed pictures, sneaking ways, false alarms of the
##     «Fehlalarm-Jäger», theft tests) - on the end screen, as XP and in the ranking «Beste Lehrer» (gamexp.gd).

var main
var game

const CFG_FILE := "user://spiel/extras.json"
var wx_on := false                        # wizard «Wetterwechsel»
var gear_on := true                       # wizard «Tarn-Sachen»
var theft_obj := "auto"                   # wizard «Diebstahl»: auto | Velo | Kühlboxen
var seq := 0                              # counts up when something for the screens changed

# ---- 1. weather / time change -------------------------------------------------------------------------------------------
const WX := {"storm": ["⛈", "Gewitter", "Ein Gewitter kommt", "Regen und Blitze: man hört dich kaum, aber die Blitze machen es hell."],
		"fog": ["🌫", "Nebel", "Eine Nebelbank kommt", "Im Nebel sieht die Kamera schlechter – die Wärmebild-Kamera auch ein bisschen."],
		"dusk": ["🌆", "Dämmerung", "Es wird dunkel", "Gleich ist es Nacht: die Kamera schaltet auf Infrarot."],
		"dawn": ["🌅", "Morgen", "Es wird hell", "Die Sonne geht auf: bald sieht dich die Kamera wieder besser."]}
var wx := {}                              # this round: {"kind", "at", "warned", "done", "w", "thunder", "wind", "h0", "t0", "goal"}
var wx_phase := ""                        # "" no change in this round | "vor" before | "nach" after the change
var wx_caught := {"vor": 0, "nach": 0}
var _wx_say := -1

# ---- 2. camouflage things ----------------------------------------------------------------------------------------------
# [id, icon, name, what it does and the downside (for kids)]
const GEAR := [["", "🙂", "Nichts", "Ganz normal, ohne Tarnung."],
		["camo", "🌿", "Tarnkleidung", "Im Grünen schwerer zu erkennen. Aber: auf Kies, Asphalt und nachts nützt sie nichts – und du bist etwas langsamer."],
		["blanket", "🥶", "Wärmedecke", "Die Wärmebild-Kamera sieht dich kaum. Aber: sie raschelt laut und glänzt im Licht."],
		["box", "📦", "Karton", "Du siehst aus wie eine Kiste, nicht wie ein Mensch. Aber: nur geduckt, sehr langsam, kein Rennen – und eine Kiste, die läuft, fällt auf."],
		["umbrella", "☂", "Regenschirm", "Versteckt deinen Oberkörper. Aber: kein Kriechen, etwas langsamer, und der grosse Schirm bewegt sich auffällig."]]
# effect: ai = person detection (head + fixed camera), mo = motion detection, th = thermal camera, loud = steps,
# spd = speed, run = may run, pmin / pmax = postures (0 standing, 1 crouching, 2 crawling)
const FX := {"camo": {"ai": 0.8, "spd": 0.9}, "blanket": {"th": 0.15, "loud": 2.2, "ai": 1.1, "spd": 0.95},
		"box": {"ai": 0.3, "th": 0.5, "spd": 0.55, "run": false, "pmin": 1, "pmax": 1, "loud": 1.3},
		"umbrella": {"ai": 0.55, "mo": 1.2, "th": 0.6, "spd": 0.85, "pmax": 1}}
const GREEN_SCENES := ["camping", "wald", "garten", "wild", "bauernhof", "seeufer", "verstecken", "lustig", "camping_voll", "tarnen"]
const CAMO_STRONG := {"tarnen": 0.6}       # 3D-4.x «Tarnen und Kriechen»: the ground has the colours of the clothes (instead of 0.8)

# ---- 3. theft --------------------------------------------------------------------------------------------------------------
const THEFT_OBJ := {"Velo": ["🚲", "das Velo", "Velo", 0.8], "Kühlboxen": ["🧊", "die Kühlbox", "Kühlbox", 0.85]}
const EXIT := Vector3(0, 0, -47.0)
const THEFT_BONUS := 500
var theft := {}                           # {"name", "icon", "label", "short", "parts": [[node, parent, transform, visible]], "pos",
										  #  "by": slot, "thief", "stolen", "mw": "" | wait | yes | no | off | noref | timeout, "scan", "cmp"}
var exit_node: Node3D
var _ref_key := ""                        # the reference scan of MoveEye was made for this scene and thing
var _scan_say := -1

# ---- 4. learning points ----------------------------------------------------------------------------------------------------
var teach := {}                           # name -> {"n", "parts": [[what, n]], "xp"} of the last round
const TEACH_XP := 15                      # XP per learning point (at most TEACH_XP_MAX)
const TEACH_XP_MAX := 150


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(CFG_FILE)) if FileAccess.file_exists(CFG_FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		wx_on = bool(d.get("game_wx", wx_on))
		gear_on = bool(d.get("game_gear", gear_on))
		theft_obj = str(d.get("game_theft", theft_obj))


func now() -> float:
	return game.now()


func _mw_gone() -> bool:
	"""MoveEye has not sent anything for a while (during a scan it can be slow - not at once)"""
	return main.now() - main.mw_t > 20.0


func mw_on() -> bool:
	return main.now() - main.mw_t < 3.0


# ---- the settings of the wizard ------------------------------------------------------------------------------------------------
func cfg_get() -> Dictionary:
	return {"game_wx": wx_on, "game_gear": gear_on, "game_theft": theft_obj}


func cfg_set(d: Dictionary) -> void:
	if d.has("game_wx"):
		wx_on = bool(d["game_wx"])
	if d.has("game_gear"):
		gear_on = bool(d["game_gear"])
	if d.has("game_theft"):
		theft_obj = str(d["game_theft"]) if str(d["game_theft"]) in ["auto", "Velo", "Kühlboxen"] else "auto"
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(CFG_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(cfg_get()))
	seq += 1


func _mode_with_goal() -> bool:
	return not main.game_mode in ["seek", "free", "jaeger"]


func wx_active() -> bool:
	"""a weather change is planned or done in this round (game.gd: then no random «Gewitter» event)"""
	return wx_phase != ""


func gear_active() -> bool:
	return gear_on and main.game_mode != "jaeger"


# ---- round ----------------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	"""from game.start_round (after the starts, the goal and the times are set)"""
	seq += 1
	teach.clear()
	_cancel_cmp()
	wx = {}
	wx_phase = ""
	wx_caught = {"vor": 0, "nach": 0}
	if wx_on and main.game_mode in ["mw", "guard", "camera", "mwhand", "patrol"]:
		var kinds := ["storm", "fog", "dawn"] if main.is_dark() or main.game_night else ["storm", "fog", "dusk"]
		var k: String = kinds[randi() % kinds.size()]
		var dur: float = float(game.t_end) - float(game.t_start)
		var at: float = float(game.t_start) + clampf(dur * randf_range(0.35, 0.5), 25.0, maxf(25.0, dur - 30.0))
		if game.sprint():
			at = float(game.t_start) + 40.0
		wx = {"kind": k, "at": at, "warned": false, "done": false}
		wx_phase = "vor"
	for p in game.players:
		if p == null:
			continue
		p["wx_seen"] = {}
		p["gear_round"] = ""
		p["gear_caught"] = 0
		if p["role"] != "runner":
			_undress(p)
			continue
		if not gear_active():
			p["gear"] = ""
		elif str(p.get("kind", "phone")) == "bot" and not p.has("gear_set") and (randf() < 0.5 or main.scene == "tarnen"):
			p["gear"] = GEAR[1 + randi() % (GEAR.size() - 1)][0]          # bots try the things too (for the learning)
		dress(p)
		p["gear_round"] = str(p.get("gear", ""))         # what was worn in this round (the end screen)
	_theft_start()


func _process(dt: float) -> void:
	if game == null or not game.open:
		return
	var t := now()
	var rs: String = game.round_state
	if rs == "countdown" and not theft.is_empty() and not (theft.get("scan", {}) as Dictionary).is_empty():
		_scan_tick(t)
	if rs == "play":
		_wx_tick(t, dt)
		for p in game.players:
			if p != null and p["role"] == "runner" and p["state"] == "play":
				_speed(p)
	if not (theft.get("cmp", {}) as Dictionary).is_empty():
		_cmp_tick(t)


# ---- 1. weather --------------------------------------------------------------------------------------------------------------
func _all_say(txt: String, secs: float) -> void:
	for q in game.players:
		if q != null:
			game._say(q, txt, secs)


func _wx_tick(t: float, dt: float) -> void:
	if wx.is_empty():
		return
	var k: String = wx["kind"]
	var W: Array = WX[k]
	var at: float = wx["at"]
	if not bool(wx["done"]) and t >= at - 10.0:
		var left := int(ceil(at - t))
		if not bool(wx["warned"]):
			wx["warned"] = true
			game.news("%s Achtung: %s – in 10 Sekunden!" % [W[0], W[2]])
			for q in game.players:
				if q != null:
					game._event(q, "item")
			if k == "storm" or k == "fog":                     # the clouds come first
				wx["w"] = main.weather
				wx["thunder"] = main.thunder
				wx["wind"] = main.wind
				main.weather = "cloudy"
				if k == "storm":
					main.wind = maxf(float(main.wind), 30.0)
			seq += 1
		if left != _wx_say and left > 0:
			_wx_say = left
			_all_say("%s Achtung! %s – noch %d s. %s" % [W[0], W[2], left, W[3]], 1.2)
		if game.ev_kind == "storm" and t >= at - 1.0:          # a random storm right now: wait until it is over
			wx["at"] = at + 2.0
			return
	if not bool(wx["done"]) and t >= float(wx["at"]):
		wx["done"] = true
		wx_phase = "nach"
		wx["t0"] = t
		wx["h0"] = main.hour()
		if not wx.has("w"):
			wx["w"] = main.weather
			wx["thunder"] = main.thunder
			wx["wind"] = main.wind
		match k:
			"storm":
				main.weather = "rain"
				main.thunder = true
				main.wind = maxf(float(main.wind), 45.0)
				main._flash_next = main.now() + 1.0             # the first flash comes at once
			"fog":
				main.weather = "fog"
		game.news("%s %s! %s" % [W[0], W[1], W[3]])
		_all_say("%s Jetzt: %s! %s" % [W[0], W[1], W[3]], 5.0)
		for q in game.players:
			if q != null:
				game._event(q, "item")
		seq += 1
	if bool(wx["done"]) and k in ["dusk", "dawn"] and not bool(wx.get("light_done", false)):
		var lt0: float = float(wx.get("lt", t))
		wx["lt"] = t
		# smooth: the clock runs fast for a few seconds until it is dark (dusk) or bright (dawn) - fits every season
		var reached: bool = main.is_dark() if k == "dusk" else (not main.is_dark() and main.light_level() > 0.45)
		var moved: float = fposmod(main.hour() - float(wx["h0"]), 24.0)
		if reached and float(wx.get("extra", 0.0)) <= 0.0:
			wx["extra"] = 0.25                                 # a bit further, so it is really dark / bright
		if float(wx.get("extra", 0.0)) > 0.0:
			wx["extra"] = float(wx["extra"]) - clampf(t - lt0, 0.0, 0.5) * 0.3
			if float(wx["extra"]) <= 0.0:
				wx["light_done"] = true
		if moved > 14.0 or t - float(wx["t0"]) > 45.0:
			wx["light_done"] = true
		if not bool(wx.get("light_done", false)):
			var el: float = main.sun_el()                       # fast through the bright (or dark) hours, slow through the twilight
			var far: bool = el > 8.0 if k == "dusk" else el < -12.0
			var rdt: float = clampf(t - lt0, 0.0, 0.5)   # the wall clock (a slow PC has long frames)
			main.set_hour(main.hour() + rdt * (1.2 if far else 0.25))


func _wx_restore() -> void:
	if wx.is_empty():
		return
	if wx.has("w"):
		main.weather = str(wx["w"])
		main.thunder = bool(wx["thunder"])
		main.wind = float(wx["wind"])
	if bool(wx.get("done", false)) and str(wx["kind"]) in ["dusk", "dawn"] and wx.has("h0"):
		main.set_hour(float(wx["h0"]) + (now() - float(wx["t0"])) * float(main.speed) / 3600.0)


func phase() -> String:
	"""for gamelearn: before / after the weather change ("" = no change in this round)"""
	return wx_phase


func cond_now() -> String:
	"""the conditions right now, in words (for the report)"""
	var c: String = {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(main.weather, str(main.weather))
	if main.thunder and main.weather == "rain":
		c = "Gewitter"
	return c + (" · Nacht" if main.is_dark() else " · Tag")


func on_caught(p: Dictionary) -> void:
	if wx_phase != "":
		wx_caught[wx_phase] = int(wx_caught.get(wx_phase, 0)) + 1
	p["gear_caught"] = int(p.get("gear_caught", 0)) + 1


func caught_text(p: Dictionary) -> String:
	"""«Gegen MoveEye»: the referee says whether MoveEye still found the player with the thing"""
	var g := str(p.get("gear", ""))
	if g == "":
		return "MoveEye hat dich erkannt!"
	return "MoveEye hat dich trotz %s %s erkannt!" % [_gear(g)[1], _gear(g)[2]]


func _wx_stats() -> Dictionary:
	"""per phase: how often a player was well in the picture and how often MoveEye reported him (gamelearn episodes)"""
	var st := {"vor": [0, 0], "nach": [0, 0]}
	for e in game.learn.eps:
		var ph := str(e.get("wx", ""))
		if st.has(ph):
			st[ph][0] += 1
			if float(e["lat"]) >= 0.0:
				st[ph][1] += 1
	return st


func wx_lines() -> Array:
	if wx.is_empty():
		return []
	var W: Array = WX[wx["kind"]]
	if not bool(wx.get("done", false)):
		return ["%s Der Wetterwechsel (%s) kam nicht mehr – die Runde war schneller vorbei." % [W[0], W[1]]]
	var st := _wx_stats()
	var out := []
	if st["vor"][0] + st["nach"][0] > 0:
		out.append("%s Vor dem %s: MoveEye hat %d von %d erkannt · %s: %d von %d" % [W[0], W[1] if wx["kind"] != "dusk" else "Dunkelwerden",
				st["vor"][1], st["vor"][0], "danach" if wx["kind"] != "storm" else "im Gewitter", st["nach"][1], st["nach"][0]])
	else:
		out.append("%s Vor dem Wechsel %d× erwischt, danach (%s) %d× erwischt" % [W[0], int(wx_caught["vor"]), W[1], int(wx_caught["nach"])])
	return out


# ---- 2. camouflage -------------------------------------------------------------------------------------------------------------
func _gear(id: String) -> Array:
	for g in GEAR:
		if g[0] == id:
			return g
	return GEAR[0]


func choose(p: Dictionary, v: String) -> void:
	"""the phone: the player picks a thing (before the round)"""
	if game.round_state in ["countdown", "play"] or not gear_active():
		return
	if _gear(v)[0] != v:
		v = ""
	p["gear"] = v
	p["gear_set"] = true                                 # chosen (a bot then keeps it)
	dress(p)
	seq += 1


func fx(p: Dictionary, key: String, def := 1.0):
	var g := str(p.get("gear", ""))
	if g == "" or not FX.has(g):
		return def
	return FX[g].get(key, def)


func ai_mul(p: Dictionary) -> float:
	"""for game.cam_sees: the person detection of the head and the fixed camera"""
	var g := str(p.get("gear", ""))
	if g == "camo" and (main.is_dark() or not main.scene in GREEN_SCENES):
		return 1.0                                       # camouflage only helps in the green by day
	var m: float = fx(p, "ai")
	if g == "camo" and CAMO_STRONG.has(main.scene):
		m = float(CAMO_STRONG[main.scene])
	if g == "blanket" and not (main.is_dark() and not p["actor"].player_lamp):
		m = 1.1                                          # it shines in the light
	elif g == "blanket":
		m = 1.0
	return m


func mo_mul(p: Dictionary) -> float:
	return fx(p, "mo")


func th_mul(p: Dictionary) -> float:
	return fx(p, "th")


func loud_mul(p: Dictionary) -> float:
	return fx(p, "loud")


func _speed(p: Dictionary) -> void:
	var a = p["actor"]
	var s: float = fx(p, "spd")
	if bool(p.get("carry", false)) and not theft.is_empty() and int(theft.get("by", -1)) == int(p["slot"]):
		s *= float(theft["spd"])                         # the bike / the cool box makes you slower
	a.gear_speed = s
	a.gear_norun = not bool(fx(p, "run", true))
	a.gear_pmin = int(fx(p, "pmin", 0))
	a.gear_pmax = int(fx(p, "pmax", 2))


func _undress(p: Dictionary) -> void:
	_free_nodes(p)
	var a = p["actor"]
	if p.has("gear_camo0"):                              # the own look back (the camouflage clothes were borrowed)
		var was: bool = bool(p["gear_camo0"])
		p.erase("gear_camo0")
		if bool(p["look"].get("camo", false)) != was:
			p["look"]["camo"] = was
			game._rebuild(p)
			a = p["actor"]
	a.gear_speed = 1.0
	a.gear_norun = false
	a.gear_pmin = 0
	a.gear_pmax = 2


func _free_nodes(p: Dictionary) -> void:
	for k in ["gear_node", "gear_node2"]:
		if p.has(k) and is_instance_valid(p[k]):
			p[k].queue_free()
		p.erase(k)
	p.erase("gear_built")


func dress(p: Dictionary) -> void:
	"""put the thing on the figure (again after a new look, game._rebuild)"""
	var g := str(p.get("gear", ""))
	if p.has("gear_node") and is_instance_valid(p["gear_node"]) and str(p.get("gear_built", "")) == g and p["actor"].is_ancestor_of(p["gear_node"]):
		_speed(p)
		return
	_free_nodes(p)
	if g != "camo" and p.has("gear_camo0"):
		var old = p["actor"]
		_undress(p)
		if p["actor"] != old:
			return                                       # the figure was built again (and dressed by _rebuild)
	var a = p["actor"]
	if g == "camo" and not bool(p["look"].get("camo", false)):
		p["gear_camo0"] = false                          # the camouflage look of actor.gd, borrowed for this round
		p["look"]["camo"] = true
		game._rebuild(p)
		return                                           # _rebuild calls dress again
	if g in ["blanket", "box", "umbrella"]:
		var nd := Node3D.new()
		nd.name = "gear"
		var amb: float = float(main.ambient)
		match g:
			"blanket":                                   # silver foil round the body: cold outside in the thermal picture
				var foil := StandardMaterial3D.new()
				foil.albedo_color = Color(0.82, 0.8, 0.72)
				foil.metallic = 0.9
				foil.roughness = 0.25
				var host: Node3D = a.torso if a.torso != null else a.body_root
				host.add_child(nd)
				main.add_mesh(nd, _caps(0.3, 1.0), Vector3(0, 0.36, 0), foil, amb + 1.5)
				if a.hips != null:
					var nd2 := Node3D.new()
					a.hips.add_child(nd2)
					main.add_mesh(nd2, _caps(0.25, 0.7), Vector3(0, -0.18, 0), foil, amb + 2.0)
					p["gear_node2"] = nd2
			"box":                                       # a cardboard box over the crouching player
				var card := StandardMaterial3D.new()
				card.albedo_color = Color(0.62, 0.47, 0.3)
				card.roughness = 0.95
				a.add_child(nd)
				main.add_mesh(nd, _bx(0.9, 1.55, 0.9), Vector3(0, 0.775, 0), card, amb + 4.0)
				var tape := StandardMaterial3D.new()
				tape.albedo_color = Color(0.75, 0.65, 0.45)
				main.add_mesh(nd, _bx(0.92, 0.06, 0.2), Vector3(0, 1.54, 0), tape, amb + 4.0)
			"umbrella":                                  # held to the front: hides the upper body
				var cloth := StandardMaterial3D.new()
				cloth.albedo_color = Color(0.12, 0.2, 0.45)
				cloth.cull_mode = BaseMaterial3D.CULL_DISABLED
				var host2: Node3D = a.torso if a.torso != null else a.body_root
				host2.add_child(nd)
				var cm := CylinderMesh.new()
				cm.top_radius = 0.04
				cm.bottom_radius = 0.62
				cm.height = 0.3
				cm.radial_segments = 10
				main.add_mesh(nd, cm, Vector3(0, 0.42, -0.45), cloth, amb + 1.0, Vector3(PI / 2, 0, 0))
				var stick := StandardMaterial3D.new()
				stick.albedo_color = Color(0.15, 0.15, 0.15)
				var sm := CylinderMesh.new()
				sm.top_radius = 0.012
				sm.bottom_radius = 0.012
				sm.height = 0.45
				main.add_mesh(nd, sm, Vector3(0.0, 0.42, -0.22), stick, amb + 1.0, Vector3(PI / 2, 0, 0))
		p["gear_node"] = nd
		p["gear_built"] = g
	_speed(p)


func _caps(r: float, h: float) -> CapsuleMesh:
	var c := CapsuleMesh.new()
	c.radius = r
	c.height = maxf(h, 2.0 * r + 0.01)
	c.radial_segments = 12
	c.rings = 4
	return c


func _bx(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


func gear_of(p: Dictionary) -> String:
	return str(p.get("gear", ""))


func _gear_res(p: Dictionary) -> String:
	"""the end screen of a player: did MoveEye still see him with the thing?"""
	var g := str(p.get("gear_round", ""))
	if g == "" or p["role"] != "runner":
		return ""
	var G := _gear(g)
	var rep := 0
	var miss := 0
	for e in game.learn.eps:
		if str(e.get("n", "")) == str(p["name"]) and str(e.get("gear", "")) == g:
			if float(e["lat"]) >= 0.0:
				rep += 1
			else:
				miss += 1
	if rep + miss > 0:
		return "%s %s: MoveEye hat dich %d× gemeldet und %d× übersehen%s" % [G[1], G[2], rep, miss, " – die Bilder lernt es jetzt" if miss > 0 else ""]
	return "%s %s: %d× erwischt" % [G[1], G[2], int(p.get("gear_caught", 0))]


# ---- 3. theft ---------------------------------------------------------------------------------------------------------------------
func theft_on() -> bool:
	return main.game_goal == "theft" and _mode_with_goal()


func goal_mode() -> String:
	"""the game goal as the referee uses it: «theft» only where it can be played (else like «reach»)"""
	if main.game_goal != "theft":
		return main.game_goal
	return "theft" if theft_on() and not _target().is_empty() else "reach"


func _target() -> Dictionary:
	"""the thing to steal in this scene: [name, node] (the wizard's choice, otherwise what there is)"""
	var order := ["Velo", "Kühlboxen"]
	if theft_obj == "Kühlboxen":
		order = ["Kühlboxen", "Velo"]
	elif theft_obj == "auto" and randf() < 0.5:
		order = ["Kühlboxen", "Velo"]
	if main.scene == "velodieb":
		order = ["Velo"]                                 # 3D-4.x «Velodieb»: always the bike
	for nm in order:
		var n = main.test_props.get(nm, null)
		if n != null and is_instance_valid(n) and n.visible:
			return {"name": nm, "node": n}
	return {}


func theft_goal() -> Array:
	"""game._pick_goal: [position, name] of the thing, or [] (then the normal goal)"""
	if not theft_on():
		return []
	if not theft.is_empty() and theft.has("pos") and _parts_ok() and str(theft.get("want", "")) == theft_obj and str(theft.get("scene", "")) == str(main.scene):
		return [theft["pos"], theft["label"]]
	theft = {}
	var tg := _target()
	if tg.is_empty():
		return []
	var parts := _parts_of(tg["name"], tg["node"])
	if parts.is_empty():
		return []
	var info: Array = THEFT_OBJ[tg["name"]]
	var pos: Vector3 = (parts[0][0] as Node3D).global_position
	theft = {"name": tg["name"], "icon": info[0], "label": info[1], "short": info[2], "spd": info[3], "parts": parts,
			"pos": Vector3(pos.x, 0, pos.z), "want": theft_obj, "scene": str(main.scene), "by": -1, "thief": "", "stolen": false, "mw": "", "scan": {}, "cmp": {}}
	return [theft["pos"], theft["label"]]


func _parts_ok() -> bool:
	for pt in theft.get("parts", []):
		if not is_instance_valid(pt[0]) or not is_instance_valid(pt[1]) or not (pt[1] as Node).is_inside_tree():
			return false
	return not theft.get("parts", []).is_empty()


func _parts_of(nm: String, n: Node3D) -> Array:
	"""what is carried away: the whole bike; of the cool boxes only the first one (its picture and its thermal twin)"""
	var out := []
	if nm == "Kühlboxen":
		var first: Node3D = null
		for c in n.get_children():
			if c is MeshInstance3D:
				if first == null:
					first = c
				if (c as Node3D).position.distance_to(first.position) < 0.05:
					out.append([c, n, (c as Node3D).transform, (c as Node3D).visible])
		return out
	return [[n, n.get_parent(), n.transform, n.visible]]


func _theft_start() -> void:
	"""the round begins: exit marker, and MoveEye takes a reference scan first (if it has none for this place and thing)"""
	if not theft.is_empty() and not bool(theft.get("stolen", false)):
		_restore()
	if goal_mode() != "theft":
		theft = {}
		_exit(false)
		return
	if theft.is_empty() or not theft.has("parts"):
		var gl := theft_goal()
		if gl.is_empty():
			return
	theft["by"] = -1
	theft["thief"] = ""
	theft["stolen"] = false
	theft["mw"] = ""
	theft["cmp"] = {}
	_exit(true)
	game.news("%s Diebstahl: Wer bringt %s unbemerkt zum Ausgang?" % [theft["icon"], theft["label"]])
	if not mw_on():
		theft["mw"] = "off"
		return
	var r = main.mw.get("refscan", null)
	var key: String = str(main.scene) + "|" + str(theft["name"])
	if typeof(r) == TYPE_DICTIONARY and bool(r.get("ref", false)) and _ref_key == key:
		return                                           # the reference of this place is there already
	main.mw_request("refscan")
	theft["scan"] = {"id": int(main.mw_cmd.get("id", 0)), "t": now(), "t0": now(), "key": key}


func _req_ok(rq: Dictionary, op: String, t: float) -> bool:
	"""a request to MoveEye (reference scan / comparison) is finished. MoveEye skips a request that came just before it
	(re)connected - then it is sent once more."""
	var r = main.mw.get("refscan", null)
	if typeof(r) != TYPE_DICTIONARY:
		return false
	if str(r.get("busy", "")) != "":
		rq["busy_seen"] = true
		return false
	if int(r.get("cmd_seen", 0)) < int(rq["id"]) or t - float(rq["t"]) < 3.0:
		return false
	if not bool(rq.get("busy_seen", false)) and int(rq.get("again", 0)) < 2 and t - float(rq["t"]) > 4.0:
		var done_anyway: bool = op == "refcompare" and typeof(r.get("last", null)) == TYPE_DICTIONARY and float(r["last"].get("t", 0.0)) > float(rq.get("last_t", 0.0))
		if not done_anyway:
			main.mw_request(op)                          # not started: once more
			rq["id"] = int(main.mw_cmd.get("id", 0))
			rq["t"] = t
			rq["again"] = int(rq.get("again", 0)) + 1
			return false
	return true


func _scan_tick(t: float) -> void:
	"""countdown: wait (max. 3 min) until MoveEye has its reference - the round starts afterwards"""
	var sc: Dictionary = theft["scan"]
	var r = main.mw.get("refscan", null)
	var done := false
	if _req_ok(sc, "refscan", t):
		done = true
		if bool(r.get("ref", false)):
			_ref_key = str(sc["key"])
		else:
			theft["mw"] = "noref"
	if t - float(sc.get("t0", sc["t"])) > 180.0 or _mw_gone():
		done = true
		theft["mw"] = "noref"
	if done:
		theft["scan"] = {}
		game.t_start = t + 4.0
		game.t_end = game.t_start + (float(game.SPRINT_SECS) if game.sprint() else float(main.game_minutes) * 60.0)
		_all_say("📸 Fertig – MoveEye kennt jetzt den Platz. Los geht's!" if str(theft["mw"]) != "noref" else "📸 MoveEye konnte sich den Platz nicht merken – los geht's trotzdem!", 3.0)
		seq += 1
		return
	if float(game.t_start) - t < 3.0:                    # hold the countdown
		var dd: float = t + 3.0 - float(game.t_start)
		game.t_start = float(game.t_start) + dd
		game.t_end = float(game.t_end) + dd
	var s := int(t - float(sc["t"]))
	if s != _scan_say:
		_scan_say = s
		var step := ""
		if typeof(r) == TYPE_DICTIONARY and str(r.get("busy", "")) != "":
			step = " (Richtung %d von %d)" % [int(r.get("step", 0)), int(r.get("n", 0))]
		_all_say("📸 MoveEye schaut sich zuerst den Platz an%s – so merkt es später, ob %s fehlt. Gleich geht's los …" % [step, theft["label"]], 1.5)


func scanning() -> bool:
	return not theft.is_empty() and not (theft.get("scan", {}) as Dictionary).is_empty()


func _exit(on: bool) -> void:
	if exit_node != null and is_instance_valid(exit_node):
		exit_node.queue_free()
	exit_node = null
	if not on:
		return
	exit_node = Node3D.new()
	game.root.add_child(exit_node)
	exit_node.position = game._g(EXIT)
	var beam := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.6
	cm.bottom_radius = 0.9
	cm.height = 7.0
	beam.mesh = cm
	beam.position.y = 3.5
	beam.material_override = game._glow(Color(1.0, 0.6, 0.15, 0.3))
	beam.layers = 16                                     # only the players see it (not MoveEye)
	exit_node.add_child(beam)
	var lb := Label3D.new()
	lb.text = "AUSGANG"
	lb.font_size = 96
	lb.pixel_size = 0.01
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.modulate = Color(1.0, 0.75, 0.3)
	lb.position.y = 3.0
	lb.layers = 16
	exit_node.add_child(lb)


func home_of(p: Dictionary) -> Vector3:
	"""where the loot goes: the exit when stealing, otherwise the own start"""
	if goal_mode() == "theft":
		return game._g(EXIT)
	return game.start_point(p["slot"])


func take(p: Dictionary) -> bool:
	"""a player is at the thing: he takes it (only one can carry it)"""
	if theft.is_empty() or bool(theft["stolen"]):
		return false
	if int(theft["by"]) >= 0 and int(theft["by"]) != int(p["slot"]):
		game._say(p, "%s %s hat schon %s – lenk die Kamera ab!" % [theft["icon"], theft["thief"], theft["label"]], 1.5)
		return false
	theft["by"] = int(p["slot"])
	theft["thief"] = str(p["name"])
	p["carry"] = true
	p["loot"].visible = false
	var a = p["actor"]
	for pt in theft["parts"]:
		var n: Node3D = pt[0]
		if not is_instance_valid(n):
			continue
		n.reparent(a, false)
		n.visible = true
		if theft["name"] == "Velo":
			n.transform = Transform3D(Basis.IDENTITY, Vector3(0.5, 0.05, 0.0))   # pushed along at the right side
		else:
			n.transform = Transform3D(Basis.IDENTITY, Vector3(0, 0.78, -0.38))  # carried in front of the belly
	_speed(p)
	if theft["name"] == "Velo" and main.scene == "velodieb":
		main.add_event("Velo", "tag")                    # 3D-4.x «Velodieb»: the bike sensor notices the grab (MoveEye gets it)
	game._say(p, "%s Du hast %s! Jetzt zum Ausgang (orange) – aber pass auf die Kamera auf." % [theft["icon"], theft["label"]], 4.0)
	game.news("%s %s schnappt sich %s!" % [theft["icon"], p["name"], theft["label"]])
	seq += 1
	return true


func drop(p: Dictionary) -> void:
	"""caught with the thing: it goes back to its place"""
	if theft.is_empty() or int(theft["by"]) != int(p["slot"]) or bool(theft["stolen"]):
		return
	theft["by"] = -1
	theft["thief"] = ""
	_restore()
	_speed(p)
	game.news("%s %s ist wieder an seinem Platz" % [theft["icon"], str(theft["short"])])
	seq += 1


func on_goal(p: Dictionary) -> void:
	"""a player reached the goal: when stealing - the thing is gone, the round ends soon"""
	if goal_mode() != "theft" or theft.is_empty() or int(theft["by"]) != int(p["slot"]):
		return
	theft["stolen"] = true
	p["bonus"] = int(p.get("bonus", 0)) + THEFT_BONUS
	for pt in theft["parts"]:                            # at its place, but invisible: it is missing
		var n: Node3D = pt[0]
		if is_instance_valid(n) and is_instance_valid(pt[1]):
			n.reparent(pt[1], false)
			n.transform = pt[2]
			n.visible = false
	p["carry"] = false
	_speed(p)
	game._say(p, "%s Geschafft! %s ist weg (+%d). Merkt MoveEye das?" % [theft["icon"], theft["label"], THEFT_BONUS], 5.0)
	game.news("%s %s hat %s gestohlen!" % [theft["icon"], p["name"], theft["label"]])
	game.t_end = minf(float(game.t_end), now() + 4.0)
	seq += 1


func _restore() -> void:
	if theft.is_empty() or not theft.has("parts"):
		return
	for pt in theft["parts"]:
		var n: Node3D = pt[0]
		if not is_instance_valid(n):
			continue
		if is_instance_valid(pt[1]) and n.get_parent() != pt[1]:
			n.reparent(pt[1], false)
		n.transform = pt[2]
		n.visible = bool(pt[3])


func _cancel_cmp() -> void:
	if not theft.is_empty() and not (theft.get("cmp", {}) as Dictionary).is_empty():
		theft["cmp"] = {}
		_restore()


func _cmp_tick(t: float) -> void:
	"""after a theft: wait for the comparison of MoveEye (reference scan) - then the answer and the thing back"""
	var cm: Dictionary = theft["cmp"]
	var r = main.mw.get("refscan", null)
	if _req_ok(cm, "refcompare", t):
		var l = r.get("last", null)
		if typeof(l) == TYPE_DICTIONARY and float(l.get("t", 0.0)) > float(cm["last_t"]):
			var gone: Array = l.get("gone", [])
			var yes: bool = int(l.get("missing", 0)) > 0 or str(theft["short"]) in gone or str(theft["name"]) in gone
			theft["mw"] = "yes" if yes else "no"
			theft["mw_l"] = {"missing": int(l.get("missing", 0)), "new": int(l.get("new", 0)), "changed": int(l.get("changed", 0)), "gone": gone}
			_cmp_done()
			return
	if t - float(cm.get("t0", cm["t"])) > 240.0 or _mw_gone():
		theft["mw"] = "timeout"
		_cmp_done()


func _cmp_done() -> void:
	theft["cmp"] = {}
	_restore()
	game.news(theft_text())
	_save_theft()
	seq += 1
	game.paint()


func _save_theft() -> void:
	"""the theft as a case for MoveEye's learning (sent with «Spielbericht senden»)"""
	var rid: String = game.learn.round_id
	if rid == "":
		return
	var dir := "user://spiel/" + rid
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir + "/diebstahl.json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"v": 1, "ding": theft["name"], "dieb": theft["thief"], "szene": main.scene, "bemerkt": theft["mw"],
				"vergleich": theft.get("mw_l", {}), "wetter": str(main.weather), "dunkel": main.is_dark(),
				"datum": Time.get_datetime_string_from_system(false, true)}, " "))


func theft_text() -> String:
	if theft.is_empty():
		return ""
	var s: String = theft["short"]
	if not bool(theft["stolen"]):
		return "%s %s ist noch da – niemand hat es zum Ausgang gebracht." % [theft["icon"], s]
	match str(theft["mw"]):
		"wait":
			return "%s %s fehlt! MoveEye schaut jetzt nach (Referenz-Scan) …" % [theft["icon"], s]
		"yes":
			return "%s MoveEye hat bemerkt: %s fehlt ✓" % [theft["icon"], s]
		"no":
			return "%s MoveEye hat nicht bemerkt, dass %s fehlt ✗" % [theft["icon"], s]
		"noref":
			return "%s %s ist weg – MoveEye hatte kein Referenz-Bild, darum keine Prüfung." % [theft["icon"], s]
		"timeout":
			return "%s %s ist weg – MoveEye hat nicht rechtzeitig geantwortet." % [theft["icon"], s]
	return "%s %s ist weg – MoveEye ist nicht verbunden, darum keine Prüfung." % [theft["icon"], s]


# ---- end of the round -----------------------------------------------------------------------------------------------------------
func round_end() -> void:
	"""from game.end_round, right after gamelearn (before the scores): weather back, ask MoveEye about the theft"""
	_wx_restore()
	if not theft.is_empty() and theft.has("parts"):
		if bool(theft["stolen"]):
			var r = main.mw.get("refscan", null)
			if mw_on() and str(theft["mw"]) not in ["noref", "off"] and typeof(r) == TYPE_DICTIONARY and bool(r.get("ref", false)):
				var l = r.get("last", null)
				main.mw_request("refcompare")
				theft["cmp"] = {"id": int(main.mw_cmd.get("id", 0)), "t": now(), "t0": now(), "last_t": float(l.get("t", 0.0)) if typeof(l) == TYPE_DICTIONARY else 0.0}
				theft["mw"] = "wait"
			else:
				if str(theft["mw"]) == "":
					theft["mw"] = "off" if not mw_on() else "noref"
				_restore()
				_save_theft()
		else:
			_restore()
		theft["scan"] = {}
	_exit(false)
	for p in game.players:
		if p != null and p["role"] == "runner":
			p["actor"].gear_speed = 1.0
	seq += 1


func teach_award(p: Dictionary) -> Array:
	"""what the round of this player taught MoveEye -> [[what, xp]] for the XP (and the total for «Beste Lehrer»)"""
	var nm := str(p["name"])
	var parts := []
	var pics := 0
	for m in game.learn.misses:
		if str(m.get("n", "")) == nm:
			pics += 1
	if pics > 0:
		parts.append(["Bild" if pics == 1 else "Bilder", pics])
	if nm in game.learn.saved_by:
		parts.append(["Schleichweg", 1])
	var fa := 0
	for c in game.jaeger.cases:
		if str(c.get("n", "")) == nm:
			fa += 1
	if fa > 0:
		parts.append(["Fehlalarm" if fa == 1 else "Fehlalarme", fa])
	if not theft.is_empty() and bool(theft.get("stolen", false)) and str(theft["thief"]) == nm and str(theft["mw"]) in ["wait", "yes", "no"]:
		parts.append(["Diebstahl-Test", 1])
	var n := 0
	for x in parts:
		n += int(x[1])
	var xpv: int = mini(TEACH_XP_MAX, n * TEACH_XP)
	var total := 0
	if n > 0:
		total = game.xp.add_teach(nm, n)
	teach[nm] = {"n": n, "parts": parts, "xp": xpv, "total": total}
	return [["MoveEye beigebracht", xpv]] if n > 0 else []


func teach_text(nm: String) -> String:
	var tc: Dictionary = teach.get(nm, {})
	if tc.is_empty() or int(tc["n"]) <= 0:
		return ""
	var bits := PackedStringArray()
	for x in tc["parts"]:
		bits.append("%d %s" % [int(x[1]), x[0]])
	return "🧠 Deine Runde hat MoveEye %d %s beigebracht (%s)" % [int(tc["n"]), "Ding" if int(tc["n"]) == 1 else "Dinge", ", ".join(bits)]


func teach_sum() -> int:
	var n := 0
	for k in teach:
		n += int(teach[k]["n"])
	return n


# ---- screens ---------------------------------------------------------------------------------------------------------------------
func lines(gear_lines := true) -> Array:
	"""the end of the round in a few lines (phones, MoveEye, the window)"""
	if game.round_state != "end":
		return []
	var out := []
	out.append_array(wx_lines())
	var tt := theft_text()
	if tt != "":
		out.append(tt)
	var gs := {}
	for p in game.players:
		if gear_lines and p != null and str(p.get("gear_round", "")) != "" and p["role"] == "runner":
			var g := str(p["gear_round"])
			if not gs.has(g):
				gs[g] = [0, 0, 0]
			for e in game.learn.eps:
				if str(e.get("n", "")) == str(p["name"]) and str(e.get("gear", "")) == g:
					gs[g][0 if float(e["lat"]) >= 0.0 else 1] += 1
			gs[g][2] += int(p.get("gear_caught", 0))
	for g in gs:
		var G := _gear(g)
		if gs[g][0] + gs[g][1] > 0:
			out.append("%s %s: MoveEye %d× gemeldet, %d× übersehen" % [G[1], G[2], gs[g][0], gs[g][1]])
		else:
			out.append("%s %s: %d× erwischt" % [G[1], G[2], gs[g][2]])
	var ts := teach_sum()
	if ts > 0:
		out.append("🧠 Diese Runde hat MoveEye %d %s beigebracht" % [ts, "Ding" if ts == 1 else "Dinge"])
	elif not mw_on():
		out.append("🧠 MoveEye war nicht verbunden – diesmal hat es nichts gelernt")
	return out


func state_for(p: Dictionary) -> Dictionary:
	var d := {"seq": seq, "gear_on": gear_active() and p["role"] == "runner" and game.round_state in ["lobby", "end"], "gear": str(p.get("gear", ""))}
	if d["gear_on"]:
		d["gears"] = GEAR.map(func(g): return [g[0], g[1], g[2], g[3]])
	if wx_on and _mode_with_goal() and game.round_state in ["lobby", "end"]:
		d["wx_rule"] = "⛅ Wetterwechsel: Mitten in der Runde kommt ein Gewitter, Nebel oder die Dämmerung. 10 Sekunden vorher warnt dich dein Handy."
	if goal_mode() == "theft":
		var nm: String = theft.get("label", "das Velo") if not theft.is_empty() else "das Velo oder die Kühlbox"
		d["theft_rule"] = "🚲 Diebstahl: Schleich zu %s, nimm es mit und bring es zum orangen AUSGANG – ohne erwischt zu werden. Wer es trägt, ist langsamer. Wirst du erwischt, ist es wieder an seinem Platz. Am Schluss schaut MoveEye nach, ob es merkt, dass etwas fehlt." % nm
		d["carry_txt"] = ("%s %s dabei – schnell zum AUSGANG! " % [theft.get("icon", "🚲"), theft.get("short", "Beute")]) if bool(p.get("carry", false)) else ""
	if game.round_state == "end":
		d["lines"] = lines(false)                           # the own camouflage thing comes in «gear_res»
		d["teach"] = teach_text(str(p["name"]))
		d["gear_res"] = _gear_res(p)
	if game.round_state in ["lobby", "end"]:
		d["teachers"] = game.xp.teachers(5)
	return d


func spec_info() -> Dictionary:
	"""for MoveEye (spectators) and the window"""
	return {"seq": seq, "lines": lines(), "wx": wx.get("kind", "") if bool(wx.get("done", false)) else "", "theft": theft_text() if game.round_state == "end" else "",
			"teachers": game.xp.teachers(5)}


func report() -> Dictionary:
	"""into the game report of gamelearn (spielbericht.json)"""
	var st := _wx_stats()
	var gp := {}
	for p in game.players:
		if p != null and str(p.get("gear_round", "")) != "":
			gp[str(p["name"])] = str(p["gear_round"])
	return {"wetterwechsel": {"art": wx.get("kind", ""), "gekommen": bool(wx.get("done", false)),
				"vor": {"sichtbar": st["vor"][0], "gemeldet": st["vor"][1], "erwischt": int(wx_caught["vor"])},
				"nach": {"sichtbar": st["nach"][0], "gemeldet": st["nach"][1], "erwischt": int(wx_caught["nach"])}} if not wx.is_empty() else {},
			"tarnung": gp, "diebstahl": {"ding": theft.get("name", ""), "gestohlen": bool(theft.get("stolen", false)), "dieb": theft.get("thief", "")} if not theft.is_empty() else {}}


func debug() -> Dictionary:
	var ps := []
	for p in game.players:
		if p != null:
			ps.append([p["name"], str(p.get("gear", "")), snappedf(float(p["actor"].gear_speed), 0.01), int(p["actor"].gear_pmin), int(p["actor"].gear_pmax),
					bool(p.get("carry", false)), p.has("gear_node") and is_instance_valid(p["gear_node"])])
	var th := {}
	if not theft.is_empty():
		th = {"name": theft.get("name", ""), "by": theft.get("by", -1), "stolen": theft.get("stolen", false), "mw": theft.get("mw", ""),
				"scan": not (theft.get("scan", {}) as Dictionary).is_empty(), "cmp": not (theft.get("cmp", {}) as Dictionary).is_empty(),
				"pos": [snappedf(theft["pos"].x, 0.1), snappedf(theft["pos"].z, 0.1)] if theft.has("pos") else []}
	return {"ok": true, "cfg": cfg_get(), "goal_mode": goal_mode(), "wx": {"plan": wx.duplicate(), "phase": wx_phase, "caught": wx_caught,
			"weather": main.weather, "thunder": main.thunder, "hour": snappedf(main.hour(), 0.01), "dark": main.is_dark(), "sun_el": snappedf(main.sun_el(), 0.1)},
			"players": ps, "theft": th, "teach": teach, "lines": lines(), "teachers": game.xp.teachers(5)}


func op(d: Dictionary) -> Dictionary:
	"""CONTROL «gameplus» (tests): get · wx_now {kind} (the change in 11 s) · gear {slot, v} · take {slot} · goal {slot} · cfg {...}"""
	var o := str(d.get("op", "get"))
	var p = null
	if d.has("slot"):
		var s := clampi(int(d["slot"]), 0, game.MAX_P - 1)
		p = game.players[s]
	match o:
		"wx_now":
			if wx.is_empty() or bool(wx["done"]):
				return {"ok": false, "error": "no weather change (left) in this round"}
			if WX.has(str(d.get("kind", ""))):
				wx["kind"] = str(d["kind"])
			wx["at"] = now() + 11.0
		"gear":
			if p == null:
				return {"ok": false, "error": "no such player"}
			choose(p, str(d.get("v", "")))
		"take":
			if p == null:
				return {"ok": false, "error": "no such player"}
			p["actor"].position = game._g(main.free_spot(game.goal, 0.4, true))
		"exit":
			if p == null:
				return {"ok": false, "error": "no such player"}
			p["actor"].position = game._g(main.free_spot(EXIT + Vector3(0.6, 0, 0), 0.4, true))
		"cfg":
			cfg_set(d.get("cfg", {}) if typeof(d.get("cfg", {})) == TYPE_DICTIONARY else {})
	return debug()
