extends RefCounted
## Maggie aus Grundformen, «einfach» (Grafik «einfach» / Lite, Raspberry Pi; Besitzer 01.11.2026): statt einzelner Kugeln und
## Kapseln weiche, zusammenhängende Körper aus Querschnitten (Rumpf mit tiefer Brust, aufgezogenem Bauch und Kruppe; Hals;
## Kopf mit Stopp und Wangen; schlanke Läufe; ein durchgehend gebogener Schwanz; gefaltete Kippohren). Maggies Muster steht
## als Vertex-Farbe im Netz (keine aufgesetzten Flecken). Ein Material für das ganze Fell.
## Gleiche Schnittstelle und gleiche Masse wie bisher (maggie_hund._maggie_koerper): Hüft- / Schultergelenke, Hand- und
## Sprunggelenk, Kopf-Gelenk am Halsansatz, Schwanzwurzel, Marken der Pfoten.

const WEISS := Color(0.9, 0.885, 0.85)
const BRAUN := Color(0.6, 0.4, 0.24)
const KOPF := Color(0.68, 0.48, 0.3)
const OHR := Color(0.56, 0.36, 0.22)
const SCHNAUZE := Color(0.86, 0.84, 0.8)

var seg := 12                        # Punkte pro Querschnitt


static func _sst(a: float, b: float, x: float) -> float:
	return smoothstep(a, b, x)


static func _mix(c1: Color, c2: Color, t: float) -> Color:
	return c1.lerp(c2, clampf(t, 0.0, 1.0))


func rohr(st: Array, farbe: Callable) -> ArrayMesh:
	"""ein weicher Körper aus Querschnitten: st = [[Mitte, rx, ry], …] entlang eines Wegs; rx quer (seitlich), ry «oben».
	Die Enden laufen zu einem Punkt zusammen. farbe(punkt) -> Color (Muster)."""
	var s := SurfaceTool.new()
	s.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := st.size()
	var pts := []
	var nrm := []
	for i in range(n):
		var c: Vector3 = st[i][0]
		var t: Vector3 = ((st[mini(i + 1, n - 1)][0] as Vector3) - (st[maxi(i - 1, 0)][0] as Vector3)).normalized()
		var side := Vector3.RIGHT                            # alle Wege liegen in einer y-z-Ebene: quer ist immer x
		var up := t.cross(side).normalized()
		var rx: float = maxf(float(st[i][1]), 0.0005)
		var ry: float = maxf(float(st[i][2]), 0.0005)
		for j in range(seg):
			var w := TAU * float(j) / float(seg)
			pts.append(c + side * rx * cos(w) + up * ry * sin(w))
			var nv := side * cos(w) / rx + up * sin(w) / ry
			if i == 0 or i == n - 1:
				nv = nv.normalized() * 0.3 + t * (-1.0 if i == 0 else 1.0)
			nrm.append(nv.normalized())
	for k in range(pts.size()):
		s.set_color(farbe.call(pts[k]))
		s.set_normal(nrm[k])
		s.add_vertex(pts[k])
	# Umlaufsinn passend zu den Normalen (sonst wäre die Fläche von innen beleuchtet)
	var i0 := seg * (n / 2)
	var geo := ((pts[i0 + seg] as Vector3) - (pts[i0] as Vector3)).cross((pts[i0 + 1] as Vector3) - (pts[i0] as Vector3))
	var flip := geo.dot(nrm[i0]) < 0.0
	for i in range(n - 1):
		for j in range(seg):
			var a := i * seg + j
			var b := i * seg + (j + 1) % seg
			var c2 := (i + 1) * seg + j
			var d := (i + 1) * seg + (j + 1) % seg
			var tri := [a, c2, b, b, c2, d] if not flip else [a, b, c2, b, d, c2]
			for x in tri:
				s.add_index(x)
	return s.commit()


func material() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.roughness = 0.85
	m.rim_enabled = true
	m.rim = 0.3
	m.rim_tint = 0.55
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


# ---- die Muster (Raum maggie_koerper, Meter; vorne = -z, Boden y = 0) --------------------------------------------------
static func rumpf_farbe(p: Vector3) -> Color:
	var platte := pow(p.z / 0.105, 2.0) + pow((p.y - 0.335) / 0.092, 2.0)
	var kruppe := pow((p.z - 0.165) / 0.075, 2.0) + pow((p.y - 0.3) / 0.105, 2.0)
	var oben := _sst(0.312, 0.322, p.y) * _sst(-0.045, -0.03, p.z)
	var b := maxf(maxf(1.0 - _sst(0.8, 1.05, platte), 1.0 - _sst(0.8, 1.05, kruppe)), oben)
	var tupfen := 1.0 - _sst(0.5, 1.0, pow((p.x - 0.008) / 0.016, 2.0) + pow((p.z - 0.04) / 0.02, 2.0))
	b *= 1.0 - tupfen * _sst(0.31, 0.325, p.y)
	return _mix(WEISS, BRAUN, b)


static func hals_farbe(p: Vector3) -> Color:
	# Raum des Kopf-Gelenks: Kehle (vorne / unten) weiss, sonst braun wie der Kopf
	var d := -p.z * 0.6 - p.y * 0.8 + 0.035
	return _mix(KOPF, WEISS, _sst(0.025, 0.042, d))


static func kopf_farbe(p: Vector3, hc: Vector3) -> Color:
	var q := p - hc
	var schnauze := _sst(-0.045, -0.06, q.z) * maxf(1.0 - _sst(0.0, 0.012, q.y), _sst(-0.07, -0.085, q.z))
	var kinn := _sst(-0.01, -0.025, q.y) * _sst(-0.02, -0.035, q.z)
	var blesse := (1.0 - _sst(0.004, 0.009, absf(q.x))) * _sst(0.02, 0.0, q.z) * _sst(-0.065, -0.04, q.z) * _sst(0.012, 0.025, q.y)
	var w := clampf(schnauze + kinn + blesse, 0.0, 1.0)
	return _mix(KOPF, SCHNAUZE if schnauze > 0.5 else WEISS, w)


# ---- die Teile ----------------------------------------------------------------------------------------------------------
func rumpf() -> ArrayMesh:
	var st := [
		[Vector3(0, 0.236, -0.178), 0.006, 0.008], [Vector3(0, 0.238, -0.168), 0.03, 0.04], [Vector3(0, 0.243, -0.15), 0.048, 0.064],
		[Vector3(0, 0.248, -0.118), 0.058, 0.078], [Vector3(0, 0.252, -0.07), 0.062, 0.08], [Vector3(0, 0.262, -0.02), 0.06, 0.068],
		[Vector3(0, 0.276, 0.03), 0.055, 0.05], [Vector3(0, 0.281, 0.08), 0.052, 0.046], [Vector3(0, 0.283, 0.13), 0.055, 0.05],
		[Vector3(0, 0.279, 0.17), 0.05, 0.047], [Vector3(0, 0.274, 0.196), 0.034, 0.035], [Vector3(0, 0.271, 0.207), 0.008, 0.008]]
	return rohr(st, rumpf_farbe)


func hals(hc: Vector3) -> ArrayMesh:
	var st := [[Vector3(0, -0.03, 0.03), 0.01, 0.01], [Vector3(0, -0.02, 0.018), 0.04, 0.046], [Vector3(0, 0.01, -0.01), 0.038, 0.044],
		[hc * 0.6, 0.034, 0.038], [hc * 0.85 + Vector3(0, -0.005, 0.01), 0.034, 0.036], [hc + Vector3(0, -0.006, 0.02), 0.02, 0.022]]
	return rohr(st, hals_farbe)


func kopf(hc: Vector3) -> ArrayMesh:
	var st := [
		[hc + Vector3(0, 0.004, 0.052), 0.012, 0.012], [hc + Vector3(0, 0.005, 0.042), 0.034, 0.036],
		[hc + Vector3(0, 0.006, 0.018), 0.046, 0.044], [hc + Vector3(0, 0.004, -0.014), 0.046, 0.042],
		[hc + Vector3(0, -0.006, -0.038), 0.034, 0.03], [hc + Vector3(0, -0.013, -0.058), 0.024, 0.022],
		[hc + Vector3(0, -0.015, -0.078), 0.019, 0.018], [hc + Vector3(0, -0.015, -0.092), 0.015, 0.014],
		[hc + Vector3(0, -0.015, -0.099), 0.006, 0.006]]
	return rohr(st, func(p): return kopf_farbe(p, hc))


func lauf(oben: Vector3, unten: Vector3, r_oben: Vector2, r_mitte: Vector2, r_unten: Vector2, farbe: Callable) -> ArrayMesh:
	"""ein Lauf-Stück von oben nach unten (Raum des Gelenks), r = (quer, längs)"""
	var d := unten - oben
	var st := [[oben + d * -0.08, r_oben.x * 0.4, r_oben.y * 0.4], [oben + d * 0.02, r_oben.x, r_oben.y],
		[oben + d * 0.45, r_mitte.x, r_mitte.y], [oben + d * 0.92, r_unten.x, r_unten.y], [oben + d * 1.06, r_unten.x * 0.5, r_unten.y * 0.5]]
	return rohr(st, farbe)


func schwanz() -> ArrayMesh:
	"""ein durchgehend gebogener Schwanz (Bezier): steil nach oben, die Spitze biegt nach vorne; aussen braun, Spitze weiss"""
	var p0 := Vector3(0, -0.005, -0.012)
	var p1 := Vector3(0, 0.06, 0.04)
	var p2 := Vector3(0, 0.15, 0.03)
	var p3 := Vector3(0, 0.165, -0.025)
	var st := []
	var n := 12
	for i in range(n + 1):
		var t := float(i) / float(n)
		var u := 1.0 - t
		var p := p0 * u * u * u + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t * t * t
		var r := lerpf(0.018, 0.0075, t) if i < n else 0.002
		st.append([p, r, r * 0.95])
	var tip_y := 0.13
	return rohr(st, func(p): return _mix(BRAUN, WEISS, _sst(tip_y - 0.012, tip_y + 0.012, p.y + p.z * 0.4)))


func ohr(s: float, hc: Vector3) -> ArrayMesh:
	"""Kippohr: der Ansatz steht, ab der Mitte fällt der Lappen nach vorne / unten (Spitze zum äusseren Augenwinkel)"""
	var reihen := [
		[hc + Vector3(0.026 * s, 0.036, 0.006), hc + Vector3(0.036 * s, 0.03, -0.02)],    # Ansatz (hinten, vorne)
		[hc + Vector3(0.04 * s, 0.056, 0.002), hc + Vector3(0.047 * s, 0.054, -0.024)],   # Knick
		[hc + Vector3(0.052 * s, 0.014, -0.03), hc + Vector3(0.05 * s, 0.01, -0.04)],     # Spitze (vorne unten)
	]
	var sf := SurfaceTool.new()
	sf.begin(Mesh.PRIMITIVE_TRIANGLES)
	for r in reihen:
		for p in r:
			sf.set_color(OHR)
			sf.add_vertex(p)
	for i in range(2):
		var a := i * 2
		for idx in [a, a + 2, a + 1, a + 1, a + 2, a + 3]:
			sf.add_index(idx)
	sf.generate_normals()
	return sf.commit()
