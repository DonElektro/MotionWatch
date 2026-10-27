extends RefCounted
## The buildings of swisstopo in 3D (swissBUILDINGS3D, 3D Tiles of geo.admin.ch) for a real place (from 3D-3.10).
## Reads tileset.json (also nested ones), takes the tiles that lie in the detailed square, unpacks b3dm (or glb), turns the
## coordinates of the earth (ECEF) into the coordinates of the scene (east = x, up = y, north = -z) and returns ArrayMeshes.
## If anything does not work (no internet, other format, compressed meshes Godot cannot read) the houses of OpenStreetMap
## are used as before.

const TILESET := "https://3d.geo.admin.ch/ch.swisstopo.swissbuildings3d.3d/v1/tileset.json"
const MAX_TILES := 40
const A_WGS := 6378137.0
const E2 := 0.00669437999014

var geo
var region := []                 # [west, south, east, north] in radians (the near square + a margin)
var ecef0 := [0.0, 0.0, 0.0]
var rot := Basis()               # ECEF -> local (rows: east, up, south)
var contents: Array = []         # [url, transform (16 doubles)]
var fetched := 0
var info := ""


static func ecef(lat: float, lon: float, h: float) -> Array:
	var la := deg_to_rad(lat)
	var lo := deg_to_rad(lon)
	var n := A_WGS / sqrt(1.0 - E2 * sin(la) * sin(la))
	return [(n + h) * cos(la) * cos(lo), (n + h) * cos(la) * sin(lo), (n * (1.0 - E2) + h) * sin(la)]


static func mat_mul(a: Array, b: Array) -> Array:
	"""4 × 4, column-major (as in 3D Tiles)"""
	var o := []
	o.resize(16)
	for c in range(4):
		for r in range(4):
			var s := 0.0
			for k in range(4):
				s += float(a[k * 4 + r]) * float(b[c * 4 + k])
			o[c * 4 + r] = s
	return o


const IDENT := [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


func fetch_buildings(g, my_gen: int, keep_out: Array) -> Array:
	"""ArrayMeshes of the buildings in local coordinates (empty if it did not work)"""
	geo = g
	var lo0: Vector2 = geo.to_ll(Vector2(-geo.NEAR - 40, geo.NEAR + 40))
	var hi0: Vector2 = geo.to_ll(Vector2(geo.NEAR + 40, -geo.NEAR - 40))
	region = [deg_to_rad(lo0.y), deg_to_rad(lo0.x), deg_to_rad(hi0.y), deg_to_rad(hi0.x)]
	ecef0 = ecef(geo.lat, geo.lon, geo.h0 + 49.0)          # about: the ellipsoid lies ~49 m below the Swiss heights (corrected below)
	var la := deg_to_rad(geo.lat)
	var lo := deg_to_rad(geo.lon)
	var east := Vector3(-sin(lo), cos(lo), 0)
	var north := Vector3(-sin(la) * cos(lo), -sin(la) * sin(lo), cos(la))
	var up := Vector3(cos(la) * cos(lo), cos(la) * sin(lo), sin(la))
	rot = Basis(Vector3(east.x, up.x, -north.x), Vector3(east.y, up.y, -north.y), Vector3(east.z, up.z, -north.z))   # columns: images of ECEF x, y, z
	contents = []
	fetched = 0
	var u: String = geo.url("b3d") if geo.has_method("url") else TILESET
	var ts = await _json(u)
	if typeof(ts) != TYPE_DICTIONARY or not ts.has("root"):
		info = "3D-Gebäude: keine Antwort von swisstopo"
		return []
	await _walk(ts["root"], u.get_base_dir() + "/", IDENT, 0, my_gen)
	if my_gen != geo.gen:
		return []
	if contents.is_empty():
		info = "3D-Gebäude: keine Kacheln für diesen Ort"
		return []
	var meshes := []
	var n := 0
	for c in contents:
		n += 1
		geo.info = "Lade 3D-Gebäude von swisstopo … %d von %d" % [n, contents.size()]
		var bytes: PackedByteArray = await geo.fetch(c[0])
		if my_gen != geo.gen:
			return []
		if bytes.size() < 28:
			continue
		var m = _tile_mesh(bytes, c[1], keep_out)
		if m != null:
			meshes.append(m)
	if meshes.is_empty():
		info = "3D-Gebäude: Format nicht lesbar – Häuser aus OpenStreetMap"
		return []
	_align(meshes)
	info = ""
	return meshes


func _json(u: String):
	var b: PackedByteArray = await geo.fetch(u)
	fetched += 1
	return JSON.parse_string(b.get_string_from_utf8()) if b.size() > 0 else null


func _hits(tile: Dictionary, tf: Array) -> bool:
	var bv = tile.get("boundingVolume", {})
	if typeof(bv) != TYPE_DICTIONARY:
		return true
	if bv.has("region"):
		var r: Array = bv["region"]
		return not (float(r[2]) < region[0] or float(r[0]) > region[2] or float(r[3]) < region[1] or float(r[1]) > region[3])
	var c := []
	var rad := 0.0
	if bv.has("box"):
		var b: Array = bv["box"]
		c = [float(b[0]), float(b[1]), float(b[2])]
		for k in range(3, 12):
			rad += abs(float(b[k]))
	elif bv.has("sphere"):
		var s: Array = bv["sphere"]
		c = [float(s[0]), float(s[1]), float(s[2])]
		rad = float(s[3])
	else:
		return true
	var w := [float(tf[0]) * c[0] + float(tf[4]) * c[1] + float(tf[8]) * c[2] + float(tf[12]),
			float(tf[1]) * c[0] + float(tf[5]) * c[1] + float(tf[9]) * c[2] + float(tf[13]),
			float(tf[2]) * c[0] + float(tf[6]) * c[1] + float(tf[10]) * c[2] + float(tf[14])]
	var d := sqrt(pow(w[0] - ecef0[0], 2) + pow(w[1] - ecef0[1], 2) + pow(w[2] - ecef0[2], 2))
	return d < rad + geo.NEAR * 1.6


func _walk(tile: Dictionary, base: String, parent_tf: Array, depth: int, my_gen: int) -> void:
	if depth > 24 or contents.size() >= MAX_TILES or fetched > 60 or my_gen != geo.gen:
		return
	var tf := parent_tf
	if tile.has("transform") and typeof(tile["transform"]) == TYPE_ARRAY and (tile["transform"] as Array).size() == 16:
		tf = mat_mul(parent_tf, tile["transform"])
	if not _hits(tile, tf):
		return
	var kids: Array = tile.get("children", []) if typeof(tile.get("children", [])) == TYPE_ARRAY else []
	var uri := ""
	var ct = tile.get("content", tile.get("contents", null))
	if typeof(ct) == TYPE_ARRAY and not (ct as Array).is_empty():
		ct = ct[0]
	if typeof(ct) == TYPE_DICTIONARY:
		uri = str(ct.get("uri", ct.get("url", "")))
	var fine := float(tile.get("geometricError", 0.0)) <= 2.0
	if uri != "":
		var full := uri if uri.begins_with("http") else base + uri
		if uri.get_extension().to_lower().begins_with("json"):
			var sub = await _json(full)
			if typeof(sub) == TYPE_DICTIONARY and sub.has("root"):
				await _walk(sub["root"], full.get_base_dir() + "/", tf, depth + 1, my_gen)
		elif kids.is_empty() or fine or str(tile.get("refine", "")).to_upper() == "ADD":
			contents.append([full, tf])
			if kids.is_empty() or fine:
				return
	for k in kids:
		if typeof(k) == TYPE_DICTIONARY:
			await _walk(k, base, tf, depth + 1, my_gen)


func _tile_mesh(bytes: PackedByteArray, tf: Array, keep_out: Array):
	"""one tile -> ArrayMesh in local coordinates (or null)"""
	var glb := bytes
	var rtc := [0.0, 0.0, 0.0]
	var magic := bytes.slice(0, 4).get_string_from_ascii()
	if magic == "b3dm":
		var ftj := bytes.decode_u32(12)
		var ftb := bytes.decode_u32(16)
		var btj := bytes.decode_u32(20)
		var btb := bytes.decode_u32(24)
		var ft = JSON.parse_string(bytes.slice(28, 28 + ftj).get_string_from_utf8()) if ftj > 0 else null
		if typeof(ft) == TYPE_DICTIONARY and ft.has("RTC_CENTER"):
			var rc = ft["RTC_CENTER"]
			if typeof(rc) == TYPE_ARRAY and rc.size() == 3:
				rtc = [float(rc[0]), float(rc[1]), float(rc[2])]
		glb = bytes.slice(28 + ftj + ftb + btj + btb)
	elif magic != "glTF":
		return null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_buffer(glb, "", st) != OK:
		return null
	var scene = doc.generate_scene(st)
	if scene == null:
		return null
	# glTF is y-up, 3D Tiles z-up: (x, y, z) -> (x, -z, y); then the tile transform; then - ecef0, then into the scene
	var st_out := SurfaceTool.new()
	st_out.begin(Mesh.PRIMITIVE_TRIANGLES)
	var count := 0
	var stack := [[scene, Transform3D()]]
	while not stack.is_empty():
		var it: Array = stack.pop_back()
		var nd: Node = it[0]
		var xf: Transform3D = it[1]
		if nd is Node3D and nd != scene:
			xf = xf * (nd as Node3D).transform
		if nd is MeshInstance3D and (nd as MeshInstance3D).mesh != null:
			count += _add_mesh(st_out, (nd as MeshInstance3D).mesh, xf, rtc, tf, keep_out)
		for ch in nd.get_children():
			stack.append([ch, xf])
	scene.free()
	if count == 0:
		return null
	return st_out.commit()


func _add_mesh(st_out: SurfaceTool, mesh: Mesh, xf: Transform3D, rtc: Array, tf: Array, keep_out: Array) -> int:
	# the whole chain without the big numbers in single precision: local = rot * (TF * (zup(xf * v) + rtc) - ecef0)
	var t3 := [float(tf[12]) + float(tf[0]) * rtc[0] + float(tf[4]) * rtc[1] + float(tf[8]) * rtc[2] - ecef0[0],
			float(tf[13]) + float(tf[1]) * rtc[0] + float(tf[5]) * rtc[1] + float(tf[9]) * rtc[2] - ecef0[1],
			float(tf[14]) + float(tf[2]) * rtc[0] + float(tf[6]) * rtc[1] + float(tf[10]) * rtc[2] - ecef0[2]]
	var tl: Vector3 = rot * Vector3(t3[0], t3[1], t3[2])
	var tb := Basis(Vector3(float(tf[0]), float(tf[1]), float(tf[2])), Vector3(float(tf[4]), float(tf[5]), float(tf[6])), Vector3(float(tf[8]), float(tf[9]), float(tf[10])))
	var zup := Basis(Vector3(1, 0, 0), Vector3(0, 0, 1), Vector3(0, -1, 0))   # glTF y -> z, glTF z -> -y
	var full := Transform3D(rot * tb * zup, tl) * xf
	var n := 0
	for si in range(mesh.get_surface_count()):
		var arr: Array = mesh.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var idx = arr[Mesh.ARRAY_INDEX]
		var ids := PackedInt32Array()
		if idx == null or (idx as PackedInt32Array).is_empty():
			ids.resize(v.size())
			for i in range(v.size()):
				ids[i] = i
		else:
			ids = idx
		var w := PackedVector3Array()
		w.resize(v.size())
		for i in range(v.size()):
			w[i] = full * v[i]
		for q in range(0, ids.size() - 2, 3):
			var a := w[ids[q]]
			var b := w[ids[q + 1]]
			var c := w[ids[q + 2]]
			var m := (a + b + c) / 3.0
			if abs(m.x) > geo.NEAR + 30.0 or abs(m.z) > geo.NEAR + 30.0:
				continue
			var skip := false
			for poly in keep_out:
				if Geometry2D.is_point_in_polygon(Vector2(m.x, m.z), poly):
					skip = true
					break
			if skip:
				continue
			var nrm := (c - a).cross(b - a)               # flat, matching the winding of Godot (front = clockwise)
			if nrm.length() < 1e-6:
				continue
			nrm = nrm.normalized()
			for pv in [a, b, c]:
				st_out.set_normal(nrm)
				st_out.add_vertex(pv)
			n += 1
	return n


func _align(meshes: Array) -> void:
	"""the houses stand on the ground: the lowest points of the buildings are compared with the terrain (median)"""
	var low := {}
	for m in meshes:
		var v: PackedVector3Array = (m as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		for p in v:
			var k := Vector2i(int(floor(p.x / 4.0)), int(floor(p.z / 4.0)))
			if not low.has(k) or p.y < low[k].y:
				low[k] = p
	var diffs := []
	for k in low:
		var p: Vector3 = low[k]
		diffs.append(geo.height(p.x, p.z) - p.y)
	if diffs.is_empty():
		return
	diffs.sort()
	var off: float = diffs[int(diffs.size() * 0.3)]        # rather lower than median: cellars / slopes
	for i in range(meshes.size()):
		var am: ArrayMesh = meshes[i]
		var arr := am.surface_get_arrays(0)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for j in range(v.size()):
			v[j].y += off
		arr[Mesh.ARRAY_VERTEX] = v
		var nm := ArrayMesh.new()
		nm.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		meshes[i] = nm
