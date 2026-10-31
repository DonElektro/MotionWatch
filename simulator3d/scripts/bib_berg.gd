extends "res://scripts/bib_objekte.gd"
## 3D-4.x «Bergtal» (Daniel, 31.10.2026): Dinge für die Berge - eine Erweiterung der Szenen-Bibliothek (bib_objekte.gd), gleiche
## Technik (Teile pro Zelle in einem Netz, viele gleiche als MultiMesh, Wärme-Zwilling, Sichtweite, Lite), gleiche Benutzung:
## var bib = BibBerg.new(main, scenes, knoten, transform) · bib.add(art, pos, drehung, {parameter}) · bib.many(...) · bib.finish().
## Bäume: Lärche (im Herbst gelb, im Winter kahl - sie wirft die Nadeln ab), Arve, Legföhre, Fichte; Felsblöcke in drei
## Gesteinsfarben; Alphütte, Stall, Brunnen-Trog, Hospiz, Biwakschachtel, Kapelle, Gipfelkreuz, Steinmann, gelber Wegweiser
## (Schweizer Wanderwege: gelb = Wanderweg, Spitze weiss-rot-weiss = Bergweg), Wegmarke, Strommast, Bunker im Fels,
## Ruine, Materialseilbahn, Leitplanke, Wollgras, Blumen, Murmeltier-Bau, eigenes Zelt / Isomatte mit Schlafsack, Rucksack.

const BERG := {
	"larch": ["Lärche", "Berg"], "arve": ["Arve", "Berg"], "pine_shrub": ["Legföhre", "Berg"], "spruce": ["Fichte", "Berg"],
	"boulder": ["Felsblock", "Berg"], "alp_hut": ["Alphütte", "Berg"], "cowshed": ["Kuhstall", "Berg"], "trough": ["Brunnen-Trog", "Berg"],
	"hospice": ["Hospiz", "Berg"], "bivouac": ["Biwakschachtel", "Berg"], "chapel": ["Kapelle", "Berg"], "summit_cross": ["Gipfelkreuz", "Berg"],
	"cairn": ["Steinmann", "Berg"], "hiking_sign": ["Wegweiser (Wanderweg)", "Berg"], "trail_mark": ["Wegmarke weiss-rot-weiss", "Berg"],
	"pylon": ["Strommast", "Berg"], "bunker": ["Bunker im Fels", "Berg"], "ruin": ["Ruine (alter Unterstand)", "Berg"],
	"lift_station": ["Materialseilbahn-Station", "Berg"], "guardrail": ["Leitplanke", "Berg"], "cottongrass": ["Wollgras", "Berg"],
	"flowers": ["Alpenblumen", "Berg"], "burrow": ["Murmeltier-Bau", "Berg"], "dry_wall": ["Trockenmauer", "Berg"],
	"stone_hut": ["Steinhütte", "Berg"], "bed_tent": ["Eigenes Zelt", "Berg"], "bed_mat": ["Isomatte mit Schlafsack", "Berg"],
	"backpack": ["Rucksack", "Berg"], "food_bag": ["Proviant", "Berg"], "snow_pole": ["Schneestange", "Berg"],
	"coin_telescope": ["Münzfernrohr", "Berg"], "panorama_board": ["Panoramatafel", "Berg"], "summit_box": ["Gipfelbuch-Kasten", "Berg"],
	"postauto": ["Postauto", "Berg"], "picnic_set": ["Picknick-Decke mit Korb", "Berg"], "paraglider": ["Gleitschirm (am Boden)", "Berg"],
	"tennis_ball": ["Tennisball", "Berg"], "wall_holes": ["Trockenmauer mit Löchern", "Berg"], "cheese_wheel": ["Käselaib", "Berg"],
	"wood_ski": ["Alter Holzski im Eis", "Berg"], "fondue_pot": ["Fondue-Caquelon", "Berg"], "lantern_old": ["Alte Laterne", "Berg"],
	"stepping_stone": ["Bachstein", "Berg"], "notice": ["Hinweiszettel (Selbstversorger)", "Berg"], "woodpile": ["Holzbeige", "Berg"],
	"lift_cabin": ["Kiste der Materialseilbahn", "Berg"], "bed_tent1": ["Einmannzelt", "Berg"], "bed_tarp": ["Tarp mit Isomatte", "Berg"],
	"bed_bivy": ["Biwaksack mit Isomatte", "Berg"], "stove": ["Kocher", "Berg"], "tripod": ["Stativ", "Berg"], "snow_cone": ["Lawinenkegel (Schneereste)", "Berg"]}


func make(kind: String, q := {}) -> Dictionary:
	if BERG.has(kind):
		var d: Dictionary = call("_b_" + kind, q)
		if not d.has("t"):
			d["t"] = "stone"
		if not d.has("lod"):
			d["lod"] = "mid"
		if bool(q.get("noob", false)):
			d.erase("ob")                                  # far away: no obstacle (nobody walks there)
		return d
	var d2: Dictionary = super.make(kind, q)
	if bool(q.get("noob", false)):
		d2.erase("ob")
	return d2


func _lod(gi: GeometryInstance3D, lod: String, shadow := true) -> void:
	"""like the library, plus «tree» (forest, 480 m / Lite 220 m) and «far» (big buildings, 1400 m / Lite 700 m)"""
	var far := {"big": 700.0 if _lite else 0.0, "mid": 110.0 if _lite else 170.0, "small": 45.0 if _lite else 75.0,
			"tree": 220.0 if _lite else 480.0, "far": 700.0 if _lite else 1400.0, "rock": 160.0 if _lite else 320.0}
	var end: float = far.get(lod, 0.0)
	if end > 0.0:
		gi.visibility_range_end = end
		gi.visibility_range_end_margin = 10.0
		gi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	if shadow:
		var cast: bool = lod in ["big", "far"] or (lod in ["mid", "tree", "rock"] and not _lite)
		gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


static func berg_names() -> Array:
	var out := []
	for k in BERG:
		out.append([k, BERG[k][0], BERG[k][1]])
	return out


# ---- trees ------------------------------------------------------------------------------------------------------------
# Lärche (Larix decidua): bis 35 m, im Gebirge meist 15–25 m, lichte Krone; Nadeln im Oktober goldgelb, im Winter kahl.
# Arve (Pinus cembra): 10–20 m, dichte, oft breite und unregelmässige Krone, dunkelgrün, an der Waldgrenze (1700–2400 m).
func _b_larch(q: Dictionary) -> Dictionary:
	var season := str(_q(q, "season", "sommer"))
	var col: String = {"fruehling": "86b850", "sommer": "5a8a3a", "herbst": "d8a42a", "winter": "5a4c40"}.get(season, "5a8a3a")
	var p := [C(0.1, 7.5, 0, 3.75, 0, "5a4030", 0.26, 0, 0, 0, "tree")]
	if season == "winter":                                 # bare: thin grey-brown twigs, see-through crown
		p.append(K(1.5, 6.5, 0, 6.0, 0, col, 0, 0, 0, "tree"))
		p[-1][1] = 1.1
	else:
		p.append(K(2.0, 5.5, 0, 4.2, 0, col, 0, 0, 0, "tree"))
		p.append(K(1.5, 4.5, 0, 6.6, 0, cc(col).darkened(0.06), 0, 0, 0, "tree"))
		p.append(K(0.9, 3.0, 0, 8.6, 0, cc(col).lightened(0.05), 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "tree", "low": true, "ob": [["circ", 0, 0, 0.28, 9.0]]}


func _b_arve(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "2c4a2a")
	var p := [C(0.14, 4.0, 0, 2.0, 0, "4a3828", 0.3, 0, 0, 0, "tree"), S(1.9, 3.6, 0, 3.6, 0, col, "tree"),
			S(1.4, 2.6, 0.7, 5.4, 0.3, cc(col).lightened(0.05), "tree"), S(1.2, 2.2, -0.8, 4.8, -0.4, cc(col).darkened(0.06), "tree"),
			S(0.8, 1.6, 0.1, 6.6, 0.0, col, "tree")]
	if bool(_q(q, "snow", false)):
		p.append(S(1.5, 0.9, 0.0, 5.0, 0.0, "e8ecf0", "tree"))
	return {"p": p, "t": "tree", "lod": "tree", "low": true, "ob": [["circ", 0, 0, 0.32, 7.0]]}


func _b_pine_shrub(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "2e4a26")
	var p := [S(1.3, 1.0, 0, 0.45, 0, col, "tree"), S(0.9, 0.8, 0.9, 0.35, 0.3, cc(col).lightened(0.06), "tree"),
			S(0.8, 0.7, -0.8, 0.3, -0.4, cc(col).darkened(0.05), "tree")]
	return {"p": p, "t": "tree", "lod": "mid", "low": true, "ob": [["circ", 0, 0, 1.2, 1.0, true]]}


func _b_spruce(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "22402a")
	var p := [C(0.12, 3.0, 0, 1.5, 0, "4a3624", 0.26, 0, 0, 0, "tree"), K(2.3, 5.0, 0, 3.8, 0, col, 0, 0, 0, "tree"),
			K(1.6, 4.2, 0, 6.6, 0, cc(col).darkened(0.08), 0, 0, 0, "tree"), K(0.9, 3.0, 0, 9.0, 0, col, 0, 0, 0, "tree")]
	if bool(_q(q, "snow", false)):
		p.append(K(1.9, 1.2, 0, 5.2, 0, "e8ecf0", 0, 0, 0, "tree"))
		p.append(K(1.2, 1.0, 0, 7.8, 0, "e8ecf0", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "tree", "low": true, "ob": [["circ", 0, 0, 0.3, 10.0]]}


# ---- rocks --------------------------------------------------------------------------------------------------------------
# Gesteine im Tal (Farbe): «gneis» grau, «kalk» hellgrau-gelblich, «serpentin» dunkel grün-grau, «rost» rötlich (Eisen)
const ROCK_COLS := {"gneis": ["7c7a74", "6a6862", "8e8a82"], "kalk": ["a8a294", "968f80", "bab4a6"],
		"serpentin": ["4e554c", "5c6158", "434a42"], "rost": ["8a6a54", "7a5c48", "9a7a62"]}


func _b_boulder(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 1.0))
	var cols: Array = ROCK_COLS.get(str(_q(q, "rock", "gneis")), ROCK_COLS["gneis"])
	var v := int(_q(q, "v", 0)) % 3
	var p := []
	match v:
		0:
			p = [S(r, r * 1.2, 0, r * 0.4, 0, cols[0], "stone"), S(r * 0.7, r * 0.9, r * 0.55, r * 0.3, r * 0.35, cols[1], "stone"),
				S(r * 0.6, r * 0.7, -r * 0.5, r * 0.25, -r * 0.3, cols[2], "stone")]
		1:                                                 # flat slab
			p = [B(r * 2.0, r * 0.9, r * 1.5, 0, r * 0.4, 0, cols[1], 4, 20, -6, "stone"), S(r * 0.8, r * 0.8, r * 0.5, r * 0.6, 0, cols[0], "stone")]
		_:                                                 # angular block
			p = [B(r * 1.5, r * 1.3, r * 1.4, 0, r * 0.55, 0, cols[0], 8, 35, 12, "stone"), B(r * 0.9, r * 0.8, r * 1.0, r * 0.6, r * 0.9, 0.2 * r, cols[2], -10, 10, 20, "stone")]
	if bool(_q(q, "snow", false)):
		p.append(S(r * 0.8, r * 0.35, 0, r * 0.95, 0, "eef1f4", "stone"))
	if str(_q(q, "mark", "")) != "":                       # the white-red-white mark of a mountain trail painted on it
		p.append(B(0.24, 0.07, 0.02, 0, r * 0.75 + 0.1, r * 0.95, "f2f2f2"))
		p.append(B(0.24, 0.07, 0.02, 0, r * 0.75, r * 0.96, "c8102e"))
		p.append(B(0.24, 0.07, 0.02, 0, r * 0.75 - 0.1, r * 0.95, "f2f2f2"))
	return {"p": p, "t": "stone", "lod": "rock", "low": true, "ob": [["circ", 0, 0, r * 0.9, r * 1.2]]}


func _b_cairn(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 1.1))
	var p := []
	var y := 0.0
	var r := 0.42 * h
	for i in range(5):
		p.append(S(r, r * 0.9, 0.03 * sin(i * 2.0), y + r * 0.4, 0.03 * cos(i * 2.3), ["7c7a74", "8e8a82", "6a6862"][i % 3], "stone"))
		y += r * 0.75
		r *= 0.72
	return {"p": p, "t": "stone", "lod": "small", "ob": [["circ", 0, 0, 0.4 * h, h, true]]}


func _b_trail_mark(q: Dictionary) -> Dictionary:
	# Markierung auf einem Stein: gelb (Wanderweg), weiss-rot-weiss (Bergweg), weiss-blau-weiss (Alpinwanderweg)
	var lvl := int(_q(q, "level", 1))
	var c1: String = ["f5c400", "f2f2f2", "f2f2f2"][clampi(lvl, 0, 2)]
	var c2: String = ["f5c400", "c8102e", "1a5ab0"][clampi(lvl, 0, 2)]
	return {"p": [S(0.35, 0.5, 0, 0.18, 0, "7c7a74", "stone"), B(0.2, 0.06, 0.02, 0, 0.28, 0.33, c1), B(0.2, 0.06, 0.02, 0, 0.22, 0.34, c2),
			B(0.2, 0.06, 0.02, 0, 0.16, 0.33, c1)], "t": "stone", "lod": "small"}


# ---- buildings -------------------------------------------------------------------------------------------------------------
func _shutters(p: Array, x: float, y: float, z: float, side := false) -> void:
	"""a small window with red-white shutters (the typical Swiss alp hut)"""
	if side:
		p.append(B(0.06, 0.6, 0.55, z, y, x, "%ffd9a0", 0, 0, 0, "window"))
		for s in [-1.0, 1.0]:
			p.append(B(0.05, 0.62, 0.3, z + signf(z) * 0.03, y, x + s * 0.45, "b8241c"))
	else:
		p.append(B(0.55, 0.6, 0.06, x, y, z, "%ffd9a0", 0, 0, 0, "window"))
		for s in [-1.0, 1.0]:
			p.append(B(0.3, 0.62, 0.05, x + s * 0.45, y, z + signf(z) * 0.03, "b8241c"))


func _b_alp_hut(q: Dictionary) -> Dictionary:
	# Alphütte: unten Bruchstein (Stall/Käsekeller), oben Holz (Wohnteil), flaches Dach mit Steinplatten, Kamin
	var w := float(_q(q, "w", 9.0))
	var dd := float(_q(q, "d", 7.5))
	var p := [B(w, 2.4, dd, 0, 1.2, 0, "a49c90", 0, 0, 0, "stone"), B(w - 0.1, 2.3, dd - 0.1, 0, 3.55, 0, "5a3a22"),
			P(w + 1.2, 1.6, dd + 1.0, 0, 5.5, 0, "7a7670", 0, 90, 0), B(0.7, 1.8, 0.7, w * 0.3, 6.2, 0, "8a8378", 0, 0, 0, "stone"),
			B(1.0, 2.0, 0.08, -w * 0.25, 1.0, dd / 2.0 + 0.04, "4a3220"), B(0.9, 0.12, 0.6, -w * 0.25, 0.06, dd / 2.0 + 0.4, "8b8680", 0, 0, 0, "stone")]
	p[2] = P(dd + 1.0, 1.6, w + 1.2, 0, 5.5, 0, "7a7670", 0, 90, 0)
	for x in [-w * 0.3, 0.05, w * 0.3]:
		_shutters(p, x, 3.6, dd / 2.0 + 0.04)
	_shutters(p, 0.0, 3.6, w / 2.0 + 0.04, true)
	_shutters(p, 0.0, 3.6, -w / 2.0 - 0.04, true)
	p.append(B(0.5, 0.35, 0.06, w * 0.15, 1.5, dd / 2.0 + 0.04, "1a1410"))      # small cellar window
	p.append(B(2.0, 0.08, 0.45, w * 0.18, 0.45, dd / 2.0 + 0.6, "8a5a32", 0, 0, 0, "tree"))   # the bench in front
	p.append(B(0.08, 0.45, 0.4, w * 0.18 - 0.9, 0.22, dd / 2.0 + 0.6, "5a3a22"))
	p.append(B(0.08, 0.45, 0.4, w * 0.18 + 0.9, 0.22, dd / 2.0 + 0.6, "5a3a22"))
	p.append(B(1.6, 0.3, 0.06, -w * 0.25, 2.3, dd / 2.0 + 0.06, "e8dcc0"))       # the name board
	p.append(B(0.5, 0.1, 0.5, w * 0.3, 7.15, 0, "5a5652", 0, 0, 0, 55.0 if bool(_q(q, "warm", true)) else "stone"))   # chimney top warm (stove)
	var lb := [[str(_q(q, "text", "Alp")), -w * 0.25, 2.3, dd / 2.0 + 0.1, 30, 0.0, "2a1a10"]]
	if not bool(_q(q, "warm", true)):                       # self-catering hut, nobody there: the windows stay dark
		for part in p:
			if typeof(part[7]) == TYPE_STRING and str(part[7]).begins_with("%"):
				part[7] = "2a2620"
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 6.5], ["box", w * 0.18, dd / 2.0 + 0.6, 2.1, 0.5, 0.5]],
			"door": [-w * 0.25, 0.0, dd / 2.0 + 0.05, 1.0, 2.0, "4a3220"], "lights": [[-w * 0.25, 2.4, dd / 2.0 + 0.5]],
			"fx": [["smoke", w * 0.3, 7.3, 0]] if bool(_q(q, "warm", true)) else [], "labels": lb}


func _b_cowshed(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 16.0))
	var dd := float(_q(q, "d", 8.0))
	var p := [B(w, 1.0, dd, 0, 0.5, 0, "9a9286", 0, 0, 0, "stone"), B(w - 0.1, 2.2, dd - 0.1, 0, 2.1, 0, "6a4a2c"),
			P(dd + 1.4, 1.8, w + 0.8, 0, 4.1, 0, "6e6a64", 0, 90, 0)]
	var n := int(w / 4.0)
	for i in range(n):
		var x := -w / 2.0 + w * (i + 0.5) / n
		p.append(B(1.3, 1.9, 0.07, x, 1.05, dd / 2.0 + 0.04, "4a3220"))
		p.append(B(0.6, 0.35, 0.05, x + 1.1, 2.4, dd / 2.0 + 0.04, "1a1410"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 5.0]]}


func _b_trough(q: Dictionary) -> Dictionary:
	# Brunnen: ein langer Holztrog (ausgehöhlter Stamm) mit Röhre, das Wasser läuft immer
	var L := float(_q(q, "len", 3.0))
	var p := [B(L, 0.55, 0.7, 0, 0.42, 0, "6a4a2c", 0, 0, 0, "tree"), B(L - 0.2, 0.04, 0.5, 0, 0.66, 0, "3a6a80", 0, 0, 0, "pond"),
			B(0.22, 1.3, 0.22, -L / 2.0 - 0.1, 0.65, 0, "5a3a22", 0, 0, 0, "tree"), C(0.025, 0.5, -L / 2.0 + 0.15, 1.15, 0, "6a6a66", 0, 0, 0, 90),
			C(0.02, 0.45, -L / 2.0 + 0.4, 0.92, 0, "a8d8f0", 0, 0, 0, 0, "pond"), B(0.15, 0.3, 0.6, -L / 2.0 + 0.1, 0.15, 0, "5a3a22"),
			B(0.15, 0.3, 0.6, L / 2.0 - 0.1, 0.15, 0, "5a3a22")]
	if bool(_q(q, "ice", false)):
		p[1] = B(L - 0.2, 0.05, 0.5, 0, 0.67, 0, "d8e8f0", 0, 0, 0, "stone")
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["box", 0, 0, L + 0.3, 0.8, 0.8]]}


func _b_hospice(q: Dictionary) -> Dictionary:
	# Hospiz auf der Passhöhe: massiver Steinbau, weiss verputzt, drei Stockwerke, Gaststube mit Licht, Parkplatz davor
	var w := float(_q(q, "w", 20.0))
	var dd := float(_q(q, "d", 12.0))
	var p := [B(w, 10.0, dd, 0, 5.0, 0, "e8e2d4", 0, 0, 0, "stone"), P(dd + 1.2, 3.5, w + 1.0, 0, 11.75, 0, "5a5a5e", 0, 90, 0),
			B(w + 0.1, 1.0, dd + 0.1, 0, 0.5, 0, "8a8478", 0, 0, 0, "stone"), B(1.6, 2.4, 0.08, 0, 1.2, dd / 2.0 + 0.05, "5a3820"),
			B(0.8, 2.0, 0.8, w * 0.35, 13.0, 0, "d8d2c4", 0, 0, 0, "stone"), B(5.0, 0.12, 2.0, 0, 2.9, dd / 2.0 + 1.0, "5a5a5e")]
	p[1] = P(w + 1.0, 3.5, dd + 1.2, 0, 11.75, 0, "5a5a5e")
	for fl in range(3):
		_window_row(p, 7, w * 0.92, 1.8 + fl * 3.0, dd / 2.0 + 0.04, 0.9, 1.2, "%ffd9a0" if fl == 0 else "%e8d0a0")
		_window_row(p, 4, dd * 0.85, 1.8 + fl * 3.0, w / 2.0 + 0.04, 0.9, 1.2, "%e8d0a0", true)
	p.append(B(4.0, 0.7, 0.08, 0, 4.0, dd / 2.0 + 0.06, "f2f2f2"))
	var lb := [[str(_q(q, "text", "Hospiz")), 0, 4.0, dd / 2.0 + 0.12, 60, 0.0, "6a1a10"]]
	return {"p": p, "t": "caravan", "lod": "far", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 14.0]], "lights": [[0, 2.6, dd / 2.0 + 0.8], [w * 0.4, 2.6, dd / 2.0 + 0.8]],
			"door": [0.0, 0.0, dd / 2.0 + 0.06, 1.6, 2.4, "5a3820"], "labels": lb, "fx": [["smoke", w * 0.35, 14.0, 0], ["flag", -w / 2.0 - 3.0, 0, dd / 2.0, "c8102e"]]}


func _b_bivouac(q: Dictionary) -> Dictionary:
	# Biwakschachtel: Notunterkunft aus Blech (rot / orange), auf Fundament, 2,4 × 2,2 m, halbrunder Rücken, eine Tür
	var col = _q(q, "col", "c8402a")
	var p := [B(2.6, 0.4, 2.8, 0, 0.2, 0, "8a857d", 0, 0, 0, "stone"), B(2.4, 1.5, 2.6, 0, 1.15, 0, col, 0, 0, 0, "metal"),
			C(1.2, 2.6, 0, 1.9, 0, col, 0, 90, 0, 0, "metal"), B(0.7, 1.5, 0.05, 0.4, 1.15, 1.32, "6a2a1a", 0, 0, 0, "metal"),
			B(0.4, 0.3, 0.05, -0.6, 1.5, 1.32, "%c8d8e0", 0, 0, 0, "window"), B(0.06, 0.06, 0.12, 0.65, 1.15, 1.37, "c0c0c0")]
	for x in [-1.0, 1.0]:
		p.append(ROD(Vector3(x * 1.1, 2.6, 0), Vector3(x * 2.6, 0.0, -0.6), 0.03, "8a8a8a"))     # guy wires (storms)
	return {"p": p, "t": "metal", "lod": "big", "ob": [["box", 0, 0, 2.7, 2.9, 3.1]], "door": [0.4, 0.0, 1.33, 0.7, 1.5, "6a2a1a"],
			"labels": [[str(_q(q, "text", "Biwak")), -0.2, 2.1, 1.34, 28, 0.0, "f2f2f2"]]}


func _b_chapel(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 5.0))
	var L := float(_q(q, "len", 7.0))
	var p := [B(w, 3.6, L, 0, 1.8, 0, "f2eee4", 0, 0, 0, "stone"), P(w + 0.8, 2.4, L + 0.6, 0, 4.8, 0, "5a5652"),
			B(1.4, 2.4, 0.08, 0, 1.2, L / 2.0 + 0.04, "5a3820"), B(1.2, 1.4, 1.2, 0, 6.3, -L / 2.0 + 0.6, "f2eee4", 0, 0, 0, "stone"),
			K(0.95, 2.0, 0, 8.0, -L / 2.0 + 0.6, "4a4a4e"), B(0.08, 0.9, 0.08, 0, 9.4, -L / 2.0 + 0.6, "c8a43a"), B(0.5, 0.08, 0.08, 0, 9.6, -L / 2.0 + 0.6, "c8a43a"),
			C(0.5, 0.05, 0, 4.4, L / 2.0 + 0.05, "%ffe0a0", 0, 90, 0, 0, "window")]
	for z in [-L * 0.2, L * 0.2]:
		p.append(B(0.06, 1.3, 0.6, w / 2.0 + 0.03, 2.2, z, "%e8c890", 0, 0, 0, "window"))
		p.append(B(0.06, 1.3, 0.6, -w / 2.0 - 0.03, 2.2, z, "%e8c890", 0, 0, 0, "window"))
	return {"p": p, "t": "stone", "lod": "far", "ob": [["box", 0, 0, w + 0.2, L + 0.2, 5.0]]}


func _b_summit_cross(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 4.0))
	var p := [B(0.2, h, 0.2, 0, h / 2.0, 0, "6a4a2e", 0, 0, 0, "tree"), B(h * 0.5, 0.18, 0.2, 0, h * 0.75, 0, "6a4a2e", 0, 0, 0, "tree"),
			S(0.7, 0.6, 0, 0.2, 0, "7c7a74", "stone"), B(0.3, 0.2, 0.06, 0, h * 0.55, 0.12, "c8a43a", 0, 0, 0, "metal")]
	return {"p": p, "t": "tree", "lod": "big", "ob": [["circ", 0, 0, 0.7, h]]}


func _b_hiking_sign(q: Dictionary) -> Dictionary:
	# Wegweiser der Schweizer Wanderwege: gelbe Pfeil-Tafeln (Ziel und Zeit), oben die weisse Standort-Tafel;
	# Bergweg: Spitze weiss-rot-weiss. Quelle: Handbuch Signalisation Wanderwege (ASTRA / Schweizer Wanderwege 2013).
	var arms: Array = _q(q, "arms", [["Bergtal", "30 min", false]])
	var here := str(_q(q, "here", ""))
	var p := [C(0.045, 2.6, 0, 1.3, 0, "8a8a8a", 0, 0, 0, 0, "metal")]
	var lb := []
	var y := 2.25
	if here != "":
		p.append(B(0.62, 0.22, 0.03, 0, 2.62, 0, "f2f2f2"))
		lb.append([here, 0, 2.62, 0.02, 14, 0.0, "1a1a1a"])
	for i in range(arms.size()):
		var a: Array = arms[i]
		var dirx := 1.0 if i % 2 == 0 else -1.0
		p.append(B(0.95, 0.18, 0.03, dirx * 0.5, y, 0, "f5c400"))
		p.append(P(0.18, 0.18, 0.03, dirx * 1.06, y, 0, "f5c400", 0, 0, -90.0 * dirx))
		var lvl := int(a[2]) if a.size() > 2 else 0
		if lvl > 0:                                        # mountain trail: white-red-white tip · alpine route: blue-white-blue
			var c1 := "f2f2f2" if lvl == 1 else "1a5ab0"
			var c2 := "c8102e" if lvl == 1 else "f2f2f2"
			p.append(B(0.12, 0.06, 0.032, dirx * 0.92, y + 0.06, 0, c1))
			p.append(B(0.12, 0.06, 0.032, dirx * 0.92, y, 0, c2))
			p.append(B(0.12, 0.06, 0.032, dirx * 0.92, y - 0.06, 0, c1))
		lb.append(["%s  %s" % [str(a[0]), str(a[1]) if a.size() > 1 else ""], dirx * 0.42, y, 0.02, 13, 0.0, "1a1a1a"])
		y -= 0.24
	return {"p": p, "t": "metal", "lod": "small", "ob": [["circ", 0, 0, 0.1, 2.6]], "labels": lb}


func _b_snow_pole(_q: Dictionary) -> Dictionary:
	# Schneestange am Strassenrand (rot-weiss, 2 m) - im Winter zeigt sie, wo die Strasse ist
	return {"p": [B(0.05, 2.0, 0.05, 0, 1.0, 0, "f2f2f2"), B(0.052, 0.3, 0.052, 0, 1.7, 0, "c8102e"), B(0.052, 0.3, 0.052, 0, 1.1, 0, "c8102e")], "t": "metal", "lod": "small"}


func _b_pylon(q: Dictionary) -> Dictionary:
	# Strommast (Fachwerk aus Stahl), 25 m, drei Ausleger; die Leiter (Seile) zieht die Szene von Mast zu Mast
	var h := float(_q(q, "h", 24.0))
	var p := []
	var b := 2.6
	var t := 0.5
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			p.append(ROD(Vector3(sx * b, 0, sz * b), Vector3(sx * t, h, sz * t), 0.12, "8a8f96", "metal"))
	for k in range(5):
		var f := (k + 0.5) / 5.0
		var r := lerpf(b, t, f)
		var y := f * h
		p.append(B(2.0 * r, 0.06, 0.06, 0, y, r, "8a8f96", 0, 0, 0, "metal"))
		p.append(B(2.0 * r, 0.06, 0.06, 0, y, -r, "8a8f96", 0, 0, 0, "metal"))
		p.append(B(0.06, 0.06, 2.0 * r, r, y, 0, "8a8f96", 0, 0, 0, "metal"))
		p.append(B(0.06, 0.06, 2.0 * r, -r, y, 0, "8a8f96", 0, 0, 0, "metal"))
	for k in range(2):
		var y2 := h * (0.78 + 0.16 * k)
		p.append(B(9.0 - k * 3.0, 0.25, 0.25, 0, y2, 0, "8a8f96", 0, 0, 0, "metal"))
	p.append(B(0.25, 0.25, 0.25, 0, h + 0.2, 0, "8a8f96", 0, 0, 0, "metal"))
	return {"p": p, "t": "metal", "lod": "far", "ob": [["box", 0, 0, 5.4, 5.4, 4.0]]}


func _b_bunker(q: Dictionary) -> Dictionary:
	# alter Militär-Bunker im Fels (Réduit): nur die getarnte Betonfront mit Stahltür und Schiessscharte schaut heraus
	var cols: Array = ROCK_COLS[str(_q(q, "rock", "gneis"))]
	var p := [S(4.5, 6.0, 0, 1.8, -2.5, cols[0], "stone"), S(3.0, 4.0, 3.5, 1.0, -1.5, cols[1], "stone"), S(3.2, 4.4, -3.6, 1.2, -1.8, cols[2], "stone"),
			B(4.2, 3.0, 0.6, 0, 1.5, 1.6, "6e6a5a", 0, 0, 0, "stone"), B(1.0, 2.0, 0.08, -0.9, 1.0, 1.94, "4a4a3a", 0, 0, 0, "metal"),
			B(0.9, 0.18, 0.08, 1.1, 2.0, 1.94, "0a0a0a"), B(1.2, 0.5, 0.62, 1.1, 2.9, 1.6, "5a6a4a"), B(1.4, 0.6, 0.62, -1.4, 0.4, 1.62, "5e5a48")]
	return {"p": p, "t": "stone", "lod": "big", "ob": [["circ", 0, -2.0, 4.6, 6.0], ["box", 0, 1.6, 4.4, 0.8, 3.0]],
			"door": [-0.9, 0.0, 1.95, 1.0, 2.0, "4a4a3a"]}


func _b_ruin(q: Dictionary) -> Dictionary:
	# Ruine eines alten Stein-Unterstands (Trockenmauern, eingefallen, ohne Dach)
	var w := float(_q(q, "w", 6.0))
	var dd := float(_q(q, "d", 4.5))
	var c := "8a8478"
	var p := [B(w, 1.6, 0.6, 0, 0.8, -dd / 2.0, c, 0, 0, 0, "stone"), B(0.6, 2.2, dd, -w / 2.0, 1.1, 0, c, 0, 0, 0, "stone"),
			B(0.6, 1.0, dd * 0.6, w / 2.0, 0.5, -dd * 0.2, c, 0, 0, 0, "stone"), B(w * 0.4, 0.7, 0.6, -w * 0.3, 0.35, dd / 2.0, c, 0, 0, 0, "stone"),
			B(w * 0.25, 1.3, 0.6, w * 0.38, 0.65, dd / 2.0, c, 0, 0, 0, "stone"), P(0.6, 0.9, dd, -w / 2.0, 2.65, 0, c)]
	for i in range(7):
		var a := i * 1.7
		p.append(S(0.25 + 0.05 * (i % 3), 0.3, cos(a) * w * 0.4, 0.1, sin(a) * dd * 0.35 + 0.2, "7c7a74", "stone"))
	p.append(B(1.2, 0.08, 0.15, 0.4, 0.05, 0.3, "4a3a2a", 0, 30, 4, "tree"))                       # an old beam
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["box", 0, -dd / 2.0, w, 0.7, 1.6], ["box", -w / 2.0, 0, 0.7, dd, 2.2], ["box", w / 2.0, -dd * 0.2, 0.7, dd * 0.6, 1.0]]}


func _b_stone_hut(q: Dictionary) -> Dictionary:
	# kleine Steinhütte / Schutzhütte (Steinplattendach)
	var w := float(_q(q, "w", 4.0))
	var dd := float(_q(q, "d", 3.5))
	var p := [B(w, 2.2, dd, 0, 1.1, 0, "8e887c", 0, 0, 0, "stone"), P(dd + 0.6, 1.0, w + 0.6, 0, 2.7, 0, "6e6a64", 0, 90, 0),
			B(0.8, 1.7, 0.06, 0, 0.85, dd / 2.0 + 0.03, "4a3220")]
	p[1] = P(w + 0.6, 1.0, dd + 0.6, 0, 2.7, 0, "6e6a64")
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["box", 0, 0, w + 0.1, dd + 0.1, 3.0]]}


func _b_lift_station(q: Dictionary) -> Dictionary:
	# Materialseilbahn (Transportseilbahn zur Alp): Holzhäuschen mit Seilrad und kleinem Motor, die Last-Kiste am Seil
	var top := bool(_q(q, "top", false))
	var p := [B(3.0, 2.4, 2.6, 0, 1.2, 0, "6a4a2c"), P(3.4, 0.8, 3.0, 0, 2.8, 0, "5a5652"), B(0.2, 3.6, 0.2, -1.2, 1.8, -1.6, "5a5a5e", 0, 0, 0, "metal"),
			B(0.2, 3.6, 0.2, 1.2, 1.8, -1.6, "5a5a5e", 0, 0, 0, "metal"), B(2.8, 0.25, 0.25, 0, 3.5, -1.6, "5a5a5e", 0, 0, 0, "metal"),
			C(0.6, 0.12, 0, 3.6, -1.6, "3a3a3e", 0, 90, 0, 0, "metal")]
	if not top:
		p.append(B(0.8, 0.6, 0.6, 0.8, 0.5, -1.0, "4a5a6a", 0, 0, 0, "metal"))
		p.append(B(1.2, 0.7, 1.0, 0, 2.6, -2.8, "8a8a86", 0, 0, 0, "metal"))         # the load box, parked
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, 3.1, 2.7, 3.0]]}


func _b_guardrail(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 4.0))
	return {"p": [B(L, 0.3, 0.06, 0, 0.6, 0, "b8bcc0", 0, 0, 0, "metal"), B(0.1, 0.7, 0.1, -L / 2.0, 0.35, -0.05, "8a8f96", 0, 0, 0, "metal")],
			"t": "metal", "lod": "mid", "ob": [["box", 0, 0, L, 0.2, 0.8, true]]}


func _b_dry_wall(q: Dictionary) -> Dictionary:
	# Trockenmauer (Alpweiden): unregelmässig, oben ein paar Decksteine
	var L := float(_q(q, "len", 3.0))
	var h := float(_q(q, "h", 0.9))
	var p := [B(L, h, 0.6, 0, h / 2.0 - 0.1, 0, "8a8478", 0, 0, 0, "stone"), S(0.32, 0.3, -L * 0.3, h - 0.05, 0, "7c7a74", "stone"),
			S(0.3, 0.26, L * 0.15, h - 0.08, 0.05, "948e82", "stone")]
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["box", 0, 0, L, 0.7, h, true]]}


# ---- plants -------------------------------------------------------------------------------------------------------------
func _b_cottongrass(q: Dictionary) -> Dictionary:
	# Wollgras (Eriophorum) im Moor: weisse Wattebäuschchen auf dünnen Halmen, 30–50 cm
	var p := []
	var white := "f4f4ee" if str(_q(q, "season", "sommer")) in ["sommer", "fruehling"] else "c8b890"
	for i in range(6):
		var a := i * 1.05
		var r := 0.12 + 0.05 * (i % 2)
		p.append(B(0.012, 0.42, 0.012, cos(a) * r, 0.21, sin(a) * r, "6a7a3a", 0, 0, 6.0 * (i % 3 - 1), "tree"))
		p.append(S(0.035, 0.07, cos(a) * r, 0.44, sin(a) * r, white, "tree"))
	return {"p": p, "t": "tree", "lod": "small", "low": true}


func _b_flowers(q: Dictionary) -> Dictionary:
	# Alpenblumen-Büschel (Enzian blau, Arnika gelb, Alpenrose rot, Edelweiss weiss, Glockenblume violett)
	var cols := ["2a4ab8", "f0c020", "c8284a", "f2f2ea", "8a5ac8"]
	var k := int(_q(q, "v", 0))
	if k == 4:                                             # Krokusse (Frühling): violett und weiss
		cols = ["9a6ad8", "f2f0f8", "8a5ac8", "b090e0", "f2f2ea"]
	var p := [S(0.22, 0.1, 0, 0.04, 0, "4a7a30", "tree")]
	for i in range(5):
		var a := i * 1.3 + k
		p.append(S(0.03, 0.04, cos(a) * 0.14, 0.14 + 0.03 * (i % 2), sin(a) * 0.14, cols[(i + k) % cols.size()], "tree"))
	return {"p": p, "t": "tree", "lod": "small", "low": true}


func _b_burrow(_q: Dictionary) -> Dictionary:
	# Murmeltier-Bau: Erdhügel mit dunklem Eingang (die Tiere verschwinden darin)
	return {"p": [S(0.9, 0.5, 0, 0.0, 0, "6a5a40", "road"), S(0.22, 0.3, 0, 0.12, 0.62, "1a140e", "road"), S(0.35, 0.3, 0.6, 0.05, -0.3, "7c7a74", "stone")],
			"t": "road", "lod": "small"}


# ---- your sleeping place --------------------------------------------------------------------------------------------------
func _b_bed_tent(q: Dictionary) -> Dictionary:
	# eigenes Kuppelzelt (2 Personen), 2,1 × 1,4 m, 1,1 m hoch; drinnen ist es wärmer (Mensch im Schlafsack)
	var col = _q(q, "col", "e86a1a")
	var p := [S(1.15, 1.1 * 2.0 * 0.5, 0, 0.0, 0, col, "tent"), B(2.4, 0.02, 1.7, 0, 0.01, 0, "3a4a3a", 0, 0, 0, "tent"),
			B(0.7, 0.75, 0.05, 0, 0.38, 1.02, "2a2a2a", 0, 0, 0, "tent"), ROD(Vector3(-1.1, 0, -0.8), Vector3(1.1, 1.1, 0.8), 0.015, "2a2a2a"),
			ROD(Vector3(1.1, 0, -0.8), Vector3(-1.1, 1.1, 0.8), 0.015, "2a2a2a")]
	p[0] = ["s", 1.2, 2.2, 0, 0, 0.0, 0, col, 0, 0, 0, 24.0]                 # the tent wall above you: a little warmer
	return {"p": p, "t": "tent", "lod": "mid", "ob": [["box", 0, 0, 2.4, 2.2, 1.1]]}


func _b_bed_mat(q: Dictionary) -> Dictionary:
	# Isomatte + Schlafsack unter freiem Himmel; im Schlafsack ist ein Mensch: warm im Wärmebild (Oberfläche ca. 25–30 °C)
	var col = _q(q, "col", "2a5ab0")
	var p := [B(0.6, 0.03, 1.9, 0, 0.015, 0, "3a8a3a", 0, 0, 0, "tent"), C(0.27, 1.7, 0, 0.2, 0.0, col, 0.2, 90, 0, 0, 27.0),
			S(0.22, 0.3, 0, 0.18, -0.95, "c8a080", 33.0), S(0.24, 0.24, 0, 0.2, -0.9, cc(col).darkened(0.2), 26.0)]
	return {"p": p, "t": "tent", "lod": "small", "ob": [["box", 0, 0, 0.7, 2.1, 0.4, true]]}


func _b_backpack(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "b83a2a")
	return {"p": [B(0.35, 0.6, 0.25, 0, 0.3, 0, col, 0, 0, 0, "tent"), B(0.3, 0.12, 0.27, 0, 0.62, 0, cc(col).darkened(0.2), 0, 0, 0, "tent"),
			B(0.28, 0.25, 0.08, 0, 0.25, 0.16, cc(col).darkened(0.1), 0, 0, 0, "tent"), C(0.06, 0.4, 0, 0.62, -0.05, "3a5a3a", 0, 0, 0, 90, "tent")],
			"t": "tent", "lod": "small", "ob": [["circ", 0, 0, 0.3, 0.7, true]]}


func _b_food_bag(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.13, 0.32, 0, 0.16, 0, "d8c070", 0.15, 0, 0, 0, "tent"), C(0.05, 0.08, 0, 0.36, 0, "a89050", 0, 0, 0, 0, "tent")], "t": "tent", "lod": "small"}


# ---- viewpoints (Aussichtspunkte, Daniel 31.10.2026) ----------------------------------------------------------------------
func _b_coin_telescope(_q: Dictionary) -> Dictionary:
	# Münzfernrohr (wie auf vielen Aussichtspunkten): Säule, Kopf mit zwei Okularen, Münzeinwurf
	return {"p": [C(0.09, 1.1, 0, 0.55, 0, "3a5a8a", 0.14, 0, 0, 0, "metal"), B(0.42, 0.32, 0.6, 0, 1.3, 0, "3a5a8a", -8, 0, 0, "metal"),
			C(0.07, 0.25, -0.08, 1.33, -0.38, "1a1a1a", 0, -82, 0, 0, "metal"), C(0.07, 0.25, 0.08, 1.33, -0.38, "1a1a1a", 0, -82, 0, 0, "metal"),
			C(0.14, 0.3, 0, 1.28, 0.38, "2a2a2a", 0, 82, 0, 0, "metal"), B(0.08, 0.12, 0.02, 0.22, 1.25, 0, "c8a43a", 0, 0, 0, "metal")],
			"t": "metal", "lod": "small", "ob": [["circ", 0, 0, 0.25, 1.5]]}


func _b_panorama_board(q: Dictionary) -> Dictionary:
	# Panoramatafel: schräge Tafel auf zwei Pfosten, die Gipfel beschriftet (labels: [[name, Höhe]] von links nach rechts)
	var peaks: Array = _q(q, "peaks", [])
	var w := 2.4
	var p := [B(0.1, 0.9, 0.1, -w * 0.4, 0.45, 0, "6a4a2e", 0, 0, 0, "tree"), B(0.1, 0.9, 0.1, w * 0.4, 0.45, 0, "6a4a2e", 0, 0, 0, "tree"),
			B(w, 0.06, 0.7, 0, 1.0, 0, "e8e0cc", 30, 0, 0), B(w + 0.1, 0.05, 0.75, 0, 0.97, 0.01, "5a4a3a", 30, 0, 0)]
	var lb := []
	for i in range(peaks.size()):
		var x := -w * 0.45 + w * 0.9 * (i + 0.5) / maxf(1.0, peaks.size())
		var pk: Array = peaks[i]
		p.append(P(0.18, 0.12, 0.02, x, 1.12, -0.1, "6a7a8a", -60, 0, 0))
		lb.append(["%s\n%s m" % [str(pk[0]), str(pk[1])], x, 1.08, 0.08, 9, 0.0, "1a1a1a"])
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0, w, 0.8, 1.2]], "labels": lb}


func _b_summit_box(_q: Dictionary) -> Dictionary:
	# Gipfelbuch-Kasten aus Blech am Kreuz (Gipfelbuch: Vignette 7)
	return {"p": [B(0.3, 0.22, 0.18, 0, 1.3, 0.16, "8a8f96", 0, 0, 0, "metal"), B(0.32, 0.04, 0.2, 0, 1.42, 0.16, "6a6f76", 0, 0, 0, "metal")], "t": "metal", "lod": "small"}


func _b_postauto(q: Dictionary) -> Dictionary:
	# Postauto (gelber Reisebus, 12 m) - das Dreiklang-Horn «Tü-ta-to» spielt die Szene (bergtal.gd postauto_horn)
	var L := 12.0
	var p := [B(L, 2.6, 2.5, 0, 1.7, 0, "f5c400", 0, 0, 0, "car"), B(L - 0.6, 0.9, 2.52, 0.1, 2.3, 0, "%2a3a4a", 0, 0, 0, "window"),
			B(0.08, 1.6, 2.3, L / 2.0 + 0.02, 2.0, 0, "%2a3a4a", 0, 0, 0, "window"), B(L, 0.35, 2.52, 0, 0.55, 0, "2a2a2a", 0, 0, 0, "car"),
			B(L, 0.12, 2.54, 0, 1.25, 0, "c8102e", 0, 0, 0, "car"), B(1.2, 0.3, 0.05, L / 2.0 - 1.0, 3.1, 1.26, "f2f2f2")]
	for x in [-L * 0.32, L * 0.32]:
		for z in [-1.15, 1.15]:
			p.append(C(0.5, 0.3, x, 0.5, z, "1a1a1a", 0, 90, 0, 0, "car"))
	p.append(B(0.4, 0.3, 0.6, -L / 2.0 + 0.3, 1.0, 0, "5a5a5a", 0, 0, 0, 60.0))          # the engine at the back: warm
	return {"p": p, "t": "car", "lod": "far", "ob": [["box", 0, 0, L + 0.2, 2.6, 3.0]], "lights": [[L / 2.0 + 0.1, 1.0, 0.9], [L / 2.0 + 0.1, 1.0, -0.9]],
			"labels": [["PostAuto", 0, 2.95, 1.27, 40, 0.0, "1a1a1a"]]}


func _b_picnic_set(_q: Dictionary) -> Dictionary:
	return {"p": [B(1.6, 0.01, 1.3, 0, 0.01, 0, "c8283a", 0, 0, 0, "tent"), B(1.6, 0.012, 0.12, 0, 0.012, 0.3, "f2f2f2"), B(1.6, 0.012, 0.12, 0, 0.012, -0.3, "f2f2f2"),
			B(0.5, 0.3, 0.35, 0.4, 0.15, 0.2, "a07a4a", 0, 0, 0, "tree"), C(0.04, 0.3, -0.3, 0.15, 0.3, "2a5a2a", 0, 0, 0, 0, "glass"),
			C(0.25, 0.08, -0.4, 0.05, -0.3, "f0f0e8")], "t": "tent", "lod": "small"}


func _b_paraglider(q: Dictionary) -> Dictionary:
	# Gleitschirm am Boden ausgelegt (Kappe 10 m) - fliegend kommt er im Ablauf (Vignette 27)
	var col = _q(q, "col", "e85a1a")
	var p := []
	for i in range(9):
		var x := -5.0 + i * 1.25
		p.append(B(1.2, 0.08, 2.4 - absf(x) * 0.14, x, 0.05 + 0.04 * (i % 2), 0, col if i % 3 != 1 else "2a5ab0", 0, 0, 0, "tent"))
	return {"p": p, "t": "tent", "lod": "mid"}


func _b_tennis_ball(_q: Dictionary) -> Dictionary:
	return {"p": [S(0.034, 0.068, 0, 0.034, 0, "d8e830", "tent")], "t": "tent", "lod": "small"}


func _b_wall_holes(q: Dictionary) -> Dictionary:
	# Trockenmauer mit Löchern (das Hermelin schaut heraus: Vignette 19)
	var L := float(_q(q, "len", 6.0))
	var p := [B(L, 1.1, 0.7, 0, 0.45, 0, "8a8478", 0, 0, 0, "stone")]
	for i in range(5):
		p.append(B(0.14, 0.12, 0.72, -L * 0.4 + i * L * 0.2, 0.3 + 0.35 * (i % 2), 0, "120e0a", 0, 0, 0, "stone"))
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["box", 0, 0, L, 0.8, 1.1, true]]}


func _b_cheese_wheel(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.3, 0.12, 0, 0.06, 0, "c89a3a", 0, 0, 0, 0, "tent"), C(0.28, 0.125, 0, 0.06, 0, "e0c070", 0, 0, 0, 0, "tent")], "t": "tent", "lod": "small"}


func _b_wood_ski(_q: Dictionary) -> Dictionary:
	return {"p": [B(0.08, 0.03, 1.9, 0, 0.05, 0, "6a4a2a", 18, 10, 0, "tree"), B(0.08, 0.03, 0.25, 0, 0.36, -0.9, "6a4a2a", 60, 10, 0, "tree"),
			B(0.1, 0.06, 0.2, 0, 0.12, 0.1, "3a2a1a", 18, 10, 0, "tree")], "t": "tree", "lod": "small"}


func _b_fondue_pot(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.15, 0.12, 0, 0.18, 0, "b8402a", 0.12, 0, 0, 0, "stone"), C(0.02, 0.25, 0.22, 0.2, 0, "3a2a1a", 0, 0, 0, 90),
			B(0.3, 0.12, 0.3, 0, 0.06, 0, "3a3a3a", 0, 0, 0, "metal")], "t": "stone", "lod": "small"}


func _b_lantern_old(_q: Dictionary) -> Dictionary:
	return {"p": [B(0.16, 0.24, 0.16, 0, 0.14, 0, "4a4030", 0, 0, 0, "metal"), B(0.12, 0.16, 0.12, 0, 0.14, 0, "%c8b070", 0, 0, 0, "window"),
			TO(0.04, 0.05, 0, 0.3, 0, "4a4030", 90, 0, 0, "metal")], "t": "metal", "lod": "small"}


func _b_stepping_stone(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 0.4))
	return {"p": [C(r, 0.35, 0, 0.1, 0, "8a8680", r * 1.1, 0, 0, 0, "stone")], "t": "stone", "lod": "small"}


func _b_notice(q: Dictionary) -> Dictionary:
	return {"p": [B(0.42, 0.6, 0.01, 0, 0, 0, "f4f0e0")], "t": "stone", "lod": "small",
			"labels": [[str(_q(q, "text", "")), 0, 0.05, 0.012, 7, 0.0, "1a1a1a"]]}


func _b_woodpile(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 2.0))
	var p := [B(L, 1.2, 0.5, 0, 0.6, 0, "8a6a42", 0, 0, 0, "tree"), B(L + 0.2, 0.06, 0.7, 0, 1.25, 0, "5a5652")]
	for i in range(6):
		p.append(C(0.07, 0.52, -L * 0.4 + i * L * 0.16, 0.3 + 0.15 * (i % 3), 0.0, "c8a070", 0, 90, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0, L, 0.6, 1.2]]}


func _b_lift_cabin(_q: Dictionary) -> Dictionary:
	return {"p": [B(1.2, 0.7, 1.0, 0, -1.2, 0, "8a8a86", 0, 0, 0, "metal"), B(0.06, 1.2, 0.06, 0, -0.5, 0, "4a4a4a", 0, 0, 0, "metal"),
			C(0.15, 0.1, 0, 0.0, 0, "3a3a3a", 0, 90, 0, 0, "metal")], "t": "metal", "lod": "mid"}


# ---- equipment (Daniel 31.10.2026: Zelttypen, Biwak-Set, Kocher) ------------------------------------------------------------
func _b_bed_tent1(q: Dictionary) -> Dictionary:
	# Einmannzelt (Tunnel, 2,2 × 0,9 m, 0,8 m hoch)
	var col = _q(q, "col", "3a7a3a")
	var p := [B(0.95, 0.02, 2.3, 0, 0.01, 0, "2a3a2a", 0, 0, 0, "tent")]
	for i in range(3):
		var z := -0.9 + i * 0.9
		var r := 0.42 - 0.08 * absf(i - 1.0)
		p.append(["c", r, 0.9, 0, 0, 0.0, z, col, 0, 0, 90, 22.0])
	p.append(B(0.5, 0.45, 0.04, 0, 0.22, 1.15, "2a2a2a", 0, 0, 0, "tent"))
	return {"p": p, "t": "tent", "lod": "mid", "ob": [["box", 0, 0, 1.0, 2.4, 0.8]]}


func _b_bed_tarp(q: Dictionary) -> Dictionary:
	# Tarp: eine Plane schräg über Stöcken, darunter Isomatte und Schlafsack (offen: Wind und Blicke)
	var col = _q(q, "col", "5a6a3a")
	var p := [B(2.4, 0.02, 2.8, 0, 0.75, 0, col, 28, 0, 0, "tent"), B(0.04, 1.35, 0.04, 0, 0.67, 1.25, "6a6a6a", 0, 0, 0, "metal"),
			ROD(Vector3(0, 1.3, 1.25), Vector3(0, 0, 2.3), 0.01, "c8c8c8")]
	var mat: Dictionary = _b_bed_mat({"col": "2a5ab0"})
	for part in mat["p"]:
		var pp: Array = part.duplicate()
		pp[6] = float(pp[6]) - 0.2
		p.append(pp)
	return {"p": p, "t": "tent", "lod": "mid", "ob": [["box", 0, 0, 2.4, 2.8, 1.3, true]]}


func _b_bed_bivy(q: Dictionary) -> Dictionary:
	# Biwaksack (wasserdicht) über dem Schlafsack, auf der Isomatte - flach am Boden
	var col = _q(q, "col", "e8a020")
	return {"p": [B(0.6, 0.03, 1.95, 0, 0.015, 0, "3a8a3a", 0, 0, 0, "tent"), C(0.3, 1.8, 0, 0.22, 0.05, col, 0.22, 90, 0, 0, 26.0),
			S(0.3, 0.42, 0, 0.25, -0.9, cc(col).darkened(0.15), 28.0), S(0.12, 0.16, 0, 0.3, -1.08, "c8a080", 33.0)],
			"t": "tent", "lod": "small", "ob": [["box", 0, 0, 0.7, 2.1, 0.45, true]]}


func _b_stove(q: Dictionary) -> Dictionary:
	# Kocher mit Topf; beim Kochen heiss (Flamme ≈ 300 °C, Topf ≈ 90 °C) - im Wärmebild sehr hell
	var hot := bool(_q(q, "hot", false))
	return {"p": [C(0.06, 0.12, 0, 0.06, 0, "c0c0c0", 0, 0, 0, 0, 90.0 if hot else "metal"), C(0.09, 0.1, 0, 0.17, 0, "3a3a3a", 0, 0, 0, 0, 90.0 if hot else "metal"),
			C(0.1, 0.02, 0, 0.12, 0, "*ff8030" if hot else "4a4a4a", 0, 0, 0, 0, 250.0 if hot else "metal")], "t": "metal", "lod": "small"}


func _b_tripod(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 1.4))
	var p := []
	for k in range(3):
		var a := TAU * k / 3.0
		p.append(ROD(Vector3(cos(a) * 0.45, 0, sin(a) * 0.45), Vector3(0, h, 0), 0.025, "2a2a2a", "metal"))
	return {"p": p, "t": "metal", "lod": "small"}


func _b_snow_cone(q: Dictionary) -> Dictionary:
	# Lawinenkegel im Frühling: schmutziger Altschnee am Fuss einer Rinne (bleibt bis in den Juni)
	var r := float(_q(q, "r", 9.0))
	return {"p": [S(r, r * 0.5, 0, 0.0, 0, "d8d8d4", "stone"), S(r * 0.6, r * 0.4, r * 0.3, r * 0.1, -r * 0.4, "c8c6c0", "stone"),
			S(r * 0.15, r * 0.15, -r * 0.4, r * 0.15, r * 0.2, "6a6058", "stone")], "t": 0.0, "lod": "far"}
