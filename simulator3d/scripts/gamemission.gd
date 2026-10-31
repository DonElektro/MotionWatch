extends RefCounted
## «Missionen mit Gegenständen» (Gameplay ausfeilen, Punkt 4, Daniel 31.10.2026): the game goal «🎒 Mission» with the things of
## the catalogue (objekte_neu.gd / objects.gd - built with Obj.build, nothing new to draw):
##   wallet  👛 Portemonnaie vom Campingtisch holen und zum eigenen Start bringen (Tisch beim grünen Licht)
##   fruit   🍎 5 Früchte (Apfel, Orange, Birne, Banane) einsammeln und in den Brotkorb beim grünen Licht bringen
##   parcel  📦 Paket holen (liegt irgendwo auf dem Platz) und zum grünen Licht bringen – wer es trägt, ist langsamer
## Caught with the thing: it goes back to its place (fruits: one falls back somewhere). The arrow of the phone and the bots
## follow the mission (target_of). Done = «Im Ziel» like the other goals (+ MISSION_BONUS).
## Called by gamemore.gd: start / tick (from the referee, every 0.2 s per runner) / on_caught / target_of / clear.

const Obj = preload("res://scripts/objects.gd")
const T = preload("res://scripts/i18n.gd")

const KINDS := [["wallet", "👛", "Portemonnaie holen", "Hol das Portemonnaie vom Campingtisch beim grünen Licht und bring es zu deinem Start zurück."],
		["fruit", "🍐", "5 Früchte sammeln", "Sammle 5 Früchte auf dem Platz und bring sie in den Korb beim grünen Licht."],
		["parcel", "📦", "Paket wegbringen", "Hol das Paket (Pfeil) und bring es zum grünen Licht. Wer es trägt, ist langsamer."]]
const FRUITS := ["apple", "orange", "pear", "banana", "apple"]
const NEED := 5
const MISSION_BONUS := 300
const PARCEL_SPEED := 0.85

var game
var main
var kind := ""                           # this round: wallet | fruit | parcel ("" = no mission)
var nodes: Array = []                    # everything built for the mission (freed at the end)
var wallet := {}                         # {"node", "home": Vector3, "by": slot}
var parcel := {}
var fruits: Array = []                   # {"node", "pos", "by": slot}
var done_n := 0


static func options() -> Array:
	var o := [["auto", "🎲 zufällig"]]
	for k in KINDS:
		o.append([k[0], "%s %s" % [k[1], k[2]]])
	return o


func info_of(k: String) -> Array:
	for e in KINDS:
		if e[0] == k:
			return e
	return []


func active() -> bool:
	return kind != "" and main.game_goal == "mission"


# ---- building -------------------------------------------------------------------------------------------------------------
func _put(k: String, pos: Vector3, scale := 1.0) -> Node3D:
	var n: Node3D = Obj.build(main, k)
	n.position = Vector3(pos.x, main.ground_y(pos.x, pos.z), pos.z)
	n.scale = Vector3.ONE * scale
	game.root.add_child(n)
	nodes.append(n)
	return n


func _ring(pos: Vector3, c: Color) -> Node3D:
	"""a soft ring on the ground, so the small thing is found (only the players see the world like this)"""
	var m := MeshInstance3D.new()
	var t := TorusMesh.new()
	t.inner_radius = 0.42
	t.outer_radius = 0.5
	m.mesh = t
	m.material_override = game._glow(c)
	m.position = Vector3(pos.x, main.ground_y(pos.x, pos.z) + 0.03, pos.z)
	game.root.add_child(m)
	nodes.append(m)
	return m


func start(choice: String) -> void:
	clear()
	if main.game_goal != "mission":
		return
	var ks := ["wallet", "fruit", "parcel"]
	kind = choice if choice in ks else ks[randi() % ks.size()]
	done_n = 0
	var g: Vector3 = game.goal
	match kind:
		"wallet":
			var tb := _put("camp_table", g + Vector3(0.0, 0, 0.0))
			tb.rotation.y = randf() * TAU
			var w := _put("wallet", g, 1.6)
			w.position.y += 0.72
			wallet = {"node": w, "home": w.position, "by": -1}
		"fruit":
			var n := NEED * clampi(game.runners_n(), 1, 3)
			for i in range(n):
				var pos: Vector3 = game._spot_far(3.0)
				var f := _put(FRUITS[i % FRUITS.size()], pos, 2.6)
				var r := _ring(pos, Color(1.0, 0.8, 0.25, 0.5))
				fruits.append({"node": f, "ring": r, "pos": pos, "by": -1})
			_put("bread_basket", g + Vector3(0.6, 0, 0.0), 2.0)
		"parcel":
			var best := Vector3.ZERO
			for _i in range(8):                            # far from the goal, but not at the starts
				var c: Vector3 = game._spot_far(4.0)
				if c.distance_to(g) > best.distance_to(g):
					best = c
			var pc := _put("parcel", best, 1.0)
			_ring(best, Color(1.0, 0.65, 0.2, 0.5))
			parcel = {"node": pc, "home": pc.position, "by": -1}
	for p in game.players:
		if p != null:
			p["ms_n"] = 0
			p["ms_carry"] = false
			p["ms_ok"] = false
	var I := info_of(kind)
	game.news(T.t("🎒 Mission: %s", [T.t(I[2])]))
	for p in game.players:
		if p != null and p["role"] == "runner":
			game._say(p, "%s %s" % [I[1], T.t(I[3])], 6.0)


func clear() -> void:
	for n in nodes:
		if is_instance_valid(n):
			n.queue_free()
	nodes.clear()
	wallet = {}
	parcel = {}
	fruits.clear()
	kind = ""


# ---- the referee ----------------------------------------------------------------------------------------------------------
func _carry_node(p: Dictionary, n: Node3D) -> void:
	var a = p["actor"]
	n.reparent(a, false)
	n.transform = Transform3D(Basis.IDENTITY.scaled(n.scale), Vector3(0, 0.82, -0.36))


func _back(n: Node3D, home: Vector3) -> void:
	if not is_instance_valid(n):
		return
	var sc := n.scale
	n.reparent(game.root, false)
	n.transform = Transform3D(Basis.IDENTITY.scaled(sc), home)


func tick(p: Dictionary) -> int:
	"""0 = no mission, 1 = the mission is the goal (the normal goal does not count), 2 = done just now"""
	if not active():
		return 0
	var a = p["actor"]
	var pos: Vector3 = a.position
	var sl := int(p["slot"])
	match kind:
		"wallet", "parcel":
			var M: Dictionary = wallet if kind == "wallet" else parcel
			if M.is_empty():
				return 1
			if int(M["by"]) == sl:
				var to: Vector3 = game.start_point(sl) if kind == "wallet" else game.goal
				if pos.distance_to(to) < (2.6 if kind == "wallet" else 1.9):
					_done(p)
					return 2
			elif int(M["by"]) < 0 and pos.distance_to(M["node"].global_position) < 1.6:
				M["by"] = sl
				p["ms_carry"] = true
				_carry_node(p, M["node"])
				if kind == "parcel":
					a.gear_speed = float(a.gear_speed) * PARCEL_SPEED
				game._say(p, T.t("👛 Portemonnaie geschnappt – zurück zu deinem Start!") if kind == "wallet" else T.t("📦 Paket dabei – bring es zum grünen Licht!"), 3.5)
				game.news(T.t("%s %s hat %s", [info_of(kind)[1], p["name"], T.t("das Portemonnaie") if kind == "wallet" else T.t("das Paket")]))
				game._event(p, "item")
			elif int(M["by"]) >= 0 and pos.distance_to(M["node"].global_position) < 1.6:
				game._say(p, T.t("Jemand anderes trägt es schon – lenk die Kamera ab!"), 1.2)
		"fruit":
			for f in fruits:
				if int(f["by"]) < 0 and int(p.get("ms_n", 0)) < NEED and pos.distance_to(f["pos"]) < 1.2:
					f["by"] = sl
					f["node"].visible = false
					f["ring"].visible = false
					p["ms_n"] = int(p.get("ms_n", 0)) + 1
					game._say(p, T.t("🍐 Frucht %d/%d", [int(p["ms_n"]), NEED]) + ("  " + T.t("– jetzt zum Korb beim grünen Licht!") if int(p["ms_n"]) >= NEED else ""), 2.5)
					game._event(p, "item")
			if int(p.get("ms_n", 0)) >= NEED and pos.distance_to(game.goal) < 1.9:
				_done(p)
				return 2
	return 1


func _done(p: Dictionary) -> void:
	var I := info_of(kind)
	var sl := int(p["slot"])
	for M in [wallet, parcel]:
		if not M.is_empty() and int(M["by"]) == sl:
			M["by"] = -1
			_back(M["node"], M["home"])                    # a new one lies there for the next
	if kind == "parcel":
		game.plus._speed(p)
	p["ms_carry"] = false
	p["ms_ok"] = true
	done_n += 1
	p["bonus"] = int(p.get("bonus", 0)) + MISSION_BONUS
	p["state"] = "goal"
	p["t_goal"] = game.now()
	p["actor"].frozen = true
	game._say(p, T.t("🎒 Mission geschafft! (+%d)", [MISSION_BONUS]), 4.0)
	game.news(T.t("🎒 %s hat die Mission geschafft: %s", [p["name"], T.t(I[2])]))
	main.spectate_cut("cheer", sl, T.t("🎒 %s: Mission geschafft!", [p["name"]]))
	p["actor"].play_emote("goal", 5.0)
	game._event(p, "goal")
	game.paint()


func on_caught(p: Dictionary) -> void:
	if not active():
		return
	var sl := int(p["slot"])
	for M in [wallet, parcel]:
		if not M.is_empty() and int(M["by"]) == sl:
			M["by"] = -1
			_back(M["node"], M["home"])
			if kind == "parcel":
				game.plus._speed(p)
			game._say(p, T.t("Erwischt – das Ding ist wieder an seinem Platz"), 3.0)
	p["ms_carry"] = false
	if kind == "fruit" and int(p.get("ms_n", 0)) > 0:      # one fruit falls back, somewhere else
		p["ms_n"] = int(p["ms_n"]) - 1
		for f in fruits:
			if int(f["by"]) == sl:
				var np: Vector3 = game._spot_far(3.0)
				f["pos"] = np
				f["by"] = -1
				f["node"].position = Vector3(np.x, main.ground_y(np.x, np.z), np.z)
				f["node"].visible = true
				f["ring"].position = Vector3(np.x, main.ground_y(np.x, np.z) + 0.03, np.z)
				f["ring"].visible = true
				break


func target_of(p: Dictionary, t: Vector3) -> Vector3:
	if not active() or p["role"] != "runner":
		return t
	var sl := int(p["slot"])
	var pos: Vector3 = p["actor"].position
	match kind:
		"wallet":
			return game.start_point(sl) if int(wallet.get("by", -1)) == sl else game.goal
		"parcel":
			return game.goal if int(parcel.get("by", -1)) == sl else (parcel["node"].global_position if not parcel.is_empty() else t)
		"fruit":
			if int(p.get("ms_n", 0)) >= NEED:
				return game.goal
			var best := t
			var bd := 1e9
			for f in fruits:
				if int(f["by"]) < 0 and pos.distance_to(f["pos"]) < bd:
					bd = pos.distance_to(f["pos"])
					best = f["pos"]
			return best
	return t


func text_for(p: Dictionary) -> String:
	if not active() or p["role"] != "runner":
		return ""
	var sl := int(p["slot"])
	match kind:
		"wallet":
			return T.t("👛 Portemonnaie dabei – zu deinem Start!") if int(wallet.get("by", -1)) == sl else T.t("👛 Mission: Portemonnaie vom Tisch holen (Pfeil)")
		"parcel":
			return T.t("📦 Paket dabei – zum grünen Licht!") if int(parcel.get("by", -1)) == sl else T.t("📦 Mission: Paket holen (Pfeil)")
		"fruit":
			var n := int(p.get("ms_n", 0))
			return T.t("🍐 Früchte %d/%d – jetzt zum Korb!", [n, NEED]) if n >= NEED else T.t("🍐 Früchte %d/%d (Pfeil zur nächsten)", [n, NEED])
	return ""


func score_info(p: Dictionary) -> String:
	if kind == "" or p["role"] != "runner":
		return ""
	if bool(p.get("ms_ok", false)):
		return T.t("🎒 Mission geschafft (+%d)", [MISSION_BONUS])
	if kind == "fruit":
		return T.t("🍐 %d/%d Früchte", [int(p.get("ms_n", 0)), NEED])
	return T.t("🎒 Mission nicht geschafft")


func debug() -> Dictionary:
	return {"kind": kind, "active": active(), "done": done_n, "wallet": [wallet.get("by", -1)] if not wallet.is_empty() else [],
			"parcel": [parcel.get("by", -1), parcel["node"].global_position.x, parcel["node"].global_position.z] if not parcel.is_empty() else [],
			"fruits": fruits.map(func(f): return [snappedf(f["pos"].x, 0.1), snappedf(f["pos"].z, 0.1), f["by"]]),
			"wallet_pos": [wallet["node"].global_position.x, wallet["node"].global_position.z] if not wallet.is_empty() else []}
