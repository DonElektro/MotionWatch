extends RefCounted
## Roboter-Labor: der Boden mit Raster und die Prüfstrecken (Besitzer 22.11.2026: Rampe, Stufe, Kies, Graben).
## Alles in echten Metern (der Roboter misst bei Massstab 0.10 rund 1.3 m). Start in der Mitte (Fahrspur z = 0, Blick +X);
## jede Prüfstrecke hat ihre eigene Spur parallel dazu, sie beginnt bei x = 2.5:
##   Rampe 15° (z = +3) · Stufe 6 cm (z = −3) · Kies (z = +6) · Graben 20 cm breit, 15 cm tief (z = −6, quer über die Spur).
## Ebene 1 (LAYER_GELAENDE), der Roboter stösst nur daran.

const T = preload("res://scripts/i18n.gd")
const START_X := 2.5
const SPUREN := {"start": 0.0, "rampe": 3.0, "stufe": -3.0, "kies": 6.0, "graben": -6.0}
const RAMPE_GRAD := 15.0
const STUFE_H := 0.06
const GRABEN_B := 0.20
const GRABEN_T := 0.15

const GRID_SHADER := """
shader_type spatial;
uniform vec3 base : source_color = vec3(0.56, 0.58, 0.61);
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
	var gx0 := float(SPUREN["graben"]) - 1.0
	var gx1 := float(SPUREN["graben"]) + 1.0
	var dx0 := START_X + 0.5
	var dx1 := dx0 + GRABEN_B
	# floor (top at y = 0), the ditch is a gap across the lane of the ditch
	_box(world, Vector3(-10, -0.5, gx1), Vector3(10, 0.0, 10), mat, 1.0, "boden")
	_box(world, Vector3(-10, -0.5, -10), Vector3(10, 0.0, gx0), mat, 1.0, "boden_sued")
	_box(world, Vector3(-10, -0.5, gx0), Vector3(dx0, 0.0, gx1), mat, 1.0, "boden_vor_graben")
	_box(world, Vector3(dx1, -0.5, gx0), Vector3(10, 0.0, gx1), mat, 1.0, "boden_nach_graben")
	_box(world, Vector3(dx0, -0.5, gx0), Vector3(dx1, -GRABEN_T, gx1), _plain(Color("#6d5a45")), 1.0, "grabensohle")
	# step
	var z := float(SPUREN["stufe"])
	_box(world, Vector3(START_X, 0.0, z - 0.8), Vector3(START_X + 2.5, STUFE_H, z + 0.8), _plain(Color("#8f8a80")), 1.0, "stufe")
	# ramp up 15°, plateau, down again
	z = float(SPUREN["rampe"])
	var ln := 1.4
	var rise := ln * tan(deg_to_rad(RAMPE_GRAD))
	_slab(world, Vector3(START_X, 0, z), ln, rise, 1.6, false)
	_box(world, Vector3(START_X + ln, 0.0, z - 0.8), Vector3(START_X + ln + 1.0, rise, z + 0.8), _plain(Color("#8f8a80")), 1.0, "rampe_oben")
	_slab(world, Vector3(START_X + ln + 1.0, 0, z), ln, rise, 1.6, true)
	# gravel: one static body with many small stones
	z = float(SPUREN["kies"])
	var gb := StaticBody3D.new()
	gb.name = "kies"
	gb.collision_layer = 1
	gb.collision_mask = 0
	var gpm := PhysicsMaterial.new()
	gpm.friction = 0.7
	gb.physics_material_override = gpm
	world.add_child(gb)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2211
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var stone := SphereMesh.new()
	stone.radius = 0.5
	stone.height = 1.0
	stone.radial_segments = 6
	stone.rings = 3
	mm.mesh = stone
	var count := 520
	mm.instance_count = count
	for i in range(count):
		var r := rng.randf_range(0.012, 0.03)
		var pos := Vector3(rng.randf_range(START_X, START_X + 2.5), r * 0.35, z + rng.randf_range(-0.8, 0.8))
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
	# signs
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["rampe"]), T.t("Rampe %d°") % int(RAMPE_GRAD))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["stufe"]), T.t("Stufe %d cm") % int(round(STUFE_H * 100)))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["kies"]), T.t("Kies"))
	_sign(world, Vector3(START_X - 0.3, 0.45, SPUREN["graben"]), T.t("Graben %d cm") % int(round(GRABEN_B * 100)))
	var out := {}
	for k in SPUREN:
		out[k] = Transform3D(Basis(), Vector3(0.6, 0.0, float(SPUREN[k])))
	return out


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
	l.pixel_size = 0.004
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.modulate = Color("#1b2430")
	l.outline_modulate = Color(1, 1, 1, 0.8)
	l.outline_size = 10
	world.add_child(l)
