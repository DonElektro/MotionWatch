extends SceneTree
## Test (ohne Bild): der Morgen im Bergtal in einer Welt (alte Szene als Ort im Tal, worlds.gd). Dort ist `spot` der Ort
## (z. B. «wild») und kein Schlafplatz - bis 3.55.0 stürzte der exportierte Simulator beim ersten Morgen dort ab (SIGSEGV in
## bergtal.gd _rank_add, z. B. KI-Bilder «Vielfalt hoch»). Mit dem Editor-Programm kam nur ein SCRIPT ERROR.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/bergtal_morgen_test.gd"   (absoluter Pfad nötig)
## Ende: «Bergtal-Morgen-Test OK» oder «SCRIPT ERROR: Bergtal-Morgen-Test: …» (Exit-Code 0 / 1).

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var Bt = load("res://scripts/bergtal.gd")
	var Worlds = load("res://scripts/worlds.gd")
	var res := {"total": 3.7, "sicherheit": 4, "aussicht": 3, "ruhe": 4}
	var bt = Bt.new()
	# 1. eine Welt: der Ort ist kein Schlafplatz
	for pl in ["wild", "wald", "parcours"]:
		eq("%s ist ein Ort im Tal" % pl, Worlds.PLACES.has(pl), true)
		eq("%s ist kein Schlafplatz" % pl, Bt.spot_data(pl), null)
		bt.place = pl
		bt.spot = pl
		bt.spot_xz = Vector2(12.3, -4.5)
		var lst: Array = bt._rank_add(res)
		var mine: Array = lst.filter(func(e): return e["spot"] == pl)
		eq("Rangliste %s: Eintrag" % pl, mine.size() >= 1, true)
		if not mine.is_empty():
			eq("Rangliste %s: Name" % pl, mine[0]["name"], Worlds.PLACES[pl][1])
	# 2. ein Schlafplatz und «frei» wie bisher
	bt.place = ""
	bt.spot = "huette"
	var l2: Array = bt._rank_add(res)
	eq("Hütte: Name", l2.filter(func(e): return e["spot"] == "huette")[0]["name"], Bt.spot_data("huette")[0])
	bt.spot = "frei"
	bt.spot_xz = Vector2(100, 200)
	var l3: Array = bt._rank_add(res)
	eq("frei: Name", l3.filter(func(e): return e["spot"] == "frei")[0]["name"], "Eigener Platz 100 / 200")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(Bt.RANK_FILE))
	if errs.is_empty():
		print("Bergtal-Morgen-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Bergtal-Morgen-Test: " + " | ".join(errs))
		quit(1)
