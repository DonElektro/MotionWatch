extends RefCounted
## «Flora und Fauna» Paket 2 – Gras, Boden, Wind (Zweig sim-flora-gras, erster Meilenstein: Stellplatz).
## Nur Normal / Hoch (Flora.stufe); Lite, MW_FLORA=alt und --quality bleiben genau wie vorher.
##
##   - Ringe: nah (bis 12 m) zusätzliche feine Gras-Büschel und Blumen mit echten Köpfen (Blütenblätter + Mitte),
##     mitte = die bisherigen Büschel (neben Wegen niedergetreten), fern = im Boden-Shader (Gras-Struktur, Blüten-Tupfen).
##   - Boden (shaders/grass.gdshader, p2): die Fotos gehen nahtlos in ihre mittlere Farbe über (keine Linie bei tex_far),
##     nah eine dritte Abtastung gegen Kacheln, Trampelpfade = abgetretene Ränder neben den Wegen (gelaende.paths).
##   - Böen: Gras, Boden, Bäume, Büsche, Hecken in EINER Welle (gleiches Rauschen, gleiche Richtung und Geschwindigkeit
##     wie foliage.gdshader); wind_fx.gd setzt gust_amt / dir auf alle.
## Zufall: eigener RandomNumberGenerator mit Startwert aus dem Ring – sc.rng bleibt unberührt.

const Flora = preload("res://scripts/flora.gd")
const NAH := 12.0
const PFAD_MAX := 32                 # HD 4600: at most 32 segments, only within 60 m (grass.gdshader)

static var _fine: ArrayMesh = null
static var _head: ArrayMesh = null


static func an(m) -> bool:
	return Flora.stufe(m) in ["normal", "hoch"]


# ---- Netze ---------------------------------------------------------------------------------------------------------------
static func fine_mesh() -> ArrayMesh:
	"""ein feines, dichtes Büschel für den nahen Ring: 9 schmale Halme (3 Dreiecke pro Halm)"""
	if _fine == null:
		var r := RandomNumberGenerator.new()
		r.seed = 2201
		var v := PackedVector3Array()
		var nn := PackedVector3Array()
		for i in range(9):
			var a := r.randf() * TAU
			var hh := r.randf_range(0.1, 0.26)
			var off := Vector3(r.randf_range(-0.06, 0.06), 0, r.randf_range(-0.06, 0.06))
			var side := Vector3(cos(a), 0, sin(a)) * 0.018
			var lean := Vector3(-sin(a), 0, cos(a)) * r.randf_range(0.03, 0.12) * hh / 0.3
			var mid := off + Vector3(0, hh * 0.55, 0) + lean * 0.35
			var top := off + Vector3(0, hh, 0) + lean
			var nrm := Vector3(-sin(a), 0.4, cos(a)).normalized()
			for q in [off - side, off + side, mid + side * 0.55, off - side, mid + side * 0.55, mid - side * 0.55,
					mid - side * 0.55, mid + side * 0.55, top]:
				v.append(q)
				nn.append(nrm)
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_NORMAL] = nn
		_fine = ArrayMesh.new()
		_fine.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return _fine


static func head_mesh() -> ArrayMesh:
	"""ein Blütenkopf: 10 Blütenblätter (leicht nach oben gewölbt) um eine erhabene Mitte. Ecken-Farbe: Blätter weiss
	(= Farbe der Blume), Mitte gelb; Alpha 0.5 = «Kopf» (der Shader dunkelt ihn nicht ab wie die Halme unten)"""
	if _head == null:
		var v := PackedVector3Array()
		var c := PackedColorArray()
		var n := 10
		var pet := Color(1, 1, 1, 0.5)
		var mid := Color(1.0, 0.78, 0.15, 0.5)
		for i in range(n):
			var a0 := TAU * (i - 0.32) / n
			var a1 := TAU * (i + 0.32) / n
			var am := TAU * i / n
			var p0 := Vector3(cos(a0), 0, sin(a0)) * 0.012
			var p1 := Vector3(cos(a1), 0, sin(a1)) * 0.012
			var tip := Vector3(cos(am), 0, sin(am)) * 0.046 + Vector3(0, 0.008, 0)
			var wide := Vector3(cos(am), 0, sin(am)) * 0.032 + Vector3(0, 0.004, 0)
			var sd := Vector3(-sin(am), 0, cos(am)) * 0.009
			for q in [p0, wide - sd, tip, p0, tip, p1, p1, tip, wide + sd]:
				v.append(q)
				c.append(pet)
		for i in range(6):                                     # the raised centre
			var a0 := TAU * i / 6.0
			var a1 := TAU * (i + 1) / 6.0
			for q in [Vector3(0, 0.007, 0), Vector3(cos(a0), 0, sin(a0)) * 0.014 + Vector3(0, 0.003, 0), Vector3(cos(a1), 0, sin(a1)) * 0.014 + Vector3(0, 0.003, 0)]:
				v.append(q)
				c.append(mid)
		var nn := PackedVector3Array()
		nn.resize(v.size())
		nn.fill(Vector3.UP)
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_NORMAL] = nn
		arr[Mesh.ARRAY_COLOR] = c
		_head = ArrayMesh.new()
		_head.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return _head


# ---- naher Ring -----------------------------------------------------------------------------------------------------------
static func _rng(dmin: float, dmax: float, salt: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = hash(Vector3i(roundi(dmin * 10), roundi(dmax * 10), salt))
	return r


static func _pos(m, r: RandomNumberGenerator, dmin: float, dmax: float) -> Vector3:
	var d := sqrt(lerpf(dmin * dmin, dmax * dmax, r.randf()))
	return m.pos_of(r.randf_range(-180, 180), d)


static func near_grass(sc, dmin: float, dmax: float, keep_clear: Callable, cells: Dictionary, cell_key: Callable) -> void:
	"""zusätzliche feine Büschel im nahen Ring (eigener Zufall) in cells (gleiche Felder wie Veg.grass)"""
	if not an(sc.m) or dmin >= NAH:
		return
	var hi := minf(dmax, NAH)
	var n := int((4200 if Flora.stufe(sc.m) == "hoch" else 2600) * (hi * hi - dmin * dmin) / (NAH * NAH))   # Hoch: 4200 (was 5200)
	var r := _rng(dmin, hi, 71)
	var greens := [Color(0.3, 0.5, 0.17), Color(0.34, 0.52, 0.19), Color(0.27, 0.45, 0.15), Color(0.4, 0.52, 0.22)]
	for i in range(n):
		var p := _pos(sc.m, r, dmin, hi)
		if keep_clear.is_valid() and keep_clear.call(p):
			continue
		p.y = sc.m.ground_y(p.x, p.z)
		var sz := r.randf_range(0.8, 1.3) * trodden(sc.m, p)
		var b := Basis(Vector3.UP, r.randf() * TAU).scaled(Vector3(sz, sz * r.randf_range(0.8, 1.2), sz))
		var key: Vector2i = cell_key.call(p)
		if not cells.has(key):
			cells[key] = []
		cells[key].append([Transform3D(b, p - Vector3(0, 0.01, 0)), greens[r.randi() % greens.size()]])


static func near_flowers(sc, dmin: float, dmax: float, keep_clear: Callable, cols: Array, stems: Dictionary, blooms: Dictionary, cell_key: Callable) -> void:
	"""zusätzliche Blumen im nahen Ring, in Flecken (eigener Zufall)"""
	if not an(sc.m) or dmin >= NAH + 4.0:
		return
	var hi := minf(dmax, NAH + 4.0)
	var n := 520 if Flora.stufe(sc.m) == "hoch" else 260
	var r := _rng(dmin, hi, 73)
	var c0 := Vector3.ZERO
	var col: Color = cols[0]
	for i in range(n):
		var p: Vector3
		if i % 8 == 0:
			c0 = _pos(sc.m, r, dmin, hi)
			col = cols[r.randi() % cols.size()]              # a patch: mostly one kind of flower
			p = c0
		else:
			p = c0 + Vector3(r.randf_range(-1.3, 1.3), 0, r.randf_range(-1.3, 1.3))
		if keep_clear.is_valid() and keep_clear.call(p):
			continue
		p.y = sc.m.ground_y(p.x, p.z)
		var hh := r.randf_range(0.7, 1.3) * trodden(sc.m, p)
		var key: Vector2i = cell_key.call(p)
		if not stems.has(key):
			stems[key] = []
			blooms[key] = []
		stems[key].append([Transform3D(Basis(Vector3.UP, r.randf() * TAU).scaled(Vector3(1, hh, 1)), p), Color(0.3, 0.48, 0.18)])
		var c: Color = col if r.randf() < 0.8 else cols[r.randi() % cols.size()]
		var tilt := Basis(Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)).normalized(), r.randf_range(0.0, 0.5))
		blooms[key].append([Transform3D(tilt * Basis(Vector3.UP, r.randf() * TAU).scaled(Vector3.ONE * r.randf_range(0.8, 1.3)),
				p + Vector3(0, 0.28 * hh, 0)), c])


static func trodden(m, p: Vector3) -> float:
	"""neben Wegen und auf Trampelpfaden ist das Gras niedergetreten: Höhen-Faktor 0.45 … 1"""
	if not an(m):
		return 1.0
	var q := Vector2(p.x, p.z)
	if m.gelaende != null:
		if m.gelaende.on_path(q, 0.5):
			return 0.45
		if m.gelaende.on_path(q, 1.1):
			return 0.7
	for ln in trampel(m):
		var d := Geometry2D.get_closest_point_to_segment(q, ln[0], ln[1]).distance_to(q)
		if d < 0.45:
			return 0.5
		if d < 0.9:
			return 0.75
	return 1.0


# ---- Trampelpfade zwischen den Plätzen (Zelt, Grill, Tisch, Tür des Wohnwagens, nächster Weg) -----------------------------
static var _tr_key := -1
static var _tr: Array = []


static func _spot(n: Node3D) -> Vector2:
	"""Mitte eines Test-Dings (Knoten am Ort, oder Knoten bei 0 mit Teilen am Ort)"""
	if n.position != Vector3.ZERO:
		return Vector2(n.position.x, n.position.z)
	var c := Vector3.ZERO
	var k := 0
	for ch in n.get_children():
		if ch is Node3D:
			c += (ch as Node3D).position
			k += 1
	return Vector2(c.x, c.z) / maxf(1.0, k)


static func trampel(m) -> Array:
	"""[[a, b], …] (x/z): kurze Stücke eines leicht gewundenen Trampelpfads; ohne Zufall (aus den Orten gerechnet), nichts
	daran ist ein Hindernis oder ändert, wo etwas steht"""
	var sc = m.get("scenes")
	if sc == null or sc.root == null:
		return []
	var key: int = sc.root.get_instance_id()
	if key == _tr_key:
		return _tr
	_tr_key = key
	_tr = []
	var pts := {}
	var tp: Dictionary = m.get("test_props") if m.get("test_props") != null else {}
	for nm in ["Zelt", "Grill", "Tisch"]:
		if tp.has(nm) and is_instance_valid(tp[nm]):
			var q := _spot(tp[nm])
			if nm == "Zelt":                                     # in front of the tent door
				var tn: Node3D = tp[nm]
				var fz: Vector3 = tn.transform.basis.z.normalized()
				q += Vector2(fz.x, fz.z) * 2.2
			pts[nm] = q
	var od = m.obj.get("door") if m.get("obj") != null else null
	if od is Vector3:
		pts["Tür"] = Vector2(od.x, od.z)
	var chain := []
	for nm in ["Tür", "Tisch", "Grill", "Zelt"]:
		if pts.has(nm):
			chain.append(pts[nm])
	var lines := []
	for i in range(chain.size() - 1):
		lines.append([chain[i], chain[i + 1]])
	if m.gelaende != null and not m.gelaende.paths.is_empty():
		for nm in ["Tür", "Zelt"]:                               # to the nearest path
			if not pts.has(nm):
				continue
			var best := Vector2.ZERO
			var bd := 1e9
			for pa in m.gelaende.paths:
				for v in (pa[0] as PackedVector2Array):
					var d: float = v.distance_to(pts[nm])
					if d < bd:
						bd = d
						best = v
			if bd < 25.0:
				lines.append([pts[nm], best])
	for ln in lines:                                             # gently winding, pieces of ~3 m
		var a: Vector2 = ln[0]
		var b: Vector2 = ln[1]
		var L := a.distance_to(b)
		if L < 1.5:
			continue
		var n := maxi(2, int(L / 3.0))
		var side := (b - a).normalized().orthogonal()
		var prev := a
		for k in range(1, n + 1):
			var u := float(k) / n
			var h := sin(u * PI * 2.0 + a.x * 0.7 + b.y * 0.3) * 0.5 * sin(u * PI)
			var q2 := a.lerp(b, u) + side * h
			_tr.append([prev, q2])
			prev = q2
	return _tr


static func boden(m, mat: ShaderMaterial) -> void:
	"""die grossen Böden (Weltkarten, Ferienpark, kompakt, Bergtal): gras_boden.gdshaderinc an / aus"""
	if mat == null:
		return
	if not an(m):
		mat.set_shader_parameter("p2", 0.0)
		return
	mat.set_shader_parameter("p2", 1.0)
	var t := "res://texturen/wiese_alp_01.jpg"
	if ResourceLoader.exists(t):
		mat.set_shader_parameter("p2_wiese", load(t))
	if m.get("wind_fx") != null and not m.wind_fx.blade_mats.has(mat):
		m.wind_fx.blade_mats.append(mat)                       # gusts: the same wave (wind_fx.gd)


# ---- Boden ---------------------------------------------------------------------------------------------------------------
static func ground(m) -> void:
	"""Boden-Shader: Paket 2 an / aus (gleiche Material-Instanz in allen Szenen: immer beide Fälle setzen)"""
	load("res://scripts/farbstimmung.gd").ensure(m, an(m))          # free view only: colour grading (farbstimmung.gd)
	var gm: ShaderMaterial = m.grass_mat
	if gm == null:
		return
	if not an(m):
		gm.set_shader_parameter("p2", 0.0)
		gm.set_shader_parameter("gust_amt", 0.0)
		gm.set_shader_parameter("pfad_n", 0)
		return
	gm.set_shader_parameter("p2", 1.0)
	gm.set_shader_parameter("fell_k", 1.0)
	var segs := PackedColorArray()
	var rads := PackedFloat32Array()
	if m.gelaende != null:
		for pa in m.gelaende.paths:
			var line: PackedVector2Array = pa[0]
			var step := maxi(1, int(line.size() / 7))            # ~7 pieces per path are enough for a worn edge
			var k := 0
			while k < line.size() - 1 and segs.size() < PFAD_MAX:
				var k2 := mini(k + step, line.size() - 1)
				segs.append(Color(line[k].x, line[k].y, line[k2].x, line[k2].y))
				rads.append(float(pa[1]))
				k = k2
	for ln in trampel(m):                                        # the trodden lines between the places
		if segs.size() >= PFAD_MAX:
			break
		segs.append(Color(ln[0].x, ln[0].y, ln[1].x, ln[1].y))
		rads.append(0.2)
	var n := segs.size()
	segs.resize(PFAD_MAX)
	rads.resize(PFAD_MAX)
	gm.set_shader_parameter("pfad", segs)
	gm.set_shader_parameter("pfad_r", rads)
	gm.set_shader_parameter("pfad_n", n)
