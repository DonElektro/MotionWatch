extends SceneTree
## Test Paket Linux (ohne Bild): Sparmodus für schwache PCs (quality.gd weak_pc), das Update-Paket für Linux in
## version.json (update.gd linux_info) und das Export-Preset «Linux» (x86_64) mit allen Beilagen.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/sparmodus_test.gd"   (absoluter Pfad nötig)
## Ende: «Sparmodus-Test OK» oder «SCRIPT ERROR: Sparmodus-Test: …» (Exit-Code 0 / 1).

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var Q = load("res://scripts/quality.gd")
	var U = load("res://scripts/update.gd")
	var GB := 1073741824
	# Daniels HP EliteDesk 800 G1 DM: i5-4590T, HD 4600 (Mesa crocus), 4 GB (meldet ~3.7 GiB)
	var w: String = Q.weak_pc("Mesa Intel(R) HD Graphics 4600 (HSW GT2)", int(3.7 * GB))
	eq("EliteDesk: Speicher erkannt", w.contains("Arbeitsspeicher"), true)
	eq("EliteDesk: Grafik erkannt", w.contains("Intel"), true)
	eq("HD 4600 Windows, 8 GB", Q.weak_pc("Intel(R) HD Graphics 4600", 8 * GB) != "", true)
	eq("Mesa alt (Haswell)", Q.weak_pc("Mesa DRI Intel(R) Haswell Desktop", 8 * GB) != "", true)
	eq("nur 4 GB", Q.weak_pc("NVIDIA GeForce GTX 1050/PCIe/SSE2", 4 * GB) != "", true)
	eq("8 GB, UHD 620", Q.weak_pc("Mesa Intel(R) UHD Graphics 620 (KBL GT2)", 8 * GB), "")
	eq("16 GB, Iris Xe", Q.weak_pc("Intel(R) Iris(R) Xe Graphics", 16 * GB), "")
	eq("6 GB, GeForce", Q.weak_pc("NVIDIA GeForce RTX 3060", 6 * GB), "")
	eq("llvmpipe 16 GB (CI, Xvfb)", Q.weak_pc("llvmpipe (LLVM 15.0.7, 256 bits)", 16 * GB), "")
	eq("Speicher unbekannt", Q.weak_pc("AMD Radeon RX 580", -1), "")
	# version.json: Linux nimmt den Block «linux», Windows bleibt bei file/size/sha256 oben
	var d := {"version": "3D-5.42.0", "ver": "3.42.0", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": 10,
			"sha256": "aa", "linux": {"file": "simulator3d/MoveEyeSim3D_Linux.zip", "ver": "3.42.0", "size": 20, "sha256": "bb"}}
	eq("has_linux", U.has_linux(d), true)
	eq("has_linux ohne Block", U.has_linux({"version": "3D-5.41.1"}), false)
	var lx: Dictionary = U.linux_info(d)
	eq("Linux: Datei", lx["file"], "simulator3d/MoveEyeSim3D_Linux.zip")
	eq("Linux: Grösse", lx["size"], 20)
	eq("Linux: Prüfsumme", lx["sha256"], "bb")
	eq("Linux: Nummer", load("res://scripts/versionen.gd").of_info(lx), "3.42.0")
	eq("Windows unverändert", d["file"], "simulator3d/MotionWatch3D_Simulator.zip")
	var old := d.duplicate(true)
	old["linux"]["ver"] = "3.41.1"                     # altes Linux-Paket: dann gilt dessen Nummer (kein Update im Kreis)
	eq("Linux: eigene Nummer", load("res://scripts/versionen.gd").of_info(U.linux_info(old)), "3.41.1")
	# Export-Preset Linux x86_64 und die Beilage
	var cf := ConfigFile.new()
	eq("export_presets.cfg lesbar", cf.load("res://export_presets.cfg"), OK)
	var found := false
	for s in cf.get_sections():
		if cf.get_value(s, "name", "") == "Linux":
			found = true
			eq("Linux: Plattform", cf.get_value(s, "platform", ""), "Linux")
			eq("Linux: x86_64", cf.get_value(s + ".options", "binary_format/architecture", ""), "x86_64")
			eq("Linux: eine Datei", cf.get_value(s + ".options", "binary_format/embed_pck", false), true)
			eq("Linux: Datei", str(cf.get_value(s, "export_path", "")).get_file(), "MoveEyeSim3D.x86_64")
	eq("Preset «Linux» da", found, true)
	var sh := FileAccess.get_file_as_string("res://beilagen_linux/installieren.sh")
	eq("installieren.sh da", sh.begins_with("#!/bin/bash"), true)
	for k in ["MoveEyeSim3D.x86_64", ".local/share", "xdg-user-dir DESKTOP", "metadata::trusted", "--entfernen"]:
		eq("installieren.sh: " + k, sh.contains(k), true)
	eq("installieren.sh ohne sudo", sh.contains("sudo "), false)
	if errs.is_empty():
		print("Sparmodus-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Sparmodus-Test: " + " | ".join(errs))
		quit(1)
