extends RefCounted
## 3D-4.x «Vier kompakte Szenen» (Daniel, 31.10.2026): je rund 200 × 200 m, jede mit eigenem Charakter und mehreren
## MoveEye-Standorten (wie im Ferienpark am See), gebaut aus der Szenen-Bibliothek (bib_objekte.gd):
##   pfadilager  Pfadilager im Wald (kompakt_pfadi.gd)     - dunkel und eng, Kinder, Tiere: schwer für die Erkennung
##   hofladen    Bauernhof mit Hofladen und Stellplätzen (kompakt_hof.gd) - viele Wärmequellen
##   bergdorf    Bergdorf mit Stellplatz (kompakt_dorf.gd)  - Kirche, Brunnen, Bäckerei, Bach, Seilbahn
##   festival    Festival-Gelände (kompakt_festival.gd)     - sehr viele Menschen, bunte Lichter: Stresstest
## Diese Datei ist die gemeinsame Grundlage: Gelände (main.ground_fn), gemalter Boden (Shader des Ferienparks), Bach,
## Wald, Wege, Lampen, Verstecke, Ortsschilder, Daten für Besucher und Autos. Jede Szene ist eine Unterklasse mit
## SPOTS / SPOT_ORDER / PLACES und den Funktionen H (Höhe), paint (Boden), content (Dinge), own_spot (dein Platz),
## people (Nachbarn: szenenplus.gd, Art «runde» mit eigenen Punkten und Stunden).
## Wie im Ferienpark steht MoveEye immer im Nullpunkt: die Szene wird gedreht und verschoben (Knoten «park»).
## Park-Koordinaten: x = Osten, z = Süden. Standort: [Name, x, z, Blickrichtung in Grad (0 = Norden, 90 = Osten)].
## Steuerbefehl {action: kompakt, do: info | spot (value) | perf}. Lite: Bib.lite() = Quality.lite().
##
## Welten (worlds.gd): Pfadilager und Bergdorf sind Orte im Bergtal, der Hofladen ein Ort im Ferienpark am See - dann baut
## die Welt das Gelände (eben auf der Fläche des Orts, Radius R) und diese Datei nur den Ort («flat»: Höhe 0, nichts
## ausserhalb R, gemalter Boden nur wo etwas ist: shaders/kompakt_ort.gdshader). Park-Nullpunkt = Mitte des Orts.
## Das Festival-Gelände ist eine eigene Welt (Gelände wie bisher), «allein» (--solo) baut auch die anderen wie bisher.

const Bib = preload("res://scripts/bib_objekte.gd")
const Szenen = preload("res://scripts/szenenplus.gd")
const T = preload("res://scripts/i18n.gd")

const SCENES := {"pfadilager": "res://scripts/kompakt_pfadi.gd", "hofladen": "res://scripts/kompakt_hof.gd",
		"bergdorf": "res://scripts/kompakt_dorf.gd", "festival": "res://scripts/kompakt_festival.gd"}
const NEAR := 130.0               # the painted ground (park metres from the centre)
const FAR := 1500.0

var s                             # scenes.gd
var m                             # main.gd
var bib
var park: Node3D
var id := ""
var spot := ""
var h0 := 0.0
var inv := Transform3D()
var rng := RandomNumberGenerator.new()
var lite := false
var info := {}
var ways: Array = []              # [[Vector2 …], width, colour] - painted, no trees there, the cars drive on «road»
var clear: Array = []             # [x0, z0, x1, z1] - no random tree, no grass there
var road: Array = []              # [Vector2 …] the road for the cars (park coordinates)
var anim_lights: Array = []       # [OmniLight3D / SpotLight3D, base colour, phase] - festival lights (only at night)
var flat := false                 # a place in a world (worlds.gd): the world makes the ground, the place is flat (height 0)
var place_r := 0.0                # its radius (only inside it is built)


# =======================================================================================================================
# the list of the scenes and their places (static: main.gd, scenes.gd)
# =======================================================================================================================
static func is_kompakt(sid: String) -> bool:
	return SCENES.has(sid)


static func _consts(sid: String) -> Dictionary:
	if not SCENES.has(sid):
		return {}
	var sc = load(SCENES[sid])
	return sc.get_script_constant_map() if sc != null else {}


static func spots_of(sid: String) -> Dictionary:
	return _consts(sid).get("SPOTS", {})


static func spot_options(sid: String) -> Array:
	var c := _consts(sid)
	var out := []
	for k in c.get("SPOT_ORDER", []):
		out.append([k, c["SPOTS"][k][0]])
	return out


static func build_scene(sc, sid: String) -> void:
	var k = load(SCENES[sid]).new()
	sc.data["kompakt"] = k                            # keeps it (and main.ground_fn) alive while the scene is there
	k._build(sc, sid)


static func build_place(sc, sid: String, r: float) -> void:
	"""worlds.gd: the place inside its world (the world is built already, around the chosen spot)"""
	var k = load(SCENES[sid]).new()
	k.flat = true
	k.place_r = r
	sc.data["kompakt"] = k
	k._build(sc, sid)


# =======================================================================================================================
# what every scene gives (overridden)
# =======================================================================================================================
func spots() -> Dictionary:
	return get_script().get_script_constant_map().get("SPOTS", {})


func spot_order() -> Array:
	return get_script().get_script_constant_map().get("SPOT_ORDER", [])


func places() -> Array:
	return get_script().get_script_constant_map().get("PLACES", [])


func H(_x: float, _z: float) -> float:
	return 0.0


func ground_colour() -> Color:
	return Color(0.30, 0.42, 0.18)


func far_colour(_x: float, _z: float, h: float) -> Color:
	if h > 140.0:
		return Color(0.42, 0.41, 0.38).lerp(Color(0.86, 0.87, 0.9), smoothstep(160.0, 260.0, h))
	if h > 30.0:
		return Color(0.16, 0.24, 0.12)
	return ground_colour().darkened(0.08)


func paint(_img: Image) -> void:
	pass


func content() -> void:
	pass


func own_spot() -> void:
	pass


func people() -> Array:
	return []


func grass_n() -> int:
	return 500


# =======================================================================================================================
# coordinates
# =======================================================================================================================
func hh(x: float, z: float) -> float:
	"""the height of the ground of the place (0 when it is a place in a world: the world made it flat)"""
	return 0.0 if flat else H(x, z)


func inside(x: float, z: float, margin := 0.0) -> bool:
	"""in the place (always true for a scene of its own)"""
	return not flat or Vector2(x, z).length() < place_r - margin


func P(x: float, z: float, dy := 0.0) -> Vector3:
	"""a point on the ground (park coordinates)"""
	return Vector3(x, hh(x, z) + dy, z)


func W(p: Vector3) -> Vector3:
	"""park -> world"""
	return park.transform * p


func WG(x: float, z: float, dy := 0.0) -> Vector3:
	"""park point on the ground -> world"""
	return park.transform * P(x, z, dy)


func wrot(r: float) -> float:
	return r + park.rotation.y


func gy(x: float, z: float) -> float:
	"""height of the ground in WORLD coordinates (main.ground_fn)"""
	var p := inv * Vector3(x, 0, z)
	return H(p.x, p.z) - h0


func nl(count: int) -> int:
	"""fewer in Lite"""
	return maxi(1, int(round(count * 0.35))) if lite else count


# =======================================================================================================================
# building
# =======================================================================================================================
func _build(sc, sid: String) -> void:
	var t0 := Time.get_ticks_msec()
	s = sc
	m = sc.m
	id = sid
	lite = Bib.lite() or str(m.quality) == "simple"
	rng.seed = hash(sid)
	var sps := spots()
	spot = str(m.scene_spot(sid)) if m.has_method("scene_spot") else ""
	if not sps.has(spot):
		spot = str(spot_order()[0])
	var sp: Array = sps[spot]
	h0 = hh(sp[1], sp[2])
	park = Node3D.new()
	park.name = sid
	var b := Basis(Vector3.UP, deg_to_rad(float(sp[3])))
	park.transform = Transform3D(b, b * -Vector3(sp[1], h0, sp[2]))
	s.root.add_child(park)
	inv = park.transform.affine_inverse()
	if not flat:                                       # a place in a world: the world has the ground (worlds.gd)
		m.terrain = true
		m.ground_fn = Callable(self, "gy")
	bib = Bib.new(m, s, park, park.transform)
	if flat:
		bib.keep = [[Vector2.ZERO, place_r]]
	m.door_node = null                                 # (the door of the scene before is gone; each spot makes its own)
	m.door_light = null                                # 3D-4.41: its light too (it was freed with the old scene -> errors in _update_sky)
	content()                                          # (fills ways / clear / road first, the ground is painted after)
	own_spot()
	_door_fallback()
	var t1 := Time.get_ticks_msec()
	if flat:
		_ground_place()
	else:
		_ground()
	bib.finish()
	_lights_and_fx()
	_hiding()
	_signs()
	s.meadow(nl(grass_n()), 3.0, 45.0, func(p: Vector3):
		var q := inv * p
		return _on_way(q.x, q.z, 1.5) or _is_clear(q.x, q.z, 0.0) or _water_at(q.x, q.z) or not inside(q.x, q.z, 1.0))
	_data()
	if not anim_lights.is_empty():
		m.anims.append(_light_show)
	info.merge({"ms": Time.get_ticks_msec() - t0, "ground_ms": Time.get_ticks_msec() - t1, "spot": spot, "lite": lite, "in_world": flat, "r": place_r,
			"lib": bib.stats.duplicate(), "lamps": bib.lamps.size(), "people": s.data.get("nachbarn", []).size()}, true)
	print("Kompakt %s: %s, %d ms, %s" % [sid, spot, info["ms"], str(bib.stats)])


# ---- ground ------------------------------------------------------------------------------------------------------------------
func _ground() -> void:
	var near := _grid(-NEAR, NEAR, 4.0 if lite else 2.5, false)
	var far := _grid(-FAR, FAR, 60.0, true)
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/ferienpark_boden.gdshader")
	tm.set_shader_parameter("photo", _paint())
	tm.set_shader_parameter("rect", Vector4(-NEAR, -NEAR, 2.0 * NEAR, 2.0 * NEAR))
	tm.set_shader_parameter("noise_tex", m.noise_tex)
	var fm := ShaderMaterial.new()
	fm.shader = tm.shader
	fm.set_shader_parameter("photo", _paint_far())
	fm.set_shader_parameter("rect", Vector4(-FAR, -FAR, 2.0 * FAR, 2.0 * FAR))
	fm.set_shader_parameter("noise_tex", m.noise_tex)
	fm.set_shader_parameter("detail", 0.0)
	m.ground_mats = [tm, fm]
	for pair in [[near, tm], [far, fm]]:
		var mi: MeshInstance3D = m.add_mesh(park, pair[0], Vector3.ZERO, pair[1], "x")
		var th: MeshInstance3D = park.get_child(park.get_child_count() - 1)
		th.material_override = m.tmats["ground"]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if pair[0] == far else GeometryInstance3D.SHADOW_CASTING_SETTING_ON


func _ground_place() -> void:
	"""a place in a world: a flat disc over the flat area of the world, painted only where the place has something"""
	var r := place_r + 1.0
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 48
	for i in range(n):
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		for q in [Vector3.ZERO, Vector3(cos(a1) * r, 0, sin(a1) * r), Vector3(cos(a0) * r, 0, sin(a0) * r)]:
			st.set_normal(Vector3.UP)
			st.add_vertex(q + Vector3(0, 0.035, 0))
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/kompakt_ort.gdshader")
	tm.set_shader_parameter("photo", _paint())
	tm.set_shader_parameter("rect", Vector4(-NEAR, -NEAR, 2.0 * NEAR, 2.0 * NEAR))
	tm.set_shader_parameter("noise_tex", m.noise_tex)
	m.ground_mats.append(tm)
	var mi: MeshInstance3D = m.add_mesh(park, st.commit(), Vector3.ZERO, tm, "x")
	if mi != null:
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var th: MeshInstance3D = park.get_child(park.get_child_count() - 1)
	if th != mi and m.tmats.has("ground"):
		th.material_override = m.tmats["ground"]


func _grid(lo: float, hi: float, step: float, hole: bool) -> ArrayMesh:
	var nn := int(round((hi - lo) / step)) + 1
	var hs := PackedFloat32Array()
	hs.resize(nn * nn)
	for j in range(nn):
		for i in range(nn):
			var x := lo + i * step
			var z := lo + j * step
			var h := H(x, z)
			if hole and absf(x) < NEAR - 1.0 and absf(z) < NEAR - 1.0:
				h -= 6.0                                   # the far ground stays below the near one
			hs[j * nn + i] = h
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	verts.resize(nn * nn)
	norms.resize(nn * nn)
	for j in range(nn):
		for i in range(nn):
			var hx := hs[j * nn + mini(i + 1, nn - 1)] - hs[j * nn + maxi(i - 1, 0)]
			var hz := hs[mini(j + 1, nn - 1) * nn + i] - hs[maxi(j - 1, 0) * nn + i]
			verts[j * nn + i] = Vector3(lo + i * step, hs[j * nn + i], lo + j * step)
			norms[j * nn + i] = Vector3(-hx, 2.0 * step, -hz).normalized()
	var idx := PackedInt32Array()
	for j in range(nn - 1):
		for i in range(nn - 1):
			if hole:
				var x0 := lo + i * step
				var z0 := lo + j * step
				if x0 >= -NEAR and x0 + step <= NEAR and z0 >= -NEAR and z0 + step <= NEAR:
					continue
			var a := j * nn + i
			idx.append_array([a, a + 1, a + nn, a + 1, a + nn + 1, a + nn])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


func _mpp() -> float:
	return 1.0 if lite else 0.5


func _px(x: float) -> int:
	return int(round((x + NEAR) / _mpp()))


func _paint() -> ImageTexture:
	var nn := int(2.0 * NEAR / _mpp())
	var img := Image.create(nn, nn, false, Image.FORMAT_RGBA8 if flat else Image.FORMAT_RGB8)
	img.fill(Color(0, 0, 0, 0) if flat else ground_colour())         # in a world: only the painted parts
	paint(img)
	for w in ways:
		polyline(img, w[0], float(w[1]), w[2])
	return ImageTexture.create_from_image(img)


func _paint_far() -> ImageTexture:
	var nn := 120
	var st := 2.0 * FAR / nn
	var img := Image.create(nn, nn, false, Image.FORMAT_RGB8)
	for j in range(nn):
		for i in range(nn):
			var x := -FAR + (i + 0.5) * st
			var z := -FAR + (j + 0.5) * st
			img.set_pixel(i, j, far_colour(x, z, H(x, z)))
	return ImageTexture.create_from_image(img)


func rect(img: Image, x0: float, z0: float, x1: float, z1: float, c: Color) -> void:
	var nn := img.get_width()
	var a := Vector2i(clampi(_px(x0), 0, nn), clampi(_px(z0), 0, nn))
	var b := Vector2i(clampi(_px(x1), 0, nn), clampi(_px(z1), 0, nn))
	if b.x > a.x and b.y > a.y:
		img.fill_rect(Rect2i(a, b - a), c)


func stamp(img: Image, x: float, z: float, w: float, c: Color) -> void:
	rect(img, x - w / 2.0, z - w / 2.0, x + w / 2.0, z + w / 2.0, c)


func disc(img: Image, x: float, z: float, r: float, c: Color) -> void:
	var k := -r
	while k <= r:
		var hw := sqrt(maxf(0.0, r * r - k * k))
		rect(img, x - hw, z + k, x + hw, z + k + _mpp(), c)
		k += _mpp()


func polyline(img: Image, pts: Array, w: float, c: Color) -> void:
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var L := a.distance_to(b)
		var k := 0.0
		while k <= L:
			var p := a.lerp(b, k / maxf(L, 0.01))
			stamp(img, p.x, p.y, w, c)
			k += _mpp() * 1.5


# ---- water: a creek as a ribbon, people do not walk in it ---------------------------------------------------------------------
var creeks: Array = []            # [[Vector2 …], width]


func creek(pts: Array, w: float, bridges := []) -> void:
	"""a creek along pts (park coordinates, the bed is in H - creek_depth); bridges = [z or index …] where people cross"""
	creeks.append([pts, w])
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var d := (b - a).normalized()
		var nrm := Vector2(-d.y, d.x) * w * 0.5
		var L := a.distance_to(b)
		var k := 0.0
		while k < L:
			var p0 := a.lerp(b, k / L)
			var p1 := a.lerp(b, minf(k + 2.0, L) / L)
			k += 2.0
			if not inside(p0.x, p0.y, 1.0) or not inside(p1.x, p1.y, 1.0):
				continue
			var y0 := hh(p0.x, p0.y) + (0.06 if flat else 0.18)
			var y1 := hh(p1.x, p1.y) + (0.06 if flat else 0.18)
			var v := [Vector3(p0.x - nrm.x, y0, p0.y - nrm.y), Vector3(p0.x + nrm.x, y0, p0.y + nrm.y),
					Vector3(p1.x - nrm.x, y1, p1.y - nrm.y), Vector3(p1.x + nrm.x, y1, p1.y + nrm.y)]
			for q in [v[0], v[1], v[2], v[1], v[3], v[2]]:
				st.set_normal(Vector3.UP)
				st.add_vertex(q)
	var cm := StandardMaterial3D.new()
	cm.albedo_color = Color(0.16, 0.3, 0.34)
	cm.metallic = 0.25
	cm.roughness = 0.08
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.add_mesh(park, st.commit(), Vector3.ZERO, cm, "pond")
	for i in range(pts.size() - 1):                    # obstacles along the water (not at the bridges)
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var c := (a + b) * 0.5
		var near_bridge := false
		for bz in bridges:
			if Geometry2D.get_closest_point_to_segment(bz, a, b).distance_to(bz) < 3.5:
				near_bridge = true
		if near_bridge or not inside(c.x, c.y):
			continue
		var d := b - a
		m.add_obstacle_box(W(Vector3(c.x, 0, c.y)), w + 0.6, d.length() + 0.4, wrot(atan2(d.x, d.y)))
		m.set_obstacle_height(0.1)


func creek_dist(x: float, z: float) -> float:
	var best := 1.0e9
	for c in creeks:
		var pts: Array = c[0]
		for i in range(pts.size() - 1):
			var q := Geometry2D.get_closest_point_to_segment(Vector2(x, z), pts[i], pts[i + 1])
			best = minf(best, q.distance_to(Vector2(x, z)))
	return best


static func seg_dist(pts: Array, x: float, z: float) -> float:
	var best := 1.0e9
	for i in range(pts.size() - 1):
		var q := Geometry2D.get_closest_point_to_segment(Vector2(x, z), pts[i], pts[i + 1])
		best = minf(best, q.distance_to(Vector2(x, z)))
	return best


func _water_at(x: float, z: float) -> bool:
	for c in creeks:
		if seg_dist(c[0], x, z) < float(c[1]) * 0.5 + 0.8:
			return true
	return false


# ---- ways and free places -------------------------------------------------------------------------------------------------------
func way(pts: Array, w: float, c: Color) -> void:
	ways.append([pts, w, c])


func _on_way(x: float, z: float, extra := 1.0) -> bool:
	for wv in ways:
		if seg_dist(wv[0], x, z) < float(wv[1]) * 0.5 + extra:
			return true
	return false


func _is_clear(x: float, z: float, extra := 2.0) -> bool:
	for r in clear:
		if x > r[0] - extra and x < r[2] + extra and z > r[1] - extra and z < r[3] + extra:
			return true
	return false


func free_at(x: float, z: float, extra := 2.0) -> bool:
	if not inside(x, z, 1.5):
		return false
	return not (_on_way(x, z, extra) or _is_clear(x, z, extra) or _water_at(x, z) or creek_dist(x, z) < extra + 1.0)


# ---- trees: MultiMesh far away, real trees (wind, the players' camera) near MoveEye --------------------------------------------
func forest(area: Callable, step: float, dens: float, conifer_share := 0.7, near_r := 34.0) -> void:
	"""trees on a grid of step metres where area(x, z) is true (park coordinates)"""
	var con := []
	var broad := []
	var real := []
	var nreal := 0
	var lim := minf(NEAR - 4.0, place_r) if flat else NEAR - 4.0
	var z := -lim
	var d := dens * (0.45 if lite else 1.0)
	while z < lim:
		var x := -lim
		while x < lim:
			var px := x + rng.randf_range(-step * 0.4, step * 0.4)
			var pz := z + rng.randf_range(-step * 0.4, step * 0.4)
			x += step
			if rng.randf() > d or not area.call(px, pz) or not free_at(px, pz, 2.0):
				continue
			var e := [P(px, pz, -0.15), rng.randf() * TAU, rng.randf_range(0.8, 1.35)]
			var dist := W(e[0]).length()
			if dist < 5.0:
				continue                                       # not on top of MoveEye
			if dist < near_r and nreal < (14 if lite else 40):
				real.append([e, rng.randf() < conifer_share])
				nreal += 1
			elif rng.randf() < conifer_share:
				con.append(e)
			else:
				broad.append(e)
		z += step
	bib.many("conifer", con)
	bib.many("tree", broad)
	for r in real:
		s.tree(s.root, W(r[0][0]), r[0][2], 1 if r[1] else 0)
	info["trees"] = info.get("trees", 0) + con.size() + broad.size() + real.size()


# ---- your door / light (like the Ferienpark) ----------------------------------------------------------------------------------
func own_door(d: Dictionary, base: Vector3, rot: float) -> void:
	"""the door of your building or vehicle as its own node (the door sensor opens it), its light and a lit window"""
	if not d.has("door"):
		return
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


func own_motorhome(x: float, z: float, rot: float) -> void:
	"""your motorhome on a pitch: the door sensor, the PIR in front, the bike, table and grill"""
	var d: Dictionary = bib.add("motorhome", P(x, z), rot, {"len": 7.0, "style": "alcove", "col": "f2f2f2", "stripe": "2a6fb0", "nodoor": true})
	own_door(d, P(x, z), rot)
	var out := Vector3(sin(rot), 0, cos(rot))          # the door side (+z of the motorhome)
	var along := Vector3(cos(rot), 0, -sin(rot))
	var c := Vector3(x, 0, z)
	var pp: Vector3 = c + out * 3.6
	m.obj["pir"] = WG(pp.x, pp.z)
	var bp: Vector3 = c + out * 2.6 + along * 3.4
	s.bike(WG(bp.x, bp.z), wrot(rot + 0.3))
	var tp: Vector3 = c + out * 4.2 - along * 1.2
	var gp: Vector3 = c + out * 4.4 + along * 1.8
	Szenen._own_things(s, WG(tp.x, tp.z), WG(gp.x, gp.z))
	s.data["platz"] = [WG(pp.x, pp.z), 7.0]


func own_tent(x: float, z: float, rot: float, col := Color(0.9, 0.5, 0.15)) -> void:
	Szenen._tent(s, WG(x, z), wrot(rot), col, true)
	s.data["platz"] = [WG(x, z), 6.0]


func _door_fallback() -> void:
	"""a spot without a door of its own (Dorfplatz, Weide, Bühne …): the door sensor is an invisible door at m.obj["door"]
	(or next to MoveEye) - main.gd needs a door node and its light in every scene"""
	var door_ok: bool = m.door_node != null and is_instance_valid(m.door_node) and m.door_node.is_inside_tree()
	var light_ok: bool = m.door_light != null and is_instance_valid(m.door_light) and m.door_light.is_inside_tree()
	if door_ok and light_ok:
		return
	var at: Vector3 = m.obj.get("door", Vector3(-3.0, 0.0, 2.0))
	var host := Node3D.new()
	host.name = "tuer_sensor"
	host.position = at
	s.root.add_child(host)
	if not door_ok:
		m.door_node = Node3D.new()
		host.add_child(m.door_node)
		m.obj["door"] = at
	if not light_ok:
		s.door_light_at(host, Vector3(0, 2.3, 0.4))


# ---- lights, smoke and flags near MoveEye -------------------------------------------------------------------------------------
func _lights_and_fx() -> void:
	var near := []
	for l in bib.lamps:
		var wp := W(l[0])
		if wp.length() < 80.0:
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
				if wp.length() < 120.0 and smokes < (1 if lite else 3):
					s.smoke(wp)
					smokes += 1
			"flag":
				if wp.length() < 160.0 and flags < (2 if lite else 5):
					s.cloth(park, Vector2(1.4, 0.9), f[1] + Vector3(0.72, 5.4, 0), Vector3(0, float(f[3]), 0), Bib.cc(f[2] if f[2] != null else "c8102e"))
					flags += 1


func show_light(p: Vector3, col: Color, spot_dir := Vector3.ZERO, rng_m := 18.0) -> void:
	"""a coloured light of a stage or a tent (only at night, changes its colour - _light_show)"""
	var l: Light3D
	if spot_dir != Vector3.ZERO:
		var sl := SpotLight3D.new()
		sl.spot_range = rng_m
		sl.spot_angle = 28.0
		l = sl
	else:
		var ol := OmniLight3D.new()
		ol.omni_range = rng_m
		l = ol
	l.position = p
	l.light_color = col
	l.light_energy = 0.0
	l.shadow_enabled = false
	park.add_child(l)
	if spot_dir != Vector3.ZERO:
		l.look_at_from_position(p, p + spot_dir, Vector3.UP if absf(spot_dir.normalized().y) < 0.95 else Vector3.FORWARD)
	anim_lights.append([l, col, rng.randf() * TAU])


const SHOW_COLS := [Color(1, 0.15, 0.5), Color(0.2, 0.4, 1), Color(0.1, 1, 0.5), Color(1, 0.75, 0.1), Color(0.75, 0.2, 1)]


func _light_show(_dt: float, t: float):
	"""the festival lights: off by day, at night they change colour and pulse (a few times per second)"""
	if not is_instance_valid(park):
		return true
	var dark: bool = m.is_dark()
	for e in anim_lights:
		var l: Light3D = e[0]
		if not is_instance_valid(l):
			continue
		if not dark:
			l.light_energy = 0.0
			continue
		var ph := float(e[2])
		var k := int(floor(t * 0.5 + ph * 3.0)) % SHOW_COLS.size()
		l.light_color = SHOW_COLS[k]
		l.light_energy = 3.0 + 2.5 * sin(t * 2.3 + ph * 5.0)
	return false


# ---- hiding places around MoveEye ----------------------------------------------------------------------------------------------
func hide_kinds() -> Array:
	return ["bush", "bush", "woodpile", "crates", "barrels"]


func _hiding() -> void:
	var made := 0
	var tries := 0
	var kinds := hide_kinds()
	while made < (4 if lite else 8) and tries < 200:
		tries += 1
		var wp: Vector3 = m.pos_of(rng.randf_range(-170, 170), rng.randf_range(8.0, 32.0))
		var q := inv * wp
		if _on_way(q.x, q.z, 1.5) or _water_at(q.x, q.z) or not inside(q.x, q.z, 1.5):    # (the buildings: obstacles below)
			continue
		var ok := true
		for o in m._ob_near(Vector2(wp.x, wp.z)):
			if float(m._ob_closest(o, Vector2(wp.x, wp.z))[1]) < 2.5:
				ok = false
				break
		if not ok:
			continue
		s.prop(kinds[rng.randi() % kinds.size()], wp, rng.randf() * TAU)
		made += 1
	info["hiding"] = made


# ---- name signs (only the window camera of the simulator sees them) --------------------------------------------------------------
func _signs() -> void:
	for pl in places():
		var p := P(pl[1], pl[2])
		if W(p).length() > 140.0 or not inside(pl[1], pl[2]):
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
		l.visibility_range_end = 110.0
		l.layers = m.HELPER_LAYER
		park.add_child(l)


# ---- what the rest of the simulator needs (cars, places, neighbours) -------------------------------------------------------------
func _data() -> void:
	if road.size() >= 2 and not (flat and s.data.has("road_line")):    # in a world: its road (cars come from far)
		var rl := PackedVector2Array()
		for i in range(road.size() - 1):
			var a: Vector2 = road[i]
			var b: Vector2 = road[i + 1]
			var L := a.distance_to(b)
			var k := 0.0
			while k < L:
				var q := a.lerp(b, k / L)
				var wp := WG(q.x, q.y)
				rl.append(Vector2(wp.x, wp.z))
				k += 10.0
		var last: Vector2 = road[road.size() - 1]
		var wl := WG(last.x, last.y)
		rl.append(Vector2(wl.x, wl.z))
		s.data["road_line"] = rl
		var best := Vector2(0, -30)
		for v in rl:
			if v.length() < best.length():
				best = v
		s.data["road_z"] = best.y + 1.2
	var orte := []
	for pl in places():
		var wp := WG(pl[1], pl[2])
		orte.append([str(pl[0]), snappedf(wp.x, 0.1), snappedf(wp.z, 0.1), snappedf(Vector2(wp.x, wp.z).length(), 0.1)])
	s.data["orte"] = orte
	var nb := []
	for e in people():
		var ee: Array = e.duplicate(true)
		if ee[1] is Vector2:
			ee[1] = WG(ee[1].x, ee[1].y)
		if ee.size() > 2 and typeof(ee[2]) == TYPE_DICTIONARY and ee[2].has("pts"):
			var pts := []
			for p in ee[2]["pts"]:
				pts.append(WG(p.x, p.y) if p is Vector2 else p)
			ee[2]["pts"] = pts
		nb.append(ee)
	s.data["nachbarn"] = nb
	if not m.obj.has("bike") or m.bike_node == null:
		m.obj["bike"] = Vector3(3, 0, -6)


func pts2(arr: Array) -> Array:
	"""[[x, z], …] -> [Vector2 …]"""
	var out := []
	for a in arr:
		out.append(Vector2(a[0], a[1]))
	return out


# =======================================================================================================================
# control {"action": "kompakt", "do": "info" | "spot" (value) | "perf" | "scenes"}
# =======================================================================================================================
static func control(main, d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "info"))
	var k = main.scenes.data.get("kompakt", null) if main.scenes != null else null
	match what:
		"spot":
			var v := str(d.get("value", ""))
			if not is_kompakt(main.scene):
				return {"ok": false, "error": "not a compact scene", "scenes": SCENES.keys()}
			if not spots_of(main.scene).has(v):
				return {"ok": false, "error": "unknown spot", "spots": spot_options(main.scene)}
			main.set_scene_spot(v)
			return {"ok": true, "spot": v}
		"scenes":
			var out := {}
			for sid in SCENES:
				out[sid] = spot_options(sid)
			return {"ok": true, "scenes": out}
		"perf":
			return {"ok": true, "fps": Engine.get_frames_per_second(), "draw": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), "prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
					"scene": main.scene, "lite": Bib.lite(), "quality": main.quality, "nodes": main.get_tree().get_node_count(),
					"visitors": main.visitors.get_child_count()}
	if k == null or not is_instance_valid(k.park):
		return {"ok": true, "scene": main.scene, "kompakt": false}
	var nbs := 0
	if main.szenen != null:
		nbs = main.szenen.nb.size()
	return {"ok": true, "scene": main.scene, "kompakt": true, "spot": k.spot, "spots": spot_options(main.scene), "info": k.info,
			"places": main.scenes.data.get("orte", []), "pir": main.obj.get("pir"), "door": main.obj.get("door"), "bike": main.obj.get("bike"),
			"neighbours": nbs, "lights_show": k.anim_lights.size(), "ground_at_0": k.gy(0.0, 0.0) if not k.flat else 0.0, "in_world": k.flat,
			"world": str(main.scenes.data.get("welt", {}).get("world", ""))}
