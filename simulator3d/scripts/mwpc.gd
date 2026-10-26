extends Node
## «Motion Watch auf diesem PC» (from 3D-1.9): runs the real Motion Watch next to the simulator, without a Raspberry Pi, so that
## the phone / tablet simulator has a web page to show. Everything is fetched by itself the first time:
##   1. Python for Windows (python-build-standalone from GitHub, ~38 MB, checked with SHA-256), unpacked with tar.exe of Windows
##   2. the packages Motion Watch needs (pip from PyPI: opencv, numpy, flask, pillow, cryptography; a few minutes)
##   3. the newest Motion Watch from GitHub (versions.json, checked with its SHA-256)
## Then Motion Watch is started invisibly: own settings folder, simulation switched on, web page only on this PC (127.0.0.1).
## Everything lives in the user folder of the simulator (%APPDATA%\Godot\app_userdata\Motion Watch 3D Simulator\motionwatch_pc).
## On Linux (test computer) the Python of the system is used instead (option --mw-python).

signal changed

const PY_URL := "https://github.com/astral-sh/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-pc-windows-msvc-install_only.tar.gz"
const PY_SIZE := 38116958
const PY_SHA := "f05531bff16fa77b53be0776587b97b466070e768e6d5920894de988bdcd547a"
const PKGS := ["opencv-python-headless", "numpy", "flask", "pillow", "cryptography"]
const MW_BASE := "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/"
const WEB_PORT := 5000

var main
var state := "off"            # off | busy | running | error
var text := "Aus"
var pid := -1
var dir := ""
var base := MW_BASE
var py_cmd := ""              # Linux: python of the system
var http: HTTPRequest
var dl_total := 0
var dl_what := ""
var test_python := false      # test computer: fetch and unpack the Windows Python anyway (--mw-test-python), then stop


func _ready() -> void:
	dir = ProjectSettings.globalize_path("user://motionwatch_pc")
	http = HTTPRequest.new()
	add_child(http)
	var args := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	for i in range(args.size() - 1):
		if args[i] == "--mw-base":
			base = args[i + 1] if args[i + 1].ends_with("/") else args[i + 1] + "/"
		elif args[i] == "--mw-python":
			py_cmd = args[i + 1]
	test_python = "--mw-test-python" in args
	if OS.get_name() != "Windows" and py_cmd == "":
		py_cmd = "python3"


func url() -> String:
	return "http://127.0.0.1:%d" % WEB_PORT


func busy() -> bool:
	return state == "busy"


func _say(s: String, st := "busy") -> void:
	text = s
	state = st
	print("motion watch on this PC: " + s)
	changed.emit()


func _process(_dt: float) -> void:
	if dl_total > 0 and http.get_http_client_status() == HTTPClient.STATUS_BODY:
		text = "%s … %.1f von %.1f MB" % [dl_what, http.get_downloaded_bytes() / 1048576.0, dl_total / 1048576.0]
		changed.emit()
	if state == "running" and pid > 0 and not OS.is_process_running(pid):
		pid = -1
		_say("Motion Watch hat sich beendet. Protokoll: " + dir.path_join("config/motionwatch.log"), "error")


func _exit_tree() -> void:
	stop()


func stop() -> void:
	if pid > 0:
		OS.kill(pid)
	pid = -1
	if state != "busy":
		_say("Aus", "off")


func toggle() -> void:
	if state == "running":
		stop()
	elif state != "busy":
		start()


# ---- start: fetch what is missing, then run Motion Watch ----------------------------------------------------------------
func start() -> void:
	if busy():
		return
	_say("Bereite vor …")
	if await _web_up():                             # still running from before (e.g. after a crash of the simulator)
		if not main.stream_on:
			main.set_stream(true)
		_say("Läuft auf diesem PC (%s)" % url(), "running")
		return
	DirAccess.make_dir_recursive_absolute(dir.path_join("config"))
	DirAccess.make_dir_recursive_absolute(dir.path_join("mw"))
	var py := await _python()
	if py == "":
		return
	if test_python:
		_say("Python-Test ok: " + py, "off")
		return
	if not await _packages(py):
		return
	var mw := await _motion_watch()
	if mw == "":
		return
	await _settings(py)
	if not main.stream_on:
		main.set_stream(true)                     # Motion Watch gets its cameras and sensors from the simulator
	_say("Starte Motion Watch …")
	var args := [mw, "--headless", "--config", dir.path_join("config"), "--port", str(WEB_PORT), "--bind", "127.0.0.1"]
	pid = OS.create_process(py, args, false)
	if pid <= 0:
		_say("Motion Watch liess sich nicht starten.", "error")
		return
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 300000:
		await get_tree().create_timer(1.5).timeout
		if pid <= 0 or not OS.is_process_running(pid):
			pid = -1
			_say("Motion Watch hat sich gleich wieder beendet. Protokoll: " + dir.path_join("config/motionwatch.log"), "error")
			return
		if await _web_up():
			_say("Läuft auf diesem PC (%s)" % url(), "running")
			return
		_say("Starte Motion Watch … %d s" % int((Time.get_ticks_msec() - t0) / 1000))
	_say("Die Webseite von Motion Watch antwortet nicht. Protokoll: " + dir.path_join("config/motionwatch.log"), "error")


func _web_up() -> bool:
	var h := HTTPRequest.new()
	h.timeout = 6.0
	add_child(h)
	var ok := false
	if h.request(url() + "/", [], HTTPClient.METHOD_HEAD) == OK:        # only ask (the page itself is big)
		var r: Array = await h.request_completed
		ok = r[0] == HTTPRequest.RESULT_SUCCESS and int(r[1]) > 0 and int(r[1]) < 500
	h.queue_free()
	return ok


func _fetch(u: String, to_file := "", size := 0, what := "") -> Array:
	"""[ok, http code, body] - with to_file the body goes into that file"""
	http.download_file = to_file
	http.timeout = 0.0 if to_file != "" else 15.0
	http.body_size_limit = size + 4096 if size > 0 else -1
	dl_total = size
	dl_what = what
	if http.request(u) != OK:
		dl_total = 0
		return [false, 0, PackedByteArray()]
	var r: Array = await http.request_completed
	dl_total = 0
	return [r[0] == HTTPRequest.RESULT_SUCCESS and int(r[1]) == 200, int(r[1]), r[3], int(r[0])]


const RESULTS := ["ok", "Grösse stimmt nicht", "keine Verbindung", "Name nicht gefunden (DNS)", "Verbindung abgebrochen",
		"TLS / Zertifikat", "keine Antwort", "Datei zu gross", "Entpacken", "Anfrage ging nicht", "Datei lässt sich nicht anlegen",
		"Datei lässt sich nicht schreiben", "zu viele Weiterleitungen", "Zeitüberschreitung"]


func _why(r: Array) -> String:
	"""an understandable reason for a failed _fetch"""
	if int(r[1]) > 0:
		return "HTTP %d" % int(r[1])
	var k: int = int(r[3]) if r.size() > 3 else -1
	return RESULTS[k] if k >= 0 and k < RESULTS.size() else "Fehler %d" % k


func _download(u: String, to: String, size: int, what: String) -> String:
	"""a big download into a file: on Windows with curl.exe (part of Windows 10 / 11: Windows certificates and proxy, follows
	redirects), otherwise / as a second try with Godot. Returns "" or why it did not work."""
	var why := ""
	if OS.get_name() == "Windows" or test_python:
		var th := Thread.new()
		th.start(func():
			var out := []
			var code := OS.execute("curl.exe" if OS.get_name() == "Windows" else "curl", ["-L", "--fail", "-s", "-S", "--retry", "2", "-o", to, u], out, true, false)
			return [code, "\n".join(out)])
		var t0 := Time.get_ticks_msec()
		while th.is_alive():
			await get_tree().create_timer(0.5).timeout
			var got := 0
			var f := FileAccess.open(to, FileAccess.READ)
			if f != null:
				got = f.get_length()
				f.close()
			if got > 0 and size > 0:
				text = "%s … %.1f von %.1f MB" % [what, got / 1048576.0, size / 1048576.0]
			elif got > 0:
				text = "%s … %.1f MB" % [what, got / 1048576.0]
			else:
				text = "%s … %d s" % [what, int((Time.get_ticks_msec() - t0) / 1000)]
			changed.emit()
		var c: Array = th.wait_to_finish()
		if int(c[0]) == 0 and FileAccess.file_exists(to):
			return ""
		why = "curl: " + (str(c[1]).strip_edges().left(160) if str(c[1]).strip_edges() != "" else "Fehler %d" % int(c[0]))
		print("motion watch on this PC: " + why)
	var r: Array = await _fetch(u, to, size, what)
	if r[0]:
		return ""
	return (why + " · " if why != "" else "") + "Godot: " + _why(r)


func _sha256_file(p: String) -> String:
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return ""
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	return h.finish().hex_encode()


func _run(cmd: String, args: Array) -> Array:
	"""run a program in a thread (the window keeps going): [exit code, output]"""
	var th := Thread.new()
	th.start(func():
		var out := []
		var code := OS.execute(cmd, args, out, true, false)
		return [code, "\n".join(out)])
	var t0 := Time.get_ticks_msec()
	var base_text := text
	while th.is_alive():
		await get_tree().create_timer(0.5).timeout
		text = "%s (%d s)" % [base_text, int((Time.get_ticks_msec() - t0) / 1000)]
		changed.emit()
	return th.wait_to_finish()


func _python() -> String:
	"""1. Python: on Windows our own copy (fetched once), on Linux the one of the system"""
	if py_cmd != "" and not test_python:
		return py_cmd
	var exe := dir.path_join("python/python.exe")
	if FileAccess.file_exists(exe):
		return exe
	var tgz := dir.path_join("python.tar.gz")
	var why := await _download(PY_URL, tgz, PY_SIZE, "Lade Python (nur beim ersten Mal)")
	if why != "":
		DirAccess.remove_absolute(tgz)
		_say("Python liess sich nicht herunterladen (%s). Internet da?" % why, "error")
		return ""
	_say("Prüfe Python …")
	if _sha256_file(tgz) != PY_SHA:
		DirAccess.remove_absolute(tgz)
		_say("Python-Download beschädigt (Prüfsumme falsch).", "error")
		return ""
	_say("Packe Python aus …")
	var x: Array = await _run("tar", ["-xzf", tgz, "-C", dir])
	DirAccess.remove_absolute(tgz)
	if not FileAccess.file_exists(exe):
		_say("Python liess sich nicht auspacken: " + str(x[1]).left(200), "error")
		return ""
	return exe


func _packages(py: String) -> bool:
	"""2. the packages for Motion Watch (once; a file remembers it)"""
	var mark := dir.path_join("pakete_ok.txt")
	var want := " ".join(PKGS)
	if FileAccess.file_exists(mark) and FileAccess.get_file_as_string(mark).strip_edges() == want:
		return true
	if py_cmd != "":                                # Linux test computer: the packages are already there
		var c: Array = await _run(py, ["-c", "import cv2, numpy, flask, PIL"])
		if int(c[0]) != 0:
			_say("Für Motion Watch fehlen Python-Pakete: " + want, "error")
			return false
		return true
	_say("Installiere die Pakete für Motion Watch (nur beim ersten Mal, ein paar Minuten)")
	var args := ["-m", "pip", "install", "--disable-pip-version-check", "--no-warn-script-location"]
	args.append_array(PKGS)
	var r: Array = await _run(py, args)
	if int(r[0]) != 0:
		var out: String = str(r[1])
		_say("Die Pakete liessen sich nicht installieren: " + out.right(300), "error")
		return false
	var f := FileAccess.open(mark, FileAccess.WRITE)
	if f != null:
		f.store_string(want)
	return true


func _motion_watch() -> String:
	"""3. the newest Motion Watch (from versions.json on GitHub); without internet the one fetched before"""
	_say("Suche die neuste Motion-Watch-Version …")
	var have := ""
	for f in DirAccess.get_files_at(dir.path_join("mw")):
		if f.begins_with("webcam_bewegung_") and f.ends_with(".py"):
			have = dir.path_join("mw").path_join(f)
	var r: Array = await _fetch(base + "versions.json")
	var d = JSON.parse_string((r[2] as PackedByteArray).get_string_from_utf8()) if r[0] else null
	if typeof(d) != TYPE_DICTIONARY or (d.get("versions", []) as Array).is_empty():
		if have != "":
			return have
		_say("Motion Watch liess sich nicht finden (GitHub nicht erreichbar: %s)." % _why(r), "error")
		return ""
	var e: Dictionary = d["versions"][0]
	var file := str(e.get("file", ""))
	if not file.begins_with("webcam_bewegung_") or not file.ends_with(".py") or "/" in file or "\\" in file:
		_say("Unerwartete Datei in versions.json: " + file, "error")
		return ""
	var target := dir.path_join("mw").path_join(file)
	if FileAccess.file_exists(target) and _sha256_file(target) == str(e.get("sha256", "")):
		return target
	var why := await _download(base + file, target + ".part", 0, "Lade Motion Watch %s" % str(e.get("version", "")))
	if why != "":
		DirAccess.remove_absolute(target + ".part")
		if have != "":
			return have
		_say("Motion Watch liess sich nicht herunterladen (%s)." % why, "error")
		return ""
	if _sha256_file(target + ".part") != str(e.get("sha256", "")):
		DirAccess.remove_absolute(target + ".part")
		_say("Motion-Watch-Download beschädigt (Prüfsumme falsch).", "error")
		return ""
	if FileAccess.file_exists(target):
		DirAccess.remove_absolute(target)
	DirAccess.rename_absolute(target + ".part", target)
	for f in DirAccess.get_files_at(dir.path_join("mw")):           # older versions away
		if f != file and f.begins_with("webcam_bewegung_"):
			DirAccess.remove_absolute(dir.path_join("mw").path_join(f))
	return target


func _settings(py: String) -> void:
	"""Motion Watch on this PC: simulation on, the simulator on this PC, the cameras from the simulator (what the switch «Simulation»
	of Motion Watch also sets). Python writes it (keeps whole numbers whole)."""
	var code := "import json,os,sys;p=sys.argv[1];d=json.load(open(p,encoding='utf-8')) if os.path.exists(p) else {};c=d.setdefault('cfg',{});c['sim_on']=True;c['sim_url']=sys.argv[2];c['sim_auto']=False;c['source']='sim:0';c['thermal_source']='sim:thermal';c.setdefault('sim_prev_source','auto');x=[e for e in c.get('extra_cams',[]) if not str(e).startswith('sim:')];c['extra_cams']=x+['sim:1'];json.dump(d,open(p,'w',encoding='utf-8'),indent=1,ensure_ascii=False)"
	var r: Array = await _run(py, ["-c", code, dir.path_join("config/motionwatch_settings.json"), "http://127.0.0.1:%d" % main.stream_port])
	if int(r[0]) != 0:
		print("motion watch on this PC: settings not written: " + str(r[1]))
