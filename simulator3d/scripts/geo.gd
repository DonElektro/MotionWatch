extends Node
## A real place in Switzerland as a scene (from 3D-3.3). On the map (karte.gd) the user picks the place where Motion Watch
## stands; this loads - on the PC of the user, from the internet - the terrain (swisstopo height model swissALTI3D, else the
## free Terrarium tiles), the aerial picture (swisstopo SWISSIMAGE) and buildings, trees, forests, roads, water, fences and
## hedges (OpenStreetMap, Overpass), keeps everything in user://orte/cache/ (once loaded it works without internet) and
## builds the scene «ort» from it: Motion Watch stands in the middle, north is -z.
## Data: © swisstopo (free use with source, OGD) · © OpenStreetMap contributors (ODbL) · Terrarium: Mapzen / AWS open data.

const NEAR := 200.0              # half side of the detailed square around the head (m)
const NEAR_STEP := 2.5           # grid of the near terrain (m)
const FAR := 1600.0              # half side of the far terrain (only the look: hills, valleys, forests far away)
const FAR_STEP := 25.0
const PROF_N := 81               # swisstopo: 81 profile lines of 81 points = every 5 m
const Z_PHOTO_NEAR := 18         # aerial picture near: ~0.4 m per pixel
const Z_PHOTO_FAR := 15          # far: ~3.3 m per pixel
const Z_DEM_NEAR := 15
const Z_DEM_FAR := 12
const MAX_TREES := 380           # real trees (with trunk, obstacle, thermal picture); more become simple ones (one MultiMesh)
const ER := 6378137.0
const CH_BOX := Rect2(5.9, 45.8, 4.6, 2.05)   # lon, lat, w, h: Switzerland (and a bit around)
const CACHE := "user://orte/cache/"

var main
var base := ""                   # tests: MW3D_GEO_BASE=http://127.0.0.1:8899 sends every request there (host = first folder)
var busy := false
var info := ""                   # what it does now / the last problem (shown in the status line and on the map)
var loaded := false              # the data of a place is ready
var lat := 0.0
var lon := 0.0
var place_name := ""
var m0 := Vector2.ZERO           # mercator metres of the head
var k := 1.0                     # mercator metres -> real metres (cos(latitude))
var h0 := 0.0                    # height above the sea at the head
var dem_source := ""
var near_n := 0
var far_n := 0
var near_h := PackedFloat32Array()
var far_h := PackedFloat32Array()
var photo_near: ImageTexture
var photo_far: ImageTexture
var photo_near_img: Image
var photo_far_img: Image
var rect_near := Rect2()         # local x / z the pictures cover
var rect_far := Rect2()
var osm: Array = []
var counts := {}                 # what was built (for the info line and tests)
var gen := 0                     # a newer load cancels an older one
var b3d_meshes: Array = []       # buildings of swisstopo in 3D (b3d.gd); empty = houses from OpenStreetMap
var b3d_on := true
var _last_err := ""


func _ready() -> void:
	base = OS.get_environment("MW3D_GEO_BASE").trim_suffix("/")
	DirAccess.make_dir_recursive_absolute(CACHE)


# ---- addresses ---------------------------------------------------------------------------------------------------
func url(kind: String, z := 0, x := 0, y := 0) -> String:
	var u := ""
	match kind:
		"photo":
			u = "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/%d/%d/%d.jpeg" % [z, x, y]
		"map":
			u = "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/%d/%d/%d.jpeg" % [z, x, y]
		"dem":
			u = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png" % [z, x, y]
		"overpass":
			u = "https://overpass-api.de/api/interpreter"
		"search":
			u = "https://api3.geo.admin.ch/rest/services/api/SearchServer?type=locations&sr=4326&limit=8&searchText="
		"profile":
			u = "https://api3.geo.admin.ch/rest/services/profile.json"
		"b3d":
			u = "https://3d.geo.admin.ch/ch.swisstopo.swissbuildings3d.3d/v1/tileset.json"
	if base != "":
		u = base + "/" + u.substr(8)
	return u


# ---- coordinates -------------------------------------------------------------------------------------------------
static func merc(la: float, lo: float) -> Vector2:
	"""web mercator metres, y to the south"""
	return Vector2(ER * deg_to_rad(lo), -ER * log(tan(PI / 4.0 + deg_to_rad(la) / 2.0)))


static func unmerc(p: Vector2) -> Vector2:
	"""(lat, lon) of mercator metres"""
	return Vector2(rad_to_deg(2.0 * atan(exp(-p.y / ER)) - PI / 2.0), rad_to_deg(p.x / ER))


static func world_px(p: Vector2, z: int) -> Vector2:
	"""pixel of the whole world map at zoom z (256 per tile)"""
	var s := 256.0 * pow(2.0, z) / (2.0 * PI * ER)
	return Vector2((p.x + PI * ER) * s, (p.y + PI * ER) * s)


static func from_px(px: Vector2, z: int) -> Vector2:
	var s := 256.0 * pow(2.0, z) / (2.0 * PI * ER)
	return Vector2(px.x / s - PI * ER, px.y / s - PI * ER)


func to_local(la: float, lo: float) -> Vector2:
	return (merc(la, lo) - m0) * k


func to_ll(p: Vector2) -> Vector2:
	return unmerc(m0 + p / k)


static func lv95(la: float, lo: float) -> Vector2:
	"""Swiss coordinates (E, N) - approximate formulas of swisstopo (about 1 m)"""
	var p := (la * 3600.0 - 169028.66) / 10000.0
	var l := (lo * 3600.0 - 26782.5) / 10000.0
	var e := 2600072.37 + 211455.93 * l - 10938.51 * l * p - 0.36 * l * p * p - 44.54 * l * l * l
	var n := 1200147.07 + 308807.95 * p + 3745.25 * l * l + 76.63 * p * p - 194.56 * l * l * p + 119.79 * p * p * p
	return Vector2(e, n)


static func in_ch(la: float, lo: float) -> bool:
	return CH_BOX.has_point(Vector2(lo, la))


# ---- downloading (with the cache on the disk) ---------------------------------------------------------------------
func cache_path(u: String, body := "") -> String:
	return CACHE + (u + "|" + body).md5_text() + ".bin"


func fetch(u: String, body := "", use_cache := true, timeout := 40.0) -> PackedByteArray:
	"""the answer of an address (empty if it failed); POST if body is given"""
	var cp := cache_path(u, body)
	if use_cache and FileAccess.file_exists(cp):
		return FileAccess.get_file_as_bytes(cp)
	var h := HTTPRequest.new()
	h.timeout = timeout
	h.use_threads = true
	add_child(h)
	var hd := PackedStringArray(["User-Agent: MotionWatch3D-Simulator/%s (github.com/DonElektro/MotionWatch)" % str(main.VERSION)])
	var err := OK
	if body != "":
		hd.append("Content-Type: application/x-www-form-urlencoded")
		err = h.request(u, hd, HTTPClient.METHOD_POST, body)
	else:
		err = h.request(u, hd)
	if err != OK:
		h.queue_free()
		_last_err = "Anfrage nicht möglich (%d)" % err
		return PackedByteArray()
	var r: Array = await h.request_completed
	h.queue_free()
	if int(r[0]) != HTTPRequest.RESULT_SUCCESS or int(r[1]) != 200:
		_last_err = "keine Verbindung" if int(r[0]) != HTTPRequest.RESULT_SUCCESS else "Antwort %d" % int(r[1])
		_last_err += " (" + u.get_slice("/", 2) + ")"
		return PackedByteArray()
	var data: PackedByteArray = r[3]
	if use_cache and data.size() > 0:
		var f := FileAccess.open(cp, FileAccess.WRITE)
		if f != null:
			f.store_buffer(data)
	return data


func fetch_many(jobs: Array, label: String, my_gen: int) -> Array:
	"""several downloads at once (4 at a time); jobs: [url, body]"""
	var res := []
	res.resize(jobs.size())
	var st := {"next": 0, "done": 0}
	for _w in range(min(4, jobs.size())):
		_worker(jobs, res, st, label, my_gen)
	while st["done"] < jobs.size():
		await get_tree().process_frame
		if my_gen != gen:
			return []
	return res


func _worker(jobs: Array, res: Array, st: Dictionary, label: String, my_gen: int) -> void:
	while st["next"] < jobs.size() and my_gen == gen:
		var i: int = st["next"]
		st["next"] += 1
		res[i] = await fetch(jobs[i][0], jobs[i][1] if jobs[i].size() > 1 else "")
		st["done"] += 1
		info = "%s … %d von %d" % [label, st["done"], jobs.size()]
	if my_gen != gen:
		st["done"] = jobs.size()


func search(text: String) -> Array:
	"""places of swisstopo for a name: [{label, lat, lon}]"""
	var t := text.strip_edges()
	if t == "":
		return []
	var data := await fetch(url("search") + t.uri_encode(), "", false, 15.0)
	var d = JSON.parse_string(data.get_string_from_utf8()) if data.size() > 0 else null
	var out := []
	if typeof(d) == TYPE_DICTIONARY and typeof(d.get("results")) == TYPE_ARRAY:
		for r in d["results"]:
			var a = r.get("attrs", {}) if typeof(r) == TYPE_DICTIONARY else {}
			if typeof(a) != TYPE_DICTIONARY or not a.has("lat"):
				continue
			var lab := str(a.get("label", "")).replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
			out.append({"label": lab, "lat": float(a["lat"]), "lon": float(a["lon"])})
	elif data.size() == 0:
		info = "Ortssuche: " + _last_err
	return out


# ---- a mosaic of map tiles -----------------------------------------------------------------------------------------
func _plan(kind: String, z: int, r: Rect2) -> Dictionary:
	"""the tiles that cover the local rectangle r"""
	var a := world_px(m0 + r.position / k, z)
	var b := world_px(m0 + r.end / k, z)
	var tx0 := int(floor(a.x / 256.0))
	var ty0 := int(floor(a.y / 256.0))
	var tx1 := int(floor(b.x / 256.0))
	var ty1 := int(floor(b.y / 256.0))
	var jobs := []
	for ty in range(ty0, ty1 + 1):
		for tx in range(tx0, tx1 + 1):
			jobs.append([url(kind, z, tx, ty)])
	return {"kind": kind, "z": z, "tx0": tx0, "ty0": ty0, "nx": tx1 - tx0 + 1, "ny": ty1 - ty0 + 1, "a": a, "b": b, "jobs": jobs}


func _stitch(p: Dictionary, data: Array) -> Dictionary:
	"""one picture of the tiles, cut to the rectangle; {img, rect (local), missing}"""
	var nx: int = p["nx"]
	var ny: int = p["ny"]
	var img := Image.create(nx * 256, ny * 256, false, Image.FORMAT_RGB8)
	img.fill(Color(0.35, 0.42, 0.28) if p["kind"] == "photo" else Color(0.5, 0.0, 0.0))   # terrarium red 128 = 0 m
	var missing := 0
	for i in range(data.size()):
		var bytes = data[i]
		var ti := Image.new()
		var ok := ERR_INVALID_DATA
		if typeof(bytes) == TYPE_PACKED_BYTE_ARRAY and bytes.size() > 0:
			ok = ti.load_png_from_buffer(bytes) if p["kind"] == "dem" else ti.load_jpg_from_buffer(bytes)
			if ok != OK:
				ok = ti.load_jpg_from_buffer(bytes) if p["kind"] == "dem" else ti.load_png_from_buffer(bytes)
		if ok != OK:
			missing += 1
			continue
		ti.convert(Image.FORMAT_RGB8)
		if ti.get_width() != 256:
			ti.resize(256, 256)
		img.blit_rect(ti, Rect2i(0, 0, 256, 256), Vector2i((i % nx) * 256, (i / nx) * 256))
	var org := Vector2(p["tx0"] * 256.0, p["ty0"] * 256.0)
	var a: Vector2 = (p["a"] as Vector2) - org
	var b: Vector2 = (p["b"] as Vector2) - org
	var cut := Rect2i(Vector2i(int(floor(a.x)), int(floor(a.y))), Vector2i(int(ceil(b.x)) - int(floor(a.x)), int(ceil(b.y)) - int(floor(a.y))))
	cut = cut.intersection(Rect2i(0, 0, img.get_width(), img.get_height()))
	var out := img.get_region(cut)
	var z: int = p["z"]
	var lo: Vector2 = (from_px(org + Vector2(cut.position), z) - m0) * k
	var hi: Vector2 = (from_px(org + Vector2(cut.end), z) - m0) * k
	return {"img": out, "rect": Rect2(lo, hi - lo), "missing": missing}


static func _terrarium(img: Image, rect: Rect2, p: Vector2) -> float:
	"""height (m above the sea) at the local point p, bilinear"""
	var u := (p.x - rect.position.x) / rect.size.x * img.get_width() - 0.5
	var v := (p.y - rect.position.y) / rect.size.y * img.get_height() - 0.5
	var x0 := clampi(int(floor(u)), 0, img.get_width() - 1)
	var y0 := clampi(int(floor(v)), 0, img.get_height() - 1)
	var x1 := mini(x0 + 1, img.get_width() - 1)
	var y1 := mini(y0 + 1, img.get_height() - 1)
	var fx := clampf(u - floor(u), 0.0, 1.0)
	var fy := clampf(v - floor(v), 0.0, 1.0)
	var hs := []
	for q in [Vector2i(x0, y0), Vector2i(x1, y0), Vector2i(x0, y1), Vector2i(x1, y1)]:
		var c := img.get_pixelv(q)
		hs.append(roundf(c.r * 255.0) * 256.0 + roundf(c.g * 255.0) + c.b * 255.0 / 256.0 - 32768.0)
	return lerpf(lerpf(hs[0], hs[1], fx), lerpf(hs[2], hs[3], fx), fy)


# ---- loading a place ---------------------------------------------------------------------------------------------
func load_place(la: float, lo: float, nm: String, rebuild := true) -> void:
	"""everything for the place (from the cache or the internet); then the scene «ort» is built"""
	if not in_ch(la, lo):
		info = "Dieser Punkt liegt nicht in der Schweiz."
		return
	gen += 1
	var my_gen := gen
	busy = true
	loaded = false
	lat = la
	lon = lo
	place_name = nm if nm != "" else "%.5f, %.5f" % [la, lo]
	k = cos(deg_to_rad(la))
	m0 = merc(la, lo)
	counts = {}
	var rn := Rect2(-NEAR, -NEAR, 2 * NEAR, 2 * NEAR).grow(8.0)
	var rf := Rect2(-FAR, -FAR, 2 * FAR, 2 * FAR).grow(40.0)
	var plans := [_plan("dem", Z_DEM_NEAR, rn), _plan("dem", Z_DEM_FAR, rf), _plan("photo", Z_PHOTO_NEAR, rn), _plan("photo", Z_PHOTO_FAR, rf)]
	var jobs := []
	for p in plans:
		jobs.append_array(p["jobs"])
	# OpenStreetMap: buildings, trees, forests, roads, water, fences in the near square
	var a := to_ll(Vector2(-NEAR - 30, NEAR + 30))
	var b := to_ll(Vector2(NEAR + 30, -NEAR - 30))
	var q := ("[out:json][timeout:90][bbox:%.6f,%.6f,%.6f,%.6f];(way[building];relation[building];way[highway];way[natural];relation[natural~\"wood|water|scrub\"];"
			+ "way[landuse];relation[landuse~\"forest|orchard\"];way[waterway];node[natural=tree];way[barrier];way[leisure~\"pitch|swimming_pool|park\"];way[amenity=parking];);out geom;") % [a.x, a.y, b.x, b.y]
	var ov_body := "data=" + q.uri_encode()
	jobs.append([url("overpass"), ov_body])
	info = "Lade Gelände, Luftbild und Gebäude"
	var res: Array = await fetch_many(jobs, "Lade Gelände, Luftbild und Gebäude", my_gen)
	if my_gen != gen:
		return
	var at := 0
	var got := []
	for p in plans:
		var n: int = p["jobs"].size()
		got.append(_stitch(p, res.slice(at, at + n)))
		at += n
	var ov: PackedByteArray = res[at]
	var problems := []
	if got[0]["missing"] > 0 or got[1]["missing"] > 0:
		problems.append("Höhen fehlen")
	if got[2]["missing"] * 2 > (plans[2]["jobs"] as Array).size():
		problems.append("Luftbild fehlt")
	if got[0]["missing"] == plans[0]["jobs"].size() and got[2]["missing"] == plans[2]["jobs"].size() and ov.size() == 0:
		busy = false
		info = "Laden nicht möglich: " + _last_err + " – Internet da?"
		return
	# OpenStreetMap
	osm = []
	var d = JSON.parse_string(ov.get_string_from_utf8()) if ov.size() > 0 else null
	if typeof(d) == TYPE_DICTIONARY and typeof(d.get("elements")) == TYPE_ARRAY:
		osm = d["elements"]
	else:
		problems.append("Gebäude fehlen (OpenStreetMap)")
		DirAccess.remove_absolute(cache_path(url("overpass"), ov_body))  # next time again
	# heights: Terrarium first (near and far), then swisstopo profiles (swissALTI3D, much finer) if they come
	var dn: Dictionary = got[0]
	var df: Dictionary = got[1]
	near_n = int(round(2 * NEAR / NEAR_STEP)) + 1
	far_n = int(round(2 * FAR / FAR_STEP)) + 1
	near_h.resize(near_n * near_n)
	for j in range(near_n):
		for i in range(near_n):
			near_h[j * near_n + i] = _terrarium(dn["img"], dn["rect"], Vector2(-NEAR + i * NEAR_STEP, -NEAR + j * NEAR_STEP))
	dem_source = "Terrarium (grob)"
	var fine: PackedFloat32Array = await _swiss_heights(my_gen)
	if my_gen != gen:
		return
	var off := 0.0
	if fine.size() == PROF_N * PROF_N:
		var sum := 0.0
		var cnt := 0
		var tera := near_h.duplicate()
		var s := (2 * NEAR) / float(PROF_N - 1)
		for j in range(near_n):
			for i in range(near_n):
				var u := (i * NEAR_STEP) / s
				var v := (j * NEAR_STEP) / s
				var i0 := mini(int(u), PROF_N - 2)
				var j0 := mini(int(v), PROF_N - 2)
				var fu := u - i0
				var fv := v - j0
				var h := lerpf(lerpf(fine[j0 * PROF_N + i0], fine[j0 * PROF_N + i0 + 1], fu), lerpf(fine[(j0 + 1) * PROF_N + i0], fine[(j0 + 1) * PROF_N + i0 + 1], fu), fv)
				near_h[j * near_n + i] = h
				sum += h - tera[j * near_n + i]
				cnt += 1
		off = sum / max(1, cnt)
		dem_source = "swisstopo swissALTI3D"
	else:
		problems.append("feine Höhen von swisstopo fehlen, grobe genommen")
	h0 = near_h[(near_n / 2) * near_n + near_n / 2]
	for i in range(near_h.size()):
		near_h[i] -= h0
	far_h.resize(far_n * far_n)
	for j in range(far_n):
		for i in range(far_n):
			var p := Vector2(-FAR + i * FAR_STEP, -FAR + j * FAR_STEP)
			if abs(p.x) <= NEAR + 0.01 and abs(p.y) <= NEAR + 0.01:
				far_h[j * far_n + i] = height(p.x, p.y, true)
			else:
				far_h[j * far_n + i] = _terrarium(df["img"], df["rect"], p) + off - h0
	# buildings of swisstopo in 3D (from 3D-3.10), else the houses of OpenStreetMap
	b3d_meshes = []
	if b3d_on:
		var keep := []                                     # the house round Motion Watch is left out
		for e in osm:
			if typeof(e) == TYPE_DICTIONARY and typeof(e.get("tags")) == TYPE_DICTIONARY and e["tags"].has("building"):
				for poly in _polys(e):
					if Geometry2D.is_point_in_polygon(Vector2.ZERO, poly):
						for grown in Geometry2D.offset_polygon(poly, 0.8):   # a bit bigger: also its walls go
							keep.append(grown)
		var b3 = load("res://scripts/b3d.gd").new()
		b3d_meshes = await b3.fetch_buildings(self, my_gen, keep)
		if my_gen != gen:
			return
		if b3d_meshes.is_empty() and b3.info != "":
			problems.append(b3.info.trim_prefix("3D-Gebäude: "))
		elif not b3d_meshes.is_empty():
			problems.append("Häuser in 3D von swisstopo")
	# aerial pictures
	photo_near_img = got[2]["img"]
	photo_near_img.generate_mipmaps()
	photo_near = ImageTexture.create_from_image(photo_near_img)
	rect_near = got[2]["rect"]
	photo_far_img = got[3]["img"]
	photo_far_img.generate_mipmaps()
	photo_far = ImageTexture.create_from_image(photo_far_img)
	rect_far = got[3]["rect"]
	busy = false
	loaded = true
	info = place_name + " geladen (Höhen: " + dem_source + ")" + (" – " + ", ".join(problems) if not problems.is_empty() else "")
	if rebuild:
		main.place_loaded()


func _swiss_heights(my_gen: int) -> PackedFloat32Array:
	"""81 × 81 heights of swissALTI3D (profile service of swisstopo), rows from north to south; empty if it fails"""
	var jobs := []
	var lens := []
	for j in range(PROF_N):
		var z := -NEAR + j * (2 * NEAR) / float(PROF_N - 1)
		var la := to_ll(Vector2(-NEAR, z))
		var lb := to_ll(Vector2(NEAR, z))
		var ea := lv95(la.x, la.y)
		var eb := lv95(lb.x, lb.y)
		lens.append(ea.distance_to(eb))
		var geom := '{"type":"LineString","coordinates":[[%.2f,%.2f],[%.2f,%.2f]]}' % [ea.x, ea.y, eb.x, eb.y]
		jobs.append([url("profile") + "?sr=2056&nb_points=%d&geom=%s" % [PROF_N, geom.uri_encode()]])
	var res: Array = await fetch_many(jobs, "Lade genaue Höhen (swisstopo)", my_gen)
	var out := PackedFloat32Array()
	if res.size() != PROF_N:
		return out
	out.resize(PROF_N * PROF_N)
	for j in range(PROF_N):
		var bytes = res[j]
		var d = JSON.parse_string(bytes.get_string_from_utf8()) if typeof(bytes) == TYPE_PACKED_BYTE_ARRAY and bytes.size() > 0 else null
		if typeof(d) != TYPE_ARRAY or (d as Array).size() < 2:
			DirAccess.remove_absolute(cache_path(jobs[j][0]))
			return PackedFloat32Array()
		var ds := PackedFloat32Array()
		var hs := PackedFloat32Array()
		for pt in d:
			if typeof(pt) != TYPE_DICTIONARY:
				continue
			var al = pt.get("alts", {})
			var h = null
			if typeof(al) == TYPE_DICTIONARY:
				for key in ["DTM2", "COMB", "DTM25"]:
					if al.get(key) != null:
						h = float(al[key])
						break
			if h == null:
				continue
			ds.append(float(pt.get("dist", ds.size())))
			hs.append(h)
		if hs.size() < 2:
			return PackedFloat32Array()
		var total: float = max(ds[ds.size() - 1], 1.0)
		var at := 0
		for i in range(PROF_N):
			var want := float(i) / float(PROF_N - 1) * total
			while at < ds.size() - 2 and ds[at + 1] < want:
				at += 1
			var f := clampf((want - ds[at]) / max(0.001, ds[at + 1] - ds[at]), 0.0, 1.0)
			out[j * PROF_N + i] = lerpf(hs[at], hs[at + 1], f)
	return out


# ---- heights for everything that walks / stands on the ground --------------------------------------------------------
func height(x: float, z: float, near_only := false) -> float:
	if near_n > 0 and abs(x) <= NEAR and abs(z) <= NEAR:
		return _grid(near_h, near_n, NEAR, NEAR_STEP, x, z)
	if near_only or far_n == 0:
		return 0.0
	return _grid(far_h, far_n, FAR, FAR_STEP, clampf(x, -FAR, FAR), clampf(z, -FAR, FAR))


static func _grid(g: PackedFloat32Array, n: int, half: float, step: float, x: float, z: float) -> float:
	var u := (x + half) / step
	var v := (z + half) / step
	var i0 := clampi(int(floor(u)), 0, n - 2)
	var j0 := clampi(int(floor(v)), 0, n - 2)
	var fu := clampf(u - i0, 0.0, 1.0)
	var fv := clampf(v - j0, 0.0, 1.0)
	return lerpf(lerpf(g[j0 * n + i0], g[j0 * n + i0 + 1], fu), lerpf(g[(j0 + 1) * n + i0], g[(j0 + 1) * n + i0 + 1], fu), fv)


func photo_color(x: float, z: float) -> Color:
	"""colour of the aerial picture at a local point"""
	var img := photo_near_img if rect_near.has_point(Vector2(x, z)) else photo_far_img
	var r := rect_near if img == photo_near_img else rect_far
	if img == null:
		return Color(0.3, 0.4, 0.25)
	var px := Vector2i(clampi(int((x - r.position.x) / r.size.x * img.get_width()), 0, img.get_width() - 1),
			clampi(int((z - r.position.y) / r.size.y * img.get_height()), 0, img.get_height() - 1))
	return img.get_pixelv(px)


static func is_tree_color(c: Color) -> bool:
	"""dark green of tree crowns in the aerial picture (meadows are lighter)"""
	return c.g > c.r * 1.02 and c.g > c.b * 1.05 and c.get_luminance() < 0.24 and c.get_luminance() > 0.04


static func is_green(c: Color) -> bool:
	return c.g > c.r * 0.98 and c.g > c.b * 1.08


# ---- building the scene ------------------------------------------------------------------------------------------
var sc                           # scenes.gd while building
var rng := RandomNumberGenerator.new()
var buildings: Array = []        # [{poly, cx, top}] for tests and «not inside a house»


func build(s) -> void:
	"""the scene «ort» below s.root (scenes.gd)"""
	sc = s
	rng.seed = int(abs(lat * 1000.0 + lon * 77.0) * 1000.0) % 100000
	counts = {}
	buildings = []
	road_segs = {}
	_terrain_meshes()
	if not b3d_meshes.is_empty():
		var bm := ShaderMaterial.new()
		bm.shader = load("res://shaders/b3d.gdshader")
		for mesh in b3d_meshes:
			main.add_mesh(sc.root, mesh, Vector3.ZERO, bm, "caravan")
		b3d_mat = bm
		main.anims.append(_b3d_night)
		counts["b3d"] = b3d_meshes.size()
	var trees_at := []                                  # [pos, size, conifer, prio]
	var roads := []
	var head_in := false
	for e in osm:
		if typeof(e) != TYPE_DICTIONARY:
			continue
		var tg = e.get("tags", {})
		if typeof(tg) != TYPE_DICTIONARY:
			tg = {}
		if tg.has("building") and str(tg.get("building")) != "no":
			for poly in _polys(e):
				if Geometry2D.is_point_in_polygon(Vector2.ZERO, poly):
					head_in = true
					continue                                # Motion Watch stands here: no house round it
				_building(poly, tg)
		elif tg.has("highway") and e.get("type") == "way" and str(tg.get("area", "")) != "yes" and str(tg.get("tunnel", "")) != "yes":
			roads.append([_line(e), tg])
		elif str(tg.get("natural", "")) == "tree" and e.get("type") == "node":
			var p := to_local(float(e["lat"]), float(e["lon"]))
			trees_at.append([p, rng.randf_range(1.0, 1.5), -1, 0])
		elif str(tg.get("natural", "")) == "tree_row":
			var ln := _line(e)
			for p in _along(ln, 7.0):
				trees_at.append([p, rng.randf_range(0.9, 1.3), 0, 1])
		elif str(tg.get("natural", "")) in ["wood", "scrub"] or str(tg.get("landuse", "")) in ["forest", "orchard"]:
			var orchard := str(tg.get("landuse", "")) == "orchard"
			var conif := 1 if str(tg.get("leaf_type", "")) == "needleleaved" else (0 if str(tg.get("leaf_type", "")) == "broadleaved" or orchard else -1)
			for poly in _polys(e):
				for p in _fill(poly, 10.0 if orchard else 6.0):
					trees_at.append([p, rng.randf_range(0.6, 0.9) if orchard else rng.randf_range(0.9, 1.6), conif, 2])
		elif str(tg.get("natural", "")) == "water" or str(tg.get("leisure", "")) == "swimming_pool" or str(tg.get("landuse", "")) in ["reservoir", "basin"]:
			for poly in _polys(e):
				_water(poly)
		elif tg.has("waterway") and e.get("type") == "way":
			var w := {"river": 8.0, "canal": 6.0, "stream": 1.6, "ditch": 0.8, "drain": 0.8}.get(str(tg.get("waterway")), 0.0) as float
			if w > 0.0 and str(tg.get("tunnel", "")) != "culvert":
				_ribbon(_line(e), w, 0.03, "water", Color(0.2, 0.3, 0.33))
		elif tg.has("barrier") and e.get("type") == "way":
			_barrier(_line(e), str(tg.get("barrier")))
	for r in roads:
		_road(r[0], r[1])
	_finish_ribbons()
	# trees seen in the aerial picture (gardens, hedges, single trees nobody put into OpenStreetMap)
	if photo_near_img != null:
		var stp := 6.0
		var z := -NEAR + 3.0
		while z < NEAR:
			var x := -NEAR + 3.0
			while x < NEAR:
				var p := Vector2(x + rng.randf_range(-2.5, 2.5), z + rng.randf_range(-2.5, 2.5))
				if is_tree_color(photo_color(p.x, p.y)) and is_tree_color(photo_color(p.x + 1.5, p.y)) and is_tree_color(photo_color(p.x, p.y + 1.5)):
					trees_at.append([p, rng.randf_range(0.8, 1.4), -1, 3])
				x += stp
			z += stp
	_trees(trees_at)
	_far_trees()
	_camp()
	if head_in:
		main.geo_note = "Motion Watch steht in einem Gebäude – das Gebäude wurde weggelassen."
	counts["trees"] = counts.get("trees", 0)
	sc = null


var b3d_mat: ShaderMaterial


func _b3d_night(_dt, _t):
	"""windows of the swisstopo houses light up at night"""
	if b3d_mat != null:
		b3d_mat.set_shader_parameter("night", 1.2 if main.is_dark() else 0.0)
	return false


func _terrain_meshes() -> void:
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/terrain.gdshader")
	tm.set_shader_parameter("photo", photo_near)
	tm.set_shader_parameter("rect", Vector4(rect_near.position.x, rect_near.position.y, rect_near.size.x, rect_near.size.y))
	tm.set_shader_parameter("noise_tex", main.noise_tex)
	var fm := ShaderMaterial.new()
	fm.shader = tm.shader
	fm.set_shader_parameter("photo", photo_far)
	fm.set_shader_parameter("rect", Vector4(rect_far.position.x, rect_far.position.y, rect_far.size.x, rect_far.size.y))
	fm.set_shader_parameter("noise_tex", main.noise_tex)
	fm.set_shader_parameter("detail", 0.0)
	main.ground_mats = [tm, fm]
	var near := _grid_mesh(near_h, near_n, NEAR, NEAR_STEP, false, true)
	var far := _grid_mesh(far_h, far_n, FAR, FAR_STEP, true, false)
	for pair in [[near, tm], [far, fm]]:
		var mi: MeshInstance3D = main.add_mesh(sc.root, pair[0], Vector3.ZERO, pair[1], "x")
		var th: MeshInstance3D = sc.root.get_child(sc.root.get_child_count() - 1)
		th.material_override = main.tmats["ground"]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if pair[0] == far else GeometryInstance3D.SHADOW_CASTING_SETTING_ON


func _grid_mesh(g: PackedFloat32Array, n: int, half: float, step: float, hole: bool, skirt: bool) -> ArrayMesh:
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	verts.resize(n * n)
	norms.resize(n * n)
	for j in range(n):
		for i in range(n):
			var hx := g[j * n + mini(i + 1, n - 1)] - g[j * n + maxi(i - 1, 0)]
			var hz := g[mini(j + 1, n - 1) * n + i] - g[maxi(j - 1, 0) * n + i]
			verts[j * n + i] = Vector3(-half + i * step, g[j * n + i], -half + j * step)
			norms[j * n + i] = Vector3(-hx, 2.0 * step, -hz).normalized()
	var idx := PackedInt32Array()
	for j in range(n - 1):
		for i in range(n - 1):
			if hole:
				var cx0 := -half + i * step
				var cz0 := -half + j * step
				if cx0 >= -NEAR - 0.01 and cx0 + step <= NEAR + 0.01 and cz0 >= -NEAR - 0.01 and cz0 + step <= NEAR + 0.01:
					continue
			var a := j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	if skirt:                                            # a strip down along the edge: no gap to the far terrain
		var ring := []
		for i in range(n):
			ring.append(i)
		for j in range(1, n):
			ring.append(j * n + n - 1)
		for i in range(n - 2, -1, -1):
			ring.append((n - 1) * n + i)
		for j in range(n - 2, 0, -1):
			ring.append(j * n)
		ring.append(0)
		var base_i := verts.size()
		for r in ring:
			verts.append(verts[r] - Vector3(0, 4.0, 0))
			norms.append(norms[r])
		for q in range(ring.size() - 1):
			var a: int = ring[q]
			var b: int = ring[q + 1]
			idx.append_array([a, base_i + q, b, b, base_i + q, base_i + q + 1])
	if hole:                                             # far edge: a wide flat ring out to the horizon (no gap to the sky)
		var ring2 := []
		for i in range(n):
			ring2.append(i)
		for j in range(1, n):
			ring2.append(j * n + n - 1)
		for i in range(n - 2, -1, -1):
			ring2.append((n - 1) * n + i)
		for j in range(n - 2, 0, -1):
			ring2.append(j * n)
		ring2.append(0)
		var b2 := verts.size()
		for r in ring2:
			var v: Vector3 = verts[r]
			verts.append(Vector3(v.x * 4.0, v.y - 30.0, v.z * 4.0))
			norms.append(Vector3.UP)
		for q in range(ring2.size() - 1):
			var a: int = ring2[q]
			var b: int = ring2[q + 1]
			idx.append_array([a, b, b2 + q, b, b2 + q + 1, b2 + q])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


# ---- OpenStreetMap shapes ----------------------------------------------------------------------------------------
func _line(e: Dictionary) -> PackedVector2Array:
	var out := PackedVector2Array()
	var g = e.get("geometry", [])
	if typeof(g) != TYPE_ARRAY:
		return out
	for pt in g:
		if typeof(pt) == TYPE_DICTIONARY and pt.has("lat"):
			out.append(to_local(float(pt["lat"]), float(pt["lon"])))
	return out


func _polys(e: Dictionary) -> Array:
	"""the outer rings of a way or a multipolygon relation (local, without the closing point)"""
	var out := []
	if e.get("type") == "way":
		var l := _line(e)
		if l.size() >= 4 and l[0].distance_to(l[l.size() - 1]) < 0.5:
			l.remove_at(l.size() - 1)
			out.append(l)
		return out
	var parts := []
	for mb in e.get("members", []):
		if typeof(mb) == TYPE_DICTIONARY and str(mb.get("role", "outer")) in ["outer", ""] and mb.get("type") == "way":
			var l2 := _line(mb)
			if l2.size() >= 2:
				parts.append(l2)
	while not parts.is_empty():                          # join the pieces into rings
		var ring: PackedVector2Array = parts.pop_back()
		var grew := true
		while grew and ring[0].distance_to(ring[ring.size() - 1]) > 0.5:
			grew = false
			for i in range(parts.size()):
				var pc: PackedVector2Array = parts[i]
				var end := ring[ring.size() - 1]
				if pc[0].distance_to(end) < 0.5:
					ring.append_array(pc.slice(1))
				elif pc[pc.size() - 1].distance_to(end) < 0.5:
					var rv := pc.duplicate()
					rv.reverse()
					ring.append_array(rv.slice(1))
				else:
					continue
				parts.remove_at(i)
				grew = true
				break
		if ring.size() >= 4 and ring[0].distance_to(ring[ring.size() - 1]) <= 0.5:
			ring.remove_at(ring.size() - 1)
			out.append(ring)
	return out


func _clip(poly: PackedVector2Array, half: float) -> Array:
	var sq := PackedVector2Array([Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half)])
	return Geometry2D.intersect_polygons(poly, sq)


func _fill(poly: PackedVector2Array, step: float) -> Array:
	"""points spread inside a polygon (only in the near square)"""
	var out := []
	for cp in _clip(poly, NEAR):
		var r := Rect2(cp[0], Vector2.ZERO)
		for p in cp:
			r = r.expand(p)
		var z := r.position.y + step * 0.5
		while z < r.end.y:
			var x := r.position.x + step * 0.5
			while x < r.end.x:
				var p := Vector2(x + rng.randf_range(-0.4, 0.4) * step, z + rng.randf_range(-0.4, 0.4) * step)
				if Geometry2D.is_point_in_polygon(p, cp):
					out.append(p)
				x += step
			z += step
	return out


func _along(l: PackedVector2Array, step: float) -> Array:
	var out := []
	var rest := 0.0
	for i in range(l.size() - 1):
		var a := l[i]
		var b := l[i + 1]
		var d := a.distance_to(b)
		var t := rest
		while t < d:
			out.append(a.lerp(b, t / d))
			t += step
		rest = t - d
	return out


static func _area(poly: PackedVector2Array) -> float:
	var s := 0.0
	for i in range(poly.size()):
		var a := poly[i]
		var b := poly[(i + 1) % poly.size()]
		s += a.x * b.y - b.x * a.y
	return s / 2.0


static func _min_rect(poly: PackedVector2Array) -> Dictionary:
	"""the smallest turned rectangle round a polygon: {c, u (long side), a, b (half lengths, a >= b)}"""
	var best := {}
	var best_area := INF
	for i in range(poly.size()):
		var e := poly[(i + 1) % poly.size()] - poly[i]
		if e.length() < 0.3:
			continue
		var u := e.normalized()
		var v := Vector2(-u.y, u.x)
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for p in poly:
			var q := Vector2(p.dot(u), p.dot(v))
			lo = Vector2(min(lo.x, q.x), min(lo.y, q.y))
			hi = Vector2(max(hi.x, q.x), max(hi.y, q.y))
		var ar := (hi.x - lo.x) * (hi.y - lo.y)
		if ar < best_area:
			best_area = ar
			var mid := (lo + hi) / 2.0
			var c := u * mid.x + v * mid.y
			var a := (hi.x - lo.x) / 2.0
			var b := (hi.y - lo.y) / 2.0
			if a >= b:
				best = {"c": c, "u": u, "a": a, "b": b, "area": ar}
			else:
				best = {"c": c, "u": v, "a": b, "b": a, "area": ar}
	return best


# ---- buildings ---------------------------------------------------------------------------------------------------
const WALLS := [Color(0.93, 0.91, 0.86), Color(0.9, 0.86, 0.76), Color(0.96, 0.95, 0.93), Color(0.82, 0.78, 0.7), Color(0.88, 0.84, 0.8), Color(0.62, 0.45, 0.3)]
const ROOFS := [Color(0.52, 0.24, 0.17), Color(0.36, 0.25, 0.2), Color(0.32, 0.33, 0.35), Color(0.6, 0.32, 0.22)]
var wall_st := {}                # colour index -> SurfaceTool
var roof_st := {}
var plain_st: SurfaceTool        # sheds, garages: no windows


func _st(d: Dictionary, key) -> SurfaceTool:
	if not d.has(key):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		d[key] = st
	return d[key]


static func _num(v) -> float:
	var s := str(v).replace(",", ".").strip_edges()
	var t := ""
	for ch in s:
		if ch in "0123456789.":
			t += ch
		else:
			break
	return float(t) if t != "" and t != "." else 0.0


func _building(poly: PackedVector2Array, tg: Dictionary) -> void:
	if abs(poly[0].x) > NEAR + 25.0 or abs(poly[0].y) > NEAR + 25.0:
		return
	var ar: float = abs(_area(poly))
	if ar < 6.0:
		return
	var kind := str(tg.get("building", "yes"))
	var h := _num(tg.get("height", ""))
	var lv := _num(tg.get("building:levels", ""))
	var roof_lv := _num(tg.get("roof:levels", ""))
	if h <= 0.0:
		if lv > 0.0:
			h = lv * 2.9 + roof_lv * 2.0
		else:
			h = {"garage": 2.6, "garages": 2.6, "shed": 2.6, "carport": 2.6, "hut": 3.0, "cabin": 3.5, "roof": 3.5, "barn": 7.5, "farm_auxiliary": 6.5,
					"stable": 6.0, "apartments": 12.0, "church": 14.0, "chapel": 7.0, "commercial": 9.0, "industrial": 8.0, "retail": 6.0, "school": 10.0,
					"house": 6.5, "detached": 6.5, "residential": 8.5, "farm": 8.0, "semidetached_house": 7.0, "terrace": 8.0}.get(kind, 6.5 if ar < 250 else 8.5)
	var shape := str(tg.get("roof:shape", ""))
	var r := _min_rect(poly)
	var rectish: bool = not r.is_empty() and ar > float(r["area"]) * 0.82
	var gable := shape in ["gabled", "hipped", "half-hipped", "gambrel", "mansard"] or (shape == "" and rectish and ar < 900.0 and not kind in ["garage", "garages", "carport", "commercial", "industrial", "retail", "roof"])
	var roof_h := 0.0
	if gable and not r.is_empty():
		roof_h = clampf(float(r["b"]) * 0.75, 1.2, 6.0)
		if lv <= 0.0 and _num(tg.get("height", "")) <= 0.0:
			h = max(2.4, h - roof_h * 0.6)                 # the default height includes some roof
		elif _num(tg.get("height", "")) > 0.0:
			h = max(2.4, h - roof_h)
	var lo := INF
	var hi := -INF
	for p in poly:
		var gy: float = height(p.x, p.y)
		lo = min(lo, gy)
		hi = max(hi, gy)
	var y0 := lo - 0.4
	var top := hi + h
	if not b3d_meshes.is_empty():                      # swisstopo draws the house: only the obstacle
		if not r.is_empty():
			var c0 := Vector3(r["c"].x, 0, r["c"].y)
			main.add_obstacle_box(c0, 2.0 * float(r["a"]) + 0.3, 2.0 * float(r["b"]) + 0.3, -atan2((r["u"] as Vector2).y, (r["u"] as Vector2).x))
			main.set_obstacle_height(hi + h + roof_h - lo)
		buildings.append({"poly": poly, "top": hi + h + roof_h, "h": h})
		counts["buildings"] = counts.get("buildings", 0) + 1
		return
	var plain := h < 3.6 or kind in ["garage", "garages", "shed", "carport", "roof", "barn", "farm_auxiliary", "stable"]
	var ci := rng.randi_range(0, 4) if not kind in ["barn", "farm_auxiliary", "stable", "shed", "hut", "cabin"] else 5
	var st := _st(wall_st, ci) if not plain else _st(wall_st, "plain%d" % ci)
	var wall := poly
	if gable and not r.is_empty():                        # a point where an edge crosses the ridge: the tip of the gable
		wall = PackedVector2Array()
		var u0: Vector2 = r["u"]
		var v0 := Vector2(-u0.y, u0.x)
		for i in range(poly.size()):
			var a := poly[i]
			var b := poly[(i + 1) % poly.size()]
			wall.append(a)
			var qa: float = (a - (r["c"] as Vector2)).dot(v0)
			var qb: float = (b - (r["c"] as Vector2)).dot(v0)
			if qa * qb < 0.0:
				wall.append(a.lerp(b, qa / (qa - qb)))
	var dist := 0.0
	for i in range(wall.size()):
		var a := wall[i]
		var b := wall[(i + 1) % wall.size()]
		var ln := a.distance_to(b)
		if ln < 0.05:
			continue
		var nrm := Vector3(b.y - a.y, 0, -(b.x - a.x)).normalized()
		var mid := (a + b) / 2.0
		if Geometry2D.is_point_in_polygon(mid + Vector2(nrm.x, nrm.z) * 0.05, poly):
			nrm = -nrm                                    # outwards
		var tg_top := top
		var tg_top_b := top
		if gable and not r.is_empty():                    # gable ends: the wall goes up to the roof
			tg_top = top + _gable_h(r, a, roof_h)
			tg_top_b = top + _gable_h(r, b, roof_h)
		_quad(st, Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, tg_top_b, b.y), Vector3(a.x, tg_top, a.y), nrm,
				Vector2(dist / 12.0, (top - y0) / 9.0), Vector2((dist + ln) / 12.0, (top - y0) / 9.0), Vector2((dist + ln) / 12.0, (top - tg_top_b) / 9.0), Vector2(dist / 12.0, (top - tg_top) / 9.0))
		dist += ln
	var rst := _st(roof_st, rng.randi_range(0, ROOFS.size() - 1) if not plain or gable else 2)
	if gable and not r.is_empty():
		_gable_roof(rst, r, top, roof_h)
	else:
		var tri := Geometry2D.triangulate_polygon(poly)
		for q in range(0, tri.size(), 3):
			var pa := poly[tri[q]]
			var pb := poly[tri[q + 1]]
			var pc := poly[tri[q + 2]]
			_tri_up(rst, Vector3(pa.x, top, pa.y), Vector3(pb.x, top, pb.y), Vector3(pc.x, top, pc.y))
	# obstacle (visitors go round) with its height for the line of sight of the game
	if not r.is_empty():
		var c3 := Vector3(r["c"].x, 0, r["c"].y)
		var u: Vector2 = r["u"]
		main.add_obstacle_box(c3, 2.0 * float(r["a"]) + 0.3, 2.0 * float(r["b"]) + 0.3, -atan2(u.y, u.x))
		main.set_obstacle_height(top + roof_h - lo)
	buildings.append({"poly": poly, "top": top + roof_h, "h": h})
	counts["buildings"] = counts.get("buildings", 0) + 1


func _gable_h(r: Dictionary, p: Vector2, roof_h: float) -> float:
	var u: Vector2 = r["u"]
	var v := Vector2(-u.y, u.x)
	var q: float = (p - (r["c"] as Vector2)).dot(v)
	return roof_h * clampf(1.0 - abs(q) / max(0.1, float(r["b"])), 0.0, 1.0)


func _gable_roof(st: SurfaceTool, r: Dictionary, top: float, rh: float) -> void:
	var u: Vector2 = r["u"]
	var v := Vector2(-u.y, u.x)
	var c: Vector2 = r["c"]
	var a: float = float(r["a"]) + 0.35                  # overhang
	var b: float = float(r["b"]) + 0.45
	var drop: float = rh * 0.45 / max(0.1, float(r["b"]))        # the overhang goes a bit lower
	var p := func(s: float, t: float, y: float) -> Vector3:
		var q: Vector2 = c + u * s + v * t
		return Vector3(q.x, y, q.y)
	for side in [-1.0, 1.0]:
		var e1: Vector3 = p.call(-a, side * b, top - drop)
		var e2: Vector3 = p.call(a, side * b, top - drop)
		var r1: Vector3 = p.call(-a, 0.0, top + rh)
		var r2: Vector3 = p.call(a, 0.0, top + rh)
		var nrm := (r1 - e1).cross(e2 - e1).normalized()
		if nrm.y < 0:
			nrm = -nrm
		var slope := e1.distance_to(r1)
		_quad(st, e1, e2, r2, r1, nrm, Vector2(0, slope / 3.0), Vector2(2 * a / 3.0, slope / 3.0), Vector2(2 * a / 3.0, 0), Vector2(0, 0))


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
	"""a quad a b c d (seen from the side of n: counter-clockwise) as two triangles, front faces outside"""
	var face := (b - a).cross(c - a)
	var verts := [[a, ua], [c, uc], [b, ub], [a, ua], [d, ud], [c, uc]]
	if face.dot(n) < 0.0:
		verts = [[a, ua], [b, ub], [c, uc], [a, ua], [c, uc], [d, ud]]
	for vv in verts:
		st.set_normal(n)
		st.set_uv(vv[1])
		st.add_vertex(vv[0])


func _tri_up(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
	"""a flat triangle whose front looks up"""
	_quad_tri(st, a, b, c, Vector3.UP)


func _quad_tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, n: Vector3) -> void:
	var vs := [a, c, b] if (b - a).cross(c - a).dot(n) >= 0.0 else [a, b, c]
	for v in vs:
		st.set_normal(n)
		st.set_uv(Vector2(v.x, v.z) / 4.0)
		st.add_vertex(v)


func _facade_tex(plain: bool) -> Array:
	"""albedo + emission (lit windows) of a wall of 4 × 3 windows (12 × 9 m)"""
	var img := Image.create(256, 192, false, Image.FORMAT_RGB8)
	var em := Image.create(256, 192, false, Image.FORMAT_RGB8)
	img.fill(Color(1, 1, 1))
	em.fill(Color(0, 0, 0))
	var r2 := RandomNumberGenerator.new()
	r2.seed = 5 if not plain else 9
	for y in range(192):                                  # a bit of texture in the plaster
		for x in range(0, 256, 2):
			var g := 0.93 + r2.randf() * 0.07
			img.set_pixel(x, y, Color(g, g, g))
			img.set_pixel(x + 1, y, Color(g, g, g))
	if plain:
		for x in range(0, 256, 16):                       # boards
			img.fill_rect(Rect2i(x, 0, 1, 192), Color(0.7, 0.7, 0.7))
		return [ImageTexture.create_from_image(img), null]
	for row in range(3):
		for col in range(4):
			var x0 := col * 64 + 22
			var y0 := row * 64 + 16
			var shut := Color(0.35, 0.5, 0.33) if r2.randf() < 0.5 else Color(0.55, 0.4, 0.28)
			img.fill_rect(Rect2i(x0 - 9, y0, 8, 32), shut)        # shutters (Swiss style)
			img.fill_rect(Rect2i(x0 + 21, y0, 8, 32), shut)
			img.fill_rect(Rect2i(x0, y0, 20, 32), Color(0.92, 0.92, 0.9))
			img.fill_rect(Rect2i(x0 + 2, y0 + 2, 16, 28), Color(0.2, 0.23, 0.27))
			img.fill_rect(Rect2i(x0 + 9, y0 + 2, 2, 28), Color(0.85, 0.85, 0.83))
			if r2.randf() < 0.3:
				em.fill_rect(Rect2i(x0 + 2, y0 + 2, 16, 28), Color(1.0, 0.75, 0.42))
	img.generate_mipmaps()
	em.generate_mipmaps()
	return [ImageTexture.create_from_image(img), ImageTexture.create_from_image(em)]


func _finish_buildings() -> void:
	var tex := _facade_tex(false)
	var tex_p := _facade_tex(true)
	var dark := Image.create(4, 4, false, Image.FORMAT_RGB8)
	dark.fill(Color(0, 0, 0))
	var tex_dark := ImageTexture.create_from_image(dark)
	var lit: Array = []
	for key in wall_st:
		var plain := str(key).begins_with("plain")
		var ci := int(str(key).trim_prefix("plain"))
		var mat := ShaderMaterial.new()
		mat.shader = load("res://shaders/facade.gdshader")
		mat.set_shader_parameter("color", WALLS[ci])
		mat.set_shader_parameter("facade", (tex_p if plain else tex)[0])
		mat.set_shader_parameter("lit", tex[1] if not plain else tex_dark)
		if not plain:
			lit.append(mat)
		var st: SurfaceTool = wall_st[key]
		main.add_mesh(sc.root, st.commit(), Vector3.ZERO, mat, "caravan")
	for key in roof_st:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = ROOFS[int(key)]
		mat.roughness = 0.8
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		main.add_mesh(sc.root, (roof_st[key] as SurfaceTool).commit(), Vector3.ZERO, mat, "stone")
	if not lit.is_empty():
		main.anims.append(func(_dt, _t):
			var e := 1.2 if main.is_dark() else 0.0
			if lit[0].get_shader_parameter("night") != e:
				for mt in lit:
					mt.set_shader_parameter("night", e))
	wall_st = {}
	roof_st = {}


# ---- roads, water, fences ----------------------------------------------------------------------------------------
var ribbon_st := {}              # key -> [SurfaceTool, colour]
var road_segs := {}              # cell of 8 m -> [[a, b, half width + margin]]: no trees there


func _road(l: PackedVector2Array, tg: Dictionary) -> void:
	var t := str(tg.get("highway"))
	var w: float = {"motorway": 11.0, "trunk": 9.0, "primary": 7.5, "secondary": 6.5, "tertiary": 5.5, "unclassified": 4.5, "residential": 4.5,
			"living_street": 4.0, "service": 3.2, "track": 2.8, "path": 1.4, "footway": 1.6, "cycleway": 2.0, "bridleway": 1.6, "steps": 1.6,
			"pedestrian": 4.0, "motorway_link": 6.0, "trunk_link": 6.0, "primary_link": 5.5, "secondary_link": 5.0}.get(t, 0.0)
	if w <= 0.0:
		return
	var surf := str(tg.get("surface", ""))
	var paved := surf in ["asphalt", "paved", "concrete", "paving_stones"] or (surf == "" and not t in ["track", "path", "bridleway"])
	for i in range(l.size() - 1):
		var sg := [l[i], l[i + 1], w / 2.0 + 1.0]
		var lo: Vector2 = Vector2(min(l[i].x, l[i + 1].x), min(l[i].y, l[i + 1].y)) - Vector2.ONE * sg[2]
		var hi: Vector2 = Vector2(max(l[i].x, l[i + 1].x), max(l[i].y, l[i + 1].y)) + Vector2.ONE * sg[2]
		if hi.x - lo.x > 2000.0 or hi.y - lo.y > 2000.0:
			continue
		for cx in range(int(floor(lo.x / 8.0)), int(floor(hi.x / 8.0)) + 1):
			for cz in range(int(floor(lo.y / 8.0)), int(floor(hi.y / 8.0)) + 1):
				var key := Vector2i(cx, cz)
				if not road_segs.has(key):
					road_segs[key] = []
				road_segs[key].append(sg)
	if paved:
		_ribbon(l, w, 0.05, "road", Color(0.36, 0.36, 0.37))
	else:
		_ribbon(l, w, 0.04, "road_g", Color(0.56, 0.52, 0.44))
	counts["roads"] = counts.get("roads", 0) + 1
	if paved and w >= 4.0 and not main.scenes.data.has("road_line"):
		var near_pt := 1e9                                 # the nearest proper road: cars drive along it
		for p in l:
			near_pt = min(near_pt, p.length())
		if near_pt < 80.0:
			main.scenes.data["road_line"] = l


func _ribbon(l: PackedVector2Array, w: float, lift: float, key: String, col: Color) -> void:
	if l.size() < 2:
		return
	if not ribbon_st.has(key):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		ribbon_st[key] = [st, col]
	var st: SurfaceTool = ribbon_st[key][0]
	var pts := PackedVector2Array()                      # every 3 m a point: the strip follows the ground
	for i in range(l.size() - 1):
		var a := l[i]
		var b := l[i + 1]
		var n := maxi(1, int(a.distance_to(b) / 3.0))
		for s in range(n):
			pts.append(a.lerp(b, float(s) / n))
	pts.append(l[l.size() - 1])
	var prev_l := Vector3.ZERO
	var prev_r := Vector3.ZERO
	for i in range(pts.size()):
		var p := pts[i]
		if abs(p.x) > NEAR + 30.0 or abs(p.y) > NEAR + 30.0:
			prev_l = Vector3.ZERO
			continue
		var d := (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var side := Vector2(-d.y, d.x) * w / 2.0
		var pl := p + side
		var pr := p - side
		var vl := Vector3(pl.x, height(pl.x, pl.y) + lift, pl.y)
		var vr := Vector3(pr.x, height(pr.x, pr.y) + lift, pr.y)
		if prev_l != Vector3.ZERO:
			_quad(st, prev_l, prev_r, vr, vl, Vector3.UP, Vector2.ZERO, Vector2(1, 0), Vector2(1, 1), Vector2(0, 1))
		prev_l = vl
		prev_r = vr


func _finish_ribbons() -> void:
	for key in ribbon_st:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = ribbon_st[key][1]
		mat.roughness = 0.15 if key == "water" else 0.95
		if key == "water":
			mat.metallic = 0.3
		var tk := "pond" if key == "water" else "road"
		var mi: MeshInstance3D = main.add_mesh(sc.root, (ribbon_st[key][0] as SurfaceTool).commit(), Vector3.ZERO, mat, tk)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ribbon_st = {}
	_finish_buildings()


func _water(poly: PackedVector2Array) -> void:
	for cp in _clip(poly, NEAR + 20.0):
		var lo := INF
		var step := maxi(1, cp.size() / 40)
		for i in range(0, cp.size(), step):
			lo = min(lo, height(cp[i].x, cp[i].y))
		var tri := Geometry2D.triangulate_polygon(cp)
		if tri.is_empty():
			continue
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for q in range(0, tri.size(), 3):
			var pa: Vector2 = cp[tri[q]]
			var pb: Vector2 = cp[tri[q + 1]]
			var pc: Vector2 = cp[tri[q + 2]]
			_tri_up(st, Vector3(pa.x, lo + 0.08, pa.y), Vector3(pb.x, lo + 0.08, pb.y), Vector3(pc.x, lo + 0.08, pc.y))
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.17, 0.27, 0.3)
		mat.metallic = 0.4
		mat.roughness = 0.08
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		main.add_mesh(sc.root, st.commit(), Vector3.ZERO, mat, "pond")
		counts["water"] = counts.get("water", 0) + 1


func _barrier(l: PackedVector2Array, kind: String) -> void:
	var spec = {"fence": [1.1, 0.05, Color(0.45, 0.35, 0.25), true], "hedge": [1.5, 0.8, Color(0.2, 0.33, 0.15), true],
			"wall": [1.1, 0.3, Color(0.6, 0.58, 0.55), false], "retaining_wall": [0.8, 0.4, Color(0.55, 0.54, 0.52), false],
			"guard_rail": [0.75, 0.08, Color(0.75, 0.76, 0.78), false]}.get(kind)
	if spec == null or l.size() < 2:
		return
	for i in range(l.size() - 1):
		var a := l[i]
		var b := l[i + 1]
		var mid := (a + b) / 2.0
		if mid.length() > NEAR + 10.0 or a.distance_to(b) < 0.2:
			continue
		var ln := a.distance_to(b)
		var y: float = min(height(a.x, a.y), height(b.x, b.y))
		var hh: float = spec[0] + abs(height(a.x, a.y) - height(b.x, b.y))
		var ang := -atan2(b.y - a.y, b.x - a.x)
		var tk := "tree" if kind == "hedge" else ("stone" if kind in ["wall", "retaining_wall", "guard_rail"] else "tent")
		sc.put(sc.root, main.box(ln, hh, spec[1]), Vector3(mid.x, y + hh / 2.0 - (hh - spec[0]), mid.y), sc.foliage(2) if kind == "hedge" else spec[2], tk, Vector3(0, ang, 0))
		main.add_obstacle_box(Vector3(mid.x, 0, mid.y), ln, max(0.3, spec[1]), ang, spec[3])
		main.set_obstacle_height(spec[0])
	counts["fences"] = counts.get("fences", 0) + 1


# ---- trees -------------------------------------------------------------------------------------------------------
func _free_for_tree(p: Vector2) -> bool:
	if p.length() < 4.0 or abs(p.x) > NEAR or abs(p.y) > NEAR:
		return false
	for o in main._ob_near(p):
		if float(main._ob_closest(o, p)[1]) < 1.2:
			return false
	for r in road_segs.get(Vector2i(int(floor(p.x / 8.0)), int(floor(p.y / 8.0))), []):
		if Geometry2D.get_closest_point_to_segment(p, r[0], r[1]).distance_to(p) < r[2]:
			return false
	return true


func _trees(spots: Array) -> void:
	"""the nearest trees as real trees, the others as simple ones in one MultiMesh"""
	spots.sort_custom(func(a, b): return a[0].length() < b[0].length())
	var simple := []
	var real := 0
	var taken := {}
	for s in spots:
		var p: Vector2 = s[0]
		var cell := Vector2i(int(floor(p.x / 3.0)), int(floor(p.y / 3.0)))
		if taken.has(cell) or not _free_for_tree(p):
			continue
		taken[cell] = true
		var conif: int = s[2]
		if conif < 0:
			var c := photo_color(p.x, p.y)
			conif = 1 if c.get_luminance() < 0.11 else 0         # very dark crowns are mostly conifers
		if real < MAX_TREES and p.length() < 130.0:
			sc.tree(sc.root, Vector3(p.x, height(p.x, p.y), p.y), s[1], conif)
			real += 1
		else:
			simple.append([p, s[1], conif])
	counts["trees"] = real
	_simple_trees(simple)


func _simple_trees(list: Array) -> void:
	if list.is_empty():
		return
	for conif in [0, 1]:
		var st := SurfaceTool.new()                       # crown and trunk in one mesh (one MultiMesh, one draw call)
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var trunk := CylinderMesh.new()
		trunk.top_radius = 0.15
		trunk.bottom_radius = 0.25
		trunk.height = 3.0
		trunk.radial_segments = 6
		trunk.rings = 1
		st.append_from(trunk, 0, Transform3D(Basis().scaled(Vector3(1, 1, 1)), Vector3(0, 1.5, 0)))
		if conif == 1:
			var cm := CylinderMesh.new()
			cm.top_radius = 0.0
			cm.bottom_radius = 2.2
			cm.height = 8.5
			cm.radial_segments = 7
			cm.rings = 1
			st.append_from(cm, 0, Transform3D(Basis(), Vector3(0, 5.6, 0)))
		else:
			var sm := SphereMesh.new()
			sm.radius = 3.0
			sm.height = 5.0
			sm.radial_segments = 8
			sm.rings = 4
			st.append_from(sm, 0, Transform3D(Basis(), Vector3(0, 5.0, 0)))
		var mesh := st.commit()
		var picks := list.filter(func(e): return e[2] == conif)
		if picks.is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = mesh
		mm.instance_count = picks.size()
		for i in range(picks.size()):
			var p: Vector2 = picks[i][0]
			var s: float = picks[i][1]
			var y := height(p.x, p.y) - 0.2
			mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * s).rotated(Vector3.UP, rng.randf() * TAU), Vector3(p.x, y, p.y)))
			var g := rng.randf_range(0.75, 1.1)
			mm.set_instance_color(i, Color(0.16 * g, 0.27 * g, 0.12 * g) if conif == 1 else Color(0.22 * g, 0.36 * g, 0.15 * g))
		_mm(mm, "tree")
		counts["simple_trees"] = counts.get("simple_trees", 0) + picks.size()


func _mm(mm: MultiMesh, tkey: String) -> void:
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.95
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = mat
	mi.layers = 1
	sc.root.add_child(mi)
	var th := MultiMeshInstance3D.new()
	th.multimesh = mm
	th.material_override = main.tmat(tkey)
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sc.root.add_child(th)


func _far_trees() -> void:
	"""forests far away (from the aerial picture): simple trees from 200 m to 1.1 km, fewer further out"""
	if photo_far_img == null:
		return
	var list := []
	var stp := 14.0
	var z := -1100.0
	while z < 1100.0:
		var x := -1100.0
		while x < 1100.0:
			var p := Vector2(x + rng.randf_range(-6, 6), z + rng.randf_range(-6, 6))
			var d := p.length()
			if (abs(p.x) > NEAR or abs(p.y) > NEAR) and d < 1100.0 and rng.randf() < 1.4 - d / 900.0:
				if is_tree_color(photo_color(p.x, p.y)):
					list.append([p, rng.randf_range(1.0, 1.7), 1 if photo_color(p.x, p.y).get_luminance() < 0.11 else 0])
			x += stp
		z += stp
	_simple_trees(list)


# ---- the camp: caravan (door sensor), tent (PIR), bike next to Motion Watch ------------------------------------------
func _camp() -> void:
	var spots := [[-28.0, 9.0], [28.0, 9.0], [-60.0, 8.0], [60.0, 8.0], [180.0, 9.0], [-120.0, 9.0], [120.0, 9.0], [0.0, 12.0]]
	var used := []
	var pick := func(r: float) -> Vector3:
		for s in spots:
			var p: Vector3 = main.pos_of(s[0], s[1])
			var ok := true
			for u in used:
				if p.distance_to(u) < 6.0:
					ok = false
			for o in main._ob_near(Vector2(p.x, p.z)):
				if float(main._ob_closest(o, Vector2(p.x, p.z))[1]) < r:
					ok = false
			if ok:
				used.append(p)
				p.y = height(p.x, p.z)
				return p
		var q: Vector3 = main.free_spot(main.pos_of(-28.0, 9.0), r, true)
		q.y = height(q.x, q.z)
		used.append(q)
		return q
	var cp: Vector3 = pick.call(3.5)
	sc.caravan(cp, atan2(cp.x, cp.z) + PI / 2.0)
	var tp: Vector3 = pick.call(2.5)
	var tn = sc.node(sc.root, tp, atan2(tp.x, tp.z))
	var tent := PrismMesh.new()
	tent.size = Vector3(2.6, 1.5, 2.4)
	sc.put(tn, tent, Vector3(0, 0.75, 0), Color(0.9, 0.5, 0.15), "tent")
	main.obj["pir"] = tp
	main.add_obstacle_node(tn, Vector3.ZERO, 3.0, 2.8)
	main.set_obstacle_height(1.4)
	var bp: Vector3 = pick.call(1.0)
	sc.bike(bp, atan2(bp.x, bp.z))
