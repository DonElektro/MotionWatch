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
	# PC des Besitzers: HP EliteDesk 800 G1 DM: i5-4590T, HD 4600 (Mesa crocus), 4 GB (meldet ~3.7 GiB)
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
	# Kiosk (01.11.2026): reine Simulator-Maschine mit Linux Mint, rückgängig machbar
	var ke := FileAccess.get_file_as_string("res://beilagen_linux/kiosk_ein.sh")
	for k in ["--trocken", "Fortfahren? (j/n)", ".moveeye_kiosk", "autologin-session=moveeye-kiosk", "kiosk_sitzung.sh", "8765/tcp", "8764/udp", "22/tcp"]:
		eq("kiosk_ein.sh: " + k, ke.contains(k), true)
	var ka := FileAccess.get_file_as_string("res://beilagen_linux/kiosk_aus.sh")
	for k in ["--trocken", "Fortfahren? (j/n)", ".moveeye_kiosk", "SSH bleibt"]:
		eq("kiosk_aus.sh: " + k, ka.contains(k), true)
	var ks := FileAccess.get_file_as_string("res://beilagen_linux/kiosk_sitzung.sh")
	for k in ["--fullscreen", "--stream", "openbox", "desktop", "cinnamon", "testbild.py", "testbild_nachlauf"]:
		eq("kiosk_sitzung.sh: " + k, ks.contains(k), true)
	# Testbild während der Tests (3.53.0): python3-tk im Kiosk, das Testbild liegt bei
	eq("kiosk_ein.sh: python3-tk", ke.contains("python3-tk"), true)
	eq("testbild.py da", FileAccess.file_exists("res://beilagen_linux/testbild.py"), true)
	# Sim 3.57.0 «Simulator intern» auf dem Raspberry Pi 5: Block «pi» in version.json, Preset «Linux Pi» (arm64), installieren.sh kennt arm64
	var dp := d.duplicate(true)
	dp["pi"] = {"file": "simulator3d/MoveEyeSim3D_Pi.zip", "ver": "3.42.0", "size": 30, "sha256": "cc",
			"url": "https://github.com/DonElektro/MotionWatch/releases/download/sim-3.42.0/MoveEyeSim3D_Pi.zip"}
	eq("has_linux pi", U.has_linux(dp, "pi"), true)
	eq("has_linux pi ohne Block", U.has_linux(d, "pi"), false)
	var px: Dictionary = U.linux_info(dp, "pi")
	eq("Pi: Datei", px["file"], "simulator3d/MoveEyeSim3D_Pi.zip")
	eq("Pi: Prüfsumme", px["sha256"], "cc")
	eq("Pi: Release-Asset", str(px.get("url", "")).begins_with(U.PI_ASSET), true)
	eq("Pi: Linux bleibt", U.linux_info(dp)["sha256"], "bb")
	var found_pi := false
	for s in cf.get_sections():
		if cf.get_value(s, "name", "") == "Linux Pi":
			found_pi = true
			eq("Pi: arm64", cf.get_value(s + ".options", "binary_format/architecture", ""), "arm64")
			eq("Pi: eine Datei", cf.get_value(s + ".options", "binary_format/embed_pck", false), true)
			eq("Pi: ETC2/ASTC", cf.get_value(s + ".options", "texture_format/etc2_astc", false), true)
			eq("Pi: Datei", str(cf.get_value(s, "export_path", "")).get_file(), "MoveEyeSim3D.arm64")
	eq("Preset «Linux Pi» da", found_pi, true)
	eq("installieren.sh: arm64", sh.contains("MoveEyeSim3D.arm64"), true)
	if errs.is_empty():
		print("Sparmodus-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Sparmodus-Test: " + " | ".join(errs))
		quit(1)
