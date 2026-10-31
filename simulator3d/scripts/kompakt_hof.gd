extends "res://scripts/kompakt.gd"
## 3D-4.x «Bauernhof mit Hofladen und Stellplätzen» (kompakt.gd): ein Hof im Flachland, als Ort im Ferienpark am See am
## Ostufer (Radius 42 m, der See im Norden), allein rund 200 × 200 m mit Feldern. Scheune, Kuhstall, Bauernhaus, Hofladen
## mit «Kasse des Vertrauens», Hühnerstall, Traktor, Misthaufen, Weide mit Kühen, Obstbäume und fünf Wohnmobil-Stellplätze
## mit Stromsäulen. Viele Wärmequellen (Kühe, Stall, Traktor, Mist, Hühner) - gut für Wärmebild und Fehlalarme.
## Park-Koordinaten: x = Osten, z = Süden, Nullpunkt = Mitte des Hofs.

const SPOTS := {"stellplatz": ["Beim Wohnmobil (Stellplatz am Hof)", 10.0, 25.0, 0.0],
		"hofladen": ["Beim Hofladen (Kasse des Vertrauens)", 7.0, 8.0, 180.0],
		"stall": ["Beim Kuhstall (viel Wärme)", 6.0, -9.0, 10.0],
		"weide": ["An der Weide (Zaun, Kühe)", 21.0, 2.0, 90.0]}
const SPOT_ORDER := ["stellplatz", "hofladen", "stall", "weide"]
const PLACES := [["Scheune", -14.0, -16.0], ["Kuhstall", 12.0, -19.0], ["Bauernhaus", -24.0, 10.0], ["Hofladen", 4.0, 2.0],
		["Hühnerstall", -3.0, -27.0], ["Misthaufen", 26.0, -24.0], ["Weide", 30.0, 6.0], ["Stellplätze", 0.0, 30.0],
		["Obstgarten", -30.0, 28.0]]
const C_MEADOW := Color(0.32, 0.45, 0.19)
const C_YARD := Color(0.5, 0.48, 0.42)
const C_GRAVEL := Color(0.55, 0.53, 0.46)
const C_MUD := Color(0.36, 0.3, 0.2)
const C_PASTURE := Color(0.36, 0.5, 0.2)
const PITCH_X := [-20.0, -10.0, 0.0, 10.0, 20.0]


func ground_colour() -> Color:
	return C_MEADOW


func H(x: float, z: float) -> float:
	# the plain (allein): almost flat, a few soft waves, hills far away
	var h := 0.5 * sin(x / 47.0) * cos(z / 39.0)
	h += smoothstep(170.0, 800.0, Vector2(x, z).length()) * 110.0 * (0.7 + 0.3 * sin(atan2(z, x) * 2.0))
	return h


func paint(img: Image) -> void:
	rect(img, -26.0, -26.0, 22.0, 14.0, C_YARD)          # the farm yard
	rect(img, 18.0, -30.0, 32.0, -18.0, C_MUD)           # at the dung heap and the stable door
	rect(img, 20.0, -10.0, 40.0, 20.0, C_PASTURE)       # the pasture
	for x in PITCH_X:                                    # the camper pitches (gravel)
		rect(img, x - 3.6, 24.0, x + 3.6, 36.0, C_GRAVEL)
	if not flat:
		rect(img, -120.0, -120.0, -40.0, -50.0, Color(0.72, 0.62, 0.32))    # a wheat field (allein)
		rect(img, 50.0, 40.0, 120.0, 110.0, Color(0.3, 0.42, 0.16))


func content() -> void:
	road = pts2([[130, 16], [60, 17], [40, 17], [0, 17], [-40, 17], [-130, 16]])
	way(pts2([[44, 17], [0, 17], [-34, 17]]), 4.5, C_GRAVEL)                  # the farm road along the pitches
	way(pts2([[0, 17], [2, 6], [0, -8]]), 3.5, C_GRAVEL)                      # into the yard
	way(pts2([[-34, 17], [-90, 16], [-130, 16]]), 4.5, C_GRAVEL)
	way(pts2([[44, 17], [130, 16]]), 4.5, C_GRAVEL)
	# the buildings: barn, cow stable, farm house, farm shop, hen house
	bib.add("barn", P(-14.0, -16.0), 0.0, {"w": 14.0, "d": 10.0})
	bib.add("stable", P(12.0, -19.0), 0.0, {"w": 16.0, "d": 7.0, "col": "9a6a42", "text": "Stall"})
	bib.add("house", P(-24.0, 10.0), PI / 2.0, {"w": 9.0, "d": 8.0, "floors": 2, "col": "efe6d2", "roof": "6a3a2a", "smoke": true})
	bib.add("shop", P(4.0, 2.0), 0.0, {"w": 7.0, "d": 5.0})
	bib.add("info_board", P(8.5, 4.6), 0.0, {"text": "Hofladen · Kasse des Vertrauens"})
	bib.add("coop", P(-3.0, -27.0), 0.0)
	for i in range(nl(8)):
		bib.add("chicken", P(-6.0 + rng.randf_range(-4.0, 6.0), -23.0 + rng.randf_range(-2.0, 3.0)), rng.randf() * TAU)
	bib.add("tractor", P(2.0, -9.0), PI * 0.6)
	for i in range(5):                                   # round bales at the barn, a few square ones
		bib.add("haybale", P(-26.0 + (i % 3) * 1.8, -5.0 + (i / 3) * 1.8), rng.randf() * TAU, {"wrapped": i % 2 == 0})
	for i in range(4):
		bib.add("haybale", P(-6.0 + i * 1.3, -10.0), 0.0, {"style": "square"})
	# the dung heap: warm in the thermal picture (compost / manure surface about 30-45 °C, the core 55-70 °C - the
	# usual values for an active heap; MoveEye only sees the surface)
	s.put(park, m.box(6.0, 1.6, 4.0), P(26.0, -24.0, 0.8), Color(0.32, 0.25, 0.16), 38.0)
	m.add_obstacle_box(WG(26.0, -24.0), 6.2, 4.2, wrot(0.0))
	# the pasture with its fence and the cows (by day; at night they are in the stable - the stable stays warm)
	var fc := [Vector2(20, -10), Vector2(40, -10), Vector2(40, 20), Vector2(20, 20)]
	for i in range(4):
		var a: Vector2 = fc[i]
		var b: Vector2 = fc[(i + 1) % 4]
		if i == 3:                                       # the gate on the side of the yard
			bib.line("fence", P(a.x, a.y), P(b.x, b.y), 2.5, {"style": "wood"}, [[a.distance_to(b) * 0.5, 2.0]])
		else:
			bib.line("fence", P(a.x, a.y), P(b.x, b.y), 2.5, {"style": "wood"})
	for i in range(nl(6)):
		bib.add("cow", P(rng.randf_range(23.0, 37.0), rng.randf_range(-7.0, 17.0)), rng.randf() * TAU,
				{"col": ["f2f0ea", "6a4a2a", "2a2420"][i % 3]})
	bib.add("water_tap", P(22.0, 18.0), 0.0)
	# the camper pitches: posts, power, three motorhomes (your own one at «stellplatz»)
	for i in range(PITCH_X.size()):
		var x: float = PITCH_X[i]
		bib.add("pitch_post", P(x - 3.0, 23.0), 0.0, {"nr": str(i + 1)})
		if i % 2 == 0:
			bib.add("power_post", P(x + 3.8, 23.5), 0.0)
		if (spot == "stellplatz" and absf(x - 10.0) < 1.0) or i == 2:
			continue
		if i in [0, 1, 4]:
			bib.add("motorhome", P(x, 31.0), PI, {"len": 6.8, "style": ["alcove", "van", "alcove"][i % 3], "col": ["f2f2f2", "d8d8d0", "f0ece0"][i % 3]})
	bib.add("signpost", P(-2.0, 15.0), 0.6, {"arms": ["Hofladen", "Stellplatz", "See"]})
	bib.add("bin", P(-14.0, 21.0), 0.0)
	bib.add("bench", P(10.5, 4.0), 0.0)
	bib.many("lamp", [[P(-4.0, 12.0), 0.0], [P(14.0, -12.0), 0.0], [P(-10.0, 24.0), 0.0], [P(14.0, 24.0), 0.0]], {"style": "lantern"})
	# fruit trees south-west, a hedge along the pitches
	var orchard := []
	for i in range(nl(10)):
		orchard.append([P(-36.0 + (i % 4) * 5.0 + rng.randf_range(-0.8, 0.8), 24.0 + (i / 4) * 5.0), rng.randf() * TAU])
	bib.many("orchard_tree", orchard)
	bib.line("hedge", P(-24.0, 38.5), P(24.0, 38.5), 2.5, {"h": 1.5})
	s.laundry(WG(-29.0, 4.0), wrot(0.1))
	s.prop("woodpile", WG(-29.0, 14.5), PI / 2.0)
	clear.append([-28.0, -28.0, 42.0, 40.0])             # no random tree on the farm
	if not flat:                                         # allein: fields, a few trees, the forest far away
		bib.add("field", P(-80.0, -85.0), 0.0, {"w": 80.0, "d": 70.0, "crop": "wheat"})
		bib.add("field", P(85.0, 75.0), 0.2, {"w": 60.0, "d": 60.0, "crop": "corn"})
		forest(func(x, z): return Vector2(x, z).length() > 95.0 and not (x < -40 and x > -120 and z < -50 and z > -120), 9.0, 0.5, 0.3, 30.0)


func own_spot() -> void:
	match spot:
		"stellplatz":
			own_motorhome(10.0, 31.0, PI)
		"hofladen":
			m.obj["pir"] = WG(4.0, 5.2)                    # in front of the shop (the till of trust)
			m.obj["door"] = WG(6.1, 4.6)
			s.bike(WG(11.5, 6.0), wrot(0.2))
			s.data["platz"] = [WG(4.0, 6.0), 6.0]
		"stall":
			m.obj["pir"] = WG(12.0, -14.6)                 # the stable door
			m.obj["door"] = WG(12.0, -15.3)
			s.bike(WG(2.0, -5.0), wrot(1.2))
			s.data["platz"] = [WG(8.0, -12.0), 7.0]
		"weide":
			m.obj["pir"] = WG(20.0, 5.0)                   # the gate of the pasture
			s.bike(WG(17.0, 0.0), wrot(0.6))
			s.data["platz"] = [WG(20.0, 4.0), 6.0]
	s.data["wc"] = WG(-20.0, 6.0)
	s.data["weg_z"] = WG(0.0, 17.0).z


func people() -> Array:
	"""the farmer between barn, stable and shop, the farm dog (always awake), customers at the shop, campers at the pitches"""
	var yard := pts2([[-14, -9], [12, -14], [2, -7], [4, 6], [-20, 8], [26, -20], [22, 0], [-4, -22]])
	var out := [["runde", Vector2(-10, -6), {"pts": yard, "actor": "person", "wach": [5.5, 21.0], "wait": [8.0, 50.0]}],
			["runde", Vector2(0, -2), {"pts": yard + pts2([[0, 20], [-20, 20], [20, 20]]), "actor": "dog", "wach": [0.0, 24.0], "spd": 1.6, "wait": [3.0, 25.0], "r": 3.0}],
			["runde", Vector2(4, 10), {"pts": pts2([[4, 6], [8, 12], [0, 17], [30, 17]]), "actor": "person", "wach": [8.0, 19.0], "wait": [5.0, 30.0]}],
			["sitz", Vector2(-10, 28)], ["koch", Vector2(20, 28)]]
	if not lite:
		out.append_array([["runde", Vector2(-24, 14), {"pts": pts2([[-24, 14], [-20, 6], [-29, 4], [4, 6]]), "actor": "person", "wach": [6.0, 22.0], "wait": [10.0, 60.0]}],
				["runde", Vector2(-6, 20), {"pts": pts2([[4, 6], [-4, 20], [0, 30], [-14, 22]]), "actor": "child", "wach": [8.0, 20.5], "spd": 1.9, "wait": [3.0, 15.0]}],
				["runde", Vector2(-20, -24), {"pts": pts2([[-6, -22], [-14, -9], [-26, -4]]), "actor": "cat", "wach": [0.0, 24.0], "spd": 0.8, "wait": [10.0, 60.0]}],
				["kinder", Vector2(-2, 26)], ["wc", Vector2(-20, 28)]])
	return out


func hide_kinds() -> Array:
	return ["bush", "woodpile", "crates", "barrels", "bush"]


func grass_n() -> int:
	return 420
