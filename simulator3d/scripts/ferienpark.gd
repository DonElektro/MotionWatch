extends RefCounted
## 3D-4.x «Ferienpark am See» (Daniel, 31.10.2026, Variante A): ein grosser terrassierter Campingplatz am Seeufer, rund
## 500 × 500 m. Unten der See mit Strand, Steg und Booten, darüber sechs Terrassen (Restaurant, Laden, Schwimmbad, Spielplatz,
## Festwiese · Zeltwiese, Minigolf, Rezeption mit Schranke und Parkplatz · Wohnmobile · Bungalows · Chalets und Streichelzoo ·
## Pfadi-Lager), oben der Wald mit Weg zum Aussichtspunkt, Hängebrücke und Seilbahn; westlich ein kleines Dorf mit Kirche.
## Gebaut aus der Szenen-Bibliothek (bib_objekte.gd).
##
## MoveEye-Standorte («Standort im Ferienpark», Gruppe Szene): beim Zelt, beim Wohnmobil, beim Bungalow, am Bootssteg, bei der
## Rezeption. Die Welt der anderen Teile des Simulators hat MoveEye immer im Nullpunkt (Besucher kommen vor die Kamera, Tests,
## Spiel); darum wird der ganze Park gedreht und verschoben, so dass der gewählte Standort im Nullpunkt liegt und MoveEye in
## die richtige Richtung schaut (Park-Knoten, Transform W). Park-Koordinaten: x = Osten, z = Süden (bergauf), der See im Norden.
## Gelände: main.ground_fn (Höhe in Weltkoordinaten) - Besucher gehen die Terrassen hinauf, Dinge stehen auf dem Boden.

const Bib = preload("res://scripts/bib_objekte.gd")
const Szenen = preload("res://scripts/szenenplus.gd")
const T = preload("res://scripts/i18n.gd")
const Worlds = preload("res://scripts/worlds.gd")      # 3D-4.x Welten: the old scenes as places in the park

# id -> [name, x, z, Blickrichtung (Grad, 0 = Norden / See, 90 = Osten)]
const SPOTS := {"zelt": ["Beim Zelt (Zeltwiese)", -55.5, -62.5, 0.0],
		"wohnmobil": ["Beim Wohnmobil (Wohnmobil-Terrasse)", 9.0, -20.0, 40.0],
		"bungalow": ["Beim Bungalow (Bungalow-Reihe)", -26.0, 3.0, -150.0],
		"steg": ["Am Bootssteg", 72.0, -156.0, 150.0],
		"rezeption": ["Bei der Rezeption (Schranke)", -180.0, -55.0, -95.0]}
const SPOT_ORDER := ["zelt", "wohnmobil", "bungalow", "steg", "rezeption"]
# the named places [name, x, z] (signs, report, the control «ferienpark»)
const PLACES := [["Badestrand", -60.0, -150.0], ["Bootssteg", 80.0, -175.0], ["Bootshaus", 88.0, -140.0], ["Kiosk am Strand", -60.0, -146.0],
		["Restaurant Seeblick", -30.0, -112.0], ["Laden", 12.0, -108.0], ["Schwimmbad", -95.0, -117.0], ["Spielplatz", -145.0, -115.0],
		["Festwiese mit Bühne", 110.0, -118.0], ["Rezeption", -205.0, -68.0], ["Parkplatz", -238.0, -78.0], ["Zeltwiese", -100.0, -68.0],
		["Minigolf", 62.0, -75.0], ["Sanitär West", -95.0, -70.0], ["Wohnmobil-Terrasse", -40.0, -30.0], ["Sanitär Ost", 64.0, -32.0],
		["Bungalow-Reihe", 0.0, 16.0], ["Chalet-Hang", -100.0, 58.0], ["Streichelzoo", 135.0, 60.0], ["Pfadi-Lager", -115.0, 100.0],
		["Hochsitz", 40.0, 118.0], ["Waldweg", 20.0, 150.0], ["Aussichtspunkt", 110.0, 232.0], ["Hängebrücke", 181.0, 241.0],
		["Seilbahn-Station", 215.0, 252.0], ["Bachbrücke", 172.0, -16.0], ["Dorf mit Kirche", -300.0, 0.0], ["Bäckerei", -278.0, -38.0]]
# terraces: the lane (gravel road) of each level, x from .. to
const LANES := [[-104.0, -200.0, 200.0], [-58.0, -185.0, 160.0], [-14.0, -200.0, 235.0], [28.0, -200.0, 160.0], [72.0, -185.0, 200.0], [104.0, -175.0, 60.0]]
const RAMPS := [-96.0, -52.0, -8.0, 36.0, 80.0]     # where the ground goes up 3.2 m over 8 m
const FOREST_PATH := [Vector2(0, 112), Vector2(30, 140), Vector2(-10, 165), Vector2(40, 190), Vector2(90, 205), Vector2(110, 226)]
const BRIDGE_PATH := [Vector2(110, 236), Vector2(160, 240), Vector2(171, 241), Vector2(191, 242), Vector2(212, 250)]
const NEAR := 320.0
# Erlebniswelt (Daniel 31.10.2026, Vignetten 1–19, Stil «dezent»): reservierte Orte [Nr, id, Name, x, z, frei-Radius].
# Die festen Dinge stehen schon (Baumhütte, Höhle, Mauslöcher, Zwerge, Flaschenpost, Kiste, Angel, versunkenes Boot,
# verlassener Wohnwagen, Baum mit Astloch); die Abläufe (Tiere, Menschen) baut ein späteres Paket an diesen Orten.
const ERLEBNIS := [[1, "katze_maus", "Katze vor den Mauslöchern", -118.0, -104.5, 3.0],
		[2, "eichhorn", "Picknicktisch und Baum mit Astloch", 6.0, -77.0, 5.0],
		[3, "enten", "Entenweg über die Promenade", -165.0, -131.0, 4.0],
		[4, "igel", "Igel an der Bungalow-Hecke", -60.0, 13.0, 3.0],
		[5, "hund_ball", "Hund mit Ball am Strand", -95.0, -152.0, 6.0],
		[6, "fuchs_abfall", "Fuchs am Abfalleimer (Recycling)", -104.0, -63.0, 2.0],
		[7, "moewe", "Möwe auf der Restaurant-Terrasse", -30.0, -121.5, 4.0],
		[8, "zelt_chaos", "Zeltaufbau-Chaos (freier Platz)", -145.0, -69.0, 5.0],
		[9, "grillmeister", "Grillmeister", -125.0, -66.0, 3.0],
		[10, "angler", "Angler am Stegende", 80.0, -197.0, 2.0],
		[11, "schlafwandler", "Schlafwandler (Weg Zeltwiese)", -100.0, -58.0, 0.0],
		[12, "verstecken", "Kinder spielen Verstecken (Hecken T1/T2)", -130.0, -34.0, 0.0],
		[13, "yoga", "Yoga am Strand", -118.0, -155.0, 6.0],
		[14, "baumhuette", "Geheimer Pfad hinter dem Sanitär West zur Baumhütte", -114.0, -84.0, 5.0],
		[15, "hoehle", "Kleine Höhle am Hang (Glühwürmchen)", -42.0, 142.0, 5.0],
		[16, "versunkenes_boot", "Versunkenes Boot (nur vom Steg aus)", 88.0, -196.0, 0.0],
		[17, "alter_wohnwagen", "Verlassener Wohnwagen am Waldrand", 150.0, 116.0, 6.0],
		[18, "zwergendorf", "Gartenzwerg-Dorf in der Hecke", -80.0, 12.0, 3.0],
		[19, "flaschenpost", "Flaschenpost am Strand / Kiste beim Aussichtspunkt", -132.0, -160.0, 2.0]]

var s                       # scenes.gd
var m                       # main.gd
var bib
var park: Node3D
var spot := "zelt"
var place := ""                              # 3D-4.x Welten: the old scene that is the place now ("" = a park spot)
var place_r := 0.0
var place_c := Vector2.ZERO                  # 3D-4.x: the centre of the place (a compact place: MoveEye can stand away from it)
var h0 := 0.0
var inv := Transform3D()
var rng := RandomNumberGenerator.new()
var lite := false
var info := {}


static func _lite() -> bool:
	return Bib.lite()


static func spot_options() -> Array:
	var out := []
	for k in SPOT_ORDER:
		out.append([k, SPOTS[k][0]])
	return out


# =======================================================================================================================
# the ground: height and the shore line (park coordinates)
# =======================================================================================================================
static func zs(px: float) -> float:
	"""the shore line (z of the water's edge)"""
	return -165.0 + 8.0 * sin(px / 55.0) + 5.0 * sin(px / 23.0 + 1.0)


static func creek_x(pz: float) -> float:
	return 175.0 + 6.0 * sin(pz / 30.0)


static var pad: Array = []                   # 3D-4.x Welten: the flat area of the place now [x, z, r, height] ([] = none)


static func H(px: float, pz: float) -> float:
	var h := _H(px, pz)
	if not pad.is_empty():
		var w := 1.0 - smoothstep(float(pad[2]), float(pad[2]) + 14.0, Vector2(px - float(pad[0]), pz - float(pad[1])).length())
		if w > 0.0:
			h = lerpf(h, float(pad[3]), w)
	return h


static func _H(px: float, pz: float) -> float:
	var d := pz - zs(px)
	if d < 0.0:                                        # the lake bed (and the far shore, 1 km away)
		var bed := -0.3 - minf(-d * 0.25, 3.0)
		if pz < -1000.0:
			bed += (-1000.0 - pz) * 0.12
		return bed
	var beach := 0.12 + minf(d, 30.0) * 0.06
	var land := 2.0
	for r in RAMPS:
		land += 3.2 * smoothstep(r, r + 8.0, pz)
	land += 34.0 * smoothstep(108.0, 290.0, pz) + 4.0 * smoothstep(112.0, 140.0, pz)
	var h := lerpf(beach, land, smoothstep(18.0, 34.0, d))
	h += smoothstep(330.0, 470.0, absf(px)) * 45.0 * smoothstep(0.0, 40.0, d)     # hills east and west
	h += 8.0 * exp(-(pow(px - 110.0, 2.0) + pow(pz - 232.0, 2.0)) / 1250.0)     # the knoll of the viewpoint
	h += smoothstep(290.0, 750.0, pz) * 190.0                                   # the mountains behind
	if pz > 112.0:                                                              # the forest is not flat
		h += 0.8 * sin(px * 0.07) * sin(pz * 0.09)
	var cd := absf(px - creek_x(pz))                                            # the creek
	if cd < 9.0 and pz < 300.0:
		var depth := lerpf(1.0, 3.6, smoothstep(110.0, 170.0, pz))
		h -= depth * (1.0 - smoothstep(1.0, 3.0 + depth, cd))
	return h


func P(x: float, z: float, dy := 0.0) -> Vector3:
	"""a point on the ground (park coordinates)"""
	return Vector3(x, H(x, z) + dy, z)


func W(p: Vector3) -> Vector3:
	"""park -> world"""
	return park.transform * p


func WG(x: float, z: float) -> Vector3:
	"""park point on the ground -> world"""
	return park.transform * P(x, z)


func wrot(r: float) -> float:
	return r + park.rotation.y


func gy(x: float, z: float) -> float:
	"""height of the ground in WORLD coordinates (main.ground_fn)"""
	var p := inv * Vector3(x, 0, z)
	return H(p.x, p.z) - h0


# =======================================================================================================================
# building
# =======================================================================================================================
static func build_scene(sc) -> void:
	var fp = new()
	sc.data["ferienpark"] = fp                         # keeps it (and main.ground_fn) alive while the scene is there
	fp._build(sc)


func _build(sc) -> void:
	var t0 := Time.get_ticks_msec()
	s = sc
	m = sc.m
	lite = _lite() or str(m.quality) == "simple"
	rng.seed = 2026
	spot = str(m.get("fp_spot")) if m.get("fp_spot") != null else "zelt"
	if not SPOTS.has(spot):
		spot = "zelt"
	var sp: Array = SPOTS[spot]
	pad = []
	place = Worlds.active(m, "ferienpark")
	if place != "":                                    # 3D-4.x Welten: an old scene is the place (worlds.gd builds it)
		var pl: Array = Worlds.PLACES[place]
		spot = place
		var po: Array = Worlds.pose(m, place)              # 3D-4.x: a compact place: its centre + the chosen spot (kompakt.gd)
		sp = [pl[1], po[0], po[1], po[2]]
		place_r = float(pl[5])
		place_c = Vector2(float(pl[2]), float(pl[3]))
		pad = [float(pl[2]), float(pl[3]), place_r, _H(float(pl[2]), float(pl[3]))]
	h0 = H(sp[1], sp[2])
	park = Node3D.new()
	park.name = "ferienpark"
	var b := Basis(Vector3.UP, deg_to_rad(float(sp[3])))
	park.transform = Transform3D(b, b * -Vector3(sp[1], h0, sp[2]))
	s.root.add_child(park)
	inv = park.transform.affine_inverse()
	m.terrain = true
	m.ground_fn = Callable(self, "gy")
	bib = Bib.new(m, s, park, park.transform)
	if place != "":
		bib.clear = [[place_c, place_r + 10.0]]     # nothing of the park on the place
	_ground()
	_water()
	var t1 := Time.get_ticks_msec()
	_lake_and_beach()
	_terrace0()
	_terrace1()
	_terrace2()
	_terrace3()
	_terrace4()
	_terrace5()
	_ways()
	_forest()
	_village()
	if place == "":
		_own_spot()
	_erlebnis()
	bib.finish()
	_lights_and_fx()
	if place == "":
		_hiding()
	_signs()
	s.meadow(220 if lite else 520, 3.0, 40.0, func(p: Vector3):
		var q := inv * p
		return H(q.x, q.z) < 0.6 or q.z > 112.0 or _on_way(q.x, q.z) or (place != "" and Vector2(q.x, q.z).distance_to(place_c) < place_r))
	_data()
	_erleben()
	if place == "":
		_leben()
	info.merge({"ms": Time.get_ticks_msec() - t0, "ground_ms": t1 - t0, "spot": spot, "lite": lite, "lib": bib.stats.duplicate(),
			"lamps": bib.lamps.size()}, true)
	print("Ferienpark: %s, %d ms (Gelände %d ms), %s" % [spot, info["ms"], info["ground_ms"], str(bib.stats)])


# ---- ground and water ----------------------------------------------------------------------------------------------------
func _ground() -> void:
	var step := 6.4 if lite else 4.0
	var near := _grid(-NEAR, NEAR, step, false)
	var far := _grid(-1900.0, 1900.0, 50.0, true)
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/ferienpark_boden.gdshader")
	tm.set_shader_parameter("photo", _paint())
	tm.set_shader_parameter("rect", Vector4(-NEAR, -NEAR, 2.0 * NEAR, 2.0 * NEAR))
	tm.set_shader_parameter("noise_tex", m.noise_tex)
	var fm := ShaderMaterial.new()
	fm.shader = tm.shader
	fm.set_shader_parameter("photo", _paint_far())
	fm.set_shader_parameter("rect", Vector4(-1900.0, -1900.0, 3800.0, 3800.0))
	fm.set_shader_parameter("noise_tex", m.noise_tex)
	fm.set_shader_parameter("detail", 0.0)
	m.ground_mats = [tm, fm]
	for pair in [[near, tm], [far, fm]]:
		var mi: MeshInstance3D = m.add_mesh(park, pair[0], Vector3.ZERO, pair[1], "x")
		var th: MeshInstance3D = park.get_child(park.get_child_count() - 1)
		th.material_override = m.tmats["ground"]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if pair[0] == far else GeometryInstance3D.SHADOW_CASTING_SETTING_ON


func _grid(lo: float, hi: float, step: float, hole: bool) -> ArrayMesh:
	var n := int(round((hi - lo) / step)) + 1
	var hs := PackedFloat32Array()
	hs.resize(n * n)
	for j in range(n):
		for i in range(n):
			var x := lo + i * step
			var z := lo + j * step
			var h := H(x, z)
			if hole and absf(x) < NEAR - 1.0 and absf(z) < NEAR - 1.0:
				h -= 6.0                                   # the far ground stays below the near one
			hs[j * n + i] = h
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	verts.resize(n * n)
	norms.resize(n * n)
	for j in range(n):
		for i in range(n):
			var hx := hs[j * n + mini(i + 1, n - 1)] - hs[j * n + maxi(i - 1, 0)]
			var hz := hs[mini(j + 1, n - 1) * n + i] - hs[maxi(j - 1, 0) * n + i]
			verts[j * n + i] = Vector3(lo + i * step, hs[j * n + i], lo + j * step)
			norms[j * n + i] = Vector3(-hx, 2.0 * step, -hz).normalized()
	var idx := PackedInt32Array()
	for j in range(n - 1):
		for i in range(n - 1):
			if hole:
				var x0 := lo + i * step
				var z0 := lo + j * step
				if x0 >= -NEAR and x0 + step <= NEAR and z0 >= -NEAR and z0 + step <= NEAR:
					continue
			var a := j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


const C_MEADOW := Color(0.30, 0.42, 0.18)
const C_SAND := Color(0.78, 0.70, 0.52)
const C_MUD := Color(0.36, 0.35, 0.22)
const C_BED := Color(0.30, 0.30, 0.24)
const C_FOREST := Color(0.25, 0.24, 0.14)
const C_RAMP := Color(0.27, 0.37, 0.16)
const C_GRAVEL := Color(0.56, 0.53, 0.46)
const C_ASPHALT := Color(0.33, 0.33, 0.34)
const C_PITCH := Color(0.38, 0.45, 0.22)
const C_PAVING := Color(0.62, 0.6, 0.56)


func _px(x: float) -> int:
	return int(round((x + NEAR) / _mpp()))


func _mpp() -> float:
	return 2.0 if lite else 1.0


func _paint() -> ImageTexture:
	"""the ground map: one pixel per metre (Lite: two) - mostly with fill_rect (fast)"""
	var mpp := _mpp()
	var n := int(2.0 * NEAR / mpp)
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	img.fill(C_MEADOW)
	for i in range(n):                                     # per column: lake bed, sand / mud, ramps, forest
		var x := -NEAR + (i + 0.5) * mpp
		var zsh := zs(x)
		var beach := x > -168.0 and x < 66.0
		img.fill_rect(Rect2i(i, 0, 1, _px(zsh)), C_BED)
		img.fill_rect(Rect2i(i, _px(zsh), 1, maxi(1, int((26.0 if beach else 6.0) / mpp))), C_SAND if beach else C_MUD)
		if beach:
			img.fill_rect(Rect2i(i, _px(zsh + 26.0), 1, maxi(1, int(5.0 / mpp))), C_SAND.lerp(C_MEADOW, 0.5))
		for r in RAMPS:
			img.fill_rect(Rect2i(i, _px(r + 1.0), 1, maxi(1, int(6.0 / mpp))), C_RAMP)
		var fz := 110.0 + 5.0 * sin(x * 0.05) + 3.0 * sin(x * 0.13)
		img.fill_rect(Rect2i(i, _px(fz), 1, n), C_FOREST)
		for k in range(4):                                 # a few lighter, dryer patches
			var zz := -90.0 + k * 50.0 + 20.0 * sin(x * 0.03 + k)
			if int(x * 7.0 + k * 13.0) % 9 == 0:
				img.fill_rect(Rect2i(i, _px(zz), 1, int(6.0 / mpp)), C_MEADOW.lerp(Color(0.5, 0.48, 0.28), 0.45))
	# the creek bed
	var z := -170.0
	while z < 300.0:
		_stamp(img, creek_x(z), z, 4.0, Color(0.32, 0.31, 0.27))
		z += 1.0
	# pitches (worn grass), paved places, paths and roads
	for pr in _paved_rects():
		_rect(img, pr[0], pr[1], pr[2], pr[3], pr[4])
	for ln in LANES:
		_rect(img, ln[1], ln[0] - 2.0, ln[2], ln[0] + 2.0, C_GRAVEL)
	_rect(img, -2.0, zs(0.0) + 22.0, 2.0, 112.0, C_PAVING)         # the main stairs path
	_rect(img, -188.0, -104.0, -182.0, 72.0, C_ASPHALT)            # the drive ramp
	_rect(img, -330.0, -61.0, -185.0, -55.0, C_ASPHALT)            # the access road
	_rect(img, -294.0, -58.0, -288.0, 35.0, C_ASPHALT)             # the village street
	_rect(img, -262.0, -90.0, -214.0, -66.0, C_ASPHALT)            # car park
	for path in [FOREST_PATH, BRIDGE_PATH]:
		_polyline(img, path, 2.2, Color(0.4, 0.34, 0.24))
	var prom := []                                       # the beach promenade
	var x2 := -200.0
	while x2 <= 165.0:
		prom.append(Vector2(x2, zs(x2) + 30.0))
		x2 += 10.0
	_polyline(img, prom, 2.6, C_GRAVEL)
	var tex := ImageTexture.create_from_image(img)
	return tex


func _paved_rects() -> Array:
	"""[x0, z0, x1, z1, colour] of pitches and paved places"""
	var out := []
	for i in range(15):                                   # the tent meadow (terrace 1)
		var x := -165.0 + 10.0 * i
		out.append([x - 4.6, -74.0, x + 4.6, -62.0, C_PITCH])
	for i in range(25):                                   # the motorhome pitches (terrace 2)
		var x := -164.0 + 12.0 * i
		out.append([x - 5.6, -38.0, x + 5.6, -22.0, C_GRAVEL.lerp(C_MEADOW, 0.35)])
	out.append([-48.0, -130.0, -12.0, -100.0, C_PAVING])   # restaurant and terrace
	out.append([2.0, -114.0, 24.0, -102.0, C_PAVING])      # shop
	out.append([-112.0, -128.0, -78.0, -105.0, C_PAVING])  # pool
	out.append([-160.0, -126.0, -128.0, -104.0, Color(0.72, 0.62, 0.44)])   # playground (bark mulch)
	out.append([28.0, -86.0, 96.0, -64.0, Color(0.4, 0.48, 0.24)])          # minigolf
	out.append([-212.0, -76.0, -196.0, -58.0, C_PAVING])   # reception
	out.append([82.0, -132.0, 140.0, -100.0, Color(0.42, 0.44, 0.24)])      # festival meadow (trodden)
	out.append([92.0, 44.0, 200.0, 82.0, Color(0.42, 0.42, 0.22)])          # petting zoo
	out.append([-175.0, 88.0, -60.0, 112.0, Color(0.36, 0.4, 0.2)])         # scout camp
	out.append([-320.0, -45.0, -262.0, 40.0, C_PAVING.lerp(C_MEADOW, 0.5)]) # village
	return out


func _rect(img: Image, x0: float, z0: float, x1: float, z1: float, c: Color) -> void:
	var n := img.get_width()
	var a := Vector2i(clampi(_px(x0), 0, n), clampi(_px(z0), 0, n))
	var b := Vector2i(clampi(_px(x1), 0, n), clampi(_px(z1), 0, n))
	if b.x > a.x and b.y > a.y:
		img.fill_rect(Rect2i(a, b - a), c)


func _stamp(img: Image, x: float, z: float, w: float, c: Color) -> void:
	_rect(img, x - w / 2.0, z - w / 2.0, x + w / 2.0, z + w / 2.0, c)


func _polyline(img: Image, pts: Array, w: float, c: Color) -> void:
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var L := a.distance_to(b)
		var k := 0.0
		while k <= L:
			var p := a.lerp(b, k / L)
			_stamp(img, p.x, p.y, w, c)
			k += 0.8


func _paint_far() -> ImageTexture:
	var n := 152
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for j in range(n):
		for i in range(n):
			var x := -1900.0 + (i + 0.5) * 25.0
			var z := -1900.0 + (j + 0.5) * 25.0
			var h := H(x, z)
			var c := C_MEADOW
			if z < zs(x):
				c = C_BED if z > -1000.0 else C_MEADOW.darkened(0.15)
			elif h > 120.0:
				c = Color(0.42, 0.41, 0.38).lerp(Color(0.85, 0.86, 0.88), smoothstep(170.0, 220.0, h))
			elif h > 25.0 or (absf(x) > 360.0 and int(x / 75.0 + z / 60.0) % 3 != 0):
				c = Color(0.16, 0.24, 0.12)
			elif int(x / 120.0) % 2 == 0:
				c = C_MEADOW.lerp(Color(0.55, 0.5, 0.28), 0.35)
			img.set_pixel(i, j, c)
	return ImageTexture.create_from_image(img)


func _water() -> void:
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.1, 0.26, 0.34)
	wm.metallic = 0.3
	wm.roughness = 0.07
	var lake := PlaneMesh.new()
	lake.size = Vector2(3800.0, 1900.0)
	m.add_mesh(park, lake, Vector3(0, 0.0, -150.0 - 950.0), wm, "pond")
	# the creek: a ribbon down the bed
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var z := 300.0
	var prev_l := Vector3.ZERO
	var prev_r := Vector3.ZERO
	var first := true
	while z > zs(creek_x(z)) - 4.0:
		var cx := creek_x(z)
		var y := H(cx, z) + 0.22
		var l := Vector3(cx - 0.9, y, z)
		var r := Vector3(cx + 0.9, y, z)
		if not first:
			for v in [prev_l, prev_r, l, prev_r, r, l]:
				st.set_normal(Vector3.UP)
				st.add_vertex(v)
		prev_l = l
		prev_r = r
		first = false
		z -= 3.0
	var cm := StandardMaterial3D.new()
	cm.albedo_color = Color(0.16, 0.32, 0.36)
	cm.metallic = 0.2
	cm.roughness = 0.1
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.add_mesh(park, st.commit(), Vector3.ZERO, cm, "pond")
	# people and animals do not walk into the lake
	var x := -NEAR
	while x < NEAR:
		var c := Vector3(x + 8.0, 0, zs(x + 8.0) - 32.0)
		m.add_obstacle_box(W(c), 16.5, 58.0, wrot(0.0))
		m.set_obstacle_height(0.1)
		x += 16.0


# ---- lake, beach, jetty (terrace 0 below) -------------------------------------------------------------------------------------
func _lake_and_beach() -> void:
	bib.add("jetty", Vector3(80.0, 0.0, -159.0), 0.0, {"len": 40.0, "h": 0.75})
	var boats := [["rowboat", 77.3, -168.0, {"col": "d8d8d0"}], ["rowboat", 77.3, -173.0, {"col": "2a6fb0"}], ["pedalboat", 83.0, -170.0, {"col": "f2c22e"}],
			["pedalboat", 83.0, -176.0, {"col": "e85a1a"}], ["rowboat", 77.3, -185.0, {"col": "c0392b"}]]
	for bt in boats:
		bib.add(bt[0], Vector3(bt[1], 0.02, bt[2]), PI / 2.0 + rng.randf_range(-0.08, 0.08), bt[3])
	bib.add("sailboat", Vector3(128.0, 0.0, -222.0), 0.6, {"len": 7.0})
	bib.add("sailboat", Vector3(-40.0, 0.0, -260.0), -0.3, {"len": 8.5})
	for bp in [[128.0, -214.0], [95.0, -205.0], [60.0, -198.0], [-120.0, -195.0], [-90.0, -200.0], [-60.0, -202.0], [-30.0, -201.0]]:
		bib.add("buoy", Vector3(bp[0], 0.0, bp[1]), 0.0, {"col": "e85a1a" if bp[0] > 0 else "f2f2f2"})
	bib.add("boathouse", P(88.0, -140.0), 0.0, {"nodoor": spot == "steg"})
	# the beach: loungers and parasols in rows, lifeguard, showers, the kiosk
	var loung := []
	var paras := []
	var x := -150.0
	while x < 40.0:
		if absf(x + 60.0) > 8.0:
			var z := zs(x) + 13.0
			loung.append([P(x, z), PI + rng.randf_range(-0.2, 0.2)])
			loung.append([P(x + 1.0, z + 0.3), PI + rng.randf_range(-0.2, 0.2)])
			paras.append([P(x + 0.5, z - 1.2), rng.randf() * TAU])
		x += 7.5
	bib.many("lounger", loung, {"col": "2a6fb0"})
	bib.many("parasol", paras, {"col": "d8392b"})
	bib.add("lifeguard", P(-45.0, zs(-45.0) + 7.0), PI)
	for sx in [-100.0, -20.0]:
		bib.add("shower", P(sx, zs(sx) + 24.0), 0.0)
	bib.add("kiosk", P(-60.0, zs(-60.0) + 19.0), PI, {"text": "KIOSK"})
	bib.many("bin", [[P(-55.0, zs(-55.0) + 22.0), 0.0], [P(10.0, zs(10.0) + 26.0), 0.0], [P(-120.0, zs(-120.0) + 26.0), 0.0]], {"col": "2e7d32"})
	# reeds east and west of the beach
	var reeds := []
	x = -300.0
	while x < 300.0:
		if (x < -175.0 or (x > 128.0 and absf(x - 180.0) > 6.0)) and rng.randf() < 0.75:
			reeds.append([Vector3(x, H(x, zs(x) - 1.0) + 0.0, zs(x) - 1.0 + rng.randf_range(-2.0, 2.0)), rng.randf() * TAU])
		x += 4.0
	bib.many("reeds", reeds, {"n": 9 if lite else 14})
	# the beach promenade: benches and lanterns
	var lam := []
	x = -190.0
	while x < 160.0:
		lam.append([P(x, zs(x) + 31.6), 0.0])
		x += 28.0
	bib.many("lamp", lam, {"style": "lantern"})
	for bx in [-130.0, -80.0, 20.0, 60.0]:
		bib.add("bench", P(bx, zs(bx) + 28.4), PI)


# ---- terrace 0: restaurant, shop, pool, playground, festival meadow ---------------------------------------------------------
func _terrace0() -> void:
	bib.add("restaurant", P(-30.0, -110.0), PI, {"text": "Restaurant Seeblick"})
	_terrace_deck(Vector3(-30.0, 0, -121.5), 14.0, 7.0, 6)
	bib.add("shop", P(12.0, -110.0), 0.0, {"text": "LADEN"})
	bib.add("bike_rack", P(20.0, -104.5), 0.0, {"n": 5})
	bib.add("pool", P(-95.0, -117.0), 0.0)
	var pf := [[Vector3(-111.0, 0, -126.5), Vector3(-79.0, 0, -126.5)], [Vector3(-79.0, 0, -126.5), Vector3(-79.0, 0, -106.0)],
			[Vector3(-111.0, 0, -106.0), Vector3(-111.0, 0, -126.5)], [Vector3(-111.0, 0, -106.0), Vector3(-79.0, 0, -106.0)]]
	for i in range(pf.size()):
		bib.line("fence", pf[i][0], pf[i][1], 2.5, {"style": "pool", "h": 1.6, "ground": Callable(self, "H")}, [[16.0, 1.5]] if i == 3 else [])
	bib.many("lounger", [[P(-105.0, -108.5), PI / 2.0], [P(-102.0, -108.5), PI / 2.0], [P(-88.0, -108.5), PI / 2.0], [P(-85.0, -108.5), PI / 2.0]], {"col": "f2f2f2"})
	bib.add("shed", P(-115.5, -110.0), PI / 2.0, {"w": 3.0, "d": 2.5, "col": "6a8aa0"})
	# playground
	bib.add("swing", P(-150.0, -121.0), 0.0, {"seats": 3})
	bib.add("slide", P(-139.0, -122.0), PI)
	bib.add("sandpit", P(-147.0, -111.0), 0.0)
	bib.add("climbing", P(-134.0, -112.0), 0.3)
	bib.add("seesaw", P(-156.0, -109.0), 0.5)
	for bx in [[-152.0, -105.5, PI], [-136.0, -105.5, PI]]:
		bib.add("bench", P(bx[0], bx[1]), bx[2])
	# festival meadow: the stage faces west, barriers, a food truck, picnic tables
	bib.add("stage", P(132.0, -116.0), -PI / 2.0, {"col": "2a3a7a"})
	bib.line("crowd_barrier", Vector3(124.0, 0, -126.0), Vector3(124.0, 0, -106.0), 2.5, {"ground": Callable(self, "H")}, [[10.0, 1.4]])
	bib.add("food_truck", P(96.0, -106.0), PI * 0.5, {"text": "Snacks"})
	for i in range(4):
		bib.add("picnic_table", P(98.0 + (i % 2) * 6.0, -122.0 + (i / 2) * 6.0), 0.1 * i)
	bib.add("bin", P(92.0, -110.0), 0.0, {"style": "recycle"})


func _terrace_deck(c: Vector3, w: float, d: float, tables: int) -> void:
	"""the restaurant terrace: a wooden deck over the slope with tables, chairs and parasols"""
	var y := H(c.x, c.z + d * 0.5)
	bib.add("wall", Vector3(c.x, H(c.x, c.z - d * 0.5), c.z - d * 0.5), 0.0, {"len": w, "h": maxf(0.5, y - H(c.x, c.z - d * 0.5) + 0.3)})
	bib.parts_of("picnic_table", Transform3D(), {})                      # (keeps the kind cache warm)
	var deck := ["b", w, 0.25, d, c.x, y + 0.12, c.z, "8a6a48", 0, 0, 0, "tree"]
	bib._part(deck, Transform3D.IDENTITY, "tree", "big", bib._cell_key(c))
	for i in range(tables):
		var tx := c.x - w / 2.0 + w * (i % 3 + 0.5) / 3.0
		var tz := c.z - d / 4.0 + (i / 3) * d / 2.0
		var tp := Vector3(tx, y + 0.25, tz)
		bib.add("parasol", tp, 0.0, {"col": "f2f2f2" if i % 2 == 0 else "2e7d32", "r": 1.4})
		var parts := [Bib.C(0.45, 0.04, 0, 0.75, 0, "f2f2f2"), Bib.C(0.04, 0.72, 0, 0.37, 0, "4a4a4a")]
		for k in range(4):
			var a := TAU * k / 4.0 + 0.4
			parts.append(Bib.B(0.42, 0.05, 0.42, cos(a) * 0.75, 0.45, sin(a) * 0.75, "3a3a3a"))
			parts.append(Bib.B(0.42, 0.4, 0.05, cos(a) * 0.95, 0.68, sin(a) * 0.95, "3a3a3a", 0, rad_to_deg(-a) + 90.0, 0))
		for pt in parts:
			bib._part(pt, Transform3D(Basis(), tp), "tree", "small", bib._cell_key(tp))
	m.add_obstacle_box(W(Vector3(c.x, 0, c.z)), w, d, wrot(0.0), true)
	m.set_obstacle_height(1.0)
	bib.line("fence", Vector3(c.x - w / 2.0, y + 0.25, c.z - d / 2.0), Vector3(c.x + w / 2.0, y + 0.25, c.z - d / 2.0), 2.0, {"style": "wood", "h": 1.0})


# ---- terrace 1: reception, car park, tent meadow, sanitary, minigolf ----------------------------------------------------------
func _terrace1() -> void:
	bib.add("reception", P(-205.0, -68.0), PI / 2.0, {"text": "REZEPTION", "nodoor": spot == "rezeption"})
	bib.add("barrier", P(-189.0, -61.0), PI / 2.0, {"len": 5.0})
	bib.add("barrier", P(-189.0, -55.0), -PI / 2.0, {"len": 5.0, "open": true})
	bib.add("info_board", P(-195.0, -52.5), PI, {"text": "Ferienpark am See"})
	bib.many("bench", [[P(-199.0, -74.0), PI / 2.0]], {})
	# car park: lines and cars (some places free)
	bib.add("parking_lines", P(-238.0, -84.0), 0.0, {"n": 16, "spacing": 2.7, "len": 5.0})
	bib.add("parking_lines", P(-238.0, -70.0), PI, {"n": 16, "spacing": 2.7, "len": 5.0})
	var cols := ["2b5fa8", "d8d8d8", "1a1a1a", "a01818", "6a6a6a", "2e6a3a", "e8e8e8", "8a5a32"]
	for row in [[-84.0, 0.0], [-70.0, PI]]:
		for i in range(16):
			if rng.randf() < 0.35:
				continue
			var x := -238.0 - 8 * 2.7 + 2.7 * (i + 0.5)
			bib.add("car", P(x, row[0]), row[1] + rng.randf_range(-0.04, 0.04),
					{"col": cols[rng.randi() % cols.size()], "style": ["sedan", "sedan", "suv", "van"][rng.randi() % 4]})
	bib.many("lamp", [[P(-250.0, -77.0), 0.0], [P(-226.0, -77.0), 0.0], [P(-200.0, -58.0), 0.0], [P(-300.0, -55.0), 0.0], [P(-260.0, -55.0), 0.0]], {"style": "street"})
	# the tent meadow: 15 pitches of 10 m, hedges between, numbers, power posts
	var styles := ["dome", "dome", "tunnel", "ridge", "family", "tunnel"]
	var tcols := ["d8692a", "2a6fb0", "2e7d32", "c0392b", "e8b21e", "6a4a8a", "3a8a8a", "8a8a3a"]
	var hedges := []
	var posts := []
	var power := []
	for i in range(15):
		var x := -165.0 + 10.0 * i
		hedges.append([P(x - 5.0, -69.0), PI / 2.0])
		hedges.append([P(x - 5.0, -72.5), PI / 2.0])
		if absf(x + 95.0) < 9.0:
			continue                                   # the sanitary building
		posts.append([P(x - 3.5, -62.3), 0.0])
		if i % 2 == 0:
			power.append([P(x - 4.6, -62.6), 0.0])
		if x == -55.0 and spot == "zelt":
			continue                                   # your pitch (_own_spot)
		if rng.randf() < 0.15 or x == -145.0:
			continue                                   # a free pitch (-145: the tent chaos of the Erlebniswelt)
		var tp := P(x + rng.randf_range(-1.5, 1.5), -69.5 + rng.randf_range(-1.0, 1.0))
		bib.add("tent", tp, rng.randf_range(-0.4, 0.4) + (PI if rng.randf() < 0.3 else 0.0), {"style": styles[rng.randi() % styles.size()], "col": tcols[rng.randi() % tcols.size()]})
		var r := rng.randf()
		if r < 0.45:
			bib.add("car", P(x + 3.0, -66.0), PI / 2.0 + rng.randf_range(-0.1, 0.1), {"col": cols[rng.randi() % cols.size()], "style": "sedan" if r < 0.3 else "van"})
		if rng.randf() < 0.7:
			bib.add("picnic_table", P(x - 2.0, -64.8), rng.randf_range(-0.3, 0.3), {"col": ["8a6a48", "c8c8c8", "2a5a8a"][rng.randi() % 3]})
		if rng.randf() < 0.3:
			bib.add("bbq", P(x + 0.5, -63.6), 0.0, {"hot": 70.0 if rng.randf() < 0.4 else 15.0})
	bib.many("hedge", hedges, {"len": 3.4, "h": 1.5})
	bib.many("pitch_post", posts, {})
	bib.many("power_post", power, {})
	bib.add("sanitary", P(-95.0, -70.0), 0.0, {"text": "WC · Dusche"})
	bib.add("water_tap", P(-86.0, -63.0), 0.0)
	bib.add("bin", P(-104.0, -63.0), 0.0, {"style": "recycle"})
	# minigolf: 18 tracks in two rows, a low fence and a hut with the clubs
	var styles2 := ["straight", "bump", "loop", "windmill", "gate", "bridge"]
	for i in range(18):
		var row := i / 9
		var x := 32.0 + 7.0 * (i % 9)
		bib.add("minigolf", P(x, -80.0 + row * 10.0), 0.0 if row == 0 else PI, {"len": 8.0, "style": styles2[i % styles2.size()], "nr": str(i + 1)})
	bib.add("kiosk", P(98.0, -66.0), -PI / 2.0, {"text": "MINIGOLF", "col": "2e7d32"})
	bib.line("fence", Vector3(27.0, 0, -86.0), Vector3(95.0, 0, -86.0), 2.5, {"style": "picket", "h": 0.8, "ground": Callable(self, "H")})


# ---- terrace 2: motorhomes and caravans -------------------------------------------------------------------------------------
func _terrace2() -> void:
	var hedges := []
	var power := []
	var cols := ["f0f0ee", "e8e4d8", "dcdcdc", "f2f2f2"]
	var stripes := ["8a8f96", "2a6fb0", "c0392b", "3a7a3a", "e8b21e"]
	for i in range(25):
		var x := -164.0 + 12.0 * i
		hedges.append([P(x - 6.0, -32.0), PI / 2.0])
		hedges.append([P(x - 6.0, -36.0), PI / 2.0])
		if absf(x - 64.0) < 10.0:
			continue
		if absf(x - 16.0) < 1.0:
			continue                                     # the own motorhome (_own_spot, always there)
		power.append([P(x - 5.3, -21.3), 0.0])
		if rng.randf() < 0.12:
			continue
		var r := rng.randf()
		var rot := rng.randf_range(-0.05, 0.05) + (PI if rng.randf() < 0.25 else 0.0)
		if r < 0.55:
			bib.add("motorhome", P(x + 0.5, -30.0), rot, {"len": rng.randf_range(6.4, 7.6), "style": "alcove" if rng.randf() < 0.6 else "integrated",
					"col": cols[rng.randi() % cols.size()], "stripe": stripes[rng.randi() % stripes.size()]})
		else:
			bib.add("caravan", P(x - 0.5, -31.0), rot, {"len": rng.randf_range(5.0, 6.6), "stripe": stripes[rng.randi() % stripes.size()],
					"awning": rng.randf() < 0.6, "awning_col": ["c86a2a", "2a6fb0", "3a7a3a"][rng.randi() % 3]})
			bib.add("car", P(x + 1.0, -25.0), rng.randf_range(-0.1, 0.1), {"col": ["2b5fa8", "1a1a1a", "a01818", "d8d8d8"][rng.randi() % 4], "style": "suv"})
		if rng.randf() < 0.6:
			bib.add("picnic_table", P(x - 2.5, -24.5), rng.randf_range(-0.2, 0.2), {"len": 1.6, "col": "c8c8c8"})
	bib.many("hedge", hedges, {"len": 3.6, "h": 1.7, "col": "2a5220"})
	bib.many("power_post", power, {})
	bib.add("sanitary", P(64.0, -32.0), 0.0, {"w": 16.0, "text": "WC · Dusche · Abwasser"})
	bib.add("bin", P(56.0, -22.0), 0.0, {"style": "recycle"})
	bib.add("water_tap", P(73.0, -22.0), 0.0)


# ---- terrace 3: bungalows ----------------------------------------------------------------------------------------------------
func _terrace3() -> void:
	var cols := ["b98a5a", "a8784a", "c9a27a", "8a6a4a", "d8c09a"]
	var roofs := ["5a3426", "3a3a3e", "6a2a1e"]
	var lam := []
	for i in range(16):
		var x := -150.0 + 20.0 * i
		if absf(x - 170.0) < 12.0:
			continue
		var own := absf(x + 30.0) < 1.0 and spot == "bungalow"
		bib.add("bungalow", P(x, 16.0), PI, {"w": 6.0, "d": 8.0, "col": cols[i % cols.size()], "roof": roofs[i % roofs.size()],
				"chimney": i % 4 == 1, "nodoor": own})
		bib.add("hedge", P(x + 10.0, 14.0), PI / 2.0, {"len": 6.0, "h": 1.3})
		if i % 2 == 0:
			lam.append([P(x + 5.0, 24.5), 0.0])
		if rng.randf() < 0.45 and not own:
			bib.add("car", P(x + 4.5, 23.0), PI / 2.0, {"col": ["2b5fa8", "1a1a1a", "d8d8d8", "8a5a32"][rng.randi() % 4]})
	bib.many("lamp", lam, {"style": "lantern"})


# ---- terrace 4: chalets, petting zoo, orchard ---------------------------------------------------------------------------------
func _terrace4() -> void:
	for i in range(6):
		var x := -160.0 + 24.0 * i
		bib.add("chalet", P(x, 58.0), PI, {"col": ["7a4b2a", "6a3e22", "8a5a32"][i % 3]})
		bib.add("car", P(x + 7.0, 66.0), PI / 2.0, {"col": ["2b5fa8", "1a1a1a", "d8d8d8"][i % 3], "style": "suv"})
	# petting zoo: barn, stable, coop, a paddock with cows, goats and sheep, chickens, hay, tractor
	bib.add("barn", P(170.0, 60.0), -PI / 2.0, {"w": 16.0, "d": 11.0})
	bib.add("stable", P(122.0, 50.0), PI, {"w": 14.0})
	bib.add("coop", P(140.0, 71.0), 0.2)
	var pad := [Vector3(96, 0, 46), Vector3(150, 0, 46), Vector3(150, 0, 64), Vector3(96, 0, 64)]
	for i in range(4):
		bib.line("fence", pad[i], pad[(i + 1) % 4], 2.5, {"style": "wood", "h": 1.2, "ground": Callable(self, "H")}, [[4.0, 1.4]] if i == 3 else [])
	for a in [["cow", 110.0, 55.0, 0.4], ["cow", 118.0, 58.0, 2.2], ["goat", 130.0, 52.0, 1.0], ["goat", 132.0, 55.0, 3.0], ["goat", 128.0, 59.0, 5.0],
			["sheep", 140.0, 57.0, 0.7], ["sheep", 142.0, 60.0, 2.0], ["chicken", 138.0, 74.0, 0.3], ["chicken", 141.0, 75.5, 2.0],
			["chicken", 143.0, 73.0, 4.0], ["chicken", 136.5, 76.0, 1.0]]:
		bib.add(a[0], P(a[1], a[2]), a[3], {"col": "8a5a3a"} if a[0] == "cow" and a[1] > 115.0 else {})
	bib.many("haybale", [[P(182.0, 72.0), 0.0], [P(184.0, 75.0), 0.3], [P(181.0, 77.5), 1.2], [P(157.0, 48.0), 0.0]], {"wrapped": false})
	bib.many("haybale", [[P(187.0, 70.0), PI / 2.0], [P(189.0, 73.0), PI / 2.0]], {"wrapped": true})
	bib.add("tractor", P(178.0, 50.0), 2.6, {"warm": 48.0})
	var trees := []
	for i in range(12):
		trees.append([P(62.0 + (i % 4) * 7.0, 48.0 + (i / 4) * 7.0), rng.randf() * TAU, rng.randf_range(0.85, 1.1)])
	bib.many("orchard_tree", trees, {"fruit": "c0392b"})
	# fields outside the park in the east
	for fd in [[300.0, -60.0, "wheat"], [300.0, -10.0, "corn"], [300.0, 40.0, "sunflower"], [255.0, 95.0, "potato"]]:
		bib.add("field", P(fd[0], fd[1]), 0.0, {"w": 40.0, "d": 36.0, "crop": fd[2]})


# ---- terrace 5: scout camp, raised hide -------------------------------------------------------------------------------------
func _terrace5() -> void:
	bib.add("sarasani", P(-122.0, 100.0), 0.0, {"r": 6.0})
	bib.add("yurt", P(-96.0, 99.0), 0.4, {"smoke": true})
	bib.add("campfire", P(-142.0, 96.0), 0.0, {"fire": true})
	bib.add("flagpole", P(-152.0, 106.0), 0.0, {"col": "c8102e"})
	bib.add("totem", P(-106.0, 108.5), 0.0)
	bib.add("latrine", P(-66.0, 108.0), PI)
	bib.add("latrine", P(-63.5, 108.0), PI)
	for i in range(6):
		bib.add("tent", P(-170.0 + i * 4.5, 90.5), 0.0, {"style": "ridge", "col": ["4a5a2a", "6a6a4a", "2a3a2a"][i % 3]})
	for i in range(3):
		bib.add("picnic_table", P(-82.0 + i * 3.0, 93.0), 0.0, {"len": 2.2})
	bib.add("hochsitz", P(40.0, 118.0), PI, {"h": 4.0})
	bib.add("info_board", P(6.0, 110.0), PI, {"text": "Waldweg · Aussicht"})


# ---- ways: stairs, drive ramp, lanes, lamps, retaining walls, bridges -------------------------------------------------------
func _ways() -> void:
	var lam := []
	for ln in LANES:
		var x: float = ln[1]
		while x <= ln[2]:
			if absf(x - creek_x(ln[0])) > 6.0:
				lam.append([P(x, ln[0] - 2.6), 0.0])
			x += 26.0
	bib.many("lamp", lam, {"style": "lantern"})
	# the main stairs at x = 0 (up to the south) and bollard lights
	var bol := []
	for r in RAMPS:
		bib.add("stairs", P(0.0, r), PI, {"n": 18, "w": 2.6, "rise": 3.2 / 18.0, "run": 8.0 / 18.0})
		bol.append([P(-1.8, r - 1.0), 0.0])
		bol.append([P(1.8, r + 9.0), 0.0])
	bib.many("lamp", bol, {"style": "path"})
	# retaining walls at the top of every ramp, with gaps for the stairs, the drive ramp and the creek
	for r in RAMPS:
		var z: float = r + 8.3
		var segs := [[-195.0, -190.5], [-180.0, -3.5], [3.5, creek_x(z) - 5.0], [creek_x(z) + 5.0, 235.0]]
		for sg in segs:
			var a := Vector3(sg[0], 0, z)
			var b := Vector3(sg[1], 0, z)
			bib.line("wall", a, b, 3.0, {"h": 0.9, "sink": 0.3, "ground": Callable(self, "H")}, _wall_gaps(sg[1] - sg[0]))
	# footbridges where the lanes and the promenade cross the creek
	for z in [-104.0, -14.0, 72.0]:
		var cx := creek_x(z)
		bib.add("footbridge", Vector3(cx, H(cx + 4.0, z) - 0.1, z), PI / 2.0, {"len": 8.0, "w": 3.0})
	var pz := zs(creek_x(-140.0)) + 30.0
	bib.add("footbridge", Vector3(creek_x(pz), H(creek_x(pz) + 4.0, pz) - 0.1, pz), PI / 2.0, {"len": 8.0, "w": 2.2})
	# benches along the lanes with the view
	for ln in LANES:
		for bx in [-120.0, -10.0, 110.0]:
			if bx > ln[1] and bx < ln[2]:
				bib.add("bench", P(bx, ln[0] - 4.0), PI)
	for bp in [[-60.0, -100.0], [30.0, -60.0], [-150.0, -14.0], [100.0, 28.0], [-30.0, 72.0], [50.0, 104.0]]:
		bib.add("bin", P(bp[0], bp[1] - 2.8), 0.0, {"col": "2e7d32"})


func _wall_gaps(L: float) -> Array:
	var out := []
	var k := 38.0
	while k < L - 5.0:
		out.append([k, 1.4])
		k += 40.0
	return out


# ---- forest, viewpoint, rope bridge, cable car --------------------------------------------------------------------------
func _forest() -> void:
	var dens := 0.4 if lite else 1.0
	var con := []
	var broad := []
	var real := []
	var z := 114.0
	while z < 320.0:
		var x := -320.0
		while x < 320.0:
			var px := x + rng.randf_range(-3.5, 3.5)
			var pz := z + rng.randf_range(-3.5, 3.5)
			x += 9.5
			if rng.randf() > dens or _on_way(px, pz, 4.0) or absf(px - creek_x(pz)) < 3.0:
				continue
			if _busy(px, pz) or pz < 116.0 + 5.0 * sin(px * 0.05) or Vector2(px - 110.0, pz - 232.0).length() < 14.0 or Vector2(px - 215.0, pz - 252.0).length() < 12.0:
				continue
			var e := [P(px, pz, -0.15), rng.randf() * TAU, rng.randf_range(0.8, 1.35)]
			if W(e[0]).length() < 42.0:
				real.append(e)
			elif rng.randf() < 0.62:
				con.append(e)
			else:
				broad.append(e)
		z += 9.5
	# scattered trees in the park: along the lake, between terraces, around the village
	for i in range(140 if not lite else 60):
		var px := rng.randf_range(-310.0, 310.0)
		var pz := rng.randf_range(-150.0, 112.0)
		if H(px, pz) < 0.8 or _on_way(px, pz, 5.0) or _busy(px, pz):
			continue
		var e := [P(px, pz, -0.1), rng.randf() * TAU, rng.randf_range(0.8, 1.3)]
		if W(e[0]).length() < 42.0:
			real.append(e)
		else:
			broad.append(e)
	bib.many("conifer", con, {})
	bib.many("tree", broad, {"col": "3a6a2a"})
	for e in real:                                          # near MoveEye: real trees (wind, the game camera keeps out)
		s.tree(s.root, W(e[0]), e[2], -1)
	info["trees"] = con.size() + broad.size() + real.size()
	# the forest path: signposts, benches, a raised hide
	bib.add("signpost", P(2.0, 114.0), PI, {"arms": ["Aussicht 25 Min", "Seilbahn 35 Min"]})
	bib.add("signpost", P(92.0, 207.0), PI * 0.8, {"arms": ["Aussicht", "Camping"]})
	bib.add("bench", P(-8.0, 167.0), PI * 0.5)
	bib.add("viewpoint", P(110.0, 232.0), PI, {"w": 6.0, "d": 4.5, "h": 2.5})
	bib.add("info_board", P(104.0, 236.0), PI, {"text": "Aussichtspunkt 512 m ü. M."})
	bib.add("hochsitz", P(-60.0, 175.0), PI * 0.9, {"h": 4.5})
	# the rope bridge over the creek ravine and the cable car station
	var bz := 241.5
	var cx := creek_x(bz)
	bib.add("rope_bridge", Vector3(cx, H(cx - 10.0, bz) - 0.2, bz), PI / 2.0, {"len": 20.0, "sag": 1.2})
	bib.add("cable_station", P(215.0, 252.0), PI, {"up": 60.0, "rise": 40.0})


func _on_way(x: float, z: float, w := 2.5) -> bool:
	for path in [FOREST_PATH, BRIDGE_PATH]:
		for i in range(path.size() - 1):
			var a: Vector2 = path[i]
			var b: Vector2 = path[i + 1]
			var q := Geometry2D.get_closest_point_to_segment(Vector2(x, z), a, b)
			if q.distance_to(Vector2(x, z)) < w:
				return true
	for ln in LANES:
		if absf(z - float(ln[0])) < w and x > float(ln[1]) - 2.0 and x < float(ln[2]) + 2.0:
			return true
	return absf(x) < w and z > -140.0 and z < 112.0


func _busy(x: float, z: float) -> bool:
	"""where the buildings, pitches and paddocks are (no random tree there)"""
	for pr in _paved_rects():
		if x > pr[0] - 3.0 and x < pr[2] + 3.0 and z > pr[1] - 3.0 and z < pr[3] + 3.0:
			return true
	for e in ERLEBNIS:
		if Vector2(x - float(e[3]), z - float(e[4])).length() < float(e[5]) + 2.0:
			return true
	for zz in [16.0, 58.0]:
		if absf(z - zz) < 9.0 and x > -175.0 and x < 165.0:
			return true
	return false


# ---- the village in the west ---------------------------------------------------------------------------------------------
func _village() -> void:
	bib.add("church", P(-305.0, 12.0), PI / 2.0, {"len": 20.0, "w": 10.0})
	bib.add("bakery", P(-278.0, -38.0), PI / 2.0, {"w": 9.0, "d": 8.0, "text": "Bäckerei"})
	bib.add("house", P(-305.0, -30.0), PI / 2.0 + 0.05, {"w": 10.0, "d": 9.0, "floors": 3, "col": "e8dcc4", "smoke": true})
	bib.add("house", P(-278.0, 0.0), -PI / 2.0, {"w": 8.0, "d": 8.0, "floors": 2, "col": "d8c8a8"})
	bib.add("house", P(-276.0, 25.0), -PI / 2.0, {"w": 9.0, "d": 9.0, "floors": 2, "col": "f0e8d8", "roof": "4a4a4e"})
	bib.add("house", P(-312.0, 34.0), PI / 2.0, {"w": 8.0, "d": 7.0, "floors": 2, "col": "c8b898"})
	bib.add("fountain", P(-291.0, -15.0), 0.0, {"r": 1.8})
	bib.many("lamp", [[P(-286.0, -40.0), 0.0], [P(-286.0, -10.0), 0.0], [P(-286.0, 20.0), 0.0]], {"style": "lantern"})
	bib.add("bus_stop" if bib.KINDS.has("bus_stop") else "bench", P(-286.0, -52.0), 0.0)
	bib.add("signpost", P(-292.0, -53.0), 0.0, {"arms": ["Dorf", "Ferienpark"]})


# ---- your place (depends on the chosen position) -------------------------------------------------------------------------
func _own_spot() -> void:
	match spot:
		"zelt":
			var tp := P(-55.5, -70.0)
			Szenen._tent(s, W(tp), wrot(0.1), Color(0.9, 0.5, 0.15), true)
			s.caravan(WG(-50.5, -69.5), wrot(PI / 2.0 + PI))            # your small caravan (door sensor)
			s.bike(WG(-60.0, -66.5), wrot(PI / 2.0 + 0.2))
			Szenen._own_things(s, WG(-59.0, -67.5), WG(-52.0, -64.0))
			s.data["platz"] = [WG(-55.0, -68.0), 7.0]
			s.data["nachbarn"] = [["koch", WG(-45.0, -65.0)], ["sitz", WG(-66.0, -65.0)], ["kinder", WG(-75.0, -80.0)], ["sitz", WG(-35.0, -66.0)]]
		"wohnmobil":
			var d: Dictionary = bib.add("motorhome", P(17.0, -30.0), 0.0, {"len": 7.2, "style": "alcove", "col": "f2f2f2", "stripe": "2a6fb0", "nodoor": true})
			_own_door(d, P(17.0, -30.0), 0.0)
			m.obj["pir"] = WG(17.0, -26.0)
			s.bike(WG(11.0, -25.0), wrot(0.3))
			Szenen._own_things(s, WG(21.0, -25.0), WG(25.0, -24.0))
			s.data["platz"] = [WG(16.0, -29.0), 7.0]
			s.data["nachbarn"] = [["koch", WG(28.0, -24.5)], ["sitz", WG(3.0, -24.5)], ["sitz", WG(-9.0, -24.0)], ["kinder", WG(40.0, -40.0)]]
		"bungalow":
			var x := -30.0
			_own_door({"door": [6.0 * 0.22, 0.35, 4.0 + 0.03, 0.95, 2.0, "6b4a32"]}, P(x, 16.0), PI)
			m.obj["pir"] = WG(x - 1.0, 9.0)
			s.bike(WG(x + 4.0, 9.5), wrot(0.2))
			Szenen._own_things(s, WG(x - 3.5, 8.0), WG(x + 2.5, 7.5))
			s.data["platz"] = [WG(x, 9.0), 7.0]
			s.data["nachbarn"] = [["sitz", WG(-50.0, 9.5)], ["koch", WG(-10.0, 8.5)], ["kinder", WG(-22.0, 2.0)]]
		"steg":
			_own_door({"door": [3.0 + 0.03, 0.0, 8.0 * 0.2, 0.9, 2.0, "4a3220", 90.0]}, P(88.0, -140.0), 0.0)
			bib.add("rowboat", P(78.0, -150.0), 0.7, {"col": "2e7d32"})
			m.obj["pir"] = WG(78.0, -150.0)
			s.bike(WG(80.0, -145.0), wrot(1.2))
			s.data["platz"] = [WG(80.0, -148.0), 7.0]
			s.data["nachbarn"] = [["kinder", WG(58.0, -150.0)], ["sitz", WG(60.0, -142.0)]]
		"rezeption":
			_own_door({"door": [12.0 * 0.3, 0.0, 4.0 + 0.04, 1.6, 2.2, "3f5b6e"]}, P(-205.0, -68.0), PI / 2.0)
			m.obj["pir"] = WG(-189.0, -58.0)
			s.bike(WG(-196.0, -50.0), wrot(0.0))
			s.data["platz"] = [WG(-192.0, -58.0), 8.0]
			s.data["nachbarn"] = [["sitz", WG(-199.0, -73.0)]]
	if spot != "wohnmobil":                                    # the own motorhome stands there anyway
		bib.add("motorhome", P(17.0, -30.0), 0.0, {"len": 7.2, "style": "alcove", "col": "f2f2f2", "stripe": "2a6fb0"})
	if spot != "zelt":                                         # the pitch at -55 of the tent meadow
		bib.add("tent", P(-55.5, -70.0), 0.1, {"style": "dome", "col": "d8692a"})
		bib.add("caravan", P(-50.5, -69.5), PI * 1.5, {"len": 5.6})


func _own_door(d: Dictionary, base: Vector3, rot: float) -> void:
	"""the door of your building as its own node (the door sensor opens it), its light and a window that lights up"""
	var dr: Array = d["door"]
	var w := float(dr[3])
	var h := float(dr[4])
	var extra := deg_to_rad(float(dr[6])) if dr.size() > 6 else 0.0
	var host := Node3D.new()
	host.position = base + Basis(Vector3.UP, rot) * Vector3(float(dr[0]), float(dr[1]), float(dr[2]))
	host.rotation.y = rot + extra
	park.add_child(host)
	m.door_node = Node3D.new()
	m.door_node.position = Vector3(-w / 2.0, 0, 0.02)
	host.add_child(m.door_node)
	s.put(m.door_node, m.box(w, h, 0.05), Vector3(w / 2.0, h / 2.0, 0), Bib.cc(dr[5]), "caravan")
	s.put(m.door_node, m.box(0.05, 0.05, 0.1), Vector3(w - 0.12, h * 0.5, 0.05), Color(0.75, 0.75, 0.75), "stone")
	s.door_light_at(host, Vector3(w / 2.0 + 0.5, h + 0.35, 0.45))
	s.put(host, m.box(0.7, 0.5, 0.04), Vector3(-w / 2.0 - 0.75, h * 0.7, 0.03), s.window_mat(), "window")
	m.obj["door"] = W(host.transform * Vector3(0, 0, 0.9))


# ---- Erlebniswelt: the static things at the reserved places -----------------------------------------------------------------
func _erlebnis() -> void:
	bib.add("mouse_holes", P(-118.0, -103.0), 0.0, {"len": 3.0})
	bib.add("picnic_table", P(6.0, -77.0), 0.2, {"len": 2.0})
	bib.add("knothole_tree", P(10.0, -80.5), PI, {})
	bib.add("bbq", P(-125.0, -64.0), 0.0, {"style": "brick", "hot": 70.0})
	bib.add("fishing_rod", Vector3(80.6, 0.8, -198.5), 0.0)
	bib.add("bin", Vector3(79.4, 0.8, -198.4), 0.0, {"col": "2a6fb0"})
	bib.add("sunken_boat", Vector3(88.0, -0.7, -196.0), 0.5)
	bib.add("boot", Vector3(78.6, 0.8, -197.6), 1.0)
	bib.add("tree_house", P(-114.0, -84.0), 0.3, {"h": 4.0})
	bib.add("cave", P(-42.0, 142.0), PI, {"r": 2.2})
	bib.add("old_caravan", P(150.0, 116.0), 0.35)
	for i in range(5):
		bib.add("gnome", P(-82.0 + i * 0.9, 12.6 + 0.3 * sin(i * 2.0)), rng.randf() * TAU, {"col": ["2a5bb0", "c0392b", "2e7d32"][i % 3]})
	bib.add("bottle_post", P(-132.0, zs(-132.0) + 3.0), 0.7)
	bib.add("chest", P(117.0, 237.0), 0.4)
	var path := [Vector2(-95.0, -74.5), Vector2(-104.0, -79.0), Vector2(-112.0, -82.0)]   # the secret path (trodden grass)
	for i in range(path.size() - 1):
		var a: Vector2 = path[i]
		var b: Vector2 = path[i + 1]
		for k in range(6):
			var q := a.lerp(b, (k + 0.5) / 6.0)
			bib._part(Bib.B(0.5, 0.01, 0.35, q.x, H(q.x, q.y) + 0.02, q.y, "6a6a3a", 0, rng.randf() * 180.0, 0, "road"), Transform3D.IDENTITY, "road", "small", bib._cell_key(Vector3(q.x, 0, q.y)))
	var er := []
	for e in ERLEBNIS:
		var wp := WG(e[3], e[4])
		er.append({"nr": e[0], "id": e[1], "name": e[2], "x": snappedf(wp.x, 0.1), "z": snappedf(wp.z, 0.1), "y": snappedf(wp.y, 0.01)})
	s.data["erlebnis"] = er
	_register_discoveries()


# the hidden places for the discovery book (branch «entdecken»: main.entdecken.register) - only if it is there
const ENTDECKEN := [["see.baumhuette", 14, "Baumhütte hinter dem Sanitärgebäude", "Ein Trampelpfad hinter dem WC führt zu einer Hütte im Baum mit Strickleiter.", "Hinter dem WC-Häuschen ist das Gras ganz platt getreten …", "🌳", "any", Vector3(3, 6, 3), 8.0],
		["see.hoehle", 15, "Kleine Höhle am Hang", "Im Wald über dem Pfadi-Lager ist eine kleine Höhle. Nachts leuchten dort Glühwürmchen.", "Am Waldhang gibt es ein dunkles Loch zwischen den Felsen.", "🕳", "any", Vector3(4, 2.5, 3), 8.0],
		["see.versunkenes_boot", 16, "Versunkenes Boot", "Vom Ende des Bootsstegs sieht man ein altes Boot, das im See liegt – nur der Mast schaut heraus.", "Schau vom Ende des Stegs ins Wasser.", "⚓", "dry", Vector3(4, 1.5, 2), 12.0],
		["see.alter_wohnwagen", 17, "Verlassener Wohnwagen", "Am Waldrand steht ein alter Wohnwagen mit Moos auf dem Dach. Wer wohnt da wohl?", "Ganz oben am Waldrand, östlich vom Hochsitz, steht etwas Altes.", "🚐", "any", Vector3(6, 3, 3), 10.0],
		["see.zwergendorf", 18, "Gartenzwerg-Dorf", "In der Hecke bei den Bungalows wohnen fünf Gartenzwerge.", "Bei den Bungalows lohnt sich ein Blick in die Hecke.", "🧙", "any", Vector3(5, 1, 2), 6.0],
		["see.flaschenpost", 19, "Flaschenpost", "Am Strand liegt eine Flasche mit einem Zettel – eine Schatzkarte zum Aussichtspunkt.", "Am Westende des Strands glitzert etwas im Sand.", "🍾", "any", Vector3(0.6, 0.4, 0.6), 5.0]]


func _register_discoveries() -> void:
	var ed = m.get("entdecken")
	if ed == null or not ed.has_method("register"):
		return
	for e in ENTDECKEN:
		var pl: Array = ERLEBNIS[int(e[1]) - 1]
		ed.register(str(e[0]), {"scene": "ferienpark", "title": T.t(str(e[2])), "short_text": T.t(str(e[3])), "hint": T.t(str(e[4])),
				"icon": e[5], "position": WG(pl[3], pl[4]) + Vector3(0, float((e[7] as Vector3).y) * 0.5, 0), "size": e[7], "radius": e[8],
				"when": e[6], "kind": "ort"})
	ed.register("see.schatzkiste", {"scene": "ferienpark", "title": T.t("Schatzkiste beim Aussichtspunkt"),
			"short_text": T.t("Die Schatzkarte aus der Flaschenpost führt hierher."), "hint": T.t("Was zeigt wohl die Karte aus der Flaschenpost?"),
			"icon": "🧰", "position": WG(117.0, 237.0) + Vector3(0, 0.3, 0), "size": Vector3(0.8, 0.6, 0.6), "radius": 5.0, "kind": "ort"})


# ---- lights, smoke, flags near MoveEye ---------------------------------------------------------------------------------------
func _lights_and_fx() -> void:
	var near := []
	for l in bib.lamps:
		var wp := W(l[0])
		if wp.length() < 95.0:
			near.append([wp.length(), l])
	near.sort_custom(func(a, b): return a[0] < b[0])
	var nmax := 4 if lite else 10
	for i in range(mini(nmax, near.size())):
		var l: Array = near[i][1]
		var ol := OmniLight3D.new()
		ol.position = l[0]
		ol.light_color = l[1]
		ol.omni_range = 11.0
		ol.light_energy = 0.0
		ol.shadow_enabled = false
		park.add_child(ol)
		m.lamps.append(ol)
	info["lights"] = mini(nmax, near.size())
	var smokes := 0
	var flags := 0
	for f in bib.fx:
		var wp := W(f[1])
		match str(f[0]):
			"smoke":
				if wp.length() < 140.0 and smokes < (1 if lite else 4):
					s.smoke(wp)
					smokes += 1
			"flag":
				if wp.length() < 220.0 and flags < (2 if lite else 6):
					s.cloth(park, Vector2(1.4, 0.9), f[1] + Vector3(0.72, 5.4, 0), Vector3(0, float(f[3]), 0), Bib.cc(f[2] if f[2] != null else "c8102e"))
					flags += 1


# ---- hiding places around MoveEye ---------------------------------------------------------------------------------------------
func _hiding() -> void:
	var made := 0
	var tries := 0
	var kinds := ["bush", "bush", "woodpile", "crates", "barrels", "hedge"]
	s.data["fp_verstecke"] = []
	while made < (5 if lite else 9) and tries < 200:
		tries += 1
		var wp: Vector3 = m.pos_of(rng.randf_range(-170, 170), rng.randf_range(8.0, 34.0))
		var q := inv * wp
		if H(q.x, q.z) < 0.7 or _on_way(q.x, q.z, 3.0):
			continue
		var ok := true
		for o in m._ob_near(Vector2(wp.x, wp.z)):
			if float(m._ob_closest(o, Vector2(wp.x, wp.z))[1]) < 2.5:
				ok = false
				break
		if not ok:
			continue
		s.prop(kinds[rng.randi() % kinds.size()], wp, rng.randf() * TAU)
		(s.data["fp_verstecke"] as Array).append(wp)        # Erlebniswelt 12: the children hide here when MoveEye plays along
		made += 1
	info["hiding"] = made


# ---- Erlebniswelt 1–19 (erlebniswelt.gd): the vignettes at the reserved places --------------------------------------------------
func _erleben() -> void:
	var t0 := Time.get_ticks_msec()
	var ew = preload("res://scripts/erlebniswelt.gd").new()
	ew.setup(self)
	s.data["erleben"] = ew
	info["erleben_ms"] = Time.get_ticks_msec() - t0


# ---- Paket «Ferienpark-Leben» (ferienpark_leben.gd): the day by the clock (barbecue, quiet night, early birds) + the tasks ---
func _leben() -> void:
	var ew = s.data.get("erleben", null)
	if ew == null:
		return
	var t0 := Time.get_ticks_msec()
	var lv = preload("res://scripts/ferienpark_leben.gd").new()
	lv.setup(self, ew)
	s.data["leben"] = lv
	info["leben_ms"] = Time.get_ticks_msec() - t0


# ---- name signs of the places --------------------------------------------------------------------------------------------------
func _signs() -> void:
	for pl in PLACES:
		var p := P(pl[1], pl[2])
		if W(p).length() > 160.0:
			continue
		var l := Label3D.new()
		l.text = T.t(str(pl[0]))
		l.position = p + Vector3(0, 4.2, 0)
		l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		l.font_size = 72
		l.pixel_size = 0.012
		l.modulate = Color(0.98, 0.96, 0.9)
		l.outline_size = 10
		l.outline_modulate = Color(0.1, 0.12, 0.1)
		l.visibility_range_end = 120.0
		l.layers = m.HELPER_LAYER                       # only the window camera of the simulator (not the camera of MoveEye)
		park.add_child(l)


# ---- what the rest of the simulator needs ----------------------------------------------------------------------------------
func _data() -> void:
	var lane_z := -58.0
	match spot:
		"wohnmobil":
			lane_z = -14.0
		"bungalow":
			lane_z = 28.0
		"steg":
			lane_z = -104.0
	var rl := PackedVector2Array()
	var xs: Array = []
	for ln in LANES:
		if float(ln[0]) == lane_z:
			xs = [ln[1], ln[2]]
	if spot == "rezeption":                                    # the access road from the village, through the barrier
		for x in range(-330, -180, 10):
			var wp := WG(float(x), -58.0)
			rl.append(Vector2(wp.x, wp.z))
	else:
		var x := float(xs[0])
		while x <= float(xs[1]):
			var wp := WG(x, lane_z + 0.8)
			rl.append(Vector2(wp.x, wp.z))
			x += 10.0
	s.data["road_line"] = rl
	var best := Vector3(0, 0, -30)
	for v in rl:
		if Vector2(v).length() < Vector2(best.x, best.z).length():
			best = Vector3(v.x, 0, v.y)
	s.data["road_z"] = best.z + 1.2
	var orte := []
	for pl in PLACES:
		var wp := WG(pl[1], pl[2])
		orte.append([str(pl[0]), snappedf(wp.x, 0.1), snappedf(wp.z, 0.1), snappedf(Vector2(wp.x, wp.z).length(), 0.1)])
	s.data["orte"] = orte
	if not m.obj.has("bike") or m.bike_node == null:
		m.obj["bike"] = Vector3(3, 0, -6)


# =======================================================================================================================
# control {"action": "ferienpark", "do": "info" | "spot" (value) | "places" | "kinds"}
# =======================================================================================================================
static func control(main, d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "info"))
	var fp = main.scenes.data.get("ferienpark", null) if main.scenes != null else null
	match what:
		"spot":
			var v := str(d.get("value", ""))
			if not SPOTS.has(v):
				return {"ok": false, "error": "unknown spot", "spots": SPOT_ORDER}
			main.set_fp_spot(v)
			return {"ok": true, "spot": v}
		"lite_test":                                     # for tests until the Lite package is merged: Engine meta «lite», then rebuild
			Engine.set_meta("lite", bool(d.get("value", true)))
			if main.scene == "ferienpark":
				main.set_scene("ferienpark")
			return {"ok": true, "lite": Bib.lite()}
		"kinds":
			return {"ok": true, "kinds": Bib.names(), "n": Bib.KINDS.size()}
		"leben":                                         # Ferienpark-Leben: {do: leben} info · {do: leben, on: bool}
			var FL = preload("res://scripts/ferienpark_leben.gd")
			if d.has("on"):
				FL.set_on(main, bool(d["on"]))
			var lv = main.scenes.data.get("leben", null) if main.scenes != null else null
			if lv == null or not is_instance_valid(lv):
				return {"ok": false, "error": "not in the Ferienpark (a spot of the park)", "on": FL.on}
			return lv.info()
		"aufgabe":                                       # kleine Aufgaben: {do: aufgabe, what: kind | velo | zelt | stop | info}
			return preload("res://scripts/ferienpark_leben.gd").tasks(main).control(d)
		"erleben", "verstecken":                         # Erlebniswelt: {what: info | verstecken | fish | where (id) | state (id, state)}
			var ew = main.scenes.data.get("erleben", null) if main.scenes != null else null
			if ew == null or not is_instance_valid(ew):
				return {"ok": false, "error": "not in the Ferienpark"}
			if what == "verstecken":
				d = d.duplicate()
				d["what"] = "verstecken"
			return ew.control(d)
		"perf":
			return {"ok": true, "fps": Engine.get_frames_per_second(), "draw": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), "prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
					"scene": main.scene, "lite": Bib.lite(), "quality": main.quality, "nodes": main.get_tree().get_node_count()}
	if fp == null:
		return {"ok": true, "scene": main.scene, "ferienpark": false, "spots": spot_options()}
	return {"ok": true, "scene": main.scene, "ferienpark": true, "spot": fp.spot, "spots": spot_options(), "info": fp.info,
			"places": main.scenes.data.get("orte", []), "erlebnis": main.scenes.data.get("erlebnis", []), "pir": main.obj.get("pir"), "door": main.obj.get("door"), "bike": main.obj.get("bike"),
			"ground_at_0": fp.gy(0.0, 0.0), "ground_at_10": fp.gy(0.0, -10.0)}
