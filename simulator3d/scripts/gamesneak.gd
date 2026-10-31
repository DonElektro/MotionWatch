extends RefCounted
## «Neue Werkzeuge» für die Schleicher (Gameplay ausfeilen, Punkt 7, Daniel 31.10.2026) - with energy, ONE rule like the guard
## (gametools.gd): every tool has a price ⚡ and a cooldown, the energy comes back slowly.
##   🐾 Lockmittel  30 ⚡, 25 s   a food bowl lands ~6 m ahead, an animal (cat / hedgehog by day, fox / marten at night)
##                                comes to it (objekte_plus.gd send_lure) - the automatic head and the Bot-Wächter look
##                                there, the guard gets a hint marker 🐾 («da bewegt sich etwas»), MoveEye sees a real animal
##   🧺 Verstecken  20 ⚡, 15 s   crouched or crawling at a hiding object (the washing line, the small tent - one of each is
##                                put on the way at the start of the round): HIDE_S seconds invisible, but standing still
## The guard's new tools (💫 Licht-Schwenk, 🔊 Geräusch-Ping) are in gametools.gd.
## Phone: two more buttons (gamemore PHONE_JS), PC: T = Lockmittel, H = Verstecken (localplay.gd).

const T = preload("res://scripts/i18n.gd")
const Obj = preload("res://scripts/objects.gd")
const MAX := 60.0
const REGEN := 0.25                      # ⚡ per second
const TOOLS := [["lure", "🐾", "Lockmittel", 30, 25.0], ["hide", "🧺", "Verstecken", 20, 15.0]]
const HIDE_S := 6.0
const HIDE_R := 1.7
const LURE_LOOK := 6.0                   # seconds the automatic head / the bot guard look at the animal

var game
var main
var more
var st := {}                             # slot -> {"e", "cd": {tool: t}, "used": {tool: n}}
var spots: Array = []                    # hiding objects: {"node", "pos", "kind", "name"}
var lures: Array = []                    # [node, until]
var log_: Array = []


func on() -> bool:
	return more.on("game_runtools") and not main.game_mode in ["free", "jaeger", "seek", "escape"] and not game.jaeger.on()


func now() -> float:
	return game.now()


func _s(sl: int) -> Dictionary:
	if not st.has(sl):
		st[sl] = {"e": MAX, "cd": {}, "used": {}}
	return st[sl]


func _tool(id: String) -> Array:
	for t in TOOLS:
		if t[0] == id:
			return t
	return []


# ---- round ----------------------------------------------------------------------------------------------------------------
func round_start() -> void:
	st.clear()
	log_.clear()
	clear()
	if not on():
		return
	var st0: Vector3 = game.start_point(0)
	var g: Vector3 = game.goal
	for k in [["laundry_line", 0.35, "Wäscheleine"], ["tent", 0.62, "Zelt"]]:
		var c: Vector3 = st0.lerp(g, float(k[1])) + Vector3(randf_range(-5.0, 5.0), 0, randf_range(-3.0, 3.0))
		var pos: Vector3 = main.free_spot(c, 1.6, true)
		pos.y = main.ground_y(pos.x, pos.z)
		var n: Node3D = Obj.build(main, "laundry_line") if k[0] == "laundry_line" else _tent()
		n.position = pos
		n.rotation.y = randf() * TAU
		game.root.add_child(n)
		spots.append({"node": n, "pos": pos, "kind": k[0], "name": T.t(k[2])})


func _tent() -> Node3D:
	"""a small dome tent (two sloped walls and a floor - cheap, also on the Pi)"""
	var n := Node3D.new()
	n.name = "spiel_zelt"
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.22, 0.42, 0.3)
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	for sgn in [-1.0, 1.0]:
		var w := MeshInstance3D.new()
		var q := BoxMesh.new()
		q.size = Vector3(0.04, 1.35, 2.0)
		w.mesh = q
		w.material_override = mt
		w.position = Vector3(sgn * 0.45, 0.55, 0)
		w.rotation.z = sgn * deg_to_rad(38.0)
		n.add_child(w)
	var back := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(1.75, 1.1, 0.04)
	back.mesh = pm
	back.material_override = mt
	back.position = Vector3(0, 0.55, -1.0)
	n.add_child(back)
	return n


func clear() -> void:
	for s in spots:
		if is_instance_valid(s["node"]):
			s["node"].queue_free()
	spots.clear()
	for l in lures:
		if is_instance_valid(l[0]):
			l[0].queue_free()
	lures.clear()


func round_end() -> void:
	clear()
	for p in game.players:
		if p != null:
			p.erase("rt_hide")


func tick(dt: float) -> void:
	if game.round_state != "play" or not on():
		return
	for k in st:
		st[k]["e"] = minf(MAX, float(st[k]["e"]) + REGEN * dt)
	var t := now()
	for l in lures.duplicate():
		if t > float(l[1]):
			if is_instance_valid(l[0]):
				l[0].queue_free()
			lures.erase(l)
	for p in game.players:                                 # a hide ends when time is up or the player moves / stands up
		if p == null or not p.has("rt_hide"):
			continue
		var H: Dictionary = p["rt_hide"]
		var a = p["actor"]
		if t > float(H["until"]) or a.ctl_posture == 0 or a.position.distance_to(H["at"]) > 0.6 or p["state"] != "play":
			p.erase("rt_hide")
			game._say(p, T.t("🧺 Raus aus dem Versteck"), 1.5)


# ---- using a tool -------------------------------------------------------------------------------------------------------
func use(p: Dictionary, id: String) -> Dictionary:
	var Tl := _tool(id)
	if Tl.is_empty():
		return {"ok": false, "error": "unknown tool"}
	if not on():
		return {"ok": false, "error": T.t("Werkzeuge für Schleicher sind aus (Assistent → Extras)")}
	if p["role"] != "runner" or p["state"] != "play" or game.round_state != "play":
		return {"ok": false, "error": T.t("Nur während einer Runde")}
	var s := _s(int(p["slot"]))
	var left := float(s["cd"].get(id, 0.0)) - now()
	var err := ""
	if left > 0.0:
		err = T.t("%s lädt noch %d s", [T.t(Tl[2]), int(ceil(left))])
	elif float(s["e"]) < float(Tl[3]):
		err = T.t("Zu wenig Energie für %s (%d ⚡ nötig)", [T.t(Tl[2]), int(Tl[3])])
	var a = p["actor"]
	var spot := {}
	if err == "" and id == "hide":
		if a.ctl_posture == 0:
			err = T.t("🧺 Zuerst ducken oder kriechen")
		else:
			for sp in spots:
				if a.position.distance_to(sp["pos"]) < HIDE_R:
					spot = sp
			if spot.is_empty():
				err = T.t("🧺 Kein Versteck in der Nähe – such die Wäscheleine oder das Zelt")
	if err != "":
		game._say(p, "⏳ " + err, 2.0)
		return {"ok": false, "error": err}
	var txt := ""
	match id:
		"lure":
			var fw := Vector3(-sin(float(p["yaw"])), 0, -cos(float(p["yaw"])))
			var at: Vector3 = main.free_spot(a.position + fw * 6.0, 0.4, true)
			at.y = main.ground_y(at.x, at.z)
			var bowl: Node3D = Obj.build(main, "food_bowl")
			bowl.position = at
			game.root.add_child(bowl)
			lures.append([bowl, now() + 40.0])
			var dark: bool = main.is_dark()
			var kinds := ["fox", "marten", "hedgehog"] if dark else ["cat", "hedgehog"]
			var kind: String = kinds[randi() % kinds.size()]
			var ang := randf() * TAU
			var start: Vector3 = at + Vector3(cos(ang), 0, sin(ang)) * 12.0
			var v = main.spawn(kind, start, at)
			if v != null:
				v.route = [[at, 12.0, 0.0, at], at + Vector3(cos(ang + 2.4), 0, sin(ang + 2.4)) * 20.0]
			game.attention = at
			game.attention_until = now() + LURE_LOOK
			game.tools.add_hint(at, "lure", LURE_LOOK, -1)
			for g in game.players:
				if g != null and g["role"] == "guard":
					game._say(g, T.t("🐾 Da bewegt sich etwas … (ein Tier?)"), 2.5)
			txt = T.t("🐾 Lockmittel geworfen – gleich kommt ein Tier und lenkt ab")
			log_.append([snappedf(now() - float(game.t_start), 0.1), int(p["slot"]), "lure", kind])
		"hide":
			p["rt_hide"] = {"until": now() + HIDE_S, "at": a.position, "spot": spot["name"]}
			txt = T.t("🧺 Versteckt bei %s – %d s, nicht bewegen!", [spot["name"], int(HIDE_S)])
			log_.append([snappedf(now() - float(game.t_start), 0.1), int(p["slot"]), "hide", spot["name"]])
	s["e"] = maxf(0.0, float(s["e"]) - float(Tl[3]))
	s["cd"][id] = now() + float(Tl[4])
	s["used"][id] = int(s["used"].get(id, 0)) + 1
	game._say(p, txt, 3.0)
	game.news("%s – %s" % [txt, p["name"]])
	return {"ok": true, "text": txt}


func hidden(p: Dictionary) -> bool:
	return p.has("rt_hide") and now() <= float(p["rt_hide"]["until"])


func info_for(p: Dictionary) -> Dictionary:
	if not on() or p["role"] != "runner":
		return {}
	var s := _s(int(p["slot"]))
	var ts := []
	for Tl in TOOLS:
		var left := maxf(0.0, float(s["cd"].get(Tl[0], 0.0)) - now())
		ts.append([Tl[0], Tl[1], T.t(Tl[2]), int(Tl[3]), int(ceil(left)), left <= 0.0 and float(s["e"]) >= float(Tl[3])])
	var near := ""
	for sp in spots:
		if p["actor"].position.distance_to(sp["pos"]) < HIDE_R:
			near = sp["name"]
	return {"e": int(floor(float(s["e"]))), "max": int(MAX), "t": ts, "hid": hidden(p), "near": near, "lab": T.t("⚡ Energie")}


func hud_text(p: Dictionary) -> String:
	var I := info_for(p)
	if I.is_empty():
		return ""
	var o := "⚡ %d" % int(I["e"])
	for t in I["t"]:
		o += " · %s %s %s" % [t[1], t[2], T.t("bereit") if bool(t[5]) else ("%d s" % int(t[4]) if int(t[4]) > 0 else "–")]
	return o


func debug() -> Dictionary:
	var o := {}
	for k in st:
		o[k] = {"e": snappedf(float(st[k]["e"]), 0.1), "used": st[k]["used"]}
	return {"on": on(), "st": o, "spots": spots.map(func(s): return [s["name"], snappedf(s["pos"].x, 0.1), snappedf(s["pos"].z, 0.1)]),
			"lures": lures.size(), "log": log_,
			"hidden": game.players.filter(func(q): return q != null and q.has("rt_hide")).map(func(q): return q["name"])}
