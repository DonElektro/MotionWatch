extends "res://scripts/kompakt.gd"
## 3D-4.x «Bergdorf mit Stellplatz» (kompakt.gd): ein kleines Bergdorf an der Passstrasse, als Ort im Bergtal am Taleingang
## (Radius 62 m, die Strasse des Tals ist die Dorfstrasse), allein rund 200 × 200 m mit Hängen. Kirche mit Turm, Dorfplatz
## mit Brunnen, Bäckerei, Häuser, Bach mit Steinbrücke und Holzsteg, Talstation einer kleinen Seilbahn, Bushaltestelle und
## am Dorfrand ein Stellplatz für Wohnmobile. Strassenlampen und beleuchtete Fenster in der Nacht, Autos auf der Strasse.
## Park-Koordinaten: x = Osten, z = Süden (talaufwärts zum Pass), Nullpunkt = Dorfplatz.

const SPOTS := {"platz": ["Am Dorfbrunnen (Dorfplatz)", 6.0, 8.0, 0.0],
		"stellplatz": ["Beim Wohnmobil am Dorfrand", 12.0, -40.0, 180.0],
		"bruecke": ["An der Bachbrücke", -6.0, 20.0, 120.0],
		"seilbahn": ["Bei der Seilbahn-Talstation", -36.0, 28.0, 90.0]}
const SPOT_ORDER := ["platz", "stellplatz", "bruecke", "seilbahn"]
const PLACES := [["Dorfplatz", 10.0, 0.0], ["Kirche", -24.0, -16.0], ["Bäckerei", 16.0, -14.0], ["Dorfbrunnen", 10.0, 2.0],
		["Bushaltestelle", 30.0, -6.0], ["Steinbrücke", 36.0, 32.0], ["Holzsteg", -2.0, 26.0], ["Seilbahn-Talstation", -44.0, 34.0],
		["Stellplatz", 10.0, -48.0], ["Passstrasse", 40.0, -55.0]]
const STREET := [Vector2(41, -62), Vector2(39.5, -30), Vector2(37.5, 0), Vector2(36, 30), Vector2(34, 62)]   # = the pass road of the valley
const CREEK := [Vector2(-64, 14), Vector2(-36, 18), Vector2(-14, 24), Vector2(-2, 26), Vector2(18, 30), Vector2(36, 32), Vector2(64, 36)]
const C_MEADOW := Color(0.34, 0.45, 0.2)
const C_ASPHALT := Color(0.3, 0.3, 0.31)
const C_STONE := Color(0.5, 0.49, 0.46)
const C_GRAVEL := Color(0.54, 0.52, 0.46)


func ground_colour() -> Color:
	return C_MEADOW


func H(x: float, z: float) -> float:
	# allein: the valley floor rises a little to the south, the slopes east and west go up steeply
	var h := 0.03 * z + 0.6 * sin(x / 33.0) * cos(z / 29.0)
	h += smoothstep(70.0, 260.0, absf(x - 10.0)) * 160.0
	h += smoothstep(150.0, 900.0, z) * 120.0
	if seg_dist(CREEK, x, z) < 6.0:
		h -= 1.2 * (1.0 - smoothstep(1.0, 6.0, seg_dist(CREEK, x, z)))
	return h


func paint(img: Image) -> void:
	disc(img, 10.0, 0.0, 15.0, C_STONE)                  # the village square (cobbles)
	rect(img, -6.0, -58.0, 30.0, -36.0, C_GRAVEL)        # the camper site
	rect(img, -32.0, -30.0, -16.0, -4.0, Color(0.42, 0.4, 0.34))   # around the church
	for c in creeks:
		polyline(img, c[0], 3.6, Color(0.35, 0.34, 0.3))


func content() -> void:
	road = pts2([[44, -200], [41, -62], [39.5, -30], [37.5, 0], [36, 30], [34, 62], [30, 200]])
	way(STREET, 6.5, C_ASPHALT)
	way(pts2([[37, 0], [22, 1], [10, 0], [-10, 2], [-24, -6]]), 4.0, C_STONE)     # the square to the street and the church
	way(pts2([[10, 0], [8, 14], [-2, 24], [-6, 34], [-30, 30], [-42, 32]]), 2.2, C_GRAVEL)   # over the footbridge to the cable car
	way(pts2([[39, -42], [20, -44], [-4, -46]]), 4.0, C_GRAVEL)                    # into the camper site
	way(pts2([[16, -14], [14, -4]]), 2.0, C_STONE)
	creek(CREEK, 2.4, [Vector2(-2, 26), Vector2(36, 32)])
	# church with tower, the bakery, houses around the square and along the street
	bib.add("church", P(-24.0, -16.0), PI / 2.0, {"len": 18.0, "w": 9.0})
	bib.add("bakery", P(16.0, -14.0), 0.0, {"w": 9.0, "d": 7.0, "text": "Bäckerei"})
	var houses := [[-8.0, -2.0, PI / 2.0, "e8dcc4"], [24.0, 12.0, PI, "d8c8a8"], [8.0, 18.0, PI, "f0e8d8"], [-14.0, 10.0, PI / 2.0, "c8b898"],
			[52.0, -18.0, -PI / 2.0, "e0d0b0"], [52.0, 8.0, -PI / 2.0, "efe4cc"], [-38.0, -2.0, PI / 2.0, "d8ccb4"], [24.0, -30.0, 0.0, "e8e0cc"]]
	for i in range(houses.size()):
		var h: Array = houses[i]
		bib.add("house", P(h[0], h[1]), h[2], {"w": 8.5, "d": 8.0, "floors": 2 + (i % 2), "col": h[3], "roof": ["4a4a4e", "6a3a2a"][i % 2], "smoke": i % 3 == 0})
	bib.add("fountain", P(10.0, 2.0), 0.0, {"r": 1.6})
	bib.add("bench", P(4.0, -3.0), 0.3)
	bib.add("bench", P(16.0, 6.0), PI + 0.2)
	bib.add("bin", P(14.0, -4.0), 0.0)
	bib.add("bench", P(30.0, -6.0), PI / 2.0)          # the bus stop (bench + sign)
	bib.add("info_board", P(30.5, -8.5), PI / 2.0, {"text": "Postauto · Bergdorf"})
	bib.add("signpost", P(33.0, 2.0), 0.0, {"arms": ["Passhöhe", "Gumpisee", "Seilbahn"]})
	bib.many("lamp", [[P(33.0, -40.0), 0.0], [P(33.0, -16.0), 0.0], [P(32.0, 10.0), 0.0], [P(31.0, 40.0), 0.0], [P(2.0, -6.0), 0.0],
			[P(18.0, 8.0), 0.0], [P(-20.0, 30.0), 0.0], [P(6.0, -42.0), 0.0]])
	# the bridges: stone road bridge, wooden footbridge
	bib.add("footbridge", P(36.0, 32.0, 0.05), PI / 2.0 + 0.1, {"len": 7.0, "w": 7.0, "stone": true})   # K3: of stone (its name)
	bib.add("footbridge", P(-2.0, 26.0, 0.05), PI / 2.0 + 0.15, {"len": 6.0, "w": 1.8})
	for i in range(10):
		var seg := rng.randi() % (CREEK.size() - 1)
		var q: Vector2 = CREEK[seg].lerp(CREEK[seg + 1], rng.randf())
		bib.add("rock", P(q.x + rng.randf_range(-2.4, 2.4), q.y, -0.2), rng.randf() * TAU, {"r": rng.randf_range(0.4, 0.9)})
	# the valley station of the cable car (up to the west slope)
	bib.add("cable_station", P(-44.0, 34.0), PI / 2.0, {"text": "Seilbahn", "up": 40.0, "rise": 18.0})
	# the camper site at the edge of the village
	for i in range(4):
		var x := -2.0 + i * 9.0
		bib.add("pitch_post", P(x - 3.4, -42.0), 0.0, {"nr": str(i + 1)})
		bib.add("power_post", P(x + 3.6, -42.5), 0.0)
		if (spot == "stellplatz" and absf(x - 16.0) < 1.0) or i == 2:
			continue
		bib.add("motorhome", P(x, -50.0), 0.0, {"len": 6.8, "style": ["alcove", "van"][i % 2], "col": ["f2f2f2", "e0dcd0"][i % 2]})
	bib.add("water_tap", P(-6.0, -40.0), 0.0)
	bib.line("hedge", P(-8.0, -36.0), P(30.0, -36.0), 2.5, {"h": 1.3}, [[25.0, 3.0]])
	# parked cars on the square, gardens with fences
	bib.add("car", P(22.0, -4.0), PI / 2.0, {"col": "8a1a1a"})
	bib.add("car", P(-2.0, 6.0), 0.1, {"col": "2b5fa8", "style": "hatch"})
	bib.line("fence", P(18.0, 16.0), P(30.0, 16.0), 2.5, {"style": "picket", "h": 0.9})
	bib.line("fence", P(-20.0, 4.0), P(-20.0, 16.0), 2.5, {"style": "picket", "h": 0.9})
	s.laundry(WG(-14.0, 16.0), wrot(0.2))
	s.prop("woodpile", WG(-42.0, 6.0), 0.3)
	clear.append([-50.0, -60.0, 60.0, 40.0])
	# trees: a few in the village, larches on the slopes (allein: the forest of the valley)
	var trees := []
	for p in [[-30.0, 14.0], [22.0, 24.0], [-48.0, -20.0], [48.0, 26.0], [-10.0, -28.0]]:
		trees.append([P(p[0], p[1], -0.15), rng.randf() * TAU, rng.randf_range(0.9, 1.3)])
	bib.many("tree", trees)
	forest(func(x, z): return absf(x - 10.0) > 58.0 or z > 50.0 or z < -64.0, 6.5, 0.7, 0.85, 30.0)


func own_spot() -> void:
	match spot:
		"platz":
			m.obj["pir"] = WG(10.0, 4.5)                   # at the fountain
			m.obj["door"] = WG(16.0, -10.4)                # the door of the bakery
			s.bike(WG(2.0, 9.0), wrot(0.4))
			s.data["platz"] = [WG(8.0, 4.0), 7.0]
		"stellplatz":
			own_motorhome(16.0, -50.0, 0.0)
		"bruecke":
			m.obj["pir"] = WG(-2.0, 22.5)                  # the end of the footbridge
			s.bike(WG(-9.0, 17.0), wrot(1.0))
			s.data["platz"] = [WG(-3.0, 22.0), 6.0]
		"seilbahn":
			m.obj["pir"] = WG(-40.0, 31.0)                 # the door of the valley station
			m.obj["door"] = WG(-39.0, 34.0)
			s.bike(WG(-33.0, 33.0), wrot(0.2))
			s.data["platz"] = [WG(-38.0, 30.0), 6.0]
	s.data["wc"] = WG(-6.0, -42.0)
	s.data["weg_z"] = WG(10.0, 0.0).z


func people() -> Array:
	"""villagers on the square, to the bakery in the morning, to the bus, the church; children at the fountain; campers"""
	var sq := pts2([[10, 4], [16, -9], [4, -2], [30, -6], [-20, -6], [8, 14], [24, 8], [-8, 4]])
	var out := [["runde", Vector2(12, -6), {"pts": sq, "actor": "person", "wach": [6.0, 22.0], "wait": [6.0, 40.0]}],
			["runde", Vector2(16, -10), {"pts": pts2([[16, -10], [10, 4], [30, -6]]), "actor": "person", "wach": [5.5, 18.5], "wait": [20.0, 90.0]}],
			["runde", Vector2(6, 2), {"pts": pts2([[10, 4], [4, -2], [16, 6], [-2, 20]]), "actor": "child", "wach": [8.0, 20.0], "spd": 2.0, "wait": [2.0, 12.0]}],
			["sitz", Vector2(4, -42)], ["runde", Vector2(-30, 2), {"pts": sq, "actor": "dog", "wach": [6.0, 21.0], "spd": 1.5, "wait": [4.0, 30.0]}]]
	if not lite:
		out.append_array([["runde", Vector2(-24, -8), {"pts": pts2([[-24, -8], [-10, 2], [10, 4]]), "actor": "person", "wach": [7.0, 20.0], "wait": [30.0, 120.0]}],
				["runde", Vector2(-38, 30), {"pts": pts2([[-40, 30], [-20, 30], [-6, 34], [10, 4]]), "actor": "person", "wach": [8.0, 17.5], "wait": [10.0, 60.0]}],
				["runde", Vector2(20, 10), {"pts": sq, "actor": "cat", "wach": [0.0, 24.0], "spd": 0.8, "wait": [10.0, 60.0]}],
				["koch", Vector2(-2, -46)], ["kinder", Vector2(14, 10)]])
	return out


func hide_kinds() -> Array:
	return ["bush", "woodpile", "crates", "bush", "barrels"]


func grass_n() -> int:
	return 360
