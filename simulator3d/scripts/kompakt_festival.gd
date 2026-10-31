extends "res://scripts/kompakt.gd"
## 3D-4.x «Festival-Gelände» (kompakt.gd, eigene Welt): eine flache Wiese, rund 200 × 200 m, mit Hauptbühne und kleiner
## Bühne, Lichttürmen, Foodtruck-Gasse, Bar, WC-Containern, Eingang mit Absperrgittern und Kontrolle, dahinter die Zeltstadt.
## Sehr viele Menschen (in Lite weniger), am Abend und in der Nacht bunte, wechselnde Bühnenlichter: ein Stresstest für
## MoveEye (Fehlalarme, viele Personen gleichzeitig, wechselndes Licht). Festivalbetrieb von 14 bis 3 Uhr.
## Park-Koordinaten: x = Osten, z = Süden, Nullpunkt = Mitte des Geländes.

const SPOTS := {"zeltstadt": ["Im Zeltdorf (beim eigenen Zelt)", 12.0, 56.0, 0.0],
		"buehne": ["Vor der Hauptbühne (beim Mischpult)", 0.0, -28.0, 0.0],
		"eingang": ["Am Eingang (Kontrolle)", -84.0, 6.0, 90.0],
		"food": ["Bei den Foodtrucks", 22.0, -6.0, 200.0]}
const SPOT_ORDER := ["zeltstadt", "buehne", "eingang", "food"]
const PLACES := [["Hauptbühne", 0.0, -72.0], ["Kleine Bühne", 76.0, 4.0], ["Foodtrucks", 0.0, -8.0], ["Bar", -40.0, -12.0],
		["WC-Container", 48.0, 30.0], ["Eingang", -92.0, 6.0], ["Zeltstadt", 0.0, 70.0], ["Mischpult", 0.0, -34.0]]
const C_GRASS := Color(0.33, 0.43, 0.19)
const C_TRAMPLED := Color(0.42, 0.4, 0.26)
const C_PATH := Color(0.5, 0.47, 0.38)
const STAGE_COLS := [Color(1, 0.15, 0.5), Color(0.2, 0.4, 1), Color(0.1, 1, 0.5), Color(1, 0.75, 0.1), Color(0.75, 0.2, 1)]


func ground_colour() -> Color:
	return C_GRASS


func H(x: float, z: float) -> float:
	var h := 0.4 * sin(x / 40.0) * cos(z / 36.0)
	h += smoothstep(150.0, 800.0, Vector2(x, z).length()) * 90.0 * (0.7 + 0.3 * sin(atan2(z, x) * 3.0 + 1.0))
	return h


func paint(img: Image) -> void:
	rect(img, -34.0, -66.0, 34.0, -24.0, C_TRAMPLED)      # in front of the main stage
	rect(img, 50.0, -16.0, 72.0, 24.0, C_TRAMPLED)        # in front of the small stage
	rect(img, -30.0, -16.0, 30.0, 0.0, C_TRAMPLED)        # the food trucks
	for i in range(8):                                    # worn grass in the tent city
		disc(img, rng.randf_range(-70.0, 70.0), rng.randf_range(40.0, 100.0), rng.randf_range(3.0, 7.0), C_TRAMPLED)


func content() -> void:
	road = pts2([[-130, 20], [-110, 18], [-100, 16], [-60, 120], [-40, 200]])
	way(pts2([[-130, 6], [-92, 6], [-60, 4], [-20, -8], [0, -20]]), 5.0, C_PATH)     # from the entrance to the stage
	way(pts2([[-60, 4], [-30, 30], [0, 40], [40, 40], [70, 30]]), 3.5, C_PATH)       # along the tent city
	way(pts2([[20, -8], [50, 0], [56, 4]]), 3.5, C_PATH)
	way(pts2([[-110, 18], [-130, 20]]), 6.0, Color(0.3, 0.3, 0.31))
	# the stages with their light towers
	bib.add("stage", P(0.0, -72.0), 0.0, {"w": 20.0, "d": 10.0, "col": "1a1a2a"})
	bib.add("stage", P(76.0, 4.0), -PI / 2.0, {"w": 10.0, "d": 6.0, "col": "3a1a3a"})
	for x in [-14.0, 14.0]:
		bib.add("flagpole", P(x, -36.0), 0.0, {"h": 8.0, "col": "ffcc00"})       # the delay towers (speakers, lights)
	bib.add("food_truck", P(0.0, -34.0), PI, {"col": "2a2a2a", "text": "FOH"})    # the mixing desk (front of house)
	# the stage lights (only in the evening and at night: change colour and pulse - kompakt.gd _light_show)
	var n_main := 3 if lite else 6
	for i in range(n_main):
		var x := -8.0 + 16.0 * i / maxf(1.0, n_main - 1.0)
		show_light(P(x, -66.0, 6.2), STAGE_COLS[i % STAGE_COLS.size()], Vector3(0.0, -0.45, 1.0), 45.0)
	show_light(P(70.0, 4.0, 5.0), STAGE_COLS[3], Vector3(-1.0, -0.5, 0.0), 30.0)
	if not lite:
		show_light(P(-14.0, -36.0, 8.0), STAGE_COLS[1], Vector3(0.3, -0.6, 1.0), 35.0)
		show_light(P(14.0, -36.0, 8.0), STAGE_COLS[0], Vector3(-0.3, -0.6, 1.0), 35.0)
	# the food trucks and the bar
	var cols := ["e8b21e", "c8102e", "2a7ab0", "3a8a3a", "e86a1e", "8a3ab0"]
	var names := ["Pizza", "Raclette", "Burger", "Falafel", "Crêpes", "Churros"]
	for i in range(6):
		bib.add("food_truck", P(-25.0 + i * 10.0, -14.0), 0.0, {"col": cols[i], "text": names[i]})
	bib.add("kiosk", P(-40.0, -12.0), PI / 2.0, {"col": "1a1a1a", "text": "BAR"})
	for i in range(6):
		bib.add("picnic_table", P(-24.0 + i * 9.0, -2.0), 0.0, {"len": 2.4})
	for i in range(4):
		bib.add("bin", P(-28.0 + i * 18.0, 2.0), 0.0, {"col": ["2e7d32", "1565c0", "f9a825", "6a6a6a"][i]})
	# toilets
	bib.add("sanitary", P(48.0, 30.0), PI, {"w": 10.0, "d": 3.0, "text": "WC"})
	bib.add("sanitary", P(-50.0, 34.0), PI, {"w": 8.0, "d": 3.0, "text": "WC"})
	# the entrance: barriers in lanes, the ticket booth, the security check
	for i in range(4):
		var z := -2.0 + i * 3.0
		bib.line("crowd_barrier", P(-100.0, z), P(-86.0, z), 2.5)
	bib.line("crowd_barrier", P(-92.0, -30.0), P(-92.0, -4.0), 2.5)
	bib.line("crowd_barrier", P(-92.0, 16.0), P(-92.0, 40.0), 2.5)
	bib.add("kiosk", P(-104.0, -6.0), PI / 2.0, {"col": "c8102e", "text": "TICKETS"})
	bib.add("info_board", P(-104.0, 14.0), PI / 2.0, {"text": "Festival · Eingang"})
	# the tent city: many tents in rows (yours at «zeltstadt»)
	var tcols := ["d8692a", "2a7ab0", "3a8a3a", "c8102e", "e8b21e", "6a6a6a", "8a3ab0", "f2f2f2"]
	var nt := 0
	for row in range(6):
		for k in range(14):
			if lite and (k + row) % 2 == 1:
				continue
			var x := -66.0 + k * 10.0 + rng.randf_range(-1.5, 1.5) + (row % 2) * 4.0
			var z := 48.0 + row * 9.0 + rng.randf_range(-1.0, 1.0)
			if spot == "zeltstadt" and Vector2(x - 12.0, z - 60.0).length() < 6.0:
				continue
			if Vector2(x - 12.0, z - 56.0).length() < 4.0:
				continue
			bib.add("tent", P(x, z), rng.randf() * TAU, {"style": ["dome", "tunnel", "dome"][k % 3], "col": tcols[(k + row * 3) % tcols.size()]})
			nt += 1
	info["tents"] = nt
	for i in range(nl(8)):                               # a few cars and vans at the edge of the tent city
		bib.add("car", P(-80.0 + i * 6.0, 108.0), PI / 2.0, {"col": ["8a1a1a", "2b5fa8", "e0e0e0", "2a2a2a"][i % 4]})
	bib.many("lamp", [[P(-60.0, 4.0), 0.0], [P(-30.0, 30.0), 0.0], [P(0.0, 40.0), 0.0], [P(40.0, 40.0), 0.0], [P(-20.0, -4.0), 0.0],
			[P(20.0, -4.0), 0.0], [P(-90.0, 0.0), 0.0], [P(-90.0, 14.0), 0.0]])
	for i in range(5):
		bib.fx.append(["flag", P(-60.0 + i * 30.0, 30.0), tcols[i], rng.randf() * TAU])
	clear.append([-110.0, -90.0, 100.0, 120.0])
	forest(func(x, z): return Vector2(x, z).length() > 125.0, 9.0, 0.6, 0.5, 30.0)


func own_spot() -> void:
	match spot:
		"zeltstadt":
			own_tent(12.0, 60.0, 0.0, Color(0.9, 0.5, 0.15))
			m.obj["pir"] = WG(12.0, 57.5)
			s.bike(WG(16.0, 58.0), wrot(1.2))
		"buehne":
			m.obj["pir"] = WG(0.0, -31.5)                  # behind the mixing desk
			m.obj["door"] = WG(0.0, -32.0)
			s.data["platz"] = [WG(0.0, -30.0), 6.0]
		"eingang":
			m.obj["pir"] = WG(-88.0, 6.0)                  # the security check
			s.data["platz"] = [WG(-86.0, 6.0), 7.0]
		"food":
			m.obj["pir"] = WG(20.0, -10.0)                 # the counter of the burger truck
			s.data["platz"] = [WG(22.0, -8.0), 6.0]
	if not m.obj.has("bike") or m.bike_node == null:
		s.bike(WG(-70.0, 10.0), wrot(0.0))
	s.data["wc"] = WG(48.0, 26.0)
	s.data["weg_z"] = WG(0.0, 40.0).z


func people() -> Array:
	"""very many people: in front of the stages, at the food trucks, between the tents; the security at the entrance.
	Lite: about a third (kompakt.gd nl())"""
	var front := pts2([[-14, -50], [0, -46], [14, -50], [-8, -40], [8, -38], [-20, -44], [20, -44], [0, -56]])
	var food := pts2([[-25, -8], [-15, -8], [-5, -8], [5, -8], [15, -8], [25, -8], [-40, -6], [0, -2], [20, -2]])
	var camp := pts2([[-50, 46], [-20, 52], [10, 50], [30, 60], [-30, 70], [0, 76], [40, 80], [48, 26], [-50, 30]])
	var small := pts2([[60, -6], [62, 6], [58, 14], [66, 0]])
	var walk := pts2([[-60, 4], [-20, -8], [0, -30], [20, -6], [50, 2], [0, 40], [-30, 30]])
	var hours := [14.0, 3.0]
	var out := [["runde", Vector2(-88, 4), {"pts": pts2([[-88, 2], [-88, 10], [-90, 6]]), "actor": "person", "wach": [12.0, 4.0], "wait": [20.0, 90.0], "r": 0.8}],
			["runde", Vector2(-88, 9), {"pts": pts2([[-88, 9], [-86, 4]]), "actor": "person", "wach": [12.0, 4.0], "wait": [20.0, 90.0], "r": 0.8}]]
	var groups := [[front, nl(14), 1.0, 1.3, [2.0, 18.0]], [food, nl(8), 1.0, 1.3, [4.0, 30.0]], [camp, nl(8), 1.0, 1.4, [6.0, 40.0]],
			[small, nl(5), 1.0, 1.2, [3.0, 20.0]], [walk, nl(6), 1.2, 1.5, [1.0, 8.0]]]
	for g in groups:
		var pts: Array = g[0]
		for i in range(int(g[1])):
			var h: Vector2 = pts[i % pts.size()]
			out.append(["runde", h, {"pts": pts, "actor": "child" if i % 9 == 8 else "person", "wach": hours,
					"spd": rng.randf_range(float(g[2]), float(g[3])), "wait": g[4], "r": 2.5}])
	out.append(["wc", Vector2(30, 46)])
	out.append(["sitz", Vector2(-20, 0)])
	if not lite:
		out.append_array([["wc", Vector2(-30, 56)], ["sitz", Vector2(10, 0)], ["kinder", Vector2(-10, 64)]])
	return out


func hide_kinds() -> Array:
	return ["crates", "barrels", "crates", "bush"]


func grass_n() -> int:
	return 300
