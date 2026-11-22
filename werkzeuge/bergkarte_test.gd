extends SceneTree
## Test ohne Bild: das Kartenpaket «Bergtal» (MoveEye 639zzzzzt) passt zu den Daten des Simulators.
##   1. export.gd läuft als eigener Godot-Prozess (genau wie im Workflow «Bergtal-Karte») in einen Ordner unter user://.
##   2. werkzeuge/bergkarte/paket.py baut daraus das Paket (ohne MapLibre: --ohne-web) und prüft es (--pruefen).
##   3. Hier noch einmal unabhängig in GDScript, gegen bergtal.gd selbst:
##      - Zahl der Orte im Paket (vektor.json, t = ort) = bergkarte.gd places() = all_places() ohne Räume + Schlafplätze,
##        jeder Name gleich; nichts Geheimes in vektor.json; geheim.json hat jeden geheimen Ort
##      - Höhen: hoehen.f32 = Bt._hm Byte für Byte; die Höhen-Kacheln (terrarium-PNG, z15) an Stichproben = Bt.H in der
##        Mitte des Pixels (± 0.06 m: Stufen von 0.1 m)
##      - jede Kennung eines geheimen Orts kommt im Simulator vor (entdecken-Einträge «berg.…» in den Skripten, oder ein
##        Kapitel «abenteuer.kapitel.N» der Geschichte)
##      - bergkarte.gd ohne Bergtal: reply() = null, Tour abgelehnt
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/bergkarte_test.gd"   (absoluter Pfad nötig)
## Ende: «Bergtal-Karte-Test OK» oder «SCRIPT ERROR: Bergtal-Karte-Test: …» (Exit-Code 0 / 1). Braucht python3 (nur Standard).

const Bt = preload("res://scripts/bergtal.gd")
const BK = preload("res://scripts/bergkarte.gd")
const M := 6371008.8 * PI / 180.0
var errs := []


func ok(cond: bool, what: String) -> void:
	print(("  ok   " if cond else "  FEHLER ") + what)
	if not cond:
		errs.append(what)


func _init() -> void:
	var t0 := Time.get_ticks_msec()
	var tmp := ProjectSettings.globalize_path("user://bergkarte_test")
	_rm(tmp)
	DirAccess.make_dir_recursive_absolute(tmp)
	var exp := tmp.path_join("exp")
	var out := tmp.path_join("out")
	var repo := ProjectSettings.globalize_path("res://").path_join("..").simplify_path()
	var tool := repo.path_join("werkzeuge/bergkarte/export.gd")
	var log := []
	var rc := OS.execute(OS.get_executable_path(), ["--headless", "--path", ProjectSettings.globalize_path("res://"), "-s", tool, "--", "--aus", exp], log, true)
	ok(rc == 0 and "Bergtal-Export OK" in "\n".join(log), "export.gd (eigener Prozess) schreibt die Daten (Exit %d)" % rc)
	var paket := repo.path_join("werkzeuge/bergkarte/paket.py")
	log = []
	rc = OS.execute("python3", ["-I", paket, "--export", exp, "--ohne-web", "--aus", out, "--pins"], log, true)
	ok(rc == 0 and "PAKET " in "\n".join(log), "paket.py baut das Paket (Exit %d)" % rc)
	log = []
	rc = OS.execute("python3", ["-I", paket, "--pruefen", out, "--export", exp], log, true)
	var rep := "\n".join(log)
	ok(rc == 0 and "PRUEFUNG OK" in rep, "paket.py --pruefen: " + rep.strip_edges().get_slice("\n", 0))
	Bt.generate()
	_check(out.path_join("bergtal-karte-1.zip"))
	var bk = BK.new()
	ok(bk.reply() == null and not bk.control({"do": "tour", "pts": [[0, 0], [10, 10]]})["ok"], "bergkarte.gd ohne Bergtal: keine Antwort, Tour abgelehnt")
	bk.free()
	_rm(tmp)
	print("Dauer %d ms" % (Time.get_ticks_msec() - t0))
	if errs.is_empty():
		print("Bergtal-Karte-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Bergtal-Karte-Test: " + "; ".join(errs))
		quit(1)


func _check(zp: String) -> void:
	var z := ZIPReader.new()
	if z.open(zp) != OK:
		ok(false, "Paket lesbar: " + zp)
		return
	var vk = JSON.parse_string(z.read_file("vektor.json").get_string_from_utf8())
	var gh = JSON.parse_string(z.read_file("geheim.json").get_string_from_utf8())
	var names := {}
	for f in vk["features"]:
		if f["properties"]["t"] == "ort":
			names[str(f["properties"]["name"])] = true
	var want: Array = BK.places()
	var same := names.size() == want.size()
	for p in want:
		same = same and names.has(str(p["name"]))
	var raw := 0
	var seen := {}
	for p in Bt.all_places():
		if not str(p[0]).ends_with("(innen)") and not seen.has(str(p[0])):
			seen[str(p[0])] = true
			raw += 1
	for k in Bt.SPOTS:
		if not seen.has(str(Bt.SPOTS[k][0])):
			raw += 1
	ok(same and raw == want.size(), "Orte: %d im Paket = %d im Simulator (all_places ohne Räume + Schlafplätze), Namen gleich" % [names.size(), want.size()])
	var txt := z.read_file("vektor.json").get_string_from_utf8()
	var leak := []
	for s in BK.secrets():
		if txt.find(str(s["name"])) >= 0:
			leak.append(str(s["name"]))
	ok(leak.is_empty() and (gh["orte"] as Array).size() == BK.secrets().size(), "geheime Orte: %d nur in geheim.json, keiner in vektor.json %s" % [BK.secrets().size(), str(leak)])
	# every found-id exists in the simulator
	var src := ""
	for f in DirAccess.get_files_at("res://scripts"):
		if f.ends_with(".gd"):
			src += FileAccess.get_file_as_string("res://scripts/" + f)
	var miss := []
	for s in BK.secrets():
		for fid in s["found"]:
			var f2 := str(fid)
			if f2.begins_with("abenteuer.kapitel."):
				continue
			if src.find('"' + f2 + '"') < 0:                  # registered in entdecken.gd with exactly this id (bergtal_erleben_*.gd)
				miss.append(f2)
	ok(miss.is_empty(), "jede Kennung eines geheimen Orts kommt im Simulator vor %s" % str(miss))
	# heights: the grid byte for byte, the tiles at sample points
	ok(z.read_file("hoehen.f32") == Bt._hm.to_byte_array(), "hoehen.f32 = Höhenkarte des Simulators (Byte für Byte)")
	var worst := 0.0
	var n := 0
	var bad := []
	var pts := [Vector2(0, 0), Vector2(60, 0), Vector2(18, 790), Vector2(-520, 560), Vector2(568, -450), Vector2(-790, 520), Vector2(600, 430), Vector2(-60, -390)]
	for k in range(30):
		pts.append(Vector2(-950.0 + k * 63.3, 900.0 - k * 57.1))
	var cache := {}
	for q in pts:
		var lon: float = q.x / M
		var lat: float = -q.y / M
		var zz := 15
		var nn := float(1 << zz)
		var fx := (lon + 180.0) / 360.0 * nn
		var r := deg_to_rad(lat)
		var fy := (1.0 - log(tan(r) + 1.0 / cos(r)) / PI) / 2.0 * nn
		var tx := int(fx)
		var ty := int(fy)
		var key := "dem/%d/%d/%d.png" % [zz, tx, ty]
		if not cache.has(key):
			var img := Image.new()
			img.load_png_from_buffer(z.read_file(key))
			cache[key] = img
		var im: Image = cache[key]
		var px := mini(255, int((fx - tx) * 256.0))
		var py := mini(255, int((fy - ty) * 256.0))
		var c := im.get_pixel(px, py)
		var v := roundf(c.r * 255.0) * 256.0 + roundf(c.g * 255.0) + roundf(c.b * 255.0) / 256.0 - 32768.0
		var clon := (tx * 256 + px + 0.5) / (256.0 * nn) * 360.0 - 180.0
		var clat := rad_to_deg(atan(sinh(PI * (1.0 - 2.0 * (ty * 256 + py + 0.5) / (256.0 * nn)))))
		var want_h := Bt.ALT0 + Bt.H(clon * M, -clat * M)
		var dv := absf(v - want_h)
		worst = maxf(worst, dv)
		n += 1
		if dv > 0.06:
			bad.append("%s: %.2f statt %.2f" % [str(q), v, want_h])
	ok(bad.is_empty(), "Höhen-Kacheln = Bt.H an %d Stichproben (grösste Abweichung %.3f m) %s" % [n, worst, str(bad.slice(0, 3))])
	z.close()


func _rm(p: String) -> void:
	if not DirAccess.dir_exists_absolute(p):
		return
	for f in DirAccess.get_files_at(p):
		DirAccess.remove_absolute(p.path_join(f))
	for d in DirAccess.get_directories_at(p):
		_rm(p.path_join(d))
	DirAccess.remove_absolute(p)
