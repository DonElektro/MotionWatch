extends RefCounted
## «Flora und Fauna» Paket 1 – Bäume und Sträucher mit echten Ästen (Freigabe des Besitzers, erster Meilenstein):
## Fichte, Buche, Hasel. Aufgerufen von flora.gd (Flora.dress mit Art), nur in den Stufen Normal und Hoch.
##
##   - Äste: zu jedem Baum ein Gerüst aus Röhren (Stamm, Astquirle bzw. Hauptäste + Seitenäste), das genau in die alten
##     Kronen-Teile (Kugeln / Kegel) hineinwächst. Alle Äste einer Zelle (32 m) sind EIN Mesh mit EINEM Rinden-Material
##     (shaders/rinde.gdshader, Muster je Art aus der Farbe der Ecke) – wenige Zeichenaufrufe auch auf dem HP.
##   - Blätter / Nadeln: Büschel aus Karten (shaders/baum_karten.gdshader, Alpha-Test) an den Astenden, Bilder je Art im
##     Code gezeichnet (Fichtenzweig, Buchenzweig, Haselzweig). Ein MultiMesh pro Art und Zelle; die Farbe, Jahreszeit
##     (kahl, Blüte) und der Wind kommen aus den Kronen-Materialien (Liste in der Karte, jede Viertelsekunde abgeglichen).
##   - Kern: die alten Kronen-Teile bleiben als kleinerer, dunkler Kern sichtbar (verdeckt Lücken, kahl im Winter weg).
##   - Ferne: ab NAH (Normal 45 m, Hoch 90 m) zeigt jeder Baum statt Ästen / Karten / Kern ein flaches Bild, das sich zur
##     Kamera dreht (shaders/baum_fern.gdshader, Bild texturen/flora_fern_<art>.png, mit werkzeuge/flora_fernbilder.gd aus
##     genau diesen Bäumen gerendert). Wechsel pro Baum im Shader (gleicher Abstand für alle Teile eines Baums).
##
## Unverändert (Invarianten): Hindernisse, tree_spots, die Kronen-Teile selbst (Lage, Grösse, Material-Zwilling im
## Wärmebild, Ebene 2), sc.rng (eigener Zufall mit Startwert aus dem Ort). Die alten Stämme werfen weiter den Schatten
## (nur Schatten, bis NAH); die neuen Teile sind nur auf Ebene 1.

const ARTEN := ["fichte", "buche", "hasel"]
const CELL := 32.0
# Ferne-Bilder: Breite / Höhe des Bild-Rahmens in m bei Grösse 1 (aus werkzeuge/flora_fernbilder.gd)
const FERN := {"fichte": Vector2(4.6, 7.6), "buche": Vector2(5.6, 7.4), "hasel": Vector2(3.6, 3.1)}
# Rinde: Farbe (rgb) + Muster (a: 0.1 Fichte schuppig, 0.4 Buche glatt grau, 0.7 Hasel glatt mit Korkporen)
const RINDE := {"fichte": Color(0.36, 0.25, 0.19, 0.1), "buche": Color(0.34, 0.34, 0.32, 0.4), "hasel": Color(0.45, 0.38, 0.31, 0.7)}

static var _tex := {}
static var _imp_mesh: ArrayMesh = null
static var last := {}                # the last tree built (for werkzeuge/flora_fernbilder.gd)


static func nah(st: String) -> float:
	return 90.0 if st == "hoch" else 45.0


# ---- Gerüst ------------------------------------------------------------------------------------------------------------
static func _cell(job: Dictionary, p: Vector3, size := CELL) -> Vector2i:
	return Vector2i(floori(p.x / size), floori(p.z / size))


static func _bark_buf(bm: Dictionary, _p: Vector3) -> Dictionary:
	var key: Vector2i = bm["cur"]                              # the cell of the tree's foot: a tree stays together
	if not bm["bark"].has(key):
		bm["bark"][key] = {"v": PackedVector3Array(), "n": PackedVector3Array(), "uv": PackedVector2Array(), "uv2": PackedVector2Array(),
				"c": PackedColorArray(), "cu": PackedFloat32Array(), "i": PackedInt32Array()}
	return bm["bark"][key]


static func _tube(B: Dictionary, pts: Array, rads: Array, sides: int, col: Color, ctr: Vector3, ups: Array, wts: Array) -> void:
	"""eine Röhre durch pts (Raum der Szene) mit Radien rads; ups / wts = Höhe im Kronen-Teil + 1 und Wind-Gewicht je Punkt"""
	var n := pts.size()
	if n < 2:
		return
	var base: int = B["v"].size()
	var vlen := 0.0
	var bx := Vector3.ZERO
	for i in range(n):
		var t: Vector3
		if i == 0:
			t = pts[1] - pts[0]
		elif i == n - 1:
			t = pts[i] - pts[i - 1]
		else:
			t = pts[i + 1] - pts[i - 1]
		t = t.normalized()
		if i == 0:
			var ref := Vector3.UP if absf(t.y) < 0.9 else Vector3.RIGHT
			bx = ref.cross(t).normalized()
		else:
			vlen += (pts[i] as Vector3).distance_to(pts[i - 1])
			bx = (bx - t * bx.dot(t)).normalized()             # carried along: no twist
		var by := t.cross(bx)
		for s in range(sides + 1):
			var a := TAU * s / sides
			var nn := bx * cos(a) + by * sin(a)
			B["v"].append(pts[i] + nn * float(rads[i]))
			B["n"].append(nn)
			B["uv"].append(Vector2(float(s) / sides, vlen))
			B["uv2"].append(Vector2(float(wts[i]), float(rads[i])))
			B["c"].append(col)
			B["cu"].append_array([ctr.x, ctr.y, ctr.z, float(ups[i])])
	for i in range(n - 1):
		for s in range(sides):
			var a0 := base + i * (sides + 1) + s
			var b0 := a0 + sides + 1
			B["i"].append_array([a0, b0, a0 + 1, a0 + 1, b0, b0 + 1])


static func _curve(a: Vector3, b: Vector3, bend: Vector3, steps: int) -> Array:
	"""Punkte von a nach b, in der Mitte um bend ausgebogen"""
	var out := []
	for i in range(steps + 1):
		var u := float(i) / steps
		out.append(a.lerp(b, u) + bend * (4.0 * u * (1.0 - u)))
	return out


static func _up_in(parts: Array, p: Vector3) -> float:
	"""Höhe im nächsten Kronen-Teil + 1 (wie «up» in foliage.gdshader: Teil-Raum, ohne Grösse des Baums)"""
	var best := 1e9
	var up := 1.0
	for pt in parts:
		var d: float = (pt["t"].origin as Vector3).distance_squared_to(p)
		if d < best:
			best = d
			up = (pt["t"].affine_inverse() * p).y + 1.0
	return up


# ---- Karten ------------------------------------------------------------------------------------------------------------
static func _card(bm: Dictionary, art: String, pos: Vector3, b: Basis, ctr: Vector3, up: float, k: int) -> void:
	var key: Vector2i = bm["cur"]
	var lists: Dictionary = bm["cards"]
	if not lists.has(art):
		lists[art] = {}
	if not lists[art].has(key):
		lists[art][key] = []
	lists[art][key].append([Transform3D(b, pos), Color(ctr.x - pos.x, ctr.y - pos.y, ctr.z - pos.z, clampf(up, 0.0, 2.0) + 4.0 * k)])


static func _basis_y(ydir: Vector3, face: Vector3, w: float, h: float) -> Basis:
	"""Karte mit «oben» des Bildes entlang ydir, Fläche möglichst zu face gedreht; Breite w, Höhe h"""
	var y := ydir.normalized()
	var z := (face - y * face.dot(y))
	if z.length() < 0.01:
		z = Vector3.UP.cross(y) if absf(y.y) < 0.9 else Vector3.RIGHT
	z = z.normalized()
	var x := y.cross(z).normalized()
	return Basis(x * w, y * h, z * w)


static func _tuft(bm: Dictionary, art: String, r: RandomNumberGenerator, tip: Vector3, dir: Vector3, out: Vector3, sz: float,
		ctr: Vector3, parts: Array, k: int, cards := 2) -> void:
	"""ein Büschel am Astende: «cards» Karten, um die Astrichtung gedreht, Zweig-Ansatz am Astende"""
	var up := _up_in(parts, tip)
	var d := (dir.normalized() * 0.6 + out.normalized() * 0.4).normalized()
	for c in range(cards):
		var face := out.rotated(d, (float(c) / cards) * PI + r.randf_range(-0.3, 0.3))
		var b := _basis_y(d, face, sz, sz)
		_card(bm, art, tip + d * sz * 0.42, b, ctr, up, k)


# ---- die Arten ---------------------------------------------------------------------------------------------------------
static func _fichte(bm: Dictionary, r: RandomNumberGenerator, base_t: Transform3D, parts: Array, trunk_r: float, st: String, k: int, ctr: Vector3) -> Dictionary:
	var s := base_t.basis.get_scale().x
	var upv := base_t.basis.y.normalized()
	var root := base_t.origin
	var top_y := 0.0
	var bot_y := 1e9
	for pt in parts:
		var h: float = pt["h"]
		top_y = maxf(top_y, ((pt["t"].origin as Vector3) - root).dot(upv) + h * 0.5 * s)
		bot_y = minf(bot_y, ((pt["t"].origin as Vector3) - root).dot(upv) - h * 0.5 * s)
	var B := _bark_buf(bm, root)
	var col: Color = RINDE["fichte"]
	var pts := []
	var rads := []
	var ups := []
	var wts := []
	var nseg := 8
	for i in range(nseg + 1):
		var u := float(i) / nseg
		var wob := Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)) * 0.03 * s * u
		pts.append(root - upv * 0.15 * s + upv * (top_y + 0.15 * s) * u + wob)
		rads.append(lerpf(trunk_r * 1.25, 0.012 * s, pow(u, 0.8)))
		ups.append(1.0)
		wts.append(clampf((u * top_y - bot_y) / maxf(0.1, top_y - bot_y), 0.0, 1.0) * 0.4)
	_tube(B, pts, rads, 7 if st == "hoch" else 6, col, ctr, ups, wts)
	var whorls := 4 if st == "hoch" else 3
	var nb := 7 if st == "hoch" else 6
	var sprigs := 6 if st == "hoch" else 4
	for pt in parts:
		var t: Transform3D = pt["t"]
		var h: float = pt["h"]
		var rb: float = pt["r"]
		for wv in range(whorls):
			var f := lerpf(0.3, 1.0, (wv + r.randf_range(0.2, 0.8)) / whorls)    # 1 = lower edge of the layer
			var a0 := r.randf() * TAU
			for bi in range(nb):
				var a := a0 + TAU * bi / nb + r.randf_range(-0.25, 0.25)
				var lp := Vector3(0, h * 0.5 - h * f, 0)
				var start: Vector3 = t * lp
				var outl := Vector3(cos(a), 0, sin(a))
				var ln := rb * f * r.randf_range(0.85, 1.0)
				var endl := lp + outl * ln + Vector3(0, -ln * r.randf_range(0.15, 0.35), 0)
				var endw: Vector3 = t * endl
				var bend := upv * ln * s * 0.12
				var bp := _curve(start, endw, bend, 3)
				var br := clampf(0.012 + 0.02 * ln, 0.01, 0.05) * s
				_tube(B, bp, [br, br * 0.7, br * 0.45, br * 0.25], 3, col, ctr,
						[_up_in(parts, bp[0]), _up_in(parts, bp[1]), _up_in(parts, bp[2]), _up_in(parts, bp[3])], [0.25, 0.55, 0.8, 1.0])
				var dirw := (endw - start).normalized()
				var side := upv.cross(dirw).normalized()
				var csz := clampf(ln * s * 0.75, 0.4, 1.3)
				for sp in range(sprigs):                         # flat side sprigs, tilted so you see them from the side too
					var u2 := lerpf(0.35, 0.95, (sp + r.randf()) / sprigs)
					var at: Vector3 = start.lerp(endw, u2) + bend * (4.0 * u2 * (1.0 - u2))
					var sd := side * (1.0 if sp % 2 == 0 else -1.0)
					var d2 := (dirw * 0.75 + sd * 0.55 - upv * 0.15).normalized()
					var face := upv.rotated(d2, r.randf_range(0.5, 1.1) * (1.0 if r.randf() < 0.5 else -1.0))
					_card(bm, "fichte", at + d2 * csz * 0.4, _basis_y(d2, face, csz * 0.8, csz), ctr, _up_in(parts, at), k)
				# the tip and a curtain of hanging twigs below the branch (seen from the side)
				_card(bm, "fichte", endw + dirw * csz * 0.3, _basis_y(dirw + upv * 0.2, upv.rotated(dirw, r.randf_range(-0.6, 0.6)), csz * 0.8, csz),
						ctr, _up_in(parts, endw), k)
				var mid: Vector3 = start.lerp(endw, 0.7)
				_card(bm, "fichte", mid - upv * csz * 0.35, _basis_y(-upv * 0.8 + dirw * 0.4, Vector3(dirw.x, 0, dirw.z), csz * 0.9, csz * 0.9),
						ctr, _up_in(parts, mid), k)
	var topw := root + upv * top_y
	for c in range(2):                                          # the leader at the top
		var face := Vector3(cos(c * PI * 0.5), 0, sin(c * PI * 0.5))
		_card(bm, "fichte", topw - upv * 0.25 * s, _basis_y(upv, face, 0.5 * s, 0.8 * s), ctr, 2.0, k)
	return {"h": top_y, "s": s}


static func _buche(bm: Dictionary, r: RandomNumberGenerator, base_t: Transform3D, parts: Array, trunk_r: float, st: String, k: int, ctr: Vector3, art := "buche") -> Dictionary:
	"""Laubbaum (Buche) und Hasel (art = hasel: mehrere Ruten vom Boden statt Stamm)"""
	var s := base_t.basis.get_scale().x
	var upv := base_t.basis.y.normalized()
	var root := base_t.origin
	var B := _bark_buf(bm, root)
	var col: Color = RINDE[art]
	var hasel := art == "hasel"
	var top_y := 0.0
	var fork_y := 1e9
	for pt in parts:
		var cy: float = ((pt["t"].origin as Vector3) - root).dot(upv)
		top_y = maxf(top_y, cy + float(pt["ry"]))
		fork_y = minf(fork_y, cy - float(pt["ry"]) * 0.45)
	fork_y = clampf(fork_y, 1.8 * s, 3.4 * s)
	var forkw := root + upv * fork_y
	if not hasel:
		var pts := []
		var rads := []
		for i in range(6):
			var u := float(i) / 5
			pts.append(root - upv * 0.15 * s + upv * (fork_y + 0.35 * s) * u + Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)) * 0.025 * s * u)
			rads.append(lerpf(trunk_r * 1.3, trunk_r * 0.75, pow(u, 0.6)))
		_tube(B, pts, rads, 8 if st == "hoch" else 6, col, ctr, [1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0.05, 0.1])
	var nsec := (12 if st == "hoch" else 8) if not hasel else (8 if st == "hoch" else 5)
	var extra := (16 if st == "hoch" else 10) if not hasel else (10 if st == "hoch" else 6)
	var art_c := art
	for pi in range(parts.size()):
		var pt: Dictionary = parts[pi]
		var c: Vector3 = pt["t"].origin
		var rx: float = pt["rx"]
		var ry: float = pt["ry"]
		var start: Vector3
		if hasel:                                               # a rod from the ground, arching outwards (vase shape)
			var a := r.randf() * TAU
			start = root + Vector3(cos(a), 0, sin(a)) * 0.12 * s - upv * 0.05
		else:
			var a2 := r.randf() * TAU
			start = forkw + Vector3(cos(a2), 0, sin(a2)) * trunk_r * 0.4 - upv * 0.3 * s
		var endw := c + upv * ry * 0.55
		var outv := Vector3(c.x - root.x, 0, c.z - root.z)
		var bend := (outv.normalized() * 0.25 if outv.length() > 0.05 else Vector3.ZERO) * (start.distance_to(endw)) * (0.6 if hasel else 0.4)
		var lp := _curve(start, endw, bend, 4)
		var lr := 0.03 if hasel else clampf(trunk_r * 0.55, 0.05, 0.14)
		var lrad := [lr, lr * 0.85, lr * 0.65, lr * 0.45, lr * 0.25]
		if hasel:
			lrad = [lr * s, lr * 0.9 * s, lr * 0.75 * s, lr * 0.55 * s, lr * 0.3 * s]
		_tube(B, lp, lrad, 4 if hasel else (6 if st == "hoch" else 5), col, ctr,
				[_up_in(parts, lp[0]), _up_in(parts, lp[1]), _up_in(parts, lp[2]), _up_in(parts, lp[3]), _up_in(parts, lp[4])],
				[0.0, 0.25 if hasel else 0.15, 0.5, 0.8, 1.0])
		var csz := clampf(rx * (0.95 if hasel else 0.85), 0.55, 1.3)
		for j in range(nsec):                                   # side branches out to the edge of the crown part, a tuft at the end
			var u := r.randf_range(0.45, 0.95)
			var i0 := mini(3, int(u * 4.0))
			var at: Vector3 = (lp[i0] as Vector3).lerp(lp[i0 + 1], u * 4.0 - i0)
			var th := r.randf() * TAU
			var ph := acos(r.randf_range(-0.85, 1.0))         # all round: you see crowns from below and the side
			var dl := Vector3(sin(ph) * cos(th), cos(ph), sin(ph) * sin(th))
			var tip := c + Vector3(dl.x * rx, dl.y * ry, dl.z * rx) * r.randf_range(0.7, 0.86)
			var sb := (tip - at) * 0.15 + upv * 0.08 * s
			var bp := _curve(at, tip, sb, 2)
			var sr := (0.012 if hasel else 0.022) * s
			_tube(B, bp, [sr, sr * 0.6, sr * 0.3], 3, col, ctr, [_up_in(parts, at), _up_in(parts, bp[1]), _up_in(parts, tip)], [0.7, 0.85, 1.0])
			var outw := (tip - c).normalized()
			_tuft(bm, art_c, r, tip, tip - at, outw, csz, ctr, parts, k, 2)
			var mid2: Vector3 = bp[1]
			_tuft(bm, art_c, r, mid2, tip - at, outw, csz * 0.85, ctr, parts, k, 1)
		for j in range(extra):                                  # a few more leaves on the outside of the crown part
			var th2 := r.randf() * TAU
			var ph2 := acos(r.randf_range(-0.9, 1.0))
			var dl2 := Vector3(sin(ph2) * cos(th2), cos(ph2), sin(ph2) * sin(th2))
			var p2 := c + Vector3(dl2.x * rx, dl2.y * ry, dl2.z * rx) * r.randf_range(0.72, 0.9)
			_tuft(bm, art_c, r, p2 - dl2 * csz * 0.3, dl2 + upv * 0.3, dl2, csz * 0.9, ctr, parts, k, 1)
	return {"h": top_y, "s": s}


# ---- Einstieg (von Flora.dress) ----------------------------------------------------------------------------------------
static func build(sc, plant: Node3D, art: String, st: String, job: Dictionary, base_t: Transform3D, rel: Callable, kern_of: Callable) -> void:
	if not job.has("bm"):
		job["bm"] = {"bark": {}, "cards": {}, "imp": {}, "crowns": [], "st": st}
	var bm: Dictionary = job["bm"]
	bm["cur"] = _cell(bm, base_t.origin)
	var r := RandomNumberGenerator.new()
	r.seed = hash(Vector3i(roundi(base_t.origin.x * 10), roundi(base_t.origin.y * 10), roundi(base_t.origin.z * 10))) + 17
	var parts := []
	var trunk_r := 0.2 * base_t.basis.get_scale().x
	var crown: ShaderMaterial = null
	var d_near := nah(st)
	var all: Array = plant.find_children("*", "MeshInstance3D", true, false)
	for ch in all:
		var mi := ch as MeshInstance3D
		if mi.layers != 1:
			continue                                            # the thermal twins stay as they are
		var t: Transform3D = rel.call(mi)
		var fol := mi.material_override is ShaderMaterial and (mi.material_override as ShaderMaterial).shader != null \
				and (mi.material_override as ShaderMaterial).shader.resource_path.ends_with("foliage.gdshader")
		if fol:
			crown = mi.material_override
			if mi.mesh is SphereMesh:
				var sm := mi.mesh as SphereMesh
				var sv := t.basis.get_scale()
				parts.append({"t": t, "rx": sm.radius * sv.x, "ry": sm.height * 0.5 * sv.y, "h": sm.height, "r": sm.radius})
			elif mi.mesh is CylinderMesh:
				var cy := mi.mesh as CylinderMesh
				parts.append({"t": t, "h": cy.height, "r": maxf(cy.bottom_radius, cy.top_radius), "rx": 0.0, "ry": 0.0})
			mi.material_override = kern_of.call(crown, art)        # smaller, darker core (the same part: same place, same twin)
			mi.visibility_range_end = d_near
		elif mi.mesh is CylinderMesh:
			if (mi.mesh as CylinderMesh).bottom_radius * t.basis.get_scale().x > trunk_r * 0.6 and t.origin.y - base_t.origin.y < 3.0 * base_t.basis.get_scale().x:
				trunk_r = maxf((mi.mesh as CylinderMesh).bottom_radius * t.basis.get_scale().x, 0.02)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY   # the old trunk: only its shadow
			mi.visibility_range_end = d_near
	if parts.is_empty() or crown == null:
		return
	var k: int = bm["crowns"].find(crown)
	if k < 0:
		bm["crowns"].append(crown)
		k = bm["crowns"].size() - 1
	if k > 15:
		k = 15
	var ctr := Vector3.ZERO
	for pt in parts:
		ctr += pt["t"].origin
	ctr /= parts.size()
	var info: Dictionary
	if art == "fichte":
		info = _fichte(bm, r, base_t, parts, trunk_r, st, k, ctr)
	else:
		info = _buche(bm, r, base_t, parts, trunk_r if art == "buche" else 0.03, st, k, ctr, art)
	# the far picture: one quad per tree (turns to the camera in the shader)
	last = {"art": art, "h": info["h"], "k": k, "crown": crown}
	var fs: Vector2 = FERN[art]
	var s: float = info["s"]
	var hy: float = float(info["h"]) / maxf(0.1, fs.y)          # as high as this tree
	var flip := 1.0 if r.randf() < 0.5 else -1.0
	var ikey := _cell(bm, base_t.origin, CELL * 2.0)
	if not bm["imp"].has(art):
		bm["imp"][art] = {}
	if not bm["imp"][art].has(ikey):
		bm["imp"][art][ikey] = []
	bm["imp"][art][ikey].append([Transform3D(Basis().scaled(Vector3(s * flip, hy, s)), base_t.origin),
			Color(ctr.x - base_t.origin.x, ctr.y - base_t.origin.y, ctr.z - base_t.origin.z, float(k))])


# ---- in die Szene (von Flora._flush) -----------------------------------------------------------------------------------
static func flush(job: Dictionary, root: Node3D, sync: Node, noise: Texture2D) -> void:
	if not job.has("bm"):
		return
	var bm: Dictionary = job["bm"]
	var st: String = bm["st"]
	var d_near := nah(st)
	var mats := []
	var bark_m := ShaderMaterial.new()
	bark_m.shader = load("res://shaders/rinde.gdshader")
	bark_m.set_shader_parameter("noise_tex", noise)
	bark_m.set_shader_parameter("near_d", d_near)
	bark_m.set_shader_parameter("fine", 1.0 if st == "hoch" else 0.0)
	bark_m.set_shader_parameter("bark_cols", PackedColorArray([RINDE["fichte"], RINDE["buche"], RINDE["hasel"], Color(0.4, 0.3, 0.2)]))
	mats.append(bark_m)
	for key in bm["bark"]:
		var B: Dictionary = bm["bark"][key]
		if B["v"].is_empty():
			continue
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = B["v"]
		arr[Mesh.ARRAY_NORMAL] = B["n"]
		arr[Mesh.ARRAY_TEX_UV] = B["uv"]
		arr[Mesh.ARRAY_TEX_UV2] = B["uv2"]
		arr[Mesh.ARRAY_COLOR] = B["c"]
		arr[Mesh.ARRAY_CUSTOM0] = B["cu"]
		arr[Mesh.ARRAY_INDEX] = B["i"]
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr, [], {},
				Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT)
		var mi := MeshInstance3D.new()
		mi.name = "rinde"
		mi.set_meta("flora_teil", "rinde")
		mi.mesh = am
		mi.material_override = bark_m
		mi.layers = 1
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF   # the old trunks throw the shadow
		mi.visibility_range_end = d_near + CELL * 0.75
		root.add_child(mi)
	for art in bm["cards"]:
		var cm := ShaderMaterial.new()
		cm.shader = load("res://shaders/baum_karten.gdshader")
		cm.set_shader_parameter("leaf_tex", tex(art))
		cm.set_shader_parameter("noise_tex", noise)
		cm.set_shader_parameter("near_d", d_near)
		cm.set_shader_parameter("backlight_k", 0.25 if st == "hoch" else 0.15)
		cm.set_shader_parameter("twig_col", RINDE[art])
		cm.set_shader_parameter("conifer", 1.0 if art == "fichte" else 0.0)
		mats.append(cm)
		for key in bm["cards"][art]:
			var list: Array = bm["cards"][art][key]
			_mm(root, "baum_karten", list, _quad(), cm, d_near + CELL * 0.75, 0.0)
	for art in bm["imp"]:
		var im := ShaderMaterial.new()
		im.shader = load("res://shaders/baum_fern.gdshader")
		im.set_shader_parameter("imp_tex", load("res://texturen/flora_fern_%s.png" % art) if ResourceLoader.exists("res://texturen/flora_fern_%s.png" % art) else tex(art))
		im.set_shader_parameter("noise_tex", noise)
		im.set_shader_parameter("near_d", d_near)
		im.set_shader_parameter("size", FERN[art])
		im.set_shader_parameter("bark_col", RINDE[art])
		mats.append(im)
		for key in bm["imp"][art]:
			_mm(root, "baum_fern", bm["imp"][art][key], _imp(), im, 0.0, maxf(0.0, d_near - CELL * 1.5))
	sync.groups.append([bm["crowns"], mats])
	sync_group([bm["crowns"], mats])


static func _mm(root: Node3D, nm: String, list: Array, mesh: Mesh, mat: Material, vis_end: float, vis_begin: float) -> void:
	if list.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = list.size()
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	for i in range(list.size()):
		mm.set_instance_transform(i, list[i][0])
		mm.set_instance_custom_data(i, list[i][1])
		lo = lo.min(list[i][0].origin)
		hi = hi.max(list[i][0].origin)
	var mmi := MultiMeshInstance3D.new()
	mmi.name = nm
	mmi.set_meta("flora_teil", nm)
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.layers = 1
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.custom_aabb = AABB(lo - Vector3(3, 1, 3), hi - lo + Vector3(6, 12, 6))
	if vis_end > 0.0:
		mmi.visibility_range_end = vis_end
	if vis_begin > 0.0:
		mmi.visibility_range_begin = vis_begin
	root.add_child(mmi)


static var _q: QuadMesh = null


static func _quad() -> QuadMesh:
	if _q == null:
		_q = QuadMesh.new()
		_q.size = Vector2(1, 1)
	return _q


static func _imp() -> ArrayMesh:
	"""Viereck für das Ferne-Bild: x -0.5 .. 0.5, y 0 .. 1 (der Shader dreht es zur Kamera)"""
	if _imp_mesh == null:
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(0.5, 0, 0), Vector3(0.5, 1, 0), Vector3(-0.5, 1, 0)])
		arr[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
		arr[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
		arr[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 2, 1, 0, 3, 2])
		_imp_mesh = ArrayMesh.new()
		_imp_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		_imp_mesh.custom_aabb = AABB(Vector3(-4, 0, -4), Vector3(8, 12, 8))
	return _imp_mesh


# ---- Abgleich (Flora-Knoten, jede Viertelsekunde) ----------------------------------------------------------------------
const GLOBAL := ["wind", "cloud_amt", "cloud_off", "gust_amt", "dir"]


static func sync_group(g: Array) -> void:
	var crowns: Array = g[0]
	if crowns.is_empty():
		return
	var cols := PackedColorArray()
	var states := PackedColorArray()
	cols.resize(16)
	states.resize(16)
	for i in range(mini(16, crowns.size())):
		var c: ShaderMaterial = crowns[i]
		if c == null:
			continue
		var cv = c.get_shader_parameter("color")
		cols[i] = cv if cv != null else Color(0.2, 0.4, 0.15)                      # sRGB, like the crown (source_color in the shaders)
		var b = c.get_shader_parameter("bare")
		var bl = c.get_shader_parameter("blossom")
		states[i] = Color(float(b) if b != null else 0.0, float(bl) if bl != null else 0.0, 0, 0)
	var c0: ShaderMaterial = crowns[0]
	for m in g[1]:
		var sm := m as ShaderMaterial
		sm.set_shader_parameter("cols", cols)
		sm.set_shader_parameter("states", states)
		for kk in GLOBAL:
			var v = c0.get_shader_parameter(kk)
			if v != null:
				sm.set_shader_parameter(kk, v)


# ---- Zweig-Bilder (im Code gezeichnet, einmal pro Sitzung) -------------------------------------------------------------
## R = Helligkeit, G = 1 Blatt / Nadel, 0 Zweig, A = Deckung. Fuss des Zweigs unten in der Mitte (Ansatz am Ast).
static func tex(art: String) -> ImageTexture:
	if _tex.has(art):
		return _tex[art]
	var img := Image.create(256, 256, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.5, 1.0, 0.0, 0.0))
	var r := RandomNumberGenerator.new()
	r.seed = {"fichte": 1201, "buche": 1202, "hasel": 1203}.get(art, 1200)
	match art:
		"fichte":
			_draw_fichte(img, r)
		"hasel":
			_draw_laub(img, r, true)
		_:
			_draw_laub(img, r, false)
	_bleed(img)
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_tex[art] = t
	return t


static func _px(img: Image, x: int, y: int, g: float, leaf: float) -> void:
	if x >= 0 and y >= 0 and x < img.get_width() and y < img.get_height():
		img.set_pixel(x, y, Color(clampf(g, 0.0, 1.0), leaf, 0.0, 1.0))


static func _line(img: Image, a: Vector2, b: Vector2, w: float, g: float, leaf: float) -> void:
	var n := int(a.distance_to(b)) + 1
	for i in range(n + 1):
		var p := a.lerp(b, float(i) / n)
		var rr := int(ceil(w * 0.5))
		for dy in range(-rr, rr + 1):
			for dx in range(-rr, rr + 1):
				if dx * dx + dy * dy <= w * w * 0.25 + 0.3:
					_px(img, int(p.x) + dx, int(p.y) + dy, g, leaf)


static func _draw_fichte(img: Image, r: RandomNumberGenerator) -> void:
	"""Fichtenzweig: Hauptzweig vom Fuss nach oben, Seitenzweige gefiedert, Nadeln rundum (vorne heller)"""
	var base := Vector2(128, 252)
	var tip := Vector2(128 + r.randf_range(-10, 10), 14)
	var side_pts := []
	var n := 9
	for i in range(n):
		var u := lerpf(0.12, 0.92, float(i) / (n - 1))
		var p := base.lerp(tip, u)
		for sd in [-1.0, 1.0]:
			var ln := lerpf(105.0, 35.0, u) * r.randf_range(0.8, 1.05)
			var ang: float = -PI / 2 + sd * r.randf_range(0.75, 1.05)
			side_pts.append([p, p + Vector2(cos(ang), sin(ang)) * ln])
	var segs := [[base, tip]]
	segs.append_array(side_pts)
	for sg in segs:                                            # needles first (behind), the twigs on top
		var a: Vector2 = sg[0]
		var b: Vector2 = sg[1]
		var dirv := (b - a).normalized()
		var L := a.distance_to(b)
		var steps := int(L / 1.6)
		for s in range(steps):
			var u := float(s) / steps
			var p := a.lerp(b, u)
			var nl := lerpf(13.0, 7.0, u) * (1.0 if sg == segs[0] else 0.85)
			for sd in [-1.0, 1.0, -0.5, 0.5]:
				var na: float = dirv.angle() + sd * r.randf_range(0.9, 1.35)
				var g := r.randf_range(0.55, 1.0) * (0.85 if absf(sd) < 1.0 else 1.0)
				for t in range(int(nl * (0.75 if absf(sd) < 1.0 else 1.0))):
					var q := p + Vector2(cos(na), sin(na)) * t
					_px(img, int(q.x), int(q.y), g * (0.8 + 0.2 * t / nl), 1.0)
	for sg in segs:
		_line(img, sg[0], sg[1], 2.2 if sg == segs[0] else 1.4, 0.42, 0.0)


static func _leaf(img: Image, c: Vector2, ang: float, ln: float, wd: float, shade: float, serr: float, round_k: float) -> void:
	"""ein Blatt (Grauwert): Stielansatz bei c, Spitze vorne, Rand gezähnt (serr), Seitennerven"""
	var dirv := Vector2(cos(ang), sin(ang))
	var nrm := Vector2(-dirv.y, dirv.x)
	var rr := int(ceil(ln)) + 2
	var sz := img.get_size()
	for y in range(maxi(0, int(c.y) - rr), mini(sz.y, int(c.y) + rr)):
		for x in range(maxi(0, int(c.x) - rr), mini(sz.x, int(c.x) + rr)):
			var d := Vector2(x, y) - c
			var u := d.dot(dirv) / ln
			var v := d.dot(nrm)
			if u < 0.0 or u > 1.0:
				continue
			var half := wd * 0.5 * pow(sin(PI * pow(u, round_k)), 0.8)
			half *= 1.0 - serr * (0.5 + 0.5 * sin(u * 70.0))                 # teeth
			if absf(v) > half:
				continue
			var vein := absf(fposmod(u * 9.0 - absf(v) / maxf(wd, 1.0) * 5.0, 1.0) - 0.5) < 0.08
			var g := shade * (0.8 + 0.25 * (absf(v) / maxf(half, 0.01)))
			if absf(v) < 0.8 or vein:
				g = minf(1.0, g * 1.18)
			_px(img, x, y, g, 1.0)


static func _draw_laub(img: Image, r: RandomNumberGenerator, hasel: bool) -> void:
	"""Laubzweig: Zickzack-Zweig vom Fuss nach oben, Blätter wechselständig (Buche: oval, glatt; Hasel: rund, gezähnt)"""
	var twigs := []
	var base := Vector2(128, 252)
	var main_tip := Vector2(128 + r.randf_range(-18, 18), 20)
	twigs.append([base, main_tip])
	for i in range(2):
		var u := 0.35 + 0.25 * i
		var p := base.lerp(main_tip, u)
		var sd := -1.0 if i == 0 else 1.0
		twigs.append([p, p + Vector2(sd * r.randf_range(70, 95), -r.randf_range(70, 100))])
	var leaves := []
	for tw in twigs:
		var a: Vector2 = tw[0]
		var b: Vector2 = tw[1]
		var n := 5 if hasel else 7
		for j in range(n):
			var u := lerpf(0.25, 1.0, float(j) / (n - 1))
			var p := a.lerp(b, u)
			var sd: float = 1.0 if j % 2 == 0 else -1.0
			var ang: float = (b - a).angle() + sd * r.randf_range(0.6, 1.0)
			if j == n - 1:
				ang = (b - a).angle()
			var ln := r.randf_range(52, 62) if hasel else r.randf_range(40, 50)
			var wd := ln * (0.85 if hasel else 0.58)
			leaves.append([p, ang, ln, wd, r.randf_range(0.6, 1.0)])
	for tw in twigs:
		_line(img, tw[0], tw[1], 2.2, 0.4, 0.0)
	leaves.sort_custom(func(x, y): return x[4] < y[4])      # darker ones behind
	for lf in leaves:
		_leaf(img, lf[0], lf[1], lf[2], lf[3], lf[4], 0.12 if hasel else 0.015, 0.55 if hasel else 0.8)


static func _bleed(img: Image) -> void:
	"""Farbe unter den durchsichtigen Pixeln = Nachbar (keine dunklen Ränder in den kleinen Mipmaps); Deckung bleibt 0"""
	var w := img.get_width()
	var h := img.get_height()
	var done := PackedByteArray()
	done.resize(w * h)
	for y in range(h):
		for x in range(w):
			done[y * w + x] = 1 if img.get_pixel(x, y).a > 0.0 else 0
	for it in range(3):
		var src := img.duplicate() as Image
		var now := done.duplicate()
		for y in range(h):
			for x in range(w):
				if done[y * w + x] != 0:
					continue
				for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
					var q: Vector2i = Vector2i(x, y) + o
					if q.x >= 0 and q.y >= 0 and q.x < w and q.y < h and done[q.y * w + q.x] != 0:
						var c := src.get_pixel(q.x, q.y)
						img.set_pixel(x, y, Color(c.r, c.g, c.b, 0.0))
						now[y * w + x] = 1
						break
		done = now
