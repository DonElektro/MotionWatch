extends RefCounted
## «Wege und Strassen» (Wunsch des Besitzers: «heute ist es nur ein Streifen»), Schritt 1: Asphalt-Strassen und Feldwege.
## Nur Normal / Hoch (Gras.an = Flora.stufe normal / hoch); Lite, MW_FLORA=alt und --quality (Prüfstand) bauen genau wie vorher
## (gleicher Code-Pfad, keine Zufallszahlen: alles Muster entsteht im Shader aus dem Ort).
##
##   - Asphalt (shaders/strasse.gdshader): Foto-Struktur (texturen/weg_asphalt_01) + Körnung, Abnutzung, Risse, Flicken,
##     dunklere Fahrspuren, Schachtdeckel, Schweizer Markierung (weisse Rand- und Leitlinien, gelbe Parkfelder wo nötig),
##     Bankett aus Kies mit weichem Rand ins Gras, Randsteine im Dorf / am Camping-Platz (randstein()), Nässe und Pfützen
##     in den Fahrspuren mit Spiegelung des Himmels, Schnee mit frei gefahrenen Spuren.
##   - Feldweg / Kies (shaders/feldweg.gdshader): zwei Kies-Fahrspuren, Grasstreifen in der Mitte (der Boden darunter scheint
##     durch: gleiches Gras, gleiche Jahreszeit), lose Steine, Spurrinnen, Pfützen nach Regen, weicher Rand ins Gras.
## Netze: ein Band mit mehreren Längsstreifen (folgt dem Gelände auch quer), UV = (quer in m ab der Mitte, längs in m),
## UV2 = (halbe Breite des Belags, Bankett / Rand in m). Ein Zeichenaufruf pro Weg wie bisher; das Wärmebild bleibt gleich
## (der Zwilling auf Ebene 2 behält das alte Netz). Erkennung: Art «road» und Ebenen unverändert.

const Gras = preload("res://scripts/gras.gd")
const Flora = preload("res://scripts/flora.gd")

static var _shader_strasse: Shader = null
static var _shader_feld: Shader = null


static func an(m) -> bool:
	return Gras.an(m)


static func _register(m, mt: ShaderMaterial) -> void:
	"""Nässe, Pfützen, Schnee (colors.gd, jahreszeiten.gd, main._update_sky) und Wolkenschatten (gelaende.gd) wie der Boden"""
	m.ground_mats.append(mt)
	if m.get("gelaende") != null and m.gelaende != null:
		m.gelaende.path_mats.append(mt)
	if m.get("noise_tex") != null:
		mt.set_shader_parameter("noise_tex", m.noise_tex)


static func strasse_mat(m, o := {}) -> ShaderMaterial:
	"""Asphalt: o = {centre: Leitlinie (gestrichelt), edge: Randlinien, park: [von, bis, Seite ±1] gelbe Parkfelder (m längs),
	hoch: Hoch-Stufe (mehr Feinheit)}"""
	if _shader_strasse == null:
		_shader_strasse = load("res://shaders/strasse.gdshader")
	var mt := ShaderMaterial.new()
	mt.shader = _shader_strasse
	mt.set_shader_parameter("centre_line", 1.0 if o.get("centre", true) else 0.0)
	mt.set_shader_parameter("edge_line", 1.0 if o.get("edge", true) else 0.0)
	var pk: Array = o.get("park", [])
	if pk.size() == 3:
		mt.set_shader_parameter("park", Vector3(float(pk[0]), float(pk[1]), float(pk[2])))
	var tx = load("res://texturen/weg_asphalt_01.jpg")
	if tx != null:
		mt.set_shader_parameter("photo", tx)
		mt.set_shader_parameter("photo_on", 1.0)
	mt.set_shader_parameter("fine", 1.0 if Flora.stufe(m) == "hoch" else 0.6)
	mt.set_meta("inhalte", true)                       # inhalte.gd / grafik_hoch.gd: has its own surface already
	_register(m, mt)
	return mt


static func feld_mat(m, kind: String, base: Color, grit: Color) -> ShaderMaterial:
	"""Feldweg («erde»: zwei Fahrspuren, Gras in der Mitte) oder Kiesweg («kies»), weicher Rand"""
	if _shader_feld == null:
		_shader_feld = load("res://shaders/feldweg.gdshader")
	var mt := ShaderMaterial.new()
	mt.shader = _shader_feld
	mt.set_shader_parameter("base", base)
	mt.set_shader_parameter("grit", grit)
	mt.set_shader_parameter("tracks", 1.0 if kind == "erde" else 0.0)
	_register(m, mt)
	return mt


# ---- Netze -----------------------------------------------------------------------------------------------------------------
static func dense(pts: Array, step := 0.8) -> PackedVector2Array:
	var line := PackedVector2Array()
	for k in range(pts.size() - 1):
		var a: Vector2 = pts[k]
		var b: Vector2 = pts[k + 1]
		var cnt := maxi(1, int(ceil(a.distance_to(b) / step)))
		for s in range(cnt):
			line.append(a.lerp(b, float(s) / cnt))
	line.append(pts[-1])
	return line


static func band(m, line: PackedVector2Array, hw: float, rim: float, lift: float, cols: Array, wob := 0.0) -> ArrayMesh:
	"""ein Band entlang line (x/z): quer an den Stellen cols (Bruchteil von -1 … 1 der ganzen halben Breite hw + rim), jede
	Ecke auf dem Boden (m.ground_y) + lift. UV = (quer m, längs m), UV2 = (hw, rim). Dreiecke schauen nach oben.
	wob: der Rand ist nicht ganz gerade (wie gelaende.path)"""
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var uv2 := PackedVector2Array()
	var idx := PackedInt32Array()
	var nc := cols.size()
	var along := 0.0
	var G = m.get("gelaende")
	var hilly: bool = G != null and G.on
	for k in range(line.size()):
		var p: Vector2 = line[k]
		var dir: Vector2 = (line[mini(k + 1, line.size() - 1)] - line[maxi(k - 1, 0)]).normalized()
		var side := Vector2(-dir.y, dir.x)
		if k > 0:
			along += p.distance_to(line[k - 1])
		var w := 1.0 + wob * sin(along * 0.9 + p.x)
		for c in cols:
			var off: float = float(c) * (hw * w + rim)
			var q: Vector2 = p + side * off
			verts.append(Vector3(q.x, m.ground_y(q.x, q.y) + lift, q.y))
			norms.append(G.normal_at(q.x, q.y) if hilly else Vector3.UP)
			uvs.append(Vector2(off, along))
			uv2.append(Vector2(hw * w, rim))
		if k > 0:
			var a := (k - 1) * nc
			var b := k * nc
			for c in range(nc - 1):
				var t0 := [a + c, a + c + 1, b + c]
				var t1 := [a + c + 1, b + c + 1, b + c]
				for t in [t0, t1]:
					var e1: Vector3 = verts[t[1]] - verts[t[0]]
					var e2: Vector3 = verts[t[2]] - verts[t[0]]
					if e1.cross(e2).y > 0.0:              # Godot: front faces clockwise seen from above
						idx.append_array([t[0], t[2], t[1]])
					else:
						idx.append_array([t[0], t[1], t[2]])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_TEX_UV2] = uv2
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


const COLS_STRASSE := [-1.0, -0.86, -0.5, 0.0, 0.5, 0.86, 1.0]
const COLS_FELD := [-1.0, -0.7, -0.35, 0.0, 0.35, 0.7, 1.0]


# ---- Szenen ----------------------------------------------------------------------------------------------------------------
static func szene_strasse(sc, mi: MeshInstance3D, z: float, width: float) -> void:
	"""scenes.road (eine gerade Strasse entlang x bei z): das sichtbare Netz wird zur echten Strasse (Normal / Hoch);
	der Zwilling im Wärmebild bleibt die alte Kiste. Am Camping-Platz Randsteine vor dem Platz und gelbe Parkfelder."""
	var m = sc.m
	var line := dense([Vector2(-200.0, z), Vector2(200.0, z)], 4.0)
	var hw := width * 0.5
	var o := {"centre": width >= 5.0, "edge": true}
	var camping := str(m.scene) == "camping"
	if camping:
		o["park"] = [-22.0 + 200.0, -4.0 + 200.0, 1.0]      # three yellow fields (private, the camping place) on its side
	mi.mesh = band(m, line, hw, 0.6, 0.03, COLS_STRASSE)
	mi.position = Vector3.ZERO
	mi.material_override = strasse_mat(m, o)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if camping:
		randstein(m, sc.root, Vector2(-26.0, z), Vector2(-1.2, z), hw, 1.0)    # kerb in front of the place, gap at the path
		randstein(m, sc.root, Vector2(2.4, z), Vector2(16.0, z), hw, 1.0)


static var _kerb_mat: StandardMaterial3D = null


static func randstein(m, parent: Node3D, a: Vector2, b: Vector2, hw: float, side: float) -> MeshInstance3D:
	"""Randstein (Granit, 12 cm hoch, 15 cm breit) entlang einer geraden Strasse a → b auf der Seite side; nur sichtbar
	(Ebene 1, kein Hindernis, nicht im Wärmebild). Die Enden sind abgesenkt."""
	var d := (b - a).normalized()
	var n := Vector2(-d.y, d.x) * side
	var L := a.distance_to(b)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := maxi(2, int(L / 1.0))                 # 1 m stones
	for i in range(seg):
		var t0 := float(i) / seg
		var t1 := float(i + 1) / seg - 0.008 / L         # a fine joint (8 mm)
		var p0 := a.lerp(b, t0) + n * hw
		var p1 := a.lerp(b, t1) + n * hw
		var h0 := 0.12 * clampf(minf(t0, 1.0 - t0) * L / 0.8, 0.25, 1.0)   # lowered ends
		var h1 := 0.12 * clampf(minf(t1, 1.0 - t1) * L / 0.8, 0.25, 1.0)
		var y0: float = m.ground_y(p0.x, p0.y)
		var y1: float = m.ground_y(p1.x, p1.y)
		var o := n * 0.15
		var lo0 := Vector3(p0.x, y0 + 0.03, p0.y)
		var lo1 := Vector3(p1.x, y1 + 0.03, p1.y)
		var hi0 := Vector3(p0.x, y0 + 0.03 + h0, p0.y)
		var hi1 := Vector3(p1.x, y1 + 0.03 + h1, p1.y)
		var ho0 := hi0 + Vector3(o.x, 0, o.y)
		var ho1 := hi1 + Vector3(o.x, 0, o.y)
		var lo0o := Vector3(p0.x + o.x, y0, p0.y + o.y)
		var lo1o := Vector3(p1.x + o.x, y1, p1.y + o.y)
		_quad(st, lo0, lo1, hi1, hi0, Vector3(-n.x, 0, -n.y))   # face to the road
		_quad(st, hi0, hi1, ho1, ho0, Vector3.UP)               # top
		_quad(st, ho0, ho1, lo1o, lo0o, Vector3(n.x, 0, n.y))   # back (to the meadow)
	if _kerb_mat == null:
		_kerb_mat = StandardMaterial3D.new()
		_kerb_mat.albedo_color = Color(0.47, 0.47, 0.46)
		_kerb_mat.roughness = 0.9
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _kerb_mat
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


static func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, nrm: Vector3) -> void:
	var vs := [a, b, c, a, c, d]
	if (b - a).cross(c - a).dot(nrm) > 0.0:             # Godot: clockwise = front
		vs = [a, c, b, a, d, c]
	for v in vs:
		st.set_normal(nrm)
		st.add_vertex(v)
