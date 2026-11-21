extends CanvasLayer
## Testkanal (Besitzer 21.11.2026: «Dateien schieben ist mühsam»): im Entwickler-Bereich (Mehr → Entwickler) zwei Knöpfe
##   «🧪 Neuste Testversion holen» – «Testversion – nicht signiert, nur zum Ausprobieren»
##   «⏪ Zur letzten Version zurück»
## Quelle: eine feste Vorabversion auf GitHub, Tag «sim-test» (nie «latest», nie in versions.json, kein Gerät und kein
## MoveEye schaut dort nach). Gebaut vom Workflow «Sim-Pakete» mit testkanal=true (sim_pi.yml, Job «testkanal»), der bei jeder
## Testrunde die Assets überschreibt: MoveEyeSim_Test_Windows.zip, MoveEyeSim_Test_Linux.zip und sim-test.json
##   {"kanal": "sim-test", "label", "branch", "commit", "built_at", "files": [{"platform": win | linux, "name", "size", "sha256"}]}
## Ablauf: sim-test.json holen → Commit, Datum, Grösse zeigen und fragen → ZIP holen → Grösse + SHA-256 prüfen (sonst nichts
## anfassen) → die laufende Datei als «.vorher» sichern (eine Sicherung; auf einer Testversion bleibt die erste) → derselbe
## sichere Tausch wie beim signierten Update (update.gd _install: die laufende .exe umbenennen, die neue hinlegen) → Neustart.
## «Zurück»: die Sicherung wieder an ihren Platz (gleicher Tausch), Neustart. Nie automatisch.
## Solange eine Testversion läuft (Marke user://testkanal.json mit Grösse + Zeit der Programmdatei): der Fenstertitel sagt
## «Testversion: <Commit>», das normale Update bietet nichts an (nur der Hinweis «Testkanal aktiv»). Das normale Update
## bleibt sonst genau wie es ist (nur signierte Versionen, über versions.json / version.json).
## Tests: werkzeuge/testkanal_test.gd (lokaler HTTP-Server statt GitHub: Manifest, falsche Prüfsumme, Sicherung + Zurück).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Updater = preload("res://scripts/update.gd")

const RELEASE := "https://github.com/DonElektro/MotionWatch/releases/download/sim-test/"
const MANIFEST := "sim-test.json"
const MARKE := "user://testkanal.json"
const MAX_BYTES := 600 * 1024 * 1024

var main
var base := RELEASE                  # tests: a local server
var exe_pfad := ""                   # tests: a file instead of the running program
var neustart := true                 # tests: no restart
var ergebnis := ""
var _panel: PanelContainer
var _text: Label
var _bar: ProgressBar
var _row: HBoxContainer
var _wahl := -1


# =======================================================================================================================
# pure helpers (tested without a window)
# =======================================================================================================================
static func parse_manifest(txt: String) -> Dictionary:
	"""{ok, m} or {ok: false, error}"""
	var j = JSON.parse_string(txt)
	if not (j is Dictionary):
		return {"ok": false, "error": "kein JSON"}
	var m: Dictionary = j
	if str(m.get("kanal", "")) != "sim-test":
		return {"ok": false, "error": "falscher Kanal"}
	var c := str(m.get("commit", ""))
	if c.length() < 7 or c.length() > 40 or not c.is_valid_hex_number(false):
		return {"ok": false, "error": "Commit fehlt"}
	var fl = m.get("files", null)
	if not (fl is Array) or (fl as Array).is_empty():
		return {"ok": false, "error": "keine Dateien"}
	var re := RegEx.create_from_string("^[A-Za-z0-9._-]+\\.zip$")
	for f in fl:
		if not (f is Dictionary):
			return {"ok": false, "error": "Datei-Eintrag"}
		var nm := str(f.get("name", ""))
		var sha := str(f.get("sha256", "")).to_lower()
		var sz := int(f.get("size", 0))
		if re.search(nm) == null:
			return {"ok": false, "error": "Dateiname %s" % nm}
		if sha.length() != 64 or not sha.is_valid_hex_number(false):
			return {"ok": false, "error": "Prüfsumme %s" % nm}
		if sz <= 0 or sz > MAX_BYTES:
			return {"ok": false, "error": "Grösse %s" % nm}
		if not str(f.get("platform", "")) in ["win", "linux"]:
			return {"ok": false, "error": "Plattform %s" % nm}
	return {"ok": true, "m": m}


static func datei_fuer(m: Dictionary, plat: String) -> Dictionary:
	for f in m.get("files", []):
		if str(f.get("platform", "")) == plat:
			return f
	return {}


static func plattform() -> String:
	return "win" if OS.get_name() == "Windows" else "linux"


static func pruefen(pfad: String, size: int, sha: String) -> String:
	"""'' = size and SHA-256 match, else why not"""
	var f := FileAccess.open(pfad, FileAccess.READ)
	if f == null:
		return "Datei fehlt"
	if f.get_length() != size:
		f.close()
		return "falsche Grösse"
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	f.close()
	if h.finish().hex_encode() != sha.to_lower():
		return "Prüfsumme stimmt nicht"
	return ""


static func backup_pfad(exe: String) -> String:
	return exe + ".vorher"


static func _stempel(exe: String) -> Dictionary:
	var f := FileAccess.open(exe, FileAccess.READ)
	var sz := f.get_length() if f != null else -1
	if f != null:
		f.close()
	return {"size": sz, "mtime": FileAccess.get_modified_time(exe)}


static func aktiv(exe := "") -> Dictionary:
	"""the test build that runs now ({commit, label, built_at}) or {} - the mark only counts while the program file is the one
	that was installed (same size and time); else it is removed"""
	if not FileAccess.file_exists(MARKE):
		return {}
	var j = JSON.parse_string(FileAccess.get_file_as_string(MARKE))
	if not (j is Dictionary):
		return {}
	var e := exe if exe != "" else Updater.real_exe()
	var st := _stempel(e)
	if int(j.get("size", -2)) != int(st["size"]) or int(j.get("mtime", -2)) != int(st["mtime"]):
		if OS.has_feature("template") or exe != "":
			DirAccess.remove_absolute(ProjectSettings.globalize_path(MARKE))
		return {}
	return j


static func titel_zusatz() -> String:
	var a := aktiv()
	return "" if a.is_empty() else "  ·  " + T.t("Testversion: %s", [str(a.get("commit", "")).left(7)])


static func hinweis() -> String:
	return T.t("Testkanal aktiv – normale Updates erst nach «Zur letzten Version zurück».")


# =======================================================================================================================
# the window
# =======================================================================================================================
func _ui() -> void:
	if _panel != null:
		return
	layer = 125
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0, 0, 0, 0.55)
	add_child(bg)
	_panel = PanelContainer.new()
	_panel.theme = UI.theme()
	_panel.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.08, 0.11, 0.98), UI.ORG, 14, 18, 1))
	add_child(_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	v.custom_minimum_size = Vector2(440, 0)
	_panel.add_child(v)
	var t := Label.new()
	t.text = T.t("🧪 Testversion – nicht signiert, nur zum Ausprobieren")
	t.add_theme_color_override("font_color", UI.ORG)
	t.add_theme_font_size_override("font_size", 17)
	v.add_child(t)
	_text = Label.new()
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(440, 0)
	v.add_child(_text)
	_bar = ProgressBar.new()
	_bar.visible = false
	v.add_child(_bar)
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 8)
	v.add_child(_row)
	_mitte.call_deferred()


func _mitte() -> void:
	if _panel != null and is_inside_tree():
		_panel.size = Vector2.ZERO
		_panel.position = (get_viewport().get_visible_rect().size - _panel.get_combined_minimum_size()) * 0.5


func _knoepfe(L: Array) -> void:
	for c in _row.get_children():
		c.queue_free()
	for i in range(L.size()):
		var b := Button.new()
		b.text = str(L[i])
		b.custom_minimum_size = Vector2(150, 40)
		var k := i
		b.pressed.connect(func(): _wahl = k)
		if i == 0 and L.size() > 1:
			UI.primary(b)
		_row.add_child(b)
	_mitte.call_deferred()


func _frage(text: String, L: Array) -> int:
	_ui()
	_text.text = text
	_knoepfe(L)
	_wahl = -1
	while _wahl < 0:
		await get_tree().process_frame
	return _wahl


func _melden(text: String) -> void:
	ergebnis = text
	if not neustart:
		return                                             # tests: no waiting for «OK»
	await _frage(text, [T.t("OK")])


# =======================================================================================================================
# «Neuste Testversion holen»
# =======================================================================================================================
func holen(bestaetigt := false) -> String:
	"""returns '' when installed (and restarting), else what happened"""
	if OS.has_feature("web") or (OS.get_name() == "Linux" and Engine.get_architecture_name().begins_with("arm")):
		await _melden(T.t("Den Testkanal gibt es nur für Windows und Linux (PC)."))
		return ergebnis
	_ui()
	_text.text = T.t("Hole die Angaben der Testversion …")
	_knoepfe([])
	var h := HTTPRequest.new()
	h.timeout = 15.0
	add_child(h)
	if h.request(base + MANIFEST + "?t=%d" % int(Time.get_unix_time_from_system())) != OK:
		await _melden(T.t("Die Anfrage liess sich nicht starten."))
		return ergebnis
	var r: Array = await h.request_completed
	if r[0] != HTTPRequest.RESULT_SUCCESS or r[1] != 200:
		await _melden(T.t("Keine Testversion gefunden (GitHub antwortet %s).") % str(r[1]))
		return ergebnis
	var pm := parse_manifest((r[3] as PackedByteArray).get_string_from_utf8())
	if not bool(pm["ok"]):
		await _melden(T.t("Die Angaben der Testversion sind ungültig (%s).") % str(pm["error"]))
		return ergebnis
	var m: Dictionary = pm["m"]
	var f := datei_fuer(m, plattform())
	if f.is_empty():
		await _melden(T.t("Für dieses System gibt es keine Testversion."))
		return ergebnis
	var jetzt := aktiv(exe_pfad)
	if not jetzt.is_empty() and str(jetzt.get("commit", "")) == str(m["commit"]):
		await _melden(T.t("Diese Testversion läuft schon (%s).") % str(m["commit"]).left(7))
		return ergebnis
	var info := T.t("Testversion %s\nZweig: %s · Commit: %s\nGebaut: %s\nGrösse: %.1f MB\n\nNicht signiert – nur zum Ausprobieren. Die jetzige Version bleibt als Sicherung («⏪ Zur letzten Version zurück»).") % [
			str(m.get("label", "")), str(m.get("branch", "")), str(m["commit"]).left(7), str(m.get("built_at", "")), float(f["size"]) / 1048576.0]
	if not bestaetigt and await _frage(info, [T.t("Installieren"), T.t("Abbrechen")]) != 0:
		ergebnis = "abgebrochen"
		queue_free()
		return ergebnis
	_knoepfe([])
	_bar.visible = true
	var zip := ProjectSettings.globalize_path("user://testkanal.zip")
	if FileAccess.file_exists(zip):
		DirAccess.remove_absolute(zip)
	h.timeout = 0.0
	h.download_file = zip
	h.download_chunk_size = 1 << 20
	h.body_size_limit = int(f["size"]) + 4096
	if h.request(base + str(f["name"])) != OK:
		await _melden(T.t("Der Download liess sich nicht starten."))
		return ergebnis
	_text.text = T.t("Lade die Testversion …")
	var rr := []                                           # lambdas copy locals: fill the array instead
	h.request_completed.connect(func(a, b, _c, _d): rr.append_array([a, b]), CONNECT_ONE_SHOT)
	while rr.is_empty():
		await get_tree().create_timer(0.3).timeout
		_bar.value = 100.0 * float(h.get_downloaded_bytes()) / maxf(1.0, float(f["size"]))
	if rr[0] != HTTPRequest.RESULT_SUCCESS or rr[1] != 200:
		DirAccess.remove_absolute(zip)
		await _melden(T.t("Download abgebrochen (%s / %s).") % [str(rr[0]), str(rr[1])])
		return ergebnis
	_text.text = T.t("Prüfe Grösse und Prüfsumme …")
	await get_tree().process_frame
	var why := pruefen(zip, int(f["size"]), str(f["sha256"]))
	if why != "":
		DirAccess.remove_absolute(zip)
		await _melden(T.t("Die Datei wurde nicht benutzt: %s.") % T.t(why))
		return ergebnis
	var err := installieren(zip, m)
	DirAccess.remove_absolute(zip)
	if err != "":
		await _melden(T.t("Installieren ging nicht: %s") % err)
		return ergebnis
	ergebnis = ""
	_text.text = T.t("Fertig. Der Simulator startet neu …")
	await _neu_starten()
	return ""


func installieren(zip: String, m: Dictionary) -> String:
	"""the backup (one: the first non-test version stays while test builds follow), then the same swap as the signed update"""
	var exe := exe_pfad if exe_pfad != "" else Updater.real_exe()
	var bk := backup_pfad(exe)
	if aktiv(exe).is_empty() or not FileAccess.file_exists(bk):
		if FileAccess.file_exists(bk):
			DirAccess.remove_absolute(bk)
		if DirAccess.copy_absolute(exe, bk) != OK:
			return T.t("Die Sicherung der jetzigen Version liess sich nicht anlegen.")
	var up = Updater.new()
	var err: String = up._install(zip, exe)
	up.free()
	if err != "":
		return err
	var mk := {"commit": str(m.get("commit", "")), "label": str(m.get("label", "")), "built_at": str(m.get("built_at", "")),
			"branch": str(m.get("branch", ""))}
	mk.merge(_stempel(exe), true)
	var fw := FileAccess.open(MARKE, FileAccess.WRITE)
	if fw != null:
		fw.store_string(JSON.stringify(mk))
		fw.close()
	return ""


# =======================================================================================================================
# «Zur letzten Version zurück»
# =======================================================================================================================
func zurueck(bestaetigt := false) -> String:
	var exe := exe_pfad if exe_pfad != "" else Updater.real_exe()
	var bk := backup_pfad(exe)
	if not FileAccess.file_exists(bk):
		await _melden(T.t("Es gibt keine Sicherung einer früheren Version."))
		return ergebnis
	if not bestaetigt and await _frage(T.t("Zurück zur Version vor der Testversion? Der Simulator startet danach neu."), [T.t("Zurück"), T.t("Abbrechen")]) != 0:
		ergebnis = "abgebrochen"
		queue_free()
		return ergebnis
	var err := zurueck_tauschen(exe)
	if err != "":
		await _melden(err)
		return ergebnis
	ergebnis = ""
	if _text != null:
		_text.text = T.t("Fertig. Der Simulator startet neu …")
	await _neu_starten()
	return ""


static func zurueck_tauschen(exe: String) -> String:
	"""the backup goes back in place of the program file (the running one is renamed first, like update.gd does)"""
	var bk := backup_pfad(exe)
	var old := exe + ".old"
	var k := 2
	while FileAccess.file_exists(old) and DirAccess.remove_absolute(old) != OK and k < 50:
		old = exe + ".old%d" % k
		k += 1
	if DirAccess.rename_absolute(exe, old) != OK:
		return T.t("Die laufende Datei lässt sich nicht ersetzen. Läuft der Simulator zweimal?")
	if DirAccess.rename_absolute(bk, exe) != OK:
		DirAccess.rename_absolute(old, exe)
		return T.t("Die Sicherung lässt sich nicht zurücklegen.")
	if OS.get_name() != "Windows":
		OS.execute("chmod", ["+x", exe])
	if FileAccess.file_exists(MARKE):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(MARKE))
	return ""


func _neu_starten() -> void:
	if not neustart:
		return
	await get_tree().create_timer(0.8).timeout
	var exe := Updater.real_exe()
	var args := OS.get_cmdline_args()
	var user: PackedStringArray = main.restart_args() if main != null and main.has_method("restart_args") else OS.get_cmdline_user_args()
	args.append("--")
	args.append_array(user)
	if main != null and main.has_method("release_ports"):
		main.release_ports()
	OS.create_process(exe, args)
	get_tree().quit()


# ---- the two buttons (devtool_extra.gd) ----------------------------------------------------------------------------------
static func knoepfe(m, parent: Control) -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	parent.add_child(box)
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 6)
	box.add_child(row)
	var b1 := Button.new()
	b1.text = T.t("🧪 Neuste Testversion holen")
	b1.tooltip_text = T.t("Testversion – nicht signiert, nur zum Ausprobieren")
	b1.pressed.connect(func(): starte(m, "holen"))
	row.add_child(b1)
	var b2 := Button.new()
	b2.text = T.t("⏪ Zur letzten Version zurück")
	b2.pressed.connect(func(): starte(m, "zurueck"))
	row.add_child(b2)
	var l := Label.new()
	var a := aktiv()
	l.text = T.t("Testversion – nicht signiert, nur zum Ausprobieren") + ("" if a.is_empty() else "  ·  " + T.t("läuft: %s", [str(a.get("commit", "")).left(7)]))
	l.add_theme_color_override("font_color", UI.ORG)
	l.add_theme_font_size_override("font_size", 12)
	box.add_child(l)


static func starte(m, was: String) -> void:
	var k = load("res://scripts/testkanal.gd").new()
	k.main = m
	m.add_child(k)
	if was == "zurueck":
		await k.zurueck()
	else:
		await k.holen()
	if is_instance_valid(k):
		k.queue_free()
