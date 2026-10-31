extends Node
## 3D-4.x «Neue Szenen» (Daniel, 30.10.2026, docs/Neue_Szenen_Plan.md): three scenes that train weak points of MoveEye,
## each with a fixed test run (testrun.gd plans «camping_voll», «tarnen», «velodieb», pruefstand.py) and a game idea.
##  1. «Voller Campingplatz»: many harmless neighbours on their own pitches and on the path (cooking, to the toilet block,
##     children playing, a dog walk) - only who comes to YOUR pitch counts (zones / «Dein Platz»). The neighbours are
##     figures of actor.gd / figur.gd below the scene node: they stay through test runs and game rounds (main.clear_visitors
##     does not touch them) and are never part of the truth of a test run - a push while only neighbours are in the
##     picture is «falsch (Nachbar)». Game: the sneakers mix with the neighbours (goal: your tent).
##  2. «Tarnen und Kriechen»: dry meadow in the colours of the camouflage clothes, persons in camouflage that crawl, behind
##     an umbrella, under a cardboard box (the things of gameplus.gd, built by the same code). Game: camouflage is stronger
##     here (gameplus.ai_mul), bots always take a thing.
##  3. «Velodieb»: fast in, grab the bike (the bike tag sensor «Velo» fires - main.add_event), away. The test run measures
##     the reaction time from the grab to the push. Game: thief against guard against the clock (preset «szene_velo»).
## Building: static build_scene (called from scenes.gd with the Scenes object); the rest is the node (main.szenen).

var main

const IDS := ["camping_voll", "tarnen", "velodieb"]
# the matching game of the scene (gamewiz.gd: an extra quick card on the first step) [preset, icon, title, text]
const GAME := {"camping_voll": ["szene_voll", "🏕", "Unter den Nachbarn", "Schleich zum Zelt (grünes Licht) und misch dich unter die Nachbarn: die Kamera sieht viele harmlose Leute – fällst du auf? MoveEye passt auf, 2 Bots laufen mit."],
		"tarnen": ["szene_tarnen", "🌿", "Tarnen und Kriechen", "Nimm Tarnkleidung, Schirm oder Karton (vor der Runde wählen) und kriech zum Zelt. Hier hilft die Tarnkleidung mehr – aber nur am Tag. MoveEye passt auf."],
		"velodieb": ["szene_velo", "🚲", "Velodieb gegen Wächter", "Ein Wächter mit Auslöser, Licht und Sirene, die anderen sind Velodiebe: schnell hin, Velo schnappen (der Velo-Sensor meldet es!), weg zum Ausgang – 2 Minuten."]}
const GOAL := {"camping_voll": "pir", "tarnen": "pir", "velodieb": "bike"}     # game._pick_goal: where the green light is
# spawn kinds (main.spawn(kind) - test runs, «Besuch», visitors by themselves): kind -> [German name, part of «Besuch»]
const KINDS := {"platz_besuch": ["Fremder kommt vom Weg an deinen Platz (Zelt, dann Velo)", "Abläufe"],
		"tarn_robben": ["Tarnkleidung: geduckt, dann robbt er am Boden", "Abläufe"],
		"tarn_schirm": ["Geduckt hinter einem Regenschirm", "Abläufe"],
		"tarn_karton": ["Unter einem Karton (eine Kiste, die sich bewegt)", "Abläufe"],
		"velodieb": ["Velodieb: rennt hin, schnappt das Velo, rennt weg (Velo-Sensor)", "Abläufe"]}
const CAMO_GROUND := Color(0.35, 0.36, 0.22)      # the ground of «Tarnen» (like the camouflage clothes of actor.gd)
const ActorS = preload("res://scripts/actor.gd")

var nb: Array = []            # neighbours: {"kind", "home", "a": [actors], "t": next change}
var tracked: Array = []       # visitors of this file: {"v", "kind", "t0", "enter", "grab", "gone"}
var events: Array = []        # for the test run: {"kind", "id", "t" (testrun clock), "what"}
var _dark := false
var _bed := false             # 22:30 - 6:30: the neighbours sleep (only the walks to the toilet go on)
var _ph := ""                 # 3D-4.x: who sleeps now (_phase) - neighbours with own hours (kompakt.gd «runde»)
var _tick := 0.0
var _bike_copy_of = null      # the original bike while a thief has the copy


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


static func is_new(id: String) -> bool:
	return id in IDS


# =======================================================================================================================
# building (static: the Scenes object s builds, like its own scenes)
# =======================================================================================================================
static func build_scene(s, id: String) -> void:
	match id:
		"camping_voll":
			_voll(s)
		"tarnen":
			_tarnen(s)
		"velodieb":
			_velo(s)


static func _tent(s, p: Vector3, rot: float, col: Color, own := false) -> Node3D:
	var tn: Node3D = s.node(s.root, p, rot)
	var tent := PrismMesh.new()
	tent.size = Vector3(2.6, 1.5, 2.4)
	var wf = s.m.get("wind_fx")                                     # F6: the fabric moves in the wind (wind_fx.gd)
	s.put(tn, tent, Vector3(0, 0.75, 0), col if wf == null else wf.tent_mat(col, 1.5), "tent")
	var fly := PrismMesh.new()
	fly.size = Vector3(2.9, 1.58, 2.0)
	s.put(tn, fly, Vector3(0, 0.78, 0), col.darkened(0.18) if wf == null else wf.tent_mat(col.darkened(0.18), 1.58), "tent")
	var door := PrismMesh.new()
	door.size = Vector3(0.9, 0.9, 0.02)
	s.put(tn, door, Vector3(0, 0.45, 1.21), Color(0.15, 0.1, 0.08), "tent")
	s.m.add_obstacle_node(tn, Vector3.ZERO, 3.0, 2.8)
	s.m.set_obstacle_height(1.4)
	if own:
		s.m.obj["pir"] = p
		s.m.test_props["Zelt"] = tn
	return tn


static func _table(s, p: Vector3, rot: float, chairs := 2) -> void:
	var t: Node3D = s.node(s.root, p, rot)
	s.put(t, s.m.box(1.2, 0.05, 0.8), Vector3(0, 0.72, 0), Color(0.8, 0.8, 0.78), "stone")
	for x in [-0.5, 0.5]:
		for z in [-0.3, 0.3]:
			s.put(t, s.cyl(0.015, 0.015, 0.7, 5), Vector3(x, 0.36, z), Color(0.6, 0.6, 0.62), "stone")
	for i in range(chairs):
		var cz: float = -0.75 if i % 2 == 0 else 0.75
		s.put(t, s.m.box(0.45, 0.05, 0.45), Vector3(-0.3 + 0.6 * (i / 2), 0.45, cz), Color(0.2, 0.35, 0.55), "tent")
		s.put(t, s.m.box(0.45, 0.45, 0.04), Vector3(-0.3 + 0.6 * (i / 2), 0.7, cz + (0.22 if cz > 0 else -0.22)), Color(0.2, 0.35, 0.55), "tent")
	s.m.add_obstacle(p, 0.8)
	s.m.set_obstacle_height(0.8)


static func _own_things(s, tbl_p: Vector3, grill_p: Vector3) -> void:
	"""table, cool boxes and grill of your pitch (the test aids and the theft game take them)"""
	var tbl: Node3D = s.node(s.root, Vector3.ZERO)
	var cbx: Node3D = s.node(s.root, Vector3.ZERO)
	s.m.test_props["Tisch"] = tbl
	s.m.test_props["Kühlboxen"] = cbx
	s.put(tbl, s.m.box(1.2, 0.05, 0.8), tbl_p + Vector3(0, 0.72, 0), Color(0.8, 0.8, 0.78), "stone")
	for x in [-0.5, 0.5]:
		for z in [-0.3, 0.3]:
			s.put(tbl, s.cyl(0.015, 0.015, 0.7, 5), tbl_p + Vector3(x, 0.36, z), Color(0.6, 0.6, 0.62), "stone")
	for sd in [-1, 1]:
		var cp: Vector3 = tbl_p + Vector3(1.1 * sd, 0, 0.2)
		s.put(cbx, s.m.box(0.45, 0.45, 0.45), cp + Vector3(0, 0.23, 0), Color(0.15, 0.3, 0.6), "tent")
		s.m.add_obstacle(cp, 0.35)
	s.m.add_obstacle(tbl_p, 0.7)
	var gr: Node3D = s.node(s.root, grill_p)
	s.m.test_props["Grill"] = gr
	for k in range(3):
		var a_ := TAU * k / 3.0
		s.put(gr, s.cyl(0.015, 0.015, 0.75, 5), Vector3(cos(a_) * 0.2, 0.36, sin(a_) * 0.2), Color(0.2, 0.2, 0.2), "stone", Vector3(sin(a_) * 0.25, 0, -cos(a_) * 0.25))
	s.put(gr, s.sph(0.3, 0.3), Vector3(0, 0.78, 0), Color(0.08, 0.08, 0.08), 45.0)
	s.m.add_obstacle(grill_p, 0.4)
	s.m.set_obstacle_height(0.6)


static func _post_rope(s, pts: Array) -> void:
	"""low wooden posts with a rope between - the border of your pitch (you can step over it)"""
	for i in range(pts.size()):
		var p: Vector3 = pts[i]
		s.put(s.root, s.m.box(0.08, 0.6, 0.08), p + Vector3(0, 0.3, 0), Color(0.5, 0.36, 0.2), "tree")
		if i + 1 < pts.size():
			var q: Vector3 = pts[i + 1]
			var d: Vector3 = q - p
			s.put(s.root, s.m.box(0.02, 0.02, d.length()), (p + q) * 0.5 + Vector3(0, 0.52, 0), Color(0.9, 0.85, 0.7), "tree", Vector3(0, atan2(d.x, d.z), 0))


static func _gravel(s, c: Vector3, sx: float, sz: float, rot := 0.0) -> void:
	s.put(s.root, s.m.box(sx, 0.03, sz), c + Vector3(0, 0.015, 0), Color(0.56, 0.53, 0.46), "road", Vector3(0, rot, 0))


# ---- 1. «Voller Campingplatz» ---------------------------------------------------------------------------------------------
static func _voll(s) -> void:
	"""your pitch in front of the camera (4 - 11 m, posts and a rope), behind it the path (14 m), behind the path a row of
	neighbours' pitches, a toilet block on the left, a play meadow behind; neighbours also left and right of you"""
	var m = s.m
	s.road(-44.0)
	_post_rope(s, [Vector3(-8, 0, -2.5), Vector3(-8, 0, -12), Vector3(8, 0, -12), Vector3(8, 0, -2.5)])
	_tent(s, m.pos_of(26.0, 7.5), deg_to_rad(-20.0), Color(0.9, 0.5, 0.15), true)      # right: the path stays in the picture
	s.bike(m.pos_of(-20.0, 6.0), deg_to_rad(20.0) + PI / 2)
	_own_things(s, m.pos_of(-36.0, 8.5), m.pos_of(42.0, 5.0))
	s.caravan(m.pos_of(-48.0, 9.5), deg_to_rad(15.0))                       # the door sensor (caravan of the neighbour on the left? no: yours)
	_gravel(s, Vector3(0, 0, -14.8), 140.0, 2.6)                            # the path in front of your pitch
	_gravel(s, Vector3(-26.0, 0, -19.0), 2.4, 7.0)                          # to the toilet block
	var wc: Node3D = s.hut(Vector3(-26.0, 0, -24.5), 0.0, Color(0.88, 0.88, 0.85))
	wc.scale = Vector3(1.6, 1.1, 1.3)
	s.label(s.root, "WC / Dusche", Vector3(-26.0, 3.3, -22.3), 64)
	for x in [-20.0, 0.0, 20.0]:
		s.lamp_post(Vector3(x, 0, -16.6), 3.6)
	# the row of neighbours behind the path: tents, caravans, cars, tables
	var cols := [Color(0.2, 0.45, 0.25), Color(0.25, 0.35, 0.65), Color(0.75, 0.2, 0.15), Color(0.85, 0.75, 0.25)]
	var row := [[-16.0, "tent"], [-6.0, "car_tent"], [5.0, "tent"], [15.0, "caravan_car"], [26.0, "tent"]]
	for i in range(row.size()):
		var x: float = row[i][0]
		match str(row[i][1]):
			"tent":
				_tent(s, Vector3(x, 0, -23.0), s.rng.randf_range(-0.3, 0.3), cols[i % cols.size()])
			"car_tent":
				_tent(s, Vector3(x - 1.5, 0, -24.0), 0.1, cols[(i + 1) % cols.size()])
				s.static_car(Vector3(x + 2.5, 0, -24.5), 0.0, Color(0.75, 0.75, 0.78))
			"caravan_car":
				s.static_car(Vector3(x - 2.5, 0, -25.0), 0.0, Color(0.2, 0.3, 0.5))
				var cv: Node3D = s.node(s.root, Vector3(x + 1.8, 0, -25.0), PI / 2)
				s.put(cv, s.m.box(4.2, 2.3, 2.1), Vector3(0, 1.35, 0), Color(0.92, 0.92, 0.88), "caravan")
				s.put(cv, s.m.box(1.0, 0.6, 0.04), Vector3(0.8, 1.6, 1.07), Color(0.25, 0.3, 0.38), "caravan")
				m.add_obstacle_box(Vector3(x + 1.8, 0, -25.0), 2.3, 4.4, PI / 2)
				m.set_obstacle_height(2.3)
		_table(s, Vector3(x + 0.5, 0, -20.0), s.rng.randf_range(-0.2, 0.2), 2 + i % 3)
	# neighbours right and left of you (beside the camera, mostly outside the picture)
	_tent(s, Vector3(-17.0, 0, -4.0), 0.6, Color(0.55, 0.25, 0.55))
	_table(s, Vector3(-14.5, 0, -7.5), 0.3, 2)
	s.static_car(Vector3(17.0, 0, -3.0), 0.2, Color(0.6, 0.12, 0.1))
	_tent(s, Vector3(17.5, 0, -8.5), -0.4, Color(0.3, 0.55, 0.6))
	s.laundry(Vector3(-11.5, 0, -10.5), deg_to_rad(80.0))
	s.flag(Vector3(21.0, 0, -18.0), Color(0.15, 0.4, 0.8))
	# the play meadow behind the row: a small goal
	for gx in [10.0, 13.0]:
		s.put(s.root, s.cyl(0.04, 0.04, 1.2, 6), Vector3(gx, 0.6, -34.0), Color(0.95, 0.95, 0.95), "stone")
	s.put(s.root, s.cyl(0.04, 0.04, 3.0, 6), Vector3(11.5, 1.2, -34.0), Color(0.95, 0.95, 0.95), "stone", Vector3(0, 0, PI / 2))
	s.meadow(600, 3.0, 45.0, func(p: Vector3): return absf(p.z + 14.8) < 1.6)
	for i in range(60):
		s.tree(s.root, m.pos_of(s.rng.randf_range(-180, 180), s.rng.randf_range(38, 110)), s.rng.randf_range(0.8, 1.4))
	s.data["platz"] = [Vector3(0, 0, -7.2), 8.0]                          # your pitch: centre, radius (for the test report)
	s.data["weg_z"] = -14.8
	s.data["wc"] = Vector3(-26.0, 0, -21.6)
	# [kind, home]: koch = cooks at his table · wc = walks along the path to the toilet block (also at night, with a torch)
	# kinder = two children play on the meadow · hund = a walk with the dog along the path · sitz = sits at the table
	s.data["nachbarn"] = [["koch", Vector3(-6.0, 0, -19.0)], ["koch", Vector3(15.5, 0, -19.2)], ["wc", Vector3(-15.5, 0, -19.5)],
			["wc", Vector3(5.5, 0, -19.5)], ["kinder", Vector3(11.5, 0, -30.0)], ["hund", Vector3(17.0, 0, -11.5)],
			["sitz", Vector3(-14.0, 0, -6.5)], ["wc", Vector3(26.5, 0, -20.0)]]


# ---- 2. «Tarnen und Kriechen» -------------------------------------------------------------------------------------------
static func _tarnen(s) -> void:
	"""a dry meadow in olive and brown (the colours of the camouflage clothes), tall grass, low bushes, earth patches;
	your tent, the bike and a caravan for the door sensor"""
	var m = s.m
	s.road(-52.0)
	s.put(s.root, m.box(150.0, 0.02, 120.0), Vector3(0, 0.01, -30.0), CAMO_GROUND, "ground")       # the dry meadow
	for i in range(70):                                                    # earth and dark patches (like the camo patches)
		var p: Vector3 = m.pos_of(s.rng.randf_range(-80, 80), s.rng.randf_range(3.0, 40.0))
		var c: Color = [Color(0.38, 0.3, 0.18), Color(0.22, 0.24, 0.13), Color(0.3, 0.3, 0.2)][i % 3]
		s.put(s.root, m.box(s.rng.randf_range(1.0, 3.5), 0.02, s.rng.randf_range(0.8, 2.5)), p + Vector3(0, 0.022, 0), c, "ground", Vector3(0, s.rng.randf() * TAU, 0))
	_tent(s, m.pos_of(30.0, 10.0), deg_to_rad(-25.0), Color(0.35, 0.42, 0.25), true)             # an olive tent (right: the meadow stays free)
	s.bike(m.pos_of(-24.0, 11.0), deg_to_rad(70.0))
	_own_things(s, m.pos_of(-42.0, 7.0), m.pos_of(46.0, 6.0))
	s.caravan(m.pos_of(48.0, 12.0), deg_to_rad(-25.0))
	# tall dry grass in clumps (hides a crawling person a little), low bushes, a woodpile, a few stones
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.5, 0.46, 0.26)
	gm.cull_mode = BaseMaterial3D.CULL_DISABLED
	for i in range(45):
		var p: Vector3 = m.pos_of(s.rng.randf_range(-70, 70), s.rng.randf_range(5.0, 30.0))
		if p.distance_to(m.obj["pir"]) < 3.0:
			continue
		var n: Node3D = s.node(s.root, p, s.rng.randf() * TAU)
		for k in range(5):
			var bl := PrismMesh.new()
			bl.size = Vector3(0.5, s.rng.randf_range(0.5, 0.9), 0.04)
			s.put(n, bl, Vector3(s.rng.randf_range(-0.3, 0.3), bl.size.y * 0.5, s.rng.randf_range(-0.3, 0.3)), gm, "tree", Vector3(0, k * 0.7, s.rng.randf_range(-0.2, 0.2)))
	for p in [Vector3(-7, 0, -15), Vector3(6, 0, -18), Vector3(13, 0, -12), Vector3(-15, 0, -22), Vector3(2, 0, -26)]:
		s.prop("bush", p, s.rng.randf() * TAU)
	s.prop("woodpile", Vector3(-12.0, 0, -15.0), 0.3)
	s.stones(10, 5.0, 22.0)
	s.meadow(250, 3.0, 35.0)
	for i in range(70):
		s.tree(s.root, m.pos_of(s.rng.randf_range(-180, 180), s.rng.randf_range(35, 110)), s.rng.randf_range(0.8, 1.5))
	s.data["platz"] = [m.pos_of(30.0, 10.0), 6.0]


# ---- 3. «Velodieb» ------------------------------------------------------------------------------------------------------
static func _velo(s) -> void:
	"""the edge of a campsite by a road: your bike at a rack in the picture (8 m), the road and a hedge gap where a thief
	comes from, a lamp by the rack (light at night), your tent and caravan"""
	var m = s.m
	s.road(-26.0, 6.0)
	_gravel(s, Vector3(2.0, 0, -15.0), 4.0, 18.0)                           # the gravel way from the road to the pitches
	for x in [-26.0, -14.0, 18.0, 30.0]:                                    # hedges along the road, with the gap at the way
		s.prop("hedge", Vector3(x, 0, -21.5), 0.0)
	var rack: Vector3 = m.pos_of(9.0, 8.0)
	for k in range(4):                                                      # the bike rack: four hoops
		var hp: Vector3 = rack + Vector3(-1.2 + k * 0.8, 0, -0.6)
		var tor := TorusMesh.new()
		tor.inner_radius = 0.36
		tor.outer_radius = 0.4
		s.put(s.root, tor, hp + Vector3(0, 0.4, 0), Color(0.6, 0.6, 0.62), "stone", Vector3(0, 0, PI / 2))
	s.bike(rack + Vector3(1.6, 0, -0.6), PI / 2 + 0.05)                     # a bike of the neighbours (not the one to watch)
	s.bike(rack + Vector3(-1.6, 0, -0.6), PI / 2 - 0.08)
	s.bike(rack + Vector3(0.0, 0, -0.6), PI / 2)                            # YOUR bike (the last one is the watched one)
	s.lamp_post(rack + Vector3(-2.6, 0, -1.4), 3.4)
	_tent(s, m.pos_of(-55.0, 7.0), deg_to_rad(30.0), Color(0.2, 0.45, 0.7), true)       # left, outside the picture of the head
	_own_things(s, m.pos_of(-80.0, 6.0), m.pos_of(62.0, 5.0))
	s.caravan(m.pos_of(-72.0, 13.0), deg_to_rad(25.0))
	s.static_car(Vector3(14.0, 0, -12.0), 0.1, Color(0.85, 0.85, 0.82))
	s.meadow(500, 3.0, 40.0, func(p: Vector3): return absf(p.z + 26.0) < 3.5 or (absf(p.x - 2.0) < 2.2 and p.z > -24.0 and p.z < -6.0))
	for i in range(80):
		s.tree(s.root, m.pos_of(s.rng.randf_range(-180, 180), s.rng.randf_range(32, 110)), s.rng.randf_range(0.8, 1.5))
	s.data["platz"] = [m.pos_of(-30.0, 7.0), 7.0]
	s.data["dieb_wege"] = [Vector3(2.0, 0, -30.0), Vector3(-34.0, 0, -9.0), Vector3(34.0, 0, -10.0)]   # where a thief comes from / goes to


# =======================================================================================================================
# the node: neighbours, special visitors, test run numbers, game hints
# =======================================================================================================================
func on_scene() -> void:
	"""main._build_scene: the neighbours of «Voller Campingplatz» (the old ones went with the scene node)"""
	nb.clear()
	tracked.clear()
	events.clear()
	_bike_copy_of = null
	_dark = main.is_dark()
	_bed = _bedtime()
	_ph = ""
	var sc = main.scenes
	if sc == null or sc.root == null:
		return
	for e in sc.data.get("nachbarn", []):
		var n := {"kind": str(e[0]), "home": e[1], "a": [], "t": now() + randf_range(2.0, 30.0)}
		if e.size() > 2 and typeof(e[2]) == TYPE_DICTIONARY:
			n["opt"] = e[2]                             # 3D-4.x «runde» (kompakt.gd): pts, actor, wach [from, to], spd, wait
		nb.append(n)
		_make(n)


func _actor(kind: String, from: Vector3, to: Vector3, spd: float) -> Node3D:
	var v = main.Actor.new()
	main.scenes.root.add_child(v)
	v.setup(main, kind, from, to, spd)
	v.set_night(main.is_dark())
	v.set_meta("nachbar", true)
	return v


func _make(n: Dictionary) -> void:
	var h: Vector3 = n["home"]
	var sp: Vector3 = main.free_spot(h, 0.4, true)
	match str(n["kind"]):
		"runde":                                        # 3D-4.x (kompakt.gd): one figure (person, child, dog, cow …) walks between points
			var o: Dictionary = n.get("opt", {})
			n["a"].append(_actor(str(o.get("actor", "person")), sp, sp + Vector3(0.5, 0, 0.5), float(o.get("spd", randf_range(1.0, 1.4)))))
		"kinder":
			for i in range(2):
				var c = _actor("child", sp + Vector3(i * 1.2, 0, 0), sp + Vector3(2, 0, 1), randf_range(1.8, 2.4))
				n["a"].append(c)
		"hund":
			var w = _actor("person", sp, sp + Vector3(0, 0, -1), 1.2)
			var dg = _actor("dog", sp + Vector3(0.8, 0, 0.8), sp, 1.8)
			if main.simreal != null:
				main.simreal.leash(w, dg)
			else:
				dg.leader = w
			n["a"].append(w)
			n["a"].append(dg)
		_:
			var v = _actor("elderly" if str(n["kind"]) == "sitz" and randf() < 0.5 else "person", sp, sp + Vector3(0.5, 0, 0.5), randf_range(1.0, 1.3))
			if str(n["kind"]) == "wc":
				v.add_torch()
				v.set_night(main.is_dark())
			n["a"].append(v)
	for v in n["a"]:
		v.route = [[sp, randf_range(1.0, 6.0), 0.0]]
	if _sleeping(n):
		_sleep(n, true)
	_plan(n)


func _bedtime() -> bool:
	var h: float = main.hour()
	return h >= 22.5 or h < 6.5


func _sleeping(n: Dictionary) -> bool:
	"""at night most neighbours are in their tents - only the walks to the toilet go on"""
	if n.has("opt") and (n["opt"] as Dictionary).has("wach"):      # 3D-4.x: own hours (festival until 3, the farm dog always)
		var w: Array = n["opt"]["wach"]
		var h: float = main.hour()
		var a := float(w[0])
		var b := float(w[1])
		return not ((h >= a and h < b) if a <= b else (h >= a or h < b))
	return _bed and str(n["kind"]) != "wc"


func _phase() -> String:
	"""what decides who sleeps: bedtime and the own hours (changes -> to bed / up again)"""
	var out := "1" if _bedtime() else "0"
	for n in nb:
		out += "1" if _sleeping(n) else "0"
	return out


func _plan(n: Dictionary) -> void:
	"""the next piece of the neighbour's day (appended to the route, so the figure never ends its way)"""
	var h: Vector3 = n["home"]
	var lead = n["a"][0]
	if not is_instance_valid(lead):
		return
	if _sleeping(n):
		return
	var wz: float = float(main.scenes.data.get("weg_z", h.z + 4.0))
	match str(n["kind"]):
		"runde":                                       # 3D-4.x: to one of its points, a while there, a few steps (kompakt.gd)
			var o: Dictionary = n.get("opt", {})
			var pts: Array = o.get("pts", [])
			var p: Vector3 = h if pts.is_empty() or randf() < 0.25 else pts[randi() % pts.size()]
			var wt: Array = o.get("wait", [4.0, 30.0])
			var r := float(o.get("r", 1.5))
			lead.route.append([main.free_spot(p + Vector3(randf_range(-r, r), 0, randf_range(-r, r)), 0.4, true), randf_range(float(wt[0]), float(wt[1])), 0.0])
		"koch":                                        # at the table and the grill: a few steps, bends over, stands
			for i in range(3):
				var p: Vector3 = main.free_spot(h + Vector3(randf_range(-1.6, 1.6), 0, randf_range(-1.2, 1.2)), 0.4, true)
				lead.route.append([p, randf_range(4.0, 14.0), 0.5 if randf() < 0.3 else 0.0])
		"sitz":
			lead.route.append([main.free_spot(h + Vector3(randf_range(-0.8, 0.8), 0, randf_range(-0.8, 0.8)), 0.4, true), randf_range(15.0, 40.0), 0.0])
		"wc":                                          # home -> the path -> the toilet block, a while there, back
			var wc: Vector3 = main.scenes.data.get("wc", h + Vector3(-10, 0, 0))
			var stay := randf_range(25.0, 90.0) if not _bed else randf_range(90.0, 240.0)
			lead.route.append([h, stay, 0.0])
			lead.route.append(Vector3(h.x, 0, wz + randf_range(-0.6, 0.6)))
			lead.route.append(Vector3(wc.x + 0.4, 0, wz))
			lead.route.append([wc, randf_range(15.0, 35.0), 0.0])
			lead.route.append(Vector3(wc.x - 0.4, 0, wz))
			lead.route.append(Vector3(h.x, 0, wz + randf_range(-0.6, 0.6)))
		"kinder":                                      # running about on the meadow
			for c in n["a"]:
				if is_instance_valid(c):
					for i in range(3):
						c.route.append([h + Vector3(randf_range(-6, 6), 0, randf_range(-4, 4)), randf_range(0.0, 2.5), 0.0])
		"hund":                                        # a round: along the path, behind the row, back
			lead.route.append([h, randf_range(30.0, 90.0), 0.0])
			lead.route.append(Vector3(h.x, 0, wz))
			lead.route.append(Vector3(-38.0, 0, wz))
			lead.route.append(Vector3(-38.0, 0, wz - 15.0))
			lead.route.append(Vector3(36.0, 0, wz - 15.0))
			lead.route.append(Vector3(36.0, 0, wz))
			lead.route.append(Vector3(h.x, 0, wz))


func _sleep(n: Dictionary, on: bool) -> void:
	var h: Vector3 = n["home"]
	for v in n["a"]:
		if not is_instance_valid(v):
			continue
		v.visible = not on
		if on:
			v.route = [[h, 1.0e6, 0.0]]
			v.position = main.free_spot(h, 0.4, true)
			v.target = v.position
			v.wait_until = v.now_s() + 1.0e6
		else:
			v.wait_until = 0.0
			v.route = [[v.position, randf_range(1.0, 8.0), 0.0]]


func _process(dt: float) -> void:
	if main == null or main.scenes == null:
		return
	_tick -= dt
	if _tick > 0.0:
		return
	_tick = 0.25
	var t := now()
	var dk: bool = main.is_dark()
	if dk != _dark:                                     # dusk / dawn: torches on / off
		_dark = dk
		for n in nb:
			for v in n["a"]:
				if is_instance_valid(v):
					v.set_night(dk)
	_bed = _bedtime()
	var ph := _phase()
	if ph != _ph:                                       # to bed, up again
		_ph = ph
		for n in nb:
			_sleep(n, _sleeping(n))
			_plan(n)
	for n in nb:
		var ok := true
		for v in n["a"]:
			if not is_instance_valid(v) or v.is_queued_for_deletion() or v.done:
				ok = false
		if not ok:                                      # gone (should not happen): make the neighbour again
			for v in n["a"]:
				if is_instance_valid(v):
					v.queue_free()
			n["a"] = []
			_make(n)
			continue
		if _sleeping(n):
			continue
		for v in n["a"]:
			if v.leader == null and v.route.size() < 2:
				_plan(n)
				break
	_track(t)


# ---- special visitors ----------------------------------------------------------------------------------------------------
func is_kind(k: String) -> bool:
	return KINDS.has(k)


func _cross(d: float) -> Array:
	"""a way across the picture of the head camera at d m (like testrun._route): [from, to]"""
	var cam: Camera3D = main.cams[0]
	var o: Vector3 = cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var r := Vector3(-f.z, 0, f.x)
	var side := 1.0 if randf() < 0.5 else -1.0
	var half: float = d * 0.68 + 5.0
	var a: Vector3 = o + f * d - r * side * half
	var b: Vector3 = o + f * d + r * side * half
	return [Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z)]


func spawn_kind(kind: String, from, to) -> Node3D:
	var v: Node3D = null
	match kind:
		"platz_besuch":
			v = _platz_besuch(from, to)
		"tarn_robben", "tarn_schirm", "tarn_karton":
			v = _tarn(kind, from, to)
		"velodieb":
			if _game_on():
				v = main.spawn("person", from, to)        # during a game round the players steal the bike, not a visitor
				return v
			v = _velodieb()
	if v != null:
		tracked.append({"v": v, "kind": kind, "id": v.get_instance_id(), "t0": now(), "enter": -1.0, "grab": -1.0, "gone": -1.0})
	return v


func _pitch() -> Array:
	var pl = main.scenes.data.get("platz", null)
	if pl is Array:
		return pl
	return [main.obj["pir"], 6.0]


func _platz_besuch(from, to) -> Node3D:
	"""somebody leaves the path and comes onto your pitch: to the tent (looks, bends), to the bike, back to the path"""
	var tent: Vector3 = main.obj["pir"]
	var bike: Vector3 = main.obj["bike"]
	var side := 1.0 if randf() < 0.5 else -1.0
	var wz = main.scenes.data.get("weg_z", null)
	var a: Vector3
	var b: Vector3
	if wz != null:
		a = Vector3(side * randf_range(17.0, 20.0), 0, float(wz))
		b = Vector3(-side * randf_range(17.0, 20.0), 0, float(wz))
	else:
		var rt: Array = _cross(12.0)
		a = from if from != null else rt[0]
		b = to if to != null else rt[1]
	var v = main.spawn("person", a, Vector3(side * 3.0, 0, a.z))
	v.speed = randf_range(1.1, 1.35)
	v.route = [main.free_spot(tent + Vector3(side * 1.2, 0, 2.2), 0.5, true),
			[main.free_spot(tent + Vector3(0.3 * side, 0, 1.6), 0.5, true), randf_range(4.0, 7.0), 0.4, tent],
			[main.free_spot(bike + Vector3(0.7, 0, 0.6), 0.5, true), randf_range(2.0, 4.0), 0.7, bike],
			Vector3(-side * 3.0, 0, b.z), b]
	return v


func _tarn(kind: String, from, to) -> Node3D:
	"""camouflage clothes and crawling, the umbrella, the cardboard box (the things of gameplus.gd)"""
	var rt: Array = _cross(randf_range(6.0, 11.0))
	var a: Vector3 = from if from != null else rt[0]
	var b: Vector3 = to if to != null else rt[1]
	var P := func(f: float) -> Vector3: return main.free_spot(a.lerp(b, f), 0.4, true)
	var v
	if kind == "tarn_robben":
		ActorS.npc_camo = true                             # actor.gd: the camouflage look of the players for this figure
		v = main.spawn("person", a, P.call(0.3))
		ActorS.npc_camo = false
		v.speed = 1.2
		v.route = [[P.call(0.3), 1.0, 1.0], [P.call(0.42), 0.5, 2.0], [P.call(0.55), 5.0, 2.0], [P.call(0.62), 1.0, 2.0], [P.call(0.78), 0.0, 1.0], b]
	else:
		v = main.spawn("person", a, P.call(0.3))
		v.speed = 1.1 if kind == "tarn_schirm" else 0.9
		var g := "umbrella" if kind == "tarn_schirm" else "box"
		if main.game != null and main.game.plus != null:
			main.game.plus.dress({"gear": g, "actor": v, "look": {}, "slot": -1})     # the same thing as a player gets
		if kind == "tarn_schirm":
			v.route = [[P.call(0.3), 2.0, 1.0], [P.call(0.48), 5.0, 1.0], [P.call(0.65), 2.0, 1.0], [P.call(0.85), 0.0, 1.0], b]
		else:                                              # a box moves, stops for a long time, moves again
			v.route = [[P.call(0.28), 6.0, 1.0], [P.call(0.42), 9.0, 1.0], [P.call(0.56), 7.0, 1.0], [P.call(0.75), 2.0, 1.0], b]
	return v


func _velodieb() -> Node3D:
	"""runs to the bike, kneels 2-3 s (cuts the lock - the bike sensor fires), runs away pushing the bike"""
	var bike: Vector3 = main.obj["bike"]
	var ways: Array = main.scenes.data.get("dieb_wege", [])
	var a: Vector3
	var b: Vector3
	if ways.size() >= 2:
		var i := randi() % ways.size()
		a = ways[i]
		b = ways[(i + 1 + randi() % (ways.size() - 1)) % ways.size()]
	else:
		var side := 1.0 if randf() < 0.5 else -1.0
		a = bike + Vector3(side * 16.0, 0, randf_range(-4.0, 2.0))
		b = bike + Vector3(-side * 18.0, 0, randf_range(-8.0, -2.0))
	var grab: Vector3 = main.free_spot(bike + Vector3(0.75, 0, 0.5), 0.4, true)
	var v = main.spawn("burglar" if main.is_dark() else "person", a, grab)
	v.speed = randf_range(2.8, 3.3)
	v.route = [[grab, randf_range(2.2, 3.2), 1.0, bike], grab.lerp(b, 0.5), b]
	v.set_meta("grab", grab)
	return v


func _game_on() -> bool:
	return main.game != null and str(main.game.round_state) in ["countdown", "play"]


func _track(t: float) -> void:
	var pc: Array = _pitch()
	for r in tracked:
		var v = r["v"]
		var alive: bool = is_instance_valid(v) and not v.is_queued_for_deletion() and not v.done
		if not alive:
			if float(r["gone"]) < 0.0:
				r["gone"] = t
			continue
		match str(r["kind"]):
			"platz_besuch":
				if float(r["enter"]) < 0.0 and Vector2(v.position.x, v.position.z).distance_to(Vector2(pc[0].x, pc[0].z)) < float(pc[1]):
					r["enter"] = t
					events.append({"kind": "platz", "id": r["id"], "t": t})
			"velodieb":
				var gp: Vector3 = v.get_meta("grab", main.obj["bike"])
				if float(r["grab"]) < 0.0 and Vector2(v.position.x, v.position.z).distance_to(Vector2(gp.x, gp.z)) < 1.2 and v.now_s() < v.wait_until:
					r["grab"] = t
					_take_bike(v)
					events.append({"kind": "griff", "id": r["id"], "t": t})
	# the bike back at its place when the thief is gone (he had a copy) - or at once when a game round begins
	if _bike_copy_of != null and _game_on():
		restore()
	if _bike_copy_of != null:
		var busy := false
		for r in tracked:
			if str(r["kind"]) == "velodieb" and float(r["grab"]) >= 0.0 and float(r["gone"]) < 0.0:
				busy = true
		if not busy:
			if is_instance_valid(_bike_copy_of):
				_bike_copy_of.visible = true
			_bike_copy_of = null
	if tracked.size() > 40:
		tracked = tracked.filter(func(r): return float(r["gone"]) < 0.0 or t - float(r["gone"]) < 600.0)


func _take_bike(v) -> void:
	"""the bike sensor fires; the thief pushes a copy away, the real one is hidden until he is gone"""
	main.add_event("Velo", "tag")
	var bk = main.bike_node
	if bk == null or not is_instance_valid(bk) or not bk.visible:
		return
	var cp: Node3D = bk.duplicate()
	v.add_child(cp)
	cp.transform = Transform3D(Basis.IDENTITY, Vector3(0.5, 0.05, 0.0))
	if v.has_meta("carry_bike"):                     # Ferienpark-Aufgabe «Velo-Dieb» (ferienpark_leben.gd): lifted and carried away
		cp.transform = Transform3D(Basis(Vector3(0, 0, 1), -0.12), Vector3(0.42, 0.42, 0.05))
		v.carry = true
	bk.visible = false
	_bike_copy_of = bk


func restore() -> void:
	"""tests / end of a test run: the bike back"""
	if _bike_copy_of != null and is_instance_valid(_bike_copy_of):
		_bike_copy_of.visible = true
	_bike_copy_of = null


# ---- test run (testrun.gd) -------------------------------------------------------------------------------------------------
func neighbours() -> Array:
	var out := []
	for n in nb:
		for v in n["a"]:
			if is_instance_valid(v) and v.visible and v.kind == "person":
				out.append(v)
	return out


func cause(tr) -> String:
	"""testrun._cause: a report without a test visitor - was a neighbour in the picture?"""
	var cam: Camera3D = main.cams[0]
	for v in neighbours():
		var p: Vector3 = v.position + Vector3(0, 0.9, 0)
		if cam.is_position_in_frustum(p) and main.line_free(cam.global_position, p):
			return "Nachbar (auf seinem Platz / dem Weg)"
	return ""


func report_extra(tr) -> Dictionary:
	"""the numbers of the scene for the report: reaction from entering your pitch / from the grab to the first push"""
	var plan: String = str(tr.plan)
	if not plan in IDS:
		return {}
	var out := {"art": plan}
	if plan == "camping_voll":
		var n := 0
		var pushed := 0
		var lat := []
		for e in events:
			if e["kind"] != "platz" or float(e["t"]) < tr.t0 or not tr.truth.has(e["id"]):
				continue
			n += 1
			var pt: float = float(tr.truth[e["id"]].get("push", -1.0))
			if pt >= 0.0:
				pushed += 1
				lat.append(pt - float(e["t"]))
		var nbf := 0
		for p in tr.pushes:
			if not bool(p["ok"]) and not bool(p["dup"]) and str(p["who"]).begins_with("Nachbar"):
				nbf += 1
		out.merge({"auf_platz": n, "push": pushed, "ohne_push": n - pushed, "reaktion_platz_s": _avg(lat), "push_falsch_nachbar": nbf})
	elif plan == "velodieb":
		var n2 := 0
		var before := 0
		var after := 0
		var lat2 := []
		for e in events:
			if e["kind"] != "griff" or float(e["t"]) < tr.t0 or not tr.truth.has(e["id"]):
				continue
			n2 += 1
			var pt2: float = float(tr.truth[e["id"]].get("push", -1.0))
			if pt2 >= 0.0:
				if pt2 <= float(e["t"]):
					before += 1
				else:
					after += 1
				lat2.append(pt2 - float(e["t"]))
		out.merge({"griffe": n2, "push_vor_griff": before, "push_nach_griff": after, "ohne_push": n2 - before - after, "reaktion_griff_s": _avg(lat2)})
	else:
		var by := {}
		for r in tr.truth.values():
			var k: String = str(r["kind"])
			if not k.begins_with("tarn_"):
				continue
			var b: Dictionary = by.get(k, {"sichtbar": 0, "erkannt": 0, "push": 0})
			if float(r["first"]) >= 0.0:
				b["sichtbar"] += 1
				if float(r["det"]) >= 0.0:
					b["erkannt"] += 1
				if float(r.get("push", -1.0)) >= 0.0:
					b["push"] += 1
			by[k] = b
		out["arten"] = by
	return out


func _avg(a: Array):
	if a.is_empty():
		return null
	var s := 0.0
	for x in a:
		s += float(x)
	return snappedf(s / a.size(), 0.1)


# ---- buttons and control --------------------------------------------------------------------------------------------------
func add_controls() -> void:
	for k in KINDS:
		var kk: String = k
		main.add_control("button", "spawn_" + kk, KINDS[kk][0], null, func(): main.spawn(kk), "Besuch", {"sub": KINDS[kk][1]})


func info() -> Dictionary:
	var acts := []
	for n in nb:
		var vis := 0
		for v in n["a"]:
			if is_instance_valid(v) and v.visible:
				vis += 1
		acts.append([n["kind"], vis])
	return {"scene": main.scene, "nachbarn": acts, "tracked": tracked.map(func(r): return [r["kind"], r["enter"] >= 0.0, r["grab"] >= 0.0, r["gone"] >= 0.0]),
			"bike_hidden": _bike_copy_of != null, "events": events.size()}


func control(d: Dictionary) -> Dictionary:
	"""CONTROL {action: szenen, do: info | spawn (kind) | restore}"""
	var op := str(d.get("do", "info"))
	if op == "spawn":
		main.spawn(str(d.get("kind", "platz_besuch")))
	elif op == "restore":
		restore()
	return {"ok": true, "szenen": info()}


# ---- game ------------------------------------------------------------------------------------------------------------------
func goal_key() -> String:
	return str(GOAL.get(main.scene, ""))


func game_card() -> Dictionary:
	"""gamewiz.gd: the quick card of the game that fits this scene ({} = none)"""
	if not GAME.has(main.scene):
		return {}
	var g: Array = GAME[main.scene]
	return {"v": g[0], "icon": g[1], "title": "Spiel zur Szene: " + str(g[2]), "text": g[3], "scene": true}
