extends PanelContainer
## Prüfstand auf diesem PC (3D-3.49): misst die Erkennung von MoveEye mit den festen Testläufen (testrun.gd), hier auf
## einem echten PC mit Grafikkarte – realistische Bildraten statt der 1–3 Bilder/s ohne Grafikkarte. Von Hand ausgelöst:
##   1. MoveEye wählen: das gerade verbundene (Pi oder PC) – oder eine Datei webcam_bewegung_X.py einlesen, die dann als
##      «MoveEye auf diesem PC» startet
##   2. Testläufe und Wiederholungen wählen, starten
##   3. am Schluss erscheint das Ergebnis; «Senden» legt es ins GitHub-Repository (pruefstand/ergebnisse/, mit einem
##      GitHub-Schlüssel) oder auf den Schreibtisch.
## Das Ergebnis hat dasselbe Format wie pruefstand/pruefstand.py im Repository (VERLAUF.md liest beide).
## Prüfstand 2: die Hauptzahl sind die echten Pushes (richtig / falsch); «Schleichwege an GitHub senden» legt die unerkannten
## Wege der Spielrunden nach simulator3d/spielwege/ (doppelte nur einmal); «Alarm-Rückblick als Prüfstand-Fall» speichert die
## zuletzt abgespielte Alarm-Spur als echte Nacht (simulator3d/pruefnaechte/), die der Prüfstand mit anderem Wetter nachspielt.

const UI = preload("res://scripts/ui_style.gd")
const TR := preload("res://scripts/testrun.gd")         # 3D-3.90: names and times of the plans only there
const PLANS := [["quick", "", true], ["night", "", true], ["standard", "", true], ["nacht", "", false], ["hard", "", false]]
const PLAN_DAUER := TR.DAUER
const REPO_API := "https://api.github.com/repos/DonElektro/MotionWatch/contents/pruefstand/ergebnisse/"
const REPO_FILES := "https://api.github.com/repos/DonElektro/MotionWatch/contents/"
const WAYS_SENT := "user://pruefstand/wege_gesendet.json"

var main
var file_lbl: Label
var src_seg: OptionButton
var plan_cbs := {}
var reps: SpinBox
var info: Label
var start_b: Button
var stop_b: Button
var token_le: LineEdit
var result_box: VBoxContainer
var result_lbl: Label
var send_b: Button
var send_lbl: Label
var setup_box: VBoxContainer
var mw_file := ""
var running := false
var queue: Array = []
var done: Array = []
var current := ""
var t_run := 0.0
var t_all := 0.0
var result := {}
var result_path := ""
var _wait_mw := 0.0
var http: HTTPRequest
var extra_lbl: Label
# 3D-3.75: automatically after every update of MoveEye: when the connected MoveEye has a new version and nobody
# uses the simulator (no click for 3 minutes, no game, no test run), the short test runs once; the result is sent when a
# GitHub key is there, else it stays in the folder (and on the list of results here).
var auto_cb: CheckBox
var auto := false
var auto_run := false
var _touch_t := 0.0
var _ver_t := 0.0
var _ver_seen := ""
const AUTO_FILE := "user://pruefstand/auto.json"


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.98), UI.LINE, 14, 14, 1))
	anchor_right = 1.0
	anchor_bottom = 1.0
	offset_left = 16
	offset_top = 16
	offset_right = -410
	offset_bottom = -16
	http = HTTPRequest.new()
	add_child(http)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 10)
	sc.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := UI.heading("Prüfstand: Erkennung messen")
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := Button.new()
	x.text = "Schliessen"
	x.pressed.connect(func(): open(false))
	hd.add_child(x)
	var lead := UI.small("Feste Testläufe: immer dieselben Besucher auf denselben Wegen. Der Simulator weiss, wer für die Kopfkamera gut sichtbar war, und vergleicht das mit den Meldungen von MoveEye. Auf diesem PC (mit Grafikkarte) sind die Zahlen realistischer als auf GitHub.")
	lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(lead)
	setup_box = VBoxContainer.new()
	setup_box.add_theme_constant_override("separation", 8)
	v.add_child(setup_box)
	setup_box.add_child(UI.small("1. Welches MoveEye wird gemessen?", UI.TXT))
	src_seg = OptionButton.new()
	src_seg.add_item("Das gerade verbundene (Pi oder MoveEye auf diesem PC)", 0)
	src_seg.add_item("Eine Datei einlesen und hier auf diesem PC starten", 1)
	src_seg.item_selected.connect(func(_i): _paint())
	setup_box.add_child(src_seg)
	var fr := HBoxContainer.new()
	setup_box.add_child(fr)
	var fb := Button.new()
	fb.text = "Datei wählen … (webcam_bewegung_X.py)"
	fb.pressed.connect(_pick_file)
	fr.add_child(fb)
	file_lbl = UI.small("keine Datei gewählt")
	file_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	file_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fr.add_child(file_lbl)
	var warn := UI.small("Während der Messung darf nur EIN MoveEye mit diesem Simulator verbunden sein (z. B. beim Pi die Simulation ausschalten, wenn eine Datei hier gemessen wird).")
	warn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	setup_box.add_child(warn)
	setup_box.add_child(UI.small("2. Welche Testläufe?", UI.TXT))
	for p in PLANS:
		var cb := CheckBox.new()
		cb.text = str(TR.PLANS[p[0]]["name"])
		cb.button_pressed = p[2]
		setup_box.add_child(cb)
		plan_cbs[p[0]] = cb
	var rr := HBoxContainer.new()
	setup_box.add_child(rr)
	var rl := UI.small("Jeden Testlauf so oft:", UI.TXT)
	rl.autowrap_mode = TextServer.AUTOWRAP_OFF
	rr.add_child(rl)
	reps = SpinBox.new()
	reps.min_value = 1
	reps.max_value = 5
	reps.value = 2
	rr.add_child(reps)
	var tk := HBoxContainer.new()
	setup_box.add_child(tk)
	var tl := UI.small("GitHub-Schlüssel (nur für «Senden»):", UI.TXT)
	tl.autowrap_mode = TextServer.AUTOWRAP_OFF
	tk.add_child(tl)
	token_le = LineEdit.new()
	token_le.secret = true
	token_le.placeholder_text = "github_pat_… (leer = Datei auf den Schreibtisch)"
	token_le.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	token_le.text = _token()
	token_le.text_changed.connect(func(s): _save_token(s.strip_edges()))
	tk.add_child(token_le)
	auto_cb = CheckBox.new()
	auto_cb.text = "Nach jedem Update von MoveEye automatisch messen (Kurz, 1×, wenn 3 Minuten niemand den Simulator bedient; mit Schlüssel wird das Ergebnis gesendet)"
	auto_cb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	auto = bool(_auto_data().get("on", false))
	auto_cb.button_pressed = auto
	auto_cb.toggled.connect(func(on_): set_auto(on_))
	v.add_child(auto_cb)
	# Prüfstand 2: bench cases from the game and from real alarms
	v.add_child(UI.small("Testfälle für den Prüfstand (auf GitHub mit dem Schlüssel oben, sonst auf den Schreibtisch):", UI.TXT))
	var xr := HBoxContainer.new()
	xr.add_theme_constant_override("separation", 8)
	v.add_child(xr)
	var wb := Button.new()
	wb.text = "Schleichwege an GitHub senden"
	wb.tooltip_text = "Die Wege aus den Spielrunden, auf denen MoveEye niemanden meldete – der Prüfstand geht sie dann bei jeder Version nach."
	wb.pressed.connect(send_ways)
	xr.add_child(wb)
	var cb2 := Button.new()
	cb2.text = "Letzten Alarm-Rückblick als Prüfstand-Fall"
	cb2.tooltip_text = "Die zuletzt abgespielte Alarm-Spur (MoveEye → Alarm-Rückblick in 3D) wird zur «echten Nacht»: der Prüfstand spielt sie nach, auch mit Regen, ohne Licht und am Tag."
	cb2.pressed.connect(save_case)
	xr.add_child(cb2)
	extra_lbl = UI.small("")
	extra_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(extra_lbl)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	v.add_child(row)
	start_b = Button.new()
	start_b.text = "▶ Messung starten"
	UI.primary(start_b)
	start_b.pressed.connect(start)
	row.add_child(start_b)
	stop_b = Button.new()
	stop_b.text = "Abbrechen"
	stop_b.pressed.connect(func(): stop("abgebrochen"))
	row.add_child(stop_b)
	info = UI.small("", UI.TXT)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 15)
	v.add_child(info)
	# the result («pop-up» at the end)
	result_box = VBoxContainer.new()
	result_box.add_theme_constant_override("separation", 8)
	result_box.visible = false
	var rp := PanelContainer.new()
	rp.add_theme_stylebox_override("panel", UI.box(Color(0.10, 0.20, 0.14, 1.0), UI.GRN, 12, 14, 2))
	rp.add_child(result_box)
	v.add_child(rp)
	result_box.add_child(UI.heading("Messung fertig"))
	result_lbl = UI.small("", UI.TXT)
	result_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	result_lbl.add_theme_font_size_override("font_size", 15)
	result_box.add_child(result_lbl)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 8)
	result_box.add_child(r2)
	send_b = Button.new()
	send_b.text = "Ergebnis senden"
	UI.primary(send_b)
	send_b.pressed.connect(send)
	r2.add_child(send_b)
	var ob := Button.new()
	ob.text = "Ordner öffnen"
	ob.pressed.connect(func(): OS.shell_show_in_file_manager(ProjectSettings.globalize_path(result_path)) if result_path != "" else null)
	r2.add_child(ob)
	send_lbl = UI.small("")
	send_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	result_box.add_child(send_lbl)
	_paint()


func _auto_data() -> Dictionary:
	var f := FileAccess.open(AUTO_FILE, FileAccess.READ)
	if f == null:
		return {}
	var d = JSON.parse_string(f.get_as_text())
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _auto_save(d: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute("user://pruefstand")
	var f := FileAccess.open(AUTO_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func set_auto(on_: bool) -> void:
	auto = on_
	var d := _auto_data()
	d["on"] = on_
	_auto_save(d)
	if auto_cb != null and auto_cb.button_pressed != on_:
		auto_cb.set_pressed_no_signal(on_)


func _input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton or ev is InputEventKey or ev is InputEventScreenTouch:
		_touch_t = main.now()


func _auto_tick(now: float) -> void:
	"""a new version of MoveEye is connected: measure once when the simulator is quiet"""
	if not auto or running or now - main.mw_t > 3.0:
		_ver_seen = ""
		return
	var ver := str(main.mw.get("mw_version", ""))
	if ver == "" or ver == str(_auto_data().get("last", "")):
		return
	if ver != _ver_seen:
		_ver_seen = ver
		_ver_t = now                                     # MoveEye just came back after its update: let it settle
		return
	var busy: bool = (main.game != null and main.game.busy()) or main.testrun.running or (main.surprise != null and not main.surprise.cur.is_empty())
	if busy or now - _ver_t < 90.0 or now - _touch_t < 180.0:
		return
	auto_run = true
	start(["quick"], 1)
	var d := _auto_data()
	d["last"] = ver                                      # also when it fails: no endless tries with the same version
	_auto_save(d)


func open(on: bool) -> void:
	visible = on
	if on:
		_paint()


func state() -> Dictionary:
	return {"ok": true, "auto": auto, "auto_run": auto_run, "auto_last": str(_auto_data().get("last", "")), "running": running, "current": current, "left": queue.size(), "done": done.size(), "info": info.text if info else "",
			"result": result, "file": result_path}


func _token() -> String:
	var f := FileAccess.open("user://pruefstand/schluessel.txt", FileAccess.READ)
	return f.get_as_text().strip_edges() if f != null else ""


func _save_token(s: String) -> void:
	DirAccess.make_dir_recursive_absolute("user://pruefstand")
	var f := FileAccess.open("user://pruefstand/schluessel.txt", FileAccess.WRITE)
	if f != null:
		f.store_string(s)


func _pick_file() -> void:
	var d := FileDialog.new()
	d.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	d.access = FileDialog.ACCESS_FILESYSTEM
	d.use_native_dialog = true
	d.filters = PackedStringArray(["webcam_bewegung_*.py ; MoveEye", "*.py ; Python"])
	d.title = "MoveEye für den Prüfstand wählen"
	d.file_selected.connect(func(p):
		mw_file = p
		src_seg.select(1)
		_paint()
		d.queue_free())
	d.canceled.connect(func(): d.queue_free())
	add_child(d)
	d.popup_centered(Vector2i(900, 600))


func _paint() -> void:
	if file_lbl == null:
		return
	file_lbl.text = mw_file.get_file() if mw_file != "" else "keine Datei gewählt"
	start_b.disabled = running
	stop_b.disabled = not running
	setup_box.modulate.a = 0.5 if running else 1.0
	if not running and info.text == "":
		var con: bool = main.now() - main.mw_t < 3.0
		info.text = ("Verbunden: %s" % str(main.mw.get("device", "MoveEye"))) if con else "Noch kein MoveEye verbunden."


func start(plans_: Array = [], reps_ := 0) -> void:
	if running:
		return
	queue = []
	if not plans_.is_empty():                            # 3D-3.75: the automatic run (the connected MoveEye)
		for p_ in plans_:
			for i in range(max(1, reps_)):
				queue.append(p_)
	else:
		auto_run = false
	for p in PLANS:
		if plans_.is_empty() and (plan_cbs[p[0]] as CheckBox).button_pressed:
			for i in int(reps.value):
				queue.append(p[0])
	if queue.is_empty():
		info.text = "Bitte mindestens einen Testlauf wählen."
		return
	if src_seg.selected == 1 and not auto_run:
		if mw_file == "" or not FileAccess.file_exists(mw_file):
			info.text = "Bitte zuerst die Datei wählen (webcam_bewegung_X.py)."
			return
		# MoveEye on this PC with exactly this file (stopped first if it runs with another one)
		main.mwpc.override_file = mw_file
		if main.mwpc.state == "running":
			main.mwpc.stop()
		main.mwpc.start()
	done = []
	result = {}
	result_box.visible = false
	running = true
	t_all = main.now()
	_wait_mw = main.now()
	current = ""
	info.text = "Warte auf MoveEye …"
	_paint()


func stop(why := "") -> void:
	if not running:
		return
	running = false
	auto_run = false
	if main.testrun.running:
		main.testrun.stop(false)
	current = ""
	info.text = "Messung " + why + "."
	_paint()


func _process(_dt: float) -> void:
	if not running:
		if main != null:
			_auto_tick(main.now())
		return
	var now: float = main.now()
	var con: bool = now - main.mw_t < 3.0
	var file_mode: bool = src_seg.selected == 1 and not auto_run
	if current == "":
		if not con:                                       # MoveEye not (yet) connected
			var waited := now - _wait_mw
			info.text = "Warte auf MoveEye … %d s%s" % [int(waited), (" · " + main.mwpc.text) if file_mode else ""]
			if waited > (900.0 if file_mode else 120.0):   # the first start on this PC loads Python (minutes)
				stop("abgebrochen: MoveEye hat sich nicht verbunden")
			return
		if queue.is_empty():
			_finish()
			return
		if now - _wait_mw < 20.0 and done.is_empty():
			info.text = "MoveEye verbunden – %d s eingewöhnen …" % int(20.0 - (now - _wait_mw))
			return
		current = queue.pop_front()
		var err: String = main.testrun.start(current, [0])
		if err != "":
			info.text = "Testlauf startet nicht: " + err
			queue.push_front(current)
			current = ""
			_wait_mw = now
			return
		t_run = now
		return
	if main.testrun.running:
		var left: float = 0.0
		for q in queue:
			left += PLAN_DAUER.get(q, 300)
		left += max(0.0, PLAN_DAUER.get(current, 300) - (now - t_run))
		info.text = "Läuft: %s (Lauf %d von %d) · %s · noch etwa %d Min." % [_name(current), done.size() + 1, done.size() + queue.size() + 1,
				main.testrun.info.get_slice("–", 1).strip_edges() if "–" in main.testrun.info else main.testrun.info, int(ceil(left / 60.0))]
		return
	var rep: Dictionary = main.testrun.report
	if rep.get("plan", "") == current and rep.has("phases"):
		var r := rep.duplicate(true)
		r["dauer_s"] = int(now - t_run)
		done.append(r)
	else:
		info.text = "Testlauf %s ohne Bericht: %s" % [_name(current), main.testrun.info]
	current = ""


func _name(p: String) -> String:
	if TR.PLANS.has(p):
		return str(TR.PLANS[p]["name"]).get_slice(" (", 0)
	return p


func _finish() -> void:
	running = false
	var plans := {}
	for r in done:
		if not plans.has(r["plan"]):
			plans[r["plan"]] = []
		plans[r["plan"]].append(r)
	var dt := Time.get_datetime_dict_from_system()
	var stamp := "%04d-%02d-%02d %02d:%02d" % [dt.year, dt.month, dt.day, dt.hour, dt.minute]
	var gpu := RenderingServer.get_video_adapter_name()
	result = {"datum": stamp, "mw_version": str(main.mw.get("mw_version", "?")), "sim_version": main.VERSION,
			"ki": str(main.mw.get("ai_status", "?")), "rechner": "PC %s (%s)" % [main.host_name(), gpu],
			"qualitaet": main.quality, "szene": main.scene, "kameras": "Kopfkamera", "quelle": "Simulator-Prüfstand",
			"motion_watch": "Datei " + mw_file.get_file() if src_seg.selected == 1 and not auto_run else str(main.mw.get("device", "verbunden")),
			"automatisch": auto_run,
			"plaene": plans}
	DirAccess.make_dir_recursive_absolute("user://pruefstand")
	var fn := "%04d-%02d-%02d_%02d%02d_%s.json" % [dt.year, dt.month, dt.day, dt.hour, dt.minute, str(result["mw_version"]).replace("?", "unbekannt")]
	result_path = "user://pruefstand/" + fn
	var f := FileAccess.open(result_path, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(result, " "))
		f.close()
	# the numbers
	var lines := []
	var tp := 0
	var td := 0
	var fa := 0
	var pok := 0
	var pfa := 0
	for p in plans:
		var P := 0
		var D := 0
		var F := 0
		var PO := 0
		var PF := 0
		for r in plans[p]:
			P += int(r.get("persons", 0))
			D += int(r.get("persons_detected", 0))
			F += int(r.get("flicker", r.get("false_alarms", 0)))
			PO += int(r.get("pushes", {}).get("ok", 0))
			PF += int(r.get("pushes", {}).get("false", 0))
		tp += P
		td += D
		fa += F
		pok += PO
		pfa += PF
		lines.append("%s ×%d: Pushes richtig %d / falsch %d · Personen %d von %d erkannt (%d %%) · Flackern %d" % [_name(p), (plans[p] as Array).size(), PO, PF, D, P, int(round(100.0 * D / max(1, P))), F])
	result_lbl.text = "MoveEye %s · %s\n\nInsgesamt: Pushes richtig %d / falsch %d · Personen %d von %d erkannt (%d %%) · Flackern %d · Dauer %d Min.\n\n%s" % [
			result["mw_version"], result["rechner"], pok, pfa, td, tp, int(round(100.0 * td / max(1, tp))), fa, int((main.now() - t_all) / 60.0), "\n".join(PackedStringArray(lines))]
	result_box.visible = true
	send_lbl.text = "Gespeichert: " + ProjectSettings.globalize_path(result_path)
	info.text = "Fertig." + (" (automatisch nach dem Update von MoveEye)" if auto_run else "")
	main.start_info = "Prüfstand fertig: MoveEye %s – Pushes richtig %d / falsch %d, Personen %d von %d" % [result["mw_version"], pok, pfa, td, tp]
	if auto_run:
		if token_le.text.strip_edges() != "":
			send()                                       # with a key: straight to GitHub
		else:
			send_lbl.text = "Gespeichert: " + ProjectSettings.globalize_path(result_path) + " – «Ergebnis senden» legt es auf den Schreibtisch."
	else:
		visible = true
		DisplayServer.window_request_attention()
	auto_run = false
	_paint()


func send() -> void:
	if result_path == "":
		return
	var body_txt := FileAccess.get_file_as_string(result_path)
	var tok := token_le.text.strip_edges()
	if tok == "":
		# no key: on the desktop, the folder opens - attach the file in the chat
		var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
		if desk == "" or not DirAccess.dir_exists_absolute(desk):
			desk = OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)
		if desk == "" or not DirAccess.dir_exists_absolute(desk):
			desk = ProjectSettings.globalize_path("user://pruefstand")
		var to := desk.path_join("Pruefstand_" + result_path.get_file())
		var f := FileAccess.open(to, FileAccess.WRITE)
		if f != null:
			f.store_string(body_txt)
			f.close()
			OS.shell_show_in_file_manager(to)
			send_lbl.text = "Auf den Schreibtisch gelegt: %s – diese Datei im Chat anhängen." % to.get_file()
		else:
			send_lbl.text = "Konnte nicht auf den Schreibtisch schreiben – «Ordner öffnen» und die Datei im Chat anhängen."
		return
	send_b.disabled = true
	send_lbl.text = "Sende an GitHub …"
	var data := JSON.stringify({"message": "Prüfstand (PC): Ergebnis %s" % result.get("mw_version", "?"),
			"content": Marshalls.utf8_to_base64(body_txt)})
	var headers := ["Authorization: Bearer " + tok, "Accept: application/vnd.github+json", "User-Agent: MotionWatch3D", "Content-Type: application/json"]
	var err := http.request(REPO_API + result_path.get_file(), headers, HTTPClient.METHOD_PUT, data)
	if err != OK:
		send_b.disabled = false
		send_lbl.text = "Senden ging nicht (%d)." % err
		return
	var r: Array = await http.request_completed
	send_b.disabled = false
	var code: int = r[1]
	if code == 201 or code == 200:
		send_lbl.text = "✅ Gesendet: pruefstand/ergebnisse/%s – die Tabelle VERLAUF.md wird auf GitHub nachgeführt." % result_path.get_file()
	elif code == 401 or code == 403:
		send_lbl.text = "GitHub lehnt den Schlüssel ab (%d) – Schlüssel prüfen (Rechte: Contents lesen und schreiben, nur dieses Repository)." % code
	elif code == 422:
		send_lbl.text = "Diese Datei ist schon auf GitHub."
	else:
		send_lbl.text = "Senden ging nicht (Antwort %d) – «Ordner öffnen» und die Datei im Chat anhängen." % code


# ---- Prüfstand 2: sneaking ways and real nights as bench cases -------------------------------------------------------
func _desk_dir() -> String:
	var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
	if desk == "" or not DirAccess.dir_exists_absolute(desk):
		desk = OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)
	if desk == "" or not DirAccess.dir_exists_absolute(desk):
		desk = ProjectSettings.globalize_path("user://pruefstand")
	return desk.path_join("MoveEye_Pruefstand")


func _put(repo_path: String, text: String, msg: String) -> int:
	"""one file into the repository (GitHub key of the test bench): 201 new, 422 already there, else the error"""
	var data := JSON.stringify({"message": msg, "content": Marshalls.utf8_to_base64(text)})
	var headers := ["Authorization: Bearer " + token_le.text.strip_edges(), "Accept: application/vnd.github+json", "User-Agent: MotionWatch3D", "Content-Type: application/json"]
	if http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		http.cancel_request()
	if http.request(REPO_FILES + repo_path, headers, HTTPClient.METHOD_PUT, data) != OK:
		return -1
	var r: Array = await http.request_completed
	return int(r[1])


func _sent_keys() -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(WAYS_SENT)) if FileAccess.file_exists(WAYS_SENT) else null
	return d if typeof(d) == TYPE_DICTIONARY else {}


func send_ways() -> void:
	"""the unseen ways of the own game rounds (user://spiel/) → simulator3d/spielwege/schleichweg_<key>.json - the same way
	only once (the key is made from the points); without a key: into a folder on the desktop (attach it in the chat)"""
	var sent := _sent_keys()
	var todo: Array = []
	for w in preload("res://scripts/gamelearn.gd").load_ways():
		if str(w.get("file", "")).begins_with("user://") and not sent.has(str(w["key"])):
			todo.append(w)
	if todo.is_empty():
		extra_lbl.text = "Keine neuen Schleichwege (alle schon gesendet – oder noch keine Spielrunde, in der jemand unerkannt ins Ziel kam)."
		return
	var tok := token_le.text.strip_edges()
	var n_new := 0
	var n_old := 0
	var n_err := 0
	for w in todo:
		var ww: Dictionary = w.duplicate(true)
		ww.erase("file")
		var fn := "schleichweg_%s.json" % str(w["key"])
		var txt := JSON.stringify(ww)
		if tok == "":
			DirAccess.make_dir_recursive_absolute(_desk_dir())
			var f := FileAccess.open(_desk_dir().path_join(fn), FileAccess.WRITE)
			if f != null:
				f.store_string(txt)
				f.close()
				n_new += 1
			continue
		extra_lbl.text = "Sende Schleichweg %d von %d …" % [n_new + n_old + n_err + 1, todo.size()]
		var code: int = await _put("simulator3d/spielwege/" + fn, txt, "Prüfstand: Schleichweg aus dem Spiel (%s)" % str(w.get("scene", "?")))
		if code in [200, 201]:
			n_new += 1
		elif code == 422:
			n_old += 1                                       # already on GitHub (somebody sent the same way)
		else:
			n_err += 1
			continue
		sent[str(w["key"])] = true
	if tok == "":
		OS.shell_show_in_file_manager(_desk_dir())
		extra_lbl.text = "%d Schleichwege in den Ordner %s gelegt – die Dateien im Chat anhängen." % [n_new, _desk_dir()]
		return
	DirAccess.make_dir_recursive_absolute("user://pruefstand")
	var fs := FileAccess.open(WAYS_SENT, FileAccess.WRITE)
	if fs != null:
		fs.store_string(JSON.stringify(sent))
	extra_lbl.text = "Schleichwege: %d neu auf GitHub, %d waren schon da%s. Der Prüfstand geht sie ab der nächsten Messung nach." % [n_new, n_old,
			(", %d gingen nicht (Schlüssel prüfen)" % n_err) if n_err > 0 else ""]


func save_case() -> void:
	"""the last «Alarm-Rückblick in 3D» → a real night for the test bench (format: testrun.gd load_cases / pruefstand/LIESMICH.md)"""
	var tr_: Dictionary = main.replay.last_track if main.replay != null else {}
	if tr_.is_empty() or tr_.get("samples", []).size() < 3:
		extra_lbl.text = "Noch kein Alarm-Rückblick – zuerst in MoveEye bei einem Alarm «Rückblick in 3D» abspielen."
		return
	var smp: Array = tr_["samples"]
	var cs: Array = []
	for x in smp:                                        # only what the format needs (no internal fields of replay.gd)
		cs.append({"t": x.get("t", 0.0), "pan": x.get("pan", 0.0), "tilt": x.get("tilt", 0.0), "objs": x.get("objs", [])})
	var t_: float = float(smp[0].get("t", 0.0))
	var bias: int = int(Time.get_time_zone_from_system().get("bias", 0)) * 60
	var dt := Time.get_datetime_dict_from_unix_time(int(t_) + bias) if t_ > 1.0e9 else Time.get_datetime_dict_from_system()
	var c := {"v": 1, "title": str(tr_.get("title", "Alarm")), "date": "%04d-%02d-%02d %02d:%02d" % [dt.year, dt.month, dt.day, dt.hour, dt.minute],
			"hour": snappedf(dt.hour + dt.minute / 60.0, 0.1), "weather": str(main.weather), "wind": snappedf(float(main.wind), 1.0),
			"quelle": "Alarm-Rückblick (MoveEye %s)" % str(main.mw.get("mw_version", "?")), "samples": cs}
	var fn := "nacht_%04d%02d%02d_%02d%02d.json" % [dt.year, dt.month, dt.day, dt.hour, dt.minute]
	DirAccess.make_dir_recursive_absolute("user://pruefstand/faelle")
	var txt := JSON.stringify(c)
	var f := FileAccess.open("user://pruefstand/faelle/" + fn, FileAccess.WRITE)
	if f != null:
		f.store_string(txt)
		f.close()
	if token_le.text.strip_edges() == "":
		extra_lbl.text = "Gespeichert als Prüfstand-Fall (läuft hier im Testlauf «Echte Nächte» mit): %s – für GitHub den Schlüssel oben eintragen und nochmals drücken." % fn
		return
	extra_lbl.text = "Sende den Fall an GitHub …"
	var code: int = await _put("simulator3d/pruefnaechte/" + fn, txt, "Prüfstand: echte Nacht %s" % c["date"])
	extra_lbl.text = ("✅ Prüfstand-Fall gesendet: simulator3d/pruefnaechte/%s" % fn) if code in [200, 201] else (
			"Dieser Fall ist schon auf GitHub." if code == 422 else "Senden ging nicht (%d) – Schlüssel prüfen. Der Fall ist hier gespeichert." % code)
