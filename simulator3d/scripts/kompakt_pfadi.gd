extends "res://scripts/kompakt.gd"
## 3D-4.x «Pfadilager im Wald» (kompakt.gd): eine Lichtung in dichtem Wald, rund 200 × 200 m. Sarasani und zwei Jurten,
## eine Reihe Spatz-Zelte, Lagerfeuerplatz mit Bänken, Fahnenmasten und Totempfahl, Küchenwagen (Türsensor), Plumpsklos,
## Wasserstelle; östlich der Bach in einer kleinen Schlucht mit Seilbrücke und Holzsteg, im Westen ein Hochsitz an einer
## kleinen Wiese, Waldwege zur Forststrasse im Süden. Dunkel und eng: Bäume bis an den Platz, viele Kinder, Tiere aus dem
## Wald - schwer für die Erkennung.

const SPOTS := {"feuer": ["Am Lagerfeuer (Blick zum Sarasani)", 3.0, 9.0, 0.0],
		"zelte": ["Bei den Spatz-Zelten", -10.0, 25.0, 15.0],
		"bach": ["An der Seilbrücke (Bach)", 31.0, -12.0, 75.0],
		"waldweg": ["Am Waldweg (Lagereingang)", -2.0, 58.0, 0.0]}
const SPOT_ORDER := ["feuer", "zelte", "bach", "waldweg"]
const PLACES := [["Sarasani", -6.0, -14.0], ["Jurte", 17.0, -16.0], ["Lagerfeuer", 0.0, 2.0], ["Spatz-Zelte", -10.0, 17.0],
		["Fahnenmast", -22.0, -10.0], ["Küchenwagen", -26.0, 4.0], ["Plumpsklo", -31.0, 23.0], ["Seilbrücke", 42.0, -20.0],
		["Holzsteg", 44.0, 50.0], ["Hochsitz", -62.0, 30.0], ["Forststrasse", 0.0, 104.0]]
const CREEK := [Vector2(40, -130), Vector2(36, -60), Vector2(42, -20), Vector2(36, 12), Vector2(44, 50), Vector2(38, 130)]
const C_FLOOR := Color(0.24, 0.23, 0.13)          # forest floor (needles)
const C_CLEARING := Color(0.32, 0.4, 0.18)
const C_TRODDEN := Color(0.4, 0.38, 0.24)
const C_PATH := Color(0.42, 0.35, 0.24)
const C_GRAVEL := Color(0.52, 0.5, 0.43)


func ground_colour() -> Color:
	return C_FLOOR


func H(x: float, z: float) -> float:
	var h := 1.6 * sin(x / 41.0) * cos(z / 37.0) + 0.025 * (-x) + 0.02 * z
	h += smoothstep(160.0, 700.0, Vector2(x, z).length()) * 140.0 * (0.7 + 0.3 * sin(atan2(z, x) * 3.0))
	var cd := seg_dist(CREEK, x, z)                    # the creek ravine
	if cd < 9.0:
		h -= 2.6 * (1.0 - smoothstep(1.0, 9.0, cd))
	var e := Vector2(x / 34.0, z / 30.0).length()       # the clearing is flatter
	if e < 1.2:
		h = lerpf(h, 0.3 * h, 1.0 - smoothstep(0.8, 1.2, e))
	return h


func far_colour(x: float, z: float, h: float) -> Color:
	if h > 110.0:
		return Color(0.38, 0.37, 0.34).lerp(Color(0.85, 0.86, 0.9), smoothstep(120.0, 150.0, h))
	return Color(0.13, 0.2, 0.1) if int(x / 90.0 + z / 70.0) % 4 != 0 else Color(0.3, 0.4, 0.2)


func _in_clearing(x: float, z: float, r := 1.0) -> bool:
	return Vector2(x / 34.0, z / 30.0).length() < r or Vector2(x + 58.0, z - 33.0).length() < 13.0 * r


func paint(img: Image) -> void:
	var k := -36.0
	while k <= 36.0:                                  # the clearing: an ellipse of meadow
		var hw := 30.0 * sqrt(maxf(0.0, 1.0 - pow(k / 36.0, 2.0)))
		rect(img, k, -hw, k + _mpp(), hw, C_CLEARING)
		k += _mpp()
	disc(img, -58.0, 33.0, 13.0, C_CLEARING)            # the glade of the raised hide
	disc(img, 0.0, 2.0, 6.0, C_TRODDEN)                 # around the fire
	disc(img, -6.0, -14.0, 9.0, C_TRODDEN)              # in front of the sarasani
	rect(img, -26.0, 14.0, 8.0, 21.0, C_TRODDEN)        # the row of tents
	for c in creeks:                                   # the creek bed: stones
		polyline(img, c[0], 4.0, Color(0.33, 0.32, 0.28))


func content() -> void:
	road = pts2([[-130, 104], [-60, 102], [0, 104], [60, 107], [130, 105]])
	way(road, 5.0, C_GRAVEL)
	way(pts2([[0, 104], [-4, 75], [-2, 50], [0, 30], [0, 10]]), 2.2, C_PATH)       # from the forest road to the camp
	way(pts2([[18, -4], [30, -14], [34, -20]]), 1.8, C_PATH)                       # to the rope bridge
	way(pts2([[50, -20], [70, -32], [110, -44], [130, -50]]), 1.6, C_PATH)         # behind the bridge into the forest
	way(pts2([[-18, 16], [-40, 26], [-50, 31]]), 1.6, C_PATH)                      # to the raised hide
	way(pts2([[8, 18], [30, 34], [40, 50]]), 1.6, C_PATH)                          # to the footbridge
	way(pts2([[48, 50], [70, 62], [130, 70]]), 1.6, C_PATH)
	way(pts2([[-30, 8], [-31, 20]]), 1.4, C_PATH)                                  # to the latrines
	creek(CREEK, 2.2, [Vector2(42, -20), Vector2(44, 50)])
	# the big tents
	bib.add("sarasani", P(-6.0, -14.0), 0.0, {"r": 7.0, "col": "262626", "flag": "2a5bb0"})
	bib.add("yurt", P(17.0, -16.0), -0.6, {"r": 3.6, "smoke": true})
	bib.add("yurt", P(21.0, -3.0), -1.2, {"r": 3.0, "col": "d8cfb0"})
	var tcols := ["6a6a3a", "4a5a3a", "8a6a3a", "d8692a", "3a4a5a", "6a6a3a", "4a5a3a"]
	for i in range(7):
		var x := -24.0 + i * 5.0
		if absf(x + 9.0) < 1.0 and spot == "zelte":
			continue                                       # your tent (own_spot)
		bib.add("tent", P(x + rng.randf_range(-0.4, 0.4), 17.5), PI + rng.randf_range(-0.15, 0.15), {"style": "ridge", "col": tcols[i]})
	# the camp fire with log benches, the dining place, the kitchen wagon (door sensor), water
	bib.add("campfire", P(0.0, 2.0), 0.0, {"fire": true, "benches": true})
	for i in range(4):
		bib.add("picnic_table", P(-17.0 + (i % 2) * 4.5, -1.0 + (i / 2) * 3.5), PI / 2.0, {"len": 2.4})
	s.caravan(WG(-26.0, 4.0), wrot(PI / 2.0))           # «Küchenwagen» - the door sensor in every place of the camp
	bib.add("water_tap", P(-16.0, 6.0), 0.0)
	bib.add("latrine", P(-31.0, 23.0), PI)
	bib.add("latrine", P(-34.0, 23.0), PI)
	# flag poles, totem, signpost, a few lanterns
	bib.add("flagpole", P(-22.0, -12.0), 0.0, {"h": 9.0, "col": "c8102e"})
	bib.add("flagpole", P(-22.0, -8.0), 0.0, {"h": 8.0, "col": "2a5bb0"})
	bib.add("totem", P(8.0, -24.0), 0.3, {"h": 4.5})
	bib.add("signpost", P(2.0, 32.0), 0.4, {"arms": ["Lager", "Bach", "Hochsitz"]})
	bib.add("info_board", P(3.0, 98.0), PI, {"text": "Pfadilager"})
	bib.many("lamp", [[P(-12.0, 9.0), 0.0], [P(-22.0, 18.0), 0.0], [P(10.0, -6.0), 0.0]], {"style": "lantern"})
	for wp in [[-14.0, -20.0], [4.0, -22.0], [-30.0, -2.0]]:
		s.prop("woodpile", WG(wp[0], wp[1]), rng.randf() * TAU)
	s.laundry(WG(-20.0, 10.0), wrot(0.2))
	# the creek: rope bridge in the ravine, footbridge further south, stones
	bib.add("rope_bridge", Vector3(42.0, H(34.0, -20.0) - 0.4, -20.0), PI / 2.0, {"len": 16.0, "sag": 1.0})
	bib.add("footbridge", Vector3(44.0, H(48.0, 50.0) - 0.1, 50.0), PI / 2.0, {"len": 8.0, "w": 1.8})
	for i in range(14):
		var t := rng.randf()
		var seg := rng.randi() % (CREEK.size() - 1)
		var q: Vector2 = CREEK[seg].lerp(CREEK[seg + 1], t)
		bib.add("rock", P(q.x + rng.randf_range(-2.6, 2.6), q.y, -0.2), rng.randf() * TAU, {"r": rng.randf_range(0.4, 1.0)})
	# the raised hide at the glade in the west
	bib.add("hochsitz", P(-66.0, 28.0), deg_to_rad(-60.0), {"h": 4.0})
	# the forest: dense, right up to the clearing; a few big broadleaf trees at its edge make it dark
	forest(func(x, z): return not _in_clearing(x, z, 1.06), 6.0, 0.9, 0.75, 36.0)
	var edge := []
	for i in range(24):
		var a := TAU * i / 24.0 + rng.randf_range(-0.1, 0.1)
		var px := cos(a) * 36.0 * rng.randf_range(1.0, 1.08)
		var pz := sin(a) * 32.0 * rng.randf_range(1.0, 1.08)
		if free_at(px, pz, 2.5):
			edge.append([P(px, pz, -0.1), rng.randf() * TAU, rng.randf_range(1.25, 1.6)])
	bib.many("tree", edge)


func own_spot() -> void:
	match spot:
		"feuer":
			m.obj["pir"] = WG(-6.0, -6.4)                  # the entrance of the sarasani
			s.bike(WG(7.0, 7.0), wrot(0.4))
			s.data["platz"] = [WG(0.0, 0.0), 9.0]
		"zelte":
			own_tent(-9.0, 17.0, 0.0, Color(0.45, 0.5, 0.3))
			s.bike(WG(-5.0, 21.0), wrot(1.2))
		"bach":
			m.obj["pir"] = WG(33.0, -20.0)                 # the west end of the rope bridge
			s.bike(WG(28.0, -8.0), wrot(0.9))
			s.data["platz"] = [WG(33.0, -18.0), 6.0]
		"waldweg":
			m.obj["pir"] = WG(2.0, 33.0)                   # the signpost at the entrance of the camp
			s.bike(WG(3.0, 54.0), wrot(0.1))
			s.data["platz"] = [WG(0.0, 42.0), 7.0]
	s.data["wc"] = WG(-31.0, 21.0)
	s.data["weg_z"] = WG(-30.0, 14.0).z


func people() -> Array:
	"""children everywhere, leaders between the tents, the fire and the kitchen, at night the walk to the latrine"""
	var camp := pts2([[0, 5], [-6, -6], [17, -11], [-14, 1], [-10, 14], [-22, 6], [10, 20], [-20, -8]])
	var out := [["kinder", Vector2(-4, 8)], ["kinder", Vector2(8, -8)], ["sitz", Vector2(2, 5)], ["wc", Vector2(-12, 14)],
			["runde", Vector2(-20, 2), {"pts": camp, "actor": "person", "wach": [7.0, 23.5], "wait": [6.0, 40.0]}]]
	if not lite:
		out.append_array([["kinder", Vector2(-14, -18)], ["kinder", Vector2(-2, 22)], ["sitz", Vector2(-3, 4)], ["wc", Vector2(2, 15)],
				["runde", Vector2(10, -2), {"pts": camp, "actor": "child", "wach": [7.5, 21.5], "spd": 2.0, "wait": [2.0, 14.0]}],
				["runde", Vector2(-8, 10), {"pts": camp, "actor": "child", "wach": [7.5, 21.5], "spd": 1.9, "wait": [2.0, 14.0]}],
				["runde", Vector2(30, -16), {"pts": pts2([[31, -18], [24, -10], [8, 0], [33, -20]]), "actor": "child", "wach": [9.0, 19.0], "spd": 1.8, "wait": [5.0, 25.0]}],
				["runde", Vector2(-24, 0), {"pts": pts2([[-24, 2], [-16, 5], [0, 4], [-30, 18]]), "actor": "person", "wach": [6.5, 22.5], "wait": [10.0, 60.0]}]])
	return out


func hide_kinds() -> Array:
	return ["bush", "bush", "woodpile", "rock", "bush"]


func grass_n() -> int:
	return 380
