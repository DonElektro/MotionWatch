extends Node
## Paket «Tiere» (Realismus, 31.10.2026): die Tiere verhalten sich wie echte - wichtig für die Fehlalarme von MoveEye.
## Baut auf den vorhandenen Besuchern auf (actor.gd: Körper, Gang, Grasen / Schnüffeln / Wühlen, Reh liegt, Rotte, Hund an
## der Leine, Katze aufs Autodach - simreal.gd) und läuft nur mit «Tiere wie echt» (Besuch → Verhalten, simreal.anim_real).
## Nichts davon während eines Testlaufs / einer Messung (main.measuring(): vergleichbare Zahlen).
##   Fuchs      trabt gleichmässig (schnürt), bleibt stehen, lauscht und springt auf eine Maus (Mäusesprung), flieht ab 15 m
##   Reh        scheu: äugt ab ~45 m zu dem, der kommt (Kopf hoch, steht still), flüchtet ab ~25 m in Sprüngen,
##              bleibt nach 30–40 m nochmals stehen und schaut zurück
##   Wildschwein wühlt länger, die Rotte flieht gemeinsam
##   Katze      schleicht geduckt, springt (Beute), sitzt; vor einem Hund: aufs nächste Auto oder davon;
##              springt mit einem Bogen aufs Autodach (statt oben zu erscheinen, simreal «cat_roof»)
##   Hund       «frei laufend»: läuft vor, zurück und zur Seite, schnüffelt, holt im Galopp auf (an der Leine: simreal.gd)
##   Igel       langsam, schnüffelt; kommt jemand näher als ~2.5 m: rollt sich ein und bleibt 20–50 s so
##   Dachs      watschelt (wiegt sich), gräbt länger, flieht ab 8 m
##   Hase       drückt sich flach ins Gras, wenn jemand kommt, springt erst ganz nah auf und flieht im Zickzack
##   (Vögel am Boden: Krähen, Elstern, Möwen - fauna.gd, Schalter «Vögel am Tag»)
## Geschwindigkeiten (m/s, Gehen / Flucht): Fuchs 1.6 / 6, Reh 0.9 / 9, Wildschwein 1.0 / 5.5, Katze 1.0 / 4.5, Dachs 0.8 / 3,
## Hase 1.0 / 10, Igel 0.3 (Quellen: Wildtier Schweiz, «Fluchtdistanzen» z. B. Stankowich 2008, Biological Conservation 141:
## 2159–2173 - Huftiere 20–100 m vor Fussgängern; die Werte hier sind auf die kleinen Szenen des Simulators verkürzt).
## Tageszeiten: life.gd activity() (Tagesablauf) - neu: Winterschlaf / Winterruhe (season_k).
## Steuerbefehl: /control {"action": "tiere", "do": info | spawn (kind, from, to) | threat (x, z, secs) | curl | pounce}

var main
const Quality = preload("res://scripts/quality.gd")

# kind: [Gehen m/s, Flucht m/s, Fluchtdistanz vor Menschen m, aufmerksam ab m]
const PROFIL := {
	"fox": [1.6, 6.0, 15.0, 28.0],
	"deer": [0.9, 9.0, 25.0, 45.0],
	"boar": [1.0, 5.5, 12.0, 22.0],
	"cat": [1.0, 4.5, 2.5, 6.0],
	"badger": [0.8, 3.0, 8.0, 14.0],
	"hare": [1.0, 10.0, 6.0, 22.0],
	"hedgehog": [0.3, 0.3, 2.5, 4.0],
}
# who frightens whom (besides persons): the cat flees from dogs, the hedgehog rolls up before dogs, cats, foxes, badgers
const PREDATORS := {"cat": ["dog"], "hedgehog": ["dog", "cat", "fox", "badger"], "hare": ["dog", "fox"], "deer": ["dog"], "fox": ["dog"]}
# spawn kinds of this package: kind -> [German name, part of «Besuch»]
const KINDS := {
	"dog_free": ["Hund frei laufend mit seinem Menschen (läuft vor, zurück, schnüffelt)", "Menschen schicken"],
	"crows": ["Krähen am Boden (picken, fliegen auf)", "Tiere schicken"],
	"magpies": ["Elstern am Boden (hüpfen, fliegen auf)", "Tiere schicken"],
	"gulls": ["Möwen am Wasser (stehen, schwimmen, segeln)", "Tiere schicken"],
}
const EMOJI := {"dog_free": "🐕", "crows": "🐦", "magpies": "🐦", "gulls": "🕊"}

var _st := {}                       # instance id -> {v, st, t, tp, ...}
var _threats: Array = []            # [[position, kind, speed]] refreshed 4× per second
var _scan := 0.0
var _test_threat = null             # control «threat»: [position, until] - a person that is not there (tests)
var stats := {"alert": 0, "flee": 0, "curl": 0, "pounce": 0, "press": 0, "stalk": 0, "car_jump": 0, "lookback": 0}


func _ready() -> void:
	process_priority = 100          # after the visitors (actor.gd): the poses here are set on top of their animation


func active() -> bool:
	return main != null and main.simreal != null and main.simreal.anim_real and not main.measuring()


func is_kind(k: String) -> bool:
	return KINDS.has(k)


func add_controls() -> void:
	"""buttons in «Besuch» (the behaviour itself is switched with «Tiere wie echt», Besuch → Verhalten)"""
	for k in KINDS:
		var kk: String = k
		main.add_control("button", "tiere_" + kk, KINDS[kk][0], null, func(): main.spawn(kk), "Besuch", {"sub": KINDS[kk][1], "emoji": EMOJI.get(kk, "")})


func season_k(kind: String) -> float:
	"""winter: the hedgehog and the bats sleep (about mid-November to mid-March), the badger rests a lot (Winterruhe)"""
	var d: int = main.day_of_year()
	var winter := d >= 320 or d < 75
	if not winter:
		return 1.0
	match kind:
		"hedgehog", "bats":
			return 0.03
		"badger":
			return 0.35
	return 1.0


# ---- new spawn kinds -------------------------------------------------------------------------------------------------
func spawn_kind(kind: String, from, to) -> Node3D:
	match kind:
		"dog_free":
			var w = main.spawn("person", from, to)
			var dg = main.spawn("dog", w.position + Vector3(2.0, 0, -1.5), w.target)
			dg.leader = w
			dg.follow_off = Vector3(randf_range(-4.0, 4.0), 0, randf_range(-6.0, 1.0))
			dg.speed = 3.6                                   # gallops to the new place, then waits / sniffs there
			_state(dg)["st"] = "free"
			_state(dg)["t"] = Time.get_ticks_msec() / 1000.0 + randf_range(2.0, 5.0)
			return w
		"crows", "magpies", "gulls":
			if main.fauna != null:
				var b = main.fauna.ground_flock(kind, from)
				if b != null:
					return b
			return Node3D.new()
	return main.spawn("fox", from, to)


func on_spawn(v) -> void:
	"""main.spawn: a new visitor - animals get their real walking speed (only with «Tiere wie echt»)"""
	if not active() or not v.is_animal() or not PROFIL.has(v.kind):
		return
	v.speed = float(PROFIL[v.kind][0]) * randf_range(0.85, 1.15)


func _state(v) -> Dictionary:
	var id: int = v.get_instance_id()
	if not _st.has(id):
		_st[id] = {"v": v, "st": "", "t": 0.0, "next": Time.get_ticks_msec() / 1000.0 + randf_range(6.0, 20.0), "k": 0.0}
	return _st[id]


# ---- every frame -----------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or main.visitors == null or not main.sim_active:
		return
	if not active():
		_release_all(dt)
		return
	var now: float = Time.get_ticks_msec() / 1000.0          # the clock of the visitors (actor.now_s)
	_scan -= dt
	if _scan <= 0.0:
		_scan = 0.25
		_scan_threats(now)
	for v in main.visitors.get_children():
		if not v.has_method("is_animal") or not v.is_animal() or v.done or v.preview or v.controlled or v.puppet or v.stars != null:
			continue
		var s := _state(v)
		match str(v.kind):
			"deer":
				_deer(v, s, now, dt)
			"hare":
				_hare(v, s, now, dt)
			"fox":
				_fox(v, s, now, dt)
			"boar", "badger":
				_boar(v, s, now, dt)
			"cat":
				_cat(v, s, now, dt)
			"hedgehog":
				_hedgehog(v, s, now, dt)
			"dog":
				_dog(v, s, now, dt)
	if randf() < 0.02:                                       # forget the ones that are gone
		for id in _st.keys():
			if not is_instance_valid(_st[id]["v"]) or _st[id]["v"].done:
				_st.erase(id)


func _release_all(dt: float) -> void:
	"""«Tiere wie echt» off (or a test started): a rolled-up hedgehog unrolls, nothing else is held"""
	for id in _st.keys():
		var s: Dictionary = _st[id]
		var v = s["v"]
		if is_instance_valid(v) and float(s["k"]) > 0.0:
			s["k"] = maxf(0.0, float(s["k"]) - dt)
			_curl_pose(v, float(s["k"]))


func _scan_threats(now: float) -> void:
	"""who is around: persons (also the players), dogs, cats, foxes, badgers; moving cars"""
	_threats.clear()
	for v in main.visitors.get_children():
		if not v.has_method("is_animal") or v.done or v.preview:
			continue
		if v.kind == "person" or v.kind in ["dog", "cat", "fox", "badger"] or (v.kind == "car" and v.cur_speed > 1.0):
			_threats.append([v.global_position, str(v.kind), float(v.cur_speed), v])
	if _test_threat != null:
		if now < float(_test_threat[1]):
			_threats.append([_test_threat[0], "person", 1.2, null])
		else:
			_test_threat = null


func _nearest(v, kinds: Array) -> Array:
	"""[distance, position] of the nearest threat of these kinds (persons always), [1e9, null] if there is none"""
	var best := 1e9
	var bp = null
	for t in _threats:
		if t[3] == v:
			continue
		var k: String = t[1]
		if k == "person" or k in kinds or (k == "car" and v.kind in ["deer", "hare", "cat"]):
			var d: float = (t[0] as Vector3).distance_to(v.global_position)
			if k == "car":
				d *= 1.6                                     # a car on the road frightens less than a walker
			if d < best:
				best = d
				bp = t[0]
	return [best, bp]


func _siren() -> bool:
	return str(main.mw.get("sound", "")) != ""


func _flee(v, s: Dictionary, from_p, spd: float, zigzag := false) -> void:
	"""run away from from_p (a little to the side, not always straight back)"""
	if v.fled and str(s["st"]) in ["flee", "gone"]:
		return
	v.scare()                                                # fled = true, leader / route / idle cleared
	var away: Vector3 = v.global_position - (from_p if from_p != null else main.head.global_position)
	away.y = 0.0
	away = away.normalized() if away.length() > 0.1 else -v.dir
	away = away.rotated(Vector3.UP, randf_range(-0.45, 0.45))
	v.speed = spd * randf_range(0.85, 1.1)
	v.route.clear()
	if zigzag:                                               # the hare: hook after hook
		var side := Vector3(-away.z, 0, away.x)
		var p: Vector3 = v.position
		for i in range(7):
			p += away * randf_range(5.0, 8.0) + side * (randf_range(2.5, 4.5) * (1.0 if i % 2 == 0 else -1.0))
			v.route.append(p)
		v.target = v.route.pop_front()
	else:
		v.target = v.position + away * 70.0
	v.dir = (v.target - v.position).normalized()
	s["st"] = "flee"
	s["from"] = v.position
	stats["flee"] += 1


func _look_at_yaw(v, p: Vector3) -> float:
	var to: Vector3 = p - v.global_position
	return clampf(wrapf(atan2(-to.x, -to.z) - v.heading, -PI, PI), -1.3, 1.3)


# ---- the deer: shy, looks («äugt»), flees in bounds, stops once more and looks back ------------------------------------
func _deer(v, s: Dictionary, now: float, dt: float) -> void:
	var P: Array = PROFIL["deer"]
	var n := _nearest(v, PREDATORS["deer"])
	var d: float = n[0]
	match str(s["st"]):
		"":
			if v.leader != null and d > float(P[2]):
				return                                       # in a herd the lead deer decides (followers react when close)
			if _siren() or d < float(P[2]):
				_flee_deer(v, s, n[1], float(P[1]))
			elif d < float(P[3]) and now > float(s["t"]):
				s["st"] = "alert"
				s["tp"] = n[1]
				s["t"] = now + randf_range(3.0, 6.5)
				v.idle_kind = "alert"
				v.idle_until = s["t"]
				stats["alert"] += 1
		"alert":
			if n[1] != null:
				s["tp"] = n[1]
			if v.head != null and s.get("tp") != null:       # looks at the one who comes (actor.gd «alert» looks at the camera)
				v.head.rotation.y = lerpf(v.head.rotation.y, _look_at_yaw(v, s["tp"]), clampf(dt * 4.0, 0.0, 1.0))
			if _siren() or d < float(P[2]):
				_flee_deer(v, s, n[1], float(P[1]))
			elif now > float(s["t"]):
				s["st"] = ""
				s["t"] = now + randf_range(6.0, 15.0)        # calm again for a while (then looks again if still there)
		"flee":
			var from: Vector3 = s["from"]
			if v.position.distance_to(from) > randf_range(30.0, 40.0) and d > float(P[2]) * 1.4 and not s.has("looked"):
				s["looked"] = true                           # stops once more, turns the head back - then away
				v.idle_kind = "alert"
				v.idle_until = now + randf_range(2.0, 4.0)
				s["tp"] = n[1] if n[1] != null else from
				s["st"] = "lookback"
				stats["lookback"] += 1
		"lookback":
			if v.head != null and s.get("tp") != null:
				v.head.rotation.y = lerpf(v.head.rotation.y, _look_at_yaw(v, s["tp"]), clampf(dt * 4.0, 0.0, 1.0))
			if now > float(v.idle_until):
				s["st"] = "gone"


func _flee_deer(v, s: Dictionary, from_p, spd: float) -> void:
	"""one deer flees - the others of the herd (within 20 m) bound away with it"""
	_flee(v, s, from_p, spd)
	for o in main.visitors.get_children():
		if o != v and o.has_method("is_animal") and o.kind == "deer" and not o.fled and o.position.distance_to(v.position) < 20.0:
			_flee(o, _state(o), from_p, spd)


# ---- the hare: presses itself flat, bolts only when close, runs in a zigzag ---------------------------------------------
func _hare(v, s: Dictionary, now: float, _dt: float) -> void:
	var P: Array = PROFIL["hare"]
	var n := _nearest(v, PREDATORS["hare"])
	var d: float = n[0]
	match str(s["st"]):
		"":
			if _siren() or d < float(P[2]):
				_flee(v, s, n[1], float(P[1]), true)
			elif d < float(P[3]) and now > float(s["t"]):
				s["st"] = "press"
				v.idle_kind = "lie"                          # actor.gd: legs folded, body down - flat in the grass
				v.idle_until = now + 120.0
				v.wait_until = 0.0
				stats["press"] += 1
		"press":
			if _siren() or d < float(P[2]):
				v.idle_until = 0.0
				v.idle_kind = ""
				_flee(v, s, n[1], float(P[1]), true)
			elif d > float(P[3]) + 6.0:
				v.idle_until = now + 1.0                      # gone: gets up again
				s["st"] = ""
				s["t"] = now + 8.0


# ---- the fox: trots, flees early, listens and pounces on a mouse --------------------------------------------------------
func _fox(v, s: Dictionary, now: float, dt: float) -> void:
	var P: Array = PROFIL["fox"]
	var n := _nearest(v, PREDATORS["fox"])
	var d: float = n[0]
	match str(s["st"]):
		"":
			if _siren() or d < float(P[2]):
				if not (v.now_s() < v.idle_until and v.idle_kind in ["sniff", "root", "stare"]) or d < float(P[2]) * 0.5 or _siren():
					_flee(v, s, n[1], float(P[1]))           # busy at the bin / the food: it stays longer, only very close it runs
			elif now > float(s["next"]) and v.cur_speed > 0.3 and v.leader == null and v.route.size() < 6:
				s["next"] = now + randf_range(18.0, 45.0)
				s["st"] = "listen"                           # stops, head low and to the side: hears a mouse
				s["t"] = now + randf_range(1.2, 2.5)
				v.idle_kind = "sniff"
				v.idle_until = s["t"] + 1.0
		"listen":
			if d < float(P[2]):
				_flee(v, s, n[1], float(P[1]))
			elif now > float(s["t"]):
				s["st"] = "pounce"
				s["t"] = now
				v.wait_until = now + 0.75
				stats["pounce"] += 1
		"pounce":                                            # the mouse jump: up in a high arc, nose first into the grass
			var k: float = clampf((now - float(s["t"])) / 0.7, 0.0, 1.0)
			_jump_pose(v, k, 0.55, 1.1, dt)
			if k >= 1.0:
				s["st"] = ""
				v.idle_kind = "sniff"                        # eats
				v.idle_until = now + randf_range(1.5, 3.0)


func _jump_pose(v, k: float, h: float, dist: float, dt: float) -> void:
	"""a jump forward: arc of height h over the distance dist (k: 0 … 1), the body tips nose up, then nose down"""
	var fwd := Vector3(-sin(v.heading), 0, -cos(v.heading))
	v.position += fwd * dist * dt / 0.7 * (1.0 if k < 1.0 else 0.0)
	v.body_root.position.y = sin(k * PI) * h
	v.body_root.rotation.x = lerpf(0.55, -0.7, k) * sin(k * PI)
	for l in v.legs:                                         # front legs forward, hind legs stretched back
		l[0].rotation.x = (-0.9 if v.legs.find(l) < 2 else 0.8) * sin(k * PI)


# ---- wild boar and badger: root / dig longer, flee together, the badger waddles -----------------------------------------
func _boar(v, s: Dictionary, now: float, dt: float) -> void:
	var P: Array = PROFIL[v.kind]
	var n := _nearest(v, [])
	var d: float = n[0]
	if str(s["st"]) == "" and (_siren() or d < float(P[2])):
		_flee(v, s, n[1], float(P[1]))
		if v.kind == "boar":                                 # the sounder runs together
			for o in main.visitors.get_children():
				if o != v and o.has_method("is_animal") and o.kind == "boar" and not o.fled and o.position.distance_to(v.position) < 15.0:
					_flee(o, _state(o), n[1], float(P[1]))
		return
	if v.idle_kind == "root" and now < float(v.idle_until) and float(s.get("dug", -1.0)) != float(v.idle_until):
		v.idle_until += randf_range(4.0, 10.0)               # rooting / digging takes long: 6–15 s (not 2–5 like grazing)
		s["dug"] = float(v.idle_until)
	if v.kind == "badger" and v.cur_speed > 0.05:            # waddles: the body rocks from side to side
		v.body_root.rotation.z = lerpf(v.body_root.rotation.z, sin(v.phase) * 0.09 * clampf(v.cur_speed, 0.0, 1.0), clampf(dt * 10.0, 0.0, 1.0))
	elif v.kind == "badger":
		v.body_root.rotation.z = lerpf(v.body_root.rotation.z, 0.0, clampf(dt * 4.0, 0.0, 1.0))


# ---- the cat: stalks, pounces, sits; from a dog onto a car or away ------------------------------------------------------
func _cat(v, s: Dictionary, now: float, dt: float) -> void:
	var P: Array = PROFIL["cat"]
	if str(s["st"]) in ["", "stalk"] and v.position.y < 0.3 and (_is_dog_near(v, 8.0) or _siren()):
		var car = _car_near(v.global_position, 9.0)
		if s.has("spd"):
			v.speed = float(s["spd"])
		if car != null and not _siren():
			cat_jump_car(v, car)
		else:
			_flee(v, s, _nearest(v, ["dog"])[1], float(P[1]))
		return
	match str(s["st"]):
		"":
			if now > float(s["next"]) and v.cur_speed > 0.2 and v.leader == null and not v.has_meta("on_car"):
				s["next"] = now + randf_range(15.0, 35.0)
				s["st"] = "stalk"                            # creeps low and slow towards something in the grass
				s["t"] = now + randf_range(4.0, 8.0)
				s["spd"] = v.speed
				v.speed = 0.3
				stats["stalk"] += 1
		"stalk":
			v.body_root.position.y = lerpf(v.body_root.position.y, -0.07, clampf(dt * 6.0, 0.0, 1.0))
			if v.head != null:
				v.head.rotation.x = lerpf(v.head.rotation.x, 0.15, clampf(dt * 4.0, 0.0, 1.0))
			if now > float(s["t"]):
				v.speed = float(s.get("spd", 1.0))
				s["st"] = "pounce"
				s["t"] = now
				v.wait_until = now + 0.75
		"pounce":
			var k: float = clampf((now - float(s["t"])) / 0.7, 0.0, 1.0)
			_jump_pose(v, k, 0.25, 0.8, dt)
			if k >= 1.0:
				s["st"] = ""
				v.idle_kind = "sit"
				v.idle_until = now + randf_range(3.0, 7.0)
		"car_up", "car_down":
			_car_jump_tick(v, s, now)


func _is_dog_near(v, r: float) -> bool:
	for t in _threats:
		if t[1] == "dog" and (t[0] as Vector3).distance_to(v.global_position) < r:
			return true
	return false


func _car_near(p: Vector3, r: float):
	if main.simreal == null:
		return null
	var best = null
	var bd := r
	for c in main.simreal._cars:
		if is_instance_valid(c) and c.is_inside_tree():
			var d: float = Vector2(c.global_position.x - p.x, c.global_position.z - p.z).length()
			if d < bd:
				bd = d
				best = c
	return best


func cat_jump_car(v, car: Node3D, sit := -1.0) -> void:
	"""the cat walks to the side of the car, jumps up in an arc (0.45 s), sits on the roof, later jumps down again"""
	var s := _state(v)
	var side: Vector3 = car.global_transform.basis.x.normalized()
	if (v.global_position - car.global_position).dot(side) < 0.0:
		side = -side
	var roof: Vector3 = car.global_transform * Vector3(0, 1.42, 0.25)
	var foot: Vector3 = Vector3(roof.x, 0, roof.z) + side * 1.15
	v.leader = null
	v.route = [[foot, 0.4, 0.0, Vector3(roof.x, 0, roof.z)]]
	v.target = foot
	v.speed = maxf(v.speed, 2.5 if v.fled else 1.0)
	v.next_idle = Time.get_ticks_msec() / 1000.0 + 999.0
	s["st"] = "car_up"
	s["phase"] = "walk"
	s["roof"] = roof
	s["foot"] = foot
	s["sit"] = sit if sit > 0.0 else randf_range(18.0, 40.0)
	s["away"] = car.global_position - side * 25.0
	v.set_meta("on_car", true)
	stats["car_jump"] += 1


func _car_jump_tick(v, s: Dictionary, now: float) -> void:
	var roof: Vector3 = s["roof"]
	var foot: Vector3 = s["foot"]
	match str(s["phase"]):
		"walk":                                              # at the car: crouches, then jumps
			if Vector2(v.position.x - foot.x, v.position.z - foot.z).length() < 0.45 or v.route.is_empty():
				s["phase"] = "up"
				s["t"] = now + 0.35
				v.route.clear()
				v.target = Vector3(roof.x, 0, roof.z)
				v.wait_until = now + 99.0
				v.dir = (Vector3(roof.x, 0, roof.z) - Vector3(v.position.x, 0, v.position.z)).normalized()
		"up":
			var k: float = clampf((now - float(s["t"])) / 0.45, 0.0, 1.0)
			if now < float(s["t"]):
				v.body_root.position.y = -0.05                # ducks before the jump
				return
			var p: Vector3 = foot.lerp(Vector3(roof.x, 0, roof.z), k)
			v.position = Vector3(p.x, roof.y * k + sin(k * PI) * 0.35, p.z)
			v.body_root.rotation.x = 0.5 * sin(k * PI)
			if k >= 1.0:
				s["phase"] = "sit"
				s["t"] = now + float(s["sit"])
				v.idle_kind = "sit"
				v.idle_until = s["t"]
		"sit":
			v.position.y = roof.y
			if v.head != null:
				v.head.rotation.y = lerpf(v.head.rotation.y, _look_at_yaw(v, main.head.global_position) * (0.5 + 0.5 * sin(now * 0.4)), 0.05)
			if now > float(s["t"]) and not _is_dog_near(v, 6.0):
				s["phase"] = "down"
				s["t"] = now
				var off: Vector3 = foot - Vector3(roof.x, 0, roof.z)
				s["down"] = Vector3(roof.x, 0, roof.z) - off   # jumps down on the other side
				v.dir = off.normalized() * -1.0
		"down":
			var k2: float = clampf((now - float(s["t"])) / 0.5, 0.0, 1.0)
			var q: Vector3 = Vector3(roof.x, 0, roof.z).lerp(s["down"], k2)
			v.position = Vector3(q.x, roof.y * (1.0 - k2) + sin(k2 * PI) * 0.2, q.z)
			if k2 >= 1.0:
				v.position.y = 0.0
				v.wait_until = 0.0
				v.idle_until = 0.0
				v.route = [s["away"]]
				v.target = s["down"] + (s["away"] - s["down"]).normalized() * 3.0
				v.next_idle = now + randf_range(4.0, 10.0)
				v.remove_meta("on_car")
				s["st"] = ""
				s["next"] = now + randf_range(10.0, 30.0)


# ---- the hedgehog: rolls itself into a ball ------------------------------------------------------------------------------
func _hedgehog(v, s: Dictionary, now: float, dt: float) -> void:
	var P: Array = PROFIL["hedgehog"]
	var n := _nearest(v, PREDATORS["hedgehog"])
	match str(s["st"]):
		"":
			if (float(n[0]) < float(P[2]) or (_siren() and v.global_position.distance_to(main.head.global_position) < 15.0)) and now > float(s["t"]):
				curl(v, randf_range(20.0, 50.0))
			elif float(s["k"]) > 0.0:
				s["k"] = maxf(0.0, float(s["k"]) - dt * 0.5)    # unrolls slowly
				_curl_pose(v, float(s["k"]))
		"curl":
			s["k"] = minf(1.0, float(s["k"]) + dt * 2.0)
			_curl_pose(v, float(s["k"]))
			if now > float(s["t"]):
				if float(n[0]) < float(P[2]):
					s["t"] = now + randf_range(5.0, 12.0)    # still somebody there: stays a ball
					v.wait_until = s["t"]
				else:
					s["st"] = ""
					s["t"] = now + 12.0
					v.wait_until = now + 2.5                    # unrolls, then trots on


func curl(v, secs: float) -> void:
	var s := _state(v)
	s["st"] = "curl"
	s["t"] = Time.get_ticks_msec() / 1000.0 + secs
	v.wait_until = s["t"]
	v.idle_until = 0.0
	v.idle_kind = ""
	stats["curl"] += 1


func _curl_pose(v, k: float) -> void:
	"""0 = walking … 1 = a ball of spines: head and legs in, rounder and a little lower"""
	if v.body_root == null:
		return
	var sc: float = v.body_root.scale.x
	v.body_root.scale = Vector3(sc, sc * (1.0 + 0.18 * k), sc * (1.0 - 0.3 * k))
	v.body_root.position.y = -0.035 * k
	if v.head != null:
		v.head.scale = Vector3.ONE * maxf(0.05, 1.0 - 0.95 * k)
		v.head.position.z = -0.2 + 0.1 * k
	for l in v.legs:
		l[0].scale = Vector3.ONE * maxf(0.05, 1.0 - 0.95 * k)


# ---- the free dog: runs ahead, back and to the side, sniffs, catches up -----------------------------------------------
func _dog(v, s: Dictionary, now: float, _dt: float) -> void:
	if str(s["st"]) != "free":
		return
	if v.leader == null or not is_instance_valid(v.leader):
		return
	if now > float(s["t"]):
		s["t"] = now + randf_range(3.0, 9.0)
		var r := randf()
		if r < 0.3:
			v.idle_kind = "sniff"                            # stays and sniffs - the person walks on, then it runs after
			v.idle_until = now + randf_range(2.0, 5.0)
		elif r < 0.45:
			v.follow_off = Vector3(randf_range(-1.0, 1.0), 0, randf_range(0.5, 1.5))   # back to its person
		else:
			v.follow_off = Vector3(randf_range(-7.0, 7.0), 0, randf_range(-10.0, 3.0))  # ahead and to the side
		v.speed = randf_range(2.8, 4.5)


# ---- control API / info ----------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var list := []
	for id in _st:
		var s: Dictionary = _st[id]
		var v = s["v"]
		if not is_instance_valid(v) or v.done:
			continue
		list.append({"kind": v.kind, "st": s["st"], "x": snappedf(v.position.x, 0.1), "y": snappedf(v.position.y, 0.01), "z": snappedf(v.position.z, 0.1),
				"spd": snappedf(v.cur_speed, 0.01), "want": snappedf(v.speed, 0.01), "fled": v.fled, "idle": v.idle_kind if v.now_s() < v.idle_until else "",
				"curl": snappedf(float(s["k"]), 0.01), "h": snappedf(v.body_h, 0.01)})
	return {"on": active(), "animals": list, "stats": stats, "birds": main.fauna.ground_info() if main.fauna != null else [],
			"lite": Quality.lite()}


func control(d: Dictionary) -> Dictionary:
	"""control API {action: tiere, do: info | spawn (kind, from, to) | threat (x, z, secs) | curl | pounce}"""
	var op := str(d.get("do", "info"))
	var now: float = Time.get_ticks_msec() / 1000.0
	match op:
		"spawn":
			var f = d.get("from", null)
			var t = d.get("to", null)
			var v = main.spawn(str(d.get("kind", "fox")), Vector3(float(f[0]), 0, float(f[1])) if f is Array else null, Vector3(float(t[0]), 0, float(t[1])) if t is Array else null)
			if v != null and d.has("speed") and v.get("speed") != null:
				v.speed = float(d["speed"])
		"threat":                                            # a person standing at (x, z) for a while - for tests
			_test_threat = [Vector3(float(d.get("x", 0.0)), 0, float(d.get("z", -5.0))), now + float(d.get("secs", 10.0))]
			_scan = 0.0
		"curl":
			for v in main.visitors.get_children():
				if v.has_method("is_animal") and v.kind == "hedgehog":
					curl(v, float(d.get("secs", 20.0)))
		"pounce":
			for v in main.visitors.get_children():
				if v.has_method("is_animal") and v.kind in ["fox", "cat"]:
					var s := _state(v)
					s["next"] = now
		"car":
			for v in main.visitors.get_children():
				if v.has_method("is_animal") and v.kind == "cat":
					var c = _car_near(v.global_position, 60.0)
					if c != null:
						cat_jump_car(v, c, float(d.get("secs", 15.0)))
	return {"ok": true, "tiere": info()}
