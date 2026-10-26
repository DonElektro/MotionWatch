extends CanvasLayer
## Before the start (from 3D-1.7): is there a newer simulator on GitHub (simulator3d/version.json)? Then a note with the buttons
## «Jetzt aktualisieren» and «Ohne Update starten». Updating: download the ZIP, check size and SHA-256, take the new files out of it,
## put the new .exe in place of the running one (Windows allows renaming a running .exe) and start again. Without internet the
## simulator starts after a few seconds as before.

signal chosen(update: bool)

const BASE := "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/"
const INFO_FILE := "simulator3d/version.json"

var base := BASE
var info := {}
var title: Label
var text: Label
var bar: ProgressBar
var b_upd: Button
var b_skip: Button
var http: HTTPRequest
var downloading := false
var manual := false           # started with the button «Nach Updates suchen» (not at the start of the simulator)


static func vnum(v: String) -> Array:
	"""'3D-1.6' -> [1, 6]"""
	var out := []
	for p in v.trim_prefix("3D-").split("."):
		out.append(int(p))
	return out


static func newer(a: String, b: String) -> bool:
	"""is version a newer than b?"""
	var x := vnum(a)
	var y := vnum(b)
	for i in range(max(x.size(), y.size())):
		var p: int = x[i] if i < x.size() else 0
		var q: int = y[i] if i < y.size() else 0
		if p != q:
			return p > q
	return false


func check(current: String, url := "") -> void:
	"""await this: returns when the simulator may start (or never, when it restarts itself after an update)"""
	if url != "":
		base = url if url.ends_with("/") else url + "/"
	_remove_old()
	_build_ui()
	title.text = "Motion Watch – 3D-Simulator %s" % current
	text.text = "Suche nach einer neuen Version …"
	http = HTTPRequest.new()
	http.timeout = 6.0
	add_child(http)
	if http.request(base + INFO_FILE) != OK:
		await _note("Die Suche liess sich nicht starten.")
		return
	var r: Array = await http.request_completed
	if r[0] != HTTPRequest.RESULT_SUCCESS or r[1] != 200:
		print("update check: no answer (%s / %s)" % [r[0], r[1]])
		await _note("GitHub antwortet nicht (Internet da?). Versuch es später noch einmal.")
		return
	var d = JSON.parse_string((r[3] as PackedByteArray).get_string_from_utf8())
	if typeof(d) != TYPE_DICTIONARY or not d.has("version") or not d.has("sha256") or not d.has("size"):
		await _note("Die Versions-Angabe auf GitHub ist nicht lesbar.")
		return
	info = d
	if not newer(str(d["version"]), current):
		print("update check: %s is the newest" % current)
		await _note("Du hast schon die neuste Version (%s)." % current)
		return
	text.text = "Eine neue Version ist da: %s (du hast %s).\n\n%s" % [d["version"], current, str(d.get("notes", ""))]
	if not OS.has_feature("template"):
		text.text += "\n\n(Im Godot-Editor wird nicht aktualisiert.)"
		b_upd.disabled = true
	if manual:
		b_skip.text = "Später"
		text.text += "\n\nDer Simulator startet nach dem Update neu. Läuft Motion Watch auf diesem PC, danach bitte wieder starten."
	b_upd.visible = true
	b_skip.visible = true
	b_upd.grab_focus()
	var up: bool = await chosen
	if not up:
		return
	await _update()


func _note(msg: String) -> void:
	"""only when the button «Nach Updates suchen» was pressed: say the result and wait for «OK» (at the start: say nothing)"""
	if not manual:
		return
	text.text = msg
	b_skip.text = "OK"
	b_skip.visible = true
	b_skip.grab_focus()
	await chosen


func _build_ui() -> void:
	layer = 100
	var bg := ColorRect.new()
	bg.color = Color(0.06, 0.07, 0.09)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var cc := CenterContainer.new()
	cc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(cc)
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.12, 0.14, 0.18)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(22)
	pc.add_theme_stylebox_override("panel", sb)
	pc.custom_minimum_size = Vector2(560, 0)
	cc.add_child(pc)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 14)
	pc.add_child(vb)
	title = Label.new()
	title.add_theme_font_size_override("font_size", 22)
	vb.add_child(title)
	text = Label.new()
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.custom_minimum_size = Vector2(516, 0)
	text.add_theme_font_size_override("font_size", 16)
	vb.add_child(text)
	bar = ProgressBar.new()
	bar.visible = false
	bar.custom_minimum_size = Vector2(0, 22)
	vb.add_child(bar)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	vb.add_child(hb)
	b_upd = Button.new()
	b_upd.text = "Jetzt aktualisieren"
	b_upd.add_theme_font_size_override("font_size", 17)
	b_upd.visible = false
	b_upd.pressed.connect(func(): chosen.emit(true))
	hb.add_child(b_upd)
	b_skip = Button.new()
	b_skip.text = "Ohne Update starten"
	b_skip.add_theme_font_size_override("font_size", 17)
	b_skip.visible = false
	b_skip.pressed.connect(func(): chosen.emit(false))
	hb.add_child(b_skip)


func _process(_dt: float) -> void:
	if downloading and http != null:
		var got := http.get_downloaded_bytes()
		var size := float(info.get("size", 1))
		bar.value = 100.0 * got / max(1.0, size)
		text.text = "Lade %s … %.1f von %.1f MB" % [info["version"], got / 1048576.0, size / 1048576.0]


func _fail(msg: String) -> void:
	"""something went wrong: say what, and start the old version"""
	downloading = false
	bar.visible = false
	text.text = "Das Update hat nicht geklappt: %s\n\nDie bisherige Version startet. Du kannst den Simulator auch von Hand neu herunterladen." % msg
	b_upd.visible = false
	b_skip.visible = true
	b_skip.disabled = false
	b_skip.text = "Weiter"
	await chosen


func _update() -> void:
	var exe := OS.get_executable_path().trim_suffix(".old")     # remember it now: after the renaming it may point to the .old file
	b_upd.visible = false
	b_skip.visible = false
	bar.visible = true
	var zip_path := ProjectSettings.globalize_path("user://update.zip")
	var file := str(info.get("file", "simulator3d/MotionWatch3D_Simulator.zip"))
	if FileAccess.file_exists(zip_path):
		DirAccess.remove_absolute(zip_path)
	var got_it := false
	if OS.get_name() == "Windows":                  # curl.exe of Windows: fast, Windows certificates and proxy
		got_it = await _curl(base + file, zip_path)
	if not got_it:
		http.timeout = 0.0
		http.download_file = zip_path
		http.download_chunk_size = 1 << 20          # bigger pieces: much faster while the simulation runs
		http.body_size_limit = int(info["size"]) + 4096
		if http.request(base + file) != OK:
			await _fail("Download liess sich nicht starten.")
			return
		downloading = true
		var r: Array = await http.request_completed
		downloading = false
		if r[0] != HTTPRequest.RESULT_SUCCESS or r[1] != 200:
			await _fail("Download abgebrochen (Fehler %s / %s)." % [r[0], r[1]])
			return
	text.text = "Prüfe die Datei …"
	await get_tree().process_frame
	var f := FileAccess.open(zip_path, FileAccess.READ)
	if f == null or f.get_length() != int(info["size"]):
		await _fail("Die Datei hat die falsche Grösse.")
		return
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	f.close()
	if h.finish().hex_encode() != str(info["sha256"]).to_lower():
		DirAccess.remove_absolute(zip_path)
		await _fail("Die Prüfsumme stimmt nicht – die Datei wurde nicht benutzt.")
		return
	text.text = "Packe aus …"
	await get_tree().process_frame
	var err := _install(zip_path, exe)
	DirAccess.remove_absolute(zip_path)
	if err != "":
		await _fail(err)
		return
	text.text = "Fertig. Der Simulator startet neu …"
	await get_tree().create_timer(0.8).timeout
	var args := OS.get_cmdline_args()
	var user := OS.get_cmdline_user_args()
	var ai := user.find("--angle-tried")         # graphics options are not passed on: let main.gd find the virtual machine again
	if ai >= 0:
		user.remove_at(ai)
	args.append("--")
	args.append_array(user)
	args.append("--updated")
	OS.create_process(exe, args)
	get_tree().quit()
	await get_tree().create_timer(60.0).timeout       # never come back


func _curl(u: String, to: String) -> bool:
	"""download with curl.exe in a thread; the bar shows the size of the file so far"""
	var th := Thread.new()
	th.start(func():
		var out := []
		return OS.execute("curl.exe", ["-L", "--fail", "-s", "-S", "--retry", "2", "-o", to, u], out, true, false))
	var size := float(info.get("size", 1))
	while th.is_alive():
		await get_tree().create_timer(0.3).timeout
		var got := 0
		var f := FileAccess.open(to, FileAccess.READ)
		if f != null:
			got = f.get_length()
			f.close()
		bar.value = 100.0 * got / max(1.0, size)
		text.text = "Lade %s … %.1f von %.1f MB" % [info["version"], got / 1048576.0, size / 1048576.0]
	var code: int = th.wait_to_finish()
	print("update: curl exit %d" % code)
	return code == 0 and FileAccess.file_exists(to)


func _install(zip_path: String, exe: String) -> String:
	"""take the files out of the ZIP and put them next to the .exe; the running .exe is renamed to .old first"""
	var dir := exe.get_base_dir()
	var me := exe.get_file()
	var z := ZIPReader.new()
	if z.open(zip_path) != OK:
		return "Die ZIP-Datei lässt sich nicht öffnen."
	var found := false
	for name in z.get_files():
		if name.ends_with("/") or name.get_file() == "":
			continue
		var target := dir.path_join(name.get_file())
		var data := z.read_file(name)
		if name.get_file() == me:
			found = true
			var tmp := target + ".new"
			var fw := FileAccess.open(tmp, FileAccess.WRITE)
			if fw == null:
				z.close()
				return "Kann im Ordner %s nicht schreiben." % dir
			fw.store_buffer(data)
			fw.close()
			if FileAccess.file_exists(exe + ".old"):
				DirAccess.remove_absolute(exe + ".old")
			if DirAccess.rename_absolute(exe, exe + ".old") != OK:
				DirAccess.remove_absolute(tmp)
				z.close()
				return "Die laufende Datei lässt sich nicht ersetzen."
			if DirAccess.rename_absolute(tmp, exe) != OK:
				DirAccess.rename_absolute(exe + ".old", exe)       # put the old one back
				z.close()
				return "Die neue Datei lässt sich nicht hinlegen."
		else:
			var fo := FileAccess.open(target, FileAccess.WRITE)
			if fo != null:
				fo.store_buffer(data)
				fo.close()
	z.close()
	if not found:
		DirAccess.remove_absolute(exe + ".old")
		return "In der ZIP-Datei fehlt %s." % me
	if OS.get_name() != "Windows":
		OS.execute("chmod", ["+x", exe])
	return ""


func _remove_old() -> void:
	"""the .exe of the version before the update (it could not be deleted while it was running)"""
	var old := OS.get_executable_path().trim_suffix(".old") + ".old"
	if FileAccess.file_exists(old):
		DirAccess.remove_absolute(old)
