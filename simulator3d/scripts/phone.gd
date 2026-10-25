extends PanelContainer
## Phone / tablet simulator inside the simulator: the real web page of Motion Watch, as on a phone or a tablet, upright or
## across, full screen or not - and it can be operated with the mouse (touch) and the keyboard.
## How: an invisible Edge / Chrome (on every Windows PC) renders the page with the size of the device; its pictures come
## over the DevTools connection (screencast) and the mouse / keys go back as touches (Chrome DevTools Protocol).

const PORT := 9333
const DEVICES := {"phone": Vector2i(390, 844), "tablet": Vector2i(820, 1180)}
const UA_PHONE := "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
const UA_TABLET := "Mozilla/5.0 (Linux; Android 14; Tab) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

var main
var device := "phone"
var landscape := false
var fullscreen := true
var pid := -1
var ws := WebSocketPeer.new()
var ws_url := ""
var connected := false
var next_id := 1
var http: HTTPRequest
var tex := ImageTexture.new()
var screen: TextureRect
var frame: PanelContainer
var msg: Label
var addr: LineEdit
var btns := {}
var touching := false
var last_move := 0
var started := false
var page_w := 390
var page_h := 844


func _ready() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.08, 0.1, 0.96)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	sb.corner_radius_bottom_right = 10
	add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	add_child(v)
	var bar := HBoxContainer.new()
	v.add_child(bar)
	for k in [["phone", "Handy"], ["tablet", "Tablet"], ["portrait", "Hoch"], ["landscape", "Quer"], ["fs", "Vollbild"], ["reload", "Neu laden"], ["close", "×"]]:
		var b := Button.new()
		b.text = k[1]
		b.toggle_mode = k[0] in ["phone", "tablet", "portrait", "landscape", "fs"]
		b.pressed.connect(_on_btn.bind(k[0]))
		bar.add_child(b)
		btns[k[0]] = b
	var row := HBoxContainer.new()
	v.add_child(row)
	var l := Label.new()
	l.text = "Adresse:"
	row.add_child(l)
	addr = LineEdit.new()
	addr.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	addr.placeholder_text = "http://192.168.1.20:5000"
	addr.text_submitted.connect(func(_t): _navigate())
	row.add_child(addr)
	msg = Label.new()
	msg.add_theme_color_override("font_color", Color(0.65, 0.7, 0.75))
	msg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(msg)
	frame = PanelContainer.new()
	var fs := StyleBoxFlat.new()
	fs.bg_color = Color(0, 0, 0)
	fs.border_color = Color(0.17, 0.18, 0.21)
	fs.set_border_width_all(12)
	fs.set_corner_radius_all(38)
	fs.set_content_margin_all(12)
	frame.add_theme_stylebox_override("panel", fs)
	frame.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(frame)
	screen = TextureRect.new()
	screen.texture = tex
	screen.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	screen.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	screen.mouse_filter = Control.MOUSE_FILTER_STOP
	screen.focus_mode = Control.FOCUS_CLICK
	screen.gui_input.connect(_on_screen_input)
	frame.add_child(screen)
	var hint := Label.new()
	hint.text = "Klicken und ziehen = Finger · Mausrad = scrollen · Tippen geht, wenn das Bild angeklickt ist"
	hint.add_theme_color_override("font_color", Color(0.5, 0.55, 0.6))
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(hint)
	http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_targets)
	_paint()
	visible = false


func open() -> void:
	visible = true
	if addr.text == "" and main.mw_addr != "":
		addr.text = "%s://%s:%d" % [str(main.mw.get("mw_scheme", "http")), main.mw_addr, int(main.mw.get("mw_port", 5000))]
	_layout()
	if not started:
		_start_browser()
	elif connected:
		_navigate()


func _exit_tree() -> void:
	stop()


func stop() -> void:
	if pid > 0:
		OS.kill(pid)
		pid = -1
	started = false
	connected = false


# ---- the invisible browser ------------------------------------------------------------------------------------------
func _find_browser() -> String:
	var args := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	for i in range(args.size() - 1):
		if args[i] == "--browser":
			return args[i + 1]
	var c := []
	if OS.get_name() == "Windows":
		for base in [OS.get_environment("ProgramFiles(x86)"), OS.get_environment("ProgramFiles"), OS.get_environment("LOCALAPPDATA")]:
			if base == "":
				continue
			c.append(base + "/Microsoft/Edge/Application/msedge.exe")
			c.append(base + "/Google/Chrome/Application/chrome.exe")
	else:
		c = ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/microsoft-edge"]
	for p in c:
		if FileAccess.file_exists(p):
			return p
	return ""


func _start_browser() -> void:
	var exe := _find_browser()
	if exe == "":
		msg.text = "Kein Edge / Chrome gefunden. Mit --browser <Pfad> angeben (z. B. zu msedge.exe)."
		return
	var prof := ProjectSettings.globalize_path("user://handy_browser")
	DirAccess.make_dir_recursive_absolute(prof)
	var sz := _size()
	var extra := []
	if OS.get_name() != "Windows" and (OS.get_environment("USER") == "root" or OS.get_environment("HOME") == "/root"):
		extra.append("--no-sandbox")                   # Linux as root only (a test computer)
	pid = OS.create_process(exe, extra + ["--headless=new", "--remote-debugging-port=%d" % PORT, "--remote-debugging-address=127.0.0.1", "--remote-allow-origins=http://127.0.0.1", "--user-data-dir=" + prof, "--no-first-run",
			"--no-default-browser-check", "--disable-extensions", "--mute-audio", "--window-size=%d,%d" % [sz.x, sz.y], "about:blank"])
	if pid <= 0:
		msg.text = "Browser liess sich nicht starten: " + exe
		return
	started = true
	msg.text = "Browser startet …"
	await get_tree().create_timer(1.5).timeout
	_ask_targets()


func _ask_targets() -> void:
	"""ask the browser for its page (plain HTTP over TCP: GET /json/list)"""
	if not started:
		return
	var tcp := StreamPeerTCP.new()
	if tcp.connect_to_host("127.0.0.1", PORT) != OK:
		await get_tree().create_timer(1.0).timeout
		_ask_targets()
		return
	var t0 := Time.get_ticks_msec()
	while tcp.get_status() == StreamPeerTCP.STATUS_CONNECTING and Time.get_ticks_msec() - t0 < 3000:
		await get_tree().process_frame
		tcp.poll()
	if tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		await get_tree().create_timer(1.0).timeout
		_ask_targets()
		return
	tcp.put_data(("GET /json/list HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nConnection: close\r\n\r\n" % PORT).to_utf8_buffer())
	var buf := PackedByteArray()
	t0 = Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 4000:
		await get_tree().process_frame
		tcp.poll()
		var n := tcp.get_available_bytes()
		if n > 0:
			var r: Array = tcp.get_data(n)
			if r[0] == OK:
				buf.append_array(r[1])
		elif tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			break
	var txt := buf.get_string_from_utf8()
	var p := txt.find("\r\n\r\n")
	_on_targets(0, 200 if p > 0 else 0, PackedStringArray(), txt.substr(p + 4).to_utf8_buffer() if p > 0 else PackedByteArray())


func _on_targets(_res: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if code != 200:
		await get_tree().create_timer(1.0).timeout
		_ask_targets()
		return
	var lst = JSON.parse_string(body.get_string_from_utf8())
	if typeof(lst) == TYPE_ARRAY:
		for t in lst:
			if t.get("type", "") == "page" and t.has("webSocketDebuggerUrl"):
				ws_url = t["webSocketDebuggerUrl"]
				ws = WebSocketPeer.new()
				ws.inbound_buffer_size = 8 * 1024 * 1024
				ws.max_queued_packets = 4096
				ws.connect_to_url(ws_url)
				return
	await get_tree().create_timer(1.0).timeout
	_ask_targets()


func _send(method: String, params := {}) -> int:
	if ws.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return -1
	ws.send_text(JSON.stringify({"id": next_id, "method": method, "params": params}))
	next_id += 1
	return next_id - 1


var shot_id := -1
var shot_t := 0


func _shoot() -> void:
	"""a picture of the emulated screen (exactly the device size) - several per second while the panel is open"""
	if not connected or not visible or shot_id >= 0 and Time.get_ticks_msec() - shot_t < 3000:
		return
	if Time.get_ticks_msec() - shot_t < 110:
		return
	shot_t = Time.get_ticks_msec()
	shot_id = _send("Page.captureScreenshot", {"format": "jpeg", "quality": 72, "captureBeyondViewport": false})


func _process(_dt: float) -> void:
	if ws_url == "":
		return
	ws.poll()
	var st := ws.get_ready_state()
	if st == WebSocketPeer.STATE_OPEN and not connected:
		connected = true
		_send("Page.enable")
		_apply_device()
		_navigate()
	elif st == WebSocketPeer.STATE_CLOSED and connected:
		connected = false
		msg.text = "Verbindung zum Browser verloren."
	_shoot()
	while ws.get_available_packet_count() > 0:
		var d = JSON.parse_string(ws.get_packet().get_string_from_utf8())
		if typeof(d) != TYPE_DICTIONARY:
			continue
		if d.has("error"):
			if int(d.get("id", -2)) == shot_id:
				shot_id = -1
			continue
		if int(d.get("id", -2)) == shot_id and d.has("result"):
			shot_id = -1
			var img2 := Image.new()
			if img2.load_jpg_from_buffer(Marshalls.base64_to_raw(str(d["result"].get("data", "")))) == OK:
				if tex.get_size() != Vector2(img2.get_size()):
					tex.set_image(img2)
				else:
					tex.update(img2)
			continue
		if d.get("method", "") == "Page.screencastFrame":
			var p: Dictionary = d["params"]
			_send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
			var img := Image.new()
			if img.load_jpg_from_buffer(Marshalls.base64_to_raw(p["data"])) == OK:
				if tex.get_size() != Vector2(img.get_size()):
					tex.set_image(img)
				else:
					tex.update(img)
		elif d.get("method", "") == "Page.loadEventFired":
			msg.text = "Motion Watch als %s · %s%s" % ["Handy" if device == "phone" else "Tablet", "Querformat" if landscape else "Hochformat", " · Vollbild" if fullscreen else ""]


func _size() -> Vector2i:
	var s: Vector2i = DEVICES[device]
	return Vector2i(s.y, s.x) if landscape else s


func _apply_device() -> void:
	var s := _size()
	page_w = s.x
	page_h = s.y
	_send("Emulation.setDeviceMetricsOverride", {"width": s.x, "height": s.y, "deviceScaleFactor": 2, "mobile": true,
			"screenOrientation": {"type": "landscapePrimary" if landscape else "portraitPrimary", "angle": 90 if landscape else 0}})
	_send("Emulation.setTouchEmulationEnabled", {"enabled": true, "maxTouchPoints": 5})
	_send("Emulation.setUserAgentOverride", {"userAgent": UA_PHONE if device == "phone" else UA_TABLET})
	_layout()


func _navigate() -> void:
	var a := addr.text.strip_edges().rstrip("/")
	if a == "":
		msg.text = "Motion Watch ist noch nicht verbunden: Simulation in Motion Watch einschalten oder die Adresse eintragen."
		return
	if not a.begins_with("http"):
		a = "http://" + a
	msg.text = "lädt " + a + " …"
	_send("Page.navigate", {"url": a + "/?preview=1" + ("&vo=1" if fullscreen else "")})


# ---- the window part --------------------------------------------------------------------------------------------------
func _on_btn(k: String) -> void:
	match k:
		"phone", "tablet":
			device = k
			_apply_device()
		"portrait", "landscape":
			landscape = k == "landscape"
			_apply_device()
		"fs":
			fullscreen = not fullscreen
			_navigate()
		"reload":
			_navigate()
		"close":
			visible = false
	_paint()


func _paint() -> void:
	if connected:
		msg.text = "Motion Watch als %s · %s%s" % ["Handy" if device == "phone" else "Tablet", "Querformat" if landscape else "Hochformat", " · Vollbild" if fullscreen else ""]
	btns["phone"].set_pressed_no_signal(device == "phone")
	btns["tablet"].set_pressed_no_signal(device == "tablet")
	btns["portrait"].set_pressed_no_signal(not landscape)
	btns["landscape"].set_pressed_no_signal(landscape)
	btns["fs"].set_pressed_no_signal(fullscreen)


func _layout() -> void:
	"""size of the device on the screen: as big as fits (left part of the window)"""
	var vs := get_viewport().get_visible_rect().size
	var s := _size()
	var max_h := vs.y - 170.0
	var max_w := vs.x - 420.0 - 60.0
	var k: float = min(max_h / s.y, max_w / s.x, 1.2)
	screen.custom_minimum_size = Vector2(s.x, s.y) * k
	var fs: StyleBoxFlat = frame.get_theme_stylebox("panel")
	fs.set_corner_radius_all(38 if device == "phone" else 22)
	reset_size()


func _to_page(p: Vector2) -> Vector2:
	var rs := screen.size
	var k: float = min(rs.x / page_w, rs.y / page_h)
	var off := (rs - Vector2(page_w, page_h) * k) / 2.0
	return (p - off) / k


func _on_screen_input(ev: InputEvent) -> void:
	if not connected:
		return
	if ev is InputEventMouseButton:
		var q := _to_page(ev.position)
		if ev.button_index == MOUSE_BUTTON_LEFT:
			touching = ev.pressed
			_send("Input.dispatchTouchEvent", {"type": "touchStart" if ev.pressed else "touchEnd",
					"touchPoints": [{"x": q.x, "y": q.y}] if ev.pressed else []})
			screen.grab_focus()
		elif ev.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and ev.pressed:
			_send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": q.x, "y": q.y, "deltaX": 0,
					"deltaY": -120 if ev.button_index == MOUSE_BUTTON_WHEEL_UP else 120})
		screen.accept_event()
	elif ev is InputEventMouseMotion and touching:
		if Time.get_ticks_msec() - last_move > 25:
			last_move = Time.get_ticks_msec()
			var q2 := _to_page(ev.position)
			_send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": q2.x, "y": q2.y}]})
		screen.accept_event()
	elif ev is InputEventKey and ev.pressed:
		var keys := {KEY_BACKSPACE: ["Backspace", 8], KEY_ENTER: ["Enter", 13], KEY_TAB: ["Tab", 9], KEY_ESCAPE: ["Escape", 27],
				KEY_LEFT: ["ArrowLeft", 37], KEY_UP: ["ArrowUp", 38], KEY_RIGHT: ["ArrowRight", 39], KEY_DOWN: ["ArrowDown", 40], KEY_DELETE: ["Delete", 46]}
		if keys.has(ev.keycode):
			var kk: Array = keys[ev.keycode]
			for t in ["keyDown", "keyUp"]:
				var ke := {"type": t, "key": kk[0], "code": kk[0], "windowsVirtualKeyCode": kk[1]}
				if kk[0] == "Enter" and t == "keyDown":
					ke["text"] = "\r"
				_send("Input.dispatchKeyEvent", ke)
		elif ev.unicode > 31:
			_send("Input.insertText", {"text": char(ev.unicode)})
		screen.accept_event()
