extends RefCounted
const Waerme = preload("res://scripts/waerme.gd")   # 3D-4.26: the heat table (fire, lamps)
## The scenes of the 3D simulator (from 3D-1.5): camping place, forest, car park, garden with house, a funny place and
## wildlife watching. Every scene builds its things below one node (root); switching frees it and builds the next one.
## Every scene must give main: door_node + door_light + window_mat (the door sensor), obj["door"], obj["pir"], obj["bike"].

const LIST := [["camping", "Camping-Platz"], ["wald", "Wald"], ["parkplatz", "Parkplatz"], ["garten", "Garten / Haus"],
		["lustig", "Lustiger Platz"], ["wild", "Wildbeobachtung"], ["verstecken", "Versteckspiel (viele Verstecke)"], ["ort", "Ort von der Karte (Schweiz)"],
		["zuhause", "Mein Zuhause (selbst gebaut)"], ["bauernhof", "Bauernhof"], ["seeufer", "Seeufer mit Steg"], ["baustelle", "Baustelle"],
		["stellplatz", "Wohnmobil-Stellplatz"], ["vorlage", "Meine Vorlage (3D-Datei)"], ["schlafzimmer", "Schlafzimmer (Wecker)"],
		["camping_voll", "Voller Campingplatz"], ["tarnen", "Tarnen und Kriechen"], ["velodieb", "Velodieb"], ["parcours", "Verfolgungs-Parcours"],
		["ferienpark", "Ferienpark am See"], ["bergtal", "Bergtal (Alp, See, Pass)"], ["daheim", "Zuhause (Haus, Garten, Baustelle)"],
		["pfadilager", "Pfadilager im Wald"], ["hofladen", "Bauernhof mit Hofladen und Stellplätzen"], ["bergdorf", "Bergdorf mit Stellplatz"],
		["festival", "Festival-Gelände"]]   # 3D-4.x: kompakt.gd (Pfadilager, Bergdorf: Orte im Bergtal; Hofladen: im Ferienpark; Festival: eigene Welt)
# 3D-4.x Welten (worlds.gd): every id stays valid; the scene list shows only worlds.gd SHOWN, the old scenes are places in them
# 3D-4.x: the English names for MoveEye (it translates them into its languages; without a name MoveEye shows the German one)
const EN := {"camping": "Campsite", "wald": "Forest", "parkplatz": "Car park", "garten": "Garden / house", "lustig": "Funny place",
		"wild": "Wildlife watching", "verstecken": "Hide and seek (many hiding places)", "ort": "Place from the map (Switzerland)",
		"zuhause": "My home (self-built)", "bauernhof": "Farm", "seeufer": "Lake shore with jetty", "baustelle": "Building site",
		"stellplatz": "Camper van site", "vorlage": "My template (3D file)", "schlafzimmer": "Bedroom (wake-up alarm)",
		"camping_voll": "Full campsite", "tarnen": "Camouflage and crawling", "velodieb": "Bike thief", "parcours": "Tracking course",
		"ferienpark": "Holiday park by the lake", "bergtal": "Mountain valley (alp, lake, pass)", "daheim": "At home (house, garden, building site)",
		"pfadilager": "Scout camp in the forest", "hofladen": "Farm with farm shop and camper pitches",
		"bergdorf": "Mountain village with camper pitch", "festival": "Festival grounds"}

# visitors that come by themselves, and how often (seconds from .. to)
const AUTO := {"camping": [["person", "child", "jogger", "dogwalk", "fox", "fox", "boar", "deer", "herd", "cat", "badger", "hare", "hedgehog", "marten", "squirrel", "cyclist", "couple", "stroller", "courier", "police", "drunk", "bats", "owl", "burglar", "bbq", "homecoming", "fox_trash", "kids_tag", "boar_group"], 35.0, 110.0],
		"wald": [["deer", "herd", "fox", "boar", "badger", "hare", "hedgehog", "person", "jogger", "dogwalk", "wolf", "marten", "squirrel", "squirrel", "lynx", "chamois", "horse_walk", "cyclist", "owl", "bats", "boar_group"], 25.0, 80.0],
		"parkplatz": [["person", "person", "child", "car_park", "car_park", "cat", "fox", "dogwalk", "van", "moto", "police", "courier", "couple", "stroller", "drunk", "burglar", "homecoming", "parcel"], 30.0, 80.0],
		"garten": [["cat", "cat", "fox", "badger", "hedgehog", "hare", "garden_person", "garden_person", "dog", "marten", "squirrel", "courier", "bats", "owl", "parcel", "fox_trash", "burglar", "bbq", "kids_tag"], 35.0, 100.0],
		"lustig": [["bench", "bench", "child", "dogwalk", "fox", "deer", "cat", "hare", "couple", "stroller", "cyclist", "drunk"], 25.0, 60.0],
		"verstecken": [["person", "child", "jogger", "dogwalk", "fox", "cat", "hare", "deer", "couple", "police", "sheep_flock"], 30.0, 90.0],
		"ort": [["person", "child", "jogger", "dogwalk", "fox", "deer", "cat", "cat", "badger", "hare", "hedgehog", "car", "marten", "squirrel", "cyclist", "couple", "stroller", "courier", "tractor", "moto", "van", "cows", "sheep_flock",
			"horse_walk", "bats", "owl", "parcel", "homecoming", "burglar", "mowing", "fox_trash", "kids_tag"], 30.0, 100.0],
		"bauernhof": [["cows", "sheep_flock", "cat", "cat", "dog", "fox", "fox", "marten", "badger", "hare", "person", "tractor", "horse_walk", "owl", "bats", "burglar", "dogwalk"], 30.0, 90.0],
		"seeufer": [["person", "couple", "jogger", "dogwalk", "fox", "deer", "hare", "cyclist", "child", "bats", "owl", "drunk", "burglar"], 30.0, 90.0],
		"baustelle": [["person", "burglar", "burglar", "police", "fox", "cat", "marten", "courier", "van", "drunk", "hare"], 40.0, 120.0],
		"stellplatz": [["person", "couple", "child", "dogwalk", "cat", "fox", "hedgehog", "cyclist", "van", "moto", "camper", "courier", "burglar", "homecoming", "drunk", "bbq"], 30.0, 90.0],
		"vorlage": [["person", "child", "dogwalk", "cat", "fox", "deer", "hare", "hedgehog", "courier", "burglar", "cyclist"], 35.0, 100.0],
		"schlafzimmer": [["cat"], 300.0, 900.0],
		"parcours": [["person", "jogger", "fox", "deer", "hare", "cyclist"], 60.0, 150.0],   # 3D-4.18 (the lessons switch them off)
		"zuhause": [["cat", "cat", "fox", "badger", "hedgehog", "hare", "garden_person", "garden_person", "dog", "marten", "squirrel", "courier", "bats", "owl", "parcel", "burglar", "kids_tag", "person", "dogwalk"], 35.0, 100.0],
		"camping_voll": [["person", "child", "dogwalk", "couple", "cyclist", "stroller", "cat", "fox", "hedgehog", "bbq", "kids_tag", "homecoming", "drunk", "burglar", "platz_besuch", "platz_besuch"], 30.0, 90.0],
		"tarnen": [["person", "dogwalk", "fox", "deer", "hare", "cat", "burglar", "tarn_robben", "tarn_robben", "tarn_schirm", "tarn_karton"], 35.0, 100.0],
		"velodieb": [["person", "cyclist", "dogwalk", "child", "couple", "cat", "fox", "courier", "velodieb", "velodieb"], 30.0, 90.0],
		"ferienpark": [["person", "person", "child", "jogger", "dogwalk", "couple", "cyclist", "stroller", "cat", "fox", "hedgehog", "badger", "hare", "marten",
			"squirrel", "deer", "bats", "owl", "drunk", "burglar", "bbq", "kids_tag", "homecoming", "courier", "fox_trash", "platz_besuch", "car"], 30.0, 90.0],   # 3D-4.x: ferienpark.gd
		"bergtal": [["berg_auto"], 25.0, 75.0],   # 3D-4.x: bergtal.gd chooses (lonely: few people, many animals, by season and time)
		"pfadilager": [["child", "child", "kids_tag", "kids_tag", "person", "jogger", "dogwalk", "deer", "deer", "herd", "fox", "fox", "boar", "boar_group", "badger",
			"hare", "hedgehog", "marten", "squirrel", "squirrel", "lynx", "owl", "bats", "drunk", "burglar"], 25.0, 75.0],   # 3D-4.x: kompakt_pfadi.gd
		"hofladen": [["person", "person", "couple", "child", "stroller", "cyclist", "dogwalk", "car", "car", "tractor", "cows", "sheep_flock", "cat", "cat", "dog",
			"fox", "marten", "badger", "hare", "hedgehog", "owl", "bats", "courier", "parcel", "burglar", "bbq", "homecoming", "platz_besuch"], 25.0, 80.0],   # 3D-4.x: kompakt_hof.gd
		"bergdorf": [["person", "person", "couple", "child", "jogger", "dogwalk", "stroller", "cyclist", "car", "car", "moto", "van", "courier", "cat", "fox", "deer",
			"chamois", "marten", "hare", "owl", "bats", "drunk", "burglar", "homecoming", "bbq", "platz_besuch"], 30.0, 90.0],   # 3D-4.x: kompakt_dorf.gd
		"festival": [["person", "person", "person", "couple", "couple", "child", "drunk", "drunk", "jogger", "cyclist", "police", "courier", "kids_tag", "fox", "cat",
			"hedgehog", "bats", "burglar", "homecoming", "platz_besuch"], 12.0, 35.0],   # 3D-4.x: kompakt_festival.gd (Stresstest: oft Besuch)
		"wild": [["feed_deer", "feed_deer", "feed_boar", "feed_fox", "feed_badger", "feed_hare", "herd", "deer", "chamois", "ibex", "lynx", "owl"], 15.0, 40.0]}

var m                     # main.gd
var root: Node3D
var rng := RandomNumberGenerator.new()
var data := {}            # things a scene needs later (parking spots, the bench, the feeder ...)


static func name_of(id: String) -> String:
	for s in LIST:
		if s[0] == id:
			return s[1]
	return id


func build(id: String, parent: Node3D) -> void:
	root = Node3D.new()
	parent.add_child(root)
	rng.seed = 7
	data = {}
	m.test_props = {}                            # 3D-3.72: things the test aids can take away (name -> node)
	m.bike_node = null
	clip = 0.0
	excl = []
	no_road = false
	decor = false
	if Worlds.is_place(id) and not Worlds.solo(m, id):
		Worlds.build(self, id)                   # 3D-4.x: an old scene as a place in its world (worlds.gd)
		return
	build_legacy(id)


# 3D-4.x Welten: building a place inside a world - clip = radius of its flat area (0 = all), excl = [[centre, r], …] stays free
# (the neighbours), no_road = no road across, decor = only scenery (a neighbour)
const Worlds = preload("res://scripts/worlds.gd")
const Quality = preload("res://scripts/quality.gd")
var clip := 0.0
var excl: Array = []
var no_road := false
var decor := false


func _out(p: Vector3) -> bool:
	"""outside the flat area of the place or on a neighbour"""
	if clip > 0.0 and Vector2(p.x, p.z).length() > clip:
		return true
	for e in excl:
		if Vector2(p.x - (e[0] as Vector3).x, p.z - (e[0] as Vector3).z).length() < float(e[1]):
			return true
	return false


func prune(n: Node3D, r: float) -> void:
	"""things of the old scene farther away than r: gone (the world is there)"""
	for c in n.get_children():
		if c is Node3D and Vector2((c as Node3D).position.x, (c as Node3D).position.z).length() > r:
			c.free()


func build_legacy(id: String, extras := true) -> void:
	"""the old scenes (from 3D-1.5) - alone, or as a place in a world (worlds.gd)"""
	match id:
		"wald":
			_wald()
		"parkplatz":
			_parkplatz()
		"zuhause":
			_zuhause()
		"garten":
			_garten()
		"lustig":
			_lustig()
		"wild":
			_wild()
		"ort":
			_ort()
		"verstecken":
			_verstecken()
		"bauernhof":
			_bauernhof()
		"seeufer":
			_seeufer()
		"baustelle":
			_baustelle()
		"stellplatz":
			_stellplatz()
		"vorlage":
			_vorlage()
		"schlafzimmer":
			_schlafzimmer()
		"parcours":
			m.parcours.build_scene(self)                    # 3D-4.18: parcours.gd (fixed obstacles for the lessons)
		"ferienpark":
			preload("res://scripts/ferienpark.gd").build_scene(self)       # 3D-4.x: big terraced campsite (bib_objekte.gd)
		"pfadilager", "hofladen", "bergdorf", "festival":
			preload("res://scripts/kompakt.gd").build_scene(self, id)          # 3D-4.x: four compact scenes (bib_objekte.gd)
		"bergtal":
			preload("res://scripts/bergtal.gd").build_scene(self)          # 3D-4.x: 2 × 2 km mountain valley (bib_berg.gd)
		"camping_voll", "tarnen", "velodieb":
			preload("res://scripts/szenenplus.gd").build_scene(self, id)     # 3D-4.x: the new scenes (szenenplus.gd)
		_:
			_camping()
	if extras and EXTRA_HIDE.has(id):                             # more places to hide (3D-3.13)
		var e: Array = EXTRA_HIDE[id]
		hide_props(int(e[0]), float(e[1]), float(e[2]), e[3])


const EXTRA_HIDE := {
	"camping": [10, 9.0, 40.0, ["bush", "woodpile", "barrels", "rock", "car", "crates", "compost"]],
	"wald": [12, 8.0, 45.0, ["bush", "bush", "woodpile", "rock", "rock", "haybale"]],
	"parkplatz": [8, 9.0, 40.0, ["car", "container", "pallets", "barrels", "bush", "wall"]],
	"garten": [8, 7.0, 30.0, ["bush", "hedge", "compost", "woodpile", "shed", "crates"]],
	"lustig": [8, 9.0, 40.0, ["bush", "haybale", "crates", "barrels", "rock"]],
	"wild": [10, 10.0, 50.0, ["bush", "bush", "rock", "rock", "woodpile", "haybale", "trailer"]],
	"bauernhof": [10, 9.0, 45.0, ["haybale", "haybale", "woodpile", "trailer", "bush", "compost", "barrels"]],
	"seeufer": [8, 8.0, 40.0, ["bush", "bush", "rock", "woodpile", "crates"]],
	"baustelle": [12, 7.0, 35.0, ["pallets", "container", "barrels", "crates", "wall", "pallets"]],
	"stellplatz": [8, 8.0, 40.0, ["bush", "hedge", "car", "crates", "barrels"]],
	"tarnen": [6, 9.0, 35.0, ["bush", "woodpile", "rock", "haybale"]],
}


# ---- small helpers -------------------------------------------------------------------------------------------------
func put(parent: Node3D, mesh: Mesh, p: Vector3, c, tkey, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	if clip > 0.0 and parent == root and mesh is BoxMesh and (mesh as BoxMesh).size.y <= 0.12 and absf(rot.y) < 0.01 \
			and (mesh as BoxMesh).size.x > clip and (mesh as BoxMesh).size.z > clip and typeof(c) == TYPE_COLOR:
		return _soft_ground(parent, (mesh as BoxMesh).size, p, c, tkey)
	if clip > 0.0 and parent == root and mesh is BoxMesh and (mesh as BoxMesh).size.y <= 0.12 and absf(rot.y) < 0.01:
		var bs: Vector3 = (mesh as BoxMesh).size        # 3D-4.x: a flat thing (road, gravel, water) only on the flat area
		if bs.x > clip or bs.z > clip:
			var x0 := maxf(p.x - bs.x / 2.0, -clip)
			var x1 := minf(p.x + bs.x / 2.0, clip)
			var z0 := maxf(p.z - bs.z / 2.0, -clip)
			var z1 := minf(p.z + bs.z / 2.0, clip)
			if x1 - x0 < 0.2 or z1 - z0 < 0.2:
				x0 = 0.0
				x1 = 0.01
				z0 = 0.0
				z1 = 0.01
			mesh = m.box(x1 - x0, bs.y, z1 - z0)
			p = Vector3((x0 + x1) / 2.0, p.y, (z0 + z1) / 2.0)
	return m.add_mesh(parent, mesh, p, m.mat(c) if typeof(c) == TYPE_COLOR else c, tkey, rot, scl)


func _soft_ground(parent: Node3D, bs: Vector3, p: Vector3, c: Color, tkey) -> MeshInstance3D:
	"""K3 (Kontaktbogen 31.10.2026, «Tarnwiese»): the ground of an old scene inside a world (bigger than its flat area) was a
	sharp-edged rectangle that stuck out over the hill. Now: only the round flat area (radius clip, in the box), lying on the
	ground of the world, and its colour fades out over the outer quarter into the ground of the world (vertex alpha).
	A grid of 2 m (Lite: 4 m) - flat area, so the heights only matter at the edge."""
	var x0 := maxf(p.x - bs.x / 2.0, -clip)
	var x1 := minf(p.x + bs.x / 2.0, clip)
	var z0 := maxf(p.z - bs.z / 2.0, -clip)
	var z1 := minf(p.z + bs.z / 2.0, clip)
	var stp := 4.0 if (Engine.has_meta("lite") and bool(Engine.get_meta("lite"))) else 2.0
	var nx := maxi(2, int(ceil((x1 - x0) / stp)) + 1)
	var nz := maxi(2, int(ceil((z1 - z0) / stp)) + 1)
	var fade := clip * 0.25
	var top := p.y + bs.y / 2.0
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var vs := []
	for j in range(nz):
		for i in range(nx):
			var x := lerpf(x0, x1, float(i) / (nx - 1))
			var z := lerpf(z0, z1, float(j) / (nz - 1))
			var edge := minf(minf(x - x0, x1 - x), minf(z - z0, z1 - z))                  # to the edge of the box …
			edge = minf(edge, clip - Vector2(x, z).length())                              # … and of the flat area
			var a := smoothstep(0.0, fade, edge)
			var y := top
			if m.ground_fn.is_valid():
				y = maxf(top, float(m.ground_fn.call(x, z)) + 0.02) if a < 0.999 else top
			vs.append([Vector3(x, y, z), a])
	for j in range(nz - 1):
		for i in range(nx - 1):
			var q := j * nx + i
			if float(vs[q][1]) + float(vs[q + 1][1]) + float(vs[q + nx][1]) + float(vs[q + nx + 1][1]) <= 0.0:
				continue                                                                   # (all four invisible)
			for k in [q, q + 1, q + nx, q + 1, q + nx + 1, q + nx]:
				st.set_color(Color(1, 1, 1, float(vs[k][1])))
				st.set_normal(Vector3.UP)
				st.add_vertex(vs[k][0])
	var mt := StandardMaterial3D.new()
	mt.albedo_color = c
	mt.vertex_color_use_as_albedo = true
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.roughness = 0.95
	var mi: MeshInstance3D = m.add_mesh(parent, st.commit(), Vector3.ZERO, mt, tkey)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


func node(parent: Node3D, p: Vector3, rot_y := 0.0) -> Node3D:
	var n := Node3D.new()
	n.position = p
	n.rotation.y = rot_y
	parent.add_child(n)
	return n


func cyl(r_top: float, r_bot: float, h: float, seg := 16) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = r_top
	c.bottom_radius = r_bot
	c.height = h
	c.radial_segments = seg
	return c


func sph(r: float, h := -1.0) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = 2.0 * r if h < 0 else h
	s.radial_segments = 12
	s.rings = 6
	return s


func glow_mat(c: Color) -> StandardMaterial3D:
	"""a lamp: glows at night (switched in main._update_sky)"""
	var lm := StandardMaterial3D.new()
	lm.albedo_color = c
	lm.emission_enabled = true
	lm.emission = c
	lm.emission_energy_multiplier = 0.0
	m.lamp_mats.append(lm)
	return lm


func label(parent: Node3D, text: String, p: Vector3, size := 48, col := Color(0.1, 0.1, 0.1)) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.position = p
	l.font_size = size
	l.pixel_size = 0.006
	l.modulate = col
	l.outline_size = 0
	l.layers = 1
	parent.add_child(l)
	return l


var fol_mats: Array = []


func foliage(k: int) -> ShaderMaterial:
	"""one of six shared foliage materials (from 3D-2.0: before, every tree had its own - slow in the forest)"""
	if fol_mats.is_empty():
		var cols := [Color(0.16, 0.36, 0.14), Color(0.2, 0.4, 0.12), Color(0.13, 0.3, 0.12), Color(0.24, 0.42, 0.16), Color(0.1, 0.26, 0.13), Color(0.3, 0.42, 0.14)]
		for broad in [false, true]:                              # 3D-3.97: broadleaf trees have their own (autumn leaves)
			for c in cols:
				var fm := ShaderMaterial.new()
				fm.shader = load("res://shaders/foliage.gdshader")
				fm.set_shader_parameter("noise_tex", m.noise_tex)
				fm.set_shader_parameter("color", c)
				fm.set_meta("broad", broad)
				m.foliage_mats.append(fm)
				fol_mats.append(fm)
	return fol_mats[k % fol_mats.size()]


func tree(parent: Node3D, p: Vector3, sc: float, conifer := -1) -> void:
	if (parent == root and _out(p)) or (decor and Quality.lite()):
		rng.randf()                                  # 3D-4.x: outside the place (worlds.gd) - the same random numbers after it
		return
	if parent == root and m.hilly():
		p.y = m.ground_y(p.x, p.z)                               # 3D-4.x: on the hills (gelaende.gd)
	var tr := node(parent, p, rng.randf() * TAU)
	tr.scale = Vector3.ONE * sc
	var bark := Color(0.3, 0.22, 0.15).lerp(Color(0.38, 0.3, 0.22), rng.randf())
	var con := rng.randf() < 0.5 if conifer < 0 else conifer == 1
	if con:                                                      # spruce: layers that get smaller, a little darker inside
		put(tr, cyl(0.08, 0.22, 5.2, 8), Vector3(0, 2.6, 0), bark, "tree")
		var fm := foliage(rng.randi_range(0, 2) * 2 + 0)
		var layers := rng.randi_range(4, 5)
		for k in range(layers):
			var f := float(k) / layers
			put(tr, cyl(0.0, 1.7 * (1.0 - f * 0.75), 2.0, 10), Vector3(rng.randf_range(-0.05, 0.05), 1.9 + k * 1.05, 0), fm, "tree",
					Vector3(0, rng.randf() * TAU, rng.randf_range(-0.04, 0.04)))
	else:                                                        # broadleaf: trunk with two branches and a round crown
		put(tr, cyl(0.12, 0.22, 3.6, 8), Vector3(0, 1.8, 0), bark, "tree")
		for b in range(2):
			var a := rng.randf() * TAU
			put(tr, cyl(0.04, 0.08, 1.6, 6), Vector3(cos(a) * 0.35, 3.3, sin(a) * 0.35), bark, "tree", Vector3(sin(a) * 0.7, 0, -cos(a) * 0.7))
		var fm2 := foliage(rng.randi_range(0, 5) + 6)
		for k in range(rng.randi_range(4, 6)):
			var r := rng.randf_range(0.9, 1.5)
			put(tr, sph(r, r * 1.7), Vector3(rng.randf_range(-0.9, 0.9), 4.1 + rng.randf_range(-0.4, 0.9), rng.randf_range(-0.9, 0.9)), fm2, "tree")
	if parent == root or parent.get_parent() == root:
		m.add_obstacle(p, 0.32 * sc)
	var gp: Vector3 = tr.global_position if tr.is_inside_tree() else p
	m.tree_spots.append([Vector2(gp.x, gp.z), (1.75 if con else 1.5) * sc, (1.9 if con else 3.0) * sc])   # 3D-3.76: crowns (camera of the players)


func trees(n: int, dmin: float, dmax: float, keep_clear: Callable) -> void:
	"""n trees at random places between dmin and dmax from the head, not where keep_clear(p) says"""
	var made := 0
	var tries := 0
	while made < n and tries < n * 6:
		tries += 1
		var p: Vector3 = m.pos_of(rng.randf_range(-180, 180), rng.randf_range(dmin, dmax))
		if keep_clear.call(p):
			continue
		tree(root, p, rng.randf_range(0.8, 1.5))
		made += 1


func road(z: float, width := 5.0) -> void:
	data["road_z"] = z + 1.2
	if no_road:
		return
	put(root, m.box(400, 0.04, width), Vector3(0, 0.02, z), Color(0.42, 0.4, 0.37), "road")


func meadow(n: int, dmin: float, dmax: float, keep_clear := Callable()) -> void:
	"""grass tufts and flowers scattered on the meadow - one MultiMesh each (cheap even for thousands)"""
	if decor and Quality.lite():
		return
	if clip > 0.0:
		dmax = minf(dmax, clip)
		dmin = minf(dmin, dmax * 0.5)
	if not excl.is_empty():
		var kc0 := keep_clear
		keep_clear = func(p: Vector3): return _out(p) or (kc0.is_valid() and kc0.call(p))
	var blade := PrismMesh.new()
	blade.size = Vector3(0.12, 0.28, 0.02)
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.3, 0.5, 0.18)
	gm.cull_mode = BaseMaterial3D.CULL_DISABLED
	gm.roughness = 0.9
	blade.material = gm if m.get("wind_fx") == null else m.wind_fx.grass_mat(gm.albedo_color)   # F6: bends in the wind
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = false
	mm.mesh = blade
	mm.instance_count = n * 3
	var fl := SphereMesh.new()
	fl.radius = 0.035
	fl.height = 0.05
	fl.radial_segments = 6
	fl.rings = 3
	var fmat := StandardMaterial3D.new()
	fmat.vertex_color_use_as_albedo = true
	fl.material = fmat
	var mf := MultiMesh.new()
	mf.transform_format = MultiMesh.TRANSFORM_3D
	mf.use_colors = true
	mf.mesh = fl
	mf.instance_count = n / 3
	var fc := [Color(0.95, 0.95, 0.95), Color(0.95, 0.85, 0.2), Color(0.85, 0.3, 0.6), Color(0.55, 0.45, 0.9), Color(0.95, 0.5, 0.15)]
	var k := 0
	for i in range(n):
		var p: Vector3 = m.pos_of(rng.randf_range(-180, 180), rng.randf_range(dmin, dmax))
		if keep_clear.is_valid() and keep_clear.call(p):
			p = Vector3(0, -50, 0)                               # hidden below the ground
		else:
			p.y = m.ground_y(p.x, p.z)
		for b in range(3):
			var t := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).rotated(Vector3.RIGHT, rng.randf_range(-0.25, 0.25)).scaled(Vector3.ONE * rng.randf_range(0.7, 1.4)),
					p + Vector3(rng.randf_range(-0.12, 0.12), 0.12, rng.randf_range(-0.12, 0.12)))
			mm.set_instance_transform(i * 3 + b, t)
		if i % 3 == 0 and k < mf.instance_count:
			mf.set_instance_transform(k, Transform3D(Basis(), p + Vector3(rng.randf_range(-0.2, 0.2), 0.26, rng.randf_range(-0.2, 0.2))))
			mf.set_instance_color(k, fc[rng.randi() % fc.size()])
			k += 1
	for x in [mm, mf]:
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = x
		mi.layers = 1
		mi.add_to_group("meadow")
		mi.visible = m.meadow_on
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mi)


func stones(n: int, dmin: float, dmax: float) -> void:
	if clip > 0.0:
		dmax = minf(dmax, clip)
		dmin = minf(dmin, dmax * 0.5)
	for i in range(n):
		var r := rng.randf_range(0.15, 0.35)
		var sp: Vector3 = m.pos_of(rng.randf_range(-60, 60), rng.randf_range(dmin, dmax), 0.05)
		sp.y += m.ground_y(sp.x, sp.z)                           # 3D-4.x: on the hills (gelaende.gd)
		put(root, sph(r, r * 1.2), sp, Color(0.48, 0.48, 0.46), "stone")


func door_light_at(parent: Node3D, p: Vector3) -> void:
	m.door_light = OmniLight3D.new()
	m.door_light.position = p
	m.door_light.light_color = Color(1.0, 0.82, 0.55)
	m.door_light.omni_range = 6.0
	m.door_light.light_energy = 0.0
	parent.add_child(m.door_light)


func window_mat_shared() -> StandardMaterial3D:
	"""the window material of the door sensor's building (all its windows light up together)"""
	return m.window_mat if m.window_mat != null else window_mat()


func window_mat() -> StandardMaterial3D:
	var w := StandardMaterial3D.new()
	w.albedo_color = Color(0.25, 0.3, 0.38)
	w.emission_enabled = true
	w.emission = Color(1.0, 0.8, 0.5)
	w.emission_energy_multiplier = 0.0
	m.window_mat = w
	return w


func caravan(p: Vector3, rot_y: float) -> void:
	"""the caravan with its door (door sensor) - camping place and car park"""
	var cv := node(root, p, rot_y)
	put(cv, m.box(5.6, 2.2, 2.3), Vector3(0, 1.4, 0), Color(0.88, 0.89, 0.9), "caravan")
	put(cv, m.box(5.6, 0.25, 2.3), Vector3(0, 0.4, 0), Color(0.35, 0.36, 0.38), "caravan")
	put(cv, m.box(5.4, 0.12, 2.1), Vector3(0, 2.56, 0), Color(0.7, 0.71, 0.73), "caravan")
	put(cv, m.box(1.6, 0.7, 0.05), Vector3(-1.5, 1.75, 1.16), window_mat(), "window")
	m.door_node = node(cv, Vector3(1.6, 0.45, 1.17))
	put(m.door_node, m.box(0.75, 1.9, 0.05), Vector3(0.375, 0.95, 0), Color(0.55, 0.56, 0.6), "caravan")
	door_light_at(cv, Vector3(1.95, 1.5, 0.6))
	for x in [-1.8, 1.8]:
		put(cv, cyl(0.33, 0.33, 0.2), Vector3(x * 0.5, 0.33, 1.1), Color(0.05, 0.05, 0.05), "caravan", Vector3(PI / 2, 0, 0))
		put(cv, cyl(0.18, 0.18, 0.21), Vector3(x * 0.5, 0.33, 1.1), Color(0.6, 0.6, 0.62), "caravan", Vector3(PI / 2, 0, 0))
	put(cv, m.box(1.75, 0.82, 0.04), Vector3(-1.5, 1.75, 1.165), Color(0.2, 0.2, 0.22), "caravan")           # window frame
	put(cv, m.box(1.0, 0.6, 0.05), Vector3(-1.5, 1.75, -1.16), window_mat_shared(), "window")              # back window
	put(cv, m.box(0.05, 0.55, 0.9), Vector3(-2.81, 1.7, 0), window_mat_shared(), "window")                  # front window
	put(cv, m.box(5.6, 0.06, 0.04), Vector3(0, 1.0, 1.16), Color(0.2, 0.45, 0.75), "caravan")              # stripe
	put(cv, m.box(5.6, 0.06, 0.04), Vector3(0, 1.0, -1.16), Color(0.2, 0.45, 0.75), "caravan")
	put(cv, m.box(2.6, 0.04, 1.4), Vector3(1.0, 2.35, 1.85), Color(0.85, 0.45, 0.15), "tent", Vector3(-0.12, 0, 0))   # awning
	for x2 in [-0.25, 2.25]:
		put(cv, cyl(0.02, 0.02, 2.2, 6), Vector3(x2, 1.12, 2.5), Color(0.6, 0.6, 0.62), "stone")
	put(cv, m.box(0.7, 0.08, 0.4), Vector3(1.97, 0.22, 1.4), Color(0.4, 0.4, 0.42), "caravan")               # step
	for s2 in [-1, 1]:                                                                                       # drawbar
		put(cv, m.box(1.6, 0.08, 0.08), Vector3(-3.4, 0.45, 0.35 * s2), Color(0.25, 0.25, 0.27), "stone", Vector3(0, 0.25 * s2, 0))
	put(cv, cyl(0.15, 0.15, 0.45, 10), Vector3(-3.3, 0.72, 0), Color(0.7, 0.2, 0.15), "stone")                 # gas bottle
	put(cv, m.box(0.5, 0.14, 0.5), Vector3(0.6, 2.68, 0), Color(0.85, 0.85, 0.85), "caravan")                 # roof vent
	m.obj["door"] = cv.transform * Vector3(2.0, 0, 2.3)
	m.add_obstacle_node(cv, Vector3(-0.4, 0, 0), 6.6, 2.5)


func hut(p: Vector3, rot_y: float, col := Color(0.45, 0.3, 0.18)) -> Node3D:
	"""a small wooden hut with a door (door sensor) and a window"""
	var h := node(root, p, rot_y)
	put(h, m.box(4.0, 2.4, 3.2), Vector3(0, 1.2, 0), col, "caravan")
	var roof := PrismMesh.new()
	roof.size = Vector3(4.6, 1.3, 3.6)
	put(h, roof, Vector3(0, 3.05, 0), col.darkened(0.35), "caravan")
	put(h, m.box(0.9, 0.6, 0.05), Vector3(-1.1, 1.5, 1.61), window_mat(), "window")
	put(h, m.box(1.04, 0.74, 0.04), Vector3(-1.1, 1.5, 1.605), col.darkened(0.5), "caravan")               # window frame
	for y in [0.4, 0.8, 1.2, 1.6, 2.0]:                                                                    # planks
		put(h, m.box(4.02, 0.03, 3.22), Vector3(0, y, 0), col.darkened(0.25), "caravan")
	put(h, m.box(0.4, 1.0, 0.4), Vector3(1.2, 3.4, -0.6), Color(0.45, 0.42, 0.4), "stone")                # chimney
	smoke(h.transform * Vector3(1.2, 4.0, -0.6))
	for i in range(6):                                                                                     # wood pile
		put(h, cyl(0.11, 0.11, 0.9, 8), Vector3(-2.35, 0.12 + (i / 3) * 0.2, -0.8 + (i % 3) * 0.24), Color(0.55, 0.4, 0.25), "tree", Vector3(PI / 2, 0, 0))
	m.add_obstacle_node(h, Vector3(-0.2, 0, 0), 4.9, 3.5)
	m.door_node = node(h, Vector3(0.5, 0, 1.62))
	put(m.door_node, m.box(0.8, 1.9, 0.05), Vector3(0.4, 0.95, 0), col.darkened(0.2), "caravan")
	door_light_at(h, Vector3(0.9, 1.8, 2.2))
	m.obj["door"] = h.transform * Vector3(0.9, 0, 2.6)
	return h


func bike(p: Vector3, rot_y: float) -> void:
	var bk := node(root, p, rot_y)
	var frame: Color = [Color(0.7, 0.1, 0.1), Color(0.1, 0.35, 0.7), Color(0.15, 0.15, 0.15), Color(0.2, 0.55, 0.3)][rng.randi() % 4]
	for z in [-0.55, 0.55]:
		var tor := TorusMesh.new()
		tor.inner_radius = 0.3
		tor.outer_radius = 0.34
		put(bk, tor, Vector3(0, 0.34, z), Color(0.05, 0.05, 0.05), "stone", Vector3(0, 0, PI / 2))
		for k in range(4):                                                                                 # spokes
			put(bk, m.box(0.008, 0.6, 0.008), Vector3(0, 0.34, z), Color(0.75, 0.75, 0.78), "stone", Vector3(k * PI / 4, 0, 0))
	put(bk, m.box(0.04, 0.04, 0.7), Vector3(0, 0.62, -0.05), frame, "stone")                                 # top tube
	put(bk, m.box(0.04, 0.04, 0.72), Vector3(0, 0.48, -0.1), frame, "stone", Vector3(0.62, 0, 0))            # down tube
	put(bk, m.box(0.04, 0.5, 0.04), Vector3(0, 0.55, 0.25), frame, "stone", Vector3(-0.3, 0, 0))             # seat tube
	put(bk, m.box(0.04, 0.45, 0.04), Vector3(0, 0.55, -0.5), frame, "stone", Vector3(0.3, 0, 0))             # fork
	put(bk, m.box(0.5, 0.03, 0.03), Vector3(0, 0.88, -0.45), Color(0.2, 0.2, 0.2), "stone")                 # handlebar
	put(bk, m.box(0.12, 0.05, 0.24), Vector3(0, 0.84, 0.32), Color(0.1, 0.1, 0.1), "stone")                 # saddle
	put(bk, cyl(0.09, 0.09, 0.02, 12), Vector3(0.03, 0.3, 0.0), Color(0.6, 0.6, 0.62), "stone", Vector3(0, 0, PI / 2))   # chain ring
	if m.simreal != null:
		m.simreal.note_bike(bk)                    # 3D-4.4: reflectors (flare up in the infrared light)
	m.obj["bike"] = p
	m.bike_node = bk                             # 3D-3.71: the test aid «Velo wegnehmen» hides it
	m.test_props["Velo"] = bk
	m.add_obstacle(p, 0.5)
	m.set_obstacle_height(1.0)


func bench(p: Vector3, rot_y: float) -> void:
	var b := node(root, p, rot_y)
	put(b, m.box(1.8, 0.06, 0.45), Vector3(0, 0.45, 0), Color(0.5, 0.33, 0.18), "tree")
	put(b, m.box(1.8, 0.4, 0.05), Vector3(0, 0.75, -0.22), Color(0.5, 0.33, 0.18), "tree", Vector3(-0.15, 0, 0))
	for x in [-0.8, 0.8]:
		put(b, m.box(0.06, 0.45, 0.4), Vector3(x, 0.22, 0), Color(0.15, 0.15, 0.15), "stone")


func lamp_post(p: Vector3, h := 4.5) -> void:
	put(root, cyl(0.06, 0.08, h, 8), p + Vector3(0, h / 2, 0), Color(0.25, 0.27, 0.3), "stone")
	put(root, cyl(0.14, 0.16, 0.3, 10), p + Vector3(0, 0.15, 0), Color(0.22, 0.24, 0.27), "stone")
	m.add_obstacle(p, 0.2)
	put(root, m.box(0.5, 0.12, 0.3), p + Vector3(0, h, 0), glow_mat(Color(1.0, 0.85, 0.6)), "lamp")   # 3D-4.26: warm only when lit (waerme_welt.gd)
	var l := OmniLight3D.new()
	l.position = p + Vector3(0, h - 0.2, 0)
	l.light_color = Color(1.0, 0.82, 0.55)
	l.omni_range = 12.0
	l.light_energy = 0.0
	root.add_child(l)
	m.lamps.append(l)


func static_car(p: Vector3, rot_y: float, col: Color) -> void:
	var c := node(root, p, rot_y)
	var glass := Color(0.15, 0.2, 0.25)
	put(c, m.box(1.75, 0.6, 4.2), Vector3(0, 0.6, 0), col, "caravan")
	put(c, m.box(1.6, 0.5, 2.1), Vector3(0, 1.15, 0.25), col.darkened(0.15), "caravan")
	put(c, m.box(1.5, 0.42, 0.05), Vector3(0, 1.15, -0.82), glass, "caravan", Vector3(-0.5, 0, 0))
	put(c, m.box(1.5, 0.4, 0.05), Vector3(0, 1.15, 1.32), glass, "caravan", Vector3(0.4, 0, 0))
	for s2 in [-1, 1]:
		put(c, m.box(0.05, 0.36, 1.9), Vector3(0.81 * s2, 1.15, 0.25), glass, "caravan")
	put(c, m.box(1.8, 0.18, 0.12), Vector3(0, 0.42, -2.12), Color(0.15, 0.15, 0.15), "caravan")
	put(c, m.box(1.8, 0.18, 0.12), Vector3(0, 0.42, 2.12), Color(0.15, 0.15, 0.15), "caravan")
	for x in [-0.85, 0.85]:
		for z in [-1.35, 1.35]:
			put(c, cyl(0.33, 0.33, 0.22), Vector3(x, 0.33, z), Color(0.05, 0.05, 0.05), "caravan", Vector3(0, 0, PI / 2))
			put(c, cyl(0.18, 0.18, 0.23), Vector3(x, 0.33, z), Color(0.6, 0.6, 0.62), "caravan", Vector3(0, 0, PI / 2))
	m.add_obstacle_box(p, 1.95, 4.4, rot_y)
	m.set_obstacle_height(1.5)
	if m.simreal != null:
		m.simreal.note_car(c)                      # 3D-4.4: number plates that reflect; a cat may sit on the roof


func mushroom(p: Vector3, s := 1.0) -> void:
	put(root, cyl(0.04 * s, 0.05 * s, 0.16 * s, 6), p + Vector3(0, 0.08 * s, 0), Color(0.95, 0.93, 0.85), "stone")
	put(root, sph(0.12 * s, 0.1 * s), p + Vector3(0, 0.17 * s, 0), Color(0.8, 0.08, 0.05), "stone")


# ---- camping place (stage 1) ---------------------------------------------------------------------------------------
# ---- life in the world (from 3D-2.9): flags and laundry in the wind, smoke from chimneys ----------------------------
func cloth(parent: Node3D, size: Vector2, pos: Vector3, rot: Vector3, col: Color, hang := false) -> MeshInstance3D:
	var q := QuadMesh.new()
	q.size = size
	q.subdivide_width = 8
	q.subdivide_depth = 6
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.position = pos
	mi.rotation = rot
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/cloth.gdshader")
	sm.set_shader_parameter("color", col)
	sm.set_shader_parameter("seed", rng.randf() * 10.0)
	sm.set_shader_parameter("hang", 1.0 if hang else 0.0)
	sm.set_shader_parameter("wind", m.wind)
	mi.material_override = sm
	mi.layers = 1
	mi.add_to_group("cloth")
	mi.visible = m.world_cloth
	m.cloth_mats.append(sm)
	parent.add_child(mi)
	return mi


func flag(p: Vector3, col: Color) -> void:
	put(root, cyl(0.04, 0.05, 6.0, 8), p + Vector3(0, 3.0, 0), Color(0.75, 0.75, 0.78), "stone")
	var f := cloth(root, Vector2(1.4, 0.9), p + Vector3(0.72, 5.4, 0), Vector3.ZERO, col)
	f.add_to_group("cloth")


func laundry(p: Vector3, rot_y: float) -> void:
	"""a washing line between two poles with a few clothes"""
	var n := node(root, p, rot_y)
	for s2 in [-1, 1]:
		put(n, cyl(0.03, 0.03, 1.9, 6), Vector3(1.6 * s2, 0.95, 0), Color(0.6, 0.6, 0.62), "stone")
	put(n, m.box(3.2, 0.012, 0.012), Vector3(0, 1.85, 0), Color(0.9, 0.9, 0.9), "stone")
	var cols := [Color(0.9, 0.9, 0.95), Color(0.2, 0.4, 0.8), Color(0.85, 0.25, 0.25), Color(0.95, 0.85, 0.3), Color(0.3, 0.6, 0.35)]
	var x := -1.2
	for i in range(4):
		var w := rng.randf_range(0.4, 0.7)
		var hgt := rng.randf_range(0.5, 0.8)
		var c := cloth(n, Vector2(w, hgt), Vector3(x + w / 2.0, 1.85 - hgt / 2.0, 0), Vector3.ZERO, cols[rng.randi() % cols.size()], true)
		c.rotation.z = PI                                  # UV.y = 0 at the line
		c.rotation.y = PI
		x += w + 0.12


func smoke(at: Vector3) -> void:
	"""smoke from a chimney: rises and drifts with the wind (moves in the picture - like in reality)"""
	var p := CPUParticles3D.new()
	p.amount = 40
	p.lifetime = 7.0
	p.position = at
	p.direction = Vector3(0, 1, 0)
	p.spread = 12.0
	p.initial_velocity_min = 0.5
	p.initial_velocity_max = 0.8
	p.gravity = Vector3(0.25 + m.wind * 0.02, 0.05, 0.0)
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.0
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.3))
	curve.add_point(Vector2(1, 2.2))
	p.scale_amount_curve = curve
	var sm := SphereMesh.new()
	sm.radius = 0.5
	sm.height = 1.0
	sm.radial_segments = 8
	sm.rings = 4
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.5, 0.5, 0.52, 0.5)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.material = mat
	p.mesh = sm
	p.add_to_group("smoke")
	p.emitting = m.world_smoke
	root.add_child(p)


func _ort() -> void:
	"""a real place in Switzerland (geo.gd); until it is loaded: the camping place"""
	if not m.geo.loaded:
		_camping()
		return
	m.terrain = true
	m.geo.build(self)
	meadow(600, 3.0, 40.0, func(p: Vector3): return not m.geo.is_green(m.geo.photo_color(p.x, p.z)) or not m.geo._free_for_tree(Vector2(p.x, p.z)))


func _camping() -> void:
	var plants: bool = m.gelaende != null and m.gelaende.plants_wanted()
	if m.gelaende != null and m.gelaende.relief_wanted():
		m.gelaende.camping_relief(self)                  # 3D-4.x: hills and hollows first - everything after stands on them
	road(-29.0)
	caravan(m.pos_of(-28.0, 9.0), deg_to_rad(28.0))
	var tn := node(root, m.pos_of(14.0, 7.0), deg_to_rad(-14.0))
	var tent := PrismMesh.new()
	tent.size = Vector3(2.6, 1.5, 2.4)
	var wf = m.get("wind_fx")                                                        # F6: the fabric moves in the wind
	put(tn, tent, Vector3(0, 0.75, 0), Color(0.9, 0.5, 0.15) if wf == null else wf.tent_mat(Color(0.9, 0.5, 0.15), 1.5), "tent")
	var fly := PrismMesh.new()                                                       # flysheet a bit bigger, darker
	fly.size = Vector3(2.9, 1.58, 2.0)
	put(tn, fly, Vector3(0, 0.78, 0), Color(0.75, 0.38, 0.1) if wf == null else wf.tent_mat(Color(0.75, 0.38, 0.1), 1.58), "tent")
	var door := PrismMesh.new()
	door.size = Vector3(0.9, 0.9, 0.02)
	put(tn, door, Vector3(0, 0.45, 1.21), Color(0.15, 0.1, 0.08), "tent")              # opening
	for s2 in [-1, 1]:                                                               # poles and guy lines
		put(tn, cyl(0.015, 0.015, 1.65, 5), Vector3(0, 0.82, 1.15 * s2), Color(0.6, 0.6, 0.62), "stone")
		put(tn, m.box(0.01, 0.01, 1.4), Vector3(0, 0.8, 1.75 * s2), Color(0.85, 0.85, 0.8), "stone", Vector3(0.62 * s2, 0, 0))
	m.obj["pir"] = m.pos_of(14.0, 7.0)
	m.test_props["Zelt"] = tn
	m.add_obstacle_node(tn, Vector3.ZERO, 3.0, 2.8)
	m.set_obstacle_height(1.4)
	bike(m.pos_of(32.0, 6.0), deg_to_rad(-32.0) + PI / 2)
	var tbl := node(root, Vector3.ZERO)                                              # 3D-3.72: in their own nodes (test aids)
	var cbx := node(root, Vector3.ZERO)
	m.test_props["Tisch"] = tbl
	m.test_props["Kühlboxen"] = cbx
	put(tbl, m.box(1.2, 0.05, 0.8), m.pos_of(-62, 5.5, 0.72), Color(0.8, 0.8, 0.78), "stone")
	for s in [-1, 1]:
		put(cbx, m.box(0.45, 0.45, 0.45), m.pos_of(-62 + 9 * s, 5.6, 0.23), Color(0.15, 0.3, 0.6), "tent")
		m.add_obstacle(m.pos_of(-62 + 9 * s, 5.6), 0.35)
	for x in [-0.5, 0.5]:
		for z in [-0.3, 0.3]:
			put(tbl, cyl(0.015, 0.015, 0.7, 5), m.pos_of(-62, 5.5) + Vector3(x, 0.36, z), Color(0.6, 0.6, 0.62), "stone")
	var gr := node(root, m.pos_of(-2.0, 5.2))                                         # 3D-3.72: a kettle grill (warm in the thermal picture)
	m.test_props["Grill"] = gr
	for k in range(3):
		var a_ := TAU * k / 3.0
		put(gr, cyl(0.015, 0.015, 0.75, 5), Vector3(cos(a_) * 0.2, 0.36, sin(a_) * 0.2), Color(0.2, 0.2, 0.2), "stone", Vector3(sin(a_) * 0.25, 0, -cos(a_) * 0.25))
	put(gr, sph(0.3, 0.3), Vector3(0, 0.78, 0), Color(0.08, 0.08, 0.08), 45.0)
	put(gr, sph(0.3, 0.3), Vector3(0, 0.82, 0), Color(0.1, 0.1, 0.1), 40.0, Vector3(PI, 0, 0))
	put(gr, cyl(0.02, 0.02, 0.06, 6), Vector3(0, 1.0, 0), Color(0.3, 0.3, 0.3), "stone")
	m.add_obstacle(m.pos_of(-2.0, 5.2), 0.4)
	m.add_obstacle(m.pos_of(-62, 5.5), 0.7)
	m.set_obstacle_height(0.5)
	flag(m.pos_of(-42.0, 13.0), Color(0.8, 0.12, 0.12))
	laundry(m.pos_of(-12.0, 11.0), deg_to_rad(20.0))
	stones(8, 4.0, 15.0)
	if plants:
		m.gelaende.camping_plants(self)                  # 3D-4.x: paths, hedges, bushes, trees of many kinds, dense grass, flowers
		return
	meadow(700, 3.0, 40.0)
	for i in range(140):
		var d := rng.randf_range(16, 60) if i < 40 else rng.randf_range(60, 120)
		tree(root, m.pos_of(rng.randf_range(-180, 180), d), rng.randf_range(0.8, 1.5))


# ---- forest ----------------------------------------------------------------------------------------------------------
func _wald() -> void:
	# a forest path across the picture, a hut, a fire place, fallen trees, mushrooms - and many trees
	put(root, m.box(400, 0.03, 3.0), Vector3(0, 0.015, -12), Color(0.36, 0.3, 0.22), "road")
	data["road_z"] = -11.4
	hut(m.pos_of(-48.0, 15.0), deg_to_rad(40.0))
	var fire: Vector3 = m.pos_of(28.0, 8.0)
	for i in range(9):
		var a := i * TAU / 9.0
		put(root, sph(0.18, 0.2), fire + Vector3(cos(a) * 0.7, 0.06, sin(a) * 0.7), Color(0.4, 0.4, 0.4), "stone")
	put(root, m.box(0.9, 0.12, 0.25), fire + Vector3(0, 0.08, 0), Color(0.15, 0.1, 0.07), Waerme.T("campfire_logs"), Vector3(0, 0.5, 0))   # 3D-4.26: waerme.gd
	put(root, m.box(0.9, 0.12, 0.25), fire + Vector3(0, 0.12, 0), Color(0.15, 0.1, 0.07), Waerme.T("campfire_logs"), Vector3(0, -0.6, 0))
	var glow := put(root, sph(0.25, 0.2), fire + Vector3(0, 0.15, 0), glow_mat(Color(1.0, 0.4, 0.08)), Waerme.T("campfire_embers"))
	var fl := OmniLight3D.new()
	fl.position = fire + Vector3(0, 0.6, 0)
	fl.light_color = Color(1.0, 0.55, 0.2)
	fl.omni_range = 7.0
	fl.light_energy = 0.0
	root.add_child(fl)
	m.lamps.append(fl)
	m.anims.append(func(_dt, t):
		if fl.light_energy > 0.0:
			fl.light_energy = 1.6 + 0.6 * sin(t * 13.0) * sin(t * 7.3)
		glow.scale = Vector3.ONE * (1.0 + 0.15 * sin(t * 9.0)))
	m.obj["pir"] = fire
	m.add_obstacle(fire, 0.9)
	m.set_obstacle_height(0.5)
	bike(m.pos_of(-38.0, 13.0), deg_to_rad(20.0))
	put(root, cyl(0.25, 0.3, 6.0, 10), Vector3(-7, 0.3, -18), Color(0.35, 0.25, 0.16), "tree", Vector3(0, 0.4, PI / 2))
	m.add_obstacle_box(Vector3(-7, 0, -18), 6.0, 0.6, 0.4 + PI / 2)
	m.set_obstacle_height(0.6)
	put(root, cyl(0.2, 0.25, 4.0, 10), Vector3(9, 0.25, -6), Color(0.35, 0.25, 0.16), "tree", Vector3(0, -0.8, PI / 2))
	m.add_obstacle_box(Vector3(9, 0, -6), 4.0, 0.5, -0.8 + PI / 2)
	m.set_obstacle_height(0.6)
	for i in range(6):
		var sp: Vector3 = m.pos_of(rng.randf_range(-70, 70), rng.randf_range(5, 20))
		put(root, cyl(0.3, 0.35, 0.4, 10), sp + Vector3(0, 0.2, 0), Color(0.42, 0.32, 0.2), "tree")
		put(root, cyl(0.26, 0.26, 0.02, 10), sp + Vector3(0, 0.41, 0), Color(0.7, 0.58, 0.4), "tree")       # cut surface
		m.add_obstacle(sp, 0.35)
	for i in range(18):                                                                                   # ferns
		var fp: Vector3 = m.pos_of(rng.randf_range(-180, 180), rng.randf_range(4, 40))
		if abs(fp.z + 12.0) < 2.0:
			continue
		for k in range(5):
			put(root, m.box(0.18, 0.02, 0.7), fp + Vector3(0, 0.25, 0), foliage(1), "tree", Vector3(0.5, k * TAU / 5.0, 0))
	for i in range(14):
		mushroom(m.pos_of(rng.randf_range(-60, 60), rng.randf_range(3, 12)), rng.randf_range(0.8, 1.5))
	stones(10, 3.0, 20.0)
	var hutp: Vector3 = m.pos_of(-48.0, 15.0)
	trees(300, 4.5, 120.0, func(p: Vector3): return abs(p.z + 12.0) < 2.4 or p.distance_to(hutp) < 4.5 or p.distance_to(fire) < 3.0 or p.length() < 4.5 or p.distance_to(Vector3(-3, 0, 3)) < 5.0)
	meadow(500, 3.0, 35.0, func(p: Vector3): return abs(p.z + 12.0) < 1.6)


# ---- car park --------------------------------------------------------------------------------------------------------
func _parkplatz() -> void:
	road(-32.0, 7.0)
	flag(Vector3(-20.0, 0, -27.0), Color(0.15, 0.35, 0.8))
	flag(Vector3(-16.5, 0, -27.0), Color(0.95, 0.95, 0.95))
	put(root, m.box(64, 0.03, 30), Vector3(0, 0.015, -15), Color(0.22, 0.22, 0.23), "road")
	var spots := []
	for row in [-9.0, -21.0]:
		for i in range(10):
			var x := -15.0 + i * 3.2
			put(root, m.box(0.12, 0.01, 5.0), Vector3(x - 1.6, 0.035, row), Color(0.9, 0.9, 0.88), "road")
			spots.append(Vector3(x, 0, row))
		put(root, m.box(0.12, 0.01, 5.0), Vector3(-15.0 + 10 * 3.2 - 1.6, 0.035, row), Color(0.9, 0.9, 0.88), "road")
	var cols := [Color(0.6, 0.1, 0.1), Color(0.75, 0.75, 0.78), Color(0.08, 0.08, 0.1), Color(0.1, 0.25, 0.55), Color(0.85, 0.85, 0.85)]
	var free := []
	for i in range(spots.size()):
		if i >= 18:
			continue                                    # room for the caravan
		if rng.randf() < 0.5:
			static_car(spots[i], 0.0 if spots[i].z < -15 else PI, cols[rng.randi() % cols.size()])
		else:
			free.append(spots[i])
	data["free"] = free
	caravan(Vector3(13.5, 0, -21.0), PI / 2)
	lamp_post(Vector3(-8, 0, -15))
	lamp_post(Vector3(8, 0, -15))
	lamp_post(Vector3(-22, 0, -15))
	lamp_post(Vector3(22, 0, -15))
	# ticket machine (the PIR sensor is here)
	put(root, m.box(0.7, 1.6, 0.5), Vector3(5, 0.8, -3.5), Color(0.9, 0.7, 0.1), "caravan")
	m.add_obstacle_box(Vector3(5, 0, -3.5), 0.8, 0.6, 0.0)
	m.set_obstacle_height(1.6)
	put(root, m.box(0.5, 0.3, 0.05), Vector3(5, 1.25, -3.24), glow_mat(Color(0.5, 0.8, 1.0)), 30.0)
	label(root, "P", Vector3(5, 1.85, -3.24), 96, Color(0.1, 0.2, 0.6))
	m.obj["pir"] = Vector3(5, 0, -3.0)
	# bike rack
	for i in range(4):
		var tor := TorusMesh.new()
		tor.inner_radius = 0.35
		tor.outer_radius = 0.38
		put(root, tor, Vector3(-9 + i * 0.7, 0.2, -3.5), Color(0.6, 0.6, 0.62), "stone", Vector3(0, PI / 2, PI / 2))
	bike(Vector3(-8.65, 0, -3.5), 0.0)
	m.add_obstacle_box(Vector3(-7.95, 0, -3.5), 2.6, 0.4, 0.0)
	m.set_obstacle_height(1.0)
	# barrier at the entrance
	put(root, m.box(0.3, 1.0, 0.3), Vector3(26, 0.5, -29), Color(0.85, 0.85, 0.85), "stone")
	put(root, m.box(0.08, 0.08, 4.0), Vector3(26, 1.0, -27), Color(0.85, 0.1, 0.1), "stone")
	m.add_obstacle(Vector3(26, 0, -29), 0.3)
	meadow(300, 34.0, 60.0, func(p: Vector3): return p.z < -28.0 and p.z > -36.0)
	for i in range(40):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(40, 120)), rng.randf_range(0.8, 1.5))
	for x in [-30.0, 30.0]:
		for i in range(5):
			tree(root, Vector3(x, 0, -4.0 - i * 6.0), rng.randf_range(0.8, 1.1), 0)


func park_route(v) -> void:
	"""a car comes from the road, drives into a free spot, waits, and drives away again"""
	var free: Array = data.get("free", [])
	var spot: Vector3 = free[rng.randi() % free.size()] if free.size() > 0 else Vector3(0, 0, -9)
	var lane := Vector3(spot.x, 0, -15.0)
	v.speed = 5.0
	v.route = [Vector3(26, 0, -15), lane, spot, [spot, 25.0, 0.0], lane, Vector3(-26, 0, -15), Vector3(-26, 0, -32.5), Vector3(-90, 0, -32.5)]


# ---- garden with house -----------------------------------------------------------------------------------------------
func _garten() -> void:
	road(-31.0)
	# the house: walls, roof, door (door sensor), lit windows, a light above the door
	var h := node(root, Vector3(-8.0, 0, -17.0), deg_to_rad(10.0))
	put(h, m.box(9.0, 5.4, 7.0), Vector3(0, 2.7, 0), Color(0.93, 0.9, 0.82), "caravan")
	var roof := PrismMesh.new()
	roof.size = Vector3(10.0, 2.6, 7.8)
	put(h, roof, Vector3(0, 6.7, 0), Color(0.55, 0.22, 0.16), "caravan", Vector3(0, PI / 2, 0), Vector3(7.8 / 10.0, 1, 10.0 / 7.8))
	var wm := window_mat()
	for p in [Vector3(-2.8, 1.6, 3.51), Vector3(2.6, 1.6, 3.51), Vector3(-2.8, 4.1, 3.51), Vector3(0.2, 4.1, 3.51), Vector3(2.6, 4.1, 3.51)]:
		put(h, m.box(1.3, 1.1, 0.05), p, wm, "window")
	m.door_node = node(h, Vector3(-0.5, 0, 3.52))
	put(m.door_node, m.box(1.0, 2.1, 0.06), Vector3(0.5, 1.05, 0), Color(0.35, 0.2, 0.12), "caravan")
	door_light_at(h, Vector3(0.0, 2.5, 4.2))
	m.obj["door"] = h.transform * Vector3(0.0, 0, 4.4)
	m.add_obstacle_node(h, Vector3.ZERO, 9.2, 7.2)
	for p2 in [Vector3(-2.8, 1.6, 3.53), Vector3(2.6, 1.6, 3.53), Vector3(-2.8, 4.1, 3.53), Vector3(0.2, 4.1, 3.53), Vector3(2.6, 4.1, 3.53)]:
		put(h, m.box(1.45, 1.25, 0.03), p2, Color(0.95, 0.95, 0.95), "caravan")        # window frames
		put(h, m.box(1.5, 0.08, 0.2), p2 + Vector3(0, -0.62, 0.08), Color(0.5, 0.45, 0.4), "caravan")   # sills
	put(h, m.box(0.5, 1.6, 0.5), Vector3(2.8, 7.4, -1.0), Color(0.5, 0.25, 0.2), "caravan")           # chimney
	smoke(h.transform * Vector3(2.8, 8.3, -1.0))
	laundry(Vector3(4.0, 0, -12.5), deg_to_rad(-8.0))
	put(h, m.box(1.6, 0.12, 1.0), Vector3(0.0, 2.75, 4.0), Color(0.4, 0.4, 0.42), "caravan")          # canopy over the door
	# terrace with table, chairs, a parasol (the PIR sensor is here)
	var terr: Vector3 = h.transform * Vector3(2.5, 0, 6.0)
	put(root, m.box(7.0, 0.1, 3.5), terr + Vector3(0, 0.05, 0), Color(0.6, 0.58, 0.55), "stone", Vector3(0, deg_to_rad(10), 0))
	put(root, m.box(1.2, 0.05, 0.8), terr + Vector3(0, 0.74, 0), Color(0.8, 0.8, 0.78), "stone")
	for s in [-1, 1]:
		put(root, m.box(0.45, 0.45, 0.45), terr + Vector3(0.9 * s, 0.23, 0), Color(0.6, 0.3, 0.1), "tent")
	put(root, cyl(0.03, 0.03, 2.3, 6), terr + Vector3(0, 1.15, 0), Color(0.8, 0.8, 0.8), "stone")
	put(root, cyl(0.0, 1.4, 0.5, 12), terr + Vector3(0, 2.35, 0), Color(0.85, 0.2, 0.2), "tent")
	m.obj["pir"] = terr
	m.add_obstacle(terr, 1.2)
	m.set_obstacle_height(1.0)
	# garden shed with the bike
	var sh := node(root, Vector3(10.0, 0, -15.0), deg_to_rad(-20.0))
	put(sh, m.box(2.6, 2.2, 2.0), Vector3(0, 1.1, 0), Color(0.3, 0.42, 0.3), "caravan")
	put(sh, m.box(3.0, 0.12, 2.4), Vector3(0, 2.25, 0), Color(0.2, 0.2, 0.2), "caravan")
	bike(sh.transform * Vector3(1.9, 0, 0.6), deg_to_rad(-20.0))
	m.add_obstacle_node(sh, Vector3.ZERO, 2.8, 2.2)
	# fence with hedge, a garden gate
	for x in range(-20, 21, 2):
		if x == 0:
			continue
		put(root, m.box(0.1, 1.1, 0.1), Vector3(x, 0.55, -26), Color(0.55, 0.4, 0.25), "tree")
	for y in [0.4, 0.9]:
		put(root, m.box(19.0, 0.08, 0.04), Vector3(-10.5, y, -26), Color(0.55, 0.4, 0.25), "tree")
		put(root, m.box(19.0, 0.08, 0.04), Vector3(10.5, y, -26), Color(0.55, 0.4, 0.25), "tree")
	for zz in range(-26, 3, 2):
		for x in [-20, 20]:
			put(root, m.box(0.1, 1.1, 0.1), Vector3(x, 0.55, zz), Color(0.55, 0.4, 0.25), "tree")
	for x in [-20.0, 20.0]:
		for y in [0.4, 0.9]:
			put(root, m.box(0.04, 0.08, 28.0), Vector3(x, y, -12.0), Color(0.55, 0.4, 0.25), "tree")
	var hm := ShaderMaterial.new()
	hm.shader = load("res://shaders/foliage.gdshader")
	hm.set_shader_parameter("noise_tex", m.noise_tex)
	hm.set_shader_parameter("color", Color(0.12, 0.3, 0.1))
	m.foliage_mats.append(hm)
	for x in [-10.5, 10.5]:                                       # hedge with a gap at the gate
		put(root, m.box(19.0, 1.8, 1.0), Vector3(x, 0.9, -27.2), hm, "tree")
		m.add_obstacle_box(Vector3(x, 0, -26.6), 19.0, 2.0, 0.0, true)   # fence + hedge: people use the gate (animals slip through)
	for x in [-20.0, 20.0]:
		m.add_obstacle_box(Vector3(x, 0, -12.0), 0.3, 28.0, 0.0, true)
	for x in [-1.0, 1.0]:                                          # gate posts
		put(root, m.box(0.14, 1.3, 0.14), Vector3(x, 0.65, -26), Color(0.45, 0.32, 0.2), "tree")
	put(root, m.box(1.2, 0.02, 6.0), Vector3(0, 0.015, -23.0), Color(0.62, 0.58, 0.52), "road")   # path from the gate
	data["gate"] = Vector3(0, 0, -26.0)
	# flower beds, a trampoline, an apple tree
	var fc := [Color(0.9, 0.2, 0.3), Color(0.95, 0.85, 0.2), Color(0.6, 0.3, 0.8), Color(1, 1, 1), Color(0.95, 0.5, 0.1)]
	for row in range(2):
		put(root, m.box(8.0, 0.12, 1.0), Vector3(8.0, 0.06, -5.5 - row * 2.0), Color(0.3, 0.2, 0.12), "stone")
		for i in range(14):
			put(root, sph(0.12), Vector3(4.4 + i * 0.55, 0.3 + rng.randf() * 0.15, -5.5 - row * 2.0 + rng.randf_range(-0.3, 0.3)), fc[rng.randi() % fc.size()], "tree")
	put(root, cyl(1.6, 1.6, 0.08, 24), Vector3(-6.0, 0.8, -6.0), Color(0.1, 0.1, 0.12), "stone")
	m.add_obstacle(Vector3(-6.0, 0, -6.0), 1.7)
	m.set_obstacle_height(0.9)
	for row2 in range(2):
		m.add_obstacle_box(Vector3(8.0, 0, -5.5 - row2 * 2.0), 8.0, 1.0, 0.0, true)
	put(root, TorusMesh.new(), Vector3(-6.0, 0.8, -6.0), Color(0.2, 0.4, 0.8), "stone", Vector3.ZERO, Vector3(1.6, 0.6, 1.6))
	for i in range(4):
		var a := i * TAU / 4.0 + 0.4
		put(root, m.box(0.06, 0.8, 0.06), Vector3(-6.0 + cos(a) * 1.5, 0.4, -6.0 + sin(a) * 1.5), Color(0.3, 0.3, 0.3), "stone")
	tree(root, Vector3(4.0, 0, -12.0), 1.0, 0)
	for i in range(6):
		put(root, sph(0.08), Vector3(4.0 + rng.randf_range(-1.2, 1.2), 3.6 + rng.randf_range(0, 1.5), -12.0 + rng.randf_range(-1.2, 1.2)), Color(0.8, 0.1, 0.1), "tree")
	lamp_post(Vector3(-12, 0, -34))
	lamp_post(Vector3(14, 0, -34))
	meadow(600, 3.0, 25.0, func(p: Vector3): return p.z < -25.0 or abs(p.x) > 19.5)
	for i in range(60):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(40, 120)), rng.randf_range(0.8, 1.5))


# ---- the funny place: a bench to sit on and things to watch -----------------------------------------------------------
func _lustig() -> void:
	put(root, m.box(3.0, 0.03, 30.0), Vector3(0, 0.015, -12), Color(0.7, 0.6, 0.45), "road")
	flag(Vector3(4.5, 0, -22.0), Color(0.95, 0.75, 0.1))
	bench(Vector3(0, 0, -17.0), 0.0)                    # visitors sit here and look at the show (and at the camera)
	data["bench"] = Vector3(0, 0, -16.8)
	bench(Vector3(-3.0, 0, -17.0), 0.0)
	data["bench2"] = Vector3(-3.0, 0, -16.8)
	label(root, "Bitte lächeln!\nSie werden beobachtet :-)", Vector3(3.2, 2.3, -17.5), 64)
	put(root, m.box(2.6, 1.0, 0.06), Vector3(3.2, 2.3, -17.56), Color(1.0, 0.95, 0.7), "tree")
	put(root, m.box(0.08, 1.8, 0.08), Vector3(3.2, 0.9, -17.6), Color(0.5, 0.35, 0.2), "tree")
	m.add_obstacle(Vector3(3.2, 0, -17.6), 0.25)
	m.obj["pir"] = Vector3(0, 0, -16.0)
	hut(Vector3(-14.0, 0, -20.0), deg_to_rad(30.0), Color(0.75, 0.45, 0.6))
	bike(Vector3(-11.0, 0, -17.0), 0.4)
	_carousel(Vector3(6.5, 0, -10.0))
	_ducks(Vector3(-6.0, 0, -9.0))
	_scarecrow(Vector3(10.0, 0, -18.0))
	_gnome(Vector3(-1.8, 0, -7.0))
	_light_chain(Vector3(-8, 3.2, -13.5), Vector3(9, 3.2, -13.5), 14)
	lamp_post(Vector3(1.6, 0, -18.2), 3.2)
	for i in range(70):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(24, 110)), rng.randf_range(0.8, 1.4))
	meadow(600, 3.0, 30.0, func(p: Vector3): return abs(p.x) < 1.6 and p.z < 3.0 and p.z > -27.0)


func _carousel(c: Vector3) -> void:
	var k := node(root, c)
	m.add_obstacle(c, 2.6)
	put(k, cyl(2.4, 2.4, 0.25, 24), Vector3(0, 0.12, 0), Color(0.85, 0.85, 0.8), "stone")
	put(k, cyl(0.1, 0.1, 3.0, 8), Vector3(0, 1.5, 0), Color(0.9, 0.75, 0.2), "stone")
	var rotor := node(k, Vector3.ZERO)
	put(rotor, cyl(0.0, 2.7, 1.0, 16), Vector3(0, 3.4, 0), Color(0.85, 0.15, 0.2), "tent")
	put(rotor, cyl(2.4, 2.4, 0.3, 16), Vector3(0, 2.8, 0), Color(1.0, 0.95, 0.85), "tent")
	var horses := []
	var cols := [Color(1, 1, 1), Color(0.3, 0.5, 0.9), Color(0.95, 0.7, 0.2), Color(0.5, 0.8, 0.4)]
	for i in range(4):
		var a := i * TAU / 4.0
		var p := Vector3(cos(a) * 1.7, 0, sin(a) * 1.7)
		put(rotor, cyl(0.03, 0.03, 2.6, 6), p + Vector3(0, 1.5, 0), Color(0.9, 0.75, 0.2), "stone")
		var hs := node(rotor, p + Vector3(0, 1.0, 0), -a)
		put(hs, m.box(0.25, 0.35, 0.8), Vector3.ZERO, cols[i], "tent")
		put(hs, m.box(0.2, 0.4, 0.25), Vector3(0, 0.3, -0.4), cols[i], "tent", Vector3(0.4, 0, 0))
		for z in [-0.3, 0.3]:
			put(hs, m.box(0.08, 0.45, 0.08), Vector3(0, -0.35, z), cols[i].darkened(0.3), "tent")
		horses.append(hs)
	var bulbs := []
	for i in range(12):
		var a := i * TAU / 12.0
		var b := put(rotor, sph(0.08), Vector3(cos(a) * 2.4, 2.65, sin(a) * 2.4), glow_mat(Color.from_hsv(i / 12.0, 0.7, 1.0)), 40.0)
		bulbs.append(b)
	var disco := OmniLight3D.new()
	disco.position = Vector3(0, 2.4, 0)
	disco.omni_range = 9.0
	disco.light_energy = 0.0
	k.add_child(disco)
	m.lamps.append(disco)
	m.anims.append(func(_dt, t):
		rotor.rotation.y = t * 0.7
		for i in range(horses.size()):
			horses[i].position.y = 1.0 + 0.25 * sin(t * 2.2 + i * PI / 2.0)
		if disco.light_energy > 0.0:
			disco.light_color = Color.from_hsv(fmod(t * 0.15, 1.0), 0.8, 1.0))


func _ducks(c: Vector3) -> void:
	"""a mother duck with her little ones, going round the pond for ever"""
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.2, 0.4, 0.6)
	wm.roughness = 0.1
	wm.metallic = 0.3
	put(root, cyl(2.4, 2.4, 0.04, 32), c + Vector3(0, 0.03, 0), wm, "pond")
	if not data.has("clear"):
		data["clear"] = []
	data["clear"].append([Vector2(c.x, c.z), 5.0])
	put(root, TorusMesh.new(), c + Vector3(0, 0.03, 0), Color(0.45, 0.42, 0.38), "stone", Vector3.ZERO, Vector3(2.45, 0.15, 2.45))   # stone rim
	for i in range(5):                                                                             # reeds
		var a := rng.randf() * TAU
		for k in range(4):
			put(root, cyl(0.01, 0.015, 0.9, 4), c + Vector3(cos(a) * 2.2 + k * 0.06, 0.45, sin(a) * 2.2), Color(0.35, 0.45, 0.2), "tree", Vector3(rng.randf_range(-0.15, 0.15), 0, rng.randf_range(-0.15, 0.15)))
	m.add_obstacle(c, 2.5)
	m.set_obstacle_height(0.1)
	var ducks := []
	for i in range(6):
		var s := 1.0 if i == 0 else 0.6
		var d := node(root, c)
		var col := Color(0.55, 0.45, 0.3) if i == 0 else Color(0.98, 0.88, 0.25)
		put(d, sph(0.22 * s, 0.32 * s), Vector3(0, 0.2 * s, 0), col, 38.0)
		put(d, sph(0.12 * s), Vector3(0, 0.42 * s, -0.17 * s), Color(0.15, 0.45, 0.2) if i == 0 else col, 39.0)
		put(d, m.box(0.08 * s, 0.04 * s, 0.12 * s), Vector3(0, 0.4 * s, -0.31 * s), Color(1.0, 0.55, 0.1), 36.0)
		ducks.append(d)
	m.anims.append(func(_dt, t):
		for i in range(ducks.size()):
			var a: float = t * 0.35 - i * 0.28
			ducks[i].position = c + Vector3(cos(a) * 3.1, 0, sin(a) * 3.1)
			ducks[i].rotation = Vector3(0, PI - a, 0.15 * sin(t * 9.0 + i)))   # head forward (3D-3.26: before they swam backwards)


func _scarecrow(p: Vector3) -> void:
	var s := node(root, p, 0.3)
	m.add_obstacle(p, 0.4)
	put(s, m.box(0.08, 1.8, 0.08), Vector3(0, 0.9, 0), Color(0.45, 0.32, 0.2), "tree")
	put(s, m.box(0.5, 0.6, 0.25), Vector3(0, 1.45, 0), Color(0.35, 0.5, 0.75), "tent")
	put(s, sph(0.2), Vector3(0, 1.95, 0), Color(0.95, 0.85, 0.55), "tent")
	put(s, cyl(0.15, 0.4, 0.15, 12), Vector3(0, 2.15, 0), Color(0.6, 0.45, 0.2), "tent")
	put(s, cyl(0.12, 0.15, 0.3, 12), Vector3(0, 2.35, 0), Color(0.6, 0.45, 0.2), "tent")
	put(s, m.box(0.6, 0.08, 0.08), Vector3(-0.5, 1.65, 0), Color(0.35, 0.5, 0.75), "tent")
	var arm := node(s, Vector3(0.25, 1.65, 0))
	put(arm, m.box(0.6, 0.08, 0.08), Vector3(0.3, 0, 0), Color(0.35, 0.5, 0.75), "tent")
	put(arm, sph(0.07), Vector3(0.62, 0, 0), Color(0.95, 0.85, 0.55), "tent")
	m.anims.append(func(_dt, t): arm.rotation.z = 0.6 + 0.5 * sin(t * 3.5))


func _gnome(p: Vector3) -> void:
	"""a garden gnome hides behind a stone and peeks out every few seconds"""
	put(root, sph(0.55, 0.7), p + Vector3(0, 0.2, 0), Color(0.48, 0.48, 0.46), "stone")
	m.add_obstacle(p, 0.6)
	m.set_obstacle_height(0.8)
	var g := node(root, p + Vector3(0.2, 0, -0.5))
	put(g, cyl(0.15, 0.2, 0.35, 10), Vector3(0, 0.2, 0), Color(0.2, 0.35, 0.7), 31.0)
	put(g, sph(0.13), Vector3(0, 0.48, 0), Color(0.95, 0.75, 0.6), 34.0)
	put(g, cyl(0.0, 0.14, 0.35, 10), Vector3(0, 0.72, 0), Color(0.85, 0.1, 0.1), 30.0)
	put(g, sph(0.1, 0.15), Vector3(0, 0.4, 0.08), Color(0.95, 0.95, 0.95), 30.0)
	m.anims.append(func(_dt, t):
		var k: float = clamp(sin(t * 0.9) * 3.0 - 1.5, 0.0, 1.0)
		g.position.y = -0.85 + 0.85 * k
		g.position.x = p.x + 0.2 + 0.45 * k)


func _light_chain(a: Vector3, b: Vector3, n: int) -> void:
	for x in [a, b]:
		put(root, m.box(0.08, x.y, 0.08), Vector3(x.x, x.y / 2.0, x.z), Color(0.4, 0.3, 0.2), "tree")
		m.add_obstacle(Vector3(x.x, 0, x.z), 0.2)
	for i in range(n):
		var f := (i + 0.5) / n
		var p := a.lerp(b, f) + Vector3(0, -0.6 * sin(f * PI), 0)
		put(root, sph(0.09), p, glow_mat(Color.from_hsv(fmod(i * 0.17, 1.0), 0.75, 1.0)), 35.0)


func garden_route(v) -> void:
	"""somebody comes from the street through the garden gate, to the terrace, rings at the door and goes back out"""
	var side := 1.0 if v.position.x > 0 else -1.0
	var gate: Vector3 = data.get("gate", Vector3(0, 0, -26))
	v.target = Vector3(0, 0, -30.0)
	v.route = [gate + Vector3(0, 0, -1.2), gate + Vector3(0, 0, 1.5), m.obj["pir"] + Vector3(0, 0, 2.2), [m.obj["door"], rng.randf_range(4.0, 10.0), 0.0],
			gate + Vector3(0, 0, 1.5), gate + Vector3(0, 0, -1.2), Vector3(-side * 40.0, 0, -30.5)]


func bench_route(v, which := "bench") -> void:
	"""somebody comes, sits on the bench for a while, watches the show - and goes on"""
	var b: Vector3 = data.get(which, Vector3(0, 0, -16.8))
	var out := Vector3(-30.0 if v.position.x > 0 else 30.0, 0, -18.0)
	v.target = b
	v._face(b)
	v.route = [[b, rng.randf_range(20.0, 40.0), 0.6, b + Vector3(0, 0, 5)], out]


# ---- wildlife watching: a high seat, a feeder, the forest edge ----------------------------------------------------------
func _wild() -> void:
	# high seat next to the camera
	var hs := node(root, Vector3(-8.0, 0, 6.0), deg_to_rad(15.0))          # behind the fixed camera 1, out of its picture
	for x in [-0.8, 0.8]:
		for z in [-0.8, 0.8]:
			put(hs, m.box(0.12, 3.2, 0.12), Vector3(x, 1.6, z), Color(0.4, 0.28, 0.16), "tree")
	put(hs, m.box(1.9, 0.1, 1.9), Vector3(0, 3.2, 0), Color(0.45, 0.32, 0.18), "tree")
	put(hs, m.box(1.9, 1.0, 0.06), Vector3(0, 3.75, -0.92), Color(0.42, 0.3, 0.17), "tree")
	put(hs, m.box(2.1, 0.08, 2.1), Vector3(0, 4.8, 0), Color(0.3, 0.22, 0.14), "tree")
	for x in [-0.9, 0.9]:
		put(hs, m.box(0.08, 1.6, 0.08), Vector3(x, 4.0, -0.9), Color(0.4, 0.28, 0.16), "tree")
	for i in range(8):
		put(hs, m.box(0.6, 0.05, 0.06), Vector3(0, 0.3 + i * 0.4, 1.3), Color(0.4, 0.28, 0.16), "tree")
	m.add_obstacle_node(hs, Vector3(0, 0, 0.2), 2.0, 2.4)
	# hunting hut at the side (door sensor) with the bike
	hut(m.pos_of(-70.0, 14.0), deg_to_rad(70.0), Color(0.4, 0.3, 0.2))
	bike(m.pos_of(-60.0, 12.0), 0.2)
	# the feeder (the animals come to eat here; the PIR sensor is here), a salt lick
	var f := Vector3(-1.5, 0, -16.0)
	var fd := node(root, f)
	for x in [-1.0, 1.0]:
		put(fd, m.box(0.1, 1.6, 0.1), Vector3(x, 0.8, 0), Color(0.4, 0.28, 0.16), "tree")
	put(fd, m.box(2.0, 0.6, 0.6), Vector3(0, 0.6, 0), Color(0.45, 0.32, 0.18), "tree")
	put(fd, m.box(1.9, 0.25, 0.5), Vector3(0, 0.95, 0), Color(0.85, 0.75, 0.35), "tree")
	var roof := PrismMesh.new()
	roof.size = Vector3(2.4, 0.5, 1.2)
	put(fd, roof, Vector3(0, 1.85, 0), Color(0.3, 0.22, 0.14), "tree")
	m.add_obstacle_box(f, 2.2, 0.7, 0.0)
	m.set_obstacle_height(2.0)
	for i in range(8):                                                     # hay on the ground
		put(root, m.box(0.5, 0.06, 0.25), f + Vector3(rng.randf_range(-1.3, 1.3), 0.03, rng.randf_range(0.5, 1.6)), Color(0.85, 0.75, 0.35), "tree", Vector3(0, rng.randf() * PI, 0))
	data["feeder"] = f
	m.obj["pir"] = f
	put(root, m.box(0.15, 1.1, 0.15), Vector3(7.0, 0.55, -21.0), Color(0.4, 0.28, 0.16), "tree")
	put(root, m.box(0.3, 0.25, 0.3), Vector3(7.0, 1.2, -21.0), Color(0.9, 0.9, 0.9), "stone")
	m.add_obstacle(Vector3(7.0, 0, -21.0), 0.2)
	data["salt"] = Vector3(7.0, 0, -21.0)
	stones(6, 5.0, 20.0)
	for i in range(10):
		var bp: Vector3 = m.pos_of(rng.randf_range(-70, 70), rng.randf_range(8, 30))
		put(root, sph(0.4, 0.5), bp + Vector3(0, 0.1, 0), Color(0.2, 0.32, 0.14), "tree")
		m.add_obstacle(bp, 0.35)
	meadow(900, 3.0, 40.0)
	# forest edge behind the meadow and on both sides
	trees(260, 20.0, 120.0, func(p: Vector3): return p.z > -32.0 and abs(p.x) < 28.0)


func feed_route(v) -> void:
	"""an animal comes out of the forest to the feeder (or the salt lick), eats for a while and goes back"""
	var at: Vector3 = data.get("feeder", Vector3(0, 0, -16)) if rng.randf() < 0.7 else data.get("salt", Vector3(7, 0, -21))
	var p := at + Vector3(rng.randf_range(-1.2, 1.2), 0, rng.randf_range(0.9, 1.5))
	var back := Vector3(rng.randf_range(-25, 25), 0, -45.0)
	v.target = p
	v.route = [[p, rng.randf_range(12.0, 30.0), 0.0, at], back]
	v._face(p)


# ---- hiding places (from 3D-3.13): things to hide behind in the games - every one is an obstacle with its height ----------
const PROP_KINDS := ["bush", "bush", "hedge", "woodpile", "crates", "barrels", "haybale", "rock", "shed", "car", "container", "wall", "pallets",
		"trailer", "compost"]


func prop(kind: String, p: Vector3, rot_y: float) -> void:
	"""one hiding place at p (on the ground), turned by rot_y"""
	p.y = m.ground_y(p.x, p.z)
	match kind:
		"bush":                                                   # a big round bush (1.2 - 1.8 m)
			var s := rng.randf_range(0.8, 1.25)
			var n := node(root, p, rot_y)
			var fm := foliage(rng.randi_range(0, 5))
			for k in range(rng.randi_range(4, 6)):
				var r := rng.randf_range(0.55, 0.85) * s
				put(n, sph(r, r * 1.6), Vector3(rng.randf_range(-0.6, 0.6) * s, r * 0.75 + rng.randf_range(0.0, 0.3), rng.randf_range(-0.6, 0.6) * s), fm, "tree")
			m.add_obstacle(p, 0.95 * s)
			m.set_obstacle_height(1.5 * s)
		"hedge":                                                  # a piece of hedge, 5 - 9 m long, 1.7 m high
			var l := rng.randf_range(5.0, 9.0)
			put(root, m.box(l, 1.7, 0.9), p + Vector3(0, 0.85, 0), foliage(2), "tree", Vector3(0, rot_y, 0))
			m.add_obstacle_box(p, l, 1.0, rot_y)
			m.set_obstacle_height(1.7)
		"woodpile":                                               # stacked firewood
			var n := node(root, p, rot_y)
			for row in range(5):
				for k in range(9):
					put(n, cyl(0.12, 0.12, 0.9, 7), Vector3(-1.1 + k * 0.27 + (0.13 if row % 2 else 0.0), 0.12 + row * 0.22, 0), Color(0.5, 0.36, 0.22).lerp(Color(0.62, 0.47, 0.3), rng.randf()), "tree", Vector3(PI / 2, 0, 0))
			put(n, m.box(2.7, 0.05, 1.2), Vector3(0, 1.25, 0), Color(0.3, 0.3, 0.32), "stone", Vector3(0.12, 0, 0))     # roof sheet
			m.add_obstacle_node(n, Vector3.ZERO, 2.6, 1.1)
			m.set_obstacle_height(1.3)
		"crates":                                                 # wooden crates, some on top
			var n := node(root, p, rot_y)
			var cc := Color(0.62, 0.48, 0.3)
			for k in range(4):
				put(n, m.box(1.0, 1.0, 1.0), Vector3(-0.55 + (k % 2) * 1.1, 0.5 + (k / 2) * 1.0, 0.0 if k < 2 else -0.0), cc.darkened(rng.randf() * 0.25), "tent", Vector3(0, rng.randf_range(-0.1, 0.1), 0))
			put(n, m.box(1.0, 1.0, 1.0), Vector3(0.2, 0.5, 1.15), cc.darkened(0.15), "tent")
			m.add_obstacle_node(n, Vector3(0, 0, 0.5), 2.3, 2.3)
			m.set_obstacle_height(2.0)
		"barrels":                                                # a group of barrels
			var n := node(root, p, rot_y)
			var bc: Color = [Color(0.15, 0.35, 0.6), Color(0.6, 0.15, 0.1), Color(0.2, 0.45, 0.2)][rng.randi() % 3]
			for k in range(5):
				var a := k * TAU / 5.0
				put(n, cyl(0.3, 0.3, 0.9, 12), Vector3(cos(a) * 0.55, 0.45, sin(a) * 0.55), bc.darkened(rng.randf() * 0.2), "stone")
			put(n, cyl(0.3, 0.3, 0.9, 12), Vector3(0, 0.45, 0), bc, "stone")
			m.add_obstacle(p, 1.0)
			m.set_obstacle_height(0.95)
		"haybale":                                                # round bales of hay (1.4 m), two or three
			var n := node(root, p, rot_y)
			for k in range(rng.randi_range(2, 3)):
				put(n, cyl(0.7, 0.7, 1.2, 16), Vector3(-1.0 + k * 1.3, 0.7, rng.randf_range(-0.2, 0.2)), Color(0.82, 0.72, 0.42).darkened(rng.randf() * 0.15), "tree", Vector3(PI / 2, rng.randf_range(-0.2, 0.2), 0))
			m.add_obstacle_node(n, Vector3(0.3, 0, 0), 4.0, 1.5)
			m.set_obstacle_height(1.4)
		"rock":                                                   # a boulder (1 - 2 m)
			var s := rng.randf_range(1.0, 2.0)
			var rk := put(root, sph(s * 0.8, s * 1.1), p + Vector3(0, s * 0.35, 0), Color(0.5, 0.5, 0.48).darkened(rng.randf() * 0.2), "stone", Vector3(rng.randf_range(-0.2, 0.2), rot_y, 0), Vector3(1.0, 0.8, rng.randf_range(0.7, 1.1)))
			put(root, sph(s * 0.45, s * 0.6), p + Vector3(s * 0.7, s * 0.15, 0.2), Color(0.46, 0.46, 0.44), "stone")
			m.add_obstacle(p, s * 0.8)
			m.set_obstacle_height(s * 0.9)
		"shed":                                                   # a small garden shed
			var n := node(root, p, rot_y)
			var col: Color = [Color(0.45, 0.3, 0.18), Color(0.3, 0.38, 0.28), Color(0.55, 0.2, 0.15)][rng.randi() % 3]
			put(n, m.box(2.4, 2.1, 1.9), Vector3(0, 1.05, 0), col, "caravan")
			var roof := PrismMesh.new()
			roof.size = Vector3(2.8, 0.8, 2.3)
			put(n, roof, Vector3(0, 2.5, 0), col.darkened(0.35), "caravan")
			put(n, m.box(0.8, 1.8, 0.04), Vector3(0.4, 0.9, 0.97), col.darkened(0.25), "caravan")
			m.add_obstacle_node(n, Vector3.ZERO, 2.6, 2.1)
			m.set_obstacle_height(2.6)
		"car":
			static_car(p, rot_y, [Color(0.75, 0.75, 0.78), Color(0.15, 0.18, 0.22), Color(0.6, 0.12, 0.1), Color(0.2, 0.35, 0.6), Color(0.85, 0.85, 0.82)][rng.randi() % 5])
		"container":                                              # a shipping container
			var n := node(root, p, rot_y)
			var col: Color = [Color(0.65, 0.2, 0.12), Color(0.15, 0.35, 0.55), Color(0.3, 0.45, 0.25)][rng.randi() % 3]
			put(n, m.box(6.0, 2.6, 2.45), Vector3(0, 1.3, 0), col, "caravan")
			for k in range(12):
				put(n, m.box(0.06, 2.4, 2.5), Vector3(-2.75 + k * 0.5, 1.3, 0), col.darkened(0.2), "caravan")
			m.add_obstacle_node(n, Vector3.ZERO, 6.1, 2.6)
			m.set_obstacle_height(2.6)
		"wall":                                                   # a stone wall (1.3 m)
			var l := rng.randf_range(4.0, 8.0)
			put(root, m.box(l, 1.3, 0.5), p + Vector3(0, 0.65, 0), Color(0.58, 0.56, 0.52), "stone", Vector3(0, rot_y, 0))
			m.add_obstacle_box(p, l, 0.6, rot_y)
			m.set_obstacle_height(1.3)
		"pallets":                                                # stacked pallets
			var n := node(root, p, rot_y)
			for k in range(rng.randi_range(6, 9)):
				put(n, m.box(1.2, 0.14, 0.8), Vector3(rng.randf_range(-0.04, 0.04), 0.07 + k * 0.15, 0), Color(0.68, 0.55, 0.38), "tree", Vector3(0, rng.randf_range(-0.06, 0.06), 0))
			put(n, m.box(1.2, 0.14, 0.8), Vector3(1.35, 0.07, 0), Color(0.68, 0.55, 0.38), "tree")
			m.add_obstacle_node(n, Vector3(0.6, 0, 0), 2.6, 1.0)
			m.set_obstacle_height(1.2)
		"trailer":                                                # a farm trailer
			var n := node(root, p, rot_y)
			put(n, m.box(2.2, 0.8, 4.0), Vector3(0, 1.0, 0), Color(0.55, 0.15, 0.1), "caravan")
			put(n, m.box(2.0, 0.1, 3.8), Vector3(0, 0.62, 0), Color(0.3, 0.3, 0.3), "stone")
			for sx in [-1.0, 1.0]:
				put(n, cyl(0.38, 0.38, 0.3, 14), Vector3(sx * 1.0, 0.38, 0.4), Color(0.05, 0.05, 0.05), "stone", Vector3(0, 0, PI / 2))
			put(n, m.box(0.1, 0.1, 1.4), Vector3(0, 0.6, -2.6), Color(0.2, 0.2, 0.2), "stone")
			m.add_obstacle_node(n, Vector3.ZERO, 2.3, 4.2)
			m.set_obstacle_height(1.4)
		"compost":                                                # wooden compost boxes
			var n := node(root, p, rot_y)
			for k in range(2):
				for side in range(4):
					var off: Vector3 = [Vector3(0, 0, 0.5), Vector3(0, 0, -0.5), Vector3(0.5, 0, 0), Vector3(-0.5, 0, 0)][side]
					var sz := Vector3(1.0, 0.9, 0.05) if side < 2 else Vector3(0.05, 0.9, 1.0)
					put(n, m.box(sz.x, sz.y, sz.z), Vector3(-0.55 + k * 1.1, 0.45, 0) + off, Color(0.45, 0.33, 0.2), "tree")
			m.add_obstacle_node(n, Vector3.ZERO, 2.3, 1.2)
			m.set_obstacle_height(0.9)
		"boat":                                                   # a rowing boat pulled onto the shore, upside down
			var n := node(root, p, rot_y)
			var bcol: Color = [Color(0.85, 0.85, 0.82), Color(0.2, 0.4, 0.6), Color(0.6, 0.18, 0.12), Color(0.5, 0.36, 0.22)][rng.randi() % 4]
			put(n, sph(0.8, 1.0), Vector3(0, 0.2, 0), bcol, "caravan", Vector3.ZERO, Vector3(1.0, 0.7, 2.9))
			put(n, m.box(1.5, 0.08, 4.2), Vector3(0, 0.55, 0), bcol.darkened(0.3), "caravan")
			put(n, cyl(0.03, 0.03, 2.4, 6), Vector3(0.9, 0.08, 0.2), Color(0.55, 0.4, 0.25), "tree", Vector3(PI / 2, 0, 0))
			m.add_obstacle_node(n, Vector3.ZERO, 1.7, 4.6)
			m.set_obstacle_height(0.75)
		"reeds":                                                  # a thick clump of reeds (2 m)
			var n := node(root, p, rot_y)
			for k in range(26):
				var q := Vector2.from_angle(rng.randf() * TAU) * sqrt(rng.randf()) * 1.6
				var hh := rng.randf_range(1.4, 2.2)
				put(n, cyl(0.015, 0.03, hh, 4), Vector3(q.x, hh / 2.0, q.y), Color(0.45, 0.55, 0.25).lerp(Color(0.65, 0.6, 0.35), rng.randf()), "tree", Vector3(rng.randf_range(-0.1, 0.1), 0, rng.randf_range(-0.1, 0.1)))
			for k in range(6):
				var q2 := Vector2.from_angle(rng.randf() * TAU) * rng.randf() * 1.4
				put(n, cyl(0.05, 0.05, 0.35, 6), Vector3(q2.x, rng.randf_range(1.7, 2.1), q2.y), Color(0.38, 0.25, 0.15), "tree")
			m.add_obstacle(p, 1.6)
			m.set_obstacle_height(1.9)
		"bench":
			bench(p, rot_y)
		_:
			prop("bush", p, rot_y)


func hide_props(n: int, dmin: float, dmax: float, kinds: Array, keep_clear := Callable()) -> int:
	"""n hiding places between dmin and dmax from MoveEye, away from each other and from obstacles; returns how many"""
	if clip > 0.0:
		dmax = minf(dmax, clip - 2.0)
		dmin = minf(dmin, dmax * 0.5)
	var made := 0
	var tries := 0
	while made < n and tries < n * 12:
		tries += 1
		var p: Vector3 = m.pos_of(rng.randf_range(-180, 180), rng.randf_range(dmin, dmax))
		if (keep_clear.is_valid() and keep_clear.call(p)) or _out(p):
			continue
		var ok := true
		for o in m._ob_near(Vector2(p.x, p.z)):
			if float(m._ob_closest(o, Vector2(p.x, p.z))[1]) < 3.0:
				ok = false
				break
		for cl in data.get("clear", []):
			if Vector2(p.x, p.z).distance_to(cl[0]) < float(cl[1]):
				ok = false
		if p.length() < 6.0:
			ok = false
		if not ok or (data.has("road_z") and abs(p.z - (float(data["road_z"]) - 1.2)) < 5.0):
			continue
		prop(kinds[rng.randi() % kinds.size()], p, rng.randf() * TAU)
		made += 1
	return made


# ---- hiding game (from 3D-3.13): a yard full of things to hide behind ---------------------------------------------------
func _verstecken() -> void:
	road(-60.0, 6.0)
	put(root, m.box(26, 0.03, 18), Vector3(20, 0.015, -20), Color(0.55, 0.52, 0.45), "road")       # gravel yard by the containers
	var h := hut(m.pos_of(-35.0, 14.0), deg_to_rad(30.0))
	bike(m.pos_of(25.0, 7.0), deg_to_rad(80.0))
	var tn := node(root, m.pos_of(12.0, 6.0), deg_to_rad(-10.0))
	var tent := PrismMesh.new()
	tent.size = Vector3(2.6, 1.5, 2.4)
	put(tn, tent, Vector3(0, 0.75, 0), Color(0.25, 0.55, 0.3), "tent")
	m.obj["pir"] = m.pos_of(12.0, 6.0)
	m.add_obstacle_node(tn, Vector3.ZERO, 3.0, 2.8)
	m.set_obstacle_height(1.4)
	# a little maze of hedges on the left, a container yard on the right, the rest spread
	for i in range(5):
		prop("hedge", Vector3(-28.0 + (i % 2) * 4.0, 0, -12.0 - i * 6.0), 0.0 if i % 2 == 0 else 0.25)
	for i in range(4):
		prop("container", Vector3(18.0 + (i % 2) * 7.5, 0, -16.0 - (i / 2) * 9.0), PI / 2 * (i % 2) * 0.0 + rng.randf_range(-0.1, 0.1))
	hide_props(30, 6.0, 26.0, ["bush", "crates", "barrels", "woodpile", "rock", "pallets", "compost", "haybale"],
			func(p: Vector3): return p.distance_to(h.position) < 6.0)
	hide_props(30, 20.0, 50.0, ["bush", "bush", "woodpile", "crates", "barrels", "haybale", "rock", "shed", "car", "wall", "pallets", "trailer", "compost"],
			func(p: Vector3): return p.distance_to(h.position) < 6.0)
	trees(60, 20.0, 90.0, func(p: Vector3): return abs(p.z + 22.0) < 26.0 and abs(p.x) < 36.0)
	meadow(400, 3.0, 40.0, func(p: Vector3): return abs(p.z + 22.0) < 25.0 and abs(p.x) < 35.0)


# ---- 3D-3.73: «Mein Zuhause» - built from the things the operator placed (main.home_items, user://zuhause.json) -----------
const HOME_KINDS := [["haus", "Haus"], ["gartenhaus", "Gartenhaus"], ["garage", "Garage"], ["zaun", "Zaun (2 Klicks)"], ["hecke", "Hecke (2 Klicks)"],
		["mauer", "Mauer (2 Klicks)"], ["weg", "Weg (2 Klicks)"], ["baum", "Laubbaum"], ["tanne", "Tanne"], ["busch", "Busch"], ["auto", "Auto"],
		["velo", "Velo"], ["bank", "Bank"], ["tisch", "Tisch + Stühle"], ["grill", "Grill"], ["trampolin", "Trampolin"], ["beet", "Blumenbeet"],
		["laterne", "Laterne"], ["sandkasten", "Sandkasten"], ["pool", "Planschbecken"]]
const HOME_LINES := ["zaun", "hecke", "mauer", "weg"]
const HOME_DEFAULT := [{"k": "haus", "x": -6.0, "z": -16.0, "r": 0.0, "s": 1.0}, {"k": "zaun", "x": -18.0, "z": -25.0, "x2": 18.0, "z2": -25.0, "r": 0.0, "s": 1.0},
		{"k": "baum", "x": 9.0, "z": -12.0, "r": 0.0, "s": 1.0}, {"k": "auto", "x": 8.0, "z": -20.0, "r": 90.0, "s": 1.0},
		{"k": "velo", "x": 4.0, "z": -9.0, "r": 30.0, "s": 1.0}, {"k": "tisch", "x": -3.0, "z": -8.0, "r": 0.0, "s": 1.0}]


func _zuhause() -> void:
	road(-34.0)
	var items: Array = m.home_items if not m.home_items.is_empty() else HOME_DEFAULT
	data["home_nodes"] = []
	var has_door := false
	data["door_done"] = false
	m.obj["pir"] = Vector3(0, 0, -8)
	m.obj["bike"] = Vector3(4, 0, -9)
	for it in items:
		var n := home_item(it)
		data["home_nodes"].append(n)
		if str(it.get("k", "")) == "haus" and not has_door:
			has_door = true
	if not has_door:                                               # every scene needs a door (sensor): a small one, far away
		var h := node(root, Vector3(0, 0, -60))
		m.door_node = node(h, Vector3(0, 0, 0))
		put(m.door_node, m.box(1.0, 2.1, 0.06), Vector3(0.5, 1.05, 0), Color(0.35, 0.2, 0.12), "caravan")
		door_light_at(h, Vector3(0.0, 2.5, 0.6))
		m.obj["door"] = Vector3(0, 0, -59)
	meadow(600, 3.0, 40.0)
	stones(6, 4.0, 15.0)
	for i in range(60):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(45, 120)), rng.randf_range(0.8, 1.4))


func _hm() -> ShaderMaterial:
	var hm := ShaderMaterial.new()
	hm.shader = load("res://shaders/foliage.gdshader")
	hm.set_shader_parameter("noise_tex", m.noise_tex)
	hm.set_shader_parameter("color", Color(0.12, 0.3, 0.1))
	m.foliage_mats.append(hm)
	return hm


func home_item(it: Dictionary) -> Node3D:
	"""one thing of «Mein Zuhause»: kind k at x, z, turned r degrees, size s (lines: from x, z to x2, z2)"""
	var k := str(it.get("k", ""))
	var p := Vector3(float(it.get("x", 0.0)), 0, float(it.get("z", 0.0)))
	p.y = m.ground_y(p.x, p.z)
	var r := deg_to_rad(float(it.get("r", 0.0)))
	var sc := clampf(float(it.get("s", 1.0)), 0.3, 3.0)
	if k in HOME_LINES:
		var q := Vector3(float(it.get("x2", p.x + 4.0)), 0, float(it.get("z2", p.z)))
		var d := q - p
		var ln := maxf(0.5, Vector2(d.x, d.z).length())
		var ang := atan2(-d.z, d.x)
		var c := node(root, (p + q) / 2.0, ang)
		c.position.y = m.ground_y(c.position.x, c.position.z)
		match k:
			"zaun":
				var nposts := int(ln / 2.0) + 1
				for i in range(nposts + 1):
					put(c, m.box(0.1, 1.1, 0.1), Vector3(-ln / 2.0 + ln * i / max(1, nposts), 0.55, 0), Color(0.55, 0.4, 0.25), "tree")
				for y in [0.4, 0.9]:
					put(c, m.box(ln, 0.08, 0.04), Vector3(0, y, 0), Color(0.55, 0.4, 0.25), "tree")
				m.add_obstacle_box(c.position, ln, 0.3, ang, true)
			"hecke":
				put(c, m.box(ln, 1.8 * sc, 1.0), Vector3(0, 0.9 * sc, 0), _hm(), "tree")
				m.add_obstacle_box(c.position, ln, 1.1, ang, true)
				m.set_obstacle_height(1.8 * sc)
			"mauer":
				put(c, m.box(ln, 1.2 * sc, 0.3), Vector3(0, 0.6 * sc, 0), Color(0.7, 0.68, 0.64), "stone")
				m.add_obstacle_box(c.position, ln, 0.4, ang, true)
				m.set_obstacle_height(1.2 * sc)
			"weg":
				put(c, m.box(ln, 0.02, 1.2 * sc), Vector3(0, 0.015, 0), Color(0.62, 0.58, 0.52), "road")
		return c
	var n := node(root, p, r)
	n.scale = Vector3.ONE * sc
	match k:
		"haus":
			put(n, m.box(9.0, 5.4, 7.0), Vector3(0, 2.7, 0), Color(0.93, 0.9, 0.82), "caravan")
			var roof := PrismMesh.new()
			roof.size = Vector3(10.0, 2.6, 7.8)
			put(n, roof, Vector3(0, 6.7, 0), Color(0.55, 0.22, 0.16), "caravan", Vector3(0, PI / 2, 0), Vector3(7.8 / 10.0, 1, 10.0 / 7.8))
			var wm := window_mat()
			for wp in [Vector3(-2.8, 1.6, 3.51), Vector3(2.6, 1.6, 3.51), Vector3(-2.8, 4.1, 3.51), Vector3(0.2, 4.1, 3.51), Vector3(2.6, 4.1, 3.51)]:
				put(n, m.box(1.3, 1.1, 0.05), wp, wm, "window")
			if not data.get("door_done", false):
				data["door_done"] = true
				m.door_node = node(n, Vector3(-0.5, 0, 3.52))
				put(m.door_node, m.box(1.0, 2.1, 0.06), Vector3(0.5, 1.05, 0), Color(0.35, 0.2, 0.12), "caravan")
				door_light_at(n, Vector3(0.0, 2.5, 4.2))
				m.obj["door"] = n.transform * Vector3(0.0, 0, 4.4)
			put(n, m.box(0.5, 1.6, 0.5), Vector3(2.8, 7.4, -1.0), Color(0.5, 0.25, 0.2), "caravan")
			m.add_obstacle_node(n, Vector3.ZERO, 9.2 * sc, 7.2 * sc)
			m.set_obstacle_height(6.0 * sc)
		"gartenhaus":
			put(n, m.box(2.6, 2.2, 2.0), Vector3(0, 1.1, 0), Color(0.3, 0.42, 0.3), "caravan")
			put(n, m.box(3.0, 0.12, 2.4), Vector3(0, 2.25, 0), Color(0.2, 0.2, 0.2), "caravan")
			m.add_obstacle_node(n, Vector3.ZERO, 2.8 * sc, 2.2 * sc)
			m.set_obstacle_height(2.2 * sc)
		"garage":
			put(n, m.box(3.4, 2.6, 6.0), Vector3(0, 1.3, 0), Color(0.82, 0.8, 0.76), "caravan")
			put(n, m.box(3.6, 0.15, 6.3), Vector3(0, 2.65, 0), Color(0.3, 0.3, 0.32), "caravan")
			put(n, m.box(2.6, 2.1, 0.05), Vector3(0, 1.05, 3.01), Color(0.6, 0.62, 0.65), "caravan")
			m.add_obstacle_node(n, Vector3.ZERO, 3.4 * sc, 6.0 * sc)
			m.set_obstacle_height(2.6 * sc)
		"baum":
			tree(n, Vector3.ZERO, 1.0, 0)
			m.add_obstacle(p, 0.4)
		"tanne":
			tree(n, Vector3.ZERO, 1.0, 1)
			m.add_obstacle(p, 0.4)
		"busch":
			put(n, sph(0.9, 1.3), Vector3(0, 0.6, 0), _hm(), "tree")
			m.add_obstacle(p, 0.9 * sc)
			m.set_obstacle_height(1.3 * sc)
		"auto":                                                      # these build at the real place (their obstacles too)
			static_car(p, r, [Color(0.7, 0.1, 0.1), Color(0.15, 0.3, 0.6), Color(0.85, 0.85, 0.85), Color(0.1, 0.1, 0.1)][int(absf(p.x * 7 + p.z)) % 4])
		"velo":
			bike(p, r)
		"bank":
			bench(p, r)
		"tisch":
			put(n, m.box(1.2, 0.05, 0.8), Vector3(0, 0.74, 0), Color(0.8, 0.8, 0.78), "stone")
			for x in [-0.5, 0.5]:
				for z in [-0.3, 0.3]:
					put(n, cyl(0.015, 0.015, 0.7, 5), Vector3(x, 0.36, z), Color(0.6, 0.6, 0.62), "stone")
			for sx in [-1, 1]:
				put(n, m.box(0.45, 0.45, 0.45), Vector3(0.9 * sx, 0.23, 0), Color(0.6, 0.3, 0.1), "tent")
			m.add_obstacle(p, 1.0)
			m.set_obstacle_height(0.8)
			m.obj["pir"] = p
		"grill":
			for kk in range(3):
				var a_ := TAU * kk / 3.0
				put(n, cyl(0.015, 0.015, 0.75, 5), Vector3(cos(a_) * 0.2, 0.36, sin(a_) * 0.2), Color(0.2, 0.2, 0.2), "stone", Vector3(sin(a_) * 0.25, 0, -cos(a_) * 0.25))
			put(n, sph(0.3, 0.3), Vector3(0, 0.78, 0), Color(0.08, 0.08, 0.08), 45.0)
			put(n, sph(0.3, 0.3), Vector3(0, 0.82, 0), Color(0.1, 0.1, 0.1), 40.0, Vector3(PI, 0, 0))
			m.add_obstacle(p, 0.4)
		"trampolin":
			put(n, cyl(1.6, 1.6, 0.08, 24), Vector3(0, 0.8, 0), Color(0.1, 0.1, 0.12), "stone")
			for kk in range(6):
				var a2 := TAU * kk / 6.0
				put(n, cyl(0.03, 0.03, 0.8, 5), Vector3(cos(a2) * 1.55, 0.4, sin(a2) * 1.55), Color(0.3, 0.5, 0.3), "stone")
			m.add_obstacle(p, 1.7 * sc)
			m.set_obstacle_height(0.9)
		"beet":
			put(n, m.box(4.0, 0.12, 1.0), Vector3(0, 0.06, 0), Color(0.3, 0.2, 0.12), "stone")
			var fc := [Color(0.9, 0.2, 0.3), Color(0.95, 0.85, 0.2), Color(0.6, 0.3, 0.8), Color(1, 1, 1)]
			for i in range(10):
				put(n, sph(0.12), Vector3(-1.8 + i * 0.4, 0.3, rng.randf_range(-0.3, 0.3)), fc[i % fc.size()], "tree")
		"laterne":
			lamp_post(p)
		"sandkasten":
			put(n, m.box(2.0, 0.25, 2.0), Vector3(0, 0.12, 0), Color(0.55, 0.4, 0.25), "tree")
			put(n, m.box(1.8, 0.27, 1.8), Vector3(0, 0.13, 0), Color(0.9, 0.82, 0.6), "stone")
		"pool":
			put(n, cyl(1.5, 1.5, 0.45, 24), Vector3(0, 0.22, 0), Color(0.2, 0.55, 0.85), "stone")
			put(n, cyl(1.35, 1.35, 0.46, 24), Vector3(0, 0.24, 0), Color(0.45, 0.8, 0.95), 18.0)
			m.add_obstacle(p, 1.6 * sc)
	return n



# ---- 3D-3.82: four more scenes ------------------------------------------------------------------------------------------
func _fence(a: Vector3, b: Vector3, h := 1.3, col := Color(0.55, 0.42, 0.28)) -> void:
	"""a wooden (or site) fence from a to b: posts and two rails"""
	var d := b - a
	var n := maxi(1, int(Vector2(d.x, d.z).length() / 2.5))
	for i in range(n + 1):
		var p := a.lerp(b, float(i) / n)
		put(root, m.box(0.12, h, 0.12), Vector3(p.x, h / 2.0, p.z), col, "tree")
	var ang := atan2(-d.z, d.x)
	var c := (a + b) / 2.0
	for y in [h * 0.4, h * 0.85]:
		put(root, m.box(Vector2(d.x, d.z).length(), 0.08, 0.05), Vector3(c.x, y, c.z), col, "tree", Vector3(0, ang, 0))
	m.add_obstacle_box(c, Vector2(d.x, d.z).length(), 0.3, ang)
	m.set_obstacle_height(h)


func _bauernhof() -> void:
	"""a farm: house with the door, a big barn, hay bales, a tractor, a pasture with a fence"""
	road(-38.0)
	var h := hut(Vector3(-10, 0, -18), 0.2, Color(0.82, 0.78, 0.7))
	h.scale = Vector3(1.6, 1.4, 1.6)
	var barn := node(root, Vector3(9, 0, -22), -0.1)
	put(barn, m.box(12, 6, 8), Vector3(0, 3, 0), Color(0.55, 0.16, 0.12), "caravan")
	var roof := PrismMesh.new()
	roof.size = Vector3(13, 3, 9)
	put(barn, roof, Vector3(0, 7.5, 0), Color(0.3, 0.3, 0.32), "caravan")
	put(barn, m.box(4, 4.5, 0.1), Vector3(0, 2.25, 4.02), Color(0.4, 0.12, 0.08), "caravan")
	m.add_obstacle_node(barn, Vector3.ZERO, 12.2, 8.2)
	static_car(Vector3(4, 0, -12), 0.6, Color(0.1, 0.5, 0.15))
	for i in range(6):
		prop("haybale", Vector3(16 + (i % 3) * 1.6, 0, -10 - (i / 3) * 1.6), 0.0)
	_fence(Vector3(-30, 0, -4), Vector3(-30, 0, -32))
	_fence(Vector3(-30, 0, -4), Vector3(-18, 0, -4))
	bike(Vector3(-4, 0, -9), 0.4)
	m.obj["pir"] = Vector3(3, 0, -14)
	lamp_post(Vector3(0, 0, -15))
	meadow(500, 3.0, 45.0)
	for i in range(50):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(45, 120)), rng.randf_range(0.8, 1.5))


func _seeufer() -> void:
	"""a lake shore: water, a wooden jetty with a boat, reeds, a tent and benches"""
	var water := StandardMaterial3D.new()
	water.albedo_color = Color(0.12, 0.3, 0.42)
	water.metallic = 0.3
	water.roughness = 0.08
	put(root, m.box(160, 0.05, 70), Vector3(0, 0.02, -60), water, "road")
	for i in range(14):                                    # the jetty
		put(root, m.box(1.8, 0.08, 0.3), Vector3(4, 0.45, -26 - i * 0.35), Color(0.5, 0.36, 0.22), "tree")
	for z in [-26.0, -28.5, -30.5]:
		for x in [3.2, 4.8]:
			put(root, cyl(0.08, 0.08, 1.2, 6), Vector3(x, 0.1, z), Color(0.35, 0.25, 0.15), "tree")
	var boat := node(root, Vector3(6.2, 0.2, -29), 0.1)
	put(boat, m.box(1.2, 0.4, 3.4), Vector3(0, 0.1, 0), Color(0.85, 0.85, 0.82), "caravan")
	for i in range(80):                                    # reeds
		var x := rng.randf_range(-40, 40)
		if absf(x - 4.0) < 4.0:
			continue
		put(root, cyl(0.02, 0.03, rng.randf_range(1.0, 1.8), 4), Vector3(x, 0.6, rng.randf_range(-26.5, -24.5)), Color(0.45, 0.5, 0.25), "tree")
	var tent := node(root, Vector3(-6, 0, -12), 0.3)
	var tm := PrismMesh.new()
	tm.size = Vector3(2.6, 1.5, 2.2)
	put(tent, tm, Vector3(0, 0.75, 0), Color(0.15, 0.45, 0.25), "tent", Vector3(0, PI / 2, 0))
	m.add_obstacle_node(tent, Vector3.ZERO, 2.4, 2.8)
	bench(Vector3(1, 0, -20), PI)
	bench(Vector3(-12, 0, -20), PI)
	hut(Vector3(14, 0, -14), -0.4)
	bike(Vector3(-2, 0, -10), 0.2)
	m.obj["pir"] = Vector3(-6, 0, -9)
	lamp_post(Vector3(4, 0, -22))
	road(30.0)
	meadow(400, 3.0, 40.0, func(p: Vector3): return p.z < -24.0)
	for i in range(40):
		var p2: Vector3 = m.pos_of(rng.randf_range(-180, 180), rng.randf_range(40, 110))
		if p2.z > -24.0:
			tree(root, p2, rng.randf_range(0.8, 1.4))


func _baustelle() -> void:
	"""a building site at night: a site fence, a container (door), an excavator, pallets, pipes, a crane"""
	road(-36.0)
	_fence(Vector3(-22, 0, -4), Vector3(22, 0, -4), 2.0, Color(0.75, 0.75, 0.78))
	_fence(Vector3(-22, 0, -4), Vector3(-22, 0, -30), 2.0, Color(0.75, 0.75, 0.78))
	_fence(Vector3(22, 0, -4), Vector3(22, 0, -30), 2.0, Color(0.75, 0.75, 0.78))
	put(root, m.box(44, 0.03, 26), Vector3(0, 0.015, -17), Color(0.45, 0.38, 0.3), "road")
	var c := node(root, Vector3(-14, 0, -10), 0.0)          # the site container with the door
	put(c, m.box(6, 2.6, 2.4), Vector3(0, 1.3, 0), Color(0.15, 0.35, 0.65), "caravan")
	put(c, m.box(1.0, 0.6, 0.05), Vector3(-1.5, 1.6, 1.22), window_mat(), "window")
	m.door_node = node(c, Vector3(1.5, 0, 1.22))
	put(m.door_node, m.box(0.9, 2.0, 0.05), Vector3(0.45, 1.0, 0), Color(0.12, 0.28, 0.5), "caravan")
	door_light_at(c, Vector3(2.0, 2.2, 1.8))
	m.obj["door"] = c.transform * Vector3(2.0, 0, 2.6)
	m.add_obstacle_node(c, Vector3.ZERO, 6.1, 2.5)
	var ex := node(root, Vector3(6, 0, -16), 0.7)            # the excavator
	put(ex, m.box(3, 0.8, 4), Vector3(0, 0.4, 0), Color(0.15, 0.15, 0.15), "caravan")
	put(ex, m.box(2.6, 1.6, 2.6), Vector3(0, 1.6, 0), Color(0.95, 0.7, 0.1), "caravan")
	put(ex, m.box(0.4, 0.4, 4.5), Vector3(0.8, 2.6, 2.6), Color(0.95, 0.7, 0.1), "caravan", Vector3(-0.5, 0, 0))
	m.add_obstacle_node(ex, Vector3.ZERO, 3.2, 4.2)
	for i in range(5):
		put(root, cyl(0.35, 0.35, 5, 12), Vector3(-4 + i * 0.75, 0.35, -24), Color(0.6, 0.6, 0.62), "stone", Vector3(0, 0, PI / 2))
	m.add_obstacle_box(Vector3(-2.5, 0, -24), 5, 4, 0.0)
	put(root, m.box(1, 22, 1), Vector3(16, 11, -26), Color(0.95, 0.75, 0.1), "stone")      # the crane
	put(root, m.box(24, 0.8, 0.8), Vector3(10, 21.6, -26), Color(0.95, 0.75, 0.1), "stone")
	m.add_obstacle(Vector3(16, 0, -26), 0.8)
	var tools := node(root, Vector3(-6, 0, -8), 0.2)         # the tool box (the thing a thief wants)
	put(tools, m.box(1.2, 0.8, 0.7), Vector3(0, 0.4, 0), Color(0.75, 0.1, 0.1), "caravan")
	m.add_obstacle_node(tools, Vector3.ZERO, 1.3, 0.8)
	m.test_props["Werkzeugkiste"] = tools
	m.obj["bike"] = Vector3(-6, 0, -7.2)
	m.obj["pir"] = Vector3(0, 0, -6)
	for x in [-18.0, 0.0, 18.0]:
		lamp_post(Vector3(x, 0, -6))
	meadow(300, 30.0, 60.0)
	for i in range(30):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(50, 120)), rng.randf_range(0.8, 1.4))


func _stellplatz() -> void:
	"""a camper van site: pitches with hedges between, power posts, a sanitary building, vans and a caravan"""
	road(-40.0, 6.0)
	put(root, m.box(50, 0.03, 4), Vector3(0, 0.015, -30), Color(0.4, 0.38, 0.35), "road")
	for i in range(5):
		var x := -20.0 + i * 10.0
		prop("hedge", Vector3(x - 5, 0, -22), PI / 2)
		var post := node(root, Vector3(x - 3.8, 0, -27))
		put(post, m.box(0.3, 1.0, 0.3), Vector3(0, 0.5, 0), Color(0.2, 0.45, 0.25), "caravan")
		put(post, m.box(0.25, 0.1, 0.05), Vector3(0, 0.85, 0.16), glow_mat(Color(0.3, 1.0, 0.4)), 30.0)
		m.add_obstacle(Vector3(x - 3.8, 0, -27), 0.25)
		if i == 2:
			caravan(Vector3(x, 0, -21), PI / 2)
		elif i != 3:
			static_car(Vector3(x, 0, -21), PI / 2, [Color(0.9, 0.9, 0.9), Color(0.75, 0.75, 0.7), Color(0.2, 0.3, 0.5)][i % 3])
	var sb := hut(Vector3(-24, 0, -8), 0.0, Color(0.85, 0.85, 0.82))
	sb.scale = Vector3(1.8, 1.2, 1.4)
	bike(Vector3(3, 0, -14), 0.5)
	bench(Vector3(8, 0, -12), 0.0)
	m.obj["pir"] = Vector3(10, 0, -18)
	for x in [-15.0, 5.0, 25.0]:
		lamp_post(Vector3(x, 0, -28))
	meadow(500, 3.0, 45.0, func(p: Vector3): return p.z < -26.0 and p.z > -34.0)
	for i in range(45):
		tree(root, m.pos_of(rng.randf_range(-180, 180), rng.randf_range(45, 120)), rng.randf_range(0.8, 1.4))


# ---- 3D-3.82: «Meine Vorlage» - a 3D file (.glb / .gltf) the operator loaded (templates.gd) ---------------------------------
func _vorlage() -> void:
	road(-60.0)
	m.obj["pir"] = Vector3(0, 0, -8)
	m.obj["bike"] = Vector3(4, 0, -9)
	var h := node(root, Vector3(0, 0, -55))                  # every scene needs a door (sensor): a small one, far away
	m.door_node = node(h, Vector3(0, 0, 0))
	put(m.door_node, m.box(1.0, 2.1, 0.06), Vector3(0.5, 1.05, 0), Color(0.35, 0.2, 0.12), "caravan")
	door_light_at(h, Vector3(0.0, 2.5, 0.6))
	m.obj["door"] = Vector3(0, 0, -54)
	meadow(300, 30.0, 60.0)
	if m.templates != null:
		m.templates.place_into(root)


# ---- 3D-3.96: the bedroom - for the wake-up alarm of MoveEye 2.98.9 (sleeping place, gestures) -------------------------------
func _schlafzimmer() -> void:
	"""a room 6.5 × 6.5 m round the head: bed on the right front (the sleeper of sleeper.gd), door in front on the left (where
	the camera looks at night), window on the left, wardrobe, night table with a lamp"""
	var wall := Color(0.82, 0.8, 0.74)
	var x0 := -3.0
	var x1 := 3.5
	var z0 := -5.0
	var z1 := 1.5
	var H := 2.6
	put(root, m.box(x1 - x0, 0.04, z1 - z0), Vector3((x0 + x1) / 2, 0.02, (z0 + z1) / 2), Color(0.55, 0.4, 0.25), "stone")        # wooden floor
	put(root, m.box(x1 - x0, 0.06, z1 - z0), Vector3((x0 + x1) / 2, H, (z0 + z1) / 2), Color(0.9, 0.9, 0.88), "stone")          # ceiling
	put(root, m.box(x1 - x0, H, 0.1), Vector3((x0 + x1) / 2, H / 2, z1), wall, "stone")                                       # back
	put(root, m.box(0.1, H, z1 - z0), Vector3(x1, H / 2, (z0 + z1) / 2), wall, "stone")                                       # right
	# front wall with the door (x -2.0 .. -1.0)
	put(root, m.box(-2.0 - x0, H, 0.1), Vector3((x0 - 2.0) / 2, H / 2, z0), wall, "stone")
	put(root, m.box(x1 + 1.0, H, 0.1), Vector3((x1 - 1.0) / 2, H / 2, z0), wall, "stone")
	put(root, m.box(1.0, H - 2.1, 0.1), Vector3(-1.5, 2.1 + (H - 2.1) / 2, z0), wall, "stone")
	m.door_node = node(root, Vector3(-2.0, 0, z0 + 0.05))
	put(m.door_node, m.box(1.0, 2.1, 0.05), Vector3(0.5, 1.05, 0), Color(0.6, 0.45, 0.3), "caravan")
	put(m.door_node, sph(0.04), Vector3(0.88, 1.0, 0.05), Color(0.8, 0.75, 0.5), "stone")
	door_light_at(root, Vector3(-1.5, 2.3, z0 + 0.4))
	m.obj["door"] = Vector3(-1.5, 0, z0 + 0.6)
	# left wall with a window
	put(root, m.box(0.1, H, 2.0), Vector3(x0, H / 2, z0 + 1.0), wall, "stone")
	put(root, m.box(0.1, H, 3.0), Vector3(x0, H / 2, z1 - 1.5), wall, "stone")
	put(root, m.box(0.1, 0.9, 1.5), Vector3(x0, 0.45, -2.25), wall, "stone")
	put(root, m.box(0.1, 0.6, 1.5), Vector3(x0, H - 0.3, -2.25), wall, "stone")
	put(root, m.box(0.04, 1.1, 1.5), Vector3(x0, 1.45, -2.25), window_mat(), "glass")
	# bed (head end at the right wall), night table, lamp, wardrobe, rug
	var bed := node(root, Vector3(2.35, 0, -3.2))
	m.test_props["Bett"] = bed
	put(bed, m.box(2.1, 0.35, 1.5), Vector3(0, 0.25, 0), Color(0.45, 0.32, 0.2), "stone")                                    # frame
	put(bed, m.box(2.0, 0.18, 1.4), Vector3(0, 0.5, 0), Color(0.92, 0.92, 0.9), "tent")                                      # mattress
	put(bed, m.box(0.1, 0.9, 1.5), Vector3(1.05, 0.45, 0), Color(0.4, 0.28, 0.18), "stone")                                  # head board
	put(bed, m.box(0.45, 0.12, 0.6), Vector3(0.72, 0.66, 0.3), Color(0.95, 0.95, 0.97), "tent")                              # pillows
	put(bed, m.box(0.45, 0.12, 0.6), Vector3(0.72, 0.66, -0.35), Color(0.95, 0.95, 0.97), "tent")
	m.add_obstacle(Vector3(2.35, 0, -3.2), 1.2)
	put(root, m.box(0.45, 0.5, 0.4), Vector3(3.1, 0.25, -1.9), Color(0.5, 0.36, 0.22), "stone")                             # night table
	put(root, cyl(0.12, 0.08, 0.25), Vector3(3.1, 0.65, -1.9), Color(0.95, 0.85, 0.6), 30.0)
	put(root, m.box(0.6, 2.1, 1.8), Vector3(x0 + 0.35, 1.05, z1 - 1.3), Color(0.62, 0.5, 0.36), "stone")                    # wardrobe
	m.add_obstacle(Vector3(x0 + 0.35, 0, z1 - 1.3), 1.0)
	put(root, m.box(1.8, 0.01, 1.2), Vector3(0.6, 0.045, -2.6), Color(0.35, 0.18, 0.2), "stone")                             # rug
	m.obj["pir"] = Vector3(-1.5, 0, -4.0)
	m.obj["bike"] = Vector3(-2.4, 0, 0.6)
	data["bed"] = bed
	data["indoor"] = true
	if m.get("sleeper") != null:
		m.sleeper.place(bed)
