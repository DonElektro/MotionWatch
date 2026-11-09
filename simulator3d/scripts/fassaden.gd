extends RefCounted
## Facades and roofs of the swisstopo houses (b3d.gd), so they do not all look the same (Wunsch des Besitzers 09.11.2026).
## Only Normal / Hoch: on Lite and during a test run / the Prüfstand b3d.gd builds the plain meshes as before.
## Per house (seed from its position in Swiss coordinates, never from the run, no draw from any RandomNumberGenerator):
##   - kind: from the OpenStreetMap tags of the house (building, building:levels, roof:shape, building:colour, roof:colour,
##     start_date) if there are any, else from size, height and roof (small/low = house, tall/long = apartments, big flat =
##     industrial, in the country with a pitched roof = farm house or chalet, big pitched in the country = barn)
##   - facade colour (Swiss: white, cream, light ochre, pale grey, soft pastels; wood for chalets and barns), storey height,
##     Fensterläden (green / red / brown / grey / none)
##   - roof colour from the aerial picture SWISSIMAGE inside the roof (median, without shadows, very dark / bright pixels and
##     trees), cleaned towards the nearest real roof colour; without picture a plausible colour for the kind
## The details (windows by storey, shutters, plinth, doors, garage doors, balconies, wood, cladding) are drawn by the shader
## b3d_fassade.gdshader from these values; the roofs by b3d_dach.gdshader. Per vertex: COLOR (facade, a = kind),
## CUSTOM0 (u0 of the wall, wall length, ground, eave), CUSTOM1 (storey height, shutters, house seed, wall seed).

enum {HOUSE, APARTMENTS, FARM, CHALET, BARN, COMMERCIAL, INDUSTRIAL, GARAGE, CHURCH}
const KIND_NAMES := ["Haus", "Wohnblock", "Bauernhaus", "Chalet", "Scheune", "Geschäft", "Industrie", "Garage", "Kirche"]

const WALLS := [Color(0.93, 0.92, 0.88), Color(0.95, 0.93, 0.86), Color(0.93, 0.88, 0.76), Color(0.90, 0.82, 0.64),
		Color(0.82, 0.82, 0.80), Color(0.94, 0.89, 0.72), Color(0.92, 0.83, 0.78), Color(0.85, 0.88, 0.80), Color(0.83, 0.86, 0.88)]
const WALL_W := [26, 16, 14, 7, 9, 8, 6, 5, 4]           # white and cream most often
const WOOD := [Color(0.50, 0.33, 0.20), Color(0.42, 0.27, 0.16), Color(0.58, 0.40, 0.24), Color(0.35, 0.23, 0.15)]
const CLAD := [Color(0.80, 0.82, 0.83), Color(0.70, 0.74, 0.78), Color(0.86, 0.86, 0.84), Color(0.62, 0.66, 0.66)]
const ROOFS := {"red": Color(0.60, 0.27, 0.18), "darkred": Color(0.47, 0.21, 0.16), "brown": Color(0.42, 0.30, 0.22),
		"eternit": Color(0.46, 0.47, 0.48), "slate": Color(0.27, 0.28, 0.31), "gravel": Color(0.52, 0.50, 0.46),
		"flat": Color(0.44, 0.44, 0.45), "green": Color(0.36, 0.45, 0.26), "copper": Color(0.36, 0.55, 0.47)}

var geo
var osm_b := []                  # [Rect2, poly, tags] of the OpenStreetMap houses
var cents := PackedVector2Array()
var stats := {"aerial": 0, "palette": 0, "tags": 0, "kinds": {}}


static func enabled(main) -> bool:
	"""Normal / Hoch, no test run, no Prüfstand"""
	if preload("res://scripts/quality.gd").lite():
		return false
	if main == null:
		return true
	if main.get("testrun") != null and main.testrun.running:
		return false
	if main.get("pruef") != null and main.pruef.running:
		return false
	return true


static func hf(a: int, b := 0) -> float:
	"""a number 0 … 1 from two whole numbers (always the same)"""
	var x := (a * 73856093) ^ (b * 19349663) ^ 0x5bd1e995
	x &= 0xffffffff
	x = ((x >> 16) ^ x) * 0x45d9f3b & 0xffffffff
	x = ((x >> 16) ^ x) * 0x45d9f3b & 0xffffffff
	x = (x >> 16) ^ x
	return float(x & 0xffffff) / 16777216.0


static func pick_w(r: float, w: Array) -> int:
	var s := 0.0
	for v in w:
		s += v
	var acc := 0.0
	for i in range(w.size()):
		acc += w[i] / s
		if r < acc:
			return i
	return w.size() - 1


func _init(g, centroids: PackedVector2Array) -> void:
	geo = g
	cents = centroids
	for e in geo.osm:
		if typeof(e) != TYPE_DICTIONARY or typeof(e.get("tags")) != TYPE_DICTIONARY or not e["tags"].has("building"):
			continue
		for poly in geo._polys(e):
			if poly.size() < 3:
				continue
			var r := Rect2(poly[0], Vector2.ZERO)
			for p in poly:
				r = r.expand(p)
			osm_b.append([r, poly, e["tags"]])


func _tags(c: Vector2) -> Dictionary:
	for o in osm_b:
		if (o[0] as Rect2).grow(0.5).has_point(c) and Geometry2D.is_point_in_polygon(c, o[1]):
			return o[2]
	return {}


static func _num(v) -> float:
	var t := str(v).strip_edges().replace(",", ".")
	var i := 0
	while i < t.length() and (t[i].is_valid_int() or t[i] == "."):
		i += 1
	t = t.substr(0, i)
	return float(t) if t != "" and t != "." else 0.0


static func _colour(v) -> Color:
	"""an OSM colour (#rrggbb or a name), Color(0,0,0,0) if none"""
	var t := str(v).strip_edges().to_lower()
	if t == "":
		return Color(0, 0, 0, 0)
	var c := Color.from_string(t, Color(0, 0, 0, 0))
	return c


func style(seed_ll: Vector2, hull: PackedVector2Array, base: float, top: float, eave: float, flat_share: float) -> Dictionary:
	"""the look of one house"""
	var c := Vector2.ZERO
	for p in hull:
		c += p
	c /= hull.size()
	var ch: Vector2 = geo.lv95(seed_ll.x, seed_ll.y)
	var sid := int(round(ch.x)) * 7919 + int(round(ch.y))
	var r := [hf(sid, 1), hf(sid, 2), hf(sid, 3), hf(sid, 4), hf(sid, 5), hf(sid, 6), hf(sid, 7)]
	var area: float = abs(geo._area(hull))
	var hgt := top - base
	var eave_h := maxf(2.2, eave - base)
	# neighbours within 60 m: few = in the country
	var near := 0
	for q in cents:
		if q.distance_squared_to(c) < 3600.0:
			near += 1
	var rural := near < 7
	var tg := _tags(c)
	if not tg.is_empty():
		stats["tags"] += 1
	var b := str(tg.get("building", ""))
	var kind := -1
	match b:
		"house", "detached", "semidetached_house", "bungalow", "villa":
			kind = HOUSE
		"apartments", "terrace", "dormitory", "hotel":
			kind = APARTMENTS
		"residential":
			kind = APARTMENTS if eave_h > 9.0 else HOUSE
		"farm":
			kind = FARM
		"barn", "farm_auxiliary", "stable", "cowshed", "sty":
			kind = BARN
		"cabin", "hut", "chalet":
			kind = CHALET
		"commercial", "retail", "office", "supermarket", "kiosk":
			kind = COMMERCIAL
		"industrial", "warehouse", "manufacture", "hangar", "service":
			kind = INDUSTRIAL
		"garage", "garages", "carport", "shed":
			kind = GARAGE
		"church", "chapel", "cathedral", "public", "school", "civic", "government", "train_station":
			kind = CHURCH if b in ["church", "chapel", "cathedral"] else COMMERCIAL
	var flat := flat_share > 0.6
	if kind < 0:                                          # no tag: size, height, roof
		if area < 45.0 and hgt < 4.5:
			kind = GARAGE
		elif flat and area > 700.0:
			kind = INDUSTRIAL
		elif flat and area > 250.0:
			kind = COMMERCIAL if eave_h < 9.0 else APARTMENTS
		elif eave_h > 9.5 or (area > 380.0 and eave_h > 6.5 and not rural):
			kind = APARTMENTS
		elif rural and not flat and area > 380.0 and eave_h < 7.5:
			kind = BARN if r[0] < 0.55 else FARM
		elif rural and not flat:
			kind = CHALET if r[0] < (0.55 if geo.h0 + base > 900.0 else 0.08) else FARM
		elif flat and area < 160.0:
			kind = GARAGE if hgt < 4.0 else HOUSE
		else:
			kind = HOUSE
	stats["kinds"][KIND_NAMES[kind]] = stats["kinds"].get(KIND_NAMES[kind], 0) + 1
	# storeys
	var lv := _num(tg.get("building:levels", ""))
	var storey: float = {HOUSE: 2.8, APARTMENTS: 2.9, FARM: 2.9, CHALET: 2.6, BARN: 3.4, COMMERCIAL: 3.6, INDUSTRIAL: 4.5, GARAGE: 2.6, CHURCH: 5.0}[kind]
	if lv >= 1.0 and lv < 40.0:
		storey = clampf(eave_h / lv, 2.4, 4.5)
	else:
		storey += (r[1] - 0.5) * 0.3
	# facade
	var wall: Color
	var tcol := _colour(tg.get("building:colour", ""))
	if kind == BARN:
		wall = WOOD[int(r[2] * WOOD.size()) % WOOD.size()]
	elif kind == INDUSTRIAL:
		wall = CLAD[int(r[2] * CLAD.size()) % CLAD.size()]
	elif kind == CHALET:
		wall = WALLS[pick_w(r[2], [10, 4, 6, 3, 2, 1, 0, 0, 0])]     # the ground floor in plaster, wood above (shader)
	elif kind == COMMERCIAL:
		wall = WALLS[pick_w(r[2], [10, 4, 3, 1, 8, 1, 1, 1, 2])]
	elif kind == CHURCH:
		wall = WALLS[pick_w(r[2], [10, 6, 3, 1, 1, 1, 0, 0, 0])]
	else:
		wall = WALLS[pick_w(r[2], WALL_W)]
	if tcol.a > 0.0 and kind != BARN:
		wall = wall.lerp(tcol, 0.7)                          # (tagged colours are often too strong: a bit of plaster stays)
	wall = wall.darkened((r[3] - 0.5) * 0.06)
	# Fensterläden
	var year := _num(str(tg.get("start_date", "")).substr(0, 4))
	var p_shut: float = {HOUSE: 0.62, APARTMENTS: 0.30, FARM: 0.55, CHALET: 0.85}.get(kind, 0.0)
	if year > 1975.0:
		p_shut *= 0.35
	elif year > 0.0 and year < 1930.0:
		p_shut = minf(0.95, p_shut + 0.25)
	var shut := 0
	if r[4] < p_shut:
		shut = 1 + pick_w(r[5], [40, 12 if kind != CHALET else 30, 25, 18])    # green, red, brown, grey
	# roof colour: tag, else the aerial picture, else a palette
	var roof := _colour(tg.get("roof:colour", ""))
	var src := "tag"
	if roof.a <= 0.0:
		roof = _aerial_roof(hull, flat)
		src = "aerial"
	if roof.a <= 0.0:
		roof = _palette_roof(kind, flat, r[6])
		src = "palette"
	if src == "aerial":
		stats["aerial"] += 1
	elif src == "palette":
		stats["palette"] += 1
	roof.a = 1.0
	return {"kind": kind, "wall": wall, "storey": storey, "shut": shut, "seed": r[6], "sid": sid, "eave": eave, "base": base,
			"roof": roof, "flat": flat, "rural": rural}


func _aerial_roof(hull: PackedVector2Array, flat: bool) -> Color:
	"""median colour of the aerial picture inside the roof (shrunk: roofs in SWISSIMAGE lean a bit); alpha 0 = no picture"""
	if geo.photo_near_img == null:
		return Color(0, 0, 0, 0)
	var inner := Geometry2D.offset_polygon(hull, -0.9)
	if inner.is_empty():
		inner = [hull]
	var poly: PackedVector2Array = inner[0]
	var rr := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		rr = rr.expand(p)
	if not geo.rect_near.encloses(rr):
		return Color(0, 0, 0, 0)
	var step := clampf(sqrt(rr.get_area()) / 14.0, 0.5, 2.0)
	var rs := []
	var gs := []
	var bs := []
	var greens := 0
	var y := rr.position.y + step * 0.5
	while y < rr.end.y:
		var x := rr.position.x + step * 0.5
		while x < rr.end.x:
			var p := Vector2(x, y)
			if Geometry2D.is_point_in_polygon(p, poly):
				var c: Color = geo.photo_color(p.x, p.y)
				var l := (c.r + c.g + c.b) / 3.0
				var veg := c.g > c.r * 1.06 and c.g > c.b * 1.04
				if veg:
					greens += 1
				if l > 0.11 and l < 0.86 and not (veg and not flat):      # no shadow, no glare, no tree over a pitched roof
					rs.append(c.r)
					gs.append(c.g)
					bs.append(c.b)
			x += step
		y += step
	if rs.size() < 6:
		return Color(0, 0, 0, 0)
	rs.sort()
	gs.sort()
	bs.sort()
	var m := Color(rs[rs.size() / 2], gs[gs.size() / 2], bs[bs.size() / 2])
	if flat and greens * 2 > rs.size():
		m = m.lerp(ROOFS["green"], 0.3)                     # green roof
	# towards the nearest real roof colour (the aerial picture is hazy and a bit dark), brightness kept from the photo
	var best: Color = ROOFS["eternit"]
	var bd := INF
	for k in ROOFS:
		var q: Color = ROOFS[k]
		var d := Vector3(q.r - m.r, q.g - m.g, q.b - m.b).length_squared()
		if (flat and k in ["red", "darkred", "slate"]) or (not flat and k in ["gravel", "flat", "green"]):
			d *= 2.0
		if d < bd:
			bd = d
			best = q
	var out := m.lerp(best, 0.6).darkened(0.08)          # (a sunny photo: roofs look lighter than they are)
	out.a = 1.0
	return out


func _palette_roof(kind: int, flat: bool, r: float) -> Color:
	if flat:
		return [ROOFS["gravel"], ROOFS["flat"], ROOFS["green"]][pick_w(r, [5, 4, 1])]
	if kind == BARN or kind == FARM:
		return [ROOFS["red"], ROOFS["eternit"], ROOFS["brown"], ROOFS["darkred"]][pick_w(r, [4, 4, 2, 2])]
	if kind == CHALET:
		return [ROOFS["brown"], ROOFS["slate"], ROOFS["eternit"]][pick_w(r, [4, 3, 3])]
	if kind == CHURCH:
		return [ROOFS["red"], ROOFS["copper"], ROOFS["slate"]][pick_w(r, [5, 2, 3])]
	return [ROOFS["red"], ROOFS["darkred"], ROOFS["eternit"], ROOFS["slate"], ROOFS["brown"]][pick_w(r, [8, 4, 4, 2, 1])]


static func wall_planes(tris: Array, sid: int) -> Array:
	"""tris: [a, b, c, n] of the walls of one house -> per triangle [u0, length, wall seed] of the flat wall it lies in"""
	var groups := {}
	var keys := []
	for t in tris:
		var n: Vector3 = t[3]
		var h := Vector2(n.x, n.z)
		if h.length_squared() < 1e-6:
			keys.append(null)
			continue
		h = h.normalized()
		var tg := Vector2(-h.y, h.x)
		var a: Vector3 = t[0]
		var d := a.x * h.x + a.z * h.y
		var key := Vector2i(int(round(atan2(h.y, h.x) / 0.06)), int(round(d / 0.4)))
		keys.append(key)
		if not groups.has(key):
			groups[key] = [INF, -INF]
		for v in [t[0], t[1], t[2]]:
			var u: float = v.x * tg.x + v.z * tg.y
			groups[key][0] = minf(groups[key][0], u)
			groups[key][1] = maxf(groups[key][1], u)
	var out := []
	for i in range(tris.size()):
		var k = keys[i]
		if k == null:
			out.append([0.0, 0.0, 0.0])
			continue
		var g: Array = groups[k]
		out.append([g[0], g[1] - g[0], hf(k.x * 131 + k.y, sid)])
	return out
