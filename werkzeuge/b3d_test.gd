extends SceneTree
## Test des Draco-Entpackers (scripts/draco.gd) und des glb-Lesers der 3D-Gebäude (scripts/b3d.gd), ohne Internet:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/b3d_test.gd"
## Kachel: werkzeuge/testdaten/swissbuildings3d_luzern_1060_1273.b3dm (© swisstopo). Geprüft wird gegen die Werte, die swisstopo
## selbst in die Kachel schreibt (min / max der Positionen je Teil), gegen einen unabhängigen Python-Entpacker (Ecken, Dreiecke,
## Summe der Koordinaten aller Dreiecksecken) und die Hausnummern (_BATCHID: ganze Zahlen 0 … BATCH_LENGTH − 1).
## Am Ende «B3D TEST OK» oder «B3D TEST FEHLER …» (Exit-Code 0 / 1).

const EXPECT := [[642, 1156, [-93423.7624760656, -34817.11697001644, 34150.34135012201]],
		[624, 1120, [-85922.57295654685, -56266.98049710048, 22046.957209948418]]]


func _initialize() -> void:
	var fails := []
	var D = load("res://scripts/draco.gd")
	var B = load("res://scripts/b3d.gd")
	var path := ProjectSettings.globalize_path("res://").path_join("../werkzeuge/testdaten/swissbuildings3d_luzern_1060_1273.b3dm").simplify_path()
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.size() < 100 or bytes.slice(0, 4).get_string_from_ascii() != "b3dm":
		_end(["Testkachel fehlt: " + path])
		return
	var ftj := bytes.decode_u32(12)
	var ftb := bytes.decode_u32(16)
	var btj := bytes.decode_u32(20)
	var btb := bytes.decode_u32(24)
	var ft = JSON.parse_string(bytes.slice(28, 28 + ftj).get_string_from_utf8())
	var batch_len := int(ft.get("BATCH_LENGTH", 0)) if typeof(ft) == TYPE_DICTIONARY else 0
	var glb := bytes.slice(28 + ftj + ftb + btj + btb)
	var jl := glb.decode_u32(12)
	var j: Dictionary = JSON.parse_string(glb.slice(20, 20 + jl).get_string_from_utf8())
	var bin := glb.slice(20 + jl + 8, 20 + jl + 8 + glb.decode_u32(20 + jl))
	var n := 0
	var t0 := Time.get_ticks_msec()
	for m in j["meshes"]:
		for pr in m["primitives"]:
			var dr: Dictionary = pr["extensions"]["KHR_draco_mesh_compression"]
			var res: Dictionary = D.decode(B._view(j, bin, int(dr["bufferView"])))
			if not res["ok"]:
				fails.append("Teil %d: %s" % [n, res.get("err", "?")])
				n += 1
				continue
			var pos: PackedVector3Array = res["pos"]
			var tri: PackedInt32Array = res["tri"]
			var acc: Dictionary = j["accessors"][int(pr["attributes"]["POSITION"])]
			var mn := Vector3(INF, INF, INF)
			var mx := -mn
			var sm := [0.0, 0.0, 0.0]
			for i in tri:
				mn = mn.min(pos[i])
				mx = mx.max(pos[i])
				sm[0] += pos[i].x
				sm[1] += pos[i].y
				sm[2] += pos[i].z
			for k in range(3):
				if abs(mn[k] - float(acc["min"][k])) > 0.01 or abs(mx[k] - float(acc["max"][k])) > 0.01:
					fails.append("Teil %d: min/max %s %s statt %s %s" % [n, mn, mx, acc["min"], acc["max"]])
					break
			if n < EXPECT.size():
				var e: Array = EXPECT[n]
				if pos.size() != int(e[0]) or tri.size() != 3 * int(e[1]):
					fails.append("Teil %d: %d Ecken / %d Dreiecke statt %d / %d" % [n, pos.size(), tri.size() / 3, e[0], e[1]])
				for k in range(3):
					if abs(sm[k] - float(e[2][k])) > 0.05:
						fails.append("Teil %d: Summe %s statt %s" % [n, sm, e[2]])
						break
			var bid: PackedFloat32Array = D.attribute(res, int(dr["attributes"]["_BATCHID"]))
			var used := {}
			for i in tri:
				var v := bid[i]
				if abs(v - round(v)) > 0.01 or v < 0.0 or (batch_len > 0 and v > batch_len - 1):
					fails.append("Teil %d: Hausnummer %s" % [n, v])
					break
				used[int(round(v))] = true
			if used.size() < 2:
				fails.append("Teil %d: nur %d Häuser" % [n, used.size()])
			n += 1
	if n != 2:
		fails.append("%d Teile statt 2" % n)
	print("B3D Draco: %d Teile in %d ms" % [n, Time.get_ticks_msec() - t0])
	# kaputte Daten: Fehler statt Absturz
	var bad := bytes.slice(28 + ftj + ftb + btj + btb)
	var cut: Dictionary = D.decode(B._view(j, bin, 0).slice(0, 300))
	if cut.get("ok", false):
		fails.append("abgeschnittene Daten als gut gemeldet")
	var junk := PackedByteArray([68, 82, 65, 67, 79, 2, 2, 1, 1, 0, 0, 2, 255, 255, 255, 255, 15])
	if D.decode(junk).get("ok", false):
		fails.append("Unsinn als gut gemeldet")
	if bad.is_empty():
		fails.append("glb fehlt")
	# Adressen in tileset.json
	for c in [["https://a.ch/x/v1/", "20260520/tileset.json", "https://a.ch/x/v1/20260520/tileset.json"],
			["https://a.ch/x/v1/20260520/", "../t.json", "https://a.ch/x/v1/t.json"],
			["https://a.ch/x/v1/20260520/", "./11/1/2.b3dm", "https://a.ch/x/v1/20260520/11/1/2.b3dm"],
			["https://a.ch/x/v1/", "/y/t.json", "https://a.ch/y/t.json"]]:
		if B._join(c[0], c[1]) != c[2]:
			fails.append("Adresse %s + %s = %s" % [c[0], c[1], B._join(c[0], c[1])])
	_end(fails)


func _end(fails: Array) -> void:
	if fails.is_empty():
		print("B3D TEST OK")
		quit(0)
	else:
		print("B3D TEST FEHLER ", fails)
		quit(1)
