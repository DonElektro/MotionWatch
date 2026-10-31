extends RefCounted
## 3D-4.x «Gelände & Pflanzen» (Zweig real-gelaende, 31.10.2026): Pflanzen für alle Szenen – Gras, hohes Gras, Blumen,
## Büsche, Hecken und Bäume verschiedener Arten und Grössen. Alles steht auf dem Boden (m.ground_y, auch mit Hügeln aus
## gelaende.gd), alles Feste hat einen Zwilling im Wärmebild und eine Hindernis-Fläche mit Höhe (Besucher gehen aussen herum,
## die Sichtlinie des Spiels und die Wahrheit «verdeckt» kennen sie).
##
## Benutzung (in einer Szene, sc = scenes.gd, das gerade baut):
##   const Veg = preload("res://scripts/vegetation.gd")
##   Veg.grass(sc, 6000, 3.0, 45.0, keep_clear, {"tall": 0.12, "flowers": 0.25})   # Gras-Büschel (MultiMesh in 20-m-Feldern)
##   Veg.flowers(sc, 900, 4.0, 40.0, keep_clear)                                   # Blumen (Stiel + Blüte)
##   Veg.bush(sc, sc.root, p, "rund" | "hasel" | "bluehend" | "beeren" | "jung", grösse)
##   Veg.hedge(sc, sc.root, Vector2(a), Vector2(b), höhe, dicke, "liguster" | "buche" | "thuja")   # dicht: verdeckt wirklich
##   Veg.tree(sc, sc.root, p, "fichte" | "laub" | "birke" | "kiefer" | "eiche" | "obst" | "jung", grösse)
##   Veg.scatter(sc, n, dmin, dmax, ["bush:rund", "tree:birke", …], keep_clear)  # zufällig verteilt, mit Abstand zu Hindernissen
##   Veg.keep_clear_default(sc, extra)                                             # nicht auf Wege, Strasse, Hindernisse
## keep_clear(p: Vector3) -> bool (true = hier nichts). p.y wird von den Funktionen selbst auf den Boden gesetzt.
##
## Effizient: Gras und Blumen sind MultiMesh in Feldern zu 20 m (jedes Feld wird ab 55 m nicht mehr gezeichnet, Lite 35 m),
## gehören zur Gruppe «meadow» (Schalter «Gras und Blumen», Lite dünnt sie auf 35 % aus, main._lite_scene). Hecken: ein
## Kern aus Kästen + die Blätter-Buckel als ein MultiMesh pro Hecke. Was verdeckt (Hecken, Büsche, Bäume), ist in Lite
## **gleich** – sonst sähe MoveEye in Lite andere Dinge als in Normal.

const Quality = preload("res://scripts/quality.gd")
const CELL := 20.0
const GRASS_FAR := 55.0
const GRASS_FAR_LITE := 35.0

static var _clump: ArrayMesh = null
static var _tall: ArrayMesh = null
static var _stem: ArrayMesh = null
static var _bloom: ArrayMesh = null
static var _lump: SphereMesh = null


# ---- meshes (built once) ---------------------------------------------------------------------------------------------
static func _blades(count: int, hmin: float, hmax: float, wbase: float, seed_: int) -> ArrayMesh:
	"""ein Büschel aus schmalen, leicht gebogenen Halmen (2 Dreiecke pro Halm)"""
	var r := RandomNumberGenerator.new()
	r.seed = seed_
	var v := PackedVector3Array()
	var nn := PackedVector3Array()
	for i in range(count):
		var a := r.randf() * TAU
		var hh := r.randf_range(hmin, hmax)
		var off := Vector3(r.randf_range(-0.07, 0.07), 0, r.randf_range(-0.07, 0.07))
		var side := Vector3(cos(a), 0, sin(a)) * wbase * 0.5
		var lean := Vector3(-sin(a), 0, cos(a)) * r.randf_range(0.04, 0.16) * hh / 0.4
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
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return m


static func _bloom_mesh() -> ArrayMesh:
	"""Blüte: zwei gekreuzte kleine Vierecke + ein flaches oben (sieht aus jeder Richtung wie ein Punkt aus)"""
	var v := PackedVector3Array()
	var nn := PackedVector3Array()
	var s := 0.035
	var quads := [[Vector3(-s, -s, 0), Vector3(s, -s, 0), Vector3(s, s, 0), Vector3(-s, s, 0)],
			[Vector3(0, -s, -s), Vector3(0, -s, s), Vector3(0, s, s), Vector3(0, s, -s)],
			[Vector3(-s, 0, -s), Vector3(s, 0, -s), Vector3(s, 0, s), Vector3(-s, 0, s)]]
	for q in quads:
		for k in [0, 1, 2, 0, 2, 3]:
			v.append(q[k])
			nn.append(Vector3.UP)
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nn
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return m


static func _meshes() -> void:
	if _clump == null:
		_clump = _blades(6, 0.16, 0.36, 0.05, 5)
		_tall = _blades(8, 0.5, 0.95, 0.05, 9)
		_stem = _blades(1, 0.22, 0.34, 0.012, 13)
		_bloom = _bloom_mesh()
		_lump = SphereMesh.new()
		_lump.radius = 0.5
		_lump.height = 0.85
		_lump.radial_segments = 8
		_lump.rings = 4


static func blade_mat(sc, stiff := 1.0) -> ShaderMaterial:
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/gras_halme.gdshader")
	gm.set_shader_parameter("noise_tex", sc.m.noise_tex)
	gm.set_shader_parameter("stiff", stiff)
	if sc.m.gelaende != null:
		sc.m.gelaende.veg_mats.append(gm)              # wind + cloud shadows (gelaende._process)
	sc.m.ground_mats.append(gm)                        # snow (main._update_sky)
	return gm


# ---- placing helpers -------------------------------------------------------------------------------------------------
static func ground(sc, p: Vector3) -> Vector3:
	return Vector3(p.x, sc.m.ground_y(p.x, p.z), p.z)


static func keep_clear_default(sc, extra := Callable()) -> Callable:
	"""nicht auf Wege (gelaende.paths), nicht auf die Strasse der Szene, nicht in Hindernisse, nicht direkt beim Kopf"""
	return func(p: Vector3) -> bool:
		var q := Vector2(p.x, p.z)
		if q.length() < 2.5:
			return true
		if sc.m.gelaende != null and sc.m.gelaende.on_path(q, 0.15):
			return true
		if sc.data.has("road_z") and absf(p.z - (float(sc.data["road_z"]) - 1.2)) < 3.0:
			return true
		if extra.is_valid() and extra.call(p):
			return true
		return false


static func _free_of_obstacles(sc, p: Vector3, gap: float) -> bool:
	for o in sc.m._ob_near(Vector2(p.x, p.z)):
		if float(sc.m._ob_closest(o, Vector2(p.x, p.z))[1]) < gap:
			return false
	return true


static func _rand_pos(sc, dmin: float, dmax: float) -> Vector3:
	"""zufälliger Punkt im Ring dmin … dmax um den Kopf, nach Fläche verteilt (aussen nicht dünner)"""
	var d = sqrt(lerpf(dmin * dmin, dmax * dmax, sc.rng.randf()))
	return sc.m.pos_of(sc.rng.randf_range(-180, 180), d)


# ---- grass and flowers -----------------------------------------------------------------------------------------------
static func _cells_to_nodes(sc, cells: Dictionary, mesh: Mesh, mat: Material, far: float) -> int:
	var made := 0
	for key in cells:
		var list: Array = cells[key]
		if list.is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = mesh
		mm.instance_count = list.size()
		for i in range(list.size()):
			mm.set_instance_transform(i, list[i][0])
			mm.set_instance_color(i, list[i][1])
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.material_override = mat
		mi.layers = 1
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visibility_range_end = far
		mi.visibility_range_end_margin = 6.0
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		mi.add_to_group("meadow")
		mi.visible = sc.m.meadow_on
		sc.root.add_child(mi)
		made += list.size()
	return made


static func _cell_key(p: Vector3) -> Vector2i:
	return Vector2i(int(floor(p.x / CELL)), int(floor(p.z / CELL)))


static func grass(sc, n: int, dmin: float, dmax: float, keep_clear := Callable(), o := {}) -> int:
	"""n Gras-Büschel (kurz) + ein Teil hohes Gras («tall», Anteil) – MultiMesh in Feldern zu 20 m; gibt die Anzahl zurück"""
	_meshes()
	var far: float = GRASS_FAR_LITE if Quality.lite() else GRASS_FAR
	var tall_share := float(o.get("tall", 0.1))
	var greens := [Color(0.3, 0.5, 0.17), Color(0.36, 0.54, 0.2), Color(0.26, 0.44, 0.15), Color(0.42, 0.52, 0.22), Color(0.5, 0.5, 0.26)]
	var short_cells := {}
	var tall_cells := {}
	var tall_spots: Array = o.get("tall_spots", [])        # [Vector2 Mitte, Radius]: dort vor allem hohes Gras
	for i in range(n):
		var p: Vector3 = _rand_pos(sc, dmin, dmax)
		if keep_clear.is_valid() and keep_clear.call(p):
			continue
		var tall = sc.rng.randf() < tall_share
		for ts in tall_spots:
			if Vector2(p.x, p.z).distance_to(ts[0]) < float(ts[1]):
				tall = sc.rng.randf() < 0.8
		p = ground(sc, p)
		var nrm: Vector3 = sc.m.gelaende.normal_at(p.x, p.z) if sc.m.gelaende != null and sc.m.gelaende.on else Vector3.UP
		var b = Basis(Vector3.UP, sc.rng.randf() * TAU)
		if nrm.y < 0.999:                                    # lean with the slope a little
			b = Basis(Vector3.UP.cross(nrm).normalized(), acos(clampf(nrm.y, -1.0, 1.0)) * 0.6) * b
		var sz = sc.rng.randf_range(0.75, 1.35)
		var col: Color = greens[sc.rng.randi() % greens.size()].lerp(Color(0.62, 0.58, 0.32), 0.35 if tall and sc.rng.randf() < 0.4 else 0.0)
		var t = Transform3D(b.scaled(Vector3(sz, sz * sc.rng.randf_range(0.85, 1.2), sz)), p - Vector3(0, 0.01, 0))
		var key := _cell_key(p)
		var cells: Dictionary = tall_cells if tall else short_cells
		if not cells.has(key):
			cells[key] = []
		cells[key].append([t, col])
	var mat := blade_mat(sc, 1.0)
	return _cells_to_nodes(sc, short_cells, _clump, mat, far) + _cells_to_nodes(sc, tall_cells, _tall, mat, far + 15.0)


static func flowers(sc, n: int, dmin: float, dmax: float, keep_clear := Callable(), cols := []) -> int:
	"""n Blumen: grüner Stiel + farbige Blüte (Wiesen-Mischung: weiss, gelb, rosa, violett, orange)"""
	_meshes()
	var far: float = GRASS_FAR_LITE if Quality.lite() else GRASS_FAR
	if cols.is_empty():
		cols = [Color(0.96, 0.96, 0.94), Color(0.96, 0.84, 0.18), Color(0.88, 0.36, 0.62), Color(0.58, 0.46, 0.9), Color(0.96, 0.52, 0.16), Color(0.96, 0.96, 0.94)]
	var stems := {}
	var blooms := {}
	var patch_c := Vector3.ZERO
	for i in range(n):
		var p: Vector3
		if i % 6 == 0 or patch_c == Vector3.ZERO:              # flowers grow in patches
			patch_c = _rand_pos(sc, dmin, dmax)
			p = patch_c
		else:
			p = patch_c + Vector3(sc.rng.randf_range(-1.6, 1.6), 0, sc.rng.randf_range(-1.6, 1.6))
		if keep_clear.is_valid() and keep_clear.call(p):
			continue
		p = ground(sc, p)
		var hh = sc.rng.randf_range(0.8, 1.3)
		var b = Basis(Vector3.UP, sc.rng.randf() * TAU).scaled(Vector3(1, hh, 1))
		var key := _cell_key(p)
		if not stems.has(key):
			stems[key] = []
			blooms[key] = []
		stems[key].append([Transform3D(b, p), Color(0.3, 0.48, 0.18)])
		var c: Color = cols[sc.rng.randi() % cols.size()]
		blooms[key].append([Transform3D(Basis(Vector3.UP, sc.rng.randf() * TAU).scaled(Vector3.ONE * sc.rng.randf_range(0.8, 1.4)),
				p + Vector3(0, 0.28 * hh, 0)), c])
	var sm := blade_mat(sc, 1.6)
	sm.set_shader_parameter("tint_amt", 0.0)              # flowers keep their colours
	_cells_to_nodes(sc, stems, _stem, sm, far)
	return _cells_to_nodes(sc, blooms, _bloom, sm, far)


# ---- bushes ------------------------------------------------------------------------------------------------------------
static func bush(sc, parent: Node3D, p: Vector3, kind := "rund", s := 1.0) -> Node3D:
	"""ein Busch; kind: rund (1.2–1.8 m), hasel (hoch und locker, 2.5 m), bluehend (mit Blüten), beeren, jung (0.6 m)"""
	p = ground(sc, p)
	var n: Node3D = sc.node(parent, p, sc.rng.randf() * TAU)
	var r_ob := 0.9 * s
	var ht := 1.5 * s
	match kind:
		"hasel":                                               # several stems, the leaves up high (you see legs below!)
			var fm: ShaderMaterial = sc.foliage(sc.rng.randi_range(0, 5) + 6)
			for k in range(sc.rng.randi_range(5, 7)):
				var a = sc.rng.randf() * TAU
				var tilt = sc.rng.randf_range(0.1, 0.35)
				sc.put(n, sc.cyl(0.02, 0.04, 2.4 * s, 5), Vector3(cos(a) * 0.15, 1.1 * s, sin(a) * 0.15), Color(0.42, 0.33, 0.24), "tree",
						Vector3(sin(a) * tilt, 0, -cos(a) * tilt))
			for k in range(sc.rng.randi_range(6, 8)):
				var r = sc.rng.randf_range(0.5, 0.8) * s
				sc.put(n, sc.sph(r, r * 1.5), Vector3(sc.rng.randf_range(-0.9, 0.9) * s, sc.rng.randf_range(1.2, 2.3) * s, sc.rng.randf_range(-0.9, 0.9) * s), fm, "tree")
			r_ob = 1.1 * s
			ht = 2.5 * s
		"jung":
			var fm2: ShaderMaterial = sc.foliage(sc.rng.randi_range(0, 5))
			for k in range(3):
				var r2 = sc.rng.randf_range(0.25, 0.4) * s
				sc.put(n, sc.sph(r2, r2 * 1.5), Vector3(sc.rng.randf_range(-0.3, 0.3) * s, r2 * 0.8, sc.rng.randf_range(-0.3, 0.3) * s), fm2, "tree")
			r_ob = 0.4 * s
			ht = 0.6 * s
		_:                                                     # rund / bluehend / beeren: dense, down to the ground
			var fm3: ShaderMaterial = sc.foliage(sc.rng.randi_range(0, 5))
			sc.put(n, sc.sph(0.75 * s, 1.2 * s), Vector3(0, 0.55 * s, 0), fm3, "tree")       # dense core (nothing shows through)
			for k in range(sc.rng.randi_range(4, 6)):
				var r3 = sc.rng.randf_range(0.5, 0.8) * s
				sc.put(n, sc.sph(r3, r3 * 1.6), Vector3(sc.rng.randf_range(-0.6, 0.6) * s, r3 * 0.75 + sc.rng.randf_range(0.0, 0.35) * s, sc.rng.randf_range(-0.6, 0.6) * s), fm3, "tree")
			if kind in ["bluehend", "beeren"]:
				var bc: Color = [Color(0.95, 0.75, 0.85), Color(0.97, 0.97, 0.95), Color(0.75, 0.25, 0.55)][sc.rng.randi() % 3] if kind == "bluehend" else Color(0.6, 0.06, 0.1)
				var dot = sc.sph(0.05 if kind == "bluehend" else 0.035)
				var dm: StandardMaterial3D = sc.m.mat(bc)
				for k in range(18):
					var a2 = sc.rng.randf() * TAU
					var el = sc.rng.randf_range(-0.2, 1.2)
					var rr := 0.95 * s
					sc.put(n, dot, Vector3(cos(a2) * cos(el) * rr, 0.75 * s + sin(el) * rr * 0.75, sin(a2) * cos(el) * rr), dm, "tree")
	sc.m.add_obstacle(p, r_ob)
	sc.m.set_obstacle_height(ht)
	return n


# ---- hedges ------------------------------------------------------------------------------------------------------------
static func hedge(sc, parent: Node3D, a: Vector2, b: Vector2, h := 1.9, thick := 0.9, kind := "liguster") -> Node3D:
	"""eine dichte Hecke von a nach b (folgt dem Gelände). Ein Kern aus Kästen (keine Lücke, verdeckt im Bild und im
	Wärmebild) + Blätter-Buckel als ein MultiMesh; Hindernis-Fläche mit Höhe h (Sichtlinie, Besucher gehen aussen herum)"""
	_meshes()
	var d := b - a
	var L := d.length()
	if L < 0.3:
		return null
	var rot_y := atan2(-d.y, d.x)
	var mid2 := (a + b) * 0.5
	var n: Node3D = sc.node(parent, Vector3(mid2.x, 0, mid2.y), rot_y)
	var fm: ShaderMaterial
	match kind:
		"thuja":
			fm = sc.foliage(4)                                    # dark, blue-green
		"buche":
			fm = sc.foliage(9)                                    # broadleaf (turns brown in autumn)
		_:
			fm = sc.foliage(2)
	var segs := maxi(1, int(ceil(L / 2.0)))
	var seg_l := L / segs
	for k in range(segs):                                         # core: one box per 2 m, at the height of the ground there
		var lx := -L * 0.5 + (k + 0.5) * seg_l
		var w := a + d * ((k + 0.5) / segs)
		var gy: float = sc.m.ground_y(w.x, w.y)
		var hk = h * sc.rng.randf_range(0.97, 1.03)
		sc.put(n, sc.m.box(seg_l + 0.05, hk + 0.3, thick * 0.82), Vector3(lx, gy - 0.3 + (hk + 0.3) * 0.5, 0), fm, "tree")
	var mm := MultiMesh.new()                                     # leafy lumps on both sides and on top
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var lumps: Array = []
	var cnt := int(ceil(L / 0.55))
	for k in range(cnt):
		var lx2 = -L * 0.5 + (k + sc.rng.randf()) * (L / cnt)
		var w2 := a + d * clampf((lx2 + L * 0.5) / L, 0.0, 1.0)
		var gy2: float = sc.m.ground_y(w2.x, w2.y)
		for side in [-1.0, 1.0]:
			for row in range(2):
				var y = gy2 + (0.35 + row * 0.5 + sc.rng.randf_range(0.0, 0.25)) * h / 1.9 * 1.6
				var sz = sc.rng.randf_range(0.45, 0.65) * thick / 0.9
				lumps.append(Transform3D(Basis(Vector3.UP, sc.rng.randf() * TAU).scaled(Vector3(sz, sz, sz)), Vector3(lx2, y, side * thick * 0.36)))
		var szt = sc.rng.randf_range(0.5, 0.7) * thick / 0.9
		lumps.append(Transform3D(Basis().scaled(Vector3(szt * 1.2, szt * 0.6, szt)), Vector3(lx2, gy2 + h - 0.05 + sc.rng.randf_range(-0.04, 0.08), sc.rng.randf_range(-0.1, 0.1))))
	mm.mesh = _lump
	mm.instance_count = lumps.size()
	for i in range(lumps.size()):
		mm.set_instance_transform(i, lumps[i])
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = fm
	mi.layers = 1
	n.add_child(mi)
	var th := MultiMeshInstance3D.new()                           # the twin for the thermal camera
	th.multimesh = mm
	th.material_override = sc.m.tmat("tree")
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.add_child(th)
	sc.m.add_obstacle_box(Vector3(mid2.x, 0, mid2.y), L + 0.2, thick + 0.15, rot_y)
	sc.m.set_obstacle_height(h)
	n.set_meta("hedge", [a, b, h])
	return n


# ---- trees -------------------------------------------------------------------------------------------------------------
static func tree(sc, parent: Node3D, p: Vector3, kind := "laub", s := 1.0) -> Node3D:
	"""ein Baum; fichte und laub wie scenes.tree, dazu birke, kiefer, eiche, obst, jung (mit Pfahl)"""
	p = ground(sc, p)
	if kind == "fichte" or kind == "laub":
		sc.tree(parent, p, s, 1 if kind == "fichte" else 0)
		return null
	var tr: Node3D = sc.node(parent, p, sc.rng.randf() * TAU)
	tr.scale = Vector3.ONE * s
	var crown_r := 1.5
	var crown_y := 3.0
	var trunk_r := 0.3
	match kind:
		"birke":                                                  # white trunk, small airy crown, light green
			var bark := Color(0.86, 0.85, 0.8)
			sc.put(tr, sc.cyl(0.06, 0.13, 6.5, 8), Vector3(0, 3.25, 0), bark, "tree")
			for k in range(5):                                    # black marks on the bark
				sc.put(tr, sc.cyl(0.115 - k * 0.01, 0.12 - k * 0.01, 0.06, 8), Vector3(0, 0.8 + k * 1.1, 0), Color(0.12, 0.12, 0.12), "tree")
			var fm: ShaderMaterial = sc.foliage(9)
			for k in range(sc.rng.randi_range(6, 8)):
				var r = sc.rng.randf_range(0.55, 0.9)
				sc.put(tr, sc.sph(r, r * 1.9), Vector3(sc.rng.randf_range(-0.8, 0.8), sc.rng.randf_range(4.0, 7.0), sc.rng.randf_range(-0.8, 0.8)), fm, "tree")
			crown_r = 1.3
			crown_y = 3.6
			trunk_r = 0.2
		"kiefer":                                                 # pine: long bare reddish trunk, flat crown on top
			var bark2 := Color(0.5, 0.32, 0.22)
			sc.put(tr, sc.cyl(0.12, 0.25, 9.0, 8), Vector3(0, 4.5, 0), bark2, "tree", Vector3(sc.rng.randf_range(-0.04, 0.04), 0, sc.rng.randf_range(-0.04, 0.04)))
			var fm2: ShaderMaterial = sc.foliage(4)
			for k in range(sc.rng.randi_range(4, 6)):
				var a = sc.rng.randf() * TAU
				var r2 = sc.rng.randf_range(0.9, 1.4)
				sc.put(tr, sc.sph(r2, r2 * 0.8), Vector3(cos(a) * sc.rng.randf_range(0.3, 1.3), sc.rng.randf_range(8.0, 9.6), sin(a) * sc.rng.randf_range(0.3, 1.3)), fm2, "tree")
			crown_r = 2.0
			crown_y = 7.5
			trunk_r = 0.3
		"eiche":                                                  # oak: thick short trunk, wide crown
			var bark3 := Color(0.32, 0.26, 0.2)
			sc.put(tr, sc.cyl(0.25, 0.42, 3.2, 10), Vector3(0, 1.6, 0), bark3, "tree")
			for b in range(3):
				var a3 = sc.rng.randf() * TAU
				sc.put(tr, sc.cyl(0.08, 0.16, 2.6, 6), Vector3(cos(a3) * 0.7, 3.6, sin(a3) * 0.7), bark3, "tree", Vector3(sin(a3) * 0.85, 0, -cos(a3) * 0.85))
			var fm3: ShaderMaterial = sc.foliage(sc.rng.randi_range(6, 11))
			for k in range(sc.rng.randi_range(7, 9)):
				var r3 = sc.rng.randf_range(1.3, 2.0)
				sc.put(tr, sc.sph(r3, r3 * 1.4), Vector3(sc.rng.randf_range(-2.0, 2.0), sc.rng.randf_range(4.3, 6.0), sc.rng.randf_range(-2.0, 2.0)), fm3, "tree")
			crown_r = 3.2
			crown_y = 3.4
			trunk_r = 0.45
		"obst":                                                   # fruit tree: short trunk, round low crown, red apples
			var bark4 := Color(0.36, 0.28, 0.2)
			sc.put(tr, sc.cyl(0.08, 0.14, 1.8, 8), Vector3(0, 0.9, 0), bark4, "tree")
			var fm4: ShaderMaterial = sc.foliage(sc.rng.randi_range(6, 11))
			for k in range(5):
				var r4 = sc.rng.randf_range(0.8, 1.1)
				sc.put(tr, sc.sph(r4, r4 * 1.5), Vector3(sc.rng.randf_range(-0.7, 0.7), sc.rng.randf_range(2.2, 2.9), sc.rng.randf_range(-0.7, 0.7)), fm4, "tree")
			var apple = sc.sph(0.05)
			var am: StandardMaterial3D = sc.m.mat(Color(0.75, 0.12, 0.08))
			for k in range(14):
				var a4 = sc.rng.randf() * TAU
				sc.put(tr, apple, Vector3(cos(a4) * 1.25, sc.rng.randf_range(1.9, 3.0), sin(a4) * 1.25), am, "tree")
			crown_r = 1.6
			crown_y = 1.6
			trunk_r = 0.2
		_:                                                        # «jung»: a young tree with a stake
			sc.put(tr, sc.cyl(0.03, 0.05, 2.4, 6), Vector3(0, 1.2, 0), Color(0.4, 0.32, 0.24), "tree")
			sc.put(tr, sc.cyl(0.025, 0.025, 1.6, 5), Vector3(0.12, 0.8, 0), Color(0.6, 0.48, 0.32), "tree")
			var fm5: ShaderMaterial = sc.foliage(sc.rng.randi_range(6, 11))
			for k in range(3):
				var r5 = sc.rng.randf_range(0.35, 0.55)
				sc.put(tr, sc.sph(r5, r5 * 1.5), Vector3(sc.rng.randf_range(-0.3, 0.3), sc.rng.randf_range(2.0, 2.6), sc.rng.randf_range(-0.3, 0.3)), fm5, "tree")
			crown_r = 0.7
			crown_y = 1.8
			trunk_r = 0.1
	if parent == sc.root or parent.get_parent() == sc.root:
		sc.m.add_obstacle(p, trunk_r * s)
	sc.m.tree_spots.append([Vector2(p.x, p.z), crown_r * s, crown_y * s])
	return tr


# ---- scatter ------------------------------------------------------------------------------------------------------------
static func scatter(sc, n: int, dmin: float, dmax: float, kinds: Array, keep_clear := Callable(), gap := 2.0) -> int:
	"""n Pflanzen zufällig zwischen dmin und dmax: kinds z. B. ["bush:rund", "bush:hasel", "tree:birke:0.9-1.3"]"""
	var made := 0
	var tries := 0
	while made < n and tries < n * 10:
		tries += 1
		var p: Vector3 = _rand_pos(sc, dmin, dmax)
		if keep_clear.is_valid() and keep_clear.call(p):
			continue
		if not _free_of_obstacles(sc, p, gap):
			continue
		var parts: PackedStringArray = str(kinds[sc.rng.randi() % kinds.size()]).split(":")
		var s = sc.rng.randf_range(0.85, 1.2)
		if parts.size() > 2 and parts[2].contains("-"):
			s = sc.rng.randf_range(float(parts[2].get_slice("-", 0)), float(parts[2].get_slice("-", 1)))
		if parts[0] == "tree":
			tree(sc, sc.root, p, parts[1] if parts.size() > 1 else "laub", s)
		else:
			bush(sc, sc.root, p, parts[1] if parts.size() > 1 else "rund", s)
		made += 1
	return made
