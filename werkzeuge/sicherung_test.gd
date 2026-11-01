extends SceneTree
## Test «Sicherung im Simulator» (System → Sicherung, scripts/sicherung.gd) - ohne Bild, ohne Welt:
##   cd simulator3d && HOME=/tmp/<test-home> [MWSIM_SICHERUNG_DIR=/tmp/…] <godot> --headless --path . \
##       -s "$PWD/../werkzeuge/sicherung_test.gd"            (absoluter Pfad nötig; nur mit einem Test-HOME unter /tmp)
## Prüft: sichern -> Daten ändern -> wiederherstellen (Vorher-Sicherung, Merker, apply_pending wie beim Neustart) -> gleich
## wie vorher; nicht Gesichertes bleibt unberührt; keine Zugangsdaten im ZIP; kaputte ZIPs (kein ZIP, abgeschnitten, ohne
## manifest, falsche Prüfsumme) werden ohne Absturz abgelehnt; neuere Version = Warnung; «../» im ZIP wird nie geschrieben;
## /control: nur «info» ist offen (net.gd dangerous). Ende: «Sicherung-Test OK» oder «SCRIPT ERROR: Sicherung-Test: …».

const S = preload("res://scripts/sicherung.gd")
const Net = preload("res://scripts/net.gd")
const SECRET := "ntfy-geheim-THEMA-4711"        # steht nur in Dateien, die nie in eine Sicherung gehören

var errs := []


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)


func _fake_main() -> Node:
	var s := GDScript.new()
	s.source_code = """extends Node
const VERSION := "3.23.0"
var kids_on := false
var start_info := ""
var mw_addr := ""
var mw_t := -100.0
var mw_cmd := {}
var mehr = null
func now() -> float:
	return Time.get_ticks_msec() / 1000.0
"""
	s.reload()
	var m := Node.new()
	m.set_script(s)
	return m


func _put(rel: String, text: String) -> void:
	DirAccess.make_dir_recursive_absolute(("user://" + rel).get_base_dir())
	var f := FileAccess.open("user://" + rel, FileAccess.WRITE)
	f.store_string(text)
	f.close()


func _snap() -> Dictionary:
	var out := {}
	for r in S.plan():
		out[r] = FileAccess.get_file_as_bytes("user://" + r).hex_encode().sha256_text()
	return out


func _zip_with(path: String, entries: Dictionary) -> void:
	var zp := ZIPPacker.new()
	zp.open(path)
	for k in entries:
		zp.start_file(k)
		zp.write_file(entries[k] if entries[k] is PackedByteArray else str(entries[k]).to_utf8_buffer())
		zp.close_file()
	zp.close()


func _init() -> void:
	var data := OS.get_user_data_dir()
	var home := OS.get_environment("HOME")
	var out := OS.get_environment("MWSIM_SICHERUNG_DIR")
	if out == "" and home.begins_with("/tmp/"):         # CI (ci.yml) sets only HOME: the backups go below it
		out = home.path_join("sicherung_test")
		OS.set_environment("MWSIM_SICHERUNG_DIR", out)
	if not home.begins_with("/tmp/") or not out.begins_with("/tmp/"):
		push_error("Sicherung-Test: nur mit HOME und MWSIM_SICHERUNG_DIR unter /tmp (jetzt: %s, %s)" % [home, out])
		quit(1)
		return
	# a user folder like a real one
	_put("simulator_settings.json", JSON.stringify({"ui_simple": true, "speed": 3}))
	_put("spielstand.json", JSON.stringify({"slot": 2, "names": ["Anna", "Lea", ""]}))
	_put("bergtal_abenteuer/fortschritt.json", "{\"etappe\": 4}")
	_put("spielstand/2/fortschritt.json", "{\"etappe\": 1}")
	_put("spielstand/3/lauf.txt", "lauf 3")
	_put("entdecken.json", "{\"gefunden\": [\"murmeltier\"]}")
	_put("entdecken/murmeltier.jpg", "JPEGDATA")
	_put("zwei_tagebuch/platz_1/spiel/tag1.json", "{\"text\": \"Hütte erreicht\"}")
	_put("spieltest/runden/r1.json", "{\"notiz\": \"zu dunkel\"}")
	_put("spiel/abzeichen.json", "{\"Lea\": {\"fuchs\": 2}}")
	_put("bergtal_horror.json", JSON.stringify({"hash": "abc123", "salt": "s", "iter": 1000, "v": 1, "progress": {"k": 2}}))
	_put("Fotos/Kopfkamera_1.jpg", "FOTO")
	# never in a backup
	_put("inhalte/textur.png", "TEXTUR")
	_put("pruefstand/schluessel.txt", "ghp_" + SECRET)
	_put("motionwatch_pc/config/motionwatch_settings.json", JSON.stringify({"web_password": SECRET, "notify_url": "https://ntfy.sh/" + SECRET}))
	_put("logs/godot.log", "log " + SECRET)
	_put("shader_cache/x.bin", "cache")
	_put("werk_kopie/2026-01-01_10-00-00/simulator_settings.json", "{}")

	var m := _fake_main()
	root.add_child(m)
	var s = S.new()
	s.main = m
	m.add_child(s)

	# ---- 1. back up ----
	var before := _snap()
	ok("plan ohne Ausgeschlossenes", not before.has("inhalte/textur.png") and not before.has("pruefstand/schluessel.txt")
			and not before.has("motionwatch_pc/config/motionwatch_settings.json") and not before.has("logs/godot.log")
			and not before.has("shader_cache/x.bin") and not before.has("werk_kopie/2026-01-01_10-00-00/simulator_settings.json"))
	ok("plan mit Spielständen, Tagebuch, Spieltest, Hospiz-Hash", before.has("spielstand/2/fortschritt.json") and before.has("zwei_tagebuch/platz_1/spiel/tag1.json")
			and before.has("spieltest/runden/r1.json") and before.has("bergtal_horror.json") and before.has("spiel/abzeichen.json"))
	var r: Dictionary = s.sichern_pc()
	ok("sichern: " + str(r.get("error", "")), bool(r.get("ok", false)))
	var zip := str(r.get("path", ""))
	ok("ZIP im Ordner MWSIM_SICHERUNG_DIR", zip.begins_with(out) and zip.get_file().begins_with("MoveEyeSim_Sicherung_") and zip.ends_with("_v3.23.0.zip"))
	var raw := FileAccess.get_file_as_bytes(zip)
	ok("keine Zugangsdaten im ZIP (auch nicht gepackt)", raw.get_string_from_ascii().find(SECRET) < 0)
	var zr := ZIPReader.new()
	ok("ZIP lesbar", zr.open(zip) == OK)
	var names := Array(zr.get_files())
	var all_text := ""
	for n in names:
		all_text += zr.read_file(n).get_string_from_utf8()
	var man = JSON.parse_string(zr.read_file("manifest.json").get_string_from_utf8())
	zr.close()
	ok("keine Zugangsdaten in den Dateien des ZIP", all_text.find(SECRET) < 0 and all_text.find("web_password") < 0)
	ok("manifest mit Version und Datum", typeof(man) == TYPE_DICTIONARY and str(man.get("ver")) == "3.23.0" and str(man.get("datum", "")) != ""
			and int(man.get("n", 0)) == before.size())
	ok("Hash dabei (ohne Verschlüsselung)", all_text.find("abc123") >= 0)

	# ---- 2. change the data ----
	_put("simulator_settings.json", JSON.stringify({"ui_simple": false, "speed": 9}))
	_put("neu_seit_der_sicherung.json", "{}")
	DirAccess.remove_absolute("user://spielstand/3/lauf.txt")
	_put("bergtal_horror.json", JSON.stringify({"hash": "ANDERS"}))
	ok("Daten geändert", _snap() != before)

	# ---- 3. restore (without the restart: apply_pending is what the next start does) ----
	var rr: Dictionary = s.start_restore(zip, "test", false)
	ok("wiederherstellen gestartet: " + str(rr.get("error", "")), bool(rr.get("ok", false)))
	ok("Vorher-Sicherung geschrieben", FileAccess.file_exists(str(rr.get("vorher", ""))) and str(rr.get("vorher", "")).ends_with("_vorher.zip"))
	ok("Merker da", FileAccess.file_exists(S.MARK))
	var ap: Dictionary = S.apply_pending("3.23.0")
	ok("apply_pending: %s" % str(ap), int(ap.get("n", 0)) == before.size())
	ok("Merker weg, ausgepackte Kopie weg", not FileAccess.file_exists(S.MARK) and not DirAccess.dir_exists_absolute(S.STAGE))
	var after := _snap()
	ok("gleich wie vorher (%d / %d Dateien)" % [after.size(), before.size()], after == before)
	ok("neue Datei seit der Sicherung wieder weg", not FileAccess.file_exists("user://neu_seit_der_sicherung.json"))
	ok("nicht Gesichertes unberührt", FileAccess.get_file_as_string("user://inhalte/textur.png") == "TEXTUR"
			and FileAccess.get_file_as_string("user://pruefstand/schluessel.txt").find(SECRET) >= 0
			and FileAccess.file_exists("user://motionwatch_pc/config/motionwatch_settings.json"))
	# undo: the «vorher» ZIP brings the changed state back
	var chv: Dictionary = S.check_zip(str(rr.get("vorher", "")), "3.23.0")
	ok("Vorher-Sicherung gültig", bool(chv.get("ok", false)) and (chv["files"] as Array).has("neu_seit_der_sicherung.json"))

	# ---- 4. broken ZIPs: refused, nothing changed, no crash ----
	var bad := out.path_join("kaputt")
	DirAccess.make_dir_recursive_absolute(bad)
	var f := FileAccess.open(bad.path_join("muell.zip"), FileAccess.WRITE)
	f.store_string("das ist kein zip " + "x".repeat(500))
	f.close()
	ok("kein ZIP abgelehnt", not bool(S.check_zip(bad.path_join("muell.zip"), "3.23.0")["ok"]))
	f = FileAccess.open(bad.path_join("halb.zip"), FileAccess.WRITE)
	f.store_buffer(raw.slice(0, raw.size() / 2))
	f.close()
	ok("abgeschnittenes ZIP abgelehnt", not bool(S.check_zip(bad.path_join("halb.zip"), "3.23.0")["ok"]))
	_zip_with(bad.path_join("ohne.zip"), {"simulator_settings.json": "{}"})
	ok("ZIP ohne manifest abgelehnt", not bool(S.check_zip(bad.path_join("ohne.zip"), "3.23.0")["ok"]))
	var mf := {"app": "MoveEye Sim", "art": "sicherung", "v": 1, "ver": "3.23.0", "files": {"simulator_settings.json": {"b": 2, "sha256": "00"}}}
	_zip_with(bad.path_join("falsch.zip"), {"manifest.json": JSON.stringify(mf), "simulator_settings.json": "{}"})
	ok("falsche Prüfsumme abgelehnt", not bool(S.check_zip(bad.path_join("falsch.zip"), "3.23.0")["ok"]))
	ok("fehlende Datei", not bool(S.check_zip(bad.path_join("gibtsnicht.zip"), "3.23.0")["ok"]))
	var snap2 := _snap()
	var rb: Dictionary = s.start_restore(bad.path_join("halb.zip"), "test", false)
	ok("kaputtes ZIP: wiederherstellen abgelehnt", not bool(rb.get("ok", true)) and not FileAccess.file_exists(S.MARK) and _snap() == snap2)
	var rc: Dictionary = s.control({"do": "restore", "confirm": true, "zip_b64": Marshalls.raw_to_base64("kaputt".to_utf8_buffer()), "no_restart": true})
	ok("kaputtes ZIP aus MoveEye abgelehnt", not bool(rc.get("ok", true)) and not FileAccess.file_exists(S.MARK))
	ok("restore nur mit confirm", not bool(s.control({"do": "restore", "path": zip})["ok"]))

	# ---- 5. newer version: warning, accepted; «../» never written ----
	var sha := "{}".to_utf8_buffer()
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(sha)
	var hx := h.finish().hex_encode()
	var mn := {"app": "MoveEye Sim", "art": "sicherung", "v": 1, "ver": "9.0.0", "datum": "2030-01-01T00:00:00",
			"files": {"simulator_settings.json": {"b": 2, "sha256": hx}, "../boese.json": {"b": 2, "sha256": hx},
					"pruefstand/schluessel.txt": {"b": 2, "sha256": hx}}}
	_zip_with(bad.path_join("neuer.zip"), {"manifest.json": JSON.stringify(mn), "simulator_settings.json": "{}", "../boese.json": "{}",
			"pruefstand/schluessel.txt": "{}"})
	var cn: Dictionary = S.check_zip(bad.path_join("neuer.zip"), "3.23.0")
	ok("neuere Version: angenommen mit Warnung", bool(cn.get("ok", false)) and str(cn.get("warn", "")) != "")
	ok("«../» und Schlüssel nicht übernommen", (cn.get("files", []) as Array) == ["simulator_settings.json"])

	# ---- 6. MoveEye: the ZIP is fetched once, only the one that is waiting; the guard of net.gd ----
	ok("get ohne Auftrag", not bool(s.control({"do": "get", "name": zip.get_file()})["ok"]))
	m.mw_addr = "192.0.2.56"
	m.mw_t = m.now()
	var sm: Dictionary = s.control({"do": "send"})
	ok("an MoveEye: Auftrag mw_cmd", bool(sm.get("ok", false)) and str(m.mw_cmd.get("op", "")) == "sim_sicherung")
	var gt: Dictionary = s.control({"do": "get", "name": str(m.mw_cmd.get("name", ""))})
	var gz := Marshalls.base64_to_raw(str(gt.get("zip_b64", "")))
	ok("MoveEye holt das ZIP", bool(gt.get("ok", false)) and gz.size() == int(gt.get("bytes", -1)) and gz.get_string_from_ascii().find(SECRET) < 0)
	ok("get anderer Name", not bool(s.control({"do": "get", "name": "../simulator_settings.json"})["ok"]))
	s.control({"do": "ack", "name": str(m.mw_cmd.get("name", "")), "ok": true})
	ok("nach ack: ZIP weg", not bool(s.control({"do": "get", "name": str(m.mw_cmd.get("name", ""))})["ok"]))
	ok("net.gd: restore geschützt", Net.dangerous({"action": "sicherung", "do": "restore"}) and Net.dangerous({"action": "sicherung", "do": "get"})
			and Net.dangerous({"action": "press", "id": "sicherung_laden"}) and not Net.dangerous({"action": "sicherung", "do": "info"}))
	m.kids_on = true
	ok("Kinder-Modus: kein Wiederherstellen", not bool(s.start_restore(zip, "test", false).get("ok", true)))
	m.kids_on = false

	if errs.is_empty():
		print("Sicherung-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Sicherung-Test: " + e)
		quit(1)
