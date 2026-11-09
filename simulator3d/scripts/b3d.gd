extends RefCounted
## The buildings of swisstopo in 3D (swissBUILDINGS3D, 3D Tiles of geo.admin.ch) for a real place (from 3D-3.10).
## Reads tileset.json (also nested ones), takes the tiles that lie in the detailed square, unpacks b3dm (or glb), turns the
## coordinates of the earth (ECEF) into the coordinates of the scene (east = x, up = y, north = -z) and returns ArrayMeshes.
## Sim 3.66.0: swisstopo sends the meshes Draco-compressed (KHR_draco_mesh_compression), which Godot 4.3 cannot read - so it
## never worked and always fell back to OpenStreetMap. Now: own glb reader with the Draco decoder draco.gd (GDScript, runs on
## Windows, Linux and the Pi alike), one footprint per building (from the batch ids) for the obstacles and «not inside a house»,
## walls and roofs merged into a few meshes. If anything does not work, the houses of OpenStreetMap are used and «reason» says
## why in a few words (shown on the map and in the status line).

const TILESET := "https://3d.geo.admin.ch/ch.swisstopo.swissbuildings3d.3d/v1/tileset.json"
const MAX_TILES := 80
const A_WGS := 6378137.0
const E2 := 0.00669437999014
const Draco = preload("res://scripts/draco.gd")

var geo
var region := []                 # [west, south, east, north] in radians (the near square + a margin)
var ecef0 := [0.0, 0.0, 0.0]
var rot := Basis()               # ECEF -> local (rows: east, up, south)
var contents: Array = []         # [url, transform (16 doubles)]
var fetched := 0
var info := ""
var reason := ""                 # short: why there are no 3D buildings (empty = they are there)
var diag: Array = []             # what happened, for the wizard and the report (from 3D-3.15)
var tiles_ok := 0
var bytes_in := 0                # downloaded or from the cache (tiles + tileset files)
var foot: Array = []             # one per building: {"poly": hull in x/z, "base": lowest y, "top": highest y}
var head_in := false             # a building stood where MoveEye is: left out
var ms_decode := 0
var ms_draco := 0
var from_cache := 0              # primitives taken unpacked from the cache
const DRACO_CACHE := "draco-v1"  # (part of the cache name: change it when draco.gd decodes differently)
var tris := 0
var fassaden_stats := {}
# collected triangles (local coordinates, before the height correction): 3 vertices each, building key per triangle
var _tv := PackedVector3Array()
var _tk := PackedInt32Array()


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


func _fail(short: String, long := "") -> Array:
	reason = short
	info = "3D-Gebäude: " + short
	if long != "":
		_note(long)
	return []


func fetch_buildings(g, my_gen: int, keep_out: Array) -> Array:
	"""[{"mesh": ArrayMesh, "t": thermal key}] of the buildings in local coordinates (empty if it did not work, see reason)"""
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
	foot = []
	head_in = false
	_tv = PackedVector3Array()
	_tk = PackedInt32Array()
	var u: String = geo.url("b3d") if geo.has_method("url") else TILESET
	diag = []
	var ts = await _json(u, true)                         # the top file fresh: it names the current version (e.g. 20260520/)
	if typeof(ts) != TYPE_DICTIONARY or not ts.has("root"):
		var why := "keine Antwort von swisstopo" if ts == null else "unbekannte Antwort von swisstopo"
		return _fail(why, "tileset.json: " + why + " (" + u + ")" + (" – " + geo._last_err if str(geo._last_err) != "" else ""))
	diag.append("tileset.json ok, Version %s" % str((ts.get("asset", {}) as Dictionary).get("version", "?")) if typeof(ts.get("asset")) == TYPE_DICTIONARY else "tileset.json ok")
	await _walk(ts["root"], u.get_base_dir() + "/", IDENT, 0, my_gen)
	if my_gen != geo.gen:
		return []
	diag.append("%d Kacheln für diesen Ort (%d Verzeichnisse gelesen)" % [contents.size(), fetched])
	if contents.is_empty():
		return _fail("keine Kacheln für diesen Ort" if fetched > 0 else "Verzeichnis nicht lesbar")
	var jobs := []
	for c in contents:
		jobs.append([c[0]])
	var got: Array = await geo.fetch_many(jobs, "Lade 3D-Gebäude von swisstopo", my_gen)
	if my_gen != geo.gen:
		return []
	var t0 := Time.get_ticks_msec()
	# unpacking (Draco in GDScript: about 1 s for a village here, several on a Pi) in a thread: the window stays alive
	var st := {"i": 0, "empty": 0, "stop": false, "done": false}
	var th := Thread.new()
	th.start(_unpack_all.bind(got, keep_out, st))
	while not st["done"]:
		await geo.get_tree().process_frame
		geo.info = "Packe 3D-Gebäude aus … %d von %d" % [st["i"], contents.size()]
		if my_gen != geo.gen:
			st["stop"] = true
	th.wait_to_finish()
	if my_gen != geo.gen:
		return []
	var empty: int = st["empty"]
	ms_decode = Time.get_ticks_msec() - t0
	if tiles_ok == 0:
		if empty == contents.size():
			return _fail("Kacheln nicht geladen (" + str(geo._last_err) + ")")
		return _fail("Kacheln nicht lesbar" + (": " + str(diag[-1]) if diag.size() > 2 else ""))
	var meshes := _finish(keep_out)
	diag.append("%d von %d Kacheln gelesen, %d Häuser, %d Dreiecke, %.0f kB, %d ms entpackt (Draco %d ms, %d Teile aus dem Speicher)" % [tiles_ok, contents.size(), foot.size(), tris, bytes_in / 1024.0, ms_decode, ms_draco, from_cache])
	if meshes.is_empty():
		return _fail("keine Häuser im Nahbereich")
	info = ""
	reason = ""
	return meshes


func _json(u: String, fresh := false):
	var b := PackedByteArray()
	if fresh:                                            # try the internet first, the cache only when offline
		b = await geo.fetch(u, "", false, 20.0)
		if b.size() > 0:
			var f := FileAccess.open(geo.cache_path(u), FileAccess.WRITE)
			if f != null:
				f.store_buffer(b)
				f.close()
		elif FileAccess.file_exists(geo.cache_path(u)):
			b = FileAccess.get_file_as_bytes(geo.cache_path(u))
			_note("swisstopo nicht erreichbar – Verzeichnis aus dem Speicher")
	else:                                                # the index files (some 10 MB each) packed in the cache
		var cp: String = geo.cache_path(u, "zstd")
		if FileAccess.file_exists(cp):
			var f := FileAccess.open_compressed(cp, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
			if f != null:
				b = f.get_buffer(f.get_length())
				f.close()
		if b.is_empty():
			b = _unzip(await geo.fetch(u, "", false))
			if b.size() > 0:
				var f := FileAccess.open_compressed(cp, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
				if f != null:
					f.store_buffer(b)
					f.close()
	b = _unzip(b)
	fetched += 1
	bytes_in += b.size()
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
	if tile.has("implicitTiling"):
		_note("implizite Kacheln (3D Tiles 1.1) – nicht unterstützt")
	var kids: Array = tile.get("children", []) if typeof(tile.get("children", [])) == TYPE_ARRAY else []
	var uris := []
	var ct = tile.get("contents", tile.get("content", null))      # 3D Tiles 1.1: «contents» (several), 1.0: «content»
	for c in (ct if typeof(ct) == TYPE_ARRAY else [ct]):
		if typeof(c) == TYPE_DICTIONARY and str(c.get("uri", c.get("url", ""))) != "":
			uris.append(str(c.get("uri", c.get("url", ""))))
	var fine := float(tile.get("geometricError", 0.0)) <= 2.0
	for uri in uris:
		var full: String = uri if uri.begins_with("http") else _join(base, uri)
		if _is_json(uri):
			var sub = await _json(full)
			if typeof(sub) == TYPE_DICTIONARY and sub.has("root"):
				await _walk(sub["root"], full.get_base_dir() + "/", tf, depth + 1, my_gen)
			elif diag.size() < 8:
				_note("Verzeichnis nicht lesbar: " + full.get_file())
		elif kids.is_empty() or fine or str(tile.get("refine", "")).to_upper() == "ADD":
			if contents.size() < MAX_TILES:
				contents.append([full, tf])
			else:
				_note("mehr als %d Kacheln – Rest weggelassen" % MAX_TILES)
	if not uris.is_empty() and not _is_json(uris[0]) and (kids.is_empty() or fine):
		return
	for k in kids:
		if typeof(k) == TYPE_DICTIONARY:
			await _walk(k, base, tf, depth + 1, my_gen)


func _unpack_all(got: Array, _keep_out: Array, st: Dictionary) -> void:
	"""(in a thread) all downloaded tiles into _tv / _tk"""
	for i in range(contents.size()):
		if st["stop"]:
			break
		st["i"] = i + 1
		var bytes: PackedByteArray = _unzip(got[i] if typeof(got[i]) == TYPE_PACKED_BYTE_ARRAY else PackedByteArray())
		bytes_in += bytes.size()
		if bytes.size() < 28:
			st["empty"] += 1
			_note("Kachel fehlt: " + str(contents[i][0]).get_file())
			continue
		if _tile(bytes, contents[i][1], i, str(contents[i][0])):
			tiles_ok += 1
	st["done"] = true


static func _is_json(uri: String) -> bool:
	return uri.get_slice("?", 0).get_extension().to_lower() == "json"


static func _join(base: String, uri: String) -> String:
	"""a relative address (also with ./ and ../ and a query) against the folder base (ending with /)"""
	var q := ""
	if base.contains("?"):
		q = base.substr(base.find("?"))
		base = base.substr(0, base.find("?"))
	if uri.begins_with("/"):
		var host := base.substr(0, base.find("/", base.find("//") + 2))
		return host + uri
	var parts := base.trim_suffix("/").split("/")
	for s in uri.split("/"):
		if s == "..":
			if parts.size() > 3:
				parts.remove_at(parts.size() - 1)
		elif s != ".":
			parts.append(s)
	var out := "/".join(parts)
	return out + (q if not uri.contains("?") else "")


# ---- one tile ------------------------------------------------------------------------------------------------------------
func _tile(bytes: PackedByteArray, tf: Array, ti: int, url: String) -> bool:
	"""one tile: its triangles into _tv / _tk (true if any)"""
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
		_note("unbekanntes Kachelformat «%s»" % magic.c_escape())
		return false
	if glb.size() < 20 or glb.slice(0, 4).get_string_from_ascii() != "glTF":
		_note("Kachel ohne glTF")
		return false
	var jl := glb.decode_u32(12)
	var j = JSON.parse_string(glb.slice(20, 20 + jl).get_string_from_utf8())
	if typeof(j) != TYPE_DICTIONARY:
		_note("glTF-Kopf unlesbar")
		return false
	var bin := PackedByteArray()
	var at := 20 + jl
	while at + 8 <= glb.size():                           # the chunks after the JSON: the first BIN chunk
		var cl := glb.decode_u32(at)
		if glb.decode_u32(at + 4) == 0x004E4942:
			bin = glb.slice(at + 8, at + 8 + cl)
			break
		at += 8 + cl + ((4 - cl % 4) % 4 if cl % 4 != 0 else 0)
	var req: Array = j.get("extensionsRequired", []) if typeof(j.get("extensionsRequired", [])) == TYPE_ARRAY else []
	for e in req:
		if not e in ["KHR_draco_mesh_compression", "CESIUM_RTC", "KHR_materials_unlit", "KHR_mesh_quantization"]:
			_note("glTF braucht %s – nicht unterstützt" % e)
			return false
	var ext = j.get("extensions", {})
	if typeof(ext) == TYPE_DICTIONARY and typeof(ext.get("CESIUM_RTC")) == TYPE_DICTIONARY:
		var cc = ext["CESIUM_RTC"].get("center", [])
		if typeof(cc) == TYPE_ARRAY and cc.size() == 3:
			rtc = [rtc[0] + float(cc[0]), rtc[1] + float(cc[1]), rtc[2] + float(cc[2])]
	# the chain without the big numbers in single precision: local = rot * (TF * (zup(xf * v) + rtc) - ecef0)
	var t3 := [float(tf[12]) + float(tf[0]) * rtc[0] + float(tf[4]) * rtc[1] + float(tf[8]) * rtc[2] - ecef0[0],
			float(tf[13]) + float(tf[1]) * rtc[0] + float(tf[5]) * rtc[1] + float(tf[9]) * rtc[2] - ecef0[1],
			float(tf[14]) + float(tf[2]) * rtc[0] + float(tf[6]) * rtc[1] + float(tf[10]) * rtc[2] - ecef0[2]]
	var tl: Vector3 = rot * Vector3(t3[0], t3[1], t3[2])
	var tb := Basis(Vector3(float(tf[0]), float(tf[1]), float(tf[2])), Vector3(float(tf[4]), float(tf[5]), float(tf[6])), Vector3(float(tf[8]), float(tf[9]), float(tf[10])))
	var zup := Basis(Vector3(1, 0, 0), Vector3(0, 0, 1), Vector3(0, -1, 0))   # glTF y -> z, glTF z -> -y
	var outer := Transform3D(rot * tb * zup, tl)
	var meshes: Array = j.get("meshes", []) if typeof(j.get("meshes", [])) == TYPE_ARRAY else []
	var n0 := _tk.size()
	# the unpacked Draco data of this tile from the cache (unpacking costs about 1 s per village here, more on a Pi)
	var cp: String = geo.cache_path(url, DRACO_CACHE)
	var dc := {}
	if FileAccess.file_exists(cp):
		var f := FileAccess.open_compressed(cp, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
		var v = f.get_var() if f != null else null
		if typeof(v) == TYPE_DICTIONARY:
			dc = v
	var dirty := [false]
	for nd in _mesh_nodes(j):
		var mi: int = nd[0]
		if mi < 0 or mi >= meshes.size() or typeof(meshes[mi]) != TYPE_DICTIONARY:
			continue
		var full: Transform3D = outer * (nd[1] as Transform3D)
		var pi := 0
		for pr in meshes[mi].get("primitives", []):
			if typeof(pr) == TYPE_DICTIONARY and int(pr.get("mode", 4)) == 4:
				_prim(j, bin, pr, full, ti, dc, "%d/%d" % [mi, pi], dirty)
			pi += 1
	if dirty[0]:
		var f := FileAccess.open_compressed(cp, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
		if f != null:
			f.store_var(dc)
			f.close()
	return _tk.size() > n0


func _mesh_nodes(j: Dictionary) -> Array:
	"""[[mesh, Transform3D]] of all nodes with a mesh (through the node tree of the scene)"""
	var nodes: Array = j.get("nodes", []) if typeof(j.get("nodes", [])) == TYPE_ARRAY else []
	var roots := []
	var scenes = j.get("scenes", [])
	if typeof(scenes) == TYPE_ARRAY and not scenes.is_empty():
		var sc = scenes[clampi(int(j.get("scene", 0)), 0, scenes.size() - 1)]
		if typeof(sc) == TYPE_DICTIONARY:
			roots = sc.get("nodes", [])
	if roots.is_empty():
		var child := {}
		for nd in nodes:
			if typeof(nd) == TYPE_DICTIONARY:
				for c in nd.get("children", []):
					child[int(c)] = true
		for i in range(nodes.size()):
			if not child.has(i):
				roots.append(i)
	var out := []
	var stack := []
	for r in roots:
		stack.append([int(r), Transform3D(), 0])
	while not stack.is_empty():
		var it: Array = stack.pop_back()
		var i: int = it[0]
		if i < 0 or i >= nodes.size() or typeof(nodes[i]) != TYPE_DICTIONARY or it[2] > 32:
			continue
		var nd: Dictionary = nodes[i]
		var xf: Transform3D = (it[1] as Transform3D) * _node_xf(nd)
		if nd.has("mesh"):
			out.append([int(nd["mesh"]), xf])
		for c in nd.get("children", []):
			stack.append([int(c), xf, it[2] + 1])
	return out


static func _node_xf(nd: Dictionary) -> Transform3D:
	var m = nd.get("matrix")
	if typeof(m) == TYPE_ARRAY and m.size() == 16:
		return Transform3D(Basis(Vector3(m[0], m[1], m[2]), Vector3(m[4], m[5], m[6]), Vector3(m[8], m[9], m[10])), Vector3(m[12], m[13], m[14]))
	var t = nd.get("translation", [0, 0, 0])
	var r = nd.get("rotation", [0, 0, 0, 1])
	var s = nd.get("scale", [1, 1, 1])
	var bs := Basis(Quaternion(float(r[0]), float(r[1]), float(r[2]), float(r[3])).normalized()) * Basis.from_scale(Vector3(s[0], s[1], s[2]))
	return Transform3D(bs, Vector3(t[0], t[1], t[2]))


func _prim(j: Dictionary, bin: PackedByteArray, pr: Dictionary, xf: Transform3D, ti: int, dc: Dictionary, key: String, dirty: Array) -> void:
	var pos := PackedVector3Array()
	var tri := PackedInt32Array()
	var bid := PackedFloat32Array()
	var attrs: Dictionary = pr.get("attributes", {}) if typeof(pr.get("attributes")) == TYPE_DICTIONARY else {}
	var ex = pr.get("extensions", {})
	if typeof(ex) == TYPE_DICTIONARY and typeof(ex.get("KHR_draco_mesh_compression")) == TYPE_DICTIONARY:
		var dr: Dictionary = ex["KHR_draco_mesh_compression"]
		if typeof(dc.get(key)) == TYPE_ARRAY and (dc[key] as Array).size() == 3:
			pos = dc[key][0]
			tri = dc[key][1]
			bid = dc[key][2]
			from_cache += 1
		else:
			var data := _view(j, bin, int(dr.get("bufferView", -1)))
			var td := Time.get_ticks_usec()
			var res: Dictionary = Draco.decode(data)
			ms_draco += int((Time.get_ticks_usec() - td) / 1000)
			if not res.get("ok", false):
				_note(str(res.get("err", "Draco nicht lesbar")))
				return
			var da = dr.get("attributes", {})
			if typeof(da) == TYPE_DICTIONARY and da.has("POSITION") and int(da["POSITION"]) != int(res.get("pos_uid", -1)):
				_note("Draco: Positionen unter anderer Nummer")
				return
			pos = res["pos"]
			tri = res["tri"]
			if typeof(da) == TYPE_DICTIONARY:
				for k in ["_BATCHID", "_FEATURE_ID_0"]:
					if da.has(k):
						bid = Draco.attribute(res, int(da[k]))
						break
			dc[key] = [pos, tri, bid]
			dirty[0] = true
	else:
		if not attrs.has("POSITION"):
			return
		pos = _acc_vec3(j, bin, int(attrs["POSITION"]))
		if pr.has("indices"):
			tri = _acc_int(j, bin, int(pr["indices"]))
		else:
			tri.resize(pos.size() - pos.size() % 3)
			for i in range(tri.size()):
				tri[i] = i
		for k in ["_BATCHID", "_FEATURE_ID_0"]:
			if attrs.has(k):
				var ids := _acc_int(j, bin, int(attrs[k]), true)
				bid.resize(ids.size())
				for i in range(ids.size()):
					bid[i] = ids[i]
				break
	if pos.is_empty() or tri.size() < 3:
		_note("Kachel ohne Dreiecke")
		return
	var w := PackedVector3Array()
	w.resize(pos.size())
	for i in range(pos.size()):
		w[i] = xf * pos[i]
	var nv := w.size()
	for q in range(0, tri.size() - 2, 3):
		var ia := tri[q]
		var ib := tri[q + 1]
		var ic := tri[q + 2]
		if ia < 0 or ib < 0 or ic < 0 or ia >= nv or ib >= nv or ic >= nv:
			continue
		_tv.append(w[ia])
		_tv.append(w[ib])
		_tv.append(w[ic])
		var bk := int(bid[ia]) if ia < bid.size() and bid[ia] >= 0.0 else 9999
		_tk.append(ti * 10000 + clampi(bk, 0, 9999))


static func _view(j: Dictionary, bin: PackedByteArray, vi: int) -> PackedByteArray:
	var views: Array = j.get("bufferViews", [])
	if vi < 0 or vi >= views.size():
		return PackedByteArray()
	var v: Dictionary = views[vi]
	var o := int(v.get("byteOffset", 0))
	return bin.slice(o, o + int(v.get("byteLength", 0)))


static func _acc_vec3(j: Dictionary, bin: PackedByteArray, ai: int) -> PackedVector3Array:
	"""an uncompressed float VEC3 accessor"""
	var out := PackedVector3Array()
	var accs: Array = j.get("accessors", [])
	if ai < 0 or ai >= accs.size():
		return out
	var a: Dictionary = accs[ai]
	if int(a.get("componentType", 0)) != 5126 or str(a.get("type", "")) != "VEC3" or not a.has("bufferView"):
		return out
	var views: Array = j.get("bufferViews", [])
	var v: Dictionary = views[int(a["bufferView"])]
	var o := int(v.get("byteOffset", 0)) + int(a.get("byteOffset", 0))
	var stride := int(v.get("byteStride", 12))
	var n := int(a.get("count", 0))
	if o + stride * (n - 1) + 12 > bin.size():
		return out
	out.resize(n)
	for i in range(n):
		out[i] = Vector3(bin.decode_float(o + i * stride), bin.decode_float(o + i * stride + 4), bin.decode_float(o + i * stride + 8))
	return out


static func _acc_int(j: Dictionary, bin: PackedByteArray, ai: int, allow_float := false) -> PackedInt32Array:
	"""an uncompressed SCALAR accessor of whole numbers (indices, batch ids)"""
	var out := PackedInt32Array()
	var accs: Array = j.get("accessors", [])
	if ai < 0 or ai >= accs.size():
		return out
	var a: Dictionary = accs[ai]
	var ctp := int(a.get("componentType", 0))
	var sz: int = {5121: 1, 5123: 2, 5125: 4, 5126: 4}.get(ctp, 0)
	if sz == 0 or (ctp == 5126 and not allow_float) or not a.has("bufferView"):
		return out
	var v: Dictionary = (j.get("bufferViews", []) as Array)[int(a["bufferView"])]
	var o := int(v.get("byteOffset", 0)) + int(a.get("byteOffset", 0))
	var stride := int(v.get("byteStride", sz))
	var n := int(a.get("count", 0))
	if o + stride * (n - 1) + sz > bin.size():
		return out
	out.resize(n)
	for i in range(n):
		var k := o + i * stride
		out[i] = bin[k] if sz == 1 else (bin.decode_u16(k) if sz == 2 else (int(bin.decode_float(k)) if ctp == 5126 else bin.decode_u32(k)))
	return out


# ---- all tiles together ------------------------------------------------------------------------------------------------
func _finish(keep_out: Array) -> Array:
	"""per building: footprint, MoveEye inside?, in the near square?; height to the terrain; then walls and roofs merged"""
	var by := {}                                          # building key -> triangles (plain arrays: they grow in place)
	for t in range(_tk.size()):
		var k := _tk[t]
		if not by.has(k):
			by[k] = []
		by[k].append(t)
	var lim: float = geo.NEAR + 30.0
	var keep := []                                        # [key, hull, base, top]
	var diffs := []
	for k in by:
		var ts: Array = by[k]
		var pts := PackedVector2Array()
		var base := INF
		var top := -INF
		var c := Vector2.ZERO
		for t in ts:
			for m in range(3):
				var v := _tv[t * 3 + m]
				pts.append(Vector2(v.x, v.z))
				c += Vector2(v.x, v.z)
				base = min(base, v.y)
				top = max(top, v.y)
		c /= pts.size()
		if abs(c.x) > lim or abs(c.y) > lim:
			continue
		var hull := Geometry2D.convex_hull(pts)
		if hull.size() > 1 and hull[0] == hull[-1]:
			hull.remove_at(hull.size() - 1)
		if hull.size() < 3:
			continue
		var inside := false
		for g in Geometry2D.offset_polygon(hull, 0.8):
			if Geometry2D.is_point_in_polygon(Vector2.ZERO, g):
				inside = true
		for poly in keep_out:                             # the house of OpenStreetMap round MoveEye
			if Geometry2D.is_point_in_polygon(c, poly):
				inside = true
		if inside and _key_house(k):
			head_in = true
			continue
		keep.append([k, hull, base, top])
		# the lowest point of the building against the terrain (several points at the bottom: the median of them)
		var lows := []
		for t in ts:
			for m in range(3):
				var v := _tv[t * 3 + m]
				if v.y < base + 0.3:
					lows.append(geo.height(v.x, v.z) - v.y)
		lows.sort()
		if not lows.is_empty():
			diffs.append(lows[lows.size() / 2])
	if keep.is_empty():
		return []
	diffs.sort()
	var off: float = diffs[int(diffs.size() * 0.3)] if not diffs.is_empty() else 0.0   # rather lower than median: cellars / slopes
	if not diffs.is_empty():
		_note("Höhe korrigiert um %.1f m (10 %%: %.1f, 50 %%: %.1f, 90 %%: %.1f, %d Häuser)" % [off, diffs[int(diffs.size() * 0.1)], diffs[diffs.size() / 2], diffs[int(diffs.size() * 0.9)], diffs.size()])
	# the meshes: 2 × 2 parts (so the camera can leave out what is behind it) × walls / roofs
	# slivers (< 0.02 m²) are left out; on Lite also small details (< 0.25 m²: chimneys, edges): ~20 % fewer triangles, 0.2 % less area
	var lite: bool = preload("res://scripts/quality.gd").lite()
	var min_a2: float = pow(2.0 * (0.25 if lite else 0.02), 2.0)
	# the roofs must face up; else the winding is the other way round (decided first: the facades need the final normals)
	var up_n := 0
	var dn_n := 0
	for kb in keep:
		for t in by[kb[0]]:
			var nrm := (_tv[t * 3 + 2] - _tv[t * 3]).cross(_tv[t * 3 + 1] - _tv[t * 3])
			if nrm.length_squared() >= min_a2 and absf(nrm.normalized().y) > 0.4:
				if nrm.y > 0.0:
					up_n += 1
				else:
					dn_n += 1
	var flip := dn_n > up_n
	# sim-fassaden: facades and roof colours per house (fassaden.gd), only Normal / Hoch, not in a test run / the Prüfstand
	var styled: bool = not lite and preload("res://scripts/fassaden.gd").enabled(geo.main)
	var fas = null
	if styled:
		var cts := PackedVector2Array()
		for kb in keep:
			var cc2 := Vector2.ZERO
			for p in kb[1]:
				cc2 += p
			cts.append(cc2 / (kb[1] as PackedVector2Array).size())
		fas = preload("res://scripts/fassaden.gd").new(geo, cts)
	var parts := {}
	for kb in keep:
		var ts: Array = by[kb[0]]
		var ctr: Vector2 = (kb[1] as PackedVector2Array)[0]
		var walls := []
		var roofs := []
		for t in ts:
			var a := _tv[t * 3] + Vector3(0, off, 0)
			var b := _tv[t * 3 + 1] + Vector3(0, off, 0)
			var cc := _tv[t * 3 + 2] + Vector3(0, off, 0)
			var nrm := (cc - a).cross(b - a)               # flat, matching the winding of Godot (front = clockwise)
			if nrm.length_squared() < min_a2:              # (|cross| = 2 × area)
				continue
			nrm = nrm.normalized()
			if flip:
				var tmp := b
				b = cc
				cc = tmp
				nrm = -nrm
			if absf(nrm.y) > 0.4:
				roofs.append([a, b, cc, nrm])
			else:
				walls.append([a, b, cc, nrm])
		var hull: PackedVector2Array = kb[1]
		var base := float(kb[2]) + off
		var top := float(kb[3]) + off
		var st := {}
		var wp := []
		if styled:
			var lows := []                                  # the eave: low edge of the roofs, by area (small porch roofs do not count)
			var fl_a := 0.0
			var all_a := 0.0
			for rt in roofs:
				var ar: float = ((rt[2] - rt[0]) as Vector3).cross(rt[1] - rt[0]).length() * 0.5
				lows.append([minf(rt[0].y, minf(rt[1].y, rt[2].y)), ar])
				all_a += ar
				if rt[3].y > 0.97:
					fl_a += ar
			lows.sort_custom(func(x, y): return x[0] < y[0])
			var eave := top
			var acc := 0.0
			for lw in lows:
				acc += lw[1]
				if acc >= all_a * 0.25:
					eave = lw[0]
					break
			eave = clampf(eave, base + 2.2, top)
			var cc3 := Vector2.ZERO
			for p in hull:
				cc3 += p
			cc3 /= hull.size()
			st = fas.style(geo.to_ll(cc3), hull, base, top, eave, fl_a / maxf(all_a, 0.01))
			wp = fas.wall_planes(walls, int(st["sid"]))
		for side in [0, 1]:
			var list: Array = walls if side == 0 else roofs
			if list.is_empty():
				continue
			var key := Vector3i(1 if ctr.x >= 0.0 else 0, 1 if ctr.y >= 0.0 else 0, side)
			if not parts.has(key):
				parts[key] = [[], [], [], [], []]           # vertices, normals, colours, custom0, custom1
			var pa: Array = parts[key]
			for i in range(list.size()):
				var tr: Array = list[i]
				pa[0].append_array([tr[0], tr[1], tr[2]])
				pa[1].append_array([tr[3], tr[3], tr[3]])
				if styled:
					if side == 0:
						var wcol: Color = st["wall"]
						wcol.a = (float(st["kind"]) + 0.5) / 16.0
						var c0 := [wp[i][0], wp[i][1], st["base"], st["eave"]]
						var c1 := [st["storey"], float(st["shut"]), st["seed"], wp[i][2]]
						for m in range(3):
							pa[2].append(wcol)
							pa[3].append_array(c0)
							pa[4].append_array(c1)
					else:
						var rcol: Color = st["roof"]
						rcol.a = 1.0 if st["flat"] else 0.0
						for m in range(3):
							pa[2].append(rcol)
							pa[3].append_array([st["seed"], float(st["kind"]), st["base"], st["eave"]])
				tris += 1
		foot.append({"poly": hull, "base": base, "top": top, "kind": int(st.get("kind", -1))})
	var out := []
	for key in parts:
		var pa: Array = parts[key]
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = PackedVector3Array(pa[0])
		arr[Mesh.ARRAY_NORMAL] = PackedVector3Array(pa[1])
		var flags := 0
		if styled:
			arr[Mesh.ARRAY_COLOR] = PackedColorArray(pa[2])
			arr[Mesh.ARRAY_CUSTOM0] = PackedFloat32Array(pa[3])
			flags = Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT
			if key.z == 0:
				arr[Mesh.ARRAY_CUSTOM1] = PackedFloat32Array(pa[4])
				flags |= Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr, [], {}, flags)
		# like the houses of OpenStreetMap: walls «caravan», roofs «stone»; «styled»: the shaders with facades (geo.build)
		out.append({"mesh": am, "t": "stone" if key.z == 1 else "caravan", "roof": key.z == 1, "styled": styled})
	if styled:
		fassaden_stats = fas.stats
		_note("Fassaden: %s; Dachfarbe aus dem Luftbild %d, ausgedacht %d, OSM-Angaben bei %d Häusern" % [str(fas.stats["kinds"]), fas.stats["aerial"], fas.stats["palette"], fas.stats["tags"]])
	_tv = PackedVector3Array()
	_tk = PackedInt32Array()
	return out


static func _key_house(k: int) -> bool:
	"""9999 = triangles without a batch id: then not a single house (do not drop them all)"""
	return k % 10000 != 9999


func _note(t: String) -> void:
	if not t in diag and diag.size() < 12:
		diag.append(t)


static func _gltf_info(glb: PackedByteArray) -> String:
	"""version and extensions of a glb (why it cannot be read)"""
	if glb.size() < 20:
		return "zu kurz"
	var magic := glb.slice(0, 4).get_string_from_ascii()
	var ver := glb.decode_u32(4)
	var jl := glb.decode_u32(12)
	var j = JSON.parse_string(glb.slice(20, 20 + jl).get_string_from_utf8()) if magic == "glTF" else null
	if typeof(j) != TYPE_DICTIONARY:
		return "glb Version %d, Kopf unlesbar" % ver
	var a = j.get("asset", {})
	var av := str(a.get("version", "?")) if typeof(a) == TYPE_DICTIONARY else "?"
	return "glTF %s (glb %d), Erweiterungen: %s" % [av, ver, ", ".join(PackedStringArray(j.get("extensionsRequired", j.get("extensionsUsed", [])))) if typeof(j.get("extensionsUsed", [])) == TYPE_ARRAY else "?"]


static func _unzip(b: PackedByteArray) -> PackedByteArray:
	"""some servers send the files gzip-packed without saying so"""
	if b.size() > 18 and b[0] == 0x1f and b[1] == 0x8b:
		var u := b.decompress_dynamic(-1, FileAccess.COMPRESSION_GZIP)
		if u.size() > 0:
			return u
	return b
