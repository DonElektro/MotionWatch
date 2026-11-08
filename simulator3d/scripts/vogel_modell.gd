extends RefCounted
## «Flora und Fauna» Paket 3, Schritt 2: Vögel echter (nur ab Stufe «Normal», wie tier_modell.gd) – fauna.gd baut und
## bewegt die Vögel wie bisher (Körper, Kopf, Schwanz, Flügel als eigene Knoten: picken, gehen, hüpfen, auffliegen,
## landen, segeln, Schwarm); hier bekommen diese Knoten nur schönere sichtbare Formen (Ebene 1):
##   - Rumpf als gedrehter Umriss (Brust vorne voll, nach hinten schmal), Rücken / Bauch in den Farben der Art,
##     angelegte Flügel als dunklere Rückenpartie
##   - Kopf mit Augen und Schnabel der Art (Krähe kräftig schwarz, Elster schwarz, Möwe gelb, Taube kurz mit Wachshaut)
##   - Flügel mit gefingerten Handschwingen und Flügelzeichnung (Möwe: schwarze Spitzen mit weissen Flecken, Elster: weisse
##     Handschwingen, Taube: Flügelbinden), Schwanz als Fächer (Elster lang und gestuft)
## Das Wärmebild bleibt aus den Grundformen (Zwillinge, Ebene 2) – Vögel sind darin klein und gleich warm wie bisher.
## Arten: Rabenkrähe, Elster, Lachmöwe / Mittelmeermöwe, Ringeltaube (neu: sitzt auch auf Bäumen, fauna.gd «perch») und
## die Schwarm-Vögel. Die Formen sind pro Art und Grösse einmal gebaut (ArrayMesh im Speicher, Vertex-Farben).

const Flora = preload("res://scripts/flora.gd")
const TierModell = preload("res://scripts/tier_modell.gd")

# Art: [Rücken, Bauch, Kopf, Schnabel, Flügel, Flügelspitze, Schwanz]
const FARBEN := {
	"crows": [Color(0.035, 0.035, 0.045), Color(0.05, 0.05, 0.06), Color(0.035, 0.035, 0.045), Color(0.03, 0.03, 0.03),
			Color(0.03, 0.03, 0.04), Color(0.025, 0.025, 0.03), Color(0.03, 0.03, 0.04)],
	"magpies": [Color(0.02, 0.025, 0.04), Color(0.82, 0.82, 0.80), Color(0.02, 0.022, 0.03), Color(0.02, 0.02, 0.02),
			Color(0.02, 0.04, 0.07), Color(0.80, 0.80, 0.78), Color(0.02, 0.05, 0.05)],
	"gulls": [Color(0.50, 0.54, 0.60), Color(0.88, 0.88, 0.87), Color(0.88, 0.88, 0.87), Color(0.85, 0.62, 0.06),
			Color(0.50, 0.54, 0.60), Color(0.02, 0.02, 0.02), Color(0.88, 0.88, 0.87)],
	"pigeons": [Color(0.22, 0.24, 0.29), Color(0.36, 0.30, 0.32), Color(0.24, 0.26, 0.31), Color(0.55, 0.42, 0.40),
			Color(0.25, 0.27, 0.32), Color(0.06, 0.06, 0.07), Color(0.13, 0.14, 0.17)],
}

static var _cache := {}
static var _mat: StandardMaterial3D = null


static func an(main) -> bool:
	return TierModell.an(Flora.stufe(main))


static func _material() -> StandardMaterial3D:
	if _mat == null:
		_mat = StandardMaterial3D.new()
		_mat.vertex_color_use_as_albedo = true
		_mat.roughness = 0.6
		_mat.metallic_specular = 0.45
		_mat.cull_mode = BaseMaterial3D.CULL_DISABLED            # Flügel und Schwanz sind dünne Flächen
	return _mat


static func _farben(kind: String, col: Color) -> Array:
	if FARBEN.has(kind):
		return FARBEN[kind]
	# Schwarm-Vögel (fauna.gd: schwarz, braun, grau): aus der Grundfarbe
	return [col, col.lightened(0.25), col, Color(0.1, 0.1, 0.1), col.darkened(0.1), col.darkened(0.4), col.darkened(0.2)]


static func _key(kind: String, col: Color, L: float, teil: String) -> String:
	return "%s/%s/%.3f/%s" % [kind, col.to_html(), L, teil]


# ---- Formen ----------------------------------------------------------------------------------------------------------
static func _rumpf(kind: String, F: Array, bl: float) -> ArrayMesh:
	"""Rumpf entlang z (vorne = -z), Länge ≈ bl, Brust vorne voll"""
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nz := 10
	var nr := 10
	var pts: Array = []
	for i in range(nz + 1):
		var t := float(i) / nz
		var z := lerpf(-0.5, 0.55, t) * bl
		var r := bl * 0.2 * pow(maxf(0.0, sin(PI * clampf(t * 0.92 + 0.04, 0.0, 1.0))), 0.6) * (1.15 - 0.35 * t)
		var ring: Array = []
		for j in range(nr):
			var a := TAU * j / nr
			var nrm := Vector3(cos(a), sin(a), 0.0)
			var p := Vector3(cos(a) * r * 0.95, sin(a) * r * 0.9 + bl * 0.02 * t, z)
			var c: Color = F[0]
			var unten := clampf(-sin(a) * 1.4 + 0.1, 0.0, 1.0)
			c = c.lerp(F[1], unten)
			if kind == "magpies":
				c = F[0] if t < 0.12 or (t > 0.65 and sin(a) > -0.6) else (F[1] if sin(a) < 0.25 else F[0])
				if absf(cos(a)) > 0.75 and sin(a) > -0.1 and t > 0.25 and t < 0.6:
					c = F[1]                                    # weisse Schulterflecken
			elif kind == "pigeons":
				if t < 0.3 and sin(a) > -0.2:
					c = Color(0.20, 0.33, 0.27).lerp(Color(0.38, 0.22, 0.36), 0.5 + 0.5 * cos(a * 3.0))   # schillernder Hals
					if t > 0.15 and absf(cos(a)) > 0.7:
						c = Color(0.85, 0.85, 0.85)             # weisser Halsfleck (Ringeltaube)
			elif kind == "gulls":
				c = F[0] if sin(a) > 0.35 and t > 0.25 else F[1]
			if sin(a) > 0.2 and t > 0.3 and kind != "gulls":
				c = c.darkened(0.15)                            # angelegte Flügel auf dem Rücken
			ring.append([p, nrm, c])
		pts.append(ring)
	for i in range(nz):
		for j in range(nr):
			var j2 := (j + 1) % nr
			for q in [[i, j], [i + 1, j], [i + 1, j2], [i, j], [i + 1, j2], [i, j2]]:
				var e: Array = pts[q[0]][q[1]]
				st.set_color(e[2])
				st.set_normal(e[1])
				st.add_vertex(e[0])
	st.generate_normals()
	return st.commit()


static func _kopf(kind: String, F: Array, bl: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var r := bl * 0.15
	var sm := SphereMesh.new()
	sm.radius = r
	sm.height = r * 2.0
	sm.radial_segments = 10
	sm.rings = 6
	var arr := sm.get_mesh_arrays()
	var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var cols := PackedColorArray()
	cols.resize(vs.size())
	for i in range(vs.size()):
		var v: Vector3 = vs[i] / r
		var c: Color = F[2]
		if absf(v.x) > 0.62 and v.z < -0.05 and v.z > -0.75 and v.y > 0.0 and v.y < 0.55:
			c = Color(0.02, 0.02, 0.02) if kind != "gulls" else Color(0.03, 0.03, 0.03)   # Augen
			if kind in ["pigeons", "gulls"] and absf(v.x) < 0.78:
				c = Color(0.8, 0.45, 0.1) if kind == "pigeons" else Color(0.85, 0.85, 0.85)   # Iris / Augenring
		cols[i] = c
	arr[Mesh.ARRAY_COLOR] = cols
	var tmp := ArrayMesh.new()
	tmp.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	st.append_from(tmp, 0, Transform3D(Basis().scaled(Vector3(0.95, 0.95, 1.1)), Vector3.ZERO))
	# Schnabel: Kegel nach vorne
	var bk := CylinderMesh.new()
	var lb: float = bl * {"crows": 0.3, "magpies": 0.22, "gulls": 0.26, "pigeons": 0.14}.get(kind, 0.16)
	bk.top_radius = 0.0
	bk.bottom_radius = bl * (0.055 if kind == "crows" else 0.04)
	bk.height = lb
	bk.radial_segments = 6
	bk.rings = 1
	var ba := bk.get_mesh_arrays()
	var bc := PackedColorArray()
	bc.resize((ba[Mesh.ARRAY_VERTEX] as PackedVector3Array).size())
	bc.fill(F[3])
	ba[Mesh.ARRAY_COLOR] = bc
	var tb := ArrayMesh.new()
	tb.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, ba)
	st.append_from(tb, 0, Transform3D(Basis(Vector3.RIGHT, -PI / 2 + 0.12), Vector3(0, -r * 0.15, -r * 0.8 - lb * 0.45)))
	return st.commit()


static func _flaeche(st: SurfaceTool, poly: Array, cols: Array) -> void:
	"""ein flaches Vieleck (Fächer vom ersten Punkt) - beide Seiten durch das Material"""
	for i in range(1, poly.size() - 1):
		for k in [0, i, i + 1]:
			st.set_color(cols[k])
			st.set_normal(Vector3.UP)
			st.add_vertex(poly[k])


static func _fluegel(kind: String, F: Array, span: float, side: float) -> ArrayMesh:
	"""Flügel nach +x (side = 1) bzw. -x: Armflügel breit, Hand mit 5 gefingerten Schwingen; Vorderkante bei -z"""
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c0: float = span * (0.42 if kind != "gulls" else 0.3)    # Tiefe am Körper
	var arm := span * 0.5
	var col_a: Color = F[4]
	var col_h: Color = F[5] if kind in ["gulls", "magpies"] else F[4].darkened(0.25)
	# Armflügel
	var poly := [Vector3(0, 0, -c0 * 0.4), Vector3(arm, 0.0, -c0 * 0.45), Vector3(arm, 0.0, c0 * 0.45), Vector3(0, 0, c0 * 0.6)]
	_flaeche(st, poly, [col_a, col_a, col_a, col_a])
	if kind == "pigeons":                                       # zwei dunkle Flügelbinden
		for zb in [0.05, 0.25]:
			_flaeche(st, [Vector3(arm * 0.15, 0.002, c0 * zb), Vector3(arm * 0.9, 0.002, c0 * zb), Vector3(arm * 0.9, 0.002, c0 * (zb + 0.08)),
					Vector3(arm * 0.15, 0.002, c0 * (zb + 0.08))], [F[5], F[5], F[5], F[5]])
	# Hand: fünf Schwingen, nach aussen kürzer und schmaler
	var n := 5
	for i in range(n):
		var t := float(i) / (n - 1)
		var z0 := lerpf(-c0 * 0.45, c0 * 0.3, t)
		var w := c0 * (0.22 - 0.05 * t)
		var len_ := span * (0.5 - 0.12 * absf(t - 0.25))
		var tip := Vector3(arm + len_, 0.0, z0 + w * 0.6 + len_ * 0.15 * (t - 0.3))
		var ca: Color = col_a.lerp(col_h, 0.6)
		var ct: Color = col_h
		if kind == "gulls" and i in [0, 1]:
			ct = Color(0.9, 0.9, 0.9)                           # «Spiegel»: weisse Flecken in den schwarzen Spitzen
		if kind == "magpies":
			ca = F[4]
		_flaeche(st, [Vector3(arm - c0 * 0.05, 0.001 * i, z0), tip, Vector3(arm - c0 * 0.05, 0.001 * i, z0 + w * 1.6)], [ca, ct, ca])
	var m := st.commit()
	if side < 0.0:
		var st2 := SurfaceTool.new()
		st2.begin(Mesh.PRIMITIVE_TRIANGLES)
		st2.append_from(m, 0, Transform3D(Basis().scaled(Vector3(-1, 1, 1)), Vector3.ZERO))
		return st2.commit()
	return m


static func _schwanz(kind: String, F: Array, bl: float, tl: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var w0 := bl * 0.08
	var w1 := bl * (0.22 if kind != "magpies" else 0.12)
	var c: Color = F[6]
	var ce: Color = c.darkened(0.3) if kind != "pigeons" else Color(0.05, 0.05, 0.06)   # Taube: dunkle Endbinde
	if kind == "magpies":                                       # gestuft: die mittleren Federn am längsten
		_flaeche(st, [Vector3(-w0, 0, 0), Vector3(w0, 0, 0), Vector3(w1, 0, tl * 0.75), Vector3(0, 0, tl), Vector3(-w1, 0, tl * 0.75)], [c, c, c, ce, c])
	else:
		_flaeche(st, [Vector3(-w0, 0, 0), Vector3(w0, 0, 0), Vector3(w1, 0, tl), Vector3(0, 0, tl * 0.93), Vector3(-w1, 0, tl)], [c, c, ce, ce, ce])
	return st.commit()


static func _mesh(kind: String, col: Color, L: float, teil: String) -> ArrayMesh:
	var k := _key(kind, col, snappedf(L, 0.02), teil)
	if _cache.has(k):
		return _cache[k]
	var F := _farben(kind, col)
	var bl := L * (0.42 if kind != "magpies" else 0.32)
	var m: ArrayMesh
	match teil:
		"rumpf":
			m = _rumpf(kind, F, bl)
		"kopf":
			m = _kopf(kind, F, bl)
		"fluegel_r":
			m = _fluegel(kind, F, L * 0.95, 1.0)
		"fluegel_l":
			m = _fluegel(kind, F, L * 0.95, -1.0)
		"schwanz":
			m = _schwanz(kind, F, bl, L * (0.5 if kind == "magpies" else 0.22))
	_cache[k] = m
	return m


static func _mi(parent: Node3D, mesh: Mesh, pos := Vector3.ZERO, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = _material()
	mi.layers = 1
	mi.position = pos
	mi.rotation = rot
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


static func _hide_visible(n: Node, keep_legs: bool) -> void:
	for c in n.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).layers == 1:
			if keep_legs and (c as MeshInstance3D).mesh is CylinderMesh:
				continue
			(c as MeshInstance3D).visible = false


# ---- an die Vögel von fauna.gd ---------------------------------------------------------------------------------------
static func boden(b: Dictionary) -> void:
	"""ein Vogel am Boden / am Wasser / auf einem Ast (fauna.gd _ground_bird): Knoten node, body, head, tail, wings"""
	var kind: String = b["kind"]
	var L: float = b["L"]
	var col: Color = FARBEN.get(kind, FARBEN["crows"])[0]
	_hide_visible(b["node"], true)
	_hide_visible(b["body"], false)
	_hide_visible(b["head"], false)
	_hide_visible(b["tail"], false)
	_mi(b["body"], _mesh(kind, col, L, "rumpf"))
	_mi(b["head"], _mesh(kind, col, L, "kopf"))
	_mi(b["tail"], _mesh(kind, col, L, "schwanz"), Vector3.ZERO, Vector3(0.12 if kind == "magpies" else -0.05, 0, 0))
	var ws: Array = b["wings"]
	for i in range(ws.size()):
		var w: Node3D = ws[i]
		_hide_visible(w, false)
		_mi(w, _mesh(kind, col, L, "fluegel_l" if i == 0 else "fluegel_r"))
	b["modell"] = true


static func schwarm(b: Dictionary, size: float, col: Color) -> void:
	"""ein Vogel im Schwarm / Fledermaus (fauna.gd _bird): Knoten node, wings (je ein Knoten pro Seite)"""
	var L := size * 1.8
	_hide_visible(b["node"], false)
	var body := Node3D.new()
	(b["node"] as Node3D).add_child(body)
	_mi(body, _mesh("schwarm", col, L, "rumpf"))
	var head := _mi(body, _mesh("schwarm", col, L, "kopf"), Vector3(0, L * 0.42 * 0.12, -L * 0.42 * 0.55))
	head.scale = Vector3.ONE
	_mi(body, _mesh("schwarm", col, L, "schwanz"), Vector3(0, 0, L * 0.42 * 0.5), Vector3(-0.1, 0, 0))
	var ws: Array = b["wings"]
	for i in range(ws.size()):
		var w: Node3D = ws[i]
		_hide_visible(w, false)
		_mi(w, _mesh("schwarm", col, L, "fluegel_l" if i == 0 else "fluegel_r"), Vector3(-L * 0.42 * 0.08 if i == 0 else L * 0.42 * 0.08, 0, 0))
