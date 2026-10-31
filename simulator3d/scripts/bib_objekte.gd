extends RefCounted
## 3D-4.x «Szenen-Bibliothek» (Daniel, 31.10.2026, Variante A): gemeinsame Bausteine für grosse Szenen (Ferienpark am See,
## später vier kompakte Szenen). Rund 80 Dinge mit Parametern, wie die anderen aus Grundformen gebaut, in echter Grösse, mit
## Hindernis (Besucher gehen herum), Wärme für das Wärmebild (Motoren, Grill, Feuer, Tiere, Lampen) und Sichtweite.
##
## Gebaut wird NICHT jedes Teil als eigener Knoten (das wären in 500 × 500 m viele tausend Zeichenaufrufe), sondern:
##   - alle Teile einer Zelle (48 m) mit gleicher Oberfläche (Wärme-Schlüssel) und gleicher Sichtweite in EIN Netz
##     (Farbe als Eckfarbe) - plus sein Zwilling für das Wärmebild (Ebene 2), gleiches Netz
##   - viele gleiche kleine Dinge (Bäume, Zäune, Hecken, Lampen, Absperrgitter, Liegestühle …) als MultiMesh (many())
##   - Tiere als eigene Knoten (der Kopf bewegt sich ein wenig - wie echte Tiere beim Fressen)
## Sichtweite (Godot visibility_range): «big» immer (Lite 320 m), «mid» 170 m (Lite 110 m), «small» 75 m (Lite 45 m).
##
## Teil (wie objects.gd): [Form, a, b, c, x, y, z, Farbe, Drehung x, y, z (Grad), Wärme]
##   b = Kiste a × b × c · c = Zylinder (Radius oben a, Höhe b, Radius unten c; 0 = wie oben) · s = Kugel (Radius a, Höhe b)
##   p = Prisma / Dach (a × b × c, First entlang z) · k = Kegel (Radius a, Höhe b) · t = Ring (innen a, aussen b)
##   Farbe: "rrggbb" oder Color; «*…» leuchtet nachts hell (Lampe), «%…» leuchtet nachts schwach (Fenster)
##   Wärme (optional): Schlüssel wie bei main.add_mesh ("caravan", "tent", "stone", "tree", "road", "window", "pond") oder °C
## Ein Ding (make(kind, q)): {"p": Teile, "t": Wärme-Standard, "lod": big|mid|small, "ob": Hindernisse, "lights": Lampen,
##   "fx": Rauch / Fahne, "door": Tür (für den Türsensor), "node": true = eigener Knoten (Tiere)}
## Lite (Raspberry Pi, Compatibility-Renderer): lite() - weniger Ecken, kleine Teile weg, kürzere Sichtweite, weniger Schatten.
## Quelle: Quality.lite() (quality.gd) oder Grafik «simple».

const T = preload("res://scripts/i18n.gd")

var m                              # main.gd
var s                              # scenes.gd (glow_mat, cloth, smoke, tree …)
var root: Node3D                   # where the nets go (e.g. the park node, turned and moved)
var to_world := Transform3D()      # root -> world (obstacles, lights and doors are in world coordinates)
var cell := 48.0
var stats := {"objects": 0, "parts": 0, "nets": 0, "multimesh": 0, "instances": 0, "animals": 0}
var lamps: Array = []              # [local position, colour] - the scene makes real lights for the nearest ones
var fx: Array = []                 # [kind, local position, extra]
var doors: Array = []              # [local position, rot_y] of things with a door

var _st := {}                      # bucket key -> {"st": SurfaceTool, "tk", "lod", "glow": Color or null, "n": parts}
var _prim := {}                    # primitive + colour -> ArrayMesh with vertex colours
var _vmats := {}                   # surface kind -> StandardMaterial3D (vertex colours)
var _gmats := {}                   # glow colour -> material (lamp_mats)
var _lite := false
var _low := false                  # the kind being built wants few corners (many(): trees, reeds)


static func lite() -> bool:
	"""the central question «Lite?» (3D-4.28: quality.gd, set by main.lite_update)"""
	return preload("res://scripts/quality.gd").lite()


func _init(main_, scenes_, root_: Node3D, xf := Transform3D()) -> void:
	m = main_
	s = scenes_
	root = root_
	to_world = xf
	_lite = lite() or (m != null and str(m.quality) == "simple")


func is_lite() -> bool:
	return _lite


# =======================================================================================================================
# the catalogue: kind -> [German name, group, function]
# =======================================================================================================================
const KINDS := {
	# Gebäude
	"bungalow": ["Bungalow", "Gebäude"], "chalet": ["Chalet", "Gebäude"], "reception": ["Rezeption", "Gebäude"],
	"sanitary": ["Sanitärgebäude", "Gebäude"], "shop": ["Laden", "Gebäude"], "restaurant": ["Restaurant", "Gebäude"],
	"kiosk": ["Kiosk", "Gebäude"], "house": ["Wohnhaus", "Gebäude"], "bakery": ["Bäckerei", "Gebäude"], "church": ["Kirche", "Gebäude"],
	"barn": ["Scheune", "Gebäude"], "stable": ["Stall", "Gebäude"], "boathouse": ["Bootshaus", "Gebäude"], "latrine": ["Plumpsklo", "Gebäude"],
	"shed": ["Geräteschuppen", "Gebäude"], "cable_station": ["Seilbahn-Station", "Gebäude"], "stage": ["Bühne mit Traverse", "Gebäude"],
	# Camping
	"tent": ["Zelt", "Camping"], "yurt": ["Jurte", "Camping"], "sarasani": ["Sarasani (grosses Pfadi-Zelt)", "Camping"],
	"caravan": ["Wohnwagen", "Camping"], "motorhome": ["Wohnmobil", "Camping"], "campfire": ["Feuerstelle", "Camping"],
	"picnic_table": ["Picknick-Tisch", "Camping"], "bbq": ["Grill", "Camping"], "power_post": ["Stromsäule", "Camping"],
	"water_tap": ["Wasserstelle", "Camping"], "pitch_post": ["Platz-Nummer", "Camping"], "flagpole": ["Fahnenmast", "Camping"],
	"totem": ["Totempfahl", "Camping"],
	# Fahrzeuge & Wasser
	"car": ["Auto", "Fahrzeuge"], "tractor": ["Traktor", "Fahrzeuge"], "food_truck": ["Imbisswagen", "Fahrzeuge"],
	"rowboat": ["Ruderboot", "Wasser"], "pedalboat": ["Pedalo", "Wasser"], "sailboat": ["Segelboot", "Wasser"], "buoy": ["Boje", "Wasser"],
	"jetty": ["Steg", "Wasser"], "pool": ["Schwimmbecken", "Wasser"], "fountain": ["Brunnen", "Wasser"], "reeds": ["Schilf", "Wasser"],
	"lifeguard": ["Bademeister-Stuhl", "Wasser"], "lounger": ["Liegestuhl", "Wasser"], "parasol": ["Sonnenschirm", "Wasser"],
	"shower": ["Strand-Dusche", "Wasser"],
	# Spielen
	"swing": ["Schaukel", "Spielen"], "slide": ["Rutschbahn", "Spielen"], "sandpit": ["Sandkasten", "Spielen"],
	"climbing": ["Klettergerüst", "Spielen"], "seesaw": ["Wippe", "Spielen"], "minigolf": ["Minigolf-Bahn", "Spielen"],
	# Wege & Grenzen
	"fence": ["Zaun", "Wege"], "hedge": ["Hecke", "Wege"], "wall": ["Mauer / Stützmauer", "Wege"], "stairs": ["Treppe", "Wege"],
	"lamp": ["Laterne", "Wege"], "bench": ["Bank", "Wege"], "bin": ["Abfalleimer", "Wege"], "signpost": ["Wegweiser", "Wege"],
	"info_board": ["Infotafel", "Wege"], "barrier": ["Schranke", "Wege"], "crowd_barrier": ["Absperrgitter", "Wege"],
	"parking_lines": ["Parkfelder", "Wege"], "bike_rack": ["Veloständer", "Wege"], "footbridge": ["Fussgängerbrücke", "Wege"],
	"rope_bridge": ["Hängebrücke", "Wege"], "viewpoint": ["Aussichtsplattform", "Wege"], "hochsitz": ["Hochsitz", "Wege"],
	"rock": ["Fels", "Wege"],
	# Bauernhof
	"haybale": ["Heuballen", "Bauernhof"], "field": ["Feld", "Bauernhof"], "coop": ["Hühnerstall", "Bauernhof"],
	"tree": ["Laubbaum", "Bauernhof"], "conifer": ["Tanne", "Bauernhof"], "orchard_tree": ["Obstbaum", "Bauernhof"],
	# Erlebniswelt (Daniel 31.10.2026, /tmp spec Vignetten 1–19): die festen Dinge; die Abläufe baut ein späteres Paket
	"tree_house": ["Baumhütte mit Strickleiter", "Erlebnis"], "cave": ["Kleine Höhle", "Erlebnis"], "mouse_holes": ["Mauer mit Mauslöchern", "Erlebnis"],
	"gnome": ["Gartenzwerg", "Erlebnis"], "bottle_post": ["Flaschenpost", "Erlebnis"], "chest": ["Schatzkiste", "Erlebnis"],
	"fishing_rod": ["Angelrute mit Eimer", "Erlebnis"], "boot": ["Gummistiefel", "Erlebnis"], "old_caravan": ["Verlassener Wohnwagen", "Erlebnis"],
	"sunken_boat": ["Versunkenes Boot", "Erlebnis"], "knothole_tree": ["Baum mit Astloch", "Erlebnis"],
	"cow": ["Kuh", "Tiere"], "goat": ["Ziege", "Tiere"], "chicken": ["Huhn", "Tiere"], "sheep": ["Schaf", "Tiere"],
}


static func names() -> Array:
	"""[[kind, German name, group]] - for lists and tests"""
	var out := []
	for k in KINDS:
		out.append([k, KINDS[k][0], KINDS[k][1]])
	return out


func make(kind: String, q := {}) -> Dictionary:
	"""the parts of a thing (not yet built)"""
	if not KINDS.has(kind) or not has_method("_k_" + kind):
		return {}
	var d: Dictionary = call("_k_" + kind, q)
	if not d.has("t"):
		d["t"] = "caravan"
	if not d.has("lod"):
		d["lod"] = "mid"
	return d


# =======================================================================================================================
# building
# =======================================================================================================================
func add(kind: String, p: Vector3, rot := 0.0, q := {}) -> Dictionary:
	"""one thing at p (local to root, y = ground) turned by rot; returns its description (door, lights …)"""
	var d := make(kind, q)
	if d.is_empty():
		return d
	var sc := float(q.get("scale", 1.0))
	var xf := Transform3D(Basis(Vector3.UP, rot).scaled(Vector3.ONE * sc), p)
	stats["objects"] += 1
	if d.get("node", false):
		_node_thing(d, xf, kind)
	else:
		var ck := _cell_key(p)
		for part in d["p"]:
			_part(part, xf, d["t"], str(d["lod"]), ck)
	_extras(d, xf, rot)
	return d


func parts_of(kind: String, xf: Transform3D, q := {}) -> void:
	"""the parts of a thing into the nets, without obstacles (e.g. a car on a ferry, a boat in the boat house)"""
	var d := make(kind, q)
	if d.is_empty():
		return
	for part in d["p"]:
		_part(part, xf, d["t"], str(d["lod"]), _cell_key(xf.origin))


func many(kind: String, list: Array, q := {}) -> void:
	"""many equal things as MultiMesh (one draw call per surface and group of 128 m): list = [[position, rot_y], …] or
	[[position, rot_y, scale]]"""
	if list.is_empty():
		return
	var d := make(kind, q)
	if d.is_empty():
		return
	# the parts once, at the origin: one mesh per surface (+ one per glow colour)
	_low = bool(d.get("low", false))
	var local := {}
	for part in d["p"]:
		var tk = part[11] if part.size() > 11 and part[11] != null else d["t"]
		var cs = part[7]
		var glow = _glow_of(cs)
		if _skip(part):
			continue
		var key := ("g" + (glow as Color).to_html()) if glow != null else _tk_name(tk)
		if not local.has(key):
			var st0 := SurfaceTool.new()
			st0.begin(Mesh.PRIMITIVE_TRIANGLES)
			local[key] = {"st": st0, "tk": tk, "glow": glow}
		_append(local[key]["st"], part, Transform3D.IDENTITY)
	_low = false
	var meshes := {}
	for key in local:
		meshes[key] = local[key]["st"].commit()
	# the instances in groups of 128 m (so the far ones can vanish)
	var groups := {}
	for e in list:
		var p: Vector3 = e[0]
		var gk := Vector2i(int(floor(p.x / 128.0)), int(floor(p.z / 128.0)))
		if not groups.has(gk):
			groups[gk] = []
		groups[gk].append(e)
	var lod := str(d["lod"])
	for gk in groups:
		var items: Array = groups[gk]
		for key in meshes:
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = meshes[key]
			mm.instance_count = items.size()
			for i in range(items.size()):
				var e: Array = items[i]
				var sc := float(e[2]) if e.size() > 2 else float(q.get("scale", 1.0))
				mm.set_instance_transform(i, Transform3D(Basis(Vector3.UP, float(e[1])).scaled(Vector3.ONE * sc), e[0]))
			var info: Dictionary = local[key]
			var vis := MultiMeshInstance3D.new()
			vis.multimesh = mm
			vis.layers = 1
			vis.material_override = _gmat(info["glow"]) if info["glow"] != null else _vmat(_kind_of(info["tk"]))
			_lod(vis, lod)
			var gc := to_world * Vector3((gk.x + 0.5) * 128.0, 0, (gk.y + 0.5) * 128.0)
			if Vector2(gc.x, gc.z).length() > 150.0:
				vis.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # far groups: no shadow pass
			root.add_child(vis)
			var th := MultiMeshInstance3D.new()
			th.multimesh = mm
			th.layers = 2
			th.material_override = _tmat(info["tk"], info["glow"])
			th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_lod(th, lod, false)
			root.add_child(th)
			stats["multimesh"] += 1
	for e in list:
		var sc2 := float(e[2]) if e.size() > 2 else float(q.get("scale", 1.0))
		var xf := Transform3D(Basis(Vector3.UP, float(e[1])).scaled(Vector3.ONE * sc2), e[0])
		_extras(d, xf, float(e[1]))
		stats["instances"] += 1


func line(kind: String, a: Vector3, b: Vector3, seg: float, q := {}, gaps := []) -> int:
	"""a row of equal pieces from a to b (fence, hedge, wall, barriers): MultiMesh; gaps = [[centre, half width], …] along
	the line (metres from a) stay free"""
	var d := b - a
	var L := Vector2(d.x, d.z).length()
	if L < 0.1:
		return 0
	var n := maxi(1, int(round(L / seg)))
	var rot := atan2(d.x, d.z) - PI / 2.0              # the piece is built along x
	var list := []
	var q2: Dictionary = q.duplicate()
	q2["len"] = L / n
	for i in range(n):
		var t := (i + 0.5) / n
		var along := t * L
		var skip := false
		for g in gaps:
			if absf(along - float(g[0])) < float(g[1]):
				skip = true
		if skip:
			continue
		var p := a.lerp(b, t)
		if q.has("ground"):
			p.y = (q["ground"] as Callable).call(p.x, p.z)
		list.append([p, rot])
	many(kind, list, q2)
	return list.size()


func finish() -> void:
	"""commit the nets: every bucket one visible and one thermal mesh instance"""
	for key in _st:
		var b: Dictionary = _st[key]
		var mesh: ArrayMesh = b["st"].commit()
		var vis := MeshInstance3D.new()
		vis.mesh = mesh
		vis.layers = 1
		vis.material_override = _gmat(b["glow"]) if b["glow"] != null else _vmat(_kind_of(b["tk"]))
		_lod(vis, str(b["lod"]))
		root.add_child(vis)
		var th := MeshInstance3D.new()
		th.mesh = mesh
		th.layers = 2
		th.material_override = _tmat(b["tk"], b["glow"])
		th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_lod(th, str(b["lod"]), false)
		root.add_child(th)
		stats["nets"] += 1
	_st.clear()


func _lod(gi: GeometryInstance3D, lod: String, shadow := true) -> void:
	var far := {"big": 320.0 if _lite else 0.0, "mid": 110.0 if _lite else 170.0, "small": 45.0 if _lite else 75.0}
	var end: float = far.get(lod, 0.0)
	if end > 0.0:
		gi.visibility_range_end = end
		gi.visibility_range_end_margin = 8.0
		gi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	if shadow:
		var cast: bool = lod == "big" or (lod == "mid" and not _lite)
		gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _cell_key(p: Vector3) -> String:
	return "%d,%d" % [int(floor(p.x / cell)), int(floor(p.z / cell))]


func _tk_name(tk) -> String:
	if typeof(tk) == TYPE_STRING:
		return tk
	return "w%.1f" % snappedf(float(tk), 0.5)


func _kind_of(tk) -> String:
	"""the kind of surface for the colours (colors.gd KIND) from the thermal key"""
	if typeof(tk) != TYPE_STRING:
		return "metal"
	match str(tk):
		"caravan", "tent", "stone", "window", "glass", "metal", "car":
			return str(tk)
		"tree":
			return "wood"
		"road", "pond":
			return "stone"
	return "stone"


func _glow_of(c):
	"""null, or the glow colour of a part («*» lamp, «~» window)"""
	if typeof(c) == TYPE_STRING:
		var cs := str(c)
		if cs.begins_with("*"):
			return cc(cs)
		if cs.begins_with("%"):
			return cc(cs) * Color(0.42, 0.36, 0.26)       # a lit window: warm and much dimmer than a lamp
	return null


func _color(c) -> Color:
	var col: Color
	if typeof(c) == TYPE_COLOR:
		col = c
	else:
		col = cc(c)
	if m != null and m.colors != null and m.colors.on:
		col = m.colors.natural(col)
	return col


func _skip(part: Array) -> bool:
	"""Lite: tiny parts (ropes, handles, spokes) are left out"""
	if not _lite:
		return false
	var sh := str(part[0])
	var a := float(part[1])
	var b := float(part[2])
	var c := float(part[3])
	match sh:
		"b":
			return maxf(a, maxf(b, c)) < 0.12 or (minf(a, minf(b, c)) < 0.025 and maxf(a, maxf(b, c)) < 1.2)
		"c", "k":
			return a < 0.025 and b < 1.0
		"s":
			return a < 0.05
	return false


func _part(part: Array, xf: Transform3D, tk_def, lod: String, ck: String) -> void:
	if _skip(part):
		return
	var tk = part[11] if part.size() > 11 and part[11] != null else tk_def
	var glow = _glow_of(part[7])
	var key := ck + "|" + lod + "|" + (("g" + (glow as Color).to_html()) if glow != null else _tk_name(tk))
	if not _st.has(key):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_st[key] = {"st": st, "tk": tk, "lod": lod, "glow": glow}
	_append(_st[key]["st"], part, xf)
	stats["parts"] += 1


func _append(st: SurfaceTool, part: Array, xf: Transform3D) -> void:
	var sh := str(part[0])
	var a := float(part[1])
	var b := float(part[2])
	var c := float(part[3])
	var col := _color(part[7])
	var rot := Basis.from_euler(Vector3(deg_to_rad(part[8]), deg_to_rad(part[9]), deg_to_rad(part[10])))
	var local := Transform3D(rot, Vector3(part[4], part[5], part[6]))
	var key := ""
	if sh == "b":
		local.basis = local.basis * Basis.from_scale(Vector3(a, b, c))        # one unit box for all sizes (normals stay right)
		key = "b"
	elif sh == "p":
		local.basis = local.basis * Basis.from_scale(Vector3(a, b, c))
		key = "p"
	else:
		key = "%s|%.3f|%.3f|%.3f" % [sh, a, b, c]
	st.append_from(_prim_mesh(key, sh, a, b, c, col), 0, xf * local)


func _prim_mesh(key: String, sh: String, a: float, b: float, c: float, col: Color) -> ArrayMesh:
	var k2 := key + "|" + col.to_html() + ("|l" if _low else "")
	if _prim.has(k2):
		return _prim[k2]
	var seg := 6 if (_lite or _low) else 10
	var pm: PrimitiveMesh
	match sh:
		"b":
			pm = BoxMesh.new()
		"p":
			pm = PrismMesh.new()
		"c":
			var cm := CylinderMesh.new()
			cm.top_radius = a
			cm.bottom_radius = c if c > 0.0 else a
			cm.height = b
			cm.radial_segments = seg
			cm.rings = 1
			pm = cm
		"k":
			var km := CylinderMesh.new()
			km.top_radius = 0.0
			km.bottom_radius = a
			km.height = b
			km.radial_segments = seg
			km.rings = 1
			pm = km
		"s":
			var sm := SphereMesh.new()
			sm.radius = a
			sm.height = b if b > 0.0 else 2.0 * a
			sm.radial_segments = seg
			sm.rings = 3 if (_lite or _low) else 5
			pm = sm
		"t":
			var tm := TorusMesh.new()
			tm.inner_radius = a
			tm.outer_radius = b
			tm.rings = 10 if _lite else 16
			tm.ring_segments = 5 if _lite else 8
			pm = tm
		_:
			pm = BoxMesh.new()
	var arr: Array = pm.get_mesh_arrays()
	var n: int = (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	var cols := PackedColorArray()
	cols.resize(n)
	cols.fill(col)
	arr[Mesh.ARRAY_COLOR] = cols
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	_prim[k2] = am
	return am


func _vmat(kind: String) -> StandardMaterial3D:
	if _vmats.has(kind):
		return _vmats[kind]
	var mt := StandardMaterial3D.new()
	mt.vertex_color_use_as_albedo = true
	mt.vertex_color_is_srgb = true
	mt.roughness = 0.85
	if m != null and m.colors != null and m.colors.on:
		var p: Array = m.colors.KIND.get(kind, [0.85, 0.0, 0.4])
		mt.roughness = float(p[0])
		mt.metallic = float(p[1])
		mt.metallic_specular = float(p[2])
		m.colors.base_alb[mt] = [mt.albedo_color, mt.roughness]      # wet in the rain like the other things
	if m != null:
		m._mat_detail(mt, str(m.quality) != "simple" and not _lite)
	_vmats[kind] = mt
	return mt


func _gmat(c: Color) -> StandardMaterial3D:
	var k := c.to_html()
	if not _gmats.has(k):
		_gmats[k] = s.glow_mat(c) if s != null else StandardMaterial3D.new()
	return _gmats[k]


func _tmat(tk, glow) -> Material:
	if glow != null:
		return m.tmat_fixed(40.0)                                     # a lamp head / lit window: warm
	return m.tmat(tk) if typeof(tk) == TYPE_STRING else m.tmat_fixed(float(tk))


func _extras(d: Dictionary, xf: Transform3D, rot: float) -> void:
	"""obstacles, lights, smoke, flags, labels and doors of one placed thing"""
	var wxf := to_world * xf
	var wrot := rot + to_world.basis.get_euler().y
	var sc := xf.basis.get_scale().x
	for o in d.get("ob", []):
		# ["box", cx, cz, sx, sz, height, people_only] · ["circ", cx, cz, r, height, people_only]
		var c: Vector3 = wxf * Vector3(float(o[1]), 0, float(o[2]))
		if str(o[0]) == "box":
			m.add_obstacle_box(c, float(o[3]) * sc, float(o[4]) * sc, wrot, o.size() > 6 and bool(o[6]))
			m.set_obstacle_height(float(o[5]) * sc)
		else:
			m.add_obstacle(c, float(o[3]) * sc, o.size() > 5 and bool(o[5]))
			m.set_obstacle_height(float(o[4]) * sc)
	for l in d.get("lights", []):
		lamps.append([xf * Vector3(float(l[0]), float(l[1]), float(l[2])), cc(l[3]) if l.size() > 3 else Color(1.0, 0.82, 0.55)])
	for f in d.get("fx", []):
		fx.append([str(f[0]), xf * Vector3(float(f[1]), float(f[2]), float(f[3])), f[4] if f.size() > 4 else null, rot])
	if d.has("door"):
		var dr: Array = d["door"]
		doors.append([xf * Vector3(float(dr[0]), float(dr[1]), float(dr[2])), rot, dr])
	for lb in d.get("labels", []):
		var l3 := Label3D.new()
		l3.text = T.t(str(lb[0]))
		l3.position = xf * Vector3(float(lb[1]), float(lb[2]), float(lb[3]))
		l3.rotation.y = rot + float(lb[5]) if lb.size() > 5 else rot
		l3.font_size = int(lb[4]) if lb.size() > 4 else 64
		l3.pixel_size = 0.01
		l3.modulate = Color(0.12, 0.12, 0.12) if lb.size() <= 6 else cc(lb[6])
		l3.outline_size = 0
		l3.layers = 1
		l3.visibility_range_end = 60.0 if _lite else 110.0
		root.add_child(l3)


func _node_thing(d: Dictionary, xf: Transform3D, kind: String) -> Node3D:
	"""a thing as its own node (animals: the head moves) - every part with its thermal twin like main.add_mesh"""
	var n := Node3D.new()
	n.name = "bib_" + kind
	n.transform = xf
	root.add_child(n)
	var pivs := {}
	for part in d["p"]:
		if _skip(part):
			continue
		var parent: Node3D = n
		var off := Vector3.ZERO
		if part.size() > 12 and part[12] != null:
			var role := str(part[12])
			if not pivs.has(role):
				var pv := Node3D.new()
				var pp: Array = (d.get("piv", {}) as Dictionary).get(role, [0, 0, 0])
				pv.position = Vector3(pp[0], pp[1], pp[2])
				n.add_child(pv)
				pivs[role] = pv
			parent = pivs[role]
			off = (pivs[role] as Node3D).position
		var tk = part[11] if part.size() > 11 and part[11] != null else d["t"]
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var p2: Array = part.duplicate()
		p2[4] = float(part[4]) - off.x
		p2[5] = float(part[5]) - off.y
		p2[6] = float(part[6]) - off.z
		_append(st, p2, Transform3D.IDENTITY)
		var mesh := st.commit()
		var vis := MeshInstance3D.new()
		vis.mesh = mesh
		vis.layers = 1
		vis.material_override = _vmat("tent")
		vis.visibility_range_end = 60.0 if _lite else 120.0
		parent.add_child(vis)
		var th := MeshInstance3D.new()
		th.mesh = mesh
		th.layers = 2
		th.material_override = _tmat(tk, null)
		th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		th.visibility_range_end = vis.visibility_range_end
		parent.add_child(th)
	stats["animals"] += 1
	if pivs.has("head") and m != null:                         # eats: the head goes down and up slowly, now and then
		var head: Node3D = pivs["head"]
		var ph := randf() * 20.0
		var sp := randf_range(0.7, 1.3)
		var amp: float = float(d.get("nod", 0.45))
		var wr: WeakRef = weakref(head)
		m.anims.append(func(_dt, t):
			var h = wr.get_ref()
			if h == null:
				return true
			var u: float = fmod(t * 0.13 * sp + ph, 1.0)
			h.rotation.z = -amp * smoothstep(0.0, 0.12, u) * (1.0 - smoothstep(0.55, 0.7, u)) + 0.04 * sin(t * 2.3 * sp + ph)
			return false)
	return n


# =======================================================================================================================
# small helpers to write parts
# =======================================================================================================================
static func B(sx: float, sy: float, sz: float, x: float, y: float, z: float, col, rx := 0.0, ry := 0.0, rz := 0.0, tk = null, role = null) -> Array:
	var a := ["b", sx, sy, sz, x, y, z, col, rx, ry, rz, tk]
	if role != null:
		a.append(role)
	return a


static func C(r: float, h: float, x: float, y: float, z: float, col, rb := 0.0, rx := 0.0, ry := 0.0, rz := 0.0, tk = null, role = null) -> Array:
	var a := ["c", r, h, rb, x, y, z, col, rx, ry, rz, tk]
	if role != null:
		a.append(role)
	return a


static func S(r: float, h: float, x: float, y: float, z: float, col, tk = null, role = null) -> Array:
	var a := ["s", r, h, 0, x, y, z, col, 0, 0, 0, tk]
	if role != null:
		a.append(role)
	return a


static func P(sx: float, sy: float, sz: float, x: float, y: float, z: float, col, rx := 0.0, ry := 0.0, rz := 0.0, tk = null) -> Array:
	return ["p", sx, sy, sz, x, y, z, col, rx, ry, rz, tk]


static func K(r: float, h: float, x: float, y: float, z: float, col, rx := 0.0, ry := 0.0, rz := 0.0, tk = null, role = null) -> Array:
	var a := ["k", r, h, 0, x, y, z, col, rx, ry, rz, tk]
	if role != null:
		a.append(role)
	return a


static func TO(ri: float, ro: float, x: float, y: float, z: float, col, rx := 0.0, ry := 0.0, rz := 0.0, tk = null) -> Array:
	return ["t", ri, ro, 0, x, y, z, col, rx, ry, rz, tk]


static func cc(c) -> Color:
	"""a colour from «rrggbb» or a Color"""
	if typeof(c) == TYPE_COLOR:
		return c
	return Color.html("#" + str(c).trim_prefix("*").trim_prefix("%").trim_prefix("#"))


static func ROD(a: Vector3, b: Vector3, r: float, col, tk = null) -> Array:
	"""a thin box from a to b (rope, rail, cable, leg)"""
	var d := b - a
	var L := d.length()
	var mid := (a + b) * 0.5
	var yaw := atan2(d.x, d.z)
	var pitch := atan2(Vector2(d.x, d.z).length(), d.y)        # from up
	# a box along y turned: first pitch around x, then yaw around y (Euler YXZ: y applied last)
	return ["b", r, L, r, mid.x, mid.y, mid.z, col, rad_to_deg(pitch), rad_to_deg(yaw), 0.0, tk]


func _window_row(out: Array, n: int, w: float, y: float, z: float, ww: float, wh: float, col := "%ffd9a0", side := false) -> void:
	"""n windows evenly on a facade of width w (front: z = facade; side: x = facade)"""
	for i in range(n):
		var x := -w / 2.0 + w * (i + 0.5) / n
		if side:
			out.append(B(0.06, wh, ww, z, y, x, col, 0, 0, 0, "window"))
			out.append(B(0.05, wh + 0.12, ww + 0.12, z - signf(z) * 0.01, y, x, "3a3a3a"))
		else:
			out.append(B(ww, wh, 0.06, x, y, z, col, 0, 0, 0, "window"))
			out.append(B(ww + 0.12, wh + 0.12, 0.05, x, y, z - signf(z) * 0.01, "3a3a3a"))


func _q(q: Dictionary, k: String, d):
	return q.get(k, d)


# =======================================================================================================================
# the kinds (local: origin on the ground in the middle, front / door = +z)
# =======================================================================================================================
func _k_bungalow(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 6.0))
	var dd := float(_q(q, "d", 8.0))
	var col = _q(q, "col", "b98a5a")
	var roof = _q(q, "roof", "5a3426")
	var h := 2.7
	var p := [B(w + 0.3, 0.35, dd + 0.3, 0, 0.17, 0, "8b8680", 0, 0, 0, "stone"),
			B(w, h, dd, 0, 0.35 + h / 2.0, 0, col),
			P(w + 0.9, 1.5, dd + 1.0, 0, 0.35 + h + 0.75, 0, roof),
			B(0.95, 2.0, 0.06, w * 0.22, 0.35 + 1.0, dd / 2.0 + 0.03, "6b4a32"),
			B(0.06, 0.06, 0.12, w * 0.22 - 0.35, 1.35, dd / 2.0 + 0.08, "c0c0c0"),
			B(0.9, 0.12, 0.6, w * 0.22, 0.06, dd / 2.0 + 0.45, "8b8680", 0, 0, 0, "stone")]
	_window_row(p, 1, w * 0.5, 1.75, dd / 2.0 + 0.03, 1.1, 0.95)
	p[p.size() - 2][4] = -w * 0.22
	p[p.size() - 1][4] = -w * 0.22
	_window_row(p, 2, dd * 0.7, 1.75, w / 2.0 + 0.03, 0.9, 0.8, "%ffd9a0", true)
	_window_row(p, 2, dd * 0.7, 1.75, -w / 2.0 - 0.03, 0.9, 0.8, "%ffd9a0", true)
	for i in range(6):                                      # wooden boards
		p.append(B(w + 0.02, 0.025, dd + 0.02, 0, 0.6 + i * 0.4, 0, cc(col).darkened(0.18)))
	if bool(_q(q, "porch", true)):                          # a covered porch with a railing and two chairs
		p.append(B(w, 0.15, 2.2, 0, 0.42, dd / 2.0 + 1.1, "8a6a48", 0, 0, 0, "tree"))
		p.append(B(w + 0.3, 0.08, 2.6, 0, 3.0, dd / 2.0 + 1.2, roof, 8))
		for x in [-w / 2.0 + 0.15, w / 2.0 - 0.15]:
			p.append(B(0.12, 2.6, 0.12, x, 1.7, dd / 2.0 + 2.1, "7a5a3a", 0, 0, 0, "tree"))
		p.append(B(w * 0.6, 0.06, 0.06, -w * 0.2, 1.4, dd / 2.0 + 2.15, "7a5a3a", 0, 0, 0, "tree"))
		for x in [-w * 0.35, -w * 0.15]:
			p.append(B(0.45, 0.05, 0.45, x, 0.92, dd / 2.0 + 1.0, "2a5a8a"))
			p.append(B(0.45, 0.45, 0.05, x, 1.15, dd / 2.0 + 0.8, "2a5a8a"))
	if bool(_q(q, "chimney", false)):
		p.append(B(0.5, 1.4, 0.5, w * 0.25, 0.35 + h + 1.1, -dd * 0.2, "7a7570", 0, 0, 0, "stone"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.4, dd + 0.4, 4.4]],
			"door": [w * 0.22, 0.35, dd / 2.0 + 0.03, 0.95, 2.0, "6b4a32"], "lights": [[w * 0.22 + 0.7, 2.4, dd / 2.0 + 0.2]],
			"fx": [["smoke", w * 0.25, 0.35 + h + 1.9, -dd * 0.2]] if bool(_q(q, "chimney", false)) else []}


func _k_chalet(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 7.0))
	var dd := float(_q(q, "d", 9.0))
	var col = _q(q, "col", "7a4b2a")
	var p := [B(w + 0.2, 1.0, dd + 0.2, 0, 0.5, 0, "9a958d", 0, 0, 0, "stone"),
			B(w, 4.6, dd, 0, 1.0 + 2.3, 0, col),
			P(w + 2.2, 2.4, dd + 1.6, 0, 5.6 + 1.2, 0, "4a3a32"),
			B(1.0, 2.1, 0.06, 0, 1.0 + 1.05, dd / 2.0 + 0.03, "4a2e1c")]
	_window_row(p, 2, w * 0.8, 2.3, dd / 2.0 + 0.03, 0.9, 1.0, "%ffd9a0")
	_window_row(p, 3, w * 0.8, 4.6, dd / 2.0 + 0.03, 0.8, 1.0, "%ffd9a0")
	_window_row(p, 3, dd * 0.8, 2.3, w / 2.0 + 0.03, 0.8, 1.0, "%ffd9a0", true)
	_window_row(p, 3, dd * 0.8, 2.3, -w / 2.0 - 0.03, 0.8, 1.0, "%ffd9a0", true)
	p.append(B(w, 0.15, 1.4, 0, 3.7, dd / 2.0 + 0.7, "6a4228", 0, 0, 0, "tree"))      # balcony
	p.append(B(w, 0.9, 0.06, 0, 4.2, dd / 2.0 + 1.38, "5a3820", 0, 0, 0, "tree"))
	for i in range(int(w / 0.5)):
		p.append(B(0.08, 0.6, 0.02, -w / 2.0 + 0.25 + i * 0.5, 4.2, dd / 2.0 + 1.42, "e8e0cc"))
	p.append(B(0.3, 0.3, 0.3, w * 0.3, 7.2, -dd * 0.15, "6a6560", 0, 0, 0, "stone"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.3, dd + 0.3, 7.5]],
			"door": [0, 1.0, dd / 2.0 + 0.03, 1.0, 2.1, "4a2e1c"], "lights": [[0.8, 3.0, dd / 2.0 + 0.2]]}


func _k_reception(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 12.0))
	var dd := float(_q(q, "d", 8.0))
	var p := [B(w, 3.4, dd, 0, 1.7, 0, "ece6da"), B(w + 1.2, 0.3, dd + 1.2, 0, 3.55, 0, "5b5b5b"),
			B(w * 0.6, 2.4, 0.06, -w * 0.12, 1.3, dd / 2.0 + 0.03, "%cfe3ee", 0, 0, 0, "window"),
			B(1.6, 2.2, 0.07, w * 0.3, 1.1, dd / 2.0 + 0.04, "3f5b6e"),
			B(w * 0.7, 0.12, 3.0, -w * 0.05, 3.0, dd / 2.0 + 1.5, "c43c2c"),
			B(3.4, 0.7, 0.12, 0, 4.05, dd / 2.0 + 0.4, "1f5a8a")]
	for x in [-w * 0.38, w * 0.28]:
		p.append(C(0.08, 3.0, x, 1.5, dd / 2.0 + 2.9, "8a8a8a"))
	for x in [-w / 2.0 - 1.5, -w / 2.0 - 3.0]:
		p.append(C(0.04, 6.0, x, 3.0, dd / 2.0 + 1.0, "d8d8dc", 0.06, 0, 0, 0, "stone"))
	_window_row(p, 3, dd * 0.7, 1.8, w / 2.0 + 0.03, 1.2, 1.0, "%ffe2b0", true)
	_window_row(p, 3, dd * 0.7, 1.8, -w / 2.0 - 0.03, 1.2, 1.0, "%ffe2b0", true)
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 3.8]],
			"door": [w * 0.3, 0.0, dd / 2.0 + 0.04, 1.6, 2.2, "3f5b6e"],
			"labels": [[str(_q(q, "text", "REZEPTION")), 0, 4.05, dd / 2.0 + 0.48, 72, 0.0, "ffffff"]],
			"lights": [[0, 2.8, dd / 2.0 + 1.8], [w * 0.3, 2.6, dd / 2.0 + 0.4]],
			"fx": [["flag", -w / 2.0 - 1.5, 0, dd / 2.0 + 1.0, "c8102e"], ["flag", -w / 2.0 - 3.0, 0, dd / 2.0 + 1.0, "1f5a8a"]]}


func _k_barrier(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 4.5))
	var open := bool(_q(q, "open", false))
	var p := [B(0.35, 1.0, 0.35, 0, 0.5, 0, "e8e8e8", 0, 0, 0, "metal"), B(0.36, 0.12, 0.36, 0, 0.75, 0, "c8102e"),
			B(0.35, 0.12, 0.35, 0, 1.06, 0, "333333"), B(0.08, 0.8, 0.08, L, 0.4, 0, "8a8a8a"),
			B(0.15, 0.25, 0.25, 0, 1.25, 0, "*ff9a2a")]                              # the orange lamp on top
	for i in range(5):
		var seg := L / 5.0
		var col := "c8102e" if i % 2 == 0 else "f2f2f2"
		if open:
			p.append(B(0.08, seg, 0.08, 0.2, 0.95 + seg * (i + 0.5), 0, col))
		else:
			p.append(B(seg, 0.08, 0.08, 0.2 + seg * (i + 0.5), 0.95, 0, col))
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["circ", 0, 0, 0.3, 1.1]], "labels": [["STOP", 0.2 + L * 0.5, 1.12, 0.06, 28, 0.0, "ffffff"]]}


func _k_sanitary(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 14.0))
	var dd := float(_q(q, "d", 7.0))
	var p := [B(w, 3.0, dd, 0, 1.5, 0, "ddd6c8"), P(w + 0.8, 1.2, dd + 0.8, 0, 3.6, 0, "6e3b2a", 0, 90, 0),
			B(w + 0.1, 0.4, dd + 0.1, 0, 0.2, 0, "9a958d", 0, 0, 0, "stone")]
	p[1] = P(dd + 0.8, 1.2, w + 0.8, 0, 3.6, 0, "6e3b2a", 0, 90, 0)
	var n := int(w / 2.6)
	for i in range(n):
		var x := -w / 2.0 + w * (i + 0.5) / n
		p.append(B(0.9, 2.05, 0.06, x, 1.02, dd / 2.0 + 0.03, ["2a6fb0", "c0392b"][i % 2]))
		p.append(B(0.5, 0.25, 0.06, x, 2.4, dd / 2.0 + 0.03, "%ffffff", 0, 0, 0, "window"))
		p.append(B(0.25, 0.12, 0.2, x, 2.7, dd / 2.0 + 0.12, "*fff4d8"))
	for i in range(3):                                       # wash basins along the back
		p.append(B(0.7, 0.2, 0.5, -w * 0.3 + i * 1.0, 0.85, -dd / 2.0 - 0.25, "f2f2f2"))
		p.append(C(0.02, 0.25, -w * 0.3 + i * 1.0, 1.05, -dd / 2.0 - 0.1, "b0b0b0"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.6, 4.2]],
			"labels": [[str(_q(q, "text", "WC · Dusche")), 0, 2.85, dd / 2.0 + 0.05, 64]],
			"lights": [[0, 2.7, dd / 2.0 + 0.6], [-w * 0.35, 2.7, dd / 2.0 + 0.6]]}


func _k_shop(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 8.0))
	var dd := float(_q(q, "d", 6.0))
	var p := [B(w, 3.2, dd, 0, 1.6, 0, "f0e6d0"), B(w + 0.6, 0.3, dd + 0.6, 0, 3.35, 0, "5a5a5a"),
			B(w * 0.55, 2.0, 0.06, -w * 0.15, 1.4, dd / 2.0 + 0.03, "%e8f0f2", 0, 0, 0, "window"),
			B(1.2, 2.2, 0.06, w * 0.3, 1.1, dd / 2.0 + 0.04, "9fc4d8", 0, 0, 0, "window"),
			B(w * 0.9, 0.7, 0.12, 0, 3.0, dd / 2.0 + 0.1, "2e7d32")]
	for i in range(8):                                      # striped awning
		p.append(B(w * 0.9 / 8.0, 0.05, 1.6, -w * 0.45 + w * 0.9 / 8.0 * (i + 0.5), 2.55, dd / 2.0 + 0.8, "f2f2f2" if i % 2 == 0 else "2e7d32", 14))
	for i in range(3):                                      # fruit and vegetable crates in front
		p.append(B(0.6, 0.35, 0.4, -w * 0.35 + i * 0.7, 0.6, dd / 2.0 + 0.5, "a87b45"))
		p.append(B(0.55, 0.12, 0.35, -w * 0.35 + i * 0.7, 0.82, dd / 2.0 + 0.5, ["d35400", "6ab04c", "c0392b"][i]))
		p.append(B(0.08, 0.45, 0.08, -w * 0.35 + i * 0.7, 0.22, dd / 2.0 + 0.5, "6b4a32"))
	p.append(B(0.9, 0.9, 0.6, w * 0.08, 0.45, dd / 2.0 + 0.4, "e6eef5", 0, 0, 0, 32.0))   # ice cream freezer (warm at the back)
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 3.5], ["box", 0, dd / 2.0 + 0.5, w * 0.8, 0.8, 0.9]],
			"labels": [[str(_q(q, "text", "LADEN")), 0, 3.0, dd / 2.0 + 0.17, 80, 0.0, "ffffff"]], "lights": [[0, 2.6, dd / 2.0 + 0.8]]}


func _k_restaurant(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 16.0))
	var dd := float(_q(q, "d", 10.0))
	var p := [B(w, 0.6, dd, 0, 0.3, 0, "8a857d", 0, 0, 0, "stone"), B(w, 3.6, dd, 0, 0.6 + 1.8, 0, "e6d8c0"),
			P(dd + 1.2, 2.6, w + 1.2, 0, 4.2 + 1.3, 0, "7a3b2a", 0, 90, 0),
			B(1.4, 2.3, 0.07, 0, 0.6 + 1.15, dd / 2.0 + 0.04, "5a3a22"),
			B(0.8, 2.6, 0.8, w * 0.3, 5.4, -dd * 0.2, "8a857d", 0, 0, 0, 45.0)]        # kitchen chimney (warm)
	_window_row(p, 4, w * 0.85, 2.2, dd / 2.0 + 0.03, 1.4, 1.5)
	_window_row(p, 3, dd * 0.7, 2.2, w / 2.0 + 0.03, 1.2, 1.3, "%ffd9a0", true)
	_window_row(p, 3, dd * 0.7, 2.2, -w / 2.0 - 0.03, 1.2, 1.3, "%ffd9a0", true)
	p.append(B(4.5, 0.8, 0.12, 0, 4.0, dd / 2.0 + 0.3, "3a2a1a"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 6.0]],
			"labels": [[str(_q(q, "text", "Restaurant")), 0, 4.0, dd / 2.0 + 0.37, 72, 0.0, "f2e6c8"]],
			"fx": [["smoke", w * 0.3, 6.9, -dd * 0.2]], "lights": [[-2.0, 3.2, dd / 2.0 + 0.5], [2.0, 3.2, dd / 2.0 + 0.5]],
			"door": [0, 0.6, dd / 2.0 + 0.04, 1.4, 2.3, "5a3a22"]}


func _k_kiosk(q: Dictionary) -> Dictionary:
	var p := [B(3.0, 2.5, 2.5, 0, 1.25, 0, _q(q, "col", "2a7ab0")), P(2.9, 0.7, 3.4, 0, 2.85, 0, "f2f2f2", 0, 90, 0),
			B(2.0, 0.08, 0.6, 0, 1.0, 1.55, "e8e0cc"), B(2.0, 1.0, 0.06, 0, 2.15, 1.5, "f2c22e", -60),
			B(1.8, 0.9, 0.04, 0, 1.55, 1.24, "%ffe2b0", 0, 0, 0, "window"),
			B(0.6, 1.4, 0.5, -1.0, 0.7, -0.6, "f2f2f2", 0, 0, 0, 34.0)]
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", 0, 0, 3.1, 2.6, 3.0]],
			"labels": [[str(_q(q, "text", "KIOSK")), 0, 2.85, 1.72, 56, 0.0, "c0392b"]], "lights": [[0, 2.3, 1.6]]}


func _k_house(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 9.0))
	var dd := float(_q(q, "d", 8.0))
	var fl := int(_q(q, "floors", 2))
	var h := 2.8 * fl
	var col = _q(q, "col", "e8dcc4")
	var p := [B(w, h, dd, 0, h / 2.0, 0, col), P(w + 1.0, 2.6, dd + 0.9, 0, h + 1.3, 0, _q(q, "roof", "8b3a2a")),
			B(1.0, 2.1, 0.06, w * 0.25, 1.05, dd / 2.0 + 0.03, "5a3a22"), B(0.6, 1.5, 0.6, -w * 0.25, h + 1.6, -dd * 0.1, "8a857d", 0, 0, 0, "stone")]
	for f in range(fl):
		_window_row(p, 3, w * 0.8, 1.6 + f * 2.8, dd / 2.0 + 0.03, 0.9, 1.1)
		_window_row(p, 2, dd * 0.7, 1.6 + f * 2.8, w / 2.0 + 0.03, 0.9, 1.1, "%ffd9a0", true)
		_window_row(p, 2, dd * 0.7, 1.6 + f * 2.8, -w / 2.0 - 0.03, 0.9, 1.1, "%ffd9a0", true)
	var lbl := []
	if bool(_q(q, "shop", false)):                           # a shop on the ground floor (bakery …)
		p.append(B(w * 0.5, 1.6, 0.07, -w * 0.15, 1.3, dd / 2.0 + 0.04, "%f8e8c8", 0, 0, 0, "window"))
		for i in range(6):
			p.append(B(w * 0.6 / 6.0, 0.05, 1.3, -w * 0.3 + w * 0.6 / 6.0 * (i + 0.5), 2.55, dd / 2.0 + 0.65, "c0392b" if i % 2 == 0 else "f2f2f2", 15))
		lbl.append([str(_q(q, "text", "Bäckerei")), 0, 3.3, dd / 2.0 + 0.06, 72, 0.0, "6a3a1a"])
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, h + 2.0]], "labels": lbl,
			"door": [w * 0.25, 0, dd / 2.0 + 0.03, 1.0, 2.1, "5a3a22"], "fx": [["smoke", -w * 0.25, h + 2.5, -dd * 0.1]] if bool(_q(q, "smoke", false)) else []}


func _k_bakery(q: Dictionary) -> Dictionary:
	var q2: Dictionary = q.duplicate()
	q2["shop"] = true
	q2["smoke"] = true
	if not q2.has("col"):
		q2["col"] = "f2e4c4"
	return _k_house(q2)


func _k_church(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 20.0))
	var w := float(_q(q, "w", 10.0))
	var p := [B(w, 9.0, L, 0, 4.5, 0, "ece6da", 0, 0, 0, "stone"), P(w + 1.0, 5.0, L + 0.8, 0, 9.0 + 2.5, 0, "4a4a4e"),
			B(5.0, 22.0, 5.0, 0, 11.0, L / 2.0 + 2.0, "e4ddd0", 0, 0, 0, "stone"),
			["c", 0.0, 9.0, 3.9, 0, 22.0 + 4.5, L / 2.0 + 2.0, "3a5a4a", 0, 45, 0, "stone"],
			C(1.0, 0.12, 0, 18.5, L / 2.0 + 4.53, "f2f2f2", 0, 90, 0, 0),
			B(1.8, 3.2, 0.1, 0, 1.6, L / 2.0 + 4.53, "5a3a22")]
	for i in range(4):
		for sd in [-1.0, 1.0]:
			p.append(B(0.08, 3.2, 1.2, sd * (w / 2.0 + 0.03), 4.8, -L / 2.0 + L * (i + 0.5) / 4.0, "%c8b070", 0, 0, 0, "window"))
	p.append(B(0.1, 1.2, 1.2, 2.53, 18.5, L / 2.0 + 2.0, "2a2a2a"))
	p.append(B(0.1, 1.2, 1.2, -2.53, 18.5, L / 2.0 + 2.0, "2a2a2a"))
	return {"p": p, "t": "stone", "lod": "big", "ob": [["box", 0, 0, w + 0.2, L + 0.2, 12.0], ["box", 0, L / 2.0 + 2.0, 5.2, 5.2, 22.0]]}


func _k_barn(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 14.0))
	var dd := float(_q(q, "d", 10.0))
	var p := [B(w, 6.0, dd, 0, 3.0, 0, _q(q, "col", "8b2a1f")), P(dd + 1.2, 4.0, w + 1.2, 0, 8.0, 0, "4a4a4e", 0, 90, 0),
			B(4.0, 4.5, 0.08, 0, 2.25, dd / 2.0 + 0.04, "6a1f16"), B(4.2, 0.15, 0.1, 0, 2.25, dd / 2.0 + 0.1, "e8e0cc", 0, 0, 45),
			B(4.2, 0.15, 0.1, 0, 2.25, dd / 2.0 + 0.1, "e8e0cc", 0, 0, -45), B(1.4, 1.4, 0.08, 0, 6.6, dd / 2.0 + 0.04, "3a2a1a")]
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 9.5]]}


func _k_stable(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 16.0))
	var dd := float(_q(q, "d", 6.0))
	var p := [B(w, 3.0, dd, 0, 1.5, 0, _q(q, "col", "9a6a42")), P(dd + 1.6, 1.5, w + 0.8, 0, 3.75, 0.3, "5a4a42", 0, 90, 0)]
	var n := int(w / 3.2)
	for i in range(n):
		var x := -w / 2.0 + w * (i + 0.5) / n
		p.append(B(1.2, 1.1, 0.07, x, 0.6, dd / 2.0 + 0.04, "5a3820"))
		p.append(B(1.2, 0.9, 0.05, x, 1.65, dd / 2.0 + 0.03, "1a1410"))
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 4.0]], "lights": [[0, 2.7, dd / 2.0 + 0.4]]}


func _k_boathouse(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 6.0))
	var dd := float(_q(q, "d", 8.0))
	var p := [B(w, 3.2, dd, 0, 1.6, 0, _q(q, "col", "6a4a2e")), P(w + 0.8, 1.8, dd + 0.8, 0, 3.2 + 0.9, 0, "3e3a36"),
			B(w * 0.7, 2.6, 0.07, 0, 1.3, -dd / 2.0 - 0.04, "4a3220"), B(0.9, 2.0, 0.06, w / 2.0 + 0.03, 1.0, dd * 0.2, "4a3220", 0, 90, 0)]
	for i in range(7):
		p.append(B(w + 0.02, 0.03, dd + 0.02, 0, 0.4 + i * 0.4, 0, "56391f"))
	_window_row(p, 1, dd * 0.4, 1.9, w / 2.0 + 0.03, 0.7, 0.6, "%ffd9a0", true)
	p[p.size() - 2][6] = -dd * 0.2
	p[p.size() - 1][6] = -dd * 0.2
	return {"p": p, "t": "caravan", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 4.5]],
			"door": [w / 2.0 + 0.03, 0.0, dd * 0.2, 0.9, 2.0, "4a3220", 90.0], "lights": [[w / 2.0 + 0.4, 2.5, dd * 0.2]]}


func _k_latrine(_q: Dictionary) -> Dictionary:
	var p := [B(1.3, 2.2, 1.3, 0, 1.1, 0, "7a5a3a", 0, 0, 0, "tree"), B(1.6, 0.08, 1.7, 0, 2.3, 0, "4a4a3e", -10),
			B(0.8, 1.9, 0.05, 0, 0.98, 0.67, "6a4a2e", 0, 0, 0, "tree"), B(0.12, 0.12, 0.02, 0, 1.6, 0.7, "1a1410")]
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["box", 0, 0, 1.4, 1.4, 2.3]]}


func _k_shed(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 2.5))
	var dd := float(_q(q, "d", 2.0))
	var p := [B(w, 2.1, dd, 0, 1.05, 0, _q(q, "col", "6d8a5a")), P(w + 0.4, 0.7, dd + 0.4, 0, 2.45, 0, "4a3a32"),
			B(0.8, 1.8, 0.05, 0, 0.9, dd / 2.0 + 0.03, "4a3a28")]
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", 0, 0, w + 0.1, dd + 0.1, 2.8]]}


func _k_cable_station(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 10.0))
	var dd := float(_q(q, "d", 8.0))
	var up := float(_q(q, "up", 40.0))                   # how far the cable is drawn uphill (along -z)
	var rise := float(_q(q, "rise", 18.0))
	var p := [B(w, 1.0, dd, 0, 0.5, 0, "8a8a86", 0, 0, 0, "stone"), B(w, 0.4, dd, 0, 6.8, 0, "3a3a3e"),
			B(1.8, 2.6, 2.4, -w * 0.3, 2.3, dd * 0.25, "c43c2c")]
	for x in [-w / 2.0 + 0.3, w / 2.0 - 0.3]:
		for z in [-dd / 2.0 + 0.3, dd / 2.0 - 0.3]:
			p.append(B(0.4, 5.8, 0.4, x, 3.9, z, "8a8a86", 0, 0, 0, "stone"))
	p.append(C(2.2, 0.3, 0, 5.6, 0, "3a3a3e", 0, 0, 0, 0, 38.0))        # the bull wheel (motor warm)
	p.append(B(1.4, 1.2, 1.4, 0, 4.9, 0, "5a5a5e", 0, 0, 0, 45.0))
	for sd in [-1.0, 1.0]:                                  # the cables up the slope and a gondola
		p.append(ROD(Vector3(sd * 2.2, 5.6, 0), Vector3(sd * 2.2, 5.6 + rise, -up), 0.05, "1a1a1a"))
	p.append(B(1.8, 1.8, 2.2, 2.2, 3.3, -6.0, "c43c2c"))
	p.append(B(1.6, 0.7, 2.25, 2.2, 3.6, -6.0, "%d0e4f0", 0, 0, 0, "window"))
	p.append(B(0.08, 1.4, 0.08, 2.2, 4.9, -6.0, "6a6a6a"))
	p.append(B(2.4, 0.3, 0.3, 0, 5.6 + rise * 0.5, -up * 0.5, "6a6a6a"))   # a pylon on the way
	p.append(B(0.5, 5.6 + rise * 0.5, 0.5, 0, (5.6 + rise * 0.5) / 2.0, -up * 0.5, "6a6a6a", 0, 0, 0, "stone"))
	return {"p": p, "t": "stone", "lod": "big", "ob": [["box", 0, 0, w + 0.2, dd + 0.2, 7.0], ["circ", 0, -up * 0.5, 0.5, 15.0]],
			"labels": [[str(_q(q, "text", "Seilbahn")), 0, 6.3, dd / 2.0 + 0.05, 72, 0.0, "f2f2f2"]], "lights": [[0, 6.0, 0]]}


func _k_stage(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 10.0))
	var dd := float(_q(q, "d", 6.0))
	var th := 6.0
	var p := [B(w, 1.2, dd, 0, 0.6, 0, "1e1e1e"), B(w, 4.5, 0.1, 0, 1.2 + 2.25, -dd / 2.0 + 0.1, _q(q, "col", "2a3a7a"), 0, 0, 0, "tent")]
	for i in range(4):                                      # stairs at the side
		p.append(B(1.2, 0.3, 0.35, w / 2.0 + 0.7, 0.15 + i * 0.3, dd / 2.0 - 0.4 - i * 0.35, "3a3a3a"))
	for x in [-w / 2.0 + 0.3, w / 2.0 - 0.3]:              # two truss towers and the beam (aluminium)
		for dx in [-0.2, 0.2]:
			for dz in [-0.2, 0.2]:
				p.append(C(0.025, th, x + dx, th / 2.0, dd / 2.0 - 0.4 + dz, "c8c8cc", 0, 0, 0, 0, "metal"))
		for k in range(6):
			p.append(B(0.4, 0.02, 0.02, x, 0.5 + k * 1.0, dd / 2.0 - 0.6, "c8c8cc", 0, 0, 35))
	for dy in [-0.2, 0.2]:
		for dz in [-0.2, 0.2]:
			p.append(C(0.025, w, 0, th + dy, dd / 2.0 - 0.4 + dz, "c8c8cc", 0, 0, 0, 90, "metal"))
	for i in range(8):                                      # spotlights (halogen: hot in the thermal picture)
		var x2 := -w * 0.4 + w * 0.8 * i / 7.0
		p.append(C(0.14, 0.35, x2, th - 0.45, dd / 2.0 - 0.4, "151515", 0, -30, 0, 0, 80.0))
		p.append(C(0.12, 0.02, x2, th - 0.62, dd / 2.0 - 0.3, "*fff0c8", 0, -30, 0, 0))
	for x in [-w / 2.0 - 0.8, w / 2.0 + 0.8]:               # speaker stacks
		p.append(B(1.0, 2.6, 0.9, x, 1.3, dd / 2.0 - 0.6, "151515"))
	return {"p": p, "t": "stone", "lod": "big", "ob": [["box", 0, 0, w + 2.0, dd + 0.2, 1.2]],
			"lights": [[-w * 0.25, th - 0.8, dd / 2.0], [w * 0.25, th - 0.8, dd / 2.0]]}


# ---- camping -----------------------------------------------------------------------------------------------------------
func _k_tent(q: Dictionary) -> Dictionary:
	var style := str(_q(q, "style", "dome"))
	var col = _q(q, "col", "d8692a")
	var c2: Color = cc(col).darkened(0.25)
	var p := []
	var ob := []
	match style:
		"tunnel":                                           # 4 × 2.4 m, three hoops
			p.append(C(1.15, 4.0, 0, 0, 0, col, 0, 90, 0, 0, "tent"))
			for z in [-1.6, 0.0, 1.6]:
				p.append(TO(1.12, 1.2, 0, 0, z, c2, 90, 0, 0, "tent"))
			p.append(B(0.9, 0.95, 0.04, 0, 0.45, 2.0, "1a1410"))
			ob.append(["box", 0, 0, 2.5, 4.2, 1.2])
		"ridge":                                            # classic ridge tent (scouts)
			p.append(P(2.2, 1.7, 3.0, 0, 0.85, 0, col, 0, 0, 0, "tent"))
			p.append(C(0.025, 1.75, 0, 0.87, 1.52, "6a4a2e"))
			p.append(C(0.025, 1.75, 0, 0.87, -1.52, "6a4a2e"))
			p.append(P(0.8, 1.1, 0.02, 0, 0.55, 1.52, "1a1410"))
			ob.append(["box", 0, 0, 2.4, 3.2, 1.7])
		"family":                                           # big cabin tent with a porch
			p.append(B(3.2, 1.9, 3.0, 0, 0.95, -0.4, col, 0, 0, 0, "tent"))
			p.append(P(3.4, 0.6, 3.2, 0, 2.2, -0.4, c2, 0, 90, 0, "tent"))
			p.append(B(3.0, 1.7, 1.6, 0, 0.85, 1.7, c2, 0, 0, 0, "tent"))
			p.append(B(1.0, 1.6, 0.04, 0, 0.8, 2.52, "1a1410"))
			ob.append(["box", 0, 0.3, 3.4, 4.8, 2.4])
		_:                                                  # dome tent 2.3 m, a little porch
			p.append(S(1.2, 2.7, 0, 0, 0, col, "tent"))
			p.append(S(0.75, 1.9, 0, 0, 1.05, c2, "tent"))
			for a in [45.0, -45.0]:
				p.append(TO(1.18, 1.23, 0, 0, 0, "3a3a3a", 90, a, 0, "tent"))
			p.append(B(0.7, 0.75, 0.04, 0, 0.38, 1.72, "1a1410"))
			ob.append(["circ", 0, 0.3, 1.3, 1.3])
	return {"p": p, "t": "tent", "lod": "mid", "ob": ob}


func _k_yurt(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 3.2))
	var p := [C(r, 1.8, 0, 0.9, 0, _q(q, "col", "e8e0cc"), 0, 0, 0, 0, "tent"), K(r + 0.3, 1.7, 0, 1.8 + 0.85, 0, "d8cfb8", 0, 0, 0, "tent"),
			C(0.5, 0.25, 0, 3.55, 0, "8a5a32"), B(0.95, 1.6, 0.12, 0, 0.8, r - 0.02, "c06020", 0, 0, 0, "tree"),
			TO(r - 0.02, r + 0.04, 0, 0.3, 0, "8a2a1a"), TO(r - 0.02, r + 0.04, 0, 1.5, 0, "8a2a1a")]
	return {"p": p, "t": "tent", "lod": "big", "ob": [["circ", 0, 0, r + 0.1, 3.5]], "fx": [["smoke", 0, 3.8, 0]] if bool(_q(q, "smoke", false)) else []}


func _k_sarasani(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 6.0))
	var col = _q(q, "col", "262626")                      # black «Kohten» cloth
	var p := [C(r, 2.0, 0, 1.0, 0, col, 0, 0, 0, 0, "tent"), K(r + 0.3, 4.6, 0, 2.0 + 2.3, 0, col, 0, 0, 0, "tent"),
			C(0.08, 8.2, 0, 4.1, 0, "8a6a48", 0, 0, 0, 0, "tree"), B(1.4, 1.8, 0.1, 0, 0.9, r - 0.02, "1a1410")]
	for i in range(8):                                     # guy ropes to the pegs
		var a := TAU * i / 8.0
		p.append(ROD(Vector3(cos(a) * r, 2.0, sin(a) * r), Vector3(cos(a) * (r + 2.0), 0.05, sin(a) * (r + 2.0)), 0.015, "d8cfb8"))
		p.append(B(0.05, 0.25, 0.05, cos(a) * (r + 2.0), 0.1, sin(a) * (r + 2.0), "8a6a48"))
	return {"p": p, "t": "tent", "lod": "big", "ob": [["circ", 0, 0, r + 0.2, 6.5]], "fx": [["flag", 0, 8.2 - 6.0, 0, str(_q(q, "flag", "c8102e"))]]}


func _k_caravan(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 5.6))
	var col = _q(q, "stripe", "2a6fb0")
	var p := [B(L, 2.2, 2.3, 0, 1.4, 0, _q(q, "col", "e4e6e8")), B(L, 0.25, 2.3, 0, 0.4, 0, "5a5c60"),
			B(L - 0.2, 0.12, 2.1, 0, 2.56, 0, "b8babd"), B(L, 0.08, 0.04, 0, 1.0, 1.16, col), B(L, 0.08, 0.04, 0, 1.0, -1.16, col),
			B(0.75, 1.9, 0.05, L * 0.28, 1.4, 1.17, "8a8c90"),
			B(0.05, 0.55, 0.9, -L / 2.0 - 0.01, 1.7, 0, "%ffd9a0", 0, 0, 0, "window"),
			B(1.6, 0.7, 0.05, -L * 0.27, 1.75, 1.16, "%ffd9a0", 0, 0, 0, "window"), B(1.0, 0.6, 0.05, -L * 0.1, 1.75, -1.16, "%ffd9a0", 0, 0, 0, "window"),
			C(0.33, 0.22, 0, 0.33, 1.1, "141414", 0, 90, 0, 0), C(0.33, 0.22, 0, 0.33, -1.1, "141414", 0, 90, 0, 0),
			ROD(Vector3(-L / 2.0, 0.45, 0.3), Vector3(-L / 2.0 - 1.4, 0.4, 0), 0.08, "3a3a3e"),
			ROD(Vector3(-L / 2.0, 0.45, -0.3), Vector3(-L / 2.0 - 1.4, 0.4, 0), 0.08, "3a3a3e"),
			C(0.15, 0.45, -L / 2.0 - 0.6, 0.72, 0, "b33a2a")]
	if bool(_q(q, "awning", true)):
		p.append(B(2.6, 0.04, 1.6, L * 0.15, 2.35, 1.95, _q(q, "awning_col", "c86a2a"), 7, 0, 0, "tent"))
		for x in [L * 0.15 - 1.25, L * 0.15 + 1.25]:
			p.append(C(0.02, 2.2, x, 1.12, 2.7, "9a9a9a"))
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", -0.4, 0, L + 1.2, 2.5, 2.6]],
			"door": [L * 0.28 - 0.375, 0.45, 1.17, 0.75, 1.9, "8a8c90"], "lights": [[L * 0.28 + 0.5, 2.1, 1.3]]}


func _k_motorhome(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 7.0))
	var style := str(_q(q, "style", "alcove"))
	var col = _q(q, "col", "f0f0ee")
	var st = _q(q, "stripe", "8a8f96")
	var p := [B(L - 1.8, 2.5, 2.3, -0.9, 0.6 + 1.25, 0, col), B(L, 0.35, 2.2, 0, 0.55, 0, "3a3a3e"),
			B(L - 1.8, 0.1, 0.04, -0.9, 1.3, 1.16, st), B(L - 1.8, 0.1, 0.04, -0.9, 1.3, -1.16, st),
			B(0.75, 1.95, 0.05, 0.3, 1.6, 1.17, "c8c8c8"),
			B(1.3, 0.6, 0.05, -1.6, 2.0, 1.16, "%ffd9a0", 0, 0, 0, "window"), B(1.1, 0.6, 0.05, -2.2, 2.0, -1.16, "%ffd9a0", 0, 0, 0, "window"),
			B(0.05, 0.9, 1.4, -L / 2.0 - 0.01, 2.0, 0, "%ffd9a0", 0, 0, 0, "window")]
	if style == "integrated":
		p.append(B(1.8, 2.5, 2.3, L / 2.0 - 0.9, 1.85, 0, col))
		p.append(B(0.06, 1.0, 2.1, L / 2.0 + 0.01, 2.2, 0, "26323c", 0, 0, -12, "glass"))
	else:                                                   # cab + alcove over the cab
		p.append(B(1.8, 1.4, 2.2, L / 2.0 - 0.9, 1.25, 0, "e8e8e8"))
		p.append(B(0.06, 0.8, 2.0, L / 2.0 - 0.15, 1.75, 0, "26323c", 0, 0, -20, "glass"))
		p.append(B(1.9, 0.9, 2.3, L / 2.0 - 1.0, 2.65, 0, col))
		p.append(B(0.06, 0.6, 1.9, L / 2.0 - 1.0 + 0.97, 2.65, 0, "dcdcdc", 0, 0, 25))
	p.append(B(0.25, 0.25, 0.3, L / 2.0 + 0.01, 0.8, 0.8, "*fff4d8"))
	p.append(B(0.25, 0.25, 0.3, L / 2.0 + 0.01, 0.8, -0.8, "*fff4d8"))
	for x in [L / 2.0 - 1.1, -L / 2.0 + 1.3]:
		for z in [1.0, -1.0]:
			p.append(C(0.38, 0.25, x, 0.38, z, "141414", 0, 90, 0, 0))
	p.append(B(L - 2.4, 0.18, 0.18, -1.2, 3.0, 1.2, "c8c8c8"))   # rolled up awning
	p.append(B(0.9, 0.12, 0.7, -L * 0.25, 3.15, 0, "dcdcdc"))     # roof vent
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", 0, 0, L + 0.1, 2.4, 3.1]],
			"door": [0.3 - 0.375, 0.65, 1.17, 0.75, 1.95, "c8c8c8"], "lights": [[0.9, 2.5, 1.3]]}


func _k_campfire(q: Dictionary) -> Dictionary:
	var fire := bool(_q(q, "fire", true))
	var p := []
	for i in range(10):
		var a := TAU * i / 10.0
		p.append(S(0.2, 0.24, cos(a) * 0.8, 0.08, sin(a) * 0.8, "707070", "stone"))
	p.append(B(1.0, 0.12, 0.14, 0, 0.08, 0, "2a1c12", 0, 30, 0, 60.0 if fire else "stone"))
	p.append(B(1.0, 0.12, 0.14, 0, 0.14, 0, "2a1c12", 0, -40, 0, 60.0 if fire else "stone"))
	var lights := []
	var fx := []
	if fire:
		p.append(K(0.32, 0.8, 0, 0.5, 0, "*ff8a1a", 0, 0, 0, 80.0))
		p.append(K(0.2, 0.55, 0.15, 0.4, 0.1, "*ffc23a", 0, 0, 0, 80.0))
		lights.append([0, 0.8, 0, Color(1.0, 0.55, 0.2)])
		fx.append(["smoke", 0, 1.2, 0])
	if bool(_q(q, "benches", true)):                        # log benches around
		for a in [0.0, PI * 0.66, PI * 1.33]:
			p.append(C(0.18, 2.0, cos(a) * 2.6, 0.18, sin(a) * 2.6, "6a4a2e", 0, 0, rad_to_deg(-a), 90, "tree"))
	return {"p": p, "t": "stone", "lod": "small", "ob": [["circ", 0, 0, 1.0, 0.4]], "lights": lights, "fx": fx}


func _k_picnic_table(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 2.0))
	var col = _q(q, "col", "8a6a48")
	var p := [B(L, 0.06, 0.8, 0, 0.75, 0, col, 0, 0, 0, "tree"), B(L, 0.05, 0.3, 0, 0.45, 0.65, col, 0, 0, 0, "tree"),
			B(L, 0.05, 0.3, 0, 0.45, -0.65, col, 0, 0, 0, "tree")]
	for x in [-L / 2.0 + 0.2, L / 2.0 - 0.2]:
		p.append(B(0.08, 0.85, 0.08, x, 0.38, 0.3, "6a4a2e", 25, 0, 0, "tree"))
		p.append(B(0.08, 0.85, 0.08, x, 0.38, -0.3, "6a4a2e", -25, 0, 0, "tree"))
		p.append(B(0.08, 0.06, 1.6, x, 0.4, 0, "6a4a2e", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0, L, 1.6, 0.8]]}


func _k_bbq(q: Dictionary) -> Dictionary:
	var hot := float(_q(q, "hot", 70.0))
	var p := []
	if str(_q(q, "style", "kettle")) == "brick":
		p = [B(1.4, 0.9, 0.8, 0, 0.45, 0, "8a4a3a", 0, 0, 0, "stone"), B(0.9, 0.05, 0.6, 0, 0.92, 0, "222222", 0, 0, 0, hot),
			B(0.5, 1.4, 0.5, 0, 1.6, -0.15, "8a4a3a", 0, 0, 0, "stone")]
	else:
		for k in range(3):
			var a := TAU * k / 3.0
			p.append(C(0.015, 0.75, cos(a) * 0.2, 0.36, sin(a) * 0.2, "222222", 0, rad_to_deg(sin(a) * 0.25), 0, rad_to_deg(-cos(a) * 0.25)))
		p.append(S(0.3, 0.3, 0, 0.78, 0, "141414", hot))
		p.append(S(0.3, 0.3, 0, 0.82, 0, "1a1a1a", hot - 10.0))
	return {"p": p, "t": "stone", "lod": "small", "ob": [["circ", 0, 0, 0.45, 0.9]], "fx": [["smoke", 0, 1.1, 0]] if hot > 50.0 else []}


func _k_power_post(_q: Dictionary) -> Dictionary:
	var p := [B(0.3, 1.0, 0.3, 0, 0.5, 0, "2a6a3a"), B(0.32, 0.08, 0.32, 0, 1.04, 0, "1a1a1a"),
			B(0.22, 0.08, 0.02, 0, 0.85, 0.16, "*4aff6a"), B(0.08, 0.08, 0.04, 0.08, 0.55, 0.16, "1a3aa0")]
	return {"p": p, "t": "caravan", "lod": "small", "ob": [["circ", 0, 0, 0.22, 1.0]]}


func _k_water_tap(_q: Dictionary) -> Dictionary:
	var p := [B(0.25, 1.1, 0.25, 0, 0.55, 0, "8a8a86", 0, 0, 0, "stone"), C(0.02, 0.2, 0, 1.0, 0.15, "b0b0b0", 0, 90, 0, 0),
			B(0.6, 0.15, 0.45, 0, 0.35, 0.3, "8a8a86", 0, 0, 0, "stone")]
	return {"p": p, "t": "stone", "lod": "small", "ob": [["circ", 0, 0.1, 0.35, 1.1]]}


func _k_pitch_post(q: Dictionary) -> Dictionary:
	var p := [B(0.1, 0.8, 0.1, 0, 0.4, 0, "6a4a2e", 0, 0, 0, "tree"), B(0.24, 0.18, 0.03, 0, 0.72, 0.06, "f2f2f2")]
	var lb := []
	if _q(q, "nr", "") != "":
		lb.append([str(q["nr"]), 0, 0.72, 0.08, 24, 0.0, "1a1a1a"])
	return {"p": p, "t": "tree", "lod": "small", "labels": lb}


func _k_flagpole(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 8.0))
	var p := [C(0.05, h, 0, h / 2.0, 0, "d8d8dc", 0.07, 0, 0, 0, "stone"), S(0.08, 0.16, 0, h, 0, "d4af37")]
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["circ", 0, 0, 0.15, h]], "fx": [["flag", 0, h - 6.0, 0, str(_q(q, "col", "c8102e"))]]}


func _k_totem(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 4.0))
	var cols := ["c0392b", "e8b21e", "2a6fb0", "2e7d32", "8a5a32"]
	var p := []
	var n := int(h / 0.8)
	for i in range(n):
		p.append(C(0.3, 0.8, 0, 0.4 + i * 0.8, 0, cols[i % cols.size()], 0, 0, 0, 0, "tree"))
		p.append(B(0.2, 0.12, 0.04, -0.1, 0.5 + i * 0.8, 0.3, "151515"))
		p.append(B(0.2, 0.12, 0.04, 0.1, 0.5 + i * 0.8, 0.3, "151515"))
	p.append(B(1.8, 0.25, 0.3, 0, h - 0.6, 0, "e8b21e", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["circ", 0, 0, 0.35, h]]}


# ---- vehicles & water ----------------------------------------------------------------------------------------------------
func _k_car(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "2b5fa8")
	var style := str(_q(q, "style", "sedan"))
	var L := 4.3
	var h2 := 0.55
	if style == "van":
		L = 5.0
		h2 = 1.2
	elif style == "suv":
		L = 4.6
		h2 = 0.75
	var p := [B(1.8, 0.65, L, 0, 0.62, 0, col, 0, 0, 0, "car")]
	if style == "van":
		p.append(B(1.78, h2, L * 0.75, 0, 0.95 + h2 / 2.0, -L * 0.1, col, 0, 0, 0, "car"))
		p.append(B(1.6, 0.6, 0.06, 0, 1.45, L * 0.28, "26323c", -25, 0, 0, "glass"))
	else:
		p.append(B(1.62, h2, L * 0.5, 0, 0.95 + h2 / 2.0, -L * 0.05, cc(col).darkened(0.12), 0, 0, 0, "car"))
		p.append(B(1.5, h2 * 0.8, 0.06, 0, 0.95 + h2 / 2.0, L * 0.2 + 0.02, "26323c", -35, 0, 0, "glass"))
		p.append(B(1.5, h2 * 0.8, 0.06, 0, 0.95 + h2 / 2.0, -L * 0.3 - 0.02, "26323c", 30, 0, 0, "glass"))
	for sd in [-1.0, 1.0]:
		p.append(B(0.05, h2 * 0.7, L * 0.42, sd * 0.82, 0.95 + h2 / 2.0, -L * 0.05, "26323c", 0, 0, 0, "glass"))
		for z in [L * 0.32, -L * 0.32]:
			p.append(C(0.33, 0.24, sd * 0.82, 0.33, z, "111111", 0, 0, 0, 90))
		p.append(B(0.3, 0.12, 0.04, sd * 0.6, 0.72, L / 2.0 + 0.01, "e8e8e0"))
		p.append(B(0.3, 0.1, 0.04, sd * 0.6, 0.72, -L / 2.0 - 0.01, "a01818"))
	p.append(B(0.52, 0.12, 0.02, 0, 0.5, -L / 2.0 - 0.02, "f2f2f2"))     # number plate
	return {"p": p, "t": "car", "lod": "mid", "ob": [["box", 0, 0, 1.95, L + 0.2, 1.5 if style != "van" else 2.2]]}


func _k_tractor(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "2f7a2f")
	var warm := float(_q(q, "warm", 48.0))                 # engine still warm (a tractor that just stopped)
	var p := [B(1.1, 0.9, 2.2, 0, 1.1, 0.6, col, 0, 0, 0, warm), B(1.2, 0.5, 1.4, 0, 0.9, -0.9, "3a3a3a"),
			C(0.06, 1.0, 0.35, 2.0, 1.4, "2a2a2a", 0, 0, 0, 0, 70.0), B(0.1, 0.1, 0.1, 0, 1.4, 1.72, "*fff4d8")]
	for sd in [-1.0, 1.0]:
		p.append(C(0.75, 0.45, sd * 0.85, 0.75, -0.9, "151515", 0, 0, 0, 90))
		p.append(C(0.4, 0.3, sd * 0.75, 0.42, 1.2, "151515", 0, 0, 0, 90))
		p.append(C(0.4, 0.46, sd * 0.85, 0.75, -0.9, "e8b21e", 0, 0, 0, 90))
		for z in [-0.35, -1.45]:
			p.append(B(0.05, 1.3, 0.05, sd * 0.55, 2.2, z, "1a1a1a"))
	p.append(B(1.3, 0.08, 1.3, 0, 2.88, -0.9, col))
	p.append(B(0.5, 0.12, 0.45, 0, 1.4, -0.9, "1a1a1a"))
	return {"p": p, "t": "car", "lod": "mid", "ob": [["box", 0, -0.1, 2.2, 3.8, 2.9]]}


func _k_food_truck(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "e8b21e")
	var p := [B(2.3, 2.6, 4.2, 0, 1.75, -0.8, col, 0, 0, 0, "car"), B(2.2, 1.6, 1.6, 0, 1.25, 2.1, col, 0, 0, 0, "car"),
			B(2.0, 0.8, 0.06, 0, 1.7, 2.92, "26323c", -15, 0, 0, "glass"), B(0.06, 1.0, 2.6, 1.17, 1.9, -0.8, "%ffe2b0", 0, 0, 0, "window"),
			B(0.06, 1.0, 2.8, 1.7, 2.65, -0.8, col, 0, 0, -60), B(0.5, 0.08, 2.6, 1.4, 1.35, -0.8, "c8c8c8"),
			C(0.08, 0.9, -0.6, 3.4, -2.2, "8a8a8a", 0, 0, 0, 0, 60.0), B(0.8, 0.5, 1.0, -0.5, 1.6, -1.6, "2a2a2a", 0, 0, 0, 65.0)]
	for z in [1.9, -2.2]:
		for sd in [-1.0, 1.0]:
			p.append(C(0.4, 0.25, sd * 1.0, 0.4, z, "111111", 0, 0, 0, 90))
	return {"p": p, "t": "car", "lod": "mid", "ob": [["box", 0, 0, 2.4, 6.0, 3.0]], "fx": [["smoke", -0.6, 3.9, -2.2]],
			"labels": [[str(_q(q, "text", "Snacks")), 1.21, 2.6, -0.8, 48, PI / 2.0, "c0392b"]], "lights": [[1.6, 2.4, -0.8]]}


func _k_rowboat(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 3.6))
	var col = _q(q, "col", "d8d8d0")
	var p := [B(1.1, 0.45, L * 0.8, 0, 0.22, -L * 0.1, col, 0, 0, 0, "caravan"), P(1.1, L * 0.25, 0.45, 0, 0.22, L * 0.38, col, 90, 0, 0, "caravan"),
			B(1.12, 0.06, L * 0.8, 0, 0.46, -L * 0.1, "6a4a2e"), B(1.0, 0.05, 0.25, 0, 0.35, 0.0, "8a6a48"), B(1.0, 0.05, 0.25, 0, 0.35, -L * 0.3, "8a6a48"),
			B(0.06, 0.04, 2.4, 0.35, 0.5, -0.2, "8a6a48", 0, 8, 0), B(0.06, 0.04, 2.4, -0.35, 0.5, -0.2, "8a6a48", 0, -8, 0)]
	return {"p": p, "t": "caravan", "lod": "small"}


func _k_pedalboat(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "f2c22e")
	var p := []
	for sd in [-0.65, 0.65]:
		p.append(C(0.32, 2.6, sd, 0.25, 0, col, 0, 90, 0, 0))
		p.append(S(0.32, 0.64, sd, 0.25, 1.3, col))
	p.append(B(1.6, 0.12, 2.0, 0, 0.55, -0.1, "f2f2f2"))
	p.append(B(1.3, 0.5, 0.12, 0, 0.85, -0.6, "f2f2f2", -15))
	p.append(B(0.5, 0.45, 0.6, 0, 0.6, -1.1, "2a6fb0"))
	p.append(B(1.2, 0.2, 0.06, 0, 0.75, 0.6, "c0392b"))
	return {"p": p, "t": "caravan", "lod": "small"}


func _k_sailboat(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 7.0))
	var mast := L * 1.3
	var p := [B(2.2, 0.8, L * 0.75, 0, 0.3, -L * 0.1, "f2f2f2", 0, 0, 0, "caravan"), P(2.2, L * 0.3, 0.8, 0, 0.3, L * 0.38, "f2f2f2", 90, 0, 0, "caravan"),
			B(2.25, 0.12, L * 0.75, 0, 0.55, -L * 0.1, "1f4a7a"), B(1.4, 0.55, 2.2, 0, 0.95, -L * 0.1, "e8e8e8"),
			C(0.07, mast, 0, 0.7 + mast / 2.0, L * 0.05, "c8c8cc", 0, 0, 0, 0, "metal"),
			C(0.05, L * 0.45, 0, 1.9, L * 0.05 - L * 0.22, "c8c8cc", 0, 90, 0, 0, "metal"),
			P(0.02, mast * 0.8, L * 0.42, 0, 1.95 + mast * 0.4, L * 0.05 - L * 0.21, "f5f2ea", 0, 90, 0, "tent"),
			ROD(Vector3(0, 0.7 + mast, L * 0.05), Vector3(0, 0.7, L * 0.48), 0.012, "9a9a9a")]
	return {"p": p, "t": "caravan", "lod": "big"}


func _k_buoy(q: Dictionary) -> Dictionary:
	return {"p": [S(0.35, 0.6, 0, 0.1, 0, _q(q, "col", "e85a1a")), C(0.05, 0.6, 0, 0.6, 0, "e85a1a")], "t": "caravan", "lod": "small"}


func _k_jetty(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 40.0))
	var w := float(_q(q, "w", 2.5))
	var h := float(_q(q, "h", 0.6))                       # deck above the origin (the water line)
	var p := []
	var n := int(L / 2.0)
	for i in range(n):                                     # planks in sections (little gaps between)
		p.append(B(w, 0.1, 1.94, 0, h, -1.0 - i * 2.0, "8a6a48", 0, 0, 0, "tree"))
	var k := 0
	var z := -0.5
	while z > -L:
		for sd in [-1.0, 1.0]:
			p.append(C(0.12, h + 2.8, sd * (w / 2.0 - 0.1), h - (h + 2.8) / 2.0 + 0.25, z, "5a4630", 0, 0, 0, 0, "tree"))
		if k % 3 == 1:
			p.append(C(0.1, 0.35, w / 2.0 - 0.15, h + 0.22, z, "3a3a3a", 0, 0, 0, 0, "stone"))        # bollard
		z -= 3.0
		k += 1
	for i in range(4):                                     # bathing ladder at the end
		p.append(B(0.5, 0.03, 0.06, w / 2.0 + 0.2, h - 0.3 - i * 0.3, -L + 0.5, "c8c8cc"))
	for dx in [-0.25, 0.25]:
		p.append(C(0.025, 1.6, w / 2.0 + 0.2 + dx, h - 0.4, -L + 0.5, "c8c8cc"))
	return {"p": p, "t": "tree", "lod": "big"}


func _k_pool(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 25.0))
	var dd := float(_q(q, "d", 12.5))
	var rim := 1.5
	var p := [B(w + 2 * rim, 0.25, rim, 0, 0.12, dd / 2.0 + rim / 2.0, "d8d2c4", 0, 0, 0, "stone"),
			B(w + 2 * rim, 0.25, rim, 0, 0.12, -dd / 2.0 - rim / 2.0, "d8d2c4", 0, 0, 0, "stone"),
			B(rim, 0.25, dd, w / 2.0 + rim / 2.0, 0.12, 0, "d8d2c4", 0, 0, 0, "stone"),
			B(rim, 0.25, dd, -w / 2.0 - rim / 2.0, 0.12, 0, "d8d2c4", 0, 0, 0, "stone"),
			B(w, 0.04, dd, 0, 0.12, 0, "3aa8d8", 0, 0, 0, float(_q(q, "water_c", 26.0)))]   # heated water: 26 °C
	for sd in [-1.0, 1.0]:                                 # two ladders
		for dx in [-0.3, 0.3]:
			p.append(TO(0.28, 0.32, w * 0.3 * sd + dx, 0.55, dd / 2.0 - 0.05, "c8c8cc", 90, 90, 0))
			p.append(C(0.025, 1.0, w * 0.3 * sd + dx, 0.0, dd / 2.0 - 0.3, "c8c8cc"))
	for i in range(5):                                     # starting blocks and lane ropes
		p.append(B(0.6, 0.7, 0.7, -w / 2.0 - rim / 2.0, 0.6, -dd / 2.0 + dd * (i + 0.5) / 5.0, "f2f2f2", 0, 0, 0, "stone"))
		if i < 4:
			p.append(B(w, 0.06, 0.06, 0, 0.16, -dd / 2.0 + dd * (i + 1) / 5.0, "c0392b" if i % 2 == 0 else "f2f2f2"))
	return {"p": p, "t": "stone", "lod": "big", "ob": [["box", 0, 0, w, dd, 0.3]]}


func _k_fountain(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 2.0))
	var p := [C(r, 0.6, 0, 0.3, 0, "9a958d", 0, 0, 0, 0, "stone"), C(r - 0.25, 0.05, 0, 0.58, 0, "3a8ab0", 0, 0, 0, 0, "pond"),
			C(0.25, 1.8, 0, 0.9, 0, "9a958d", 0, 0, 0, 0, "stone"), C(0.7, 0.2, 0, 1.8, 0, "9a958d", 0.3, 0, 0, 0, "stone"),
			C(0.03, 1.0, 0.4, 1.4, 0, "a8d8f0", 0, 0, 0, 30, "pond"), C(0.03, 1.0, -0.4, 1.4, 0, "a8d8f0", 0, 0, 0, -30, "pond")]
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["circ", 0, 0, r + 0.1, 0.6]]}


func _k_reeds(q: Dictionary) -> Dictionary:
	var n := int(_q(q, "n", 12))
	var p := []
	var rng := RandomNumberGenerator.new()
	rng.seed = int(_q(q, "seed", 3))
	for i in range(n):
		var h := rng.randf_range(1.1, 2.0)
		var x := rng.randf_range(-1.2, 1.2)
		var z := rng.randf_range(-1.2, 1.2)
		p.append(C(0.015, h, x, h / 2.0, z, "6a7a3a", 0.03, rng.randf_range(-8, 8), 0, rng.randf_range(-8, 8), "tree"))
		if i % 3 == 0:
			p.append(C(0.035, 0.22, x, h + 0.05, z, "5a3a22", 0, 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "small", "low": true}


func _k_lifeguard(_q: Dictionary) -> Dictionary:
	var p := [B(0.8, 0.08, 0.8, 0, 1.8, 0, "f2f2f2"), B(0.8, 0.8, 0.08, 0, 2.2, -0.4, "f2f2f2"),
			B(0.8, 0.5, 0.08, 0, 2.05, 0.4, "c0392b"), C(0.025, 1.4, 0.3, 2.5, -0.3, "c8c8cc"), K(0.8, 0.4, 0.3, 3.25, -0.3, "c0392b")]
	for x in [-0.4, 0.4]:
		for z in [-0.4, 0.4]:
			p.append(B(0.08, 1.85, 0.08, x * 1.3, 0.9, z * 1.3, "f2f2f2", z * 14, 0, -x * 14))
	for i in range(5):
		p.append(B(0.7, 0.04, 0.06, 0, 0.3 + i * 0.32, 0.85 - i * 0.08, "f2f2f2"))
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", 0, 0, 1.2, 1.2, 2.0]]}


func _k_lounger(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "2a6fb0")
	var p := [B(0.65, 0.05, 1.3, 0, 0.32, 0.25, col, 0, 0, 0, "tent"), B(0.65, 0.05, 0.8, 0, 0.55, -0.6, col, 35, 0, 0, "tent")]
	for x in [-0.3, 0.3]:
		for z in [-0.4, 0.8]:
			p.append(B(0.04, 0.3, 0.04, x, 0.15, z, "c8c8cc"))
	return {"p": p, "t": "tent", "lod": "small"}


func _k_parasol(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 1.5))
	var col = _q(q, "col", "d8392b")
	return {"p": [C(0.025, 2.3, 0, 1.15, 0, "dddddd"), K(r, 0.5, 0, 2.25, 0, col, 0, 0, 0, "tent"), C(0.3, 0.08, 0, 0.04, 0, "444444")],
			"t": "tent", "lod": "small", "ob": [["circ", 0, 0, 0.25, 2.3]]}


func _k_shower(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.05, 2.3, 0, 1.15, 0, "c8c8cc"), C(0.15, 0.05, 0.25, 2.25, 0, "c8c8cc"), B(0.6, 0.05, 0.6, 0, 0.03, 0, "8a8a86")],
			"t": "stone", "lod": "small", "ob": [["circ", 0, 0, 0.12, 2.3]]}


# ---- play -------------------------------------------------------------------------------------------------------------
func _k_swing(q: Dictionary) -> Dictionary:
	var n := int(_q(q, "seats", 2))
	var w := 1.4 * n + 0.6
	var p := [C(0.06, w, 0, 2.4, 0, "8a6a48", 0, 0, 0, 90, "tree")]
	for x in [-w / 2.0, w / 2.0]:
		for sd in [-1.0, 1.0]:
			p.append(C(0.06, 2.6, x, 1.2, sd * 0.55, "8a6a48", 0, sd * -12, 0, 0, "tree"))
	for i in range(n):
		var x2 := -w / 2.0 + 0.3 + 1.4 * (i + 0.5)
		p.append(B(0.5, 0.05, 0.22, x2, 0.5, 0, "c0392b" if i % 2 == 0 else "2a6fb0"))
		for dx in [-0.22, 0.22]:
			p.append(B(0.015, 1.9, 0.015, x2 + dx, 1.45, 0, "9a9a9a"))
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0, w + 0.3, 1.4, 2.4, true]]}


func _k_slide(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 2.0))
	var p := [B(1.2, 0.08, 1.2, 0, h, 0, "8a6a48", 0, 0, 0, "tree"), P(1.5, 0.8, 1.5, 0, h + 1.9, 0, "c0392b", 0, 0, 0, "tent")]
	for x in [-0.55, 0.55]:
		for z in [-0.55, 0.55]:
			p.append(B(0.1, h + 1.5, 0.1, x, (h + 1.5) / 2.0, z, "8a6a48", 0, 0, 0, "tree"))
	var L := h * 1.9
	p.append(B(0.6, 0.06, L, 0, h / 2.0 + 0.05, 0.6 + L * 0.42, "2ab07a", rad_to_deg(atan2(h, L * 0.85)), 0, 0, "caravan"))
	for sd in [-0.3, 0.3]:
		p.append(B(0.04, 0.2, L, sd, h / 2.0 + 0.15, 0.6 + L * 0.42, "2ab07a", rad_to_deg(atan2(h, L * 0.85)), 0, 0, "caravan"))
	for i in range(int(h / 0.3)):
		p.append(B(0.6, 0.04, 0.06, 0, 0.3 + i * 0.3, -0.75 - i * 0.05, "8a6a48"))
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0.8, 1.4, 3.5, h + 1.5]]}


func _k_sandpit(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 4.0))
	var p := [B(w, 0.06, w, 0, 0.12, 0, "d8c08a", 0, 0, 0, "road")]
	for i in range(4):
		var a := PI / 2.0 * i
		p.append(B(w, 0.3, 0.15, sin(a) * w / 2.0, 0.15, cos(a) * w / 2.0, "8a6a48", 0, rad_to_deg(a), 0, "tree"))
	p.append(B(0.25, 0.2, 0.18, 0.5, 0.25, 0.3, "e8b21e"))
	return {"p": p, "t": "tree", "lod": "small"}


func _k_climbing(_q: Dictionary) -> Dictionary:
	var p := []
	for x in [-1.0, 0.0, 1.0]:
		for z in [-1.0, 0.0, 1.0]:
			p.append(C(0.04, 2.0, x, 1.0, z, "2a6fb0", 0, 0, 0, 0, "metal"))
	for y in [0.7, 1.4, 2.0]:
		for z in [-1.0, 0.0, 1.0]:
			p.append(C(0.035, 2.0, 0, y, z, "e8b21e", 0, 0, 0, 90, "metal"))
		for x in [-1.0, 1.0]:
			p.append(C(0.035, 2.0, x, y, 0, "e8b21e", 0, 90, 0, 90, "metal"))
	return {"p": p, "t": "stone", "lod": "small", "ob": [["box", 0, 0, 2.1, 2.1, 2.0, true]]}


func _k_seesaw(_q: Dictionary) -> Dictionary:
	return {"p": [B(0.3, 0.5, 0.3, 0, 0.25, 0, "8a6a48", 0, 0, 0, "tree"), B(3.2, 0.08, 0.3, 0, 0.55, 0, "c0392b", 0, 0, 8),
			B(0.05, 0.3, 0.3, 1.3, 0.85, 0, "e8b21e"), B(0.05, 0.3, 0.3, -1.3, 0.45, 0, "e8b21e")], "t": "tree", "lod": "small"}


func _k_minigolf(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 8.0))
	var style := str(_q(q, "style", "straight"))
	var p := [B(1.3, 0.2, L, 0, 0.1, 0, "9a958d", 0, 0, 0, "stone"), B(0.9, 0.04, L - 0.2, 0, 0.21, 0, "2f8a3a", 0, 0, 0, "road"),
			B(0.1, 0.12, L, 0.5, 0.26, 0, "f2f2f2"), B(0.1, 0.12, L, -0.5, 0.26, 0, "f2f2f2"),
			C(0.06, 0.02, 0, 0.24, -L / 2.0 + 0.5, "111111"), C(0.008, 0.8, 0.05, 0.6, -L / 2.0 + 0.5, "f2f2f2"),
			B(0.25, 0.15, 0.01, 0.17, 0.92, -L / 2.0 + 0.5, "c0392b")]
	match style:
		"bump":
			p.append(P(0.9, 0.25, 1.4, 0, 0.35, 0, "2f8a3a", 0, 90, 0))
		"loop":
			p.append(TO(0.55, 0.62, 0, 0.8, 0, "2a6fb0", 0, 90, 0))
		"windmill":
			p.append(B(1.0, 1.6, 0.8, 0, 1.0, 0.5, "c0392b"))
			p.append(P(1.1, 0.6, 0.9, 0, 2.1, 0.5, "4a3a32"))
			for a in [0.0, 90.0]:
				p.append(B(0.15, 1.8, 0.04, 0, 1.4, 0.95, "e8e0cc", 0, 0, a + 45.0))
		"gate":
			for x in [-0.25, 0.25]:
				p.append(B(0.2, 0.25, 0.2, x, 0.36, 0, "e8b21e"))
		"bridge":
			p.append(B(0.5, 0.06, 2.0, 0, 0.45, 0, "8a6a48", 12))
	p.append(B(0.08, 0.15, 0.04, 0.5, 0.42, L / 2.0 - 0.3, "1a1a1a"))
	var lb := []
	if _q(q, "nr", "") != "":
		lb.append([str(q["nr"]), 0.5, 0.48, L / 2.0 - 0.27, 24, 0.0, "f2f2f2"])
	return {"p": p, "t": "stone", "lod": "small", "labels": lb, "ob": [["box", 0, 0, 1.3, L, 0.3, true]]}


# ---- ways and borders --------------------------------------------------------------------------------------------------
func _k_fence(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 2.5))
	var h := float(_q(q, "h", 1.2))
	var style := str(_q(q, "style", "wood"))
	var p := []
	match style:
		"metal", "pool":                                   # mesh panel (pool: higher, green)
			var col := "2f5a3a" if style == "pool" else "8a8f96"
			p.append(B(0.05, h, 0.05, -L / 2.0, h / 2.0, 0, col, 0, 0, 0, "metal"))
			p.append(B(L, 0.04, 0.04, 0, h - 0.05, 0, col, 0, 0, 0, "metal"))
			p.append(B(L, 0.04, 0.04, 0, 0.08, 0, col, 0, 0, 0, "metal"))
			for i in range(int(L / 0.2)):
				p.append(B(0.012, h - 0.1, 0.012, -L / 2.0 + 0.1 + i * 0.2, h / 2.0, 0, col, 0, 0, 0, "metal"))
		"picket":
			p.append(B(L, 0.06, 0.03, 0, h * 0.75, 0, "f2f2f2"))
			p.append(B(L, 0.06, 0.03, 0, h * 0.3, 0, "f2f2f2"))
			for i in range(int(L / 0.15)):
				p.append(B(0.08, h, 0.02, -L / 2.0 + 0.075 + i * 0.15, h / 2.0, 0.025, "f2f2f2"))
		_:                                                 # wooden post-and-rail (pasture)
			p.append(B(0.12, h, 0.12, -L / 2.0, h / 2.0, 0, "6a4a2e", 0, 0, 0, "tree"))
			p.append(B(L, 0.1, 0.05, 0, h * 0.85, 0, "8a6a48", 0, 0, 0, "tree"))
			p.append(B(L, 0.1, 0.05, 0, h * 0.45, 0, "8a6a48", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree" if style in ["wood", "picket"] else "metal", "lod": "small" if h < 1.5 else "mid",
			"ob": [["box", 0, 0, L, 0.2, h, style in ["wood", "picket"]]]}


func _k_hedge(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 2.5))
	var h := float(_q(q, "h", 1.6))
	var col = _q(q, "col", "2f5a24")
	var p := [B(L, h, 0.9, 0, h / 2.0, 0, col, 0, 0, 0, "tree"), S(0.55, 0.9, -L * 0.25, h - 0.05, 0.1, cc(col).lightened(0.08), "tree"),
			S(0.5, 0.8, L * 0.25, h - 0.08, -0.1, col, "tree")]
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["box", 0, 0, L, 1.0, h]]}


func _k_wall(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 3.0))
	var h := float(_q(q, "h", 1.0))
	var t := float(_q(q, "thick", 0.45))
	var col = _q(q, "col", "8a8378")
	return {"p": [B(L, h, t, 0, h / 2.0 - float(_q(q, "sink", 0.0)), 0, col, 0, 0, 0, "stone"), B(L, 0.08, t + 0.1, 0, h + 0.04 - float(_q(q, "sink", 0.0)), 0, "6e6860", 0, 0, 0, "stone")],
			"t": "stone", "lod": "mid", "ob": [["box", 0, 0, L, t + 0.1, h]]}


func _k_stairs(q: Dictionary) -> Dictionary:
	var n := int(_q(q, "n", 10))
	var w := float(_q(q, "w", 2.0))
	var rise := float(_q(q, "rise", 0.17))
	var run := float(_q(q, "run", 0.32))
	var p := []
	for i in range(n):                                    # going up towards -z
		p.append(B(w, rise * (i + 1), run, 0, rise * (i + 1) / 2.0, -run * (i + 0.5), "a8a296", 0, 0, 0, "stone"))
	var L := Vector2(run * n, rise * n).length()
	var ang := rad_to_deg(atan2(rise * n, run * n))
	for sd in [-1.0, 1.0]:
		p.append(B(0.05, 0.05, L, sd * (w / 2.0 + 0.05), rise * n / 2.0 + 0.9, -run * n / 2.0, "4a4a4e", ang, 0, 0, "metal"))
		for k in range(3):
			var f := (k + 0.5) / 3.0
			p.append(B(0.05, 0.9, 0.05, sd * (w / 2.0 + 0.05), rise * n * f + 0.45, -run * n * f, "4a4a4e", 0, 0, 0, "metal"))
	return {"p": p, "t": "stone", "lod": "mid"}


func _k_lamp(q: Dictionary) -> Dictionary:
	var style := str(_q(q, "style", "lantern"))
	var p := []
	var lt := []
	match style:
		"path":                                            # bollard light 1 m
			p = [C(0.1, 0.9, 0, 0.45, 0, "3a3a3e", 0, 0, 0, 0, "metal"), C(0.11, 0.12, 0, 0.95, 0, "*fff0c8", 0, 0, 0, 0, 40.0)]
			lt = [[0, 0.95, 0]]
		"street":
			p = [C(0.07, 6.0, 0, 3.0, 0, "5a5f66", 0.1, 0, 0, 0, "metal"), B(1.4, 0.08, 0.08, 0.7, 5.95, 0, "5a5f66", 0, 0, 0, "metal"),
				B(0.55, 0.12, 0.3, 1.3, 5.9, 0, "3a3a3e", 0, 0, 0, 40.0), B(0.5, 0.03, 0.26, 1.3, 5.83, 0, "*fff0c8")]
			lt = [[1.3, 5.7, 0]]
		_:                                                 # lantern on a post (3.5 m)
			p = [C(0.06, 3.3, 0, 1.65, 0, "2a2d32", 0.09, 0, 0, 0, "metal"), C(0.15, 0.3, 0, 0.15, 0, "2a2d32", 0, 0, 0, 0, "metal"),
				B(0.32, 0.45, 0.32, 0, 3.5, 0, "*ffe2a8"), K(0.3, 0.25, 0, 3.85, 0, "2a2d32", 0, 0, 0, 40.0)]
			lt = [[0, 3.4, 0]]
	return {"p": p, "t": "metal", "lod": "mid" if style != "path" else "small", "ob": [["circ", 0, 0, 0.18, 3.0]], "lights": lt}


func _k_bench(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "8a5a32")
	return {"p": [B(1.8, 0.06, 0.45, 0, 0.45, 0, col, 0, 0, 0, "tree"), B(1.8, 0.4, 0.05, 0, 0.75, -0.22, col, -12, 0, 0, "tree"),
			B(0.06, 0.45, 0.5, -0.8, 0.22, 0, "333333"), B(0.06, 0.45, 0.5, 0.8, 0.22, 0, "333333")],
			"t": "tree", "lod": "small", "ob": [["box", 0, 0, 1.8, 0.6, 0.8]]}


func _k_bin(q: Dictionary) -> Dictionary:
	var style := str(_q(q, "style", "bin"))
	if style == "recycle":                                 # three containers (glass, PET, rest)
		var p := []
		var cols := ["2e7d32", "2a6fb0", "5a5a5a"]
		for i in range(3):
			p.append(B(1.0, 1.3, 1.0, -1.1 + i * 1.1, 0.65, 0, cols[i]))
			p.append(B(1.02, 0.08, 1.02, -1.1 + i * 1.1, 1.34, 0, "3a3a3a"))
		return {"p": p, "t": "caravan", "lod": "small", "ob": [["box", 0, 0, 3.3, 1.1, 1.4]]}
	return {"p": [C(0.25, 0.85, 0, 0.42, 0, _q(q, "col", "2e7d32"), 0, 0, 0, 0, "caravan"), C(0.27, 0.06, 0, 0.87, 0, "3a3a3a")],
			"t": "caravan", "lod": "small", "ob": [["circ", 0, 0, 0.3, 0.9]]}


func _k_signpost(q: Dictionary) -> Dictionary:
	var arms: Array = _q(q, "arms", ["Weg"])
	var p := [C(0.05, 2.4, 0, 1.2, 0, "8a8a8a", 0, 0, 0, 0, "metal")]
	var lb := []
	for i in range(arms.size()):
		var y := 2.2 - i * 0.28
		var dirx := 1.0 if i % 2 == 0 else -1.0
		p.append(B(0.9, 0.2, 0.03, dirx * 0.48, y, 0, "e9c11b"))
		p.append(P(0.2, 0.2, 0.03, dirx * 0.99, y, 0, "e9c11b", 0, 0, -90.0 * dirx))
		lb.append([str(arms[i]), dirx * 0.48, y, 0.02, 20, 0.0, "1a1a1a"])
	return {"p": p, "t": "metal", "lod": "small", "ob": [["circ", 0, 0, 0.1, 2.4]], "labels": lb}


func _k_info_board(q: Dictionary) -> Dictionary:
	var p := [B(0.12, 2.2, 0.12, -0.9, 1.1, 0, "6a4a2e", 0, 0, 0, "tree"), B(0.12, 2.2, 0.12, 0.9, 1.1, 0, "6a4a2e", 0, 0, 0, "tree"),
			B(1.8, 1.1, 0.06, 0, 1.45, 0, "f2ead8"), P(2.2, 0.45, 0.6, 0, 2.35, 0, "4a3a32", 0, 90, 0)]
	p[3] = P(0.6, 0.45, 2.2, 0, 2.35, 0, "4a3a32", 0, 90, 0)
	return {"p": p, "t": "tree", "lod": "small", "ob": [["box", 0, 0, 2.0, 0.4, 2.4]],
			"labels": [[str(_q(q, "text", "Info")), 0, 1.75, 0.04, 40, 0.0, "1a1a1a"]]}


func _k_crowd_barrier(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 2.5))
	var p := [B(L, 0.04, 0.04, 0, 1.05, 0, "b0b4ba", 0, 0, 0, "metal"), B(L, 0.04, 0.04, 0, 0.2, 0, "b0b4ba", 0, 0, 0, "metal"),
			B(0.04, 1.05, 0.04, -L / 2.0, 0.6, 0, "b0b4ba", 0, 0, 0, "metal"), B(0.08, 0.05, 0.7, -L / 2.0 + 0.1, 0.03, 0, "8a8f96")]
	for i in range(int(L / 0.12)):
		p.append(B(0.015, 0.85, 0.015, -L / 2.0 + 0.06 + i * 0.12, 0.62, 0, "b0b4ba", 0, 0, 0, "metal"))
	return {"p": p, "t": "metal", "lod": "small", "ob": [["box", 0, 0, L, 0.3, 1.1]]}


func _k_parking_lines(q: Dictionary) -> Dictionary:
	var n := int(_q(q, "n", 10))
	var sp := float(_q(q, "spacing", 2.6))
	var L := float(_q(q, "len", 5.0))
	var p := []
	for i in range(n + 1):
		p.append(B(0.12, 0.012, L, -n * sp / 2.0 + i * sp, 0.03, 0, "f2f2f2", 0, 0, 0, "road"))
	p.append(B(n * sp, 0.012, 0.12, 0, 0.03, -L / 2.0, "f2f2f2", 0, 0, 0, "road"))
	return {"p": p, "t": "road", "lod": "mid"}


func _k_bike_rack(q: Dictionary) -> Dictionary:
	var n := int(_q(q, "n", 5))
	var p := []
	for i in range(n):
		p.append(TO(0.36, 0.4, -n * 0.4 + 0.4 + i * 0.8, 0.0, 0, "9a9a9a", 0, 0, 90))
	return {"p": p, "t": "metal", "lod": "small", "ob": [["box", 0, 0, n * 0.8, 0.3, 0.8, true]]}


func _k_footbridge(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 6.0))
	var w := float(_q(q, "w", 1.8))
	var p := [B(w, 0.15, L, 0, 0.35, 0, "8a6a48", 0, 0, 0, "tree"), B(w + 0.4, 0.6, 0.8, 0, 0.0, L / 2.0, "8a857d", 0, 0, 0, "stone"),
			B(w + 0.4, 0.6, 0.8, 0, 0.0, -L / 2.0, "8a857d", 0, 0, 0, "stone")]
	for sd in [-1.0, 1.0]:
		p.append(B(0.07, 0.07, L, sd * w / 2.0, 1.35, 0, "6a4a2e", 0, 0, 0, "tree"))
		for i in range(int(L / 1.5) + 1):
			p.append(B(0.09, 1.0, 0.09, sd * w / 2.0, 0.9, -L / 2.0 + i * L / int(L / 1.5), "6a4a2e", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "mid"}


func _k_rope_bridge(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 20.0))
	var w := float(_q(q, "w", 1.2))
	var sag := float(_q(q, "sag", 1.0))
	var p := []
	var n := int(L / 0.5)
	var prev_l := Vector3.ZERO
	for i in range(n + 1):
		var t := float(i) / n
		var z := -L / 2.0 + t * L
		var y := 1.0 - sag * 4.0 * t * (1.0 - t)
		if i < n:
			p.append(B(w, 0.05, 0.3, 0, y, z + 0.25, "7a5a3a", 0, 0, 0, "tree"))
		for sd in [-1.0, 1.0]:
			var hand := Vector3(sd * w / 2.0, y + 1.0, z)
			if i > 0:
				p.append(ROD(Vector3(sd * w / 2.0, prev_l.y, prev_l.z), hand, 0.025, "c8b88a"))
			if i % 4 == 0:
				p.append(B(0.015, 1.0, 0.015, sd * w / 2.0, y + 0.5, z, "c8b88a"))
		prev_l = Vector3(0, y + 1.0, z)
	for z in [-L / 2.0 - 0.3, L / 2.0 + 0.3]:
		for sd in [-1.0, 1.0]:
			p.append(B(0.2, 2.6, 0.2, sd * (w / 2.0 + 0.1), 1.0, z, "5a4630", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "mid"}


func _k_viewpoint(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 5.0))
	var dd := float(_q(q, "d", 4.0))
	var h := float(_q(q, "h", 2.5))
	var p := [B(w, 0.2, dd, 0, h, 0, "8a6a48", 0, 0, 0, "tree")]
	for x in [-w / 2.0 + 0.2, w / 2.0 - 0.2]:
		for z in [-dd / 2.0 + 0.2, dd / 2.0 - 0.2]:
			p.append(B(0.25, h + 1.1, 0.25, x, (h + 1.1) / 2.0, z, "6a4a2e", 0, 0, 0, "tree"))
	for sd in [-1.0, 1.0]:
		p.append(B(w, 0.08, 0.08, 0, h + 1.05, sd * dd / 2.0, "6a4a2e", 0, 0, 0, "tree"))
		p.append(B(0.08, 0.08, dd, sd * w / 2.0, h + 1.05, 0, "6a4a2e", 0, 0, 0, "tree"))
	for i in range(7):                                     # stairs from the back
		p.append(B(1.0, 0.06, 0.3, w / 2.0 - 0.6, 0.35 * (i + 1), dd / 2.0 + 2.1 - i * 0.32, "8a6a48", 0, 0, 0, "tree"))
	p.append(C(0.05, 1.1, -w / 2.0 + 0.8, h + 0.65, -dd / 2.0 + 0.5, "3a3a3e"))      # telescope
	p.append(C(0.09, 0.45, -w / 2.0 + 0.8, h + 1.25, -dd / 2.0 + 0.5, "2a6a3a", 0, 70, 0, 0))
	p.append(B(1.6, 0.06, 0.4, 0, h + 0.55, 0.4, "8a5a32", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "big", "ob": [["box", 0, 0, w, dd, h + 1.1]]}


func _k_hochsitz(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 4.0))
	var p := [B(1.5, 0.1, 1.5, 0, h, 0, "6a4a2e", 0, 0, 0, "tree"), B(1.5, 1.0, 0.06, 0, h + 0.55, -0.72, "5a3e26", 0, 0, 0, "tree"),
			B(0.06, 1.0, 1.5, 0.72, h + 0.55, 0, "5a3e26", 0, 0, 0, "tree"), B(0.06, 1.0, 1.5, -0.72, h + 0.55, 0, "5a3e26", 0, 0, 0, "tree"),
			B(1.5, 0.45, 0.06, 0, h + 0.25, 0.72, "5a3e26", 0, 0, 0, "tree"), P(1.9, 0.6, 1.9, 0, h + 1.85, 0, "3a3a2e", 0, 90, 0)]
	for x in [-0.7, 0.7]:
		for z in [-0.7, 0.7]:
			p.append(C(0.08, h + 1.6, x * 1.15, (h + 1.6) / 2.0, z * 1.15, "5a4630", 0, z * 6, 0, -x * 6, "tree"))
	var L := h * 1.15
	for sd in [-0.3, 0.3]:
		p.append(B(0.07, L, 0.07, sd, h / 2.0, 0.72 + h * 0.28, "6a4a2e", -15, 0, 0, "tree"))
	for i in range(int(h / 0.35)):
		p.append(B(0.6, 0.05, 0.05, 0, 0.3 + i * 0.35, 0.72 + h * 0.56 - (0.3 + i * 0.35) * 0.27, "6a4a2e", 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "big", "ob": [["box", 0, 0, 1.8, 1.8, h + 1.5]]}


func _k_rock(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 0.8))
	return {"p": [S(r, r * 1.3, 0, r * 0.35, 0, "7a7670", "stone"), S(r * 0.6, r * 0.8, r * 0.6, r * 0.25, r * 0.3, "6e6a64", "stone")],
			"t": "stone", "lod": "mid", "ob": [["circ", 0, 0, r, r]]}


# ---- farm ---------------------------------------------------------------------------------------------------------------
func _k_haybale(q: Dictionary) -> Dictionary:
	if str(_q(q, "style", "round")) == "square":
		return {"p": [B(1.2, 0.5, 0.5, 0, 0.25, 0, "d8b85a", 0, 0, 0, "tree"), B(1.21, 0.02, 0.51, 0, 0.3, 0, "c8a84a")], "t": "tree", "lod": "small", "ob": [["box", 0, 0, 1.2, 0.5, 0.5]]}
	var col = "f0f0ea" if bool(_q(q, "wrapped", false)) else "d8b85a"
	return {"p": [C(0.75, 1.2, 0, 0.75, 0, col, 0, 0, 0, 90, "tree")], "t": "tree", "lod": "mid", "ob": [["circ", 0, 0, 0.8, 1.5]]}


func _k_field(q: Dictionary) -> Dictionary:
	var w := float(_q(q, "w", 30.0))
	var dd := float(_q(q, "d", 20.0))
	var crop := str(_q(q, "crop", "wheat"))
	var col: String = {"wheat": "c8a84a", "corn": "4a8a2a", "potato": "3f6f2a", "sunflower": "e8b21e"}.get(crop, "c8a84a")
	var h: float = {"wheat": 0.9, "corn": 2.2, "potato": 0.5, "sunflower": 1.6}.get(crop, 0.9)
	var p := [B(w, 0.04, dd, 0, 0.02, 0, "5a4630", 0, 0, 0, "road")]
	var n := mini(int(dd / 1.0), 30)
	for i in range(n):
		p.append(B(w, h, 0.45, 0, h / 2.0, -dd / 2.0 + dd * (i + 0.5) / n, col, 0, 0, 0, "tree"))
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["box", 0, 0, w, dd, h, crop != "corn"]]}


func _k_coop(_q: Dictionary) -> Dictionary:
	var p := [B(2.0, 1.2, 1.5, 0, 1.1, 0, "a0522d"), P(2.3, 0.6, 1.8, 0, 2.0, 0, "5d4037", 0, 90, 0),
			B(0.4, 0.3, 1.1, 0.4, 0.3, 1.1, "8d6e63", -30), B(0.35, 0.35, 0.03, 0.4, 0.95, 0.76, "1a1a1a")]
	p[1] = P(1.8, 0.6, 2.3, 0, 2.0, 0, "5d4037", 0, 90, 0)
	for x in [-0.9, 0.9]:
		for z in [-0.65, 0.65]:
			p.append(B(0.08, 0.5, 0.08, x, 0.25, z, "6d4c41"))
	return {"p": p, "t": "caravan", "lod": "mid", "ob": [["box", 0, 0, 2.1, 1.6, 2.2]]}


func _k_tree(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "3a6a2a")
	return {"p": [C(0.18, 3.0, 0, 1.5, 0, "4a3624", 0.26, 0, 0, 0, "tree"), S(2.2, 3.4, 0, 4.4, 0, col, "tree"),
			S(1.5, 2.4, 0.9, 3.6, 0.5, cc(col).darkened(0.1), "tree")], "t": "tree", "lod": "big", "low": true,
			"ob": [["circ", 0, 0, 0.32, 6.0]]}


func _k_conifer(q: Dictionary) -> Dictionary:
	var col = _q(q, "col", "24452a")
	return {"p": [C(0.12, 2.0, 0, 1.0, 0, "4a3624", 0.24, 0, 0, 0, "tree"), K(2.2, 4.6, 0, 3.6, 0, col, 0, 0, 0, "tree"),
			K(1.4, 3.6, 0, 6.2, 0, cc(col).darkened(0.08), 0, 0, 0, "tree")], "t": "tree", "lod": "big", "low": true,
			"ob": [["circ", 0, 0, 0.3, 8.0]]}


func _k_orchard_tree(q: Dictionary) -> Dictionary:
	var fruit = _q(q, "fruit", "c0392b")
	var p := [C(0.1, 1.6, 0, 0.8, 0, "5a3d24", 0.14, 0, 0, 0, "tree"), S(1.3, 1.8, 0, 2.3, 0, "3d7a30", "tree"),
			S(0.8, 1.2, 0.6, 2.0, 0.4, "47873a", "tree")]
	for i in range(8):
		var a := TAU * i / 8.0
		p.append(S(0.06, 0.12, cos(a) * 1.15, 1.9 + (i % 3) * 0.35, sin(a) * 1.15, fruit, "tree"))
	return {"p": p, "t": "tree", "lod": "mid", "ob": [["circ", 0, 0, 0.25, 3.0]]}


# ---- animals (own nodes: the head nods while eating; warm in the thermal picture) ------------------------------------------
# Wärme: Oberfläche des Fells/Gefieders, nicht Körperkern - Rinder 28–33 °C im Wärmebild (Infrarot-Thermografie an Milchkühen,
# z. B. Montanholi et al. 2008, J. Therm. Biol.), Ziegen/Schafe mit dichtem Fell etwas kühler, Hühner am Kopf/Kamm wärmer.
func _k_cow(q: Dictionary) -> Dictionary:
	var c1 = _q(q, "col", "f2f0ea")
	var c2 = _q(q, "spots", "2a2420")
	var p := [B(1.6, 0.8, 0.7, 0, 1.05, 0, c1), B(0.5, 0.5, 0.72, 0.3, 1.15, 0, c2), B(0.4, 0.4, 0.71, -0.45, 1.0, 0, c2),
			B(0.08, 0.6, 0.08, -0.8, 0.95, 0, c1, 0, 0, -20),
			B(0.5, 0.35, 0.3, 1.05, 1.45, 0, c1, 0, 0, 0, null, "head"), B(0.2, 0.22, 0.28, 1.32, 1.38, 0, "e8b8a8", 0, 0, 0, null, "head"),
			C(0.03, 0.18, 0.95, 1.65, 0.12, "e8e0cc", 0, 0, 0, 0, null, "head"), C(0.03, 0.18, 0.95, 1.65, -0.12, "e8e0cc", 0, 0, 0, 0, null, "head"),
			B(0.08, 0.15, 0.18, 0.92, 1.55, 0.2, c2, 0, 0, 0, null, "head"), B(0.08, 0.15, 0.18, 0.92, 1.55, -0.2, c2, 0, 0, 0, null, "head")]
	for x in [0.6, -0.6]:
		for z in [0.22, -0.22]:
			p.append(B(0.14, 0.75, 0.14, x, 0.37, z, c1))
	p.append(S(0.15, 0.15, -0.3, 0.68, 0, "e8b8a8"))
	return {"p": p, "t": 31.0, "node": true, "piv": {"head": [0.8, 1.4, 0]}, "nod": 0.6, "ob": [["box", 0, 0, 2.2, 0.8, 1.5]]}


func _k_goat(q: Dictionary) -> Dictionary:
	var c1 = _q(q, "col", "c8b8a0")
	var p := [B(0.8, 0.4, 0.35, 0, 0.62, 0, c1), B(0.25, 0.25, 0.18, 0.5, 0.88, 0, c1, 0, 0, 20, null, "head"),
			K(0.03, 0.2, 0.5, 1.08, 0.06, "4a4030", -10, 0, 25, null, "head"), K(0.03, 0.2, 0.5, 1.08, -0.06, "4a4030", 10, 0, 25, null, "head"),
			B(0.06, 0.12, 0.04, 0.62, 0.72, 0, "f2f2f2", 0, 0, 0, null, "head")]
	for x in [0.3, -0.3]:
		for z in [0.12, -0.12]:
			p.append(B(0.07, 0.45, 0.07, x, 0.22, z, c1))
	p.append(B(0.12, 0.06, 0.05, -0.43, 0.82, 0, c1, 0, 0, 40))
	return {"p": p, "t": 29.0, "node": true, "piv": {"head": [0.42, 0.75, 0]}, "nod": 0.7, "ob": [["circ", 0, 0, 0.5, 1.0]]}


func _k_sheep(q: Dictionary) -> Dictionary:
	var c1 = _q(q, "col", "ece6d8")
	var p := [S(0.45, 0.6, 0, 0.7, 0, c1), B(0.25, 0.22, 0.2, 0.5, 0.82, 0, "2a2420", 0, 0, 0, null, "head")]
	for x in [0.25, -0.25]:
		for z in [0.13, -0.13]:
			p.append(B(0.07, 0.42, 0.07, x, 0.21, z, "2a2420"))
	return {"p": p, "t": 26.0, "node": true, "piv": {"head": [0.4, 0.78, 0]}, "nod": 0.7, "ob": [["circ", 0, 0, 0.5, 0.9]]}


func _k_chicken(q: Dictionary) -> Dictionary:
	var c1 = _q(q, "col", "a0522d")
	var p := [S(0.15, 0.24, 0, 0.25, 0, c1), B(0.06, 0.18, 0.18, -0.15, 0.32, 0, c1, 0, 0, 30),
			S(0.07, 0.12, 0.13, 0.42, 0, c1, null), B(0.03, 0.06, 0.02, 0.13, 0.5, 0, "c0392b"),
			B(0.02, 0.14, 0.02, 0.03, 0.07, 0.05, "e8b21e"), B(0.02, 0.14, 0.02, 0.03, 0.07, -0.05, "e8b21e")]
	p[2] = ["s", 0.07, 0.12, 0, 0.13, 0.42, 0, c1, 0, 0, 0, 38.0, "head"]
	p[3] = ["b", 0.03, 0.06, 0.02, 0.13, 0.5, 0, "c0392b", 0, 0, 0, 40.0, "head"]
	p.append(["k", 0.025, 0.06, 0, 0.2, 0.42, 0, "e8b21e", 0, 0, -90, null, "head"])
	return {"p": p, "t": 33.0, "node": true, "piv": {"head": [0.1, 0.35, 0]}, "nod": 0.9}


# ---- Erlebniswelt: static things (style «dezent»: plausible, small, you have to look closely) -----------------------------
func _k_tree_house(q: Dictionary) -> Dictionary:
	var h := float(_q(q, "h", 4.0))
	var p := [C(0.35, h + 4.0, 0, (h + 4.0) / 2.0, 0, "4a3624", 0.5, 0, 0, 0, "tree"), S(3.0, 4.0, 0, h + 4.2, 0, "35662a", "tree"),
			S(2.0, 2.8, 1.6, h + 3.2, 1.0, "3d7030", "tree"), B(2.6, 0.12, 2.4, 0.6, h, 0.9, "7a5a3a", 0, 0, 0, "tree"),
			B(2.2, 1.6, 0.06, 0.6, h + 0.85, -0.25, "6a4a2e", 0, 0, 0, "tree"), B(0.06, 1.6, 2.0, 1.85, h + 0.85, 0.9, "6a4a2e", 0, 0, 0, "tree"),
			B(0.06, 1.6, 2.0, -0.65, h + 0.85, 0.9, "6a4a2e", 0, 0, 0, "tree"), P(2.6, 0.8, 2.6, 0.6, h + 2.05, 0.9, "4a3a2e", 0, 90, 0),
			B(0.5, 0.4, 0.04, 1.86, h + 1.0, 0.9, "1a1410", 0, 90, 0)]
	for sd in [-0.2, 0.2]:                                  # the rope ladder
		p.append(B(0.02, h, 0.02, 0.6 + sd, h / 2.0, 2.15, "c8b88a"))
	for i in range(int(h / 0.35)):
		p.append(B(0.44, 0.04, 0.05, 0.6, 0.3 + i * 0.35, 2.15, "8a6a48"))
	return {"p": p, "t": "tree", "lod": "big", "ob": [["circ", 0, 0, 0.5, h + 4.0]]}


func _k_cave(q: Dictionary) -> Dictionary:
	var r := float(_q(q, "r", 2.2))
	var p := [S(r * 1.4, r * 1.6, 0, 0.2, -r * 0.4, "6e6a62", "stone"), S(r, r * 1.2, r * 0.9, 0.1, 0.1, "7a7670", "stone"),
			S(r * 0.9, r * 1.1, -r * 0.9, 0.1, 0.0, "68645c", "stone"), B(1.0, 1.1, 0.4, 0, 0.5, r * 0.62, "0c0a08"),
			S(0.55, 0.7, 0, 1.0, r * 0.6, "0c0a08")]
	return {"p": p, "t": "stone", "lod": "mid", "ob": [["circ", 0, -r * 0.3, r * 1.3, r * 1.2]]}


func _k_mouse_holes(q: Dictionary) -> Dictionary:
	var L := float(_q(q, "len", 3.0))
	var p := [B(L, 1.1, 0.4, 0, 0.55, 0, "8a8378", 0, 0, 0, "stone"), B(L, 0.08, 0.5, 0, 1.14, 0, "6e6860", 0, 0, 0, "stone")]
	for x in [-L * 0.3, L * 0.3]:
		p.append(C(0.045, 0.02, x, 0.04, 0.2, "0c0a08", 0, 90, 0, 0))
	return {"p": p, "t": "stone", "lod": "small", "ob": [["box", 0, 0, L, 0.5, 1.1]]}


func _k_gnome(q: Dictionary) -> Dictionary:
	return {"p": [C(0.07, 0.16, 0, 0.08, 0, _q(q, "col", "2a5bb0"), 0.09), S(0.055, 0.1, 0, 0.21, 0, "f0c8a0"),
			K(0.06, 0.14, 0, 0.32, 0, _q(q, "hat", "c62020")), K(0.04, 0.08, 0, 0.16, 0.045, "f2f2f2", 180)], "t": "stone", "lod": "small"}


func _k_bottle_post(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.035, 0.22, 0, 0.035, 0, "3a6a4a", 0, 0, 0, 80), C(0.015, 0.06, 0.13, 0.035, 0, "3a6a4a", 0, 0, 0, 80),
			C(0.02, 0.12, 0, 0.035, 0, "e8dcb8", 0, 0, 0, 80)], "t": "stone", "lod": "small"}


func _k_chest(_q: Dictionary) -> Dictionary:
	return {"p": [B(0.6, 0.35, 0.4, 0, 0.18, 0, "6a4228", 0, 0, 0, "tree"), C(0.2, 0.6, 0, 0.36, 0, "5a3820", 0, 0, 0, 90, "tree"),
			B(0.62, 0.05, 0.42, 0, 0.12, 0, "b08a30"), B(0.08, 0.1, 0.03, 0, 0.32, 0.21, "b08a30")], "t": "tree", "lod": "small"}


func _k_fishing_rod(_q: Dictionary) -> Dictionary:
	return {"p": [ROD(Vector3(0, 0.05, 0), Vector3(0, 2.0, -2.6), 0.02, "2a2a2a"), ROD(Vector3(0, 2.0, -2.6), Vector3(0, -0.5, -3.0), 0.005, "d8d8d8"),
			C(0.15, 0.3, 0.4, 0.15, 0.1, "2a6fb0", 0.12), C(0.06, 0.18, -0.4, 0.09, 0.2, "3a6a3a")], "t": "stone", "lod": "small"}


func _k_boot(_q: Dictionary) -> Dictionary:
	return {"p": [C(0.06, 0.28, 0, 0.14, 0, "2a4a2a"), B(0.12, 0.08, 0.24, 0, 0.04, 0.06, "2a4a2a")], "t": "stone", "lod": "small"}


func _k_old_caravan(q: Dictionary) -> Dictionary:
	var d := _k_caravan({"len": 4.8, "col": "b8b0a0", "stripe": "8a6a3a", "awning": false})
	for part in d["p"]:
		if typeof(part[7]) == TYPE_STRING and str(part[7]).begins_with("%"):
			part[7] = "2a2e30"                                 # no light inside (or is there? - the later package decides)
	d["p"].append(B(4.2, 0.05, 2.0, 0.2, 2.57, 0.05, "4a5a2a"))  # moss on the roof
	d["p"].append(B(0.6, 0.4, 0.05, -1.2, 1.5, 1.17, "1a1410"))  # broken window
	d.erase("lights")
	d["lod"] = "mid"
	return d


func _k_sunken_boat(_q: Dictionary) -> Dictionary:
	var d := _k_rowboat({"len": 4.0, "col": "4a4a3e"})
	d["p"].append(C(0.05, 1.4, 0, 0.9, 0.8, "3a3a2e", 0, 30, 0, 0))   # the stub of the mast sticks out of the water
	return d


func _k_knothole_tree(q: Dictionary) -> Dictionary:
	var d := _k_tree(q)
	d["p"].append(S(0.11, 0.16, 0, 2.2, 0.22, "0c0a08", "tree"))
	return d
