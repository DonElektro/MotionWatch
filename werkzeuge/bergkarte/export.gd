extends SceneTree
## Bergtal-Karte, Stufe 1 (Besitzer 21.11.2026): die Daten des Bergtals aus dem Simulator für das Kartenpaket von MoveEye
## (werkzeuge/bergkarte/paket.py macht daraus Höhen-Kacheln, Höhenlinien, Landschaft und GeoJSON).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/bergkarte/export.gd" -- --aus /pfad/ordner
## Schreibt in den Ordner (nichts anderes):
##   hoehen.f32    die Höhenkarte bergtal.gd _hm (N × N Float32, little endian, Zeile = z, Spalte = x; Tal-Meter über dem
##                 Nordende, wie Bt.H im Gitter) - dieselben Zahlen wie main.ground_y im Tal (ohne Brücken / Eis)
##   land.u8       die Bodenart je Gitterpunkt (bergkarte.gd land_class: 0 Wiese … 7 Weide), N × N Bytes
##   bergtal.json  Gitter (lo, step, n, alt0), Orte, geheime Orte, Wanderwege, Bäche, Seen, Strasse, erfundene Wildruhezonen
##                 («Wildcamp», MoveEye 639zzzzzw), Stichproben der Höhe
##                 (für den Test), Sim-Version
## Ende: «Bergtal-Export OK …» (Exit 0) oder «SCRIPT ERROR: Bergtal-Export: …» (Exit 1). Kein Bild, kein Netz.

const Bt = preload("res://scripts/bergtal.gd")
const BK = preload("res://scripts/bergkarte.gd")


func _init() -> void:
	var aus := ""
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--aus" and i + 1 < args.size():
			aus = args[i + 1]
	if aus == "":
		printerr("SCRIPT ERROR: Bergtal-Export: --aus ORDNER fehlt")
		quit(1)
		return
	var t0 := Time.get_ticks_msec()
	Bt.generate()
	var r := export_to(aus)
	if r != "":
		printerr("SCRIPT ERROR: Bergtal-Export: " + r)
		quit(1)
		return
	print("Bergtal-Export OK: %s (%d ms)" % [aus, Time.get_ticks_msec() - t0])
	quit(0)


static func sim_version() -> String:
	var src := FileAccess.get_file_as_string("res://scripts/main.gd")
	var i := src.find('const VERSION := "')
	return src.substr(i + 18, src.find('"', i + 18) - i - 18) if i >= 0 else "?"


static func export_to(aus: String) -> String:
	"""writes the three files; "" = ok, else the reason"""
	if Bt._hm.is_empty():
		return "die Höhenkarte fehlt (Bt.generate)"
	DirAccess.make_dir_recursive_absolute(aus)
	var n: int = Bt.N
	var f := FileAccess.open(aus.path_join("hoehen.f32"), FileAccess.WRITE)
	if f == null:
		return "kann nicht schreiben: " + aus
	f.big_endian = false
	f.store_buffer(Bt._hm.to_byte_array())
	f.close()
	var land := PackedByteArray()
	land.resize(n * n)
	for j in range(n):
		var z: float = Bt.LO + j * Bt.STEP
		for i in range(n):
			land[j * n + i] = BK.land_class(Bt.LO + i * Bt.STEP, z)
	var g := FileAccess.open(aus.path_join("land.u8"), FileAccess.WRITE)
	g.store_buffer(land)
	g.close()
	# sample heights: a fixed grid of points between the grid nodes (bilinear), for the test of the package
	var samples := []
	var k := 0
	for sj in range(-9, 10, 3):
		for si in range(-9, 10, 3):
			k += 1
			var x := si * 101.3 + k * 0.7
			var z := sj * 97.1 - k * 0.3
			samples.append([snappedf(x, 0.01), snappedf(z, 0.01), snappedf(Bt.H(x, z), 0.001)])
	for p in BK.places():
		samples.append([p["x"], p["z"], snappedf(Bt.H(float(p["x"]), float(p["z"])), 0.001)])
	var d := {"format": BK.VERSION, "sim": sim_version(), "grid": {"lo": Bt.LO, "step": Bt.STEP, "n": n, "alt0": Bt.ALT0},
			"places": BK.places(), "secrets": BK.secrets(), "trails": BK.trails(), "streams": BK.streams(), "lakes": BK.lakes(),
			"road": BK.road(), "wildruhezonen": BK.wildruhezonen(), "samples": samples,
			"land_classes": ["wiese", "wald", "fels", "geroell", "gletscher", "see", "moor", "weide"]}
	var j_ := FileAccess.open(aus.path_join("bergtal.json"), FileAccess.WRITE)
	j_.store_string(JSON.stringify(d, "", false))
	j_.close()
	return ""
