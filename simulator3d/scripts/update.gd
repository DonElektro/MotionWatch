extends CanvasLayer
## Before the start (from 3D-1.7): is there a newer simulator on GitHub (simulator3d/version.json)? Then a note with the buttons
## «Jetzt aktualisieren» and «Ohne Update starten». Updating: download the ZIP, check size and SHA-256, take the new files out of it,
## put the new .exe in place of the running one (Windows allows renaming a running .exe) and start again. Without internet the
## simulator starts after a few seconds as before.

signal chosen(update: bool)

const BASE := "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/"
const INFO_FILE := "simulator3d/version.json"
# 3D-4.24: the program file is called MoveEyeSim3D.exe (Linux MoveEyeSim3D.x86_64), before MotionWatch3D.exe. The ZIP (path
# in the repository unchanged, old installs and older MoveEye versions fetch it there) holds for the change both files: the old
# updater of an install looks for MotionWatch3D.exe, puts it in place of the running file and starts it - that one sees its
# old name and starts MoveEyeSim3D.exe (written next to it from the same ZIP) instead, see old_name_forward().
const EXE_STEM := "MoveEyeSim3D"
const OLD_STEM := "MotionWatch3D"
const GONE_FILES := ["Start auf Port 8766.bat"]   # Ports aufräumen: umbenannt (8766 = Tunnel-Port von MoveEye) - nach dem Update weg

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
var quiet := false            # check in the background: show nothing unless there is a new version
var auto := false             # install without asking (setting «Neue Versionen automatisch installieren» or from far away):
							  # 15 seconds to cancel, then it installs by itself
var result := ""              # what came out (for the window and the web page of MoveEye)
var choice := -1              # -1 not decided, 0 later / OK, 1 update


const V = preload("res://scripts/versionen.gd")   # Versionierung 3.0.0: both schemas («3D-4.82» and «3.0.0»), see there


static func vnum(v: String) -> Array:
	"""'3D-4.82' -> [2, 82, 0], '3.0.0' -> [3, 0, 0] (versionen.gd)"""
	return V.key(v)


static func newer(a: String, b: String) -> bool:
	"""is version a newer than b?"""
	return V.newer(a, b)


func check(current: String, url := "") -> void:
	"""await this: returns when the simulator may start (or never, when it restarts itself after an update)"""
	if url != "":
		base = url if url.ends_with("/") else url + "/"
	if OS.get_name() == "Linux" and Engine.get_architecture_name().begins_with("arm"):
		result = "Auf dem Pi bringt MoveEye die neue Version"   # 3D-3.43: the package here is for Windows
		return
	_remove_old()
	if not quiet:
		_build_ui()
		title.text = V.label(current)
		text.text = "Suche nach einer neuen Version …"
	http = HTTPRequest.new()
	http.timeout = 6.0
	add_child(http)
	if http.request(base + INFO_FILE + "?t=%d" % int(Time.get_unix_time_from_system())) != OK:   # 3D-3.81: past the cache
		await _note("Die Suche liess sich nicht starten.")
		return
	var r: Array = await http.request_completed
	if r[0] != HTTPRequest.RESULT_SUCCESS or r[1] != 200:
		print("update check: no answer (%s / %s)" % [r[0], r[1]])
		result = "GitHub antwortet nicht"
		await _note("GitHub antwortet nicht (Internet da?). Versuch es später noch einmal.")
		return
	var d = JSON.parse_string((r[3] as PackedByteArray).get_string_from_utf8())
	if typeof(d) != TYPE_DICTIONARY or not d.has("version") or not d.has("sha256") or not d.has("size"):
		await _note("Die Versions-Angabe auf GitHub ist nicht lesbar.")
		return
	info = d
	var latest := V.of_info(d)                    # Versionierung 3.0.0: «ver» (new number), «version» = for old simulators
	info["version"] = V.plain(latest)             # (the progress text and the messages show the new number)
	if not newer(latest, current):
		print("update check: %s is the newest" % current)
		result = "schon die neuste Version (%s)" % current
		await _note("Du hast schon die neuste Version (%s)." % current)
		return
	result = "neue Version %s gefunden" % info["version"]
	if quiet:
		_build_ui()
		title.text = V.label(current)
	text.text = "Eine neue Version ist da: %s (du hast %s).\n\n%s" % [V.label(latest), V.plain(current), str(d.get("notes", ""))]
	if not OS.has_feature("template"):
		text.text += "\n\n(Im Godot-Editor wird nicht aktualisiert.)"
		b_upd.disabled = true
	if manual:
		b_skip.text = "Später"
		text.text += "\n\nDer Simulator startet nach dem Update neu. Läuft MoveEye auf diesem PC, danach bitte wieder starten."
	b_upd.visible = true
	b_skip.visible = true
	b_upd.grab_focus()
	var up := false
	if auto and OS.has_feature("template"):
		b_upd.text = "Jetzt installieren"
		b_skip.text = "Abbrechen"
		var base_text := text.text
		choice = -1
		for i in range(15, 0, -1):
			text.text = base_text + "\n\nWird in %d s automatisch installiert, danach startet der Simulator neu." % i
			await get_tree().create_timer(1.0).timeout
			if choice != -1:
				break
		up = choice != 0
	else:
		up = await chosen
	if not up:
		result = "Update auf %s abgebrochen" % info["version"]
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
	b_upd.pressed.connect(func():
		choice = 1
		chosen.emit(true))
	hb.add_child(b_upd)
	b_skip = Button.new()
	b_skip.text = "Ohne Update starten"
	b_skip.add_theme_font_size_override("font_size", 17)
	b_skip.visible = false
	b_skip.pressed.connect(func():
		choice = 0
		chosen.emit(false))
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
	result = "Update hat nicht geklappt: " + msg
	if auto:                                        # maybe nobody is at the PC: go on by itself after 20 s
		choice = -1
		for i in range(20):
			await get_tree().create_timer(1.0).timeout
			if choice != -1:
				break
		return
	await chosen


func _update() -> void:
	var exe := real_exe()                           # remember it now: after the renaming it may point to the .old file
	b_upd.visible = false
	b_skip.visible = false
	bar.visible = true
	var zip_path := ProjectSettings.globalize_path("user://update.zip")
	var file := str(info.get("file", "simulator3d/MotionWatch3D_Simulator.zip"))
	var ok_file := false
	for attempt in range(3):                        # GitHub may hand out the old ZIP for some minutes after a new version
		var u := base + file                        # (cache): then wait and ask again, the address made new (from 3D-3.4)
		if attempt > 0:
			for i in range(20 * attempt, 0, -1):
				text.text = "GitHub liefert noch die alte Datei – neuer Versuch in %d s …" % i
				await get_tree().create_timer(1.0).timeout
			u += "?v=%s%d" % [str(info["sha256"]).left(12), Time.get_ticks_msec()]
		var why := await _download_check(u, zip_path)
		if why == "":
			ok_file = true
			break
		if why.begins_with("!"):
			await _fail(why.substr(1))
			return
		if attempt == 2:
			await _fail(why)
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
	var user: PackedStringArray = get_parent().restart_args() if get_parent().has_method("restart_args") else OS.get_cmdline_user_args()
	var ai := user.find("--angle-tried")         # graphics options are not passed on: let main.gd find the virtual machine again
	if ai >= 0:
		user.remove_at(ai)
	args.append("--")
	args.append_array(user)
	args.append("--updated")
	if get_parent().has_method("release_ports"):
		get_parent().release_ports()          # 3D-3.68: the new simulator must not inherit port 8765
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
		if name.get_file().begins_with(OLD_STEM + "."):
			continue                                # 3D-4.24: the copy under the old name is only for old updaters
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
			# the running .exe gets another name (Windows allows that); an old one that is still running (a second
			# simulator, or the one before the last update) cannot be deleted: then a free name (from 3D-3.4)
			var old := exe + ".old"
			if FileAccess.file_exists(old):
				DirAccess.remove_absolute(old)
			var k := 2
			while FileAccess.file_exists(old) and k < 50:
				old = exe + ".old%d" % k
				if FileAccess.file_exists(old):
					DirAccess.remove_absolute(old)
				k += 1
			if DirAccess.rename_absolute(exe, old) != OK:
				DirAccess.remove_absolute(tmp)
				z.close()
				return "Die laufende Datei lässt sich nicht ersetzen. Läuft der Simulator zweimal? Bitte alle Simulator-Fenster schliessen (auch das kleine Kästchen) und neu starten."
			if DirAccess.rename_absolute(tmp, exe) != OK:
				DirAccess.rename_absolute(old, exe)                # put the old one back
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
	for g in GONE_FILES:                            # alte Beilagen, die es in der neuen ZIP nicht mehr gibt
		if FileAccess.file_exists(dir.path_join(g)):
			DirAccess.remove_absolute(dir.path_join(g))
	if OS.get_name() != "Windows":
		OS.execute("chmod", ["+x", exe])
	return ""


func _remove_old() -> void:
	"""the .exe of the version before the update (it could not be deleted while it was running)"""
	var exe := real_exe()
	for f in DirAccess.get_files_at(exe.get_base_dir()):
		if f.begins_with(exe.get_file() + ".old"):
			DirAccess.remove_absolute(exe.get_base_dir().path_join(f))   # fails quietly while it still runs


static func old_name_forward() -> bool:
	"""3D-4.24: started under the old name MotionWatch3D.exe (an old install updated itself, the autostart or a link of the
	old name, the .bat files of an old ZIP) and MoveEyeSim3D.exe is next to it: start that one with the same arguments
	(plus --renamed) and return true - the caller ends this one at once, before it opens ports or reads any setting"""
	if not OS.has_feature("template"):
		return false
	var exe := real_exe()
	if not exe.get_file().begins_with(OLD_STEM + "."):
		return false
	var nf := exe.get_base_dir().path_join(EXE_STEM + "." + exe.get_extension())
	if not FileAccess.file_exists(nf):
		return false
	if OS.get_name() != "Windows":
		OS.execute("chmod", ["+x", nf])
	var a := OS.get_cmdline_args()
	a.append("--")
	a.append_array(OS.get_cmdline_user_args())
	if not "--renamed" in a:
		a.append("--renamed")
	print("old file name %s: starting %s" % [exe.get_file(), nf.get_file()])
	return OS.create_process(nf, a) > 0


static func remove_old_name_files() -> int:
	"""3D-4.24: removes MotionWatch3D.exe / .old* next to MoveEyeSim3D.exe (only when this one runs under the new name and no
	autostart entry still points to the old file). Fails quietly while one of them still runs; returns how many are left."""
	if not OS.has_feature("template"):
		return 0
	var exe := real_exe()
	if not exe.get_file().begins_with(EXE_STEM + "."):
		return 0
	var left := 0
	var dir := exe.get_base_dir()
	for f in DirAccess.get_files_at(dir):
		if f.begins_with(OLD_STEM + "." + exe.get_extension()):
			if DirAccess.remove_absolute(dir.path_join(f)) != OK:
				left += 1
			else:
				print("removed the old file %s" % f)
	return left


static func real_exe() -> String:
	"""the path of the .exe, also when this one runs as .old / .old2 after an update"""
	var p := OS.get_executable_path()
	var i := p.rfind(".old")
	return p.substr(0, i) if i > 0 and p.substr(i + 4).is_valid_int() or p.ends_with(".old") else p


func _download_check(u: String, zip_path: String) -> String:
	"""download the ZIP and check size and SHA-256: "" = good, else what went wrong ("!" = do not try again)"""
	if FileAccess.file_exists(zip_path):
		DirAccess.remove_absolute(zip_path)
	var got_it := false
	if OS.get_name() == "Windows":                  # curl.exe of Windows: fast, Windows certificates and proxy
		got_it = await _curl(u, zip_path)
	if not got_it:
		http.timeout = 0.0
		http.download_file = zip_path
		http.download_chunk_size = 1 << 20          # bigger pieces: much faster while the simulation runs
		http.body_size_limit = int(info["size"]) + 4096
		if http.request(u) != OK:
			return "!Download liess sich nicht starten."
		downloading = true
		var r: Array = await http.request_completed
		downloading = false
		if r[0] != HTTPRequest.RESULT_SUCCESS or r[1] != 200:
			return "Download abgebrochen (Fehler %s / %s)." % [r[0], r[1]]
	text.text = "Prüfe die Datei …"
	await get_tree().process_frame
	var f := FileAccess.open(zip_path, FileAccess.READ)
	if f == null or f.get_length() != int(info["size"]):
		if f != null:
			f.close()
		return "Die Datei hat die falsche Grösse."
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	f.close()
	if h.finish().hex_encode() != str(info["sha256"]).to_lower():
		DirAccess.remove_absolute(zip_path)
		return "Die Prüfsumme stimmt nicht – die Datei wurde nicht benutzt."
	return ""
