extends SceneTree
## Test ohne Bild für den Simulator-Anhang (update.gd, Sim 3.67.2): Windows- und Linux-Paket als Release-Asset.
## Ein kleiner HTTP-Server in diesem Test steht für GitHub: /repo/ = Repository (version.json, die eingefrorenen Pakete von
## Sim 3.67.2), /dl/sim-X.Y.Z/<Datei> = Release-Asset, antwortet wie GitHub mit einer Umleitung (302) auf /blob/<Datei>.
##   Sprung 1  ALTER Updater (Testdaten: update.gd aus Sim 3.67.1) bei 3.60.0: sieht 3.67.2, lädt das Paket aus dem
##             Repository, Grösse + SHA-256 stimmen - der Block «anhang» stört ihn nicht.
##   Sprung 2  NEUER Updater bei 3.67.2: nimmt 3.68.0 aus «anhang» (Windows und Linux), lädt über die Umleitung.
##   Fehler    Asset fehlt (404) · falsche Prüfsumme · falsche Grösse · Server nicht erreichbar · fremde Adresse im Block:
##             nichts wird benutzt, keine halbe Datei bleibt liegen, klare Meldung.
##   Ohne «anhang» verhält sich der neue Updater wie der alte.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/sim_anhang_test.gd"   (absoluter Pfad nötig)
## Ende: «Sim-Anhang-Test OK» oder «SCRIPT ERROR: Sim-Anhang-Test: …» (Exit-Code 0 / 1).
## Die echte Umleitung von GitHub ist hier nicht getestet. MW_ANHANG_PROBE=<url>|<grösse>|<sha256> lädt zusätzlich genau
## diese echte Adresse mit demselben Code (Workflow «Sim-Pakete», Abruf-Probe).

const PORT := 18761
var errs := []
var srv := TCPServer.new()
var conns := []
var files := {}               # path -> PackedByteArray
var seen := []                # requested paths
var base := "http://127.0.0.1:%d" % PORT
var srv2 := TCPServer.new()                      # the redirect ends at an other server (as with GitHub)
var blob_host := "http://127.0.0.1:%d" % (PORT + 1)


func ok(cond: bool, what: String) -> void:
	print(("  ok   " if cond else "  FEHLER ") + what)
	if not cond:
		errs.append(what)


func _serve() -> void:
	while srv.is_connection_available():
		conns.append({"p": srv.take_connection(), "buf": PackedByteArray(), "blob": false})
	while srv2.is_connection_available():
		conns.append({"p": srv2.take_connection(), "buf": PackedByteArray(), "blob": true})
	for c in conns.duplicate():
		var p: StreamPeerTCP = c["p"]
		p.poll()
		if p.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			conns.erase(c)
			continue
		var n := p.get_available_bytes()
		var buf: PackedByteArray = c["buf"]
		if n > 0:
			buf.append_array(p.get_data(n)[1])
			c["buf"] = buf                               # (a PackedByteArray in a Dictionary is a copy)
		var t := buf.get_string_from_ascii()
		if t.find("\r\n\r\n") < 0:
			continue
		if OS.get_environment("MW_ANHANG_LAUT") != "":
			print("     Server: " + t.split("\r\n")[0])
		var path := t.split(" ")[1].split("?")[0] if t.split(" ").size() > 1 else "/"
		seen.append(path)
		var head := ""
		var body := PackedByteArray()
		if c["blob"] != path.begins_with("/blob/"):      # each server only knows its own part
			head = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
		elif path.begins_with("/dl/"):
			head = "HTTP/1.1 302 Found\r\nLocation: %s/blob/%s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n" % [blob_host, path.get_file()]
		elif files.has(path):
			body = files[path]
			head = "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % body.size()
		else:
			head = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
		p.put_data(head.to_ascii_buffer())
		if body.size() > 0:
			p.put_data(body)
		p.disconnect_from_host()
		conns.erase(c)


func sha(b: PackedByteArray) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(b)
	return h.finish().hex_encode()


func bytes(tag: String, n: int) -> PackedByteArray:
	var b := PackedByteArray()
	b.resize(n)
	for i in range(n):
		b[i] = (i * 7 + tag.length() * 13 + tag.unicode_at(i % tag.length())) % 251
	return b


func version_json(anhang: bool, asset: String, mods := {}) -> Dictionary:
	"""version.json as versionen.py writes it: the top fields and «linux» = Sim 3.67.2 in the repository (frozen)"""
	var d := {"version": "3D-5.67.2", "ver": "3.67.2", "name": "MoveEye Sim 3.67.2", "file": "simulator3d/MotionWatch3D_Simulator.zip",
			"size": files["/repo/simulator3d/MotionWatch3D_Simulator.zip"].size(), "sha256": sha(files["/repo/simulator3d/MotionWatch3D_Simulator.zip"]),
			"notes": "im Repository", "mw_min": "3.55.0",
			"linux": {"file": "simulator3d/MoveEyeSim3D_Linux.zip", "ver": "3.67.2", "size": files["/repo/simulator3d/MoveEyeSim3D_Linux.zip"].size(),
					"sha256": sha(files["/repo/simulator3d/MoveEyeSim3D_Linux.zip"])}}
	if anhang:
		var w: PackedByteArray = mods.get("win_bytes", files.get("/blob/MotionWatch3D_Simulator.zip", bytes("w", 10)))
		var l: PackedByteArray = mods.get("linux_bytes", files.get("/blob/MoveEyeSim3D_Linux.zip", bytes("l", 10)))
		d["anhang"] = {"ver": "3.68.0", "version": "3D-5.68.0", "name": "MoveEye Sim 3.68.0", "notes": "als Release-Asset", "mw_min": "3.55.0",
				"win": {"file": "simulator3d/anhang/MotionWatch3D_Simulator.zip", "ver": "3.68.0", "size": w.size() + int(mods.get("size_plus", 0)),
						"sha256": sha(w), "url": asset + "3.68.0/MotionWatch3D_Simulator.zip"},
				"linux": {"file": "simulator3d/anhang/MoveEyeSim3D_Linux.zip", "ver": "3.68.0", "size": l.size() + int(mods.get("size_plus", 0)),
						"sha256": sha(l), "url": asset + "3.68.0/MoveEyeSim3D_Linux.zip"}}
	return d


func publish(d: Dictionary) -> void:
	files["/repo/simulator3d/version.json"] = JSON.stringify(d).to_utf8_buffer()


func updater(script_path: String) -> Node:
	var u: Node = (load(script_path) as GDScript).new()
	u.quiet = true
	get_root().add_child(u)
	u._build_ui()
	return u


func run_check(u: Node, current: String) -> void:
	"""check() up to the question «update?» - the answer is «later» (nothing is installed in a test)"""
	var st := {"done": false}
	var f := func():
		await u.check(current, base + "/repo/")
		st["done"] = true
	f.call()
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 20000:
		await process_frame
		if st["done"]:
			return
		if str(u.result).begins_with("neue Version") and u.b_skip != null and u.b_skip.visible:
			u.chosen.emit(false)
	errs.append("check() kam nicht zurück (%s)" % current)


func zip_path() -> String:
	return ProjectSettings.globalize_path("user://update.zip")


func _init() -> void:
	if srv.listen(PORT, "127.0.0.1") != OK or srv2.listen(PORT + 1, "127.0.0.1") != OK:
		push_error("Sim-Anhang-Test: Port %d besetzt" % PORT)
		quit(1)
		return
	process_frame.connect(_serve)                    # the little server answers once per frame
	await process_frame                              # the tree runs now (HTTPRequest needs it)
	await process_frame
	var neu_gd := "res://scripts/update.gd"
	var alt_gd := ProjectSettings.globalize_path("res://").path_join("../werkzeuge/testdaten/update_gd_3_67_1.gd").simplify_path()
	var asset := base + "/dl/sim-"
	files["/repo/simulator3d/MotionWatch3D_Simulator.zip"] = bytes("repo-win", 3000)
	files["/repo/simulator3d/MoveEyeSim3D_Linux.zip"] = bytes("repo-linux", 3100)
	files["/blob/MotionWatch3D_Simulator.zip"] = bytes("asset-win", 4000)
	files["/blob/MoveEyeSim3D_Linux.zip"] = bytes("asset-linux", 4100)
	var plat := "linux" if OS.get_name() == "Linux" else "win"
	var repo_file := "/repo/simulator3d/MoveEyeSim3D_Linux.zip" if plat == "linux" else "/repo/simulator3d/MotionWatch3D_Simulator.zip"
	var asset_name := "MoveEyeSim3D_Linux.zip" if plat == "linux" else "MotionWatch3D_Simulator.zip"
	var U = load(neu_gd)

	# ---- the block alone (both platforms, no network)
	print("0  Block «anhang» lesen (Windows und Linux)")
	var d := version_json(true, asset)
	for pl in ["win", "linux"]:
		var a: Dictionary = U.anhang_info(d, pl, asset)
		ok(a.get("ver", "") == "3.68.0" and a.get("version", "") == "3D-5.68.0" and str(a.get("url", "")).begins_with(asset + "3.68.0/")
				and int(a.get("size", 0)) == int(d["anhang"][pl]["size"]) and a.get("notes", "") == "als Release-Asset", "%s: Paket 3.68.0 aus «anhang»" % pl)
	ok(U.anhang_info(version_json(false, asset), "win", asset).is_empty(), "ohne Block: nichts")
	ok(U.anhang_info(d, "win", "https://example.org/sim-").is_empty(), "Adresse nicht unter der Asset-Adresse dieses Projekts: nicht genommen")
	var d2 := version_json(true, asset)
	d2["anhang"]["win"]["url"] = asset + "3.67.0/MotionWatch3D_Simulator.zip"
	ok(U.anhang_info(d2, "win", asset).is_empty(), "Adresse einer anderen Nummer: nicht genommen")
	d2 = version_json(true, asset)
	d2["anhang"]["win"].erase("sha256")
	ok(U.anhang_info(d2, "win", asset).is_empty() and not U.anhang_info(d2, "linux", asset).is_empty(), "unvollständiges Paket: nicht genommen (das andere schon)")
	ok(U.anhang_info(d, "pi", asset).is_empty(), "Pi: kein Paket im Block (bleibt bei «pi»)")
	var un: Node = updater(neu_gd)
	un.asset_base = asset
	ok(un.pick(d, "win") and un.info.get("ver", "") == "3.68.0" and un.download_url(0) == asset + "3.68.0/MotionWatch3D_Simulator.zip", "Windows: lädt vom Asset (%s)" % un.download_url(0))
	ok(un.pick(d, "linux") and un.info.get("ver", "") == "3.68.0" and un.download_url(0) == asset + "3.68.0/MoveEyeSim3D_Linux.zip", "Linux: lädt vom Asset")
	ok(un.pick(version_json(false, asset), "win") and un.info.get("ver", "") == "3.67.2" and un.download_url(0) == un.base + "simulator3d/MotionWatch3D_Simulator.zip", "ohne Block: Windows aus dem Repository wie bisher")
	ok(un.pick(version_json(false, asset), "linux") and un.download_url(0) == un.base + "simulator3d/MoveEyeSim3D_Linux.zip", "ohne Block: Linux aus dem Repository wie bisher")
	var dp := version_json(true, asset)
	ok(not un.pick(dp, "pi"), "Pi ohne «pi»: kein Paket")
	un.queue_free()

	# ---- hop 1: an OLD simulator (updater of 3.67.1) with the block in version.json
	print("1  Sprung 1: alter Updater (3.67.1) bei 3.60.0 -> 3.67.2 aus dem Repository")
	publish(version_json(true, asset))
	if not FileAccess.file_exists(alt_gd):
		errs.append("Testdaten fehlen: " + alt_gd)
	else:
		var ua: Node = updater(alt_gd)
		await run_check(ua, "3.60.0")
		ok(str(ua.result).find("3.67.2") >= 0 and ua.info.get("version", "") == "3.67.2", "sieht 3.67.2 (%s) - der Block «anhang» stört nicht" % ua.result)
		ok(not str(ua.info.get("url", "")).begins_with("http"), "keine Asset-Adresse: lädt aus dem Repository")
		seen.clear()
		var why: String = await ua._download_check(ua.base + str(ua.info["file"]), zip_path())
		ok(why == "" and FileAccess.file_exists(zip_path()) and FileAccess.get_file_as_bytes(zip_path()) == files[repo_file], "Paket aus dem Repository geladen, Grösse und SHA-256 stimmen (%s)" % (why if why != "" else ", ".join(seen)))
		await run_check(ua, "3.67.2")
		ok(str(ua.result).begins_with("schon die neuste"), "alter Updater bei 3.67.2: «%s» (er käme nie weiter - darum trägt 3.67.2 den neuen)" % ua.result)
		ua.queue_free()

	# ---- hop 2: the new updater at 3.67.2
	print("2  Sprung 2: neuer Updater bei 3.67.2 -> 3.68.0 vom Asset (Umleitung)")
	var u: Node = updater(neu_gd)
	u.asset_base = asset
	await run_check(u, "3.67.2")
	ok(str(u.result).find("3.68.0") >= 0 and u.info.get("version", "") == "3.68.0", "sieht 3.68.0 (%s)" % u.result)
	ok(u.download_url(0) == asset + "3.68.0/" + asset_name, "Adresse: %s" % u.download_url(0))
	seen.clear()
	var w2: String = await u._download_check(u.download_url(0), zip_path())
	ok(w2 == "" and FileAccess.get_file_as_bytes(zip_path()) == files["/blob/" + asset_name], "über die Umleitung geladen, Grösse und SHA-256 stimmen (%s)" % (w2 if w2 != "" else ", ".join(seen)))
	ok(seen.has("/dl/sim-3.68.0/" + asset_name) and seen.has("/blob/" + asset_name), "Weg: Asset-Adresse -> Umleitung -> Datei")
	await run_check(u, "3.68.0")
	ok(str(u.result).begins_with("schon die neuste"), "bei 3.68.0: «%s»" % u.result)
	publish(version_json(false, asset))
	await run_check(u, "3.67.2")
	ok(str(u.result).begins_with("schon die neuste"), "ohne Block (z. B. nach einem Zurück): «%s»" % u.result)

	# ---- errors
	print("3  Fehler: nichts wird benutzt, nichts bleibt liegen")
	publish(version_json(true, asset))
	await run_check(u, "3.67.2")
	var keep: PackedByteArray = files["/blob/" + asset_name]
	files.erase("/blob/" + asset_name)
	var w3: String = await u._download_check(u.download_url(0), zip_path())
	ok(w3.find("404") >= 0 and not FileAccess.file_exists(zip_path()), "Asset fehlt: «%s», keine Datei" % w3)
	files["/blob/" + asset_name] = keep
	var kap := keep.duplicate()
	kap[100] = (kap[100] + 1) % 256
	files["/blob/" + asset_name] = kap
	var w4: String = await u._download_check(u.download_url(0), zip_path())
	ok(w4.find("Prüfsumme") >= 0 and not FileAccess.file_exists(zip_path()), "Asset verändert: «%s», keine Datei" % w4)
	files["/blob/" + asset_name] = keep.slice(0, 3000)
	var w5: String = await u._download_check(u.download_url(0), zip_path())
	ok(w5.find("Grösse") >= 0 and not FileAccess.file_exists(zip_path()), "Asset abgeschnitten: «%s», keine Datei" % w5)
	files["/blob/" + asset_name] = keep
	var tot := "http://127.0.0.1:9/dl/sim-"
	publish(version_json(true, tot))
	u.asset_base = tot
	await run_check(u, "3.67.2")
	ok(u.info.get("version", "") == "3.68.0", "Asset-Server nicht erreichbar: die Version wird noch gesehen")
	var w6: String = await u._download_check(u.download_url(0), zip_path())
	ok(w6.find("Download") >= 0 and not FileAccess.file_exists(zip_path()), "Asset-Server nicht erreichbar: «%s», keine Datei" % w6)
	u.asset_base = asset
	publish(version_json(true, "https://example.org/sim-"))
	await run_check(u, "3.67.2")
	ok(str(u.result).begins_with("schon die neuste"), "fremde Adresse im Block: nicht genommen (%s)" % u.result)

	# ---- optional: one real address (workflow «Sim-Pakete», Abruf-Probe)
	var probe := OS.get_environment("MW_ANHANG_PROBE").split("|")
	if probe.size() == 3:
		print("4  Abruf-Probe: " + probe[0])
		u.info = {"version": "probe", "size": int(probe[1]), "sha256": probe[2]}
		var w7: String = await u._download_check(probe[0], zip_path())
		ok(w7 == "", "echte Adresse geladen, Grösse und SHA-256 stimmen (%s)" % (w7 if w7 != "" else "ok"))
	if FileAccess.file_exists(zip_path()):
		DirAccess.remove_absolute(zip_path())
	srv.stop()
	srv2.stop()
	if errs.is_empty():
		print("Sim-Anhang-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Sim-Anhang-Test: " + str(e))
		quit(1)
