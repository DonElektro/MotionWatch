extends Node
## 3D-4.x «Gelände & Pflanzen» (Zweig real-gelaende, 31.10.2026): leichte Hügel und Senken statt flachem Boden, Wege aus Kies
## und Erde, Wolkenschatten, die über den Boden ziehen. Die Pflanzen (Gras, Blumen, Büsche, Hecken, Bäume) baut vegetation.gd.
## Knoten `main.gelaende` (vor _build_world angelegt, damit die erste Szene es schon hat), Einstellungen in user://gelaende.json.
##
## API für Szenen (auch andere Pakete: Ferienpark, Bergtal …) – alles im Bau der Szene (scenes.gd), Reihenfolge wichtig:
##   var G = m.gelaende
##   if G.relief_wanted():                                     # Schalter «Gelände: Hügel und Senken» (Szene)
##       G.setup_relief({"amp": 0.9, "scale": 34.0, "seed": 3,
##               "flat": [[Vector2(0, 0), 11.0, 8.0]],         # flach: [Mitte, Radius, Übergang] (dein Platz, Gebäude …)
##               "bands": [["z", -29.0, 3.5, 6.0]],           # flach entlang einer Linie: [Achse, Wert, halbe Breite, Übergang]
##               "dips": [[Vector2(14, -18), 5.0, 0.8]],       # Senke: [Mitte, Radius, Tiefe] (negativ = Hügel)
##               "half": 120.0})                              # Grösse des Geländes (± m), aussen flach bei y = 0
##       G.build_ground(sc.root)                               # Boden-Gitter mit dem Gras-Material (Schnee, Nässe, Pfützen wirken)
##   G.path(sc.root, [Vector2(0, -27), Vector2(1, -15), Vector2(0, -6)], 1.6, "kies")   # Weg «kies» / «erde» / «platten»
##   m.ground_y(x, z)                                          # Höhe des Bodens (Gelände, sonst 0, am echten Ort geo.gd)
##   G.on_path(Vector2(x, z), 0.5) -> bool                     # liegt der Punkt auf einem Weg (+ Rand)? (kein Gras dort)
## Danach stellt man alles mit m.ground_y() auf den Boden (vegetation.gd, scenes.prop, tree, stones machen das selbst).
## Ohne setup_relief bleibt der Boden flach (alle anderen Szenen unverändert); Wege gehen auch auf flachem Boden.
## Besucher, Figuren und Spieler folgen dem Gelände über m.hilly() (actor.gd, figur.gd); die Sichtlinie des Spiels
## (main.line_blocker) und die Wahrheit «verdeckt» rechnen Hügel mit.
##
## Wolkenschatten (Schalter «Wolkenschatten» in Wetter → Mehr Wetter, gab es schon: cloud_shade): bei Bewölkung ziehen
## Schatten-Flecken mit dem Wind über Boden, Wege, Gras und Baumkronen (Uniform cloud_amt / cloud_off in grass, foliage,
## pfad, gras_halme). Die Helligkeit am Kopf (main.cloud_shade) folgt dann demselben Fleck (cloud_here), damit Bild und
## Licht zusammenpassen. Nur in Szenen mit Gelände (relief), sonst wie bisher.
##
## Test: /control {"action": "gelaende", "do": info | set (key, value) | height (x, z) | los (from [x,y,z], to [x,y,z]) | cloud (x, z)
##        | walk (kind, from [x,z], to [x,z]) – ein Besucher, z. B. hinter der Hecke}

const Quality = preload("res://scripts/quality.gd")
const FILE := "user://gelaende.json"
const SAVE := ["g_relief", "g_plants"]
var main
var g_relief := true          # Szenen mit Gelände bekommen Hügel und Senken (Camping-Platz)
var g_plants := true          # mehr Pflanzen: Büsche, Hecken, Bäume verschiedener Arten, Blumen (vegetation.gd)

var on := false               # die jetzige Szene hat Gelände
var half := 120.0
var step := 2.0
var n := 0
var h := PackedFloat32Array()
var hmin := 0.0
var hmax := 0.0
var paths: Array = []         # [PackedVector2Array Mittellinie, halbe Breite, Art]
var path_mats: Array = []
var ground_node: MeshInstance3D = null

const CLOUD_SCALE := 0.0035   # 1 / Grösse der Wolken-Flecken (Textur 0..1 auf ~285 m)
var cloud_off := Vector2(37.0, 11.0)
var cloud_amt := 0.0
var _cloud_img: Image = null
var _t := 0.0


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, bool(d[k]))


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _put(k: String, v) -> void:
	set(k, v)
	save()
	if main != null and main.has_method("set_scene"):
		main.set_scene.call_deferred(main.scene)       # neu bauen (Hügel / Pflanzen kommen oder gehen)


func add_controls() -> void:
	main.add_control("toggle", "g_relief", "Gelände: leichte Hügel und Senken statt flachem Boden (Camping-Platz; baut die Szene neu)",
			func(): return g_relief, func(v): _put("g_relief", bool(v)), "Szene", {"sub": ""})
	main.add_control("toggle", "g_plants", "Mehr Pflanzen: Büsche, Hecken, Bäume verschiedener Arten, Blumen und Wege (Camping-Platz; baut die Szene neu)",
			func(): return g_plants, func(v): _put("g_plants", bool(v)), "Szene", {"sub": ""})


func relief_wanted() -> bool:
	return g_relief


func plants_wanted() -> bool:
	return g_plants


# ---- the scene -------------------------------------------------------------------------------------------------------
func reset() -> void:
	"""vor dem Bau jeder Szene (main._build_scene): flach, keine Wege"""
	on = false
	veg_mats.clear()
	n = 0
	h = PackedFloat32Array()
	hmin = 0.0
	hmax = 0.0
	paths.clear()
	path_mats.clear()
	ground_node = null


func on_scene() -> void:
	"""nach dem Bau: mit Gelände den flachen Boden von main ausblenden (das eigene Gitter deckt alles bis zum Horizont)"""
	if on and main.flat_nodes.size() >= 2:
		main.flat_nodes[0].visible = false
		main.flat_nodes[1].visible = false
	_apply_cloud(true)


func setup_relief(o: Dictionary) -> void:
	half = float(o.get("half", 120.0))
	step = float(o.get("step", 2.0))
	n = int(round(2.0 * half / step)) + 1
	h.resize(n * n)
	var amp := float(o.get("amp", 0.9))
	var fn := FastNoiseLite.new()
	fn.seed = int(o.get("seed", 3))
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 1.0 / float(o.get("scale", 34.0))
	fn.fractal_octaves = 3
	fn.fractal_gain = 0.35
	var flat: Array = o.get("flat", [])
	var bands: Array = o.get("bands", [])
	var dips: Array = o.get("dips", [])
	hmin = 0.0
	hmax = 0.0
	for j in range(n):
		for i in range(n):
			var x := -half + i * step
			var z := -half + j * step
			var v := fn.get_noise_2d(x, z) * amp * 1.6
			for dp in dips:
				var dd: float = Vector2(x, z).distance_to(dp[0])
				if dd < float(dp[1]):
					v -= float(dp[2]) * (0.5 + 0.5 * cos(PI * dd / float(dp[1])))
			var k := 1.0 - smoothstep(half - 30.0, half - 4.0, maxf(absf(x), absf(z)))
			for f in flat:
				k = minf(k, smoothstep(float(f[1]), float(f[1]) + float(f[2]), Vector2(x, z).distance_to(f[0])))
			for b in bands:
				var dist := absf((z if str(b[0]) == "z" else x) - float(b[1]))
				k = minf(k, smoothstep(float(b[2]), float(b[2]) + float(b[3]), dist))
			v *= k
			h[j * n + i] = v
			hmin = minf(hmin, v)
			hmax = maxf(hmax, v)
	on = true


func height(x: float, z: float) -> float:
	if not on or absf(x) >= half or absf(z) >= half:
		return 0.0
	var u := (x + half) / step
	var v := (z + half) / step
	var i0 := clampi(int(floor(u)), 0, n - 2)
	var j0 := clampi(int(floor(v)), 0, n - 2)
	var fu := clampf(u - i0, 0.0, 1.0)
	var fv := clampf(v - j0, 0.0, 1.0)
	return lerpf(lerpf(h[j0 * n + i0], h[j0 * n + i0 + 1], fu), lerpf(h[(j0 + 1) * n + i0], h[(j0 + 1) * n + i0 + 1], fu), fv)


func normal_at(x: float, z: float) -> Vector3:
	var e := 0.75
	return Vector3(height(x - e, z) - height(x + e, z), 2.0 * e, height(x, z - e) - height(x, z + e)).normalized()


func build_ground(parent: Node3D) -> void:
	"""das Boden-Gitter (gleiche Punkte wie height(), daher stehen alle genau darauf) + ein flacher Ring bis 600 m"""
	if not on:
		return
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	verts.resize(n * n)
	norms.resize(n * n)
	for j in range(n):
		for i in range(n):
			var hx := h[j * n + mini(i + 1, n - 1)] - h[j * n + maxi(i - 1, 0)]
			var hz := h[mini(j + 1, n - 1) * n + i] - h[maxi(j - 1, 0) * n + i]
			verts[j * n + i] = Vector3(-half + i * step, h[j * n + i], -half + j * step)
			norms[j * n + i] = Vector3(-hx, 2.0 * step, -hz).normalized()
	var idx := PackedInt32Array()
	for j in range(n - 1):
		for i in range(n - 1):
			var a := j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	var R := 600.0                                       # the flat ring outside (like the plane of main)
	var b0 := verts.size()
	for c in [Vector3(-half, 0, -half), Vector3(half, 0, -half), Vector3(half, 0, half), Vector3(-half, 0, half),
			Vector3(-R, 0, -R), Vector3(R, 0, -R), Vector3(R, 0, R), Vector3(-R, 0, R)]:
		verts.append(c)
		norms.append(Vector3.UP)
	for s in range(4):
		var i0 := b0 + s
		var i1 := b0 + (s + 1) % 4
		var o0 := b0 + 4 + s
		var o1 := b0 + 4 + (s + 1) % 4
		idx.append_array([i0, i1, o0, i1, o1, o0])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	ground_node = main.add_mesh(parent, am, Vector3.ZERO, main.grass_mat, "x")
	ground_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var th: MeshInstance3D = parent.get_child(parent.get_child_count() - 1)
	th.material_override = main.tmats["ground"]


# ---- paths -----------------------------------------------------------------------------------------------------------
func path_mat(kind: String) -> ShaderMaterial:
	var pm := ShaderMaterial.new()
	pm.shader = load("res://shaders/pfad.gdshader")
	pm.set_shader_parameter("noise_tex", main.noise_tex)
	match kind:
		"erde":
			pm.set_shader_parameter("base", Color(0.36, 0.28, 0.19))
			pm.set_shader_parameter("grit", Color(0.27, 0.21, 0.15))
			pm.set_shader_parameter("grain", 0.35)
			pm.set_shader_parameter("tracks", 1.0)         # two wheel tracks, grass in the middle
		"platten":
			pm.set_shader_parameter("base", Color(0.55, 0.53, 0.5))
			pm.set_shader_parameter("grit", Color(0.4, 0.39, 0.37))
			pm.set_shader_parameter("grain", 0.2)
			pm.set_shader_parameter("tiles", 1.0)
		_:
			pm.set_shader_parameter("base", Color(0.58, 0.55, 0.49))
			pm.set_shader_parameter("grit", Color(0.38, 0.36, 0.33))
			pm.set_shader_parameter("grain", 1.0)
	path_mats.append(pm)
	main.ground_mats.append(pm)                          # snow and wetness like the ground (main._update_sky, colors.gd)
	return pm


func path(parent: Node3D, pts: Array, width := 1.6, kind := "kies") -> MeshInstance3D:
	"""ein Weg entlang der Punkte (Vector2 x/z), liegt auf dem Gelände (0.025 m darüber); kind: kies, erde, platten"""
	var line := PackedVector2Array()
	for k in range(pts.size() - 1):                      # every ~0.8 m a point (the path follows the hills)
		var a: Vector2 = pts[k]
		var b: Vector2 = pts[k + 1]
		var cnt := maxi(1, int(ceil(a.distance_to(b) / 0.8)))
		for s in range(cnt):
			line.append(a.lerp(b, float(s) / cnt))
	line.append(pts[-1])
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	var along := 0.0
	for k in range(line.size()):
		var p: Vector2 = line[k]
		var dir: Vector2 = (line[mini(k + 1, line.size() - 1)] - line[maxi(k - 1, 0)]).normalized()
		var side := Vector2(-dir.y, dir.x)
		if k > 0:
			along += p.distance_to(line[k - 1])
		var wob := 1.0 + 0.08 * sin(along * 0.9 + p.x)  # the edge is not quite straight
		for s in [-1.0, 1.0]:
			var q: Vector2 = p + side * s * width * 0.5 * wob
			verts.append(Vector3(q.x, main.ground_y(q.x, q.y) + 0.025, q.y))
			norms.append(normal_at(q.x, q.y))
			uvs.append(Vector2(0.5 + 0.5 * s, along))
		if k > 0:
			var a := (k - 1) * 2
			idx.append_array([a, a + 1, a + 2, a + 1, a + 3, a + 2])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi: MeshInstance3D = main.add_mesh(parent, am, Vector3.ZERO, path_mat(kind), "road")
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	paths.append([line, width * 0.5, kind])
	return mi


func on_path(p: Vector2, margin := 0.3) -> bool:
	for pa in paths:
		var line: PackedVector2Array = pa[0]
		var r: float = float(pa[1]) + margin
		for k in range(line.size() - 1):
			if Geometry2D.get_closest_point_to_segment(p, line[k], line[k + 1]).distance_to(p) < r:
				return true
	return false


func path_kind_at(p: Vector2) -> String:
	"""«kies» / «erde» / «platten» – oder leer (für Schritte, Spuren …)"""
	for pa in paths:
		var line: PackedVector2Array = pa[0]
		for k in range(line.size() - 1):
			if Geometry2D.get_closest_point_to_segment(p, line[k], line[k + 1]).distance_to(p) < float(pa[1]):
				return str(pa[2])
	return ""


func hill_blocks(a: Vector3, b: Vector3) -> bool:
	"""verdeckt das Gelände die Linie a → b? (Hügelkuppe dazwischen)"""
	if not on:
		return false
	var a2 := Vector2(a.x, a.z)
	var b2 := Vector2(b.x, b.z)
	var cnt := int(ceil(a2.distance_to(b2) / 1.0))
	for i in range(1, cnt):
		var f := float(i) / float(cnt)
		var p := a2.lerp(b2, f)
		if height(p.x, p.y) > lerpf(a.y, b.y, f) + 0.03:
			return true
	return false


# ---- cloud shadows ---------------------------------------------------------------------------------------------------
func cloud_active() -> bool:
	return on and cloud_amt > 0.001


func _cloud_strength() -> float:
	if main.cond.get("shadows", false):
		return 0.6
	if not main.cloud_shadows or not main.weather in ["cloudy", "rain", "snow", "storm"]:
		return 0.0
	return 0.42 if main.weather == "cloudy" else 0.22


func cloud_here(x: float, z: float) -> float:
	"""Schatten an diesem Punkt (0 = Sonne, 1 = voller Wolkenschatten), gleich gerechnet wie im Shader"""
	if _cloud_img == null:
		var img = main.noise_tex.get_image() if main.noise_tex != null else null
		if img == null:
			return 0.0
		_cloud_img = img
		if _cloud_img.is_compressed():
			_cloud_img.decompress()
	var w := _cloud_img.get_width()
	var hh := _cloud_img.get_height()
	var uv := (Vector2(x, z) + cloud_off) * CLOUD_SCALE
	var px := fposmod(uv.x, 1.0) * w - 0.5
	var py := fposmod(uv.y, 1.0) * hh - 0.5
	var x0 := int(floor(px))
	var y0 := int(floor(py))
	var fx := px - x0
	var fy := py - y0
	var c00 := _cloud_img.get_pixel(posmod(x0, w), posmod(y0, hh)).r
	var c10 := _cloud_img.get_pixel(posmod(x0 + 1, w), posmod(y0, hh)).r
	var c01 := _cloud_img.get_pixel(posmod(x0, w), posmod(y0 + 1, hh)).r
	var c11 := _cloud_img.get_pixel(posmod(x0 + 1, w), posmod(y0 + 1, hh)).r
	var v := lerpf(lerpf(c00, c10, fx), lerpf(c01, c11, fx), fy)
	return smoothstep(0.52, 0.68, v)


func shade_at_head() -> float:
	"""für main.cloud_shade: 1 = volle Sonne am Kopf"""
	return 1.0 - cloud_here(0.0, 0.0) * minf(1.0, cloud_amt * 1.6)


func _process(dt: float) -> void:
	if main == null or main.grass_mat == null:
		return
	if on:                                              # the clouds drift with the wind (from the west, a bit from the south)
		var spd := 3.0 + float(main.wind) / 3.6 * 0.9
		if main.cond.get("shadows", false):
			spd = 9.0
		cloud_off -= Vector2(0.92, -0.38) * spd * dt
	_t -= dt
	if _t <= 0.0:
		_t = 0.1
		var w_now: float = float(main.wind) * float(main.gust())
		var tint = main.grass_mat.get_shader_parameter("grass")
		for vm in veg_mats:
			vm.set_shader_parameter("wind", w_now)
			if tint != null:
				vm.set_shader_parameter("tint", tint)
		_apply_cloud(false)


func _apply_cloud(force: bool) -> void:
	var amt := _cloud_strength() if on else 0.0
	var el: float = main.sun_pos().x if main.has_method("sun_pos") else 30.0
	amt *= clampf(el / 12.0, 0.0, 1.0)                  # no sun, no shadow (night, dawn)
	if not force and is_equal_approx(amt, cloud_amt) and amt == 0.0:
		return
	cloud_amt = amt
	var mats: Array = [main.grass_mat]
	mats.append_array(main.foliage_mats)
	mats.append_array(path_mats)
	mats.append_array(veg_mats)
	for mt in mats:
		if mt is ShaderMaterial:
			mt.set_shader_parameter("cloud_amt", amt)
			mt.set_shader_parameter("cloud_off", cloud_off)


var veg_mats: Array = []      # materials of vegetation.gd (grass blades, flowers): get the cloud shadows and the wind too


# ---- scenes: the camping place (scenes._camping) --------------------------------------------------------------------
const Veg = preload("res://scripts/vegetation.gd")


func camping_relief(sc) -> void:
	"""Camping-Platz: dein Platz (12 m um den Kopf) und die Strasse bleiben flach, rundherum leichte Wellen (±0.9 m),
	vorne rechts eine kleine Böschung mit einer Senke dahinter (dort sieht MoveEye einen Kauernden nicht)"""
	setup_relief({"amp": 0.75, "scale": 30.0, "seed": 4,
			"flat": [[Vector2.ZERO, 12.0, 8.0]],
			"bands": [["z", -29.0, 3.5, 6.0]],
			"dips": [[_v2(main.pos_of(22.0, 26.0)), 5.0, 0.9], [_v2(main.pos_of(22.0, 19.5)), 3.5, -0.75],
					[_v2(main.pos_of(-120.0, 30.0)), 9.0, -1.2], [_v2(main.pos_of(150.0, 34.0)), 7.0, 0.7]]})
	build_ground(sc.root)


static func _v2(p: Vector3) -> Vector2:
	return Vector2(p.x, p.z)


func camping_plants(sc) -> void:
	"""Camping-Platz mit «Mehr Pflanzen»: Wege (Kies, Feldweg), drei Hecken (hoch, hoch + dunkel, niedrig), Büsche,
	Bäume verschiedener Arten, dichtes Gras mit hohen Stellen, Blumen"""
	var root: Node3D = sc.root
	path(root, [Vector2(0.5, -27.0), Vector2(1.6, -20.0), Vector2(0.6, -13.0), Vector2(-1.0, -8.5), Vector2(-2.6, -5.0)], 1.7, "kies")
	path(root, [Vector2(-48.0, -15.0), Vector2(-30.0, -12.5), Vector2(-16.0, -9.5), Vector2(-7.0, -6.5), Vector2(-3.4, -4.6)], 2.4, "erde")
	path(root, [Vector2(7.5, -3.0), Vector2(18.0, 1.5), Vector2(30.0, 3.0), Vector2(52.0, 2.0)], 1.4, "kies")
	# hedges: they really hide (core without gaps, obstacle with height)
	Veg.hedge(sc, root, Vector2(-25.0, -21.0), Vector2(-5.5, -21.5), 1.9, 0.95, "liguster")   # front left, in the picture
	Veg.hedge(sc, root, Vector2(13.5, -8.0), Vector2(13.0, -25.0), 2.2, 1.1, "thuja")        # right, along the neighbour
	Veg.hedge(sc, root, Vector2(4.5, -11.5), Vector2(10.5, -9.5), 1.1, 0.7, "buche")         # low: upper body shows
	Veg.hedge(sc, root, Vector2(-34.0, 10.0), Vector2(-20.0, 24.0), 1.8, 0.9, "liguster")    # behind (back left)
	var kc: Callable = Veg.keep_clear_default(sc)
	for b in [[Vector3(-27.0, 0, -19.5), "hasel"], [Vector3(-4.0, 0, -19.8), "rund"], [Vector3(15.5, 0, -6.5), "bluehend"],
			[Vector3(-14.0, 0, -15.5), "jung"], [Vector3(11.0, 0, -12.5), "beeren"]]:
		Veg.bush(sc, root, b[0], b[1], sc.rng.randf_range(0.9, 1.15))
	Veg.scatter(sc, 22, 10.0, 55.0, ["bush:rund", "bush:rund", "bush:hasel", "bush:bluehend", "bush:beeren", "bush:jung"], kc, 2.5)
	Veg.scatter(sc, 40, 16.0, 60.0, ["tree:laub", "tree:fichte", "tree:birke:0.8-1.2", "tree:eiche:0.8-1.15", "tree:obst:0.9-1.2",
			"tree:kiefer:0.8-1.1", "tree:jung", "tree:birke:0.7-1.0"], kc, 3.0)
	Veg.scatter(sc, 100, 60.0, 120.0, ["tree:fichte:0.9-1.6", "tree:fichte:0.9-1.6", "tree:laub:0.9-1.5", "tree:kiefer:0.9-1.3",
			"tree:eiche:0.9-1.3", "tree:birke:0.9-1.3"], kc, 3.0)
	var tall := [[Vector2(-15.0, -20.0), 6.0], [_v2(main.pos_of(22.0, 26.0)), 6.0], [Vector2(12.0, -16.0), 4.0], [Vector2(-28.0, 16.0), 6.0]]
	Veg.grass(sc, 2600, 2.5, 15.0, kc, {"tall": 0.05, "tall_spots": tall})     # dense near the camera
	Veg.grass(sc, 3600, 15.0, 50.0, kc, {"tall": 0.1, "tall_spots": tall})
	Veg.flowers(sc, 900, 4.0, 42.0, kc)


# ---- tests ---------------------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	return {"g_relief": g_relief, "g_plants": g_plants, "on": on, "half": half, "step": step, "min": snappedf(hmin, 0.01),
			"max": snappedf(hmax, 0.01), "paths": paths.size(), "cloud_amt": snappedf(cloud_amt, 0.01),
			"cloud_head": snappedf(cloud_here(0, 0), 0.01), "lite": Quality.lite()}


func control(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "info"))
	if op == "set" and str(d.get("key", "")) in SAVE:
		_put(str(d["key"]), bool(d.get("value", true)))
	elif op == "height":
		var x := float(d.get("x", 0.0))
		var z := float(d.get("z", 0.0))
		return {"ok": true, "y": snappedf(main.ground_y(x, z), 0.001), "path": path_kind_at(Vector2(x, z))}
	elif op == "los":
		var f: Array = d.get("from", [0, 1.6, 0])
		var t: Array = d.get("to", [0, 1.0, -20])
		var a := Vector3(float(f[0]), float(f[1]), float(f[2]))
		var b := Vector3(float(t[0]), float(t[1]), float(t[2]))
		return {"ok": true, "blocker": main.line_blocker(a, b), "hill": hill_blocks(a, b)}
	elif op == "walk":                                 # test: a visitor from → to ([x, z]), e.g. behind a hedge
		var fa: Array = d.get("from", [-22.0, -23.5])
		var ta: Array = d.get("to", [-8.0, -23.5])
		var v = main.spawn(str(d.get("kind", "person")), Vector3(float(fa[0]), 0, float(fa[1])), Vector3(float(ta[0]), 0, float(ta[1])))
		return {"ok": v != null}
	elif op == "cloud":
		return {"ok": true, "shade": snappedf(cloud_here(float(d.get("x", 0.0)), float(d.get("z", 0.0))), 0.01), "amt": cloud_amt}
	return {"ok": true, "info": info()}
