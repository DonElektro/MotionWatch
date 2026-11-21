extends SceneTree
## Test ohne Bild für den Testkanal (testkanal.gd, 21.11.2026): ein kleiner HTTP-Server hier steht für GitHub
## (/dl/sim-test/<Datei> antwortet wie GitHub mit 302 auf /blob/<Datei>). Statt der laufenden Programmdatei eine Datei in
## user://tk_fake/ - es wird nichts neu gestartet.
##   0  sim-test.json lesen: gut · falscher Kanal · Prüfsumme · Dateiname mit Pfad · Grösse 0 · kein JSON · kein Commit
##   1  Manifest fehlt (404) · falsche Prüfsumme · falsche Grösse: nichts wird angefasst (Datei, Sicherung, Marke, ZIP)
##   2  gute Testversion: neue Datei liegt, Sicherung = alte Datei, Marke «aktiv» mit Commit
##   3  zweite Testversion: die Sicherung bleibt die erste (nicht signierte Versionen sichern sich nicht gegenseitig)
##   4  dieselbe noch einmal: «läuft schon», nichts geladen
##   5  «Zur letzten Version zurück»: alte Datei wieder da, keine Sicherung, keine Marke · ohne Sicherung: Meldung
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/testkanal_test.gd" -- --no-update --no-tour
## Ende: «Testkanal-Test OK» oder «SCRIPT ERROR: Testkanal-Test: …» (Exit-Code 0 / 1).

const PORT := 18771
const TK = preload("res://scripts/testkanal.gd")
var errs := []
var srv := TCPServer.new()
var conns := []
var files := {}
var base := "http://127.0.0.1:%d" % PORT


func ok(cond: bool, what: String) -> void:
	print(("  ok   " if cond else "  FEHLER ") + what)
	if not cond:
		errs.append(what)


func _serve() -> void:
	while srv.is_connection_available():
		conns.append({"p": srv.take_connection(), "buf": PackedByteArray()})
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
			c["buf"] = buf
		var t := buf.get_string_from_ascii()
		if t.find("\r\n\r\n") < 0:
			continue
		var path := t.split(" ")[1].split("?")[0] if t.split(" ").size() > 1 else "/"
		var head := ""
		var body := PackedByteArray()
		if path.begins_with("/dl/sim-test/"):
			head = "HTTP/1.1 302 Found\r\nLocation: %s/blob/%s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n" % [base, path.get_file()]
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


func make_zip(exe_name: String, inhalt: String) -> PackedByteArray:
	var p := ProjectSettings.globalize_path("user://tk_bau.zip")
	var z := ZIPPacker.new()
	z.open(p)
	z.start_file("MoveEyeSim3D/" + exe_name)
	z.write_file(inhalt.to_utf8_buffer())
	z.close_file()
	z.start_file("MoveEyeSim3D/Lies mich.txt")
	z.write_file("Testkanal".to_utf8_buffer())
	z.close_file()
	z.close()
	var b := FileAccess.get_file_as_bytes(p)
	DirAccess.remove_absolute(p)
	return b


func manifest(commit: String, zip: PackedByteArray, mods := {}) -> Dictionary:
	var f := {"name": "MoveEyeSim_Test_Linux.zip", "size": zip.size() + int(mods.get("size_plus", 0)),
			"sha256": str(mods.get("sha", sha(zip)))}
	var fl := []
	for plat in ["win", "linux"]:
		var g := f.duplicate()
		g["platform"] = plat
		g["name"] = "MoveEyeSim_Test_Windows.zip" if plat == "win" else "MoveEyeSim_Test_Linux.zip"
		fl.append(g)
	return {"kanal": "sim-test", "label": "Grossvater K2", "branch": "sim-grossvater-k2", "commit": commit,
			"built_at": "2026-11-21T12:00:00Z", "files": fl}


func publish(m: Dictionary, zip: PackedByteArray) -> void:
	files["/blob/sim-test.json"] = JSON.stringify(m).to_utf8_buffer()
	files["/blob/MoveEyeSim_Test_Windows.zip"] = zip
	files["/blob/MoveEyeSim_Test_Linux.zip"] = zip


func lesen(p: String) -> String:
	return FileAccess.get_file_as_string(p) if FileAccess.file_exists(p) else "<fehlt>"


func kanal(exe: String) -> Node:
	var k: Node = TK.new()
	k.base = base + "/dl/sim-test/"
	k.exe_pfad = exe
	k.neustart = false
	get_root().add_child(k)
	return k


func _init() -> void:
	if srv.listen(PORT, "127.0.0.1") != OK:
		push_error("Testkanal-Test: Port %d besetzt" % PORT)
		quit(1)
		return
	process_frame.connect(_serve)
	await process_frame
	await process_frame
	preload("res://scripts/i18n.gd").set_lang("de")

	print("0  sim-test.json lesen")
	var z0 := make_zip("x", "a")
	var m0 := manifest("abc1234def", z0)
	ok(bool(TK.parse_manifest(JSON.stringify(m0))["ok"]), "gutes Manifest")
	ok(TK.datei_fuer(m0, "linux").get("name", "") == "MoveEyeSim_Test_Linux.zip" and TK.datei_fuer(m0, "win").get("name", "") == "MoveEyeSim_Test_Windows.zip", "Datei je Plattform")
	var bad := m0.duplicate(true)
	bad["kanal"] = "latest"
	ok(not bool(TK.parse_manifest(JSON.stringify(bad))["ok"]), "falscher Kanal: abgelehnt")
	bad = m0.duplicate(true)
	bad["files"][0]["sha256"] = "1234"
	ok(not bool(TK.parse_manifest(JSON.stringify(bad))["ok"]), "Prüfsumme zu kurz: abgelehnt")
	bad = m0.duplicate(true)
	bad["files"][1]["name"] = "../../evil.zip"
	ok(not bool(TK.parse_manifest(JSON.stringify(bad))["ok"]), "Dateiname mit Pfad: abgelehnt")
	bad = m0.duplicate(true)
	bad["files"][1]["size"] = 0
	ok(not bool(TK.parse_manifest(JSON.stringify(bad))["ok"]), "Grösse 0: abgelehnt")
	bad = m0.duplicate(true)
	bad["commit"] = "xyz"
	ok(not bool(TK.parse_manifest(JSON.stringify(bad))["ok"]), "kein gültiger Commit: abgelehnt")
	ok(not bool(TK.parse_manifest("<html>nicht gefunden</html>")["ok"]), "kein JSON: abgelehnt")

	var dir := ProjectSettings.globalize_path("user://tk_fake")
	DirAccess.make_dir_recursive_absolute(dir)
	var exe := dir.path_join("MoveEyeSim3D.x86_64")
	for f in DirAccess.get_files_at(dir):
		DirAccess.remove_absolute(dir.path_join(f))
	var fw := FileAccess.open(exe, FileAccess.WRITE)
	fw.store_string("SIGNIERT 3.71.0")
	fw.close()
	if FileAccess.file_exists(TK.MARKE):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TK.MARKE))
	var bk := TK.backup_pfad(exe)
	var zip_tmp := ProjectSettings.globalize_path("user://testkanal.zip")

	print("1  Fehler: nichts wird angefasst")
	var k := kanal(exe)
	var r: String = await k.holen(true)
	ok(r.find("Keine Testversion") >= 0, "Manifest fehlt (404): %s" % r)
	k.queue_free()
	var z1 := make_zip("MoveEyeSim3D.x86_64", "TEST aaaaaaa")
	publish(manifest("aaaaaaa1111", z1, {"sha": sha("anders".to_utf8_buffer())}), z1)
	k = kanal(exe)
	r = await k.holen(true)
	ok(r.find("Prüfsumme") >= 0, "falsche Prüfsumme abgelehnt: %s" % r)
	ok(lesen(exe) == "SIGNIERT 3.71.0" and not FileAccess.file_exists(bk) and TK.aktiv(exe).is_empty() and not FileAccess.file_exists(zip_tmp),
			"  … Datei unverändert, keine Sicherung, keine Marke, kein ZIP liegen geblieben")
	k.queue_free()
	publish(manifest("aaaaaaa1111", z1, {"size_plus": 7}), z1)
	k = kanal(exe)
	r = await k.holen(true)
	ok(r.find("Grösse") >= 0 and lesen(exe) == "SIGNIERT 3.71.0" and not FileAccess.file_exists(bk), "falsche Grösse abgelehnt: %s" % r)
	k.queue_free()

	print("2  gute Testversion")
	publish(manifest("aaaaaaa1111", z1), z1)
	k = kanal(exe)
	r = await k.holen(true)
	ok(r == "", "installiert (%s)" % r)
	ok(lesen(exe) == "TEST aaaaaaa", "neue Datei liegt")
	ok(lesen(bk) == "SIGNIERT 3.71.0", "Sicherung = die vorige Version")
	ok(str(TK.aktiv(exe).get("commit", "")) == "aaaaaaa1111", "Marke: Testversion aaaaaaa aktiv")
	ok(not FileAccess.file_exists(zip_tmp), "kein ZIP liegen geblieben")
	k.queue_free()

	print("3  zweite Testversion")
	var z2 := make_zip("MoveEyeSim3D.x86_64", "TEST bbbbbbb")
	publish(manifest("bbbbbbb2222", z2), z2)
	k = kanal(exe)
	r = await k.holen(true)
	ok(r == "" and lesen(exe) == "TEST bbbbbbb", "zweite installiert")
	ok(lesen(bk) == "SIGNIERT 3.71.0", "Sicherung bleibt die signierte Version")
	ok(str(TK.aktiv(exe).get("commit", "")) == "bbbbbbb2222", "Marke: bbbbbbb")
	k.queue_free()

	print("4  dieselbe noch einmal")
	k = kanal(exe)
	r = await k.holen(true)
	ok(r.find("läuft schon") >= 0 and lesen(exe) == "TEST bbbbbbb", "läuft schon: %s" % r)
	k.queue_free()

	print("5  Zur letzten Version zurück")
	k = kanal(exe)
	r = await k.zurueck(true)
	ok(r == "" and lesen(exe) == "SIGNIERT 3.71.0", "alte Datei wieder da (%s)" % r)
	ok(not FileAccess.file_exists(bk) and TK.aktiv(exe).is_empty() and not FileAccess.file_exists(TK.MARKE), "keine Sicherung, keine Marke")
	k.queue_free()
	k = kanal(exe)
	r = await k.zurueck(true)
	ok(r.find("keine Sicherung") >= 0 and lesen(exe) == "SIGNIERT 3.71.0", "ohne Sicherung: Meldung (%s)" % r)
	k.queue_free()

	print("6  Marke gilt nur für die installierte Datei")
	publish(manifest("ccccccc3333", z1), z1)
	k = kanal(exe)
	r = await k.holen(true)
	fw = FileAccess.open(exe, FileAccess.WRITE)
	fw.store_string("SIGNIERT 3.72.0 (von Hand hingelegt)")
	fw.close()
	ok(TK.aktiv(exe).is_empty(), "andere Programmdatei: Testkanal nicht mehr aktiv")
	k.queue_free()

	for f in DirAccess.get_files_at(dir):
		DirAccess.remove_absolute(dir.path_join(f))
	await process_frame
	if errs.is_empty():
		print("Testkanal-Test OK")
		quit(0)
	else:
		push_error("Testkanal-Test: " + "; ".join(errs))
		quit(1)
