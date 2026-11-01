extends Node
## Paket «Sicherung im Simulator» (Besitzer 01.11.2026): System → Sicherung, bedient wie die Sicherung von MoveEye
## (quelle/060 backup_copy: «Sicherung» der Aufnahmen auf WebDAV / Ordner (USB-Stick) / Telegram, «Sicherung testen»;
## quelle/586 factory_reset: Kopie vor dem Zurücksetzen). Nur von Hand, keine automatische Sicherung.
##
## Inhalt: alles aus user://, das nicht von selbst wieder entsteht (Spielstände 1–3, Einstellungen, Entdeckungsbuch, Fotos /
## Fotowettbewerb, Reisetagebuch user://zwei_tagebuch, Spieltest-Notizen und -Berichte, Abzeichen, Geheimnisse, der
## Hospiz-Passwort-HASH ohne zusätzliche Verschlüsselung). Nicht dabei (OHNE unten): Foto-Inhalte / Texturen (user://inhalte),
## heruntergeladene Pakete, Zwischenspeicher, Protokolle, Merker, Godot-Shader-Cache, MoveEye auf diesem PC (dessen
## Einstellungen mit Zugangsdaten) und der Prüfstand-Schlüssel (GitHub) - keine Zugangsdaten in einer Sicherung.
## Im ZIP: manifest.json {app, art, v, ver, datum, n, bytes, files: {pfad: {b, sha256}}} - eine Sicherung aus einer neueren
## Version wird mit Warnung angenommen; ein kaputtes ZIP (kein ZIP, manifest fehlt, Prüfsumme falsch) wird abgelehnt.
##
## Ziele: 1. «Jetzt sichern»: ZIP in Dokumente (sonst Schreibtisch) → «MoveEye Sim Sicherung»,
##           Name MoveEyeSim_Sicherung_<datum>_<zeit>_v<version>.zip (Tests: MWSIM_SICHERUNG_DIR)
##        2. «In einen Ordner / auf einen USB-Stick»: Ordner wählen (FileDialog)
##        3. «In die MoveEye-Sicherung senden»: Auftrag mw_cmd «sim_sicherung» (wie «feedback», 350) - MoveEye holt das ZIP
##           selbst über /control {"action": "sicherung", "do": "get", "name"} und meldet {"do": "ack"}. So braucht der
##           Simulator keine Anmeldedaten von MoveEye. MoveEye zeigt es in Sicherung → Eintrag «Simulator» (Teil 639za).
## Wiederherstellen: ZIP wählen (oder aus MoveEye: /control {"do": "restore", "zip_b64", "confirm": true}), prüfen,
##   automatisch eine Sicherung des jetzigen Stands (…_vorher.zip, zum Rückgängigmachen), auspacken nach user://sicherung_neu,
##   Merker user://sicherung_laden.json, Neustart. Der neue Simulator ersetzt ganz am Anfang von main._ready (apply_pending,
##   wie werk.gd), bevor ein Teil eine Datei liest, die gesicherten Dateien durch die aus dem ZIP.
## Geschützt (net.gd dangerous): alles ausser «info» nur von diesem PC oder vom verbundenen MoveEye, nie im Kinder-Modus.
## Test ohne Bild: werkzeuge/sicherung_test.gd.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Werk = preload("res://scripts/werk.gd")
const Versionen = preload("res://scripts/versionen.gd")

const MARK := "user://sicherung_laden.json"
const STAGE := "user://sicherung_neu"
const TMP := "user://sicherung_tmp"
const ORDNER := "MoveEye Sim Sicherung"
const PREFIX := "MoveEyeSim_Sicherung_"
const MANIFEST := "manifest.json"
const APP := "MoveEye Sim"
const ART := "sicherung"
const MAX_FILE := 200 * 1024 * 1024                   # a single file bigger than this is left out (never seen so far)
const MAX_MW := 100 * 1024 * 1024                     # to MoveEye at most 100 MB (MoveEye takes the same)
const MARK_FRESH := 120.0
const MARK_MAX := 7 * 24 * 3600.0
const MW_WAIT := 150.0                                # s: MoveEye fetches the ZIP within this time (else: too old / gone)

# NOT in the backup: path relative to user:// ("/" at the end = the whole folder) - why: the comment
const OHNE := [
	"inhalte/",                          # Foto-Inhalte, CC0-Texturen, Himmel (heruntergeladen, inhalte.gd)
	"inhalte_merker.json",               # Merker während die Foto-Inhalte geladen werden
	"figuren_v1.zip",                    # Figuren-Paket (heruntergeladen)
	"orte/cache/",                       # Karten-Zwischenspeicher (geo.gd)
	"orte/3d_gebaeude_bericht.txt",      # entsteht beim Laden eines Orts
	"motionwatch_pc/",                   # MoveEye auf diesem PC: Programm UND seine Einstellungen (Passwörter, ntfy) - nie mitnehmen
	"autologon/",                        # Autologon-Programm von Microsoft (heruntergeladen)
	"pruefstand/schluessel.txt",         # GitHub-Schlüssel des Prüfstands - nie in eine Sicherung
	"trainingsbilder/",                  # KI-Trainingsbilder (entstehen neu)
	"parcours/lernbilder/",              # Parcours-Lernbilder (entstehen neu)
	"dev_test/",                         # Kapitel-Tests des Entwickler-Fensters
	"dev_notizen_export/",               # ZIP der Notizen (die Notizen selbst sind dabei)
	"logs/",                             # Protokolle
	"shader_cache/",                     # Godot-Grafik-Zwischenspeicher
	"vulkan/",                           # Godot-Grafik-Zwischenspeicher
	"update.zip",                        # heruntergeladenes Update
	"handy_browser/",                    # Zwischenspeicher der Handy-Ansicht
	"mehr_shots/",                       # Bildschirmfotos der Tests
	"localplay_debug.png",               # Testbild
	"figur_shot.png",                    # Testbild
	"werk_kopie/",                       # Kopien vor dem Zurücksetzen (sonst würde jede Sicherung immer grösser)
	"werk_reset.json",                   # Merker der Werksrücksetzung (Absturz- / Neustart-Merker)
	"sicherung_neu/",                    # ausgepackte Sicherung bis zum Neustart
	"sicherung_tmp/",                    # ZIP auf dem Weg zu / von MoveEye
	"sicherung_laden.json",              # Merker «beim nächsten Start wiederherstellen»
]

var main
var busy := false
var note := ""                                        # the last message (also /control info)
var _mw_wait := {}                                    # {name, t}: MoveEye shall fetch this ZIP
var _fd: FileDialog = null
var _go: Button
var _err: Label


func _ready() -> void:
	if Engine.has_meta("sicherung_done"):            # the start right after a restore: say so once
		var r: Dictionary = Engine.get_meta("sicherung_done")
		get_tree().create_timer(3.5).timeout.connect(func():
			_toast(T.t("Wiederhergestellt: {n} Dateien aus {z}.", {"n": int(r.get("n", 0)), "z": str(r.get("name", ""))})
					+ (" " + T.t("Rückgängig: {v}", {"v": str(r.get("vorher", ""))}) if str(r.get("vorher", "")) != "" else ""))
			_log("Sicherung wiederhergestellt: %d Dateien aus %s" % [int(r.get("n", 0)), str(r.get("name", ""))]))


func add_controls() -> void:
	var g := {"sub": "Sicherung"}
	main.add_control("button", "sicherung_jetzt", "📦 Jetzt sichern (ZIP in Dokumente → MoveEye Sim Sicherung)", null,
			func(): sichern_pc(), "System", g)
	main.add_control("button", "sicherung_ordner", "📦 In einen Ordner oder auf einen USB-Stick sichern …", null,
			func(): ordner_waehlen(), "System", g)
	main.add_control("button", "sicherung_mw", "📡 In die MoveEye-Sicherung senden (Eintrag «Simulator»)", null,
			func(): an_moveeye(), "System", g)
	main.add_control("button", "sicherung_laden", "⚠ Wiederherstellen aus einer Sicherung (ZIP) …", null,
			func(): zip_waehlen(), "System", g)
	main.add_control("button", "sicherung_zeigen", "Ordner der Sicherungen öffnen", null,
			func(): OS.shell_open(pc_dir()), "System", {"sub": "Sicherung", "expert": true})


func _toast(t: String) -> void:
	note = t
	print("sicherung: " + t)
	if main != null and main.get("mehr") != null and main.mehr != null and main.mehr.has_method("toast"):
		main.mehr.toast(t)
	if main != null and main.get("start_info") != null:
		main.start_info = t


func _log(t: String) -> void:
	if main != null and main.get("mehr") != null and main.mehr != null and main.mehr.get("protokoll") != null:
		main.mehr.protokoll.add("info", t)


func _version() -> String:
	return str(main.VERSION) if main != null and main.get("VERSION") != null else "?"


# =============================================================================================================================
# what goes into a backup
# =============================================================================================================================
static func ohne(rel: String) -> bool:
	"""true = this file is never in a backup (and never taken from one)"""
	if rel.ends_with(".part") or rel.ends_with(".tmp"):
		return true
	for k in OHNE:
		if rel == k or (k.ends_with("/") and rel.begins_with(k)):
			return true
	return false


static func safe_rel(rel: String) -> bool:
	"""a path from a ZIP: relative, inside user://, no tricks"""
	if rel == "" or rel.begins_with("/") or rel.find("\\") >= 0 or rel.find(":") >= 0 or rel.ends_with("/"):
		return false
	for p in rel.split("/"):
		if p == "" or p == "." or p == "..":
			return false
	return true


static func plan() -> Array:
	"""the files (relative to user://) a backup takes now"""
	var all := []
	Werk._walk("", all)
	var out := []
	for r in all:
		if not ohne(r):
			out.append(r)
	out.sort()
	return out


static func pc_dir() -> String:
	"""Documents (else the desktop) / «MoveEye Sim Sicherung»; tests: MWSIM_SICHERUNG_DIR"""
	var e := OS.get_environment("MWSIM_SICHERUNG_DIR")
	if e != "":
		return e
	for k in [OS.SYSTEM_DIR_DOCUMENTS, OS.SYSTEM_DIR_DESKTOP]:
		var d := OS.get_system_dir(k)
		if d != "" and DirAccess.dir_exists_absolute(d):
			return d.path_join(ORDNER)
	return ProjectSettings.globalize_path("user://sicherungen")


static func zip_name(version: String, extra := "") -> String:
	var stamp := Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
	var v := Versionen.plain(version).replace(" ", "")
	return PREFIX + stamp + "_v" + v + extra + ".zip"


static func _sha(b: PackedByteArray) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	if b.size() > 0:
		h.update(b)
	return h.finish().hex_encode()


static func make_zip(dest: String, version: String) -> Dictionary:
	"""writes the backup to dest (absolute path or user://…): {ok, path, n, bytes, skipped, error}"""
	var path := ProjectSettings.globalize_path(dest)
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var part := path + ".part"
	var zp := ZIPPacker.new()
	if zp.open(part) != OK:
		return {"ok": false, "error": T.t("Die Sicherung lässt sich hier nicht schreiben: {p}", {"p": path.get_base_dir()})}
	var files := {}
	var total := 0
	var skipped := []
	for rel in plan():
		var b := FileAccess.get_file_as_bytes("user://" + rel)
		if b.size() == 0 and FileAccess.get_open_error() != OK:
			skipped.append(rel)
			continue
		if b.size() > MAX_FILE:
			skipped.append(rel)
			continue
		if zp.start_file(rel) != OK or zp.write_file(b) != OK or zp.close_file() != OK:
			zp.close()
			DirAccess.remove_absolute(part)
			return {"ok": false, "error": T.t("Die Sicherung konnte nicht ganz geschrieben werden.")}
		files[rel] = {"b": b.size(), "sha256": _sha(b)}
		total += b.size()
	var man := {"app": APP, "art": ART, "v": 1, "ver": Versionen.plain(version), "version": version,
			"datum": Time.get_datetime_string_from_system(false, true), "n": files.size(), "bytes": total, "files": files}
	var mb := JSON.stringify(man, " ").to_utf8_buffer()
	var ok := zp.start_file(MANIFEST) == OK and zp.write_file(mb) == OK and zp.close_file() == OK
	ok = zp.close() == OK and ok
	if not ok:
		DirAccess.remove_absolute(part)
		return {"ok": false, "error": T.t("Die Sicherung konnte nicht ganz geschrieben werden.")}
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	if DirAccess.rename_absolute(part, path) != OK:
		return {"ok": false, "error": T.t("Die Sicherung lässt sich hier nicht schreiben: {p}", {"p": path.get_base_dir()})}
	return {"ok": true, "path": path, "name": path.get_file(), "n": files.size(), "bytes": total, "skipped": skipped}


static func check_zip(path: String, version: String) -> Dictionary:
	"""is it a backup of the simulator, complete and unchanged? {ok, error, manifest, warn, n, files: [rel]}
	(never crashes: a broken file is an answer with ok = false)"""
	var p := ProjectSettings.globalize_path(path)
	if not FileAccess.file_exists(p):
		return {"ok": false, "error": T.t("Datei nicht gefunden.")}
	var zr := ZIPReader.new()
	if zr.open(p) != OK:
		return {"ok": false, "error": T.t("Kein gültiges ZIP oder beschädigt – nichts geändert.")}
	var names := Array(zr.get_files())
	if not names.has(MANIFEST):
		zr.close()
		return {"ok": false, "error": T.t("Das ist keine Sicherung des Simulators (manifest.json fehlt) – nichts geändert.")}
	var m = JSON.parse_string(zr.read_file(MANIFEST).get_string_from_utf8())
	if typeof(m) != TYPE_DICTIONARY or str(m.get("app", "")) != APP or str(m.get("art", "")) != ART or typeof(m.get("files")) != TYPE_DICTIONARY:
		zr.close()
		return {"ok": false, "error": T.t("Das ist keine Sicherung des Simulators (manifest.json fehlt) – nichts geändert.")}
	var take := []
	for rel in (m["files"] as Dictionary).keys():
		var r := str(rel)
		if not safe_rel(r) or ohne(r):
			continue                                    # never into the key / MoveEye folder, never out of user://
		var info = m["files"][rel]
		if typeof(info) != TYPE_DICTIONARY or not names.has(r):
			zr.close()
			return {"ok": false, "error": T.t("Die Sicherung ist beschädigt ({f}) – nichts geändert.", {"f": r})}
		var b := zr.read_file(r)
		if b.size() != int(info.get("b", -1)) or _sha(b) != str(info.get("sha256", "")):
			zr.close()
			return {"ok": false, "error": T.t("Die Sicherung ist beschädigt ({f}) – nichts geändert.", {"f": r})}
		take.append(r)
	zr.close()
	var warn := ""
	if Versionen.newer(str(m.get("ver", m.get("version", ""))), version):
		warn = T.t("Diese Sicherung stammt aus einer neueren Version ({v}). Sie wird trotzdem geladen – Neues kennt dieser Simulator vielleicht nicht.",
				{"v": str(m.get("ver", ""))})
	take.sort()
	return {"ok": true, "manifest": m, "warn": warn, "n": take.size(), "files": take, "name": p.get_file()}


static func _rm_tree(path: String) -> void:
	"""only below user://sicherung_neu or user://sicherung_tmp (links are removed, not followed)"""
	if not (path == STAGE or path == TMP or path.begins_with(STAGE + "/") or path.begins_with(TMP + "/")) or path.find("..") >= 0:
		return
	var d := DirAccess.open(path)
	if d == null:
		return
	d.include_hidden = true
	d.include_navigational = false
	for f in d.get_files():
		DirAccess.remove_absolute(path + "/" + f)
	for s in d.get_directories():
		if d.is_link(s):
			DirAccess.remove_absolute(path + "/" + s)
		else:
			_rm_tree(path + "/" + s)
	DirAccess.remove_absolute(path)


static func stage(path: String, chk: Dictionary) -> Dictionary:
	"""unpack the checked backup to user://sicherung_neu (the files are put in place at the next start)"""
	_rm_tree(STAGE)
	var zr := ZIPReader.new()
	if zr.open(ProjectSettings.globalize_path(path)) != OK:
		return {"ok": false, "error": T.t("Kein gültiges ZIP oder beschädigt – nichts geändert.")}
	var n := 0
	for r in chk["files"]:
		var to: String = STAGE + "/" + str(r)
		DirAccess.make_dir_recursive_absolute(to.get_base_dir())
		var f := FileAccess.open(to, FileAccess.WRITE)
		if f == null:
			zr.close()
			_rm_tree(STAGE)
			return {"ok": false, "error": T.t("Die Sicherung lässt sich hier nicht schreiben: {p}", {"p": ProjectSettings.globalize_path(STAGE)})}
		f.store_buffer(zr.read_file(str(r)))
		f.close()
		n += 1
	zr.close()
	return {"ok": true, "n": n}


static func write_mark(info: Dictionary) -> bool:
	var f := FileAccess.open(MARK, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(info))
	f.close()
	return true


# =============================================================================================================================
# 1. / 2. / 3. back up
# =============================================================================================================================
func _save_now() -> void:
	if main != null and main.has_method("_save_settings"):
		main._save_settings()                           # the backup has the settings as they are now


func sichern(dir: String) -> Dictionary:
	if busy:
		return {"ok": false, "error": "busy"}
	busy = true
	_save_now()
	var r := make_zip(dir.path_join(zip_name(_version())), _version())
	busy = false
	if bool(r["ok"]):
		_toast(T.t("Gesichert: {n} Dateien in {p}", {"n": int(r["n"]), "p": str(r["path"])}))
		_log("Sicherung: %d Dateien, %s" % [int(r["n"]), str(r["path"])])
	else:
		_toast("⚠ " + str(r["error"]))
	return r


func sichern_pc() -> Dictionary:
	return sichern(pc_dir())


func ordner_waehlen() -> void:
	_dialog(FileDialog.FILE_MODE_OPEN_DIR, T.t("Ordner oder USB-Stick für die Sicherung wählen"), func(p): sichern(str(p)))


func zip_waehlen() -> void:
	if not Werk.is_owner(main):
		_toast(T.t("Nur für den Besitzer – nicht im Kinder-Modus."))
		return
	_dialog(FileDialog.FILE_MODE_OPEN_FILE, T.t("Sicherung (ZIP) zum Wiederherstellen wählen"), func(p): open_restore(str(p)))


func _dialog(mode: int, title: String, done: Callable) -> void:
	if _fd != null and is_instance_valid(_fd):
		_fd.queue_free()
	_fd = FileDialog.new()
	_fd.file_mode = mode
	_fd.access = FileDialog.ACCESS_FILESYSTEM
	_fd.use_native_dialog = true
	_fd.title = title
	if mode == FileDialog.FILE_MODE_OPEN_FILE:
		_fd.filters = PackedStringArray(["*.zip ; " + T.t("Sicherung (ZIP)")])
	var start := pc_dir()
	if DirAccess.dir_exists_absolute(start):
		_fd.current_dir = start
	_fd.file_selected.connect(func(p): done.call(p))
	_fd.dir_selected.connect(func(p): done.call(p))
	add_child(_fd)
	_fd.popup_centered(Vector2i(900, 600))


func mw_connected() -> bool:
	return main != null and str(main.get("mw_addr")) != "" and main.now() - float(main.get("mw_t")) < 10.0


func an_moveeye() -> Dictionary:
	"""3. the ZIP to the MoveEye that is connected: it fetches it itself (/control sicherung get) and says «ack»"""
	if not mw_connected():
		_toast(T.t("MoveEye ist nicht verbunden – zuerst in MoveEye die Simulation einschalten."))
		return {"ok": false, "error": "not connected"}
	if busy:
		return {"ok": false, "error": "busy"}
	busy = true
	_save_now()
	_rm_tree(TMP)
	var r := make_zip(TMP + "/" + zip_name(_version()), _version())
	busy = false
	if not bool(r["ok"]):
		_toast("⚠ " + str(r["error"]))
		return r
	if int(r["bytes"]) > MAX_MW or FileAccess.get_file_as_bytes(TMP + "/" + str(r["name"])).size() > MAX_MW:
		_rm_tree(TMP)
		_toast(T.t("Zu gross für MoveEye (höchstens 100 MB) – bitte auf dem PC oder einem USB-Stick sichern."))
		return {"ok": false, "error": "too big"}
	_mw_wait = {"name": str(r["name"]), "t": main.now(), "sent": main.now(), "n": 0,
			"bytes": FileAccess.get_file_as_bytes(TMP + "/" + str(r["name"])).size()}
	_mw_ask()
	_toast(T.t("Sicherung bereit – MoveEye holt sie ab …"))
	return {"ok": true, "name": r["name"], "n": r["n"], "wait": true}


func _mw_ask() -> void:
	"""the request to MoveEye (again with a new number: a request that arrives right at a new connection is ignored there, 350)"""
	_mw_wait["sent"] = main.now()
	_mw_wait["n"] = int(_mw_wait.get("n", 0)) + 1
	main.mw_cmd = {"id": max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1), "op": "sim_sicherung",
			"name": str(_mw_wait["name"]), "bytes": int(_mw_wait["bytes"]), "sim": _version()}


func _process(_dt: float) -> void:
	if not _mw_wait.is_empty() and main != null and not _mw_wait.has("got") and int(_mw_wait.get("n", 0)) < 4 \
			and main.now() - float(_mw_wait.get("sent", 0.0)) > 20.0 and str(main.mw_cmd.get("op", "")) in ["sim_sicherung", ""]:
		_mw_ask()
	if not _mw_wait.is_empty() and main != null and main.now() - float(_mw_wait["t"]) > MW_WAIT:
		_mw_wait = {}
		_rm_tree(TMP)
		_toast(T.t("MoveEye hat die Sicherung nicht abgeholt (MoveEye zu alt oder nicht mehr verbunden)."))


# =============================================================================================================================
# restore
# =============================================================================================================================
func open_restore(path: String) -> void:
	"""the window: what is in the ZIP, a warning for a newer version, «Jetzt wiederherstellen» (red, like werk.gd)"""
	var chk := check_zip(path, _version())
	if not bool(chk["ok"]):
		_toast("⚠ " + str(chk["error"]))
		return
	var mehr = main.get("mehr")
	if mehr == null:
		start_restore(path, "Fenster")
		return
	var m: Dictionary = chk["manifest"]
	var b: VBoxContainer = mehr._window(T.t("Simulator wiederherstellen"), "update")
	mehr.win_id = "sicherung"
	var info := UI.small(T.t("Sicherung: {z}", {"z": str(chk["name"])}) + "\n" + T.t("Von: {d} · Version {v} · {n} Dateien",
			{"d": str(m.get("datum", "?")).replace("T", " "), "v": str(m.get("ver", "?")), "n": int(chk["n"])}), UI.TXT)
	info.custom_minimum_size = Vector2(480, 0)
	b.add_child(info)
	if str(chk["warn"]) != "":
		var w := UI.small("⚠ " + str(chk["warn"]), UI.ORG)
		w.custom_minimum_size = Vector2(480, 0)
		b.add_child(w)
	var c := UI.small(T.t("Spielstände, Einstellungen, Entdeckungsbuch, Fotos und Tagebücher werden durch die aus der Sicherung ersetzt. Vorher wird automatisch der jetzige Stand gesichert (…_vorher.zip) – damit kannst du es rückgängig machen. Danach startet der Simulator neu."), UI.TXT)
	c.custom_minimum_size = Vector2(480, 0)
	b.add_child(c)
	_err = UI.small("", UI.RED)
	b.add_child(_err)
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	b.add_child(bt)
	var cl := Button.new()
	cl.text = T.t("Schliessen")
	cl.pressed.connect(mehr.close_window)
	bt.add_child(cl)
	_go = Button.new()
	_go.text = T.t("Jetzt wiederherstellen")
	for st in ["normal", "hover", "pressed"]:
		_go.add_theme_stylebox_override(st, UI.box(UI.RED if st != "hover" else UI.RED.lightened(0.1), UI.RED))
	_go.add_theme_color_override("font_color", Color.WHITE)
	_go.pressed.connect(func():
		var r := start_restore(path, "Fenster")
		if not bool(r["ok"]):
			_err.text = "⚠ " + str(r.get("error", ""))
			return
		_go.disabled = true
		_err.add_theme_color_override("font_color", UI.GRN)
		_err.text = "✓ " + T.t("Rückgängig: {v}", {"v": str(r.get("vorher", ""))}) + "\n" + T.t("Der Simulator startet neu …"))
	bt.add_child(_go)


func start_restore(path: String, who := "Fenster", restart := true) -> Dictionary:
	"""check, back up the present state (…_vorher.zip), unpack, mark, restart"""
	if not Werk.is_owner(main):
		return {"ok": false, "error": T.t("Nur für den Besitzer – nicht im Kinder-Modus.")}
	if busy:
		return {"ok": false, "error": "busy"}
	if not Werk._safe_root():
		return {"ok": false, "error": T.t("Der Benutzerordner sieht unerwartet aus – zur Sicherheit wird nichts gelöscht.")}
	var chk := check_zip(path, _version())
	if not bool(chk["ok"]):
		return chk
	busy = true
	_save_now()
	var v := make_zip(pc_dir().path_join(zip_name(_version(), "_vorher")), _version())
	if not bool(v["ok"]):
		busy = false
		return {"ok": false, "error": T.t("Vorher-Sicherung ging nicht – nichts geändert.") + " " + str(v.get("error", ""))}
	var s := stage(path, chk)
	if not bool(s["ok"]):
		busy = false
		return s
	if not write_mark({"pid": OS.get_process_id(), "t": Time.get_unix_time_from_system(), "name": str(chk["name"]),
			"vorher": str(v["path"]), "n": int(s["n"]), "who": who}):
		_rm_tree(STAGE)
		busy = false
		return {"ok": false, "error": T.t("Der Merker für den Neustart liess sich nicht schreiben – nichts wurde gelöscht.")}
	print("sicherung (%s): %s staged (%d files), copy before: %s" % [who, str(chk["name"]), int(s["n"]), str(v["path"])])
	busy = restart                                      # (without the restart - tests - the next start applies it)
	if restart:
		get_tree().create_timer(1.2).timeout.connect(_restart)
	return {"ok": true, "restart": restart, "n": int(s["n"]), "warn": chk["warn"], "vorher": str(v["path"]), "vorher_name": str(v["name"]),
			"name": str(chk["name"])}


func _restart() -> void:
	var a := OS.get_cmdline_args()
	a.append("--")
	var ua: PackedStringArray = main.restart_args() if main.has_method("restart_args") else OS.get_cmdline_user_args()
	for x in ua:
		a.append(x)
	if main.has_method("release_ports"):
		main.release_ports()
	if OS.create_process(OS.get_executable_path(), a) <= 0:
		busy = false
		_toast(T.t("Bitte den Simulator neu starten – das Wiederherstellen geschieht beim nächsten Start."))
		return
	get_tree().quit()


static func apply_pending(version := "?") -> Dictionary:
	"""the new simulator, right at the start (main._ready, after werk.apply_pending, before anything reads user://)"""
	if not FileAccess.file_exists(MARK):
		return {}
	var m = JSON.parse_string(FileAccess.get_file_as_string(MARK))
	if typeof(m) != TYPE_DICTIONARY or not Werk._safe_root():
		printerr("sicherung: mark unreadable or user folder looks wrong - nothing changed")
		DirAccess.remove_absolute(MARK)
		_rm_tree(STAGE)
		return {}
	var age := absf(Time.get_unix_time_from_system() - float(m.get("t", 0.0)))
	if age > MARK_MAX:
		printerr("sicherung: the mark is %d days old - forgotten" % int(age / 86400.0))
		DirAccess.remove_absolute(MARK)
		_rm_tree(STAGE)
		return {}
	var op := int(m.get("pid", 0))
	var vorher := str(m.get("vorher", ""))
	if age <= MARK_FRESH and op > 0 and op != OS.get_process_id():
		var t0 := Time.get_ticks_msec()
		while OS.is_process_running(op) and Time.get_ticks_msec() - t0 < 10000:
			OS.delay_msec(100)
		if OS.is_process_running(op):
			printerr("sicherung: process %d still runs - again at the next start" % op)
			return {}
	elif age > MARK_FRESH:                              # the restart failed, played since then: a fresh copy first
		var c := make_zip(pc_dir().path_join(zip_name(version, "_vorher")), version)
		if not bool(c["ok"]):
			printerr("sicherung: no fresh copy - nothing changed")
			return {}
		vorher = str(c["path"])
	var staged := []
	Werk._walk(STAGE.trim_prefix("user://") + "/", staged)
	if staged.size() != int(m.get("n", -1)):
		printerr("sicherung: the unpacked backup is incomplete (%d of %d) - nothing changed" % [staged.size(), int(m.get("n", -1))])
		DirAccess.remove_absolute(MARK)
		_rm_tree(STAGE)
		return {}
	var gone := 0
	for r in plan():                                    # what a backup holds: the old state goes (also files that are new since)
		if DirAccess.remove_absolute("user://" + r) == OK:
			gone += 1
	var n := 0
	var pre := STAGE.trim_prefix("user://") + "/"
	for s in staged:
		var rel := str(s).trim_prefix(pre)
		if not safe_rel(rel) or ohne(rel):
			continue
		DirAccess.make_dir_recursive_absolute(("user://" + rel).get_base_dir())
		if DirAccess.copy_absolute("user://" + str(s), "user://" + rel) == OK:
			n += 1
	_rm_tree(STAGE)                                     # (applying twice would be harmless: the mark goes last)
	DirAccess.remove_absolute(MARK)
	var res := {"name": str(m.get("name", "")), "n": n, "gone": gone, "vorher": vorher.get_file()}
	print("sicherung: restored %d files from %s (before: %s)" % [n, res["name"], vorher])
	Engine.set_meta("sicherung_done", res)
	return res


# =============================================================================================================================
# /control {"action": "sicherung", "do": info | make (dir) | send | get (name) | ack (name, ok, error) | check (path) |
#           restore (path | zip_b64, confirm: true)}  - all but «info» only from this PC / the connected MoveEye (net.gd)
# =============================================================================================================================
func local_list() -> Array:
	var out := []
	var d := DirAccess.open(pc_dir())
	if d == null:
		return out
	var names := Array(d.get_files()).filter(func(x): return str(x).begins_with(PREFIX) and str(x).ends_with(".zip"))
	names.sort()
	names.reverse()
	for x in names.slice(0, 20):
		var f := FileAccess.open(pc_dir().path_join(x), FileAccess.READ)
		out.append({"name": x, "bytes": f.get_length() if f != null else 0})
	return out


func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	match dd:
		"info":
			return {"ok": true, "owner": Werk.is_owner(main), "dir": pc_dir(), "files": plan().size(), "local": local_list(),
					"wait": _mw_wait.get("name", ""), "note": note, "mw": mw_connected(), "busy": busy}
		"make":
			return sichern(str(d.get("dir", pc_dir())))
		"send":
			return an_moveeye()
		"get":
			var nm := str(d.get("name", ""))
			if _mw_wait.is_empty() or nm != str(_mw_wait.get("name", "")) or not FileAccess.file_exists(TMP + "/" + nm):
				return {"ok": false, "error": "no such backup"}
			var b := FileAccess.get_file_as_bytes(TMP + "/" + nm)
			_mw_wait["got"] = true
			return {"ok": true, "name": nm, "bytes": b.size(), "sha256": _sha(b), "zip_b64": Marshalls.raw_to_base64(b), "sim": _version()}
		"ack":
			var nm2 := str(d.get("name", ""))
			if nm2 != "" and nm2 == str(_mw_wait.get("name", "")):
				_mw_wait = {}
				_rm_tree(TMP)
				if bool(d.get("ok", false)):
					_toast(T.t("In der MoveEye-Sicherung: {z}", {"z": nm2}))
					_log("Sicherung an MoveEye: " + nm2)
				else:
					_toast("⚠ " + T.t("MoveEye konnte die Sicherung nicht ablegen:") + " " + str(d.get("error", "")))
			return {"ok": true}
		"check":
			return check_zip(str(d.get("path", "")), _version())
		"restore":
			if d.get("confirm", false) != true:
				return {"ok": false, "error": "only with \"confirm\": true"}
			var path := str(d.get("path", ""))
			var from_mw := d.has("zip_b64")
			if from_mw:
				var raw := Marshalls.base64_to_raw(str(d.get("zip_b64", "")))
				if raw.is_empty():
					return {"ok": false, "error": T.t("Kein gültiges ZIP oder beschädigt – nichts geändert.")}
				_rm_tree(TMP)
				DirAccess.make_dir_recursive_absolute(TMP)
				path = TMP + "/eingang.zip"
				var f := FileAccess.open(path, FileAccess.WRITE)
				if f == null:
					return {"ok": false, "error": "cannot write"}
				f.store_buffer(raw)
				f.close()
			var r := start_restore(path, "MoveEye" if from_mw else "control", not bool(d.get("no_restart", false)))
			if from_mw and bool(r.get("ok", false)) and bool(d.get("want_before", true)):
				var vb := FileAccess.get_file_as_bytes(str(r["vorher"]))
				if vb.size() > 0 and vb.size() <= MAX_MW:
					r["vorher_b64"] = Marshalls.raw_to_base64(vb)          # MoveEye keeps it too (undo from there)
			return r
	return {"ok": false, "error": "do: info | make | send | get | ack | check | restore (confirm: true)"}
