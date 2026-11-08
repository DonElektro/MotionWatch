extends Node
## «Flora und Fauna» (Idee Nr. 5 des Besitzers, Phase 1 – erster Ausschnitt zur Freigabe): Pflanzen sollen echter aussehen.
## Alles selbst gebaut (keine fremde Datei): die Blatt-Bilder entstehen hier beim Start aus Zufall mit festem Startwert.
##
##   - Kronen, Büsche, Hecken (shaders/foliage.gdshader, «neu»): Blätterbüschel statt glatter Kugel (Rauschen in Farbe und
##     Normale, dunkler innen und unten, Gegenlicht), ausgefranster Rand (nur Normal / Hoch).
##   - Blatt-Karten (shaders/blatt_karten.gdshader): auf jede Kugel einer Krone bzw. jeden Kegel einer Fichte kommen kleine
##     Karten mit Blatt- bzw. Nadelzweig-Bild (Alpha-Test, kein Mischen – schnell auch auf Intel HD 4600). Pro Krone-Material
##     EIN MultiMesh für die ganze Szene (wenige Zeichenaufrufe), weit weg schrumpfen sie weg (nur die Krone bleibt).
##     Sie bewegen sich mit der Krone im Wind (gleiche Formel, Mitte der Kugel in INSTANCE_CUSTOM) und folgen der Jahreszeit
##     (gleiche Werte wie das Material der Krone, jede Viertelsekunde abgeglichen).
##   - Gras (shaders/gras_halme.gdshader): Farbflecken in zwei Grössen, trockene Spitzen, dunkler am Boden, weiches
##     Ausblenden in der Ferne statt hartem Abschneiden.
##
## Stufen (aus den vorhandenen Grafik-Einstellungen, keine neue Einstellung):
##   lite   = Grafik-Modus Lite (Raspberry Pi):   nur die neuen Farben, kein ausgefranster Rand, keine Karten
##   normal = Normal (Qualität einfach / mittel, z. B. der HP mit HD 4600, Compatibility):  Karten ~12 pro Kugel, bis 55 m
##   hoch   = Qualität schön / ultra oder Grafik-Modus Hoch:   Karten ~24 pro Kugel, bis 110 m, Gegenlicht stärker
## Was verdeckt, bleibt gleich: die Kugeln / Kegel der Kronen, die Hindernisse und tree_spots ändern sich nicht; die Karten
## sitzen zur Hälfte in der Krone (Rand höchstens ~0.3 m weiter), sie sind nicht im Wärmebild (Ebene 1 allein).
## Zufall: eigener RandomNumberGenerator (Startwert aus dem Ort) – sc.rng bleibt unberührt, die Szene wird gleich gebaut.
##
## Schalter für Tests / Vergleiche: Flora.modus = "" (nach Stufe) | "alt" (alles wie vor Phase 1) | "lite" | "normal" | "hoch".

const Quality = preload("res://scripts/quality.gd")
const Baeume = preload("res://scripts/baeume.gd")    # Paket 1: Bäume und Sträucher mit Ästen (Fichte, Buche, Hasel)

static var modus := ""
static var _tex_broad: ImageTexture = null
static var _tex_needle: ImageTexture = null
static var _quad: QuadMesh = null
static var _pending := {}            # scene root id -> {root, sc, mats: {card_mat: [[Transform3D, Color custom]]}}


static func stufe(m) -> String:
	"""lite | normal | hoch | alt"""
	if modus != "":
		return modus
	var e := OS.get_environment("MW_FLORA")
	if e in ["alt", "lite", "normal", "hoch"]:
		return e
	if "--quality" in OS.get_cmdline_user_args():
		return "alt"                       # Prüfstand / fixed test runs: pictures stay comparable (like inhalte.gd F2)
	if Quality.lite():
		return "lite"
	if m != null and (str(m.get("quality")) in ["nice", "ultra"] or str(m.get("grafik_mode")) == "hoch"):
		return "hoch"
	return "normal"


static func neu(m) -> bool:
	return stufe(m) != "alt"


static func foliage_params(m, fm: ShaderMaterial) -> void:
	"""foliage.gdshader: neu (Klumpen, Schatten innen) ab Lite, ausgefranster Rand ab Normal"""
	var st := stufe(m)
	fm.set_shader_parameter("neu", 0.0 if st == "alt" else 1.0)
	fm.set_shader_parameter("ragged", 1.0 if st in ["normal", "hoch"] else 0.0)


static func tuft(p: Vector3) -> Vector3:
	"""Gras wächst in Horsten: den Punkt etwas zur nächsten Horst-Mitte ziehen (Gitter 1.3 m, Mitte aus dem Ort gerechnet –
	kein Zufall aus sc.rng, die übrige Szene bleibt gleich)"""
	var g := 1.3
	var c := Vector2(roundf(p.x / g), roundf(p.z / g))
	var h := Vector2(fposmod(sin(c.dot(Vector2(12.9898, 78.233))) * 43758.5453, 1.0), fposmod(sin(c.dot(Vector2(39.346, 11.135))) * 24634.634, 1.0))
	var ctr := (c + (h - Vector2(0.5, 0.5)) * 0.6) * g
	var q := Vector2(p.x, p.z).lerp(ctr, 0.45)
	return Vector3(q.x, p.y, q.y)


static func ground(m) -> void:
	"""Boden der Wiese (shaders/grass.gdshader): wo F2 (inhalte.gd) keine Fotos gesetzt hat, die eigenen Fotos des Besitzers
	(texturen/wiese_alp_01 = sattes Gras, wiese_alp_steinig_01 = trockenere Stellen, LIZENZEN.md) mit dem vorhandenen Weg
	«tex_on» des Shaders; die Farbe der Jahreszeit bleibt. Lite / alt: wie bisher."""
	var gm: ShaderMaterial = m.grass_mat
	if gm == null:
		return
	load("res://scripts/gras.gd").ground(m)            # Paket 2: worn path edges, far ring, gusts (or off)
	var st := stufe(m)
	if st in ["alt", "lite"]:
		if gm.has_meta("flora_tex"):
			gm.set_shader_parameter("tex_on", 0.0)
			gm.set_shader_parameter("ref_auto", 0.0)
			gm.remove_meta("flora_tex")
		return
	var on = gm.get_shader_parameter("tex_on")
	if on != null and float(on) > 0.0 and not gm.has_meta("flora_tex"):
		gm.set_shader_parameter("ref_auto", 0.0)
		return                             # F2 photos are on
	var a := "res://texturen/wiese_alp_01.jpg"
	var b := "res://texturen/wiese_alp_steinig_01.jpg"
	if not (ResourceLoader.exists(a) and ResourceLoader.exists(b)):
		return
	gm.set_shader_parameter("tex_a_alb", load(a))
	gm.set_shader_parameter("tex_b_alb", load(b))
	gm.set_shader_parameter("ref_a", Vector3(0.1997, 0.2383, 0.1204))
	gm.set_shader_parameter("ref_b", Vector3(0.2115, 0.2280, 0.1449))
	gm.set_shader_parameter("scale_a", 0.3)
	gm.set_shader_parameter("scale_b", 0.22)
	gm.set_shader_parameter("tex_far", 110.0 if st == "hoch" else 70.0)
	gm.set_shader_parameter("ref_auto", 1.0)
	gm.set_shader_parameter("tex_on", 1.0)
	gm.set_meta("flora_tex", true)


static func grass_params(m, gm: ShaderMaterial, far: float) -> void:
	"""gras_halme.gdshader: Farbflecken, trockene Spitzen, weiches Ende vor «far»"""
	var st := stufe(m)
	gm.set_shader_parameter("neu", 0.0 if st == "alt" else 1.0)
	gm.set_shader_parameter("fade_far", 0.0 if st in ["alt", "lite"] else far)


# ---- Blatt-Bilder (einmal pro Sitzung) -----------------------------------------------------------------------------------
static func _leaf(img: Image, c: Vector2, ang: float, ln: float, wd: float, shade: float) -> void:
	"""ein Blatt: Spitze vorne, breiteste Stelle bei 40 %, helle Mittelrippe; Grauwert (die Farbe kommt aus dem Shader)"""
	var dirv := Vector2(cos(ang), sin(ang))
	var nrm := Vector2(-dirv.y, dirv.x)
	var r := int(ceil(ln)) + 2
	var sz := img.get_size()
	for y in range(maxi(0, int(c.y) - r), mini(sz.y, int(c.y) + r)):
		for x in range(maxi(0, int(c.x) - r), mini(sz.x, int(c.x) + r)):
			var d := Vector2(x, y) - c
			var u := d.dot(dirv) / ln                      # 0 = stem end, 1 = tip
			var v := d.dot(nrm)
			if u < 0.0 or u > 1.0:
				continue
			var half := wd * 0.5 * sin(PI * pow(u, 0.75)) # leaf outline
			if absf(v) > half:
				continue
			var g := shade * (0.78 + 0.22 * (absf(v) / maxf(half, 0.01)))   # a bit lighter at the edge
			if absf(v) < 0.9:
				g = minf(1.0, g * 1.25)                     # the midrib
			img.set_pixel(x, y, Color(g, g, g, 1.0))


static func broad_tex() -> ImageTexture:
	if _tex_broad != null:
		return _tex_broad
	var img := Image.create(128, 128, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.5, 0.5, 0.5, 0.0))
	var r := RandomNumberGenerator.new()
	r.seed = 4711
	var c := Vector2(64, 64)
	for k in range(5):                                  # a few twigs with leaf clusters, the ones behind darker
		var a0 := r.randf() * TAU
		var cc := c + Vector2(cos(a0), sin(a0)) * r.randf_range(8.0, 26.0)
		for j in range(7):
			var a := r.randf() * TAU
			var p := cc + Vector2(cos(a), sin(a)) * r.randf_range(2.0, 16.0)
			var ang := a + r.randf_range(-0.5, 0.5)
			var sh := lerpf(0.5, 1.0, float(k * 7 + j) / 35.0) * r.randf_range(0.85, 1.0)
			_leaf(img, p - Vector2(cos(ang), sin(ang)) * 8.0, ang, r.randf_range(24.0, 32.0), r.randf_range(11.0, 15.0), sh)
	img.generate_mipmaps()
	_tex_broad = ImageTexture.create_from_image(img)
	return _tex_broad


static func needle_tex() -> ImageTexture:
	if _tex_needle != null:
		return _tex_needle
	var img := Image.create(128, 128, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.4, 0.4, 0.4, 0.0))
	var r := RandomNumberGenerator.new()
	r.seed = 815
	for br in range(3):                                 # a spruce sprig: a twig with side twigs, needles on both sides
		var p0 := Vector2(64 + (br - 1) * 22, 118)
		var ang := -PI / 2 + (br - 1) * 0.35 + r.randf_range(-0.1, 0.1)
		var ln := r.randf_range(80.0, 105.0)
		var steps := int(ln / 2.0)
		for s in range(steps):
			var u := float(s) / steps
			var p := p0 + Vector2(cos(ang), sin(ang)) * ln * u
			var w := lerpf(16.0, 5.0, u)                  # needles get shorter towards the tip
			for side in [-1.0, 1.0]:
				var na: float = ang + side * 1.1 + r.randf_range(-0.15, 0.15)
				for t in range(int(w)):
					var q := p + Vector2(cos(na), sin(na)) * t
					if q.x >= 0 and q.y >= 0 and q.x < 128 and q.y < 128:
						var g := r.randf_range(0.6, 1.0) * (0.75 + 0.25 * float(t) / w)
						img.set_pixel(int(q.x), int(q.y), Color(g, g, g, 1.0))
			if s % 2 == 0 and p.x >= 1 and p.y >= 1 and p.x < 127 and p.y < 127:
				img.set_pixel(int(p.x), int(p.y), Color(0.35, 0.3, 0.25, 1.0))
	img.generate_mipmaps()
	_tex_needle = ImageTexture.create_from_image(img)
	return _tex_needle


static func _card_mesh() -> QuadMesh:
	if _quad == null:
		_quad = QuadMesh.new()
		_quad.size = Vector2(1, 1)
	return _quad


# ---- die Karten an einer Pflanze ------------------------------------------------------------------------------------------
static func _rel(n: Node3D, root: Node3D) -> Transform3D:
	"""Lage von n im Raum von root (auch bevor die Szene im Baum hängt)"""
	var t := n.transform
	var p := n.get_parent()
	while p != null and p != root:
		if p is Node3D:
			t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


static func _card_mat(sc, crown: ShaderMaterial, conifer: bool) -> ShaderMaterial:
	var mk := "flora_card_n" if conifer else "flora_card_b"
	if crown.has_meta(mk):
		return crown.get_meta(mk)
	var st := stufe(sc.m)
	var cm := ShaderMaterial.new()
	cm.shader = load("res://shaders/blatt_karten.gdshader")
	cm.set_shader_parameter("leaf_tex", needle_tex() if conifer else broad_tex())
	cm.set_shader_parameter("noise_tex", sc.m.noise_tex)
	cm.set_shader_parameter("far", 110.0 if st == "hoch" else 55.0)
	cm.set_shader_parameter("backlight_k", 0.22 if st == "hoch" else 0.12)
	for k in ["color", "wind", "bare", "blossom", "cloud_amt", "cloud_off", "gust_amt", "dir"]:
		var v = crown.get_shader_parameter(k)
		if v != null:
			cm.set_shader_parameter(k, v)
	crown.set_meta(mk, cm)
	return cm


static func _kern(crown: ShaderMaterial, art: String) -> ShaderMaterial:
	"""Paket 1: der alte Kronen-Teil als kleinerer Kern hinter den Ästen und Blättern (kahl im Winter weg); einer pro
	Kronen-Material und Art (geteilte Materialien)"""
	var key := "flora_kern_" + art
	if crown.has_meta(key):
		return crown.get_meta(key)
	var k := crown.duplicate() as ShaderMaterial
	k.set_shader_parameter("ragged", 0.0)
	var nadel := art in Baeume.NADEL
	k.set_shader_parameter("kern", {"kiefer": 0.4, "arve": 0.45, "laerche": 0.33}.get(art, 0.5 if nadel else 0.55))
	k.set_shader_parameter("kern_y", 0.72 if nadel else 0.75)
	k.set_shader_parameter("kern_dark", 0.85 if art in ["fichte", "tanne"] else 1.05)  # like shaded leaves, not a dark lump
	crown.set_meta(key, k)
	return k


static func _job(sc) -> Dictionary:
	var key: int = sc.root.get_instance_id()
	if not _pending.has(key):
		_pending[key] = {"root": sc.root, "sc": sc, "mats": {}}
	var tree: SceneTree = sc.m.get_tree()
	if not tree.process_frame.is_connected(_flush_all):     # one call for all roots (bound callables count as the same)
		tree.process_frame.connect(_flush_all, CONNECT_ONE_SHOT)
	return _pending[key]


static func _flush_all() -> void:
	for key in _pending.keys():
		_flush(key)


static func hedge(sc, n: Node3D, L: float, h: float, thick: float, kind: String, crown: ShaderMaterial, ground: Callable) -> void:
	"""Paket 1: Blatt-Karten auf einer Hecke (vegetation.gd Veg.hedge); Kern, Buckel, Wärmebild, Hindernis bleiben gleich"""
	if sc == null or sc.root == null or n == null:
		return
	var st := stufe(sc.m)
	if st == "alt" or st == "lite":
		return
	Baeume.hedge(_job(sc), st, _rel(n, sc.root), L, h, thick, kind, crown, ground)


static var _bib_crowns := {}


static func bib(b, kind: String, list: Array, q: Dictionary) -> void:
	"""Paket 1: Bäume der Bergtal-Bibliothek (bib_berg.gd many): Gerüst + Büschel für die nahen; die MultiMesh-Bäume
	(Kegel / Kugeln, Wärmebild, Hindernisse) bleiben ganz"""
	var sc = b.s
	if sc == null or sc.root == null or b.m == null:
		return
	var st := stufe(b.m)
	if st == "alt" or st == "lite":
		return
	var d: Dictionary = b.make(kind, q)
	if d.is_empty() or not d.has("p"):
		return
	var col := ""
	for part in d["p"]:
		if str(part[0]) in ["k", "s"] and str(part[7]) != "e8ecf0":
			col = str(part[7])
			break
	if col == "":
		return
	var ck := kind + "|" + col
	var crown: ShaderMaterial = _bib_crowns.get(ck)
	if crown == null or not is_instance_valid(crown):
		crown = ShaderMaterial.new()                          # stands for the crown (colour, wind): never drawn itself
		crown.shader = load("res://shaders/foliage.gdshader")
		crown.set_shader_parameter("color", Color("#" + col))
		crown.set_shader_parameter("noise_tex", b.m.noise_tex)
		crown.set_meta("broad", false)
		_bib_crowns[ck] = crown
	if not b.m.foliage_mats.has(crown):
		b.m.foliage_mats.append(crown)                        # wind like the other crowns
	Baeume.bib(_job(sc), st, kind, list, d, _rel(b.root, sc.root) if b.root != sc.root else Transform3D(), crown, str(q.get("season", "sommer")))


static func dress(sc, plant: Node3D, art := "") -> void:
	"""Blatt-Karten an alle Kronen-Teile (Kugeln, Kegel mit foliage.gdshader) dieser Pflanze.
	Paket 1: mit art (Baeume.ARTEN) statt dessen Äste, Blatt-Büschel, Kern und Ferne-Bild (baeume.gd)"""
	if plant == null or sc == null or sc.root == null:
		return
	var st := stufe(sc.m)
	if st == "alt" or st == "lite":
		return
	var per := 24 if st == "hoch" else 12
	var job := _job(sc)
	var base_t := _rel(plant, sc.root)
	if art in Baeume.ARTEN:
		var root: Node3D = sc.root
		Baeume.build(sc, plant, art, st, job, base_t, func(n): return _rel(n, root), func(c, a):
			var km := _kern(c, a)
			if not job.has("kerns"):
				job["kerns"] = {}
			job["kerns"][km] = c
			return km)
		return
	var r := RandomNumberGenerator.new()
	r.seed = hash(Vector3i(roundi(base_t.origin.x * 10), roundi(base_t.origin.y * 10), roundi(base_t.origin.z * 10)))
	var parts: Array = plant.find_children("*", "MeshInstance3D", true, false)
	if plant is MeshInstance3D:
		parts.append(plant)
	for ch in parts:
		var mi := ch as MeshInstance3D
		if mi.layers != 1 or not (mi.material_override is ShaderMaterial):
			continue
		var crown := mi.material_override as ShaderMaterial
		if crown.shader == null or not crown.shader.resource_path.ends_with("foliage.gdshader"):
			continue
		var t := _rel(mi, sc.root)
		var cm := _card_mat(sc, crown, mi.mesh is CylinderMesh)
		if not job["mats"].has(cm):
			job["mats"][cm] = {"crown": crown, "list": []}
		var list: Array = job["mats"][cm]["list"]
		var centre: Vector3 = t.origin
		if mi.mesh is SphereMesh:
			var sm := mi.mesh as SphereMesh
			var rx := sm.radius
			var ry := sm.height * 0.5
			var n := int(per * clampf(rx * ry / 0.9, 0.5, 2.2))
			for i in range(n):
				var u := r.randf() * TAU
				var v := acos(r.randf_range(-0.55, 1.0))      # more on top and the sides than below
				var dl := Vector3(sin(v) * cos(u), cos(v), sin(v) * sin(u))
				var pl := Vector3(dl.x * rx, dl.y * ry, dl.z * rx) * r.randf_range(0.82, 0.98)
				var sz := clampf(rx * r.randf_range(0.8, 1.15), 0.35, 1.4)
				var pw: Vector3 = t * pl
				var outw: Vector3 = (pw - centre).normalized()
				var b := Basis.looking_at(-outw, Vector3.UP if absf(outw.y) < 0.95 else Vector3.FORWARD)   # the card faces outwards
				b = b * Basis(Vector3.FORWARD, r.randf() * TAU)
				b = b.scaled(Vector3(sz, sz, sz))
				list.append([Transform3D(b, pw), _cd(centre - pw, pl.y + 1.0)])
		elif mi.mesh is CylinderMesh:                       # a layer of the spruce: sprigs hanging down round the cone
			var cy := mi.mesh as CylinderMesh
			var rb := maxf(cy.bottom_radius, cy.top_radius)
			var h := cy.height
			var n2 := int(per * 1.6 * clampf(rb / 1.2, 0.5, 1.6))
			for i in range(n2):
				var u2 := r.randf() * TAU
				var f := r.randf_range(0.15, 1.0)             # 1 = the lower edge of the layer
				var rad := rb * f * r.randf_range(0.9, 1.04)
				var pl2 := Vector3(cos(u2) * rad, h * 0.5 - h * f, sin(u2) * rad)
				var pw2: Vector3 = t * pl2
				var outw2 := Vector3(pw2.x - centre.x, 0.0, pw2.z - centre.z).normalized()
				var sz2 := clampf(rb * r.randf_range(0.45, 0.7), 0.35, 1.0)
				var b2 := Basis.looking_at(-outw2, Vector3.UP)
				b2 = b2 * Basis(Vector3.RIGHT, -r.randf_range(0.35, 0.8))   # tilted: the sprigs droop
				b2 = b2.scaled(Vector3(sz2, sz2 * 1.25, sz2))
				list.append([Transform3D(b2, pw2 - Vector3(0, sz2 * 0.25, 0)), _cd(centre - pw2 + Vector3(0, sz2 * 0.25, 0), pl2.y + 1.0)])


static func _cd(off: Vector3, h: float) -> Color:
	"""INSTANCE_CUSTOM: from the card to the centre of its crown part (xyz), height in the part + 1 (w, as foliage «up»)"""
	return Color(off.x, off.y, off.z, h)


static func _flush(key: int) -> void:
	var job: Dictionary = _pending.get(key, {})
	_pending.erase(key)
	if job.is_empty() or not is_instance_valid(job["root"]):
		return
	var root: Node3D = job["root"]
	var sync: Node = root.get_node_or_null("flora_sync")
	if sync == null:
		sync = load("res://scripts/flora.gd").new()
		sync.name = "flora_sync"
		root.add_child(sync)
	for km in job.get("kerns", {}):
		sync.pairs.append([job["kerns"][km], km])
	Baeume.flush(job, root, sync, job["sc"].m.noise_tex)
	for cm in job["mats"]:
		var list: Array = job["mats"][cm]["list"]
		if list.is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = _card_mesh()
		mm.instance_count = list.size()
		var lo := Vector3(INF, INF, INF)
		var hi := -lo
		for i in range(list.size()):
			mm.set_instance_transform(i, list[i][0])
			mm.set_instance_custom_data(i, list[i][1])
			lo = lo.min(list[i][0].origin)
			hi = hi.max(list[i][0].origin)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "blatt_karten"
		mmi.multimesh = mm
		mmi.material_override = cm
		mmi.layers = 1
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.custom_aabb = AABB(lo - Vector3(2, 2, 2), hi - lo + Vector3(4, 4, 4))
		root.add_child(mmi)
		sync.pairs.append([job["mats"][cm]["crown"], cm])


# ---- Abgleich mit der Krone (Wind, Jahreszeit, Wolkenschatten) ----------------------------------------------------------
var pairs: Array = []                # [crown ShaderMaterial, card ShaderMaterial]
var groups: Array = []               # Paket 1: [[crown materials], [card / bark / far materials]] (baeume.gd)
var _t := 0.0
const SYNC := ["color", "wind", "bare", "blossom", "cloud_amt", "cloud_off", "gust_amt", "dir"]


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.25
	for g in groups:
		Baeume.sync_group(g)
	for p in pairs:
		if p[0] == null:
			continue
		for k in SYNC:
			var v = p[0].get_shader_parameter(k)
			if v != null:
				p[1].set_shader_parameter(k, v)
