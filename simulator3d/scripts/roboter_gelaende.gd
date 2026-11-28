extends RefCounted
## Roboter-Labor: der Boden mit Raster und die Prüfstrecken (Besitzer 22.11.2026: Rampe, Stufe, Kies, Graben).
## Alles in echten Metern (der Roboter misst bei Massstab 0.10 rund 1.3 m). Start in der Mitte (Fahrspur z = 0, Blick +X);
## jede Prüfstrecke hat ihre eigene Spur parallel dazu, sie beginnt bei x = 2.5 (Ost) bzw. x = −8 (West):
##   Rampe 15° (z = +3) · Stufe 6 cm (z = −3) · Kies (z = +6) · Graben 20 cm breit, 15 cm tief (z = −6, quer über die Spur).
## Gang-KI (28.11.2026, Besitzer 14:36: mehrere Grössen): Stufe 10 cm (z = +9) · Lücke 30 cm ohne Boden (z = −9) · West:
##   Treppe 3 × 4 cm (z = +3) · Lücke 15 cm (z = −3) · Rohr Ø 6 cm (z = +6) · Balken 16 cm über dem Boden (drunter durch,
##   z = −6) · Geröll 3 – 6 cm (z = +9) · Rohr Ø 10 cm (z = −9).
## Ebene 1 (LAYER_GELAENDE), der Roboter stösst nur daran.

const T = preload("res://scripts/i18n.gd")
const START_X := 2.5
const WEST_X := -8.0
const SPUREN := {"start": 0.0, "rampe": 3.0, "stufe": -3.0, "kies": 6.0, "graben": -6.0,
		"stufe_hoch": 9.0, "luecke_breit": -9.0, "treppe": 3.0, "luecke": -3.0, "rohr": 6.0, "balken": -6.0,
		"geroell": 9.0, "rohr_dick": -9.0}
const WEST := ["treppe", "luecke", "rohr", "balken", "geroell", "rohr_dick"]
const RAMPE_GRAD := 15.0
const STUFE_H := 0.06
const STUFE_HOCH_H := 0.10
const GRABEN_B := 0.20
const GRABEN_T := 0.15
const LUECKE_B := 0.15
const LUECKE_BREIT_B := 0.30
const TREPPE_N := 3
const TREPPE_H := 0.04
const TREPPE_A := 0.25           # Auftritt (m)
const ROHR_D := 0.06
const ROHR_DICK_D := 0.10
const BALKEN_H := 0.16           # lichte Höhe unter dem Balken
const BALKEN_D := 0.05
const HINDERNIS_AB := 0.5        # Graben, Lücke, Rohr, Balken: so weit nach dem Anfang der Spur
# Gelände-Test: geschafft, wenn das hinterste Segment (im Ring: die Ringmitte) diese x-Lage erreicht
const ENDE := {"rampe": START_X + 3.9, "stufe": START_X + 0.25, "kies": START_X + 2.6, "graben": START_X + 0.5 + GRABEN_B + 0.15,
		"stufe_hoch": START_X + 0.25, "luecke_breit": START_X + 0.5 + LUECKE_BREIT_B + 0.15,
		"treppe": WEST_X + TREPPE_N * TREPPE_A + 0.1, "luecke": WEST_X + 0.5 + LUECKE_B + 0.15, "rohr": WEST_X + 0.5 + ROHR_D + 0.15,
		"balken": WEST_X + 0.5 + BALKEN_D + 0.15, "geroell": WEST_X + 2.6, "rohr_dick": WEST_X + 0.5 + ROHR_DICK_D + 0.15}
const NAMEN := [["rampe", "Rampe 15°"], ["stufe", "Stufe 6 cm"], ["kies", "Kies"], ["graben", "Graben 20 cm"],
		["stufe_hoch", "Stufe 10 cm"], ["treppe", "Treppe 3 × 4 cm"], ["luecke", "Lücke 15 cm"], ["luecke_breit", "Lücke 30 cm"],
		["rohr", "Rohr 6 cm"], ["rohr_dick", "Rohr 10 cm"], ["balken", "Balken 16 cm hoch"], ["geroell", "Geröll"]]
# what the lane holds (for tests and the KI): art + measures (m, °) - the same words as roboter_ki_gang.gd sehen()
const SOLL := {"rampe": {"art": "rampe", "hoehe": 0.375, "neigung": 15.0}, "stufe": {"art": "stufe", "hoehe": STUFE_H},
		"kies": {"art": "geroell"}, "graben": {"art": "graben", "breite": GRABEN_B, "tiefe": GRABEN_T},
		"stufe_hoch": {"art": "stufe", "hoehe": STUFE_HOCH_H}, "luecke_breit": {"art": "luecke", "breite": LUECKE_BREIT_B},
		"treppe": {"art": "treppe", "hoehe": TREPPE_N * TREPPE_H, "stufen": TREPPE_N}, "luecke": {"art": "luecke", "breite": LUECKE_B},
		"rohr": {"art": "rohr", "hoehe": ROHR_D, "breite": ROHR_D}, "rohr_dick": {"art": "rohr", "hoehe": ROHR_DICK_D, "breite": ROHR_DICK_D},
		"balken": {"art": "balken", "hoehe": BALKEN_H}, "geroell": {"art": "geroell"}}


static func lane_x(k: String) -> float:
	"""where the lane begins (x)"""
	return WEST_X if k in WEST else START_X


const GRID_SHADER := """
shader_type spatial;
uniform vec3 base : source_color = vec3(0.40, 0.42, 0.45);
varying vec3 wp;
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float lines(vec2 g) {
	vec2 f = abs(fract(g - 0.5) - 0.5) / max(fwidth(g), vec2(1e-4));
	return 1.0 - min(min(f.x, f.y), 1.0);
}
void fragment() {
	float l1 = lines(wp.xz * 10.0);
	float l2 = lines(wp.xz);
	ALBEDO = base * (1.0 - 0.10 * l1 - 0.38 * l2);
	ROUGHNESS = 0.92;
}
"""


static func build(world: Node3D) -> Dictionary:
	"""makes floor, ramp, step, gravel and ditch under «world»; returns {name: start Transform3D of its lane}"""
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = GRID_SHADER
	mat.shader = sh
	var z := 0.0
	# floor (top at y = 0) with holes: the ditch (with a bottom) and the two gaps (none: the ray finds nothing)
	var holes := []
	for k in ["graben", "luecke_breit", "luecke"]:
		var hx := lane_x(k) + HINDERNIS_AB
		var hb: float = {"graben": GRABEN_B, "luecke_breit": LUECKE_BREIT_B, "luecke": LUECKE_B}[k]
		holes.append(Rect2(hx, float(SPUREN[k]) - 1.0, hb, 2.0))
	_floor(world, Rect2(-10, -10, 20, 20), holes, mat)
	var dx0 := START_X + HINDERNIS_AB
	var gz := float(SPUREN["graben"])
	_box(world, Vector3(dx0, -0.5, gz - 1.0), Vector3(dx0 + GRABEN_B, -GRABEN_T, gz + 1.0), _plain(Color("#6d5a45")), 1.0, "grabensohle")
	var stone_col := _plain(Color("#8f8a80"))
	# a higher step
	z = float(SPUREN["stufe_hoch"])
	_box(world, Vector3(START_X, 0.0, z - 0.8), Vector3(START_X + 2.5, STUFE_HOCH_H, z + 0.8), stone_col, 1.0, "stufe_hoch")
	# stairs: TREPPE_N steps up, then the top
	z = float(SPUREN["treppe"])
	for i in range(TREPPE_N):
		var x0 := WEST_X + i * TREPPE_A
		_box(world, Vector3(x0, 0.0, z - 0.8), Vector3(WEST_X + TREPPE_N * TREPPE_A + 1.2, (i + 1) * TREPPE_H, z + 0.8), stone_col, 1.0, "treppe_%d" % i)
	# pipes lying across the lane
	for k in ["rohr", "rohr_dick"]:
		var d: float = ROHR_D if k == "rohr" else ROHR_DICK_D
		_pipe(world, Vector3(WEST_X + HINDERNIS_AB + d * 0.5, d * 0.5, float(SPUREN[k])), d * 0.5, 1.6, k)
	# beam above the lane on two posts (crawl under it)
	z = float(SPUREN["balken"])
	var bx := WEST_X + HINDERNIS_AB
	var wood := _plain(Color("#8a6a48"))
	_box(world, Vector3(bx, BALKEN_H, z - 0.9), Vector3(bx + BALKEN_D, BALKEN_H + 0.04, z + 0.9), wood, 1.0, "balken")
	for sz in [-1.0, 1.0]:
		_box(world, Vector3(bx, 0.0, z + sz * 0.9 - 0.03), Vector3(bx + BALKEN_D, BALKEN_H, z + sz * 0.9 + 0.03), wood, 1.0, "balken_pfosten")
	# rubble: bigger stones than the gravel
	_stones(world, "geroell", WEST_X, float(SPUREN["geroell"]), 140, 0.015, 0.03, 0.6, 2811)
	# step
	z = float(SPUREN["stufe"])
	_box(world, Vector3(START_X, 0.0, z - 0.8), Vector3(START_X + 2.5, STUFE_H, z + 0.8), _plain(Color("#8f8a80")), 1.0, "stufe")
	# ramp up 15°, plateau, down again
	z = float(SPUREN["rampe"])
	var ln := 1.4
	var rise := ln * tan(deg_to_rad(RAMPE_GRAD))
	_slab(world, Vector3(START_X, 0, z), ln, rise, 1.6, false)
	_box(world, Vector3(START_X + ln, 0.0, z - 0.8), Vector3(START_X + ln + 1.0, rise, z + 0.8), _plain(Color("#8f8a80")), 1.0, "rampe_oben")
	_slab(world, Vector3(START_X + ln + 1.0, 0, z), ln, rise, 1.6, true)
	# gravel: one static body with many small stones
	_stones(world, "kies", START_X, float(SPUREN["kies"]), 520, 0.012, 0.03, 0.35, 2211)
	# signs
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["rampe"]), T.t("Rampe %d°") % int(RAMPE_GRAD))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["stufe"]), T.t("Stufe %d cm") % int(round(STUFE_H * 100)))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["kies"]), T.t("Kies"))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["graben"]), T.t("Graben %d cm") % int(round(GRABEN_B * 100)))
	for nm in NAMEN.slice(4):
		_sign(world, Vector3(lane_x(nm[0]) - 0.3, 0.45, SPUREN[nm[0]]), T.t(nm[1]))
	var out := {}
	for k in SPUREN:
		out[k] = Transform3D(Basis(), Vector3(0.6 if k == "start" else lane_x(k) - 0.35, 0.0, float(SPUREN[k])))
	return out


static func _floor(world: Node3D, area: Rect2, holes: Array, mat: Material) -> void:
	"""the floor slab (top y = 0, 0.5 m thick) over «area» without the «holes» (Rect2 in x / z): split in bands along z"""
	var zs := [area.position.y, area.end.y]
	for h in holes:
		zs.append((h as Rect2).position.y)
		zs.append((h as Rect2).end.y)
	zs.sort()
	var k := 0
	for bi in range(zs.size() - 1):
		var z0: float = zs[bi]
		var z1: float = zs[bi + 1]
		if z1 - z0 < 1e-4:
			continue
		var xs := [area.position.x]
		for h in holes:
			var r := h as Rect2
			if r.position.y < z1 - 1e-4 and r.end.y > z0 + 1e-4:
				xs.append(r.position.x)
				xs.append(r.end.x)
		xs.append(area.end.x)
		xs.sort()
		for i in range(0, xs.size() - 1, 2):
			if float(xs[i + 1]) - float(xs[i]) > 1e-4:
				_box(world, Vector3(xs[i], -0.5, z0), Vector3(xs[i + 1], 0.0, z1), mat, 1.0, "boden_%d" % k)
				k += 1


static func _stones(world: Node3D, nm: String, x0: float, z: float, count: int, r0: float, r1: float, sink: float, sd: int) -> void:
	"""one static body with many stones (spheres) on the lane from x0 over 2.5 m"""
	var gb := StaticBody3D.new()
	gb.name = nm
	gb.collision_layer = 1
	gb.collision_mask = 0
	var gpm := PhysicsMaterial.new()
	gpm.friction = 0.7
	gb.physics_material_override = gpm
	world.add_child(gb)
	var rng := RandomNumberGenerator.new()
	rng.seed = sd
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var stone := SphereMesh.new()
	stone.radius = 0.5
	stone.height = 1.0
	stone.radial_segments = 6
	stone.rings = 3
	mm.mesh = stone
	mm.instance_count = count
	for i in range(count):
		var r := rng.randf_range(r0, r1)
		var pos := Vector3(rng.randf_range(x0, x0 + 2.5), r * sink, z + rng.randf_range(-0.8, 0.8))
		var cs := CollisionShape3D.new()
		var ss := SphereShape3D.new()
		ss.radius = r
		cs.shape = ss
		cs.position = pos
		gb.add_child(cs)
		var b := Basis(Vector3(rng.randf(), rng.randf(), rng.randf()).normalized(), rng.randf() * TAU).scaled(Vector3(2 * r, 1.4 * r, 1.7 * r))
		mm.set_instance_transform(i, Transform3D(b, pos))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = _plain(Color("#9a948a"))
	world.add_child(mmi)


static func _pipe(world: Node3D, c: Vector3, r: float, ln: float, nm: String) -> void:
	"""a pipe lying across the lane (axis along z)"""
	var sb := StaticBody3D.new()
	sb.name = nm
	sb.collision_layer = 1
	sb.collision_mask = 0
	sb.position = c
	sb.rotation_degrees = Vector3(90, 0, 0)
	world.add_child(sb)
	var cs := CollisionShape3D.new()
	var cy := CylinderShape3D.new()
	cy.radius = r
	cy.height = ln
	cs.shape = cy
	sb.add_child(cs)
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = ln
	mi.mesh = cm
	mi.material_override = _plain(Color("#6f7f8c"))
	sb.add_child(mi)


static func _plain(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.9
	return m


static func _box(world: Node3D, a: Vector3, b: Vector3, mat: Material, fr: float, nm: String) -> void:
	var sb := StaticBody3D.new()
	sb.name = nm
	sb.collision_layer = 1
	sb.collision_mask = 0
	var pm := PhysicsMaterial.new()
	pm.friction = fr
	sb.physics_material_override = pm
	sb.position = (a + b) * 0.5
	world.add_child(sb)
	var size := (b - a).abs()
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	sb.add_child(cs)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = mat
	sb.add_child(mi)


static func _slab(world: Node3D, start: Vector3, ln: float, rise: float, width: float, down: bool) -> void:
	"""a ramp as a wedge (convex shape) from start.x over ln metres, up (or down) by rise"""
	var sb := StaticBody3D.new()
	sb.name = "rampe_ab" if down else "rampe"
	sb.collision_layer = 1
	sb.collision_mask = 0
	world.add_child(sb)
	var hw := width * 0.5
	var y0 := rise if down else 0.0
	var y1 := 0.0 if down else rise
	var pts := PackedVector3Array([Vector3(0, 0, -hw), Vector3(ln, 0, -hw), Vector3(0, 0, hw), Vector3(ln, 0, hw),
			Vector3(0, y0, -hw), Vector3(ln, y1, -hw), Vector3(0, y0, hw), Vector3(ln, y1, hw)])
	var clean := PackedVector3Array()
	for q in pts:
		if not clean.has(q):
			clean.append(q)
	sb.position = start
	var cs := CollisionShape3D.new()
	var cv := ConvexPolygonShape3D.new()
	cv.points = clean
	cs.shape = cv
	sb.add_child(cs)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var A := Vector3(0, y0, -hw)
	var B := Vector3(ln, y1, -hw)
	var C := Vector3(ln, y1, hw)
	var D := Vector3(0, y0, hw)
	for tri in [[A, D, C], [A, C, B]]:          # the sloped top
		for v in tri:
			st.add_vertex(v)
	var lo := [Vector3(0, 0, -hw), Vector3(ln, 0, -hw), Vector3(ln, 0, hw), Vector3(0, 0, hw)]
	for side in [[lo[0], A, B, lo[1]], [lo[3], lo[2], C, D]]:   # the two sides
		for tri in [[side[0], side[1], side[2]], [side[0], side[2], side[3]]]:
			for v in tri:
				st.add_vertex(v)
	var hi_end := [lo[1], B, C, lo[2]] if not down else [lo[0], A, D, lo[3]]
	for tri in [[hi_end[0], hi_end[1], hi_end[2]], [hi_end[0], hi_end[2], hi_end[3]]]:
		for v in tri:
			st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := _plain(Color("#8f8a80"))
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	sb.add_child(mi)


static func _sign(world: Node3D, pos: Vector3, text: String) -> void:
	var l := Label3D.new()
	l.text = text
	l.position = pos
	l.font_size = 64
	l.pixel_size = 0.0022
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.modulate = Color("#1b2430")
	l.outline_modulate = Color(1, 1, 1, 0.8)
	l.outline_size = 10
	l.add_to_group("roboter_schild")              # hidden in the side / top view (they would lie on top of each other)
	world.add_child(l)
