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
	"""Nässe, Pfützen, Schnee (colors.gd, jahreszeiten.gd, main._update_sky) und Wolkenschatten (gelaende.gd) wie der Boden;
	Schritt 2: Herbstlaub (season(), aus jahreszeiten.update)"""
	mt.set_meta("wege", true)
	mt.set_shader_parameter("laub", laub_now(m))
	m.ground_mats.append(mt)
	if m.get("gelaende") != null and m.gelaende != null:
		m.gelaende.path_mats.append(mt)
	if m.get("noise_tex") != null:
		mt.set_shader_parameter("noise_tex", m.noise_tex)


static func strasse_mat(m, o := {}) -> ShaderMaterial:
	"""Asphalt: o = {centre: Leitlinie (gestrichelt), edge: Randlinien, park: [von, bis, Seite ±1] gelbe Parkfelder (m längs),
	bays: 1 Parkstreifen (Felder längs) / 2 Parkplatz (zwei Reihen quer), bay_col: Farbe der Felder (gelb / weiss)}"""
	if _shader_strasse == null:
		_shader_strasse = load("res://shaders/strasse.gdshader")
	var mt := ShaderMaterial.new()
	mt.shader = _shader_strasse
	mt.set_shader_parameter("centre_line", 1.0 if o.get("centre", true) else 0.0)
	mt.set_shader_parameter("edge_line", 1.0 if o.get("edge", true) else 0.0)
	mt.set_shader_parameter("bays", float(o.get("bays", 0)))
	if o.has("bay_col"):
		mt.set_shader_parameter("bay_col", o["bay_col"])
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


static func band(m, line: PackedVector2Array, hw: float, rim: float, lift: float, cols: Array, wob := 0.0, hfn := Callable(), hs := PackedFloat32Array()) -> ArrayMesh:
	"""ein Band entlang line (x/z): quer an den Stellen cols (Bruchteil von -1 … 1 der ganzen halben Breite hw + rim), jede
	Ecke auf dem Boden (m.ground_y, oder hfn(x, z) in den Koordinaten des Netzes, z. B. Bergtal H) + lift.
	UV = (quer m, längs m), UV2 = (hw, rim). Dreiecke schauen nach oben. wob: der Rand ist nicht ganz gerade (wie gelaende.path).
	hs: eine Höhe je Punkt der Linie (quer eben - eine Strasse auf Dämmen und Brücken, Bergtal)"""
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var uv2 := PackedVector2Array()
	var idx := PackedInt32Array()
	var nc := cols.size()
	var along := 0.0
	var G = m.get("gelaende")
	var hilly: bool = G != null and G.on and not hfn.is_valid()
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
			var gy: float
			if not hs.is_empty():
				gy = hs[mini(k, hs.size() - 1)]
			elif hfn.is_valid():
				gy = float(hfn.call(q.x, q.y))
			else:
				gy = mesh_y(G, q.x, q.y) if hilly else m.ground_y(q.x, q.y)
			verts.append(Vector3(q.x, gy + lift, q.y))
			if hfn.is_valid():
				var e := 0.75
				norms.append(Vector3(float(hfn.call(q.x - e, q.y)) - float(hfn.call(q.x + e, q.y)), 2.0 * e,
						float(hfn.call(q.x, q.y - e)) - float(hfn.call(q.x, q.y + e))).normalized())
			else:
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


static func mesh_y(G, x: float, z: float) -> float:
	"""die Höhe des Boden-Gitters von gelaende.gd genau wie gezeichnet (zwei Dreiecke je Zelle, nicht bilinear wie
	G.height): sonst sinkt ein Weg auf Hügeln stellenweise unter den Boden (der alte Weg war dort unsichtbar)"""
	if absf(x) >= G.half or absf(z) >= G.half:
		return 0.0
	var u: float = (x + G.half) / G.step
	var v: float = (z + G.half) / G.step
	var nn: int = G.n
	var i0 := clampi(int(floor(u)), 0, nn - 2)
	var j0 := clampi(int(floor(v)), 0, nn - 2)
	var fu := clampf(u - i0, 0.0, 1.0)
	var fv := clampf(v - j0, 0.0, 1.0)
	var h00: float = G.h[j0 * nn + i0]
	var h10: float = G.h[j0 * nn + i0 + 1]
	var h01: float = G.h[(j0 + 1) * nn + i0]
	var h11: float = G.h[(j0 + 1) * nn + i0 + 1]
	if fu + fv <= 1.0:
		return h00 + fu * (h10 - h00) + fv * (h01 - h00)
	return h11 + (1.0 - fu) * (h01 - h11) + (1.0 - fv) * (h10 - h11)


static func grid_fn(hfn: Callable, lo: float, step: float) -> Callable:
	"""die Höhe eines Boden-Gitters (Ecken aus hfn, Zelle step ab lo, zwei Dreiecke je Zelle wie in ferienpark / kompakt / bergtal
	_grid) - genau wie gezeichnet, damit ein Weg an Terrassen und Knicken nicht in den Boden sinkt oder darüber schwebt"""
	return func(x: float, z: float) -> float:
		var u := (x - lo) / step
		var v := (z - lo) / step
		var i0 := floorf(u)
		var j0 := floorf(v)
		var fu := u - i0
		var fv := v - j0
		var x0 := lo + i0 * step
		var z0 := lo + j0 * step
		var h00 := float(hfn.call(x0, z0))
		var h10 := float(hfn.call(x0 + step, z0))
		var h01 := float(hfn.call(x0, z0 + step))
		if fu + fv <= 1.0:
			return h00 + fu * (h10 - h00) + fv * (h01 - h00)
		var h11 := float(hfn.call(x0 + step, z0 + step))
		return h11 + (1.0 - fu) * (h01 - h11) + (1.0 - fv) * (h10 - h11)


const COLS_STRASSE := [-1.0, -0.86, -0.5, 0.0, 0.5, 0.86, 1.0]
const COLS_FELD := [-1.0, -0.7, -0.35, 0.0, 0.35, 0.7, 1.0]


# ---- Szenen ----------------------------------------------------------------------------------------------------------------
static func szene_strasse(sc, mi: MeshInstance3D, z: float, width: float) -> void:
	"""scenes.road (eine gerade Strasse entlang x bei z): das sichtbare Netz wird zur echten Strasse (Normal / Hoch);
	der Zwilling im Wärmebild bleibt die alte Kiste. Am Camping-Platz Randsteine (Schrägbord) vor dem Platz."""
	var m = sc.m
	var line := dense([Vector2(-200.0, z), Vector2(200.0, z)], 4.0)
	var hw := width * 0.5
	var o := {"centre": width >= 5.0, "edge": true}
	var camping := str(m.scene) == "camping"            # (no yellow fields here: cars park beside the road, fahrzeuge.gd)
	mi.mesh = band(m, line, hw, 0.6, 0.03, COLS_STRASSE)
	mi.position = Vector3.ZERO
	mi.material_override = strasse_mat(m, o)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if camping:
		randstein(m, sc.root, Vector2(-26.0, z), Vector2(-1.2, z), hw, 1.0)    # kerb in front of the place, gap at the path
		randstein(m, sc.root, Vector2(2.4, z), Vector2(16.0, z), hw, 1.0)


static var _kerb_mat: StandardMaterial3D = null


static func randstein(m, parent: Node3D, a: Vector2, b: Vector2, hw: float, side: float) -> MeshInstance3D:
	"""Randstein als Schrägbord (Granit, 7 cm hoch, schräg zur Strasse, 18 cm breit: Autos fahren zum Parkieren darüber)
	entlang einer geraden Strasse a → b auf der Seite side; nur sichtbar (Ebene 1, kein Hindernis, nicht im Wärmebild).
	Die Enden sind abgesenkt."""
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
		var h0 := 0.07 * clampf(minf(t0, 1.0 - t0) * L / 0.8, 0.25, 1.0)   # lowered ends
		var h1 := 0.07 * clampf(minf(t1, 1.0 - t1) * L / 0.8, 0.25, 1.0)
		var y0: float = m.ground_y(p0.x, p0.y)
		var y1: float = m.ground_y(p1.x, p1.y)
		var o := n * 0.18
		var lo0 := Vector3(p0.x, y0 + 0.03, p0.y)
		var lo1 := Vector3(p1.x, y1 + 0.03, p1.y)
		var sl := n * 0.07                                # the slanted face
		var hi0 := Vector3(p0.x + sl.x, y0 + 0.03 + h0, p0.y + sl.y)
		var hi1 := Vector3(p1.x + sl.x, y1 + 0.03 + h1, p1.y + sl.y)
		var ho0 := hi0 + Vector3(o.x - sl.x * 0.5, 0, o.y - sl.y * 0.5)
		var ho1 := hi1 + Vector3(o.x - sl.x * 0.5, 0, o.y - sl.y * 0.5)
		var lo0o := Vector3(ho0.x, y0, ho0.z)
		var lo1o := Vector3(ho1.x, y1, ho1.z)
		_quad(st, lo0, lo1, hi1, hi0, Vector3(-n.x, 1.0, -n.y).normalized())   # slanted face to the road
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


# =============================================================================================================================
# Schritt 2: Wanderwege, Verlauf im Gelände, Jahreszeiten
# =============================================================================================================================
static var _shader_wander: Shader = null


static func wander_mat(m, o := {}) -> ShaderMaterial:
	"""Wanderweg: o = {rock: 0 Erde … 1 Bergweg (Geröll), roots: Wurzeln (Wald), earth / earth2: Farben}"""
	if _shader_wander == null:
		_shader_wander = load("res://shaders/wanderweg.gdshader")
	var mt := ShaderMaterial.new()
	mt.shader = _shader_wander
	mt.set_shader_parameter("rock", float(o.get("rock", 0.0)))
	mt.set_shader_parameter("roots", float(o.get("roots", 1.0)))
	if o.has("earth"):
		mt.set_shader_parameter("earth", o["earth"])
		mt.set_shader_parameter("earth2", (o["earth"] as Color).darkened(0.25))
	_register(m, mt)
	return mt


# ---- Verlauf: Kurven statt gerader Stücke, sanftes Mäandern ---------------------------------------------------------------
static func spline(pts: Array, step := 0.8) -> PackedVector2Array:
	"""Catmull-Rom durch alle Punkte (die Ecken werden zu Kurven, die Punkte selbst bleiben), alle ~step m ein Punkt"""
	var n := pts.size()
	if n < 3:
		return dense(pts, step)
	var out := PackedVector2Array()
	for i in range(n - 1):
		var p1: Vector2 = pts[i]
		var p2: Vector2 = pts[i + 1]
		var p0: Vector2 = pts[i - 1] if i > 0 else p1 * 2.0 - p2
		var p3: Vector2 = pts[i + 2] if i + 2 < n else p2 * 2.0 - p1
		# tangents limited by the segment (no loops where a short piece meets a long one)
		var L := p1.distance_to(p2)
		var t1 := (p2 - p0) * 0.5
		var t2 := (p3 - p1) * 0.5
		t1 = t1.limit_length(L * 0.9)
		t2 = t2.limit_length(L * 0.9)
		var cnt := maxi(1, int(ceil(L / step)))
		for s in range(cnt):
			var t := float(s) / cnt
			var t2_ := t * t
			var t3 := t2_ * t
			out.append(p1 * (2.0 * t3 - 3.0 * t2_ + 1.0) + t1 * (t3 - 2.0 * t2_ + t) + p2 * (-2.0 * t3 + 3.0 * t2_) + t2 * (t3 - t2_))
	out.append(pts[-1])
	return out


static func rounded(pts: Array, r := 6.0) -> Array:
	"""die Ecken eines Linienzugs abrunden (höchstens r m und ein Viertel der Stücke weit von der Ecke): der Weg bleibt nahe am
	alten Verlauf (Bäume, Wegweiser, Ziele stehen weiter richtig)"""
	if pts.size() < 3:
		return pts
	var out := [pts[0]]
	for i in range(1, pts.size() - 1):
		var a: Vector2 = pts[i - 1]
		var p: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var c := minf(r, minf(a.distance_to(p), p.distance_to(b)) * 0.25)
		var q0 := p + (a - p).normalized() * c
		var q1 := p + (b - p).normalized() * c
		for k in range(5):                                # quadratic Bézier q0 - p - q1
			var t := float(k) / 4.0
			out.append(q0.lerp(p, t).lerp(p.lerp(q1, t), t))
	out.append(pts[-1])
	return out


static func meander(line: PackedVector2Array, amp: float, ph := 0.0, keep_ends := 12.0) -> PackedVector2Array:
	"""sanftes Pendeln quer zum Weg (zwei Wellen, ~23 m und ~9 m), an den Enden (Abzweigungen) null"""
	var out := PackedVector2Array()
	var total := 0.0
	for k in range(1, line.size()):
		total += line[k].distance_to(line[k - 1])
	var s := 0.0
	for k in range(line.size()):
		if k > 0:
			s += line[k].distance_to(line[k - 1])
		var d := (line[mini(k + 1, line.size() - 1)] - line[maxi(k - 1, 0)]).normalized()
		var side := Vector2(-d.y, d.x)
		var fade := smoothstep(0.0, keep_ends, s) * smoothstep(0.0, keep_ends, total - s)
		var off := amp * (sin(s * TAU / 23.0 + ph) * 0.7 + sin(s * TAU / 9.0 + ph * 2.3) * 0.3) * fade
		out.append(line[k] + side * off)
	return out


# ---- Treppen an steilen Stellen ------------------------------------------------------------------------------------------
static var _step_mat: StandardMaterial3D = null


static func steps(m, parent: Node3D, line: PackedVector2Array, hw: float, hfn: Callable, stone := false, vis := 70.0) -> int:
	"""Stufen quer über den Weg, wo er steiler ist als ~28 %: Holzbalken (Wald) oder Steinstufen (Berg), alle ~17 cm Höhe.
	Nur sichtbar (Ebene 1, kein Hindernis); in Stücken von 120 m, weit weg nicht gezeichnet. Gibt die Anzahl Stufen zurück."""
	if line.size() < 3:
		return 0
	var hs := PackedFloat32Array()
	for p in line:
		hs.append(float(hfn.call(p.x, p.y)))
	var pieces := {}
	var cnt := 0
	var last_h := INF
	var last_s := -10.0
	var s := 0.0
	for k in range(1, line.size() - 1):
		s += line[k].distance_to(line[k - 1])
		var k0 := maxi(0, k - 2)
		var k1 := mini(line.size() - 1, k + 2)
		var run := 0.0
		for j in range(k0, k1):
			run += line[j + 1].distance_to(line[j])
		var grade := absf(hs[k1] - hs[k0]) / maxf(run, 0.1)
		if grade < 0.28:
			last_h = INF
			continue
		if absf(hs[k] - last_h) < 0.17 and s - last_s < 1.2:
			continue
		last_h = hs[k]
		last_s = s
		var p := line[k]
		var d := (line[k + 1] - line[k - 1]).normalized()
		var side := Vector2(-d.y, d.x)
		var key := "%d,%d" % [int(floor(p.x / 120.0)), int(floor(p.y / 120.0))]
		if not pieces.has(key):
			var st0 := SurfaceTool.new()
			st0.begin(Mesh.PRIMITIVE_TRIANGLES)
			pieces[key] = st0
		var col := Color(0.5, 0.48, 0.45) if stone else Color(0.45, 0.34, 0.23)
		var depth := 0.3 if stone else 0.13
		var wdt := hw * (1.7 if stone else 1.8)
		_step(pieces[key], p, d, side, wdt, depth, hfn, col)
		cnt += 1
	if _step_mat == null:
		_step_mat = StandardMaterial3D.new()
		_step_mat.vertex_color_use_as_albedo = true
		_step_mat.roughness = 0.9
	for key in pieces:
		var mi := MeshInstance3D.new()
		mi.mesh = (pieces[key] as SurfaceTool).commit()
		mi.material_override = _step_mat
		mi.layers = 1
		mi.visibility_range_end = vis
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		parent.add_child(mi)
	return cnt


static func _step(st: SurfaceTool, p: Vector2, d: Vector2, side: Vector2, w: float, depth: float, hfn: Callable, col: Color) -> void:
	"""eine Stufe, die dem Hang quer folgt: oben eben in Wegrichtung (an der oberen Kante bündig mit dem Boden), vorne eine
	Kante bis in den Boden - keine schiefen Klötze auf einem Querhang"""
	var f := d * depth * 0.5
	var tops := []
	var lows := []
	for e in [p - side * w * 0.5, p + side * w * 0.5]:
		var h0 := float(hfn.call((e - f).x, (e - f).y))
		var h1 := float(hfn.call((e + f).x, (e + f).y))
		tops.append(maxf(h0, h1) + 0.03)
		lows.append(minf(h0, h1) - 0.03)
	var a := p - side * w * 0.5
	var b := p + side * w * 0.5
	var A0 := Vector3((a - f).x, tops[0], (a - f).y)
	var A1 := Vector3((a + f).x, tops[0], (a + f).y)
	var B0 := Vector3((b - f).x, tops[1], (b - f).y)
	var B1 := Vector3((b + f).x, tops[1], (b + f).y)
	_quad_c(st, A0, A1, B1, B0, Vector3.UP, col)
	for k in [0, 1]:                                      # both long faces down into the ground (the lower one shows)
		var sg := -1.0 if k == 0 else 1.0
		var t0 := A0 if k == 0 else A1
		var t1 := B0 if k == 0 else B1
		_quad_c(st, t0, t1, Vector3(t1.x, lows[1], t1.z), Vector3(t0.x, lows[0], t0.z), Vector3(d.x * sg, 0, d.y * sg), col * 0.88)


static func _box(st: SurfaceTool, c: Vector3, fwd: Vector2, side: Vector2, w: float, h: float, d: float, col: Color) -> void:
	"""ein Quader (Mitte c, quer w entlang side, tief d entlang fwd, hoch h) ohne Boden"""
	var f := Vector3(fwd.x, 0, fwd.y) * d * 0.5
	var sd := Vector3(side.x, 0, side.y) * w * 0.5
	var up := Vector3(0, h * 0.5, 0)
	var shade := [1.0, 0.9, 0.9, 0.82, 0.82]
	var faces := [[up, f, sd], [f, up, sd], [-f, up, sd], [sd, up, f], [-sd, up, f]]
	for i in range(faces.size()):
		var n: Vector3 = faces[i][0]
		var u: Vector3 = faces[i][1]
		var v: Vector3 = faces[i][2]
		var o: Vector3 = c + n
		st.set_color(col * shade[i])
		_quad_c(st, o - u - v, o + u - v, o + u + v, o - u + v, n.normalized(), col * shade[i])


static func _quad_c(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, nrm: Vector3, col: Color) -> void:
	var vs := [a, b, c, a, c, d]
	if (b - a).cross(c - a).dot(nrm) > 0.0:
		vs = [a, c, b, a, d, c]
	for v in vs:
		st.set_color(col)
		st.set_normal(nrm)
		st.add_vertex(v)


# ---- Markierung: gelbe Raute auf Pfosten, weiss-rot-weiss beim Bergweg ------------------------------------------------------
static var _mark_mat: StandardMaterial3D = null


static func mark_posts(m, parent: Node3D, list: Array, vis := 90.0) -> MeshInstance3D:
	"""Markierungs-Pfosten: list = [[Vector3 Fuss (Boden), Vector2 Wegrichtung, Stufe 0 / 1]] - Holzpfosten 1.2 m; Stufe 0 eine
	gelbe Raute auf beiden Seiten (in Wegrichtung lesbar), Stufe 1 weiss-rot-weiss um den Kopf. Ein Netz, ein Zeichenaufruf;
	nur sichtbar (kein Hindernis, nicht im Wärmebild)."""
	if list.is_empty():
		return null
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for e in list:
		var p: Vector3 = e[0]
		var d: Vector2 = (e[1] as Vector2).normalized()
		var side := Vector2(-d.y, d.x)
		var lvl := int(e[2])
		_box(st, p + Vector3(0, 0.6, 0), d, side, 0.09, 1.2, 0.09, Color(0.42, 0.33, 0.24))
		if lvl == 0:
			for sgn in [-1.0, 1.0]:                        # the rhombus faces both ways along the trail
				var c: Vector3 = p + Vector3(d.x, 0, d.y) * (0.047 * float(sgn)) + Vector3(0, 1.0, 0)
				var sv := Vector3(side.x, 0, side.y) * 0.075
				var uv := Vector3(0, 0.075, 0)
				_quad_c(st, c - uv, c + sv, c + uv, c - sv, Vector3(d.x, 0, d.y) * sgn, Color(0.96, 0.76, 0.0))
		else:
			for k in range(3):
				_box(st, p + Vector3(0, 1.1 - k * 0.06, 0), d, side, 0.096, 0.06, 0.096, Color(0.78, 0.06, 0.12) if k == 1 else Color(0.95, 0.95, 0.95))
	if _mark_mat == null:
		_mark_mat = StandardMaterial3D.new()
		_mark_mat.vertex_color_use_as_albedo = true
		_mark_mat.roughness = 0.8
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _mark_mat
	mi.layers = 1
	mi.visibility_range_end = vis
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


# ---- Jahreszeiten (jahreszeiten.update ruft season() auf, alle paar Sekunden - kein eigenes Skript pro Bild) -----------------
static func laub_now(m) -> float:
	"""Laub auf den Wegen: ab Ende September, voll ab Ende Oktober, bis Mitte Dezember (Laubfall wie jahreszeiten.bare_k); Bergtal nach seiner Jahreszeit"""
	if m == null or not an(m) or not bool(m.get("seasons_on")) or m.get("jahreszeiten") == null:
		return 0.0
	var d := float(m.jahreszeiten.doy())
	return smoothstep(265.0, 300.0, d) * (1.0 - smoothstep(345.0, 365.0, d))


static func season(m) -> void:
	var l := laub_now(m)
	for gm in m.ground_mats:
		if gm is ShaderMaterial and gm.get_meta("wege", false) and not gm.get_meta("laub_fest", false):
			if absf(float(gm.get_shader_parameter("laub")) - l) > 0.005:
				gm.set_shader_parameter("laub", l)


# ---- Camping-Platz: ein Wanderweg mit Wegweiser (nur Normal / Hoch) --------------------------------------------------------
const CAMP_TRAIL := [Vector2(-16.0, -9.5), Vector2(-21.0, -12.0), Vector2(-27.5, -15.2), Vector2(-31.0, -19.5), Vector2(-31.6, -24.5),
		Vector2(-32.0, -29.0), Vector2(-33.5, -34.5), Vector2(-38.0, -41.0), Vector2(-40.0, -50.0), Vector2(-46.0, -58.0), Vector2(-50.0, -70.0),
		Vector2(-58.0, -82.0)]


static func hide_fn(G, trail: PackedVector2Array) -> Callable:
	"""für Veg.grass / flowers: liegt p auf einer neuen Weg-Form (Kurven der Wege, Wanderweg)? (Raster 4 m: schnell)"""
	var lines := []
	for pa in G.paths:
		if pa.size() > 3:
			lines.append([pa[3], float(pa[1])])
	if trail.size() >= 2:
		lines.append([trail, 0.45])
	var grid := {}
	for ln in lines:
		var l: PackedVector2Array = ln[0]
		var r: float = float(ln[1]) + 0.15
		for k in range(l.size() - 1):
			var lo := Vector2(minf(l[k].x, l[k + 1].x), minf(l[k].y, l[k + 1].y)) - Vector2(r, r)
			var hi := Vector2(maxf(l[k].x, l[k + 1].x), maxf(l[k].y, l[k + 1].y)) + Vector2(r, r)
			for cx in range(int(floor(lo.x / 4.0)), int(floor(hi.x / 4.0)) + 1):
				for cz in range(int(floor(lo.y / 4.0)), int(floor(hi.y / 4.0)) + 1):
					var key := Vector2i(cx, cz)
					if not grid.has(key):
						grid[key] = []
					grid[key].append([l[k], l[k + 1], r])
	return func(p: Vector3) -> bool:
		var q := Vector2(p.x, p.z)
		var key := Vector2i(int(floor(q.x / 4.0)), int(floor(q.y / 4.0)))
		if not grid.has(key):
			return false
		for sg in grid[key]:
			if Geometry2D.get_closest_point_to_segment(q, sg[0], sg[1]).distance_to(q) < float(sg[2]):
				return true
		return false


static func camping_trail(sc) -> PackedVector2Array:
	"""vom Feldweg über die Strasse ins Feld und in den Wald: Wanderweg 0.9 m (gelb markiert), Wegweiser an der Strasse,
	Pfosten mit Raute. Nach Bäumen und Büschen gebaut (deren Plätze bleiben gleich); gibt die Linie zurück (gelaende.gd:
	das Gras lässt sie frei, danach kommt sie in gelaende.paths)."""
	var m = sc.m
	var G = m.gelaende
	if G == null or not an(m):
		return PackedVector2Array()
	var pts := []
	for q in CAMP_TRAIL:                                  # keep 1.6 m from trunks, bushes, hedges (moved sideways)
		var p: Vector2 = q
		for it in range(3):
			for o in m._ob_near(p):
				var r: Array = m._ob_closest(o, p)
				var dd: float = float(r[1])
				if dd < 1.6:
					p += (r[2] as Vector2) * (1.6 - dd)
		pts.append(p)
	var line := meander(spline(pts, 0.7), 0.35, 1.3, 6.0)
	var road_z := float(sc.data.get("road_z", -27.8)) - 1.2
	var st := SurfaceTool.new()                            # not over the road (it crosses it): two pieces
	var run := PackedVector2Array()
	for k in range(line.size() + 1):
		var on_road: bool = k < line.size() and absf(line[k].y - road_z) < 2.9
		if k < line.size() and not on_road:
			run.append(line[k])
			continue
		if run.size() >= 2:
			st.append_from(band(m, run, 0.42, 0.35, 0.03, COLS_FELD), 0, Transform3D.IDENTITY)
		run = PackedVector2Array()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = wander_mat(m, {"rock": 0.1, "roots": 0.6})
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.layers = 1
	sc.root.add_child(mi)
	# signpost at the road (camp side) and posts with the rhombus every ~35 m (not on the road)
	var Bib = load("res://scripts/bib_berg.gd")          # (the yellow signpost of the Swiss hiking trails)
	var bib = Bib.new(m, sc, sc.root, Transform3D.IDENTITY)
	var sp := Vector2(-29.6, road_z + 3.3)
	var yaw := func(to: Vector2) -> float:                 # like bergtal_wegweiser.groups_for: the arm points along the way
		var dv := (to - sp).normalized()
		return atan2(-dv.y, dv.x)
	var groups := [[yaw.call(pts[7]), 0, [["Chrüzweid", "25 min"], ["Ober Tannenegg", "1 h 10 min"]]],
			[yaw.call(sp + Vector2(1, 0)), 0, [["Seeblick", "35 min"]]], [yaw.call(pts[2]), 0, [["Camping Moosmatt", "5 min"]]]]
	bib.add("hiking_sign", Vector3(sp.x, m.ground_y(sp.x, sp.y), sp.y), 0.0,
			{"here": "Moosmatt Strasse %d m" % 512, "groups": groups, "both": true, "noob": true})
	bib.finish()
	var posts := []
	var s := 0.0
	var next := 22.0
	for k in range(1, line.size() - 1):
		s += line[k].distance_to(line[k - 1])
		if s < next:
			continue
		var p := line[k]
		if absf(p.y - road_z) < 4.5:
			continue
		var d := (line[k + 1] - line[k - 1]).normalized()
		var q := p + Vector2(-d.y, d.x) * 0.85
		posts.append([Vector3(q.x, m.ground_y(q.x, q.y), q.y), d, 0])
		next = s + 35.0
	mark_posts(m, sc.root, posts)
	return line


# =============================================================================================================================
# Schritt 2b: am Strassenrand, Strassen der anderen Welten, gelbe Parkfelder
# =============================================================================================================================
const WEISS := Color(0.9, 0.9, 0.88)
const GELB := Color(0.88, 0.7, 0.12)


static func strassen_band(m, parent: Node3D, line: PackedVector2Array, hw: float, o: Dictionary, hfn := Callable(), hs := PackedFloat32Array(),
		lift := 0.06, rim := 0.6, vis := 0.0, mat: ShaderMaterial = null) -> ShaderMaterial:
	"""eine Asphalt-Strasse als Band in parent (Koordinaten von parent; hfn / hs: Höhe dort), in Stücken von 200 m (vis > 0:
	Sichtweite); nur sichtbar (Ebene 1). Gibt das Material zurück (für weitere Stücke derselben Art)."""
	if mat == null:
		mat = strasse_mat(m, o)
	var pieces := {}
	var hp := {}
	for k in range(line.size()):
		var key := Vector2i(int(floor(line[k].x / 200.0)), int(floor(line[k].y / 200.0)))
		if not pieces.has(key):
			pieces[key] = PackedVector2Array()
			hp[key] = PackedFloat32Array()
			if k > 0:
				pieces[key].append(line[k - 1])
				if not hs.is_empty():
					hp[key].append(hs[k - 1])
		pieces[key].append(line[k])
		if not hs.is_empty():
			hp[key].append(hs[k])
	for key in pieces:
		var run: PackedVector2Array = pieces[key]
		if run.size() < 2:
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = band(m, run, hw, rim, lift, COLS_STRASSE, 0.0, hfn, hp[key])
		mi.material_override = mat
		mi.layers = 1
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if vis > 0.0:
			mi.visibility_range_end = vis
		parent.add_child(mi)
	return mat


static func parkplatz(m, parent: Node3D, c: Vector2, sx: float, sz: float, rot: float, hfn: Callable, col: Color, lift := 0.08) -> void:
	"""ein Parkplatz (Rechteck sx × sz um c, gedreht um rot): Asphalt mit zwei Reihen Felder quer (2.5 m), Fahrgasse in der Mitte"""
	var ax := Vector2(cos(rot), -sin(rot))                # local x in the plane (Basis(UP, rot) * (1, 0, 0))
	var line := dense([c - ax * sx * 0.5, c + ax * sx * 0.5], 2.0)
	strassen_band(m, parent, line, sz * 0.5, {"centre": false, "edge": false, "bays": 2, "bay_col": col}, hfn, PackedFloat32Array(), lift, 0.3)


# ---- am Strassenrand -----------------------------------------------------------------------------------------------------
static func kleinzeug(m, parent: Node3D, list: Array, vis := 120.0) -> MeshInstance3D:
	"""kleine Dinge am Weg in EINEM Netz (ein Zeichenaufruf; Farben je Ecke; nur sichtbar, kein Hindernis, nicht im Wärmebild):
	list = [[Art, Vector3 Fuss, yaw]] - «leitpfosten» (weiss, schwarzes Band, Rückstrahler), «robidog» (grüner Kasten für
	Hundekot-Säckli mit Behälter, ohne Marke), «briefkasten» (anthrazit, auf Pfosten)"""
	if list.is_empty():
		return null
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for e in list:
		var p: Vector3 = e[1]
		var yaw: float = e[2]
		var f := Vector2(sin(yaw), cos(yaw))              # front (+z of the thing turned by yaw)
		var sd := Vector2(cos(yaw), -sin(yaw))
		match str(e[0]):
			"leitpfosten":                                # Swiss delineator: white, 1 m, black band at the top, reflectors
				_box(st, p + Vector3(0, 0.45, 0), f, sd, 0.1, 0.9, 0.12, Color(0.93, 0.93, 0.92))
				_box(st, p + Vector3(0, 0.95, 0), f, sd, 0.101, 0.1, 0.121, Color(0.06, 0.06, 0.06))
				for k in [0, 1]:
					var c: Vector3 = p + Vector3(f.x, 0, f.y) * (0.061 if k == 0 else -0.061) + Vector3(0, 0.82, 0)
					var sv := Vector3(sd.x, 0, sd.y) * 0.025
					var uv := Vector3(0, 0.05, 0)
					_quad_c(st, c - sv - uv, c + sv - uv, c + sv + uv, c - sv + uv, Vector3(f.x, 0, f.y) * (1.0 if k == 0 else -1.0),
							Color(0.95, 0.55, 0.05) if k == 0 else Color(0.95, 0.95, 0.95))
			"robidog":                                    # dog-waste station: post, bag box, bin (green, no brand)
				_box(st, p + Vector3(0, 0.6, 0), f, sd, 0.08, 1.2, 0.08, Color(0.2, 0.35, 0.22))
				_box(st, p + Vector3(0, 1.08, 0) + Vector3(f.x, 0, f.y) * 0.1, f, sd, 0.28, 0.34, 0.12, Color(0.16, 0.45, 0.24))
				_box(st, p + Vector3(0, 0.62, 0) + Vector3(f.x, 0, f.y) * 0.16, f, sd, 0.34, 0.46, 0.24, Color(0.14, 0.38, 0.2))
				_box(st, p + Vector3(0, 0.86, 0) + Vector3(f.x, 0, f.y) * 0.16, f, sd, 0.36, 0.03, 0.26, Color(0.1, 0.25, 0.14))
				var c2: Vector3 = p + Vector3(f.x, 0, f.y) * 0.161 + Vector3(0, 1.1, 0)     # a white dog sign (a simple shape)
				var sv2 := Vector3(sd.x, 0, sd.y) * 0.07
				var uv2 := Vector3(0, 0.05, 0)
				_quad_c(st, c2 - sv2 - uv2, c2 + sv2 - uv2, c2 + sv2 + uv2, c2 - sv2 + uv2, Vector3(f.x, 0, f.y), Color(0.95, 0.95, 0.95))
			"briefkasten":                                # letterbox on a post
				_box(st, p + Vector3(0, 0.55, 0), f, sd, 0.07, 1.1, 0.07, Color(0.3, 0.3, 0.31))
				_box(st, p + Vector3(0, 1.22, 0), f, sd, 0.38, 0.34, 0.3, Color(0.23, 0.24, 0.26))
				_box(st, p + Vector3(0, 1.3, 0) + Vector3(f.x, 0, f.y) * 0.151, f, sd, 0.26, 0.02, 0.005, Color(0.08, 0.08, 0.08))
				var c3: Vector3 = p + Vector3(f.x, 0, f.y) * 0.152 + Vector3(0, 1.16, 0)    # name plate
				var sv3 := Vector3(sd.x, 0, sd.y) * 0.08
				var uv3 := Vector3(0, 0.025, 0)
				_quad_c(st, c3 - sv3 - uv3, c3 + sv3 - uv3, c3 + sv3 + uv3, c3 - sv3 + uv3, Vector3(f.x, 0, f.y), Color(0.85, 0.85, 0.8))
	if _mark_mat == null:
		_mark_mat = StandardMaterial3D.new()
		_mark_mat.vertex_color_use_as_albedo = true
		_mark_mat.roughness = 0.8
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _mark_mat
	mi.layers = 1
	mi.visibility_range_end = vis
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


static func lampen_licht(m, bib, parent: Node3D, near := Vector3.ZERO, nmax := 6, rmax := 90.0) -> int:
	"""die Lichter der Strassenlampen einer Bib: OmniLight (12 m, warm) wie die Lampen der Plätze - licht.gd schaltet sie in
	der Dämmerung ein (main.lamps), die Leuchte glüht (glow_mat). Nur die nächsten nmax (HD 4600)."""
	var near_l := []
	for l in bib.lamps:
		var wp: Vector3 = bib.to_world * (l[0] as Vector3)
		if wp.distance_to(near) < rmax:
			near_l.append([wp.distance_to(near), l])
	near_l.sort_custom(func(a, b): return a[0] < b[0])
	var n := mini(nmax, near_l.size())
	for i in range(n):
		var l: Array = near_l[i][1]
		var ol := OmniLight3D.new()
		ol.position = l[0]
		ol.light_color = Color(1.0, 0.82, 0.55)
		ol.omni_range = 12.0
		ol.light_energy = 0.0
		ol.shadow_enabled = false
		parent.add_child(ol)
		m.lamps.append(ol)
	return n


static func camping_strassenrand(sc) -> void:
	"""Camping-Platz an der Strasse (nur Normal / Hoch, nach den Pflanzen; nichts davon ist ein Hindernis - die Szene bleibt
	gleich): zwei Strassenlampen vor dem Platz (leuchten nachts), Bank beim Wegweiser, Robidog-artiger Kasten beim Wanderweg,
	Briefkasten an der Einfahrt, Leitpfosten ausserhalb, Leitplanke gegenüber, ein Weidezaun am Wanderweg"""
	var m = sc.m
	var road_c := float(sc.data.get("road_z", -27.8)) - 1.2
	var hw := 2.5
	var Bib = load("res://scripts/bib_berg.gd")
	var bib = Bib.new(m, sc, sc.root, Transform3D.IDENTITY)
	var gy := func(x: float, z: float) -> Vector3: return Vector3(x, m.ground_y(x, z), z)
	for x in [-17.0, 9.0]:                                 # street lamps on the side of the place, arm over the road
		bib.add("lamp", gy.call(x, road_c + hw + 0.9), PI / 2.0, {"style": "street", "noob": true})
	bib.add("bench", gy.call(-26.6, road_c + hw + 2.3), PI, {"noob": true})
	for k in range(4):                                     # guardrail on the other side, where the meadow falls away
		bib.add("guardrail", gy.call(32.0 + k * 4.0, road_c - hw - 0.7), 0.0, {"len": 4.0, "noob": true})
	var trail_dir := (CAMP_TRAIL[9] - CAMP_TRAIL[8]).normalized()
	for k in range(5):                                     # a pasture fence west of the trail in the field
		var q: Vector2 = CAMP_TRAIL[7] + Vector2(-4.0, 0.0) + trail_dir * (2.5 * k + 1.25)
		bib.add("fence", gy.call(q.x, q.y), atan2(-trail_dir.y, trail_dir.x), {"len": 2.5, "h": 1.1, "noob": true})
	bib.finish()
	lampen_licht(m, bib, sc.root)
	var list := []
	for side in [-1.0, 1.0]:                               # delineators every 50 m outside the place (both sides)
		for x in [-145.0, -95.0, -45.0, 45.0, 95.0, 145.0]:
			var z: float = road_c + float(side) * (hw + 0.85)
			list.append(["leitpfosten", gy.call(x, z), 0.0 if side > 0.0 else PI])
	list.append(["robidog", gy.call(-18.2, -12.2), deg_to_rad(-30.0)])
	list.append(["briefkasten", gy.call(3.2, road_c + hw + 1.4), PI])
	kleinzeug(m, sc.root, list)


# ---- gelbe Parkfelder am Strassenrand (Ort von der Karte: wo geo.gd Autos parkiert) ------------------------------------------
static func park_streifen(m, parent: Node3D, segs: Array) -> int:
	"""segs = [[a, b, halbe Breite der Strasse]] - auf beiden Seiten ein Parkstreifen (Asphalt, gelbe Felder längs, 5.5 m) genau
	dort, wo geo.gd die Autos abstellt (Mitte halbe Breite + 1.3 m). Ein Netz, ein Zeichenaufruf."""
	var st := SurfaceTool.new()
	var n := 0
	for sg in segs:
		var a: Vector2 = sg[0]
		var b: Vector2 = sg[1]
		if a.distance_to(b) < 5.0:
			continue
		var d := (b - a).normalized()
		var side := Vector2(-d.y, d.x)
		for sgn in [-1.0, 1.0]:
			var off: Vector2 = side * sgn * (float(sg[2]) + 1.3)
			var line := dense([a + off + d * 0.5, b + off - d * 0.5], 3.0)
			st.append_from(band(m, line, 1.1, 0.0, 0.06, COLS_FELD), 0, Transform3D.IDENTITY)
			n += 1
	if n == 0:
		return 0
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = strasse_mat(m, {"centre": false, "edge": false, "bays": 1, "bay_col": GELB})
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return n
